"""Infraestructura de hooks del harness GCBA.

Las cuatro cosas que son identicas en los cuatro eventos y que, hechas mal, fallan
en silencio: encoding, lectura del evento por stdin, las tres unicas salidas validas,
y el control de errores. Un hook JAMAS rompe la sesion.
"""
import json
import os
import re
import sys
import tempfile

DIR_ESTADO = os.path.join(tempfile.gettempdir(), "gcba-harness")

# Se emite un unico JSON por corrida. Dos objetos concatenados sin separador rompen
# el parseo de Claude Code y se llevan puesto el primer aviso, que ya era valido:
# gana la primera escritura, cualquier otra se descarta en silencio.
_ya_emitido = False


def leer_evento():
    """Lee el JSON de stdin. Devuelve None si vino vacio.

    Se lee del buffer binario y se decodifica con utf-8-sig: si el BOM viene, se
    descarta en vez de romper el parseo.
    """
    crudo = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    if not crudo.strip():
        return None
    return json.loads(crudo)


def campo(evento, ruta, default=None):
    """Lee una propiedad anidada sin explotar si no existe.

    La forma de tool_input cambia segun la herramienta, asi que el acceso directo
    no sirve: Write trae file_path y content, Edit trae old_string y new_string.
    """
    actual = evento
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return default
        actual = actual[parte]
    return default if actual is None else actual


def _emitir(objeto):
    """Escribe un JSON por stdout. Devuelve True si escribio, False si ya se habia
    emitido algo en esta corrida (ver `_ya_emitido`) y este llamado se descarto.
    """
    global _ya_emitido
    if _ya_emitido:
        return False
    _ya_emitido = True
    # ensure_ascii=False: sin esto un aviso con tilde llega escapado al contexto.
    # Y se escriben bytes UTF-8 al buffer: en Windows sys.stdout sale en cp1252 y
    # el aviso llegaria corrupto -o el hook explotaria- justo cuando tiene tildes.
    crudo = json.dumps(objeto, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.buffer.write(crudo.encode("utf-8"))
    sys.stdout.buffer.flush()
    return True


def avisar(evento_nombre, texto):
    """AVISA: inyecta texto en el contexto sin interrumpir nada."""
    if not texto or not texto.strip():
        return
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre, "additionalContext": texto}})


def bloquear(evento_nombre, motivo):
    """BLOQUEA. Reservado a la regla de secretos: es lo unico que el harness impide."""
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre,
        "permissionDecision": "deny", "permissionDecisionReason": motivo}})


def preguntar(evento_nombre, motivo):
    """PREGUNTA: lo ambiguo lo decide la persona, no el harness."""
    _emitir({"hookSpecificOutput": {
        "hookEventName": evento_nombre,
        "permissionDecision": "ask", "permissionDecisionReason": motivo}})


def mensaje_de_sistema(texto, session_id="sin-sesion", clave="general"):
    """Avisa de un problema del propio harness, una sola vez por sesion y evento."""
    marca = None
    try:
        os.makedirs(DIR_ESTADO, exist_ok=True)
        seguro = re.sub(r"[^A-Za-z0-9._-]", "_", "%s.%s" % (session_id, clave))
        marca = os.path.join(DIR_ESTADO, seguro + ".avisado")
        if os.path.exists(marca):
            return
    except OSError:
        # Si no se puede ni preguntar por la marca, se avisa igual: perder el aviso
        # es peor que repetirlo.
        pass

    try:
        emitido = _emitir({"systemMessage": texto})
    except BaseException:              # noqa: BLE001 - la ultima red no puede fallar
        # El padre pudo haber cerrado el pipe (BrokenPipeError adentro de un except
        # que ya esta manejando otra falla): no hay adonde avisar, pero invoke_hook
        # tiene que poder seguir camino a salir 0 igual.
        return

    if not emitido or marca is None:
        return

    # La marca se escribe DESPUES de emitir, no antes: si algo interrumpe la emision
    # el proximo intento tiene que poder avisar de nuevo, no encontrarse ya silenciado.
    # "x" es atomico -crea y falla si ya existe- a diferencia de comprobar con
    # os.path.exists y despues abrir en "w", que deja una ventana entre las dos
    # operaciones.
    try:
        open(marca, "x").close()
    except OSError:
        # FileExistsError (otra invocacion concurrente ya la dejo) u otro problema de
        # disco: en cualquier caso, el aviso de esta corrida ya salio.
        pass


def invoke_hook(evento_nombre, cuerpo):
    """Envoltorio de todo hook. Garantiza salida 0 pase lo que pase."""
    evento = None
    session_id = "sin-sesion"
    try:
        evento = leer_evento()
        if evento is None:
            sys.exit(0)
        session_id = campo(evento, "session_id", "sin-sesion")
        cuerpo(evento)
    except SystemExit as e:
        if e.code in (0, None):
            raise
        # El contrato es salir 0 siempre: un sys.exit con otro codigo -aunque venga
        # del cuerpo del hook- no se deja escapar, se normaliza en el sys.exit(0) de
        # mas abajo.
    except BaseException as e:            # noqa: BLE001 - a proposito: nada escapa
        mensaje_de_sistema(
            "harness: fallo el hook %s (%s). Se omite hasta el proximo reinicio."
            % (evento_nombre, e),
            session_id=session_id, clave=evento_nombre)
    sys.exit(0)
