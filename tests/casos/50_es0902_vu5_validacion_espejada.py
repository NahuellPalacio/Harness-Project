# ES0902 §6 Vu5: toda validacion del cliente esta espejada en el servidor.
#
# Escenarios E-01 a E-67 de docs/cambios/es0902-vu5-validacion-espejada-en-el-servidor/spec.md.
# E-nn es el VU5-nn del pedido de instalacion; E-63 a E-67 los agrega la spec.
#
# 🔴 CASO es el portal con una validacion cumplida: el CUIT es obligatorio en el cliente, la
# operacion `POST /tramites` esta en `interfaces` del contexto de proyecto, y el codigo de
# validacion del servidor, citado, establece la paridad para esa validacion y esa operacion. Casi
# todo este archivo sale de romperla. E-12 la mira en PASS.
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
from orquestacion import cruzada                        # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import matriz as c_matriz             # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "client-server-validation-parity.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu5_paridad")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu5"}
LOS_11 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "CLIENT_VALIDATION_COVERAGE_UNRESOLVED", "CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED",
          "SERVER_VALIDATION_MISSING", "SERVER_VALIDATION_WEAKER",
          "VALIDATION_EQUIVALENCE_UNRESOLVED", "SERVER_VALIDATION_TEST_UNSAFE",
          "TEST_TARGET_UNAVAILABLE")
FALLAS = ("FAIL", "SERVER_VALIDATION_MISSING", "SERVER_VALIDATION_WEAKER")
SIN_COB = "CLIENT_VALIDATION_COVERAGE_UNRESOLVED"
SIN_MAPEO = "CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED"
FALTA = "SERVER_VALIDATION_MISSING"
DEBIL = "SERVER_VALIDATION_WEAKER"
SIN_EQ = "VALIDATION_EQUIVALENCE_UNRESOLVED"
INSEGURA = "SERVER_VALIDATION_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"

VID = "cuit-requerido"
OP = "POST /tramites"

SUPERFICIE = {"surfaceId": "portal", "scope": "tramites", "audience": "INSTITUTIONAL",
              "environment": "QA", "currentProvider": "https://sso-qa.identidad.example/auth",
              "protocol": "OIDC", "flow": "FLUJO-A", "credentialEntryDelegated": True,
              "evidence": []}
BACKOFFICE = dict(SUPERFICIE, surfaceId="backoffice", scope="gestion",
                  credentialEntryDelegated=False)


def _interfaz(iid):
    return {"interface_id": iid, "type": "http", "path": iid, "auth_requirements": "",
            "request_contract_ref": "", "response_contract_ref": "", "owning_component": ""}


CONTEXTO = {"interfaces": {"items": [_interfaz(i) for i in (
    OP, "POST /backoffice/altas", "POST /movil/turnos", "POST /legado/consultas",
    "GET /solo-servidor")], "knowledge_status": "inferred"}}


def _e(eid, fuente, establece, valor=None, validaciones=(VID,), operaciones=(OP,), **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if validaciones is not None:
        base["validations"] = list(validaciones)
    if operaciones is not None:
        base["operations"] = list(operaciones)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _cli(eid="cli", fuente="CLIENT_CODE", sup="portal", vid=VID):
    return _e(eid, fuente, "CLIENT_VALIDATION", "PRESENT", validaciones=[vid], operaciones=None,
              targets=[sup])


def _srv(eid="srv", fuente="SERVER_VALIDATION_CODE", establece="VALIDATION_PARITY",
         valor="EQUIVALENT", vid=VID, op=OP, **extra):
    return _e(eid, fuente, establece, valor, validaciones=[vid], operaciones=[op], **extra)


CLI = _cli()
SRV = _srv()
EVIDENCIA = [CLI, SRV]


def _val(vid=VID, tipo="REQUIRED", descripcion="el CUIT es obligatorio", op=OP, estado="PRESENT",
         paridad="EQUIVALENT", modo="STATIC", evidencia=("cli", "srv"), cref="cli", sref="srv",
         entrada="tramite.cuit"):
    return {"validationId": vid, "inputRef": entrada,
            "constraint": {"type": tipo, "description": descripcion, "clientEvidenceRef": cref},
            "serverMapping": {"operationRef": op, "enforcementStatus": estado,
                              "serverEvidenceRef": sref},
            "parity": paridad, "verificationMode": modo, "evidence": list(evidencia)}


def _cliente(cid="portal", tipo="WEB", validaciones=None, evidencia=()):
    return {"clientSurfaceId": cid, "clientType": tipo,
            "validations": [_val()] if validaciones is None else list(validaciones),
            "evidence": list(evidencia)}


def _caso(superficies=None, clientes=None, evidencia=None, contexto=CONTEXTO):
    caso = {"inventory": {"version": "1.0", "surfaces": copy.deepcopy(
                [SUPERFICIE] if superficies is None else superficies)},
            "clients": {"version": "1.0", "clients": copy.deepcopy(
                [_cliente()] if clientes is None else clientes)},
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if contexto is not None:
        caso["projectContext"] = copy.deepcopy(contexto)
    return caso


def _r(*a, senal=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal)


def _estado(*a, **k):
    return _r(*a, **k)["state"]


def _v(r, vid=VID):
    return [v for c in r["clients"] for v in c["validations"] if v["validationId"] == vid][0]


def _c(r, cid="portal"):
    return [c for c in r["clients"] if c["clientSurfaceId"] == cid][0]


def _sin(eid, *mas):
    return [x for x in EVIDENCIA if x["evidenceId"] != eid] + list(mas)


def _solo_con(*evidencia, **cambios):
    """La validacion base sostenida solo por `evidencia` en lugar de `srv`."""
    ids = [x["evidenceId"] for x in evidencia]
    val = _val(evidencia=["cli"] + ids, sref=None, **cambios)
    return _r(clientes=[_cliente(validaciones=[val])], evidencia=_sin("srv", *evidencia))


def _con_ademas(*evidencia, **cambios):
    """La validacion base, con `srv`, y ademas `evidencia` citada."""
    ids = [x["evidenceId"] for x in evidencia]
    val = _val(evidencia=["cli", "srv"] + ids, **cambios)
    return _r(clientes=[_cliente(validaciones=[val])], evidencia=EVIDENCIA + list(evidencia))


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


PRUEBA = dict(environment="QA", authorized=True, testIdentityRef="qa-contexto-7",
              syntheticValues=True, rejectedBy="VALIDATION")


def _prueba(outcome="INVALID_INPUT_REJECTED", eid="qa", validaciones=(VID,), **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _e(eid, "AUTHORIZED_QA_DIRECT_REQUEST", "SERVER_INPUT_REJECTION", outcome=outcome,
              validaciones=validaciones, **datos)


def _vu5_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu5", ev, sen, MATRIZ)


def _otro(cid, tipo, vid, op, **cambios):
    """Otro cliente cumplido, en el alcance por una evidencia citada, con su validacion y su evidencia."""
    alcance = _e("alcance-%s" % cid, "PROJECT_REQUIREMENT", "CLIENT_SURFACE_SCOPE",
                 validaciones=None, operaciones=None, values=[cid])
    cli = _cli("cli-%s" % cid, sup=cid, vid=vid)
    srv = _srv("srv-%s" % cid, vid=vid, op=op, **{k: v for k, v in cambios.items()
                                                 if k in ("valor", "establece", "fuente")})
    val = _val(vid=vid, op=op, evidencia=[cli["evidenceId"], srv["evidenceId"]],
               cref=cli["evidenceId"], sref=srv["evidenceId"],
               **{k: v for k, v in cambios.items() if k in ("paridad", "estado", "tipo")})
    return (_cliente(cid, tipo, [val], evidencia=[alcance["evidenceId"]]), [alcance, cli, srv])


def _debil(eid="debil", fuente="INTEGRATION_TEST"):
    return _srv(eid, fuente=fuente, valor="SERVER_WEAKER")


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (VU5-01)."""
    t.igual("E-01 la fila", "ES0902.Vu5", seguridad.regla("Vu5", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu5", CHECK.CLAVE)
    for nombre, r in (("pasa", _r()), ("sin senal", CHECK.evaluar({})),
                      ("falla", _con_ademas(_debil())),
                      ("no aplica", _r(clientes=[], evidencia=[_ausente()]))):
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu5", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu5", _vu5_en_seguridad(r)["ruleKey"])


def test_e02_los_ids(t):
    """E-02 (VU5-02)."""
    vu5 = seguridad.regla("Vu5", MATRIZ)
    t.igual("E-02 la senal", ["clientValidationPresent"], vu5["applicability"]["signals"])
    # La matriz declara tres agentes primarios; `dev-security` es el dueno normativo y va primero.
    t.igual("E-02 los agentes", ["dev-security", "dev-backend", "dev-frontend"],
            vu5["primaryAgents"])
    t.igual("E-02 la policy", ["client-validation-server-mirroring-required"], vu5["policies"])
    t.igual("E-02 el check", ["client-server-validation-parity"], vu5["checks"])
    t.igual("E-02 el modulo", ("clientValidationPresent", "client-server-validation-parity",
                               "client-validation-server-mirroring-required"),
            (CHECK.SENAL, CHECK.CONTROL, CHECK.POLICY))
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("client-validation-server-mirroring-required", "POLICY",
             "controles/policies/client-validation-server-mirroring-required.md"),
            ("client-server-validation-parity", "CHECK",
             "controles/checks/client-server-validation-parity.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.igual("E-02 %s regla" % cid, "Vu5", registro[cid]["rule"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    for md in ("es0902-vu5-governance.md", "es0902-vu5-client-validation-present-signal.md",
               "es0902-vu5-client-server-validation-parity-check.md"):
        t.verdadero("E-02 %s instalado" % md, (REGLAS / md).is_file())


def test_e03_nada_nuevo(t):
    """E-03 (VU5-03)."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 10, len(registro["agents"]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 cero reviews", [], seguridad.regla("Vu5", MATRIZ)["reviews"])
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-03 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-03 y Vu5 no tiene algoritmo propio", "Vu5" not in seguridad.ALGORITMOS)


# -- La senal -------------------------------------------------------------------

def test_e04_una_validacion_explicita_enciende(t):
    """E-04 (VU5-04)."""
    doc = CHECK.senal(_caso())
    t.igual("E-04 TRUE", "TRUE", doc["value"])
    t.igual("E-04 la cita", ["client-server-validation-parity.json#cuit-requerido"],
            sorted(e["reference"] for e in doc["evidence"]))
    booleanos = senales.booleanos({"clientValidationPresent": doc})
    t.igual("E-04 enciende la fila", "APPLICABLE",
            seguridad.resolver_regla(seguridad.regla("Vu5", MATRIZ), booleanos)[0])
    sin_citar = _val(evidencia=["srv"], cref=None)
    t.igual("E-04 sin citar la evidencia del cliente no enciende", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[_cliente(validaciones=[sin_citar])]))["value"])
    suelta = dict(CLI, targets=None, validations=None)
    t.igual("E-04 citada y sin nombrar nada, la cita la ata y enciende", "TRUE",
            CHECK.senal(_caso(evidencia=[suelta, SRV]))["value"])
    t.igual("E-04 citada y de otra validacion, no", "UNRESOLVED",
            CHECK.senal(_caso(evidencia=[dict(CLI, targets=["otro"], validations=["otra"]),
                                         SRV]))["value"])
    t.igual("E-04 una validacion sin evidencia no enciende", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[_cliente(validaciones=[_val(evidencia=[], cref=None,
                                                                    sref=None)])],
                              evidencia=[]))["value"])


