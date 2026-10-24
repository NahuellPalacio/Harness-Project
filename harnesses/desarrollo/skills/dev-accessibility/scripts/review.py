#!/usr/bin/env python3
"""Revisión completa estática de accesibilidad: HTML, plantillas y JSX/TSX.

  review.py src/forms/alta.tsx templates/alta.blade.php
  review.py src/ --json
  review.py src/ --register evidencia.json --components form-text,button

Es la revisión que se corre cuando el alcance de la tarea lo pide (un formulario nuevo, una pantalla,
un componente), no tras cada escritura: eso lo hace el check liviano `dev-accesibilidad-html`. Usa el
mismo motor (checks/lib/a11y.py) y suma lo que el check liviano calla: heurísticas, recomendaciones y
lo que el archivo no alcanza a decidir.

Dice siempre qué cubrió y qué no: los archivos que no pudo leer, los componentes propios que no
resuelve, los {...props}. Un análisis estático limpio NO acredita conformidad: no mira contraste, foco,
teclado ni lector de pantalla. Con `--register` escribe un borrador del registro de evidencia donde lo
que falla estáticamente figura como `fail` con archivo y línea, y todo lo demás como `not_tested`; nada
sale `pass`.

Código de salida: 0 revisó (con `--strict`, 1 si hay algún fallo), 2 no encuentra el motor, no hay
archivos que revisar o el uso es incorrecto. Compatible con Python 3.9.
"""
import argparse
import json
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

IGNORADOS = ("node_modules", "vendor", "dist", "build", "out", "bin", "obj", ".git", ".venv", "__pycache__", "coverage", "target")
EXT_VISTAS = (".html", ".htm", ".xhtml", ".jsx", ".tsx", ".blade.php", ".njk", ".hbs", ".handlebars", ".twig",
              ".ejs", ".erb", ".jinja", ".jinja2", ".j2")
TIPO_ES = {"fail": "fallo", "defect": "defecto", "probable": "probable", "undeterminable": "no determinable",
           "recommendation": "recomendación"}


def buscar_motor(explicito=None):
    """La carpeta con a11y.py: la de la fábrica, la de un proyecto instalado, o la que se indique."""
    base = AQUI.parents[2]
    candidatos = [Path(explicito)] if explicito else [base / "checks" / "lib", base / "harness" / "checks" / "desarrollo" / "lib"]
    for c in candidatos:
        if (c / "a11y.py").is_file():
            return c
    return None


def juntar_archivos(rutas):
    vistos, salida, fuera = set(), [], []
    for r in rutas:
        p = Path(r)
        if p.is_dir():
            for raiz, dirs, archivos in os.walk(str(p)):
                dirs[:] = sorted(d for d in dirs if d not in IGNORADOS)
                for a in sorted(archivos):
                    if a.lower().endswith(EXT_VISTAS):
                        f = Path(raiz) / a
                        if str(f) not in vistos:
                            vistos.add(str(f))
                            salida.append(f)
        elif p.is_file():
            if str(p) not in vistos:
                vistos.add(str(p))
                salida.append(p)
        else:
            fuera.append((str(p), "no existe"))
    return salida, fuera


def revisar_archivos(a11y, archivos):
    resultados, no_leidos = [], []
    for f in archivos:
        try:
            if f.stat().st_size > 2 * 1024 * 1024:
                no_leidos.append((str(f), "más de 2 MB: no se analiza"))
                continue
            texto = f.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as e:
            no_leidos.append((str(f), "no se pudo leer: %s" % e.__class__.__name__))
            continue
        r = a11y.revisar(texto, str(f), "completo")
        resultados.append(r)
    return resultados, no_leidos


def cobertura(resultados, no_leidos, fuera, a11y):
    por_formato = {"html": 0, "template": 0, "jsx": 0}
    parciales, sin_alcance = [], []
    for r in resultados:
        if r.formato is None:
            sin_alcance.append(r.nombre)
            continue
        por_formato[r.formato] += 1
        if r.no_analizado:
            parciales.append(r.nombre)
    return {
        "analyzed": sum(por_formato.values()),
        "by_format": por_formato,
        "partial": parciales,
        "out_of_scope": sin_alcance,
        "unreadable": [{"file": f, "reason": m} for f, m in no_leidos],
        "missing": [{"file": f, "reason": m} for f, m in fuera],
    }


