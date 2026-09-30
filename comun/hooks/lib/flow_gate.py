"""La compuerta del flujo en PreToolUse: si una herramienta puede correr para la tarea de la sesion.

    sesion -> tarea (task_binding) -> clase (tool_policy) -> task-flow-state -> allow / deny

READ_ONLY y FLOW_RECOVERY pasan siempre. El resto pasa si la tarea puede avanzar, y eso no lo
decide este modulo: lo dicen `estado.vigencia_local` y `estado.puede_avanzar`, de la Wave 2. Aca
no hay una segunda maquina de estados ni un segundo calculo de vigencia.

🔴 Deny, nunca ask. Un ask dejaria saltar un HARD_BLOCKER aprobando una herramienta; un bloqueo
se resuelve arreglando su causa.

🔴 Fallar cerrado. Un error de la compuerta, con una herramienta que no es de lectura ni de
recuperacion, es FLOW_GATE_UNRESOLVED y deny. `invoke_hook` lo volveria silencio, y en este hook
el silencio es permiso para escribir.

No lee el puntero a la tarea activa, no lee el `.env` y no sale a la red. El unico proceso es
`git remote -v`, y solo con una tarea que evaluar.
"""
import os
import sys

from . import hook
from . import task_binding
from . import tool_policy

HARD_BLOCKER = "FLOW_HARD_BLOCKER"
STATE_STALE = "FLOW_STATE_STALE"
TASK_CLOSED = "FLOW_TASK_CLOSED"
GATE_UNRESOLVED = "FLOW_GATE_UNRESOLVED"
CLASS_UNRESOLVED = "FLOW_TOOL_CLASS_UNRESOLVED"

CLI = "python .claude/harness/bin/desarrollo/dev-harness.py"

# El limite de `git remote -v` en un hook. Medido en esta clase de maquina (N=200): mediana 50 ms,
# p95 69 ms, p99 91 ms, maximo 258 ms. 1,5 s es seis veces el maximo y deja lugar a un disco frio
# o a un antivirus; mas no, porque es lo que espera cada herramienta si `git` se cuelga. Vencido,
# la compuerta falla cerrada: FLOW_GATE_UNRESOLVED. La CLI sigue con los 10 s de `remotos`.
TIMEOUT_REMOTOS = 1.5
_PASAN = (tool_policy.READ_ONLY, tool_policy.FLOW_RECOVERY)


# -- flujo/, de este mismo harness ---------------------------------------------

