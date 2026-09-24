"""`security-summary.json`: una funcion pura de sus cuatro entradas.

    libro + matriz + dominios + summary.json del Bloque 4 (vacio si no hay)  ->  resumen

`generatedAt` es el `timestamp` del ultimo evento, no la hora del reloj. `snapshotFingerprint` es
el sha256 de las cuatro entradas en ese orden, cada una precedida por su nombre y su largo, y
`reportId` sale de esa huella. Las claves se escriben ordenadas. Las mismas entradas dan el mismo
archivo byte a byte, y una huella que no cubriera lo que se muestra no identificaria la foto.

🔴 **El resultado de una regla sale solo de un `RULE_EVALUATION` de esa regla.** Un
`CHECK_EVALUATION` no le pone resultado a ninguna, ni a la suya ni a las que comparten el control.
No existe el camino que lo copiaria.

🔴 **Lo que no se evaluo es `NOT_EVALUATED`, y suma al denominador.** Una regla sin evento no
desaparece del tablero ni se vuelve PASS.

🔴 **No hay puntaje.** Estado, cobertura, hallazgos y bloqueos van por separado. Un numero unico
promedia una falla critica con veinte reglas en verde y la esconde.

🔴 **Tres estados que no se deducen uno de otro.** El del sistema, el de la evaluacion y el de la
aprobacion oficial se calculan cada uno de sus propios eventos. `READY_FOR_SECURITY_REVIEW` no
toca la aprobacion.
"""
import decimal
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from orquestacion import evaluacion              # noqa: E402
from orquestacion import frescura                # noqa: E402
from orquestacion import integridad              # noqa: E402
from orquestacion import roster                  # noqa: E402
from orquestacion import seguridad               # noqa: E402

from . import libro                              # noqa: E402

VERSION_SCHEMA = "security-summary/1.0"
SCHEMA = "security-summary.schema.json"
DOMINIOS = "security-report-domains.json"
SIN_EVENTOS = "UNRESOLVED"

# -- los estados del tablero ---------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
SIN_RESOLVER = "UNRESOLVED"
NO_APLICA = "NOT_APPLICABLE"
SIN_EVALUAR = "NOT_EVALUATED"
RESULTADOS = (PASA, FALLA, SIN_RESOLVER, NO_APLICA, SIN_EVALUAR)

# Del motor al tablero. `OVERRIDDEN` baja a UNRESOLVED: el tablero no tiene donde mostrar una
# excepcion, y convertirla en PASS seria copiar una aprobacion que el reporte no puede verificar.
TRADUCCION = {
    seguridad.CUMPLE: PASA,
    seguridad.NO_CUMPLE: FALLA,
    seguridad.RESULTADO_SIN_RESOLVER: SIN_RESOLVER,
    seguridad.EXCEPTUADA: SIN_RESOLVER,
    seguridad.NO_APLICABLE: NO_APLICA,
}

LISTO = "READY_FOR_SECURITY_REVIEW"
ACCION = "ACTION_REQUIRED"
INCOMPLETA = "REVIEW_INCOMPLETE"
BLOQUEADO = "BLOCKED"

# -- la evaluacion -------------------------------------------------------------

NO_PEDIDA = "NOT_REQUESTED"
LISTA_PARA_PEDIR = "READY_TO_REQUEST"
EN_CURSO = "ASSESSMENT_IN_PROGRESS"
REEVALUAR = "REASSESSMENT_REQUIRED"
LISTA_PARA_REENVIAR = "READY_TO_RESUBMIT"
UMBRAL = "G2_THRESHOLD_SATISFIED"
EXTERNA = "EXTERNAL_APPROVAL_EVIDENCED"
EVALUACION_SIN_RESOLVER = "ASSESSMENT_STATE_UNRESOLVED"

