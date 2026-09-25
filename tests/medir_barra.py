"""La latencia de la Context Bar, medida como la corre el cliente: el renderizador instalado,
un proceso por dibujo, con una transcripcion de 5 MB.

    python tests/medir_barra.py [--corridas 11] [--mb 5]

Imprime un JSON en una linea:

    primeraMs              la primera invocacion: ingiere la transcripcion entera
    p50Ms                  el p50 de las siguientes, sin mensajes nuevos
    conMensajeNuevoP50Ms   el p50 con un mensaje nuevo por invocacion, que es el caso real
    corridas, bytes, umbralMs

Lo usan `install.ps1 -Doctor` y la suite. No es un test ni corre como uno: la suite no le pone
un umbral, porque la latencia depende de la maquina y una compuerta que falla segun la maquina
se apaga. El umbral de la spec (400 ms) se informa, no se mueve.

Arma un proyecto descartable en el temporal con el arbol que copia install.ps1 -hooks, reglas,
schemas, bin y bin/desarrollo-, compilado como lo deja install.ps1, y lo borra al terminar. No
toca ningun proyecto de nadie. El proceso se lanza directo, sin shell: lo que agrega Git Bash o
PowerShell alrededor no es de la barra.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UMBRAL_MS = 400
SESION = "s-medida-barra"

# Lo que install.ps1 copia a .claude/harness/, con el mismo destino.
ARBOLES = (("comun/hooks", "hooks"), ("comun/reglas", "reglas"), ("comun/schemas", "schemas"),
           ("comun/bin", "bin"), ("harnesses/desarrollo/bin", "bin/desarrollo"))
RENDERIZADOR = ("bin", "desarrollo", "contabilidad", "statusline.py")


def armar(proyecto):
    """El arbol instalado del harness en `proyecto`, con el bytecode que deja install.ps1.
    Devuelve la ruta del renderizador.

    install.ps1 no compila nada: el bytecode que queda es el de los hooks, que corren para
    verificarlos -hooks/lib-, y en bin/ no hay ninguno (E-33 de integraciones-bootstrap). La
    barra no escribe el suyo, asi que sus modulos se compilan en memoria en cada dibujo, y eso
    entra en la medicion.
    """
    harness = os.path.join(proyecto, ".claude", "harness")
    for origen, destino in ARBOLES:
        shutil.copytree(os.path.join(RAIZ, *origen.split("/")),
                        os.path.join(harness, *destino.split("/")),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                        dirs_exist_ok=True)
    subprocess.run([sys.executable, "-m", "compileall", "-q", os.path.join(harness, "hooks")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(harness, *RENDERIZADOR)


def _mensaje(n, sesion):
    """Un turno como los escribe el cliente: el pedido, la llamada con su uso, el resultado
    de la herramienta -casi todo el peso- y el texto de cierre del mismo mensaje."""
    mid = "msg_%06d" % n
    uso = {"input_tokens": 12, "output_tokens": 300 + n % 97,
           "cache_read_input_tokens": 40000 + 50 * n, "cache_creation_input_tokens": 900}
    base = {"sessionId": sesion, "timestamp": "2026-09-24T10:%02d:%02d" % (n // 60 % 60, n % 60)}
    lineas = [
        dict(base, type="user", message={"role": "user", "content": "pedido %d: " % n + "x" * 300}),
        dict(base, type="assistant", message={
            "id": mid, "model": "m-medida", "role": "assistant", "usage": uso,
            "content": [{"type": "tool_use", "id": "tu_%d" % n, "name": "Read",
                         "input": {"file_path": "src/modulo_%d.py" % n}}]}),
        dict(base, type="user", message={"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu_%d" % n,
             "content": ("def f_%d(x):\n    return x * %d\n" % (n, n)) * 220}]}),
        dict(base, type="assistant", message={
            "id": mid, "model": "m-medida", "role": "assistant", "usage": uso,
            "content": [{"type": "text", "text": "listo el paso %d" % n}]}),
    ]
    return "".join(json.dumps(l, separators=(",", ":")) + "\n" for l in lineas)


def transcripcion(ruta, bytes_objetivo, sesion=SESION):
    """Escribe turnos hasta pasar `bytes_objetivo`. Devuelve cuantos."""
    n = 0
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        escritos = 0
        while escritos < bytes_objetivo:
            n += 1
            texto = _mensaje(n, sesion)
            f.write(texto)
            escritos += len(texto.encode("utf-8"))
    return n


def _dibujar(renderizador, entrada):
    t = time.perf_counter()
    r = subprocess.run([sys.executable, renderizador], input=entrada,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return (time.perf_counter() - t) * 1000.0, r.stdout.decode("utf-8", "replace").strip()


def medir(corridas=11, mb=5.0):
    base = tempfile.mkdtemp(prefix="harness-latencia-barra-")
    try:
        proyecto = os.path.join(base, "proyecto con espacios")
        renderizador = armar(proyecto)
        ruta = os.path.join(base, "sesion.jsonl")
        turnos = transcripcion(ruta, int(mb * 1024 * 1024))
        entrada = json.dumps({"session_id": SESION, "transcript_path": ruta}).encode("utf-8")

        primera, linea = _dibujar(renderizador, entrada)
        quietas = [_dibujar(renderizador, entrada)[0] for _ in range(max(1, corridas))]
        nuevas = []
        for i in range(max(1, corridas)):
            with open(ruta, "a", encoding="utf-8", newline="\n") as f:
                f.write(_mensaje(turnos + 1 + i, SESION))
            nuevas.append(_dibujar(renderizador, entrada)[0])
        return {"primeraMs": round(primera), "p50Ms": round(statistics.median(quietas)),
                "conMensajeNuevoP50Ms": round(statistics.median(nuevas)),
                "corridas": max(1, corridas), "bytes": os.path.getsize(ruta),
                "umbralMs": UMBRAL_MS, "linea": linea}
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corridas", type=int, default=11)
    ap.add_argument("--mb", type=float, default=5.0)
    args = ap.parse_args(argv)
    sys.stdout.write(json.dumps(medir(args.corridas, args.mb)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
