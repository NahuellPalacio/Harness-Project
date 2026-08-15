#!/usr/bin/env python
"""
docimg — lo que markitdown descarta.

markitdown convierte documentos a texto y tira las imagenes: de un .docx solo
sobrevive el alt-text, y de un PDF nada. Este script recupera esa capa.

Corre con el Python del venv de markitdown, que ya trae pypdfium2, pdfplumber y
pillow. No instala nada.

    PY = C:\\Users\\<usuario>\\AppData\\Roaming\\uv\\tools\\markitdown\\Scripts\\python.exe

Verbos:

    inventario <archivo>                      que hay adentro, sin extraer nada
    extraer    <docx|pptx|xlsx> --out <dir>   imagenes embebidas a disco
    buscar     <pdf> <termino>                en que paginas aparece
    render     <pdf> --pag 3,7-9 --out <dir>  paginas a PNG

Todo sale como JSON por stdout.

En PDF se renderiza la pagina, nunca se extraen las imagenes embebidas: los
diagramas de los estandares del GCBA son vectoriales (ES0901 tiene 2.968 objetos
vectoriales, Obelisco v2 tiene 28.348) y una extraccion de rasters devuelve nada.
"""

import argparse
import json
import os
import sys
import unicodedata
import zipfile

# La consola de Windows es cp1252 y rompe las tildes al imprimir.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OOXML = {".docx": "word/media/", ".pptx": "ppt/media/", ".xlsx": "xl/media/"}
RENDER_MAX = 8  # tope de paginas por render; se salta con --si


