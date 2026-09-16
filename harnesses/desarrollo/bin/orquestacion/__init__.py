"""El nucleo de orquestacion: de un TaskContext a un OrchestrationPlan.

Bloque 3, y solo su mitad determinista. Lo que decide una persona o un modelo -que hay que
hacer, que dominios toca, como se parte en unidades- entra como propuesta; lo que este
paquete hace es todo lo que se puede testear: resolver capacidades contra el registro,
rutear modelo por perfiles, aplicar la politica de consumo, calcular el estado y versionar
el plan.

Nada de aca ejecuta una unidad de trabajo. READY_FOR_EXECUTION es un estado del documento.
"""
