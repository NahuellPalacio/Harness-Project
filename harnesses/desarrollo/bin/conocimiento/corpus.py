"""Que corpus hay, donde estan, que se puede abrir y como se lee un documento.

docs/cambios/knowledge-api/spec.md, secciones 8 a 10, 16.3, 19.2, 21 y 22 (ADR-0017). Es la politica de
lectura de Knowledge Access: la fachada (`acceso.py`) ve documentos por el lector de este modulo, el recuperador
por la vista de ese lector, y nada abre un archivo por otro camino.

La interfaz interna, que usa la fachada y que ningun consumidor ve:

    CATALOGO                     los cuatro corpus, en una tabla cerrada (§8.1)
    cargar_politicas(proyecto)   el catalogo de secretos y el deny efectivo del proyecto; levanta
                                 `PoliticaNoDisponible` si falta alguno o no se entiende (§22, falla
                                 cerrada: sin politicas no se abre ningun documento)
    Lector(proyecto, scope, politicas)
                                 el lector de una consulta (§19.2): resuelve la raiz de cada corpus del
                                 `scope`, enumera sus documentos y los lee una sola vez
        .no_disponibles          los corpus cuya raiz no sirve (§8.2), en el orden de §16.3
        .documentos()            [(corpus, document)] elegibles, en el orden de §16.3
        .texto(corpus, document) el texto normalizado, o None si no se pudo leer
        .lectura(corpus, document)  lo mismo con la revision y las lineas: `Lectura` o None
        .motivo(corpus, document)   por que no se pudo leer, o None
        .entrada(corpus, document)  la `Entrada` elegible (su ruta relativa es el localizador): es del lector y
                                 de la fachada, y un recuperador no la ve
        .formato(corpus, document)  "json" o "markdown" de un documento elegible, o None
        .resolver_id(corpus, document)
                                 (estado, entrada) de un id exacto: "OK", "NOT_FOUND", "DUPLICATE_ID",
                                 "DENIED", "OUTSIDE_ROOT" o "CORPUS_UNAVAILABLE" (§12 paso 5)
        .huecos()                [{"corpus", "path", "reason"}] ordenados por (corpus, path, reason)
        .vista()                 la `Vista` que la fachada le pasa a un recuperador (§19.2)
    Vista                        lo UNICO que un recuperador ve del lector: `documentos()`, `texto(corpus,
                                 document)` y `formato(corpus, document)`, de solo lectura; ni la `Entrada`, ni
                                 una ruta, ni la raiz, ni el lector
    ordenar_huecos(huecos)       el orden de §16.3 para los huecos
    decodificar(datos), huella(texto), lineas(texto)
                                 la normalizacion de §10.1, el `contentHash` y las lineas numeradas

Costuras de la suite (§35.2). Son atributos de este modulo y la suite los reemplaza: no son una API, ni
una configuracion de producto, y la consulta no lleva nada de esto (KC-28):

    abrir(ruta)                  abre el archivo en binario: es el unico lugar donde se abre un documento
    realpath(ruta)               la ruta real, para la contencion de carpetas y de archivos
    TOPE_DOCUMENTO               bytes por documento (1 MiB)
    TOPE_DOCUMENTOS              documentos leidos por consulta (2000)
    TOPE_BYTES                   bytes leidos por consulta (64 MiB)

🔴 Una sola lectura por documento y por consulta (KD-17): de esos bytes salen el texto normalizado, la
revision y las lineas, y no hay una segunda apertura que pueda ver otro contenido (KA-I04). No hay cache
entre consultas: el lector se arma por consulta y se descarta.

🔴 Un id nunca se vuelve ruta (KD-20): `resolver_id` compara el pedido contra los ids de lo enumerado, y
la enumeracion no devuelve un nombre con `..`, un stream NTFS ni un nombre que Windows reinterpreta.

🔴 Este modulo no importa `ejecucion.registro`: la contencion de MD-16 se escribe aca (KC-42). No lanza
procesos, no escribe, no imprime y no usa `logging`.
"""
import hashlib
import io
import json
import os
import re
import stat
import sys
import unicodedata

_BIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BIN not in sys.path:
    sys.path.insert(0, _BIN)

