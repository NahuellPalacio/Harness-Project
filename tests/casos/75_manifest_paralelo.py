# tests/casos/75_manifest_paralelo.py - Task 6.1 (Verification Pipeline Performance).
#
# VP-E24, parte A: la POLITICA del manifest real (spec 10.3b), `tests/parallel-manifest.json`,
# contra el `tests/casos/` real. Es unidad pura: no lanza procesos, no lanza el runner, no lee
# el oraculo. La parte B (la forma que valida el runner, con procesos reales) esta en
# 75_runner_paralelo.py.
#
# La funcion de politica, validar_politica(), vive SOLO aca (spec 10.3b: la logica normativa no
# se duplica en el runner). Los tests sinteticos le dan manifests y listas de nombres en memoria
# y exigen el rojo NOMBRANDO el caso; los tests del manifest real exigen cero errores.
#
# Restricciones que la suite impone a este archivo (spec 8.3): sin BOM (E-28, 00-encoding-fuentes)
# y sin el parametro viejo de la composicion ni las formas de analisis que E-57/E-61 de
# 63_harness_unico.py buscan en todo tests/.
import copy
import json
import math
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MANIFEST = RAIZ / "tests" / "parallel-manifest.json"
CASOS = RAIZ / "tests" / "casos"

SCHEMA = "parallel-manifest/1"
CLASES = ("parallel", "lane", "serial")
CAMPOS = ("suite", "class", "lane", "maxSeconds", "timeoutSeconds", "reason")
FACTOR = 3
PISO = 1200

# Las etiquetas de los errores, una por regla de 10.3b: los tests las usan para atribuir el rojo.
FORMA, COBERTURA, REASON, FORMULA, SUBCADENA = ("[forma]", "[cobertura]", "[reason]",
                                                 "[formula]", "[subcadena]")


