# ES0902 §6 Vu9: lo publico sin autenticacion tiene control de uso.
#
# Escenarios E-01 a E-62 de docs/cambios/es0902-vu9-control-de-uso-publico/spec.md. Cada E-nn es el
# VU9-nn del paquete con el mismo numero.
#
# 🔴 CASO es una busqueda publica de una API, en QA, sin autenticacion. El inventario de rutas dice que
# es la unica superficie publica. Una cuota del gateway la controla: la configuracion del gateway dice
# que existe y que mitiga el consumo excesivo y el automatizado, la topologia dice que la ruta publica
# pasa por el gateway, y la configuracion de capacidad sostiene la estabilidad. Casi todo este archivo
# sale de romperlo. E-13 a E-16 lo miran en PASS desde cada capa.
import ast
import copy
import importlib.util
import json
import random
import re
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

RUTA_CHECK = CONTROLES / "checks" / "public-interface-abuse-protection.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu9_control_de_uso_publico")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu9"}
LOS_13 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED", "PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED",
          "ABUSE_CONTROL_MISSING", "ABUSE_CONTROL_BYPASS_PRESENT",
          "EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED", "AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED",
          "SERVICE_STABILITY_EVIDENCE_UNRESOLVED", "PUBLIC_ABUSE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
NA = "NOT_APPLICABLE"
SIN_APLIC = "APPLICABILITY_UNRESOLVED"
SUPERFICIE = "PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED"
COBERTURA = "PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED"
FALTA = "ABUSE_CONTROL_MISSING"
SALTEO = "ABUSE_CONTROL_BYPASS_PRESENT"
EXCESIVO = "EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED"
AUTOMATIZADO = "AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED"
ESTABILIDAD = "SERVICE_STABILITY_EVIDENCE_UNRESOLVED"
INSEGURA = "PUBLIC_ABUSE_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"
FALLAS = ("FAIL", FALTA, SALTEO)
# Un JWT: `controles/lib/evidencia.py` no reconoce un token con prefijo de proveedor (`glpat-`), y eso
# esta anotado en PENDIENTES-FH.md. E-57 prueba la regla de salida que hay, no la que falta.
TOKEN = "eyJhbGciOiJSUzI1NiJ9" + ".eyJyZWFsbV9hY2Nlc3MiOnt9fQ.firma"

SUP = "busqueda-publica"
CTL = "gw-cuota"
OTRA = "formulario-publico"


