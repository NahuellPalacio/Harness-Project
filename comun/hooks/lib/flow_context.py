"""Lo que el flujo le dice a la sesion: el bloqueo en UserPromptSubmit, la continuidad en SessionStart.

    del_turno(evento)    UserPromptSubmit: vincula si el prompt declara una clave, y si la tarea
                         de la sesion no puede avanzar devuelve (para el modelo, para la persona)
    continuidad(evento)  SessionStart: una linea, o None

Solo muestra: no decide nada, y un error propio se calla (el hook sigue). La posicion y el enlace
de un input que la persona completa en un archivo los da `entrada_humana`, el unico localizador:
ni este modulo ni el estado guardado tienen una linea del `.env`, y nunca un valor.

No repite el bloque: la huella del ultimo que se mostro queda en
`.claude/runtime/sessions/<SAFE>/notice.json` (session-flow-notice/1.0). Con la misma huella sale
una linea; con otra, el bloque entero. Si la tarea vuelve a poder avanzar, la huella se borra.
"""
import hashlib
import io
import json
import os

from . import flow_gate
from . import task_binding

VERSION_AVISO = "session-flow-notice/1.0"
CLI = flow_gate.CLI
_PUNTERO = (".claude", "runtime", "active-task.json")


# -- la huella del ultimo aviso ------------------------------------------------

def _ruta_aviso(proyecto, sesion):
    archivo = task_binding.ruta(proyecto, sesion)
    return os.path.join(os.path.dirname(archivo), "notice.json") if archivo else None


def _ultima_huella(proyecto, sesion):
    ruta = _ruta_aviso(proyecto, sesion)
    try:
        with io.open(ruta, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError, TypeError):
        return None
    ok = isinstance(doc, dict) and doc.get("schema_version") == VERSION_AVISO \
        and doc.get("sessionId") == sesion
    return doc.get("fingerprint") if ok else None


def _guardar_huella(proyecto, sesion, huella):
    ruta = _ruta_aviso(proyecto, sesion)
    if ruta is None:
        return
    task_binding.escribir_atomico(ruta, {"schema_version": VERSION_AVISO, "sessionId": sesion,
                                         "fingerprint": huella,
                                         "updatedAt": task_binding._ahora()})


def _olvidar_huella(proyecto, sesion):
    ruta = _ruta_aviso(proyecto, sesion)
    if ruta and os.path.isfile(ruta):
        os.remove(ruta)


