"""Aplicar una decision humana: consumir el intent una vez, un efecto acotado, reconciliar.

    aplicar(proyecto, clave, accion, interactionId, sesion, opcion, valor)
    retomar(proyecto, clave)        --resume: revalida desde las fuentes y reconcilia

🔴 model tool call != human approval. Nada de aca decide por la persona: sin un human-intent/1.0
sin consumir de esa sesion, para esa tarea, esa interaccion, esa accion y ese estado, no hay
transicion. La CLI que llama a esto la puede correr el modelo; lo que no puede es escribir la
intencion, que sale de UserPromptSubmit.

El orden importa: se valida todo, se consume el intent y recien despues se aplica. Un corte a la
mitad deja la intencion gastada, nunca aplicada dos veces. El estado no se declara: se reconcilia
con la Wave 2, y la tarea retoma desde su compuerta.

Escribe el plan (por orq_plan.replanificar), el human-decision-record/1.0 y el estado. Nunca el
`.env`. Nada sale a la red.
"""
import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                              # noqa: E402
from flujo import estado                                  # noqa: E402
from flujo import interaccion                             # noqa: E402
from flujo import repositorio                             # noqa: E402
from . import persistencia                                # noqa: E402

VERSION = interaccion.VERSION_DECISION

DECISION_STALE = "HUMAN_DECISION_STALE"
INTENT_STALE = "HUMAN_INTENT_STALE"


