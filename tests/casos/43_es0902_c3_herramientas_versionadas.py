# ES0902 §3 C3: las herramientas versionadas y autorizadas, con los controles de G1.
#
# Escenarios E-01 a E-40 de docs/cambios/es0902-c3-herramientas-versionadas/spec.md. E-nn es el
# C3-nn del pedido de instalacion.
#
# 🔴 Lo que se verifica es que C3 NO tenga un camino propio a la homologacion: ni catalogo, ni
# inventario, ni comparador, ni copia del resultado de G1. Y que no quede congelada en 6.3: el dia
# que cambie el Estandar de Desarrollo, C3 deja de pasar hasta que catalogo y controles se muevan.
#
# 🔴 INVENTARIO es el caso que APRUEBA; E-27 lo mira en COMPLIANT.
import ast
import copy
import inspect
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
from orquestacion import normativa                      # noqa: E402
from orquestacion import linea_base                     # noqa: E402
from orquestacion import registro_fuentes as c_fuentes  # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from orquestacion import estandar_de_desarrollo as bt        # noqa: E402

RUTA = BIN / "orquestacion" / "estandar_de_desarrollo.py"
MATRIZ = seguridad.cargar()
REGISTRO = c_controles.cargar()
LINEA = linea_base.cargar()
CATALOGO = json.loads((REGLAS / "annex-ii-technology-catalog.json").read_text(encoding="utf-8"))

LAS_POLICIES = ["approved-technology-required", "homologated-version-required"]
LOS_CHECKS = ["technology-homologation", "technology-version-compliance"]
TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": "C3"}
TRAZA_G1 = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "G1"}

# 🔴 El inventario que APRUEBA: dos tecnologias homologadas.
INVENTARIO = [{"technology": "PHP", "version": "8.2.30"},
              {"technology": "Python", "version": "3.12.12"}]


def _c3(inventario=None, **k):
    return bt.evaluar_c3(copy.deepcopy(INVENTARIO if inventario is None else inventario), **k)


def _una(tecnologia):
    return _c3([tecnologia])


def _linea(*fuentes):
    return {"version": "1.0", "authority": "GCBA / ASI", "sources": list(fuentes)}


ES0901 = {"id": "ES0901", "title": "Estandar de Desarrollo", "version": "6.3", "status": "LOADED"}


def _registro(version="6.4"):
    """Un registro de fuentes forjado. Aca vive la version de una fuente gestionada.

    🔴 La linea base dejo de declararla -una sola autoridad por dato-, asi que un escenario que
    dice "el harness esta en 6.4" se escribe aca. Escribirlo en la linea base ya no significa
    nada, y un test que lo escriba ahi pasa por una razon que no es la suya.
    """
    fuentes = [] if version is None else [{
        "id": "ES0901", "kind": "norma", "title": "Estandar de Desarrollo",
        "version": version, "sha256": None, "extract": "normativa/extractos/ES0901.md",
        "status": "CURRENT"}]
    return {"schema_version": "source-registry/1.1", "sources": fuentes}


def _catalogo(**cambios):
    c = copy.deepcopy(CATALOGO)
    c.update(cambios)
    return c


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


def _valores(dato):
    if isinstance(dato, dict):
        return [x for v in dato.values() for x in _valores(v)]
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


def _todas():
    return {s: True for s in seguridad.senales_declaradas(MATRIZ)}


# -- La fila -------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01 (C3-01)."""
    t.igual("E-01 la matriz", "ES0902.C3", seguridad.regla("C3", MATRIZ)["ruleKey"])
    t.igual("E-01 el resultado", "ES0902.C3", _c3()["ruleKey"])


def test_e02_always(t):
    """E-02 (C3-02)."""
    c3 = seguridad.regla("C3", MATRIZ)
    t.igual("E-02 ALWAYS", "ALWAYS", c3["applicability"]["mode"])
    t.igual("E-02 aplica sin senales", "APPLICABLE", seguridad.resolver_regla(c3, {})[0])


def test_e03_cero_senales(t):
    """E-03 (C3-03)."""
    t.igual("E-03 ninguna", [], seguridad.regla("C3", MATRIZ)["applicability"].get("signals") or [])


def test_e04_agentes(t):
    """E-04 (C3-04)."""
    t.igual("E-04 los dos", ["dev-architecture", "dev-security"],
            seguridad.regla("C3", MATRIZ)["primaryAgents"])