import rutas                                               # noqa: E402
import contexto.limpieza as limpieza                       # noqa: E402

# -- los topes (§21.4) -----------------------------------------------------------------------
# Constantes de la implementacion: el contrato promete que existen y que pasarlos se declara, no los
# numeros. Ninguno es de tiempo de reloj. Los de la fachada (20 items, 40 lineas, 4000 caracteres) son de
# `acceso.py`.

TOPE_DOCUMENTO = 1 << 20
TOPE_DOCUMENTOS = 2000
TOPE_BYTES = 64 << 20


# -- las costuras de la suite ----------------------------------------------------------------

def abrir(ruta):
    """El archivo abierto en binario. Reemplazable por la suite (KA-E28, KA-E45)."""
    return io.open(ruta, "rb")


realpath = os.path.realpath


# -- el catalogo (§8.1, KD-04, KD-18) --------------------------------------------------------

class _Definicion(object):
    """Un corpus: id, raiz por defecto, la clave de la configuracion que la mueve (o None), si
    desciende a las subcarpetas, y la derivacion, que declara el corpus y nunca el contenido."""
    __slots__ = ("id", "raiz", "clave", "profundo", "derivacion")

    def __init__(self, id_, raiz, clave, profundo, derivacion):
        self.id = id_
        self.raiz = raiz
        self.clave = clave
        self.profundo = profundo
        self.derivacion = derivacion


CATALOGO = dict((d.id, d) for d in (
    _Definicion("adr", "docs/adr", None, False, "PRIMARY"),
    _Definicion("dominio", "docs/dominio", None, False, "PRIMARY"),
    _Definicion("codebase", "docs/codebase", "rutaCodebase", False, "GENERATED"),
    _Definicion("memoria", "docs/conocimiento", "rutaMemoria", True, "GENERATED"),
))

_ADR = re.compile(r"[0-9]{4}-.*\.md")
_ESQUEMA = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_BOM = b"\xef\xbb\xbf"


def id_de_documento(corpus, partes):
    """El id logico de un archivo del corpus, o None si no sigue su regla (§8.1).

    `partes` son los nombres del archivo, relativos a la raiz del corpus. Un archivo que no sigue la
    regla no es un documento: no existe para Knowledge Access y no es un hueco.
    """
    nombre = partes[-1]
    if corpus == "memoria":
        if len(nombre) > 3 and nombre.endswith(".md"):
            return "/".join(partes)[:-3]
        return None
    if len(partes) != 1:
        return None
    if corpus == "adr":
        return "ADR-" + nombre[:4] if _ADR.fullmatch(nombre) else None
    if corpus == "codebase" and nombre == "project-context.json":
        return "project-context"
    if corpus in ("dominio", "codebase"):
        return nombre[:-3] if len(nombre) > 3 and nombre.endswith(".md") else None
    return None


# -- la configuracion y la raiz (§8.1, §8.2) -------------------------------------------------

def comparable(ruta):
    """Como se comparan dos rutas: sin distinguir mayusculas en Windows y en macOS."""
    return ruta.casefold() if sys.platform in ("win32", "darwin") else ruta


def adentro(raiz, ruta):
    """`ruta` queda ESTRICTAMENTE adentro de `raiz`: commonpath de los dos con normcase igual a la raiz, y
    distinta de ella. Dos unidades distintas son afuera. Un prefijo de texto no alcanza (§21.2)."""
    raiz, ruta = os.path.normcase(raiz), os.path.normcase(ruta)
    try:
        comun = os.path.commonpath([raiz, ruta])
    except ValueError:
        return False
    return comun == raiz and ruta != raiz


def _config_de(proyecto):
    """`<proyecto>/.claude/harness.config.json` como un dict, o {}: la lee como `dev-harness.py` (§8.1).
    Si no existe, no es JSON o no es un objeto, no hay configuracion. «No es JSON» incluye un contenido que el
    interprete no puede leer por su anidacion (`RecursionError`): tampoco hay configuracion y vale el defecto."""
    ruta = os.path.join(proyecto, ".claude", "harness.config.json")
    if not os.path.isfile(ruta):
        return {}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError, RecursionError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _segmentos(valor):
    """Los tramos de una raiz configurada, o None si no es una ruta relativa valida (§8.2): absoluta, con
    unidad o esquema, con `~`, con un tramo vacio, `.` o `..`, o con un caracter de control. `\\` se
    acepta como separador y se convierte a `/`."""
    ruta = valor.replace("\\", "/")
    if any(unicodedata.category(c) == "Cc" for c in ruta):
        return None
    if ruta.startswith("/") or ruta.startswith("~") or _ESQUEMA.match(ruta):
        return None
    tramos = tuple(ruta.split("/"))
    if any(t in ("", ".", "..") for t in tramos):
        return None
    return tramos


