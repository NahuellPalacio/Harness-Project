"""`security-status.md` y `security-status.html`, generados del resumen y de nada mas.

    security-summary.json  ->  security-status.md
                           ->  security-status.html   (el PDF sale de imprimir esta pagina)

🔴 **Este modulo no calcula ningun estado.** No importa `seguridad`, `evaluacion`, `integridad`,
`frescura` ni el libro: lee el diccionario del resumen y lo muestra. Cada valor del HTML lleva
`data-field="<ruta en el resumen>"`, y un test compara lo que dice la pagina contra lo que dice el
resumen. Si un numero de la pagina no esta en el resumen, no tiene de donde salir.

La unica ruta derivada es `<ruta>.length`: la cantidad de elementos de la lista que esta en
`<ruta>`. La usan la tarjeta y la fila de "Condiciones de bloqueo" (`blockingConditions.length`).
No es una clave del resumen -el resumen no guarda ningun numero global, E-07- sino una regla de
presentacion declarada, y el test la resuelve por su cuenta.

🔴 **Escribe y no lee.** No hay una funcion que abra un `.md` o un `.html`: recuperar estado de un
reporte es como una cifra formateada para una tabla se vuelve el dato.

En espanol, por ADR-0011: lo lee una persona. Los valores de estado -`BLOCKED`, `PASS`- son
identificadores de contrato y no se traducen.

Solo stdlib. El HTML es autocontenido -sin fuentes, scripts ni imagenes de afuera- y trae CSS de
impresion: el harness no tiene generador de PDF, y sumarle uno romperia la regla de dependencias.
"""
import os

from . import archivo

LIBRO = archivo.LIBRO
RESUMEN = "security-summary.json"
REPORTE_MD = "security-status.md"
REPORTE_HTML = "security-status.html"

# El contrato de renderizado, `security-report/1.0`. El PDF es la impresion del HTML.
CONTRATO = {
    "schema_version": "security-report/1.0",
    "summaryRef": RESUMEN,
    "markdownOutput": REPORTE_MD,
    "pdfOutput": REPORTE_HTML,
    "dashboard": {
        "primaryCards": ["systemSecurityState", "blockingConditions", "coverage",
                         "officialApprovalStatus"],
        "showRuleHeatmap": True,
        "showFindingsChart": True,
        "showCoverage": True,
        "showBlockers": True,
    },
}

DESCONOCIDO = "desconocido"
SIN_DENOMINADOR = "N/D"
EXTERNA = "EXTERNAL_APPROVAL_EVIDENCED"
MAXIMO_EN_PAGINA_1 = 5

AVISO_OFICIAL = ("La revisión interna del harness no es aprobación oficial de GCBA/DGSEI.")

SEVERIDADES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNRESOLVED")

# La grilla de la pagina 1, en el orden del estandar. Es disposicion, no normativa.
GRILLA = (("O1", "O2"), ("C1", "C2", "C3"), ("Vu1", "Vu2", "Vu3", "Vu4", "Vu5"),
          ("Vu6", "Vu7", "Vu8", "Vu9", "Vu10"), ("Ve1", "Ve2"), ("G1", "G2", "G3", "G4"))

ESTADO_DEL_SISTEMA = {
    "BLOCKED": "El resultado no se puede tomar como base: hay una condición que impide confiar "
               "en él. Se resuelve antes que cualquier otra cosa.",
    "REVIEW_INCOMPLETE": "Quedan reglas aplicables sin evaluar o sin resolver, o evidencia "
                         "necesaria sin verificar. Lo que falló igual figura en los bloqueos.",
    "ACTION_REQUIRED": "La revisión alcanza para establecer condiciones que hay que corregir.",
    "READY_FOR_SECURITY_REVIEW": "La revisión interna no dejó bloqueos. Está lista para pedir "
                                 "la revisión de seguridad; no es una aprobación.",
}

INTEGRIDAD = {
    "NO_SUSPICIOUS_INDICATORS_DETECTED":
        "No se detectaron indicadores sospechosos en lo que se revisó. Es el resultado de esa "
        "revisión, no una garantía sobre el repositorio.",
    "SUSPICIOUS_BEHAVIOR_DETECTED":
        "Se detectaron indicadores sospechosos. Un indicador no prueba intención: hace falta "
        "revisión humana.",
    "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE":
        "Hay comportamiento malicioso confirmado por evidencia. Preservar antes de cambiar.",
    "REVIEW_INCOMPLETE":
        "La revisión de integridad no cubrió todo lo que tenía que cubrir.",
    "TRUSTED_BASELINE_UNRESOLVED":
        "No hay línea de base confiable: lo que se concluya es parcial.",
    "NOT_EVALUATED":
        "No hay revisión de integridad en el libro. No cambia el estado del sistema: la "
        "integridad es una capacidad, no una regla.",
}


