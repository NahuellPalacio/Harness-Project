"""Las reglas de ES0901 §7.1 como dato, y cuales aplican a un plan.

Dos archivos, y cada uno contesta una pregunta distinta:

    es0901-7.1.json                   el TEXTO citado y la pagina. La fuente
    es0901-7.1-normative-matrix.json  la clasificacion. La resuelve `matriz.py`

`aplicables` y `aviso_de_matriz` siguen contestando lo mismo que antes -son lo que el plan
ya consume en `applicableStandards`- y al lado esta `resolucion`, que devuelve el bloque
normativo completo. Cambiarle el tipo a un campo que alguien ya lee es romper a distancia.

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


# -- la clasificacion, que vive en la matriz -----------------------------------

def resolucion(senales, desde=None):
    """El bloque normativo de una unidad: que aplica, que no, y que no se sabe.

    Las senales entran de dos formas y las dos siguen andando: booleanos explicitos -la forma
    vieja- o documentos de senal con su evidencia y su productor. Lo que no esta no se deduce:
    la regla queda `APPLICABILITY_UNRESOLVED` con la senal que le falta escrita al lado. La
    evidencia todavia la junta nadie, asi que una unidad real sale casi toda sin resolver — y
    eso es lo que hay, no un defecto que convenga disimular convirtiendo lo ausente en "no
    aplica".

    Lo resuelto viaja al lado, en `signals`: quien lee la unidad ve el valor, su estado y de
    donde salio, sin tener que confiar en un booleano que nadie firmo.
    """
    from . import matriz
    from . import senales as modulo_senales
    try:
        booleanos, resueltas = modulo_senales.normalizar(senales, desde)
    except modulo_senales.SenalInvalida:
        # Sin contrato de senal no se interpreta ninguna: quedan todas sin resolver.
        booleanos, resueltas = {}, {}
    try:
        bloque = matriz.resolver(booleanos, None, desde)
    except matriz.MatrizInvalida:
        # Fallo cerrado: sin matriz no se clasifica nada, y se dice.
        bloque = {"standard": {}, "applicableRules": [], "notApplicableRules": [],
                  "unresolvedRules": [], "declaredPolicies": [], "declaredChecks": [],
                  "evidence": {"signals": {}}}
    bloque["signals"] = resueltas
    bloque["standards"] = {bloque.get("standard", {}).get("id") or "ES0901": _sin_senales(bloque)}

    # 🔴 ES0902 se suma AL LADO, nunca encima. Todo lo de arriba sigue siendo lo de ES0901 y
    # conserva su tipo: quien ya lee `applicableRules` no se entera de que hay un segundo
    # estandar. Cambiarle el tipo a un campo que alguien ya lee es romper a distancia, y es la
    # regla que este modulo declara desde que existe.
    from . import seguridad
    try:
        bloque["standards"][seguridad.ESTANDAR] = seguridad.resolver(booleanos, None, desde)
    except seguridad.SeguridadInvalida as e:
        # Un estandar roto no se lleva puesto al otro. Se dice cual, y ES0901 sigue resolviendo.
        bloque["standards"][seguridad.ESTANDAR] = {
            "standard": {"id": seguridad.ESTANDAR, "version": None, "section": None,
                         "sourceDate": None},
            "applicableRules": [], "notApplicableRules": [], "unresolvedRules": [],
            "declaredPolicies": [], "declaredChecks": [], "declaredReviews": [],
            "evidence": {"signals": {}}, "error": str(e)}
    return bloque


def _sin_senales(bloque):
    """El bloque de ES0901 sin `signals` ni `standards`: lo que va adentro de `standards`.

    Se copia y no se referencia. Un diccionario que se apunta a si mismo no se serializa, y
    este bloque viaja a un plan en JSON.
    """
    return {k: v for k, v in bloque.items() if k not in ("signals", "standards")}


def estado_de_matriz(desde=None):
    """(estado, errores) de la matriz instalada, o el estado de que no este."""
    from . import matriz
    try:
        return matriz.validar(matriz.cargar(desde), desde)
    except matriz.MatrizInvalida as e:
        return "NORMATIVE_MATRIX_INVALID", [str(e)]
