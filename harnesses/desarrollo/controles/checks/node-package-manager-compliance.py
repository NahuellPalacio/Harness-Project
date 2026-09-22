"""Check normativo: en Node, el administrador de paquetes es el permitido y no hay otro activo.

    source: ES0901 / 6.3 / 7.1 / P1   ·   clausula: P1.node

Contesta sobre **con que se administran las dependencias en el camino gobernado**, no sobre que
archivos hay en el repositorio. Un lockfile viejo que quedo de una migracion y el lockfile que el
build usa todos los dias se ven igual desde afuera, y confundirlos rompe la regla en las dos
direcciones: falla sobre un proyecto correcto, o aprueba uno que instala con otra cosa en el
pipeline.

🔴 **Se compara contra EL PERMITIDO, no contra una lista de prohibidos.** El estandar nombra uno y
dice que no estan permitidas las alternativas. Una lista de prohibidos envejece y deja entrar a la
numero cuatro; adentro de este archivo no hay ninguna, y todo administrador activo que no sea el
permitido es una alternativa sin que nadie tenga que agregarlo.

🔴 **Lo historico se investiga: ni se ignora ni falla solo.** Un artefacto de otro administrador
declarado historico no es un incumplimiento y tampoco es nada — es una pregunta: *¿esta vivo en el
build gobernado?*. El check la deja escrita en vez de contestarla.

    activo y es el permitido           cumple
    activo y no es el permitido        FAIL
    historico, con su investigacion    observacion. No falla y no desaparece
    historico sin investigar           PARTIAL: la pregunta quedo abierta
    sin declarar si esta activo        NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED
    dos activos distintos              NODE_PACKAGE_MANAGER_CONFLICT

🔴 **`NOT_RELEVANT` no es `NOT_APPLICABLE`.** P1 es ALWAYS: un proyecto sin superficie Node sigue
debiendo frameworks homologados. Lo que no tiene sujeto es ESTA CLAUSULA, y eso se dice con otra
palabra a proposito.

🔴 **Este modulo no valida la version de nada.** Que version de Node corresponde es de G1, y el
estandar no fija una version del administrador: no hay un numero adentro de este archivo.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

CONTROL = "node-package-manager-compliance"
TIPO = "CHECK"
REGLA = "P1"
CLAUSULA = "P1.node"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "P1"}

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_RELEVANTE = "NOT_RELEVANT"
SIN_CONTEXTO = "NODE_TECHNOLOGY_CONTEXT_UNRESOLVED"
SIN_EVIDENCIA = "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED"
CONFLICTO = "NODE_PACKAGE_MANAGER_CONFLICT"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Ocho, y el unico que aprueba es PASA. 🔴 `NOT_APPLICABLE` NO esta: P1 es ALWAYS, y lo que puede
# no tener sujeto es la clausula.
ESTADOS = (PASA, FALLA, PARCIAL, NO_RELEVANTE, SIN_CONTEXTO, SIN_EVIDENCIA, CONFLICTO,
           SIN_OBJETIVO)

# El unico que el estandar nombra como permitido. Es el unico nombre de administrador de paquetes
# que hay en este archivo, y es a proposito.
PERMITIDO = "NPM"

# De donde puede salir la evidencia del camino de dependencias gobernado. La lista dice que fuentes
# son defendibles; el valor lo declara el proyecto.
FUENTES = ("REPOSITORY_MANIFEST", "LOCKFILE", "PACKAGE_MANAGER_METADATA", "CI_PIPELINE",
           "CONTAINER_BUILD", "BUILD_SCRIPT", "BUILD_DOCUMENTATION", "HUMAN_CONFIRMATION")

ALTERNATIVO = "ALTERNATIVE_PACKAGE_MANAGER_ACTIVE"
SIN_INVESTIGAR = "HISTORICAL_ARTIFACT_NOT_INVESTIGATED"
ACTIVIDAD_SIN_DECLARAR = "PACKAGE_MANAGER_ACTIVITY_UNDECLARED"
SIN_ORIGEN = "PACKAGE_MANAGER_SOURCE_UNDECLARED"

AGENTES = ("dev-architecture", "dev-devops")


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada."""
    return str(valor or "").strip()


def _nombre(entrada):
    """El administrador que una entrada declara, normalizado para comparar."""
    return declarado((entrada or {}).get("manager")).upper()


def entradas(caso):
    """Las evidencias de administrador de paquetes declaradas."""
    return list((caso or {}).get("packageManagers") or [])


def activas(caso):
    """Las que el proyecto declara vivas en el camino gobernado."""
    return [e for e in entradas(caso) if e.get("active") is True]


def historicas(caso):
    """Las que el proyecto declara que ya no participan del build gobernado."""
    return [e for e in entradas(caso) if e.get("active") is False]


def relevante(caso):
    """(relevante, motivo_o_estado) de la clausula de Node para este proyecto.

    🔴 Sale del inventario de tecnologias que ya existe, no de una senal nueva. Node es una rama
    interna de evaluacion de P1 y no una regla normativa aparte.
    """
    contexto = (caso or {}).get("nodeContext") or {}
    if contexto.get("complete") is not True:
        return False, SIN_CONTEXTO
    if not [s for s in contexto.get("surfaces") or [] if declarado(s)]:
        return False, NO_RELEVANTE
    return True, ""


