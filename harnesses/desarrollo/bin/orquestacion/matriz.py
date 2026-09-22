"""La matriz de ES0901 §7.1: que regla aplica a una unidad, y que todavia no se sabe.

Dos archivos y una union por id de regla:

    es0901-7.1.json                  26 filas: el texto CITADO y la pagina, en espanol
    es0901-7.1-normative-matrix.json 24 filas: modo, senales, agentes, policies, checks

La matriz clasifica; no cita. Lo que trae en ingles es una parafrasis operativa, y una cita
traducida deja de ser una cita (ADR-0011).

🔴 **Desconocido no es falso.** Una senal ausente deja la regla en
`APPLICABILITY_UNRESOLVED`, nunca en `NOT_APPLICABLE`. Convertir lo que falta en "no aplica"
es la forma mas barata de que un plan quede verde: la regla desaparece del reporte y nadie la
busca de nuevo.

🔴 **La matriz no decide que existe.** El orden es registro de agentes -> resolucion
estructural -> matriz. Un agente que la matriz nombra y el registro no declara es
`NORMATIVE_AGENT_REFERENCE_INVALID`: no se crea, no se instala y no se vuelve existente.

🔴 **Un id declarado no finge estar implementado.** Las 36 policies y los 34 checks que la
matriz declara no existen todavia; se reportan `DECLARED_POLICY_NOT_INSTALLED` y
`DECLARED_CHECK_NOT_INSTALLED` y eso NO invalida la matriz. Es el estado correcto de un
harness que clasifico antes de construir.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO = "es0901-7.1-normative-matrix.json"
SCHEMA = "es0901-7.1-normative-matrix.schema.json"

ESTANDAR = "ES0901"
VERSION_ESPERADA = "6.3"
SECCION = "7.1"

MODOS = ("ALWAYS", "CONDITIONAL")
APLICABLE = "APPLICABLE"
NO_APLICABLE = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
EXPRESION_SIN_RESOLVER = "APPLICABILITY_EXPRESSION_UNRESOLVED"

# El inventario exacto. No se deduce del archivo: es contra esto que se compara lo que el
# archivo trae, y por eso puede decir CUAL falta en vez de solo cuantas hay.
INVENTARIO = ("G1", "G2",
              "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
              "P1", "P2", "P3", "P4", "P5", "P6", "P7",
              "C1", "C2", "C3", "C4",
              "M1", "M2", "M3")

_CACHE = {}


class MatrizInvalida(Exception):
    """La matriz no se carga a medias. Se falla cerrado."""


# -- carga y validacion --------------------------------------------------------

def cargar(desde=None):
    """La matriz como dato. Levanta si no esta o si es de otra version del estandar."""
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        raise MatrizInvalida("no esta %s" % ARCHIVO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise MatrizInvalida("%s no se pudo leer: %s" % (ruta, e))
    estado = controlar_version(doc)
    if estado:
        raise MatrizInvalida(estado)
    return doc


def controlar_version(doc):
    """"" si la matriz es del estandar esperado; el estado del error si no."""
    est = doc.get("standard") or {}
    if est.get("id") != ESTANDAR or est.get("version") != VERSION_ESPERADA \
            or est.get("section") != SECCION:
        return ("NORMATIVE_STANDARD_VERSION_MISMATCH: se esperaba %s %s §%s y la matriz dice "
                "%s %s §%s. Las reglas cambian entre versiones, y una clasificacion vieja "
                "aplicada a un estandar nuevo miente sin avisar."
                % (ESTANDAR, VERSION_ESPERADA, SECCION, est.get("id"), est.get("version"),
                   est.get("section")))
    return ""


def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise MatrizInvalida("no esta %s; la matriz no se valida sin su contrato." % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(doc, desde=None):
    """Lista de errores contra el schema. Vacia es valido."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise MatrizInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def validar(doc, desde=None):
    """(estado, errores). `NORMATIVE_MATRIX_VALID` o `NORMATIVE_MATRIX_INVALID`.

    Se falla cerrado: una matriz con una regla de mas, una de menos, una repetida, una
    condicional con varias senales y sin modo de combinacion, o una referencia a un agente
    que no existe no se usa a medias.
    """
    errores = list(validar_schema(doc, desde))

    version = controlar_version(doc)
    if version:
        return "NORMATIVE_STANDARD_VERSION_MISMATCH", [version]

    ids = [r.get("id") for r in doc.get("rules", [])]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        errores.append("reglas repetidas: %s" % ", ".join(repetidos))
    faltan = [i for i in INVENTARIO if i not in ids]
    if faltan:
        errores.append("faltan reglas del inventario: %s" % ", ".join(faltan))
    sobran = sorted(set(ids) - set(INVENTARIO))
    if sobran:
        errores.append("reglas que no son de §7.1: %s" % ", ".join(sobran))

    for regla in doc.get("rules", []):
        modo = (regla.get("applicability") or {}).get("mode")
        if modo not in MODOS:
            errores.append("%s declara el modo `%s`, que no existe" % (regla.get("id"), modo))
        # Dos senales sin `combination` no son una regla a medio escribir que se completa con
        # un AND: el cargador lo dice aca, y el resolvedor igual falla cerrado si le llega.
        aplic = regla.get("applicability") or {}
        senales = aplic.get("signals") or []
        if len(senales) > 1 and not aplic.get("combination"):
            errores.append("%s declara %d senales (%s) y ningun modo de combinacion: falta "
                           "`combination` (ALL o ANY), y ni un AND ni un OR se inventan"
                           % (regla.get("id"), len(senales), ", ".join(senales)))
        for campo in ("policies", "checks"):
            valores = regla.get(campo) or []
            if len(valores) != len(set(valores)):
                errores.append("%s repite un id en %s" % (regla.get("id"), campo))

    errores.extend(validar_referencias(doc, desde))
    return ("NORMATIVE_MATRIX_INVALID" if errores else "NORMATIVE_MATRIX_VALID"), errores


