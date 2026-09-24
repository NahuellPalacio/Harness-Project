# ES0902 §6 Vu4: una sesion inactiva vence sola, aparte del token de OpenID.
#
# Escenarios E-01 a E-60 de docs/cambios/es0902-vu4-vencimiento-por-inactividad/spec.md. E-nn es
# el VU4-nn del pedido de instalacion; E-58 a E-60 los agrega la spec.
#
# 🔴 CASO es una superficie con una sesion ciudadana cumplida: vencimiento propio configurado,
# independiente del token, semantica de actividad con su politica citada y comportamiento
# evidenciado. Casi todo este archivo sale de romperla. E-19 la mira en PASS.
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
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "session-inactivity-timeout.py"
RUTA_C1 = CONTROLES / "checks" / "oidc-keycloak-integration.py"
RUTA_VU3 = CONTROLES / "checks" / "browser-close-session-termination.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu4_vencimiento")
C1 = _cargar(RUTA_C1, "vu4_c1")
VU3 = _cargar(RUTA_VU3, "vu4_vu3")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu4"}
LOS_12 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "SESSION_COVERAGE_UNRESOLVED", "SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED",
          "SESSION_ACTIVITY_SEMANTICS_UNRESOLVED", "SESSION_INACTIVITY_TIMEOUT_UNRESOLVED",
          "TOKEN_TIMEOUT_ONLY", "INACTIVE_SESSION_REMAINS_USABLE",
          "SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
FALLAS = ("FAIL", "TOKEN_TIMEOUT_ONLY", "INACTIVE_SESSION_REMAINS_USABLE")
SIN_VENC = "SESSION_INACTIVITY_TIMEOUT_UNRESOLVED"
SIN_SEM = "SESSION_ACTIVITY_SEMANTICS_UNRESOLVED"
SIN_COB = "SESSION_COVERAGE_UNRESOLVED"
SIN_ROLES = "SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED"
SOLO_TOKEN = "TOKEN_TIMEOUT_ONLY"
USABLE = "INACTIVE_SESSION_REMAINS_USABLE"
INSEGURA = "SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"
VIEJA = "OLD_INACTIVE_SESSION_STILL_USABLE"
INACT = "APPLICATION_INACTIVITY"

SUPERFICIE = {"surfaceId": "portal", "scope": "tramites", "audience": "INSTITUTIONAL",
              "environment": "QA", "currentProvider": "https://sso-qa.identidad.example/auth",
              "protocol": "OIDC", "flow": "FLUJO-A", "credentialEntryDelegated": True,
              "evidence": []}
BACKOFFICE = dict(SUPERFICIE, surfaceId="backoffice", scope="gestion",
                  credentialEntryDelegated=False)


def _e(eid, fuente, establece, valor=None, domain=INACT, sesiones=("ciudadana",), **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece], "domain": domain}
    if sesiones is not None:
        base["sessions"] = list(sesiones)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _comp(eid="comp", valor="SESSION_REJECTED", fuente="INTEGRATION_TEST", **extra):
    return _e(eid, fuente, "POST_TIMEOUT_BEHAVIOR", valor, **extra)


def _sesion(sid="ciudadana", surface="portal", roles=("CIUDADANO",), evidencia=("comp",),
            resultado="SESSION_REJECTED", modo="INTEGRATION_TEST", politica="politica",
            valor="cfg:timeout-app", estado="CONFIGURED", independiente="YES",
            semantica="DEFINED", modelo="SERVER_SIDE_SESSION", capa="backend", ambiente="QA",
            token=None):
    return {"sessionId": sid, "surfaceRef": surface, "roles": list(roles), "environment": ambiente,
            "sessionModel": modelo,
            "inactivityTimeout": {"status": estado, "valueRef": valor,
                                  "independentFromOidcTokenTimeout": independiente,
                                  "enforcementLayer": capa},
            "oidcTimeouts": dict(token if token is not None else {
                "accessTokenTimeoutRef": "kc:access-lifespan",
                "refreshTokenTimeoutRef": "kc:refresh-lifespan",
                "idpSessionTimeoutRef": "kc:sso-idle"}),
            "activitySemantics": {"status": semantica, "sourceRef": politica},
            "verification": {"result": resultado, "evidenceMode": modo},
            "evidence": list(evidencia)}


POLITICA = _e("politica", "PROJECT_SESSION_POLICY", "ACTIVITY_SEMANTICS", "DEFINED",
              sesiones=None, values=["USER_REQUEST"])
ENTRADA = _sesion()
EVIDENCIA = [POLITICA, _comp()]


def _caso(superficies=None, entradas=None, evidencia=None, detectadas=None, vu3=None):
    caso = {"inventory": {"version": "1.0", "surfaces": copy.deepcopy(
                [SUPERFICIE] if superficies is None else superficies)},
            "sessions": {"version": "1.0", "sessions": copy.deepcopy(
                [ENTRADA] if entradas is None else entradas)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if detectadas is not None:
        caso["detectedSurfaces"] = detectadas
    if vu3 is not None:
        caso["browserSessions"] = copy.deepcopy(vu3)
    return caso


def _r(*a, senal=None, autenticacion=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal, autenticacion)


def _estado(*a, **k):
    return _r(*a, **k)["state"]


def _ses(r, sid="ciudadana"):
    return [s for s in r["sessions"] if s["sessionId"] == sid][0]


def _sin(eid, *mas):
    return [x for x in EVIDENCIA if x["evidenceId"] != eid] + list(mas)


def _solo_con(*evidencia, **cambios):
    """La sesion base sostenida solo por `evidencia` en lugar de `comp`."""
    ids = [x["evidenceId"] for x in evidencia]
    return _r(entradas=[_sesion(evidencia=ids, **cambios)], evidencia=_sin("comp", *evidencia))


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


def _sin_excepcion(f):
    try:
        return f()
    except Exception as e:                              # noqa: BLE001 - el test nombra la excepcion
        return "EXCEPCION %s: %s" % (type(e).__name__, e)


PRUEBA = dict(environment="QA", authorized=True, testIdentityRef="qa-user-7", outcome="CONFIRMED")


def _prueba(valor="SESSION_REJECTED", eid="rt", **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _comp(eid, valor, "AUTHORIZED_RUNTIME_TEST", **datos)


def _vu4_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu4", ev, sen, MATRIZ)


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (VU4-01)."""
    t.igual("E-01 la fila", "ES0902.Vu4", seguridad.regla("Vu4", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu4", CHECK.CLAVE)
    for nombre, r in (("pasa", _r()), ("sin senal", CHECK.evaluar({})),
                      ("falla", _r(entradas=[_sesion(valor="kc:access-lifespan")]))):
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu4", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu4", _vu4_en_seguridad(r)["ruleKey"])


def test_e02_los_ids(t):
    """E-02 (VU4-02)."""
    vu4 = seguridad.regla("Vu4", MATRIZ)
    t.igual("E-02 la senal", ["sessionPresent"], vu4["applicability"]["signals"])
    # La matriz declara dos agentes primarios; `dev-security` es el dueno normativo y va primero.
    t.igual("E-02 los agentes", ["dev-security", "dev-backend"], vu4["primaryAgents"])
    t.igual("E-02 la policy", ["session-inactivity-timeout-required"], vu4["policies"])
    t.igual("E-02 el check", ["session-inactivity-timeout"], vu4["checks"])
    t.igual("E-02 el modulo", ("sessionPresent", "session-inactivity-timeout",
                               "session-inactivity-timeout-required"),
            (CHECK.SENAL, CHECK.CONTROL, CHECK.POLICY))
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("session-inactivity-timeout-required", "POLICY",
             "controles/policies/session-inactivity-timeout-required.md"),
            ("session-inactivity-timeout", "CHECK",
             "controles/checks/session-inactivity-timeout.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    for md in ("es0902-vu4-governance.md", "es0902-vu4-session-present-signal.md",
               "es0902-vu4-session-inactivity-timeout-check.md"):
        t.verdadero("E-02 %s instalado" % md, (REGLAS / md).is_file())


def test_e03_nada_nuevo(t):
    """E-03 (VU4-03)."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 10, len(registro["agents"]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 cero reviews", [], seguridad.regla("Vu4", MATRIZ)["reviews"])
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-03 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-03 y Vu4 sigue siendo `_vu4`", seguridad.ALGORITMOS["Vu4"] is seguridad._vu4)


# -- La senal -------------------------------------------------------------------

def test_e04_una_sesion_autenticada_enciende(t):
    """E-04 (VU4-04)."""
    doc = CHECK.senal(_caso())
    t.igual("E-04 TRUE", "TRUE", doc["value"])
    t.igual("E-04 la cita", ["authentication-surfaces.json#portal",
                             "session-inactivity-timeout.json#ciudadana"],
            sorted(e["reference"] for e in doc["evidence"]))
    booleanos = senales.booleanos({"sessionPresent": doc})
    t.igual("E-04 enciende la fila", "APPLICABLE",
            seguridad.resolver_regla(seguridad.regla("Vu4", MATRIZ), booleanos)[0])
    t.igual("E-04 una sesion fuera del inventario tambien", "TRUE",
            CHECK.senal(_caso([], [_sesion(surface="otra")]))["value"])


def test_e05_una_sesion_por_tokens_en_el_browser(t):
    """E-05 (VU4-05)."""
    entrada = _sesion(modelo="TOKEN_BASED_APPLICATION_SESSION")
    t.igual("E-05 TRUE", "TRUE", CHECK.senal(_caso(entradas=[entrada]))["value"])
    t.igual("E-05 y se evalua como cualquiera", "PASS", _estado(entradas=[entrada]))


def test_e06_una_app_movil(t):
    """E-06 (VU4-06)."""
    movil = dict(SUPERFICIE, surfaceId="app-movil", scope="movil")
    entrada = _sesion(sid="movil", surface="app-movil", modelo="TOKEN_BASED_APPLICATION_SESSION")
    t.igual("E-06 TRUE por el registro", "TRUE", CHECK.senal(_caso([movil], [entrada]))["value"])
    presente = _e("pres", "CONFIGURATION", "APPLICATION_SESSION", "PRESENT",
                  domain="APPLICATION_SESSION", sesiones=None, targets=["app-movil"])
    t.igual("E-06 TRUE por evidencia, sin entrada", "TRUE",
            CHECK.senal(_caso([movil], [], [presente]))["value"])


def test_e07_sin_estado_u_oidc_no_apaga(t):
    """E-07 (VU4-07)."""
    for delegada in (True, False, None):
        sup = dict(SUPERFICIE, credentialEntryDelegated=delegada)
        t.igual("E-07 con credentialEntryDelegated %r sigue TRUE" % delegada, "TRUE",
                CHECK.senal(_caso([sup]))["value"])
    for establece in ("STATELESS_BACKEND", "OIDC_DELEGATED_LOGIN", "CLIENT_STORED_TOKENS",
                      "NO_SERVER_SESSION_COOKIE"):
        doc = _e("arq", "ARCHITECTURE_DOCUMENTATION", establece, "TRUE",
                 domain="APPLICATION_SESSION", sesiones=None, targets=["portal"])
        t.igual("E-07 `%s` no apaga" % establece, "UNRESOLVED",
                CHECK.senal(_caso(entradas=[], evidencia=[doc]))["value"])
    oidc = _e("oidc", "ARCHITECTURE_DOCUMENTATION", "APPLICATION_SESSION", "ABSENT",
              domain="OIDC_ACCESS_TOKEN", sesiones=None, targets=["portal"])
    t.igual("E-07 un ABSENT del dominio del token no apaga", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[oidc]))["value"])


