# ES0902 §3 C1: OpenID Connect con el Keycloak de DGSEI, por superficie y con evidencia.
#
# Escenarios E-01 a E-50 de docs/cambios/es0902-c1-openid-connect-keycloak/spec.md. E-nn es el
# C1-nn del pedido de instalacion.
#
# 🔴 Lo que se verifica es que C1 NO se pueda poner en verde barato: la libreria por el protocolo,
# el hostname por la autoridad, el `client_id` por el registro, el default por el flujo y la
# aplicacion por la superficie. Y que una superficie ciudadana no se resuelva sola de ningun lado.
#
# 🔴 SUPERFICIE es el caso que APRUEBA, y casi todo este archivo sale de romperlo. Si dejara de
# aprobar, los escenarios que lo rompen seguirian en verde sin verificar nada: por eso E-26 y E-40
# lo miran en PASS.
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
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import cruzada                        # noqa: E402
from orquestacion import normativa                      # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import matriz as c_matriz             # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "oidc-keycloak-integration.py"
RUTA_D2 = CONTROLES / "checks" / "authentication-delegation.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "c1_oidc")
D2 = _cargar(RUTA_D2, "c1_d2_delegacion")
MATRIZ = seguridad.cargar()
MAPA = cruzada.cargar()
REGISTRO = c_controles.cargar()

# Los ids, escritos a mano. Es la unica forma de que renombrarlos rompa algo.
LAS_3_POLICIES = ("openid-connect-authentication-required", "dgsei-keycloak-provider-required",
                  "credential-entry-delegation-required")
LOS_2_CHECKS = ("oidc-keycloak-integration", "authentication-delegation")
LOS_3_NUEVOS = ("openid-connect-authentication-required", "dgsei-keycloak-provider-required",
                "oidc-keycloak-integration")

# Los diecisiete estados, clavados por literal.
LOS_17 = ("PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", "OIDC_PROTOCOL_EVIDENCE_UNRESOLVED",
          "KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED", "OIDC_CLIENT_REGISTRATION_UNRESOLVED",
          "OIDC_FLOW_CONTEXT_UNRESOLVED", "OIDC_FLOW_AUTHORITY_UNRESOLVED",
          "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED", "LEGACY_OPENID_PROVIDER_DETECTED",
          "OIDC_MIGRATION_REQUIRED", "ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED",
          "CROSS_STANDARD_INTERPRETATION_REQUIRED", "TEST_TARGET_UNAVAILABLE")

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": "C1"}

ANTERIOR = "https://oauth2-server.apps.buenosaires.gob.ar/"
PROVEEDOR = "https://sso-qa.identidad.example/auth"

# 🔴 La superficie que APRUEBA. Un backoffice institucional en QA.
SUPERFICIE = {
    "surfaceId": "backoffice", "scope": "tramites", "audience": "INSTITUTIONAL",
    "environment": "QA", "currentProvider": PROVEEDOR, "intendedProvider": PROVEEDOR,
    "protocol": "OIDC", "flow": "FLUJO-A", "clientIdReference": "tramites-bo",
    "registrationEvidence": ["reg"], "credentialEntryDelegated": True,
    "applicationRoleOwnership": "APPLICATION",
    "evidence": ["cfg", "aud", "amb", "prov", "flujo", "asi"],
}


def _e(eid, fuente, dimension, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [dimension], "scope": "tramites"}
    base.update(extra)
    return base


EVIDENCIA = [
    _e("cfg", "PROJECT_CONFIGURATION", "OIDC_PROTOCOL"),
    # La audiencia nombra las superficies que resuelve. Sin `surfaceIds` no resuelve ninguna.
    _e("aud", "PROJECT_CONTRACT", "AUDIENCE", value="INSTITUTIONAL",
       surfaceIds=["backoffice", "mobile", "api"]),
    _e("amb", "ENVIRONMENT_IDENTITY_CONTRACT", "ENVIRONMENT_IDENTITY", environment="QA"),
    _e("prov", "DGSEI_IDENTITY_REGISTRATION", "PROVIDER_AUTHORITY", environment="QA",
       value=PROVEEDOR),
    _e("reg", "DGSEI_IDENTITY_REGISTRATION", "CLIENT_REGISTRATION", value="tramites-bo"),
    _e("flujo", "ASI_POLICY", "FLOW_AUTHORITY", value="FLUJO-A"),
    _e("asi", "ASI_POLICY", "ASI_IDENTITY_POLICY"),
]


def _d2(flujos=None):
    """El resultado REAL de D2, corrido una vez. Por defecto, el backoffice delegado a DGSEI."""
    caso = {"application": {"id": "tramites", "environment": "QA"},
            "authenticationFlows": flujos if flujos is not None else [
                {"flowId": "backoffice", "audience": "INSTITUTIONAL",
                 "credentialEntry": "DELEGATED", "provider": "DGSEI_OPENID_KEYCLOAK",
                 "evidenceRefs": ["d2-cfg"]}],
            "evidence": [{"evidenceId": "d2-cfg", "sourceType": "PROJECT_CONFIGURATION",
                          "reference": "application-qa.yml"}]}
    return D2.evaluar(caso, True)


DELEGACION = _d2()
_POR_DEFECTO = object()


def _sup(**cambios):
    s = copy.deepcopy(SUPERFICIE)
    s.update(cambios)
    return s


def _evid(*cambios, sin=(), mas=()):
    """La evidencia base, con reemplazos por id, sacando ids, y agregando."""
    salida = []
    por_id = {c["evidenceId"]: c for c in cambios}
    for e in EVIDENCIA:
        if e["evidenceId"] in sin:
            continue
        salida.append(copy.deepcopy(por_id.get(e["evidenceId"], e)))
    return salida + [copy.deepcopy(m) for m in mas]


