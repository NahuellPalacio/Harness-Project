import sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402


def _dir_temporal_con_checks(archivos):
    """Crea un directorio temporal con un .py por entrada de `archivos` (nombre ->
    contenido) y lo devuelve. El descubrimiento de reglas.py es estar en el
    directorio: no hace falta registrar nada mas."""
    d = tempfile.mkdtemp(prefix="gcba-harness-reglas-")
    for nombre, contenido in archivos.items():
        (Path(d) / nombre).write_text(contenido, encoding="utf-8")
    return d


def _dir_temporal_con_check(nombre, contenido):
    return _dir_temporal_con_checks({nombre: contenido})


def test_descubre_por_estar_en_el_directorio(t):
    """E-13 — un .py nuevo en el directorio corre, sin registrarlo en ningun lado."""
    d = _dir_temporal_con_check("mi-check.py", 'def verificar(e, p, c): return ["hola"]')
    t.igual("E-13", ["hola"], reglas.correr_checks({}, d, "", None))


def test_un_check_roto_no_tumba_a_los_demas(t):
    """E-14 — se saltea en silencio y los otros corren igual."""
    d = _dir_temporal_con_checks({
        "a-explota.py": 'def verificar(e, p, c): raise RuntimeError("boom")',
        "b-anda.py":    'def verificar(e, p, c): return ["sigo vivo"]'})
    t.igual("E-14", ["sigo vivo"], reglas.correr_checks({}, d, "", None))


def test_tope_de_ocho(t):
    """E-15 — con mas de 8 hallazgos, se recorta."""
    d = _dir_temporal_con_check("mucho.py",
        'def verificar(e, p, c): return ["h%d" % i for i in range(20)]')
    t.igual("E-15", 8, len(reglas.correr_checks({}, d, "", None)))
