# ES0902 §6 Vu3: cerrar la aplicacion o el browser no deja viva la sesion anterior.
#
# Escenarios E-01 a E-50 de docs/cambios/es0902-vu3-cierre-de-sesion/spec.md. E-nn es el VU3-nn
# del pedido de instalacion.
#
# 🔴 CASO es una superficie con dos clientes y los dos cierres exigidos, las cuatro combinaciones
# cumplidas con evidencia de comportamiento, y casi todo este archivo sale de romperla. E-27 y
# E-29 la miran en PASS.
import ast
import copy
import importlib.util
import inspect
import json
import random
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"

sys.path.insert(0, str(BIN))
from orquestacion import seguridad                      # noqa: E402
from orquestacion import senales                        # noqa: E402
from orquestacion import normativa                      # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "browser-close-session-termination.py"
RUTA_C1 = CONTROLES / "checks" / "oidc-keycloak-integration.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu3_cierre")
C1 = _cargar(RUTA_C1, "vu3_c1")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu3"}
LOS_10 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "SUPPORTED_BROWSER_SCOPE_UNRESOLVED", "BROWSER_SESSION_MODEL_UNRESOLVED",
          "BROWSER_CLOSE_BEHAVIOR_UNRESOLVED", "OLD_APPLICATION_SESSION_REMAINS_ACTIVE",
          "BROWSER_SESSION_TERMINATION_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
SIN_COMP = "BROWSER_CLOSE_BEHAVIOR_UNRESOLVED"
SIN_MODELO = "BROWSER_SESSION_MODEL_UNRESOLVED"
SIN_ALCANCE = "SUPPORTED_BROWSER_SCOPE_UNRESOLVED"
VIVA = "OLD_APPLICATION_SESSION_REMAINS_ACTIVE"
INSEGURA = "BROWSER_SESSION_TERMINATION_TEST_UNSAFE"
VENTANA, BROWSER, PESTANA = "APPLICATION_WINDOW_CLOSE", "BROWSER_CLOSE", "TAB_CLOSE"
CLIENTES = ("cliente-escritorio", "cliente-movil")

SUPERFICIE = {"surfaceId": "portal", "scope": "tramites", "audience": "INSTITUTIONAL",
              "environment": "QA", "currentProvider": "https://sso-qa.identidad.example/auth",
              "protocol": "OIDC", "flow": "FLUJO-A", "credentialEntryDelegated": True,
              "evidence": []}


def _e(eid, fuente, establece, valor=None, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece], "scope": "tramites", "targets": ["portal"]}
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _comp(cliente, evento, valor="OLD_SESSION_REJECTED", fuente="PROTECTED_ENDPOINT_CHECK",
          eid=None, domain="APPLICATION_SESSION", **extra):
    return _e(eid or "b-%s-%s" % (cliente, evento), fuente, "CLOSE_BEHAVIOR", valor,
              domain=domain, client=cliente, event=evento, **extra)


def _evento(cliente, evento, resultado="OLD_SESSION_REJECTED", evidencia=None):
    return {"event": evento, "result": resultado,
            "evidence": list(evidencia if evidencia is not None else ["b-%s-%s" % (cliente, evento)])}


def _cliente(cid, eventos=None):
    return {"clientId": cid,
            "closeEvents": eventos if eventos is not None else [_evento(cid, VENTANA),
                                                                _evento(cid, BROWSER)]}


ENTRADA = {"surfaceId": "portal", "sessionModel": "HYBRID",
           "clients": [_cliente(c) for c in CLIENTES], "evidence": ["modelo", "alcance"]}
EVIDENCIA = ([_e("modelo", "ARCHITECTURE_DOCUMENTATION", "SESSION_MODEL", "HYBRID"),
              _e("alcance", "PROJECT_REQUIREMENT", "SUPPORTED_CLIENT_SCOPE", values=list(CLIENTES))]
             + [_comp(c, ev) for c in CLIENTES for ev in (VENTANA, BROWSER)])


def _caso(superficies=None, entradas=None, evidencia=None, detectadas=None):
    caso = {"inventory": {"version": "1.0", "surfaces": copy.deepcopy(
                [SUPERFICIE] if superficies is None else superficies)},
            "sessions": {"version": "1.0", "surfaces": copy.deepcopy(
                [ENTRADA] if entradas is None else entradas)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if detectadas is not None:
        caso["detectedSurfaces"] = detectadas
    return caso


def _r(*a, senal=None, autenticacion=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal, autenticacion)


def _estado(*a, **k):
    return _r(*a, **k)["state"]


def _sup(r, sid="portal"):
    return [s for s in r["surfaces"] if s["surfaceId"] == sid][0]


def _comb(r, cliente, evento, sid="portal"):
    return [c for c in _sup(r, sid)["combinations"]
            if c["client"] == cliente and c["event"] == evento][0]


def _con_evento(cliente, evento, **cambios):
    """La entrada base con un evento cambiado."""
    e = copy.deepcopy(ENTRADA)
    for c in e["clients"]:
        if c["clientId"] == cliente:
            for ev in c["closeEvents"]:
                if ev["event"] == evento:
                    ev.update(cambios)
    return [e]


def _sin(eid, *mas):
    return [x for x in EVIDENCIA if x["evidenceId"] != eid] + list(mas)


def _solo_con(cliente, evento, *evidencia, resultado="OLD_SESSION_REJECTED"):
    """La combinacion (cliente, evento) sostenida solo por `evidencia`."""
    eid = "b-%s-%s" % (cliente, evento)
    ids = [x["evidenceId"] for x in evidencia]
    return _r(entradas=_con_evento(cliente, evento, result=resultado, evidence=ids),
              evidencia=_sin(eid, *evidencia))


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


A, B = CLIENTES


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (VU3-01)."""
    t.igual("E-01 la fila", "ES0902.Vu3", seguridad.regla("Vu3", MATRIZ)["ruleKey"])
    t.igual("E-01 el resultado", "ES0902.Vu3", _r()["ruleKey"])


def test_e02_los_ids(t):
    """E-02 (VU3-02)."""
    vu3 = seguridad.regla("Vu3", MATRIZ)
    t.igual("E-02 la senal", ["browserSessionPresent"], vu3["applicability"]["signals"])
    # La matriz declara dos agentes primarios; `dev-security` es el dueno normativo y va primero.
    t.igual("E-02 los agentes", ["dev-security", "dev-frontend"], vu3["primaryAgents"])
    t.igual("E-02 la policy", ["browser-close-session-termination-required"], vu3["policies"])
    t.igual("E-02 el check", ["browser-close-session-termination"], vu3["checks"])
    t.igual("E-02 el modulo", ("browserSessionPresent", "browser-close-session-termination",
                               "browser-close-session-termination-required"),
            (CHECK.SENAL, CHECK.CONTROL, CHECK.POLICY))
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("browser-close-session-termination-required", "POLICY",
             "controles/policies/browser-close-session-termination-required.md"),
            ("browser-close-session-termination", "CHECK",
             "controles/checks/browser-close-session-termination.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())


def test_e03_nada_nuevo(t):
    """E-03 (VU3-03)."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 10, len(registro["agents"]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 cero reviews", [], seguridad.regla("Vu3", MATRIZ)["reviews"])
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))