class Raiz(object):
    """La raiz de un corpus disponible: sus tramos relativos al proyecto, su ruta y su `realpath`."""
    __slots__ = ("segmentos", "ruta", "real")

    def __init__(self, segmentos, ruta, real):
        self.segmentos = segmentos
        self.ruta = ruta
        self.real = real


def resolver_raiz(proyecto, corpus):
    """La `Raiz` del corpus, o None si no esta disponible (§8.2): la configurada no es una ruta relativa
    valida, su `realpath` no queda estrictamente adentro del `realpath` del proyecto, o no existe o no es
    un directorio. No hay caida a otra ruta: una `rutaCodebase` invalida no vuelve al defecto."""
    definicion = CATALOGO[corpus]
    valor = definicion.raiz
    if definicion.clave is not None:
        configurado = _config_de(proyecto).get(definicion.clave)
        if isinstance(configurado, str) and configurado.strip():
            valor = configurado
    segmentos = _segmentos(valor)
    if segmentos is None:
        return None
    ruta = os.path.join(proyecto, *segmentos)
    real = realpath(ruta)
    if not adentro(realpath(proyecto), real):
        return None
    if not os.path.isdir(ruta):
        return None
    return Raiz(segmentos, ruta, real)


# -- las politicas: el catalogo de secretos y el deny (§22) ----------------------------------

class PoliticaNoDisponible(Exception):
    """Falta el catalogo de secretos, o el deny no se puede leer o trae una sintaxis que no se entiende.
    La fachada la convierte en POLICY_UNAVAILABLE antes de abrir ningun documento (§22.3)."""


_READ = re.compile(r"Read\((.*)\)", re.DOTALL)


def _patron(texto):
    """El patron de un `Read(<patron>)` como regex (§22.1). `./` al comienzo ancla a la raiz del proyecto;
    sin `./` vale a cualquier profundidad; `**` es cualquier cantidad de carpetas, cero incluido; `*` es
    cualquier texto adentro de un tramo; todo lo demas es literal. `? [ ] { }`: falla cerrada."""
    if any(c in texto for c in "?[]{}"):
        raise PoliticaNoDisponible("el deny trae una sintaxis que no se entiende")
    texto = comparable(texto)
    anclado = texto.startswith("./")
    if anclado:
        texto = texto[2:]
    tramos = texto.split("/")
    partes = []
    for i, tramo in enumerate(tramos):
        ultimo = i == len(tramos) - 1
        if tramo == "**":
            partes.append(".+" if ultimo else "(?:[^/]+/)*")
        else:
            partes.append(re.escape(tramo).replace(r"\*", "[^/]*") + ("" if ultimo else "/"))
    return re.compile(("" if anclado else "(?:.*/)?") + "".join(partes))


class Politicas(object):
    """El catalogo de secretos y el deny efectivo, cargados antes de abrir nada."""
    __slots__ = ("catalogo", "_deny")

    def __init__(self, catalogo, deny):
        self.catalogo = catalogo
        self._deny = deny

    def deniega(self, ruta):
        """`ruta` es relativa al proyecto, POSIX: coincide con alguna entrada `Read(...)` del deny."""
        ruta = comparable(ruta)
        return any(p.fullmatch(ruta) for p in self._deny)


