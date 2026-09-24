"""Check normativo: todo mensaje de error que ve un consumidor esta customizado.

    source: ES0902 / 6.2 / 6 / Vu6

    "Todos los mensajes de error deben estar customizados."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Superficie por superficie, y escenario por escenario.** Una pantalla prolija no tapa un payload
de API con el stack trace, y un escenario en verde no tapa otro de la misma superficie. Cada
superficie del alcance tiene que traer su error inesperado, porque es el camino por el que sale la
pagina por defecto.

🔴 **El comportamiento, no el manejador.** Lo unico que sostiene que ve el consumidor es evidencia de
comportamiento: un mapeo del manejador que nombra la superficie y el tipo de error, un test, una
prueba segura o una observacion de la salida. Que exista un manejador central, que un framework sea
el dueno, el codigo fuente o la configuracion, solos, no.

🔴 **Ninguna palabra decide.** El modulo no busca `Exception`, `at java.` ni nada en ningun texto. La
clasificacion sale de lo que establece cada evidencia, y la salida lleva ids y estados, nunca el
texto de una evidencia.

🔴 **El log no es el mensaje.** Un `INTERNAL_LOG` ni enciende la senal ni hace FAIL. Un
`INTERNAL_DIAGNOSTIC_FORWARDED` si es exposicion, diga lo que diga su `value`: el diagnostico
llega al consumidor, y nunca sostiene un mensaje customizado.

🔴 **El 200 amable es enmascarar.** Un error inesperado respondido con 2xx o 3xx es
`HTTP_ERROR_SEMANTICS_MASKED`; la fuente de apoyo es ES0901 §11, citada y no evaluada. Para otro tipo
de error, solo con un contrato de API citado. Ningun codigo exacto se exige.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Una prueba insegura o
sin objetivo no aprueba ni hace FAIL. El modulo no ejecuta nada: lee la evidencia de una prueba ya
hecha.
"""
import importlib.util
import io
import json
import os
import sys

_CONTROLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN = os.path.join(os.path.dirname(_CONTROLES), "bin")
if _BIN not in sys.path:
    sys.path.insert(0, _BIN)
if os.path.join(_CONTROLES, "lib") not in sys.path:
    sys.path.insert(0, os.path.join(_CONTROLES, "lib"))

import rutas                                        # noqa: E402
import evidencia as _ev                             # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "custom-error-message-compliance"
POLICY = "custom-error-messages-required"
TIPO = "CHECK"
REGLA = "Vu6"
CLAVE = "ES0902.Vu6"
SENAL = "userFacingErrorPresent"

ARCHIVO = "custom-error-message-evidence.json"
SCHEMA = "custom-error-message-evidence.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = "Todos los mensajes de error deben estar customizados."

# 🔴 Fuente de apoyo, citada y no evaluada: ningun resultado de ES0901 entra ni sale de este check.
FUENTE_DE_APOYO = {"standard": "ES0901", "version": "6.3", "section": "11", "page": 22,
                   "title": "Errores HTTP no enmascarados",
                   "extract": "normativa/extractos/ES0901.md",
                   "role": "SUPPORTING_SOURCE"}


# 🔴 Las superficies que hay que cubrir incluyen las de C1, leidas con su cargador. Se importa el
# modulo; no se corre su evaluacion.
def _modulo(archivo, alias):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_SUPERFICIES = _modulo("oidc-keycloak-integration.py", "_vu6_inventario_de_superficies")

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "ERROR_SURFACE_COVERAGE_UNRESOLVED"
POR_DEFECTO = "DEFAULT_ERROR_EXPOSED"
CRUDO = "RAW_TECHNICAL_ERROR_EXPOSED"
INFRAESTRUCTURA = "INFRASTRUCTURE_DETAIL_EXPOSED"
SIN_CUSTOMIZADO = "ERROR_CUSTOMIZATION_UNRESOLVED"
ENMASCARADO = "HTTP_ERROR_SEMANTICS_MASKED"
PRUEBA_INSEGURA = "ERROR_MESSAGE_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_COBERTURA, POR_DEFECTO, CRUDO,
           INFRAESTRUCTURA, SIN_CUSTOMIZADO, ENMASCARADO, PRUEBA_INSEGURA, SIN_OBJETIVO)
# Las formas de fallar. El agregado informa la de la falla.
EXPOSICIONES = (POR_DEFECTO, CRUDO, INFRAESTRUCTURA)
FALLAS = (FALLA,) + EXPOSICIONES + (ENMASCARADO,)
RESUELTAS = (PASA, NO_APLICA)
# Sin ninguna falla, el sin resolver que se informa es el primero de este orden: el de los pasos.
ORDEN_DE_LO_ABIERTO = (SIN_CUSTOMIZADO, PRUEBA_INSEGURA, SIN_OBJETIVO)

# -- lo que dice el registro ------------------------------------------------------------