def validar_referencias(doc, desde=None):
    """Errores de referencia a agentes y skills, contra el registro. Nunca los crea."""
    from . import registro_agentes as reg
    try:
        registro = reg.cargar(desde or __file__)
    except reg.RegistroInvalido:
        return ["no se pudo leer el registro de agentes: las referencias no se validaron"]
    agentes = {a.get("id") for a in registro.get("agents", [])}
    skills = {s.get("id") for a in registro.get("agents", []) for s in a.get("skills", [])}
    errores = []
    for regla in doc.get("rules", []):
        for aid in regla.get("primaryAgents", []):
            if aid not in agentes:
                errores.append("NORMATIVE_AGENT_REFERENCE_INVALID: %s nombra a %s, que el "
                               "registro no declara" % (regla.get("id"), aid))
        for sid in regla.get("skills", []) or []:
            if sid not in skills:
                errores.append("NORMATIVE_SKILL_REFERENCE_INVALID: %s nombra a %s, que el "
                               "registro no declara" % (regla.get("id"), sid))
    return errores


# -- consultas -----------------------------------------------------------------

def reglas(doc=None, desde=None):
    return list((doc if doc is not None else cargar(desde)).get("rules", []))


def regla(rule_id, doc=None, desde=None):
    """La regla, o levanta `NORMATIVE_RULE_NOT_FOUND`.

    Una clausula derivada -`P1.node`- HEREDA de su regla madre. El archivo citable partio P1
    en tres porque el estandar agrupa tres clausulas bajo ese id; la matriz clasifica la
    madre y las derivadas toman esa clasificacion. La herencia vive aca y en ningun otro
    lado: nadie mas mira el punto del nombre.
    """
    todas = reglas(doc, desde)
    for r in todas:
        if r.get("id") == rule_id:
            return r
    if "." in (rule_id or ""):
        madre = rule_id.split(".")[0]
        for r in todas:
            if r.get("id") == madre:
                heredada = dict(r)
                heredada["id"] = rule_id
                heredada["inheritedFrom"] = madre
                return heredada
    raise MatrizInvalida("NORMATIVE_RULE_NOT_FOUND: %s" % rule_id)


def trazabilidad(rule_id, doc=None, desde=None):
    """De donde sale la regla. Se conserva entera: el id derivado no alcanza."""
    est = (doc if doc is not None else cargar(desde)).get("standard") or {}
    return {"standard": est.get("id"), "version": est.get("version"),
            "section": est.get("section"), "rule": rule_id}


# -- aplicabilidad -------------------------------------------------------------

