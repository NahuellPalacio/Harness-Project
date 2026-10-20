"""La fachada de Knowledge Access: `lookup` y `search` (docs/cambios/knowledge-api/spec.md, secciones 11 a 19; ADR-0017).

Es el unico punto publico del contexto: dos operaciones, en una interfaz Python interna, sin REST, sin CLI y sin
capability. Las dos devuelven un `knowledge-result/1.0` (§14), `OK` o `ERROR`, y no levantan por una falla
operacional ordinaria.

    lookup(proyecto, {"corpus", "document"})
                                 un documento por su id logico, exacto, sin recuperador (§12)
    search(proyecto, {"text", "scope"}, recuperador=None)
                                 tramos literales de los corpus pedidos, en el orden de un recuperador (§13);
                                 sin `recuperador`, `local-lexico/1`. El parametro es de la suite de
                                 conformidad (§19.4): ningun consumidor de producto lo pasa

El resultado es un contrato CERRADO (§14.5): sus claves y sus enums son exactamente los de §14, en todos los
niveles. No lleva `score`, ni el id de un chunk, ni hora, ni ruta absoluta, ni nada del recuperador.

    La fachada arma cada item de SU PROPIA lectura (§15.3): la cita `(corpus, document, anchor)` con el ancla
    que ella calcula, la revision (`contentHash` del texto normalizado del documento ENTERO), el localizador
    relativo, el tramo literal y la derivacion que declara el corpus. Un recuperador solo dice DONDE: `corpus`,
    `document` y `lines`. Lo que agregue (`text`, `score`, `_chunk_id`) se ignora.

    Sobre la lista de CUALQUIER recuperador hace cumplir el contrato (§19.3): un candidato invalido hace fallar la
    consulta con `RETRIEVAL_FAILED`; uno de un documento que el lector no pudo leer se descarta (el hueco ya esta
    anotado); un repetido se descarta, y el corte en 20 viene despues, sobre la lista entera. La fachada no
    reordena: el orden es el del recuperador.

    El respaldo en `local-lexico/1` es de SELECCION y ocurre antes de llamar a `buscar` (§27.4): una falla desde
    que se llamo a `buscar` termina `RETRIEVAL_FAILED`, con la identidad del que se llamo, y la consulta no se
    vuelve a correr con otro recuperador.

    Una excepcion que deriva de `Exception` y surge dentro de la consulta se captura y se convierte en un
    resultado (§11.1). Las senales de control del proceso (`KeyboardInterrupt`, `SystemExit` y todo lo que no
    deriva de `Exception`) NO se capturan: se propagan a quien llamo.

🔴 Seguridad (§21, §22): la consulta se valida ANTES de leer nada; las politicas (el catalogo de secretos y el
deny) se cargan antes de abrir un documento, y sin ellas es `POLICY_UNAVAILABLE`; el texto de la consulta se
redacta ANTES de llegar al recuperador, y el resultado entero se redacta antes de devolverlo: lo de confianza alta
se reemplaza, lo de media se declara. El error es `{code, reason, corpus, document}`, sin texto libre: ni un
mensaje, ni el texto de una excepcion, ni una ruta absoluta, ni contenido de un documento.

🔴 Sin estado (§26): no escribe, no imprime, no loguea y no guarda nada entre dos consultas. El contenido de un
documento es dato: nada de este modulo decide por lo que dice (§21.5).

Las costuras de la suite (el abridor, el `realpath` y los topes de lectura) son de `corpus.py` y no se exponen
aca: esta fachada no lleva un `limit` ni configuracion de producto.
"""
import re
import unicodedata

from . import corpus
from . import recuperador_local
import contexto.limpieza as limpieza

__all__ = ("lookup", "search")

CONTRATO = "knowledge-result/1.0"

# -- los topes de la fachada (§21.4) ---------------------------------------------------------
# Constantes de la implementacion: el contrato promete que existen y que pasarlos se declara, no los numeros.
# Los de la lectura (1 MiB, 2000 documentos, 64 MiB) son de `corpus.py`.

TOPE_ITEMS = 20
TOPE_LINEAS = 40
TOPE_CARACTERES = 4000

_LARGO_DOCUMENT = 200
_LARGO_TEXT = 500
_MAX_SCOPE = 4