CUSTOMIZADO = "CUSTOMIZED_SAFE"
INESPERADO = "UNEXPECTED_ERROR"
DETECTADO, NINGUNO = "DETECTED", "NONE"
CONSUMIDOR_DE_API = "API_CONSUMER"

# -- lo que establece una evidencia ---------------------------------------------------------

ERROR_VISIBLE = "USER_FACING_ERROR"                   # value PRESENT | ABSENT
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
ALCANCE = "ERROR_SURFACE_SCOPE"                       # values: las superficies
CAMINOS = "ERROR_PATH_SCOPE"                          # targets + errorTypes
SALIDA = "ERROR_OUTPUT"                               # value CUSTOMIZED_SAFE | una exposicion
DETALLE = "TECHNICAL_DETAIL_EXPOSURE"                 # value DETECTED | NONE
CLASE_HTTP = "HTTP_STATUS_CLASS"                      # value 1xx .. 5xx
SUPERFICIE_HTTP = "HTTP_SURFACE"                      # targets
CONTRATO = "API_ERROR_CONTRACT"                       # value ERROR
ES_ERROR = "ERROR"
DE_EXITO = ("2xx",)
DE_EXITO_O_REDIRECCION = ("2xx", "3xx")
CLASES_HTTP = ("1xx", "2xx", "3xx", "4xx", "5xx")

CONFIRMADA = "CONFIRMED"
OBSERVADA = "OBSERVED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, OBSERVADA)

# -- que clase sostiene que ------------------------------------------------------------------

PRUEBA = "AUTHORIZED_QA_RUNTIME_TEST"
MAPEO_DEL_MANEJADOR = "ERROR_HANDLER_MAPPING"
LOG_INTERNO = "INTERNAL_LOG"
REENVIADO = "INTERNAL_DIAGNOSTIC_FORWARDED"
# 🔴 Las unicas que sostienen que ve el consumidor. Las tablas son del harness, no del estandar.
DE_COMPORTAMIENTO = (MAPEO_DEL_MANEJADOR, "UNIT_TEST", "INTEGRATION_TEST", "CONTRACT_TEST", PRUEBA,
                     "EXPOSED_OUTPUT_OBSERVATION", REENVIADO, "ASSESSMENT_FINDING",
                     "OTHER_AUTHORITATIVE_EVIDENCE")
# Las que no sostienen nada, nombradas para que la salida diga por que.
INSUFICIENTES = ("ERROR_HANDLER_PRESENCE", "FRAMEWORK_OWNERSHIP", "SOURCE_CODE", "CONFIGURATION",
                 LOG_INTERNO, "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT")
AUTORIDADES = ("ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT", "PROJECT_CONTRACT",
               "API_CONTRACT", "OFFICIAL_ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")

# Lo que una evidencia dice de un escenario. Si la dice una clase que no sostiene, no cuenta.
DEL_ESCENARIO = (SALIDA, DETALLE, CLASE_HTTP)

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "targets": _ev.LISTA, "scenarios": _ev.LISTA,
         "errorTypes": _ev.LISTA, "value": _ev.TEXTO, "values": _ev.LISTA,
         "outcome": _ev.TEXTO, "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO,
         "syntheticData": _ev.BOOLEANO, "destructive": _ev.BOOLEANO,
         "infrastructureOutageInduced": _ev.BOOLEANO, "realPersonalData": _ev.BOOLEANO,
         "realSecrets": _ev.BOOLEANO, "rawSecretsLogged": _ev.BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def catalogo(caso):
    """El catalogo de `evidencia.py`, sin nada agregado."""
    return _ev.catalogo(caso, FORMA, OBLIGATORIOS)


def prueba_segura(e):
    """Los motivos por los que una prueba no era segura. Vacio es segura. No ejecuta nada.

    Ninguna condicion exige provocar una caida ni usar datos reales: un error de validacion, un
    recurso inexistente o una peticion invalida, con datos sinteticos, alcanzan."""
    motivos = []
    if e.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    ambiente = e.get("environment")
    if ambiente in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    elif ambiente == PRODUCCION:
        motivos.append("PRODUCTION")
    elif ambiente not in AMBIENTES_DE_PRUEBA:
        motivos.append("ENVIRONMENT_UNKNOWN")
    if e.get("syntheticData") is not True:
        motivos.append("NOT_SYNTHETIC_DATA")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
    if e.get("infrastructureOutageInduced") is True:
        motivos.append("INFRASTRUCTURE_OUTAGE_INDUCED")
    if e.get("realPersonalData") is True:
        motivos.append("REAL_PERSONAL_DATA")
    if e.get("realSecrets") is True:
        motivos.append("REAL_SECRETS")
    if e.get("rawSecretsLogged") is True:
        motivos.append("RAW_SECRETS_LOGGED")
    return sorted(motivos)


