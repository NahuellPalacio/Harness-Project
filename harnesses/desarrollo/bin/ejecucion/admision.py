"""ExecutionAdmission: la regla de quince condiciones de T3 §37.5, leyendo a cada dueno.

docs/cambios/minimal-execution-engine/spec.md, MD-11 a MD-13 y MD-23.

    al_pedir      condiciones 1 a 3 y 5 a 15, y el armado de la request (MD-23)
    al_entregar   las quince, sobre la request guardada, mas el adaptador (agente y capacidades)

El orden y los codigos son los de `contrato.PRECEDENCIA`, y gana la primera falla. Cada dato sale de
su dueno: el plan de Planning por su regla de lectura, el flujo de su TaskFlowState guardado y su
vigencia local, la compuerta normativa de Normative Sources, el agente y las capacidades de Catalog,
y las dependencias y los duplicados de los turnos del registro.

🔴 La admision no escribe estado del flujo: lo lee con `estado.leer` y `estado.vigencia_local`, y
nunca reconcilia ni deriva (MD-12). Lo que escribe la compuerta normativa al refrescar es suyo.

🔴 Al entregar, el `request.json` guardado no se cree: se vuelve a derivar todo, y su WorkUnit tiene
que tener la huella de la del plan (ME-16).
"""
import copy
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import contrato                                     # noqa: E402
from . import registro                                     # noqa: E402
from contexto import limpieza                              # noqa: E402
from flujo import estado as flujo_estado                   # noqa: E402
from orquestacion import auto_refresh                      # noqa: E402
from orquestacion import capacidades                       # noqa: E402
from orquestacion import plan as orq_plan                  # noqa: E402
from orquestacion import registro_agentes                  # noqa: E402

LISTO = "READY_FOR_EXECUTION"
UNIDAD = re.compile(r"[a-z0-9][a-z0-9-]*")
NORMA_POR_DEFECTO = "ES0901"


class SinCatalogo(Exception):
    """Sin el catalogo de secretos no se persiste nada: es un error del comando."""


class Rechazo(Exception):
    """Una condicion que no se cumple: su codigo y su detalle, todavia sin redactar."""

    def __init__(self, codigo, detalle):
        Exception.__init__(self, codigo)
        self.codigo = codigo
        self.detalle = detalle


# -- el detalle ------------------------------------------------------------------------------

def detalle(texto, catalogo):
    """Redactado y de hasta 300 caracteres. Sin catalogo no se llama: quien no lo tiene arma un
    detalle hecho solo de texto del motor."""
    texto = str(texto or "").strip() or "sin detalle"
    if catalogo is not None:
        texto, _ = limpieza.redactar(texto, catalogo, "$.error.detail")
    tope = contrato.TOPE_DE_DETALLE
    return texto if len(texto) <= tope else texto[:tope - 1].rstrip() + "…"


def error(codigo, texto, catalogo):
    return {"code": codigo, "detail": detalle(texto, catalogo)}


# -- las normas de la unidad (MD-13) ----------------------------------------------------------

def normas_de(unidad):
    """Las normas que la unidad exige: las claves de `normative.standards` que traen su bloque, y
    sin esa estructura la de arriba, o ES0901. Es la regla de `refutacion.estandares_de_unidades`,
    escrita aca a proposito: Execution no importa la refutacion (MD-13, ME-E29)."""
    normative = unidad.get("normative") if isinstance(unidad, dict) else None
    normative = normative if isinstance(normative, dict) else {}
    estandares = normative.get("standards")
    if isinstance(estandares, dict) and estandares:
        return sorted(sid for sid, bloque in estandares.items() if isinstance(bloque, dict))
    return [str((normative.get("standard") or {}).get("id") or NORMA_POR_DEFECTO)]


def compuerta_por_defecto(proyecto, observar_jira=None):
    """La compuerta como la llama `plan`, con las normas de la unidad. El CLI le pasa su
    observador de Jira; sin el, un refresco vencido queda `unresolved`."""
    def compuerta(requeridas):
        return auto_refresh.ensure_normative_knowledge_fresh(
            proyecto, observar_jira, _capacidades(proyecto), auto_refresh.canal_previsto(proyecto),
            requeridas=requeridas)
    return compuerta


# -- los duenos ------------------------------------------------------------------------------

def _capacidades(proyecto):
    ruta = os.path.join(proyecto, ".claude", "harness.capacidades.json")
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return {}
    registro_ = doc.get("capacidades") if isinstance(doc, dict) else None
    return registro_ if isinstance(registro_, dict) else {}


