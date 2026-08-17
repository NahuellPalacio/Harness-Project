# SessionStart, UserPromptSubmit y PostToolUse, punta a punta como proceso hijo -igual
# que los invoca Claude Code-. Es lo que reemplaza a tests/casos/05-memoria.ps1.
#
# El resto de lo que probaba 05-memoria.ps1 -medicion de zonas, zonas no reconocidas,
# contenido fuera de zonas- son funciones de lib.zonas y quedaron en tests/casos/09_zonas.py,
# que ya las cubre.
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"


def _correr_proceso(script, payload):
    entrada = json.dumps(payload).encode("utf-8")
    return subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=entrada, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _correr(script, payload):
    return _correr_proceso(script, payload).stdout.decode("utf-8")


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def _proyecto_de_prueba(usuario=None, harness=None, version="0.0.0", config_extra=None):
    """Un proyecto descartable con .claude/harness.config.json y harness.lock.json,
    como los deja install.ps1."""
    proy = Path(tempfile.gettempdir()) / ("harness-mem-" + uuid.uuid4().hex[:8])
    proy.mkdir(parents=True, exist_ok=True)

    config = dict(config_extra or {})
    if usuario is not None:
        config["usuario"] = usuario
    _escribir(proy / ".claude" / "harness.config.json", json.dumps(config, ensure_ascii=False))

    if harness is not None:
        lock = {"harness": harness, "version": version}
        _escribir(proy / ".claude" / "harness.lock.json", json.dumps(lock, ensure_ascii=False))

    return proy


def _dir_vacio():
    """Una ruta que NO existe en disco. SessionStart corta apenas la lee -paridad con
    `-not (Test-Path $proyecto)` en session-start.ps1- y sale en silencio total.

    Un directorio que SI existe pero esta vacio no es silencioso: la seccion de git dice
    igual que el proyecto no esta versionado. Eso no es un caso de "nada que decir", es
    un caso con UNA sola cosa que decir -y session-start.ps1 ya la dice hoy-, asi que
    portarlo con silencio total seria un cambio de comportamiento, no una migracion."""
    return Path(tempfile.gettempdir()) / ("harness-vacio-" + uuid.uuid4().hex[:8])


def _rama_actual(proy):
    return subprocess.run(["git", "-C", str(proy), "rev-parse", "--abbrev-ref", "HEAD"],
                          capture_output=True, text=True, encoding="utf-8").stdout.strip()


def _git_init(proy):
    subprocess.run(["git", "-C", str(proy), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(proy), "config", "user.email", "prueba@gcba.gob.ar"], check=True)
    subprocess.run(["git", "-C", str(proy), "config", "user.name", "Prueba"], check=True)


# ── SessionStart: el saludo ──────────────────────────────────────────────────────

def test_saludo_trae_nombre_y_harness(t):
    proy = _proyecto_de_prueba(usuario="Nahue", harness=["comun", "analisis"], version="0.13.0")
    _git_init(proy)
    _escribir(proy / "a.txt", "x")
    subprocess.run(["git", "-C", str(proy), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(proy), "commit", "-q", "-m", "primero"], check=True)

    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("saludo: nombre", "Nahue", ctx)
    t.contiene("saludo: harness", "comun, analisis v0.13.0", ctx)
    t.verdadero("las cuatro secciones van en orden: encabezado antes que el estado de git",
               ctx.index("Nahue") < ctx.index("git:"))


def test_sin_nada_que_decir_no_dice_nada(t):
    """E-12 tambien vale para SessionStart."""
    t.igual("silencio", "", _correr("session-start.py",
            {"session_id": "s", "cwd": str(_dir_vacio()), "hook_event_name": "SessionStart"}))


def test_avisa_git_limpio_y_los_ultimos_commits(t):
    proy = _proyecto_de_prueba()
    _git_init(proy)
    _escribir(proy / "a.txt", "contenido")
    # -A: el proyecto ya trae .claude/harness.config.json de _proyecto_de_prueba, y si
    # queda sin commitear el repo aparece sucio y el caso deja de probar lo que dice probar.
    subprocess.run(["git", "-C", str(proy), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(proy), "commit", "-q", "-m", "primer commit"], check=True)
    rama = _rama_actual(proy)

    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("git limpio", "git: %s, limpio" % rama, ctx)
    t.contiene("ultimo trabajo", "Ultimo trabajo:", ctx)
    t.contiene("nombra el commit", "primer commit", ctx)


def test_avisa_git_sucio_con_la_cuenta(t):
    proy = _proyecto_de_prueba()
    _git_init(proy)
    _escribir(proy / "a.txt", "contenido")
    subprocess.run(["git", "-C", str(proy), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(proy), "commit", "-q", "-m", "primero"], check=True)
    _escribir(proy / "b.txt", "otro")

    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("git sucio", "1 con cambios", ctx)