def test_e05_una_validacion_declarativa_o_generada(t):
    """E-05 (VU5-05)."""
    for fuente in ("HTML_ATTRIBUTE", "GENERATED_CLIENT_CODE", "FRAMEWORK_CONFIGURATION"):
        caso = _caso(evidencia=[_cli(fuente=fuente), SRV])
        t.igual("E-05 `%s` enciende" % fuente, "TRUE", CHECK.senal(caso)["value"])
        t.igual("E-05 y se evalua como cualquiera (%s)" % fuente, "PASS",
                CHECK.evaluar(caso)["state"])


def test_e06_una_libreria_sola_no_enciende(t):
    """E-06 (VU5-06)."""
    dep = _cli("dep", fuente="DEPENDENCY_MANIFEST")
    val = _val(evidencia=["dep", "srv"], cref="dep")
    caso = _caso(clientes=[_cliente(validaciones=[val])], evidencia=[dep, SRV])
    t.igual("E-06 un DEPENDENCY_MANIFEST solo no enciende", "UNRESOLVED", CHECK.senal(caso)["value"])
    t.igual("E-06 y el check no se evalua", "APPLICABILITY_UNRESOLVED", CHECK.evaluar(caso)["state"])
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT"):
        caso = _caso(clientes=[_cliente(validaciones=[val])],
                     evidencia=[dict(dep, sourceType=fuente), SRV])
        t.igual("E-06 `%s` tampoco" % fuente, "UNRESOLVED", CHECK.senal(caso)["value"])


def _ausente(fuente="ARCHITECTURE_DOCUMENTATION", sup="portal", eid="aus"):
    return _e(eid, fuente, "CLIENT_VALIDATION", "ABSENT", validaciones=None, operaciones=None,
              targets=[sup])


def test_e07_la_ausencia_autoritativa_apaga(t):
    """E-07 (VU5-07)."""
    caso = _caso(clientes=[], evidencia=[_ausente()])
    t.igual("E-07 FALSE", "FALSE", CHECK.senal(caso)["value"])
    t.igual("E-07 NOT_APPLICABLE", "NOT_APPLICABLE", CHECK.evaluar(caso)["state"])
    cobertura = CHECK.evaluar(caso)["coverage"]
    t.igual("E-07 sin entrada, la ausencia que nombra la superficie la cubre sin cita",
            ([], ["portal"]), (cobertura["uncovered"], cobertura["absent"]))
    vacia = _cliente(validaciones=[])
    t.igual("E-07 con una entrada vacia, la ausencia no citada no la cubre ni apaga", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[vacia], evidencia=[_ausente()]))["value"])
    t.igual("E-07 y queda sin cubrir", ["portal"],
            CHECK.evaluar(_caso(clientes=[vacia], evidencia=[_ausente()]))["coverage"]["uncovered"])
    t.igual("E-07 con una entrada vacia que cita la ausencia, apaga", "FALSE",
            CHECK.senal(_caso(clientes=[_cliente(validaciones=[], evidencia=["aus"])],
                              evidencia=[_ausente()]))["value"])
    for nombre, c in (("sin entrada", _caso(clientes=[], evidencia=[_ausente()])),
                      ("con entrada vacia", _caso(clientes=[vacia], evidencia=[_ausente()])),
                      ("dos superficies", _caso([SUPERFICIE, BACKOFFICE], [], [_ausente()]))):
        r = CHECK.evaluar(c)
        t.verdadero("E-07 nunca FALSE con una superficie sin cubrir (%s)" % nombre,
                    not (r["signalValue"] == "FALSE" and r["coverage"]["uncovered"]))
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT", "CLIENT_CODE", "UI_OBSERVATION",
                   "DEPENDENCY_MANIFEST"):
        t.igual("E-07 una fuente debil (%s) no apaga" % fuente, "UNRESOLVED",
                CHECK.senal(_caso(clientes=[], evidencia=[_ausente(fuente)]))["value"])
    t.igual("E-07 con una superficie sin la ausencia no apaga", "UNRESOLVED",
            CHECK.senal(_caso([SUPERFICIE, BACKOFFICE], [], [_ausente()]))["value"])
    t.igual("E-07 con las dos ausentes, apaga", "FALSE",
            CHECK.senal(_caso([SUPERFICIE, BACKOFFICE], [],
                              [_ausente(), _ausente(sup="backoffice", eid="aus-2")]))["value"])
    t.igual("E-07 con una validacion en el registro no apaga", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[_cliente(validaciones=[_val(evidencia=[], cref=None)])],
                              evidencia=[_ausente()]))["value"])
    t.igual("E-07 con un cliente del registro fuera del alcance no apaga", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[_cliente("otro", validaciones=[])],
                              evidencia=[_ausente()]))["value"])
    t.igual("E-07 con una evidencia que dice PRESENT no apaga", "UNRESOLVED",
            CHECK.senal(_caso(clientes=[], evidencia=[_ausente(), _cli()]))["value"])
    t.igual("E-07 sin ninguna superficie no apaga: el vacio no es FALSE", "UNRESOLVED",
            CHECK.senal(_caso([], [], []))["value"])
    t.igual("E-07 un registro que no valida no apaga", "UNRESOLVED",
            CHECK.senal(dict(_caso(clientes=[], evidencia=[_ausente()]),
                             clients={"version": "1.0", "clients": [], "extra": 1}))["value"])


def test_e08_un_alcance_sin_cubrir(t):
    """E-08 (VU5-08)."""
    caso = _caso(clientes=[], evidencia=[])
    t.igual("E-08 UNRESOLVED", "UNRESOLVED", CHECK.senal(caso)["value"])
    t.igual("E-08 y el check", "APPLICABILITY_UNRESOLVED", CHECK.evaluar(caso)["state"])
    t.igual("E-08 con el backoffice sin nada y el portal ausente, tambien", "UNRESOLVED",
            CHECK.senal(_caso([SUPERFICIE, BACKOFFICE], [], [_ausente()]))["value"])


# -- La direccion -----------------------------------------------------------------

SOLO_SERVIDOR = [_srv("srv-extra", valor="EQUIVALENT", vid="solo-en-el-servidor",
                      op="GET /solo-servidor"),
                 # Una prueba insegura que nombra solo una validacion y una operacion del servidor.
                 _e("qa-srv", "AUTHORIZED_QA_DIRECT_REQUEST", "SERVER_INPUT_REJECTION",
                    validaciones=["solo-en-el-servidor"], operaciones=["GET /solo-servidor"],
                    outcome="INVALID_INPUT_ACCEPTED", environment="PRD", authorized=True,
                    testIdentityRef="qa-contexto-7", syntheticValues=True),
                 _e("srv-extra-2", "SERVER_VALIDATION_CODE", "SERVER_VALIDATION", "PRESENT",
                    validaciones=["otra-del-servidor"], operaciones=["GET /solo-servidor"])]


def test_e09_solo_el_cliente_genera_exigencias(t):
    """E-09 (VU5-09)."""
    r = _r(evidencia=EVIDENCIA + SOLO_SERVIDOR)
    t.igual("E-09 se evaluan solo las del registro", [VID],
            [v["validationId"] for c in r["clients"] for v in c["validations"]])
    t.igual("E-09 ninguna interfaz sin validacion del cliente genera una exigencia", "PASS",
            r["state"])
    t.igual("E-09 una validacion se evalua solo desde un cliente", ["evaluar_cliente"],
            _llamadores("evaluar_validacion"))
    t.igual("E-09 y un cliente solo desde el registro", ["evaluar"], _llamadores("evaluar_cliente"))
    t.no_contiene("E-09 la del servidor no aparece", "solo-en-el-servidor", json.dumps(r))


def test_e10_lo_que_solo_esta_en_el_servidor_no_cambia_nada(t):
    """E-10 (VU5-10)."""
    for nombre, caso in (("que pasa", {}),
                         ("sin resolver", {"clientes": [_cliente(validaciones=[
                             _val(paridad="UNRESOLVED")])]})):
        base = json.dumps(_r(**caso), sort_keys=True)
        con = json.dumps(_r(evidencia=EVIDENCIA + SOLO_SERVIDOR, **caso), sort_keys=True)
        t.igual("E-10 el mismo resultado entero (%s)" % nombre, base, con)


def test_e11_las_del_servidor_de_mas_no_impiden_el_pass(t):
    """E-11 (VU5-11)."""
    r = _r(evidencia=EVIDENCIA + SOLO_SERVIDOR)
    t.igual("E-11 PASS", "PASS", r["state"])
    t.verdadero("E-11 aprueba", CHECK.aprueba(r))


# -- La paridad ---------------------------------------------------------------------

def test_e12_required_en_los_dos_lados(t):
    """E-12 (VU5-12)."""
    r = _r()
    t.igual("E-12 PASS", "PASS", r["state"])
    t.igual("E-12 la validacion cumple", "PASS", _v(r)["state"])
    t.igual("E-12 con su enforcement", ["srv"], _v(r)["evidenceUsed"]["enforcement"])
    t.igual("E-12 y su paridad", ["srv"], _v(r)["evidenceUsed"]["parity"])
    t.igual("E-12 y la evidencia del cliente", ["cli"], _v(r)["evidenceUsed"]["clientValidation"])
    t.igual("E-12 el mapeo resuelto", True, _v(r)["serverMapping"]["resolved"])
    t.verdadero("E-12 aprueba", CHECK.aprueba(r))
    t.igual("E-12 y en seguridad cumple", "COMPLIANT", _vu5_en_seguridad(r)["result"])


