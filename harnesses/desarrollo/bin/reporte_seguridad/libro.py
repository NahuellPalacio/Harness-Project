"""El `security-ledger.ndjson`: append-only, y append-only por construccion.

Copia el patron del libro del Bloque 4 y no su codigo. Un solo verbo de escritura, `agregar`:
no hay `reemplazar`, no hay `borrar`, no hay `reescribir`. Un hecho que cambia es un evento
nuevo -un `FINDING_UPDATED`, otro `RULE_EVALUATION`- y el viejo queda donde estaba.

🔴 Nadie escribe un evento a mano. `agregar` rechaza un evento sin `details.producer` de la lista
cerrada de `productores.py` o sin `evidenceFingerprints`. La huella dice de que salida
estructurada salio el evento; no prueba que esa salida sea verdadera, y eso esta en Riesgos.

La redaccion es la del Bloque 2 -`contexto/limpieza.redactar_arbol`, con el catalogo de
`comun/reglas/secretos.patrones.json`- mas dos capas que el catalogo no cubre y que este libro
necesita:

    por nombre de clave    `password`, `token`, `secret`, `cookie`, `sessionId`, `privateKey`
                           dentro de `details` llegan como `[redactado]`
    por formato            un bloque PEM entero, `sk-ant-...`, `Bearer ...`, `JSESSIONID=` y
                           `sessionid=`, que el catalogo no conoce o conoce a medias

Y el texto que deja el catalogo en lugar de un secreto se recorta a su id: la muestra de doce
caracteres que el catalogo guarda sirve en una transcripcion y sobra en un libro que se archiva.
"""
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from contexto import limpieza                    # noqa: E402

from . import archivo                            # noqa: E402

LIBRO = "security-ledger.ndjson"
RESUMEN = "security-summary.json"
REPORTE_MD = "security-status.md"
REPORTE_HTML = "security-status.html"

VERSION_SCHEMA = "security-ledger-event/1.0"
SCHEMA = "security-ledger-event.schema.json"

# Bajo `.claude/runtime/`, al lado de `accounting/`. Nunca en la raiz del proyecto, que no es
# nuestro.
BASE = (".claude", "runtime", "security")

# La lista cerrada. Son los nueve productores de `productores.py`, por nombre: un evento que no
# dice de cual salio no entra.
PRODUCTORES = ("desde_regla", "desde_check", "desde_revision", "desde_hallazgo",
               "desde_evaluacion", "desde_g2", "desde_aprobacion", "desde_integridad",
               "desde_frescura", "desde_refutacion")

# Una clave de `details` que contenga alguno de estos nombres llega con el valor redactado,
# sea lo que sea. Se compara en minusculas y sin separadores: `session_id`, `Set-Cookie` y
# `clientSecret` caen igual.
CLAVES_SENSIBLES = ("password", "passwd", "contrasena", "token", "secret", "cookie",
                    "sessionid", "privatekey")
REDACTADO = "[redactado]"

# Lo que el catalogo compartido no reconoce, o reconoce a medias: del PEM redacta la linea
# `BEGIN` y deja el cuerpo de la clave. Van ANTES del catalogo, porque despues del catalogo la
# linea `BEGIN` ya no esta y el cuerpo no tiene forma reconocible.
#
# Tres decisiones que valen para todos:
#   - el nombre no se ancla con `\b`: `db_password` y `x_sessionid` tienen un `_` antes, y `_`
#     es caracter de palabra. Se exige que antes NO haya letra ni digito.
#   - el valor puede venir citado con `"` o `'` -tambien escapado, `\"`, dentro de un JSON que
#     viaja como texto- y entonces se redacta hasta la comilla que cierra, con espacios adentro.
#   - `Bearer` y `sk-ant-` se redactan desde UN caracter de valor. Un token corto sigue siendo un
#     token, y el falso positivo -redactar "Bearer x" en una frase- cuesta menos que el contrario.
_VALOR = r"""(?:\\?"[^"\n]*?\\?"|'[^'\n]*'|[^\s;,&"'<>)\]}]+)"""
_ANTES = r"(?<![A-Za-z0-9])"

