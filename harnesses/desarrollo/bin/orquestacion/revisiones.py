"""Las REVIEW normativas: lo que no se puede reducir a un check sin mentir.

G2 exige adoptar las buenas practicas reconocidas de cada tecnologia. Eso pide decidir que
practicas existen, cuales aplican a esta version, si la implementacion las adopto y si un
apartamiento esta justificado — cuatro preguntas, ninguna con respuesta booleana. Escribir
`goodPractices() == true` seria una funcion que se lee autoritativa y no comprueba nada.

🔴 **La estructura se valida siempre; el juicio no.** Que el schema valide, que este la tupla
normativa, que cada hallazgo referencie evidencia que exista y que los agentes esten
declarados en el registro es codigo y se comprueba. Que una practica sea efectivamente una
buena practica de Angular es criterio de quien revisa, y ningun test lo puede contradecir.

🔴 **La opinion de un agente no es evidencia.** Ni la convencion del proyecto: que algo se
haga de una manera no lo vuelve practica reconocida de la industria. Sin al menos una fuente
reconocida, un hallazgo de G2 no sostiene un resultado que cumple.

🔴 **Que evidencia alcanza depende de la pregunta, y por eso se declara por regla.** G2 pregunta
si una practica es reconocida AFUERA, asi que exige una fuente reconocida y la implementacion del
proyecto no le alcanza. D3 pregunta como esta hecho ESTE sistema, y ahi la unica evidencia que
contesta es la implementacion: una guia de Angular no prueba que este codigo este bien disenado.
La tabla vive en `EXIGENCIA` y el default es el de G2, el mas estricto: una review nueva es
estricta hasta que alguien decida lo contrario y lo escriba.

🔴 **Lo que NO lo declara el documento de review.** Dejar que quien escribe la revision elija que
evidencia le alcanza es dejar que una revision sin respaldo diga que cumple.

🔴 **Un conflicto de paradigma no es un desvio ni evidencia faltante.** Si la tecnologia elegida
no permite demostrar la obligacion, eso lo resuelve arquitectura o una persona: queda
`TECHNOLOGY_PARADIGM_CONFLICT` y la revision no cumple. Reinterpretar la regla para que entre la
tecnologia que ya se eligio es el atajo que este estado existe para cerrar.

🔴 **Sin evidencia no hay COMPLIANT.** Falta material -> `REVIEW_INCOMPLETE`, que no es un
aprobado. Es la misma regla que ya sostiene `dev-quality-validation`.

🔴 **Una justificacion no aprueba una excepcion.** Se registra y queda
`JUSTIFICATION_PENDING`: la autoridad que aprueba todavia no existe, y el harness no se
arroga el papel.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

SCHEMA = "normative-review.schema.json"

# Las de proyecto NO alcanzan solas para afirmar que una practica es reconocida por la industria.
FUENTES_RECONOCIDAS = ("GCBA_NORMATIVE", "OFFICIAL_TECHNOLOGY_DOCUMENTATION",
                       "FORMAL_STANDARD", "RECOGNIZED_INDUSTRY_GUIDANCE")
FUENTES_DE_PROYECTO = ("PROJECT_IMPLEMENTATION", "PROJECT_ARCHITECTURE", "PROJECT_CONVENTION")

# Y al reves: para saber como esta hecho un sistema, la unica evidencia que contesta es el
# sistema. `PROJECT_CONVENTION` queda afuera tambien aca: que en el proyecto se haga de una
# manera no es evidencia de que ESTE codigo lo haga.
FUENTES_DE_IMPLEMENTACION = ("PROJECT_IMPLEMENTATION", "PROJECT_ARCHITECTURE")

# Las dimensiones de diseño que un hallazgo de D3 puede evaluar. Son dimensiones OPERATIVAS de
# revision y NO requisitos citados de ES0901: el estandar dice una linea y esa linea no enumera
# nada. Citarlas como si fueran la norma seria inventar texto normativo.
#
# 🔴 Un conteo no esta y no puede estar. "El modulo define 240 clases" y "hay tres niveles de
# herencia" son hechos del codigo, no propiedades de su diseño: pueden ser EVIDENCIA de una
# dimension, y entonces la conclusion es sobre la dimension y la firma quien revisa. Sin este
# vocabulario, un hallazgo que solo reporta un conteo entra como si fuera un juicio de diseño.
DIMENSIONES = ("responsibility-encapsulation", "cohesion", "controlled-coupling",
               "abstraction-boundaries", "layer-responsibilities",
               "framework-native-organization", "procedural-concentration",
               "collaboration-maintainability")

# Que le exige cada regla a un hallazgo: que clases de fuente lo sostienen, con que campo se
# pesa un desvio, y como se dice que falta. Una sola tabla y no tres: la exigencia de una regla
# se lee de un renglon.
#
# 🔴 El default es el de G2 a proposito: una review que entre sin fila queda con la exigencia
# mas estricta hasta que alguien decida otra cosa y la escriba.
EXIGENCIA = {
    "G2": {"fuentes": FUENTES_RECONOCIDAS, "eje": "practiceStrength",
           "motivo": "ninguna fuente reconocida respalda la practica",
           "dimensiones": ()},
    "D3": {"fuentes": FUENTES_DE_IMPLEMENTACION, "eje": "materiality",
           "motivo": "ninguna evidencia de la implementacion respalda el hallazgo",
           "dimensiones": DIMENSIONES},
}
POR_DEFECTO = EXIGENCIA["G2"]

MATERIAL = "MATERIAL"
MENOR = "MINOR"
MATERIALIDAD = (MATERIAL, MENOR, "UNRESOLVED")

FUERZA = ("REQUIRED_BY_SOURCE", "RECOMMENDED_BY_SOURCE", "OPTIONAL_BY_SOURCE", "UNRESOLVED")
APLICABILIDAD = ("APPLICABLE", "NOT_APPLICABLE", "UNRESOLVED")

CUMPLE = "COMPLIANT"
CUMPLE_CON_OBSERVACIONES = "COMPLIANT_WITH_OBSERVATIONS"
NO_CUMPLE = "NON_COMPLIANT"
INCOMPLETA = "REVIEW_INCOMPLETE"

CONFLICTO_DE_PARADIGMA = "TECHNOLOGY_PARADIGM_CONFLICT"

NO_INSTALADA = "DECLARED_REVIEW_NOT_INSTALLED"
SCHEMA_INVALIDO = "REVIEW_SCHEMA_INVALID"
EVIDENCIA_INCOMPLETA = "REVIEW_EVIDENCE_INCOMPLETE"
FUENTE_SIN_RESOLVER = "REVIEW_SOURCE_UNRESOLVED"
CONFLICTO = "SOURCE_CONFLICT"
JUSTIFICACION_PENDIENTE = "JUSTIFICATION_PENDING"
SIN_CONTEXTO_DE_VERSION = "REVIEW_VERSION_CONTEXT_MISSING"


class RevisionInvalida(Exception):
    """Una revision mal formada no se interpreta: se rechaza."""


# -- el contrato ---------------------------------------------------------------

def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise RevisionInvalida("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(revision, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise RevisionInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(revision, esquema)


def validar_estructura(revision, desde=None):
    """Lista de problemas estructurales. Vacia es bien formada.

    Nada de esto opina sobre el contenido tecnico: opina sobre si la revision se puede leer,
    discutir y rastrear. Una revision que no cita la fuente de un hallazgo no es una revision
    mas floja — es una opinion con formato de revision.
    """
    problemas = list(validar_schema(revision, desde))

    fuente = (revision or {}).get("source") or {}
    for campo in ("standard", "version", "section", "rule"):
        if not fuente.get(campo):
            problemas.append("%s: la tupla normativa esta incompleta, falta `%s`"
                             % (SCHEMA_INVALIDO, campo))

    sujeto = (revision or {}).get("subject") or {}
    if not sujeto.get("id"):
        problemas.append("%s: la revision no dice sobre que es" % SCHEMA_INVALIDO)

    ids_evidencia = {e.get("evidenceId") for e in (revision or {}).get("evidence") or []}
    for hallazgo in (revision or {}).get("findings") or []:
        refs = hallazgo.get("evidenceRefs") or []
        huerfanas = [r for r in refs if r not in ids_evidencia]
        if huerfanas:
            problemas.append("%s: el hallazgo %s referencia evidencia que no existe: %s"
                             % (SCHEMA_INVALIDO, hallazgo.get("findingId"),
                                ", ".join(sorted(huerfanas))))
        if hallazgo.get("applicability") == "NOT_APPLICABLE" and not hallazgo.get("rationale"):
            problemas.append("%s: el hallazgo %s dice que no aplica y no dice por que. Sin "
                             "motivo es indistinguible de uno que nadie miro"
                             % (SCHEMA_INVALIDO, hallazgo.get("findingId")))
        # El eje con el que se pesa un desvio es obligatorio, y cual es depende de la regla:
        # el schema lleva la union de los dos porque una review usa uno y la otra el otro.
        eje = eje_de(revision)
        if hallazgo.get("applicability") != "NOT_APPLICABLE" and eje not in hallazgo:
            problemas.append("%s: el hallazgo %s no declara `%s`, que es con lo que %s pesa un "
                             "desvio" % (SCHEMA_INVALIDO, hallazgo.get("findingId"), eje,
                                         regla_de(revision) or "esta regla"))
        # Y que dimension del diseño evalua, cuando la regla tiene vocabulario. Sin esto un
        # hallazgo que solo reporta un conteo entra como si fuera un juicio de diseño.
        dimensiones = dimensiones_de(revision)
        if dimensiones and hallazgo.get("applicability") != "NOT_APPLICABLE":
            dim = hallazgo.get("dimension")
            if not dim:
                problemas.append("%s: el hallazgo %s no dice que dimension del diseño evalua. "
                                 "Un conteo no es una dimension: puede ser evidencia de una"
                                 % (SCHEMA_INVALIDO, hallazgo.get("findingId")))
            elif dim not in dimensiones:
                problemas.append("%s: el hallazgo %s declara la dimension `%s`, que no esta en "
                                 "el vocabulario de %s"
                                 % (SCHEMA_INVALIDO, hallazgo.get("findingId"), dim,
                                    regla_de(revision) or "esta regla"))

    problemas.extend(validar_agentes(revision, desde))
    return problemas


def validar_agentes(revision, desde=None):
    """El dueno y los de apoyo tienen que estar declarados. La revision no crea agentes."""
    from . import registro_agentes as reg
    revisor = (revision or {}).get("reviewer") or {}
    nombres = [revisor.get("ownerAgent")] + list(revisor.get("supportingAgents") or [])
    try:
        registro = reg.cargar(desde or __file__)
    except reg.RegistroInvalido:
        return ["no se pudo leer el registro de agentes: las referencias no se validaron"]
    declarados = {a.get("id") for a in registro.get("agents", [])}
    return ["%s: la revision nombra a %s, que el registro de agentes no declara"
            % (SCHEMA_INVALIDO, n) for n in nombres if n and n not in declarados]


# -- la evidencia --------------------------------------------------------------

def fuentes_de(revision, ids):
    """Las clases de fuente de las evidencias referenciadas por un hallazgo."""
    por_id = {e.get("evidenceId"): e for e in (revision or {}).get("evidence") or []}
    return [por_id[i].get("sourceType") for i in (ids or []) if i in por_id]


def regla_de(revision):
    """La regla de la que sale la revision. Es la que decide que evidencia se le exige."""
    return ((revision or {}).get("source") or {}).get("rule") or ""


def fuentes_exigidas(revision):
    """Que clases de fuente sostienen un hallazgo de ESTA regla.

    No lo decide el documento: lo decide la tabla. Y una regla sin fila queda con la exigencia
    de G2, que es la mas estricta.
    """
    return exigencia_de(revision)["fuentes"]


def exigencia_de(revision):
    """El renglon de la tabla que le toca a esta regla."""
    return EXIGENCIA.get(regla_de(revision), POR_DEFECTO)


def eje_de(revision):
    """Con que campo pesa un desvio esta regla: la fuerza de la fuente o la materialidad."""
    return exigencia_de(revision)["eje"]


def dimensiones_de(revision):
    """El vocabulario de dimensiones de esta regla, o vacio si no exige ninguna."""
    return exigencia_de(revision).get("dimensiones") or ()


def tiene_fuente_reconocida(revision, hallazgo):
    """Si el hallazgo se apoya en al menos una fuente que alcance PARA SU REGLA.

    En G2 la convencion del proyecto y la implementacion son evidencia de lo que el proyecto
    HACE, no de lo que la industria reconoce, y solas no alcanzan. En D3 es al reves: la
    pregunta es como esta hecho este sistema, y una guia externa no la contesta.
    """
    clases = fuentes_de(revision, hallazgo.get("evidenceRefs"))
    exigidas = fuentes_exigidas(revision)
    return any(c in exigidas for c in clases)


def conflicto_de_fuentes(revision, hallazgo):
    """Dos fuentes que alcanzan y afirman cosas distintas sobre el mismo hallazgo.

    No se elige una: se devuelven las dos. Quedarse con la que hace pasar la implementacion
    es el sesgo mas barato que puede tener un revisor, y no deja rastro.
    """
    por_id = {e.get("evidenceId"): e for e in (revision or {}).get("evidence") or []}
    exigidas = fuentes_exigidas(revision)
    reconocidas = [por_id[i] for i in (hallazgo.get("evidenceRefs") or [])
                   if i in por_id and por_id[i].get("sourceType") in exigidas]
    afirmaciones = {e.get("claim") for e in reconocidas}
    if len(afirmaciones) > 1:
        return {"state": CONFLICTO,
                "sources": [{"evidenceId": e.get("evidenceId"),
                             "sourceType": e.get("sourceType"),
                             "reference": e.get("reference"),
                             "claim": e.get("claim")} for e in reconocidas]}
    return None


def falta_contexto_de_version(revision, hallazgo):
    """Si el hallazgo declara que su guia depende de la version y el sujeto no la trae.

    Lo declara el hallazgo, no se deduce: saber que guias cambian entre versiones es criterio de
    quien revisa. Lo que es codigo es que, dicho eso, sin version no se juzga.
    """
    if hallazgo.get("versionDependent") is not True:
        return False
    return not ((revision or {}).get("subject") or {}).get("version")


# -- el resultado --------------------------------------------------------------

def resolver(revision, desde=None):
    """El resultado de una revision, derivado de sus hallazgos y de su evidencia.

    Devuelve `{result, states, issues}`. El resultado NO lo declara quien revisa: se calcula,
    por la misma razon por la que el estado de un plan se calcula — dejar que lo declare quien
    lo escribe es dejar que una revision sin evidencia diga que cumple.
    """
    problemas = validar_estructura(revision, desde)
    estados = []

    if problemas:
        return {"result": INCOMPLETA, "states": [SCHEMA_INVALIDO], "issues": problemas,
                "source": dict((revision or {}).get("source") or {})}

    hallazgos = (revision or {}).get("findings") or []
    if not hallazgos:
        return {"result": INCOMPLETA, "states": [EVIDENCIA_INCOMPLETA],
                "issues": ["la revision no tiene ningun hallazgo"],
                "source": dict(revision.get("source") or {})}

    incompleta = False
    no_cumple = False
    observaciones = False
    issues = []

    for h in hallazgos:
        conflicto = conflicto_de_fuentes(revision, h)
        if conflicto:
            estados.append(CONFLICTO)
            issues.append("%s: %s" % (h.get("findingId"), CONFLICTO))
            incompleta = True

        if falta_contexto_de_version(revision, h):
            # 🔴 Antes que la aplicabilidad: sin la version, tampoco se puede afirmar que la
            # guia NO aplica. Un "no aplica" dicho sin saber la version es el mismo juicio a
            # ciegas que un "cumple".
            estados.append(SIN_CONTEXTO_DE_VERSION)
            issues.append("%s: la guia depende de la version y el sujeto no dice que version "
                          "es" % h.get("findingId"))
            incompleta = True
            continue

        if h.get("applicability") == "UNRESOLVED":
            estados.append(FUENTE_SIN_RESOLVER)
            incompleta = True
            continue
        if h.get("applicability") == "NOT_APPLICABLE":
            continue

        if h.get("status") == "EVIDENCE_MISSING":
            estados.append(EVIDENCIA_INCOMPLETA)
            incompleta = True
            continue
        if h.get("status") == "JUSTIFICATION_PENDING":
            estados.append(JUSTIFICACION_PENDIENTE)
            issues.append("%s: hay una justificacion registrada y nadie la aprobo todavia"
                          % h.get("findingId"))
            incompleta = True
            continue
        if h.get("status") == CONFLICTO_DE_PARADIGMA:
            # 🔴 No es un desvio ni evidencia faltante: es un problema que resuelve
            # arquitectura o una persona. No vuelve la regla NOT_APPLICABLE, no aprueba una
            # excepcion y no llega a COMPLIANT. El harness no se arroga ese papel.
            estados.append(CONFLICTO_DE_PARADIGMA)
            issues.append("%s: la tecnologia elegida y la obligacion de la regla estan en "
                          "conflicto, y eso lo resuelve arquitectura o una persona"
                          % h.get("findingId"))
            incompleta = True
            continue

        if not tiene_fuente_reconocida(revision, h):
            # En G2: solo opinion del agente o solo convencion. En D3: nada que muestre como
            # esta hecho el sistema.
            estados.append(EVIDENCIA_INCOMPLETA)
            issues.append("%s: %s" % (h.get("findingId"), exigencia_de(revision)["motivo"]))
            incompleta = True
            continue

        eje = eje_de(revision)
        peso = h.get(eje)
        if peso is None or peso == "UNRESOLVED":
            # Un desvio sin su eje declarado NO se resuelve hacia el lado suave: elegir
            # "habra sido menor" por defecto es como un NON_COMPLIANT se convierte en una
            # observacion sin que nadie lo decida.
            estados.append(FUENTE_SIN_RESOLVER)
            issues.append("%s: falta `%s`, que es con lo que esta regla pesa un desvio"
                          % (h.get("findingId"), eje))
            incompleta = True
            continue

        if h.get("status") == "DEVIATION":
            if peso in ("REQUIRED_BY_SOURCE", MATERIAL):
                no_cumple = True
            else:
                observaciones = True

    if incompleta:
        resultado = INCOMPLETA
    elif no_cumple:
        resultado = NO_CUMPLE
    elif observaciones:
        resultado = CUMPLE_CON_OBSERVACIONES
    else:
        resultado = CUMPLE

    return {"result": resultado, "states": sorted(set(estados)), "issues": issues,
            "source": dict(revision.get("source") or {})}