def _e(eid, fuente, establece, valor=None, sups=None, ctls=None, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if sups is not None:
        base["surfaces"] = list(sups)
    if ctls is not None:
        base["controls"] = list(ctls)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _publica(sups=(SUP,), fuente="API_SPECIFICATION", valor="PRESENT", eid="publica", **k):
    return _e(eid, fuente, "PUBLIC_UNAUTHENTICATED_FUNCTIONALITY", valor, sups, **k)


def _inventario(sups=(SUP,), valor="COMPLETE", fuente="ROUTE_INVENTORY", eid="inventario", **k):
    return _e(eid, fuente, "PUBLIC_SURFACE_INVENTORY", valor, sups, **k)


def _existe(cid=CTL, fuente="GATEWAY_CONFIGURATION", valor="PRESENT", eid="cuota", sups=None, **k):
    return _e(eid, fuente, "USE_CONTROL", valor, sups, [cid], **k)


def _ruta(cid=CTL, sups=(SUP,), valor="BOUND", fuente="NETWORK_TOPOLOGY", eid="ruta", **k):
    return _e(eid, fuente, "PATH_BINDING", valor, sups, [cid], **k)


def _dim(que, eid, cid=CTL, valor="EVIDENCED", fuente="GATEWAY_CONFIGURATION", **k):
    return _e(eid, fuente, que, valor, None, [cid], **k)


def _excesivo(**k):
    return _dim("EXCESSIVE_CONSUMPTION_MITIGATION", k.pop("eid", "excesivo"), **k)


def _automatizado(**k):
    return _dim("AUTOMATED_CONSUMPTION_MITIGATION", k.pop("eid", "automatizado"), **k)


def _estabilidad(**k):
    k.setdefault("fuente", "CAPACITY_CONFIGURATION")
    return _dim("SERVICE_STABILITY", k.pop("eid", "capacidad"), **k)


PUBLICA = _publica()
INVENTARIO = _inventario()
EXISTE = _existe()
RUTA = _ruta()
EXCESIVO_EV = _excesivo()
AUTOMATIZADO_EV = _automatizado()
ESTABILIDAD_EV = _estabilidad()
EVIDENCIA = [PUBLICA, INVENTARIO, EXISTE, RUTA, EXCESIVO_EV, AUTOMATIZADO_EV, ESTABILIDAD_EV]
CITAS_CTL = ("cuota", "ruta", "excesivo", "automatizado", "capacidad")


def _ctl(cid=CTL, capa="API_GATEWAY", camino="BOUND", exc="EVIDENCED", aut="EVIDENCED",
         est="EVIDENCED", tipo="cuota por cliente", evidencia=CITAS_CTL):
    return {"controlId": cid, "controlType": tipo, "enforcementLayer": capa, "pathBinding": camino,
            "excessiveConsumptionMitigation": exc, "automatedConsumptionMitigation": aut,
            "stabilityEvidence": est, "evidence": list(evidencia)}


def _sup(sid=SUP, controles=None, publica="YES", autenticada="NO", resultado="PROTECTED",
         modo="STATIC_CONFIGURATION", evidencia=("publica", "inventario"), tipo="API",
         operacion="GET /buscar"):
    return {"surfaceId": sid, "interfaceType": tipo, "operationRef": operacion,
            "publiclyReachable": publica, "authenticationRequired": autenticada,
            "controls": [_ctl()] if controles is None else list(controles),
            "verificationMode": modo, "result": resultado, "evidence": list(evidencia)}


def _reg(superficies=None, ambiente="QA"):
    return {"version": "1.0", "environment": ambiente,
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


def _c(r, cid=CTL, sid=SUP):
    return [c for c in _s(r, sid)["controls"] if c["controlId"] == cid][0]


def _sin(*ids_y_mas):
    """La evidencia base sin los ids que se nombran, mas los items que se pasan."""
    ids = [x for x in ids_y_mas if isinstance(x, str)]
    mas = [x for x in ids_y_mas if isinstance(x, dict)]
    return [x for x in EVIDENCIA if x["evidenceId"] not in ids] + mas


def _con(*items, quitar=(), citas=None, **ctl):
    """El caso con `items` agregados y citados desde el control."""
    citas = list(citas) if citas is not None else (
        [i for i in CITAS_CTL if i not in quitar] + [x["evidenceId"] for x in items])
    return _r(_reg([_sup(controles=[_ctl(evidencia=citas, **ctl)])]), _sin(*quitar, *items))


def _dos(segunda=None, evidencia_extra=(), inventario=(SUP, OTRA)):
    """El caso con una segunda superficie, protegida por su propio control si no se dice otra cosa."""
    otra = segunda if segunda is not None else _sup(OTRA, controles=[_ctl(
        "app-limite", "APPLICATION", evidencia=("existe-app", "ruta-app", "dims-app", "capacidad-app"))],
        evidencia=("publica-otra",), tipo="WEB", operacion="POST /formulario")
    extra = [_publica([OTRA], "ROUTE_INVENTORY", eid="publica-otra"),
             _existe("app-limite", "APPLICATION_CODE", eid="existe-app"),
             _ruta("app-limite", [OTRA], fuente="APPLICATION_CONFIGURATION", eid="ruta-app"),
             _e("dims-app", "APPLICATION_CODE", ["EXCESSIVE_CONSUMPTION_MITIGATION",
                                                 "AUTOMATED_CONSUMPTION_MITIGATION"], "EVIDENCED", None,
                ["app-limite"]),
             _estabilidad(cid="app-limite", eid="capacidad-app")]
    return _r(_reg([_sup(), otra]), _sin("inventario", _inventario(list(inventario)), *extra,
                                         *evidencia_extra))


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


def _vu9_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu9", ev, sen, MATRIZ)


def _unidad(r, senal=True):
    senales = {"unauthenticatedPublicInterfacePresent": senal} if senal is not None else {}
    return normativa.resolucion(senales, evidencia={"ES0902.Vu9": r})["standards"]["ES0902"]["rules"]["Vu9"]


def _de_control_pasa(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": ["ev-%s" % regla]}
                               for c in fila["policies"] + fila["checks"] + fila["reviews"]}}


def _todas_las_senales():
    return {s: True for s in seguridad.senales_declaradas(MATRIZ)}


PRUEBA = dict(environment="QA", authorized=True, bounded=True, stopConditions=True, syntheticData=True)


def _prueba(eid, que, valor, ctls=(CTL,), sups=None, **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _e(eid, "AUTHORIZED_QA_BOUNDED_TEST", que, valor, sups, list(ctls), **datos)


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01."""
    t.igual("E-01 la fila", "ES0902.Vu9", seguridad.regla("Vu9", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu9", CHECK.CLAVE)
    caminos = (("pasa", _r()), ("vacio", CHECK.evaluar({})),
               ("falla", _r(_reg([_sup(controles=[])]))),
               ("no aplica", CHECK.evaluar({"registry": {"version": "1.0", "environment": None,
                                                         "surfaces": []},
                                            "evidence": [_publica(valor="ABSENT",
                                                                  fuente="SECURITY_DOCUMENTATION")]})),
               ("registro invalido", CHECK.evaluar({"registry": {"surfaces": 1}})))
    for nombre, r in caminos:
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu9", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu9", _vu9_en_seguridad(r)["ruleKey"])
        t.igual("E-01 y en el libro (%s)" % nombre, "ES0902.Vu9",
                prod.desde_regla(_vu9_en_seguridad(r), "GCBA-9001", {"project": "P"},
                                 "2026-09-26T10:00:00")[0]["details"]["ruleKey"])
    t.igual("E-01 y en la refutacion", "ES0902.Vu9",
            CHECK.para_refutacion(_r(), {"standard": {"ruleKey": "ES0902.Vu9"}, "workUnitId": "WU-1",
                                         "evidenceFingerprint": "h", "repoRevision": "r"})["ruleKey"])


def test_e02_los_ids(t):
    """E-02."""
    vu9 = seguridad.regla("Vu9", MATRIZ)
    t.igual("E-02 CONDITIONAL", "CONDITIONAL", vu9["applicability"]["mode"])
    t.igual("E-02 la senal", ["unauthenticatedPublicInterfacePresent"], vu9["applicability"]["signals"])
    t.igual("E-02 la policy", ["public-interface-abuse-control-required"], vu9["policies"])
    t.igual("E-02 el check", ["public-interface-abuse-protection"], vu9["checks"])
    t.igual("E-02 cero reviews", [], vu9["reviews"])
    t.igual("E-02 los agentes, en el orden de la matriz", ["dev-security", "dev-backend", "dev-devops"],
            vu9["primaryAgents"])
    ids = {a["id"] for a in c_reg.cargar()["agents"]}
    for agente in vu9["primaryAgents"]:
        t.verdadero("E-02 %s esta en el registro de agentes" % agente, agente in ids)
    t.igual("E-02 el modulo", ("public-interface-abuse-protection", "public-interface-abuse-control-required",
                               "unauthenticatedPublicInterfacePresent"),
            (CHECK.CONTROL, CHECK.POLICY, CHECK.SENAL))
    t.igual("E-02 la senal que produce el modulo es la de la matriz",
            "unauthenticatedPublicInterfacePresent", CHECK.senal(_caso())["signalId"])
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("public-interface-abuse-control-required", "POLICY",
             "controles/policies/public-interface-abuse-control-required.md"),
            ("public-interface-abuse-protection", "CHECK",
             "controles/checks/public-interface-abuse-protection.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.igual("E-02 %s regla" % cid, "Vu9", registro[cid]["rule"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    gobierno = (REGLAS / "es0902-vu9-governance.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    for trozo in ("ruleKey: ES0902.Vu9", "mode: CONDITIONAL", "- unauthenticatedPublicInterfacePresent",
                  "- public-interface-abuse-control-required", "- public-interface-abuse-protection",
                  "reviews: []", "primaryAgents:\n  - dev-security\n  - dev-backend\n  - dev-devops"):
        t.contiene("E-02 el gobierno declara `%s`" % trozo, trozo, gobierno)
    t.contiene("E-02 la senal tiene su documento", "# Signal: unauthenticatedPublicInterfacePresent",
               (REGLAS / "es0902-vu9-unauthenticated-public-interface-present-signal.md").read_text(
                   encoding="utf-8"))
    t.contiene("E-02 el check tiene su documento", "# Check: public-interface-abuse-protection",
               (REGLAS / "es0902-vu9-public-interface-abuse-protection-check.md").read_text(encoding="utf-8"))
    politica = (CONTROLES / "policies" / "public-interface-abuse-control-required.md").read_text(
        encoding="utf-8")
    t.contiene("E-02 la policy declara su id", "id: public-interface-abuse-control-required", politica)
    t.contiene("E-02 y su regla", "rule: Vu9", politica)


def test_e03_nada_nuevo(t):
    """E-03."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 11, len(registro["agents"]))  # once desde la Wave 6: dev-iniciador-code se registro (integrity-cleanup, E-21)
    t.igual("E-03 los mismos once archivos de agentes, con el refutador", 11,
            len([p for p in AGENTES.glob("*.md")]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "owasp-security-guidance-review.md", "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-03 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    todas = _todas_las_senales()
    for nombre, r, esperado in (("PASS", _r(), "COMPLIANT"), ("sin resolver", _r(evidencia=_sin("ruta")),
                                                                 "UNRESOLVED"),
                                ("FAIL", _r(_reg([_sup(controles=[])])), "NON_COMPLIANT")):
        ev, sen = CHECK.para_seguridad(r)
        t.igual("E-03 con el resultado del check (%s), Vu9 da lo del generico" % nombre, esperado,
                seguridad.resultado("Vu9", ev, dict(todas, **sen), MATRIZ)["result"])
    ev, _ = CHECK.para_seguridad(_r())
    t.igual("E-03 con la forma vieja, sin mecanismos, sigue sin cumplir", "NON_COMPLIANT",
            seguridad.resultado("Vu9", dict(ev, abuseControls=[]), todas, MATRIZ)["result"])
    t.igual("E-03 los documentos de Vu9 son los tres del paquete",
            ["es0902-vu9-governance.md", "es0902-vu9-public-interface-abuse-protection-check.md",
             "es0902-vu9-unauthenticated-public-interface-present-signal.md"],
            sorted(p.name for p in REGLAS.glob("es0902-vu9-*")))
    senales = sorted(seguridad.senales_declaradas(MATRIZ))
    t.igual("E-03 las senales siguen siendo las de la matriz, sin una nueva", sorted({
        s for r in seguridad.reglas(MATRIZ) for s in r["applicability"].get("signals") or []}), senales)
    t.igual("E-03 y son quince", 15, len(senales))


# -- La senal -------------------------------------------------------------------

def _senal(evidencia, registro=None):
    return CHECK.derivar({"registry": registro if registro is not None else
                          {"version": "1.0", "environment": None, "surfaces": []},
                          "evidence": evidencia})["value"]


def test_e04_una_api_publica_enciende(t):
    """E-04."""
    t.igual("E-04 una operacion de API publica sin autenticacion enciende la senal", "TRUE",
            _senal([_publica()]))
    r = _r()
    t.igual("E-04 y con la superficie de API protegida, pasa", "PASS", r["state"])
    t.igual("E-04 la senal queda en TRUE en la salida", "TRUE", r["signalValue"])
    t.igual("E-04 y va a seguridad", {"unauthenticatedPublicInterfacePresent": True},
            CHECK.para_seguridad(r)[1])


def test_e05_una_funcionalidad_web_enciende(t):
    """E-05."""
    web = _publica(fuente="ROUTE_INVENTORY", eid="web")
    t.igual("E-05 una funcionalidad web publica sin autenticacion enciende la senal", "TRUE",
            _senal([web]))
    r = _r(_reg([_sup(tipo="WEB", operacion="POST /consulta", evidencia=("web", "inventario"))]),
           _sin("publica", web))
    t.igual("E-05 y la superficie web protegida pasa", "PASS", r["state"])
    t.igual("E-05 con su tipo", "WEB", _s(r)["interfaceType"])


def test_e06_un_asset_estatico_no_enciende(t):
    """E-06."""
    asset = _publica(fuente="STATIC_ASSET_EXPOSURE", eid="asset")
    t.igual("E-06 un asset estatico publico, solo, no enciende la senal", "UNRESOLVED", _senal([asset]))
    t.igual("E-06 y no hay PASS", SIN_APLIC,
            _estado(evidencia=_sin("publica", asset)))


def test_e07_un_dns_publico_no_enciende(t):
    """E-07."""
    for fuente in ("PUBLIC_DNS_RECORD", "HEALTH_ENDPOINT"):
        item = _publica(fuente=fuente, eid="dns")
        t.igual("E-07 un %s, solo, no enciende la senal" % fuente, "UNRESOLVED", _senal([item]))
        t.igual("E-07 y no hay PASS (%s)" % fuente, SIN_APLIC, _estado(evidencia=_sin("publica", item)))
    t.igual("E-07 y tampoco apaga: con un DNS y una ausencia autoritativa, sigue sin resolver",
            "UNRESOLVED", _senal([_publica(fuente="PUBLIC_DNS_RECORD", eid="dns"),
                                  _publica(valor="ABSENT", fuente="SECURITY_DOCUMENTATION", eid="no")]))


def test_e08_solo_lectura_sigue_en_alcance(t):
    """E-08."""
    t.igual("E-08 una funcionalidad de solo lectura enciende la senal", "TRUE",
            _senal([_publica(readOnly=True)]))
    con = _r(evidencia=_sin("publica", _publica(readOnly=True)))
    sin = _r(evidencia=_sin("publica", _publica(readOnly=False)))
    t.igual("E-08 readOnly no cambia el resultado", _json(sin), _json(con))
    t.igual("E-08 una superficie de solo lectura sin control falla igual", FALTA,
            _estado(_reg([_sup(controles=[])]), _sin("publica", _publica(readOnly=True))))
    usos = [n for n in ast.walk(_arbol()) if isinstance(n, ast.Constant) and n.value == "readOnly"]
    t.igual("E-08 el modulo nombra readOnly una sola vez: en el catalogo, que no lo lee", 1, len(usos))


def test_e09_lo_incompleto_no_resuelve(t):
    """E-09."""
    t.igual("E-09 sin inventario, la superficie no esta entera", SUPERFICIE,
            _estado(evidencia=_sin("inventario")))
    t.igual("E-09 con un inventario INCOMPLETE, tampoco", SUPERFICIE,
            _estado(evidencia=EVIDENCIA + [_inventario(valor="INCOMPLETE", eid="parcial")]))
    t.igual("E-09 dos inventarios enteros que no coinciden", SUPERFICIE,
            _estado(evidencia=EVIDENCIA + [_inventario([SUP, "otra"], eid="inventario-2")]))
    t.igual("E-09 un inventario de SOURCE_CODE no lo sostiene", SUPERFICIE,
            _estado(evidencia=_sin("inventario", _inventario(fuente="SOURCE_CODE"))))
    t.igual("E-09 el vacio", SIN_APLIC, CHECK.evaluar({"registry": _reg([]), "evidence": []})["state"])
    t.igual("E-09 una evidencia debil", SIN_APLIC,
            _estado(_reg([]), [_publica(fuente="README_STATEMENT")]))
    ausente = _publica(valor="ABSENT", fuente="SECURITY_DOCUMENTATION", eid="no")
    t.igual("E-09 una ausencia con algo ilegible", SIN_APLIC,
            _estado(_reg([]), [ausente, {"evidenceId": "roto", "sourceType": "X",
                                         "establishes": ["PUBLIC_UNAUTHENTICATED_FUNCTIONALITY"],
                                         "reference": "r", "payload": "x"}]))
    t.igual("E-09 una ausencia con una superficie registrada", SIN_APLIC, _estado(_reg(), [ausente]))
    t.igual("E-09 una ausencia autoritativa sola no aplica", NA, _estado(_reg([]), [ausente]))
    t.igual("E-09 una ausencia de SOURCE_CODE no apaga", SIN_APLIC,
            _estado(_reg([]), [_publica(valor="ABSENT", fuente="SOURCE_CODE")]))


# -- La cobertura ----------------------------------------------------------------

def test_e10_una_superficie_sin_control(t):
    """E-10."""
    r = _r(_reg([_sup(controles=[], resultado="PROTECTED")]))
    t.igual("E-10 falla aunque el registro la declare protegida", FALTA, r["state"])
    t.igual("E-10 en seguridad no cumple", "NON_COMPLIANT", _vu9_en_seguridad(r)["result"])
    ausente = _e("sin-control", "ASSESSMENT_FINDING", "USE_CONTROL", "ABSENT", [SUP])
    r2 = _r(_reg([_sup(evidencia=("publica", "inventario", "sin-control"))]), EVIDENCIA + [ausente])
    t.igual("E-10 una evidencia citada que dice que no hay control, tambien", FALTA, r2["state"])
    t.igual("E-10 y es la que sostiene la falla", ["sin-control"], _s(r2)["evidenceUsed"])
    t.igual("E-10 no citada, deja sin resolver", COBERTURA, _estado(evidencia=EVIDENCIA + [ausente]))
    anonima = _e("sin-control", "ASSESSMENT_FINDING", "USE_CONTROL", "ABSENT")
    t.igual("E-10 citada pero sin nombrar la superficie, no establece la falta", "PASS",
            _estado(_reg([_sup(evidencia=("publica", "inventario", "sin-control"))]), EVIDENCIA + [anonima]))


def test_e11_una_protegida_no_tapa_otra(t):
    """E-11."""
    r = _dos(_sup(OTRA, controles=[], evidencia=("publica-otra",)))
    t.igual("E-11 el agregado falla", FALTA, r["state"])
    t.igual("E-11 aunque la busqueda pase", "PASS", _s(r)["state"])
    t.igual("E-11 y el formulario falla", FALTA, _s(r, OTRA)["state"])
    t.igual("E-11 con las dos protegidas, pasa", "PASS", _dos()["state"])


def test_e12_la_superficie_entera(t):
    """E-12."""
    r = _r(evidencia=_sin("inventario", _inventario([SUP, OTRA])))
    t.igual("E-12 una superficie del inventario sin entrada impide el PASS", SUPERFICIE, r["state"])
    t.igual("E-12 y queda nombrada", [OTRA], r["coverage"]["missingSurfaces"])
    # Refutador, pase 1 (H-4): y al reves, una superficie en alcance que el inventario no nombra.
    for nombre, lista in (("vacio", []), ("de otra", ["otra"])):
        r = _r(evidencia=_sin("inventario", _inventario(lista)))
        t.igual("E-12 un inventario %s no cubre la superficie en alcance" % nombre, SUPERFICIE, r["state"])
        t.igual("E-12 (%s) y queda nombrada" % nombre, [SUP], r["coverage"]["notInInventory"])
    sacada = _sup(OTRA, controles=[], autenticada="YES", evidencia=())
    t.igual("E-12 una superficie sacada del alcance sin evidencia impide el PASS", SUPERFICIE,
            _dos(sacada)["state"])
    aut = _e("auth", "APPLICATION_CONFIGURATION", "AUTHENTICATION_REQUIRED", "YES", [OTRA])
    fuera = _r(_reg([_sup(), dict(sacada, evidence=["auth"])]), EVIDENCIA + [aut])
    t.igual("E-12 con la evidencia que la saca, no pesa", "PASS", fuera["state"])
    t.igual("E-12 y queda fuera de alcance", NA, _s(fuera, OTRA)["state"])
    t.igual("E-12 una evidencia que dice que es publica la vuelve a meter", SUPERFICIE,
            _estado(_reg([_sup(), dict(sacada, evidence=["auth"])]),
                    EVIDENCIA + [aut, _publica([OTRA], eid="dice-publica")]))
    anonima = _e("auth", "APPLICATION_CONFIGURATION", "AUTHENTICATION_REQUIRED", "YES")
    t.igual("E-12 una citada que no nombra la superficie no la saca", SUPERFICIE,
            _estado(_reg([_sup(), dict(sacada, evidence=["auth"])]), EVIDENCIA + [anonima]))
    t.igual("E-12 una evidencia que dice que pide autenticacion, no citada, no la saca", SUPERFICIE,
            _estado(_reg([_sup(), sacada]), EVIDENCIA + [aut]))
    t.igual("E-12 una superficie con UNRESOLVED no sale", SUPERFICIE,
            _dos(_sup(OTRA, controles=[], publica="UNRESOLVED", evidencia=()))["state"])
    t.igual("E-12 y sin el alcance resuelto no falla, aunque no tenga control",
            SUPERFICIE, _s(_dos(_sup(OTRA, controles=[], publica="UNRESOLVED", evidencia=())), OTRA)["state"])
    t.igual("E-12 sin ninguna superficie en alcance, con la senal en TRUE, no pasa", SUPERFICIE,
            _estado(_reg([_sup(autenticada="YES", evidencia=("auth-busqueda", "inventario"))]),
                    EVIDENCIA[1:] + [_e("auth-busqueda", "APPLICATION_CONFIGURATION",
                                        "AUTHENTICATION_REQUIRED", "YES", [SUP]),
                                     _publica([], eid="publica-sin-superficie")]))


# -- Donde vive el control -------------------------------------------------------

def _capa(capa, fuente_ctl, fuente_ruta, cid="c"):
    evid = [_existe(cid, fuente_ctl, eid="e-%s" % cid), _ruta(cid, fuente=fuente_ruta, eid="r-%s" % cid),
            _e("d-%s" % cid, fuente_ctl, ["EXCESSIVE_CONSUMPTION_MITIGATION",
                                           "AUTOMATED_CONSUMPTION_MITIGATION"], "EVIDENCED", None, [cid]),
            _estabilidad(cid=cid, fuente=fuente_ctl, eid="s-%s" % cid)]
    citas = [x["evidenceId"] for x in evid]
    ctl = _ctl(cid, capa, evidencia=citas)
    return _reg([_sup(controles=[ctl])]), [PUBLICA, INVENTARIO] + evid


def _sin_camino(reg, ev, cid="c"):
    """El caso sin la evidencia del camino y sin citarla: sin eso, cae por la cita ilegible."""
    reg = copy.deepcopy(reg)
    for c in reg["surfaces"][0]["controls"]:
        c["evidence"] = [i for i in c["evidence"] if i != "r-%s" % cid]
    return _estado(reg, [x for x in ev if x["evidenceId"] != "r-%s" % cid])


def test_e13_en_la_aplicacion(t):
    """E-13."""
    reg, ev = _capa("APPLICATION", "APPLICATION_CODE", "APPLICATION_CONFIGURATION")
    t.igual("E-13 un control en la aplicacion pasa", "PASS", _estado(reg, ev))
    t.igual("E-13 sin el camino no", COBERTURA, _sin_camino(reg, ev))


def test_e14_en_el_gateway(t):
    """E-14."""
    t.igual("E-14 un control en el gateway con camino pasa", "PASS", _estado())
    t.igual("E-14 sin el camino no", COBERTURA,
            _estado(_reg([_sup(controles=[_ctl(evidencia=("cuota", "excesivo", "automatizado", "capacidad"))])]),
                    _sin("ruta")))


def test_e15_en_el_waf(t):
    """E-15."""
    reg, ev = _capa("WAF", "WAF_CONFIGURATION", "NETWORK_TOPOLOGY")
    t.igual("E-15 un control en el WAF con camino pasa", "PASS", _estado(reg, ev))
    t.igual("E-15 sin el camino no", COBERTURA, _sin_camino(reg, ev))


def test_e16_en_el_router_de_openshift(t):
    """E-16."""
    reg, ev = _capa("OPENSHIFT_ROUTER", "INGRESS_CONFIGURATION", "INGRESS_CONFIGURATION")
    t.igual("E-16 un control en el router con camino pasa", "PASS", _estado(reg, ev))
    t.igual("E-16 sin el camino no", COBERTURA, _sin_camino(reg, ev))
    t.igual("E-16 con la capa sin resolver no", COBERTURA,
            _estado(_reg([_sup(controles=[dict(reg["surfaces"][0]["controls"][0],
                                               enforcementLayer="UNRESOLVED")])]), ev))


MECANISMOS = re.compile(r"(?i)rate|throttl|captcha|recaptcha|quota|cuota|backpressure|circuit|"
                        r"bucket|token bucket|concurren|req/|per minute|por minuto")


def test_e17_no_exige_rate_limiting(t):
    """E-17."""
    for tipo in ("cola con contrapresion", "limite de concurrencia", "costo por pedido"):
        t.igual("E-17 un control `%s` pasa" % tipo, "PASS",
                _estado(_reg([_sup(controles=[_ctl(tipo=tipo)])])))
    t.igual("E-17 el modulo no nombra ningun mecanismo", [],
            sorted(x for x in _literales() if MECANISMOS.search(x)))


def test_e18_no_exige_captcha(t):
    """E-18."""
    r = _r()
    t.igual("E-18 se pasa sin CAPTCHA", "PASS", r["state"])
    t.no_contiene("E-18 y nada en el caso nombra un CAPTCHA", "captcha", _json(_caso()).lower())
    t.igual("E-18 el modulo no nombra CAPTCHA", [], sorted(x for x in _literales() if "captcha" in x.lower()))


def test_e19_no_exige_waf(t):
    """E-19."""
    t.igual("E-19 se pasa con un gateway, sin WAF", "PASS", _estado())
    reg, ev = _capa("APPLICATION", "APPLICATION_CODE", "APPLICATION_CONFIGURATION")
    t.igual("E-19 y con la aplicacion sola", "PASS", _estado(reg, ev))
    t.no_contiene("E-19 sin ninguna evidencia de WAF", "WAF_CONFIGURATION", _json(ev))


def test_e20_ningun_numero(t):
    """E-20."""
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.igual("E-20 el modulo no tiene ningun numero mas alla de 0, 1 y 2", [], [x for x in numeros
                                                                               if x not in (0, 1, 2)])
    t.igual("E-20 el mismo control con otro limite declarado da el mismo resultado",
            _json(_r(_reg([_sup(controles=[_ctl(tipo="100 pedidos por minuto")])]))["surfaces"][0]["state"]),
            _json(_r(_reg([_sup(controles=[_ctl(tipo="5 pedidos por segundo")])]))["surfaces"][0]["state"]))


# -- El camino y el cliente --------------------------------------------------------

def _solo_cliente(fuente, eid):
    item = _existe(fuente=fuente, eid=eid)
    return _con(item, quitar=("cuota",))


def test_e21_un_boton_deshabilitado_no_es_un_control(t):
    """E-21."""
    r = _solo_cliente("CLIENT_SIDE_CONTROL", "boton")
    t.igual("E-21 un boton deshabilitado solo no pasa", COBERTURA, r["state"])
    t.igual("E-21 y queda a la vista como del cliente", ["boton"], _c(r)["clientSide"])
    t.verdadero("E-21 y no es FAIL", r["state"] not in FALLAS)


def test_e22_un_temporizador_no_es_un_control(t):
    """E-22."""
    r = _solo_cliente("FRONTEND_CODE", "temporizador")
    t.igual("E-22 un temporizador en JavaScript solo no pasa", COBERTURA, r["state"])
    t.igual("E-22 y queda a la vista como del cliente", ["temporizador"], _c(r)["clientSide"])
    ausente = _e("no-srv", "GATEWAY_CONFIGURATION", "USE_CONTROL", "ABSENT", [SUP])
    r2 = _r(_reg([_sup(controles=[_ctl(evidencia=["temporizador", "ruta"])],
                       evidencia=("publica", "inventario", "no-srv"))]),
            _sin("cuota", _existe(fuente="FRONTEND_CODE", eid="temporizador"), ausente))
    t.igual("E-22 con el servidor diciendo que no hay control, falta", FALTA, r2["state"])


def test_e23_un_origen_por_detras(t):
    """E-23."""
    detras = _ruta(valor="BYPASS_PRESENT", eid="origen")
    r = _con(detras)
    t.igual("E-23 un origen alcanzable por detras del gateway falla", SALTEO, r["state"])
    t.igual("E-23 en seguridad no cumple", "NON_COMPLIANT", _vu9_en_seguridad(r)["result"])
    t.igual("E-23 y lo sostiene la evidencia del salteo", ["origen"], _s(r)["evidenceUsed"])
    reg, ev = _capa("APPLICATION", "APPLICATION_CODE", "APPLICATION_CONFIGURATION")
    ambos = _reg([_sup(controles=[reg["surfaces"][0]["controls"][0],
                                  _ctl(evidencia=list(CITAS_CTL) + ["origen"])])])
    t.igual("E-23 falla aunque otro control de la aplicacion siga en el camino", SALTEO,
            _estado(ambos, EVIDENCIA + ev[2:] + [detras]))
    t.igual("E-23 declarar el salteo sin evidencia no falla", COBERTURA,
            _estado(_reg([_sup(controles=[_ctl(camino="BYPASS_PRESENT")])])))
    t.igual("E-23 un salteo no citado deja sin resolver", COBERTURA, _estado(evidencia=EVIDENCIA + [detras]))


def test_e24_configurado_no_es_atravesado(t):
    """E-24."""
    t.igual("E-24 configurado sin camino no pasa", COBERTURA, _estado(evidencia=_sin("ruta")))
    t.igual("E-24 declarado BOUND sin camino tampoco", COBERTURA,
            _estado(_reg([_sup(controles=[_ctl(evidencia=("cuota", "excesivo", "automatizado",
                                                           "capacidad"))])])))
    no_pasa = _ruta(valor="NOT_BOUND", eid="no-pasa")
    t.igual("E-24 un control que el camino no atraviesa, solo, deja la superficie sin control", FALTA,
            _estado(evidencia=_sin("ruta", no_pasa),
                    registro=_reg([_sup(controles=[_ctl(evidencia=("cuota", "no-pasa", "excesivo",
                                                                    "automatizado", "capacidad"))])])))
    reg, ev = _capa("APPLICATION", "APPLICATION_CODE", "APPLICATION_CONFIGURATION")
    dos = _reg([_sup(controles=[reg["surfaces"][0]["controls"][0],
                                _ctl(evidencia=("cuota", "no-pasa"))])])
    r = _r(dos, _sin("ruta", no_pasa) + ev[2:])
    t.igual("E-24 con otro control en el camino, pasa por ese", "PASS", r["state"])
    t.igual("E-24 y el que no atraviesa no cubre", "NOT_BOUND", _c(r)["coverage"])


def test_e25_una_politica_compartida(t):
    """E-25."""
    compartido = _ctl(evidencia=CITAS_CTL)
    ruta = _ruta(sups=[SUP, OTRA])
    r = _r(_reg([_sup(), _sup(OTRA, controles=[compartido], evidencia=("publica-otra",), tipo="WEB")]),
           _sin("inventario", "ruta", _inventario([SUP, OTRA]), ruta,
                _publica([OTRA], "ROUTE_INVENTORY", eid="publica-otra")))
    t.igual("E-25 la politica compartida cubre las dos", "PASS", r["state"])
    t.igual("E-25 con la misma evidencia del control", [["cuota"], ["cuota"]],
            [_c(r, sid=s)["existence"] for s in (SUP, OTRA)])
    t.igual("E-25 que es un solo item del catalogo", 1,
            len([x for x in _caso()["evidence"] if x["evidenceId"] == "cuota"]))
    solo_una = _r(_reg([_sup(), _sup(OTRA, controles=[compartido], evidencia=("publica-otra",))]),
                  _sin("inventario", _inventario([SUP, OTRA]),
                       _publica([OTRA], "ROUTE_INVENTORY", eid="publica-otra")))
    t.igual("E-25 sin el camino de la segunda, la segunda no pasa", COBERTURA, _s(solo_una, OTRA)["state"])
    t.igual("E-25 y la primera si", "PASS", _s(solo_una)["state"])
    # Refutador, pase 1: un camino que no nombra ninguna superficie no cubre ninguna.
    sin_superficie = _r(_reg([_sup(), _sup(OTRA, controles=[compartido], evidencia=("publica-otra",))]),
                        _sin("inventario", "ruta", _inventario([SUP, OTRA]), _ruta(sups=None),
                             _publica([OTRA], "ROUTE_INVENTORY", eid="publica-otra")))
    t.igual("E-25 un camino que solo nombra el control no cubre la primera", COBERTURA,
            _s(sin_superficie)["state"])
    t.igual("E-25 ni la segunda", COBERTURA, _s(sin_superficie, OTRA)["state"])
    t.igual("E-25 un control citado que no nombra ni control ni superficie no existe", COBERTURA,
            _estado(evidencia=_sin("cuota", _e("cuota", "GATEWAY_CONFIGURATION", "USE_CONTROL", "PRESENT"))))
    # Refutador, pase 2 (N-3): uno que nombra solo la superficie habla de la superficie, no del control.
    t.igual("E-25 un control citado que nombra solo la superficie no existe", COBERTURA,
            _estado(evidencia=_sin("cuota", _e("cuota", "GATEWAY_CONFIGURATION", "USE_CONTROL", "PRESENT",
                                               surfaces=[SUP]))))
    t.igual("E-25 una dimension que nombra solo la superficie no sostiene", EXCESIVO,
            _estado(evidencia=_sin("excesivo", _e("excesivo", "GATEWAY_CONFIGURATION",
                                                  "EXCESSIVE_CONSUMPTION_MITIGATION", "EVIDENCED",
                                                  surfaces=[SUP]))))
    t.igual("E-25 una dimension citada que no nombra nada no sostiene", EXCESIVO,
            _estado(evidencia=_sin("excesivo", _e("excesivo", "GATEWAY_CONFIGURATION",
                                                  "EXCESSIVE_CONSUMPTION_MITIGATION", "EVIDENCED"))))


# -- El consumo excesivo y el automatizado ------------------------------------------

def test_e26_el_excesivo_se_evidencia(t):
    """E-26."""
    t.igual("E-26 sin mitigacion del excesivo no pasa", EXCESIVO, _estado(evidencia=_sin("excesivo")))
    t.igual("E-26 declarada NOT_EVIDENCED tampoco", EXCESIVO,
            _estado(_reg([_sup(controles=[_ctl(exc="NOT_EVIDENCED")])])))


def test_e27_el_excesivo_sin_sostener_no_falla(t):
    """E-27."""
    contra = _excesivo(valor="NOT_EVIDENCED", eid="contra", fuente="APPLICATION_CONFIGURATION")
    r = _r(evidencia=EVIDENCIA + [contra])
    t.igual("E-27 una mitigacion contradicha queda sin resolver", EXCESIVO, r["state"])
    t.verdadero("E-27 y no falla", r["state"] not in FALLAS)
    t.igual("E-27 queda a la vista", ["contra"],
            _c(r)["dimensions"]["excessiveConsumptionMitigation"]["contradictedBy"])


def test_e28_el_automatizado_se_evidencia(t):
    """E-28."""
    t.igual("E-28 sin mitigacion del automatizado no pasa", AUTOMATIZADO,
            _estado(evidencia=_sin("automatizado")))


def test_e29_el_automatizado_sin_sostener_no_falla(t):
    """E-29."""
    r = _r(evidencia=_sin("automatizado", _automatizado(fuente="PERFORMANCE_TEST_REPORT")))
    t.igual("E-29 de una clase que no lo dice, queda sin resolver", AUTOMATIZADO, r["state"])
    t.verdadero("E-29 y no falla", r["state"] not in FALLAS)
    t.igual("E-29 del navegador tampoco", AUTOMATIZADO,
            _estado(evidencia=_sin("automatizado", _automatizado(fuente="CLIENT_SIDE_CONTROL"))))


def test_e30_sin_captcha_se_mitiga_lo_automatizado(t):
    """E-30."""
    r = _r()
    t.verdadero("E-30 una cuota del gateway sostiene la mitigacion automatizada",
                _s(r)["dimensions"]["automatedConsumptionMitigation"]["evidenced"])
    t.igual("E-30 con el control de la cuota", [CTL],
            _s(r)["dimensions"]["automatedConsumptionMitigation"]["controls"])


def test_e31_una_sola_evidencia_para_las_dos(t):
    """E-31."""
    ambas = _e("ambas", "GATEWAY_CONFIGURATION", ["EXCESSIVE_CONSUMPTION_MITIGATION",
                                                  "AUTOMATED_CONSUMPTION_MITIGATION"], "EVIDENCED", None,
               [CTL])
    r = _con(ambas, quitar=("excesivo", "automatizado"))
    t.igual("E-31 una sola evidencia sostiene las dos", "PASS", r["state"])
    dims = _c(r)["dimensions"]
    t.igual("E-31 y es la misma en las dos", (["ambas"], ["ambas"]),
            (dims["excessiveConsumptionMitigation"]["evidenceUsed"],
             dims["automatedConsumptionMitigation"]["evidenceUsed"]))


# -- La estabilidad -----------------------------------------------------------------

def test_e32_la_estabilidad_se_evidencia(t):
    """E-32."""
    r = _r(evidencia=_sin("capacidad"))
    t.igual("E-32 sin evidencia de estabilidad no pasa", ESTABILIDAD, r["state"])
    t.verdadero("E-32 y no falla", r["state"] not in FALLAS)


def test_e33_ningun_sla(t):
    """E-33."""
    t.igual("E-33 el modulo no nombra SLA, uptime ni disponibilidad", [],
            sorted(x for x in _literales() if re.search(r"(?i)\bsla\b|uptime|availability|%", x)
                   and "%s" not in x and "%d" not in x))


def test_e34_una_configuracion_acotada(t):
    """E-34."""
    t.igual("E-34 la configuracion de capacidad sostiene la estabilidad", "PASS", _estado())
    t.igual("E-34 y la del gateway tambien", "PASS",
            _estado(evidencia=_sin("capacidad", _estabilidad(fuente="GATEWAY_CONFIGURATION"))))


def test_e35_una_prueba_de_carga_acotada(t):
    """E-35."""
    carga = _prueba("capacidad", "SERVICE_STABILITY", "EVIDENCED")
    t.igual("E-35 una prueba acotada en QA sostiene la estabilidad", "PASS",
            _estado(evidencia=_sin("capacidad", carga)))


def test_e36_performance_no_cierra_vu9(t):
    """E-36."""
    # Cada afirmacion con su valor propio: lo que no sostiene es la clase, no el valor.
    informe = [_existe(fuente="PERFORMANCE_TEST_REPORT", eid="perf-control"),
               _ruta(fuente="PERFORMANCE_TEST_REPORT", eid="perf-camino"),
               _e("perf-dims", "PERFORMANCE_TEST_REPORT", ["EXCESSIVE_CONSUMPTION_MITIGATION",
                                                           "AUTOMATED_CONSUMPTION_MITIGATION",
                                                           "SERVICE_STABILITY"], "EVIDENCED", None, [CTL])]
    r = _r(_reg([_sup(controles=[_ctl(evidencia=[x["evidenceId"] for x in informe])])]),
           [PUBLICA, INVENTARIO] + informe)
    t.igual("E-36 un informe de performance en verde, solo, no cierra Vu9", COBERTURA, r["state"])
    t.igual("E-36 y no sostiene el control", [], _c(r)["existence"])
    t.igual("E-36 si sostiene la estabilidad de un control que cubre", "PASS",
            _estado(evidencia=_sin("capacidad", _estabilidad(fuente="PERFORMANCE_TEST_REPORT"))))


def test_e37_vu9_no_es_performance(t):
    """E-37."""
    ev, _ = CHECK.para_seguridad(_r())
    todas = _todas_las_senales()
    for fila in seguridad.reglas(MATRIZ):
        if fila["id"] == "Vu9":
            continue
        t.igual("E-37 %s no cambia con Vu9 en PASS" % fila["id"],
                seguridad.resultado(fila["id"], {}, todas, MATRIZ)["result"],
                seguridad.resultado(fila["id"], ev, todas, MATRIZ)["result"])
    claves = set()

    def recorrer(d):
        if isinstance(d, dict):
            claves.update(d)
            for v in d.values():
                recorrer(v)
        elif isinstance(d, list):
            for v in d:
                recorrer(v)
    recorrer(_r())
    t.igual("E-37 la salida no dice nada de performance", [],
            sorted(k for k in claves if re.search(r"(?i)perform|nfr|latenc", k)))


# -- El ambiente ------------------------------------------------------------------

def test_e38_dev_no_prueba_qa(t):
    """E-38."""
    for registro in ("QA", "HML", "PRD"):
        r = _r(_reg(ambiente=registro), _sin("ruta", _ruta(environment="DEV")))
        t.igual("E-38 el camino de DEV no sostiene un registro de %s" % registro, COBERTURA, r["state"])
    t.igual("E-38 el mismo camino, de QA, si sostiene QA", "PASS",
            _estado(evidencia=_sin("ruta", _ruta(environment="QA"))))
    t.igual("E-38 una evidencia sin ambiente vale para cualquiera", "PASS", _estado(_reg(ambiente="PRD")))
    detras = _ruta(valor="BYPASS_PRESENT", eid="origen", environment="DEV")
    r = _con(detras)
    t.igual("E-38 un salteo de DEV citado en QA no falla ni pasa", COBERTURA, r["state"])
    t.contiene("E-38 y queda a la vista", "origen", _json(_s(r)["contradictedBy"]))


def test_e39_las_huellas_de_despliegue(t):
    """E-39."""
    huellas = dict(routeVersion="route-v7", configFingerprint="sha256:abc", buildId="build-42",
                   imageDigest="sha256:def")
    r = _r(evidencia=_sin("cuota", "ruta", _existe(**{k: huellas[k] for k in ("configFingerprint",
                                                                                "imageDigest")}),
                          _ruta(**{k: huellas[k] for k in ("routeVersion", "buildId")})))
    t.igual("E-39 pasa", "PASS", r["state"])
    t.igual("E-39 las huellas de la evidencia usada salen", {k: [v] for k, v in huellas.items()},
            _c(r)["deployment"])


def test_e40_lo_estatico_alcanza(t):
    """E-40."""
    r = _r()
    t.igual("E-40 se pasa sin ninguna prueba en runtime", "PASS", r["state"])
    clases = {x["sourceType"] for x in EVIDENCIA if x["evidenceId"] in _s(r)["evidenceUsed"]}
    t.igual("E-40 con evidencia estatica sola",
            ["CAPACITY_CONFIGURATION", "GATEWAY_CONFIGURATION", "NETWORK_TOPOLOGY"], sorted(clases))


# -- La prueba ----------------------------------------------------------------------

def test_e41_una_prueba_acotada_y_autorizada(t):
    """E-41."""
    camino = _prueba("ruta", "PATH_BINDING", "BOUND", sups=[SUP])
    r = _r(evidencia=_sin("ruta", camino))
    t.igual("E-41 una prueba autorizada, acotada, en QA y sintetica sostiene el camino", "PASS", r["state"])
    t.igual("E-41 y es la que se usa", ["ruta"], _c(r)["path"]["bound"])


def test_e42_el_modulo_no_genera_pedidos(t):
    """E-42."""
    raices = ({a.name.split(".")[0] for n in ast.walk(_arbol()) if isinstance(n, ast.Import)
               for a in n.names}
              | {(n.module or "").split(".")[0] for n in ast.walk(_arbol())
                 if isinstance(n, ast.ImportFrom)})
    t.igual("E-42 no importa nada que abra una conexion o un proceso", set(),
            {"subprocess", "socket", "urllib", "requests", "http", "asyncio", "threading",
             "multiprocessing", "ssl"} & raices)
    t.igual("E-42 no tiene ningun while", [], [n for n in ast.walk(_arbol()) if isinstance(n, ast.While)])
    escrituras = [n for n in ast.walk(_arbol()) if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", getattr(n.func, "id", "")) == "open"
                  and any(isinstance(a, ast.Constant) and "w" in str(a.value) for a in n.args[1:])]
    t.igual("E-42 y no abre nada para escribir", [], escrituras)


def _insegura(**cambios):
    return _r(evidencia=_sin("ruta", _prueba("ruta", "PATH_BINDING", "BOUND", sups=[SUP], **cambios)))


def test_e43_nada_en_produccion(t):
    """E-43."""
    r = _insegura(environment="PRD")
    t.igual("E-43 una prueba en PRD es insegura", INSEGURA, r["state"])
    t.verdadero("E-43 y dice por que", "PRODUCTION" in _s(r)["unsafe"])


def test_e44_datos_sinteticos(t):
    """E-44."""
    for nombre, cambio in (("sin la marca", {"syntheticData": None}), ("con datos reales",
                                                                       {"syntheticData": False})):
        r = _insegura(**cambio)
        t.igual("E-44 una prueba %s es insegura" % nombre, INSEGURA, r["state"])
        t.verdadero("E-44 %s dice por que" % nombre, "NOT_SYNTHETIC_DATA" in _s(r)["unsafe"])


def test_e45_una_prueba_insegura(t):
    """E-45."""
    for nombre, cambio, motivo in (
            ("no autorizada", {"authorized": None}, "NOT_AUTHORIZED"),
            ("no acotada", {"bounded": None}, "NOT_BOUNDED"),
            ("sin condiciones de corte", {"stopConditions": False}, "NO_STOP_CONDITIONS"),
            ("destructiva", {"destructive": True}, "DESTRUCTIVE"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED"),
            ("en un ambiente desconocido", {"environment": "LAB"}, "ENVIRONMENT_UNKNOWN")):
        r = _insegura(**cambio)
        t.igual("E-45 %s" % nombre, INSEGURA, r["state"])
        t.verdadero("E-45 %s dice por que" % nombre, motivo in _s(r)["unsafe"])


def test_e46_insegura_no_es_pass_ni_fail(t):
    """E-46."""
    for citada in (True, False):
        salteo = _prueba("insegura", "PATH_BINDING", "BYPASS_PRESENT", sups=[SUP], environment="PRD")
        r = _con(salteo) if citada else _r(evidencia=EVIDENCIA + [salteo])
        t.igual("E-46 una insegura %s que dice que se saltea" % ("citada" if citada else "no citada"),
                INSEGURA, r["state"])
        t.verdadero("E-46 (%s) no es FAIL" % citada, r["state"] not in FALLAS)
    ajena = _r(evidencia=EVIDENCIA + [_prueba("ajena", "PATH_BINDING", "BOUND", ctls=("otro",),
                                              sups=["otra-superficie"], environment="PRD")])
    t.igual("E-46 una insegura que habla de otra superficie no bloquea", "PASS", ajena["state"])
    # Refutador, pase 1 (H-1): lo que no se pudo leer pesa si toca la superficie o un control suyo,
    # diga lo que diga, y en todas sus formas.
    toca = _r(evidencia=EVIDENCIA + [_prueba("toca", "PATH_BINDING", "BOUND", sups=[SUP], environment="PRD")])
    t.igual("E-46 una insegura no citada que toca la superficie bloquea, aunque diga BOUND", INSEGURA,
            toca["state"])
    solo_control = _r(evidencia=EVIDENCIA + [_prueba("ctl", "PATH_BINDING", "BYPASS_PRESENT", environment="PRD")])
    t.igual("E-46 una insegura no citada que nombra solo el control bloquea", INSEGURA, solo_control["state"])
    for outcome in ("INCONCLUSIVE", "REFUTED"):
        t.igual("E-46 un ABSENT %s no citado que nombra solo el control no deja pasar" % outcome, COBERTURA,
                _estado(evidencia=EVIDENCIA + [_existe(valor="ABSENT", eid="raro", outcome=outcome)]))
        t.igual("E-46 un PRESENT %s no citado que nombra la superficie tampoco" % outcome, COBERTURA,
                _estado(evidencia=EVIDENCIA + [_existe(valor="PRESENT", eid="raro", sups=[SUP],
                                                       outcome=outcome)]))
    # Refutador, pase 2: un control compartido. Un item que nombra la otra superficie y el control toca
    # esta superficie, y en las tres formas pesa igual.
    compartido = _r(_reg([_sup(), _sup(OTRA, controles=[_ctl(evidencia=list(CITAS_CTL) + ["ruta-otra"])],
                                       evidencia=("publica-otra",))]),
                    _sin("inventario", _inventario([SUP, OTRA]), _publica([OTRA], eid="publica-otra"),
                         _ruta(sups=[OTRA], eid="ruta-otra")))
    t.igual("E-46 (compartido) sin nada raro pasa", "PASS", compartido["state"])
    base_dos = [_inventario([SUP, OTRA]), _publica([OTRA], eid="publica-otra"), _ruta(sups=[OTRA], eid="ruta-otra")]
    reg_dos = _reg([_sup(), _sup(OTRA, controles=[_ctl(evidencia=list(CITAS_CTL) + ["ruta-otra"])],
                                 evidencia=("publica-otra",))])
    for forma, item in (("mal formado", dict(_ruta(sups=[OTRA], valor="BYPASS_PRESENT", eid="x"), extra="y")),
                        ("INCONCLUSIVE", _ruta(sups=[OTRA], valor="BYPASS_PRESENT", eid="x", outcome="INCONCLUSIVE")),
                        ("prueba insegura", _prueba("x", "PATH_BINDING", "BYPASS_PRESENT", sups=[OTRA],
                                                    environment="PRD"))):
        r = _r(reg_dos, _sin("inventario", *base_dos, item))
        t.verdadero("E-46 (compartido, %s) la busqueda no pasa" % forma, _s(r)["state"] != "PASS")
        t.verdadero("E-46 (compartido, %s) y no falla" % forma, _s(r)["state"] not in FALLAS)
    # Refutador, pase 2 (N-1): en el paso 2 manda lo que falta de verdad.
    camino_inseguro = _prueba("q", "PATH_BINDING", "BOUND", sups=[SUP], environment="PRD")
    t.igual("E-46 falta la existencia, con una insegura del camino: falta la existencia", COBERTURA,
            _con(camino_inseguro, quitar=("cuota",))["state"])
    t.igual("E-46 la capa sin resolver, con una insegura del camino: falta la capa", COBERTURA,
            _con(camino_inseguro, capa="UNRESOLVED")["state"])
    # Refutador, pase 1 (H-2): una insegura citada que habla de estabilidad no cambia lo que falta del
    # consumo excesivo, ni del camino.
    estable = _prueba("carga", "SERVICE_STABILITY", "EVIDENCED", environment="PRD")
    t.igual("E-46 sin excesivo, una insegura de estabilidad deja el excesivo como lo que falta", EXCESIVO,
            _con(estable, quitar=("excesivo",))["state"])
    t.igual("E-46 sin camino, deja la cobertura como lo que falta", COBERTURA,
            _con(estable, quitar=("ruta",))["state"])
    falla = _con(_ruta(valor="BYPASS_PRESENT", eid="origen"),
                 _prueba("insegura", "PATH_BINDING", "BOUND", sups=[SUP], environment="PRD"))
    t.igual("E-46 una insegura no tapa un FAIL", SALTEO, falla["state"])
    sin_objetivo = _insegura(outcome="UNAVAILABLE")
    t.igual("E-46 sin objetivo", SIN_OBJ, sin_objetivo["state"])
    t.verdadero("E-46 y no es FAIL", sin_objetivo["state"] not in FALLAS)
    for outcome in ("UNAVAILABLE", "INCONCLUSIVE", "REFUTED"):
        raro = _ruta(valor="BYPASS_PRESENT", eid="raro", outcome=outcome)
        r = _con(raro)
        t.igual("E-46 un salteo %s citado no pasa ni falla" % outcome, COBERTURA, r["state"])
        bien = _r(evidencia=_sin("ruta", _ruta(outcome=outcome)))
        t.igual("E-46 un camino %s citado no pasa" % outcome, COBERTURA, bien["state"])
    t.igual("E-46 CONFIRMED y OBSERVED si se leen", [SALTEO, SALTEO],
            [_con(_ruta(valor="BYPASS_PRESENT", eid="raro", outcome=o))["state"]
             for o in ("CONFIRMED", "OBSERVED")])


# -- Los limites --------------------------------------------------------------------

def test_e47_vu1_no_es_vu9(t):
    """E-47."""
    todas = _todas_las_senales()
    t.igual("E-47 Vu1 en PASS pasa por su lado", "COMPLIANT",
            seguridad.resultado("Vu1", _de_control_pasa("Vu1"), todas, MATRIZ)["result"])
    t.verdadero("E-47 y Vu9 no cumple con eso",
                seguridad.resultado("Vu9", _de_control_pasa("Vu1"), todas, MATRIZ)["result"] != "COMPLIANT")


def test_e48_vu9_no_es_vu1(t):
    """E-48."""
    ev, _ = CHECK.para_seguridad(_r())
    todas = _todas_las_senales()
    t.igual("E-48 Vu9 en PASS cumple", "COMPLIANT", seguridad.resultado("Vu9", ev, todas, MATRIZ)["result"])
    t.igual("E-48 y Vu1 no se mueve", seguridad.resultado("Vu1", {}, todas, MATRIZ)["result"],
            seguridad.resultado("Vu1", ev, todas, MATRIZ)["result"])


def test_e49_vu10_no_es_vu9(t):
    """E-49."""
    todas = _todas_las_senales()
    vu10 = _de_control_pasa("Vu10")
    t.verdadero("E-49 la review de Vu10 en PASS no pone en PASS a Vu9",
                seguridad.resultado("Vu9", vu10, todas, MATRIZ)["result"] != "COMPLIANT")
    t.igual("E-49 la fila de Vu10 tiene su review", ["owasp-security-guidance-review"],
            seguridad.regla("Vu10", MATRIZ)["reviews"])


def test_e50_vu9_no_es_vu10(t):
    """E-50."""
    ev, _ = CHECK.para_seguridad(_r())
    todas = _todas_las_senales()
    t.igual("E-50 Vu10 no se mueve con Vu9 en PASS", seguridad.resultado("Vu10", {}, todas, MATRIZ)["result"],
            seguridad.resultado("Vu10", ev, todas, MATRIZ)["result"])
    t.verdadero("E-50 y no cumple", seguridad.resultado("Vu10", ev, todas, MATRIZ)["result"] != "COMPLIANT")


# -- La refutacion atomica ------------------------------------------------------------

CLAVE_REF = "GCBA-9051"
OTRA_TAREA = "GCBA-9054"
_PLANTILLA = {}


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def _plan(clave):
    if clave not in _PLANTILLA:
        tc = {"meta": {"task_key": clave, "context_hash": "h"}, "task": {"title": "t"}}
        prop = {"objective": "o", "domains": ["backend"],
                "workUnits": [{"id": wu, "objective": "x", "domain": "backend"} for wu in ("WU-1", "WU-2")]}
        _PLANTILLA[clave] = json.dumps(orq_plan.armar(prop, tc, {}, {}))
    return json.loads(_PLANTILLA[clave])


def _plantilla():
    if "base" not in _PLANTILLA:
        base = Path(tempfile.gettempdir()) / ("harness-vu9-base-" + uuid.uuid4().hex[:8])
        _escribir(base / "config" / "gateway.yml", "politica: cuota-por-cliente\n")
        _escribir(base / "src" / "busqueda.py", "def buscar(q): return []\n")
        _escribir(base / "otro" / "nada.py", "x = 1\n")
        for args in (("init", "-q"), ("add", "-A"), ("commit", "-q", "-m", "i")):
            subprocess.run(["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t"]
                           + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        _PLANTILLA["base"] = base
    return _PLANTILLA["base"]


def _bloque(reglas, checks=("public-interface-abuse-protection",)):
    return {"standard": {"id": "ES0902", "version": "6.2"}, "applicableRules": list(reglas),
            "notApplicableRules": [], "unresolvedRules": [], "declaredPolicies": [],
            "declaredChecks": list(checks), "declaredReviews": []}


def _tarea(proy, clave, unidades, scope):
    doc = _plan(clave)
    doc["workUnits"] = [u for u in doc["workUnits"] if u["id"] in unidades]
    for u in doc["workUnits"]:
        u["normative"] = dict(u["normative"], standards={"ES0902": unidades[u["id"]]})
    _escribir(proy / ".claude" / "planes" / (clave + ".json"), json.dumps(doc, ensure_ascii=False))
    if scope is not None:
        _escribir(proy / ".claude" / "refutaciones" / clave / "scope.json",
                  json.dumps({"schema_version": R.VERSION_ALCANCE, "workUnits": scope}))


def _proyecto(unidades, scope):
    proy = Path(tempfile.gettempdir()) / ("harness-vu9-" + uuid.uuid4().hex[:8])
    shutil.copytree(str(_plantilla()), str(proy))
    _tarea(proy, CLAVE_REF, unidades, scope)
    _caso_55()._listo_para_la_compuerta(proy, CLAVE_REF)
    return proy


def _caso_55():
    """La refutacion atomica, por su `_listo_para_la_compuerta` (Wave 6: `compilar` evalua la
    compuerta tambien como biblioteca)."""
    if "55" not in _CASOS:
        import importlib.util as _iu
        spec = _iu.spec_from_file_location("caso_55_compuerta", str(
            Path(__file__).resolve().parent / "55_refutacion_atomica.py"))
        modulo = _iu.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CASOS["55"] = modulo
    return _CASOS["55"]


_CASOS = {}


def _alcance(*paths, sid="gateway"):
    return [{"scopeId": sid, "source": "workUnitFiles", "paths": list(paths)}]


def _unidades(proy, clave=CLAVE_REF):
    return R.leer(str(proy), clave)[1]


def _con_resultado(r):
    """El proyecto de una unidad de Vu9, con la salida del check en checks.json."""
    proy = _proyecto({"WU-1": _bloque(["Vu9"])}, {"WU-1": _alcance("config/gateway.yml")})
    R.compilar(str(proy), CLAVE_REF)
    u = _unidades(proy)[0]
    entrada = CHECK.para_refutacion(r, u)
    _escribir(proy / ".claude" / "refutaciones" / CLAVE_REF / "checks.json",
              json.dumps({"schema_version": R.VERSION_CHECKS, "results": [entrada]}))
    doc = R.compilar(str(proy), CLAVE_REF)
    return proy, doc, _unidades(proy)[0], entrada


def _levanta(funcion, codigo=None):
    try:
        funcion()
    except R.RefutacionInvalida as e:
        return codigo is None or e.codigo == codigo
    return False


def _veredicto(u, **cambios):
    v = {"schema_version": R.VERSION_VEREDICTO, "refutationUnitId": u["refutationUnitId"],
         "workUnitId": u["workUnitId"], "ruleKey": "ES0902.Vu9", "verdict": "cumple",
         "reason": None, "citation": {"skillId": u["skillId"], "locator": "ES0902 §6"},
         "evidence": [{"path": "config/gateway.yml", "line": 1, "observed": "politica: cuota-por-cliente"}],
         "needed": None, "cacheKey": u["cacheKey"],
         "evidenceFingerprint": u["evidenceFingerprint"], "repoRevision": u["repoRevision"]}
    v.update(cambios)
    return v


def test_e51_una_unidad_por_regla_y_alcance(t):
    """E-51."""
    proy = _proyecto({"WU-1": _bloque(["Vu9", "Vu1"]), "WU-2": _bloque(["Vu9"])},
                     {"WU-1": _alcance("config/gateway.yml"), "WU-2": _alcance("src/busqueda.py", sid="app")})
    try:
        R.compilar(str(proy), CLAVE_REF)
        de_vu9 = [u for u in _unidades(proy) if u["standard"]["ruleKey"] == "ES0902.Vu9"]
        t.igual("E-51 una unidad de Vu9 por unidad de trabajo", ["WU-1", "WU-2"],
                sorted(u["workUnitId"] for u in de_vu9))
        t.igual("E-51 con el alcance de cada una", [["config/gateway.yml"], ["src/busqueda.py"]],
                [u["evidenceScope"]["paths"] for u in sorted(de_vu9, key=lambda u: u["workUnitId"])])
        t.igual("E-51 y Vu1 queda en su propia unidad", 1,
                len([u for u in _unidades(proy) if u["standard"]["ruleKey"] == "ES0902.Vu1"]))
        skills = {s["id"] for a in c_reg.cargar()["agents"]
                  if a["id"] in ("dev-security", "dev-backend", "dev-devops") for s in a["skills"]}
        for u in de_vu9:
            t.verdadero("E-51 %s: la skill es de un agente de la fila" % u["workUnitId"], u["skillId"] in skills)
            t.igual("E-51 %s: la unidad valida" % u["workUnitId"], [], R.validar(u, R.SCHEMA_UNIDAD))
            t.verdadero("E-51 %s: declara el check" % u["workUnitId"],
                        "public-interface-abuse-protection" in u["declaredChecks"])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e52_un_check_concluyente_no_llama_al_refutador(t):
    """E-52."""
    for nombre, r, veredicto in (
            ("PASS", _r(), "cumple"),
            ("MISSING", _r(_reg([_sup(controles=[])])), "incumple"),
            ("BYPASS", _con(_ruta(valor="BYPASS_PRESENT", eid="origen")), "incumple")):
        proy, doc, u, entrada = _con_resultado(r)
        try:
            t.igual("E-52 %s: la entrada valida" % nombre, [],
                    R.validar({"schema_version": R.VERSION_CHECKS, "results": [entrada]},
                              R.SCHEMA_UNIDAD, "checksInput"))
            t.igual("E-52 %s: resuelta" % nombre, "RESOLVED", u["status"])
            t.igual("E-52 %s: veredicto" % nombre, veredicto, doc["units"][0]["verdict"])
            t.igual("E-52 %s: por check" % nombre, "DETERMINISTIC_CHECK", u["resolutionPath"])
            t.verdadero("E-52 %s: y el refutador no la recibe" % nombre,
                        _levanta(lambda: R.para_refutar(str(proy), CLAVE_REF, u["refutationUnitId"])))
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)
    t.igual("E-52 una unidad de otra regla no se traduce", None,
            CHECK.para_refutacion(_r(), {"standard": {"ruleKey": "ES0902.Vu1"}, "evidenceFingerprint": "h"}))
    t.igual("E-52 un resultado ajeno tampoco", None,
            CHECK.para_refutacion(dict(_r(), control="otro"), {"standard": {"ruleKey": "ES0902.Vu9"},
                                                               "evidenceFingerprint": "h"}))


def test_e53_un_sin_resolver_queda_acotado(t):
    """E-53."""
    for nombre, r in (("sin camino", _r(evidencia=_sin("ruta"))),
                      ("insegura", _insegura(environment="PRD"))):
        proy, doc, u, _ = _con_resultado(r)
        try:
            t.igual("E-53 %s: pendiente" % nombre, "PENDING_SEMANTIC", u["status"])
            t.igual("E-53 %s: una sola pendiente" % nombre, 1, doc["counts"]["pending"])
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)
    proy, doc, u, _ = _con_resultado(_r(evidencia=_sin("ruta")))
    try:
        entregada = R.para_refutar(str(proy), CLAVE_REF, u["refutationUnitId"])
        entregada = entregada[0] if isinstance(entregada, list) else entregada
        t.igual("E-53 la unidad lleva solo el alcance declarado", ["config/gateway.yml"],
                entregada["evidenceScope"]["paths"])
        t.igual("E-53 y una sola regla", "ES0902.Vu9", entregada["standard"]["ruleKey"])
        t.verdadero("E-53 un veredicto de otra regla se rechaza",
                    _levanta(lambda: R.registrar(str(proy), CLAVE_REF,
                                                 json.dumps(_veredicto(u, ruleKey="ES0902.Vu1"))),
                             "REFUTATION_OUTPUT_INVALID"))
        t.verdadero("E-53 uno con evidencia fuera del alcance tambien",
                    _levanta(lambda: R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(
                        u, evidence=[{"path": "src/busqueda.py", "line": 1,
                                      "observed": "def buscar(q): return []"}]))),
                             "REFUTATION_OUTPUT_INVALID"))
        t.verdadero("E-53 y el que se queda en el alcance se acepta",
                    not _levanta(lambda: R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(u)))))
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e54_la_huella_invalida_la_cache(t):
    """E-54."""
    proy = _proyecto({"WU-1": _bloque(["Vu9"])}, {"WU-1": _alcance("config/gateway.yml")})
    try:
        R.compilar(str(proy), CLAVE_REF)
        u = _unidades(proy)[0]
        R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(u)))
        _tarea(proy, OTRA_TAREA, {"WU-1": _bloque(["Vu9"])}, {"WU-1": _alcance("config/gateway.yml")})
        _caso_55()._listo_para_la_compuerta(proy, OTRA_TAREA)
        R.compilar(str(proy), OTRA_TAREA)
        t.igual("E-54 con la misma evidencia se reusa", "CACHE", _unidades(proy, OTRA_TAREA)[0]["resolutionPath"])
        _escribir(proy / "config" / "gateway.yml", "politica: ninguna\n")
        tercera = "GCBA-9055"
        _tarea(proy, tercera, {"WU-1": _bloque(["Vu9"])}, {"WU-1": _alcance("config/gateway.yml")})
        _caso_55()._listo_para_la_compuerta(proy, tercera)
        R.compilar(str(proy), tercera)
        otra = _unidades(proy, tercera)[0]
        t.verdadero("E-54 otra evidencia, otra huella", otra["evidenceFingerprint"] != u["evidenceFingerprint"])
        t.verdadero("E-54 y otra clave de cache", otra["cacheKey"] != u["cacheKey"])
        t.igual("E-54 el veredicto guardado no se reusa", "PENDING_SEMANTIC", otra["status"])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e55_sin_alcance_no_se_refuta_el_repo(t):
    """E-55."""
    proy = _proyecto({"WU-1": _bloque(["Vu9"])}, {})
    try:
        R.compilar(str(proy), CLAVE_REF)
        u = _unidades(proy)[0]
        t.igual("E-55 una unidad sin alcance queda bloqueada", "BLOCKED", u["status"])
        t.igual("E-55 sin huella de evidencia", None, u["evidenceFingerprint"])
        t.verdadero("E-55 y no se entrega al refutador",
                    _levanta(lambda: R.para_refutar(str(proy), CLAVE_REF, u["refutationUnitId"])))
        t.igual("E-55 y el check no la traduce", None, CHECK.para_refutacion(_r(), u))
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


