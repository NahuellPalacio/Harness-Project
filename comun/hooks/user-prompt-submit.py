# UserPromptSubmit — se dispara con cada mensaje del usuario.
#
# Un trabajo: el FLUJO (lib/flow_context.py). Si el prompt declara una tarea («Seguimos con
# ABC-123»), vincula la sesion a ella. Si la tarea de la sesion no puede avanzar, le dice al
# modelo por que -y a la persona, la primera vez- con el enlace al archivo donde se completa lo
# que falta. Nunca un valor: la ubicacion la da flujo/entrada_humana.py.
#
# Presupuesto: sin tarea bloqueada, silencio. Con la misma tarea y el mismo bloqueo, una linea.
# El bloque entero sale solo cuando algo cambio. Corre en cada mensaje: nada de red, de modelo,
# de Jira, de GitLab ni de recorrer el repositorio.
#
# Un secreto que el humano tipeo se AVISA, no se bloquea. Bloquear lo que alguien
# escribio a mano es la via mas rapida a que desinstalen el harness.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, avisar_y_mostrar, campo    # noqa: E402


def cuerpo(e):
    prompt = campo(e, "prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        return
    try:
        from lib import flow_context
        salida = flow_context.del_turno(e)
    except Exception:                    # noqa: BLE001 - lo que se muestra no rompe el turno
        salida = None
    if salida:
        avisar_y_mostrar("UserPromptSubmit", salida[0], salida[1])

    # El ruteo por disparadores de skill se agrega cuando existan las skills.


invoke_hook("UserPromptSubmit", cuerpo)