def ruta_del_plan(proyecto, clave):
    """`.claude/planes/<KEY>.json`, con la clave ya validada con anclaje completo (condicion 1).

    🔴 No es `refutacion.ruta_del_plan`: Execution no importa la refutacion (MD-13, EX-E08). Es la
    misma ruta, y un escenario lo fija (ME-E29)."""
    return os.path.join(proyecto, ".claude", "planes", clave + ".json")


def leer_plan(proyecto, clave):
    """El plan por la regla de lectura de Planning. Levanta Rechazo(PLAN_UNREADABLE).

    Publico desde Task 5 (GD-27, paso 3): el GraphRun lee el plan con esta misma regla, sin duplicarla.
    Es el unico lector del plan de la admision."""
    ruta = ruta_del_plan(proyecto, clave)
    try:
        with io.open(ruta, "rb") as f:
            crudo = f.read()
    except FileNotFoundError:
        raise Rechazo("PLAN_UNREADABLE", "%s no tiene plan guardado: corré `plan %s`."
                      % (clave, clave))
    except OSError as e:
        raise Rechazo("PLAN_UNREADABLE", "el plan de %s no se puede leer: %s"
                      % (clave, type(e).__name__))
    try:
        plan = json.loads(crudo.decode("utf-8-sig"))
    except ValueError:
        raise Rechazo("PLAN_UNREADABLE", "el plan de %s no es un JSON legible (cortado o roto)."
                      % clave)
    if not isinstance(plan, dict):
        raise Rechazo("PLAN_UNREADABLE", "el plan de %s no es un objeto." % clave)
    try:
        orq_plan.aceptar_guardado(plan, clave)
    except orq_plan.PlanInvalido as e:
        raise Rechazo("PLAN_UNREADABLE", str(e))
    unidades = plan.get("workUnits")
    if not isinstance(unidades, list) or not all(isinstance(u, dict) for u in unidades):
        raise Rechazo("PLAN_UNREADABLE", "el plan de %s no trae sus workUnits." % clave)
    ids = [u.get("id") for u in unidades]
    repetidos = sorted(set(str(i) for i in ids if ids.count(i) > 1))
    if repetidos:
        raise Rechazo("PLAN_UNREADABLE", "el plan de %s repite unidades: %s"
                      % (clave, ", ".join(repetidos)))
    return plan


def _plan_listo(plan):
    """2.1 y READY_FOR_EXECUTION por los dos lados, como `precondiciones.plan_listo`."""
    meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
    try:
        return (meta.get("schema_version") == orq_plan.VERSION_SCHEMA
                and plan.get("status") == LISTO and orq_plan.estado_de(plan) == LISTO)
    except (KeyError, TypeError, AttributeError, ValueError):
        return False


def _flujo(proyecto, clave):
    """None si la tarea puede delegar, o el detalle de por que no (MD-12)."""
    reconciliar = ("Para reconciliarlo: `dev-harness.py flujo %s --status`, o la etapa que "
                   "corresponda." % clave)
    doc, codigo = flujo_estado.leer(proyecto, clave)
    if doc is None:
        return "%s: la tarea no tiene un estado del flujo que se pueda aplicar. %s" % (
            codigo or flujo_estado.AUSENTE, reconciliar)
    try:
        vigencia = flujo_estado.vigencia_local(doc, proyecto, remotos=True, timeout=10)
    except Exception as e:                       # noqa: BLE001 - ante la duda, no se delega
        return "no se pudo saber si el estado del flujo esta vigente (%s). %s" % (
            type(e).__name__, reconciliar)
    if flujo_estado.permisos(doc, vigencia)["delegationAllowed"]:
        return None
    bloqueos = " ".join("%s %s" % (b.get("blockerId") or b.get("inputId") or "?", b.get("code"))
                        for b in doc.get("blockedOn") or [] if isinstance(b, dict))
    return "%s/%s; bloqueos: %s; vigencia: %s. %s" % (
        doc.get("stage"), doc.get("status"), bloqueos or "ninguno",
        " ".join(vigencia) or "al dia", reconciliar)


def _unidad(plan, unidad_id):
    return next((u for u in plan["workUnits"] if u.get("id") == unidad_id), None)


