# D1: la primera regla condicional que necesita una senal de verdad.
#
# Escenarios E-01 a E-31 de docs/cambios/d1-autenticacion-ciudadana/spec.md. Entre parentesis,
# el D1-nn del pedido de instalacion.
#
# Nada de esto verifica una integracion con miBA: no hay material autoritativo para hacerlo y
# el cambio no lo promete. Lo que se comprueba es que la aplicabilidad se resuelva con
# evidencia, que lo ausente quede sin resolver y que el unico estado que aprueba sea PASS.
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


def _check():
    ruta = CONTROLES / "checks" / "citizen-authentication-mechanism.py"
    spec = importlib.util.spec_from_file_location("d1_check", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _check()

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D1"}


# -- las piezas de los casos ---------------------------------------------------

def _evidencia(eid="ev-1", tipo="JIRA_FICHA_DE_PROYECTO", ref="GCBA-1234",
               claim="el tramite lo inicia el ciudadano", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, productor=None, sid="citizenFacing", **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_evidencia()] if evidencia is None else evidencia,
         "producer": productor or {"type": "HUMAN"}}
    s.update(extra)
    return s


def _evidencia_de_flujo(eid="e1", tipo="PROJECT_CONFIGURATION", ref="auth.config",
                        claim="el frontend autentica con el mecanismo ciudadano del GCBA",
                        **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _caso(flujos=None, evidencia=None, aplicacion=None):
    return {
        "application": aplicacion or {"id": "tramites-ciudadano", "environment": "PRD"},
        "authenticationFlows": flujos if flujos is not None else [
            {"flowId": "f1", "audience": "CITIZEN",
             "mechanism": "GCBA_CITIZEN_AUTHENTICATION", "evidenceRefs": ["e1"]}],
        "evidence": evidencia if evidencia is not None else [_evidencia_de_flujo()],
    }


_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "a" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


# -- la senal y su contrato ----------------------------------------------------

def test_e01_d1_es_condicional(t):
    """E-01 (D1-01) — CONDITIONAL con una sola senal, y la fila no cambio."""
    d1 = c_matriz.regla("D1")
    t.igual("E-01 el modo", "CONDITIONAL", d1["applicability"]["mode"])
    t.igual("E-01 la senal", ["citizenFacing"], d1["applicability"]["signals"])
    t.igual("E-01 la policy", ["gcba-citizen-authentication-required"], d1["policies"])
    t.igual("E-01 el check", ["citizen-authentication-mechanism"], d1["checks"])
    t.igual("E-01 el agente", ["dev-integration"], d1["primaryAgents"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d1["status"])


def test_e02_el_contrato_de_una_senal(t):
    """E-02 — el schema valida y entra en el subconjunto soportado."""
    t.vacio("E-02 una senal bien formada valida",
            "; ".join(c_senales.validar_schema(_senal())))

    sin_valor = _senal()
    del sin_valor["value"]
    t.verdadero("E-02 sin `value` no valida", bool(c_senales.validar_schema(sin_valor)))

    t.verdadero("E-02 un valor fuera del enum no pasa",
                bool(c_senales.validar_schema(_senal(valor="MAYBE"))))

    sin_productor = _senal()
    del sin_productor["producer"]
    t.verdadero("E-02 sin productor no valida",
                bool(c_senales.validar_schema(sin_productor)))


def test_e03_true_hace_aplicable(t):
    """E-03 (D1-02) — citizenFacing TRUE deja D1 aplicable."""
    bloque = c_normativa.resolucion({"citizenFacing": _senal("TRUE")})
    t.verdadero("E-03 D1 aplica", "D1" in bloque["applicableRules"])
    t.verdadero("E-03 y exige su policy",
                "gcba-citizen-authentication-required" in bloque["declaredPolicies"])
    t.verdadero("E-03 y su check",
                "citizen-authentication-mechanism" in bloque["declaredChecks"])


def test_e04_false_hace_no_aplicable(t):
    """E-04 (D1-03) — citizenFacing FALSE deja D1 fuera."""
    evidencia = [_evidencia(tipo="PROJECT_CONTEXT", ref="project_profile.purpose",
                            claim="backoffice de uso interno, sin acceso del ciudadano")]
    bloque = c_normativa.resolucion({"citizenFacing": _senal("FALSE", evidencia)})
    t.verdadero("E-04 D1 no aplica", "D1" in bloque["notApplicableRules"])
    t.verdadero("E-04 y no esta entre las aplicables",
                "D1" not in bloque["applicableRules"])
    t.verdadero("E-04 y su policy no se exige",
                "gcba-citizen-authentication-required" not in bloque["declaredPolicies"])


def test_e05_sin_senal_queda_sin_resolver(t):
    """E-05 (D1-04) — sin senal, D1 queda sin resolver con la que falta escrita."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-05 D1 esta sin resolver", "D1" in sin_resolver)
    t.igual("E-05 con el motivo", "APPLICABILITY_UNRESOLVED",
            sin_resolver["D1"]["reason"])
    t.igual("E-05 y la senal que falta", ["citizenFacing"],
            sin_resolver["D1"]["missingSignals"])


def test_e06_lo_ausente_nunca_es_falso(t):
    """E-06 (D1-05) — UNRESOLVED no se convierte en FALSE por ningun camino."""
    caminos = {
        "sin senal": {},
        "senal UNRESOLVED": {"citizenFacing": _senal("UNRESOLVED", [])},
        "senal sin evidencia": {"citizenFacing": _senal("TRUE", [])},
        "senal invalida": {"citizenFacing": _senal("TRUE", [_evidencia(ref="")])},
    }
    for nombre, senales in caminos.items():
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-06 %s no vuelve a D1 no aplicable" % nombre,
                    "D1" not in bloque["notApplicableRules"])
        t.verdadero("E-06 %s no vuelve a D1 aplicable" % nombre,
                    "D1" not in bloque["applicableRules"])
        t.verdadero("E-06 %s la deja sin resolver" % nombre,
                    "D1" in {u["rule"] for u in bloque["unresolvedRules"]})


def test_e07_la_senal_conserva_su_evidencia(t):
    """E-07 (D1-06) — el resultado preserva las referencias de evidencia."""
    evidencia = [_evidencia("ev-1"), _evidencia("ev-2", tipo="PROJECT_DOCUMENTATION",
                                                ref="docs/alcance.md",
                                                claim="el tramite es de cara al ciudadano")]
    resuelta = c_senales.resolver_una(_senal("TRUE", evidencia))
    t.igual("E-07 el valor", "TRUE", resuelta["value"])
    t.igual("E-07 estan las dos evidencias", 2, len(resuelta["evidence"]))
    t.igual("E-07 con su referencia", "GCBA-1234", resuelta["evidence"][0]["reference"])
    t.igual("E-07 con su clase", "PROJECT_DOCUMENTATION",
            resuelta["evidence"][1]["sourceType"])
    t.igual("E-07 con lo que afirma", "el tramite es de cara al ciudadano",
            resuelta["evidence"][1]["claim"])
    t.igual("E-07 y quien la produjo", "HUMAN", resuelta["producer"]["type"])

    # Y sobrevive al bloque normativo de la unidad.
    bloque = c_normativa.resolucion({"citizenFacing": _senal("TRUE", evidencia)})
    t.igual("E-07 la unidad la lleva", 2,
            len(bloque["signals"]["citizenFacing"]["evidence"]))


def test_e08_afirmar_sin_evidencia_no_afirma(t):
    """E-08 (D1-06) — TRUE o FALSE sin evidencia se degradan."""
    for valor in ("TRUE", "FALSE"):
        resuelta = c_senales.resolver_una(_senal(valor, []))
        t.igual("E-08 %s sin evidencia" % valor, "UNRESOLVED", resuelta["value"])
        t.verdadero("E-08 %s lo dice" % valor,
                    "SIGNAL_EVIDENCE_MISSING" in resuelta["states"])

    # Una evidencia que no referencia nada no es evidencia.
    hueca = c_senales.resolver_una(_senal("TRUE", [_evidencia(ref="   ")]))
    t.igual("E-08 sin referencia no vale", "UNRESOLVED", hueca["value"])

    # Y la opinion de un agente, sola, tampoco.
    opinion = c_senales.resolver_una(
        _senal("TRUE", [_evidencia(tipo="AGENT_STATEMENT", ref="dev-integration",
                                   claim="parece una app ciudadana")]))
    t.igual("E-08 la opinion sola no sostiene", "UNRESOLVED", opinion["value"])
    t.verdadero("E-08 y lo dice", "SIGNAL_EVIDENCE_MISSING" in opinion["states"])


def test_e09_dos_evidencias_que_se_contradicen(t):
    """E-09 — SIGNAL_CONFLICT, sin elegir una."""
    evidencia = [
        _evidencia("ev-1", tipo="PROJECT_CONTEXT", ref="project_profile",
                   claim="portal del ciudadano", supports="TRUE"),
        _evidencia("ev-2", tipo="TASK_CONTEXT", ref="task.title",
                   claim="backoffice interno", supports="FALSE"),
    ]
    resuelta = c_senales.resolver_una(_senal("TRUE", evidencia))
    t.igual("E-09 no se decide", "UNRESOLVED", resuelta["value"])
    t.verdadero("E-09 y se dice", "SIGNAL_CONFLICT" in resuelta["states"])
    t.igual("E-09 las dos se conservan", 2, len(resuelta["evidence"]))


def test_e10_lo_interpretado_no_pisa_lo_estructurado(t):
    """E-10 — gana el dato estructurado y la interpretacion queda anotada."""
    evidencia = [
        _evidencia("ev-1", tipo="PROJECT_CONTEXT", ref="identity_and_access.auth_model",
                   claim="autenticacion ciudadana declarada", supports="TRUE"),
        _evidencia("ev-2", tipo="PROJECT_DOCUMENTATION", ref="docs/viejo.md",
                   claim="el documento dice que es interno", supports="FALSE"),
    ]
    resuelta = c_senales.resolver_una(_senal("TRUE", evidencia))
    t.igual("E-10 gana lo estructurado", "TRUE", resuelta["value"])
    t.verdadero("E-10 y la interpretacion queda anotada",
                "SIGNAL_INTERPRETATION_OVERRIDDEN" in resuelta["states"])
    t.igual("E-10 sin perder la evidencia", 2, len(resuelta["evidence"]))


def test_e11_una_senal_que_la_matriz_no_declara(t):
    """E-11 — SIGNAL_NOT_DECLARED, y no entra en la resolucion."""
    inventada = _senal("TRUE", sid="tieneChatbot")
    resuelta = c_senales.resolver_una(inventada)
    t.igual("E-11 no se resuelve", "UNRESOLVED", resuelta["value"])
    t.verdadero("E-11 y se dice por que",
                "SIGNAL_NOT_DECLARED" in resuelta["states"])
    t.igual("E-11 no llega a la matriz", {},
            c_senales.booleanos({"tieneChatbot": resuelta}))
    t.verdadero("E-11 citizenFacing si esta declarada",
                "citizenFacing" in c_senales.declaradas())


def test_e12_la_abstraccion_no_es_de_citizen_facing(t):
    """E-12 — la misma funcion produce otra senal declarada y mueve otra regla."""
    evidencia = [_evidencia("ev-1", tipo="REPOSITORY_CONFIGURATION", ref="docker-compose.yml",
                            claim="el sistema usa PostgreSQL")]
    resuelta = c_senales.producir("databasePresent", evidencia, {"type": "DETERMINISTIC"},
                                  valor="TRUE")
    t.igual("E-12 la senal se resuelve", "TRUE", resuelta["value"])

    bloque = c_normativa.resolucion({"databasePresent": resuelta})
    t.verdadero("E-12 P7 pasa a aplicable", "P7" in bloque["applicableRules"])
    t.verdadero("E-12 y D1 sigue sin resolver, que es otra senal",
                "D1" in {u["rule"] for u in bloque["unresolvedRules"]})

    # Tres senales distintas por el mismo camino, sin una rama por id: la evidencia floja
    # falla igual en las tres, y cada una mueve las reglas que la matriz le ata.
    for sid in ("citizenFacing", "databasePresent", "frontendPresent"):
        floja = c_senales.producir(
            sid, [_evidencia(tipo="AGENT_STATEMENT", ref="un agente", claim="me parece")],
            {"type": "AGENT_EVIDENCE_BACKED", "id": "dev-integration"}, valor="TRUE")
        t.igual("E-12 %s con evidencia floja" % sid, "UNRESOLVED", floja["value"])
        t.verdadero("E-12 %s lo dice igual" % sid,
                    "SIGNAL_EVIDENCE_MISSING" in floja["states"])
        firme = c_senales.producir(sid, [_evidencia(tipo="PROJECT_CONTEXT")],
                                   {"type": "DETERMINISTIC"}, valor="TRUE")
        t.igual("E-12 %s se resuelve igual" % sid, "TRUE", firme["value"])
        t.verdadero("E-12 %s mueve sus reglas" % sid,
                    bool(set(c_senales.reglas_de(sid))
                         & set(c_normativa.resolucion({sid: firme})["applicableRules"])))


def test_e13_los_booleanos_viejos_siguen(t):
    """E-13 — la forma vieja no se rompe."""
    directo = c_matriz.resolver({"citizenFacing": True})
    t.verdadero("E-13 la matriz sigue recibiendo booleanos",
                "D1" in directo["applicableRules"])

    bloque = c_normativa.resolucion({"citizenFacing": True, "databasePresent": False})
    t.verdadero("E-13 D1 aplica", "D1" in bloque["applicableRules"])
    t.verdadero("E-13 P7 no", "P7" in bloque["notApplicableRules"])
    t.igual("E-13 y queda dicho de donde salio", "TASK_CONTEXT",
            bloque["signals"]["citizenFacing"]["evidence"][0]["sourceType"])


# -- el check ------------------------------------------------------------------

def test_e14_mecanismo_del_gcba_pasa(t):
    """E-14 (D1-07) — flujo ciudadano con el mecanismo del GCBA: PASS."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-14 el estado", "PASS", salida["state"])
    t.verdadero("E-14 aprueba", CHECK.aprueba(salida))
    t.igual("E-14 con la evidencia usada", ["e1"], salida["flows"][0]["evidenceUsed"])


def test_e15_credenciales_propias_falla(t):
    """E-15 (D1-08) — login propio del ciudadano: FAIL."""
    caso = _caso(
        flujos=[{"flowId": "f1", "audience": "CITIZEN",
                 "mechanism": "CUSTOM_LOCAL_CREDENTIALS", "evidenceRefs": ["e1"]}],
        evidencia=[_evidencia_de_flujo(claim="tabla de usuarios y registro propio")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-15 el estado", "FAIL", salida["state"])
    t.igual("E-15 con el motivo", "CITIZEN_AUTHENTICATION_MECHANISM_REPLACED",
            salida["reason"])
    t.verdadero("E-15 no aprueba", not CHECK.aprueba(salida))


def test_e16_evidencia_incompleta_es_parcial(t):
    """E-16 (D1-09) — proveedor sin evidencia suficiente: PARTIAL, y no aprueba."""
    caso = _caso(evidencia=[_evidencia_de_flujo(tipo="AGENT_STATEMENT",
                                                ref="dev-integration",
                                                claim="deberia usar el mecanismo del GCBA")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-16 el estado", "PARTIAL", salida["state"])
    t.igual("E-16 con el motivo", "EVIDENCE_INCOMPLETE", salida["reason"])
    t.verdadero("E-16 no aprueba", not CHECK.aprueba(salida))


def test_e17_app_interna_no_aplica(t):
    """E-17 (D1-10) — la regla no aplica y el check no evalua."""
    evidencia = [_evidencia(tipo="PROJECT_CONTEXT", ref="project_profile.purpose",
                            claim="backoffice de empleados")]
    salida = CHECK.evaluar(_caso(), _senal("FALSE", evidencia))
    t.igual("E-17 el estado", "NOT_APPLICABLE", salida["state"])
    t.igual("E-17 y no mira ningun flujo", [], salida["flows"])
    t.verdadero("E-17 no aprueba", not CHECK.aprueba(salida))


def test_e18_senal_sin_resolver_no_evalua(t):
    """E-18 (D1-04) — APPLICABILITY_UNRESOLVED, con la senal que falta."""
    for senal in (None, _senal("UNRESOLVED", []), _senal("TRUE", [])):
        salida = CHECK.evaluar(_caso(), senal and c_senales.resolver_una(senal))
        t.igual("E-18 el estado", "APPLICABILITY_UNRESOLVED", salida["state"])
        t.igual("E-18 y la senal que falta", ["citizenFacing"], salida["missingSignals"])
        t.igual("E-18 no evalua ningun flujo", [], salida["flows"])
        # El quinto estado, salido de una corrida de verdad, tampoco aprueba.
        t.verdadero("E-18 y no aprueba", not CHECK.aprueba(salida))


def test_e19_lo_institucional_no_satisface(t):
    """E-19 (D1-11) — Active Directory o el OpenID de la DGSEI no son D1."""
    solo_interno = _caso(
        flujos=[{"flowId": "f1", "audience": "INTERNAL",
                 "mechanism": "INSTITUTIONAL_DIRECTORY", "evidenceRefs": ["e1"]}],
        evidencia=[_evidencia_de_flujo(claim="autentica contra el directorio institucional")])
    salida = CHECK.evaluar(solo_interno, _senal("TRUE"))
    t.verdadero("E-19 no aprueba", not CHECK.aprueba(salida))
    t.igual("E-19 el motivo", "CITIZEN_AUTHENTICATION_FLOW_NOT_EVIDENCED", salida["reason"])
    t.contiene("E-19 y lo dice", "institucional", salida["detail"])

    # Y si el flujo ciudadano mismo autentica contra el directorio, contradice la regla.
    ciudadano_institucional = _caso(
        flujos=[{"flowId": "f1", "audience": "CITIZEN",
                 "mechanism": "INSTITUTIONAL_DIRECTORY", "evidenceRefs": ["e1"]}])
    otra = CHECK.evaluar(ciudadano_institucional, _senal("TRUE"))
    t.igual("E-19 el flujo ciudadano institucional falla", "FAIL", otra["state"])


def test_e20_una_dependencia_oidc_no_alcanza(t):
    """E-20 (D1-12) — que la libreria este instalada no dice que el flujo la use."""
    caso = _caso(
        flujos=[{"flowId": "f1", "audience": "CITIZEN", "mechanism": "UNRESOLVED",
                 "evidenceRefs": ["e1"]}],
        evidencia=[_evidencia_de_flujo(tipo="REPOSITORY_CONFIGURATION", ref="package.json",
                                       claim="angular-oauth2-oidc esta en dependencies")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.verdadero("E-20 no aprueba", not CHECK.aprueba(salida))
    t.igual("E-20 el mecanismo queda sin identificar",
            "CITIZEN_AUTHENTICATION_MECHANISM_UNIDENTIFIED", salida["reason"])

    # Y aunque el flujo se declare del GCBA, la dependencia sola no lo sostiene.
    declarado = _caso(evidencia=[_evidencia_de_flujo(
        tipo="REPOSITORY_CONFIGURATION", ref="package.json",
        claim="angular-oauth2-oidc esta en dependencies")])
    t.igual("E-20 la dependencia no sostiene el PASS", "PARTIAL",
            CHECK.evaluar(declarado, _senal("TRUE"))["state"])


def test_e21_la_afirmacion_de_un_agente_no_alcanza(t):
    """E-21 (D1-13) — que un agente lo diga no es evidencia."""
    caso = _caso(evidencia=[_evidencia_de_flujo(
        tipo="AGENT_STATEMENT", ref="dev-integration",
        claim="revise el codigo y esta bien")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-21 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-21 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-21 AGENT_STATEMENT no es fuente suficiente",
                "AGENT_STATEMENT" not in CHECK.FUENTES_SUFICIENTES)


def test_e22_evidencia_de_otro_sistema_no_sostiene(t):
    """E-22 — la evidencia tiene que ser de esta aplicacion y de este ambiente."""
    de_otra_app = _caso(evidencia=[_evidencia_de_flujo(application="otro-sistema")])
    salida = CHECK.evaluar(de_otra_app, _senal("TRUE"))
    t.igual("E-22 no sostiene el PASS", "PARTIAL", salida["state"])
    t.verdadero("E-22 y se dice",
                any("EVIDENCE_OUT_OF_SCOPE" in i for i in salida["issues"]))

    de_otro_ambiente = _caso(evidencia=[_evidencia_de_flujo(environment="DEV")])
    t.igual("E-22 otro ambiente tampoco", "PARTIAL",
            CHECK.evaluar(de_otro_ambiente, _senal("TRUE"))["state"])

    # Una evidencia que no dice de que aplicacion es, es de esta.
    t.igual("E-22 la que no lo dice cuenta", "PASS",
            CHECK.evaluar(_caso(), _senal("TRUE"))["state"])


def test_e23_solo_pass_aprueba(t):
    """E-23 — los otros cuatro estados no son un aprobado."""
    t.igual("E-23 son cinco", 5, len(CHECK.ESTADOS))
    for estado in CHECK.ESTADOS:
        t.igual("E-23 %s" % estado, str(estado == "PASS"),
                str(CHECK.aprueba({"state": estado})))


# -- las fronteras -------------------------------------------------------------

def test_e24_d1_no_es_d2(t):
    """E-24 (D1-14) — la delegacion de credenciales es de D2."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-24 pasa sin decir nada de delegacion", "PASS", salida["state"])
    texto = repr(salida)
    for palabra in ("delegation", "delegacion", "D2", "authentication-delegation"):
        t.verdadero("E-24 el resultado no habla de %s" % palabra, palabra not in texto)

    d1, d2 = c_matriz.regla("D1"), c_matriz.regla("D2")
    t.verdadero("E-24 no comparten check",
                not set(d1["checks"]) & set(d2["checks"]))
    t.verdadero("E-24 ni policy", not set(d1["policies"]) & set(d2["policies"]))
    t.verdadero("E-24 y D2 tiene su propia senal",
                d1["applicability"]["signals"] != d2["applicability"]["signals"])


def test_e25_sin_dev_miba_los_controles_existen(t):
    """E-25 (D1-15) — el hueco de la skill no invalida la instalacion estructural."""
    ruteo = c_reg.resolver_ruteo("dev-integration", "dev-miba")
    t.igual("E-25 dev-miba sigue pendiente", "SPECIALIZED_SKILL_GAP", ruteo["result"])

    informe = c_controles.validar()
    t.igual("E-25 la policy existe", "INSTALLED",
            informe["controls"]["gcba-citizen-authentication-required"])
    t.igual("E-25 el check existe", "INSTALLED",
            informe["controls"]["citizen-authentication-mechanism"])
    t.igual("E-25 y el registro sigue valido", [], informe["schemaErrors"])


def test_e26_la_remediacion_declara_el_hueco(t):
    """E-26 (D1-16) — SPECIALIZED_SKILL_GAP, y D1 sigue sin cumplir."""
    fallado = CHECK.evaluar(
        _caso(flujos=[{"flowId": "f1", "audience": "CITIZEN",
                       "mechanism": "CUSTOM_LOCAL_CREDENTIALS", "evidenceRefs": ["e1"]}]),
        _senal("TRUE"))
    hueco = CHECK.remediacion(fallado)
    t.igual("E-26 el estado", "SPECIALIZED_SKILL_GAP", hueco["state"])
    t.igual("E-26 la skill que falta", "dev-miba", hueco["skill"])
    t.igual("E-26 no hace cumplir a D1", "False", str(hueco["compliant"]))
    t.igual("E-26 el check sigue fallando", "FAIL", fallado["state"])
    t.igual("E-26 con su trazabilidad", "D1", hueco["source"]["rule"])

    t.igual("E-26 lo que pasa no pide remediacion", "None",
            str(CHECK.remediacion(CHECK.evaluar(_caso(), _senal("TRUE")))))


def test_e27_d1_no_crea_dev_miba(t):
    """E-27 (D1-17) — ni el archivo ni una entrada nueva en el registro."""
    antes = c_reg.skill("dev-integration", "dev-miba")
    CHECK.remediacion({"state": "FAIL"})
    despues = c_reg.skill("dev-integration", "dev-miba")

    t.igual("E-27 la skill sigue declarada y no instalada", "DECLARED_NOT_INSTALLED",
            despues["status"])
    t.igual("E-27 con el mismo motivo", antes["reason"], despues["reason"])
    t.verdadero("E-27 y el archivo no existe",
                not (RAIZ / "harnesses" / "desarrollo" / "skills" / "dev-miba").exists())


# Las seis clases que E-28 nombra: client ids, claims, redirect URIs, endpoints, URLs de
# proveedor y configuracion por ambiente. Los de forma de dato van anclados a principio de
# linea a proposito: los propios artefactos nombran esas palabras EN PROSA para negarlas, y un
# patron literal se pondria rojo contra el descargo en vez de contra una fuga.
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

# Fugas verosimiles. La guarda tiene que atrapar las seis clases, no solo las que se
# escriben como codigo: un test de patron que nadie probo contra una fuga real es una
# aserción que se lee severa y no comprueba nada.
FUGAS = (
    ("client id en forma de codigo", "clientId: portal-tramites-prd"),
    ("URL del proveedor", "issuer: https://id.ejemplo.gob.ar"),
    ("endpoint de descubrimiento", "GET /.well-known/openid-configuration"),
    ("bloque de claims", "claims:\n  sub: el identificador del ciudadano\n"),
    ("un claim suelto", "cuil: documento del ciudadano"),
    ("token endpoint", "token endpoint: /protocol/openid-connect/token"),
    ("redirect uri en kebab", "redirect-uri: /callback"),
    ("configuracion por ambiente", "DEV: miba-dev\nUAT: miba-uat\nPRD: miba-prod"),
)

ARTEFACTOS_D1 = ("policies/gcba-citizen-authentication-required.md",
                 "checks/citizen-authentication-mechanism.py")


def test_e28_no_se_inventan_internos_de_miba(t):
    """E-28 — ni client ids, ni claims, ni redirect URIs, ni endpoints, ni valores por ambiente."""
    for relativa in ARTEFACTOS_D1:
        archivo = CONTROLES / Path(relativa)
        texto = io.open(archivo, encoding="utf-8").read()
        for patron in PROHIBIDOS:
            encontrado = re.search(patron, texto)
            t.vacio("E-28 %s sin %s" % (archivo.name, patron),
                    encontrado.group(0).strip() if encontrado else "")

    # Y la guarda sirve: cada fuga puesta en el texto lo pone rojo. Sin esto, el caso
    # afirma seis clases y patrulla las que alguien se acordo de escribir.
    base = io.open(CONTROLES / Path(ARTEFACTOS_D1[0]), encoding="utf-8").read()
    for nombre, fuga in FUGAS:
        contaminado = base + "\n\n" + fuga + "\n"
        t.verdadero("E-28 la guarda atrapa %s" % nombre,
                    any(re.search(p, contaminado) for p in PROHIBIDOS))


# -- la propagacion y la instalacion -------------------------------------------

def test_e29_la_unidad_lleva_la_senal(t):
    """E-29 (D1-18) — valor, estado y evidencia, sin romper lo que ya se consume."""
    unidad = {"id": "u1", "objective": "o", "domain": "integration",
              "requiredCapabilities": [], "dependencies": [], "signals": [],
              "normativeSignals": {"citizenFacing": _senal("TRUE")}}
    documento = c_plan.armar({"objective": "x", "domains": ["integration"], "policies": [],
                              "workUnits": [unidad]}, _CONTEXTO, {}, None)
    n = documento["workUnits"][0]["normative"]

    t.igual("E-29 el valor viaja", "TRUE", n["signals"]["citizenFacing"]["value"])
    t.igual("E-29 la evidencia tambien", "GCBA-1234",
            n["signals"]["citizenFacing"]["evidence"][0]["reference"])
    t.verdadero("E-29 D1 aplica en la unidad", "D1" in n["applicableRules"])
    t.verdadero("E-29 y sigue exigiendo su check",
                "citizen-authentication-mechanism" in n["declaredChecks"])
    t.verdadero("E-29 las listas siguen siendo de strings",
                all(isinstance(x, str) for x in n["declaredPolicies"] + n["declaredChecks"]
                    + n.get("declaredReviews", [])))
    t.vacio("E-29 el plan valida", c_plan.validar(documento))

    # Y una unidad sin senales no cambia de forma.
    sin_senales = {"id": "u1", "objective": "o", "domain": "integration",
                   "requiredCapabilities": [], "dependencies": [], "signals": []}
    otro = c_plan.armar({"objective": "x", "domains": ["integration"], "policies": [],
                         "workUnits": [sin_senales]}, _CONTEXTO, {}, None)
    t.igual("E-29 sin senales no hay ninguna", {},
            otro["workUnits"][0]["normative"]["signals"])
    t.vacio("E-29 y valida igual", c_plan.validar(otro))


def test_e30_los_controles_dejan_de_faltar(t):
    """E-30 (D1-19) — desaparecen de la lista sin tocar la fila de la matriz."""
    resolucion = c_matriz.resolver({"citizenFacing": True})

    sin_nada = c_matriz.controles_no_instalados(resolucion, policies_instaladas=[],
                                                checks_instalados=[], reviews_instaladas=[])
    estados = {f["id"]: f["state"] for f in sin_nada}
    t.igual("E-30 antes la policy", "DECLARED_POLICY_NOT_INSTALLED",
            estados.get("gcba-citizen-authentication-required"))
    t.igual("E-30 antes el check", "DECLARED_CHECK_NOT_INSTALLED",
            estados.get("citizen-authentication-mechanism"))

    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    t.verdadero("E-30 despues la policy no falta",
                "gcba-citizen-authentication-required" not in faltan)
    t.verdadero("E-30 despues el check no falta",
                "citizen-authentication-mechanism" not in faltan)

    d1 = c_matriz.regla("D1")
    t.igual("E-30 la fila no cambio", ["gcba-citizen-authentication-required"], d1["policies"])
    t.igual("E-30 ni sus checks", ["citizen-authentication-mechanism"], d1["checks"])
    t.igual("E-30 ni su modo", "CONDITIONAL", d1["applicability"]["mode"])


def test_e31_la_traza_se_conserva(t):
    """E-31 (D1-20) — ES0901 / 6.3 / 7.1 / D1 en todo lo que D1 emite."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    for campo, esperado in TRAZA.items():
        t.igual("E-31 el check: %s" % campo, esperado, salida["source"][campo])

    t.igual("E-31 la trazabilidad de la matriz", TRAZA, c_matriz.trazabilidad("D1"))

    senal_con_traza = _senal("TRUE", source=dict(TRAZA))
    t.igual("E-31 la senal la conserva", "D1",
            c_senales.resolver_una(senal_con_traza)["source"]["rule"])

    policy = io.open(CONTROLES / "policies" / "gcba-citizen-authentication-required.md",
                     encoding="utf-8").read()
    t.contiene("E-31 la policy dice su regla", "rule: D1", policy)
    t.contiene("E-31 y su estandar", 'standard: ES0901', policy)

    declarado = c_controles.control("citizen-authentication-mechanism")
    t.igual("E-31 el registro tambien", "D1", declarado["source"]["rule"])
    t.igual("E-31 con su version", "6.3", declarado["source"]["version"])
