"""El vocabulario de eventos y su contrato.

Trece tipos, y ninguno lo emite un agente. El id de un evento derivado de una fuente es
DETERMINISTICO: sale del adaptador, del tipo y de la clave de deduplicacion. Volver a
ingerir la misma transcripcion tiene que ser inofensivo, y lo unico que lo garantiza es
que el segundo evento traiga el mismo id que el primero.
"""
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas  # noqa: E402

SCHEMA = "execution-accounting-event.schema.json"

TIPOS = (
    "TASK_STARTED",
    "TASK_COMPLETED",
    "SESSION_STARTED",
    "SESSION_COMPLETED",
    "WORKUNIT_STARTED",
    "WORKUNIT_COMPLETED",
    "AGENT_RUN_STARTED",
    "AGENT_RUN_COMPLETED",
    "MODEL_CALL_COMPLETED",
    "TOOL_CALL_COMPLETED",
    "MODEL_ESCALATION_REQUESTED",
    "BUDGET_DECISION_RECORDED",
    "ACCOUNTING_CORRECTION",
)

# Los que traen consumo y por lo tanto entran en la agregacion de tokens.
TIPOS_CON_USO = ("MODEL_CALL_COMPLETED", "TOOL_CALL_COMPLETED", "ACCOUNTING_CORRECTION")

CORRECCION = "ACCOUNTING_CORRECTION"

# 🔴 `metadata` es un objeto libre en el schema porque el validador de subconjunto no sabe
# decir "nada mas que esto". Las claves permitidas se cierran ACA, y la lista es corta a
# proposito: es lo unico que impide que alguien guarde una conversacion en el libro
# contable. Un `metadata` abierto era la puerta por la que entraba un prompt entero -con la
# IP de produccion y la clave del admin adentro- sin que la limpieza de secretos pudiera
# hacer nada, porque un prompt no es un patron de secreto.
CLAVES_DE_METADATA = (
    "cacheHit",           # refutacion: siempre false; un acierto de cache no es una llamada
    "correctionMode",     # como se aplica una correccion
    "phase",              # la fase de la corrida: `refutation`
    "providerAggregate",  # este evento es otra medicion del mismo periodo
    "providerSessionId",  # el id de sesion que declara el proveedor
    "reason",             # por que: el motivo de una correccion o de una decision
    "refutationUnitId",   # refutacion: la unidad REF-nnn que se refuto
    "resolutionPath",     # refutacion: SEMANTIC_REFUTATION
    "status",             # el estado de una decision de presupuesto
    "tier",               # el tier de un escalamiento
    "unreadable",         # la linea del libro no se pudo parsear
)

# 🔴 Y los valores son ESCALARES. Cerrar las claves de un solo nivel no cierra nada: con un
# objeto adentro, `{"reason": {"prompt": "..."}}` pasaba limpio, y con una lista entraban
# veinte turnos de doscientos caracteres cada uno sin que el recorte por string disparara
# nunca. Un anidamiento es donde entra una conversacion. Acá no hay ninguno: siete claves,
# un valor plano cada una, y ese valor recortado a `libro.TOPE_DE_TEXTO`.
ESCALARES = (str, int, float, bool, type(None))

# 🔴 Las cuatro de la refutacion no son texto libre: son un valor de una lista corta o un id
# con forma. No suben el techo de un evento, y `cacheHit` solo admite `false` porque un
# acierto de cache no es una llamada al modelo: un evento que dijera lo contrario seria una
# llamada de cero tokens que no existio.
ACOTADAS = {
    "phase": ("refutation",),
    "resolutionPath": ("SEMANTIC_REFUTATION",),
    "cacheHit": (False,),
}
ID_DE_REFUTACION = re.compile(r"^REF-[0-9]{3,6}$")

# 🔴 Y el cierre vale para TODO el evento, no para `metadata`. El interprete de subconjunto
# no tiene `additionalProperties`, asi que `usage`, `time`, `cost`, `source` y la raiz son
# tan libres como lo era `metadata`: cerrar uno de los cinco no cerraba nada. Una clave sin
# declarar en `usage` guardaba veinte turnos, y una clave de dos mil caracteres guardaba la
# conversacion en el NOMBRE del campo, donde ningun recorte de valores la miraba.
#
# Las claves permitidas salen del propio schema —`properties` en cada nivel—, no de una
# lista paralela: un campo nuevo del contrato queda permitido solo, y uno que nadie declaro
# no entra nunca.
#
# El tope numerico existe por el mismo motivo: `int` es escalar, y un entero de cuatro mil
# digitos es una conversacion codificada en base 256. Una cantidad de contabilidad
# -tokens, milisegundos, plata- entra en dieciocho digitos con lugar de sobra.
DIGITOS = 18
TOPE_NUMERICO = 10 ** DIGITOS

SIN_RESOLVER = "USAGE_UNRESOLVED"
RESUELTO = "RESOLVED"


