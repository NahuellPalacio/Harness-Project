# D4: verificar lo que se renderiza, sin inventar el tamaño de la pantalla.
#
# Escenarios E-01 a E-31 de docs/cambios/d4-comportamiento-responsive/spec.md. Entre parentesis,
# el D4-nn del pedido de instalacion.
#
# 🔴 Nada de esto renderiza nada. Lo que se verifica es el CONTROL: que una corrida entre como
# dato, que lo que esta instalado no alcance, que la matriz de viewports no se invente y que lo
# que no se ejecuto no pase. Que la aplicacion de un proyecto sea efectivamente responsive lo
# dice una corrida real.
import importlib.util
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"

sys.path.insert(0, str(BIN))
from orquestacion import anexo2 as c_anexo2            # noqa: E402
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


CHECK = _cargar("responsive-behavior", "d4_check")

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D4"}

BUILD = {"id": "b-2026-09-20", "runtime": "chromium-129"}


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="s-1", tipo="PROJECT_CONTEXT", ref="interfaces.items",
              claim="el sistema expone vistas de usuario", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid="frontendPresent", **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    s.update(extra)
    return s


def _ev(eid="e1", tipo="RENDERED_BEHAVIOR_RUN", ref="corridas/2026-09-20.json",
        claim="la corrida recorrio el flujo en el viewport", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim,
         "buildId": BUILD["id"], "runtime": BUILD["runtime"]}
    e.update(extra)
    return e


def _defecto(dimension="content-clipping", materialidad="MATERIAL", did="d-1"):
    return {"id": did, "dimension": dimension, "materiality": materialidad}


def _res(vid="compacto", ejecucion="EXECUTED", defectos=None, refs=("e1",), flujo="alta"):
    return {"viewportId": vid, "flowId": flujo, "execution": ejecucion,
            "defects": list(defectos or []), "evidenceRefs": list(refs)}


VIEWPORTS = [{"id": "compacto", "class": "handheld"}, {"id": "amplio", "class": "desktop"}]


def _caso(resultados=None, viewports=None, fuente="PROJECT_UX_REQUIREMENT", evidencia=None,
          objetivo=True, matriz=None, **extra):
    d = {"application": {"id": "portal-tramites", "environment": "QA"},
         "build": dict(BUILD),
         "testTarget": {"available": objetivo},
         "viewportMatrix": matriz if matriz is not None else {
             "source": fuente,
             "viewports": list(VIEWPORTS if viewports is None else viewports)},
         "results": [_res("compacto"), _res("amplio")] if resultados is None else resultados,
         "evidence": [_ev()] if evidencia is None else evidencia}
    d.update(extra)
    return d


_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "d" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


# -- la senal ------------------------------------------------------------------

