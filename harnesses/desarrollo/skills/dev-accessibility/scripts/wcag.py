#!/usr/bin/env python3
"""Consulta de WCAG 2.2, niveles de un texto y registro de evidencia.

Cada comando imprime lo que se pidió y nada más: la skill no se carga entera, se consulta.

  wcag.py count                              cuántos criterios hay, por nivel (sale de los datos)
  wcag.py criterion 2.4.11 [--brief]         un criterio: nivel, pruebas que exige y su texto normativo
  wcag.py list [--level AA | --up-to AA] [--new] [--principle operable]
  wcag.py task [forms]                       criterios y guía de una tarea (sin argumento: las tareas)
  wcag.py component [form-text]              fila de la matriz de Obelisco (sin argumento: los componentes)
  wcag.py term target                        definición normativa del glosario
  wcag.py levels ARCHIVO...                  marca los pares «criterio / nivel» mal escritos en un texto
  wcag.py register template --level AA       registro vacío con todos los criterios en not_tested
  wcag.py register validate REGISTRO.json    valida un registro de evidencia

Salida para personas, en español. `--json` entrega lo mismo como datos.
Código de salida: 0 bien, 1 el control encontró algo, 2 uso incorrecto o dato inexistente.
Compatible con Python 3.9.
"""
import argparse
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REFS = AQUI.parent / "references"

RANGO = {"A": 1, "AA": 2, "AAA": 3}
FAMILIAS = ("browser", "keyboard", "screen_reader")
FAMILIA_ES = {"browser": "navegador", "keyboard": "teclado", "screen_reader": "lector de pantalla"}
RESULTADOS = ("pass", "fail", "not_applicable", "not_tested")
RESULTADO_ES = {"pass": "aprobado", "fail": "fallido", "not_applicable": "no aplicable", "not_tested": "no probado"}
TIPOS_EVIDENCIA = ("static", "code_review", "contrast_computed") + FAMILIAS
ESQUEMA_REGISTRO = "a11y-evidence/1"
MAX_SECCION = 7000


# -- datos ------------------------------------------------------------------------------------

def _leer_json(nombre):
    return json.loads((REFS / nombre).read_text(encoding="utf-8"))


def cargar_criterios():
    return _leer_json("wcag22-criteria.json")


def cargar_matriz():
    return _leer_json("obelisco-matrix.json")


def indice_criterios(datos=None):
    datos = datos or cargar_criterios()
    return {c["id"]: c for c in datos["criteria"]}


def conteo(datos=None):
    datos = datos or cargar_criterios()
    por_nivel = {n: 0 for n in RANGO}
    for c in datos["criteria"]:
        por_nivel[c["level"]] += 1
    return {"total": len(datos["criteria"]), "by_level": por_nivel,
            "removed": [r["id"] for r in datos["removed"]]}


# -- texto normativo ---------------------------------------------------------------------------

def _seccion(archivo, es_inicio, limite=MAX_SECCION):
    """Las líneas desde el encabezado `### ...` que cumple es_inicio hasta el siguiente encabezado."""
    ruta = REFS / "wcag22" / archivo
    if not ruta.is_file():
        return None
    salida, dentro = [], False
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if dentro and (linea.startswith("### ") or linea.startswith("## ")):
            break
        if not dentro and linea.startswith("### ") and es_inicio(linea[4:]):
            dentro = True
        if dentro:
            salida.append(linea)
    if not salida:
        return None
    texto = "\n".join(salida).strip()
    if len(texto) > limite:
        texto = texto[:limite].rstrip() + "\n[… recortado: el texto completo está en references/wcag22/%s]" % archivo
    return texto


def texto_de_criterio(sc, datos=None):
    indice = indice_criterios(datos)
    if sc not in indice:
        return None
    prefijo = sc + " "
    return _seccion(indice[sc]["principle"] + ".md", lambda t: t.startswith(prefijo))


def texto_de_termino(palabra):
    palabra = palabra.strip().lower()
    return _seccion("glossary.md", lambda t: palabra in re.sub(r"\*\*.*?\*\*", "", t).strip().lower(), 4000)


