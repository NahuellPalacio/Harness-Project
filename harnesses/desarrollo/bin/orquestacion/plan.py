"""El OrchestrationPlan: se arma, se valida, se calcula su estado y se versiona.

Este modulo es la costura entre las dos mitades del bloque. Recibe una PROPUESTA -objetivo,
dominios, unidades, senales: lo que decidio el agente- y hace todo lo que se puede testear:
resolver capacidades, rutear modelo, aplicar la politica, ordenar por dependencias, aislar
el contexto de cada unidad, validar el contrato y escribirlo.

🔴 El estado se CALCULA del contenido. Dejar que lo declare quien arma el plan es dejar que
un plan con huecos diga READY_FOR_EXECUTION, y el estado es justo lo que el bloque
siguiente va a mirar para decidir si arranca.

🔴 Nada de aca ejecuta una unidad de trabajo.

🔴 READY_FOR_EXECUTION exige las precondiciones del flujo (docs/cambios/flujo-precondiciones):
repositorio de la tarea resuelto, checkout coincidente, ningun input HARD_BLOCKER sin
resolver y todos los agentes ruteables. Un plan que no las evaluo es BLOCKED.
"""
import datetime
import importlib.util
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from contexto import limpieza                    # noqa: E402
from . import capacidades as cap                 # noqa: E402
from . import consumo                            # noqa: E402
from . import modelo                             # noqa: E402
from . import normativa                          # noqa: E402
from . import roster                             # noqa: E402

VERSION_SCHEMA = "orchestration-plan/2.1"

# Los estados que existen, y son los unicos que el codigo escribe: el del plan sale de
# `estado_de` y el de cada unidad de `_armar_unidad`. El schema 2.1 dice lo mismo, y la regla
# de lectura de un plan guardado los toma de aca. Ninguno habla de delegar ni de ejecutar: el
# estado detallado de la tarea vive en task-flow-state, no aca (integracion-flow-governance-0-31).
ESTADOS_DEL_PLAN = ("BLOCKED", "CAPABILITY_RESOLUTION", "WAITING_FOR_HUMAN_APPROVAL",
                    "READY_FOR_EXECUTION")
ESTADOS_DE_UNIDAD = ("PENDING", "BLOCKED", "WAITING_FOR_HUMAN_APPROVAL")

# Lo que se lee de un plan guardado. Se escribe solo 2.1. Un 2.0 o un 1.0 cuyos estados existen
# en 2.1 es un 2.1 salvo la cadena de version: se lee tal cual y pasa a 2.1 cuando se reescribe.
VERSIONES_LEGIBLES = ("orchestration-plan/2.1", "orchestration-plan/2.0", "orchestration-plan/1.0")

# El input del registro que dice si los agentes del plan se rutean. Una unidad BLOCKED por una
# capacidad tambien lleva `blockers`, asi que el ruteo se lee de los suyos y no de cualquiera.
RUTEO_DE_AGENTES = "agents.routing"

# Que parte del contexto ve cada dominio. Lo que no figura, no viaja — y lo que no viaja se
# declara en `omitted`, porque un aislamiento que no se puede auditar no es un aislamiento.
CONTEXTO_POR_DOMINIO = {
    "backend":      ("acceptance_criteria", "rules", "documents", "repository"),
    "frontend":     ("acceptance_criteria", "documents"),
    "architecture": ("rules", "documents", "repository"),
    "integration":  ("acceptance_criteria", "rules", "repository"),
    "devops":       ("repository",),
    "quality":      ("acceptance_criteria", "repository"),
    "security":     ("rules", "documents", "repository"),
    # Los transversales del roster. Estaban declarados como dominio y no figuraban aca:
    # cualquier unidad suya caia al default y se llevaba el contexto entero en silencio.
    "tooling":       ("repository",),
    "orchestration": ("acceptance_criteria", "rules", "documents", "repository"),
    "refutation":    ("acceptance_criteria", "rules", "documents", "repository"),
}
TODO_EL_CONTEXTO = ("acceptance_criteria", "rules", "documents", "repository")


class PlanInvalido(Exception):
    """El plan no se escribe. Un plan roto con el sello puesto es peor que ninguno."""