def _numero(v):
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def _entero(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _formula(max_seconds):
    """max(ceil(3 x maxSeconds), 1200), exacto: la aritmetica es de Decimal, no de flotantes."""
    exacto = FACTOR * Decimal(str(max_seconds))
    return max(math.ceil(exacto), PISO)


def validar_politica(manifest, casos):
    """Politica del manifest (spec 10.3b) sobre `manifest` (ya cargado con parse_float=Decimal) y
    `casos` (los nombres de los archivos .ps1 y .py). Devuelve la lista de errores, cada uno con
    su etiqueta y nombrando el caso o el archivo; lista vacia = cumple."""
    errores = []
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        return ["%s schema distinto de %s" % (FORMA, SCHEMA)]
    entradas = manifest.get("suites")
    if not isinstance(entradas, list):
        return ["%s suites no es una lista" % FORMA]

    cuenta = {}
    for i, e in enumerate(entradas):
        if not isinstance(e, dict):
            errores.append("%s la entrada %d no es un objeto" % (FORMA, i))
            continue
        suite = e.get("suite")
        if not isinstance(suite, str) or not suite.strip():
            errores.append("%s la entrada %d no tiene suite (texto no vacio)" % (FORMA, i))
            continue
        cuenta[suite] = cuenta.get(suite, 0) + 1
        faltan = [c for c in CAMPOS if c not in e]
        if faltan:
            errores.append("%s %s: faltan campos %s" % (FORMA, suite, ", ".join(faltan)))
            continue

        clase, lane = e["class"], e["lane"]
        if clase not in CLASES:
            errores.append("%s %s: class desconocida %r" % (FORMA, suite, clase))
        elif clase == "lane":
            if not isinstance(lane, str) or not lane.strip():
                errores.append("%s %s: class lane sin nombre de lane (%r)" % (FORMA, suite, lane))
        elif lane is not None:
            errores.append("%s %s: lane %r con class %s (tiene que ser null)"
                           % (FORMA, suite, lane, clase))

        mx, to = e["maxSeconds"], e["timeoutSeconds"]
        if mx is not None and not (_numero(mx) and mx > 0):
            errores.append("%s %s: maxSeconds %r no es null ni un numero > 0" % (FORMA, suite, mx))
        if to is not None and not (_entero(to) and to > 0):
            errores.append("%s %s: timeoutSeconds %r no es null ni un entero > 0"
                           % (FORMA, suite, to))

        reason = e["reason"]
        if not isinstance(reason, str):
            errores.append("%s %s: reason no es string (%s)" % (REASON, suite, type(reason).__name__))
        elif not reason.strip():
            errores.append("%s %s: reason vacio o solo espacios" % (REASON, suite))

        if mx is None:
            if to is not None:
                errores.append("%s %s: timeoutSeconds %r con maxSeconds null (tiene que ser null)"
                               % (FORMULA, suite, to))
        elif _numero(mx) and mx > 0 and (to is None or _entero(to)):
            esperado = _formula(mx)
            if to != esperado:
                errores.append("%s %s: timeoutSeconds %r, la formula da %d para maxSeconds %s"
                               % (FORMULA, suite, to, esperado, mx))

    nombres = list(casos)
    for suite, veces in sorted(cuenta.items()):
        if veces > 1:
            errores.append("%s %s: entrada duplicada (%d veces)" % (COBERTURA, suite, veces))
        if suite not in nombres:
            errores.append("%s %s: entrada de un archivo inexistente" % (COBERTURA, suite))
    for caso in sorted(nombres):
        if caso not in cuenta:
            errores.append("%s %s: sin entrada" % (COBERTURA, caso))
    if len(entradas) != len(nombres):
        errores.append("%s %d entradas para %d archivos" % (COBERTURA, len(entradas), len(nombres)))

    py = sorted(n for n in nombres if n.endswith(".py"))
    for a in py:
        for b in py:
            if a != b and a in b:
                errores.append("%s %s es subcadena de %s" % (SUBCADENA, a, b))
    return errores


# ---- Datos sinteticos: manifests y listas en memoria, sin archivos ------------------------------

CASOS_SINT = ["caso_a.ps1", "caso_b.py", "caso_c.py"]


def _e(suite, clase="parallel", lane=None, mx=None, to=None, reason="una razon"):
    return {"suite": suite, "class": clase, "lane": lane,
            "maxSeconds": None if mx is None else Decimal(mx), "timeoutSeconds": to,
            "reason": reason}


def _bueno():
    return {"schema": SCHEMA, "suites": [
        _e("caso_a.ps1", mx="1.0", to=1200),
        _e("caso_b.py", clase="lane", lane="motor", mx="728.8", to=2187),
        _e("caso_c.py")]}


def _con(cambio):
    """Una copia del manifest correcto con `cambio(manifest)` aplicado."""
    m = copy.deepcopy(_bueno())
    cambio(m)
    return m


def _nombra(errores, etiqueta, caso):
    return any(etiqueta in e and caso in e for e in errores)


def _cargar_real():
    texto = MANIFEST.read_text(encoding="utf-8")
    return json.loads(texto, parse_float=Decimal)


def _casos_reales():
    return sorted(p.name for p in CASOS.iterdir()
                  if p.is_file() and p.suffix in (".ps1", ".py"))


# ---- VP-E24 parte A: el manifest real ------------------------------------------------------------

def _errores_reales(etiqueta=None):
    errores = validar_politica(_cargar_real(), _casos_reales())
    return [e for e in errores if etiqueta is None or etiqueta in e]


def test_vp_e24a_real_cobertura_uno_a_uno(t):
    """VP-E24 (A): cada tests/casos/*.ps1 y *.py tiene exactamente una entrada, sin duplicadas ni
    entradas de archivos inexistentes."""
    m, casos = _cargar_real(), _casos_reales()
    t.igual("VP-E24A tantas entradas como archivos", len(casos), len(m["suites"]))
    nombres = [e["suite"] for e in m["suites"]]
    t.vacio("VP-E24A archivos de tests/casos/ sin entrada", sorted(set(casos) - set(nombres)))
    t.vacio("VP-E24A entradas sin archivo en tests/casos/", sorted(set(nombres) - set(casos)))
    t.vacio("VP-E24A cobertura del manifest real", _errores_reales(COBERTURA))


def test_vp_e24a_real_reason_no_vacio(t):
    """VP-E24 (A): reason es string y no esta vacio ni es solo espacios (el texto no se juzga)."""
    t.vacio("VP-E24A reason del manifest real", _errores_reales(REASON))


def test_vp_e24a_real_timeout_sigue_la_formula(t):
    """VP-E24 (A): timeoutSeconds = max(ceil(3 x maxSeconds), 1200) exacto; null si maxSeconds es null."""
    t.vacio("VP-E24A formula del manifest real", _errores_reales(FORMULA))


def test_vp_e24a_real_ningun_py_es_subcadena_de_otro(t):
    """VP-E24 (A): -k es por subcadena (correr.py), un nombre dentro de otro correria los dos."""
    t.vacio("VP-E24A subcadenas entre los .py reales", _errores_reales(SUBCADENA))


def test_vp_e24a_real_forma_de_cada_entrada(t):
    """VP-E24 (A): schema, class, lane, maxSeconds y timeoutSeconds segun 10.2 (las reglas de politica)."""
    t.vacio("VP-E24A forma de las entradas del manifest real", _errores_reales(FORMA))


def test_vp_e24a_real_cero_errores_de_politica(t):
    """VP-E24 (A): el manifest real cumple toda la politica de 10.3b."""
    t.vacio("VP-E24A politica completa sobre el manifest real", _errores_reales())


# ---- VP-E24 parte A: datos sinteticos (cada uno exige el rojo nombrando el caso) -----------------

def test_vp_e24a_sintetico_un_manifest_correcto_da_cero_errores(t):
    """VP-E24 (A): el manifest sintetico correcto cumple la politica; t73 (2187) pasa el piso."""
    t.igual("VP-E24A sintetico correcto", [], validar_politica(_bueno(), CASOS_SINT))


def test_vp_e24a_sintetico_falta_una_entrada(t):
    """VP-E24 (A): un archivo de tests/casos/ sin entrada pone rojo y lo nombra."""
    m = _con(lambda m: m["suites"].pop(1))                       # sin caso_b.py
    errores = validar_politica(m, CASOS_SINT)
    t.verdadero("VP-E24A falta de una entrada: rojo", errores != [])
    t.verdadero("VP-E24A falta de una entrada: nombra caso_b.py",
                _nombra(errores, COBERTURA, "caso_b.py"))


def test_vp_e24a_sintetico_entrada_duplicada(t):
    """VP-E24 (A): dos entradas del mismo archivo ponen rojo y lo nombran."""
    m = _con(lambda m: m["suites"].append(_e("caso_c.py")))
    errores = validar_politica(m, CASOS_SINT)
    t.verdadero("VP-E24A entrada duplicada: nombra caso_c.py",
                _nombra(errores, COBERTURA, "caso_c.py") and any("duplicada" in e for e in errores))


def test_vp_e24a_sintetico_entrada_de_un_archivo_inexistente(t):
    """VP-E24 (A): una entrada que nombra un archivo que no esta pone rojo y lo nombra."""
    m = _con(lambda m: m["suites"].append(_e("fantasma.py")))
    errores = validar_politica(m, CASOS_SINT)
    t.verdadero("VP-E24A archivo inexistente: nombra fantasma.py",
                _nombra(errores, COBERTURA, "fantasma.py") and any("inexistente" in e for e in errores))


def test_vp_e24a_sintetico_class_desconocida(t):
    """VP-E24 (A): una class fuera de parallel / lane / serial pone rojo y nombra el caso."""
    m = _con(lambda m: m["suites"][2].update({"class": "paralelo"}))
    t.verdadero("VP-E24A class desconocida: nombra caso_c.py",
                _nombra(validar_politica(m, CASOS_SINT), FORMA, "caso_c.py"))


def test_vp_e24a_sintetico_lane_sin_nombre(t):
    """VP-E24 (A): class lane con lane null o vacio pone rojo y nombra el caso; lane con otra class tambien."""
    for nombre, valor in (("null", None), ("vacio", ""), ("solo espacios", "  ")):
        m = _con(lambda m: m["suites"][1].update({"lane": valor}))
        t.verdadero("VP-E24A lane %s con class lane: nombra caso_b.py" % nombre,
                    _nombra(validar_politica(m, CASOS_SINT), FORMA, "caso_b.py"))
    m = _con(lambda m: m["suites"][2].update({"lane": "motor"}))
    t.verdadero("VP-E24A lane con class parallel: nombra caso_c.py",
                _nombra(validar_politica(m, CASOS_SINT), FORMA, "caso_c.py"))


def test_vp_e24a_sintetico_reason_vacio_o_solo_espacios(t):
    """VP-E24 (A): reason "" y reason "   " ponen rojo y nombran el caso."""
    for nombre, valor in (("vacio", ""), ("tres espacios", "   "), ("tab y salto", "\t\n")):
        m = _con(lambda m: m["suites"][0].update({"reason": valor}))
        t.verdadero("VP-E24A reason %s: nombra caso_a.ps1" % nombre,
                    _nombra(validar_politica(m, CASOS_SINT), REASON, "caso_a.ps1"))


def test_vp_e24a_sintetico_reason_que_no_es_string(t):
    """VP-E24 (A): reason que no es string (numero, null, lista) pone rojo y nombra el caso."""
    for nombre, valor in (("numero", 5), ("null", None), ("lista", ["x"])):
        m = _con(lambda m: m["suites"][0].update({"reason": valor}))
        t.verdadero("VP-E24A reason %s: nombra caso_a.ps1" % nombre,
                    _nombra(validar_politica(m, CASOS_SINT), REASON, "caso_a.ps1"))


def test_vp_e24a_sintetico_timeout_fuera_de_la_formula(t):
    """VP-E24 (A): 1201 con maxSeconds 1.0 y 2186 con 728.8 ponen rojo; 2187 y el borde de ceil no."""
    m = _con(lambda m: m["suites"][0].update({"timeoutSeconds": 1201}))
    t.verdadero("VP-E24A 1201 con maxSeconds 1.0: nombra caso_a.ps1",
                _nombra(validar_politica(m, CASOS_SINT), FORMULA, "caso_a.ps1"))
    m = _con(lambda m: m["suites"][1].update({"timeoutSeconds": 2186}))
    t.verdadero("VP-E24A 2186 con maxSeconds 728.8: nombra caso_b.py",
                _nombra(validar_politica(m, CASOS_SINT), FORMULA, "caso_b.py"))
    m = _con(lambda m: m["suites"][1].update({"timeoutSeconds": 2188}))
    t.verdadero("VP-E24A 2188 con maxSeconds 728.8: nombra caso_b.py",
                _nombra(validar_politica(m, CASOS_SINT), FORMULA, "caso_b.py"))
    # El borde de ceil: 3 x 400.1 = 1200.3 -> 1201; 3 x 400 = 1200 -> 1200 (el piso).
    for mx, to, ok in (("400.1", 1201, True), ("400.1", 1200, False), ("400", 1200, True),
                       ("400", 1201, False)):
        m = _con(lambda m: m["suites"][0].update({"maxSeconds": Decimal(mx), "timeoutSeconds": to}))
        t.igual("VP-E24A borde maxSeconds %s timeoutSeconds %d" % (mx, to),
                ok, validar_politica(m, CASOS_SINT) == [])


def test_vp_e24a_sintetico_timeout_con_maxseconds_null(t):
    """VP-E24 (A): timeoutSeconds no null con maxSeconds null pone rojo; y null con maxSeconds dado tambien."""
    m = _con(lambda m: m["suites"][2].update({"timeoutSeconds": 1200}))
    t.verdadero("VP-E24A timeout 1200 con maxSeconds null: nombra caso_c.py",
                _nombra(validar_politica(m, CASOS_SINT), FORMULA, "caso_c.py"))
    m = _con(lambda m: m["suites"][0].update({"timeoutSeconds": None}))
    t.verdadero("VP-E24A timeout null con maxSeconds 1.0: nombra caso_a.ps1",
                _nombra(validar_politica(m, CASOS_SINT), FORMULA, "caso_a.ps1"))


def test_vp_e24a_sintetico_numeros_fuera_de_rango(t):
    """VP-E24 (A): maxSeconds <= 0, timeoutSeconds no entero o <= 0 ponen rojo y nombran el caso."""
    for nombre, campo, valor in (("maxSeconds 0", "maxSeconds", Decimal("0")),
                                 ("maxSeconds negativo", "maxSeconds", Decimal("-1.5")),
                                 ("maxSeconds texto", "maxSeconds", "1.0"),
                                 ("timeoutSeconds 0", "timeoutSeconds", 0),
                                 ("timeoutSeconds decimal", "timeoutSeconds", Decimal("1200.0")),
                                 ("timeoutSeconds texto", "timeoutSeconds", "1200")):
        m = _con(lambda m: m["suites"][0].update({campo: valor}))
        t.verdadero("VP-E24A %s: nombra caso_a.ps1" % nombre,
                    _nombra(validar_politica(m, CASOS_SINT), FORMA, "caso_a.ps1"))


def test_vp_e24a_sintetico_par_caso_b_y_xcaso_b(t):
    """VP-E24 (A): caso_b.py dentro de xcaso_b.py pone rojo y nombra los dos; el unico error es ese."""
    casos = ["caso_b.py", "xcaso_b.py"]
    m = {"schema": SCHEMA, "suites": [_e("caso_b.py"), _e("xcaso_b.py")]}
    errores = validar_politica(m, casos)
    t.verdadero("VP-E24A subcadena: nombra caso_b.py y xcaso_b.py",
                any(SUBCADENA in e and "caso_b.py" in e and "xcaso_b.py" in e for e in errores))
    t.igual("VP-E24A subcadena: ningun otro error", 1, len(errores))
    # Un .ps1 dentro de otro nombre no cuenta: -k solo existe en el motor de Python.
    t.igual("VP-E24A los .ps1 no entran en la regla de subcadena", [],
            validar_politica({"schema": SCHEMA, "suites": [_e("a.ps1"), _e("xa.ps1")]},
                             ["a.ps1", "xa.ps1"]))


def test_vp_e24a_sintetico_manifest_de_forma_rota_no_revienta(t):
    """VP-E24 (A): schema distinto, suites que no es lista, entrada sin campos: rojo, no excepcion."""
    t.verdadero("VP-E24A schema distinto", validar_politica({"schema": "otro", "suites": []}, []) != [])
    t.verdadero("VP-E24A suites no es lista",
                validar_politica({"schema": SCHEMA, "suites": {}}, []) != [])
    m = _con(lambda m: m["suites"][0].pop("reason"))
    t.verdadero("VP-E24A entrada sin reason: nombra caso_a.ps1",
                _nombra(validar_politica(m, CASOS_SINT), FORMA, "caso_a.ps1"))
