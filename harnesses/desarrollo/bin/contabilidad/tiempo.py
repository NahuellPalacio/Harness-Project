"""El motor de tiempo: tres clases, y ninguna se deduce de otra.

    wallMs    cuanto paso en el reloj de la pared
    modelMs   cuanto estuvo el modelo trabajando
    toolMs    cuanto tardaron las tools

🔴 Tiempo de pared NO es tiempo de modelo. Entre el principio y el final de una unidad hay
tools, red, esperas y una persona leyendo. Rotular la pared como modelo infla la unica
metrica con la que despues se compara un tier contra otro, y la infla justo en las
unidades que mas esperan.

Sin evidencia de tiempo de modelo el bloque sale `TIME_ATTRIBUTION_UNRESOLVED` con
`modelMs` en None. No se rellena con la pared.
"""
RESUELTO = "RESOLVED"
SIN_ATRIBUIR = "TIME_ATTRIBUTION_UNRESOLVED"

CLASES = ("wallMs", "modelMs", "toolMs")


def _entero(valor):
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def medir(wall=None, model=None, tool=None):
    """Un bloque de tiempo. Lo que no se sabe queda en None, nunca en cero."""
    bloque = {"wallMs": _entero(wall), "modelMs": _entero(model), "toolMs": _entero(tool)}
    falta = [c for c in CLASES if bloque[c] is None]
    bloque["state"] = SIN_ATRIBUIR if falta else RESUELTO
    return bloque


def sumar(bloques):
    """Las tres clases sumadas por separado, mas cuantos bloques no se pudieron atribuir.

    Cada clase suma lo que tiene y cuenta lo que le falto. Un total de `modelMs` que se
    armo con la mitad de los eventos y no lo dice es un numero que despues alguien divide.
    """
    total = {"state": RESUELTO}
    for clase in CLASES:
        valores = [b.get(clase) for b in bloques if b and b.get(clase) is not None]
        total[clase] = sum(valores) if valores else None
        total[clase + "Missing"] = sum(
            1 for b in bloques if b and b.get(clase) is None)
    if any(total[c] is None for c in CLASES) or any(
            total[c + "Missing"] for c in CLASES):
        total["state"] = SIN_ATRIBUIR
    return total


def como_texto(ms):
    """Milisegundos como los lee una persona. None es `sin resolver`, no `0m`."""
    if ms is None:
        return "sin resolver"
    segundos = int(ms) // 1000
    horas, resto = divmod(segundos, 3600)
    minutos, seg = divmod(resto, 60)
    if horas:
        return "%dh %02dm" % (horas, minutos)
    if minutos:
        return "%dm %02ds" % (minutos, seg)
    return "%ds" % seg