FLUJO = {
    evaluacion.NO_EMPEZADA: NO_PEDIDA,
    evaluacion.EVALUACION_INTERNA: NO_PEDIDA,
    evaluacion.LISTO_PARA_PEDIR: LISTA_PARA_PEDIR,
    evaluacion.PEDIDA: EN_CURSO,
    evaluacion.EN_EVALUACION: EN_CURSO,
    evaluacion.REENVIADA: EN_CURSO,
    evaluacion.HALLAZGOS_RECIBIDOS: REEVALUAR,
    evaluacion.REMEDIACION: REEVALUAR,
    evaluacion.RECHAZADA: REEVALUAR,
    evaluacion.LISTO_PARA_REENVIAR: LISTA_PARA_REENVIAR,
}

# -- la aprobacion oficial -----------------------------------------------------

NO_DISPONIBLE = "NOT_AVAILABLE"
APROBACION_SIN_RESOLVER = "UNRESOLVED"
VENCIDA = "EXTERNAL_APPROVAL_STALE"
C2_CAMBIADA = "SECURITY_APPROVAL_EVIDENCE_CHANGED"
C2_REEVALUAR = "SECURITY_REASSESSMENT_REQUIRED"

# -- la integridad -------------------------------------------------------------

SIN_INDICADORES = "NO_SUSPICIOUS_INDICATORS_DETECTED"
INTEGRIDAD_SIN_EVALUAR = "NOT_EVALUATED"
RENOMBRE_DE_INTEGRIDAD = {integridad.SIN_HALLAZGOS: SIN_INDICADORES}

# -- los hallazgos y la evidencia ----------------------------------------------

SEVERIDADES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNRESOLVED")
ABIERTO = "OPEN"
REABIERTO = "REOPENED"
RESUELTO = "RESOLVED"
HALLAZGO_SIN_RESOLVER = "UNRESOLVED"
VIGENTES = (ABIERTO, REABIERTO)

EVIDENCIA_MATERIAL = ("MISSING", "CONFLICTING", "UNRESOLVED", "UNSAFE_TEST_SKIPPED")
CONTADORES = (("VERIFIED", "verified"), ("MISSING", "missing"), ("CONFLICTING", "conflicting"),
              ("UNSAFE_TEST_SKIPPED", "unsafeTestsSkipped"), ("UNRESOLVED", "unresolved"))

# Lo que se copia del `summary.json` del Bloque 4, tal cual. Se referencia, no se recalcula.
EJECUCION = (("events", "counted"), ("time", "wallMs"), ("time", "modelMs"), ("time", "toolMs"),
             ("tokens", "inputTokens"), ("tokens", "outputTokens"),
             ("cost", "actual"), ("cost", "apiEquivalentEstimated"), ("cost", "currency"))

_CACHE = {}


class ResumenInvalido(ValueError):
    """El resumen no se arma a medias."""


# -- entradas ------------------------------------------------------------------

def ruta_de_matriz(desde=None):
    ruta = roster.ruta_de_regla(seguridad.ARCHIVO, desde or __file__)
    if ruta is None:
        raise ResumenInvalido("no esta %s: sin la matriz no hay contra que armar el tablero"
                              % seguridad.ARCHIVO)
    return ruta


def cargar_dominios(desde=None):
    """Los ocho dominios. Levanta si una regla falta, sobra o esta en dos."""
    with io.open(ruta_de_dominios(desde), encoding="utf-8-sig") as f:
        doc = json.load(f)
    errores = controlar_dominios(doc)
    if errores:
        raise ResumenInvalido("%s no es una agrupacion de las 21 reglas:\n  - %s"
                              % (DOMINIOS, "\n  - ".join(errores)))
    return doc