def _ausente(fuente="ARCHITECTURE_DOCUMENTATION", sup="portal"):
    return _e("aus", fuente, "APPLICATION_SESSION", "ABSENT", domain="APPLICATION_SESSION",
              sesiones=None, targets=[sup])


def test_e08_sin_sesion_con_autoridad_apaga(t):
    """E-08 (VU4-08)."""
    caso = _caso(entradas=[], evidencia=[_ausente()])
    t.igual("E-08 FALSE", "FALSE", CHECK.senal(caso)["value"])
    t.igual("E-08 NOT_APPLICABLE", "NOT_APPLICABLE", CHECK.evaluar(caso)["state"])
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT", "CONFIGURATION", "SOURCE_CODE"):
        t.igual("E-08 %s no apaga" % fuente, "UNRESOLVED",
                CHECK.senal(_caso(entradas=[], evidencia=[_ausente(fuente)]))["value"])
    t.igual("E-08 con una entrada del registro no apaga", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[_sesion(modelo="UNRESOLVED")],
                              evidencia=[_ausente()]))["value"])
    vu3 = {"version": "1.0", "surfaces": [{"surfaceId": "portal", "sessionModel": "UNRESOLVED",
                                           "clients": [], "evidence": []}]}
    t.igual("E-08 con una entrada del registro de Vu3 no apaga", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[_ausente()], vu3=vu3))["value"])
    t.igual("E-08 con la cobertura incompleta no apaga", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[_ausente()],
                              detectadas=["portal", "otra"]))["value"])
    t.igual("E-08 con una superficie sin la evidencia no apaga", "UNRESOLVED",
            CHECK.senal(_caso([SUPERFICIE, BACKOFFICE], [], [_ausente()]))["value"])
    presente = _e("pres-rt", "AUTHORIZED_RUNTIME_TEST", "APPLICATION_SESSION", "PRESENT",
                  domain="APPLICATION_SESSION", sesiones=None, targets=["portal"],
                  environment="PRD", authorized=True, testIdentityRef="qa-user-7",
                  outcome="CONFIRMED")
    t.igual("E-08 una prueba insegura que dice PRESENT no deja apagar", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[_ausente(), presente]))["value"])
    t.igual("E-08 sin autenticacion y sin nada, FALSE", "FALSE",
            CHECK.senal(_caso([], [], []), autenticacion=False)["value"])
    t.igual("E-08 sin autenticacion y con una sesion, no", "TRUE",
            CHECK.senal(_caso([], [_sesion(surface="otra")], []), autenticacion=False)["value"])


def test_e09_con_autenticacion_y_sin_semantica(t):
    """E-09 (VU4-09)."""
    t.igual("E-09 UNRESOLVED", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[]))["value"])
    t.igual("E-09 y el check", "APPLICABILITY_UNRESOLVED", _estado(entradas=[], evidencia=[]))
    t.igual("E-09 con authenticationPresent TRUE y nada mas, UNRESOLVED", "UNRESOLVED",
            CHECK.senal(_caso([], [], []), autenticacion=True)["value"])
    t.igual("E-09 una entrada sin modelo tampoco la resuelve", "APPLICABILITY_UNRESOLVED",
            _estado(entradas=[_sesion(modelo="UNRESOLVED")], evidencia=[]))


# -- La cobertura -----------------------------------------------------------------

def test_e10_las_superficies_son_las_de_c1(t):
    """E-10 (VU4-10)."""
    t.verdadero("E-10 el cargador es el de C1",
                Path(CHECK._SUPERFICIES.__file__).name == "oidc-keycloak-integration.py")
    t.verdadero("E-10 la senal de Vu3 es la de Vu3",
                Path(CHECK._CIERRE.__file__).name == "browser-close-session-termination.py")
    t.verdadero("E-10 el modulo no lee un inventario propio",
                not ({"authentication-surfaces.json", "authentication-surface.schema.json"}
                     & _literales()))
    r = CHECK.evaluar({"inventory": {"surfaces": 1}, "sessions": {"version": "1.0",
                                                                  "sessions": [ENTRADA]},
                       "evidence": EVIDENCIA}, True)
    t.igual("E-10 un inventario roto no lo arregla el modulo", SIN_COB, r["state"])
    t.contiene("E-10 y lo dice", "el inventario de superficies no valida", " ".join(r["issues"]))
    vu3 = {"version": "1.0", "surfaces": [{"surfaceId": "portal", "sessionModel": "HYBRID",
                                           "clients": [], "evidence": []}]}
    caso = _caso(entradas=[], evidencia=[], vu3=vu3)
    t.igual("E-10 una superficie con senal de Vu3 enciende Vu4", "TRUE", CHECK.senal(caso)["value"])
    r = CHECK.evaluar(caso)
    t.igual("E-10 y cuenta como superficie con sesion", SIN_COB, r["state"])
    t.igual("E-10 que nadie registro", ["portal"], r["coverage"]["surfacesWithoutSession"])


def test_e11_el_backoffice_se_evalua(t):
    """E-11 (VU4-11)."""
    admin = _sesion(sid="admin", surface="backoffice", roles=["ADMIN"], resultado="NOT_TESTED",
                    evidencia=[])
    r = _r([SUPERFICIE, BACKOFFICE], [ENTRADA, admin])
    t.igual("E-11 las dos en sessions", ["admin", "ciudadana"],
            sorted(s["sessionId"] for s in r["sessions"]))
    t.igual("E-11 la ciudadana cumple", "PASS", _ses(r)["state"])
    t.igual("E-11 la de backoffice no", SIN_VENC, _ses(r, "admin")["state"])
    t.igual("E-11 y el agregado no pasa", SIN_VENC, r["state"])


def test_e12_una_superficie_sin_entrada(t):
    """E-12 (VU4-12)."""
    presente = _e("pres", "ARCHITECTURE_DOCUMENTATION", "APPLICATION_SESSION", "PRESENT",
                  domain="APPLICATION_SESSION", sesiones=None, targets=["backoffice"])
    r = _r([SUPERFICIE, BACKOFFICE], evidencia=EVIDENCIA + [presente])
    t.igual("E-12 SESSION_COVERAGE_UNRESOLVED", SIN_COB, r["state"])
    t.igual("E-12 y dice cual", ["backoffice"], r["coverage"]["surfacesWithoutSession"])
    t.igual("E-12 la que tiene entrada sigue cumpliendo", "PASS", _ses(r)["state"])
    fuera = _r(entradas=[_sesion(surface="otra")])
    t.igual("E-12 una entrada fuera del inventario tambien se evalua", ("PASS", False),
            (_ses(fuera)["state"], _ses(fuera)["inInventory"]))
    t.igual("E-12 y su ausencia en C1 se informa", ["ciudadana"],
            fuera["coverage"]["sessionsOutsideInventory"])


# -- El token no es la sesion -----------------------------------------------------

def _de_otro_dominio(dominio, eid):
    return _comp(eid, domain=dominio, fuente="AUTHORIZED_RUNTIME_TEST", **PRUEBA)


def _token_solo(t, escenario, dominio, campo):
    otro = _de_otro_dominio(dominio, "tok")
    r = _solo_con(otro)
    s = _ses(r)
    t.igual("%s sola no sostiene el vencimiento" % escenario, SIN_VENC, s["state"])
    t.igual("%s y no pasa" % escenario, SIN_VENC, r["state"])
    t.igual("%s se informa en su dominio" % escenario, ["tok"], s["supportingContext"][dominio])
    t.igual("%s el vencimiento de la aplicacion va aparte" % escenario, "cfg:timeout-app",
            s["applicationInactivityTimeout"]["valueRef"])
    t.igual("%s y el del token tambien" % escenario, ENTRADA["oidcTimeouts"][campo],
            s["oidcTimeouts"][campo])
    config = _e("cfg", "CONFIGURATION", "INACTIVITY_TIMEOUT", "NOT_CONFIGURED", domain=dominio)
    t.igual("%s un NOT_CONFIGURED de ese dominio no es el de la aplicacion" % escenario, SIN_VENC,
            _ses(_solo_con(config, estado="NOT_CONFIGURED"))["state"])