# -- niveles de un texto ------------------------------------------------------------------------

_SC = re.compile(r"(?<![\d.])(\d\.\d{1,2}\.\d{1,2})(?![\d])")
_NIVEL = re.compile(r"\b(?:Level|Nivel)\s+(AAA|AA|A)\b|\((AAA|AA|A)\)")
_FILA = re.compile(r"^\|\s*(?:SC\s*)?(\d\.\d{1,2}\.\d{1,2})\s*[⚠★]*\s*\|[^|\n]*\|\s*(AAA|AA|A)\s*\|")
# la variante con el nombre en la misma celda: | 2.4.11 Focus Not Obscured (Minimum) | AA | ...
_FILA_NOMBRE = re.compile(r"^\|\s*(?:SC\s*)?(\d\.\d{1,2}\.\d{1,2})\s+[^|\n]*\|\s*(AAA|AA|A)\s*\|")
_HISTORICO = re.compile(r"removed|obsolete|retirad|\b2\.0\b|\b2\.1\b", re.IGNORECASE)
# Lo que puede haber entre el número de criterio y su nivel para que sean un par: el nombre del
# criterio (palabras con mayúscula y conectores, con paréntesis) o nada más que «is», «:» o «=».
# Una oración entera en el medio no es un par: «… follow Success Criterion 2.1.1. If that is not
# possible … this Level AAA success criterion» habla del nivel de OTRO criterio.
_CONECTOR = r"(?:and|of|in|or|the|to|for|a|an|with|on|no|by|&)"
_PALABRA = r"(?:[A-Z0-9(][\w’'/()-]*,?|" + _CONECTOR + r",?)"
_ENTRE = re.compile(r"^\.?[\s:–—-]*(?:(?:is|are|=)\s*)?(?:" + _PALABRA + r"(?:\s+" + _PALABRA + r")*)?\s*\(?$")


def comprobar_niveles(texto, nombre="", datos=None):
    """Los pares «criterio / nivel» del texto que no coinciden con WCAG 2.2.

    Devuelve dicts {file, line, sc, level, code, message}. Un par es un número de criterio seguido,
    en la misma línea y sin otro criterio en el medio, por «Level X», «Nivel X» o «(X)»; o la fila
    de una tabla `| n.n.n | nombre | X |`.
    """
    datos = datos or cargar_criterios()
    indice = indice_criterios(datos)
    retirados = {r["id"] for r in datos["removed"]}
    problemas = []

    def revisar(n, sc, nivel, linea):
        if sc in retirados:
            if not _HISTORICO.search(linea):
                problemas.append({"file": nombre, "line": n, "sc": sc, "level": nivel, "code": "removed_with_level",
                                  "message": "4.1.1 fue retirado en WCAG 2.2 y no tiene nivel; escribirlo con «%s» solo vale si se habla de 2.0 o 2.1." % nivel})
            return
        if sc not in indice:
            problemas.append({"file": nombre, "line": n, "sc": sc, "level": nivel, "code": "unknown_sc",
                              "message": "WCAG 2.2 no tiene un criterio %s." % sc})
            return
        real = indice[sc]["level"]
        if real != nivel:
            problemas.append({"file": nombre, "line": n, "sc": sc, "level": nivel, "code": "wrong_level",
                              "message": "SC %s %s es nivel %s, no %s." % (sc, indice[sc]["name"], real, nivel)})

    for n, linea in enumerate(texto.splitlines(), 1):
        fila = _FILA.match(linea) or _FILA_NOMBRE.match(linea)
        if fila:
            revisar(n, fila.group(1), fila.group(2), linea)
            continue
        criterios = [(m.start(), m.group(1)) for m in _SC.finditer(linea)]
        if not criterios:
            continue
        for m in _NIVEL.finditer(linea):
            previos = [(p, sc) for p, sc in criterios if p < m.start() and m.start() - p <= 140]
            if not previos:
                continue
            p, sc = previos[-1]
            entre = linea[p + len(sc):m.start()]
            if not _ENTRE.match(entre.strip()):
                continue
            revisar(n, sc, m.group(1) or m.group(2), linea)
    return problemas