# -- La senal -------------------------------------------------------------------

def test_e04_una_sesion_en_el_browser_enciende(t):
    """E-04 (VU3-04)."""
    doc = CHECK.senal(_caso())
    t.igual("E-04 TRUE", "TRUE", doc["value"])
    t.igual("E-04 la cita", ["authentication-surfaces.json#portal"],
            [e["reference"] for e in doc["evidence"]])
    booleanos = senales.booleanos({"browserSessionPresent": doc})
    t.igual("E-04 enciende la fila", "APPLICABLE",
            seguridad.resolver_regla(seguridad.regla("Vu3", MATRIZ), booleanos)[0])
    presente = _e("pres", "APPLICATION_CONFIGURATION", "BROWSER_SESSION", "PRESENT")
    t.igual("E-04 tambien por evidencia, sin entrada", "TRUE",
            CHECK.senal(_caso(entradas=[], evidencia=[presente]))["value"])


def test_e05_oidc_no_apaga(t):
    """E-05 (VU3-05)."""
    for delegada in (True, False, None):
        sup = dict(SUPERFICIE, credentialEntryDelegated=delegada)
        t.igual("E-05 con credentialEntryDelegated %r sigue TRUE" % delegada, "TRUE",
                CHECK.senal(_caso([sup]))["value"])
    t.verdadero("E-05 el modulo no apaga por el proveedor",
                not any("keycloak" in l.lower() and l != "oidc-keycloak-integration.py"
                        for l in _literales()))


def test_e06_un_spa_con_tokens(t):
    """E-06 (VU3-06)."""
    entrada = dict(ENTRADA, sessionModel="TOKEN_BASED_APPLICATION_SESSION")
    t.igual("E-06 TRUE", "TRUE", CHECK.senal(_caso(entradas=[entrada]))["value"])


def test_e07_sin_sesion_con_autoridad_apaga(t):
    """E-07 (VU3-07)."""
    aus = _e("aus", "ARCHITECTURE_DOCUMENTATION", "BROWSER_SESSION", "ABSENT")
    caso = _caso(entradas=[], evidencia=[aus])
    t.igual("E-07 FALSE", "FALSE", CHECK.senal(caso)["value"])
    t.igual("E-07 NOT_APPLICABLE", "NOT_APPLICABLE", CHECK.evaluar(caso)["state"])
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT", "APPLICATION_CONFIGURATION"):
        t.igual("E-07 %s no apaga" % fuente, "UNRESOLVED",
                CHECK.senal(_caso(entradas=[], evidencia=[dict(aus, sourceType=fuente)]))["value"])
    # Fuera de la letra del pase 1: lo que dice que HAY sesion y no se pudo leer no deja apagar.
    insegura = _e("pres-rt", "AUTHORIZED_RUNTIME_TEST", "BROWSER_SESSION", "PRESENT",
                  environment="PRD", authorized=True, testIdentityRef="qa-user-7", outcome="CONFIRMED")
    t.igual("E-07 una prueba insegura que dice PRESENT no deja apagar", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[], evidencia=[aus, insegura]))["value"])
    t.igual("E-07 con una entrada del registro no apaga", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[dict(ENTRADA, sessionModel="UNRESOLVED")],
                              evidencia=[aus]))["value"])


def test_e08_sin_modelo_no_se_sabe(t):
    """E-08 (VU3-08)."""
    t.igual("E-08 UNRESOLVED", "UNRESOLVED",
            CHECK.senal(_caso(entradas=[dict(ENTRADA, sessionModel="UNRESOLVED")],
                              evidencia=[]))["value"])
    t.igual("E-08 y el check", "APPLICABILITY_UNRESOLVED",
            _estado(entradas=[dict(ENTRADA, sessionModel="UNRESOLVED")], evidencia=[]))


# -- Los dominios ---------------------------------------------------------------

def test_e09_aplicacion_y_proveedor_por_separado(t):
    """E-09 (VU3-09)."""
    idp = _e("idp", "IDP_SESSION_OBSERVATION", "CLOSE_BEHAVIOR", "OLD_SESSION_STILL_ACTIVE",
             domain="IDENTITY_PROVIDER", client=A, event=BROWSER)
    r = _r(evidencia=EVIDENCIA + [idp])
    t.igual("E-09 el SSO del proveedor activo no es FAIL", "PASS", r["state"])
    t.igual("E-09 y se informa aparte", ["idp"], _sup(r)["supportingContext"]["IDENTITY_PROVIDER"])
    t.verdadero("E-09 el dominio de la aplicacion se informa",
                "APPLICATION_SESSION" in _sup(r)["domains"])


def test_e10_el_tiempo_de_vida_del_token(t):
    """E-10 (VU3-10)."""
    tok = _comp(A, VENTANA, fuente="TOKEN_LIFETIME_CONFIGURATION", eid="tok",
                domain="TOKEN_LIFETIME")
    r = _solo_con(A, VENTANA, tok)
    t.igual("E-10 sin resolver", "UNRESOLVED", _comb(r, A, VENTANA)["state"])
    t.igual("E-10 y no pasa", SIN_COMP, r["state"])
    tok2 = dict(tok, sourceType="PROTECTED_ENDPOINT_CHECK")
    t.igual("E-10 con dominio TOKEN_LIFETIME tampoco", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, tok2), A, VENTANA)["state"])


def test_e11_no_se_exige_el_logout_global(t):
    """E-11 (VU3-11)."""
    texto = " ".join(_literales()).lower()
    for palabra in ("global", "single_logout", "backchannel", "frontchannel", "end_session"):
        t.no_contiene("E-11 no nombra `%s`" % palabra, palabra, texto)
    t.igual("E-11 pasa sin evidencia del proveedor", "PASS", _estado())