def _cargar_deny(proyecto):
    """`permissions.deny` de `<proyecto>/.claude/settings.json` si existe, y si no el de la fabrica,
    `comun/settings/permissions.deny.json`, por `rutas.localizar` (§22.1). Si existe `settings.json` y no
    sirve, no se cae al de la fabrica: es POLICY_UNAVAILABLE. Un contenido que el interprete no puede leer por
    su anidacion (`RecursionError`) es «no es JSON»: tambien es POLICY_UNAVAILABLE, antes de abrir nada."""
    del_proyecto = os.path.join(proyecto, ".claude", "settings.json")
    if os.path.exists(del_proyecto):
        ruta = del_proyecto
    else:
        ruta = rutas.localizar(("settings", "permissions.deny.json"), __file__)
        if ruta is None:
            raise PoliticaNoDisponible("no hay un deny que leer")
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError, RecursionError):
        raise PoliticaNoDisponible("el deny no se puede leer")
    permisos = doc.get("permissions") if isinstance(doc, dict) else None
    lista = permisos.get("deny") if isinstance(permisos, dict) else None
    if not isinstance(lista, list) or not all(isinstance(x, str) for x in lista):
        raise PoliticaNoDisponible("permissions.deny no es una lista de textos")
    patrones = []
    for entrada in lista:
        m = _READ.fullmatch(entrada)
        if m:
            patrones.append(_patron(m.group(1)))
    return patrones


def cargar_politicas(proyecto):
    """Las `Politicas` de la consulta, o levanta `PoliticaNoDisponible`. Sin catalogo de secretos
    (`limpieza.cargar_catalogo()` devuelve None) o sin un deny legible y entendido no se lee nada: es la
    falla cerrada de §22.3, el precedente del motor («sin catalogo, falla cerrado»)."""
    catalogo = limpieza.cargar_catalogo()
    if catalogo is None:
        raise PoliticaNoDisponible("no hay catalogo de secretos")
    return Politicas(catalogo, _cargar_deny(proyecto))


# -- la enumeracion y la contencion (§21.2) --------------------------------------------------

class Entrada(object):
    """Un archivo del corpus que la enumeracion vio, o una carpeta que no se pudo recorrer.

    `document` es el id logico (None para una carpeta). `path` es el localizador: relativo al proyecto,
    POSIX. `estado` es None si es elegible, o `DENIED`, `OUTSIDE_ROOT`, `DUPLICATE_ID` o `UNREADABLE`
    (una subcarpeta que el sistema no dejo listar): lo no elegible es un hueco y no se abre.
    """
    __slots__ = ("corpus", "document", "path", "ruta", "estado")

    def __init__(self, corpus, document, path, ruta, estado):
        self.corpus = corpus
        self.document = document
        self.path = path
        self.ruta = ruta
        self.estado = estado


def _reinterpretado(nombre):
    """Un nombre con un caracter de control, o que termina en punto o en espacio, no se considera: en
    Windows, abrir `notas./x.md` por una ruta comun abre `notas/x.md`, que es otro archivo (§21.2)."""
    return nombre.endswith((".", " ")) or any(unicodedata.category(c) == "Cc" for c in nombre)


def _unir(tramos):
    return "/".join(tramos)


def _recorrer(corpus, raiz, politicas, directorio, partes, pila, entradas):
    """Una carpeta del corpus, con sus entradas ordenadas por nombre, por punto de codigo; en `memoria`
    desciende en profundidad, con el mismo orden en cada nivel (§16.3).

    Una carpeta cuyo `realpath` no queda adentro de la raiz es OUTSIDE_ROOT y no se desciende: la politica
    no depende de como trate `os.walk` un junction (§21.2). Una carpeta que lleva de vuelta a una de las
    que se estan recorriendo (un ciclo) tampoco se desciende, y se declara igual: no hay un motivo mas
    propio en la lista cerrada, y lo no mirado nunca se pierde.
    """
    try:
        nombres = sorted(os.listdir(directorio))
    except OSError:
        if not partes:
            raise
        entradas.append(Entrada(corpus, None, _unir(raiz.segmentos + partes), directorio, "UNREADABLE"))
        return
    profundo = CATALOGO[corpus].profundo
    for nombre in nombres:
        if _reinterpretado(nombre):
            continue
        ruta = os.path.join(directorio, nombre)
        hijos = partes + (nombre,)
        path = _unir(raiz.segmentos + hijos)
        if os.path.isdir(ruta):
            if not profundo:
                continue
            real = realpath(ruta)
            if not adentro(raiz.real, real) or os.path.normcase(real) in pila:
                entradas.append(Entrada(corpus, None, path, ruta, "OUTSIDE_ROOT"))
                continue
            _recorrer(corpus, raiz, politicas, ruta, hijos, pila + (os.path.normcase(real),), entradas)
            continue
        document = id_de_documento(corpus, hijos)
        if document is None:
            continue
        if politicas.deniega(path):
            estado = "DENIED"
        elif not adentro(raiz.real, realpath(ruta)):
            estado = "OUTSIDE_ROOT"
        else:
            estado = None
        entradas.append(Entrada(corpus, document, path, ruta, estado))


