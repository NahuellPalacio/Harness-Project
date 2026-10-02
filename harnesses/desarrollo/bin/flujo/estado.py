"""El estado del flujo de una tarea: en que etapa esta, en que condicion y que la frena.

    derivar(proyecto, clave)     el estado de ahora, armado de las fuentes que mandan
    leer(proyecto, clave)        el guardado, o por que no sirve
    vigencia(guardado, derivado) que cambio desde que se guardo
    vigencia_local(guardado, p)  lo mismo, sin `.env` ni git: la que leen los hooks
    permisos(estado, vigencia)   que se puede hacer; no se guarda nunca
    puede_avanzar(...)           la condicion de todo permiso de avance
    reanudar_desde(...)          la etapa mas temprana desde la que se retoma
    validar_transicion(...)      un estado no se declara: se reevalua
    texto(...)                   lo que ve la persona, en espanol

🔴 Es DERIVADO. No manda sobre el TaskContext, el plan, la identidad del repositorio, la
configuracion ni la refutacion: los referencia por ruta, hash y huella. Si el archivo se
borra, `derivar` da el mismo estado logico. Sin ningun artefacto la tarea esta en CONTEXT,
nunca lista.

🔴 Este modulo no escribe: `flujo/` no abre nada para escribir (E-18 de
docs/cambios/flujo-precondiciones). Guardar es de `estado_de_tarea/persistencia.py`.

Nada de aca sale a la red ni llama a un modelo. Lee archivos del proyecto, el `.env` por
`entorno.resolver` y `git remote -v`.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import precondiciones                              # noqa: E402
from . import repositorio                                 # noqa: E402
from . import requeridos                                  # noqa: E402

VERSION = "task-flow-state/1.0"
VERSION_ACTIVA = "active-task/1.0"
SCHEMA = "task-flow-state.schema.json"

STAGES = ("CONTEXT", "PLANNING", "EXECUTION", "VERIFICATION", "REFUTATION", "COMPLETION")
STATUSES = ("NEW", "ACTIVE", "BLOCKED", "WAITING_FOR_HUMAN_APPROVAL", "INCOMPLETE", "FAILED",
            "COMPLETED", "CANCELLED")
BLOQUEADOS = ("BLOCKED", "WAITING_FOR_HUMAN_APPROVAL")
TERMINALES = ("COMPLETED", "CANCELLED")
AVANZAN = ("NEW", "ACTIVE", "INCOMPLETE", "FAILED")

AVANCE = ("planningAllowed", "delegationAllowed", "implementationAllowed", "refutationAllowed",
          "completionAllowed")
RECUPERACION = ("inspectState", "renderPendingInteraction", "locatePersistentInput", "validate",
                "revalidate", "cancel")

INVALIDO = "TASK_FLOW_STATE_INVALID"
AUSENTE = "TASK_FLOW_STATE_MISSING"
TRANSICION = "FLOW_TRANSITION_INVALID"

TASK_CONTEXT_STALE = "TASK_CONTEXT_STALE"
PLAN_STALE = "PLAN_STALE"
REPOSITORY_STATE_STALE = "REPOSITORY_STATE_STALE"
REFUTATION_STATE_STALE = "REFUTATION_STATE_STALE"

LISTO = "READY_FOR_EXECUTION"
CLAVE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")

# Los bloqueos que no salen del registro de inputs, con el codigo que ya existia.
# (codigo) -> (inputId, clasificacion, interaccion, fuente, etapa)
_PROPIOS = {
    "CONTEXT_STALE": ("planning.taskContext", "DERIVABLE", None, "task-flow-state", "PLANNING"),
    "CAPABILITY_GAP": ("plan.capabilityGaps", "DERIVABLE", None, "orchestration-plan", "PLANNING"),
    "HUMAN_APPROVAL_PENDING": ("plan.humanApprovals", "HARD_BLOCKER", "HUMAN_DECISION",
                               "orchestration-plan", "PLANNING"),
    "PLAN_NOT_READY": ("plan.status", "DERIVABLE", None, "orchestration-plan", "PLANNING"),
    "REFUTATION_PLAN_STALE": ("refutation.compile", "DERIVABLE", None, "atomic-refutation",
                              "REFUTATION"),
    # Un run.json que esta y no se lee: el codigo de 0.23.0 para una salida que no sirve.
    "REFUTATION_OUTPUT_INVALID": ("refutation.compile", "DERIVABLE", None, "atomic-refutation",
                                  "REFUTATION"),
}
# Jira configurado en el `.env` pero la ultima sonda del registro de capacidades fallo: CONTEXT no
# avanza, con el estado del adapter como codigo. Se revalida con `flujo <KEY> --resume`.
_JIRA_NO_DISPONIBLE = ("AUTHENTICATION_FAILED", "CONNECTION_FAILED", "PERMISSION_DENIED")
for _codigo in _JIRA_NO_DISPONIBLE:
    _PROPIOS[_codigo] = ("jira.availability", "HARD_BLOCKER", None, "task-flow-state", "CONTEXT")
# Wave 5. Un plan que pide una capacidad soportada cuya integracion esta caida: no es un hueco que
# se deriva, es una integracion que hay que revalidar (`flujo <KEY> --resume`).
CAPACIDAD_NO_DISPONIBLE = "CAPABILITY_UNAVAILABLE"
_PROPIOS[CAPACIDAD_NO_DISPONIBLE] = ("plan.capabilityStatus", "HARD_BLOCKER", None,
                                     "orchestration-plan", "PLANNING")
# Wave 5. Una fuente que el plan exige con un problema de integridad lleva su estado como codigo.
# La lista es la de `frescura.BLOQUEAN_OPERACION`, la misma que frena `plan` y `refute --compile`:
# se lee de ahi, en `_bloqueo_propio`, y no se repite aca.
_DE_LA_FUENTE = ("plan.knowledgeSources", "HARD_BLOCKER", None, "orchestration-plan", "PLANNING")


class ErrorDeEstado(Exception):
    """Lleva el codigo canonico adelante. Nunca un pedazo de un artefacto."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


