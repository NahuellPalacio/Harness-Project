"""Un Host falso: imita `claude -p --output-format json` para la suite del motor de ejecucion.

docs/cambios/minimal-execution-engine/spec.md, seccion 29. El motor lo encuentra por
`ejecucion.comandoHost` de harness.config.json, como encontraria a `claude`: no hay monkeypatch
del motor. Lee su guion de un archivo JSON cuya ruta esta en HOST_FALSO_GUION:

    eco            ruta donde deja {argv, stdin, cwd, pid, sistema} de lo que recibio; `sistema` es
                   el contenido del archivo de --system-prompt-file
    cambios        [{ruta, contenido}] a escribir en el proyecto; contenido null borra
    commit         true: `git add -A` y `git commit` de los cambios
    hijo           ruta donde deja el pid de un nieto que duerme, para ver morir el arbol
    dormir         segundos antes de contestar
    senal          true: muere por SIGTERM (en Windows sale con 143, como el Host real)
    sin_json       texto que imprime en vez del resultado
    salida         el codigo de salida
    stderr         texto para stderr
    resultado      campos que pisan los del objeto `type: result` (subtype, is_error, result,
                   structured_output, error...). `structured_output: null` lo saca.

Task 5 (docs/cambios/graph-execution/spec.md, GD-27 paso 6) suma dos claves, y sin ellas el Host
hace lo de siempre:

    por_unidad     {workUnitId: {claves del guion}}: un guion distinto por WorkUnit. El workUnitId se
                   lee del prompt, del bloque ```json donde `host_claude_code.prompt` pone la WorkUnit.
                   Las claves de la unidad pisan las de arriba; una WorkUnit que no figura usa el
                   guion de arriba, y una sin workUnitId legible tambien.
    bitacora       ruta de un archivo con una linea JSON por escritura: {id, workUnitId, pid, inicio,
                   fin}. Cada invocacion escribe su linea al empezar, con `fin: null`, y la misma
                   linea con el `fin` al terminar, antes de contestar o de morir: quien la lee toma la
                   ultima de cada `id`. Asi una invocacion que muere desde afuera (el arbol del Host
                   terminado, el conductor muerto) igual cuenta, y una que termino tiene su intervalo.
                   `inicio` y `fin` son `time.time()`: se comparan entre procesos.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time

# El bloque ```json de `host_claude_code.prompt`: es la unica WorkUnit que viaja en el prompt.
BLOQUE_DE_LA_UNIDAD = re.compile(r"```json\r?\n(.*?)\r?\n```", re.S)


def _argumento(argv, nombre):
    return argv[argv.index(nombre) + 1] if nombre in argv[:-1] else None


def _unidad_del_prompt(entrada):
    """El workUnitId de la WorkUnit que viaja en el prompt, o None."""
    bloque = BLOQUE_DE_LA_UNIDAD.search(entrada)
    try:
        unidad = json.loads(bloque.group(1)) if bloque else None
    except ValueError:
        return None
    return unidad.get("id") if isinstance(unidad, dict) else None


def _anotar(ruta, linea):
    """Una linea a la bitacora, en un solo write con el archivo abierto para agregar: otro Host que
    escribe a la vez agrega la suya entera."""
    with open(ruta, "ab") as f:
        f.write((json.dumps(linea, ensure_ascii=False) + "\n").encode("utf-8"))


def _bitacora(ruta, unidad):
    """Anota que esta invocacion empezo, y devuelve lo que anota que termino."""
    if not ruta:
        return lambda: None
    linea = {"id": "%d-%d" % (os.getpid(), time.time_ns()), "workUnitId": unidad,
             "pid": os.getpid(), "inicio": time.time(), "fin": None}
    _anotar(ruta, linea)
    return lambda: _anotar(ruta, dict(linea, fin=time.time()))


def main():
    argv = sys.argv[1:]
    entrada = sys.stdin.buffer.read().decode("utf-8", "replace")
    with open(os.environ["HOST_FALSO_GUION"], encoding="utf-8") as f:
        guion = json.load(f)

    unidad = _unidad_del_prompt(entrada) if guion.get("por_unidad") or guion.get("bitacora") else None
    guion.update((guion.pop("por_unidad", None) or {}).get(unidad) or {})
    cerrar_la_bitacora = _bitacora(guion.get("bitacora"), unidad)

    if guion.get("eco"):
        sistema = _argumento(argv, "--system-prompt-file")
        try:
            with open(sistema, encoding="utf-8") as f:
                prompt_de_sistema = f.read()
        except (OSError, TypeError):
            prompt_de_sistema = None
        # Entero o nada: el test lo lee mientras el Host sigue vivo, y un eco a medio escribir
        # es JSON roto.
        temporal = "%s.%d.tmp" % (guion["eco"], os.getpid())
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump({"argv": argv, "stdin": entrada, "cwd": os.getcwd(), "pid": os.getpid(),
                       "sistema": prompt_de_sistema}, f)
        # En Windows, reemplazar un eco viejo que el test esta leyendo justo ahora falla: se reintenta.
        for intento in range(50):
            try:
                os.replace(temporal, guion["eco"])
                break
            except PermissionError:
                if intento == 49:
                    raise
                time.sleep(0.02)

    for cambio in guion.get("cambios") or []:
        ruta = os.path.join(os.getcwd(), *cambio["ruta"].split("/"))
        if cambio.get("contenido") is None:
            if os.path.exists(ruta):
                os.remove(ruta)
        else:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(cambio["contenido"])
    if guion.get("commit"):
        for args in (["add", "-A"], ["commit", "-q", "-m", "el Host falso"]):
            subprocess.run(["git", "-c", "user.email=h@f", "-c", "user.name=host-falso"] + args,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if guion.get("hijo"):
        nieto = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        with open(guion["hijo"], "w", encoding="utf-8") as f:
            f.write(str(nieto.pid))

    if guion.get("dormir"):
        time.sleep(float(guion["dormir"]))

    if guion.get("stderr"):
        sys.stderr.write(guion["stderr"])
        sys.stderr.flush()

    if guion.get("senal"):
        cerrar_la_bitacora()
        if os.name == "nt":
            os._exit(143)
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(5)

    if "sin_json" in guion:
        cerrar_la_bitacora()
        sys.stdout.write(guion["sin_json"])
        sys.stdout.flush()
        return int(guion.get("salida", 1))

    resultado = {"type": "result", "subtype": "success", "is_error": False,
                 "result": "listo", "session_id": _argumento(argv, "--session-id"),
                 "num_turns": 1, "duration_ms": 10, "total_cost_usd": 0, "usage": {},
                 "permission_denials": [],
                 "structured_output": {"declaredStatus": "COMPLETE", "artifact": "# Informe\n"}}
    resultado.update(guion.get("resultado") or {})
    if resultado.get("structured_output") is None:
        resultado.pop("structured_output", None)
    cerrar_la_bitacora()
    sys.stdout.write(json.dumps(resultado, ensure_ascii=False))
    sys.stdout.flush()
    return int(guion.get("salida", 0))


if __name__ == "__main__":
    sys.exit(main())
