"""ES0902 v6.2: las 21 reglas del estandar de seguridad, y que resultado tiene cada una.

Es un estandar distinto de ES0901, no una extension suya. Comparte el runtime -senales,
policies, checks, reviews, registro de controles- y no comparte ni el archivo ni el espacio de
ids:

    es0901-7.1-normative-matrix.json   24 filas   G1, G2, D1..D8, P1..P7, C1..C4, M1..M3
    es0902-6.2-normative-matrix.json   21 filas   O1, O2, C1..C3, Vu1..Vu10, Ve1, Ve2, G1..G4

🔴 **`G1` no identifica una regla.** Los dos estandares tienen G1 y no son la misma. La clave
global es compuesta -`ES0901.G1`, `ES0902.G1`- y viaja al lado del id local, que es el que se
cita contra el texto del estandar. Reemplazar uno por el otro rompe uno de los dos usos.

🔴 **El harness no aprueba seguridad.** ES0902 §4 separa el control automatizado del circuito
interno de DGSEI. Todo lo que este modulo produce es interno: prepara, mide y declara lo que
falta. `APPROVED` exige procedencia externa y esa frontera vive en `evaluacion.py`.

🔴 **Falta evidencia -> `UNRESOLVED`, nunca PASS.** Y una regla que no declara ningun control
tampoco cumple al vacio: cumplir sobre un conjunto vacio de controles es la forma mas barata de
que un estandar entero salga verde.

🔴 **Las reglas con algoritmo propio son diez y estan declaradas.** El resultado es generico
-hallazgo abierto, control en FAIL, control sin evidencia- salvo donde el estandar declara un
algoritmo: O1, C2, C3, Ve2, Vu4, Vu9, Vu10, G2, G3 y G4. Una undecima rama por id seria el estandar
reinterpretandose en el codigo, y `ALGORITMOS` esta para que se vea.

🔴 **C3 tampoco la contesta el camino generico.** Cuatro `controlResults` en PASS la pondrian en
`COMPLIANT` sin mirar si el catalogo es del Estandar de Desarrollo VIGENTE. Sale de
`estandar_de_desarrollo.py`, que resuelve esa linea base y agrega C3 de los controles de G1. Este modulo
no sabe del Anexo II, a proposito.

🔴 **O1 es el que el camino generico no puede contestar.** Sus dos controles declarados son su
propia policy y su propia review: dos `controlResults` en `PASS` la pondrian en `COMPLIANT` sin
que nadie mire que normativa de TI del GCABA aplica. Sale de `linea_base.py`, que la resuelve
contra la linea base normativa y contra los resultados que los dos estandares ya produjeron.

🔴 **La matriz provista no se corrige.** Declara `security-vulnerability-acceptance-threshold`
como policy y como check bajo la misma regla. Se reporta `SECURITY_CONTROL_ID_TYPE_COLLISION`
y se sigue: arreglar un archivo normativo provisto es inventar normativa.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO = "es0902-6.2-normative-matrix.json"
SCHEMA = "es0902-normative-matrix.schema.json"

ESTANDAR = "ES0902"
VERSION_ESPERADA = "6.2"
FECHA_DE_FUENTE = "2025-08"
CANTIDAD_ESPERADA = 21

# El inventario exacto. No se deduce del archivo: es contra esto que se compara lo que el
# archivo trae, y por eso puede decir CUAL falta en vez de solo cuantas hay.
INVENTARIO = ("O1", "O2",
              "C1", "C2", "C3",
              "Vu1", "Vu2", "Vu3", "Vu4", "Vu5",
              "Vu6", "Vu7", "Vu8", "Vu9", "Vu10",
              "Ve1", "Ve2",
              "G1", "G2", "G3", "G4")

SEPARADOR = "."

MODOS = ("ALWAYS", "CONDITIONAL")
APLICABLE = "APPLICABLE"
NO_APLICABLE = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
EXPRESION_SIN_RESOLVER = "APPLICABILITY_EXPRESSION_UNRESOLVED"

# El resultado de una regla. `OVERRIDDEN` no es un aprobado: es una obligacion levantada por
# una excepcion con respaldo, y la excepcion viaja pegada al resultado.
CUMPLE = "COMPLIANT"
NO_CUMPLE = "NON_COMPLIANT"
RESULTADO_SIN_RESOLVER = "UNRESOLVED"
EXCEPTUADA = "OVERRIDDEN"
RESULTADOS = (CUMPLE, NO_CUMPLE, RESULTADO_SIN_RESOLVER, EXCEPTUADA, NO_APLICABLE)

# Los ocho estados globales que ES0902 exige. Viven aca, en un solo lugar, porque los tres
# modulos del estandar los emiten y una constante repetida se desincroniza en silencio.
OVERRIDE_SIN_RESOLVER = "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED"
INTERPRETACION_CRUZADA = "CROSS_STANDARD_INTERPRETATION_REQUIRED"
LIGADURA_CRUZADA = "CROSS_STANDARD_CONTROL_BINDING_REQUIRED"
ESTADO_OFICIAL_SIN_RESOLVER = "OFFICIAL_STATUS_UNRESOLVED"
WAF_SIN_CONTEXTO = "WAF_FORM_CONTEXT_REQUIRED"
MAPEO_DE_RIESGO_SIN_RESOLVER = "VULNERABILITY_RISK_MAPPING_UNRESOLVED"
ENTREGABLES_INCOMPLETOS = "SECURITY_DELIVERABLES_INCOMPLETE"
CONTEXTO_NORMATIVO_EXTERNO = "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED"

ESTADOS_GLOBALES = (OVERRIDE_SIN_RESOLVER, INTERPRETACION_CRUZADA, LIGADURA_CRUZADA,
                    ESTADO_OFICIAL_SIN_RESOLVER, WAF_SIN_CONTEXTO,
                    MAPEO_DE_RIESGO_SIN_RESOLVER, ENTREGABLES_INCOMPLETOS,
                    CONTEXTO_NORMATIVO_EXTERNO)

# Estados de este modulo, que no son de la lista exigida y se suman a ella.
SIN_EVIDENCIA_DE_CONTROL = "SECURITY_CONTROL_EVIDENCE_MISSING"
SIN_CONTROLES = "SECURITY_RULE_DECLARES_NO_CONTROL"
COLISION_DE_TIPO = "SECURITY_CONTROL_ID_TYPE_COLLISION"
REGLA_DESCONOCIDA = "NORMATIVE_RULE_NOT_FOUND"
CLAVE_INCOHERENTE = "NORMATIVE_RULE_KEY_MISMATCH"
AGENTE_INVALIDO = "NORMATIVE_AGENT_REFERENCE_INVALID"
VERSION_DISTINTA = "NORMATIVE_STANDARD_VERSION_MISMATCH"
MATRIZ_VALIDA = "NORMATIVE_MATRIX_VALID"
MATRIZ_INVALIDA = "NORMATIVE_MATRIX_INVALID"

PASA = "PASS"
FALLA = "FAIL"

# -- la excepcion aprobada por ASI ---------------------------------------------

# Que fuente sostiene cada mitad de una excepcion. Son dos listas y no una porque la
# excepcion exige las DOS cosas: un contrato que diga que el proyecto puede apartarse, y la
# aprobacion de la autoridad que puede permitirselo. Una sola nunca alcanza.
FUENTES_DE_CONTRATO = ("PROJECT_CONTRACT", "GCBA_NORMATIVE", "SIGNED_AGREEMENT")
FUENTES_DE_APROBACION_ASI = ("ASI_APPROVAL",)

# 🔴 Lo local NUNCA cuenta, para ninguna de las dos mitades. Un proyecto que se exime a si
# mismo escribiendo un archivo en su propio repositorio es exactamente lo que el mecanismo de
# excepcion existe para impedir, y una fuente con nombre de estructurada no deja de ser local.
FUENTES_LOCALES = ("PROJECT_LOCAL_CONFIGURATION", "REPOSITORY_CONFIGURATION",
                   "AGENT_STATEMENT", "PROJECT_CONVENTION", "PROJECT_DOCUMENTATION")

CAMPOS_DE_EXCEPCION = ("affectedRules", "contractEvidence", "asiApprovalEvidence", "reason")

# -- Vu9: los mecanismos, sin que ninguno sea el unico -------------------------

# 🔴 Ninguno es obligatorio y ninguno alcanza por definicion: lo que ES0902 exige es mitigar
# el consumo excesivo y sostener la estabilidad del servicio. Cablear "rate limiting" como el
# unico mecanismo compliant seria inventar normativa, y cablear un numero de peticiones por
# minuto seria inventar el umbral ademas.
MECANISMOS_DE_ABUSO = ("RATE_LIMITING", "QUOTA", "ANTI_BOT", "REQUEST_THROTTLING",
                       "RESOURCE_CAP", "GATEWAY_CONTROL", "OTHER_AUTHORITATIVE_MITIGATION")

# -- Vu10: la guia OWASP por tipo de activo ------------------------------------

# Los tres que ES0902 nombra. Un tipo de activo que el estandar no mapea queda sin resolver:
# elegir una guia por parecido es inventarla.
GUIA_OWASP = {"WEB_APPLICATION": "OWASP Top 10",
              "WEB_SERVICE": "OWASP API Security",
              "MOBILE_APPLICATION": "OWASP Mobile Top 10"}
CAMPOS_DE_GUIA = ("reference", "version", "date")

# -- Vu4: lo que NO satisface el vencimiento por inactividad -------------------

# 🔴 El tiempo de vida de un token de OpenID no es un vencimiento por inactividad: uno mide
# cuanto dura la credencial, el otro cuanto hace que la persona no hace nada. ES0902 Vu4 los
# separa a proposito y aceptar el primero como prueba del segundo deja sesiones abiertas.
EVIDENCIA_QUE_NO_ES_INACTIVIDAD = ("OPENID_TOKEN_LIFETIME", "ACCESS_TOKEN_EXPIRY",
                                   "REFRESH_TOKEN_EXPIRY")

_CACHE = {}


class SeguridadInvalida(Exception):
    """La matriz de ES0902 no se carga a medias. Se falla cerrado."""


# -- carga y validacion --------------------------------------------------------

def cargar(desde=None):
    """La matriz como dato. Levanta si no esta o si es de otra version del estandar."""
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        raise SeguridadInvalida("no esta %s" % ARCHIVO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise SeguridadInvalida("%s no se pudo leer: %s" % (ruta, e))
    estado = controlar_version(doc)
    if estado:
        raise SeguridadInvalida(estado)
    return doc


def controlar_version(doc):
    """"" si la matriz es del estandar esperado; el estado del error si no."""
    doc = doc or {}
    if (doc.get("standard") != ESTANDAR or doc.get("version") != VERSION_ESPERADA
            or doc.get("expectedRuleCount") != CANTIDAD_ESPERADA):
        return ("%s: se esperaba %s %s con %d reglas y la matriz dice %s %s con %s. Las reglas "
                "cambian entre versiones, y una clasificacion vieja aplicada a un estandar "
                "nuevo miente sin avisar."
                % (VERSION_DISTINTA, ESTANDAR, VERSION_ESPERADA, CANTIDAD_ESPERADA,
                   doc.get("standard"), doc.get("version"), doc.get("expectedRuleCount")))
    return ""


def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise SeguridadInvalida("no esta %s; la matriz no se valida sin su contrato." % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(doc, desde=None):
    """Lista de errores contra el schema. Vacia es valido."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise SeguridadInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def clave(rule_id):
    """La clave global compuesta. `G1` no identifica nada; `ES0902.G1` si."""
    return "%s%s%s" % (ESTANDAR, SEPARADOR, rule_id)


