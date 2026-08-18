# Fixture de prueba: emite una pregunta.
# Para lo ambiguo: ni bloquea ni pasa en silencio, deja que decida la persona.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    hook.preguntar("PreToolUse", "Patron ambiguo: podria ser un identificador comun.")


hook.invoke_hook("PreToolUse", _cuerpo)
