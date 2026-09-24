# ES0902 §6 Vu6: todo mensaje de error que ve un consumidor esta customizado.
#
# Escenarios E-01 a E-60 de docs/cambios/es0902-vu6-mensajes-de-error-customizados/spec.md.
# E-nn es el VU6-nn del pedido de instalacion; E-54 a E-60 los agrega la spec.
#
# 🔴 CASO es el portal con su error inesperado cumplido: la superficie esta en el inventario de C1,
# una observacion citada establece que muestra errores, y un test de integracion citado establece
# que el mensaje del error inesperado esta customizado. Casi todo este archivo sale de romperlo.
# E-09 lo mira en PASS.
import ast
import copy
import importlib.util
import inspect
import json
import random
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import seguridad                      # noqa: E402
from orquestacion import senales                        # noqa: E402
from orquestacion import normativa                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "custom-error-message-compliance.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu6_mensajes")
VU5 = _cargar(CONTROLES / "checks" / "client-server-validation-parity.py", "vu6_de_vu5")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu6"}
LOS_12 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "ERROR_SURFACE_COVERAGE_UNRESOLVED", "DEFAULT_ERROR_EXPOSED", "RAW_TECHNICAL_ERROR_EXPOSED",
          "INFRASTRUCTURE_DETAIL_EXPOSED", "ERROR_CUSTOMIZATION_UNRESOLVED",
          "HTTP_ERROR_SEMANTICS_MASKED", "ERROR_MESSAGE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
POR_DEFECTO = "DEFAULT_ERROR_EXPOSED"
CRUDO = "RAW_TECHNICAL_ERROR_EXPOSED"
INFRA = "INFRASTRUCTURE_DETAIL_EXPOSED"
ENMASC = "HTTP_ERROR_SEMANTICS_MASKED"
FALLAS = ("FAIL", POR_DEFECTO, CRUDO, INFRA, ENMASC)
SIN_COB = "ERROR_SURFACE_COVERAGE_UNRESOLVED"
SIN_CUST = "ERROR_CUSTOMIZATION_UNRESOLVED"
INSEGURA = "ERROR_MESSAGE_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"
INESPERADO = "UNEXPECTED_ERROR"

SUPERFICIE = {"surfaceId": "portal", "scope": "tramites", "audience": "INSTITUTIONAL",
              "environment": "QA", "currentProvider": "https://sso-qa.identidad.example/auth",
              "protocol": "OIDC", "flow": "FLUJO-A", "credentialEntryDelegated": True,
              "evidence": []}
BACKOFFICE = dict(SUPERFICIE, surfaceId="backoffice", scope="gestion",
                  credentialEntryDelegated=False)


def _e(eid, fuente, establece, valor=None, sup=("portal",), esc=("inesperado",), tipos=None,
       **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if sup is not None:
        base["targets"] = list(sup)
    if esc is not None:
        base["scenarios"] = list(esc)
    if tipos is not None:
        base["errorTypes"] = list(tipos)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _vis(eid="vis", sup="portal", fuente="EXPOSED_OUTPUT_OBSERVATION", valor="PRESENT"):
    return _e(eid, fuente, "USER_FACING_ERROR", valor, sup=[sup], esc=None)


def _obs(eid="obs", valor="CUSTOMIZED_SAFE", fuente="INTEGRATION_TEST", sup="portal",
         esc="inesperado", **extra):
    return _e(eid, fuente, "ERROR_OUTPUT", valor, sup=[sup], esc=[esc], **extra)


VIS = _vis()
OBS = _obs()
EVIDENCIA = [VIS, OBS]


def _esc(eid="inesperado", tipo=INESPERADO, resultado="CUSTOMIZED_SAFE", detalle="NONE",
         modo="INTEGRATION_TEST", evidencia=("obs",), http=None):
    return {"scenarioId": eid, "errorType": tipo, "result": resultado, "httpStatusRef": http,
            "technicalDetailExposure": detalle, "verificationMode": modo,
            "evidence": list(evidencia)}


def _sup(sid="portal", tipo="WEB_USER", owner="APPLICATION_CONTROLLED", escenarios=None,
         evidencia=("vis",)):
    return {"surfaceId": sid, "consumerType": tipo, "owner": owner,
            "scenarios": [_esc()] if escenarios is None else list(escenarios),
            "evidence": list(evidencia)}


def _caso(inventario=None, registro=None, evidencia=None, contexto=None):
    caso = {"inventory": {"version": "1.0", "surfaces": copy.deepcopy(
                [SUPERFICIE] if inventario is None else inventario)},
            "surfaces": {"version": "1.0", "surfaces": copy.deepcopy(
                [_sup()] if registro is None else registro)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if contexto is not None:
        caso["projectContext"] = copy.deepcopy(contexto)
    return caso


def _r(*a, senal=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal)


def _estado(*a, **k):
    return _r(*a, **k)["state"]


def _s(r, sid="portal"):
    return [s for s in r["surfaces"] if s["surfaceId"] == sid][0]


def _x(r, sid="portal", eid="inesperado"):
    return [x for x in _s(r, sid)["scenarios"] if x["scenarioId"] == eid][0]


def _sin(eid, *mas):
    return [x for x in EVIDENCIA if x["evidenceId"] != eid] + list(mas)


def _solo_con(*evidencia, **cambios):
    """El portal con su error inesperado sostenido solo por `evidencia` en lugar de `obs`."""
    ids = [x["evidenceId"] for x in evidencia]
    return _r(registro=[_sup(escenarios=[_esc(evidencia=ids, **cambios)])],
              evidencia=_sin("obs", *evidencia))


def _con_ademas(*evidencia, **cambios):
    """El portal con `obs`, y ademas `evidencia` citada desde el escenario."""
    ids = [x["evidenceId"] for x in evidencia]
    return _r(registro=[_sup(escenarios=[_esc(evidencia=["obs"] + ids, **cambios)])],
              evidencia=EVIDENCIA + list(evidencia))


def _arbol():
    return ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))


def _literales():
    arbol = _arbol()
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    return {n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)} - docs


def _llamadores(funcion):
    return sorted({f.name for f in ast.walk(_arbol()) if isinstance(f, ast.FunctionDef)
                   for n in ast.walk(f) if isinstance(n, ast.Call)
                   and getattr(n.func, "id", None) == funcion})


def _sin_excepcion(f):
    try:
        return f()
    except Exception as e:                              # noqa: BLE001 - el test nombra la excepcion
        return "EXCEPCION %s: %s" % (type(e).__name__, e)


def _claves(dato):
    if isinstance(dato, dict):
        for k, v in dato.items():
            yield k
            yield from _claves(v)
    elif isinstance(dato, list):
        for v in dato:
            yield from _claves(v)


