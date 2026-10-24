# WCAG 2.2 con Obelisco V2: los escenarios de docs/cambios/wcag22-obelisco/spec.md que no instalan
# (E-01 a E-61). Los que instalan, actualizan y desinstalan de verdad van en
# 78-wcag22-obelisco-instalador.ps1 (E-62 a E-65). Cada aserción nombra su E-nn.
#
# Lo que NO hace este archivo: abrir un navegador, un teclado o un lector de pantalla. Verifica los
# controles —los datos, los scripts, el motor, el check—, no que una pagina real sea accesible.
#
# Sin BOM (00-encoding-fuentes) y sin las formas que E-61 de 63_harness_unico.py busca en tests/.
import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DESARROLLO = RAIZ / "harnesses" / "desarrollo"
SKILL = DESARROLLO / "skills" / "dev-accessibility"
REFS = SKILL / "references"
SCRIPTS = SKILL / "scripts"
LIB = DESARROLLO / "checks" / "lib"
CHECK = DESARROLLO / "checks" / "dev-accesibilidad-html.py"
TESTIGO = RAIZ / "tests" / "fixtures" / "wcag22-w3c.json"
CORPUS = RAIZ / "tests" / "fixtures" / "a11y" / "corpus.json"

sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402


def _cargar(ruta, alias):
    """Un modulo por ruta y con un alias propio: la suite corre todos los casos en un mismo proceso y
    `wcag`, `contrast` o `a11y` no tienen por que pisar nada de nadie."""
    spec = importlib.util.spec_from_file_location(alias, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


W = _cargar(SCRIPTS / "wcag.py", "wcag22_obelisco_wcag")
C = _cargar(SCRIPTS / "contrast.py", "wcag22_obelisco_contrast")
A = _cargar(LIB / "a11y.py", "wcag22_obelisco_a11y")

DATOS = json.loads((REFS / "wcag22-criteria.json").read_text("utf-8"))
MATRIZ = json.loads((REFS / "obelisco-matrix.json").read_text("utf-8"))
OBS = json.loads(TESTIGO.read_text("utf-8"))
INDICE = {c["id"]: c for c in DATOS["criteria"]}


def _leer(ruta):
    return Path(ruta).read_text("utf-8")


def _cli(script, *args, entrada=None):
    """Un script de la skill como proceso, con la salida decodificada como UTF-8."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-B", str(script)] + [str(a) for a in args], capture_output=True,
                       input=entrada, env=env, timeout=120)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _wcag(*args):
    return _cli(SCRIPTS / "wcag.py", *args)


def _registro(**cambios):
    """Un registro valido de nivel AA, con todo en not_tested, al que se le aplican los cambios."""
    doc = W.plantilla_de_registro("AA", [], [], DATOS)
    for k, v in cambios.items():
        doc[k] = v
    return doc


def _fila(doc, sc):
    return next(f for f in doc["criteria"] if f["sc"] == sc)


def _codigos(doc):
    return {e["code"] for e in W.validar_registro(doc, DATOS)}


# -- los criterios: una sola fuente ------------------------------------------------------------------

def test_e01_ochenta_y_seis_criterios_contra_el_testigo(t):
    """E-01 — 86 criterios, A 31 · AA 24 · AAA 31, ids unicos, y id, nombre y nivel como el W3C."""
    crit = DATOS["criteria"]
    t.igual("E-01 son 86", 86, len(crit))
    t.igual("E-01 A 31, AA 24, AAA 31", {"A": 31, "AA": 24, "AAA": 31}, dict(Counter(c["level"] for c in crit)))
    t.igual("E-01 ids unicos", len(crit), len({c["id"] for c in crit}))
    testigo = {c["id"]: c for c in OBS["criteria"]}
    t.igual("E-01 el testigo del W3C tiene los mismos 86 ids", set(testigo), set(INDICE))
    for i, c in INDICE.items():
        if i in testigo:
            t.igual("E-01 %s: nombre y nivel como el W3C" % i, (testigo[i]["name"], testigo[i]["level"]), (c["name"], c["level"]))
    t.verdadero("E-01 el testigo lleva el hash de su origen", re.fullmatch(r"[0-9a-f]{64}", OBS["sha256"]) is not None)


def test_e02_el_criterio_retirado_no_es_uno_de_los_86(t):
    """E-02 — 4.1.1 vive en `removed`, sin nivel y con su motivo; ningun criterio de los 86 va sin nivel."""
    t.verdadero("E-02 4.1.1 no esta entre los 86", "4.1.1" not in INDICE)
    t.igual("E-02 un solo retirado", ["4.1.1"], [r["id"] for r in DATOS["removed"]])
    r = DATOS["removed"][0]
    t.verdadero("E-02 sin nivel", r["level"] is None)
    t.contiene("E-02 con el motivo", "removed", r["status"])
    t.contiene("E-02 manda el marcado a 1.3.1", "1.3.1", " ".join(r["route_to"]))
    t.contiene("E-02 y a 4.1.2", "4.1.2", " ".join(r["route_to"]))
    t.vacio("E-02 ninguno de los 86 va sin nivel", [c["id"] for c in DATOS["criteria"] if not c["level"]])
    t.igual("E-02 el testigo tambien lo tiene aparte, sin nivel", ["4.1.1"], [x["id"] for x in OBS["removed"]])


def test_e03_los_nueve_criterios_nuevos_de_2_2(t):
    """E-03 — nueve criterios nuevos, con su nivel, y ningun otro marcado como nuevo."""
    nuevos = {"2.4.11": "AA", "2.4.12": "AAA", "2.4.13": "AAA", "2.5.7": "AA", "2.5.8": "AA",
              "3.2.6": "A", "3.3.7": "A", "3.3.8": "AA", "3.3.9": "AAA"}
    marcados = {c["id"]: c["level"] for c in DATOS["criteria"] if c["new_in_22"]}
    t.igual("E-03 los nueve y ninguno mas, con su nivel", nuevos, marcados)


_CONTEOS_VIEJOS = (
    re.compile(r"\b87\s+(?:success\s+)?(?:criteria|criterios)", re.IGNORECASE),
    re.compile(r"\bLevel A\s*=\s*32\b|\bA\s*=\s*32\b"),
    re.compile(r"\b30 testable\b"),
)


def _archivos_del_cambio():
    out = [SKILL / "SKILL.md"] + sorted(p for p in REFS.rglob("*.md"))
    for s in ("dev-ui", "dev-responsive", "dev-frontend-implementation"):
        out.append(DESARROLLO / "skills" / s / "SKILL.md")
    out.append(DESARROLLO / "agents" / "dev-frontend.md")
    return out


def test_e04_ningun_texto_afirma_un_conteo_distinto(t):
    """E-04 — ningun archivo de la skill ni de las skills de frontend dice 87 criterios, A = 32 ni 30 testable."""
    hallados = []
    for ruta in _archivos_del_cambio():
        for n, linea in enumerate(_leer(ruta).splitlines(), 1):
            if any(p.search(linea) for p in _CONTEOS_VIEJOS):
                hallados.append("%s:%d" % (ruta.relative_to(RAIZ), n))
    t.vacio("E-04 sin conteos viejos", hallados)
    alcance = _leer(REFS / "scope-and-sources.md")
    t.contiene("E-04 el alcance dice 86", "86 criteria", alcance)
    t.contiene("E-04 con A 31, AA 24, AAA 31", "A 31, AA 24, AAA 31", alcance)
    t.contiene("E-04 y que 4.1.1 fue retirado", "removed", alcance)


def test_e05_el_conteo_sale_de_los_datos(t):
    """E-05 — `wcag.py count` imprime 86, 31, 24 y 31, y cambia si cambia el JSON."""
    codigo, salida, _ = _wcag("count")
    t.igual("E-05 sale con 0", 0, codigo)
    for n in ("86", "A 31", "AA 24", "AAA 31"):
        t.contiene("E-05 imprime %s" % n, n, salida)
    codigo, salida, _ = _wcag("count", "--json")
    t.igual("E-05 en JSON", {"total": 86, "by_level": {"A": 31, "AA": 24, "AAA": 31}, "removed": ["4.1.1"]}, json.loads(salida))
    recortado = json.loads(json.dumps(DATOS))
    recortado["criteria"] = [c for c in recortado["criteria"] if c["id"] != "2.4.13"]
    c = W.conteo(recortado)
    t.igual("E-05 sin un criterio AAA el conteo baja a 85 y a 30", (85, 30), (c["total"], c["by_level"]["AAA"]))


def test_e06_pruebas_requeridas_por_criterio(t):
    """E-06 — `requires` usa solo browser, keyboard y screen_reader, y los criterios clave piden lo que corresponde."""
    t.igual("E-06 las familias", ["browser", "keyboard", "screen_reader"], DATOS["families"])
    for c in DATOS["criteria"]:
        t.verdadero("E-06 %s: requires dentro del vocabulario" % c["id"], set(c["requires"]) <= set(DATOS["families"]))
    for sc in ("2.1.1", "2.1.2", "2.4.7"):
        t.verdadero("E-06 %s pide teclado" % sc, "keyboard" in INDICE[sc]["requires"])
    for sc in ("1.4.10", "2.5.8"):
        t.verdadero("E-06 %s pide navegador" % sc, "browser" in INDICE[sc]["requires"])
    t.verdadero("E-06 4.1.3 pide lector de pantalla", "screen_reader" in INDICE["4.1.3"]["requires"])


# -- consultar sin cargar todo --------------------------------------------------------------------------

def test_e07_un_criterio_solo(t):
    """E-07 — `criterion 2.4.11` imprime ese criterio y nada de los vecinos, en menos de 6.000 caracteres."""
    codigo, salida, _ = _wcag("criterion", "2.4.11")
    t.igual("E-07 sale con 0", 0, codigo)
    t.contiene("E-07 nombre", "Focus Not Obscured (Minimum)", salida)
    t.contiene("E-07 nivel", "nivel AA", salida)
    t.contiene("E-07 texto normativo", "entirely hidden", salida)
    t.no_contiene("E-07 la seccion de 2.4.12 no esta", "### 2.4.12", salida)
    t.no_contiene("E-07 la seccion de 2.4.10 no esta", "### 2.4.10", salida)
    t.igual("E-07 una sola seccion", 1, salida.count("### "))
    t.verdadero("E-07 menos de 6.000 caracteres (%d)" % len(salida), len(salida) < 6000)


def test_e08_criterio_retirado(t):
    """E-08 — `criterion 4.1.1` dice que fue retirado, que no tiene nivel, y manda a 1.3.1 y 4.1.2."""
    codigo, salida, _ = _wcag("criterion", "4.1.1")
    t.igual("E-08 sale con 0", 0, codigo)
    t.contiene("E-08 retirado", "retirado en WCAG 2.2", salida)
    t.contiene("E-08 sin nivel", "no tiene nivel", salida)
    t.contiene("E-08 1.3.1", "1.3.1", salida)
    t.contiene("E-08 4.1.2", "4.1.2", salida)
    t.no_contiene("E-08 no le inventa un nivel", "nivel A", salida)


def test_e09_criterio_inexistente(t):
    """E-09 — `criterion 9.9.9` sale con error, dice que no existe y no imprime un traceback."""
    codigo, salida, errores = _wcag("criterion", "9.9.9")
    t.verdadero("E-09 sale con un codigo distinto de 0", codigo != 0)
    t.contiene("E-09 dice que no existe", "No existe el criterio 9.9.9", errores)
    t.no_contiene("E-09 sin traceback", "Traceback", salida + errores)


def test_e10_listas_por_nivel(t):
    """E-10 — `list --level AA` lista los 24 AA; `--up-to AA` lista 55; con nombre y nivel."""
    _, salida, _ = _wcag("list", "--level", "AA")
    lineas = [l for l in salida.splitlines() if re.match(r"^\d\.\d\.\d+\s", l)]
    t.igual("E-10 24 AA", 24, len(lineas))
    t.verdadero("E-10 todos de nivel AA", all(re.search(r"\sAA\s", l) for l in lineas))
    t.contiene("E-10 con nombre", "Focus Not Obscured (Minimum)", salida)
    t.contiene("E-10 el total", "— 24 criterios", salida)
    _, salida, _ = _wcag("list", "--up-to", "AA")
    lineas = [l for l in salida.splitlines() if re.match(r"^\d\.\d\.\d+\s", l)]
    t.igual("E-10 hasta AA son 55", 55, len(lineas))
    t.vacio("E-10 ningun AAA entre ellos", [l for l in lineas if re.search(r"\sAAA\s", l)])


def _filas_de_tareas():
    """Las filas de la primera tabla de «Where to read — by task» de SKILL.md: id de tarea -> texto."""
    texto = _leer(SKILL / "SKILL.md")
    bloque = texto.split("## Where to read — by task", 1)[1].split("\n\n| Need", 1)[0]
    return dict(re.findall(r"^\| `([\w-]+)` \| (.+) \|$", bloque, re.M))


def test_e11_cada_tarea_se_resuelve(t):
    """E-11 — `task <id>` devuelve criterios y guia de cada tarea de la tabla, y la guia existe."""
    filas = _filas_de_tareas()
    t.igual("E-11 la tabla tiene las mismas tareas que los datos", set(DATOS["tasks"]), set(filas))
    for tarea, destino in filas.items():
        codigo, salida, _ = _wcag("task", tarea)
        t.igual("E-11 task %s sale con 0" % tarea, 0, codigo)
        t.contiene("E-11 task %s dice su guia" % tarea, "Guía:", salida)
        t.contiene("E-11 task %s trae criterios" % tarea, "Criterios A/AA", salida)
        ruta = re.search(r"`([^`]+)`", destino)
        if tarea == "responsive":
            t.verdadero("E-11 la tarea responsive apunta a una skill que existe",
                        (DESARROLLO / "skills" / "dev-responsive" / "SKILL.md").is_file())
        else:
            t.verdadero("E-11 la guia de %s existe" % tarea, ruta is not None and (SKILL / ruta.group(1)).is_file())
    codigo, _, errores = _wcag("task", "no-existe")
    t.verdadero("E-11 una tarea inexistente sale con error", codigo != 0 and "No existe la tarea" in errores)


def test_e12_fila_de_un_componente(t):
    """E-12 — `component form-text` imprime lo que Obelisco declara, lo adicional con su origen y como se verifica."""
    codigo, salida, _ = _wcag("component", "form-text")
    t.igual("E-12 sale con 0", 0, codigo)
    t.contiene("E-12 los criterios declarados", "Criterios que Obelisco declara", salida)
    t.contiene("E-12 con nivel", "3.3.2 Labels or Instructions (A)", salida)
    t.contiene("E-12 origen obelisco", "[obelisco]", salida)
    t.contiene("E-12 origen wcag", "[wcag]", salida)
    t.contiene("E-12 la cita literal", "Cada campo de texto debe tener una etiqueta", salida)
    t.contiene("E-12 la verificacion", "Verificación:", salida)
    t.contiene("E-12 con las pruebas manuales", "pruebas manuales: navegador, teclado, lector de pantalla", salida)
    t.contiene("E-12 y las reglas estaticas", "reglas estáticas que cubren una parte: control-no-accessible-name", salida)
    _, salida, _ = _wcag("component", "breadcrumb")
    t.contiene("E-12 un AAA se marca como adicional", "AAA: adicional, no es parte de AA", salida)
    _, salida, _ = _wcag("component", "tabs")
    t.contiene("E-12 dice cuando Obelisco no publica accesibilidad", "SIN sección de accesibilidad publicada", salida)


def test_e13_sin_referencias_huerfanas(t):
    """E-13 — todo archivo que la tabla de SKILL.md nombra existe, y todo archivo de references/ esta en la tabla."""
    texto = _leer(SKILL / "SKILL.md")
    tablas = "\n".join(l for l in texto.split("## Where to read — by task", 1)[1].split("## Custom components", 1)[0].splitlines() if l.startswith("|"))
    nombrados = {n for n in re.findall(r"`references/([\w./-]+?)`", tablas) if not n.endswith("/")}
    for n in sorted(nombrados):
        t.verdadero("E-13 existe references/%s" % n, (REFS / n).exists())
    de_references = sorted(p.name for p in REFS.iterdir() if p.is_file())
    for n in de_references:
        t.verdadero("E-13 references/%s esta en la tabla de SKILL.md" % n, n in nombrados)
    fuente = _leer(REFS / "wcag22" / "SOURCE.md")
    for p in sorted((REFS / "wcag22").glob("*.md")):
        if p.name != "SOURCE.md":
            t.verdadero("E-13 SOURCE.md lista wcag22/%s" % p.name, p.name in fuente)


def test_e14_la_entrada_es_corta(t):
    """E-14 — SKILL.md no pasa de 8.000 caracteres y la carga de formularios no pasa de los 12.573 de antes."""
    entrada = _leer(SKILL / "SKILL.md")
    guia = _leer(REFS / "task-forms.md")
    t.verdadero("E-14 SKILL.md: %d caracteres, techo 8.000" % len(entrada), len(entrada) <= 8000)
    t.verdadero("E-14 formularios: %d caracteres, techo 12.573" % (len(entrada) + len(guia)), len(entrada) + len(guia) <= 12573)


def _costo_descriptor(ruta):
    texto = _leer(ruta)
    cabecera = re.search(r"^---\s*(.*?)^---", texto, re.S | re.M).group(1)
    nombre = re.search(r"^name:\s*(.*)$", cabecera, re.M).group(1)
    descr = re.search(r"^description:\s*(.*)$", cabecera, re.M).group(1)
    return len(nombre + descr) // 4


def test_e15_el_costo_que_se_paga_siempre_no_crece(t):
    """E-15 — name + description de las cinco piezas: a lo sumo 20 tokens mas que los 591 de v0.35.0."""
    piezas = [DESARROLLO / "skills" / s / "SKILL.md" for s in ("dev-accessibility", "dev-ui", "dev-responsive", "dev-frontend-implementation")]
    piezas.append(DESARROLLO / "agents" / "dev-frontend.md")
    total = sum(_costo_descriptor(p) for p in piezas)
    t.verdadero("E-15 %d tokens, techo 611" % total, total <= 591 + 20)


# -- tres fuentes, niveles a la vista --------------------------------------------------------------------

def test_e16_cada_requisito_dice_de_quien_es(t):
    """E-16 — `origin` en {wcag, obelisco, harness}; lo de Obelisco trae su pagina y su fecha de consulta."""
    origenes = {"wcag", "obelisco", "harness"}
    t.igual("E-16 la matriz declara los tres origenes", origenes, set(MATRIZ["origins"]))
    for c in MATRIZ["components"] + [MATRIZ["custom"]]:
        for r in c["requirements"]:
            t.verdadero("E-16 %s: origen valido (%s)" % (c["id"], r["origin"]), r["origin"] in origenes)
            if r["origin"] == "obelisco":
                t.verdadero("E-16 %s: un requisito de Obelisco trae su pagina" % c["id"],
                            str(c.get("obelisco_page") or "").startswith("https://gcba.github.io/Obelisco-V2/"))
                t.verdadero("E-16 %s: y la fecha de consulta" % c["id"], re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.get("obelisco_consulted", "")) is not None)
        if c["declared"]:
            t.verdadero("E-16 %s: lo que declara Obelisco trae su pagina y su fecha" % c["id"], bool(c.get("obelisco_page")) and bool(c.get("obelisco_consulted")))


def _criterios_de_la_matriz():
    citados = set()
    for c in MATRIZ["components"] + [MATRIZ["custom"]]:
        citados.update(d["sc"] for d in c["declared"])
        for r in c["requirements"]:
            citados.update(r["sc"])
    return citados


def test_e17_los_aaa_de_obelisco_son_adicionales(t):
    """E-17 — todo AAA que la matriz cita figura en aaa_additional, nunca en el conjunto base de AA."""
    adicionales = {a["sc"]: a for a in MATRIZ["aaa_additional"]}
    for sc in ("2.4.13", "3.1.5", "2.2.5", "1.4.6"):
        t.verdadero("E-17 %s esta entre los adicionales" % sc, sc in adicionales)
    base = {i for i, c in INDICE.items() if c["level"] in ("A", "AA")}
    for sc, a in adicionales.items():
        t.igual("E-17 %s es AAA de verdad" % sc, "AAA", INDICE[sc]["level"])
        t.verdadero("E-17 %s no esta en la base A+AA" % sc, sc not in base)
        t.verdadero("E-17 %s dice quien lo pide y de donde" % sc, a["asked_by"] == "obelisco" and bool(a["source"]))
    citados_aaa = {sc for sc in _criterios_de_la_matriz() if INDICE[sc]["level"] == "AAA"}
    t.vacio("E-17 ningun AAA citado queda fuera de los adicionales", sorted(citados_aaa - set(adicionales)))
    for tarea, d in DATOS["tasks"].items():
        t.vacio("E-17 la tarea %s solo suma AAA que Obelisco nombra" % tarea, sorted(set(d["additional_aaa"]) - set(adicionales)))
        t.vacio("E-17 la tarea %s no cuenta un AAA entre los A/AA" % tarea, [s for s in d["criteria"] if INDICE[s]["level"] == "AAA"])


def _niveles_declarados_mal(componentes):
    malos = []
    for c in componentes:
        for d in c["declared"]:
            real = INDICE[d["sc"]]["level"]
            if d["declared_level"] not in (None, real) and "discrepancy" not in d:
                malos.append((c["id"], d["sc"], d["declared_level"], real))
    return malos


def test_e18_el_nivel_que_obelisco_declara_es_el_real(t):
    """E-18 — el nivel declarado por Obelisco es el de WCAG 2.2, o la discrepancia esta registrada."""
    t.vacio("E-18 ningun nivel declarado difiere del real sin registrarlo", _niveles_declarados_mal(MATRIZ["components"]))
    falso = [{"id": "x", "declared": [{"sc": "1.3.4", "declared_level": "A"}]}]
    t.igual("E-18 el control detecta un 1.3.4 declarado como A", [("x", "1.3.4", "A", "AA")], _niveles_declarados_mal(falso))
    registrado = [{"id": "x", "declared": [{"sc": "1.3.4", "declared_level": "A", "discrepancy": "Obelisco dice A; WCAG 2.2 dice AA"}]}]
    t.vacio("E-18 y acepta la discrepancia registrada", _niveles_declarados_mal(registrado))
    t.verdadero("E-18 las discrepancias generales estan dichas", len(MATRIZ["discrepancies"]) >= 3)


REQUERIDOS = ("form-text", "form-select", "form-check", "form-radio", "form-search", "form-file", "form-validation",
              "button", "link", "modal", "table", "tabs", "alert", "status-message", "tooltip", "pagination",
              "breadcrumb", "collapse", "nav-horizontal", "nav-vertical", "header", "footer", "steps-form", "grid")


def test_e19_la_matriz_cubre_formularios_y_pantallas(t):
    """E-19 — la matriz cubre los componentes de un formulario o una pantalla de tramite, con verificacion."""
    ids = {c["id"] for c in MATRIZ["components"]}
    t.vacio("E-19 no falta ningun componente requerido", sorted(set(REQUERIDOS) - ids))
    reglas_del_motor = set(A.REGLAS)
    for c in MATRIZ["components"]:
        t.verdadero("E-19 %s: pagina de Obelisco" % c["id"], c["obelisco_page"].startswith("https://gcba.github.io/Obelisco-V2/"))
        t.verdadero("E-19 %s: trae requisitos" % c["id"], len(c["requirements"]) > 0)
        t.verdadero("E-19 %s: dice si Obelisco documenta su accesibilidad" % c["id"], isinstance(c["obelisco_accessibility_documented"], bool))
        v = c.get("verification")
        t.verdadero("E-19 %s: trae `verification` con static y manual" % c["id"],
                    isinstance(v, dict) and isinstance(v.get("static"), list) and isinstance(v.get("manual"), list))
        if not isinstance(v, dict):
            continue
        for r in v["static"]:
            t.verdadero("E-19 %s: la regla %s existe en el motor" % (c["id"], r), r in reglas_del_motor)
        for fam in v["manual"]:
            t.verdadero("E-19 %s: la prueba %s esta en el vocabulario" % (c["id"], fam), fam in DATOS["families"])
        # las pruebas manuales de la fila no se desvian de lo que piden sus criterios en wcag22-criteria.json
        scs = [d["sc"] for d in c["declared"]] + [s for r in c["requirements"] for s in r["sc"]]
        derivadas = [f for f in DATOS["families"] if any(f in INDICE[s]["requires"] for s in scs)]
        t.igual("E-19 %s: las pruebas manuales salen de los criterios de la fila" % c["id"], derivadas, v["manual"])
        if not c["obelisco_accessibility_documented"]:
            t.verdadero("E-19 %s: sin seccion en Obelisco, lo dice y no lo inventa" % c["id"],
                        any(r["origin"] == "harness" and "Obelisco publishes no accessibility section" in r["text"] for r in c["requirements"])
                        or not any(r["origin"] == "obelisco" for r in c["requirements"]))


def test_e20_la_ui_propia_exige_diseno_explicito(t):
    """E-20 — la fila `custom` exige nombre, rol y estados, modelo de teclado y de foco, y las tres pruebas manuales."""
    c = MATRIZ["custom"]
    texto = " ".join(r["text"] for r in c["requirements"]).lower()
    for pieza in ("accessible name", "states", "keyboard model", "focus model"):
        t.contiene("E-20 pide %s" % pieza, pieza, texto)
    t.igual("E-20 las tres pruebas manuales", ["browser", "keyboard", "screen_reader"], c["verification"]["manual"])
    t.verdadero("E-20 y reglas estaticas que existen en el motor", c["verification"]["static"] and set(c["verification"]["static"]) <= set(A.REGLAS))
    codigo, salida, _ = _wcag("component", "custom")
    t.verdadero("E-20 `component custom` muestra el piso de pruebas", codigo == 0 and "navegador, teclado, lector de pantalla" in salida)


def test_e21_la_skill_nombra_las_tres_fuentes(t):
    """E-21 — SKILL.md nombra las tres fuentes, propone AA, dice que los AAA de Obelisco son adicionales y que no certifica."""
    texto = _leer(SKILL / "SKILL.md")
    for pieza in ("WCAG 2.2", "Obelisco V2", "Harness / project"):
        t.contiene("E-21 nombra %s" % pieza, pieza, texto)
    t.contiene("E-21 propone AA", "WCAG 2.2 AA", texto)
    t.contiene("E-21 es una propuesta", "proposal", texto)
    t.contiene("E-21 los AAA de Obelisco son adicionales", "are extra", texto)
    t.contiene("E-21 no los presenta como AA", "Never present one as AA", texto)
    t.contiene("E-21 no certifica conformidad", "never self-certifies conformance", texto)
    t.contiene("E-21 un analisis limpio no es conformidad", "A clean static analysis is not conformance", texto)


# -- el registro de evidencia ------------------------------------------------------------------------------

def test_e22_la_plantilla_del_registro(t):
    """E-22 — `register template --level AA`: 55 criterios en not_tested, 4.1.1 not_applicable, tres pruebas not_performed."""
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / "evidencia.json"
        codigo, salida, _ = _wcag("register", "template", "--level", "AA", "--out", ruta)
        t.igual("E-22 sale con 0", 0, codigo)
        doc = json.loads(ruta.read_text("utf-8"))
    cuenta = Counter(f["result"] for f in doc["criteria"])
    t.igual("E-22 55 en not_tested", 55, cuenta["not_tested"])
    t.igual("E-22 uno en not_applicable", 1, cuenta["not_applicable"])
    t.igual("E-22 y ese es 4.1.1", "not_applicable", _fila(doc, "4.1.1")["result"])
    t.contiene("E-22 con su motivo", "Retirado", _fila(doc, "4.1.1")["reason"])
    t.igual("E-22 las tres pruebas en not_performed", {"browser": "not_performed", "keyboard": "not_performed", "screen_reader": "not_performed"}, doc["tests"])
    t.vacio("E-22 el registro vacio ya es valido", W.validar_registro(doc, DATOS))


def test_e23_no_se_omite_ningun_criterio(t):
    """E-23 — un registro sin un criterio del nivel objetivo falla y nombra el criterio."""
    doc = _registro()
    doc["criteria"] = [f for f in doc["criteria"] if f["sc"] != "2.4.11"]
    errores = W.validar_registro(doc, DATOS)
    t.contiene("E-23 el codigo", "missing_criterion", " ".join(e["code"] for e in errores))
    t.contiene("E-23 nombra el criterio", "2.4.11", " ".join(e["message"] for e in errores))
    t.contiene("E-23 y su nombre", "Focus Not Obscured (Minimum)", " ".join(e["message"] for e in errores))


def test_e24_el_vocabulario_de_resultados(t):
    """E-24 — un resultado fuera de pass, fail, not_applicable y not_tested falla."""
    doc = _registro()
    _fila(doc, "1.1.1")["result"] = "aprobado"
    t.contiene("E-24 «aprobado» no es un valor del contrato", "bad_result", _codigos(doc))
    doc = _registro()
    _fila(doc, "1.1.1")["result"] = "passed"
    t.contiene("E-24 «passed» tampoco", "bad_result", _codigos(doc))


def test_e25_un_fallo_trae_lugar_evidencia_y_correccion(t):
    """E-25 — `fail` sin ubicacion, evidencia o correccion se rechaza, y dice cual falta."""
    for faltante in ("location", "evidence", "fix"):
        doc = _registro()
        f = _fila(doc, "1.1.1")
        f.pop("reason", None)
        f.update({"result": "fail", "location": "a.tsx:1", "evidence": "img sin alt", "fix": "agregar alt", "evidence_types": ["static"]})
        del f[faltante]
        errores = W.validar_registro(doc, DATOS)
        t.contiene("E-25 sin %s: se rechaza" % faltante, "incomplete_fail", " ".join(e["code"] for e in errores))
        t.contiene("E-25 y dice que falta %s" % faltante, faltante, " ".join(e["message"] for e in errores))
    doc = _registro()
    f = _fila(doc, "1.1.1")
    f.pop("reason", None)
    f.update({"result": "fail", "location": "a.tsx:1", "evidence": "img sin alt", "fix": "agregar alt", "evidence_types": ["static"]})
    t.vacio("E-25 con las tres, es valido", W.validar_registro(doc, DATOS))


def test_e26_un_pass_exige_las_pruebas_que_el_criterio_requiere(t):
    """E-26 — `pass` sobre un criterio de teclado se rechaza sin la prueba; se acepta con ella y su evidencia."""
    doc = _registro()
    f = _fila(doc, "2.1.1")
    f.pop("reason", None)
    f.update({"result": "pass", "evidence": "recorrido con Tab", "evidence_types": ["static"]})
    t.contiene("E-26 sin la prueba de teclado: se rechaza", "pass_without_test", _codigos(doc))
    doc["tests"]["keyboard"] = "performed"
    t.contiene("E-26 con la prueba pero sin citarla: se rechaza", "pass_without_evidence_of_test", _codigos(doc))
    f["evidence_types"] = ["keyboard"]
    t.vacio("E-26 con la prueba hecha y citada: se acepta", [e for e in W.validar_registro(doc, DATOS) if e["sc"] == "2.1.1"])
    f["evidence"] = ""
    t.contiene("E-26 un pass sin evidencia se rechaza siempre", "pass_without_evidence", _codigos(doc))
    doc = _registro()
    f = _fila(doc, "2.4.2")
    f.pop("reason", None)
    f.update({"result": "pass", "evidence": "", "evidence_types": []})
    t.contiene("E-26 aun el criterio que no pide pruebas necesita evidencia", "pass_without_evidence", _codigos(doc))
    doc = _registro()
    f = _fila(doc, "1.1.1")
    f.update({"result": "fail", "location": "a:1", "evidence": "x", "fix": "y", "evidence_types": ["keyboard"]})
    f.pop("reason", None)
    t.contiene("E-26 evidencia de una prueba que no se hizo se rechaza", "evidence_type_not_performed", _codigos(doc))


def test_e27_no_aplicable_y_no_probado_necesitan_motivo(t):
    """E-27 — `not_applicable` y `not_tested` sin `reason` se rechazan."""
    for resultado in ("not_applicable", "not_tested"):
        doc = _registro()
        f = _fila(doc, "1.2.2")
        f["result"] = resultado
        f.pop("reason", None)
        t.contiene("E-27 %s sin reason: se rechaza" % resultado, "missing_reason", _codigos(doc))
        f["reason"] = "no hay video"
        t.vacio("E-27 %s con reason: se acepta" % resultado, W.validar_registro(doc, DATOS))


def test_e28_4_1_1_solo_como_no_aplicable(t):
    """E-28 — 4.1.1 como fail o como pass se rechaza; solo puede ser not_applicable."""
    for resultado in ("fail", "pass"):
        doc = _registro()
        _fila(doc, "4.1.1")["result"] = resultado
        t.contiene("E-28 4.1.1 como %s se rechaza" % resultado, "removed_criterion", _codigos(doc))
    doc = _registro()
    t.vacio("E-28 como not_applicable, valido", W.validar_registro(doc, DATOS))
    doc = _registro()
    doc["criteria"] = [f for f in doc["criteria"] if f["sc"] != "4.1.1"]
    t.vacio("E-28 y tampoco hace falta la fila", W.validar_registro(doc, DATOS))


def test_e29_el_resumen_coincide_con_las_filas(t):
    """E-29 — un summary que no coincide con las filas se rechaza (declarar 13 y 12 cuando las filas dan 14 y 11)."""
    doc = _registro()
    doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 55}
    t.vacio("E-29 un resumen correcto se acepta", W.validar_registro(doc, DATOS))
    doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 54}
    errores = W.validar_registro(doc, DATOS)
    t.contiene("E-29 uno distinto se rechaza", "summary_mismatch", " ".join(e["code"] for e in errores))
    t.contiene("E-29 y dice lo que dan las filas", "no probado 55", " ".join(e["message"] for e in errores))
    for clave in ("pass", "fail", "not_applicable", "not_tested"):
        mal = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 55}
        mal[clave] += 1
        doc["summary"] = mal
        t.contiene("E-29 un conteo de %s que no coincide se rechaza" % clave, "summary_mismatch", _codigos(doc))
    doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1}
    t.contiene("E-29 un resumen al que le falta un conteo se rechaza", "summary_mismatch", _codigos(doc))

    # el error del informe de la evaluacion: «13 de nivel A y 12 de AA» cuando las filas dan 14 y 11
    doc = _registro()
    a = [c["id"] for c in DATOS["criteria"] if c["level"] == "A"][:14]
    aa = [c["id"] for c in DATOS["criteria"] if c["level"] == "AA"][:11]
    for sc in a + aa:
        f = _fila(doc, sc)
        f.pop("reason", None)
        f.update({"result": "fail", "location": "x.html:1", "evidence": "falla", "fix": "arreglar", "evidence_types": ["static"]})
    doc["summary"] = {"pass": 0, "fail": 25, "not_applicable": 1, "not_tested": 30, "fail_by_level": {"A": 13, "AA": 12, "AAA": 0}}
    errores = W.validar_registro(doc, DATOS)
    t.contiene("E-29 13 de A y 12 de AA cuando las filas dan 14 y 11: se rechaza", "summary_mismatch", " ".join(e["code"] for e in errores))
    t.contiene("E-29 y dice lo que dan las filas", "A 14 · AA 11", " ".join(e["message"] for e in errores))
    doc["summary"]["fail_by_level"] = {"A": 14, "AA": 11, "AAA": 0}
    t.vacio("E-29 con los 14 y los 11 correctos, se acepta", W.validar_registro(doc, DATOS))


def test_e30_criterios_adicionales(t):
    """E-30 — `target.additional` pide una fila por adicional; un AAA que no esta entre ellos no se exige."""
    doc = W.plantilla_de_registro("AA", ["2.4.13"], [], DATOS)
    t.verdadero("E-30 la plantilla trae la fila adicional", any(f["sc"] == "2.4.13" for f in doc["criteria"]))
    t.vacio("E-30 con la fila, valido", W.validar_registro(doc, DATOS))
    doc["criteria"] = [f for f in doc["criteria"] if f["sc"] != "2.4.13"]
    t.contiene("E-30 sin la fila adicional, se rechaza", "missing_criterion", _codigos(doc))
    doc = _registro()
    t.verdadero("E-30 el registro AA no trae ningun AAA", not any(INDICE.get(f["sc"], {}).get("level") == "AAA" for f in doc["criteria"]))
    t.vacio("E-30 y no se exige", W.validar_registro(doc, DATOS))
    doc["criteria"].append({"sc": "1.4.6", "result": "not_tested", "reason": "no se pidio"})
    t.vacio("E-30 un AAA que no se exigia se acepta si aparece", W.validar_registro(doc, DATOS))

    # ... y se cuenta aparte: no entra en los conteos de lo que se exigia
    r = W.resumir_registro(doc, DATOS)
    t.igual("E-30 los 56 de lo exigido (55 + 4.1.1) no incluyen la fila extra", 56, sum(r["counts"].values()))
    t.igual("E-30 y la fila extra se cuenta aparte", 1, sum(r["extra"].values()))
    t.igual("E-30 como no probada", 1, r["extra"]["not_tested"])
    doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 55}
    t.vacio("E-30 un resumen de lo exigido, sin la extra, es correcto", W.validar_registro(doc, DATOS))
    doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 56}
    t.contiene("E-30 un resumen que la mezcla con lo exigido se rechaza", "summary_mismatch", _codigos(doc))
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / "extra.json"
        doc["summary"] = {"pass": 0, "fail": 0, "not_applicable": 1, "not_tested": 55}
        ruta.write_text(json.dumps(doc), encoding="utf-8")
        codigo, salida, _ = _wcag("register", "validate", ruta)
        t.igual("E-30 el CLI lo da por valido", 0, codigo)
        t.contiene("E-30 y dice la cuenta de lo exigido", "Registro válido: 56 criterios", salida)
        t.contiene("E-30 y que la extra se cuenta aparte", "contados aparte (no probado 1)", salida)
        codigo, salida, _ = _wcag("register", "validate", ruta, "--json")
        t.verdadero("E-30 en JSON, aparte", codigo == 0 and json.loads(salida)["extra"]["not_tested"] == 1 and json.loads(salida)["counts"]["not_tested"] == 55)


def test_e31_niveles_de_un_texto(t):
    """E-31 — `levels` marca 1.3.4 como A, un criterio inexistente y 4.1.1 con nivel; acepta lo correcto."""
    def problemas(texto):
        return W.comprobar_niveles(texto, "x", DATOS)

    t.contiene("E-31 1.3.4 como A es un par incorrecto", "wrong_level", " ".join(p["code"] for p in problemas("**SC 1.3.4 Orientation (Level A)**")))
    t.vacio("E-31 1.3.4 como AA es correcto", problemas("**SC 1.3.4 Orientation (Level AA)**"))
    t.contiene("E-31 5.1.1 no existe", "unknown_sc", " ".join(p["code"] for p in problemas("SC 5.1.1 Nada (Level A)")))
    t.contiene("E-31 4.1.1 con nivel se marca", "removed_with_level", " ".join(p["code"] for p in problemas("4.1.1 Parsing (Level A)")))
    t.vacio("E-31 4.1.1 con nivel, hablando de WCAG 2.1, se acepta", problemas("4.1.1 Parsing (Level A) in WCAG 2.1"))
    t.contiene("E-31 la fila de tabla incorrecta", "wrong_level", " ".join(p["code"] for p in problemas("| 1.3.4 | Orientation | A | Met |")))
    t.vacio("E-31 la fila de tabla correcta", problemas("| 1.3.4 | Orientation | AA | Met |"))
    t.vacio("E-31 la fila con el nombre en la misma celda, correcta", problemas("| 2.4.11 Focus Not Obscured (Minimum) | AA | wcag | x |"))
    t.contiene("E-31 y la incorrecta", "wrong_level", " ".join(p["code"] for p in problemas("| 2.4.11 Focus Not Obscured (Minimum) | AAA | wcag | x |")))
    t.vacio("E-31 una frase que habla de otro criterio no se confunde",
            problemas("Follow Success Criterion 2.1.1. If that is not possible, it is not possible to meet this Level AAA success criterion."))
    with tempfile.TemporaryDirectory() as d:
        mal = Path(d) / "mal.md"
        mal.write_text("**SC 1.3.4 Orientation (Level A)**\n", encoding="utf-8")
        bien = Path(d) / "bien.md"
        bien.write_text("**SC 1.3.4 Orientation (Level AA)**\n", encoding="utf-8")
        codigo, salida, _ = _wcag("levels", mal)
        t.verdadero("E-31 el CLI sale con 1 y dice la linea", codigo == 1 and "mal.md:1" in salida and "es nivel AA, no A" in salida)
        codigo, salida, _ = _wcag("levels", bien)
        t.igual("E-31 el CLI sale con 0 si esta bien", 0, codigo)


def test_e32_ningun_nivel_mal_escrito_en_lo_que_se_carga(t):
    """E-32 — `levels` sobre la skill, sus referencias y las skills de frontend: ningun par mal escrito."""
    archivos = [SKILL / "SKILL.md"] + sorted(REFS.rglob("*.md"))
    for s in ("dev-ui", "dev-responsive", "dev-frontend-implementation"):
        archivos.append(DESARROLLO / "skills" / s / "SKILL.md")
    for ruta in archivos:
        malos = W.comprobar_niveles(_leer(ruta), str(ruta.relative_to(RAIZ)), DATOS)
        t.vacio("E-32 %s sin pares mal escritos" % ruta.relative_to(RAIZ), ["%d %s" % (p["line"], p["message"]) for p in malos])


# -- contraste ------------------------------------------------------------------------------------------------

def _ratio(fg, bg, **kw):
    return C.calcular(fg, bg, kw.get("base"), kw.get("tam"), kw.get("negrita", False))


def test_e33_valores_exactos(t):
    """E-33 — 21:1, 4,48:1 para #777 y 4,54:1 para #767676; para entradas opacas, lo mismo que el script original."""
    t.igual("E-33 negro sobre blanco", 21.0, _ratio("#000", "#fff")["ratio"])
    t.igual("E-33 #777 sobre #fff", 4.48, _ratio("#777", "#fff")["ratio"])
    t.igual("E-33 #767676 sobre #fff", 4.54, _ratio("#767676", "#ffffff")["ratio"])
    t.verdadero("E-33 #777 no cumple 1.4.3 para texto normal", not _ratio("#777", "#fff")["criteria"]["1.4.3"]["normal_text"])
    t.verdadero("E-33 #767676 si", _ratio("#767676", "#fff")["criteria"]["1.4.3"]["normal_text"])
    # el calculo original: (L1 + 0,05) / (L2 + 0,05) con la luminancia del glosario de WCAG
    def original(c1, c2):
        def ch(v):
            v = v / 255
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        def lum(rgb):
            r, g, b = (ch(x) for x in rgb)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        a, b = lum(c1), lum(c2)
        return (max(a, b) + 0.05) / (min(a, b) + 0.05)
    for fg, bg in (((51, 51, 51), (255, 255, 255)), ((0, 51, 102), (204, 214, 224)), ((119, 119, 119), (238, 238, 238))):
        got = C.relacion(fg, bg)
        t.verdadero("E-33 igual que el original para %s sobre %s" % (fg, bg), abs(got - original(fg, bg)) < 1e-12)
    codigo, salida, _ = _cli(SCRIPTS / "contrast.py", "#777", "#fff", "--json")
    t.igual("E-33 el CLI da 4.48:1", "4.48:1", json.loads(salida)["ratio_text"])


def test_e34_el_alfa_se_compone(t):
    """E-34 — rgba(0,0,0,0.5) sobre blanco se compone en #808080 y da 3,95:1, no 21:1."""
    r = _ratio("rgba(0,0,0,0.5)", "#ffffff")
    t.igual("E-34 el color compuesto", "#808080", r["foreground"])
    t.igual("E-34 la relacion", 3.95, r["ratio"])
    t.verdadero("E-34 no es el 21:1 de descartar la transparencia", r["ratio"] < 4)
    t.verdadero("E-34 dice como compuso", any("compuesto" in n for n in r["composition"]))
    t.igual("E-34 con alfa 1 no cambia", 21.0, _ratio("rgba(0,0,0,1)", "#fff")["ratio"])
    t.igual("E-34 con alfa 0 el primer plano desaparece", 1.0, _ratio("rgba(0,0,0,0)", "#fff")["ratio"])


def test_e35_formatos_de_color(t):
    """E-35 — #rgb, #rgba, #rrggbb, #rrggbbaa, rgb()/rgba() con comas o espacios, alfa en numero o %, hsl() y nombres."""
    t.igual("E-35 #rgb", (255, 255, 255, 1.0), C.leer_color("#fff"))
    t.igual("E-35 #rgba", 0.0, C.leer_color("#0000")[3])
    t.igual("E-35 #rrggbbaa", 128 / 255.0, C.leer_color("#00000080")[3])
    t.igual("E-35 rgb con comas", (10.0, 20.0, 30.0, 1.0), C.leer_color("rgb(10, 20, 30)"))
    t.igual("E-35 rgba con comas", 0.5, C.leer_color("rgba(0,0,0,0.5)")[3])
    t.igual("E-35 rgb con espacios y barra", 0.25, C.leer_color("rgb(0 0 0 / 0.25)")[3])
    t.igual("E-35 alfa en porcentaje", 0.5, C.leer_color("rgb(0 0 0 / 50%)")[3])
    t.igual("E-35 canales en porcentaje", 255.0, C.leer_color("rgb(100% 0% 0%)")[0])
    h = C.leer_color("hsl(0, 0%, 46.7%)")
    t.verdadero("E-35 hsl gris", abs(h[0] - 119.085) < 0.2 and h[0] == h[1] == h[2])
    t.igual("E-35 hsla con alfa", 0.5, C.leer_color("hsla(120, 100%, 25%, 0.5)")[3])
    t.igual("E-35 un nombre basico", (0.0, 0.0, 0.0, 1.0), C.leer_color("black"))
    t.igual("E-35 los formatos dan el mismo contraste", _ratio("#777", "#fff")["ratio"], _ratio("rgb(119 119 119)", "white")["ratio"])


def test_e36_fondo_translucido_pide_base(t):
    """E-36 — un fondo con alfa menor a 1 sin --backdrop no da numero (codigo 2); con la base, compone los dos niveles."""
    codigo, salida, errores = _cli(SCRIPTS / "contrast.py", "#000", "rgba(255,255,255,0.8)")
    t.igual("E-36 sin base sale con 2", 2, codigo)
    t.contiene("E-36 dice que falta la base", "--backdrop", errores)
    t.no_contiene("E-36 no inventa un ratio", ":1", salida)
    codigo, salida, _ = _cli(SCRIPTS / "contrast.py", "#000", "rgba(255,255,255,0.8)", "--backdrop", "#003366", "--json")
    t.igual("E-36 con la base calcula", 0, codigo)
    r = json.loads(salida)
    t.igual("E-36 el fondo efectivo", "#ccd6e0", r["background"])
    t.igual("E-36 la relacion sobre el fondo compuesto", 14.26, r["ratio"])
    t.verdadero("E-36 dice como compuso el fondo", any("fondo" in n for n in r["composition"]))
    codigo, _, errores = _cli(SCRIPTS / "contrast.py", "#000", "rgba(255,255,255,0.8)", "--backdrop", "rgba(0,0,0,0.5)")
    t.verdadero("E-36 una base translucida tampoco sirve", codigo == 2 and "opaca" in errores)
    t.verdadero("E-36 un primer plano translucido y un fondo translucido, con base, se compone en cadena",
                _ratio("rgba(0,0,0,0.6)", "rgba(255,255,255,0.8)", base="#003366")["ratio"] > 1)


def test_e37_lo_que_no_se_puede_calcular_se_dice(t):
    """E-37 — currentColor, var(), inherit, transparent y un nombre desconocido salen con codigo 2 y sin traceback."""
    # lo dinamico se distingue de lo desconocido: dice que depende de la cascada, no que no lo reconoce
    for color in ("currentColor", "var(--c)", "inherit", "calc(1px + 2px)"):
        codigo, salida, errores = _cli(SCRIPTS / "contrast.py", color, "#fff")
        t.verdadero("E-37 %s sale con 2" % color, codigo == 2)
        t.contiene("E-37 %s dice que es una limitacion" % color, "Limitación", errores)
        t.contiene("E-37 %s dice que depende de la cascada" % color, "cascada", errores)
        t.no_contiene("E-37 %s sin traceback" % color, "Traceback", salida + errores)
    for color in ("papayawhip", "oklch(0.5 0.1 200)", "no-es-un-color"):
        codigo, salida, errores = _cli(SCRIPTS / "contrast.py", color, "#fff")
        t.verdadero("E-37 %s sale con 2" % color, codigo == 2)
        t.contiene("E-37 %s dice que es una limitacion" % color, "Limitación", errores)
        t.verdadero("E-37 %s dice que no lo reconoce o que no lo convierte" % color, "No reconozco" in errores or "no convierte" in errores)
        t.no_contiene("E-37 %s sin traceback" % color, "Traceback", salida + errores)
    codigo, salida, errores = _cli(SCRIPTS / "contrast.py", "#000", "transparent")
    t.verdadero("E-37 transparent como fondo pide base", codigo == 2 and "--backdrop" in errores)
    t.contiene("E-37 y dice que es una limitacion", "Limitación", errores)
    t.no_contiene("E-37 sin traceback", "Traceback", salida + errores)
    codigo, salida, _ = _cli(SCRIPTS / "contrast.py", "currentColor", "#fff", "--json")
    t.verdadero("E-37 en JSON tambien lo dice", codigo == 2 and json.loads(salida)["error"] == "limitation")


def test_e38_umbrales_y_niveles(t):
    """E-38 — grande es 24 px (18 pt) o 14 pt (18,67 px) en negrita; el informe distingue 1.4.3, 1.4.11 y 1.4.6 (AAA)."""
    t.verdadero("E-38 24 px es grande", C.es_grande(24, False))
    t.verdadero("E-38 23,9 px no", not C.es_grande(23.9, False))
    t.verdadero("E-38 14 pt (18,67 px) en negrita es grande", C.es_grande(14 * 4 / 3.0, True))
    t.verdadero("E-38 18,67 px en negrita es grande", C.es_grande(18.67, True))
    t.verdadero("E-38 18,67 px sin negrita no", not C.es_grande(18.67, False))
    t.verdadero("E-38 18,5 px en negrita no: queda por debajo de 14 pt", not C.es_grande(18.5, True))
    t.verdadero("E-38 14 pt son 18,67 px", abs(14 * 4 / 3.0 - 18.6667) < 1e-3)
    r = _ratio("#767676", "#fff", tam=24)
    t.verdadero("E-38 en texto grande 1.4.3 pide 3:1", r["criteria"]["1.4.3"]["this_text"] and r["large_text"])
    r = _ratio("#777", "#fff", tam=16)
    t.verdadero("E-38 en texto normal #777 no cumple", not r["criteria"]["1.4.3"]["this_text"])
    t.igual("E-38 1.4.3 es AA", "AA", r["criteria"]["1.4.3"]["level"])
    t.igual("E-38 1.4.11 es AA", "AA", r["criteria"]["1.4.11"]["level"])
    t.igual("E-38 1.4.6 es AAA", "AAA", r["criteria"]["1.4.6"]["level"])
    t.contiene("E-38 el informe marca 1.4.6 como AAA", "AAA, no forma parte de AA", C.informe(_ratio("#777", "#fff")))
    t.igual("E-38 los niveles salen de los datos", [INDICE["1.4.3"]["level"], INDICE["1.4.11"]["level"], INDICE["1.4.6"]["level"], INDICE["2.4.13"]["level"]],
            [r["criteria"][k]["level"] for k in ("1.4.3", "1.4.11", "1.4.6", "2.4.13")])


def lint_python39(codigo, nombre="x.py"):
    """Los problemas de compatibilidad con Python 3.9 de un fuente: sintaxis de 3.10+, `|` en anotaciones
    evaluadas al definir, zip(strict=) y unas pocas APIs. Es un lint, no un 3.9 de verdad."""
    problemas = []
    try:
        arbol = ast.parse(codigo, feature_version=(3, 9))
    except SyntaxError as e:
        return ["sintaxis de 3.10+ o invalida: %s" % e.msg]
    futuro = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and any(a.name == "annotations" for a in n.names) for n in ast.walk(arbol))

    def tiene_union(nodo):
        return nodo is not None and any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.BitOr) for x in ast.walk(nodo))

    for n in ast.walk(arbol):
        anotaciones = []
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            todos = n.args.args + n.args.kwonlyargs + n.args.posonlyargs + [a for a in (n.args.vararg, n.args.kwarg) if a]
            anotaciones = [a.annotation for a in todos] + [n.returns]
        elif isinstance(n, ast.AnnAssign):
            anotaciones = [n.annotation]
        for a in anotaciones:
            if tiene_union(a) and not futuro:
                problemas.append("%s:%d anotacion con | sin `from __future__ import annotations`" % (nombre, a.lineno))
        if isinstance(n, ast.Call):
            if any(k.arg == "strict" for k in n.keywords) and isinstance(n.func, ast.Name) and n.func.id == "zip":
                problemas.append("%s:%d zip(strict=) es de 3.10" % (nombre, n.lineno))
            # Path.write_text(newline=) es de 3.10: lo atrapo un Python 3.9 de verdad, no el lint de antes
            if isinstance(n.func, ast.Attribute) and n.func.attr == "write_text" and any(k.arg == "newline" for k in n.keywords):
                problemas.append("%s:%d write_text(newline=) es de 3.10" % (nombre, n.lineno))
            if isinstance(n.func, ast.Attribute) and n.func.attr == "pairwise":
                problemas.append("%s:%d itertools.pairwise es de 3.10" % (nombre, n.lineno))
            if isinstance(n.func, ast.Name) and n.func.id == "isinstance" and len(n.args) == 2 and tiene_union(n.args[1]):
                problemas.append("%s:%d isinstance con | es de 3.10" % (nombre, n.lineno))
            if isinstance(n.func, ast.Attribute) and n.func.attr in ("insort", "bisect_left", "bisect_right", "bisect") and any(k.arg == "key" for k in n.keywords):
                problemas.append("%s:%d bisect(key=) es de 3.10" % (nombre, n.lineno))
        if isinstance(n, ast.Attribute) and n.attr in ("bit_count",):
            problemas.append("%s:%d %s es de 3.10" % (nombre, n.lineno, n.attr))
        if isinstance(n, ast.ImportFrom) and n.module == "tomllib":
            problemas.append("%s:%d tomllib es de 3.11" % (nombre, n.lineno))
        if isinstance(n, ast.Import) and any(a.name == "tomllib" for a in n.names):
            problemas.append("%s:%d tomllib es de 3.11" % (nombre, n.lineno))
        if isinstance(n, ast.ImportFrom) and n.module == "typing" and any(a.name in ("ParamSpec", "TypeAlias", "Self") for a in n.names):
            problemas.append("%s:%d typing trae algo de 3.10+" % (nombre, n.lineno))
    return problemas