def salida(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def error(msg, **extra):
    salida({"ok": False, "error": msg, **extra})
    sys.exit(1)


def normalizar(s):
    """Minusculas y sin tildes, para que 'especificacion' encuentre 'especificación'."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def parse_paginas(spec, total):
    """'3,7-9' -> [3, 7, 8, 9]. Descarta lo que se sale del documento."""
    paginas = []
    for parte in spec.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            ini, fin = parte.split("-", 1)
            paginas.extend(range(int(ini), int(fin) + 1))
        else:
            paginas.append(int(parte))
    return sorted({p for p in paginas if 1 <= p <= total})


# --------------------------------------------------------------------------- #


def inventario(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    info = {
        "ok": True,
        "archivo": os.path.basename(ruta),
        "ruta": os.path.abspath(ruta),
        "tipo": ext,
        "kb": round(os.path.getsize(ruta) / 1024),
    }

    if ext == ".pdf":
        import pdfplumber
        import pypdfium2 as pdfium

        info["paginas"] = len(pdfium.PdfDocument(ruta))
        raster = vector = chars = 0
        with pdfplumber.open(ruta) as pdf:
            for pg in pdf.pages:
                raster += len(pg.images)
                vector += len(pg.curves) + len(pg.rects)
                chars += len(pg.extract_text() or "")
        info["raster"] = raster
        info["vector"] = vector
        info["chars_texto"] = chars
        info["chars_por_pagina"] = round(chars / max(info["paginas"], 1))
        # Un PDF con texto real ronda los miles de chars por pagina.
        info["probable_escaneado"] = info["chars_por_pagina"] < 100
        if info["probable_escaneado"]:
            motivo = "el PDF es escaneado y no tiene capa de texto"
        elif vector > raster:
            motivo = f"los diagramas son vectoriales ({vector} objetos), no hay rasters que extraer"
        else:
            motivo = "extraer rasters sueltos fragmenta el contenido y pierde el contexto"
        info["estrategia"] = f"render de pagina — {motivo}"
        info["render_completo_barato"] = info["paginas"] <= RENDER_MAX

    elif ext in OOXML:
        prefijo = OOXML[ext]
        with zipfile.ZipFile(ruta) as z:
            medios = [e for e in z.infolist() if e.filename.startswith(prefijo)]
        info["imagenes"] = [
            {"nombre": os.path.basename(e.filename), "kb": round(e.file_size / 1024)}
            for e in sorted(medios, key=lambda e: -e.file_size)
        ]
        info["total_imagenes"] = len(medios)
        info["estrategia"] = "extraer — son un ZIP, las imagenes salen tal cual"

    else:
        info["estrategia"] = "sin capa de imagen conocida para esta extension"

    return info


def extraer(ruta, destino):
    ext = os.path.splitext(ruta)[1].lower()
    if ext not in OOXML:
        error(
            f"'{ext}' no es un contenedor OOXML. Para PDF usa 'render'.",
            soportados=sorted(OOXML),
        )

    os.makedirs(destino, exist_ok=True)
    base = os.path.splitext(os.path.basename(ruta))[0][:40]
    prefijo = OOXML[ext]
    escritos = []

    with zipfile.ZipFile(ruta) as z:
        for entrada in z.infolist():
            if not entrada.filename.startswith(prefijo):
                continue
            nombre = f"{base}--{os.path.basename(entrada.filename)}"
            salida_archivo = os.path.join(destino, nombre)
            with z.open(entrada) as origen, open(salida_archivo, "wb") as fh:
                fh.write(origen.read())
            escritos.append({"archivo": salida_archivo, "kb": round(entrada.file_size / 1024)})

    return {
        "ok": True,
        "extraidas": len(escritos),
        "destino": os.path.abspath(destino),
        "imagenes": sorted(escritos, key=lambda i: -i["kb"]),
        "nota": "Leelas con la herramienta Read, que si ve imagenes.",
    }


def buscar(ruta, termino):
    import pdfplumber

    aguja = normalizar(termino)
    hits = []
    with pdfplumber.open(ruta) as pdf:
        total = len(pdf.pages)
        for i, pg in enumerate(pdf.pages, 1):
            texto = normalizar(pg.extract_text() or "")
            if aguja in texto:
                hits.append({"pagina": i, "coincidencias": texto.count(aguja)})

    return {
        "ok": True,
        "termino": termino,
        "paginas_totales": total,
        "encontrado_en": [h["pagina"] for h in hits],
        "detalle": hits,
        "nota": (
            "Sin coincidencias. Puede ser un PDF escaneado (probalo con inventario) "
            "o el termino esta solo dentro de una imagen."
            if not hits
            else f"Renderiza estas paginas con: render \"{os.path.basename(ruta)}\" "
            f"--pag {','.join(str(h['pagina']) for h in hits)}"
        ),
    }


def render(ruta, spec, destino, escala, forzar):
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(ruta)
    total = len(pdf)
    paginas = parse_paginas(spec, total) if spec else list(range(1, total + 1))

    if not paginas:
        error(f"Ninguna pagina valida en '{spec}'. El PDF tiene {total}.", paginas=total)

    if len(paginas) > RENDER_MAX and not forzar:
        error(
            f"{len(paginas)} paginas superan el tope de {RENDER_MAX}. "
            f"Acota con --pag, o pasa --si si de verdad las necesitas todas.",
            paginas_pedidas=len(paginas),
            tope=RENDER_MAX,
        )

    os.makedirs(destino, exist_ok=True)
    base = os.path.splitext(os.path.basename(ruta))[0][:40]
    escritos = []

    for n in paginas:
        img = pdf[n - 1].render(scale=escala).to_pil()
        archivo = os.path.join(destino, f"{base}--p{n:03d}.png")
        img.save(archivo)
        escritos.append(
            {
                "pagina": n,
                "archivo": archivo,
                "kb": round(os.path.getsize(archivo) / 1024),
                "px": f"{img.size[0]}x{img.size[1]}",
            }
        )

    return {
        "ok": True,
        "renderizadas": len(escritos),
        "de_un_total_de": total,
        "destino": os.path.abspath(destino),
        "paginas": escritos,
        "nota": "Leelas con la herramienta Read, que si ve imagenes.",
    }


# --------------------------------------------------------------------------- #


def main():
    p = argparse.ArgumentParser(prog="docimg", description=__doc__)
    sub = p.add_subparsers(dest="verbo", required=True)

    a = sub.add_parser("inventario", help="que hay adentro, sin extraer nada")
    a.add_argument("archivo")

    b = sub.add_parser("extraer", help="imagenes embebidas de docx/pptx/xlsx a disco")
    b.add_argument("archivo")
    b.add_argument("--out", required=True)

    c = sub.add_parser("buscar", help="en que paginas de un PDF aparece un termino")
    c.add_argument("archivo")
    c.add_argument("termino")

    d = sub.add_parser("render", help="paginas de un PDF a PNG")
    d.add_argument("archivo")
    d.add_argument("--pag", help="3,7-9 — sin esto, todas (hasta el tope)")
    d.add_argument("--out", required=True)
    d.add_argument("--escala", type=float, default=2.0)
    d.add_argument("--si", action="store_true", help="saltar el tope de paginas")

    args = p.parse_args()

    if not os.path.isfile(args.archivo):
        error(
            f"No existe: {args.archivo}",
            pista="Los archivos se mueven sin aviso. Buscalo con Glob antes de reintentar.",
        )

    if args.verbo == "inventario":
        salida(inventario(args.archivo))
    elif args.verbo == "extraer":
        salida(extraer(args.archivo, args.out))
    elif args.verbo == "buscar":
        salida(buscar(args.archivo, args.termino))
    elif args.verbo == "render":
        salida(render(args.archivo, args.pag, args.out, args.escala, args.si))


if __name__ == "__main__":
    main()