def test_e01_d4_es_condicional(t):
    """E-01 (D4-01) — CONDITIONAL sobre frontendPresent, identidad intacta."""
    d4 = c_matriz.regla("D4")
    t.igual("E-01 el modo", "CONDITIONAL", d4["applicability"]["mode"])
    t.igual("E-01 la senal", ["frontendPresent"], d4["applicability"]["signals"])
    t.igual("E-01 el id", "D4", d4["id"])
    t.igual("E-01 la categoria", "DESIGN", d4["category"])
    t.igual("E-01 la intencion operativa no cambio",
            "Frontend code must adapt responsively to viewing devices.",
            d4["operationalIntentEn"])
    t.igual("E-01 el agente", ["dev-frontend"], d4["primaryAgents"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d4["status"])


def test_e02_true_hace_aplicable(t):
    """E-02 (D4-02) — TRUE con evidencia deja D4 aplicable con sus dos controles."""
    bloque = c_normativa.resolucion({"frontendPresent": _senal("TRUE")})
    t.verdadero("E-02 D4 aplica", "D4" in bloque["applicableRules"])
    t.verdadero("E-02 exige su policy",
                "responsive-ui-required" in bloque["declaredPolicies"])
    t.verdadero("E-02 y su check", "responsive-behavior" in bloque["declaredChecks"])


def test_e03_false_hace_no_aplicable(t):
    """E-03 (D4-03) — FALSE con evidencia deja D4 fuera."""
    evidencia = [_ev_senal(claim="el componente no expone ninguna vista")]
    bloque = c_normativa.resolucion({"frontendPresent": _senal("FALSE", evidencia)})
    t.verdadero("E-03 D4 no aplica", "D4" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no esta entre las aplicables", "D4" not in bloque["applicableRules"])
    t.verdadero("E-03 su policy no se exige",
                "responsive-ui-required" not in bloque["declaredPolicies"])


def test_e04_sin_senal_queda_sin_resolver(t):
    """E-04 (D4-04) — sin senal, D4 sin resolver con la que falta escrita."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D4 esta sin resolver", "D4" in sin_resolver)
    t.igual("E-04 con el motivo", "APPLICABILITY_UNRESOLVED", sin_resolver["D4"]["reason"])
    t.igual("E-04 y la senal que falta", ["frontendPresent"],
            sin_resolver["D4"]["missingSignals"])


def test_e05_lo_ausente_nunca_es_falso(t):
    """E-05 (D4-05) — que no aparezca una carpeta frontend no es evidencia de nada."""
    caminos = {
        "sin senal": {},
        "senal UNRESOLVED": {"frontendPresent": _senal("UNRESOLVED", [])},
        "senal sin evidencia": {"frontendPresent": _senal("TRUE", [])},
        "no se encontro carpeta": {"frontendPresent": _senal("FALSE", [_ev_senal(
            tipo="REPOSITORY_DEPENDENCY", ref="ls src/",
            claim="no aparecio ninguna carpeta frontend")])},
    }
    for nombre, senales in caminos.items():
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-05 %s no vuelve D4 no aplicable" % nombre,
                    "D4" not in bloque["notApplicableRules"])
        t.verdadero("E-05 %s la deja sin resolver" % nombre,
                    "D4" in {u["rule"] for u in bloque["unresolvedRules"]})


def test_e06_la_senal_es_reusable(t):
    """E-06 (D4-06) — sumar un consumidor no pide una linea de codigo."""
    t.igual("E-06 hoy la declara D4", ["D4"], c_senales.reglas_de("frontendPresent"))

    senal = _senal("TRUE")
    resuelta = c_senales.resolver_una(senal)
    t.igual("E-06 se resuelve una vez", "TRUE", resuelta["value"])

    # Una matriz donde D5 tambien la declara: la MISMA senal resuelta mueve las dos reglas,
    # sin tocar codigo.
    doc = c_matriz.cargar()
    doc = {k: (list(v) if isinstance(v, list) else v) for k, v in doc.items()}
    doc["rules"] = [dict(r) for r in doc["rules"]]
    for r in doc["rules"]:
        if r["id"] == "D5":
            r["applicability"] = {"mode": "CONDITIONAL", "signals": ["frontendPresent"]}
    salida = c_matriz.resolver(c_senales.booleanos({"frontendPresent": resuelta}), doc)
    t.verdadero("E-06 D4 aplica", "D4" in salida["applicableRules"])
    t.verdadero("E-06 y el consumidor nuevo tambien", "D5" in salida["applicableRules"])

    # Y el productor es el mismo para cualquier senal declarada.
    for sid in ("frontendPresent", "applicationCodePresent", "citizenFacing"):
        floja = c_senales.producir(
            sid, [_ev_senal(tipo="AGENT_STATEMENT", ref="un agente", claim="me parece")],
            {"type": "DETERMINISTIC"}, valor="TRUE")
        t.igual("E-06 %s con evidencia floja" % sid, "UNRESOLVED", floja["value"])


def test_e07_una_unidad_de_backend_no_aplica(t):
    """E-07 (D4-08) — backend o API solamente: NOT_APPLICABLE con evidencia."""
    evidencia = [_ev_senal(tipo="PROJECT_CONTEXT", ref="project_profile.project_type",
                           claim="el proyecto es una API sin interfaz de usuario")]
    senal = _senal("FALSE", evidencia)
    bloque = c_normativa.resolucion({"frontendPresent": senal})
    t.verdadero("E-07 D4 no aplica", "D4" in bloque["notApplicableRules"])

    salida = CHECK.evaluar(_caso(), senal)
    t.igual("E-07 el check no evalua", "NOT_APPLICABLE", salida["state"])
    t.igual("E-07 ni mira ningun caso", [], salida["cases"])
    t.verdadero("E-07 no aprueba", not CHECK.aprueba(salida))


# -- la forma del control ------------------------------------------------------

def test_e08_una_policy_y_un_check(t):
    """E-08 (D4-07) — y ninguna review."""
    d4 = c_matriz.regla("D4")
    t.igual("E-08 la policy", ["responsive-ui-required"], d4["policies"])
    t.igual("E-08 el check", ["responsive-behavior"], d4["checks"])
    t.igual("E-08 ninguna review", [], d4.get("reviews") or [])

    de_d4 = c_controles.de_la_regla("D4")
    t.igual("E-08 dos controles", 2, len(de_d4))
    t.igual("E-08 una policy y un check", ["CHECK", "POLICY"],
            sorted(c["type"] for c in de_d4))
    t.igual("E-08 y ninguna REVIEW", [],
            [c["id"] for c in de_d4 if c["type"] == "REVIEW"])


# -- lo que no alcanza ---------------------------------------------------------

def _solo_con(tipo, claim):
    """Un caso donde todo corrio bien y el unico respaldo es esa clase de evidencia."""
    return _caso(evidencia=[_ev(tipo=tipo, claim=claim)])


def test_e09_bootstrap_instalado_no_alcanza(t):
    """E-09 (D4-09) — que este en el manifiesto no dice como se ve."""
    salida = CHECK.evaluar(_solo_con("REPOSITORY_DEPENDENCY",
                                     "bootstrap figura en dependencies"), _senal("TRUE"))
    t.igual("E-09 el estado", "PARTIAL", salida["state"])
    t.igual("E-09 con el motivo", "RENDERED_EVIDENCE_MISSING", salida["reason"])
    t.verdadero("E-09 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-09 la dependencia no prueba nada",
                "REPOSITORY_DEPENDENCY" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e10_obelisco_instalado_no_alcanza(t):
    """E-10 (D4-10) — ni instalado, ni homologado por G1."""
    salida = CHECK.evaluar(_solo_con("DESIGN_SYSTEM_USAGE",
                                     "la aplicacion usa el design system del GCBA"),
                           _senal("TRUE"))
    t.igual("E-10 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-10 no aprueba", not CHECK.aprueba(salida))

    # Y que G1 lo de por homologado no mueve el resultado de D4.
    entrada = c_anexo2.buscar("obelisco-v2")
    t.verdadero("E-10 G1 conoce el design system", entrada is not None)
    t.igual("E-10 y eso es de G1, no de D4", "G1", c_anexo2.TRAZA["rule"])
    t.igual("E-10 el estado de D4 sigue igual", "PARTIAL",
            CHECK.evaluar(_solo_con("DESIGN_SYSTEM_USAGE",
                                    "el design system esta homologado por G1"),
                          _senal("TRUE"))["state"])


def test_e11_las_media_queries_no_alcanzan(t):
    """E-11 (D4-11) — que exista el CSS no dice que funcione."""
    salida = CHECK.evaluar(_solo_con("STYLESHEET_CONFIGURATION",
                                     "hay media queries y una hoja mobile"), _senal("TRUE"))
    t.igual("E-11 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-11 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-11 la configuracion de estilos no prueba nada",
                "STYLESHEET_CONFIGURATION" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e12_una_captura_sola_no_alcanza(t):
    """E-12 (D4-18) — una imagen acompana, no sostiene."""
    salida = CHECK.evaluar(_solo_con("SCREENSHOT", "captura del home"), _senal("TRUE"))
    t.igual("E-12 el estado", "PARTIAL", salida["state"])
    t.igual("E-12 con el motivo", "RENDERED_EVIDENCE_MISSING", salida["reason"])
    t.verdadero("E-12 la captura es apoyo", "SCREENSHOT" in CHECK.EVIDENCIA_DE_APOYO)
    t.verdadero("E-12 y no es evidencia de corrida",
                "SCREENSHOT" not in CHECK.EVIDENCIA_DE_CORRIDA)

    # Acompanando a una corrida, suma sin molestar.
    con_las_dos = _caso(resultados=[_res("compacto", refs=("e1", "e2")),
                                    _res("amplio", refs=("e1", "e2"))],
                        evidencia=[_ev("e1"), _ev("e2", tipo="SCREENSHOT",
                                                   claim="captura del viewport compacto")])
    t.igual("E-12 acompanando si", "PASS", CHECK.evaluar(con_las_dos, _senal("TRUE"))["state"])


def test_e13_la_afirmacion_de_alguien_no_alcanza(t):
    """E-13 — que alguien diga que es responsive no es evidencia de que lo sea."""
    salida = CHECK.evaluar(_solo_con("AGENT_STATEMENT", "lo mire y es responsive"),
                           _senal("TRUE"))
    t.igual("E-13 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-13 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-13 la afirmacion no prueba nada",
                "AGENT_STATEMENT" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


# -- la matriz de viewports ----------------------------------------------------

def test_e14_sin_matriz_no_hay_resultado(t):
    """E-14 (D4-12) — VIEWPORT_MATRIX_UNRESOLVED, que no es PARTIAL ni FAIL."""
    # Las tres formas de no tener matriz, y las tres corren de verdad: la version anterior
    # etiquetaba "sin bloque" y armaba la matriz vacia dos veces.
    sin_bloque = _caso(resultados=[])
    del sin_bloque["viewportMatrix"]
    formas = (("sin bloque", sin_bloque),
              ("en nulo", dict(_caso(resultados=[]), viewportMatrix=None)),
              ("vacia", _caso(resultados=[],
                              matriz={"source": "PROJECT_UX_REQUIREMENT", "viewports": []})))
    for nombre, caso in formas:
        salida = CHECK.evaluar(caso, _senal("TRUE"))
        t.igual("E-14 %s" % nombre, "VIEWPORT_MATRIX_UNRESOLVED", salida["state"])
        t.verdadero("E-14 %s no es PARTIAL" % nombre, salida["state"] != "PARTIAL")
        t.verdadero("E-14 %s no es FAIL" % nombre, salida["state"] != "FAIL")
        t.verdadero("E-14 %s no aprueba" % nombre, not CHECK.aprueba(salida))


def test_e15_la_matriz_declara_de_donde_sale(t):
    """E-15 — la fuente es parte del contrato."""
    sin_fuente = _caso(fuente="PORQUE_LO_DECIDIMOS_HOY")
    salida = CHECK.evaluar(sin_fuente, _senal("TRUE"))
    t.igual("E-15 el estado", "VIEWPORT_MATRIX_UNRESOLVED", salida["state"])
    t.contiene("E-15 y dice por que", "no declara de donde sale", salida["detail"])

    for fuente in CHECK.FUENTES_DE_MATRIZ:
        t.igual("E-15 %s si vale" % fuente, "PASS",
                CHECK.evaluar(_caso(fuente=fuente), _senal("TRUE"))["state"])

    # Un viewport sin identificar tampoco.
    t.igual("E-15 un viewport sin id", "VIEWPORT_MATRIX_UNRESOLVED",
            CHECK.evaluar(_caso(viewports=[{"class": "handheld"}]), _senal("TRUE"))["state"])


# Los valores que D4 NO define y este harness no inventa: anchos, modelos de dispositivo y
# listas de breakpoints. Van anclados donde hace falta para convivir con la prosa que los nombra
# para negarlos.
# 🔴 **Ningun numero.** No hay lista de anchos "conocidos" y no hay regla de proximidad: el
# estandar no define ningun valor, asi que un artefacto de D4 no tiene nada legitimo que
# contar. Enumerar es la forma equivocada para un dominio que la norma deja abierto — la
# primera version enumeraba anchos y dejaba entrar 640, 900 y 1200; la segunda los buscaba
# cerca de una palabra de tamaño y dejaba entrar `escritorio: 1600` y `MINIMO = 600`.
#
# Las marcas siguen siendo una enumeracion porque no hay invariante equivalente, y por eso van
# acompanadas de la forma generica marca + numero de modelo: esa no necesita acertarle a la
# marca, que es lo que hace que la lista no tenga que estar completa.
PROHIBIDOS = (
    r"\b\d{2,4}\b",
    r"(?i)\b\d+\s*(px|rem|em|pt|vw|vh|dp)\b",
    r"(?i)\b(?:min|max)-(?:width|height)\s*:",
    r"(?i)\bbreakpoints?\b[^\n]{0,10}?[:=]",
    r"(?i)\b(iPhone|iPad|iPod|Galaxy|Nexus|Surface|Moto\s?G|Motorola|Pixel|Xiaomi|Redmi|"
    r"Huawei|OnePlus|MacBook|Samsung|Nokia|Oppo|Realme|Vivo|Chromebook|Kindle|Honor)\b",
    r"\b[A-Z][A-Za-z]{2,}\s+[A-Z]?\d{1,3}\b",
)

# 🔴 Cada fuga es la forma CRUDA. La version anterior escribia `escritorio: ancho 1600` —le
# agregaba la palabra que el patron necesitaba— y la lista decia cubrir una forma que no
# cubria. Una fuga reescrita para que el patron la atrape no prueba nada.
FUGAS = (
    ("un ancho en pixeles", "mobile: 320px"),
    ("un ancho en rem", "mobile: 20rem"),
    ("una media query", "@media (min-width: 768px) { }"),
    ("una lista de breakpoints", "breakpoints = [320, 768, 1024, 1440]"),
    ("una constante en mayuscula", "BREAKPOINTS = (640, 900, 1200)"),
    ("anchos fuera de la lista conocida", "ANCHOS_POR_DEFECTO = (640, 900)"),
    ("una constante de anchos", "VIEWPORTS_POR_DEFECTO = (1440, 1024, 768)"),
    ("un ancho suelto", "el viewport de tablet es 768"),
    ("un ancho de escritorio, crudo", "escritorio: 1600"),
    ("un ancho chico suelto", "el viewport chico es 600"),
    ("un ancho en una tabla", "| movil | 600 |"),
    ("un entero con nombre sin pistas", "MINIMO = 600"),
    ("un modelo de dispositivo", "perfil de referencia: iPhone 14 Pro"),
    ("otro modelo de dispositivo", "perfil de referencia: Google Pixel 7"),
    ("una marca que nadie lista", "se prueba en Xiaomi Redmi Note"),
    ("una marca que tampoco estaba", "se prueba en Nokia G22"),
    ("un modelo con marca nueva", "dispositivo: Oppo Reno 8"),
    ("un equipo que no es telefono", "perfil de referencia: Chromebook Plus"),
)

ARTEFACTOS_D4 = ("policies/responsive-ui-required.md", "checks/responsive-behavior.py")


def test_e16_no_se_inventan_breakpoints(t):
    """E-16 (D4-24) — ningun artefacto de D4 trae un valor que el estandar no define."""
    for relativa in ARTEFACTOS_D4:
        archivo = CONTROLES / Path(relativa)
        texto = io.open(archivo, encoding="utf-8").read()
        for patron in PROHIBIDOS:
            encontrado = re.search(patron, texto)
            t.vacio("E-16 %s sin %s" % (archivo.name, patron),
                    encontrado.group(0).strip() if encontrado else "")

    # La premisa de la mitad de abajo, afirmada y no supuesta.
    base = io.open(CONTROLES / Path(ARTEFACTOS_D4[0]), encoding="utf-8").read()
    t.verdadero("E-16 el texto base no matchea ningun patron",
                not any(re.search(p, base) for p in PROHIBIDOS))

    for nombre, fuga in FUGAS:
        contaminado = base + "\n\n" + fuga + "\n"
        t.verdadero("E-16 la guarda atrapa %s" % nombre,
                    any(re.search(p, contaminado) for p in PROHIBIDOS))

    # Y el modulo no trae NINGUNA constante con numeros que alguien pueda leer como la matriz
    # normativa, se llame como se llame. Acotarlo a los nombres con "VIEWPORT" dejaba entrar un
    # `ANCHOS_POR_DEFECTO = (640, 900)` por la puerta de al lado.
    def _tiene_numero(valor, hondura=0):
        """Un entero en cualquier lado: suelto, en una coleccion o anidado."""
        if hondura > 4:
            return False
        if isinstance(valor, bool):
            return False
        if isinstance(valor, int):
            return True
        if isinstance(valor, (list, tuple, set, frozenset)):
            return any(_tiene_numero(x, hondura + 1) for x in valor)
        if isinstance(valor, dict):
            return any(_tiene_numero(x, hondura + 1)
                       for x in list(valor.keys()) + list(valor.values()))
        return False

    con_numeros = [n for n in dir(CHECK)
                   if not n.startswith("_") and _tiene_numero(getattr(CHECK, n))]
    t.igual("E-16 ninguna constante del check trae numeros", [], con_numeros)


# -- la corrida ----------------------------------------------------------------

def test_e17_sin_objetivo_no_hay_corrida(t):
    """E-17 — TEST_TARGET_UNAVAILABLE, y no se colapsa en PASS."""
    salida = CHECK.evaluar(_caso(objetivo=False), _senal("TRUE"))
    t.igual("E-17 el estado", "TEST_TARGET_UNAVAILABLE", salida["state"])
    t.verdadero("E-17 no aprueba", not CHECK.aprueba(salida))
    t.igual("E-17 no evalua ningun caso", [], salida["cases"])


def test_e18_un_defecto_material_falla(t):
    """E-18 (D4-14) — recorte o superposicion en un viewport requerido."""
    for dimension in ("content-clipping", "material-overlap", "horizontal-overflow"):
        caso = _caso(resultados=[_res("compacto", defectos=[_defecto(dimension)]),
                                 _res("amplio")])
        salida = CHECK.evaluar(caso, _senal("TRUE"))
        t.igual("E-18 %s" % dimension, "FAIL", salida["state"])
        t.igual("E-18 %s con el motivo" % dimension, "MATERIAL_RESPONSIVE_DEFECT",
                salida["reason"])
        t.verdadero("E-18 %s no aprueba" % dimension, not CHECK.aprueba(salida))


def test_e19_una_accion_inalcanzable_falla(t):
    """E-19 (D4-15) — una accion critica que no se puede alcanzar."""
    caso = _caso(resultados=[_res("compacto",
                                  defectos=[_defecto("critical-action-reachability")]),
                             _res("amplio")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-19 el estado", "FAIL", salida["state"])
    t.igual("E-19 el caso que falla es el del viewport compacto", "compacto",
            [c["viewportId"] for c in salida["cases"] if c["state"] == "FAIL"][0])


def test_e20_lo_que_no_se_ejecuto_no_pasa(t):
    """E-20 (D4-16) — PARTIAL aunque todos los demas pasen."""
    sin_ejecutar = _caso(resultados=[_res("compacto", ejecucion="NOT_EXECUTED"),
                                     _res("amplio")])
    salida = CHECK.evaluar(sin_ejecutar, _senal("TRUE"))
    t.igual("E-20 el estado", "PARTIAL", salida["state"])
    t.igual("E-20 con el motivo", "REQUIRED_VIEWPORT_NOT_EXECUTED", salida["reason"])
    t.verdadero("E-20 no aprueba", not CHECK.aprueba(salida))
    t.igual("E-20 el otro caso sigue pasando", "PASS",
            [c["state"] for c in salida["cases"] if c["viewportId"] == "amplio"][0])

    # Un viewport de la matriz sin ningun resultado tampoco se omite.
    faltante = _caso(resultados=[_res("amplio")])
    otra = CHECK.evaluar(faltante, _senal("TRUE"))
    t.igual("E-20 un viewport sin resultado", "PARTIAL", otra["state"])
    t.verdadero("E-20 y aparece como caso",
                "compacto" in [c["viewportId"] for c in otra["cases"]])


def test_e21_todo_ejecutado_y_sin_defecto_pasa(t):
    """E-21 (D4-17) — con evidencia de la corrida."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-21 el estado", "PASS", salida["state"])
    t.verdadero("E-21 aprueba", CHECK.aprueba(salida))
    t.igual("E-21 los dos viewports", 2, len(salida["cases"]))
    t.verdadero("E-21 los dos con evidencia de la corrida",
                all(c["evidenceUsed"] for c in salida["cases"]))

    # Un defecto MINOR no tumba el PASS.
    con_menor = _caso(resultados=[_res("compacto", defectos=[_defecto("media", "MINOR")]),
                                  _res("amplio")])
    t.igual("E-21 un defecto menor no falla", "PASS",
            CHECK.evaluar(con_menor, _senal("TRUE"))["state"])


def test_e22_el_desktop_no_tapa_al_mobile(t):
    """E-22 — ignorar el mobile porque el desktop anda es el modo de falla del pedido."""
    caso = _caso(resultados=[_res("compacto", defectos=[_defecto()]), _res("amplio")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-22 el resultado falla", "FAIL", salida["state"])
    t.igual("E-22 aunque el amplio pase", "PASS",
            [c["state"] for c in salida["cases"] if c["viewportId"] == "amplio"][0])

    # Y un resultado de un viewport que la matriz no declara no compensa nada.
    colado = _caso(resultados=[_res("compacto", defectos=[_defecto()]), _res("amplio"),
                               _res("un-viewport-que-nadie-pidio")])
    otra = CHECK.evaluar(colado, _senal("TRUE"))
    t.igual("E-22 el colado no compensa", "FAIL", otra["state"])
    t.igual("E-22 y se reporta como ignorado", ["un-viewport-que-nadie-pidio"],
            otra["ignoredResults"])


def test_e23_la_evidencia_esta_atada_a_la_corrida(t):
    """E-23 (D4-19) — una corrida sobre otro build es sobre otro sistema."""
    otro_build = _caso(evidencia=[_ev(buildId="b-viejo")])
    salida = CHECK.evaluar(otro_build, _senal("TRUE"))
    t.igual("E-23 otro build no sostiene", "PARTIAL", salida["state"])
    t.verdadero("E-23 y se dice",
                any("EVIDENCE_OUT_OF_BUILD" in i for i in salida["issues"]))

    otro_runtime = _caso(evidencia=[_ev(runtime="un-navegador-viejo")])
    t.igual("E-23 otro runtime tampoco", "PARTIAL",
            CHECK.evaluar(otro_runtime, _senal("TRUE"))["state"])

    huerfana = _caso(resultados=[_res("compacto", refs=("e-99",)), _res("amplio")])
    salida = CHECK.evaluar(huerfana, _senal("TRUE"))
    t.igual("E-23 una referencia que no existe tampoco", "PARTIAL", salida["state"])
    t.verdadero("E-23 y se dice",
                any("EVIDENCE_REFERENCE_MISSING" in i for i in salida["issues"]))

    # La que no declara build es de esta corrida.
    sin_declarar = _ev()
    del sin_declarar["buildId"]
    t.igual("E-23 la que no lo declara cuenta", "PASS",
            CHECK.evaluar(_caso(evidencia=[sin_declarar]), _senal("TRUE"))["state"])


def test_e24_misma_entrada_mismo_resultado(t):
    """E-24 (D4-13) — determinista, y el resultado conserva su contexto."""
    caso = _caso()
    uno = CHECK.evaluar(caso, _senal("TRUE"))
    dos = CHECK.evaluar(dict(caso), _senal("TRUE"))
    t.igual("E-24 el estado", uno["state"], dos["state"])
    t.igual("E-24 y el resultado entero", repr(uno), repr(dos))

    t.igual("E-24 conserva el build", BUILD["id"], uno["build"]["id"])
    t.igual("E-24 y el runtime", BUILD["runtime"], uno["build"]["runtime"])
    t.igual("E-24 y la matriz con su fuente", "PROJECT_UX_REQUIREMENT",
            uno["viewportMatrix"]["source"])
    t.igual("E-24 con sus viewports", ["compacto", "amplio"],
            uno["viewportMatrix"]["viewports"])


def test_e25_un_defecto_sin_materialidad_no_se_ablanda(t):
    """E-25 — deja el caso sin resolver, no en el lado suave."""
    sin_materialidad = {"id": "d-1", "dimension": "content-clipping"}
    caso = _caso(resultados=[_res("compacto", defectos=[sin_materialidad]), _res("amplio")])
    salida = CHECK.evaluar(caso, _senal("TRUE"))
    t.igual("E-25 el estado", "PARTIAL", salida["state"])
    t.igual("E-25 con el motivo", "DEFECT_MATERIALITY_UNRESOLVED", salida["reason"])
    t.verdadero("E-25 no pasa", salida["state"] != "PASS")


def test_e26_solo_pass_aprueba(t):
    """E-26 — siete estados, uno solo aprueba."""
    t.igual("E-26 son siete", 7, len(CHECK.ESTADOS))
    for estado in CHECK.ESTADOS:
        t.igual("E-26 %s" % estado, str(estado == "PASS"),
                str(CHECK.aprueba({"state": estado})))


# -- las fronteras, los agentes y la instalacion -------------------------------

def test_e27_d4_no_es_accesibilidad_ni_g1(t):
    """E-27 — tres preguntas distintas sobre la misma pantalla."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    texto = repr(salida)
    for ajeno in ("accessibility", "accesibilidad", "dev-accessibility", "WCAG",
                  "technology-homologation", "approved-technology-required", "G1"):
        t.verdadero("E-27 el resultado no habla de %s" % ajeno, ajeno not in texto)

    t.verdadero("E-27 la accesibilidad tiene su propia skill",
                c_reg.hay_skill("dev-frontend", "dev-accessibility"))
    t.verdadero("E-27 y no es la de D4",
                c_reg.hay_skill("dev-frontend", "dev-responsive"))
    t.igual("E-27 la homologacion es de G1", "G1", c_anexo2.TRAZA["rule"])
    t.igual("E-27 y el check de D4 es de D4", "D4", salida["source"]["rule"])


def test_e28_no_se_crea_otro_framework_de_automatizacion(t):
    """E-28 (D4-21) — las skills son las instaladas y salen del registro."""
    skills = CHECK.skills_de_ejecucion()
    t.igual("E-28 son tres", 3, len(skills))
    pedidas = sorted(s["requestedSkill"] for s in skills)
    t.igual("E-28 y son las instaladas",
            ["dev-quality-validation", "dev-responsive", "dev-test-automation"], pedidas)
    for s in skills:
        t.igual("E-28 %s se rutea" % s["requestedSkill"], "ROUTABLE", s["result"])
        t.verdadero("E-28 %s es ruteable" % s["requestedSkill"], s["routable"])

    # El check no importa ningun navegador ni trae automatizacion propia.
    fuente = io.open(CONTROLES / "checks" / "responsive-behavior.py", encoding="utf-8").read()
    for libreria in ("playwright", "selenium", "puppeteer", "webdriver", "subprocess"):
        t.verdadero("E-28 el check no importa %s" % libreria,
                    ("import %s" % libreria) not in fuente
                    and ("from %s" % libreria) not in fuente)

    # Y no aparecio un modulo de automatizacion nuevo.
    nuevos = [p.name for p in (BIN / "orquestacion").glob("*.py")
              if any(x in p.name for x in ("browser", "navegador", "playwright", "e2e"))]
    t.igual("E-28 no hay modulo de automatizacion nuevo", [], nuevos)


def test_e29_la_unidad_propaga_senal_policy_y_check(t):
    """E-29 (D4-20) — con su evidencia."""
    unidad = {"id": "u1", "objective": "o", "domain": "frontend",
              "requiredCapabilities": [], "dependencies": [], "signals": [],
              "normativeSignals": {"frontendPresent": _senal("TRUE")}}
    documento = c_plan.armar({"objective": "x", "domains": ["frontend"], "policies": [],
                              "workUnits": [unidad]}, _CONTEXTO, {}, None)
    n = documento["workUnits"][0]["normative"]

    t.igual("E-29 el valor viaja", "TRUE", n["signals"]["frontendPresent"]["value"])
    t.igual("E-29 la evidencia tambien", "interfaces.items",
            n["signals"]["frontendPresent"]["evidence"][0]["reference"])
    t.verdadero("E-29 D4 aplica", "D4" in n["applicableRules"])
    t.verdadero("E-29 con su policy", "responsive-ui-required" in n["declaredPolicies"])
    t.verdadero("E-29 y su check", "responsive-behavior" in n["declaredChecks"])
    t.vacio("E-29 el plan valida", c_plan.validar(documento))


def test_e30_los_controles_dejan_de_faltar(t):
    """E-30 (D4-22) — sin tocar la identidad normativa de D4."""
    resolucion = c_matriz.resolver({"frontendPresent": True})

    sin_nada = c_matriz.controles_no_instalados(resolucion, policies_instaladas=[],
                                                checks_instalados=[], reviews_instaladas=[])
    estados = {f["id"]: f["state"] for f in sin_nada}
    t.igual("E-30 antes la policy", "DECLARED_POLICY_NOT_INSTALLED",
            estados.get("responsive-ui-required"))
    t.igual("E-30 antes el check", "DECLARED_CHECK_NOT_INSTALLED",
            estados.get("responsive-behavior"))

    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    t.verdadero("E-30 despues la policy no falta", "responsive-ui-required" not in faltan)
    t.verdadero("E-30 despues el check no falta", "responsive-behavior" not in faltan)

    d4 = c_matriz.regla("D4")
    t.igual("E-30 la fila no cambio", ["responsive-ui-required"], d4["policies"])
    t.igual("E-30 ni sus checks", ["responsive-behavior"], d4["checks"])
    t.igual("E-30 ni su senal", ["frontendPresent"], d4["applicability"]["signals"])

    citable = [r for r in c_normativa.reglas() if r.get("rule") == "D4"]
    t.igual("E-30 la regla citable sigue estando", 1, len(citable))
    t.igual("E-30 con su pagina", "12", str(citable[0]["page"]))


def test_e31_la_traza_se_conserva(t):
    """E-31 (D4-23) — ES0901 / 6.3 / 7.1 / D4 en todo lo que D4 emite."""
    for salida in (CHECK.evaluar(_caso(), _senal("TRUE")),
                   CHECK.evaluar(_caso(), _senal("FALSE")),
                   CHECK.evaluar(_caso(), None),
                   CHECK.evaluar(_caso(objetivo=False), _senal("TRUE")),
                   CHECK.evaluar(_caso(fuente="NADA"), _senal("TRUE"))):
        for campo, esperado in TRAZA.items():
            t.igual("E-31 %s en %s" % (campo, salida["state"]), esperado,
                    salida["source"][campo])

    t.igual("E-31 la trazabilidad de la matriz", TRAZA, c_matriz.trazabilidad("D4"))

    policy = io.open(CONTROLES / "policies" / "responsive-ui-required.md",
                     encoding="utf-8").read()
    t.contiene("E-31 la policy dice su regla", "rule: D4", policy)
    t.contiene("E-31 y su estandar", "standard: ES0901", policy)

    for cid in ("responsive-ui-required", "responsive-behavior"):
        declarado = c_controles.control(cid)
        t.igual("E-31 el registro: %s" % cid, "D4", declarado["source"]["rule"])
        t.igual("E-31 con su version: %s" % cid, "6.3", declarado["source"]["version"])