def controlar_dominios(doc):
    vistas = []
    for dominio in (doc or {}).get("domains") or []:
        vistas.extend(dominio.get("rules") or [])
    errores = []
    repetidas = sorted(set(r for r in vistas if vistas.count(r) > 1))
    if repetidas:
        errores.append("reglas en mas de un dominio: %s" % ", ".join(repetidas))
    faltan = [r for r in seguridad.INVENTARIO if r not in vistas]
    if faltan:
        errores.append("reglas sin dominio: %s" % ", ".join(faltan))
    sobran = sorted(set(vistas) - set(seguridad.INVENTARIO))
    if sobran:
        errores.append("reglas que no son de ES0902: %s" % ", ".join(sobran))
    return errores


def ruta_del_bloque4(proyecto, task_id):
    return os.path.join(proyecto, ".claude", "runtime", "accounting",
                        libro.validar_tarea(task_id), "summary.json")


def bytes_del_bloque4(proyecto, task_id):
    """Los bytes del `summary.json` del Bloque 4, o `None` si no esta. Solo lee."""
    ruta = ruta_del_bloque4(proyecto, task_id)
    if not os.path.isfile(ruta):
        return None
    with io.open(ruta, "rb") as f:
        return f.read()


def ejecucion_del_bloque4(datos, task_id):
    """(ref, valores) de los bytes del `summary.json` del Bloque 4, o (None, None) si no hay.

    Un archivo vacio no tiene nada que mostrar y deja la referencia en null; la huella igual lo
    distingue del ausente por la marca de presencia.
    """
    if not datos:
        return None, None
    try:
        doc = json.loads(datos.decode("utf-8-sig"))
    except ValueError:
        doc = None
    if not isinstance(doc, dict):
        return "task:%s" % task_id, {}
    valores = {}
    for grupo, campo in EJECUCION:
        bloque = doc.get(grupo) if isinstance(doc.get(grupo), dict) else {}
        valores.setdefault(grupo, {})[campo] = bloque.get(campo)
    return "task:%s" % task_id, valores


# -- piezas --------------------------------------------------------------------

def porcentaje(parte, total):
    """Un decimal, ROUND_HALF_UP. Sin denominador no hay porcentaje: `None`, no 100 ni 0."""
    if not total:
        return None
    valor = (decimal.Decimal(100) * decimal.Decimal(parte) / decimal.Decimal(total)).quantize(
        decimal.Decimal("0.1"), rounding=decimal.ROUND_HALF_UP)
    return float(valor)


def _local(regla):
    texto = regla if isinstance(regla, str) else ""
    prefijo = seguridad.ESTANDAR + seguridad.SEPARADOR
    return texto[len(prefijo):] if texto.startswith(prefijo) else texto


def _de_tipo(eventos, tipo, productor=None):
    return [e for e in eventos if e.get("eventType") == tipo
            and (productor is None or (e.get("details") or {}).get("producer") == productor)]


def _ultimo(eventos, tipo, productor=None):
    lista = _de_tipo(eventos, tipo, productor)
    return lista[-1] if lista else None


def _refs(evento):
    return [r for r in ((evento or {}).get("evidenceRefs") or []) if isinstance(r, str)]


def _detalle(evento, clave):
    detalles = (evento or {}).get("details")
    return detalles.get(clave) if isinstance(detalles, dict) else None


def _alcance(eventos):
    """Cada campo es el ultimo valor no nulo del libro, en su orden."""
    salida = dict((c, None) for c in ("project", "application", "environment", "branch",
                                      "commitSha", "buildId", "releaseId", "artifactDigest"))
    for e in eventos:
        alcance = e.get("scope") if isinstance(e.get("scope"), dict) else {}
        for campo in salida:
            valor = alcance.get(campo)
            if isinstance(valor, str) and valor.strip():
                salida[campo] = valor
    return salida


# -- cada parte ----------------------------------------------------------------