def _ev(superficies=None, evidencia=None, delegacion=_POR_DEFECTO, senal=True, detectadas=None):
    caso = {"inventory": {"version": "1.0",
                          "surfaces": copy.deepcopy([SUPERFICIE] if superficies is None
                                                    else superficies)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if detectadas is not None:
        caso["detectedSurfaces"] = detectadas
    return CHECK.evaluar(caso, senal, DELEGACION if delegacion is _POR_DEFECTO else delegacion)


def _estado(*a, **k):
    return _ev(*a, **k)["state"]


def _superficie(resultado, sid):
    return [s for s in resultado["surfaces"] if s["surfaceId"] == sid][0]


def _valores(dato):
    if isinstance(dato, dict):
        return [x for v in dato.values() for x in _valores(v)]
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


def _literales(ruta):
    """Las cadenas literales del modulo, sin los docstrings."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    return {n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)} - docs


def _importados(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    salida = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            salida.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            salida.add(nodo.module or "")
            salida.update(a.name for a in nodo.names)
    return salida


# -- La fila, que no se toca ---------------------------------------------------

def test_e01_la_clave_es_es0902_c1(t):
    """E-01 (C1-01)."""
    c1 = seguridad.regla("C1", MATRIZ)
    t.igual("E-01 la clave de la fila", "ES0902.C1", c1["ruleKey"])
    t.igual("E-01 y la del check", "ES0902.C1", _ev()["ruleKey"])
    t.igual("E-01 el check dice que es de C1", "C1", _ev()["rule"])


def test_e02_authentication_present_se_reusa(t):
    """E-02 (C1-02) — una sola senal, la de D2, y ninguna otra de autenticacion."""
    c1 = seguridad.regla("C1", MATRIZ)
    t.igual("E-02 C1 declara solo authenticationPresent", ["authenticationPresent"],
            c1["applicability"]["signals"])
    d2 = c_matriz.regla("D2")
    t.igual("E-02 D2 declara la misma", ["authenticationPresent"],
            d2["applicability"]["signals"])
    t.igual("E-02 el check pregunta por esa", "authenticationPresent", CHECK.SENAL)
    todas = seguridad.senales_declaradas(MATRIZ) | {
        s for r in c_matriz.cargar()["rules"]
        for s in (r.get("applicability") or {}).get("signals") or []}
    # Las tres que ya habia: las otras dos son de Vu y dicen otra cosa -una pagina de login, una
    # interfaz publica sin autenticar-. C1 no agrega ninguna.
    de_autenticacion = sorted(s for s in todas
                              if "auth" in s.lower() or "oidc" in s.lower()
                              or "login" in s.lower())
    t.igual("E-02 ninguna senal de autenticacion nueva",
            ["authenticationPagePresent", "authenticationPresent",
             "unauthenticatedPublicInterfacePresent"], de_autenticacion)


def test_e03_sin_la_senal_queda_sin_resolver(t):
    """E-03 (C1-03)."""
    estado, faltan = seguridad.resolver_regla(seguridad.regla("C1", MATRIZ), {})
    t.igual("E-03 la matriz", "APPLICABILITY_UNRESOLVED", estado)
    t.igual("E-03 dice cual falta", ["authenticationPresent"], faltan)
    t.igual("E-03 el resultado de la regla", "UNRESOLVED",
            seguridad.resultado("C1", {}, {}, MATRIZ)["result"])
    for sin in (None, "UNRESOLVED", {"value": None}):
        t.igual("E-03 el check con %r" % (sin,), "APPLICABILITY_UNRESOLVED", _estado(senal=sin))


def test_e04_con_la_senal_en_falso_no_aplica(t):
    """E-04 (C1-04)."""
    estado, _ = seguridad.resolver_regla(seguridad.regla("C1", MATRIZ),
                                         {"authenticationPresent": False})
    t.igual("E-04 la matriz", "NOT_APPLICABLE", estado)
    t.igual("E-04 el check con False", "NOT_APPLICABLE", _estado(senal=False))
    t.igual("E-04 el check con FALSE", "NOT_APPLICABLE", _estado(senal="FALSE"))


def test_e05_los_agentes_primarios(t):
    """E-05 (C1-05)."""
    t.igual("E-05 exactamente dos, en este orden", ["dev-security", "dev-integration"],
            seguridad.regla("C1", MATRIZ)["primaryAgents"])


def test_e06_las_tres_policies(t):
    """E-06 (C1-06)."""
    t.igual("E-06 exactamente estas tres", list(LAS_3_POLICIES),
            seguridad.regla("C1", MATRIZ)["policies"])


def test_e07_los_dos_checks(t):
    """E-07 (C1-07)."""
    c1 = seguridad.regla("C1", MATRIZ)
    t.igual("E-07 exactamente estos dos", list(LOS_2_CHECKS), c1["checks"])
    t.igual("E-07 y cero reviews", [], c1["reviews"])
    t.igual("E-07 el check nuevo se llama asi", "oidc-keycloak-integration", CHECK.CONTROL)


def test_e08_ningun_agente_ni_skill_nuevos(t):
    """E-08 (C1-08)."""
    registro = c_reg.cargar()
    t.igual("E-08 siguen siendo diez agentes", 10, len(registro["agents"]))
    por_id = {a["id"]: a for a in registro["agents"]}
    t.igual("E-08 las skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in por_id["dev-security"].get("skills") or []))
    t.igual("E-08 las skills de dev-integration",
            ["dev-esb", "dev-external-integration", "dev-integration-implementation", "dev-miba",
             "dev-openid-connect", "dev-service-integration"],
            sorted(s["id"] for s in por_id["dev-integration"].get("skills") or []))
    t.igual("E-08 los mismos veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))


# -- Lo que se reusa de D2 -----------------------------------------------------

def test_e09_la_policy_de_d2_no_se_duplica(t):
    """E-09 (C1-09)."""
    ids = [c["id"] for c in REGISTRO["controls"]]
    t.igual("E-09 una sola vez", 1, ids.count("credential-entry-delegation-required"))
    politicas = sorted(p.stem for p in (CONTROLES / "policies").glob("*.md"))
    de_credenciales = [p for p in politicas if "credential" in p or "delegation" in p]
    t.igual("E-09 una sola policy de delegacion de credenciales",
            ["credential-entry-delegation-required"], de_credenciales)


def test_e10_el_check_de_d2_se_reusa_y_no_se_corre(t):
    """E-10 (C1-10) — sin el resultado de D2, la delegacion queda sin resolver."""
    ids = [c["id"] for c in REGISTRO["controls"]]
    t.igual("E-10 authentication-delegation una sola vez", 1,
            ids.count("authentication-delegation"))
    sin_d2 = _ev(delegacion=None)
    t.igual("E-10 sin D2 no pasa aunque el inventario diga que delega", "PARTIAL",
            sin_d2["state"])
    t.igual("E-10 la dimension queda parcial", "PARTIAL",
            _superficie(sin_d2, "backoffice")["dimensions"]["CREDENTIAL_DELEGATION"])
    t.contiene("E-10 con el motivo", "CREDENTIAL_DELEGATION_UNRESOLVED",
               _superficie(sin_d2, "backoffice")["reason"])
    # Y no reimplementa D2: no importa el modulo ni conoce su vocabulario de captura.
    literales = _literales(RUTA_CHECK)
    for propio_de_d2 in ("APPLICATION_OWNED", "DELEGATED", "DGSEI_OPENID_KEYCLOAK",
                         "APPLICATION_LOCAL"):
        t.verdadero("E-10 ningun literal operativo es `%s`" % propio_de_d2,
                    propio_de_d2 not in literales)
    t.verdadero("E-10 no carga el archivo de D2",
                not any("authentication-delegation.py" in lit for lit in literales))


def test_e11_las_fuentes_de_cada_control(t):
    """E-11 (C1-11)."""
    for cid in ("credential-entry-delegation-required", "authentication-delegation"):
        fuentes = c_controles.fuentes_de(c_controles.control(cid, REGISTRO))
        t.igual("E-11 `%s` declara las dos fuentes" % cid, ["ES0901.D2", "ES0902.C1"],
                sorted(f["ruleKey"] for f in fuentes))
    for cid in LOS_3_NUEVOS:
        fuentes = c_controles.fuentes_de(c_controles.control(cid, REGISTRO))
        t.igual("E-11 `%s` tiene una fuente" % cid, 1, len(fuentes))
        t.igual("E-11 `%s` sale de ES0902 6.2 §3 C1" % cid, ["ES0902", "6.2", "3", "C1"],
                [fuentes[0]["standard"], fuentes[0]["version"], fuentes[0]["section"],
                 fuentes[0]["rule"]])


def test_e12_el_resultado_compartido_no_decide_la_regla(t):
    """E-12 (C1-12)."""
    anotado = cruzada.resultado_por_fuente("authentication-delegation", {"result": "PASS"},
                                           ["ES0901.D2", "ES0902.C1"], MAPA)
    for k in ("ES0901.D2", "ES0902.C1"):
        t.igual("E-12 %s no hereda resultado de regla" % k, None,
                anotado["bySource"][k]["ruleResult"])
    ev = {"controlResults": {c: {"result": "PASS", "evidence": ["d2"]}
                             for c in ("authentication-delegation",
                                       "credential-entry-delegation-required")}}
    r = seguridad.resultado("C1", ev, {"authenticationPresent": True}, MATRIZ)
    t.igual("E-12 los de D2 en PASS no ponen a C1 en COMPLIANT", "UNRESOLVED", r["result"])
    t.contiene("E-12 falta el check de C1", "oidc-keycloak-integration", " | ".join(r["reasons"]))
    t.igual("E-12 D2 entero pasa", "PASS", DELEGACION["state"])
    sin_asi = _ev([_sup(evidence=["cfg", "aud", "amb", "prov", "flujo"])])
    t.igual("E-12 y con D2 en PASS el check de C1 no pasa si falta otra dimension",
            "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED", sin_asi["state"])


# -- El inventario ------------------------------------------------------------

def test_e13_el_inventario_vacio_no_cubre(t):
    """E-13 (C1-13)."""
    instalado = json.loads((REGLAS / "authentication-surfaces.json").read_text(encoding="utf-8"))
    t.igual("E-13 se instala vacio", [], instalado["surfaces"])
    t.igual("E-13 valida", [], CHECK.validar_schema(instalado))
    t.igual("E-13 lo carga el check", [], CHECK.cargar()["surfaces"])
    t.igual("E-13 vacio con autenticacion no cubre", "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED",
            CHECK.evaluar({}, True, DELEGACION)["state"])
    t.igual("E-13 y un inventario declarado vacio tampoco",
            "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", _estado([]))
    for nombre, doc in (
            ("una clave de mas arriba", {"version": "1.0", "surfaces": [], "extra": 1}),
            ("una clave de mas en la superficie",
             {"version": "1.0", "surfaces": [_sup(roles=["admin"])]}),
            ("una audiencia fuera del enum",
             {"version": "1.0", "surfaces": [_sup(audience="EMPLOYEE")]}),
            ("un ambiente fuera del enum",
             {"version": "1.0", "surfaces": [_sup(environment="STAGING")]})):
        t.verdadero("E-13 el schema rechaza %s" % nombre, bool(CHECK.validar_schema(doc)))
        t.igual("E-13 y el check no cubre con %s" % nombre,
                "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED",
                CHECK.evaluar({"inventory": doc}, True, DELEGACION)["state"])


def test_e14_cada_superficie_se_evalua_sola(t):
    """E-14 (C1-14)."""
    otra = _sup(surfaceId="mobile", evidence=["cfg", "aud", "amb", "prov", "flujo"])
    d2 = _d2([{"flowId": sid, "audience": "INSTITUTIONAL", "credentialEntry": "DELEGATED",
               "provider": "DGSEI_OPENID_KEYCLOAK", "evidenceRefs": ["d2-cfg"]}
              for sid in ("backoffice", "mobile")])
    r = _ev([SUPERFICIE, otra], delegacion=d2)
    t.igual("E-14 dos resultados", ["backoffice", "mobile"],
            [s["surfaceId"] for s in r["surfaces"]])
    t.igual("E-14 el backoffice pasa", "PASS", _superficie(r, "backoffice")["state"])
    t.igual("E-14 el mobile no", "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED",
            _superficie(r, "mobile")["state"])
    # Cambiar la evidencia de uno no cambia al otro.
    r2 = _ev([SUPERFICIE, _sup(surfaceId="mobile", evidence=[])], delegacion=d2)
    t.igual("E-14 el backoffice sigue igual", _superficie(r, "backoffice"),
            _superficie(r2, "backoffice"))


def test_e15_una_que_cumple_no_tapa_a_otra(t):
    """E-15 (C1-15)."""
    otra = _sup(surfaceId="mobile", flow=None)
    r = _ev([SUPERFICIE, otra])
    t.igual("E-15 el agregado es el de la que falta", "OIDC_FLOW_CONTEXT_UNRESOLVED", r["state"])
    t.verdadero("E-15 y no aprueba", not CHECK.aprueba(r))
    visto = _ev(detectadas=["backoffice", "legacy-admin"])
    t.igual("E-15 una superficie que otra fuente vio y el inventario no",
            "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", visto["state"])
    t.igual("E-15 dice cual", ["legacy-admin"], visto["coverage"]["missing"])
    d2_con_dos = _d2([{"flowId": "backoffice", "audience": "INSTITUTIONAL",
                       "credentialEntry": "DELEGATED", "provider": "DGSEI_OPENID_KEYCLOAK",
                       "evidenceRefs": ["d2-cfg"]},
                      {"flowId": "admin", "audience": "INSTITUTIONAL",
                       "credentialEntry": "DELEGATED", "provider": "DGSEI_OPENID_KEYCLOAK",
                       "evidenceRefs": ["d2-cfg"]}])
    t.igual("E-15 un flujo de D2 que el inventario no nombra",
            "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", _estado(delegacion=d2_con_dos))
    # 🔴 El caso del quinto pase: `detectedSurfaces` torcido no se descarta en silencio.
    for torcido in ([5], [["admin"]], [{"surfaceId": "admin"}], "admin", [""]):
        r = _ev(detectadas=torcido)
        t.igual("E-15 detectedSurfaces=%r no cubre" % (torcido,),
                "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", r["state"])
        t.contiene("E-15 detectedSurfaces=%r y lo dice" % (torcido,), "detectedSurfaces",
                   " | ".join(r["issues"]))
    t.igual("E-15 y dos superficies con el mismo id",
            "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", _estado([SUPERFICIE, SUPERFICIE]))


# -- El protocolo, el proveedor y el registro -----------------------------------

def test_e16_una_libreria_no_prueba_oidc(t):
    """E-16 (C1-16) — las cuatro, una por una."""
    for fuente in ("REPOSITORY_DEPENDENCY", "FRAMEWORK_CONFIGURATION_CLASS", "README_STATEMENT",
                   "SAMPLE_CONFIGURATION"):
        r = _ev(evidencia=_evid(_e("cfg", fuente, "OIDC_PROTOCOL")))
        t.igual("E-16 `%s` no prueba el protocolo" % fuente,
                "OIDC_PROTOCOL_EVIDENCE_UNRESOLVED", r["state"])


def test_e17_la_evidencia_real_prueba_el_protocolo(t):
    """E-17 (C1-17)."""
    for fuente in ("PROJECT_CONFIGURATION", "PROVIDER_METADATA"):
        t.igual("E-17 `%s` prueba el protocolo" % fuente, "PASS",
                _estado(evidencia=_evid(_e("cfg", fuente, "OIDC_PROTOCOL"))))
    # 🔴 Una prueba puede decir que no: sin resultado declarado no prueba.
    t.igual("E-17 una prueba de integracion sin resultado no prueba",
            "OIDC_PROTOCOL_EVIDENCE_UNRESOLVED",
            _estado(evidencia=_evid(_e("cfg", "RUNTIME_INTEGRATION_TEST", "OIDC_PROTOCOL"))))
    for resultado in ("FAIL", "FAILED", "ERROR", "UNAVAILABLE"):
        t.igual("E-17 una prueba de integracion con `%s` no prueba" % resultado,
                "OIDC_PROTOCOL_EVIDENCE_UNRESOLVED" if resultado != "UNAVAILABLE"
                else "TEST_TARGET_UNAVAILABLE",
                _estado(evidencia=_evid(_e("cfg", "RUNTIME_INTEGRATION_TEST", "OIDC_PROTOCOL",
                                           outcome=resultado))))
    t.igual("E-17 y con `CONFIRMED` si", "PASS",
            _estado(evidencia=_evid(_e("cfg", "RUNTIME_INTEGRATION_TEST", "OIDC_PROTOCOL",
                                       outcome="CONFIRMED"))))
    t.igual("E-17 un protocolo declarado que no es OIDC falla", "FAIL",
            _estado([_sup(protocol="SAML")]))
    t.igual("E-17 sin protocolo declarado no es otro protocolo", "PASS",
            _estado([_sup(protocol=None)]))
    t.igual("E-17 un protocolo vacio tampoco", "PASS", _estado([_sup(protocol="  ")]))
    t.igual("E-17 y la grafia no decide", "PASS", _estado([_sup(protocol="oidc")]))
    t.igual("E-17 ni el separador", "PASS", _estado([_sup(protocol="OpenID Connect")]))


def test_e18_el_hostname_no_prueba_la_autoridad(t):
    """E-18 (C1-18)."""
    con_keycloak = "https://keycloak.gcba.example/auth"
    for nombre, sup, prov in (
            ("la forma del hostname", _sup(currentProvider=con_keycloak),
             _e("prov", "HOSTNAME_PATTERN", "PROVIDER_AUTHORITY", environment="QA",
                value=con_keycloak)),
            ("la metadata del proveedor", SUPERFICIE,
             _e("prov", "PROVIDER_METADATA", "PROVIDER_AUTHORITY", environment="QA",
                value=PROVEEDOR)),
            ("una autoridad sobre otro proveedor", _sup(currentProvider=con_keycloak),
             _e("prov", "DGSEI_IDENTITY_REGISTRATION", "PROVIDER_AUTHORITY", environment="QA",
                value=PROVEEDOR))):
        t.igual("E-18 %s no prueba la autoridad" % nombre,
                "KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED", _estado([sup], _evid(prov)))


def test_e19_la_evidencia_de_dgsei_satisface_el_proveedor(t):
    """E-19 (C1-19)."""
    r = _superficie(_ev(), "backoffice")
    t.igual("E-19 la dimension queda satisfecha", "SATISFIED",
            r["dimensions"]["PROVIDER_AUTHORITY"])
    t.igual("E-19 con la evidencia que la sostiene", ["prov"],
            r["evidenceUsed"]["PROVIDER_AUTHORITY"])


def test_e20_un_client_id_no_prueba_el_registro(t):
    """E-20 (C1-20)."""
    t.igual("E-20 client_id sin evidencia de registro", "OIDC_CLIENT_REGISTRATION_UNRESOLVED",
            _estado([_sup(registrationEvidence=[])]))
    t.igual("E-20 un literal de client_id como evidencia", "OIDC_CLIENT_REGISTRATION_UNRESOLVED",
            _estado(evidencia=_evid(_e("reg", "CLIENT_ID_LITERAL", "CLIENT_REGISTRATION",
                                       value="tramites-bo"))))
    t.igual("E-20 el registro de otro cliente", "OIDC_CLIENT_REGISTRATION_UNRESOLVED",
            _estado(evidencia=_evid(_e("reg", "DGSEI_IDENTITY_REGISTRATION",
                                       "CLIENT_REGISTRATION", value="otro-cliente"))))


def test_e21_el_registro_autoritativo_satisface(t):
    """E-21 (C1-21)."""
    for fuente in ("DGSEI_IDENTITY_REGISTRATION", "IDENTITY_TICKET"):
        t.igual("E-21 `%s` en registrationEvidence satisface" % fuente, "PASS",
                _estado(evidencia=_evid(_e("reg", fuente, "CLIENT_REGISTRATION"))))
    t.igual("E-21 la misma citada solo en evidence no", "OIDC_CLIENT_REGISTRATION_UNRESOLVED",
            _estado([_sup(registrationEvidence=[],
                          evidence=SUPERFICIE["evidence"] + ["reg"])]))


# -- El flujo -----------------------------------------------------------------

def test_e22_no_hay_flujo_universal(t):
    """E-22 (C1-22)."""
    literales = {lit.lower() for lit in _literales(RUTA_CHECK)}
    for flujo in ("authorization_code", "authorization code", "pkce", "client_credentials",
                  "implicit", "hybrid", "device_code", "password"):
        t.verdadero("E-22 ningun literal operativo nombra `%s`" % flujo,
                    not any(flujo in lit for lit in literales))
    otra = _sup(surfaceId="api", flow="FLUJO-B")
    ev = _evid(mas=[_e("flujo-b", "OFFICIAL_IDENTITY_GUIDANCE", "FLOW_AUTHORITY",
                       value="FLUJO-B", surfaceIds=["api"])])
    otra["evidence"] = ["cfg", "aud", "amb", "prov", "flujo-b", "asi"]
    d2 = _d2([{"flowId": sid, "audience": "INSTITUTIONAL", "credentialEntry": "DELEGATED",
               "provider": "DGSEI_OPENID_KEYCLOAK", "evidenceRefs": ["d2-cfg"]}
              for sid in ("backoffice", "api")])
    r = _ev([SUPERFICIE, otra], ev, d2)
    t.igual("E-22 dos flujos distintos, cada uno con su autoridad, pasan", "PASS", r["state"])


def test_e23_el_default_del_framework_no_alcanza(t):
    """E-23 (C1-23)."""
    t.igual("E-23 un default del framework", "OIDC_FLOW_AUTHORITY_UNRESOLVED",
            _estado(evidencia=_evid(_e("flujo", "FRAMEWORK_DEFAULT", "FLOW_AUTHORITY",
                                       value="FLUJO-A"))))


def test_e24_sin_flujo_declarado(t):
    """E-24 (C1-24)."""
    t.igual("E-24 sin flujo", "OIDC_FLOW_CONTEXT_UNRESOLVED", _estado([_sup(flow=None)]))


def test_e25_flujo_sin_autoridad(t):
    """E-25 (C1-25)."""
    t.igual("E-25 sin autoridad", "OIDC_FLOW_AUTHORITY_UNRESOLVED",
            _estado(evidencia=_evid(sin=("flujo",))))
    t.igual("E-25 con autoridad para otro flujo", "OIDC_FLOW_AUTHORITY_UNRESOLVED",
            _estado(evidencia=_evid(_e("flujo", "ASI_POLICY", "FLOW_AUTHORITY",
                                       value="FLUJO-Z"))))


def test_e26_con_autoridad_para_el_flujo_pasa(t):
    """E-26 (C1-26) — y es el caso base, que tiene que aprobar."""
    r = _ev()
    t.igual("E-26 pasa", "PASS", r["state"])
    t.verdadero("E-26 aprueba", CHECK.aprueba(r))
    t.igual("E-26 la dimension del flujo", "SATISFIED",
            _superficie(r, "backoffice")["dimensions"]["FLOW_AUTHORITY"])
    t.igual("E-26 todas las dimensiones satisfechas",
            {"SATISFIED"}, set(_superficie(r, "backoffice")["dimensions"].values()))


# -- La delegacion y el servicio anterior ----------------------------------------

def test_e27_recibir_la_contrasena_falla(t):
    """E-27 (C1-27)."""
    t.igual("E-27 por el inventario", "FAIL", _estado([_sup(credentialEntryDelegated=False)]))
    propio = _d2([{"flowId": "backoffice", "audience": "INSTITUTIONAL",
                   "credentialEntry": "APPLICATION_OWNED", "provider": "DGSEI_OPENID_KEYCLOAK",
                   "evidenceRefs": ["d2-cfg"]}])
    t.igual("E-27 D2 falla", "FAIL", propio["state"])
    r = _ev(delegacion=propio)
    t.igual("E-27 y por D2 en FAIL", "FAIL", r["state"])
    t.contiene("E-27 con el motivo de D2", "DIRECT_CREDENTIAL_CAPTURE", r["surfaces"][0]["reason"])
    # 🔴 El caso del tercer pase: D2 evalua por separado dos flujos con el mismo id. Uno delegado
    # no tapa al que captura la contrasena, venga en el orden que venga.
    delegado = {"flowId": "backoffice", "audience": "INSTITUTIONAL",
                "credentialEntry": "DELEGATED", "provider": "DGSEI_OPENID_KEYCLOAK",
                "evidenceRefs": ["d2-cfg"]}
    captura = dict(delegado, credentialEntry="APPLICATION_OWNED")
    for nombre, flujos in (("delegado primero", [delegado, captura]),
                           ("captura primero", [captura, delegado])):
        d2 = _d2(flujos)
        t.igual("E-27 D2 falla con %s" % nombre, "FAIL", d2["state"])
        t.igual("E-27 y C1 tambien, con %s" % nombre, "FAIL", _estado(delegacion=d2))


def test_e28_la_delegacion_sale_de_d2(t):
    """E-28 (C1-28)."""
    r = _superficie(_ev(), "backoffice")
    t.igual("E-28 informa el control de D2", "authentication-delegation",
            r["credentialDelegation"]["control"])
    t.igual("E-28 y su estado para este flujo", "PASS", r["credentialDelegation"]["flowState"])
    t.igual("E-28 la dimension queda satisfecha", "SATISFIED",
            r["dimensions"]["CREDENTIAL_DELEGATION"])
    otro_id = _d2([{"flowId": "otro", "audience": "INSTITUTIONAL", "credentialEntry": "DELEGATED",
                    "provider": "DGSEI_OPENID_KEYCLOAK", "evidenceRefs": ["d2-cfg"]}])
    r2 = _ev(delegacion=otro_id, detectadas=None)
    t.igual("E-28 un flujo de D2 con otro id no delega por esta superficie", "PARTIAL",
            _superficie(r2, "backoffice")["dimensions"]["CREDENTIAL_DELEGATION"])
    # 🔴 El caso del cuarto pase: un D2 torcido SOLO EN PARTE. Descartar el flujo torcido y
    # quedarse con el sano borraria un FAIL; el resultado entero no se lee.
    delegado = {"flowId": "backoffice", "audience": "INSTITUTIONAL",
                "credentialEntry": "DELEGATED", "provider": "DGSEI_OPENID_KEYCLOAK",
                "evidenceRefs": ["d2-cfg"]}
    for x in (["backoffice"], None, 7):
        d2 = _d2([delegado, dict(delegado, flowId=x, credentialEntry="APPLICATION_OWNED")])
        r4 = _ev(delegacion=d2)
        t.verdadero("E-28 D2 con un flowId %r no aprueba" % (x,), r4["state"] != "PASS")
        t.igual("E-28 D2 con un flowId %r deja la delegacion sin resolver" % (x,), "PARTIAL",
                _superficie(r4, "backoffice")["dimensions"]["CREDENTIAL_DELEGATION"])
        t.contiene("E-28 y lo dice con %r" % (x,), "authentication-delegation",
                   " | ".join(r4["issues"]))
        t.igual("E-28 y la cobertura tampoco consta con %r" % (x,),
                "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED", r4["state"])
    for estado_torcido in (["FAIL"], None, {"x": 1}):
        r5 = _ev(delegacion={"flows": [{"flowId": "backoffice", "state": estado_torcido}]})
        t.igual("E-28 un state %r no se lee" % (estado_torcido,), "PARTIAL",
                _superficie(r5, "backoffice")["dimensions"]["CREDENTIAL_DELEGATION"])
    # Un resultado de D2 mal formado no hace caer el check: no cuenta.
    for nombre, torcido in (("flows string", {"flows": "backoffice"}),
                            ("flowId numerico", {"flows": [{"flowId": 1, "state": "PASS"}]}),
                            ("flowId lista", {"flows": [{"flowId": ["backoffice"],
                                                         "state": "PASS"}]}),
                            ("flujo string", {"flows": ["backoffice"]}),
                            ("delegacion lista", [DELEGACION])):
        r3 = _ev(delegacion=torcido)
        t.igual("E-28 D2 con %s deja la delegacion sin resolver" % nombre, "PARTIAL",
                _superficie(r3, "backoffice")["dimensions"]["CREDENTIAL_DELEGATION"])


def test_e29_el_servicio_anterior_activo_falla(t):
    """E-29 (C1-29)."""
    r = _ev([_sup(currentProvider=ANTERIOR)],
            _evid(_e("prov", "DGSEI_IDENTITY_REGISTRATION", "PROVIDER_AUTHORITY",
                     environment="QA", value=ANTERIOR)))
    t.igual("E-29 falla", "FAIL", r["state"])
    s = r["surfaces"][0]
    t.igual("E-29 con los dos estados", ["LEGACY_OPENID_PROVIDER_DETECTED",
                                         "OIDC_MIGRATION_REQUIRED"], s["states"])
    t.verdadero("E-29 y se suben al agregado",
                "OIDC_MIGRATION_REQUIRED" in r["states"]
                and "LEGACY_OPENID_PROVIDER_DETECTED" in r["states"])
    t.igual("E-29 con el punto final del DNS tambien", "FAIL",
            _estado([_sup(currentProvider="https://oauth2-server.apps.buenosaires.gob.ar./")]))
    t.igual("E-29 sin esquema tambien", "FAIL",
            _estado([_sup(currentProvider="oauth2-server.apps.buenosaires.gob.ar/login")]))


def test_e30_una_referencia_historica_no_falla(t):
    """E-30 (C1-30)."""
    hist = _e("hist", "HISTORICAL_REFERENCE", "OIDC_PROTOCOL", value=ANTERIOR)
    r = _ev([_sup(evidence=SUPERFICIE["evidence"] + ["hist"])], _evid(mas=[hist]))
    t.igual("E-30 pasa", "PASS", r["state"])
    t.igual("E-30 y la informa", ["hist"], r["surfaces"][0]["legacyReferences"])
    parecido = "https://oauth2-server.apps.buenosaires.gob.ar.otro.example/"
    t.verdadero("E-30 un host que la contiene no es ella",
                "LEGACY_OPENID_PROVIDER_DETECTED" not in _ev(
                    [_sup(currentProvider=parecido)])["states"])


def test_e31_la_migracion_no_se_aplica(t):
    """E-31 (C1-31)."""
    caso = {"inventory": {"version": "1.0", "surfaces": [_sup(currentProvider=ANTERIOR)]},
            "evidence": copy.deepcopy(EVIDENCIA)}
    antes = copy.deepcopy(caso)
    r = CHECK.evaluar(caso, True, DELEGACION)
    t.igual("E-31 dice que hay que migrar", True, r["surfaces"][0]["migration"]["required"])
    t.igual("E-31 y que no se aplico", False, r["surfaces"][0]["migration"]["applied"])
    t.igual("E-31 el caso no cambio", antes, caso)
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))
    atributos = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    for escritura in ("write", "dump", "writelines", "replace", "remove", "unlink", "rename"):
        t.verdadero("E-31 el modulo no llama a `.%s`" % escritura, escritura not in atributos)
    t.verdadero("E-31 ningun open en modo escritura",
                not ({"w", "a", "wb", "ab", "w+", "r+"} & _literales(RUTA_CHECK)))


# -- El ambiente y la politica de ASI -------------------------------------------

def test_e32_produccion_no_se_fuerza_en_qa(t):
    """E-32 (C1-32)."""
    prd = "https://identidad-prd.example/auth"
    ev = _evid(_e("prov", "DGSEI_IDENTITY_REGISTRATION", "PROVIDER_AUTHORITY",
                  environment="PRD", value=prd),
               _e("amb", "ENVIRONMENT_IDENTITY_CONTRACT", "ENVIRONMENT_IDENTITY",
                  environment="PRD"))
    for ambiente in ("QA", "HML", "DEV"):
        r = _ev([_sup(environment=ambiente, currentProvider=prd)], ev)
        t.verdadero("E-32 la evidencia de produccion no autoriza a %s" % ambiente,
                    r["state"] != "PASS")
        t.igual("E-32 %s queda sin contrato de ambiente" % ambiente,
                "ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED",
                _superficie(r, "backoffice")["dimensions"]["ENVIRONMENT_IDENTITY"])
        t.igual("E-32 %s queda sin autoridad de proveedor" % ambiente,
                "KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED",
                _superficie(r, "backoffice")["dimensions"]["PROVIDER_AUTHORITY"])
    urls = sorted(lit for lit in _literales(RUTA_CHECK)
                  if "buenosaires" in lit or "gob.ar" in lit or lit.startswith("http"))
    t.igual("E-32 la unica URL del modulo es la del servicio anterior", [ANTERIOR], urls)


def test_e33_sin_contrato_de_ambiente(t):
    """E-33 (C1-33)."""
    t.igual("E-33 sin contrato", "ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED",
            _estado(evidencia=_evid(sin=("amb",))))
    t.igual("E-33 con el ambiente sin resolver", "ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED",
            _estado([_sup(environment="UNRESOLVED")]))


def test_e34_sin_politica_de_asi(t):
    """E-34 (C1-34)."""
    t.igual("E-34 sin politica", "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED",
            _estado(evidencia=_evid(sin=("asi",))))
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT"):
        t.igual("E-34 `%s` no la reemplaza" % fuente, "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED",
                _estado(evidencia=_evid(_e("asi", fuente, "ASI_IDENTITY_POLICY"))))


def test_e35_no_se_inventa_ningun_parametro(t):
    """E-35 (C1-35)."""
    salidas = json.dumps([_ev(), _ev(evidencia=[]), _ev([_sup(currentProvider=ANTERIOR)])],
                         ensure_ascii=False).lower()
    literales = {lit.lower() for lit in _literales(RUTA_CHECK)}
    for parametro in ("lifetime", "expires", "claim", "algorithm", "rs256", "hs256", "logout",
                      "end_session", "issuer", "offline_access", "scopes", "ttl"):
        t.no_contiene("E-35 `%s` no sale" % parametro, parametro, salidas)
        t.verdadero("E-35 ningun literal operativo nombra `%s`" % parametro,
                    not any(parametro in lit for lit in literales))


# -- Autenticacion no es autorizacion ---------------------------------------------

def test_e36_autenticar_no_prueba_autorizar(t):
    """E-36 (C1-36)."""
    s = _superficie(_ev(), "backoffice")
    t.igual("E-36 pasa", "PASS", s["state"])
    t.igual("E-36 y la autorizacion no se evaluo", False, s["authorization"]["evaluated"])


def test_e37_los_roles_son_de_la_aplicacion(t):
    """E-37 (C1-37)."""
    t.igual("E-37 se informa el dueno", "APPLICATION",
            _superficie(_ev(), "backoffice")["authorization"]["roleAssignmentOwner"])
    r = _ev([_sup(applicationRoleOwnership="IDENTITY_PROVIDER")])
    s = r["surfaces"][0]
    t.contiene("E-37 otro dueno sale como observacion", "responsabilidad de la aplicacion",
               " | ".join(s["issues"]))
    t.igual("E-37 y no se vuelve una aprobacion de roles", False,
            s["authorization"]["evaluated"])


def test_e38_los_grupos_de_ad_no_se_exigen(t):
    """E-38 (C1-38)."""
    t.igual("E-38 sin grupos de AD pasa", "PASS", _estado())
    t.verdadero("E-38 ninguna dimension habla de AD",
                not any("AD" in d.split("_") for d in
                        _superficie(_ev(), "backoffice")["dimensions"]))


def test_e39_la_restriccion_de_ad_es_recomendacion(t):
    """E-39 (C1-39)."""
    s = _superficie(_ev(), "backoffice")
    t.igual("E-39 sale como recomendacion", [("AD_TREE_GROUP_RESTRICTION", "RECOMMENDATION")],
            [(r["id"], r["binding"]) for r in s["recommendations"]])
    t.igual("E-39 y la superficie pasa igual", "PASS", s["state"])
    t.verdadero("E-39 no es un estado", "AD_TREE_GROUP_RESTRICTION" not in LOS_17)


# -- Ciudadano e institucional ------------------------------------------------------

def test_e40_institucional_con_evidencia_se_evalua(t):
    """E-40 (C1-40)."""
    s = _superficie(_ev(), "backoffice")
    t.igual("E-40 pasa", "PASS", s["state"])
    t.igual("E-40 por la evidencia de audiencia", ["aud"], s["evidenceUsed"]["AUDIENCE"])


def test_e41_ciudadana_no_reemplaza_d1(t):
    """E-41 (C1-41)."""
    r = _ev([_sup(audience="CITIZEN")])
    s = r["surfaces"][0]
    t.igual("E-41 no pasa", "CROSS_STANDARD_INTERPRETATION_REQUIRED", s["state"])
    t.igual("E-41 no se evaluo Keycloak sobre ella", {}, s["dimensions"])
    t.verdadero("E-41 y no dice que D1 se cumpla", "governedBy" not in s)


def test_e42_las_cuatro_audiencias_sin_reconciliar(t):
    """E-42 (C1-42)."""
    for audiencia, ev in (("CITIZEN", None), ("MIXED", None), ("UNRESOLVED", None),
                          ("INSTITUTIONAL", _evid(sin=("aud",)))):
        t.igual("E-42 %s sin reconciliar" % audiencia, "CROSS_STANDARD_INTERPRETATION_REQUIRED",
                _estado([_sup(audience=audiencia)], ev))


def _reconciliacion(resolucion="KEYCLOAK_OIDC", **extra):
    extra.setdefault("surfaceIds", ["backoffice"])
    return _e("rec", "IDENTITY_CHECKPOINT", "CROSS_STANDARD_RECONCILIATION",
              resolution=resolucion, **extra)


def test_e43_la_reconciliacion_de_un_proyecto_es_suya(t):
    """E-43 (C1-43)."""
    ciudadana = _sup(audience="CITIZEN", evidence=SUPERFICIE["evidence"] + ["rec"])
    t.igual("E-43 con la reconciliacion de su proyecto se evalua", "PASS",
            _estado([ciudadana], _evid(mas=[_reconciliacion()])))
    t.igual("E-43 la de otro proyecto no", "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado([ciudadana], _evid(mas=[_reconciliacion(scope="licencias")])))
    t.igual("E-43 la de otra superficie del mismo proyecto no",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado([ciudadana], _evid(mas=[_reconciliacion(surfaceIds=["portal"])])))
    d1 = _ev([ciudadana], _evid(mas=[_reconciliacion("ES0901_D1")]))
    t.igual("E-43 resuelta por el camino ciudadano no aplica", "NOT_APPLICABLE", d1["state"])
    t.igual("E-43 y dice quien la gobierna", "ES0901.D1", d1["surfaces"][0]["governedBy"])
    t.igual("E-43 dos reconciliaciones que se contradicen no resuelven nada",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado([_sup(audience="CITIZEN",
                          evidence=SUPERFICIE["evidence"] + ["rec", "rec2"])],
                    _evid(mas=[_reconciliacion(),
                               _e("rec2", "IDENTITY_TICKET", "CROSS_STANDARD_RECONCILIATION",
                                  resolution="ES0901_D1", surfaceIds=["backoffice"])])))

    # 🔴 El caso del refutador: UNA reconciliacion sin `surfaceIds`, citada por dos superficies
    # ciudadanas del mismo proyecto. La cita la escribe quien arma el inventario; si alcanzara,
    # cualquier superficie del proyecto se resolveria citandola.
    for resolucion in ("KEYCLOAK_OIDC", "ES0901_D1"):
        sin_nombrar = _reconciliacion(resolucion)
        del sin_nombrar["surfaceIds"]
        portal = _sup(surfaceId="portal", audience="CITIZEN",
                      evidence=SUPERFICIE["evidence"] + ["rec"])
        turnos = _sup(surfaceId="turnos", audience="CITIZEN",
                      evidence=SUPERFICIE["evidence"] + ["rec"])
        d2 = _d2([{"flowId": sid, "audience": "INSTITUTIONAL", "credentialEntry": "DELEGATED",
                   "provider": "DGSEI_OPENID_KEYCLOAK", "evidenceRefs": ["d2-cfg"]}
                  for sid in ("portal", "turnos")])
        r = _ev([portal, turnos], _evid(mas=[sin_nombrar]), d2)
        for sid in ("portal", "turnos"):
            t.igual("E-43 %s sin surfaceIds no resuelve `%s`" % (resolucion, sid),
                    "CROSS_STANDARD_INTERPRETATION_REQUIRED", _superficie(r, sid)["state"])
        nombra_uno = dict(sin_nombrar, surfaceIds=["portal"])
        r = _ev([portal, turnos], _evid(mas=[nombra_uno]), d2)
        t.igual("E-43 %s nombrando portal, turnos sigue sin resolver" % resolucion,
                "CROSS_STANDARD_INTERPRETATION_REQUIRED", _superficie(r, "turnos")["state"])
        t.verdadero("E-43 %s y portal si se resuelve" % resolucion,
                    _superficie(r, "portal")["state"] != "CROSS_STANDARD_INTERPRETATION_REQUIRED")
    # 🔴 El caso del segundo pase: `surfaceIds` como string no es una lista, y un string se
    # compara por substring. Lo que no tiene la forma declarada no cuenta, en ninguna dimension.
    ciudadana_base = _sup(audience="CITIZEN", evidence=SUPERFICIE["evidence"] + ["rec"])
    for torcido in ("backoffice-legacy", "portal,backoffice", "backoffice", ["backoffice", 1]):
        r = _ev([ciudadana_base], _evid(mas=[_reconciliacion(surfaceIds=torcido)]))
        t.igual("E-43 surfaceIds=%r no resuelve" % (torcido,),
                "CROSS_STANDARD_INTERPRETATION_REQUIRED", r["state"])
        t.contiene("E-43 surfaceIds=%r se informa como mal formada" % (torcido,), "rec",
                   " | ".join(i for i in r["issues"] if "forma declarada" in i))
    t.igual("E-43 una audiencia con surfaceIds string no clasifica",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado(evidencia=_evid(_e("aud", "PROJECT_CONTRACT", "AUDIENCE",
                                       value="INSTITUTIONAL", surfaceIds="otro-backoffice-x"))))
    t.igual("E-43 y el ambiente de otra forma tampoco cuenta",
            "KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED",
            _estado(evidencia=_evid(_e("prov", "DGSEI_IDENTITY_REGISTRATION",
                                       "PROVIDER_AUTHORITY", environment=["QA"],
                                       value=PROVEEDOR))))
    # 🔴 El caso del quinto pase: dos reconciliaciones que se contradicen, y la que dice que no
    # viene torcida. No se descarta: la superficie queda sin resolver.
    contra = _sup(audience="CITIZEN", evidence=SUPERFICIE["evidence"] + ["rec", "rec2"])
    for nombre, torcida in (
            ("surfaceIds string", {"surfaceIds": "backoffice"}),
            ("resolution lista", {"resolution": ["ES0901_D1"]})):
        rec2 = _e("rec2", "IDENTITY_TICKET", "CROSS_STANDARD_RECONCILIATION",
                  resolution="ES0901_D1", surfaceIds=["backoffice"])
        rec2.update(torcida)
        t.igual("E-43 la reconciliacion contraria con %s no desaparece" % nombre,
                "CROSS_STANDARD_INTERPRETATION_REQUIRED",
                _estado([contra], _evid(mas=[_reconciliacion(), rec2])))
    # 🔴 El caso del sexto pase: la contraria con el propio id torcido, o ausente del catalogo.
    for nombre, cambio in (("evidenceId lista", {"evidenceId": ["rec2"]}),
                           ("sin evidenceId", {"evidenceId": None}),
                           ("evidenceId numerico", {"evidenceId": 7}),
                           ("evidenceId vacio", {"evidenceId": ""})):
        rec2 = _e("rec2", "IDENTITY_TICKET", "CROSS_STANDARD_RECONCILIATION",
                  resolution="ES0901_D1", surfaceIds=["backoffice"])
        rec2.update(cambio)
        t.igual("E-43 la contraria con %s no desaparece" % nombre,
                "CROSS_STANDARD_INTERPRETATION_REQUIRED",
                _estado([contra], _evid(mas=[_reconciliacion(), rec2])))
    # El caso del septimo pase: una resolucion que no se reconoce tampoco se descarta.
    for resolucion in ("es0901_d1", "ES0901-D1", None):
        rec2 = _e("rec2", "IDENTITY_TICKET", "CROSS_STANDARD_RECONCILIATION",
                  surfaceIds=["backoffice"])
        if resolucion is not None:
            rec2["resolution"] = resolucion
        t.igual("E-43 la contraria con resolution=%r no desaparece" % (resolucion,),
                "CROSS_STANDARD_INTERPRETATION_REQUIRED",
                _estado([contra], _evid(mas=[_reconciliacion(), rec2])))
    t.igual("E-43 ni una citada que no esta en el catalogo",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado([contra], _evid(mas=[_reconciliacion()])))
    # Y la audiencia institucional, por el mismo mecanismo.
    t.igual("E-43 una evidencia de audiencia que no nombra la superficie no la clasifica",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _estado(evidencia=_evid(_e("aud", "PROJECT_CONTRACT", "AUDIENCE",
                                       value="INSTITUTIONAL"))))


def test_e44_frontend_ciudadano_y_backoffice(t):
    """E-44 (C1-44)."""
    frontend = _sup(surfaceId="frontend", audience="CITIZEN")
    r = _ev([frontend, SUPERFICIE])
    t.igual("E-44 el backoffice pasa", "PASS", _superficie(r, "backoffice")["state"])
    t.igual("E-44 el frontend queda sin resolver", "CROSS_STANDARD_INTERPRETATION_REQUIRED",
            _superficie(r, "frontend")["state"])
    t.igual("E-44 el agregado no es PASS", "CROSS_STANDARD_INTERPRETATION_REQUIRED", r["state"])


def test_e45_ningun_checkpoint_se_vuelve_doctrina(t):
    """E-45 (C1-45) — sobre un modulo recien cargado, que no vio las corridas de los otros tests."""
    fresco = _cargar(RUTA_CHECK, "c1_oidc_fresco")
    ciudadana = _sup(audience="CITIZEN", evidence=SUPERFICIE["evidence"] + ["rec"])

    def corrida(evidencia):
        return fresco.evaluar({"inventory": {"version": "1.0", "surfaces": [ciudadana]},
                               "evidence": evidencia}, True, DELEGACION)["state"]

    t.igual("E-45 con el checkpoint pasa", "PASS", corrida(_evid(mas=[_reconciliacion()])))
    t.igual("E-45 la corrida siguiente sin el checkpoint vuelve a quedar sin resolver",
            "CROSS_STANDARD_INTERPRETATION_REQUIRED", corrida(_evid()))
    t.igual("E-45 y el inventario instalado sigue vacio", [], CHECK.cargar()["surfaces"])
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))
    globales = [n for n in ast.walk(arbol) if isinstance(n, ast.Global)]
    t.igual("E-45 el modulo no reescribe ningun global", [], globales)


# -- Los limites -----------------------------------------------------------------

def test_e46_dev_openid_connect_no_crea_verdad(t):
    """E-46 (C1-46)."""
    # 🔴 Un PRODUCTO: cada evidencia del caso que aprueba, reemplazada de a una por lo que diria
    # la skill o un agente. Reemplazarlas todas juntas corta en la audiencia y nunca llega a mirar
    # el resto de las dimensiones.
    for fuente in ("SKILL_OUTPUT", "AGENT_STATEMENT"):
        for base in EVIDENCIA:
            dimension = base["establishes"][0]
            prestada = dict(base, sourceType=fuente, reference="dev-openid-connect")
            r = _ev(evidencia=_evid(prestada))
            t.verdadero("E-46 `%s` en lugar de `%s` no pasa" % (fuente, base["evidenceId"]),
                        r["state"] != "PASS")
            t.verdadero("E-46 `%s` no satisface %s" % (fuente, dimension),
                        r["surfaces"][0]["dimensions"].get(dimension) != "SATISFIED")
    t.verdadero("E-46 el modulo no importa el registro de agentes",
                "registro_agentes" not in _importados(RUTA_CHECK))
    registro = c_reg.cargar()
    nombres = {a["id"] for a in registro["agents"]} | {
        s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    literales = _literales(RUTA_CHECK)
    t.igual("E-46 ningun literal operativo nombra un agente o una skill", [],
            sorted(nombres & literales))


def test_e47_c1_no_es_c2_ni_vu8_ni_d1_ni_d8(t):
    """E-47 (C1-47)."""
    literales = _literales(RUTA_CHECK)
    for otra in ("C2", "Vu8", "D8", "ES0902.C2", "ES0902.Vu8", "ES0901.D8"):
        t.verdadero("E-47 ningun literal operativo es `%s`" % otra, otra not in literales)
    serializado = json.dumps(_ev(), ensure_ascii=False)
    for otra in ('"C2"', "Vu8", "D1", "D8"):
        t.no_contiene("E-47 un PASS no nombra %s" % otra, otra, serializado)
    senales = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    ev = {"controlResults": {c["id"]: {"result": "PASS", "evidence": ["c1"]}
                             for c in seguridad.controles_de("C1", MATRIZ)}}
    t.igual("E-47 C1 cumple con sus cinco", "COMPLIANT",
            seguridad.resultado("C1", ev, senales, MATRIZ)["result"])
    t.verdadero("E-47 y C2 no", seguridad.resultado("C2", ev, senales, MATRIZ)["result"]
                != "COMPLIANT")


def test_e48_c1_no_es_aprobacion_oficial(t):
    """E-48 (C1-48)."""
    r = _ev()
    t.igual("E-48 ningun valor es un estado oficial", [],
            sorted(set(_valores(r)) & set(evaluacion.ESTADOS_OFICIALES)))
    t.no_contiene("E-48 no dice APPROVED", "APPROVED", json.dumps(r))
    for productor in evaluacion.PRODUCTORES_INTERNOS:
        t.igual("E-48 `%s` no puede aprobar" % productor, "OFFICIAL_STATUS_UNRESOLVED",
                evaluacion.estado_oficial({"state": "APPROVED", "producer": productor,
                                           "evidence": ["c1-pass"]})["state"])


def test_e49_la_trazabilidad_viaja(t):
    """E-49 (C1-49)."""
    caminos = {
        "sin senal": _ev(senal=None), "no aplica": _ev(senal=False),
        "inventario vacio": _ev([]), "pasa": _ev(),
        "falla": _ev([_sup(currentProvider=ANTERIOR)]),
        "cruzada": _ev([_sup(audience="CITIZEN")]),
        "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True, DELEGACION),
    }
    for nombre, r in caminos.items():
        t.igual("E-49 %s conserva la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-49 %s conserva la clave" % nombre, "ES0902.C1", r["ruleKey"])
    bloque = normativa.resolucion({"authenticationPresent": True})["standards"]["ES0902"]
    t.igual("E-49 la unidad de trabajo cita ES0902", "ES0902", bloque["standard"]["id"])
    t.igual("E-49 en la version 6.2", "6.2", bloque["standard"]["version"])
    t.verdadero("E-49 con C1 aplicable", "C1" in bloque["applicableRules"])
    t.verdadero("E-49 y el check de C1 declarado", "oidc-keycloak-integration"
                in bloque["declaredChecks"])
    t.igual("E-49 la trazabilidad de la regla", "ES0902.C1",
            seguridad.trazabilidad("C1", MATRIZ)["ruleKey"])


def test_e50_la_misma_evidencia_el_mismo_resultado(t):
    """E-50 (C1-50)."""
    frontend = _sup(surfaceId="frontend", audience="CITIZEN")
    mobile = _sup(surfaceId="mobile", flow=None)
    superficies = [SUPERFICIE, frontend, mobile]
    base = json.dumps(_ev(superficies), sort_keys=True)
    t.igual("E-50 dos corridas iguales", base, json.dumps(_ev(superficies), sort_keys=True))
    azar = random.Random(50)
    for vuelta in range(5):
        s = copy.deepcopy(superficies)
        e = copy.deepcopy(EVIDENCIA)
        azar.shuffle(s)
        azar.shuffle(e)
        t.igual("E-50 desordenado %d" % vuelta, base, json.dumps(_ev(s, e), sort_keys=True))
    t.igual("E-50 los diecisiete estados, con ese nombre", sorted(LOS_17), sorted(CHECK.ESTADOS))

    # 🔴 Los dos casos del refutador. Un id de evidencia repetido no cuenta en ninguna de sus
    # versiones -si ganara una, ganaria la que venga ultima-, y las observaciones salen ordenadas.
    readme = _e("asi", "README_STATEMENT", "ASI_IDENTITY_POLICY")
    directo = json.dumps(_ev(evidencia=_evid(mas=[readme])), sort_keys=True)
    invertido = json.dumps(_ev(evidencia=[readme] + _evid()), sort_keys=True)
    t.igual("E-50 un id repetido da lo mismo en los dos ordenes", directo, invertido)
    t.igual("E-50 y no cuenta: la politica de ASI queda sin resolver",
            "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED", json.loads(directo)["state"])
    t.contiene("E-50 y lo dice", "asi", " | ".join(json.loads(directo)["issues"]))
    a = _sup(surfaceId="a", evidence=SUPERFICIE["evidence"] + ["zz1"])
    b = _sup(surfaceId="b", evidence=SUPERFICIE["evidence"] + ["zz2"])
    t.igual("E-50 la evidencia huerfana sale igual en cualquier orden",
            json.dumps(_ev([a, b]), sort_keys=True), json.dumps(_ev([b, a]), sort_keys=True))
    # 🔴 El caso del segundo pase: dos superficies con el mismo id. Toda lista de la salida se
    # ordena por su contenido completo, no solo por su id.
    x, y = SUPERFICIE, _sup(flow=None)
    t.igual("E-50 dos superficies con el mismo id salen igual en cualquier orden",
            json.dumps(_ev([x, y]), sort_keys=True), json.dumps(_ev([y, x]), sort_keys=True))
    torcida = _e("asi", "ASI_POLICY", "ASI_IDENTITY_POLICY", surfaceIds="backoffice")
    t.igual("E-50 un id repetido con una version mal formada tampoco cuenta",
            "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED",
            _estado(evidencia=_evid(mas=[torcida])))
    t.igual("E-50 un id repetido se informa una vez, y no como huerfano", [],
            [i for i in json.loads(directo)["issues"] if "no existe" in i])
