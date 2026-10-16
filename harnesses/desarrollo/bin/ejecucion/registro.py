"""El registro de las Executions: donde vive cada una y como se sabe en que estado esta.

    .claude/ejecuciones/<TaskKey>/
      claves/<hex de la idempotencyKey>/<NNNNNN>.json    turnos de intento (MD-04)
      <executionId>/
        vivo.lock           el candado de vida del motor (MD-06)
        request.json        execution-request/1.0
        cancelacion.json    un pedido explicito de cancelar
        entrega.json        la marca de entrega: desde aca la Execution esta RUNNING
        prompt-de-sistema.md  el texto del agente que recibe el Host (§34, MD-08′)
        proceso.json        el pid del Host, solo para avisar
        output.md           el artifact redactado
        result.json         execution-result/1.0
      grafos/               los GraphRuns de la tarea (Task 5, GD-12): ninguna funcion de Execution
                            lo nombra ni lo toca
        vivo.lock           el candado de la tarea (§14.1): archivo estable, sin O_EXCL, que no se
                            borra al soltarlo; solo cuenta si esta tomado
        <graphRunId>/
          inicio.json         el GraphRun existe: una vez, al crear
          despachos/<NNN>.json  una vez cada uno, antes de llamar al motor
          cancelacion.json    una vez, a pedido
          result.json         graph-run-result/1.0, una vez, al cerrar

docs/cambios/minimal-execution-engine/spec.md, secciones 12 a 14.
docs/cambios/graph-execution/spec.md, secciones 13, 14.1 y 16.

🔴 Todo se escribe una sola vez (MD-05): un archivo que existe no se pisa nunca, ni el turno, ni la
request, ni el resultado. No hay un archivo de estado: el estado se deriva de cuales existen
(MD-07).

🔴 Una Execution existe si y solo si un turno la nombra (ME-I21). Una carpeta sin turno es un
residuo previo a la publicacion: no la ve nadie, no bloquea nada, y la barre la recuperacion cuando
su candado esta libre y paso el umbral (MD-04d).

🔴 La vida del motor la dice un candado del sistema operativo, nunca una fecha ni un pid: si el
proceso muere, el sistema suelta el candado. Ante la duda, el motor esta vivo.
"""
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import contrato                                     # noqa: E402

if os.name == "nt":
    import msvcrt
else:
    import fcntl

RAIZ = (".claude", "ejecuciones")
CLAVES = "claves"
GRAFOS = "grafos"
DESPACHOS = "despachos"

REQUEST = "request.json"
CANCELACION = "cancelacion.json"
ENTREGA = "entrega.json"
PROCESO = "proceso.json"
OUTPUT = "output.md"
RESULT = "result.json"
VIVO = "vivo.lock"
INICIO = "inicio.json"

# Los ids que se vuelven carpetas se validan con fullmatch, nunca con `$`: un `\n` final no pasa
# (MD-15, ME-14).
ID = re.compile(r"exe_[0-9a-f]{32}")
ID_DE_GRAFO = re.compile(r"grf_[0-9a-f]{32}")
CLAVE_DE_TAREA = re.compile(r"[A-Za-z][A-Za-z0-9_]*-[0-9]+")
HEX = re.compile(r"[0-9a-f]{64}")
HUELLA = re.compile(r"sha256:[0-9a-f]{64}")
TURNO = re.compile(r"[0-9]{6}\.json")
DESPACHO = re.compile(r"[0-9]{3}\.json")
TEMPORAL = re.compile(r"\..+\.tmp")

# Un residuo previo a la publicacion se barre recien con el candado libre y mas de diez minutos.
UMBRAL_DE_RESIDUO = 600

REQUESTED, RUNNING = "REQUESTED", "RUNNING"
ILEGIBLE = "ILEGIBLE"
ABIERTOS = (REQUESTED, RUNNING)

# El estado de un GraphRun (GD-04): ACTIVE es un `inicio.json` sin `result.json`.
ACTIVE = "ACTIVE"
TERMINALES_DE_GRAFO = ("SUCCEEDED", "FAILED", "CANCELLED")

# Las claves de cada marca del GraphRun, cerradas: las marcas no tienen schema (GD-12).
CLAVES_DE_INICIO = frozenset(("graphRunId", "taskKey", "planFingerprint", "planId", "planVersion",
                              "requestedBy", "startedAt", "nodes", "order"))
CLAVES_DE_NODO = frozenset(("workUnitId", "dependencies"))
CLAVES_DE_DESPACHO = frozenset(("numero", "workUnitId", "executionId", "dispatchedAt"))
CLAVES_DE_PEDIDO = frozenset(("pedidoEn", "pedidoPor"))


class RegistroInvalido(Exception):
    """Un id que no se puede usar como ruta, o un registro que no se puede escribir."""