def _reglas(eventos, matriz, dominios):
    del_dominio = {}
    for d in dominios.get("domains") or []:
        for r in d.get("rules") or []:
            del_dominio[r] = d.get("domainId")
    ultimas = {}
    for e in _de_tipo(eventos, "RULE_EVALUATION"):
        rid = _local((e.get("normative") or {}).get("rule"))
        if rid:
            ultimas[rid] = e                    # gana el ultimo en el orden del libro
    filas = []
    for r in sorted(matriz.get("rules") or [], key=lambda x: seguridad._orden(x.get("id"))):
        rid = r.get("id")
        evento = ultimas.get(rid)
        if evento is None:
            resultado, fuente = SIN_EVALUAR, None
        else:
            fuente = evento.get("result")
            resultado = TRADUCCION.get(fuente, SIN_RESOLVER)
        filas.append({"ruleKey": r.get("ruleKey") or seguridad.clave(rid), "rule": rid,
                      "result": resultado, "sourceResult": fuente,
                      "blocking": resultado == FALLA, "evidenceRefs": _refs(evento),
                      "domainId": del_dominio.get(rid)})
    return filas


def _cobertura(filas):
    cuenta = dict((r, sum(1 for f in filas if f["result"] == r)) for r in RESULTADOS)
    aplicables = cuenta[PASA] + cuenta[FALLA] + cuenta[SIN_RESOLVER] + cuenta[SIN_EVALUAR]
    intentadas = cuenta[PASA] + cuenta[FALLA] + cuenta[SIN_RESOLVER]
    resueltas = cuenta[PASA] + cuenta[FALLA]
    return {"applicableRules": aplicables, "attemptedRules": intentadas,
            "resolvedRules": resueltas, "passRules": cuenta[PASA], "failRules": cuenta[FALLA],
            "unresolvedRules": cuenta[SIN_RESOLVER], "notEvaluatedRules": cuenta[SIN_EVALUAR],
            "notApplicableRules": cuenta[NO_APLICA],
            "assessmentCoveragePct": porcentaje(intentadas, aplicables),
            "evidenceResolutionPct": porcentaje(resueltas, aplicables)}


def _conocimiento(eventos):
    e = _ultimo(eventos, "KNOWLEDGE_STATE")
    if e is None:
        return {"standard": seguridad.ESTANDAR, "version": None, "freshness": None,
                "sourceIntegrity": None, "blocking": True, "verifiedAt": None}
    estado = _detalle(e, "freshness")
    return {"standard": (e.get("normative") or {}).get("standard") or seguridad.ESTANDAR,
            "version": _detalle(e, "version"), "freshness": estado,
            "sourceIntegrity": _detalle(e, "sourceIntegrity"),
            # Falla cerrado: bloquea si el productor lo dijo O si el estado no es de los que no
            # bloquean. Un evento con el flag perdido no se vuelve vigente.
            "blocking": e.get("blocking") is True or estado not in frescura.NO_BLOQUEAN,
            "verifiedAt": _detalle(e, "verifiedAt")}


