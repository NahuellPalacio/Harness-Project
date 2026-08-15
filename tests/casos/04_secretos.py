import json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import secretos  # noqa: E402


def test_paridad_con_powershell(t):
    """E-01 — mismo veredicto que la implementacion PowerShell, caso por caso."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-secretos.json").read_text("utf-8"))
    catalogo = secretos.importar_patrones(str(RAIZ / "comun/reglas/secretos.patrones.json"))

    for caso in testigo["casos"]:
        h = secretos.buscar_secreto(caso["texto"], catalogo)
        etiqueta = "E-01 " + caso["texto"][:40]
        if not caso["hallazgo"]:
            t.igual(etiqueta + " (no debe disparar)", None, h)
            continue
        t.verdadero(etiqueta + " (debe disparar)", h is not None)
        t.igual(etiqueta + " id", caso["id"], h["id"])
        t.igual(etiqueta + " confianza", caso["confianza"], h["confianza"])
        t.igual(etiqueta + " muestra", caso["muestra"], h["muestra"])


def test_secreto_entre_comillas_invertidas(t):
    """E-05 — el caso que rompio la escritura de docs/versiones/0.4.0.md: un relleno
    obvio entre delimitadores de codigo markdown se bloqueaba como credencial real."""
    catalogo = secretos.importar_patrones(str(RAIZ / "comun/reglas/secretos.patrones.json"))
    t.igual("E-05 relleno entre backticks",
            None, secretos.buscar_secreto("`password = xxxxxxxx`", catalogo))


def test_catalogo_compila(t):
    """E-02 — sobre el catalogo real, no sobre una copia."""
    cat = json.loads((RAIZ / "comun/reglas/secretos.patrones.json").read_text("utf-8"))
    for p in cat["patrones"]:
        try:
            re.compile(p["regex"])
            t.verdadero("E-02 compila " + p["id"], True)
        except re.error as e:
            t.verdadero("E-02 compila %s -> %s" % (p["id"], e), False)
    for i, r in enumerate(cat["ignorar"]["patrones"]):
        try:
            re.compile(r)
            t.verdadero("E-02 compila ignorar[%d]" % i, True)
        except re.error as e:
            t.verdadero("E-02 compila ignorar[%d] -> %s" % (i, e), False)