# -- registro de evidencia ------------------------------------------------------------------------

def _exigidos(objetivo, datos):
    nivel = objetivo.get("level")
    adicionales = list(objetivo.get("additional") or [])
    base = [c["id"] for c in datos["criteria"] if RANGO[c["level"]] <= RANGO[nivel]]
    return base, adicionales


def plantilla_de_registro(nivel="AA", adicionales=None, componentes=None, datos=None):
    datos = datos or cargar_criterios()
    adicionales = list(adicionales or [])
    base, _ = _exigidos({"level": nivel, "additional": adicionales}, datos)
    filas = []
    for sc in base + [a for a in adicionales if a not in base]:
        filas.append({"sc": sc, "result": "not_tested", "reason": "Todavía no se probó."})
    filas.append({"sc": "4.1.1", "result": "not_applicable",
                  "reason": "Retirado en WCAG 2.2; los defectos de marcado con efecto se informan en 1.3.1 o 4.1.2."})
    filas.sort(key=lambda f: [int(x) for x in f["sc"].split(".")])
    return {
        "schema": ESQUEMA_REGISTRO,
        "target": {"wcag": "2.2", "level": nivel, "additional": adicionales},
        "scope": {"description": "", "files": [], "components": list(componentes or [])},
        "tests": {f: "not_performed" for f in FAMILIAS},
        "static_analysis": {"run": False, "files_analyzed": 0, "not_analyzed": []},
        "criteria": filas,
    }


def _vacio(valor):
    return not (isinstance(valor, str) and valor.strip())


def resumir_registro(doc, datos=None):
    """Los conteos por resultado de lo que el objetivo exige (más 4.1.1), y los de las filas extra.

    Una fila extra es un criterio que existe y que el objetivo no exige —un AAA en un registro de nivel
    AA—: se acepta, no se exige, y se cuenta aparte para no mezclarla con lo que sí se exigía.
    """
    datos = datos or cargar_criterios()
    indice = indice_criterios(datos)
    retirados = {r["id"] for r in datos["removed"]}
    base, adicionales = _exigidos(doc.get("target") or {}, datos)
    exigidos = set(base) | {a for a in adicionales if a in indice}
    conteos = {r: 0 for r in RESULTADOS}
    extra = {r: 0 for r in RESULTADOS}
    fallos_por_nivel = {n: 0 for n in RANGO}
    for f in doc.get("criteria") or []:
        if not isinstance(f, dict) or f.get("result") not in RESULTADOS:
            continue
        sc, resultado = f.get("sc"), f["result"]
        if sc in exigidos or sc in retirados:
            conteos[resultado] += 1
            if resultado == "fail" and sc in indice:
                fallos_por_nivel[indice[sc]["level"]] += 1
        elif sc in indice:
            extra[resultado] += 1
    return {"counts": conteos, "extra": extra, "fail_by_level": fallos_por_nivel}


