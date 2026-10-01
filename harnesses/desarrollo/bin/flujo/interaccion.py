"""Que le toca a una persona en una tarea: las interacciones abiertas, derivadas. Nunca escribe.

    interacciones(proyecto, clave)      las abiertas, con su interactionId, sus acciones y opciones
    huella_de_estado(doc)               el stateFingerprint de un estado guardado
    decisiones(proyecto, clave)         los human-decision-record/1.0 de la tarea
    eleccion_de_repositorio(...)        el candidato que eligio una persona, si sigue valiendo

🔴 El interactionId se deriva de datos no secretos -tarea, tipo, input, codigo, bloqueo, unidad,
huella del plan, hash del contexto- y nunca de la hora. Si cambia el bloqueo, el plan o el
contexto, cambia el id, y una intencion sobre el id anterior queda vieja. No se guarda en el
estado: task-flow-state/1.0 no cambia.

Las decisiones las escribe estado_de_tarea/decisiones.py. Aca solo se leen. Nada sale a la red.
"""
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import estado                                      # noqa: E402
from . import requeridos                                  # noqa: E402

VERSION_DECISION = "human-decision-record/1.0"

APPROVE, USE_ALTERNATIVE, CHOOSE, CANCEL, ANSWER, RESUME = (
    "APPROVE", "USE_ALTERNATIVE", "CHOOSE", "CANCEL", "ANSWER", "RESUME")
ACCIONES = (APPROVE, USE_ALTERNATIVE, CHOOSE, CANCEL, ANSWER, RESUME)

HUMAN_DECISION = "HUMAN_DECISION"
TASK_INPUT = "TASK_INPUT"
PERSISTENT = "PERSISTENT_CONFIG_INPUT"

APROBACION = "HUMAN_APPROVAL_PENDING"
CONFLICTO = "REPOSITORY_CONFLICT"

ID = re.compile(r"^ixn-[0-9a-f]{16}$")

# Un TASK_INPUT acepta un valor solo si su fuente de verdad no es un hecho local: la de estos es
# `git remote -v`, y se arregla en el checkout, no contestando.
_SIN_VALOR = ("git remote -v",)