def _lectura(e):
    """(cuenta, bloqueo, motivos). La misma compuerta para lo que dice que si y que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO, []
        motivos = prueba_segura(e)
        if motivos:
            return False, PRUEBA_INSEGURA, motivos
    return e.get("outcome") in LEIBLES, None, []


def _citada(e, citados):
    return _ev.id_de(e) in citados


def _nombra(e, sid, escenario):
    """Si el item habla de ESTE escenario de ESTA superficie.

    Lo nombra por su id, o por su tipo de error con la superficie. Un mapeo del manejador nombra
    siempre las dos cosas, superficie y tipo de error. Un item que nombra otras superficies u otros
    escenarios, y no estos, habla de otra cosa."""
    objetivos, escenarios, tipos = e.get("targets"), e.get("scenarios"), e.get("errorTypes")
    if objetivos and not _ev.en(sid, objetivos):
        return False
    if escenarios and not _ev.en(escenario.get("scenarioId"), escenarios):
        return False
    if tipos and not _ev.en(escenario.get("errorType"), tipos):
        return False
    por_tipo = _ev.en(sid, objetivos) and _ev.en(escenario.get("errorType"), tipos)
    if e["sourceType"] == MAPEO_DEL_MANEJADOR:
        return por_tipo
    return bool(escenarios) or por_tipo


def _afirmaciones(e, sid, escenario):
    """Lo que un item legible de comportamiento dice del escenario, como (que, valor)."""
    dice = set()
    # 🔴 Un diagnostico interno reenviado no afirma nada por su `value`: es exposicion, y la
    # juzga `_reenviados`. Nunca sostiene un CUSTOMIZED_SAFE (refutador de Vu6, pase 1).
    if (e["sourceType"] not in DE_COMPORTAMIENTO or e["sourceType"] == REENVIADO
            or not _lectura(e)[0]):
        return dice
    if not _nombra(e, sid, escenario):
        return dice
    establece = e["establishes"]
    if SALIDA in establece and e.get("value") in (CUSTOMIZADO,) + EXPOSICIONES:
        dice.add(("output", e["value"]))
    if DETALLE in establece and e.get("value") in (DETECTADO, NINGUNO):
        dice.add(("detail", e["value"]))
    if CLASE_HTTP in establece and e.get("value") in CLASES_HTTP:
        dice.add(("status", e["value"]))
    return dice


# -- los registros ------------------------------------------------------------------------------

def cargar(desde=None):
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "surfaces": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return None
    from orquestacion import tools
    armador = tools._armador()
    if armador is None:
        return None
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def entradas(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del registro instalado."""
    declarado = (caso or {}).get("surfaces")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el registro de mensajes de error no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de mensajes de error no se pudo validar"
    if errores:
        return [], ("el registro de mensajes de error no valida contra su schema: %d errores"
                    % len(errores))
    return list(doc.get("surfaces") or []), ""


def interfaces(caso):
    """Los `interface_id` de `interfaces.items[]` del contexto de proyecto, en NFC."""
    contexto = (caso or {}).get("projectContext")
    bloque = contexto.get("interfaces") if isinstance(contexto, dict) else None
    items = bloque.get("items") if isinstance(bloque, dict) else None
    if not isinstance(items, list):
        return set()
    return {_ev.nfc(i["interface_id"]) for i in items
            if isinstance(i, dict) and isinstance(i.get("interface_id"), str)
            and i["interface_id"].strip()}


def _citas(superficie, escenario=None):
    """Los ids que cita una superficie, o un escenario con su superficie, en NFC."""
    citados = _ev.claves(superficie.get("evidence"))
    for s in ([escenario] if escenario is not None else superficie.get("scenarios") or []):
        citados |= _ev.claves(s.get("evidence")) | _ev.claves([s.get("httpStatusRef")])
    return citados


def _presencias(superficie, cat, citados):
    """Lo citado y legible que establece un error visible en la superficie, sin ser un log interno.

    La cita la ata a la superficie. Un item que nombra otras superficies, y no esta, habla de otra."""
    sid = superficie.get("surfaceId")
    return sorted(e["evidenceId"] for e in cat.values()
                  if ERROR_VISIBLE in e["establishes"] and e.get("value") == PRESENTE
                  and e["sourceType"] != LOG_INTERNO and _citada(e, citados) and _lectura(e)[0]
                  and (not e.get("targets") or _ev.en(sid, e.get("targets"))))


def _tipos_exigidos(sid, cat, citados):
    """Los tipos de error que una evidencia autoritativa citada `ERROR_PATH_SCOPE` exige a la
    superficie, en NFC. El error inesperado se exige siempre."""
    tipos = {INESPERADO}
    for e in cat.values():
        if (CAMINOS in e["establishes"] and e["sourceType"] in AUTORIDADES and _citada(e, citados)
                and _lectura(e)[0] and _ev.en(sid, e.get("targets"))):
            tipos |= {_ev.nfc(t) for t in e.get("errorTypes") or []}
    return tipos


# -- la senal y la cobertura -----------------------------------------------------------------------

HAY, NO_HAY, NO_SE = "USER_FACING_ERROR", "NO_USER_FACING_ERROR", "UNRESOLVED"