def validar_registro(doc, datos=None):
    """Los errores de un registro de evidencia, cada uno {code, sc, message}. Lista vacía = válido."""
    datos = datos or cargar_criterios()
    indice = indice_criterios(datos)
    retirados = {r["id"] for r in datos["removed"]}
    errores = []

    def err(code, sc, mensaje):
        errores.append({"code": code, "sc": sc, "message": mensaje})

    if not isinstance(doc, dict) or doc.get("schema") != ESQUEMA_REGISTRO:
        err("schema", None, "El registro tiene que declarar schema = %s." % ESQUEMA_REGISTRO)
        return errores
    objetivo = doc.get("target")
    if not isinstance(objetivo, dict) or objetivo.get("level") not in RANGO:
        err("target", None, "target.level tiene que ser A, AA o AAA.")
        return errores
    adicionales = objetivo.get("additional") or []
    for a in adicionales:
        if a not in indice:
            err("unknown_criterion", a, "target.additional nombra %s, que no es un criterio de WCAG 2.2." % a)

    pruebas = doc.get("tests")
    if not isinstance(pruebas, dict) or any(pruebas.get(f) not in ("performed", "not_performed") for f in FAMILIAS):
        err("tests", None, "tests tiene que traer browser, keyboard y screen_reader, cada uno performed o not_performed.")
        pruebas = {}

    base, _ = _exigidos(objetivo, datos)
    exigidos = set(base) | {a for a in adicionales if a in indice}
    filas = doc.get("criteria")
    if not isinstance(filas, list):
        err("criteria", None, "criteria tiene que ser una lista.")
        return errores

    vistos = set()
    for f in filas:
        if not isinstance(f, dict):
            err("criteria", None, "Una fila de criteria no es un objeto.")
            continue
        sc, resultado = f.get("sc"), f.get("result")
        if sc in vistos:
            err("duplicate_criterion", sc, "El criterio %s aparece más de una vez." % sc)
        vistos.add(sc)
        if sc not in indice and sc not in retirados:
            err("unknown_criterion", sc, "%s no es un criterio de WCAG 2.2." % sc)
            continue
        if resultado not in RESULTADOS:
            err("bad_result", sc, "SC %s: el resultado «%s» no es pass, fail, not_applicable ni not_tested." % (sc, resultado))
            continue
        if sc in retirados:
            if resultado != "not_applicable":
                err("removed_criterion", sc, "4.1.1 fue retirado en WCAG 2.2: solo puede ir como not_applicable.")
            elif _vacio(f.get("reason")):
                err("missing_reason", sc, "SC %s: not_applicable necesita reason." % sc)
            continue
        tipos = f.get("evidence_types") or []
        for t in tipos:
            if t not in TIPOS_EVIDENCIA:
                err("bad_evidence_type", sc, "SC %s: el tipo de evidencia «%s» no existe." % (sc, t))
            elif t in FAMILIAS and pruebas.get(t) != "performed":
                err("evidence_type_not_performed", sc,
                    "SC %s cita evidencia de %s pero esa prueba figura como not_performed." % (sc, FAMILIA_ES[t]))
        if resultado == "fail":
            faltan = [k for k, v in (("location", f.get("location")), ("evidence", f.get("evidence")), ("fix", f.get("fix"))) if _vacio(v)]
            if faltan:
                err("incomplete_fail", sc, "SC %s fallido sin %s." % (sc, ", ".join(faltan)))
        elif resultado == "pass":
            if _vacio(f.get("evidence")) or not tipos:
                err("pass_without_evidence", sc, "SC %s aprobado sin evidencia: hace falta evidence y evidence_types." % sc)
            for fam in indice[sc]["requires"]:
                if pruebas.get(fam) != "performed":
                    err("pass_without_test", sc, "SC %s no se puede aprobar: exige la prueba de %s y no se hizo." % (sc, FAMILIA_ES[fam]))
                elif fam not in tipos:
                    err("pass_without_evidence_of_test", sc, "SC %s exige evidencia de %s y la fila no la cita." % (sc, FAMILIA_ES[fam]))
        else:
            if _vacio(f.get("reason")):
                err("missing_reason", sc, "SC %s: %s necesita reason." % (sc, resultado))

    for sc in sorted(exigidos - vistos, key=lambda s: [int(x) for x in s.split(".")]):
        err("missing_criterion", sc, "Falta el criterio %s %s: no se omite ninguno en silencio." % (sc, indice[sc]["name"]))

    resumen = doc.get("summary")
    if resumen is not None:
        calculado = resumir_registro(doc, datos)
        conteos = calculado["counts"]
        if not isinstance(resumen, dict) or any(resumen.get(r) != conteos[r] for r in RESULTADOS):
            err("summary_mismatch", None, "El resumen no coincide con las filas: las filas dan %s." %
                ", ".join("%s %d" % (RESULTADO_ES[r], conteos[r]) for r in RESULTADOS))
        elif "fail_by_level" in resumen and resumen["fail_by_level"] != calculado["fail_by_level"]:
            # el error de decir «13 de nivel A y 12 de AA» cuando las filas dan 14 y 11
            err("summary_mismatch", None, "Los fallidos por nivel del resumen no coinciden con las filas: las filas dan A %d · AA %d · AAA %d." %
                (calculado["fail_by_level"]["A"], calculado["fail_by_level"]["AA"], calculado["fail_by_level"]["AAA"]))
    return errores


