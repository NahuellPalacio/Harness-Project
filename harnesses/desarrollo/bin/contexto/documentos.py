"""Document Resolver: los adjuntos de la Ficha, y su texto cuando se puede.

Lo que produce es el corpus documental del proyecto. **Cual de estos documentos hay que
leer para esta tarea no se decide aca**: es una decision semantica y la toma quien tenga
un modelo. Lo que se declara es que hay, de que tipo parece ser, y si su contenido esta
disponible o no.

La extraccion sigue ADR-0008 al pie: el harness no instala markitdown, no lo asume presente
y degrada sin el. Con markitdown, el documento entra con su texto; sin markitdown, entra
con su ruta y un hueco que dice que falta. Lo que nunca pasa es que el contrato mienta
sobre si el contenido esta.
"""
import os
import re
import subprocess

from . import limpieza

TOPE_POR_DEFECTO = 20000

# La clasificacion sale del nombre del archivo. Es una heuristica y viaja declarada como
# tal: abrir cada documento para clasificarlo es una decision semantica, y esa esta
# explicitamente afuera de este bloque.
PATRONES = (
    ("prd", r"\bprd\b|product[\s_-]*requirement"),
    ("adr", r"\badr\b|architecture[\s_-]*decision|decision[\s_-]*record"),
    ("regla", r"\bregla|\brules?\b|negocio|business"),
    ("arquitectura", r"arquitectura|architecture|diagrama[\s_-]*de[\s_-]*componentes"),
    ("manual", r"manual|instructivo|guia|guide|handbook"),
    ("diagrama", r"diagrama|diagram|\.vsdx?$|\.drawio$"),
)

CONVERTIBLES = (".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls")
TEXTO_PLANO = (".md", ".txt", ".csv", ".json", ".yaml", ".yml")


def clasificar(nombre):
    bajo = (nombre or "").lower()
    for etiqueta, patron in PATRONES:
        if re.search(patron, bajo):
            return etiqueta
    return "otro"


def markitdown_disponible(ejecutar=None):
    """Si `markitdown --version` contesta. No se instala ni se configura nada."""
    correr = ejecutar or _correr
    try:
        return correr(["markitdown", "--version"])[0] == 0
    except OSError:
        return False


def _correr(argumentos):
    r = subprocess.run(argumentos, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def resolver(jira, campos_tarea, campos_ficha, catalogo, config, acumulador,
             dir_descargas, ejecutar=None):
    """La seccion `documentation`. Nunca levanta."""
    adjuntos = _adjuntos(campos_tarea, campos_ficha)
    if not adjuntos:
        acumulador.falta("documentos: ni el ticket ni la Ficha de Proyecto tienen adjuntos")
        return {"items": [], "knowledge_status": "missing"}

    if not acumulador.hay("jira.attachment.read",
                          "sin eso no se pueden bajar los adjuntos de la Ficha"):
        return {"items": [], "knowledge_status": "missing"}

    hay_markitdown = markitdown_disponible(ejecutar)
    if not hay_markitdown:
        acumulador.falta(
            "el texto de los documentos convertibles: markitdown no esta en esta maquina. "
            "Los archivos se bajaron igual y quedan en %s; instalar markitdown hace que la "
            "proxima resolucion traiga el texto." % dir_descargas)

    tope = int(config.get("topeTextoDocumento") or TOPE_POR_DEFECTO)
    items = []
    for adjunto in adjuntos:
        items.append(_uno(jira, adjunto, catalogo, acumulador, dir_descargas,
                          hay_markitdown, tope, ejecutar))
    return {"items": items, "knowledge_status": "inferred"}


def _adjuntos(campos_tarea, campos_ficha):
    """Los del ticket y los de la ficha, sin duplicados, en orden estable."""
    vistos = set()
    salida = []
    for origen, campos in (("tarea", campos_tarea), ("ficha", campos_ficha)):
        if not isinstance(campos, dict):
            continue
        for a in (campos.get("attachment") or []):
            if not isinstance(a, dict):
                continue
            ident = str(a.get("id") or a.get("filename") or "")
            if not ident or ident in vistos:
                continue
            vistos.add(ident)
            salida.append((origen, a))
    return sorted(salida, key=lambda par: str(par[1].get("filename") or ""))


def _uno(jira, par, catalogo, acumulador, dir_descargas, hay_markitdown, tope, ejecutar):
    origen, adjunto = par
    nombre = str(adjunto.get("filename") or "")
    doc_id = str(adjunto.get("id") or nombre)
    clave_origen = str(adjunto.get("_origen") or origen)
    extension = os.path.splitext(nombre)[1].lower()

    item = {
        "doc_id": doc_id,
        "title": str(adjunto.get("title") or nombre),
        "filename": nombre,
        "mime": str(adjunto.get("mimeType") or ""),
        "size": int(adjunto.get("size") or 0),
        "origin": clave_origen,
        "classification": clasificar(nombre),
        "local_path": "",
        "text": "",
        "text_extracted": False,
        "extractor": "ninguno",
        "truncated": False,
    }

    url = str(adjunto.get("content") or "")
    if not url:
        acumulador.falta("el adjunto %s no trae URL de contenido" % nombre)
        return item

    destino = os.path.join(dir_descargas, nombre)
    vuelta = jira.bajar_adjunto(url, destino)
    ok = bool(vuelta[0])
    motivo = str(vuelta[2]) if len(vuelta) > 2 and vuelta[2] else ""
    if not ok:
        acumulador.falta("no se pudo bajar el adjunto %s" % nombre
                         + (": " + motivo if motivo else ""))
        return item

    item["local_path"] = destino
    acumulador.fuente("jira:adjunto:" + doc_id, "jira_attachment", nombre)

    texto = ""
    if extension in TEXTO_PLANO:
        try:
            with open(destino, "r", encoding="utf-8", errors="replace") as f:
                texto = f.read()
            item["extractor"] = "texto-plano"
        except OSError:
            texto = ""
    elif extension in CONVERTIBLES and hay_markitdown:
        codigo, salida = (ejecutar or _correr)(["markitdown", destino])
        if codigo == 0:
            texto = salida
            item["extractor"] = "markitdown"
        else:
            acumulador.falta("markitdown no pudo convertir %s" % nombre)

    if texto:
        texto, hallazgos = limpieza.redactar(texto, catalogo, "documento %s" % nombre)
        acumulador.redactado(hallazgos)
        texto, recortado = limpieza.recortar(texto, tope)
        item["truncated"] = recortado
        if recortado:
            acumulador.falta("el documento %s se recorto en %d caracteres" % (nombre, tope))
        item["text"] = texto
        item["text_extracted"] = True

    return item
