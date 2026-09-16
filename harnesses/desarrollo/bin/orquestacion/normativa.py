"""Las reglas de ES0901 §7.1 como dato, y cuales aplican a un plan.

🔴 Una regla sin `conditions` declaradas NUNCA se cita como aplicable. Las 26 reglas entran
con su id, su texto y su pagina, y la clasificacion -owners, skills, policies, checks- entra
vacia: clasificarlas es trabajo de criterio que alguien tiene que validar contra el
estandar, y una matriz inventada se lee igual de autoritativa que una real.

La consecuencia se acepta y se declara: hoy el plan cita pocas reglas, y dice cuantas quedan
sin clasificar para que el hueco se vea en cada corrida.
"""
import io
import json

from . import roster

_CACHE = {}


def cargar(desde=None):
    """El catalogo normativo. Vacio si no se encontro."""
    if "normativa" in _CACHE:
        return _CACHE["normativa"]
    ruta = roster.ruta_de_regla("es0901-7.1.json", desde or __file__)
    datos = {"rules": []}
    if ruta:
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                datos = json.load(f)
        except (ValueError, OSError):
            datos = {"rules": []}
    _CACHE["normativa"] = datos
    return datos


def reglas(desde=None):
    return cargar(desde).get("rules", [])


def sin_clasificar(desde=None):
    """Las que todavia no tienen condiciones: no se pueden citar."""
    return [r for r in reglas(desde) if not r.get("conditions")]


def aplicables(dominios, desde=None):
    """Los ids de las reglas cuyas condiciones coinciden con el plan.

    Hoy la unica condicion soportada es `domains`. Se sostiene a proposito: agregar un
    lenguaje de condiciones antes de tener una sola regla clasificada seria disenar para un
    caso que nadie vio.
    """
    salida = []
    for regla in reglas(desde):
        condiciones = regla.get("conditions") or {}
        if not condiciones:
            continue
        exigidos = condiciones.get("domains")
        if exigidos and not (set(exigidos) & set(dominios)):
            continue
        salida.append(regla["id"])
    return sorted(salida)


def aviso_de_matriz(desde=None):
    """Lo que el plan tiene que decir sobre la matriz pendiente, o "" si esta completa."""
    faltan = sin_clasificar(desde)
    todas = reglas(desde)
    if not faltan:
        return ""
    return ("%d de las %d reglas de ES0901 §7.1 estan sin clasificar y por eso no se citan: "
            "la matriz normativa todavia no se construyo." % (len(faltan), len(todas)))