# -- salida --------------------------------------------------------------------------------------

def _imprimir(texto):
    sys.stdout.write(texto if texto.endswith("\n") else texto + "\n")


def _pruebas_de(ids, indice):
    pedidas = set()
    for sc in ids:
        if sc in indice:
            pedidas.update(indice[sc]["requires"])
    return [FAMILIA_ES[f] for f in FAMILIAS if f in pedidas]


def _linea_de_criterio(c):
    marcas = []
    if c["new_in_22"]:
        marcas.append("nuevo en 2.2")
    if c["interference"]:
        marcas.append("no interferencia")
    if c["scope"] == "page_set":
        marcas.append("conjunto de páginas")
    return "%-7s %-3s %s%s" % (c["id"], c["level"], c["name"], ("  [" + ", ".join(marcas) + "]") if marcas else "")


def cmd_count(args):
    datos = cargar_criterios()
    c = conteo(datos)
    if args.json:
        _imprimir(json.dumps(c, ensure_ascii=False))
        return 0
    n = c["by_level"]
    _imprimir("WCAG 2.2 tiene %d criterios de éxito: A %d · AA %d · AAA %d." % (c["total"], n["A"], n["AA"], n["AAA"]))
    _imprimir("Retirado en 2.2 y sin nivel: %s (Parsing). El objetivo AA son A + AA: %d criterios." % (", ".join(c["removed"]), n["A"] + n["AA"]))
    return 0


def cmd_criterion(args):
    datos = cargar_criterios()
    indice = indice_criterios(datos)
    codigo = 0
    for sc in args.ids:
        if sc in {r["id"] for r in datos["removed"]}:
            r = datos["removed"][0]
            _imprimir("SC %s %s — retirado en WCAG 2.2: no tiene nivel ni requisitos." % (sc, r["name"]))
            _imprimir("El W3C recomienda darlo por satisfecho en contenido HTML y XML. Los defectos de marcado con efecto en la persona usuaria se informan en %s." %
                      " o ".join(r["route_to"]))
            continue
        if sc not in indice:
            sys.stderr.write("No existe el criterio %s en WCAG 2.2 (son %d; `wcag.py list` los muestra).\n" % (sc, len(indice)))
            codigo = 2
            continue
        c = indice[sc]
        if args.json:
            _imprimir(json.dumps(dict(c, text=None if args.brief else texto_de_criterio(sc, datos)), ensure_ascii=False))
            continue
        _imprimir("SC %s %s — nivel %s%s · principio %s, pauta %s" % (
            sc, c["name"], c["level"], " · nuevo en 2.2" if c["new_in_22"] else "", c["principle"], c["guideline"]))
        pruebas = _pruebas_de([sc], indice)
        _imprimir("Para registrarlo como aprobado el harness exige: %s (regla propia del harness)." %
                  (", ".join(pruebas) if pruebas else "evidencia de revisión; ninguna prueba manual en particular"))
        if not args.brief:
            _imprimir("")
            _imprimir(texto_de_criterio(sc, datos) or "(sin texto en references/wcag22)")
    return codigo


def cmd_list(args):
    datos = cargar_criterios()
    filas = datos["criteria"]
    if args.level:
        filas = [c for c in filas if c["level"] == args.level]
    if args.up_to:
        filas = [c for c in filas if RANGO[c["level"]] <= RANGO[args.up_to]]
    if args.new:
        filas = [c for c in filas if c["new_in_22"]]
    if args.principle:
        filas = [c for c in filas if c["principle"] == args.principle]
    if args.json:
        _imprimir(json.dumps(filas, ensure_ascii=False))
        return 0
    for c in filas:
        _imprimir(_linea_de_criterio(c))
    _imprimir("— %d criterios" % len(filas))
    return 0


