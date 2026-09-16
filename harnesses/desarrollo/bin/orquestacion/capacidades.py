"""Lo que una unidad de trabajo pide, resuelto contra lo que el harness tiene.

El orquestador piensa en CAPACIDADES, no en tools: una unidad pide `repository.read`, no
`Glob`. Atar el plan al nombre de una tool lo ata a un runtime, y el mismo plan deja de
servir el dia que la misma capacidad la provea otra cosa.

Dos fuentes, y ninguna reemplaza a la otra:

    registro de integraciones  ->  lo que el bootstrap valido contra un servidor
    capacidades locales        ->  lo que da el propio runtime, declarado en el roster

🔴 Lo que no esta en ninguna de las dos es un hueco, y un hueco se DERIVA. No se improvisa
con una tool parecida: ese es exactamente el momento en que un plan empieza a hacer algo
que nadie pidio.
"""
from . import roster

DERIVA_A = "dev-tool-builder"
TEMPORAL = "TEMPORARY"


def disponibles(registro, desde=None):
    """Todo lo que se puede usar hoy: integraciones validadas mas capacidades del runtime."""
    del_registro = sorted(c for c, estado in (registro or {}).items() if estado == "ENABLED")
    locales = roster.capacidades_locales(desde or __file__)
    return sorted(set(del_registro) | set(locales))


def resolver(unidades, registro, desde=None):
    """Devuelve (capacidades, huecos).

    `unidades` son las de la propuesta: cada una con su `id` y sus `requiredCapabilities`.
    El hueco nombra que unidad pidio la capacidad, que es lo que permite decidir si vale la
    pena construir la tool o partir la unidad de otra forma.
    """
    tengo = set(disponibles(registro, desde))
    pedidas = {}
    for unidad in unidades:
        for capacidad in unidad.get("requiredCapabilities", []):
            pedidas.setdefault(capacidad, []).append(unidad.get("id", "?"))

    hay = sorted(c for c in pedidas if c in tengo)
    faltan = sorted(c for c in pedidas if c not in tengo)

    huecos = []
    for capacidad in faltan:
        huecos.append({
            "capability": capacidad,
            "workUnits": sorted(pedidas[capacidad]),
            "derivedTo": DERIVA_A,
            # Una tool generada no nace permanente: se promueve despues de usarse bien.
            "toolClass": TEMPORAL,
        })

    return {"available": hay, "missing": faltan}, huecos