def test_e12_sesion_nueva_no_es_sesion_vieja(t):
    """E-12 (VU3-12)."""
    nueva = _comp(A, BROWSER, valor="NEW_SESSION_ESTABLISHED_AFTER_AUTH", eid="nueva")
    r = _solo_con(A, BROWSER, nueva, resultado="NEW_SESSION_ESTABLISHED_AFTER_AUTH")
    t.igual("E-12 cumple", "COMPLIANT", _comb(r, A, BROWSER)["state"])
    t.igual("E-12 pasa", "PASS", r["state"])
    vieja = dict(nueva, value="OLD_SESSION_STILL_ACTIVE")
    t.igual("E-12 la vieja es FAIL", "FAIL",
            _solo_con(A, BROWSER, vieja, resultado="NEW_SESSION_ESTABLISHED_AFTER_AUTH")["state"])


# -- Eventos y clientes -----------------------------------------------------------

def _sin_evento(cliente, evento):
    e = copy.deepcopy(ENTRADA)
    for c in e["clients"]:
        if c["clientId"] == cliente:
            c["closeEvents"] = [x for x in c["closeEvents"] if x["event"] != evento]
    return [e]


def test_e13_la_ventana(t):
    """E-13 (VU3-13)."""
    r = _r(entradas=_sin_evento(A, VENTANA))
    t.igual("E-13 sin la ventana", SIN_COMP, r["state"])
    t.igual("E-13 la combinacion falta", "MISSING", _comb(r, A, VENTANA)["state"])


def test_e14_el_browser(t):
    """E-14 (VU3-14)."""
    r = _r(entradas=_sin_evento(B, BROWSER))
    t.igual("E-14 sin el browser", SIN_COMP, r["state"])
    t.igual("E-14 la combinacion falta", "MISSING", _comb(r, B, BROWSER)["state"])


def test_e15_la_pestana_no_se_inventa(t):
    """E-15 (VU3-15)."""
    t.igual("E-15 sin pestana pasa", "PASS", _estado())
    e = copy.deepcopy(ENTRADA)
    e["clients"][0]["closeEvents"].append(_evento(A, PESTANA, "OLD_SESSION_STILL_ACTIVE",
                                                  ["b-tab"]))
    viva = _comp(A, PESTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="b-tab")
    r = _r(entradas=[e], evidencia=EVIDENCIA + [viva])
    t.igual("E-15 la pestana viva sin equivalencia no hace FAIL", "PASS", r["state"])
    t.igual("E-15 y se informa", ["%s/TAB_CLOSE" % A], _sup(r)["ignoredEvents"])
    # Fuera de la letra del pase 1: ni siquiera con una referencia que no existe.
    colgada = copy.deepcopy(ENTRADA)
    colgada["clients"][0]["closeEvents"].append(_evento(A, PESTANA, "UNRESOLVED", ["no-existe"]))
    colgada["clients"].append(_cliente("fuera", [_evento("fuera", VENTANA, "UNRESOLVED", ["nada"])]))
    t.igual("E-15 una referencia colgada en la pestana o fuera del alcance no bloquea", "PASS",
            _estado(entradas=[colgada]))
    eq = _e("eq", "PROJECT_REQUIREMENT", "TAB_CLOSE_EQUIVALENT")
    e2 = copy.deepcopy(e)
    e2["evidence"].append("eq")
    t.igual("E-15 con la equivalencia, la pestana viva es FAIL", "FAIL",
            _estado(entradas=[e2], evidencia=EVIDENCIA + [viva, eq]))
    e3 = copy.deepcopy(ENTRADA)
    e3["evidence"].append("eq")
    t.igual("E-15 con la equivalencia, la pestana se exige", SIN_COMP,
            _estado(entradas=[e3], evidencia=EVIDENCIA + [eq]))


def test_e16_los_clientes_los_dice_el_proyecto(t):
    """E-16 (VU3-16)."""
    texto = " ".join(_literales()).lower()
    for browser in ("chrome", "firefox", "edge", "safari", "opera", "chromium"):
        t.no_contiene("E-16 no nombra `%s`" % browser, browser, texto)
    e = copy.deepcopy(ENTRADA)
    e["clients"].append(_cliente("cliente-extra", [_evento("cliente-extra", VENTANA,
                                                           "OLD_SESSION_STILL_ACTIVE", [])]))
    r = _r(entradas=[e])
    t.igual("E-16 un cliente fuera del alcance no se evalua", "PASS", r["state"])
    t.igual("E-16 y se informa", ["cliente-extra"], _sup(r)["outOfScopeClients"])


def test_e17_sin_alcance(t):
    """E-17 (VU3-17)."""
    # Sin citarla: si la entrada citara un id que no esta, caeria por ilegible y no por el alcance.
    sin_cita = dict(copy.deepcopy(ENTRADA), evidence=["modelo"])
    t.igual("E-17 sin evidencia de alcance", SIN_ALCANCE,
            _estado(entradas=[sin_cita], evidencia=_sin("alcance")))
    otro = _e("alcance-2", "PROJECT_CONTRACT", "SUPPORTED_CLIENT_SCOPE", values=[A])
    t.igual("E-17 dos alcances que no coinciden", SIN_ALCANCE,
            _estado(evidencia=EVIDENCIA + [otro]))
    debil = dict(EVIDENCIA[1], sourceType="README_STATEMENT")
    t.igual("E-17 un alcance de una fuente debil", SIN_ALCANCE,
            _estado(evidencia=_sin("alcance", debil)))
    t.igual("E-17 un alcance legible que la entrada no cita", SIN_ALCANCE,
            _estado(entradas=[sin_cita]))


# -- El logout explicito -----------------------------------------------------------

def test_e18_el_boton_de_logout(t):
    """E-18 (VU3-18)."""
    boton = _comp(A, VENTANA, fuente="EXPLICIT_LOGOUT_TEST", eid="boton")
    t.igual("E-18 no aprueba", "UNRESOLVED", _comb(_solo_con(A, VENTANA, boton), A, VENTANA)["state"])


def test_e19_el_logout_del_proveedor(t):
    """E-19 (VU3-19)."""
    oidc = _comp(A, VENTANA, fuente="OIDC_LOGOUT_EVIDENCE", eid="oidc")
    t.igual("E-19 no aprueba", "UNRESOLVED", _comb(_solo_con(A, VENTANA, oidc), A, VENTANA)["state"])


def test_e20_dev_openid_connect_entra_por_su_clase(t):
    """E-20 (VU3-20)."""
    modelo = _e("modelo", "OIDC_SESSION_EVIDENCE", "SESSION_MODEL", "HYBRID")
    t.igual("E-20 sostiene el modelo", "PASS", _estado(evidencia=_sin("modelo", modelo)))
    cierre = _comp(A, VENTANA, fuente="OIDC_SESSION_EVIDENCE", eid="oidc-cierre")
    t.igual("E-20 y no el cierre", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, cierre), A, VENTANA)["state"])
    t.igual("E-20 ninguna skill nueva", 27, len([d for d in SKILLS.iterdir() if d.is_dir()]))


