# ES0902 §6 Vu2: ningun dato sensible en texto plano, salto por salto y con evidencia.
#
# Escenarios E-01 a E-44 de docs/cambios/es0902-vu2-datos-sensibles-en-transito/spec.md.
#
# 🔴 CAMINO es el caso que APRUEBA -navegador a ingreso, ingreso a backend, backend a proveedor,
# los tres protegidos con evidencia- y casi todo este archivo sale de romperlo. E-17 lo mira en
# PASS: si dejara de aprobar, los escenarios que lo rompen seguirian en verde sin probar nada.
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

RUTA_CHECK = CONTROLES / "checks" / "sensitive-data-transport-protection.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu2_transito")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu2"}
LOS_10 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
          "SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED", "TRANSMISSION_PATH_COVERAGE_UNRESOLVED",
          "TRANSPORT_PROTECTION_UNRESOLVED", "PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED",
          "SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
ALCANCE = "tramites"
EN_CLARO = "PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED"
SIN_PROT = "TRANSPORT_PROTECTION_UNRESOLVED"
SIN_CLAS = "SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED"
SIN_COB = "TRANSMISSION_PATH_COVERAGE_UNRESOLVED"
INSEGURA = "SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE"


def _ev(eid, fuente, establece, targets, valor=None, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece], "scope": ALCANCE, "targets": list(targets)}
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _hop(de, a, transporte="https", estado="PROTECTED", evidencia=None, **extra):
    base = {"from": de, "to": a, "transport": transporte, "protectionStatus": estado,
            "evidence": list(evidencia if evidencia is not None else ["t-%s-%s" % (de, a)])}
    base.update(extra)
    return base


def _prot(de, a, pid="alta", fuente="DEPLOYMENT_CONFIGURATION", valor="PROTECTED", eid=None,
          **extra):
    return _ev(eid or "t-%s-%s" % (de, a), fuente, "TRANSPORT_CONFIDENTIALITY", [pid], valor,
               hop="%s->%s" % (de, a), **extra)


CLASE = {"dataClassId": "datos-personales", "description": "nombre y documento del vecino",
         "classification": "SENSITIVE", "classificationEvidence": ["clas"]}
SALTOS = [_hop("navegador", "ingreso"), _hop("ingreso", "backend"), _hop("backend", "proveedor")]
CAMINO = {"pathId": "alta", "scope": ALCANCE, "dataClassRefs": ["datos-personales"],
          "hops": SALTOS, "evidence": []}
EVIDENCIA = [
    _ev("clas", "GCBA_DATA_CLASSIFICATION_POLICY", "DATA_CLASSIFICATION", ["datos-personales"],
        "SENSITIVE"),
    _prot("navegador", "ingreso"), _prot("ingreso", "backend"), _prot("backend", "proveedor"),
]


def _inv(clases=None, caminos=None):
    return {"version": "1.0", "dataClasses": copy.deepcopy([CLASE] if clases is None else clases),
            "paths": copy.deepcopy([CAMINO] if caminos is None else caminos)}


def _caso(clases=None, caminos=None, evidencia=None, detectados=None, alcance=ALCANCE):
    caso = {"scope": alcance, "inventory": _inv(clases, caminos),
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}
    if detectados is not None:
        caso["detectedPaths"] = detectados
    return caso


def _r(*a, senal=None, **k):
    return CHECK.evaluar(_caso(*a, **k), senal)


def _estado(*a, **k):
    return _r(*a, **k)["state"]


def _camino(saltos, pid="alta", **extra):
    base = dict(copy.deepcopy(CAMINO), pathId=pid, hops=copy.deepcopy(saltos))
    base.update(extra)
    return base


def _con_salto(i, **cambios):
    """El camino base, con el salto i cambiado."""
    saltos = copy.deepcopy(SALTOS)
    saltos[i].update(cambios)
    return [_camino(saltos)]


def _pc(r, pid="alta"):
    return [p for p in r["paths"] if p["pathId"] == pid][0]


def _salto(r, i, pid="alta"):
    return _pc(r, pid)["hops"][i]


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


def _claves(dato):
    if isinstance(dato, dict):
        return list(dato.keys()) + [k for v in dato.values() for k in _claves(v)]
    if isinstance(dato, list):
        return [k for v in dato for k in _claves(v)]
    return []


# -- La fila ------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01."""
    t.igual("E-01 la fila", "ES0902.Vu2", seguridad.regla("Vu2", MATRIZ)["ruleKey"])
    t.igual("E-01 el resultado", "ES0902.Vu2", _r()["ruleKey"])
    t.igual("E-01 la regla", "Vu2", _r()["rule"])


def test_e02_la_senal(t):
    """E-02."""
    t.igual("E-02 la fila", ["sensitiveDataTransmissionPresent"],
            seguridad.regla("Vu2", MATRIZ)["applicability"]["signals"])
    t.igual("E-02 el check", "sensitiveDataTransmissionPresent", CHECK.SENAL)
    t.igual("E-02 la produce", "sensitiveDataTransmissionPresent",
            CHECK.senal(_caso())["signalId"])