def _agente(proyecto, unidad, cargar_registro, adaptador):
    """(validacion, declaracion, definicion), o levanta el Rechazo de 10, 11 o 12.

    La 10 es el AgentRegistry y, al entregar, la definicion del agente en el Host, antes de
    `entrega.json`: es la ultima vez que AGENT_UNAVAILABLE puede salir (ME-I29)."""
    agente_id = unidad.get("assignedAgent")
    try:
        documento = cargar_registro()
    except registro_agentes.RegistroInvalido as e:
        raise Rechazo("AGENT_UNAVAILABLE", "el registro de agentes no se puede leer: %s" % e)
    ruteo = registro_agentes.resolver_ruteo(agente_id, documento=documento)
    if not ruteo.get("routable"):
        raise Rechazo("AGENT_UNAVAILABLE", "%s no se puede rutear: %s"
                      % (agente_id, ruteo.get("result")))
    definicion = None
    if adaptador is not None:
        definicion, motivo = adaptador.resolver_agente(proyecto, agente_id)
        if definicion is None:
            raise Rechazo("AGENT_UNAVAILABLE", motivo)
    declaracion = registro_agentes.agente(agente_id, documento) or {}
    if declaracion.get("type") not in contrato.TIPOS_EJECUTABLES:
        raise Rechazo("AGENT_NOT_EXECUTABLE", "%s es %s, y se ejecutan solo %s"
                      % (agente_id, declaracion.get("type"), ", ".join(contrato.TIPOS_EJECUTABLES)))
    if declaracion.get("domain") != unidad.get("domain"):
        raise Rechazo("AGENT_DOMAIN_MISMATCH", "%s es de %s y la unidad de %s"
                      % (agente_id, declaracion.get("domain"), unidad.get("domain")))
    return ruteo.get("agentValidation"), declaracion, definicion


def _faltan_capacidades(proyecto, unidad):
    tengo = set(capacidades.disponibles(_capacidades(proyecto)))
    return [c for c in unidad.get("requiredCapabilities") or [] if c not in tengo]


def _dependencias(proyecto, clave, huella_plan, unidad):
    """[{workUnitId, executionId}] o levanta el Rechazo de 14."""
    satisfechas, faltan = [], []
    for dependencia in unidad.get("dependencies") or []:
        llave = contrato.clave_de_idempotencia(clave, huella_plan, dependencia)
        ultimo = registro.ultimo_turno(proyecto, clave, llave)
        if ultimo is None or ultimo["estado"] != "SUCCEEDED":
            faltan.append("%s (%s)" % (dependencia, "sin ejecutar" if ultimo is None
                                       else ultimo["estado"]))
        else:
            satisfechas.append({"workUnitId": dependencia, "executionId": ultimo["executionId"]})
    if faltan:
        raise Rechazo("DEPENDENCY_NOT_SATISFIED",
                      "dependencias sin SUCCEEDED en esta huella del plan: %s" % ", ".join(faltan))
    return satisfechas


def _duplicado(clave, ultimo):
    estado = ultimo["estado"]
    texto = "la clave ya tiene el turno %d, %s, %s" % (
        ultimo["numero"], ultimo["executionId"] or "ilegible", estado)
    if estado == registro.ILEGIBLE:
        texto += " (%s)" % ultimo["motivo"]
    if estado == registro.REQUESTED:
        texto += ". Si su motor murio, se cancela con `ejecutar %s --cancelar %s`" % (
            clave, ultimo["executionId"])
    return Rechazo("DUPLICATE_EXECUTION", texto)


# -- la regla --------------------------------------------------------------------------------

