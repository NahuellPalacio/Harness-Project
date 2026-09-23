# ES0902 §3 C2: la aprobacion de seguridad en QA, atada al artefacto y revalidada por el Anexo V.
#
# Escenarios E-01 a E-56 de docs/cambios/es0902-c2-aprobacion-de-seguridad-en-qa/spec.md. E-nn es
# el C2-nn del pedido de instalacion.
#
# 🔴 Lo que se verifica es que C2 NO se pueda poner en verde barato: que apruebe algo interno, que
# valga otro ambiente, que valga otro release porque se parece, que se reuse una aprobacion vieja
# sin mirar que cambio, y que un parcial se lea como total.
#
# 🔴 APROBACION + CANDIDATO + REEVALUACION es el caso que APRUEBA, y casi todo sale de romperlo.
# E-14 lo mira en PASS: si dejara de aprobar, lo demas seguiria verde sin verificar nada.
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
from orquestacion import normativa                      # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "qa-security-approval-evidence.py"
RUTA_O2 = CONTROLES / "checks" / "security-control-authority-evidence.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "c2_aprobacion")
O2 = _cargar(RUTA_O2, "c2_o2_autoridad")
MATRIZ = seguridad.cargar()
REGISTRO = c_controles.cargar()

POLICY = "qa-security-approval-required"
CHEQUEO = "qa-security-approval-evidence"

LOS_17 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "SECURITY_APPROVAL_REQUIRED", "SECURITY_APPROVAL_EVIDENCE_UNRESOLVED",
          "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED", "SECURITY_APPROVAL_NOT_IN_QA",
          "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED", "SECURITY_APPROVAL_SCOPE_UNRESOLVED",
          "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED", "SECURITY_REASSESSMENT_REQUIRED",
          "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED", "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
          "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED", "SECURITY_APPROVAL_EVIDENCE_CHANGED",
          "ASSESSMENT_VALIDITY_UNRESOLVED")

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": "C2"}
ANEXO_V = {"standard": "ES0901", "version": "6.3", "section": "Anexo V"}

# El O2 que resuelve: una autoridad del GCABA, vigente, para el proyecto `tramites`.
AUTORIDAD_O2 = O2.evaluar({
    "target": {"id": "tramites-web", "scope": {"type": "PROJECT", "value": "tramites"}},
    "evaluationDate": "2026-09-22",
    "authorities": [{"authorityId": "aut-1",
                     "organization": {"name": "Direccion General de Seguridad de la Informacion",
                                      "gcabaMembership": "VERIFIED"},
                     "responsibilities": ["SECURITY_CONTROL"],
                     "scope": {"type": "PROJECT", "value": "tramites"},
                     "effectiveFrom": "2026-01-01", "effectiveTo": "2027-01-01",
                     "evidence": [{"sourceType": "OFFICIAL_GCBA_DOCUMENT",
                                   "reference": "acta 12/2026"}]}]})

# 🔴 La aprobacion que APRUEBA.
APROBACION = {
    "approvalId": "apr-1", "projectId": "tramites", "applicationId": "tramites-web",
    "environment": "QA", "status": "APPROVED", "assessmentType": "FULL",
    "assessmentDate": "2026-09-10", "assessmentId": "ASM-77",
    "provenanceClass": "EXTERNAL_GCABA_SECURITY_AUTHORITY",
    "authorityEvidence": ["aut-1", "acta-dgsei-77"], "scope": ["frontend", "api"],
    "artifact": {"repository": "gitlab/tramites", "commitSha": "abc123", "buildId": None,
                 "artifactDigest": None, "imageDigest": "sha256:img1", "releaseId": "1.4.0"},
    "evidenceReference": "informe DGSEI ASM-77", "evidenceFingerprint": None,
}
CANDIDATO = {"projectId": "tramites", "applicationId": "tramites-web",
             "scope": ["frontend", "api"],
             "artifact": {"repository": "gitlab/tramites", "branch": "release/1.4",
                          "commitSha": "abc123", "imageDigest": "sha256:img1",
                          "releaseId": "1.4.0"}}
REEVALUACION = {"evaluationDate": "2026-09-22", "development": False, "complete": True,
                "changes": []}

_POR_DEFECTO = object()


def _apr(**cambios):
    a = copy.deepcopy(APROBACION)
    a.update(cambios)
    return a


def _cand(**cambios):
    c = copy.deepcopy(CANDIDATO)
    c.update(cambios)
    return c


def _caso(aprobaciones=None, candidato=None, reevaluacion=None, **extra):
    caso = {"registry": {"version": "1.0",
                         "approvals": copy.deepcopy([APROBACION] if aprobaciones is None
                                                    else aprobaciones)},
            "candidate": copy.deepcopy(CANDIDATO if candidato is None else candidato),
            "reassessment": copy.deepcopy(REEVALUACION if reevaluacion is None
                                          else reevaluacion)}
    caso.update(copy.deepcopy(extra))
    return caso


def _ev(*a, senal=True, autoridad=_POR_DEFECTO, **k):
    return CHECK.evaluar(_caso(*a, **k), senal,
                         AUTORIDAD_O2 if autoridad is _POR_DEFECTO else autoridad)


def _estado(*a, **k):
    return _ev(*a, **k)["state"]


def _cambiado(*cambios, development=None, evaluacion="2026-09-22"):
    """Un candidato que es OTRO commit, con el change set completo desde el aprobado."""
    candidato = _cand(artifact={"repository": "gitlab/tramites", "branch": "release/1.4",
                                "commitSha": "def456"})
    return {"candidato": candidato,
            "changeSet": {"from": {"commitSha": "abc123"}, "to": {"commitSha": "def456"},
                          "complete": True},
            "reevaluacion": {"evaluationDate": evaluacion, "development": development,
                             "complete": True, "changes": list(cambios)}}


def _cambio(categoria, cid="MR-1", quien="DETERMINISTIC", cuando="2026-09-15"):
    return {"changeId": cid, "category": categoria, "classifiedBy": quien, "date": cuando,
            "evidence": "gitlab %s" % cid}


def _con_cambios(*cambios, **k):
    c = _cambiado(*cambios, **k)
    return _ev(candidato=c["candidato"], reevaluacion=c["reevaluacion"],
               changeSet=c["changeSet"])


def _valores(dato):
    if isinstance(dato, dict):
        return [x for v in dato.values() for x in _valores(v)]
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


