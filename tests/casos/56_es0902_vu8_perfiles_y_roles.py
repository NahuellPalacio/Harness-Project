# ES0902 §6 Vu8: los perfiles de usuarios armados en las aplicaciones respetan los roles asignados.
#
# Escenarios E-01 a E-61 de docs/cambios/es0902-vu8-perfiles-respetan-roles/spec.md. Cada E-nn es el
# VU8-nn del paquete con el mismo numero.
#
# 🔴 CASO es una API de tramites con un rol, `operador`, que sale de la base segun la arquitectura. La
# matriz de acceso dice que el perfil `perfil-operador` ve tramites y solo los propios. Un test de
# integracion prueba que el servidor lo permite, y un test de API prueba que niega borrar y ver todos.
# Las dos semanticas estan documentadas. Casi todo este archivo sale de romperlo. E-20 lo mira en PASS.
import ast
import copy
import importlib.util
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
AGENTES = RAIZ / "harnesses" / "desarrollo" / "agents"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import seguridad                      # noqa: E402
from orquestacion import normativa                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from orquestacion import plan as orq_plan               # noqa: E402
from orquestacion import refutacion as R                # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "role-profile-consistency.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu8_perfiles_y_roles")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu8"}
LOS_13 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "ROLE_ASSIGNMENT_SOURCE_UNRESOLVED", "ROLE_PROFILE_MAPPING_UNRESOLVED",
          "MULTI_ROLE_PROFILE_UNRESOLVED", "ROLE_CHANGE_PROPAGATION_UNRESOLVED",
          "OVER_PRIVILEGED_PROFILE", "UNDER_PRIVILEGED_PROFILE", "DIRECT_ACCESS_BYPASSES_ROLE",
          "ROLE_PROFILE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
NA = "NOT_APPLICABLE"
SIN_APLIC = "APPLICABILITY_UNRESOLVED"
FUENTE = "ROLE_ASSIGNMENT_SOURCE_UNRESOLVED"
MAPEO = "ROLE_PROFILE_MAPPING_UNRESOLVED"
VARIOS = "MULTI_ROLE_PROFILE_UNRESOLVED"
CAMBIO = "ROLE_CHANGE_PROPAGATION_UNRESOLVED"
DE_MAS = "OVER_PRIVILEGED_PROFILE"
DE_MENOS = "UNDER_PRIVILEGED_PROFILE"
SALTEO = "DIRECT_ACCESS_BYPASSES_ROLE"
INSEGURA = "ROLE_PROFILE_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"
FALLAS = ("FAIL", DE_MAS, DE_MENOS, SALTEO)
# Un JWT: `controles/lib/evidencia.py` no reconoce un token con prefijo de proveedor (`glpat-`), y
# eso esta anotado en PENDIENTES-FH.md. E-49 prueba la regla de salida que hay, no la que falta.
TOKEN = "eyJhbGciOiJSUzI1NiJ9" + ".eyJyZWFsbV9hY2Nlc3MiOnt9fQ.firma"

SUP = "api-tramites"
MAP = "m-operador"
ROL = "operador"
VER, BORRAR = "ver-tramite", "borrar-tramite"
PROPIOS, TODOS = "tramites-propios", "tramites-de-todos"