def _mas_debil(t, escenario, tipo, descripcion):
    r = _solo_con(_debil(), paridad="SERVER_WEAKER", tipo=tipo, descripcion=descripcion)
    t.igual("%s SERVER_VALIDATION_WEAKER" % escenario, DEBIL, r["state"])
    t.igual("%s la validacion" % escenario, DEBIL, _v(r)["state"])
    t.igual("%s con su evidencia" % escenario, ["debil"], _v(r)["evidenceUsed"]["parity"])
    t.igual("%s es FAIL en seguridad" % escenario, "NON_COMPLIANT", _vu5_en_seguridad(r)["result"])
    t.igual("%s el registro dice EQUIVALENT y una citada dice que no: falla" % escenario, DEBIL,
            _con_ademas(_debil(), tipo=tipo)["state"])
    t.igual("%s sin citarla no es FAIL" % escenario, SIN_EQ,
            _r(clientes=[_cliente(validaciones=[_val(paridad="SERVER_WEAKER", tipo=tipo)])],
               evidencia=EVIDENCIA + [_debil()])["state"])
    t.igual("%s declarada, citada, y otra no citada que dice que cumple: falla" % escenario, DEBIL,
            _r(clientes=[_cliente(validaciones=[_val(paridad="SERVER_WEAKER", tipo=tipo,
                                                     evidencia=["cli", "debil"], sref="debil")])],
               evidencia=EVIDENCIA + [_debil()])["state"])
    t.igual("%s declarada, citada, y otra citada que dice que cumple: falla" % escenario, DEBIL,
            _con_ademas(_debil(), paridad="SERVER_WEAKER", tipo=tipo)["state"])
    t.igual("%s sin ninguna evidencia no es FAIL" % escenario, SIN_EQ,
            _solo_con(paridad="SERVER_WEAKER", tipo=tipo)["state"])
    t.igual("%s de una fuente que no es de enforcement no es FAIL" % escenario, SIN_EQ,
            _solo_con(_debil(fuente="FIELD_NAME_MATCH"), paridad="SERVER_WEAKER", tipo=tipo)["state"])


def test_e13_el_servidor_acepta_null(t):
    """E-13 (VU5-13)."""
    _mas_debil(t, "E-13 required contra null", "REQUIRED", "el CUIT es obligatorio")


def test_e14_un_enum_contra_un_string_libre(t):
    """E-14 (VU5-14)."""
    _mas_debil(t, "E-14 enum contra string", "ALLOWED_VALUES", "tipo en [A, B]")


def test_e15_una_cota_inferior_sin_cota(t):
    """E-15 (VU5-15)."""
    _mas_debil(t, "E-15 min 1 contra nada", "RANGE", "cantidad >= 1")


def _estricto(eid="estricto"):
    return _srv(eid, fuente="CONTRACT_TEST", valor="SERVER_STRONGER_COMPATIBLE")


def _compat(valor="COMPATIBLE", eid="compat", fuente="API_CONTRACT"):
    return _e(eid, fuente, "CONTRACT_COMPATIBILITY", valor, operaciones=None)


def test_e16_mas_estricto_sin_contrato(t):
    """E-16 (VU5-16)."""
    r = _solo_con(_estricto(), paridad="SERVER_STRONGER_COMPATIBLE", tipo="LENGTH",
                  descripcion="maxLength 100 en el cliente, 80 en el servidor")
    t.igual("E-16 VALIDATION_EQUIVALENCE_UNRESOLVED", SIN_EQ, r["state"])
    t.contiene("E-16 y dice que falta el contrato", "contrato", _v(r)["reason"])


def test_e17_mas_estricto_con_contrato(t):
    """E-17 (VU5-17)."""
    r = _solo_con(_estricto(), _compat(), paridad="SERVER_STRONGER_COMPATIBLE", tipo="LENGTH")
    t.igual("E-17 cumple", "PASS", r["state"])
    t.igual("E-17 con su contrato", ["compat"], _v(r)["evidenceUsed"]["contractCompatibility"])
    sin_citar = _r(clientes=[_cliente(validaciones=[_val(
        evidencia=["cli", "estricto"], sref=None, paridad="SERVER_STRONGER_COMPATIBLE")])],
        evidencia=_sin("srv", _estricto(), _compat()))
    t.igual("E-17 sin citar el contrato, no", SIN_EQ, sin_citar["state"])
    t.igual("E-17 de una fuente que no es autoritativa, no", SIN_EQ,
            _solo_con(_estricto(), _compat(fuente="README_STATEMENT"),
                      paridad="SERVER_STRONGER_COMPATIBLE")["state"])
    t.igual("E-17 con el contrato y sin enforcement, no", SIN_EQ,
            _solo_con(_compat(), paridad="SERVER_STRONGER_COMPATIBLE")["state"])
    t.igual("E-17 una evidencia EQUIVALENT no sostiene una paridad mas estricta", SIN_EQ,
            _solo_con(_srv("eq", fuente="CONTRACT_TEST"), _compat(),
                      paridad="SERVER_STRONGER_COMPATIBLE")["state"])


def test_e18_mas_estricto_con_contrato_en_contra(t):
    """E-18 (VU5-18)."""
    r = _solo_con(_estricto(), _compat("INCOMPATIBLE"), paridad="SERVER_STRONGER_COMPATIBLE")
    t.igual("E-18 sin resolver", SIN_EQ, r["state"])
    t.verdadero("E-18 y no es FAIL", r["state"] not in FALLAS)
    t.igual("E-18 aunque otra diga COMPATIBLE", SIN_EQ,
            _solo_con(_estricto(), _compat("INCOMPATIBLE"), _compat(eid="compat-2"),
                      paridad="SERVER_STRONGER_COMPATIBLE")["state"])
    t.igual("E-18 y la nombra", ["compat"],
            _v(_solo_con(_estricto(), _compat("INCOMPATIBLE"),
                         paridad="SERVER_STRONGER_COMPATIBLE"))["contradictedBy"])


def _falta(eid="falta", fuente="OTHER_AUTHORITATIVE_EVIDENCE"):
    return _srv(eid, fuente=fuente, establece="SERVER_VALIDATION", valor="MISSING")


def test_e19_missing_establecido(t):
    """E-19 (VU5-19)."""
    r = _solo_con(_falta(), estado="MISSING")
    t.igual("E-19 SERVER_VALIDATION_MISSING", FALTA, r["state"])
    t.igual("E-19 con su evidencia", ["falta"], _v(r)["evidenceUsed"]["enforcement"])
    t.igual("E-19 FAIL en seguridad", "NON_COMPLIANT", _vu5_en_seguridad(r)["result"])
    t.igual("E-19 sin citarla no es FAIL", SIN_EQ,
            _r(clientes=[_cliente(validaciones=[_val(estado="MISSING", evidencia=["cli"],
                                                     sref=None)])],
               evidencia=[CLI, _falta()])["state"])
    t.igual("E-19 el registro solo no es FAIL", SIN_EQ, _solo_con(estado="MISSING")["state"])
    t.igual("E-19 de una fuente que no es de enforcement no es FAIL", SIN_EQ,
            _solo_con(_falta(fuente="DTO_NAME_MATCH"), estado="MISSING")["state"])
    t.igual("E-19 el registro dice PRESENT y una citada dice MISSING: falla", FALTA,
            _con_ademas(_falta())["state"])
    t.igual("E-19 MISSING citado y otra citada que dice que valida: la falla gana", FALTA,
            _con_ademas(_falta(), estado="MISSING")["state"])
    t.igual("E-19 MISSING citado y otra no citada que dice que valida: la falla gana", FALTA,
            _r(clientes=[_cliente(validaciones=[_val(estado="MISSING", evidencia=["cli", "falta"],
                                                     sref="falta")])],
               evidencia=EVIDENCIA + [_falta()])["state"])
    t.igual("E-19 MISSING no citado y el registro dice MISSING: sin resolver", SIN_EQ,
            _r(clientes=[_cliente(validaciones=[_val(estado="MISSING")])],
               evidencia=EVIDENCIA + [_falta()])["state"])
    t.igual("E-19 PRESENT sin evidencia no aprueba", SIN_EQ, _solo_con()["state"])
    t.igual("E-19 enforcementStatus UNRESOLVED", SIN_EQ, _estado(clientes=[_cliente(
        validaciones=[_val(estado="UNRESOLVED")])]))


def test_e20_parity_unresolved(t):
    """E-20 (VU5-20)."""
    r = _r(clientes=[_cliente(validaciones=[_val(paridad="UNRESOLVED")])])
    t.igual("E-20 VALIDATION_EQUIVALENCE_UNRESOLVED", SIN_EQ, r["state"])
    t.igual("E-20 y la validacion", SIN_EQ, _v(r)["state"])


# -- Lo que se parece y no es ------------------------------------------------------

def _no_aprueba(t, escenario, fuente, establece="VALIDATION_PARITY", valor="EQUIVALENT"):
    item = _srv("parecido", fuente=fuente, establece=establece, valor=valor)
    r = _solo_con(item)
    t.igual("%s solo no aprueba" % escenario, SIN_EQ, r["state"])
    t.igual("%s y no sostiene nada" % escenario, [], _v(r)["evidenceUsed"]["parity"])
    t.igual("%s y se informa como insuficiente" % escenario, ["parecido"], _v(r)["insufficient"])
    t.igual("%s tampoco diciendo que el servidor valida" % escenario, SIN_EQ,
            _solo_con(_srv("parecido", fuente=fuente, establece="SERVER_VALIDATION",
                           valor="PRESENT"))["state"])


def test_e21_el_nombre_del_campo(t):
    """E-21 (VU5-21)."""
    _no_aprueba(t, "E-21 un FIELD_NAME_MATCH", "FIELD_NAME_MATCH")


def test_e22_el_nombre_del_dto(t):
    """E-22 (VU5-22)."""
    _no_aprueba(t, "E-22 un DTO_NAME_MATCH", "DTO_NAME_MATCH")


def test_e23_la_libreria_compartida(t):
    """E-23 (VU5-23)."""
    _no_aprueba(t, "E-23 un DEPENDENCY_MANIFEST", "DEPENDENCY_MANIFEST")


def test_e24_el_schema_compartido_presente(t):
    """E-24 (VU5-24)."""
    _no_aprueba(t, "E-24 un SHARED_SCHEMA_PRESENCE", "SHARED_SCHEMA_PRESENCE")
    t.igual("E-24 aunque diga que el servidor lo ejecuta", SIN_EQ,
            _solo_con(_srv("parecido", fuente="SHARED_SCHEMA_PRESENCE",
                           establece="SHARED_SCHEMA_SERVER_EXECUTION", valor=None))["state"])