def _hallazgos(eventos):
    tipos = ("FINDING_CREATED", "FINDING_UPDATED", "FINDING_RESOLVED")
    items, orden = {}, []
    for e in eventos:
        if e.get("eventType") not in tipos:
            continue
        for fid in e.get("findingIds") or []:
            if not isinstance(fid, str):
                continue
            if fid not in items:
                orden.append(fid)
                items[fid] = {"findingId": fid, "state": ABIERTO, "severity": "UNRESOLVED",
                              "confidence": None, "title": None, "rule": None,
                              "blocking": False, "evidenceRefs": [], "_resuelto": False}
            h = items[fid]
            tipo, resultado = e.get("eventType"), e.get("result")
            if tipo == "FINDING_RESOLVED" or resultado == RESUELTO:
                h["state"] = RESUELTO
                h["_resuelto"] = True
            elif resultado == HALLAZGO_SIN_RESOLVER:
                h["state"] = HALLAZGO_SIN_RESOLVER
            elif tipo == "FINDING_CREATED" and not h["_resuelto"]:
                h["state"] = ABIERTO
            else:
                h["state"] = REABIERTO if (h["_resuelto"] or resultado == REABIERTO) else ABIERTO
            if e.get("severity") in SEVERIDADES:
                h["severity"] = e["severity"]
            if isinstance(e.get("confidence"), str):
                h["confidence"] = e["confidence"]
            if isinstance(_detalle(e, "title"), str):
                h["title"] = _detalle(e, "title")
            regla = (e.get("normative") or {}).get("rule")
            if isinstance(regla, str):
                h["rule"] = regla
            h["blocking"] = e.get("blocking") is True
            h["evidenceRefs"] = sorted(set(h["evidenceRefs"]) | set(_refs(e)))
    lista = []
    for fid in orden:
        h = dict(items[fid])
        h.pop("_resuelto")
        lista.append(h)
    totales = dict((s, 0) for s in SEVERIDADES)
    for h in lista:
        if h["state"] != RESUELTO:
            totales[h["severity"]] += 1
    return {"totalsBySeverity": totales,
            "open": sum(1 for h in lista if h["state"] == ABIERTO),
            "resolved": sum(1 for h in lista if h["state"] == RESUELTO),
            "reopened": sum(1 for h in lista if h["state"] == REABIERTO),
            "unresolved": sum(1 for h in lista if h["state"] == HALLAZGO_SIN_RESOLVER),
            "items": lista}


def _evidencia(eventos):
    ultimas, orden = {}, []
    for e in _de_tipo(eventos, "EVIDENCE_STATE"):
        refs = _refs(e)
        clave = refs[0] if refs else "event:%s" % e.get("eventId")
        if clave not in ultimas:
            orden.append(clave)
        ultimas[clave] = e
    salida = dict((campo, 0) for _, campo in CONTADORES)
    material = []
    for clave in orden:
        e = ultimas[clave]
        resultado = e.get("result")
        if resultado not in dict(CONTADORES):
            resultado = "UNRESOLVED"
        salida[dict(CONTADORES)[resultado]] += 1
        if e.get("blocking") is True and resultado in EVIDENCIA_MATERIAL:
            material.append({"evidenceRef": clave, "result": resultado})
    salida["material"] = material
    return salida


def _integridad(eventos):
    e = _ultimo(eventos, "REPOSITORY_INTEGRITY")
    if e is None:
        return {"state": INTEGRIDAD_SIN_EVALUAR, "sourceState": None, "mode": None,
                "trustedBaseline": None, "suspiciousFindings": None, "confirmedMalicious": None,
                "findingsAnalyzed": None, "reviewId": None, "evidenceRefs": []}
    estado = e.get("result")
    return {"state": RENOMBRE_DE_INTEGRIDAD.get(estado, estado), "sourceState": estado,
            "mode": _detalle(e, "mode"), "trustedBaseline": _detalle(e, "trustedBaseline"),
            "suspiciousFindings": _detalle(e, "suspiciousFindings"),
            "confirmedMalicious": _detalle(e, "confirmedMalicious"),
            "findingsAnalyzed": _detalle(e, "findingsAnalyzed"),
            "reviewId": _detalle(e, "reviewId"), "evidenceRefs": _refs(e)}