def test_e13_el_access_token(t):
    """E-13 (VU4-13)."""
    _token_solo(t, "E-13 el access token", "OIDC_ACCESS_TOKEN", "accessTokenTimeoutRef")


def test_e14_el_refresh_token(t):
    """E-14 (VU4-14)."""
    _token_solo(t, "E-14 el refresh token", "OIDC_REFRESH_TOKEN", "refreshTokenTimeoutRef")


def test_e15_el_sso_del_proveedor(t):
    """E-15 (VU4-15)."""
    _token_solo(t, "E-15 el SSO del proveedor", "IDP_SSO_SESSION", "idpSessionTimeoutRef")


def _no_configurado(eid="nocfg", fuente="CONFIGURATION"):
    return _e(eid, fuente, "INACTIVITY_TIMEOUT", "NOT_CONFIGURED")


def test_e16_solo_el_token_es_fail(t):
    """E-16 (VU4-16)."""
    r = _r(entradas=[_sesion(estado="NOT_CONFIGURED", valor=None,
                             evidencia=["comp", "nocfg"])],
           evidencia=EVIDENCIA + [_no_configurado()])
    t.igual("E-16 NOT_CONFIGURED con el token, citado", SOLO_TOKEN, r["state"])
    t.igual("E-16 y la sesion", SOLO_TOKEN, _ses(r)["state"])
    t.igual("E-16 con su evidencia", ["nocfg"], _ses(r)["evidenceUsed"]["inactivityTimeout"])
    t.igual("E-16 sin citarla no es FAIL", SIN_VENC,
            _estado(entradas=[_sesion(estado="NOT_CONFIGURED", valor=None)],
                    evidencia=EVIDENCIA + [_no_configurado()]))
    t.igual("E-16 sin ninguna evidencia no es FAIL", SIN_VENC,
            _estado(entradas=[_sesion(estado="NOT_CONFIGURED", valor=None)]))
    sin_token = _sesion(estado="NOT_CONFIGURED", valor=None, evidencia=["comp", "nocfg"],
                        token={})
    t.igual("E-16 NOT_CONFIGURED sin token, citado, es FAIL", "FAIL",
            _estado(entradas=[sin_token], evidencia=EVIDENCIA + [_no_configurado()]))
    dep = _e("dep", "ARCHITECTURE_DOCUMENTATION", "TIMEOUT_INDEPENDENCE", "NO")
    t.igual("E-16 independencia NO, citada", SOLO_TOKEN,
            _estado(entradas=[_sesion(independiente="NO", evidencia=["comp", "dep"])],
                    evidencia=EVIDENCIA + [dep]))
    t.igual("E-16 independencia NO sin evidencia no es FAIL", SIN_VENC,
            _estado(entradas=[_sesion(independiente="NO")]))
    t.igual("E-16 el registro dice YES y una evidencia citada dice NO", SOLO_TOKEN,
            _estado(entradas=[_sesion(evidencia=["comp", "dep"])], evidencia=EVIDENCIA + [dep]))
    t.igual("E-16 el registro dice YES y una no citada dice NO: no se elige", SIN_VENC,
            _estado(evidencia=EVIDENCIA + [dep]))
    t.igual("E-16 CONFIGURED con una citada que dice NOT_CONFIGURED", SOLO_TOKEN,
            _estado(entradas=[_sesion(evidencia=["comp", "nocfg"])],
                    evidencia=EVIDENCIA + [_no_configurado()]))


def test_e17_el_valor_del_access_token(t):
    """E-17 (VU4-17)."""
    r = _r(entradas=[_sesion(valor="kc:access-lifespan")])
    t.igual("E-17 TOKEN_TIMEOUT_ONLY", SOLO_TOKEN, r["state"])
    t.verdadero("E-17 y no aprueba", not CHECK.aprueba(r))
    nfc, nfd = (unicodedata.normalize(f, "kc:accesó") for f in ("NFC", "NFD"))
    token = dict(ENTRADA["oidcTimeouts"], accessTokenTimeoutRef=nfd)
    t.igual("E-17 igual en NFC es igual", SOLO_TOKEN,
            _estado(entradas=[_sesion(valor=nfc, token=token)]))
    for campo in ("refreshTokenTimeoutRef", "idpSessionTimeoutRef"):
        t.igual("E-17 lo mismo con `%s`" % campo, SOLO_TOKEN,
                _estado(entradas=[_sesion(valor=ENTRADA["oidcTimeouts"][campo])]))


def test_e18_el_vencimiento_de_keycloak(t):
    """E-18 (VU4-18)."""
    kc = _de_otro_dominio("IDP_SSO_SESSION", "kc-vencio")
    r = _solo_con(kc)
    t.igual("E-18 no aprueba", SIN_VENC, r["state"])
    t.igual("E-18 y se informa", ["kc-vencio"], _ses(r)["supportingContext"]["IDP_SSO_SESSION"])


def test_e19_un_vencimiento_independiente_cumple(t):
    """E-19 (VU4-19)."""
    r = _r()
    t.igual("E-19 PASS", "PASS", r["state"])
    t.igual("E-19 la sesion cumple", "PASS", _ses(r)["state"])
    t.igual("E-19 con su comportamiento", ["comp"], _ses(r)["evidenceUsed"]["behavior"])
    t.igual("E-19 y su semantica", ["politica"], _ses(r)["evidenceUsed"]["activitySemantics"])
    t.verdadero("E-19 aprueba", CHECK.aprueba(r))


# -- La duracion -----------------------------------------------------------------------

def test_e20_ninguna_duracion(t):
    """E-20 (VU4-20)."""
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.verdadero("E-20 sin numeros salvo 0 o 1: %s" % numeros, set(numeros) <= {0, 1})
    texto = " ".join(_literales()).lower()
    for palabra in ("minut", "second", "segund", "hour", "hora"):
        t.no_contiene("E-20 ningun literal nombra `%s`" % palabra, palabra, texto)
    corta = _r(entradas=[_sesion(valor="cfg:timeout-3m")])
    larga = _r(entradas=[_sesion(valor="cfg:timeout-8h")])
    t.igual("E-20 3m y 8h dan el mismo estado", corta["state"], larga["state"])
    sin_valor = json.dumps(corta, sort_keys=True).replace("cfg:timeout-3m", "X")
    t.igual("E-20 y el mismo resultado entero", sin_valor,
            json.dumps(larga, sort_keys=True).replace("cfg:timeout-8h", "X"))


def test_e21_sin_valor_o_sin_estado(t):
    """E-21 (VU4-21)."""
    t.igual("E-21 CONFIGURED con valueRef nulo", SIN_VENC, _estado(entradas=[_sesion(valor=None)]))
    t.igual("E-21 CONFIGURED con valueRef vacio", SIN_VENC, _estado(entradas=[_sesion(valor=" ")]))
    t.igual("E-21 status UNRESOLVED", SIN_VENC, _estado(entradas=[_sesion(estado="UNRESOLVED")]))
    t.igual("E-21 independencia UNRESOLVED", SIN_VENC,
            _estado(entradas=[_sesion(independiente="UNRESOLVED")]))


def test_e22_el_valor_sale_tal_cual(t):
    """E-22 (VU4-22)."""
    for valor in ("cfg:timeout-app", "application.yml#server.servlet.session.timeout"):
        r = _r(entradas=[_sesion(valor=valor)])
        t.igual("E-22 `%s` sale en la sesion" % valor, valor,
                _ses(r)["applicationInactivityTimeout"]["valueRef"])


def test_e23_ninguna_duracion_hace_fail(t):
    """E-23 (VU4-23)."""
    for valor in ("cfg:timeout-1s", "cfg:timeout-1m", "cfg:timeout-24h", "cfg:timeout-365d"):
        t.igual("E-23 `%s` pasa" % valor, "PASS", _estado(entradas=[_sesion(valor=valor)]))


# -- La actividad -------------------------------------------------------------------------

def _observacion(escenario, t, evento, fuente):
    obs = _e("obs", fuente, "ACTIVITY_RESET_OBSERVATION", "OBSERVED", values=[evento])
    r = _r(entradas=[_sesion(politica="obs", evidencia=["comp", "obs"])],
           evidencia=_sin("politica", obs))
    t.igual("%s como fuente de la semantica no la define" % escenario, SIN_SEM, r["state"])
    t.igual("%s y se informa" % escenario, ["obs"],
            _ses(r)["supportingContext"]["activityObservations"])
    dice = _e("obs-def", fuente, "ACTIVITY_SEMANTICS", "DEFINED", values=[evento])
    t.igual("%s aunque diga DEFINED" % escenario, SIN_SEM,
            _estado(entradas=[_sesion(politica="obs-def")], evidencia=_sin("politica", dice)))
    t.igual("%s sin politica, la semantica no se inventa" % escenario, SIN_SEM,
            _estado(entradas=[_sesion(politica=None, semantica="UNRESOLVED",
                                      evidencia=["comp", "obs"])],
                    evidencia=_sin("politica", obs)))


def test_e24_el_mouse(t):
    """E-24 (VU4-24)."""
    _observacion("E-24 el mouse", t, "MOUSE_MOVEMENT", "UI_OBSERVATION")


def test_e25_el_scroll(t):
    """E-25 (VU4-25)."""
    _observacion("E-25 el scroll", t, "SCROLL", "UI_OBSERVATION")


