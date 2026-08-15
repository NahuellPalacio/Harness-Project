# Fixture de prueba: el caso normal, en que no hay nada que decir.
# stdout tiene que quedar COMPLETAMENTE vacio: cualquier byte de mas cuesta contexto
# en cada llamada a herramienta de cada sesion.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    pass  # sin hallazgos: no se emite nada


hook.invoke_hook("PostToolUse", _cuerpo)
