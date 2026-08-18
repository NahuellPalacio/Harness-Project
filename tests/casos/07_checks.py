import json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402

# generar-testigo.ps1 arma, para cada caso, un evento con tool_input.file_path
# apuntando al archivo REAL de tests/fixtures/proyecto-checks/ -no al payload
# generico de tests/payloads/-, porque Get-ArchivoEscrito (y, en claude-md-zonas, el
# acceso directo a tool_input.file_path) lee del disco. El payload guardado en el
# testigo solo documenta la FORMA del evento (PostToolUse / Write); el campo
# "archivo" del testigo -relativo a la raiz del repo, como "proyecto"- dice sobre
# que archivo se corrio de verdad.


def _evento_real(payload_generico, proyecto, ruta_archivo):
    """Toma la forma del payload generico y le pone el file_path y el content del
    archivo real de fixture, tal como lo arma New-EventoEscritura en
    generar-testigo.ps1."""
    evento = json.loads(json.dumps(payload_generico))  # copia
    evento["tool_input"]["file_path"] = str(ruta_archivo)
    evento["tool_input"]["content"] = ruta_archivo.read_text("utf-8")
    evento["cwd"] = str(proyecto)
    return evento


def test_paridad_de_hallazgos(t):
    """E-16 — mismos hallazgos, texto incluido, que la version PowerShell."""
    testigo = json.loads((RAIZ / "tests/fixtures/paridad-checks.json").read_text("utf-8"))

    for caso in testigo["casos"]:
        # La forma del payload la dice el propio testigo, caso por caso: hoy los cinco
        # declaran el mismo archivo, pero leerlo de aca -y no de una ruta clavada- es lo
        # que evita que el dia que diverjan el test siga probando el payload de otro caso.
        payload_generico = json.loads((RAIZ / "tests/payloads" / caso["payload"]).read_text("utf-8"))
        # El testigo guarda la ruta que corrio PowerShell (.ps1); _cargar es un
        # cargador de Python, asi que se traduce al hermano .py.
        ruta_check = RAIZ / Path(caso["ruta"]).with_suffix(".py")
        # El testigo guarda "proyecto" y "archivo" relativos a la raiz del repo,
        # porque el generador corrio desde ahi.
        proyecto = RAIZ / caso["proyecto"]
        ruta_archivo = RAIZ / caso["archivo"]

        evento = _evento_real(payload_generico, proyecto, ruta_archivo)

        modulo = reglas._cargar(str(ruta_check))
        obtenidos = modulo.verificar(evento, str(proyecto), caso.get("config"))
        t.igual("E-16 " + caso["check"], caso["hallazgos"], list(obtenidos or []))