def test_e26_el_polling(t):
    """E-26 (VU4-26)."""
    _observacion("E-26 el polling", t, "BACKGROUND_POLLING", "SOURCE_CODE")


def test_e27_el_refresh_del_token(t):
    """E-27 (VU4-27)."""
    _observacion("E-27 el refresh del token", t, "TOKEN_REFRESH", "OIDC_TOKEN_CONFIGURATION")


def test_e28_el_heartbeat(t):
    """E-28 (VU4-28)."""
    _observacion("E-28 el heartbeat", t, "HEARTBEAT", "CLIENT_TIMER")


def test_e29_una_politica_citada_resuelve(t):
    """E-29 (VU4-29)."""
    pol = dict(POLITICA, values=["USER_REQUEST", "TOKEN_REFRESH"])
    r = _r(evidencia=_sin("politica", pol))
    t.igual("E-29 con el refresh adentro, pasa", "PASS", r["state"])
    t.igual("E-29 y dice que cuenta", ["TOKEN_REFRESH", "USER_REQUEST"],
            _ses(r)["activitySemantics"]["events"])
    no_req = dict(POLITICA, value="NOT_REQUIRED")
    t.igual("E-29 NOT_REQUIRED con su politica tambien", "PASS",
            _estado(entradas=[_sesion(semantica="NOT_REQUIRED")],
                    evidencia=_sin("politica", no_req)))
    otra = dict(POLITICA, sessions=["otra-sesion"])
    t.igual("E-29 una politica de otra sesion no", SIN_SEM, _estado(evidencia=_sin("politica", otra)))


def test_e30_sin_semantica(t):
    """E-30 (VU4-30)."""
    t.igual("E-30 UNRESOLVED", SIN_SEM, _estado(entradas=[_sesion(semantica="UNRESOLVED")]))
    t.igual("E-30 DEFINED sin sourceRef", SIN_SEM, _estado(entradas=[_sesion(politica=None)]))
    t.igual("E-30 DEFINED con un sourceRef que no existe", SIN_SEM,
            _estado(entradas=[_sesion(politica="no-existe")]))
    debil = dict(POLITICA, sourceType="README_STATEMENT")
    t.igual("E-30 DEFINED con una fuente debil", SIN_SEM, _estado(evidencia=_sin("politica", debil)))
    sin_confirmar = dict(POLITICA, outcome="REFUTED")
    t.igual("E-30 DEFINED con una politica sin confirmar", SIN_SEM,
            _estado(evidencia=_sin("politica", sin_confirmar)))
    t.igual("E-30 NOT_REQUIRED con una politica que dice DEFINED", SIN_SEM,
            _estado(entradas=[_sesion(semantica="NOT_REQUIRED")]))


# -- El comportamiento despues del vencimiento --------------------------------------------

def test_e31_la_configuracion_sola(t):
    """E-31 (VU4-31)."""
    cfg = _comp("cfg", fuente="CONFIGURATION")
    r = _solo_con(cfg, modo="CONFIGURATION")
    t.igual("E-31 no cumple", SIN_VENC, r["state"])
    t.igual("E-31 y se informa como insuficiente", ["cfg"],
            _ses(r)["supportingContext"]["insufficient"])
    vence = _e("vence", "CONFIGURATION", "INACTIVITY_TIMEOUT", "CONFIGURED")
    t.igual("E-31 ni con el vencimiento configurado y citado", SIN_VENC,
            _solo_con(cfg, vence, modo="CONFIGURATION")["state"])


def _cumple_con(t, escenario, valor):
    r = _solo_con(_comp("b", valor=valor), resultado=valor)
    t.igual("%s cumple" % escenario, "PASS", r["state"])
    t.igual("%s con su evidencia" % escenario, ["b"], _ses(r)["evidenceUsed"]["behavior"])
    otro = "SESSION_REJECTED" if valor != "SESSION_REJECTED" else "NEW_SESSION_REQUIRED"
    t.igual("%s con otro valor en la evidencia, no" % escenario, SIN_VENC,
            _solo_con(_comp("b", valor=otro), resultado=valor)["state"])
    t.igual("%s sin citarla, no" % escenario, SIN_VENC,
            _r(entradas=[_sesion(evidencia=[], resultado=valor)],
               evidencia=_sin("comp", _comp("b", valor=valor)))["state"])
    t.igual("%s de otra sesion, no" % escenario, SIN_VENC,
            _solo_con(_comp("b", valor=valor, sesiones=["otra"]), resultado=valor)["state"])


def test_e32_session_rejected(t):
    """E-32 (VU4-32)."""
    _cumple_con(t, "E-32 SESSION_REJECTED", "SESSION_REJECTED")


def test_e33_reauthentication_required(t):
    """E-33 (VU4-33)."""
    _cumple_con(t, "E-33 REAUTHENTICATION_REQUIRED", "REAUTHENTICATION_REQUIRED")


def test_e34_new_session_required(t):
    """E-34 (VU4-34)."""
    _cumple_con(t, "E-34 NEW_SESSION_REQUIRED", "NEW_SESSION_REQUIRED")


def test_e35_la_sesion_vieja_sigue_sirviendo(t):
    """E-35 (VU4-35)."""
    vieja = _comp("vieja", valor=VIEJA, fuente="PROTECTED_ENDPOINT_CHECK")
    r = _solo_con(vieja, resultado=VIEJA)
    t.igual("E-35 INACTIVE_SESSION_REMAINS_USABLE", USABLE, r["state"])
    t.igual("E-35 y la sesion", USABLE, _ses(r)["state"])
    t.verdadero("E-35 es una falla", r["state"] in CHECK.FALLAS)
    t.igual("E-35 y en seguridad es NON_COMPLIANT", "NON_COMPLIANT", _vu4_en_seguridad(r)["result"])
    # Lo que dice que no pasa por la misma compuerta que lo que dice que si: el registro solo no
    # hace FAIL.
    t.igual("E-35 el registro solo, sin evidencia citada, no es FAIL", SIN_VENC,
            _estado(entradas=[_sesion(resultado=VIEJA, evidencia=[])], evidencia=[POLITICA]))


def test_e36_la_pantalla_no_tapa_al_recurso(t):
    """E-36 (VU4-36)."""
    ui = _comp("ui", valor="REAUTHENTICATION_REQUIRED", fuente="UI_OBSERVATION")
    api = _comp("api", valor=VIEJA, fuente="PROTECTED_ENDPOINT_CHECK")
    r = _solo_con(ui, api, resultado="REAUTHENTICATION_REQUIRED")
    t.igual("E-36 INACTIVE_SESSION_REMAINS_USABLE", USABLE, r["state"])
    no_citada = _r(entradas=[_sesion(evidencia=["ui", "b"], resultado="REAUTHENTICATION_REQUIRED")],
                   evidencia=_sin("comp", ui, api, _comp("b", valor="REAUTHENTICATION_REQUIRED")))
    t.igual("E-36 no citada, la deja sin resolver", SIN_VENC, no_citada["state"])
    t.igual("E-36 y dice quien la contradice", ["api"], _ses(no_citada)["contradictedBy"])
    contra = _r(entradas=[_sesion(resultado=VIEJA)])
    t.igual("E-36 y en la otra direccion: el registro dice que sirve y la evidencia que no",
            (SIN_VENC, ["comp"]), (contra["state"], _ses(contra)["contradictedBy"]))
    t.igual("E-36 la pantalla sola no aprueba", SIN_VENC,
            _solo_con(ui, resultado="REAUTHENTICATION_REQUIRED")["state"])


def test_e37_el_reloj_del_cliente(t):
    """E-37 (VU4-37)."""
    reloj = _comp("reloj", valor="REAUTHENTICATION_REQUIRED", fuente="CLIENT_TIMER")
    t.igual("E-37 un CLIENT_TIMER no aprueba", SIN_VENC,
            _solo_con(reloj, resultado="REAUTHENTICATION_REQUIRED")["state"])
    t.igual("E-37 con enforcementLayer frontend tampoco", SIN_VENC,
            _solo_con(reloj, resultado="REAUTHENTICATION_REQUIRED", capa="frontend")["state"])
    t.igual("E-37 frontend con el recurso evidenciado, si", "PASS",
            _estado(entradas=[_sesion(capa="frontend")]))


# -- Los roles ------------------------------------------------------------------------------

AGENTE = _sesion(sid="portal-agente", roles=["AGENTE"], valor="cfg:timeout-agente",
                 evidencia=["comp-agente"])
COMP_AGENTE = _comp("comp-agente", sesiones=["portal-agente"])


def test_e38_dos_roles_dos_entradas(t):
    """E-38 (VU4-38)."""
    r = _r(entradas=[ENTRADA, AGENTE], evidencia=EVIDENCIA + [COMP_AGENTE])
    t.igual("E-38 pasan las dos", "PASS", r["state"])
    t.igual("E-38 salen las dos", ["ciudadana", "portal-agente"],
            sorted(s["sessionId"] for s in r["sessions"]))
    t.igual("E-38 cada una con su politica", ("cfg:timeout-app", "cfg:timeout-agente"),
            (_ses(r)["applicationInactivityTimeout"]["valueRef"],
             _ses(r, "portal-agente")["applicationInactivityTimeout"]["valueRef"]))
    r = _r(entradas=[ENTRADA, dict(AGENTE, evidence=["comp"])], evidencia=EVIDENCIA + [COMP_AGENTE])
    t.igual("E-38 y cada una con su evidencia: la de la ciudadana no sostiene la del agente",
            ("PASS", SIN_VENC), (_ses(r)["state"], _ses(r, "portal-agente")["state"]))
    agente_token = _sesion(sid="portal-agente", roles=["AGENTE"], valor="kc:access-lifespan",
                           evidencia=["comp-agente"])
    r = _r(entradas=[ENTRADA, agente_token], evidencia=EVIDENCIA + [COMP_AGENTE])
    t.igual("E-38 y con su propia politica: una falla, la otra no",
            ("PASS", SOLO_TOKEN, SOLO_TOKEN),
            (_ses(r)["state"], _ses(r, "portal-agente")["state"], r["state"]))