def resolver_regla(r, senales):
    """(estado, senales_faltantes) de una regla contra las senales que haya.

    `senales` es un dict de booleanos explicitos. Lo que no esta, no esta: no se deduce, no
    se asume y no se pregunta.
    """
    aplic = r.get("applicability") or {}
    modo = aplic.get("mode")
    if modo == "ALWAYS":
        return APLICABLE, []
    if modo != "CONDITIONAL":
        return EXPRESION_SIN_RESOLVER, []

    declaradas = list(aplic.get("signals") or [])
    if not declaradas:
        return EXPRESION_SIN_RESOLVER, []
    if len(declaradas) > 1 and not aplic.get("combination"):
        # Dos senales sin modo de combinacion declarado: ni AND ni OR se inventan.
        return EXPRESION_SIN_RESOLVER, declaradas

    valores = []
    faltan = []
    for s in declaradas:
        v = (senales or {}).get(s)
        if not isinstance(v, bool):
            faltan.append(s)
        else:
            valores.append(v)
    if faltan:
        return SIN_RESOLVER, faltan

    combinacion = aplic.get("combination", "ALL")
    aplica = all(valores) if combinacion == "ALL" else any(valores)
    return (APLICABLE if aplica else NO_APLICABLE), []


def resolver(senales, doc=None, desde=None):
    """La resolucion normativa completa de una unidad de trabajo.

    Devuelve las aplicables, las que no, las que no se pudieron decidir -con la senal que
    falta- y los ids de policies y checks que exige lo aplicable, con su trazabilidad.
    """
    documento = doc if doc is not None else cargar(desde)
    est = documento.get("standard") or {}
    aplicables, no_aplicables, sin_resolver = [], [], []
    policies, checks, reviews = [], [], []

    for r in reglas(documento):
        estado, faltan = resolver_regla(r, senales)
        rid = r.get("id")
        if estado == APLICABLE:
            aplicables.append(rid)
            for p in r.get("policies") or []:
                if p not in policies:
                    policies.append(p)
            for c in r.get("checks") or []:
                if c not in checks:
                    checks.append(c)
            # `reviews` es opcional: 23 de las 24 filas no lo traen y siguen siendo validas.
            for v in r.get("reviews") or []:
                if v not in reviews:
                    reviews.append(v)
        elif estado == NO_APLICABLE:
            no_aplicables.append(rid)
        else:
            sin_resolver.append({"rule": rid, "reason": estado, "missingSignals": faltan})

    return {
        "standard": {"id": est.get("id"), "version": est.get("version"),
                     "section": est.get("section")},
        "applicableRules": sorted(aplicables, key=_orden),
        "notApplicableRules": sorted(no_aplicables, key=_orden),
        "unresolvedRules": sorted(sin_resolver, key=lambda u: _orden(u["rule"])),
        "declaredPolicies": sorted(policies),
        "declaredChecks": sorted(checks),
        "declaredReviews": sorted(reviews),
        "evidence": {"signals": {k: v for k, v in sorted((senales or {}).items())}},
    }


def _orden(rule_id):
    """El orden del estandar, no el alfabetico: G1, G2, D1... M3."""
    base = (rule_id or "").split(".")[0]
    try:
        return (INVENTARIO.index(base), rule_id)
    except ValueError:
        return (len(INVENTARIO), rule_id)


# -- la frontera con lo que todavia no existe ----------------------------------

def controles_no_instalados(resolucion, policies_instaladas=None, checks_instalados=None,
                            reviews_instaladas=None, desde=None):
    """Que exige lo aplicable y todavia no existe.

    Lo instalado sale del **registro de controles**, no de una lista escrita a mano: el dia
    que una regla instala los suyos, sus ids salen de esta lista sin que la matriz cambie una
    linea. Las dos listas se pueden pasar a mano para probar, y es lo unico para lo que estan.

    No es un error de la matriz que falten: es el estado de un harness que clasifico antes de
    construir.
    """
    if policies_instaladas is None or checks_instalados is None or reviews_instaladas is None:
        from . import controles
        try:
            hay = controles.instalados(None, desde)
        except controles.RegistroInvalido:
            hay = {"POLICY": [], "CHECK": [], "REVIEW": []}
        if policies_instaladas is None:
            policies_instaladas = hay.get("POLICY", [])
        if checks_instalados is None:
            checks_instalados = hay.get("CHECK", [])
        if reviews_instaladas is None:
            reviews_instaladas = hay.get("REVIEW", [])

    salida = []
    for p in resolucion.get("declaredPolicies", []):
        if p not in set(policies_instaladas):
            salida.append({"id": p, "state": "DECLARED_POLICY_NOT_INSTALLED"})
    for c in resolucion.get("declaredChecks", []):
        if c not in set(checks_instalados):
            salida.append({"id": c, "state": "DECLARED_CHECK_NOT_INSTALLED"})
    for v in resolucion.get("declaredReviews", []):
        if v not in set(reviews_instaladas or []):
            salida.append({"id": v, "state": "DECLARED_REVIEW_NOT_INSTALLED"})
    return salida
