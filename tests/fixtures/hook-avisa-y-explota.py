# Fixture de prueba: avisa y despues explota en el mismo cuerpo.
# Verifica que un aviso legitimo no se corrompa si el mismo hook falla despues:
# gana la primera escritura, el systemMessage del error se descarta en silencio.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    hook.avisar("PostToolUse", "aviso legitimo antes de explotar")
    raise RuntimeError("falla deliberada despues de avisar")


hook.invoke_hook("PostToolUse", _cuerpo)