def validar(doc=None, desde=None):
    """(estado, errores). `NORMATIVE_MATRIX_VALID` o `NORMATIVE_MATRIX_INVALID`.

    Se falla cerrado y se dice CUAL: una regla de menos, una de mas o una repetida se reportan
    con su id. Un conteo que no cierra obliga a comparar dos listas a mano.
    """
    documento = doc if doc is not None else cargar(desde)
    errores = list(validar_schema(documento, desde))
    version = controlar_version(documento)
    if version:
        return MATRIZ_INVALIDA, [version]

    ids = [r.get("id") for r in documento.get("rules", [])]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        errores.append("reglas repetidas: %s" % ", ".join(repetidos))
    faltan = [i for i in INVENTARIO if i not in ids]
    if faltan:
        errores.append("faltan reglas del inventario: %s" % ", ".join(faltan))
    sobran = sorted(set(ids) - set(INVENTARIO), key=lambda i: str(i))
    if sobran:
        errores.append("reglas que no son de %s %s: %s"
                       % (ESTANDAR, VERSION_ESPERADA, ", ".join(str(s) for s in sobran)))
    if len(ids) != CANTIDAD_ESPERADA:
        errores.append("la matriz trae %d reglas y el estandar declara %d"
                       % (len(ids), CANTIDAD_ESPERADA))

    for regla_ in documento.get("rules", []):
        rid = regla_.get("id")
        esperada = clave(rid)
        if regla_.get("ruleKey") != esperada:
            errores.append("%s: %s declara `%s` y le corresponde `%s`"
                           % (CLAVE_INCOHERENTE, rid, regla_.get("ruleKey"), esperada))
        modo = (regla_.get("applicability") or {}).get("mode")
        if modo not in MODOS:
            errores.append("%s declara el modo `%s`, que no existe" % (rid, modo))
        for campo in ("policies", "checks", "reviews"):
            valores = regla_.get(campo) or []
            if len(valores) != len(set(valores)):
                errores.append("%s repite un id en %s" % (rid, campo))

    errores.extend(validar_referencias(documento, desde))
    return (MATRIZ_INVALIDA if errores else MATRIZ_VALIDA), errores