def ahora():
    """UTC, con el formato del contrato."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def nuevo_id():
    """`exe_` y 128 bits del generador criptografico del sistema (MD-15)."""
    return "exe_" + secrets.token_hex(16)


def nuevo_id_de_grafo():
    """`grf_` y 128 bits del generador criptografico del sistema (GD-03). No sale de la TaskKey, de la
    huella del plan, del pid, de la sesion ni de la hora: un GraphRun que se vuelve a lanzar es otro."""
    return "grf_" + secrets.token_hex(16)


def es(patron, valor):
    return isinstance(valor, str) and patron.fullmatch(valor) is not None


def _exigir(patron, valor, que):
    if not es(patron, valor):
        raise RegistroInvalido("%s no se puede usar como ruta: %r" % (que, valor))
    return valor


# -- las rutas -----------------------------------------------------------------------------

def carpeta_de_tarea(proyecto, clave):
    return os.path.join(proyecto, *(RAIZ + (_exigir(CLAVE_DE_TAREA, clave, "la TaskKey"),)))


def carpeta_de(proyecto, clave, execution_id):
    return os.path.join(carpeta_de_tarea(proyecto, clave),
                        _exigir(ID, execution_id, "el executionId"))


def carpeta_de_clave(proyecto, clave, idempotency_key):
    hexa = idempotency_key[len("sha256:"):] if isinstance(idempotency_key, str) and \
        idempotency_key.startswith("sha256:") else None
    return os.path.join(carpeta_de_tarea(proyecto, clave), CLAVES,
                        _exigir(HEX, hexa, "la idempotencyKey"))


def ruta_del_turno(proyecto, clave, idempotency_key, numero):
    if not isinstance(numero, int) or isinstance(numero, bool) or not 0 < numero < 1000000:
        raise RegistroInvalido("el turno %r no se puede usar como ruta" % (numero,))
    return os.path.join(carpeta_de_clave(proyecto, clave, idempotency_key), "%06d.json" % numero)


def relativa(proyecto, ruta):
    """La ruta relativa POSIX desde la raiz del proyecto."""
    return os.path.relpath(ruta, proyecto).replace(os.sep, "/")


# -- la ruta canonica (MD-16) ----------------------------------------------------------------

_ESQUEMA = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def ruta_mala(proyecto, ruta):
    """Por que una ruta no es canonica, o None. Mas estricta que `contrato._ruta_mala`."""
    if not isinstance(ruta, str) or not ruta:
        return "esta vacia"
    if any(ord(c) < 32 or ord(c) == 127 for c in ruta):
        return "tiene un caracter de control"
    if "\\" in ruta:
        return "no es POSIX"
    if ruta.startswith("/"):
        return "es absoluta"
    if _ESQUEMA.match(ruta):
        return "tiene esquema o unidad"
    if ruta.startswith("~"):
        return "empieza con ~"
    if ruta.endswith("/"):
        return "termina en /"
    tramos = ruta.split("/")
    if any(t in ("", ".", "..") for t in tramos):
        return "tiene un tramo vacio, . o .."
    raiz = os.path.realpath(proyecto)
    real = os.path.realpath(os.path.join(raiz, *tramos))
    try:
        adentro = os.path.commonpath([os.path.normcase(raiz), os.path.normcase(real)]) == \
            os.path.normcase(raiz)
    except ValueError:
        adentro = False
    if not adentro or os.path.normcase(real) == os.path.normcase(raiz):
        return "sale del proyecto"
    return None


def comparable(ruta):
    """Como se comparan dos rutas: sin distinguir mayusculas en Windows y en macOS."""
    return ruta.casefold() if sys.platform in ("win32", "darwin") else ruta


def repetidas(rutas):
    vistas, salida = {}, []
    for r in rutas:
        c = comparable(r)
        if c in vistas and r not in salida:
            salida.append(r)
        vistas.setdefault(c, r)
    return salida


# -- la escritura de una sola vez (MD-05) ----------------------------------------------------

def escribir_una_vez(ruta, datos):
    """Crea `ruta` con `datos`, o levanta FileExistsError sin tocarla.

    Temporal exclusivo en la misma carpeta, fsync, y `os.link`, que es atomico y no reemplaza. El
    temporal se borra siempre. En un sistema de archivos sin enlaces duros `os.link` falla, y el
    motor no sigue sin esta primitiva.
    """
    carpeta, nombre = os.path.split(ruta)
    descriptor, temporal = tempfile.mkstemp(prefix="." + nombre + ".", suffix=".tmp", dir=carpeta)
    try:
        try:
            vista = memoryview(datos)
            while vista:
                vista = vista[os.write(descriptor, vista):]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(temporal, ruta)
    finally:
        try:
            os.unlink(temporal)
        except OSError:
            pass


def bytes_de(doc):
    return (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def escribir_json(ruta, doc):
    escribir_una_vez(ruta, bytes_de(doc))


def leer_json(ruta):
    """(doc, None), (None, None) si no esta, o (None, motivo)."""
    try:
        with io.open(ruta, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, None
    except (OSError, ValueError) as e:
        return None, "%s: %s" % (os.path.basename(ruta), type(e).__name__)


# -- el candado de vida (MD-06) --------------------------------------------------------------

def _bloquear(descriptor):
    os.lseek(descriptor, 0, os.SEEK_SET)
    if os.name == "nt":
        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _soltar(descriptor):
    os.lseek(descriptor, 0, os.SEEK_SET)
    if os.name == "nt":
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(descriptor, fcntl.LOCK_UN)


class Vida(object):
    """El candado que el motor tiene tomado desde que crea la carpeta hasta que la Execution queda
    terminal. Lo suelta el sistema operativo si el proceso muere."""

    def __init__(self, carpeta):
        self.ruta = os.path.join(carpeta, VIVO)
        self.descriptor = os.open(self.ruta, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        try:
            _bloquear(self.descriptor)
        except OSError:
            os.close(self.descriptor)
            raise

    def soltar(self):
        if self.descriptor is None:
            return
        try:
            _soltar(self.descriptor)
        except OSError:
            pass
        os.close(self.descriptor)
        self.descriptor = None


def candado_libre(carpeta):
    """True si nadie tiene el candado (el motor murio), False si esta tomado o no se sabe, None si
    no hay `vivo.lock`. Si se toma, se suelta enseguida."""
    try:
        descriptor = os.open(os.path.join(carpeta, VIVO), os.O_RDONLY)
    except FileNotFoundError:
        return None
    except OSError:
        return False
    try:
        try:
            _bloquear(descriptor)
        except OSError:
            return False
        try:
            _soltar(descriptor)
        except OSError:
            pass
        return True
    finally:
        os.close(descriptor)


class Tomado(object):
    """El candado de una Execution huerfana, tomado por quien la va a cerrar."""

    def __init__(self, carpeta):
        self.descriptor = None
        try:
            descriptor = os.open(os.path.join(carpeta, VIVO), os.O_RDONLY)
        except OSError:
            return
        try:
            _bloquear(descriptor)
        except OSError:
            os.close(descriptor)
            return
        self.descriptor = descriptor

    def __bool__(self):
        return self.descriptor is not None

    __nonzero__ = __bool__

    def soltar(self):
        if self.descriptor is not None:
            try:
                _soltar(self.descriptor)
            except OSError:
                pass
            os.close(self.descriptor)
            self.descriptor = None


# -- los turnos (MD-04) ----------------------------------------------------------------------

def _turno_valido(doc):
    return (isinstance(doc, dict) and set(doc) == {"executionId", "reservadoEn"}
            and es(ID, doc.get("executionId")) and isinstance(doc.get("reservadoEn"), str)
            and contrato.UTC.match(doc["reservadoEn"]) is not None)


def turnos(proyecto, clave, idempotency_key):
    """[(numero, ruta)] de los turnos de una clave, en orden."""
    carpeta = carpeta_de_clave(proyecto, clave, idempotency_key)
    try:
        nombres = os.listdir(carpeta)
    except FileNotFoundError:
        return []
    return sorted((int(n[:6]), os.path.join(carpeta, n)) for n in nombres if es(TURNO, n))


def leer_turno(ruta):
    """(executionId, None) o (None, motivo)."""
    doc, motivo = leer_json(ruta)
    if doc is None:
        return None, motivo or "el turno no esta"
    if not _turno_valido(doc):
        return None, "%s no es un turno valido" % os.path.basename(ruta)
    return doc["executionId"], None


def ultimo_turno(proyecto, clave, idempotency_key):
    """{numero, executionId, estado, motivo} del ultimo turno, o None si la clave no tiene."""
    lista = turnos(proyecto, clave, idempotency_key)
    if not lista:
        return None
    numero, ruta = lista[-1]
    execution_id, motivo = leer_turno(ruta)
    if execution_id is None:
        return {"numero": numero, "executionId": None, "estado": ILEGIBLE, "motivo": motivo}
    derivado = estado(proyecto, clave, execution_id)
    return {"numero": numero, "executionId": execution_id, "estado": derivado["estado"],
            "motivo": derivado["motivo"]}


def reservar(proyecto, clave, idempotency_key, numero, execution_id):
    """Crea el turno `numero`. False si ya existe: otra admision gano."""
    try:
        escribir_json(ruta_del_turno(proyecto, clave, idempotency_key, numero),
                      {"executionId": execution_id, "reservadoEn": ahora()})
    except FileExistsError:
        return False
    return True


def nombrada(proyecto, clave, idempotency_key, numero, execution_id):
    """Si el turno `numero` existe y nombra a `execution_id`."""
    ruta = ruta_del_turno(proyecto, clave, idempotency_key, numero)
    return os.path.isfile(ruta) and leer_turno(ruta)[0] == execution_id


def crear(proyecto, request, leido, antes_de_reservar=None):
    """Los pasos 2 a 6 de MD-04: la carpeta, el candado, la request y el turno `leido + 1`.

    Devuelve la Vida del motor si la Execution quedo publicada, o None si otra admision gano: en
    ese caso la carpeta propia, que nadie mas conoce, ya se borro. Una falla antes de publicar
    tambien borra la carpeta; despues de publicar, nunca.
    """
    clave = request["taskKey"]
    execution_id = request["executionId"]
    llave = request["idempotencyKey"]
    carpeta = carpeta_de(proyecto, clave, execution_id)
    os.makedirs(os.path.join(carpeta_de_tarea(proyecto, clave), CLAVES), exist_ok=True)
    os.mkdir(carpeta)
    vida = None
    try:
        vida = Vida(carpeta)
        escribir_json(os.path.join(carpeta, REQUEST), request)
        if antes_de_reservar is not None:
            antes_de_reservar()
        os.makedirs(carpeta_de_clave(proyecto, clave, llave), exist_ok=True)
        publicada = reservar(proyecto, clave, llave, leido + 1, execution_id)
    except BaseException:
        if not nombrada(proyecto, clave, llave, leido + 1, execution_id):
            if vida is not None:
                vida.soltar()
            shutil.rmtree(carpeta, ignore_errors=True)
        raise
    if not publicada:
        vida.soltar()
        shutil.rmtree(carpeta, ignore_errors=True)
        return None
    return vida


# -- el estado derivado (MD-07) --------------------------------------------------------------

def estado(proyecto, clave, execution_id):
    """{estado, request, entrega, resultado, motivo} de una Execution que un turno nombra.

    REQUESTED, RUNNING, un terminal, o ILEGIBLE si la request o el resultado no validan: una
    ilegible cuenta como abierta para los duplicados.
    """
    carpeta = carpeta_de(proyecto, clave, execution_id)
    salida = {"estado": ILEGIBLE, "request": None, "entrega": None, "resultado": None,
              "motivo": None}
    request, motivo = leer_json(os.path.join(carpeta, REQUEST))
    if request is None:
        salida["motivo"] = motivo or "no tiene request.json"
        return salida
    errores = contrato.validar_request(request)
    if errores or request.get("executionId") != execution_id or request.get("taskKey") != clave:
        salida["motivo"] = "request.json no valida: %s" % (errores[0] if errores else
                                                           "no es de esta Execution")
        return salida
    salida["request"] = request
    entrega, _ = leer_json(os.path.join(carpeta, ENTREGA))
    salida["entrega"] = entrega
    if os.path.exists(os.path.join(carpeta, RESULT)):
        resultado, motivo = leer_json(os.path.join(carpeta, RESULT))
        errores = contrato.validar_resultado(resultado, request) if resultado is not None else []
        if resultado is None or errores:
            salida["motivo"] = "result.json no valida: %s" % (errores[0] if errores else motivo)
            return salida
        salida.update(estado=resultado["status"], resultado=resultado)
        return salida
    salida["estado"] = RUNNING if os.path.exists(os.path.join(carpeta, ENTREGA)) else REQUESTED
    return salida


def claves_de(proyecto, clave):
    """Los hex de las idempotencyKey con turnos en la tarea."""
    carpeta = os.path.join(carpeta_de_tarea(proyecto, clave), CLAVES)
    try:
        return sorted(n for n in os.listdir(carpeta) if es(HEX, n))
    except FileNotFoundError:
        return []


def nombradas(proyecto, clave):
    """[(hex, numero, executionId o None, motivo)] de cada turno de la tarea."""
    salida = []
    for hexa in claves_de(proyecto, clave):
        for numero, ruta in turnos(proyecto, clave, "sha256:" + hexa):
            execution_id, motivo = leer_turno(ruta)
            salida.append((hexa, numero, execution_id, motivo))
    return salida


def carpetas(proyecto, clave):
    """Los executionId que tienen carpeta en la tarea, sean Executions o residuos."""
    try:
        return sorted(n for n in os.listdir(carpeta_de_tarea(proyecto, clave)) if es(ID, n))
    except FileNotFoundError:
        return []


def tareas(proyecto):
    """Las TaskKey con registro en el proyecto."""
    try:
        return sorted(n for n in os.listdir(os.path.join(proyecto, *RAIZ))
                      if es(CLAVE_DE_TAREA, n))
    except FileNotFoundError:
        return []


def entregada_en(carpeta):
    """Cuando se escribio `entrega.json`, con la precision del sistema de archivos. Los tiempos del
    contrato van al segundo, y dos corridas seguidas caben en el mismo segundo."""
    return os.stat(os.path.join(carpeta, ENTREGA)).st_mtime


def otras_entregadas(proyecto, propio, desde):
    """Si otra Execution del proyecto, de cualquier tarea, estuvo RUNNING desde `desde` (la hora de
    la entrega propia): tiene `entrega.json` y no termino, o su `result.json` se escribio despues.
    Con ella, los cambios no se pueden atribuir."""
    for clave in tareas(proyecto):
        for execution_id in carpetas(proyecto, clave):
            if execution_id == propio:
                continue
            carpeta = carpeta_de(proyecto, clave, execution_id)
            if not os.path.exists(os.path.join(carpeta, ENTREGA)):
                continue
            try:
                fin = os.stat(os.path.join(carpeta, RESULT)).st_mtime
            except OSError:
                return True
            if fin >= desde:
                return True
    return False


# -- los residuos y los temporales (MD-04d) ---------------------------------------------------

def _edad(carpeta):
    for ruta in (os.path.join(carpeta, VIVO), carpeta):
        try:
            return time.time() - os.stat(ruta).st_mtime
        except OSError:
            continue
    return 0


def residuos(proyecto, clave):
    """Las carpetas sin un turno que las nombre."""
    con_turno = set(e for _, _, e, _ in nombradas(proyecto, clave) if e)
    return [e for e in carpetas(proyecto, clave) if e not in con_turno]


def barrer(proyecto, clave, umbral=UMBRAL_DE_RESIDUO):
    """Borra los residuos previos a la publicacion con el candado libre y mas de `umbral`
    segundos. El candado decide y la edad es la guarda, y la guarda va primero: una carpeta nueva
    puede ser una admision en curso, entre su `O_EXCL` y el candado de `Vida`, y una sonda que la
    toca la hace fallar (Task 5 / GD-20, F1). Devuelve los que borro."""
    borrados = []
    for execution_id in residuos(proyecto, clave):
        carpeta = carpeta_de(proyecto, clave, execution_id)
        if _edad(carpeta) <= umbral or candado_libre(carpeta) is False:
            continue
        if execution_id in set(e for _, _, e, _ in nombradas(proyecto, clave) if e):
            continue
        shutil.rmtree(carpeta, ignore_errors=True)
        if not os.path.exists(carpeta):
            borrados.append(execution_id)
    return borrados


def _temporales(carpeta):
    try:
        return [os.path.join(carpeta, n) for n in os.listdir(carpeta) if es(TEMPORAL, n)]
    except OSError:
        return []


def _vencido(ruta, umbral):
    """Si el temporal tiene mas de `umbral` segundos, por su propia fecha."""
    try:
        return time.time() - os.stat(ruta).st_mtime > umbral
    except OSError:
        return False


def limpiar_temporales(proyecto, clave, umbral=UMBRAL_DE_RESIDUO):
    """Los temporales de escritura con mas de `umbral` segundos, por su propia fecha: una escritura
    dura milisegundos. En una carpeta de Execution, y solo si hay alguno vencido, se sondea el
    candado, y si esta libre se borran solo esos (Task 5 / GD-20, F2'): un temporal nuevo puede ser
    de una escritura en curso de otro proceso, y una carpeta sin vencidos no se sondea. Devuelve
    cuantos borro."""
    borrados = 0
    for execution_id in carpetas(proyecto, clave):
        carpeta = carpeta_de(proyecto, clave, execution_id)
        vencidos = [r for r in _temporales(carpeta) if _vencido(r, umbral)]
        if not vencidos or candado_libre(carpeta) is False:
            continue
        for ruta in vencidos:
            try:
                os.unlink(ruta)
                borrados += 1
            except OSError:
                pass
    for hexa in claves_de(proyecto, clave):
        for ruta in _temporales(carpeta_de_clave(proyecto, clave, "sha256:" + hexa)):
            try:
                if _vencido(ruta, umbral):
                    os.unlink(ruta)
                    borrados += 1
            except OSError:
                pass
    return borrados


# -- el GraphRun: cuatro marcas de una sola escritura (Task 5, GD-12, §14.1, §16) -----------------
#
# Todo lo que el GraphRun escribe en disco pasa por aca (ME-E46, GE-I29): `grafo.py` lee y llama a
# estas funciones. Ninguna funcion de arriba nombra `grafos/`: no es una Execution, no es un residuo
# y no cuenta como otra entrega (GE-E62). No hay un `state.json`, ni un puntero a la unidad actual,
# ni un contador: el estado sale de las marcas y del registro de Executions (GD-12).
# Una segunda escritura de una marca levanta FileExistsError, sin tocar la que estaba: gana la primera.

def carpeta_de_grafos(proyecto, clave):
    return os.path.join(carpeta_de_tarea(proyecto, clave), GRAFOS)


def carpeta_de_grafo(proyecto, clave, graph_run_id):
    return os.path.join(carpeta_de_grafos(proyecto, clave),
                        _exigir(ID_DE_GRAFO, graph_run_id, "el graphRunId"))


def ruta_del_despacho(proyecto, clave, graph_run_id, numero):
    if not isinstance(numero, int) or isinstance(numero, bool) or not 0 < numero < 1000:
        raise RegistroInvalido("el despacho %r no se puede usar como ruta" % (numero,))
    return os.path.join(carpeta_de_grafo(proyecto, clave, graph_run_id), DESPACHOS,
                        "%03d.json" % numero)


# -- las claves cerradas de cada marca

def _texto(valor):
    return isinstance(valor, str) and re.search(r"\S", valor) is not None


def _fecha(valor):
    return isinstance(valor, str) and contrato.UTC.fullmatch(valor) is not None


def _entero(valor, desde, hasta=None):
    return (isinstance(valor, int) and not isinstance(valor, bool) and valor >= desde
            and (hasta is None or valor <= hasta))


def _lista_de_textos(valor):
    return isinstance(valor, list) and all(_texto(v) for v in valor)


def _motivo_de_inicio(doc):
    """Por que `doc` no es un inicio.json valido, o None."""
    if not isinstance(doc, dict) or set(doc) != CLAVES_DE_INICIO:
        return "no tiene exactamente las claves de inicio.json"
    if not es(ID_DE_GRAFO, doc["graphRunId"]):
        return "graphRunId no es grf_ y 32 hexadecimales"
    if not es(CLAVE_DE_TAREA, doc["taskKey"]):
        return "taskKey no es una TaskKey"
    if not es(HUELLA, doc["planFingerprint"]):
        return "planFingerprint no es una huella"
    if not _texto(doc["planId"]):
        return "planId no es un texto"
    if not _entero(doc["planVersion"], 1):
        return "planVersion no es un entero desde 1"
    if not _texto(doc["requestedBy"]):
        return "requestedBy no es un texto"
    if not _fecha(doc["startedAt"]):
        return "startedAt no es una fecha UTC"
    nodos = doc["nodes"]
    if not isinstance(nodos, list) or not nodos:
        return "nodes no es una lista con al menos una unidad"
    for nodo in nodos:
        if not isinstance(nodo, dict) or set(nodo) != CLAVES_DE_NODO:
            return "un nodo no tiene exactamente workUnitId y dependencies"
        if not _texto(nodo["workUnitId"]) or not _lista_de_textos(nodo["dependencies"]):
            return "un nodo no tiene un workUnitId y una lista de dependencias, de textos"
    ids = [n["workUnitId"] for n in nodos]
    if len(set(ids)) != len(ids):
        return "nodes repite un workUnitId"
    if not _lista_de_textos(doc["order"]) or sorted(doc["order"]) != sorted(ids):
        return "order no es una permutacion de los workUnitId de nodes"
    return None


def _motivo_de_despacho(doc, numero=None):
    """Por que `doc` no es una marca de despacho valida, o None. Con `numero`, el del archivo."""
    if not isinstance(doc, dict) or set(doc) != CLAVES_DE_DESPACHO:
        return "no tiene exactamente las claves de una marca de despacho"
    if not _entero(doc["numero"], 1, 999) or (numero is not None and doc["numero"] != numero):
        return "numero no es el del archivo"
    if not _texto(doc["workUnitId"]):
        return "workUnitId no es un texto"
    if not es(ID, doc["executionId"]):
        return "executionId no es exe_ y 32 hexadecimales"
    if not _fecha(doc["dispatchedAt"]):
        return "dispatchedAt no es una fecha UTC"
    return None


def _motivo_de_pedido(doc):
    """Por que `doc` no es un cancelacion.json valido, o None."""
    if not isinstance(doc, dict) or set(doc) != CLAVES_DE_PEDIDO:
        return "no tiene exactamente pedidoEn y pedidoPor"
    if not _fecha(doc["pedidoEn"]):
        return "pedidoEn no es una fecha UTC"
    if not _texto(doc["pedidoPor"]):
        return "pedidoPor no es un texto"
    return None


def _motivo_de_terminal(doc, clave, graph_run_id):
    """Por que `doc` no sirve como result.json, o None. Solo lo que hace falta para derivar el
    estado: el schema y las coherencias de graph-run-result/1.0 son de quien lo arma."""
    if not isinstance(doc, dict):
        return "no es un objeto"
    if doc.get("status") not in TERMINALES_DE_GRAFO:
        return "status no es SUCCEEDED, FAILED ni CANCELLED"
    if doc.get("graphRunId") != graph_run_id or doc.get("taskKey") != clave:
        return "no es de este GraphRun"
    return None


def _leer_marca(ruta, motivo_de):
    """(doc, None), (None, None) si no esta, o (None, motivo)."""
    doc, motivo = leer_json(ruta)
    if doc is None:
        return None, motivo or ("%s: no es un objeto" % os.path.basename(ruta)
                                if os.path.exists(ruta) else None)
    razon = motivo_de(doc)
    if razon is not None:
        return None, "%s no es valido: %s" % (os.path.basename(ruta), razon)
    return doc, None


# -- las escrituras

def _con_inicio(proyecto, clave, graph_run_id):
    """La carpeta de un GraphRun que existe: lo que lo hace existir es su inicio.json (GD-04)."""
    carpeta = carpeta_de_grafo(proyecto, clave, graph_run_id)
    if not os.path.exists(os.path.join(carpeta, INICIO)):
        raise RegistroInvalido("el GraphRun %s no existe: no tiene inicio.json" % graph_run_id)
    return carpeta


def crear_grafo(proyecto, inicio):
    """Crea la carpeta del GraphRun y su `inicio.json`, que es lo que lo hace existir. `inicio` trae
    el `graphRunId` y la TaskKey: el que lo escribe tiene tomado el candado de la tarea (§14.1), y
    quien lo llama, el conductor, es quien lo toma. Si el id ya tiene carpeta levanta FileExistsError.
    Una falla antes de publicar `inicio.json` borra la carpeta; una carpeta sin `inicio.json` que
    quede de un corte la barre el proximo que toma el candado (`barrer_grafos`)."""
    razon = _motivo_de_inicio(inicio)
    if razon is not None:
        raise RegistroInvalido("el inicio.json no valida: %s" % razon)
    clave, graph_run_id = inicio["taskKey"], inicio["graphRunId"]
    carpeta = carpeta_de_grafo(proyecto, clave, graph_run_id)
    os.makedirs(carpeta_de_grafos(proyecto, clave), exist_ok=True)
    os.mkdir(carpeta)
    try:
        os.mkdir(os.path.join(carpeta, DESPACHOS))
        escribir_json(os.path.join(carpeta, INICIO), inicio)
    except BaseException:
        if not os.path.exists(os.path.join(carpeta, INICIO)):
            shutil.rmtree(carpeta, ignore_errors=True)
        raise


def _siguiente_despacho(carpeta):
    try:
        nombres = os.listdir(os.path.join(carpeta, DESPACHOS))
    except FileNotFoundError:
        return 1
    return max([int(n[:3]) for n in nombres if es(DESPACHO, n)] or [0]) + 1


def registrar_despacho(proyecto, clave, graph_run_id, work_unit_id, execution_id):
    """La marca de despacho, antes de llamar al motor: nombra el `executionId` preasignado. El numero
    es el siguiente al ultimo que hay, desde 001. Devuelve la marca escrita."""
    carpeta = _con_inicio(proyecto, clave, graph_run_id)
    doc = {"numero": _siguiente_despacho(carpeta), "workUnitId": work_unit_id,
           "executionId": execution_id, "dispatchedAt": ahora()}
    razon = _motivo_de_despacho(doc)
    if razon is not None:
        raise RegistroInvalido("la marca de despacho no valida: %s" % razon)
    escribir_json(ruta_del_despacho(proyecto, clave, graph_run_id, doc["numero"]), doc)
    return doc


def marcar_cancelacion(proyecto, clave, graph_run_id, pedido_por):
    """La marca de cancelacion del GraphRun. La escribe quien cancela, con el conductor vivo: no pide
    el candado de la tarea. `pedido_por` ya viene redactado. Si ya estaba, FileExistsError."""
    carpeta = _con_inicio(proyecto, clave, graph_run_id)
    doc = {"pedidoEn": ahora(), "pedidoPor": pedido_por}
    razon = _motivo_de_pedido(doc)
    if razon is not None:
        raise RegistroInvalido("el cancelacion.json no valida: %s" % razon)
    escribir_json(os.path.join(carpeta, CANCELACION), doc)
    return doc


def escribir_terminal(proyecto, clave, graph_run_id, resultado):
    """El `result.json` del GraphRun, una sola vez: gana el primero (GD-04). Lo escribe quien tiene el
    candado de la tarea: el conductor, o el que cierra un huerfano."""
    carpeta = _con_inicio(proyecto, clave, graph_run_id)
    razon = _motivo_de_terminal(resultado, clave, graph_run_id)
    if razon is not None:
        raise RegistroInvalido("el result.json no sirve: %s" % razon)
    escribir_json(os.path.join(carpeta, RESULT), resultado)


# -- las lecturas

def _ids_de_grafos(proyecto, clave):
    """Los graphRunId que tienen carpeta en la tarea, sean GraphRuns o residuos de la creacion."""
    try:
        return sorted(n for n in os.listdir(carpeta_de_grafos(proyecto, clave))
                      if es(ID_DE_GRAFO, n))
    except FileNotFoundError:
        return []


def grafos_de(proyecto, clave):
    """Los graphRunId de los GraphRuns de la tarea: los que tienen `inicio.json`."""
    return [g for g in _ids_de_grafos(proyecto, clave)
            if os.path.exists(os.path.join(carpeta_de_grafo(proyecto, clave, g), INICIO))]


def residuos_de_grafos(proyecto, clave):
    """Las carpetas `grf_...` sin `inicio.json`: un residuo de la creacion, no un GraphRun."""
    return [g for g in _ids_de_grafos(proyecto, clave)
            if not os.path.exists(os.path.join(carpeta_de_grafo(proyecto, clave, g), INICIO))]


def cancelada(proyecto, clave, graph_run_id):
    """Si existe la marca de cancelacion del GraphRun. Existe o no existe: como la de una Execution
    (`motor.py`), no se lee lo que dice para decidir."""
    return os.path.exists(os.path.join(carpeta_de_grafo(proyecto, clave, graph_run_id), CANCELACION))


def despachos(proyecto, clave, graph_run_id):
    """[(numero, marca, motivo)] de las marcas de despacho, en orden. `marca` es None, con su motivo,
    si la que hay no valida."""
    carpeta = os.path.join(carpeta_de_grafo(proyecto, clave, graph_run_id), DESPACHOS)
    try:
        nombres = sorted(n for n in os.listdir(carpeta) if es(DESPACHO, n))
    except FileNotFoundError:
        return []
    salida = []
    for nombre in nombres:
        numero = int(nombre[:3])
        marca, motivo = _leer_marca(os.path.join(carpeta, nombre),
                                    lambda d, n=numero: _motivo_de_despacho(d, n))
        salida.append((numero, marca, None if marca is not None else (motivo or "no esta")))
    return salida


def leer_grafo(proyecto, clave, graph_run_id):
    """None si no hay un GraphRun con ese id. Si no, {graphRunId, estado, motivo, inicio,
    cancelada, cancelacion, resultado, despachos}.

    `estado` es ACTIVE (`inicio.json` sin `result.json`), el `status` del terminal, o ILEGIBLE si el
    `inicio.json` o el `result.json` no validan: no se cierra, y el motivo dice por que. Un ACTIVE que
    ve quien tiene el candado de la tarea es un huerfano (§14.1). El estado de cada nodo no se
    escribe: se deriva del registro de Executions (§9.2)."""
    carpeta = carpeta_de_grafo(proyecto, clave, graph_run_id)
    if not os.path.exists(os.path.join(carpeta, INICIO)):
        return None
    salida = {"graphRunId": graph_run_id, "estado": ILEGIBLE, "motivo": None, "inicio": None,
              "cancelada": cancelada(proyecto, clave, graph_run_id), "cancelacion": None,
              "resultado": None, "despachos": despachos(proyecto, clave, graph_run_id)}
    inicio, motivo = _leer_marca(os.path.join(carpeta, INICIO), _motivo_de_inicio)
    if inicio is not None and (inicio["graphRunId"] != graph_run_id or inicio["taskKey"] != clave):
        inicio, motivo = None, "inicio.json no es de este GraphRun"
    if inicio is None:
        salida["motivo"] = motivo or "inicio.json no esta"
        return salida
    salida["inicio"] = inicio
    salida["cancelacion"], _ = _leer_marca(os.path.join(carpeta, CANCELACION), _motivo_de_pedido)
    if not os.path.exists(os.path.join(carpeta, RESULT)):
        salida["estado"] = ACTIVE
        return salida
    resultado, motivo = _leer_marca(os.path.join(carpeta, RESULT),
                                    lambda d: _motivo_de_terminal(d, clave, graph_run_id))
    if resultado is None:
        salida["motivo"] = motivo or "result.json no esta"
        return salida
    salida.update(estado=resultado["status"], resultado=resultado)
    return salida


def activos(proyecto, clave):
    """Los GraphRuns ACTIVE de la tarea. Para quien tiene el candado, todos son huerfanos: son los que
    hay que cerrar (§16.1). Sin el candado, no se puede afirmar que lo sean."""
    return [g for g in grafos_de(proyecto, clave)
            if leer_grafo(proyecto, clave, g)["estado"] == ACTIVE]


def propias(proyecto, clave, graph_run_id):
    """[{numero, workUnitId, executionId, estado}] de las Executions del GraphRun: las que nombra una
    de sus marcas de despacho y a la vez nombra un turno (ME-I21). Una marca que ningun turno nombra
    (el corte G2) no es una Execution. `estado` es el derivado, REQUESTED, RUNNING, ILEGIBLE o un
    terminal. Nunca incluye una Execution de la tarea que ninguna marca suya nombra."""
    con_turno = set(e for _, _, e, _ in nombradas(proyecto, clave) if e)
    return [{"numero": numero, "workUnitId": marca["workUnitId"],
             "executionId": marca["executionId"],
             "estado": estado(proyecto, clave, marca["executionId"])["estado"]}
            for numero, marca, _ in despachos(proyecto, clave, graph_run_id)
            if marca is not None and marca["executionId"] in con_turno]


# -- el candado de la tarea (§14.1)

class CandadoDeTarea(object):
    """Ser el conductor de un GraphRun es tener tomado este candado: `grafos/vivo.lock`, con la misma
    primitiva del sistema operativo que el candado de vida, sin esperar. Se toma antes de crear el
    GraphRun y se suelta despues de su terminal; si el proceso muere, lo suelta el sistema.

    El archivo es estable: se abre con O_CREAT y sin O_EXCL, y no se borra nunca, tampoco al soltarlo.
    Que exista no dice nada, solo cuenta si esta tomado: asi no hay un instante en que "existe y no
    esta tomado" quiera decir "el conductor murio" (GD-20, N1). Es falso si otro lo tiene; si no se
    puede ni abrir el archivo (disco, permisos) levanta OSError, que no es lo mismo que "lo tiene otro"."""

    def __init__(self, proyecto, clave):
        os.makedirs(carpeta_de_grafos(proyecto, clave), exist_ok=True)
        self.ruta = os.path.join(carpeta_de_grafos(proyecto, clave), VIVO)
        self.descriptor = None
        descriptor = os.open(self.ruta, os.O_CREAT | os.O_RDWR)
        try:
            _bloquear(descriptor)
        except OSError:
            os.close(descriptor)
            return
        self.descriptor = descriptor

    def __bool__(self):
        return self.descriptor is not None

    __nonzero__ = __bool__

    def soltar(self):
        if self.descriptor is not None:
            try:
                _soltar(self.descriptor)
            except OSError:
                pass
            os.close(self.descriptor)
            self.descriptor = None


def tiene_el_candado(candado, proyecto, clave):
    """Si `candado` es el de la tarea `clave` de este proyecto y esta tomado. Lo exige quien borra de
    `grafos/` y quien cierra un GraphRun huerfano (GD-10, 16.1): solo con el candado se puede afirmar que
    ningun otro conductor vive en la tarea (Task 5 / 5b: grafo.py lo pregunta aca en vez de repetir la
    comparacion de rutas)."""
    return (isinstance(candado, CandadoDeTarea) and bool(candado)
            and candado.ruta == os.path.join(carpeta_de_grafos(proyecto, clave), VIVO))


def _exigir_candado(candado, proyecto, clave, que):
    """Quien borra de `grafos/` tiene que tener el candado de esa tarea: sin el, una carpeta sin
    `inicio.json` puede ser un GraphRun que un conductor vivo esta creando."""
    if not tiene_el_candado(candado, proyecto, clave):
        raise RegistroInvalido("%s exige tener el candado de la tarea %s" % (que, clave))


def barrer_grafos(proyecto, clave, candado):
    """Borra las carpetas `grf_...` sin `inicio.json`, que el conductor anterior no alcanzo a
    publicar (§16.2, G1 antes de `inicio.json`). Sin edad: con el candado tomado ningun otro
    conductor vive en la tarea, asi que ninguna esta en creacion. Devuelve las que borro."""
    _exigir_candado(candado, proyecto, clave, "barrer los GraphRuns sin inicio.json")
    borrados = []
    for graph_run_id in residuos_de_grafos(proyecto, clave):
        carpeta = carpeta_de_grafo(proyecto, clave, graph_run_id)
        shutil.rmtree(carpeta, ignore_errors=True)
        if not os.path.exists(carpeta):
            borrados.append(graph_run_id)
    return borrados


def limpiar_temporales_de_grafos(proyecto, clave, candado, umbral=UMBRAL_DE_RESIDUO):
    """Los temporales de escritura de las carpetas `grf_...` con mas de `umbral` segundos, por su
    propia fecha, como `limpiar_temporales` (GD-20, F2'): un `--cancelar` escribe `cancelacion.json`
    sin el candado, y su temporal nuevo no se toca. Devuelve cuantos borro."""
    _exigir_candado(candado, proyecto, clave, "limpiar los temporales de los GraphRuns")
    borrados = 0
    for graph_run_id in _ids_de_grafos(proyecto, clave):
        carpeta = carpeta_de_grafo(proyecto, clave, graph_run_id)
        for sitio in (carpeta, os.path.join(carpeta, DESPACHOS)):
            for ruta in _temporales(sitio):
                try:
                    if _vencido(ruta, umbral):
                        os.unlink(ruta)
                        borrados += 1
                except OSError:
                    pass
    return borrados
