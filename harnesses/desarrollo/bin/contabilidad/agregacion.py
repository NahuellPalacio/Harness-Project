"""Del libro al `summary.json`. Deterministico, y con las tres reglas que lo hacen serio.

    1. Un hecho observado dos veces cuenta una vez      -> `dedupKey`
    2. La foto de la ventana no se suma                 -> `contextTokens`
    3. Lo que no se pudo atribuir no se reparte         -> `unattributed`

La invariante que todo reporte tiene que cumplir, y que se puede contar a mano:

    suma de las unidades  +  lo no atribuido  =  total de la tarea

Repartir lo no atribuido entre las unidades conocidas daria un reporte que cierra y una
atribucion inventada. Un reporte que no cierra y lo dice es mas barato.

🔴 Una correccion REEMPLAZA al evento que enmienda: el original sale de la suma y entra la
correccion en su lugar. El original sigue en el disco byte a byte — lo append-only es el
archivo, no la aritmetica.
"""
import io
import json
import os

from . import costos
from . import eventos
from . import libro
from . import tiempo

VERSION_SCHEMA = "execution-summary/1.0"

CLASES = eventos.CLASES_DE_TOKEN

SIN_SESION = "SESSION_ATTRIBUTION_UNRESOLVED"
SIN_UNIDAD = "WORKUNIT_ATTRIBUTION_UNRESOLVED"
SIN_AGENTE = "AGENT_ATTRIBUTION_UNRESOLVED"
SIN_USO = "USAGE_UNRESOLVED"
SIN_TIEMPO = tiempo.SIN_ATRIBUIR
SIN_COSTO = costos.SIN_RESOLVER
SIN_PRECIO = costos.SIN_PRECIO
SIN_CONCILIAR = "USAGE_RECONCILIATION_UNRESOLVED"

ESCALAMIENTO = "MODEL_ESCALATION_REQUESTED"
DECISION = "BUDGET_DECISION_RECORDED"


def _cero():
    return dict((c, 0) for c in CLASES)


def _sumar_en(acumulador, uso):
    for clase in CLASES:
        valor = (uso or {}).get(clase)
        if valor is not None:
            acumulador[clase] += int(valor)


def _agregado_del_proveedor(evento):
    """True si el evento trae un agregado que reporto el proveedor.

    No se suma con los demas: es OTRA medicion del mismo periodo, no un hecho adicional.
    Sumarla seria contar todo dos veces, que es exactamente lo que este modulo existe para
    no hacer.
    """
    return bool((evento.get("metadata") or {}).get("providerAggregate"))


def _utiles(libro):
    """Los eventos que entran en la suma, en orden, ya deduplicados y corregidos.

    Devuelve (contables, conteos, agregados_del_proveedor).
    """
    corregidos = set()
    for evento in libro:
        if evento.get("eventType") == eventos.CORRECCION and evento.get("correctsEventId"):
            corregidos.add(str(evento["correctsEventId"]))

    contables = []
    agregados = []
    vistas = set()
    ids = set()
    conteos = {"total": len(libro), "counted": 0, "duplicates": 0,
               "corrections": 0, "corrected": 0, "unreadable": 0,
               "providerAggregates": 0}

    for evento in libro:
        if (evento.get("metadata") or {}).get("unreadable"):
            conteos["unreadable"] += 1
            continue
        eid = str(evento.get("eventId") or "")
        if eid and eid in ids:
            conteos["duplicates"] += 1
            continue
        ids.add(eid)
        if eid in corregidos:
            conteos["corrected"] += 1
            continue
        if evento.get("eventType") == eventos.CORRECCION:
            conteos["corrections"] += 1
        if _agregado_del_proveedor(evento):
            conteos["providerAggregates"] += 1
            agregados.append(evento)
            continue
        clave = evento.get("dedupKey")
        if clave:
            if clave in vistas:
                conteos["duplicates"] += 1
                continue
            vistas.add(clave)
        contables.append(evento)
        conteos["counted"] += 1

    return contables, conteos, agregados


def _filas(contables, campo):
    """Una fila por valor conocido del campo. Lo desconocido NO entra: va a `unattributed`."""
    filas = {}
    for evento in contables:
        valor = evento.get(campo)
        if valor in (None, ""):
            continue
        fila = filas.setdefault(str(valor), {"id": str(valor), "tokens": _cero(),
                                             "time": [], "cost": [], "events": 0})
        fila["events"] += 1
        _sumar_en(fila["tokens"], evento.get("usage"))
        if evento.get("time"):
            fila["time"].append(evento["time"])
        if evento.get("cost"):
            fila["cost"].append(evento["cost"])
    salida = []
    for clave in sorted(filas):
        fila = filas[clave]
        fila["time"] = tiempo.sumar(fila["time"])
        fila["cost"] = costos.sumar(fila["cost"])
        salida.append(fila)
    return salida