def _evaluar_entrada(entrada):
    """El estado de una evidencia de administrador de paquetes."""
    salida = {"id": declarado(entrada.get("id")), "manager": _nombre(entrada),
              "active": entrada.get("active")}

    if entrada.get("source") not in FUENTES:
        salida.update({"state": SIN_EVIDENCIA, "reason": SIN_ORIGEN,
                       "detail": "la evidencia no declara de donde sale"})
        return salida
    if not declarado(entrada.get("reference")):
        salida.update({"state": SIN_EVIDENCIA, "reason": SIN_ORIGEN,
                       "detail": "la evidencia no dice donde esta"})
        return salida
    if not _nombre(entrada):
        salida.update({"state": SIN_EVIDENCIA, "reason": SIN_EVIDENCIA,
                       "detail": "la evidencia no dice que administrador de paquetes es"})
        return salida

    # 🔴 Lo que no declara si esta activo NO se da por muerto. Dar por historico un lockfile que
    # nadie apago es el defecto que esta clausula busca, del lado que aprueba de mas.
    if not isinstance(entrada.get("active"), bool):
        salida.update({"state": SIN_EVIDENCIA, "reason": ACTIVIDAD_SIN_DECLARAR,
                       "detail": "no se declaro si este camino esta vivo en el build gobernado"})
        return salida

    if entrada.get("active") is True:
        if _nombre(entrada) != PERMITIDO:
            salida.update({"state": FALLA, "reason": ALTERNATIVO,
                           "detail": "el camino de dependencias activo usa un administrador que "
                                     "no es el permitido"})
            return salida
        salida.update({"state": PASA, "reason": "",
                       "detail": "el camino activo usa el administrador permitido"})
        return salida

    # Historico. No falla; lo que decide es si alguien lo miro.
    if _nombre(entrada) == PERMITIDO:
        salida.update({"state": PASA, "reason": "",
                       "detail": "un camino historico del administrador permitido"})
        return salida
    if entrada.get("investigated") is not True:
        salida.update({"state": PARCIAL, "reason": SIN_INVESTIGAR,
                       "detail": "hay un artefacto de otro administrador declarado historico y "
                                 "sin investigar: no falla, y la pregunta queda abierta"})
        return salida
    salida.update({"state": PASA, "reason": "",
                   "detail": "un artefacto historico de otro administrador, investigado y fuera "
                             "del build gobernado"})
    return salida


def evaluar(caso, desde=None):
    """El estado de la clausula de Node, con su motivo y su trazabilidad.

    `caso` trae, ademas del build y el objetivo:

        {"nodeContext": {"complete": bool, "surfaces": [<ids de superficie Node>]},
         "packageManagers": [{"id", "manager", "active", "investigated", "source",
                              "reference"}]}

    🔴 Para un inventario y unos datos fijos, esto devuelve siempre lo mismo.
    """
    salida = {"control": CONTROL, "source": dict(TRAZA), "rule": REGLA, "clause": CLAUSULA,
              "managers": [], "issues": []}

    if not ((caso or {}).get("testTarget") or {}).get("available"):
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo "
                                 "que no se ejecuto no pasa"})
        return salida

    hay, estado = relevante(caso)
    if not hay:
        if estado == NO_RELEVANTE:
            salida.update({"state": NO_RELEVANTE, "reason": NO_RELEVANTE,
                           "detail": "no hay superficie basada en Node en alcance. P1 sigue "
                                     "aplicando: lo que no tiene sujeto es esta clausula"})
        else:
            salida.update({"state": SIN_CONTEXTO, "reason": SIN_CONTEXTO,
                           "detail": "el inventario de tecnologias no esta completo, y sin eso no "
                                     "se sabe si hay una superficie basada en Node"})
        return salida

    salida["nodeSurfaces"] = [declarado(s) for s in
                              ((caso or {}).get("nodeContext") or {}).get("surfaces") or []]

    declaradas = entradas(caso)
    if not declaradas:
        salida.update({"state": SIN_EVIDENCIA, "reason": SIN_EVIDENCIA,
                       "detail": "hay superficie Node y no hay ninguna evidencia del camino de "
                                 "dependencias gobernado"})
        return salida

    evaluadas = [_evaluar_entrada(e) for e in declaradas]
    salida["managers"] = evaluadas
    salida["historical"] = [e["id"] for e in evaluadas if e["active"] is False]

    # 🔴 El conflicto se mira antes que el resto: dos caminos activos distintos no se resuelven
    # eligiendo uno, y elegir el que deja el resultado mas corto es el sesgo mas barato que hay.
    nombres = sorted({_nombre(e) for e in activas(caso) if _nombre(e)})
    salida["activeManagers"] = nombres
    if len(nombres) > 1:
        salida.update({"state": CONFLICTO, "reason": CONFLICTO,
                       "detail": "hay dos administradores de paquetes declarados activos y "
                                 "distintos; no se elige uno"})
        return salida

    estados = [e["state"] for e in evaluadas]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": ALTERNATIVO})
    elif SIN_EVIDENCIA in estados:
        salida.update({"state": SIN_EVIDENCIA, "reason": next(
            e["reason"] for e in evaluadas if e["state"] == SIN_EVIDENCIA)})
    elif not nombres:
        salida.update({"state": SIN_EVIDENCIA, "reason": SIN_EVIDENCIA,
                       "detail": "ninguna evidencia declara un camino activo, asi que no se sabe "
                                 "con que se administran las dependencias hoy"})
    elif PARCIAL in estados:
        salida.update({"state": PARCIAL, "reason": next(
            e["reason"] for e in evaluadas if e["state"] == PARCIAL)})
    else:
        salida.update({"state": PASA, "reason": ""})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills y no las modifica.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTES[1], "dev-ci-cd"), (AGENTES[1], "dev-devops-implementation"),
               (AGENTES[0], "dev-architecture-analysis"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
