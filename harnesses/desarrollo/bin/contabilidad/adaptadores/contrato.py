"""El contrato normalizado que todo adaptador cumple, y la traduccion a evento.

Un adaptador devuelve REGISTROS normalizados y nada mas. No arma eventos, no calcula plata
y no sabe que existe un libro. Lo que sigue -pasar de registro a evento, y de consumo a
costo- pasa acá, del lado que no conoce ningun proveedor.

    provider / model
    tokens   input, output, cacheRead, cacheCreation, context, contextLimit
    time     wallMs, modelMs, toolMs
    session  providerSessionId
    dedupKey la clave de idempotencia del hecho
    kind     USAGE (un hecho) o PROVIDER_AGGREGATE (otra medicion del mismo periodo)

🔴 `context` no es facturable y no se suma. Va en el registro porque la barra lo necesita;
la agregacion sabe que es una foto.
"""
from .. import costos
from .. import eventos
from .. import tiempo

USO = "USAGE"
AGREGADO = "PROVIDER_AGGREGATE"
CLASES = (USO, AGREGADO)

RESUELTO = "RESOLVED"
SIN_RESOLVER = eventos.SIN_RESOLVER

# Del nombre normalizado al del evento. El adaptador no escribe los nombres del contrato de
# eventos: los escribe una sola vez este modulo.
DE_TOKEN = (
    ("input", "inputTokens"),
    ("output", "outputTokens"),
    ("cacheRead", "cacheReadTokens"),
    ("cacheCreation", "cacheCreationTokens"),
    ("context", "contextTokens"),
    ("contextLimit", "contextLimit"),
)


class ContratoInvalido(Exception):
    """El registro no cumple el contrato y no se convierte en evento."""


def registro(provider=None, model=None, tokens=None, time=None, session=None,
             dedup_key=None, reference=None, timestamp=None, kind=USO,
             reported_amount=None, currency=None, state=RESUELTO):
    """Un registro normalizado. Lo que no se sabe queda en None."""
    if kind not in CLASES:
        raise ContratoInvalido("`%s` no es una clase de registro." % kind)
    return {
        "provider": provider,
        "model": model,
        "tokens": dict((nombre, (tokens or {}).get(nombre)) for nombre, _ in DE_TOKEN),
        "time": {"wallMs": (time or {}).get("wallMs"),
                 "modelMs": (time or {}).get("modelMs"),
                 "toolMs": (time or {}).get("toolMs")},
        "session": {"providerSessionId": (session or {}).get("providerSessionId")},
        "dedupKey": dedup_key,
        "reference": reference,
        "timestamp": timestamp,
        "kind": kind,
        "reportedAmount": reported_amount,
        "currency": currency,
        "state": state,
    }


def sin_resolver(reference="", motivo="", provider=None, model=None):
    """El registro de una fuente que no pudo reportar consumo.

    Es lo que devuelve un adaptador sin fuente autoritativa, y es deliberadamente distinto
    de una lista vacia: una lista vacia dice "no paso nada", esto dice "paso y no se cuanto".
    """
    reg = registro(provider=provider, model=model, reference=reference,
                   state=SIN_RESOLVER)
    reg["reason"] = str(motivo)
    return reg


def validar_registro(reg):
    """Lista de errores. Vacia es valido."""
    errores = []
    if not isinstance(reg, dict):
        return ["el registro no es un objeto"]
    for clave in ("provider", "model", "tokens", "time", "session", "dedupKey",
                  "reference", "kind", "state"):
        if clave not in reg:
            errores.append("falta `%s`" % clave)
    if reg.get("kind") not in CLASES:
        errores.append("`kind` tiene que ser uno de %s" % ", ".join(CLASES))
    if reg.get("state") not in (RESUELTO, SIN_RESOLVER):
        errores.append("`state` tiene que ser %s o %s" % (RESUELTO, SIN_RESOLVER))
    for nombre, _ in DE_TOKEN:
        valor = (reg.get("tokens") or {}).get(nombre)
        if valor is not None and not isinstance(valor, int):
            errores.append("`tokens.%s` no es un entero ni None" % nombre)
    if reg.get("state") == RESUELTO and reg.get("kind") == USO and not reg.get("dedupKey"):
        errores.append(
            "un registro de uso resuelto sin `dedupKey` no se puede deduplicar, y lo que "
            "no se puede deduplicar se cuenta dos veces")
    return errores


def _uso_de(reg):
    if reg.get("state") == SIN_RESOLVER:
        return eventos.uso_sin_resolver(reg.get("provider"), reg.get("model"))
    uso = {"state": RESUELTO, "provider": reg.get("provider"), "model": reg.get("model")}
    for normalizado, del_evento in DE_TOKEN:
        uso[del_evento] = (reg.get("tokens") or {}).get(normalizado)
    return uso


def a_evento(reg, task_id, adaptador, politica=None, tipo="MODEL_CALL_COMPLETED",
             **atribucion):
    """De un registro normalizado a un evento de contabilidad, con su costo.

    La atribucion -sessionId, workUnitId, agentId- la pone quien ingiere, porque es lo
    unico que el adaptador no puede saber: una transcripcion no sabe a que unidad de
    trabajo del plan pertenece. Lo que no se le pasa queda sin atribuir, y el resumen lo
    muestra en vez de repartirlo.
    """
    errores = validar_registro(reg)
    if errores:
        raise ContratoInvalido(
            "el registro no cumple el contrato:\n  - %s" % "\n  - ".join(errores[:5]))

    uso = _uso_de(reg)
    crudo = reg.get("time") or {}
    bloque = tiempo.medir(crudo.get("wallMs"), crudo.get("modelMs"), crudo.get("toolMs"))
    costo = costos.calcular(
        uso, politica, reportado=reg.get("reportedAmount"),
        fuente=str(reg.get("reference") or ""),
        version=str(reg.get("timestamp") or ""))
    if reg.get("currency") and not costo.get("currency"):
        costo["currency"] = reg["currency"]

    meta = dict(atribucion.pop("metadata", None) or {})
    if reg.get("kind") == AGREGADO:
        meta["providerAggregate"] = True
    if reg.get("session", {}).get("providerSessionId"):
        meta["providerSessionId"] = reg["session"]["providerSessionId"]
    if reg.get("reason"):
        meta["reason"] = reg["reason"]

    campos = dict(atribucion)
    campos.setdefault("sessionId", reg.get("session", {}).get("providerSessionId"))
    campos.update({
        "dedupKey": reg.get("dedupKey"),
        "timestamp": reg.get("timestamp"),
        "rawReference": reg.get("reference"),
        "usage": uso,
        "time": bloque,
        "cost": costo,
        "metadata": meta,
    })
    return eventos.nuevo(tipo, task_id, adaptador, **campos)


def a_eventos(registros, task_id, adaptador, politica=None, **atribucion):
    """Todos los registros de una corrida, en orden."""
    salida = []
    for reg in registros:
        tipo = "SESSION_COMPLETED" if reg.get("kind") == AGREGADO else "MODEL_CALL_COMPLETED"
        salida.append(a_evento(reg, task_id, adaptador, politica, tipo, **atribucion))
    return salida