def _huella(*partes):
    crudo = json.dumps(partes, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def huella_de_estado(doc):
    return "sha256:" + _huella(estado.logico(doc)) if doc else None


def _leer_json(ruta):
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _plan(proyecto, clave):
    return _leer_json(os.path.join(proyecto, ".claude", "planes", clave + ".json"))


def huella_del_plan(plan):
    if plan is None:
        return None
    from orquestacion import refutacion
    return refutacion.huella(plan)


def _contexto(proyecto, clave):
    return _leer_json(os.path.join(proyecto, ".claude", "contextos", clave + ".json"))


def hash_del_contexto(proyecto, clave):
    ctx = _contexto(proyecto, clave)
    return str(((ctx or {}).get("meta") or {}).get("context_hash") or "") or None


def _id(*partes):
    return "ixn-" + _huella(*partes)[:16]


def _candidatos(proyecto, clave):
    """Los repositorios que declara la ficha del TaskContext. Sin `.env`: lo que declara
    GITLAB_PROJECT lo agrega la CLI, que si lo puede leer."""
    from . import repositorio
    _, _, _, candidatos = repositorio.de_la_tarea(_contexto(proyecto, clave), None)
    return candidatos


def _acepta_valor(entrada):
    return (entrada or {}).get("sourceOfTruth") not in _SIN_VALOR and \
        (entrada or {}).get("inputId") != "task.key"


def _sensibilidad(entrada, input_id):
    """SECRET o PUBLIC_CONFIG, con el mismo criterio que entrada_humana."""
    destino = (entrada or {}).get("persistentTarget")
    if destino:
        from . import entrada_humana
        try:
            return entrada_humana.sensibilidad(destino)
        except Exception:                              # noqa: BLE001 - ante la duda, secreto
            return "SECRET"
    from integraciones.config import es_clave_de_secreto
    return "SECRET" if es_clave_de_secreto(str(input_id).replace(".", "_")) else "PUBLIC_CONFIG"


def interacciones(proyecto, clave, doc=None, registro=None, candidatos=None):
    """Las interacciones abiertas de la tarea, en orden. Sin estado guardado o terminal: ninguna.

    `candidatos` reemplaza los de la ficha para REPOSITORY_CONFLICT: la CLI pasa los de verdad,
    GITLAB_PROJECT incluido.
    """
    clave = estado.validar_clave(clave)
    if doc is None:
        doc, _ = estado.leer(proyecto, clave)
    if not doc or doc.get("status") in estado.TERMINALES:
        return []
    registro = registro if registro is not None else requeridos.cargar()
    plan = _plan(proyecto, clave)
    huella_plan = huella_del_plan(plan)
    contexto = hash_del_contexto(proyecto, clave)
    salida = []
    for b in doc.get("blockedOn") or []:
        base = {"taskKey": clave, "inputId": b["inputId"], "code": b["code"],
                "blockerId": b["blockerId"], "workUnitId": None, "options": []}
        if b["code"] == APROBACION:
            from orquestacion import consumo
            for a in (plan or {}).get("humanApprovals") or []:
                if a.get("status") != "PENDING":
                    continue
                opcion = consumo.alternativa_mas_barata(a["tier"])
                i = dict(base, kind=HUMAN_DECISION, workUnitId=a["workUnit"], tier=a["tier"],
                         reason=a.get("reason", ""), actions=[APPROVE, USE_ALTERNATIVE, CANCEL],
                         options=[opcion], sensitivity="PUBLIC_CONFIG")
                i["interactionId"] = _id(clave, HUMAN_DECISION, b["inputId"], b["code"],
                                         b["blockerId"], a["workUnit"], a["tier"], huella_plan,
                                         contexto)
                salida.append(i)
            continue
        tipo = b.get("interactionType")
        if not tipo:
            continue                                   # DERIVABLE: lo resuelve el harness
        entrada = requeridos.buscar(registro, b["inputId"])
        if b["code"] == CONFLICTO:
            i = dict(base, kind=HUMAN_DECISION, actions=[CHOOSE, CANCEL],
                     options=list(candidatos if candidatos is not None
                                  else _candidatos(proyecto, clave)))
        elif tipo == TASK_INPUT:
            i = dict(base, kind=TASK_INPUT, actions=([ANSWER] if _acepta_valor(entrada) else [])
                     + [RESUME, CANCEL])
        elif tipo == PERSISTENT:
            destino = (entrada or {}).get("persistentTarget") or {}
            i = dict(base, kind=PERSISTENT, target=destino.get("file"), key=destino.get("key"),
                     actions=[RESUME, CANCEL])
        else:
            i = dict(base, kind=tipo, actions=[CANCEL])
        i["sensitivity"] = _sensibilidad(entrada, b["inputId"])
        # Las opciones de un conflicto no entran al id: salen del TaskContext y del `.env`, y el
        # hash del contexto ya cambia si cambia la ficha.
        i["interactionId"] = _id(clave, i["kind"], b["inputId"], b["code"], b["blockerId"], None,
                                 None, huella_plan, contexto)
        salida.append(i)
    return salida


def buscar(interacciones_, interaction_id):
    return next((i for i in interacciones_ if i["interactionId"] == interaction_id), None)


# -- las decisiones, de solo lectura --------------------------------------------

def carpeta_de_decisiones(proyecto, clave):
    return os.path.join(proyecto, ".claude", "runtime", "tasks", estado.validar_clave(clave),
                        "decisions")


def decisiones(proyecto, clave):
    """Los decision records de la tarea que tienen la forma del contrato, por fecha."""
    carpeta = carpeta_de_decisiones(proyecto, clave)
    try:
        nombres = sorted(os.listdir(carpeta))
    except OSError:
        return []
    salida = []
    for nombre in nombres:
        if not nombre.endswith(".json"):
            continue
        doc = _leer_json(os.path.join(carpeta, nombre))
        if doc and doc.get("schema_version") == VERSION_DECISION and doc.get("taskKey") == clave:
            salida.append(doc)
    return sorted(salida, key=lambda d: str(d.get("decidedAt") or ""))


def cancelada(proyecto, clave):
    """El decision record de CANCEL de la tarea, o None."""
    return next((d for d in decisiones(proyecto, clave) if d.get("action") == CANCEL), None)


def eleccion_de_repositorio(proyecto, clave, contexto_hash):
    """El candidato que eligio una persona para ESTA tarea, si la eleccion es sobre este mismo
    TaskContext. Una eleccion vieja no cuenta."""
    elegido = None
    for d in decisiones(proyecto, clave):
        if d.get("action") == CHOOSE and d.get("contextHash") == contexto_hash:
            elegido = d.get("optionId")
    return elegido