def _evaluacion(eventos, alcance):
    """(assessmentState, officialApprovalStatus, detalle). Cada uno de sus propios eventos."""
    flujo = _ultimo(eventos, "ASSESSMENT_STATE")
    g2 = _ultimo(eventos, "CHECK_EVALUATION", "desde_g2")
    c2 = _ultimo(eventos, "APPROVAL_EVIDENCE")

    base_flujo = flujo.get("result") if flujo else None
    declarado_por = _detalle(flujo, "declaredBy")
    if base_flujo == evaluacion.APROBADA and declarado_por in evaluacion.PRODUCTORES_EXTERNOS:
        estado = EXTERNA
    elif base_flujo in FLUJO:
        estado = FLUJO[base_flujo]
    else:
        # APPROVED interno, OFFICIAL_STATUS_UNRESOLVED, un valor desconocido o ningun evento.
        estado = EVALUACION_SIN_RESOLVER
    g2_satisfecho = _detalle(g2, "satisfied") is True
    if (base_flujo in evaluacion.ESTADOS_DEL_HARNESS and estado in (NO_PEDIDA, LISTA_PARA_PEDIR)
            and g2_satisfecho):
        estado = UMBRAL
    estado_c2 = c2.get("result") if c2 else None
    if estado_c2 == C2_REEVALUAR:
        estado = REEVALUAR

    productor = _detalle(c2, "approvalProducer")
    ambiente = _detalle(c2, "approvalEnvironment")
    release = _detalle(c2, "approvalReleaseId")
    # Las cinco filas de la spec, en orden: gana la primera que se cumple. `STALE` es una
    # aprobacion que valio y ya no; una que nunca valio -interna, o emitida fuera de QA- es
    # UNRESOLVED.
    del_alcance = alcance.get("releaseId")
    if c2 is None:                                                              # 1
        aprobacion = NO_DISPONIBLE
    elif estado_c2 in (C2_CAMBIADA, C2_REEVALUAR):                              # 2
        aprobacion = VENCIDA
    elif (estado_c2 != seguridad.PASA or productor not in evaluacion.PRODUCTORES_EXTERNOS
          or ambiente != evaluacion.AMBIENTE_DE_HOMOLOGACION):                  # 3
        aprobacion = APROBACION_SIN_RESOLVER
    elif release is not None and del_alcance is not None and release != del_alcance:   # 4
        aprobacion = VENCIDA
    else:                                                                       # 5
        aprobacion = EXTERNA

    detalle = {"workflowState": base_flujo, "declaredBy": declarado_por,
               "g2Satisfied": g2_satisfecho if g2 else None, "c2State": estado_c2,
               "approvalProducer": productor, "approvalEnvironment": ambiente,
               "approvalReleaseId": release,
               "reassessmentRequired": estado == REEVALUAR,
               "evidenceRefs": sorted(set(_refs(flujo) + _refs(c2)))}
    return estado, aprobacion, detalle


def _bloqueos(conocimiento, integridad_, filas, hallazgos, estado_evaluacion, evaluacion_):
    lista = []

    def sumar(fuente, titulo, estado, refs, efecto):
        lista.append({"blockerId": "B-%03d" % (len(lista) + 1), "source": fuente,
                      "title": titulo, "state": estado, "evidenceRefs": list(refs),
                      "effect": efecto})

    if conocimiento["blocking"]:
        estado = conocimiento["freshness"] or SIN_EVALUAR
        sumar("knowledge",
              "El conocimiento de %s no se puede tratar como vigente (%s)"
              % (conocimiento["standard"], estado), estado, [], BLOQUEADO)
    if (integridad_["sourceState"] == integridad.SIN_BASELINE
            and integridad_["mode"] == integridad.INCIDENTE):
        sumar("repository-integrity",
              "Sin línea de base confiable del repositorio en una revisión de incidente",
              integridad_["state"], integridad_["evidenceRefs"], BLOQUEADO)
    for f in filas:
        if f["result"] == FALLA:
            sumar(f["ruleKey"], "La regla %s de %s no se cumple" % (f["rule"], seguridad.ESTANDAR),
                  FALLA, f["evidenceRefs"], ACCION)
    for h in hallazgos["items"]:
        if h["state"] in VIGENTES and (h["severity"] == "CRITICAL" or h["blocking"]):
            sumar("finding", h["title"] or "Hallazgo %s (%s)" % (h["findingId"], h["severity"]),
                  h["state"], ["finding:%s" % h["findingId"]] + h["evidenceRefs"], ACCION)
    if integridad_["sourceState"] in (integridad.CONFIRMADO, integridad.SOSPECHOSO):
        sumar("repository-integrity",
              "La revisión de integridad del repositorio reporta %s" % integridad_["state"],
              integridad_["state"], integridad_["evidenceRefs"], ACCION)
    if estado_evaluacion == REEVALUAR:
        sumar("assessment", "La evaluación de seguridad tiene que volver a hacerse",
              REEVALUAR, evaluacion_["evidenceRefs"], ACCION)
    return lista


