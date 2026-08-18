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


# ── zonas_no_reconocidas — el bug real que la motiva ────────────────────────────
#
# El caso real: el CLAUDE.md del IGE traia las zonas del prototipo con otro nombre
# -'INDICE' y 'CACHE' sin el prefijo 'ZONA'- el instalador no las reconocio y agrego
# las canonicas al lado. Quedaron dos indices y dos caches, uno con el contenido y
# otro vacio, y el check media el vacio. Fallo en silencio, que es lo unico que este
# harness no se permite. Portado de tests/casos/05-memoria.ps1 antes de borrarlo:
# es la unica cobertura directa de zonas.zonas_no_reconocidas.

_CON_VIEJAS = """# CLAUDE.md - proyecto

<!-- ZONA FIJA - reglas -->
- una regla
<!-- /ZONA FIJA -->

<!-- ÍNDICE - un puntero por nota del vault -->
- Dominio -> nota de dominio
<!-- /ÍNDICE -->

<!-- CACHÉ - zona purgable -->
- algo aprendido
<!-- /CACHÉ -->
"""


def test_zonas_no_reconocidas_encuentra_nombres_viejos(t):
    raras = zonas.zonas_no_reconocidas(_CON_VIEJAS)
    t.igual("E-19b encuentra los dos marcadores con nombre viejo", 2, len(raras))
    t.igual("E-19b no confunde ZONA FIJA, que si es canonica", 0,
            len([r for r in raras if r["marcador"] == "ZONA FIJA"]))

    indice = next(r for r in raras if r["marcador"] == "ÍNDICE")
    t.igual("E-19b sugiere la zona canonica a la que se parece", "ZONA INDICE", indice["parecida"])
    cache = next(r for r in raras if r["marcador"] == "CACHÉ")
    t.igual("E-19b reconoce la equivalencia aunque cambie la tilde", "ZONA CACHE", cache["parecida"])


def test_zonas_no_reconocidas_no_dispara_en_lo_canonico(t):
    plantilla = (RAIZ / "comun/claude-md/plantilla-proyecto.md").read_text("utf-8-sig")
    t.igual("E-19b la plantilla canonica no dispara ningun aviso", 0,
            len(zonas.zonas_no_reconocidas(plantilla)))

    con_bloque_comun = "<!-- HARNESS:COMUN - generado -->\ntexto\n<!-- /HARNESS:COMUN -->"
    t.igual("E-19b el bloque HARNESS:COMUN no se reporta como zona rara", 0,
            len(zonas.zonas_no_reconocidas(con_bloque_comun)))

    comentario_suelto = "# CLAUDE.md\n\n<!-- ojo con esto -->\n\ntexto"
    t.igual("E-19b un comentario sin cierre no se confunde con una zona", 0,
            len(zonas.zonas_no_reconocidas(comentario_suelto)))

    t.igual("E-19b un texto sin marcadores no dispara nada", 0,
            len(zonas.zonas_no_reconocidas("# nada")))