def _regla(proyecto, clave, unidad_id, compuerta, cargar_registro, request=None,
           adaptador=None, huella_esperada=None):
    """Las condiciones en el orden de la precedencia. Sin `request` es al pedir; con ella, al
    entregar. Devuelve lo derivado, o levanta el Rechazo de la primera que falla.

    `huella_esperada` (Task 5, GD-16) solo cuenta al entregar: si viene y la request guardada se armo
    con otra huella del plan, es la condicion 4, PLAN_CHANGED, en su lugar de la precedencia."""
    plan = leer_plan(proyecto, clave)                                          # 2
    meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
    if meta.get("task_key") != clave:                                          # 3
        raise Rechazo("TASK_KEY_MISMATCH", "el plan guardado es de %s y se pidio %s"
                      % (meta.get("task_key"), clave))
    huella_plan = contrato.huella(plan)
    if request is not None:
        if huella_plan == request["plan"]["planFingerprint"]:                  # 1, al entregar
            de_plan = _unidad(plan, unidad_id)
            if de_plan is None or contrato.huella(de_plan) != request["workUnitFingerprint"] \
                    or contrato.huella(request["workUnit"]) != contrato.huella(de_plan):
                raise Rechazo("CONTRACT_INVALID", "la WorkUnit de request.json no es la del plan")
            if huella_esperada is not None \
                    and huella_esperada != request["plan"]["planFingerprint"]:         # 4, esperada
                raise Rechazo("PLAN_CHANGED", "la request se armo con una huella del plan que no es "
                              "la que esperaba quien la pidio: el plan cambio antes de leerlo")
        else:                                                                  # 4
            raise Rechazo("PLAN_CHANGED", "el plan cambio desde que se creo la Execution: su "
                          "huella ya no es la de la request")
    if not _plan_listo(plan):                                                  # 5
        raise Rechazo("PLAN_NOT_READY", "el plan es %s con status %s; se admite solo un %s %s "
                      "por los dos lados" % (meta.get("schema_version"), plan.get("status"),
                                             orq_plan.VERSION_SCHEMA, LISTO))
    motivo = _flujo(proyecto, clave)                                           # 6
    if motivo is not None:
        raise Rechazo("DELEGATION_NOT_ALLOWED", motivo)
    unidad = _unidad(plan, unidad_id)                                          # 7
    if unidad is None:
        raise Rechazo("WORK_UNIT_NOT_FOUND", "el plan no tiene la unidad %s" % unidad_id)
    if unidad.get("status") != "PENDING":                                      # 8
        raise Rechazo("WORK_UNIT_NOT_PENDING", "la unidad %s esta %s"
                      % (unidad_id, unidad.get("status")))
    veredicto = compuerta(normas_de(unidad))                                   # 9
    if veredicto.get("decision") == auto_refresh.BLOQUEADO:
        raise Rechazo("NORMATIVE_GATE_BLOCKED", veredicto.get("reason") or "fuentes en alerta")
    validacion, declaracion, definicion = _agente(proyecto, unidad, cargar_registro,
                                                  adaptador)                   # 10 a 12
    faltan = _faltan_capacidades(proyecto, unidad)                             # 13
    if faltan:
        raise Rechazo("CAPABILITY_UNAVAILABLE", "no estan disponibles: %s" % ", ".join(faltan))
    if adaptador is not None:
        faltan = adaptador.provee(unidad.get("requiredCapabilities") or [], definicion)
        if faltan:
            raise Rechazo("CAPABILITY_UNAVAILABLE", "el Host Adapter no las provee al agente: %s"
                          % ", ".join(faltan))
    dependencias = _dependencias(proyecto, clave, huella_plan, unidad)         # 14
    llave = contrato.clave_de_idempotencia(clave, huella_plan, unidad_id)      # 15
    ultimo = registro.ultimo_turno(proyecto, clave, llave)
    if request is None:
        if ultimo is not None and ultimo["estado"] not in ("FAILED", "CANCELLED", "REJECTED"):
            raise _duplicado(clave, ultimo)
    elif ultimo is None or ultimo["executionId"] != request["executionId"]:
        raise _duplicado(clave, ultimo) if ultimo is not None else Rechazo(
            "DUPLICATE_EXECUTION", "ningun turno nombra a esta Execution")
    return {"plan": plan, "huellaPlan": huella_plan, "unidad": unidad, "llave": llave,
            "leido": ultimo["numero"] if ultimo is not None else 0,
            "validacion": validacion, "declaracion": declaracion, "decision":
            veredicto.get("decision"), "dependencias": dependencias, "definicion": definicion}


def _forma(clave, unidad_id, pedido_por):
    if not registro.es(registro.CLAVE_DE_TAREA, clave):
        raise Rechazo("CONTRACT_INVALID", "%r no es una TaskKey" % (clave,))
    if not registro.es(UNIDAD, unidad_id):
        raise Rechazo("CONTRACT_INVALID", "%r no es el id de una WorkUnit" % (unidad_id,))
    if not isinstance(pedido_por, str) or not pedido_por.strip():
        raise Rechazo("CONTRACT_INVALID", "falta quien pide la ejecucion")