def derivar(caso, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    lista, problema = _SUPERFICIES.superficies(entrada, desde)
    registradas, problema_registro = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    citados = set()
    for s in registradas:
        citados |= _citas(s)
    # 🔴 Los ids se normalizan UNA vez, antes de contar (Vu2, tercer pase).
    del_inventario = sorted({_ev.nfc(s.get("surfaceId")) for s in lista
                             if isinstance(s.get("surfaceId"), str)})
    de_alcance = [e for e in cat.values()
                  if ALCANCE in e["establishes"] and _citada(e, citados) and _lectura(e)[0]]
    de_evidencia = sorted({_ev.nfc(x) for e in de_alcance for x in e.get("values") or []})
    ids_de_interfaces = interfaces(entrada)
    de_interfaces = sorted({_ev.nfc(x) for e in de_alcance if e["sourceType"] in AUTORIDADES
                            for x in e.get("values") or [] if _ev.nfc(x) in ids_de_interfaces})
    alcance = sorted(set(del_inventario) | set(de_evidencia))
    ids = [_ev.nfc(s.get("surfaceId")) for s in registradas]
    escenarios = [(_ev.nfc(s.get("surfaceId")), _ev.nfc(e.get("scenarioId")))
                  for s in registradas for e in s.get("scenarios") or []]

    superficies, ausentes_citadas, sin_cubrir, faltan_tipos = [], [], [], []
    for sid in alcance:
        propias = [s for s in registradas if _ev.igual(s.get("surfaceId"), sid)]
        sobre = [e for e in cat.values() if ERROR_VISIBLE in e["establishes"]
                 and _ev.en(sid, e.get("targets")) and e["sourceType"] != LOG_INTERNO]
        legibles = [e for e in sobre if _lectura(e)[0]]
        presentes = [e for e in sobre if e.get("value") == PRESENTE]
        ausentes = [e for e in legibles if e.get("value") == AUSENTE and e["sourceType"] in AUTORIDADES]
        enciende = any(_presencias(s, cat, _citas(s)) for s in propias)
        con_escenarios = any(s.get("scenarios") for s in propias)
        ilegibles = _ev.ilegibles_sobre(sid, cat, crudas)
        if enciende:
            estado = HAY
        elif ausentes and not con_escenarios and not presentes and not ilegibles:
            estado = NO_HAY
        else:
            estado = NO_SE
        # Cubierta: con una entrada que trae el error inesperado y cada tipo que un ERROR_PATH_SCOPE
        # citado exige, o con una ausencia autoritativa y legible que nada contradice. Si hay
        # entrada, la ausencia se cita desde ella; si no, no hay desde donde citarla.
        desde_la_entrada = set()
        for s in propias:
            desde_la_entrada |= _citas(s)
        valen = [e for e in ausentes if not propias or _citada(e, desde_la_entrada)]
        if con_escenarios:
            traidos = {_ev.nfc(e.get("errorType")) for s in propias for e in s.get("scenarios") or []}
            faltan = sorted(str(t) for t in _tipos_exigidos(sid, cat, desde_la_entrada) - traidos)
            if faltan:
                sin_cubrir.append(sid)
                faltan_tipos.append({"surfaceId": sid, "errorTypes": faltan})
        elif valen and not presentes and not ilegibles:
            ausentes_citadas.append(sid)
        else:
            sin_cubrir.append(sid)
        superficies.append({"surfaceId": sid, "userFacingError": estado})

    fuera = sorted({str(i) for i in ids if i not in alcance})
    cobertura = {
        "scope": [str(s) for s in alcance], "fromInventory": [str(s) for s in del_inventario],
        "fromScopeEvidence": [str(s) for s in de_evidencia],
        "fromProjectInterfaces": [str(s) for s in de_interfaces],
        "registered": sorted({str(i) for i in ids}),
        "duplicatedSurfaces": sorted({str(i) for i in ids if ids.count(i) > 1}),
        "duplicatedScenarios": sorted({"%s/%s" % par for par in escenarios
                                       if escenarios.count(par) > 1}),
        "surfacesOutsideScope": fuera,
        "uncovered": [str(s) for s in sin_cubrir],
        "missingErrorTypes": faltan_tipos,
        "absent": [str(s) for s in ausentes_citadas],
        "registryUnreadable": bool(problema_registro)}
    completa = not (problema or problema_registro or cobertura["duplicatedSurfaces"]
                    or cobertura["duplicatedScenarios"])
    presentes_en_el_registro = [s for s in registradas if _presencias(s, cat, _citas(s))]
    if problema:
        valor = _senales.SIN_RESOLVER
    elif presentes_en_el_registro:
        valor = _senales.VERDADERA
    elif (superficies and completa and not escenarios and not fuera and not sin_cubrir
          and all(s["userFacingError"] == NO_HAY for s in superficies)):
        valor = _senales.FALSA
    else:
        # Tambien un alcance vacio: el vacio no es FALSE.
        valor = _senales.SIN_RESOLVER
    return {"value": valor, "surfaces": superficies, "inventory": lista, "registry": registradas,
            "coverage": cobertura, "complete": completa, "problem": problema,
            "registryProblem": problema_registro, "catalog": cat, "raw": crudas,
            "repeated": repetidos, "malformed": torcidas, "cited": citados,
            "present": presentes_en_el_registro}


def senal(caso, desde=None):
    d = derivar(caso, desde)
    evidencia = []
    if d["value"] == _senales.VERDADERA:
        for s in d["present"]:
            evidencia.append({"evidenceId": "surface:%s" % s.get("surfaceId"),
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "%s#%s" % (ARCHIVO, s.get("surfaceId")),
                              "claim": "la superficie `%s` muestra un error a un consumidor, con "
                                       "evidencia" % s.get("surfaceId"),
                              "supports": d["value"]})
    elif d["value"] == _senales.FALSA:
        for s in d["surfaces"]:
            evidencia.append({"evidenceId": "surface:%s" % s["surfaceId"],
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "error-surface#%s" % s["surfaceId"],
                              "claim": "una evidencia autoritativa establece que la superficie `%s` "
                                       "no muestra errores a ningun consumidor" % s["surfaceId"],
                              "supports": d["value"]})
    return _ev.depurar(_senales.producir(SENAL, _ev.ordenadas(evidencia), {"type": "DETERMINISTIC"},
                                         d["value"], desde))


def _combinar(derivado, externo):
    if externo is None:
        return derivado
    valor = _SUPERFICIES._valor_de_senal(externo)
    if valor == derivado:
        return valor
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- el bloqueo, uno solo ----------------------------------------------------------------------

def _dice_que_no(e):
    """Si el item dice que algo se expone o se enmascara: pesa aunque no se lo cite."""
    return ((SALIDA in e["establishes"] and e.get("value") in EXPOSICIONES)
            or (DETALLE in e["establishes"] and e.get("value") == DETECTADO)
            or (CLASE_HTTP in e["establishes"] and e.get("value") in DE_EXITO_O_REDIRECCION))


def _bloqueos(cat, citados, sid=None, escenario=None, registradas=(), alcance=()):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan: las que se citan, o las que
    dicen que no. Con `escenario`, las que lo nombran; sin el, las que nombran una superficie del
    registro o del alcance y ningun escenario registrado.

    🔴 Una prueba que nombra solamente algo que no esta en el registro ni en el alcance no mueve
    nada, y una ajena e insegura que dice que el mensaje esta customizado tampoco."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        if escenario is not None and not _nombra(dict(e, sourceType=None), sid, escenario):
            continue
        if escenario is None and (any(_nombra(dict(e, sourceType=None), s, x) for s, x in registradas)
                                  or not any(_ev.en(s, e.get("targets")) for s in alcance)):
            continue
        _, bloqueo, m = _lectura(e)
        if bloqueo and (_citada(e, citados) or _dice_que_no(e)):
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return SIN_CUSTOMIZADO


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan el escenario, el PASS y el NOT_APPLICABLE.

    Lo que no se pudo leer y pesa impide el PASS y tambien el NOT_APPLICABLE; un FAIL no se toca:
    bloquear impide aprobar, no tapa lo que falla. Tampoco reemplaza un sin resolver que ya estaba:
    ese es el estado que sale, y el del bloqueo queda en `states`."""
    if estado in FALLAS or estado not in RESUELTAS:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), ("una prueba que se cita, o que dice que el error se expone, no "
                                    "se pudo leer")
    if ilegibles:
        return SIN_CUSTOMIZADO, ("hay evidencia ilegible sobre la superficie o el escenario, y esa "
                                 "podia ser la que decia que el error se expone")
    return estado, motivo


# -- un escenario, en el orden de la spec -----------------------------------------------------

def _ids(cat, sid, escenario, que, valores, citados=None):
    """Los ids de lo legible de comportamiento que afirma `que` con uno de `valores`."""
    return sorted(e["evidenceId"] for e in cat.values()
                  if any((que, x) in _afirmaciones(e, sid, escenario) for x in valores)
                  and (citados is None or _citada(e, citados)))


def _exposicion_de(ids_por_estado):
    """El estado de la exposicion: el unico que hay, o FAIL si son varios."""
    estados = sorted(k for k, v in ids_por_estado.items() if v)
    return estados[0] if len(estados) == 1 else FALLA


def _reenviados(cat, sid, escenario, citados=None):
    """Los `INTERNAL_DIAGNOSTIC_FORWARDED` legibles sobre el escenario: diga lo que diga su `value`,
    el diagnostico interno llega al consumidor, y eso es `RAW_TECHNICAL_ERROR_EXPOSED`.

    Citado, alcanza con que no nombre otra superficie, otro escenario ni otro tipo de error: la cita
    lo ata. No citado, tiene que nombrar la superficie o el escenario."""
    def de_este(e):
        objetivos, escenarios, tipos = e.get("targets"), e.get("scenarios"), e.get("errorTypes")
        if objetivos and not _ev.en(sid, objetivos):
            return False
        if escenarios and not _ev.en(escenario.get("scenarioId"), escenarios):
            return False
        if tipos and not _ev.en(escenario.get("errorType"), tipos):
            return False
        return citados is not None or bool(objetivos or escenarios)
    return sorted(e["evidenceId"] for e in cat.values()
                  if e["sourceType"] == REENVIADO and _lectura(e)[0] and de_este(e)
                  and (citados is None or _citada(e, citados)))


def _paso_exposicion(sid, escenario, cat, citados, salida, _):
    por_estado = {x: _ids(cat, sid, escenario, "output", (x,), citados) for x in EXPOSICIONES}
    por_estado[CRUDO] = sorted(set(por_estado[CRUDO]) | set(_reenviados(cat, sid, escenario,
                                                                         citados)))
    detalle = _ids(cat, sid, escenario, "detail", (DETECTADO,), citados)
    por_estado[INFRAESTRUCTURA] = sorted(set(por_estado[INFRAESTRUCTURA]) | set(detalle))
    usadas = sorted({i for v in por_estado.values() for i in v})
    # 🔴 La falla establecida gana siempre: diga lo que diga el registro y diga lo que diga otra
    # evidencia. Declarar la falla con honestidad nunca da algo mas blando que declarar que cumple.
    if usadas:
        salida["evidenceUsed"]["exposure"] = usadas
        salida["contradictedBy"].extend(_ids(cat, sid, escenario, "output", (CUSTOMIZADO,)))
        return _exposicion_de(por_estado), ("una evidencia citada de comportamiento establece que el "
                                            "consumidor recibe un error por defecto, crudo o con "
                                            "detalle de infraestructura")
    no_citadas = sorted(set(_ids(cat, sid, escenario, "output", EXPOSICIONES))
                        | set(_ids(cat, sid, escenario, "detail", (DETECTADO,)))
                        | set(_reenviados(cat, sid, escenario)))
    if no_citadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_CUSTOMIZADO, ("una evidencia dice que el error se expone y no se la cita: lo no "
                                 "citado nunca hace FAIL, y tampoco se elige")
    return None, ""


def _paso_customizado(sid, escenario, cat, citados, salida, _):
    declarado = escenario.get("result")
    detalle = escenario.get("technicalDetailExposure")
    if declarado in EXPOSICIONES or detalle == DETECTADO:
        # Declarar la exposicion sin la evidencia que la establece no es FAIL: lo que dice que no
        # pasa por la misma compuerta que lo que dice que si.
        return _abierto(salida["blockedBy"]), ("que el error se exponga no consta con evidencia "
                                               "citada de comportamiento")
    if declarado != CUSTOMIZADO:
        return SIN_CUSTOMIZADO, "no esta establecido que el mensaje de este escenario este customizado"
    if detalle not in (None, NINGUNO):
        return SIN_CUSTOMIZADO, "no esta resuelto si el escenario expone detalle tecnico"
    apoyo = _ids(cat, sid, escenario, "output", (CUSTOMIZADO,), citados)
    if not apoyo:
        return _abierto(salida["blockedBy"]), (
            "que el mensaje este customizado no consta con evidencia citada de comportamiento para "
            "esta superficie y este escenario; un manejador, un framework o la configuracion no "
            "alcanzan")
    salida["evidenceUsed"]["behaviour"] = apoyo
    return None, ""


def _paso_http(sid, escenario, cat, citados, salida, contexto):
    """🔴 Solo sobre una superficie HTTP, y ningun codigo exacto se exige."""
    if not contexto["http"]:
        return None, ""
    exito = _ids(cat, sid, escenario, "status", DE_EXITO_O_REDIRECCION, citados)
    inesperado = _ev.igual(escenario.get("errorType"), INESPERADO)
    if inesperado:
        enmascaran = exito
        no_citadas = _ids(cat, sid, escenario, "status", DE_EXITO_O_REDIRECCION)
    else:
        contrato = sorted(e["evidenceId"] for e in cat.values()
                          if CONTRATO in e["establishes"] and e["sourceType"] in AUTORIDADES
                          and e.get("value") == ES_ERROR and _citada(e, citados) and _lectura(e)[0]
                          and _nombra(dict(e, sourceType=None), sid, escenario))
        if not contrato:
            # Sin contrato no se juzga ningun codigo: seria inventado.
            return None, ""
        salida["evidenceUsed"]["apiContract"] = contrato
        enmascaran = _ids(cat, sid, escenario, "status", DE_EXITO, citados)
        no_citadas = _ids(cat, sid, escenario, "status", DE_EXITO)
    if enmascaran:
        salida["evidenceUsed"]["httpStatus"] = enmascaran
        salida["supportingSource"] = dict(FUENTE_DE_APOYO)
        return ENMASCARADO, ("una evidencia citada establece que un error se responde con un estado de "
                             "exito: customizar el cuerpo no es reemplazar el estado")
    if no_citadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_CUSTOMIZADO, ("una evidencia dice que el estado de error se reemplaza y no se la "
                                 "cita: lo no citado nunca hace FAIL")
    salida["evidenceUsed"]["httpStatus"] = _ids(cat, sid, escenario, "status", CLASES_HTTP, citados)
    return None, ""


PASOS = (_paso_exposicion, _paso_customizado, _paso_http)


def evaluar_escenario(escenario, superficie, d, contexto):
    """Un escenario de una superficie, solo: su estado y la evidencia que lo sostiene, por id."""
    cat, crudas = d["catalog"], d["raw"]
    sid = superficie.get("surfaceId")
    citados = _citas(superficie, escenario)
    salida = {"scenarioId": escenario.get("scenarioId"), "errorType": escenario.get("errorType"),
              "result": escenario.get("result"), "httpStatusRef": escenario.get("httpStatusRef"),
              "technicalDetailExposure": escenario.get("technicalDetailExposure"),
              "verificationMode": escenario.get("verificationMode"),
              "evidenceUsed": {"behaviour": [], "exposure": [], "httpStatus": [],
                               "apiContract": []},
              "contradictedBy": [], "issues": [],
              # Lo citado que dice algo del escenario y no es de una clase que lo sostenga.
              "insufficient": sorted(e["evidenceId"] for e in cat.values()
                                     if e["sourceType"] in INSUFICIENTES and _citada(e, citados)
                                     and set(e["establishes"]) & set(DEL_ESCENARIO))}
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, citados, sid, escenario)
    pasos = [paso(sid, escenario, cat, citados, salida, contexto) for paso in PASOS]
    # 🔴 En el orden de la spec, y lo que falla no lo tapa un paso anterior sin resolver.
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = [p for p in pasos if p[0] is not None]
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | set(_ev.ilegibles_sobre(escenario.get("scenarioId"), cat, crudas))
                       | set(_ev.ilegibles_sobre(sid, cat, crudas)))
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre el escenario o su superficie: %s"
                                % ", ".join(str(i) for i in ilegibles))
    final, motivo = _bloquear(estado, motivo, salida["blockedBy"], ilegibles)
    if final != estado:
        # Lo bloqueado no se sostiene con nada: no queda evidencia usada.
        salida["evidenceUsed"] = {k: [] for k in salida["evidenceUsed"]}
    salida["contradictedBy"] = sorted(set(salida["contradictedBy"]))
    salida["issues"] = sorted(set(salida["issues"]))
    salida["state"] = final
    queda = set(salida["blockedBy"]) if final not in FALLAS else set()
    salida["states"] = sorted(({p[0] for p in pasos if p[0] is not None} | {final} | queda)
                              - {PASA})
    salida["reason"] = motivo
    return salida


def _de_lo_evaluado(estados):
    """(estado, motivo) de un conjunto de estados de escenarios."""
    fallas = sorted({e for e in estados if e in FALLAS})
    if fallas:
        return (fallas[0] if len(fallas) == 1 else FALLA,
                "al menos un escenario falla; los que cumplen no lo tapan")
    abiertos = {e for e in estados if e != PASA}
    for e in ORDEN_DE_LO_ABIERTO:
        if e in abiertos:
            return e, "hay escenarios sin resolver"
    return PASA, ""


def _es_http(superficie, d):
    """API_CONSUMER, o una evidencia citada y legible de que la superficie responde por HTTP: una
    `HTTP_SURFACE` que la nombra, o un `HTTP_STATUS_CLASS` de comportamiento de uno de sus
    escenarios."""
    if superficie.get("consumerType") == CONSUMIDOR_DE_API:
        return True
    sid, cat = superficie.get("surfaceId"), d["catalog"]
    citados = _citas(superficie)
    if any(SUPERFICIE_HTTP in e["establishes"] and _citada(e, citados) and _lectura(e)[0]
           and _ev.en(sid, e.get("targets")) for e in cat.values()):
        return True
    return any(_ids(cat, sid, x, "status", CLASES_HTTP, _citas(superficie, x))
               for x in superficie.get("scenarios") or [])


def evaluar_superficie(superficie, d):
    """Una superficie del registro con sus escenarios. Una superficie en verde no tapa otra."""
    sid = superficie.get("surfaceId")
    contexto = {"http": _es_http(superficie, d)}
    escenarios = _ev.ordenadas(evaluar_escenario(x, superficie, d, contexto)
                               for x in superficie.get("scenarios") or [])
    salida = {"surfaceId": sid, "consumerType": superficie.get("consumerType"),
              "owner": superficie.get("owner"), "http": contexto["http"],
              "inScope": _ev.nfc(sid) in d["coverage"]["scope"], "scenarios": escenarios,
              "issues": []}
    if not salida["inScope"]:
        salida["issues"].append("la superficie `%s` no esta en el inventario de C1 ni en una "
                                "evidencia citada de alcance" % sid)
    if _ev.nfc(sid) in d["coverage"]["uncovered"]:
        salida["issues"].append("a la superficie `%s` le falta el error inesperado o un tipo de "
                                "error que su alcance exige" % sid)
    if escenarios:
        salida["state"], salida["reason"] = _de_lo_evaluado([x["state"] for x in escenarios])
    elif _ev.nfc(sid) in d["coverage"]["absent"]:
        salida["state"], salida["reason"] = NO_APLICA, "la superficie no muestra errores, con evidencia"
    else:
        salida["state"], salida["reason"] = SIN_COBERTURA, ("la superficie no declara escenarios ni "
                                                            "una ausencia citada")
    return salida


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de Vu6, superficie por superficie y escenario por escenario.

    `caso`:

        {"inventory": {...},        # el de C1; opcional
         "surfaces": {...},         # el registro de Vu6; opcional
         "projectContext": {...},   # el contexto de proyecto; sus interfaces entran por el alcance
         "evidence": [...]}         # el catalogo, cerrado
    """
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "supportingSources": [dict(FUENTE_DE_APOYO)],
              "surfaces": [], "issues": [], "coverage": {}}
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    for problema in (d["problem"], d["registryProblem"]):
        if problema:
            salida["issues"].append("el inventario de superficies no valida contra su schema"
                                    if problema.startswith("el inventario de superficies no valida")
                                    else problema)
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    for sid in d["coverage"]["surfacesOutsideScope"]:
        salida["issues"].append("la superficie `%s` no esta en el alcance" % sid)
    salida["issues"].sort()
    salida["coverage"] = d["coverage"]
    registrados = [(s.get("surfaceId"), x) for s in d["registry"] for x in s.get("scenarios") or []]
    sueltos, motivos = _bloqueos(d["catalog"], d["cited"], registradas=registrados,
                                 alcance=sorted(set(d["coverage"]["scope"])
                                                | set(d["coverage"]["registered"])))
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos

    if valor == _senales.SIN_RESOLVER:
        estado, motivo = SIN_APLICABILIDAD, "no consta si hay mensajes de error que vea un consumidor"
    elif valor == _senales.FALSA:
        estado, motivo = NO_APLICA, "ninguna superficie del alcance muestra errores, con evidencia"
    elif d["problem"]:
        estado, motivo = SIN_COBERTURA, "el inventario de superficies no se pudo leer"
    else:
        # 🔴 Cada superficie se evalua sola, tambien la que no esta en el alcance.
        salida["surfaces"] = _ev.ordenadas(evaluar_superficie(s, d) for s in d["registry"])
        estado, motivo = _agregado(salida["surfaces"], d)
    final, motivo = _bloquear(estado, motivo, sueltos, [])
    return _cerrar(salida, final, motivo, estado)


