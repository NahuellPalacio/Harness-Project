"""Check normativo: toda validacion del cliente esta espejada en el servidor.

    source: ES0902 / 6.2 / 6 / Vu5

    "Toda validacion del lado del cliente, debe estar espejada del lado del servidor."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Va del cliente al servidor, y solo en esa direccion.** Cada exigencia sale de una validacion del
cliente declarada en el registro. Una validacion que existe solo en el servidor no viola nada y no
se busca.

🔴 **El nombre no es la regla, la libreria no es la ejecucion, el atributo no es la validacion.** Lo
unico que sostiene que el servidor valida es evidencia de enforcement: codigo de validacion del
servidor, un test o una prueba directa segura. Un campo que se llama igual, un DTO, un schema
compartido, un `required` de HTML, un tipo de TypeScript o una mascara del cliente, solos, no.

🔴 **Validar no es autorizar.** Un rechazo por autorizacion, o un 401 o un 403, no prueba que el
servidor valido la entrada. Aparte de eso, ningun codigo de estado y ningun mensaje deciden.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Un FAIL exige evidencia
citada, legible y de enforcement, igual que un PASS. Una prueba insegura o sin objetivo no aprueba
ni hace FAIL. El modulo no ejecuta nada: lee la evidencia de una prueba ya hecha.

🔴 **Vu5 no es C1 ni ES0901 P5.** Los clientes salen del inventario de C1, con su cargador, y de una
evidencia citada de alcance; las operaciones del servidor, de `interfaces` del contexto de proyecto.
El resultado de P5 no se lee ni se escribe.
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

CONTROL = "client-server-validation-parity"
POLICY = "client-validation-server-mirroring-required"
TIPO = "CHECK"
REGLA = "Vu5"
CLAVE = "ES0902.Vu5"
SENAL = "clientValidationPresent"

ARCHIVO = "client-server-validation-parity.json"
SCHEMA = "client-server-validation-parity.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = "Toda validación del lado del cliente, debe estar espejada del lado del servidor."


# 🔴 Los clientes que hay que cubrir incluyen las superficies de C1, leidas con su cargador. Se
# importa el modulo; no se corre su evaluacion.
def _modulo(archivo, alias):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_SUPERFICIES = _modulo("oidc-keycloak-integration.py", "_vu5_inventario_de_superficies")

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "CLIENT_VALIDATION_COVERAGE_UNRESOLVED"
SIN_MAPEO = "CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED"
FALTA_EN_EL_SERVIDOR = "SERVER_VALIDATION_MISSING"
MAS_DEBIL_EN_EL_SERVIDOR = "SERVER_VALIDATION_WEAKER"
SIN_EQUIVALENCIA = "VALIDATION_EQUIVALENCE_UNRESOLVED"
PRUEBA_INSEGURA = "SERVER_VALIDATION_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_COBERTURA, SIN_MAPEO,
           FALTA_EN_EL_SERVIDOR, MAS_DEBIL_EN_EL_SERVIDOR, SIN_EQUIVALENCIA, PRUEBA_INSEGURA,
           SIN_OBJETIVO)
# Las tres formas de fallar. El agregado informa la de la falla.
FALLAS = (FALLA, FALTA_EN_EL_SERVIDOR, MAS_DEBIL_EN_EL_SERVIDOR)
RESUELTAS = (PASA, NO_APLICA)
# Sin ninguna falla, el sin resolver que se informa es el primero de este orden: el de los pasos.
ORDEN_DE_LO_ABIERTO = (SIN_MAPEO, SIN_EQUIVALENCIA, PRUEBA_INSEGURA, SIN_OBJETIVO)

# -- lo que dice el registro ------------------------------------------------------------

PRESENTE, FALTANTE, SIN_RESOLVER = "PRESENT", "MISSING", "UNRESOLVED"
EQUIVALENTE = "EQUIVALENT"
MAS_ESTRICTO = "SERVER_STRONGER_COMPATIBLE"
MAS_DEBIL = "SERVER_WEAKER"
PARIDADES_QUE_CUMPLEN = (EQUIVALENTE, MAS_ESTRICTO)

# -- lo que establece una evidencia ---------------------------------------------------------

VALIDACION_DEL_CLIENTE = "CLIENT_VALIDATION"          # value PRESENT | ABSENT
AUSENTE = "ABSENT"
ALCANCE = "CLIENT_SURFACE_SCOPE"                      # values: las superficies
VALIDACION_DEL_SERVIDOR = "SERVER_VALIDATION"         # value PRESENT | MISSING
PARIDAD = "VALIDATION_PARITY"                         # value EQUIVALENT | ..._COMPATIBLE | ..._WEAKER
COMPATIBILIDAD = "CONTRACT_COMPATIBILITY"             # value COMPATIBLE | INCOMPATIBLE
COMPATIBLE, INCOMPATIBLE = "COMPATIBLE", "INCOMPATIBLE"
EJECUCION_DEL_SCHEMA = "SHARED_SCHEMA_SERVER_EXECUTION"
RECHAZO = "SERVER_INPUT_REJECTION"                    # outcome INVALID_INPUT_ACCEPTED | ..._REJECTED

ACEPTADA = "INVALID_INPUT_ACCEPTED"
RECHAZADA = "INVALID_INPUT_REJECTED"
CONFIRMADA = "CONFIRMED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, ACEPTADA, RECHAZADA)
POR_VALIDACION = "VALIDATION"
# 🔴 La unica regla sobre codigos de estado: un 401 o un 403 es autorizacion, no validacion.
DE_AUTORIZACION = (401, 403)

# -- que clase sostiene que ------------------------------------------------------------------

PRUEBA = "AUTHORIZED_QA_DIRECT_REQUEST"
# 🔴 Las unicas que sostienen que el servidor valida. Las tablas son del harness, no del estandar.
DE_ENFORCEMENT = ("SERVER_VALIDATION_CODE", "UNIT_TEST", "INTEGRATION_TEST", "CONTRACT_TEST",
                  PRUEBA, "OTHER_AUTHORITATIVE_EVIDENCE")
# Estas tienen que nombrar la operacion del mapeo y la validacion.
NOMBRAN_OPERACION_Y_VALIDACION = ("SERVER_VALIDATION_CODE", "UNIT_TEST", "INTEGRATION_TEST",
                                  "CONTRACT_TEST")
# Las que no sostienen nada, nombradas para que la salida diga por que.
INSUFICIENTES = ("CLIENT_CODE", "HTML_ATTRIBUTE", "TYPESCRIPT_TYPE", "UI_OBSERVATION",
                 "SHARED_SCHEMA_PRESENCE", "DEPENDENCY_MANIFEST", "DTO_NAME_MATCH",
                 "FIELD_NAME_MATCH", "CLIENT_TRANSFORMATION", "README_STATEMENT",
                 "AGENT_STATEMENT", "SKILL_OUTPUT")
# Las que ni siquiera encienden la senal: una libreria instalada no es una validacion.
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "DEPENDENCY_MANIFEST")
AUTORIDADES = ("ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT", "PROJECT_CONTRACT",
               "API_CONTRACT", "OFFICIAL_ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")

# Lo que una evidencia dice del servidor. Si la dice una clase que no es de enforcement, no sostiene.
DEL_SERVIDOR = (VALIDACION_DEL_SERVIDOR, PARIDAD, EJECUCION_DEL_SCHEMA, RECHAZO)

# Lo que, si no se pudo leer, igual impide el PASS aunque no se lo cite: dice que no.
DICEN_QUE_NO = (FALTANTE, MAS_DEBIL)

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

ENTERO = "integer"
FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "targets": _ev.LISTA, "validations": _ev.LISTA,
         "operations": _ev.LISTA, "value": _ev.TEXTO, "values": _ev.LISTA,
         "outcome": _ev.TEXTO, "rejectedBy": _ev.TEXTO, "responseStatus": ENTERO,
         "errorMessage": _ev.TEXTO, "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO,
         "testIdentityRef": _ev.TEXTO, "syntheticValues": _ev.BOOLEANO,
         "destructive": _ev.BOOLEANO, "realPrivilegedData": _ev.BOOLEANO,
         "rawSecretsLogged": _ev.BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def catalogo(caso):
    """El catalogo de `evidencia.py`, y un `responseStatus` que no es un entero lo deja mal formado."""
    cat, crudas, repetidos, torcidas = _ev.catalogo(caso, FORMA, OBLIGATORIOS)
    for ident in [i for i, e in cat.items() if e.get("responseStatus") is not None
                  and (isinstance(e["responseStatus"], bool)
                       or not isinstance(e["responseStatus"], int))]:
        torcidas = sorted(set(torcidas) | {_ev.etiqueta(cat.pop(ident))})
    return cat, crudas, repetidos, torcidas


def prueba_segura(e):
    """Los motivos por los que una prueba no era segura. Vacio es segura. No ejecuta nada.

    Ninguna condicion exige datos reales: los valores son sinteticos o la prueba no cuenta."""
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
    if not (e.get("testIdentityRef") or "").strip():
        motivos.append("NO_AUTHORIZED_TEST_CONTEXT")
    if e.get("syntheticValues") is not True:
        motivos.append("NOT_SYNTHETIC_VALUES")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
    if e.get("realPrivilegedData") is True:
        motivos.append("REAL_PRIVILEGED_DATA")
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


def _nombra(e, vid, op, por_operacion=False):
    """Si el item habla de ESTA validacion sobre ESTA operacion.

    El codigo del servidor y los tests nombran las dos cosas. Una ejecucion del schema compartido
    se establece para la operacion. Lo demas nombra la validacion. Un item que nombra otras
    operaciones y no la del mapeo no habla de esta."""
    operaciones = e.get("operations")
    nombra_la_operacion = op is not None and _ev.en(op, operaciones)
    if operaciones and not nombra_la_operacion:
        return False
    nombra_la_validacion = _ev.en(vid, e.get("validations"))
    if e["sourceType"] in NOMBRAN_OPERACION_Y_VALIDACION:
        return nombra_la_validacion and nombra_la_operacion
    if por_operacion:
        return nombra_la_operacion
    return nombra_la_validacion


def _afirmaciones(e, vid, op):
    """Lo que un item legible de enforcement dice de la validacion, como (que, valor)."""
    dice = set()
    if e["sourceType"] not in DE_ENFORCEMENT or not _lectura(e)[0]:
        return dice
    establece = e["establishes"]
    if VALIDACION_DEL_SERVIDOR in establece and _nombra(e, vid, op):
        if e.get("value") in (PRESENTE, FALTANTE):
            dice.add(("server", e["value"]))
    if PARIDAD in establece and _nombra(e, vid, op):
        if e.get("value") in (EQUIVALENTE, MAS_ESTRICTO, MAS_DEBIL):
            dice.add(("parity", e["value"]))
            dice.add(("server", PRESENTE))
    if EJECUCION_DEL_SCHEMA in establece and _nombra(e, vid, op, por_operacion=True):
        dice.update({("parity", EJECUCION_DEL_SCHEMA), ("server", PRESENTE)})
    if RECHAZO in establece and _nombra(e, vid, op):
        if e.get("outcome") == ACEPTADA:
            dice.add(("direct", ACEPTADA))
        elif e.get("outcome") == RECHAZADA:
            # 🔴 Validar no es autorizar: solo un rechazo por validacion, y nunca un 401 o un 403.
            if (e.get("rejectedBy") == POR_VALIDACION
                    and e.get("responseStatus") not in DE_AUTORIZACION):
                dice.update({("direct", RECHAZADA), ("parity", RECHAZADA), ("server", PRESENTE)})
            else:
                dice.add(("direct", "NOT_VALIDATION"))
    return dice


# -- los registros ------------------------------------------------------------------------------

def cargar(desde=None):
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "clients": []}
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
    declarado = (caso or {}).get("clients")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el registro de validaciones espejadas no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de validaciones espejadas no se pudo validar"
    if errores:
        return [], ("el registro de validaciones espejadas no valida contra su schema: %d "
                    "errores" % len(errores))
    return list(doc.get("clients") or []), ""


def interfaces(caso):
    """(ids, problema). Los `interface_id` de `interfaces.items[]` del contexto de proyecto, en NFC.

    🔴 No hay otro inventario de endpoints: sin contexto, ningun mapeo se resuelve."""
    contexto = (caso or {}).get("projectContext")
    if contexto is None:
        return set(), "no hay contexto de proyecto: ningun mapeo al servidor se puede resolver"
    bloque = contexto.get("interfaces") if isinstance(contexto, dict) else None
    items = bloque.get("items") if isinstance(bloque, dict) else None
    if not isinstance(items, list):
        return set(), "el contexto de proyecto no trae `interfaces.items`"
    return {_ev.nfc(i["interface_id"]) for i in items
            if isinstance(i, dict) and isinstance(i.get("interface_id"), str)
            and i["interface_id"].strip()}, ""


def _citas(cliente, validacion=None):
    """Los ids que cita un cliente, o una validacion con su cliente, en NFC."""
    citados = _ev.claves(cliente.get("evidence"))
    for v in ([validacion] if validacion is not None else cliente.get("validations") or []):
        citados |= _ev.claves(v.get("evidence")) | _ev.claves(
            [(v.get("constraint") or {}).get("clientEvidenceRef"),
             (v.get("serverMapping") or {}).get("serverEvidenceRef")])
    return citados


def _presencias(v, cliente, cat, citados):
    """Lo citado y legible que establece la validacion del cliente, de una clase que no es debil.

    La cita la ata a la validacion. Un item que nombra otras validaciones u otros clientes, y no
    estos, habla de otra cosa."""
    def de_esta(e):
        if not e.get("validations") and not e.get("targets"):
            return True
        return (_ev.en(v.get("validationId"), e.get("validations"))
                or _ev.en(cliente.get("clientSurfaceId"), e.get("targets")))
    return sorted(e["evidenceId"] for e in cat.values()
                  if VALIDACION_DEL_CLIENTE in e["establishes"] and e.get("value") == PRESENTE
                  and e["sourceType"] not in DEBILES and _citada(e, citados) and _lectura(e)[0]
                  and de_esta(e))


# -- la senal y la cobertura -----------------------------------------------------------------------

HAY, NO_HAY, NO_SE = "CLIENT_VALIDATION", "NO_CLIENT_VALIDATION", "UNRESOLVED"


def derivar(caso, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    lista, problema = _SUPERFICIES.superficies(entrada, desde)
    registrados, problema_registro = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    citados = set()
    for c in registrados:
        citados |= _citas(c)
    # 🔴 Los ids se normalizan UNA vez, antes de contar (Vu2, tercer pase).
    del_inventario = sorted({_ev.nfc(s.get("surfaceId")) for s in lista
                             if isinstance(s.get("surfaceId"), str)})
    de_evidencia = sorted({_ev.nfc(x) for e in cat.values()
                           if ALCANCE in e["establishes"] and e["sourceType"] in AUTORIDADES
                           and _citada(e, citados) and _lectura(e)[0]
                           for x in e.get("values") or []})
    alcance = sorted(set(del_inventario) | set(de_evidencia))
    clientes = [_ev.nfc(c.get("clientSurfaceId")) for c in registrados]
    validaciones = [_ev.nfc(v.get("validationId")) for c in registrados
                    for v in c.get("validations") or []]

    superficies, ausentes_citadas, sin_cubrir = [], [], []
    for sid in alcance:
        propias = [c for c in registrados if _ev.igual(c.get("clientSurfaceId"), sid)]
        sobre = [e for e in cat.values() if VALIDACION_DEL_CLIENTE in e["establishes"]
                 and _ev.en(sid, e.get("targets")) and e["sourceType"] not in DEBILES]
        legibles = [e for e in sobre if _lectura(e)[0]]
        presentes = [e for e in sobre if e.get("value") == PRESENTE]
        ausentes = [e for e in legibles if e.get("value") == AUSENTE and e["sourceType"] in AUTORIDADES]
        enciende = any(_presencias(v, c, cat, _citas(c, v))
                       for c in propias for v in c.get("validations") or [])
        con_validaciones = any(c.get("validations") for c in propias)
        ilegibles = _ev.ilegibles_sobre(sid, cat, crudas)
        if enciende:
            estado = HAY
        elif ausentes and not con_validaciones and not presentes and not ilegibles:
            estado = NO_HAY
        else:
            estado = NO_SE
        # Cubierta: con una entrada que trae al menos una validacion, o con una ausencia autoritativa
        # y legible que nombra la superficie y que nada contradice. Si hay entrada, la ausencia se
        # cita desde ella; si no, no hay desde donde citarla. Una entrada vacia no cubre.
        desde_la_entrada = set()
        for c in propias:
            desde_la_entrada |= _citas(c)
        valen = [e for e in ausentes if not propias or _citada(e, desde_la_entrada)]
        if con_validaciones:
            pass
        elif valen and not presentes and not ilegibles:
            ausentes_citadas.append(sid)
        else:
            sin_cubrir.append(sid)
        superficies.append({"clientSurfaceId": sid, "clientValidation": estado})

    fuera = sorted({str(i) for i in clientes if i not in alcance})
    cobertura = {
        "scope": [str(s) for s in alcance], "fromInventory": [str(s) for s in del_inventario],
        "fromScopeEvidence": [str(s) for s in de_evidencia],
        "registered": sorted({str(i) for i in clientes}),
        "duplicatedClients": sorted({str(i) for i in clientes if clientes.count(i) > 1}),
        "duplicatedValidations": sorted({str(i) for i in validaciones
                                         if validaciones.count(i) > 1}),
        "clientsOutsideScope": fuera,
        "uncovered": [str(s) for s in sin_cubrir],
        "absent": [str(s) for s in ausentes_citadas],
        "registryUnreadable": bool(problema_registro)}
    completa = not (problema or problema_registro or cobertura["duplicatedClients"]
                    or cobertura["duplicatedValidations"])
    presentes_en_el_registro = [(c, v) for c in registrados for v in c.get("validations") or []
                                if _presencias(v, c, cat, _citas(c, v))]
    if problema:
        valor = _senales.SIN_RESOLVER
    elif presentes_en_el_registro:
        valor = _senales.VERDADERA
    elif (superficies and completa and not validaciones and not fuera and not sin_cubrir
          and all(s["clientValidation"] == NO_HAY for s in superficies)):
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    return {"value": valor, "surfaces": superficies, "inventory": lista, "registry": registrados,
            "coverage": cobertura, "complete": completa, "problem": problema,
            "registryProblem": problema_registro, "catalog": cat, "raw": crudas,
            "repeated": repetidos, "malformed": torcidas, "cited": citados,
            "present": presentes_en_el_registro}


def senal(caso, desde=None):
    d = derivar(caso, desde)
    evidencia = []
    if d["value"] == _senales.VERDADERA:
        for c, v in d["present"]:
            evidencia.append({"evidenceId": "validation:%s" % v.get("validationId"),
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "%s#%s" % (ARCHIVO, v.get("validationId")),
                              "claim": "la validacion `%s` del cliente `%s` esta evidenciada" % (
                                  v.get("validationId"), c.get("clientSurfaceId")),
                              "supports": d["value"]})
    elif d["value"] == _senales.FALSA:
        for s in d["surfaces"]:
            evidencia.append({"evidenceId": "surface:%s" % s["clientSurfaceId"],
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "client-surface#%s" % s["clientSurfaceId"],
                              "claim": "una evidencia autoritativa establece que el cliente `%s` "
                                       "no valida nada" % s["clientSurfaceId"],
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

def _bloqueos(cat, vid, citados, registradas=(), alcance=()):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan: las que se citan, o las que
    dicen que no. Con `vid`, las de esa validacion; sin ella, las que nombran una superficie del
    alcance y ninguna validacion registrada.

    🔴 Una prueba que nombra solamente validaciones u operaciones que no estan en el registro no
    mueve nada, y una ajena e insegura que dice que el servidor rechazo tampoco."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        if vid is not None and not _ev.en(vid, e.get("validations")):
            continue
        if vid is None and (any(_ev.en(r, e.get("validations")) for r in registradas)
                            or not any(_ev.en(s, e.get("targets")) for s in alcance)):
            continue
        _, bloqueo, m = _lectura(e)
        if bloqueo and (_citada(e, citados) or e.get("outcome") == ACEPTADA
                        or e.get("value") in DICEN_QUE_NO):
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return SIN_EQUIVALENCIA


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan la validacion, el PASS y el NOT_APPLICABLE.

    Lo que no se pudo leer y pesa impide el PASS y tambien el NOT_APPLICABLE; un FAIL no se toca:
    bloquear impide aprobar, no tapa lo que falla. Tampoco reemplaza un sin resolver que ya estaba:
    ese es el estado que sale, y el del bloqueo queda en `states`."""
    if estado in FALLAS or estado not in RESUELTAS:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), ("una prueba que se cita, o que dice que el servidor acepta la "
                                    "entrada invalida, no se pudo leer")
    if ilegibles and estado in RESUELTAS:
        return SIN_EQUIVALENCIA, ("hay evidencia ilegible sobre la validacion, y esa podia ser la "
                                  "que decia que el servidor no la espeja")
    return estado, motivo


