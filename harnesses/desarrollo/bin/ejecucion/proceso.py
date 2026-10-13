"""Los procesos de Execution: lanzar con limite, esperar sin hilos y matar el arbol.

docs/cambios/minimal-execution-engine/spec.md, MD-14. Repite el algoritmo de
`flujo/repositorio.py` (`_correr_con_limite`, `_matar_arbol`) en vez de importarlo: esas funciones
son privadas de Flow Governance, que esta Task no toca. Consolidarlas es un pendiente.

- la salida va a archivos, nunca a un pipe: un nieto que hereda el pipe no cuelga la espera;
- en POSIX el hijo abre su propio grupo, y se mata el grupo; en Windows, `taskkill /F /T`;
- la espera es por tramos de un segundo, para mirar un pedido de cancelar sin hilos.

🔴 Nadie mata por pid guardado: `pid_vivo` solo informa (R1). Un pid se reusa, y matar por
numero puede matar un proceso ajeno.
"""
import os
import signal
import subprocess
import tempfile
import time

TERMINO = "TERMINO"
VENCIDO = "VENCIDO"
CANCELADO = "CANCELADO"
INTERRUMPIDO = "INTERRUMPIDO"

TRAMO = 1.0
LIMITE_DE_GIT = 10


def git(proyecto, *args):
    """(codigo, stdout) de `git -C <proyecto> ...`, o (None, None) si no se pudo lanzar o no
    contesto en LIMITE_DE_GIT segundos. Vencido, se mata el arbol y no se espera a nadie."""
    argumentos = ["git", "-c", "core.fsmonitor=false", "-C", proyecto] + list(args)
    with tempfile.TemporaryFile() as salida:
        try:
            hijo = subprocess.Popen(argumentos, stdout=salida, stderr=subprocess.DEVNULL,
                                    stdin=subprocess.DEVNULL, start_new_session=os.name != "nt")
        except (OSError, ValueError):
            return None, None
        try:
            hijo.wait(LIMITE_DE_GIT)
        except subprocess.TimeoutExpired:
            matar_arbol(hijo)
            return None, None
        salida.seek(0)
        return hijo.returncode, salida.read()


def lanzar(argumentos, cwd, entrada, salida, error):
    """El proceso, con stdin, stdout y stderr en archivos ya abiertos. Levanta OSError si el
    sistema operativo no lo puede lanzar."""
    return subprocess.Popen(argumentos, cwd=cwd, stdin=entrada, stdout=salida, stderr=error,
                            start_new_session=os.name != "nt")


def esperar(hijo, limite, cancelada=None, tramo=TRAMO):
    """(TERMINO, codigo), (VENCIDO, None), (CANCELADO, None) o (INTERRUMPIDO, None).

    Mira el pedido de cancelar antes de cada tramo. Si el proceso ya termino, gana su codigo. Un
    Ctrl-C sobre el motor mata el arbol y vuelve INTERRUMPIDO.
    """
    fin = time.monotonic() + limite
    try:
        while True:
            if cancelada is not None and cancelada():
                matar_arbol(hijo)
                return CANCELADO, None
            restante = fin - time.monotonic()
            if restante <= 0:
                matar_arbol(hijo)
                return VENCIDO, None
            try:
                return TERMINO, hijo.wait(min(tramo, restante))
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        matar_arbol(hijo)
        return INTERRUMPIDO, None


def matar_arbol(hijo):
    """El proceso y todo lo que lanzo. En Windows `claude` es un shim que deja vivo al Host de
    verdad si se mata solo al primero."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(hijo.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL, timeout=10)
        else:
            os.killpg(hijo.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        hijo.kill()
    except OSError:
        pass
    try:
        hijo.wait(10)
    except subprocess.TimeoutExpired:
        pass


def pid_vivo(pid):
    """Si hay un proceso con ese pid. Solo para avisar en `--estado`: puede ser otro que reuso el
    numero, y por eso nadie mata por esto."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        manija = kernel32.OpenProcess(0x1000, False, pid)
        if not manija:
            return False
        try:
            codigo = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(manija, ctypes.byref(codigo)):
                return False
            return codigo.value == 259
        finally:
            kernel32.CloseHandle(manija)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True