def _bin_desarrollo():
    """bin/desarrollo instalado; harnesses/desarrollo/bin en el repositorio. None si no esta."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for candidata in (os.path.join(raiz, "bin", "desarrollo"),
                      os.path.join(os.path.dirname(raiz), "harnesses", "desarrollo", "bin")):
        if os.path.isfile(os.path.join(candidata, "flujo", "estado.py")):
            return candidata
    return None


def estado_del_flujo():
    """El modulo `flujo.estado`. Levanta ImportError si este harness no tiene `desarrollo`."""
    carpeta = _bin_desarrollo()
    if carpeta is None:
        raise ImportError("no esta bin/desarrollo/flujo")
    if carpeta not in sys.path:
        sys.path.insert(0, carpeta)
    from flujo import estado
    return estado


def evaluar_tarea(estado, proyecto, clave, remotos=True):
    """(estado guardado o None, vigencia). La vigencia de la Wave 2, sin `.env`: el unico proceso
    es `git remote -v`, local, para ver si el checkout sigue siendo el del estado guardado."""
    doc, error = estado.leer(proyecto, clave)
    if error:
        return None, [error]
    if doc is None:
        return None, [estado.AUSENTE]
    return doc, list(estado.vigencia_local(doc, proyecto, remotos, TIMEOUT_REMOTOS))


# -- los textos ----------------------------------------------------------------

def _bloqueos(doc):
    return ", ".join("%s %s" % (b["blockerId"], b["code"]) for b in (doc or {}).get("blockedOn") or [])


def _motivo_de_tarea(estado, clave, doc, vig, clase):
    """(codigo, texto). Dice que hacer, no solo que se impidio."""
    detalle = "Qué falta: `%s flujo %s --status`." % (CLI, clave)
    if doc is None and vig == [estado.AUSENTE]:
        return estado.AUSENTE, (
            "Flujo: %s todavía no tiene estado del flujo [%s]. Armá el contexto con `%s contexto %s`;"
            " hasta entonces no se modifica el proyecto para esa tarea." % (clave, estado.AUSENTE,
                                                                             CLI, clave))
    if doc is None:
        return vig[0], ("Flujo: el estado guardado de %s no se puede leer [%s]. Se reconstruye con "
                        "`%s contexto %s`. %s" % (clave, vig[0], CLI, clave, detalle))
    status = doc.get("status")
    if status in ("BLOCKED", "WAITING_FOR_HUMAN_APPROVAL") or doc.get("blockedOn"):
        que = ("espera una aprobación humana" if status == "WAITING_FOR_HUMAN_APPROVAL"
               else "está bloqueada")
        return HARD_BLOCKER, (
            "Flujo: %s %s (%s en %s: %s) [%s]. Esta herramienta (%s) modifica o avanza el "
            "proyecto, y un bloqueo no se saltea aprobándola: se resuelve su causa. %s" % (
                clave, que, status, doc.get("stage"), _bloqueos(doc), HARD_BLOCKER,
                clase["reason"], detalle))
    desactualizado = sorted(set(list(doc.get("stale") or []) + list(vig)))
    if desactualizado:
        return STATE_STALE, (
            "Flujo: el estado de %s quedó desactualizado (%s) [%s]: lo guardado ya no es lo de "
            "los artefactos. Regenerá la etapa que cambió antes de modificar el proyecto. %s" % (
                clave, ", ".join(desactualizado), STATE_STALE, detalle))
    return TASK_CLOSED, ("Flujo: %s está %s [%s] y no se sigue modificando. Nombrá otra tarea "
                         "para trabajar." % (clave, status, TASK_CLOSED))


def _ambigua(candidatos):
    return ("Flujo: esta sesión no dijo con qué tarea trabaja y en el proyecto hay más de una (%s) "
            "[%s]. Pedile a la persona que la nombre —por ejemplo «Seguimos con %s»— y reintentá. "
            "El harness no elige una por su cuenta." % (", ".join(candidatos),
                                                       task_binding.AMBIGUOUS, candidatos[0]))


def _vinculo_roto():
    return ("Flujo: el vínculo de esta sesión con su tarea no se puede leer [%s]. Pedile a la "
            "persona que nombre la tarea otra vez (por ejemplo «Seguimos con ABC-123»)."
            % task_binding.STALE)


# -- la decision ---------------------------------------------------------------

def _negar(salida, codigo, texto):
    if salida["class"] == tool_policy.UNRESOLVED:
        texto += (" No se reconoce qué hace este comando [%s]: mientras tanto solo pasan la lectura"
                  " y la recuperación del flujo." % CLASS_UNRESOLVED)
    salida.update(decision="deny", code=codigo, reason=texto)
    return salida


def _evaluar(evento, clase, salida):
    proyecto = task_binding.raiz(hook.campo(evento, "cwd", ""))
    sesion = hook.campo(evento, "session_id", None)
    if not task_binding.tareas(proyecto):
        # Sin ningun estado del flujo no hay nada que gobernar, haya o no binding: un binding
        # solo no traba un proyecto que nunca paso por `contexto`, ni un harness sin `desarrollo`.
        return salida
    resolucion = task_binding.resolver(proyecto, sesion, clase.get("taskKey"))
    salida.update(resolution=resolucion["status"], via=resolucion["via"])
    if resolucion["status"] == task_binding.AMBIGUOUS:
        return _negar(salida, task_binding.AMBIGUOUS, _ambigua(resolucion["candidates"]))
    if resolucion["status"] == task_binding.STALE:
        return _negar(salida, task_binding.STALE, _vinculo_roto())
    clave = resolucion["taskKey"]
    if clave is None:
        return salida
    estado = estado_del_flujo()
    salida["taskKey"] = clave
    doc, vig = evaluar_tarea(estado, proyecto, clave)
    salida["vigencia"] = vig
    if estado.puede_avanzar(doc, vig):
        return salida
    # Revalidar: un comando del Harness que corre la etapa donde el flujo retoma, o una anterior,
    # reevalua su propia compuerta. Esperando una aprobacion no hay revalidacion: es la Wave 4.
    if (clase["class"] == tool_policy.WORKFLOW_ADVANCING and clase.get("reconcilia")
            and (doc or {}).get("status") != "WAITING_FOR_HUMAN_APPROVAL"):
        desde = estado.reanudar_desde(doc, vig)
        if desde and estado.STAGES.index(clase["stage"]) <= estado.STAGES.index(desde):
            salida["revalidation"] = True
            return salida
    codigo, texto = _motivo_de_tarea(estado, clave, doc, vig, clase)
    return _negar(salida, codigo, texto)


def decidir(evento):
    """{decision: allow|deny, code, reason, class, taskKey, resolution, via}. Nunca levanta."""
    try:
        clase = tool_policy.clasificar(hook.campo(evento, "tool_name", ""),
                                       hook.campo(evento, "tool_input", {}),
                                       task_binding.raiz(hook.campo(evento, "cwd", "")),
                                       hook.campo(evento, "cwd", None))
    except Exception:                                  # noqa: BLE001 - se clasifica de mas, no de menos
        clase = {"class": tool_policy.UNRESOLVED, "reason": "no se pudo clasificar",
                 "taskKey": None, "stage": None, "reconcilia": False}
    salida = {"decision": "allow", "code": None, "reason": "", "class": clase["class"],
              "taskKey": None, "resolution": None, "via": None}
    if clase["class"] in _PASAN:
        if clase.get("taskKey"):
            _vincular_por_comando(evento, clase["taskKey"])
        return salida
    try:
        return _evaluar(evento, clase, salida)
    except Exception as e:                             # noqa: BLE001 - fallar cerrado
        return _negar(salida, GATE_UNRESOLVED, (
            "Flujo: no se pudo evaluar la compuerta (%s) [%s]. Una herramienta que modifica o "
            "avanza el proyecto no pasa sin evaluarla; la lectura y `flujo <KEY> --status` sí."
            % (type(e).__name__, GATE_UNRESOLVED)))


def _vincular_por_comando(evento, clave):
    """Un comando del Harness que nombra su tarea vincula una sesion que no tenia (prioridad 3)."""
    try:
        proyecto = task_binding.raiz(hook.campo(evento, "cwd", ""))
        if task_binding.tareas(proyecto):
            task_binding.resolver(proyecto, hook.campo(evento, "session_id", None), clave)
    except Exception:                                  # noqa: BLE001 - vincular no voltea la lectura
        pass