# -- una validacion, en el orden de la spec -----------------------------------------------------

def _ids(cat, vid, op, que, valores, citados=None):
    """Los ids de lo legible de enforcement que afirma `que` con uno de `valores`, citados o no."""
    return sorted(e["evidenceId"] for e in cat.values()
                  if any((que, x) in _afirmaciones(e, vid, op) for x in valores)
                  and (citados is None or _citada(e, citados)))


def _paso_mapeo(v, op, cat, citados, salida, interfaces_):
    if not isinstance(op, str) or not op.strip():
        return SIN_MAPEO, "la validacion no nombra la operacion del servidor"
    if _ev.nfc(op) not in interfaces_:
        return SIN_MAPEO, ("`%s` no es una interfaz del contexto de proyecto, o no hay contexto"
                           % op)
    salida["serverMapping"]["resolved"] = True
    return None, ""


def _paso_servidor(v, op, cat, citados, salida, _):
    vid = v.get("validationId")
    declarado = (v.get("serverMapping") or {}).get("enforcementStatus")
    si = _ids(cat, vid, op, "server", (PRESENTE,))
    no = _ids(cat, vid, op, "server", (FALTANTE,))
    no_citadas = _ids(cat, vid, op, "server", (FALTANTE,), citados)
    # 🔴 La falla establecida gana siempre: diga lo que diga el registro y diga lo que diga otra
    # evidencia. Declarar la falla con honestidad nunca da algo mas blando que declarar que cumple.
    if no_citadas:
        salida["evidenceUsed"]["enforcement"] = no_citadas
        salida["contradictedBy"].extend(si)
        return FALTA_EN_EL_SERVIDOR, ("una evidencia citada de enforcement establece que el "
                                      "servidor no valida lo que valida el cliente")
    if declarado == FALTANTE:
        if no:
            return SIN_EQUIVALENCIA, ("que el servidor no valide lo dice una evidencia que no se "
                                      "cita: lo no citado nunca hace FAIL")
        return _abierto(salida["blockedBy"]), ("que el servidor no valide no consta con evidencia "
                                               "citada")
    if declarado != PRESENTE:
        return SIN_EQUIVALENCIA, "no esta resuelto si el servidor valida"
    if no:
        salida["contradictedBy"].extend(no)
        return SIN_EQUIVALENCIA, ("una evidencia dice que el servidor no valida y el registro dice "
                                  "que si; no se elige")
    apoyo = _ids(cat, vid, op, "server", (PRESENTE,), citados)
    if not apoyo:
        return _abierto(salida["blockedBy"]), (
            "que el servidor valide no consta con evidencia citada de enforcement; un nombre, una "
            "libreria o un atributo no alcanzan")
    salida["evidenceUsed"]["enforcement"] = apoyo
    return None, ""