def cmd_task(args):
    datos = cargar_criterios()
    indice = indice_criterios(datos)
    tareas = datos["tasks"]
    if not args.name:
        for k, t in tareas.items():
            _imprimir("%-20s %s" % (k, t["title"]))
        return 0
    if args.name not in tareas:
        sys.stderr.write("No existe la tarea «%s». Hay: %s.\n" % (args.name, ", ".join(tareas)))
        return 2
    t = tareas[args.name]
    if args.json:
        _imprimir(json.dumps(t, ensure_ascii=False))
        return 0
    guia = ("references/" + t["guide"]) if "guide" in t else "skills/%s/SKILL.md" % t["skill"]
    _imprimir("%s — %s" % (args.name, t["title"]))
    _imprimir("Guía: %s" % guia)
    _imprimir("Criterios A/AA:")
    for sc in t["criteria"]:
        _imprimir("  " + _linea_de_criterio(indice[sc]))
    if t["additional_aaa"]:
        _imprimir("AAA adicionales que pide Obelisco (no son parte de AA):")
        for sc in t["additional_aaa"]:
            _imprimir("  " + _linea_de_criterio(indice[sc]))
    pruebas = _pruebas_de(t["criteria"], indice)
    _imprimir("Pruebas manuales que esos criterios piden: %s." % (", ".join(pruebas) if pruebas else "ninguna"))
    return 0


def cmd_component(args):
    datos = cargar_criterios()
    indice = indice_criterios(datos)
    matriz = cargar_matriz()
    filas = {c["id"]: c for c in matriz["components"]}
    filas["custom"] = matriz["custom"]
    if not args.id:
        for k, c in filas.items():
            _imprimir("%-16s %s" % (k, c["name"]))
        return 0
    if args.id not in filas:
        sys.stderr.write("No existe el componente «%s». `wcag.py component` los lista.\n" % args.id)
        return 2
    c = filas[args.id]
    if args.json:
        _imprimir(json.dumps(c, ensure_ascii=False))
        return 0
    _imprimir("%s (%s)" % (c["name"], c["id"]))
    if c.get("obelisco_page"):
        _imprimir("Obelisco: %s · consultada %s%s" % (c["obelisco_page"], c["obelisco_consulted"],
                  "" if c.get("obelisco_accessibility_documented", True) else " · SIN sección de accesibilidad publicada"))
    declarados = c.get("declared", [])
    if declarados:
        _imprimir("Criterios que Obelisco declara:")
        for d in declarados:
            real = indice[d["sc"]]
            nota = "" if d["declared_level"] in (None, real["level"]) else " ⚠ Obelisco dice %s" % d["declared_level"]
            aaa = "  ← AAA: adicional, no es parte de AA" if real["level"] == "AAA" else ""
            _imprimir("  %s %s (%s)%s%s" % (d["sc"], real["name"], real["level"], nota, aaa))
    _imprimir("Requisitos (el origen dice de quién es cada uno):")
    todos = [d["sc"] for d in declarados]
    for r in c["requirements"]:
        todos.extend(r["sc"])
        sc = (" [" + ", ".join(r["sc"]) + "]") if r["sc"] else ""
        _imprimir("  [%s]%s %s" % (r["origin"], sc, r["text"]))
        if r.get("quote_es"):
            _imprimir("      «%s»" % r["quote_es"])
    v = c["verification"]
    _imprimir("Verificación:")
    _imprimir("  pruebas manuales: %s" % (", ".join(FAMILIA_ES[f] for f in v["manual"]) or "ninguna"))
    _imprimir("  reglas estáticas que cubren una parte: %s" % (", ".join(v["static"]) or "ninguna"))
    for n in c.get("notes", []):
        _imprimir("Nota: " + n)
    return 0


def cmd_term(args):
    texto = texto_de_termino(args.word)
    if not texto:
        sys.stderr.write("El glosario no tiene «%s».\n" % args.word)
        return 2
    _imprimir(texto)
    return 0


