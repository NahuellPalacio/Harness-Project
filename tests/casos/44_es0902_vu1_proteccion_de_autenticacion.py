# ES0902 §6 Vu1: captcha o bloqueo de usuario, en cada pagina de autenticacion y con evidencia.
#
# Escenarios E-01 a E-44 de docs/cambios/es0902-vu1-proteccion-de-la-pagina-de-autenticacion/
# spec.md. E-nn es el VU1-nn del pedido de instalacion.
#
# 🔴 CASO tiene dos paginas que APRUEBAN -la del proveedor con bloqueo, la de la aplicacion con
# captcha- y casi todo este archivo sale de romperlas. Si dejaran de aprobar, los escenarios que
# las rompen seguirian en verde sin verificar nada: por eso E-11 a E-13 las miran en PASS.
import ast
import copy
import importlib.util
import json
import random
import sys
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

RUTA_CHECK = CONTROLES / "checks" / "authentication-abuse-protection.py"
RUTA_C1 = CONTROLES / "checks" / "oidc-keycloak-integration.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu1_proteccion")
C1 = _cargar(RUTA_C1, "vu1_c1_oidc")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu1"}
LOS_9 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
         "AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
         "AUTHENTICATION_ABUSE_PROTECTION_INACTIVE", "AUTH_ABUSE_RUNTIME_TEST_UNSAFE",
         "TEST_TARGET_UNAVAILABLE")
LOS_5 = ("CAPTCHA_ACTIVE", "LOCKOUT_ACTIVE", "BOTH_ACTIVE", "NO_ALLOWED_MECHANISM_ACTIVE",
         "PROTECTION_UNRESOLVED")
BLOQUEO = "USER_LOCKOUT_AFTER_FAILED_ATTEMPTS"

# 🔴 Las dos paginas que APRUEBAN.
PROVEEDOR = {"surfaceId": "ciudadano", "scope": "tramites", "audience": "INSTITUTIONAL",
             "environment": "QA", "currentProvider": "https://sso-qa.identidad.example/auth",
             "protocol": "OIDC", "flow": "FLUJO-A", "credentialEntryDelegated": True,
             "evidence": []}
APLICACION = {"surfaceId": "backoffice", "scope": "tramites", "audience": "INSTITUTIONAL",
              "environment": "QA", "credentialEntryDelegated": False, "evidence": []}


def _e(eid, fuente, establece, sids, valor="ACTIVE", **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece], "scope": "tramites", "surfaceIds": list(sids),
            "value": valor}
    base.update(extra)
    return base


EVIDENCIA = [
    _e("kc", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano"]),
    _e("cap", "APPLICATION_CONFIGURATION", "CAPTCHA", ["backoffice"]),
]


def _m(tipo, estado="ACTIVE", modo="PROVIDER_CONFIGURATION", **extra):
    base = {"type": tipo, "status": estado, "evidenceMode": modo}
    base.update(extra)
    return base


def _entrada(sid, dueno, mecanismos, evidencia, **extra):
    base = {"surfaceId": sid, "pageOwnership": dueno, "mechanisms": mecanismos,
            "evidence": evidencia}
    base.update(extra)
    return base


ENTRADAS = [
    _entrada("ciudadano", "IDENTITY_PROVIDER", [_m(BLOQUEO)], ["kc"]),
    _entrada("backoffice", "APPLICATION", [_m("CAPTCHA", modo="APPLICATION_CONFIGURATION")],
             ["cap"]),
]


def _caso(superficies=None, evidencia=None, entradas=None, detectadas=None):
    caso = {"inventory": {"version": "1.0",
                          "surfaces": copy.deepcopy([PROVEEDOR, APLICACION] if superficies is None
                                                    else superficies)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia),
            "protection": {"version": "1.0",
                           "surfaces": copy.deepcopy(ENTRADAS if entradas is None else entradas)}}
    if detectadas is not None:
        caso["detectedSurfaces"] = detectadas
    return caso


def _ev(*a, senal=None, autenticacion=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal, autenticacion)


def _estado(*a, **k):
    return _ev(*a, **k)["state"]


def _pag(resultado, sid):
    return [p for p in resultado["pages"] if p["surfaceId"] == sid][0]


def _sup(base, **cambios):
    s = copy.deepcopy(base)
    s.update(cambios)
    return s


def _solo_proveedor(mecanismos, evidencia, extra_entrada=None, superficie=None):
    """Una sola pagina, la del proveedor, con estos mecanismos y esta evidencia."""
    entrada = _entrada("ciudadano", "IDENTITY_PROVIDER", mecanismos,
                       [e["evidenceId"] for e in evidencia], **(extra_entrada or {}))
    return _ev([superficie or PROVEEDOR], evidencia, [entrada])


def _valores(dato):
    if isinstance(dato, dict):
        return [x for v in dato.values() for x in _valores(v)]
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


def _claves(dato):
    if isinstance(dato, dict):
        return list(dato.keys()) + [k for v in dato.values() for k in _claves(v)]
    if isinstance(dato, list):
        return [k for v in dato for k in _claves(v)]
    return []


def _arbol():
    return ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))


def _literales():
    """Las cadenas literales del modulo, sin los docstrings."""
    arbol = _arbol()
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    return {n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)} - docs


# -- La fila, que no se toca ---------------------------------------------------

def test_e01_la_clave_es_es0902_vu1(t):
    """E-01 (VU1-01)."""
    t.igual("E-01 la clave de la fila", "ES0902.Vu1", seguridad.regla("Vu1", MATRIZ)["ruleKey"])
    t.igual("E-01 la del check", "ES0902.Vu1", _ev()["ruleKey"])
    t.igual("E-01 el check dice que es de Vu1", "Vu1", _ev()["rule"])


def test_e02_la_senal_es_authentication_page_present(t):
    """E-02 (VU1-02)."""
    t.igual("E-02 la fila declara exactamente esa", ["authenticationPagePresent"],
            seguridad.regla("Vu1", MATRIZ)["applicability"]["signals"])
    t.igual("E-02 el check pregunta por esa", "authenticationPagePresent", CHECK.SENAL)
    t.igual("E-02 y la produce con ese id", "authenticationPagePresent",
            CHECK.senal(_caso())["signalId"])


