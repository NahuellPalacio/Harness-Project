"""Adaptador de transcripciones JSONL de Claude Code.

Lee un archivo de transcripcion y devuelve registros normalizados. No arma eventos, no
calcula plata y no sabe que existe un libro: eso es de `contrato.py`, del lado que no
conoce ningun proveedor.

🔴 La transcripcion escribe UNA LINEA POR BLOQUE DE CONTENIDO, y todas las lineas del mismo
mensaje repiten el mismo `usage`. Medido el 20-09-2026 sobre una transcripcion real de este
repositorio: 438 lineas de asistente, 252 ids de mensaje distintos, 186 repetidas. Sumar
linea por linea daba 739.096 tokens de salida contra 370.919 reales. La clave de
deduplicacion es el id del mensaje, y por eso existe.

🔴 `cost-state` es ACUMULADO. Aparece varias veces en el mismo archivo y cada aparicion
incluye a la anterior: se queda la ultima. Sumarlas seria contar la sesion entera tantas
veces como veces se escribio la linea.

🔴 La foto de la ventana -input + cache read + cache creation- NO es un consumo adicional.
Viaja como `context` para que la barra la muestre, y la agregacion sabe que no se suma.
"""
import io
import json
import os

from . import contrato

NOMBRE = "claude-code"
PROVEEDOR = "anthropic"

ASISTENTE = "assistant"
ESTADO_DE_COSTO = "cost-state"

# Del nombre del proveedor al del contrato normalizado. Es la unica tabla de traduccion, y
# vive acá: el nucleo no conoce ninguno de los nombres de la izquierda.
DE_USO = (
    ("input", "input_tokens"),
    ("output", "output_tokens"),
    ("cacheRead", "cache_read_input_tokens"),
    ("cacheCreation", "cache_creation_input_tokens"),
)
DE_AGREGADO = (
    ("input", "inputTokens"),
    ("output", "outputTokens"),
    ("cacheRead", "cacheReadInputTokens"),
    ("cacheCreation", "cacheCreationInputTokens"),
)

# Lo que ocupa la ventana ahora: lo que entro en esta llamada, no lo que salio.
DEL_CONTEXTO = ("input", "cacheRead", "cacheCreation")

MONEDA = "USD"


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# Lo que una linea tiene que decir, como texto, para que valga la pena parsearla: una linea
# de asistente o de estado de costo nombra su tipo, y la que no lo nombra no es ninguna de las
# dos. Saltearla sin parsear no pierde nada. Lo usa la Context Bar, que lee la transcripcion
# entera en cada mensaje: ahi casi todos los bytes son resultados de herramientas, y
# parsearlos para descartarlos era la mitad de su latencia.
TIPOS_QUE_CUENTAN = (ASISTENTE, ESTADO_DE_COSTO)


def _lineas(ruta, solo_con=None, desde=0, cuenta=None):
    """(numero, dato) de cada linea que parsea. Las lineas hasta `desde` se cuentan y no se
    parsean. En `cuenta`, si se pasa, queda cuantas lineas tiene el archivo."""
    numero = 0
    with io.open(ruta, encoding="utf-8") as f:
        for numero, linea in enumerate(f, 1):
            if numero <= desde:
                continue
            if solo_con is not None and not any(m in linea for m in solo_con):
                continue
            linea = linea.strip()
            if not linea:
                continue
            try:
                yield numero, json.loads(linea)
            except ValueError:
                continue
    if cuenta is not None:
        cuenta.append(numero)


def _tokens_de(uso, tabla):
    tokens = {}
    for normalizado, crudo in tabla:
        tokens[normalizado] = _entero(uso.get(crudo))
    presentes = [tokens[c] for c in DEL_CONTEXTO if tokens.get(c) is not None]
    tokens["context"] = sum(presentes) if presentes else None
    tokens["contextLimit"] = None
    return tokens


