"""Check: la forma del indice del codigo que escribe dev-iniciador-code.

El indice sirve para leer una linea y despues UNA ficha, en vez de cargar el codigo
entero. Eso se sostiene sobre tres cosas, y las tres se rompen en silencio:

  - que el indice y las fichas se correspondan en los dos sentidos. Una linea que
    apunta a un archivo que no existe manda a leer la nada; una ficha que nadie
    indexo es invisible, y el trabajo de escribirla ya se pago.
  - que cada ficha tenga sus cuatro secciones. Una ficha sin "De que depende" se lee
    igual de bien y contesta una pregunta menos.
  - que haya UNA ficha por modulo. El recorrido regenera el indice entero y pisa lo
    que habia; una copia al lado del original deja dos versiones del mismo modulo y
    ninguna que se sepa cual manda.
  - que los enlaces entre fichas lleguen a algun lado. La arista del mapa ES el
    enlace: uno que apunta a una ficha que no existe manda a leer la nada y ademas
    dibuja una arista falsa en el grafo, que se ve igual de firme que una real.

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

# Un wikilink de Obsidian. GitHub NO lo renderiza: lo muestra con los corchetes, como
# texto. Una ficha que los usa deja de ser navegable justo donde se lee la documentacion,
# a cambio de nada -la vista de grafo de Obsidian se arma igual con enlaces markdown-.
WIKILINK = re.compile(r"\[\[[^\]]+\]\]")

# Un bloque cercado o un span entre comillas invertidas. Se saca ANTES de buscar el
# wikilink: una ficha que documenta que los wikilinks no van escribe `[[wiki]]` como
# codigo, y reportarla seria avisarle a alguien que hizo justo lo que se le pidio. El
# falso positivo es lo que apaga un check.
CODIGO = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)

# Un nombre con sufijo de copia: `comun-hooks-1`, `comun-hooks (2)`, `comun-hooks-copia`.
# El sufijo solo, sin el original al lado, no prueba nada: un modulo puede llamarse
# `docs-adr-0001` con todo derecho. Por eso el hallazgo pide las DOS fichas.
DUPLICADA = re.compile(
    r"^(?P<base>.+?)(?:[-_ ](?:\d+|copia|copy)|\s*\((?:\d+|copia|copy)\))$",
    re.IGNORECASE)


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
    return (_revisar_ficha(archivo)
            + _revisar_enlaces(archivo, directorio)
            + _revisar_duplicada(archivo, directorio))


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


def _revisar_enlaces(archivo, directorio):
    """E-03, E-03b, E-04, E-06 — una ficha enlaza a otra ficha, y la otra ficha existe.

    Solo se miran los enlaces SIN barra: `[checks](checks.md)`. Uno con ruta
    -`../adr/0008-lo-externo.md`- apunta afuera del indice y no es asunto de este check.
    Exigirle que exista adentro seria un hallazgo sobre un enlace legitimo, y el falso
    positivo es el riesgo existencial de todo esto: un aviso que molesta sobre algo bien
    escrito se apaga, y con el se apagan los que servian.

    El enlace al propio archivo y el enlace a `indice.md` no son hallazgo: el primero es
    una ficha que se cita a si misma y el segundo es la vuelta al indice, que existe
    siempre.
    """
    hallazgos = []

    if WIKILINK.search(CODIGO.sub("", archivo["texto"])):
        hallazgos.append(
            "[codebase] %s usa enlaces [[wiki]]. GitHub no los renderiza: los muestra "
            "con los corchetes, como texto, y la ficha deja de ser navegable donde mas "
            "se la lee. Se enlaza con markdown relativo -[checks](checks.md)-, que anda "
            "en GitHub, en el editor y tambien en la vista de grafo de Obsidian."
            % archivo["nombre"])

    destinos = [d for d in ENLACE.findall(archivo["texto"])
                if "/" not in d and "\\" not in d]
    if not destinos:
        return hallazgos

    en_disco = _fichas_en_disco(directorio)
    if en_disco is None:
        return hallazgos

    conocidas = {n.lower() for n in en_disco}
    conocidas.add(INDICE)
    conocidas.add(archivo["nombre"].lower())

    rotos = sorted({d for d in destinos if d.lower() not in conocidas})
    if rotos:
        hallazgos.append(
            "[codebase] %s enlaza %d ficha(s) que no existen — %s. El enlace es la "
            "arista del mapa: uno que apunta a la nada manda a leer un archivo que no "
            "esta, y encima dibuja una arista que en el grafo se ve igual de firme que "
            "una real."
            % (archivo["nombre"], len(rotos), dev.formatear_lista(rotos)))
    return hallazgos


def _revisar_duplicada(archivo, directorio):
    """E-13 — un segundo recorrido regenera la ficha; no deja otra al lado.

    El recorrido es completo o no es: la segunda pasada PISA `comun-hooks.md`. Si
    aparece `comun-hooks-1.md` con el original todavia ahi, lo que se rompio no es esta
    ficha sino la promesa de que el indice se puede regenerar entero, y a partir de ahi
    hay dos versiones del mismo modulo y ninguna se sabe cual manda.

    Se mira el NOMBRE y no el contenido: dos fichas del mismo modulo pueden decir cosas
    distintas y las dos ser ciertas en el momento en que se escribieron. Lo unico que
    las distingue de dos modulos parecidos es el sufijo sobre un original que existe.
    """
    m = DUPLICADA.match(os.path.splitext(archivo["nombre"])[0])
    if m is None:
        return []

    en_disco = _fichas_en_disco(directorio)
    if en_disco is None:
        return []

    original = m.group("base") + ".md"
    hermanas = {n.lower(): n for n in en_disco}
    if original.lower() not in hermanas:
        return []

    return [
        "[codebase] %s parece una copia de %s, que sigue ahi. El recorrido regenera el "
        "indice entero y pisa la ficha: dos con el mismo modulo dejan al que lee sin "
        "saber cual manda. Se conserva una sola."
        % (archivo["nombre"], hermanas[original.lower()])
    ]
