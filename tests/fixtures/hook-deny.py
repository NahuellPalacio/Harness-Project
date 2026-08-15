# Fixture de prueba: emite un bloqueo.
# Es la unica forma de salida que impide que la herramienta se ejecute, y en el
# harness real la usa exclusivamente la regla de secretos.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    hook.bloquear("PreToolUse", "Literal con forma de client_secret. Usá una variable de entorno.")


hook.invoke_hook("PreToolUse", _cuerpo)