# -- valores -------------------------------------------------------------------

def valor_en(resumen, ruta):
    """El valor de una ruta `a.b[3].c` del resumen. `<ruta>.length` es el largo de esa lista."""
    actual = resumen
    for parte in ruta.replace("[", ".[").split("."):
        if not parte:
            continue
        if parte == "length" and isinstance(actual, list):
            actual = len(actual)
        elif parte.startswith("["):
            actual = actual[int(parte[1:-1])]
        else:
            actual = actual.get(parte) if isinstance(actual, dict) else None
    return actual


def texto(valor):
    """Como se muestra un valor. Lo ausente se dice: `desconocido`, nunca vacio."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return DESCONOCIDO
    if valor is True:
        return "sí"
    if valor is False:
        return "no"
    if isinstance(valor, list):
        return ", ".join(texto(v) for v in valor) if valor else "ninguna"
    return str(valor)


def porciento(valor):
    """Sin denominador es `N/D`. Nunca `100%` ni `0%` por defecto."""
    if valor is None:
        return SIN_DENOMINADOR
    return "%.1f%%" % float(valor)


def _escapar(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def _es_porcentaje(ruta):
    return ruta.endswith("Pct")


def mostrado(resumen, ruta):
    """El texto que la pagina muestra para una ruta. Uno solo, para md y html."""
    valor = valor_en(resumen, ruta)
    return porciento(valor) if _es_porcentaje(ruta) else texto(valor)


def _aviso(resumen):
    return resumen.get("officialApprovalStatus") != EXTERNA


def _indices(resumen):
    return dict((f.get("rule"), i) for i, f in enumerate(resumen["normative"]["rules"]))


# -- el Markdown ---------------------------------------------------------------

EJECUTIVA = (
    ("Estado de seguridad del sistema", "systemSecurityState"),
    ("Condiciones de bloqueo", "blockingConditions.length"),
    ("Cobertura de la evaluación", "coverage.assessmentCoveragePct"),
    ("Resolución de la evidencia", "coverage.evidenceResolutionPct"),
    ("Aprobación oficial", "officialApprovalStatus"),
    ("Estado de la evaluación", "assessmentState"),
    ("Hallazgos críticos", "findings.totalsBySeverity.CRITICAL"),
    ("Hallazgos altos", "findings.totalsBySeverity.HIGH"),
    ("Frescura del conocimiento", "knowledge.freshness"),
)

ALCANCE = (("Proyecto", "project"), ("Aplicación", "application"), ("Ambiente", "environment"),
           ("Rama", "branch"), ("Commit", "commitSha"), ("Build", "buildId"),
           ("Release", "releaseId"), ("Digest del artefacto", "artifactDigest"))

EJECUCION = (("Eventos contados", "events.counted"), ("Tiempo de pared (ms)", "time.wallMs"),
             ("Tiempo de modelo (ms)", "time.modelMs"), ("Tiempo de tools (ms)", "time.toolMs"),
             ("Tokens de input", "tokens.inputTokens"),
             ("Tokens de output", "tokens.outputTokens"), ("Costo real", "cost.actual"),
             ("Equivalente de API estimado", "cost.apiEquivalentEstimated"),
             ("Moneda", "cost.currency"))

EVIDENCIA = (("Verificada", "verified"), ("Faltante", "missing"), ("En conflicto", "conflicting"),
             ("Pruebas inseguras salteadas", "unsafeTestsSkipped"), ("Sin resolver", "unresolved"))


def _tabla(filas, encabezado):
    lineas = ["| %s |" % " | ".join(encabezado), "|%s|" % "|".join("---" for _ in encabezado)]
    for fila in filas:
        lineas.append("| %s |" % " | ".join(_md(c) for c in fila))
    return "\n".join(lineas)


def _md_bloqueos(resumen):
    bloqueos = resumen["blockingConditions"]
    if not bloqueos:
        return "_No hay condiciones de bloqueo._"
    return _tabla([(b["blockerId"], b["source"], b["title"], b["state"], texto(b.get("effect")),
                    texto(b.get("evidenceRefs"))) for b in bloqueos],
                  ("Id", "Origen", "Condición", "Estado", "Empuja a", "Evidencia"))


def _md_reglas(resumen):
    return _tabla([(f["ruleKey"], f["result"], texto(f.get("sourceResult")),
                    texto(f.get("domainId")), texto(f.get("evidenceRefs")))
                   for f in resumen["normative"]["rules"]],
                  ("Regla", "Resultado", "Resultado del motor", "Dominio", "Evidencia"))


def _md_hallazgos(resumen):
    h = resumen["findings"]
    partes = [_tabla([(s, str(h["totalsBySeverity"].get(s, 0))) for s in SEVERIDADES],
                     ("Severidad (vigentes)", "Cantidad")),
              "",
              _tabla([("Abiertos", h["open"]), ("Reabiertos", h["reopened"]),
                      ("Sin resolver", h["unresolved"]), ("Resueltos", h["resolved"])],
                     ("Estado", "Cantidad")),
              "",
              "La severidad y la confianza son dos ejes y ninguno se deduce del otro."]
    return "\n".join(partes)


def _md_detalle(resumen):
    items = resumen["findings"]["items"]
    if not items:
        return "_No hay hallazgos en el libro._"
    return _tabla([(i["findingId"], i["state"], i["severity"], texto(i.get("confidence")),
                    texto(i.get("rule")), texto(i.get("title")), texto(i.get("blocking")),
                    texto(i.get("evidenceRefs"))) for i in items],
                  ("Hallazgo", "Estado", "Severidad", "Confianza", "Regla", "Título",
                   "Bloquea", "Evidencia"))


def _md_dominios(resumen):
    partes = []
    for d in resumen.get("domains") or []:
        partes.append("### %s" % d["title"])
        partes.append("")
        partes.append(_tabla([(r["ruleKey"], r["result"]) for r in d["rules"]],
                             ("Regla", "Resultado")))
        partes.append("")
    partes.append("Los dominios agrupan reglas para leerlas; no son reglas nuevas.")
    return "\n".join(partes)


def _md_integridad(resumen):
    i = resumen["repositoryIntegrity"] or {}
    estado = i.get("state") or "NOT_EVALUATED"
    return "\n".join([
        _tabla([("Estado", estado), ("Modo", texto(i.get("mode"))),
                ("Línea de base confiable", texto(i.get("trustedBaseline"))),
                ("Hallazgos sospechosos", texto(i.get("suspiciousFindings"))),
                ("Malicioso confirmado por evidencia", texto(i.get("confirmedMalicious"))),
                ("Revisión", texto(i.get("reviewId")))], ("Campo", "Valor")),
        "",
        INTEGRIDAD.get(estado, "")])


def _md_evaluacion(resumen):
    a = resumen.get("assessment") or {}
    return _tabla([("Estado de la evaluación", resumen["assessmentState"]),
                   ("Aprobación oficial", resumen["officialApprovalStatus"]),
                   ("Estado del flujo declarado", texto(a.get("workflowState"))),
                   ("Declarado por", texto(a.get("declaredBy"))),
                   ("Umbral de G2 satisfecho", texto(a.get("g2Satisfied"))),
                   ("Estado del check de C2", texto(a.get("c2State"))),
                   ("Reevaluación requerida", texto(a.get("reassessmentRequired")))],
                  ("Campo", "Valor"))


def _md_evidencia(resumen):
    e = resumen["evidence"]
    partes = [_tabla([(nombre, e[campo]) for nombre, campo in EVIDENCIA], ("Evidencia", "Cantidad"))]
    if e.get("material"):
        partes += ["", "Evidencia necesaria sin verificar: %s."
                   % ", ".join("%s (%s)" % (m["evidenceRef"], m["result"]) for m in e["material"])]
    return "\n".join(partes)


def _md_ejecucion(resumen):
    valores = resumen.get("block4Execution") or {}
    return "\n".join([
        "Referencia: `%s`. Los valores se copian tal cual del resumen del Bloque 4, que es el "
        "dueño de tiempos, tokens y costos." % resumen["block4ExecutionRef"],
        "",
        _tabla([(nombre, texto(valor_en(valores, ruta))) for nombre, ruta in EJECUCION],
               ("Métrica", "Valor"))])


def _conclusion(resumen):
    estado = resumen["systemSecurityState"]
    lineas = ["Estado del sistema: **%s**. %s" % (estado, ESTADO_DEL_SISTEMA.get(estado, ""))]
    incompleto = resumen.get("reviewIncomplete") or {}
    if incompleto.get("rules"):
        lineas.append("- Reglas aplicables sin evaluar o sin resolver: %s."
                      % ", ".join(incompleto["rules"]))
    if incompleto.get("materialEvidence"):
        lineas.append("- Evidencia necesaria sin verificar: %s."
                      % ", ".join(incompleto["materialEvidence"]))
    if incompleto.get("repositoryIntegrity"):
        lineas.append("- La revisión de integridad del repositorio quedó incompleta.")
    if resumen["blockingConditions"]:
        lineas.append("- Condiciones de bloqueo abiertas: %d." % len(resumen["blockingConditions"]))
    return "\n".join(lineas)


def generar_md(resumen):
    """El Markdown entero, como texto. Todo valor sale del resumen."""
    k = resumen.get("knowledge") or {}
    alcance = resumen.get("scope") or {}
    partes = [
        "# Reporte de estado de seguridad — %s" % texto(resumen.get("taskId")),
        "",
        "> Generado de forma determinista a partir de `%s`. Este Markdown es un reporte, no la "
        "fuente: la fuente es el libro." % RESUMEN,
        "",
        "## Resumen ejecutivo",
        "",
        _tabla([(nombre, mostrado(resumen, ruta)) for nombre, ruta in EJECUTIVA],
               ("Métrica", "Valor")),
        "",
        ESTADO_DEL_SISTEMA.get(resumen["systemSecurityState"], ""),
        "",
        "## Alcance",
        "",
    ]
    for nombre, campo in ALCANCE:
        partes.append("- %s: %s" % (nombre, texto(alcance.get(campo))))
    partes += [
        "- Generado: %s" % texto(resumen.get("generatedAt")),
        "- %s: versión %s" % (texto(k.get("standard")), texto(k.get("version"))),
        "- Id del reporte: `%s`" % resumen["reportId"],
        "- Huella de la foto: `%s`" % resumen["snapshotFingerprint"],
        "",
        "## Conocimiento normativo",
        "",
        _tabla([("Estándar", texto(k.get("standard"))), ("Versión", texto(k.get("version"))),
                ("Frescura", texto(k.get("freshness"))),
                ("Integridad de la fuente", texto(k.get("sourceIntegrity")))],
               ("Campo", "Valor")),
        "",
    ]
    if k.get("blocking"):
        partes += ["> El conocimiento normativo con que se evaluó no está verificado como "
                   "vigente. Mientras sea así, el estado del sistema no puede ser "
                   "`READY_FOR_SECURITY_REVIEW`.", ""]
    partes += [
        "## Condiciones de bloqueo",
        "",
        _md_bloqueos(resumen),
        "",
        "## Cumplimiento normativo",
        "",
        _md_reglas(resumen),
        "",
        "Cobertura: %d aplicables, %d intentadas, %d resueltas. Una regla sin evaluar suma al "
        "denominador; una que no aplica, no." % (
            resumen["coverage"]["applicableRules"], resumen["coverage"]["attemptedRules"],
            resumen["coverage"]["resolvedRules"]),
        "",
        "## Hallazgos",
        "",
        _md_hallazgos(resumen),
        "",
        "## Dominios",
        "",
        _md_dominios(resumen),
        "",
        "## Integridad del repositorio",
        "",
        _md_integridad(resumen),
        "",
        "## Evaluación y aprobación",
        "",
        _md_evaluacion(resumen),
        "",
        "## Completitud de la evidencia",
        "",
        _md_evidencia(resumen),
        "",
    ]
    if resumen.get("block4ExecutionRef"):
        partes += ["## Ejecución", "", _md_ejecucion(resumen), ""]
    partes += [
        "## Hallazgos en detalle",
        "",
        _md_detalle(resumen),
        "",
        "## Conclusión",
        "",
        _conclusion(resumen),
        "",
    ]
    if _aviso(resumen):
        partes += ["> %s" % AVISO_OFICIAL, ""]
    return "\n".join(partes)


# -- el HTML -------------------------------------------------------------------

CSS = """
*{box-sizing:border-box}
body{font-family:Arial,Helvetica,sans-serif;background:#eef1f5;margin:0;padding:24px;color:#17202a}
.pagina{width:1180px;max-width:100%;min-height:760px;background:#fff;margin:0 auto 24px;padding:32px;box-shadow:0 4px 22px rgba(0,0,0,.12)}
.cabecera{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #1f2d3d;padding-bottom:14px}
.h1{font-size:28px;font-weight:700}.meta{font-size:12px;text-align:right;line-height:1.55;color:#53606d}
.tarjetas{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}
.tarjeta{border:1px solid #d5dbe3;border-radius:8px;padding:14px;min-height:78px}
.primaria{border-width:2px;border-color:#1f2d3d}
.rotulo{font-size:11px;font-weight:700;letter-spacing:.06em;color:#66717d;text-transform:uppercase}
.valor{font-size:21px;font-weight:700;margin-top:8px;word-break:break-word}
.sub{font-size:12px;color:#53606d;margin-top:4px}
.dos{display:grid;grid-template-columns:1.35fr .95fr;gap:16px;margin-top:16px}
.panel{border:1px solid #d5dbe3;border-radius:8px;padding:16px}
.panel h3{margin:0 0 12px;font-size:15px}
.fila-grilla{display:flex;gap:8px;margin-bottom:8px}
.regla{flex:1;padding:8px 4px;border-radius:6px;background:#f3f5f7;text-align:center;font-size:11px;border:1px solid #e0e4e8}
.regla b{display:block;font-size:13px}
.r-FAIL{border-left:6px solid #222;background:#e4e6e9}
.r-UNRESOLVED{border-left:6px dashed #666}
.r-PASS{border-left:6px solid #b5bcc4}
.r-NOT_EVALUATED{border-left:6px dotted #999;color:#555}
.r-NOT_APPLICABLE{color:#8a939c;background:#fafbfc}
.barra{height:12px;background:#eceff3;border-radius:6px;margin:6px 0 14px;overflow:hidden}
.relleno{height:100%;background:#596675}
.linea{display:flex;justify-content:space-between;font-size:13px;margin:6px 0}
.bloqueo{border-left:5px solid #444;background:#f6f7f8;padding:8px 12px;margin:6px 0;font-size:13px}
.mas{font-size:13px;font-weight:700;margin-top:6px}
.nota{font-size:12px;color:#53606d;margin-top:8px}
.aviso{border:2px solid #1f2d3d;padding:8px 12px;margin-top:10px;font-weight:700;font-size:13px}
.pie{margin-top:16px;font-size:11px;color:#6b7680;border-top:1px solid #dde2e7;padding-top:10px}
table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}
th,td{border:1px solid #d5dbe3;padding:5px 7px;text-align:left;vertical-align:top}
th{background:#f3f5f7}
h2{font-size:19px;border-bottom:1px solid #d5dbe3;padding-bottom:6px}
code{font-size:11px;word-break:break-all}
@page{size:A4 landscape;margin:10mm}
@media print{
  body{background:#fff;padding:0}
  .pagina{box-shadow:none;margin:0;width:auto;min-height:0;page-break-after:always;break-after:page}
  .pagina:last-child{page-break-after:auto;break-after:auto}
}
"""


def _campo(ruta, contenido, etiqueta="span", clase=""):
    return '<%s%s data-field="%s">%s</%s>' % (
        etiqueta, (' class="%s"' % clase) if clase else "", _escapar(ruta),
        _escapar(contenido), etiqueta)


def _f(resumen, ruta, etiqueta="span", clase=""):
    return _campo(ruta, mostrado(resumen, ruta), etiqueta, clase)


def _tarjeta(clave, rotulo, cuerpo, primaria=False):
    return ('<div class="tarjeta%s" data-card="%s"><div class="rotulo">%s</div>%s</div>'
            % (" primaria" if primaria else "", _escapar(clave), _escapar(rotulo), cuerpo))


def _html_tabla(encabezado, filas):
    salida = ["<table><tr>%s</tr>" % "".join("<th>%s</th>" % _escapar(c) for c in encabezado)]
    for fila in filas:
        salida.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in fila))
    salida.append("</table>")
    return "".join(salida)


def _barra(pct):
    ancho = 0.0 if pct is None else max(0.0, min(100.0, float(pct)))
    return '<div class="barra"><div class="relleno" style="width:%.1f%%"></div></div>' % ancho


def _cabecera(resumen):
    k = "knowledge"
    return "".join([
        '<div class="cabecera"><div><div class="h1">REPORTE DE ESTADO DE SEGURIDAD</div>',
        "<div>", _f(resumen, "scope.project"), " · ", _f(resumen, "scope.application"), " · ",
        _f(resumen, "scope.environment"), "</div></div>",
        '<div class="meta">', _f(resumen, k + ".standard"), " v", _f(resumen, k + ".version"),
        " · frescura ", _f(resumen, k + ".freshness"), " · integridad ",
        _f(resumen, k + ".sourceIntegrity"), "<br/>commit ", _f(resumen, "scope.commitSha"),
        " · release ", _f(resumen, "scope.releaseId"), "<br/>generado ",
        _f(resumen, "generatedAt"), "</div></div>"])


def _primarias(resumen):
    return "".join([
        '<div class="tarjetas">',
        _tarjeta("systemSecurityState", "Estado de seguridad del sistema",
                 _f(resumen, "systemSecurityState", "div", "valor"), True),
        _tarjeta("blockingConditions", "Condiciones de bloqueo",
                 _f(resumen, "blockingConditions.length", "div", "valor"), True),
        _tarjeta("coverage", "Cobertura normativa",
                 _f(resumen, "coverage.assessmentCoveragePct", "div", "valor")
                 + '<div class="sub">evaluada · resuelta '
                 + _f(resumen, "coverage.evidenceResolutionPct") + "</div>", True),
        _tarjeta("officialApprovalStatus", "Aprobación oficial",
                 _f(resumen, "officialApprovalStatus", "div", "valor"), True),
        "</div>"])


def _secundarias(resumen):
    return "".join([
        '<div class="tarjetas">',
        _tarjeta("findings", "Hallazgos críticos / altos",
                 '<div class="valor">' + _f(resumen, "findings.totalsBySeverity.CRITICAL")
                 + " / " + _f(resumen, "findings.totalsBySeverity.HIGH") + "</div>"),
        _tarjeta("unresolvedRules", "Reglas sin resolver / sin evaluar",
                 '<div class="valor">' + _f(resumen, "coverage.unresolvedRules") + " / "
                 + _f(resumen, "coverage.notEvaluatedRules") + "</div>"),
        _tarjeta("evidenceResolution", "Resolución de la evidencia",
                 _f(resumen, "coverage.evidenceResolutionPct", "div", "valor")),
        _tarjeta("assessmentState", "Estado de la evaluación",
                 _f(resumen, "assessmentState", "div", "valor")),
        "</div>"])


def _grilla(resumen):
    indices = _indices(resumen)
    reglas = resumen["normative"]["rules"]
    filas, vistas = [], set()
    for grupo in GRILLA:
        celdas = []
        for rid in grupo:
            if rid not in indices:
                continue
            vistas.add(rid)
            i = indices[rid]
            ruta = "normative.rules[%d].result" % i
            celdas.append('<div class="regla r-%s" data-rule="%s"><b>%s</b>%s</div>' % (
                _escapar(reglas[i]["result"]), _escapar(rid), _escapar(rid),
                _f(resumen, ruta)))
        filas.append('<div class="fila-grilla">%s</div>' % "".join(celdas))
    sueltas = [rid for rid in indices if rid not in vistas]
    if sueltas:
        filas.append('<div class="fila-grilla">%s</div>' % "".join(
            '<div class="regla" data-rule="%s"><b>%s</b>%s</div>' % (
                _escapar(rid), _escapar(rid),
                _f(resumen, "normative.rules[%d].result" % indices[rid])) for rid in sueltas))
    return ('<div class="panel" data-panel="heatmap"><h3>Cumplimiento de %s</h3>%s</div>'
            % (_escapar(texto(resumen["normative"].get("standard"))), "".join(filas)))


def _cobertura_y_hallazgos(resumen):
    c = resumen["coverage"]
    totales = resumen["findings"]["totalsBySeverity"]
    tope = max([totales.get(s, 0) for s in SEVERIDADES] + [1])
    barras = []
    for s in SEVERIDADES:
        barras.append('<div class="linea"><span>%s</span><b>%s</b></div>%s' % (
            _escapar(s), _f(resumen, "findings.totalsBySeverity.%s" % s),
            _barra(100.0 * totales.get(s, 0) / tope)))
    return "".join([
        '<div class="panel" data-panel="coverage"><h3>Cobertura y evidencia</h3>',
        '<div class="linea"><span>Cobertura de la evaluación</span><b>',
        _f(resumen, "coverage.assessmentCoveragePct"), "</b></div>",
        _barra(c.get("assessmentCoveragePct")),
        '<div class="linea"><span>Resolución de la evidencia</span><b>',
        _f(resumen, "coverage.evidenceResolutionPct"), "</b></div>",
        _barra(c.get("evidenceResolutionPct")),
        '<div class="linea"><span>Aplicables · intentadas · resueltas</span><b>',
        _f(resumen, "coverage.applicableRules"), " · ", _f(resumen, "coverage.attemptedRules"),
        " · ", _f(resumen, "coverage.resolvedRules"), "</b></div>",
        '<div class="linea"><span>Pruebas inseguras salteadas</span><b>',
        _f(resumen, "evidence.unsafeTestsSkipped"), "</b></div>",
        '<h3 style="margin-top:14px">Hallazgos vigentes por severidad</h3>',
        '<div data-panel="findings-chart">', "".join(barras), "</div>",
        '<div class="nota">Cantidades, no un puntaje. La confianza va aparte.</div></div>'])


def _panel_bloqueos(resumen):
    bloqueos = resumen["blockingConditions"]
    if not bloqueos:
        cuerpo = '<div class="nota" data-empty="blockingConditions">No hay condiciones de bloqueo.</div>'
    else:
        items = []
        for i, b in enumerate(bloqueos[:MAXIMO_EN_PAGINA_1]):
            base = "blockingConditions[%d]" % i
            items.append('<div class="bloqueo" data-blocker="%s"><b>%s</b> · %s · %s · %s</div>'
                         % (_escapar(b["blockerId"]), _f(resumen, base + ".source"),
                            _f(resumen, base + ".title"), _f(resumen, base + ".state"),
                            _f(resumen, base + ".evidenceRefs")))
        cuerpo = "".join(items)
        if len(bloqueos) > MAXIMO_EN_PAGINA_1:
            cuerpo += '<div class="mas" data-more="%d">+%d más</div>' % (
                len(bloqueos) - MAXIMO_EN_PAGINA_1, len(bloqueos) - MAXIMO_EN_PAGINA_1)
    return ('<div class="panel" data-panel="blockers"><h3>Condiciones de bloqueo</h3>%s</div>'
            % cuerpo)


def _mini_integridad(resumen):
    r = "repositoryIntegrity"
    estado = (resumen.get(r) or {}).get("state") or "NOT_EVALUATED"
    return "".join([
        '<div class="panel" data-panel="repository-integrity"><h3>Integridad del repositorio</h3>',
        '<div class="linea"><span>Estado</span><b>', _f(resumen, r + ".state"), "</b></div>",
        '<div class="linea"><span>Línea de base confiable</span><b>',
        _f(resumen, r + ".trustedBaseline"), "</b></div>",
        '<div class="linea"><span>Hallazgos sospechosos</span><b>',
        _f(resumen, r + ".suspiciousFindings"), "</b></div>",
        '<div class="linea"><span>Malicioso confirmado</span><b>',
        _f(resumen, r + ".confirmedMalicious"), "</b></div>",
        '<div class="nota">', _escapar(INTEGRIDAD.get(estado, "")), "</div>",
        "<h3 style=\"margin-top:14px\">Evaluación</h3>",
        '<div class="linea"><span>Ambiente</span><b>', _f(resumen, "scope.environment"),
        "</b></div>",
        '<div class="linea"><span>Estado de la evaluación</span><b>',
        _f(resumen, "assessmentState"), "</b></div>",
        '<div class="linea"><span>Reevaluación requerida</span><b>',
        _f(resumen, "assessment.reassessmentRequired"), "</b></div>",
        '<div class="linea"><span>Aprobación oficial</span><b>',
        _f(resumen, "officialApprovalStatus"), "</b></div></div>"])


def _pie(resumen):
    aviso = ('<div class="aviso" data-notice="official-approval">%s</div>'
             % _escapar(AVISO_OFICIAL)) if _aviso(resumen) else ""
    return "".join(['<div class="pie">', aviso, "Reporte ", _f(resumen, "reportId"),
                    " · foto ", _f(resumen, "snapshotFingerprint"), "</div>"])


def _pagina_1(resumen):
    return "".join([
        '<section class="pagina" id="pagina-1">', _cabecera(resumen), _primarias(resumen),
        _secundarias(resumen),
        '<div class="dos">', _grilla(resumen), _cobertura_y_hallazgos(resumen), "</div>",
        '<div class="dos">', _panel_bloqueos(resumen), _mini_integridad(resumen), "</div>",
        _pie(resumen), "</section>"])


def _pagina_alcance(resumen):
    filas = [(_escapar(nombre), _f(resumen, "scope." + campo)) for nombre, campo in ALCANCE]
    filas += [("Generado", _f(resumen, "generatedAt")), ("Tarea", _f(resumen, "taskId")),
              ("Estándar", _f(resumen, "knowledge.standard")),
              ("Versión", _f(resumen, "knowledge.version")),
              ("Frescura", _f(resumen, "knowledge.freshness")),
              ("Integridad de la fuente", _f(resumen, "knowledge.sourceIntegrity")),
              ("Id del reporte", _f(resumen, "reportId")),
              ("Huella de la foto", _f(resumen, "snapshotFingerprint"))]
    partes = ['<section class="pagina" id="pagina-2"><h2>Alcance y contexto</h2>',
              _html_tabla(("Campo", "Valor"), filas)]
    if (resumen.get("knowledge") or {}).get("blocking"):
        partes.append('<div class="aviso">El conocimiento normativo con que se evaluó no está '
                      'verificado como vigente. Mientras sea así, el estado del sistema no '
                      'puede ser READY_FOR_SECURITY_REVIEW.</div>')
    if resumen.get("block4ExecutionRef"):
        filas = [(_escapar(nombre), _f(resumen, "block4Execution." + ruta))
                 for nombre, ruta in EJECUCION]
        partes.append(_tarjeta("block4Execution", "Ejecución (Bloque 4)",
                               '<div class="sub">' + _f(resumen, "block4ExecutionRef")
                               + " · los valores se copian tal cual</div>"
                               + _html_tabla(("Métrica", "Valor"), filas)))
    partes.append("</section>")
    return "".join(partes)


def _pagina_normativa(resumen):
    filas = []
    for i, f in enumerate(resumen["normative"]["rules"]):
        base = "normative.rules[%d]" % i
        filas.append((_f(resumen, base + ".ruleKey"), _f(resumen, base + ".result"),
                      _f(resumen, base + ".sourceResult"), _f(resumen, base + ".domainId"),
                      _f(resumen, base + ".evidenceRefs")))
    dominios = []
    for j, d in enumerate(resumen.get("domains") or []):
        celdas = [(_f(resumen, "domains[%d].rules[%d].ruleKey" % (j, k)),
                   _f(resumen, "domains[%d].rules[%d].result" % (j, k)))
                  for k in range(len(d["rules"]))]
        dominios.append("<h3>%s</h3>%s" % (_f(resumen, "domains[%d].title" % j),
                                          _html_tabla(("Regla", "Resultado"), celdas)))
    return "".join([
        '<section class="pagina" id="pagina-3"><h2>Cumplimiento normativo</h2>',
        _html_tabla(("Regla", "Resultado", "Resultado del motor", "Dominio", "Evidencia"), filas),
        "<h2>Dominios</h2>", "".join(dominios),
        '<div class="nota">Los dominios agrupan reglas para leerlas; no son reglas nuevas.</div>',
        "</section>"])


def _pagina_hallazgos(resumen):
    bloqueos = []
    for i, _ in enumerate(resumen["blockingConditions"]):
        base = "blockingConditions[%d]" % i
        bloqueos.append(tuple(_f(resumen, base + "." + c) for c in
                              ("blockerId", "source", "title", "state", "effect", "evidenceRefs")))
    items = []
    for i, _ in enumerate(resumen["findings"]["items"]):
        base = "findings.items[%d]" % i
        items.append(tuple(_f(resumen, base + "." + c) for c in
                           ("findingId", "state", "severity", "confidence", "rule", "title",
                            "blocking", "evidenceRefs")))
    conteo = [(_escapar(n), _f(resumen, "findings." + c)) for n, c in
              (("Abiertos", "open"), ("Reabiertos", "reopened"), ("Sin resolver", "unresolved"),
               ("Resueltos", "resolved"))]
    return "".join([
        '<section class="pagina" id="pagina-4"><h2>Condiciones de bloqueo</h2>',
        _html_tabla(("Id", "Origen", "Condición", "Estado", "Empuja a", "Evidencia"), bloqueos)
        if bloqueos else '<div class="nota">No hay condiciones de bloqueo.</div>',
        "<h2>Hallazgos</h2>", _html_tabla(("Estado", "Cantidad"), conteo),
        _html_tabla(("Hallazgo", "Estado", "Severidad", "Confianza", "Regla", "Título",
                     "Bloquea", "Evidencia"), items)
        if items else '<div class="nota">No hay hallazgos en el libro.</div>',
        "</section>"])


def _pagina_cierre(resumen):
    e = "evidence"
    evidencia = [(_escapar(n), _f(resumen, "%s.%s" % (e, c))) for n, c in EVIDENCIA]
    a = "assessment"
    evaluacion = [(_escapar(n), _f(resumen, r)) for n, r in (
        ("Estado de la evaluación", "assessmentState"),
        ("Aprobación oficial", "officialApprovalStatus"),
        ("Estado del flujo declarado", a + ".workflowState"),
        ("Declarado por", a + ".declaredBy"),
        ("Umbral de G2 satisfecho", a + ".g2Satisfied"),
        ("Estado del check de C2", a + ".c2State"),
        ("Reevaluación requerida", a + ".reassessmentRequired"))]
    conclusion = _escapar(_conclusion(resumen).replace("**", "")).replace("\n", "<br/>")
    return "".join([
        '<section class="pagina" id="pagina-5"><h2>Evaluación y aprobación</h2>',
        _html_tabla(("Campo", "Valor"), evaluacion),
        "<h2>Completitud de la evidencia</h2>", _html_tabla(("Evidencia", "Cantidad"), evidencia),
        "<h2>Conclusión</h2>", '<div data-section="conclusion">', conclusion, "</div>",
        _pie(resumen), "</section>"])


def generar_html(resumen):
    """La pagina entera, autocontenida. Todo valor sale del resumen."""
    return "".join([
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8"/>\n',
        "<title>Reporte de estado de seguridad — %s</title>\n" % _escapar(texto(
            resumen.get("taskId"))),
        "<style>", CSS, "</style>\n</head>\n<body>\n",
        _pagina_1(resumen), "\n", _pagina_alcance(resumen), "\n", _pagina_normativa(resumen),
        "\n", _pagina_hallazgos(resumen), "\n", _pagina_cierre(resumen),
        "\n</body>\n</html>\n"])


# -- escritura -----------------------------------------------------------------

def _escribir(ruta, contenido):
    """A un `.tmp` y despues encima. Nunca sobre el libro: la guarda es la de `archivo.py`."""
    return archivo.escribir_atomico(ruta, contenido, "el reporte")


def escribir(resumen, carpeta):
    """(ruta_md, ruta_html) en la carpeta de la tarea."""
    return (_escribir(os.path.join(carpeta, REPORTE_MD), generar_md(resumen)),
            _escribir(os.path.join(carpeta, REPORTE_HTML), generar_html(resumen)))
