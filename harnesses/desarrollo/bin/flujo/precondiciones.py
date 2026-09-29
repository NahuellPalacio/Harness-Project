"""Tengo todo lo que necesito para avanzar? La evaluacion de una etapa del flujo.

    evaluar(etapa, hechos)      READY o BLOCKED, con una pregunta por input sin resolver
    de_planificacion(...)       los hechos de PLANNING: el TaskContext, el repositorio y los
                                criterios de aceptacion. El ruteo de agentes lo pone el plan
    compuerta_de_refutacion()   REFUTATION: plan listo, contexto vigente, repositorio local

🔴 Solo bloquea lo que el registro declara bloqueante PARA ESA ETAPA. Un SOFT_DEPENDENCY sin
resolver es una pregunta con `blocking: false`: se dice, y no frena.

🔴 Lo que no se evaluo no pasa. Un input bloqueante de la etapa del que no llego ningun hecho
cuenta como no resuelto. `None` es "no se pudo evaluar porque otro fallo antes" y solo se
acepta si otro input bloqueante ya tiene la etapa bloqueada.

Nada de aca sale a la red ni llama a un modelo. Lee archivos del proyecto y `git remote -v`.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import repositorio                                  # noqa: E402
from . import requeridos                                   # noqa: E402

READY = "READY"
BLOCKED = "BLOCKED"

PLANNING = "PLANNING"
REFUTATION = "REFUTATION"

LISTO_PARA_EJECUTAR = "READY_FOR_EXECUTION"


def _pregunta(entrada):
    return {"inputId": entrada["inputId"],
            "classification": entrada["classification"],
            "interactionType": entrada["interactionType"],
            "failureCode": entrada["failureCode"],
            "blocking": entrada["blocking"],
            "askUser": entrada["askUser"]}


def evaluar(etapa, hechos, registro=None):
    """{stage, status, questions}. La misma etapa con los mismos hechos da lo mismo."""
    registro = registro if registro is not None else requeridos.cargar()
    preguntas, sin_evaluar = [], []
    for entrada in sorted(requeridos.de_etapa(registro, etapa), key=lambda e: e["inputId"]):
        if entrada["classification"] == requeridos.OPTIONAL:
            continue
        valor = hechos.get(entrada["inputId"], False)
        if valor is True:
            continue
        if valor is None:
            sin_evaluar.append(entrada)
            continue
        preguntas.append(_pregunta(entrada))
    bloquea = any(p["blocking"] for p in preguntas)
    if not bloquea:
        preguntas.extend(_pregunta(e) for e in sin_evaluar if e["blocking"])
        preguntas.sort(key=lambda p: p["inputId"])
    return {"stage": etapa,
            "status": BLOCKED if any(p["blocking"] for p in preguntas) else READY,
            "questions": preguntas}


def bloqueantes(evaluacion):
    return [p for p in (evaluacion or {}).get("questions") or [] if p.get("blocking")]


# -- PLANNING ------------------------------------------------------------------

def de_planificacion(task_context, gitlab, proyecto, config_harness):
    """Los hechos de PLANNING que no son del plan, y la identidad del repositorio.

    `gitlab` es la configuracion publica de GitLab que resuelve `entorno.py` desde el `.env`.
    `agents.routing` no esta: lo sabe el plan cuando arma las unidades.
    """
    identidad = repositorio.identidad(task_context, gitlab, proyecto)
    hechos = dict(identidad["facts"])
    hechos["planning.taskContext"] = bool(
        ((task_context or {}).get("meta") or {}).get("task_key"))
    hechos["task.acceptanceCriteriaField"] = bool(
        str((config_harness or {}).get("campoCriteriosAceptacion") or "").strip())
    return {"facts": hechos, "repository": _sin_hechos(identidad)}


def _sin_hechos(identidad):
    return dict((k, v) for k, v in identidad.items() if k != "facts")


# -- REFUTATION ----------------------------------------------------------------

def _leer(ruta):
    if not os.path.isfile(ruta):
        return None
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def contexto_vigente(plan, task_context):
    """Si el plan se hizo sobre este TaskContext, y el TaskContext es el que se escribio.

    Dos comparaciones: el hash del plan contra el del contexto, y el del contexto contra el
    que da recalcularlo. Un contexto editado a mano despues de escribirse dice un hash que ya
    no es el suyo.
    """
    if not isinstance(plan, dict) or not isinstance(task_context, dict):
        return False
    from orquestacion import refutacion
    declarado = str((task_context.get("meta") or {}).get("context_hash") or "")
    referido = str(((plan.get("meta") or {}).get("task_context_ref") or {}).get("context_hash")
                   or "")
    return bool(declarado) and declarado == referido and \
        declarado == refutacion._armador().hash_de(task_context)


def plan_listo(plan):
    """El estado RECALCULADO del plan, no el que dice el archivo."""
    if not isinstance(plan, dict):
        return False
    from orquestacion import plan as orq_plan
    try:
        return plan.get("status") == LISTO_PARA_EJECUTAR and \
            orq_plan.estado_de(plan) == LISTO_PARA_EJECUTAR
    except (KeyError, TypeError, AttributeError):
        return False


def compuerta_de_refutacion(proyecto, clave, gitlab, registro=None):
    """{stage, status, questions, repository}. No escribe nada: decide si se compila."""
    plan = _leer(os.path.join(proyecto, ".claude", "planes", clave + ".json"))
    contexto = _leer(os.path.join(proyecto, ".claude", "contextos", clave + ".json"))
    identidad = repositorio.identidad(contexto, gitlab, proyecto)
    hechos = {"refutation.planReady": plan_listo(plan),
              "refutation.contextFresh": contexto_vigente(plan, contexto),
              "refutation.repositoryMatch": identidad["status"] == repositorio.MATCHED}
    salida = evaluar(REFUTATION, hechos, registro)
    salida["repository"] = _sin_hechos(identidad)
    return salida
