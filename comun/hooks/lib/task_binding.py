"""Que tarea trabaja una sesion: session-task-binding/1.0.

    .claude/runtime/sessions/<SAFE_SESSION_ID>/task.json
    {schema_version, sessionId, taskKey, source, updatedAt}

La identidad es el `session_id` que Claude Code le pasa a cada hook por stdin. No se inventa
otra: sin `session_id` no hay binding.

🔴 El binding lo crea una declaracion: una clave dicha en el prompt, o la de un comando del
Harness. Nada se infiere de la ultima tarea tocada ni de cual esta activa: con dos o mas
tareas y sin binding, la resolucion es SESSION_TASK_AMBIGUOUS y nadie elige por la persona.

No guarda el prompt, ni `tool_input`, ni un valor, ni el TaskContext, el plan o el estado del
flujo: solo la clave. Local, sin red, sin procesos.
"""
import hashlib
import io
import json
import os
import re
import uuid
from datetime import datetime

VERSION = "session-task-binding/1.0"
CAMPOS = ("schema_version", "sessionId", "source", "taskKey", "updatedAt")
FUENTES = ("user-prompt", "harness-command")

BOUND = "SESSION_TASK_BOUND"
UNRESOLVED = "SESSION_TASK_UNRESOLVED"
AMBIGUOUS = "SESSION_TASK_AMBIGUOUS"
STALE = "SESSION_TASK_STALE"
SESSION_ID_UNAVAILABLE = "SESSION_ID_UNAVAILABLE"

# La de flujo/estado.py: es el nombre de la carpeta de la tarea en runtime/tasks/.
CLAVE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")

