"""Adaptador de Codex: el contrato completo, sin fuente autoritativa de uso.

No hay hoy una fuente local que reporte consumo facturable de Codex a la que este harness
tenga acceso. El adaptador existe igual, cumple el mismo contrato que cualquier otro y
devuelve `USAGE_UNRESOLVED`.

🔴 Devolver cero seria decir que Codex no consumio. Devolver una lista vacia seria decir
que no paso nada. Las dos cosas son falsas y las dos abaratan la tarea en el reporte. Lo
unico honesto es decir que paso y no se sabe cuanto, que es lo que el pedido exige
explicitamente: *"If exact billable usage is unavailable, USAGE_UNRESOLVED must remain
visible."*

El dia que exista la fuente, lo unico que cambia es `leer`. Nada del nucleo se toca: para
eso esta el borde.
"""
from . import contrato

NOMBRE = "codex"
PROVEEDOR = "openai"

MOTIVO = ("no hay una fuente local autoritativa de uso de Codex: el consumo existe y no se "
          "puede medir desde acá")


def leer(ruta=""):
    """Un registro sin resolver, siempre. Nunca cero, nunca vacio."""
    return [contrato.sin_resolver(reference=str(ruta or NOMBRE), motivo=MOTIVO,
                                  provider=PROVEEDOR)]