def _no_atribuido(contables, campo):
    acumulador = _cero()
    eventos_sin = 0
    for evento in contables:
        if evento.get(campo) in (None, ""):
            eventos_sin += 1
            _sumar_en(acumulador, evento.get("usage"))
    return {"tokens": acumulador, "events": eventos_sin}


def _filas_por_modelo(contables):
    filas = {}
    for evento in contables:
        modelo = (evento.get("usage") or {}).get("model")
        if not modelo:
            continue
        fila = filas.setdefault(str(modelo), {"id": str(modelo), "tokens": _cero(),
                                              "cost": [], "events": 0})
        fila["events"] += 1
        _sumar_en(fila["tokens"], evento.get("usage"))
        if evento.get("cost"):
            fila["cost"].append(evento["cost"])
    salida = []
    for clave in sorted(filas):
        fila = filas[clave]
        fila["cost"] = costos.sumar(fila["cost"])
        salida.append(fila)
    return salida


def _foto_de_contexto(contables):
    """La ULTIMA foto de la ventana, nunca la suma de todas.

    🔴 Sumar fotos de contexto es la forma mas facil de reportar un numero enorme y falso:
    cada llamada vuelve a mandar la conversacion entera, asi que la suma de las fotos crece
    como el cuadrado de los turnos y no significa nada.
    """
    ultima = None
    for evento in contables:
        uso = evento.get("usage") or {}
        if uso.get("contextTokens") is None:
            continue
        ultima = {"contextTokens": int(uso["contextTokens"]),
                  "contextLimit": uso.get("contextLimit"),
                  "sessionId": evento.get("sessionId"),
                  "model": uso.get("model"),
                  "at": evento.get("timestamp")}
    if ultima is None:
        return {"contextTokens": None, "contextLimit": None, "sessionId": None,
                "model": None, "at": None}
    return ultima


def _conciliar(tokens, agregados):
    """Compara lo derivado contra lo que reporto el proveedor. No elige: reporta las dos.

    La derivacion de una transcripcion es un PISO — lo que se compacto ya no esta en el
    archivo—. Elegir una de las dos en silencio es la decision que nadie despues puede
    auditar.
    """
    reportado = _cero()
    fuentes = []
    for evento in agregados:
        _sumar_en(reportado, evento.get("usage"))
        fuentes.append({"adapter": (evento.get("source") or {}).get("adapter"),
                        "reference": (evento.get("source") or {}).get("rawReference"),
                        "model": (evento.get("usage") or {}).get("model")})
    if not agregados:
        return {"providerReported": None, "derived": dict(tokens), "sources": [],
                "state": "NOT_APPLICABLE", "differences": {}}

    diferencias = dict((c, reportado[c] - tokens[c]) for c in CLASES
                       if reportado[c] != tokens[c])
    return {
        "providerReported": reportado,
        "derived": dict(tokens),
        "sources": fuentes,
        "differences": diferencias,
        "state": SIN_CONCILIAR if diferencias else "RECONCILED",
    }


REPORTADO = "PROVIDER_REPORTED"
DERIVADO = "DERIVED"


def _elegir(reportado, derivado, resuelto):
    """Para PLATA y TIEMPO gana lo que reporto el proveedor; para TOKENS no gana ninguno.

    La asimetria tiene motivo y no es comodidad. De los tokens hay una derivacion por
    evento, que ademas es lo unico que sabe a que sesion, unidad y agente pertenece cada
    consumo: elegir el agregado seria perder la atribucion entera. De la plata y del tiempo
    no hay derivacion por evento — lo unico que existe es la medicion del que factura—, asi
    que preferirla no pierde nada y usa el numero de quien lo cobra.
    """
    if reportado.get("state") == resuelto:
        return reportado, REPORTADO
    return derivado, DERIVADO