def test_e03_los_ids_de_agente_policy_y_check(t):
    """E-03 (VU1-03)."""
    vu1 = seguridad.regla("Vu1", MATRIZ)
    t.igual("E-03 el agente", ["dev-security"], vu1["primaryAgents"])
    t.igual("E-03 la policy", ["authentication-abuse-protection-required"], vu1["policies"])
    t.igual("E-03 el check", ["authentication-abuse-protection"], vu1["checks"])
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("authentication-abuse-protection-required", "POLICY",
             "controles/policies/authentication-abuse-protection-required.md"),
            ("authentication-abuse-protection", "CHECK",
             "controles/checks/authentication-abuse-protection.py")):
        t.igual("E-03 %s en el registro" % cid, tipo, registro[cid]["type"])
        t.igual("E-03 %s con su archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-03 %s con la fuente de Vu1" % cid, TRAZA, registro[cid]["source"])
        t.verdadero("E-03 %s existe en disco" % cid,
                    (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    t.igual("E-03 el modulo se llama asi", "authentication-abuse-protection", CHECK.CONTROL)
    t.igual("E-03 y nombra su policy", "authentication-abuse-protection-required", CHECK.POLICY)
    t.contiene("E-03 la policy declara su id", "id: authentication-abuse-protection-required",
               (CONTROLES / "policies" / "authentication-abuse-protection-required.md")
               .read_text(encoding="utf-8"))


def test_e04_no_se_inventa_nada(t):
    """E-04 (VU1-04)."""
    registro = c_reg.cargar()
    t.igual("E-04 siguen siendo diez agentes", 10, len(registro["agents"]))
    por_id = {a["id"]: a for a in registro["agents"]}
    t.igual("E-04 las skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in por_id["dev-security"].get("skills") or []))
    t.igual("E-04 los mismos veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-04 cero reviews en la fila", [], seguridad.regla("Vu1", MATRIZ)["reviews"])
    t.igual("E-04 ninguna review nueva en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))


# -- La senal ------------------------------------------------------------------

def test_e05_la_senal_sale_del_inventario_de_c1(t):
    """E-05 (VU1-05)."""
    doc = CHECK.senal(_caso([APLICACION], entradas=[]))
    t.igual("E-05 una pagina enciende la senal", "TRUE", doc["value"])
    t.igual("E-05 y la cita por surfaceId", ["authentication-surfaces.json#backoffice"],
            [e["reference"] for e in doc["evidence"]])
    t.igual("E-05 sin evidencia de productor invalida", [], doc["issues"])
    t.igual("E-05 sin inventario no hay senal", "UNRESOLVED",
            CHECK.senal({"inventory": {"surfaces": 1}})["value"])
    t.igual("E-05 el instalado vacio tampoco", "UNRESOLVED", CHECK.senal({})["value"])
    booleanos = senales.booleanos({"authenticationPagePresent": doc})
    t.igual("E-05 pasada por senales", {"authenticationPagePresent": True}, booleanos)
    estado, _ = seguridad.resolver_regla(seguridad.regla("Vu1", MATRIZ), booleanos)
    t.igual("E-05 y enciende la fila", "APPLICABLE", estado)
    t.igual("E-05 el check usa la misma derivacion", "TRUE",
            _ev([APLICACION], entradas=[])["signalValue"])


def test_e06_la_pagina_del_proveedor_enciende(t):
    """E-06 (VU1-06)."""
    d = CHECK.derivar(_caso([PROVEEDOR]))
    t.igual("E-06 la senal", "TRUE", d["value"])
    t.igual("E-06 la pagina es del proveedor", "IDENTITY_PROVIDER", d["pages"][0]["pageOwnership"])
    t.igual("E-06 y queda con su proveedor", PROVEEDOR["currentProvider"],
            d["pages"][0]["provider"])


def test_e07_lo_no_interactivo_con_autoridad_apaga(t):
    """E-07 (VU1-07)."""
    m2m = _sup(PROVEEDOR, surfaceId="m2m", credentialEntryDelegated=None, evidence=["ni"])
    ni = _e("ni", "ARCHITECTURE_DECISION", "AUTHENTICATION_PAGE", ["m2m"], "NON_INTERACTIVE")
    caso = _caso([m2m], [ni], [])
    t.igual("E-07 la senal en FALSE", "FALSE", CHECK.senal(caso)["value"])
    t.igual("E-07 el check no aplica", "NOT_APPLICABLE", CHECK.evaluar(caso)["state"])
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT"):
        debil = dict(ni, sourceType=fuente)
        t.igual("E-07 %s no apaga" % fuente, "UNRESOLVED",
                CHECK.senal(_caso([m2m], [debil], []))["value"])
    delegada = _sup(m2m, credentialEntryDelegated=True)
    # Delegar el login ES tener pagina, la del proveedor: contra la autoridad que dice que no la
    # hay, no se elige.
    t.igual("E-07 con el login delegado no apaga", "UNRESOLVED",
            CHECK.senal(_caso([delegada], [ni], []))["value"])


def test_e08_lo_que_no_consta_no_apaga(t):
    """E-08 (VU1-08)."""
    t.igual("E-08 inventario vacio", "UNRESOLVED", CHECK.senal(_caso([], [], []))["value"])
    dudosa = _sup(PROVEEDOR, surfaceId="api", credentialEntryDelegated=None)
    t.igual("E-08 interactividad que no consta", "UNRESOLVED",
            CHECK.senal(_caso([dudosa], [], []))["value"])
    m2m = _sup(dudosa, surfaceId="m2m", evidence=["ni"])
    ni = _e("ni", "ARCHITECTURE_DECISION", "AUTHENTICATION_PAGE", ["m2m"], "NON_INTERACTIVE")
    t.igual("E-08 una superficie detectada que el inventario no tiene", "UNRESOLVED",
            CHECK.senal(_caso([m2m], [ni], [], detectadas=["legacy"]))["value"])
    r = _ev([PROVEEDOR, APLICACION, dudosa])
    t.igual("E-08 y una superficie sin resolver al lado de las paginas",
            "AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED", r["state"])
    t.igual("E-08 que la nombra", ["api"], r["coverage"]["unresolved"])


# -- Cada pagina -----------------------------------------------------------------

def test_e09_una_pagina_no_tapa_a_otra(t):
    """E-09 (VU1-09)."""
    r = _ev(entradas=[ENTRADAS[0]])
    t.igual("E-09 el agregado es el de la que falta",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-09 la que cumple sigue en PASS", "PASS", _pag(r, "ciudadano")["state"])
    t.igual("E-09 y la otra trae su estado", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _pag(r, "backoffice")["state"])


def test_e10_la_pagina_vieja_entra(t):
    """E-10 (VU1-10)."""
    vieja = _sup(APLICACION, surfaceId="login-viejo")
    r = _ev([PROVEEDOR, APLICACION, vieja])
    t.verdadero("E-10 la vieja se evalua", "login-viejo" in [p["surfaceId"] for p in r["pages"]])
    t.igual("E-10 sin proteccion impide el PASS", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            r["state"])
    t.igual("E-10 una detectada fuera del inventario deja la cobertura sin resolver",
            "AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED", _estado(detectadas=["login-viejo"]))


# -- Captcha o bloqueo -----------------------------------------------------------

def test_e11_captcha_solo(t):
    """E-11 (VU1-11)."""
    r = _ev()
    t.igual("E-11 el caso aprueba", "PASS", r["state"])
    t.igual("E-11 la pagina con captcha solo", "CAPTCHA_ACTIVE",
            _pag(r, "backoffice")["mechanismResult"])
    t.igual("E-11 sin bloqueo declarado", "NOT_DECLARED",
            _pag(r, "backoffice")["mechanisms"][BLOQUEO]["status"])


def test_e12_bloqueo_solo(t):
    """E-12 (VU1-12)."""
    r = _ev()
    t.igual("E-12 la pagina con bloqueo solo", "LOCKOUT_ACTIVE",
            _pag(r, "ciudadano")["mechanismResult"])
    t.igual("E-12 y pasa", "PASS", _pag(r, "ciudadano")["state"])


def test_e13_los_dos(t):
    """E-13 (VU1-13)."""
    ev = [EVIDENCIA[0], _e("kcc", "PROVIDER_CONFIGURATION", "CAPTCHA", ["ciudadano"])]
    r = _solo_proveedor([_m(BLOQUEO), _m("CAPTCHA")], ev)
    t.igual("E-13 los dos activos", "BOTH_ACTIVE", r["pages"][0]["mechanismResult"])
    t.igual("E-13 y pasa", "PASS", r["state"])


def test_e14_es_una_o(t):
    """E-14 (VU1-14)."""
    kcc = _e("kcc", "PROVIDER_CONFIGURATION", "CAPTCHA", ["ciudadano"])
    for nombre, mecs, ev, esperado in (
            ("bloqueo activo, captcha inactivo", [_m(BLOQUEO), _m("CAPTCHA", "INACTIVE")],
             [EVIDENCIA[0]], "LOCKOUT_ACTIVE"),
            ("bloqueo activo, captcha sin resolver", [_m(BLOQUEO), _m("CAPTCHA", "UNRESOLVED")],
             [EVIDENCIA[0]], "LOCKOUT_ACTIVE"),
            ("captcha activo, bloqueo inactivo", [_m("CAPTCHA"), _m(BLOQUEO, "INACTIVE")],
             [kcc], "CAPTCHA_ACTIVE"),
            ("captcha activo, bloqueo sin declarar", [_m("CAPTCHA")], [kcc], "CAPTCHA_ACTIVE")):
        r = _solo_proveedor(mecs, ev)
        t.igual("E-14 %s" % nombre, esperado, r["pages"][0]["mechanismResult"])
        t.igual("E-14 %s pasa" % nombre, "PASS", r["state"])


def test_e15_ninguno_activo_es_fail(t):
    """E-15 (VU1-15)."""
    r = _solo_proveedor([_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], [])
    t.igual("E-15 FAIL", "FAIL", r["state"])
    t.igual("E-15 la pagina", "NO_ALLOWED_MECHANISM_ACTIVE", r["pages"][0]["mechanismResult"])
    t.contiene("E-15 con el estado de inactiva", "AUTHENTICATION_ABUSE_PROTECTION_INACTIVE",
               r["states"])
    t.igual("E-15 por evidencia inactiva tambien", "FAIL", _solo_proveedor(
        [], [_e("i1", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano"], "INACTIVE"),
             _e("i2", "PROVIDER_CONFIGURATION", "CAPTCHA", ["ciudadano"], "INACTIVE")])["state"])
    uno = _solo_proveedor([_m(BLOQUEO, "INACTIVE")], [])
    t.igual("E-15 uno inactivo y el otro sin declarar no es FAIL",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", uno["state"])
    # 🔴 El pase 2 del refutador: los dos declarados INACTIVE contra una evidencia legible que
    # dice ACTIVE no es FAIL. El registro no le gana a la evidencia, ni al reves.
    r = _solo_proveedor([_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], [EVIDENCIA[0]])
    t.igual("E-15 declarado inactivo contra evidencia activa", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            r["state"])


def test_e16_la_capacidad_del_proveedor_no_aprueba(t):
    """E-16 (VU1-16)."""
    for nombre, e in (
            ("PROVIDER_CAPABILITY", _e("kc", "PROVIDER_CAPABILITY", BLOQUEO, ["ciudadano"])),
            ("configuracion con SUPPORTED",
             _e("kc", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano"], "SUPPORTED"))):
        r = _solo_proveedor([_m(BLOQUEO)], [e])
        t.igual("E-16 %s" % nombre, "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
        t.igual("E-16 %s se informa como capacidad" % nombre, ["kc"],
                r["pages"][0]["capabilityClaims"])
    r = _solo_proveedor([_m(BLOQUEO, modo="PROVIDER_CAPABILITY")],
                        [_e("kc", "PROVIDER_CAPABILITY", BLOQUEO, ["ciudadano"])])
    t.verdadero("E-16 y el modo PROVIDER_CAPABILITY ni siquiera valida", r["state"] != "PASS")


def test_e17_la_capacidad_de_libreria_no_aprueba(t):
    """E-17 (VU1-17)."""
    for fuente in ("LIBRARY_CAPABILITY", "FRAMEWORK_CAPABILITY", "REPOSITORY_DEPENDENCY"):
        r = _solo_proveedor([_m("CAPTCHA")], [_e("lib", fuente, "CAPTCHA", ["ciudadano"])])
        t.igual("E-17 %s" % fuente, "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])


# -- Otros controles no son Vu1 --------------------------------------------------

def _solo_sustituto(nombre):
    e = _e("sus", "PROVIDER_CONFIGURATION", nombre, ["ciudadano"])
    return _solo_proveedor([], [e])


def test_e18_waf(t):
    """E-18 (VU1-18)."""
    r = _solo_sustituto("WAF")
    t.igual("E-18 no pasa", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-18 y sale como sustituto", ["WAF"], r["pages"][0]["substitutesObserved"])


def test_e19_limite_por_ip(t):
    """E-19 (VU1-19)."""
    r = _solo_sustituto("IP_RATE_LIMITING")
    t.igual("E-19 no pasa", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-19 y se informa", ["IP_RATE_LIMITING"], r["pages"][0]["substitutesObserved"])


def test_e20_mfa(t):
    """E-20 (VU1-20)."""
    r = _solo_sustituto("MFA")
    t.igual("E-20 no pasa", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-20 y se informa", ["MFA"], r["pages"][0]["substitutesObserved"])


def test_e21_complejidad_de_contrasena(t):
    """E-21 (VU1-21)."""
    r = _solo_sustituto("PASSWORD_COMPLEXITY")
    t.igual("E-21 no pasa", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-21 y se informa", ["PASSWORD_COMPLEXITY"], r["pages"][0]["substitutesObserved"])


def test_e22_bots_y_equivalencias(t):
    """E-22 (VU1-22)."""
    for nombre in ("BOT_SCORING", "GENERIC_THROTTLING", "GATEWAY_QUOTA",
                   "DEVICE_FINGERPRINTING"):
        t.igual("E-22 %s solo" % nombre, "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
                _solo_sustituto(nombre)["state"])
    disfrazada = _e("bot", "BOT_SCORING", "CAPTCHA", ["ciudadano"])
    r = _solo_proveedor([_m("CAPTCHA", modo="PROVIDER_CONFIGURATION")], [disfrazada])
    t.igual("E-22 una evidencia de bots que dice ser captcha", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            r["state"])
    t.igual("E-22 se informa el sustituto", ["BOT_SCORING"], r["pages"][0]["substitutesObserved"])
    otro = _entrada("ciudadano", "IDENTITY_PROVIDER", [_m("WAF")], ["kc"])
    t.verdadero("E-22 el schema rechaza un mecanismo de otro tipo",
                bool(CHECK.validar_schema({"version": "1.0", "surfaces": [otro]})))
    t.igual("E-22 y el check no aprueba", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _ev([PROVEEDOR], [EVIDENCIA[0]], [otro])["state"])
    eq = _e("eq", "ASI_POLICY", "MECHANISM_EQUIVALENCE", ["ciudadano"], "BOT_SCORING")
    r = _solo_proveedor([_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")],
                        [eq, _e("sus", "PROVIDER_CONFIGURATION", "BOT_SCORING", ["ciudadano"])])
    t.igual("E-22 la equivalencia evita el FAIL pero no aprueba",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    t.igual("E-22 y se informa", ["eq"], r["pages"][0]["equivalenceClaims"])
    # 🔴 El pase 1 del refutador: una equivalencia con un control que no esta en la lista de los
    # ocho tambien es una equivalencia. No es FAIL, y tampoco aprueba.
    for fuente in ("ASI_POLICY", "GCBA_NORMATIVE"):
        otra = dict(eq, sourceType=fuente, value="ANOMALY_DETECTION")
        r = _solo_proveedor([_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], [otra])
        t.igual("E-22 equivalencia %s con un control fuera de la lista" % fuente,
                "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    debil = dict(eq, sourceType="README_STATEMENT", value="ANOMALY_DETECTION")
    t.igual("E-22 una equivalencia sin autoridad no evita el FAIL", "FAIL", _solo_proveedor(
        [_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], [debil])["state"])
    # 🔴 El pase 2 del refutador: la equivalencia se lee en todo el catalogo, como la
    # contradiccion; y `ACTIVE` o `INACTIVE` no son un control equivalente.
    entrada = _entrada("ciudadano", "IDENTITY_PROVIDER",
                       [_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], [])
    t.igual("E-22 una equivalencia con autoridad que la entrada no cita",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _ev([PROVEEDOR], [dict(eq, value="ANOMALY_DETECTION")], [entrada])["state"])
    for valor in ("ACTIVE", "INACTIVE", "CAPTCHA"):
        t.igual("E-22 una equivalencia con `%s` no es equivalencia" % valor, "FAIL",
                _solo_proveedor([_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")],
                                [dict(eq, value=valor)])["state"])


# -- Umbrales --------------------------------------------------------------------

def test_e23_no_se_inventa_una_cantidad_de_intentos(t):
    """E-23 (VU1-23)."""
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.verdadero("E-23 ningun numero salvo 0 o 1: %s" % numeros, set(numeros) <= {0, 1})
    claves = {k.lower() for k in _claves(_ev())}
    t.igual("E-23 ningun campo de intentos", [], sorted(k for k in claves if "attempt" in k and k != BLOQUEO.lower()))


def test_e24_no_se_inventa_una_duracion(t):
    """E-24 (VU1-24)."""
    texto = " ".join(_literales()).lower() + " " + json.dumps(_ev()).lower()
    for palabra in ("duration", "minute", "second", "minuto", "segundo", "duracion"):
        t.no_contiene("E-24 no aparece `%s`" % palabra, palabra, texto)


def test_e25_no_se_inventa_un_umbral_de_captcha(t):
    """E-25 (VU1-25)."""
    kcc = _e("kcc", "PROVIDER_CONFIGURATION", "CAPTCHA", ["ciudadano"])
    r = _solo_proveedor([_m("CAPTCHA")], [kcc])
    t.igual("E-25 un captcha sin details pasa", "PASS", r["state"])
    t.igual("E-25 y no aparece ningun umbral", [],
            r["pages"][0]["mechanisms"]["CAPTCHA"]["thresholds"])
    t.igual("E-25 ni un campo de umbral", [],
            sorted(k for k in _claves(r) if "threshold" in k.lower() and k != "thresholds"))


def test_e26_el_umbral_de_la_evidencia_pasa_como_no_normativo(t):
    """E-26 (VU1-26)."""
    texto = "Keycloak: bloqueo temporal tras N fallos, segun realm tramites-qa"
    r = _solo_proveedor([_m(BLOQUEO, details=texto)], [EVIDENCIA[0]])
    umbrales = r["pages"][0]["mechanisms"][BLOQUEO]["thresholds"]
    t.igual("E-26 sale tal cual", [{"text": texto, "source": "PROVIDER_CONFIGURATION",
                                    "normative": False}], umbrales)
    sin = _solo_proveedor([_m(BLOQUEO)], [EVIDENCIA[0]])
    t.igual("E-26 y no cambia el estado", sin["state"], r["state"])
    t.igual("E-26 ni el resultado de la pagina", sin["pages"][0]["mechanismResult"],
            r["pages"][0]["mechanismResult"])


# -- C1 y el proveedor -----------------------------------------------------------

def test_e27_una_evidencia_del_proveedor_sirve_a_varias_paginas(t):
    """E-27 (VU1-27)."""
    otra = _sup(PROVEEDOR, surfaceId="mobile")
    kc = _e("kc", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano", "mobile"])
    entradas = [_entrada(s, "IDENTITY_PROVIDER", [_m(BLOQUEO)], ["kc"])
                for s in ("ciudadano", "mobile")]
    r = _ev([PROVEEDOR, otra], [kc], entradas)
    t.igual("E-27 las dos pasan con la misma evidencia", "PASS", r["state"])
    t.igual("E-27 las dos citan la misma", [["kc"], ["kc"]],
            [p["mechanisms"][BLOQUEO]["evidenceUsed"] for p in r["pages"]])
    t.igual("E-27 y la pagina del proveedor sale de C1", ["IDENTITY_PROVIDER"] * 2,
            [p["pageOwnership"] for p in r["pages"]])
    # 🔴 El pase 1 del refutador: sin `credentialEntryDelegated`, el inventario no dice de quien es
    # la pagina, y el registro no lo puede decir por el.
    sin_dueno = _sup(PROVEEDOR, credentialEntryDelegated=None, evidence=["pag"])
    pag = _e("pag", "README_STATEMENT", "AUTHENTICATION_PAGE", ["ciudadano"], "INTERACTIVE")
    for dueno, ev in (("IDENTITY_PROVIDER", EVIDENCIA[0]),
                      ("APPLICATION", _e("kc", "APPLICATION_CONFIGURATION", BLOQUEO,
                                         ["ciudadano"]))):
        entrada = _entrada("ciudadano", dueno, [_m(BLOQUEO, modo=ev["sourceType"])], ["kc"])
        r = _ev([sin_dueno], [pag, ev], [entrada])
        t.igual("E-27 el registro no pone el dueno %s que el inventario no dice" % dueno,
                "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])


def test_e28_a_la_pagina_del_proveedor_no_se_le_pide_la_aplicacion(t):
    """E-28 (VU1-28)."""
    r = _solo_proveedor([_m(BLOQUEO)], [EVIDENCIA[0]])
    t.igual("E-28 pasa sin evidencia de la aplicacion", "PASS", r["state"])
    app = _e("kc", "APPLICATION_CONFIGURATION", BLOQUEO, ["ciudadano"])
    r = _solo_proveedor([_m(BLOQUEO, modo="APPLICATION_CONFIGURATION")], [app])
    t.igual("E-28 y la configuracion de la aplicacion no la sostiene",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])


def test_e29_oidc_configurado_no_es_vu1(t):
    """E-29 (VU1-29)."""
    r = _ev([PROVEEDOR], [], [])
    t.igual("E-29 OIDC con Keycloak sin evidencia no pasa",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
    oidc = _e("oidc", "OIDC_CONFIGURED", BLOQUEO, ["ciudadano"])
    t.igual("E-29 OIDC_CONFIGURED no sostiene nada",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _solo_proveedor([_m(BLOQUEO)], [oidc])["state"])
    t.contiene("E-29 el resultado conserva la frase de la fuente",
               "funcionalidad que se encuentra contenida en OpenID", r["sourceText"])


# El caso con que C1 aprueba (su E-26/E-40), para cruzarlo con Vu1.
C1_SUP = {"surfaceId": "backoffice", "scope": "tramites", "audience": "INSTITUTIONAL",
          "environment": "QA", "currentProvider": PROVEEDOR["currentProvider"],
          "intendedProvider": PROVEEDOR["currentProvider"], "protocol": "OIDC",
          "flow": "FLUJO-A", "clientIdReference": "tramites-bo", "registrationEvidence": ["reg"],
          "credentialEntryDelegated": True, "applicationRoleOwnership": "APPLICATION",
          "evidence": ["cfg", "aud", "amb", "prov", "flujo", "asi"]}


def _c1e(eid, fuente, dim, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [dim], "scope": "tramites"}
    base.update(extra)
    return base


C1_EV = [_c1e("cfg", "PROJECT_CONFIGURATION", "OIDC_PROTOCOL"),
         _c1e("aud", "PROJECT_CONTRACT", "AUDIENCE", value="INSTITUTIONAL",
              surfaceIds=["backoffice"]),
         _c1e("amb", "ENVIRONMENT_IDENTITY_CONTRACT", "ENVIRONMENT_IDENTITY", environment="QA"),
         _c1e("prov", "DGSEI_IDENTITY_REGISTRATION", "PROVIDER_AUTHORITY", environment="QA",
              value=PROVEEDOR["currentProvider"]),
         _c1e("reg", "DGSEI_IDENTITY_REGISTRATION", "CLIENT_REGISTRATION", value="tramites-bo"),
         _c1e("flujo", "ASI_POLICY", "FLOW_AUTHORITY", value="FLUJO-A"),
         _c1e("asi", "ASI_POLICY", "ASI_IDENTITY_POLICY")]
C1_D2 = {"flows": [{"flowId": "backoffice", "state": "PASS"}]}


def test_e30_c1_no_es_vu1(t):
    """E-30 (VU1-30)."""
    caso = {"inventory": {"version": "1.0", "surfaces": [C1_SUP]}, "evidence": C1_EV}
    t.igual("E-30 el caso aprueba C1", "PASS", C1.evaluar(caso, True, C1_D2)["state"])
    t.igual("E-30 y sin registro de proteccion no aprueba Vu1",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            CHECK.evaluar(dict(caso, protection={"version": "1.0", "surfaces": []}))["state"])
    ev = {"controlResults": {c: {"result": "PASS", "evidence": ["c1"]}
                             for c in seguridad.regla("C1", MATRIZ)["policies"]
                             + seguridad.regla("C1", MATRIZ)["checks"]}}
    t.igual("E-30 los controles de C1 en PASS no ponen a Vu1 en COMPLIANT", "UNRESOLVED",
            seguridad.resultado("Vu1", ev, {"authenticationPagePresent": True}, MATRIZ)["result"])
    import inspect
    t.igual("E-30 evaluar no recibe un resultado de C1",
            ["caso", "senal", "autenticacion", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    import re
    nombra_c1 = re.compile(r"(?i)(?<![a-z0-9])c1(?![0-9])|keycloak|oidc-")
    t.igual("E-30 el unico literal que nombra a C1 es el archivo del cargador",
            ["oidc-keycloak-integration.py"],
            sorted(l for l in _literales() if nombra_c1.search(l)))


def test_e31_vu1_no_es_c1(t):
    """E-31 (VU1-31)."""
    ev = {"controlResults": {c: {"result": "PASS", "evidence": ["vu1"]}
                             for c in ("authentication-abuse-protection",
                                       "authentication-abuse-protection-required")}}
    t.igual("E-31 Vu1 con sus dos controles cumple", "COMPLIANT",
            seguridad.resultado("Vu1", ev, {"authenticationPagePresent": True}, MATRIZ)["result"])
    t.igual("E-31 y C1 sigue sin cumplir", "UNRESOLVED",
            seguridad.resultado("C1", ev, {"authenticationPresent": True}, MATRIZ)["result"])
    caso = _caso()
    t.igual("E-31 el caso aprueba Vu1", "PASS", CHECK.evaluar(caso)["state"])
    t.verdadero("E-31 y no aprueba C1", C1.evaluar(caso, True, None)["state"] != "PASS")


# -- La prueba en ejecucion ------------------------------------------------------

PRUEBA_OK = {"environment": "QA", "dedicatedTestIdentityRef": "vault://qa/vu1-test-user",
             "authorized": True, "result": "CONFIRMED"}
EV_PRUEBA = _e("rt", "AUTHORIZED_RUNTIME_TEST", BLOQUEO, ["ciudadano"], outcome="CONFIRMED")


def _con_prueba(prueba, evidencia=None):
    extra = {} if prueba is _SIN else {"runtimeTest": prueba}
    return _solo_proveedor([_m(BLOQUEO, modo="AUTHORIZED_RUNTIME_TEST")],
                           [evidencia or EV_PRUEBA], extra)


_SIN = object()


def test_e32_en_produccion_no(t):
    """E-32 (VU1-32)."""
    r = _con_prueba(dict(PRUEBA_OK, environment="PRD"))
    t.igual("E-32 no cuenta", "AUTH_ABUSE_RUNTIME_TEST_UNSAFE", r["state"])
    t.contiene("E-32 y dice por que", "PRODUCTION", r["pages"][0]["runtimeTest"]["unsafe"])
    t.igual("E-32 no se ejecuto nada", False, r["pages"][0]["runtimeTest"]["executed"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    llamadas = sorted({"%s.%s" % (n.value.id, n.attr) for n in ast.walk(_arbol())
                       if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                       and n.value.id == "os"})
    t.igual("E-32 de `os` solo usa rutas", ["os.path"], llamadas)
    t.igual("E-32 el modulo no importa nada con que ejecutarla", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess",
                                 "ssl", "asyncio", "httpx", "multiprocessing"}))


def test_e33_sin_identidad_dedicada_no(t):
    """E-33 (VU1-33)."""
    for nombre, prueba in (("sin la clave", {k: v for k, v in PRUEBA_OK.items()
                                             if k != "dedicatedTestIdentityRef"}),
                           ("vacia", dict(PRUEBA_OK, dedicatedTestIdentityRef="  "))):
        r = _con_prueba(prueba)
        t.igual("E-33 %s" % nombre, "AUTH_ABUSE_RUNTIME_TEST_UNSAFE", r["state"])
        t.contiene("E-33 %s dice por que" % nombre, "NO_DEDICATED_TEST_IDENTITY",
                   r["pages"][0]["runtimeTest"]["unsafe"])


def test_e34_la_prueba_autorizada_sostiene(t):
    """E-34 (VU1-34)."""
    r = _con_prueba(PRUEBA_OK)
    t.igual("E-34 pasa", "PASS", r["state"])
    t.igual("E-34 con la prueba", ["rt"], r["pages"][0]["mechanisms"][BLOQUEO]["evidenceUsed"])


def test_e35_las_cuatro_condiciones_inseguras(t):
    """E-35 (VU1-35)."""
    for nombre, prueba, motivo in (
            ("sin autorizacion", dict(PRUEBA_OK, authorized=None), "NOT_AUTHORIZED"),
            ("sin ambiente", dict(PRUEBA_OK, environment=None), "ENVIRONMENT_UNRESOLVED"),
            ("en otro ambiente", dict(PRUEBA_OK, environment="DEV"), "ENVIRONMENT_MISMATCH"),
            ("sin runtimeTest", _SIN, "NO_RUNTIME_TEST_RECORD")):
        r = _con_prueba(prueba)
        t.igual("E-35 %s" % nombre, "AUTH_ABUSE_RUNTIME_TEST_UNSAFE", r["state"])
        t.contiene("E-35 %s dice por que" % nombre, motivo, r["pages"][0]["runtimeTest"]["unsafe"])


def test_e36_no_poder_probar_no_es_fail(t):
    """E-36 (VU1-36)."""
    t.igual("E-36 insegura", "AUTH_ABUSE_RUNTIME_TEST_UNSAFE",
            _con_prueba(dict(PRUEBA_OK, environment="PRD"))["state"])
    t.igual("E-36 sin objetivo, por la prueba", "TEST_TARGET_UNAVAILABLE",
            _con_prueba(dict(PRUEBA_OK, result="UNAVAILABLE"))["state"])
    t.igual("E-36 sin objetivo, por la evidencia", "TEST_TARGET_UNAVAILABLE",
            _con_prueba(PRUEBA_OK, dict(EV_PRUEBA, outcome="UNAVAILABLE"))["state"])
    # 🔴 El pase 1 del refutador: una prueba que dice que el mecanismo esta INACTIVO pasa por la
    # misma compuerta que una que dice que esta activo. Insegura o sin objetivo no hace FAIL.
    inactiva = dict(EV_PRUEBA, value="INACTIVE")
    for nombre, prueba, esperado in (
            ("en PRD", dict(PRUEBA_OK, environment="PRD"), "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("sin autorizacion", dict(PRUEBA_OK, authorized=False),
             "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("sin ambiente", dict(PRUEBA_OK, environment=None), "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("en otro ambiente", dict(PRUEBA_OK, environment="HML"),
             "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("sin identidad", dict(PRUEBA_OK, dedicatedTestIdentityRef=None),
             "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("sin runtimeTest", None, "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"),
            ("sin objetivo", dict(PRUEBA_OK, result="UNAVAILABLE"), "TEST_TARGET_UNAVAILABLE")):
        extra = {} if prueba is None else {"runtimeTest": prueba}
        r = _solo_proveedor([_m("CAPTCHA", "INACTIVE")], [inactiva], extra)
        t.igual("E-36 la prueba que dice inactivo, %s" % nombre, esperado, r["state"])
    r = _solo_proveedor([_m("CAPTCHA", "INACTIVE")],
                        [dict(inactiva, outcome="UNAVAILABLE")], {"runtimeTest": PRUEBA_OK})
    t.igual("E-36 y con la evidencia sin objetivo", "TEST_TARGET_UNAVAILABLE", r["state"])
    otra = _e("i", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano"], "INACTIVE",
              outcome="UNAVAILABLE")
    t.verdadero("E-36 una configuracion inactiva que no se pudo confirmar tampoco hace FAIL",
                _solo_proveedor([_m("CAPTCHA", "INACTIVE")], [otra])["state"] != "FAIL")
    t.igual("E-36 la prueba segura que dice inactivo si cuenta", "FAIL", _solo_proveedor(
        [_m("CAPTCHA", "INACTIVE")], [inactiva], {"runtimeTest": PRUEBA_OK})["state"])


# -- El registro -----------------------------------------------------------------

def test_e37_el_registro_se_instala_vacio(t):
    """E-37 (VU1-37)."""
    instalado = json.loads((REGLAS / "authentication-abuse-protection.json")
                           .read_text(encoding="utf-8"))
    t.igual("E-37 vacio", [], instalado["surfaces"])
    t.igual("E-37 valida", [], CHECK.validar_schema(instalado))
    t.igual("E-37 lo carga el check", [], CHECK.cargar()["surfaces"])
    caso = _caso([PROVEEDOR])
    del caso["protection"]
    t.igual("E-37 con una pagina y el registro instalado, sin resolver",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", CHECK.evaluar(caso)["state"])
    entrada = ENTRADAS[0]
    for nombre, doc in (
            ("arriba", {"version": "1.0", "surfaces": [], "extra": 1}),
            ("en la superficie", {"version": "1.0", "surfaces": [dict(entrada, extra=1)]}),
            ("en el mecanismo", {"version": "1.0", "surfaces": [
                dict(entrada, mechanisms=[_m(BLOQUEO, extra=1)])]}),
            ("en la prueba", {"version": "1.0", "surfaces": [
                dict(entrada, runtimeTest=dict(PRUEBA_OK, extra=1))]})):
        t.verdadero("E-37 el schema rechaza una clave de mas %s" % nombre,
                    bool(CHECK.validar_schema(doc)))


def test_e38_la_evidencia_se_ata_por_surface_id(t):
    """E-38 (VU1-38)."""
    ajena = _entrada("fantasma", "APPLICATION", [], [])
    r = _ev(entradas=ENTRADAS + [ajena])
    t.igual("E-38 una entrada para una superficie que C1 no tiene",
            "AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED", r["state"])
    t.igual("E-38 que la nombra", ["fantasma"], r["coverage"]["unknownProtectionEntries"])
    sin_nombre = [dict(EVIDENCIA[0], surfaceIds=["otra"]), EVIDENCIA[1]]
    t.igual("E-38 una evidencia que no nombra la pagina no la sostiene",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", _estado(evidencia=sin_nombre))
    # 🔴 El pase 1 del refutador: con la senal en FALSE el registro tambien se lee. Una entrada
    # que dice "aca hay una pagina" no se puede apagar.
    m2m = _sup(PROVEEDOR, surfaceId="m2m", credentialEntryDelegated=None, evidence=["ni"])
    ni = _e("ni", "ARCHITECTURE_DECISION", "AUTHENTICATION_PAGE", ["m2m"], "NON_INTERACTIVE")
    for nombre, caso in (
            ("junto a una superficie no interactiva", _caso([m2m], [ni], [ajena])),
            ("para la superficie no interactiva",
             _caso([m2m], [ni], [_entrada("m2m", "APPLICATION", [], [])])),
            ("con el inventario vacio", _caso([], [], [ajena]))):
        t.igual("E-38 una entrada %s no deja apagar la senal" % nombre, "UNRESOLVED",
                CHECK.senal(caso, autenticacion=False)["value"])
        t.verdadero("E-38 y el check no dice NOT_APPLICABLE %s" % nombre,
                    CHECK.evaluar(caso, autenticacion=False)["state"] != "NOT_APPLICABLE")
    t.igual("E-38 un registro ilegible tampoco deja apagarla", "UNRESOLVED",
            CHECK.senal(dict(_caso([m2m], [ni], []), protection={"surfaces": 1}))["value"])
    doble = ENTRADAS + [copy.deepcopy(ENTRADAS[0])]
    r = _ev(entradas=doble)
    t.igual("E-38 dos entradas para la misma pagina", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _pag(r, "ciudadano")["state"])
    t.igual("E-38 en cualquier orden", json.dumps(r, sort_keys=True),
            json.dumps(_ev(entradas=list(reversed(doble))), sort_keys=True))


def test_e39_ningun_secreto(t):
    """E-39 (VU1-39)."""
    for clave in ("password", "token"):
        doc = {"version": "1.0", "surfaces": [dict(ENTRADAS[0], **{clave: "x"})]}
        t.verdadero("E-39 el schema rechaza `%s`" % clave, bool(CHECK.validar_schema(doc)))
    for nombre, texto in (("asignacion", "password=hunter22-vu1"),
                          ("bearer", "Bearer abcdefghijklmnopqrstu"),
                          ("jwt", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ2dTEifQ.firma"),
                          ("pem", "-----BEGIN RSA PRIVATE KEY-----")):
        entradas = [_entrada("ciudadano", "IDENTITY_PROVIDER", [_m(BLOQUEO, details=texto)],
                             ["kc"]), ENTRADAS[1]]
        r = _ev(entradas=entradas)
        t.igual("E-39 %s: el registro no se lee" % nombre,
                "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
        t.no_contiene("E-39 %s: y no se repite" % nombre, texto, json.dumps(r))
    identidad = [_entrada("ciudadano", "IDENTITY_PROVIDER", [_m(BLOQUEO)], ["kc"],
                          runtimeTest=dict(PRUEBA_OK, dedicatedTestIdentityRef="token: s3cr3t")),
                 ENTRADAS[1]]
    t.no_contiene("E-39 tampoco en la referencia de la identidad", "s3cr3t",
                  json.dumps(_ev(entradas=identidad)))
    # 🔴 El pase 1 del refutador: la forma, no la palabra suelta.
    for texto in ("DB_PASSWORD=hunter2", "api_token: abc123", "mysecret: abc", "pwd=hunter2",
                  "Authorization: Basic dXNlcjpwYXNz", "https://u:hunter2@sso.example"):
        entradas = [_entrada("ciudadano", "IDENTITY_PROVIDER", [_m(BLOQUEO, details=texto)],
                             ["kc"]), ENTRADAS[1]]
        r = _ev(entradas=entradas)
        t.igual("E-39 `%s` deja el registro sin leer" % texto,
                "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", r["state"])
        t.no_contiene("E-39 y `%s` no se repite" % texto, texto, json.dumps(r))
    enum = [_entrada("ciudadano", "hunter2xyz", [_m(BLOQUEO)], ["kc"]), ENTRADAS[1]]
    t.no_contiene("E-39 un error de schema no repite el valor", "hunter2xyz",
                  json.dumps(_ev(entradas=enum)))
    con_url = _sup(PROVEEDOR, currentProvider="https://u:password=hunter2@sso.example")
    t.no_contiene("E-39 un secreto del inventario no se repite", "hunter2",
                  json.dumps(_ev([con_url, APLICACION])))
    # 🔴 El pase 2 del refutador: la regla es de SALIDA y vale para todo campo, venga de donde
    # venga. Un surfaceId, un id de evidencia, un `detectedSurfaces`, un error de schema del
    # inventario, una clave del registro.
    secreto = "token=hunter2abc"
    sid = _sup(APLICACION, surfaceId=secreto)
    for nombre, r in (
            ("un surfaceId", _ev([PROVEEDOR, sid])),
            ("un surfaceId, en la senal", CHECK.senal(_caso([PROVEEDOR, sid]))),
            ("un error de schema del inventario",
             CHECK.evaluar(_caso([_sup(PROVEEDOR, audience="password=hunter2abc")]), True)),
            ("un id citado en el inventario",
             _ev([_sup(PROVEEDOR, evidence=[secreto])],
                 EVIDENCIA + [_e(secreto, "README_STATEMENT", "AUTHENTICATION_PAGE",
                                 ["ciudadano"], "INTERACTIVE")])),
            ("un detectedSurfaces", _ev(detectadas=[secreto])),
            ("un id de evidencia que contradice",
             _ev(evidencia=EVIDENCIA + [_e(secreto, "PROVIDER_CONFIGURATION", BLOQUEO,
                                           ["ciudadano"], "INACTIVE")])),
            ("una clave del registro", _ev(entradas=[dict(ENTRADAS[0], **{
                "db_password=hunter2abc": {"x": "Bearer abcdefghijklmnop"}}), ENTRADAS[1]]))):
        t.no_contiene("E-39 %s no sale" % nombre, "hunter2abc", json.dumps(r))
    # Y la forma no cierra textos legitimos: un umbral o una referencia a un gestor de secretos.
    for texto in ("Keycloak passwordPolicy: length(12)", "tokenLifespan=300", "Bypass: ninguno",
                  "arn:aws:secretsmanager:us-east-1:123:secret:vu1-qa"):
        r = _solo_proveedor([_m(BLOQUEO, details=texto)], [EVIDENCIA[0]])
        t.igual("E-39 `%s` no es un secreto" % texto, "PASS", r["state"])


# -- El agregado -----------------------------------------------------------------

def test_e40_todas_tienen_que_pasar(t):
    """E-40 (VU1-40)."""
    r = _ev()
    t.igual("E-40 las dos pasan", ["PASS", "PASS"], [p["state"] for p in r["pages"]])
    t.igual("E-40 y el agregado es PASS", "PASS", r["state"])
    t.igual("E-40 sin una, no", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _estado(entradas=[ENTRADAS[1]]))


def test_e41_una_en_fail_es_fail(t):
    """E-41 (VU1-41)."""
    inactiva = _entrada("backoffice", "APPLICATION",
                        [_m("CAPTCHA", "INACTIVE"), _m(BLOQUEO, "INACTIVE")], [])
    # Sin la evidencia de captcha activo del backoffice: con ella, el INACTIVE declarado queda
    # contradicho y no se elige (E-15).
    r = _ev(evidencia=[EVIDENCIA[0]], entradas=[ENTRADAS[0], inactiva])
    t.igual("E-41 FAIL", "FAIL", r["state"])
    t.igual("E-41 aunque la otra pase", "PASS", _pag(r, "ciudadano")["state"])


def test_e42_una_sin_resolver_impide_el_pass(t):
    """E-42 (VU1-42)."""
    sin = _entrada("backoffice", "APPLICATION",
                   [_m("CAPTCHA", "UNRESOLVED", "APPLICATION_CONFIGURATION")], ["cap"])
    t.igual("E-42 una sin resolver", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _estado(entradas=[ENTRADAS[0], sin]))
    ilegible = _entrada("ciudadano", "IDENTITY_PROVIDER", [_m(BLOQUEO)], ["kc", "no-existe"])
    r = _ev(entradas=[ilegible, ENTRADAS[1]])
    t.igual("E-42 una evidencia ilegible citada", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _pag(r, "ciudadano")["state"])
    t.contiene("E-42 y lo dice", "no-existe", " | ".join(_pag(r, "ciudadano")["issues"]))
    # 🔴 Fuera de la letra del pase 1: quien arma el registro no elige que contradiccion se lee.
    no_citada = _e("kc-off", "PROVIDER_CONFIGURATION", BLOQUEO, ["ciudadano"], "INACTIVE")
    r = _ev(evidencia=EVIDENCIA + [no_citada])
    t.igual("E-42 una contradiccion que la entrada no cita igual se lee",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", _pag(r, "ciudadano")["state"])
    # 🔴 El pase 2 del refutador: lo ilegible que nombra la pagina impide el PASS aunque nadie lo
    # cite -repetido, o mal formado-.
    for nombre, extra in (("repetida", [no_citada, copy.deepcopy(no_citada)]),
                          ("mal formada", [dict(no_citada, outcome=["CONFIRMED"])]),
                          ("con surfaceIds como texto", [dict(no_citada, surfaceIds="ciudadano")])):
        r = _ev(evidencia=EVIDENCIA + extra)
        t.igual("E-42 una contradiccion %s y no citada" % nombre,
                "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", _pag(r, "ciudadano")["state"])
    # Pero lo no citado nunca hace FAIL: no se lee con la prueba de esta entrada.
    ajena = dict(EV_PRUEBA, evidenceId="rt-ajena", value="INACTIVE")
    entrada = _entrada("ciudadano", "IDENTITY_PROVIDER", [_m("CAPTCHA", "INACTIVE")], [],
                       runtimeTest=PRUEBA_OK)
    t.igual("E-42 una prueba inactiva que la entrada no cita no hace FAIL",
            "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED",
            _ev([PROVEEDOR], [ajena], [entrada])["state"])


def test_e43_la_misma_evidencia_el_mismo_resultado(t):
    """E-43 (VU1-43)."""
    vieja = _sup(APLICACION, surfaceId="login-viejo")
    sups = [PROVEEDOR, APLICACION, vieja]
    ents = ENTRADAS + [_entrada("login-viejo", "APPLICATION",
                                [_m("CAPTCHA", "INACTIVE"), _m(BLOQUEO, "UNRESOLVED")], [])]
    base = json.dumps(_ev(sups, entradas=ents), sort_keys=True)
    t.igual("E-43 dos corridas iguales", base, json.dumps(_ev(sups, entradas=ents),
                                                          sort_keys=True))
    azar = random.Random(43)
    for vuelta in range(5):
        s, e, n = copy.deepcopy(sups), copy.deepcopy(EVIDENCIA), copy.deepcopy(ents)
        azar.shuffle(s)
        azar.shuffle(e)
        azar.shuffle(n)
        for x in n:
            azar.shuffle(x["mechanisms"])
        t.igual("E-43 desordenado %d" % vuelta, base,
                json.dumps(_ev(s, e, n), sort_keys=True))
    repetida = dict(EVIDENCIA[0], sourceType="README_STATEMENT")
    a = json.dumps(_ev(evidencia=EVIDENCIA + [repetida]), sort_keys=True)
    b = json.dumps(_ev(evidencia=[repetida] + EVIDENCIA), sort_keys=True)
    t.igual("E-43 un id repetido da lo mismo en los dos ordenes", a, b)
    t.igual("E-43 y no cuenta", "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED", json.loads(a)["state"])
    t.igual("E-43 los nueve estados, con ese nombre", sorted(LOS_9), sorted(CHECK.ESTADOS))
    t.igual("E-43 los cinco resultados de pagina", sorted(LOS_5),
            sorted(CHECK.RESULTADOS_DE_PAGINA))


def test_e44_la_trazabilidad_viaja(t):
    """E-44 (VU1-44)."""
    caminos = {
        "sin senal": CHECK.evaluar({}), "no aplica": CHECK.evaluar({}, autenticacion=False),
        "pasa": _ev(), "falla": _solo_proveedor(
            [_m(BLOQUEO, "INACTIVE"), _m("CAPTCHA", "INACTIVE")], []),
        "cobertura": _ev(detectadas=["otra"]),
        "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True),
        "registro invalido": CHECK.evaluar(dict(_caso(), protection={"surfaces": 1})),
        "insegura": _con_prueba(dict(PRUEBA_OK, environment="PRD")),
    }
    for nombre, r in caminos.items():
        t.igual("E-44 %s conserva la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-44 %s conserva la clave" % nombre, "ES0902.Vu1", r["ruleKey"])
    bloque = normativa.resolucion({"authenticationPagePresent": True})["standards"]["ES0902"]
    t.igual("E-44 la unidad de trabajo cita ES0902 6.2", ("ES0902", "6.2"),
            (bloque["standard"]["id"], bloque["standard"]["version"]))
    t.verdadero("E-44 con Vu1 aplicable", "Vu1" in bloque["applicableRules"])
    t.verdadero("E-44 y su check declarado",
                "authentication-abuse-protection" in bloque["declaredChecks"])
    t.igual("E-44 la trazabilidad de la regla", "ES0902.Vu1",
            seguridad.trazabilidad("Vu1", MATRIZ)["ruleKey"])