def test_e39_compatible_con_python_3_9(t):
    """E-39 — los scripts de la skill y el motor son validos en 3.9: lint sintactico siempre; 3.9 real si hay HARNESS_PYTHON39."""
    fuentes = sorted(SCRIPTS.glob("*.py")) + [LIB / "a11y.py", CHECK]
    for ruta in fuentes:
        t.vacio("E-39 %s: sin problemas de 3.9" % ruta.name, lint_python39(_leer(ruta), ruta.name))
    # el lint no es decorativo: ve lo que el script original de contraste hacia
    t.verdadero("E-39 el lint ve `float | None` sin el import del futuro", len(lint_python39("def f(x: float | None) -> bool | None:\n    return x\n")) == 2)
    t.vacio("E-39 y lo acepta con el import del futuro", lint_python39("from __future__ import annotations\ndef f(x: float | None) -> bool | None:\n    return x\n"))
    t.verdadero("E-39 el lint ve un match", len(lint_python39("match 1:\n    case 1:\n        pass\n")) == 1)
    t.verdadero("E-39 el lint ve zip(strict=)", len(lint_python39("list(zip([1], [2], strict=True))\n")) == 1)
    t.verdadero("E-39 el lint ve write_text(newline=), que un 3.9 real rechazo en este cambio",
                len(lint_python39("from pathlib import Path\nPath('x').write_text('a', encoding='utf-8', newline='\\n')\n")) == 1)
    t.verdadero("E-39 el lint ve isinstance con |", len(lint_python39("isinstance(1, int | str)\n")) == 1)
    py39 = os.environ.get("HARNESS_PYTHON39")
    if py39:
        for script, args in (("wcag.py", ["count"]), ("contrast.py", ["#777", "#fff"]), ("review.py", ["--help"])):
            p = subprocess.run([py39, "-B", str(SCRIPTS / script)] + args, capture_output=True, timeout=120)
            t.igual("E-39 %s corre en el Python 3.9 de HARNESS_PYTHON39" % script, 0, p.returncode)
    else:
        # No hay donde ejecutar: se dice en el nombre de la aserción, que es lo que sale en --detallado,
        # y no se da por pasado en silencio. La aserción es verdadera por construcción: su trabajo es decir.
        t.verdadero("E-39 SIN HARNESS_PYTHON39: la compatibilidad se verificó por lint, NO con un Python 3.9 real", True)


