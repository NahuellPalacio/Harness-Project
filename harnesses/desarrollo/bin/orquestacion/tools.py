"""El contrato de una tool: se valida, se le deriva el riesgo y se le miden los permisos.

Una tool sin contrato valido no se implementa y no se registra. El contrato es lo que
permite decir despues con que permisos, con que alcance y con que riesgo se resolvio una
capacidad, y sin el una capacidad nueva aparece sola en el harness.

Tres reglas que este modulo hace cumplir y que no son opinables:

🔴 **El riesgo sale del contrato, nunca del modelo.** Un perfil low_cost tambien escribe una
tool que borra una base. La derivacion mira side effects, red, secrets y blast radius; el
tier con el que se construyo no entra en la cuenta. Costo y peligro son dos dimensiones.

🔴 **El riesgo declarado no puede ser menor que el derivado.** Mas alto se respeta, mas bajo
se rechaza. Sin esa asimetria, `riskLevel` es un campo que se completa para pasar la
compuerta.

🔴 **Una capacidad sin permisos declarados es un hueco, no un permiso.** Lo que no esta en
`permisos-por-capacidad.json` no se concede por defecto: se devuelve MISSING_CONTEXT. Es la
misma regla que el resto del bloque — lo que el documento declara como hueco se trata como
hueco.
"""
import importlib.util
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

VERSION_CONTRATO = "tool-contract/1.0"
CONSTRUCTOR = "dev-tool-builder"

SIDE_EFFECTS = ("READ_ONLY", "MUTATING", "DESTRUCTIVE")
RIESGOS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

LIFECYCLE = ("EXPERIMENTAL", "TEMPORARY", "PROMOTION_CANDIDATE", "APPROVED",
             "DEPRECATED", "RETIRED")

# Con que estado nace una tool generada. APPROVED no esta, y no por olvido: una tool que se
# aprueba a si misma por haber pasado sus propios tests es la misma trampa que un agente que
# escribe su veredicto.
AL_NACER = ("EXPERIMENTAL", "TEMPORARY")

TRANSICIONES = {
    "EXPERIMENTAL": ("TEMPORARY", "PROMOTION_CANDIDATE", "RETIRED"),
    "TEMPORARY": ("PROMOTION_CANDIDATE", "DEPRECATED", "RETIRED"),
    "PROMOTION_CANDIDATE": ("APPROVED", "TEMPORARY", "RETIRED"),
    "APPROVED": ("DEPRECATED", "RETIRED"),
    "DEPRECATED": ("RETIRED",),
    "RETIRED": (),
}

# El salto a APPROVED no lo da quien construyo. Es la regla del harness entero.
NO_PUEDEN_APROBAR = (CONSTRUCTOR,)

# Lo que hay que poder mostrar para pasar a PROMOTION_CANDIDATE. Falta uno solo y no pasa:
# una evidencia parcial es la forma en que una tool temporal se vuelve permanente sin que
# nadie lo decida.
EVIDENCIA_PARA_PROMOVER = ("ejecucion", "tests", "contrato", "seguridad", "permisos",
                           "blastRadius")

ETAPAS_PIPELINE = ("static", "unit", "contract", "security", "sandbox", "capability")
RESULTADOS_ETAPA = ("PASS", "FAIL", "NOT_RUN")


class ToolInvalida(Exception):
    """Algo que impide que la tool exista. Nunca se degrada a aviso."""


# -- schema --------------------------------------------------------------------