def _paso_paridad(v, op, cat, citados, salida, _):
    vid = v.get("validationId")
    declarada = v.get("parity")
    positivas = (EQUIVALENTE, MAS_ESTRICTO, EJECUCION_DEL_SCHEMA, RECHAZADA)
    debiles = _ids(cat, vid, op, "parity", (MAS_DEBIL,))
    debiles_citadas = _ids(cat, vid, op, "parity", (MAS_DEBIL,), citados)
    # 🔴 La falla establecida gana siempre, como en el paso anterior.
    if debiles_citadas:
        salida["evidenceUsed"]["parity"] = debiles_citadas
        salida["contradictedBy"].extend(_ids(cat, vid, op, "parity", positivas))
        return MAS_DEBIL_EN_EL_SERVIDOR, ("una evidencia citada de enforcement establece que el "
                                          "servidor acepta lo que el cliente rechaza")
    if declarada == MAS_DEBIL:
        if debiles:
            return SIN_EQUIVALENCIA, ("que el servidor sea mas debil lo dice una evidencia que no "
                                      "se cita: lo no citado nunca hace FAIL")
        return _abierto(salida["blockedBy"]), ("que el servidor sea mas debil no consta con "
                                               "evidencia citada")
    if declarada not in PARIDADES_QUE_CUMPLEN:
        return SIN_EQUIVALENCIA, "la paridad entre cliente y servidor no esta resuelta"
    if debiles:
        salida["contradictedBy"].extend(debiles)
        return SIN_EQUIVALENCIA, ("una evidencia dice que el servidor es mas debil y el registro "
                                  "dice que no; no se elige")
    apoyo = _ids(cat, vid, op, "parity", (declarada, EJECUCION_DEL_SCHEMA, RECHAZADA), citados)
    if not apoyo:
        return _abierto(salida["blockedBy"]), ("la paridad no consta con evidencia citada de "
                                               "enforcement para esta validacion")
    if declarada == MAS_ESTRICTO:
        compat = [e for e in cat.values()
                  if COMPATIBILIDAD in e["establishes"] and e["sourceType"] in AUTORIDADES
                  and _ev.en(vid, e.get("validations")) and _lectura(e)[0]]
        no_compatibles = sorted(e["evidenceId"] for e in compat if e.get("value") == INCOMPATIBLE)
        compatibles = sorted(e["evidenceId"] for e in compat
                             if e.get("value") == COMPATIBLE and _citada(e, citados))
        if no_compatibles:
            salida["contradictedBy"].extend(no_compatibles)
            return SIN_EQUIVALENCIA, ("un servidor mas estricto con el contrato en contra rechaza "
                                      "entrada valida: no es una brecha, pero tampoco es espejo")
        if not compatibles:
            return SIN_EQUIVALENCIA, ("un servidor mas estricto necesita una evidencia autoritativa "
                                      "y citada de que el contrato lo admite")
        salida["evidenceUsed"]["contractCompatibility"] = compatibles
    salida["evidenceUsed"]["parity"] = apoyo
    return None, ""