def test_e21_el_logout_es_contexto(t):
    """E-21 (VU3-21)."""
    e = dict(copy.deepcopy(ENTRADA), explicitLogoutEvidenceRefs=["logout-ok"])
    r = _r(entradas=[e])
    t.igual("E-21 sale como contexto", ["logout-ok"],
            _sup(r)["supportingContext"]["explicitLogoutRefs"])
    t.igual("E-21 y no cambia nada", _estado(), r["state"])
    sin_nada = copy.deepcopy(e)
    for c in sin_nada["clients"]:
        c["closeEvents"] = []
    t.igual("E-21 sin cierres, el logout no alcanza", SIN_COMP, _estado(entradas=[sin_nada]))


# -- El almacenamiento --------------------------------------------------------------

def _almacen(valor, eid):
    # Con el dominio de la aplicacion: con el del almacenamiento, el dominio solo ya la descarta y
    # el escenario -que el ALMACENAMIENTO no es el veredicto- no se probaria.
    return _comp(A, VENTANA, valor=valor, fuente="STORAGE_INSPECTION", eid=eid)


def test_e22_la_cookie_de_sesion(t):
    """E-22 (VU3-22)."""
    t.igual("E-22 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, _almacen("OLD_SESSION_REJECTED", "cookie")), A,
                  VENTANA)["state"])


def test_e23_session_storage(t):
    """E-23 (VU3-23)."""
    ss = _almacen("OLD_SESSION_REJECTED", "ss")
    t.igual("E-23 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, ss), A, VENTANA)["state"])


def test_e24_local_storage(t):
    """E-24 (VU3-24)."""
    ls = _almacen("OLD_SESSION_STILL_ACTIVE", "ls")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["b-%s-%s" % (A, VENTANA), "ls"]),
           evidencia=EVIDENCIA + [ls])
    t.igual("E-24 no reprueba", "PASS", r["state"])


def test_e25_el_artefacto_que_restaura_la_sesion(t):
    """E-25 (VU3-25)."""
    prueba = _comp(A, BROWSER, valor="OLD_SESSION_STILL_ACTIVE", fuente="AUTHORIZED_RUNTIME_TEST",
                   eid="rt", environment="QA", authorized=True, testIdentityRef="qa-user-7",
                   outcome="CONFIRMED")
    r = _r(entradas=_con_evento(A, BROWSER, evidence=["b-%s-%s" % (A, BROWSER), "rt"]),
           evidencia=EVIDENCIA + [prueba])
    t.igual("E-25 FAIL", "FAIL", r["state"])
    t.contiene("E-25 la sesion vieja", VIVA, r["states"])


def test_e26_la_sesion_del_servidor(t):
    """E-26 (VU3-26)."""
    srv = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", fuente="SESSION_STORE_OBSERVATION",
                eid="srv")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["b-%s-%s" % (A, VENTANA), "srv"]),
           evidencia=EVIDENCIA + [srv])
    t.igual("E-26 FAIL", "FAIL", r["state"])


def test_e27_el_artefacto_rechazado(t):
    """E-27 (VU3-27)."""
    r = _r()
    t.igual("E-27 PASS", "PASS", r["state"])
    t.igual("E-27 las cuatro combinaciones", ["COMPLIANT"] * 4,
            [c["state"] for c in _sup(r)["combinations"]])


# -- La sesion vieja ------------------------------------------------------------------

def test_e28_la_pantalla_con_la_api_viva(t):
    """E-28 (VU3-28)."""
    ui = _comp(A, VENTANA, fuente="UI_OBSERVATION", eid="ui")
    api = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="api")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["ui", "api"]),
           evidencia=_sin("b-%s-%s" % (A, VENTANA), ui, api))
    t.igual("E-28 FAIL", "FAIL", r["state"])


def test_e29_la_pantalla_con_la_sesion_rechazada(t):
    """E-29 (VU3-29)."""
    ui = _comp(A, VENTANA, fuente="UI_OBSERVATION", eid="ui")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["ui", "b-%s-%s" % (A, VENTANA)]),
           evidencia=EVIDENCIA + [ui])
    t.igual("E-29 con la sesion rechazada pasa", "PASS", r["state"])
    t.igual("E-29 la pantalla sola, no", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, ui), A, VENTANA)["state"])


def test_e30_una_sesion_nueva_despues_del_sso(t):
    """E-30 (VU3-30)."""
    nueva = _comp(A, VENTANA, valor="NEW_SESSION_ESTABLISHED_AFTER_AUTH", eid="sso",
                  fuente="AUTHORIZED_RUNTIME_TEST", environment="QA", authorized=True,
                  testIdentityRef="qa-user-7", outcome="CONFIRMED")
    r = _solo_con(A, VENTANA, nueva, resultado="NEW_SESSION_ESTABLISHED_AFTER_AUTH")
    t.igual("E-30 no es reusar la vieja", "PASS", r["state"])


def test_e31_la_sesion_vieja_que_vuelve(t):
    """E-31 (VU3-31)."""
    t.igual("E-31 declarada, FAIL", "FAIL",
            _estado(entradas=_con_evento(A, BROWSER, result="OLD_SESSION_STILL_ACTIVE",
                                         evidence=[]),
                    evidencia=_sin("b-%s-%s" % (A, BROWSER))))


# -- Los hooks ------------------------------------------------------------------------

def _hook(nombre):
    return _comp(A, VENTANA, fuente="IMPLEMENTATION_HOOK", eid="hook-%s" % nombre)


def test_e32_beforeunload(t):
    """E-32 (VU3-32)."""
    t.igual("E-32 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, _hook("beforeunload")), A, VENTANA)["state"])


def test_e33_unload(t):
    """E-33 (VU3-33)."""
    t.igual("E-33 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, _hook("unload")), A, VENTANA)["state"])


def test_e34_pagehide(t):
    """E-34 (VU3-34)."""
    t.igual("E-34 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, _hook("pagehide")), A, VENTANA)["state"])


def test_e35_send_beacon(t):
    """E-35 (VU3-35)."""
    fuente = _comp(A, VENTANA, fuente="SOURCE_CODE", eid="beacon")
    t.igual("E-35 no aprueba", "UNRESOLVED",
            _comb(_solo_con(A, VENTANA, fuente), A, VENTANA)["state"])


def test_e36_el_comportamiento_gana(t):
    """E-36 (VU3-36)."""
    hook = _hook("beforeunload")
    viva = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="viva")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["hook-beforeunload", "viva"]),
           evidencia=_sin("b-%s-%s" % (A, VENTANA), hook, viva))
    t.igual("E-36 FAIL", "FAIL", r["state"])
    t.igual("E-36 y el hook se informa", ["hook-beforeunload"],
            _sup(r)["supportingContext"]["implementation"])


