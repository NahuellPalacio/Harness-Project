"""El Anexo II de ES0901: que tecnologia esta homologada y en que version.

Es el dato contra el que se evalua G1. Lo que este modulo sabe hacer es leer el catalogo y
comparar una version contra una rama; **decidir no homologa nada**: lo que no esta en el
Anexo II no se aprueba ni se rechaza, es `ASI_EVALUATION_REQUIRED` y lo resuelve la ASI.

🔴 **Ningun booleano antes de tiempo.** Ocho estados, y cada uno es una decision distinta de
la siguiente:

    HOMOLOGATED                 esta, y la version cae en una rama homologada
    DEPRECATED_TOLERATED        esta listada como deprecada: se tolera con observacion
    NOT_HOMOLOGATED             esta, y la version no llega a lo que exige su rama
    ASI_EVALUATION_REQUIRED     no esta en el Anexo II, o la rama es posterior a lo listado
    TOOLCHAIN_AUXILIARY_REVIEW  es auxiliar declarada: no se homologa individualmente
    VERSION_CONTEXT_REQUIRED    el catalogo no fija numero: depende del framework
    PROVIDER_VERSION_REQUIRED   la version la asigna DGSEI
    VERSION_HISTORY_REQUIRED    para afirmar "dos estandares atras" hace falta historia
    UNRESOLVED                  no hay con que comparar

Un `false` no distingue "no esta homologada" de "no sabemos todavia", y son decisiones
opuestas: una frena un despliegue y la otra pide una evaluacion.

🔴 **El parche sube dentro de su rama, y nada mas.** Homologada `8.2.30` quiere decir que
`8.2.31` vale y `8.2.29` no. Una rama que no figura no se vuelve valida sola: mas vieja es
`NOT_HOMOLOGATED` y mas nueva es `ASI_EVALUATION_REQUIRED`, porque nadie la evaluo.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO = "annex-ii-technology-catalog.json"
SCHEMA = "annex-ii-technology-catalog.schema.json"

ESTANDAR = "ES0901"
VERSION_ESPERADA = "6.3"

HOMOLOGADA = "HOMOLOGATED"
DEPRECADA = "DEPRECATED_TOLERATED"
NO_HOMOLOGADA = "NOT_HOMOLOGATED"
EVALUACION_ASI = "ASI_EVALUATION_REQUIRED"
AUXILIAR = "TOOLCHAIN_AUXILIARY_REVIEW"
FALTA_CONTEXTO = "VERSION_CONTEXT_REQUIRED"
FALTA_HISTORIA = "VERSION_HISTORY_REQUIRED"
FALTA_PROVEEDOR = "PROVIDER_VERSION_REQUIRED"
SIN_RESOLVER = "UNRESOLVED"

TRAZA = {"standard": ESTANDAR, "version": VERSION_ESPERADA, "section": "7.1", "rule": "G1"}

# Una version que no se puede contrastar contra nada. `latest` no es una version homologada:
# no hay una sola entrada del Anexo II que diga "la ultima".
SIN_FIJAR = ("latest", "*", "", "x", "next", "main", "master", "stable")


class CatalogoInvalido(Exception):
    """El catalogo no se lee a medias."""


# -- carga ---------------------------------------------------------------------

def cargar(desde=None):
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        raise CatalogoInvalido("no esta %s" % ARCHIVO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise CatalogoInvalido("%s no se pudo leer: %s" % (ruta, e))
    problema = controlar_fuente(doc)
    if problema:
        raise CatalogoInvalido(problema)
    return doc


def controlar_fuente(doc):
    """"" si el catalogo es del estandar esperado; el error si no.

    Un catalogo de otra version homologa lo que ya no esta homologado, y lo hace en silencio.
    """
    fuente = doc.get("source") or {}
    if fuente.get("standard") != ESTANDAR or fuente.get("version") != VERSION_ESPERADA:
        return ("el catalogo es de %s %s y se esperaba %s %s: las versiones homologadas "
                "cambian entre versiones del estandar."
                % (fuente.get("standard"), fuente.get("version"), ESTANDAR, VERSION_ESPERADA))
    return ""


def validar_schema(doc, desde=None):
    """Lista de errores contra annex-ii-technology-catalog/1.0. Vacia es valido."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise CatalogoInvalido("no esta contexto-armar.py, de donde sale el validador.")
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise CatalogoInvalido("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def entradas(doc=None, desde=None):
    return list((doc if doc is not None else cargar(desde)).get("entries", []))


def buscar(nombre, doc=None, desde=None):
    """La entrada por id o por cualquiera de sus alias. None si no esta."""
    if not nombre:
        return None
    buscado = str(nombre).strip().lower()
    for e in entradas(doc, desde):
        if e.get("id", "").lower() == buscado:
            return e
        if any(str(a).lower() == buscado for a in e.get("aliases", []) or []):
            return e
        if str(e.get("name", "")).lower() == buscado:
            return e
    return None


# -- versiones -----------------------------------------------------------------
#
# 🔴 **Un solo orden de evaluacion** (ratificado por la autora de la spec el 2026-09-22):
#
#   1. la forma: lo que no esta escrito como lo escribe el Anexo II es UNRESOLVED, dentro o
#      fuera de cualquier rama;
#   2. el calificativo contra una rama listada: si el numero cae en una rama listada —en su
#      piso, arriba o ABAJO—, un calificativo de soporte que la tecnologia no usa o uno de otro
#      tipo que el del catalogo para esa rama es UNRESOLVED;
#   3. recien entonces la rama y el numero. Fuera de toda rama listada, un calificativo
#      canonico no cambia nada.

_NUM = re.compile(r"^(\d+(?:\.\d+)*)$")
# La forma canonica, la unica que se lee: numero, sufijo pegado en minuscula (`19c`), y o bien
# UN espacio y un calificativo en mayuscula (`1.1.0 CE`, `6.0 SP1`, `8.2.30 LTS`), o bien
# `(LTS)`/`(LTR)` con un espacio o pegado (`19.2.18 (LTS)`, `19.2.18(LTS)`). Nada mas: ni
# minuscula, ni pegado, ni edicion o service pack entre parentesis, ni parentesis suelto, ni
# un numero con cero adelante (`SP01`), ni dos espacios, ni tabulador.
_CON_CALIFICATIVO = re.compile(
    r"^(\d+(?:\.\d+)*)([a-z]{1,2})?(?: ([A-Z]+(?:0|[1-9]\d*)?)| ?\((LTS|LTR)\))?$")
_RAMA = re.compile(r"^(\d+(?:\.\d+)*)\.x$", re.I)
_RANGO = re.compile(r"^(\d+(?:\.\d+)*)\s+a\s+(\d+(?:\.\d+)*)$", re.I)
_SP = re.compile(r"^SP(0|[1-9]\d*)$")
_EDICION = re.compile(r"^[A-Z]+$")

# Los calificativos de soporte nombran la linea de mantenimiento de un numero que ya identifica
# el artefacto: `19.2.18` de Angular es el mismo paquete lo declare el inventario con `(LTS)` o
# sin el. Cualquier otro calificativo —la edicion `CE`, el service pack `SP1`— es parte de la
# identidad: `1.1.0 CE` y `1.1.0 EE` son dos artefactos distintos.
SOPORTE = ("LTS", "LTR")

# El tipo de un calificativo. Dos calificativos de distinto tipo no se comparan entre si.
SIN_TIPO = ""
TIPO_SOPORTE = "SUPPORT"
TIPO_SP = "SERVICE_PACK"
TIPO_EDICION = "EDITION"
TIPO_OTRO = "OTHER"                       # `X1`, `LTS1`: canonico en forma, de ningun tipo

# Lo que devuelve `comparar`. Solo COINCIDE homologa.
COINCIDE = "MATCH"
FUERA = "OUTSIDE"                         # fuera de toda rama: lo decide `_fuera_de_rama`
DEBAJO = "BELOW"                          # misma rama, por debajo del piso
ARRIBA = "ABOVE"                          # service pack posterior al listado: nadie lo evaluo
SP_ANTERIOR = "SERVICE_PACK_EARLIER"      # service pack anterior al listado
OTRO_CALIFICATIVO = "QUALIFIER_OTHER"     # otra edicion del mismo tipo: `EE` contra `CE`
FALTA_CALIFICATIVO = "QUALIFIER_MISSING"  # el catalogo fija uno y no se declara
CALIFICATIVO_AJENO = "QUALIFIER_UNLISTED" # de otro tipo, o de soporte que la tecnologia no usa

# Los que objetan en el paso 2, antes de mirar el numero.
OBJECIONES = (CALIFICATIVO_AJENO, FALTA_CALIFICATIVO, OTRO_CALIFICATIVO, SP_ANTERIOR, ARRIBA)


def parsear(crudo):
    """Que forma tiene una version del catalogo.

    El estandar las escribe de cinco maneras y las cinco significan cosas distintas:

        8.2.30               una version exacta: piso de su rama
        19.2.18 (LTS)        idem, con calificativo que se CONSERVA
        19c (LTR)            idem, con sufijo `c` que es parte del numero
        4.1.x                una rama entera
        2.51.0 a 2.57.1      un rango inclusivo
        framework-dependent  no hay numero, y el motivo importa
    """
    texto = str(crudo or "").strip()
    m = _RANGO.match(texto)
    if m:
        return {"kind": "RANGE", "from": _tupla(m.group(1)), "to": _tupla(m.group(2)),
                "qualifier": "", "suffix": "", "raw": texto}
    m = _RAMA.match(texto)
    if m:
        return {"kind": "BRANCH", "version": _tupla(m.group(1)), "qualifier": "", "suffix": "",
                "raw": texto}
    m = _NUM.match(texto)
    if m:
        return {"kind": "EXACT", "version": _tupla(m.group(1)), "qualifier": "", "suffix": "",
                "raw": texto}
    m = _CON_CALIFICATIVO.match(texto)
    if m:
        return {"kind": "EXACT", "version": _tupla(m.group(1)), "suffix": m.group(2) or "",
                "qualifier": m.group(3) or m.group(4) or "", "raw": texto}
    return {"kind": "SENTINEL", "qualifier": "", "suffix": "", "raw": texto}


def _tupla(texto):
    return tuple(int(p) for p in texto.split("."))


def _rama(version):
    """La rama: major.minor. Es la unidad dentro de la que sube el parche."""
    return tuple(version[:2])


def _como_pedida(pedida):
    if isinstance(pedida, dict):
        return pedida
    return {"version": tuple(pedida), "qualifier": "", "suffix": ""}


def tipo(calificativo):
    q = calificativo or ""
    if not q:
        return SIN_TIPO
    if q in SOPORTE:
        return TIPO_SOPORTE
    if _SP.match(q):
        return TIPO_SP
    if _EDICION.match(q):
        return TIPO_EDICION
    return TIPO_OTRO


def soporte_de(entrada):
    """Los calificativos de soporte que el catalogo usa para una tecnologia, en cualquiera de
    sus versiones. `angular` usa `LTS`; `php` no usa ninguno."""
    usados = set()
    crudas = (list(entrada.get("homologatedVersionsRaw") or [])
              + list(entrada.get("deprecatedVersionsRaw") or []))
    for crudo in crudas:
        q = parsear(crudo).get("qualifier", "")
        if q in SOPORTE:
            usados.add(q)
    return tuple(sorted(usados))


def en_rama(pedida, parsed):
    """Si el numero cae en la rama de una version del catalogo: en su piso, arriba o abajo."""
    v = tuple(_como_pedida(pedida)["version"])
    kind = parsed["kind"]
    if kind == "EXACT":
        return _rama(v) == _rama(parsed["version"])
    if kind == "BRANCH":
        return tuple(v[:len(parsed["version"])]) == parsed["version"]
    if kind == "RANGE":
        return parsed["from"] <= v <= parsed["to"]
    return False


def comparar(pedida, parsed, soporte=()):
    """Donde cae una version pedida respecto de UNA version del catalogo: pasos 2 y 3.

    🔴 **El calificativo no se recorta al comparar, y se mira antes que el numero.** Si el
    numero cae en la rama, primero objeta el calificativo (`objecion`) y solo sin objecion se
    compara el numero contra el piso.

    `soporte` son los calificativos de soporte que la tecnologia usa en el catalogo
    (`soporte_de`). Uno de esos, declarado, no cambia el artefacto en ninguna comparacion.
    """
    d = _como_pedida(pedida)
    if not en_rama(d, parsed):
        return FUERA
    reparo = objecion(d, parsed, soporte)
    if reparo:
        return reparo
    if parsed["kind"] == "EXACT" and tuple(d["version"]) < parsed["version"]:
        return DEBAJO
    return COINCIDE


def objecion(d, parsed, soporte=()):
    """Paso 2: lo que el calificativo declarado objeta contra una version de la rama. "" si nada."""
    s_cat, s_ped = parsed.get("suffix", ""), d.get("suffix", "")
    if s_cat != s_ped:
        if s_cat and s_ped:
            return OTRO_CALIFICATIVO
        return FALTA_CALIFICATIVO if s_cat else CALIFICATIVO_AJENO
    q_cat, q_ped = parsed.get("qualifier", ""), d.get("qualifier", "")
    t_cat, t_ped = tipo(q_cat), tipo(q_ped)
    if t_ped == TIPO_SOPORTE:
        if q_ped not in soporte:
            return CALIFICATIVO_AJENO
        t_ped = SIN_TIPO                 # la tecnologia lo usa: no cambia el artefacto
    if t_cat == TIPO_SOPORTE:
        t_cat = SIN_TIPO                 # el inventario puede no decirlo
    if t_ped == SIN_TIPO and t_cat == SIN_TIPO:
        return ""
    if t_ped == SIN_TIPO:
        return FALTA_CALIFICATIVO
    if t_cat == SIN_TIPO or t_ped != t_cat or t_ped == TIPO_OTRO:
        return CALIFICATIVO_AJENO
    if t_ped == TIPO_EDICION:
        return "" if q_ped == q_cat else OTRO_CALIFICATIVO
    n_cat, n_ped = int(_SP.match(q_cat).group(1)), int(_SP.match(q_ped).group(1))
    if n_ped == n_cat:
        return ""
    return ARRIBA if n_ped > n_cat else SP_ANTERIOR


def cae_en(version, parsed):
    """Si una version pedida cae adentro de una version homologada del catalogo."""
    return comparar(version, parsed) == COINCIDE


def version_pedida(crudo):
    """Paso 1: lo que declara el inventario, parseado (`version`, `suffix`, `qualifier`), o None
    si no esta en forma canonica o no se puede contrastar contra nada.

    El texto se lee como viene: un espacio o un tabulador de mas, adelante o atras, ya no es
    como lo escribe el Anexo II.
    """
    texto = str(crudo if crudo is not None else "")
    if texto != texto.strip():
        return None
    if texto.lower() in SIN_FIJAR or texto.lower().endswith(".x"):
        return None
    p = parsear(texto)
    if p["kind"] == "EXACT":
        return p
    return None
