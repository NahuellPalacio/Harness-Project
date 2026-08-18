# Fixture de prueba: tira una excepcion a proposito.
# Verifica la garantia central del harness: un check roto no rompe la sesion.
# Tiene que salir con codigo 0 y emitir un systemMessage, no un stack trace.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    raise RuntimeError("falla deliberada del check de prueba")


hook.invoke_hook("PostToolUse", _cuerpo)