def _incompleto(filas, evidencia_, integridad_):
    return {"rules": [f["ruleKey"] for f in filas if f["result"] in (SIN_RESOLVER, SIN_EVALUAR)],
            "materialEvidence": [m["evidenceRef"] for m in evidencia_["material"]],
            "repositoryIntegrity": integridad_["sourceState"] == integridad.INCOMPLETA}


def _estado_del_sistema(bloqueos, incompleto):
    if any(b["effect"] == BLOQUEADO for b in bloqueos):
        return BLOQUEADO
    if incompleto["rules"] or incompleto["materialEvidence"] or incompleto["repositoryIntegrity"]:
        return INCOMPLETA
    if any(b["effect"] == ACCION for b in bloqueos):
        return ACCION
    return LISTO


def _dominios(filas, dominios):
    por_regla = dict((f["rule"], f) for f in filas)
    salida = []
    for d in dominios.get("domains") or []:
        reglas = [por_regla[r] for r in d.get("rules") or [] if r in por_regla]
        salida.append({"domainId": d.get("domainId"), "title": d.get("title"),
                       "rules": [{"ruleKey": f["ruleKey"], "rule": f["rule"],
                                  "result": f["result"]} for f in reglas],
                       "counts": dict((r, sum(1 for f in reglas if f["result"] == r))
                                      for r in RESULTADOS)})
    return salida


# -- el resumen ----------------------------------------------------------------

ENTRADAS = (libro.LIBRO, seguridad.ARCHIVO, DOMINIOS, "summary.json")


def huella_de_la_foto(datos_libro, datos_matriz, datos_dominios, datos_bloque4=None):
    """`sha256:` de las cuatro entradas, cada una precedida por su nombre y su largo.

    El nombre y el largo hacen que la frontera entre una entrada y la siguiente cuente: sin
    ellos, correr un byte del final del libro al principio de la matriz daria la misma huella.
    El Bloque 4 lleva ademas una marca de presencia: `None` es que el `summary.json` no existe,
    y `b""` que existe vacio. Son dos fotos distintas y dan dos huellas.
    """
    h = hashlib.sha256()
    for nombre, datos in zip(ENTRADAS, (datos_libro, datos_matriz, datos_dominios,
                                        datos_bloque4)):
        marca = ""
        if nombre == ENTRADAS[-1]:
            marca = "ausente\n" if datos is None else "presente\n"
        datos = datos or b""
        h.update(("%s\n%s%d\n" % (nombre, marca, len(datos))).encode("utf-8"))
        h.update(datos)
    return "sha256:" + h.hexdigest()


