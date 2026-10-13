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

docs/cambios/minimal-execution-engine/spec.md, secciones 12 a 14.

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

REQUEST = "request.json"
CANCELACION = "cancelacion.json"
ENTREGA = "entrega.json"
PROCESO = "proceso.json"
OUTPUT = "output.md"
RESULT = "result.json"
VIVO = "vivo.lock"

# Los ids que se vuelven carpetas se validan con fullmatch, nunca con `$`: un `\n` final no pasa
# (MD-15, ME-14).
ID = re.compile(r"exe_[0-9a-f]{32}")
CLAVE_DE_TAREA = re.compile(r"[A-Za-z][A-Za-z0-9_]*-[0-9]+")
HEX = re.compile(r"[0-9a-f]{64}")
TURNO = re.compile(r"[0-9]{6}\.json")
TEMPORAL = re.compile(r"\..+\.tmp")

# Un residuo previo a la publicacion se barre recien con el candado libre y mas de diez minutos.
UMBRAL_DE_RESIDUO = 600

REQUESTED, RUNNING = "REQUESTED", "RUNNING"
ILEGIBLE = "ILEGIBLE"
ABIERTOS = (REQUESTED, RUNNING)


class RegistroInvalido(Exception):
    """Un id que no se puede usar como ruta, o un registro que no se puede escribir."""


def ahora():
    """UTC, con el formato del contrato."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def nuevo_id():
    """`exe_` y 128 bits del generador criptografico del sistema (MD-15)."""
    return "exe_" + secrets.token_hex(16)


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
    segundos. El candado decide, y la edad es la guarda. Devuelve los que borro."""
    borrados = []
    for execution_id in residuos(proyecto, clave):
        carpeta = carpeta_de(proyecto, clave, execution_id)
        if candado_libre(carpeta) is False or _edad(carpeta) <= umbral:
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


def limpiar_temporales(proyecto, clave, umbral=UMBRAL_DE_RESIDUO):
    """Los temporales de escritura de toda carpeta con el candado libre, y los de los turnos con
    mas de `umbral` segundos: una escritura dura milisegundos. Devuelve cuantos borro."""
    borrados = 0
    for execution_id in carpetas(proyecto, clave):
        carpeta = carpeta_de(proyecto, clave, execution_id)
        if candado_libre(carpeta) is False:
            continue
        for ruta in _temporales(carpeta):
            try:
                os.unlink(ruta)
                borrados += 1
            except OSError:
                pass
    for hexa in claves_de(proyecto, clave):
        for ruta in _temporales(carpeta_de_clave(proyecto, clave, "sha256:" + hexa)):
            try:
                if time.time() - os.stat(ruta).st_mtime > umbral:
                    os.unlink(ruta)
                    borrados += 1
            except OSError:
                pass
    return borrados
