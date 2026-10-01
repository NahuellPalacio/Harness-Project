"""La intencion de una persona: human-intent/1.0. Solo la escribe UserPromptSubmit.

    analizar(prompt)            el comando HARNESS del prompt, o None
    registrar(evento)           UserPromptSubmit: valida contra las interacciones abiertas y escribe
    verificar(...)              si hay un intent sin consumir que coincide; None o el codigo
    consumir(proyecto, sesion)  consumedAt, una sola vez

    .claude/runtime/sessions/<SAFE_SESSION_ID>/human-intent.json

🔴 model tool call != human approval. UserPromptSubmit es el unico evento que prueba que un texto
lo escribio la persona. Un comando que aplica una decision solo consume lo que la persona dejo
aca, para esa sesion, esa tarea, esa interaccion, esa accion y ese estado.

🔴 Una linea exacta, en mayusculas. «dale», «ok», «sí» o un comando adentro de un parrafo no son una
intencion: no se interpreta lenguaje natural para una aprobacion.

No guarda el prompt, ni un token, ni una linea del `.env`. Local, sin red, sin procesos.
"""
import io
import json
import os
import re

from . import task_binding

VERSION = "human-intent/1.0"
CAMPOS = ("action", "consumedAt", "createdAt", "inputId", "interactionId", "optionId",
          "planFingerprint", "schema_version", "sessionId", "stateFingerprint", "taskKey", "value")

APPROVE, USE_ALTERNATIVE, CHOOSE, CANCEL, ANSWER, RESUME = (
    "APPROVE", "USE_ALTERNATIVE", "CHOOSE", "CANCEL", "ANSWER", "RESUME")
_VERBO = {"APPROVE": APPROVE, "ALTERNATIVE": USE_ALTERNATIVE, "CHOOSE": CHOOSE,
          "CANCEL": CANCEL, "ANSWER": ANSWER, "RESUME": RESUME}
# (lleva interactionId, lleva opcion)
_ARIDAD = {APPROVE: (True, False), USE_ALTERNATIVE: (True, True), CHOOSE: (True, True),
           CANCEL: (True, False), ANSWER: (True, True), RESUME: (False, False)}
_FLAG = {APPROVE: "--approve", USE_ALTERNATIVE: "--alternative", CHOOSE: "--choose",
         CANCEL: "--cancel", ANSWER: "--answer"}

_COMANDO = re.compile(r"^HARNESS (APPROVE|ALTERNATIVE|CHOOSE|CANCEL|ANSWER|RESUME) "
                      r"([A-Z][A-Z0-9_]*-[0-9]+)(?: (ixn-[0-9a-f]{16}))?(?: (\S{1,200}))?$")

REQUIRED = "HUMAN_INTENT_REQUIRED"
CONSUMED = "HUMAN_INTENT_ALREADY_CONSUMED"
SESSION_MISMATCH = "HUMAN_INTENT_SESSION_MISMATCH"
TASK_MISMATCH = "HUMAN_INTENT_TASK_MISMATCH"
MISMATCH = "HUMAN_INTENT_MISMATCH"
NOT_OPEN = "HUMAN_INTERACTION_NOT_OPEN"
ACTION_INVALID = "HUMAN_ACTION_INVALID"
OPTION_INVALID = "HUMAN_OPTION_INVALID"
ANSWER_NOT_ACCEPTED = "HUMAN_ANSWER_NOT_ACCEPTED"
ANSWER_SECRET = "HUMAN_ANSWER_SECRET"

CLI = "python .claude/harness/bin/desarrollo/dev-harness.py"
_CANDADO_VIEJO = 60


# -- la gramatica ----------------------------------------------------------------

def analizar(prompt):
    """{action, taskKey, interactionId, option} si el prompt es exactamente un comando HARNESS."""
    if not isinstance(prompt, str):
        return None
    m = _COMANDO.match(prompt.strip())
    if not m:
        return None
    accion = _VERBO[m.group(1)]
    con_id, con_opcion = _ARIDAD[accion]
    if bool(m.group(3)) != con_id or bool(m.group(4)) != con_opcion:
        return None
    return {"action": accion, "taskKey": m.group(2), "interactionId": m.group(3),
            "option": m.group(4)}


