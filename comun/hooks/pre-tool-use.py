# PreToolUse — EXCLUSIVAMENTE el bloqueo de secretos. Nada mas entra aca.
#   1. Es la puerta: una sola cosa la cruza.
#   2. Avisar desde aca no sirve: en exito la salida va a la transcripcion.
#   3. Latencia: dispara antes de cada llamada. Cada regla de mas se paga siempre.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, bloquear, preguntar          # noqa: E402
from lib.secretos import importar_patrones, buscar_secreto, texto_de_herramienta  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def cuerpo(e):
    texto = texto_de_herramienta(e)
    if not texto.strip():
        return
    catalogo = importar_patrones(os.path.join(AQUI, "..", "reglas", "secretos.patrones.json"))
    h = buscar_secreto(texto, catalogo)
    if h is None:
        return
    mensaje = "%s [%s: %s]" % (h["motivo"], h["id"], h["muestra"])
    if h["confianza"] == "alta":
        bloquear("PreToolUse", mensaje)
    else:
        # Ambiguo: decide la persona. Bloquear de mas es como se pierde un harness.
        preguntar("PreToolUse", mensaje)


invoke_hook("PreToolUse", cuerpo)