def resumir(datos_libro, datos_matriz, task_id, datos_dominios, datos_bloque4=None):
    """El resumen de las cuatro entradas, como bytes. No lee nada mas ni mira el reloj."""
    task_id = libro.validar_tarea(task_id)
    try:
        matriz = json.loads((datos_matriz or b"").decode("utf-8-sig"))
    except ValueError as e:
        raise ResumenInvalido("la matriz no se pudo leer: %s" % e)
    try:
        dominios = json.loads((datos_dominios or b"").decode("utf-8-sig"))
    except ValueError as e:
        raise ResumenInvalido("%s no se pudo leer: %s" % (DOMINIOS, e))
    ejecucion_ref, ejecucion = ejecucion_del_bloque4(datos_bloque4, task_id)
    version = seguridad.controlar_version(matriz)
    if version:
        raise ResumenInvalido(version)
    errores = controlar_dominios(dominios)
    if errores:
        raise ResumenInvalido("; ".join(errores))

    todos = libro.leer_bytes(datos_libro)
    eventos = [e for e in todos if not e.get("unreadable")]
    huella = huella_de_la_foto(datos_libro, datos_matriz, datos_dominios, datos_bloque4)
    alcance = _alcance(eventos)

    filas = _reglas(eventos, matriz, dominios)
    cobertura = _cobertura(filas)
    conocimiento = _conocimiento(eventos)
    hallazgos = _hallazgos(eventos)
    evidencia_ = _evidencia(eventos)
    integridad_ = _integridad(eventos)
    estado_evaluacion, aprobacion, detalle_evaluacion = _evaluacion(eventos, alcance)
    bloqueos = _bloqueos(conocimiento, integridad_, filas, hallazgos, estado_evaluacion,
                         detalle_evaluacion)
    incompleto = _incompleto(filas, evidencia_, integridad_)

    por_tipo = {}
    for e in eventos:
        por_tipo[e.get("eventType")] = por_tipo.get(e.get("eventType"), 0) + 1

    return {
        "schema_version": VERSION_SCHEMA,
        "reportId": "SEC-%s-%s" % (task_id, huella[len("sha256:"):][:12]),
        "taskId": task_id,
        "generatedAt": (eventos[-1].get("timestamp") if eventos else None) or SIN_EVENTOS,
        "scope": alcance,
        "systemSecurityState": _estado_del_sistema(bloqueos, incompleto),
        "assessmentState": estado_evaluacion,
        "officialApprovalStatus": aprobacion,
        "knowledge": conocimiento,
        "normative": {"standard": matriz.get("standard"), "version": matriz.get("version"),
                      "rules": filas},
        "coverage": cobertura,
        "findings": hallazgos,
        "blockingConditions": bloqueos,
        "reviewIncomplete": incompleto,
        "repositoryIntegrity": integridad_,
        "assessment": detalle_evaluacion,
        "domains": _dominios(filas, dominios),
        "evidence": evidencia_,
        "ledger": {"events": len(eventos), "unreadableLines": len(todos) - len(eventos),
                   "byType": dict(sorted(por_tipo.items()))},
        "block4ExecutionRef": ejecucion_ref,
        "block4Execution": ejecucion if ejecucion_ref else None,
        "snapshotFingerprint": huella,
    }


def ruta_de_dominios(desde=None):
    ruta = roster.ruta_de_regla(DOMINIOS, desde or __file__)
    if ruta is None:
        raise ResumenInvalido("no esta %s" % DOMINIOS)
    return ruta


def generar(proyecto, task_id, desde=None):
    """Lee las cuatro entradas y arma el resumen. El Bloque 4 solo se lee."""
    task_id = libro.validar_tarea(task_id)
    datos_libro = libro.bytes_de(libro.ruta_de(proyecto, task_id))
    with io.open(ruta_de_matriz(desde), "rb") as f:
        datos_matriz = f.read()
    with io.open(ruta_de_dominios(desde), "rb") as f:
        datos_dominios = f.read()
    return resumir(datos_libro, datos_matriz, task_id, datos_dominios,
                   bytes_del_bloque4(proyecto, task_id))


# -- contrato y escritura ------------------------------------------------------

def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise ResumenInvalido("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar(resumen, desde=None):
    from orquestacion import tools
    armador = tools._armador()
    if armador is None:
        return ["no esta contexto-armar.py, de donde sale el validador"]
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(resumen, esquema)


def como_texto(resumen):
    return json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def escribir(resumen, ruta, desde=None):
    """Lo valida y lo escribe. Un resumen que no valida no se escribe."""
    errores = validar(resumen, desde)
    if errores:
        raise ResumenInvalido("el resumen no valida contra %s:\n  - %s"
                              % (VERSION_SCHEMA, "\n  - ".join(errores[:5])))
    return libro.escribir_atomico(ruta, como_texto(resumen), "el resumen")
