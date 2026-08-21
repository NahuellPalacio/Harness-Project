"""Check: la forma del indice del codigo que escribe dev-iniciador-code.

El indice sirve para leer una linea y despues UNA ficha, en vez de cargar el codigo
entero. Eso se sostiene sobre dos cosas, y las dos se rompen en silencio:

  - que el indice y las fichas se correspondan en los dos sentidos. Una linea que
    apunta a un archivo que no existe manda a leer la nada; una ficha que nadie
    indexo es invisible, y el trabajo de escribirla ya se pago.
  - que cada ficha tenga sus cuatro secciones. Una ficha sin "De que depende" se lee
    igual de bien y contesta una pregunta menos.

Solo mira lo que se acaba de escribir, y solo si cayo adentro del directorio del
indice. En cualquier otro proyecto -y en cualquier otra escritura- no hace nada.

🔴 Los secretos NO se chequean aca. Los bloquea pre-tool-use.py ANTES de que el
archivo llegue al disco, que es la unica regla que este harness bloquea. Un segundo
detector en PostToolUse llegaria tarde y con menos autoridad. E-10 se verifica en la
suite, sobre el catalogo, no en tiempo de ejecucion.

Avisa, no bloquea. Lo unico que este harness bloquea son los secretos.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import dev  # noqa: E402

RUTA_POR_DEFECTO = "docs/codebase"
INDICE = "indice.md"

# Los titulos van exactos, con tilde. El agente los escribe asi y el que lee una ficha
# espera encontrarlos siempre iguales: cuatro preguntas, en el mismo orden, en todas.
SECCIONES = ["## Qué es", "## Qué expone", "## De qué depende", "## Dónde está"]

# Un enlace markdown a una ficha: [`comun-hooks.md`](comun-hooks.md). Se lee el destino
# del parentesis, que es lo que un lector va a seguir de verdad.
ENLACE = re.compile(r"\]\(\s*([^)\s]+\.md)\s*\)")


def _ruta_codebase(proyecto, config):
    """El directorio del indice. El default vive aca porque harness.config.json solo se
    crea si no existe: un proyecto instalado antes de este cambio no tiene la clave."""
    ruta = (config or {}).get("rutaCodebase")
    if not isinstance(ruta, str) or not ruta.strip():
        ruta = RUTA_POR_DEFECTO
    return os.path.normpath(os.path.join(proyecto, ruta))


def _adentro(ruta_archivo, directorio):
    try:
        return os.path.commonpath([os.path.normpath(ruta_archivo), directorio]) == directorio
    except ValueError:      # unidades distintas en Windows
        return False


def _fichas_en_disco(directorio):
    try:
        nombres = os.listdir(directorio)
    except OSError:
        return None
    return sorted(n for n in nombres
                  if n.lower().endswith(".md") and n.lower() != INDICE)


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    archivo = dev.archivo_escrito(evento)
    if archivo is None or archivo["extension"] != ".md":
        return []

    directorio = _ruta_codebase(proyecto, config)
    if not _adentro(archivo["ruta"], directorio):
        return []

    if archivo["nombre"].lower() == INDICE:
        return _revisar_indice(archivo, directorio)
    return _revisar_ficha(archivo)


def _revisar_indice(archivo, directorio):
    """E-08 — la correspondencia va en los dos sentidos."""
    en_disco = _fichas_en_disco(directorio)
    if en_disco is None:
        return []

    apuntadas = {os.path.basename(d) for d in ENLACE.findall(archivo["texto"])}
    apuntadas.discard(INDICE)

    faltan = sorted(n for n in apuntadas if n not in en_disco)
    huerfanas = sorted(n for n in en_disco if n not in apuntadas)

    hallazgos = []
    if faltan:
        hallazgos.append(
            "[codebase] el indice apunta a %d ficha(s) que no existen — %s. "
            "Una linea que manda a leer la nada cuesta mas que una linea que falta: "
            "el que la sigue cree que el dato esta y no lo encuentra."
            % (len(faltan), dev.formatear_lista(faltan)))
    if huerfanas:
        hallazgos.append(
            "[codebase] hay %d ficha(s) que el indice no nombra — %s. "
            "Una ficha sin linea en el indice es invisible: se pago escribirla y nadie "
            "la va a abrir. Se agrega la linea, o se borra la ficha a mano."
            % (len(huerfanas), dev.formatear_lista(huerfanas)))
    return hallazgos


def _revisar_ficha(archivo):
    """E-09 — las cuatro secciones, con esos titulos exactos."""
    faltantes = [s for s in SECCIONES if s not in archivo["texto"]]
    if not faltantes:
        return []

    return [
        "[codebase] %s no tiene %d de las cuatro secciones — falta %s. "
        "Van con ese titulo exacto y con tilde: son las cuatro preguntas que alguien "
        "le va a hacer a la ficha, y una que falte se lee como si no tuviera respuesta."
        % (archivo["nombre"], len(faltantes), dev.formatear_lista(faltantes))
    ]