def _paso_prueba_directa(v, op, cat, citados, salida, _):
    vid = v.get("validationId")
    aceptan = _ids(cat, vid, op, "direct", (ACEPTADA,))
    aceptan_citadas = _ids(cat, vid, op, "direct", (ACEPTADA,), citados)
    otras = _ids(cat, vid, op, "direct", ("NOT_VALIDATION",))
    for i in otras:
        salida["issues"].append("`%s` no muestra un rechazo por validacion: uno por autorizacion, "
                                "un 401 o un 403 no prueban que el servidor valido" % i)
    if aceptan_citadas:
        salida["evidenceUsed"]["directTest"] = aceptan_citadas
        return FALTA_EN_EL_SERVIDOR, ("una prueba citada muestra que el servidor procesa como valida "
                                      "una entrada que el cliente rechaza")
    if aceptan:
        salida["contradictedBy"].extend(aceptan)
        return SIN_EQUIVALENCIA, ("una prueba muestra que el servidor acepta la entrada invalida y "
                                  "no se la cita; no se elige")
    salida["evidenceUsed"]["directTest"] = _ids(cat, vid, op, "direct", (RECHAZADA,), citados)
    return None, ""


PASOS = (_paso_mapeo, _paso_servidor, _paso_paridad, _paso_prueba_directa)