def validar_referencias(doc=None, desde=None):
    """Errores de referencia a agentes, contra el registro. Nunca los crea."""
    documento = doc if doc is not None else cargar(desde)
    from . import registro_agentes as reg
    try:
        registro = reg.cargar(desde or __file__)
    except reg.RegistroInvalido:
        return ["no se pudo leer el registro de agentes: las referencias no se validaron"]
    agentes = {a.get("id") for a in registro.get("agents", [])}
    errores = []
    for regla_ in documento.get("rules", []):
        for aid in regla_.get("primaryAgents") or []:
            if aid not in agentes:
                errores.append("%s: %s nombra a %s, que el registro no declara"
                               % (AGENTE_INVALIDO, regla_.get("id"), aid))
    return errores


def colisiones_de_id(doc=None, desde=None):
    """Un id de control declarado con mas de un tipo. Diagnostico: no invalida la matriz.

    La matriz provista trae una: G2 declara `security-vulnerability-acceptance-threshold` como
    policy y como check. El archivo no se corrige aca -corregir normativa provista es
    inventarla-; se reporta y quien pueda lo arregla en origen.
    """
    documento = doc if doc is not None else cargar(desde)
    tipos = {}
    for regla_ in documento.get("rules", []):
        for campo, tipo in (("policies", "POLICY"), ("checks", "CHECK"), ("reviews", "REVIEW")):
            for cid in regla_.get(campo) or []:
                tipos.setdefault(cid, set()).add(tipo)
    return [{"id": cid, "types": sorted(t), "state": COLISION_DE_TIPO}
            for cid, t in sorted(tipos.items()) if len(t) > 1]