def enumerar(corpus, raiz, politicas):
    """Las `Entrada` del corpus, en el orden de §16.3, con los ids repetidos marcados `DUPLICATE_ID`.

    Un id que no es unico no se resuelve (§9): se cuenta entre todos los archivos que siguen la regla del
    corpus, tambien los excluidos, y cada archivo elegible que lo comparte queda `DUPLICATE_ID`. Un
    archivo excluido conserva su motivo.
    """
    entradas = []
    _recorrer(corpus, raiz, politicas, raiz.ruta, (), (os.path.normcase(raiz.real),), entradas)
    cuentas = {}
    for e in entradas:
        if e.document is not None:
            cuentas[e.document] = cuentas.get(e.document, 0) + 1
    for e in entradas:
        if e.document is not None and e.estado is None and cuentas[e.document] > 1:
            e.estado = "DUPLICATE_ID"
    return entradas


# -- la lectura y la revision (§10.1) --------------------------------------------------------

def decodificar(datos):
    """(texto normalizado, None) o (None, motivo) de los bytes de un documento (§10.1, pasos 3 a 5).

    Un byte 0x00 es BINARY. Un BOM UTF-8 al comienzo se quita, y el resto se decodifica como UTF-8
    ESTRICTO: si falla, NOT_UTF8 (nunca se reemplazan bytes). Despues `\\r\\n` y `\\r` suelto pasan a `\\n`.
    """
    if b"\x00" in datos:
        return None, "BINARY"
    if datos.startswith(_BOM):
        datos = datos[len(_BOM):]
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError:
        return None, "NOT_UTF8"
    return texto.replace("\r\n", "\n").replace("\r", "\n"), None


def huella(texto):
    """`revision.contentHash`: `sha256:` del texto normalizado, codificado en UTF-8 (§10.1, paso 6)."""
    return "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()


def lineas(texto):
    """Las lineas del texto normalizado, numeradas desde 1 por quien las use. Un `\\n` final no agrega
    una linea vacia, y un documento vacio tiene cero lineas (§10.1, paso 7)."""
    if not texto:
        return []
    partes = texto.split("\n")
    if texto.endswith("\n"):
        partes.pop()
    return partes


def _tamano(ruta):
    """(tamano, None) o (None, motivo): `stat` antes de abrir. Mas de 1 MiB es TOO_LARGE sin abrir, y lo
    que no es un archivo regular (una carpeta, un FIFO) no se abre."""
    try:
        st = os.stat(ruta)
    except OSError:
        return None, "UNREADABLE"
    if not stat.S_ISREG(st.st_mode):
        return None, "UNREADABLE"
    if st.st_size > TOPE_DOCUMENTO:
        return None, "TOO_LARGE"
    return st.st_size, None


def _leer_bytes(ruta):
    """(datos, motivo): una sola apertura, que lee como mucho 1 MiB mas un byte y cierra. Si leyo mas de
    1 MiB, el motivo es TOO_LARGE; si el sistema no dejo abrir o leer, (None, UNREADABLE)."""
    try:
        f = abrir(ruta)
        try:
            datos = f.read(TOPE_DOCUMENTO + 1)
        finally:
            f.close()
    except OSError:
        return None, "UNREADABLE"
    if len(datos) > TOPE_DOCUMENTO:
        return datos, "TOO_LARGE"
    return datos, None


class Lectura(object):
    """Lo que sale de la unica lectura de un documento: el texto normalizado, su revision y sus lineas."""
    __slots__ = ("entrada", "texto", "huella", "lineas")

    def __init__(self, entrada, texto):
        self.entrada = entrada
        self.texto = texto
        self.huella = huella(texto)
        self.lineas = lineas(texto)


