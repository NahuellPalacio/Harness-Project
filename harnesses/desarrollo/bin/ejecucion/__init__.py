"""El contexto Execution: el contrato entre Planning y cualquier implementacion que ejecute WorkUnits.

El contrato es de Task 3 (docs/cambios/execution-contract/spec.md; ADR-0014): los dos schemas de
comun/schemas/ y los validadores puros de `contrato.py`. El motor minimo es de Task 4
(docs/cambios/minimal-execution-engine/spec.md; ADR-0015): la admision, el registro de cada
Execution bajo `.claude/ejecuciones/`, la evidencia, los procesos y el Host Adapter de Claude Code.

🔴 Una WorkUnit, un intento, por invocacion de `dev-harness.py ejecutar`. No hay scheduler, cola,
hilos, reintento automatico ni reanudacion: son de la Task siguiente.
"""