# -- el check liviano y la revision completa -------------------------------------------------------------------

def _revisar(contenido, nombre="p.html", modo="liviano"):
    return A.revisar(contenido, nombre, modo)


def _reglas(contenido, nombre="p.html", modo="liviano"):
    return sorted({h["rule"] for h in _revisar(contenido, nombre, modo).hallazgos})


DOC = '<html lang="es">\n<head><title>Pagina</title></head>\n<body>\n<h1>Uno</h1>\n%s\n</body>\n</html>\n'


def test_e40_un_id_solo_no_es_un_nombre(t):
    """E-40 — `<input id="x">` sin `<label for="x">` en un documento completo es un control sin nombre accesible."""
    t.igual("E-40 id sin etiqueta", ["control-no-accessible-name"], _reglas(DOC % '<input id="x" type="text">'))
    t.igual("E-40 id con su label for: silencio", [], _reglas(DOC % '<label for="x">Nombre</label><input id="x" type="text">'))
    t.igual("E-40 la label apunta a otro id", ["control-no-accessible-name", "label-for-broken"],
            _reglas(DOC % '<label for="y">Nombre</label><input id="x" type="text">'))
    t.igual("E-40 label for sin texto", ["control-no-accessible-name"], _reglas(DOC % '<label for="x"></label><input id="x" type="text">'))
    t.igual("E-40 select y textarea tambien", ["control-no-accessible-name"], _reglas(DOC % '<select id="s"><option>a</option></select><textarea id="a"></textarea>'))
    mensaje = A.mensajes(_revisar(DOC % '<input id="x" type="text">'))[0]
    t.contiene("E-40 el aviso dice que un id no es un nombre", "Un id no es un nombre", mensaje)
    t.contiene("E-40 y cita el criterio y su nivel", "criterio 4.1.2, nivel A", mensaje)