# -- La prueba ------------------------------------------------------------------------

PRUEBA = dict(environment="QA", authorized=True, testIdentityRef="qa-user-7", outcome="CONFIRMED")


def _prueba(valor="OLD_SESSION_REJECTED", **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _comp(A, VENTANA, valor=valor, fuente="AUTHORIZED_RUNTIME_TEST", eid="rt", **datos)


def test_e37_en_produccion_no(t):
    """E-37 (VU3-37)."""
    r = _solo_con(A, VENTANA, _prueba(environment="PRD"))
    t.igual("E-37 insegura", INSEGURA, r["state"])
    t.contiene("E-37 y dice por que", "PRODUCTION", _comb(r, A, VENTANA)["unsafe"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-37 ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing", "selenium", "playwright"}))


def test_e38_con_una_cuenta_real_no(t):
    """E-38 (VU3-38)."""
    r = _solo_con(A, VENTANA, _prueba(realUserAccount=True))
    t.igual("E-38 insegura", INSEGURA, r["state"])
    t.contiene("E-38 y dice por que", "REAL_USER_ACCOUNT", _comb(r, A, VENTANA)["unsafe"])


def test_e39_con_identidad_dedicada_en_qa(t):
    """E-39 (VU3-39)."""
    r = _solo_con(A, VENTANA, _prueba())
    t.igual("E-39 cumple", "COMPLIANT", _comb(r, A, VENTANA)["state"])
    t.igual("E-39 pasa", "PASS", r["state"])


def test_e40_ningun_secreto(t):
    """E-40 (VU3-40)."""
    for campo in ("cookie", "accessToken", "refreshToken", "sessionId", "id_token_hint"):
        con = dict(_prueba(), **{campo: "abc"})
        r = _solo_con(A, VENTANA, con)
        t.igual("E-40 un item con `%s` no cuenta" % campo, "UNRESOLVED",
                _comb(r, A, VENTANA)["state"])
    for texto in ("app:password=hunter2abc", "env/DB_PASSWORD=hunter2abc",
                  "Bearer abcdefghijkhunter2abc", "session_token=hunter2abc"):
        casos = {
            "un surfaceId": _r([dict(SUPERFICIE, surfaceId=texto)],
                               [dict(ENTRADA, surfaceId=texto)]),
            "un clientId": _r(entradas=[dict(ENTRADA, clients=[_cliente(texto)])]),
            "una superficie detectada": _r(detectadas=[texto]),
            "un id de evidencia": _r(evidencia=EVIDENCIA + [dict(EVIDENCIA[0], evidenceId=texto)]),
            "la senal": CHECK.senal(_caso([dict(SUPERFICIE, surfaceId=texto)],
                                          [dict(ENTRADA, surfaceId=texto)])),
        }
        for nombre, r in casos.items():
            t.no_contiene("E-40 `%s` en %s no sale" % (texto, nombre), "hunter2abc", json.dumps(r))
    # 🔴 El pase 1 del refutador: para Vu3 la sesion ES la credencial.
    for texto in ("JSESSIONID=hunter2abc", "sessionid=hunter2abc", "sid=hunter2abc",
                  "Cookie: SESSION=hunter2abc", "Set-Cookie: KEYCLOAK_SESSION=hunter2abc",
                  "code=hunter2abc", "id_token_hint=hunter2abc", "authorization_code=hunter2abc"):
        for nombre, r in (("un surfaceId", _r([dict(SUPERFICIE, surfaceId=texto)],
                                              [dict(ENTRADA, surfaceId=texto)])),
                          ("un clientId", _r(entradas=[dict(ENTRADA, clients=[_cliente(texto)])]))):
            t.no_contiene("E-40 `%s` en %s no sale" % (texto, nombre), "hunter2abc", json.dumps(r))
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu3_lib")
    for texto in ("status_code=200", "errorCode: 7", "sessionModel: HYBRID"):
        t.verdadero("E-40 `%s` no es una credencial" % texto, not lib.es_secreto(texto))
    t.igual("E-40 el registro no acepta una cookie", True,
            bool(CHECK.validar_schema({"version": "1.0",
                                       "surfaces": [dict(ENTRADA, cookie="abc")]})))


# `code=` y `code:` se redactan siempre, con el valor que sea: `zip code=1414` y `http code: 401`
# no son ids legitimos (refutador, pase 3). La unica excepcion es `status_code=`.
LEGITIMOS = ("session:portal-close", "cookie:check-1", "sid:portal", "sub-session: ok", "consid=3",
             "session:portal-window", "status_code=200")


def test_e40_un_id_legitimo_no_se_redacta(t):
    """E-40 (VU3-40). El pase 2 del refutador: la regla de salida no se come ids legitimos que
    nombran una sesion, una cookie o un codigo; las formas de credencial siguen sin salir."""
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu3_lib_legitimos")
    for texto in LEGITIMOS:
        t.verdadero("E-40 `%s` no es una credencial" % texto, not lib.es_secreto(texto))
    # Las vecinas siguen siendo credencial: no importa el nombre de la cookie ni el prefijo.
    for texto in ("Cookie: foo=hunter2abc", "PHPSESSID=hunter2abc", "sub-session=hunter2abc",
                  "code=12345678-aaaa-hunter2abc", "code: hunter2abc", "sessionid: hunter2abc"):
        t.verdadero("E-40 `%s` sigue siendo una credencial" % texto, lib.es_secreto(texto))
    # El pase 3 del refutador: un codigo de autorizacion hecho solo de digitos tambien es un codigo.
    for texto, valor in (("code=4815162342", "4815162342"),
                         ("portal?code=4815162342&state=x", "4815162342"),
                         ("code = 99999999", "99999999"), ("http code: 401", None)):
        t.verdadero("E-40 `%s` es una credencial" % texto, lib.es_secreto(texto))
        if valor is None:
            continue
        for nombre, r in (("un surfaceId", _r([dict(SUPERFICIE, surfaceId=texto)],
                                              [dict(ENTRADA, surfaceId=texto)])),
                          ("un clientId", _r(entradas=[dict(ENTRADA, clients=[_cliente(texto)])])),
                          ("la senal", CHECK.senal(_caso([dict(SUPERFICIE, surfaceId=texto)],
                                                         [dict(ENTRADA, surfaceId=texto)])))):
            t.no_contiene("E-40 `%s` en %s no sale" % (texto, nombre), valor, json.dumps(r))
    base = "b-%s-%s" % (A, VENTANA)
    for texto in ("session:portal-close", "cookie:check-1"):
        r = _r(entradas=_con_evento(A, VENTANA, evidence=[texto]),
               evidencia=_sin(base, dict(_comp(A, VENTANA), evidenceId=texto)))
        t.igual("E-40 `%s` pasa entero por la salida" % texto, ("PASS", [texto]),
                (r["state"], _comb(r, A, VENTANA)["evidenceUsed"]))
        vu3 = normativa.resolucion({"browserSessionPresent": True}, evidencia={"ES0902.Vu3": r})
        vu3 = vu3["standards"]["ES0902"]["rules"]["Vu3"]
        t.contiene("E-40 `%s` llega entero a rules.Vu3.evidence" % texto, texto, vu3["evidence"])
    sid = "session:portal-window"
    r = _r([dict(SUPERFICIE, surfaceId=sid)], [dict(ENTRADA, surfaceId=sid)])
    t.igual("E-40 un surfaceId legitimo sale entero", [sid],
            [s["surfaceId"] for s in r["surfaces"]])


def test_e41_las_condiciones_inseguras(t):
    """E-41 (VU3-41)."""
    for nombre, cambios, motivo in (
            ("sin autorizacion", {"authorized": None}, "NOT_AUTHORIZED"),
            ("sin identidad", {"testIdentityRef": None}, "NO_DEDICATED_TEST_IDENTITY"),
            ("en otro ambiente", {"environment": "HML"}, "ENVIRONMENT_MISMATCH"),
            ("con secretos registrados", {"rawSecretsLogged": True}, "RAW_SECRETS_LOGGED"),
            ("con cuenta real", {"realUserAccount": True}, "REAL_USER_ACCOUNT")):
        r = _solo_con(A, VENTANA, _prueba(**cambios))
        t.igual("E-41 %s" % nombre, INSEGURA, r["state"])
        t.contiene("E-41 %s dice por que" % nombre, motivo, _comb(r, A, VENTANA)["unsafe"])


def test_e42_no_poder_probar_no_es_fail(t):
    """E-42 (VU3-42)."""
    viva = _prueba(valor="OLD_SESSION_STILL_ACTIVE", environment="PRD")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["b-%s-%s" % (A, VENTANA), "rt"]),
           evidencia=EVIDENCIA + [viva])
    t.igual("E-42 insegura que dice viva no es FAIL", INSEGURA, r["state"])
    sin = _prueba(valor="OLD_SESSION_STILL_ACTIVE", outcome="UNAVAILABLE")
    r = _r(entradas=_con_evento(A, VENTANA, evidence=["b-%s-%s" % (A, VENTANA), "rt"]),
           evidencia=EVIDENCIA + [sin])
    t.igual("E-42 sin objetivo que dice viva no es FAIL", "TEST_TARGET_UNAVAILABLE", r["state"])
    # Fuera de la letra del pase 1: una prueba insegura NO citada que dice "rechazada" no mueve nada.
    ajena = _prueba(environment="PRD")
    t.igual("E-42 una prueba ajena insegura que dice rechazada no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [ajena]))


# -- Los limites ------------------------------------------------------------------------

def test_e43_el_timeout_no_reemplaza(t):
    """E-43 (VU3-43)."""
    to = _comp(A, VENTANA, fuente="INACTIVITY_TIMEOUT_CONFIGURATION", eid="to")
    t.igual("E-43 no aprueba", "UNRESOLVED", _comb(_solo_con(A, VENTANA, to), A, VENTANA)["state"])
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.verdadero("E-43 sin numeros salvo 0 o 1: %s" % numeros, set(numeros) <= {0, 1})


def _pass_de(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": [regla]}
                               for c in fila["policies"] + fila["checks"]}}


def test_e44_vu3_no_es_vu4(t):
    """E-44 (VU3-44)."""
    ev = _pass_de("Vu3")
    t.igual("E-44 Vu3 cumple", "COMPLIANT",
            seguridad.resultado("Vu3", ev, {"browserSessionPresent": True}, MATRIZ)["result"])
    senal = {s: True for s in seguridad.regla("Vu4", MATRIZ)["applicability"]["signals"]}
    # Vu4 exige su propia evidencia de inactividad: con ella y sus controles cumple, y el test
    # discrimina. Con la misma evidencia y los controles de Vu3 en lugar de los suyos, no.
    inactividad = {"inactivityTimeout": [{"kind": "SESSION_INACTIVITY_CONFIGURATION",
                                          "evidence": ["vu4-cfg"]}]}
    propio = dict(_pass_de("Vu4"), **inactividad)
    t.igual("E-44 Vu4 con lo suyo cumple", "COMPLIANT",
            seguridad.resultado("Vu4", propio, senal, MATRIZ)["result"])
    t.verdadero("E-44 y con los controles de Vu3, no",
                seguridad.resultado("Vu4", dict(ev, **inactividad), senal, MATRIZ)["result"]
                != "COMPLIANT")


def test_e45_c1_no_es_vu3(t):
    """E-45 (VU3-45)."""
    t.igual("E-45 con C1 en PASS Vu3 no cumple", "UNRESOLVED",
            seguridad.resultado("Vu3", _pass_de("C1"), {"browserSessionPresent": True},
                                MATRIZ)["result"])
    t.igual("E-45 evaluar no recibe resultados de C1", ["caso", "senal", "autenticacion", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))


def test_e46_vu3_no_es_c1(t):
    """E-46 (VU3-46)."""
    t.igual("E-46 con Vu3 en PASS C1 no cumple", "UNRESOLVED",
            seguridad.resultado("C1", _pass_de("Vu3"), {"authenticationPresent": True},
                                MATRIZ)["result"])
    caso = _caso()
    t.igual("E-46 el caso que aprueba Vu3", "PASS", CHECK.evaluar(caso)["state"])
    t.verdadero("E-46 no aprueba C1", C1.evaluar(caso, True, None)["state"] != "PASS")


# -- El agregado -----------------------------------------------------------------------

def test_e47_una_combinacion_no_tapa_a_otra(t):
    """E-47 (VU3-47)."""
    viva = _comp(B, BROWSER, valor="OLD_SESSION_STILL_ACTIVE", eid="viva-b")
    r = _r(entradas=_con_evento(B, BROWSER, evidence=["viva-b"]),
           evidencia=_sin("b-%s-%s" % (B, BROWSER), viva))
    t.igual("E-47 FAIL", "FAIL", r["state"])
    t.igual("E-47 las otras cumplen", 3,
            len([c for c in _sup(r)["combinations"] if c["state"] == "COMPLIANT"]))


def test_e48_una_sin_resolver_impide_el_pass(t):
    """E-48 (VU3-48)."""
    r = _r(entradas=_con_evento(B, VENTANA, result="UNRESOLVED"))
    t.igual("E-48 no pasa", SIN_COMP, r["state"])
    mal = dict(_comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="mal"), outcome=["X"])
    t.igual("E-48 una ilegible que nombra la superficie, no citada", SIN_COMP,
            _estado(evidencia=EVIDENCIA + [mal]))
    rep = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="rep")
    t.igual("E-48 una repetida no citada", SIN_COMP,
            _estado(evidencia=EVIDENCIA + [rep, copy.deepcopy(rep)]))
    viva = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", eid="viva-nc")
    t.igual("E-48 una viva no citada impide el PASS sin hacer FAIL", SIN_COMP,
            _estado(evidencia=EVIDENCIA + [viva]))
    # 🔴 El pase 1 del refutador: dos ids iguales en NFC son el mismo id, repetido.
    nfc, nfd = (unicodedata.normalize(f, "b-é") for f in ("NFC", "NFD"))
    base = "b-%s-%s" % (A, VENTANA)
    for nombre, par in (("iguales", ("OLD_SESSION_REJECTED", "OLD_SESSION_REJECTED")),
                        ("viva la NFC", ("OLD_SESSION_STILL_ACTIVE", "OLD_SESSION_REJECTED")),
                        ("viva la NFD", ("OLD_SESSION_REJECTED", "OLD_SESSION_STILL_ACTIVE"))):
        gemelas = [_comp(A, VENTANA, valor=par[0], eid=nfc), _comp(A, VENTANA, valor=par[1], eid=nfd)]
        r = _r(entradas=_con_evento(A, VENTANA, evidence=[nfc]), evidencia=_sin(base, *gemelas))
        t.igual("E-48 gemelas en NFC y NFD (%s) no pasan ni fallan" % nombre, SIN_COMP, r["state"])
    citada_nfd = _r(entradas=_con_evento(A, VENTANA, evidence=[unicodedata.normalize("NFD", "b-é")]),
                    evidencia=_sin(base, _comp(A, VENTANA, eid=nfc)))
    t.igual("E-48 citar en NFD una evidencia en NFC es citarla", "PASS", citada_nfd["state"])
    na = _con_evento(A, VENTANA, result="NOT_APPLICABLE", evidence=["na"])
    motivo = _e("na", "PROJECT_REQUIREMENT", "CLOSE_EVENT_NOT_APPLICABLE", client=A, event=VENTANA)
    t.igual("E-48 un NOT_APPLICABLE con su autoridad pasa", "PASS",
            _estado(entradas=na, evidencia=_sin(base, motivo)))
    t.igual("E-48 y contra una viva legible, no", SIN_COMP,
            _estado(entradas=na, evidencia=_sin(base, motivo, viva)))


