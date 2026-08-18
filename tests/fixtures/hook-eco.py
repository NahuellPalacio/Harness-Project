# Fixture de prueba: hace eco de la ruta, el contenido y el prompt del evento.
# Sirve para verificar el camino completo stdin -> parseo -> additionalContext -> stdout.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun" / "hooks"))
from lib import hook  # noqa: E402


def _cuerpo(e):
    ruta = hook.campo(e, "tool_input.file_path", "(sin ruta)")
    contenido = hook.campo(e, "tool_input.content", "(sin contenido)")
    prompt = hook.campo(e, "prompt", "(sin prompt)")
    hook.avisar("PostToolUse", "eco|%s|%s|%s" % (ruta, contenido, prompt))


hook.invoke_hook("PostToolUse", _cuerpo)