def leer(ruta, rapido=False, desde_linea=0):
    """Los registros normalizados de una transcripcion. Deduplicados por id de mensaje.

    `rapido` saltea sin parsear las lineas que no nombran ninguno de TIPOS_QUE_CUENTAN. Da
    los mismos registros, con las mismas referencias de linea.

    `desde_linea` saltea sin parsear las lineas hasta esa, incluida: es quien ya las ingirio
    diciendo hasta donde leyo. Una transcripcion se escribe solo agregando al final; si el
    archivo tiene menos lineas que eso, es otro archivo, y se lee entero.
    """
    if not ruta or not os.path.isfile(ruta):
        return [contrato.sin_resolver(
            reference=str(ruta or ""),
            motivo="no hay transcripcion en esa ruta: el consumo existe y no se pudo leer",
            provider=PROVEEDOR)]

    archivo = os.path.basename(ruta)
    registros = []
    vistos = set()
    ultimo_costo = None

    cuenta = []
    for numero, dato in _lineas(ruta, TIPOS_QUE_CUENTAN if rapido else None,
                                desde_linea, cuenta):
        tipo = dato.get("type")
        if tipo == ESTADO_DE_COSTO:
            ultimo_costo = (numero, dato)
            continue
        if tipo != ASISTENTE:
            continue
        mensaje = dato.get("message") or {}
        mid = str(mensaje.get("id") or "")
        if not mid or mid in vistos:
            continue
        vistos.add(mid)
        uso = mensaje.get("usage") or {}
        registros.append(contrato.registro(
            provider=PROVEEDOR,
            model=mensaje.get("model"),
            tokens=_tokens_de(uso, DE_USO),
            session={"providerSessionId": dato.get("sessionId")},
            dedup_key="msg|" + mid,
            reference="%s#L%d" % (archivo, numero),
            timestamp=dato.get("timestamp"),
        ))

    if desde_linea and cuenta and cuenta[0] < desde_linea:
        return leer(ruta, rapido)
    if ultimo_costo is not None:
        registros.extend(_del_estado_de_costo(ultimo_costo, archivo))
    if not registros:
        return [contrato.sin_resolver(
            reference=archivo,
            motivo="la transcripcion no trae ninguna linea con consumo",
            provider=PROVEEDOR)]
    return registros


def _del_estado_de_costo(ultimo, archivo):
    """Lo que reporta el proveedor sobre la sesion entera: tokens, plata y tiempo.

    Los tokens salen como AGREGADO -otra medicion del mismo periodo, no un hecho
    adicional- y por eso la agregacion los concilia en vez de sumarlos. La plata y el
    tiempo tambien vienen acá porque no existen en ningun otro lado de la transcripcion.

    🔴 La clave lleva la linea del estado (`agg|<sesion>|<modelo>|L<n>`). Con una clave fija,
    el libro -que deduplica por eventId- se quedaba con el PRIMER estado acumulado que vio, y
    una sesion ingerida de a poco congelaba la plata y el tiempo en el primer cost-state. Con
    la linea, cada estado nuevo entra como un evento nuevo, reingerir el mismo no duplica, y
    la agregacion toma el ultimo de cada medicion en vez de sumarlos.
    """
    numero, dato = ultimo
    sesion = str(dato.get("sessionId") or "")
    referencia = "%s#L%d" % (archivo, numero)
    marca = dato.get("timestamp") or str(dato.get("startTime") or "")
    registros = []

    for modelo in sorted((dato.get("modelUsage") or {})):
        crudo = (dato.get("modelUsage") or {})[modelo]
        registros.append(contrato.registro(
            provider=PROVEEDOR,
            model=modelo,
            tokens=_tokens_de(crudo, DE_AGREGADO),
            session={"providerSessionId": sesion},
            dedup_key="agg|%s|%s|L%d" % (sesion, modelo, numero),
            reference=referencia,
            timestamp=marca,
            kind=contrato.AGREGADO,
            reported_amount=(None if dato.get("hasUnknownModelCost")
                             else crudo.get("costUSD")),
            currency=MONEDA,
        ))

    registros.append(contrato.registro(
        provider=PROVEEDOR,
        session={"providerSessionId": sesion},
        time={"wallMs": _entero(dato.get("totalDuration")),
              "modelMs": _entero(dato.get("totalAPIDuration")),
              "toolMs": _entero(dato.get("totalToolDuration"))},
        dedup_key="agg|%s|time|L%d" % (sesion, numero),
        reference=referencia,
        timestamp=marca,
        kind=contrato.AGREGADO,
    ))
    return registros