def _literales(ruta):
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


def _registro_valida(aprobacion):
    return not CHECK.validar_schema({"version": "1.0", "approvals": [aprobacion]})


# -- La fila -------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (C2-01)."""
    t.igual("E-01 la matriz", "ES0902.C2", seguridad.regla("C2", MATRIZ)["ruleKey"])
    t.igual("E-01 el check", "ES0902.C2", _ev()["ruleKey"])


def test_e02_la_senal(t):
    """E-02 (C2-02)."""
    t.igual("E-02 la matriz", ["securityHomologationPresent"],
            seguridad.regla("C2", MATRIZ)["applicability"]["signals"])
    t.igual("E-02 el check", "securityHomologationPresent", CHECK.SENAL)


def test_e03_agente_policy_check(t):
    """E-03 (C2-03)."""
    c2 = seguridad.regla("C2", MATRIZ)
    t.igual("E-03 el agente", ["dev-security"], c2["primaryAgents"])
    t.igual("E-03 la policy", [POLICY], c2["policies"])
    t.igual("E-03 el check", [CHEQUEO], c2["checks"])
    t.igual("E-03 el check se llama asi", CHEQUEO, CHECK.CONTROL)


def test_e04_nada_inventado(t):
    """E-04 (C2-04)."""
    registro = c_reg.cargar()
    t.igual("E-04 diez agentes", 10, len(registro["agents"]))
    de_security = [a for a in registro["agents"] if a["id"] == "dev-security"][0]
    t.igual("E-04 las cuatro skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in de_security.get("skills") or []))
    t.igual("E-04 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-04 cero reviews en la fila", [], seguridad.regla("C2", MATRIZ)["reviews"])
    t.igual("E-04 ningun control de C2 es REVIEW", [],
            [c["id"] for c in REGISTRO["controls"] if c["rule"] == "C2" and c["type"] == "REVIEW"])


def test_e05_sin_senal(t):
    """E-05 (C2-05)."""
    estado, faltan = seguridad.resolver_regla(seguridad.regla("C2", MATRIZ), {})
    t.igual("E-05 la matriz", "APPLICABILITY_UNRESOLVED", estado)
    t.igual("E-05 dice cual", ["securityHomologationPresent"], faltan)
    for sin in (None, "UNRESOLVED", {"value": None}):
        t.igual("E-05 el check con %r" % (sin,), "APPLICABILITY_UNRESOLVED", _estado(senal=sin))


def test_e06_senal_en_falso(t):
    """E-06 (C2-06)."""
    estado, _ = seguridad.resolver_regla(seguridad.regla("C2", MATRIZ),
                                         {"securityHomologationPresent": False})
    t.igual("E-06 la matriz", "NOT_APPLICABLE", estado)
    t.igual("E-06 el check", "NOT_APPLICABLE", _estado(senal=False))


def test_e07_sin_aprobacion_no_es_no_aplica(t):
    """E-07 (C2-07)."""
    t.igual("E-07 registro vacio con la senal en verdadero", "SECURITY_APPROVAL_REQUIRED",
            _estado([]))
    instalado = json.loads((REGLAS / "security-approval-evidence.json").read_text(encoding="utf-8"))
    t.igual("E-07 el registro se instala vacio", [], instalado["approvals"])
    t.igual("E-07 y valida", [], CHECK.validar_schema(instalado))
    t.igual("E-07 el instalado da lo mismo", "SECURITY_APPROVAL_REQUIRED",
            CHECK.evaluar({"candidate": CANDIDATO}, True, AUTORIDAD_O2)["state"])


# -- Nada interno aprueba ------------------------------------------------------

def test_e08_dev_security_no_aprueba(t):
    """E-08 (C2-08)."""
    for interno in ("DEV_SECURITY_AGENT", "dev-security", "HARNESS_REVIEW", "HARNESS_CHECK"):
        t.verdadero("E-08 la procedencia `%s` no se puede escribir" % interno,
                    not _registro_valida(_apr(provenanceClass=interno)))
    t.igual("E-08 escrita como UNRESOLVED no aprueba", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado([_apr(provenanceClass="UNRESOLVED")]))
    t.igual("E-08 estado_oficial con el agente", "OFFICIAL_STATUS_UNRESOLVED",
            evaluacion.estado_oficial({"state": "APPROVED", "producer": "DEV_SECURITY_AGENT",
                                       "evidence": ["x"]})["state"])


def test_e09_un_escaneo_no_aprueba(t):
    """E-09 (C2-09)."""
    t.igual("E-09 un escaneo limpio no cambia nada", "SECURITY_APPROVAL_REQUIRED",
            _estado([], internalResults=["SCAN_CLEAN"]))
    t.igual("E-09 AUTOMATED_SCAN no emite APPROVED", "OFFICIAL_STATUS_UNRESOLVED",
            evaluacion.estado_oficial({"state": "APPROVED", "producer": "AUTOMATED_SCAN",
                                       "evidence": ["x"]})["state"])
    t.verdadero("E-09 ni se escribe como procedencia",
                not _registro_valida(_apr(provenanceClass="AUTOMATED_SCAN")))


def test_e10_un_ci_verde_no_aprueba(t):
    """E-10 (C2-10)."""
    t.igual("E-10 un CI verde no cambia nada", "SECURITY_APPROVAL_REQUIRED",
            _estado([], internalResults=["CI_GREEN"]))
    t.verdadero("E-10 ni se escribe como procedencia",
                not _registro_valida(_apr(provenanceClass="CI_PIPELINE")))
    t.igual("E-10 resultados internos que no son lista no rompen", "SECURITY_APPROVAL_REQUIRED",
            _estado([], internalResults=5))
    t.contiene("E-10 y se informa como no considerado", "CI_GREEN",
               " | ".join(_ev([], internalResults=["CI_GREEN"])["issues"]))


def test_e11_ready_to_request_no_alcanza(t):
    """E-11 (C2-11)."""
    for interno in ("READY_TO_REQUEST", "READY_TO_RESUBMIT", "INTERNAL_REVIEW_COMPLETE"):
        t.verdadero("E-11 `%s` no es un estado de aprobacion" % interno,
                    not _registro_valida(_apr(status=interno)))
        t.igual("E-11 `%s` como resultado interno no cambia nada" % interno,
                "SECURITY_APPROVAL_REQUIRED", _estado([], internalResults=[interno]))


def test_e12_el_umbral_de_g2_no_alcanza(t):
    """E-12 (C2-12)."""
    t.igual("E-12 G2_THRESHOLD_SATISFIED solo", "SECURITY_APPROVAL_REQUIRED",
            _estado([], internalResults=["G2_THRESHOLD_SATISFIED"]))
    literales = {lit.lower() for lit in _literales(RUTA_CHECK)}
    for g2 in ("findings", "riskmapping", "severity", "threshold"):
        t.verdadero("E-12 el modulo no mira `%s`" % g2,
                    not any(g2 in lit for lit in literales))
    t.verdadero("E-12 no importa evaluacion", "evaluacion" not in _importados(RUTA_CHECK))


def test_e13_procedencia_externa(t):
    """E-13 (C2-13) — las tres formas de no tenerla."""
    t.igual("E-13 sin procedencia externa", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado([_apr(provenanceClass="UNRESOLVED")]))
    sin_o2 = O2.evaluar({"target": {"id": "x", "scope": {"type": "PROJECT", "value": "tramites"}},
                         "evaluationDate": "2026-09-22", "authorities": []})
    t.igual("E-13 O2 sin resolver", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado(autoridad=sin_o2))
    t.igual("E-13 O2 ausente", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED", _estado(autoridad=None))
    t.igual("E-13 sin citar la autoridad de O2", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado([_apr(authorityEvidence=["acta-dgsei-77"])]))
    # O2 en PASS para OTRO alcance no es procedencia de esto, y un O2 torcido no cuenta.
    de_otro = O2.evaluar({"target": {"id": "lic", "scope": {"type": "PROJECT", "value": "licencias"}},
                          "evaluationDate": "2026-09-22",
                          "authorities": [{"authorityId": "aut-1",
                                           "organization": {"name": "DGSI",
                                                            "gcabaMembership": "VERIFIED"},
                                           "responsibilities": ["SECURITY_CONTROL"],
                                           "scope": {"type": "PROJECT", "value": "licencias"},
                                           "effectiveFrom": "2026-01-01",
                                           "effectiveTo": "2027-01-01",
                                           "evidence": [{"sourceType": "OFFICIAL_GCBA_DOCUMENT",
                                                         "reference": "acta"}]}]})
    t.igual("E-13 O2 de otro alcance esta en PASS", "PASS", de_otro["state"])
    t.igual("E-13 y no es procedencia de tramites", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado(autoridad=de_otro))
    # 🔴 El caso del segundo pase: la aplicacion HERMANA del mismo proyecto. Su cadena contiene
    # al proyecto, y la autoridad que O2 resolvio cubre solo a la hermana.
    hermana = O2.evaluar({"target": {"id": "tramites-bo",
                                     "scope": {"type": "APPLICATION", "value": "tramites-bo"},
                                     "within": [{"type": "PROJECT", "value": "tramites"}]},
                          "evaluationDate": "2026-09-22",
                          "authorities": [{"authorityId": "aut-9",
                                           "organization": {"name": "DGSI",
                                                            "gcabaMembership": "VERIFIED"},
                                           "responsibilities": ["SECURITY_CONTROL"],
                                           "scope": {"type": "APPLICATION",
                                                     "value": "tramites-bo"},
                                           "effectiveFrom": "2026-01-01",
                                           "effectiveTo": "2027-01-01",
                                           "evidence": [{"sourceType": "OFFICIAL_GCBA_DOCUMENT",
                                                         "reference": "acta"}]}]})
    t.igual("E-13 O2 de la hermana esta en PASS", "PASS", hermana["state"])
    t.igual("E-13 y no es procedencia de tramites-web", "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado([_apr(authorityEvidence=["aut-9"])], autoridad=hermana))
    otro_proyecto = dict(AUTORIDAD_O2, scopeChain=[{"type": "APPLICATION", "value": "tramites-web"},
                                                    {"type": "PROJECT", "value": "licencias"}])
    t.igual("E-13 ni una cadena que contradice el proyecto del candidato",
            "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado(autoridad=otro_proyecto))
    t.igual("E-13 ni un eslabon de otro tipo con el mismo valor",
            "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
            _estado(autoridad=dict(AUTORIDAD_O2,
                                   scopeChain=[{"type": "ORGANIZATION", "value": "tramites"}])))
    for nombre, torcido in (("forjado sin cadena", {"state": "PASS",
                                                    "authority": {"authorityId": "aut-1"}}),
                            ("authority string", {"state": "PASS", "authority": "aut-1",
                                                  "scopeChain": [{"value": "tramites"}]}),
                            ("cadena torcida", {"state": "PASS",
                                                "authority": {"authorityId": "aut-1"},
                                                "scopeChain": "tramites"})):
        t.igual("E-13 O2 %s no cuenta" % nombre, "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED",
                _estado(autoridad=torcido))


# -- QA ------------------------------------------------------------------------

def test_e14_qa_aprueba(t):
    """E-14 (C2-14) — el caso base, que tiene que aprobar."""
    r = _ev()
    t.igual("E-14 pasa", "PASS", r["state"])
    t.verdadero("E-14 aprueba", CHECK.aprueba(r))
    t.igual("E-14 relacion exacta", "EXACT", r["assessedArtifactRelation"])
    t.igual("E-14 sin revalidacion", False, r["reassessment"]["required"])


def test_e15_dev(t):
    """E-15 (C2-15)."""
    t.igual("E-15 DEV", "SECURITY_APPROVAL_NOT_IN_QA", _estado([_apr(environment="DEV")]))


def test_e16_hml(t):
    """E-16 (C2-16)."""
    t.igual("E-16 HML", "SECURITY_APPROVAL_NOT_IN_QA", _estado([_apr(environment="HML")]))


def _regla(ambiente):
    ev = {"environment": ambiente,
          "officialApproval": {"state": "APPROVED", "producer": "GCBA_DGSEI",
                               "evidence": ["acta"]},
          "controlResults": {c: {"result": "PASS", "evidence": ["x"]} for c in (POLICY, CHEQUEO)}}
    return seguridad.resultado("C2", ev, {"securityHomologationPresent": True}, MATRIZ)


def test_e17_prd(t):
    """E-17 (C2-17)."""
    t.igual("E-17 PRD", "SECURITY_APPROVAL_NOT_IN_QA", _estado([_apr(environment="PRD")]))
    t.igual("E-17 OTHER", "SECURITY_APPROVAL_NOT_IN_QA", _estado([_apr(environment="OTHER")]))
    r = _regla("PRD")
    t.verdadero("E-17 la regla no cumple en PRD", r["result"] != "COMPLIANT")
    t.contiene("E-17 con el mismo nombre", "SECURITY_APPROVAL_NOT_IN_QA", repr(r["states"]))


def test_e18_ambiente_sin_resolver(t):
    """E-18 (C2-18)."""
    t.igual("E-18 el check", "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED",
            _estado([_apr(environment="UNRESOLVED")]))
    for ambiente in (None, "UNRESOLVED", "qa"):
        r = _regla(ambiente)
        t.contiene("E-18 la regla con %r" % (ambiente,),
                   "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED", repr(r["states"]))
    t.igual("E-18 y en QA la regla cumple", "COMPLIANT", _regla("QA")["result"])


# -- El sujeto y el artefacto --------------------------------------------------

def test_e19_otro_proyecto_falla(t):
    """E-19 (C2-19)."""
    t.igual("E-19 otro proyecto", "FAIL", _estado([_apr(projectId="licencias")]))
    t.igual("E-19 otra aplicacion", "FAIL", _estado([_apr(applicationId="tramites-bo")]))


def test_e20_alcance_sin_resolver(t):
    """E-20 (C2-20)."""
    t.igual("E-20 alcance vacio", "SECURITY_APPROVAL_SCOPE_UNRESOLVED", _estado([_apr(scope=[])]))
    t.igual("E-20 sin cubrir el del candidato", "SECURITY_APPROVAL_SCOPE_UNRESOLVED",
            _estado(candidato=_cand(scope=["frontend", "api", "admin"])))
    t.igual("E-20 candidato sin alcance", "SECURITY_APPROVAL_SCOPE_UNRESOLVED",
            _estado(candidato=_cand(scope="frontend")))
    t.igual("E-20 un alcance vacio no cubre a otro vacio", "SECURITY_APPROVAL_SCOPE_UNRESOLVED",
            _estado([_apr(scope=[""])], candidato=_cand(scope=[""])))
    t.igual("E-20 candidato sin identidad", "SECURITY_APPROVAL_SCOPE_UNRESOLVED",
            _estado(candidato=_cand(projectId=None)))


def test_e21_la_rama_no_alcanza(t):
    """E-21 (C2-21)."""
    solo_repo = _apr(artifact={"repository": "gitlab/tramites", "commitSha": None,
                               "buildId": None, "artifactDigest": None, "imageDigest": None,
                               "releaseId": None})
    t.igual("E-21 mismo repo y misma rama", "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED",
            _estado([solo_repo]))
    t.igual("E-21 sin artefacto", "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED",
            _estado([_apr(artifact=None)]))
    t.verdadero("E-21 la rama no es un identificador", "branch" not in CHECK.INMUTABLES)


def test_e22_identidad_exacta(t):
    """E-22 (C2-22)."""
    for clave, valor in (("commitSha", "abc123"), ("imageDigest", "sha256:img1"),
                         ("releaseId", "1.4.0")):
        artefacto = {k: None for k in ("commitSha", "buildId", "artifactDigest", "imageDigest",
                                       "releaseId")}
        artefacto[clave] = valor
        r = _ev([_apr(artifact=artefacto)])
        t.igual("E-22 `%s` solo establece EXACT" % clave, "EXACT", r["assessedArtifactRelation"])
        t.igual("E-22 y pasa con `%s`" % clave, "PASS", r["state"])
    contradice = _cand(artifact=dict(CANDIDATO["artifact"], imageDigest="sha256:otra"))
    t.igual("E-22 mismo commit y otro digest no es EXACT",
            "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED", _estado(candidato=contradice))


def test_e23_relacion_sin_resolver(t):
    """E-23 (C2-23)."""
    otro = _cand(artifact={"commitSha": "def456"})
    t.igual("E-23 otro commit sin change set", "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED",
            _estado(candidato=otro))
    incompleto = {"from": {"commitSha": "abc123"}, "to": {"commitSha": "def456"},
                  "complete": False}
    t.igual("E-23 con change set incompleto", "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED",
            _estado(candidato=otro, changeSet=incompleto))
    otro_origen = {"from": {"commitSha": "zzz"}, "to": {"commitSha": "def456"}, "complete": True}
    t.igual("E-23 con un change set que no sale del aprobado",
            "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED",
            _estado(candidato=otro, changeSet=otro_origen))


def test_e24_una_vieja_no_se_reusa_a_ciegas(t):
    """E-24 (C2-24)."""
    r = _con_cambios(_cambio("DEPENDENCY_CHANGED"))
    t.igual("E-24 superada por el cambio", "SUPERSEDED_BY_CHANGE", r["assessedArtifactRelation"])
    t.igual("E-24 hay que reevaluar", "SECURITY_REASSESSMENT_REQUIRED", r["state"])
    vieja = _apr(approvalId="apr-0", assessmentDate="2026-08-01")
    nueva = _apr(approvalId="apr-2", assessmentDate="2026-09-12", status="REJECTED")
    t.igual("E-24 una aprobada vieja no tapa a una rechazada nueva", "FAIL",
            _estado([vieja, nueva]))
    # 🔴 El caso del primer pase: una rechazada mas nueva con la fecha mal escrita no se ordena
    # por texto ni se descarta. Sin todas las fechas no se sabe cual es la mas reciente.
    for fecha in (" 2026-09-30", "12/09/2026", "", "2026-13-01"):
        rechazada = _apr(approvalId="apr-2", assessmentDate=fecha, status="REJECTED")
        t.igual("E-24 una rechazada con fecha %r no desaparece" % fecha,
                "SECURITY_APPROVAL_EVIDENCE_UNRESOLVED", _estado([APROBACION, rechazada]))
    # Ni una rechazada con el sujeto escrito de otra forma.
    # 🔴 El caso del tercer pase: la forma no se acota a espacios y mayusculas. Un caracter
    # invisible, un acento o un separador distinto son el mismo sujeto escrito de otra forma.
    for campo, valor in (("projectId", "tramites "), ("applicationId", "Tramites-Web"),
                         ("projectId", "tramites\u200b"), ("projectId", "trámites"),
                         ("projectId", "tra mites"), ("applicationId", "tramites_web"),
                         ("applicationId", "tramites web"), ("applicationId", "tramites\u2013web"),
                         ("projectId", "tramites\u00a0"), ("projectId", "\ttramites")):
        rechazada = _apr(approvalId="apr-2", assessmentDate="2026-09-12", status="REJECTED")
        rechazada[campo] = valor
        t.igual("E-24 una rechazada con %s=%r no desaparece" % (campo, valor),
                "SECURITY_APPROVAL_EVIDENCE_UNRESOLVED", _estado([APROBACION, rechazada]))


# -- Los motivos del Anexo V ---------------------------------------------------

def test_e25_desarrollo_y_mas_de_20_dias(t):
    """E-25 (C2-25)."""
    r = _ev(reevaluacion=dict(REEVALUACION, development=True, evaluationDate="2026-10-15"))
    t.igual("E-25 hay que reevaluar", "SECURITY_REASSESSMENT_REQUIRED", r["state"])
    t.igual("E-25 por el desarrollo", ["DEVELOPMENT_OVER_20_DAYS"],
            [m["type"] for m in r["reassessment"]["triggers"]])
    t.igual("E-25 a los 20 justos no", "PASS",
            _estado(reevaluacion=dict(REEVALUACION, development=True,
                                      evaluationDate="2026-09-30")))


def test_e26_los_20_dias_van_con_el_desarrollo(t):
    """E-26 (C2-26)."""
    t.igual("E-26 sin desarrollo, 35 dias, no es motivo", "PASS",
            _estado(reevaluacion=dict(REEVALUACION, development=False,
                                      evaluationDate="2026-10-15")))
    t.igual("E-26 sin saber si hubo desarrollo", "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
            _estado(reevaluacion=dict(REEVALUACION, development=None,
                                      evaluationDate="2026-10-15")))
    t.igual("E-26 con desarrollo y sin fecha de evaluacion", "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
            _estado(reevaluacion=dict(REEVALUACION, development=True, evaluationDate=None)))
    c = _cambiado(_cambio("DEPENDENCY_CHANGED"), development=False)
    t.igual("E-26 dice que no hubo y trae cambios", "SECURITY_REASSESSMENT_REQUIRED",
            _ev(candidato=c["candidato"], reevaluacion=c["reevaluacion"],
                changeSet=c["changeSet"])["state"])
    # 🔴 El caso del primer pase: un `development` que no se reconoce es no saberlo.
    for raro in ("yes", 1, "true", [], {}):
        t.igual("E-26 development=%r a los 35 dias" % (raro,), "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
                _estado(reevaluacion=dict(REEVALUACION, development=raro,
                                          evaluationDate="2026-10-15")))
    # Y otro commit ES desarrollo: no se esquiva con un change set vacio.
    c0 = _cambiado(development=None, evaluacion="2026-10-15")
    t.igual("E-26 otro commit, change set vacio, 35 dias", "SECURITY_REASSESSMENT_REQUIRED",
            _ev(candidato=c0["candidato"], reevaluacion=c0["reevaluacion"],
                changeSet=c0["changeSet"])["state"])
    c1 = _cambiado(development=False, evaluacion="2026-10-15")
    t.igual("E-26 otro commit que declara que no hubo desarrollo",
            "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
            _ev(candidato=c1["candidato"], reevaluacion=c1["reevaluacion"],
                changeSet=c1["changeSet"])["state"])
    t.igual("E-26 una evaluacion anterior al assessment no es una edad",
            "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
            _estado(reevaluacion=dict(REEVALUACION, development=True,
                                      evaluationDate="2026-09-01")))
    t.contiene("E-26 y la contradiccion queda dicha", "ASSESSMENT_AGE_CONTEXT_UNRESOLVED",
               repr(_ev(candidato=c["candidato"], reevaluacion=c["reevaluacion"],
                        changeSet=c["changeSet"])["reassessment"]["states"]))


def _un_motivo(t, escenario, categoria):
    r = _con_cambios(_cambio(categoria))
    t.igual("%s `%s` obliga a reevaluar" % (escenario, categoria),
            "SECURITY_REASSESSMENT_REQUIRED", r["state"])
    t.igual("%s `%s` sale con su evidencia" % (escenario, categoria),
            [(categoria, "gitlab MR-1")],
            [(m["type"], m["evidence"]) for m in r["reassessment"]["triggers"]])


def test_e27_remediacion(t):
    """E-27 (C2-27)."""
    _un_motivo(t, "E-27", "VULNERABILITY_REMEDIATION")


def test_e28_incidente(t):
    """E-28 (C2-28)."""
    _un_motivo(t, "E-28", "SECURITY_INCIDENT")


def test_e29_funcionalidad(t):
    """E-29 (C2-29)."""
    _un_motivo(t, "E-29", "FUNCTIONALITY_CHANGED")


def test_e30_endpoint(t):
    """E-30 (C2-30)."""
    _un_motivo(t, "E-30", "ENDPOINT_ADDED_OR_MODIFIED")
    # Y la seccion eliminada, que el pedido no numero y el Anexo V si nombra.
    _un_motivo(t, "E-30", "FRONTEND_OR_BACKEND_SECTION_REMOVED")


def test_e31_parametros(t):
    """E-31 (C2-31)."""
    _un_motivo(t, "E-31", "FORM_OR_API_PARAMETER_CHANGED")


def test_e32_integracion_externa(t):
    """E-32 (C2-32)."""
    _un_motivo(t, "E-32", "EXTERNAL_INTEGRATION_CHANGED")


def test_e33_iframe(t):
    """E-33 (C2-33)."""
    _un_motivo(t, "E-33", "IFRAME_OR_EXTERNAL_EMBED_ADDED")


def test_e34_script_de_terceros(t):
    """E-34 (C2-34)."""
    _un_motivo(t, "E-34", "THIRD_PARTY_SCRIPT_ADDED")


def test_e35_politica_de_seguridad(t):
    """E-35 (C2-35)."""
    _un_motivo(t, "E-35", "SECURITY_POLICY_CHANGED")


def test_e36_roles(t):
    """E-36 (C2-36)."""
    _un_motivo(t, "E-36", "ROLE_OR_PERMISSION_CHANGED")


def test_e37_dependencias(t):
    """E-37 (C2-37)."""
    _un_motivo(t, "E-37", "DEPENDENCY_CHANGED")


def test_e38_infraestructura(t):
    """E-38 (C2-38)."""
    _un_motivo(t, "E-38", "INFRASTRUCTURE_MIGRATED")


def test_e39_protocolo(t):
    """E-39 (C2-39)."""
    _un_motivo(t, "E-39", "COMMUNICATION_PROTOCOL_CHANGED")


def test_e40_archivos(t):
    """E-40 (C2-40)."""
    _un_motivo(t, "E-40", "FILE_UPLOAD_OR_DOWNLOAD_ADDED")


def test_e41_flujo_sensible(t):
    """E-41 (C2-41)."""
    _un_motivo(t, "E-41", "SENSITIVE_FLOW_CHANGED")


def test_e42_autenticacion(t):
    """E-42 (C2-42) — y los dieciocho, clavados por literal."""
    _un_motivo(t, "E-42", "AUTHENTICATION_FLOW_CHANGED")
    t.igual("E-42 los dieciocho motivos",
            sorted(("DEVELOPMENT_OVER_20_DAYS", "VULNERABILITY_REMEDIATION", "SECURITY_INCIDENT",
                    "FUNCTIONALITY_CHANGED", "ENDPOINT_ADDED_OR_MODIFIED",
                    "FRONTEND_OR_BACKEND_SECTION_REMOVED", "FORM_OR_API_PARAMETER_CHANGED",
                    "EXTERNAL_INTEGRATION_CHANGED", "IFRAME_OR_EXTERNAL_EMBED_ADDED",
                    "THIRD_PARTY_SCRIPT_ADDED", "SECURITY_POLICY_CHANGED",
                    "ROLE_OR_PERMISSION_CHANGED", "DEPENDENCY_CHANGED", "INFRASTRUCTURE_MIGRATED",
                    "COMMUNICATION_PROTOCOL_CHANGED", "FILE_UPLOAD_OR_DOWNLOAD_ADDED",
                    "SENSITIVE_FLOW_CHANGED", "AUTHENTICATION_FLOW_CHANGED")),
            sorted(CHECK.MOTIVOS))


def test_e43_varios_motivos_salen_todos(t):
    """E-43 (C2-43)."""
    r = _con_cambios(_cambio("AUTHENTICATION_FLOW_CHANGED", "MR-2"),
                     _cambio("DEPENDENCY_CHANGED", "MR-1"),
                     evaluacion="2026-10-15")
    t.igual("E-43 los tres, con su evidencia",
            [("DEVELOPMENT_OVER_20_DAYS", None), ("DEPENDENCY_CHANGED", "gitlab MR-1"),
             ("AUTHENTICATION_FLOW_CHANGED", "gitlab MR-2")],
            [(m["type"], m["evidence"] if m["changeId"] else None)
             for m in r["reassessment"]["triggers"]])
    t.igual("E-43 y required es verdadero, no un opaco", True, r["reassessment"]["required"])


def test_e44_clasificacion_ambigua(t):
    """E-44 (C2-44)."""
    for nombre, cambio in (("una categoria fuera de la lista", _cambio("MISC")),
                           ("sin categoria", dict(_cambio("MISC"), category=None)),
                           ("sin evidencia", dict(_cambio("DEPENDENCY_CHANGED"), evidence=None))):
        r = _con_cambios(cambio)
        t.igual("E-44 %s" % nombre, "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED", r["state"])
    c = _cambiado()
    c["reevaluacion"]["changes"] = "DEPENDENCY_CHANGED"
    t.contiene("E-44 changes que no es una lista", "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED",
               repr(_ev(candidato=c["candidato"], reevaluacion=c["reevaluacion"],
                        changeSet=c["changeSet"])["reassessment"]["states"]))


def test_e45_un_modelo_no_suprime(t):
    """E-45 (C2-45)."""
    t.igual("E-45 NOT_A_TRIGGER de un modelo", "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED",
            _con_cambios(_cambio("NOT_A_TRIGGER", quien="MODEL"))["state"])
    t.igual("E-45 sin clasificador tampoco", "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED",
            _con_cambios(_cambio("NOT_A_TRIGGER", quien=None))["state"])
    for quien in ("HUMAN", "DETERMINISTIC"):
        t.igual("E-45 de `%s` vale" % quien, "PASS",
                _con_cambios(_cambio("NOT_A_TRIGGER", quien=quien))["state"])
    t.igual("E-45 y un modelo si puede sumar un motivo", "SECURITY_REASSESSMENT_REQUIRED",
            _con_cambios(_cambio("DEPENDENCY_CHANGED", quien="MODEL"))["state"])


def test_e46_reuso_permitido(t):
    """E-46 (C2-46)."""
    r = CHECK.revalidacion("2026-09-10", REEVALUACION)
    t.igual("E-46 evidencia completa, ningun motivo", "REUSE_ALLOWED", r["result"])
    t.igual("E-46 required falso", False, r["required"])
    t.igual("E-46 sin evidencia completa no", "ASSESSMENT_VALIDITY_UNRESOLVED",
            CHECK.revalidacion("2026-09-10", dict(REEVALUACION, complete=None))["result"])
    t.igual("E-46 y el check lo dice", "ASSESSMENT_VALIDITY_UNRESOLVED",
            _estado(reevaluacion=dict(REEVALUACION, complete=False)))
    d = _con_cambios(_cambio("NOT_A_TRIGGER", quien="HUMAN"))
    t.igual("E-46 un descendiente sin motivo", "DESCENDANT_WITH_NO_REASSESSMENT_TRIGGER",
            d["assessedArtifactRelation"])
    t.igual("E-46 un cambio anterior al assessment no es motivo", "PASS",
            _con_cambios(_cambio("DEPENDENCY_CHANGED", cuando="2026-09-01"))["state"])


# -- Parcial, limites, huella y traza ------------------------------------------

def _cobertura(**cambios):
    c = {"approvalId": "apr-1", "covers": {"commitSha": "abc123"},
         "provenanceClass": "EXTERNAL_GCABA_SECURITY_AUTHORITY",
         "evidenceReference": "informe parcial ASM-78"}
    c.update(cambios)
    return c


def test_e47_parcial_no_aprueba_un_release_cambiado(t):
    """E-47 (C2-47)."""
    # 🔴 La cobertura nombra al candidato CAMBIADO: lo unico que puede frenarlo es el motivo del
    # Anexo V. Si la cobertura nombrara el commit viejo, el test pasaria por otra razon.
    c = _cambiado(_cambio("DEPENDENCY_CHANGED"))
    r = _ev([_apr(assessmentType="PARTIAL")], candidato=c["candidato"],
            reevaluacion=c["reevaluacion"], changeSet=c["changeSet"],
            partialCoverage=[_cobertura(covers={"commitSha": "def456"})])
    t.verdadero("E-47 no pasa", r["state"] != "PASS")
    t.igual("E-47 porque hay que reevaluar", "SECURITY_REASSESSMENT_REQUIRED", r["state"])
    r = _ev([_apr(assessmentType="PARTIAL")], candidato=c["candidato"],
            reevaluacion=c["reevaluacion"], changeSet=c["changeSet"])
    t.verdadero("E-47 y sin cobertura tampoco", r["state"] != "PASS")


def test_e48_parcial_sin_cobertura(t):
    """E-48 (C2-48)."""
    for tipo in ("PARTIAL", "UNRESOLVED"):
        t.igual("E-48 %s sin cobertura" % tipo, "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED",
                _estado([_apr(assessmentType=tipo)]))
    sin_tipo = _apr()
    del sin_tipo["assessmentType"]
    t.igual("E-48 sin tipo", "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED", _estado([sin_tipo]))
    for nombre, cobertura in (("interna", _cobertura(provenanceClass="UNRESOLVED")),
                              ("sin referencia", _cobertura(evidenceReference="")),
                              ("de otra aprobacion", _cobertura(approvalId="apr-9")),
                              ("de otro commit", _cobertura(covers={"commitSha": "zzz"})),
                              ("mal formada", "apr-1")):
        t.igual("E-48 una cobertura %s no cubre" % nombre, "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED",
                _estado([_apr(assessmentType="PARTIAL")], partialCoverage=[cobertura]))


def test_e49_parcial_con_cobertura(t):
    """E-49 (C2-49)."""
    t.igual("E-49 pasa", "PASS",
            _estado([_apr(assessmentType="PARTIAL")], partialCoverage=[_cobertura()]))
    # La misma regla que el artefacto: un commit ajeno al lado de un release igual no cubre.
    t.igual("E-49 una cobertura que se contradice no cubre", "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED",
            _estado([_apr(assessmentType="PARTIAL")],
                    partialCoverage=[_cobertura(covers={"commitSha": "zzz",
                                                        "releaseId": "1.4.0"})]))
    t.igual("E-49 ni una con la referencia de otra forma", "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED",
            _estado([_apr(assessmentType="PARTIAL")],
                    partialCoverage=[_cobertura(evidenceReference=7)]))


def test_e50_o2_no_es_c2(t):
    """E-50 (C2-50)."""
    t.igual("E-50 O2 pasa", "PASS", AUTORIDAD_O2["state"])
    t.igual("E-50 y sin aprobacion C2 no", "SECURITY_APPROVAL_REQUIRED", _estado([]))


def test_e51_c2_no_es_vu(t):
    """E-51 (C2-51)."""
    senales = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    ev = {"environment": "QA",
          "officialApproval": {"state": "APPROVED", "producer": "GCBA_DGSEI", "evidence": ["a"]},
          "controlResults": {c: {"result": "PASS", "evidence": ["c2"]} for c in (POLICY, CHEQUEO)}}
    t.igual("E-51 C2 cumple", "COMPLIANT", seguridad.resultado("C2", ev, senales, MATRIZ)["result"])
    for r in seguridad.resultados(ev, senales, MATRIZ):
        if r["rule"].startswith("Vu"):
            t.verdadero("E-51 %s no cumple por C2" % r["rule"], r["result"] != "COMPLIANT")


def test_e52_c2_no_es_despliegue(t):
    """E-52 (C2-52)."""
    r = _ev()
    t.igual("E-52 ningun valor es un estado oficial", [],
            sorted(set(_valores(r)) & set(evaluacion.ESTADOS_OFICIALES)))
    serializado = json.dumps(r).upper()
    for palabra in ("DEPLOY", "PRODUCTION", "HOMOLOGATION_COMPLETE"):
        t.no_contiene("E-52 no nombra %s" % palabra, palabra, serializado)


def test_e53_huella(t):
    """E-53 (C2-53)."""
    ref = _ev()["approvalEvidenceRef"]
    t.igual("E-53 id", "apr-1", ref["approvalId"])
    t.igual("E-53 referencia", "informe DGSEI ASM-77", ref["evidenceReference"])
    t.verdadero("E-53 sha256", ref["fingerprint"].startswith("sha256:")
                and len(ref["fingerprint"]) == len("sha256:") + 64)
    t.verdadero("E-53 cambia si cambia la aprobacion",
                ref["fingerprint"] != _ev([_apr(scope=["frontend", "api", "x"])])[
                    "approvalEvidenceRef"]["fingerprint"])


def test_e54_evidencia_cambiada(t):
    """E-54 (C2-54)."""
    huella = _ev()["approvalEvidenceRef"]["fingerprint"]
    t.igual("E-54 la misma huella pasa", "PASS",
            _estado(previousDecision={"approvalId": "apr-1", "fingerprint": huella}))
    t.igual("E-54 otra huella", "SECURITY_APPROVAL_EVIDENCE_CHANGED",
            _estado(previousDecision={"approvalId": "apr-1", "fingerprint": "sha256:otra"}))
    # 🔴 La huella anterior puede decir que no: torcida no se descarta.
    for torcida in ([huella], {"approvalId": None, "fingerprint": huella},
                    {"approvalId": 1, "fingerprint": huella}, {"fingerprint": huella},
                    {"approvalId": "apr-1"}):
        t.igual("E-54 una decision anterior %r obliga a reevaluar" % (torcida,),
                "SECURITY_APPROVAL_EVIDENCE_CHANGED", _estado(previousDecision=torcida))
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))
    atributos = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    for escritura in ("write", "dump", "writelines", "replace", "remove", "unlink", "rename"):
        t.verdadero("E-54 el modulo no llama a `.%s`" % escritura, escritura not in atributos)


def test_e55_determinismo(t):
    """E-55 (C2-55)."""
    vieja = _apr(approvalId="apr-0", assessmentDate="2026-08-01")
    c = _cambiado(_cambio("AUTHENTICATION_FLOW_CHANGED", "MR-2"), _cambio("DEPENDENCY_CHANGED"),
                  _cambio("DEPENDENCY_CHANGED", "MR-3"))
    base = json.dumps(_ev([vieja, APROBACION], candidato=c["candidato"],
                          reevaluacion=c["reevaluacion"], changeSet=c["changeSet"]),
                      sort_keys=True)
    azar = random.Random(55)
    for vuelta in range(5):
        aprobaciones = [copy.deepcopy(vieja), copy.deepcopy(APROBACION)]
        reev = copy.deepcopy(c["reevaluacion"])
        azar.shuffle(aprobaciones)
        azar.shuffle(reev["changes"])
        t.igual("E-55 desordenado %d" % vuelta, base,
                json.dumps(_ev(aprobaciones, candidato=c["candidato"], reevaluacion=reev,
                               changeSet=c["changeSet"]), sort_keys=True))
    t.igual("E-55 los diecisiete estados", sorted(LOS_17), sorted(CHECK.ESTADOS))
    # 🔴 El caso del primer pase: dos aprobaciones del mismo dia, o con el mismo id. No se elige
    # por el orden de la entrada ni por el orden del texto del id.
    rechazada = _apr(status="REJECTED")
    for nombre, par in (("mismo id", [rechazada, APROBACION]),
                        ("mismo dia", [_apr(approvalId="apr-9"),
                                       _apr(approvalId="apr-10", status="REJECTED")])):
        directo, invertido = _estado(par), _estado(list(reversed(par)))
        t.igual("E-55 %s da lo mismo en los dos ordenes" % nombre, directo, invertido)
        t.igual("E-55 %s no se elige" % nombre, "SECURITY_APPROVAL_EVIDENCE_UNRESOLVED", directo)


def test_e56_traza_y_unidad(t):
    """E-56 (C2-56)."""
    caminos = {"sin senal": _ev(senal=None), "no aplica": _ev(senal=False),
               "vacio": _ev([]), "pasa": _ev(), "falla": _ev([_apr(projectId="x")]),
               "reevaluar": _con_cambios(_cambio("DEPENDENCY_CHANGED")),
               "registro invalido": CHECK.evaluar({"registry": {"approvals": 1}}, True,
                                                  AUTORIDAD_O2)}
    for nombre, r in caminos.items():
        t.igual("E-56 %s conserva ES0902" % nombre, TRAZA, r["source"])
        t.igual("E-56 %s conserva el Anexo V" % nombre, ANEXO_V, r["supportingSource"])
        t.igual("E-56 %s conserva la clave" % nombre, "ES0902.C2", r["ruleKey"])
    r = _con_cambios(_cambio("DEPENDENCY_CHANGED"))
    bloque = normativa.resolucion({"securityHomologationPresent": True},
                                  evidencia={"ES0902.C2": r})
    c2 = bloque["standards"]["ES0902"]["rules"]["C2"]
    t.igual("E-56 la unidad trae la aplicabilidad", "APPLICABLE", c2["applicability"])
    t.igual("E-56 el resultado", "SECURITY_REASSESSMENT_REQUIRED", c2["result"])
    t.igual("E-56 la referencia", r["approvalEvidenceRef"], c2["approvalEvidenceRef"])
    t.igual("E-56 la relacion", "SUPERSEDED_BY_CHANGE", c2["assessedArtifactRelation"])
    t.igual("E-56 la revalidacion", {"required": True, "triggers": r["reassessment"]["triggers"]},
            c2["reassessment"])
    t.igual("E-56 la traza", TRAZA, c2["source"])
    t.no_contiene("E-56 sin el registro", "authorityEvidence", json.dumps(bloque))
    # 🔴 La unidad no copia cualquier cosa: un estado oficial, un resultado de otro control, o un
    # PASS con la regla que no aplica, no se proyectan.
    con_registro = dict(r, approvalEvidenceRef=dict(r["approvalEvidenceRef"],
                                                     authorityEvidence=["aut-1"]),
                        evidence=["x", {"authorityEvidence": 1}])
    b = normativa.resolucion({"securityHomologationPresent": True},
                             evidencia={"ES0902.C2": con_registro})
    t.no_contiene("E-56 una referencia con el registro adentro no lo mete", "authorityEvidence",
                  json.dumps(b))
    t.igual("E-56 la lista de la unidad es la del check", sorted(CHECK.ESTADOS),
            sorted(evaluacion.ESTADOS_DEL_CHECK_C2))
    for raro in ("COMPLIANT", "OK", "GREEN", 7):
        b = normativa.resolucion({"securityHomologationPresent": True},
                                 evidencia={"ES0902.C2": {"control": "qa-security-approval-evidence",
                                                          "state": raro}})
        t.igual("E-56 un estado %r que el check no emite no se proyecta" % (raro,), "UNRESOLVED",
                b["standards"]["ES0902"]["rules"]["C2"]["result"])
    for nombre, falso in (("un estado oficial", {"control": "qa-security-approval-evidence",
                                                 "state": "APPROVED"}),
                          ("otro control", {"control": "otro", "state": "PASS"}),
                          ("sin control", {"state": "PASS"})):
        b = normativa.resolucion({"securityHomologationPresent": True},
                                 evidencia={"ES0902.C2": falso})
        t.igual("E-56 %s no se proyecta" % nombre, "UNRESOLVED",
                b["standards"]["ES0902"]["rules"]["C2"]["result"])
    no_aplica = normativa.resolucion({"securityHomologationPresent": False},
                                     evidencia={"ES0902.C2": _ev()})
    t.igual("E-56 con la regla que no aplica el resultado es NOT_APPLICABLE", "NOT_APPLICABLE",
            no_aplica["standards"]["ES0902"]["rules"]["C2"]["result"])
    t.igual("E-56 una evidencia que no es un dict no rompe la unidad", "UNRESOLVED",
            normativa.resolucion({"securityHomologationPresent": True},
                                 evidencia=[1])["standards"]["ES0902"]["rules"]["C2"]["result"])
    sin = normativa.resolucion({"securityHomologationPresent": True})
    t.igual("E-56 sin resultado queda sin resolver", "UNRESOLVED",
            sin["standards"]["ES0902"]["rules"]["C2"]["result"])
    t.igual("E-56 y la forma de seguridad.resolver no cambio", False,
            "rules" in seguridad.resolver({}))