def cmd_levels(args):
    datos = cargar_criterios()
    total, codigo = 0, 0
    for archivo in args.files:
        ruta = Path(archivo)
        try:
            texto = ruta.read_text(encoding="utf-8-sig")
        except OSError as e:
            sys.stderr.write("No se pudo leer %s: %s\n" % (archivo, e))
            return 2
        for p in comprobar_niveles(texto, str(archivo), datos):
            total += 1
            codigo = 1
            _imprimir("%s:%d  %s  %s" % (p["file"], p["line"], p["code"], p["message"]))
    if not total:
        _imprimir("Ningún par criterio/nivel mal escrito en %d archivo(s)." % len(args.files))
    return codigo


def cmd_register(args):
    datos = cargar_criterios()
    if args.action == "template":
        adicionales = [a for a in (args.additional or "").split(",") if a]
        componentes = [c for c in (args.components or "").split(",") if c]
        doc = plantilla_de_registro(args.level, adicionales, componentes, datos)
        texto = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as f:      # Path.write_text(newline=) es de 3.10
                f.write(texto)
            _imprimir("Registro escrito en %s: %d criterios, todos «no probado»." % (args.out, len(doc["criteria"])))
        else:
            sys.stdout.write(texto)
        return 0
    try:
        doc = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.stderr.write("No se pudo leer el registro: %s\n" % e)
        return 2
    errores = validar_registro(doc, datos)
    if args.json:
        salida = {"valid": not errores, "errors": errores}
        if not errores:
            salida.update(resumir_registro(doc, datos))
        _imprimir(json.dumps(salida, ensure_ascii=False))
        return 1 if errores else 0
    if errores:
        for e in errores:
            _imprimir("%s  %s" % (e["code"], e["message"]))
        _imprimir("Registro inválido: %d problema(s)." % len(errores))
        return 1
    resumen = resumir_registro(doc, datos)
    conteos, extra = resumen["counts"], resumen["extra"]
    _imprimir("Registro válido: %d criterios (%s)." % (sum(conteos.values()), " · ".join("%s %d" % (RESULTADO_ES[r], conteos[r]) for r in RESULTADOS)))
    if sum(extra.values()):
        _imprimir("Además, %d criterio(s) que el objetivo no exige, contados aparte (%s)." % (
            sum(extra.values()), " · ".join("%s %d" % (RESULTADO_ES[r], extra[r]) for r in RESULTADOS if extra[r])))
    pendientes = [FAMILIA_ES[f] for f in FAMILIAS if doc["tests"].get(f) != "performed"]
    if pendientes:
        _imprimir("Pruebas manuales no realizadas: %s. Un análisis estático limpio no acredita conformidad." % ", ".join(pendientes))
    return 0


def armar_parser():
    p = argparse.ArgumentParser(prog="wcag.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("count")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("criterion")
    s.add_argument("ids", nargs="+")
    s.add_argument("--brief", action="store_true")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("list")
    s.add_argument("--level", choices=list(RANGO))
    s.add_argument("--up-to", dest="up_to", choices=list(RANGO))
    s.add_argument("--new", action="store_true")
    s.add_argument("--principle", choices=["perceivable", "operable", "understandable", "robust"])
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("task")
    s.add_argument("name", nargs="?")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("component")
    s.add_argument("id", nargs="?")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("term")
    s.add_argument("word")
    s = sub.add_parser("levels")
    s.add_argument("files", nargs="+")
    s = sub.add_parser("register")
    s.add_argument("action", choices=["template", "validate"])
    s.add_argument("file", nargs="?")
    s.add_argument("--level", choices=list(RANGO), default="AA")
    s.add_argument("--additional", default="")
    s.add_argument("--components", default="")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    return p


COMANDOS = {"count": cmd_count, "criterion": cmd_criterion, "list": cmd_list, "task": cmd_task,
            "component": cmd_component, "term": cmd_term, "levels": cmd_levels, "register": cmd_register}


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            try:
                flujo.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    parser = armar_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    if args.cmd == "register" and args.action == "validate" and not args.file:
        sys.stderr.write("register validate necesita el archivo del registro.\n")
        return 2
    try:
        return COMANDOS[args.cmd](args)
    except (OSError, ValueError, KeyError) as e:
        sys.stderr.write("No se pudo completar: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
