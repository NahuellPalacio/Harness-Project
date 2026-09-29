"""Flow Governance: antes de cada transicion, tengo todo lo que necesito para avanzar?

No es un quinto bloque. Es transversal a los cuatro y no absorbe nada de ellos: lee el
TaskContext, el OrchestrationPlan, el Agent Registry y el contrato de entorno, que siguen
siendo la autoridad de su dato, y decide una sola cosa -si se puede seguir, y si no, que
falta y como se consigue-.

    requeridos       que necesita cada etapa (reglas/flow-required-inputs.json)
    repositorio      de que repositorio es la tarea, y si este checkout es ese
    precondiciones   la evaluacion de una etapa y la compuerta de la refutacion
    entrada_humana   donde completa la persona lo que falta, sin ver nunca un valor

🔴 Nada de aca escribe el `.env`, ni ningun otro archivo. Detecta, localiza, explica y
valida. La persona edita.
"""