def _sin_resolver(contables, tokens_tiempo, costo, no_atribuido, conciliacion):
    """Los estados que quedaron abiertos, ordenados y sin repetir."""
    abiertos = set()
    for evento in contables:
        if (evento.get("usage") or {}).get("state") == SIN_USO:
            abiertos.add(SIN_USO)
        if (evento.get("time") or {}).get("state") == SIN_TIEMPO:
            abiertos.add(SIN_TIEMPO)
        estado = (evento.get("cost") or {}).get("state")
        if estado in (SIN_COSTO, SIN_PRECIO):
            abiertos.add(estado)
    if tokens_tiempo.get("state") == SIN_TIEMPO:
        abiertos.add(SIN_TIEMPO)
    if costo.get("state") == SIN_COSTO:
        abiertos.add(SIN_COSTO)
    for campo, estado in (("sessionId", SIN_SESION), ("workUnitId", SIN_UNIDAD),
                          ("agentId", SIN_AGENTE)):
        if no_atribuido[campo]["events"]:
            abiertos.add(estado)
    if conciliacion.get("state") == SIN_CONCILIAR:
        abiertos.add(SIN_CONCILIAR)
    return sorted(abiertos)


def resumir(libro, task_id="", project_id=None, presupuesto=None):
    """El `summary.json` de un libro. Mismo libro, mismo resumen, byte a byte."""
    contables, conteos, agregados = _utiles(libro)

    tokens = _cero()
    for evento in contables:
        _sumar_en(tokens, evento.get("usage"))

    total_tiempo, fuente_tiempo = _elegir(
        tiempo.sumar([e["time"] for e in agregados
                      if (e.get("time") or {}).get("state") == tiempo.RESUELTO]),
        tiempo.sumar([e["time"] for e in contables if e.get("time")]),
        tiempo.RESUELTO)
    total_costo, fuente_costo = _elegir(
        costos.sumar([e["cost"] for e in agregados
                      if (e.get("cost") or {}).get("state") == costos.RESUELTO]),
        costos.sumar([e["cost"] for e in contables if e.get("cost")]),
        costos.RESUELTO)

    no_atribuido = dict((campo, _no_atribuido(contables, campo))
                        for campo in ("sessionId", "workUnitId", "agentId"))
    conciliacion = _conciliar(tokens, agregados)

    marcas = sorted(str(e.get("timestamp") or "") for e in contables if e.get("timestamp"))
    tarea = str(task_id or (contables[0].get("taskId") if contables else ""))

    resumen = {
        "schema_version": VERSION_SCHEMA,
        "taskId": tarea,
        "projectId": project_id,
        "generatedFrom": "ledger.jsonl",
        "events": conteos,
        "window": {"startedAt": marcas[0] if marcas else None,
                   "completedAt": marcas[-1] if marcas else None},
        "tokens": tokens,
        "context": _foto_de_contexto(contables),
        "time": total_tiempo,
        "timeSource": fuente_tiempo,
        "cost": total_costo,
        "costSource": fuente_costo,
        "byAgent": _filas(contables, "agentId"),
        "byWorkUnit": _filas(contables, "workUnitId"),
        "bySession": _filas(contables, "sessionId"),
        "byModel": _filas_por_modelo(contables),
        "unattributed": no_atribuido,
        "reconciliation": conciliacion,
        "budgetEvents": [_decision(e) for e in contables if e.get("eventType") == DECISION],
        "premiumEscalations": [_escalamiento(e) for e in contables
                               if e.get("eventType") == ESCALAMIENTO],
        "budget": presupuesto or {},
    }
    resumen["unresolved"] = _sin_resolver(
        contables, total_tiempo, total_costo, no_atribuido, conciliacion)
    return resumen


def _decision(evento):
    meta = evento.get("metadata") or {}
    return {"eventId": evento.get("eventId"), "timestamp": evento.get("timestamp"),
            "workUnitId": evento.get("workUnitId"),
            "status": meta.get("status"), "reason": meta.get("reason")}


def _escalamiento(evento):
    meta = evento.get("metadata") or {}
    return {"eventId": evento.get("eventId"), "timestamp": evento.get("timestamp"),
            "workUnitId": evento.get("workUnitId"), "agentId": evento.get("agentId"),
            "tier": meta.get("tier"), "reason": meta.get("reason")}


def cierra(resumen, campo="workUnitId", fila="byWorkUnit"):
    """True si las filas mas lo no atribuido dan el total. La invariante del reporte."""
    for clase in CLASES:
        suma = sum(f["tokens"][clase] for f in resumen[fila])
        suma += resumen["unattributed"][campo]["tokens"][clase]
        if suma != resumen["tokens"][clase]:
            return False
    return True


def escribir(resumen, ruta):
    libro.exigir_que_no_sea_el_libro(ruta, "el resumen")
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return ruta