def _agregado(superficies, d):
    estados = [x["state"] for s in superficies for x in s["scenarios"]]
    fallas = sorted({e for e in estados if e in FALLAS})
    if fallas:
        return _de_lo_evaluado(estados)
    c = d["coverage"]
    # Una superficie fuera del alcance tambien: registro y alcance no coinciden (E-60).
    if not d["complete"] or not estados or c["uncovered"] or c["surfacesOutsideScope"]:
        return SIN_COBERTURA, ("no constan todas las superficies de error: sin cubrir %s, fuera del "
                               "alcance %s" % (c["uncovered"] or "-", c["surfacesOutsideScope"] or "-"))
    return _de_lo_evaluado(estados)


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None,) + RESUELTAS:
        todos.add(previo)
    for s in salida["surfaces"]:
        for x in s["scenarios"]:
            todos.update(x.get("states") or [])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


# -- hacia seguridad.resultado ----------------------------------------------------------------------

def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu6", ...)`, desde la salida de `evaluar`.

    Vu6 no tiene algoritmo propio en `seguridad.py`: va por el generico. Los dos controles de la
    fila llevan el estado del check -PASS, FAIL o el estado abierto tal cual- con la evidencia por
    id. Un resultado que no dice ser de este check no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return {}, {}
    estado = r["state"]
    control = FALLA if estado in FALLAS else estado
    ids = set()
    for s in r.get("surfaces") or []:
        for x in s.get("scenarios") or []:
            ids.update(i for u in (x.get("evidenceUsed") or {}).values() for i in u)
    evidencia = sorted(ids) or (["check:%s" % CONTROL] if estado in RESUELTAS + FALLAS else [])
    doc = {"controlResults": {c: {"result": control, "evidence": evidencia}
                              for c in (POLICY, CONTROL)}}
    valor = r.get("signalValue")
    # 🔴 Un NOT_APPLICABLE que el bloqueo impidio no vuelve a entrar por la senal.
    senales = ({SENAL: True} if valor == _senales.VERDADERA
               else {SENAL: False} if valor == _senales.FALSA and estado == NO_APLICA else {})
    return _ev.depurar(doc), senales
