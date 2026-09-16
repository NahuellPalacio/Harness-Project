"""El OrchestrationPlan: se arma, se valida, se calcula su estado y se versiona.

Este modulo es la costura entre las dos mitades del bloque. Recibe una PROPUESTA -objetivo,
dominios, unidades, senales: lo que decidio el agente- y hace todo lo que se puede testear:
resolver capacidades, rutear modelo, aplicar la politica, ordenar por dependencias, aislar
el contexto de cada unidad, validar el contrato y escribirlo.

🔴 El estado se CALCULA del contenido. Dejar que lo declare quien arma el plan es dejar que
un plan con huecos diga READY_FOR_EXECUTION, y el estado es justo lo que el bloque
siguiente va a mirar para decidir si arranca.

🔴 Nada de aca ejecuta una unidad de trabajo.
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

VERSION_SCHEMA = "orchestration-plan/1.0"

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

def armar(propuesta, task_context, registro, config, version_harness="", ruta_contexto=""):
    """De una propuesta a un plan completo. No escribe: eso lo hace `escribir`."""
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

    politica = consumo.politica(config)
    perfiles = modelo.perfiles_declarados((config or {}).get("modelRouting"))
    capacidades, huecos = cap.resolver(unidades_propuestas, registro)

    agentes = roster.agentes_para(dominios)
    skills = roster.skills_para(dominios)
    checks = roster.checks_para(dominios)

    aprobaciones = []
    unidades = []
    for propuesta_unidad in unidades_propuestas:
        unidad, aprobacion, politica = _armar_unidad(
            propuesta_unidad, task_context, capacidades, politica, dominios)
        unidades.append(unidad)
        if aprobacion:
            aprobaciones.append(aprobacion)

    orden = orden_de_ejecucion(unidades)

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


def _armar_unidad(propuesta_unidad, task_context, capacidades, politica, dominios_del_plan):
    dominio = str(propuesta_unidad.get("domain") or "")
    senales = list(propuesta_unidad.get("signals") or [])
    if propuesta_unidad.get("requiredCapabilities"):
        faltan = [c for c in propuesta_unidad["requiredCapabilities"]
                  if c in capacidades["missing"]]
        if faltan and "capability_gap" not in senales:
            senales.append("capability_gap")

    ruteo = modelo.enrutar(senales)
    agente = str(propuesta_unidad.get("assignedAgent") or roster.agente_de_dominio(dominio))
    unidad_para_gate = {"id": propuesta_unidad.get("id"), "assignedAgent": agente}
    aprobada, solicitud, presupuesto = consumo.decidir(
        unidad_para_gate, ruteo["requiredTier"], ruteo["reason"], politica)
    politica = dict(politica, sessionBudget=presupuesto)

    if not aprobada:
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
        "context": contexto_para(dominio, task_context),
        "skills": [s["name"] for s in roster.skills_para([dominio])],
        "requiredCapabilities": list(propuesta_unidad.get("requiredCapabilities") or []),
        "applicablePolicies": list(propuesta_unidad.get("applicablePolicies") or []),
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
    return unidad, solicitud, politica


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
    """El estado sale del contenido, no de quien arma el plan."""
    if documento["capabilityGaps"]:
        return "CAPABILITY_RESOLUTION"
    if any(a["status"] == "PENDING" for a in documento["humanApprovals"]):
        return "WAITING_FOR_HUMAN_APPROVAL"
    if any(u["status"] == "BLOCKED" for u in documento["workUnits"]):
        return "CAPABILITY_RESOLUTION"
    return "READY_FOR_EXECUTION"


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
