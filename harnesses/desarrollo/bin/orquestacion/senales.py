"""Las senales de aplicabilidad: el dato que decide si una regla CONDITIONAL aplica.

La matriz ya sabia que hacer con una senal; lo que no existia era quien la produce. Hasta
hoy `plan.py` le pasaba un diccionario de booleanos que nadie llenaba, y las 16 reglas
condicionales del estandar salian sin resolver en toda corrida real.

Un booleano no alcanza. `{"citizenFacing": true}` no dice quien lo dijo ni contra que, y una
regla que decide aplicar sobre un booleano sin respaldo se equivoca en silencio en las dos
direcciones: le exige autenticacion ciudadana a un backoffice, o se la saca a un tramite del
ciudadano porque nadie escribio la palabra en el Jira.

    Matriz normativa      declara el id de la senal
    Productor             emite TRUE/FALSE/UNRESOLVED con evidencia
    Resolucion            mapea a APPLICABLE / NOT_APPLICABLE / APPLICABILITY_UNRESOLVED
    Policy y Check        se ejecutan despues de resolver la aplicabilidad

🔴 **La ausencia de evidencia es `UNRESOLVED`, nunca `FALSE`.** Que nadie haya escrito
"ciudadano" en ningun lado no prueba que la aplicacion no interactue con el ciudadano: prueba
que nadie lo escribio. Convertir lo ausente en `FALSE` hace desaparecer la regla del reporte,
y una regla que desaparece no se vuelve a buscar.

🔴 **Dos evidencias que se contradicen no se deciden.** `SIGNAL_CONFLICT` y las dos
conservadas. Elegir la que deja el plan mas corto es el sesgo mas barato que puede tener un
productor y no deja rastro.

🔴 **Lo que interpreta un modelo no pisa un dato estructurado.** Gana lo estructurado y la
interpretacion queda anotada. Un modelo leyendo un PDF no revierte un campo que alguien
escribio.

🔴 **Esto es generico.** La senal valida es la que declara la matriz; no hay una lista
paralela que alguien tenga que acordarse de actualizar, ni una rama por id de senal.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

SCHEMA = "normative-signal.schema.json"

VERDADERA = "TRUE"
FALSA = "FALSE"
SIN_RESOLVER = "UNRESOLVED"
VALORES = (VERDADERA, FALSA, SIN_RESOLVER)

# Las estructuradas son un dato explicito que alguien escribio; las interpretadas salen de
# leer material no estructurado. Cuando discrepan gana la estructurada.
FUENTES_ESTRUCTURADAS = ("TASK_CONTEXT", "PROJECT_CONTEXT", "REPOSITORY_CONFIGURATION",
                         "HUMAN_CONFIRMATION")
FUENTES_INTERPRETADAS = ("JIRA_FICHA_DE_PROYECTO", "PROJECT_DOCUMENTATION", "AGENT_STATEMENT",
                         "REPOSITORY_DEPENDENCY")

# Ninguna de las dos sostiene un valor por si sola. La opinion de un agente es la misma regla que
# ya sostiene `revisiones.py` con PROJECT_CONVENTION: algo con formato de evidencia no es
# evidencia. Y una dependencia declarada prueba lo que HAY instalado, no lo que la aplicacion
# HACE: `angular-oauth2-oidc` en el manifiesto no es una aplicacion que autentica usuarios.
#
# 🔴 La clase se separo de REPOSITORY_CONFIGURATION, que si es estructurada. Mezclarlas era una
# clase de mas ancha: con la vieja, una dependencia sola alcanzaba para encender cualquier senal.
FUENTES_DEBILES = ("AGENT_STATEMENT", "REPOSITORY_DEPENDENCY")

PRODUCTORES = ("DETERMINISTIC", "AGENT_EVIDENCE_BACKED", "HUMAN")

SIN_EVIDENCIA = "SIGNAL_EVIDENCE_MISSING"
CONFLICTO = "SIGNAL_CONFLICT"
NO_DECLARADA = "SIGNAL_NOT_DECLARED"
PISADA = "SIGNAL_INTERPRETATION_OVERRIDDEN"
SCHEMA_INVALIDO = "SIGNAL_SCHEMA_INVALID"
PRODUCTOR_INVALIDO = "SIGNAL_PRODUCER_INVALID"


class SenalInvalida(Exception):
    """Una senal mal formada no se interpreta: se rechaza y queda sin resolver."""


# -- el contrato ---------------------------------------------------------------

def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise SenalInvalida("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(senal, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise SenalInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(senal, esquema)


def declaradas(desde=None):
    """Los ids de senal que las matrices declaran. Sale de ahi y de ningun lado mas.

    Son dos estandares y las dos matrices cuentan: una senal que solo declara ES0902 esta
    declarada igual. Que un estandar no se pueda leer no borra las senales del otro.
    """
    from . import matriz
    from . import seguridad
    ids = set()
    try:
        for r in matriz.cargar(desde).get("rules", []):
            for s in (r.get("applicability") or {}).get("signals") or []:
                ids.add(s)
    except matriz.MatrizInvalida:
        pass
    try:
        ids |= seguridad.senales_declaradas(None, desde)
    except seguridad.SeguridadInvalida:
        pass
    return ids


def reglas_de(signal_id, desde=None):
    """Que reglas dependen de esta senal. Para decir a quien afecta que falte.

    Las de ES0901 salen con su id local -es lo que ya leia quien llama-; las de ES0902 salen
    con su clave compuesta, porque `G1` no alcanza para saber de cual de los dos se habla.
    """
    from . import matriz
    from . import seguridad
    salida = []
    try:
        salida.extend(r.get("id") for r in matriz.cargar(desde).get("rules", [])
                      if signal_id in ((r.get("applicability") or {}).get("signals") or []))
    except matriz.MatrizInvalida:
        pass
    try:
        salida.extend(seguridad.clave(r.get("id")) for r in seguridad.reglas(None, desde)
                      if signal_id in ((r.get("applicability") or {}).get("signals") or []))
    except seguridad.SeguridadInvalida:
        pass
    return salida


def validar(senal, desde=None):
    """Lista de problemas estructurales. Vacia es bien formada.

    Nada de esto opina sobre si el valor es cierto: opina sobre si la senal se puede leer,
    rastrear y discutir. Una senal que no cita de donde sale no es una senal mas floja — es
    una afirmacion con formato de senal.
    """
    problemas = list(validar_schema(senal, desde))

    sid = (senal or {}).get("signalId") or ""
    if sid and sid not in declaradas(desde):
        problemas.append("%s: `%s` no es una senal que la matriz declare. Las senales validas "
                         "salen de la matriz normativa" % (NO_DECLARADA, sid))

    for i, e in enumerate((senal or {}).get("evidence") or []):
        if not (e.get("reference") or "").strip():
            problemas.append("%s: la evidencia %s no referencia nada"
                             % (SCHEMA_INVALIDO, e.get("evidenceId") or i))
        if not (e.get("claim") or "").strip():
            problemas.append("%s: la evidencia %s no dice que afirma la fuente"
                             % (SCHEMA_INVALIDO, e.get("evidenceId") or i))

    problemas.extend(validar_productor(senal, desde))
    return problemas


def validar_productor(senal, desde=None):
    """El productor tiene que existir. Una senal no crea agentes."""
    productor = (senal or {}).get("producer") or {}
    tipo = productor.get("type")
    if tipo not in PRODUCTORES:
        return ["%s: el productor declara el tipo `%s`, que no existe"
                % (PRODUCTOR_INVALIDO, tipo)]
    if tipo != "AGENT_EVIDENCE_BACKED":
        return []
    aid = productor.get("id") or ""
    if not aid:
        return ["%s: un productor AGENT_EVIDENCE_BACKED tiene que decir que agente es"
                % PRODUCTOR_INVALIDO]
    from . import registro_agentes as reg
    try:
        registro = reg.cargar(desde or __file__)
    except reg.RegistroInvalido:
        return ["no se pudo leer el registro de agentes: el productor no se valido"]
    if aid not in {a.get("id") for a in registro.get("agents", [])}:
        return ["%s: la senal nombra a %s, que el registro de agentes no declara"
                % (PRODUCTOR_INVALIDO, aid)]
    return []


# -- la evidencia --------------------------------------------------------------

def _utiles(senal):
    """Las evidencias que referencian algo y afirman algo. El resto no cuenta."""
    return [e for e in (senal or {}).get("evidence") or []
            if (e.get("reference") or "").strip() and (e.get("claim") or "").strip()]


def _sostiene(evidencia, declarado):
    """Que valor sostiene una evidencia. Sin `supports`, sostiene el valor declarado."""
    return evidencia.get("supports") or declarado


def _por_clase(senal, declarado):
    """(estructuradas, interpretadas) como {valor: [evidencia, ...]}, sin las debiles."""
    estructuradas, interpretadas = {}, {}
    for e in _utiles(senal):
        clase = e.get("sourceType")
        if clase in FUENTES_DEBILES:
            continue
        destino = estructuradas if clase in FUENTES_ESTRUCTURADAS else interpretadas
        destino.setdefault(_sostiene(e, declarado), []).append(e)
    return estructuradas, interpretadas


# -- la resolucion -------------------------------------------------------------

def resolver_una(senal, desde=None):
    """El valor de una senal, derivado de su evidencia, con sus estados y su evidencia entera.

    El valor NO lo decide quien escribe la senal: se deriva. Dejar que lo declare quien la
    escribe es dejar que una senal sin evidencia decida que una regla no aplica.
    """
    sid = (senal or {}).get("signalId") or ""
    salida = {"signalId": sid, "value": SIN_RESOLVER, "states": [],
              "evidence": list((senal or {}).get("evidence") or []),
              "producer": dict((senal or {}).get("producer") or {}),
              "reason": (senal or {}).get("reason") or "", "issues": []}
    # 🔴 Los dos se copian solo si SON un objeto. `dict("PROJECT")` no es un dato invalido: es
    # un ValueError que rompe la resolucion de cualquier senal, y `validar` -que corre dos
    # lineas mas abajo- ya sabe contestar "se esperaba object y vino str". Un dato malformado
    # que rompe el modulo no es un dato que fallo cerrado.
    #
    # La linea de `source` tenia el mismo agujero desde antes que existiera el alcance, asi que
    # se arreglan las dos: el patron es de la casa, no de este cambio.
    if isinstance((senal or {}).get("source"), dict):
        salida["source"] = dict(senal["source"])
    # 🔴 El alcance se conserva, como la tupla normativa. Sin esto, el campo que
    # `normative-signal.schema.json` declara existe en el documento y desaparece en la
    # resolucion, asi que una regla que exija coherencia de alcance -ES0901 7.1 D5- no lo ve
    # nunca por el camino por el que una senal viaja a un plan, y toda corrida real le sale
    # sin alcance declarado. Lo encontro el refutador de D5: el mecanismo quedaba estricto
    # donde el dato no podia cumplir y laxo donde no se habia declarado nada.
    if isinstance((senal or {}).get("scope"), dict):
        salida["scope"] = dict(senal["scope"])

    problemas = validar(senal, desde)
    if problemas:
        estados = [NO_DECLARADA] if any(p.startswith(NO_DECLARADA) for p in problemas) else []
        if any(p.startswith(PRODUCTOR_INVALIDO) for p in problemas):
            estados.append(PRODUCTOR_INVALIDO)
        if not estados:
            estados = [SCHEMA_INVALIDO]
        salida.update({"states": sorted(set(estados)), "issues": problemas})
        return salida

    declarado = senal.get("value")
    if declarado == SIN_RESOLVER:
        return salida

    estructuradas, interpretadas = _por_clase(senal, declarado)
    if not estructuradas and not interpretadas:
        salida["states"] = [SIN_EVIDENCIA]
        salida["issues"] = ["%s: `%s` afirma %s y no lo respalda ninguna fuente que alcance"
                            % (SIN_EVIDENCIA, sid, declarado)]
        return salida

    if len(estructuradas) > 1 or (not estructuradas and len(interpretadas) > 1):
        salida["states"] = [CONFLICTO]
        salida["issues"] = ["%s: `%s` tiene evidencia que afirma las dos cosas; no se elige "
                            "una" % (CONFLICTO, sid)]
        return salida

    if estructuradas:
        valor = list(estructuradas.keys())[0]
        # Lo interpretado que contradice a lo estructurado no lo pisa: se anota.
        if any(v != valor for v in interpretadas):
            salida["states"] = [PISADA]
            salida["issues"] = ["%s: una fuente interpretada afirma lo contrario de un dato "
                                "estructurado; gana el estructurado" % PISADA]
    else:
        valor = list(interpretadas.keys())[0]

    salida["value"] = valor
    return salida


def resolver(senales, desde=None):
    """{signalId: resolucion} de un conjunto de senales, en el orden de entrada.

    `senales` es una lista de documentos de senal, o un diccionario {id: documento}. Un
    booleano tambien entra: es la forma vieja y sigue andando.
    """
    salida = {}
    for senal in _como_lista(senales):
        resuelta = resolver_una(senal, desde)
        sid = resuelta["signalId"]
        if not sid:
            continue
        salida[sid] = resuelta
    return salida


def booleanos(resueltas):
    """Lo que la matriz consume: {id: bool} solo con lo resuelto.

    Lo que quedo `UNRESOLVED` no entra. Que no entre es lo que deja la regla en
    `APPLICABILITY_UNRESOLVED` con el nombre de la senal que falta escrito al lado.
    """
    salida = {}
    for sid, r in (resueltas or {}).items():
        if r.get("value") == VERDADERA:
            salida[sid] = True
        elif r.get("value") == FALSA:
            salida[sid] = False
    return salida


def normalizar(entrada, desde=None):
    """(booleanos, senales) de lo que venga: booleanos viejos o documentos con evidencia.

    Las dos formas conviven a proposito. `matriz.resolver` conserva su contrato -recibe
    booleanos- y lo nuevo se apoya arriba: cambiarle el tipo a un campo que alguien ya
    consume es romper a distancia.
    """
    lista = _como_lista(entrada)
    if not lista:
        return {}, {}
    resueltas = resolver(lista, desde)
    return booleanos(resueltas), resueltas


def _como_lista(entrada):
    """Las tres formas de entrada, en una sola. Un booleano suelto se envuelve."""
    if not entrada:
        return []
    if isinstance(entrada, dict):
        lista = []
        for sid, valor in entrada.items():
            if isinstance(valor, dict):
                senal = dict(valor)
                senal.setdefault("signalId", sid)
                lista.append(senal)
            elif isinstance(valor, bool):
                lista.append(_de_booleano(sid, valor))
        return lista
    return [s for s in entrada if isinstance(s, dict)]


def _de_booleano(sid, valor):
    """La forma vieja, envuelta. Se declara de donde sale para que no parezca respaldada."""
    return {
        "signalId": sid,
        "value": VERDADERA if valor else FALSA,
        "evidence": [{"evidenceId": "%s-declarada" % sid,
                      "sourceType": "TASK_CONTEXT",
                      "reference": "normativeSignals",
                      "claim": "la unidad de trabajo declara %s = %s" % (sid, valor)}],
        "producer": {"type": "DETERMINISTIC"},
    }


# -- el productor --------------------------------------------------------------

def producir(signal_id, evidencias, productor=None, valor=None, desde=None):
    """Arma una senal a partir de su evidencia y la resuelve. Es el productor, y es generico.

    No detecta nada: la evidencia entra como dato, igual que el inventario de tecnologias de
    G1 y que las fuentes de practica de G2. Quien la junte -el analisis de impacto, la ficha,
    una persona- es otro cambio.

    Sin evidencia util no hay valor: sale `UNRESOLVED`, nunca `FALSE`.
    """
    declarado = valor
    if declarado is None:
        # Sin valor declarado, lo dice la evidencia. Si ninguna dice que sostiene, no hay
        # nada que derivar: UNRESOLVED. Si dicen cosas distintas, la contradiccion la
        # reporta la resolucion — aca no se elige.
        utiles = [e for e in (evidencias or [])
                  if (e.get("reference") or "").strip() and (e.get("claim") or "").strip()
                  and e.get("sourceType") not in FUENTES_DEBILES]
        sostenidos = sorted({e["supports"] for e in utiles if e.get("supports")})
        declarado = sostenidos[0] if sostenidos else SIN_RESOLVER
    senal = {"signalId": signal_id, "value": declarado,
             "evidence": list(evidencias or []),
             "producer": dict(productor or {"type": "DETERMINISTIC"})}
    return resolver_una(senal, desde)