_IDENTIDAD = re.compile(r"[a-z0-9-]+/[0-9]+")
_ENCABEZADO = re.compile(r"#{1,6}(?: |\Z)")
_CERCAS = ("```", "~~~")

# Los motivos que admite DOCUMENT_UNREADABLE (§18.1): una lista cerrada, y LIMIT_REACHED no es uno de ellos.
_MOTIVOS_DE_DOCUMENTO = ("UNREADABLE", "NOT_UTF8", "BINARY", "TOO_LARGE", "DUPLICATE_ID")


# -- la consulta (§11.2) ---------------------------------------------------------------------

def _con_control(texto):
    return any(unicodedata.category(c) == "Cc" for c in texto)


def _document_valido(document):
    """Un texto de 1 a 200 caracteres, sin caracteres de control, sin `\\`, sin `/` al comienzo ni al final, y
    sin tramos vacios, `.` ni `..`."""
    if not isinstance(document, str) or not 1 <= len(document) <= _LARGO_DOCUMENT:
        return False
    if "\\" in document or _con_control(document):
        return False
    return all(tramo not in ("", ".", "..") for tramo in document.split("/"))


def _text_valido(text):
    """Un texto de hasta 500 caracteres, no vacio sin los espacios de los costados, sin caracteres de control
    (U+0000 a U+001F y U+007F) y con al menos una letra o un digito."""
    if not isinstance(text, str) or len(text) > _LARGO_TEXT or not text.strip():
        return False
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in text):
        return False
    return any(c.isalpha() or c.isdigit() for c in text)


def _scope_valido(scope):
    """Una lista de 1 a 4 elementos distintos, cada uno del catalogo."""
    if not isinstance(scope, list) or not 1 <= len(scope) <= _MAX_SCOPE:
        return False
    if not all(isinstance(c, str) and c in corpus.CATALOGO for c in scope):
        return False
    return len(set(scope)) == len(scope)


def _lookup_valido(consulta):
    if not isinstance(consulta, dict) or set(consulta) != set(("corpus", "document")):
        return False
    corpus_id = consulta["corpus"]
    return isinstance(corpus_id, str) and corpus_id in corpus.CATALOGO and _document_valido(consulta["document"])


def _search_valido(consulta):
    if not isinstance(consulta, dict) or set(consulta) != set(("text", "scope")):
        return False
    return _text_valido(consulta["text"]) and _scope_valido(consulta["scope"])


# -- el resultado (§14) ----------------------------------------------------------------------

class _Consulta(object):
    """Lo que se sabe de la consulta mientras corre, para armar un resultado de error y para cerrar el
    resultado: el corpus y el documento de un `lookup` ya validado, la identidad del recuperador cuando se lo
    llamo, el catalogo de secretos cuando se cargo y los hallazgos de redactar el texto de la consulta."""
    __slots__ = ("corpus", "document", "retriever", "catalogo", "hallazgos")

    def __init__(self):
        self.corpus = None
        self.document = None
        self.retriever = None
        self.catalogo = None
        self.hallazgos = []


def _resultado(operacion, estado, retriever, items, gaps, truncated, error):
    """Un `knowledge-result/1.0` con exactamente las claves de §14.1. `complete` es verdadero si y solo si el
    estado es OK y no hay huecos."""
    return {
        "contract": CONTRATO,
        "operation": operacion,
        "status": estado,
        "retriever": retriever,
        "items": items,
        "gaps": gaps,
        "complete": estado == "OK" and not gaps,
        "truncated": truncated,
        "redactions": [],
        "error": error,
    }


def _error(operacion, codigo, reason=None, corpus_id=None, document=None, retriever=None):
    """Un resultado `ERROR` (§18): `{code, reason, corpus, document}` y nada mas. Sin items ni huecos."""
    return _resultado(operacion, "ERROR", retriever, [], [], False,
                      {"code": codigo, "reason": reason, "corpus": corpus_id, "document": document})


def _catalogo_de(consulta):
    """El catalogo de secretos de la consulta (§22.2, §22.3). `consulta.catalogo` se asigna cuando las politicas
    cargaron enteras. Si fallaron DESPUES de cargar el catalogo (un deny ilegible o no entendido, que levanta
    `PoliticaNoDisponible` despues de `limpieza.cargar_catalogo()`, o una falla imprevista de esa carga), sigue
    en None aunque haya catalogo: se lo pide de nuevo a `limpieza.cargar_catalogo()`, que lo devuelve de su
    cache, para que el error redacte lo que repite de la consulta. None si no hay catalogo: el unico caso en
    que un error sale sin redactar."""
    if consulta.catalogo is None:
        consulta.catalogo = limpieza.cargar_catalogo()
    return consulta.catalogo


