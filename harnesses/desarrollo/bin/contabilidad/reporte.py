"""`execution-cost.md`: el reporte administrativo, generado del resumen.

🔴 Este modulo ESCRIBE Markdown y no lo lee nunca. No hay una funcion que abra un `.md`. El
libro es la fuente, el resumen es el agregado determinista y el Markdown es el ultimo paso
de una sola direccion:

    ledger.jsonl  ->  summary.json  ->  execution-cost.md

Recuperar estado contable parseando un reporte es como una cifra redondeada para que entre
en una tabla se convierte en el dato.

En espanol, por ADR-0011: este archivo lo lee una persona que rinde cuentas, no un modelo.
El template original del pedido esta en ingles y esa es una desviacion declarada en la spec.
"""
import io
import os

from . import costos
from . import libro
from . import tiempo

TITULO = "Contabilidad de ejecucion"


def _num(valor):
    if valor is None:
        return "sin resolver"
    return "{:,}".format(int(valor)).replace(",", ".")


def _plata(valor, moneda):
    if valor is None:
        return "sin resolver"
    return "%s %.4f" % (moneda or "", float(valor))


def _fila(nombre, valor):
    return "| %s | %s |" % (nombre, valor)


def _tabla_de_filas(filas, titulo_columna, moneda):
    if not filas:
        return "_Nada atribuido a %s._" % titulo_columna.lower()
    lineas = ["| %s | Eventos | Input | Output | Cache read | Cache creation | Costo |"
              % titulo_columna,
              "|---|---:|---:|---:|---:|---:|---:|"]
    for fila in filas:
        costo = fila.get("cost") or {}
        monto = costo.get("actual")
        if monto is None:
            monto = costo.get("apiEquivalentEstimated")
        lineas.append("| %s | %d | %s | %s | %s | %s | %s |" % (
            fila["id"], fila["events"],
            _num(fila["tokens"]["inputTokens"]),
            _num(fila["tokens"]["outputTokens"]),
            _num(fila["tokens"]["cacheReadTokens"]),
            _num(fila["tokens"]["cacheCreationTokens"]),
            _plata(monto, costo.get("currency") or moneda)))
    return "\n".join(lineas)


def _sin_atribuir(resumen):
    lineas = ["| Dimension | Eventos | Input | Output | Cache read | Cache creation |",
              "|---|---:|---:|---:|---:|---:|"]
    nombres = {"sessionId": "Sesion", "workUnitId": "Unidad de trabajo", "agentId": "Agente"}
    for campo in ("sessionId", "workUnitId", "agentId"):
        bloque = resumen["unattributed"][campo]
        lineas.append("| %s | %d | %s | %s | %s | %s |" % (
            nombres[campo], bloque["events"],
            _num(bloque["tokens"]["inputTokens"]),
            _num(bloque["tokens"]["outputTokens"]),
            _num(bloque["tokens"]["cacheReadTokens"]),
            _num(bloque["tokens"]["cacheCreationTokens"])))
    return "\n".join(lineas)


def _conciliacion(resumen):
    conciliacion = resumen["reconciliation"]
    if conciliacion["state"] == "NOT_APPLICABLE":
        return ("_El proveedor no reporto un agregado propio: no hay contra que conciliar._")
    if conciliacion["state"] == "RECONCILED":
        return "_Lo derivado coincide con lo que reporto el proveedor._"
    lineas = ["Lo derivado de la fuente y lo que reporta el proveedor **no coinciden**. Se "
              "guardan los dos: la derivacion es un piso, no la verdad.",
              "",
              "| Clase | Derivado | Reportado | Diferencia |",
              "|---|---:|---:|---:|"]
    for clase in sorted(conciliacion["differences"]):
        lineas.append("| %s | %s | %s | %s |" % (
            clase, _num(conciliacion["derived"][clase]),
            _num(conciliacion["providerReported"][clase]),
            _num(conciliacion["differences"][clase])))
    return "\n".join(lineas)


def _presupuesto(resumen):
    presupuesto = resumen.get("budget") or {}
    if not presupuesto:
        return "_No hay presupuesto declarado para esta tarea._"
    return "\n".join([
        _fila("Estado", presupuesto.get("status", "sin resolver")),
        _fila("Consumido", _plata(presupuesto.get("currentAmount"),
                                  presupuesto.get("currency"))),
        _fila("Limite blando", _plata(presupuesto.get("softLimit"),
                                      presupuesto.get("currency"))),
        _fila("Limite duro", _plata(presupuesto.get("hardLimit"),
                                    presupuesto.get("currency"))),
        _fila("Motivo", presupuesto.get("reason", "")),
    ])