def test_e25_el_schema_compartido_ejecutado(t):
    """E-25 (VU5-25)."""
    ejecuta = _e("ejecuta", "OTHER_AUTHORITATIVE_EVIDENCE", "SHARED_SCHEMA_SERVER_EXECUTION",
                 validaciones=None)
    r = _solo_con(ejecuta)
    t.igual("E-25 sostiene la paridad", "PASS", r["state"])
    t.igual("E-25 con esa evidencia", ["ejecuta"], _v(r)["evidenceUsed"]["parity"])
    otra = dict(ejecuta, operations=["POST /backoffice/altas"])
    t.igual("E-25 para otra operacion, no", SIN_EQ, _solo_con(otra)["state"])
    t.igual("E-25 sin nombrar la operacion, no", SIN_EQ,
            _solo_con(dict(ejecuta, operations=None, validations=[VID]))["state"])
    test = _srv("test", fuente="INTEGRATION_TEST", establece="SHARED_SCHEMA_SERVER_EXECUTION",
                valor=None)
    t.igual("E-25 un test que lo ejecuta y nombra las dos cosas, si", "PASS",
            _solo_con(test)["state"])
    t.igual("E-25 un test que no nombra la validacion, no", SIN_EQ,
            _solo_con(dict(test, validations=None))["state"])


def test_e26_el_atributo_required(t):
    """E-26 (VU5-26)."""
    _no_aprueba(t, "E-26 un HTML_ATTRIBUTE", "HTML_ATTRIBUTE")


def test_e27_el_tipo_de_typescript(t):
    """E-27 (VU5-27)."""
    _no_aprueba(t, "E-27 un TYPESCRIPT_TYPE", "TYPESCRIPT_TYPE")


# -- Transformar no es validar ----------------------------------------------------------

def _transforma(t, escenario, tipo):
    tr = _srv("tr", fuente="CLIENT_TRANSFORMATION")
    r = _solo_con(tr, tipo=tipo)
    t.igual("%s no cumple" % escenario, SIN_EQ, r["state"])
    t.igual("%s y la transformacion es insuficiente" % escenario, ["tr"], _v(r)["insufficient"])
    t.igual("%s con enforcement propio del servidor, si" % escenario, "PASS",
            _estado(clientes=[_cliente(validaciones=[_val(tipo=tipo)])]))


def test_e28_la_mascara(t):
    """E-28 (VU5-28)."""
    _transforma(t, "E-28 una mascara", "MASKING")


def test_e29_la_sanitizacion(t):
    """E-29 (VU5-29)."""
    _transforma(t, "E-29 una sanitizacion", "SANITIZATION")


def test_e30_la_normalizacion(t):
    """E-30 (VU5-30)."""
    _transforma(t, "E-30 una normalizacion", "NORMALIZATION")


def test_e31_la_normalizacion_con_el_dominio_validado(t):
    """E-31 (VU5-31)."""
    normalizado = _srv("dominio", fuente="UNIT_TEST")
    r = _solo_con(normalizado, _srv("tr", fuente="CLIENT_TRANSFORMATION"), tipo="NORMALIZATION",
                  descripcion="el CUIT se normaliza sin guiones y el servidor valida 11 digitos")
    t.igual("E-31 cumple", "PASS", r["state"])
    t.igual("E-31 por el enforcement, no por la transformacion", ["dominio"],
            _v(r)["evidenceUsed"]["parity"])


# -- Validar no es autorizar ------------------------------------------------------------

def test_e32_rechazada_por_autorizacion(t):
    """E-32 (VU5-32)."""
    r = _solo_con(_prueba(rejectedBy="AUTHORIZATION"))
    t.igual("E-32 no sostiene la validacion", SIN_EQ, r["state"])
    t.contiene("E-32 y lo dice", "autorizacion", " ".join(_v(r)["issues"]))
    t.igual("E-32 sin rejectedBy tampoco", SIN_EQ, _solo_con(_prueba(rejectedBy=None))["state"])


def test_e33_un_403_no_es_validacion(t):
    """E-33 (VU5-33)."""
    for codigo in (403, 401):
        r = _solo_con(_prueba(responseStatus=codigo))
        t.igual("E-33 un %d con rejectedBy VALIDATION no sostiene" % codigo, SIN_EQ, r["state"])
        t.igual("E-33 y no usa la prueba (%d)" % codigo, [], _v(r)["evidenceUsed"]["directTest"])


def test_e34_una_prueba_segura_que_llega_a_la_validacion(t):
    """E-34 (VU5-34)."""
    r = _solo_con(_prueba(), modo="AUTHORIZED_QA_DIRECT_REQUEST")
    t.igual("E-34 sostiene la validacion", "PASS", r["state"])
    t.igual("E-34 con la prueba", ["qa"], _v(r)["evidenceUsed"]["directTest"])
    t.igual("E-34 sin contexto de prueba, no", INSEGURA,
            _solo_con(_prueba(testIdentityRef=None))["state"])


def _pass_de(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": [regla]}
                               for c in fila["policies"] + fila["checks"] + fila["reviews"]}}


def _no_mueve(t, escenario, regla, senal):
    ev, _ = CHECK.para_seguridad(_r())
    sin = seguridad.resultado(regla, {}, {senal: True}, MATRIZ)
    con = seguridad.resultado(regla, ev, {senal: True, "clientValidationPresent": True}, MATRIZ)
    t.igual("%s el resultado de %s no cambia" % (escenario, regla), sin["result"], con["result"])
    t.verdadero("%s y no cumple" % escenario, con["result"] != "COMPLIANT")
    t.igual("%s y los controles de Vu5 no son los de %s" % (escenario, regla), [],
            sorted(set(ev["controlResults"]) & set(_pass_de(regla)["controlResults"])))


def test_e35_el_pass_de_vu5_no_es_el_de_vu8(t):
    """E-35 (VU5-35)."""
    _no_mueve(t, "E-35", "Vu8", "applicationRolesPresent")


# -- La prueba directa -------------------------------------------------------------

def test_e36_la_prueba_ve_aceptar_la_entrada_invalida(t):
    """E-36 (VU5-36)."""
    r = _con_ademas(_prueba("INVALID_INPUT_ACCEPTED"))
    t.igual("E-36 FAIL aunque el registro diga EQUIVALENT", FALTA, r["state"])
    t.igual("E-36 con la prueba", ["qa"], _v(r)["evidenceUsed"]["directTest"])
    t.igual("E-36 sin citarla no es FAIL: se contradice y no se elige", SIN_EQ,
            _r(evidencia=EVIDENCIA + [_prueba("INVALID_INPUT_ACCEPTED")])["state"])


def test_e37_la_prueba_ve_rechazar_por_validacion(t):
    """E-37 (VU5-37)."""
    r = _solo_con(_prueba())
    t.igual("E-37 sostiene", "PASS", r["state"])
    t.igual("E-37 el servidor valida", ["qa"], _v(r)["evidenceUsed"]["enforcement"])
    t.igual("E-37 y la paridad", ["qa"], _v(r)["evidenceUsed"]["parity"])
    t.igual("E-37 una prueba de otra validacion, no", SIN_EQ,
            _solo_con(_prueba(validations=["otra"]))["state"])


def test_e38_el_mensaje_no_decide(t):
    """E-38 (VU5-38)."""
    uno = _solo_con(_prueba(errorMessage="El CUIT es invalido"))
    otro = _solo_con(_prueba(errorMessage="400 Bad Request: campo cuit"))
    t.igual("E-38 el mismo estado", "PASS", uno["state"])
    t.igual("E-38 el mismo resultado entero", json.dumps(uno, sort_keys=True),
            json.dumps(otro, sort_keys=True))


def test_e39_el_codigo_no_decide(t):
    """E-39 (VU5-39)."""
    salidas = [_solo_con(_prueba(responseStatus=c)) for c in (400, 422, None)]
    t.igual("E-39 cumple", "PASS", salidas[0]["state"])
    for s, c in zip(salidas[1:], ("422", "sin codigo")):
        t.igual("E-39 400 y %s dan lo mismo" % c, json.dumps(salidas[0], sort_keys=True),
                json.dumps(s, sort_keys=True))


def test_e40_el_servidor_proceso_como_valida(t):
    """E-40 (VU5-40)."""
    procesada = _srv("procesada", fuente="INTEGRATION_TEST", establece="SERVER_INPUT_REJECTION",
                     valor=None, outcome="INVALID_INPUT_ACCEPTED")
    r = _con_ademas(procesada)
    t.igual("E-40 FAIL", FALTA, r["state"])
    t.igual("E-40 FAIL en seguridad", "NON_COMPLIANT", _vu5_en_seguridad(r)["result"])
    t.igual("E-40 sin citarla no es FAIL", SIN_EQ,
            _r(evidencia=EVIDENCIA + [procesada])["state"])
    t.igual("E-40 de una fuente que no es de enforcement no es FAIL", "PASS",
            _con_ademas(dict(procesada, sourceType="UI_OBSERVATION"))["state"])


# -- Los clientes -----------------------------------------------------------------

def test_e41_el_backoffice_no_lo_tapa_el_portal(t):
    """E-41 (VU5-41)."""
    falta = _falta("falta-alta")
    falta["validations"], falta["operations"] = ["alta-cuil"], ["POST /backoffice/altas"]
    back = _cliente("backoffice", "BACKOFFICE", [_val(
        vid="alta-cuil", op="POST /backoffice/altas", estado="MISSING",
        evidencia=["cli-back", "falta-alta"], cref="cli-back", sref="falta-alta")])
    r = _r([SUPERFICIE, BACKOFFICE], [_cliente(), back],
           EVIDENCIA + [_cli("cli-back", sup="backoffice", vid="alta-cuil"), falta])
    t.igual("E-41 FAIL", FALTA, r["state"])
    t.igual("E-41 el portal cumple", "PASS", _c(r)["state"])
    t.igual("E-41 el backoffice falla", FALTA, _c(r, "backoffice")["state"])
    t.igual("E-41 y en seguridad", "NON_COMPLIANT", _vu5_en_seguridad(r)["result"])


def _un_cliente_mas(t, escenario, cid, tipo, vid, op):
    otro, ev = _otro(cid, tipo, vid, op)
    r = _r(clientes=[_cliente(), otro], evidencia=EVIDENCIA + ev)
    t.igual("%s pasa" % escenario, "PASS", r["state"])
    t.igual("%s sale en clients" % escenario, sorted(["portal", cid]),
            sorted(c["clientSurfaceId"] for c in r["clients"]))
    t.igual("%s con su tipo" % escenario, tipo, _c(r, cid)["clientType"])
    t.igual("%s con sus validaciones" % escenario, [vid],
            [v["validationId"] for v in _c(r, cid)["validations"]])
    t.igual("%s en el alcance por la evidencia citada" % escenario, [cid],
            r["coverage"]["fromScopeEvidence"])
    roto, ev2 = _otro(cid, tipo, vid, op, paridad="UNRESOLVED")
    r = _r(clientes=[_cliente(), roto], evidencia=EVIDENCIA + ev2)
    t.igual("%s y con su propia validacion sin resolver, no pasa" % escenario,
            ("PASS", SIN_EQ, SIN_EQ), (_c(r)["state"], _c(r, cid)["state"], r["state"]))
    otro_sin_alcance = dict(otro, evidence=[])
    t.igual("%s sin la evidencia de alcance, queda fuera y no pasa" % escenario, SIN_COB,
            _estado(clientes=[_cliente(), otro_sin_alcance], evidencia=EVIDENCIA + ev))
    alcance = ev[0]
    t.igual("%s un alcance citado sin su entrada deja la cobertura sin resolver" % escenario,
            SIN_COB, _estado(clientes=[_cliente(evidencia=[alcance["evidenceId"]])],
                             evidencia=EVIDENCIA + [alcance]))