def ordenar_huecos(huecos):
    """Los huecos por `(corpus, path, reason)`, por punto de codigo, con `path` None como texto vacio. No
    se usa `casefold` para ordenar (§16.3)."""
    return sorted(huecos, key=lambda h: (h["corpus"], h["path"] or "", h["reason"]))


# -- lo que un recuperador ve del lector (§19.2) ---------------------------------------------

class Vista(object):
    """Lo UNICO que un recuperador ve del lector de una consulta: tres metodos, de solo lectura.

        documentos()               [(corpus, document)] elegibles, en el orden de §16.3 (una lista nueva cada vez)
        texto(corpus, document)    el texto normalizado, o None si no se pudo leer
        formato(corpus, document)  "json" o "markdown" de un documento elegible, o None

    No es el `Lector`: no da la `Entrada`, ni la `Lectura`, ni el proyecto, ni las raices, ni las politicas, ni una
    ruta, y no se puede reasignar ni borrar nada de ella. Guarda tres funciones en atributos privados y nada mas.
    Python no impide la reflexion, y no se pide: se pide que no haya ningun camino PUBLICO a lo del lector.
    """
    __slots__ = ("_documentos", "_texto", "_formato")

    def __init__(self, documentos, texto, formato):
        object.__setattr__(self, "_documentos", documentos)
        object.__setattr__(self, "_texto", texto)
        object.__setattr__(self, "_formato", formato)

    def __setattr__(self, nombre, valor):
        raise AttributeError("la vista del lector es de solo lectura")

    def __delattr__(self, nombre):
        raise AttributeError("la vista del lector es de solo lectura")

    def documentos(self):
        return self._documentos()

    def texto(self, corpus, document):
        return self._texto(corpus, document)

    def formato(self, corpus, document):
        return self._formato(corpus, document)


# -- el lector de una consulta (§19.2) -------------------------------------------------------

