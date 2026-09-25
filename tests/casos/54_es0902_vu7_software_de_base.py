# ES0902 §6 Vu7: todo el software de base esta configurado para no entregar datos privados.
#
# Escenarios E-01 a E-45 de docs/cambios/es0902-vu7-software-de-base-sin-datos-privados/spec.md.
#
# 🔴 CASO es un servidor web de QA con una superficie, un listado de directorios publico que sirve la
# clase `ciudadanos`, clasificada PRIVATE por una evidencia de privacidad citada. El inventario y el
# alcance salen de una evidencia de arquitectura citada, y una configuracion efectiva de QA citada
# establece que no hay fuga. Casi todo este archivo sale de romperlo. E-24 lo mira en PASS.
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
from orquestacion import normativa                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "base-software-data-disclosure-configuration.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "vu7_software_de_base")
VU6 = _cargar(CONTROLES / "checks" / "custom-error-message-compliance.py", "vu7_de_vu6")
MATRIZ = seguridad.cargar()

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu7"}
LOS_9 = ("PASS", "FAIL", "BASE_SOFTWARE_INVENTORY_UNRESOLVED",
         "PRIVATE_DATA_CLASSIFICATION_UNRESOLVED", "DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED",
         "BASE_SOFTWARE_CONFIGURATION_UNRESOLVED", "UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE",
         "BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")
INV = "BASE_SOFTWARE_INVENTORY_UNRESOLVED"
CLASE = "PRIVATE_DATA_CLASSIFICATION_UNRESOLVED"
COB = "DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED"
CONF = "BASE_SOFTWARE_CONFIGURATION_UNRESOLVED"
FUGA = "UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE"
INSEGURA = "BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE"
SIN_OBJ = "TEST_TARGET_UNAVAILABLE"
FALLAS = ("FAIL", FUGA)
SIN_FUGA = "NO_PRIVATE_DATA_DISCLOSURE"
ACCESO = "AUTHORIZED_PRIVATE_DATA_ACCESS"

COMP = "servidor-web"
SUP = "listado"