class PlanRechazado(PlanInvalido):
    """Un rechazo por un invariante del modelo canonico, y la CLI lo saca con codigo 2.

    Son tres y nada mas: un id de unidad repetido, una unidad de un dominio que no esta en el
    plan, y un plan guardado que la regla de lectura no acepta. Los PlanInvalido de antes -un
    ciclo, una dependencia rota, un plan que no valida- siguen saliendo como salian: mapearlos
    a 2 no evita ningun artefacto y no entra por la regla de inclusion (D15).
    """


def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _armador():
    """`contexto-armar.py`, que trae el validador de subconjunto. Su nombre tiene un guion."""
    ruta = rutas.localizar(("bin", "contexto-armar.py"), __file__)
    if ruta is None:
        return None
    spec = importlib.util.spec_from_file_location("contexto_armar_plan", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def cargar_schema():
    ruta = rutas.localizar(("schemas", "orchestration-plan.schema.json"), __file__)
    if ruta is None:
        raise PlanInvalido(
            "no esta orchestration-plan.schema.json. El plan no se escribe sin poder validarlo.")
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


# -- dependencias --------------------------------------------------------------

def orden_de_ejecucion(unidades):
    """Orden topologico, determinista. Levanta si hay una dependencia rota o un ciclo.

    Determinista importa: dos corridas sobre la misma propuesta tienen que dar el mismo
    orden, o el plan deja de ser comparable consigo mismo.
    """
    ids = [u["id"] for u in unidades]
    conocidos = set(ids)
    for unidad in unidades:
        for dep in unidad.get("dependencies", []):
            if dep not in conocidos:
                raise PlanInvalido(
                    "la unidad %s depende de %s, que no existe en el plan."
                    % (unidad["id"], dep))

    pendientes = {u["id"]: set(u.get("dependencies", [])) for u in unidades}
    orden = []
    while pendientes:
        listos = sorted(uid for uid, deps in pendientes.items() if not deps)
        if not listos:
            enredadas = ", ".join(sorted(pendientes))
            raise PlanInvalido(
                "hay un ciclo de dependencias entre estas unidades: %s. Ninguna puede empezar."
                % enredadas)
        for uid in listos:
            orden.append(uid)
            del pendientes[uid]
        for deps in pendientes.values():
            deps.difference_update(listos)
    return orden


# -- aislamiento de contexto ---------------------------------------------------

def contexto_para(dominio, task_context):
    """Lo que este especialista necesita, y nada mas.

    No es una optimizacion de tokens: es que una unidad de backend no tenga adelante los
    criterios de accesibilidad, porque lo que esta adelante se usa.
    """
    tarea = (task_context or {}).get("task") or {}
    proyecto = (task_context or {}).get("project") or {}
    ficha = proyecto.get("ficha") or {}
    documentacion = (task_context or {}).get("documentation") or {}
    repositorio = (task_context or {}).get("repository") or {}

    # 🔴 Sin dominio conocido no hay aislamiento posible, y el default silencioso era el
    # peor de los mundos: la unidad se llevaba las cuatro categorias y `omitted` salia
    # vacio, indistinguible de un dominio que tiene derecho a todo.
    if dominio not in CONTEXTO_POR_DOMINIO:
        raise PlanInvalido(
            "el dominio '%s' no existe. Los conocidos son: %s. Un dominio que nadie declaro "
            "no tiene un contexto que se le pueda recortar." % (
                dominio, ", ".join(sorted(CONTEXTO_POR_DOMINIO))))

    permitido = CONTEXTO_POR_DOMINIO[dominio]
    fuera = [c for c in TODO_EL_CONTEXTO if c not in permitido]

    contexto = {
        "summary": str(tarea.get("title") or ""),
        "acceptance_criteria": [],
        "rules": [],
        "documents": [],
        "omitted": ["%s: no corresponde al dominio %s" % (c, dominio) for c in fuera],
    }
    if "acceptance_criteria" in permitido:
        contexto["acceptance_criteria"] = list(tarea.get("acceptance_criteria") or [])
    if "rules" in permitido:
        contexto["rules"] = list(ficha.get("rules") or [])
    if "documents" in permitido:
        contexto["documents"] = [str(d.get("doc_id") or "")
                                 for d in (documentacion.get("items") or [])]
    if "repository" in permitido:
        contexto["repository"] = str((repositorio.get("project") or {}).get("name") or "")
    return contexto


# -- el plan -------------------------------------------------------------------

def armar(propuesta, task_context, registro, config, version_harness="", ruta_contexto="",
          precondiciones=None, integraciones=None, fuentes=None):
    """De una propuesta a un plan completo. No escribe: eso lo hace `escribir`.

    `precondiciones` es lo que devuelve `flujo.precondiciones.de_planificacion`: los hechos
    de PLANNING que no salen del plan y la identidad del repositorio. Sin eso el plan se arma
    igual y sale BLOCKED: lo que no se evaluo no pasa.

    `integraciones` es el estado de cada integracion del registro de capacidades: con eso una
    capacidad soportada y caida se distingue de una que no existe. `fuentes` es el
    `harness.fuentes.json` del proyecto: la frescura de lo que el plan exige (Wave 5).
    """
    clave = str((task_context.get("meta") or {}).get("task_key") or "")
    dominios = sorted(set(propuesta.get("domains") or []))
    # Los dominios del plan se validan igual que el de cada unidad. No hay fuga de
    # contexto por aca -`domains` no elige que ve nadie- pero un plan que declara un
    # dominio inventado y unidades en otro es un plan que dice dos cosas.
    for dominio in dominios:
        if dominio not in CONTEXTO_POR_DOMINIO:
            raise PlanInvalido(
                "el plan declara el dominio '%s', que no existe. Los conocidos son: %s."
                % (dominio, ", ".join(sorted(CONTEXTO_POR_DOMINIO))))
    unidades_propuestas = propuesta.get("workUnits") or []
    if not unidades_propuestas:
        raise PlanInvalido("la propuesta no trae ninguna unidad de trabajo.")

    # 🔴 El id es la identidad de la unidad: con el se arman las dependencias, el orden, las
    # aprobaciones y las unidades de la refutacion. Dos unidades con el mismo id colapsaban
    # en silencio en `orden_de_ejecucion`, y el plan escrito tenia una que nadie podia nombrar.
    # Se normaliza como lo hace `_armar_unidad`, que es el id que se escribiria.
    vistos, repetidos = set(), []
    for propuesta_unidad in unidades_propuestas:
        uid = str(propuesta_unidad.get("id") or "")
        if uid in vistos and uid not in repetidos:
            repetidos.append(uid)
        vistos.add(uid)
    if repetidos:
        raise PlanRechazado(
            "la propuesta repite el id de unidad %s. El id es lo que identifica a una unidad: "
            "dos con el mismo no se pueden distinguir." % ", ".join("'%s'" % r for r in repetidos))

    # El dominio de cada unidad tiene que estar entre los del plan. `domains` es lo que decide
    # que especialistas participan (el schema lo dice): una unidad de otro dominio mete a uno
    # que, segun el mismo plan, no participa.
    for propuesta_unidad in unidades_propuestas:
        dominio = str(propuesta_unidad.get("domain") or "")
        if dominio not in dominios:
            raise PlanRechazado(
                "la unidad '%s' es del dominio '%s', que no esta entre los dominios del plan: "
                "%s. Agregalo a `domains` o cambiale el dominio a la unidad." % (
                    str(propuesta_unidad.get("id") or ""), dominio,
                    ", ".join(dominios) or "ninguno"))

    politica = consumo.politica(config)
    perfiles = modelo.perfiles_declarados((config or {}).get("modelRouting"))
    capacidades, huecos = cap.resolver(unidades_propuestas, registro, integraciones=integraciones)
    estado_de_capacidades = cap.estado(unidades_propuestas, registro, integraciones=integraciones)
    no_soportadas = set(h["capability"] for h in huecos)

    agentes = roster.agentes_para(dominios)
    skills = roster.skills_para(dominios)
    checks = roster.checks_para(dominios)

    aprobaciones = []
    unidades = []
    for propuesta_unidad in unidades_propuestas:
        unidad, aprobacion, politica = _armar_unidad(
            propuesta_unidad, task_context, capacidades, politica, dominios, no_soportadas)
        unidades.append(unidad)
        if aprobacion:
            aprobaciones.append(aprobacion)

    orden = orden_de_ejecucion(unidades)
    precondiciones_del_flujo = _precondiciones(precondiciones, unidades)
    if precondiciones is not None:
        # Una fuente para el repositorio de la tarea (Wave 6): la identidad del flujo, la que usa
        # la compuerta y la que resuelve conflictos y elecciones de la persona. Sin identidad
        # resuelta, nada: no se completa con un nombre que la identidad no confirmo.
        repositorio = (precondiciones_del_flujo.get("repository") or {}).get("taskRepository")
        for unidad in unidades:
            if "repository" in (unidad.get("context") or {}):
                unidad["context"]["repository"] = str(repositorio or "")

    avisos = roster.huecos(agentes, skills, checks)
    aviso_matriz = normativa.aviso_de_matriz()
    if aviso_matriz:
        avisos.append(aviso_matriz)
    sin_declarar = [p["tier"] for p in perfiles if not p["declared"]]
    if sin_declarar:
        avisos.append(
            "no hay modelo declarado para %s: el perfil existe y nadie dijo con que modelo se "
            "resuelve. No se inventa uno." % ", ".join(sin_declarar))
    if capacidades["missing"]:
        avisos.append(
            "las capacidades locales del roster son una declaracion, no una comprobacion: "
            "nadie verifico que la sesion tenga habilitada la herramienta que las provee.")
    for d in estado_de_capacidades:
        if d["availability"] == "SUPPORTED_UNAVAILABLE":
            avisos.append(
                "%s esta soportada pero %s no esta disponible (%s): no se construye una tool, se "
                "revalida la integracion." % (d["capabilityId"], d["integration"], d["reasonCode"]))
    from . import frescura
    from . import refutacion
    conocimiento = frescura.de_la_operacion(fuentes, refutacion.estandares_de_unidades(unidades))
    for f in conocimiento:
        if f["blocking"]:
            avisos.append("la fuente %s esta en %s: el plan no avanza hasta revisarla."
                          % (f["standard"], f["state"]))
        elif not f["verified"]:
            avisos.append("la fuente %s no esta verificada como vigente (%s): el plan la usa, "
                          "pero no como CURRENT." % (f["standard"], f["state"]))

    documento = {
        "meta": {
            "schema_version": VERSION_SCHEMA,
            "plan_id": "pln_" + clave,
            "plan_version": 1,
            "generated_at": ahora(),
            "harness_version": version_harness,
            "task_key": clave,
            "task_context_ref": {
                "path": ruta_contexto,
                "context_hash": str((task_context.get("meta") or {}).get("context_hash") or ""),
            },
        },
        "objective": str(propuesta.get("objective") or ""),
        "domains": dominios,
        "applicableStandards": normativa.aplicables(dominios),
        "agents": agentes,
        "skills": skills,
        "checks": checks,
        "capabilities": capacidades,
        "capabilityGaps": huecos,
        "capabilityStatus": estado_de_capacidades,
        "knowledgeSources": conocimiento,
        "policies": list(propuesta.get("policies") or []),
        "workUnits": unidades,
        "executionOrder": orden,
        "modelRouting": {
            "runtime": _runtime(config),
            "profiles": perfiles,
            "defaultTier": "low_cost",
        },
        "consumptionPolicy": politica,
        "humanApprovals": aprobaciones,
        "flowPreconditions": precondiciones_del_flujo,
        "planHistory": [{
            "planVersion": 1,
            "changes": ["plan inicial"],
            "reason": "primera planificacion de %s" % clave,
            "timestamp": ahora(),
            "trigger": "task-context",
        }],
        "warnings": avisos,
        "status": "PLANNING",
    }
    documento["status"] = estado_de(documento)
    _limpiar(documento)
    return documento


def _armar_unidad(propuesta_unidad, task_context, capacidades, politica, dominios_del_plan,
                  no_soportadas=None):
    dominio = str(propuesta_unidad.get("domain") or "")
    senales = list(propuesta_unidad.get("signals") or [])
    if propuesta_unidad.get("requiredCapabilities"):
        # La senal es de construir una tool: solo por lo que no se soporta. Lo soportado y caido
        # bloquea la unidad igual, mas abajo, pero no pide una tool nueva.
        faltan = [c for c in propuesta_unidad["requiredCapabilities"]
                  if c in capacidades["missing"]
                  and (no_soportadas is None or c in no_soportadas)]
        if faltan and "capability_gap" not in senales:
            senales.append("capability_gap")

    ruteo = modelo.enrutar(senales)
    agente = str(propuesta_unidad.get("assignedAgent") or roster.agente_de_dominio(dominio))
    ruteable = _ruteo_de_agente(agente)
    skills_del_dominio = roster.skills_para([dominio])
    unidad_para_gate = {"id": propuesta_unidad.get("id"), "assignedAgent": agente}
    aprobada, solicitud, presupuesto = consumo.decidir(
        unidad_para_gate, ruteo["requiredTier"], ruteo["reason"], politica)
    politica = dict(politica, sessionBudget=presupuesto)

    if not ruteable["routable"]:
        # Ruteo cerrado: un agente que el registro no rutea no recibe trabajo, y ninguna
        # aprobacion lo arregla. No se le pregunta a nadie: es DERIVABLE del registro.
        estado = "BLOCKED"
    elif not aprobada:
        estado = "WAITING_FOR_HUMAN_APPROVAL"
    elif any(c in capacidades["missing"]
             for c in propuesta_unidad.get("requiredCapabilities", [])):
        estado = "BLOCKED"
    else:
        estado = "PENDING"

    unidad = {
        "id": str(propuesta_unidad.get("id") or ""),
        "objective": str(propuesta_unidad.get("objective") or ""),
        "domain": dominio,
        "assignedAgent": agente,
        # 🔴 La unidad lo dice, no solo el aviso del plan. Quien lee una unidad suelta
        # -que es como la va a recibir un especialista- tiene que poder saber que el
        # agente al que esta asignada todavia no existe, sin ir a buscar la lista de
        # avisos tres niveles mas arriba.
        "agentExists": bool(agente) and roster.existe_agente(agente),
        # Que dijo el registro, no solo si existe. Un `false` puede ser un archivo que
        # falta, un id que no coincide o un especialista sin skills instaladas, y quien
        # recibe la unidad suelta no tiene como distinguirlos mirando un booleano.
        "agentValidation": roster.validacion_de_agente(agente),
        "context": contexto_para(dominio, task_context),
        "skills": [s["name"] for s in skills_del_dominio],
        # El contrato viejo era una lista de nombres y sigue siendolo: `skills` no cambia
        # de tipo. Al lado va el estado de cada una, que es lo que permite ver que
        # `dev-miba` esta declarada y todavia no se puede usar sin que parezca que falta.
        "skillStates": [{"id": s["name"], "status": s.get("status", ""),
                         "validation": s.get("validation", "")}
                        for s in skills_del_dominio],
        "requiredCapabilities": list(propuesta_unidad.get("requiredCapabilities") or []),
        "applicablePolicies": list(propuesta_unidad.get("applicablePolicies") or []),
        # Que reglas de §7.1 le aplican, cuales no y cuales no se pudieron decidir. Las
        # senales entran como booleanos explicitos -la forma vieja- o como documentos con su
        # evidencia y su productor; lo que no viene queda sin resolver, nunca en "no aplica".
        # El valor resuelto y su evidencia viajan en `normative.signals`.
        "normative": normativa.resolucion(propuesta_unidad.get("normativeSignals") or {},
                                          evidencia=propuesta_unidad.get("normativeEvidence")),
        "requiredChecks": [c["name"] for c in roster.checks_para([dominio])],
        "dependencies": list(propuesta_unidad.get("dependencies") or []),
        "modelPolicy": {
            "mode": politica["mode"],
            "requiredTier": ruteo["requiredTier"],
            "allowEscalation": bool(propuesta_unidad.get("allowEscalation", True)),
            "maxTierWithoutApproval": consumo.techo_sin_aprobacion(politica),
            "reason": ruteo["reason"],
            "signals": ruteo["signals"],
        },
        "status": estado,
    }
    if estado == "BLOCKED":
        # 🔴 En 2.1 toda unidad BLOCKED dice por que, con el input y el codigo de quien lo decidio.
        # El schema no puede exigirlo (no hay if/then en el validador): lo exigen este productor y
        # la regla de lectura.
        unidad["blockers"] = _bloqueos_de_unidad(
            ruteable, propuesta_unidad.get("requiredCapabilities") or [], capacidades,
            no_soportadas)
    return unidad, solicitud, politica


def _bloqueos_de_unidad(ruteable, requeridas, capacidades, no_soportadas):
    """Los blockers de una unidad BLOCKED: el ruteo primero, despues cada clase de capacidad."""
    bloqueos = []
    if not ruteable["routable"]:
        bloqueos.append({"inputId": RUTEO_DE_AGENTES, "code": ruteable["result"]})
    faltan = [c for c in requeridas if c in capacidades["missing"]]
    if any(no_soportadas is None or c in no_soportadas for c in faltan):
        bloqueos.append({"inputId": "plan.capabilityGaps", "code": "CAPABILITY_GAP"})
    if any(no_soportadas is not None and c not in no_soportadas for c in faltan):
        bloqueos.append({"inputId": "plan.capabilityStatus", "code": "CAPABILITY_UNAVAILABLE"})
    return bloqueos


def ruteo_bloqueado(unidades):
    """Si alguna unidad tiene un agente que el registro no rutea. Solo cuentan sus blockers de
    ruteo: una unidad BLOCKED por una capacidad no dice nada del ruteo."""
    return any(isinstance(b, dict) and b.get("inputId") == RUTEO_DE_AGENTES
               for u in unidades or [] for b in (u.get("blockers") or []))


def _ruteo_de_agente(agente):
    """La validacion canonica del Agent Registry. Sin registro no se rutea nada."""
    from . import registro_agentes
    try:
        return registro_agentes.resolver_ruteo(agente)
    except registro_agentes.RegistroInvalido:
        return {"requestedAgent": agente, "result": "AGENT_NOT_FOUND", "routable": False}


def _precondiciones(precondiciones, unidades):
    """flowPreconditions: la evaluacion de PLANNING, con el ruteo de agentes que sabe el plan."""
    from flujo import precondiciones as flujo
    from flujo import requeridos
    hechos = dict((precondiciones or {}).get("facts") or {})
    hechos[RUTEO_DE_AGENTES] = not ruteo_bloqueado(unidades)
    try:
        evaluacion = flujo.evaluar(flujo.PLANNING, hechos)
    except requeridos.RegistroInvalido as e:
        raise PlanInvalido("no se pueden evaluar las precondiciones del flujo: %s" % e)
    evaluacion["repository"] = (precondiciones or {}).get("repository")
    return evaluacion


def _runtime(config):
    """Lo que se sabe del runtime. `detected` dice si lo dijo el runtime o lo declaro alguien."""
    declarado = ((config or {}).get("llmRuntime") or {})
    return {
        "provider": str(declarado.get("provider") or "desconocido"),
        "version": str(declarado.get("version") or ""),
        "detected": bool(declarado.get("detected", False)),
    }


# Todo menos `meta`, que lo escribe este modulo y no tiene texto de afuera.
#
# 🔴 La primera version limpiaba cuatro campos por nombre y dejaba afuera `planHistory`,
# asi que un token escrito con `--motivo` quedaba en claro en el plan. Es EXACTAMENTE el
# error que el Bloque 2 ya habia cometido y corregido un bloque antes: limpiar por lista
# obliga a acordarse una vez por campo, para siempre, y el campo numero veinte lo escribe
# alguien que no leyo la discusion. La leccion no era "agregar planHistory a la lista".
# Lo unico que NO se limpia. `meta` lo escribe este modulo entero: no hay texto de afuera
# adentro, y el hash se calcula sobre lo demas.
SIN_LIMPIAR = ("meta",)


def _limpiar(documento):
    """Redacta el documento entero, en su lugar. Todo menos `meta`.

    🔴 Se recorren las claves DEL DOCUMENTO, no una lista escrita a mano. La primera
    version tenia una lista de cuatro nombres y `planHistory` no estaba, asi que un token
    en un `--motivo` quedaba en claro en el plan. La segunda tenia una lista de dieciseis:
    cubria todo lo de hoy, y una seccion nueva manana se escapaba igual. La leccion no era
    "hacer la lista mas larga" — era que una lista de nombres obliga a acordarse una vez
    por campo, para siempre.
    """
    catalogo = limpieza.cargar_catalogo()
    if catalogo is None:
        return
    nuevos = []
    for clave in [c for c in documento if c not in SIN_LIMPIAR]:
        limpio, hallazgos = limpieza.redactar_arbol(documento[clave], catalogo, "$." + clave)
        documento[clave] = limpio
        nuevos.extend(hallazgos)
    documento["warnings"].extend(nuevos)


# -- estado, validacion y escritura --------------------------------------------

def estado_de(documento):
    """El estado sale del contenido, no de quien arma el plan.

    🔴 Las precondiciones van primero y se recalculan de sus preguntas: un `status: READY`
    escrito a mano al lado de una pregunta bloqueante no hace pasar nada.
    """
    previas = documento.get("flowPreconditions")
    if not isinstance(previas, dict) or previas.get("status") != "READY" or any(
            p.get("blocking") for p in previas.get("questions") or []):
        return "BLOCKED"
    # Una integracion caida o una fuente con un problema de integridad no se resuelven
    # construyendo nada: el plan queda BLOCKED, no en CAPABILITY_RESOLUTION (Wave 5).
    if no_disponibles(documento) or fuentes_que_bloquean(documento):
        return "BLOCKED"
    if documento["capabilityGaps"]:
        return "CAPABILITY_RESOLUTION"
    if any(a["status"] == "PENDING" for a in documento["humanApprovals"]):
        return "WAITING_FOR_HUMAN_APPROVAL"
    if any(u["status"] == "BLOCKED" for u in documento["workUnits"]):
        return "CAPABILITY_RESOLUTION"
    return "READY_FOR_EXECUTION"


def no_disponibles(documento):
    """Las capacidades que el plan pide, soportadas y no disponibles. Un plan de antes de la
    Wave 5 no trae capabilityStatus: no hay ninguna."""
    return [d for d in documento.get("capabilityStatus") or []
            if d.get("availability") == "SUPPORTED_UNAVAILABLE"]


def huecos_de_un_plan_viejo(documento):
    """Los huecos de un plan de antes de la Wave 5 -sin capabilityStatus- que son capacidades
    soportadas: ese plan derivo a dev-tool-builder una integracion caida. No es un hueco: el plan
    quedo viejo y se regenera."""
    if "capabilityStatus" in documento:
        return []
    soportadas = cap.registro_de_capacidades.soporte()
    return [h for h in documento.get("capabilityGaps") or [] if h.get("capability") in soportadas]


def fuentes_que_bloquean(documento):
    """Las fuentes que el plan exige y que tenian un problema de integridad al armarlo."""
    return [f for f in documento.get("knowledgeSources") or [] if f.get("blocking")]


def validar(documento):
    armador = _armador()
    if armador is None:
        raise PlanInvalido(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def escribir(documento, ruta):
    errores = validar(documento)
    if errores:
        raise PlanInvalido(
            "el plan no valida contra %s:\n  - %s" % (VERSION_SCHEMA, "\n  - ".join(errores[:5])))
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return ruta


# -- la lectura de un plan guardado --------------------------------------------

def aceptar_guardado(documento, clave=""):
    """La regla de lectura de un plan guardado: una sola, para `refute --compile` y para
    `--replanificar`. Devuelve el documento tal cual o levanta PlanRechazado.

    Se lee un 2.1, o un 2.0 o un 1.0 cuyo `status` y los de todas sus unidades existen en 2.1.
    Nada se convierte, nada se escribe y el documento no se toca: pasa a 2.1 recien cuando
    alguien lo reescribe. Un 2.1 ademas dice por que esta BLOCKED cada unidad que lo esta; un
    2.0 o un 1.0 no, porque esa exigencia nacio con 2.1.

    🔴 Un estado que no existe en 2.1 no se migra. No hay un estado 2.0 que signifique
    "delegando", y elegir uno parecido es hacerle decir al plan algo que no dice. La salida
    es regenerarlo, y el mensaje lo dice.

    `clave` es la de quien lo pide, para el mensaje: se usa si el plan no trae la suya.
    """
    meta = documento.get("meta") if isinstance(documento, dict) else None
    meta = meta if isinstance(meta, dict) else {}
    clave = str(meta.get("task_key") or clave or "<KEY>")
    regenerar = "Hay que regenerarlo con `dev-harness.py plan %s --propuesta ...`." % clave

    version = meta.get("schema_version")
    if version in (None, ""):
        raise PlanRechazado(
            "el plan guardado de %s no dice su version: falta `meta.schema_version`. Se leen "
            "%s. %s" % (clave, " y ".join(VERSIONES_LEGIBLES), regenerar))
    if version not in VERSIONES_LEGIBLES:
        raise PlanRechazado(
            "el plan guardado de %s es `%s`, y se leen solo %s. %s"
            % (clave, version, " y ".join(VERSIONES_LEGIBLES), regenerar))

    # Las tres versiones pasan por aca: el 1.0 declaraba validos estados que el 2.1 no tiene.
    estado = documento.get("status")
    if estado not in ESTADOS_DEL_PLAN:
        raise PlanRechazado(
            "el plan guardado de %s tiene `status: %s`, un estado que no existe en %s. Los de un "
            "plan son %s, y no se convierte a ninguno. %s" % (
                clave, _valor(estado), VERSION_SCHEMA, ", ".join(ESTADOS_DEL_PLAN), regenerar))
    unidades = documento.get("workUnits")
    for i, unidad in enumerate(unidades if isinstance(unidades, list) else []):
        unidad = unidad if isinstance(unidad, dict) else {}
        if unidad.get("status") not in ESTADOS_DE_UNIDAD:
            raise PlanRechazado(
                "la unidad '%s' del plan guardado de %s tiene `workUnits[%d].status: %s`, un "
                "estado que no existe en %s. Los de una unidad son %s, y no se convierte a "
                "ninguno. %s" % (
                    str(unidad.get("id") or ""), clave, i, _valor(unidad.get("status")),
                    VERSION_SCHEMA, ", ".join(ESTADOS_DE_UNIDAD), regenerar))
        if (version == VERSION_SCHEMA and unidad.get("status") == "BLOCKED"
                and not _bloqueos_validos(unidad.get("blockers"))):
            raise PlanRechazado(
                "la unidad '%s' del plan guardado de %s esta BLOCKED y no dice por que: "
                "`workUnits[%d].blockers` falta o esta vacio. En %s una unidad BLOCKED lleva sus "
                "blockers. %s" % (str(unidad.get("id") or ""), clave, i, VERSION_SCHEMA, regenerar))
    return documento


def _bloqueos_validos(bloqueos):
    """Una lista no vacia de blockers, cada uno con su input y su codigo."""
    return isinstance(bloqueos, list) and bool(bloqueos) and all(
        isinstance(b, dict) and b.get("inputId") and b.get("code") for b in bloqueos)


def _valor(valor):
    """Un valor para el mensaje. Uno ausente se dice, no se imprime `None`."""
    return "(vacio)" if valor in (None, "") else str(valor)


def replanificar(documento, cambios, motivo, disparador):
    """Sube la version y deja escrito por que. Un plan que cambia solo no se puede auditar."""
    if not motivo:
        raise PlanInvalido("una replanificacion sin motivo es un plan que cambio solo.")
    documento = json.loads(json.dumps(documento))
    documento["meta"]["plan_version"] += 1
    documento["meta"]["generated_at"] = ahora()
    documento["planHistory"].append({
        "planVersion": documento["meta"]["plan_version"],
        "changes": list(cambios),
        "reason": motivo,
        "timestamp": ahora(),
        "trigger": disparador,
    })
    documento["status"] = estado_de(documento)
    # 🔴 Aca, y no antes. El motivo y los cambios los escribio una persona en la linea de
    # comandos: no pasaron por la limpieza de `armar` porque todavia no existian. Un PAT
    # en un `--motivo` quedaba en claro en el plan escrito.
    _limpiar(documento)
    return documento
