"""Los nueve productores: la salida estructurada de una funcion del harness, como evento del libro.

Cada productor recibe lo que devuelve una funcion de `orquestacion/` -no texto, no un resumen
escrito por alguien- y exige su forma. Si la forma no es la de esa funcion, levanta y no hay
evento. El evento sale con:

    details.producer        el nombre del productor, de la lista cerrada de `libro.PRODUCTORES`
    evidenceFingerprints    el sha256 de la salida que recibio
    eventId                 el sha256 del evento mismo: la misma salida en el mismo momento es el
                            mismo evento, y reingerirla no duplica nada

    desde_regla        seguridad.resultado           RULE_EVALUATION
    desde_check        la salida de un check          CHECK_EVALUATION (+ EVIDENCE_STATE)
    desde_revision     revisiones.resolver            REVIEW_EVALUATION
    desde_hallazgo     un hallazgo y su ciclo         FINDING_CREATED / _UPDATED / _RESOLVED
    desde_evaluacion   evaluacion.estado_oficial      ASSESSMENT_STATE
    desde_g2           evaluacion.umbral              CHECK_EVALUATION de G2
    desde_aprobacion   el check de C2                 APPROVAL_EVIDENCE
    desde_integridad   integridad.revisar             REPOSITORY_INTEGRITY
    desde_frescura     el documento de frescura       KNOWLEDGE_STATE

Todos devuelven una LISTA de eventos, aunque casi siempre traiga uno: `desde_check` puede
agregar el `EVIDENCE_STATE` de lo que el check dejo sin verificar, y una firma uniforme evita
que quien los llama tenga que acordarse de cual devuelve que.

🔴 Nada de aca decide un resultado. `desde_regla` copia el de `seguridad.resultado`; el resumen
lo traduce con una tabla. Y ningun productor importa `controles/`: el check de C2 se reconoce
por el nombre de su control y por los estados que `evaluacion.ESTADOS_DEL_CHECK_C2` ya copia.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orquestacion import evaluacion              # noqa: E402
from orquestacion import frescura                # noqa: E402
from orquestacion import integridad              # noqa: E402
from orquestacion import seguridad               # noqa: E402

from . import libro                              # noqa: E402

CAMPOS_DE_ALCANCE = ("project", "application", "environment", "branch", "commitSha",
                     "buildId", "releaseId", "artifactDigest")

CONTROL_C2 = "qa-security-approval-evidence"
CONTROL_G2 = "security-vulnerability-acceptance-threshold"

ACCIONES_DE_HALLAZGO = {"CREATED": "FINDING_CREATED", "UPDATED": "FINDING_UPDATED",
                        "RESOLVED": "FINDING_RESOLVED"}
ESTADOS_DE_HALLAZGO = ("OPEN", "REOPENED", "RESOLVED", "UNRESOLVED")
SEVERIDADES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNRESOLVED")

# Lo que la evidencia de un check puede ser. La clase sale del estado del check con una regla
# fija y declarada aca, no de un juicio:
#
#     termina en _TEST_UNSAFE     UNSAFE_TEST_SKIPPED   la prueba no se corrio por insegura
#     PASS o FAIL                 VERIFIED              el check llego a una conclusion
#     NOT_APPLICABLE              (ninguno)             no habia nada que verificar
#     contiene CONFLICT           CONFLICTING
#     contiene MISSING            MISSING
#     cualquier otro              UNRESOLVED
VERIFICADA = "VERIFIED"
FALTANTE = "MISSING"
EN_CONFLICTO = "CONFLICTING"
PRUEBA_INSEGURA = "UNSAFE_TEST_SKIPPED"
SIN_RESOLVER = "UNRESOLVED"
ESTADOS_DE_EVIDENCIA = (VERIFICADA, FALTANTE, EN_CONFLICTO, PRUEBA_INSEGURA, SIN_RESOLVER)
SUFIJO_INSEGURO = "_TEST_UNSAFE"

# La frescura, vista como integridad de la fuente.
INTEGRIDAD_DE_FUENTE = {
    frescura.ALERTA_DE_INTEGRIDAD: "ALERT",
    frescura.CAMBIO_MISMA_VERSION: "ALERT",
    frescura.SIN_VERIFICAR: "UNVERIFIED",
    frescura.CURRENT: "VERIFIED",
}


class ProductorInvalido(ValueError):
    """La entrada no tiene la forma de la salida que el productor dice traducir."""


# -- las piezas comunes --------------------------------------------------------

def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _alcance(alcance):
    if not isinstance(alcance, dict):
        raise ProductorInvalido("el alcance tiene que ser un objeto con al menos `project`")
    proyecto = alcance.get("project")
    if not isinstance(proyecto, str) or not proyecto.strip():
        raise ProductorInvalido("el alcance no declara `project`: no se sabe que se evaluo")
    salida = {}
    for campo in CAMPOS_DE_ALCANCE:
        valor = alcance.get(campo)
        salida[campo] = valor if isinstance(valor, str) and valor.strip() else None
    salida["project"] = proyecto
    return salida


def _textos(valor):
    return sorted(set(v for v in (valor or []) if isinstance(v, str) and v.strip())) \
        if isinstance(valor, list) else []


def _evento(tipo, entrada, productor, task_id, alcance, cuando, agente, resultado,
            normativa=None, detalles=None, **campos):
    evento = {
        "schema_version": libro.VERSION_SCHEMA,
        "timestamp": cuando or ahora(),
        "eventType": tipo,
        "taskId": libro.validar_tarea(task_id),
        "executionId": None,
        "agentId": agente if isinstance(agente, str) else None,
        "scope": _alcance(alcance),
        "normative": normativa,
        "result": str(resultado),
        "findingIds": [],
        "severity": None,
        "confidence": None,
        "evidenceRefs": [],
        "evidenceFingerprints": [libro.huella(entrada)],
        "blocking": False,
        "details": dict(detalles or {}, producer=productor),
    }
    evento.update(campos)
    evento["eventId"] = "sev-" + libro.huella(evento)[len("sha256:"):][:32]
    return evento


def _normativa(regla=None, check=None, review=None, policy=None,
               estandar=seguridad.ESTANDAR, version=seguridad.VERSION_ESPERADA):
    return {"standard": estandar, "version": version, "rule": regla, "policy": policy,
            "check": check, "review": review}


def _exigir(condicion, motivo):
    if not condicion:
        raise ProductorInvalido(motivo)


# -- las reglas ----------------------------------------------------------------

def desde_regla(resultado, task_id, alcance, cuando=None, agente=None):
    """Lo que devuelve `seguridad.resultado`, como `RULE_EVALUATION`. El resultado va tal cual."""
    r = resultado if isinstance(resultado, dict) else {}
    rid = r.get("rule")
    _exigir(rid in seguridad.INVENTARIO,
            "desde_regla recibe la salida de seguridad.resultado, y `%s` no es una regla de "
            "ES0902" % rid)
    _exigir(r.get("ruleKey") == seguridad.clave(rid),
            "desde_regla: `ruleKey` es `%s` y a %s le corresponde `%s`"
            % (r.get("ruleKey"), rid, seguridad.clave(rid)))
    _exigir(r.get("result") in seguridad.RESULTADOS,
            "desde_regla: `%s` no es un resultado de seguridad.RESULTADOS" % r.get("result"))
    _exigir(isinstance(r.get("states"), list) and isinstance(r.get("source"), dict),
            "desde_regla: faltan `states` o `source`, que seguridad.resultado siempre trae")
    fuente = r["source"]
    return [_evento("RULE_EVALUATION", r, "desde_regla", task_id, alcance, cuando, agente,
                    r["result"],
                    normativa=_normativa(regla=rid, version=fuente.get("version")
                                         or seguridad.VERSION_ESPERADA),
                    detalles={"ruleKey": r["ruleKey"], "states": _textos(r.get("states")),
                              "applicability": r.get("applicability")},
                    evidenceRefs=_textos(r.get("evidence")))]


def clase_de_evidencia(estado):
    """La clase de evidencia que deja un estado de check, o None si no hubo nada que verificar."""
    if not isinstance(estado, str) or estado == seguridad.NO_APLICABLE:
        return None
    if estado.endswith(SUFIJO_INSEGURO):
        return PRUEBA_INSEGURA
    if estado in (seguridad.PASA, seguridad.FALLA):
        return VERIFICADA
    if "CONFLICT" in estado:
        return EN_CONFLICTO
    if "MISSING" in estado:
        return FALTANTE
    return SIN_RESOLVER


def desde_check(resultado, task_id, alcance, cuando=None, agente=None, material=True):
    """La salida de un check, como `CHECK_EVALUATION`, y el estado de su evidencia.

    El `CHECK_EVALUATION` no le pone resultado a ninguna regla: el resumen no lo lee para eso.
    `material` dice si esa evidencia es necesaria para concluir; lo decide quien llama, que
    sabe para que corrio el check.
    """
    r = resultado if isinstance(resultado, dict) else {}
    control = r.get("control")
    estado = r.get("state")
    _exigir(isinstance(control, str) and control.strip(),
            "desde_check recibe la salida de un check, y no trae `control`")
    _exigir(isinstance(estado, str) and estado.strip(),
            "desde_check: la salida de %s no trae `state`" % control)
    regla = r.get("rule") if isinstance(r.get("rule"), str) else None
    fuente = r.get("source") if isinstance(r.get("source"), dict) else {}
    normativa = _normativa(regla=regla, check=control,
                           estandar=fuente.get("standard") or seguridad.ESTANDAR,
                           version=fuente.get("version") or seguridad.VERSION_ESPERADA)
    ref = "check:%s" % control
    eventos = [_evento("CHECK_EVALUATION", r, "desde_check", task_id, alcance, cuando, agente,
                       estado, normativa=normativa, detalles={"control": control},
                       evidenceRefs=[ref] + [e for e in _textos(r.get("evidence")) if e != ref])]
    clase = clase_de_evidencia(estado)
    if clase is not None:
        eventos.append(_evento("EVIDENCE_STATE", r, "desde_check", task_id, alcance, cuando,
                               agente, clase, normativa=normativa,
                               detalles={"control": control, "checkState": estado},
                               evidenceRefs=[ref], blocking=bool(material)))
    return eventos


def desde_revision(resuelta, task_id, alcance, review_id, cuando=None, agente=None):
    """Lo que devuelve `revisiones.resolver`, como `REVIEW_EVALUATION`."""
    r = resuelta if isinstance(resuelta, dict) else {}
    _exigir(isinstance(r.get("result"), str) and isinstance(r.get("states"), list),
            "desde_revision recibe la salida de revisiones.resolver: `result` y `states`")
    _exigir(isinstance(review_id, str) and review_id.strip(),
            "desde_revision necesita el id de la review")
    fuente = r.get("source") if isinstance(r.get("source"), dict) else {}
    return [_evento("REVIEW_EVALUATION", r, "desde_revision", task_id, alcance, cuando, agente,
                    r["result"],
                    normativa=_normativa(regla=fuente.get("rule"), review=review_id,
                                         estandar=fuente.get("standard") or seguridad.ESTANDAR,
                                         version=fuente.get("version")
                                         or seguridad.VERSION_ESPERADA),
                    detalles={"states": _textos(r.get("states"))})]


# -- los hallazgos -------------------------------------------------------------

def _severidad(valor):
    """La severidad como uno de los seis valores. La de integridad viene como {value, source}."""
    if isinstance(valor, dict):
        valor = valor.get("value")
    if valor is None:
        return "UNRESOLVED"
    texto = str(valor).upper()
    return texto if texto in SEVERIDADES else "UNRESOLVED"


def desde_hallazgo(hallazgo, accion, task_id, alcance, estado=None, cuando=None, agente=None):
    """Un paso del ciclo de vida de un hallazgo: creado, actualizado o resuelto.

    No hay schema unificado de hallazgo y este productor no inventa uno. Del hallazgo toma
    `findingId` (o `id`), `severity`, `confidence`, `blocking`, `title`, `rule` y `evidence`. La
    severidad y la confianza viajan cada una en su campo y ninguna se deriva de la otra.
    `blocking` es `true` solo si el que produjo el hallazgo lo marco asi.
    """
    h = hallazgo if isinstance(hallazgo, dict) else {}
    fid = h.get("findingId") or h.get("id")
    _exigir(isinstance(fid, str) and fid.strip(), "desde_hallazgo: el hallazgo no tiene id")
    _exigir(accion in ACCIONES_DE_HALLAZGO,
            "desde_hallazgo: la accion es una de %s" % ", ".join(sorted(ACCIONES_DE_HALLAZGO)))
    if accion == "CREATED":
        resultado = "OPEN"
    elif accion == "RESOLVED":
        resultado = "RESOLVED"
    else:
        _exigir(estado in ESTADOS_DE_HALLAZGO,
                "desde_hallazgo: una actualizacion dice a que estado pasa (%s)"
                % ", ".join(ESTADOS_DE_HALLAZGO))
        resultado = estado
    regla = h.get("rule") if isinstance(h.get("rule"), str) else None
    if regla and regla.startswith(seguridad.ESTANDAR + seguridad.SEPARADOR):
        regla = regla[len(seguridad.ESTANDAR) + len(seguridad.SEPARADOR):]
    confianza = h.get("confidence")
    return [_evento(ACCIONES_DE_HALLAZGO[accion], h, "desde_hallazgo", task_id, alcance, cuando,
                    agente, resultado, normativa=_normativa(regla=regla),
                    detalles={"title": h.get("title") if isinstance(h.get("title"), str)
                              else None},
                    findingIds=[fid], severity=_severidad(h.get("severity")),
                    confidence=str(confianza).upper() if isinstance(confianza, str) else None,
                    evidenceRefs=_textos(h.get("evidence")),
                    blocking=h.get("blocking") is True)]


# -- la evaluacion y la aprobacion ---------------------------------------------

def desde_evaluacion(declarada, task_id, alcance, cuando=None, agente=None):
    """Lo que devuelve `evaluacion.estado_oficial`, como `ASSESSMENT_STATE`.

    Se copia el `state` que la guarda dejo -un APPROVED interno ya llega como
    OFFICIAL_STATUS_UNRESOLVED- y quien lo declaro, para que el resumen vuelva a mirarlo.
    """
    r = declarada if isinstance(declarada, dict) else {}
    _exigir("state" in r and "requestedState" in r and "producer" in r,
            "desde_evaluacion recibe la salida de evaluacion.estado_oficial: `state`, "
            "`requestedState` y `producer`")
    _exigir(r.get("state") in evaluacion.ESTADOS,
            "desde_evaluacion: `%s` no es un estado de evaluacion.ESTADOS" % r.get("state"))
    return [_evento("ASSESSMENT_STATE", r, "desde_evaluacion", task_id, alcance, cuando, agente,
                    r["state"], normativa=_normativa(),
                    detalles={"requestedState": r.get("requestedState"),
                              "declaredBy": r.get("producer")
                              if isinstance(r.get("producer"), str) else None},
                    evidenceRefs=_textos(r.get("evidence")))]


def desde_g2(umbral, task_id, alcance, cuando=None, agente=None):
    """Lo que devuelve `evaluacion.umbral`, como el `CHECK_EVALUATION` de G2.

    No es un `ASSESSMENT_STATE`: el umbral es un calculo y no un estado del flujo. Y como
    `CHECK_EVALUATION` no le pone resultado a la regla G2.
    """
    r = umbral if isinstance(umbral, dict) else {}
    _exigir(isinstance(r.get("satisfied"), bool) and "maxLowAllowed" in r,
            "desde_g2 recibe la salida de evaluacion.umbral: `satisfied` y `maxLowAllowed`")
    satisfecho = r["satisfied"] is True
    estados = _textos(r.get("states"))
    resultado = evaluacion.UMBRAL_SATISFECHO if satisfecho else (
        estados[0] if estados else "G2_THRESHOLD_NOT_SATISFIED")
    return [_evento("CHECK_EVALUATION", r, "desde_g2", task_id, alcance, cuando, agente,
                    resultado, normativa=_normativa(regla="G2", check=CONTROL_G2),
                    detalles={"satisfied": satisfecho, "lowCount": r.get("lowCount"),
                              "aboveLowCount": r.get("aboveLowCount")})]


def desde_aprobacion(resultado_c2, task_id, alcance, productor=None, ambiente=None,
                     release=None, cuando=None, agente=None):
    """La salida del check de C2, como `APPROVAL_EVIDENCE`.

    La salida del check no dice quien emitio la aprobacion, en que ambiente ni para que release:
    los validó y no los devuelve. Los pasa quien llama, desde el registro de la aprobacion
    elegida, y el resumen los vuelve a mirar contra el alcance.
    """
    r = resultado_c2 if isinstance(resultado_c2, dict) else {}
    _exigir(r.get("control") == CONTROL_C2,
            "desde_aprobacion recibe la salida de %s y esto dice ser de `%s`"
            % (CONTROL_C2, r.get("control")))
    _exigir(r.get("state") in evaluacion.ESTADOS_DEL_CHECK_C2,
            "desde_aprobacion: `%s` no es un estado del check de C2" % r.get("state"))
    ref = r.get("approvalEvidenceRef") if isinstance(r.get("approvalEvidenceRef"), dict) else {}
    return [_evento("APPROVAL_EVIDENCE", r, "desde_aprobacion", task_id, alcance, cuando, agente,
                    r["state"], normativa=_normativa(regla="C2", check=CONTROL_C2),
                    detalles={"approvalProducer": productor if isinstance(productor, str)
                              else None,
                              "approvalEnvironment": ambiente if isinstance(ambiente, str)
                              else None,
                              "approvalReleaseId": release if isinstance(release, str)
                              else None,
                              "approvalId": ref.get("approvalId")
                              if isinstance(ref.get("approvalId"), str) else None},
                    evidenceRefs=_textos(r.get("evidence")))]


# -- la integridad y el conocimiento -------------------------------------------

def desde_integridad(revision, task_id, alcance, cuando=None, agente=None):
    """Lo que devuelve `integridad.revisar`, como `REPOSITORY_INTEGRITY`."""
    r = revision if isinstance(revision, dict) else {}
    _exigir(r.get("capability") == "repository-integrity-review",
            "desde_integridad recibe la salida de integridad.revisar")
    _exigir(r.get("state") in integridad.ESTADOS,
            "desde_integridad: `%s` no es un estado de integridad.ESTADOS" % r.get("state"))
    _exigir(r.get("mode") in integridad.MODOS,
            "desde_integridad: `%s` no es un modo de integridad.MODOS" % r.get("mode"))
    hallazgos = [h for h in (r.get("findings") or []) if isinstance(h, dict)]
    estados = [h.get("status") for h in hallazgos]
    return [_evento("REPOSITORY_INTEGRITY", r, "desde_integridad", task_id, alcance, cuando,
                    agente, r["state"], normativa=None,
                    detalles={"mode": r["mode"],
                              "reviewId": r.get("reviewId")
                              if isinstance(r.get("reviewId"), str) else None,
                              "trustedBaseline": "VERIFIED" if isinstance(r.get("baseline"), dict)
                              else "UNRESOLVED",
                              "findingsAnalyzed": len(hallazgos),
                              "suspiciousFindings": estados.count(integridad.SOSPECHOSO),
                              "confirmedMalicious": estados.count(integridad.CONFIRMADO)},
                    findingIds=sorted(set(h.get("findingId") for h in hallazgos
                                          if isinstance(h.get("findingId"), str))))]


def integridad_de_fuente(estado):
    return INTEGRIDAD_DE_FUENTE.get(estado, "UNRESOLVED")


def desde_frescura(doc, task_id, alcance, cuando=None, agente=None):
    """La entrada `ES0902` del documento de frescura, como `KNOWLEDGE_STATE`.

    El momento del evento es el `verified_at` del documento: la misma verificacion es el mismo
    evento, y correr `--conocimiento` dos veces no duplica nada. Sin entrada de ES0902 el
    conocimiento queda sin estado y bloqueante, que es lo que es.
    """
    d = doc if isinstance(doc, dict) else {}
    _exigir(isinstance(d.get("sources"), dict),
            "desde_frescura recibe el documento de frescura (%s), con `sources`" % frescura.ARCHIVO)
    entrada = d["sources"].get(seguridad.ESTANDAR)
    entrada = entrada if isinstance(entrada, dict) else {}
    estado = entrada.get("state") if entrada.get("state") in frescura.ESTADOS else None
    version = entrada.get("registry_version") or entrada.get("observed_version")
    bloquea = entrada.get("blocking")
    if not isinstance(bloquea, bool):
        bloquea = estado not in frescura.NO_BLOQUEAN
    marca = d.get("verified_at") if isinstance(d.get("verified_at"), str) else None
    return [_evento("KNOWLEDGE_STATE", {"verified_at": marca, "entry": entrada},
                    "desde_frescura", task_id, alcance, cuando or marca, agente,
                    estado or "UNRESOLVED",
                    normativa=_normativa(version=version if isinstance(version, str) else None),
                    detalles={"version": version if isinstance(version, str) else None,
                              "freshness": estado,
                              "sourceIntegrity": integridad_de_fuente(estado),
                              "verifiedAt": marca},
                    blocking=bool(bloquea) or estado is None)]
