"""Check normativo: la tecnologia esta aprobada por la ASI.

    source: ES0901 / 6.3 / 7.1 / G1

Contesta UNA pregunta: si la herramienta figura en el Anexo II. Que su version sirva es del
otro check —`technology-version-compliance`— y separarlos importa: una tecnologia aprobada con
una version vieja y una tecnologia que nadie evaluo son dos problemas distintos y se resuelven
con dos personas distintas.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de
latencia y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control
normativo: se evalua contra evidencia y devuelve el estado con su motivo.

🔴 **El harness no homologa.** Lo que no esta en el Anexo II no se rechaza: es
`ASI_EVALUATION_REQUIRED`, y lo resuelve quien puede.

🔴 **Una herramienta desconocida no se clasifica como auxiliar.** Que algo sea auxiliar de la
cadena de herramientas se DECLARA en el inventario. Deducirlo seria la forma mas comoda de
sacarse de encima cualquier tecnologia que no figure: "ah, era un bundler".
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import anexo2                  # noqa: E402

CONTROL = "technology-homologation"
TIPO = "CHECK"
REGLA = "G1"

AUXILIAR_DECLARADA = "TOOLCHAIN_AUXILIARY"


def evaluar(item, catalogo=None, desde=None):
    """El estado de una tecnologia del inventario, con su motivo y su trazabilidad.

    `item` es lo que declara el inventario: `{"technology": ..., "role": ...}`. El inventario
    entra como dato — detectarlo del repositorio es otro cambio, y sin inventario esto no
    contesta "cumple": no contesta nada.
    """
    doc = catalogo if catalogo is not None else anexo2.cargar(desde)
    nombre = (item or {}).get("technology") or ""
    salida = {"control": CONTROL, "technology": nombre, "source": dict(anexo2.TRAZA)}

    if not nombre:
        salida.update({"state": anexo2.SIN_RESOLVER,
                       "reason": "el inventario no dice que tecnologia es"})
        return salida

    if (item or {}).get("role") == AUXILIAR_DECLARADA:
        regla = doc.get("toolchainRule") or {}
        salida.update({"state": anexo2.AUXILIAR,
                       "reason": "auxiliar de la cadena de herramientas: no se homologa "
                                 "individualmente, pero sigue debiendo compatibilidad y "
                                 "revision de seguridad y mantenimiento",
                       "requirements": list(regla.get("requirements") or [])})
        return salida

    entrada = anexo2.buscar(nombre, doc, desde)
    if entrada is None:
        salida.update({"state": anexo2.EVALUACION_ASI,
                       "reason": "no figura en el Anexo II. No se aprueba ni se rechaza: "
                                 "lo evalua la ASI"})
        return salida

    salida.update({"state": anexo2.HOMOLOGADA,
                   "entry": entrada.get("id"),
                   "category": entrada.get("category"),
                   "sourcePage": entrada.get("sourcePage"),
                   "reason": "figura en el Anexo II"})
    return salida


def evaluar_inventario(inventario, catalogo=None, desde=None):
    """El estado de cada tecnologia declarada. El orden de entrada se conserva."""
    doc = catalogo if catalogo is not None else anexo2.cargar(desde)
    return [evaluar(item, doc, desde) for item in (inventario or [])]