def _json(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


PRUEBA = dict(environment="QA", authorized=True, syntheticData=True)


def _prueba(valor="CUSTOMIZED_SAFE", eid="qa", esc="inesperado", tipos=None, **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _e(eid, "AUTHORIZED_QA_RUNTIME_TEST", "ERROR_OUTPUT", valor,
              esc=None if esc is None else [esc], tipos=tipos, **datos)


def _vu6_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu6", ev, sen, MATRIZ)


def _alcance(sid, eid=None, fuente="PROJECT_REQUIREMENT"):
    return _e(eid or "alcance-%s" % sid, fuente, "ERROR_SURFACE_SCOPE", sup=None, esc=None,
              values=[sid])


def _otra(sid, tipo, valor="CUSTOMIZED_SAFE", fuente="CONTRACT_TEST", escenarios=None, extra=()):
    """Otra superficie, en el alcance por una evidencia citada, con su error inesperado."""
    alcance = _alcance(sid)
    vis = _vis("vis-%s" % sid, sup=sid)
    obs = _obs("obs-%s" % sid, valor=valor, fuente=fuente, sup=sid)
    esc = escenarios if escenarios is not None else [
        _esc(resultado=valor, evidencia=[obs["evidenceId"]])]
    return (_sup(sid, tipo, escenarios=esc, evidencia=[alcance["evidenceId"], vis["evidenceId"]]),
            [alcance, vis, obs] + list(extra))


def _ausente(fuente="ARCHITECTURE_DOCUMENTATION", sup="portal", eid="aus"):
    return _vis(eid, sup=sup, fuente=fuente, valor="ABSENT")


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (VU6-01)."""
    t.igual("E-01 la fila", "ES0902.Vu6", seguridad.regla("Vu6", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu6", CHECK.CLAVE)
    for nombre, r in (("pasa", _r()), ("sin senal", CHECK.evaluar({})),
                      ("falla", _con_ademas(_obs("crudo", valor=CRUDO))),
                      ("no aplica", _r(registro=[], evidencia=[_ausente()]))):
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu6", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu6", _vu6_en_seguridad(r)["ruleKey"])


def test_e02_los_ids(t):
    """E-02 (VU6-02)."""
    vu6 = seguridad.regla("Vu6", MATRIZ)
    t.igual("E-02 la senal", ["userFacingErrorPresent"], vu6["applicability"]["signals"])
    t.igual("E-02 los agentes, en el orden de la matriz",
            ["dev-security", "dev-backend", "dev-frontend"], vu6["primaryAgents"])
    t.igual("E-02 la policy", ["custom-error-messages-required"], vu6["policies"])
    t.igual("E-02 el check", ["custom-error-message-compliance"], vu6["checks"])
    t.igual("E-02 el modulo", ("userFacingErrorPresent", "custom-error-message-compliance",
                               "custom-error-messages-required"),
            (CHECK.SENAL, CHECK.CONTROL, CHECK.POLICY))
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("custom-error-messages-required", "POLICY",
             "controles/policies/custom-error-messages-required.md"),
            ("custom-error-message-compliance", "CHECK",
             "controles/checks/custom-error-message-compliance.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.igual("E-02 %s regla" % cid, "Vu6", registro[cid]["rule"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    for md in ("es0902-vu6-governance.md", "es0902-vu6-user-facing-error-present-signal.md",
               "es0902-vu6-custom-error-message-compliance-check.md"):
        t.verdadero("E-02 %s instalado" % md, (REGLAS / md).is_file())
    politica = (CONTROLES / "policies" / "custom-error-messages-required.md").read_text(
        encoding="utf-8")
    t.contiene("E-02 la policy declara su id", "id: custom-error-messages-required", politica)


def test_e03_nada_nuevo(t):
    """E-03 (VU6-03)."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 10, len(registro["agents"]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 cero reviews", [], seguridad.regla("Vu6", MATRIZ)["reviews"])
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-03 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-03 y Vu6 no tiene algoritmo propio", "Vu6" not in seguridad.ALGORITMOS)


# -- La senal -------------------------------------------------------------------

def test_e04_una_pantalla_de_error_enciende(t):
    """E-04 (VU6-04)."""
    doc = CHECK.senal(_caso())
    t.igual("E-04 TRUE", "TRUE", doc["value"])
    t.igual("E-04 la cita", ["custom-error-message-evidence.json#portal"],
            sorted(e["reference"] for e in doc["evidence"]))
    booleanos = senales.booleanos({"userFacingErrorPresent": doc})
    t.igual("E-04 enciende la fila", "APPLICABLE",
            seguridad.resolver_regla(seguridad.regla("Vu6", MATRIZ), booleanos)[0])
    t.igual("E-04 sin citarla no enciende", "UNRESOLVED",
            CHECK.senal(_caso(registro=[_sup(evidencia=[])]))["value"])
    t.igual("E-04 citada y de otra superficie, no", "UNRESOLVED",
            CHECK.senal(_caso(evidencia=[_vis(sup="otra"), OBS]))["value"])
    t.igual("E-04 una que dice ABSENT no enciende", "UNRESOLVED",
            CHECK.senal(_caso(evidencia=[_vis(valor="ABSENT"), OBS]))["value"])


def test_e05_un_payload_de_api_enciende(t):
    """E-05 (VU6-05)."""
    api, ev = _otra("api", "API_CONSUMER")
    caso = _caso(inventario=[], registro=[api], evidencia=ev)
    t.igual("E-05 TRUE", "TRUE", CHECK.senal(caso)["value"])
    t.igual("E-05 y se evalua", "PASS", CHECK.evaluar(caso)["state"])
    t.igual("E-05 la api en el alcance por la evidencia citada", ["api"],
            CHECK.evaluar(caso)["coverage"]["fromScopeEvidence"])


def test_e06_el_movil_y_el_backoffice_encienden(t):
    """E-06 (VU6-06)."""
    for sid, tipo in (("app-movil", "MOBILE_USER"), ("backoffice", "BACKOFFICE_USER")):
        otra, ev = _otra(sid, tipo)
        caso = _caso(inventario=[], registro=[otra], evidencia=ev)
        t.igual("E-06 %s enciende" % tipo, "TRUE", CHECK.senal(caso)["value"])
        t.igual("E-06 %s sale en surfaces" % tipo, [sid],
                [s["surfaceId"] for s in CHECK.evaluar(caso)["surfaces"]])


def test_e07_un_log_interno_solo_no_enciende(t):
    """E-07 (VU6-07)."""
    log = _vis("log", fuente="INTERNAL_LOG")
    caso = _caso(registro=[_sup(evidencia=["log"])], evidencia=[log, OBS])
    t.igual("E-07 un INTERNAL_LOG solo no enciende", "UNRESOLVED", CHECK.senal(caso)["value"])
    t.igual("E-07 y el check no se evalua", "APPLICABILITY_UNRESOLVED", CHECK.evaluar(caso)["state"])
    t.igual("E-07 tampoco impide apagarla: el log esta fuera de la senal", "FALSE",
            CHECK.senal(_caso(registro=[], evidencia=[_ausente(), log]))["value"])
    t.igual("E-07 una fuente debil no apaga", "UNRESOLVED",
            CHECK.senal(_caso(registro=[], evidencia=[_ausente("README_STATEMENT")]))["value"])
    t.igual("E-07 una ausencia autoritativa apaga y no aplica", "NOT_APPLICABLE",
            _estado(registro=[], evidencia=[_ausente()]))


def test_e08_un_alcance_sin_cubrir(t):
    """E-08 (VU6-08)."""
    caso = _caso(registro=[], evidencia=[])
    t.igual("E-08 UNRESOLVED", "UNRESOLVED", CHECK.senal(caso)["value"])
    t.igual("E-08 y el check", "APPLICABILITY_UNRESOLVED", CHECK.evaluar(caso)["state"])
    t.igual("E-08 con el backoffice sin nada y el portal ausente, tambien", "UNRESOLVED",
            CHECK.senal(_caso([SUPERFICIE, BACKOFFICE], [], [_ausente()]))["value"])
    t.igual("E-08 un alcance vacio no es FALSE", "UNRESOLVED",
            CHECK.senal(_caso([], [], []))["value"])
    t.igual("E-08 tampoco en lo que deriva el check", ("UNRESOLVED", "APPLICABILITY_UNRESOLVED"),
            tuple(CHECK.evaluar(_caso([], [], []))[k] for k in ("signalValue", "state")))


# -- El escenario ------------------------------------------------------------------

def test_e09_un_mensaje_controlado_cumple(t):
    """E-09 (VU6-09)."""
    r = _r()
    t.igual("E-09 PASS", "PASS", r["state"])
    t.igual("E-09 el escenario cumple", "PASS", _x(r)["state"])
    t.igual("E-09 con su evidencia de comportamiento", ["obs"], _x(r)["evidenceUsed"]["behaviour"])
    t.verdadero("E-09 aprueba", CHECK.aprueba(r))
    t.igual("E-09 y en seguridad cumple", "COMPLIANT", _vu6_en_seguridad(r)["result"])
    t.igual("E-09 sin evidencia, no cumple", SIN_CUST,
            _estado(registro=[_sup(escenarios=[_esc(evidencia=[])])]))


def _expuesto(t, escenario, valor, esperado, fuente="EXPOSED_OUTPUT_OBSERVATION", owner=None,
              tipo="WEB_USER"):
    item = _obs("expuesto", valor=valor, fuente=fuente)
    honesto = dict(resultado=valor)
    r = _r(registro=[_sup(tipo=tipo, owner=owner or "APPLICATION_CONTROLLED", escenarios=[
        _esc(evidencia=["expuesto"], **honesto)])], evidencia=[VIS, item])
    t.igual("%s %s" % (escenario, esperado), esperado, r["state"])
    t.igual("%s el escenario" % escenario, esperado, _x(r)["state"])
    t.igual("%s con su evidencia" % escenario, ["expuesto"], _x(r)["evidenceUsed"]["exposure"])
    t.igual("%s es FAIL en seguridad" % escenario, "NON_COMPLIANT", _vu6_en_seguridad(r)["result"])
    t.igual("%s sin citarla no es FAIL" % escenario, SIN_CUST,
            _r(registro=[_sup(escenarios=[_esc(evidencia=[], **honesto)])],
               evidencia=[VIS, item])["state"])
    t.igual("%s de una clase que no sostiene no es FAIL" % escenario, SIN_CUST,
            _r(registro=[_sup(escenarios=[_esc(evidencia=["expuesto"], **honesto)])],
               evidencia=[VIS, dict(item, sourceType="SOURCE_CODE")])["state"])
    return r


def test_e10_la_pagina_de_debug_del_framework(t):
    """E-10 (VU6-10)."""
    _expuesto(t, "E-10 debug del framework", POR_DEFECTO, POR_DEFECTO, owner="FRAMEWORK_DEFAULT")


def test_e11_el_stack_trace_expuesto(t):
    """E-11 (VU6-11)."""
    _expuesto(t, "E-11 stack trace", CRUDO, CRUDO, fuente="INTEGRATION_TEST")


def test_e12_la_pagina_por_defecto_del_servidor(t):
    """E-12 (VU6-12)."""
    r = _expuesto(t, "E-12 pagina del servidor", POR_DEFECTO, POR_DEFECTO,
                  owner="SERVER_PLATFORM_DEFAULT")
    t.igual("E-12 el dueno viaja", "SERVER_PLATFORM_DEFAULT", _s(r)["owner"])
    t.verdadero("E-12 y no aprueba", not CHECK.aprueba(r))


def _infra(t, escenario, item, **registro):
    r = _r(registro=[_sup(escenarios=[_esc(evidencia=[item["evidenceId"]], **registro)])],
           evidencia=[VIS, item])
    t.igual("%s INFRASTRUCTURE_DETAIL_EXPOSED" % escenario, INFRA, r["state"])
    t.igual("%s con su evidencia" % escenario, [item["evidenceId"]],
            _x(r)["evidenceUsed"]["exposure"])
    t.igual("%s FAIL en seguridad" % escenario, "NON_COMPLIANT", _vu6_en_seguridad(r)["result"])
    t.igual("%s con el registro diciendo que cumple, igual" % escenario, INFRA,
            _con_ademas(item)["state"])
    t.igual("%s sin citarla no es FAIL" % escenario, SIN_CUST,
            _r(evidencia=EVIDENCIA + [item])["state"])


def test_e13_una_ruta_expuesta(t):
    """E-13 (VU6-13)."""
    _infra(t, "E-13 ruta del sistema de archivos",
           _obs("ruta", valor=INFRA, fuente="INTEGRATION_TEST"), resultado=INFRA)


def test_e14_una_ip_interna(t):
    """E-14 (VU6-14)."""
    _infra(t, "E-14 IP interna",
           _e("ip", "EXPOSED_OUTPUT_OBSERVATION", "TECHNICAL_DETAIL_EXPOSURE", "DETECTED"),
           detalle="DETECTED", resultado="UNRESOLVED")


def test_e15_una_excepcion_del_driver(t):
    """E-15 (VU6-15)."""
    _infra(t, "E-15 excepcion de la base",
           _obs("driver", valor=INFRA, fuente="CONTRACT_TEST"), resultado=INFRA)


def test_e16_un_diagnostico_de_la_plataforma(t):
    """E-16 (VU6-16)."""
    _infra(t, "E-16 diagnostico del contenedor",
           _e("contenedor", "ASSESSMENT_FINDING", "TECHNICAL_DETAIL_EXPOSURE", "DETECTED"),
           detalle="DETECTED", resultado="UNRESOLVED")
    t.igual("E-16 NONE no es exposicion", "PASS",
            _con_ademas(_e("nada", "ASSESSMENT_FINDING", "TECHNICAL_DETAIL_EXPOSURE", "NONE"))
            ["state"])


# -- Lo que Vu6 no fija ------------------------------------------------------------

def _con_texto(texto, eid="obs"):
    return _r(evidencia=[VIS, dict(_obs(eid), reference=texto)])


def test_e17_ningun_texto_se_exige(t):
    """E-17 (VU6-17)."""
    t.igual("E-17 un mensaje que no dice `Ocurrio un error` cumple", "PASS",
            _con_texto("la pantalla dice: No pudimos completar su tramite")["state"])
    t.igual("E-17 igual que uno que si lo dice",
            _json(_con_texto("la pantalla dice: Ocurrió un error")),
            _json(_con_texto("la pantalla dice: No pudimos completar su tramite")))
    t.verdadero("E-17 el modulo no tiene ninguna frase de error",
                not [s for s in _literales() if "ocurri" in s.lower() or "lo sentimos" in s.lower()])


def test_e18_dos_textos_en_castellano(t):
    """E-18 (VU6-18)."""
    uno = _con_texto("mensaje: Hubo un problema, intente mas tarde")
    otro = _con_texto("mensaje: El servicio no esta disponible en este momento")
    t.igual("E-18 cumple", "PASS", uno["state"])
    t.igual("E-18 el mismo resultado entero", _json(uno), _json(otro))


def test_e19_ingles_y_castellano(t):
    """E-19 (VU6-19)."""
    t.igual("E-19 el mismo resultado entero",
            _json(_con_texto("mensaje: Algo salio mal")),
            _json(_con_texto("message: Something went wrong")))


def test_e20_dos_formas_json(t):
    """E-20 (VU6-20)."""
    api, ev = _otra("api", "API_CONSUMER")

    def con(ref):
        e = [dict(x, reference=ref) if x["evidenceId"] == "obs-api" else x for x in ev]
        return _r(inventario=[], registro=[api], evidencia=e)
    uno = con('{"error": {"code": "E1", "message": "fallo"}}')
    otro = con('{"title": "Error", "status": 500, "detail": "reintente", "traceId": "t-1"}')
    t.igual("E-20 cumple", "PASS", uno["state"])
    t.igual("E-20 el mismo resultado entero", _json(uno), _json(otro))


def test_e21_el_componente_no_decide(t):
    """E-21 (VU6-21)."""
    t.igual("E-21 un toast y una pagina completa dan lo mismo",
            _json(_con_texto("componente Toast con el mensaje")),
            _json(_con_texto("pagina de error completa con la marca")))
    t.igual("E-21 cumple", "PASS", _con_texto("modal de error")["state"])


def _api_con(escenarios, extra=()):
    """La api, sola en el alcance, con sus escenarios y su evidencia."""
    alcance = _alcance("api")
    vis = _vis("vis-api", sup="api")
    return _r(inventario=[], registro=[_sup("api", "API_CONSUMER", escenarios=escenarios,
                                            evidencia=[alcance["evidenceId"], "vis-api"])],
              evidencia=[alcance, vis] + list(extra))


def _inesperado_api(eid="obs-api", **k):
    return (_esc(evidencia=[eid]), _obs(eid, sup="api", fuente="CONTRACT_TEST", **k))


def _status(eid, clase, sup="api", esc="inesperado", fuente="CONTRACT_TEST"):
    return _e(eid, fuente, "HTTP_STATUS_CLASS", clase, sup=[sup], esc=[esc])


def test_e22_el_codigo_de_error_no_decide(t):
    """E-22 (VU6-22)."""
    esc_i, obs_i = _inesperado_api()

    def validacion(ref, clase="4xx"):
        st = dict(_status("st-val", clase, esc="validacion"), reference=ref)
        ok = _obs("obs-val", sup="api", esc="validacion", fuente="CONTRACT_TEST")
        return _api_con([esc_i, _esc("validacion", "VALIDATION_ERROR",
                                     evidencia=["obs-val", "st-val"])], [obs_i, ok, st])
    c400, c422 = validacion("HTTP 400"), validacion("HTTP 422")
    t.igual("E-22 cumple con 400", "PASS", c400["state"])
    t.igual("E-22 400 y 422 dan lo mismo", _json(c400), _json(c422))
    t.igual("E-22 sin contrato ni un 200 se juzga", "PASS", validacion("HTTP 200", "2xx")["state"])


# -- Cada superficie por su cuenta -----------------------------------------------------

def test_e23_el_frontend_no_tapa_la_api(t):
    """E-23 (VU6-23)."""
    api, ev = _otra("api", "API_CONSUMER", valor=CRUDO)
    r = _r(registro=[_sup(), api], evidencia=EVIDENCIA + ev)
    t.igual("E-23 FAIL", CRUDO, r["state"])
    t.igual("E-23 el frontend cumple", "PASS", _s(r)["state"])
    t.igual("E-23 la api falla", CRUDO, _s(r, "api")["state"])


def test_e24_la_api_no_tapa_el_backoffice(t):
    """E-24 (VU6-24)."""
    api, ev = _otra("api", "API_CONSUMER")
    back, ev2 = _otra("backoffice", "BACKOFFICE_USER", valor=POR_DEFECTO,
                      fuente="EXPOSED_OUTPUT_OBSERVATION")
    r = _r(inventario=[], registro=[api, back], evidencia=ev + ev2)
    t.igual("E-24 FAIL", POR_DEFECTO, r["state"])
    t.igual("E-24 la api cumple", "PASS", _s(r, "api")["state"])
    t.igual("E-24 el backoffice falla", POR_DEFECTO, _s(r, "backoffice")["state"])


def test_e25_un_escenario_no_tapa_otro(t):
    """E-25 (VU6-25)."""
    abierto = _esc("validacion", "VALIDATION_ERROR", resultado="UNRESOLVED", evidencia=[])
    r = _r(registro=[_sup(escenarios=[_esc(), abierto])])
    t.igual("E-25 no pasa", SIN_CUST, r["state"])
    t.igual("E-25 aunque el inesperado cumpla", "PASS", _x(r)["state"])
    t.igual("E-25 el otro sin resolver", SIN_CUST, _x(r, eid="validacion")["state"])
    t.igual("E-25 en seguridad no cumple", "UNRESOLVED", _vu6_en_seguridad(r)["result"])


def _caminos(tipos, eid="caminos", fuente="PROJECT_REQUIREMENT", sup="portal"):
    return _e(eid, fuente, "ERROR_PATH_SCOPE", sup=[sup], esc=None, tipos=tipos)


def test_e26_sin_el_error_inesperado(t):
    """E-26 (VU6-26)."""
    solo_validacion = _esc("validacion", "VALIDATION_ERROR", evidencia=["obs-val"])
    ok = _obs("obs-val", esc="validacion")
    r = _r(registro=[_sup(escenarios=[solo_validacion])], evidencia=[VIS, ok])
    t.igual("E-26 sin UNEXPECTED_ERROR no se cubre", SIN_COB, r["state"])
    t.igual("E-26 y lo dice", [{"surfaceId": "portal", "errorTypes": [INESPERADO]}],
            r["coverage"]["missingErrorTypes"])
    t.igual("E-26 y el escenario que hay cumple", "PASS", _x(r, eid="validacion")["state"])
    caminos = _caminos(["NOT_FOUND"])
    exige = _r(registro=[_sup(evidencia=["vis", "caminos"])], evidencia=EVIDENCIA + [caminos])
    t.igual("E-26 un ERROR_PATH_SCOPE citado exige su tipo", SIN_COB, exige["state"])
    t.igual("E-26 y nombra el que falta", [{"surfaceId": "portal", "errorTypes": ["NOT_FOUND"]}],
            exige["coverage"]["missingErrorTypes"])
    con = _r(registro=[_sup(escenarios=[_esc(), _esc("no-existe", "NOT_FOUND",
                                                     evidencia=["obs-nf"])],
                            evidencia=["vis", "caminos"])],
             evidencia=EVIDENCIA + [caminos, _obs("obs-nf", esc="no-existe")])
    t.igual("E-26 con el tipo exigido traido, pasa", "PASS", con["state"])
    t.igual("E-26 sin citarlo no exige", "PASS", _estado(evidencia=EVIDENCIA + [caminos]))
    t.igual("E-26 de una fuente que no es autoritativa no exige", "PASS",
            _estado(registro=[_sup(evidencia=["vis", "caminos"])],
                    evidencia=EVIDENCIA + [_caminos(["NOT_FOUND"], fuente="README_STATEMENT")]))


# -- Los logs ----------------------------------------------------------------------

def _log(valor=CRUDO, eid="log"):
    return _obs(eid, valor=valor, fuente="INTERNAL_LOG")


def test_e27_un_stack_trace_en_el_log(t):
    """E-27 (VU6-27)."""
    r = _con_ademas(_log())
    t.igual("E-27 citado, no hace FAIL", "PASS", r["state"])
    t.igual("E-27 y es insuficiente", ["log"], _x(r)["insufficient"])
    t.igual("E-27 no citado tampoco", "PASS", _estado(evidencia=EVIDENCIA + [_log()]))
    solo = _solo_con(_log(), resultado=CRUDO)
    t.igual("E-27 solo, no es FAIL", SIN_CUST, solo["state"])
    t.igual("E-27 un log con DETECTED tampoco", "PASS",
            _con_ademas(_e("log-d", "INTERNAL_LOG", "TECHNICAL_DETAIL_EXPOSURE", "DETECTED"))
            ["state"])


def test_e28_el_diagnostico_reenviado(t):
    """E-28 (VU6-28)."""
    reenviado = _obs("reenviado", valor=CRUDO, fuente="INTERNAL_DIAGNOSTIC_FORWARDED", sup="api")
    api, ev = _otra("api", "API_CONSUMER", extra=[reenviado])
    api["scenarios"][0]["evidence"].append("reenviado")
    r = _r(inventario=[], registro=[api], evidencia=ev)
    t.igual("E-28 llega al consumidor de la API: FAIL", CRUDO, r["state"])
    t.igual("E-28 con su evidencia", ["reenviado"], _x(r, "api")["evidenceUsed"]["exposure"])
    api2, ev2 = _otra("api", "API_CONSUMER", extra=[reenviado])
    t.igual("E-28 sin citarlo no es FAIL", SIN_CUST,
            _estado(inventario=[], registro=[api2], evidencia=ev2))
    # Pase 1 del refutador: el value del diagnostico reenviado no lo salva.
    amable = _obs("reenviado", valor="CUSTOMIZED_SAFE", fuente="INTERNAL_DIAGNOSTIC_FORWARDED",
                  sup="api")
    visible = _e("reenviado", "INTERNAL_DIAGNOSTIC_FORWARDED", "USER_FACING_ERROR", "PRESENT",
                 sup=["api"], esc=None)
    for nombre, item in (("que dice CUSTOMIZED_SAFE", amable),
                         ("que solo dice USER_FACING_ERROR: PRESENT", visible)):
        citado, ev3 = _otra("api", "API_CONSUMER", extra=[item])
        citado["scenarios"][0]["evidence"].append("reenviado")
        r3 = _r(inventario=[], registro=[citado], evidencia=ev3)
        t.igual("E-28 citado %s: FAIL" % nombre, CRUDO, r3["state"])
        t.igual("E-28 citado %s: con su evidencia" % nombre, ["reenviado"],
                _x(r3, "api")["evidenceUsed"]["exposure"])
        solo, ev4 = _otra("api", "API_CONSUMER", extra=[item])
        solo["scenarios"][0]["evidence"] = ["reenviado"]
        r4 = _r(inventario=[], registro=[solo], evidencia=ev4)
        t.igual("E-28 solo %s: FAIL y no sostiene el escenario" % nombre,
                (CRUDO, []), (r4["state"], _x(r4, "api")["evidenceUsed"]["behaviour"]))
        suelto, ev5 = _otra("api", "API_CONSUMER", extra=[item])
        t.igual("E-28 no citado %s: sin resolver, nunca FAIL" % nombre, SIN_CUST,
                _estado(inventario=[], registro=[suelto], evidencia=ev5))


def test_e29_ningun_texto_de_evidencia_sale(t):
    """E-29 (VU6-29)."""
    texto = ("java.lang.IllegalStateException at com.gcba.Tramite(Tramite.java:42) "
             "host 10.20.30.40 /var/app/conf/app.yml")
    crudo = dict(_obs("traza", valor=CRUDO), reference=texto)
    casos = {"pasa": _r(evidencia=[dict(VIS, reference=texto), dict(OBS, reference=texto)]),
             "falla": _con_ademas(crudo),
             "no citada": _r(evidencia=EVIDENCIA + [crudo]),
             "log": _con_ademas(dict(_log(), reference=texto))}
    unidad = {n: normativa.resolucion({"userFacingErrorPresent": True},
                                      evidencia={"ES0902.Vu6": r})["standards"]["ES0902"]["rules"]["Vu6"]
              for n, r in casos.items()}
    senal = CHECK.senal(_caso(evidencia=[dict(VIS, reference=texto), OBS]))
    carpeta = tempfile.mkdtemp(prefix="vu6_29_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-6029")
        for i, r in enumerate(casos.values()):
            for evento in prod.desde_regla(_vu6_en_seguridad(r), "GCBA-6029",
                                           {"project": "Sistema", "environment": "QA"},
                                           "2026-09-24T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        en_el_libro = Path(ruta).read_text(encoding="utf-8")
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    for trozo in ("IllegalStateException", "Tramite.java", "10.20.30.40", "/var/app"):
        for nombre, r in casos.items():
            t.no_contiene("E-29 `%s` no sale en la salida (%s)" % (trozo, nombre), trozo, _json(r))
            t.no_contiene("E-29 `%s` no sale en rules.Vu6 (%s)" % (trozo, nombre), trozo,
                          _json(unidad[nombre]))
        t.no_contiene("E-29 `%s` no sale en la senal" % trozo, trozo, _json(senal))
        t.no_contiene("E-29 `%s` no llega al libro" % trozo, trozo, en_el_libro)
    t.igual("E-29 solo su id", ["obs", "traza"], _x(casos["falla"])["contradictedBy"]
            + _x(casos["falla"])["evidenceUsed"]["exposure"])
    t.contiene("E-29 y el id llega a la unidad", "traza", unidad["falla"]["evidence"])


# -- La semantica HTTP ----------------------------------------------------------------

def test_e30_un_5xx_customizado_cumple(t):
    """E-30 (VU6-30)."""
    esc, obs = _inesperado_api()
    esc["evidence"].append("st")
    r = _api_con([esc], [obs, _status("st", "5xx")])
    t.igual("E-30 cumple", "PASS", r["state"])
    t.igual("E-30 con su estado", ["st"], _x(r, "api")["evidenceUsed"]["httpStatus"])
    t.igual("E-30 la api es HTTP", True, _s(r, "api")["http"])


def test_e31_un_error_inesperado_con_2xx(t):
    """E-31 (VU6-31)."""
    for clase in ("2xx", "3xx"):
        esc, obs = _inesperado_api()
        esc["evidence"].append("st")
        r = _api_con([esc], [obs, _status("st", clase)])
        t.igual("E-31 %s enmascara" % clase, ENMASC, r["state"])
        t.igual("E-31 %s con su evidencia" % clase, ["st"], _x(r, "api")["evidenceUsed"]["httpStatus"])
        t.igual("E-31 %s FAIL en seguridad" % clase, "NON_COMPLIANT", _vu6_en_seguridad(r)["result"])
        t.igual("E-31 %s con la fuente de apoyo" % clase, ("ES0901", "11", 22),
                tuple((_x(r, "api").get("supportingSource") or {}).get(k)
                      for k in ("standard", "section", "page")))
        esc2, obs2 = _inesperado_api()
        t.igual("E-31 %s sin citarla no es FAIL" % clase, SIN_CUST,
                _api_con([esc2], [obs2, _status("st", clase)])["state"])
        t.igual("E-31 %s de una clase que no sostiene no es FAIL" % clase, "PASS",
                _api_con([esc], [obs, _status("st", clase, fuente="CONFIGURATION")])["state"])
    web = _status("st", "2xx", sup="portal")
    t.igual("E-31 en la web tambien: el estado prueba que responde por HTTP", ENMASC,
            _con_ademas(web)["state"])
    t.igual("E-31 un 404 convertido en 200 sin contrato no se juzga", "PASS",
            _api_con([_esc(evidencia=["obs-api"]), _esc("nf", "NOT_FOUND", evidencia=["obs-nf", "st"])],
                     [_inesperado_api()[1], _obs("obs-nf", sup="api", esc="nf"),
                      _status("st", "2xx", esc="nf")])["state"])
    contrato = _e("contrato", "API_CONTRACT", "API_ERROR_CONTRACT", "ERROR", sup=["api"], esc=["nf"])
    t.igual("E-31 con un contrato citado que dice que es error, si", ENMASC,
            _api_con([_esc(evidencia=["obs-api"]),
                      _esc("nf", "NOT_FOUND", evidencia=["obs-nf", "st", "contrato"])],
                     [_inesperado_api()[1], _obs("obs-nf", sup="api", esc="nf"),
                      _status("st", "2xx", esc="nf"), contrato])["state"])
    t.igual("E-31 con contrato, un 3xx no es de exito", "PASS",
            _api_con([_esc(evidencia=["obs-api"]),
                      _esc("nf", "NOT_FOUND", evidencia=["obs-nf", "st", "contrato"])],
                     [_inesperado_api()[1], _obs("obs-nf", sup="api", esc="nf"),
                      _status("st", "3xx", esc="nf"), contrato])["state"])


def test_e32_customizar_no_es_enmascarar(t):
    """E-32 (VU6-32)."""
    for clase in ("5xx", "4xx"):
        esc, obs = _inesperado_api()
        esc["evidence"].append("st")
        r = _api_con([esc], [obs, _status("st", clase)])
        t.igual("E-32 cuerpo customizado con %s: cumple" % clase, "PASS", r["state"])
        t.verdadero("E-32 y no es HTTP_ERROR_SEMANTICS_MASKED (%s)" % clase,
                    ENMASC not in r["states"])


def test_e33_es0901_se_cita_y_no_se_evalua(t):
    """E-33 (VU6-33)."""
    for nombre, r in (("pasa", _r()), ("sin senal", CHECK.evaluar({}))):
        t.igual("E-33 la fuente de apoyo (%s)" % nombre,
                [{"standard": "ES0901", "version": "6.3", "section": "11", "page": 22,
                  "title": "Errores HTTP no enmascarados", "extract": "normativa/extractos/ES0901.md",
                  "role": "SUPPORTING_SOURCE"}], r["supportingSources"])
    extracto = (RAIZ / "normativa" / "extractos" / "ES0901.md").read_text(encoding="utf-8")
    t.contiene("E-33 el extracto existe y la nombra", "**Errores HTTP no enmascarados** (pág. 22)",
               extracto)
    base = _json(_r())
    for valor in ("PASS", "FAIL"):
        resultado = _e("es0901", "OTHER_AUTHORITATIVE_EVIDENCE", "RULE_RESULT", valor,
                       reference="ES0901 §11")
        t.igual("E-33 con un resultado de ES0901 en %s, Vu6 no cambia" % valor, base,
                _json(_r(evidencia=EVIDENCIA + [resultado])))
    t.igual("E-33 evaluar no recibe resultados de ES0901", ["caso", "senal", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    ev, _ = CHECK.para_seguridad(_r())
    t.igual("E-33 lo que sale va solo a los controles de Vu6",
            ["custom-error-message-compliance", "custom-error-messages-required"],
            sorted(ev["controlResults"]))
    fuera = {k for k in _claves(_r()) if "es0901" in k.lower()}
    t.igual("E-33 ningun campo de la salida es un resultado de ES0901", set(), fuera)


# -- El manejador y el framework -------------------------------------------------------

def test_e34_el_manejador_presente_no_cumple(t):
    """E-34 (VU6-34)."""
    for fuente in ("ERROR_HANDLER_PRESENCE", "FRAMEWORK_OWNERSHIP", "SOURCE_CODE", "CONFIGURATION",
                   "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT"):
        r = _solo_con(_obs("parecido", fuente=fuente))
        t.igual("E-34 `%s` solo no cumple" % fuente, SIN_CUST, r["state"])
        t.igual("E-34 `%s` no sostiene nada" % fuente, [], _x(r)["evidenceUsed"]["behaviour"])
        t.igual("E-34 `%s` se informa como insuficiente" % fuente, ["parecido"], _x(r)["insufficient"])


def _mapeo(eid="mapeo", valor="CUSTOMIZED_SAFE", sup=("portal",), tipos=(INESPERADO,), esc=None):
    return _e(eid, "ERROR_HANDLER_MAPPING", "ERROR_OUTPUT", valor, sup=sup, esc=esc, tipos=tipos)


def test_e35_el_mapeo_que_nombra_la_superficie_y_el_tipo(t):
    """E-35 (VU6-35)."""
    mapeo = _mapeo(tipos=(INESPERADO, "VALIDATION_ERROR"))
    r = _r(registro=[_sup(escenarios=[_esc(evidencia=["mapeo"]),
                                   _esc("validacion", "VALIDATION_ERROR", evidencia=["mapeo"])])],
        evidencia=[VIS, mapeo])
    t.igual("E-35 cumple", "PASS", r["state"])
    t.igual("E-35 los dos escenarios con el mapeo", [["mapeo"], ["mapeo"]],
            [x["evidenceUsed"]["behaviour"] for x in _s(r)["scenarios"]])
    t.igual("E-35 sin nombrar el tipo, no", SIN_CUST,
            _solo_con(_mapeo(tipos=None, esc=["inesperado"]))["state"])
    t.igual("E-35 sin nombrar la superficie, no", SIN_CUST,
            _solo_con(_mapeo(sup=None))["state"])
    t.igual("E-35 con otro tipo, no", SIN_CUST, _solo_con(_mapeo(tipos=["NOT_FOUND"]))["state"])
    t.igual("E-35 con un escenario sin cubrir, no pasa", SIN_CUST,
            _r(registro=[_sup(escenarios=[_esc(evidencia=["mapeo"]),
                                          _esc("validacion", "VALIDATION_ERROR",
                                               evidencia=["mapeo"])])],
               evidencia=[VIS, _mapeo()])["state"])


def test_e36_el_framework_customizado_por_configuracion(t):
    """E-36 (VU6-36)."""
    r = _r(registro=[_sup(owner="FRAMEWORK_DEFAULT")])
    t.igual("E-36 cumple", "PASS", r["state"])
    t.igual("E-36 y el dueno viaja", "FRAMEWORK_DEFAULT", _s(r)["owner"])
    duenio = _obs("duenio", valor=POR_DEFECTO, fuente="FRAMEWORK_OWNERSHIP")
    t.igual("E-36 un FRAMEWORK_OWNERSHIP que supone la pagina por defecto no es FAIL", "PASS",
            _r(registro=[_sup(owner="FRAMEWORK_DEFAULT", escenarios=[
                _esc(evidencia=["obs", "duenio"])])], evidencia=EVIDENCIA + [duenio])["state"])
    t.igual("E-36 ni solo", SIN_CUST, _solo_con(duenio)["state"])


def test_e37_el_mapeo_contra_la_observacion(t):
    """E-37 (VU6-37)."""
    visto = _obs("visto", valor=CRUDO, fuente="EXPOSED_OUTPUT_OBSERVATION")
    r = _solo_con(_mapeo(), visto)
    t.igual("E-37 FAIL", CRUDO, r["state"])
    t.igual("E-37 el mapeo queda contradicho", ["mapeo"], _x(r)["contradictedBy"])
    t.igual("E-37 con la observacion no citada, sin resolver", SIN_CUST,
            _r(registro=[_sup(escenarios=[_esc(evidencia=["mapeo"])])],
               evidencia=[VIS, _mapeo(), visto])["state"])


# -- La prueba -------------------------------------------------------------------------

def _con_prueba(tipo, eid, **cambios):
    qa = _prueba(eid="qa", esc=eid, **cambios)
    return _r(registro=[_sup(escenarios=[_esc(), _esc(eid, tipo, evidencia=["qa"],
                                                      modo="AUTHORIZED_QA_RUNTIME_TEST")])],
              evidencia=EVIDENCIA + [qa])


def test_e38_una_prueba_en_qa_con_un_error_de_validacion(t):
    """E-38 (VU6-38)."""
    r = _con_prueba("VALIDATION_ERROR", "validacion")
    t.igual("E-38 cuenta", "PASS", r["state"])
    t.igual("E-38 con la prueba", ["qa"], _x(r, eid="validacion")["evidenceUsed"]["behaviour"])
    t.igual("E-38 y la prueba segura no tiene motivos", [], CHECK.prueba_segura(_prueba()))


def test_e39_un_recurso_inexistente_o_una_peticion_invalida(t):
    """E-39 (VU6-39)."""
    for tipo, eid in (("NOT_FOUND", "no-existe"), ("INVALID_REQUEST", "invalida")):
        t.igual("E-39 %s cuenta" % tipo, "PASS", _con_prueba(tipo, eid)["state"])
    t.verdadero("E-39 la prueba segura no mira el tipo de error",
                "errorType" not in inspect.getsource(CHECK.prueba_segura))


def test_e40_una_caida_o_una_prueba_destructiva(t):
    """E-40 (VU6-40)."""
    for campo, motivo in (("infrastructureOutageInduced", "INFRASTRUCTURE_OUTAGE_INDUCED"),
                          ("destructive", "DESTRUCTIVE")):
        r = _solo_con(_prueba(**{campo: True}))
        t.igual("E-40 %s no cuenta" % campo, INSEGURA, r["state"])
        t.contiene("E-40 %s dice por que" % campo, motivo, _x(r)["unsafe"])
        t.igual("E-40 %s en falso cuenta" % campo, "PASS", _solo_con(_prueba(**{campo: False}))["state"])


def test_e41_datos_personales_o_secretos_reales(t):
    """E-41 (VU6-41)."""
    for campo, motivo in (("realPersonalData", "REAL_PERSONAL_DATA"), ("realSecrets", "REAL_SECRETS")):
        r = _solo_con(_prueba(**{campo: True}))
        t.igual("E-41 %s no cuenta" % campo, INSEGURA, r["state"])
        t.contiene("E-41 %s dice por que" % campo, motivo, _x(r)["unsafe"])
        t.igual("E-41 %s en falso cuenta" % campo, "PASS", _solo_con(_prueba(**{campo: False}))["state"])
    t.igual("E-41 ninguna condicion exige datos reales", [], CHECK.prueba_segura(_prueba()))


def test_e42_las_condiciones_inseguras(t):
    """E-42 (VU6-42)."""
    for nombre, cambios, motivo in (
            ("sin autorizacion", {"authorized": None}, "NOT_AUTHORIZED"),
            ("autorizada en falso", {"authorized": False}, "NOT_AUTHORIZED"),
            ("en produccion", {"environment": "PRD"}, "PRODUCTION"),
            ("en un ambiente desconocido", {"environment": "STAGING"}, "ENVIRONMENT_UNKNOWN"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED"),
            ("sin datos sinteticos", {"syntheticData": None}, "NOT_SYNTHETIC_DATA"),
            ("con datos no sinteticos", {"syntheticData": False}, "NOT_SYNTHETIC_DATA"),
            ("con secretos registrados", {"rawSecretsLogged": True}, "RAW_SECRETS_LOGGED")):
        r = _solo_con(_prueba(**cambios))
        t.igual("E-42 %s" % nombre, INSEGURA, r["state"])
        t.contiene("E-42 %s dice por que" % nombre, motivo, _x(r)["unsafe"])
    for ambiente in ("QA", "DEV", "HML", "OTHER"):
        t.igual("E-42 en %s cuenta" % ambiente, "PASS", _solo_con(_prueba(environment=ambiente))["state"])
    t.igual("E-42 sin objetivo", SIN_OBJ, _solo_con(_prueba(outcome="UNAVAILABLE"))["state"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-42 el modulo no ejecuta nada: ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing", "selenium", "playwright",
                                 "time", "threading"}))


def test_e43_una_prueba_insegura_no_es_fail(t):
    """E-43 (VU6-43)."""
    crudo = _prueba(CRUDO, environment="PRD")
    t.igual("E-43 insegura que dice RAW, citada, no es FAIL", INSEGURA, _con_ademas(crudo)["state"])
    t.igual("E-43 y no citada tampoco", INSEGURA, _r(evidencia=EVIDENCIA + [crudo])["state"])
    t.igual("E-43 sin objetivo que dice RAW no es FAIL", SIN_OBJ,
            _con_ademas(_prueba(CRUDO, outcome="UNAVAILABLE"))["state"])
    t.igual("E-43 insegura con RAW en el registro no es FAIL", INSEGURA,
            _solo_con(crudo, resultado=CRUDO)["state"])
    t.igual("E-43 una ajena insegura que dice customizado no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(environment="PRD")]))


# -- Los limites ------------------------------------------------------------------------

def _pass_de(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {c for c in fila["policies"] + fila["checks"] + fila["reviews"]}


def _no_mueve(t, escenario, regla, senal):
    ev, _ = CHECK.para_seguridad(_r())
    base = {senal: True} if senal else {}
    sin = seguridad.resultado(regla, {}, base, MATRIZ)
    con = seguridad.resultado(regla, ev, dict(base, userFacingErrorPresent=True), MATRIZ)
    t.igual("%s el resultado de %s no cambia" % (escenario, regla), sin["result"], con["result"])
    t.verdadero("%s y no cumple" % escenario, con["result"] != "COMPLIANT")
    t.igual("%s y los controles de Vu6 no son los de %s" % (escenario, regla), [],
            sorted(set(ev["controlResults"]) & _pass_de(regla)))


def test_e44_el_pass_de_vu5_no_es_el_de_vu6(t):
    """E-44 (VU6-44)."""
    vu5 = VU5.evaluar({"inventory": {"version": "1.0", "surfaces": []},
                       "clients": {"version": "1.0", "clients": []}, "evidence": []}, True)
    ev5, _ = VU5.para_seguridad(dict(vu5, state="PASS"))
    sin = seguridad.resultado("Vu6", {}, {"userFacingErrorPresent": True}, MATRIZ)
    con = seguridad.resultado("Vu6", ev5, {"userFacingErrorPresent": True,
                                           "clientValidationPresent": True}, MATRIZ)
    t.igual("E-44 Vu5 en PASS no mueve a Vu6", sin["result"], con["result"])
    t.verdadero("E-44 y Vu6 no cumple", con["result"] != "COMPLIANT")
    t.igual("E-44 el check de Vu6 no recibe el resultado de Vu5", ["caso", "senal", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    t.igual("E-44 ni lo lee", _json(_r(senal=None)),
            _json(CHECK.evaluar(dict(_caso(), clients={"version": "1.0", "clients": []}))))


def test_e45_el_pass_de_vu6_no_es_el_de_vu5(t):
    """E-45 (VU6-45)."""
    _no_mueve(t, "E-45", "Vu5", "clientValidationPresent")


def test_e46_el_pass_de_vu6_no_es_el_de_vu7(t):
    """E-46 (VU6-46)."""
    _no_mueve(t, "E-46", "Vu7", None)


def test_e47_el_pass_de_vu6_no_es_el_de_vu10(t):
    """E-47 (VU6-47)."""
    _no_mueve(t, "E-47", "Vu10", "owaspApplicableAssetPresent")


def test_e48_el_pass_de_vu6_no_es_la_aprobacion(t):
    """E-48 (VU6-48)."""
    _no_mueve(t, "E-48", "C2", "securityHomologationPresent")
    ev, _ = CHECK.para_seguridad(_r())
    ids = ev["controlResults"][CHECK.CONTROL]["evidence"]
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK",
                                         "evidence": ids})
    t.igual("E-48 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])
    senal = {"userFacingErrorPresent": True, "securityHomologationPresent": True}
    sin = normativa.resolucion(senal)["standards"]["ES0902"]["rules"]["C2"]
    con = normativa.resolucion(senal, evidencia={"ES0902.Vu6": _r()})["standards"]["ES0902"]
    t.igual("E-48 y C2 en la unidad sigue igual", sin, con["rules"]["C2"])
    t.igual("E-48 mientras Vu6 pasa", "PASS", con["rules"]["Vu6"]["result"])


# -- El agregado -------------------------------------------------------------------------------

def test_e49_una_exposicion_en_cualquier_superficie(t):
    """E-49 (VU6-49)."""
    for valor in (POR_DEFECTO, CRUDO, INFRA):
        back, ev = _otra("backoffice", "BACKOFFICE_USER", valor=valor)
        r = _r(registro=[_sup(), back], evidencia=EVIDENCIA + ev)
        t.igual("E-49 %s en el backoffice hace FAIL el agregado" % valor, valor, r["state"])
        t.igual("E-49 aunque el portal cumpla (%s)" % valor, "PASS", _s(r)["state"])
        t.verdadero("E-49 y no aprueba (%s)" % valor, not CHECK.aprueba(r))
    back, ev = _otra("backoffice", "BACKOFFICE_USER", valor=CRUDO)
    api, ev2 = _otra("api", "API_CONSUMER", valor=POR_DEFECTO)
    dos = _r(registro=[_sup(), back, api], evidencia=EVIDENCIA + ev + ev2)
    t.igual("E-49 dos exposiciones distintas dan FAIL", "FAIL", dos["state"])
    t.igual("E-49 y las nombra", sorted([CRUDO, POR_DEFECTO]),
            sorted(s for s in dos["states"] if s in FALLAS and s != "FAIL"))


def test_e50_un_camino_material_sin_resolver(t):
    """E-50 (VU6-50)."""
    back, ev = _otra("backoffice", "BACKOFFICE_USER",
                     escenarios=[_esc(resultado="UNRESOLVED", evidencia=[])])
    r = _r(registro=[_sup(), back], evidencia=EVIDENCIA + ev)
    t.igual("E-50 no pasa", SIN_CUST, r["state"])
    t.igual("E-50 aunque el portal cumpla", "PASS", _s(r)["state"])
    t.igual("E-50 en seguridad no cumple", "UNRESOLVED", _vu6_en_seguridad(r)["result"])
    falla = _r(registro=[_sup(escenarios=[_esc(), _esc("x", "OTHER", resultado="UNRESOLVED",
                                                       evidencia=["crudo"])])],
               evidencia=EVIDENCIA + [_obs("crudo", valor=CRUDO, esc="x")])
    t.igual("E-50 una falla le gana a un sin resolver", CRUDO, falla["state"])


def test_e51_el_mismo_resultado(t):
    """E-51 (VU6-51)."""
    back, ev = _otra("backoffice", "BACKOFFICE_USER",
                     escenarios=[_esc(resultado="UNRESOLVED", evidencia=[])])
    api, ev2 = _otra("api", "API_CONSUMER")
    registro = [_sup(escenarios=[_esc(), _esc("validacion", "VALIDATION_ERROR",
                                              evidencia=["obs-val"])]), back, api]
    evid = EVIDENCIA + ev + ev2 + [_obs("obs-val", esc="validacion"), _obs("rep"), _obs("rep")]
    base = _json(_r([SUPERFICIE, BACKOFFICE], registro, evid))
    azar = random.Random(51)
    for vuelta in range(6):
        s, c, e = copy.deepcopy([SUPERFICIE, BACKOFFICE]), copy.deepcopy(registro), copy.deepcopy(evid)
        azar.shuffle(s)
        azar.shuffle(c)
        azar.shuffle(e)
        for x in c:
            azar.shuffle(x["scenarios"])
        t.igual("E-51 desordenado %d" % vuelta, base, _json(_r(s, c, e)))
    t.igual("E-51 los doce estados", sorted(LOS_12), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "observación") for f in ("NFC", "NFD"))
    for nombre, par in (("iguales", ("CUSTOMIZED_SAFE", "CUSTOMIZED_SAFE")),
                        ("cruda la NFC", (CRUDO, "CUSTOMIZED_SAFE")),
                        ("cruda la NFD", ("CUSTOMIZED_SAFE", CRUDO))):
        gemelas = [_obs(nfc, valor=par[0]), _obs(nfd, valor=par[1])]
        for orden in (gemelas, gemelas[::-1]):
            t.igual("E-51 gemelas en NFC y NFD (%s) no pasan ni fallan" % nombre, SIN_CUST,
                    _solo_con(*orden)["state"])
    t.igual("E-51 citar en NFD una evidencia en NFC es citarla", "PASS",
            _estado(registro=[_sup(escenarios=[_esc(evidencia=[nfd])])], evidencia=[VIS, _obs(nfc)]))
    dos = _r(registro=[_sup(escenarios=[_esc(nfc), _esc(nfd)])],
             evidencia=[VIS, _obs(esc=nfc)])
    t.igual("E-51 dos escenarios iguales en NFC son el mismo, repetido", (SIN_COB, ["portal/" + nfc]),
            (dos["state"], dos["coverage"]["duplicatedScenarios"]))
    t.igual("E-51 dos superficies iguales en NFC son la misma, repetida", [nfc],
            _r(registro=[_sup(), _sup(nfc), _sup(nfd)])["coverage"]["duplicatedSurfaces"])


def test_e52_la_trazabilidad(t):
    """E-52 (VU6-52)."""
    caminos = {"sin senal": CHECK.evaluar({}), "pasa": _r(),
               "falla": _con_ademas(_obs("crudo", valor=CRUDO)),
               "insegura": _solo_con(_prueba(environment="PRD")),
               "no aplica": _r(registro=[], evidencia=[_ausente()]),
               "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True)}
    for nombre, r in caminos.items():
        t.igual("E-52 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-52 %s la clave" % nombre, "ES0902.Vu6", r["ruleKey"])
        t.igual("E-52 %s el control" % nombre, "custom-error-message-compliance", r["control"])
    t.igual("E-52 un inventario invalido deja la cobertura sin resolver", SIN_COB,
            caminos["inventario invalido"]["state"])
    resultado = _r()
    vu6 = normativa.resolucion({"userFacingErrorPresent": True},
                               evidencia={"ES0902.Vu6": resultado})["standards"]["ES0902"]["rules"]["Vu6"]
    t.igual("E-52 la unidad lleva Vu6", ("APPLICABLE", "PASS"), (vu6["applicability"], vu6["result"]))
    t.igual("E-52 con sus superficies", ["portal"], vu6["surfaces"])
    t.igual("E-52 y su evidencia por id", ["obs"], vu6["evidence"])
    t.igual("E-52 y nada mas", ["applicability", "evidence", "result", "source", "surfaces"],
            sorted(vu6))
    t.igual("E-52 con la fuente", TRAZA, vu6["source"])
    falso = dict(resultado, control="otro-control")
    t.igual("E-52 un resultado ajeno no se proyecta", "UNRESOLVED",
            normativa.resolucion({"userFacingErrorPresent": True},
                                 evidencia={"ES0902.Vu6": falso})["standards"]["ES0902"]
            ["rules"]["Vu6"]["result"])
    t.igual("E-52 sin la senal no se proyecta", ("UNRESOLVED", []),
            tuple(normativa.resolucion({}, evidencia={"ES0902.Vu6": resultado})["standards"]
                  ["ES0902"]["rules"]["Vu6"][k] for k in ("result", "surfaces")))
    t.igual("E-52 con la senal en falso, NOT_APPLICABLE", "NOT_APPLICABLE",
            normativa.resolucion({"userFacingErrorPresent": False})["standards"]["ES0902"]
            ["rules"]["Vu6"]["result"])
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = normativa.resolucion({"userFacingErrorPresent": True},
                                       evidencia={"ES0902.Vu6": resultado})
    finally:
        normativa._ruta_de_evidencia = original
    vu6_sin = sin_lib["standards"]["ES0902"]["rules"]["Vu6"]
    t.igual("E-52 sin la lib la unidad se arma, con el estado y sin ids", ("PASS", [], []),
            (vu6_sin["result"], vu6_sin["surfaces"], vu6_sin["evidence"]))
    t.verdadero("E-52 y Vu5 sigue en la unidad", "Vu5" in sin_lib["standards"]["ES0902"]["rules"])


def test_e53_entra_al_libro_como_cualquier_regla(t):
    """E-53 (VU6-53)."""
    paquete = BIN / "reporte_seguridad"
    t.igual("E-53 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in paquete.iterdir() if p.is_file()))
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu6_53_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-6053")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _con_ademas(_obs("crudo", valor=CRUDO)), "NON_COMPLIANT"),
                     ("sin resolver", _r(registro=[_sup(escenarios=[_esc(resultado="UNRESOLVED")])]),
                      "UNRESOLVED"),
                     ("no aplica", _r(registro=[], evidencia=[_ausente()]), "NOT_APPLICABLE"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu6_en_seguridad(r)
            t.igual("E-53 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-6053", alcance,
                                           "2026-09-24T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-53 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-53 de ES0902.Vu6", [("ES0902", "Vu6", "ES0902.Vu6")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-53 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "NOT_APPLICABLE"],
                [e["result"] for e in eventos])
        t.igual("E-53 producido por desde_regla", ["desde_regla"] * 4,
                [e["details"]["producer"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    t.igual("E-53 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))
    t.igual("E-53 Vu6 en el dominio de validacion y manejo de errores", True,
            "Vu6" in [d for d in json.loads((REGLAS / "security-report-domains.json").read_text(
                encoding="utf-8"))["domains"] if d["domainId"] == "validation-error-handling"][0]
            ["rules"])


# -- Lo que agrega esta spec ------------------------------------------------------------------

def test_e54_ninguna_palabra_decide(t):
    """E-54."""
    npe = dict(OBS, reference="respuesta: java.lang.NullPointerException at Tramite.java:10")
    t.igual("E-54 una referencia con NullPointerException que establece customizado cumple", "PASS",
            _estado(evidencia=[VIS, npe]))
    neutro = dict(_obs("neutro", valor=CRUDO), reference="captura 3 del informe de QA")
    t.igual("E-54 una referencia neutra que establece RAW falla", CRUDO,
            _con_ademas(neutro)["state"])
    t.igual("E-54 el texto no mueve nada", _json(_estado(evidencia=[VIS, OBS])),
            _json(_estado(evidencia=[VIS, npe])))
    importados = {a.name for n in ast.walk(_arbol()) if isinstance(n, ast.Import) for a in n.names}
    t.verdadero("E-54 el modulo no importa `re`", "re" not in importados)
    for palabra in ("exception", "stack", "trace", "java", "traceback", "at ", "error:"):
        t.verdadero("E-54 ninguna literal busca `%s`" % palabra,
                    not [s for s in _literales() if s.lower() == palabra
                         or (palabra in s.lower() and len(s) < 16 and "_" not in s)])
    t.verdadero("E-54 nadie lee `reference` para decidir",
                "\"reference\"" not in "".join(
                    ast.get_source_segment(RUTA_CHECK.read_text(encoding="utf-8"), f) or ""
                    for f in ast.walk(_arbol()) if isinstance(f, ast.FunctionDef)
                    and f.name.startswith(("_paso", "_afirmaciones", "_nombra", "_lectura"))))


CREDENCIALES = ("password=hunter2abc", "contraseña=hunter2abc", "clave: hunter2abc",
                "access_token=hunter2abc", "api_key=hunter2abc", "Bearer abcdefghhunter2abc",
                "JSESSIONID=hunter2abc", "Cookie: SESSION=hunter2abc", "code=hunter2abc",
                "https://usuario:hunter2abc@db.example")


def test_e55_ningun_secreto(t):
    """E-55."""
    base_claves = set(_claves(_r()))
    base_senal = set(_claves(CHECK.senal(_caso())))
    base_unidad = set(_claves(normativa.resolucion(
        {"userFacingErrorPresent": True}, evidencia={"ES0902.Vu6": _r()})["standards"]["ES0902"]
        ["rules"]["Vu6"]))
    for texto in CREDENCIALES:
        casos = {
            "un surfaceId": _r(registro=[_sup(), _sup(texto)]),
            "un scenarioId": _r(registro=[_sup(escenarios=[_esc(texto)])],
                                evidencia=[VIS, _obs(esc=texto)]),
            "un id de evidencia citado": _r(registro=[_sup(escenarios=[_esc(evidencia=[texto])])],
                                            evidencia=[VIS, _obs(texto)]),
            "un httpStatusRef": _r(registro=[_sup(escenarios=[_esc(http=texto)])]),
            "un errorType": _r(registro=[_sup(escenarios=[_esc(), _esc("otro", texto)])]),
            "la senal": CHECK.senal(_caso(registro=[_sup(texto)], evidencia=[_vis(sup=texto)])),
            "rules.Vu6": normativa.resolucion(
                {"userFacingErrorPresent": True},
                evidencia={"ES0902.Vu6": _r(registro=[_sup(texto)])})["standards"]["ES0902"]
            ["rules"]["Vu6"],
            "rules.Vu6 por la evidencia": normativa.resolucion(
                {"userFacingErrorPresent": True},
                evidencia={"ES0902.Vu6": _r(registro=[_sup(escenarios=[_esc(evidencia=[texto])])],
                                            evidencia=[VIS, _obs(texto)])})["standards"]["ES0902"]
            ["rules"]["Vu6"],
            "seguridad": CHECK.para_seguridad(_r(registro=[_sup(escenarios=[
                _esc(evidencia=[texto])])], evidencia=[VIS, _obs(texto)]))[0],
        }
        for nombre, r in casos.items():
            t.no_contiene("E-55 `%s` en %s no sale" % (texto, nombre), "hunter2", _json(r))
        for nombre in ("un surfaceId", "un scenarioId", "un id de evidencia citado", "un errorType"):
            t.igual("E-55 con `%s` en %s ninguna clave nueva" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_claves)
        t.igual("E-55 con `%s` ninguna clave nueva en la senal" % texto, set(),
                set(_claves(casos["la senal"])) - base_senal)
        for nombre in ("rules.Vu6", "rules.Vu6 por la evidencia"):
            t.igual("E-55 con `%s` ninguna clave nueva en %s" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_unidad)
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu6_lib")
    t.igual("E-55 la regla de salida redacta las claves", {"[redactado]": 1},
            lib.depurar({"password=hunter2abc": 1}))
    t.verdadero("E-55 la regla de salida es la de la lib, no una copia",
                "SECRETOS" not in {n.id for n in ast.walk(_arbol()) if isinstance(n, ast.Name)}
                and CHECK._ev.__file__.endswith("evidencia.py"))
    for campo in ("password", "token", "stackTrace", "message", "realValue"):
        con = dict(OBS, **{campo: "abc"})
        t.igual("E-55 un item con `%s` no cuenta" % campo, SIN_CUST, _estado(evidencia=[VIS, con]))
        t.verdadero("E-55 el registro no acepta `%s`" % campo,
                    bool(CHECK.validar_schema({"version": "1.0", "surfaces": [
                        dict(_sup(), **{campo: "abc"})]})))


def test_e56_lo_ilegible_que_nombra_la_superficie_o_el_escenario(t):
    """E-56."""
    for nombre, eid in (("una lista", ["x"]), ("un dict", {"k": "v"})):
        crudo = dict(_obs("c", valor=CRUDO), evidenceId=eid)
        for forma, item in (("suelto", {"evidenceId": eid, "scenarios": ["inesperado"]}),
                            ("con forma de exposicion", crudo)):
            t.igual("E-56 un id que es %s (%s) impide el PASS sin romper" % (nombre, forma),
                    SIN_CUST, _sin_excepcion(lambda: _estado(evidencia=EVIDENCIA + [item])))
            t.igual("E-56 un id que es %s (%s) no deja apagar la senal" % (nombre, forma),
                    "UNRESOLVED", _sin_excepcion(lambda: CHECK.senal(_caso(
                        registro=[], evidencia=[_ausente(), dict(item, targets=["portal"])]))["value"]))
    mal = dict(_obs("mal", valor=CRUDO), outcome=["X"])
    t.igual("E-56 una mal formada no citada", SIN_CUST, _estado(evidencia=EVIDENCIA + [mal]))
    t.igual("E-56 una mal formada citada", SIN_CUST, _con_ademas(mal)["state"])
    t.igual("E-56 una que nombra solo la superficie", SIN_CUST,
            _estado(evidencia=EVIDENCIA + [{"evidenceId": "m", "targets": ["portal"], "extra": 1}]))
    rep = _obs("rep", valor=CRUDO)
    t.igual("E-56 una repetida no citada", SIN_CUST,
            _estado(evidencia=EVIDENCIA + [rep, copy.deepcopy(rep)]))
    t.igual("E-56 un id citado que no esta en el catalogo", SIN_CUST,
            _estado(registro=[_sup(escenarios=[_esc(evidencia=["obs", "fantasma"])])]))
    t.igual("E-56 una ilegible de otra superficie y otro escenario no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_obs("m", sup="otra", esc="otro"), outcome=1)]))
    for nombre, eid in (("vacio", ""), ("en blanco", "  ")):
        t.igual("E-56 un id %s no cuenta aunque se lo cite" % nombre, SIN_CUST,
                _estado(registro=[_sup(escenarios=[_esc(evidencia=[eid])])],
                        evidencia=[VIS, dict(OBS, evidenceId=eid)]))
    t.verdadero("E-56 ninguna es FAIL", _estado(evidencia=EVIDENCIA + [mal]) not in FALLAS)
    t.igual("E-56 y no tapa un FAIL", CRUDO,
            _con_ademas(_obs("crudo", valor=CRUDO), mal)["state"])


def test_e57_la_falla_establecida_gana_siempre(t):
    """E-57."""
    for valor in (POR_DEFECTO, CRUDO, INFRA):
        falla = _obs("falla", valor=valor, fuente="EXPOSED_OUTPUT_OBSERVATION")
        honesto = _r(registro=[_sup(escenarios=[_esc(resultado=valor, evidencia=["falla"])])],
                     evidencia=EVIDENCIA + [falla])
        negado = _r(registro=[_sup(escenarios=[_esc(evidencia=["falla"])])],
                    evidencia=EVIDENCIA + [falla])
        t.igual("E-57 %s con el registro honesto" % valor, valor, honesto["state"])
        t.igual("E-57 %s: el mismo FAIL con el registro en CUSTOMIZED_SAFE" % valor,
                (honesto["state"], _x(honesto)["state"]), (negado["state"], _x(negado)["state"]))
        t.igual("E-57 %s: y con la que dice customizado tambien citada" % valor, valor,
                _con_ademas(falla)["state"])
        t.igual("E-57 %s: en seguridad es FAIL" % valor, "NON_COMPLIANT",
                _vu6_en_seguridad(negado)["result"])
    t.igual("E-57 lo no citado que dice que falla nunca es FAIL", SIN_CUST,
            _r(evidencia=EVIDENCIA + [_obs("x", valor=CRUDO)])["state"])


def test_e58_un_solo_bloqueo(t):
    """E-58."""
    crudo = _prueba(CRUDO, environment="PRD", esc=None)
    no_aplica = _r(registro=[], evidencia=[_ausente(), crudo])
    t.igual("E-58 la senal sigue en FALSE", "FALSE", no_aplica["signalValue"])
    t.igual("E-58 una insegura que nombra la superficie impide el NOT_APPLICABLE", INSEGURA,
            no_aplica["state"])
    t.igual("E-58 y en seguridad tampoco vuelve a ser NOT_APPLICABLE", "UNRESOLVED",
            _vu6_en_seguridad(no_aplica)["result"])
    t.igual("E-58 e impide el PASS", INSEGURA, _estado(evidencia=EVIDENCIA + [crudo]))
    amable = _prueba(environment="PRD")
    t.igual("E-58 una citada que dice customizado impide el PASS", INSEGURA,
            _con_ademas(amable)["state"])
    t.igual("E-58 una no citada que dice customizado no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [amable]))
    t.igual("E-58 ni suelta sobre la superficie", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(environment="PRD", esc=None)]))
    t.igual("E-58 ni con el NOT_APPLICABLE", "NOT_APPLICABLE",
            _estado(registro=[], evidencia=[_ausente(), _prueba(environment="PRD", esc=None)]))
    t.igual("E-58 nunca tapa un FAIL", CRUDO,
            _con_ademas(_obs("crudo", valor=CRUDO), crudo)["state"])
    t.igual("E-58 una que nombra algo fuera del registro y del alcance no mueve nada",
            "NOT_APPLICABLE", _estado(registro=[], evidencia=[_ausente(), dict(crudo, targets=["otra"])]))
    t.igual("E-58 ni en un PASS", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(CRUDO, environment="PRD", sup=None,
                                                   esc="no-registrado", targets=["otra"])]))
    abierto = _r(registro=[_sup(escenarios=[_esc(evidencia=["obs", "qa"])])],
                 evidencia=EVIDENCIA + [_obs("x", valor=CRUDO), _prueba(environment="PRD")])
    t.igual("E-58 no reemplaza un sin resolver anterior", SIN_CUST, _x(abierto)["state"])
    t.contiene("E-58 y el bloqueo queda en states", INSEGURA, _x(abierto)["states"])
    sin_cob = _r([SUPERFICIE, BACKOFFICE], evidencia=EVIDENCIA + [crudo])
    t.igual("E-58 tampoco una cobertura sin resolver", SIN_COB, sin_cob["state"])
    t.contiene("E-58 con el bloqueo a la vista", INSEGURA, sin_cob["states"])
    sin_senal = _r(registro=[], evidencia=[crudo])
    t.igual("E-58 con la senal UNRESOLVED es APPLICABILITY_UNRESOLVED", "APPLICABILITY_UNRESOLVED",
            sin_senal["state"])
    t.contiene("E-58 y el bloqueo queda en states", INSEGURA, sin_senal["states"])
    t.igual("E-58 un solo paso de bloqueo en el modulo", 1,
            len([n for n in ast.walk(_arbol()) if isinstance(n, ast.FunctionDef)
                 and n.name == "_bloquear"]))
    t.igual("E-58 y lo llaman el escenario y el agregado", ["evaluar", "evaluar_escenario"],
            _llamadores("_bloquear"))


def test_e59_el_schema_cerrado(t):
    """E-59."""
    instalado = json.loads((REGLAS / "custom-error-message-evidence.json").read_text(encoding="utf-8"))
    t.igual("E-59 el registro se instala vacio", {"version": "1.0", "surfaces": []}, instalado)
    t.igual("E-59 y valida", [], CHECK.validar_schema(instalado))
    t.igual("E-59 la superficie base valida", [],
            CHECK.validar_schema({"version": "1.0", "surfaces": [_sup()]}))
    capas = {"la raiz": lambda d: d.update(extra=1),
             "una superficie": lambda d: d["surfaces"][0].update(extra=1),
             "un escenario": lambda d: d["surfaces"][0]["scenarios"][0].update(extra=1)}
    for nombre, cambiar in capas.items():
        doc = {"version": "1.0", "surfaces": [_sup()]}
        cambiar(doc)
        t.verdadero("E-59 una clave de mas en %s no valida" % nombre, bool(CHECK.validar_schema(doc)))
        r = CHECK.evaluar(dict(_caso(), surfaces=doc))
        t.verdadero("E-59 y el check no pasa con ese registro (%s)" % nombre, r["state"] != "PASS")
        t.contiene("E-59 y dice por que (%s)" % nombre, "no valida contra su schema",
                   " ".join(r["issues"]))
    esquema = json.loads((SCHEMAS / "custom-error-message-evidence.schema.json").read_text(
        encoding="utf-8"))

    def objetos(nodo):
        if isinstance(nodo, dict):
            if nodo.get("type") == "object":
                yield nodo
            for v in nodo.values():
                yield from objetos(v)
        elif isinstance(nodo, list):
            for v in nodo:
                yield from objetos(v)
    capas_del_schema = list(objetos(esquema))
    t.igual("E-59 tres capas de objeto", 3, len(capas_del_schema))
    t.verdadero("E-59 todas cerradas",
                all(c.get("additionalProperties") is False for c in capas_del_schema))


def test_e60_una_entrada_fuera_del_alcance(t):
    """E-60."""
    fuera, ev = _otra("externo", "OTHER")
    fuera = dict(fuera, evidence=["vis-externo"])
    r = _r(registro=[_sup(), fuera], evidencia=EVIDENCIA + ev[1:])
    t.igual("E-60 el caso sin la de afuera pasa", "PASS", _estado(evidencia=EVIDENCIA + ev[1:]))
    t.igual("E-60 una entrada fuera del alcance impide el PASS", SIN_COB, r["state"])
    t.igual("E-60 se evalua igual", "PASS", _s(r, "externo")["state"])
    t.igual("E-60 y dice que esta afuera", False, _s(r, "externo")["inScope"])
    t.igual("E-60 y se informa", ["externo"], r["coverage"]["surfacesOutsideScope"])
    t.verdadero("E-60 y nunca es FAIL", r["state"] not in FALLAS)
    t.igual("E-60 en seguridad no cumple", "UNRESOLVED", _vu6_en_seguridad(r)["result"])
    t.igual("E-60 tambien cuando es la unica", SIN_COB,
            _estado(inventario=[], registro=[fuera], evidencia=ev[1:]))
    roto, ev2 = _otra("externo", "OTHER", valor=CRUDO)
    roto = dict(roto, evidence=["vis-externo"])
    t.igual("E-60 fuera del alcance no tapa su propia falla", CRUDO,
            _estado(registro=[_sup(), roto], evidencia=EVIDENCIA + ev2[1:]))