def test_e42_el_cliente_movil(t):
    """E-42 (VU5-42)."""
    _un_cliente_mas(t, "E-42 el movil", "app-movil", "MOBILE", "turno-fecha", "POST /movil/turnos")


def test_e43_el_cliente_legado(t):
    """E-43 (VU5-43)."""
    _un_cliente_mas(t, "E-43 el legado", "legado", "LEGACY", "consulta-dni",
                    "POST /legado/consultas")


def test_e44_el_mapeo_es_una_interfaz_del_contexto(t):
    """E-44 (VU5-44)."""
    otra = _srv(op="POST /no-existe")
    r = _r(clientes=[_cliente(validaciones=[_val(op="POST /no-existe")])],
           evidencia=[CLI, otra])
    t.igual("E-44 una operacion que no esta", SIN_MAPEO, r["state"])
    t.igual("E-44 y no queda resuelta", False, _v(r)["serverMapping"]["resolved"])
    sin = _r(contexto=None)
    t.igual("E-44 sin contexto", SIN_MAPEO, sin["state"])
    t.contiene("E-44 y lo dice", "contexto de proyecto", " ".join(sin["issues"]))
    t.igual("E-44 un contexto sin interfaces", SIN_MAPEO, _estado(contexto={"meta": {}}))
    t.igual("E-44 operationRef nulo", SIN_MAPEO,
            _estado(clientes=[_cliente(validaciones=[_val(op=None)])]))
    nfd = unicodedata.normalize("NFD", "POST /trámites")
    nfc = unicodedata.normalize("NFC", "POST /trámites")
    ctx = {"interfaces": {"items": [_interfaz(nfc)], "knowledge_status": "inferred"}}
    t.igual("E-44 igual en NFC es la misma interfaz", "PASS",
            _estado(clientes=[_cliente(validaciones=[_val(op=nfd)])],
                    evidencia=[CLI, _srv(op=nfc)], contexto=ctx))


# -- La prueba segura ----------------------------------------------------------------

def test_e45_en_produccion_no(t):
    """E-45 (VU5-45)."""
    r = _solo_con(_prueba(environment="PRD"))
    t.igual("E-45 insegura", INSEGURA, r["state"])
    t.contiene("E-45 y dice por que", "PRODUCTION", _v(r)["unsafe"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-45 ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing", "selenium", "playwright",
                                 "time", "threading"}))


def test_e46_en_qa_con_valores_sinteticos(t):
    """E-46 (VU5-46)."""
    for ambiente in ("QA", "DEV", "HML", "OTHER"):
        r = _solo_con(_prueba(environment=ambiente))
        t.igual("E-46 en %s cuenta" % ambiente, "PASS", r["state"])
    t.igual("E-46 y la prueba segura no tiene motivos", [], CHECK.prueba_segura(_prueba()))


def test_e47_destructiva_no(t):
    """E-47 (VU5-47)."""
    r = _solo_con(_prueba(destructive=True))
    t.igual("E-47 insegura", INSEGURA, r["state"])
    t.contiene("E-47 y dice por que", "DESTRUCTIVE", _v(r)["unsafe"])
    t.igual("E-47 destructive false cuenta", "PASS", _solo_con(_prueba(destructive=False))["state"])


def test_e48_con_datos_privilegiados_reales_no(t):
    """E-48 (VU5-48)."""
    r = _solo_con(_prueba(realPrivilegedData=True))
    t.igual("E-48 insegura", INSEGURA, r["state"])
    t.contiene("E-48 y dice por que", "REAL_PRIVILEGED_DATA", _v(r)["unsafe"])
    t.igual("E-48 ninguna condicion exige datos reales: sin el campo cuenta", [],
            CHECK.prueba_segura(_prueba()))
    t.igual("E-48 y en falso tambien", [], CHECK.prueba_segura(_prueba(realPrivilegedData=False)))
    t.igual("E-48 los valores sinteticos son los que se exigen", ["NOT_SYNTHETIC_VALUES"],
            CHECK.prueba_segura(_prueba(syntheticValues=False)))


