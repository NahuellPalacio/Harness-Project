"""El contrato normalizado que todo adaptador cumple, y la traduccion a evento.

Un adaptador devuelve REGISTROS normalizados y nada mas. No arma eventos, no calcula plata
y no sabe que existe un libro. Lo que sigue -pasar de registro a evento, y de consumo a
costo- pasa acá, del lado que no conoce ningun proveedor.

    provider / model
    tokens   input, output, cacheRead, cacheCreation, context, contextLimit
    time     wallMs, modelMs, toolMs
    session  providerSessionId
    dedupKey la clave de idempotencia del hecho
    kind     USAGE (un hecho), PROVIDER_AGGREGATE (otra medicion del mismo periodo) o
             CONTEXT_SNAPSHOT (una foto de la ventana, que no es consumo)

🔴 `context` no es facturable y no se suma. Va en el registro porque la barra lo necesita;
la agregacion sabe que es una foto.

🔴 Un CONTEXT_SNAPSHOT se escribe como CONTEXT_WINDOW_OBSERVED, con sus numeros en
`contextWindow` y sin `usage`, `time` ni `cost`: una foto no es una llamada al modelo, y un
evento de uso con ceros entraria a los conteos, a la conciliacion y a la atribucion. Lo arma
el adaptador con `foto(...)`; aca no se sabe de donde salio ni como se llaman sus campos.
"""
from .. import costos
from .. import eventos
from .. import tiempo

USO = "USAGE"
AGREGADO = "PROVIDER_AGGREGATE"
FOTO = "CONTEXT_SNAPSHOT"
CLASES = (USO, AGREGADO, FOTO)

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


def foto(provider=None, model=None, context=None, limit=None, reported_used=None,
         reported_remaining=None, source=None, session=None, dedup_key=None, reference=None,
         timestamp=None):
    """Una foto de la ventana: cuanto ocupa y de cuanto es, segun el proveedor.

    `context` tiene que ser un entero ya resuelto: una foto sin tokens no es una foto, y el
    adaptador devuelve "sin observacion" en vez de armarla. `limit` puede faltar -None-, y
    los dos porcentajes van como los mando el proveedor: son evidencia, no el calculo.
    """
    reg = registro(provider=provider, model=model,
                   tokens={"context": context, "contextLimit": limit},
                   session=session, dedup_key=dedup_key, reference=reference,
                   timestamp=timestamp, kind=FOTO)
    reg["window"] = {"source": source, "usedPercentage": reported_used,
                     "remainingPercentage": reported_remaining}
    return reg


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
    if reg.get("kind") == FOTO:
        if not eventos.entero_no_negativo((reg.get("tokens") or {}).get("context")):
            errores.append("una foto sin `tokens.context` no es una foto de la ventana")
        if not reg.get("dedupKey"):
            errores.append(
                "una foto sin `dedupKey` tendria un id nuevo en cada dibujo, y el libro creceria "
                "con la misma observacion")
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
    if reg.get("kind") == FOTO:
        return _evento_de_foto(reg, task_id, adaptador, **atribucion)

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


def _evento_de_foto(reg, task_id, adaptador, **atribucion):
    """CONTEXT_WINDOW_OBSERVED: la foto en `contextWindow`, y nada de uso, tiempo ni plata.

    El diagnostico sale de los numeros, no de lo que diga el adaptador: con mas tokens que
    ventana la foto lo lleva escrito, y el resumen lo vuelve a calcular igual."""
    tokens = reg.get("tokens") or {}
    ventana = reg.get("window") or {}
    foto_ = {"contextTokens": tokens.get("context"),
             "contextLimit": tokens.get("contextLimit"),
             "reportedUsedPercentage": ventana.get("usedPercentage"),
             "reportedRemainingPercentage": ventana.get("remainingPercentage")}
    if ventana.get("source"):
        foto_["source"] = ventana["source"]
    diagnostico = eventos.diagnostico_de_ventana(foto_["contextTokens"], foto_["contextLimit"])
    if diagnostico:
        foto_["diagnostic"] = diagnostico
    campos = dict(atribucion)
    campos.pop("metadata", None)
    campos.setdefault("sessionId", (reg.get("session") or {}).get("providerSessionId"))
    campos.update({
        "dedupKey": reg.get("dedupKey"),
        "rawReference": reg.get("reference"),
        "contextWindow": foto_,
    })
    if reg.get("timestamp"):
        campos["timestamp"] = reg["timestamp"]
    return eventos.nuevo(eventos.FOTO_DE_VENTANA, task_id, adaptador, **campos)


def tipo_de(reg):
    """El tipo de evento que le toca a un registro: un agregado cierra la sesion, y una foto
    es una observacion de la ventana."""
    if reg.get("kind") == FOTO:
        return eventos.FOTO_DE_VENTANA
    return "SESSION_COMPLETED" if reg.get("kind") == AGREGADO else "MODEL_CALL_COMPLETED"


def id_de(reg, adaptador):
    """El `eventId` que va a tener el evento de este registro, sin armarlo. None si el registro
    no tiene `dedupKey`: ese id se inventa al armar el evento, y no se puede saber antes.

    Es lo que deja saltear lo que el libro ya tiene sin pagar la conversion y la validacion de
    cada registro, que es lo caro de reingerir una transcripcion larga.
    """
    clave = reg.get("dedupKey")
    return eventos.id_de(adaptador, tipo_de(reg), clave) if clave else None


def a_eventos(registros, task_id, adaptador, politica=None, **atribucion):
    """Todos los registros de una corrida, en orden."""
    salida = []
    for reg in registros:
        salida.append(a_evento(reg, task_id, adaptador, politica, tipo_de(reg), **atribucion))
    return salida