def generar(resumen):
    """El reporte entero, como texto. Todos sus numeros salen del resumen."""
    costo = resumen["cost"]
    moneda = costo.get("currency")
    real = costo.get("actual")
    equivalente = costo.get("apiEquivalentEstimated")

    partes = [
        "# %s — %s" % (TITULO, resumen["taskId"] or "sin tarea"),
        "",
        "Generado de `ledger.jsonl` por agregacion determinista. **Este Markdown es un "
        "reporte, no la fuente contable.**",
        "",
        "## Resumen administrativo",
        "",
        "| Metrica | Valor |",
        "|---|---:|",
        _fila("Tarea", resumen["taskId"] or "sin resolver"),
        _fila("Proyecto", resumen.get("projectId") or "sin atribuir"),
        _fila("Desde", resumen["window"]["startedAt"] or "sin resolver"),
        _fila("Hasta", resumen["window"]["completedAt"] or "sin resolver"),
        _fila("Eventos contados", str(resumen["events"]["counted"])),
        _fila("Duplicados descartados", str(resumen["events"]["duplicates"])),
        _fila("Correcciones", str(resumen["events"]["corrections"])),
        _fila("Tiempo de pared", tiempo.como_texto(resumen["time"].get("wallMs"))),
        _fila("Tiempo de modelo", tiempo.como_texto(resumen["time"].get("modelMs"))),
        _fila("Tiempo de tools", tiempo.como_texto(resumen["time"].get("toolMs"))),
        _fila("Tokens de input", _num(resumen["tokens"]["inputTokens"])),
        _fila("Tokens de output", _num(resumen["tokens"]["outputTokens"])),
        _fila("Tokens de cache read", _num(resumen["tokens"]["cacheReadTokens"])),
        _fila("Tokens de cache creation", _num(resumen["tokens"]["cacheCreationTokens"])),
        _fila("Ventana al final", "%s / %s" % (
            _num(resumen["context"]["contextTokens"]),
            _num(resumen["context"]["contextLimit"]))),
        _fila("Costo real", _plata(real, moneda)),
        _fila("Equivalente de API estimado", _plata(equivalente, moneda)),
        _fila("Origen del costo", resumen.get("costSource", "")),
        _fila("Modo de facturacion", ", ".join(costo.get("billingModes") or []) or "sin declarar"),
        "",
        "> 🔴 **Costo real y equivalente de API no son lo mismo.** Con una suscripcion, lo "
        "que figura como equivalente NO se gasto: es lo que habria costado por API.",
        "",
        "## Por agente",
        "",
        _tabla_de_filas(resumen["byAgent"], "Agente", moneda),
        "",
        "## Por unidad de trabajo",
        "",
        _tabla_de_filas(resumen["byWorkUnit"], "Unidad", moneda),
        "",
        "## Por sesion",
        "",
        _tabla_de_filas(resumen["bySession"], "Sesion", moneda),
        "",
        "## Por modelo",
        "",
        _tabla_de_filas(resumen["byModel"], "Modelo", moneda),
        "",
        "## Presupuesto",
        "",
        "| Metrica | Valor |",
        "|---|---:|",
        _presupuesto(resumen),
        "",
        "## Escalamientos caros",
        "",
        _escalamientos(resumen),
        "",
        "## Sin atribuir",
        "",
        "Lo que no se pudo atribuir **cuenta en el total de la tarea y no se reparte** entre "
        "las filas conocidas. Por eso las tablas de arriba suman menos que el total.",
        "",
        _sin_atribuir(resumen),
        "",
        "## Conciliacion con el proveedor",
        "",
        _conciliacion(resumen),
        "",
        "## Contabilidad sin resolver",
        "",
        _abiertos(resumen),
        "",
        "## Trazabilidad",
        "",
        "```",
        "ledger.jsonl",
        "  -> agregacion determinista",
        "  -> summary.json",
        "  -> execution-cost.md",
        "```",
        "",
    ]
    return "\n".join(partes)


def _escalamientos(resumen):
    if not resumen["premiumEscalations"] and not resumen["budgetEvents"]:
        return "_No hubo escalamientos ni decisiones de presupuesto registradas._"
    lineas = ["| Cuando | Unidad | Tier | Estado | Motivo |", "|---|---|---|---|---|"]
    for evento in resumen["premiumEscalations"]:
        lineas.append("| %s | %s | %s | %s | %s |" % (
            evento.get("timestamp") or "", evento.get("workUnitId") or "sin atribuir",
            evento.get("tier") or "", "solicitado", evento.get("reason") or ""))
    for evento in resumen["budgetEvents"]:
        lineas.append("| %s | %s | %s | %s | %s |" % (
            evento.get("timestamp") or "", evento.get("workUnitId") or "sin atribuir",
            "", evento.get("status") or "", evento.get("reason") or ""))
    return "\n".join(lineas)


def _abiertos(resumen):
    if not resumen["unresolved"]:
        return "_Nada quedo sin resolver._"
    explicacion = {
        "USAGE_UNRESOLVED": "hay eventos cuyo consumo no se pudo leer. No es cero.",
        costos.SIN_RESOLVER: "hay costo que no se pudo calcular.",
        costos.SIN_PRECIO: "falta una fuente de precios: el harness no trae tarifas.",
        tiempo.SIN_ATRIBUIR: "falta tiempo en alguna de las tres clases.",
        "SESSION_ATTRIBUTION_UNRESOLVED": "hay consumo sin sesion conocida.",
        "WORKUNIT_ATTRIBUTION_UNRESOLVED": "hay consumo sin unidad de trabajo conocida.",
        "AGENT_ATTRIBUTION_UNRESOLVED": "hay consumo sin agente conocido.",
        "USAGE_RECONCILIATION_UNRESOLVED":
            "lo derivado y lo que reporta el proveedor no coinciden.",
    }
    lineas = ["| Estado | Que significa |", "|---|---|"]
    for estado in resumen["unresolved"]:
        lineas.append("| `%s` | %s |" % (estado, explicacion.get(estado, "")))
    return "\n".join(lineas)


def escribir(resumen, ruta):
    libro.exigir_que_no_sea_el_libro(ruta, "el reporte")
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(generar(resumen))
    return ruta
