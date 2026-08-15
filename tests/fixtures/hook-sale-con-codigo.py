# Fixture de prueba: el cuerpo intenta salir con un codigo distinto de 0.
# Verifica que invoke_hook normaliza cualquier sys.exit a 0: el contrato es salir 0
# siempre, sin excepciones para lo que haga el cuerpo del hook.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    sys.exit(3)


hook.invoke_hook("PostToolUse", _cuerpo)