def evaluar_validacion(v, cliente, d, interfaces_):
    """Una validacion del cliente, sola: su estado y la evidencia que lo sostiene, por id."""
    cat, crudas = d["catalog"], d["raw"]
    vid = v.get("validationId")
    restriccion = v.get("constraint") or {}
    mapeo = v.get("serverMapping") or {}
    op = mapeo.get("operationRef") if isinstance(mapeo.get("operationRef"), str) else None
    citados = _citas(cliente, v)
    salida = {"validationId": vid, "inputRef": v.get("inputRef"),
              "constraint": {"type": restriccion.get("type"),
                             "description": restriccion.get("description"),
                             "clientEvidenceRef": restriccion.get("clientEvidenceRef")},
              "serverMapping": {"operationRef": mapeo.get("operationRef"),
                                "enforcementStatus": mapeo.get("enforcementStatus"),
                                "serverEvidenceRef": mapeo.get("serverEvidenceRef"),
                                "resolved": False},
              "parity": v.get("parity"), "verificationMode": v.get("verificationMode"),
              "evidenceUsed": {"clientValidation": _presencias(v, cliente, cat, citados),
                               "enforcement": [], "parity": [], "contractCompatibility": [],
                               "directTest": []},
              "contradictedBy": [], "issues": [],
              # Lo citado que dice algo del servidor y no es de una clase que lo sostenga.
              "insufficient": sorted(e["evidenceId"] for e in cat.values()
                                     if e["sourceType"] in INSUFICIENTES and _citada(e, citados)
                                     and set(e["establishes"]) & set(DEL_SERVIDOR))}
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, vid, citados)
    pasos = [paso(v, op, cat, citados, salida, interfaces_) for paso in PASOS]
    # 🔴 En el orden de la spec, y lo que falla no lo tapa un paso anterior sin resolver.
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = [p for p in pasos if p[0] is not None]
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | set(_ev.ilegibles_sobre(vid, cat, crudas)))
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre la validacion: %s"
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
    """(estado, motivo) de un conjunto de estados de validaciones."""
    fallas = sorted({e for e in estados if e in FALLAS})
    if fallas:
        return (fallas[0] if len(fallas) == 1 else FALLA,
                "al menos una validacion falla; las que cumplen no la tapan")
    abiertos = {e for e in estados if e != PASA}
    for e in ORDEN_DE_LO_ABIERTO:
        if e in abiertos:
            return e, "hay validaciones sin resolver"
    return PASA, ""