def _armador():
    """`contexto-armar.py`, que trae el validador de subconjunto. Su nombre tiene un guion."""
    ruta = rutas.localizar(("bin", "contexto-armar.py"), __file__)
    if ruta is None:
        return None
    spec = importlib.util.spec_from_file_location("contexto_armar_tools", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def cargar_schema(nombre="tool-contract.schema.json"):
    ruta = rutas.localizar(("schemas", nombre), __file__)
    if ruta is None:
        raise ToolInvalida(
            "no esta %s. Una tool no se valida contra un schema que no esta." % nombre)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def hash_de_contrato(contrato):
    """El sha256 canonico del contrato. Lo calcula el mismo armador que el del contexto."""
    armador = _armador()
    if armador is None:
        raise ToolInvalida(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el hash canonico.")
    return armador.hash_de(contrato)


def validar_contrato(contrato):
    """Lista de errores contra tool-contract/1.0. Vacia es valido."""
    armador = _armador()
    if armador is None:
        raise ToolInvalida(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    return armador.validar(contrato, esquema)


# -- riesgo --------------------------------------------------------------------

def _al_menos(actual, piso):
    return actual if RIESGOS.index(actual) >= RIESGOS.index(piso) else piso


def derivar_riesgo(contrato):
    """El riesgo que el contrato justifica por si solo.

    No mira quien lo escribio ni con que modelo. Mira lo unico que se puede contrastar
    despues: que hace, con que permisos, si sale a la red, si toca secretos y hasta donde
    llega si sale mal.
    """
    efectos = contrato.get("sideEffects")
    radio = contrato.get("blastRadius") or {}
    alcance = radio.get("scope")
    produccion = bool(radio.get("productionImpact"))
    muta = efectos in ("MUTATING", "DESTRUCTIVE")

    riesgo = "LOW"
    if muta:
        riesgo = _al_menos(riesgo, "MEDIUM")
    if contrato.get("networkAccess"):
        riesgo = _al_menos(riesgo, "MEDIUM")
    if contrato.get("secretsRequired"):
        riesgo = _al_menos(riesgo, "HIGH")
    if alcance in ("external-system", "organization"):
        riesgo = _al_menos(riesgo, "HIGH")
    if produccion:
        # Leer produccion ya es serio; modificarla es otra cosa.
        riesgo = _al_menos(riesgo, "CRITICAL" if muta else "HIGH")
    if efectos == "DESTRUCTIVE":
        riesgo = "CRITICAL"
    return riesgo


def controlar_riesgo(contrato):
    """Errores si el riesgo declarado esta por debajo del derivado."""
    declarado = contrato.get("riskLevel")
    if declarado not in RIESGOS:
        return ["riskLevel: `%s` no es un nivel de riesgo" % declarado]
    derivado = derivar_riesgo(contrato)
    if RIESGOS.index(declarado) < RIESGOS.index(derivado):
        return ["riskLevel: declara %s y el contrato justifica %s. Declarar de menos no baja "
                "el riesgo, lo esconde." % (declarado, derivado)]
    return []


def exige_aprobacion_humana(contrato):
    """Si esta tool no se habilita sin que una persona decida.

    Dos causas independientes: el nivel CRITICAL y el efecto DESTRUCTIVE. La segunda existe
    aparte porque una tool puede ser destructiva y haber quedado clasificada mas abajo.
    """
    return (contrato.get("riskLevel") == "CRITICAL"
            or derivar_riesgo(contrato) == "CRITICAL"
            or contrato.get("sideEffects") == "DESTRUCTIVE")


# -- permisos ------------------------------------------------------------------

def cargar_permisos(desde=__file__):
    """El mapa capacidad -> permisos minimos. {} si el archivo no esta.

    La ruta la resuelve `roster.ruta_de_regla`, que ya sabe que `reglas/` cuelga a distinta
    altura instalado que en el repositorio. Dos busquedas de rutas con criterios parecidos
    terminan en que un dia una encuentra el archivo y la otra no.
    """
    ruta = roster.ruta_de_regla("permisos-por-capacidad.json", desde)
    if ruta is None:
        return {}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return (json.load(f) or {}).get("capacidades") or {}
    except (OSError, ValueError):
        return {}


def permisos_de(capacidad, desde=__file__):
    """Los permisos minimos de una capacidad, o None si nadie los declaro todavia."""
    entrada = cargar_permisos(desde).get(capacidad)
    if entrada is None:
        return None
    return list(entrada.get("permisos") or [])


def controlar_permisos(contrato, desde=__file__):
    """(estado, detalle). Estado vacio es que los permisos estan bien.

    Dos resultados distintos y no hay que confundirlos: pedir de mas es
    PERMISSION_SCOPE_TOO_BROAD y es culpa del contrato; no saber cuanto es el minimo es
    MISSING_CONTEXT y es un hueco del harness.
    """
    capacidades = list(contrato.get("capabilities") or [])
    if not capacidades:
        return "CONTRACT_INVALID", ["capabilities: una tool sin capacidad no resuelve nada"]

    sin_declarar = [c for c in capacidades if permisos_de(c, desde) is None]
    if sin_declarar:
        return "MISSING_CONTEXT", [
            "permisos-por-capacidad.json no declara el minimo de %s: sin eso no se puede "
            "decir si los permisos pedidos son los justos, y no se conceden por defecto."
            % c for c in sorted(sin_declarar)]

    permitidos = set()
    for c in capacidades:
        permitidos.update(permisos_de(c, desde))
    sobrantes = sorted(set(contrato.get("permissions") or []) - permitidos)
    if sobrantes:
        return "PERMISSION_SCOPE_TOO_BROAD", [
            "%s no hace falta para %s" % (p, ", ".join(sorted(capacidades)))
            for p in sobrantes]
    return "", []


# -- evaluacion completa -------------------------------------------------------

def evaluar(contrato, desde=__file__):
    """El veredicto del contrato antes de que exista una linea de codigo de la tool.

    Devuelve {status, errors, derivedRisk, requiresHumanApproval}. `status` vacio no existe:
    o esta bien y es "OK", o dice exactamente que lo frena.
    """
    errores = validar_contrato(contrato)
    if errores:
        return {"status": "CONTRACT_INVALID", "errors": errores,
                "derivedRisk": "", "requiresHumanApproval": False}

    errores = controlar_riesgo(contrato)
    if errores:
        return {"status": "CONTRACT_INVALID", "errors": errores,
                "derivedRisk": derivar_riesgo(contrato), "requiresHumanApproval": False}

    estado, detalle = controlar_permisos(contrato, desde)
    if estado:
        return {"status": estado, "errors": detalle,
                "derivedRisk": derivar_riesgo(contrato),
                "requiresHumanApproval": exige_aprobacion_humana(contrato)}

    return {"status": "OK", "errors": [],
            "derivedRisk": derivar_riesgo(contrato),
            "requiresHumanApproval": exige_aprobacion_humana(contrato)}


# -- ciclo de vida -------------------------------------------------------------

def transicionar(actual, siguiente, por_quien=""):
    """El estado nuevo, o levanta. La maquina es cerrada: lo que no figura, no pasa."""
    if actual not in LIFECYCLE:
        raise ToolInvalida("`%s` no es un estado de ciclo de vida" % actual)
    if siguiente not in LIFECYCLE:
        raise ToolInvalida("`%s` no es un estado de ciclo de vida" % siguiente)
    if siguiente not in TRANSICIONES[actual]:
        raise ToolInvalida(
            "de %s no se pasa a %s. Desde %s se puede ir a: %s."
            % (actual, siguiente, actual,
               ", ".join(TRANSICIONES[actual]) or "ningun estado"))
    if siguiente == "APPROVED" and por_quien in NO_PUEDEN_APROBAR:
        raise ToolInvalida(
            "%s no puede aprobar una tool: quien construye no aprueba." % por_quien)
    return siguiente


def todas_en_verde(validaciones):
    """Si TODAS las etapas del pipeline pasaron.

    🔴 `NOT_RUN` no cuenta como `PASS`. Una etapa que nadie pudo correr no dice que la tool
    ande: dice que nadie la miro. Hoy `sandbox` sale `NOT_RUN` en toda corrida real porque el
    harness no tiene entorno aislado, y tratar eso como verde seria fabricar el unico dato
    que no tenemos.
    """
    return all((validaciones or {}).get(e) == "PASS" for e in ETAPAS_PIPELINE)


def puede_promover(evidencia, validaciones=None):
    """(bool, faltantes) para pasar a PROMOTION_CANDIDATE.

    Dos condiciones: la evidencia completa y el pipeline entero en verde. Una tool que se
    promueve con una etapa sin correr es una tool reutilizable que nadie termino de mirar.
    """
    faltan = [e for e in EVIDENCIA_PARA_PROMOVER if not (evidencia or {}).get(e)]
    if validaciones is not None and not todas_en_verde(validaciones):
        faltan.extend("pipeline:" + e for e in ETAPAS_PIPELINE
                      if (validaciones or {}).get(e) != "PASS")
    return (not faltan), faltan


# -- versionado ----------------------------------------------------------------

def _mayor(version):
    return version.split(".")[0]


def es_cambio_incompatible(viejo, nuevo):
    """Si el contrato nuevo rompe a quien dependia del viejo.

    Se mira lo que un consumidor puede haber atado: las capacidades que resolvia, las claves
    que devolvia, las que le pedia, los efectos que declaraba y los permisos que usaba.
    """
    if set(viejo.get("capabilities") or []) - set(nuevo.get("capabilities") or []):
        return True
    if set((viejo.get("outputs") or {})) - set((nuevo.get("outputs") or {})):
        return True
    if set((nuevo.get("inputs") or {})) - set((viejo.get("inputs") or {})):
        return True
    if (SIDE_EFFECTS.index(nuevo.get("sideEffects", "READ_ONLY"))
            > SIDE_EFFECTS.index(viejo.get("sideEffects", "READ_ONLY"))):
        return True
    if set(nuevo.get("permissions") or []) - set(viejo.get("permissions") or []):
        return True
    return False


def controlar_version(viejo, nuevo):
    """Errores si un cambio incompatible no subio la major."""
    if not es_cambio_incompatible(viejo, nuevo):
        return []
    if _mayor(nuevo.get("version", "0.0.0")) == _mayor(viejo.get("version", "0.0.0")):
        return ["el contrato cambia de forma incompatible y sigue en la major %s: "
                "eso rompe en silencio a quien dependia de %s@%s."
                % (_mayor(viejo.get("version", "0.0.0")), viejo.get("name"),
                   viejo.get("version"))]
    return []


# -- resolucion: reusar antes que extender, extender antes que crear ------------

ALTERNATIVAS = ("reuse", "extend", "create")


def resolver(capacidad, disponibles, entradas):
    """Que corresponde hacer con una capacidad que alguien pidio.

    `disponibles` son las capacidades que el Capability Registry ya da. `entradas` son las
    del Tool Registry. Crear es lo ultimo, y este modulo lo dice antes de que nadie escriba
    codigo: la tool que no hace falta es la mas barata de todas.
    """
    if capacidad in set(disponibles or []):
        return {"status": "CAPABILITY_ALREADY_EXISTS", "strategy": "", "tool": None,
                "alternativesEvaluated": ["reuse"]}

    for entrada in _seleccionables(entradas):
        if capacidad in (entrada.get("capabilities") or []):
            return {"status": "COMPLETE", "strategy": "REUSE",
                    "tool": {"name": entrada["name"], "version": entrada["version"]},
                    "alternativesEvaluated": ["reuse"]}

    return {"status": "CAPABILITY_GAP", "strategy": "CREATE", "tool": None,
            "alternativesEvaluated": ["reuse", "extend", "create"]}


def _seleccionables(entradas):
    return [e for e in (entradas or [])
            if e.get("lifecycle") not in ("DEPRECATED", "RETIRED")]


def validar_resolucion(resolucion):
    """Errores de una resolucion escrita por el agente.

    Crear sin haber escrito que alternativas se miraron no es una decision, es un default
    con nombre de decision.
    """
    errores = []
    estrategia = (resolucion or {}).get("strategy")
    evaluadas = list((resolucion or {}).get("alternativesEvaluated") or [])
    for a in evaluadas:
        if a not in ALTERNATIVAS:
            errores.append("alternativesEvaluated: `%s` no es una alternativa" % a)
    if estrategia == "CREATE":
        faltan = [a for a in ("reuse", "extend") if a not in evaluadas]
        if faltan:
            errores.append(
                "strategy CREATE sin haber evaluado %s: crear es la ultima opcion y tiene "
                "que constar que se miraron las otras." % " ni ".join(faltan))
    return errores