# Un session_id que se usa tal cual como carpeta. En minusculas: NTFS no distingue mayusculas,
# y dos ids que solo difieren en eso caerian en la misma carpeta.
_SEGURA = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_RESERVADOS = re.compile(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?$")

_RUNTIME = (".claude", "runtime")


# -- la sesion -----------------------------------------------------------------

def sesion_segura(session_id):
    """El nombre de la carpeta de una sesion, o None si no hay sesion.

    Tal cual si es seguro en Windows. Si no, `_` + SHA-256: ningun id seguro empieza con `_`,
    asi que no hay colision, y el archivo guarda el original para poder verificarlo.
    """
    if not isinstance(session_id, str) or not session_id:
        return None
    if _SEGURA.match(session_id) and not session_id.endswith(".") \
            and not _RESERVADOS.match(session_id):
        return session_id
    return "_" + hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def raiz(cwd):
    """La raiz del proyecto: el primer directorio, de `cwd` hacia arriba, con runtime del flujo.

    Claude Code puede reportar un `cwd` que ya no es la raiz (despues de un `cd`). Si ninguno
    tiene `.claude/runtime/tasks` ni `.claude/runtime/sessions`, es el mismo `cwd`.
    """
    if not isinstance(cwd, str) or not cwd:
        return ""
    actual = os.path.abspath(cwd)
    while True:
        base = os.path.join(actual, *_RUNTIME)
        if os.path.isdir(os.path.join(base, "tasks")) or os.path.isdir(os.path.join(base, "sessions")):
            return actual
        arriba = os.path.dirname(actual)
        if arriba == actual:
            return os.path.abspath(cwd)
        actual = arriba


def ruta(proyecto, session_id):
    segura = sesion_segura(session_id)
    if segura is None:
        return None
    return os.path.join(proyecto, *(_RUNTIME + ("sessions", segura, "task.json")))


# -- las tareas del proyecto ---------------------------------------------------

def tareas(proyecto):
    """Las claves con `state.json` en runtime/tasks/, ordenadas. Un listado, no un recorrido."""
    carpeta = os.path.join(proyecto, *(_RUNTIME + ("tasks",)))
    try:
        nombres = os.listdir(carpeta)
    except OSError:
        return []
    return sorted(n for n in nombres
                  if CLAVE.match(n) and os.path.isfile(os.path.join(carpeta, n, "state.json")))


# -- leer y escribir -----------------------------------------------------------

def _valido(doc, session_id):
    return (isinstance(doc, dict) and tuple(sorted(doc)) == CAMPOS
            and doc.get("schema_version") == VERSION and doc.get("sessionId") == session_id
            and isinstance(doc.get("taskKey"), str) and bool(CLAVE.match(doc["taskKey"]))
            and doc.get("source") in FUENTES and isinstance(doc.get("updatedAt"), str))


def leer(proyecto, session_id):
    """(binding, None), (None, None) si no hay, o (None, SESSION_TASK_STALE) si no se puede creer.

    Ilegible, de otra version o con otro `sessionId` es STALE: no se usa ni se repara aca, y
    tampoco se cae a otra resolucion. Lo reemplaza la proxima declaracion.
    """
    archivo = ruta(proyecto, session_id)
    if archivo is None or not os.path.exists(archivo):
        return None, None
    try:
        with io.open(archivo, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None, STALE
    return (doc, None) if _valido(doc, session_id) else (None, STALE)


def _ahora():
    return datetime.now().replace(microsecond=0).isoformat()


def escribir_atomico(archivo, doc):
    """Temporal en la misma carpeta, flush, fsync y `os.replace`. Todo o nada."""
    carpeta = os.path.dirname(archivo)
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    temporal = os.path.join(carpeta, ".%s.%s.tmp" % (os.path.basename(archivo), uuid.uuid4().hex[:8]))
    try:
        with io.open(temporal, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, archivo)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise
    return archivo


def escribir(proyecto, session_id, clave, fuente):
    """Vincula la sesion a `clave`. None si no hay sesion. No reescribe un binding igual."""
    archivo = ruta(proyecto, session_id)
    if archivo is None or not CLAVE.match(str(clave or "")) or fuente not in FUENTES:
        return None
    actual, _ = leer(proyecto, session_id)
    if actual is not None and actual["taskKey"] == clave and actual["source"] == fuente:
        return actual
    doc = {"schema_version": VERSION, "sessionId": session_id, "taskKey": clave,
           "source": fuente, "updatedAt": _ahora()}
    escribir_atomico(archivo, doc)
    return doc


# -- la clave declarada en un prompt -------------------------------------------

_CODIGO = re.compile(r"```.*?(?:```|\Z)|`[^`\n]*`", re.S)
_CLAVE_EN_TEXTO = re.compile(r"(?<![A-Za-z0-9_/.#=-])[A-Za-z][A-Za-z0-9_]*-[0-9]+(?![A-Za-z0-9_/-])")
_VERBOS = (r"seguimos|sigamos|sigo|continuamos|continuemos|continu[aá]|continuo|retomamos|"
           r"retomemos|retom[aá]|trabajamos|trabajemos|trabajo|vamos|pasamos|pasemos|arrancamos|"
           r"arranquemos|empezamos|empecemos|cambiamos|cambiemos|working|work|continue|continuing|"
           r"resume|resuming|switch|switching|let'?s continue|let'?s work")
# Con un verbo de continuidad adelante, la clave puede seguir con texto («Vamos con ABC-1, arrancá
# por el login»). Sin verbo, la linea tiene que ser solo la clave, o `tarea`/`task` y la clave, y
# nada despues: «ABC-1 failed at line 3» o «task ABC-1 failed with ...» son un log, no una
# declaracion.
_DECLARA_CON_VERBO = re.compile(
    r"^\s*(?:%s)\s+(?:(?:con|en|a|on|with|to)\s+)?(?:(?:la\s+)?(?:tarea|task)\s+)?"
    r"(?P<clave>[A-Z][A-Z0-9_]*-[0-9]+)(?:[.,;:!?)]*\s|[.,;:!?)]*$)" % _VERBOS, re.I)
_DECLARA_SOLA = re.compile(
    r"^\s*(?:(?:la\s+)?(?:tarea|task|ticket|issue)\s*(?::|es|is)?\s*)?"
    r"(?P<clave>[A-Z][A-Z0-9_]*-[0-9]+)[.,;:!?)]*\s*$", re.I)


def clave_declarada(prompt):
    """La unica clave que el prompt declara, o None.

    Una linea declara si es solo la clave (o `tarea`/`task` y la clave), o si empieza con un verbo
    de continuidad y sigue la clave, en mayusculas. Afuera el codigo; una linea que nombra dos
    claves no declara; dos declaraciones distintas son ambiguas. Una clave en una URL, un JSON o
    un log no esta declarada.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    declaradas = set()
    for linea in _CODIGO.sub(" ", prompt).split("\n"):
        m = _DECLARA_CON_VERBO.match(linea) or _DECLARA_SOLA.match(linea)
        if not m or not re.match(r"^[A-Z][A-Z0-9_]*-[0-9]+$", m.group("clave")):
            continue
        if len(set(_CLAVE_EN_TEXTO.findall(linea))) != 1:
            continue
        declaradas.add(m.group("clave"))
    return declaradas.pop() if len(declaradas) == 1 else None


# -- la resolucion -------------------------------------------------------------

def resolver(proyecto, session_id, clave_del_comando=None):
    """Que tarea evaluar para esta sesion. Nunca lee el puntero a la tarea activa.

    {status, taskKey, via, candidates, sessionId}. `via` dice de donde salio la tarea:
    `harness-command` (la clave del comando, sobre cualquier binding: es la tarea que toca),
    `binding`, `single-candidate` (sin binding y una sola tarea con estado) o None.
    """
    candidatos = tareas(proyecto)
    salida = {"status": UNRESOLVED, "taskKey": None, "via": None, "candidates": candidatos,
              "sessionId": session_id if sesion_segura(session_id) else None}
    binding, error = leer(proyecto, session_id)
    if clave_del_comando and CLAVE.match(str(clave_del_comando)):
        if binding is None and error is None:
            binding = escribir(proyecto, session_id, clave_del_comando, "harness-command")
        salida.update(status=BOUND if binding is not None else UNRESOLVED,
                      taskKey=clave_del_comando, via="harness-command")
        return salida
    if error:
        salida.update(status=STALE)
        return salida
    if binding is not None:
        salida.update(status=BOUND, taskKey=binding["taskKey"], via="binding")
        return salida
    if len(candidatos) >= 2:
        salida.update(status=AMBIGUOUS)
    elif len(candidatos) == 1:
        salida.update(taskKey=candidatos[0], via="single-candidate")
    return salida