def _cerrar(resultado, consulta):
    """El resultado, redactado entero con el catalogo de la consulta (§22.2), un `ERROR` incluido. `redactions`
    lleva los hallazgos de la consulta y despues los del resultado, con su lugar. Sin catalogo
    (`limpieza.cargar_catalogo()` devuelve None) no hay con que redactar (§22.3): el resultado sale como esta."""
    if consulta.catalogo is None:
        return resultado
    limpio, hallazgos = limpieza.redactar_arbol(resultado, consulta.catalogo)
    limpio["redactions"] = list(consulta.hallazgos) + list(hallazgos)
    return limpio


def _imprevisto(operacion, consulta):
    """El resultado de una falla operacional ordinaria que el contrato no clasifica (§11.1, §18.1):
    `RETRIEVAL_FAILED`, sin el texto de la excepcion. Nunca levanta."""
    try:
        _catalogo_de(consulta)
        return _cerrar(_error(operacion, "RETRIEVAL_FAILED", None, consulta.corpus, consulta.document,
                              consulta.retriever), consulta)
    except Exception:
        return _error(operacion, "RETRIEVAL_FAILED", None, None, None, consulta.retriever)


def _item(corpus_id, document, lectura, ancla, primera, ultima, texto, truncado):
    """Un item (§14.2), armado de la unica lectura del documento."""
    return {
        "citation": {"corpus": corpus_id, "document": document, "anchor": ancla},
        "revision": {"contentHash": lectura.huella},
        "locator": {"path": lectura.entrada.path, "lines": [primera, ultima]},
        "excerpt": {"text": texto, "truncated": truncado},
        "derivation": corpus.CATALOGO[corpus_id].derivacion,
    }


def _ancla_documento():
    return {"kind": "DOCUMENT", "heading": None, "occurrence": None}


# -- la procedencia: el ancla y el tramo (§15.2, §15.3) --------------------------------------

def _encabezados(lineas):
    """`[(numero de linea, texto del encabezado)]` de un Markdown, en orden (§20.2): una linea que empieza con
    uno a seis `#` seguidos de un espacio o del fin de linea, salvo adentro de un bloque de codigo (entre dos
    lineas que empiezan con ``` o con ~~~). El texto va sin los `#` del comienzo ni los espacios de los
    costados. Que es un encabezado lo define la primera implementacion; el ancla la calcula la fachada para
    cualquier recuperador."""
    salida = []
    en_codigo = False
    for numero, linea in enumerate(lineas, 1):
        if linea.startswith(_CERCAS):
            en_codigo = not en_codigo
        elif not en_codigo and _ENCABEZADO.match(linea):
            salida.append((numero, linea.lstrip("#").strip()))
    return salida


def _ancla(lectura, primera, cache):
    """El ancla de un tramo que empieza en la linea `primera` (§15.2). `DOCUMENT` para un JSON y para el texto
    anterior al primer encabezado de un Markdown. `SECTION` si no: el encabezado que gobierna la primera linea,
    y cuantas secciones del documento, contando esa, tienen el mismo texto."""
    ruta = lectura.entrada.path
    if ruta.endswith(".json"):
        return _ancla_documento()
    if ruta not in cache:
        cache[ruta] = _encabezados(lectura.lineas)
    hasta_aca = [texto for numero, texto in cache[ruta] if numero <= primera]
    if not hasta_aca:
        return _ancla_documento()
    return {"kind": "SECTION", "heading": hasta_aca[-1], "occurrence": hasta_aca.count(hasta_aca[-1])}


