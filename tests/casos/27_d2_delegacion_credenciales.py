# D2: delegar el ingreso de credenciales, y decir que no se puede verificar.
#
# Escenarios E-01 a E-31 de docs/cambios/d2-delegacion-de-credenciales/spec.md. Entre
# parentesis, el D2-nn del pedido de instalacion.
#
# Nada de esto verifica una integracion con miBA ni un requisito de ES0902: lo primero no tiene
# material autoritativo y lo segundo no es fuente declarada de este harness. Lo que se comprueba
# es donde escribe el usuario su credencial, a que proveedor se delega, y que los dos huecos
# queden nombrados en vez de rellenados.
import importlib.util
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"

sys.path.insert(0, str(BIN))
from orquestacion import controles as c_controles      # noqa: E402
from orquestacion import matriz as c_matriz            # noqa: E402
from orquestacion import normativa as c_normativa      # noqa: E402
from orquestacion import plan as c_plan                # noqa: E402
from orquestacion import registro_agentes as c_reg     # noqa: E402
from orquestacion import senales as c_senales          # noqa: E402


def _cargar(nombre, alias):
    spec = importlib.util.spec_from_file_location(alias, CONTROLES / "checks" / (nombre + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar("authentication-delegation", "d2_check")
CHECK_D1 = _cargar("citizen-authentication-mechanism", "d2_check_d1")

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D2"}


# -- las piezas de los casos ---------------------------------------------------

def _ev(eid="ev-1", tipo="PROJECT_CONTEXT", ref="identity_and_access.auth_model",
        claim="la aplicacion autentica usuarios", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid="authenticationPresent", productor=None, **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev()] if evidencia is None else evidencia,
         "producer": productor or {"type": "HUMAN"}}
    s.update(extra)
    return s


def _ciudadana(valor="TRUE"):
    return _senal(valor, [_ev("cf-1", "PROJECT_CONTEXT", "project_profile.purpose",
                              "tramite de cara al ciudadano")], sid="citizenFacing")


def _evf(eid="e1", tipo="PROJECT_CONFIGURATION", ref="auth.config",
         claim="el ingreso de credenciales se delega en el portal autorizado", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _flujo(audiencia="INSTITUTIONAL", ingreso="DELEGATED", proveedor="DGSEI_OPENID_KEYCLOAK",
           fid="f1", refs=None):
    return {"flowId": fid, "audience": audiencia, "credentialEntry": ingreso,
            "provider": proveedor, "evidenceRefs": ["e1"] if refs is None else refs}


def _caso(flujos=None, evidencia=None, aplicacion=None, **extra):
    d = {"application": aplicacion or {"id": "portal-tramites", "environment": "PRD"},
         "authenticationFlows": [_flujo()] if flujos is None else flujos,
         "evidence": [_evf()] if evidencia is None else evidencia}
    d.update(extra)
    return d


_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "b" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


# -- la senal ------------------------------------------------------------------

def test_e01_d2_es_condicional(t):
    """E-01 (D2-01) — CONDITIONAL sobre authenticationPresent, y la fila no cambio."""
    d2 = c_matriz.regla("D2")
    t.igual("E-01 el modo", "CONDITIONAL", d2["applicability"]["mode"])
    t.igual("E-01 la senal", ["authenticationPresent"], d2["applicability"]["signals"])
    t.igual("E-01 la policy", ["credential-entry-delegation-required"], d2["policies"])
    t.igual("E-01 el check", ["authentication-delegation"], d2["checks"])
    t.igual("E-01 el agente", ["dev-integration"], d2["primaryAgents"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d2["status"])


def test_e02_true_hace_aplicable(t):
    """E-02 (D2-02) — TRUE con evidencia deja D2 aplicable y exige sus dos controles."""
    bloque = c_normativa.resolucion({"authenticationPresent": _senal("TRUE")})
    t.verdadero("E-02 D2 aplica", "D2" in bloque["applicableRules"])
    t.verdadero("E-02 exige su policy",
                "credential-entry-delegation-required" in bloque["declaredPolicies"])
    t.verdadero("E-02 y su check",
                "authentication-delegation" in bloque["declaredChecks"])


def test_e03_false_hace_no_aplicable(t):
    """E-03 (D2-03) — FALSE con evidencia deja D2 fuera."""
    evidencia = [_ev(tipo="PROJECT_CONTEXT", ref="project_profile.purpose",
                     claim="servicio publico sin login de usuarios")]
    bloque = c_normativa.resolucion({"authenticationPresent": _senal("FALSE", evidencia)})
    t.verdadero("E-03 D2 no aplica", "D2" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no esta entre las aplicables", "D2" not in bloque["applicableRules"])
    t.verdadero("E-03 su policy no se exige",
                "credential-entry-delegation-required" not in bloque["declaredPolicies"])


def test_e04_sin_senal_queda_sin_resolver(t):
    """E-04 (D2-04) — sin senal, D2 sin resolver, nunca en no aplicable."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D2 esta sin resolver", "D2" in sin_resolver)
    t.igual("E-04 con el motivo", "APPLICABILITY_UNRESOLVED", sin_resolver["D2"]["reason"])
    t.igual("E-04 y la senal que falta", ["authenticationPresent"],
            sin_resolver["D2"]["missingSignals"])
    t.verdadero("E-04 y nunca en no aplicable", "D2" not in bloque["notApplicableRules"])


def test_e05_una_dependencia_sola_no_enciende_la_senal(t):
    """E-05 (D2-05) — REPOSITORY_DEPENDENCY sola deja la senal sin resolver."""
    solo_dependencia = [_ev("d1", "REPOSITORY_DEPENDENCY", "package.json",
                            "angular-oauth2-oidc figura en dependencies")]
    resuelta = c_senales.resolver_una(_senal("TRUE", solo_dependencia))
    t.igual("E-05 no afirma", "UNRESOLVED", resuelta["value"])
    t.verdadero("E-05 y lo dice",
                "SIGNAL_EVIDENCE_MISSING" in resuelta["states"])

    bloque = c_normativa.resolucion({"authenticationPresent": _senal("TRUE", solo_dependencia)})
    t.verdadero("E-05 D2 queda sin resolver",
                "D2" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-05 y no se vuelve no aplicable", "D2" not in bloque["notApplicableRules"])


def test_e06_la_dependencia_con_evidencia_de_uso_resuelve(t):
    """E-06 — la misma dependencia, acompanada de evidencia de que participa, si resuelve."""
    evidencia = [_ev("d1", "REPOSITORY_DEPENDENCY", "package.json",
                     "angular-oauth2-oidc figura en dependencies"),
                 _ev("c1", "REPOSITORY_CONFIGURATION", "src/auth/auth.config.ts",
                     "la ruta /login usa el cliente OIDC configurado")]
    resuelta = c_senales.resolver_una(_senal("TRUE", evidencia))
    t.igual("E-06 ahora si", "TRUE", resuelta["value"])
    t.igual("E-06 y conserva las dos evidencias", 2, len(resuelta["evidence"]))


def test_e07_no_hay_un_segundo_framework(t):
    """E-07 — la misma infraestructura de D1, y la clase nueva vale para cualquier senal."""
    t.verdadero("E-07 la matriz declara la senal",
                "authenticationPresent" in c_senales.declaradas())
    # 📌 Son dos desde que se instalo ES0902: C1 reusa `authenticationPresent` a proposito, y
    # las de ES0902 salen con su clave compuesta porque `C1` sola no dice de cual estandar es.
    t.igual("E-07 y dice de que regla es", ["D2", "ES0902.C1"],
            c_senales.reglas_de("authenticationPresent"))
    t.vacio("E-07 valida contra el mismo schema",
            "; ".join(c_senales.validar_schema(_senal())))

    # La clase debil no es de D2: vale igual para la senal de D1.
    sola = [_ev("d1", "REPOSITORY_DEPENDENCY", "package.json", "hay una libreria")]
    for sid in ("authenticationPresent", "citizenFacing", "databasePresent"):
        r = c_senales.producir(sid, sola, {"type": "DETERMINISTIC"}, valor="TRUE")
        t.igual("E-07 %s con una dependencia sola" % sid, "UNRESOLVED", r["value"])
    t.verdadero("E-07 y esta declarada como debil",
                "REPOSITORY_DEPENDENCY" in c_senales.FUENTES_DEBILES)


def test_e08_la_senal_conserva_evidencia_y_productor(t):
    """E-08 (D2-18) — la evidencia y el modo del productor viajan con el resultado."""
    resuelta = c_senales.resolver_una(
        _senal("TRUE", productor={"type": "AGENT_EVIDENCE_BACKED", "id": "dev-integration"}))
    t.igual("E-08 el valor", "TRUE", resuelta["value"])
    t.igual("E-08 el modo del productor", "AGENT_EVIDENCE_BACKED",
            resuelta["producer"]["type"])
    t.igual("E-08 quien fue", "dev-integration", resuelta["producer"]["id"])
    t.igual("E-08 y la referencia de la evidencia", "identity_and_access.auth_model",
            resuelta["evidence"][0]["reference"])

    # Un productor que el registro no declara invalida la senal: no se crean agentes.
    inventado = c_senales.resolver_una(
        _senal("TRUE", productor={"type": "AGENT_EVIDENCE_BACKED", "id": "dev-inventado"}))
    t.igual("E-08 un agente inexistente no produce", "UNRESOLVED", inventado["value"])


# -- la delegacion -------------------------------------------------------------

def test_e09_credenciales_en_la_aplicacion_fallan(t):
    """E-09 (D2-06) — validacion local de credenciales con D2 aplicable: FAIL."""
    caso = _caso([_flujo(ingreso="APPLICATION_OWNED", proveedor="APPLICATION_LOCAL")],
                 [_evf(claim="tabla de usuarios con contrasenas y validacion propia")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-09 el estado", "FAIL", salida["state"])
    t.igual("E-09 con el motivo", "DIRECT_CREDENTIAL_CAPTURE", salida["reason"])
    t.verdadero("E-09 no aprueba", not CHECK.aprueba(salida))


def test_e10_institucional_delegado_pasa(t):
    """E-10 (D2-07) — delegado al portal de la DGSEI con Keycloak: PASS."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-10 el estado", "PASS", salida["state"])
    t.verdadero("E-10 aprueba", CHECK.aprueba(salida))
    t.igual("E-10 y el proveedor esperado era ese", "DGSEI_OPENID_KEYCLOAK",
            salida["flows"][0]["expectedProvider"])


def test_e11_el_endpoint_viejo_no_es_proveedor(t):
    """E-11 (D2-08) — el endpoint anterior no vale para credenciales nuevas."""
    caso = _caso([_flujo(proveedor="LEGACY_OPENID_ENDPOINT")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-11 el estado", "FAIL", salida["state"])
    t.igual("E-11 con el motivo", "LEGACY_PROVIDER_NOT_AUTHORIZED", salida["reason"])
    t.verdadero("E-11 aunque haya delegacion", "DELEGATED" ==
                salida["flows"][0]["credentialEntry"])


def test_e12_flujo_ciudadano_a_nivel_gobierno(t):
    """E-12 (D2-09) — satisface la delegacion sin nombrar un solo interno de miBA."""
    caso = _caso([_flujo(audiencia="CITIZEN", proveedor="GCBA_CITIZEN_AUTHENTICATION")],
                 [_evf(claim="el frontend delega el login en el servicio de autenticacion "
                             "ciudadana del GCBA")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-12 el estado", "PASS", salida["state"])
    texto = repr(salida)
    for interno in ("client_id", "clientId", "redirect_uri", "well-known", "http"):
        t.verdadero("E-12 el resultado no trae %s" % interno, interno not in texto)


def test_e13_un_formulario_propio_no_es_delegacion(t):
    """E-13 — que despues llame a una API no la vuelve delegada."""
    caso = _caso([_flujo(ingreso="APPLICATION_OWNED", proveedor="DGSEI_OPENID_KEYCLOAK")],
                 [_evf(claim="formulario propio que despues llama a la API de identidad")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-13 el estado", "FAIL", salida["state"])
    t.igual("E-13 con el motivo", "DIRECT_CREDENTIAL_CAPTURE", salida["reason"])
    t.contiene("E-13 y lo explica", "no la vuelve delegada", salida["flows"][0]["detail"])


def test_e14_una_dependencia_no_prueba_delegacion(t):
    """E-14 (D2-05) — la libreria instalada no dice donde se escribe la credencial."""
    caso = _caso(evidencia=[_evf(tipo="REPOSITORY_DEPENDENCY", ref="package.json",
                                 claim="angular-oauth2-oidc esta en dependencies")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-14 el estado", "PARTIAL", salida["state"])
    t.igual("E-14 con el motivo", "EVIDENCE_INCOMPLETE", salida["reason"])
    t.verdadero("E-14 no aprueba", not CHECK.aprueba(salida))


def test_e15_las_tres_formas_de_que_falte_evidencia(t):
    """E-15 — redirect sin proveedor, ingreso sin resolver y sin ningun flujo: PARTIAL."""
    sin_proveedor = _caso([_flujo(proveedor="UNRESOLVED")],
                          [_evf(claim="el login redirige a un portal externo")])
    salida = CHECK.evaluar(sin_proveedor, _senal("TRUE"))
    t.igual("E-15 sin proveedor", "PARTIAL", salida["state"])
    t.igual("E-15 con el motivo", "PROVIDER_NOT_EVIDENCED", salida["reason"])

    sin_ingreso = _caso([_flujo(ingreso="UNRESOLVED")],
                        [_evf(claim="hay un login y no se sabe como")])
    otra = CHECK.evaluar(sin_ingreso, _senal("TRUE"))
    t.igual("E-15 sin saber donde se escribe la credencial", "PARTIAL", otra["state"])
    t.igual("E-15 con su motivo", "CREDENTIAL_ENTRY_UNRESOLVED", otra["reason"])

    sin_flujos = _caso(flujos=[], evidencia=[])
    tercera = CHECK.evaluar(sin_flujos, _senal("TRUE"))
    t.igual("E-15 sin ningun flujo", "PARTIAL", tercera["state"])
    t.igual("E-15 y su motivo", "AUTHENTICATION_FLOW_NOT_EVIDENCED", tercera["reason"])

    for nombre, r in (("sin proveedor", salida), ("sin ingreso", otra),
                      ("sin flujos", tercera)):
        t.verdadero("E-15 %s no aprueba" % nombre, not CHECK.aprueba(r))


def test_e16_la_afirmacion_de_un_agente_no_alcanza(t):
    """E-16 — una opinion con formato de evidencia no sostiene el PASS."""
    caso = _caso(evidencia=[_evf(tipo="AGENT_STATEMENT", ref="dev-integration",
                                 claim="lo revise y delega bien")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-16 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-16 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-16 AGENT_STATEMENT no es fuente suficiente",
                "AGENT_STATEMENT" not in CHECK.FUENTES_SUFICIENTES)


def test_e17_solo_pass_aprueba(t):
    """E-17 — siete estados, uno solo aprueba, y PARTIAL no se sube por suposicion."""
    t.igual("E-17 son siete", 7, len(CHECK.ESTADOS))
    for estado in CHECK.ESTADOS:
        t.igual("E-17 %s" % estado, str(estado == "PASS"),
                str(CHECK.aprueba({"state": estado})))

    # El mismo caso, con la unica diferencia de la clase de fuente, cruza de PARTIAL a PASS.
    flojo = _caso(evidencia=[_evf(tipo="REPOSITORY_DEPENDENCY")])
    t.igual("E-17 con evidencia floja", "PARTIAL",
            CHECK.evaluar(flojo, _senal("TRUE"))["state"])
    t.igual("E-17 con evidencia que alcanza", "PASS",
            CHECK.evaluar(_caso(), _senal("TRUE"))["state"])


def test_e18_un_camino_directo_activo_manda(t):
    """E-18 — el flujo que cumple no tapa al que no."""
    caso = _caso([_flujo(fid="f1"),
                  _flujo(fid="f2", ingreso="APPLICATION_OWNED", proveedor="APPLICATION_LOCAL",
                         refs=["e2"])],
                 [_evf("e1"), _evf("e2", claim="login de emergencia con usuario y clave local")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-18 el estado", "FAIL", salida["state"])
    t.igual("E-18 el flujo que cumple sigue diciendo que cumple", "PASS",
            salida["flows"][0]["state"])
    t.igual("E-18 y el otro que no", "FAIL", salida["flows"][1]["state"])
    t.verdadero("E-18 el resultado no aprueba", not CHECK.aprueba(salida))


# -- el contexto y las fronteras -----------------------------------------------

def test_e19_audiencia_sin_resolver(t):
    """E-19 (D2-12) — hay autenticacion y no se sabe de quien: no se adivina."""
    caso = _caso([_flujo(audiencia="UNRESOLVED")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-19 el estado", "AUTHENTICATION_CONTEXT_UNRESOLVED", salida["state"])
    t.verdadero("E-19 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-19 no es un PARTIAL", salida["state"] != "PARTIAL")
    t.contiene("E-19 y lo dice", "No se adivina",
               salida["flows"][0]["detail"].replace("no se adivina", "No se adivina"))


def test_e20_citizen_facing_es_contexto_secundario(t):
    """E-20 (D2-12) — se reusa la senal de D1, no se redefine."""
    caso = _caso([_flujo(audiencia="UNRESOLVED",
                         proveedor="GCBA_CITIZEN_AUTHENTICATION")])
    salida = CHECK.evaluar(caso, _senal("TRUE"), contexto=_ciudadana("TRUE"))
    t.igual("E-20 resuelve con el contexto", "PASS", salida["state"])
    t.igual("E-20 y dice de donde salio la audiencia", "citizenFacing",
            salida["flows"][0]["audienceFrom"])
    t.igual("E-20 es la senal de D1", "citizenFacing", CHECK.SENAL_DE_CONTEXTO)

    # Lo que declara el flujo le gana al contexto general: una app ciudadana puede tener
    # un backoffice.
    con_flujo = _caso([_flujo(audiencia="INSTITUTIONAL")])
    otra = CHECK.evaluar(con_flujo, _senal("TRUE"), contexto=_ciudadana("TRUE"))
    t.igual("E-20 el flujo manda", "flow", otra["flows"][0]["audienceFrom"])
    t.igual("E-20 y pasa como institucional", "PASS", otra["state"])


def test_e21_la_aplicabilidad_no_depende_de_citizen_facing(t):
    """E-21 (D2-13) — con citizenFacing en cualquiera de sus tres valores, D2 aplica."""
    for valor in ("TRUE", "FALSE", "UNRESOLVED"):
        senales = {"authenticationPresent": _senal("TRUE")}
        if valor != "UNRESOLVED":
            senales["citizenFacing"] = _ciudadana(valor)
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-21 con citizenFacing %s D2 aplica igual" % valor,
                    "D2" in bloque["applicableRules"])

    # Y D2 resuelve donde D1 ni siquiera puede decir si le toca.
    bloque = c_normativa.resolucion({"authenticationPresent": _senal("TRUE")})
    t.verdadero("E-21 D1 queda sin resolver",
                "D1" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.igual("E-21 el check de D2 resuelve igual", "PASS",
            CHECK.evaluar(_caso(), _senal("TRUE"))["state"])


def test_e22_d1_y_d2_aplican_juntas(t):
    """E-22 (D2-14) — una app ciudadana que autentica dispara las dos."""
    bloque = c_normativa.resolucion({"authenticationPresent": _senal("TRUE"),
                                     "citizenFacing": _ciudadana("TRUE")})
    t.verdadero("E-22 D1 aplica", "D1" in bloque["applicableRules"])
    t.verdadero("E-22 D2 tambien", "D2" in bloque["applicableRules"])
    for control in ("gcba-citizen-authentication-required",
                    "credential-entry-delegation-required"):
        t.verdadero("E-22 exige %s" % control, control in bloque["declaredPolicies"])
    for control in ("citizen-authentication-mechanism", "authentication-delegation"):
        t.verdadero("E-22 exige %s" % control, control in bloque["declaredChecks"])


def test_e23_d2_no_duplica_la_seleccion_de_mecanismo(t):
    """E-23 (D2-15) — el mismo caso, dos motivos distintos, y ninguno nombra al otro."""
    flujo_ciudadano_mal = _caso(
        [_flujo(audiencia="CITIZEN", proveedor="DGSEI_OPENID_KEYCLOAK")],
        [_evf(claim="el login del ciudadano delega en el portal institucional")])
    d2 = CHECK.evaluar(flujo_ciudadano_mal, _senal("TRUE"), contexto=_ciudadana("TRUE"))

    caso_d1 = {"application": flujo_ciudadano_mal["application"],
               "authenticationFlows": [{"flowId": "f1", "audience": "CITIZEN",
                                        "mechanism": "INSTITUTIONAL_DIRECTORY",
                                        "evidenceRefs": ["e1"]}],
               "evidence": flujo_ciudadano_mal["evidence"]}
    d1 = CHECK_D1.evaluar(caso_d1, _ciudadana("TRUE"))

    t.igual("E-23 D2 falla", "FAIL", d2["state"])
    t.igual("E-23 D1 tambien", "FAIL", d1["state"])
    t.verdadero("E-23 y por motivos distintos", d2["reason"] != d1["reason"])
    t.igual("E-23 el de D2", "DELEGATION_TARGET_MISMATCH", d2["reason"])

    t.verdadero("E-23 D2 no nombra el control de D1",
                "citizen-authentication-mechanism" not in repr(d2))
    t.verdadero("E-23 ni su motivo",
                "CITIZEN_AUTHENTICATION_MECHANISM_REPLACED" not in repr(d2))
    t.verdadero("E-23 D1 no nombra el control de D2",
                "authentication-delegation" not in repr(d1))
    t.verdadero("E-23 ni la senal de D2", "authenticationPresent" not in repr(d1))


def test_e24_lo_que_depende_de_es0902(t):
    """E-24 (D2-16) — se nombra, y no anula la verificacion de la delegacion."""
    caso = _caso(requestedValidations=[{"id": "DELEGATION"}, {"id": "PASSWORD_POLICY"}])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-24 la delegacion se verifica igual", "PASS", salida["state"])
    t.igual("E-24 y lo diferido se nombra", 1, len(salida["deferred"]))
    t.igual("E-24 con su estado", "ES0902_CONTEXT_REQUIRED", salida["deferred"][0]["state"])

    # Una validacion declarada de ES0902 por quien la pide tambien.
    declarada = _caso(requestedValidations=[{"id": "LO_QUE_SEA", "standard": "ES0902"}])
    t.igual("E-24 la declarada tambien se difiere", 1,
            len(CHECK.evaluar(declarada, _senal("TRUE"))["deferred"]))

    # Y si lo unico que se pidio es de ES0902, ese es el estado del resultado.
    solo = {"application": {"id": "portal-tramites", "environment": "PRD"},
            "authenticationFlows": [], "evidence": [],
            "requestedValidations": [{"id": "SESSION_SECURITY"}]}
    t.igual("E-24 solo ES0902", "ES0902_CONTEXT_REQUIRED",
            CHECK.evaluar(solo, _senal("TRUE"))["state"])


def test_e25_no_se_inventa_ninguna_regla_de_es0902(t):
    """E-25 (D2-17) — el check nombra lo que no contesta y no produce ni un requisito."""
    caso = _caso(requestedValidations=[{"id": "PASSWORD_POLICY"},
                                       {"id": "CIPHER_REQUIREMENTS"}])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    for diferida in salida["deferred"]:
        t.igual("E-25 %s no se contesta" % diferida["id"], "ES0902_CONTEXT_REQUIRED",
                diferida["state"])
        t.contiene("E-25 y dice por que", "no tiene como fuente declarada", diferida["reason"])
        t.verdadero("E-25 %s no trae un requisito" % diferida["id"],
                    "requirement" not in diferida and "expected" not in diferida)

    # 📌 Esto medía "ES0902 no esta instalado" barriendo el disco, y ES0902 ya esta instalado.
    # La proposicion que importaba no era esa: era que el check de D2 **no contesta** lo que es
    # de otro estandar. Ahora vale mas fuerte, porque el otro estandar existe y el check sigue
    # difiriendo en vez de ponerse a resolverlo.
    t.verdadero("E-25 ES0902 si esta instalado ahora",
                bool(list((RAIZ / "harnesses" / "desarrollo" / "reglas").glob("es0902*.json"))))
    t.verdadero("E-25 y el check de D2 sigue sin resolverlo",
                all(d["state"] == "ES0902_CONTEXT_REQUIRED" for d in salida["deferred"])
                and bool(salida["deferred"]))
    # 📌 El sujeto del barrido son IDENTIFICADORES, no una palabra del idioma: `seguridad`
    # aparece en la prosa del check y no prueba nada. Lo que no puede aparecer es una REGLA de
    # ES0902 — el check nombra el estandar para decir que no lo contesta, y ahi se termina.
    t.no_contiene("E-25 el check no nombra ninguna regla de ES0902", "ES0902.", repr(salida))
    t.igual("E-25 la traza sigue siendo de ES0901", "ES0901", salida["source"]["standard"])


def test_e26_la_remediacion_ciudadana_declara_el_hueco(t):
    """E-26 (D2-10) — SPECIALIZED_SKILL_GAP, y D2 sigue sin cumplir."""
    fallado = CHECK.evaluar(
        _caso([_flujo(audiencia="CITIZEN", ingreso="APPLICATION_OWNED",
                      proveedor="APPLICATION_LOCAL")]),
        _senal("TRUE"))
    hueco = CHECK.remediacion(fallado)
    t.igual("E-26 el estado", "SPECIALIZED_SKILL_GAP", hueco["state"])
    t.igual("E-26 la skill que falta", "dev-miba", hueco["skill"])
    t.igual("E-26 no hace cumplir a D2", "False", str(hueco["compliant"]))
    t.igual("E-26 el check sigue fallando", "FAIL", fallado["state"])
    t.igual("E-26 con su trazabilidad", "D2", hueco["source"]["rule"])
    t.igual("E-26 lo que pasa no pide remediacion", "None",
            str(CHECK.remediacion(CHECK.evaluar(_caso(), _senal("TRUE")))))


def test_e27_openid_no_reemplaza_a_miba(t):
    """E-27 (D2-11) — apoya lo institucional; no cubre lo ciudadano."""
    ruteo = c_reg.resolver_ruteo("dev-integration", "dev-openid-connect")
    t.igual("E-27 dev-openid-connect esta instalada", "ROUTABLE", ruteo["result"])

    institucional = CHECK.remediacion(
        CHECK.evaluar(_caso([_flujo(ingreso="APPLICATION_OWNED",
                                    proveedor="APPLICATION_LOCAL")]), _senal("TRUE")))
    t.igual("E-27 lo institucional se rutea", "ROUTABLE", institucional["state"])
    t.igual("E-27 a la skill de OpenID", "dev-openid-connect", institucional["skill"])

    ciudadano = CHECK.remediacion(
        CHECK.evaluar(_caso([_flujo(audiencia="CITIZEN", ingreso="APPLICATION_OWNED",
                                    proveedor="APPLICATION_LOCAL")]), _senal("TRUE")))
    t.igual("E-27 lo ciudadano no", "SPECIALIZED_SKILL_GAP", ciudadano["state"])
    t.verdadero("E-27 y no se rutea a la de OpenID",
                ciudadano["skill"] != "dev-openid-connect")
    t.igual("E-27 tampoco hace cumplir", "False", str(ciudadano["compliant"]))


# Las seis clases que E-28 nombra. Mismos patrones que el caso de D1: los de forma de dato van
# anclados a principio de linea porque los artefactos nombran esas palabras EN PROSA para
# negarlas, y un patron literal se pondria rojo contra el descargo en vez de contra una fuga.
PROHIBIDOS = (
    r"https?://",
    r"client_id", r"clientId", r"client-id",
    r"redirect_uri", r"redirectUri", r"redirect-uri",
    r"\.well-known", r"realms/", r"buenosaires\.gob\.ar",
    r"(?m)^\s*claims\s*:",
    r"(?m)^\s*(sub|preferred_username|given_name|family_name|email|cuil|documento)\s*:",
    r"(?mi)^.*\bendpoints?\s*:",
    r"(?m)^\s*(DEV|UAT|HML|PRD)\s*:",
)

FUGAS = (
    ("client id en forma de codigo", "clientId: portal-tramites-prd"),
    ("URL del proveedor", "issuer: https://id.ejemplo.gob.ar"),
    ("endpoint de descubrimiento", "GET /.well-known/openid-configuration"),
    ("bloque de claims", "claims:\n  sub: el identificador del ciudadano\n"),
    ("un claim suelto", "cuil: documento del ciudadano"),
    ("token endpoint", "token endpoint: /protocol/openid-connect/token"),
    ("redirect uri en kebab", "redirect-uri: /callback"),
    ("configuracion por ambiente", "DEV: idp-dev\nUAT: idp-uat\nPRD: idp-prod"),
)

ARTEFACTOS_D2 = ("policies/credential-entry-delegation-required.md",
                 "checks/authentication-delegation.py")


def test_e28_no_se_inventan_internos_de_proveedor(t):
    """E-28 — ni client ids, ni claims, ni redirect URIs, ni endpoints, ni ambientes."""
    for relativa in ARTEFACTOS_D2:
        archivo = CONTROLES / Path(relativa)
        texto = io.open(archivo, encoding="utf-8").read()
        for patron in PROHIBIDOS:
            encontrado = re.search(patron, texto)
            t.vacio("E-28 %s sin %s" % (archivo.name, patron),
                    encontrado.group(0).strip() if encontrado else "")

    # La premisa de la mitad de abajo, afirmada y no supuesta: si el texto base ya matcheara
    # algun patron, `any()` daria verdadero para cualquier fuga y las ocho serian decorado.
    base = io.open(CONTROLES / Path(ARTEFACTOS_D2[0]), encoding="utf-8").read()
    t.verdadero("E-28 el texto base no matchea ningun patron",
                not any(re.search(p, base) for p in PROHIBIDOS))

    for nombre, fuga in FUGAS:
        contaminado = base + "\n\n" + fuga + "\n"
        t.verdadero("E-28 la guarda atrapa %s" % nombre,
                    any(re.search(p, contaminado) for p in PROHIBIDOS))


# -- la propagacion y la instalacion -------------------------------------------

def test_e29_la_unidad_lleva_las_dos_senales(t):
    """E-29 (D2-18) — authenticationPresent con su evidencia, citizenFacing al lado."""
    unidad = {"id": "u1", "objective": "o", "domain": "integration",
              "requiredCapabilities": [], "dependencies": [], "signals": [],
              "normativeSignals": {"authenticationPresent": _senal("TRUE"),
                                   "citizenFacing": _ciudadana("TRUE")}}
    documento = c_plan.armar({"objective": "x", "domains": ["integration"], "policies": [],
                              "workUnits": [unidad]}, _CONTEXTO, {}, None)
    n = documento["workUnits"][0]["normative"]

    t.igual("E-29 el valor viaja", "TRUE", n["signals"]["authenticationPresent"]["value"])
    t.igual("E-29 la evidencia tambien", "identity_and_access.auth_model",
            n["signals"]["authenticationPresent"]["evidence"][0]["reference"])
    t.igual("E-29 citizenFacing se conserva, no se redefine", "TRUE",
            n["signals"]["citizenFacing"]["value"])
    t.igual("E-29 con su propia evidencia", "project_profile.purpose",
            n["signals"]["citizenFacing"]["evidence"][0]["reference"])
    t.verdadero("E-29 D2 aplica en la unidad", "D2" in n["applicableRules"])
    t.verdadero("E-29 y D1 tambien", "D1" in n["applicableRules"])
    t.vacio("E-29 el plan valida", c_plan.validar(documento))

    # Con una sola senal, la otra no aparece inventada.
    sola = dict(unidad, normativeSignals={"authenticationPresent": _senal("TRUE")})
    otro = c_plan.armar({"objective": "x", "domains": ["integration"], "policies": [],
                         "workUnits": [sola]}, _CONTEXTO, {}, None)
    señales = otro["workUnits"][0]["normative"]["signals"]
    t.verdadero("E-29 citizenFacing no se inventa", "citizenFacing" not in señales)


def test_e30_los_controles_dejan_de_faltar(t):
    """E-30 (D2-19) — desaparecen de la lista sin tocar la declaracion de D2."""
    resolucion = c_matriz.resolver({"authenticationPresent": True})

    sin_nada = c_matriz.controles_no_instalados(resolucion, policies_instaladas=[],
                                                checks_instalados=[], reviews_instaladas=[])
    estados = {f["id"]: f["state"] for f in sin_nada}
    t.igual("E-30 antes la policy", "DECLARED_POLICY_NOT_INSTALLED",
            estados.get("credential-entry-delegation-required"))
    t.igual("E-30 antes el check", "DECLARED_CHECK_NOT_INSTALLED",
            estados.get("authentication-delegation"))

    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    t.verdadero("E-30 despues la policy no falta",
                "credential-entry-delegation-required" not in faltan)
    t.verdadero("E-30 despues el check no falta",
                "authentication-delegation" not in faltan)

    d2 = c_matriz.regla("D2")
    t.igual("E-30 la fila no cambio", ["credential-entry-delegation-required"], d2["policies"])
    t.igual("E-30 ni sus checks", ["authentication-delegation"], d2["checks"])
    t.igual("E-30 ni su senal", ["authenticationPresent"], d2["applicability"]["signals"])


def test_e31_la_traza_se_conserva(t):
    """E-31 (D2-20) — ES0901 / 6.3 / 7.1 / D2 en todo lo que D2 emite."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    for campo, esperado in TRAZA.items():
        t.igual("E-31 el check: %s" % campo, esperado, salida["source"][campo])

    t.igual("E-31 la trazabilidad de la matriz", TRAZA, c_matriz.trazabilidad("D2"))

    policy = io.open(CONTROLES / "policies" / "credential-entry-delegation-required.md",
                     encoding="utf-8").read()
    t.contiene("E-31 la policy dice su regla", "rule: D2", policy)
    t.contiene("E-31 y su estandar", "standard: ES0901", policy)

    declarado = c_controles.control("authentication-delegation")
    t.igual("E-31 el registro tambien", "D2", declarado["source"]["rule"])
    t.igual("E-31 con su version", "6.3", declarado["source"]["version"])

    hueco = CHECK.remediacion({"state": "FAIL", "flows": [{"audience": "CITIZEN"}]})
    t.igual("E-31 y la remediacion", "D2", hueco["source"]["rule"])