def _huella(*partes):
    crudo = json.dumps(partes, ensure_ascii=False, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _dedup(proyecto, sesion, huella, bloque, linea):
    """(para el modelo, para la persona): el bloque la primera vez, la linea despues."""
    if sesion and _ultima_huella(proyecto, sesion) == huella:
        return (linea, None) if linea else None
    if sesion:
        _guardar_huella(proyecto, sesion, huella)
    return bloque, bloque


# -- los textos ----------------------------------------------------------------

def _pendiente_en_archivo(doc):
    pendiente = (doc or {}).get("pendingHumanInteraction") or {}
    return pendiente if pendiente.get("kind") == "PERSISTENT_CONFIG_INPUT" else None


def _ubicacion(proyecto, pendiente):
    from flujo import entrada_humana
    try:
        return entrada_humana.localizar(pendiente["inputId"], proyecto)
    except entrada_humana.EntradaNoUbicable:
        return None


def _revalidar(estado, doc, vig, clave):
    if estado.reanudar_desde(doc, vig) == "CONTEXT":
        return "%s contexto %s" % (CLI, clave)
    return "%s flujo %s --status" % (CLI, clave)


def _bloque(estado, proyecto, clave, doc, vig, via):
    unica = " (la única tarea con estado del proyecto)" if via == "single-candidate" else ""
    detalle = "Detalle: `%s flujo %s --status`." % (CLI, clave)
    if doc is None:
        return ("Flujo · %s%s no tiene un estado del flujo que se pueda usar (%s). Armá el contexto "
                "con `%s contexto %s`; hasta entonces no se modifica el proyecto para esa tarea."
                % (clave, unica, ", ".join(vig), CLI, clave)), None
    pendiente = _pendiente_en_archivo(doc)
    ubicacion = _ubicacion(proyecto, pendiente) if pendiente else None
    status = doc.get("status")
    if doc.get("blockedOn"):
        que = ("espera una aprobación humana" if status == "WAITING_FOR_HUMAN_APPROVAL"
               else "está bloqueada")
        por = " por `%s`" % pendiente["key"] if pendiente else ""
        lineas = ["Flujo · la tarea %s%s %s (%s en %s)%s." % (clave, unica, que, status,
                                                             doc.get("stage"), por)]
        for b in doc["blockedOn"]:
            lineas.append("  %s  %s (%s)" % (b["blockerId"], b["inputId"], b["code"]))
        repo = doc.get("repositoryRef") or {}
        if any(b["code"] == "REPOSITORY_MISMATCH" for b in doc["blockedOn"]):
            lineas.append("  La tarea es de %s y este checkout es de %s." % (
                repo.get("taskRepository") or "—",
                ", ".join(repo.get("localRepositories") or []) or "—"))
        if ubicacion:
            from flujo import entrada_humana
            lineas.append("")
            lineas.append(entrada_humana.renderizar(ubicacion, _revalidar(estado, doc, vig, clave)))
            lineas.append("")
        lineas.append("Mientras siga así solo pasan la lectura y la recuperación del flujo: nada "
                      "que modifique el proyecto. %s" % detalle)
        return "\n".join(lineas), ubicacion
    desactualizado = sorted(set(list(doc.get("stale") or []) + list(vig)))
    return ("Flujo · el estado de %s%s quedó desactualizado (%s): lo guardado ya no es lo de los "
            "artefactos. Regenerá la etapa que cambió antes de modificar el proyecto. %s" % (
                clave, unica, ", ".join(desactualizado) or status, detalle)), None


def _linea(clave, doc, vig):
    if doc is None:
        return "Flujo · %s sigue sin un estado del flujo que se pueda usar (%s)." % (
            clave, ", ".join(vig))
    pendiente = _pendiente_en_archivo(doc)
    bloqueos = ", ".join("%s %s" % (b["blockerId"], b["code"]) for b in doc.get("blockedOn") or [])
    if bloqueos:
        return "Flujo · %s sigue %s%s (%s): el detalle ya salió en esta sesión." % (
            clave, "esperando una aprobación" if doc.get("status") == "WAITING_FOR_HUMAN_APPROVAL"
            else "bloqueada", " por %s" % pendiente["key"] if pendiente else "", bloqueos)
    return "Flujo · %s sigue desactualizada (%s): el detalle ya salió en esta sesión." % (
        clave, ", ".join(sorted(set(list(doc.get("stale") or []) + list(vig)))))


# -- UserPromptSubmit ----------------------------------------------------------

def del_turno(evento):
    """(para el modelo, para la persona) o None. Vincula si el prompt declara una clave."""
    from . import hook
    proyecto = task_binding.raiz(hook.campo(evento, "cwd", ""))
    if not proyecto or not os.path.isdir(proyecto):
        return None
    sesion = hook.campo(evento, "session_id", None)
    sesion = sesion if task_binding.sesion_segura(sesion) else None
    clave = task_binding.clave_declarada(hook.campo(evento, "prompt", ""))
    if clave and sesion:
        task_binding.escribir(proyecto, sesion, clave, "user-prompt")
    if not task_binding.tareas(proyecto):
        return None                                    # sin estado del flujo no hay que decir
    resolucion = task_binding.resolver(proyecto, sesion)
    if resolucion["status"] == task_binding.AMBIGUOUS:
        candidatos = resolucion["candidates"]
        texto = ("Flujo · esta sesión no dijo con qué tarea trabaja y en el proyecto hay %d con "
                 "estado (%s) [%s]. Hasta que la nombres —por ejemplo «Seguimos con %s»— no se "
                 "modifica el proyecto." % (len(candidatos), ", ".join(candidatos),
                                            task_binding.AMBIGUOUS, candidatos[0]))
        return _dedup(proyecto, sesion, _huella(task_binding.AMBIGUOUS, candidatos), texto, None)
    if resolucion["status"] == task_binding.STALE:
        texto = ("Flujo · el vínculo de esta sesión con su tarea no se puede leer [%s]. Nombrá la "
                 "tarea otra vez (por ejemplo «Seguimos con ABC-123»)." % task_binding.STALE)
        return _dedup(proyecto, sesion, _huella(task_binding.STALE), texto, None)
    clave = resolucion["taskKey"]
    if clave is None:
        return None
    estado = flow_gate.estado_del_flujo()
    doc, vig = flow_gate.evaluar_tarea(estado, proyecto, clave)
    if estado.puede_avanzar(doc, vig):
        if sesion:
            _olvidar_huella(proyecto, sesion)
        return None
    bloque, ubicacion = _bloque(estado, proyecto, clave, doc, vig, resolucion["via"])
    huella = _huella(clave, (doc or {}).get("stage"), (doc or {}).get("status"),
                     [(b["blockerId"], b["code"], b["inputId"])
                      for b in (doc or {}).get("blockedOn") or []],
                     sorted(set(list((doc or {}).get("stale") or []) + list(vig))),
                     (doc or {}).get("pendingHumanInteraction"),
                     [ubicacion.get(k) for k in ("file", "line", "column", "present")]
                     if ubicacion else None)
    return _dedup(proyecto, sesion, huella, bloque, _linea(clave, doc, vig))


# -- SessionStart --------------------------------------------------------------

def _sugerencia(proyecto, tareas):
    """La ultima tarea tocada en el proyecto, solo para mostrar. Nunca decide nada."""
    try:
        with io.open(os.path.join(proyecto, *_PUNTERO), encoding="utf-8") as f:
            clave = json.load(f).get("taskKey")
    except (OSError, ValueError, AttributeError):
        return None
    return clave if clave in tareas else None


def continuidad(evento):
    """Una linea para SessionStart, o None. Sin binding no inventa tarea."""
    from . import hook
    proyecto = task_binding.raiz(hook.campo(evento, "cwd", ""))
    if not proyecto or not os.path.isdir(proyecto):
        return None
    sesion = hook.campo(evento, "session_id", None)
    if not task_binding.tareas(proyecto):
        return None
    binding, error = task_binding.leer(proyecto, sesion)
    if error:
        return ("Flujo · el vínculo de esta sesión con su tarea no se puede leer; nombrá la tarea "
                "para seguir.")
    if binding is None:
        tareas = task_binding.tareas(proyecto)
        if not tareas:
            return None
        sugerida = _sugerencia(proyecto, tareas)
        if sugerida:
            return ("Flujo · esta sesión está sin tarea vinculada. La última tocada en el proyecto "
                    "es %s, como sugerencia y no como elección: nombrala («Seguimos con %s») para "
                    "trabajarla." % (sugerida, sugerida))
        return ("Flujo · esta sesión está sin tarea vinculada y hay %d con estado (%s): nombrá la "
                "que trabajás." % (len(tareas), ", ".join(tareas)))
    clave = binding["taskKey"]
    estado = flow_gate.estado_del_flujo()
    # Una linea que solo muestra: sin `git remote -v`. La compuerta si lo corre.
    doc, vig = flow_gate.evaluar_tarea(estado, proyecto, clave, remotos=False)
    if estado.puede_avanzar(doc, vig):
        return "Flujo · esta sesión trabaja %s: %s, %s." % (
            clave, doc.get("stage"), estado.LEGIBLE.get(doc.get("status"), doc.get("status")))
    if doc is None:
        return "Flujo · %s no tiene un estado del flujo que se pueda usar (%s)." % (
            clave, ", ".join(vig))
    pendiente = _pendiente_en_archivo(doc)
    if pendiente and doc.get("blockedOn"):
        return ("Flujo · %s sigue bloqueada por %s; pedime continuar para mostrar dónde "
                "completarlo." % (clave, pendiente["key"]))
    if doc.get("status") == "WAITING_FOR_HUMAN_APPROVAL":
        return "Flujo · %s sigue esperando una aprobación humana (%s)." % (
            clave, ", ".join(b["code"] for b in doc["blockedOn"]))
    if doc.get("blockedOn"):
        return "Flujo · %s sigue bloqueada (%s); pedime continuar para ver qué falta." % (
            clave, ", ".join(b["code"] for b in doc["blockedOn"]))
    return "Flujo · %s tiene el estado desactualizado (%s); pedime continuar para ver qué falta." % (
        clave, ", ".join(sorted(set(list(doc.get("stale") or []) + list(vig)))))
