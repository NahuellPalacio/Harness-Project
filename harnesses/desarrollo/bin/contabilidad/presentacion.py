"""Como se muestra una metrica del Bloque 4: lo que no se resolvio es N/D, nunca un cero.

    resuelto(resumen)         -> {"tokens", "cost", "wallMs", "modelMs", "toolMs": bool}
    cantidad(valor, ok)       -> N/D si no esta resuelta; si no, el valor
    para_refutacion(resumen)  -> lo que el resumen de la refutacion muestra del Bloque 4

🔴 `summary.json` guarda los tokens sumados -un 0 si no se resolvio ninguno- con su lista
`unresolved` al lado, y un monto o un tiempo parcial con su estado. Para un programa que lee las
dos cosas alcanza; una persona que lee el numero solo lee un cero que nadie midio, o un piso
presentado como total. La regla de que familia esta resuelta vive aca, una vez, y viaja en el
resumen (`resolved`) para quien no puede importar este paquete (docs/cambios/fail-closed-hardening).
"""
import json

ND = "N/D"
RESUELTO = "RESOLVED"
_FILAS = ("byAgent", "byWorkUnit", "bySession", "byModel")

USO_SIN_RESOLVER = ("USAGE_UNRESOLVED", "USAGE_RECONCILIATION_UNRESOLVED")
COSTO_SIN_RESOLVER = "COST_UNRESOLVED"
TIEMPO_SIN_RESOLVER = "TIME_ATTRIBUTION_UNRESOLVED"
CLASES_DE_TIEMPO = ("wallMs", "modelMs", "toolMs")


def resuelto(resumen):
    """Que metricas estan resueltas. `resumen` es un summary.json o el estado de la barra.

    Cada una con su mejor evidencia, de la mas fina a la mas gruesa:

        tokens   -> USAGE_UNRESOLVED en `unresolved`: los tokens sumados son un piso
        costo    -> el estado del total; sin el, COST_UNRESOLVED en `unresolved`
        tiempo   -> por clase, `<clase>Missing`: un tiempo de pared completo no deja de serlo
                    porque falte el de las tools; sin eso, el estado; sin eso, la lista

    `unresolved` junta los estados de cada evento: es la evidencia mas gruesa, y alcanza para
    ocultar, no para afirmar mas de lo que dice.
    """
    resumen = resumen if isinstance(resumen, dict) else {}
    abiertos = set(resumen.get("unresolved") or ())
    costo = resumen.get("cost") if isinstance(resumen.get("cost"), dict) else {}
    tiempo = resumen.get("time") if isinstance(resumen.get("time"), dict) else {}
    salida = {"tokens": not (abiertos & set(USO_SIN_RESOLVER)),
              "cost": (costo.get("state") == RESUELTO) if "state" in costo
              else COSTO_SIN_RESOLVER not in abiertos}
    for clase in CLASES_DE_TIEMPO:
        if (clase + "Missing") in tiempo:
            salida[clase] = not tiempo[clase + "Missing"]
        elif "state" in tiempo:
            salida[clase] = tiempo["state"] == RESUELTO
        else:
            salida[clase] = TIEMPO_SIN_RESOLVER not in abiertos
    return salida


def cantidad(valor, ok):
    """Como se muestra una metrica: N/D si no se resolvio -un 0 que nadie midio, un piso, o un
    valor que no esta-, y su valor si se resolvio, 0 incluido. Nunca `sin resolver` ni `?`: una
    sola convencion para todo lo que presenta el Bloque 4 (E-43)."""
    return valor if (ok and valor is not None) else ND


def para_mostrar(resumen):
    """Una copia del resumen para mostrarle a una persona: los numeros de una familia sin resolver
    -tokens, costo, tiempo- pasan a N/D. El resumen no se toca."""
    ok = resuelto(resumen)
    vista = json.loads(json.dumps(resumen))

    def _tokens(bloque):
        for clase in list(bloque or {}):
            bloque[clase] = cantidad(bloque[clase], ok["tokens"])

    def _costo(bloque):
        for campo in ("actual", "apiEquivalentEstimated"):
            if isinstance(bloque, dict) and campo in bloque:
                bloque[campo] = cantidad(bloque[campo], ok["cost"])

    _tokens(vista.get("tokens"))
    _costo(vista.get("cost"))
    for campo in ("contextTokens", "contextLimit"):
        # La ventana es una foto: esta o no esta.
        if isinstance(vista.get("context"), dict) and campo in vista["context"]:
            vista["context"][campo] = cantidad(vista["context"][campo], True)
    for campo in CLASES_DE_TIEMPO:
        if isinstance(vista.get("time"), dict) and campo in vista["time"]:
            vista["time"][campo] = cantidad(vista["time"][campo], ok[campo])
    presupuesto = vista.get("budget")
    if isinstance(presupuesto, dict):
        # Lo consumido y lo proyectado son el costo: si el costo no se resolvio, son un piso.
        for campo in ("currentAmount", "projectedAmount"):
            if campo in presupuesto:
                presupuesto[campo] = cantidad(presupuesto[campo], ok["cost"])
        for campo in ("estimatedIncrement", "softLimit", "hardLimit"):
            if campo in presupuesto:
                presupuesto[campo] = cantidad(presupuesto[campo], True)
    for grupo in _FILAS:
        for fila in vista.get(grupo) or []:
            _tokens(fila.get("tokens"))
            _costo(fila.get("cost"))
    for bloque in (vista.get("unattributed") or {}).values():
        if isinstance(bloque, dict):
            _tokens(bloque.get("tokens"))
    return vista


def para_refutacion(resumen):
    """Llamadas, tokens, tiempo y costo del refutador, como los muestra el resumen."""
    ok = resuelto(resumen)
    tokens = resumen.get("tokens") or {}
    tiempo = resumen.get("time") or {}
    costo = resumen.get("cost") or {}
    return {"events": (resumen.get("events") or {}).get("counted"),
            "inputTokens": cantidad(tokens.get("inputTokens"), ok["tokens"]),
            "outputTokens": cantidad(tokens.get("outputTokens"), ok["tokens"]),
            "wallMs": cantidad(tiempo.get("wallMs"), ok["wallMs"]),
            "modelMs": cantidad(tiempo.get("modelMs"), ok["modelMs"]),
            "actual": cantidad(costo.get("actual"), ok["cost"]),
            "apiEquivalentEstimated": cantidad(costo.get("apiEquivalentEstimated"), ok["cost"]),
            "currency": costo.get("currency")}
