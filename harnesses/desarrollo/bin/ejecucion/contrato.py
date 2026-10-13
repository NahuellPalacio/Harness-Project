"""El contrato de ejecucion: sus constantes y sus validadores puros.

Execution es el decimo contexto (ADR-0014) y hoy es solo contrato: execution-request/1.0,
execution-result/1.0 y lo que el subconjunto de JSON Schema no puede decir, que vive aca. El
precedente es `eventos.validar_estructura` del Bloque 4: el validador de subconjunto no tiene
condicionales, y las coherencias entre campos se escriben a mano.

    validar_request     el schema, la WorkUnit contra la del plan y ocho coherencias
    validar_resultado   el schema y las doce coherencias con su request
    validar_rechazo     un ExecutionError devuelto al pedir
    validar_informe     el AgentReport que entrega el Host Adapter

🔴 Este modulo no es la admision ni el motor. Lee sus dos schemas y el del plan, y nada mas: ni
planes del proyecto, ni el registro de agentes, ni capacidades, ni la compuerta normativa, ni
ejecuciones guardadas. No escribe, no lanza procesos y no persiste nada.

🔴 Execution no interpreta texto. El `artifact` de un AgentReport es opaco: ningun validador de
aca lo lee, y un texto que dice `status: COMPLETE` no reemplaza a un `declaredStatus`.
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

VERSION_REQUEST = "execution-request/1.0"
VERSION_RESULT = "execution-result/1.0"

SCHEMA_REQUEST = "execution-request.schema.json"
SCHEMA_RESULT = "execution-result.schema.json"
# La forma de una WorkUnit es de Planning. El request no la copia: la valida contra esta.
SCHEMA_PLAN = "orchestration-plan.schema.json"

# El ciclo de vida (seccion 13). Seis estados, cuatro terminales, ninguno BLOCKED.
ESTADOS = ("REQUESTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "REJECTED")
TERMINALES = ("SUCCEEDED", "FAILED", "CANCELLED", "REJECTED")
# Las unicas transiciones. Desde un terminal no sale ninguna: un resultado no cambia.
TRANSICIONES = (
    ("REQUESTED", "RUNNING"),
    ("REQUESTED", "REJECTED"),
    ("REQUESTED", "CANCELLED"),
    ("RUNNING", "SUCCEEDED"),
    ("RUNNING", "FAILED"),
    ("RUNNING", "CANCELLED"),
)

# Donde puede ir cada codigo (seccion 14). AL_PEDIR es el rechazo de la admision, que no crea una
# Execution: vuelve al que pidio.
AL_PEDIR = "AL_PEDIR"
CODIGOS = {
    "CONTRACT_INVALID": (AL_PEDIR, "REJECTED"),
    "PLAN_UNREADABLE": (AL_PEDIR, "REJECTED"),
    "TASK_KEY_MISMATCH": (AL_PEDIR, "REJECTED"),
    "PLAN_CHANGED": ("REJECTED",),
    "PLAN_NOT_READY": (AL_PEDIR, "REJECTED"),
    "DELEGATION_NOT_ALLOWED": (AL_PEDIR, "REJECTED"),
    "WORK_UNIT_NOT_FOUND": (AL_PEDIR, "REJECTED"),
    "WORK_UNIT_NOT_PENDING": (AL_PEDIR, "REJECTED"),
    "NORMATIVE_GATE_BLOCKED": (AL_PEDIR, "REJECTED"),
    "AGENT_UNAVAILABLE": (AL_PEDIR, "REJECTED", "FAILED"),
    "AGENT_NOT_EXECUTABLE": (AL_PEDIR, "REJECTED"),
    "AGENT_DOMAIN_MISMATCH": (AL_PEDIR, "REJECTED"),
    "CAPABILITY_UNAVAILABLE": (AL_PEDIR, "REJECTED", "FAILED"),
    "DEPENDENCY_NOT_SATISFIED": (AL_PEDIR, "REJECTED"),
    "DUPLICATE_EXECUTION": (AL_PEDIR, "REJECTED"),
    "HOST_FAILURE": ("FAILED",),
    "HOST_INTERRUPTED": ("FAILED",),
    "PROVIDER_FAILURE": ("FAILED",),
    "TIMEOUT": ("FAILED",),
    "OUTPUT_INVALID": ("FAILED",),
    "AGENT_DECLARED_NOT_COMPLETE": ("FAILED",),
    "ENGINE_FAILURE": ("FAILED",),
    "CANCELLED": ("CANCELLED",),
}

# La regla de admision (9.2), en el orden en que se mira: se informa el primer codigo que falla.
# Las capas van en este orden: la forma de lo pedido, Planning, Normative Sources, Catalog y el
# estado de Execution. PLAN_CHANGED solo se puede dar al entregar. DELEGATION_NOT_ALLOWED es el
# TaskFlowState, que en 0.31.0 es de Planning: va despues del plan, que es mas especifico, y antes de
# la WorkUnit, porque es de la tarea entera.
PRECEDENCIA = (
    "CONTRACT_INVALID",
    "PLAN_UNREADABLE",
    "TASK_KEY_MISMATCH",
    "PLAN_CHANGED",
    "PLAN_NOT_READY",
    "DELEGATION_NOT_ALLOWED",
    "WORK_UNIT_NOT_FOUND",
    "WORK_UNIT_NOT_PENDING",
    "NORMATIVE_GATE_BLOCKED",
    "AGENT_UNAVAILABLE",
    "AGENT_NOT_EXECUTABLE",
    "AGENT_DOMAIN_MISMATCH",
    "CAPABILITY_UNAVAILABLE",
    "DEPENDENCY_NOT_SATISFIED",
    "DUPLICATE_EXECUTION",
)

# Los valores de `declaredStatus` de un AgentReport. Es el vocabulario comun del `agentResult` de
# los agentes que se pueden ejecutar; Execution toma el vocabulario, no el formato.
DECLARACIONES_DEL_AGENTE = ("COMPLETE", "PARTIAL", "BLOCKED", "FAILED")
COMPLETO = "COMPLETE"
INCOMPLETAS = ("PARTIAL", "BLOCKED", "FAILED")
CLAVES_DEL_INFORME = ("declaredStatus", "artifact")

# Ni el orquestador ni el refutador: Execution no replanifica ni refuta.
TIPOS_EJECUTABLES = ("SPECIALIST_AGENT", "INFRASTRUCTURE_AGENT")

DECLARADO_INCOMPLETO = "AGENT_DECLARED_NOT_COMPLETE"
RESUELTO = "RESOLVED"

# El tope de `detail`, el mismo de `libro.TOPE_DE_TEXTO`.
TOPE_DE_DETALLE = 300


# -- huellas ----------------------------------------------------------------------------------

def huella(valor):
    """`sha256:` del JSON canonico: claves ordenadas, separadores `,` y `:`, UTF-8 sin escapar.

    Es el mismo algoritmo que `refutacion.huella`, y a proposito no se importa de ahi: Execution
    no depende de un modulo de Governance para calcular un hash. Un escenario fija que los dos
    dan lo mismo.
    """
    texto = json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()


def clave_de_idempotencia(task_key, plan_fingerprint, work_unit_id):
    """La misma WorkUnit del mismo documento de plan. Sin intento, sin sesion y sin reloj."""
    return huella([task_key, plan_fingerprint, work_unit_id])


def transicion_valida(desde, hacia):
    """Si el par esta en TRANSICIONES. Lo que no esta declarado no vale."""
    return (desde, hacia) in TRANSICIONES


# -- schemas y validador ----------------------------------------------------------------------

_CACHE = {}


def _armador():
    """`contexto-armar.py`, que trae el validador de subconjunto. Su nombre tiene un guion."""
    if "armador" not in _CACHE:
        ruta = rutas.localizar(("bin", "contexto-armar.py"), __file__)
        modulo = None
        if ruta is not None:
            spec = importlib.util.spec_from_file_location("contexto_armar_ejecucion", ruta)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
        _CACHE["armador"] = modulo
    return _CACHE["armador"]


def _schema(nombre):
    """(schema, None) o (None, motivo). Se controla una vez que el validador lo entiende entero."""
    if nombre not in _CACHE:
        ruta = rutas.localizar(("schemas", nombre), __file__)
        armador = _armador()
        if ruta is None:
            _CACHE[nombre] = (None, "no esta %s: sin el no se puede validar el contrato" % nombre)
        elif armador is None:
            _CACHE[nombre] = (None, "no esta comun/bin/contexto-armar.py, que trae el validador")
        else:
            with io.open(ruta, encoding="utf-8") as f:
                esquema = json.load(f)
            armador.controlar_soporte(esquema)
            _CACHE[nombre] = (esquema, None)
    return _CACHE[nombre]


def _contra(dato, nombre, ruta="$", sub=None):
    """Los errores de `dato` contra el schema `nombre`, o contra su parte `sub` (una lista de
    claves desde la raiz). Un schema que falta es un error, no una excepcion."""
    esquema, motivo = _schema(nombre)
    if esquema is None:
        return ["%s: %s" % (ruta, motivo)]
    parte = esquema
    for clave in sub or ():
        parte = parte[clave]
    return _armador().validar(dato, parte, ruta, esquema)


def _es_dict(valor):
    return isinstance(valor, dict)


# -- el request -------------------------------------------------------------------------------

def validar_request(doc):
    """Los errores de un ExecutionRequest. Vacia es valido. No levanta por un documento roto.

    1. el schema;
    2. `workUnit` contra `workUnits.items` del schema del plan, que es la autoridad de su forma;
    3. `plan.planId == "pln_" + taskKey`;
    4. `workUnitFingerprint == huella(workUnit)`;
    5. `idempotencyKey == clave_de_idempotencia(taskKey, plan.planFingerprint, workUnit.id)`;
    6. `admission.agent.domain == workUnit.domain`;
    7. `admission.dependencies` nombra exactamente las dependencias de la WorkUnit, una vez cada
       una, y ninguna con el `executionId` del propio request;
    8. `workUnit` no trae `blockers`: en orchestration-plan/2.1 los lleva solo una unidad BLOCKED,
       y una bloqueada no se admite. El schema del plan no lo puede decir (no hay if/then).

    🔴 No lee el plan guardado: que la WorkUnit este de verdad en un plan lo mira la admision,
    que es de la Task siguiente.
    """
    errores = _contra(doc, SCHEMA_REQUEST)
    if not _es_dict(doc):
        return errores

    unidad = doc.get("workUnit")
    if _es_dict(unidad):
        errores += _contra(unidad, SCHEMA_PLAN, "$.workUnit", ("properties", "workUnits", "items"))

    clave = doc.get("taskKey")
    plan = doc.get("plan") if _es_dict(doc.get("plan")) else {}
    if isinstance(clave, str) and plan.get("planId") != "pln_" + clave:
        errores.append("$.plan.planId: `%s` no es pln_ mas la taskKey `%s`"
                       % (plan.get("planId"), clave))

    if unidad is not None and doc.get("workUnitFingerprint") != huella(unidad):
        errores.append("$.workUnitFingerprint: no es la huella de workUnit")

    if _es_dict(unidad):
        esperada = clave_de_idempotencia(clave, plan.get("planFingerprint"), unidad.get("id"))
        if doc.get("idempotencyKey") != esperada:
            errores.append("$.idempotencyKey: no es la huella de [taskKey, planFingerprint, "
                           "workUnit.id]")

    admision = doc.get("admission") if _es_dict(doc.get("admission")) else {}
    agente = admision.get("agent") if _es_dict(admision.get("agent")) else {}
    if _es_dict(unidad) and "domain" in agente and agente.get("domain") != unidad.get("domain"):
        errores.append("$.admission.agent.domain: el agente es de `%s` y la WorkUnit de `%s`"
                       % (agente.get("domain"), unidad.get("domain")))

    if _es_dict(unidad) and isinstance(admision.get("dependencies"), list):
        errores += _dependencias(admision["dependencies"], unidad.get("dependencies"),
                                 doc.get("executionId"))

    if _es_dict(unidad) and "blockers" in unidad:
        errores.append("$.workUnit.blockers: una WorkUnit PENDING no lleva blockers "
                       "(orchestration-plan/2.1); una bloqueada no se admite")
    return errores


def _dependencias(satisfechas, declaradas, propio):
    # Lo que no es texto ya lo marca el schema; aca se comparan solo los nombres.
    errores = []
    nombradas = [d.get("workUnitId") for d in satisfechas
                 if _es_dict(d) and isinstance(d.get("workUnitId"), str)]
    declaradas = [d for d in (declaradas if isinstance(declaradas, list) else [])
                  if isinstance(d, str)]
    repetidas = sorted({n for n in nombradas if nombradas.count(n) > 1})
    if repetidas:
        errores.append("$.admission.dependencies: repite %s" % ", ".join(repetidas))
    faltan = sorted(set(declaradas) - set(nombradas))
    sobran = sorted(set(nombradas) - set(declaradas))
    if faltan:
        errores.append("$.admission.dependencies: faltan dependencias de la WorkUnit: %s"
                       % ", ".join(faltan))
    if sobran:
        errores.append("$.admission.dependencies: nombra lo que la WorkUnit no declara: %s"
                       % ", ".join(sobran))
    if any(_es_dict(d) and d.get("executionId") == propio for d in satisfechas):
        errores.append("$.admission.dependencies: una dependencia no se satisface con la propia "
                       "Execution")
    return errores


# -- el resultado -----------------------------------------------------------------------------

def validar_resultado(doc, request):
    """Los errores de un ExecutionResult frente a su request. Vacia es valido.

    El schema, y las doce coherencias de la seccion 11.3: la identidad, el error, REJECTED,
    startedAt y evidencia, el AgentReport, SUCCEEDED y FAILED, los cambios, las rutas, los tiempos
    y el detalle.
    """
    errores = _contra(doc, SCHEMA_RESULT)
    if not _es_dict(doc):
        return errores
    request = request if _es_dict(request) else {}
    estado = doc.get("status")
    error = doc.get("error")
    codigo = error.get("code") if _es_dict(error) else None
    codigo = codigo if isinstance(codigo, str) else None
    declarado = doc.get("agentDeclaredStatus")
    salida = doc.get("output")
    inicio = doc.get("startedAt")
    evidencia = doc.get("evidence")

    # 1. La identidad: el resultado es de este request, y el request no se toco despues.
    if doc.get("executionId") != request.get("executionId"):
        errores.append("$.executionId: no es el de su request")
    if doc.get("requestFingerprint") != huella(request):
        errores.append("$.requestFingerprint: no es la huella de su request")

    # 2. SUCCEEDED si y solo si no hay error.
    if (estado == "SUCCEEDED") != (error is None):
        errores.append("$.error: SUCCEEDED va sin error, y cualquier otro terminal con uno")

    # 3. Cada codigo va solo a los estados que le corresponden.
    if codigo in CODIGOS and estado in TERMINALES and estado not in CODIGOS[codigo]:
        errores.append("$.error.code: `%s` no puede ir con %s" % (codigo, estado))

    # 4. Lo rechazado no corrio.
    if estado == "REJECTED":
        for campo in ("startedAt", "evidence", "output", "agentDeclaredStatus"):
            if doc.get(campo) is not None:
                errores.append("$.%s: un REJECTED no corrio, y va en null" % campo)

    # 5. Con entrega hay evidencia, y sin entrega no.
    if inicio is not None and evidencia is None:
        errores.append("$.evidence: con startedAt la evidencia no puede ser null")
    if inicio is None and evidencia is not None:
        errores.append("$.evidence: sin startedAt no hay nada que observar, y va en null")

    # 6. agentDeclaredStatus y output vienen del mismo AgentReport: los dos o ninguno.
    if (declarado is None) != (salida is None):
        errores.append("$.output: agentDeclaredStatus y output van los dos o ninguno: vienen del "
                       "mismo AgentReport")

    # 7. Con un AgentReport, el status lo decide su declaredStatus, y sin el no hay SUCCEEDED.
    if declarado == COMPLETO and estado != "SUCCEEDED":
        errores.append("$.agentDeclaredStatus: COMPLETE va solo con SUCCEEDED")
    if declarado in INCOMPLETAS and not (estado == "FAILED" and codigo == DECLARADO_INCOMPLETO):
        errores.append("$.agentDeclaredStatus: %s va solo con FAILED y %s"
                       % (declarado, DECLARADO_INCOMPLETO))
    if estado == "SUCCEEDED" and declarado != COMPLETO:
        errores.append("$.agentDeclaredStatus: SUCCEEDED exige un AgentReport que declare COMPLETE")
    if codigo == DECLARADO_INCOMPLETO and declarado not in INCOMPLETAS:
        errores.append("$.agentDeclaredStatus: %s exige PARTIAL, BLOCKED o FAILED"
                       % DECLARADO_INCOMPLETO)

    # 8. A SUCCEEDED y a FAILED solo se llega desde RUNNING.
    if estado in ("SUCCEEDED", "FAILED") and inicio is None:
        errores.append("$.startedAt: %s solo se alcanza desde RUNNING, y lleva startedAt" % estado)

    # 9. Lo que falta no es cero.
    cambios = evidencia.get("changes") if _es_dict(evidencia) else None
    archivos = cambios.get("files") if _es_dict(cambios) else None
    if _es_dict(cambios) and cambios.get("state") != RESUELTO and archivos:
        errores.append("$.evidence.changes.files: con %s la lista va vacia"
                       % cambios.get("state"))

    # 10. Las rutas.
    errores += _rutas(salida, archivos)

    # 11. Los tiempos.
    errores += _tiempos(request.get("createdAt"), inicio, doc.get("endedAt"))

    # 12. El detalle.
    if _es_dict(error):
        errores += _detalle(error.get("detail"), "$.error.detail")
    return errores


def _ruta_mala(ruta):
    """Por que una ruta no es relativa y POSIX, o None."""
    if not isinstance(ruta, str) or not ruta.strip():
        return "esta vacia"
    if "\\" in ruta:
        return "no es POSIX"
    if ruta.startswith("/") or re.match(r"^[A-Za-z]:", ruta):
        return "es absoluta"
    if ".." in ruta.split("/"):
        return "tiene .."
    return None


def _rutas(salida, archivos):
    errores = []
    nombradas = []
    if _es_dict(salida) and "path" in salida:
        nombradas.append(("$.output.path", salida["path"]))
    for i, archivo in enumerate(archivos if isinstance(archivos, list) else []):
        if _es_dict(archivo) and "path" in archivo:
            nombradas.append(("$.evidence.changes.files[%d].path" % i, archivo["path"]))
    for donde, ruta in nombradas:
        motivo = _ruta_mala(ruta)
        if motivo:
            errores.append("%s: `%s` %s" % (donde, ruta, motivo))
    de_archivos = [r for d, r in nombradas if d.startswith("$.evidence")]
    repetidas = sorted({r for r in de_archivos if de_archivos.count(r) > 1}, key=str)
    if repetidas:
        errores.append("$.evidence.changes.files: repite %s" % ", ".join(map(str, repetidas)))
    return errores


UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def _tiempos(creado, inicio, fin):
    """createdAt <= startedAt <= endedAt cuando estan, y createdAt <= endedAt siempre. Los tres
    van en UTC con el mismo formato, asi que se comparan como texto."""
    def bien(t):
        return isinstance(t, str) and UTC.match(t)
    errores = []
    if bien(inicio) and bien(creado) and inicio < creado:
        errores.append("$.startedAt: es anterior al createdAt de su request")
    if bien(inicio) and bien(fin) and fin < inicio:
        errores.append("$.endedAt: es anterior a startedAt")
    if bien(creado) and bien(fin) and fin < creado:
        errores.append("$.endedAt: es anterior al createdAt de su request")
    return errores


def _detalle(texto, donde):
    if not isinstance(texto, str) or not texto.strip():
        return ["%s: no puede estar vacio" % donde]
    if len(texto) > TOPE_DE_DETALLE:
        return ["%s: tiene %d caracteres y el tope es %d" % (donde, len(texto), TOPE_DE_DETALLE)]
    return []


# -- el rechazo al pedir ----------------------------------------------------------------------

def validar_rechazo(error):
    """Los errores de un ExecutionError devuelto al pedir: `$defs.error`, y un codigo que puede
    darse al pedir. PLAN_CHANGED no, porque solo se da al entregar; los de corrida y CANCELLED,
    tampoco."""
    if not _es_dict(error):
        return ["$: un rechazo es un objeto {code, detail}"]
    errores = _contra(error, SCHEMA_RESULT, "$", ("$defs", "error"))
    codigo = error.get("code")
    if isinstance(codigo, str) and codigo in CODIGOS and AL_PEDIR not in CODIGOS[codigo]:
        errores.append("$.code: `%s` no es un rechazo al pedir" % codigo)
    errores += _detalle(error.get("detail"), "$.detail")
    return errores


# -- el AgentReport ---------------------------------------------------------------------------

def validar_informe(informe):
    """Los errores de un AgentReport: exactamente `declaredStatus`, uno de los cuatro, y
    `artifact`, que es texto y puede estar vacio.

    🔴 No lee el contenido de `artifact`. Un `declaredStatus` que falta no lo arregla un texto
    que dice `status: COMPLETE`, ni un bloque `agentResult`: sacar el dato de la salida nativa es
    trabajo del Host Adapter.
    """
    if not _es_dict(informe):
        return ["$: un AgentReport es un objeto {declaredStatus, artifact}"]
    errores = []
    for clave in sorted(set(informe) - set(CLAVES_DEL_INFORME), key=str):
        errores.append("$.%s: un AgentReport tiene solo declaredStatus y artifact" % clave)
    if "declaredStatus" not in informe:
        errores.append("$.declaredStatus: falta y es obligatorio")
    elif informe["declaredStatus"] not in DECLARACIONES_DEL_AGENTE:
        errores.append("$.declaredStatus: `%s` no es uno de %s"
                       % (informe["declaredStatus"], ", ".join(DECLARACIONES_DEL_AGENTE)))
    if "artifact" not in informe:
        errores.append("$.artifact: falta y es obligatorio")
    elif not isinstance(informe["artifact"], str):
        errores.append("$.artifact: tiene que ser texto")
    return errores
