"""El recuperador lexico local, `local-lexico/1` (docs/cambios/knowledge-api/spec.md, seccion 20; ADR-0017).

Es el camino permanente que ADR-0008 exige y el unico de Task 6 (KD-15). Cumple el puerto interno de §19.1:

    identidad            `local-lexico/1`, que cumple `^[a-z0-9-]+/[0-9]+$`
    buscar(texto, lector)
                         recibe el texto YA redactado y la VISTA del lector de la consulta (`corpus.Vista`: solo
                         `documentos()`, `texto(corpus, document)` y `formato(corpus, document)`; sin `Entrada`,
                         sin ruta, sin raiz y sin el `Lector`), y devuelve una lista de candidatos
                         `{corpus, document, lines}` en su orden de preferencia

El modulo es el recuperador: `acceso.search` lo usa sin `recuperador` (§19.4), y la suite de conformidad le
pasa el modulo o un falso con la misma forma.

Lo que sigue es de ESTA implementacion, no del contrato (KC-40): un recuperador de Task 7 no lo tiene que
imitar.

    normalizacion  NFKD, sin marcas combinantes (categoria `Mn`) y `casefold`: «Cancelacion», «cancelacion» y
                   «CANCELACION» dan lo mismo (§20.2)
    terminos       los tramos de letras y digitos del texto normalizado, de tres caracteres o mas, sin repetir
    unidades       Markdown: cada encabezado de nivel 1 a 6 abre una seccion, salvo adentro de un bloque de
                   codigo; las lineas anteriores al primer encabezado son una unidad si alguna no esta en
                   blanco. JSON: una sola unidad, el documento entero (§20.2)
    puntaje        cuantos terminos DISTINTOS aparecen, como subcadena, en el texto normalizado de la unidad,
                   encabezado incluido; un entero (§20.3)
    orden          puntaje descendente, despues `corpus`, `document` y la primera linea de la unidad, todos por
                   punto de codigo (§20.3)

🔴 No devuelve texto contractual: solo donde esta cada candidato. El tramo, la revision y el ancla los arma la
fachada de su propia lectura (§15.3). Y el puntaje no sale de aca: el candidato no lo lleva, y el resultado de
la fachada tampoco (no hay `score`, KC-27).

🔴 No toca el disco: todo documento llega por la vista del lector, que lee cada uno una sola vez por consulta
(§19.2). Si un documento es JSON o Markdown lo dice la vista (`formato`), no una ruta.
Solo biblioteca estandar: sin red, sin embeddings, sin modelo, sin base vectorial y sin procesos (KA-E52).
Sin estado: no guarda nada entre dos consultas.
"""
import re
import unicodedata

from . import corpus

identidad = "local-lexico/1"

_LARGO_MINIMO = 3
_TERMINO = re.compile(r"[^\W_]+")                    # letras y digitos: `\w` sin el guion bajo
_ENCABEZADO = re.compile(r"#{1,6}(?: |\Z)")          # de uno a seis `#`, y un espacio o el fin de linea
_CERCAS = ("```", "~~~")


def normalizar(texto):
    """NFKD, sin las marcas de categoria `Mn` y `casefold` (§20.2)."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").casefold()


def terminos(texto):
    """Los terminos distintos del texto, ordenados: los tramos de letras y digitos del texto normalizado que
    tienen tres caracteres o mas (§20.2)."""
    return sorted(set(t for t in _TERMINO.findall(normalizar(texto)) if len(t) >= _LARGO_MINIMO))


def _unidades_markdown(lineas):
    """Las unidades de un Markdown como `(primera, ultima)`, numeradas desde 1 (§20.2).

    Un encabezado es una linea que EMPIEZA con uno a seis `#` seguidos de un espacio o del fin de linea. Una
    linea que empieza con ``` o con ~~~ abre un bloque de codigo y la siguiente de esas lo cierra: adentro no
    hay encabezados, y un bloque que no se cierra llega hasta el final. Cada encabezado abre una unidad que
    llega hasta la linea anterior al siguiente; lo anterior al primero es una unidad mas si alguna de sus
    lineas no esta en blanco.
    """
    encabezados = []
    en_codigo = False
    for n, linea in enumerate(lineas, 1):
        if linea.startswith(_CERCAS):
            en_codigo = not en_codigo
        elif not en_codigo and _ENCABEZADO.match(linea):
            encabezados.append(n)
    total = len(lineas)
    primero = encabezados[0] if encabezados else total + 1
    unidades = []
    if any(linea.strip() for linea in lineas[:primero - 1]):
        unidades.append((1, primero - 1))
    for i, desde in enumerate(encabezados):
        hasta = encabezados[i + 1] - 1 if i + 1 < len(encabezados) else total
        unidades.append((desde, hasta))
    return unidades


def _es_json(lector, corpus_id, documento):
    """El documento es un JSON si la vista del lector declara su `formato` como `json` (§19.2, §20.2): hoy, solo
    `project-context.json` de `codebase` (§8.1). No mira ninguna ruta: la vista no la tiene."""
    return lector.formato(corpus_id, documento) == "json"


def buscar(texto, lector):
    """Los candidatos de `texto` en los documentos que la vista del lector deja leer, en su orden de preferencia.

    Cada candidato es `{"corpus", "document", "lines"}`, con `lines` igual a `[primera, ultima]` de la unidad
    entera. Una consulta sin ningun termino no da candidatos. Un documento que el lector no pudo leer no
    cuenta: el lector ya anoto el hueco.
    """
    buscados = terminos(texto)
    if not buscados:
        return []
    puntuados = []
    for corpus_id, documento in lector.documentos():
        contenido = lector.texto(corpus_id, documento)
        if contenido is None:
            continue
        lineas = corpus.lineas(contenido)
        if _es_json(lector, corpus_id, documento):
            unidades = [(1, len(lineas))] if lineas else []
        else:
            unidades = _unidades_markdown(lineas)
        for primera, ultima in unidades:
            unidad = normalizar("\n".join(lineas[primera - 1:ultima]))
            puntaje = sum(1 for termino in buscados if termino in unidad)
            if puntaje:
                puntuados.append((-puntaje, corpus_id, documento, primera, ultima))
    puntuados.sort()
    return [{"corpus": c, "document": d, "lines": [p, u]} for _, c, d, p, u in puntuados]