# -- consultas -----------------------------------------------------------------

def reglas(doc=None, desde=None):
    return list((doc if doc is not None else cargar(desde)).get("rules", []))


def regla(rule_id, doc=None, desde=None):
    """La regla, por id local o por clave compuesta. Levanta si no esta."""
    buscado = rule_id or ""
    if buscado.startswith(ESTANDAR + SEPARADOR):
        buscado = buscado[len(ESTANDAR) + len(SEPARADOR):]
    for r in reglas(doc, desde):
        if r.get("id") == buscado:
            return r
    raise SeguridadInvalida("%s: %s" % (REGLA_DESCONOCIDA, rule_id))


def trazabilidad(rule_id, doc=None, desde=None):
    """De donde sale la regla. La clave compuesta viaja con la tupla, no en vez de ella."""
    documento = doc if doc is not None else cargar(desde)
    local = rule_id[len(ESTANDAR) + len(SEPARADOR):] \
        if (rule_id or "").startswith(ESTANDAR + SEPARADOR) else rule_id
    return {"standard": documento.get("standard"), "version": documento.get("version"),
            "sourceDate": documento.get("sourceDate"), "rule": local,
            "ruleKey": clave(local)}


def senales_declaradas(doc=None, desde=None):
    """Los ids de senal que ES0902 declara. El inventario sale de la matriz y de ningun lado mas."""
    ids = set()
    for r in reglas(doc, desde):
        for s in (r.get("applicability") or {}).get("signals") or []:
            ids.add(s)
    return ids


def controles_de(rule_id, doc=None, desde=None):
    """Los ids de control que la regla declara, con su tipo. Policies, checks y reviews."""
    r = regla(rule_id, doc, desde)
    salida = []
    for campo, tipo in (("policies", "POLICY"), ("checks", "CHECK"), ("reviews", "REVIEW")):
        for cid in r.get(campo) or []:
            salida.append({"id": cid, "type": tipo})
    return salida