def test_e49_las_condiciones_inseguras(t):
    """E-49 (VU5-49)."""
    for nombre, cambios, motivo in (
            ("sin autorizacion", {"authorized": None}, "NOT_AUTHORIZED"),
            ("autorizada en falso", {"authorized": False}, "NOT_AUTHORIZED"),
            ("sin contexto de prueba", {"testIdentityRef": None}, "NO_AUTHORIZED_TEST_CONTEXT"),
            ("con contexto en blanco", {"testIdentityRef": "  "}, "NO_AUTHORIZED_TEST_CONTEXT"),
            ("sin valores sinteticos", {"syntheticValues": None}, "NOT_SYNTHETIC_VALUES"),
            ("con valores reales", {"syntheticValues": False}, "NOT_SYNTHETIC_VALUES"),
            ("con secretos registrados", {"rawSecretsLogged": True}, "RAW_SECRETS_LOGGED"),
            ("en un ambiente desconocido", {"environment": "STAGING"}, "ENVIRONMENT_UNKNOWN"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED")):
        r = _solo_con(_prueba(**cambios))
        t.igual("E-49 %s" % nombre, INSEGURA, r["state"])
        t.contiene("E-49 %s dice por que" % nombre, motivo, _v(r)["unsafe"])
    t.igual("E-49 sin objetivo", SIN_OBJ, _solo_con(_prueba(outcome="UNAVAILABLE"))["state"])


def test_e50_insegura_no_es_fail(t):
    """E-50 (VU5-50)."""
    acepta = _prueba("INVALID_INPUT_ACCEPTED", environment="PRD")
    t.igual("E-50 insegura que dice que acepta, citada, no es FAIL", INSEGURA,
            _con_ademas(acepta)["state"])
    t.igual("E-50 y no citada tampoco", INSEGURA, _r(evidencia=EVIDENCIA + [acepta])["state"])
    t.igual("E-50 sin objetivo que dice que acepta no es FAIL", SIN_OBJ,
            _con_ademas(_prueba("UNAVAILABLE", value="MISSING"))["state"])
    t.igual("E-50 insegura con MISSING en el registro no es FAIL", INSEGURA,
            _solo_con(acepta, estado="MISSING")["state"])
    t.igual("E-50 una ajena insegura que dice rechazada no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(environment="PRD")]))


# -- Los limites ------------------------------------------------------------------------

P5 = [_e("p5-pasa", "OTHER_AUTHORITATIVE_EVIDENCE", "RULE_RESULT", "PASS", validaciones=None,
         operaciones=None, reference="ES0901.P5"),
      _e("p5-falla", "OTHER_AUTHORITATIVE_EVIDENCE", "RULE_RESULT", "FAIL", validaciones=None,
         operaciones=None, reference="ES0901.P5")]


def test_e51_p5_no_mueve_a_vu5(t):
    """E-51 (VU5-51)."""
    for nombre, caso in (("que pasa", {}),
                         ("sin resolver", {"clientes": [_cliente(validaciones=[
                             _val(paridad="UNRESOLVED")])]})):
        base = json.dumps(_r(**caso), sort_keys=True)
        for p5 in P5:
            t.igual("E-51 con P5 en %s, Vu5 no cambia (%s)" % (p5["value"], nombre), base,
                    json.dumps(_r(evidencia=EVIDENCIA + [p5], **caso), sort_keys=True))
    rel = [r for r in cruzada.relaciones() if r["from"] == "ES0902.Vu5"]
    t.igual("E-51 el mapa cruzado sigue en revision", [("ES0901.P5", "EQUIVALENCE_REVIEW_REQUIRED",
                                                        "CROSS_STANDARD_CONTROL_BINDING_REQUIRED")],
            [(r["to"], r["type"], r["state"]) for r in rel])
    t.igual("E-51 evaluar no recibe resultados de P5", ["caso", "senal", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    t.verdadero("E-51 el modulo no nombra a P5",
                not ({"P5", "ES0901.P5", "ES0901"} & _literales()))


def test_e52_el_pass_de_vu5_no_es_el_de_p5(t):
    """E-52 (VU5-52)."""
    ev, _ = CHECK.para_seguridad(_r())
    p5 = c_matriz.regla("P5")
    t.igual("E-52 los controles de Vu5 no son los de P5", [],
            sorted(set(ev["controlResults"]) & set(p5["policies"] + p5["checks"])))
    t.igual("E-52 P5 sigue sin construir", [],
            sorted(set(p5["policies"] + p5["checks"])
                   & {c["id"] for c in c_controles.cargar()["controls"]}))
    cruce = cruzada.resolver(["P5"], ["Vu5"], {"evidence": ev})
    t.contiene("E-52 con Vu5 en PASS el cruce sigue sin reconciliar",
               "CROSS_STANDARD_CONTROL_BINDING_REQUIRED", cruce["unresolved"])


def test_e53_una_evidencia_compartida_no_copia_el_resultado(t):
    """E-53 (VU5-53)."""
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    sin = {r["rule"]: r["result"] for r in seguridad.resultados({}, todas, MATRIZ)}
    vu6 = seguridad.regla("Vu6", MATRIZ)
    for nombre, r, de_vu5, de_vu6, otro in (
            ("Vu5 pasa y Vu6 falla", _r(), "COMPLIANT", "FAIL", "NON_COMPLIANT"),
            ("Vu5 falla y Vu6 pasa", _con_ademas(_debil()), "NON_COMPLIANT", "PASS", "COMPLIANT")):
        ev, _ = CHECK.para_seguridad(r)
        # La misma evidencia, `srv`, citada por los dos controles de Vu5 y por los de Vu6.
        # Todo lo que produce `para_seguridad`, no solo `controlResults`.
        compartida = dict(ev, controlResults=dict(ev["controlResults"], **{
            c: {"result": de_vu6, "evidence": ["srv"]} for c in vu6["policies"] + vu6["checks"]}))
        t.verdadero("E-53 la evidencia es la misma (%s)" % nombre,
                    "srv" in ev["controlResults"][CHECK.CONTROL]["evidence"])
        con = {x["rule"]: x["result"] for x in seguridad.resultados(compartida, todas, MATRIZ)}
        t.igual("E-53 Vu5 tiene el suyo (%s)" % nombre, de_vu5, con["Vu5"])
        t.igual("E-53 Vu6 sigue con el suyo (%s)" % nombre, otro, con["Vu6"])
        t.igual("E-53 y no cambia ninguna otra (%s)" % nombre, ["Vu5", "Vu6"],
                sorted(k for k in con if con[k] != sin[k]))


def test_e54_vu5_no_dice_nada_de_la_autorizacion(t):
    """E-54 (VU5-54)."""
    for nombre, r in (("pasa", _r()), ("por autorizacion", _solo_con(
            _prueba(rejectedBy="AUTHORIZATION")))):
        claves = {k.lower() for k in _claves(r)}
        for palabra in ("role", "permission", "permiso", "authoriz", "privileg"):
            t.verdadero("E-54 ningun campo nombra `%s` (%s)" % (palabra, nombre),
                        not [k for k in claves if palabra in k])
    t.verdadero("E-54 ni lo que va a seguridad",
                not [k for k in _claves(CHECK.para_seguridad(_r())) if "role" in k.lower()])


def test_e55_el_pass_de_vu5_no_es_el_de_vu6(t):
    """E-55 (VU5-55)."""
    _no_mueve(t, "E-55", "Vu6", "userFacingErrorPresent")


def test_e56_el_pass_de_vu5_no_es_el_de_vu10(t):
    """E-56 (VU5-56)."""
    _no_mueve(t, "E-56", "Vu10", "owaspApplicableAssetPresent")


def test_e57_el_pass_de_vu5_no_es_la_aprobacion(t):
    """E-57 (VU5-57)."""
    _no_mueve(t, "E-57", "C2", "securityHomologationPresent")
    ev, _ = CHECK.para_seguridad(_r())
    ids = ev["controlResults"][CHECK.CONTROL]["evidence"]
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK",
                                         "evidence": ids})
    t.igual("E-57 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])
    senal = {"clientValidationPresent": True, "securityHomologationPresent": True}
    sin = normativa.resolucion(senal)["standards"]["ES0902"]["rules"]["C2"]
    con = normativa.resolucion(senal, evidencia={"ES0902.Vu5": _r()})["standards"]["ES0902"]
    t.igual("E-57 y C2 en la unidad sigue igual", sin, con["rules"]["C2"])
    t.igual("E-57 mientras Vu5 pasa", "PASS", con["rules"]["Vu5"]["result"])


# -- El agregado -------------------------------------------------------------------------------

def test_e58_una_validacion_en_fail(t):
    """E-58 (VU5-58)."""
    otra_cumple = _val(vid="nombre-requerido", evidencia=["cli-2", "srv-2"], cref="cli-2",
                       sref="srv-2")
    # Sin `srv`: una evidencia legible que dice que el servidor valida contradice la falla.
    ev = [CLI, _cli("cli-2", vid="nombre-requerido"), _srv("srv-2", vid="nombre-requerido")]
    for nombre, val, extra, esperado in (
            ("MISSING", _val(estado="MISSING", evidencia=["cli", "falta"], sref="falta"),
             [_falta()], FALTA),
            ("WEAKER", _val(paridad="SERVER_WEAKER", evidencia=["cli", "debil"], sref="debil"),
             [_debil()], DEBIL)):
        r = _r(clientes=[_cliente(validaciones=[otra_cumple, val])], evidencia=ev + extra)
        t.igual("E-58 una en %s hace FAIL el agregado" % nombre, esperado, r["state"])
        t.igual("E-58 aunque la otra cumpla (%s)" % nombre, "PASS", _v(r, "nombre-requerido")["state"])
        t.verdadero("E-58 y no aprueba (%s)" % nombre, not CHECK.aprueba(r))
    dos = _r(clientes=[_cliente(validaciones=[
        _val(estado="MISSING", evidencia=["cli", "falta"], sref="falta"),
        _val(vid="nombre-requerido", paridad="SERVER_WEAKER", evidencia=["cli-2", "debil-2"],
             cref="cli-2", sref="debil-2")])],
        evidencia=[CLI, _cli("cli-2", vid="nombre-requerido"), _falta(),
                   _srv("debil-2", fuente="UNIT_TEST", valor="SERVER_WEAKER",
                        vid="nombre-requerido")])
    t.igual("E-58 dos fallas distintas dan FAIL", "FAIL", dos["state"])
    t.igual("E-58 y las nombra", sorted([FALTA, DEBIL]),
            sorted(s for s in dos["states"] if s in FALLAS and s != "FAIL"))


def test_e59_un_mapeo_sin_resolver_impide_el_pass(t):
    """E-59 (VU5-59)."""
    sin_op = _val(vid="nombre-requerido", op="POST /no-existe", evidencia=["cli-2", "srv-2"],
                  cref="cli-2", sref="srv-2")
    r = _r(clientes=[_cliente(validaciones=[_val(), sin_op])],
           evidencia=EVIDENCIA + [_cli("cli-2", vid="nombre-requerido"),
                                  _srv("srv-2", vid="nombre-requerido", op="POST /no-existe")])
    t.igual("E-59 no pasa", SIN_MAPEO, r["state"])
    t.igual("E-59 aunque la otra cumpla", "PASS", _v(r)["state"])
    t.igual("E-59 en seguridad no cumple", "UNRESOLVED", _vu5_en_seguridad(r)["result"])
    falla = _r(clientes=[_cliente(validaciones=[_val(op="POST /no-existe", estado="MISSING",
                                                     evidencia=["cli", "falta"], sref="falta")])],
               evidencia=[CLI, dict(_falta(), operations=["POST /no-existe"])])
    t.igual("E-59 una falla posterior le gana al mapeo sin resolver", FALTA, falla["state"])
    t.igual("E-59 y el mapeo queda a la vista", True, SIN_MAPEO in _v(falla)["states"])


def test_e60_el_mismo_resultado(t):
    """E-60 (VU5-60)."""
    otro, ev_otro = _otro("app-movil", "MOBILE", "turno-fecha", "POST /movil/turnos")
    back = _cliente("backoffice", "BACKOFFICE", [_val(
        vid="alta-cuil", op="POST /backoffice/altas", paridad="UNRESOLVED",
        evidencia=["cli-back"], cref="cli-back", sref=None)])
    clientes = [_cliente(), otro, back]
    ev = EVIDENCIA + ev_otro + [_cli("cli-back", sup="backoffice", vid="alta-cuil"),
                                _srv("repetida"), _srv("repetida")]
    base = json.dumps(_r([SUPERFICIE, BACKOFFICE], clientes, ev), sort_keys=True)
    azar = random.Random(60)
    for vuelta in range(6):
        s, c, e = copy.deepcopy([SUPERFICIE, BACKOFFICE]), copy.deepcopy(clientes), copy.deepcopy(ev)
        azar.shuffle(s)
        azar.shuffle(c)
        azar.shuffle(e)
        for cl in c:
            azar.shuffle(cl["validations"])
        t.igual("E-60 desordenado %d" % vuelta, base, json.dumps(_r(s, c, e), sort_keys=True))
    t.igual("E-60 los once estados", sorted(LOS_11), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "validación") for f in ("NFC", "NFD"))
    for nombre, par in (("iguales", ("EQUIVALENT", "EQUIVALENT")),
                        ("debil la NFC", ("SERVER_WEAKER", "EQUIVALENT")),
                        ("debil la NFD", ("EQUIVALENT", "SERVER_WEAKER"))):
        gemelas = [_srv(nfc, valor=par[0]), _srv(nfd, valor=par[1])]
        for orden in (gemelas, gemelas[::-1]):
            t.igual("E-60 gemelas en NFC y NFD (%s) no pasan ni fallan" % nombre, SIN_EQ,
                    _solo_con(*orden)["state"])
    t.igual("E-60 citar en NFD una evidencia en NFC es citarla", "PASS",
            _estado(clientes=[_cliente(validaciones=[_val(evidencia=["cli", nfd], sref=None)])],
                    evidencia=[CLI, _srv(nfc)]))
    v1 = _val(vid=nfc, evidencia=["cli", "s1"], sref="s1")
    v2 = _val(vid=nfd, evidencia=["cli", "s1"], sref="s1")
    ev2 = [CLI, _srv("s1", vid=nfc)]
    dos = _r(clientes=[_cliente(validaciones=[v1, v2])], evidencia=ev2)
    t.igual("E-60 dos validaciones iguales en NFC son la misma, repetida", (SIN_COB, [nfc]),
            (dos["state"], dos["coverage"]["duplicatedValidations"]))
    t.igual("E-60 y dan lo mismo en los dos ordenes", json.dumps(dos, sort_keys=True),
            json.dumps(_r(clientes=[_cliente(validaciones=[v2, v1])], evidencia=ev2),
                       sort_keys=True))
    c1, c2 = _cliente(nfc, validaciones=[]), _cliente(nfd, validaciones=[])
    t.igual("E-60 dos clientes iguales en NFC son el mismo, repetido", [nfc],
            _r(clientes=[_cliente(), c1, c2])["coverage"]["duplicatedClients"])


def test_e61_la_trazabilidad(t):
    """E-61 (VU5-61)."""
    caminos = {"sin senal": CHECK.evaluar({}), "pasa": _r(),
               "falla": _con_ademas(_debil()),
               "insegura": _solo_con(_prueba(environment="PRD")),
               "no aplica": _r(clientes=[], evidencia=[_ausente()]),
               "inventario invalido": CHECK.evaluar({"inventory": {"surfaces": 1}}, True)}
    for nombre, r in caminos.items():
        t.igual("E-61 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-61 %s la clave" % nombre, "ES0902.Vu5", r["ruleKey"])
        t.igual("E-61 %s el control" % nombre, "client-server-validation-parity", r["control"])
    t.igual("E-61 un inventario invalido deja la cobertura sin resolver", SIN_COB,
            caminos["inventario invalido"]["state"])
    resultado = _r()
    vu5 = normativa.resolucion({"clientValidationPresent": True},
                               evidencia={"ES0902.Vu5": resultado})["standards"]["ES0902"]
    vu5 = vu5["rules"]["Vu5"]
    t.igual("E-61 la unidad lleva Vu5", ("APPLICABLE", "PASS"),
            (vu5["applicability"], vu5["result"]))
    t.igual("E-61 con sus clientes", ["portal"], vu5["clients"])
    t.igual("E-61 y su evidencia por id", ["cli", "srv"], vu5["evidence"])
    t.igual("E-61 y nada mas", ["applicability", "clients", "evidence", "result", "source"],
            sorted(vu5))
    t.igual("E-61 con la fuente", TRAZA, vu5["source"])
    t.no_contiene("E-61 sin contenido: ni la descripcion ni la operacion", "CUIT",
                  json.dumps(vu5, ensure_ascii=False))
    falso = dict(resultado, control="otro-control")
    t.igual("E-61 un resultado ajeno no se proyecta", "UNRESOLVED",
            normativa.resolucion({"clientValidationPresent": True},
                                 evidencia={"ES0902.Vu5": falso})["standards"]["ES0902"]
            ["rules"]["Vu5"]["result"])
    t.igual("E-61 sin la senal no se proyecta", ("UNRESOLVED", []),
            tuple(normativa.resolucion({}, evidencia={"ES0902.Vu5": resultado})["standards"]
                  ["ES0902"]["rules"]["Vu5"][k] for k in ("result", "clients")))
    t.igual("E-61 con la senal en falso, NOT_APPLICABLE", "NOT_APPLICABLE",
            normativa.resolucion({"clientValidationPresent": False})["standards"]["ES0902"]
            ["rules"]["Vu5"]["result"])
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = normativa.resolucion({"clientValidationPresent": True},
                                       evidencia={"ES0902.Vu5": resultado})
    finally:
        normativa._ruta_de_evidencia = original
    vu5_sin = sin_lib["standards"]["ES0902"]["rules"]["Vu5"]
    t.igual("E-61 sin la lib la unidad se arma, con el estado y sin ids",
            ("PASS", [], []), (vu5_sin["result"], vu5_sin["clients"], vu5_sin["evidence"]))
    t.verdadero("E-61 y Vu4 sigue en la unidad", "Vu4" in sin_lib["standards"]["ES0902"]["rules"])


def test_e62_entra_al_libro_como_cualquier_regla(t):
    """E-62 (VU5-62)."""
    paquete = BIN / "reporte_seguridad"
    t.igual("E-62 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in paquete.iterdir() if p.is_file()))
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu5_62_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-5062")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _con_ademas(_debil()), "NON_COMPLIANT"),
                     ("sin resolver", _r(clientes=[_cliente(validaciones=[
                         _val(paridad="UNRESOLVED")])]), "UNRESOLVED"),
                     ("no aplica", _r(clientes=[], evidencia=[_ausente()]), "NOT_APPLICABLE"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu5_en_seguridad(r)
            t.igual("E-62 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-5062", alcance,
                                           "2026-09-24T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-62 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-62 de ES0902.Vu5", [("ES0902", "Vu5", "ES0902.Vu5")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-62 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "NOT_APPLICABLE"],
                [e["result"] for e in eventos])
        t.igual("E-62 producido por desde_regla", ["desde_regla"] * 4,
                [e["details"]["producer"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    t.igual("E-62 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))
    t.igual("E-62 Vu5 en el dominio de validacion del reporte", True,
            "Vu5" in [d for d in json.loads((REGLAS / "security-report-domains.json").read_text(
                encoding="utf-8"))["domains"] if d["domainId"] == "validation-error-handling"][0]
            ["rules"])


# -- Lo que agrega esta spec ------------------------------------------------------------------

CREDENCIALES = ("password=hunter2abc", "contraseña=hunter2abc", "clave: hunter2abc",
                "access_token=hunter2abc", "api_key=hunter2abc", "Bearer abcdefghhunter2abc",
                "JSESSIONID=hunter2abc", "Cookie: SESSION=hunter2abc", "code=hunter2abc",
                "https://usuario:hunter2abc@db.example")


def test_e63_ningun_secreto(t):
    """E-63."""
    base_claves = set(_claves(_r()))
    base_senal = set(_claves(CHECK.senal(_caso())))
    base_unidad = set(_claves(normativa.resolucion(
        {"clientValidationPresent": True}, evidencia={"ES0902.Vu5": _r()})["standards"]["ES0902"]
        ["rules"]["Vu5"]))
    for texto in CREDENCIALES:
        cliente_raro = _cliente(texto)
        casos = {
            "un clientSurfaceId": _r(clientes=[_cliente(), cliente_raro]),
            "un validationId": _r(clientes=[_cliente(validaciones=[_val(vid=texto)])],
                                  evidencia=[_cli(vid=texto), _srv(vid=texto)]),
            "constraint.description": _r(clientes=[_cliente(validaciones=[
                _val(descripcion="se valida con " + texto)])]),
            "un inputRef": _r(clientes=[_cliente(validaciones=[_val(entrada=texto)])]),
            "un operationRef": _r(clientes=[_cliente(validaciones=[_val(op=texto)])]),
            "un id de evidencia citado": _r(clientes=[_cliente(validaciones=[
                _val(evidencia=["cli", texto], sref=texto)])], evidencia=[CLI, _srv(texto)]),
            "la senal": CHECK.senal(_caso(clientes=[_cliente(validaciones=[_val(vid=texto)])],
                                          evidencia=[_cli(vid=texto), _srv(vid=texto)])),
            "rules.Vu5": normativa.resolucion(
                {"clientValidationPresent": True},
                evidencia={"ES0902.Vu5": _r(clientes=[_cliente(texto)], evidencia=[
                    _cli(sup=texto), SRV])})["standards"]["ES0902"]["rules"]["Vu5"],
            "rules.Vu5 por la evidencia": normativa.resolucion(
                {"clientValidationPresent": True},
                evidencia={"ES0902.Vu5": _r(clientes=[_cliente(validaciones=[
                    _val(evidencia=["cli", texto], sref=texto)])],
                    evidencia=[CLI, _srv(texto)])})["standards"]["ES0902"]["rules"]["Vu5"],
            "seguridad": CHECK.para_seguridad(_r(clientes=[_cliente(validaciones=[
                _val(evidencia=["cli", texto], sref=texto)])], evidencia=[CLI, _srv(texto)]))[0],
        }
        for nombre, r in casos.items():
            t.no_contiene("E-63 `%s` en %s no sale" % (texto, nombre), "hunter2",
                          json.dumps(r, ensure_ascii=False))
        # 🔴 Ninguna clave de la salida es un dato: un id nunca llega a ser clave de un diccionario.
        for nombre in ("un clientSurfaceId", "un validationId", "constraint.description",
                       "un id de evidencia citado"):
            t.igual("E-63 con `%s` en %s ninguna clave nueva" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_claves)
        t.igual("E-63 con `%s` ninguna clave nueva en la senal" % texto, set(),
                set(_claves(casos["la senal"])) - base_senal)
        for nombre in ("rules.Vu5", "rules.Vu5 por la evidencia"):
            t.igual("E-63 con `%s` ninguna clave nueva en %s" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_unidad)
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu5_lib")
    for texto in ("contrasenia=hunter2abc", "contrasenia: hunter2abc", "pw=hunter2abc",
                  "pw: hunter2abc", "PIN=1234", "pin: 1234", "pin = 1234", "clave => hunter2abc",
                  "clave := hunter2abc", "pass>hunter2abc", "clave 'hunter2abc'",
                  "--password hunter2abc", "set password hunter2abc", "contraseña=hunter2abc",
                  "pass=hunter2abc"):
        t.verdadero("E-63 `%s` es una credencial" % texto, lib.es_secreto(texto))
    for texto in ("la clave del trámite es obligatoria", "se valida la contraseña mínima de 8",
                  "pass-through del valor", "la contrasenia tiene 8 caracteres",
                  "el pin del cajero", "spin: 3", "pwa: si", "pinta=roja"):
        t.verdadero("E-63 `%s` sale entera" % texto, not lib.es_secreto(texto))
        r = _r(clientes=[_cliente(validaciones=[_val(descripcion=texto)])])
        t.igual("E-63 `%s` sale entera en la descripcion" % texto, texto,
                _v(r)["constraint"]["description"])
    t.igual("E-63 y la regla de salida que se usa redacta las claves", {"[redactado]": 1},
            lib.depurar({"password=hunter2abc": 1}))
    t.verdadero("E-63 la regla de salida es la de la lib, no una copia",
                "SECRETOS" not in {n.id for n in ast.walk(_arbol()) if isinstance(n, ast.Name)}
                and CHECK._ev.__file__.endswith("evidencia.py"))
    for campo in ("password", "token", "accessToken", "cookie", "realValue"):
        con = dict(_prueba(), **{campo: "abc"})
        t.igual("E-63 un item con `%s` no cuenta" % campo, SIN_EQ, _solo_con(con)["state"])
        t.verdadero("E-63 el registro no acepta `%s`" % campo,
                    bool(CHECK.validar_schema({"version": "1.0", "clients": [
                        dict(_cliente(), **{campo: "abc"})]})))


def test_e64_lo_ilegible_que_nombra_la_validacion(t):
    """E-64."""
    for nombre, eid in (("una lista", ["x"]), ("un dict", {"k": "v"})):
        debil = dict(_debil(), evidenceId=eid)
        for forma, item in (("suelto", {"evidenceId": eid, "validations": [VID]}),
                            ("con forma de debil", debil)):
            t.igual("E-64 un id que es %s (%s) impide el PASS sin romper" % (nombre, forma),
                    SIN_EQ, _sin_excepcion(lambda: _estado(evidencia=EVIDENCIA + [item])))
            t.igual("E-64 un id que es %s (%s) no deja apagar la senal" % (nombre, forma),
                    "UNRESOLVED", _sin_excepcion(lambda: CHECK.senal(_caso(
                        clientes=[], evidencia=[_ausente(), dict(item, targets=["portal"])]))["value"]))
    mal = dict(_debil("mal"), outcome=["X"])
    t.igual("E-64 una mal formada no citada", SIN_EQ, _estado(evidencia=EVIDENCIA + [mal]))
    t.igual("E-64 una mal formada citada", SIN_EQ, _con_ademas(mal)["state"])
    t.igual("E-64 un responseStatus que no es un entero", SIN_EQ,
            _estado(evidencia=EVIDENCIA + [dict(_prueba(), responseStatus="403")]))
    t.igual("E-64 un responseStatus booleano", SIN_EQ,
            _estado(evidencia=EVIDENCIA + [dict(_prueba(), responseStatus=True)]))
    rep = _debil("rep")
    t.igual("E-64 una repetida no citada", SIN_EQ,
            _estado(evidencia=EVIDENCIA + [rep, copy.deepcopy(rep)]))
    t.igual("E-64 un id citado que no esta en el catalogo", SIN_EQ,
            _estado(clientes=[_cliente(validaciones=[_val(evidencia=["cli", "srv", "fantasma"])])]))
    nfd = unicodedata.normalize("NFD", "validación")
    nfc = unicodedata.normalize("NFC", "validación")
    t.igual("E-64 nombrar es igualdad en NFC", SIN_EQ,
            _estado(clientes=[_cliente(validaciones=[_val(vid=nfc, evidencia=["cli", "s"],
                                                          sref="s")])],
                    evidencia=[_cli(vid=nfc), _srv("s", vid=nfc),
                               dict(_srv("m", vid=nfd), outcome=1)]))
    t.igual("E-64 una ilegible de otra validacion no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_srv("m", vid="otra"), outcome=1)]))
    for nombre, eid in (("vacio", ""), ("en blanco", "  ")):
        vacia = dict(_srv(), evidenceId=eid)
        t.igual("E-64 un id %s no cuenta aunque se lo cite" % nombre, SIN_EQ,
                _estado(clientes=[_cliente(validaciones=[_val(evidencia=["cli", eid], sref=None)])],
                        evidencia=[CLI, vacia]))
    t.verdadero("E-64 ninguna es FAIL", _estado(evidencia=EVIDENCIA + [mal]) not in FALLAS)
    t.igual("E-64 y no tapa un FAIL", DEBIL,
            _estado(clientes=[_cliente(validaciones=[_val(evidencia=["cli", "srv", "debil"])])],
                    evidencia=EVIDENCIA + [_debil(), mal]))


def test_e65_un_solo_bloqueo(t):
    """E-65."""
    acepta = _prueba("INVALID_INPUT_ACCEPTED", environment="PRD")
    t.igual("E-65 impide el PASS aunque no se la cite", INSEGURA,
            _estado(evidencia=EVIDENCIA + [acepta]))
    en_el_alcance = _prueba("INVALID_INPUT_ACCEPTED", environment="PRD", validaciones=None,
                            targets=["portal"])
    no_aplica = _r(clientes=[], evidencia=[_ausente(), en_el_alcance])
    t.igual("E-65 la senal sigue en FALSE", "FALSE", no_aplica["signalValue"])
    t.igual("E-65 e impide el NOT_APPLICABLE igual", INSEGURA, no_aplica["state"])
    t.igual("E-65 y en seguridad tampoco vuelve a ser NOT_APPLICABLE", "UNRESOLVED",
            _vu5_en_seguridad(no_aplica)["result"])
    t.contiene("E-65 y lo impedido queda a la vista", INSEGURA, no_aplica["states"])
    t.igual("E-65 sin objetivo, lo mismo", SIN_OBJ,
            _estado(clientes=[], evidencia=[_ausente(), _prueba(
                "UNAVAILABLE", value="MISSING", validaciones=None, targets=["portal"])]))
    t.igual("E-65 una que nombra solo una validacion que no esta en el registro no mueve nada",
            "NOT_APPLICABLE", _estado(clientes=[], evidencia=[_ausente(), acepta]))
    t.igual("E-65 ni una que nombra una superficie fuera del alcance", "NOT_APPLICABLE",
            _estado(clientes=[], evidencia=[_ausente(), dict(en_el_alcance, targets=["otra"])]))
    t.igual("E-65 una ajena que dice rechazada no impide el NOT_APPLICABLE", "NOT_APPLICABLE",
            _estado(clientes=[], evidencia=[_ausente(), _prueba(environment="PRD")]))
    t.igual("E-65 y nunca tapa un FAIL", DEBIL,
            _estado(clientes=[_cliente(validaciones=[_val(evidencia=["cli", "srv", "debil"])])],
                    evidencia=EVIDENCIA + [_debil(), acepta]))
    bloqueada = _r(evidencia=EVIDENCIA + [acepta])
    t.igual("E-65 y lo bloqueado no usa evidencia", [], _v(bloqueada)["evidenceUsed"]["parity"])
    t.igual("E-65 un solo paso de bloqueo en el modulo", 1,
            len([n for n in ast.walk(_arbol())
                 if isinstance(n, ast.FunctionDef) and n.name == "_bloquear"]))
    t.igual("E-65 y lo llaman la validacion y el agregado", ["evaluar", "evaluar_validacion"],
            _llamadores("_bloquear"))


def test_e66_el_schema_cerrado(t):
    """E-66."""
    instalado = json.loads((REGLAS / "client-server-validation-parity.json").read_text(
        encoding="utf-8"))
    t.igual("E-66 el registro se instala vacio", {"version": "1.0", "clients": []}, instalado)
    t.igual("E-66 y valida", [], CHECK.validar_schema(instalado))
    t.igual("E-66 el cliente base valida", [],
            CHECK.validar_schema({"version": "1.0", "clients": [_cliente()]}))
    capas = {"la raiz": lambda d: d.update(extra=1),
             "un cliente": lambda d: d["clients"][0].update(extra=1),
             "una validacion": lambda d: d["clients"][0]["validations"][0].update(extra=1),
             "constraint": lambda d: d["clients"][0]["validations"][0]["constraint"].update(extra=1),
             "serverMapping": lambda d: d["clients"][0]["validations"][0]["serverMapping"].update(
                 extra=1)}
    for nombre, cambiar in capas.items():
        doc = {"version": "1.0", "clients": [_cliente()]}
        cambiar(doc)
        t.verdadero("E-66 una clave de mas en %s no valida" % nombre, bool(CHECK.validar_schema(doc)))
        r = CHECK.evaluar(dict(_caso(), clients=doc))
        t.verdadero("E-66 y el check no pasa con ese registro (%s)" % nombre, r["state"] != "PASS")
        t.contiene("E-66 y dice por que (%s)" % nombre, "no valida contra su schema",
                   " ".join(r["issues"]))
    esquema = json.loads((SCHEMAS / "client-server-validation-parity.schema.json").read_text(
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
    t.igual("E-66 cinco capas de objeto", 5, len(capas_del_schema))
    t.verdadero("E-66 todas cerradas",
                all(c.get("additionalProperties") is False for c in capas_del_schema))


def test_e67_un_cliente_fuera_del_alcance(t):
    """E-67."""
    fuera, ev = _otro("externo", "OTHER", "externo-requerido", OP)
    fuera = dict(fuera, evidence=[])
    r = _r(clientes=[_cliente(), fuera], evidencia=EVIDENCIA + ev[1:])
    t.igual("E-67 el caso sin el de afuera pasa", "PASS", _estado(evidencia=EVIDENCIA + ev[1:]))
    t.igual("E-67 un cliente fuera del alcance impide el PASS", SIN_COB, r["state"])
    t.igual("E-67 se evalua igual", "PASS", _c(r, "externo")["state"])
    t.igual("E-67 y dice que esta afuera", False, _c(r, "externo")["inScope"])
    t.igual("E-67 y se informa", ["externo"], r["coverage"]["clientsOutsideScope"])
    t.verdadero("E-67 y nunca es FAIL", r["state"] not in FALLAS)
    t.igual("E-67 en seguridad no cumple", "UNRESOLVED", _vu5_en_seguridad(r)["result"])
    solo = _r(clientes=[fuera], evidencia=ev[1:])
    t.igual("E-67 tambien cuando es el unico cliente", SIN_COB, solo["state"])
    roto, ev2 = _otro("externo", "OTHER", "externo-requerido", OP, paridad="SERVER_WEAKER",
                      valor="SERVER_WEAKER")
    roto = dict(roto, evidence=[])
    falla = _r(clientes=[_cliente(), roto], evidencia=EVIDENCIA + ev2[1:])
    t.igual("E-67 fuera del alcance no tapa una falla", DEBIL, falla["state"])


def test_e68_la_falla_establecida_gana_siempre(t):
    """E-68."""
    for nombre, falla, esperado, honesto in (
            ("SERVER_WEAKER", _debil(), DEBIL, {"paridad": "SERVER_WEAKER"}),
            ("MISSING", _falta(), FALTA, {"estado": "MISSING"})):
        cita = ["cli", falla["evidenceId"]]
        # La que dice que cumple, `srv`, esta en el catalogo y no se cita.
        declarada = _r(clientes=[_cliente(validaciones=[_val(
            evidencia=cita, sref=falla["evidenceId"], **honesto)])], evidencia=EVIDENCIA + [falla])
        negada = _r(clientes=[_cliente(validaciones=[_val(
            evidencia=cita, sref=falla["evidenceId"])])], evidencia=EVIDENCIA + [falla])
        t.igual("E-68 %s declarado, citado, con otra no citada que cumple: FAIL" % nombre, esperado,
                declarada["state"])
        t.igual("E-68 %s: el mismo resultado que con el registro diciendo que cumple" % nombre,
                (negada["state"], _v(negada)["state"]), (declarada["state"], _v(declarada)["state"]))
        t.igual("E-68 %s: y con la otra citada tambien" % nombre, esperado,
                _con_ademas(falla, **honesto)["state"])
        t.igual("E-68 %s: en seguridad es FAIL" % nombre, "NON_COMPLIANT",
                _vu5_en_seguridad(declarada)["result"])
    acepta = _prueba("INVALID_INPUT_ACCEPTED")
    t.igual("E-68 una prueba segura citada que acepta gana aunque otra diga que valida", FALTA,
            _con_ademas(acepta, _srv("srv-b", fuente="UNIT_TEST"))["state"])
    t.igual("E-68 lo no citado que dice que falla nunca es FAIL", SIN_EQ,
            _r(evidencia=EVIDENCIA + [_falta(), _debil()])["state"])


def test_e69_entrada_vacia_y_estado_informado(t):
    """E-69."""
    vacia = _cliente("backoffice", "BACKOFFICE", validaciones=[])
    r = _r([SUPERFICIE, BACKOFFICE], [_cliente(), vacia])
    t.igual("E-69 una entrada sin validaciones no cubre", SIN_COB, r["state"])
    t.igual("E-69 y la superficie queda sin cubrir", ["backoffice"], r["coverage"]["uncovered"])
    sin_op = _val(op="POST /no-existe", evidencia=["cli", "srv-x", "qa"], sref="srv-x")
    ev = [CLI, _srv("srv-x", op="POST /no-existe"),
          _prueba(environment="PRD", operations=["POST /no-existe"])]
    r = _r(clientes=[_cliente(validaciones=[sin_op])], evidencia=ev)
    t.igual("E-69 mapeo sin resolver y prueba insegura citada: sale el mapeo", SIN_MAPEO,
            _v(r)["state"])
    t.igual("E-69 y el agregado tambien", SIN_MAPEO, r["state"])
    t.contiene("E-69 con la prueba en states", INSEGURA, _v(r)["states"])
    t.contiene("E-69 y en el agregado", INSEGURA, r["states"])
    suelta = _prueba("INVALID_INPUT_ACCEPTED", environment="PRD", validaciones=None,
                     targets=["portal"])
    sin_senal = _r(clientes=[], evidencia=[suelta])
    t.igual("E-69 con la senal UNRESOLVED", "UNRESOLVED", sin_senal["signalValue"])
    t.igual("E-69 el estado es APPLICABILITY_UNRESOLVED", "APPLICABILITY_UNRESOLVED",
            sin_senal["state"])
    t.contiene("E-69 y el bloqueo queda en states", INSEGURA, sin_senal["states"])
    t.igual("E-69 una prueba insegura sola, sin otro sin resolver, sigue informandose", INSEGURA,
            _solo_con(_prueba(environment="PRD"))["state"])
