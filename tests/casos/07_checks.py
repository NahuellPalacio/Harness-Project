import json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402

# generar-testigo.ps1 arma, para cada caso, un evento con tool_input.file_path
# apuntando al archivo REAL de tests/fixtures/proyecto-checks/ -no al payload
# generico de tests/payloads/-, porque Get-ArchivoEscrito (y, en claude-md-zonas, el
# acceso directo a tool_input.file_path) lee del disco. El payload guardado en el
# testigo solo documenta la FORMA del evento (PostToolUse / Write); el archivo real
# que cada caso ejercito es, en orden, el mismo que arma generar-testigo.ps1.
ARCHIVO_POR_CHECK = {
    "claude-md-zonas": "CLAUDE.md",
    "dev-accesibilidad-html": "pagina.html",
    "dev-api-rutas": "rutas.ts",
    "dev-dependencias": "package.json",
    "dev-infra-en-codigo": "config.ts",
}


def _evento_real(payload_generico, proyecto, archivo):
    """Toma la forma del payload generico y le pone el file_path y el content del
    archivo real de fixture, tal como lo arma New-EventoEscritura en
    generar-testigo.ps1."""
    evento = json.loads(json.dumps(payload_generico))  # copia
    ruta_real = proyecto / archivo
    evento["tool_input"]["file_path"] = str(ruta_real)
    evento["tool_input"]["content"] = ruta_real.read_text("utf-8")
    evento["cwd"] = str(proyecto)
    return evento


def test_paridad_de_hallazgos(t):
    """E-16 — mismos hallazgos, texto incluido, que la version PowerShell."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-checks.json").read_text("utf-8"))
    payload_generico = json.loads((RAIZ / "tests/payloads/post-tool-use-write.json").read_text("utf-8"))

    for caso in testigo["casos"]:
        # El testigo guarda la ruta que corrio PowerShell (.ps1); _cargar es un
        # cargador de Python, asi que se traduce al hermano .py.
        ruta_check = RAIZ / Path(caso["ruta"]).with_suffix(".py")
        # El testigo guarda "proyecto" relativo a la raiz del repo, porque el
        # generador corrio desde ahi.
        proyecto = RAIZ / caso["proyecto"]

        archivo = ARCHIVO_POR_CHECK[caso["check"]]
        evento = _evento_real(payload_generico, proyecto, archivo)

        modulo = reglas._cargar(str(ruta_check))
        obtenidos = modulo.verificar(evento, str(proyecto), caso.get("config"))
        t.igual("E-16 " + caso["check"], caso["hallazgos"], list(obtenidos or []))
