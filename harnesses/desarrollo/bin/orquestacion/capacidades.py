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

🔴 Pero un hueco es solo lo que NINGUN adapter soporta (Wave 5). Una capacidad soportada cuya
integracion esta caida -AUTHENTICATION_FAILED, CONNECTION_FAILED, sin validar- no se construye:
se revalida la integracion. Mandarla a dev-tool-builder es pedir una tool para leer issues de
Jira porque el token vencio.
"""
from integraciones import registro as registro_de_capacidades
from . import roster

DERIVA_A = "dev-tool-builder"
TEMPORAL = "TEMPORARY"


def disponibles(registro, desde=None):
    """Todo lo que se puede usar hoy: integraciones validadas mas capacidades del runtime."""
    del_registro = sorted(c for c, estado in (registro or {}).items() if estado == "ENABLED")
    locales = roster.capacidades_locales(desde or __file__)
    return sorted(set(del_registro) | set(locales))


def _pedidas(unidades):
    pedidas = {}
    for unidad in unidades:
        for capacidad in unidad.get("requiredCapabilities", []):
            pedidas.setdefault(capacidad, []).append(unidad.get("id", "?"))
    return pedidas


def estado(unidades, registro, desde=None, integraciones=None):
    """capabilityStatus: por cada capacidad pedida, si se puede usar y si no, por que.

    `registro` es el bloque `capacidades` del registro escrito; `integraciones`, su bloque
    `integraciones` (el estado de cada una). Solo lo NOT_SUPPORTED lleva a quien se deriva.
    """
    locales = roster.capacidades_locales(desde or __file__)
    salida = []
    for capacidad, unidades_ in sorted(_pedidas(unidades).items()):
        d = registro_de_capacidades.disponibilidad(capacidad, registro, integraciones, locales)
        no_soportada = d["availability"] == registro_de_capacidades.NO_SOPORTADA
        d.update(workUnits=sorted(unidades_), derivedTo=DERIVA_A if no_soportada else None,
                 toolClass=TEMPORAL if no_soportada else None)
        salida.append(d)
    return salida


def resolver(unidades, registro, desde=None, integraciones=None):
    """Devuelve (capacidades, huecos).

    `unidades` son las de la propuesta: cada una con su `id` y sus `requiredCapabilities`.
    El hueco nombra que unidad pidio la capacidad, que es lo que permite decidir si vale la
    pena construir la tool o partir la unidad de otra forma. Un hueco es solo lo que no se
    soporta: lo soportado y caido falta igual, pero no se deriva.
    """
    tengo = set(disponibles(registro, desde))
    pedidas = _pedidas(unidades)

    hay = sorted(c for c in pedidas if c in tengo)
    faltan = sorted(c for c in pedidas if c not in tengo)

    huecos = []
    for d in estado(unidades, registro, desde, integraciones):
        if d["derivedTo"] is None:
            continue
        huecos.append({
            "capability": d["capabilityId"],
            "workUnits": d["workUnits"],
            "derivedTo": d["derivedTo"],
            # Una tool generada no nace permanente: se promueve despues de usarse bien.
            "toolClass": d["toolClass"],
        })

    return {"available": hay, "missing": faltan}, huecos