def test_avisa_que_no_esta_versionado(t):
    proy = _proyecto_de_prueba(usuario="Ana")
    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("avisa que el proyecto no esta versionado", "no esta versionado", ctx)


def test_devuelve_lo_que_quedo_anotado_en_la_cache(t):
    proy = _proyecto_de_prueba(usuario="Ana")
    _escribir(proy / "CLAUDE.md",
              "# CLAUDE.md\n\n<!-- ZONA CACHE -->\n"
              "- ES0903 sin validar contra un proyecto con codigo\n"
              "- una\n- dos\n- tres\n- cuatro\n"
              "<!-- /ZONA CACHE -->\n")
    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("devuelve lo que quedo anotado en la cache", "ES0903", ctx)
    t.contiene("trunca a cuatro lineas y avisa cuanto sobra", "1 mas en la zona cache", ctx)


def test_cuenta_definiciones_pendientes(t):
    proy = _proyecto_de_prueba(usuario="Ana", config_extra={"rutaDefinicionesPendientes": "PENDIENTES.md"})
    _escribir(proy / "PENDIENTES.md", "- [ ] uno\n- [x] hecho\n- [ ] dos\n")
    salida = json.loads(_correr("session-start.py", {"session_id": "s", "cwd": str(proy),
                                                     "hook_event_name": "SessionStart"}))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("cuenta solo las abiertas", "2 definiciones pendientes abiertas", ctx)


def test_no_inventa_contexto_de_otro_proyecto(t):
    """Lo que NO tiene que hacer: SessionStart solo puede leer lo que hay en ESE proyecto."""
    _proyecto_de_prueba(usuario="Ana Prueba")   # otro proyecto configurado, no el que se consulta
    proy_ajeno = _dir_vacio()
    salida = _correr_proceso("session-start.py", {"session_id": "s", "cwd": str(proy_ajeno),
                                                   "hook_event_name": "SessionStart"})
    t.igual("codigo 0", 0, salida.returncode)
    t.no_contiene("no menciona a nadie que no este configurado ahi",
                  "Ana Prueba", salida.stdout.decode("utf-8"))


# ── UserPromptSubmit: mudo, igual que hoy ────────────────────────────────────────

def test_user_prompt_submit_sale_mudo(t):
    """El ruteo por disparadores de skill es otro pendiente: hoy este hook calla siempre."""
    resultado = _correr_proceso("user-prompt-submit.py",
                                {"session_id": "s", "prompt": "che, arreglame el hook de secretos",
                                 "hook_event_name": "UserPromptSubmit"})
    t.igual("codigo 0", 0, resultado.returncode)
    t.igual("silencio", "", resultado.stdout.decode("utf-8"))


# ── PostToolUse: el caballo de batalla ───────────────────────────────────────────

def test_post_tool_use_reporta_hallazgos_de_los_checks(t):
    proy = _proyecto_de_prueba(usuario="Ana", config_extra={"techoZonaFija": 1})
    claude_md = proy / "CLAUDE.md"
    contenido = "# CLAUDE.md\n\n<!-- ZONA FIJA -->\n- una\n- dos\n- tres\n<!-- /ZONA FIJA -->\n"
    _escribir(claude_md, contenido)

    payload = {"session_id": "s", "cwd": str(proy), "hook_event_name": "PostToolUse",
               "tool_name": "Write",
               "tool_input": {"file_path": str(claude_md), "content": contenido}}
    salida = json.loads(_correr("post-tool-use.py", payload))
    ctx = salida["hookSpecificOutput"]["additionalContext"]
    t.contiene("reporta el exceso de la zona", "ZONA FIJA", ctx)
    t.contiene("cita el techo", "techo es 1", ctx)


def test_post_tool_use_sin_hallazgos_es_silencio(t):
    proy = _proyecto_de_prueba(usuario="Ana")
    payload = {"session_id": "s", "cwd": str(proy), "hook_event_name": "PostToolUse",
               "tool_name": "Write",
               "tool_input": {"file_path": str(proy / "a.ts"), "content": "const x = 1;"}}
    t.igual("silencio", "", _correr("post-tool-use.py", payload))


def test_post_tool_use_sin_cwd_es_silencio(t):
    resultado = _correr_proceso("post-tool-use.py",
                                {"session_id": "s", "hook_event_name": "PostToolUse",
                                 "tool_name": "Write",
                                 "tool_input": {"file_path": "a.ts", "content": "x"}})
    t.igual("codigo 0", 0, resultado.returncode)
    t.igual("silencio", "", resultado.stdout.decode("utf-8"))