def borrador_de_registro(wcag, a11y, resultados, cob, nivel, componentes):
    datos = wcag.cargar_criterios()
    doc = wcag.plantilla_de_registro(nivel, [], componentes, datos)
    por_sc = {}
    for r in resultados:
        for h in r.hallazgos:
            for sc in h["sc"]:
                por_sc.setdefault(sc, []).append((r, h))
    n = cob["analyzed"]
    for fila in doc["criteria"]:
        sc = fila["sc"]
        hs = por_sc.get(sc, [])
        fallos = [(r, h) for r, h in hs if h["kind"] == "fail"]
        otros = [(r, h) for r, h in hs if h["kind"] != "fail"]
        if fila["result"] == "not_applicable":
            continue
        if fallos:
            r, h = fallos[0]
            fila.pop("reason", None)
            fila["result"] = "fail"
            fila["location"] = "%s:%s" % (r.nombre.replace("\\", "/"), h["line"] or "?")
            extra = (" — " + str(h["detail"])) if h["detail"] else ""
            fila["evidence"] = ("%s: %s%s" % (h["rule"], h["element"] or "", extra)).strip()
            fila["evidence_types"] = ["static"]
            fila["fix"] = a11y.CORRECCION[h["rule"]]
            fila["origin"] = h["origin"]
            if len(fallos) > 1:
                fila["occurrences"] = len(fallos)
        elif otros:
            r, h = otros[0]
            fila["reason"] = "El análisis estático marcó %s en %s:%s (%s); hay que confirmarlo. Falta la prueba manual." % (
                h["rule"], r.nombre.replace("\\", "/"), h["line"] or "?", TIPO_ES[h["kind"]])
        else:
            fila["reason"] = "Estática sin hallazgos en %d archivo(s); eso no acredita el criterio. Falta la prueba manual." % n
    doc["scope"]["files"] = [r.nombre.replace("\\", "/") for r in resultados if r.formato]
    doc["static_analysis"] = {
        "run": True,
        "files_analyzed": cob["analyzed"],
        "not_analyzed": (
            [{"file": r.nombre.replace("\\", "/"), "reason": x["reason"]} for r in resultados for x in r.no_analizado]
            + [{"file": u["file"], "reason": u["reason"]} for u in cob["unreadable"]]),
    }
    return doc


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            try:
                flujo.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="*", help="archivos o carpetas")
    p.add_argument("--json", action="store_true")
    p.add_argument("--register", help="escribe un borrador del registro de evidencia en este archivo")
    p.add_argument("--target-level", choices=["A", "AA", "AAA"], default="AA")
    p.add_argument("--components", default="", help="ids de componentes de Obelisco, separados por comas")
    p.add_argument("--strict", action="store_true", help="sale con 1 si hay algún fallo")
    p.add_argument("--engine", help="carpeta con a11y.py (por defecto se busca sola)")
    a = p.parse_args(argv)
    if not a.paths:
        p.print_usage(sys.stderr)
        return 2
    motor = buscar_motor(a.engine)
    if motor is None:
        sys.stderr.write("No encuentro el motor de análisis (checks/lib/a11y.py). Corré `install.ps1 -Update` para reponerlo.\n")
        return 2
    sys.path.insert(0, str(motor))
    import a11y
    import wcag

    archivos, fuera = juntar_archivos(a.paths)
    if not archivos:
        sys.stderr.write("No hay archivos HTML, de plantilla ni JSX/TSX para revisar en: %s\n" % ", ".join(a.paths))
        return 2
    resultados, no_leidos = revisar_archivos(a11y, archivos)
    cob = cobertura(resultados, no_leidos, fuera, a11y)
    fallos = sum(1 for r in resultados for h in r.hallazgos if h["kind"] == "fail")

    if a.register:
        doc = borrador_de_registro(wcag, a11y, resultados, cob, a.target_level, [c for c in a.components.split(",") if c])
        with open(a.register, "w", encoding="utf-8", newline="\n") as f:      # Path.write_text(newline=) es de 3.10
            f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    if a.json:
        salida = {
            "files": [{
                "file": r.nombre, "format": r.formato, "document": r.es_documento, "closed": r.cerrado,
                "findings": [dict(h, fix=a11y.CORRECCION[h["rule"]]) for h in r.hallazgos],
                "not_analyzed": r.no_analizado,
            } for r in resultados],
            "coverage": cob,
            "summary": {"failures": fallos, "findings": sum(len(r.hallazgos) for r in resultados)},
            "note": "Un análisis estático limpio no acredita conformidad.",
        }
        sys.stdout.write(json.dumps(salida, ensure_ascii=False, indent=1) + "\n")
        return 1 if (a.strict and fallos) else 0

    total = 0
    for r in resultados:
        for m in a11y.mensajes(r, os.path.basename(r.nombre)):
            total += 1
            sys.stdout.write(m + "\n")
    if not total:
        sys.stdout.write("Sin hallazgos estáticos en %d archivo(s). Eso no acredita conformidad.\n" % cob["analyzed"])
    f = cob["by_format"]
    sys.stdout.write("\nCobertura: %d archivo(s) analizados (HTML %d · plantillas %d · JSX/TSX %d); %d con partes que no se pudieron analizar.\n" % (
        cob["analyzed"], f["html"], f["template"], f["jsx"], len(cob["partial"])))
    for r in resultados:
        for x in r.no_analizado:
            sys.stdout.write("  no analizado — %s%s: %s\n" % (os.path.basename(r.nombre), (":L%d" % x["line"]) if x["line"] else "", x["reason"]))
    for u in cob["unreadable"] + cob["missing"]:
        sys.stdout.write("  no analizado — %s: %s\n" % (u["file"], u["reason"]))
    sys.stdout.write("No se probó: navegador, teclado ni lector de pantalla; contraste, foco, zoom y reflujo quedan sin verificar.\n")
    if a.register:
        sys.stdout.write("Borrador del registro en %s (todo `not_tested` salvo los fallos estáticos).\n" % a.register)
    return 1 if (a.strict and fallos) else 0


if __name__ == "__main__":
    sys.exit(main())