def evaluar_cliente(cliente, d, interfaces_):
    """Un cliente del registro con sus validaciones. Un cliente en verde no tapa otro."""
    cid = cliente.get("clientSurfaceId")
    validaciones = _ev.ordenadas(evaluar_validacion(v, cliente, d, interfaces_)
                                 for v in cliente.get("validations") or [])
    salida = {"clientSurfaceId": cid, "clientType": cliente.get("clientType"),
              "inScope": _ev.nfc(cid) in d["coverage"]["scope"], "validations": validaciones,
              "issues": []}
    if not salida["inScope"]:
        salida["issues"].append("el cliente `%s` no esta en el inventario de C1 ni en una "
                                "evidencia citada de alcance" % cid)
    if validaciones:
        salida["state"], salida["reason"] = _de_lo_evaluado([v["state"] for v in validaciones])
    elif _ev.nfc(cid) in d["coverage"]["absent"]:
        salida["state"], salida["reason"] = NO_APLICA, "el cliente no valida nada, con evidencia"
    else:
        salida["state"], salida["reason"] = SIN_COBERTURA, ("el cliente no declara validaciones ni "
                                                            "una ausencia citada")
    return salida


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de Vu5, cliente por cliente y validacion por validacion.

    `caso`:

        {"inventory": {...},        # el de C1; opcional
         "clients": {...},          # el registro de Vu5; opcional
         "projectContext": {...},   # el contexto de proyecto; sin el, ningun mapeo se resuelve
         "evidence": [...]}         # el catalogo, cerrado
    """
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "clients": [], "issues": [], "coverage": {}}
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    ids_de_interfaces, problema_de_contexto = interfaces(entrada)
    evalua = valor == _senales.VERDADERA and not d["problem"]
    for problema in (d["problem"], d["registryProblem"], problema_de_contexto if evalua else ""):
        if problema:
            salida["issues"].append("el inventario de superficies no valida contra su schema"
                                    if problema.startswith("el inventario de superficies no valida")
                                    else problema)
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    for cid in d["coverage"]["clientsOutsideScope"]:
        salida["issues"].append("el cliente `%s` no esta en el alcance" % cid)
    salida["issues"].sort()
    salida["coverage"] = d["coverage"]
    registradas = [v.get("validationId") for c in d["registry"] for v in c.get("validations") or []]
    sueltos, motivos = _bloqueos(d["catalog"], None, d["cited"], registradas,
                                 d["coverage"]["scope"])
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos

    if valor == _senales.SIN_RESOLVER:
        estado, motivo = SIN_APLICABILIDAD, "no consta si hay validaciones del lado del cliente"
    elif valor == _senales.FALSA:
        estado, motivo = NO_APLICA, "ningun cliente del alcance valida nada, con evidencia"
    elif d["problem"]:
        estado, motivo = SIN_COBERTURA, "el inventario de superficies no se pudo leer"
    else:
        # 🔴 Cada cliente se evalua solo, tambien el que no esta en el alcance.
        salida["clients"] = _ev.ordenadas(evaluar_cliente(c, d, ids_de_interfaces)
                                          for c in d["registry"])
        estado, motivo = _agregado(salida["clients"], d)
    final, motivo = _bloquear(estado, motivo, sueltos, [])
    return _cerrar(salida, final, motivo, estado)


def _agregado(clientes, d):
    estados = [v["state"] for c in clientes for v in c["validations"]]
    fallas = sorted({e for e in estados if e in FALLAS})
    if fallas:
        return _de_lo_evaluado(estados)
    c = d["coverage"]
    # Un cliente fuera del alcance tambien: registro y alcance no coinciden (E-67).
    if not d["complete"] or not estados or c["uncovered"] or c["clientsOutsideScope"]:
        return SIN_COBERTURA, ("no constan todas las validaciones del cliente: sin cubrir %s, fuera "
                               "del alcance %s" % (c["uncovered"] or "-",
                                                   c["clientsOutsideScope"] or "-"))
    return _de_lo_evaluado(estados)


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None,) + RESUELTAS:
        todos.add(previo)
    for c in salida["clients"]:
        for v in c["validations"]:
            todos.update(v.get("states") or [])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


# -- hacia seguridad.resultado ----------------------------------------------------------------------

def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu5", ...)`, desde la salida de `evaluar`.

    Vu5 no tiene algoritmo propio en `seguridad.py`: va por el generico. Los dos controles de la
    fila llevan el estado del check -PASS, FAIL o el estado abierto tal cual- con la evidencia por
    id. Un resultado que no dice ser de este check no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return {}, {}
    estado = r["state"]
    control = FALLA if estado in FALLAS else estado
    ids = set()
    for c in r.get("clients") or []:
        for v in c.get("validations") or []:
            ids.update(i for u in (v.get("evidenceUsed") or {}).values() for i in u)
    evidencia = sorted(ids) or (["check:%s" % CONTROL] if estado in RESUELTAS + FALLAS else [])
    doc = {"controlResults": {c: {"result": control, "evidence": evidencia}
                              for c in (POLICY, CONTROL)}}
    valor = r.get("signalValue")
    # 🔴 Un NOT_APPLICABLE que el bloqueo impidio no vuelve a entrar por la senal.
    senales = ({SENAL: True} if valor == _senales.VERDADERA
               else {SENAL: False} if valor == _senales.FALSA and estado == NO_APLICA else {})
    return _ev.depurar(doc), senales