def test_e03_los_ids(t):
    """E-03."""
    vu2 = seguridad.regla("Vu2", MATRIZ)
    t.igual("E-03 el agente", ["dev-security"], vu2["primaryAgents"])
    t.igual("E-03 la policy", ["sensitive-data-plaintext-transmission-prohibited"], vu2["policies"])
    t.igual("E-03 el check", ["sensitive-data-transport-protection"], vu2["checks"])
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("sensitive-data-plaintext-transmission-prohibited", "POLICY",
             "controles/policies/sensitive-data-plaintext-transmission-prohibited.md"),
            ("sensitive-data-transport-protection", "CHECK",
             "controles/checks/sensitive-data-transport-protection.py")):
        t.igual("E-03 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-03 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-03 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.verdadero("E-03 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    t.igual("E-03 el modulo", "sensitive-data-transport-protection", CHECK.CONTROL)
    t.igual("E-03 su policy", "sensitive-data-plaintext-transmission-prohibited", CHECK.POLICY)
    t.contiene("E-03 la policy declara su id", "id: sensitive-data-plaintext-transmission-prohibited",
               (CONTROLES / "policies" / "sensitive-data-plaintext-transmission-prohibited.md")
               .read_text(encoding="utf-8"))


def test_e04_nada_nuevo(t):
    """E-04."""
    registro = c_reg.cargar()
    t.igual("E-04 diez agentes", 10, len(registro["agents"]))
    por_id = {a["id"]: a for a in registro["agents"]}
    t.igual("E-04 las skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in por_id["dev-security"].get("skills") or []))
    t.igual("E-04 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-04 cero reviews", [], seguridad.regla("Vu2", MATRIZ)["reviews"])
    t.igual("E-04 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))


# -- La senal -----------------------------------------------------------------

def test_e05_la_senal_enciende_con_autoridad(t):
    """E-05."""
    doc = CHECK.senal(_caso())
    t.igual("E-05 TRUE", "TRUE", doc["value"])
    t.igual("E-05 cita el camino", ["sensitive-data-transmission.json#alta"],
            [e["reference"] for e in doc["evidence"]])
    t.igual("E-05 sin issues", [], doc["issues"])
    # 🔴 El pase 1 del refutador: la senal conserva lo que el paquete pide -la fuente de la
    # clasificacion, la clase, los saltos y el alcance-, no solo el id del camino.
    claim = doc["evidence"][0]["claim"]
    for pieza in ("datos-personales=SENSITIVE", "[clas]", "navegador->ingreso",
                  "backend->proveedor", ALCANCE):
        t.contiene("E-05 el claim conserva `%s`" % pieza, pieza, claim)
    booleanos = senales.booleanos({"sensitiveDataTransmissionPresent": doc})
    t.igual("E-05 por senales", {"sensitiveDataTransmissionPresent": True}, booleanos)
    t.igual("E-05 enciende la fila", "APPLICABLE",
            seguridad.resolver_regla(seguridad.regla("Vu2", MATRIZ), booleanos)[0])
    t.igual("E-05 un registro que no valida", "UNRESOLVED",
            CHECK.senal({"scope": ALCANCE, "inventory": {"paths": 1}})["value"])
    t.igual("E-05 el instalado, vacio", "UNRESOLVED", CHECK.senal({"scope": ALCANCE})["value"])


def test_e06_un_nombre_de_campo_no_enciende(t):
    """E-06."""
    for fuente in ("FIELD_NAME_PATTERN", "README_STATEMENT", "AGENT_STATEMENT"):
        ev = [dict(EVIDENCIA[0], sourceType=fuente)] + EVIDENCIA[1:]
        doc = CHECK.senal(_caso(evidencia=ev))
        t.igual("E-06 %s no enciende" % fuente, "UNRESOLVED", doc["value"])
        t.contiene("E-06 %s: clasificacion sin resolver" % fuente, SIN_CLAS, doc["reasons"])


def _no_sensible():
    clase = dict(CLASE, classification="NOT_SENSITIVE")
    ev = [dict(EVIDENCIA[0], value="NOT_SENSITIVE")] + EVIDENCIA[1:]
    return clase, ev


def test_e07_apagar_exige_autoridad(t):
    """E-07."""
    clase, ev = _no_sensible()
    caso = _caso([clase], evidencia=ev)
    t.igual("E-07 todo no sensible con autoridad", "FALSE", CHECK.senal(caso)["value"])
    t.igual("E-07 el check no aplica", "NOT_APPLICABLE", CHECK.evaluar(caso)["state"])
    alcance = _ev("scope-ok", "ASI_POLICY", "NO_SENSITIVE_TRANSMISSION", [ALCANCE])
    vacio = _caso([], [], [alcance])
    t.igual("E-07 inventario vacio con NO_SENSITIVE_TRANSMISSION autoritativa", "FALSE",
            CHECK.senal(vacio)["value"])
    t.igual("E-07 y el check no aplica", "NOT_APPLICABLE", CHECK.evaluar(vacio)["state"])
    for fuente in ("README_STATEMENT", "AGENT_STATEMENT"):
        t.igual("E-07 %s no apaga una clase" % fuente, "UNRESOLVED",
                CHECK.senal(_caso([clase], evidencia=[dict(ev[0], sourceType=fuente)] + ev[1:]))
                ["value"])
        t.igual("E-07 %s no apaga el alcance" % fuente, "UNRESOLVED",
                CHECK.senal(_caso([], [], [dict(alcance, sourceType=fuente)]))["value"])
    t.igual("E-07 otro alcance no apaga", "UNRESOLVED",
            CHECK.senal(_caso([], [], [alcance], alcance="otro"))["value"])


def test_e08_la_ausencia_no_apaga(t):
    """E-08."""
    t.igual("E-08 inventario vacio", "UNRESOLVED", CHECK.senal(_caso([], [], []))["value"])
    escaner = _ev("esc", "SECRET_SCANNER", "NO_SENSITIVE_TRANSMISSION", [ALCANCE])
    t.igual("E-08 un escaner sin hallazgos", "UNRESOLVED",
            CHECK.senal(_caso([], [], [escaner]))["value"])
    clase, ev = _no_sensible()
    dudosa = {"dataClassId": "otra", "classification": "UNRESOLVED", "classificationEvidence": []}
    caminos = [dict(CAMINO, dataClassRefs=["datos-personales", "otra"])]
    t.igual("E-08 una clase sin resolver al lado de las no sensibles", "UNRESOLVED",
            CHECK.senal(_caso([clase, dudosa], caminos, ev))["value"])
    t.igual("E-08 un camino detectado que no esta", "UNRESOLVED",
            CHECK.senal(_caso([clase], evidencia=ev, detectados=["export-nocturno"]))["value"])


# -- La clasificacion ---------------------------------------------------------

def test_e09_sensible_sin_autoridad_no_pasa(t):
    """E-09."""
    otra = {"dataClassId": "salud", "classification": "SENSITIVE", "classificationEvidence": []}
    segundo = _camino(SALTOS, pid="turnos", dataClassRefs=["salud"])
    r = _r([CLASE, otra], [CAMINO, segundo])
    t.igual("E-09 clasificacion sin resolver", SIN_CLAS, r["state"])
    t.igual("E-09 en ese camino", SIN_CLAS, _pc(r, "turnos")["state"])


def test_e10_lo_declarado_contra_la_evidencia(t):
    """E-10."""
    contra = _ev("clas-2", "ASI_POLICY", "DATA_CLASSIFICATION", ["datos-personales"],
                 "NOT_SENSITIVE")
    for nombre, ev in (("citada", EVIDENCIA + [contra]), ("no citada", EVIDENCIA + [contra])):
        clase = dict(CLASE, classificationEvidence=["clas", "clas-2"]) if nombre == "citada" else CLASE
        d = CHECK.derivar(_caso([clase], evidencia=ev))
        t.igual("E-10 sensible contra no sensible, %s" % nombre, "UNRESOLVED",
                d["classes"]["datos-personales"]["classification"])
    clase, ev = _no_sensible()
    ev = ev + [_ev("clas-3", "ASI_POLICY", "DATA_CLASSIFICATION", ["datos-personales"],
                   "SENSITIVE")]
    t.igual("E-10 no sensible contra sensible", "UNRESOLVED",
            CHECK.derivar(_caso([clase], evidencia=ev))["classes"]["datos-personales"]
            ["classification"])


def test_e11_ninguna_taxonomia(t):
    """E-11."""
    texto = " ".join(_literales()).lower()
    for palabra in ("dni", "cuit", "cuil", "email", "telefono", "tarjeta", "card", "phone"):
        t.no_contiene("E-11 no aparece `%s`" % palabra, palabra, texto)


# -- La cobertura -------------------------------------------------------------

def test_e12_un_camino_detectado(t):
    """E-12."""
    r = _r(detectados=["export-nocturno"])
    t.igual("E-12 cobertura", SIN_COB, r["state"])
    t.igual("E-12 que lo nombra", ["export-nocturno"], r["coverage"]["missing"])


def test_e13_referencias_repetidos_y_sin_saltos(t):
    """E-13."""
    for nombre, clases, caminos in (
            ("clase que no existe", [CLASE], [dict(CAMINO, dataClassRefs=["datos-personales", "x"])]),
            ("camino repetido", [CLASE], [CAMINO, copy.deepcopy(CAMINO)]),
            ("clase repetida", [CLASE, copy.deepcopy(CLASE)], [CAMINO]),
            ("camino sin saltos", [CLASE], [CAMINO, dict(CAMINO, pathId="vacio", hops=[])])):
        t.verdadero("E-13 %s no pasa" % nombre, _estado(clases, caminos) != "PASS")
        t.contiene("E-13 %s y es cobertura o clasificacion" % nombre,
                   _estado(clases, caminos), (SIN_COB, SIN_CLAS, "APPLICABILITY_UNRESOLVED"))
    t.igual("E-13 un camino sin saltos, cobertura", SIN_COB,
            _estado([CLASE], [CAMINO, dict(CAMINO, pathId="vacio", hops=[])]))
    t.igual("E-13 un camino repetido, cobertura", SIN_COB,
            _estado([CLASE], [CAMINO, copy.deepcopy(CAMINO)]))
    t.igual("E-13 una clase que no existe, cobertura", SIN_COB,
            _estado([CLASE], [dict(CAMINO, dataClassRefs=["datos-personales", "x"])]))
    # 🔴 El pase 1 del refutador: la clase repetida se prueba por la cobertura, no solo por "no
    # pasa" -la clase queda sin resolver igual, y eso solo no prueba el escenario-.
    r = _r([CLASE, copy.deepcopy(CLASE)], [CAMINO], senal=True)
    t.igual("E-13 una clase repetida la nombra la cobertura", ["datos-personales"],
            r["coverage"]["duplicatedClasses"])
    t.igual("E-13 y deja la cobertura sin resolver", SIN_COB, r["state"])
    doble = [_hop("navegador", "ingreso"), _hop("ingreso", "ingreso"), _hop("ingreso", "ingreso")]
    r = _r(caminos=[_camino(doble)],
           evidencia=EVIDENCIA + [_prot("ingreso", "ingreso")])
    t.igual("E-13 dos saltos con el mismo from->to no se distinguen", ["alta"],
            r["coverage"]["ambiguousHops"])
    t.igual("E-13 y la cobertura no consta", SIN_COB, r["state"])
    # 🔴 El pase 2 del refutador: "la cobertura nombra cual", en los cinco casos.
    for nombre, clases, caminos, campo, esperado in (
            ("clase que no existe", [CLASE],
             [dict(CAMINO, dataClassRefs=["datos-personales", "x"])], "undefinedClassRefs", ["alta"]),
            ("camino repetido", [CLASE], [CAMINO, copy.deepcopy(CAMINO)], "duplicatedPaths",
             ["alta"]),
            ("camino sin saltos", [CLASE], [CAMINO, dict(CAMINO, pathId="vacio", hops=[])],
             "withoutHops", ["vacio"])):
        r = _r(clases, caminos)
        t.igual("E-13 %s: la cobertura lo nombra" % nombre, esperado, r["coverage"][campo])
        t.igual("E-13 %s: y es cobertura" % nombre, SIN_COB, r["state"])


def test_e14_la_cadena_entera(t):
    """E-14."""
    saltos = [_hop("navegador", "ingreso"), _hop("backend", "proveedor")]
    ev = [EVIDENCIA[0], _prot("navegador", "ingreso"), _prot("backend", "proveedor")]
    r = _r(caminos=[_camino(saltos)], evidencia=ev)
    t.igual("E-14 una cadena cortada", SIN_COB, r["state"])
    t.igual("E-14 que la nombra", ["alta"], r["coverage"]["brokenChain"])


# -- Salto por salto -----------------------------------------------------------

def test_e15_el_salto_interno_en_claro(t):
    """E-15."""
    r = _r(caminos=_con_salto(1, transport="http"))
    t.igual("E-15 FAIL", "FAIL", r["state"])
    t.contiene("E-15 en claro", EN_CLARO, r["states"])
    t.igual("E-15 el salto", "PLAINTEXT", _salto(r, 1)["state"])
    t.igual("E-15 el borde sigue protegido", "PROTECTED", _salto(r, 0)["state"])
    t.contiene("E-15 lo nombra", "ingreso->backend", _pc(r)["reason"])
    t.igual("E-15 declarado PLAINTEXT tambien", "FAIL",
            _estado(caminos=_con_salto(1, protectionStatus="PLAINTEXT"),
                    evidencia=[e for e in EVIDENCIA if e["evidenceId"] != "t-ingreso-backend"]))


def test_e16_cada_salto_solo(t):
    """E-16."""
    # Sin citar nada: si el salto citara un id que no esta, caeria por ilegible y no por lo que
    # este escenario dice.
    ev = [e for e in EVIDENCIA if e["evidenceId"] != "t-backend-proveedor"]
    r = _r(caminos=_con_salto(2, evidence=[]), evidencia=ev)
    t.igual("E-16 no pasa", SIN_PROT, r["state"])
    t.igual("E-16 y no es por evidencia ilegible", [], _pc(r)["issues"])
    t.igual("E-16 los otros dos protegidos", ["PROTECTED", "PROTECTED", "UNRESOLVED"],
            [s["state"] for s in _pc(r)["hops"]])


def test_e17_todo_protegido_pasa(t):
    """E-17."""
    r = _r()
    t.igual("E-17 PASS", "PASS", r["state"])
    t.igual("E-17 los tres", ["PROTECTED"] * 3, [s["state"] for s in _pc(r)["hops"]])


def test_e18_la_terminacion_no_cubre_lo_de_atras(t):
    """E-18."""
    borde = _prot("navegador", "ingreso", eid="t-ingreso-backend")
    ev = [e for e in EVIDENCIA if e["evidenceId"] != "t-ingreso-backend"] + [borde]
    r = _r(evidencia=ev)
    t.igual("E-18 la evidencia del borde no sostiene el interno", "UNRESOLVED",
            _salto(r, 1)["state"])
    t.igual("E-18 y no pasa", SIN_PROT, r["state"])


def test_e19_la_frontera_no_material(t):
    """E-19."""
    front = _ev("front", "ARCHITECTURE_DOCUMENTATION", "NOT_MATERIAL_BOUNDARY", ["alta"],
                hop="ingreso->backend")
    ev = EVIDENCIA + [front]
    r = _r(caminos=_con_salto(1, transport="http", evidence=["front"]), evidencia=ev)
    t.igual("E-19 el salto no se evalua", "NOT_MATERIAL_BOUNDARY", _salto(r, 1)["state"])
    t.igual("E-19 y no falla", "PASS", r["state"])
    # El paquete pide evidencia de ARQUITECTURA: la configuracion de red o un hallazgo no alcanzan.
    for fuente in ("README_STATEMENT", "NETWORK_CONFIGURATION", "OFFICIAL_ASSESSMENT_FINDING"):
        otra = dict(front, sourceType=fuente)
        t.igual("E-19 con %s, se evalua" % fuente, "FAIL",
                _estado(caminos=_con_salto(1, transport="http", evidence=["front"]),
                        evidencia=EVIDENCIA + [otra]))


# -- Que no es cifrar -----------------------------------------------------------

CODIFICACIONES = ("BASE64", "URL_ENCODING", "HEX", "COMPRESSION", "SERIALIZATION", "JWT_SIGNED",
                  "OBFUSCATION")


def test_e20_codificar_sobre_http_es_fail(t):
    """E-20."""
    for mec in CODIFICACIONES:
        t.igual("E-20 %s sobre http" % mec, "FAIL",
                _estado(caminos=_con_salto(1, transport="http", protectionMechanism=mec)))


def test_e21_codificar_sobre_lo_que_no_se_sabe(t):
    """E-21."""
    for mec in CODIFICACIONES:
        r = _r(caminos=_con_salto(1, transport=None, protectionMechanism=mec))
        t.igual("E-21 %s no es protegido" % mec, "UNRESOLVED", _salto(r, 1)["state"])
        t.igual("E-21 %s tampoco falla" % mec, SIN_PROT, r["state"])


def test_e22_un_hash_no_es_cifrar(t):
    """E-22."""
    r = _r(caminos=_con_salto(1, protectionMechanism="HASHING"))
    t.igual("E-22 no es protegido", "UNRESOLVED", _salto(r, 1)["state"])
    t.igual("E-22 y solo no es FAIL", SIN_PROT, r["state"])


def test_e23_cifrado_de_aplicacion_sobre_http(t):
    """E-23."""
    r = _r(caminos=_con_salto(1, transport="http",
                              protectionMechanism="APPLICATION_LEVEL_ENCRYPTION"))
    t.igual("E-23 protegido", "PROTECTED", _salto(r, 1)["state"])
    t.igual("E-23 y pasa", "PASS", r["state"])
    ev = [e for e in EVIDENCIA if e["evidenceId"] != "t-ingreso-backend"]
    t.igual("E-23 sin evidencia, en claro", "FAIL",
            _estado(caminos=_con_salto(1, transport="http",
                                       protectionMechanism="APPLICATION_LEVEL_ENCRYPTION"),
                    evidencia=ev))


# -- https no es prueba -------------------------------------------------------

def _sin(eid, *mas):
    return [e for e in EVIDENCIA if e["evidenceId"] != eid] + list(mas)


def test_e24_la_forma_de_la_url(t):
    """E-24."""
    url = _prot("ingreso", "backend", fuente="URL_SCHEME")
    t.igual("E-24 sin resolver", "UNRESOLVED",
            _salto(_r(evidencia=_sin("t-ingreso-backend", url)), 1)["state"])


def test_e25_protegido_contra_en_claro(t):
    """E-25."""
    claro = _prot("ingreso", "backend", valor="PLAINTEXT", eid="cap")
    citada = _con_salto(1, evidence=["t-ingreso-backend", "cap"])
    t.igual("E-25 citada es FAIL", "FAIL", _estado(caminos=citada, evidencia=EVIDENCIA + [claro]))
    r = _r(evidencia=EVIDENCIA + [claro])
    t.igual("E-25 no citada queda sin resolver", "UNRESOLVED", _salto(r, 1)["state"])
    t.igual("E-25 y no es FAIL", SIN_PROT, r["state"])
    declarado = _con_salto(1, protectionStatus="PLAINTEXT")
    r = _r(caminos=declarado)
    t.igual("E-25 PLAINTEXT declarado contra PROTECTED", "UNRESOLVED", _salto(r, 1)["state"])
    # 🔴 Fuera de la letra del pase 1: un "en claro" citado que no se confirmo no se descarta.
    pendiente = dict(claro, outcome="PENDING")
    r = _r(caminos=citada, evidencia=EVIDENCIA + [pendiente])
    t.igual("E-25 un en claro sin confirmar impide el PASS", SIN_PROT, r["state"])


def test_e26_validacion_apagada(t):
    """E-26."""
    for campo in ("certificateValidation", "hostnameVerification"):
        r = _r(caminos=_con_salto(1, **{campo: "DISABLED"}))
        t.igual("E-26 %s apagada no pasa" % campo, SIN_PROT, r["state"])
        for valor in ("UNRESOLVED", "NOT_APPLICABLE", "ENABLED"):
            t.igual("E-26 %s en %s no bloquea" % (campo, valor), "PASS",
                    _estado(caminos=_con_salto(1, **{campo: valor})))
    t.igual("E-26 ausente no bloquea", "PASS", _estado())


def test_e27_el_codigo_fuente_solo(t):
    """E-27."""
    codigo = _prot("ingreso", "backend", fuente="SOURCE_CODE")
    t.igual("E-27 sin resolver", "UNRESOLVED",
            _salto(_r(evidencia=_sin("t-ingreso-backend", codigo)), 1)["state"])


# -- Nada inventado -------------------------------------------------------------

def test_e28_nada_criptografico(t):
    """E-28."""
    texto = (" ".join(_literales()) + " " + " ".join(_claves(_r()))).lower()
    for palabra in ("tls1", "tlsv", "tls_1", "cipher", "suite", "keysize", "key_size", "mtls",
                    "mutual", "rotation", "rsa", "ecdsa", "aes"):
        t.no_contiene("E-28 no aparece `%s`" % palabra, palabra, texto)


def test_e29_ningun_numero(t):
    """E-29."""
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.verdadero("E-29 solo 0 o 1: %s" % numeros, set(numeros) <= {0, 1})


# -- La prueba ------------------------------------------------------------------

PRUEBA = dict(syntheticData=True, authorized=True, payloadCaptured=False, outcome="CONFIRMED")


def _prueba(**cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _prot("ingreso", "backend", fuente="AUTHORIZED_SYNTHETIC_TEST", **datos)


def test_e30_la_prueba_sintetica(t):
    """E-30."""
    r = _r(evidencia=_sin("t-ingreso-backend", _prueba()))
    t.igual("E-30 sostiene el salto", "PROTECTED", _salto(r, 1)["state"])
    t.igual("E-30 y pasa", "PASS", r["state"])


def test_e31_la_prueba_insegura(t):
    """E-31."""
    for nombre, cambios in (("con datos reales", {"syntheticData": False}),
                            ("sin declarar sinteticos", {"syntheticData": None}),
                            ("con el payload capturado", {"payloadCaptured": True}),
                            ("sin autorizacion", {"authorized": False})):
        r = _r(evidencia=_sin("t-ingreso-backend", _prueba(**cambios)))
        t.igual("E-31 %s" % nombre, INSEGURA, r["state"])
        claro = _prueba(value="PLAINTEXT", **cambios)
        r = _r(caminos=_con_salto(1, evidence=["t-ingreso-backend"]),
               evidencia=_sin("t-ingreso-backend", claro))
        t.igual("E-31 %s que dice en claro no es FAIL" % nombre, INSEGURA, r["state"])


def test_e32_sin_objetivo(t):
    """E-32."""
    r = _r(evidencia=_sin("t-ingreso-backend", _prueba(outcome="UNAVAILABLE")))
    t.igual("E-32 sin objetivo", "TEST_TARGET_UNAVAILABLE", r["state"])
    # 🔴 El pase 1 del refutador: el "no es FAIL" se prueba con una prueba que dice EN CLARO. Con
    # una que dice protegido no hay FAIL posible.
    for nombre, cambios in (("sin objetivo", {"outcome": "UNAVAILABLE"}),
                            ("sin objetivo e insegura", {"outcome": "UNAVAILABLE",
                                                         "syntheticData": False})):
        claro = _prueba(value="PLAINTEXT", **cambios)
        r = _r(evidencia=_sin("t-ingreso-backend", claro))
        t.igual("E-32 %s que dice en claro no es FAIL" % nombre, "TEST_TARGET_UNAVAILABLE",
                r["state"])


def test_e33_no_ejecuta_nada(t):
    """E-33."""
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-33 ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing"}))
    usos = sorted({"%s.%s" % (n.value.id, n.attr) for n in ast.walk(_arbol())
                   if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                   and n.value.id == "os"})
    t.igual("E-33 de os solo rutas", ["os.path"], usos)
    escrituras = [n for n in ast.walk(_arbol()) if isinstance(n, ast.Call)
                  and any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                          and a.value[:1] in ("w", "a", "x") and len(a.value) <= 3
                          for a in n.args[1:2])]
    t.igual("E-33 no abre nada para escribir", 0, len(escrituras))


# -- La evidencia y los secretos --------------------------------------------------

def test_e34_el_registro_vacio(t):
    """E-34."""
    instalado = json.loads((REGLAS / "sensitive-data-transmission.json").read_text(encoding="utf-8"))
    t.igual("E-34 vacio", ([], []), (instalado["dataClasses"], instalado["paths"]))
    t.igual("E-34 valida", [], CHECK.validar_schema(instalado))
    for nombre, doc in (
            ("arriba", dict(_inv(), extra=1)),
            ("en la clase", _inv([dict(CLASE, extra=1)])),
            ("en el camino", _inv(caminos=[dict(CAMINO, extra=1)])),
            ("en el salto", _inv(caminos=_con_salto(0, extra=1)))):
        t.verdadero("E-34 rechaza una clave de mas %s" % nombre, bool(CHECK.validar_schema(doc)))
    t.igual("E-34 senal en TRUE y registro vacio: cobertura", SIN_COB,
            CHECK.evaluar({"scope": ALCANCE}, True)["state"])


def test_e35_el_catalogo_cerrado(t):
    """E-35."""
    for campo in ("payload", "sample"):
        con = dict(EVIDENCIA[3], **{campo: "valor"})
        ev = [e for e in EVIDENCIA if e["evidenceId"] != con["evidenceId"]] + [con]
        r = _r(evidencia=ev)
        t.igual("E-35 `%s` no cuenta" % campo, "UNRESOLVED", _salto(r, 2)["state"])
        t.igual("E-35 `%s` y bloquea el PASS" % campo, SIN_PROT, r["state"])
        t.no_contiene("E-35 `%s` y no sale" % campo, '"valor"', json.dumps(r))


def test_e36_ningun_secreto_sale(t):
    """E-36."""
    for texto in ("app:password=hunter2abc", "env/DB_PASSWORD=hunter2abc", "token=hunter2abc",
                  "Bearer abcdefghijkhunter2abc", "https://u:hunter2abc@x.example"):
        casos = {
            "un pathId": _r(caminos=[_camino(SALTOS, pid=texto)],
                            evidencia=[EVIDENCIA[0]] + [dict(e, targets=[texto])
                                                        for e in EVIDENCIA[1:]]),
            "un dataClassId": _r([dict(CLASE, dataClassId=texto)],
                                 [dict(CAMINO, dataClassRefs=[texto])]),
            "un transporte": _r(caminos=_con_salto(1, transport=texto)),
            "un mecanismo": _r(caminos=_con_salto(1, protectionMechanism=texto)),
            "un camino detectado": _r(detectados=[texto]),
            "un id de evidencia": _r(evidencia=EVIDENCIA + [dict(EVIDENCIA[1], evidenceId=texto)]),
            "la senal": CHECK.senal(_caso(caminos=[_camino(SALTOS, pid=texto)])),
            "un error de schema": _r([dict(CLASE, classification=texto)]),
        }
        for nombre, r in casos.items():
            t.no_contiene("E-36 `%s` en %s no sale" % (texto, nombre), "hunter2abc",
                          json.dumps(r))
    for texto in ("arn:aws:secretsmanager:us-east-1:123:secret:vu2-qa", "tokenLifespan=300",
                  "passwordPolicy: length(12)"):
        t.verdadero("E-36 `%s` no es un secreto" % texto, not CHECK.es_secreto(texto))
    # 🔴 El pase 1 del refutador: el prefijo `arn:` no exime el texto entero.
    for texto in ("arn:password=hunter2abc", "arn:aws:iam::1:user/password=hunter2abc",
                  "arn:aws:secretsmanager:us-east-1:123:secret:x/token=hunter2abc"):
        t.verdadero("E-36 `%s` es un secreto" % texto, CHECK.es_secreto(texto))
        for nombre, r in (("un pathId", _r(caminos=[_camino(SALTOS, pid=texto)])),
                          ("un transporte", _r(caminos=_con_salto(1, transport=texto))),
                          ("un camino detectado", _r(detectados=[texto])),
                          ("un id de evidencia citado", _r(
                              caminos=_con_salto(1, evidence=[texto]),
                              evidencia=_sin("t-ingreso-backend",
                                             dict(EVIDENCIA[2], evidenceId=texto))))):
            t.no_contiene("E-36 `%s` en %s no sale" % (texto, nombre), "hunter2abc",
                          json.dumps(r))
    t.no_contiene("E-36 la description no sale", CLASE["description"], json.dumps(_r()))


def test_e37_lo_ilegible_sobre_el_camino(t):
    """E-37."""
    claro = _prot("ingreso", "backend", valor="PLAINTEXT", eid="off")
    for nombre, extra in (("repetida", [claro, copy.deepcopy(claro)]),
                          ("mal formada", [dict(claro, outcome=["CONFIRMED"])]),
                          ("con targets como texto", [dict(claro, targets="alta")])):
        r = _r(evidencia=EVIDENCIA + extra)
        t.igual("E-37 %s no citada bloquea" % nombre, SIN_PROT, r["state"])
        cit = _r(caminos=_con_salto(1, evidence=["t-ingreso-backend", "off"]),
                 evidencia=EVIDENCIA + extra)
        t.igual("E-37 %s citada bloquea" % nombre, SIN_PROT, cit["state"])
    for pid in ("trámites-alta", 'al"ta'):
        ev = [EVIDENCIA[0]] + [dict(e, targets=[pid]) for e in EVIDENCIA[1:]]
        ev.append(dict(claro, targets=[pid], outcome=["CONFIRMED"]))
        r = _r(caminos=[_camino(SALTOS, pid=pid)], evidencia=ev)
        t.igual("E-37 `%s` tambien bloquea" % pid, SIN_PROT, r["state"])
    # Fuera de la letra del pase 1: NFC y NFD son el mismo id.
    import unicodedata
    nfc, nfd = (unicodedata.normalize(f, "trámites-alta") for f in ("NFC", "NFD"))
    ev = [EVIDENCIA[0]] + [dict(e, targets=[nfc]) for e in EVIDENCIA[1:]]
    ev.append(dict(claro, targets=[nfd], outcome=["CONFIRMED"]))
    t.igual("E-37 un id en NFD bloquea al mismo en NFC", SIN_PROT,
            _estado(caminos=[_camino(SALTOS, pid=nfc)], evidencia=ev))
    otro = dict(claro, targets=["alta-v2"], outcome=["CONFIRMED"])
    t.igual("E-37 una sobre otro camino que contiene el id no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [otro]))


# -- Los limites ------------------------------------------------------------------

def test_e38_vu2_no_es_otras_reglas(t):
    """E-38."""
    mios = ("sensitive-data-plaintext-transmission-prohibited", "sensitive-data-transport-protection")
    ev = {"controlResults": {c: {"result": "PASS", "evidence": ["vu2"]} for c in mios}}
    t.igual("E-38 Vu2 cumple con sus dos", "COMPLIANT",
            seguridad.resultado("Vu2", ev, {"sensitiveDataTransmissionPresent": True},
                                MATRIZ)["result"])
    for regla, senal in (("Vu7", {}), ("C1", {"authenticationPresent": True})):
        t.verdadero("E-38 y %s no" % regla,
                    seguridad.resultado(regla, ev, senal, MATRIZ)["result"] != "COMPLIANT")
    ajenos = {}
    for regla in ("Vu7", "C1"):
        fila = seguridad.regla(regla, MATRIZ)
        ajenos.update({c: {"result": "PASS", "evidence": [regla]}
                       for c in fila["policies"] + fila["checks"]})
    ajenos.update({c: {"result": "PASS", "evidence": ["d8"]}
                   for c in ("service-token-protection", "service-token-protection-required")})
    t.igual("E-38 con los de ellas en PASS Vu2 no cumple", "UNRESOLVED",
            seguridad.resultado("Vu2", {"controlResults": ajenos},
                                {"sensitiveDataTransmissionPresent": True}, MATRIZ)["result"])
    t.igual("E-38 evaluar no recibe resultados de otras reglas", ["caso", "senal", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    # 🔴 El pase 1 del refutador: D8 es de ES0901, que no tiene resultado de regla. La
    # independencia se prueba por su fila: no declara ninguno de los controles de Vu2, y sus
    # controles no son los de Vu2.
    from orquestacion import matriz as c_matriz
    d8 = c_matriz.regla("D8")
    t.igual("E-38 la fila de D8 no declara controles de Vu2", [],
            sorted(set(d8["policies"] + d8["checks"]) & set(mios)))
    t.igual("E-38 y la de Vu2 no declara los de D8", [],
            sorted(set(seguridad.regla("Vu2", MATRIZ)["policies"]
                       + seguridad.regla("Vu2", MATRIZ)["checks"])
                   & set(d8["policies"] + d8["checks"])))


def test_e39_no_nombra_otros_controles(t):
    """E-39."""
    ajenos = set()
    for regla in ("Vu7", "C1", "Vu1"):
        fila = seguridad.regla(regla, MATRIZ)
        ajenos |= set(fila["policies"] + fila["checks"])
    ajenos |= {"service-token-protection", "service-token-protection-required"}
    t.igual("E-39 ningun literal los nombra", [],
            sorted(l for l in _literales() for a in ajenos if a in l))


# -- El agregado -------------------------------------------------------------------

def _otro_camino(pid="turnos"):
    saltos = [_hop("app", "cola", evidencia=["t-%s" % pid])]
    return (_camino(saltos, pid=pid),
            _ev("t-%s" % pid, "NETWORK_CONFIGURATION", "TRANSPORT_CONFIDENTIALITY", [pid],
                "PROTECTED", hop="app->cola"))


def test_e40_uno_en_fail(t):
    """E-40."""
    otro, ev = _otro_camino()
    r = _r(caminos=_con_salto(1, transport="http") + [otro], evidencia=EVIDENCIA + [ev])
    t.igual("E-40 FAIL", "FAIL", r["state"])
    t.igual("E-40 aunque el otro pase", "PASS", _pc(r, "turnos")["state"])


def test_e41_uno_sin_resolver(t):
    """E-41."""
    otro, _ = _otro_camino()
    r = _r(caminos=[CAMINO, otro])
    t.igual("E-41 no pasa", SIN_PROT, r["state"])
    t.igual("E-41 el bueno pasa", "PASS", _pc(r)["state"])


def test_e42_lo_no_sensible_no_se_evalua(t):
    """E-42."""
    libre = {"dataClassId": "catalogo-publico", "classification": "NOT_SENSITIVE",
             "classificationEvidence": ["pub"]}
    pub = _ev("pub", "ASI_POLICY", "DATA_CLASSIFICATION", ["catalogo-publico"], "NOT_SENSITIVE")
    abierto = _camino([_hop("app", "cdn", transport="http", estado="PLAINTEXT", evidencia=[])],
                      pid="publico", dataClassRefs=["catalogo-publico"])
    r = _r([CLASE, libre], [CAMINO, abierto], EVIDENCIA + [pub])
    t.igual("E-42 pasa", "PASS", r["state"])
    t.igual("E-42 el publico no se evalua", "NOT_APPLICABLE", _pc(r, "publico")["state"])


def test_e43_el_mismo_resultado(t):
    """E-43."""
    otro, ev = _otro_camino()
    libre = {"dataClassId": "catalogo-publico", "classification": "NOT_SENSITIVE",
             "classificationEvidence": ["pub"]}
    pub = _ev("pub", "ASI_POLICY", "DATA_CLASSIFICATION", ["catalogo-publico"], "NOT_SENSITIVE")
    clases = [CLASE, libre]
    # Con dos clases en el camino: con una sola, desordenar las referencias no cambia nada.
    caminos = _con_salto(2, transport=None) + [otro]
    caminos[0]["dataClassRefs"] = ["datos-personales", "catalogo-publico"]
    evid = EVIDENCIA + [ev, pub, copy.deepcopy(ev)]
    base = json.dumps(_r(clases, caminos, evid), sort_keys=True)
    t.igual("E-43 dos corridas", base, json.dumps(_r(clases, caminos, evid), sort_keys=True))
    azar = random.Random(43)
    for vuelta in range(6):
        c, p, e = copy.deepcopy(clases), copy.deepcopy(caminos), copy.deepcopy(evid)
        azar.shuffle(c)
        azar.shuffle(p)
        azar.shuffle(e)
        for x in p:
            azar.shuffle(x["dataClassRefs"])
            for s in x["hops"]:
                azar.shuffle(s["evidence"])
        t.igual("E-43 desordenado %d" % vuelta, base, json.dumps(_r(c, p, e), sort_keys=True))
    t.igual("E-43 los diez estados", sorted(LOS_10), sorted(CHECK.ESTADOS))


def test_e44_la_trazabilidad(t):
    """E-44."""
    caminos = {
        "sin senal": CHECK.evaluar({"scope": ALCANCE}),
        "no aplica": CHECK.evaluar(_caso([], [], [_ev("s", "ASI_POLICY",
                                                       "NO_SENSITIVE_TRANSMISSION", [ALCANCE])])),
        "pasa": _r(), "falla": _r(caminos=_con_salto(1, transport="http")),
        "cobertura": _r(detectados=["x"]),
        "registro invalido": CHECK.evaluar({"scope": ALCANCE, "inventory": {"paths": 1}}, True),
        "insegura": _r(evidencia=_sin("t-ingreso-backend", _prueba(syntheticData=False))),
    }
    for nombre, r in caminos.items():
        t.igual("E-44 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-44 %s la clave" % nombre, "ES0902.Vu2", r["ruleKey"])
    bloque = normativa.resolucion({"sensitiveDataTransmissionPresent": True})["standards"]["ES0902"]
    t.igual("E-44 la unidad cita ES0902 6.2", ("ES0902", "6.2"),
            (bloque["standard"]["id"], bloque["standard"]["version"]))
    t.verdadero("E-44 Vu2 aplicable", "Vu2" in bloque["applicableRules"])
    t.verdadero("E-44 su check", "sensitive-data-transport-protection" in bloque["declaredChecks"])
    t.igual("E-44 la trazabilidad", "ES0902.Vu2", seguridad.trazabilidad("Vu2", MATRIZ)["ruleKey"])


# -- Redirect y downgrade -----------------------------------------------------------

def test_e45_un_redirect_que_expone_el_payload(t):
    """E-45 — agregado por el pase 1 del refutador: el paquete lo pide y la spec no lo tenia."""
    baja = _ev("baja", "RUNTIME_TRANSPORT_CONFIGURATION", "REDIRECT_DOWNGRADE", ["alta"],
               "EXPOSES_PAYLOAD", hop="navegador->ingreso")
    citada = _con_salto(0, evidence=["t-navegador-ingreso", "baja"])
    r = _r(caminos=citada, evidencia=EVIDENCIA + [baja])
    t.igual("E-45 citado es FAIL", "FAIL", r["state"])
    t.igual("E-45 en el salto del borde", "PLAINTEXT", _salto(r, 0)["state"])
    r = _r(evidencia=EVIDENCIA + [baja])
    t.igual("E-45 no citado impide el PASS sin hacer FAIL", SIN_PROT, r["state"])
    t.igual("E-45 una fuente debil no cuenta", "PASS",
            _estado(caminos=citada, evidencia=EVIDENCIA + [dict(baja, sourceType="README_STATEMENT")]))


# -- La regla del pase 2: todo id se compara igual ---------------------------------------

NFC, NFD = (unicodedata.normalize(f, "trámites-alta") for f in ("NFC", "NFD"))


def _en_nfc(targets_nfd=True):
    """El camino base con el id en NFC; la evidencia nombra el camino en NFD si se pide."""
    otro = NFD if targets_nfd else NFC
    ev = [EVIDENCIA[0]] + [dict(e, targets=[NFC]) for e in EVIDENCIA[1:]]
    return [_camino(SALTOS, pid=NFC)], ev, otro


def test_e46_la_misma_regla_para_todo_id(t):
    """E-46 — agregado por el pase 2 del refutador (E-10, E-25 y E-45 caian por la misma causa)."""
    caminos, ev, nfd = _en_nfc()
    claro = _prot("ingreso", "backend", pid=nfd, valor="PLAINTEXT", eid="cap")
    citado = copy.deepcopy(caminos)
    citado[0]["hops"][1]["evidence"] = ["t-ingreso-backend", "cap"]
    t.igual("E-46 (E-25) un en claro legible en NFD, citado, es FAIL", "FAIL",
            _estado(caminos=citado, evidencia=ev + [claro]))
    t.igual("E-46 (E-25) y no citado impide el PASS", SIN_PROT,
            _estado(caminos=caminos, evidencia=ev + [claro]))
    baja = _ev("baja", "RUNTIME_TRANSPORT_CONFIGURATION", "REDIRECT_DOWNGRADE", [nfd],
               "EXPOSES_PAYLOAD", hop="navegador->ingreso")
    t.igual("E-46 (E-45) un redirect en NFD no citado impide el PASS", SIN_PROT,
            _estado(caminos=caminos, evidencia=ev + [baja]))
    senal_nfc = unicodedata.normalize("NFC", "ingreso->señal")
    senal_nfd = unicodedata.normalize("NFD", "ingreso->señal")
    saltos = [_hop("navegador", "ingreso"), _hop("ingreso", unicodedata.normalize("NFC", "señal"),
                                                evidencia=["t-s"])]
    ev2 = [EVIDENCIA[0], _prot("navegador", "ingreso"),
           _ev("t-s", "DEPLOYMENT_CONFIGURATION", "TRANSPORT_CONFIDENTIALITY", ["alta"], "PROTECTED",
               hop=senal_nfc)]
    t.igual("E-46 el caso con acentos en el salto pasa", "PASS",
            _estado(caminos=[_camino(saltos)], evidencia=ev2))
    hop_nfd = _ev("off", "DEPLOYMENT_CONFIGURATION", "TRANSPORT_CONFIDENTIALITY", ["alta"],
                  "PLAINTEXT", hop=senal_nfd)
    t.igual("E-46 (E-25) un en claro con el hop en NFD impide el PASS", SIN_PROT,
            _estado(caminos=[_camino(saltos)], evidencia=ev2 + [hop_nfd]))
    salud = unicodedata.normalize("NFC", "salúd")
    clase = {"dataClassId": salud, "classification": "NOT_SENSITIVE",
             "classificationEvidence": ["c1"]}
    ev3 = [_ev("c1", "ASI_POLICY", "DATA_CLASSIFICATION", [salud], "NOT_SENSITIVE"),
           _ev("c2", "ASI_POLICY", "DATA_CLASSIFICATION", [unicodedata.normalize("NFD", salud)],
               "SENSITIVE")] + EVIDENCIA[1:]
    d = CHECK.derivar(_caso([clase], [dict(CAMINO, dataClassRefs=[salud])], ev3))
    t.igual("E-46 (E-10) una clasificacion contraria en NFD deja la clase sin resolver",
            "UNRESOLVED", d["classes"][salud]["classification"])
    t.igual("E-46 (E-10) y la senal no se apaga", "UNRESOLVED", d["value"])
    ref_nfd = dict(CAMINO, dataClassRefs=[unicodedata.normalize("NFD", "datos-persónales")])
    clase_nfc = dict(CLASE, dataClassId=unicodedata.normalize("NFC", "datos-persónales"))
    ev4 = [dict(EVIDENCIA[0], targets=[clase_nfc["dataClassId"]])] + EVIDENCIA[1:]
    t.igual("E-46 una referencia a la clase en NFD es la misma clase", "PASS",
            _estado([clase_nfc], [ref_nfd], ev4))


def test_e47_un_no_que_no_dice_de_que_salto_habla(t):
    """E-47 — fuera de la letra del pase 2: un en claro o un redirect sin `hop`, con un `hop` que
    el camino no tiene o sin `value`, no se descarta: impide el PASS y no hace FAIL."""
    for nombre, cambios in (("sin hop", {"hop": None}), ("con otro hop", {"hop": "x->y"}),
                            ("sin value", {"value": None})):
        for dim, valor in (("REDIRECT_DOWNGRADE", "EXPOSES_PAYLOAD"),
                           ("TRANSPORT_CONFIDENTIALITY", "PLAINTEXT")):
            e = _ev("suelta", "RUNTIME_TRANSPORT_CONFIGURATION", dim, ["alta"], valor,
                    hop="ingreso->backend")
            e.update(cambios)
            e = {k: v for k, v in e.items() if v is not None}
            t.igual("E-47 %s %s" % (dim, nombre), SIN_PROT, _estado(evidencia=EVIDENCIA + [e]))