def test_e41_el_control_envuelto_en_una_label(t):
    """E-41 — una `<label>` envolvente con texto da nombre sin id; sin texto, no."""
    t.igual("E-41 envuelto, sin id", [], _reglas(DOC % '<label>Nombre <input type="text"></label>'))
    t.igual("E-41 envuelto y con id", [], _reglas(DOC % '<label>Nombre <input id="n" type="text"></label>'))
    t.igual("E-41 envolvente sin texto", ["control-no-accessible-name"], _reglas(DOC % '<label><input type="text"></label>'))
    t.igual("E-41 el texto de la envolvente es una expresion de plantilla", [], _reglas('<label>{{ $nombre }} <input type="text"></label>', "c.blade.php"))
    t.igual("E-41 la etiqueta envolvente en JSX", [], _reglas('export const C = () => <label>Nombre <input type="text" /></label>;', "C.tsx"))


def test_e42_aria_label(t):
    """E-42 — `aria-label="Buscar"` nombra; `aria-label="  "` no."""
    t.igual("E-42 aria-label con texto", [], _reglas(DOC % '<input type="search" aria-label="Buscar">'))
    t.igual("E-42 aria-label en blanco", ["control-no-accessible-name"], _reglas(DOC % '<input type="search" aria-label="  ">'))
    t.igual("E-42 aria-label vacio", ["control-no-accessible-name"], _reglas(DOC % '<input type="search" aria-label="">'))