def test_e39_la_ciudadana_no_tapa_a_la_de_administracion(t):
    """E-39 (VU4-39)."""
    admin = _sesion(sid="admin", surface="backoffice", roles=["ADMIN"], estado="NOT_CONFIGURED",
                    valor=None, token={}, evidencia=["nocfg-admin"])
    r = _r([SUPERFICIE, BACKOFFICE], [ENTRADA, admin],
           EVIDENCIA + [_e("nocfg-admin", "CONFIGURATION", "INACTIVITY_TIMEOUT", "NOT_CONFIGURED",
                           sesiones=["admin"])])
    t.igual("E-39 FAIL", "FAIL", r["state"])
    t.igual("E-39 la ciudadana cumple", "PASS", _ses(r)["state"])
    t.igual("E-39 la de administracion falla", "FAIL", _ses(r, "admin")["state"])


def _alcance(roles=("CIUDADANO", "AGENTE"), **extra):
    return _e("roles", "PROJECT_REQUIREMENT", "SESSION_ROLE_SCOPE", domain="APPLICATION_SESSION",
              sesiones=None, targets=["portal"], values=list(roles), **extra)


def test_e40_un_rol_sin_entrada(t):
    """E-40 (VU4-40)."""
    citada = _sesion(evidencia=["comp", "roles"])
    r = _r(entradas=[citada], evidencia=EVIDENCIA + [_alcance()])
    t.igual("E-40 SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED", SIN_ROLES, r["state"])
    t.igual("E-40 y dice cual", {"portal": ["AGENTE"]}, r["coverage"]["rolesWithoutPolicy"])
    t.igual("E-40 con la entrada del rol, pasa", "PASS",
            _estado(entradas=[citada, AGENTE], evidencia=EVIDENCIA + [_alcance(), COMP_AGENTE]))
    t.igual("E-40 sin citarla no cuenta", "PASS", _estado(evidencia=EVIDENCIA + [_alcance()]))
    t.igual("E-40 de una fuente debil no cuenta", "PASS",
            _estado(entradas=[citada],
                    evidencia=EVIDENCIA + [dict(_alcance(), sourceType="README_STATEMENT")]))
    nfd = unicodedata.normalize("NFD", "GESTIÓN")
    t.igual("E-40 los roles se comparan en NFC", "PASS",
            _estado(entradas=[_sesion(roles=["CIUDADANO", unicodedata.normalize("NFC", "GESTIÓN")],
                                      evidencia=["comp", "roles"])],
                    evidencia=EVIDENCIA + [_alcance(("CIUDADANO", nfd))]))


# -- Los limites ------------------------------------------------------------------------------

VU3_SUPERFICIE = {"surfaceId": "portal", "sessionModel": "HYBRID",
                  "clients": [{"clientId": c, "closeEvents": [
                      {"event": ev, "result": "OLD_SESSION_REJECTED",
                       "evidence": ["b-%s-%s" % (c, ev)]}
                      for ev in ("APPLICATION_WINDOW_CLOSE", "BROWSER_CLOSE")]}
                      for c in ("escritorio", "movil")],
                  "evidence": ["modelo", "alcance"]}
VU3_EVIDENCIA = ([{"evidenceId": "modelo", "sourceType": "ARCHITECTURE_DOCUMENTATION",
                   "reference": "ref-modelo", "establishes": ["SESSION_MODEL"], "scope": "tramites",
                   "targets": ["portal"], "value": "HYBRID"},
                  {"evidenceId": "alcance", "sourceType": "PROJECT_REQUIREMENT",
                   "reference": "ref-alcance", "establishes": ["SUPPORTED_CLIENT_SCOPE"],
                   "scope": "tramites", "targets": ["portal"], "values": ["escritorio", "movil"]}]
                 + [{"evidenceId": "b-%s-%s" % (c, ev), "sourceType": "PROTECTED_ENDPOINT_CHECK",
                     "reference": "ref-b", "establishes": ["CLOSE_BEHAVIOR"], "scope": "tramites",
                     "targets": ["portal"], "value": "OLD_SESSION_REJECTED",
                     "domain": "APPLICATION_SESSION", "client": c, "event": ev}
                    for c in ("escritorio", "movil")
                    for ev in ("APPLICATION_WINDOW_CLOSE", "BROWSER_CLOSE")])


def _pass_de(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": [regla]}
                               for c in fila["policies"] + fila["checks"]}}


def test_e41_vu3_no_es_vu4(t):
    """E-41 (VU4-41)."""
    caso_vu3 = {"inventory": {"version": "1.0", "surfaces": [SUPERFICIE]},
                "sessions": {"version": "1.0", "surfaces": [VU3_SUPERFICIE]},
                "evidence": VU3_EVIDENCIA}
    t.igual("E-41 el cierre de Vu3 cumple", "PASS", VU3.evaluar(caso_vu3)["state"])
    caso = {"inventory": caso_vu3["inventory"],
            "browserSessions": caso_vu3["sessions"], "evidence": VU3_EVIDENCIA,
            "sessions": {"version": "1.0", "sessions": []}}
    r = CHECK.evaluar(caso)
    t.igual("E-41 y Vu4, sin vencimiento, no aprueba", SIN_COB, r["state"])
    t.igual("E-41 seguridad: Vu4 con los controles de Vu3 no cumple", "UNRESOLVED",
            seguridad.resultado("Vu4", dict(_pass_de("Vu3"), inactivityTimeout=[
                {"kind": "APPLICATION_INACTIVITY_TIMEOUT", "evidence": ["x"]}]),
                {"sessionPresent": True}, MATRIZ)["result"])


def test_e42_vu4_no_es_vu3(t):
    """E-42 (VU4-42)."""
    caso = _caso()
    t.igual("E-42 Vu4 pasa", "PASS", CHECK.evaluar(caso)["state"])
    t.verdadero("E-42 Vu3 no", VU3.evaluar({"inventory": caso["inventory"],
                                            "evidence": caso["evidence"]})["state"] != "PASS")
    t.igual("E-42 seguridad: Vu3 con los controles de Vu4 no cumple", "UNRESOLVED",
            seguridad.resultado("Vu3", _pass_de("Vu4"), {"browserSessionPresent": True},
                                MATRIZ)["result"])


def test_e43_c1_no_es_vu4(t):
    """E-43 (VU4-43)."""
    t.igual("E-43 con C1 en PASS Vu4 no cumple", "UNRESOLVED",
            seguridad.resultado("Vu4", dict(_pass_de("C1"), inactivityTimeout=[
                {"kind": "APPLICATION_INACTIVITY_TIMEOUT", "evidence": ["x"]}]),
                {"sessionPresent": True}, MATRIZ)["result"])
    t.igual("E-43 evaluar no recibe resultados de C1", ["caso", "senal", "autenticacion", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))


def test_e44_vu4_no_es_c1(t):
    """E-44 (VU4-44)."""
    t.igual("E-44 con Vu4 en PASS C1 no cumple", "UNRESOLVED",
            seguridad.resultado("C1", _pass_de("Vu4"), {"authenticationPresent": True},
                                MATRIZ)["result"])
    caso = _caso()
    t.igual("E-44 el caso que aprueba Vu4", "PASS", CHECK.evaluar(caso)["state"])
    t.verdadero("E-44 no aprueba C1", C1.evaluar(caso, True, None)["state"] != "PASS")


def test_e45_no_se_exige_cerrar_el_sso(t):
    """E-45 (VU4-45)."""
    texto = " ".join(_literales()).lower()
    for palabra in ("global", "single_logout", "backchannel", "frontchannel", "end_session",
                    "logout"):
        t.no_contiene("E-45 no nombra `%s`" % palabra, palabra, texto)
    activo = _comp("sso-activo", valor=VIEJA, fuente="SESSION_STORE_OBSERVATION",
                   domain="IDP_SSO_SESSION")
    r = _r(entradas=[_sesion(evidencia=["comp", "sso-activo"])], evidencia=EVIDENCIA + [activo])
    t.igual("E-45 con el SSO del proveedor activo, cumple", "PASS", r["state"])
    t.igual("E-45 y se informa aparte", ["sso-activo"],
            _ses(r)["supportingContext"]["IDP_SSO_SESSION"])


# -- La prueba ----------------------------------------------------------------------------------

def test_e46_en_produccion_no(t):
    """E-46 (VU4-46)."""
    r = _solo_con(_prueba(environment="PRD"))
    t.igual("E-46 insegura", INSEGURA, r["state"])
    t.contiene("E-46 y dice por que", "PRODUCTION", _ses(r)["unsafe"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-46 ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing", "selenium", "playwright",
                                 "time", "threading"}))


def test_e47_con_una_cuenta_real_no(t):
    """E-47 (VU4-47)."""
    r = _solo_con(_prueba(realUserAccount=True))
    t.igual("E-47 insegura", INSEGURA, r["state"])
    t.contiene("E-47 y dice por que", "REAL_USER_ACCOUNT", _ses(r)["unsafe"])