# -- aplicabilidad -------------------------------------------------------------

def resolver_regla(r, senales):
    """(estado, senales_faltantes) de una regla contra las senales que haya.

    Lo que no esta no se deduce: una senal ausente deja la regla sin resolver, nunca en
    `NOT_APPLICABLE`. Convertir lo ausente en "no aplica" hace desaparecer la regla del
    reporte, y una regla que desaparece no se vuelve a buscar.
    """
    aplic = (r or {}).get("applicability") or {}
    modo = aplic.get("mode")
    if modo == "ALWAYS":
        return APLICABLE, []
    if modo != "CONDITIONAL":
        return EXPRESION_SIN_RESOLVER, []

    declaradas = list(aplic.get("signals") or [])
    if not declaradas:
        return EXPRESION_SIN_RESOLVER, []
    if len(declaradas) > 1 and not aplic.get("combination"):
        return EXPRESION_SIN_RESOLVER, declaradas

    valores, faltan = [], []
    for s in declaradas:
        v = (senales or {}).get(s)
        if not isinstance(v, bool):
            faltan.append(s)
        else:
            valores.append(v)
    if faltan:
        return SIN_RESOLVER, faltan

    combinacion = aplic.get("combination", "ALL")
    aplica = all(valores) if combinacion == "ALL" else any(valores)
    return (APLICABLE if aplica else NO_APLICABLE), []


def resolver(senales, doc=None, desde=None):
    """La resolucion normativa de ES0902. Mismas claves que la de ES0901, a proposito.

    Quien sabe leer un bloque normativo sabe leer los dos. Lo propio de ES0902 -la fecha de
    fuente, las claves compuestas- viaja adentro de `standard` y de cada fila, no como una
    clave de mas arriba que obligue a ramificar por estandar.
    """
    documento = doc if doc is not None else cargar(desde)
    aplicables, no_aplicables, sin_resolver = [], [], []
    policies, checks, reviews = [], [], []

    for r in reglas(documento):
        estado, faltan = resolver_regla(r, senales)
        rid = r.get("id")
        if estado == APLICABLE:
            aplicables.append(rid)
            for campo, acumulador in (("policies", policies), ("checks", checks),
                                      ("reviews", reviews)):
                for cid in r.get(campo) or []:
                    if cid not in acumulador:
                        acumulador.append(cid)
        elif estado == NO_APLICABLE:
            no_aplicables.append(rid)
        else:
            sin_resolver.append({"rule": rid, "ruleKey": clave(rid), "reason": estado,
                                 "missingSignals": faltan})

    return {
        "standard": {"id": documento.get("standard"), "version": documento.get("version"),
                     "section": None, "sourceDate": documento.get("sourceDate")},
        "applicableRules": sorted(aplicables, key=_orden),
        "notApplicableRules": sorted(no_aplicables, key=_orden),
        "unresolvedRules": sorted(sin_resolver, key=lambda u: _orden(u["rule"])),
        "declaredPolicies": sorted(policies),
        "declaredChecks": sorted(checks),
        "declaredReviews": sorted(reviews),
        "evidence": {"signals": {k: v for k, v in sorted((senales or {}).items())}},
    }


def _orden(rule_id):
    """El orden del estandar, no el alfabetico: O1, O2, C1... G4."""
    try:
        return (INVENTARIO.index(rule_id), rule_id)
    except ValueError:
        return (len(INVENTARIO), str(rule_id))


# -- la excepcion aprobada por ASI ---------------------------------------------

def _fuentes(bloque):
    """Las fuentes declaradas de una mitad de la excepcion, como lista de strings."""
    if isinstance(bloque, dict):
        bloque = [bloque]
    salida = []
    for e in bloque or []:
        if isinstance(e, dict):
            salida.append(e.get("source"))
    return salida


def _mitad_sostenida(bloque, admitidas):
    """Si esta mitad tiene al menos una fuente que la sostiene. Lo local no cuenta nunca."""
    for fuente in _fuentes(bloque):
        if fuente in FUENTES_LOCALES:
            continue
        if fuente in admitidas:
            return True
    return False