def test_e43_referencias_aria(t):
    """E-43 — aria-labelledby a un elemento con texto nombra; a un id inexistente o a uno sin texto, se reporta."""
    t.igual("E-43 apunta a un elemento con texto", [], _reglas(DOC % '<span id="t">Nombre</span><input type="text" aria-labelledby="t">'))
    roto = _revisar(DOC % '<input type="text" aria-labelledby="no-existe">')
    t.igual("E-43 apunta a un id que no existe", ["control-no-accessible-name"], sorted({h["rule"] for h in roto.hallazgos}))
    t.contiene("E-43 el aviso nombra el id", "#no-existe", " ".join(A.mensajes(roto)))
    vacio = _revisar(DOC % '<span id="t"></span><input type="text" aria-labelledby="t">')
    t.igual("E-43 apunta a un elemento sin texto", ["control-no-accessible-name"], sorted({h["rule"] for h in vacio.hallazgos}))
    t.contiene("E-43 y dice que no tiene texto", "que no tiene texto", " ".join(A.mensajes(vacio)))
    t.igual("E-43 con varios ids, basta uno con texto", [], _reglas(DOC % '<span id="a">Calle</span><input type="text" aria-labelledby="x a">'))
    t.igual("E-43 un describedby roto es un defecto",
            ["aria-reference-broken"], _reglas(DOC % '<label for="n">N</label><input id="n" type="text" aria-describedby="ayuda">'))
    t.igual("E-43 un describedby sin texto tambien",
            ["aria-reference-no-text"], _reglas(DOC % '<label for="n">N</label><input id="n" type="text" aria-describedby="ayuda"><p id="ayuda"></p>'))
    t.igual("E-43 un labelledby roto con otro nombre es un defecto, no un fallo",
            ["aria-reference-broken"], _reglas(DOC % '<label for="n">N</label><input id="n" type="text" aria-labelledby="no-existe">'))
    t.igual("E-43 un aria-labelledby dinamico no se juzga", [], _reglas('<input type="text" aria-labelledby="{{ $id }}">', "c.blade.php"))


