"""El conductor de un GraphRun: lleva todas las WorkUnits de un plan a un terminal, de a una por vez.

docs/cambios/graph-execution/spec.md, secciones 6 a 12 y 16 a 23.

    conducir            el algoritmo de la seccion 10 (GD-07): el candado de la tarea, el cierre de los
                        huerfanos, el plan, el GraphRun, un bucle sobre el orden topologico y el cierre
    cerrar_huerfano     16.1: lo que hace quien toma el candado con un GraphRun ACTIVE (GD-10)
    cancelar_grafo      17: una marca, propagada solo a lo propio (GD-11)
    estado_de_grafos    solo lee: no recupera, no cierra, no sondea el candado, no escribe (GE-I30)
    validar_resultado   el schema de graph-run-result/1.0 y las coherencias que el schema no dice

Un GraphRun referencia Executions: no las crea ni es su duenio. Cada Execution sale de
`motor.ejecutar`, con sus dos admisiones, y el conductor decide solo con lo que vuelve a derivar
del registro y del plan (el estado del nodo, la huella, el `status` y el `code` del motor). Nunca lee el
texto de un rechazo, de un resultado ni del agente.

🔴 Un conductor, un bucle, un proceso: nada de hilos, de procesos ni de colas (GD-07, ME-E47, E-41).
El GraphRun despacha una Execution propia a la vez y no excluye a las manuales de la tarea: el chequeo
de las abiertas (7d) mira el registro en un instante y no es un mutex de la TaskKey (GD-06, §15.4).

🔴 Todo lo que se escribe pasa por `registro.py` (ME-E46). Este modulo no abre un archivo para escribir.

🔴 No elige por capacidades, no evalua la compuerta normativa ni el flujo, no los guarda en cache entre
unidades: cada intento paga sus dos admisiones (GD-17 a GD-19).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import admision                                     # noqa: E402
from . import contrato                                     # noqa: E402
from . import motor                                        # noqa: E402
from . import registro                                     # noqa: E402
from contexto import limpieza                              # noqa: E402
from orquestacion import plan as orq_plan                  # noqa: E402

VERSION = "graph-run-result/1.0"
SCHEMA = "graph-run-result.schema.json"

# Los nueve codigos de GraphRunError (GD-22): propios del GraphRun. Un ExecutionError aparece solo como
# causa referenciada, en `executionCode`.
GRAPH_ALREADY_ACTIVE = "GRAPH_ALREADY_ACTIVE"
GRAPH_PLAN_UNREADABLE = "GRAPH_PLAN_UNREADABLE"
GRAPH_STRUCTURE_INVALID = "GRAPH_STRUCTURE_INVALID"
WORK_UNIT_NOT_SUCCEEDED = "WORK_UNIT_NOT_SUCCEEDED"
ADMISSION_REJECTED = "ADMISSION_REJECTED"
TASK_EXECUTION_OPEN = "TASK_EXECUTION_OPEN"
PLAN_FINGERPRINT_CHANGED = "PLAN_FINGERPRINT_CHANGED"
DISPATCH_FAILED = "DISPATCH_FAILED"
GRAPH_INTERRUPTED = "GRAPH_INTERRUPTED"
CODIGOS = (GRAPH_ALREADY_ACTIVE, GRAPH_PLAN_UNREADABLE, GRAPH_STRUCTURE_INVALID,
           WORK_UNIT_NOT_SUCCEEDED, ADMISSION_REJECTED, TASK_EXECUTION_OPEN,
           PLAN_FINGERPRINT_CHANGED, DISPATCH_FAILED, GRAPH_INTERRUPTED)

# El estado de un nodo (§9.2): derivado del ultimo turno de su clave bajo F, nunca persistido.
SATISFIED, NOT_SATISFIED, OPEN = "SATISFIED", "NOT_SATISFIED", "OPEN"
UNREADABLE, NOT_STARTED = "UNREADABLE", "NOT_STARTED"
DEL_TURNO = {"SUCCEEDED": SATISFIED, "FAILED": NOT_SATISFIED, "CANCELLED": NOT_SATISFIED,
             "REJECTED": NOT_SATISFIED, registro.REQUESTED: OPEN, registro.RUNNING: OPEN,
             registro.ILEGIBLE: UNREADABLE}

# Los puntos de encuentro de los tests (§24), en el estilo de los del motor: en produccion no se pasan.
# Los dos ultimos son los del motor (`antes_de_reservar`, `antes_de_entregar`) y llegan tal cual.
GANCHOS = ("despues_de_inicio", "despues_del_despacho", "despues_del_retorno", "antes_del_terminal",
           "antes_de_reservar", "antes_de_entregar")


def _catalogo(cargar):
    try:
        return cargar()
    except Exception:                            # noqa: BLE001 - sin catalogo, falla cerrado
        return None


def _rechazo(codigo, texto, catalogo):
    """Un rechazo al arrancar: `{code, detail}`. No se persiste: no hay un GraphRun donde guardarlo."""
    return {"code": codigo, "detail": admision.detalle(texto, catalogo)}


# -- la estructura (§11.1) -------------------------------------------------------------------

def _estructura(unidades):
    """(orden, None) o (None, por_que): el grafo se puede recorrer. La forma, lo que Planning no
    controla al leer un plan guardado (plan.py), y el orden y los ciclos, con la funcion de Planning."""
    if not unidades:
        return None, "el plan no tiene unidades: un grafo vacio no tiene nada que llevar a termino"
    for unidad in unidades:
        uid = unidad.get("id")
        if not isinstance(uid, str) or not uid.strip():
            return None, "hay una unidad sin un id de texto"
        dependencias = unidad.get("dependencies", [])
        if not isinstance(dependencias, list) or not all(
                isinstance(d, str) and d.strip() for d in dependencias):
            return None, "la unidad %s no tiene una lista de dependencias de texto" % uid
        repetidas = sorted(set(d for d in dependencias if dependencias.count(d) > 1))
        if repetidas:
            return None, "la unidad %s repite su dependencia %s" % (uid, ", ".join(repetidas))
    try:
        return orq_plan.orden_de_ejecucion(unidades), None
    except orq_plan.PlanInvalido as e:
        return None, str(e)


def _huella_del_plan(proyecto, clave):
    """La huella del plan guardado, o None si no se lee. La misma regla de lectura de la admision."""
    try:
        return contrato.huella(admision.leer_plan(proyecto, clave))
    except admision.Rechazo:
        return None


# -- el estado de un nodo (§9.2) ----------------------------------------------------------------

def _nodo(proyecto, clave, huella, unidad):
    """{state, executionId, turn} de la unidad bajo F: del ultimo turno de su clave. Sin turno es
    NOT_STARTED. Una Execution de otra huella no se ve: su clave es otra."""
    ultimo = registro.ultimo_turno(proyecto, clave,
                                   contrato.clave_de_idempotencia(clave, huella, unidad))
    if ultimo is None:
        return {"state": NOT_STARTED, "executionId": None, "turn": None}
    return {"state": DEL_TURNO[ultimo["estado"]], "executionId": ultimo["executionId"],
            "turn": ultimo["numero"]}


def _de_la_execution(proyecto, clave, execution_id):
    """(estado, code) de una Execution que un turno nombra, o (None, None) si ninguno la nombra: una
    carpeta o una marca de despacho sin turno no es una Execution (ME-I21). `code` es el `error.code`
    de su resultado, si lo tiene."""
    if execution_id not in set(e for _, _, e, _ in registro.nombradas(proyecto, clave) if e):
        return None, None
    derivado = registro.estado(proyecto, clave, execution_id)
    error = (derivado["resultado"] or {}).get("error") or {}
    return derivado["estado"], error.get("code")


def _primera_abierta(proyecto, clave, excepto=None):
    """{executionId, estado} de la primera Execution de la TaskKey, de cualquier clave, que esta
    abierta o es ilegible, sin contar a `excepto`; o None. Mira el registro en un instante: es el chequeo
    preventivo de 7d, y no excluye una que se publique despues (§15.4)."""
    for _, _, execution_id, _ in registro.nombradas(proyecto, clave):
        if execution_id is None:
            return {"executionId": None, "estado": registro.ILEGIBLE}
        if execution_id == excepto:
            continue
        estado = registro.estado(proyecto, clave, execution_id)["estado"]
        if estado in registro.ABIERTOS or estado == registro.ILEGIBLE:
            return {"executionId": execution_id, "estado": estado}
    return None


# -- el cierre (GD-05, §23) ------------------------------------------------------------------------

def _causa(codigo, texto, catalogo, unidad=None, execution_id=None, estado=None, de_execution=None):
    """Un GraphRunError (§22). `texto` es del GraphRun: ids, codigos y el comando que sigue. `unidad` es
    en la que se detuvo el conductor, o la de la Execution que es la causa; nunca texto del Host."""
    return {"code": codigo, "workUnitId": unidad, "executionId": execution_id,
            "executionStatus": estado, "executionCode": de_execution,
            "detail": admision.detalle(texto, catalogo)}


def _foto(proyecto, clave, inicio):
    """Los nodos del resultado: el estado derivado de cada unidad del conjunto congelado, en el orden
    de `order`, al cerrar. `dispatched` dice si la Execution de ese turno la despacho este GraphRun."""
    propias = set(p["executionId"] for p in registro.propias(proyecto, clave, inicio["graphRunId"]))
    nodos = []
    for unidad in inicio["order"]:
        nodo = _nodo(proyecto, clave, inicio["planFingerprint"], unidad)
        nodos.append({"workUnitId": unidad, "state": nodo["state"],
                      "executionId": nodo["executionId"], "turn": nodo["turn"],
                      "dispatched": nodo["executionId"] is not None and nodo["executionId"] in propias})
    return nodos


def cerrar_grafo(proyecto, clave, inicio, causa, catalogo):
    """El `result.json` por la regla de cierre (GD-05), una sola vez, y devuelve lo escrito. Lo escribe
    quien tiene el candado de la tarea: el conductor, o quien cierra un huerfano, que no tiene causa y
    cierra con GRAPH_INTERRUPTED si no esta todo satisfecho ni hay marca de cancelacion.

    1. todos los nodos SATISFIED bajo F: SUCCEEDED, haya o no marca de cancelacion;
    2. con la marca: CANCELLED;
    3. si no: FAILED, con el codigo de la causa.

    Si ya habia un terminal, gana el primero y se devuelve ese."""
    graph_run_id = inicio["graphRunId"]
    nodos = _foto(proyecto, clave, inicio)
    cancelada = registro.cancelada(proyecto, clave, graph_run_id)
    if all(n["state"] == SATISFIED for n in nodos):
        estado, error = "SUCCEEDED", None
    elif cancelada:
        estado, error = "CANCELLED", None
    else:
        estado = "FAILED"
        error = causa or _causa(
            GRAPH_INTERRUPTED, "el conductor de este GraphRun se corto antes de cerrarlo: lo cerro "
            "quien tomo el candado de la tarea. Las Executions quedan como estaban: `ejecutar %s "
            "--estado`." % clave, catalogo)
    resultado = {"schema_version": VERSION, "graphRunId": graph_run_id, "taskKey": clave,
                 "planFingerprint": inicio["planFingerprint"], "requestedBy": inicio["requestedBy"],
                 "startedAt": inicio["startedAt"],
                 "endedAt": max(registro.ahora(), inicio["startedAt"]), "status": estado,
                 "error": error, "cancelRequested": cancelada, "nodes": nodos}
    errores = validar_resultado(resultado, inicio)
    if errores:
        raise motor.ErrorDelComando("el conductor armo un resultado que no valida: %s" % errores[0])
    try:
        registro.escribir_terminal(proyecto, clave, graph_run_id, resultado)
    except FileExistsError:
        return registro.leer_grafo(proyecto, clave, graph_run_id)["resultado"]
    return resultado


def validar_resultado(doc, inicio):
    """Los errores de un graph-run-result/1.0 frente al `inicio.json` de su GraphRun. Vacia es valida.

    El schema, y lo que el schema no dice (§23): que `SUCCEEDED` es todos los nodos `SATISFIED`; que
    `nodes` tiene exactamente los `workUnitId` de `inicio.json`, en su orden; que `error.workUnitId`, si
    no es null, es uno de ellos; que hay un error si y solo si es FAILED; que la identidad es la de su
    inicio; y los tiempos y el tope del texto."""
    errores = contrato._contra(doc, SCHEMA)
    if not isinstance(doc, dict):
        return errores
    inicio = inicio if isinstance(inicio, dict) else {}
    estado, error, nodos = doc.get("status"), doc.get("error"), doc.get("nodes")
    nodos = nodos if isinstance(nodos, list) else []
    ids = [n.get("workUnitId") if isinstance(n, dict) else None for n in nodos]

    for campo in ("graphRunId", "taskKey", "planFingerprint", "requestedBy", "startedAt"):
        if doc.get(campo) != inicio.get(campo):
            errores.append("$.%s: no es el de su inicio.json" % campo)
    if ids != inicio.get("order"):
        errores.append("$.nodes: no tiene exactamente los workUnitId de inicio.json, en el orden de "
                       "`order`")
    todos = bool(nodos) and all(isinstance(n, dict) and n.get("state") == SATISFIED for n in nodos)
    if (estado == "SUCCEEDED") != todos:
        errores.append("$.status: SUCCEEDED si y solo si todos los nodes estan SATISFIED")
    if (estado == "FAILED") != (error is not None):
        errores.append("$.error: FAILED lleva un error, y SUCCEEDED y CANCELLED no")
    if isinstance(error, dict):
        unidad = error.get("workUnitId")
        if unidad is not None and unidad not in ids:
            errores.append("$.error.workUnitId: `%s` no es una de las unidades de nodes" % unidad)
        for campo, valor in error.items():
            if campo == "detail" and (not isinstance(valor, str) or not valor.strip()
                                      or len(valor) > contrato.TOPE_DE_DETALLE):
                errores.append("$.error.%s: texto de hasta %d caracteres, no vacio"
                               % (campo, contrato.TOPE_DE_DETALLE))
    inicio_, fin = doc.get("startedAt"), doc.get("endedAt")
    if (isinstance(inicio_, str) and isinstance(fin, str) and contrato.UTC.match(inicio_)
            and contrato.UTC.match(fin) and fin < inicio_):
        errores.append("$.endedAt: es anterior a startedAt")
    return errores


# -- recuperar: el cierre de un huerfano (GD-10, 16.1) -------------------------------------------
#
# 🔴 El que toma el candado de la tarea cierra los huerfanos; nadie reanuda. Un GraphRun ACTIVE que ve
# quien tiene el candado es huerfano, porque con el candado tomado ningun otro conductor vive (14.1). Se
# cierra con el terminal que da la regla de cierre: no se reabre, no se vuelve a despachar nada y ninguna
# Execution existente se vuelve a entregar. Seguir es un GraphRun nuevo, que lee el registro y adopta.

def _propias_abiertas(proyecto, clave, graph_run_id):
    """Las Executions del GraphRun que siguen abiertas: las que una marca de despacho suya nombra y un
    turno nombra tambien (`registro.propias`). Una manual o una ajena de la tarea no esta aca nunca (GE-I19)."""
    return [p for p in registro.propias(proyecto, clave, graph_run_id)
            if p["estado"] in registro.ABIERTOS]


def _cancelar_las_propias(proyecto, clave, graph_run_id, pedido_por, catalogo):
    """`motor.cancelar` sobre cada Execution propia abierta, por el camino de Task 4 (recupera primero y pide
    despues): una REQUESTED sin motor queda CANCELLED, una RUNNING recibe el pedido y el motor mata el
    arbol del Host (17.3). Es cumplir un pedido persistido, no una decision del GraphRun. Nunca una manual
    ni una ajena (GD-11, GE-I18). Devuelve los executionId a los que les pidio cancelar."""
    pedidas = []
    for propia in _propias_abiertas(proyecto, clave, graph_run_id):
        motor.cancelar(proyecto, clave, propia["executionId"], pedido_por, catalogo)
        pedidas.append(propia["executionId"])
    return pedidas


def _causa_del_corte(proyecto, clave, inicio, catalogo_):
    """La causa de GRAPH_INTERRUPTED de un huerfano que dejo una Execution propia abierta o ilegible: el
    `result.json` la nombra, con el comando que la cancela (16.1). Sin una, None: el cierre usa la causa de
    siempre, sin Execution que nombrar."""
    for propia in registro.propias(proyecto, clave, inicio["graphRunId"]):
        if propia["estado"] in registro.ABIERTOS:
            que_sigue = "Para cancelarla: `ejecutar %s --cancelar %s`." % (clave, propia["executionId"])
        elif propia["estado"] == registro.ILEGIBLE:
            que_sigue = "No se lee: revisala con `ejecutar %s --estado`." % clave
        else:
            continue
        return _causa(
            GRAPH_INTERRUPTED, "el conductor se corto y dejo %s (%s) %s, sin motor: no se cancela sola. %s" % (
                propia["workUnitId"], propia["executionId"], propia["estado"], que_sigue),
            catalogo_, propia["workUnitId"], propia["executionId"], propia["estado"])
    return None


def cerrar_huerfano(proyecto, clave, graph_run_id, candado, pedido_por, catalogo=None):
    """16.1: cierra un GraphRun ACTIVE cuyo conductor murio, con el candado de la tarea tomado por quien lo
    llama. El `result.json` escrito, o None si el GraphRun no esta ACTIVE (ya tiene terminal, no se lee o no
    existe): no se toca. Levanta `RegistroInvalido` sin el candado de esa tarea: sin el no se puede afirmar
    que el conductor murio (GM-18).

    1. `motor.recuperar`: las RUNNING sin motor quedan FAILED HOST_INTERRUPTED, o CANCELLED con pedido;
    2. con la marca de cancelacion, `motor.cancelar` sobre cada Execution **propia** abierta;
    3. `result.json` por la regla de cierre (GD-05): SUCCEEDED si todo esta satisfecho, CANCELLED con la
       marca, y si no FAILED con GRAPH_INTERRUPTED.

    Sin la marca una REQUESTED propia sin motor (R2) no se cancela: queda abierta y el resultado la nombra."""
    if not registro.tiene_el_candado(candado, proyecto, clave):
        raise registro.RegistroInvalido(
            "cerrar un GraphRun huerfano exige tener el candado de la tarea %s: sin el no se puede "
            "afirmar que su conductor murio" % clave)
    cargar_catalogo = catalogo or limpieza.cargar_catalogo
    catalogo_ = _catalogo(cargar_catalogo)
    if catalogo_ is None:
        raise motor.ErrorDelComando("no esta el catalogo de secretos: sin el no se persiste nada")
    leido = registro.leer_grafo(proyecto, clave, graph_run_id)
    if leido is None or leido["estado"] != registro.ACTIVE:
        return None
    motor.recuperar(proyecto, clave)                                                   # 1
    if registro.cancelada(proyecto, clave, graph_run_id):                              # 2
        de = (leido["cancelacion"] or {}).get("pedidoPor") or pedido_por
        _cancelar_las_propias(proyecto, clave, graph_run_id, de, cargar_catalogo)
    return cerrar_grafo(proyecto, clave, leido["inicio"],                              # 3
                        _causa_del_corte(proyecto, clave, leido["inicio"], catalogo_), catalogo_)


def cerrar_huerfanos(proyecto, clave, candado, pedido_por, catalogo=None):
    """El paso 2 de `conducir`: cierra todos los GraphRuns ACTIVE de la tarea, que para quien tiene el
    candado son huerfanos. [resultado] de los que cerro. Un GraphRun ilegible no es ACTIVE: no se cierra ni
    se reabre, y el conductor nuevo sigue de largo (no hay un inicio.json del que sacar sus nodos)."""
    cerrados = []
    for graph_run_id in registro.activos(proyecto, clave):
        cerrado = cerrar_huerfano(proyecto, clave, graph_run_id, candado, pedido_por, catalogo)
        if cerrado is not None:
            cerrados.append(cerrado)
    return cerrados


# -- el conductor (GD-07, §10) -----------------------------------------------------------------

class _Conductor(object):
    """El estado de un `conducir`: el GraphRun ya creado y con que se llama al motor."""

    def __init__(self, proyecto, clave, pedido_por, inicio, catalogo_, motor_kw, ganchos):
        self.proyecto = proyecto
        self.clave = clave
        self.pedido_por = pedido_por
        self.inicio = inicio
        self.graph_run_id = inicio["graphRunId"]
        self.huella = inicio["planFingerprint"]
        self.orden = inicio["order"]
        self.dependencias = dict((n["workUnitId"], n["dependencies"]) for n in inicio["nodes"])
        self.catalogo = catalogo_
        self.motor_kw = motor_kw
        self.ganchos = ganchos

    def _gancho(self, nombre, *args):
        if self.ganchos.get(nombre) is not None:
            self.ganchos[nombre](*args)

    def _cancelada(self):
        return registro.cancelada(self.proyecto, self.clave, self.graph_run_id)

    def _nodo(self, unidad):
        return _nodo(self.proyecto, self.clave, self.huella, unidad)

    def _causa(self, codigo, texto, unidad=None, execution_id=None, estado=None, de_execution=None):
        return _causa(codigo, texto, self.catalogo, unidad, execution_id, estado, de_execution)

    def _cerrar(self, causa):
        """El cierre del conductor: el gancho anterior al terminal, y la regla de cierre."""
        self._gancho("antes_del_terminal", self.graph_run_id)
        return cerrar_grafo(self.proyecto, self.clave, self.inicio, causa, self.catalogo)

    def correr(self):
        """Los pasos 7 y 8 de la seccion 10. El resultado escrito, siempre: el GraphRun ya existe."""
        try:
            self._gancho("despues_de_inicio", self.graph_run_id)
            for unidad in self.orden:
                resultado = self._paso(unidad)
                if resultado is not None:
                    return resultado
            return self._cerrar(None)                                                  # 8
        except KeyboardInterrupt:
            # Ctrl-C en el conductor o antes de la entrega (el del Host lo absorbe el motor): cierra por
            # la regla, sin el gancho, y deja salir la interrupcion (16.3, GE-I21).
            cerrar_grafo(self.proyecto, self.clave, self.inicio, self._causa(
                GRAPH_INTERRUPTED, "Ctrl-C sobre el conductor: no se despacho nada mas. Las Executions "
                "quedan como estaban: `ejecutar %s --estado`." % self.clave), self.catalogo)
            raise

    def _paso(self, unidad):
        """7a a 7h para `unidad`: None si sigue con la siguiente, o el resultado ya escrito."""
        if self._cancelada():                                                          # 7a
            return self._cerrar(None)
        huella = _huella_del_plan(self.proyecto, self.clave)                           # 7b
        if huella is None:
            return self._cerrar(self._causa(
                GRAPH_PLAN_UNREADABLE, "el plan de %s no se pudo leer a mitad del GraphRun, antes de "
                "despachar %s. Si se estaba escribiendo, lanzá `ejecutar %s --grafo` de nuevo."
                % (self.clave, unidad, self.clave), unidad))
        if huella != self.huella:
            return self._cerrar(self._plan_cambio(unidad))

        nodo = self._nodo(unidad)                                                      # 7c
        if nodo["state"] == SATISFIED:
            return None                       # adoptada, o despachada antes por este GraphRun
        if nodo["state"] != NOT_STARTED:
            return self._cerrar(self._de_un_nodo(unidad, nodo))
        causa = self._inelegible(unidad)                                               # GD-08
        if causa is not None:
            return self._cerrar(causa)
        ajena = _primera_abierta(self.proyecto, self.clave)                            # 7d
        if ajena is not None:
            return self._cerrar(self._abierta(unidad, ajena["executionId"], ajena["estado"]))

        execution_id = registro.nuevo_id()                                             # 7e
        marca = registro.registrar_despacho(self.proyecto, self.clave, self.graph_run_id, unidad,
                                            execution_id)
        self._gancho("despues_del_despacho", marca)
        if self._cancelada():                                                          # 7f
            return self._cerrar(None)
        try:                                                                           # 7g
            _, error = motor.ejecutar(
                self.proyecto, self.clave, unidad, self.pedido_por, execution_id=execution_id,
                huella_esperada=self.huella, **self.motor_kw)
        except motor.ErrorDelComando:
            estado, de_execution = _de_la_execution(self.proyecto, self.clave, execution_id)
            return self._cerrar(self._causa(
                DISPATCH_FAILED, "el motor levanto un error del comando al despachar %s (%s)%s: no "
                "se despacho nada mas. Revisá `ejecutar %s --estado`." % (
                    unidad, execution_id, "" if estado is None else ", que quedo %s" % estado,
                    self.clave), unidad, execution_id, estado, de_execution))
        self._gancho("despues_del_retorno", marca)
        return self._derivar(unidad, execution_id, error)                              # 7h

    def _derivar(self, unidad, execution_id, error):
        """7h: derivar otra vez, en este orden. Lo que decide es el registro y el plan, no el rechazo."""
        huella = _huella_del_plan(self.proyecto, self.clave)
        if huella is not None and huella != self.huella:
            return self._cerrar(self._plan_cambio(unidad))
        if self._nodo(unidad)["state"] == SATISFIED:
            return None
        ajena = _primera_abierta(self.proyecto, self.clave, execution_id)
        if ajena is not None:
            return self._cerrar(self._abierta(unidad, ajena["executionId"], ajena["estado"]))
        if _de_la_execution(self.proyecto, self.clave, execution_id)[0] is not None:
            return self._cerrar(self._sin_exito(unidad, execution_id))
        codigo = error.get("code") if error else None
        return self._cerrar(self._causa(
            ADMISSION_REJECTED, "la admision rechazo pedir %s%s: no hay Execution. Corregí la causa y "
            "lanzá `ejecutar %s --grafo` de nuevo." % (
                unidad, "" if codigo is None else " (%s)" % codigo, self.clave), unidad,
            de_execution=codigo))

    def _inelegible(self, unidad):
        """GD-08: una unidad es elegible si todas sus dependencias estan SATISFIED bajo F. Lo decide el
        conductor, no la admision: el orden es topologico y cada anterior se cerro o quedo satisfecha, asi
        que solo un registro que cambio por detras llega aca. Devuelve la causa de la primera que no."""
        for dependencia in self.dependencias[unidad]:
            nodo = self._nodo(dependencia)
            if nodo["state"] != SATISFIED:
                return self._de_un_nodo(dependencia, nodo, "no se despacha %s" % unidad)
        return None

    def _de_un_nodo(self, unidad, nodo, que_sigue=None):
        """La causa de cierre de un nodo que no esta SATISFIED (7c): abierto o ilegible es
        TASK_EXECUTION_OPEN, y terminal no exitoso es WORK_UNIT_NOT_SUCCEEDED. Sin turno solo se llega por
        una dependencia, cuando el registro cambio por detras: es lo mismo, sin Execution que nombrar."""
        if nodo["state"] == NOT_STARTED:
            return self._causa(
                WORK_UNIT_NOT_SUCCEEDED, "%s no tiene Execution bajo la huella del GraphRun, y %s." % (
                    unidad, que_sigue or "el GraphRun se detiene"), unidad)
        if nodo["state"] == NOT_SATISFIED:
            return self._sin_exito(unidad, nodo["executionId"])
        return self._abierta(unidad, nodo["executionId"])

    def _plan_cambio(self, unidad):
        return self._causa(
            PLAN_FINGERPRINT_CHANGED, "el plan de %s cambio: su huella ya no es la del GraphRun (%s) "
            "y no se despacha %s. Lanzá `ejecutar %s --grafo` de nuevo: atado a la huella nueva, "
            "despacha de cero." % (self.clave, self.huella[:19], unidad, self.clave), unidad)

    def _sin_exito(self, unidad, execution_id):
        """WORK_UNIT_NOT_SUCCEEDED: la Execution de `unidad` terminal y no exitosa (FAILED, CANCELLED o
        REJECTED), o ilegible. Nunca se reintenta sola (GD-09): la reintenta una persona."""
        estado, de_execution = _de_la_execution(self.proyecto, self.clave, execution_id)
        return self._causa(
            WORK_UNIT_NOT_SUCCEEDED, "%s (%s) quedo %s%s y el GraphRun se detiene. Para reintentarla: "
            "`ejecutar %s --unidad %s` y despues `ejecutar %s --grafo`." % (
                unidad, execution_id, estado, "" if de_execution is None else " por %s" % de_execution,
                self.clave, unidad, self.clave), unidad, execution_id, estado, de_execution)

    def _abierta(self, unidad, execution_id, estado=None):
        """TASK_EXECUTION_OPEN: una Execution abierta o ilegible que este GraphRun no esta corriendo. No la
        cancela, no la espera y no la toma como propia (GD-15): dice como se cancela. Un turno que no se
        lee no nombra a ninguna (`execution_id` None): es ilegible y no hay nada que cancelar."""
        if execution_id is None:
            estado = registro.ILEGIBLE
            texto = ("hay un turno ilegible en %s: no se despacha %s. Revisá `ejecutar %s --estado`."
                     % (self.clave, unidad, self.clave))
        else:
            if estado is None:
                estado, _ = _de_la_execution(self.proyecto, self.clave, execution_id)
            texto = ("%s (%s) esta abierta en %s y este GraphRun no la corre: no se despacha %s. Si "
                     "su motor murio, cancelala: `ejecutar %s --cancelar %s`." % (
                         execution_id, estado, self.clave, unidad, self.clave, execution_id))
        return self._causa(TASK_EXECUTION_OPEN, texto, unidad, execution_id, estado)


# -- conducir ------------------------------------------------------------------------------------

def conducir(proyecto, clave, pedido_por, adaptador=None, config=None, catalogo=None, compuerta=None,
             cargar_registro=None, ganchos=None):
    """(resultado, None) con el graph-run-result/1.0 de un GraphRun que llego a un terminal, o
    (None, {code, detail}) si no empezo: GRAPH_ALREADY_ACTIVE, GRAPH_PLAN_UNREADABLE o
    GRAPH_STRUCTURE_INVALID, y entonces no hay un GraphRun ni una Execution. Levanta
    `motor.ErrorDelComando`, sin crear nada, si falla la configuracion, el catalogo de secretos, la
    TaskKey o quien pide, o si no se puede tomar el candado.

    Con el candado tomado cierra los GraphRuns huerfanos de la tarea (16.1, paso 2) antes de crear el suyo:
    nunca reanuda uno.

    Los parametros son los de `motor.ejecutar`, que los recibe tal cual en cada despacho. `ganchos` son los
    puntos de encuentro de los tests, un dict de `GANCHOS` a funcion: `despues_de_inicio(graphRunId)`,
    `despues_del_despacho(marca)` (con la marca escrita y antes de mirar la cancelacion y de llamar al
    motor), `despues_del_retorno(marca)` (con el motor ya devuelto y antes de derivar), y
    `antes_del_terminal(graphRunId)`. `antes_de_reservar` y `antes_de_entregar` son los del motor. Una
    excepcion que no es Ctrl-C sale sin cerrar: el GraphRun queda huerfano y lo cierra quien tome el
    candado despues (16.3)."""
    ganchos = dict(ganchos or {})
    desconocidos = sorted(set(ganchos) - set(GANCHOS))
    if desconocidos:
        raise ValueError("ganchos que el conductor no tiene: %s" % ", ".join(desconocidos))
    config = config or motor.configuracion(proyecto)                                   # 0
    cargar_catalogo = catalogo or limpieza.cargar_catalogo
    catalogo_ = _catalogo(cargar_catalogo)
    if catalogo_ is None:
        raise motor.ErrorDelComando("no esta el catalogo de secretos: sin el no se persiste nada")
    if not registro.es(registro.CLAVE_DE_TAREA, clave):
        raise motor.ErrorDelComando("%r no es una TaskKey" % (clave,))
    if not isinstance(pedido_por, str) or not pedido_por.strip():
        raise motor.ErrorDelComando("falta quien pide el GraphRun")

    try:                                                                               # 1
        candado = registro.CandadoDeTarea(proyecto, clave)
    except OSError as e:
        raise motor.ErrorDelComando("no se pudo tomar el candado de la tarea (%s): el GraphRun no "
                                    "sigue sin el" % type(e).__name__)
    if not candado:
        return None, _rechazo(GRAPH_ALREADY_ACTIVE, "el candado de la tarea %s esta tomado: hay otro "
                              "conductor, y no se crea un GraphRun. Esperá a que termine, o mirá "
                              "`ejecutar %s --grafo --estado`." % (clave, clave), catalogo_)
    try:
        # 2: con el candado, ningun otro conductor vive: todo GraphRun ACTIVE es huerfano. Se cierran por la
        # regla de cierre (16.1), y se barren las carpetas grf_... sin inicio.json y los temporales viejos.
        cerrar_huerfanos(proyecto, clave, candado, pedido_por, catalogo)
        registro.barrer_grafos(proyecto, clave, candado)
        registro.limpiar_temporales_de_grafos(proyecto, clave, candado)
        motor.recuperar(proyecto, clave)                                               # 3
        try:                                                                           # 4
            plan = admision.leer_plan(proyecto, clave)
        except admision.Rechazo as r:
            return None, _rechazo(GRAPH_PLAN_UNREADABLE, r.detalle, catalogo_)
        meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
        if meta.get("task_key") != clave:
            return None, _rechazo(GRAPH_PLAN_UNREADABLE, "el plan guardado es de %s y se pidio %s"
                                  % (meta.get("task_key"), clave), catalogo_)
        orden, motivo = _estructura(plan["workUnits"])                                 # 5
        if orden is None:
            return None, _rechazo(GRAPH_STRUCTURE_INVALID, motivo, catalogo_)

        por, _ = limpieza.redactar(pedido_por, catalogo_, "$.requestedBy")
        inicio = {"graphRunId": registro.nuevo_id_de_grafo(), "taskKey": clave,
                  "planFingerprint": contrato.huella(plan), "planId": meta.get("plan_id"),
                  "planVersion": meta.get("plan_version"), "requestedBy": por,
                  "startedAt": registro.ahora(),
                  "nodes": [{"workUnitId": u["id"], "dependencies": list(u.get("dependencies", []))}
                            for u in plan["workUnits"]], "order": orden}
        try:                                                                           # 6
            registro.crear_grafo(proyecto, inicio)
        except registro.RegistroInvalido as e:
            return None, _rechazo(GRAPH_STRUCTURE_INVALID, "el plan no se puede congelar en el "
                                  "inicio.json del GraphRun: %s" % e, catalogo_)
        motor_kw = {"adaptador": adaptador, "config": config, "catalogo": catalogo,
                    "compuerta": compuerta, "cargar_registro": cargar_registro,
                    "antes_de_reservar": ganchos.get("antes_de_reservar"),
                    "antes_de_entregar": ganchos.get("antes_de_entregar")}
        return _Conductor(proyecto, clave, pedido_por, inicio, catalogo_, motor_kw, ganchos).correr(), None
    finally:
        candado.soltar()


# -- cancelar el grafo (GD-11, §17) --------------------------------------------------------------

# Cuanto espera quien cancela a un conductor vivo, y cada cuanto vuelve a mirar (17, paso 3).
ESPERA = 60
INTERVALO = 1.0


def cancelar_grafo(proyecto, clave, graph_run_id, pedido_por, catalogo=None, espera=ESPERA,
                   intervalo=INTERVALO):
    """`ejecutar <KEY> --cancelar grf_...` (GD-11): una marca, propagada solo a lo propio.

    1. el GraphRun tiene que existir; si ya es terminal lo informa y no escribe nada;
    2. escribe `cancelacion.json` una vez, con `pedido_por` redactado: la marca va PRIMERO, y si ya estaba
       sigue (GE-I18). Con la marca vista el conductor no despacha (7a, 7f);
    3. intenta tomar el candado de la tarea. Si lo toma, el conductor murio: cierra el huerfano como 16.1, que
       propaga la cancelacion. Si no, el conductor vive: cada `intervalo` segundos, durante a lo sumo
       `espera`, llama a `motor.cancelar` sobre cada Execution PROPIA abierta (la que una marca de despacho
       suya y un turno nombran: nunca una manual ni una ajena) e intenta el candado. Cuando lo toma, si el
       conductor ya escribio el terminal termina, y si no cierra como 16.1;
    4. informa el estado antes y despues.

    {graphRunId, antes, despues, pedido, marcaNueva, conductorVivo, cerradoAqui, canceladas, sigue,
    resultado}. `conductorVivo` es si el candado estaba tomado al pedir; `sigue`, si a la hora de salir el
    GraphRun sigue ACTIVE: el pedido quedo persistido y el conductor lo va a cumplir. Levanta
    `ErrorDelComando`, sin escribir, con un id que no se usa, un GraphRun que no existe o no se lee, o sin
    catalogo de secretos."""
    if not registro.es(registro.CLAVE_DE_TAREA, clave) or not registro.es(registro.ID_DE_GRAFO,
                                                                           graph_run_id):
        raise motor.ErrorDelComando("la TaskKey o el graphRunId no se pueden usar")
    cargar_catalogo = catalogo or limpieza.cargar_catalogo
    leido = registro.leer_grafo(proyecto, clave, graph_run_id)
    if leido is None:
        raise motor.ErrorDelComando("%s no es un GraphRun de %s: no tiene inicio.json"
                                    % (graph_run_id, clave))
    if leido["estado"] == registro.ILEGIBLE:
        raise motor.ErrorDelComando("%s es ilegible: %s" % (graph_run_id, leido["motivo"]))
    salida = {"graphRunId": graph_run_id, "antes": leido["estado"], "despues": leido["estado"],
              "pedido": False, "marcaNueva": False, "conductorVivo": False, "cerradoAqui": False,
              "canceladas": [], "sigue": False, "resultado": leido["resultado"]}
    if leido["estado"] != registro.ACTIVE:
        return salida                                                  # terminal: se informa, no se escribe
    catalogo_ = _catalogo(cargar_catalogo)
    if catalogo_ is None:
        raise motor.ErrorDelComando("no esta el catalogo de secretos: sin el no se persiste nada")
    por, _ = limpieza.redactar(pedido_por or "?", catalogo_, "$.pedidoPor")
    try:                                                               # la marca va primero
        registro.marcar_cancelacion(proyecto, clave, graph_run_id, por)
        salida["marcaNueva"] = True
    except FileExistsError:
        pass
    salida["pedido"] = True

    limite = time.time() + espera
    while True:
        try:
            candado = registro.CandadoDeTarea(proyecto, clave)
        except OSError as e:
            raise motor.ErrorDelComando("no se pudo tomar el candado de la tarea (%s): el pedido quedo "
                                        "escrito, pero no se pudo cerrar" % type(e).__name__)
        if candado:
            try:                                                       # el conductor murio, o ya termino
                salida["cerradoAqui"] = cerrar_huerfano(proyecto, clave, graph_run_id, candado, por,
                                                        catalogo) is not None
            finally:
                candado.soltar()
            break
        salida["conductorVivo"] = True
        for execution_id in _cancelar_las_propias(proyecto, clave, graph_run_id, por, cargar_catalogo):
            if execution_id not in salida["canceladas"]:
                salida["canceladas"].append(execution_id)
        if time.time() >= limite:
            break
        time.sleep(max(0, min(intervalo, limite - time.time())))
    final = registro.leer_grafo(proyecto, clave, graph_run_id)
    salida.update(despues=final["estado"], resultado=final["resultado"],
                  sigue=final["estado"] == registro.ACTIVE)
    return salida


# -- el estado de los GraphRuns (GE-I30) ------------------------------------------------------------

def estado_de_grafos(proyecto, clave):
    """`ejecutar <KEY> --grafo --estado`: los GraphRuns de la tarea, en el orden en que empezaron. SOLO LEE:
    no recupera, no cierra huerfanos, no sondea el candado de la tarea ni el de ninguna Execution, y no
    escribe nada (GE-E70). Un ACTIVE puede ser un conductor vivo o uno muerto, y desde afuera no se sabe
    cual: dice como lo cierra, si murio, el proximo `--grafo` o `--cancelar grf_...`.

    [{graphRunId, estado, motivo, taskKey, planFingerprint, requestedBy, startedAt, endedAt,
    cancelRequested, despachos, error, comandos}]. `estado` es ACTIVE, el terminal, o ILEGIBLE (su
    inicio.json o su result.json no validan: no se cierra, y `motivo` dice por que). `despachos` es
    [{numero, workUnitId, executionId, estado}] con el estado derivado de cada Execution que un turno
    nombra, y None si ninguno la nombra (el corte G2). `error` es el del terminal, o None."""
    if not registro.es(registro.CLAVE_DE_TAREA, clave):
        raise motor.ErrorDelComando("%r no es una TaskKey" % (clave,))
    con_turno = set(e for _, _, e, _ in registro.nombradas(proyecto, clave) if e)
    filas = []
    for graph_run_id in registro.grafos_de(proyecto, clave):
        leido = registro.leer_grafo(proyecto, clave, graph_run_id)
        inicio, terminal = leido["inicio"] or {}, leido["resultado"] or {}
        despachos = []
        for numero, marca, motivo in leido["despachos"]:
            if marca is None:
                despachos.append({"numero": numero, "workUnitId": None, "executionId": None,
                                  "estado": registro.ILEGIBLE})
                continue
            nombrada = marca["executionId"] in con_turno
            despachos.append({
                "numero": numero, "workUnitId": marca["workUnitId"], "executionId": marca["executionId"],
                "estado": registro.estado(proyecto, clave, marca["executionId"])["estado"]
                if nombrada else None})
        filas.append({
            "graphRunId": graph_run_id, "estado": leido["estado"], "motivo": leido["motivo"],
            "taskKey": clave, "planFingerprint": inicio.get("planFingerprint"),
            "requestedBy": inicio.get("requestedBy"), "startedAt": inicio.get("startedAt"),
            "endedAt": terminal.get("endedAt"), "cancelRequested": leido["cancelada"],
            "despachos": despachos, "error": terminal.get("error"),
            "comandos": ["ejecutar %s --grafo" % clave,
                         "ejecutar %s --cancelar %s" % (clave, graph_run_id)]
            if leido["estado"] == registro.ACTIVE else []})
    return sorted(filas, key=lambda f: (f["startedAt"] or "", f["graphRunId"]))
