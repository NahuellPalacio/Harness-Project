# Contrato de pre-tool-use.py punta a punta: el hook real, como proceso hijo, con el
# JSON de un evento por stdin -igual que lo invoca Claude Code-, no la libreria por
# adentro. Es lo unico que prueba que el mecanismo completo funciona.
import json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"


def _correr(script, payload):
    """Corre un hook real de comun/hooks/ con `payload` (dict) por stdin y devuelve
    su stdout decodificado."""
    entrada = json.dumps(payload).encode("utf-8")
    resultado = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=entrada, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return resultado.stdout.decode("utf-8")


def test_deny_con_secreto_alto(t):
    """E-03 — confianza alta -> deny."""
    payload = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": "a.cs",
                              "content": 'var cs = "Server=s;Password=Tr4ns4cc10n;";'}}
    salida = json.loads(_correr("pre-tool-use.py", payload))
    hs = salida["hookSpecificOutput"]
    t.igual("E-03 deny", "deny", hs["permissionDecision"])
    t.contiene("E-03 dice que hacer", "archivo externo al codigo", hs["permissionDecisionReason"])


def test_ask_con_secreto_medio(t):
    """E-03 — confianza media -> ask, no deny. Es la asimetria que mantiene el harness
    instalado: bloquear de mas es como se pierde un harness.

    Literal armado por concatenacion, como tests/casos/04-secretos.ps1: un fuente que
    dispara el propio detector de secretos es un fuente que nadie puede editar en una
    maquina donde el harness ya esta instalado.
    """
    payload = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": "a.ts",
                              "content": ('const api' + 'Key = "9f8e7d6c5b4a39281706f5e4d3c2b1a0";')}}
    salida = json.loads(_correr("pre-tool-use.py", payload))
    hs = salida["hookSpecificOutput"]
    t.igual("E-03 ask", "ask", hs["permissionDecision"])
    t.verdadero("E-03 ask no es deny", hs["permissionDecision"] != "deny")


def test_placeholder_no_dispara(t):
    """E-04 — ${DB_PASSWORD} no es un secreto."""
    payload = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": "a.cs", "content": "password = ${DB_PASSWORD}"}}
    t.igual("E-04 silencio", "", _correr("pre-tool-use.py", payload))