def test_e44_fragmentos(t):
    """E-44 — en un fragmento, id sin label es un defecto con caveat; con componente, expresion o includes, se calla."""
    frag = _revisar('<input id="n" type="text">', "campo.component.html")
    t.igual("E-44 un fragmento con id y sin label: defecto", ["control-label-missing-in-file"], sorted({h["rule"] for h in frag.hallazgos}))
    t.igual("E-44 no es un fallo", {"defect"}, {h["kind"] for h in frag.hallazgos})
    t.contiene("E-44 el aviso dice que la etiqueta puede estar en otro archivo", "otro archivo", " ".join(A.mensajes(frag)))
    t.igual("E-44 sin id, sin aria y sin envolvente: fallo", ["control-no-accessible-name"], _reglas('<input type="text">', "campo.component.html"))
    t.igual("E-44 dentro de un componente propio se calla", [], _reglas('<app-campo><input id="n" type="text"></app-campo>', "campo.component.html"))
    t.igual("E-44 con un id que es una expresion se calla", [], _reglas('export const C = ({ id }: any) => <input id={id} />;', "C.tsx"))
    t.igual("E-44 con una label for dinamica se calla", [], _reglas('<label for="{{ $x }}">N</label><input id="n" type="text">', "c.blade.php"))
    t.igual("E-44 con includes se calla", [], _reglas("@include('x')<input id=\"n\" type=\"text\">", "c.blade.php"))
    completa = _revisar('<app-campo><input id="n" type="text"></app-campo>', "campo.component.html", "completo")
    t.igual("E-44 la revision completa lo lista como no determinable", ["control-name-undeterminable"], sorted({h["rule"] for h in completa.hallazgos}))
    t.igual("E-44 de tipo undeterminable", {"undeterminable"}, {h["kind"] for h in completa.hallazgos if h["rule"] == "control-name-undeterminable"})
    t.igual("E-44 un documento que incluye otros no es un mundo cerrado", False, _revisar("@include('x')" + DOC % "", "c.blade.php").cerrado)


def test_e45_un_h1_no_es_un_fallo(t):
    """E-45 — cero o dos <h1> no producen avisos del check liviano; la revision completa los informa como recomendacion."""
    dos = DOC % '<h1>Dos</h1>'
    ninguno = '<html lang="es"><head><title>x</title></head><body><p>x</p></body></html>'
    t.igual("E-45 dos h1 en el liviano: silencio", [], _reglas(dos))
    t.igual("E-45 ningun h1 en el liviano: silencio", [], _reglas(ninguno))
    completa = _revisar(dos, "p.html", "completo")
    h = [x for x in completa.hallazgos if x["rule"] == "heading-multiple-h1"]
    t.igual("E-45 la revision completa lo informa", 1, len(h))
    t.igual("E-45 como recomendacion", "recommendation", h[0]["kind"])
    t.igual("E-45 sin criterio", [], h[0]["sc"])
    t.verdadero("E-45 sin nivel", h[0]["level"] is None)
    t.igual("E-45 de origen harness", "harness", h[0]["origin"])
    mensaje = [m for m in A.mensajes(completa) if "<h1>" in m][0]
    t.contiene("E-45 el aviso dice que WCAG no lo exige", "WCAG 2.2 no lo exige", mensaje)
    t.contiene("E-45 la falta de h1 tambien es una recomendacion", "heading-no-h1", " ".join(x["rule"] for x in _revisar(ninguno, "p.html", "completo").hallazgos))
    t.verdadero("E-45 ninguna regla WCAG de la tabla lleva `h1`", not any("h1" in r for r, v in A.REGLAS.items() if v[0]))


def _corpus():
    return json.loads(CORPUS.read_text("utf-8"))


def test_e46_el_liviano_solo_dice_fallos_y_defectos(t):
    """E-46 — el check liviano emite solo fail y defect, cada aviso con su criterio y su nivel."""
    tipos = set()
    for caso in _corpus()["cases"]:
        res = _revisar(caso["content"], caso["file"])
        tipos |= {h["kind"] for h in res.hallazgos}
        for m in A.mensajes(res):
            t.verdadero("E-46 %s: el aviso cita criterio y nivel" % caso["id"], re.search(r"criterios? [\d.]+( y [\d.]+)?, nivel [A-Z/]+", m) is not None)
    t.verdadero("E-46 solo fail y defect (%s)" % sorted(tipos), tipos <= {"fail", "defect"})
    # y la revision completa si dice mas
    completa = set()
    for caso in _corpus()["cases"]:
        completa |= {h["kind"] for h in _revisar(caso["content"], caso["file"], "completo").hallazgos}
    t.verdadero("E-46 la completa trae tambien probable, no determinable y recomendacion", {"probable", "undeterminable", "recommendation"} <= completa)
    for regla, (sc, tipo, origen, liviana, tecnica) in A.REGLAS.items():
        t.verdadero("E-46 la regla %s liviana es fail o defect" % regla, (not liviana) or tipo in ("fail", "defect"))


def _check(nombre, contenido):
    """Corre el check .py como lo hace el hook: por ruta, con el evento minimo."""
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, bytes):
            ruta.write_bytes(contenido)
        else:
            ruta.write_text(contenido, encoding="utf-8")
        evento = {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(ruta)}}
        modulo = reglas._cargar(str(CHECK))
        return [s for s in (modulo.verificar(evento, d, None) or []) if s]


def test_e47_lo_que_no_le_toca_y_lo_que_no_se_puede_leer(t):
    """E-47 — ignora .ts, .js, .css, .py, rutas generadas y archivos de mas de 512 KB; lo ilegible da silencio."""
    malo = DOC % '<img src="a.png"><input type="text">'
    t.verdadero("E-47 el HTML malo si se reporta (el check corrio)", len(_check("p.html", malo)) >= 2)
    for nombre in ("algo.ts", "algo.js", "estilo.css", "algo.py", "algo.vue", "README.md"):
        t.vacio("E-47 %s no le toca" % nombre, _check(nombre, malo))
    for ruta in ("node_modules/x/p.html", "dist/p.html", "vendor/p.html"):
        t.vacio("E-47 %s esta en una ruta generada" % ruta, _check(ruta, malo))
    grande = ("<html lang=\"es\"><body>" + "<img src=\"a.png\">" * 40000 + "</body></html>")
    t.verdadero("E-47 el archivo grande pasa los 512 KB (%d)" % len(grande), len(grande) > 512 * 1024)
    t.vacio("E-47 uno de mas de 512 KB se descarta", _check("p.html", grande))
    for roto in ("<<<<>>>> <input", "<html <body <img", "\x00\x01\x02", "<input aria-labelledby=", "export const C = () => <input {", "<div " * 3000):
        try:
            salida = _check("p.html", roto)
            salio = True
        except Exception as e:     # noqa: BLE001
            salio = False
            salida = [repr(e)]
        t.verdadero("E-47 un archivo roto no tira una excepcion: %r" % roto[:20], salio)
    for roto in ("export const C = () => <input {", "const x = <<<<>>>> <a", "<div>{" * 200, "<>".join(["<"] * 50)):
        try:
            _check("C.tsx", roto)
            salio = True
        except Exception:      # noqa: BLE001
            salio = False
        t.verdadero("E-47 un JSX roto no tira una excepcion: %r" % roto[:20], salio)
    t.vacio("E-47 un archivo binario con extension html da silencio", _check("p.html", b"\xff\xfe\x00\x00\x80\x81"))


def test_e48_plantillas(t):
    """E-48 — {{ }}, {% %}, Blade, <?php ?> y Angular no dan falsos positivos; un <img [src]> sin alt si se reporta."""
    t.igual("E-48 label con expresion", [], _reglas('<label for="{{ $id }}">{{ $label }}</label><input id="{{ $id }}" type="text">', "c.blade.php"))
    t.igual("E-48 aria-label con expresion", [], _reglas("<input type=\"text\" aria-label=\"{{ __('buscar') }}\">", "c.blade.php"))
    t.igual("E-48 una directiva de Blade dentro del tag", [], _reglas('<input type="text" @if($x) disabled @endif aria-label="Nombre">', "c.blade.php"))
    t.igual("E-48 <?php ?> dentro de un atributo", [], _reglas('<input type="text" aria-label="<?php echo $x; ?>">', "c.blade.php"))
    t.igual("E-48 {% %} de Twig/Jinja", [], _reglas('<input type="text" aria-label="{% trans %}Nombre{% endtrans %}">', "c.twig"))
    t.igual("E-48 el titulo es una expresion", [], _reglas('<html lang="{{ app()->getLocale() }}"><head><title>{{ $t }}</title></head><body></body></html>', "l.blade.php"))
    t.igual("E-48 un titulo hecho con un bloque", [], _reglas('<html lang="es"><head><title>{% block title %}{% endblock %}</title></head><body></body></html>', "l.njk"))
    t.igual("E-48 un documento que incluye su cabecera no se acusa de no tener titulo", [],
            _reglas("<html lang=\"es\"><head>@include('p.head')</head><body></body></html>", "l.blade.php"))
    t.igual("E-48 binding de Angular", [], _reglas('<input type="text" [attr.aria-label]="etiqueta">', "c.component.html"))
    t.igual("E-48 *ngIf y (input)", [], _reglas('<div *ngIf="ok"><label>Nombre <input type="text" (input)="x($event)"></label></div>', "c.component.html"))
    t.igual("E-48 un <img [src]> sin alt si se reporta", ["img-missing-alt"], _reglas('<img [src]="u">', "f.component.html"))
    t.igual("E-48 con [alt] no", [], _reglas('<img [src]="u" [alt]="t">', "f.component.html"))
    t.igual("E-48 {{ }} con un < adentro no rompe el arbol", ["img-missing-alt"], _reglas('<p>{{ a < b ? 1 : 2 }}</p><img src="a.png">', "c.blade.php"))
    t.igual("E-48 un {{ sin cerrar no cuelga ni rompe", [], _reglas("<p>{{ sin cerrar</p>", "c.blade.php"))
    t.igual("E-48 los saltos de linea se conservan para el numero de linea", ["L3"],
            ["L%d" % h["line"] for h in _revisar("{{ a\nb }}\n<img src=\"a.png\">", "c.blade.php").hallazgos])


def test_e49_jsx_y_tsx(t):
    """E-49 — tokenizador propio: htmlFor, autocerradas, expresiones, > dentro de { }, genericos y comparaciones."""
    t.igual("E-49 htmlFor", [], _reglas('export const C = () => <><label htmlFor="n">Nombre</label><input id="n" type="text" /></>;', "C.tsx"))
    t.igual("E-49 etiqueta autocerrada sin nombre", ["control-no-accessible-name"], _reglas("export const C = () => <input type=\"text\" />;", "C.tsx"))
    t.igual("E-49 un atributo con expresion vale presente", [], _reglas("export const C = () => <input type=\"text\" aria-label={t(\"x\")} />;", "C.tsx"))
    t.igual("E-49 img con expresion en src y sin alt", ["img-missing-alt"], _reglas("export const F = ({ u }: any) => <img src={u} />;", "F.tsx"))
    t.igual("E-49 img con alt vacio", [], _reglas('export const F = ({ u }: any) => <img src={u} alt="" />;', "F.tsx"))
    t.igual("E-49 > dentro de una expresion no cierra la etiqueta", ["control-no-accessible-name"],
            _reglas('export const C = ({ a, b }: any) => <div title={a > b ? "x" : "y"}><input type="text" /></div>;', "C.tsx"))
    t.igual("E-49 > dentro de una cadena", ["control-no-accessible-name"],
            _reglas('export const C = () => <div title="a > b"><input type="text" /></div>;', "C.tsx"))
    t.igual("E-49 genericos y comparaciones", ["control-no-accessible-name"],
            _reglas('const f = <T,>(x: T) => x;\nconst g = (a: number, b: number) => (a < b ? 1 : 2);\nconst h: Array<string> = [];\nconst k = <T extends object>(x: T) => x;\nexport const C = () => <input type="text" />;', "u.tsx"))
    t.igual("E-49 un JSX dentro de un map", ["img-missing-alt"],
            _reglas('export const L = ({ items }: any) => <ul>{items.map((i: string) => <li key={i}><img src={i} /></li>)}</ul>;', "L.tsx"))
    t.igual("E-49 un JSX dentro de un operador logico", ["img-missing-alt"],
            _reglas('export const L = ({ ok }: any) => <div>{ok && <img src="a.png" />}</div>;', "L.tsx"))
    t.igual("E-49 un template literal con una etiqueta adentro no es JSX", [],
            _reglas('export const c = `<input type="text">`;\nexport const d = "<img src=a>";\n', "u.tsx"))
    # el contexto de estos dos permite un JSX («= <img />»): solo saltar la cadena y la plantilla los deja afuera
    t.igual("E-49 una etiqueta dentro de un template literal, donde un JSX seria valido, no se lee", [],
            _reglas('export const c = `ver = <img src="a.png" />`;\n', "u.tsx"))
    t.igual("E-49 ni dentro de una cadena", [], _reglas("export const c = 'ver = <img src=\"a.png\" />';\n", "u.tsx"))
    t.igual("E-49 un ${ } con una llave y una cadena adentro no desordena lo que sigue", ["img-missing-alt"],
            _reglas('export const c = `x ${f({ a: "}" })} y`;\nexport const D = () => <img src="a.png" />;\n', "u.tsx"))
    t.igual("E-49 una expresion regular con < no es JSX", [], _reglas("export const r = /<input>/g.test(x);\n", "u.tsx"))
    t.igual("E-49 un comentario con una etiqueta adentro no es JSX", [], _reglas("// <img src=a>\n/* <input> */\nexport const x = 1;\n", "u.tsx"))
    t.igual("E-49 fragmento <></>", [], _reglas("export const C = () => <><p>hola</p></>;", "C.tsx"))
    t.igual("E-49 jsx con atributo booleano y mayuscula", ["control-no-accessible-name"], _reglas("export const C = () => <input type=\"text\" required readOnly />;", "C.tsx"))
    t.igual("E-49 etiqueta html con onClick en un div: probable", ["clickable-not-keyboard"],
            _reglas("export const C = () => <div onClick={go}>x</div>;", "C.tsx", "completo"))
    profundo = "export const C = () => " + "<div>" * 40 + "<img src=\"a.png\" />" + "</div>" * 40 + ";"
    t.igual("E-49 anidado a 40 niveles", ["img-missing-alt"], _reglas(profundo, "C.tsx"))
    t.verdadero("E-49 anidado a 200 niveles no tira excepcion", isinstance(_revisar("export const C = () => " + "<div>" * 200 + "x" + "</div>" * 200 + ";", "C.tsx").hallazgos, list))