class Lector(object):
    """El unico objeto por el que se ven documentos. Lo arma la fachada para cada consulta y se descarta
    al terminar.

    Resuelve y enumera cada corpus del `scope` al construirse, en el orden de §16.3. Lo excluido (deny,
    fuera de la raiz, id repetido) no es elegible y ya es un hueco. Cada documento se lee UNA vez: la
    segunda llamada devuelve lo mismo sin abrir el archivo. Los topes de la consulta (§21.4): pasado uno,
    todo lo que sigue devuelve None y se anota un hueco LIMIT_REACHED por corpus afectado, con `path`
    None. El conteo de documentos incluye los que no se pudieron leer; el de bytes se mira antes de
    abrir, con el tamano de `stat`, y lo que se lee suma lo realmente leido.
    """

    def __init__(self, proyecto, scope, politicas):
        self.proyecto = proyecto
        self.politicas = politicas
        self.no_disponibles = []
        self._entradas = {}
        self._elegibles = {}
        self._orden = []
        self._de_enumeracion = []
        self._de_lectura = []
        self._lecturas = {}
        self._fallas = {}
        self._con_tope = set()
        self._leidos = 0
        self._bytes = 0
        self._agotado = False
        for corpus in sorted(set(scope)):
            raiz = resolver_raiz(proyecto, corpus)
            entradas = None
            if raiz is not None:
                try:
                    entradas = enumerar(corpus, raiz, politicas)
                except OSError:
                    entradas = None
            if entradas is None:
                self.no_disponibles.append(corpus)
                self._de_enumeracion.append({"corpus": corpus, "path": None,
                                             "reason": "CORPUS_UNAVAILABLE"})
                continue
            self._entradas[corpus] = entradas
            for e in entradas:
                if e.estado is None:
                    self._elegibles[(corpus, e.document)] = e
                    self._orden.append((corpus, e.document))
                else:
                    self._de_enumeracion.append({"corpus": corpus, "path": e.path, "reason": e.estado})

    def documentos(self):
        """Los `(corpus, document)` elegibles del `scope`, en el orden de §16.3."""
        return list(self._orden)

    def entrada(self, corpus, document):
        """La `Entrada` elegible de un documento, o None. Es del lector y de la fachada: un recuperador no la ve
        (recibe la `Vista`, §19.2)."""
        return self._elegibles.get((corpus, document))

    def formato(self, corpus, document):
        """`"json"` o `"markdown"`: el formato de un documento elegible, o None. Es JSON el archivo que se
        enumero con extension `.json` (§8.1: hoy, solo `project-context.json` de `codebase`), y Markdown todo lo
        demas del corpus. El recuperador lo pide por la `Vista` y no necesita la ruta."""
        entrada = self._elegibles.get((corpus, document))
        if entrada is None:
            return None
        return "json" if entrada.path.endswith(".json") else "markdown"

    def vista(self):
        """La `Vista` que la fachada le pasa a un recuperador en vez del lector (§19.2). Sus tres metodos van al
        lector, que lee cada documento una sola vez por consulta."""
        return Vista(self.documentos, self.texto, self.formato)

    def resolver_id(self, corpus, document):
        """El triage exacto de un `lookup` (§12, paso 5): `(estado, entrada)`.

        El id se compara por igualdad exacta (mayusculas incluidas) contra los ids de lo enumerado, nunca
        se convierte en una ruta. Estados: `CORPUS_UNAVAILABLE` (la raiz no sirve), `NOT_FOUND` (ninguno),
        `DUPLICATE_ID` (mas de uno: no se resuelve), `DENIED` u `OUTSIDE_ROOT` (uno excluido) y `OK`.
        """
        if corpus in self.no_disponibles:
            return "CORPUS_UNAVAILABLE", None
        coincidencias = [e for e in self._entradas[corpus] if e.document == document]
        if not coincidencias:
            return "NOT_FOUND", None
        if len(coincidencias) > 1:
            return "DUPLICATE_ID", None
        e = coincidencias[0]
        return (e.estado or "OK"), e

    def _anotar(self, corpus, document, entrada, motivo):
        self._fallas[(corpus, document)] = motivo
        if motivo == "LIMIT_REACHED":
            if corpus not in self._con_tope:
                self._con_tope.add(corpus)
                self._de_lectura.append({"corpus": corpus, "path": None, "reason": motivo})
        else:
            self._de_lectura.append({"corpus": corpus, "path": entrada.path, "reason": motivo})

    def lectura(self, corpus, document):
        """La `Lectura` de un documento elegible (una sola apertura por consulta), o None. Si no se puede,
        el motivo queda en `motivo()` y el hueco anotado."""
        clave = (corpus, document)
        if clave in self._lecturas:
            return self._lecturas[clave]
        entrada = self._elegibles.get(clave)
        if entrada is None or clave in self._fallas:
            return None
        if self._agotado or self._leidos >= TOPE_DOCUMENTOS:
            self._agotado = True
            self._anotar(corpus, document, entrada, "LIMIT_REACHED")
            return None
        self._leidos += 1
        tamano, motivo = _tamano(entrada.ruta)
        if motivo is None and self._bytes + tamano > TOPE_BYTES:
            self._agotado = True
            motivo = "LIMIT_REACHED"
        texto = None
        if motivo is None:
            datos, motivo = _leer_bytes(entrada.ruta)
            if datos is not None:
                self._bytes += len(datos)
            if motivo is None:
                texto, motivo = decodificar(datos)
        if motivo is not None:
            self._anotar(corpus, document, entrada, motivo)
            return None
        self._lecturas[clave] = Lectura(entrada, texto)
        return self._lecturas[clave]

    def texto(self, corpus, document):
        """El texto normalizado de un documento elegible, o None si no se pudo leer (§19.2)."""
        leida = self.lectura(corpus, document)
        return leida.texto if leida is not None else None

    def motivo(self, corpus, document):
        """Por que un documento no se pudo leer (UNREADABLE, NOT_UTF8, BINARY, TOO_LARGE o LIMIT_REACHED),
        o None."""
        return self._fallas.get((corpus, document))

    def huecos(self):
        """Los huecos hasta ahora: lo no disponible y lo excluido de la enumeracion, y lo que no se pudo
        leer, ordenados por `(corpus, path, reason)` (§16.3)."""
        return ordenar_huecos([dict(h) for h in self._de_enumeracion + self._de_lectura])