class EventoInvalido(Exception):
    """El evento no se escribe. Una linea rota en un libro append-only no se saca mas."""


def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


_CACHE = {}


def _armador():
    """`contexto-armar.py`, de donde sale el validador de subconjunto.

    Se carga una vez por proceso. Un evento se valida en cada escritura, y ejecutar el
    modulo entero por evento convierte una ingesta de mil lineas en un minuto.
    """
    if "armador" not in _CACHE:
        ruta = rutas.localizar(("bin", "contexto-armar.py"), __file__)
        if ruta is None:
            return None
        spec = importlib.util.spec_from_file_location("contexto_armar_contabilidad", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CACHE["armador"] = modulo
    return _CACHE.get("armador")


def cargar_schema():
    if "schema" not in _CACHE:
        ruta = rutas.localizar(("schemas", SCHEMA), __file__)
        if ruta is None:
            raise EventoInvalido(
                "no esta %s. Un evento no se escribe sin poder validarlo." % SCHEMA)
        with io.open(ruta, encoding="utf-8") as f:
            _CACHE["schema"] = json.load(f)
    # Copia: el que pide el schema se lo puede quedar, y un cache compartido que alguien
    # toca deja de validar lo mismo a mitad de una corrida.
    return json.loads(json.dumps(_CACHE["schema"]))


def validar_metadata(evento):
    """Lo que el schema no puede decir: `metadata` no acepta una clave que nadie declaro.

    El interprete de subconjunto no tiene `additionalProperties`, asi que el cierre vive
    acá. No es una comodidad: `metadata` es el unico campo libre del contrato, y libre
    quiere decir que ahi entra un prompt.
    """
    metadata = evento.get("metadata")
    if metadata in (None, {}):
        return []
    if not isinstance(metadata, dict):
        return ["$.metadata: se esperaba un objeto"]

    errores = []
    sobran = sorted(k for k in metadata if k not in CLAVES_DE_METADATA)
    if sobran:
        errores.append(
            "$.metadata.%s: no es una clave declarada. El libro guarda contabilidad, no "
            "conversacion. Las declaradas son: %s"
            % (sobran[0], ", ".join(CLAVES_DE_METADATA)))
    for clave in sorted(metadata):
        if not isinstance(metadata[clave], ESCALARES):
            errores.append(
                "$.metadata.%s: solo valores escalares. Un objeto o una lista adentro de "
                "`metadata` es por donde entra una conversacion, y el cierre de claves no "
                "baja de nivel." % clave)
        errores.extend(_numero_acotado(metadata[clave], "$.metadata." + clave))
        valor = metadata[clave]
        if clave in ACOTADAS and not any(valor is v or (valor == v and type(valor) is type(v))
                                         for v in ACOTADAS[clave]):
            errores.append("$.metadata.%s: `%s` no es un valor admitido (%s)."
                           % (clave, str(valor)[:40], ", ".join(str(v) for v in ACOTADAS[clave])))
        if clave == "refutationUnitId" and not (isinstance(valor, str)
                                                and ID_DE_REFUTACION.match(valor)):
            errores.append("$.metadata.refutationUnitId: `%s` no es un id REF-nnn."
                           % str(valor)[:40])
    return errores


def _numero_acotado(valor, ruta):
    """Un entero de cuatro mil digitos es una conversacion codificada, no una cantidad."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return []
    # NaN primero: toda comparacion con NaN es falsa, asi que el control de abajo no lo ve.
    if valor != valor:
        return ["%s: NaN no es una cantidad." % ruta]
    try:
        desbordado = abs(valor) >= TOPE_NUMERICO
    except (TypeError, OverflowError):
        desbordado = True
    if not desbordado:
        return []
    return ["%s: el numero no entra en %d digitos. Una cantidad de contabilidad si; un "
            "texto codificado como entero, no." % (ruta, DIGITOS)]


def _revisar(nodo, esquema, ruta, errores):
    if isinstance(nodo, dict):
        declaradas = (esquema.get("properties") or {})
        for clave in sorted(nodo):
            if clave not in declaradas:
                errores.append(
                    "%s.%s: no es una clave declarada en el contrato. El libro guarda los "
                    "campos que el schema nombra y ninguno mas." % (ruta, clave))
                continue
            _revisar(nodo[clave], declaradas[clave], "%s.%s" % (ruta, clave), errores)
        return
    if isinstance(nodo, list):
        for i, item in enumerate(nodo):
            _revisar(item, esquema.get("items") or {}, "%s[%d]" % (ruta, i), errores)
        return
    errores.extend(_numero_acotado(nodo, ruta))


def validar_estructura(evento):
    """Ninguna clave que nadie declaro, en ningun nivel, y ningun numero desbordado.

    🔴 Es lo que el interprete de subconjunto no puede decir, y lo que hace falta para que
    la frase "el libro no puede guardar una conversacion" sea cierta: sin esto, `usage`,
    `time`, `cost`, `source` y la raiz del evento aceptan cualquier campo inventado, y una
    clave de dos mil caracteres guarda la conversacion en el nombre del campo.

    `metadata` no se recorre acá: su vocabulario no esta en el schema y lo cierra
    `validar_metadata`.
    """
    if not isinstance(evento, dict):
        return ["$: se esperaba un objeto"]
    esquema = cargar_schema()
    propiedades = dict(esquema.get("properties") or {})
    propiedades.pop("metadata", None)
    errores = []
    _revisar(dict((k, v) for k, v in evento.items() if k != "metadata"),
             {"properties": propiedades}, "$", errores)
    return errores


def validar(evento):
    """Lista de errores. Vacia es valido.

    Es el schema MAS lo que el subconjunto no sabe expresar. Las dos mitades van juntas
    porque separarlas seria dejar una puerta con dos llaves y una sola cerradura.
    """
    armador = _armador()
    if armador is None:
        raise EventoInvalido(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    return (armador.validar(evento, esquema)
            + validar_estructura(evento)
            + validar_metadata(evento))


def id_de(adaptador, tipo, clave):
    """El id determinista de un evento derivado de una fuente.

    Con la misma fuente leida dos veces sale el mismo id, y el libro lo rechaza la segunda
    vez. Es la primera de las dos defensas contra el doble conteo; la otra es `dedupKey`,
    que sigue viva adentro del evento para que la agregacion tambien pueda verla.
    """
    crudo = "|".join((str(adaptador), str(tipo), str(clave)))
    return "ev_" + hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:24]


def nuevo(tipo, task_id, adaptador, **campos):
    """Un evento armado y validado. Levanta si no cumple el contrato."""
    if tipo not in TIPOS:
        raise EventoInvalido(
            "`%s` no es un tipo de evento. Los trece son: %s." % (tipo, ", ".join(TIPOS)))
    if not str(task_id or ""):
        raise EventoInvalido("un evento sin taskId no tiene libro donde escribirse.")

    clave = campos.get("dedupKey")
    evento = {
        "eventId": campos.get("eventId") or id_de(adaptador, tipo, clave or ahora()),
        "eventType": tipo,
        "timestamp": str(campos.get("timestamp") or ahora()),
        "taskId": str(task_id),
        "source": {
            "adapter": str(adaptador),
            "rawReference": campos.get("rawReference"),
        },
    }
    for nombre in ("projectId", "sessionId", "workUnitId", "agentId", "dedupKey",
                   "correctsEventId", "usage", "time", "cost", "metadata"):
        if nombre in campos:
            evento[nombre] = campos[nombre]

    if tipo == CORRECCION and not evento.get("correctsEventId"):
        raise EventoInvalido(
            "una correccion sin `correctsEventId` no dice que enmienda, y una correccion "
            "que no dice que enmienda es una linea suelta que suma dos veces.")

    errores = validar(evento)
    if errores:
        raise EventoInvalido(
            "el evento no valida contra %s:\n  - %s" % (SCHEMA, "\n  - ".join(errores[:5])))
    return evento


def corregir(original, motivo, adaptador, **campos):
    """Una correccion es un evento NUEVO. El original queda donde estaba, byte a byte.

    🔴 No hay forma de enmendar un evento tocandolo. Lo que hace confiable a un libro no es
    la intencion de quien escribe: es que no exista el verbo.
    """
    if not str(motivo or ""):
        raise EventoInvalido(
            "una correccion sin motivo es un ajuste que nadie puede auditar despues.")
    datos = dict(campos)
    datos["correctsEventId"] = original["eventId"]
    datos.setdefault("dedupKey", None)
    meta = dict(datos.get("metadata") or {})
    meta["reason"] = str(motivo)
    datos["metadata"] = meta
    for heredado in ("projectId", "sessionId", "workUnitId", "agentId"):
        if heredado not in datos and heredado in original:
            datos[heredado] = original[heredado]
    datos["eventId"] = id_de(adaptador, CORRECCION, original["eventId"] + "|" + str(motivo))
    return nuevo(CORRECCION, original["taskId"], adaptador, **datos)


CLASES_DE_TOKEN = ("inputTokens", "outputTokens", "cacheReadTokens", "cacheCreationTokens")


def uso_sin_resolver(provider=None, model=None):
    """El consumo que no se pudo leer. NO es cero, y la diferencia importa.

    Cero dice "no consumio". Esto dice "no se sabe", que es lo unico honesto cuando la
    fuente no reporta. Un reporte que suma ceros desconocidos da un total que parece
    barato, y barato es exactamente lo que nadie revisa.
    """
    uso = {"state": SIN_RESOLVER, "provider": provider, "model": model,
           "contextTokens": None, "contextLimit": None}
    for clase in CLASES_DE_TOKEN:
        uso[clase] = None
    return uso