def test_e48_con_identidad_dedicada_en_qa(t):
    """E-48 (VU4-48)."""
    r = _solo_con(_prueba(), modo="AUTHORIZED_RUNTIME_TEST")
    t.igual("E-48 la sesion cumple", "PASS", _ses(r)["state"])
    t.igual("E-48 pasa", "PASS", r["state"])
    t.igual("E-48 con la prueba", ["rt"], _ses(r)["evidenceUsed"]["behavior"])


CREDENCIALES = ("JSESSIONID=hunter2abc", "Cookie: SESSION=hunter2abc", "sid=hunter2abc",
                "sessionid: hunter2abc", "access_token=hunter2abc", "refresh_token=hunter2abc",
                "code=hunter2abc", "code: hunter2abc", "authorization_code=hunter2abc",
                "password=hunter2abc", "Bearer abcdefghhunter2abc",
                "Set-Cookie: KEYCLOAK_SESSION=hunter2abc")
LEGITIMOS = ("session:portal-inactividad", "cookie:check-1", "sid:portal", "status_code=200",
             "sessionModel: HYBRID")


def test_e49_ningun_secreto(t):
    """E-49 (VU4-49)."""
    for texto in CREDENCIALES:
        entrada = _sesion(sid=texto, evidencia=["comp"])
        comp = _comp(sesiones=[texto])
        casos = {
            "un sessionId": _r(entradas=[entrada], evidencia=_sin("comp", comp)),
            "un valueRef": _r(entradas=[_sesion(valor="cfg?" + texto)]),
            "un id de evidencia": _r(evidencia=EVIDENCIA + [dict(POLITICA, evidenceId=texto)]),
            "un rol": _r(entradas=[_sesion(roles=[texto])]),
            "un texto de la salida": _r(entradas=[_sesion(sid=texto, resultado="NOT_TESTED")],
                                        evidencia=_sin("comp", comp)),
            "una referencia del token": _r(entradas=[_sesion(token={
                "accessTokenTimeoutRef": texto})]),
            "la senal": CHECK.senal(_caso(entradas=[entrada])),
            "rules.Vu4": normativa.resolucion(
                {"sessionPresent": True},
                evidencia={"ES0902.Vu4": _r(entradas=[entrada], evidencia=_sin("comp", comp))}
            )["standards"]["ES0902"]["rules"]["Vu4"],
            "seguridad": CHECK.para_seguridad(_r(entradas=[entrada],
                                                 evidencia=_sin("comp", comp)))[0],
        }
        for nombre, r in casos.items():
            t.no_contiene("E-49 `%s` en %s no sale" % (texto, nombre), "hunter2abc", json.dumps(r))
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu4_lib")
    for texto in LEGITIMOS:
        t.verdadero("E-49 `%s` no es una credencial" % texto, not lib.es_secreto(texto))
    sid = "session:portal-inactividad"
    r = _r(entradas=[_sesion(sid=sid)], evidencia=_sin("comp", _comp(sesiones=[sid])))
    t.igual("E-49 un sessionId legitimo sale entero", ("PASS", [sid]),
            (r["state"], [s["sessionId"] for s in r["sessions"]]))
    vu4 = normativa.resolucion({"sessionPresent": True}, evidencia={"ES0902.Vu4": r})
    t.igual("E-49 y llega entero a rules.Vu4", [sid],
            vu4["standards"]["ES0902"]["rules"]["Vu4"]["sessions"])
    for campo in ("cookie", "accessToken", "refreshToken", "sessionCookie", "password"):
        con = dict(_prueba(), **{campo: "abc"})
        t.igual("E-49 un item con `%s` no cuenta" % campo, SIN_VENC, _solo_con(con)["state"])
        t.verdadero("E-49 el registro no acepta `%s`" % campo,
                    bool(CHECK.validar_schema({"version": "1.0",
                                               "sessions": [dict(ENTRADA, **{campo: "abc"})]})))


# E-03b del reporte de seguridad: la palabra anuncia la contrasena, sin letra ni digito pegado
# antes y sin letra, digito ni `_` pegado despues (refutador de Vu4, pase 1).
CONTRASENAS = ("contraseña=hunter2abc", "contrasena=hunter2abc", "Contraseña: hunter2abc",
               "clave=hunter2abc", "clave: hunter2abc", "pass=hunter2abc",
               "passphrase=hunter2abc", "CLAVE = hunter2abc",
               unicodedata.normalize("NFD", "contraseña=hunter2abc"),
               "db_password hunter2abc", "'password' => 'hunter2abc'", "--password hunter2abc",
               "set password hunter2abc", "<password>hunter2abc</password>")
NO_SON_CONTRASENAS = ("passwordPolicy: strict", "password_hash=abc", "bypass=1", "compass:norte",
                      "enclave: x", "clavel:rojo", "passive-mode", "pwdless")


def test_e49_una_contrasena_en_castellano_o_corta(t):
    """E-49 (VU4-49). El pase 1 del refutador: `contraseña=`, `clave:` o `pass=` salian enteros."""
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu4_lib_contrasenas")
    for texto in CONTRASENAS:
        t.verdadero("E-49 `%s` es una contrasena" % texto, lib.es_secreto(texto))
        entrada = _sesion(sid=texto)
        ev = _sin("comp", _comp(sesiones=[texto]))
        r = _r(entradas=[entrada], evidencia=ev)
        casos = {
            "un sessionId": r,
            "un valueRef": _r(entradas=[_sesion(valor="cfg?" + texto)]),
            "la senal": CHECK.senal(_caso(entradas=[entrada], evidencia=ev)),
            "rules.Vu4": normativa.resolucion({"sessionPresent": True},
                                              evidencia={"ES0902.Vu4": r}
                                              )["standards"]["ES0902"]["rules"]["Vu4"],
        }
        for nombre, salida in casos.items():
            t.no_contiene("E-49 `%s` en %s no sale" % (texto, nombre), "hunter2abc",
                          json.dumps(salida, ensure_ascii=False))
    for texto in NO_SON_CONTRASENAS:
        t.verdadero("E-49 `%s` no es una contrasena" % texto, not lib.es_secreto(texto))


def test_e49_un_id_como_clave_de_diccionario(t):
    """E-49 (VU4-49). El pase 1 del refutador: `rolesWithoutPolicy` usa el surfaceId de clave, y
    la regla de salida miraba los valores y no las claves."""
    ids = ("sid=hunter2abc", "sid=hunter2xyz", "contraseña=hunter2qqq")
    superficies = [dict(SUPERFICIE, surfaceId=i) for i in ids]
    entradas = [_sesion(sid="s%d" % n, surface=i, evidencia=["c%d" % n, "roles%d" % n])
                for n, i in enumerate(ids)]
    ev = [POLITICA] + [_comp("c%d" % n, sesiones=["s%d" % n]) for n in range(len(ids))] + [
        dict(_alcance(), evidenceId="roles%d" % n, targets=[i]) for n, i in enumerate(ids)]
    r = _r(superficies, entradas, ev)
    t.igual("E-49 los roles sin politica siguen informados", SIN_ROLES, r["state"])
    t.no_contiene("E-49 un id como clave no sale", "hunter2", json.dumps(r, ensure_ascii=False))
    t.igual("E-49 y dos claves que se redactan igual no se funden", 3,
            len(r["coverage"]["rolesWithoutPolicy"]))
    t.igual("E-49 con un sufijo determinista", ["[redactado]", "[redactado]-2", "[redactado]-3"],
            sorted(r["coverage"]["rolesWithoutPolicy"]))
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu4_lib_claves")
    t.igual("E-49 una clave que no es credencial sale entera, y no la pisa un sufijo",
            {"[redactado]": 1, "[redactado]-2": 2, "portal": 3},
            lib.depurar({"[redactado]": 1, "sid=hunter2abc": 2, "portal": 3}))
    t.igual("E-49 el sufijo no depende del orden de las claves",
            lib.depurar({"sid=b1": 1, "sid=a1": 2}), lib.depurar({"sid=a1": 2, "sid=b1": 1}))


def test_e50_el_timeout_de_produccion_debilitado(t):
    """E-50 (VU4-50)."""
    r = _solo_con(_prueba(productionTimeoutWeakened=True))
    t.igual("E-50 insegura", INSEGURA, r["state"])
    t.contiene("E-50 y dice por que", "PRODUCTION_TIMEOUT_WEAKENED", _ses(r)["unsafe"])


