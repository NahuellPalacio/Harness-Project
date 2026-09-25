"""El registro de fuentes: de que documento sale lo que el harness afirma.

Es la unica autoridad sobre la IDENTIDAD de una fuente -id, tipo, version, hash del original
y extracto activo-. Antes de este modulo la unica version escrita en el arbol era la que
`gcba-it-normative-baseline.json` declaraba a mano, y los 42 controles declaraban la suya en
`normativeSources[]` sin nada contra que compararla.

🔴 **Una entrada por fuente.** No hay `ES0901@6.2` conviviendo con `ES0901@6.3`: el registro
dice que hay hoy, y el historial es git. Un registro con historial es un archivo que crece para
siempre y que obliga a elegir cual de las tres filas es la que vale.

🔴 **El hash es el del archivo ORIGINAL.** Nunca el del markdown del extracto: el extracto se
reescribe cuando alguien lo mejora, sin que la fuente cambie, y no cambia cuando el PDF se
reemplaza por otro con el mismo nombre. Mide exactamente lo contrario de lo que hace falta.

🔴 **Lo que no consta entra `null`.** Sin los PDF originales en la maquina no hay hash, y
entonces la integridad de esa fuente no se puede verificar. Eso se dice; no se rellena.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO = "source-registry.json"
SCHEMA = "source-registry.schema.json"
VERSION_SCHEMA = "source-registry/1.1"

TIPOS = ("norma", "proceso", "tecnologia")

GESTIONADA = "CURRENT"
RETIRADA = "RETIRED"
ESTADOS = (GESTIONADA, RETIRADA)

# El diagnostico de una entrada. `OK` no significa que la fuente este al dia -eso lo resuelve
# `frescura.py`-: significa que la entrada es coherente con el arbol.
OK = "OK"
DUPLICADA = "DUPLICATE_SOURCE_ID"
SIN_EXTRACTO = "SOURCE_EXTRACT_MISSING"
SIN_HASH = "SOURCE_HASH_UNKNOWN"


class RegistroInvalido(Exception):
    """El registro no se lee a medias. Media identidad es peor que ninguna."""


def vacio():
    return {"schema_version": VERSION_SCHEMA, "sources": []}


# -- carga ---------------------------------------------------------------------

def cargar(desde=None):
    """El registro como dato. Vacio si no esta: un harness sin fuentes gestionadas es valido."""
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return vacio()
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            documento = json.load(f)
    except (OSError, ValueError) as e:
        raise RegistroInvalido("%s no se pudo leer: %s" % (ruta, e))
    _sin_repetidas(documento, ruta)
    return documento


def _sin_repetidas(documento, ruta=""):
    """Levanta si una fuente esta declarada dos veces.

    🔴 Acá y no en el diagnostico. Un id repetido no es una entrada torcida que se pueda
    reportar y seguir: `buscar` devolveria la primera y nadie sabria que hay otra, que es
    exactamente el «dos lugares que el dia que difieran van a tener razon los dos» que este
    registro existe para que no pase. Se falla cerrado y se dice cual.
    """
    ids = [f.get("id") for f in (documento or {}).get("sources") or [] if isinstance(f, dict)]
    repetidas = sorted({i for i in ids if i and ids.count(i) > 1})
    if repetidas:
        raise RegistroInvalido(
            "%s declara dos veces %s: el registro lleva una entrada por fuente, no una por "
            "version. El historial es git." % (ruta or ARCHIVO, ", ".join(repetidas)))


def validar_schema(doc, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise RegistroInvalido("no esta contexto-armar.py, de donde sale el validador.")
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise RegistroInvalido("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


# -- lectura -------------------------------------------------------------------

def fuentes(doc=None, desde=None):
    documento = doc if doc is not None else cargar(desde)
    return list(documento.get("sources") or [])


def gestionadas(doc=None, desde=None):
    """Las que se siguen. Una `RETIRED` no se descubre, no se resuelve y no bloquea."""
    return [f for f in fuentes(doc, desde) if f.get("status") == GESTIONADA]


def buscar(sid, doc=None, desde=None):
    for f in fuentes(doc, desde):
        if f.get("id") == sid:
            return f
    return None


def version_de(sid, doc=None, desde=None):
    """La version aceptada de una fuente, o None.

    🔴 Esta es la puerta por la que la linea base de O1 dejo de declarar la suya. Dos lugares
    que dicen que version de ES0901 tiene el harness son dos lugares que el dia que difieran
    van a tener razon los dos.
    """
    entrada = buscar(sid, doc, desde)
    return (entrada or {}).get("version")


def ruta_de_extracto(entrada, desde=None):
    """Donde esta el conocimiento activo de esta fuente, o None si no esta en este arbol.

    `normativa/` es de la fabrica y no se instala en un proyecto -lo dice su LEEME-, asi que
    fuera del repositorio esto devuelve None y la fuente no puede decir que esta al dia. Es
    incomodo y es cierto.
    """
    relativa = (entrada or {}).get("extract") or ""
    if not relativa:
        return None
    return rutas.localizar(tuple(relativa.split("/")), desde or __file__)


# -- diagnostico ---------------------------------------------------------------

def validar(doc=None, desde=None):
    """{id: estado} de cada fuente declarada, mas los errores de schema.

    El estado es del REGISTRO contra el arbol, no de la fuente contra su original: si el
    extracto que la entrada declara existe, si el id esta repetido, si hay hash aceptado.
    """
    documento = doc if doc is not None else cargar(desde)
    errores = list(validar_schema(documento, desde))
    estados = {}
    vistos = set()
    for f in documento.get("sources") or []:
        sid = f.get("id", "")
        if sid in vistos:
            estados[sid] = DUPLICADA
            continue
        vistos.add(sid)
        if ruta_de_extracto(f, desde) is None:
            estados[sid] = SIN_EXTRACTO
            continue
        if not f.get("sha256"):
            estados[sid] = SIN_HASH
            continue
        estados[sid] = OK
    return {"schemaErrors": errores, "sources": estados}


def hallazgos(doc=None, desde=None):
    """Lo que hay que decirle a una persona, en texto. Vacio es que no hay nada que decir."""
    documento = doc if doc is not None else cargar(desde)
    informe = validar(documento, desde)
    salida = ["el registro de fuentes no valida: %s" % e for e in informe["schemaErrors"]]
    for f in documento.get("sources") or []:
        estado = informe["sources"].get(f.get("id"))
        if estado == DUPLICADA:
            salida.append("la fuente %s esta declarada dos veces: el registro lleva una "
                          "entrada por fuente, no una por version" % f.get("id"))
        elif estado == SIN_EXTRACTO:
            salida.append("la fuente %s declara el extracto %s y no esta en este arbol"
                          % (f.get("id"), f.get("extract")))
        elif estado == SIN_HASH:
            salida.append("la fuente %s no tiene hash aceptado: su integridad no se puede "
                          "verificar hasta que alguien acepte el original (fuentes "
                          "--archivo <dir> --aceptar %s)" % (f.get("id"), f.get("id")))
    return salida