def excepcion(documento):
    """El resultado de una excepcion: si se concede, a que reglas, y con que respaldo.

    🔴 Las dos mitades o ninguna. Contrato sin aprobacion de ASI no exime; aprobacion de ASI
    sin contrato tampoco. Y la configuracion local del proyecto no es ninguna de las dos: un
    proyecto que se exime a si mismo no tiene excepcion, tiene un archivo.
    """
    doc = documento if isinstance(documento, dict) else {}
    salida = {"granted": False, "state": OVERRIDE_SIN_RESOLVER, "reasons": []}
    for campo in CAMPOS_DE_EXCEPCION:
        valor = doc.get(campo)
        salida[campo] = list(valor) if isinstance(valor, list) else valor

    afectadas = [r for r in (doc.get("affectedRules") or []) if isinstance(r, str)]
    if not afectadas:
        salida["reasons"].append("la excepcion no nombra ninguna regla en `affectedRules`")

    contrato = _mitad_sostenida(doc.get("contractEvidence"), FUENTES_DE_CONTRATO)
    asi = _mitad_sostenida(doc.get("asiApprovalEvidence"), FUENTES_DE_APROBACION_ASI)
    if not contrato:
        salida["reasons"].append("no hay evidencia de contrato de una fuente que alcance; lo "
                                 "local del proyecto no exime")
    if not asi:
        salida["reasons"].append("no hay evidencia de aprobacion de ASI")
    if not (doc.get("reason") or "").strip():
        salida["reasons"].append("la excepcion no dice por que")

    if contrato and asi and afectadas and not salida["reasons"]:
        salida["granted"] = True
        salida["state"] = None
        salida["affectedRules"] = list(afectadas)
    return salida


def excepcion_de(rule_id, excepciones):
    """La excepcion concedida que alcanza a esta regla, o `None`.

    Alcanza solo a las reglas que nombra. Una excepcion no derrama: exceptuar Vu2 no exceptua
    Vu3 aunque las dos sean principios de seguridad del mismo capitulo.
    """
    local = rule_id[len(ESTANDAR) + len(SEPARADOR):] \
        if (rule_id or "").startswith(ESTANDAR + SEPARADOR) else rule_id
    for doc in excepciones or []:
        resuelta = excepcion(doc)
        if not resuelta.get("granted"):
            continue
        nombradas = set(resuelta.get("affectedRules") or [])
        if local in nombradas or clave(local) in nombradas:
            return resuelta
    return None


# -- el resultado de una regla -------------------------------------------------

def _base(rid, documento):
    return {"rule": rid, "ruleKey": clave(rid), "result": RESULTADO_SIN_RESOLVER,
            "states": [], "reasons": [],
            "source": {"standard": documento.get("standard"),
                       "version": documento.get("version"), "rule": rid}}


def _generico(r, evidencia, salida):
    """El resultado por defecto: hallazgos, controles en FAIL, controles sin evidencia."""
    declarados = [c for campo in ("policies", "checks", "reviews")
                  for c in (r.get(campo) or [])]
    if not declarados:
        # Cumplir sobre el conjunto vacio es la forma mas barata de que una regla salga verde.
        salida["states"].append(SIN_CONTROLES)
        salida["reasons"].append("la regla no declara ningun control: no hay contra que medir")
        return salida

    rid = r.get("id")
    abiertos = [f for f in (evidencia.get("findings") or [])
                if _cita(f, rid) and (f.get("status") or "OPEN") != "CLOSED"]
    if abiertos:
        salida["result"] = NO_CUMPLE
        salida["reasons"].append("hay %d hallazgo(s) abierto(s) que citan la regla: %s"
                                 % (len(abiertos),
                                    ", ".join(str(f.get("id")) for f in abiertos)))
        return salida

    resultados = evidencia.get("controlResults") or {}
    fallados = [c for c in declarados if (resultados.get(c) or {}).get("result") == FALLA]
    if fallados:
        salida["result"] = NO_CUMPLE
        salida["reasons"].append("controles en FAIL: %s" % ", ".join(sorted(fallados)))
        return salida

    faltan = [c for c in declarados
              if (resultados.get(c) or {}).get("result") != PASA
              or not (resultados.get(c) or {}).get("evidence")]
    if faltan:
        salida["states"].append(SIN_EVIDENCIA_DE_CONTROL)
        salida["reasons"].append("sin evidencia de PASS: %s" % ", ".join(sorted(faltan)))
        return salida

    salida["result"] = CUMPLE
    return salida