PATRONES_PROPIOS = (
    ("clave-privada-pem",
     re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----[\s\S]*?"
                r"(?:-----END [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|$)")),
    ("api-key-anthropic", re.compile(_ANTES + r"sk-ant-[A-Za-z0-9_\-]+")),
    ("authorization-bearer", re.compile(r"(?i)" + _ANTES + r"bearer\s+[A-Za-z0-9._~+/\-]+=*")),
    ("cookie-de-sesion",
     re.compile(r"(?i)" + _ANTES + r"(?:jsessionid|asp\.net_sessionid|aspsessionid[a-z]*|"
                r"phpsessid|connect\.sid|session_id|sessionid)\\?[\"']?\s*[:=]\s*" + _VALOR)),
    # E-03b: la contrasena se reconoce por la palabra, no por la sintaxis. Sin letra ni digito
    # pegado antes, sin letra, digito ni `_` pegado despues; entre la palabra y el valor,
    # cualquier mezcla de espacios, comillas, `:`, `=`, `>`, `-` (y `\`, que escapa una comilla).
    # Se redacta el primer valor de la misma linea: entre comillas, hasta la que cierra; si no,
    # hasta un espacio, una comilla, `<`, `,` o `;`.
    ("contrasena-en-texto",
     re.compile(r"(?i)" + _ANTES + r"(?:passphrase|password|passwd|pass|pwd|contrase(?:\u00f1|n)a"
                r"|clave)(?![A-Za-z0-9_])(?:"
                r"[ \t\"'`:=>\-\\]*[\"'][^\"'\n]+"
                r"|[ \t\"'`:=>\-\\]*[^\s\"'`<,;\\]+)")),
)

# Lo que deja el catalogo en lugar de un secreto, en sus dos formas: en el texto,
# `[secreto redactado: <id> <muestra>]`, y en el hallazgo, `<id>: <muestra> redactado en <donde>`.
# En las dos se queda el id y se va la muestra.
_MUESTRA_DEL_CATALOGO = re.compile(r"\[secreto redactado: ([A-Za-z0-9_\-]+)[^\]]*\]")
_MUESTRA_EN_HALLAZGO = re.compile(r"^([A-Za-z0-9_\-]+): .* redactado en (\$.*)$", re.S)

_HUELLA = re.compile(r"^sha256:[0-9a-f]{64}$")

_CACHE = {}


class EventoInvalido(ValueError):
    """El evento no entra al libro. Se dice por que y el libro queda igual."""


class TareaInvalida(ValueError):
    """Un `taskId` que no se puede usar como nombre de carpeta."""


# -- la carpeta por tarea ------------------------------------------------------

def validar_tarea(task_id):
    """El `taskId`, si sirve como nombre de carpeta. Levanta ANTES de tocar el disco.

    `..`, `/` y `\\` sacarian la carpeta de `.claude/runtime/security/`. `:` tambien se
    rechaza: en Windows `C:x` es una ruta relativa a otra unidad.
    """
    texto = task_id if isinstance(task_id, str) else ""
    if (not texto.strip() or ".." in texto or "/" in texto or "\\" in texto
            or ":" in texto or "\0" in texto):
        raise TareaInvalida(
            "`%s` no sirve como tarea: no puede estar vacia ni tener `..`, `/`, `\\` o `:`."
            % task_id)
    return texto


def carpeta_de(proyecto, task_id):
    return os.path.join(proyecto, *(BASE + (validar_tarea(task_id),)))


def ruta_de(proyecto, task_id, nombre=LIBRO):
    return os.path.join(carpeta_de(proyecto, task_id), nombre)


def es_el_libro(ruta):
    return archivo.es_el_libro(ruta)


def exigir_que_no_sea_el_libro(ruta, quien):
    return archivo.exigir_que_no_sea_el_libro(ruta, quien)