# -- La salida y el agregado ------------------------------------------------------------

def test_e56_entra_al_libro_de_siempre(t):
    """E-56."""
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu9_56_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-9056")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _r(_reg([_sup(controles=[])])), "NON_COMPLIANT"),
                     ("sin resolver", _r(evidencia=_sin("ruta")), "UNRESOLVED"),
                     ("vacio", CHECK.evaluar({}), "UNRESOLVED"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu9_en_seguridad(r)
            t.igual("E-56 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-9056", alcance, "2026-09-26T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-56 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-56 de ES0902.Vu9", [("ES0902", "Vu9", "ES0902.Vu9")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-56 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "UNRESOLVED"], [e["result"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    dominios = json.loads((REGLAS / "security-report-domains.json").read_text(encoding="utf-8"))["domains"]
    t.igual("E-56 Vu9 esta en sensitive-data-public-interfaces, y en ningun otro dominio",
            ["sensitive-data-public-interfaces"], [d["domainId"] for d in dominios if "Vu9" in d["rules"]])
    t.igual("E-56 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))
    t.igual("E-56 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in (BIN / "reporte_seguridad").iterdir() if p.is_file()))
    importados = set()
    for n in ast.walk(_arbol()):
        if isinstance(n, ast.Import):
            importados.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            importados.update("%s.%s" % (n.module, a.name) for a in n.names)
    t.igual("E-56 el modulo importa esto y nada mas",
            sorted({"evidencia", "io", "json", "orquestacion.roster", "orquestacion.senales",
                    "orquestacion.tools", "os", "rutas", "sys"}), sorted(importados))


def test_e57_ninguna_credencial_sale(t):
    """E-57."""
    contrasena = "postgres://busqueda:" + "S3cr3t0!@db.qa.local/app"
    reg = _reg([_sup(operacion="GET /buscar?token=" + TOKEN)])
    reg["surfaces"][0]["controls"][0]["controlType"] = contrasena
    r = _r(reg, _sin("cuota", _existe(reference=TOKEN)))
    texto = _json(r)
    unidad = _json(_unidad(r))
    evento = _json(prod.desde_regla(_vu9_en_seguridad(r), "GCBA-9057", {"project": "P"},
                                    "2026-09-26T10:00:00"))
    for nombre, salida in (("la salida", texto), ("la unidad", unidad), ("el libro", evento)):
        t.no_contiene("E-57 %s no lleva el token" % nombre, TOKEN, salida)
        t.no_contiene("E-57 %s no lleva la contrasena" % nombre, "S3cr3t0", salida)
    t.igual("E-57 sin cambiar el resultado", "PASS", r["state"])
    # Refutador, pase 1 (H-5): operationRef y controlType son texto libre y no salen: ni un dato personal.
    personal = _reg([_sup(operacion="GET /buscar?dni=30123456&nombre=Juana Perez")])
    personal["surfaces"][0]["controls"][0]["controlType"] = "contacto: juana.perez@example.com"
    salida = _json(_r(personal))
    for dato in ("30123456", "Juana Perez", "juana.perez@example.com"):
        t.no_contiene("E-57 `%s` no sale" % dato, dato, salida)
    t.verdadero("E-57 la salida no tiene los campos libres",
                all("operationRef" not in s and all("controlType" not in c for c in s["controls"])
                    for s in _r()["surfaces"]))
    # La regla de salida compartida sigue en el camino: un id con forma de credencial sale redactado.
    raro = "token=" + TOKEN
    r = _r(_reg([_sup(controles=[_ctl(evidencia=[raro, "ruta", "excesivo", "automatizado", "capacidad"])])]),
           _sin("cuota", _existe(eid=raro)))
    t.contiene("E-57 lo que tiene forma de credencial sale redactado", "[redactado]", _json(r))
    t.no_contiene("E-57 y el token no", TOKEN, _json(r))
    esquema = json.loads((SCHEMAS / "public-interface-abuse-protection.schema.json").read_text(encoding="utf-8"))
    t.igual("E-57 el schema es el que se valida", "public-interface-abuse-protection/1.0", esquema["$id"])
    t.vacio("E-57 el registro vacio instalado valida",
            CHECK.validar_schema(json.loads((REGLAS / "public-interface-abuse-protection.json").read_text(
                encoding="utf-8"))))
    for capa, parchar in (("la raiz", lambda d: d.update(password="x")),
                          ("la superficie", lambda d: d["surfaces"][0].update(token="x")),
                          ("el control", lambda d: d["surfaces"][0]["controls"][0].update(credential="x"))):
        doc = _reg()
        parchar(doc)
        t.verdadero("E-57 una clave de mas en %s no valida" % capa, CHECK.validar_schema(doc))


def test_e58_ningun_script_ni_payload(t):
    """E-58."""
    for campo in ("script", "payload", "requestBody", "attackScript"):
        r = _r(evidencia=_sin("ruta", dict(RUTA, **{campo: "while true; do curl ...; done"})))
        t.verdadero("E-58 un item con `%s` queda mal formado" % campo,
                    any("mal formada" in i for i in r["issues"]))
        t.igual("E-58 y no sostiene nada (%s)" % campo, COBERTURA, r["state"])
        t.no_contiene("E-58 y no sale (%s)" % campo, "curl", _json(r))
        doc = _reg()
        doc["surfaces"][0][campo] = "x"
        t.verdadero("E-58 el registro no tiene donde guardar `%s`" % campo, CHECK.validar_schema(doc))


def test_e59_una_falla_tumba_el_agregado(t):
    """E-59."""
    salteada = _dos(_sup(OTRA, controles=[_ctl("app-limite", "APPLICATION", evidencia=(
        "existe-app", "ruta-app", "dims-app", "capacidad-app", "origen-otra"))],
        evidencia=("publica-otra",)), [_ruta("app-limite", [OTRA], "BYPASS_PRESENT", eid="origen-otra")])
    t.igual("E-59 un salteo en una superficie tumba el agregado", SALTEO, salteada["state"])
    t.igual("E-59 aunque la otra pase", "PASS", _s(salteada)["state"])
    faltante = _dos(_sup(OTRA, controles=[], evidencia=("publica-otra",)))
    t.igual("E-59 un control faltante tambien", FALTA, faltante["state"])
    ambas = _r(_reg([_sup(controles=[]), _sup(OTRA, controles=[_ctl(evidencia=list(CITAS_CTL) + ["o"])],
                                              evidencia=("publica-otra",))]),
               _sin("inventario", _inventario([SUP, OTRA]), _publica([OTRA], eid="publica-otra"),
                    _ruta(sups=[OTRA], valor="BYPASS_PRESENT", eid="o")))
    t.igual("E-59 con las dos formas de fallar, el salteo va primero", SALTEO, ambas["state"])


def test_e60_una_dimension_sin_resolver_impide_el_pass(t):
    """E-60."""
    r = _dos(evidencia_extra=[_estabilidad(cid="app-limite", eid="capacidad-app", valor="NOT_EVIDENCED")])
    t.igual("E-60 una dimension sin resolver en una superficie impide el PASS", ESTABILIDAD, r["state"])
    t.igual("E-60 aunque la otra pase", "PASS", _s(r)["state"])
    t.igual("E-60 en seguridad no cumple", "UNRESOLVED", _vu9_en_seguridad(r)["result"])
    # Refutador, pase 2 (N-2): gana el primer sin resolver de la lista de la spec, no el primer paso.
    t.igual("E-60 sin excesivo y declarada UNRESOLVED, gana la cobertura", COBERTURA,
            _estado(_reg([_sup(resultado="UNRESOLVED")]), _sin("excesivo")))
    t.igual("E-60 una superficie declarada NOT_VERIFIED tampoco", COBERTURA,
            _estado(_reg([_sup(modo="NOT_VERIFIED")])))
    t.igual("E-60 ni una declarada UNRESOLVED", COBERTURA, _estado(_reg([_sup(resultado="UNRESOLVED")])))


def test_e61_el_mismo_resultado(t):
    """E-61."""
    reg_app, ev_app = _capa("APPLICATION", "APPLICATION_CODE", "APPLICATION_CONFIGURATION")
    registro = _reg([_sup(controles=[_ctl(), reg_app["surfaces"][0]["controls"][0]]),
                     _sup(OTRA, controles=[_ctl(evidencia=list(CITAS_CTL) + ["ruta-otra"])],
                          evidencia=("publica-otra",))])
    evid = _sin("inventario", _inventario([SUP, OTRA]), _publica([OTRA], eid="publica-otra"),
                _ruta(sups=[OTRA], eid="ruta-otra"), *ev_app[2:])
    base = _json(_r(registro, evid))
    t.igual("E-61 el caso de dos superficies pasa", "PASS", json.loads(base)["state"])
    azar = random.Random(61)
    for vuelta in range(6):
        reg, ev = copy.deepcopy(registro), copy.deepcopy(evid)
        azar.shuffle(reg["surfaces"])
        azar.shuffle(ev)
        for s in reg["surfaces"]:
            azar.shuffle(s["controls"])
            azar.shuffle(s["evidence"])
            for c in s["controls"]:
                azar.shuffle(c["evidence"])
        t.igual("E-61 desordenado %d" % vuelta, base, _json(_r(reg, ev)))
    t.igual("E-61 los trece estados", sorted(LOS_13), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "búsqueda") for f in ("NFC", "NFD"))
    t.igual("E-61 una superficie en NFD es la del inventario en NFC", "PASS",
            _estado(_reg([_sup(nfd)]), _sin("inventario", "publica", "ruta", _inventario([nfc]),
                                            _publica([nfc]), _ruta(sups=[nfc]))))
    t.igual("E-61 citar en NFD una evidencia en NFC es citarla", "PASS",
            _estado(_reg([_sup(controles=[_ctl(evidencia=["cuota", nfd, "excesivo", "automatizado",
                                                          "capacidad"])])]),
                    _sin("ruta", _ruta(eid=nfc))))
    gemelas = _r(evidencia=EVIDENCIA + [_ruta(eid=nfc), _ruta(eid=nfd)])
    t.verdadero("E-61 dos ids iguales en NFC son un id repetido", any(nfc in i for i in gemelas["issues"]))
    t.igual("E-61 dos superficies iguales en NFC son la misma, repetida", [nfc],
            _r(_reg([_sup(nfc), _sup(nfd)]))["coverage"]["duplicatedSurfaces"])
    for nombre, raro in (("una lista", ["x"]), ("un numero", 7), ("un dict", {"a": 1})):
        ev = EVIDENCIA + [{"evidenceId": raro, "sourceType": "NETWORK_TOPOLOGY", "reference": "x",
                           "establishes": ["PATH_BINDING"], "surfaces": [SUP], "value": "BYPASS_PRESENT"}]
        t.igual("E-61 un id que es %s no levanta" % nombre, COBERTURA,
                _sin_excepcion(lambda: _estado(evidencia=ev)))


def test_e62_la_trazabilidad(t):
    """E-62."""
    caminos = {"vacio": CHECK.evaluar({}), "pasa": _r(), "falla": _r(_reg([_sup(controles=[])])),
               "insegura": _insegura(environment="PRD"),
               "no aplica": CHECK.evaluar({"evidence": [_publica(valor="ABSENT",
                                                                 fuente="SECURITY_DOCUMENTATION")]}),
               "registro invalido": CHECK.evaluar({"registry": {"surfaces": 1}})}
    for nombre, r in caminos.items():
        t.igual("E-62 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-62 %s la clave" % nombre, "ES0902.Vu9", r["ruleKey"])
        t.igual("E-62 %s el control" % nombre, "public-interface-abuse-protection", r["control"])
    vu9 = _unidad(_r())
    t.igual("E-62 la unidad lleva Vu9 en PASS", "PASS", vu9["result"])
    t.igual("E-62 aplicable", "APPLICABLE", vu9["applicability"])
    t.igual("E-62 con sus superficies", [SUP], vu9["surfaces"])
    t.igual("E-62 y su evidencia por id", ["automatizado", "capacidad", "cuota", "excesivo", "ruta"],
            vu9["evidence"])
    t.igual("E-62 y nada mas", ["applicability", "evidence", "result", "source", "surfaces"], sorted(vu9))
    t.igual("E-62 con la fuente", TRAZA, vu9["source"])
    t.igual("E-62 sin la senal, la unidad dice sin resolver", "UNRESOLVED", _unidad(_r(), None)["result"])
    t.igual("E-62 con la senal en FALSE, no aplica", "NOT_APPLICABLE", _unidad(_r(), False)["result"])
    t.igual("E-62 un resultado ajeno no se proyecta", "UNRESOLVED",
            _unidad(dict(_r(), control="otro-control"))["result"])
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = _unidad(_r())
    finally:
        normativa._ruta_de_evidencia = original
    t.igual("E-62 sin la lib la unidad se arma, con el estado y sin ids", ("PASS", [], []),
            (sin_lib["result"], sin_lib["surfaces"], sin_lib["evidence"]))
    ev, _ = CHECK.para_seguridad(_r())
    ids = ev["controlResults"][CHECK.CONTROL]["evidence"]
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK", "evidence": ids})
    t.igual("E-62 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])