def test_e50_componentes_y_spread_no_se_juzgan(t):
    """E-50 — un componente capitalizado y un {...props} no se juzgan; la revision completa los cuenta como no analizados."""
    comp = _revisar('export const C = () => <TextField label="Nombre" />;', "C.tsx", "completo")
    t.vacio("E-50 un componente propio: sin hallazgos", comp.hallazgos)
    t.contiene("E-50 se cuenta como no analizado, con su nombre", "<TextField>", " ".join(x["reason"] for x in comp.no_analizado))
    t.igual("E-50 y con su linea", 1, comp.no_analizado[0]["line"])
    sp = _revisar("export const C = (p: any) => <input {...p} />;", "C.tsx", "completo")
    t.vacio("E-50 un {...props}: ningun fallo ni defecto", [h for h in sp.hallazgos if h["kind"] in ("fail", "defect")])
    t.igual("E-50 se lista como no determinable", ["control-name-undeterminable"], sorted({h["rule"] for h in sp.hallazgos}))
    t.contiene("E-50 se cuenta como no analizado", "{...props}", " ".join(x["reason"] for x in sp.no_analizado))
    t.vacio("E-50 el check liviano calla ante ambos", _reglas('export const C = (p: any) => <><TextField /><input {...p} /></>;', "C.tsx"))
    t.igual("E-50 un boton con un componente adentro no se acusa", [],
            _reglas("export const B = () => <button><Icon name=\"x\" /></button>;", "B.tsx"))
    t.igual("E-50 un elemento personalizado de HTML tambien es un componente", [],
            _reglas('<x-campo><input type="text"></x-campo>', "c.blade.php"))
    t.igual("E-50 pero el control de al lado, sin nombre, si", ["control-no-accessible-name"],
            _reglas('<x-campo></x-campo><input type="text">', "c.blade.php"))


def test_e51_cobertura(t):
    """E-51 — `review.py` informa archivos analizados, no analizados con su motivo y formatos; lo fuera de alcance se lista."""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "a.html").write_text(DOC % "<p>x</p>", encoding="utf-8")
        (base / "C.tsx").write_text("export const C = () => <><TextField /></>;", encoding="utf-8")
        (base / "campo.blade.php").write_text("<input aria-label=\"x\">", encoding="utf-8")
        (base / "Otro.vue").write_text("<template><input></template>", encoding="utf-8")
        (base / "node_modules").mkdir()
        (base / "node_modules" / "z.html").write_text("<img>", encoding="utf-8")
        codigo, salida, _ = _cli(SCRIPTS / "review.py", base, (base / "Otro.vue"), "--json")
        t.igual("E-51 sale con 0", 0, codigo)
        r = json.loads(salida)
        cob = r["coverage"]
        t.igual("E-51 analiza 3 archivos (no el de node_modules)", 3, cob["analyzed"])
        t.igual("E-51 formatos", {"html": 1, "template": 1, "jsx": 1}, cob["by_format"])
        t.igual("E-51 un archivo con partes no analizadas", 1, len(cob["partial"]))
        t.igual("E-51 la extension fuera de alcance se lista", 1, len(cob["out_of_scope"]))
        t.verdadero("E-51 es el .vue", cob["out_of_scope"][0].endswith("Otro.vue"))
        t.contiene("E-51 dice por que", "extensión fuera de alcance", json.dumps(r, ensure_ascii=False))
        t.contiene("E-51 la nota", "no acredita conformidad", r["note"])
        codigo, texto, _ = _cli(SCRIPTS / "review.py", base)
        t.contiene("E-51 en texto: la cobertura", "Cobertura: 3 archivo(s) analizados (HTML 1 · plantillas 1 · JSX/TSX 1)", texto)
        t.contiene("E-51 en texto: lo no analizado", "no analizado —", texto)
        t.contiene("E-51 en texto: lo que no se probo", "navegador, teclado ni lector de pantalla", texto)
        codigo, _, errores = _cli(SCRIPTS / "review.py", base / "no-hay-nada")
        t.verdadero("E-51 una ruta sin archivos sale con 2", codigo == 2 and "No hay archivos" in errores)


def test_e52_el_costo_no_es_cuadratico(t):
    """E-52 — un documento de 5.000 controles (~400 KB) se analiza en menos de 5 s."""
    filas = "".join('<div><label for="c%d">Campo %d</label><input id="c%d" type="text"></div>\n' % (i, i, i) for i in range(5000))
    doc = DOC % filas
    t.verdadero("E-52 pesa unos 400 KB (%d)" % len(doc), len(doc) > 300 * 1024)
    t0 = time.perf_counter()
    res = _revisar(doc)
    dt = time.perf_counter() - t0
    t.verdadero("E-52 %.2f s (< 5 s)" % dt, dt < 5.0)
    t.vacio("E-52 y no inventa hallazgos", res.hallazgos)
    anidado = DOC % ("<li>" * 4000 + '<input type="text">')
    t0 = time.perf_counter()
    res = _revisar(anidado)
    dt = time.perf_counter() - t0
    t.verdadero("E-52 cuatro mil <li> sin cerrar: %.2f s (< 5 s)" % dt, dt < 5.0)
    t.igual("E-52 y lo encuentra", ["control-no-accessible-name"], sorted({h["rule"] for h in res.hallazgos}))
    jsx = "export const L = () => <ul>" + "".join('<li key="%d"><img src="a.png" alt="x" /></li>' % i for i in range(3000)) + "</ul>;"
    t0 = time.perf_counter()
    _revisar(jsx, "L.tsx")
    dt = time.perf_counter() - t0
    t.verdadero("E-52 un JSX de 3.000 elementos: %.2f s (< 5 s)" % dt, dt < 5.0)

    # El costo crece lineal, no cuadratico: con cuatro veces los controles, el tiempo no se multiplica por mas
    # de ocho (lineal da cerca de cuatro, cuadratico cerca de dieciseis). Un cociente no depende de la maquina.
    def mejor(texto, nombre="p.html", veces=3):
        marcas = []
        for _ in range(veces):
            t0 = time.perf_counter()
            _revisar(texto, nombre)
            marcas.append(time.perf_counter() - t0)
        return min(marcas)

    def filas_(n):
        return "".join('<div><label for="c%d">Campo %d</label><input id="c%d" type="text"></div>\n' % (i, i, i) for i in range(n))

    chico, grande = mejor(DOC % filas_(2500)), mejor(DOC % filas_(10000))
    t.verdadero("E-52 diez mil controles contra dos mil quinientos: %.2f s contra %.2f s, cociente %.1f (< 8)" % (grande, chico, grande / max(chico, 1e-6)),
                grande / max(chico, 1e-6) < 8.0)
    t.verdadero("E-52 y diez mil controles caben en %.2f s (< 5 s)" % grande, grande < 5.0)


def test_e53_el_corpus_etiquetado(t):
    """E-53 — sobre el corpus, el check liviano no tiene falsos positivos ni negativos; cada problema tiene un caso de cada signo."""
    corpus = _corpus()
    t.verdadero("E-53 el corpus tiene casos (%d)" % len(corpus["cases"]), len(corpus["cases"]) >= 60)
    ids = [c["id"] for c in corpus["cases"]]
    t.igual("E-53 ids unicos", len(ids), len(set(ids)))
    tp = fp = fn = 0
    for c in corpus["cases"]:
        obtenidas = set(_reglas(c["content"], c["file"]))
        esperadas = set(c["light"])
        tp += len(obtenidas & esperadas)
        fp += len(obtenidas - esperadas)
        fn += len(esperadas - obtenidas)
        t.igual("E-53 %s" % c["id"], sorted(esperadas), sorted(obtenidas))
    t.igual("E-53 falsos positivos", 0, fp)
    t.igual("E-53 falsos negativos", 0, fn)
    t.verdadero("E-53 hay positivos verdaderos (%d)" % tp, tp >= 25)
    for c in corpus["cases"]:
        # lo que solo la revision completa dice (probables, recomendaciones) tambien se etiqueta
        completas = set(_reglas(c["content"], c["file"], "completo"))
        t.vacio("E-53 %s: la revision completa dice lo que se espera de ella" % c["id"], sorted(set(c.get("full", [])) - completas))
    for problema in corpus["problems"]:
        casos = [c for c in corpus["cases"] if problema in c["covers"]]
        t.verdadero("E-53 «%s» tiene un caso positivo" % problema, any(c["light"] or c.get("full") for c in casos))
        t.verdadero("E-53 «%s» tiene un caso negativo" % problema, any(not c["light"] for c in casos))
    # el corpus ejercita las tres familias de formato
    t.verdadero("E-53 cubre HTML, plantillas y JSX", {"html", "template", "jsx"} <= {A.formato_de(c["file"]) for c in corpus["cases"]})


def test_e54_las_reglas_coinciden_con_los_datos_y_con_el_w3c(t):
    """E-54 — NIVELES coincide con el JSON; toda tecnica citada existe en el testigo y se asocia al criterio; static-coverage.md lista las reglas."""
    for sc, nivel in A.NIVELES.items():
        t.igual("E-54 el nivel de %s" % sc, INDICE[sc]["level"], nivel)
    for regla, (criterios, tipo, origen, liviana, tecnica) in A.REGLAS.items():
        for sc in criterios:
            t.verdadero("E-54 %s cita %s, que esta en NIVELES" % (regla, sc), sc in A.NIVELES)
        t.verdadero("E-54 %s: tipo valido" % regla, tipo in A.ORDEN_TIPO)
        t.verdadero("E-54 %s: origen valido" % regla, origen in ("wcag", "obelisco", "harness"))
        t.verdadero("E-54 %s: una recomendacion no cita criterio" % regla, tipo != "recommendation" or not criterios)
        t.verdadero("E-54 %s: tiene correccion" % regla, regla in A.CORRECCION)
        if tecnica:
            t.verdadero("E-54 %s: la tecnica %s existe en el W3C" % (regla, tecnica), tecnica in OBS["techniques"])
            if tecnica in OBS["techniques"]:
                t.verdadero("E-54 %s: %s esta asociada a alguno de %s" % (regla, tecnica, list(criterios)),
                            bool(set(criterios) & set(OBS["techniques"][tecnica]["scs"])))
    t.verdadero("E-54 F47 no es una tecnica de WCAG 2.2 y no se cita", "F47" not in OBS["techniques"] and all(v[4] != "F47" for v in A.REGLAS.values()))
    tabla = {}
    for linea in _leer(REFS / "static-coverage.md").splitlines():
        m = re.match(r"^\| `([\w-]+)` \| (.+?) \| (\w+) \| (\w+) \| (yes|no) \|$", linea)
        if m:
            tabla[m.group(1)] = (m.group(2), m.group(3), m.group(4), m.group(5) == "yes")
    t.igual("E-54 static-coverage.md lista exactamente las reglas del motor", sorted(A.REGLAS), sorted(tabla))
    for regla, (criterios, tipo, origen, liviana, _t) in A.REGLAS.items():
        if regla not in tabla:
            continue
        esperado_sc = ", ".join("%s (%s)" % (c, A.NIVELES[c]) for c in criterios) or "none (Harness recommendation)"
        t.igual("E-54 %s en static-coverage.md" % regla, (esperado_sc, tipo, origen, liviana), tabla[regla])