def _tramo(lineas, primera, ultima):
    """`(texto, ultima linea devuelta, truncado)` del tramo de un candidato `[primera, ultima]` (§15.3).

    Desde la primera linea, se toman lineas enteras mientras no pasen de 40 ni de 4000 caracteres en total; si la
    primera sola pasa de 4000, se toman sus primeros 4000 caracteres. Los 4000 se cuentan sobre el largo de las
    lineas, sin los `\\n` que las unen: es la cuenta con la que cuatro lineas de 1000 caracteres entran (KA-E22).
    `truncado` es verdadero si el candidato seguia despues de lo que se devolvio.
    """
    tomadas = []
    total = 0
    for numero in range(primera, ultima + 1):
        linea = lineas[numero - 1]
        if len(tomadas) >= TOPE_LINEAS or total + len(linea) > TOPE_CARACTERES:
            break
        tomadas.append(linea)
        total += len(linea)
    if not tomadas:
        return lineas[primera - 1][:TOPE_CARACTERES], primera, True
    hasta = primera + len(tomadas) - 1
    return "\n".join(tomadas), hasta, hasta < ultima


# -- lookup (§12) ----------------------------------------------------------------------------

def lookup(proyecto, consulta):
    """Un documento por su identidad logica `(corpus, document)`, exacto. No pasa por un recuperador.

    `consulta` es un dict con exactamente `corpus` y `document`. Devuelve un `knowledge-result/1.0`: `OK` con un
    item cuyo tramo es el documento entero (un `lookup` no recorta), o `ERROR` con el codigo de §18.
    """
    pedido = _Consulta()
    try:
        return _lookup(proyecto, consulta, pedido)
    except Exception:
        return _imprevisto("lookup", pedido)


def _lookup(proyecto, consulta, pedido):
    if not _lookup_valido(consulta):
        return _error("lookup", "QUERY_INVALID")
    corpus_id, document = consulta["corpus"], consulta["document"]
    pedido.corpus, pedido.document = corpus_id, document
    try:
        politicas = corpus.cargar_politicas(proyecto)
    except corpus.PoliticaNoDisponible:
        # Un deny ilegible o no entendido falla despues de cargar el catalogo: con catalogo, el error repite el
        # `document` redactado (§22.2); sin catalogo, tal cual (§22.3).
        _catalogo_de(pedido)
        return _cerrar(_error("lookup", "POLICY_UNAVAILABLE", None, corpus_id, document), pedido)
    pedido.catalogo = politicas.catalogo
    lector = corpus.Lector(proyecto, [corpus_id], politicas)
    estado, _ = lector.resolver_id(corpus_id, document)
    if estado == "CORPUS_UNAVAILABLE":
        error = _error("lookup", "CORPUS_UNAVAILABLE", None, corpus_id, document)
    elif estado == "NOT_FOUND":
        error = _error("lookup", "DOCUMENT_NOT_FOUND", None, corpus_id, document)
    elif estado == "DUPLICATE_ID":
        error = _error("lookup", "DOCUMENT_UNREADABLE", "DUPLICATE_ID", corpus_id, document)
    elif estado in ("DENIED", "OUTSIDE_ROOT"):
        error = _error("lookup", "ACCESS_DENIED", estado, corpus_id, document)
    elif estado == "OK":
        error = None
    else:
        raise RuntimeError("estado de documento que el contrato no clasifica")
    if error is not None:
        return _cerrar(error, pedido)
    lectura = lector.lectura(corpus_id, document)
    if lectura is None:
        motivo = lector.motivo(corpus_id, document)
        if motivo not in _MOTIVOS_DE_DOCUMENTO:
            motivo = "UNREADABLE"
        return _cerrar(_error("lookup", "DOCUMENT_UNREADABLE", motivo, corpus_id, document), pedido)
    total = len(lectura.lineas)
    item = _item(corpus_id, document, lectura, _ancla_documento(), 1 if total else 0, total, lectura.texto, False)
    return _cerrar(_resultado("lookup", "OK", None, [item], [], False, None), pedido)


# -- search (§13) ----------------------------------------------------------------------------

def search(proyecto, consulta, recuperador=None):
    """Tramos literales de los corpus pedidos, para un texto, en el orden de un recuperador.

    `consulta` es un dict con exactamente `text` y `scope`. Devuelve un `knowledge-result/1.0`: `OK` con hasta 20
    items (puede ser cero), los huecos de lo que no se pudo mirar y `complete`; o `ERROR` con el codigo de §18.
    Un `search` vacio no prueba ausencia (§13). `recuperador` es de la suite de conformidad (§19.4).
    """
    pedido = _Consulta()
    try:
        return _search(proyecto, consulta, recuperador, pedido)
    except Exception:
        return _imprevisto("search", pedido)