# -- las compuertas ------------------------------------------------------------

def gate_de(input_id):
    """`repository.match` -> `repository-match`; `planning.taskContext` -> `planning-task-context`.

    Sale del inputId y no de un campo del registro: flow-required-inputs/1.0 cierra sus claves.
    """
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(input_id)).replace(".", "-").lower()


def _compuertas():
    propias = set(gate_de(v[0]) for v in _PROPIOS.values())
    try:
        return frozenset(propias | set(gate_de(e["inputId"]) for e in requeridos.cargar()["inputs"]))
    except requeridos.RegistroInvalido:
        return frozenset(propias)


GATES = _compuertas()


# -- rutas y lectura -----------------------------------------------------------

def validar_clave(clave):
    clave = str(clave or "")
    if not CLAVE.match(clave):
        raise ErrorDeEstado("TASK_KEY_INVALID", "`%s` no es una clave de tarea." % clave)
    return clave


def ruta(proyecto, clave):
    return os.path.join(proyecto, ".claude", "runtime", "tasks", validar_clave(clave), "state.json")


def ruta_activa(proyecto):
    return os.path.join(proyecto, ".claude", "runtime", "active-task.json")


def _relativas(clave):
    return {"context": ".claude/contextos/%s.json" % clave,
            "plan": ".claude/planes/%s.json" % clave,
            "run": ".claude/refutaciones/%s/run.json" % clave}


