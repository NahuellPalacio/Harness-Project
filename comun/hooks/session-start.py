# SessionStart — se dispara al abrir, retomar o limpiar una sesion.
#
# Contesta la pregunta que si no, hay que hacer a mano: en que quedamos.
#
# TODO lo que inyecta sale de fuentes que ya pasaron por el filtro humano de "esto vale
# la pena escribirlo": commits, la zona cache del CLAUDE.md, definiciones pendientes.
# No captura nada por su cuenta.
#
# Esa es la diferencia con una memoria que graba todo por las dudas: un capturador
# automatico persiste tambien la cadena de conexion que el agente leyo hace un rato, y
# entonces el secreto queda en dos lugares en vez de uno. Aca no puede pasar, porque lo
# unico que se lee es lo que alguien decidio dejar anotado.
#
# Presupuesto: 12 lineas. Se paga una vez por sesion, pero ocupa ventana todo el rato.
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.hook import invoke_hook, avisar, campo               # noqa: E402
from lib.reglas import config_proyecto                        # noqa: E402
from lib.zonas import definicion_zonas, contenido_zona        # noqa: E402


def _leer_utf8(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return f.read()


def _hay_fichas(directorio):
    """Si hay algun .md que no sea el indice. Un directorio que no existe, o que no se
    puede listar, es lo mismo que uno vacio: el aviso que sale igual es el de siempre.

    os.listdir SI levanta -a diferencia de os.path.isfile, que devuelve False y sigue-,
    y ademas de OSError puede tirar ValueError con un byte nulo en la ruta. Las dos se
    atrapan: esto es una linea de contexto, no una razon para perder el bloque entero."""
    try:
        return any(n.lower().endswith(".md") and n.lower() != "indice.md"
                   for n in os.listdir(directorio))
    except (OSError, ValueError):
        return False


def _git(proyecto, *args):
    try:
        r = subprocess.run(["git", "-C", proyecto] + list(args),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.stdout
    except OSError:
        return None


def cuerpo(e):
    proyecto = campo(e, "cwd", "")
    if not proyecto or not os.path.isdir(proyecto):
        return

    config = config_proyecto(proyecto)
    lineas = []

    # --- Quien sos y que harness rige aca -----------------------------------------
    encabezado = ""
    if config and config.get("usuario"):
        encabezado = str(config["usuario"])

    harness_instalados = []
    ruta_lock = os.path.join(proyecto, ".claude", "harness.lock.json")
    if os.path.isfile(ruta_lock):
        try:
            datos = json.loads(_leer_utf8(ruta_lock))
            harness_instalados = datos.get("harness") or []
            ids = ", ".join(harness_instalados)
            texto = "harness: %s v%s" % (ids, datos.get("version", ""))
            encabezado = "%s - %s" % (encabezado, texto) if encabezado else texto
        except (OSError, ValueError):
            pass
    if encabezado:
        lineas.append(encabezado)

    # --- Estado del control de versiones y ultimo trabajo -------------------------
    if os.path.isdir(os.path.join(proyecto, ".git")):
        rama = _git(proyecto, "rev-parse", "--abbrev-ref", "HEAD")
        sucio = _git(proyecto, "status", "--porcelain")
        if rama is not None and sucio is not None:
            rama = rama.strip()
            sucio_lineas = [l for l in sucio.splitlines() if l.strip()]
            estado = "limpio" if not sucio_lineas else "%d con cambios" % len(sucio_lineas)
            lineas.append("git: %s, %s" % (rama, estado))

            commits = _git(proyecto, "log", "--format=%s", "-3") or ""
            commits_lineas = [l for l in commits.splitlines() if l.strip()]
            if commits_lineas:
                lineas.append("Ultimo trabajo:")
                for c in commits_lineas:
                    lineas.append("  - " + c)
    else:
        lineas.append("git: este proyecto no esta versionado. No hay diff ni vuelta atras.")

    # --- Lo que quedo anotado en la cache ------------------------------------------
    # Es lo que alguien dejo escrito a proposito para el proximo que llegue.
    claude_md = os.path.join(proyecto, "CLAUDE.md")
    if os.path.isfile(claude_md):
        try:
            texto = _leer_utf8(claude_md)
            zona_cache = next(z for z in definicion_zonas() if z["nombre"] == "ZONA CACHE")
            contenido = contenido_zona(texto, zona_cache)
            if contenido:
                utiles = [l for l in contenido.split("\n")
                         if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("_(")]
                if utiles:
                    lineas.append("En la cache quedo anotado:")
                    for u in utiles[:4]:
                        lineas.append("  " + u.strip())
                    if len(utiles) > 4:
                        lineas.append("  ... y %d mas en la zona cache del CLAUDE.md" % (len(utiles) - 4))
        except OSError:
            pass

    # --- Definiciones pendientes abiertas -------------------------------------------
    if config and config.get("rutaDefinicionesPendientes"):
        ruta_def = os.path.join(proyecto, config["rutaDefinicionesPendientes"])
        if os.path.isfile(ruta_def):
            try:
                txt = _leer_utf8(ruta_def)
                abiertas = len(re.findall(r"(?m)^\s*[-*]\s*\[ \]", txt))
                if abiertas > 0:
                    lineas.append("%d definiciones pendientes abiertas" % abiertas)
            except OSError:
                pass

    # --- El primer recorrido del codigo, mientras no exista --------------------------
    # Solo con `desarrollo` instalado -un proyecto de solo analisis no tiene codigo que
    # recorrer- y solo hasta que el indice exista. Un aviso permanente se vuelve ruido y
    # se deja de leer, y ahi se pierde tambien el resto del bloque.
    #
    # El orden importa: el chequeo de disco va ultimo y no corre en un proyecto sin
    # `desarrollo`.
    if "desarrollo" in harness_instalados:
        # harness.config.json es el archivo de la persona: el harness no lo valida ni lo
        # pisa nunca, asi que cualquier cosa puede llegar hasta aca. Y solo se crea si no
        # existe, por lo que un proyecto instalado antes de este cambio no va a ver la
        # clave jamas. Por las dos razones el default vive aca y no en el manifiesto.
        #
        # La guarda es de TIPO y nada mas, y eso es a proposito. os.path.isfile no
        # levanta: devuelve False ante una ruta invalida o inaccesible, y se traga
        # tambien el ValueError de un byte nulo -comprobado el 2026-08-21 en 3.13-. Asi
        # que envolverlo en un try/except, o filtrar el nulo aca, son ramas que no
        # ejecuta nadie: se probo sacando cada una y la suite siguio verde.
        #
        # Lo unico que si rompe de verdad es un valor que no sea texto: ahi el que
        # levanta es os.path.join, con TypeError, y se pierde el bloque ENTERO.
        ruta_codebase = (config or {}).get("rutaCodebase")
        if not isinstance(ruta_codebase, str) or not ruta_codebase.strip():
            ruta_codebase = "docs/codebase"
        dir_codebase = os.path.join(proyecto, ruta_codebase)
        if not os.path.isfile(os.path.join(dir_codebase, "indice.md")):
            # E-07 — fichas sin indice.md es un recorrido que quedo a medias, y por
            # fuera se ve igual que uno que no empezo nunca. Sugerir "arrancalo" ahi
            # manda a rehacer lo que ya esta escrito; lo que falta es la ultima parte.
            # El indice se escribe ULTIMO a proposito, asi que este estado es tambien
            # el que deja un recorrido cortado a la mitad.
            if _hay_fichas(dir_codebase):
                lineas.append("Hay fichas del codigo sin indice.md: el recorrido de "
                              "dev-iniciador-code quedo a medias y sin el indice no "
                              "las abre nadie.")
            else:
                lineas.append("Sin indice del codigo todavia: dev-iniciador-code lo arma en una pasada.")

    if not lineas:
        return

    avisar("SessionStart", "\n".join(lineas))


invoke_hook("SessionStart", cuerpo)