def escribir_atomico(ruta, texto, quien="el resumen"):
    """A un `.tmp` y despues encima. La guarda contra el libro vive en `archivo.py`."""
    return archivo.escribir_atomico(ruta, texto, quien)


# -- el contrato ---------------------------------------------------------------

def cargar_schema(desde=None):
    if "schema" in _CACHE:
        return _CACHE["schema"]
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise EventoInvalido("no esta %s: un evento no se valida contra un schema que no esta."
                             % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    _CACHE["schema"] = esquema
    return esquema


def _armador():
    if "armador" not in _CACHE:
        from orquestacion import tools
        _CACHE["armador"] = tools._armador()
    return _CACHE["armador"]


def validar(evento):
    """Lista de errores. Vacia es valido: schema, productor de la lista y huella."""
    if not isinstance(evento, dict):
        return ["el evento no es un objeto"]
    armador = _armador()
    if armador is None:
        return ["no esta contexto-armar.py, de donde sale el validador"]
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    errores = list(armador.validar(evento, esquema))

    detalles = evento.get("details")
    productor = detalles.get("producer") if isinstance(detalles, dict) else None
    if productor not in PRODUCTORES:
        errores.append("$.details.producer: `%s` no es un productor de la lista cerrada (%s). "
                       "Un evento escrito a mano no entra." % (productor, ", ".join(PRODUCTORES)))
    huellas = evento.get("evidenceFingerprints")
    if not isinstance(huellas, list) or not huellas:
        errores.append("$.evidenceFingerprints: falta. Sin la huella de la salida de la que "
                       "salio, el evento no dice de donde viene.")
    else:
        for i, h in enumerate(huellas):
            if not isinstance(h, str) or not _HUELLA.match(h):
                errores.append("$.evidenceFingerprints[%d]: `%s` no es sha256:<64 hex>" % (i, h))
    return errores


def huella(valor):
    """`sha256:` del JSON canonico del valor. Es lo que ata un evento a la salida de la que salio."""
    texto = json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       default=str)
    return "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()


# -- lectura -------------------------------------------------------------------

def leer_bytes(datos):
    """Los eventos de los bytes de un libro, en orden. Una linea rota no voltea el libro.

    La linea ilegible se devuelve marcada y el resumen la cuenta: perder el libro entero por
    una linea seria cambiar un dato malo por ninguno.
    """
    eventos = []
    texto = (datos or b"").decode("utf-8", errors="replace")
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            evento = json.loads(linea)
        except ValueError:
            evento = None
        if not isinstance(evento, dict):
            eventos.append({"eventId": "", "eventType": "", "unreadable": True})
            continue
        eventos.append(evento)
    return eventos


def bytes_de(ruta):
    if not os.path.isfile(ruta):
        return b""
    with io.open(ruta, "rb") as f:
        return f.read()


def leer(ruta):
    return leer_bytes(bytes_de(ruta))


def ids(ruta):
    return set(str(e.get("eventId") or "") for e in leer(ruta))


# -- redaccion -----------------------------------------------------------------

def _es_sensible(clave):
    normal = re.sub(r"[^a-z]", "", str(clave).lower().replace("ñ", "n"))
    return any(nombre in normal for nombre in CLAVES_SENSIBLES)


def _por_nombre(nodo, donde):
    """Redacta el valor de toda clave sensible, a cualquier profundidad."""
    if isinstance(nodo, dict):
        salida, hallazgos = {}, []
        for clave in nodo:
            ruta = "%s.%s" % (donde, clave)
            if _es_sensible(clave):
                salida[clave] = REDACTADO
                hallazgos.append("%s: clave sensible, valor redactado" % ruta)
                continue
            salida[clave], nuevos = _por_nombre(nodo[clave], ruta)
            hallazgos.extend(nuevos)
        return salida, hallazgos
    if isinstance(nodo, list):
        salida, hallazgos = [], []
        for i, hijo in enumerate(nodo):
            limpio, nuevos = _por_nombre(hijo, "%s[%d]" % (donde, i))
            salida.append(limpio)
            hallazgos.extend(nuevos)
        return salida, hallazgos
    return nodo, []