def _e(eid, fuente, establece, valor=None, comps=(COMP,), sups=(SUP,), **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": "ref-%s" % eid,
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if comps is not None:
        base["components"] = list(comps)
    if sups is not None:
        base["surfaces"] = list(sups)
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _inv(valores=(COMP,), eid="inv", fuente="ARCHITECTURE_DOCUMENTATION", **extra):
    return _e(eid, fuente, "BASE_SOFTWARE_INVENTORY", comps=None, sups=None, values=list(valores),
              **extra)


def _alc(valores=(SUP,), eid="alc", comp=COMP, fuente="ARCHITECTURE_DOCUMENTATION", **extra):
    return _e(eid, fuente, "DISCLOSURE_SURFACE_SCOPE", comps=[comp], sups=None, values=list(valores),
              **extra)


def _clasif(clase="ciudadanos", valor="PRIVATE", eid="clasif", fuente="PRIVACY_DOCUMENTATION",
            **extra):
    return _e(eid, fuente, "DATA_CLASSIFICATION", valor, comps=None, sups=None, dataClasses=[clase],
              **extra)


def _ent(eid="efectiva", valor=SIN_FUGA, fuente="EFFECTIVE_CONFIGURATION", ambiente="QA",
         sup=SUP, comp=COMP, **extra):
    datos = dict(extra)
    if ambiente is not None:
        datos["environment"] = ambiente
    return _e(eid, fuente, "DATA_DISCLOSURE", valor, comps=None if comp is None else [comp],
              sups=None if sup is None else [sup], **datos)


def _fuga(eid="fuga", fuente="ENVIRONMENT_OVERRIDE", **k):
    return _ent(eid, FUGA, fuente, **k)


def _aut(eid="aut", valor="AUTHORIZED", fuente="SECURITY_DOCUMENTATION", ambiente="QA", sup=SUP):
    datos = {"environment": ambiente} if ambiente is not None else {}
    return _e(eid, fuente, "AUTHORIZATION_CONTEXT", valor, sups=[sup], **datos)


INVENTARIO = _inv()
ALCANCE = _alc()
CLASIF = _clasif()
EFECTIVA = _ent()
EVIDENCIA = [INVENTARIO, ALCANCE, CLASIF, EFECTIVA]


def _sup(sid=SUP, ctx="PUBLIC", refs=("ciudadanos",), resultado=SIN_FUGA, evidencia=("efectiva",),
         tipo="DIRECTORY_LISTING", modo="STATIC_CONFIGURATION"):
    return {"surfaceId": sid, "surfaceType": tipo, "authorizationContext": ctx,
            "dataClassRefs": list(refs), "result": resultado, "verificationMode": modo,
            "evidence": list(evidencia)}


def _comp(cid=COMP, superficies=None, evidencia=("inv", "alc"), estado="RESOLVED",
          tipo="WEB_SERVER", producto="producto-a"):
    return {"componentId": cid, "componentType": tipo, "productRef": producto,
            "configurationStatus": estado,
            "surfaces": [_sup()] if superficies is None else list(superficies),
            "evidence": list(evidencia)}


def _clase(cid="ciudadanos", valor="PRIVATE", evidencia=("clasif",)):
    return {"dataClassId": cid, "classification": valor, "evidence": list(evidencia)}


def _reg(componentes=None, clases=None, ambiente="QA", enlace="ocp-qa/tramites"):
    return {"version": "1.0", "environment": ambiente, "deploymentBinding": enlace,
            "dataClasses": copy.deepcopy([_clase()] if clases is None else clases),
            "components": copy.deepcopy([_comp()] if componentes is None else componentes)}


def _caso(registro=None, evidencia=None):
    return {"registry": _reg() if registro is None else copy.deepcopy(registro),
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}


def _r(registro=None, evidencia=None):
    return CHECK.evaluar(_caso(registro, evidencia))


def _estado(registro=None, evidencia=None):
    return _r(registro, evidencia)["state"]


def _c(r, cid=COMP):
    return [c for c in r["components"] if c["componentId"] == cid][0]


def _s(r, cid=COMP, sid=SUP):
    return [s for s in _c(r, cid)["surfaces"] if s["surfaceId"] == sid][0]


def _sin(eid, *mas):
    return [x for x in EVIDENCIA if x["evidenceId"] != eid] + list(mas)


def _solo_con(*evidencia, **cambios):
    """La superficie sostenida solo por `evidencia` en lugar de `efectiva`."""
    ids = [x["evidenceId"] for x in evidencia]
    return _r(_reg([_comp(superficies=[_sup(evidencia=ids, **cambios)])]),
              _sin("efectiva", *evidencia))


def _con_ademas(*evidencia, **cambios):
    """La superficie con `efectiva`, y ademas `evidencia` citada desde la superficie."""
    ids = [x["evidenceId"] for x in evidencia]
    return _r(_reg([_comp(superficies=[_sup(evidencia=["efectiva"] + ids, **cambios)])]),
              EVIDENCIA + list(evidencia))


def _honesta(*evidencia, ctx="UNAUTHORIZED"):
    """La superficie que declara la fuga con honestidad, citando `evidencia`."""
    return _solo_con(*evidencia, resultado=FUGA, ctx=ctx)


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


def _json(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


def _vu7_en_seguridad(r):
    ev, sen = CHECK.para_seguridad(r)
    return seguridad.resultado("Vu7", ev, sen, MATRIZ)


def _unidad(r):
    return normativa.resolucion({}, evidencia={"ES0902.Vu7": r})["standards"]["ES0902"]["rules"]["Vu7"]


PRUEBA = dict(environment="QA", authorized=True, syntheticFixtures=True)


def _prueba(valor=SIN_FUGA, eid="qa", sup=SUP, **cambios):
    datos = dict(PRUEBA, **cambios)
    datos = {k: v for k, v in datos.items() if v is not None}
    return _e(eid, "AUTHORIZED_QA_RUNTIME_TEST", "DATA_DISCLOSURE", valor,
              sups=None if sup is None else [sup], **datos)


def _otro(cid="base-de-datos", sid="consola", valor=SIN_FUGA, ctx="UNAUTHORIZED", resultado=None):
    """Otro componente, en el inventario y con su alcance, con una superficie sostenida."""
    evid = [_alc([sid], eid="alc-%s" % cid, comp=cid),
            _ent("ent-%s" % cid, valor, sup=sid, comp=cid)]
    comp = _comp(cid, [_sup(sid, ctx=ctx, resultado=resultado or valor,
                            evidencia=["ent-%s" % cid])],
                 evidencia=["inv", "alc-%s" % cid], tipo="DATABASE", producto="producto-b")
    return comp, evid


def _con_otro(**k):
    comp, evid = _otro(**k)
    return _r(_reg([_comp(), comp]),
              [_inv([COMP, comp["componentId"]])] + EVIDENCIA[1:] + evid)


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01."""
    t.igual("E-01 la fila", "ES0902.Vu7", seguridad.regla("Vu7", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu7", CHECK.CLAVE)
    for nombre, r in (("pasa", _r()), ("vacio", CHECK.evaluar({})),
                      ("falla", _con_ademas(_fuga())),
                      ("registro invalido", CHECK.evaluar({"registry": {"components": 1}}))):
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu7", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu7", _vu7_en_seguridad(r)["ruleKey"])
        t.igual("E-01 y en el libro (%s)" % nombre, "ES0902.Vu7",
                prod.desde_regla(_vu7_en_seguridad(r), "GCBA-7001", {"project": "P"},
                                 "2026-09-24T10:00:00")[0]["details"]["ruleKey"])


def test_e02_los_ids(t):
    """E-02."""
    vu7 = seguridad.regla("Vu7", MATRIZ)
    t.igual("E-02 ALWAYS", "ALWAYS", vu7["applicability"]["mode"])
    t.igual("E-02 sin senal", [], vu7["applicability"]["signals"])
    t.igual("E-02 los agentes, en el orden de la matriz", ["dev-security", "dev-devops"],
            vu7["primaryAgents"])
    t.igual("E-02 la policy", ["base-software-private-data-disclosure-prohibited"], vu7["policies"])
    t.igual("E-02 el check", ["base-software-data-disclosure-configuration"], vu7["checks"])
    t.igual("E-02 el modulo", ("base-software-data-disclosure-configuration",
                               "base-software-private-data-disclosure-prohibited"),
            (CHECK.CONTROL, CHECK.POLICY))
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (
            ("base-software-private-data-disclosure-prohibited", "POLICY",
             "controles/policies/base-software-private-data-disclosure-prohibited.md"),
            ("base-software-data-disclosure-configuration", "CHECK",
             "controles/checks/base-software-data-disclosure-configuration.py")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.igual("E-02 %s regla" % cid, "Vu7", registro[cid]["rule"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    for md in ("es0902-vu7-governance.md", "es0902-vu7-base-software-data-disclosure-configuration-check.md"):
        t.verdadero("E-02 %s instalado" % md, (REGLAS / md).is_file())
    gobierno = (REGLAS / "es0902-vu7-governance.md").read_text(encoding="utf-8")
    for trozo in ("ruleKey: ES0902.Vu7", "mode: ALWAYS", "- dev-security",
                  "- base-software-private-data-disclosure-prohibited",
                  "- base-software-data-disclosure-configuration"):
        t.contiene("E-02 el gobierno declara `%s`" % trozo, trozo, gobierno)
    politica = (CONTROLES / "policies" / "base-software-private-data-disclosure-prohibited.md"
                ).read_text(encoding="utf-8")
    t.contiene("E-02 la policy declara su id", "id: base-software-private-data-disclosure-prohibited",
               politica)
    t.contiene("E-02 y su regla", "rule: Vu7", politica)


def test_e03_nada_nuevo(t):
    """E-03."""
    registro = c_reg.cargar()
    t.igual("E-03 diez agentes", 10, len(registro["agents"]))
    t.igual("E-03 veintisiete directorios de skills", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-03 cero reviews", [], seguridad.regla("Vu7", MATRIZ)["reviews"])
    t.igual("E-03 las mismas reviews en disco",
            ["gcba-it-security-normative-review.md", "object-oriented-design-review.md",
             "technology-practice-review.md"],
            sorted(p.name for p in (CONTROLES / "reviews").iterdir() if p.is_file()))
    t.igual("E-03 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-03 y Vu7 no tiene algoritmo propio", "Vu7" not in seguridad.ALGORITMOS)
    t.igual("E-03 ninguna senal de Vu7 en disco", [],
            sorted(p.name for p in REGLAS.glob("es0902-vu7-*signal*")))
    t.verdadero("E-03 el modulo no declara senal", not hasattr(CHECK, "SENAL"))
    t.verdadero("E-03 ni produce una", "senal" not in {n.name for n in ast.walk(_arbol())
                                                       if isinstance(n, ast.FunctionDef)})
    t.igual("E-03 ninguna senal nueva en la matriz", sorted({
        s for r in seguridad.reglas(MATRIZ) if r["id"] != "Vu7"
        for s in r["applicability"].get("signals") or []}), sorted(seguridad.senales_declaradas(MATRIZ)))


# -- ALWAYS ---------------------------------------------------------------------

def test_e04_nunca_no_aplica(t):
    """E-04."""
    t.verdadero("E-04 no es un estado del check", "NOT_APPLICABLE" not in CHECK.ESTADOS)
    t.verdadero("E-04 ni una literal del modulo", "NOT_APPLICABLE" not in _literales())
    t.verdadero("E-04 ni un estado de la unidad", "NOT_APPLICABLE" not in normativa.ESTADOS_DEL_CHECK_VU7)
    entradas = [None, {}, [], "x", {"registry": None}, {"registry": _reg([], [], None)},
                {"registry": {"components": 1}}, _caso(), _caso(evidencia=[])]
    azar = random.Random(4)
    for _ in range(40):
        sup = _sup(ctx=azar.choice(["AUTHORIZED", "UNAUTHORIZED", "PUBLIC", "UNRESOLVED"]),
                   resultado=azar.choice([SIN_FUGA, ACCESO, FUGA, "UNRESOLVED"]),
                   evidencia=azar.sample(["efectiva", "fuga", "aut", "qa"], 2))
        reg = _reg([_comp(superficies=[sup], estado=azar.choice(["RESOLVED", "UNRESOLVED"]))],
                   [_clase(valor=azar.choice(["PRIVATE", "NOT_PRIVATE", "UNRESOLVED"]))],
                   azar.choice(["QA", None, "DEV", "PRD"]))
        evid = EVIDENCIA + [_fuga(), _aut(), _prueba(environment=azar.choice(["QA", "PRD"]))]
        entradas.append(_caso(reg, azar.sample(evid, azar.randint(0, len(evid)))))
    vistos = set()
    for i, caso in enumerate(entradas):
        r = CHECK.evaluar(caso)
        vistos.add(r["state"])
        t.verdadero("E-04 entrada %d no es NOT_APPLICABLE" % i,
                    r["state"] != "NOT_APPLICABLE" and "NOT_APPLICABLE" not in r["states"])
        t.verdadero("E-04 entrada %d tampoco en seguridad" % i,
                    _vu7_en_seguridad(r)["result"] != "NOT_APPLICABLE")
    t.verdadero("E-04 el barrido paso por estados distintos", len(vistos) >= 4)
    t.igual("E-04 sin evidencia, seguridad dice que aplica", "APPLICABLE",
            seguridad.resultado("Vu7", {}, {}, MATRIZ)["applicability"])


def test_e05_el_registro_vacio(t):
    """E-05."""
    instalado = CHECK.evaluar({})
    t.igual("E-05 el registro instalado da inventario sin resolver", INV, instalado["state"])
    t.igual("E-05 y lo leyo vacio", [], instalado["coverage"]["registered"])
    t.igual("E-05 un registro vacio explicito tambien", INV, _estado(_reg([], [])))
    t.igual("E-05 aunque traiga ambiente", INV, _estado(_reg([], [], "QA")))
    t.igual("E-05 y con toda la evidencia suelta", INV, _estado(_reg([], []), EVIDENCIA))
    t.igual("E-05 en seguridad no cumple", "UNRESOLVED", _vu7_en_seguridad(instalado)["result"])


# -- El inventario y las superficies ---------------------------------------------------

def test_e06_un_componente_del_inventario_sin_entrada(t):
    """E-06."""
    r = _r(evidencia=_sin("inv", _inv([COMP, "base-de-datos"])))
    t.igual("E-06 inventario sin resolver", INV, r["state"])
    t.igual("E-06 y nombra el que falta", ["base-de-datos"], r["coverage"]["missingComponents"])
    t.igual("E-06 aunque la superficie cumpla", "PASS", _s(r)["state"])
    t.igual("E-06 con la entrada, pasa", "PASS", _con_otro()["state"])


def test_e07_sin_inventario_autoritativo(t):
    """E-07."""
    for nombre, evid in (("sin ninguna", _sin("inv")),
                         ("sin citarla", EVIDENCIA),
                         ("de un README", _sin("inv", _inv(fuente="README_STATEMENT"))),
                         ("del codigo", _sin("inv", _inv(fuente="SOURCE_CODE"))),
                         ("de otro ambiente", _sin("inv", _inv(environment="DEV")))):
        registro = _reg([_comp(evidencia=["alc"])]) if nombre == "sin citarla" else None
        r = _r(registro, evid)
        t.igual("E-07 %s el inventario no esta entero" % nombre, INV, r["state"])
        t.igual("E-07 %s y no hay evidencia de inventario" % nombre, [],
                r["coverage"]["inventoryEvidence"])
    t.igual("E-07 sin ambiente propio, la de inventario vale", "PASS", _estado())


def test_e08_una_superficie_del_alcance_sin_entrada(t):
    """E-08."""
    r = _r(evidencia=_sin("alc", _alc([SUP, "backups"])))
    t.igual("E-08 cobertura sin resolver", COB, r["state"])
    t.igual("E-08 y nombra la que falta", ["%s/backups" % COMP], r["coverage"]["missingSurfaces"])
    t.igual("E-08 sin alcance citado tambien", COB,
            _estado(_reg([_comp(evidencia=["inv"])])))
    t.igual("E-08 de una fuente que no sostiene tampoco", COB,
            _estado(evidencia=_sin("alc", _alc(fuente="PRODUCT_DOCUMENTATION"))))
    t.igual("E-08 el alcance de otro componente no cubre este", COB,
            _estado(evidencia=_sin("alc", _alc(comp="otro"))))


def test_e09_lo_que_esta_afuera(t):
    """E-09."""
    comp, evid = _otro()
    afuera = _r(_reg([_comp(), comp]), EVIDENCIA + evid)
    t.igual("E-09 un componente fuera del inventario impide el PASS", INV, afuera["state"])
    t.igual("E-09 se evalua igual", "PASS", _s(afuera, "base-de-datos", "consola")["state"])
    t.igual("E-09 y dice que esta afuera", False, _c(afuera, "base-de-datos")["inInventory"])
    t.igual("E-09 y se informa", ["base-de-datos"], afuera["coverage"]["componentsOutsideInventory"])
    t.verdadero("E-09 y no es FAIL", afuera["state"] not in FALLAS)
    extra = _sup("admin", evidencia=["ent-admin"])
    fuera = _r(_reg([_comp(superficies=[_sup(), extra])]),
               EVIDENCIA + [_ent("ent-admin", sup="admin")])
    t.igual("E-09 una superficie fuera del alcance impide el PASS", COB, fuera["state"])
    t.igual("E-09 se evalua igual", "PASS", _s(fuera, sid="admin")["state"])
    t.igual("E-09 y dice que esta afuera", False, _s(fuera, sid="admin")["inScope"])
    t.igual("E-09 y se informa", ["%s/admin" % COMP], fuera["coverage"]["surfacesOutsideScope"])
    t.verdadero("E-09 y no es FAIL", fuera["state"] not in FALLAS)
    for nombre, r in (("afuera", afuera), ("fuera", fuera)):
        t.igual("E-09 en seguridad no cumple (%s)" % nombre, "UNRESOLVED", _vu7_en_seguridad(r)["result"])
    comp2, evid2 = _otro(valor=FUGA)
    t.igual("E-09 afuera no tapa su propia fuga", FUGA,
            _estado(_reg([_comp(), comp2], [_clase()]), EVIDENCIA + evid2))


def test_e10_ninguna_lista_de_productos(t):
    """E-10."""
    base = _json(_r())
    for tipo, producto in (("REVERSE_PROXY", "otro-producto"), ("APPLICATION_SERVER", None),
                           ("DATABASE_ENGINE", "motor-x")):
        t.igual("E-10 %s / %s da el mismo resultado entero" % (tipo, producto), base,
                _json(_r(_reg([_comp(tipo=tipo, producto=producto)]))))
    falla = _json(_con_ademas(_fuga()))
    t.igual("E-10 tambien cuando falla", falla, _json(CHECK.evaluar(_caso(
        _reg([_comp(tipo="CACHE", producto="cache-y",
                    superficies=[_sup(evidencia=["efectiva", "fuga"])])]),
        EVIDENCIA + [_fuga()]))))
    literales = {s.lower() for s in _literales()}
    for nombre in ("nginx", "apache", "tomcat", "jboss", "wildfly", "iis", "postgres", "mysql",
                   "oracle", "redis", "rabbitmq", "kafka", "openshift", "kubernetes", "actuator",
                   "phpmyadmin", "web_server", "database", "/status", ".bak"):
        t.verdadero("E-10 ninguna literal nombra `%s`" % nombre,
                    not [s for s in literales if nombre in s])
    t.verdadero("E-10 nadie lee `componentType` ni `productRef`",
                not {"componentType", "productRef", "surfaceType"} & _literales())


# -- La clasificacion ----------------------------------------------------------------

def test_e11_una_clase_privada_sin_clasificacion(t):
    """E-11."""
    for nombre, clases, evid in (
            ("sin citar", [_clase(evidencia=[])], EVIDENCIA),
            ("sin evidencia", [_clase()], _sin("clasif")),
            ("de un README", [_clase()], _sin("clasif", _clasif(fuente="README_STATEMENT"))),
            ("de la metadata de la infraestructura", [_clase()],
             _sin("clasif", _clasif(fuente="EFFECTIVE_CONFIGURATION"))),
            ("con otro valor", [_clase()], _sin("clasif", _clasif(valor="NOT_PRIVATE"))),
            ("de otra clase", [_clase()], _sin("clasif", _clasif(clase="otra")))):
        r = _r(_reg(clases=clases), evid)
        t.igual("E-11 %s: la superficie queda sin clasificar" % nombre, CLASE, _s(r)["state"])
        t.igual("E-11 %s: y el agregado" % nombre, CLASE, r["state"])
    r = _r(_reg(clases=[_clase(evidencia=[])]))
    t.igual("E-11 la clase dice por que", (None, "PRIVATE_DATA_CLASSIFICATION_UNRESOLVED"),
            (r["dataClasses"][0]["resolved"], r["dataClasses"][0]["state"]))
    t.igual("E-11 una clase que no esta declarada tampoco", CLASE,
            _s(_r(_reg([_comp(superficies=[_sup(refs=["no-declarada"])])])))["state"])
    t.igual("E-11 con la clasificacion citada, pasa", "PASS", _estado())
    for nombre, contra in (("no citada", _clasif(valor="NOT_PRIVATE", eid="contra")),
                           ("de arquitectura", _clasif(valor="NOT_PRIVATE", eid="contra",
                                                       fuente="ARCHITECTURE_DOCUMENTATION"))):
        r = _r(evidencia=EVIDENCIA + [contra])
        t.igual("E-11 una autoritativa %s que dice otro valor la deja sin resolver" % nombre, CLASE,
                _s(r)["state"])
        t.igual("E-11 y queda contradicha (%s)" % nombre, ["contra"], r["dataClasses"][0]["contradictedBy"])
    t.igual("E-11 una no autoritativa que dice otro valor no mueve nada", "PASS",
            _estado(evidencia=EVIDENCIA + [_clasif(valor="NOT_PRIVATE", eid="contra",
                                                   fuente="README_STATEMENT")]))
    t.igual("E-11 una de otra clase no mueve nada", "PASS",
            _estado(evidencia=EVIDENCIA + [_clasif("otra", "NOT_PRIVATE", "contra")]))


def test_e12_un_nombre_no_clasifica(t):
    """E-12."""
    for clase in ("dni", "cuit", "password", "tarjeta_credito", "cbu", "email"):
        for nombre, clases in (("declarada sin resolver", [_clase(clase, "UNRESOLVED", [])]),
                               ("sin declarar", [])):
            r = _r(_reg([_comp(superficies=[_sup(refs=[clase], ctx="PUBLIC", resultado=FUGA,
                                                 evidencia=["fuga"])])], clases),
                   _sin("efectiva", _fuga()))
            t.igual("E-12 `%s` %s no es privada: sin resolver" % (clase, nombre), CLASE, r["state"])
            t.verdadero("E-12 `%s` %s nunca FAIL" % (clase, nombre), r["state"] not in FALLAS)
    literales = {s.lower() for s in _literales()}
    for palabra in ("dni", "cuit", "cuil", "password", "email", "tarjeta", "telefono", ".sql", ".bak",
                    ".env", "personal"):
        t.verdadero("E-12 ninguna literal busca `%s`" % palabra,
                    not [s for s in literales if palabra in s and len(s) < 20 and "_" not in s])
    importados = {a.name for n in ast.walk(_arbol()) if isinstance(n, ast.Import) for a in n.names}
    t.verdadero("E-12 el modulo no importa `re`", "re" not in importados)


def test_e13_una_fuga_de_datos_no_privados(t):
    """E-13."""
    clases = [_clase(valor="NOT_PRIVATE")]
    evid = _sin("clasif", _clasif(valor="NOT_PRIVATE"))
    r = _r(_reg([_comp(superficies=[_sup(evidencia=["efectiva", "fuga"])])], clases),
           evid + [_fuga()])
    t.igual("E-13 no es FAIL: los datos no son privados", "PASS", r["state"])
    t.igual("E-13 y queda anotada aparte", ["fuga"], _s(r)["notPrivateDisclosure"])
    t.igual("E-13 no se usa como fuga", [], _s(r)["evidenceUsed"]["disclosure"])
    honesta = _r(_reg([_comp(superficies=[_sup(resultado=FUGA, evidencia=["fuga"])])], clases),
                 evid + [_fuga()])
    t.verdadero("E-13 declarada como fuga, tampoco es FAIL", honesta["state"] not in FALLAS)
    t.igual("E-13 con la clase PRIVATE, la misma evidencia si es FAIL", FUGA,
            _con_ademas(_fuga())["state"])


# -- La configuracion efectiva y el ambiente -----------------------------------------------

def test_e14_la_configuracion_sin_resolver(t):
    """E-14."""
    r = _r(_reg([_comp(estado="UNRESOLVED")]))
    t.igual("E-14 la superficie", CONF, _s(r)["state"])
    t.igual("E-14 el agregado", CONF, r["state"])
    t.igual("E-14 un componente sin superficies tambien", CONF,
            _estado(_reg([_comp(estado="UNRESOLVED", superficies=[])]),
                    _sin("alc", _alc([]))))
    t.igual("E-14 resuelto y sin superficies, pasa", "PASS",
            _estado(_reg([_comp(superficies=[])]), _sin("alc", _alc([]))))


def test_e15_el_default_del_repositorio_solo(t):
    """E-15."""
    defecto = _ent("defecto", fuente="REPOSITORY_DEFAULT_CONFIGURATION")
    r = _solo_con(defecto)
    t.igual("E-15 no cumple", CONF, r["state"])
    t.igual("E-15 no sostiene nada", [], _s(r)["evidenceUsed"]["noDisclosure"])
    t.igual("E-15 y se informa como insuficiente", ["defecto"], _s(r)["insufficient"])
    t.igual("E-15 sin ambiente tampoco", CONF,
            _solo_con(_ent("defecto", ambiente=None,
                           fuente="REPOSITORY_DEFAULT_CONFIGURATION"))["state"])


def test_e16_el_override_le_gana_al_default(t):
    """E-16."""
    defecto = _ent("defecto", fuente="REPOSITORY_DEFAULT_CONFIGURATION")
    override = _fuga("override", fuente="ENVIRONMENT_OVERRIDE")
    r = _solo_con(defecto, override)
    t.igual("E-16 FAIL", FUGA, r["state"])
    t.igual("E-16 con el override", ["override"], _s(r)["evidenceUsed"]["disclosure"])
    t.igual("E-16 y el default no pesa", ["defecto"], _s(r)["insufficient"])
    t.igual("E-16 en seguridad es FAIL", "NON_COMPLIANT", _vu7_en_seguridad(r)["result"])
    t.igual("E-16 un default que dice que hay fuga no es FAIL", CONF,
            _solo_con(_fuga("d", fuente="REPOSITORY_DEFAULT_CONFIGURATION"))["state"])


def test_e17_dev_no_prueba_qa(t):
    """E-17."""
    dev = _ent("dev", ambiente="DEV")
    r = _solo_con(dev)
    t.igual("E-17 una EFFECTIVE_CONFIGURATION de DEV no sostiene QA", CONF, r["state"])
    t.igual("E-17 y se informa", ["dev"], _s(r)["otherEnvironment"])
    t.igual("E-17 sin ambiente propio tampoco", CONF, _solo_con(_ent("sin", ambiente=None))["state"])
    t.igual("E-17 una fuga de DEV no es FAIL en QA", CONF, _honesta(_fuga(ambiente="DEV"))["state"])
    t.igual("E-17 en un registro de DEV la misma cumple", "PASS",
            _r(_reg([_comp(superficies=[_sup(evidencia=["dev"])])], ambiente="DEV"),
               _sin("efectiva", dev))["state"])
    t.igual("E-17 el ambiente se compara en NFC", "PASS",
            _r(_reg(ambiente=unicodedata.normalize("NFD", "PRUEBAÑ")),
               _sin("efectiva", _ent(ambiente=unicodedata.normalize("NFC", "PRUEBAÑ"))))["state"])


def test_e18_sin_ambiente(t):
    """E-18."""
    dos = [_comp(superficies=[_sup(), _sup("backups", evidencia=["ent-b"])])]
    evid = _sin("alc", _alc([SUP, "backups"]), _ent("ent-b", sup="backups", ambiente=None),
                _ent("ent-n", ambiente=None))
    r = _r(_reg(dos, ambiente=None), evid)
    for sid in (SUP, "backups"):
        t.igual("E-18 %s sin resolver" % sid, CONF, _s(r, sid=sid)["state"])
    t.igual("E-18 el agregado", CONF, r["state"])
    t.igual("E-18 con la clase sin resolver, igual", CONF,
            _s(_r(_reg(ambiente=None, clases=[_clase(evidencia=[])])))["state"])
    t.igual("E-18 una fuga sin ambiente no hace FAIL", CONF,
            _r(_reg([_comp(superficies=[_sup(resultado=FUGA, ctx="UNAUTHORIZED",
                                             evidencia=["f"])])], ambiente=None),
               _sin("efectiva", _fuga("f", ambiente=None)))["state"])
    blanco = _r(_reg(ambiente="  "), _sin("efectiva", _ent(ambiente="  ")))
    t.igual("E-18 un ambiente en blanco es nulo, tambien contra una evidencia en blanco", (CONF, None),
            (blanco["state"], blanco["environment"]))
    t.igual("E-18 la salida dice que no hay ambiente", None, r["environment"])


def test_e19_el_codigo_solo(t):
    """E-19."""
    codigo = _ent("codigo", fuente="SOURCE_CODE")
    t.igual("E-19 no cumple", CONF, _solo_con(codigo)["state"])
    t.igual("E-19 y es insuficiente", ["codigo"], _s(_solo_con(codigo))["insufficient"])
    t.igual("E-19 tampoco hace FAIL", CONF, _honesta(_fuga("codigo", fuente="SOURCE_CODE"))["state"])
    for fuente in ("PRODUCT_DOCUMENTATION", "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT"):
        t.igual("E-19 %s tampoco" % fuente, CONF, _solo_con(_ent("x", fuente=fuente))["state"])


# -- La fuga y el acceso autorizado ------------------------------------------------------

def test_e20_la_fuga_a_un_no_autorizado(t):
    """E-20."""
    r = _honesta(_fuga())
    t.igual("E-20 UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE", FUGA, r["state"])
    t.igual("E-20 la superficie", FUGA, _s(r)["state"])
    t.igual("E-20 con su evidencia", ["fuga"], _s(r)["evidenceUsed"]["disclosure"])
    t.igual("E-20 y FAIL en seguridad", "NON_COMPLIANT", _vu7_en_seguridad(r)["result"])
    t.igual("E-20 los dos controles en FAIL", {"FAIL"},
            {v["result"] for v in CHECK.para_seguridad(r)[0]["controlResults"].values()})
    t.verdadero("E-20 y no aprueba", not CHECK.aprueba(r))
    for fuente in ("EFFECTIVE_CONFIGURATION", "DEPLOYED_MANIFEST", "CONFIGURATION_TEST",
                   "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE"):
        t.igual("E-20 establecida por %s" % fuente, FUGA,
                _honesta(_fuga("f", fuente=fuente))["state"])
    t.igual("E-20 sin citarla no es FAIL", CONF,
            _r(_reg([_comp(superficies=[_sup(resultado=FUGA, ctx="UNAUTHORIZED", evidencia=[])])]),
               EVIDENCIA + [_fuga()])["state"])


def test_e21_la_fuga_publica(t):
    """E-21."""
    r = _honesta(_fuga(), ctx="PUBLIC")
    t.igual("E-21 PUBLIC tambien es fuga", FUGA, r["state"])
    t.igual("E-21 FAIL en seguridad", "NON_COMPLIANT", _vu7_en_seguridad(r)["result"])


def test_e22_el_acceso_autorizado(t):
    """E-22."""
    r = _solo_con(_aut(), ctx="AUTHORIZED", resultado=ACCESO)
    t.igual("E-22 cumple", "PASS", r["state"])
    t.igual("E-22 con su contexto", ["aut"], _s(r)["evidenceUsed"]["authorization"])
    t.verdadero("E-22 y no es fuga", FUGA not in r["states"])
    t.igual("E-22 en seguridad cumple", "COMPLIANT", _vu7_en_seguridad(r)["result"])
    for fuente in ("ARCHITECTURE_DOCUMENTATION", "EFFECTIVE_CONFIGURATION", "PROJECT_CONTRACT"):
        t.igual("E-22 el contexto por %s" % fuente, "PASS",
                _solo_con(_aut(fuente=fuente), ctx="AUTHORIZED", resultado=ACCESO)["state"])
    t.igual("E-22 el mismo dato a un anonimo es fuga", FUGA, _honesta(_fuga(), ctx="PUBLIC")["state"])


def test_e23_el_acceso_autorizado_sin_contexto(t):
    """E-23."""
    for nombre, evid, ctx in (("sin evidencia", [], "AUTHORIZED"),
                              ("de un README", [_aut(fuente="README_STATEMENT")], "AUTHORIZED"),
                              ("de otro ambiente", [_aut(ambiente="DEV")], "AUTHORIZED"),
                              ("de otra superficie", [_aut(sup="otra")], "AUTHORIZED"),
                              ("con el contexto en UNRESOLVED", [_aut()], "UNRESOLVED"),
                              ("con el contexto en PUBLIC", [_aut()], "PUBLIC")):
        r = _solo_con(*evid, ctx=ctx, resultado=ACCESO)
        t.igual("E-23 %s no cumple" % nombre, CONF, r["state"])
        t.igual("E-23 %s no sostiene nada" % nombre, [], _s(r)["evidenceUsed"]["authorization"])
    t.igual("E-23 con una que dice UNAUTHORIZED, tampoco", CONF,
            _solo_con(_aut(), _aut("no", "UNAUTHORIZED"), ctx="AUTHORIZED", resultado=ACCESO)["state"])
    t.igual("E-23 ni con una no citada que lo dice", CONF,
            _r(_reg([_comp(superficies=[_sup(ctx="AUTHORIZED", resultado=ACCESO, evidencia=["aut"])])]),
               EVIDENCIA + [_aut(), _aut("no", "PUBLIC")])["state"])


def test_e24_sin_fuga_con_la_configuracion_efectiva(t):
    """E-24."""
    r = _r()
    t.igual("E-24 PASS", "PASS", r["state"])
    t.igual("E-24 la superficie cumple", "PASS", _s(r)["state"])
    t.igual("E-24 con su configuracion efectiva", ["efectiva"], _s(r)["evidenceUsed"]["noDisclosure"])
    t.verdadero("E-24 aprueba", CHECK.aprueba(r))
    t.igual("E-24 y en seguridad cumple", "COMPLIANT", _vu7_en_seguridad(r)["result"])
    t.igual("E-24 sin citarla, no", CONF, _estado(_reg([_comp(superficies=[_sup(evidencia=[])])])))
    for fuente in ("DEPLOYED_MANIFEST", "ENVIRONMENT_OVERRIDE", "CONFIGURATION_TEST",
                   "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE"):
        t.igual("E-24 por %s tambien" % fuente, "PASS", _solo_con(_ent("x", fuente=fuente))["state"])


def test_e25_el_tipo_de_superficie_no_decide(t):
    """E-25."""
    def con(tipo, *evid, **k):
        ids = [x["evidenceId"] for x in evid]
        return _r(_reg([_comp(superficies=[_sup(tipo=tipo, evidencia=ids, **k)])]),
                  _sin("efectiva", *evid))
    tipos = ("DIRECTORY_LISTING", "BACKUP_FILE_EXPOSURE", "ADMIN_INTERFACE", "STATUS_ENDPOINT", None)
    for nombre, evid, k, esperado in (("cumple", [EFECTIVA], {}, "PASS"),
                                      ("falla", [_fuga()], {"resultado": FUGA}, FUGA),
                                      ("sin resolver", [], {}, CONF)):
        base = _json(con(tipos[0], *evid, **k))
        t.igual("E-25 %s: %s" % (nombre, tipos[0]), esperado, con(tipos[0], *evid, **k)["state"])
        for tipo in tipos[1:]:
            t.igual("E-25 %s: %s da el mismo resultado entero" % (nombre, tipo), base,
                    _json(con(tipo, *evid, **k)))


# -- El banner, el nombre y el error ----------------------------------------------------

def test_e26_el_banner_de_version(t):
    """E-26."""
    banner = _fuga("banner", fuente="VERSION_BANNER")
    r = _honesta(banner)
    t.verdadero("E-26 un VERSION_BANNER que dice fuga no hace FAIL", r["state"] not in FALLAS)
    t.igual("E-26 y no sostiene nada", ([], ["banner"]),
            (_s(r)["evidenceUsed"]["disclosure"], _s(r)["insufficient"]))
    t.igual("E-26 citado junto a la configuracion efectiva, no mueve nada", "PASS",
            _con_ademas(banner)["state"])
    t.igual("E-26 solo, no cumple", CONF, _solo_con(_ent("banner", fuente="VERSION_BANNER"))["state"])
    t.igual("E-26 salvo que una evidencia que sostiene establezca la entrega de una clase privada",
            FUGA, _honesta(_fuga("prueba-banner", fuente="CONFIGURATION_TEST"))["state"])


def test_e27_el_nombre_del_endpoint(t):
    """E-27."""
    actuator = _fuga("actuator", fuente="ENDPOINT_NAME", reference="/actuator")
    r = _honesta(actuator)
    t.verdadero("E-27 `/actuator`, solo, no hace FAIL", r["state"] not in FALLAS)
    t.igual("E-27 ni cumple", CONF,
            _solo_con(_ent("actuator", fuente="ENDPOINT_NAME", reference="/actuator"))["state"])
    t.igual("E-27 y se informa como insuficiente", ["actuator"], _s(r)["insufficient"])
    t.igual("E-27 el nombre de la superficie tampoco decide", "PASS",
            _r(_reg([_comp(superficies=[_sup("/actuator", evidencia=["e"])])]),
               [INVENTARIO, _alc(["/actuator"]), CLASIF, _ent("e", sup="/actuator")])["state"])


def test_e28_vu6_no_entra_ni_sale(t):
    """E-28."""
    compartida = _fuga("error-500", fuente="CONFIGURATION_TEST")
    r = _honesta(compartida)
    t.igual("E-28 Vu7 con la evidencia compartida", FUGA, r["state"])
    vu6 = VU6.evaluar({"evidence": [dict(compartida)]})
    for nombre, caso in (("un resultado de Vu6", dict(_caso(_reg([_comp(superficies=[
                              _sup(resultado=FUGA, ctx="UNAUTHORIZED", evidencia=["error-500"])])]),
                              _sin("efectiva", compartida)), **{"ES0902.Vu6": vu6, "vu6": vu6})),
                         ("un Vu6 en PASS", dict(_caso(_reg([_comp(superficies=[
                              _sup(resultado=FUGA, ctx="UNAUTHORIZED", evidencia=["error-500"])])]),
                              _sin("efectiva", compartida)),
                              **{"ES0902.Vu6": dict(vu6, state="PASS")}))):
        t.igual("E-28 %s no entra" % nombre, _json(r), _json(CHECK.evaluar(caso)))
    t.igual("E-28 evaluar no recibe resultados de otra regla", ["caso", "desde"],
            list(inspect.signature(CHECK.evaluar).parameters))
    ev, _ = CHECK.para_seguridad(r)
    t.igual("E-28 lo que sale va solo a los controles de Vu7",
            ["base-software-data-disclosure-configuration",
             "base-software-private-data-disclosure-prohibited"], sorted(ev["controlResults"]))
    sin = seguridad.resultado("Vu6", {}, {"userFacingErrorPresent": True}, MATRIZ)
    con = seguridad.resultado("Vu6", ev, {"userFacingErrorPresent": True}, MATRIZ)
    t.igual("E-28 y no sale hacia Vu6", sin["result"], con["result"])
    t.verdadero("E-28 el modulo no nombra los controles de Vu6",
                not {"custom-error-message-compliance", "custom-error-messages-required",
                     "ES0902.Vu6", "Vu6"} & _literales())


# -- La prueba ---------------------------------------------------------------------

def test_e29_una_prueba_segura_en_qa(t):
    """E-29."""
    r = _solo_con(_prueba())
    t.igual("E-29 cuenta", "PASS", r["state"])
    t.igual("E-29 con la prueba", ["qa"], _s(r)["evidenceUsed"]["noDisclosure"])
    t.igual("E-29 y la prueba segura no tiene motivos", [], CHECK.prueba_segura(_prueba(), "QA"))
    t.igual("E-29 una prueba segura que establece la fuga es FAIL", FUGA,
            _honesta(_prueba(FUGA))["state"])


def test_e30_las_condiciones_inseguras(t):
    """E-30."""
    for nombre, cambios, motivo in (
            ("sin autorizacion", {"authorized": None}, "NOT_AUTHORIZED"),
            ("autorizada en falso", {"authorized": False}, "NOT_AUTHORIZED"),
            ("en produccion", {"environment": "PRD"}, "PRODUCTION"),
            ("en un ambiente desconocido", {"environment": "STAGING"}, "ENVIRONMENT_UNKNOWN"),
            ("sin ambiente", {"environment": None}, "ENVIRONMENT_UNRESOLVED"),
            ("destructiva", {"destructive": True}, "DESTRUCTIVE"),
            ("con datos privados reales", {"realPrivateDataAccessed": True},
             "REAL_PRIVATE_DATA_ACCESSED"),
            ("sin fixtures sinteticos", {"syntheticFixtures": None}, "NOT_SYNTHETIC_FIXTURES"),
            ("con fixtures no sinteticos", {"syntheticFixtures": False}, "NOT_SYNTHETIC_FIXTURES"),
            ("con secretos registrados", {"rawSecretsLogged": True}, "RAW_SECRETS_LOGGED")):
        r = _solo_con(_prueba(**cambios))
        t.igual("E-30 %s" % nombre, INSEGURA, r["state"])
        t.contiene("E-30 %s dice por que" % nombre, motivo, _s(r)["unsafe"])
    for campo in ("destructive", "realPrivateDataAccessed", "rawSecretsLogged"):
        t.igual("E-30 %s en falso cuenta" % campo, "PASS", _solo_con(_prueba(**{campo: False}))["state"])
    for ambiente in ("QA", "DEV", "HML", "OTHER"):
        t.igual("E-30 en %s, en un registro de %s, cuenta" % (ambiente, ambiente), "PASS",
                _r(_reg([_comp(superficies=[_sup(evidencia=["qa"])])], ambiente=ambiente),
                   _sin("efectiva", _prueba(environment=ambiente)))["state"])
    t.igual("E-30 en un registro de PRD ninguna prueba cuenta", INSEGURA,
            _r(_reg([_comp(superficies=[_sup(evidencia=["qa"])])], ambiente="PRD"),
               _sin("efectiva", _prueba(environment="PRD")))["state"])
    importados = set()
    for nodo in ast.walk(_arbol()):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add((nodo.module or "").split(".")[0])
    t.igual("E-30 el modulo no ejecuta nada: ni red ni procesos", [],
            sorted(importados & {"socket", "http", "urllib", "requests", "subprocess", "ssl",
                                 "asyncio", "httpx", "multiprocessing", "selenium", "playwright",
                                 "time", "threading"}))


def test_e31_una_prueba_de_otro_ambiente(t):
    """E-31."""
    for ambiente in ("DEV", "HML", "OTHER"):
        r = _solo_con(_prueba(environment=ambiente))
        t.igual("E-31 una prueba de %s en un registro de QA no cuenta" % ambiente, INSEGURA, r["state"])
        t.contiene("E-31 %s dice por que" % ambiente, "ENVIRONMENT_MISMATCH", _s(r)["unsafe"])
        t.igual("E-31 %s no sostiene nada" % ambiente, [], _s(r)["evidenceUsed"]["noDisclosure"])
    t.igual("E-31 sin ambiente en el registro, tampoco", [
        "ENVIRONMENT_MISMATCH"], CHECK.prueba_segura(_prueba(), None))


def test_e32_una_prueba_insegura_no_es_fail(t):
    """E-32."""
    insegura = _prueba(FUGA, environment="PRD")
    t.igual("E-32 insegura que dice fuga, citada, no es FAIL", INSEGURA, _con_ademas(insegura)["state"])
    t.igual("E-32 y no citada tampoco", INSEGURA, _r(evidencia=EVIDENCIA + [insegura])["state"])
    t.igual("E-32 con la fuga declarada en el registro tampoco", INSEGURA, _honesta(insegura)["state"])
    t.igual("E-32 sin objetivo que dice fuga no es FAIL", SIN_OBJ,
            _con_ademas(_prueba(FUGA, outcome="UNAVAILABLE"))["state"])
    t.igual("E-32 sin objetivo, sola", SIN_OBJ, _solo_con(_prueba(outcome="UNAVAILABLE"))["state"])
    t.igual("E-32 en seguridad no es FAIL", "UNRESOLVED",
            _vu7_en_seguridad(_honesta(insegura))["result"])
    # Del mismo ambiente que el registro: lo unico que la deja afuera es que es insegura, y no el
    # ambiente (rojo visto: con PRD sola el test pasaba por la ligadura al ambiente).
    for campo in ("destructive", "realPrivateDataAccessed", "rawSecretsLogged"):
        en_qa = _prueba(FUGA, **{campo: True})
        t.igual("E-32 insegura en QA por `%s` que dice fuga, citada, no es FAIL" % campo, INSEGURA,
                _honesta(en_qa)["state"])
        t.igual("E-32 y no sostiene la fuga (%s)" % campo, [],
                _s(_honesta(en_qa))["evidenceUsed"]["disclosure"])
    t.igual("E-32 sin fixtures sinteticos en QA, tampoco", INSEGURA,
            _honesta(_prueba(FUGA, syntheticFixtures=False))["state"])


# -- La evidencia y la salida -------------------------------------------------------------

def test_e33_ningun_texto_ni_muestra_sale(t):
    """E-33."""
    texto = "respuesta con DNI 30111222 de Juan Perez, calle Falsa 123, /var/backups/db.sql"
    muestra = dict(_fuga("con-muestra"), sample="30111222 Juan Perez")
    casos = {"pasa": _r(evidencia=[dict(x, reference=texto) for x in EVIDENCIA]),
             "falla": _honesta(dict(_fuga(), reference=texto)),
             "no citada": _r(evidencia=EVIDENCIA + [dict(_fuga(), reference=texto)]),
             "con muestra": _honesta(muestra)}
    unidad = {n: _unidad(r) for n, r in casos.items()}
    carpeta = tempfile.mkdtemp(prefix="vu7_33_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-7033")
        for i, r in enumerate(casos.values()):
            for evento in prod.desde_regla(_vu7_en_seguridad(r), "GCBA-7033",
                                           {"project": "Sistema", "environment": "QA"},
                                           "2026-09-24T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        en_el_libro = Path(ruta).read_text(encoding="utf-8")
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    for trozo in ("30111222", "Juan Perez", "Falsa 123", "/var/backups", "db.sql", "ref-"):
        for nombre, r in casos.items():
            t.no_contiene("E-33 `%s` no sale en la salida (%s)" % (trozo, nombre), trozo, _json(r))
            t.no_contiene("E-33 `%s` no sale en rules.Vu7 (%s)" % (trozo, nombre), trozo,
                          _json(unidad[nombre]))
        t.no_contiene("E-33 `%s` no llega al libro" % trozo, trozo, en_el_libro)
    t.igual("E-33 una muestra deja el item mal formado, y no hace FAIL", CONF,
            casos["con muestra"]["state"])
    t.contiene("E-33 y se nombra por su id", "con-muestra", " ".join(casos["con muestra"]["issues"]))
    t.igual("E-33 solo su id", ["fuga"], _s(casos["falla"])["evidenceUsed"]["disclosure"])
    t.contiene("E-33 y el id llega a la unidad", "fuga", unidad["falla"]["evidence"])
    for campo in ("sample", "value", "redactedSample", "fingerprint", "rawValue"):
        t.verdadero("E-33 el registro no acepta `%s` en una superficie" % campo,
                    bool(CHECK.validar_schema(dict(_reg(), components=[dict(_comp(), surfaces=[
                        dict(_sup(), **{campo: "30111222"})])]))))


CREDENCIALES = ("password=hunter2abc", "contraseña=hunter2abc", "clave: hunter2abc",
                "access_token=hunter2abc", "api_key=hunter2abc", "Bearer abcdefghhunter2abc",
                "JSESSIONID=hunter2abc", "Cookie: SESSION=hunter2abc", "code=hunter2abc",
                "https://usuario:hunter2abc@db.example")


def test_e34_ningun_secreto(t):
    """E-34."""
    base_claves = set(_claves(_r()))
    base_unidad = set(_claves(_unidad(_r())))
    for texto in CREDENCIALES:
        casos = {
            "un componentId": _r(_reg([_comp(), _comp(texto)])),
            "un surfaceId": _r(_reg([_comp(superficies=[_sup(), _sup(texto)])])),
            "un dataClassId": _r(_reg([_comp(superficies=[_sup(refs=[texto])])],
                                      [_clase(), _clase(texto)])),
            "un id de evidencia citado": _r(_reg([_comp(superficies=[_sup(evidencia=[texto])])]),
                                            _sin("efectiva", _ent(texto))),
            "el ambiente": _r(_reg(ambiente=texto)),
            "el deploymentBinding": _r(_reg(enlace=texto)),
            "rules.Vu7": _unidad(_r(_reg([_comp(texto)]))),
            "rules.Vu7 por la evidencia": _unidad(_r(_reg([_comp(superficies=[_sup(
                evidencia=[texto])])]), _sin("efectiva", _ent(texto)))),
            "rules.Vu7 por el ambiente": _unidad(_r(_reg(ambiente=texto))),
            "seguridad": CHECK.para_seguridad(_r(_reg([_comp(superficies=[_sup(evidencia=[texto])])]),
                                                 _sin("efectiva", _ent(texto))))[0],
        }
        for nombre, r in casos.items():
            t.no_contiene("E-34 `%s` en %s no sale" % (texto, nombre), "hunter2", _json(r))
        for nombre in ("un componentId", "un surfaceId", "un dataClassId", "un id de evidencia citado",
                       "el ambiente", "el deploymentBinding"):
            t.igual("E-34 con `%s` en %s ninguna clave nueva" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_claves)
        for nombre in ("rules.Vu7", "rules.Vu7 por la evidencia", "rules.Vu7 por el ambiente"):
            t.igual("E-34 con `%s` ninguna clave nueva en %s" % (texto, nombre), set(),
                    set(_claves(casos[nombre])) - base_unidad)
    lib = _cargar(CONTROLES / "lib" / "evidencia.py", "vu7_lib")
    t.igual("E-34 la regla de salida redacta las claves", {"[redactado]": 1},
            lib.depurar({"password=hunter2abc": 1}))
    t.verdadero("E-34 la regla de salida es la de la lib, no una copia",
                "SECRETOS" not in {n.id for n in ast.walk(_arbol()) if isinstance(n, ast.Name)}
                and CHECK._ev.__file__.endswith("evidencia.py"))
    for campo in ("password", "token", "secretValue", "realValue"):
        t.igual("E-34 un item con `%s` no cuenta" % campo, CONF,
                _estado(evidencia=_sin("efectiva", dict(EFECTIVA, **{campo: "abc"}))))


def test_e35_el_schema_cerrado(t):
    """E-35."""
    instalado = json.loads((REGLAS / "base-software-data-disclosure.json").read_text(encoding="utf-8"))
    t.igual("E-35 el registro se instala vacio",
            {"version": "1.0", "environment": None, "deploymentBinding": None, "dataClasses": [],
             "components": []}, instalado)
    t.igual("E-35 y valida", [], CHECK.validar_schema(instalado))
    t.igual("E-35 el registro base valida", [], CHECK.validar_schema(_reg()))
    capas = {"la raiz": lambda d: d.update(extra=1),
             "una clase": lambda d: d["dataClasses"][0].update(extra=1),
             "un componente": lambda d: d["components"][0].update(extra=1),
             "una superficie": lambda d: d["components"][0]["surfaces"][0].update(extra=1)}
    for nombre, cambiar in capas.items():
        doc = _reg()
        cambiar(doc)
        t.verdadero("E-35 una clave de mas en %s no valida" % nombre, bool(CHECK.validar_schema(doc)))
        r = CHECK.evaluar(dict(_caso(), registry=doc))
        t.verdadero("E-35 y el check no pasa con ese registro (%s)" % nombre, r["state"] != "PASS")
        t.contiene("E-35 y dice por que (%s)" % nombre, "no valida contra su schema",
                   " ".join(r["issues"]))
    esquema = json.loads((SCHEMAS / "base-software-data-disclosure.schema.json").read_text(
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
    t.igual("E-35 cuatro capas de objeto", 4, len(capas_del_schema))
    t.verdadero("E-35 todas cerradas",
                all(c.get("additionalProperties") is False for c in capas_del_schema))


# -- Las reglas de siempre ---------------------------------------------------------------

def test_e36_lo_ilegible(t):
    """E-36."""
    for nombre, eid in (("una lista", ["x"]), ("un dict", {"k": "v"}), ("un numero", 7)):
        for forma, item in (("suelto", {"evidenceId": eid, "surfaces": [SUP]}),
                            ("con forma de fuga", dict(_fuga(), evidenceId=eid)),
                            ("sobre el componente", {"evidenceId": eid, "components": [COMP]})):
            t.igual("E-36 un id que es %s (%s) impide el PASS sin romper" % (nombre, forma),
                    CONF, _sin_excepcion(lambda: _estado(evidencia=EVIDENCIA + [item])))
    mal = dict(_fuga("mal"), outcome=["X"])
    t.igual("E-36 una mal formada no citada", CONF, _estado(evidencia=EVIDENCIA + [mal]))
    t.igual("E-36 una mal formada citada", CONF, _con_ademas(mal)["state"])
    rep = _fuga("rep")
    t.igual("E-36 una repetida no citada", CONF, _estado(evidencia=EVIDENCIA + [rep, copy.deepcopy(rep)]))
    t.igual("E-36 un id citado que no esta en el catalogo", CONF,
            _estado(_reg([_comp(superficies=[_sup(evidencia=["efectiva", "fantasma"])])])))
    t.igual("E-36 citado desde el componente tambien", CONF,
            _estado(_reg([_comp(evidencia=["inv", "alc", "fantasma"], superficies=[])]),
                    _sin("alc", _alc([]))))
    sobre = _r(evidencia=EVIDENCIA + [{"evidenceId": "m", "components": [COMP], "extra": 1}])
    t.igual("E-36 una ilegible sobre el componente bloquea cada superficie", CONF, _s(sobre)["state"])
    t.igual("E-36 sobre un componente sin superficies", CONF,
            _estado(_reg([_comp(superficies=[])]),
                    _sin("alc", _alc([]), {"evidenceId": "m", "components": [COMP], "extra": 1})))
    t.igual("E-36 una ilegible sobre otra cosa no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_fuga("m", sup="otra", comp="otro"), outcome=1)]))
    t.igual("E-36 una ilegible sobre la clase la deja sin resolver", CLASE,
            _estado(evidencia=EVIDENCIA + [{"evidenceId": "m", "dataClasses": ["ciudadanos"], "x": 1}]))
    for nombre, eid in (("vacio", ""), ("en blanco", "  ")):
        t.igual("E-36 un id %s no cuenta aunque se lo cite" % nombre, CONF,
                _estado(_reg([_comp(superficies=[_sup(evidencia=[eid])])]),
                        _sin("efectiva", dict(EFECTIVA, evidenceId=eid))))
    t.verdadero("E-36 ninguna es FAIL", _estado(evidencia=EVIDENCIA + [mal]) not in FALLAS)
    t.igual("E-36 y no tapa un FAIL", FUGA, _honesta(_fuga(), mal)["state"])


def test_e37_la_falla_establecida_gana_siempre(t):
    """E-37."""
    honesta = _honesta(_fuga())
    for nombre, cambios in (("en NO_PRIVATE_DATA_DISCLOSURE", {"resultado": SIN_FUGA}),
                            ("en UNRESOLVED", {"resultado": "UNRESOLVED"}),
                            ("con el contexto AUTHORIZED sin sostener",
                             {"resultado": ACCESO, "ctx": "AUTHORIZED"}),
                            ("con el contexto sin resolver", {"ctx": "UNRESOLVED"})):
        negada = _solo_con(_fuga(), **cambios)
        t.igual("E-37 el registro %s da el mismo FAIL" % nombre,
                (honesta["state"], _s(honesta)["state"]), (negada["state"], _s(negada)["state"]))
        t.igual("E-37 %s: en seguridad es FAIL" % nombre, "NON_COMPLIANT",
                _vu7_en_seguridad(negada)["result"])
    con = _con_ademas(_fuga())
    t.igual("E-37 con la que dice que no hay fuga tambien citada", FUGA, con["state"])
    t.igual("E-37 y queda contradicha", ["efectiva"], _s(con)["contradictedBy"])
    t.igual("E-37 lo no citado que dice fuga nunca es FAIL", CONF,
            _r(evidencia=EVIDENCIA + [_fuga()])["state"])
    t.igual("E-37 tampoco si nombra solo el componente, y deja la superficie sin resolver", CONF,
            _s(_r(evidencia=EVIDENCIA + [_fuga(sup=None)]))["state"])
    t.igual("E-37 citada y nombrando solo el componente, es FAIL", FUGA,
            _honesta(_fuga(sup=None))["state"])
    t.igual("E-37 una no citada que no nombra nada habla de otra cosa", "PASS",
            _estado(evidencia=EVIDENCIA + [_fuga(sup=None, comp=None)]))
    t.igual("E-37 una que nombra la superficie de otro componente habla de otra cosa", "PASS",
            _estado(evidencia=EVIDENCIA + [_fuga(comp="otro")]))
    t.igual("E-37 citada, tambien", "PASS", _con_ademas(_fuga(comp="otro"))["state"])
    t.igual("E-37 con un contexto AUTHORIZED sostenido, dos cosas establecidas no dan PASS ni FAIL",
            CONF, _solo_con(_fuga(), _aut(), resultado=ACCESO, ctx="AUTHORIZED")["state"])


def test_e38_un_solo_bloqueo(t):
    """E-38."""
    amable = _prueba(environment="PRD")
    t.igual("E-38 una no citada que dice sin fuga no bloquea", "PASS",
            _estado(evidencia=EVIDENCIA + [amable]))
    t.igual("E-38 ni suelta sobre el componente", "PASS",
            _estado(evidencia=EVIDENCIA + [_prueba(environment="PRD", sup=None)]))
    t.igual("E-38 una citada que dice sin fuga impide el PASS", INSEGURA, _con_ademas(amable)["state"])
    bloqueada = _con_ademas(amable)
    t.igual("E-38 la bloquea la superficie", (INSEGURA, [INSEGURA]),
            (_s(bloqueada)["state"], _s(bloqueada)["blockedBy"]))
    t.igual("E-38 y el agregado no la cuenta dos veces", [], bloqueada["blockedBy"])
    t.igual("E-38 una citada desde el componente tambien", INSEGURA,
            _estado(_reg([_comp(evidencia=["inv", "alc", "qa"])]),
                    EVIDENCIA + [_prueba(environment="PRD", sup=None)]))
    crudo = _prueba(FUGA, environment="PRD")
    t.igual("E-38 una no citada que dice fuga impide el PASS", INSEGURA,
            _estado(evidencia=EVIDENCIA + [crudo]))
    t.igual("E-38 suelta sobre el componente, tambien", INSEGURA,
            _estado(evidencia=EVIDENCIA + [_prueba(FUGA, environment="PRD", sup=None)]))
    t.igual("E-38 sobre un componente sin superficies, tambien", INSEGURA,
            _estado(_reg([_comp(superficies=[])]),
                    _sin("alc", _alc([]), _prueba(FUGA, environment="PRD", sup=None))))
    t.igual("E-38 nunca tapa un FAIL", FUGA, _honesta(_fuga(), crudo)["state"])
    t.igual("E-38 una que nombra algo fuera del registro no mueve nada", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_prueba(FUGA, environment="PRD", sup="otra"),
                                                components=["otro"])]))
    abierto = _r(_reg([_comp(estado="UNRESOLVED", superficies=[_sup(evidencia=["efectiva", "qa"])])]),
                 EVIDENCIA + [amable])
    t.igual("E-38 no reemplaza un sin resolver anterior", CONF, _s(abierto)["state"])
    t.contiene("E-38 y el bloqueo queda en states", INSEGURA, _s(abierto)["states"])
    sin_inv = _r(_reg([_comp(evidencia=["alc"])]), EVIDENCIA + [crudo])
    t.igual("E-38 tampoco un inventario sin resolver", INV, sin_inv["state"])
    t.contiene("E-38 con el bloqueo a la vista", INSEGURA, sin_inv["states"])
    t.igual("E-38 un solo paso de bloqueo en el modulo", 1,
            len([n for n in ast.walk(_arbol()) if isinstance(n, ast.FunctionDef)
                 and n.name == "_bloquear"]))
    t.igual("E-38 y lo llaman la superficie y el agregado", ["evaluar", "evaluar_superficie"],
            _llamadores("_bloquear"))


# -- Los limites -----------------------------------------------------------------------

def test_e39_el_pass_de_vu7_no_es_el_de_otras(t):
    """E-39."""
    ev, _ = CHECK.para_seguridad(_r())
    todas = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    for regla in ("Vu6", "C3", "Ve1"):
        fila = seguridad.regla(regla, MATRIZ)
        sin = seguridad.resultado(regla, {}, todas, MATRIZ)
        con = seguridad.resultado(regla, ev, todas, MATRIZ)
        t.igual("E-39 %s no cambia" % regla, sin["result"], con["result"])
        t.verdadero("E-39 %s no cumple" % regla, con["result"] != "COMPLIANT")
        t.igual("E-39 los controles de Vu7 no son los de %s" % regla, [],
                sorted(set(ev["controlResults"]) & set(fila["policies"] + fila["checks"]
                                                        + fila["reviews"])))
    ids = ev["controlResults"][CHECK.CONTROL]["evidence"]
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK",
                                         "evidence": ids})
    t.igual("E-39 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])
    senal = {"userFacingErrorPresent": True, "securityHomologationPresent": True}
    sin = normativa.resolucion(senal)["standards"]["ES0902"]["rules"]
    con = normativa.resolucion(senal, evidencia={"ES0902.Vu7": _r()})["standards"]["ES0902"]["rules"]
    for regla in ("C2", "C3", "Vu6"):
        t.igual("E-39 %s en la unidad sigue igual" % regla, sin[regla], con[regla])
    t.igual("E-39 mientras Vu7 pasa", "PASS", con["Vu7"]["result"])


def test_e40_la_integridad_del_repositorio_no_decide(t):
    """E-40."""
    for nombre, base in (("pasa", _r()), ("falla", _honesta(_fuga())),
                         ("sin resolver", _r(_reg([_comp(estado="UNRESOLVED")])))):
        for valor in ("PASS", "FAIL", "SUSPICIOUS_CHANGE"):
            veredicto = _e("integridad", "REPOSITORY_INTEGRITY_VERDICT", "REPOSITORY_INTEGRITY", valor,
                           comps=None, sups=None)
            if nombre == "pasa":
                caso = _caso(evidencia=EVIDENCIA + [veredicto])
            elif nombre == "falla":
                caso = _caso(_reg([_comp(superficies=[_sup(resultado=FUGA, ctx="UNAUTHORIZED",
                                                           evidencia=["fuga"])])]),
                             _sin("efectiva", _fuga(), veredicto))
            else:
                caso = _caso(_reg([_comp(estado="UNRESOLVED")]), EVIDENCIA + [veredicto])
            caso["repositoryIntegrity"] = {"result": valor}
            t.igual("E-40 %s con un veredicto %s no cita: mismo resultado" % (nombre, valor),
                    _json(base), _json(CHECK.evaluar(caso)))
            citado = copy.deepcopy(caso)
            for comp in citado["registry"]["components"]:
                comp["evidence"].append("integridad")
            t.igual("E-40 %s con el veredicto %s citado: mismo estado" % (nombre, valor),
                    base["state"], CHECK.evaluar(citado)["state"])


# -- El agregado ------------------------------------------------------------------------

def test_e41_una_fuga_en_cualquier_superficie(t):
    """E-41."""
    r = _con_otro(valor=FUGA)
    t.igual("E-41 una fuga en la base hace FAIL el agregado", FUGA, r["state"])
    t.verdadero("E-41 y es una falla", r["state"] in FALLAS)
    t.igual("E-41 aunque el servidor web cumpla", "PASS", _s(r)["state"])
    t.igual("E-41 la base falla", FUGA, _s(r, "base-de-datos", "consola")["state"])
    t.verdadero("E-41 y no aprueba", not CHECK.aprueba(r))
    t.igual("E-41 en seguridad es FAIL", "NON_COMPLIANT", _vu7_en_seguridad(r)["result"])
    dos = _r(_reg([_comp(superficies=[_sup(), _sup("backups", ctx="UNAUTHORIZED", resultado=FUGA,
                                               evidencia=["f-b"])])]),
             _sin("alc", _alc([SUP, "backups"]), _fuga("f-b", sup="backups")))
    t.igual("E-41 una superficie falla y la otra cumple, en el mismo componente", FUGA, dos["state"])


def test_e42_un_sin_resolver_material(t):
    """E-42."""
    comp, evid = _otro(valor="UNRESOLVED", resultado="UNRESOLVED")
    evid = [x for x in evid if not x["evidenceId"].startswith("ent-")]
    r = _r(_reg([_comp(), comp]), [_inv([COMP, "base-de-datos"])] + EVIDENCIA[1:] + evid)
    t.igual("E-42 no pasa", CONF, r["state"])
    t.igual("E-42 aunque el servidor web cumpla", "PASS", _s(r)["state"])
    t.igual("E-42 en seguridad no cumple", "UNRESOLVED", _vu7_en_seguridad(r)["result"])
    for nombre, registro, esperado in (
            ("el inventario", _reg([_comp(evidencia=["alc"])]), INV),
            ("la clasificacion", _reg(clases=[_clase(evidencia=[])]), CLASE),
            ("la cobertura", _reg([_comp(evidencia=["inv"])]), COB),
            ("la configuracion", _reg([_comp(estado="UNRESOLVED")]), CONF)):
        solo = _r(registro)
        t.igual("E-42 %s sin resolver impide el PASS" % nombre, esperado, solo["state"])
        t.igual("E-42 %s sin resolver no cumple en seguridad" % nombre, "UNRESOLVED",
                _vu7_en_seguridad(solo)["result"])
    t.igual("E-42 una clase declarada sin resolver, aunque nadie la nombre", CLASE,
            _estado(_reg(clases=[_clase(), _clase("otra", "UNRESOLVED", [])])))
    t.igual("E-42 el primer sin resolver en el orden de la lista", INV,
            _estado(_reg([_comp(evidencia=[], estado="UNRESOLVED")])))
    comp2, evid2 = _otro(valor=FUGA)
    t.igual("E-42 una falla le gana a un sin resolver", FUGA,
            _estado(_reg([_comp(estado="UNRESOLVED"), comp2]), EVIDENCIA + evid2))


def test_e43_el_mismo_resultado(t):
    """E-43."""
    comp, evid = _otro(valor=FUGA)
    comp3, evid3 = _otro("cache", "metricas", valor="UNRESOLVED", resultado="UNRESOLVED")
    registro = _reg([_comp(superficies=[_sup(), _sup("backups", evidencia=["e-b"])]), comp, comp3],
                    [_clase(), _clase("otra", "NOT_PRIVATE", ["c2"])])
    evid_todo = ([_inv([COMP, "base-de-datos", "cache"])] + EVIDENCIA[1:] + evid + evid3
                 + [_ent("e-b", sup="backups"), _clasif("otra", "NOT_PRIVATE", "c2"), _fuga("rep"),
                    _fuga("rep")])
    base = _json(_r(registro, evid_todo))
    azar = random.Random(43)
    for vuelta in range(6):
        reg, ev = copy.deepcopy(registro), copy.deepcopy(evid_todo)
        azar.shuffle(reg["components"])
        azar.shuffle(reg["dataClasses"])
        azar.shuffle(ev)
        for c in reg["components"]:
            azar.shuffle(c["surfaces"])
            azar.shuffle(c["evidence"])
        t.igual("E-43 desordenado %d" % vuelta, base, _json(_r(reg, ev)))
    t.igual("E-43 los nueve estados", sorted(LOS_9), sorted(CHECK.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "configuración") for f in ("NFC", "NFD"))
    for nombre, par in (("iguales", (SIN_FUGA, SIN_FUGA)), ("fuga la NFC", (FUGA, SIN_FUGA)),
                        ("fuga la NFD", (SIN_FUGA, FUGA))):
        gemelas = [_ent(nfc, par[0]), _ent(nfd, par[1])]
        for orden in (gemelas, gemelas[::-1]):
            t.igual("E-43 gemelas en NFC y NFD (%s) no pasan ni fallan" % nombre, CONF,
                    _solo_con(*orden)["state"])
    t.igual("E-43 citar en NFD una evidencia en NFC es citarla", "PASS",
            _estado(_reg([_comp(superficies=[_sup(evidencia=[nfd])])]), _sin("efectiva", _ent(nfc))))
    dos = _r(_reg([_comp(superficies=[_sup(nfc, evidencia=["e1"]), _sup(nfd, evidencia=["e1"])])]),
             _sin("alc", _alc([nfc]), _ent("e1", sup=nfc)))
    t.igual("E-43 dos superficies iguales en NFC son la misma, repetida",
            (COB, ["%s/%s" % (COMP, nfc)]), (dos["state"], dos["coverage"]["duplicatedSurfaces"]))
    t.igual("E-43 dos componentes iguales en NFC son el mismo, repetido", [nfc],
            _r(_reg([_comp(nfc), _comp(nfd)]), _sin("inv", _inv([nfc])))["coverage"]
            ["duplicatedComponents"])
    t.igual("E-43 dos clases iguales en NFC no se resuelven", CLASE,
            _estado(_reg([_comp(superficies=[_sup(refs=[nfc])])], [_clase(nfc), _clase(nfd)]),
                    _sin("clasif", _clasif(nfc))))


def test_e44_la_trazabilidad(t):
    """E-44."""
    caminos = {"vacio": CHECK.evaluar({}), "pasa": _r(), "falla": _honesta(_fuga()),
               "insegura": _solo_con(_prueba(environment="PRD")),
               "sin ambiente": _r(_reg(ambiente=None)),
               "registro invalido": CHECK.evaluar({"registry": {"components": 1}})}
    for nombre, r in caminos.items():
        t.igual("E-44 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-44 %s la clave" % nombre, "ES0902.Vu7", r["ruleKey"])
        t.igual("E-44 %s el control" % nombre, "base-software-data-disclosure-configuration",
                r["control"])
    t.igual("E-44 un registro invalido deja el inventario sin resolver", INV,
            caminos["registro invalido"]["state"])
    vu7 = _unidad(_r())
    t.igual("E-44 la unidad lleva Vu7 en PASS", "PASS", vu7["result"])
    t.igual("E-44 con su ambiente", "QA", vu7["environment"])
    t.igual("E-44 con sus componentes", [COMP], vu7["components"])
    t.igual("E-44 y su evidencia por id", ["alc", "clasif", "efectiva", "inv"], vu7["evidence"])
    t.igual("E-44 y nada mas, sin applicability",
            ["components", "environment", "evidence", "result", "source"], sorted(vu7))
    t.igual("E-44 con la fuente", TRAZA, vu7["source"])
    t.igual("E-44 sin resultado, la unidad dice sin resolver", ("UNRESOLVED", None, []),
            tuple(normativa.resolucion({})["standards"]["ES0902"]["rules"]["Vu7"][k]
                  for k in ("result", "environment", "components")))
    t.igual("E-44 un resultado ajeno no se proyecta", "UNRESOLVED",
            _unidad(dict(_r(), control="otro-control"))["result"])
    t.igual("E-44 ni uno que dice NOT_APPLICABLE", "UNRESOLVED",
            _unidad(dict(_r(), state="NOT_APPLICABLE"))["result"])
    original = normativa._ruta_de_evidencia
    normativa._ruta_de_evidencia = lambda: str(RAIZ / "no-existe" / "evidencia.py")
    try:
        sin_lib = normativa.resolucion({}, evidencia={"ES0902.Vu7": _r()})
    finally:
        normativa._ruta_de_evidencia = original
    vu7_sin = sin_lib["standards"]["ES0902"]["rules"]["Vu7"]
    t.igual("E-44 sin la lib la unidad se arma, con el estado y sin ids", ("PASS", None, [], []),
            (vu7_sin["result"], vu7_sin["environment"], vu7_sin["components"], vu7_sin["evidence"]))
    t.verdadero("E-44 y Vu6 sigue en la unidad", "Vu6" in sin_lib["standards"]["ES0902"]["rules"])


def test_e45_entra_al_libro_como_cualquier_regla(t):
    """E-45."""
    paquete = BIN / "reporte_seguridad"
    t.igual("E-45 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in paquete.iterdir() if p.is_file()))
    alcance = {"project": "Sistema de prueba", "environment": "QA"}
    carpeta = tempfile.mkdtemp(prefix="vu7_45_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-7045")
        esperados = (("pasa", _r(), "COMPLIANT"),
                     ("falla", _honesta(_fuga()), "NON_COMPLIANT"),
                     ("sin resolver", _r(_reg([_comp(estado="UNRESOLVED")])), "UNRESOLVED"),
                     ("vacio", CHECK.evaluar({}), "UNRESOLVED"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu7_en_seguridad(r)
            t.igual("E-45 %s en seguridad" % nombre, resultado, regla["result"])
            t.igual("E-45 %s aplica siempre" % nombre, "APPLICABLE", regla["applicability"])
            for evento in prod.desde_regla(regla, "GCBA-7045", alcance, "2026-09-24T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-45 cuatro RULE_EVALUATION en el mismo libro", ["RULE_EVALUATION"] * 4,
                [e["eventType"] for e in eventos])
        t.igual("E-45 de ES0902.Vu7", [("ES0902", "Vu7", "ES0902.Vu7")] * 4,
                [(e["normative"]["standard"], e["normative"]["rule"], e["details"]["ruleKey"])
                 for e in eventos])
        t.igual("E-45 con el resultado tal cual",
                ["COMPLIANT", "NON_COMPLIANT", "UNRESOLVED", "UNRESOLVED"],
                [e["result"] for e in eventos])
        t.igual("E-45 producido por desde_regla", ["desde_regla"] * 4,
                [e["details"]["producer"] for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    t.igual("E-45 un resultado ajeno no se traduce", ({}, {}),
            CHECK.para_seguridad(dict(_r(), control="otro-control")))
    t.igual("E-45 sin senales: la regla es ALWAYS", {}, CHECK.para_seguridad(_r())[1])
    t.igual("E-45 Vu7 en el dominio de datos sensibles e interfaces publicas", True,
            "Vu7" in [d for d in json.loads((REGLAS / "security-report-domains.json").read_text(
                encoding="utf-8"))["domains"] if d["domainId"] == "sensitive-data-public-interfaces"][0]
            ["rules"])