class ErrorDeDecision(Exception):
    """Lleva el codigo canonico adelante. Nunca un valor."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


def _intenciones():
    """lib.human_intent de los hooks de este harness: una sola implementacion del contrato."""
    ruta = rutas.localizar(("hooks", "lib", "human_intent.py"), __file__)
    if ruta is None:
        raise ErrorDeDecision("HUMAN_INTENT_REQUIRED", "no estan los hooks del harness.")
    hooks = os.path.dirname(os.path.dirname(ruta))
    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    return importlib.import_module("lib.human_intent")


def _candidatos_reales(proyecto, clave, proceso):
    """Los candidatos de verdad, con GITLAB_PROJECT: la CLI si puede leer el `.env`."""
    contexto = interaccion._contexto(proyecto, clave)
    gitlab, _ = estado._entorno(proyecto, proceso)
    _, _, _, candidatos = repositorio.de_la_tarea(contexto, gitlab)
    return candidatos


def _aprobacion(plan, unidad):
    for a in plan.get("humanApprovals") or []:
        if a.get("workUnit") == unidad and a.get("status") == "PENDING":
            return a
    return None


def _efecto_en_el_plan(proyecto, clave, plan, abierta, accion, opcion):
    """APPROVE o USE_ALTERNATIVE: la aprobacion de esa unidad, en el plan, con su historia."""
    from orquestacion import plan as orq_plan
    documento = json.loads(json.dumps(plan))
    solicitud = _aprobacion(documento, abierta["workUnitId"])
    if solicitud is None:
        raise ErrorDeDecision(INTENT_STALE, "la aprobacion de %s ya no esta pendiente."
                              % abierta["workUnitId"])
    solicitud["status"] = "APPROVED" if accion == interaccion.APPROVE else "DOWNGRADED"
    for u in documento.get("workUnits") or []:
        if u.get("id") == abierta["workUnitId"] and u.get("status") == "WAITING_FOR_HUMAN_APPROVAL":
            u["status"] = "PENDING"
            if accion == interaccion.USE_ALTERNATIVE:
                u["modelPolicy"]["requiredTier"] = opcion
    cambio = ("aprobacion humana de %s" % abierta["workUnitId"] if accion == interaccion.APPROVE
              else "alternativa humana para %s: %s" % (abierta["workUnitId"], opcion))
    documento = orq_plan.replanificar(documento, [cambio], "decision humana %s"
                                      % abierta["interactionId"], "human-decision")
    orq_plan.escribir(documento, os.path.join(proyecto, ".claude", "planes", clave + ".json"))
    return documento


def aplicar(proyecto, clave, accion, interaction_id, sesion, opcion=None, valor=None,
            harness_version="", proceso=None):
    """(decision record, estado reconciliado). Levanta ErrorDeDecision y no toca nada si falla."""
    clave = estado.validar_clave(clave)
    hi = _intenciones()
    comparado = opcion if accion in (interaccion.USE_ALTERNATIVE, interaccion.CHOOSE) else \
        valor if accion == interaccion.ANSWER else None
    codigo = hi.verificar(proyecto, sesion, clave, accion, interaction_id, comparado)
    if codigo:
        raise ErrorDeDecision(codigo, "no hay una intencion de la persona que autorice esto. La "
                              "persona tiene que escribirla en el chat: HARNESS ...")
    intent = hi.leer(proyecto, sesion)
    guardado, error = estado.leer(proyecto, clave)
    plan = interaccion._plan(proyecto, clave)
    if intent.get("planFingerprint") != interaccion.huella_del_plan(plan):
        raise ErrorDeDecision(DECISION_STALE, "el plan cambio desde que la persona decidio: "
                              "la decision era sobre otro plan.")
    if error or intent.get("stateFingerprint") != interaccion.huella_de_estado(guardado):
        raise ErrorDeDecision(INTENT_STALE, "el estado de %s cambio desde la intencion." % clave)
    candidatos = _candidatos_reales(proyecto, clave, proceso) \
        if accion == interaccion.CHOOSE else None
    abierta = interaccion.buscar(interaccion.interacciones(proyecto, clave, guardado,
                                                           candidatos=candidatos), interaction_id)
    if abierta is None:
        raise ErrorDeDecision(INTENT_STALE, "%s ya no es una interaccion abierta." % interaction_id)
    if accion not in abierta["actions"]:
        raise ErrorDeDecision(hi.ANSWER_NOT_ACCEPTED if accion == interaccion.ANSWER
                              else hi.ACTION_INVALID, "%s no acepta %s." % (interaction_id, accion))
    if accion in (interaccion.USE_ALTERNATIVE, interaccion.CHOOSE) and \
            opcion not in abierta["options"]:
        raise ErrorDeDecision(hi.OPTION_INVALID, "la opcion no es una de las declaradas.")

    if hi.consumir(proyecto, sesion) is None:
        raise ErrorDeDecision(hi.CONSUMED, "la intencion ya se uso.")
    huella_antes = interaccion.huella_del_plan(plan)
    huella_despues = huella_antes
    if accion in (interaccion.APPROVE, interaccion.USE_ALTERNATIVE):
        huella_despues = interaccion.huella_del_plan(
            _efecto_en_el_plan(proyecto, clave, plan, abierta, accion, opcion))
    record = {"schema_version": VERSION, "taskKey": clave, "interactionId": interaction_id,
              "action": accion, "inputId": abierta["inputId"],
              "workUnitId": abierta.get("workUnitId"),
              "optionId": opcion if accion in (interaccion.USE_ALTERNATIVE, interaccion.CHOOSE)
              else None,
              "planFingerprint": huella_antes, "planFingerprintAfter": huella_despues,
              "contextHash": interaccion.hash_del_contexto(proyecto, clave),
              "stateFingerprint": intent.get("stateFingerprint"), "sessionId": sesion,
              "decidedAt": hi.task_binding._ahora()}
    persistencia._escribir_atomico(
        os.path.join(interaccion.carpeta_de_decisiones(proyecto, clave), interaction_id + ".json"),
        persistencia._como_texto(record))
    doc = persistencia.reconciliar(proyecto, clave, harness_version, proceso)
    return record, doc


def integraciones_a_revalidar(guardado):
    """Que integraciones revalida --resume: las de lo que estaba pendiente. Un input de jira.* o
    de gitlab.*, o la disponibilidad de Jira. Nada mas: retomar otro bloqueo no sale a la red."""
    nombres = set()
    for b in (guardado or {}).get("blockedOn") or []:
        prefijo = str(b.get("inputId") or "").split(".", 1)[0]
        if prefijo in ("jira", "gitlab") and (b.get("interactionType") == "PERSISTENT_CONFIG_INPUT"
                                              or b.get("inputId") == "jira.availability"):
            nombres.add(prefijo)
    return sorted(nombres)


def retomar(proyecto, clave, harness_version="", proceso=None):
    """--resume: reevaluar desde las fuentes -el `.env`, el TaskContext, el plan, los remotos- y
    reconciliar. No declara nada: si sigue faltando, sigue bloqueada."""
    return persistencia.reconciliar(proyecto, estado.validar_clave(clave), harness_version, proceso)
