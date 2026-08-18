# PostToolUse — se dispara despues de una escritura o un comando.
#
# El caballo de batalla: corre los checks de comun y de los harness instalados contra lo
# que se acaba de escribir, y devuelve los hallazgos como additionalContext. Claude los
# lee y corrige en el turno siguiente.
#
# Es el UNICO lugar donde el harness avisa, porque es el unico evento portatil en que
# additionalContext llega de verdad al modelo: en PreToolUse la salida en exito va a la
# transcripcion y nadie la ve.
#
# Si no hay hallazgos: silencio. El costo tiene que ser proporcional a los problemas
# reales, no al tamano del reglamento.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, avisar, campo            # noqa: E402
from lib.reglas import config_proyecto, correr_checks      # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def cuerpo(e):
    proyecto = campo(e, "cwd", "")
    if not proyecto:
        return

    dir_checks = os.path.join(AQUI, "..", "checks")
    if not os.path.isdir(dir_checks):
        return

    config = config_proyecto(proyecto)
    hallazgos = correr_checks(e, dir_checks, proyecto, config)
    if not hallazgos:
        return

    avisar("PostToolUse", "\n".join(hallazgos))


invoke_hook("PostToolUse", cuerpo)