def _cita(hallazgo, rid):
    """Si un hallazgo cita esta regla. Acepta el id local y la clave compuesta."""
    citada = (hallazgo or {}).get("rule")
    return citada in (rid, clave(rid))


# -- los cuatro algoritmos que viven aca ---------------------------------------

def _ve2(r, evidencia, salida):
    """Una version mas nueva no se vuelve permitida por ser mas nueva."""
    consenso = evidencia.get("infrastructureConsensus")
    if not _con_evidencia(consenso):
        salida["states"].append(CONTEXTO_NORMATIVO_EXTERNO)
        salida["reasons"].append("una version mas nueva, o alegada mas segura, exige consenso "
                                 "de Infraestructura con evidencia antes de usarse")
        return salida
    return _generico(r, evidencia, salida)


def _vu4(r, evidencia, salida):
    """El vencimiento por inactividad se mide solo, no por el tiempo de vida del token."""
    declarada = evidencia.get("inactivityTimeout")
    prestada = [e for e in _evidencias(declarada)
                if e.get("kind") in EVIDENCIA_QUE_NO_ES_INACTIVIDAD]
    propia = [e for e in _evidencias(declarada)
              if e.get("kind") not in EVIDENCIA_QUE_NO_ES_INACTIVIDAD]
    if prestada and not propia:
        salida["states"].append(SIN_EVIDENCIA_DE_CONTROL)
        salida["reasons"].append("el tiempo de vida del token no prueba el vencimiento por "
                                 "inactividad: son dos cosas distintas y ES0902 las separa")
        return salida
    if not propia:
        salida["states"].append(SIN_EVIDENCIA_DE_CONTROL)
        salida["reasons"].append("no hay evidencia propia del vencimiento por inactividad")
        return salida
    return _generico(r, evidencia, salida)


def _vu9(r, evidencia, salida):
    """Mitigar el consumo excesivo. Cualquier mecanismo con evidencia, ninguno obligatorio."""
    declarados = [m for m in _evidencias(evidencia.get("abuseControls"))
                  if m.get("mechanism") in MECANISMOS_DE_ABUSO and m.get("evidence")]
    if not declarados:
        salida["result"] = NO_CUMPLE
        salida["reasons"].append("interfaz publica sin autenticar y sin ningun mecanismo de "
                                 "control de abuso con evidencia")
        return salida
    salida["mechanisms"] = sorted({m.get("mechanism") for m in declarados})
    # 🔴 El umbral sale del contrato del proyecto o de la plataforma, o no sale. ES0902 no da
    # un numero y el que lo invente queda escrito como si fuera normativo.
    contrato = evidencia.get("platformContract") or {}
    if isinstance(contrato, dict) and contrato.get("threshold") is not None:
        salida["threshold"] = {"value": contrato.get("threshold"),
                               "source": contrato.get("source")}
    return _generico(r, evidencia, salida)


def _vu10(r, evidencia, salida):
    """La guia OWASP se resuelve por tipo de activo, con referencia, version y fecha."""
    tipos = [t for t in (evidencia.get("assetTypes") or []) if isinstance(t, str)]
    sin_mapeo = [t for t in tipos if t not in GUIA_OWASP]
    esperadas = sorted({GUIA_OWASP[t] for t in tipos if t in GUIA_OWASP})
    salida["expectedGuidance"] = esperadas
    if sin_mapeo:
        salida["states"].append(CONTEXTO_NORMATIVO_EXTERNO)
        salida["reasons"].append("ES0902 no mapea guia OWASP para: %s" % ", ".join(sorted(sin_mapeo)))
    if not esperadas:
        return salida

    citadas = {}
    incompletas = []
    for g in _evidencias(evidencia.get("owaspGuidance")):
        referencia = g.get("reference")
        if not all(g.get(c) for c in CAMPOS_DE_GUIA):
            incompletas.append(referencia)
            continue
        citadas[referencia] = {c: g.get(c) for c in CAMPOS_DE_GUIA}
    salida["guidance"] = {k: citadas[k] for k in sorted(citadas)}
    if incompletas:
        salida["states"].append(CONTEXTO_NORMATIVO_EXTERNO)
        salida["reasons"].append("referencia OWASP sin version o sin fecha: %s"
                                 % ", ".join(sorted(str(i) for i in incompletas)))
    faltan = [g for g in esperadas if g not in citadas]
    if faltan:
        salida["states"].append(CONTEXTO_NORMATIVO_EXTERNO)
        salida["reasons"].append("falta la guia OWASP que corresponde al tipo de activo: %s"
                                 % ", ".join(faltan))
        return salida
    if salida["states"]:
        return salida
    return _generico(r, evidencia, salida)


