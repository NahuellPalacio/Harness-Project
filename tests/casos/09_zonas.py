import json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIB = RAIZ / "comun" / "hooks" / "lib"
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import zonas  # noqa: E402


def test_mide_igual_que_powershell(t):
    """E-19 — mismas mediciones y mismos excesos sobre el mismo CLAUDE.md."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-zonas.json").read_text("utf-8"))
    texto = (RAIZ / "tests/fixtures/claude-md-de-prueba.md").read_text("utf-8")
    medido = {z["nombre"]: z["lineas"] for z in zonas.medir_zonas(texto)}
    for nombre, esperado in testigo["zonas"].items():
        t.igual("E-19 " + nombre, esperado, medido[nombre])
    t.igual("E-19 fuera de zonas", testigo["fueraDeZonas"], zonas.medir_fuera_de_zonas(texto))


def test_la_definicion_sale_por_json(t):
    """E-18 — el verbo que consume install.ps1."""
    salida = subprocess.run([sys.executable, str(LIB / "zonas.py"), "definicion"],
                            capture_output=True, text=True, encoding="utf-8")
    zs = json.loads(salida.stdout)
    t.igual("E-18 cuatro zonas", 4, len(zs))
    t.igual("E-18 primera", "ZONA FIJA", zs[0]["nombre"])
    t.igual("E-18 techo", "techoZonaFija", zs[0]["techo"])