def _leer_json(ruta_):
    """(documento, error). Ausente es (None, None)."""
    if not os.path.isfile(ruta_):
        return None, None
    try:
        with io.open(ruta_, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        return None, str(e)
    return (doc, None) if isinstance(doc, dict) else (None, "no es un objeto")


def validar(doc, definicion=None):
    """Errores contra task-flow-state/1.0, o contra uno de sus `$defs`. Vacio es valido."""
    from orquestacion import refutacion
    return refutacion.validar(doc, SCHEMA, definicion, desde=__file__)


def leer(proyecto, clave):
    """(estado, None), (None, None) si no hay, o (None, TASK_FLOW_STATE_INVALID).

    Un estado roto no se usa ni se repara aca: se dice, y lo reemplaza la proxima
    reconciliacion. Tratarlo como listo seria el peor default posible.
    """
    doc, error = _leer_json(ruta(proyecto, clave))
    if doc is None and error is None:
        return None, None
    if error or validar(doc) or doc.get("taskKey") != clave:
        return None, INVALIDO
    return doc, None


def logico(doc):
    """El estado sin `updatedAt`: lo que se compara para saber si algo cambio."""
    return dict((k, v) for k, v in (doc or {}).items() if k != "updatedAt")


def difiere(guardado, derivado):
    """Si reconciliar cambiaria lo que aplica la compuerta: la etapa, el estado o los bloqueos."""
    def _clave(doc):
        return (doc.get("stage"), doc.get("status"),
                [(b["code"], b["inputId"]) for b in doc.get("blockedOn") or []])
    return _clave(guardado or {}) != _clave(derivado or {})


def texto_de_revalidacion(derivado):
    """Lo que diria el estado si se reconciliara ahora, y el comando que lo aplica."""
    bloqueos = ", ".join("%s %s" % (b["blockerId"], b["code"]) for b in derivado.get("blockedOn") or [])
    return ("Revalidado ahora       %s / %s · bloqueos: %s · vista previa, no aplicado\n"
            "                       La compuerta aplica lo guardado, de arriba. Para revalidar y "
            "aplicarlo: `python .claude/harness/bin/desarrollo/dev-harness.py flujo %s --resume`." % (
                derivado.get("stage"), derivado.get("status"), bloqueos or "ninguno",
                derivado.get("taskKey")))


def texto_sin_autoridad(clave, codigo):
    """Sin estado guardado, o con uno roto, no hay autoridad que mostrar: se dice con su codigo."""
    return ("%s no tiene un estado del flujo guardado que se pueda aplicar [%s]. Lo que se "
            "derivaría ahora es una vista previa, no aplicado; lo aplica "
            "`python .claude/harness/bin/desarrollo/dev-harness.py flujo %s --resume`." % (
                clave, codigo, clave))


# -- derivar -------------------------------------------------------------------

def _entorno(proyecto, proceso):
    """(bloque gitlab publico, Resolucion). De solo lectura: no escribe la proyeccion."""
    from integraciones import entorno
    rutas_ = (os.path.join(proyecto, ".env"),
              os.path.join(proyecto, ".claude", "harness.integraciones.json"))
    resolucion = entorno.resolver(entorno.cargar_contrato(), rutas_[0], rutas_[1], entorno=proceso)
    return resolucion.de("gitlab"), resolucion


def _hechos_de_contexto(registro, resolucion, clave):
    """CONTEXT: la clave, y si cada variable del `.env` que pide la etapa esta y sirve."""
    hechos = {}
    for entrada in requeridos.de_etapa(registro, "CONTEXT"):
        destino = entrada["persistentTarget"]
        if entrada["inputId"] == "task.key":
            hechos["task.key"] = bool(clave)
        elif destino and destino["format"] == "dotenv":
            hechos[entrada["inputId"]] = _variable_resuelta(resolucion, destino["key"])
        else:
            hechos[entrada["inputId"]] = False
    return hechos


def _variable_resuelta(resolucion, nombre):
    for integ in resolucion.integraciones.values():
        if integ.bandera == nombre:
            return bool(integ.habilitada)
        for v in integ.variables:
            if v.nombre == nombre:
                return bool(v.presente and v.valida)
    return False


def _capacidades_de_ahora(proyecto):
    """El bloque `capacidades` del registro escrito, o {}."""
    doc, _ = _leer_json(os.path.join(proyecto, ".claude", "harness.capacidades.json"))
    return (doc or {}).get("capacidades") or {}


def _explicaciones_del_plan(proyecto, plan, orq_plan):
    """(bloqueos, viejo): lo que frena al plan y no es del plan (Wave 5), mirado AHORA.

    Una capacidad soportada y caida, o una fuente que el plan exige con un problema de integridad,
    son bloqueos propios. Si lo que lo frenaba al armarlo ya no esta -la integracion volvio, la
    alerta se resolvio-, el plan quedo viejo y hay que regenerarlo.
    """
    from orquestacion import frescura
    from orquestacion import refutacion
    bloqueos, viejo = [], False
    caidas = orq_plan.no_disponibles(plan)
    if caidas:
        ahora = _capacidades_de_ahora(proyecto)
        if all(ahora.get(d.get("capabilityId")) == "ENABLED" for d in caidas):
            viejo = True
        else:
            bloqueos.append(_bloqueo_propio(CAPACIDAD_NO_DISPONIBLE))
    de_ahora = frescura.de_la_operacion(
        frescura.leer(frescura.ruta_por_defecto(proyecto)),
        refutacion.estandares_de_unidades(plan.get("workUnits") or []))
    codigos = sorted(set(f["state"] for f in de_ahora if f["blocking"]))
    bloqueos += [_bloqueo_propio(c) for c in codigos]
    if not codigos and orq_plan.fuentes_que_bloquean(plan):
        viejo = True
    if orq_plan.huecos_de_un_plan_viejo(plan):
        viejo = True           # un plan de antes de la Wave 5 derivo algo que esta soportado
    return bloqueos, viejo


def _estado_de_jira(proyecto):
    """El estado de Jira en el registro de capacidades (harness.capacidades.json), o None.
    Lo escribe la sonda de `estado`/`setup`/`reconfigurar`/`flujo --resume`; aca solo se lee."""
    doc, _ = _leer_json(os.path.join(proyecto, ".claude", "harness.capacidades.json"))
    return (((doc or {}).get("integraciones") or {}).get("jira") or {}).get("estado")


def _config_harness(proyecto):
    doc, _ = _leer_json(os.path.join(proyecto, ".claude", "harness.config.json"))
    return doc or {}


def _repo_min(identidad):
    if not isinstance(identidad, dict):
        return None
    return {"status": identidad.get("status"), "failureCode": identidad.get("failureCode"),
            "taskRepository": identidad.get("taskRepository"),
            "localRepositories": sorted(identidad.get("localRepositories") or [])}


def _bloqueo_del_registro(entrada, etapa):
    return {"inputId": entrada["inputId"], "code": entrada["failureCode"],
            "classification": entrada["classification"],
            "interactionType": entrada["interactionType"], "source": "flow-preconditions",
            "stage": etapa}


def _bloqueo_propio(codigo):
    if codigo not in _PROPIOS:
        from orquestacion import frescura
        if codigo not in frescura.BLOQUEAN_OPERACION:
            raise KeyError(codigo)
    input_id, clase, interaccion, fuente, etapa = _PROPIOS.get(codigo, _DE_LA_FUENTE)
    return {"inputId": input_id, "code": codigo, "classification": clase,
            "interactionType": interaccion, "source": fuente, "stage": etapa}


def _bloqueos_de(evaluacion, registro):
    salida = []
    for pregunta in precondiciones.bloqueantes(evaluacion):
        entrada = next(e for e in requeridos.de_etapa(registro, evaluacion["stage"])
                       if e["inputId"] == pregunta["inputId"])
        salida.append(_bloqueo_del_registro(entrada, evaluacion["stage"]))
    return salida


def _ordenar(bloqueos):
    """Orden canonico (etapa, inputId, codigo), sin repetidos, con su id y su compuerta."""
    vistos, unicos = set(), []
    for b in bloqueos:
        llave = (b["stage"], b["inputId"], b["code"])
        if llave not in vistos:
            vistos.add(llave)
            unicos.append(b)
    unicos.sort(key=lambda b: (STAGES.index(b["stage"]), b["inputId"], b["code"]))
    contadores = {}
    for b in unicos:
        contadores[b["stage"]] = contadores.get(b["stage"], 0) + 1
        b["blockerId"] = "FLOW-%s-%03d" % (b["stage"], contadores[b["stage"]])
        b["resumeFrom"] = {"stage": b["stage"], "gate": gate_de(b["inputId"])}
    return unicos


def _pendiente(bloqueos, registro):
    """La primera interaccion humana, con solo lo que se puede guardar sin riesgo."""
    from . import entrada_humana
    for b in bloqueos:
        if not b["interactionType"]:
            continue
        salida = {"kind": b["interactionType"], "inputId": b["inputId"]}
        entrada = requeridos.buscar(registro, b["inputId"])
        destino = (entrada or {}).get("persistentTarget")
        if b["interactionType"] == requeridos.PERSISTENT_CONFIG_INPUT and destino:
            salida.update({"target": destino["file"], "key": destino["key"],
                           "sensitivity": entrada_humana.sensibilidad(destino)})
        return salida
    return None


def _referencias(relativas, contexto, plan, corrida, huella_plan):
    """contextRef, planRef y refutationRef de los artefactos leidos. Una sola forma de armarlas:
    la usan `derivar` y `vigencia_local`."""
    return {
        "contextRef": {"path": relativas["context"],
                       "contextHash": str((contexto.get("meta") or {}).get("context_hash") or "")}
        if contexto is not None else None,
        "planRef": {"path": relativas["plan"], "planFingerprint": huella_plan,
                    "planStatus": str(plan.get("status") or "")} if plan is not None else None,
        "refutationRef": {"path": relativas["run"],
                          "planFingerprint": str((corrida.get("meta") or {}).get(
                              "planFingerprint") or ""),
                          "status": str(corrida.get("status") or "")} if corrida is not None else None,
    }


def derivar(proyecto, clave, harness_version="", proceso=None, registro=None):
    """El estado de ahora, de las fuentes que mandan. La misma entrada da el mismo estado."""
    from orquestacion import plan as orq_plan
    from orquestacion import refutacion
    clave = validar_clave(clave)
    registro = registro if registro is not None else requeridos.cargar()
    relativas = _relativas(clave)
    # Un artefacto que esta y no se lee no es un artefacto ausente: bloquea, con su codigo.
    contexto, roto_ctx = _leer_json(os.path.join(proyecto, *relativas["context"].split("/")))
    plan, roto_plan = _leer_json(os.path.join(proyecto, *relativas["plan"].split("/")))
    corrida, roto_run = _leer_json(os.path.join(proyecto, *relativas["run"].split("/")))
    gitlab, resolucion = _entorno(proyecto, proceso)

    bloqueos, stale = [], []
    etapa, estado = "CONTEXT", "NEW"
    # `is not None`, no la verdad del dict: un plan `{}` esta y no sirve; no es un plan ausente.
    huella_plan = refutacion.huella(plan) if plan is not None else None

    if roto_ctx:
        bloqueos.append(_bloqueo_del_registro(
            requeridos.buscar(registro, "planning.taskContext"), precondiciones.PLANNING))
        identidad = repositorio.identidad(None, gitlab, proyecto)
    elif contexto is None:
        evaluacion = precondiciones.evaluar("CONTEXT", _hechos_de_contexto(
            registro, resolucion, clave), registro)
        bloqueos += _bloqueos_de(evaluacion, registro)
        if not bloqueos:
            jira = _estado_de_jira(proyecto)
            if jira in _JIRA_NO_DISPONIBLE:
                bloqueos.append(_bloqueo_propio(jira))
        identidad = repositorio.identidad(None, gitlab, proyecto)
    else:
        previas = precondiciones.de_planificacion(contexto, gitlab, proyecto,
                                                  _config_harness(proyecto))
        identidad = previas["repository"]
        hechos = dict(previas["facts"])
        # El ruteo sale de las unidades del plan. Sin plan no hay nada que rutear todavia:
        # es la planificacion la que lo va a decidir.
        hechos["agents.routing"] = not any(u.get("blockers") for u in (plan or {}).get(
            "workUnits") or []) if plan is not None else True
        evaluacion = precondiciones.evaluar(precondiciones.PLANNING, hechos, registro)
        de_planificacion = _bloqueos_de(evaluacion, registro)
        bloqueos += de_planificacion
        etapa, estado = "PLANNING", "ACTIVE"

        if roto_plan:
            bloqueos.append(_bloqueo_propio("PLAN_NOT_READY"))
        if plan is not None:
            referido = str(((plan.get("meta") or {}).get("task_context_ref") or {}).get(
                "context_hash") or "")
            if referido != str((contexto.get("meta") or {}).get("context_hash") or ""):
                stale.append(TASK_CONTEXT_STALE)
                bloqueos.append(_bloqueo_propio("CONTEXT_STALE"))
            try:
                recalculado = orq_plan.estado_de(plan)
            except (KeyError, TypeError, AttributeError):
                recalculado = None
            if recalculado != plan.get("status"):
                stale.append(PLAN_STALE)
            del_plan = _repo_min((plan.get("flowPreconditions") or {}).get("repository"))
            if del_plan is not None and del_plan != _repo_min(identidad):
                stale.append(REPOSITORY_STATE_STALE)
            explicados, viejo = _explicaciones_del_plan(proyecto, plan, orq_plan)
            bloqueos += explicados
            if viejo:
                stale.append(PLAN_STALE)
            if recalculado == "CAPABILITY_RESOLUTION" and not orq_plan.huecos_de_un_plan_viejo(plan):
                bloqueos.append(_bloqueo_propio("CAPABILITY_GAP"))
            elif recalculado == "WAITING_FOR_HUMAN_APPROVAL":
                bloqueos.append(_bloqueo_propio("HUMAN_APPROVAL_PENDING"))
            elif not de_planificacion and not explicados and (
                    recalculado != LISTO or plan.get("status") != LISTO
                    or PLAN_STALE in stale or REPOSITORY_STATE_STALE in stale):
                # El plan no esta listo -el escrito o el recalculado- o se hizo con otros
                # hechos, y las compuertas de hoy no explican por que. Hay que regenerarlo,
                # no saltearlo: sin un plan listo por los dos lados no hay EXECUTION.
                bloqueos.append(_bloqueo_propio("PLAN_NOT_READY"))
            if roto_run:
                bloqueos.append(_bloqueo_propio("REFUTATION_OUTPUT_INVALID"))
            elif corrida is not None:
                if (corrida.get("meta") or {}).get("planFingerprint") != huella_plan:
                    stale.append(REFUTATION_STATE_STALE)
                    bloqueos.append(_bloqueo_propio("REFUTATION_PLAN_STALE"))
                elif not bloqueos:
                    etapa, estado = {
                        "PASS": ("COMPLETION", "ACTIVE"),
                        "NOTHING_TO_VERIFY": ("COMPLETION", "ACTIVE"),
                        "FAIL": ("REFUTATION", "FAILED"),
                    }.get(corrida.get("status"), ("REFUTATION", "INCOMPLETE"))
            if not bloqueos and corrida is None and not roto_run:
                etapa, estado = "EXECUTION", "ACTIVE"

    if roto_run and plan is None:
        # Sin plan igual: un run.json que esta y no se lee no se toma por ausente.
        bloqueos.append(_bloqueo_propio("REFUTATION_OUTPUT_INVALID"))
    bloqueos = _ordenar(bloqueos)
    if bloqueos:
        etapa = bloqueos[0]["stage"]
        estado = ("WAITING_FOR_HUMAN_APPROVAL"
                  if all(b["code"] == "HUMAN_APPROVAL_PENDING" for b in bloqueos) else "BLOCKED")
    # Una persona cancelo la tarea (human-decision-record/1.0, Wave 4): terminal, sin bloqueos
    # que resolver. Los artefactos quedan; lo que cambia es que ya no se avanza.
    from . import interaccion
    if interaccion.cancelada(proyecto, clave):
        bloqueos, estado = [], "CANCELLED"

    from orquestacion.plan import ahora
    doc = {
        "schema_version": VERSION,
        "taskKey": clave,
        "stage": etapa,
        "status": estado,
        "blockedOn": bloqueos,
        "pendingHumanInteraction": _pendiente(bloqueos, registro),
        "resumeFrom": dict(bloqueos[0]["resumeFrom"]) if bloqueos else None,
        "repositoryRef": _repo_min(identidad),
        "stale": sorted(set(stale)),
        "harnessVersion": str(harness_version or ""),
        "updatedAt": ahora(),
    }
    doc.update(_referencias(relativas, contexto, plan, corrida, huella_plan))
    errores = validar(doc)
    if errores:
        raise ErrorDeEstado(INVALIDO, "el estado derivado no valida: %s" % "; ".join(errores[:3]))
    return doc


# -- vigencia, permisos y transiciones -----------------------------------------

_REFS = (("contextRef", TASK_CONTEXT_STALE), ("planRef", PLAN_STALE),
         ("repositoryRef", REPOSITORY_STATE_STALE), ("refutationRef", REFUTATION_STATE_STALE))


def vigencia(guardado, derivado, error=None):
    """Que no cuadra entre el estado guardado y el de ahora. Vacio es vigente."""
    if error:
        return [error]
    if guardado is None:
        return [AUSENTE]
    return sorted(codigo for campo, codigo in _REFS if guardado.get(campo) != derivado.get(campo))


def _locales_de_ahora(proyecto, timeout):
    """Los repositorios de este checkout como los guarda repositoryRef, de `git remote -v`.
    Levanta RemotosSinRespuesta si `git` no contesta en `timeout`."""
    return sorted(set(repositorio.como_texto(i) for _, i in repositorio.remotos(
        proyecto, timeout=timeout, estricto=True) or []))


def vigencia_local(guardado, proyecto, remotos=True, timeout=10):
    """`vigencia()` contra las referencias de AHORA que se leen sin secretos.

    Recalcula contextRef, planRef y refutationRef de los artefactos de la tarea, y la parte local
    de repositoryRef -los remotos de este checkout- con `repositorio.remotos`: solo `git remote -v`,
    local y sin red. La identidad del repositorio de la TAREA pide la URL de GitLab del `.env`:
    esa no se recalcula aca. Un remoto cambiado sin reconciliar da REPOSITORY_STATE_STALE.

    `remotos=False` salta `git remote -v`: es para lo que solo muestra (SessionStart), nunca para
    una compuerta. `timeout` es el de `git remote -v`; si se vence, levanta
    repositorio.RemotosSinRespuesta y quien decide falla cerrado. Es lo que consumen los hooks de
    la Wave 3.
    """
    if guardado is None:
        return vigencia(None, None)
    clave = validar_clave(guardado.get("taskKey"))
    relativas = _relativas(clave)
    contexto, _ = _leer_json(os.path.join(proyecto, *relativas["context"].split("/")))
    plan, _ = _leer_json(os.path.join(proyecto, *relativas["plan"].split("/")))
    corrida, _ = _leer_json(os.path.join(proyecto, *relativas["run"].split("/")))
    huella_plan = None
    if plan is not None:
        from orquestacion import refutacion
        huella_plan = refutacion.huella(plan)
    ahora_ = dict(guardado)
    ahora_.update(_referencias(relativas, contexto, plan, corrida, huella_plan))
    if remotos and isinstance(guardado.get("repositoryRef"), dict):
        ahora_["repositoryRef"] = dict(guardado["repositoryRef"],
                                       localRepositories=_locales_de_ahora(proyecto, timeout))
    return vigencia(guardado, ahora_)


def puede_avanzar(doc, vigencia_=()):
    """Si una tarea puede avanzar: en curso, sin bloqueos, sin `stale` y con el estado vigente.

    Es la condicion de todos los permisos de avance de `permisos()`, y la que usa la compuerta
    de los hooks para dejar pasar una herramienta que modifica el proyecto.
    """
    doc = doc or {}
    return bool(doc.get("status") in AVANZAN and not doc.get("blockedOn") and not doc.get("stale")
                and not list(vigencia_))


# Desde que etapa se retoma cada desactualizacion: la del comando que la reconcilia. Un estado
# ausente o roto lo reconstruye cualquier comando que reconcilia, hasta la refutacion.
_REANUDA = {TASK_CONTEXT_STALE: "PLANNING", PLAN_STALE: "PLANNING",
            REPOSITORY_STATE_STALE: "PLANNING", REFUTATION_STATE_STALE: "REFUTATION",
            AUSENTE: "REFUTATION", INVALIDO: "REFUTATION"}


def reanudar_desde(doc, vigencia_=()):
    """La etapa mas temprana desde la que el flujo tiene que retomar, o None.

    Sale del `resumeFrom` guardado y de cada desactualizacion. Volver a correr esa etapa, o una
    anterior, es revalidar: el comando reevalua su compuerta. Una posterior es saltearla.
    """
    doc = doc or {}
    etapas = []
    if doc.get("resumeFrom"):
        etapas.append(doc["resumeFrom"].get("stage"))
    for codigo in list(doc.get("stale") or []) + list(vigencia_):
        if codigo in _REANUDA:
            etapas.append(_REANUDA[codigo])
    etapas = [e for e in etapas if e in STAGES]
    return min(etapas, key=STAGES.index) if etapas else None


def permisos(doc, vigencia_=()):
    """Que se puede hacer. Pura, y no se guarda: se deriva cada vez.

    Bloqueado, esperando una aprobacion, terminado, con artefactos que no cuadran entre si,
    desactualizado o invalido: ningun permiso de avance, y solo las de recuperacion.
    """
    doc = doc or {}
    etapa, estado = doc.get("stage"), doc.get("status")
    avanza = puede_avanzar(doc, vigencia_)
    salida = {
        "planningAllowed": avanza and etapa != "CONTEXT",
        "delegationAllowed": avanza and etapa in ("EXECUTION", "VERIFICATION", "REFUTATION"),
        "implementationAllowed": avanza and etapa in ("EXECUTION", "VERIFICATION", "REFUTATION"),
        "refutationAllowed": avanza and etapa in ("EXECUTION", "VERIFICATION", "REFUTATION"),
        "completionAllowed": avanza and etapa == "COMPLETION",
    }
    salida["recovery"] = [r for r in RECUPERACION if not (r == "cancel" and estado in TERMINALES)]
    return salida


def validar_transicion(anterior, nuevo, revalidado):
    """Levanta FLOW_TRANSITION_INVALID. Un estado no se declara: sale de reevaluar la autoridad."""
    bloqueado = nuevo.get("status") in BLOQUEADOS
    if bloqueado and not nuevo.get("blockedOn"):
        raise ErrorDeEstado(TRANSICION, "un estado %s sin bloqueos." % nuevo.get("status"))
    if not bloqueado and nuevo.get("blockedOn"):
        raise ErrorDeEstado(TRANSICION, "un estado %s con bloqueos." % nuevo.get("status"))
    if anterior is None:
        return None
    mismo = logico(anterior) == logico(nuevo)
    if anterior.get("status") in TERMINALES and not mismo:
        raise ErrorDeEstado(TRANSICION, "%s es terminal." % anterior.get("status"))
    cambio = (anterior.get("stage"), anterior.get("status")) != (nuevo.get("stage"),
                                                                 nuevo.get("status"))
    if cambio and not revalidado and nuevo.get("status") != "CANCELLED":
        raise ErrorDeEstado(
            TRANSICION, "de %s/%s a %s/%s sin reevaluar las fuentes: un estado no se declara."
            % (anterior.get("stage"), anterior.get("status"), nuevo.get("stage"),
               nuevo.get("status")))
    return None


# -- lo que ve la persona ------------------------------------------------------

LEGIBLE = {"NEW": "nueva", "ACTIVE": "en curso", "BLOCKED": "bloqueada",
           "WAITING_FOR_HUMAN_APPROVAL": "esperando una aprobación", "INCOMPLETE": "incompleta",
           "FAILED": "con incumplimientos", "COMPLETED": "terminada", "CANCELLED": "cancelada"}


def _o_guion(valor):
    return valor if valor else "—"


def texto(doc, vigencia_, proyecto):
    """El estado en espanol. Los codigos canonicos van tal cual, entre parentesis."""
    lineas = ["", "%s — estado del flujo" % doc["taskKey"], "-" * 60,
              "Etapa                  %s" % doc["stage"],
              "Estado                 %s (%s)" % (LEGIBLE.get(doc["status"], doc["status"]),
                                                  doc["status"])]
    if doc["blockedOn"]:
        lineas.append("Bloqueos")
        for b in doc["blockedOn"]:
            lineas.append("  %s  %s (%s) · %s · retoma en %s / %s" % (
                b["blockerId"], b["inputId"], b["code"], b["classification"],
                b["resumeFrom"]["stage"], b["resumeFrom"]["gate"]))
    else:
        lineas.append("Bloqueos               ninguno")
    lineas.extend(_texto_pendiente(doc["pendingHumanInteraction"], proyecto))
    lineas.extend(_texto_interacciones(doc, proyecto))
    resume = doc["resumeFrom"]
    lineas.append("Retoma en              %s" % ("%s / %s" % (resume["stage"], resume["gate"])
                                                  if resume else "—"))
    ctx, plan, run, repo = (doc["contextRef"], doc["planRef"], doc["refutationRef"],
                            doc["repositoryRef"])
    lineas.append("Contexto               %s" % ("%s · %s" % (ctx["path"], ctx["contextHash"][:19])
                                                  if ctx else "—"))
    lineas.append("Plan                   %s" % ("%s · %s · %s" % (
        plan["path"], plan["planStatus"], plan["planFingerprint"][:19]) if plan else "—"))
    lineas.append("Refutación             %s" % ("%s · %s" % (run["path"], run["status"])
                                                  if run else "—"))
    if repo:
        lineas.append("Repositorio            %s%s · tarea %s" % (
            repo["status"], " (%s)" % repo["failureCode"] if repo["failureCode"] else "",
            _o_guion(repo["taskRepository"])))
    lineas.append("Desactualizado         %s" % _o_guion(", ".join(doc["stale"])))
    lineas.append("Estado guardado        %s" % (", ".join(vigencia_) if vigencia_ else "vigente"))
    p = permisos(doc, vigencia_)
    lineas.append("Permisos               planificar %s · delegar %s · implementar %s · "
                  "refutar %s · completar %s" % tuple(
                      "sí" if p[k] else "no" for k in AVANCE))
    return "\n".join(lineas)


def lineas_para_la_persona(interacciones_, clave):
    """Las lineas exactas que la persona escribe en el chat para cada interaccion abierta."""
    salida = []
    for i in interacciones_:
        iid = i["interactionId"]
        if "APPROVE" in i["actions"]:
            salida.append("HARNESS APPROVE %s %s" % (clave, iid))
        if "USE_ALTERNATIVE" in i["actions"]:
            salida.extend("HARNESS ALTERNATIVE %s %s %s" % (clave, iid, o) for o in i["options"])
        if "CHOOSE" in i["actions"]:
            salida.extend("HARNESS CHOOSE %s %s %s" % (clave, iid, o) for o in i["options"])
        if "RESUME" in i["actions"] and "HARNESS RESUME %s" % clave not in salida:
            salida.append("HARNESS RESUME %s" % clave)
        if "CANCEL" in i["actions"]:
            salida.append("HARNESS CANCEL %s %s" % (clave, iid))
    return salida


def _texto_interacciones(doc, proyecto):
    """Las interacciones abiertas y como las decide la persona. Solo las lineas: nunca un valor."""
    from . import interaccion
    try:
        abiertas = interaccion.interacciones(proyecto, doc["taskKey"], doc)
    except Exception:                                  # noqa: BLE001 - mostrar no voltea el estado
        return []
    if not abiertas:
        return []
    salida = ["Interacciones"]
    for i in abiertas:
        detalle = (" · unidad %s, tier %s" % (i["workUnitId"], i.get("tier"))
                   if i.get("workUnitId") else "")
        salida.append("  %s  %s %s%s · %s" % (i["interactionId"], i["kind"], i["inputId"], detalle,
                                             ", ".join(i["actions"])))
    salida.append("  La persona decide escribiendo en el chat exactamente una de estas líneas:")
    salida.extend("    %s" % l for l in lineas_para_la_persona(abiertas, doc["taskKey"]))
    return salida


def _texto_pendiente(pendiente, proyecto):
    """La interaccion pendiente, con la posicion de AHORA.

    La linea y el enlace no se guardan en el estado: el archivo puede haber cambiado. Se
    piden a entrada_humana cada vez, que es el unico localizador.
    """
    if not pendiente:
        return ["Interacción pendiente  ninguna"]
    salida = ["Interacción pendiente  %s %s%s" % (
        pendiente["kind"], pendiente["inputId"],
        " · %s en %s (%s)" % (pendiente["key"], pendiente["target"], pendiente["sensitivity"])
        if pendiente.get("key") else "")]
    if pendiente["kind"] == requeridos.PERSISTENT_CONFIG_INPUT:
        from . import entrada_humana
        try:
            ubicacion = entrada_humana.localizar(pendiente["inputId"], proyecto)
            salida.append("  Dónde                %s" % ubicacion["fallback"])
            salida.append("  Abrir                %s" % ubicacion["vscodeUri"])
            if ubicacion["sensitivity"] == entrada_humana.SECRET:
                salida.append("  No pegues el valor en el chat.")
        except entrada_humana.EntradaNoUbicable as e:
            salida.append("  Dónde                no se pudo ubicar (%s)" % e.codigo)
    return salida
