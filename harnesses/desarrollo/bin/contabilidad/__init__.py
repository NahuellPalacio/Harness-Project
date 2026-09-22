"""Bloque 4: la contabilidad de ejecucion y el control de presupuesto.

Observa al Bloque 3 y no lo toca. `orquestacion/consumo.py` y `orquestacion/modelo.py`
quedan exactamente como estaban: este paquete no los importa, ellos no lo importan, y la
compuerta humana sigue siendo la de `consumo.decidir`. Lo unico que este bloque hace con
un escalamiento caro es darle EVIDENCIA a quien decide.

Cuatro reglas que valen para todo lo que cuelga de aca:

    lo que falta NO es cero       un uso desconocido es USAGE_UNRESOLVED
    la foto NO es un consumo      contextTokens no se suma nunca
    lo no atribuido NO se reparte  se ve en el resumen y suma solo al total
    el Markdown NO es la fuente    se genera del resumen y nunca se lee

🔴 El nucleo no nombra ningun proveedor. Un `if provider == "..."` aca adentro convierte
al adaptador en una decoracion: la rama vuelve al centro y el proximo proveedor se agrega
tocando el centro otra vez. Los nombres viven en `adaptadores/registro.py`, que es el
unico lugar donde un proveedor es un string.

🔴 Un agente y una skill NUNCA llaman a esto. Si un agente tuviera que acordarse de
registrar su consumo, el consumo del agente que se olvide no existe. Los eventos los emite
quien orquesta la ejecucion.
"""