def test_e05_policies(t):
    """E-05 (C3-05)."""
    t.igual("E-05 las dos", LAS_POLICIES, seguridad.regla("C3", MATRIZ)["policies"])


def test_e06_checks(t):
    """E-06 (C3-06)."""
    t.igual("E-06 los dos", LOS_CHECKS, seguridad.regla("C3", MATRIZ)["checks"])


def test_e07_cero_reviews(t):
    """E-07 (C3-07)."""
    t.igual("E-07 ninguna", [], seguridad.regla("C3", MATRIZ)["reviews"])
    t.igual("E-07 ni en el registro", [],
            [c["id"] for c in REGISTRO["controls"] if c["rule"] == "C3" and c["type"] == "REVIEW"])


def test_e08_ningun_agente_ni_skill(t):
    """E-08 (C3-08)."""
    registro = c_reg.cargar()
    t.igual("E-08 diez agentes", 10, len(registro["agents"]))
    t.igual("E-08 veintisiete skills", 27, len([d for d in SKILLS.iterdir() if d.is_dir()]))
    por_id = {a["id"]: a for a in registro["agents"]}
    t.igual("E-08 las skills de dev-architecture", ["dev-architecture-analysis"],
            sorted(s["id"] for s in por_id["dev-architecture"].get("skills") or []))
    t.igual("E-08 las skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in por_id["dev-security"].get("skills") or []))


# -- Reusar, no duplicar -------------------------------------------------------

def test_e09_un_solo_catalogo(t):
    """E-09 (C3-09)."""
    catalogos = sorted(p.name for p in REGLAS.glob("*.json")
                       if "technolog" in p.name or "catalog" in p.name)
    t.igual("E-09 uno solo, el del Anexo II", ["annex-ii-technology-catalog.json"], catalogos)


def test_e10_un_solo_inventario(t):
    """E-10 (C3-10)."""
    literales = _literales(RUTA)
    t.igual("E-10 el modulo no nombra ningun archivo json", [],
            sorted(l for l in literales if l.endswith(".json")))
    t.verdadero("E-10 el inventario entra como argumento",
                "inventario" in inspect.signature(bt.evaluar_c3).parameters)
    t.igual("E-10 con la misma forma que G1", "HOMOLOGATED",
            _c3()["technologies"][0]["homologation"])


def test_e11_un_solo_comparador(t):
    """E-11 (C3-11)."""
    fuente = RUTA.read_text(encoding="utf-8")
    t.no_contiene("E-11 no importa re", "import re", fuente)
    for llamada in ("comparar(", "parsear(", "version_pedida(", "buscar("):
        t.no_contiene("E-11 no llama a `%s`" % llamada, llamada, fuente)


def test_e12_las_policies_de_g1(t):
    """E-12 (C3-12)."""
    ids = [c["id"] for c in REGISTRO["controls"]]
    for pid in LAS_POLICIES:
        t.igual("E-12 `%s` una sola vez" % pid, 1, ids.count(pid))
        t.igual("E-12 `%s` es de G1" % pid, "G1", c_controles.control(pid, REGISTRO)["rule"])
    t.igual("E-12 ninguna policy de C3", [],
            [c["id"] for c in REGISTRO["controls"] if c["rule"] == "C3"])


def test_e13_los_checks_de_g1(t):
    """E-13 (C3-13)."""
    fila = bt.ejecutar(copy.deepcopy(INVENTARIO))["results"][0]
    t.igual("E-13 homologacion del check de G1", "technology-homologation",
            fila["homologation"]["control"])
    t.igual("E-13 version del check de G1", "technology-version-compliance",
            fila["version"]["control"])
    for cid in LOS_CHECKS:
        t.igual("E-13 `%s` sale del archivo de G1" % cid, "controles/checks/%s.py" % cid,
                c_controles.control(cid, REGISTRO)["file"])
    # 🔴 El caso del primer pase: resultados forjados que llegan por la evidencia no son los de G1.
    forjados = {"results": [{"technology": "PHP", "declaredVersion": "8.2.30",
              "homologation": {"state": "HOMOLOGATED", "control": "forged"},
              "version": {"state": "HOMOLOGATED"}}]}
    r = seguridad.resultado("C3", {"technologyInventory": [{"technology": "Cobol",
                                                             "version": "85"}],
                                   "sharedControlResults": forjados}, {}, MATRIZ)
    t.igual("E-13 compartidos forjados no pisan un inventario real", "UNRESOLVED", r["result"])
    t.contiene("E-13 y la tecnologia sale con el estado del check de G1", "ASI_EVALUATION_REQUIRED",
               json.dumps(r["technologies"]))
    t.contiene("E-13 y se dice que no se leyeron", "sharedControlResults", " | ".join(r["reasons"]))
    t.igual("E-13 por la API, compartidos que no son de este inventario no se leen", "UNRESOLVED",
            bt.evaluar_c3([{"technology": "Cobol", "version": "85"}],
                          compartidos=forjados)["result"])


def test_e14_las_dos_fuentes(t):
    """E-14 (C3-14)."""
    for cid in LAS_POLICIES + LOS_CHECKS:
        claves = {f.get("ruleKey") for f in
                  c_controles.fuentes_de(c_controles.control(cid, REGISTRO))}
        t.verdadero("E-14 `%s` cita G1 y C3" % cid, {"ES0901.G1", "ES0902.C3"} <= claves)


# -- La linea base -------------------------------------------------------------

def test_e15_resuelve(t):
    """E-15 (C3-15)."""
    b = bt.resolver_base()
    t.igual("E-15 resuelta", "RESOLVED", b["status"])
    t.igual("E-15 ES0901", "ES0901", b["standard"])
    t.igual("E-15 6.3", "6.3", b["version"])
    t.igual("E-15 el catalogo", {"standard": "ES0901", "version": "6.3"}, b["catalogSource"])
    t.igual("E-15 las policies", LAS_POLICIES, b["policies"])
    t.igual("E-15 los checks", LOS_CHECKS, b["checks"])


def test_e16_sin_resolver(t):
    """E-16 (C3-16)."""
    casos = {
        "sin ES0901": _linea(),
        "ES0901 no cargado": _linea(dict(ES0901, status="DECLARED_EXTERNAL_NOT_LOADED")),
        "dos cargados sin vigente": _linea(ES0901, dict(ES0901, version="6.4")),
        "dos vigentes": _linea(dict(ES0901, currency="CURRENT"),
                               dict(ES0901, version="6.4", currency="CURRENT")),
    }
    for nombre, linea in casos.items():
        b = bt.resolver_base(linea=linea)
        t.igual("E-16 %s" % nombre, ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED"],
                b["states"])
    # 🔴 Del primer pase: lo que no se reconoce no se descarta, y lo reemplazado no rige.
    ilegibles = {
        "el unico, reemplazado": _linea(dict(ES0901, currency="SUPERSEDED")),
        "otro con currency mal escrita": _linea(dict(ES0901, currency="CURRENT"),
                                                dict(ES0901, version="6.4", currency="Current")),
        "otro con status mal escrito": _linea(ES0901, dict(ES0901, version="6.4",
                                                           status="Loaded")),
        "una fuente que no es dict": {"version": "1.0", "sources": [ES0901, "ES0901 6.4"]},
        "sources que no es lista": {"version": "1.0", "sources": "ES0901"},
    }
    # 🔴 Del segundo pase: el vigente sin cargar, y el id escrito de otra forma.
    no_cargada = dict(ES0901, version="6.4", status="DECLARED_EXTERNAL_NOT_LOADED",
                      currency="CURRENT")
    ilegibles.update({
        "otro vigente sin cargar": _linea(ES0901, no_cargada),
        "otro vigente sin cargar, con 6.3 CURRENT": _linea(dict(ES0901, currency="CURRENT"),
                                                           no_cargada),
        "otro con el id con espacio": _linea(ES0901, dict(ES0901, id="ES0901 ", version="6.4",
                                                          currency="CURRENT")),
        "otro con el id en minuscula": _linea(ES0901, dict(ES0901, id="es0901", version="6.4")),
        "una fuente sin id": _linea(ES0901, {"version": "6.4", "status": "LOADED"}),
        # 🔴 Del tercer pase, y la regla que cierra la clase.
        "un id vacio": _linea(ES0901, dict(ES0901, id="", version="6.4", currency="CURRENT")),
        "un id en ancho completo": _linea(ES0901, dict(ES0901, id="ＥＳ" + "0901",
                                                      version="6.4", currency="CURRENT")),
        "un id con la version pegada": _linea(ES0901, dict(ES0901, id="ES0901-6.4",
                                                          version="6.4", currency="CURRENT")),
        "un id numerico": _linea(ES0901, dict(ES0901, id=901, version="6.4")),
        # Del cuarto pase: una marca combinada sobre una letra, y un id que solo es invisible.
        "una tilde combinada sobre la E": _linea(ES0901, dict(ES0901, id="ÉS0901",
                                                             version="6.4", currency="CURRENT")),
        "un id de ancho cero": _linea(ES0901, dict(ES0901, id="​", version="6.4")),
        "un id que es un BOM": _linea(ES0901, dict(ES0901, id="﻿", version="6.4")),
    })
    for nombre, linea in ilegibles.items():
        t.igual("E-16 %s" % nombre, ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED"],
                bt.resolver_base(linea=linea)["states"])
    # 🔴 "Sin version" ya no se escribe en la linea base: la dice el registro de fuentes. Sin
    # registro que la diga, la base queda sin resolver igual — que es lo que el escenario pide.
    t.igual("E-16 sin version", ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED"],
            bt.resolver_base(linea=_linea(dict(ES0901, version=None)),
                             registro_de_fuentes=_registro(None))["states"])
    uno = _linea(dict(ES0901, currency="CURRENT"),
                 dict(ES0901, version="6.2", currency="SUPERSEDED"))
    t.igual("E-16 con uno solo vigente resuelve", "RESOLVED", bt.resolver_base(linea=uno)["status"])


def test_e17_desfase_de_version(t):
    """E-17 (C3-17)."""
    nueva = _linea(ES0901)
    en64 = _registro("6.4")
    t.igual("E-17 6.4 contra el catalogo de 6.3",
            ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH"],
            bt.resolver_base(linea=nueva, registro_de_fuentes=en64)["states"])
    cat64 = _catalogo(source=dict(CATALOGO["source"], version="6.4"),
                      status="COMPLETE_FOR_ANNEX_II_V6_4")
    t.igual("E-17 catalogo 6.4 y controles de 6.3",
            ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH"],
            bt.resolver_base(linea=nueva, catalogo=cat64, registro_de_fuentes=en64)["states"])
    t.igual("E-17 los tres en 6.4 resuelven", "RESOLVED",
            bt.resolver_base(linea=nueva, catalogo=cat64, version_de_controles="6.4",
                             registro_de_fuentes=en64)["status"])
    r = seguridad.resultado("C3", {"technologyInventory": INVENTARIO,
                                   "developmentStandardBaseline": bt.resolver_base(
                                       linea=nueva, registro_de_fuentes=en64)},
                            {}, MATRIZ)
    t.igual("E-17 y C3 no pasa", "UNRESOLVED", r["result"])
    # 🔴 Del segundo pase: la puerta mira el mismo catalogo contra el que se ejecuta.
    cat62 = _catalogo(source=dict(CATALOGO["source"], version="6.2"),
                      status="COMPLETE_FOR_ANNEX_II_V6_2")
    t.igual("E-17 un catalogo de 6.2 pasado por la API no aprueba", "UNRESOLVED",
            bt.evaluar_c3(INVENTARIO, catalogo=cat62)["result"])


def test_e18_otro_estandar(t):
    """E-18 (C3-18)."""
    for nombre, cat in (("otro estandar", _catalogo(source=dict(CATALOGO["source"],
                                                                 standard="ES0902"))),
                        ("status de otra version", _catalogo(status="COMPLETE_FOR_ANNEX_II_V6_2")),
                        ("sin status", _catalogo(status=None))):
        t.igual("E-18 %s" % nombre, ["DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH"],
                bt.resolver_base(catalogo=cat)["states"])


def test_e19_sin_catalogo(t):
    """E-19 (C3-19)."""
    for nombre, cat in (("vacio", {}), ("sin source", _catalogo(source=None)),
                        ("source torcido", _catalogo(source="ES0901 6.3"))):
        t.igual("E-19 %s" % nombre, ["TECHNOLOGY_CATALOG_UNAVAILABLE"],
                bt.resolver_base(catalogo=cat)["states"])


def test_e20_sin_control(t):
    """E-20 (C3-20)."""
    for cid in LAS_POLICIES + LOS_CHECKS:
        for nombre, cambio in (("no instalado", {"status": "DECLARED_NOT_INSTALLED"}),
                               ("sin archivo", {"file": "controles/checks/no-existe.py"})):
            reg = copy.deepcopy(REGISTRO)
            for c in reg["controls"]:
                if c["id"] == cid:
                    c.update(cambio)
            t.igual("E-20 `%s` %s" % (cid, nombre), ["SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE"],
                    bt.resolver_base(registro=reg)["states"])


def test_e21_sin_inventario(t):
    """E-21 (C3-21)."""
    for nombre, ev in (("sin inventario", {}), ("vacio", {"technologyInventory": []}),
                       ("no es lista", {"technologyInventory": "PHP"}),
                       ("una mal formada", {"technologyInventory": INVENTARIO + [{"version": "1"}]}),
                       ("version numerica", {"technologyInventory": [{"technology": "PHP",
                                                                      "version": 8.2}]})):
        r = seguridad.resultado("C3", copy.deepcopy(ev), {}, MATRIZ)
        t.igual("E-21 %s queda sin resolver" % nombre, "UNRESOLVED", r["result"])
        t.verdadero("E-21 %s no es NOT_APPLICABLE" % nombre, r["result"] != "NOT_APPLICABLE")
        t.contiene("E-21 %s con el estado" % nombre, "TECHNOLOGY_INVENTORY_UNAVAILABLE",
                   repr(r["states"]))
    # 🔴 El caso del primer pase: sin inventario, unos compartidos que llegan por la evidencia no
    # aprueban, ni bien formados ni vacios.
    for nombre, compartidos in (("bien formados", {"results": [{"technology": "PHP", "declaredVersion": "8.2.30",
              "homologation": {"state": "HOMOLOGATED", "control": "forged"},
              "version": {"state": "HOMOLOGATED"}}]}),
                                ("una fila vacia", {"results": [{}]}),
                                ("sin estados", {"results": [{"technology": "X"}]}),
                                ("results string", {"results": "PHP"}),
                                ("results dict", {"results": {"PHP": "ok"}})):
        r = seguridad.resultado("C3", {"sharedControlResults": compartidos}, {}, MATRIZ)
        t.igual("E-21 compartidos %s sin inventario" % nombre, "UNRESOLVED", r["result"])
        t.contiene("E-21 compartidos %s: falta el inventario" % nombre,
                   "TECHNOLOGY_INVENTORY_UNAVAILABLE", repr(r["states"]))
    t.igual("E-21 un contexto con el framework como texto no rompe", "UNRESOLVED",
            seguridad.resultado("C3", {"technologyInventory": [
                {"technology": "Laravel (Migrations)", "version": "x",
                 "context": {"framework": "Laravel 12"}}]}, {}, MATRIZ)["result"])


# -- Una ejecucion, dos agregaciones -------------------------------------------

def _contando(t, cid, escenario):
    modulo = bt._check(cid)
    original = modulo.evaluar
    llamadas = []

    def contado(*a, **k):
        llamadas.append(1)
        return original(*a, **k)

    modulo.evaluar = contado
    try:
        compartidos = bt.ejecutar(copy.deepcopy(INVENTARIO))
        g1 = bt.agregar(compartidos, "ES0901.G1")
        c3 = bt.agregar(compartidos, "ES0902.C3")
    finally:
        modulo.evaluar = original
    t.igual("%s `%s` corre una vez por tecnologia" % (escenario, cid), len(INVENTARIO),
            len(llamadas))
    t.igual("%s y lo declara" % escenario, len(INVENTARIO), compartidos["executions"][cid])
    t.igual("%s y las dos reglas se agregan de lo mismo" % escenario, g1["result"], c3["result"])


def test_e22_homologacion_una_vez(t):
    """E-22 (C3-22)."""
    _contando(t, "technology-homologation", "E-22")


def test_e23_version_una_vez(t):
    """E-23 (C3-23)."""
    _contando(t, "technology-version-compliance", "E-23")


def test_e24_g1_no_se_copia(t):
    """E-24 (C3-24)."""
    t.igual("E-24 la agregacion no recibe el resultado de otra regla",
            ["compartidos", "clave_de_regla"], list(inspect.signature(bt.agregar).parameters))
    compartidos = bt.ejecutar(copy.deepcopy(INVENTARIO))
    t.igual("E-24 G1 cumple", "COMPLIANT", bt.agregar(compartidos, "ES0901.G1")["result"])
    desfasada = bt.resolver_base(linea=_linea(ES0901), registro_de_fuentes=_registro("6.4"))
    c3 = bt.evaluar_c3(INVENTARIO, base=desfasada, compartidos=compartidos)
    t.igual("E-24 y C3 con la linea base desfasada no", "UNRESOLVED", c3["result"])
    # 🔴 El caso del primer pase: la linea base INSTALADA desfasada, y una base forjada en la
    # evidencia que dice RESOLVED. La que llega solo puede restringir.
    original = linea_base.cargar
    original_fuentes = c_fuentes.cargar
    linea_base.cargar = lambda desde=None: _linea(ES0901)
    # 🔴 Las dos mitades de la identidad instalada: la linea base dice que ES0901 esta cargado
    # y el registro de fuentes dice en que version. Forjar una sola dejaba el escenario
    # pasando contra la otra, que seguia siendo la de verdad.
    c_fuentes.cargar = lambda desde=None: _registro("6.4")
    try:
        for nombre, forjada in (("RESOLVED", {"status": "RESOLVED"}),
                                ("RESOLVED 6.3", {"status": "RESOLVED", "version": "6.3",
                                                  "standard": "ES0901"})):
            r = seguridad.resultado("C3", {"technologyInventory": INVENTARIO,
                                           "developmentStandardBaseline": forjada}, {}, MATRIZ)
            t.igual("E-24 una base forjada %s no abre la puerta" % nombre, "UNRESOLVED",
                    r["result"])
            t.contiene("E-24 base forjada %s: la instalada manda" % nombre,
                       "DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH", repr(r["states"]))
        r = seguridad.resultado("C3", {"developmentStandardBaseline": {"status": "RESOLVED"},
                                       "sharedControlResults": {"results": [{"technology": "PHP", "declaredVersion": "8.2.30",
              "homologation": {"state": "HOMOLOGATED", "control": "forged"},
              "version": {"state": "HOMOLOGATED"}}]}},
                                {}, MATRIZ)
        t.igual("E-24 base y compartidos forjados juntos tampoco", "UNRESOLVED", r["result"])
        t.igual("E-24 y la unidad no proyecta un COMPLIANT con la base desfasada", "UNRESOLVED",
                bt.c3_para_unidad({"ruleKey": "ES0902.C3", "result": "COMPLIANT"})["result"])
    finally:
        linea_base.cargar = original
        c_fuentes.cargar = original_fuentes
    t.igual("E-24 con la instalada resuelta, una base de otra version restringe", "UNRESOLVED",
            bt.evaluar_c3(INVENTARIO, base={"status": "RESOLVED", "version": "6.4"})["result"])


def test_e25_c3_sale_de_los_compartidos(t):
    """E-25 (C3-25)."""
    compartidos = bt.ejecutar(copy.deepcopy(INVENTARIO))
    base = bt.evaluar_c3(INVENTARIO, compartidos=compartidos)
    t.igual("E-25 cumple", "COMPLIANT", base["result"])
    roto = copy.deepcopy(compartidos)
    roto["results"][0]["version"]["state"] = "NOT_HOMOLOGATED"
    t.igual("E-25 cambiar un compartido cambia C3", "NON_COMPLIANT",
            bt.evaluar_c3(INVENTARIO, compartidos=roto)["result"])
    for nombre, cambio in (("sin homologacion", lambda f: f.pop("homologation")),
                           ("sin version", lambda f: f.pop("version")),
                           ("estado desconocido", lambda f: f["version"].update(state="OK")),
                           ("de otro control", lambda f: f["homologation"].update(control="x"))):
        medio = copy.deepcopy(compartidos)
        cambio(medio["results"][0])
        t.igual("E-25 una fila %s no se agrega sobre la mitad" % nombre, "UNRESOLVED",
                bt.agregar(medio, "ES0902.C3")["result"])
    g1 = bt.agregar(compartidos, "ES0901.G1")
    g1["result"] = "NON_COMPLIANT"
    t.igual("E-25 cambiar el agregado de G1 no", "COMPLIANT",
            bt.evaluar_c3(INVENTARIO, compartidos=compartidos)["result"])


def test_e26_determinismo(t):
    """E-26 (C3-26)."""
    inventario = INVENTARIO + [{"technology": "PHP", "version": "8.2.29"},
                               {"technology": "Keycloak", "version": "24"}]
    base = json.dumps(_c3(inventario), sort_keys=True)
    t.igual("E-26 dos corridas", base, json.dumps(_c3(inventario), sort_keys=True))
    azar = random.Random(26)
    for vuelta in range(5):
        otro = copy.deepcopy(inventario)
        azar.shuffle(otro)
        t.igual("E-26 desordenado %d" % vuelta, base, json.dumps(_c3(otro), sort_keys=True))


# -- Las semanticas de G1 ------------------------------------------------------

def test_e27_homologada(t):
    """E-27 (C3-27) — el caso que aprueba."""
    r = _c3()
    t.igual("E-27 cumple", "COMPLIANT", r["result"])
    t.igual("E-27 las dos homologadas", ["HOMOLOGATED"],
            sorted({e for x in r["technologies"] for e in x["states"]}))
    t.igual("E-27 y por seguridad.resultado tambien", "COMPLIANT",
            seguridad.resultado("C3", {"technologyInventory": INVENTARIO}, {}, MATRIZ)["result"])


def test_e28_deprecada(t):
    """E-28 (C3-28)."""
    r = _una({"technology": "PHP", "version": "8.2.29"})
    t.igual("E-28 la version sale deprecada", "DEPRECATED_TOLERATED", r["technologies"][0]["version"])
    t.verdadero("E-28 y no homologada", "HOMOLOGATED" != r["technologies"][0]["version"])
    t.igual("E-28 la regla con observaciones", "COMPLIANT_WITH_OBSERVATIONS", r["result"])
    s = seguridad.resultado("C3", {"technologyInventory": [{"technology": "PHP",
                                                            "version": "8.2.29"}]}, {}, MATRIZ)
    t.igual("E-28 y lo dice en seguridad", "COMPLIANT_WITH_OBSERVATIONS", s.get("compliance"))


def test_e29_mas_nueva(t):
    """E-29 (C3-29)."""
    r = _una({"technology": "PHP", "version": "8.4.1"})
    t.igual("E-29 no se autoriza", "ASI_EVALUATION_REQUIRED", r["technologies"][0]["version"])
    t.igual("E-29 la regla sin resolver", "UNRESOLVED", r["result"])


def test_e30_no_figura(t):
    """E-30 (C3-30)."""
    r = _una({"technology": "Cobol", "version": "85"})
    t.igual("E-30 la ASI evalua", "ASI_EVALUATION_REQUIRED", r["technologies"][0]["homologation"])
    t.igual("E-30 sin resolver", "UNRESOLVED", r["result"])


def test_e31_auxiliar(t):
    """E-31 (C3-31)."""
    r = _una({"technology": "eslint", "version": "9.0.0", "role": "TOOLCHAIN_AUXILIARY"})
    t.igual("E-31 auxiliar", "TOOLCHAIN_AUXILIARY_REVIEW", r["technologies"][0]["homologation"])
    t.igual("E-31 sin resolver", "UNRESOLVED", r["result"])


def test_e32_version_del_proveedor(t):
    """E-32 (C3-32)."""
    for nombre in ("Keycloak", "OpenID Connect (OIDC)"):
        r = _una({"technology": nombre, "version": "24.0"})
        t.igual("E-32 %s" % nombre, "PROVIDER_VERSION_REQUIRED", r["technologies"][0]["version"])
        t.igual("E-32 %s sin resolver" % nombre, "UNRESOLVED", r["result"])
        t.no_contiene("E-32 %s sin version inventada" % nombre, "homologatedVersion",
                      json.dumps(r["technologies"]))


def test_e33_contexto_de_framework(t):
    """E-33 (C3-33)."""
    r = _una({"technology": "Laravel (Migrations)", "version": "x"})
    t.igual("E-33 pide el framework", "VERSION_CONTEXT_REQUIRED", r["technologies"][0]["version"])
    con = _una({"technology": "Laravel (Migrations)", "version": "x",
                "context": {"framework": {"technology": "Laravel", "version": "12.47.0"}}})
    t.igual("E-33 con el framework hereda", "HOMOLOGATED", con["technologies"][0]["version"])


# -- Los limites ---------------------------------------------------------------

def _con_c3_conforme():
    ev = {"technologyInventory": copy.deepcopy(INVENTARIO)}
    return {r["rule"]: r for r in seguridad.resultados(ev, _todas(), MATRIZ)}


def test_e34_no_es_c2(t):
    """E-34 (C3-34)."""
    rs = _con_c3_conforme()
    t.igual("E-34 C3 cumple", "COMPLIANT", rs["C3"]["result"])
    t.verdadero("E-34 C2 no", rs["C2"]["result"] != "COMPLIANT")


def test_e35_no_es_vu7(t):
    """E-35 (C3-35)."""
    t.verdadero("E-35 Vu7 no", _con_c3_conforme()["Vu7"]["result"] != "COMPLIANT")


def test_e36_no_es_vu10(t):
    """E-36 (C3-36)."""
    t.verdadero("E-36 Vu10 no", _con_c3_conforme()["Vu10"]["result"] != "COMPLIANT")


def test_e37_no_es_g2(t):
    """E-37 (C3-37)."""
    t.verdadero("E-37 G2 no", _con_c3_conforme()["G2"]["result"] != "COMPLIANT")


def test_e38_no_escanea(t):
    """E-38 (C3-38)."""
    literales = {l.lower() for l in _literales(RUTA)}
    for palabra in ("cve", "vulnerab", "severity", "finding", "scanner"):
        t.verdadero("E-38 ningun literal nombra `%s`" % palabra,
                    not any(palabra in l for l in literales))


def test_e39_la_traza_de_c3(t):
    """E-39 (C3-39)."""
    caminos = {"pasa": _c3(), "vacio": _c3([]),
               "desfasada": bt.evaluar_c3(INVENTARIO, base=bt.resolver_base(
                   linea=_linea(ES0901), registro_de_fuentes=_registro("6.4")))}
    for nombre, r in caminos.items():
        t.igual("E-39 %s conserva la traza" % nombre, TRAZA, r["source"])
        t.igual("E-39 %s y la clave" % nombre, "ES0902.C3", r["ruleKey"])
    bloque = normativa.resolucion({}, evidencia={"ES0902.C3": _c3()})
    c3 = bloque["standards"]["ES0902"]["rules"]["C3"]
    t.igual("E-39 la unidad trae el resultado", "COMPLIANT", c3["result"])
    t.igual("E-39 la linea base", {"standard": "ES0901", "version": "6.3"},
            {k: c3["developmentStandardBaseline"][k] for k in ("standard", "version")})
    t.igual("E-39 los controles", {"policies": LAS_POLICIES, "checks": LOS_CHECKS},
            c3["sharedControls"])
    for pesado in ("homologatedVersionsRaw", "entries", "deprecatedVersionsRaw"):
        t.no_contiene("E-39 sin el catalogo: `%s`" % pesado, pesado, json.dumps(bloque))
    for nombre, falso in (("un estado que C3 no emite", {"ruleKey": "ES0902.C3", "result": "BOGUS"}),
                          ("el de otra regla", {"ruleKey": "ES0901.G1", "result": "COMPLIANT"}),
                          ("sin clave", {"result": "COMPLIANT"})):
        t.igual("E-39 la unidad no proyecta %s" % nombre, "UNRESOLVED",
                bt.c3_para_unidad(falso)["result"])
    t.igual("E-39 la base de la unidad es la instalada, no la del resultado", "RESOLVED",
            bt.c3_para_unidad(dict(_c3(), developmentStandardBaseline={"status": "MISMATCH"}))[
                "developmentStandardBaseline"]["status"])
    t.igual("E-39 sin resultado queda sin resolver", "UNRESOLVED",
            normativa.resolucion({})["standards"]["ES0902"]["rules"]["C3"]["result"])


def test_e40_la_traza_de_g1(t):
    """E-40 (C3-40)."""
    for fila in bt.ejecutar(copy.deepcopy(INVENTARIO))["results"]:
        for parte in ("homologation", "version"):
            t.igual("E-40 %s de %s trae la traza de G1" % (parte, fila["technology"]), TRAZA_G1,
                    fila[parte]["source"])
        for cid in LOS_CHECKS:
            t.verdadero("E-40 %s cita G1 y C3" % cid,
                        {"ES0901.G1", "ES0902.C3"} <= set(fila["normativeSources"][cid]))