def _sin_excepcion(f):
    try:
        return f()
    except Exception as e:                              # noqa: BLE001 - el test nombra la excepcion
        return "EXCEPCION %s: %s" % (type(e).__name__, e)


def test_e48_un_id_que_no_es_texto_es_ilegible(t):
    """E-48 (VU3-48). El pase 2 del refutador: un id de evidencia que no es texto, o vacio, es
    ilegible. Impide el PASS y no deja apagar la senal; nunca rompe la evaluacion."""
    aus = _e("aus", "ARCHITECTURE_DOCUMENTATION", "BROWSER_SESSION", "ABSENT")
    for nombre, eid in (("una lista", ["x"]), ("un dict", {"k": "v"})):
        viva = dict(_comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE"), evidenceId=eid)
        for forma, item in (("suelto", {"evidenceId": eid, "targets": ["portal"]}),
                            ("con forma de viva", viva)):
            t.igual("E-48 un id que es %s (%s) impide el PASS sin romper" % (nombre, forma),
                    SIN_COMP, _sin_excepcion(lambda: _estado(evidencia=EVIDENCIA + [item])))
            t.igual("E-48 un id que es %s (%s) no deja apagar la senal" % (nombre, forma),
                    "UNRESOLVED", _sin_excepcion(
                        lambda: CHECK.senal(_caso(entradas=[], evidencia=[aus, item]))["value"]))
    base = "b-%s-%s" % (A, VENTANA)
    for nombre, eid in (("vacio", ""), ("en blanco", "  ")):
        vacia = dict(_comp(A, VENTANA), evidenceId=eid)
        t.igual("E-48 un id %s no cuenta aunque se lo cite" % nombre, SIN_COMP,
                _estado(entradas=_con_evento(A, VENTANA, evidence=[eid]),
                        evidencia=_sin(base, vacia)))


def test_e48_lo_ilegible_bloquea_igual_en_toda_rama(t):
    """E-48 (VU3-48). El pase 2 del refutador: bloquea lo que la entrada cita o lo que dice que la
    sesion vieja sigue viva, tambien cuando el cierre se declara NOT_APPLICABLE."""
    base = "b-%s-%s" % (A, VENTANA)
    motivo = _e("na", "PROJECT_REQUIREMENT", "CLOSE_EVENT_NOT_APPLICABLE", client=A, event=VENTANA)
    na = _con_evento(A, VENTANA, result="NOT_APPLICABLE", evidence=["na"])
    for nombre, prueba, esperado in (
            ("insegura", _prueba(valor="OLD_SESSION_STILL_ACTIVE", environment="PRD"), INSEGURA),
            ("sin objetivo", _prueba(valor="OLD_SESSION_STILL_ACTIVE", outcome="UNAVAILABLE"),
             "TEST_TARGET_UNAVAILABLE")):
        t.igual("E-48 contra un rechazado, una prueba %s no citada que dice viva bloquea" % nombre,
                esperado, _estado(evidencia=EVIDENCIA + [prueba]))
        r = _r(entradas=na, evidencia=_sin(base, motivo, prueba))
        t.igual("E-48 contra un NOT_APPLICABLE, tambien (%s)" % nombre, esperado, r["state"])
        t.igual("E-48 y la combinacion bloqueada no usa evidencia (%s)" % nombre, [],
                _comb(r, A, VENTANA)["evidenceUsed"])
    cita = _con_evento(A, VENTANA, result="NOT_APPLICABLE", evidence=["na", "rt"])
    t.igual("E-48 un NOT_APPLICABLE que cita una prueba insegura no es NOT_APPLICABLE", INSEGURA,
            _estado(entradas=cita, evidencia=_sin(base, motivo, _prueba(environment="PRD"))))
    t.igual("E-48 una prueba ajena insegura que dice rechazada no bloquea un NOT_APPLICABLE", "PASS",
            _estado(entradas=na, evidencia=_sin(base, motivo, _prueba(environment="PRD"))))


def test_e49_el_mismo_resultado(t):
    """E-49 (VU3-49)."""
    otra = dict(SUPERFICIE, surfaceId="backoffice", credentialEntryDelegated=False)
    entradas = [ENTRADA, dict(copy.deepcopy(ENTRADA), surfaceId="backoffice")]
    ev = EVIDENCIA + [dict(x, evidenceId=x["evidenceId"] + "-bo", targets=["backoffice"])
                      for x in EVIDENCIA]
    for x in entradas[1]["clients"]:
        for e in x["closeEvents"]:
            e["evidence"] = [i + "-bo" for i in e["evidence"]]
    entradas[1]["evidence"] = ["modelo-bo", "alcance-bo"]
    base = json.dumps(_r([SUPERFICIE, otra], entradas, ev + [copy.deepcopy(ev[-1])]),
                      sort_keys=True)
    azar = random.Random(49)
    for vuelta in range(6):
        s, n, e = copy.deepcopy([SUPERFICIE, otra]), copy.deepcopy(entradas), copy.deepcopy(
            ev + [ev[-1]])
        azar.shuffle(s)
        azar.shuffle(n)
        azar.shuffle(e)
        for x in n:
            azar.shuffle(x["clients"])
            for c in x["clients"]:
                azar.shuffle(c["closeEvents"])
        t.igual("E-49 desordenado %d" % vuelta, base, json.dumps(_r(s, n, e), sort_keys=True))
    t.igual("E-49 los diez estados", sorted(LOS_10), sorted(CHECK.ESTADOS))
    # 🔴 El pase 1 del refutador: la misma superficie dos veces en el inventario -o dos iguales en
    # NFC- se evalua cada una con la suya, y el orden no decide.
    viva = _comp(A, VENTANA, valor="OLD_SESSION_STILL_ACTIVE", fuente="AUTHORIZED_RUNTIME_TEST",
                 eid="rt", environment="QA", authorized=True, testIdentityRef="qa-user-7",
                 outcome="CONFIRMED")
    entradas = _con_evento(A, VENTANA, evidence=["rt"])
    qa, hml = SUPERFICIE, dict(SUPERFICIE, environment="HML")
    ev = _sin("b-%s-%s" % (A, VENTANA), viva)
    t.igual("E-49 una superficie repetida da lo mismo en los dos ordenes",
            json.dumps(_r([qa, hml], entradas, ev), sort_keys=True),
            json.dumps(_r([hml, qa], entradas, ev), sort_keys=True))
    t.igual("E-49 y la prueba de QA hace FAIL en la de QA", "FAIL", _estado([hml, qa], entradas, ev))
    nfc, nfd = (unicodedata.normalize(f, "portalé") for f in ("NFC", "NFD"))
    s1, s2 = dict(SUPERFICIE, surfaceId=nfc), dict(SUPERFICIE, surfaceId=nfd, environment="HML")
    e2 = [dict(copy.deepcopy(entradas[0]), surfaceId=nfc)]
    ev2 = [dict(x, targets=[nfc]) for x in ev]
    t.igual("E-49 gemelas en NFC dan lo mismo en los dos ordenes",
            json.dumps(_r([s1, s2], e2, ev2), sort_keys=True),
            json.dumps(_r([s2, s1], e2, ev2), sort_keys=True))


def test_e50_la_trazabilidad(t):
    """E-50 (VU3-50)."""
    caminos = {"sin senal": CHECK.evaluar({}), "pasa": _r(),
               "falla": _r(entradas=_con_evento(A, BROWSER, result="OLD_SESSION_STILL_ACTIVE")),
               "insegura": _solo_con(A, VENTANA, _prueba(environment="PRD")),
               "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True)}
    for nombre, r in caminos.items():
        t.igual("E-50 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-50 %s la clave" % nombre, "ES0902.Vu3", r["ruleKey"])
    resultado = _r()
    bloque = normativa.resolucion({"browserSessionPresent": True},
                                  evidencia={"ES0902.Vu3": resultado})["standards"]["ES0902"]
    vu3 = bloque["rules"]["Vu3"]
    t.igual("E-50 la unidad lleva Vu3", ("APPLICABLE", "PASS"), (vu3["applicability"],
                                                                vu3["result"]))
    t.igual("E-50 con sus superficies", ["portal"], vu3["surfaces"])
    t.verdadero("E-50 y su evidencia por id", "modelo" in vu3["evidence"])
    t.igual("E-50 y nada mas", ["applicability", "evidence", "result", "source", "surfaces"],
            sorted(vu3))
    falso = dict(resultado, control="otro-control")
    t.igual("E-50 un resultado ajeno no se proyecta", "UNRESOLVED",
            normativa.resolucion({"browserSessionPresent": True},
                                 evidencia={"ES0902.Vu3": falso})["standards"]["ES0902"]
            ["rules"]["Vu3"]["result"])
    for texto in ("JSESSIONID=hunter2abc", "code=hunter2abc"):
        otro = dict(resultado, surfaces=[dict(resultado["surfaces"][0], surfaceId=texto)])
        t.no_contiene("E-50 `%s` no llega a la unidad" % texto, "hunter2abc", json.dumps(
            normativa.resolucion({"browserSessionPresent": True},
                                 evidencia={"ES0902.Vu3": otro})["standards"]["ES0902"]["rules"]))
    # 🔴 Fuera de la letra del pase 1: `bin/` se instala y `controles/` no. Sin la lib la unidad no
    # se cae, y no lleva ningun id.
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = normativa.resolucion({"browserSessionPresent": True},
                                       evidencia={"ES0902.Vu3": resultado})
    finally:
        normativa._ruta_de_evidencia = original
    vu3_sin = sin_lib["standards"]["ES0902"]["rules"]["Vu3"]
    t.igual("E-50 sin la lib la unidad se arma, con el estado y sin ids",
            ("PASS", [], []), (vu3_sin["result"], vu3_sin["surfaces"], vu3_sin["evidence"]))
    secreto = dict(resultado, surfaces=[dict(resultado["surfaces"][0], surfaceId="token=hunter2abc")])
    t.no_contiene("E-50 sin secretos en la unidad", "hunter2abc", json.dumps(
        normativa.resolucion({"browserSessionPresent": True},
                             evidencia={"ES0902.Vu3": secreto})["standards"]["ES0902"]["rules"]))
