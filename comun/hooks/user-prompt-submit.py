# UserPromptSubmit — se dispara con cada mensaje del usuario.
#
# Un solo trabajo: RUTEO. Si lo que se pidio corresponde a una skill instalada, lo dice
# en una linea. Si no matchea nada, silencio absoluto.
#
# Presupuesto: 0 o 1 linea. Corre en cada mensaje: cualquier cosa de mas se paga en
# todos los turnos de todas las sesiones.
#
# Un secreto que el humano tipeo se AVISA, no se bloquea. Bloquear lo que alguien
# escribio a mano es la via mas rapida a que desinstalen el harness.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, campo    # noqa: E402


def cuerpo(e):
    prompt = campo(e, "prompt", "")
    if not prompt.strip():
        return

    # El ruteo por disparadores de skill se agrega cuando existan las skills.
    # Hasta entonces este hook calla, que es exactamente lo que tiene que hacer
    # cuando no tiene nada util que decir.


invoke_hook("UserPromptSubmit", cuerpo)