def test_e55_el_borrador_del_registro(t):
    """E-55 — `review.py --register` produce un borrador valido: fallos estaticos como fail con archivo y linea, el resto not_tested, ningun pass."""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "pagina.html").write_text("<html>\n<body>\n<img src=\"a.png\">\n<input type=\"text\">\n</body>\n</html>\n", encoding="utf-8")
        (base / "C.tsx").write_text("export const C = (p: any) => <><input {...p} /><TextField /></>;\n", encoding="utf-8")
        salida = base / "evidencia.json"
        codigo, texto, _ = _cli(SCRIPTS / "review.py", base, "--register", salida, "--components", "form-text,button")
        t.igual("E-55 sale con 0", 0, codigo)
        doc = json.loads(salida.read_text("utf-8"))
        t.vacio("E-55 el borrador pasa la validacion", W.validar_registro(doc, DATOS))
        codigo, texto, _ = _wcag("register", "validate", salida)
        t.igual("E-55 y el CLI lo da por valido", 0, codigo)
    fallidos = {f["sc"]: f for f in doc["criteria"] if f["result"] == "fail"}
    t.igual("E-55 los fallos estaticos", {"1.1.1", "2.4.2", "3.1.1", "4.1.2"}, set(fallidos))
    for sc, f in fallidos.items():
        t.verdadero("E-55 %s lleva archivo y linea" % sc, re.search(r"\.html:\d+$", f["location"]) is not None)
        t.verdadero("E-55 %s lleva la correccion y la evidencia estatica" % sc, f["fix"] and f["evidence_types"] == ["static"])
    t.vacio("E-55 ningun criterio sale pass", [f["sc"] for f in doc["criteria"] if f["result"] == "pass"])
    sin_hallazgos = [f for f in doc["criteria"] if f["result"] == "not_tested"]
    t.verdadero("E-55 lo demas sale not_tested con el motivo", all(f["reason"] for f in sin_hallazgos) and len(sin_hallazgos) > 40)
    t.contiene("E-55 la nota dice «estatica sin hallazgos»", "Estática sin hallazgos", " ".join(f["reason"] for f in sin_hallazgos))
    t.contiene("E-55 y que lo estatico limpio no acredita", "no acredita", " ".join(f["reason"] for f in sin_hallazgos))
    t.igual("E-55 las tres pruebas siguen sin hacerse", {"browser": "not_performed", "keyboard": "not_performed", "screen_reader": "not_performed"}, doc["tests"])
    t.igual("E-55 el analisis estatico dice cuantos archivos", 2, doc["static_analysis"]["files_analyzed"])
    t.verdadero("E-55 y lo que no pudo analizar", len(doc["static_analysis"]["not_analyzed"]) >= 2)
    t.igual("E-55 con los componentes que se dieron", ["form-text", "button"], doc["scope"]["components"])


def test_e56_encuentra_el_motor_donde_este(t):
    """E-56 — `review.py` encuentra el motor en la fabrica y en un arbol instalado, y si no esta lo dice y sale con 2."""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "p.html").write_text(DOC % "<p>x</p>", encoding="utf-8")
        codigo, _, _ = _cli(SCRIPTS / "review.py", base / "p.html")
        t.igual("E-56 en la fabrica lo encuentra", 0, codigo)
        # un arbol instalado: .claude/skills/dev-accessibility/scripts y .claude/harness/checks/desarrollo/lib
        claude = base / "proy" / ".claude"
        (claude / "skills" / "dev-accessibility" / "scripts").mkdir(parents=True)
        (claude / "skills" / "dev-accessibility" / "references").mkdir(parents=True)
        (claude / "harness" / "checks" / "desarrollo" / "lib").mkdir(parents=True)
        for f in SCRIPTS.glob("*.py"):
            (claude / "skills" / "dev-accessibility" / "scripts" / f.name).write_text(f.read_text("utf-8"), encoding="utf-8")
        for f in REFS.glob("*.json"):
            (claude / "skills" / "dev-accessibility" / "references" / f.name).write_text(f.read_text("utf-8"), encoding="utf-8")
        script = claude / "skills" / "dev-accessibility" / "scripts" / "review.py"
        codigo, _, errores = _cli(script, base / "p.html")
        t.verdadero("E-56 sin el motor sale con 2", codigo == 2)
        t.contiene("E-56 dice que no lo encuentra", "No encuentro el motor de análisis", errores)
        t.contiene("E-56 y como reponerlo", "install.ps1 -Update", errores)
        t.no_contiene("E-56 sin traceback", "Traceback", errores)
        (claude / "harness" / "checks" / "desarrollo" / "lib" / "a11y.py").write_text((LIB / "a11y.py").read_text("utf-8"), encoding="utf-8")
        codigo, salida, _ = _cli(script, base / "p.html")
        t.igual("E-56 con el motor instalado, corre", 0, codigo)
        t.contiene("E-56 y revisa", "Cobertura: 1 archivo(s)", salida)
        codigo, _, _ = _cli(script, base / "p.html", "--engine", base / "no-existe")
        t.igual("E-56 --engine a una carpeta sin motor sale con 2", 2, codigo)


def test_e57_los_defectos_de_la_lista_quedaron_arreglados(t):
    """E-57 — id sin etiqueta, falsos positivos con <label>, referencias ARIA y el <h1>: cada uno cubierto por E-40 a E-45."""
    casos = {c["id"]: c for c in _corpus()["cases"]}
    pares = (("html-id-sin-label", ["control-no-accessible-name"]), ("html-label-envolvente", []), ("html-labelledby-roto", ["control-no-accessible-name"]),
             ("html-labelledby-sin-texto", ["control-no-accessible-name"]), ("html-dos-h1", []), ("html-sin-h1", []), ("jsx-sin-id", ["control-no-accessible-name"]))
    for id_, esperado in pares:
        c = casos[id_]
        t.igual("E-57 %s" % id_, esperado, _reglas(c["content"], c["file"]))
    # el caso del testigo de paridad quedo reescrito, con su nota
    testigo = json.loads((RAIZ / "tests" / "fixtures" / "paridad-checks.json").read_text("utf-8"))
    caso = next(c for c in testigo["casos"] if c["check"] == "dev-accesibilidad-html")
    t.contiene("E-57 el testigo explica por que dejo de ser paridad con PowerShell", "E-57", caso["nota"])
    t.no_contiene("E-57 y ya no pide dos <h1>", "h1", " ".join(caso["hallazgos"]))
    t.verdadero("E-57 cada aviso del testigo cita criterio y nivel", all("criterio" in h and "nivel" in h for h in caso["hallazgos"]))


# -- la integracion en las skills y el agente ----------------------------------------------------------------------

def test_e58_dev_ui_enlaza_cada_componente(t):
    """E-58 — dev-ui exige una fila accessibilityLinks por componente; sin ellas, ACCESSIBILITY_REVIEW_REQUIRED; el ejemplo usa ids reales."""
    texto = _leer(DESARROLLO / "skills" / "dev-ui" / "SKILL.md")
    t.contiene("E-58 exige las filas", "produces one `accessibilityLinks` row", texto)
    for campo in ("component:", "strategy:", "wcagCriteria:", "verification:"):
        t.contiene("E-58 la fila trae %s" % campo, campo, texto)
    t.contiene("E-58 sin ellas, el estado", "returns `ACCESSIBILITY_REVIEW_REQUIRED`", texto)
    t.contiene("E-58 el estado existe en la lista de estados de dev-ui", "ACCESSIBILITY_REVIEW_REQUIRED\nRESPONSIVE_REVIEW_REQUIRED", texto)
    ids = {c["id"] for c in MATRIZ["components"]} | {"custom"}
    citados = set(re.findall(r"component:\s+([\w-]+)", texto))
    t.verdadero("E-58 el ejemplo nombra componentes (%s)" % sorted(citados), len(citados) >= 2)
    t.vacio("E-58 todo componente del ejemplo esta en la matriz", sorted(citados - ids))
    reusados = re.search(r"reused:\n((?:\s+- [\w-]+\n)+)", texto)
    t.verdadero("E-58 hay una lista de componentes reusados", reusados is not None)
    for r in re.findall(r"- ([\w-]+)", reusados.group(1)):
        t.verdadero("E-58 el componente reusado %s esta en la matriz" % r, r in ids)
    for c in re.findall(r"wcagCriteria: \[([^\]]*)\]", texto):
        for sc in [x.strip() for x in c.split(",")]:
            t.verdadero("E-58 el criterio %s del ejemplo existe" % sc, sc in INDICE)
    for estrategia in re.findall(r"strategy:[ \t]+(\w+)", texto):
        t.verdadero("E-58 la estrategia %s es una de las cuatro" % estrategia,
                    estrategia in ("PROJECT_EXISTING_PATTERN", "OBELISCO_COMPONENT", "OBELISCO_COMPOSITION", "CUSTOM_GCBA_UI"))
    t.contiene("E-58 el AAA de Obelisco es adicional", "An AAA criterion Obelisco names is additional, never AA", texto)


def test_e59_dev_responsive_trae_los_umbrales(t):
    """E-59 — dev-responsive cubre 1.4.4, 1.4.10, 1.4.12, 1.3.4 y 2.5.8 como AA, 2.5.5 como AAA, y dice que se verifican en navegador."""
    texto = _leer(DESARROLLO / "skills" / "dev-responsive" / "SKILL.md")
    for sc in ("1.4.4", "1.4.10", "1.4.12", "1.3.4", "2.5.8"):
        t.verdadero("E-59 %s esta y es AA" % sc, re.search(r"\| %s [^|]+\| AA \|" % re.escape(sc), texto) is not None)
    t.verdadero("E-59 2.5.5 esta y es AAA", re.search(r"\| 2\.5\.5 [^|]+\| AAA \|", texto) is not None)
    for valor in ("200%", "320 CSS px wide", "256 CSS px tall", "line height 1.5", "2 times the font size", "0.12 em", "0.16 em", "24 by 24 CSS px", "44 by 44 CSS px"):
        t.contiene("E-59 el umbral «%s»" % valor, valor, texto)
    t.contiene("E-59 se verifican en navegador", "they are **browser** checks", texto)
    t.contiene("E-59 y no se da por hecho", "stays `not_performed`", texto)
    t.contiene("E-59 el 2.5.5 es adicional y Obelisco no lo nombra", "Additional, not AA; Obelisco does not name it", texto)
    t.contiene("E-59 el contrato trae las entradas wcag", "resizeText200:", texto)


def test_e60_el_flujo_del_frontend_entrega_evidencia(t):
    """E-60 — frontend-implementation ordena ui, accessibility y responsive y exige el registro; el agente lo devuelve."""
    impl = _leer(DESARROLLO / "skills" / "dev-frontend-implementation" / "SKILL.md")
    posiciones = []
    for skill in ("dev-ui", "dev-accessibility", "dev-responsive"):
        m = re.search(r"^%s\s+→\s" % skill, impl, re.M)
        t.verdadero("E-60 la skill %s esta en el orden" % skill, m is not None)
        posiciones.append(m.start() if m else -1)
    t.igual("E-60 en ese orden: ui, accessibility, responsive", sorted(posiciones), posiciones)
    t.contiene("E-60 dice que corren en ese orden", "in this order", impl)
    t.contiene("E-60 exige el registro validado", "register validate", impl)
    t.contiene("E-60 las pruebas manuales solo si se corrieron", "only if they were run", impl)
    t.contiene("E-60 el contrato de la skill", "accessibilityEvidence:", impl)
    agente = _leer(DESARROLLO / "agents" / "dev-frontend.md")
    t.contiene("E-60 el agente devuelve accessibilityEvidence", "accessibilityEvidence:", agente)
    for campo in ("register:", "links:", "counts:", "tests:"):
        t.contiene("E-60 con %s" % campo, campo, agente)
    t.contiene("E-60 con el estado de las tres pruebas", "browser: not_performed, keyboard: not_performed, screen_reader: not_performed", agente)
    t.contiene("E-60 el agente no declara conformidad por una estatica", "claim accessibility conformance from a static analysis", agente)
    for s in ("dev-frontend-implementation", "dev-ui", "dev-accessibility", "dev-responsive"):
        t.contiene("E-60 conserva la skill %s" % s, s, agente.split("## Installed Skills")[1].split("## Responsibilities")[0])


def test_e61_el_registro_de_agentes_sigue_valido(t):
    """E-61 — los cuatro id de skills de dev-frontend y sus rutas no cambian."""
    reg = json.loads((DESARROLLO / "reglas" / "agent-registry.json").read_text("utf-8"))
    agente = next(a for a in reg["agents"] if a["id"] == "dev-frontend")
    t.igual("E-61 las cuatro skills", ["dev-frontend-implementation", "dev-ui", "dev-accessibility", "dev-responsive"], [s["id"] for s in agente["skills"]])
    for s in agente["skills"]:
        t.igual("E-61 la ruta de %s" % s["id"], "skills/%s/SKILL.md" % s["id"], s["file"])
        t.verdadero("E-61 el archivo de %s existe" % s["id"], (DESARROLLO / s["file"]).is_file())
        t.igual("E-61 %s sigue INSTALLED" % s["id"], "INSTALLED", s["status"])
    for s in agente["skills"]:
        texto = _leer(DESARROLLO / s["file"])
        t.contiene("E-61 %s tiene su cabecera" % s["id"], "name: %s" % s["id"], texto)