def _por_formato(nodo, donde):
    """Los patrones propios sobre cada string. Nunca devuelve el valor encontrado."""
    if isinstance(nodo, str):
        texto, hallazgos = nodo, []
        for nombre, patron in PATRONES_PROPIOS:
            texto, cuantos = patron.subn("[secreto redactado: %s]" % nombre, texto)
            if cuantos:
                hallazgos.append("%s: %s redactado en %s" % (nombre, nombre, donde))
        return texto, hallazgos
    if isinstance(nodo, dict):
        salida, hallazgos = {}, []
        for clave in nodo:
            salida[clave], nuevos = _por_formato(nodo[clave], "%s.%s" % (donde, clave))
            hallazgos.extend(nuevos)
        return salida, hallazgos
    if isinstance(nodo, list):
        salida, hallazgos = [], []
        for i, hijo in enumerate(nodo):
            limpio, nuevos = _por_formato(hijo, "%s[%d]" % (donde, i))
            salida.append(limpio)
            hallazgos.extend(nuevos)
        return salida, hallazgos
    return nodo, []


def _sin_muestra(nodo):
    if isinstance(nodo, str):
        return _MUESTRA_DEL_CATALOGO.sub(r"[secreto redactado: \1]", nodo)
    if isinstance(nodo, dict):
        return dict((k, _sin_muestra(v)) for k, v in nodo.items())
    if isinstance(nodo, list):
        return [_sin_muestra(v) for v in nodo]
    return nodo


def _hallazgo_sin_muestra(texto):
    return _MUESTRA_EN_HALLAZGO.sub(r"\1: valor redactado en \2", _sin_muestra(texto))


def redactar(evento):
    """(evento_limpio, hallazgos). Por nombre en `details`, por formato, y el catalogo."""
    limpio = dict(evento)
    hallazgos = []
    if isinstance(limpio.get("details"), dict):
        limpio["details"], nuevos = _por_nombre(limpio["details"], "$.details")
        hallazgos.extend(nuevos)
    limpio, nuevos = _por_formato(limpio, "$")
    hallazgos.extend(nuevos)
    catalogo = limpieza.cargar_catalogo()
    if catalogo is not None:
        limpio, nuevos = limpieza.redactar_arbol(limpio, catalogo, "$")
        hallazgos.extend(_hallazgo_sin_muestra(h) for h in nuevos)
        limpio = _sin_muestra(limpio)
    return limpio, hallazgos


# -- el unico verbo de escritura -----------------------------------------------

def agregar(ruta, evento):
    """Escribe el evento al final si su `eventId` no esta. Devuelve (escrito, hallazgos).

    Valida, deduplica, redacta y recien ahi abre el archivo, en modo `a`: nada de lo que ya
    estaba se toca.
    """
    if os.path.basename(str(ruta or "")) != LIBRO:
        raise EventoInvalido("agregar escribe solo en %s y la ruta es %s" % (LIBRO, ruta))
    errores = validar(evento)
    if errores:
        raise EventoInvalido("el evento no valida y no se escribe:\n  - %s"
                             % "\n  - ".join(errores[:6]))

    eid = str(evento.get("eventId") or "")
    if eid in ids(ruta):
        return False, []

    limpio, hallazgos = redactar(evento)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    linea = json.dumps(limpio, ensure_ascii=False, sort_keys=True) + "\n"
    with io.open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write(linea)
    return True, hallazgos


def agregar_varios(ruta, lista):
    """(escritos, salteados, hallazgos). Los salteados ya estaban."""
    escritos = salteados = 0
    hallazgos = []
    for evento in lista:
        ok, nuevos = agregar(ruta, evento)
        if ok:
            escritos += 1
        else:
            salteados += 1
        hallazgos.extend(nuevos)
    return escritos, salteados, hallazgos