def test_e51_las_condiciones_inseguras(t):
    """E-51 (VU4-51)."""
    for nombre, cambios, motivo in (
            ("sin autorizacion", {"authorized": None}, "NOT_AUTHORIZED"),
            ("autorizada en falso", {"authorized": False}, "NOT_AUTHORIZED"),
            ("sin identidad", {"testIdentityRef": None}, "NO_DEDICATED_TEST_IDENTITY"),
            ("en otro ambiente", {"environment": "HML"}, "ENVIRONMENT_MISMATCH"),
            ("en un ambiente desconocido", {"environment": "STAGING"}, "ENVIRONMENT_UNKNOWN"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED"),
            ("con secretos registrados", {"rawSecretsLogged": True}, "RAW_SECRETS_LOGGED")):
        r = _solo_con(_prueba(**cambios))
        t.igual("E-51 %s" % nombre, INSEGURA, r["state"])
        t.contiene("E-51 %s dice por que" % nombre, motivo, _ses(r)["unsafe"])
    t.igual("E-51 sin objetivo", SIN_OBJ, _solo_con(_prueba(outcome="UNAVAILABLE"))["state"])


def test_e52_no_poder_probar_no_es_fail(t):
    """E-52 (VU4-52)."""
    vieja = _prueba(valor=VIEJA, environment="PRD")
    r = _r(entradas=[_sesion(evidencia=["comp", "rt"])], evidencia=EVIDENCIA + [vieja])
    t.igual("E-52 insegura que dice que sigue sirviendo no es FAIL", INSEGURA, r["state"])
    sin = _prueba(valor=VIEJA, outcome="UNAVAILABLE")
    t.igual("E-52 sin objetivo que dice que sigue sirviendo no es FAIL", SIN_OBJ,
            _estado(entradas=[_sesion(evidencia=["comp", "rt"])], evidencia=EVIDENCIA + [sin]))
    t.igual("E-52 con el registro diciendo que sigue sirviendo, tampoco", INSEGURA,
            _estado(entradas=[_sesion(resultado=VIEJA, evidencia=["rt"])],
                    evidencia=_sin("comp", vieja)))
    nocfg = dict(_prueba(valor="NOT_CONFIGURED", environment="PRD"),
                 establishes=["INACTIVITY_TIMEOUT"])
    t.igual("E-52 una insegura que dice NOT_CONFIGURED no es FAIL", INSEGURA,
            _estado(entradas=[_sesion(estado="NOT_CONFIGURED", evidencia=["comp", "rt"])],
                    evidencia=EVIDENCIA + [nocfg]))
    t.igual("E-52 una prueba ajena insegura que dice rechazada no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(environment="PRD")]))


# -- El agregado -------------------------------------------------------------------------------

def test_e53_una_sesion_en_fail(t):
    """E-53 (VU4-53)."""
    vieja = _comp("vieja", valor=VIEJA, fuente="PROTECTED_ENDPOINT_CHECK", sesiones=["portal-agente"])
    r = _r(entradas=[ENTRADA, dict(AGENTE, evidence=["vieja"])], evidencia=EVIDENCIA + [vieja])
    t.igual("E-53 el agregado informa la falla", USABLE, r["state"])
    t.verdadero("E-53 y no aprueba", not CHECK.aprueba(r))
    t.igual("E-53 seguridad lo ve NON_COMPLIANT", "NON_COMPLIANT", _vu4_en_seguridad(r)["result"])
    dos = _r(entradas=[_sesion(valor="kc:access-lifespan"), dict(AGENTE, evidence=["vieja"])],
             evidencia=EVIDENCIA + [vieja])
    t.igual("E-53 dos fallas distintas dan FAIL", "FAIL", dos["state"])
    t.igual("E-53 y las nombra", sorted([SOLO_TOKEN, USABLE]),
            sorted(s for s in dos["states"] if s in FALLAS and s != "FAIL"))


def test_e54_una_sin_resolver_impide_el_pass(t):
    """E-54 (VU4-54)."""
    r = _r(entradas=[ENTRADA, dict(AGENTE, evidence=[])], evidencia=EVIDENCIA + [COMP_AGENTE])
    t.igual("E-54 no pasa", SIN_VENC, r["state"])
    t.igual("E-54 aunque una cumpla", "PASS", _ses(r)["state"])
    t.igual("E-54 seguridad no la ve cumplida", "UNRESOLVED", _vu4_en_seguridad(r)["result"])
    t.igual("E-54 dos sesiones con el mismo id no pasan", SIN_COB,
            _estado(entradas=[ENTRADA, dict(ENTRADA, roles=["OTRO"])]))


def test_e55_el_mismo_resultado(t):
    """E-55 (VU4-55)."""
    admin = _sesion(sid="admin", surface="backoffice", roles=["ADMIN"], evidencia=["comp-admin"])
    entradas = [ENTRADA, AGENTE, admin]
    ev = EVIDENCIA + [COMP_AGENTE, _comp("comp-admin", sesiones=["admin"]),
                      _comp("repetida"), _comp("repetida")]
    base = json.dumps(_r([SUPERFICIE, BACKOFFICE], entradas, ev), sort_keys=True)
    azar = random.Random(55)
    for vuelta in range(6):
        s, n, e = copy.deepcopy([SUPERFICIE, BACKOFFICE]), copy.deepcopy(entradas), copy.deepcopy(ev)
        azar.shuffle(s)
        azar.shuffle(n)
        azar.shuffle(e)
        t.igual("E-55 desordenado %d" % vuelta, base, json.dumps(_r(s, n, e), sort_keys=True))
    t.igual("E-55 los doce estados", sorted(LOS_12), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "sesión") for f in ("NFC", "NFD"))
    for nombre, par in (("iguales", ("SESSION_REJECTED", "SESSION_REJECTED")),
                        ("vieja la NFC", (VIEJA, "SESSION_REJECTED")),
                        ("vieja la NFD", ("SESSION_REJECTED", VIEJA))):
        gemelas = [_comp(nfc, valor=par[0]), _comp(nfd, valor=par[1])]
        for orden in (gemelas, gemelas[::-1]):
            t.igual("E-55 gemelas en NFC y NFD (%s) no pasan ni fallan" % nombre, SIN_VENC,
                    _solo_con(*orden)["state"])
    t.igual("E-55 citar en NFD una evidencia en NFC es citarla", "PASS",
            _r(entradas=[_sesion(evidencia=[nfd])], evidencia=_sin("comp", _comp(nfc)))["state"])
    s1, s2 = _sesion(sid=nfc), _sesion(sid=nfd, roles=["OTRO"])
    ev2 = _sin("comp", _comp(sesiones=[nfc]))
    t.igual("E-55 dos sesiones iguales en NFC son la misma, repetida",
            (SIN_COB, [nfc]), (_estado(entradas=[s1, s2], evidencia=ev2),
                               _r(entradas=[s1, s2], evidencia=ev2)["coverage"]["duplicatedSessions"]))
    t.igual("E-55 y dan lo mismo en los dos ordenes",
            json.dumps(_r(entradas=[s1, s2], evidencia=ev2), sort_keys=True),
            json.dumps(_r(entradas=[s2, s1], evidencia=ev2), sort_keys=True))


def test_e56_la_trazabilidad(t):
    """E-56 (VU4-56)."""
    caminos = {"sin senal": CHECK.evaluar({}), "pasa": _r(),
               "falla": _r(entradas=[_sesion(valor="kc:access-lifespan")]),
               "insegura": _solo_con(_prueba(environment="PRD")),
               "no aplica": _r(entradas=[], evidencia=[_ausente()]),
               "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True)}
    for nombre, r in caminos.items():
        t.igual("E-56 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-56 %s la clave" % nombre, "ES0902.Vu4", r["ruleKey"])
        t.igual("E-56 %s el control" % nombre, "session-inactivity-timeout", r["control"])
    resultado = _r()
    vu4 = normativa.resolucion({"sessionPresent": True},
                               evidencia={"ES0902.Vu4": resultado})["standards"]["ES0902"]
    vu4 = vu4["rules"]["Vu4"]
    t.igual("E-56 la unidad lleva Vu4", ("APPLICABLE", "PASS"), (vu4["applicability"],
                                                                vu4["result"]))
    t.igual("E-56 con sus sesiones", ["ciudadana"], vu4["sessions"])
    t.igual("E-56 y su evidencia por id", ["comp", "politica"], vu4["evidence"])
    t.igual("E-56 y nada mas", ["applicability", "evidence", "result", "sessions", "source"],
            sorted(vu4))
    t.igual("E-56 con la fuente", TRAZA, vu4["source"])
    falso = dict(resultado, control="otro-control")
    t.igual("E-56 un resultado ajeno no se proyecta", "UNRESOLVED",
            normativa.resolucion({"sessionPresent": True},
                                 evidencia={"ES0902.Vu4": falso})["standards"]["ES0902"]
            ["rules"]["Vu4"]["result"])
    t.igual("E-56 sin la senal no se proyecta", ("UNRESOLVED", []),
            tuple(normativa.resolucion({}, evidencia={"ES0902.Vu4": resultado})["standards"]
                  ["ES0902"]["rules"]["Vu4"][k] for k in ("result", "sessions")))
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = normativa.resolucion({"sessionPresent": True},
                                       evidencia={"ES0902.Vu4": resultado})
    finally:
        normativa._ruta_de_evidencia = original
    vu4_sin = sin_lib["standards"]["ES0902"]["rules"]["Vu4"]
    t.igual("E-56 sin la lib la unidad se arma, con el estado y sin ids",
            ("PASS", [], []), (vu4_sin["result"], vu4_sin["sessions"], vu4_sin["evidence"]))
    t.verdadero("E-56 y Vu3 sigue en la unidad",
                "Vu3" in sin_lib["standards"]["ES0902"]["rules"])


def test_e57_entra_al_libro_como_cualquier_regla(t):
    """E-57 (VU4-57)."""
    paquete = BIN / "reporte_seguridad"
    t.igual("E-57 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in paquete.iterdir() if p.is_file()))
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu4_57_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-4957")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _r(entradas=[_sesion(valor="kc:access-lifespan")]), "NON_COMPLIANT"),
                     ("sin resolver", _r(entradas=[_sesion(resultado="NOT_TESTED")]), "UNRESOLVED"),
                     ("no aplica", _r(entradas=[], evidencia=[_ausente()]), "NOT_APPLICABLE"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu4_en_seguridad(r)
            t.igual("E-57 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-4957", alcance,
                                           "2026-09-23T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-57 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-57 de ES0902.Vu4", [("ES0902", "Vu4", "ES0902.Vu4")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-57 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "NOT_APPLICABLE"],
                [e["result"] for e in eventos])
        t.igual("E-57 producido por desde_regla", ["desde_regla"] * 4,
                [e["details"]["producer"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    t.igual("E-57 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))
    t.igual("E-57 la identidad de Vu4 con el dominio del reporte", True,
            "Vu4" in [d for d in json.loads((REGLAS / "security-report-domains.json").read_text(
                encoding="utf-8"))["domains"] if d["domainId"] == "identity-session"][0]["rules"])


# -- Lo que agrega esta spec ------------------------------------------------------------------

def test_e58_lo_ilegible_que_nombra_la_sesion(t):
    """E-58."""
    for nombre, eid in (("una lista", ["x"]), ("un dict", {"k": "v"})):
        vieja = dict(_comp(valor=VIEJA, fuente="PROTECTED_ENDPOINT_CHECK"), evidenceId=eid)
        for forma, item in (("suelto", {"evidenceId": eid, "sessions": ["ciudadana"]}),
                            ("con forma de vieja", vieja)):
            t.igual("E-58 un id que es %s (%s) impide el PASS sin romper" % (nombre, forma),
                    SIN_VENC, _sin_excepcion(lambda: _estado(evidencia=EVIDENCIA + [item])))
            t.igual("E-58 un id que es %s (%s) no deja apagar la senal" % (nombre, forma),
                    "UNRESOLVED", _sin_excepcion(lambda: CHECK.senal(_caso(
                        entradas=[], evidencia=[_ausente(), dict(item, targets=["portal"])]))["value"]))
    mal = dict(_comp("mal", valor=VIEJA), outcome=["X"])
    t.igual("E-58 una mal formada no citada", SIN_VENC, _estado(evidencia=EVIDENCIA + [mal]))
    t.igual("E-58 una mal formada citada", SIN_VENC,
            _estado(entradas=[_sesion(evidencia=["comp", "mal"])], evidencia=EVIDENCIA + [mal]))
    t.igual("E-58 una con un dominio que no existe", SIN_VENC,
            _estado(evidencia=EVIDENCIA + [_comp("dom", valor=VIEJA, domain="OTRO")]))
    rep = _comp("rep", valor=VIEJA)
    t.igual("E-58 una repetida no citada", SIN_VENC,
            _estado(evidencia=EVIDENCIA + [rep, copy.deepcopy(rep)]))
    nfd = unicodedata.normalize("NFD", "sesión")
    t.igual("E-58 nombrar es igualdad en NFC", SIN_VENC,
            _r(entradas=[_sesion(sid=unicodedata.normalize("NFC", "sesión"))],
               evidencia=_sin("comp", _comp(sesiones=[unicodedata.normalize("NFC", "sesión")]),
                              dict(_comp("m", sesiones=[nfd]), outcome=1)))["state"])
    t.igual("E-58 una ilegible de otra sesion no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_comp("m", sesiones=["otra"]), outcome=1)]))
    for nombre, eid in (("vacio", ""), ("en blanco", "  ")):
        vacia = dict(_comp(), evidenceId=eid)
        t.igual("E-58 un id %s no cuenta aunque se lo cite" % nombre, SIN_VENC,
                _estado(entradas=[_sesion(evidencia=[eid])], evidencia=_sin("comp", vacia)))
    t.verdadero("E-58 ninguna es FAIL",
                _estado(evidencia=EVIDENCIA + [mal]) not in FALLAS)


def test_e59_un_solo_bloqueo(t):
    """E-59."""
    vieja = _prueba(valor=VIEJA, environment="PRD")
    t.igual("E-59 impide el PASS aunque no se la cite", INSEGURA,
            _estado(evidencia=EVIDENCIA + [vieja]))
    no_aplica = _r(entradas=[], evidencia=[_ausente(), dict(vieja, sessions=["x"])])
    t.igual("E-59 la senal sigue en FALSE", "FALSE", no_aplica["signalValue"])
    t.igual("E-59 e impide el NOT_APPLICABLE igual", INSEGURA, no_aplica["state"])
    t.igual("E-59 y en seguridad tampoco vuelve a ser NOT_APPLICABLE", "UNRESOLVED",
            _vu4_en_seguridad(no_aplica)["result"])
    t.contiene("E-59 y lo impedido queda a la vista", INSEGURA, no_aplica["states"])
    t.igual("E-59 sin objetivo, lo mismo", SIN_OBJ,
            _estado(entradas=[], evidencia=[_ausente(), dict(
                _prueba(valor=VIEJA, outcome="UNAVAILABLE"), sessions=["x"])]))
    t.igual("E-59 una ajena que dice rechazada no impide el NOT_APPLICABLE", "NOT_APPLICABLE",
            _estado(entradas=[], evidencia=[_ausente(), dict(_prueba(environment="PRD"),
                                                              sessions=["x"])]))
    falla = _r(entradas=[_sesion(valor="kc:access-lifespan")], evidencia=EVIDENCIA + [vieja])
    t.igual("E-59 y nunca tapa un FAIL", SOLO_TOKEN, falla["state"])
    vieja_citada = _comp("api", valor=VIEJA, fuente="PROTECTED_ENDPOINT_CHECK")
    r = _r(entradas=[_sesion(evidencia=["comp", "api"])],
           evidencia=EVIDENCIA + [vieja_citada, vieja])
    t.igual("E-59 tampoco el FAIL de la sesion", USABLE, r["state"])
    bloqueada = _r(evidencia=EVIDENCIA + [vieja])
    t.igual("E-59 y lo bloqueado no usa evidencia", [],
            _ses(bloqueada)["evidenceUsed"]["behavior"])
    t.igual("E-59 un solo paso de bloqueo en el modulo", 1,
            len([n for n in ast.walk(_arbol())
                 if isinstance(n, ast.FunctionDef) and n.name == "_bloquear"]))
    llamadas = sorted({f.name for f in ast.walk(_arbol()) if isinstance(f, ast.FunctionDef)
                       for n in ast.walk(f) if isinstance(n, ast.Call)
                       and getattr(n.func, "id", None) == "_bloquear"})
    t.igual("E-59 y lo llaman la sesion y el agregado", ["evaluar", "evaluar_sesion"], llamadas)


def test_e60_el_schema_cerrado(t):
    """E-60."""
    instalado = json.loads((REGLAS / "session-inactivity-timeout.json").read_text(encoding="utf-8"))
    t.igual("E-60 el registro se instala vacio", {"version": "1.0", "sessions": []}, instalado)
    t.igual("E-60 y valida", [], CHECK.validar_schema(instalado))
    t.igual("E-60 la sesion base valida", [],
            CHECK.validar_schema({"version": "1.0", "sessions": [ENTRADA]}))
    capas = {"la raiz": lambda d: d.update(extra=1),
             "una sesion": lambda d: d["sessions"][0].update(extra=1),
             "inactivityTimeout": lambda d: d["sessions"][0]["inactivityTimeout"].update(extra=1),
             "oidcTimeouts": lambda d: d["sessions"][0]["oidcTimeouts"].update(extra=1),
             "activitySemantics": lambda d: d["sessions"][0]["activitySemantics"].update(extra=1),
             "verification": lambda d: d["sessions"][0]["verification"].update(extra=1)}
    for nombre, cambiar in capas.items():
        doc = {"version": "1.0", "sessions": [copy.deepcopy(ENTRADA)]}
        cambiar(doc)
        t.verdadero("E-60 una clave de mas en %s no valida" % nombre, bool(CHECK.validar_schema(doc)))
        r = CHECK.evaluar({"inventory": {"version": "1.0", "surfaces": [SUPERFICIE]},
                           "sessions": doc, "evidence": EVIDENCIA})
        t.verdadero("E-60 y el check no pasa con ese registro (%s)" % nombre, r["state"] != "PASS")
        t.contiene("E-60 y dice por que (%s)" % nombre, "no valida contra su schema",
                   " ".join(r["issues"]))
    esquema = json.loads((SCHEMAS / "session-inactivity-timeout.schema.json").read_text(
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
    t.igual("E-60 seis capas de objeto", 6, len(capas_del_schema))
    t.verdadero("E-60 todas cerradas",
                all(c.get("additionalProperties") is False for c in capas_del_schema))


def test_e61_fuera_del_inventario_y_la_observacion(t):
    """E-61."""
    # La del portal cumple y su superficie esta resuelta: lo unico que falta es la de afuera.
    otra = _sesion(sid="externa", surface="otra", evidencia=["comp-externa"])
    ev = EVIDENCIA + [_comp("comp-externa", sesiones=["externa"])]
    fuera = _r(entradas=[ENTRADA, otra], evidencia=ev)
    t.igual("E-61 el caso sin la de afuera pasa", "PASS", _estado(evidencia=ev))
    t.igual("E-61 una sesion fuera del inventario impide el PASS", SIN_COB, fuera["state"])
    t.igual("E-61 la sesion se evalua igual", "PASS", _ses(fuera, "externa")["state"])
    t.igual("E-61 y se informa", ["externa"], fuera["coverage"]["sessionsOutsideInventory"])
    t.igual("E-61 sin surfaceRef, lo mismo", SIN_COB,
            _estado(entradas=[ENTRADA, dict(otra, surfaceRef=None)], evidencia=ev))
    t.verdadero("E-61 y nunca es FAIL", fuera["state"] not in FALLAS)
    admin = _sesion(sid="admin", surface="otra", estado="NOT_CONFIGURED", valor=None, token={},
                    evidencia=["nocfg-admin"])
    falla = _r(entradas=[ENTRADA, admin], evidencia=EVIDENCIA + [
        _e("nocfg-admin", "CONFIGURATION", "INACTIVITY_TIMEOUT", "NOT_CONFIGURED",
           sesiones=["admin"])])
    t.igual("E-61 fuera del inventario no tapa una falla", "FAIL", falla["state"])
    doble = dict(POLITICA, establishes=["ACTIVITY_SEMANTICS", "ACTIVITY_RESET_OBSERVATION"])
    r = _r(evidencia=_sin("politica", doble))
    t.igual("E-61 una observacion que tambien dice ser politica no resuelve la semantica",
            SIN_SEM, r["state"])
