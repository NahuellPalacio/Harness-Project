# PreToolUse — la puerta. Dos reglas la cruzan, y en este orden:
#   1. El Secret Guard (lib/secretos.py): un secreto de confianza alta es deny y la compuerta
#      del flujo ni se evalua; uno ambiguo pregunta.
#   2. La compuerta del flujo (lib/flow_gate.py): si la tarea de la sesion no puede avanzar,
#      lo que modifica o avanza el proyecto es deny. Gana sobre el ask de un secreto ambiguo:
#      un ask dejaria saltar un HARD_BLOCKER aprobando una herramienta.
# Una sola emision por corrida. Avisar desde aca no sirve: en exito la salida va a la
# transcripcion. Latencia: dispara antes de cada llamada, y sin estado del flujo en el proyecto
# la compuerta es un listado de una carpeta que no existe.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, bloquear, preguntar          # noqa: E402
from lib.secretos import importar_patrones, buscar_secreto, texto_de_herramienta  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def secreto(e):
    """(confianza, mensaje) del Secret Guard, o None."""
    texto = texto_de_herramienta(e)
    if not texto.strip():
        return None
    catalogo = importar_patrones(os.path.join(AQUI, "..", "reglas", "secretos.patrones.json"))
    h = buscar_secreto(texto, catalogo)
    if h is None:
        return None
    return h["confianza"], "%s [%s: %s]" % (h["motivo"], h["id"], h["muestra"])


def _hay_estado_del_flujo(cwd):
    """Si `cwd` o alguna carpeta de arriba tiene `.claude/runtime/tasks` con algo adentro."""
    if not isinstance(cwd, str) or not cwd:
        return False
    actual = os.path.abspath(cwd)
    while True:
        try:
            if any(os.scandir(os.path.join(actual, ".claude", "runtime", "tasks"))):
                return True
        except OSError:
            pass
        arriba = os.path.dirname(actual)
        if arriba == actual:
            return False
        actual = arriba


def compuerta(e):
    """La decision de lib/flow_gate.py. Se importa aca y no arriba: una instalacion a medias no
    puede apagar el Secret Guard, que ya decidio antes. Si no carga y el proyecto tiene estado del
    flujo, falla cerrado; si no tiene, no hay nada que gobernar."""
    try:
        from lib import flow_gate
    except Exception as falla:            # noqa: BLE001 - fallar cerrado, sin apagar el resto
        if not _hay_estado_del_flujo(e.get("cwd") if isinstance(e, dict) else None):
            return {"decision": "allow"}
        return {"decision": "deny", "reason": (
            "Flujo: no se pudo cargar la compuerta (%s) [FLOW_GATE_UNRESOLVED]. Una herramienta "
            "que modifica o avanza el proyecto no pasa sin evaluarla. Reinstalá el harness."
            % type(falla).__name__)}
    return flow_gate.decidir(e)


def cuerpo(e):
    fallo_del_detector = None
    try:
        hallazgo = secreto(e)
    except Exception as falla:            # noqa: BLE001 - la compuerta se evalua igual
        hallazgo, fallo_del_detector = None, falla
    if hallazgo is not None and hallazgo[0] == "alta":
        bloquear("PreToolUse", hallazgo[1])
        return
    flujo = compuerta(e)
    if flujo["decision"] == "deny":
        motivo = flujo["reason"]
        if hallazgo is not None:
            motivo += " Además, un posible secreto: " + hallazgo[1]
        bloquear("PreToolUse", motivo)
        return
    if fallo_del_detector is not None:
        raise fallo_del_detector          # como siempre: se avisa una vez y se sigue
    if hallazgo is not None:
        # Ambiguo: decide la persona. Bloquear de mas es como se pierde un harness.
        preguntar("PreToolUse", hallazgo[1])


invoke_hook("PreToolUse", cuerpo)