def al_pedir(proyecto, clave, unidad_id, pedido_por, catalogo, compuerta=None,
             cargar_registro=None, execution_id=None):
    """(request, None, leido, huella) o (None, ExecutionError, None, None).

    Condiciones 1 a 3 y 5 a 15, y despues la request, en el orden de MD-23: derivar, redactar,
    verificar que la WorkUnit no cambio, validar y calcular su huella. La request que vuelve es la
    que se persiste, y `huella` es la suya: la que lleva `requestFingerprint` (ME-I30). `leido` es
    el numero del ultimo turno de la clave, el que la reserva tiene que superar. Sin catalogo
    levanta SinCatalogo: no hay Execution ni ExecutionError.
    """
    if catalogo is None:
        raise SinCatalogo("no esta el catalogo de secretos: sin el no se persiste nada")
    compuerta = compuerta or compuerta_por_defecto(proyecto)
    cargar_registro = cargar_registro or registro_agentes.cargar
    try:
        _forma(clave, unidad_id, pedido_por)                                   # 1
        derivado = _regla(proyecto, clave, unidad_id, compuerta, cargar_registro)
        request = _request(derivado, clave, pedido_por, execution_id or registro.nuevo_id())
        redactada, _ = limpieza.redactar_arbol(request, catalogo)
        if redactada["workUnit"] != request["workUnit"]:
            raise Rechazo("CONTRACT_INVALID", "la unidad %s del plan tiene un secreto segun el "
                          "catalogo de hoy: hay que replanificar" % unidad_id)
        errores = contrato.validar_request(redactada)
        if errores:
            raise Rechazo("CONTRACT_INVALID", "la request no valida: %s" % errores[0])
        huella = contrato.huella(redactada)
    except Rechazo as r:
        return None, error(r.codigo, r.detalle, catalogo), None, None
    return redactada, None, derivado["leido"], huella


def _request(derivado, clave, pedido_por, execution_id):
    plan, unidad = derivado["plan"], copy.deepcopy(derivado["unidad"])
    meta = plan["meta"]
    referencia = meta.get("task_context_ref") if isinstance(meta.get("task_context_ref"), dict) \
        else {}
    declaracion = derivado["declaracion"]
    return {
        "schema_version": contrato.VERSION_REQUEST,
        "executionId": execution_id,
        "idempotencyKey": derivado["llave"],
        "createdAt": registro.ahora(),
        "requestedBy": pedido_por,
        "taskKey": clave,
        "plan": {"planId": meta.get("plan_id"), "planVersion": meta.get("plan_version"),
                 "planFingerprint": derivado["huellaPlan"],
                 "schemaVersion": meta.get("schema_version")},
        "taskContextRef": {"path": referencia.get("path"),
                           "contextHash": referencia.get("context_hash")},
        "workUnit": unidad,
        "workUnitFingerprint": contrato.huella(unidad),
        "admission": {"planStatus": plan.get("status"),
                      "flow": "DELEGATION_ALLOWED",
                      "agent": {"validation": derivado["validacion"],
                                "type": declaracion.get("type"),
                                "domain": declaracion.get("domain")},
                      "capabilities": "ALL_AVAILABLE",
                      "normativeGate": derivado["decision"],
                      "dependencies": derivado["dependencias"]},
    }


def al_entregar(proyecto, request, adaptador, compuerta=None, cargar_registro=None, huella=None,
                huella_esperada=None):
    """(None, lo derivado) si se puede entregar, o (Rechazo, None). Las quince condiciones sobre
    la request guardada, derivando todo otra vez, y el adaptador: la definicion del agente
    (condicion 10) y las capacidades que provee (13). La condicion 15 excluye a la propia.

    `huella` es la que el motor calculo al crear la request (MD-23). La primera comprobacion de la
    condicion 1 es que la request guardada la tenga: cualquier cambio de su contenido, en la
    WorkUnit, en `admission`, en `requestedBy` o en `createdAt`, la rechaza (MD-11′). Reescribirla
    con el mismo contenido no la cambia, porque `contrato.huella` es de la estructura.

    `huella_esperada` es la del plan a la que esta atado quien pidio la Execution (Task 5, GD-16):
    si viene y `request.plan.planFingerprint` es otra, PLAN_CHANGED en el lugar de la condicion 4.
    Sin ella, igual que antes."""
    compuerta = compuerta or compuerta_por_defecto(proyecto)
    cargar_registro = cargar_registro or registro_agentes.cargar
    try:
        if huella is not None and contrato.huella(request) != huella:                 # 1
            raise Rechazo("CONTRACT_INVALID", "request.json cambio desde que se creo la "
                          "Execution: su huella ya no es la que escribio el motor")
        errores = contrato.validar_request(request)                            # 1
        if errores:
            raise Rechazo("CONTRACT_INVALID", "request.json no valida: %s" % errores[0])
        clave, unidad_id = request["taskKey"], request["workUnit"]["id"]
        _forma(clave, unidad_id, request["requestedBy"])
        derivado = _regla(proyecto, clave, unidad_id, compuerta, cargar_registro, request,
                          adaptador, huella_esperada)
    except Rechazo as r:
        return r, None
    return None, derivado