# -- el archivo ------------------------------------------------------------------

def ruta(proyecto, sesion):
    archivo = task_binding.ruta(proyecto, sesion)
    return os.path.join(os.path.dirname(archivo), "human-intent.json") if archivo else None


def _valido(doc, sesion):
    return (isinstance(doc, dict) and tuple(sorted(doc)) == CAMPOS
            and doc.get("schema_version") == VERSION and doc.get("sessionId") == sesion
            and doc.get("action") in _ARIDAD and isinstance(doc.get("taskKey"), str))


def leer(proyecto, sesion):
    archivo = ruta(proyecto, sesion)
    if archivo is None or not os.path.isfile(archivo):
        return None
    try:
        with io.open(archivo, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if _valido(doc, sesion) else None


def _escribir(proyecto, sesion, doc):
    task_binding.escribir_atomico(ruta(proyecto, sesion), doc)


def consumir(proyecto, sesion):
    """consumedAt, una sola vez aunque dos procesos lo intenten a la vez: el que no consigue el
    candado exclusivo lo da por consumido."""
    archivo = ruta(proyecto, sesion)
    if archivo is None:
        return None
    candado = archivo + ".lock"
    try:
        fd = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        # Un candado de mas de un minuto es de un proceso que murio a la mitad: se reclama una vez.
        try:
            import time
            if time.time() - os.path.getmtime(candado) <= _CANDADO_VIEJO:
                return None
            os.remove(candado)
            fd = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            return None
    try:
        doc = leer(proyecto, sesion)
        if doc is None or doc.get("consumedAt"):
            return None
        doc["consumedAt"] = task_binding._ahora()
        _escribir(proyecto, sesion, doc)
        return doc
    finally:
        os.close(fd)
        try:
            os.remove(candado)
        except OSError:
            pass


def _en_otra_sesion(proyecto, clave, interaction_id, sesion):
    carpeta = os.path.join(proyecto, ".claude", "runtime", "sessions")
    try:
        nombres = os.listdir(carpeta)
    except OSError:
        return False
    propia = task_binding.sesion_segura(sesion)
    for nombre in nombres:
        if nombre == propia:
            continue
        try:
            with io.open(os.path.join(carpeta, nombre, "human-intent.json"), encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("taskKey") == clave and \
                doc.get("interactionId") == interaction_id and not doc.get("consumedAt"):
            return True
    return False


def verificar(proyecto, sesion, clave, accion, interaction_id, opcion=None):
    """None si hay, en ESTA sesion, un intent sin consumir que coincide con el comando; si no, el
    codigo. No mira si sigue vigente contra el estado: eso lo hace quien aplica."""
    doc = leer(proyecto, sesion) if task_binding.sesion_segura(sesion) else None
    if doc is None:
        return SESSION_MISMATCH if _en_otra_sesion(proyecto, clave, interaction_id, sesion) \
            else REQUIRED
    if doc.get("consumedAt"):
        return CONSUMED
    if doc.get("taskKey") != clave:
        return TASK_MISMATCH
    esperado = doc.get("optionId") if accion in (USE_ALTERNATIVE, CHOOSE) else \
        doc.get("value") if accion == ANSWER else None
    if doc.get("interactionId") != interaction_id or doc.get("action") != accion or \
            (esperado or None) != (opcion or None):
        return MISMATCH
    return None


def comando_de_aplicacion(intent, sesion):
    """La linea que el modelo tiene que correr para aplicar la intencion. Nunca con un valor."""
    partes = [CLI, "flujo", intent["taskKey"], _FLAG[intent["action"]], intent["interactionId"]]
    if intent["action"] in (USE_ALTERNATIVE, CHOOSE):
        partes += ["--option", intent["optionId"]]
    if intent["action"] == ANSWER:
        partes += ["--value", "<el valor que escribiste>"]
    return " ".join(partes + ["--sesion", sesion])


# -- UserPromptSubmit ------------------------------------------------------------

def _parece_secreto(valor):
    try:
        from .secretos import importar_patrones, buscar_secreto
        catalogo = importar_patrones(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "..", "reglas", "secretos.patrones.json"))
        if buscar_secreto(valor, catalogo) is not None:
            return True
    except Exception:                                  # noqa: BLE001 - ante la duda, secreto
        return True
    # Un valor largo, sin espacios y con letras y digitos mezclados tiene forma de token.
    return len(valor) >= 20 and bool(re.search(r"[A-Za-z]", valor)) and bool(re.search(r"\d", valor))


def _abiertas_texto(abiertas):
    return ", ".join(i["interactionId"] for i in abiertas) or "ninguna"


def registrar(proyecto, sesion, prompt, estado, interaccion):
    """(para el modelo, para la persona) si el prompt es un comando HARNESS; None si no.

    `estado` y `interaccion` son flujo.estado y flujo.interaccion de este harness.
    """
    cmd = analizar(prompt)
    if cmd is None:
        return None
    clave, accion = cmd["taskKey"], cmd["action"]
    if not task_binding.sesion_segura(sesion):
        texto = ("Flujo · sin session_id no se registra una intención [%s]." % REQUIRED)
        return texto, texto
    task_binding.escribir(proyecto, sesion, clave, "user-prompt")
    if accion == RESUME:
        texto = ("Flujo · retomar %s: corré `%s flujo %s --resume`. Revalida desde las fuentes; si "
                 "algo sigue faltando, la tarea sigue bloqueada y lo vuelve a mostrar." % (
                     clave, CLI, clave))
        return texto, texto
    abiertas = interaccion.interacciones(proyecto, clave)
    abierta = interaccion.buscar(abiertas, cmd["interactionId"])

    def _rechazo(codigo, porque):
        texto = ("Flujo · no se registró la intención [%s]: %s No se aplica nada." % (codigo, porque))
        return texto, texto

    if abierta is None:
        return _rechazo(NOT_OPEN, "%s no es una interacción abierta de %s (abiertas: %s)." % (
            cmd["interactionId"], clave, _abiertas_texto(abiertas)))
    if accion not in abierta["actions"]:
        if accion == ANSWER:
            return _rechazo(ANSWER_NOT_ACCEPTED, "%s no se resuelve con un valor: %s. Corregilo en "
                            "su fuente y escribí `HARNESS RESUME %s`." % (
                                abierta["inputId"], "editá el archivo del enlace"
                                if abierta["kind"] == "PERSISTENT_CONFIG_INPUT"
                                else "se arregla en el checkout", clave))
        return _rechazo(ACTION_INVALID, "%s acepta %s." % (abierta["interactionId"],
                                                           ", ".join(abierta["actions"])))
    if accion in (USE_ALTERNATIVE, CHOOSE) and cmd["option"] not in abierta["options"]:
        return _rechazo(OPTION_INVALID, "las opciones de %s son %s." % (
            abierta["interactionId"], ", ".join(abierta["options"]) or "ninguna"))
    if accion == ANSWER and (abierta.get("sensitivity") == "SECRET" or _parece_secreto(cmd["option"])):
        return _rechazo(ANSWER_SECRET, "el valor tiene forma de secreto y no se acepta por el chat.")
    guardado, _ = estado.leer(proyecto, clave)
    plan = interaccion._plan(proyecto, clave)
    doc = {"schema_version": VERSION, "sessionId": sesion, "taskKey": clave,
           "interactionId": abierta["interactionId"], "action": accion,
           "inputId": abierta["inputId"],
           "optionId": cmd["option"] if accion in (USE_ALTERNATIVE, CHOOSE) else None,
           "value": cmd["option"] if accion == ANSWER else None,
           "stateFingerprint": interaccion.huella_de_estado(guardado),
           "planFingerprint": interaccion.huella_del_plan(plan),
           "createdAt": task_binding._ahora(), "consumedAt": None}
    _escribir(proyecto, sesion, doc)
    texto = ("Flujo · intención registrada: %s sobre %s de %s. Para aplicarla, corré exactamente:\n"
             "    %s\nSe aplica una sola vez, desde esta sesión, y solo si la tarea sigue igual." % (
                 accion, abierta["interactionId"], clave, comando_de_aplicacion(doc, sesion)))
    return texto, texto