def _e(eid, fuente, establece, valor=None, sups=(SUP,), maps=None, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if sups is not None:
        base["surfaces"] = list(sups)
    if maps is not None:
        base["mappings"] = list(maps)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _roles(valor="PRESENT", fuente="APPLICATION_DATABASE_SCHEMA", eid="roles", **k):
    return _e(eid, fuente, "APPLICATION_ROLES", valor, **k)


def _fuente(ref="db-roles", roles=(ROL,), fuente="ARCHITECTURE_DOCUMENTATION", eid="fuente", **k):
    return _e(eid, fuente, "ROLE_ASSIGNMENT_SOURCE", ref, roles=list(roles), **k)


def _varios(valor="NOT_APPLICABLE", fuente="SECURITY_DOCUMENTATION", eid="varios", **k):
    return _e(eid, fuente, "MULTI_ROLE_SEMANTICS", valor, **k)


def _cambio(valor="RESOLVED", fuente="SESSION_CONFIGURATION", eid="cambio", **k):
    return _e(eid, fuente, "ROLE_CHANGE_SEMANTICS", valor, **k)


def _mapeo(perfil="perfil-operador", ops=(VER,), alcances=(PROPIOS,), mapping=MAP,
           fuente="ACCESS_CONTROL_MATRIX", eid="mapeo", **k):
    return _e(eid, fuente, "ROLE_PROFILE_MAPPING", perfil, sups=None, maps=[mapping],
              operations=list(ops), dataScopes=list(alcances), **k)


def _acceso(eid, valor, ops=(), alcances=(), fuente="INTEGRATION_AUTHORIZATION_TEST", mapping=MAP,
            **k):
    datos = dict(k)
    if ops:
        datos["operations"] = list(ops)
    if alcances:
        datos["dataScopes"] = list(alcances)
    return _e(eid, fuente, "ACCESS", valor, sups=None, maps=[mapping], **datos)


ROLES = _roles()
FUENTE_EV = _fuente()
VARIOS_EV = _varios()
CAMBIO_EV = _cambio()
MAPEO_EV = _mapeo()
SRV = _acceso("srv", "ALLOWED", [VER], [PROPIOS])
SRV_NO = _acceso("srv-no", "DENIED", [BORRAR], [TODOS], fuente="API_AUTHORIZATION_TEST")
EVIDENCIA = [ROLES, FUENTE_EV, VARIOS_EV, CAMBIO_EV, MAPEO_EV, SRV, SRV_NO]


def _map(mid=MAP, roles=(ROL,), perfil="perfil-operador", protegidas=(BORRAR, VER),
         alcances=(TODOS,), resultado="CONSISTENT", modo="INTEGRATION_TEST", identidad="qa-operador-1",
         evidencia=("mapeo", "srv", "srv-no")):
    return {"mappingId": mid, "assignedRoleRefs": list(roles), "expectedProfileRef": perfil,
            "observedProfileRef": None, "protectedOperationRefs": list(protegidas),
            "dataScopeRefs": list(alcances), "result": resultado, "verificationMode": modo,
            "testIdentityRef": identidad, "evidence": list(evidencia)}


def _sup(sid=SUP, mappings=None, estado="RESOLVED", ref="db-roles", varios="NOT_APPLICABLE",
         cambio="RESOLVED", evidencia=("fuente", "varios", "cambio"), ambiente="QA"):
    s = {"surfaceId": sid, "environment": ambiente,
         "roleAssignmentSource": {"status": estado, "sourceRef": ref},
         "mappings": [_map()] if mappings is None else list(mappings),
         "evidence": list(evidencia)}
    if varios is not None:
        s["multiRoleSemantics"] = varios
    if cambio is not None:
        s["roleChangeSemantics"] = cambio
    return s


def _reg(superficies=None):
    return {"version": "1.0",
            "surfaces": copy.deepcopy([_sup()] if superficies is None else superficies)}


def _caso(registro=None, evidencia=None):
    return {"registry": _reg() if registro is None else copy.deepcopy(registro),
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}


def _r(registro=None, evidencia=None, senal=None):
    return CHECK.evaluar(_caso(registro, evidencia), senal)


def _estado(registro=None, evidencia=None):
    return _r(registro, evidencia)["state"]


def _s(r, sid=SUP):
    return [s for s in r["surfaces"] if s["surfaceId"] == sid][0]


def _m(r, mid=MAP, sid=SUP):
    return [m for m in _s(r, sid)["mappings"] if m["mappingId"] == mid][0]


def _fila(m, ref):
    return [c for c in m["comparison"] if c["ref"] == ref][0]


def _sin(*ids_y_mas):
    """La evidencia base sin los ids que se nombran, mas los items que se pasan."""
    ids = [x for x in ids_y_mas if isinstance(x, str)]
    mas = [x for x in ids_y_mas if isinstance(x, dict)]
    return [x for x in EVIDENCIA if x["evidenceId"] not in ids] + mas


def _con(*items, quitar=(), mapping_ev=None, **cambios_map):
    """El caso con `items` agregados y citados desde el mapping."""
    citas = list(mapping_ev) if mapping_ev is not None else (
        [i for i in ("mapeo", "srv", "srv-no") if i not in quitar] + [x["evidenceId"] for x in items])
    return _r(_reg([_sup(mappings=[_map(evidencia=citas, **cambios_map)])]), _sin(*quitar, *items))


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


def _json(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


def _vu8_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu8", ev, sen, MATRIZ)


def _unidad(r, senal=True):
    senales = {"applicationRolesPresent": senal} if senal is not None else {}
    return normativa.resolucion(senales, evidencia={"ES0902.Vu8": r})["standards"]["ES0902"]["rules"]["Vu8"]


def _de_control_pasa(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": ["ev-%s" % regla]}
                               for c in fila["policies"] + fila["checks"] + fila["reviews"]}}


PRUEBA = dict(environment="QA", authorized=True, syntheticIdentities=True)


def _prueba(eid, valor, ops=(), alcances=(), **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _acceso(eid, valor, ops, alcances, fuente="AUTHORIZED_QA_ROLE_TEST", **datos)


def _segundo(mid="m-auditor", rol="auditor", ops=("exportar",), resultado_srv="ALLOWED", citar=True):
    """Otro mapping de otro rol en la misma superficie, sostenido."""
    evid = [_mapeo("perfil-%s" % rol, ops, (), mid, eid="mapeo-%s" % mid),
            _acceso("srv-%s" % mid, resultado_srv, ops, (), mapping=mid)]
    m = _map(mid, [rol], "perfil-%s" % rol, protegidas=list(ops), alcances=(),
             evidencia=[x["evidenceId"] for x in evid] if citar else [])
    return m, evid


def _con_segundo(**k):
    m, evid = _segundo(**k)
    return _r(_reg([_sup(mappings=[_map(), m])]),
              _sin("fuente", _fuente(roles=[ROL, m["assignedRoleRefs"][0]]), *evid))


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01."""
    t.igual("E-01 la fila", "ES0902.Vu8", seguridad.regla("Vu8", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu8", CHECK.CLAVE)
    caminos = (("pasa", _r()), ("vacio", CHECK.evaluar({})),
               ("falla", _con(_acceso("mas", "ALLOWED", ["anular"]))),
               ("no aplica", CHECK.evaluar({"registry": {"version": "1.0", "surfaces": []},
                                            "evidence": [_roles("ABSENT", "SECURITY_DOCUMENTATION")]})),
               ("registro invalido", CHECK.evaluar({"registry": {"surfaces": 1}})))
    for nombre, r in caminos:
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu8", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu8", _vu8_en_seguridad(r)["ruleKey"])
        t.igual("E-01 y en el libro (%s)" % nombre, "ES0902.Vu8",
                prod.desde_regla(_vu8_en_seguridad(r), "GCBA-8001", {"project": "P"},
                                 "2026-09-25T10:00:00")[0]["details"]["ruleKey"])
    t.igual("E-01 y en la refutacion", "ES0902.Vu8",
            CHECK.para_refutacion(_r(), {"standard": {"ruleKey": "ES0902.Vu8"}, "workUnitId": "WU-1",
                                         "evidenceFingerprint": "h", "repoRevision": "r"})["ruleKey"])


def test_e02_los_ids(t):
    """E-02."""
    vu8 = seguridad.regla("Vu8", MATRIZ)
    t.igual("E-02 CONDITIONAL", "CONDITIONAL", vu8["applicability"]["mode"])
    t.igual("E-02 la senal", ["applicationRolesPresent"], vu8["applicability"]["signals"])
    t.igual("E-02 la policy", ["user-profile-role-enforcement-required"], vu8["policies"])
    t.igual("E-02 el check", ["role-profile-consistency"], vu8["checks"])
    t.igual("E-02 cero reviews", [], vu8["reviews"])
    t.igual("E-02 el modulo", ("role-profile-consistency", "user-profile-role-enforcement-required",
                               "applicationRolesPresent"),
            (CHECK.CONTROL, CHECK.POLICY, CHECK.SENAL))
    t.igual("E-02 la senal que produce el modulo es la de la matriz", "applicationRolesPresent",
            CHECK.senal(_caso())["signalId"])
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("user-profile-role-enforcement-required", "POLICY",
             "controles/policies/user-profile-role-enforcement-required.md"),
            ("role-profile-consistency", "CHECK", "controles/checks/role-profile-consistency.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.igual("E-02 %s regla" % cid, "Vu8", registro[cid]["rule"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    gobierno = (REGLAS / "es0902-vu8-governance.md").read_text(encoding="utf-8")
    for trozo in ("ruleKey: ES0902.Vu8", "mode: CONDITIONAL", "- applicationRolesPresent",
                  "- user-profile-role-enforcement-required", "- role-profile-consistency",
                  "reviews: []"):
        t.contiene("E-02 el gobierno declara `%s`" % trozo, trozo, gobierno)
    t.contiene("E-02 la senal tiene su documento", "# Signal: applicationRolesPresent",
               (REGLAS / "es0902-vu8-application-roles-present-signal.md").read_text(encoding="utf-8"))
    t.contiene("E-02 el check tiene su documento", "# Check: role-profile-consistency",
               (REGLAS / "es0902-vu8-role-profile-consistency-check.md").read_text(encoding="utf-8"))
    politica = (CONTROLES / "policies" / "user-profile-role-enforcement-required.md"
                ).read_text(encoding="utf-8")
    t.contiene("E-02 la policy declara su id", "id: user-profile-role-enforcement-required", politica)
    t.contiene("E-02 y su regla", "rule: Vu8", politica)


def test_e03_los_dos_agentes(t):
    """E-03."""
    t.igual("E-03 los agentes, en el orden de la matriz", ["dev-security", "dev-backend"],
            seguridad.regla("Vu8", MATRIZ)["primaryAgents"])
    gobierno = (REGLAS / "es0902-vu8-governance.md").read_text(encoding="utf-8")
    t.contiene("E-03 el gobierno los declara", "primaryAgents:\n  - dev-security\n  - dev-backend",
               gobierno.replace("\r\n", "\n"))
    ids = {a["id"] for a in c_reg.cargar()["agents"]}
    for agente in ("dev-security", "dev-backend"):
        t.verdadero("E-03 %s esta en el registro de agentes" % agente, agente in ids)


def test_e04_nada_nuevo(t):
    """E-04."""
    registro = c_reg.cargar()
    t.igual("E-04 diez agentes", 10, len(registro["agents"]))
    t.igual("E-04 los mismos once archivos de agentes, con el refutador", 11,
            len([p for p in AGENTES.glob("*.md")]))
    t.igual("E-04 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-04 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-04 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-04 y Vu8 no tiene algoritmo propio", "Vu8" not in seguridad.ALGORITMOS)
    t.igual("E-04 los documentos de Vu8 son los tres del paquete",
            ["es0902-vu8-application-roles-present-signal.md", "es0902-vu8-governance.md",
             "es0902-vu8-role-profile-consistency-check.md"],
            sorted(p.name for p in REGLAS.glob("es0902-vu8-*")))
    senales = sorted(seguridad.senales_declaradas(MATRIZ))
    t.igual("E-04 las senales siguen siendo las de la matriz, sin una nueva", sorted({
        s for r in seguridad.reglas(MATRIZ) for s in r["applicability"].get("signals") or []}), senales)
    t.igual("E-04 y son quince", 15, len(senales))


# -- La senal -------------------------------------------------------------------

def _senal(evidencia, registro=None):
    return CHECK.derivar({"registry": registro if registro is not None else
                          {"version": "1.0", "surfaces": []}, "evidence": evidencia})["value"]


def test_e05_un_modelo_de_roles_enciende(t):
    """E-05."""
    for fuente in ("BACKEND_AUTHORIZATION_CODE", "ARCHITECTURE_DOCUMENTATION", "SOURCE_CODE"):
        t.igual("E-05 %s PRESENT enciende" % fuente, "TRUE", _senal([_roles(fuente=fuente)]))
    t.igual("E-05 la senal producida dice TRUE", "TRUE", CHECK.senal(_caso())["value"])
    t.igual("E-05 y la salida lo lleva", "TRUE", _r()["signalValue"])
    t.igual("E-05 una debil sola no enciende", "UNRESOLVED",
            _senal([_roles(fuente="AGENT_STATEMENT")]))


def test_e06_roles_en_la_base(t):
    """E-06."""
    t.igual("E-06 los roles en la base encienden", "TRUE",
            _senal([_roles(fuente="APPLICATION_DATABASE_SCHEMA")]))
    t.igual("E-06 y el caso sigue a PASS", "PASS", _estado())


def test_e07_roles_por_claims_o_grupos(t):
    """E-07."""
    for fuente in ("IDENTITY_PROVIDER_CONFIGURATION", "TOKEN_CLAIM_PRESENCE"):
        t.igual("E-07 %s enciende" % fuente, "TRUE", _senal([_roles(fuente=fuente)]))
    t.igual("E-07 y con la senal de grupos el caso llega a PASS", "PASS",
            _estado(evidencia=_sin("roles", _roles(fuente="IDENTITY_PROVIDER_CONFIGURATION"))))


def test_e08_sin_enum_role_no_apaga(t):
    """E-08."""
    for fuente in ("SOURCE_CODE", "NAMING_CONVENTION", "REPOSITORY_DEPENDENCY"):
        ev = [_roles("ABSENT", fuente)]
        t.igual("E-08 %s ABSENT no apaga" % fuente, "UNRESOLVED", _senal(ev))
        r = CHECK.evaluar({"registry": {"version": "1.0", "surfaces": []}, "evidence": ev})
        t.igual("E-08 %s ABSENT da APPLICABILITY_UNRESOLVED" % fuente, SIN_APLIC, r["state"])
        t.verdadero("E-08 %s ABSENT nunca da NOT_APPLICABLE" % fuente, r["state"] != NA)


def test_e09_una_ausencia_autoritativa_apaga(t):
    """E-09."""
    ev = [_roles("ABSENT", "ARCHITECTURE_DOCUMENTATION")]
    t.igual("E-09 FALSE", "FALSE", _senal(ev))
    r = CHECK.evaluar({"registry": {"version": "1.0", "surfaces": []}, "evidence": ev})
    t.igual("E-09 NOT_APPLICABLE", NA, r["state"])
    t.igual("E-09 la senal viaja en FALSE a seguridad", {"applicationRolesPresent": False},
            CHECK.para_seguridad(r)[1])
    t.igual("E-09 y en seguridad no aplica", "NOT_APPLICABLE", _vu8_en_seguridad(r)["applicability"])
    t.igual("E-09 con el registro instalado vacio tambien", NA,
            CHECK.evaluar({"evidence": ev})["state"])


def test_e10_lo_incompleto_no_resuelve(t):
    """E-10."""
    ausente = _roles("ABSENT", "ARCHITECTURE_DOCUMENTATION", eid="ausente")
    torcida = {"evidenceId": "torcida", "sourceType": "SECURITY_DOCUMENTATION", "reference": "x",
               "establishes": ["APPLICATION_ROLES"], "value": "PRESENT", "password": "x"}
    for nombre, ev, registro in (
            ("el vacio", [], None),
            ("una debil", [_roles(fuente="README_STATEMENT")], None),
            ("un ABSENT con una superficie registrada", [ausente], _reg()),
            ("un ABSENT con un item ilegible", [ausente, torcida], None),
            ("un ABSENT con un PRESENT inseguro", [ausente, _prueba("p", "ALLOWED", [VER],
                                                   environment="PRD")
                                                   | {"establishes": ["APPLICATION_ROLES"],
                                                      "value": "PRESENT"}], None),
            ("un registro invalido", [_roles()], {"surfaces": 1})):
        t.igual("E-10 %s: UNRESOLVED" % nombre, "UNRESOLVED", _senal(ev, registro))
        caso = {"evidence": ev, "registry": registro or {"version": "1.0", "surfaces": []}}
        t.igual("E-10 %s: APPLICABILITY_UNRESOLVED" % nombre, SIN_APLIC, CHECK.evaluar(caso)["state"])
    t.igual("E-10 un PRESENT legible le gana a un ABSENT", "TRUE", _senal([ausente, _roles()]))
    t.igual("E-10 una senal externa TRUE sobre un sin resolver vale", "TRUE",
            CHECK.evaluar({"evidence": []}, {"value": "TRUE"})["signalValue"])
    t.igual("E-10 una senal externa FALSE contra un TRUE derivado no vale", "UNRESOLVED",
            _r(senal=False)["signalValue"])


# -- La fuente de los roles ---------------------------------------------------------

def test_e11_la_fuente_se_registra(t):
    """E-11."""
    fuente = _s(_r())["roleAssignmentSource"]
    t.igual("E-11 resuelta", True, fuente["resolved"])
    t.igual("E-11 con su sourceRef", "db-roles", fuente["sourceRef"])
    t.igual("E-11 con la evidencia que la sostiene", ["fuente"], fuente["evidenceUsed"])
    t.igual("E-11 con los roles que asigna", [ROL], fuente["roles"])
    t.verdadero("E-11 y la evidencia viaja a seguridad",
                "fuente" in CHECK.para_seguridad(_r())[0]["controlResults"][CHECK.CONTROL]["evidence"])


def test_e12_la_fuente_no_sale_de_un_nombre(t):
    """E-12."""
    for fuente in ("NAMING_CONVENTION", "SOURCE_CODE", "README_STATEMENT"):
        r = _r(evidencia=_sin("fuente", _fuente(fuente=fuente)))
        t.igual("E-12 %s no resuelve la fuente" % fuente, FUENTE, r["state"])
        t.igual("E-12 %s queda como insuficiente" % fuente, ["fuente"],
                _s(r)["roleAssignmentSource"]["insufficient"])
    nombres = _r(_reg([_sup(ref="roles-de-la-app")]), _sin("fuente", _fuente("otra-cosa")))
    t.igual("E-12 un sourceRef que no es el de la evidencia no se resuelve", FUENTE, nombres["state"])


def test_e13_sin_fuente(t):
    """E-13."""
    t.igual("E-13 sin evidencia de fuente", FUENTE, _estado(evidencia=_sin("fuente")))
    t.igual("E-13 declarada UNRESOLVED", FUENTE, _estado(_reg([_sup(estado="UNRESOLVED")])))
    t.igual("E-13 sin citarla", FUENTE, _estado(_reg([_sup(evidencia=("varios", "cambio"))])))
    dos = _r(evidencia=EVIDENCIA + [_fuente("keycloak-grupos", eid="otra-fuente")])
    t.igual("E-13 dos fuentes autoritativas distintas", FUENTE, dos["state"])
    t.igual("E-13 y la otra queda como contradiccion", ["otra-fuente"],
            _s(dos)["roleAssignmentSource"]["contradictedBy"])
    t.igual("E-13 el registro vacio con la senal en TRUE", FUENTE,
            _estado({"version": "1.0", "surfaces": []}))


def test_e14_autenticar_no_es_la_fuente(t):
    """E-14."""
    r = _r(evidencia=_sin("fuente", _fuente(fuente="AUTHENTICATION_SUCCESS")))
    t.igual("E-14 un login exitoso no resuelve la fuente", FUENTE, r["state"])
    login = _acceso("login", "ALLOWED", [VER], [PROPIOS], fuente="AUTHENTICATION_SUCCESS")
    r = _con(login, quitar=("srv",))
    t.verdadero("E-14 ni prueba el acceso", r["state"] != "PASS")
    t.igual("E-14 y queda como insuficiente", ["login"], _m(r)["insufficient"])


# -- El mapeo -------------------------------------------------------------------

def test_e15_el_mapeo_resuelve_lo_esperado(t):
    """E-15."""
    m = _m(_r())
    t.igual("E-15 lo esperado", {"operations": [VER], "dataScopes": [PROPIOS]}, m["expected"])
    t.igual("E-15 sale del mapeo citado", ["mapeo"], m["evidenceUsed"]["mapping"])
    t.igual("E-15 cumple", "PASS", m["state"])


def test_e16_el_nombre_del_rol_no_define_permisos(t):
    """E-16."""
    admin = _map("m-admin", ["admin"], "admin", evidencia=["srv-admin"])
    r = _r(_reg([_sup(mappings=[_map(), admin])]),
           _sin("fuente", _fuente(roles=[ROL, "admin"]),
                _acceso("srv-admin", "ALLOWED", [VER, BORRAR], mapping="m-admin")))
    t.igual("E-16 un rol `admin` sin mapeo no tiene acceso esperado",
            {"operations": [], "dataScopes": []}, _m(r, "m-admin")["expected"])
    t.igual("E-16 y queda sin resolver", MAPEO, _m(r, "m-admin")["state"])
    nombrado = _r(evidencia=_sin("mapeo", _mapeo(fuente="NAMING_CONVENTION")))
    t.igual("E-16 un NAMING_CONVENTION no es mapeo", MAPEO, nombrado["state"])
    for nombre in ("admin", "administrator", "superuser", "root", "ROLE_ADMIN", "operador", "auditor"):
        t.verdadero("E-16 el modulo no tiene el rol `%s` como literal operativo" % nombre,
                    not any(nombre.lower() == x.lower() for x in _literales()))
    renombrado = json.loads(json.dumps(_caso()).replace('"operador"', '"admin"'))
    t.igual("E-16 llamar `admin` al rol no cambia el resultado", _r()["state"],
            CHECK.evaluar(renombrado)["state"])


def test_e17_sin_mapeo(t):
    """E-17."""
    t.igual("E-17 sin evidencia de mapeo", MAPEO, _estado(evidencia=_sin("mapeo")))
    t.igual("E-17 sin mappings", MAPEO, _estado(_reg([_sup(mappings=[])])))
    r = _r(evidencia=_sin("fuente", _fuente(roles=[ROL, "auditor"])))
    t.igual("E-17 un rol de la fuente sin mapping", MAPEO, r["state"])
    t.igual("E-17 y queda nombrado", ["auditor"], _s(r)["coverage"]["missingRoles"])
    t.igual("E-17 un mapeo con otro perfil no es el del mapping", MAPEO,
            _estado(evidencia=_sin("mapeo", _mapeo("perfil-otro"))))
    vacio = _r(_reg([_sup(mappings=[_map(protegidas=(), alcances=(), evidencia=["mapeo"])])]),
               _sin("mapeo", "srv", "srv-no", _mapeo(ops=(), alcances=())))
    t.igual("E-17 un mapeo sin nada que comparar no cumple", MAPEO, vacio["state"])
    t.igual("E-17 dos mapeos que no coinciden", MAPEO,
            _estado(evidencia=EVIDENCIA + [_mapeo(ops=[VER, BORRAR], eid="mapeo-2")]))


def test_e18_ningun_framework(t):
    """E-18."""
    for nombre in ("spring", "preauthorize", "rolesallowed", "secured", "django", "casbin",
                   "realm_access", "resource_access", "keycloak", "role_admin", "role_user", "jwt", "@"):
        t.verdadero("E-18 el modulo no tiene `%s` en ningun literal operativo" % nombre,
                    not any(nombre in x.lower() for x in _literales()))
    base = _r()
    for referencia in ("@PreAuthorize(\"hasRole('OPERADOR')\")", "app.use(requireRole('operador'))",
                       "casbin policy p, operador, tramites, read"):
        ev = copy.deepcopy(EVIDENCIA)
        for x in ev:
            if x["evidenceId"] in ("srv", "srv-no"):
                x["reference"] = referencia
        t.igual("E-18 `%s` da el mismo resultado" % referencia, _json(base), _json(_r(evidencia=ev)))


def test_e19_grupos_claims_y_permisos(t):
    """E-19."""
    for modelo, fuente, rol in (("grupos", "IDENTITY_PROVIDER_CONFIGURATION", "grupo:mesa-de-entradas"),
                                ("claims", "IDENTITY_PROVIDER_CONFIGURATION", "claim:tramites.operador"),
                                ("permisos", "APPLICATION_DATABASE_SCHEMA", "permset:lectura-tramites")):
        r = _r(_reg([_sup(mappings=[_map(roles=[rol])])]),
               _sin("fuente", _fuente(roles=[rol], fuente=fuente)))
        t.igual("E-19 un modelo de %s llega a PASS" % modelo, "PASS", r["state"])


# -- La comparacion -------------------------------------------------------------

def test_e20_igual_es_consistente(t):
    """E-20."""
    r = _r()
    t.igual("E-20 PASS", "PASS", r["state"])
    t.igual("E-20 el mapping es CONSISTENT", "CONSISTENT", _m(r)["result"])
    t.igual("E-20 cada fila de la comparacion es CONSISTENT", ["CONSISTENT"] * 4,
            [c["result"] for c in _m(r)["comparison"]])
    t.igual("E-20 y compara lo esperado y lo protegido", sorted([VER, BORRAR, PROPIOS, TODOS]),
            sorted(c["ref"] for c in _m(r)["comparison"]))
    t.igual("E-20 en seguridad cumple", "COMPLIANT", _vu8_en_seguridad(r)["result"])


def test_e21_una_operacion_de_mas(t):
    """E-21."""
    r = _con(_acceso("mas", "ALLOWED", ["anular-tramite"], fuente="API_AUTHORIZATION_TEST"))
    t.igual("E-21 una operacion permitida y no esperada", DE_MAS, r["state"])
    t.igual("E-21 el mapping es OVER", DE_MAS, _m(r)["result"])
    t.igual("E-21 en seguridad no cumple", "NON_COMPLIANT", _vu8_en_seguridad(r)["result"])
    protegida = _con(_acceso("srv-no", "DENIED", alcances=[TODOS], fuente="API_AUTHORIZATION_TEST"),
                     _acceso("borra", "ALLOWED", [BORRAR], fuente="API_AUTHORIZATION_TEST"),
                     quitar=("srv-no",), mapping_ev=["mapeo", "srv", "srv-no", "borra"])
    t.igual("E-21 una operacion protegida permitida por el servidor", DE_MAS, protegida["state"])
    t.igual("E-21 y su fila es OVER", DE_MAS, _fila(_m(protegida), BORRAR)["result"])


def test_e22_un_alcance_de_datos_de_mas(t):
    """E-22."""
    r = _con(_acceso("srv-no", "DENIED", [BORRAR], fuente="API_AUTHORIZATION_TEST"),
             _acceso("todos", "ALLOWED", alcances=[TODOS], fuente="API_AUTHORIZATION_TEST"),
             quitar=("srv-no",), mapping_ev=["mapeo", "srv", "srv-no", "todos"])
    t.igual("E-22 un alcance mas ancho", DE_MAS, r["state"])
    t.igual("E-22 su fila es de alcance y es OVER", ("dataScope", DE_MAS),
            (_fila(_m(r), TODOS)["dimension"], _fila(_m(r), TODOS)["result"]))
    fuera = _con(_acceso("ajeno", "ALLOWED", alcances=["tramites-de-otra-area"],
                         fuente="API_AUTHORIZATION_TEST"))
    t.igual("E-22 un alcance que nadie lista, permitido, tambien", DE_MAS, fuera["state"])
    solo_cliente = _con(_acceso("srv", "ALLOWED", [VER]), _ui("vista", "ALLOWED", []) | {
        "dataScopes": [PROPIOS]}, quitar=("srv",), mapping_ev=["mapeo", "srv", "srv-no", "vista"])
    t.igual("E-22 un alcance de datos es siempre del servidor: el cliente solo no lo resuelve",
            "UNRESOLVED", _fila(_m(solo_cliente), PROPIOS)["result"])


def test_e23_una_operacion_de_menos(t):
    """E-23."""
    r = _con(_acceso("srv", "DENIED", [VER], [PROPIOS]), quitar=("srv",),
             mapping_ev=["mapeo", "srv", "srv-no"])
    t.igual("E-23 una operacion esperada negada", DE_MENOS, r["state"])
    t.igual("E-23 el mapping es UNDER", DE_MENOS, _m(r)["result"])
    t.verdadero("E-23 y falla", r["state"] in FALLAS)
    t.igual("E-23 en seguridad no cumple", "NON_COMPLIANT", _vu8_en_seguridad(r)["result"])


def test_e24_la_severidad_no_es_el_resultado(t):
    """E-24."""
    for nombre, construir in (
            ("OVER", lambda sev: _con(_acceso("mas", "ALLOWED", ["anular-tramite"], severity=sev)
                                      if sev else _acceso("mas", "ALLOWED", ["anular-tramite"]))),
            ("UNDER", lambda sev: _con(_acceso("srv", "DENIED", [VER], [PROPIOS], severity=sev)
                                       if sev else _acceso("srv", "DENIED", [VER], [PROPIOS]),
                                       quitar=("srv",), mapping_ev=["mapeo", "srv", "srv-no"]))):
        base = _json(construir(None))
        for sev in ("INFO", "LOW", "HIGH", "CRITICAL"):
            t.igual("E-24 %s con severidad %s: la misma salida" % (nombre, sev), base,
                    _json(construir(sev)))
    leve = _con(_acceso("srv", "DENIED", [VER], [PROPIOS], severity="LOW"), quitar=("srv",),
                mapping_ev=["mapeo", "srv", "srv-no"])
    grave = _con(_acceso("mas", "ALLOWED", ["anular-tramite"], severity="CRITICAL"))
    t.igual("E-24 un UNDER leve y un OVER grave fallan igual en seguridad",
            ("NON_COMPLIANT", "NON_COMPLIANT"),
            (_vu8_en_seguridad(leve)["result"], _vu8_en_seguridad(grave)["result"]))
    pasa = _r(evidencia=[dict(x, severity="CRITICAL") for x in EVIDENCIA])
    t.igual("E-24 y una severidad alta no tumba un PASS", "PASS", pasa["state"])


def test_e25_un_mapping_inconsistente_tumba_el_agregado(t):
    """E-25."""
    r = _con_segundo(resultado_srv="DENIED")
    t.igual("E-25 el agregado falla", DE_MENOS, r["state"])
    t.igual("E-25 aunque el operador cumpla", "PASS", _m(r)["state"])
    t.igual("E-25 el auditor es el que falla", DE_MENOS, _m(r, "m-auditor")["state"])
    t.igual("E-25 con los dos sanos pasa", "PASS", _con_segundo()["state"])


# -- El servidor y el cliente ----------------------------------------------------------

def _ui(eid, valor, ops, fuente="FRONTEND_ROLE_GUARD"):
    return _acceso(eid, valor, ops, fuente=fuente)


def test_e26_un_boton_escondido_no_prueba_nada(t):
    """E-26."""
    for fuente in ("FRONTEND_ROLE_GUARD", "UI_VISIBILITY_CONFIGURATION", "UI_TEST"):
        r = _con(_acceso("srv-no", "DENIED", alcances=[TODOS], fuente="API_AUTHORIZATION_TEST"),
                 _ui("boton", "DENIED", [BORRAR], fuente), quitar=("srv-no",),
                 mapping_ev=["mapeo", "srv", "srv-no", "boton"])
        t.igual("E-26 %s escondiendo borrar no alcanza" % fuente, MAPEO, r["state"])
        t.igual("E-26 %s: la fila de borrar queda sin resolver" % fuente, "UNRESOLVED",
                _fila(_m(r), BORRAR)["result"])


def test_e27_el_acceso_directo_saltea_el_rol(t):
    """E-27."""
    r = _con(_acceso("srv-no", "DENIED", alcances=[TODOS], fuente="API_AUTHORIZATION_TEST"),
             _ui("boton", "DENIED", [BORRAR]),
             _acceso("directo", "ALLOWED", [BORRAR], fuente="API_AUTHORIZATION_TEST"),
             quitar=("srv-no",), mapping_ev=["mapeo", "srv", "srv-no", "boton", "directo"])
    t.igual("E-27 el cliente niega y el servidor permite", SALTEO, r["state"])
    t.igual("E-27 el mapping lo dice", SALTEO, _m(r)["result"])
    t.verdadero("E-27 y falla", r["state"] in FALLAS)
    t.igual("E-27 en seguridad no cumple", "NON_COMPLIANT", _vu8_en_seguridad(r)["result"])
    t.igual("E-27 en seguridad los controles dicen FAIL", "FAIL",
            CHECK.para_seguridad(r)[0]["controlResults"][CHECK.CONTROL]["result"])


def test_e28_el_servidor_rechaza(t):
    """E-28."""
    r = _r()
    fila = _fila(_m(r), BORRAR)
    t.igual("E-28 el servidor niega borrar al operador", ["srv-no"], fila["server"]["denied"])
    t.igual("E-28 y eso es consistente", "CONSISTENT", fila["result"])
    t.igual("E-28 y el caso pasa", "PASS", r["state"])


def test_e29_cliente_y_servidor_por_separado(t):
    """E-29."""
    r = _con(_ui("boton", "DENIED", [BORRAR]))
    fila = _fila(_m(r), BORRAR)
    t.igual("E-29 la guarda del cliente queda aparte", {"allowed": [], "denied": ["boton"]},
            fila["client"])
    t.igual("E-29 y la del servidor tambien", {"allowed": [], "denied": ["srv-no"]}, fila["server"])
    t.igual("E-29 pasa", "PASS", r["state"])
    manda = _con(_ui("boton", "ALLOWED", [BORRAR]))
    t.igual("E-29 con el servidor negando, un cliente que muestra no cambia el resultado", "CONSISTENT",
            _fila(_m(manda), BORRAR)["result"])
    t.igual("E-29 y el caso sigue en PASS", "PASS", manda["state"])
    # Primera refutacion: un cliente NO citado que el servidor contradice bloqueaba el PASS.
    for nombre, cliente in (("niega lo que el servidor permite", _ui("guarda", "DENIED", [VER])),
                            ("muestra lo que el servidor niega", _ui("guarda", "ALLOWED", [BORRAR]))):
        t.igual("E-29 un cliente no citado que %s no cambia nada" % nombre, "PASS",
                _estado(evidencia=EVIDENCIA + [cliente]))
    # Segunda refutacion: el mismo cliente, ilegible, todavia pesaba.
    for outcome in ("INCONCLUSIVE", "REFUTED"):
        for nombre, cliente in (("niega", _ui("guarda", "DENIED", [VER])),
                                ("muestra", _ui("guarda", "ALLOWED", [BORRAR]))):
            t.igual("E-29 un cliente no citado e ilegible (%s) que %s no cambia nada" % (outcome, nombre),
                    "PASS", _estado(evidencia=EVIDENCIA + [dict(cliente, outcome=outcome)]))
    t.igual("E-29 pero un servidor no citado que permite de mas si bloquea", MAPEO,
            _estado(evidencia=EVIDENCIA + [_acceso("otro-srv", "ALLOWED", [BORRAR],
                                                   fuente="API_AUTHORIZATION_TEST")]))


def test_e30_una_opcion_de_presentacion_local(t):
    """E-30."""
    tema = _ui("tema", "ALLOWED", ["tema-oscuro"], fuente="UI_TEST")
    ev = _sin("mapeo", _mapeo(ops=[VER, "tema-oscuro"]), tema)
    r = _r(_reg([_sup(mappings=[_map(evidencia=["mapeo", "srv", "srv-no", "tema"])])]), ev)
    t.igual("E-30 una opcion local se resuelve con el cliente", "PASS", r["state"])
    t.igual("E-30 y no exige servidor", "CONSISTENT", _fila(_m(r), "tema-oscuro")["result"])
    protegida = _r(_reg([_sup(mappings=[_map(protegidas=[BORRAR, VER, "tema-oscuro"],
                                             evidencia=["mapeo", "srv", "srv-no", "tema"])])]), ev)
    t.igual("E-30 la misma opcion declarada protegida si lo exige", MAPEO, protegida["state"])
    # Primera refutacion: la tabla hacia fallar una diferencia de presentacion local (paquete, §6).
    mostrada = _con(_ui("tema", "ALLOWED", ["tema-oscuro"], fuente="UI_TEST"))
    t.igual("E-30 una opcion local mostrada sin esperarla no falla", "PASS", mostrada["state"])
    escondida = _r(_reg([_sup(mappings=[_map(evidencia=["mapeo", "srv", "srv-no", "tema"])])]),
                   _sin("mapeo", _mapeo(ops=[VER, "tema-oscuro"]),
                        _ui("tema", "DENIED", ["tema-oscuro"], fuente="UI_TEST")))
    t.igual("E-30 ni una esperada que el cliente esconde", "PASS", escondida["state"])
    del_servidor = _con(_acceso("tema", "ALLOWED", ["tema-oscuro"], fuente="API_AUTHORIZATION_TEST"))
    t.igual("E-30 pero si el servidor la permite sin esperarla, es de mas", DE_MAS, del_servidor["state"])
    # Segunda refutacion: un cliente NO citado sobre una opcion local bloqueaba el PASS.
    t.igual("E-30 un cliente no citado sobre una opcion local no cambia nada", "PASS",
            _estado(evidencia=EVIDENCIA + [_ui("tema", "ALLOWED", ["tema-oscuro"], fuente="UI_TEST")]))


# -- Varios roles ----------------------------------------------------------------

def _varios_roles(permitidas, negadas=(), propio=None):
    """El operador (ver-tramite), el auditor (exportar y ver-reportes) y un mapping de los dos juntos.

    El servidor permite al conjunto `permitidas` y le niega `negadas`, y las dos son sus operaciones
    protegidas. `propio` es el mapeo propio del conjunto, o None si no tiene. Sin mapeo propio, un
    modulo que calculara la union, la interseccion o el perfil del rol "mas alto" veria consistente
    alguno de estos casos."""
    auditor, evid = _segundo(ops=("exportar", "ver-reportes"))
    juntos_ev = [_acceso("srv-juntos-si", "ALLOWED", permitidas, mapping="m-juntos"),
                 _acceso("srv-juntos-no", "DENIED", negadas, mapping="m-juntos")]
    juntos_ev = [x for x in juntos_ev if x.get("operations")]
    citas = [x["evidenceId"] for x in juntos_ev]
    if propio is not None:
        juntos_ev.append(_mapeo("perfil-juntos", propio, (), "m-juntos", eid="mapeo-juntos"))
        citas.append("mapeo-juntos")
    juntos = _map("m-juntos", [ROL, "auditor"], "perfil-juntos",
                  protegidas=sorted(set(permitidas) | set(negadas)), alcances=(), evidencia=citas)
    return _r(_reg([_sup(mappings=[_map(), auditor, juntos], varios="RESOLVED")]),
              _sin("fuente", "varios", _fuente(roles=[ROL, "auditor"]), _varios("RESOLVED"),
                   *(evid + juntos_ev)))


TRES = [VER, "exportar", "ver-reportes"]


def test_e31_no_se_suman(t):
    """E-31."""
    r = _varios_roles(TRES)
    t.igual("E-31 la union no se calcula", {"operations": [], "dataScopes": []},
            _m(r, "m-juntos")["expected"])
    t.igual("E-31 con el servidor dando la union, el conjunto queda sin resolver", MAPEO,
            _m(r, "m-juntos")["state"])
    t.verdadero("E-31 no pasa", r["state"] != "PASS")


def test_e32_no_se_intersecan(t):
    """E-32."""
    r = _varios_roles([], TRES)
    t.igual("E-32 la interseccion no se calcula", {"operations": [], "dataScopes": []},
            _m(r, "m-juntos")["expected"])
    t.igual("E-32 con el servidor negando todo (la interseccion vacia), queda sin resolver", MAPEO,
            _m(r, "m-juntos")["state"])


def test_e33_no_gana_el_mas_alto(t):
    """E-33."""
    for nombre, si, no in (("el del auditor", ["exportar", "ver-reportes"], [VER]),
                           ("el del operador", [VER], ["exportar", "ver-reportes"])):
        r = _varios_roles(si, no)
        t.igual("E-33 el perfil %s no se elige" % nombre, MAPEO, _m(r, "m-juntos")["state"])
    t.verdadero("E-33 el modulo no ordena roles: ningun literal dice highest, first ni max",
                not any(p in x.lower() for x in _literales() for p in ("highest", "first", "rank",
                                                                        "priority", "jerarquia")))


def test_e34_la_semantica_del_proyecto(t):
    """E-34."""
    r = _varios_roles(TRES, propio=TRES)
    t.igual("E-34 con la semantica y el mapeo propio, el conjunto cumple", "PASS",
            _m(r, "m-juntos")["state"])
    t.igual("E-34 y el caso pasa", "PASS", r["state"])
    t.igual("E-34 la semantica de varios roles queda sostenida", ["varios"],
            _s(r)["multiRoleSemantics"]["evidenceUsed"])
    menos = _varios_roles(TRES, propio=[VER])
    t.igual("E-34 y si el proyecto dice que el conjunto tiene menos, lo de mas falla", DE_MAS,
            _m(menos, "m-juntos")["state"])


def test_e35_semantica_desconocida(t):
    """E-35."""
    t.igual("E-35 sin declararla", VARIOS, _estado(_reg([_sup(varios=None)])))
    t.igual("E-35 declarada UNRESOLVED", VARIOS, _estado(_reg([_sup(varios="UNRESOLVED")])))
    t.igual("E-35 declarada RESOLVED sin evidencia", VARIOS,
            _estado(_reg([_sup(varios="RESOLVED")])))
    t.igual("E-35 con una evidencia debil", VARIOS,
            _estado(evidencia=_sin("varios", _varios(fuente="AGENT_STATEMENT"))))
    auditor, evid = _segundo()
    juntos = _map("m-juntos", [ROL, "auditor"], "perfil-juntos", protegidas=[VER], alcances=(),
                  evidencia=["mapeo-juntos", "srv-juntos"])
    r = _r(_reg([_sup(mappings=[_map(), auditor, juntos])]),
           _sin("fuente", _fuente(roles=[ROL, "auditor"]), *evid,
                _mapeo("perfil-juntos", [VER], (), "m-juntos", eid="mapeo-juntos"),
                _acceso("srv-juntos", "ALLOWED", [VER], mapping="m-juntos")))
    t.igual("E-35 dos roles con la semantica en NOT_APPLICABLE", VARIOS, _m(r, "m-juntos")["state"])


# -- Los cambios de rol ------------------------------------------------------------

def _revocado(valor, eid="revocado"):
    return _acceso(eid, valor, fuente="INTEGRATION_AUTHORIZATION_TEST") | {
        "establishes": ["ROLE_CHANGE_ACCESS"]}


def test_e36_no_se_inventa_la_propagacion(t):
    """E-36."""
    for declarada in (None, "UNRESOLVED", "RESOLVED"):
        ev = _sin("cambio", _revocado("REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH"))
        r = _r(_reg([_sup(cambio=declarada, evidencia=("fuente", "varios"),
                          mappings=[_map(evidencia=["mapeo", "srv", "srv-no", "revocado"])])]), ev)
        t.igual("E-36 sin semantica sostenida (%s), un rol revocado vigente no falla" % declarada,
                CAMBIO, r["state"])
        t.verdadero("E-36 (%s) y no es FAIL" % declarada, r["state"] not in FALLAS)
    t.verdadero("E-36 el modulo no compara tiempos: ningun literal de segundos ni minutos",
                not any(p in x.lower() for x in _literales() for p in ("seconds", "minutes", "ttl",
                                                                        "timedelta")))


def test_e37_la_ventana_documentada(t):
    """E-37."""
    for valor in ("REVOKED_ROLE_EFFECTIVE_WITHIN_REFRESH", "REVOKED_ROLE_NOT_EFFECTIVE"):
        r = _con(_revocado(valor))
        t.igual("E-37 %s cumple" % valor, "PASS", r["state"])
        t.igual("E-37 %s queda como evidencia usada" % valor, ["revocado"],
                _m(r)["evidenceUsed"]["roleChange"])
    t.igual("E-37 la semantica queda sostenida", ["cambio"],
            _s(_r())["roleChangeSemantics"]["evidenceUsed"])


def test_e38_semantica_de_cambio_desconocida(t):
    """E-38."""
    t.igual("E-38 sin declararla", CAMBIO, _estado(_reg([_sup(cambio=None)])))
    t.igual("E-38 declarada RESOLVED sin evidencia", CAMBIO, _estado(evidencia=_sin("cambio")))
    t.igual("E-38 con una evidencia debil", CAMBIO,
            _estado(evidencia=_sin("cambio", _cambio(fuente="README_STATEMENT"))))
    t.igual("E-38 con una evidencia que dice otra cosa", CAMBIO,
            _estado(evidencia=_sin("cambio", _cambio("NOT_APPLICABLE"))))


def test_e39_un_rol_revocado_mas_alla_de_la_ventana(t):
    """E-39."""
    r = _con(_revocado("REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH"))
    t.igual("E-39 con la semantica resuelta, falla", DE_MAS, r["state"])
    t.igual("E-39 y la evidencia queda usada", ["revocado"], _m(r)["evidenceUsed"]["roleChange"])
    no_citada = _r(evidencia=EVIDENCIA + [_revocado("REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH")])
    t.igual("E-39 sin citarla no falla, y no pasa", CAMBIO, no_citada["state"])
    cliente = _con(_revocado("REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH") | {"sourceType": "UI_TEST"})
    t.igual("E-39 dicha por el cliente no cuenta", "PASS", cliente["state"])
    no_cambian = _r(_reg([_sup(cambio="NOT_APPLICABLE",
                               mappings=[_map(evidencia=["mapeo", "srv", "srv-no", "revocado"])])]),
                    _sin("cambio", _cambio("NOT_APPLICABLE"),
                         _revocado("REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH")))
    t.igual("E-39 con la semantica en NOT_APPLICABLE es una contradiccion, no un FAIL", CAMBIO,
            no_cambian["state"])


# -- Los limites -----------------------------------------------------------------

def test_e40_c1_no_es_vu8(t):
    """E-40."""
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    con_c1 = seguridad.resultado("Vu8", _de_control_pasa("C1"), todas, MATRIZ)
    t.verdadero("E-40 los controles de C1 en PASS no cumplen Vu8", con_c1["result"] != "COMPLIANT")
    t.igual("E-40 y dejan a Vu8 igual que sin nada", seguridad.resultado("Vu8", {}, todas, MATRIZ)["result"],
            con_c1["result"])
    login = [_e("oidc", "AUTHENTICATION_SUCCESS", ["ROLE_ASSIGNMENT_SOURCE", "ROLE_PROFILE_MAPPING",
                                                    "ACCESS"], "ALLOWED", maps=[MAP],
                operations=[VER], dataScopes=[PROPIOS], roles=[ROL])]
    for nombre, base in (("sin fuente", _sin("fuente")), ("sin acceso", _sin("srv"))):
        # Solo se cita lo que esta: una cita a algo que no esta es ilegible y taparia el caso.
        hay = {x["evidenceId"] for x in base} | {"oidc"}
        caso = _caso(_reg([_sup(evidencia=[i for i in ("fuente", "varios", "cambio", "oidc") if i in hay],
                                mappings=[_map(evidencia=[i for i in ("mapeo", "srv", "srv-no", "oidc")
                                                          if i in hay])])]),
                     base + login)
        caso["c1Result"] = {"state": "PASS", "control": "oidc-keycloak-integration"}
        t.igual("E-40 %s: un login citado y un C1 en PASS no mueven Vu8" % nombre,
                _estado(evidencia=base), CHECK.evaluar(caso)["state"])
        t.verdadero("E-40 %s: y no pasa" % nombre, CHECK.evaluar(caso)["state"] != "PASS")


def test_e41_vu8_no_es_c1(t):
    """E-41."""
    ev, _ = CHECK.para_seguridad(_r())
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    for regla in ("C1", "Vu1", "Vu3", "Vu4"):
        sin = seguridad.resultado(regla, {}, todas, MATRIZ)
        con = seguridad.resultado(regla, ev, todas, MATRIZ)
        t.igual("E-41 %s no cambia con Vu8 en PASS" % regla, sin["result"], con["result"])
        t.verdadero("E-41 %s no cumple" % regla, con["result"] != "COMPLIANT")
    t.igual("E-41 y ningun control de Vu8 es de C1", [],
            sorted(set(ev["controlResults"]) & set(seguridad.regla("C1", MATRIZ)["checks"]
                                                    + seguridad.regla("C1", MATRIZ)["policies"])))


def test_e42_un_claim_no_prueba_vu8(t):
    """E-42."""
    for quitar, item in (("fuente", _fuente(fuente="TOKEN_CLAIM_PRESENCE")),
                         ("mapeo", _mapeo(fuente="TOKEN_CLAIM_PRESENCE")),
                         ("srv", _acceso("srv", "ALLOWED", [VER], [PROPIOS],
                                         fuente="TOKEN_CLAIM_PRESENCE"))):
        r = _r(evidencia=_sin(quitar, item))
        t.verdadero("E-42 un claim en lugar de `%s` no pasa" % quitar, r["state"] != "PASS")
        t.verdadero("E-42 ni falla" if quitar != "srv" else "E-42 ni falla (acceso)",
                    r["state"] not in FALLAS)


def test_e43_vu5_no_es_vu8(t):
    """E-43."""
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    con_vu5 = seguridad.resultado("Vu8", _de_control_pasa("Vu5"), todas, MATRIZ)
    t.verdadero("E-43 los controles de Vu5 en PASS no cumplen Vu8", con_vu5["result"] != "COMPLIANT")
    ev, _ = CHECK.para_seguridad(_r())
    t.igual("E-43 y Vu8 en PASS no mueve a Vu5", seguridad.resultado("Vu5", {}, todas, MATRIZ)["result"],
            seguridad.resultado("Vu5", ev, todas, MATRIZ)["result"])


def test_e44_validar_no_es_autorizar(t):
    """E-44."""
    validacion = _acceso("srv-no", "DENIED", [BORRAR], [TODOS], fuente="INPUT_VALIDATION")
    r = _r(evidencia=_sin("srv-no", validacion))
    t.igual("E-44 un rechazo por validacion no prueba que se niegue", MAPEO, r["state"])
    t.igual("E-44 y queda como insuficiente", ["srv-no"], _m(r)["insufficient"])
    t.igual("E-44 las dos filas protegidas quedan sin resolver", ["UNRESOLVED", "UNRESOLVED"],
            [_fila(_m(r), BORRAR)["result"], _fila(_m(r), TODOS)["result"]])


# -- La evidencia y la prueba ---------------------------------------------------------

def test_e45_evidencia_estatica(t):
    """E-45."""
    ev = _sin("srv", "srv-no",
              _acceso("srv", "ALLOWED", [VER], [PROPIOS], fuente="BACKEND_AUTHORIZATION_CONFIGURATION"),
              _acceso("srv-no", "DENIED", [BORRAR], [TODOS], fuente="BACKEND_AUTHORIZATION_CODE"))
    t.igual("E-45 configuracion y codigo del servidor alcanzan", "PASS", _estado(evidencia=ev))
    t.igual("E-45 con el mapeo en ROLE_PROFILE_CONFIGURATION tambien", "PASS",
            _estado(evidencia=_sin("mapeo", _mapeo(fuente="ROLE_PROFILE_CONFIGURATION"))))


def test_e46_tests_de_autorizacion(t):
    """E-46."""
    for f1, f2 in (("UNIT_AUTHORIZATION_TEST", "UNIT_AUTHORIZATION_TEST"),
                   ("INTEGRATION_AUTHORIZATION_TEST", "INTEGRATION_AUTHORIZATION_TEST"),
                   ("UNIT_AUTHORIZATION_TEST", "INTEGRATION_AUTHORIZATION_TEST")):
        ev = _sin("srv", "srv-no", _acceso("srv", "ALLOWED", [VER], [PROPIOS], fuente=f1),
                  _acceso("srv-no", "DENIED", [BORRAR], [TODOS], fuente=f2))
        t.igual("E-46 %s + %s" % (f1, f2), "PASS", _estado(evidencia=ev))


def test_e47_prueba_autorizada_en_qa(t):
    """E-47."""
    ev = _sin("srv", "srv-no", _prueba("srv", "ALLOWED", [VER], [PROPIOS]),
              _prueba("srv-no", "DENIED", [BORRAR], [TODOS]))
    r = _r(evidencia=ev)
    t.igual("E-47 una prueba autorizada con identidades sinteticas", "PASS", r["state"])
    t.igual("E-47 y no queda nada inseguro", [], _m(r)["unsafe"])
    for ambiente in ("DEV", "HML", "OTHER"):
        ev = _sin("srv", "srv-no", _prueba("srv", "ALLOWED", [VER], [PROPIOS], environment=ambiente),
                  _prueba("srv-no", "DENIED", [BORRAR], [TODOS], environment=ambiente))
        t.igual("E-47 tambien en %s" % ambiente, "PASS", _estado(evidencia=ev))


def test_e48_sin_cuenta_real(t):
    """E-48."""
    ev = _sin("srv", "srv-no",
              _acceso("srv", "ALLOWED", [VER], [PROPIOS], fuente="BACKEND_AUTHORIZATION_CONFIGURATION"),
              _acceso("srv-no", "DENIED", [BORRAR], [TODOS], fuente="UNIT_AUTHORIZATION_TEST"))
    r = _r(_reg([_sup(mappings=[_map(modo="STATIC", identidad=None)])]), ev)
    t.igual("E-48 PASS sin ninguna prueba en runtime", "PASS", r["state"])
    t.verdadero("E-48 y sin ninguna AUTHORIZED_QA_ROLE_TEST en el catalogo",
                not any(x["sourceType"] == "AUTHORIZED_QA_ROLE_TEST" for x in ev))
    t.igual("E-48 una prueba sin cuenta real es segura", [],
            CHECK.prueba_segura(dict(PRUEBA, sourceType="AUTHORIZED_QA_ROLE_TEST")))


def test_e49_ninguna_credencial_sale(t):
    """E-49."""
    contrasena = "postgres://tramites:" + "S3cr3t0!@db.qa.local/app"
    reg = _reg([_sup(mappings=[_map(identidad=TOKEN)])])
    reg["surfaces"][0]["roleAssignmentSource"]["sourceRef"] = contrasena
    ev = _sin("fuente", _fuente(contrasena, reference=TOKEN))
    r = _r(reg, ev)
    texto = _json(r)
    unidad = _json(_unidad(r))
    evento = _json(prod.desde_regla(_vu8_en_seguridad(r), "GCBA-8049", {"project": "P"},
                                    "2026-09-25T10:00:00"))
    for nombre, salida in (("la salida", texto), ("la unidad", unidad), ("el libro", evento)):
        t.no_contiene("E-49 %s no lleva el token" % nombre, TOKEN, salida)
        t.no_contiene("E-49 %s no lleva la contrasena" % nombre, "S3cr3t0", salida)
    t.contiene("E-49 la fuente sale redactada", "[redactado]", texto)
    # Primera refutacion: `testIdentityRef` es texto libre y la lib no reconoce toda credencial.
    proveedor = "glpat-" + "AbCdEfGhIjKlMnOpQrSt"
    for nombre, identidad in (("un token con prefijo", proveedor), ("una contrasena sin marca",
                                                                    "hunter2Secreto")):
        r2 = _r(_reg([_sup(mappings=[_map(identidad=identidad)])]))
        t.no_contiene("E-49 testIdentityRef con %s no sale en la salida" % nombre, identidad, _json(r2))
        t.no_contiene("E-49 ni en la unidad (%s)" % nombre, identidad, _json(_unidad(r2)))
        t.verdadero("E-49 y la salida no tiene el campo (%s)" % nombre,
                    all("testIdentityRef" not in m for m in _s(r2)["mappings"]))
        t.igual("E-49 sin cambiar el resultado (%s)" % nombre, "PASS", r2["state"])
    # 📌 El limite, clavado en verde: el dia que la lib reconozca `glpat-`, esto se pone en rojo y
    # hay que venir a angostarlo.
    fuera = _r(_reg([_sup(ref=proveedor)]), _sin("fuente", _fuente(proveedor)))
    t.contiene("E-49 (pendiente de la lib) un token con prefijo en sourceRef todavia sale", proveedor,
               _json(fuera))
    esquema = json.loads((SCHEMAS / "role-profile-consistency.schema.json").read_text(encoding="utf-8"))
    t.vacio("E-49 el registro vacio instalado valida",
            CHECK.validar_schema(json.loads((REGLAS / "role-profile-consistency.json").read_text(
                encoding="utf-8"))))
    for capa, parchar in (("la raiz", lambda d: d.update(password="x")),
                          ("la superficie", lambda d: d["surfaces"][0].update(token="x")),
                          ("la fuente", lambda d: d["surfaces"][0]["roleAssignmentSource"].update(
                              credential="x")),
                          ("el mapping", lambda d: d["surfaces"][0]["mappings"][0].update(
                              password="x"))):
        doc = _reg()
        parchar(doc)
        t.verdadero("E-49 una clave de mas en %s no valida" % capa, CHECK.validar_schema(doc))
    t.igual("E-49 el schema es el que se valida", "role-profile-consistency/1.0", esquema["$id"])
    con_campo = _sin("srv", dict(SRV, password="x"))
    r = _r(evidencia=con_campo)
    t.verdadero("E-49 un item con un campo de mas queda mal formado y no sostiene nada",
                r["state"] != "PASS" and any("mal formada" in i for i in r["issues"]))


def test_e50_una_prueba_insegura(t):
    """E-50."""
    for nombre, cambio, motivo in (
            ("en PRD", {"environment": "PRD"}, "PRODUCTION"),
            ("con una cuenta privilegiada real", {"realPrivilegedAccount": True},
             "REAL_PRIVILEGED_ACCOUNT"),
            ("destructiva", {"destructive": True}, "DESTRUCTIVE"),
            ("sin identidades sinteticas", {"syntheticIdentities": None}, "NOT_SYNTHETIC_IDENTITIES"),
            ("no autorizada", {"authorized": None}, "NOT_AUTHORIZED"),
            ("con credenciales registradas", {"rawCredentialsLogged": True}, "RAW_CREDENTIALS_LOGGED"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED")):
        r = _r(evidencia=_sin("srv-no", _prueba("srv-no", "DENIED", [BORRAR], [TODOS], **cambio)))
        t.igual("E-50 %s" % nombre, INSEGURA, r["state"])
        t.verdadero("E-50 %s dice por que" % nombre, motivo in _m(r)["unsafe"])
    sin_objetivo = _r(evidencia=_sin("srv-no", _prueba("srv-no", "DENIED", [BORRAR], [TODOS],
                                                        outcome="UNAVAILABLE")))
    t.igual("E-50 sin objetivo", SIN_OBJ, sin_objetivo["state"])
    raices = ({a.name.split(".")[0] for n in ast.walk(_arbol()) if isinstance(n, ast.Import)
               for a in n.names}
              | {(n.module or "").split(".")[0] for n in ast.walk(_arbol())
                 if isinstance(n, ast.ImportFrom)})
    t.igual("E-50 el modulo no ejecuta nada: no importa subprocess, socket ni urllib", set(),
            {"subprocess", "socket", "urllib", "requests", "http"} & raices)


def test_e51_insegura_no_es_pass_ni_fail(t):
    """E-51."""
    for citada in (True, False):
        insegura = _prueba("insegura", "ALLOWED", ["anular-tramite"], environment="PRD")
        r = _con(insegura) if citada else _r(evidencia=EVIDENCIA + [insegura])
        t.igual("E-51 una prueba insegura %s que dice que hay acceso de mas" %
                ("citada" if citada else "no citada"), INSEGURA, r["state"])
        t.verdadero("E-51 (%s) no es FAIL" % citada, r["state"] not in FALLAS)
    # Primera refutacion: una insegura no citada que niega lo esperado dejaba pasar el PASS.
    menos = _r(evidencia=EVIDENCIA + [_prueba("insegura", "DENIED", [VER], environment="PRD")])
    t.igual("E-51 una insegura no citada que dice que hay acceso de menos", INSEGURA, menos["state"])
    t.verdadero("E-51 y no es FAIL", menos["state"] not in FALLAS)
    # Segunda refutacion: una insegura no citada que dice que un rol revocado sigue vigente daba PASS.
    revocado = _prueba("revocada", "REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH", environment="PRD")
    revocado["establishes"] = ["ROLE_CHANGE_ACCESS"]
    t.igual("E-51 una insegura no citada que dice que un rol revocado sigue vigente", INSEGURA,
            _estado(evidencia=EVIDENCIA + [revocado]))
    no_dice = _r(evidencia=EVIDENCIA + [_prueba("ajena", "DENIED", [BORRAR], environment="PRD")])
    t.igual("E-51 una no citada que no dice nada de mas no bloquea", "PASS", no_dice["state"])
    falla = _con(_acceso("mas", "ALLOWED", ["anular-tramite"]),
                 _prueba("insegura", "DENIED", [BORRAR], environment="PRD"))
    t.igual("E-51 y una insegura no tapa un FAIL", DE_MAS, falla["state"])


def test_e51b_lo_citado_que_no_se_puede_leer(t):
    """E-51b - de la primera refutacion: un `outcome` fuera de lo legible es ilegible."""
    for outcome in ("UNAVAILABLE", "INCONCLUSIVE", "REFUTED"):
        mas = _con(_acceso("raro", "ALLOWED", ["anular-tramite"], fuente="API_AUTHORIZATION_TEST",
                           outcome=outcome))
        t.igual("E-51b %s citada que dice de mas no pasa" % outcome, MAPEO, mas["state"])
        t.verdadero("E-51b %s y no falla" % outcome, mas["state"] not in FALLAS)
        bien = _con(_acceso("raro", "DENIED", [BORRAR], fuente="API_AUTHORIZATION_TEST", outcome=outcome))
        t.igual("E-51b %s citada que dice lo esperado tampoco pasa" % outcome, MAPEO, bien["state"])
        fuente = _r(evidencia=_sin("fuente", _fuente(outcome=outcome)))
        t.verdadero("E-51b %s en la fuente citada no pasa" % outcome, fuente["state"] != "PASS")
        suelta = _r(evidencia=EVIDENCIA + [_acceso("raro", "ALLOWED", ["anular-tramite"],
                                                   fuente="API_AUTHORIZATION_TEST", outcome=outcome)])
        t.igual("E-51b %s no citada que dice de mas tampoco pasa" % outcome, MAPEO, suelta["state"])
    # Segunda refutacion: una prueba segura con `outcome` ilegible, citada, daba PASS.
    for outcome in ("INCONCLUSIVE", "REFUTED"):
        for nombre, prueba in (("de mas", _prueba("q", "ALLOWED", ["anular-tramite"], outcome=outcome)),
                               ("lo esperado", _prueba("q", "DENIED", [BORRAR], outcome=outcome))):
            r = _con(prueba)
            t.igual("E-51b una prueba segura %s citada que dice %s no pasa" % (outcome, nombre), MAPEO,
                    r["state"])
        revocado = _acceso("rev", "REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH",
                           fuente="INTEGRATION_AUTHORIZATION_TEST", outcome=outcome)
        revocado["establishes"] = ["ROLE_CHANGE_ACCESS"]
        t.igual("E-51b un rol revocado vigente, %s y no citado, no pasa" % outcome, MAPEO,
                _estado(evidencia=EVIDENCIA + [revocado]))
    t.igual("E-51b CONFIRMED y OBSERVED si se leen", [DE_MAS, DE_MAS],
            [_con(_acceso("raro", "ALLOWED", ["anular-tramite"], fuente="API_AUTHORIZATION_TEST",
                          outcome=o))["state"] for o in ("CONFIRMED", "OBSERVED")])


# -- El agregado ------------------------------------------------------------------------

def test_e52_un_mapping_sin_resolver(t):
    """E-52."""
    m, evid = _segundo()
    evid = [x for x in evid if not x["evidenceId"].startswith("srv-")]
    r = _r(_reg([_sup(mappings=[_map(), dict(m, evidence=["mapeo-m-auditor"])])]),
           _sin("fuente", _fuente(roles=[ROL, "auditor"]), *evid))
    t.igual("E-52 no pasa", MAPEO, r["state"])
    t.igual("E-52 aunque el operador cumpla", "PASS", _m(r)["state"])
    t.igual("E-52 en seguridad no cumple", "UNRESOLVED", _vu8_en_seguridad(r)["result"])
    t.igual("E-52 un mapping declarado NOT_VERIFIED tampoco", MAPEO,
            _estado(_reg([_sup(mappings=[_map(modo="NOT_VERIFIED")])])))
    t.igual("E-52 ni uno declarado UNRESOLVED", MAPEO,
            _estado(_reg([_sup(mappings=[_map(resultado="UNRESOLVED")])])))


def test_e53_una_superficie_sin_fuente(t):
    """E-53."""
    otra = _sup("backoffice", mappings=[_map()], evidencia=("varios", "cambio"))
    ev = [dict(x, surfaces=[SUP, "backoffice"]) if x.get("surfaces") else x for x in EVIDENCIA]
    r = _r(_reg([_sup(), otra]), ev)
    t.igual("E-53 no pasa", FUENTE, r["state"])
    t.igual("E-53 aunque la api cumpla", "PASS", _s(r)["state"])
    t.igual("E-53 el backoffice no tiene fuente", FUENTE, _s(r, "backoffice")["state"])
    nombrada = _r(evidencia=_sin("roles", _roles(sups=[SUP, "portal"])))
    t.igual("E-53 una superficie que la senal nombra sin entrada", FUENTE, nombrada["state"])
    t.igual("E-53 y queda nombrada", ["portal"], nombrada["coverage"]["missingSurfaces"])


def test_e54_el_mismo_resultado(t):
    """E-54."""
    m, evid = _segundo(resultado_srv="DENIED")
    otra = _sup("backoffice", mappings=[_map()], evidencia=("varios", "cambio"))
    registro = _reg([_sup(mappings=[_map(), m]), otra])
    evid_todo = [dict(x, surfaces=[SUP, "backoffice"]) if x.get("surfaces") else x
                 for x in _sin("fuente", _fuente(roles=[ROL, "auditor"]), *evid)] + [SRV, SRV]
    base = _json(_r(registro, evid_todo))
    azar = random.Random(54)
    for vuelta in range(6):
        reg, ev = copy.deepcopy(registro), copy.deepcopy(evid_todo)
        azar.shuffle(reg["surfaces"])
        azar.shuffle(ev)
        for s in reg["surfaces"]:
            azar.shuffle(s["mappings"])
            azar.shuffle(s["evidence"])
            for x in s["mappings"]:
                azar.shuffle(x["evidence"])
                azar.shuffle(x["protectedOperationRefs"])
        t.igual("E-54 desordenado %d" % vuelta, base, _json(_r(reg, ev)))
    t.igual("E-54 los trece estados", sorted(LOS_13), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "gestión") for f in ("NFC", "NFD"))
    t.igual("E-54 un rol en NFD en el mapping es el de la fuente en NFC", "PASS",
            _estado(_reg([_sup(mappings=[_map(roles=[nfd])])]), _sin("fuente", _fuente(roles=[nfc]))))
    t.igual("E-54 citar en NFD una evidencia en NFC es citarla", "PASS",
            _estado(_reg([_sup(mappings=[_map(evidencia=["mapeo", nfd, "srv-no"])])]),
                    _sin("srv", dict(SRV, evidenceId=nfc))))
    gemelas = _r(evidencia=EVIDENCIA + [dict(SRV, evidenceId=nfc), dict(SRV, evidenceId=nfd)])
    t.verdadero("E-54 dos ids iguales en NFC son un id repetido",
                any(nfc in i for i in gemelas["issues"]))
    t.igual("E-54 dos mappings iguales en NFC son el mismo, repetido", [nfc],
            _s(_r(_reg([_sup(mappings=[_map(nfc), _map(nfd)])])))["coverage"]["duplicatedMappings"])
    t.igual("E-54 una operacion en NFD es la esperada en NFC", "PASS",
            _estado(_reg([_sup(mappings=[_map(protegidas=[BORRAR, nfd])])]),
                    _sin("mapeo", "srv", _mapeo(ops=[nfc]), _acceso("srv", "ALLOWED", [nfd], [PROPIOS]))))
    for nombre, raro in (("una lista", ["x"]), ("un numero", 7), ("un dict", {"a": 1})):
        ev = EVIDENCIA + [{"evidenceId": raro, "sourceType": "UI_TEST", "reference": "x",
                           "establishes": ["ACCESS"], "mappings": [MAP], "value": "ALLOWED"}]
        t.igual("E-54 un id que es %s no levanta" % nombre, MAPEO,
                _sin_excepcion(lambda: _estado(evidencia=ev)))


def test_e55_la_trazabilidad(t):
    """E-55."""
    caminos = {"vacio": CHECK.evaluar({}), "pasa": _r(), "falla": _con(_acceso("mas", "ALLOWED",
                                                                               ["anular-tramite"])),
               "insegura": _r(evidencia=_sin("srv-no", _prueba("srv-no", "DENIED", [BORRAR], [TODOS],
                                                               environment="PRD"))),
               "no aplica": CHECK.evaluar({"evidence": [_roles("ABSENT", "SECURITY_DOCUMENTATION")]}),
               "registro invalido": CHECK.evaluar({"registry": {"surfaces": 1}})}
    for nombre, r in caminos.items():
        t.igual("E-55 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-55 %s la clave" % nombre, "ES0902.Vu8", r["ruleKey"])
        t.igual("E-55 %s el control" % nombre, "role-profile-consistency", r["control"])
    vu8 = _unidad(_r())
    t.igual("E-55 la unidad lleva Vu8 en PASS", "PASS", vu8["result"])
    t.igual("E-55 aplicable", "APPLICABLE", vu8["applicability"])
    t.igual("E-55 con sus superficies", [SUP], vu8["surfaces"])
    t.igual("E-55 y su evidencia por id", ["cambio", "fuente", "mapeo", "srv", "srv-no", "varios"],
            vu8["evidence"])
    t.igual("E-55 y nada mas", ["applicability", "evidence", "result", "source", "surfaces"],
            sorted(vu8))
    t.igual("E-55 con la fuente", TRAZA, vu8["source"])
    t.igual("E-55 sin la senal, la unidad dice sin resolver", "UNRESOLVED", _unidad(_r(), None)["result"])
    t.igual("E-55 con la senal en FALSE, no aplica", "NOT_APPLICABLE", _unidad(_r(), False)["result"])
    t.igual("E-55 un resultado ajeno no se proyecta", "UNRESOLVED",
            _unidad(dict(_r(), control="otro-control"))["result"])
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = _unidad(_r())
    finally:
        normativa._ruta_de_evidencia = original
    t.igual("E-55 sin la lib la unidad se arma, con el estado y sin ids", ("PASS", [], []),
            (sin_lib["result"], sin_lib["surfaces"], sin_lib["evidence"]))


def test_e56_entra_al_libro_de_siempre(t):
    """E-56."""
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu8_56_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-8056")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _con(_acceso("mas", "ALLOWED", ["anular-tramite"])), "NON_COMPLIANT"),
                     ("sin resolver", _r(evidencia=_sin("mapeo")), "UNRESOLVED"),
                     ("vacio", CHECK.evaluar({}), "UNRESOLVED"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu8_en_seguridad(r)
            t.igual("E-56 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-8056", alcance, "2026-09-25T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-56 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-56 de ES0902.Vu8", [("ES0902", "Vu8", "ES0902.Vu8")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-56 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "UNRESOLVED"], [e["result"] for e in eventos])
        t.igual("E-56 producido por desde_regla", ["desde_regla"] * 4,
                [e["details"]["producer"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    dominios = json.loads((REGLAS / "security-report-domains.json").read_text(encoding="utf-8"))["domains"]
    t.igual("E-56 Vu8 esta en authorization-roles, y en ningun otro dominio", ["authorization-roles"],
            [d["domainId"] for d in dominios if "Vu8" in d["rules"]])
    t.igual("E-56 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))


def test_e57_ningun_libro_nuevo(t):
    """E-57."""
    paquete = BIN / "reporte_seguridad"
    t.igual("E-57 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in paquete.iterdir() if p.is_file()))
    importados = set()
    for n in ast.walk(_arbol()):
        if isinstance(n, ast.Import):
            importados.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            importados.update("%s.%s" % (n.module, a.name) for a in n.names)
    t.igual("E-57 el modulo importa esto y nada mas",
            sorted({"evidencia", "io", "json", "orquestacion.roster", "orquestacion.senales",
                    "orquestacion.tools", "os", "rutas", "sys"}), sorted(importados))
    escrituras = [n for n in ast.walk(_arbol()) if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", getattr(n.func, "id", "")) == "open"
                  and any(isinstance(a, ast.Constant) and "w" in str(a.value) for a in n.args[1:])]
    t.igual("E-57 y no abre nada para escribir", [], escrituras)


# -- La refutacion atomica ------------------------------------------------------------

CLAVE_REF = "GCBA-8058"
_PLANTILLA = {}


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def _plantilla():
    if "base" not in _PLANTILLA:
        base = Path(tempfile.gettempdir()) / ("harness-vu8-base-" + uuid.uuid4().hex[:8])
        _escribir(base / "src" / "roles.py", "PERMISOS = {'operador': ['ver-tramite']}\n")
        _escribir(base / "src" / "api.py", "def borrar(): requiere('admin')\n")
        _escribir(base / "otro" / "nada.py", "x = 1\n")
        for args in (("init", "-q"), ("add", "-A"), ("commit", "-q", "-m", "i")):
            subprocess.run(["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t"]
                           + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        tc = {"meta": {"task_key": CLAVE_REF, "context_hash": "h"}, "task": {"title": "t"}}
        prop = {"objective": "o", "domains": ["backend"],
                "workUnits": [{"id": wu, "objective": "x", "domain": "backend"} for wu in ("WU-1", "WU-2")]}
        _PLANTILLA["plan"] = json.dumps(orq_plan.armar(prop, tc, {}, {}))
        _PLANTILLA["base"] = base
    return _PLANTILLA["base"]


def _bloque(reglas, checks=("role-profile-consistency",)):
    return {"standard": {"id": "ES0902", "version": "6.2"}, "applicableRules": list(reglas),
            "notApplicableRules": [], "unresolvedRules": [], "declaredPolicies": [],
            "declaredChecks": list(checks), "declaredReviews": []}


def _proyecto(unidades, scope):
    proy = Path(tempfile.gettempdir()) / ("harness-vu8-" + uuid.uuid4().hex[:8])
    shutil.copytree(str(_plantilla()), str(proy))
    doc = json.loads(_PLANTILLA["plan"])
    doc["workUnits"] = [u for u in doc["workUnits"] if u["id"] in unidades]
    for u in doc["workUnits"]:
        u["normative"] = dict(u["normative"], standards={"ES0902": unidades[u["id"]]})
    _escribir(proy / ".claude" / "planes" / (CLAVE_REF + ".json"), json.dumps(doc, ensure_ascii=False))
    _escribir(proy / ".claude" / "refutaciones" / CLAVE_REF / "scope.json",
              json.dumps({"schema_version": R.VERSION_ALCANCE, "workUnits": scope}))
    return proy


def _alcance(*paths, sid="roles"):
    return [{"scopeId": sid, "source": "workUnitFiles", "paths": list(paths)}]


def _unidades(proy):
    return R.leer(str(proy), CLAVE_REF)[1]


def _con_resultado(r):
    """El proyecto de una unidad de Vu8, con la salida del check en checks.json."""
    proy = _proyecto({"WU-1": _bloque(["Vu8"])}, {"WU-1": _alcance("src/roles.py")})
    R.compilar(str(proy), CLAVE_REF)
    u = _unidades(proy)[0]
    entrada = CHECK.para_refutacion(r, u)
    _escribir(proy / ".claude" / "refutaciones" / CLAVE_REF / "checks.json",
              json.dumps({"schema_version": R.VERSION_CHECKS, "results": [entrada]}))
    doc = R.compilar(str(proy), CLAVE_REF)
    return proy, doc, _unidades(proy)[0], entrada


def test_e58_una_unidad_por_regla_y_alcance(t):
    """E-58."""
    proy = _proyecto({"WU-1": _bloque(["Vu8", "Vu5"]), "WU-2": _bloque(["Vu8"])},
                     {"WU-1": _alcance("src/roles.py"), "WU-2": _alcance("src/api.py", sid="api")})
    try:
        R.compilar(str(proy), CLAVE_REF)
        de_vu8 = [u for u in _unidades(proy) if u["standard"]["ruleKey"] == "ES0902.Vu8"]
        t.igual("E-58 una unidad de Vu8 por unidad de trabajo", ["WU-1", "WU-2"],
                sorted(u["workUnitId"] for u in de_vu8))
        t.igual("E-58 con el alcance de cada una", [["src/roles.py"], ["src/api.py"]],
                [u["evidenceScope"]["paths"] for u in sorted(de_vu8, key=lambda u: u["workUnitId"])])
        t.igual("E-58 y Vu5 queda en su propia unidad", 1,
                len([u for u in _unidades(proy) if u["standard"]["ruleKey"] == "ES0902.Vu5"]))
        skills = {s["id"] for a in c_reg.cargar()["agents"] if a["id"] in ("dev-security", "dev-backend")
                  for s in a["skills"]}
        for u in de_vu8:
            t.verdadero("E-58 %s: la skill es de dev-security o dev-backend" % u["workUnitId"],
                        u["skillId"] in skills)
            t.igual("E-58 %s: la unidad valida" % u["workUnitId"], [], R.validar(u, R.SCHEMA_UNIDAD))
            t.verdadero("E-58 %s: declara el check" % u["workUnitId"],
                        "role-profile-consistency" in u["declaredChecks"])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e59_un_check_concluyente_no_llama_al_refutador(t):
    """E-59."""
    for nombre, r, estado, veredicto in (
            ("PASS", _r(), "RESOLVED", "cumple"),
            ("OVER", _con(_acceso("mas", "ALLOWED", ["anular-tramite"])), "RESOLVED", "incumple"),
            ("DIRECT_ACCESS", _con(_acceso("srv-no", "DENIED", alcances=[TODOS],
                                           fuente="API_AUTHORIZATION_TEST"),
                                   _ui("boton", "DENIED", [BORRAR]),
                                   _acceso("directo", "ALLOWED", [BORRAR], fuente="API_AUTHORIZATION_TEST"),
                                   quitar=("srv-no",),
                                   mapping_ev=["mapeo", "srv", "srv-no", "boton", "directo"]),
             "RESOLVED", "incumple"),
            ("sin mapeo", _r(evidencia=_sin("mapeo")), "PENDING_SEMANTIC", None),
            ("insegura", _r(evidencia=_sin("srv-no", _prueba("srv-no", "DENIED", [BORRAR], [TODOS],
                                                             environment="PRD"))),
             "PENDING_SEMANTIC", None)):
        proy, doc, u, entrada = _con_resultado(r)
        try:
            t.igual("E-59 %s: la entrada valida" % nombre, [],
                    R.validar({"schema_version": R.VERSION_CHECKS, "results": [entrada]},
                              R.SCHEMA_UNIDAD, "checksInput"))
            t.igual("E-59 %s: estado de la unidad" % nombre, estado, u["status"])
            t.igual("E-59 %s: veredicto" % nombre, veredicto, doc["units"][0]["verdict"])
            if veredicto:
                t.igual("E-59 %s: por check" % nombre, "DETERMINISTIC_CHECK", u["resolutionPath"])
                t.verdadero("E-59 %s: y el refutador no la recibe" % nombre,
                            _levanta(lambda: R.para_refutar(str(proy), CLAVE_REF, u["refutationUnitId"])))
            else:
                t.igual("E-59 %s: queda una sola pendiente" % nombre, 1, doc["counts"]["pending"])
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)
    t.igual("E-59 una unidad de otra regla no se traduce", None,
            CHECK.para_refutacion(_r(), {"standard": {"ruleKey": "ES0902.Vu5"}, "evidenceFingerprint": "h"}))
    t.igual("E-59 un resultado ajeno tampoco", None,
            CHECK.para_refutacion(dict(_r(), control="otro"), {"standard": {"ruleKey": "ES0902.Vu8"},
                                                               "evidenceFingerprint": "h"}))


def _levanta(funcion, codigo=None):
    try:
        funcion()
    except R.RefutacionInvalida as e:
        return codigo is None or e.codigo == codigo
    return False


def test_e60_la_refutacion_no_sale_del_alcance(t):
    """E-60."""
    proy, doc, u, _ = _con_resultado(_r(evidencia=_sin("mapeo")))
    try:
        entregada = R.para_refutar(str(proy), CLAVE_REF, u["refutationUnitId"])
        entregada = entregada[0] if isinstance(entregada, list) else entregada
        t.igual("E-60 la unidad lleva solo el alcance declarado", ["src/roles.py"],
                entregada["evidenceScope"]["paths"])
        t.igual("E-60 y una sola regla", "ES0902.Vu8", entregada["standard"]["ruleKey"])

        def veredicto(**cambios):
            v = {"schema_version": R.VERSION_VEREDICTO, "refutationUnitId": u["refutationUnitId"],
                 "workUnitId": u["workUnitId"], "ruleKey": "ES0902.Vu8", "verdict": "cumple",
                 "reason": None, "citation": {"skillId": u["skillId"], "locator": "ES0902 §6, pág. 7"},
                 "evidence": [{"path": "src/roles.py", "line": 1,
                               "observed": "PERMISOS = {'operador': ['ver-tramite']}"}],
                 "needed": None, "cacheKey": u["cacheKey"],
                 "evidenceFingerprint": u["evidenceFingerprint"], "repoRevision": u["repoRevision"]}
            v.update(cambios)
            return json.dumps(v)
        t.verdadero("E-60 un veredicto de otra regla se rechaza",
                    _levanta(lambda: R.registrar(str(proy), CLAVE_REF, veredicto(ruleKey="ES0902.C1")),
                             "REFUTATION_OUTPUT_INVALID"))
        t.verdadero("E-60 uno con evidencia fuera del alcance tambien",
                    _levanta(lambda: R.registrar(str(proy), CLAVE_REF, veredicto(
                        evidence=[{"path": "src/api.py", "line": 1,
                                   "observed": "def borrar(): requiere('admin')"}])),
                             "REFUTATION_OUTPUT_INVALID"))
        t.verdadero("E-60 y el que se queda en el alcance se acepta",
                    not _levanta(lambda: R.registrar(str(proy), CLAVE_REF, veredicto())))
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e61_no_es_la_aprobacion_oficial(t):
    """E-61."""
    ev, _ = CHECK.para_seguridad(_r())
    ids = ev["controlResults"][CHECK.CONTROL]["evidence"]
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK", "evidence": ids})
    t.igual("E-61 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    for regla in ("C2", "O2"):
        t.igual("E-61 %s no cambia con Vu8 en PASS" % regla,
                seguridad.resultado(regla, {}, todas, MATRIZ)["result"],
                seguridad.resultado(regla, ev, todas, MATRIZ)["result"])
