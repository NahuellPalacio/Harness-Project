# Flow Governance, Wave 3: la sesion, su tarea y la compuerta del flujo en los hooks.
#
# Spec: docs/cambios/compuerta-del-flujo/spec.md. Cada test nombra su escenario E-nn, que es el
# W3-0nn de la Wave con el mismo numero; de E-49 en adelante los pidio el runtime. E-42 a E-48 son
# archivos de la suite y la compuerta entera.
#
# Se escribieron antes que lib/task_binding.py, lib/tool_policy.py, lib/flow_gate.py y
# lib/flow_context.py. Los modulos se importan adentro de cada test (`_TB()`, `_TP()`, `_FG()`,
# `_FC()`), para que el rojo inicial sea de cada escenario y no un solo error al cargar el archivo.
# Los hooks corren como proceso hijo, con el JSON del evento por stdin, igual que en Claude Code.
#
# Los estados se arman con la Wave 2 de verdad (`reconciliar`), sobre proyectos temporales con
# remotos que no existen. Los secretos son sinteticos y se arman por concatenacion.
import hashlib
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI_INSTALADO = "python .claude/harness/bin/desarrollo/dev-harness.py"

for _ruta in (str(BIN), str(HOOKS)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# Los proyectos, los TaskContexts y el .env de la Wave 2: una sola forma de armarlos.
W2 = _cargar("caso_62_para_63", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")

A, B, C = "ABC-123", "ABC-456", "ABC-789"
SECRETO = "ATATT3xFfGF0" + "w3w3w3w3w3w3w3w3w3w3"
SECRETO_ALTO = 'var cs = "Server=s;Pass' + 'word=Tr4ns4cc10n;";'
SECRETO_MEDIO = 'const api' + 'Key = "9f8e7d6c5b4a39281706f5e4d3c2b1a0";'


def _TB():
    return importlib.import_module("lib.task_binding")


def _TP():
    return importlib.import_module("lib.tool_policy")


def _FG():
    return importlib.import_module("lib.flow_gate")


def _FC():
    return importlib.import_module("lib.flow_context")


def _E():
    return importlib.import_module("flujo.estado")


def _P():
    return importlib.import_module("estado_de_tarea.persistencia")


def _sesion(nombre="s"):
    return "sesion-%s-%s" % (nombre, uuid.uuid4().hex[:8])


# -- los proyectos -------------------------------------------------------------

def _reconciliar(p, clave):
    return _P().reconciliar(str(p), clave, proceso={})


def _dos():
    """ABC-123 BLOCKED por REPOSITORY_MISMATCH y ABC-456 ACTIVE, en el mismo checkout.

    El remoto es repo-b: la ficha de ABC-123 dice repo-a y la de ABC-456 repo-b. El puntero queda
    en ABC-456, la ultima que se reconcilio.
    """
    p = W2._proyecto(remoto=W2.REPO_B + ".git")
    W2._contexto(p, A)
    W2._contexto(p, B, ficha="Repo: " + W2.REPO_B)
    _reconciliar(p, A)
    _reconciliar(p, B)
    return p


ENV_SIN_TOKEN = W2.ENV_COMPLETO.replace("JIRA_TOKEN=%s" % W2.TOKEN_JIRA, "JIRA_TOKEN=")


def _por_token(env=ENV_SIN_TOKEN):
    """ABC-123 en CONTEXT / BLOCKED, con `jira.token` pendiente en el .env."""
    p = W2._proyecto(env=env)
    _reconciliar(p, A)
    return p


def _linea_de(p, clave):
    for numero, linea in enumerate((p / ".env").read_text(encoding="utf-8").split("\n"), 1):
        if linea.startswith(clave + "="):
            return numero
    return None


# -- los hooks, como los corre Claude Code --------------------------------------

def _env():
    env = W2._entorno_limpio()
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def _evento(p, sesion, **campos):
    e = {"transcript_path": "C:\\x\\transcript.jsonl", "cwd": str(p)}
    if sesion is not None:
        e["session_id"] = sesion
    e.update(campos)
    return e


def _correr(hook, evento, hooks=HOOKS):
    return subprocess.run([sys.executable, str(Path(hooks) / (hook + ".py"))],
                          input=json.dumps(evento).encode("utf-8"), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=_env())


def _salida(r):
    texto = r.stdout.decode("utf-8")
    return json.loads(texto) if texto.strip() else None


def _una_emision(r):
    """True si stdout es vacio o exactamente un objeto JSON, sin nada atras."""
    texto = r.stdout.decode("utf-8")
    if not texto.strip():
        return True
    try:
        _, fin = json.JSONDecoder().raw_decode(texto)
    except ValueError:
        return False
    return texto[fin:].strip() == ""


def _pre_r(p, sesion, tool, entrada, hooks=HOOKS):
    return _correr("pre-tool-use", _evento(p, sesion, hook_event_name="PreToolUse",
                                           tool_name=tool, tool_input=entrada), hooks)


def _pre(p, sesion, tool, entrada):
    return _salida(_pre_r(p, sesion, tool, entrada))


def _prompt_r(p, sesion, texto):
    return _correr("user-prompt-submit", _evento(p, sesion, hook_event_name="UserPromptSubmit",
                                                 prompt=texto))


def _prompt(p, sesion, texto):
    return _salida(_prompt_r(p, sesion, texto))


def _start(p, sesion):
    return _salida(_correr("session-start", _evento(p, sesion, hook_event_name="SessionStart",
                                                    source="startup")))


def _decision(salida):
    return ((salida or {}).get("hookSpecificOutput") or {}).get("permissionDecision")


def _motivo(salida):
    return ((salida or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason") or ""


def _contexto(salida):
    return ((salida or {}).get("hookSpecificOutput") or {}).get("additionalContext") or ""


def _todo(salida):
    return json.dumps(salida or {}, ensure_ascii=False)


def _lineas_del_flujo(salida):
    return [l for l in _contexto(salida).split("\n") if l.startswith("Flujo")]


def _write(ruta="src/app.py", contenido="print('hola')\n"):
    return "Write", {"file_path": ruta, "content": contenido}


def _bash(comando):
    return "Bash", {"command": comando, "description": "x"}


def _ps(comando):
    return "PowerShell", {"command": comando}


def _harness(argumentos):
    return _bash("%s %s" % (CLI_INSTALADO, argumentos))


def _binding(p, sesion):
    ruta = p / ".claude" / "runtime" / "sessions" / sesion / "task.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def _vincular(p, sesion, clave):
    return _prompt(p, sesion, "Seguimos con %s" % clave)


def _decidir(p, sesion, tool, entrada):
    return _FG().decidir(_evento(p, sesion, hook_event_name="PreToolUse", tool_name=tool,
                                 tool_input=entrada))


def _borrar(*carpetas):
    for c in carpetas:
        shutil.rmtree(str(c), ignore_errors=True)


# -- el espia: sockets, procesos y modulos de un hook --------------------------

_ESPIA = r'''
import atexit, json, runpy, socket, subprocess, sys
registro = {"sockets": 0, "procesos": []}
class _SinRed(socket.socket):
    def __init__(self, *a, **k):
        registro["sockets"] += 1
        raise OSError("el hook abrio un socket")
socket.socket = _SinRed
def _conexion(*a, **k):
    registro["sockets"] += 1
    raise OSError("el hook abrio una conexion")
socket.create_connection = _conexion
_Popen = subprocess.Popen
class _Espiado(_Popen):
    def __init__(self, args, *a, **k):
        registro["procesos"].append(args if isinstance(args, str) else [str(x) for x in args])
        if __import__("os").environ.get("ESPIA_GIT_CUELGA") and not isinstance(args, str) \
                and str(args[0]) == "git":
            args = [sys.executable, "-c", "import subprocess, sys; subprocess.call([sys.executable, "
                    "'-c', 'import time; time.sleep(30)'])"]
        _Popen.__init__(self, args, *a, **k)
subprocess.Popen = _Espiado
import os as _os
registro["env"] = []
def _auditar(evento, argumentos):
    if evento == "open" and argumentos and isinstance(argumentos[0], (str, bytes)):
        nombre = _os.path.basename(_os.fsdecode(argumentos[0]))
        if nombre == ".env" or nombre.startswith(".env.") or nombre == "harness.integraciones.json":
            registro["env"].append(nombre)
sys.addaudithook(_auditar)
registro["resolver"] = 0
if _os.environ.get("ESPIA_BIN"):
    sys.path.insert(0, _os.environ["ESPIA_BIN"])
    from integraciones import entorno as _entorno
    _resolver = _entorno.resolver
    def _contado(*a, **k):
        registro["resolver"] += 1
        return _resolver(*a, **k)
    _entorno.resolver = _contado
PROHIBIDOS = ("http", "ssl", "anthropic", "openai", "requests")
EXACTOS = ("urllib.request", "integraciones.http", "integraciones.jira", "integraciones.gitlab")
def _fin():
    modulos = sorted(m for m in list(sys.modules)
                     if m.split(".")[0] in PROHIBIDOS or m in EXACTOS)
    registro["modulos"] = modulos
    registro["flujo"] = "flujo.estado" in sys.modules
    sys.stderr.write("\nESPIA " + json.dumps(registro) + "\n")
atexit.register(_fin)
hook = sys.argv[1]
sys.argv = [hook]
runpy.run_path(hook, run_name="__main__")
'''


def _solo_remote_v(procesos, p):
    """El unico proceso que puede correr un hook del flujo: `git -C <raiz> remote -v`, una vez."""
    return len(procesos) <= 1 and all(pr == ["git", "-C", str(p), "remote", "-v"] for pr in procesos)


def _espiar(hook, evento, git_cuelga=False):
    env = _env()
    env["ESPIA_BIN"] = str(BIN)
    if git_cuelga:
        env["ESPIA_GIT_CUELGA"] = "1"
    r = subprocess.run([sys.executable, "-c", _ESPIA, str(HOOKS / (hook + ".py"))],
                       input=json.dumps(evento).encode("utf-8"), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=env)
    error = r.stderr.decode("utf-8", "replace")
    m = re.search(r"ESPIA (\{.*\})", error)
    return r, (json.loads(m.group(1)) if m else {"sockets": -1, "procesos": ["sin espia"],
                                                "modulos": ["sin espia"], "flujo": None,
                                                "env": ["sin espia"], "resolver": -1})


# -- E-01 a E-07: el session_id y el binding ------------------------------------

def test_e01_session_start_lee_el_session_id(t):
    """E-01 — SessionStart con binding: la linea de continuidad nombra la tarea de ESA sesion."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        linea_a = " ".join(_lineas_del_flujo(_start(p, sa)))
        linea_b = " ".join(_lineas_del_flujo(_start(p, sb)))
        t.contiene("E-01 la sesion A ve ABC-123", A, linea_a)
        t.no_contiene("E-01 la sesion A no ve ABC-456", B, linea_a)
        t.contiene("E-01 la sesion B ve ABC-456", B, linea_b)
        t.no_contiene("E-01 la sesion B no ve ABC-123", A, linea_b)
    finally:
        _borrar(p)


def test_e02_user_prompt_submit_lee_el_session_id(t):
    """E-02 — el binding queda en la carpeta de la sesion del evento."""
    p = _dos()
    try:
        s = _sesion("e02")
        _vincular(p, s, A)
        doc = _binding(p, s)
        t.verdadero("E-02 hay binding en la carpeta de la sesion", doc is not None)
        t.igual("E-02 con su sessionId", s, (doc or {}).get("sessionId"))
        t.igual("E-02 y su tarea", A, (doc or {}).get("taskKey"))
        otras = [d.name for d in (p / ".claude" / "runtime" / "sessions").iterdir()] \
            if (p / ".claude" / "runtime" / "sessions").is_dir() else []
        t.igual("E-02 y ninguna otra carpeta de sesion", [s], otras)
    finally:
        _borrar(p)


def test_e03_pre_tool_use_lee_el_session_id(t):
    """E-03 — PreToolUse evalua la tarea del binding de la sesion del evento."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        de_a = _pre(p, sa, *_write())
        t.igual("E-03 la sesion A (ABC-123 BLOCKED) recibe deny", "deny", _decision(de_a))
        t.contiene("E-03 y el motivo nombra ABC-123", A, _motivo(de_a))
        t.igual("E-03 la sesion B (ABC-456 ACTIVE) pasa", None, _decision(_pre(p, sb, *_write())))
    finally:
        _borrar(p)


def test_e04_un_binding_es_estable(t):
    """E-04 — otro prompt sin clave no lo cambia; tres PreToolUse evaluan la misma tarea."""
    p = _dos()
    try:
        s = _sesion("e04")
        _vincular(p, s, A)
        ruta = p / ".claude" / "runtime" / "sessions" / s / "task.json"
        antes = ruta.read_bytes() if ruta.exists() else b""
        _prompt(p, s, "arreglá el test que falla")
        t.igual("E-04 el binding no cambio", antes, ruta.read_bytes() if ruta.exists() else None)
        for i in range(3):
            salida = _pre(p, s, *_write())
            t.igual("E-04 llamada %d deny" % i, "deny", _decision(salida))
            t.contiene("E-04 llamada %d nombra ABC-123" % i, A, _motivo(salida))
    finally:
        _borrar(p)


def test_e05_dos_sesiones_dos_tareas(t):
    """E-05 — dos sesiones vinculan dos tareas, cada una en su archivo."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        t.igual("E-05 A -> ABC-123", A, (_binding(p, sa) or {}).get("taskKey"))
        t.igual("E-05 B -> ABC-456", B, (_binding(p, sb) or {}).get("taskKey"))
    finally:
        _borrar(p)


def test_e06_active_task_no_pisa_otro_binding(t):
    """E-06 — mover el puntero no toca el binding de ninguna sesion."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        _P().marcar_activa(str(p), B)
        _reconciliar(p, B)
        t.igual("E-06 A sigue en ABC-123", A, (_binding(p, sa) or {}).get("taskKey"))
        salida = _pre(p, sa, *_write())
        t.igual("E-06 y PreToolUse de A evalua ABC-123", "deny", _decision(salida))
        t.contiene("E-06 nombrandola", A, _motivo(salida))
        _P().marcar_activa(str(p), A)
        t.igual("E-06 B sigue en ABC-456", B, (_binding(p, sb) or {}).get("taskKey"))
    finally:
        _borrar(p)


def test_e07_active_task_no_autoriza(t):
    """E-07 — con el puntero en la tarea activa, una sesion sin binding no escribe; y ningun
    modulo de PreToolUse nombra active-task."""
    p = _dos()
    try:
        _P().marcar_activa(str(p), B)
        salida = _pre(p, _sesion("e07"), *_write())
        t.igual("E-07 deny aunque el puntero este en ABC-456 ACTIVE", "deny", _decision(salida))
        t.contiene("E-07 por ambigua", "SESSION_TASK_AMBIGUOUS", _motivo(salida))
    finally:
        _borrar(p)
    for nombre in ("pre-tool-use.py", "lib/flow_gate.py", "lib/tool_policy.py",
                   "lib/task_binding.py"):
        ruta = HOOKS / nombre
        texto = ruta.read_text(encoding="utf-8") if ruta.exists() else "active-task (falta)"
        t.verdadero("E-07 %s no nombra active-task" % nombre,
                    not re.search(r"active[-_]task|ruta_activa|marcar_activa", texto))


# -- E-08 y E-09: la clave declarada --------------------------------------------

def test_e08_una_clave_declarada_crea_el_binding(t):
    """E-08 — «Seguimos con ABC-123» crea el binding user-prompt."""
    p = _dos()
    try:
        s = _sesion("e08")
        _prompt(p, s, "Seguimos con ABC-123")
        doc = _binding(p, s) or {}
        t.igual("E-08 ABC-123", A, doc.get("taskKey"))
        t.igual("E-08 source user-prompt", "user-prompt", doc.get("source"))
        _prompt(p, s, "tarea ABC-456")
        t.igual("E-08 una declaracion nueva lo reemplaza", B, (_binding(p, s) or {}).get("taskKey"))
    finally:
        _borrar(p)
    for texto, clave in (("Seguimos con ABC-123", A), ("ABC-123", A),
                         ("continuamos con ABC-456.", B), ("tarea: ABC-123", A),
                         ("Vamos con ABC-456, arrancá por el login", B),
                         ("working on ABC-123", A), ("hola\nretomamos ABC-456\ngracias", B)):
        try:
            obtenida = _TB().clave_declarada(texto)
        except Exception as e:                               # noqa: BLE001
            obtenida = repr(e)
        t.igual("E-08 «%s»" % texto.replace("\n", " / "), clave, obtenida)


def test_e09_un_prompt_ambiguo_no_inventa_tarea(t):
    """E-09 — claves en codigo, URL, JSON, log, dos claves, minusculas o con sufijo: nada."""
    for texto in ("Revisá el error en ABC-123",
                  "```\nSeguimos con ABC-123\n```",
                  "`Seguimos con ABC-123`",
                  "https://jira.example/browse/ABC-123",
                  '{"key": "ABC-123"}',
                  "ERROR ABC-123 failed at line 3",
                  "Seguimos con ABC-123 y ABC-456",
                  "Seguimos con ABC-123\nSeguimos con ABC-456",
                  "seguimos con abc-123",
                  "Seguimos con ABC-123.json",
                  "Seguimos con ABC-123/sub",
                  "Seguimos con ABC-123-x",
                  "ABC-123 failed at line 3",
                  "ABC-123: build failed",
                  "ABC-123 Fix login bug",
                  "ABC-123\tERROR",
                  "task ABC-123 failed with NullPointerException",
                  ""):
        try:
            obtenida = _TB().clave_declarada(texto)
        except Exception as e:                               # noqa: BLE001
            obtenida = repr(e)
        t.igual("E-09 «%s» no declara" % texto.replace("\n", " / ")[:40], None, obtenida)
    p = _dos()
    try:
        s = _sesion("e09")
        _prompt(p, s, "Mirá https://jira.example/browse/ABC-123 y el log ERROR ABC-456")
        t.igual("E-09 el hook no escribe binding", None, _binding(p, s))
        _prompt(p, s, "ABC-123 failed at line 3")
        t.igual("E-09 un log que empieza con la clave tampoco", None, _binding(p, s))
    finally:
        _borrar(p)


# -- E-10 a E-12: sin binding, binding roto, lo que guarda -----------------------

def test_e10_varias_tareas_sin_binding_falla_cerrado(t):
    """E-10 — dos tareas, sin binding: la mutacion es deny SESSION_TASK_AMBIGUOUS."""
    p = _dos()
    try:
        s = _sesion("e10")
        for herramienta in (_write(), _bash("rm -rf build")):
            salida = _pre(p, s, *herramienta)
            t.igual("E-10 %s deny" % herramienta[0], "deny", _decision(salida))
            t.contiene("E-10 %s SESSION_TASK_AMBIGUOUS" % herramienta[0],
                       "SESSION_TASK_AMBIGUOUS", _motivo(salida))
            t.contiene("E-10 %s nombra ABC-123" % herramienta[0], A, _motivo(salida))
            t.contiene("E-10 %s nombra ABC-456" % herramienta[0], B, _motivo(salida))
        t.igual("E-10 la lectura pasa", None, _decision(_pre(p, s, *_bash("git status"))))
        t.igual("E-10 y no se escribio binding", None, _binding(p, s))
    finally:
        _borrar(p)


def test_e11_un_binding_stale_falla_cerrado(t):
    """E-11 — roto, de otra version o de otro sessionId: SESSION_TASK_STALE, deny a mutar."""
    p = W2._proyecto(remoto=W2.REPO_B + ".git")
    W2._contexto(p, B, ficha="Repo: " + W2.REPO_B)
    _reconciliar(p, B)
    try:
        casos = {
            "roto": "{no es json",
            "version": json.dumps({"schema_version": "session-task-binding/0.9",
                                   "sessionId": "X", "taskKey": B, "source": "user-prompt",
                                   "updatedAt": "2026-09-30T10:00:00"}),
            "otra sesion": json.dumps({"schema_version": "session-task-binding/1.0",
                                       "sessionId": "sesion-otra", "taskKey": B,
                                       "source": "user-prompt",
                                       "updatedAt": "2026-09-30T10:00:00"}),
        }
        for rotulo, contenido in casos.items():
            s = _sesion("e11")
            contenido = contenido.replace('"X"', json.dumps(s))
            ruta = p / ".claude" / "runtime" / "sessions" / s / "task.json"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
            salida = _pre(p, s, *_write())
            t.igual("E-11 %s: deny aunque la unica tarea este ACTIVE" % rotulo, "deny",
                    _decision(salida))
            t.contiene("E-11 %s: SESSION_TASK_STALE" % rotulo, "SESSION_TASK_STALE",
                       _motivo(salida))
            t.igual("E-11 %s: la lectura pasa" % rotulo, None,
                    _decision(_pre(p, s, *_bash("git log --oneline -3"))))
    finally:
        _borrar(p)


def test_e12_el_binding_no_guarda_el_prompt(t):
    """E-12 — cinco campos; ni el prompt ni un secreto del prompt quedan en sessions/."""
    p = _dos()
    try:
        s = _sesion("e12")
        prompt = "Seguimos con ABC-123. Frase distintiva W3 y el token %s" % SECRETO
        _prompt(p, s, prompt)
        doc = _binding(p, s) or {}
        t.igual("E-12 exactamente sus cinco campos",
                ["schema_version", "sessionId", "source", "taskKey", "updatedAt"], sorted(doc))
        t.igual("E-12 session-task-binding/1.0", "session-task-binding/1.0",
                doc.get("schema_version"))
        todo = ""
        carpeta = p / ".claude" / "runtime" / "sessions"
        for archivo in (carpeta.rglob("*") if carpeta.is_dir() else []):
            if archivo.is_file():
                todo += archivo.read_text(encoding="utf-8", errors="replace")
        t.verdadero("E-12 hay algo que mirar", bool(todo))
        t.no_contiene("E-12 sin el prompt", "Frase distintiva W3", todo)
        t.no_contiene("E-12 sin el secreto", SECRETO, todo)
        errores = __import__("orquestacion.refutacion", fromlist=["x"]).validar(
            doc, "session-task-binding.schema.json") if doc else ["sin binding"]
        t.igual("E-12 valida contra su schema", [], errores)
    finally:
        _borrar(p)


# -- E-13 y E-14: SessionStart ---------------------------------------------------

def test_e13_session_start_continuidad_compacta(t):
    """E-13 — con binding a una tarea bloqueada, una linea: sin el enlace ni la explicacion."""
    p = _por_token()
    try:
        s = _sesion("e13")
        _vincular(p, s, A)
        salida = _start(p, s)
        lineas = _lineas_del_flujo(salida)
        t.igual("E-13 una sola linea del flujo", 1, len(lineas))
        linea = " ".join(lineas)
        t.contiene("E-13 nombra ABC-123", A, linea)
        t.contiene("E-13 nombra JIRA_TOKEN", "JIRA_TOKEN", linea)
        t.no_contiene("E-13 sin el enlace", "vscode://", _todo(salida))
        t.no_contiene("E-13 sin la instruccion", "Agregá o reemplazá", _todo(salida))
    finally:
        _borrar(p)


def test_e14_session_start_sin_binding_no_inventa(t):
    """E-14 — sin binding, la ultima tarea es una sugerencia; sin tareas, nada del flujo."""
    p = _dos()
    try:
        s = _sesion("e14")
        linea = " ".join(_lineas_del_flujo(_start(p, s)))
        t.contiene("E-14 sugiere la ultima tocada", B, linea)
        t.contiene("E-14 y dice que es una sugerencia", "sugerencia", linea)
        t.contiene("E-14 y que la sesion no tiene tarea", "sin tarea", linea)
        t.igual("E-14 no escribio binding", None, _binding(p, s))
    finally:
        _borrar(p)
    vacio = W2._proyecto()
    try:
        t.igual("E-14 sin tareas no dice nada del flujo", [],
                _lineas_del_flujo(_start(vacio, _sesion("e14v"))))
    finally:
        _borrar(vacio)


# -- E-15 a E-18: UserPromptSubmit -----------------------------------------------

def test_e15_user_prompt_submit_inyecta_el_bloqueo(t):
    """E-15 — con la tarea bloqueada, el contexto dice cual, por que y con que id."""
    p = _dos()
    try:
        salida = _vincular(p, _sesion("e15"), A)
        texto = _contexto(salida)
        t.contiene("E-15 nombra la tarea", A, texto)
        t.contiene("E-15 con el codigo", "REPOSITORY_MISMATCH", texto)
        t.contiene("E-15 con el id del bloqueo", "FLOW-PLANNING-001", texto)
        t.contiene("E-15 y donde ver el detalle", "flujo %s --status" % A, texto)
    finally:
        _borrar(p)


def test_e16_un_secreto_pendiente_sin_valor(t):
    """E-16 — URI, linea, placeholder y «No pegues»; ni un valor del .env."""
    p = _por_token()
    try:
        salida = _vincular(p, _sesion("e16"), A)
        todo = _todo(salida)
        linea = _linea_de(p, "JIRA_TOKEN")
        t.contiene("E-16 la URI de VS Code", "vscode://file/", todo)
        t.contiene("E-16 en la linea de JIRA_TOKEN", ".env:%s:1" % linea, todo)
        t.contiene("E-16 el placeholder", "JIRA_TOKEN=<jira-token>", todo)
        t.contiene("E-16 no pegues", "No pegues", todo)
        for valor in (W2.TOKEN_GITLAB, W2.USUARIO, W2.BASE):
            t.no_contiene("E-16 sin %s" % valor[:12], valor, todo)
        for prohibido in ('"value"', '"rawLine"', "password", "credential"):
            t.no_contiene("E-16 sin %s" % prohibido, prohibido, todo)
    finally:
        _borrar(p)


def test_e17_el_mismo_bloqueo_no_se_repite(t):
    """E-17 — el turno siguiente, con el mismo bloqueo: una linea, sin el enlace."""
    p = _por_token()
    try:
        s = _sesion("e17")
        primero = _vincular(p, s, A)
        segundo = _prompt(p, s, "dale, seguí")
        t.contiene("E-17 el primero trae el enlace", "vscode://file/", _todo(primero))
        texto = _contexto(segundo)
        t.contiene("E-17 el segundo recuerda la tarea", A, texto)
        t.igual("E-17 en una linea", 1, len([l for l in texto.split("\n") if l.strip()]))
        t.no_contiene("E-17 sin el enlace", "vscode://", _todo(segundo))
    finally:
        _borrar(p)


def test_e18_un_bloqueo_distinto_se_informa_entero(t):
    """E-18 — otra ubicacion del input, u otra tarea: el bloque entero otra vez."""
    p = _por_token()
    try:
        s = _sesion("e18")
        _vincular(p, s, A)
        _prompt(p, s, "dale")
        env = (p / ".env").read_text(encoding="utf-8")
        (p / ".env").write_text("# una linea nueva arriba\n# y otra\n" + env, encoding="utf-8")
        movido = _prompt(p, s, "listo, fijate")
        t.contiene("E-18 con el input en otra linea, el bloque entero", "vscode://file/",
                   _todo(movido))
        t.contiene("E-18 en la linea nueva", ".env:%s:1" % _linea_de(p, "JIRA_TOKEN"),
                   _todo(movido))
    finally:
        _borrar(p)
    p = _dos()
    try:
        s = _sesion("e18b")
        _vincular(p, s, A)
        _prompt(p, s, "dale")
        W2._contexto(p, C, ficha="Repo: " + W2.REPO_A)
        _reconciliar(p, C)
        otra = _prompt(p, s, "Seguimos con ABC-789")
        t.contiene("E-18 otra tarea bloqueada se informa entera", "FLOW-PLANNING-001",
                   _contexto(otra))
        t.contiene("E-18 nombrandola", C, _contexto(otra))
    finally:
        _borrar(p)


# -- E-19 y E-20: Secret Guard x Flow Gate ---------------------------------------

def test_e19_secreto_alto_gana(t):
    """E-19 — un secreto de confianza alta con la tarea bloqueada: deny del secreto."""
    p = _dos()
    try:
        s = _sesion("e19")
        _vincular(p, s, A)
        r = _pre_r(p, s, *_write("a.cs", SECRETO_ALTO))
        salida = _salida(r)
        t.igual("E-19 deny", "deny", _decision(salida))
        t.contiene("E-19 el motivo es el del secreto", "archivo externo al codigo", _motivo(salida))
        t.no_contiene("E-19 y no el del flujo", A, _motivo(salida))
        t.verdadero("E-19 una sola emision", _una_emision(r))
    finally:
        _borrar(p)


def test_e20_secreto_ambiguo(t):
    """E-20 — ambiguo con la tarea sana: ask; con la tarea bloqueada: deny, una emision."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        r = _pre_r(p, sb, *_write("a.ts", SECRETO_MEDIO))
        t.igual("E-20 sana: ask", "ask", _decision(_salida(r)))
        t.verdadero("E-20 sana: una emision", _una_emision(r))
        r = _pre_r(p, sa, *_write("a.ts", SECRETO_MEDIO))
        salida = _salida(r)
        t.igual("E-20 bloqueada: deny, nunca ask", "deny", _decision(salida))
        t.contiene("E-20 con el motivo del flujo", A, _motivo(salida))
        t.contiene("E-20 y el aviso del secreto", "variable de entorno", _motivo(salida))
        t.verdadero("E-20 bloqueada: una emision", _una_emision(r))
    finally:
        _borrar(p)


# -- E-21 a E-26: la clasificacion frente a una tarea bloqueada ------------------

def test_e21_bloqueada_y_mutacion(t):
    """E-21 — BLOCKED + Write, Edit, MultiEdit, NotebookEdit: deny."""
    p = _dos()
    try:
        s = _sesion("e21")
        _vincular(p, s, A)
        for tool, entrada in (_write(),
                              ("Edit", {"file_path": "a.py", "old_string": "a", "new_string": "b"}),
                              ("MultiEdit", {"file_path": "a.py",
                                             "edits": [{"old_string": "a", "new_string": "b"}]}),
                              ("NotebookEdit", {"notebook_path": "n.ipynb", "new_source": "x"})):
            salida = _pre(p, s, tool, entrada)
            t.igual("E-21 %s deny" % tool, "deny", _decision(salida))
            t.contiene("E-21 %s por el bloqueo" % tool, "REPOSITORY_MISMATCH", _motivo(salida))
    finally:
        _borrar(p)


def test_e22_bloqueada_y_avance(t):
    """E-22 — BLOCKED en PLANNING + refute --compile o la delegacion: deny."""
    p = _dos()
    try:
        s = _sesion("e22")
        _vincular(p, s, A)
        for tool, entrada in (_harness("refute %s --compile" % A),
                              _harness("refute %s --record veredicto.json" % A),
                              ("Task", {"description": "x", "prompt": "implementá",
                                        "subagent_type": "dev-backend"})):
            salida = _pre(p, s, tool, entrada)
            t.igual("E-22 %s deny" % entrada.get("command", tool)[-30:], "deny", _decision(salida))
        try:
            clase = _TP().clasificar("Task", {"prompt": "x"})["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.igual("E-22 Task es WORKFLOW_ADVANCING", "WORKFLOW_ADVANCING", clase)
    finally:
        _borrar(p)


def test_e23_bloqueada_y_lectura(t):
    """E-23 — BLOCKED + git status, ls, Get-Content, Read: pasa."""
    p = _dos()
    try:
        s = _sesion("e23")
        _vincular(p, s, A)
        for tool, entrada in (_bash("git status"), _bash("ls -la src"),
                              _bash("git log --oneline -5 | head -3"),
                              _bash("git diff --stat && git status --short"),
                              _ps("Get-Content README.md"), _ps("Get-ChildItem -Recurse src"),
                              ("Read", {"file_path": str(p / "README.md")}),
                              ("Grep", {"pattern": "x", "path": "src"}),
                              ("BashOutput", {"bash_id": "shell-1"}),
                              ("KillBash", {"shell_id": "shell-1"})):
            r = _pre_r(p, s, tool, entrada)
            t.igual("E-23 %s pasa" % entrada.get("command", tool), None, _decision(_salida(r)))
            t.igual("E-23 %s sale 0" % entrada.get("command", tool), 0, r.returncode)
    finally:
        _borrar(p)


def test_e24_bloqueada_y_recuperacion(t):
    """E-24 — BLOCKED + flujo --status o contexto: pasa."""
    p = _dos()
    try:
        s = _sesion("e24")
        _vincular(p, s, A)
        for tool, entrada in (_harness("flujo %s --status" % A),
                              _harness("flujo %s --status --json" % A),
                              _harness("contexto %s" % A),
                              _ps("& python .claude\\harness\\bin\\desarrollo\\dev-harness.py "
                                  "flujo %s --status" % A)):
            salida = _pre(p, s, tool, entrada)
            t.igual("E-24 %s pasa" % entrada["command"][-32:], None, _decision(salida))
        try:
            clase = _TP().clasificar(*_harness("flujo %s --status" % A))["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.igual("E-24 flujo --status es FLOW_RECOVERY", "FLOW_RECOVERY", clase)
    finally:
        _borrar(p)


def test_e25_lo_que_no_se_clasifica_falla_cerrado(t):
    """E-25 — npm install, curl, $(...), un script: FLOW_TOOL_CLASS_UNRESOLVED y deny."""
    p = _dos()
    try:
        s = _sesion("e25")
        _vincular(p, s, A)
        for comando in ("npm install", "curl https://example.invalid", "echo $(whoami)",
                        "python script.py", "git status; npm run build"):
            salida = _pre(p, s, *_bash(comando))
            t.igual("E-25 «%s» deny" % comando, "deny", _decision(salida))
            t.contiene("E-25 «%s» FLOW_TOOL_CLASS_UNRESOLVED" % comando,
                       "FLOW_TOOL_CLASS_UNRESOLVED", _motivo(salida))
        salida = _pre(p, s, *_bash("echo hola > salida.txt"))
        t.igual("E-25 una redireccion de escritura es deny", "deny", _decision(salida))
    finally:
        _borrar(p)
    casos = (("npm install", "UNRESOLVED_TOOL_CLASS"), ("echo hola > x.txt", "MUTATING"),
             ("rm -rf build", "MUTATING"), ("git commit -m x", "MUTATING"),
             ("mcp__x__y", None))
    for comando, esperada in casos:
        try:
            if comando.startswith("mcp__"):
                clase = _TP().clasificar(comando, {})["class"]
                esperada = "UNRESOLVED_TOOL_CLASS"
            else:
                clase = _TP().clasificar(*_bash(comando))["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.igual("E-25 «%s» es %s" % (comando, esperada), esperada, clase)


def test_e26_el_env_nunca_es_recuperacion(t):
    """E-26 — cat/Get-Content/type/head de un .env, o Read de un .env: nunca de lectura."""
    casos = (_bash("cat .env"), _bash("head -5 .env.local"), _bash("grep TOKEN .env"),
             _ps("Get-Content .env"), _ps("type .env"), _bash("cat ./config/.env | head"),
             _harness("flujo %s --status < .env" % A),
             ("Read", {"file_path": "C:\\Work\\app\\.env"}),
             ("Grep", {"pattern": "TOKEN", "path": ".env"}))
    for tool, entrada in casos:
        rotulo = entrada.get("command") or "%s %s" % (tool, entrada.get("file_path") or
                                                      entrada.get("path"))
        try:
            clase = _TP().clasificar(tool, entrada)["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.verdadero("E-26 «%s» no es lectura ni recuperacion (%s)" % (rotulo, clase),
                    clase not in ("READ_ONLY", "FLOW_RECOVERY") and clase.isupper())
    p = _dos()
    try:
        s = _sesion("e26")
        _vincular(p, s, A)
        for tool, entrada in (_bash("cat .env"), _ps("Get-Content .env")):
            t.igual("E-26 %s deny con la tarea bloqueada" % entrada["command"], "deny",
                    _decision(_pre(p, s, tool, entrada)))
    finally:
        _borrar(p)


# -- E-27 a E-32: sin red, sin modelo --------------------------------------------

def test_e27_a_e30_pre_tool_use_local(t):
    """E-27 a E-30 — PreToolUse no consulta Jira ni GitLab, no abre sockets, no carga un
    cliente de modelo ni corre procesos."""
    p = _dos()
    (p / ".claude" / "harness.integraciones.json").write_text("{}", encoding="utf-8")
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        for rotulo, sesion, herramienta, esperada in (
                ("bloqueada", sa, _write(), "deny"), ("sana", sb, _write(), None),
                ("comando", sa, _harness("plan %s --propuesta p.json" % A), None),
                ("ambigua", _sesion("c"), _write(), "deny")):
            r, espia = _espiar("pre-tool-use", _evento(p, sesion, hook_event_name="PreToolUse",
                                                        tool_name=herramienta[0],
                                                        tool_input=herramienta[1]))
            t.igual("E-27..30 %s: la decision" % rotulo, esperada, _decision(_salida(r)))
            t.igual("E-29 %s: sin sockets" % rotulo, 0, espia["sockets"])
            t.verdadero("E-28 %s: ningun proceso salvo un git remote -v local (%s)"
                        % (rotulo, espia["procesos"]), _solo_remote_v(espia["procesos"], p))
            t.verdadero("E-28 %s: hay un .env que se podria leer" % rotulo, (p / ".env").exists())
            t.igual("E-28 %s: no abre el .env ni harness.integraciones.json" % rotulo, [],
                    espia["env"])
            t.igual("E-28 %s: no resuelve el entorno, de donde sale la URL" % rotulo, 0,
                    espia["resolver"])
            t.igual("E-27/E-28/E-30 %s: sin Jira, GitLab, HTTP ni modelo" % rotulo, [],
                    espia["modulos"])
            t.verdadero("E-27..30 %s: el espia corrio" % rotulo, espia["flujo"] is not None)
    finally:
        _borrar(p)
    prohibido = re.compile(r"^\s*(?:import|from)\s+(anthropic|openai|requests|socket|http|"
                           r"urllib\.request|subprocess|integraciones)\b", re.M)
    for nombre in ("task_binding.py", "tool_policy.py", "flow_gate.py", "flow_context.py"):
        ruta = HOOKS / "lib" / nombre
        texto = ruta.read_text(encoding="utf-8") if ruta.exists() else "import socket"
        t.igual("E-30 lib/%s no importa red, procesos ni modelos" % nombre, [],
                prohibido.findall(texto))


def test_e31_user_prompt_submit_local(t):
    """E-31 — UserPromptSubmit con un bloqueo por secreto: sin red, procesos ni modelo."""
    p = _por_token()
    try:
        r, espia = _espiar("user-prompt-submit", _evento(p, _sesion("e31"),
                                                         hook_event_name="UserPromptSubmit",
                                                         prompt="Seguimos con ABC-123"))
        t.contiene("E-31 inyecto el bloqueo", "JIRA_TOKEN", _todo(_salida(r)))
        t.igual("E-31 sin sockets", 0, espia["sockets"])
        t.verdadero("E-31 ningun proceso salvo un git remote -v local (%s)" % espia["procesos"],
                    _solo_remote_v(espia["procesos"], p))
        t.igual("E-31 sin Jira, GitLab, HTTP ni modelo", [], espia["modulos"])
    finally:
        _borrar(p)


def test_e32_session_start_local(t):
    """E-32 — SessionStart: sin red ni modelo; git solo lo de siempre, nunca `remote`."""
    p = _dos()
    try:
        s = _sesion("e32")
        _vincular(p, s, A)
        r, espia = _espiar("session-start", _evento(p, s, hook_event_name="SessionStart",
                                                    source="startup"))
        t.contiene("E-32 dijo la continuidad", A, _todo(_salida(r)))
        t.igual("E-32 sin sockets", 0, espia["sockets"])
        t.igual("E-32 sin Jira, GitLab, HTTP ni modelo", [], espia["modulos"])
        t.verdadero("E-32 ningun git remote",
                    not any("remote" in (p_ if isinstance(p_, str) else " ".join(p_))
                            for p_ in espia["procesos"]))
    finally:
        _borrar(p)


# -- E-33 y E-34: la Wave 2 decide -----------------------------------------------

def test_e33_consume_vigencia_y_permisos(t):
    """E-33 — con vigencia y puede_avanzar cambiados en el proceso, cambia la decision."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        E = _E()
        try:
            t.igual("E-33 sin tocar, B pasa", "allow", _decidir(p, sb, *_write())["decision"])
            original = E.vigencia
            E.vigencia = lambda *a, **k: ["PLAN_STALE"]
            try:
                t.igual("E-33 con vigencia no vacia, B es deny", "deny",
                        _decidir(p, sb, *_write())["decision"])
            finally:
                E.vigencia = original
            original = E.puede_avanzar
            E.puede_avanzar = lambda *a, **k: True
            try:
                t.igual("E-33 con puede_avanzar verdadero, A pasa", "allow",
                        _decidir(p, sa, *_write())["decision"])
            finally:
                E.puede_avanzar = original
        except Exception as e:                               # noqa: BLE001
            t.verdadero("E-33 corre: %r" % e, False)
        doc = _E().leer(str(p), A)[0]
        E = _E()
        t.igual("E-33 permisos() sin tocar: ABC-123 no planifica", False,
                E.permisos(doc).get("planningAllowed"))
        original = E.puede_avanzar
        E.puede_avanzar = lambda *a, **k: True
        try:
            t.igual("E-33 permisos() usa puede_avanzar", True, E.permisos(doc).get("planningAllowed"))
        finally:
            E.puede_avanzar = original
    finally:
        _borrar(p)


def test_e34_un_estado_viejo_no_deja_mutar(t):
    """E-34 — plan reescrito (PLAN_STALE) o TaskContext cambiado (TASK_CONTEXT_STALE): deny."""
    p = W2._proyecto()
    try:
        doc = W2._listo(p, A)
        t.igual("E-34 la tarea esta en EXECUTION / ACTIVE", ["EXECUTION", "ACTIVE"],
                [(doc or {}).get("stage"), (doc or {}).get("status")])
        s = _sesion("e34")
        _vincular(p, s, A)
        t.igual("E-34 lista: el Write pasa", None, _decision(_pre(p, s, *_write())))
        ruta_plan = p / ".claude" / "planes" / (A + ".json")
        plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
        original = ruta_plan.read_bytes()
        plan["objective"] = "otro objetivo, reescrito a mano"
        ruta_plan.write_text(json.dumps(plan), encoding="utf-8")
        salida = _pre(p, s, *_write())
        t.igual("E-34 plan reescrito: deny", "deny", _decision(salida))
        t.contiene("E-34 con PLAN_STALE", "PLAN_STALE", _motivo(salida))
        ruta_plan.write_bytes(original)
        ruta_ctx = p / ".claude" / "contextos" / (A + ".json")
        ctx = json.loads(ruta_ctx.read_text(encoding="utf-8"))
        ctx["meta"]["context_hash"] = "sha256:" + "0" * 64
        ruta_ctx.write_text(json.dumps(ctx), encoding="utf-8")
        salida = _pre(p, s, *_write())
        t.igual("E-34 contexto cambiado: deny", "deny", _decision(salida))
        t.contiene("E-34 con TASK_CONTEXT_STALE", "TASK_CONTEXT_STALE", _motivo(salida))
    finally:
        _borrar(p)


# -- E-35 y E-36: concurrencia y una emision -------------------------------------

def test_e35_dos_sesiones_concurrentes(t):
    """E-35 — A -> ABC-123, B -> ABC-456; el puntero en una y en la otra no cambia nada."""
    p = _dos()
    try:
        sa, sb = "session-a-" + uuid.uuid4().hex[:6], "session-b-" + uuid.uuid4().hex[:6]
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        _P().marcar_activa(str(p), B)
        salida = _pre(p, sa, *_write())
        t.igual("E-35 puntero en ABC-456: A recibe deny", "deny", _decision(salida))
        t.contiene("E-35 y evalua ABC-123", A, _motivo(salida))
        t.no_contiene("E-35 nunca ABC-456", B, _motivo(salida))
        try:
            t.igual("E-35 decidir de A es ABC-123", A, _decidir(p, sa, *_write())["taskKey"])
        except Exception as e:                               # noqa: BLE001
            t.verdadero("E-35 decidir corre: %r" % e, False)
        _P().marcar_activa(str(p), A)
        t.igual("E-35 puntero en ABC-123: B pasa", None, _decision(_pre(p, sb, *_write())))
        try:
            t.igual("E-35 decidir de B es ABC-456", B, _decidir(p, sb, *_write())["taskKey"])
        except Exception as e:                               # noqa: BLE001
            t.verdadero("E-35 decidir corre: %r" % e, False)
        t.igual("E-35 los bindings no se pisaron", [A, B],
                [(_binding(p, sa) or {}).get("taskKey"), (_binding(p, sb) or {}).get("taskKey")])
    finally:
        _borrar(p)


def test_e36_una_sola_emision(t):
    """E-36 — cada combinacion emite a lo sumo un JSON."""
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        corridas = [_prompt_r(p, sa, "Seguimos con ABC-123"), _prompt_r(p, sb, "Seguimos con ABC-456"),
                    _prompt_r(p, sa, "dale")]
        for herramienta in (_write("a.cs", SECRETO_ALTO), _write("a.ts", SECRETO_MEDIO), _write(),
                            _bash("git status"), _bash("npm install")):
            corridas.append(_pre_r(p, sa, *herramienta))
            corridas.append(_pre_r(p, sb, *herramienta))
            corridas.append(_pre_r(p, _sesion("c"), *herramienta))
        for i, r in enumerate(corridas):
            t.verdadero("E-36 corrida %d: una emision" % i, _una_emision(r))
            t.igual("E-36 corrida %d: sale 0" % i, 0, r.returncode)
    finally:
        _borrar(p)


# -- E-37 a E-39 y E-57: los shells, las rutas, la instalacion -------------------

def _instalado():
    """Un proyecto en una ruta con espacios, con el harness como lo copia install.ps1."""
    p = W2._proyecto(remoto=W2.REPO_B + ".git")
    destino = Path(str(p) + " con espacios")
    shutil.move(str(p), str(destino))
    p = destino
    harness = p / ".claude" / "harness"
    ignorar = shutil.ignore_patterns("__pycache__")
    shutil.copytree(str(RAIZ / "comun" / "hooks"), str(harness / "hooks"), ignore=ignorar)
    shutil.copytree(str(RAIZ / "comun" / "reglas"), str(harness / "reglas"), ignore=ignorar)
    shutil.copytree(str(RAIZ / "comun" / "schemas"), str(harness / "schemas"), ignore=ignorar)
    shutil.copytree(str(RAIZ / "comun" / "bin"), str(harness / "bin"), ignore=ignorar)
    shutil.copytree(str(BIN), str(harness / "bin" / "desarrollo"), ignore=ignorar)
    shutil.copytree(str(RAIZ / "harnesses" / "desarrollo" / "reglas"),
                    str(harness / "reglas" / "desarrollo"), ignore=ignorar)
    shutil.copy(str(RAIZ / "comun" / "settings" / "run-hook.sh.plantilla"),
                str(harness / "run-hook.sh"))
    W2._contexto(p, A)
    W2._contexto(p, B, ficha="Repo: " + W2.REPO_B)
    _reconciliar(p, A)
    _reconciliar(p, B)
    return p


def _posix(ruta):
    ruta = str(ruta).replace("\\", "/")
    return "/" + ruta[0].lower() + ruta[2:] if re.match(r"^[A-Za-z]:", ruta) else ruta


def _bash_exe():
    for candidato in (r"C:\Program Files\Git\bin\bash.exe", shutil.which("bash") or ""):
        if candidato and os.path.isfile(candidato):
            return candidato
    return None


def test_e37_e38_e39_e57_shells_rutas_e_instalacion(t):
    """E-37 PowerShell, E-38 Git Bash, E-39 ruta con espacios, E-57 instalado."""
    p = _instalado()
    try:
        hooks = p / ".claude" / "harness" / "hooks"
        s = _sesion("e37")
        t.verdadero("E-39 la ruta tiene espacios", " " in str(p))
        vinculo = _salida(_correr("user-prompt-submit", _evento(
            p, s, hook_event_name="UserPromptSubmit", prompt="Seguimos con ABC-123"), hooks))
        t.igual("E-57 instalado: el binding se escribe", A, (_binding(p, s) or {}).get("taskKey"))
        t.contiene("E-57 instalado: el bloqueo se inyecta", "REPOSITORY_MISMATCH",
                   _contexto(vinculo))
        salida = _salida(_pre_r(p, s, *_write(), hooks=hooks))
        t.igual("E-57 instalado: deny", "deny", _decision(salida))
        t.contiene("E-57 instalado: por ABC-123", A, _motivo(salida))
        evento = json.dumps(_evento(p, s, hook_event_name="PreToolUse", tool_name="Write",
                                    tool_input=_write()[1])).encode("utf-8")
        powershell = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                  "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        comando = "& '%s' '%s'; exit $LASTEXITCODE" % (sys.executable,
                                                        str(hooks / "pre-tool-use.py"))
        codificado = __import__("base64").b64encode(comando.encode("utf-16-le")).decode("ascii")
        r = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand",
                            codificado], input=evento, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, env=_env())
        t.igual("E-37 PowerShell sale 0", 0, r.returncode)
        t.igual("E-37 PowerShell: deny", "deny", _decision(_salida(r)))
        bash = _bash_exe()
        t.verdadero("E-38 hay Git Bash", bash is not None)
        if bash:
            envoltorio = Path(tempfile.mkdtemp(prefix="harness-w3-py-"))
            (envoltorio / "python3").write_bytes(
                ('#!/bin/sh\nexec "%s" "$@"\n' % _posix(sys.executable)).encode("utf-8"))
            script = 'PATH="%s:$PATH" exec sh "%s" pre-tool-use' % (
                _posix(envoltorio), _posix(p / ".claude" / "harness" / "run-hook.sh"))
            r = subprocess.run([bash, "-c", script], input=evento, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=_env())
            _borrar(envoltorio)
            t.igual("E-38 Git Bash sale 0", 0, r.returncode)
            t.igual("E-38 Git Bash: deny", "deny", _decision(_salida(r)))
        # E-39 — la URI de un .env en una ruta con espacios sale codificada.
        (p / ".env").write_text(ENV_SIN_TOKEN, encoding="utf-8")
        W2._borrar(p / ".claude" / "contextos")
        _reconciliar(p, C)
        s2 = _sesion("e39")
        texto = _todo(_salida(_correr("user-prompt-submit", _evento(
            p, s2, hook_event_name="UserPromptSubmit", prompt="Seguimos con ABC-789"), hooks)))
        uri = re.search(r"vscode://file/[^\s\"\\]+", texto)
        t.verdadero("E-39 hay URI", uri is not None)
        t.contiene("E-39 con los espacios codificados", "%20con%20espacios",
                   uri.group(0) if uri else "")
        t.no_contiene("E-39 sin espacios crudos", " ", uri.group(0) if uri else " ")
    finally:
        _borrar(p)


# -- E-40 y E-41: la Context Bar -------------------------------------------------

def test_e40_la_context_bar_sigue_siendo_la_statusline(t):
    """E-40 — el registro de hooks no la toca y los hooks del flujo no escriben su senal."""
    plantilla = json.loads((RAIZ / "comun" / "settings" / "hooks.plantilla.json").read_text(
        encoding="utf-8"))
    t.verdadero("E-40 la plantilla de hooks no trae statusLine", "statusLine" not in plantilla)
    t.igual("E-40 el matcher de PostToolUse no cambio",
            "Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell",
            plantilla["hooks"]["PostToolUse"][0]["matcher"])
    p = _dos()
    try:
        s = _sesion("e40")
        _vincular(p, s, A)
        _pre(p, s, *_write())
        _prompt(p, s, "dale")
        t.verdadero("E-40 ningun hook del flujo escribio la senal de la barra",
                    not (p / ".claude" / "runtime" / "contextbar.json").exists())
    finally:
        _borrar(p)
    for nombre in ("task_binding.py", "tool_policy.py", "flow_gate.py", "flow_context.py"):
        ruta = HOOKS / "lib" / nombre
        texto = ruta.read_text(encoding="utf-8") if ruta.exists() else "contextbar"
        t.verdadero("E-40 lib/%s no toca la Context Bar" % nombre,
                    "contextbar" not in texto.lower() and "statusline" not in texto.lower())


def test_e41_e25_de_la_context_bar_queda_acotado(t):
    """E-41 — un enlace vscode:// no afirma nada; decir que la barra se ve en VS Code, si."""
    try:
        cb = _cargar("caso_53_para_63", RAIZ / "tests" / "casos" / "53_context_bar.py")
        menciona = cb._menciona_vscode
    except Exception as e:                                   # noqa: BLE001
        t.verdadero("E-41 53_context_bar tiene _menciona_vscode: %r" % e, False)
        return
    t.verdadero("E-41 un enlace solo no cuenta",
                not menciona("Abrí:\n\n    vscode://file/C:/Work/app/.env:3:1"))
    t.verdadero("E-41 el identificador vscodeUri no cuenta",
                not menciona("La salida trae `vscodeUri` y `fallback`."))
    t.verdadero("E-41 nombrar VS Code sigue contando",
                menciona("La Context Bar se ve también en la barra de estado de VS Code."))
    t.verdadero("E-41 nombrar VS Code junto a un enlace sigue contando",
                menciona("Se abre en VS Code con vscode://file/C:/x:1:1"))
    t.verdadero("E-41 VSCode junto sigue contando", menciona("Integración nativa con VSCode."))


# -- E-49 a E-58: lo que pidio el runtime ----------------------------------------

def test_e49_sin_session_id(t):
    """E-49 — sin session_id no hay binding, y con dos tareas la mutacion es deny."""
    p = _dos()
    try:
        _prompt(p, None, "Seguimos con ABC-123")
        _prompt(p, "", "Seguimos con ABC-123")
        t.verdadero("E-49 no se escribio ninguna sesion",
                    not (p / ".claude" / "runtime" / "sessions").exists())
        salida = _pre(p, None, *_write())
        t.igual("E-49 deny", "deny", _decision(salida))
        t.contiene("E-49 ambigua", "SESSION_TASK_AMBIGUOUS", _motivo(salida))
    finally:
        _borrar(p)


def test_e50_un_session_id_inseguro(t):
    """E-50 — `_<sha256>`; dos que difieren en mayusculas no comparten carpeta; es trazable."""
    try:
        seguro = _TB().sesion_segura
        for sid in ("sesion-abc", "0f8c2a1e-5b7d-4c3a-9e2f-1a2b3c4d5e6f"):
            t.igual("E-50 «%s» queda igual" % sid, sid, seguro(sid))
        for sid in ("Sesion-ABC", "con", "nul.txt", "COM1", "a.", "../x", "a b", "x" * 200):
            t.igual("E-50 «%s» va a _sha256" % sid[:20],
                    "_" + hashlib.sha256(sid.encode("utf-8")).hexdigest(), seguro(sid))
        t.verdadero("E-50 Sesion-ABC y sesion-abc no comparten carpeta",
                    seguro("Sesion-ABC").lower() != seguro("sesion-abc").lower())
        t.igual("E-50 vacio no es una sesion", None, seguro(""))
        t.igual("E-50 None no es una sesion", None, seguro(None))
    except Exception as e:                                   # noqa: BLE001
        t.verdadero("E-50 sesion_segura corre: %r" % e, False)
    p = _dos()
    try:
        sid = "Sesion-Insegura/../X"
        _prompt(p, sid, "Seguimos con ABC-456")
        carpeta = p / ".claude" / "runtime" / "sessions" / (
            "_" + hashlib.sha256(sid.encode("utf-8")).hexdigest())
        doc = json.loads((carpeta / "task.json").read_text(encoding="utf-8")) \
            if (carpeta / "task.json").exists() else {}
        t.igual("E-50 el archivo guarda el session_id original", sid, doc.get("sessionId"))
        t.igual("E-50 y PreToolUse lo lee: ABC-456 pasa", None, _decision(_pre(p, sid, *_write())))
    finally:
        _borrar(p)


def test_e51_revalidar_la_etapa_bloqueada(t):
    """E-51 — BLOCKED en PLANNING + plan pasa; BLOCKED en CONTEXT + plan es deny."""
    p = _dos()
    try:
        s = _sesion("e51")
        _vincular(p, s, A)
        t.igual("E-51 PLANNING + plan pasa (revalida)", None,
                _decision(_pre(p, s, *_harness("plan %s --propuesta p.json" % A))))
        t.igual("E-51 PLANNING + refute --compile es deny", "deny",
                _decision(_pre(p, s, *_harness("refute %s --compile" % A))))
    finally:
        _borrar(p)
    p = _por_token()
    try:
        s = _sesion("e51b")
        _vincular(p, s, A)
        salida = _pre(p, s, *_harness("plan %s --propuesta p.json" % A))
        t.igual("E-51 CONTEXT + plan es deny", "deny", _decision(salida))
        t.igual("E-51 CONTEXT + contexto pasa", None,
                _decision(_pre(p, s, *_harness("contexto %s" % A))))
    finally:
        _borrar(p)


def test_e52_esperando_una_aprobacion_no_revalida(t):
    """E-52 — WAITING_FOR_HUMAN_APPROVAL + plan: deny, sin excepcion."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A)
        doc = _reconciliar(p, A)
        bloqueo = {"inputId": "plan.humanApprovals", "code": "HUMAN_APPROVAL_PENDING",
                   "classification": "HARD_BLOCKER", "interactionType": "HUMAN_DECISION",
                   "source": "orchestration-plan", "stage": "PLANNING",
                   "blockerId": "FLOW-PLANNING-001",
                   "resumeFrom": {"stage": "PLANNING", "gate": "plan-human-approvals"}}
        doc.update({"status": "WAITING_FOR_HUMAN_APPROVAL", "stage": "PLANNING",
                    "blockedOn": [bloqueo], "resumeFrom": dict(bloqueo["resumeFrom"]),
                    "pendingHumanInteraction": {"kind": "HUMAN_DECISION",
                                                "inputId": "plan.humanApprovals"}})
        _P().escribir(str(p), A, doc)
        s = _sesion("e52")
        _vincular(p, s, A)
        salida = _pre(p, s, *_harness("plan %s --propuesta p.json" % A))
        t.igual("E-52 plan es deny", "deny", _decision(salida))
        t.contiene("E-52 por la aprobacion", "HUMAN_APPROVAL_PENDING", _motivo(salida))
        t.igual("E-52 Write es deny", "deny", _decision(_pre(p, s, *_write())))
        t.igual("E-52 flujo --status pasa", None,
                _decision(_pre(p, s, *_harness("flujo %s --status" % A))))
    finally:
        _borrar(p)


def test_e53_un_comando_con_clave_evalua_su_clave(t):
    """E-53 — refute ABC-123 desde una sesion de ABC-456 evalua ABC-123; y vincula si no habia."""
    p = _dos()
    try:
        s = _sesion("e53")
        _vincular(p, s, B)
        salida = _pre(p, s, *_harness("refute %s --compile" % A))
        t.igual("E-53 deny por ABC-123", "deny", _decision(salida))
        t.contiene("E-53 nombrandola", A, _motivo(salida))
        t.igual("E-53 el binding no cambio", B, (_binding(p, s) or {}).get("taskKey"))
        nueva = _sesion("e53n")
        t.igual("E-53 flujo --status pasa", None,
                _decision(_pre(p, nueva, *_harness("flujo %s --status" % B))))
        doc = _binding(p, nueva) or {}
        t.igual("E-53 y vincula la sesion nueva", [B, "harness-command"],
                [doc.get("taskKey"), doc.get("source")])
        t.igual("E-53 despues el Write pasa (ABC-456 ACTIVE)", None,
                _decision(_pre(p, nueva, *_write())))
    finally:
        _borrar(p)


def test_e54_un_fallo_de_la_compuerta_falla_cerrado(t):
    """E-54 — con estado.leer roto: deny FLOW_GATE_UNRESOLVED a mutar; la lectura pasa."""
    p = _dos()
    try:
        s = _sesion("e54")
        _vincular(p, s, B)
        E = _E()
        original = E.leer

        def _roto(*_a, **_k):
            raise RuntimeError("fallo interno sintetico")
        E.leer = _roto
        try:
            try:
                escritura = _decidir(p, s, *_write())
                lectura = _decidir(p, s, *_bash("git status"))
            except Exception as e:                           # noqa: BLE001
                escritura, lectura = {"decision": repr(e)}, {"decision": repr(e)}
        finally:
            E.leer = original
        t.igual("E-54 Write: deny", "deny", escritura.get("decision"))
        t.igual("E-54 FLOW_GATE_UNRESOLVED", "FLOW_GATE_UNRESOLVED", escritura.get("code"))
        t.igual("E-54 git status: pasa", "allow", lectura.get("decision"))
    finally:
        _borrar(p)
    p = _instalado()
    try:
        W2._borrar(p / ".claude" / "harness" / "bin" / "desarrollo")
        hooks = p / ".claude" / "harness" / "hooks"
        s = _sesion("e54i")
        _correr("user-prompt-submit", _evento(p, s, hook_event_name="UserPromptSubmit",
                                              prompt="Seguimos con ABC-456"), hooks)
        salida = _salida(_pre_r(p, s, *_write(), hooks=hooks))
        t.igual("E-54 sin flujo/ instalado y con tareas: deny", "deny", _decision(salida))
        t.contiene("E-54 FLOW_GATE_UNRESOLVED instalado", "FLOW_GATE_UNRESOLVED", _motivo(salida))
    finally:
        _borrar(p)


def test_e55_sin_flujo_nada_cambia(t):
    """E-55 — sin estado del flujo, PreToolUse calla y no carga flujo/."""
    p = W2._proyecto()
    try:
        s = _sesion("e55")
        for herramienta in (_write(), _bash("npm install"), _bash("rm -rf build")):
            r, espia = _espiar("pre-tool-use", _evento(p, s, hook_event_name="PreToolUse",
                                                        tool_name=herramienta[0],
                                                        tool_input=herramienta[1]))
            t.igual("E-55 %s: silencio" % herramienta[0], "", r.stdout.decode("utf-8"))
            t.igual("E-55 %s: sale 0" % herramienta[0], 0, r.returncode)
            t.igual("E-55 %s: no carga flujo/" % herramienta[0], False, espia["flujo"])
        t.verdadero("E-55 no crea runtime/sessions",
                    not (p / ".claude" / "runtime" / "sessions").exists())
    finally:
        _borrar(p)


def test_e56_una_tarea_vinculada_sin_estado(t):
    """E-56 — sin state.json: deny TASK_FLOW_STATE_MISSING; contexto pasa."""
    p = _dos()
    try:
        s = _sesion("e56")
        _vincular(p, s, C)
        salida = _pre(p, s, *_write())
        t.igual("E-56 deny", "deny", _decision(salida))
        t.contiene("E-56 TASK_FLOW_STATE_MISSING", "TASK_FLOW_STATE_MISSING", _motivo(salida))
        t.contiene("E-56 dice como salir", "contexto %s" % C, _motivo(salida))
        t.igual("E-56 contexto pasa", None, _decision(_pre(p, s, *_harness("contexto %s" % C))))
    finally:
        _borrar(p)


def test_e58_cwd_en_una_subcarpeta(t):
    """E-58 — con cwd en src/, el hook encuentra la raiz del runtime."""
    p = _dos()
    try:
        s = _sesion("e58")
        _vincular(p, s, A)
        (p / "src" / "modulo").mkdir(parents=True)
        salida = _pre(p / "src" / "modulo", s, *_write())
        t.igual("E-58 deny desde la subcarpeta", "deny", _decision(salida))
        t.contiene("E-58 por ABC-123", A, _motivo(salida))
    finally:
        _borrar(p)


# -- E-59 a E-62: lo que encontro la verificacion --------------------------------

def test_e59_un_binding_sin_estado_del_flujo_no_gobierna(t):
    """E-59 — sin ningun state.json en el proyecto, un binding no traba nada: ni con desarrollo
    ni sin el."""
    p = W2._proyecto()
    try:
        s = _sesion("e59")
        salida = _vincular(p, s, A)
        t.igual("E-59 el binding se escribe igual", A, (_binding(p, s) or {}).get("taskKey"))
        t.igual("E-59 UserPromptSubmit calla", None, salida)
        t.igual("E-59 el Write pasa", None, _decision(_pre(p, s, *_write())))
        t.igual("E-59 SessionStart no dice nada del flujo", [], _lineas_del_flujo(_start(p, s)))
    finally:
        _borrar(p)
    p = _instalado()
    try:
        W2._borrar(p / ".claude" / "harness" / "bin" / "desarrollo", p / ".claude" / "runtime" / "tasks")
        hooks = p / ".claude" / "harness" / "hooks"
        s = _sesion("e59i")
        dicho = _salida(_correr("user-prompt-submit", _evento(
            p, s, hook_event_name="UserPromptSubmit", prompt="Seguimos con ABC-123"), hooks))
        t.igual("E-59 sin desarrollo ni estado: UserPromptSubmit calla", None, dicho)
        inicio = _salida(_correr("session-start", _evento(
            p, s, hook_event_name="SessionStart", source="startup"), hooks))
        t.igual("E-59 sin desarrollo ni estado: SessionStart no dice nada del flujo", [],
                _lineas_del_flujo(inicio))
        r = _pre_r(p, s, *_write(), hooks=hooks)
        t.igual("E-59 sin desarrollo ni estado: el Write pasa", None, _decision(_salida(r)))
        t.igual("E-59 y sale 0", 0, r.returncode)
    finally:
        _borrar(p)


def test_e60_refute_record_no_revalida(t):
    """E-60 — BLOCKED en REFUTATION: --record no tiene compuerta propia y es deny; --compile pasa."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A)
        doc = _reconciliar(p, A)
        bloqueo = {"inputId": "refutation.compile", "code": "REFUTATION_PLAN_STALE",
                   "classification": "DERIVABLE", "interactionType": None,
                   "source": "atomic-refutation", "stage": "REFUTATION",
                   "blockerId": "FLOW-REFUTATION-001",
                   "resumeFrom": {"stage": "REFUTATION", "gate": "refutation-compile"}}
        doc.update({"status": "BLOCKED", "stage": "REFUTATION", "blockedOn": [bloqueo],
                    "resumeFrom": dict(bloqueo["resumeFrom"]), "pendingHumanInteraction": None})
        _P().escribir(str(p), A, doc)
        s = _sesion("e60")
        _vincular(p, s, A)
        t.igual("E-60 --record es deny", "deny",
                _decision(_pre(p, s, *_harness("refute %s --record v.json" % A))))
        t.igual("E-60 --unit es deny", "deny",
                _decision(_pre(p, s, *_harness("refute %s --unit REF-001" % A))))
        t.igual("E-60 --compile pasa (revalida con su compuerta)", None,
                _decision(_pre(p, s, *_harness("refute %s --compile" % A))))
    finally:
        _borrar(p)


def test_e61_el_secret_guard_no_depende_del_flujo(t):
    """E-61 — sin lib/tool_policy.py: el secreto alto sigue siendo deny; con tareas, la mutacion es
    FLOW_GATE_UNRESOLVED; sin tareas, silencio y salida 0."""
    copia = Path(tempfile.mkdtemp(prefix="harness-w3-a-medias-"))
    try:
        shutil.copytree(str(HOOKS), str(copia / "hooks"), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(str(RAIZ / "comun" / "reglas"), str(copia / "reglas"))
        (copia / "hooks" / "lib" / "tool_policy.py").unlink()
        hooks = copia / "hooks"
        p = _dos()
        vacio = W2._proyecto()
        try:
            s = _sesion("e61")
            r = _pre_r(vacio, s, *_write("a.cs", SECRETO_ALTO), hooks=hooks)
            t.igual("E-61 secreto alto: deny", "deny", _decision(_salida(r)))
            t.igual("E-61 secreto alto: sale 0", 0, r.returncode)
            r = _pre_r(p, s, *_write(), hooks=hooks)
            t.igual("E-61 con tareas: deny", "deny", _decision(_salida(r)))
            t.contiene("E-61 FLOW_GATE_UNRESOLVED", "FLOW_GATE_UNRESOLVED", _motivo(_salida(r)))
            (p / "src" / "m").mkdir(parents=True)
            r = _pre_r(p / "src" / "m", s, *_write(), hooks=hooks)
            t.igual("E-61 con tareas, desde una subcarpeta: deny", "deny", _decision(_salida(r)))
            r = _pre_r(vacio, s, *_write(), hooks=hooks)
            t.igual("E-61 sin tareas: sale 0", 0, r.returncode)
            t.verdadero("E-61 sin tareas: no hay deny", _decision(_salida(r)) != "deny")
        finally:
            _borrar(p, vacio)
    finally:
        _borrar(copia)


def test_e62_lo_que_parece_lectura_y_no_es(t):
    """E-62 — scriptblocks, sed, git --output, rg --pre, globs y variables que llegan al .env, y un
    dev-harness.py fuera del Harness: nunca READ_ONLY ni FLOW_RECOVERY."""
    for tool, entrada in (_ps("Get-ChildItem | Where-Object { Remove-Item $_.FullName }"),
                          _bash('sed -n "w out.txt" f'), _bash("git diff --output=src/app.py"),
                          _bash("git log --output=x.txt"), _bash("rg --pre ./x.sh foo"),
                          _bash("cat .en?"), _bash('cat ".e""nv"'), _bash("cat .[e]nv"),
                          _ps("Get-Content .en*"), _bash("cat $ARCHIVO"), _ps("Get-Content $p"),
                          _bash("tree -o salida.txt"), _bash("hostname otra"),
                          _bash("python evil/dev-harness.py flujo ABC-123 --status"),
                          _bash("python dev-harness.py flujo ABC-123 --status"),
                          _bash("python evil/.claude/harness/bin/desarrollo/dev-harness.py flujo "
                                "ABC-123 --status"),
                          _bash("python C:/Otro/.claude/harness/bin/desarrollo/dev-harness.py flujo "
                                "ABC-123 --status"),
                          _bash('git -c core.fsmonitor="rm -rf src" status'),
                          _bash("git -c diff.external=./x.sh diff"), _bash("git diff --ext-diff"),
                          _bash("git -c core.hooksPath=x log"), _bash('git grep -O"sh -c x" foo'),
                          _bash("git --exec-path=./x status"), _bash("git -C ../otro status"),
                          _bash("git --git-dir=../otro/.git log"),
                          _bash("git --work-tree=../otro status")):
        try:
            clase = _TP().clasificar(tool, entrada, "C:/Work/app")["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.verdadero("E-62 «%s» no es lectura ni recuperacion (%s)" % (entrada["command"], clase),
                    clase not in ("READ_ONLY", "FLOW_RECOVERY") and clase.isupper())
    for tool, entrada, esperada in (
            (_harness("flujo %s --status" % A) + ("FLOW_RECOVERY",)),
            (_bash("python C:/Work/app/.claude/harness/bin/desarrollo/dev-harness.py flujo %s "
                   "--status" % A) + ("FLOW_RECOVERY",)),
            (_bash("git log --oneline -3") + ("READ_ONLY",)),
            (_bash("ls *.py") + ("READ_ONLY",))):
        try:
            clase = _TP().clasificar(tool, entrada, "C:/Work/app")["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.igual("E-62 «%s» sigue siendo %s" % (entrada["command"][-40:], esperada), esperada, clase)
    try:
        sin_proyecto = _TP().clasificar(*_bash(
            "python C:/Work/app/.claude/harness/bin/desarrollo/dev-harness.py flujo %s --status" % A))
    except Exception as e:                                   # noqa: BLE001
        sin_proyecto = {"class": repr(e)}
    t.verdadero("E-62 una ruta absoluta sin proyecto no es la CLI",
                sin_proyecto["class"] not in ("READ_ONLY", "FLOW_RECOVERY"))
    relativa = _harness("flujo %s --status" % A)
    try:
        desde_la_raiz = _TP().clasificar(*relativa, proyecto="C:/Work/app", cwd="C:/Work/app")
        desde_src = _TP().clasificar(*relativa, proyecto="C:/Work/app", cwd="C:/Work/app/src")
    except Exception as e:                                   # noqa: BLE001
        desde_la_raiz = desde_src = {"class": repr(e)}
    t.igual("E-62 la CLI relativa desde la raiz es la CLI", "FLOW_RECOVERY", desde_la_raiz["class"])
    t.verdadero("E-62 la CLI relativa desde una subcarpeta no es la CLI (%s)" % desde_src["class"],
                desde_src["class"] not in ("READ_ONLY", "FLOW_RECOVERY"))
    p = _dos()
    try:
        s = _sesion("e62")
        _vincular(p, s, A)
        falso = p / "src" / ".claude" / "harness" / "bin" / "desarrollo" / "dev-harness.py"
        falso.parent.mkdir(parents=True)
        falso.write_text("print('no soy el harness')\n", encoding="utf-8")
        salida = _pre(p / "src", s, *relativa)
        t.igual("E-62 por el hook, desde src/ con un dev-harness.py falso: deny", "deny",
                _decision(salida))
        t.igual("E-62 desde la raiz, la CLI de verdad pasa", None, _decision(_pre(p, s, *relativa)))
    finally:
        _borrar(p)


# -- E-63: el remoto cambiado sin reconciliar ------------------------------------

def test_e63_un_remoto_cambiado_sin_reconciliar_no_deja_mutar(t):
    """E-63 — ACTIVE con el repositorio MATCHED; se cambia solo el remoto, sin correr contexto,
    plan ni refute: Write y Edit son deny REPOSITORY_STATE_STALE, sin reconciliar el estado."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A)
        doc = _reconciliar(p, A)
        t.igual("E-63 la tarea arranca ACTIVE", "ACTIVE", doc.get("status"))
        t.igual("E-63 con el repositorio MATCHED", "MATCHED", (doc.get("repositoryRef") or {}).get("status"))
        s = _sesion("e63")
        _vincular(p, s, A)
        t.igual("E-63 con el remoto igual, el Write pasa", None, _decision(_pre(p, s, *_write())))
        estado = p / ".claude" / "runtime" / "tasks" / A / "state.json"
        antes = estado.read_bytes()
        W2._git(p, "remote", "set-url", "origin", W2.REPO_B + ".git")
        for tool, entrada in (_write(),
                              ("Edit", {"file_path": "a.py", "old_string": "a", "new_string": "b"}),
                              ("Task", {"description": "x", "prompt": "y", "subagent_type": "z"})):
            salida = _pre(p, s, tool, entrada)
            t.igual("E-63 %s con el remoto cambiado: deny" % tool, "deny", _decision(salida))
            t.contiene("E-63 %s por REPOSITORY_STATE_STALE" % tool, "REPOSITORY_STATE_STALE",
                       _motivo(salida))
        t.igual("E-63 el estado guardado no se reconcilio", antes, estado.read_bytes())
        t.igual("E-63 la lectura sigue pasando", None, _decision(_pre(p, s, *_bash("git status"))))
        t.igual("E-63 plan revalida (reconcilia)", None,
                _decision(_pre(p, s, *_harness("plan %s --propuesta p.json" % A))))
        W2._git(p, "remote", "set-url", "origin", W2.REPO_A + ".git")
        t.igual("E-63 con el remoto de vuelta, el Write pasa", None, _decision(_pre(p, s, *_write())))
        W2._git(p, "remote", "remove", "origin")
        t.igual("E-63 sin remoto: deny", "deny", _decision(_pre(p, s, *_write())))
    finally:
        _borrar(p)


# -- E-64: la delegacion pasa por la compuerta ------------------------------------

_DELEGAR = {"description": "x", "prompt": "implementá la unidad", "subagent_type": "dev-backend"}


def _matchea(matcher, herramienta):
    """Como Claude Code: una regex sin anclar contra el nombre de la herramienta."""
    return re.search(matcher, herramienta) is not None


def test_e64_la_delegacion_pasa_por_la_compuerta(t):
    """E-64 — el matcher registrado de PreToolUse alcanza a Agent y a Task (y a nada mas con ese
    nombre); con la tarea BLOCKED, AMBIGUOUS o desactualizada, delegar es deny; ACTIVE, pasa; un
    secreto alto en el pedido sigue siendo deny del secreto."""
    plantilla = json.loads((RAIZ / "comun" / "settings" / "hooks.plantilla.json").read_text(
        encoding="utf-8"))
    matchers = [g["matcher"] for g in plantilla["hooks"]["PreToolUse"]]
    for herramienta in ("Agent", "Task"):
        t.verdadero("E-64 PreToolUse alcanza a %s" % herramienta,
                    any(_matchea(m, herramienta) for m in matchers))
    for herramienta in ("Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "PowerShell"):
        t.verdadero("E-64 y sigue alcanzando a %s" % herramienta,
                    any(_matchea(m, herramienta) for m in matchers))
    for herramienta in ("TaskCreate", "TaskUpdate", "TaskOutput", "TaskStop", "AgentOutput",
                        "Read", "Glob", "Grep"):
        t.verdadero("E-64 no alcanza a %s" % herramienta,
                    not any(_matchea(m, herramienta) for m in matchers))
    p = _dos()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        for herramienta in ("Agent", "Task"):
            t.igual("E-64 BLOCKED + %s: deny" % herramienta, "deny",
                    _decision(_pre(p, sa, herramienta, _DELEGAR)))
            t.igual("E-64 ACTIVE + %s: pasa" % herramienta, None,
                    _decision(_pre(p, sb, herramienta, _DELEGAR)))
            salida = _pre(p, _sesion("c"), herramienta, _DELEGAR)
            t.igual("E-64 AMBIGUOUS + %s: deny" % herramienta, "deny", _decision(salida))
            t.contiene("E-64 AMBIGUOUS + %s: el codigo" % herramienta, "SESSION_TASK_AMBIGUOUS",
                       _motivo(salida))
        salida = _pre(p, sa, "Agent", dict(_DELEGAR, prompt="usá " + SECRETO_ALTO))
        t.igual("E-64 secreto alto en el pedido: deny", "deny", _decision(salida))
        t.contiene("E-64 y es el del secreto", "archivo externo al codigo", _motivo(salida))
        ruta_ctx = p / ".claude" / "contextos" / (B + ".json")
        ctx = json.loads(ruta_ctx.read_text(encoding="utf-8"))
        ctx["meta"]["context_hash"] = "sha256:" + "1" * 64
        ruta_ctx.write_text(json.dumps(ctx), encoding="utf-8")
        salida = _pre(p, sb, "Agent", _DELEGAR)
        t.igual("E-64 desactualizada + Agent: deny", "deny", _decision(salida))
        t.contiene("E-64 con TASK_CONTEXT_STALE", "TASK_CONTEXT_STALE", _motivo(salida))
    finally:
        _borrar(p)
    try:
        clase = _TP().clasificar("Agent", _DELEGAR)["class"]
    except Exception as e:                                   # noqa: BLE001
        clase = repr(e)
    t.igual("E-64 Agent es WORKFLOW_ADVANCING", "WORKFLOW_ADVANCING", clase)


# -- E-65: `git remote -v` colgado no deja pasar nada ---------------------------

def test_e65_git_colgado_falla_cerrado_y_rapido(t):
    """E-65 — la compuerta corre `git remote -v` con su propio timeout, corto y explicito
    (flow_gate.TIMEOUT_REMOTOS), y el resolver de la CLI sigue con el suyo. Vencido: deny
    FLOW_GATE_UNRESOLVED para Write y Agent, tambien sin remotos guardados; nunca allow; sin red
    ni .env; la lectura no corre git."""
    import time
    FG = _FG()
    limite = getattr(FG, "TIMEOUT_REMOTOS", None)
    t.verdadero("E-65 la compuerta declara su timeout (%r)" % limite,
                isinstance(limite, (int, float)) and 0 < limite < 10)
    repo = importlib.import_module("flujo.repositorio")
    import inspect
    t.igual("E-65 el resolver de la CLI conserva 10 s", 10,
            inspect.signature(repo.remotos).parameters.get("timeout").default
            if "timeout" in inspect.signature(repo.remotos).parameters else None)
    p = _dos()
    sin_remoto = W2._proyecto(remoto=None)
    try:
        sa, sb = _sesion("a"), _sesion("b")
        _vincular(p, sa, A)
        _vincular(p, sb, B)
        # A. normal: la compuerta pasa su timeout y el estado vigente sigue pasando
        vistos = []
        original_remotos = repo.remotos

        def _mira(*a, **k):
            vistos.append((k.get("timeout"), k.get("estricto")))
            return original_remotos(*a, **k)
        repo.remotos = _mira
        try:
            normal = _decidir(p, sb, *_write())
        finally:
            repo.remotos = original_remotos
        t.igual("E-65 A: con git normal, ABC-456 pasa", "allow", normal["decision"])
        t.igual("E-65 A: con el timeout de la compuerta, estricto", [(limite, True)], vistos)
        # B, C, F. colgado como el lanzador de Git para Windows: el proceso que se lanza deja un
        # nieto dormido con los pipes heredados. Matar solo al hijo no alcanza.
        original = repo.subprocess.Popen
        lanzador = [sys.executable, "-c", "import subprocess, sys; subprocess.call([sys.executable, "
                    "'-c', 'import time; time.sleep(30)'])"]

        class _Colgado(original):
            def __init__(self, argumentos, *a, **k):
                if not isinstance(argumentos, str) and str(argumentos[0]) == "git":
                    argumentos = lanzador
                original.__init__(self, argumentos, *a, **k)
        repo.subprocess.Popen = _Colgado
        try:
            inicio = time.time()
            colgado_write = _decidir(p, sb, *_write())
            demora = time.time() - inicio
            colgado_agent = _decidir(p, sb, "Agent", {"prompt": "x", "subagent_type": "y"})
            lectura = _decidir(p, sb, *_bash("git status"))
        finally:
            repo.subprocess.Popen = original
        t.igual("E-65 B: Write con git colgado: deny", "deny", colgado_write["decision"])
        t.igual("E-65 B: FLOW_GATE_UNRESOLVED", "FLOW_GATE_UNRESOLVED", colgado_write.get("code"))
        t.verdadero("E-65 B: corta en el timeout, no en 10 s (%.1f s)" % demora,
                    limite is not None and demora < limite + 1.5)
        t.igual("E-65 F: Agent con git colgado: deny", "deny", colgado_agent["decision"])
        t.igual("E-65 lectura con git colgado: pasa, no lo corre", "allow", lectura["decision"])
        # C. sin remotos guardados: vencido no es lo mismo que vacio
        guardado = _reconciliar(sin_remoto, A)
        t.igual("E-65 C: la tarea sin remoto esta en CONTEXT / NEW, sin bloqueos",
                ["CONTEXT", "NEW", []], [guardado["stage"], guardado["status"],
                                         (guardado.get("repositoryRef") or {}).get("localRepositories")])
        sc = _sesion("c")
        _vincular(sin_remoto, sc, A)
        repo.subprocess.Popen = _Colgado
        try:
            vacio = _decidir(sin_remoto, sc, *_write())
        finally:
            repo.subprocess.Popen = original
        t.igual("E-65 C: sin remotos guardados y git colgado: nunca allow", "deny", vacio["decision"])
        # D, E. por el hook, con el espia colgando git: sin red, sin .env, deny y rapido
        inicio = time.time()
        r, espia = _espiar("pre-tool-use", _evento(p, sb, hook_event_name="PreToolUse",
                                                    tool_name="Write", tool_input=_write()[1]),
                           git_cuelga=True)
        demora = time.time() - inicio
        salida = _salida(r)
        t.igual("E-65 hook: deny", "deny", _decision(salida))
        t.contiene("E-65 hook: FLOW_GATE_UNRESOLVED", "FLOW_GATE_UNRESOLVED", _motivo(salida))
        t.igual("E-65 D: sin sockets", 0, espia["sockets"])
        # E-28 en el camino colgado: git remote -v, y a lo sumo el taskkill de ese arbol.
        otros = [pr for pr in espia["procesos"] if pr != ["git", "-C", str(p), "remote", "-v"]]
        t.igual("E-65 / E-28 colgado: git remote -v una vez", 1,
                espia["procesos"].count(["git", "-C", str(p), "remote", "-v"]))
        t.verdadero("E-65 / E-28 colgado: el unico otro proceso es el taskkill del arbol (%s)" % otros,
                    all(isinstance(pr, list) and pr[:4] == ["taskkill", "/F", "/T", "/PID"]
                        and len(pr) == 5 for pr in otros) and len(otros) <= 1)
        # E-31 en el camino colgado: UserPromptSubmit sale 0, calla, y corre lo mismo.
        r, espia = _espiar("user-prompt-submit", _evento(p, sa, hook_event_name="UserPromptSubmit",
                                                         prompt="dale"), git_cuelga=True)
        otros = [pr for pr in espia["procesos"] if pr != ["git", "-C", str(p), "remote", "-v"]]
        t.igual("E-65 / E-31 colgado: UserPromptSubmit sale 0", 0, r.returncode)
        t.igual("E-65 / E-31 colgado: git remote -v una vez", 1,
                espia["procesos"].count(["git", "-C", str(p), "remote", "-v"]))
        t.verdadero("E-65 / E-31 colgado: el unico otro proceso es el taskkill del arbol (%s)" % otros,
                    all(isinstance(pr, list) and pr[:4] == ["taskkill", "/F", "/T", "/PID"]
                        and len(pr) == 5 for pr in otros) and len(otros) <= 1)
        t.igual("E-65 / E-31 colgado: sin sockets", 0, espia["sockets"])
        t.igual("E-65 / E-31 colgado: sin .env", [], espia["env"])
        t.igual("E-65 E: sin .env", [], espia["env"])
        t.verdadero("E-65 hook: termina en el timeout (%.1f s)" % demora,
                    limite is not None and demora < limite + 3)
    finally:
        _borrar(p, sin_remoto)