def _evidencias(bloque):
    """Lo que venga -un dict, una lista, nada- como lista de dicts."""
    if isinstance(bloque, dict):
        bloque = [bloque]
    return [e for e in (bloque or []) if isinstance(e, dict)]


def _con_evidencia(bloque):
    return any(e.get("evidence") for e in _evidencias(bloque))


# -- los cuatro que viven en evaluacion.py -------------------------------------

def _delegado(nombre, modulo="evaluacion"):
    def envoltorio(r, evidencia, salida):
        from importlib import import_module
        return getattr(import_module("." + modulo, __package__), nombre)(r, evidencia, salida)
    envoltorio.__name__ = nombre
    return envoltorio


# 🔴 Las diez reglas con algoritmo propio, en un solo lugar. El resto es generico, y una rama
# por id que no este aca es el estandar reinterpretandose en el codigo.
ALGORITMOS = {
    "O1": _delegado("regla_o1", "linea_base"),
    "C2": _delegado("regla_c2"),
    "C3": _delegado("regla_c3", "estandar_de_desarrollo"),
    "Ve2": _ve2,
    "Vu4": _vu4,
    "Vu9": _vu9,
    "Vu10": _vu10,
    "G2": _delegado("regla_g2"),
    "G3": _delegado("regla_g3"),
    "G4": _delegado("regla_g4"),
}


def resultado(rule_id, evidencia=None, senales=None, doc=None, desde=None):
    """El resultado de una regla: aplicabilidad, excepcion, algoritmo propio, generico.

    El orden importa. La aplicabilidad primero -una regla que no aplica no tiene resultado-,
    despues la excepcion -que levanta la obligacion y deja escrito con que respaldo-, despues
    el algoritmo si la regla tiene uno, y recien ahi lo generico.
    """
    documento = doc if doc is not None else cargar(desde)
    r = regla(rule_id, documento, desde)
    rid = r.get("id")
    salida = _base(rid, documento)
    ev = evidencia if isinstance(evidencia, dict) else {}

    estado, faltan = resolver_regla(r, senales or {})
    salida["applicability"] = estado
    if estado == NO_APLICABLE:
        salida["result"] = NO_APLICABLE
        return salida
    if estado != APLICABLE:
        salida["reasons"].append("no se pudo decidir si aplica; faltan senales: %s"
                                 % (", ".join(faltan) if faltan else "-"))
        salida["missingSignals"] = faltan
        return salida

    pedidas = ev.get("overrides") or []
    concedida = excepcion_de(rid, pedidas)
    if concedida:
        salida["result"] = EXCEPTUADA
        salida["override"] = concedida
        return salida
    for pedida in pedidas:
        sin_conceder = excepcion(pedida)
        nombradas = set(sin_conceder.get("affectedRules") or [])
        if rid in nombradas or clave(rid) in nombradas:
            salida["states"].append(OVERRIDE_SIN_RESOLVER)
            salida["reasons"].extend(sin_conceder.get("reasons") or [])

    algoritmo = ALGORITMOS.get(rid)
    if algoritmo is not None:
        salida = algoritmo(r, ev, salida)
    else:
        salida = _generico(r, ev, salida)

    if salida.get("result") == CUMPLE and salida.get("states"):
        # Un estado sin resolver nunca convive con un cumplimiento: si algo quedo abierto, la
        # regla no cumple todavia.
        salida["result"] = RESULTADO_SIN_RESOLVER
    return salida


def resultados(evidencia=None, senales=None, doc=None, desde=None):
    """El resultado de las 21 reglas, en el orden del estandar."""
    documento = doc if doc is not None else cargar(desde)
    return [resultado(r.get("id"), evidencia, senales, documento, desde)
            for r in sorted(reglas(documento), key=lambda x: _orden(x.get("id")))]


def controles_no_instalados(resolucion, policies_instaladas=None, checks_instalados=None,
                            reviews_instaladas=None, desde=None):
    """Que exige lo aplicable y todavia no existe. Lo resuelve el mismo codigo que ES0901."""
    from . import matriz
    return matriz.controles_no_instalados(resolucion, policies_instaladas, checks_instalados,
                                          reviews_instaladas, desde)
