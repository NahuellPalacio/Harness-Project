import json, subprocess, sys, os, re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import hook   # noqa: E402


def _ejecutar(fixture, entrada_bytes):
    """Corre un fixture de hook como subproceso con `entrada_bytes` crudos en stdin.

    A diferencia de `_correr`, devuelve el CompletedProcess completo: da acceso al
    codigo de salida ademas del stdout, y acepta stdin roto o con BOM tal cual.

    PYTHONUTF8 fuerza el modo UTF-8 de Python (PEP 540) en el subproceso: sin esto,
    en Windows sys.stdout usa la codepage ANSI de la consola y un aviso con tilde
    llega corrupto, el mismo problema que Hook.psm1 resuelve con
    Initialize-HookEncoding en la version PowerShell.
    """
    ruta = RAIZ / "tests" / "fixtures" / fixture
    entorno = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, str(ruta)],
        input=entrada_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=entorno,
    )


def _correr(fixture, payload):
    """Corre un fixture de hook con `payload` (dict) por stdin y devuelve su stdout."""
    entrada = json.dumps(payload).encode("utf-8")
    return _ejecutar(fixture, entrada).stdout.decode("utf-8")


def _ruta_marca(session_id, clave):
    # Misma sanitizacion que hook.mensaje_de_sistema: no reimplementa la logica del
    # modulo, calcula donde deberia haber quedado la marca para poder limpiarla.
    seguro = re.sub(r"[^A-Za-z0-9._-]", "_", "%s.%s" % (session_id, clave))
    return os.path.join(hook.DIR_ESTADO, seguro + ".avisado")


def _limpiar_marca(session_id, clave):
    ruta = _ruta_marca(session_id, clave)
    if os.path.exists(ruta):
        os.remove(ruta)


def test_campo_devuelve_default_si_falta(t):
    e = {"tool_input": {"file_path": "a.md"}}
    t.igual("E-09 ruta presente", "a.md", hook.campo(e, "tool_input.file_path", ""))
    t.igual("E-09 ruta ausente", "", hook.campo(e, "tool_input.content", ""))
    t.igual("E-09 rama inexistente", "", hook.campo(e, "no.existe.nada", ""))
    t.igual("E-09 evento None", "", hook.campo(None, "tool_input.file_path", ""))


def test_avisar_no_escapa_no_ascii(t):
    salida = _correr("hook-eco.py", {"session_id": "s", "prompt": "definición"})
    t.contiene("E-10 tilde intacta", "definición", salida)
    t.no_contiene("E-10 sin \\u", "\\u00f3", salida)


def test_silencio_es_silencio(t):
    salida = _correr("hook-silencio.py", {"session_id": "s"})
    t.igual("E-12 stdout vacio", "", salida)


def test_codigo_0_siempre(t):
    _limpiar_marca("sin-sesion", "PostToolUse")
    try:
        valido = _ejecutar("hook-silencio.py", json.dumps({"session_id": "s-e06"}).encode("utf-8"))
        t.igual("E-06 codigo 0 con evento valido", 0, valido.returncode)

        vacio = _ejecutar("hook-silencio.py", b"")
        t.igual("E-06 codigo 0 con stdin vacio", 0, vacio.returncode)

        roto = _ejecutar("hook-silencio.py", b"{ esto no es json")
        t.igual("E-06 codigo 0 con json roto", 0, roto.returncode)
    finally:
        _limpiar_marca("sin-sesion", "PostToolUse")


def test_hook_roto_avisa_y_sale_0(t):
    session_id = "s-e07-explota-gcba-harness"
    _limpiar_marca(session_id, "PostToolUse")
    try:
        resultado = _ejecutar(
            "hook-explota.py", json.dumps({"session_id": session_id}).encode("utf-8"))
        salida = resultado.stdout.decode("utf-8")
        t.igual("E-07 codigo 0", 0, resultado.returncode)
        t.contiene("E-07 emite systemMessage", '"systemMessage"', salida)
        t.contiene("E-07 el mensaje nombra el hook que fallo", "PostToolUse", salida)
    finally:
        _limpiar_marca(session_id, "PostToolUse")


def test_hook_roto_no_avisa_dos_veces(t):
    session_id = "s-e08-explota-gcba-harness"
    _limpiar_marca(session_id, "PostToolUse")
    try:
        entrada = json.dumps({"session_id": session_id}).encode("utf-8")
        primera = _ejecutar("hook-explota.py", entrada).stdout.decode("utf-8")
        segunda = _ejecutar("hook-explota.py", entrada).stdout.decode("utf-8")
        t.contiene("E-08 la primera vez avisa", '"systemMessage"', primera)
        t.igual("E-08 la segunda vez ya no avisa", "", segunda)
    finally:
        _limpiar_marca(session_id, "PostToolUse")


def test_stdin_con_bom_parsea(t):
    payload = json.dumps({"session_id": "s-e11", "prompt": "hola"}).encode("utf-8")
    con_bom = b"\xef\xbb\xbf" + payload
    resultado = _ejecutar("hook-eco.py", con_bom)
    salida = resultado.stdout.decode("utf-8")
    t.igual("E-11 codigo 0 con BOM", 0, resultado.returncode)
    t.contiene("E-11 el BOM no rompe el parseo", "hola", salida)