def _seleccionar(recuperador):
    """El recuperador que corre la consulta (§19.4, §27.4): el que pasa la suite de conformidad o, sin el,
    `local-lexico/1`, que existe siempre. Es la fase de SELECCION, antes de llamar a `buscar`: el respaldo en el
    local ocurre aca y nunca despues de una falla."""
    return recuperador if recuperador is not None else recuperador_local


def _entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar(candidatos, scope, lector):
    """Los candidatos validos y unicos, en el orden del recuperador, como `(corpus, document, primera, ultima,
    lectura)`; o None si alguno es invalido (§19.3).

    Un candidato que no es un dict, sin `corpus`, `document` o `lines` bien tipados, de un corpus fuera del
    `scope`, de un documento que la enumeracion no devolvio o que quedo excluido, o con lineas fuera de
    `1 <= primera <= ultima <= n`, hace fallar la consulta entera: un recuperador que propone algo fuera del
    contrato tiene un defecto y esconderlo es lo que no se quiere. Uno de un documento que el lector no pudo leer
    se descarta: el hueco ya esta anotado. Uno repetido (mismo corpus, documento y lineas) se descarta y queda el
    primero. Las claves de mas se ignoran.
    """
    en_scope = set(scope)
    elegibles = set(lector.documentos())
    vistos = set()
    validos = []
    for candidato in candidatos:
        if not isinstance(candidato, dict):
            return None
        corpus_id, document, lineas = candidato.get("corpus"), candidato.get("document"), candidato.get("lines")
        if not isinstance(corpus_id, str) or not isinstance(document, str):
            return None
        if not isinstance(lineas, list) or len(lineas) != 2 or not all(_entero(n) for n in lineas):
            return None
        if corpus_id not in en_scope or (corpus_id, document) not in elegibles:
            return None
        lectura = lector.lectura(corpus_id, document)
        if lectura is None:
            continue
        primera, ultima = lineas
        if not 1 <= primera <= ultima <= len(lectura.lineas):
            return None
        clave = (corpus_id, document, primera, ultima)
        if clave in vistos:
            continue
        vistos.add(clave)
        validos.append((corpus_id, document, primera, ultima, lectura))
    return validos


def _search(proyecto, consulta, recuperador, pedido):
    if not _search_valido(consulta):
        return _error("search", "QUERY_INVALID")
    texto, scope = consulta["text"], consulta["scope"]
    try:
        politicas = corpus.cargar_politicas(proyecto)
    except corpus.PoliticaNoDisponible:
        return _error("search", "POLICY_UNAVAILABLE")
    pedido.catalogo = politicas.catalogo
    lector = corpus.Lector(proyecto, sorted(scope), politicas)
    if len(lector.no_disponibles) == len(scope):
        return _cerrar(_error("search", "CORPUS_UNAVAILABLE"), pedido)
    redactado, pedido.hallazgos = limpieza.redactar(texto, politicas.catalogo, "la consulta")
    elegido = _seleccionar(recuperador)
    identidad = elegido.identidad
    if not isinstance(identidad, str) or not _IDENTIDAD.fullmatch(identidad):
        return _cerrar(_error("search", "RETRIEVAL_FAILED"), pedido)
    pedido.retriever = identidad
    # Desde aca se llamo al recuperador: cualquier falla es RETRIEVAL_FAILED con su identidad, y la consulta no
    # se vuelve a correr con otro (§27.4).
    # Al recuperador le llega la VISTA del lector (§19.2), no el lector: sin la `Entrada`, sin ruta y sin raiz. El
    # lector entero sigue siendo de la fachada: valida los candidatos y arma los items con el.
    candidatos = elegido.buscar(redactado, lector.vista())
    validos = _validar(candidatos, scope, lector) if isinstance(candidatos, list) else None
    if validos is None:
        return _cerrar(_error("search", "RETRIEVAL_FAILED", retriever=identidad), pedido)
    encabezados = {}
    items = []
    for corpus_id, document, primera, ultima, lectura in validos[:TOPE_ITEMS]:
        tramo, hasta, truncado = _tramo(lectura.lineas, primera, ultima)
        items.append(_item(corpus_id, document, lectura, _ancla(lectura, primera, encabezados),
                           primera, hasta, tramo, truncado))
    resultado = _resultado("search", "OK", identidad, items, lector.huecos(), len(validos) > TOPE_ITEMS, None)
    return _cerrar(resultado, pedido)
