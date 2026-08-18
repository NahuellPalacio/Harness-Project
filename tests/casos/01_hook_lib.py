import json, subprocess, sys, os, re, types
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import hook   # noqa: E402


def _ejecutar(fixture, entrada_bytes, entorno=None):
    """Corre un fixture de hook como subproceso con `entrada_bytes` crudos en stdin.

    A diferencia de `_correr`, devuelve el CompletedProcess completo: da acceso al
    codigo de salida ademas del stdout, y acepta stdin roto o con BOM tal cual.

    Sin `entorno`, hereda el del proceso actual tal cual: el hook tiene que garantizar
    su propio encoding de salida, no depender de que quien lo invoque se lo prepare
    (ver `test_avisar_sobrevive_consola_cp1252`, que lo fuerza al peor caso a proposito).
    """
    ruta = RAIZ / "tests" / "fixtures" / fixture
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


def test_avisar_sobrevive_consola_cp1252(t):
    # E-10 tal cual la escribe la spec: el aviso llega integro "aunque la consola este
    # en CP1252". Se fuerza el peor caso a proposito -PYTHONIOENCODING=cp1252, sin
    # PYTHONUTF8- para probar que el hook garantiza su propio encoding de salida en vez
    # de depender de que quien lo invoque (el shim, en produccion) se lo prepare.
    entorno = dict(os.environ)
    entorno.pop("PYTHONUTF8", None)
    entorno["PYTHONIOENCODING"] = "cp1252"
    entrada = json.dumps({"session_id": "s-e10-cp1252", "prompt": "definición"}).encode("utf-8")
    resultado = _ejecutar("hook-eco.py", entrada, entorno=entorno)
    salida = resultado.stdout.decode("utf-8")
    t.igual("E-10 cp1252 codigo 0", 0, resultado.returncode)
    t.contiene("E-10 cp1252 tilde intacta", "definición", salida)


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


def test_sys_exit_no_cero_se_normaliza(t):
    # Fix 2: un sys.exit con codigo distinto de 0 o None, aunque salga del cuerpo del
    # hook, no puede escapar. El contrato es salir 0 siempre.
    resultado = _ejecutar(
        "hook-sale-con-codigo.py", json.dumps({"session_id": "s-fix2"}).encode("utf-8"))
    t.igual("fix2 codigo se normaliza a 0", 0, resultado.returncode)
    t.igual("fix2 no emite nada", "", resultado.stdout.decode("utf-8"))


def test_bloquear_emite_deny(t):
    # Fix 3: bloquear es la unica salida capaz de impedir una herramienta y no tenia
    # ningun test. Se verifica la forma completa del JSON, no solo que la palabra
    # "deny" aparezca en algun lado.
    salida = _correr("hook-deny.py", {"session_id": "s-deny"})
    objeto = json.loads(salida)
    especifico = objeto.get("hookSpecificOutput", {})
    t.igual("bloquear declara su evento", "PreToolUse", especifico.get("hookEventName"))
    t.igual("bloquear decide deny", "deny", especifico.get("permissionDecision"))
    t.contiene("bloquear dice que hacer, no solo que se impidio",
               "variable de entorno", especifico.get("permissionDecisionReason", ""))


def test_preguntar_emite_ask(t):
    # Fix 3: preguntar no tenia ni fixture. Misma verificacion de forma completa.
    salida = _correr("hook-preguntar.py", {"session_id": "s-preguntar"})
    objeto = json.loads(salida)
    especifico = objeto.get("hookSpecificOutput", {})
    t.igual("preguntar declara su evento", "PreToolUse", especifico.get("hookEventName"))
    t.igual("preguntar decide ask", "ask", especifico.get("permissionDecision"))
    t.verdadero("preguntar trae un motivo", bool(especifico.get("permissionDecisionReason")))


def test_doble_emision_gana_la_primera(t):
    # Fix 4: un cuerpo que avisa y despues explota no puede dejar dos JSON
    # concatenados en stdout. json.loads revienta solo si hay "extra data" -es decir,
    # si el bug esta presente-, asi que la asercion mas fuerte es que el parseo ni
    # siquiera tire excepcion.
    session_id = "s-fix4-doble-emision"
    _limpiar_marca(session_id, "PostToolUse")
    try:
        entrada = json.dumps({"session_id": session_id}).encode("utf-8")
        resultado = _ejecutar("hook-avisa-y-explota.py", entrada)
        salida = resultado.stdout.decode("utf-8")
        t.igual("fix4 codigo 0", 0, resultado.returncode)
        objeto = json.loads(salida)  # explota con "Extra data" si hay dos JSON pegados
        t.verdadero("fix4 la salida es un unico objeto JSON", isinstance(objeto, dict))
        t.contiene("fix4 sobrevive el primer aviso", "aviso legitimo antes de explotar", salida)
        t.no_contiene("fix4 el systemMessage descartado no aparece", "systemMessage", salida)
    finally:
        _limpiar_marca(session_id, "PostToolUse")


def test_mensaje_de_sistema_sobrevive_pipe_roto(t):
    # Fix 1: si escribir el systemMessage revienta (el padre cerro el pipe), la
    # excepcion no puede escapar de mensaje_de_sistema -es la ultima red del harness.
    # Se simula en proceso, sin subprocess: reproducir un BrokenPipeError real via
    # pipes de SO es no determinista (el buffer del kernel puede absorber un JSON
    # chico sin que nadie lo lea), asi que se reemplaza sys.stdout.buffer por un doble
    # que revienta al escribir.
    def _escribir_roto(_datos):
        raise BrokenPipeError("simulado: el padre cerro el pipe")

    falso_stdout = types.SimpleNamespace(
        buffer=types.SimpleNamespace(write=_escribir_roto, flush=lambda: None))

    session_id = "s-fix1-pipe-roto"
    clave = "prueba-pipe-roto"
    _limpiar_marca(session_id, clave)
    original_stdout = sys.stdout
    hook._ya_emitido = False
    sys.stdout = falso_stdout
    try:
        no_exploto = True
        try:
            hook.mensaje_de_sistema("prueba", session_id=session_id, clave=clave)
        except BaseException:
            no_exploto = False
        t.verdadero("fix1 mensaje_de_sistema no propaga el BrokenPipeError", no_exploto)
    finally:
        sys.stdout = original_stdout
        hook._ya_emitido = False
        _limpiar_marca(session_id, clave)
