"""La politica de consumo y la compuerta humana.

`automatic` NO significa que el orquestador pueda usar cualquier modelo automaticamente.
Significa que elige el tier solo, y que los tiers baratos los ejecuta solo. Lo caro se
detiene y pregunta.

    autoApprove            -> se ejecuta sin preguntar
    requireHumanApproval   -> se arma la solicitud y el plan queda esperando

🔴 La solicitud lleva SIEMPRE una alternativa mas barata. Una compuerta que ofrece "aprobar
o cancelar" fuerza a aprobar: la decision util es entre dos formas de hacer la tarea, no
entre hacerla y no hacerla.

El presupuesto preautorizado es la unica forma de saltear la pregunta, y se gasta: dos
llamadas premium autorizadas son dos, y la tercera vuelve a preguntar.
"""
from . import modelo

POR_DEFECTO = {
    "mode": "automatic",
    "autoApprove": ["low_cost", "standard"],
    "requireHumanApproval": ["reasoning", "premium"],
    "sessionBudget": {"premiumCallsAllowed": 0, "premiumCallsSpent": 0, "maxRetries": 3},
}

CONSUMO = {"low_cost": "BAJO", "standard": "BAJO", "reasoning": "MEDIO", "premium": "ALTO"}


def politica(config):
    """La politica del proyecto, con los defaults abajo. Cambiarla no toca el codigo."""
    dada = (config or {}).get("consumptionPolicy") or {}
    presupuesto = dict(POR_DEFECTO["sessionBudget"])
    presupuesto.update(dada.get("sessionBudget") or {})
    presupuesto.setdefault("premiumCallsSpent", 0)
    return {
        "mode": str(dada.get("mode") or POR_DEFECTO["mode"]),
        "autoApprove": list(dada.get("autoApprove") or POR_DEFECTO["autoApprove"]),
        "requireHumanApproval": list(dada.get("requireHumanApproval")
                                     or POR_DEFECTO["requireHumanApproval"]),
        "sessionBudget": presupuesto,
    }


def techo_sin_aprobacion(politica_):
    """El tier mas alto que se puede usar sin preguntarle a nadie."""
    permitidos = [t for t in modelo.TIERS if t in politica_["autoApprove"]]
    return permitidos[-1] if permitidos else "low_cost"


def alternativa_mas_barata(tier):
    i = modelo.TIERS.index(tier)
    return modelo.TIERS[max(i - 1, 0)]


def decidir(unidad, tier, motivo, politica_):
    """Devuelve (aprobada, solicitud_o_None, presupuesto_actualizado).

    El presupuesto se gasta aca adentro para que gastarlo y decidir no puedan quedar
    desincronizados: no hay forma de consumir una llamada premium sin pasar por esta
    funcion.
    """
    presupuesto = dict(politica_["sessionBudget"])

    if tier in politica_["autoApprove"]:
        return True, None, presupuesto

    if tier == "premium":
        permitidas = int(presupuesto.get("premiumCallsAllowed") or 0)
        gastadas = int(presupuesto.get("premiumCallsSpent") or 0)
        if gastadas < permitidas:
            presupuesto["premiumCallsSpent"] = gastadas + 1
            return True, None, presupuesto

    solicitud = {
        "workUnit": unidad.get("id", "?"),
        "agent": unidad.get("assignedAgent", ""),
        "tier": tier,
        "reason": motivo,
        "expectedConsumption": CONSUMO.get(tier, "ALTO"),
        "cheaperAlternative": (
            "%s, con menor nivel de confianza en el resultado" % alternativa_mas_barata(tier)),
        "status": "PENDING",
    }
    return False, solicitud, presupuesto


def texto_de_solicitud(solicitud):
    """La solicitud como la lee una persona. En espanol, por ADR-0011."""
    return "\n".join([
        "Solicitud de escalamiento de modelo",
        "",
        "  Agente:            %s" % (solicitud["agent"] or "sin asignar"),
        "  Unidad de trabajo: %s" % solicitud["workUnit"],
        "  Tier recomendado:  %s" % solicitud["tier"].upper(),
        "  Modelo propuesto:  lo resuelve el runtime",
        "  Motivo:            %s" % solicitud["reason"],
        "  Consumo esperado:  %s" % solicitud["expectedConsumption"],
        "  Alternativa:       %s" % solicitud["cheaperAlternative"],
        "",
        "  Acciones: APROBAR · USAR LA ALTERNATIVA · CANCELAR",
    ])
