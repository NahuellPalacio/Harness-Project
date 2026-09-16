"""De las senales de una unidad de trabajo al tier de modelo que necesita.

🔴 Perfiles, nunca nombres de modelo. `low_cost`, `standard`, `reasoning`, `premium`. El
nombre concreto lo resuelve el runtime: un plan que dice un modelo con nombre y apellido
deja de valer en cuanto el proveedor renombra algo, y deja de ser portable a otro runtime.

🔴 El principio es usar el modelo MENOS costoso que pueda hacer la unidad de forma
confiable, no el mas potente. Por eso el default es `low_cost` y hay que justificar subir.

Las senales las declara el agente que planifica. Nadie las audita — y eso esta asumido: la
defensa contra un agente que declare todo ambiguo para conseguir premium no es el scoring,
es la compuerta humana de `consumo.py`.
"""
TIERS = ("low_cost", "standard", "reasoning", "premium")

# Cuanto empuja cada senal. Los numeros son groseros a proposito: un scoring fino sugiere
# una precision que no existe, y lo que importa es el orden de magnitud.
PESOS = {
    "ambiguity": 3,
    "novelty": 2,
    "architectural_impact": 3,
    "security_impact": 3,
    "cross_domain": 2,
    "many_components": 1,
    "dependency_complexity": 1,
    "large_context": 1,
    "capability_gap": 2,
    "needs_tool_creation": 2,
    "previous_failures": 2,
}

# De puntaje a tier. Los cortes se pueden mover; lo que no se mueve es que el default sea
# el mas barato.
CORTES = ((0, "low_cost"), (2, "standard"), (5, "reasoning"), (8, "premium"))

COMO_SE_LEE = {
    "ambiguity": "la tarea es ambigua",
    "novelty": "no hay antecedente parecido en el proyecto",
    "architectural_impact": "toca la arquitectura",
    "security_impact": "toca seguridad",
    "cross_domain": "cruza varios dominios",
    "many_components": "toca muchos componentes",
    "dependency_complexity": "las dependencias entre unidades son complejas",
    "large_context": "el contexto es grande",
    "capability_gap": "hay una capacidad faltante",
    "needs_tool_creation": "hay que construir una tool",
    "previous_failures": "hubo intentos fallidos antes",
}


def _tier_de_puntaje(puntaje):
    elegido = CORTES[0][1]
    for umbral, tier in CORTES:
        if puntaje >= umbral:
            elegido = tier
    return elegido


def enrutar(senales, minimo="low_cost"):
    """Devuelve el tier, su motivo y las senales que lo empujaron.

    `senales` es la lista de nombres que declaro el agente. Lo que no esta en PESOS se
    ignora y se dice: una senal inventada no puede empujar el tier sin que nadie la vea.
    """
    conocidas = [s for s in senales if s in PESOS]
    desconocidas = [s for s in senales if s not in PESOS]
    puntaje = sum(PESOS[s] for s in conocidas)
    tier = _tier_de_puntaje(puntaje)
    if TIERS.index(tier) < TIERS.index(minimo):
        tier = minimo

    if conocidas:
        motivo = "%s: %s." % (tier, ", ".join(COMO_SE_LEE[s] for s in conocidas))
    else:
        motivo = ("%s: no se declaro ninguna senal de complejidad, asi que corresponde el "
                  "tier mas barato." % tier)
    if desconocidas:
        motivo += " Se ignoraron senales desconocidas: %s." % ", ".join(sorted(desconocidas))

    return {"requiredTier": tier, "reason": motivo,
            "signals": sorted(conocidas), "score": puntaje,
            "unknownSignals": sorted(desconocidas)}


def siguiente(tier):
    """El tier de arriba, o el mismo si ya es el ultimo. NUNCA saltea uno."""
    i = TIERS.index(tier)
    return TIERS[min(i + 1, len(TIERS) - 1)]


def escalar(tier_actual, que_fallo, intentos):
    """Una escalada explicita: que fallo, cuantas veces, y a donde se va.

    Un tier que se saltea es una decision de consumo que nadie vio.
    """
    proximo = siguiente(tier_actual)
    if proximo == tier_actual:
        return {"from": tier_actual, "to": tier_actual, "attempts": intentos,
                "reason": "%s ya es el tier mas alto: no hay a donde escalar. Lo que fallo: %s."
                          % (tier_actual, que_fallo),
                "exhausted": True}
    return {"from": tier_actual, "to": proximo, "attempts": intentos,
            "reason": "%s no alcanzo despues de %d intento(s). Lo que fallo: %s. Se sube a %s, "
                      "que es el tier inmediato siguiente."
                      % (tier_actual, intentos, que_fallo, proximo),
            "exhausted": False}


def perfiles_declarados(config):
    """Los modelos por perfil, como los declara la configuracion del proyecto.

    Un perfil sin modelo declarado sale con `declared: false` y el plan lo avisa. No se
    inventa un nombre: el harness no sabe que modelos existen en el runtime de al lado.
    """
    declarados = (config or {}).get("perfiles") or {}
    return [{"tier": t, "model": str(declarados.get(t, "")), "declared": bool(declarados.get(t))}
            for t in TIERS]
