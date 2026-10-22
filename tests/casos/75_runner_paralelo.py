# tests/casos/75_runner_paralelo.py - Task 6.1 (Verification Pipeline Performance).
#
# El runner paralelo y su oraculo, probados por PROCESOS REALES sobre layouts sinteticos: una
# carpeta <tmp>\ly\ con copias del oraculo, de correr.py y de las suites que genera este mismo
# archivo (ASCII, rutas cortas), fuera del arbol real. Los eventos de las fixtures y los
# temporales de cada corrida viven FUERA de la raiz del layout (<tmp>\ev, <tmp>\tp).
#
# Etapa 2 de la construccion (spec §29 paso 2): la infraestructura comun del layout y solo
# VP-E23, la compatibilidad del oraculo (M2, `-SoloCaso`). Los demas escenarios entran en las
# etapas siguientes sobre esta misma infraestructura. La etapa 5 agrega el timeout, la huella, la
# cancelacion y la limpieza (VP-E08, E10, E19, E20, E21) al final del archivo. La etapa 6 agrega el
# candado pesada.lock (VP-E22) antes del guardian. La etapa 7 agrega el comparador (VP-E15 a VP-E18).
#
# Restricciones que la suite impone a este archivo (spec §8.3): sin BOM (E-28, 00-encoding-fuentes),
# y sin el parametro viejo de la composicion ni las formas de analisis que E-57/E-61 de
# 63_harness_unico.py buscan en todo tests/.
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TAG_PARTIDA = "v0.34.0"
COMMIT_PARTIDA = "d86b285a9d0a4610a44a15ba3ca455be42d2edaa"
POWERSHELL = (Path(os.environ.get("SystemRoot", r"C:\Windows"))
              / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
MAX_TMP = 70                 # MAX_PATH: sin LongPathsEnabled las rutas del layout tienen que ser cortas
TOPE_S = 180                 # tope de una corrida del oraculo sobre un layout de pocas filas
TOPE_RUNNER_S = 240          # tope (una guarda, no una asercion) de una corrida del runner sobre un layout
SIN_VENTANA = 0x08000000 if os.name == "nt" else 0
VARIABLES_QUE_SE_QUITAN = ("PYTHONHASHSEED", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")
RUNNER = "Invoke-Tests-Parallel.ps1"
_CREADOS = []                # los <tmp> que creo este modulo (el guardian final los mira, etapa 5)
# La costura de testabilidad del agregador (spec 16.7) la elige el builder: es esta funcion del runner, que
# se alcanza cargando el script con dot-source (no ejecuta ninguna corrida).
COSTURA = "Get-ReporteDeCorrida"


# ---- Fixtures: se generan aca, ASCII, y cada una escribe un archivo de eventos ------------------
#
# Una suite sintetica es un dict: nombre, texto, motor ("ps" | "py"), filas, rojas. Las cuentas
# esperadas salen de `filas` y `rojas` (los parametros del generador), nunca de la salida.

_PS_EVENTOS = """function Write-T61Ev {
    param([string] $Tipo)
    $ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $ruta = Join-Path $env:T61_EV '@@SUITE@@.ev'
    [System.IO.File]::AppendAllText($ruta, ($Tipo + ' pid=' + $PID + ' t=' + $ms + "`n"))
}
"""

_PS_VERBOS = ("Assert-Igual 'fila-%02d' 1 1",
              "Assert-Contiene 'fila-%02d' 'a' 'abc'",
              "Assert-Vacio 'fila-%02d' ''",
              "Assert-Verdadero 'fila-%02d' $true")

_PY_EVENTOS = """import os
import time


def _ev(tipo):
    ms = int(time.time() * 1000)
    ruta = os.path.join(os.environ["T61_EV"], "@@SUITE@@.ev")
    with open(ruta, "a", encoding="ascii") as f:
        f.write("%s pid=%d t=%d\\n" % (tipo, os.getpid(), ms))


_ev("INICIO")
"""

_PY_VERBOS = ('t.igual("fila-%02d", 1, 1)',
              't.contiene("fila-%02d", "a", "abc")',
              't.no_contiene("fila-%02d", "z", "abc")',
              't.vacio("fila-%02d", "")',
              't.verdadero("fila-%02d", True)')


def ps_suite(nombre, filas, rojas=0, grupo=None, extra=None, dormir=0.0):
    """Un .ps1: `filas` filas, las primeras `rojas` rojas (esperado <1> / obtenido <2>).
    `extra` reemplaza el cuerpo (una fixture que tira, por ejemplo). `dormir`: segundos que sostiene
    la suite entre INICIO y FIN (es el worker el que duerme: no deja hijos)."""
    grupo = grupo or nombre[:-len(".ps1")]
    lineas = [_PS_EVENTOS.replace("@@SUITE@@", nombre), "Write-T61Ev 'INICIO'"]
    if extra is not None:
        lineas.append(extra)
        return {"nombre": nombre, "texto": "\n".join(lineas) + "\n", "motor": "ps",
                "filas": 1, "rojas": 1, "grupo": grupo}
    if dormir:
        lineas.append("Start-Sleep -Milliseconds %d" % int(dormir * 1000))
    lineas.append("Set-Grupo '%s'" % grupo)
    for i in range(1, filas + 1):
        if i <= rojas:
            lineas.append("Assert-Igual 'fila-%02d' 1 2" % i)
        else:
            lineas.append(_PS_VERBOS[i % len(_PS_VERBOS)] % i)
    lineas.append("Write-T61Ev 'FIN'")
    return {"nombre": nombre, "texto": "\n".join(lineas) + "\n", "motor": "ps",
            "filas": filas, "rojas": rojas, "grupo": grupo}


def py_suite(nombre, filas, rojas=0, no_carga=False, dormir=0.0):
    """Un .py: un test_ con `filas` filas, las primeras `rojas` rojas. `no_carga`: tira al importar,
    y correr.py lo cuenta como UNA fila roja (la de carga). `dormir`: segundos que sostiene la suite."""
    texto = _PY_EVENTOS.replace("@@SUITE@@", nombre)
    if no_carga:
        texto += "\nimport t61_no_existe_xyz  # noqa\n"
        return {"nombre": nombre, "texto": texto, "motor": "py", "filas": 1, "rojas": 1,
                "grupo": nombre[:-len(".py")]}
    texto += "\n\ndef test_filas(t):\n"
    if dormir:
        texto += "    time.sleep(%r)\n" % float(dormir)
    for i in range(1, filas + 1):
        if i <= rojas:
            texto += '    t.igual("fila-%02d", 1, 2)\n' % i
        else:
            texto += "    " + _PY_VERBOS[i % len(_PY_VERBOS)] % i + "\n"
    texto += '    _ev("FIN")\n'
    return {"nombre": nombre, "texto": texto, "motor": "py", "filas": filas, "rojas": rojas,
            "grupo": nombre[:-len(".py")]}


_PY_ENCUENTRO = """

def test_filas(t):
    # Suite de encuentro (VP-E12): marca que esta viva y espera ver otra marca; sostiene 2 s.
    marcas = os.environ["T61_VIVAS"]
    mia = os.path.join(marcas, "@@SUITE@@.alive")
    open(mia, "w").close()
    visto = False
    try:
        desde = time.time()
        while time.time() - desde < 15:
            if len(os.listdir(marcas)) >= 2:
                visto = True
                break
            time.sleep(0.05)
        t.verdadero("encuentro-con-otra-suite-viva", visto)
        if visto:
            time.sleep(2.0)
    finally:
        os.remove(mia)
    _ev("FIN")
"""


def py_encuentro(nombre):
    """Un .py que solo termina bien si, mientras vive, hay otra suite viva (marcas en T61_VIVAS)."""
    texto = _PY_EVENTOS.replace("@@SUITE@@", nombre) + _PY_ENCUENTRO.replace("@@SUITE@@", nombre)
    return {"nombre": nombre, "texto": texto, "motor": "py", "filas": 1, "rojas": 0,
            "grupo": nombre[:-len(".py")]}


# ---- Fixtures de la etapa 4b: fallos de lectura, stderr, procesos muertos y aislamiento -----------

def _suite_py(nombre, cuerpo, filas, rojas=0, antes=""):
    """Un .py con `antes` a nivel de modulo (despues de INICIO) y, si hay `cuerpo`, un test_filas con ese cuerpo."""
    texto = _PY_EVENTOS.replace("@@SUITE@@", nombre) + antes
    if cuerpo is not None:
        texto += "\n\ndef test_filas(t):\n" + cuerpo
    return {"nombre": nombre, "texto": texto, "motor": "py", "filas": filas, "rojas": rojas,
            "grupo": nombre[:-len(".py")]}


def py_decoy(nombre):
    """VP-E04(a): 10 filas, una roja cuyo detalle trae el texto `3/4 pasaron.` (senuelo para un lector que tome el
    primer `N/M pasaron.`): el oraculo lee 3/4 del detalle y los grupos suman 10."""
    cuerpo = "".join("    " + _PY_VERBOS[i % len(_PY_VERBOS)] % i + "\n" for i in range(1, 10))
    cuerpo += '    t.igual("fila-roja", "3/4 pasaron.", "otro")\n    _ev("FIN")\n'
    return _suite_py(nombre, cuerpo, 10, rojas=1)


def ps_decoy(nombre):
    """VP-E04(c): 3 filas, una roja cuyo detalle trae `7/9 pasaron.` (el oraculo no lo lee: cuenta las filas)."""
    texto = (_PS_EVENTOS.replace("@@SUITE@@", nombre) + "Write-T61Ev 'INICIO'\nSet-Grupo '%s'\n" % nombre[:-len(".ps1")]
             + _PS_VERBOS[1] % 1 + "\n" + _PS_VERBOS[2] % 2 + "\n"
             + "Assert-Igual 'fila-roja' '7/9 pasaron.' 'otro'\nWrite-T61Ev 'FIN'\n")
    return {"nombre": nombre, "texto": texto, "motor": "ps", "filas": 3, "rojas": 1, "grupo": nombre[:-len(".ps1")]}


def py_liar_ok(nombre):
    """VP-E04(b): 5 filas verdes que imprime `5/5 pasaron.` y TERMINA con exit 1 (atexit). El flush es obligatorio:
    os._exit dentro de atexit corre antes del flush final y se perderia el resumen."""
    cuerpo = "".join("    " + _PY_VERBOS[i % len(_PY_VERBOS)] % i + "\n" for i in range(1, 6)) + '    _ev("FIN")\n'
    return _suite_py(nombre, cuerpo, 5, antes="\nimport atexit\nimport sys\natexit.register(lambda: (sys.stdout.flush(), os._exit(1)))\n")


def py_liar_fail(nombre):
    """VP-E04(b): 3 verdes y 2 rojas que imprime `3/5 pasaron.` y TERMINA con exit 0 (correr.py llama a sys.exit por
    atributo y aca no hace nada)."""
    cuerpo = "".join("    " + _PY_VERBOS[i % len(_PY_VERBOS)] % i + "\n" for i in range(1, 4))
    cuerpo += '    t.igual("fila-04", 1, 2)\n    t.igual("fila-05", 1, 2)\n    _ev("FIN")\n'
    return _suite_py(nombre, cuerpo, 5, rojas=2, antes="\nimport sys\nsys.exit = lambda *a: None\n")


_SIN_RESUMEN = {
    "exit0": 'print("hola")\nsys.stdout.flush()\nos._exit(0)\n',          # imprime algo y sale 0 sin resumen
    "trunca": 'sys.stdout.write("12/")\nsys.stdout.flush()\nos._exit(0)\n',   # `12/` y corta
    "vacia": "os._exit(0)\n",                                             # no imprime nada
}


def py_sin_resumen(nombre, forma):
    """VP-E06: una suite Py que termina con os._exit(0) en tres formas, sin que correr.py llegue a su resumen."""
    return _suite_py(nombre, None, 0, antes="\nimport sys\n" + _SIN_RESUMEN[forma])


def py_cero(nombre):
    """VP-E06: una suite Py sin ningun test_: correr.py imprime `0/0 pasaron.` y sale 0 (verde, como el oraculo)."""
    return _suite_py(nombre, None, 0, antes='\n_ev("FIN")\n')


def py_stderr(nombre, marca):
    """VP-E07: dos filas verdes y UNA linea en stderr: el oraculo (2>&1 bajo Stop) corta ahi."""
    cuerpo = ('    import sys\n    t.verdadero("fila-01", True)\n    t.verdadero("fila-02", True)\n'
              '    sys.stderr.write(%r + "\\n")\n    sys.stderr.flush()\n    _ev("FIN")\n' % marca)
    return _suite_py(nombre, cuerpo, 2)


def ps_stderr(nombre, dormir=0.0):
    """VP-E07 / VP-E05: una fila verde y un `cmd /c "echo x 1>&2"` nativo (stderr de una suite PS). `dormir`: segundos
    que sostiene la suite despues de escribir en stderr (la sonda de VP-E05 la mata ahi)."""
    texto = _PS_EVENTOS.replace("@@SUITE@@", nombre) + "Write-T61Ev 'INICIO'\ncmd /c \"echo x 1>&2\"\n"
    if dormir:
        texto += "Start-Sleep -Milliseconds %d\n" % int(dormir * 1000)
    texto += "Set-Grupo '%s'\nAssert-Igual 'fila-01' 1 1\nWrite-T61Ev 'FIN'\n" % nombre[:-len(".ps1")]
    return {"nombre": nombre, "texto": texto, "motor": "ps", "filas": 1, "rojas": 0, "grupo": nombre[:-len(".ps1")]}


# VP-E09: cada suite vuelca (a <T61_EV>\<suite>.json) lo que ve de su temporal y de su entorno. Las marcas de
# encuentro (T61_VIVAS) NO se borran: una suite pasa la barrera cuando hay T61_BARRERA marcas, y cada marca la
# escribio una suite que sigue viva hasta ver la ultima: cuatro marcas son cuatro suites vivas a la vez.
_PS_TEMP = """
Write-T61Ev 'INICIO'
$t61Ini = @(Get-ChildItem -LiteralPath $env:TEMP -Force | ForEach-Object { $_.Name })
$t61Dir = Join-Path $env:TEMP 'gcba-harness'
[void][System.IO.Directory]::CreateDirectory($t61Dir)
[System.IO.File]::WriteAllText((Join-Path $t61Dir '@@SUITE@@.avisado'), 'x')
[System.IO.File]::WriteAllText((Join-Path $env:T61_VIVAS '@@SUITE@@.alive'), 'x')
$t61Desde = [DateTime]::UtcNow
while (@(Get-ChildItem -LiteralPath $env:T61_VIVAS).Count -lt [int]$env:T61_BARRERA -and ([DateTime]::UtcNow - $t61Desde).TotalSeconds -lt 30) { Start-Sleep -Milliseconds 50 }
$t61Marcas = @(Get-ChildItem -LiteralPath $env:T61_VIVAS).Count
$t61Vio = @(Get-ChildItem -LiteralPath $t61Dir -Filter '*.avisado' | ForEach-Object { $_.Name })
$t61Py = (& $env:T61_PY -c "import tempfile; print(tempfile.gettempdir())" | Out-String).Trim()
$t61Dump = [ordered]@{ TEMP = $env:TEMP; TMP = $env:TMP; TMPDIR = $env:TMPDIR; net = [System.IO.Path]::GetTempPath(); py = $t61Py; inicial = $t61Ini; avisados = $t61Vio; marcas = $t61Marcas }
[System.IO.File]::WriteAllText((Join-Path $env:T61_EV '@@SUITE@@.json'), (ConvertTo-Json -Compress -InputObject $t61Dump), (New-Object System.Text.UTF8Encoding $false))
Set-Grupo '@@GRUPO@@'
Assert-Verdadero 'barrera cumplida' ($t61Marcas -ge [int]$env:T61_BARRERA)
Write-T61Ev 'FIN'
"""

_PY_TEMP = """

def test_filas(t):
    import json
    import subprocess
    import tempfile
    inicial = sorted(os.listdir(os.environ["TEMP"]))
    d = os.path.join(os.environ["TEMP"], "gcba-harness")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "@@SUITE@@.avisado"), "w").close()
    vivas = os.environ["T61_VIVAS"]
    open(os.path.join(vivas, "@@SUITE@@.alive"), "w").close()
    barrera = int(os.environ["T61_BARRERA"])
    hasta = time.time() + 30
    while len(os.listdir(vivas)) < barrera and time.time() < hasta:
        time.sleep(0.05)
    marcas = len(os.listdir(vivas))
    vio = sorted(n for n in os.listdir(d) if n.endswith(".avisado"))
    ps = os.path.join(os.environ["SystemRoot"], "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    net = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
                          "[System.IO.Path]::GetTempPath()"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=60).stdout.decode("utf-8", "replace").strip()
    volcado = {"TEMP": os.environ["TEMP"], "TMP": os.environ["TMP"], "TMPDIR": os.environ["TMPDIR"], "net": net,
               "py": tempfile.gettempdir(), "inicial": inicial, "avisados": vio, "marcas": marcas}
    with open(os.path.join(os.environ["T61_EV"], "@@SUITE@@.json"), "w", encoding="ascii") as f:
        json.dump(volcado, f)
    t.verdadero("barrera cumplida", marcas >= barrera)
    _ev("FIN")
"""

_PY_ENV = """

def test_filas(t):
    import json
    import shutil
    import sys
    quitadas = ("TEMP", "TMP", "TMPDIR")
    volcado = {"env": {k: v for k, v in os.environ.items() if k.upper() not in quitadas and not k.startswith("=")},
               "cwd": os.getcwd(), "exe": sys.executable, "path": os.environ.get("PATH"),
               "bash": shutil.which("bash")}
    with open(os.path.join(os.environ["T61_EV"], "@@SUITE@@.json"), "w", encoding="ascii") as f:
        json.dump(volcado, f)
    t.verdadero("volcado escrito", True)
    _ev("FIN")
"""


def ps_temp(nombre):
    texto = _PS_EVENTOS.replace("@@SUITE@@", nombre) + _PS_TEMP.replace("@@SUITE@@", nombre).replace(
        "@@GRUPO@@", nombre[:-len(".ps1")])
    return {"nombre": nombre, "texto": texto, "motor": "ps", "filas": 1, "rojas": 0, "grupo": nombre[:-len(".ps1")]}


def py_temp(nombre):
    return _suite_py(nombre, None, 1, antes=_PY_TEMP.replace("@@SUITE@@", nombre))


def py_env(nombre):
    return _suite_py(nombre, None, 1, antes=_PY_ENV.replace("@@SUITE@@", nombre))


def esperado_final(suites):
    """(linea final, exit) que da el oraculo para ese conjunto de suites, de sus parametros."""
    total = sum(s["filas"] for s in suites)
    malas = sum(s["rojas"] for s in suites)
    if malas:
        return "%d/%d pasaron. %d fallaron." % (total - malas, total, malas), 1
    return "%d/%d pasaron." % (total, total), 0


# ---- El layout -----------------------------------------------------------------------------------

def _sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def _borrar(ruta):
    """rmtree que aguanta los archivos de solo lectura de .git y los reintentos de Windows."""
    def _soltar(funcion, camino, _info):
        os.chmod(camino, stat.S_IWRITE)
        funcion(camino)
    for intento in range(10):
        if not Path(ruta).exists():
            return
        try:
            shutil.rmtree(ruta, onerror=_soltar)
        except OSError:
            time.sleep(0.5)
    shutil.rmtree(ruta, ignore_errors=True)


def _git(cwd, *args):
    r = subprocess.run(["git"] + list(args), cwd=str(cwd), stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=SIN_VENTANA)
    if r.returncode != 0:
        raise RuntimeError("git %s fallo (%d): %s" % (" ".join(args), r.returncode,
                                                      r.stderr.decode("utf-8", "replace").strip()))
    return r.stdout


class Layout:
    """<tmp>\\ly = raiz del layout (repo git minimo). Los eventos (<tmp>\\ev_<corrida>) y el TEMP de cada
    corrida (<tmp>\\tp_<corrida>) quedan FUERA de ly: no ensucian el arbol del layout."""

    def __init__(self, suites, con_oraculo_partida=False, con_runner=False, manifest=None):
        """`con_runner`: copia el runner del arbol (verificada por hash) y escribe un manifest sintetico:
        `manifest` (texto) o, si es None, todas las suites `parallel` con maxSeconds 1.0."""
        self.suites = suites
        self.tmp = Path(tempfile.mkdtemp(prefix="t61_"))
        _CREADOS.append(self.tmp)
        self.ly = self.tmp / "ly"
        self.con_oraculo_partida = con_oraculo_partida
        self.con_runner = con_runner
        self.manifest = manifest
        self.oraculo = self.ly / "tests" / "Invoke-Tests.ps1"
        self.oraculo_partida = self.ly / "tests" / "Invoke-Tests-v034.ps1"
        self.runner = self.ly / "tests" / RUNNER
        self.manifest_ruta = self.ly / "tests" / "parallel-manifest.json"

    def crear(self):
        if len(str(self.tmp)) > MAX_TMP:
            raise RuntimeError("TEMP demasiado largo para MAX_PATH sin LongPathsEnabled: %s (%d > %d)"
                               % (self.tmp, len(str(self.tmp)), MAX_TMP))
        nombres = [s["nombre"] for s in self.suites]
        if len(set(nombres)) != len(nombres):
            raise RuntimeError("nombres de suite repetidos: %r" % nombres)
        (self.ly / "tests" / "casos").mkdir(parents=True)
        (self.ly / ".gitignore").write_bytes(b"__pycache__/\n*.pyc\n")
        # Las copias del arbol, verificadas por hash contra el archivo del arbol (bytes, CRLF incluido).
        for nombre in ("Invoke-Tests.ps1", "correr.py"):
            origen = RAIZ / "tests" / nombre
            destino = self.ly / "tests" / nombre
            shutil.copyfile(str(origen), str(destino))
            if _sha256(origen) != _sha256(destino):
                raise RuntimeError("la copia de %s no coincide con el arbol" % nombre)
        if self.con_oraculo_partida:
            self._copiar_oraculo_de_partida()
        if self.con_runner:
            origen, destino = RAIZ / "tests" / RUNNER, self.runner
            shutil.copyfile(str(origen), str(destino))
            if _sha256(origen) != _sha256(destino):
                raise RuntimeError("la copia de %s no coincide con el arbol" % RUNNER)
            texto = self.manifest
            if texto is None:
                texto = manifest_texto([ent(s["nombre"]) for s in self.suites])
            self.manifest_ruta.write_bytes(texto.encode("utf-8"))
        for s in self.suites:
            (self.ly / "tests" / "casos" / s["nombre"]).write_bytes(s["texto"].encode("ascii"))
        _git(self.ly, "init", "-q")
        _git(self.ly, "config", "core.autocrlf", "false")
        _git(self.ly, "config", "user.name", "t61")
        _git(self.ly, "config", "user.email", "t61@example.invalid")
        _git(self.ly, "config", "commit.gpgsign", "false")
        _git(self.ly, "add", "-A")
        _git(self.ly, "commit", "-q", "-m", "layout sintetico t61")
        sucio = self.estado()
        if sucio.strip():
            raise RuntimeError("precondicion: el layout nace sucio: %s" % sucio.strip()[:200])
        return self

    def _copiar_oraculo_de_partida(self):
        """El oraculo de v0.34.0, de git, a un archivo del layout. Identidad por BLOB ID: el blob es LF
        y el arbol es CRLF (.gitattributes), asi que el sha256 de los bytes nunca coincide."""
        esperado = _git(RAIZ, "rev-parse", "%s:tests/Invoke-Tests.ps1" % TAG_PARTIDA).decode().strip()
        contenido = _git(RAIZ, "show", "%s:tests/Invoke-Tests.ps1" % TAG_PARTIDA)
        self.oraculo_partida.write_bytes(contenido)
        obtenido = _git(RAIZ, "hash-object", "--no-filters", str(self.oraculo_partida)).decode().strip()
        if obtenido != esperado:
            raise RuntimeError("la copia del oraculo de %s no es el blob: %s != %s"
                               % (TAG_PARTIDA, obtenido, esperado))

    def estado(self):
        return _git(self.ly, "status", "--porcelain", "--untracked-files=all").decode("utf-8", "replace")

    def aislamiento(self, clave):
        """Un par (eventos, TEMP) propio de una corrida, FUERA de ly: asi varias corridas del oraculo
        pueden ir a la vez sobre el mismo layout sin pisarse los eventos ni las marcas."""
        ev, tp = self.tmp / ("ev_" + clave), self.tmp / ("tp_" + clave)
        ev.mkdir()
        tp.mkdir()
        return ev, tp

    def rutas(self, clave):
        """Lo propio de una corrida del runner, todo FUERA de ly: eventos, TEMP del runner, TempBase (vacio),
        carpeta de marcas de encuentro, y las rutas del candado y de la cancelacion (que NO se crean: las
        crea el runner, o el test cuando cancela)."""
        ev, tp = self.aislamiento(clave)
        tb, vi = self.tmp / ("tb_" + clave), self.tmp / ("vi_" + clave)
        tb.mkdir()
        vi.mkdir()
        return {"ev": ev, "tp": tp, "tb": tb, "vivas": vi,
                "lock": self.tmp / ("lk_" + clave) / "pesada.lock",
                "cancel": self.tmp / ("cn_" + clave) / "cancelar.flag"}

    def reescribir_manifest(self, texto, confirmar=False):
        self.manifest_ruta.write_bytes(texto.encode("utf-8"))
        if confirmar:
            _git(self.ly, "add", "-A")
            _git(self.ly, "commit", "-q", "-m", "manifest sintetico t61")

    @staticmethod
    def eventos(ev):
        """{archivo de eventos: [(tipo, pid, t)]}"""
        r = {}
        for p in sorted(Path(ev).iterdir()):
            if p.suffix != ".ev":            # los volcados (<suite>.json) de VP-E09 viven en la misma carpeta
                continue
            filas = []
            for linea in p.read_text(encoding="ascii").splitlines():
                m = re.match(r"^(\w+) pid=(\d+) t=(\d+)$", linea)
                filas.append((m.group(1), int(m.group(2)), int(m.group(3))) if m else ("?", 0, 0))
            r[p.name] = filas
        return r

    @staticmethod
    def entorno(ev, tp, vivas=None):
        env = os.environ.copy()
        for k in list(env):
            if k.upper() in VARIABLES_QUE_SE_QUITAN:
                del env[k]
        env["T61_EV"] = str(ev)
        env["TEMP"] = env["TMP"] = env["TMPDIR"] = str(tp)
        if vivas is not None:
            env["T61_VIVAS"] = str(vivas)
        return env

    def destruir(self):
        _borrar(self.tmp)


class Corrida:
    """Una corrida del oraculo: sus argumentos y, despues de correr, rc / stdout / stderr / eventos."""

    def __init__(self, layout, clave, script, args=()):
        self.layout, self.clave, self.script, self.args = layout, clave, script, list(args)
        self.ev, self.tp = layout.aislamiento(clave)
        self.rc = self.out = self.err = self.eventos = None

    def correr(self):
        """El oraculo se lanza como lo lanza quien lo usa: powershell -File, cwd = la raiz del layout.
        stdout y stderr SEPARADOS (nunca 2>&1: PowerShell 5.1 envuelve el stderr nativo y cambia el texto)."""
        cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", str(self.script)] + self.args
        r = subprocess.run(cmd, cwd=str(self.layout.ly), env=self.layout.entorno(self.ev, self.tp),
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=TOPE_S, creationflags=SIN_VENTANA)
        self.rc, self.out, self.err = r.returncode, r.stdout, r.stderr
        self.eventos = self.layout.eventos(self.ev)
        return self

    @property
    def lineas(self):
        return lineas_de(self.out)

    @property
    def texto(self):
        return self.out.decode("utf-8", "replace")

    @property
    def ultima(self):
        return ultima_linea(self.out)

    def inicios(self):
        """{archivo de eventos: cuantos INICIO}"""
        return {k: sum(1 for e in v if e[0] == "INICIO") for k, v in self.eventos.items()}


def correr_en_lotes(corridas, simultaneas=4):
    """Las corridas en hilos, de a `simultaneas`: cada una es un proceso powershell aparte, con su
    propio temporal y sus propios eventos. Si una explota (tope de tiempo), la excepcion sube."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=simultaneas) as pool:
        for futuro in [pool.submit(c.correr) for c in corridas]:
            futuro.result()
    return corridas


def lineas_de(salida):
    return salida.decode("utf-8", "replace").splitlines()


def ultima_linea(salida):
    no_vacias = [l for l in lineas_de(salida) if l.strip()]
    return no_vacias[-1] if no_vacias else ""


def primera_diferencia(a, b):
    """'' si son iguales byte a byte; si no, donde difieren (para que el rojo diga algo)."""
    if a == b:
        return ""
    la, lb = a.splitlines(), b.splitlines()
    for i, (x, y) in enumerate(zip(la, lb), 1):
        if x != y:
            return "linea %d: %r != %r" % (i, x[:100], y[:100])
    return "largo: %d != %d lineas (%d != %d bytes)" % (len(la), len(lb), len(a), len(b))


# ---- El runner: manifest sintetico, ejecucion, eventos, procesos, huella --------------------------

def ent(suite, cls="parallel", lane=None, maxs=1.0, to=None):
    """Una entrada de manifest sintetico: reason 't61', maxSeconds 1.0 y timeoutSeconds null salvo que se pida."""
    return {"suite": suite, "class": cls, "lane": lane, "maxSeconds": maxs, "timeoutSeconds": to,
            "reason": "t61"}


def manifest_texto(entradas, schema="parallel-manifest/1"):
    return json.dumps({"schema": schema, "suites": entradas}, indent=2) + "\n"


def esperar(pred, timeout, paso=0.1):
    """La unica forma de sincronizar de este archivo: sondea `pred` hasta que da verdadero o vence `timeout`.
    Devuelve lo ultimo que dio `pred` (falso si vencio)."""
    limite = time.time() + timeout
    while True:
        valor = pred()
        if valor or time.time() >= limite:
            return valor
        time.sleep(paso)


def _lector(pipe, trozos):
    try:
        while True:
            b = pipe.read1(65536)
            if not b:
                break
            trozos.append(b)
    except (OSError, ValueError):
        pass


def matar_arbol(pid):
    """taskkill /T /F sobre un proceso que lanzo ESTE test (solo se mira su codigo de salida: el texto esta localizado)."""
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SIN_VENTANA)


class Ejecucion:
    """Un runner de verdad: powershell -File <ly>\\tests\\Invoke-Tests-Parallel.ps1, con stdout y stderr por pipes
    SEPARADOS (nunca 2>&1), drenados por dos hilos (un runner que imprime mas de 64 KB no se bloquea)."""

    def __init__(self, ly, r, workers, extra=(), env_extra=None):
        self.ly, self.r = ly, r
        cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", str(ly.runner), "-Workers", str(workers),
               "-TempBase", str(r["tb"]), "-LockPath", str(r["lock"])] + [str(e) for e in extra]
        env = ly.entorno(r["ev"], r["tp"], r["vivas"])
        env.update(env_extra or {})
        self.env = env                    # lo que se le paso al runner (VP-E09 lo compara con lo que ve cada suite)
        self.t0 = time.time()
        self.proc = subprocess.Popen(cmd, cwd=str(ly.ly), env=env, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=SIN_VENTANA)
        self._out, self._err = [], []
        self._hilos = [threading.Thread(target=_lector, args=(self.proc.stdout, self._out), daemon=True),
                       threading.Thread(target=_lector, args=(self.proc.stderr, self._err), daemon=True)]
        for h in self._hilos:
            h.start()
        self.eventos = None
        self.t1 = None                    # cuando termino el runner (E08 mide el corte desde un evento observado)

    def esperar(self, timeout=TOPE_RUNNER_S):
        """Espera el fin del runner. Si vence el tope lo mata (arbol entero) y levanta con la salida parcial."""
        try:
            self.proc.wait(timeout=timeout)
            self.t1 = time.time()
        except subprocess.TimeoutExpired:
            self.matar()
            raise AssertionError("el runner no termino en %d s; salida parcial: %r" % (timeout, self.texto[-600:]))
        self._cerrar()
        self.eventos = self.ly.eventos(self.r["ev"])
        return self

    def matar(self):
        if self.proc.poll() is None:
            matar_arbol(self.proc.pid)
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self._cerrar()

    def _cerrar(self):
        for h in self._hilos:
            h.join(timeout=15)
        for p in (self.proc.stdout, self.proc.stderr):
            try:
                p.close()
            except (OSError, ValueError):
                pass

    @property
    def rc(self):
        return self.proc.returncode

    @property
    def out(self):
        return b"".join(self._out)

    @property
    def err(self):
        return b"".join(self._err)

    @property
    def texto(self):
        return self.out.decode("utf-8", "replace")

    @property
    def lineas(self):
        return lineas_de(self.out)

    @property
    def ultima(self):
        return ultima_linea(self.out)

    def inicios(self):
        return {k: sum(1 for e in v if e[0] == "INICIO") for k, v in self.eventos.items()}

    def finales(self):
        return {k: sum(1 for e in v if e[0] == "FIN") for k, v in self.eventos.items()}


def correr_runner(ly, r, workers, extra=(), env_extra=None):
    """Lanza el runner del layout. `r` es el resultado de ly.rutas(clave): el TempBase y el candado SALEN de ahi,
    siempre propios del test (un runner de prueba que tomara el pesada.lock real del usuario le pisaria el candado)."""
    return Ejecucion(ly, r, workers, extra, env_extra)


def intervalos(eventos):
    """{suite: (inicio_ms, fin_ms)} de los archivos de eventos (<suite>.ev); fin None si la suite no llego a FIN."""
    res = {}
    for nombre, filas in eventos.items():
        ini = [t for tipo, _p, t in filas if tipo == "INICIO"]
        fin = [t for tipo, _p, t in filas if tipo == "FIN"]
        res[nombre[:-len(".ev")]] = (ini[0] if ini else None, fin[-1] if fin else None)
    return res


def se_intersectan(a, b):
    """Dos intervalos se solapan si cada uno empieza antes de que termine el otro (tocarse no es solaparse)."""
    return a[0] < b[1] and b[0] < a[1]


def max_solapadas(ints):
    puntos = []
    for ini, fin in ints.values():
        puntos.append((ini, 1))
        puntos.append((fin, -1))
    puntos.sort(key=lambda p: (p[0], p[1]))
    vivas = mejor = 0
    for _t, delta in puntos:
        vivas += delta
        mejor = max(mejor, vivas)
    return mejor


def procesos():
    """Todos los procesos (pid, ppid, nombre, linea de comandos) por una sola consulta CIM. El token se busca
    en Python: si estuviera en la linea de comandos de la consulta, la consulta se encontraria a si misma."""
    cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
           "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine "
           "| ConvertTo-Json -Compress"]
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=90, creationflags=SIN_VENTANA)
    datos = json.loads(r.stdout.decode("utf-8", "replace") or "[]")
    if isinstance(datos, dict):
        datos = [datos]
    return [(int(d["ProcessId"]), int(d["ParentProcessId"]), d.get("Name") or "", d.get("CommandLine") or "")
            for d in datos]


def vivos_con(token):
    """Los procesos cuya linea de comandos contiene el token del layout (t61_<6>): workers, runner, hijos."""
    return [p for p in procesos() if token in p[3]]


def huella(ly):
    """La huella de la spec 5.1, calculada aparte del runner: HEAD + sha256(status) + sha256(lista ordenada de
    ruta, tamano, sha256 de lo no ignorado). Es la cuenta de huella.py de WU03-a."""
    raiz = ly.ly
    head = _git(raiz, "rev-parse", "HEAD").decode().strip()
    status = _git(raiz, "status", "--porcelain", "--untracked-files=all")
    lista = _git(raiz, "ls-files", "-c", "-o", "--exclude-standard", "-z").decode("utf-8", "replace").split("\0")
    filas = []
    for rel in sorted(a for a in lista if a):
        ruta = raiz / rel
        if not ruta.is_file():
            continue
        datos = ruta.read_bytes()
        filas.append("%s\t%d\t%s" % (rel, len(datos), hashlib.sha256(datos).hexdigest()))
    h_status = hashlib.sha256(status).hexdigest()
    h_files = hashlib.sha256("\n".join(filas).encode("utf-8")).hexdigest()
    return hashlib.sha256((head + h_status + h_files).encode("utf-8")).hexdigest().upper()


def region(salida):
    """El reporte comparable (A1): desde la ULTIMA linea `gcba-harness - tests` hasta el final, en bytes.
    Todo lo anterior (encabezado propio del runner, progreso, avisos con rutas) queda afuera. None si no hay."""
    ms = list(re.finditer(rb"(?m)^gcba-harness - tests\r?$", salida))
    return salida[ms[-1].start():] if ms else None


def lineas_del_reporte(ej):
    reg = region(ej.out)
    return reg.decode("utf-8", "replace").splitlines() if reg is not None else []


def grupos_ps(lineas):
    """{grupo: texto de la cuenta} de las lineas `  OK    g  (n)` y `  FALLA g  (m/n)` (antes del bloque Python)."""
    res = {}
    for l in lineas:
        if l.startswith("gcba-harness - tests (python)"):
            break
        m = re.match(r"^  (OK   |FALLA) (.+?)  \((\d+(?:/\d+)?)\)$", l)
        if m:
            res[m.group(2)] = (m.group(1).strip(), m.group(3))
    return res


def grupos_py(lineas):
    """[(estado, grupo, n)] de las lineas de grupo del bloque Python, en el orden en que salen."""
    res, dentro = [], False
    for l in lineas:
        if l.startswith("gcba-harness - tests (python)"):
            dentro = True
            continue
        if dentro:
            m = re.match(r"^  (OK   |FALLA) (\S+)  \((\d+)\)$", l)
            if m:
                res.append((m.group(1).strip(), m.group(2), int(m.group(3))))
    return res


def tb_vacio(r):
    return sorted(p.name for p in Path(r["tb"]).iterdir())


def lineas_de_progreso(ej):
    """Las lineas `[k/n] OK|FALLA|INFRA suite (n) seg s` que el runner imprime ANTES del reporte."""
    return [l for l in ej.lineas if re.match(r"^\[\d+/\d+\] (OK|FALLA|INFRA) ", l)]


def lineas_con(ej, patron):
    """Las lineas de TODO el stdout que cumplen el patron (anclado a inicio de linea por quien llama)."""
    return [l for l in ej.lineas if re.search(patron, l)]


def estado_en_progreso(ej, suite):
    """OK | FALLA | INFRA, de la linea de progreso `[k/n] <estado> <suite> (<n>) <seg> s` de esa suite (None si no sale)."""
    for l in lineas_de_progreso(ej):
        m = re.match(r"^\[\d+/\d+\] (OK|FALLA|INFRA) (\S+) \(", l)
        if m and m.group(2) == suite:
            return m.group(1)
    return None


def bloque_de_progreso(ej, suite):
    """La linea de progreso de la suite y las lineas con sangria de 4 que la siguen (sus fallos, su stderr, sus logs)."""
    lineas = ej.lineas
    for i, l in enumerate(lineas):
        if re.match(r"^\[\d+/\d+\] (OK|FALLA|INFRA) %s \(" % re.escape(suite), l):
            j = i + 1
            while j < len(lineas) and lineas[j].startswith("    "):
                j += 1
            return lineas[i:j]
    return []


def canon(ruta):
    """La forma comparable de un directorio (VP-E09): sin barra final, en su forma larga y sin mayusculas. Una ruta que ya
    no existe (el temporal de una suite se borra al terminar) se resuelve por su ancestro que si existe."""
    ruta = str(ruta).rstrip("\\/")
    cabeza, cola = ruta, []
    while cabeza and not os.path.exists(cabeza):
        cabeza, hoja = os.path.split(cabeza)
        if not hoja:
            break
        cola.insert(0, hoja)
    base = os.path.realpath(cabeza) if cabeza else ""
    return os.path.normcase(os.path.join(base, *cola) if cola else base)


def stop_process(pid):
    """Stop-Process desde afuera (lo que pide VP-E05): el proceso termina con exit -1, no con el 0 o el 1 del oraculo."""
    r = subprocess.run([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
                        "Stop-Process -Id %d -Force" % pid], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=90, creationflags=SIN_VENTANA)
    return r.returncode


def hijos_de(ppid, contiene):
    """Los procesos cuyo padre es `ppid` y cuya linea de comandos contiene `contiene`: (pid, ppid, nombre, linea)."""
    return [p for p in procesos() if p[1] == ppid and contiene in p[3]]


def leer_volcado(ev, suite):
    return json.loads((Path(ev) / (suite + ".json")).read_text(encoding="ascii"))


def interprete_del_oraculo(env):
    """El Python que resuelve el oraculo (Invoke-Tests.ps1: python, py, python3; vale el que corre y dice donde esta),
    con el PATH de `env`."""
    for c in ("python", "py", "python3"):
        exe = shutil.which(c, path=env.get("PATH", ""))
        if not exe:
            continue
        r = subprocess.run([exe, "-c", "import sys; print(sys.executable)"], env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60, creationflags=SIN_VENTANA)
        ruta = r.stdout.decode("utf-8", "replace").strip()
        if ruta and os.path.exists(ruta):
            return ruta
    return None


def _borrar_layout(ly, *ejecuciones):
    for ej in ejecuciones:
        try:
            ej.matar()
        except Exception:
            pass
    ly.destruir()


# ---- VP-E23: compatibilidad del oraculo ----------------------------------------------------------

def _suites_e23():
    return [ps_suite("ps_ok.ps1", 3),
            ps_suite("ps_rojo.ps1", 3, rojas=1),
            py_suite("caso_a.py", 3),
            py_suite("caso_a_extra.py", 3, rojas=1),
            py_suite("py_import_error.py", 0, no_carga=True)]


def _precondicion_de_partida(t, id_):
    """NB-14: la version de partida tiene que estar en el clon; si falta, el test FALLA con el motivo."""
    try:
        commit = _git(RAIZ, "rev-parse", "--verify", "%s^{commit}" % TAG_PARTIDA).decode().strip()
    except Exception as e:
        t.verdadero("%s precondicion: falta el tag %s en el clon (%s)" % (id_, TAG_PARTIDA, str(e)[:120]), False)
        return False
    t.igual("%s precondicion: %s apunta a la version de partida" % (id_, TAG_PARTIDA), COMMIT_PARTIDA, commit)
    return commit == COMMIT_PARTIDA


def test_vp_e23_el_texto_del_oraculo_conserva_lo_que_la_suite_exige(t):
    """VP-E23 - el texto del Invoke-Tests.ps1 del repo sigue conteniendo sys.executable (E-22, 66:471-476)
    y correr.py (ME-E51, 72:2330-2335), y declara -SoloCaso."""
    texto = (RAIZ / "tests" / "Invoke-Tests.ps1").read_text(encoding="utf-8-sig")
    t.contiene("VP-E23 el oraculo conserva sys.executable", "sys.executable", texto)
    t.contiene("VP-E23 el oraculo conserva la mencion de correr.py", "correr.py", texto)
    t.contiene("VP-E23 el oraculo declara -SoloCaso", "[string] $SoloCaso", texto)


def test_vp_e23_sin_parametros_el_oraculo_da_lo_mismo_que_v0_34_0_y_con_solocaso_corre_un_archivo(t):
    """VP-E23 - (a) sin parametros y con -Detallado, el oraculo del repo y el de v0.34.0 dan la misma
    salida estandar byte a byte y el mismo exit; (b) con -SoloCaso <x.py> y <y.ps1> corre exactamente
    ese archivo y la primera linea es la de corrida parcial, la ultima la combinada; (c) un archivo
    inexistente sale 1."""
    ID = "VP-E23"
    if not _precondicion_de_partida(t, ID):
        return
    suites = _suites_e23()
    ly = Layout(suites, con_oraculo_partida=True)
    try:
        ly.crear()
        todas = sorted(s["nombre"] + ".ev" for s in suites)
        final, rc_esperado = esperado_final(suites)
        t.verdadero("%s control: el layout mezcla suites verdes y rojas de los dos motores" % ID,
                    rc_esperado == 1 and {s["motor"] for s in suites} == {"ps", "py"})

        # Las diez corridas del oraculo, de a cuatro, cada una con sus eventos y su TEMP propios.
        por_nombre = {s["nombre"]: s for s in suites}
        generales = (("repo", ly.oraculo, []), ("repo_d", ly.oraculo, ["-Detallado"]),
                     ("partida", ly.oraculo_partida, []), ("partida_d", ly.oraculo_partida, ["-Detallado"]))
        parciales = (
            # (archivo pedido, argumentos extra, archivos de eventos esperados, nombres que NO pueden salir)
            ("caso_a.py", [], ["caso_a.py.ev"], ["ps_ok", "ps_rojo", "caso_a_extra", "py_import_error"]),
            ("ps_ok.ps1", ["-Detallado"], ["ps_ok.ps1.ev"], ["caso_a", "ps_rojo", "py_import_error"]),
            ("caso_a_extra.py", ["-Detallado"], ["caso_a_extra.py.ev"], ["ps_ok", "ps_rojo", "py_import_error"]),
            ("ps_rojo.ps1", [], ["ps_rojo.ps1.ev"], ["caso_a", "py_import_error"]),
        )
        inexistentes = ("no_existe.py", "CASO_A.PY")      # el nombre es EXACTO: otra capitalizacion no existe
        corridas = {c[0]: Corrida(ly, c[0], c[1], c[2]) for c in generales}
        for i, (pedido, extra, _ev, _aj) in enumerate(parciales):
            corridas["p%d" % i] = Corrida(ly, "p%d" % i, ly.oraculo, ["-SoloCaso", pedido] + extra)
        for i, nombre in enumerate(inexistentes):
            corridas["n%d" % i] = Corrida(ly, "n%d" % i, ly.oraculo, ["-SoloCaso", nombre])
        correr_en_lotes(list(corridas.values()))

        # (a) lo mismo que la version de partida, sin parametros y con -Detallado
        for etiqueta, clave in (("sin parametros", ""), ("con -Detallado", "_d")):
            r, p = corridas["repo" + clave], corridas["partida" + clave]
            t.igual("%s (a) %s: la salida estandar es identica byte a byte" % (ID, etiqueta),
                    "", primera_diferencia(r.out, p.out))
            t.igual("%s (a) %s: stderr identico" % (ID, etiqueta), "", primera_diferencia(r.err, p.err))
            t.igual("%s (a) %s: el mismo exit" % (ID, etiqueta), p.rc, r.rc)
            t.igual("%s (a) %s: el exit es el de la suite (rojo)" % (ID, etiqueta), rc_esperado, r.rc)
            t.igual("%s (a) %s: la ultima linea es la combinada, de los parametros" % (ID, etiqueta),
                    final, r.ultima)
            t.igual("%s (a) %s: corrieron las cinco suites, cada una una vez" % (ID, etiqueta),
                    {n: 1 for n in todas}, r.inicios())
            t.igual("%s (a) %s: la version de partida corrio lo mismo" % (ID, etiqueta), r.inicios(), p.inicios())
            t.no_contiene("%s (a) %s: sin el parametro no hay linea de corrida parcial" % (ID, etiqueta),
                          "Corrida parcial", r.texto)
            t.contiene("%s (a) %s: sin el parametro corre el motor de Python" % (ID, etiqueta),
                       "python tests/correr.py", r.texto)
            t.contiene("%s (a) %s: y el de PowerShell" % (ID, etiqueta), "(PowerShell).", r.texto)
        t.igual("%s (a) las corridas no ensuciaron el layout (eventos y temporales estan afuera)" % ID,
                "", ly.estado().strip())

        # (b) -SoloCaso corre exactamente un archivo
        for i, (pedido, extra, ev_esperado, ajenos) in enumerate(parciales):
            c = corridas["p%d" % i]
            suite = por_nombre[pedido]
            fin, rc_s = esperado_final([suite])
            lineas, texto = c.lineas, c.texto
            etiqueta = "-SoloCaso %s" % pedido
            t.igual("%s (b) %s: la primera linea es la de corrida parcial" % (ID, etiqueta),
                    "Corrida parcial (-SoloCaso %s): no es la compuerta." % pedido,
                    lineas[0] if lineas else "")
            t.igual("%s (b) %s: la ultima linea es la combinada" % (ID, etiqueta), fin, c.ultima)
            t.igual("%s (b) %s: el exit sigue la regla de la compuerta" % (ID, etiqueta), rc_s, c.rc)
            t.igual("%s (b) %s: un solo archivo de eventos, el pedido, con un INICIO" % (ID, etiqueta),
                    {ev_esperado[0]: 1}, c.inicios())
            t.vacio("%s (b) %s: ningun otro archivo aparece en la salida: %s" % (ID, etiqueta, ajenos),
                    [a for a in ajenos if a in texto])
            t.igual("%s (b) %s: stderr vacio" % (ID, etiqueta), b"", c.err)
            if pedido.endswith(".ps1"):
                t.no_contiene("%s (b) %s: un .ps1 no lanza Python" % (ID, etiqueta),
                              "python tests/correr.py", texto)
                t.no_contiene("%s (b) %s: y eso no cuenta como resumen ausente" % (ID, etiqueta),
                              "No se pudo leer el resumen", texto)
                t.contiene("%s (b) %s: imprime el resumen de PowerShell" % (ID, etiqueta), "(PowerShell).", texto)
            else:
                t.contiene("%s (b) %s: un .py corre correr.py -k" % (ID, etiqueta), "python tests/correr.py", texto)
            if extra:
                # -Detallado: el motor PS lista cada fila con un punto medio; correr.py, con 'ok  grupo / fila'
                marca = ("        \u00b7 fila-01" if pedido.endswith(".ps1")
                         else "ok  %s / fila-02" % suite["grupo"])
                t.contiene("%s (b) %s: -Detallado sigue andando en esta rama" % (ID, etiqueta), marca, texto)
        t.igual("%s (b) las corridas parciales no ensuciaron el layout" % ID, "", ly.estado().strip())

        # (c) un archivo inexistente sale 1 y no corre nada
        for i, inexistente in enumerate(inexistentes):
            c = corridas["n%d" % i]
            etiqueta = "-SoloCaso %s" % inexistente
            t.igual("%s (c) %s: sale 1" % (ID, etiqueta), 1, c.rc)
            t.contiene("%s (c) %s: dice cual" % (ID, etiqueta), inexistente, c.texto)
            t.igual("%s (c) %s: la primera linea es la de corrida parcial" % (ID, etiqueta),
                    "Corrida parcial (-SoloCaso %s): no es la compuerta." % inexistente,
                    (c.lineas or [""])[0])
            t.igual("%s (c) %s: no corrio nada" % (ID, etiqueta), [], sorted(c.eventos))
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        ly.destruir()


def test_vp_e23_solocaso_saca_el_grupo_de_la_fila_de_carga_del_archivo_pedido(t):
    """VP-E23 / regla B6 (spec §5.7, §21, VX-19) - una fixture .ps1 que tira a mitad, bajo -SoloCaso, aporta
    exactamente UNA fila 'el archivo de casos se pudo cargar' con grupo = su BaseName, aunque haya pisado
    $caso y $nombre antes de tirar (03-instalador.ps1:846 y 65-inst/66-inst lo hacen en el scope del oraculo)."""
    ID = "VP-E23"
    pisa = ps_suite("ps_pisa.ps1", 1, extra="$caso = 'X'\n$nombre = 'Y'\nthrow 'boom'")
    ly = Layout([pisa])
    try:
        ly.crear()
        c = Corrida(ly, "b6", ly.oraculo, ["-SoloCaso", "ps_pisa.ps1"]).correr()
        out, rc, lineas = c.out, c.rc, c.lineas
        filas_de_carga = [l for l in lineas if l.rstrip().endswith("] el archivo de casos se pudo cargar")]
        t.igual("%s B6 la primera linea es la de corrida parcial" % ID,
                "Corrida parcial (-SoloCaso ps_pisa.ps1): no es la compuerta.", lineas[0] if lineas else "")
        t.igual("%s B6 una sola fila de carga, con grupo = BaseName del archivo pedido" % ID,
                ["  [ps_pisa] el archivo de casos se pudo cargar"], [l.rstrip() for l in filas_de_carga])
        t.igual("%s B6 el grupo es uno solo, el del archivo (no X ni Y)" % ID,
                ["  FALLA ps_pisa  (1/1)"], [l.rstrip() for l in lineas if l.startswith("  FALLA ") or l.startswith("  OK ")])
        t.contiene("%s B6 la excepcion del caso queda visible" % ID, "boom", out.decode("utf-8", "replace"))
        t.igual("%s B6 la ultima linea es la combinada" % ID, "0/1 pasaron. 1 fallaron.", ultima_linea(out))
        t.igual("%s B6 sale 1" % ID, 1, rc)
        ev = c.eventos
        t.igual("%s B6 un solo archivo de eventos, un INICIO y ningun FIN (la fixture tiro)" % ID,
                (["ps_pisa.ps1.ev"], ["INICIO"]),
                (sorted(ev), [e[0] for e in ev.get("ps_pisa.ps1.ev", [])]))
    except Exception as e:
        t.verdadero("%s B6 el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        ly.destruir()


# ---- VP-E01, VP-E02, VP-E11, VP-E12, VP-E13, VP-E14 y VP-E24 parte B: el runner -----------------------
#
# Etapa 4 (lote a) de la construccion (spec §29 paso 4): los escenarios del nucleo del runner. Cada uno corre
# el runner REAL (powershell -File) sobre un layout sintetico, con -TempBase y -LockPath propios.

def _final_verde(suites):
    return "%d/%d pasaron." % (sum(s["filas"] for s in suites), sum(s["filas"] for s in suites))


def test_vp_e01_con_seis_suites_verdes_de_dos_motores_el_runner_sale_0_con_la_suma(t):
    """VP-E01 - seis suites verdes (dos .ps1 y cuatro .py, dos de ellas con un stem prefijo del otro), N = 2:
    exit 0; la ultima linea es <ok>/<total> pasaron. con ok == total == la suma de las seis; cada suite un solo
    INICIO; cada suite Py reporta solo su stem."""
    ID = "VP-E01"
    suites = [ps_suite("ps_a.ps1", 3), ps_suite("ps_b.ps1", 4),
              py_suite("caso_a.py", 3), py_suite("caso_a_extra.py", 4),
              py_suite("caso_c.py", 5), py_suite("caso_d.py", 2)]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ly.crear()
        h0 = huella(ly)
        r = ly.rutas("e01")
        ej = correr_runner(ly, r, 2).esperar()
        total = sum(s["filas"] for s in suites)
        todas = sorted(s["nombre"] + ".ev" for s in suites)
        t.igual("%s el exit es 0" % ID, 0, ej.rc)
        t.igual("%s la ultima linea es <suma>/<suma> pasaron. (de los parametros, no de la salida)" % ID,
                "%d/%d pasaron." % (total, total), ej.ultima)
        t.igual("%s cada suite tiene un solo INICIO" % ID, {n: 1 for n in todas}, ej.inicios())
        t.igual("%s y un solo FIN" % ID, {n: 1 for n in todas}, ej.finales())
        lineas = lineas_del_reporte(ej)
        t.igual("%s cada suite Py reporta solo su stem, con su cuenta, en orden" % ID,
                [("OK", "caso_a", 3), ("OK", "caso_a_extra", 4), ("OK", "caso_c", 5), ("OK", "caso_d", 2)],
                grupos_py(lineas))
        t.igual("%s los grupos PS son los de los dos .ps1" % ID,
                {"ps_a": ("OK", "3"), "ps_b": ("OK", "4")}, grupos_ps(lineas))
        t.igual("%s sin lineas INFRA ni AVISO" % ID, [], lineas_con(ej, r"^(INFRA|AVISO) "))
        prog = lineas_de_progreso(ej)
        t.igual("%s seis lineas de progreso [k/6] OK, una por suite" % ID,
                sorted(s["nombre"] for s in suites),
                sorted(re.match(r"^\[\d+/6\] OK (\S+) \(\d+\) ", l).group(1) for l in prog if re.match(r"^\[\d+/6\] OK ", l)))
        t.no_contiene("%s no es una corrida parcial" % ID, "Corrida parcial", ej.texto)
        t.igual("%s stderr del runner vacio" % ID, b"", ej.err)
        t.igual("%s verde y limpia: TempBase vacio (ni raiz, ni sidecar)" % ID, [], tb_vacio(r))
        t.verdadero("%s el candado pesada.lock existe y no se borra" % ID, Path(r["lock"]).is_file())
        t.verdadero("%s pesada.json informativo al lado" % ID, Path(r["lock"]).with_suffix(".json").is_file())
        t.igual("%s la huella del arbol es la del principio" % ID, h0, huella(ly))
        t.igual("%s el arbol del layout queda limpio" % ID, "", ly.estado().strip())
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e02_con_filas_rojas_en_los_dos_motores_el_runner_sale_1_y_cuenta_los_fallos(t):
    """VP-E02 - una suite PS con 2 de 5 rojas, una Py con 1 de 7 y cuatro verdes, N = 4: exit 1; N fallaron. con
    N = 3; Fallos: y MAL contienen exactamente esas tres filas, PS antes que Py; las cuatro verdes salen OK."""
    ID = "VP-E02"
    suites = [ps_suite("ps_rojo.ps1", 5, rojas=2), py_suite("py_rojo.py", 7, rojas=1),
              ps_suite("ps_ok1.ps1", 3), ps_suite("ps_ok2.ps1", 3),
              py_suite("py_ok1.py", 4), py_suite("py_ok2.py", 4)]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ly.crear()
        r = ly.rutas("e02")
        ej = correr_runner(ly, r, 4).esperar()
        final, rc_esperado = esperado_final(suites)
        lineas = lineas_del_reporte(ej)
        t.igual("%s el exit es 1" % ID, 1, ej.rc)
        t.igual("%s la ultima linea dice 23/26 y 3 fallaron." % ID, "23/26 pasaron. 3 fallaron.", ej.ultima)
        t.igual("%s coincide con lo que da el oraculo para esos parametros" % ID, final, ej.ultima)
        i_fallos = lineas.index("Fallos:") if "Fallos:" in lineas else -1
        filas_ps = [l for l in lineas[i_fallos + 1:] if re.match(r"^  \[", l)] if i_fallos >= 0 else []
        malas_py = [l for l in lineas if re.match(r"^    MAL ", l)]
        t.igual("%s Fallos: tiene exactamente las dos filas PS" % ID,
                ["  [ps_rojo] fila-01", "  [ps_rojo] fila-02"], filas_ps)
        t.igual("%s hay exactamente una linea MAL, de la suite Py" % ID, 1, len(malas_py))
        t.verdadero("%s y es la fila fila-01 de py_rojo" % ID,
                    bool(malas_py) and malas_py[0].startswith("    MAL py_rojo / fila-01 "))
        i_mal = next((i for i, l in enumerate(lineas) if l.startswith("    MAL ")), -1)
        t.verdadero("%s Fallos: (PS) sale antes que MAL (Py)" % ID, 0 <= i_fallos < i_mal)
        g = grupos_ps(lineas)
        t.igual("%s el grupo PS rojo dice 2/5" % ID, ("FALLA", "2/5"), g.get("ps_rojo"))
        t.igual("%s los dos .ps1 verdes salen OK con su cuenta" % ID,
                [("OK", "3"), ("OK", "3")], [g.get("ps_ok1"), g.get("ps_ok2")])
        gp = {x[1]: (x[0], x[2]) for x in grupos_py(lineas)}
        t.igual("%s la Py roja sale FALLA con sus 7 y las dos verdes OK" % ID,
                {"py_rojo": ("FALLA", 7), "py_ok1": ("OK", 4), "py_ok2": ("OK", 4)}, gp)
        t.igual("%s sin INFRA: son filas rojas, no errores de infraestructura" % ID, [], lineas_con(ej, r"^INFRA "))
        t.igual("%s las seis corrieron, una vez cada una" % ID,
                {n: 1 for n in sorted(s["nombre"] + ".ev" for s in suites)}, ej.inicios())
        # La corrida roja conserva su raiz y deja su sidecar liberado al lado (spec 19.5, caso 2).
        t.verdadero("%s roja: queda la raiz hpp-<id> y su .lock, y nada mas" % ID,
                    len(tb_vacio(r)) == 2 and all(re.match(r"^hpp-[0-9a-f]{8}(\.lock)?$", n) for n in tb_vacio(r)))
        t.verdadero("%s y el resumen imprime donde quedaron los logs" % ID, "Logs de la corrida" in ej.texto)
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e11_serial_y_desconocida_corren_solas_y_el_carril_nunca_se_solapa(t):
    """VP-E11 - dos suites serial, dos del mismo carril y una sin entrada, N = 2, por los intervalos: durante
    cada serial y durante la desconocida no hay otra suite viva; las dos del carril nunca se solapan; la
    desconocida corre, sale AVISO SUITE_NO_CLASIFICADA y su resultado es el de sus aserciones."""
    ID = "VP-E11"
    # par_corto.py es la ULTIMA suite del pool (la de menor maxSeconds) y la desconocida se lanza justo despues: tiene que seguir viva
    # cuando arranca el cuerpo de la desconocida (el arranque de un worker son ~3 s), si no el escenario no ve que se la trate como parallel
    # (etapa 9, VM-06a: con dormir=1.0 la desconocida nunca se solapaba y la mutacion pasaba en verde).
    suites = [ps_suite("ser_1.ps1", 1, dormir=1.5), py_suite("ser_2.py", 1, dormir=1.5),
              py_suite("lan_1.py", 1, dormir=2.5), ps_suite("lan_2.ps1", 1, dormir=2.5),
              py_suite("par_largo.py", 1, dormir=5.0), py_suite("par_corto.py", 1, dormir=9.0),
              py_suite("desc.py", 1, dormir=1.5)]
    manifest = manifest_texto([
        ent("ser_1.ps1", "serial", maxs=50.0), ent("ser_2.py", "serial", maxs=50.0),
        ent("lan_1.py", "lane", "motor", maxs=30.0), ent("lan_2.ps1", "lane", "motor", maxs=30.0),
        ent("par_largo.py", "parallel", maxs=20.0), ent("par_corto.py", "parallel", maxs=10.0)])
    ly = Layout(suites, con_runner=True, manifest=manifest)
    ej = None
    try:
        ly.crear()
        r = ly.rutas("e11")
        ej = correr_runner(ly, r, 2).esperar()
        ints = intervalos(ej.eventos)
        completos = all(v[0] is not None and v[1] is not None for v in ints.values()) and len(ints) == 7
        t.verdadero("%s control: las siete suites tienen su intervalo completo" % ID, completos)
        if not completos:
            return
        solas = ["ser_1.ps1", "ser_2.py", "desc.py"]
        for s in solas:
            otras = [n for n in ints if n != s and se_intersectan(ints[s], ints[n])]
            t.igual("%s durante %s no hay otra suite viva" % (ID, s), [], otras)
        t.verdadero("%s las dos del carril no se solapan" % ID, not se_intersectan(ints["lan_1.py"], ints["lan_2.ps1"]))
        t.verdadero("%s control positivo: el pool convive (par_largo se solapa con una del carril)" % ID,
                    se_intersectan(ints["par_largo.py"], ints["lan_1.py"])
                    or se_intersectan(ints["par_largo.py"], ints["lan_2.ps1"]))
        fin_pool = max(ints[n][1] for n in ("lan_1.py", "lan_2.ps1", "par_largo.py", "par_corto.py"))
        t.verdadero("%s las seriales y la desconocida corren despues de todo el pool" % ID,
                    min(ints[n][0] for n in solas) >= fin_pool)
        lineas = lineas_del_reporte(ej)
        t.igual("%s AVISO SUITE_NO_CLASIFICADA nombra la desconocida" % ID,
                ["AVISO SUITE_NO_CLASIFICADA desc.py"], [l for l in lineas if l.startswith("AVISO ")])
        t.igual("%s la desconocida sale OK: su resultado es el de sus aserciones" % ID, 1,
                len([l for l in lineas_de_progreso(ej) if l.startswith("[") and " OK desc.py " in l]))
        t.igual("%s exit 0 y la linea final verde (7/7)" % ID, (0, "7/7 pasaron."), (ej.rc, ej.ultima))
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e12_nunca_hay_mas_de_n_suites_vivas_y_hay_n_y_workers_fuera_de_rango_no_corre_nada(t):
    """VP-E12 - con N = 2 y cuatro suites de encuentro (cada una espera ver dos marcas vivas y sostiene 2 s), el
    maximo de suites vivas a la vez es exactamente 2 y la corrida termina; con -Workers 0 o 5 el runner sale 1
    sin correr nada."""
    ID = "VP-E12"
    # El oraculo (y el runner, igual) pide al menos un .ps1: lo hay, pero serial, asi corre solo y al final.
    suites = [py_encuentro("enc_%d.py" % i) for i in range(1, 5)] + [ps_suite("ps_base.ps1", 1)]
    manifest = manifest_texto([ent("enc_%d.py" % i) for i in range(1, 5)] + [ent("ps_base.ps1", "serial")])
    ly = Layout(suites, con_runner=True, manifest=manifest)
    ly2 = Layout([py_suite("trivial.py", 1)], con_runner=True)
    ejs = []
    try:
        ly.crear()
        r = ly.rutas("e12")
        ej = correr_runner(ly, r, 2).esperar()
        ejs.append(ej)
        ints = intervalos(ej.eventos)
        t.igual("%s las cinco suites terminaron (FIN)" % ID, 5, sum(1 for v in ints.values() if v[1] is not None))
        t.igual("%s el maximo de suites vivas a la vez es exactamente 2" % ID, 2, max_solapadas(ints))
        t.igual("%s exit 0 y la linea final verde (5/5)" % ID, (0, "5/5 pasaron."), (ej.rc, ej.ultima))
        t.no_contiene("%s ninguna suite se quedo sin encuentro" % ID, "encuentro-con-otra-suite-viva", ej.texto)

        ly2.crear()
        for n in (0, 5):
            r2 = ly2.rutas("w%d" % n)
            e2 = correr_runner(ly2, r2, n).esperar()
            ejs.append(e2)
            t.igual("%s -Workers %d: sale 1" % (ID, n), 1, e2.rc)
            t.igual("%s -Workers %d: no corrio ninguna suite (cero archivos de eventos)" % (ID, n), [], sorted(e2.eventos))
            t.igual("%s -Workers %d: no creo nada en TempBase" % (ID, n), [], tb_vacio(r2))
            t.verdadero("%s -Workers %d: ni tomo el candado" % (ID, n), not Path(r2["lock"]).exists())
            t.verdadero("%s -Workers %d: lo dice" % (ID, n), "ARGUMENTO_INVALIDO" in e2.texto and "-Workers" in e2.texto)
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *ejs)
        _borrar_layout(ly2)


# VP-E13: el agregador por la costura de testabilidad (spec 16.7), con registros armados a mano.

def _reg(suite, engine, ok, total, grupos, exit_code=0, forma="verde", n_fallaron=None, infra=None,
         state="TERMINADA", reported=True):
    """Un registro de suite con los campos de la spec 15.1 (la forma es interna del runner y puede cambiar)."""
    return {"suite": suite, "engine": engine, "index": 0, "state": state, "exitCode": exit_code,
            "reported": reported, "forma": forma, "nFallaron": n_fallaron, "sinResumen": False,
            "ok": ok, "total": total,
            "groups": [{"name": g[0], "n": g[1], "malos": g[2], "detalle": []} for g in grupos],
            "failedRows": [], "failedLines": [], "pyRowLines": [], "rows": [], "infra": infra,
            "timeoutSeconds": None, "seconds": 0.0}


_DRIVER_E13 = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$lockReal = Join-Path $env:LOCALAPPDATA 'gcba-harness\recursos\pesada.lock'
function Get-EstadoLock {
    if (Test-Path -LiteralPath $lockReal) { $i = Get-Item -LiteralPath $lockReal; return ('{0}/{1}' -f $i.Length, $i.LastWriteTimeUtc.Ticks) }
    return 'no existe'
}
$lockAntes = Get-EstadoLock
$tmpAntes = @(Get-ChildItem -LiteralPath $env:TEMP -Force).Count
$carga = (. $env:T61_RUNNER *>&1 | Out-String)
'T61|CARGA|vacia=' + [string]::IsNullOrWhiteSpace($carga)
'T61|FUNCION|' + [bool](Get-Command $env:T61_COSTURA -ErrorAction SilentlyContinue)
'T61|TMP|igual=' + ($tmpAntes -eq @(Get-ChildItem -LiteralPath $env:TEMP -Force).Count)
'T61|LOCK|igual=' + ($lockAntes -eq (Get-EstadoLock))
$casos = [System.IO.File]::ReadAllText($env:T61_CASOS) | ConvertFrom-Json
foreach ($c in $casos) {
    $r = & $env:T61_COSTURA -Registros @($c.registros) -Enumeradas @($c.enumeradas) -HuellaInicial $c.hIni -HuellaFinal $c.hFin -ManifestOk ([bool]$c.manifestOk)
    'T61|CASO|' + $c.nombre + '|' + $r.Exit
    $r.Texto
    'T61|FIN|' + $c.nombre
}
'T61|LOCK2|igual=' + ($lockAntes -eq (Get-EstadoLock))
"""


def invocar_agregador(ly, clave, casos):
    """Adaptador de la costura: carga el runner del layout por dot-source en UN powershell con PATH minimo (sin git ni
    python: cualquier intento de lanzarlos explota) y llama COSTURA con cada caso. Devuelve (salida_de_carga, {caso:
    (exit, texto)})."""
    ev, tp = ly.aislamiento(clave)
    driver = ly.tmp / ("driver_%s.ps1" % clave)
    driver.write_bytes(_DRIVER_E13.encode("utf-8"))
    archivo = ly.tmp / ("casos_%s.json" % clave)
    archivo.write_bytes(json.dumps(casos).encode("utf-8"))
    env = ly.entorno(ev, tp)
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    env["PATH"] = sysroot + r"\System32;" + sysroot
    env.update({"T61_RUNNER": str(ly.runner), "T61_COSTURA": COSTURA, "T61_CASOS": str(archivo)})
    r = subprocess.run([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                        "-File", str(driver)], cwd=str(ly.ly), env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TOPE_S, creationflags=SIN_VENTANA)
    texto = r.stdout.decode("utf-8", "replace")
    meta, res, actual, buf = {}, {}, None, []
    for l in texto.splitlines():
        m = re.match(r"^T61\|(CARGA|FUNCION|TMP|LOCK|LOCK2)\|(.*)$", l)
        if m:
            meta[m.group(1)] = m.group(2)
        elif l.startswith("T61|CASO|"):
            _, _, nombre, cod = l.split("|", 3)
            actual, buf = nombre, []
            res[nombre] = [int(cod) if cod.strip().isdigit() else cod, ""]
        elif l.startswith("T61|FIN|"):
            res[actual][1] = "\n".join(buf)
            actual = None
        elif actual is not None:
            buf.append(l)
    return meta, {k: tuple(v) for k, v in res.items()}, r.stderr.decode("utf-8", "replace"), r.returncode


def test_vp_e13_el_agregador_por_su_costura_sale_distinto_de_cero_y_nombra_cada_inconsistencia(t):
    """VP-E13 - el agregador, invocado por la costura de la spec 16.7 con registros armados a mano y sin lanzar ningun
    worker (sin tocar TempBase, ni el candado, ni el arbol), sale != 0 y nombra: una suite faltante, una sobrante, una
    repetida, una con INFRA, una con exit 0 y 'N fallaron.', una con grupo ajeno y una con total nulo (ERROR_INTERNO,
    sin tragarse la excepcion); con el conjunto completo y coherente sale 0 con el reporte canonico; cargar el runner
    no ejecuta ninguna corrida."""
    ID = "VP-E13"
    a = _reg("a.ps1", "ps", 3, 3, [("a", 3, 0)])
    b = _reg("b.py", "py", 2, 2, [("b", 2, 0)])
    c = _reg("c.py", "py", 4, 4, [("c", 4, 0)])
    enum = ["a.ps1", "b.py", "c.py"]

    def caso(nombre, regs, enumeradas=None, h_fin="H1"):
        return {"nombre": nombre, "registros": regs, "enumeradas": enumeradas or enum,
                "hIni": "H1", "hFin": h_fin, "manifestOk": True}

    casos = [
        caso("completo", [a, b, c]),
        caso("falta", [a, b]),
        caso("sobra", [a, b, c, _reg("z.py", "py", 1, 1, [("z", 1, 0)])]),
        caso("repetida", [a, b, b, c]),
        caso("infra", [a, _reg("b.py", "py", 0, 0, [], state="MUERTA", reported=False, infra="WORKER_MUERTO"), c]),
        caso("exit0_con_fallaron", [a, b, _reg("c.py", "py", 3, 5, [("c", 5, 2)], exit_code=0, forma="roja", n_fallaron=2)]),
        caso("grupo_ajeno", [a, _reg("b.py", "py", 2, 2, [("otro", 2, 0)]), c]),
        caso("total_nulo", [a, _reg("b.py", "py", 2, None, [("b", 2, 0)]), c]),
        caso("arbol_cambiado", [a, b, c], h_fin="H2"),
    ]
    ly = Layout([py_suite("trivial.py", 1)], con_runner=True)
    try:
        ly.crear()
        h0 = huella(ly)
        ev_antes = sorted(ly.eventos(ly.aislamiento("pre")[0]))
        meta, res, err, rc = invocar_agregador(ly, "e13", casos)
        t.igual("%s el driver termino bien" % ID, (0, ""), (rc, err.strip()))
        t.igual("%s cargar el runner no imprime nada (no ejecuta ninguna corrida)" % ID, "vacia=True", meta.get("CARGA"))
        t.igual("%s la costura %s existe despues de cargarlo" % (ID, COSTURA), "True", meta.get("FUNCION"))
        t.igual("%s cargarlo no toco el temporal del proceso" % ID, "igual=True", meta.get("TMP"))
        t.igual("%s ni el candado real del usuario (antes de la costura)" % ID, "igual=True", meta.get("LOCK"))
        t.igual("%s ni el candado real del usuario (despues de los casos)" % ID, "igual=True", meta.get("LOCK2"))
        t.igual("%s los nueve casos volvieron con su resultado" % ID, sorted(c["nombre"] for c in casos), sorted(res))

        def lineas_de_caso(n):
            return res.get(n, (None, ""))[1].splitlines()

        def finales(n):
            return [l for l in lineas_de_caso(n) if re.match(r"^\d+/\d+ pasaron\.( \d+ fallaron\.)?$", l)]

        ex, txt = res.get("completo", (None, ""))
        t.igual("%s completo y coherente: sale 0" % ID, 0, ex)
        t.igual("%s y la ultima linea es la suma de los registros (9/9)" % ID, "9/9 pasaron.", (lineas_de_caso("completo") or [""])[-1])
        t.verdadero("%s el reporte canonico trae el grupo PS y los dos de Python en orden" % ID,
                    "  OK    a  (3)" in txt and txt.index("  OK    b  (2)") < txt.index("  OK    c  (4)"))
        t.no_contiene("%s sin INFRA el reporte completo" % ID, "INFRA ", txt)

        esperados = (
            ("falta", r"^INFRA SUITE_AUSENTE c\.py$", "una suite faltante"),
            ("sobra", r"^INFRA \w+ z\.py\b", "una suite sobrante"),
            ("repetida", r"^INFRA SUITE_DUPLICADA b\.py$", "una suite repetida"),
            ("infra", r"^INFRA WORKER_MUERTO b\.py$", "una suite con INFRA"),
            ("exit0_con_fallaron", r"^INFRA EXIT_INCOHERENTE c\.py\b", "exit 0 con N fallaron."),
            ("grupo_ajeno", r"^INFRA GRUPO_AJENO b\.py\b", "un grupo ajeno"),
            ("total_nulo", r"^INFRA ERROR_INTERNO ", "un total nulo"),
            ("arbol_cambiado", r"^INFRA ARBOL_CAMBIADO", "una huella final distinta"),
        )
        for nombre, patron, que in esperados:
            ex, txt = res.get(nombre, (None, ""))
            t.verdadero("%s %s: sale distinto de cero" % (ID, que), isinstance(ex, int) and ex != 0)
            t.verdadero("%s %s: lo nombra (%s)" % (ID, que, patron),
                        any(re.search(patron, l) for l in txt.splitlines()))
            t.verdadero("%s %s: la linea final no es la forma verde" % (ID, que),
                        not re.match(r"^\d+/\d+ pasaron\.$", (txt.splitlines() or [""])[-1]))
        t.verdadero("%s total nulo: no se traga la excepcion (nombra la suite y el campo)" % ID,
                    "b.py" in res["total_nulo"][1] and "total" in res["total_nulo"][1])
        t.verdadero("%s con INFRA el error no suma a ok (7/7 de las otras dos)" % ID,
                    (lineas_de_caso("infra") or [""])[-1] == "7/7 pasaron. 0 fallaron.")
        t.igual("%s ningun worker: no se escribio ningun evento" % ID, ev_antes, sorted(ly.eventos(ly.aislamiento("post")[0])))
        t.igual("%s ni se toco el arbol del layout" % ID, h0, huella(ly))
    except Exception as e:
        t.verdadero("%s el layout y el agregador: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly)


# VP-E14: el reporte comparable es el mismo para cualquier orden de terminacion y cualquier N.

def _orden_ps_del_sistema(ly):
    """El orden de Sort-Object Name sobre tests\\casos del layout: la sonda real, nunca un orden escrito a mano."""
    cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
           "Get-ChildItem '%s' -Filter '*.ps1' | Sort-Object Name | ForEach-Object { $_.Name }" % (ly.ly / "tests" / "casos")]
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=TOPE_S, creationflags=SIN_VENTANA)
    return [l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if l.strip()]


def test_vp_e14_el_reporte_comparable_es_identico_byte_a_byte_para_cualquier_orden_y_cualquier_n(t):
    """VP-E14 - con fixtures cuyas demoras invierten el orden de terminacion respecto del canonico, con a_b.py y ab.py
    entre ellas, y con N = 1, 2 y 4, el reporte comparable de las seis corridas es identico byte a byte, sale en el orden
    canonico (Sort-Object Name y sorted() de Python) y ninguna linea suya contiene un pid, la ruta del temporal, el id de
    corrida ni una hora."""
    ID = "VP-E14"
    # Demoras: la ultima del orden canonico termina primero cuando corren todas a la vez (N = 4).
    suites = [ps_suite("p_x.ps1", 2, dormir=1.2), ps_suite("px.ps1", 2, dormir=0.9),
              py_suite("a_b.py", 2, dormir=0.6), py_suite("ab.py", 2, dormir=0.3)]
    layouts = {"A": Layout(suites, con_runner=True), "B": Layout(suites, con_runner=True)}
    ejs = []
    try:
        for ly in layouts.values():
            ly.crear()
        ps_canon = _orden_ps_del_sistema(layouts["A"])
        py_canon = sorted(s["nombre"] for s in suites if s["motor"] == "py")
        py_canon = sorted(py_canon, key=lambda n: n.lower())
        canon = ps_canon + py_canon
        t.igual("%s la sonda ve los dos .ps1 y a_b antes que ab (el orden de sorted() de Python)" % ID,
                (2, ["a_b.py", "ab.py"]), (len(ps_canon), py_canon))
        # A: el primero del orden canonico recibe el maxSeconds mas chico (se lanza ultimo); B: el mas grande.
        for nombre, ly in layouts.items():
            valores = [10.0 * (len(canon) - i) for i in range(len(canon))]
            if nombre == "A":
                valores = list(reversed(valores))
            ly.reescribir_manifest(manifest_texto([ent(n, "parallel", maxs=v) for n, v in zip(canon, valores)]), confirmar=True)
        corridas = []
        for nombre, ly in layouts.items():
            for n in (1, 2, 4):
                clave = "%s%d" % (nombre.lower(), n)
                corridas.append((nombre, n, correr_runner(ly, ly.rutas(clave), n), clave))
        ejs = [c[2] for c in corridas]
        for c in corridas:
            c[2].esperar()
        regiones = {(c[0], c[1]): region(c[2].out) for c in corridas}
        t.verdadero("%s las seis corridas dieron exit 0 y tienen su reporte" % ID,
                    all(c[2].rc == 0 and regiones[(c[0], c[1])] is not None for c in corridas))
        base = regiones[("A", 1)]
        for (nombre, n), reg in sorted(regiones.items()):
            t.igual("%s la region comparable de %s con N=%d es identica a la de A con N=1" % (ID, nombre, n),
                    "", primera_diferencia(base or b"", reg or b""))
        # El orden de terminacion fue distinto del canonico (si no, el escenario no probaria nada).
        for nombre, n in (("A", 1), ("A", 4), ("B", 4)):
            ej = next(c[2] for c in corridas if c[0] == nombre and c[1] == n)
            fins = sorted(((v[1], k) for k, v in intervalos(ej.eventos).items()))
            orden_fin = [k for _t, k in fins]
            t.verdadero("%s control: con %s N=%d el orden de terminacion no coincide con el canonico" % (ID, nombre, n),
                        orden_fin != canon)
        # El orden canonico: PS segun la sonda, Python segun sorted().
        lineas = (base or b"").decode("utf-8", "replace").splitlines()
        t.igual("%s los grupos PS salen en el orden de la sonda" % ID,
                [n[:-len(".ps1")] for n in ps_canon], list(grupos_ps(lineas)))
        t.igual("%s los grupos Python salen en el orden de sorted()" % ID,
                [n[:-len(".py")] for n in py_canon], [g[1] for g in grupos_py(lineas)])
        # Pureza: nada del entorno de la corrida en el reporte comparable.
        texto = (base or b"").decode("utf-8", "replace")
        pids = set()
        for c in corridas:
            pids.add(c[2].proc.pid)
            for filas in c[2].eventos.values():
                pids.update(p for _tipo, p, _t in filas)
        t.vacio("%s sin ruta de temporal ni de TempBase" % ID,
                [p for p in {str(c[2].r["tb"]) for c in corridas} | {str(layouts['A'].tmp)} if p in texto])
        t.vacio("%s sin id de corrida (hpp-<8 hex>)" % ID, re.findall(r"hpp-[0-9a-f]{8}", texto))
        t.vacio("%s sin pids conocidos" % ID, [p for p in pids if p >= 1000 and re.search(r"\b%d\b" % p, texto)])
        t.vacio("%s sin horas ni fechas" % ID, re.findall(r"\d{2}:\d{2}|\d{4}-\d{2}-\d{2}", texto))
        t.vacio("%s sin duraciones" % ID, re.findall(r"\d+(?:\.\d+)? s\b", texto))
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        for ly in layouts.values():
            _borrar_layout(ly, *ejs)


# VP-E24 parte B: la validacion de forma del manifest, en el runner, con procesos reales.

def _parametros_del_runner(ly):
    """Los parametros que declara el runner (por AST, sin ejecutarlo), sin los comunes de CmdletBinding."""
    ev, tp = ly.aislamiento("ast")
    env = ly.entorno(ev, tp)
    env["T61_RUNNER"] = str(ly.runner)
    cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
           "$e = $null; $a = [System.Management.Automation.Language.Parser]::ParseFile($env:T61_RUNNER, [ref]$null, [ref]$e); "
           "$a.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath }"]
    r = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=TOPE_S, creationflags=SIN_VENTANA)
    return sorted(l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if l.strip())


def test_vp_e24_b_un_manifest_ilegible_o_de_forma_invalida_no_corre_nada_y_uno_valido_fuera_de_la_formula_corre(t):
    """VP-E24 parte B - con un manifest que no es JSON, o con una entrada de forma invalida (schema, class, timeoutSeconds que
    no es entero > 0, suite repetido), el runner sale 1 con MANIFEST_INVALIDO y no lanza ninguna suite (cero archivos de
    eventos, ni TempBase tocado ni candado tomado); con un timeoutSeconds entero > 0 fuera de la formula productiva, corre.
    Sin testMode ni parametro oculto: los parametros del runner son exactamente cinco."""
    ID = "VP-E24-B"
    suites = [ps_suite("ps_ok.ps1", 2), py_suite("py_ok.py", 2)]
    buenas = [ent("ps_ok.ps1"), ent("py_ok.py")]
    malos = (
        ("no es JSON", "esto no es json {{{"),
        ("schema distinto", manifest_texto(buenas, schema="parallel-manifest/2")),
        ("class desconocida", manifest_texto([ent("ps_ok.ps1", "heavy"), ent("py_ok.py")])),
        ("timeoutSeconds 3.5", manifest_texto([ent("ps_ok.ps1", to=3.5), ent("py_ok.py")])),
        ("timeoutSeconds 0", manifest_texto([ent("ps_ok.ps1", to=0), ent("py_ok.py")])),
        ("suite repetido", manifest_texto([ent("ps_ok.ps1"), ent("ps_ok.ps1")])),
    )
    ly = Layout(suites, con_runner=True)
    ejs = []
    try:
        ly.crear()
        for i, (que, texto) in enumerate(malos):
            ly.reescribir_manifest(texto)
            r = ly.rutas("m%d" % i)
            ej = correr_runner(ly, r, 2).esperar()
            ejs.append(ej)
            t.igual("%s %s: sale 1" % (ID, que), 1, ej.rc)
            t.verdadero("%s %s: la salida dice MANIFEST_INVALIDO y la causa" % (ID, que),
                        bool(re.search(r"^MANIFEST_INVALIDO \S", ej.texto, re.M)))
            t.igual("%s %s: ninguna suite se lanzo (cero archivos de eventos)" % (ID, que), [], sorted(ej.eventos))
            t.igual("%s %s: TempBase intacto y vacio" % (ID, que), [], tb_vacio(r))
            t.verdadero("%s %s: pesada.lock no se creo (el manifest se valida antes del candado)" % (ID, que),
                        not Path(r["lock"]).exists() and not Path(r["lock"]).parent.exists())
        # Positivo: un timeoutSeconds entero > 0 fuera de la formula del manifest real es valido para el runner.
        ly.reescribir_manifest(manifest_texto([ent("ps_ok.ps1", to=7), ent("py_ok.py", to=7)]), confirmar=True)
        r = ly.rutas("pos")
        ej = correr_runner(ly, r, 2).esperar()
        ejs.append(ej)
        t.igual("%s timeoutSeconds 7 (fuera de la formula): corre y sale 0" % ID, 0, ej.rc)
        t.igual("%s y lanzo las dos suites, una vez cada una" % ID, {"ps_ok.ps1.ev": 1, "py_ok.py.ev": 1}, ej.inicios())
        t.igual("%s y la linea final es verde (4/4)" % ID, "4/4 pasaron.", ej.ultima)
        t.verdadero("%s y esta vez si tomo el candado" % ID, Path(r["lock"]).is_file())
        # Sin testMode: los parametros son los cinco y ninguno mas.
        t.igual("%s los parametros del runner son exactamente los cinco" % ID,
                sorted(["CancelFile", "Detallado", "LockPath", "TempBase", "Workers"]), _parametros_del_runner(ly))
        t.no_contiene("%s el texto del runner no tiene ningun modo de prueba" % ID, "testmode",
                      ly.runner.read_text(encoding="utf-8-sig").lower())
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *ejs)


# ---- VP-E03, VP-E04, VP-E05, VP-E06, VP-E07 y VP-E09: lo que el runner lee, lo que ve cada suite -----------
#
# Etapa 4 (lote b) de la construccion (spec §29 paso 4): fallos de lectura, stderr, procesos muertos y aislamiento.
# Cada escenario afirma el motivo que corresponde Y niega el del vecino (INFRA contra fila roja, WORKER_MUERTO contra
# SIN_RESUMEN, 0/0 contra resumen ausente): una mutacion que los confunda tiene que ponerlo en rojo.

def test_vp_e03_un_archivo_que_no_carga_aporta_una_fila_roja_con_su_grupo_y_no_es_infra(t):
    """VP-E03 - un .ps1 con error de sintaxis y un .py con ImportError aportan cada uno exactamente una fila roja 'el
    archivo de casos se pudo cargar' con grupo = su nombre base o stem; ninguno sale INFRA ni suite ausente (VP-I05); un
    .ps1 que pisa $caso y $nombre antes de tirar da el grupo del archivo, no X ni Y (regla B6); exit 1."""
    ID = "VP-E03"
    CARGA = "el archivo de casos se pudo cargar"
    suites = [ps_suite("ps_sintaxis.ps1", 1, extra="if ("),
              py_suite("py_import_error.py", 0, no_carga=True),
              ps_suite("ps_ok.ps1", 3), py_suite("py_ok.py", 3),
              ps_suite("ps_pisa.ps1", 1, extra="$caso = 'X'\n$nombre = 'Y'\nthrow 'boom'")]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ly.crear()
        r = ly.rutas("e03")
        ej = correr_runner(ly, r, 4).esperar()
        final, rc_esperado = esperado_final(suites)
        lineas = lineas_del_reporte(ej)
        t.igual("%s el exit es 1" % ID, rc_esperado, ej.rc)
        t.igual("%s la ultima linea cuenta las tres filas rojas (6/9, de los parametros)" % ID, final, ej.ultima)
        i_fallos = lineas.index("Fallos:") if "Fallos:" in lineas else -1
        filas_ps = [l.rstrip() for l in lineas[i_fallos + 1:] if re.match(r"^  \[", l)] if i_fallos >= 0 else []
        t.igual("%s Fallos: tiene UNA fila de carga por cada .ps1 que no carga, con grupo = su BaseName" % ID,
                ["  [ps_pisa] " + CARGA, "  [ps_sintaxis] " + CARGA], filas_ps)
        t.igual("%s y ninguna con el grupo que pisaron (X, Y)" % ID, [],
                [l for l in lineas if l.startswith("  [X]") or l.startswith("  [Y]")])
        t.igual("%s el .py que no importa aporta UNA linea MAL, con grupo = su stem" % ID, 1,
                len([l for l in lineas if l.startswith("    MAL py_import_error / " + CARGA)]))
        t.igual("%s en total, tres filas de carga en el reporte, ni una mas" % ID, 3,
                len([l for l in lineas if CARGA in l]))
        t.contiene("%s la excepcion del caso que tiro queda visible" % ID, "boom", "\n".join(lineas))
        g = grupos_ps(lineas)
        t.igual("%s los grupos PS son los de los archivos: los dos rojos con 1/1 y ps_ok con 3" % ID,
                {"ps_ok": ("OK", "3"), "ps_pisa": ("FALLA", "1/1"), "ps_sintaxis": ("FALLA", "1/1")}, g)
        t.igual("%s el grupo Python es el stem de cada archivo, en orden" % ID,
                [("FALLA", "py_import_error", 1), ("OK", "py_ok", 3)], grupos_py(lineas))
        # El vecino: ninguna de las cuatro es un error de infraestructura ni una suite ausente.
        t.igual("%s ninguna linea INFRA en toda la salida" % ID, [], lineas_con(ej, r"^\s*INFRA "))
        t.no_contiene("%s ni suite ausente" % ID, "SUITE_AUSENTE", ej.texto)
        t.no_contiene("%s ni resumen ausente" % ID, "SIN_RESUMEN", ej.texto)
        t.igual("%s todas con reporte: FALLA en el progreso y no INFRA (ps_sintaxis, ps_pisa, py_import_error)" % ID,
                ["FALLA", "FALLA", "FALLA"],
                [estado_en_progreso(ej, n) for n in ("ps_sintaxis.ps1", "ps_pisa.ps1", "py_import_error.py")])
        t.igual("%s y las dos verdes, OK" % ID, ["OK", "OK"],
                [estado_en_progreso(ej, n) for n in ("ps_ok.ps1", "py_ok.py")])
        t.igual("%s un .ps1 con error de sintaxis no llega a su INICIO; las otras cuatro corrieron una vez" % ID,
                {"ps_ok.ps1.ev": 1, "ps_pisa.ps1.ev": 1, "py_import_error.py.ev": 1, "py_ok.py.ev": 1}, ej.inicios())
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e04_el_resumen_es_la_ultima_linea_y_un_proceso_que_miente_sale_rojo(t):
    """VP-E04 - (a) una suite Py cuya fila roja trae `3/4 pasaron.` en el detalle y cuyo grupo cuenta 10 sale INFRA
    RESUMEN_INCOHERENTE con los dos valores, nunca verde; (b) una suite Py que imprime `5/5 pasaron.` y termina con exit
    1 por un atexit, y otra que imprime `3/5 pasaron.` y termina con exit 0, salen rojas en el runner y el oraculo copiado
    da exit 1 sobre cada una; (c) un senuelo PS (`7/9 pasaron.` en el detalle de una fila roja) no cambia la cuenta: la
    del runner es la de la ultima linea del worker, no la del primer match."""
    ID = "VP-E04"
    sa = [py_decoy("py_decoy.py"), ps_decoy("ps_decoy.ps1")]
    sb = [py_liar_ok("py_liar_ok.py"), py_liar_fail("py_liar_fail.py"), ps_suite("ps_ok.ps1", 2)]
    la, lb = Layout(sa, con_runner=True), Layout(sb, con_runner=True)
    ejs = []
    try:
        la.crear()
        lb.crear()
        ea = correr_runner(la, la.rutas("e04a"), 2)
        eb = correr_runner(lb, lb.rutas("e04b"), 2)
        ejs += [ea, eb]
        oraculos = {n: Corrida(lb, "o_" + n[:-3], lb.oraculo, ["-SoloCaso", n]) for n in ("py_liar_ok.py", "py_liar_fail.py")}
        correr_en_lotes(list(oraculos.values()), 2)
        ea.esperar()
        eb.esperar()

        # (a) y (c): layout con el senuelo Py y el senuelo PS
        final_a, _rc = esperado_final([sa[1]])
        t.igual("%s (a) el runner sale 1" % ID, 1, ea.rc)
        incoh = lineas_con(ea, r"^INFRA RESUMEN_INCOHERENTE py_decoy\.py\b")
        t.igual("%s (a) INFRA RESUMEN_INCOHERENTE nombra la suite, una vez" % ID, 1, len(incoh))
        t.verdadero("%s (a) y trae los dos valores: el total que leyo el oraculo (4) y los 10 del grupo" % ID,
                    bool(incoh) and re.search(r"\b4\b", incoh[0]) is not None and re.search(r"\b10\b", incoh[0]) is not None)
        t.igual("%s (a) en el progreso sale INFRA, nunca OK" % ID, "INFRA", estado_en_progreso(ea, "py_decoy.py"))
        t.igual("%s (a) no es un resumen ausente ni un exit incoherente (el vecino)" % ID, [],
                lineas_con(ea, r"^\s*INFRA (SIN_RESUMEN|EXIT_INCOHERENTE|WORKER_MUERTO) "))
        t.igual("%s (a) el `3/4 pasaron` (con punto) del detalle no es la linea final ni una linea de resumen" % ID, [],
                [l for l in ea.lineas if re.match(r"^\s*3/4 pasaron\.", l)])
        t.igual("%s (a) un error de infraestructura no suma: la unica suite que cuenta es la PS (2/3, 1 fallaron.)" % ID,
                final_a, ea.ultima)
        t.igual("%s (a) las dos corrieron una vez" % ID, {"ps_decoy.ps1.ev": 1, "py_decoy.py.ev": 1}, ea.inicios())
        # (c) la suite PS cuyo detalle trae `7/9 pasaron.`
        t.igual("%s (c) la suite PS del senuelo sale FALLA por su fila roja, no INFRA" % ID, "FALLA",
                estado_en_progreso(ea, "ps_decoy.ps1"))
        t.igual("%s (c) y ninguna linea INFRA la nombra" % ID, [], lineas_con(ea, r"^\s*INFRA \w+ ps_decoy\.ps1"))
        t.igual("%s (c) la cuenta del runner es la del worker (2/3), no el 7/9 del primer match" % ID, "2/3 pasaron. 1 fallaron.",
                ea.ultima)
        t.contiene("%s (c) el detalle del senuelo si esta en Fallos: (la fila es real)" % ID, "7/9 pasaron.",
                   "\n".join(lineas_del_reporte(ea)))

        # (b) las dos suites que mienten: el oraculo copiado y el runner
        for nombre, fin_esperado in (("py_liar_ok.py", "5/5 pasaron. 0 fallaron."), ("py_liar_fail.py", "3/5 pasaron. 2 fallaron.")):
            o = oraculos[nombre]
            t.igual("%s (b) el oraculo copiado sobre %s da exit 1" % (ID, nombre), 1, o.rc)
            t.igual("%s (b) %s: la ultima linea del oraculo es la roja" % (ID, nombre), fin_esperado, o.ultima)
            mentira = "5/5 pasaron." if nombre == "py_liar_ok.py" else "3/5 pasaron."
            t.verdadero("%s (b) %s: de verdad imprimio %s (la fixture miente)" % (ID, nombre, mentira.rstrip(".")),
                        mentira in o.lineas)
        t.igual("%s (b) el runner sale 1" % ID, 1, eb.rc)
        t.verdadero("%s (b) y su linea final es roja (N fallaron.), nunca la forma verde" % ID,
                    re.match(r"^\d+/\d+ pasaron\. \d+ fallaron\.$", eb.ultima) is not None)
        for nombre in ("py_liar_ok.py", "py_liar_fail.py"):
            est = estado_en_progreso(eb, nombre)
            t.verdadero("%s (b) %s sale roja en el runner (observado: %s), nunca OK" % (ID, nombre, est),
                        est in ("FALLA", "INFRA"))
        t.igual("%s (b) la suite PS verde sigue OK" % ID, "OK", estado_en_progreso(eb, "ps_ok.ps1"))
        t.igual("%s (b) las tres corrieron una vez" % ID, {"ps_ok.ps1.ev": 1, "py_liar_fail.py.ev": 1, "py_liar_ok.py.ev": 1},
                eb.inicios())
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(la, *ejs)
        _borrar_layout(lb, *ejs)


def _inicio_de(ev, archivo):
    """El pid del primer INICIO del archivo de eventos de la suite (None si todavia no hay)."""
    p = Path(ev) / (archivo + ".ev")
    if not p.exists():
        return None
    for linea in p.read_text(encoding="ascii").splitlines():
        m = re.match(r"^INICIO pid=(\d+) t=\d+$", linea)
        if m:
            return int(m.group(1))
    return None


def test_vp_e05_un_worker_matado_desde_afuera_sale_worker_muerto_y_no_se_relanza(t):
    """VP-E05 - si un worker se mata con Stop-Process a mitad de su suite (el pid sale del arbol del runner por
    ParentProcessId), esa suite sale INFRA WORKER_MUERTO, no suma a ok, no se relanza (un solo inicio) y las demas se
    reportan con sus resultados; exit 1. WORKER_MUERTO y SIN_RESUMEN son motivos distintos: aca NO sale el segundo.
    Sonda dentro del mismo id: tambien el worker que ya escribio en stderr antes de morir (no es un resumen ausente)."""
    ID = "VP-E05"
    victimas = ("kill_me.ps1", "kill_err.ps1")
    suites = [ps_suite("kill_me.ps1", 1, dormir=25.0), ps_stderr("kill_err.ps1", dormir=25.0),
              ps_suite("ps_ok.ps1", 3), py_suite("py_ok.py", 3)]
    manifest = manifest_texto([ent("kill_me.ps1", maxs=50.0), ent("kill_err.ps1", maxs=40.0),
                               ent("ps_ok.ps1"), ent("py_ok.py")])
    ly = Layout(suites, con_runner=True, manifest=manifest)
    ej = None
    try:
        ly.crear()
        r = ly.rutas("e05")
        ej = correr_runner(ly, r, 4)     # las cuatro a la vez: las dos que viven se matan, las otras dos terminan
        iniciadas = esperar(lambda: all(_inicio_de(r["ev"], v) for v in victimas), 120)
        t.verdadero("%s precondicion: las dos suites a matar empezaron (si no, el escenario esta inconcluso)" % ID, iniciadas)
        if not iniciadas:
            return
        todos = procesos()
        workers = {}
        for v in victimas:
            hijos = [p for p in todos if p[1] == ej.proc.pid and v in p[3] and "-SoloCaso" in p[3]]
            t.igual("%s el worker de %s sale del arbol del runner (ParentProcessId == runner, -SoloCaso %s)" % (ID, v, v),
                    1, len(hijos))
            if hijos:
                workers[v] = hijos[0][0]
                t.igual("%s y es el mismo proceso que escribio el INICIO de la suite" % ID, _inicio_de(r["ev"], v), hijos[0][0])
        if len(workers) != len(victimas):
            return
        for v in victimas:
            t.igual("%s Stop-Process sobre el worker de %s termina bien" % (ID, v), 0, stop_process(workers[v]))
        ej.esperar()
        lineas = lineas_del_reporte(ej)
        t.igual("%s el runner sale 1" % ID, 1, ej.rc)
        for v in victimas:
            t.igual("%s INFRA WORKER_MUERTO %s, una sola linea" % (ID, v), ["INFRA WORKER_MUERTO " + v],
                    lineas_con(ej, r"^INFRA WORKER_MUERTO %s$" % re.escape(v)))
            t.igual("%s %s: en el progreso sale INFRA" % (ID, v), "INFRA", estado_en_progreso(ej, v))
        t.igual("%s no es un resumen ausente (el vecino): ninguna linea INFRA SIN_RESUMEN" % ID, [],
                lineas_con(ej, r"SIN_RESUMEN"))
        t.igual("%s el bloque dice cuantas suites tuvieron error de infraestructura (2)" % ID,
                ["2 suites con error de infraestructura."], lineas_con(ej, r"^\d+ suites con error de infraestructura\.$"))
        t.igual("%s las muertas no se relanzan: un INICIO y ningun FIN cada una" % ID,
                {v + ".ev": (1, 0) for v in victimas},
                {k: (sum(1 for e in ev if e[0] == "INICIO"), sum(1 for e in ev if e[0] == "FIN"))
                 for k, ev in ej.eventos.items() if k[:-len(".ev")] in victimas})
        t.igual("%s las otras dos corrieron una vez y salen OK" % ID, ["OK", "OK"],
                [estado_en_progreso(ej, n) for n in ("ps_ok.ps1", "py_ok.py")])
        t.igual("%s las muertas no suman a ok ni a total: solo cuentan las otras dos (6/6, forma roja, 0 fallaron.)" % ID,
                "6/6 pasaron. 0 fallaron.", ej.ultima)
        t.verdadero("%s y la linea final no es la verde" % ID, re.match(r"^\d+/\d+ pasaron\.$", ej.ultima) is None)
        t.igual("%s todas las suites enumeradas tienen archivo de eventos (ninguna desaparece del reporte)" % ID,
                sorted(s["nombre"] + ".ev" for s in suites), sorted(ej.eventos))
        t.verdadero("%s el grupo de ps_ok esta en el reporte, el de las muertas no" % ID,
                    "ps_ok" in grupos_ps(lineas) and "kill_me" not in grupos_ps(lineas) and "kill_err" not in grupos_ps(lineas))
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e06_un_resumen_ausente_es_infra_y_nunca_0_de_0_pero_0_de_0_real_es_verde(t):
    """VP-E06 - una suite Py que termina con os._exit(0) sin imprimir resumen, otra que imprime `12/` y corta, y otra con la
    salida vacia salen cada una INFRA SIN_RESUMEN (no WORKER_MUERTO: nadie las mato), nunca `0/0 pasaron.`; exit 1. Una
    suite Py sin ningun test_, que imprime `0/0 pasaron.` con exit 0, es verde, como en el oraculo."""
    ID = "VP-E06"
    nombres = ("py_sr_exit0.py", "py_sr_trunca.py", "py_sr_vacia.py")
    s1 = [py_sin_resumen(nombres[0], "exit0"), py_sin_resumen(nombres[1], "trunca"), py_sin_resumen(nombres[2], "vacia"),
          py_suite("py_ok.py", 3), ps_suite("ps_ok.ps1", 2)]
    s2 = [py_cero("py_cero.py"), ps_suite("ps_ok.ps1", 2)]
    l1, l2 = Layout(s1, con_runner=True), Layout(s2, con_runner=True)
    ejs = []
    try:
        l1.crear()
        l2.crear()
        e1 = correr_runner(l1, l1.rutas("e06a"), 4)
        e2 = correr_runner(l2, l2.rutas("e06b"), 2)
        ejs += [e1, e2]
        o_todo = Corrida(l2, "o_todo", l2.oraculo)
        o_cero = Corrida(l2, "o_cero", l2.oraculo, ["-SoloCaso", "py_cero.py"])
        correr_en_lotes([o_todo, o_cero], 2)
        e1.esperar()
        e2.esperar()

        t.igual("%s el runner sale 1" % ID, 1, e1.rc)
        for n in nombres:
            t.igual("%s INFRA SIN_RESUMEN %s, una sola linea" % (ID, n), ["INFRA SIN_RESUMEN " + n],
                    lineas_con(e1, r"^INFRA SIN_RESUMEN %s$" % re.escape(n)))
            t.igual("%s %s: en el progreso sale INFRA" % (ID, n), "INFRA", estado_en_progreso(e1, n))
        t.igual("%s nadie las mato: ninguna linea WORKER_MUERTO (el vecino)" % ID, [], lineas_con(e1, r"WORKER_MUERTO"))
        t.igual("%s tres suites con error de infraestructura" % ID, ["3 suites con error de infraestructura."],
                lineas_con(e1, r"^\d+ suites con error de infraestructura\.$"))
        t.igual("%s nunca `0/0 pasaron` (con punto): ninguna linea de toda la salida lo dice" % ID, [],
                [l for l in e1.lineas if l.strip() == "0/0 pasaron."])
        t.igual("%s lo que no es infraestructura cuenta y las infra no suman: 5/5, forma roja" % ID,
                "5/5 pasaron. 0 fallaron.", e1.ultima)
        t.igual("%s las otras dos suites OK" % ID, ["OK", "OK"], [estado_en_progreso(e1, n) for n in ("py_ok.py", "ps_ok.ps1")])
        t.igual("%s las cinco corrieron una vez" % ID, {s["nombre"] + ".ev": 1 for s in s1}, e1.inicios())

        # Una suite Py sin ningun test_: 0/0 pasaron. con exit 0, verde, como en el oraculo
        t.igual("%s py_cero: el runner sale 0" % ID, 0, e2.rc)
        t.igual("%s py_cero: sin ninguna linea INFRA" % ID, [], lineas_con(e2, r"^\s*INFRA "))
        t.igual("%s py_cero sale OK con su cero en el progreso" % ID, "OK", estado_en_progreso(e2, "py_cero.py"))
        t.verdadero("%s y es `(0)`: cero aserciones, no un error" % ID,
                    any(re.match(r"^\[\d+/2\] OK py_cero\.py \(0\) ", l) for l in e2.lineas))
        t.igual("%s la ultima linea del runner es verde (2/2)" % ID, "2/2 pasaron.", e2.ultima)
        t.igual("%s el oraculo copiado sobre el mismo layout: el mismo exit" % ID, o_todo.rc, e2.rc)
        t.igual("%s y la misma ultima linea" % ID, o_todo.ultima, e2.ultima)
        t.igual("%s el oraculo sobre py_cero sola da 0/0 pasaron (con punto) con exit 0" % ID, (0, "0/0 pasaron."), (o_cero.rc, o_cero.ultima))
        t.verdadero("%s el reporte del runner trae el bloque Python con 0/0 pasaron (con punto), como el oraculo" % ID,
                    "0/0 pasaron." in lineas_del_reporte(e2))
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(l1, *ejs)
        _borrar_layout(l2, *ejs)


def test_vp_e07_el_stderr_de_una_suite_py_la_pone_roja_y_el_de_una_ps_decide_como_el_oraculo(t):
    """VP-E07 - una suite Py verde que escribe una linea en stderr sale roja en el runner con ese texto visible en su
    bloque, y el oraculo copiado sobre el mismo layout sale 1; una suite PS verde que lanza `cmd /c "echo x 1>&2"` da en el
    runner el mismo resultado (verde o rojo) que en el oraculo copiado (VP-I06). Dos layouts: con un .py con stderr el
    oraculo muere antes de dar el resultado PS, no se pueden mezclar."""
    ID = "VP-E07"
    MARCA = "T61-STDERR-MARCA"
    l1 = Layout([py_stderr("py_stderr.py", MARCA), py_suite("py_ok.py", 2), ps_suite("ps_ok.ps1", 2)], con_runner=True)
    l2 = Layout([ps_stderr("ps_stderr.ps1"), ps_suite("ps_ok.ps1", 2)], con_runner=True)
    ejs = []
    try:
        l1.crear()
        l2.crear()
        e1 = correr_runner(l1, l1.rutas("e07a"), 2)
        e2 = correr_runner(l2, l2.rutas("e07b"), 2)
        ejs += [e1, e2]
        o1 = Corrida(l1, "o1", l1.oraculo)
        o2 = Corrida(l2, "o2", l2.oraculo)
        correr_en_lotes([o1, o2], 2)
        e1.esperar()
        e2.esperar()

        # Py con stderr
        t.igual("%s el oraculo copiado sobre el layout con stderr de Python sale 1" % ID, 1, o1.rc)
        t.verdadero("%s y su ultima linea no es la verde" % ID, re.match(r"^\d+/\d+ pasaron\.$", o1.ultima) is None)
        t.igual("%s el runner sale 1" % ID, 1, e1.rc)
        t.verdadero("%s y su linea final no es la verde" % ID, re.match(r"^\d+/\d+ pasaron\.$", e1.ultima) is None)
        est = estado_en_progreso(e1, "py_stderr.py")
        t.verdadero("%s la suite sale roja (observado: %s), nunca OK" % (ID, est), est in ("FALLA", "INFRA"))
        t.igual("%s lo que hizo el oraculo dentro del worker: corta, sin linea final (F6: SIN_RESUMEN)" % ID,
                ["INFRA SIN_RESUMEN py_stderr.py"], lineas_con(e1, r"^INFRA SIN_RESUMEN py_stderr\.py$"))
        bloque = bloque_de_progreso(e1, "py_stderr.py")
        t.verdadero("%s el texto de stderr esta visible en el bloque de la suite" % ID, any(MARCA in l for l in bloque))
        t.verdadero("%s y el bloque dice que es del worker" % ID, any("stderr del worker:" in l for l in bloque))
        t.verdadero("%s y esta en los logs conservados de la corrida (<raiz>\\logs\\*.err)" % ID,
                    any(MARCA in p.read_text(encoding="utf-8", errors="replace")
                        for p in Path(e1.r["tb"]).glob("hpp-*/logs/*.err")))
        t.igual("%s las otras dos suites siguen OK: el stderr de una no tumba a las demas" % ID, ["OK", "OK"],
                [estado_en_progreso(e1, n) for n in ("py_ok.py", "ps_ok.ps1")])
        t.igual("%s cada suite corrio una vez" % ID, {"ps_ok.ps1.ev": 1, "py_ok.py.ev": 1, "py_stderr.py.ev": 1}, e1.inicios())

        # PS con stderr nativo
        t.igual("%s PS: el runner da el mismo exit que el oraculo copiado" % ID, o2.rc, e2.rc)
        t.igual("%s PS: y la misma ultima linea" % ID, o2.ultima, e2.ultima)
        est2 = estado_en_progreso(e2, "ps_stderr.ps1")
        t.verdadero("%s PS: la suite sale como el oraculo la lee (observado: oraculo %s, runner %s)"
                    % (ID, "verde" if o2.rc == 0 else "rojo", est2), (est2 == "OK") == (o2.rc == 0))
        bloque2 = bloque_de_progreso(e2, "ps_stderr.ps1")
        t.verdadero("%s PS: el stderr del worker se muestra en el bloque de la suite" % ID,
                    any("stderr del worker:" in l for l in bloque2))
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(l1, *ejs)
        _borrar_layout(l2, *ejs)


def test_vp_e09_cada_suite_tiene_su_temporal_y_el_resto_del_entorno_es_el_del_runner(t):
    """VP-E09 - cuatro suites que corren a la vez (N = 4) vuelcan TEMP, TMP, TMPDIR, tempfile.gettempdir() y
    [IO.Path]::GetTempPath(): los cinco valores son el mismo directorio dentro de cada suite, distintos entre suites y
    respecto de una segunda corrida, vacios al empezar, fuera de la raiz; una marca .avisado que escribe una suite no la ve
    otra. Otra suite vuelca el entorno entero (ordenado, sin esas tres variables), el cwd, sys.executable, PATH y
    shutil.which('bash'), y da los mismos valores que el runner le paso, sin PYTHONHASHSEED, PYTHONPYCACHEPREFIX ni
    PYTHONDONTWRITEBYTECODE agregados (el helper los quita del entorno del runner: su aparicion seria inyeccion)."""
    ID = "VP-E09"
    temps = ["tmp_a.ps1", "tmp_b.py", "tmp_c.ps1", "tmp_d.py"]
    suites = [ps_temp("tmp_a.ps1"), py_temp("tmp_b.py"), ps_temp("tmp_c.ps1"), py_temp("tmp_d.py"), py_env("py_env.py")]
    manifest = manifest_texto([ent(n, maxs=30.0) for n in temps] + [ent("py_env.py")])
    ly = Layout(suites, con_runner=True, manifest=manifest)
    ejs = []
    try:
        ly.crear()
        senuelo = ly.tmp / "sen"            # una carpeta vacia al frente del PATH: si el runner lo reordena, se nota
        senuelo.mkdir()
        path = str(senuelo) + os.pathsep + os.environ.get("PATH", "")
        extra = {"PATH": path, "CLAUDE_T61": "1", "T61_PY": sys.executable, "T61_BARRERA": "4"}
        r1 = ly.rutas("e09a")
        e1 = correr_runner(ly, r1, 4, env_extra=extra)
        ejs.append(e1)
        e1.esperar()
        t.igual("%s la primera corrida sale 0, verde (5/5)" % ID, (0, "5/5 pasaron."), (e1.rc, e1.ultima))
        t.igual("%s verde y limpia: TempBase vacio" % ID, [], tb_vacio(r1))
        ints = intervalos(e1.eventos)
        completos = all(ints.get(n, (None, None))[0] is not None and ints[n][1] is not None for n in temps)
        t.verdadero("%s control: las cuatro suites de temporal tienen su intervalo completo" % ID, completos)
        if not completos:
            return
        t.verdadero("%s las cuatro estuvieron vivas a la vez (hay un instante comun a los cuatro intervalos)" % ID,
                    max(ints[n][0] for n in temps) < min(ints[n][1] for n in temps))
        t.igual("%s nunca mas de cuatro vivas a la vez" % ID, True, max_solapadas(ints) <= 4)

        d1 = {n: leer_volcado(r1["ev"], n) for n in temps}
        raiz_ly, base1 = canon(ly.ly), canon(r1["tb"])
        for n in temps:
            d = d1[n]
            valores = [d["TEMP"], d["TMP"], d["TMPDIR"], d["net"], d["py"]]
            t.igual("%s %s: TEMP, TMP, TMPDIR, GetTempPath() y gettempdir() son el mismo directorio" % (ID, n),
                    1, len({canon(v) for v in valores}))
            c = canon(d["TEMP"])
            t.verdadero("%s %s: su forma es <TempBase>\\hpp-<id>\\s<nnn> (%s)" % (ID, n, d["TEMP"]),
                        c.startswith(base1 + "\\")
                        and re.fullmatch(r"hpp-[0-9a-f]{8}\\s\d{3}", c[len(base1) + 1:]) is not None)
            t.verdadero("%s %s: esta fuera de la raiz del arbol" % (ID, n), not (c == raiz_ly or c.startswith(raiz_ly + "\\")))
            t.igual("%s %s: estaba vacio al empezar" % (ID, n), [], d["inicial"])
            t.igual("%s %s: vio solo su propia marca .avisado" % (ID, n), [n + ".avisado"], d["avisados"])
            t.verdadero("%s %s: la barrera se cumplio (>= 4 marcas de suites vivas)" % (ID, n), d["marcas"] >= 4)
        t.igual("%s los cuatro temporales son distintos entre si" % ID, 4, len({canon(d1[n]["TEMP"]) for n in temps}))
        t.igual("%s y viven en cuatro raices s<nnn> de la misma corrida (una sola hpp-<id>)" % ID, 1,
                len({canon(d1[n]["TEMP"]).rsplit("\\", 1)[0] for n in temps}))

        # el entorno entero, el cwd, el interprete, el PATH, bash
        env = leer_volcado(r1["ev"], "py_env.py")
        pasado = {k.upper(): v for k, v in e1.env.items() if k.upper() not in ("TEMP", "TMP", "TMPDIR") and not k.startswith("=")}
        visto = {k.upper(): v for k, v in env["env"].items()}
        # Calibracion (C-3): la unica variable que el entorno de la suite gana por su cuenta es la que fija el propio
        # `powershell -ExecutionPolicy Bypass` del runner y del worker (con o sin ella en el entorno de quien lanza).
        esperado = dict(pasado, PSEXECUTIONPOLICYPREFERENCE="Bypass")
        difiere = {k: (esperado.get(k), visto.get(k)) for k in set(esperado) | set(visto) if esperado.get(k) != visto.get(k)}
        t.igual("%s el entorno que ve la suite es el que se le paso al runner, menos TEMP/TMP/TMPDIR (no difiere nada mas)" % ID,
                {}, difiere)
        t.igual("%s PATH identico, con la carpeta senuelo primera (el runner no lo reordena)" % ID, path, env["path"])
        t.igual("%s la primera entrada del PATH sigue siendo el senuelo" % ID, str(senuelo), env["path"].split(os.pathsep)[0])
        t.igual("%s ninguna de las tres variables de PYTHON fue agregada" % ID, [],
                [k for k in env["env"] if k.upper() in VARIABLES_QUE_SE_QUITAN])
        t.igual("%s CLAUDE_T61 llega tal cual" % ID, "1", env["env"].get("CLAUDE_T61"))
        t.igual("%s el cwd es la raiz del layout" % ID, canon(ly.ly), canon(env["cwd"]))
        t.igual("%s sys.executable es el que resuelve el oraculo con ese PATH" % ID,
                canon(interprete_del_oraculo(e1.env) or ""), canon(env["exe"]))
        t.igual("%s shutil.which('bash') es el que da ese PATH" % ID, shutil.which("bash", path=path), env["bash"])
        t.verdadero("%s y bash existe (Git Bash al frente es del entorno, no del runner)" % ID, bool(env["bash"]))

        # una segunda corrida con el mismo TempBase: los temporales son otros
        r2 = ly.rutas("e09b")
        r2["tb"], r2["lock"] = r1["tb"], r1["lock"]
        e2 = correr_runner(ly, r2, 4, env_extra=dict(extra, T61_BARRERA="1"))
        ejs.append(e2)
        e2.esperar()
        t.igual("%s la segunda corrida sale 0, verde" % ID, (0, "5/5 pasaron."), (e2.rc, e2.ultima))
        d2 = {n: leer_volcado(r2["ev"], n) for n in temps}
        for n in temps:
            t.verdadero("%s %s: su temporal de la segunda corrida es otro" % (ID, n),
                        canon(d1[n]["TEMP"]) != canon(d2[n]["TEMP"]))
            t.igual("%s %s: y estaba vacio al empezar tambien en la segunda" % (ID, n), [], d2[n]["inicial"])
        t.igual("%s ningun temporal de la segunda corrida repite uno de la primera" % ID, set(),
                {canon(d1[n]["TEMP"]) for n in temps} & {canon(d2[n]["TEMP"]) for n in temps})
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *ejs)


# ---- Etapa 5 (spec §29 paso 5): timeout, huella, cancelacion y limpieza --------------------------
#
# VP-E08, VP-E10, VP-E19, VP-E20 y VP-E21. Reglas de este tramo:
#  - Todo proceso que lance una fixture (hijo, nieto, retenedor) lleva en su argv un token que contiene el
#    nombre del <tmp> del layout (t61_<random>): asi un barrido por token alcanza a todo lo del test y
#    SOLO a lo del test. Nunca se mata por nombre de imagen: el testigo (misma imagen, otro token) lo prueba.
#  - Cada escenario afirma el motivo y niega el vecino (TIMEOUT contra WORKER_MUERTO/SIN_RESUMEN, etc.).
#  - "En menos de N s" se mide desde un evento observado y nunca pasa vacio: si el hijo no llego a nacer
#    antes del corte el test FALLA como inconcluso, con el motivo.

_PY_HIJO = """
import subprocess
import sys

# Un hijo vivo con su padre vivo: la suite sigue viva y el hijo cuelga de ella (alcanzable por taskkill /T).
_hijo = subprocess.Popen([os.environ.get("T61_PY") or sys.executable, "-c", "import time; time.sleep(@@VIDA@@)",
                          "T61H-" + os.environ["T61_TOK"] + "-@@SUITE@@"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
with open(os.path.join(os.environ["T61_EV"], "@@SUITE@@.ev"), "a", encoding="ascii") as _f:
    _f.write("HIJO pid=%d t=%d\\n" % (_hijo.pid, int(time.time() * 1000)))
"""

# El proceso que retiene un archivo del temporal de la suite: lo abre, lo mantiene abierto y duerme.
_R_CODE = """import os
import time
f = open(os.path.join(os.environ["TEMP"], "retenido.bin"), "wb")
f.write(b"x")
f.flush()
time.sleep(@@VIDA@@)
"""

_PY_RETIENE = """
import subprocess
import sys

_r = subprocess.Popen([os.environ.get("T61_PY") or sys.executable, "-c", @@R@@,
                       "T61H-" + os.environ["T61_TOK"] + "-@@SUITE@@"],
                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
_ruta = os.path.join(os.environ["TEMP"], "retenido.bin")
_desde = time.time()
while not os.path.exists(_ruta) and time.time() - _desde < 30:
    time.sleep(0.05)
with open(os.path.join(os.environ["T61_EV"], "@@SUITE@@.ev"), "a", encoding="ascii") as _f:
    _f.write("HIJO pid=%d t=%d\\n" % (_r.pid, int(time.time() * 1000)))
"""

# VP-E20: la suite lanza A, A lanza B (que retiene el archivo) y A termina con os._exit: B queda huerfano, con el
# padre muerto. La suite sigue viva (duerme) hasta que el runner la corta por timeout.
_A_CODE = """import os
import subprocess
import sys
import time
tok = "T61H-" + os.environ["T61_TOK"] + "-@@SUITE@@"
b = subprocess.Popen([os.environ.get("T61_PY") or sys.executable, "-c", @@B@@, tok],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ruta = os.path.join(os.environ["TEMP"], "retenido.bin")
desde = time.time()
while not os.path.exists(ruta) and time.time() - desde < 30:
    time.sleep(0.05)
with open(os.path.join(os.environ["T61_EV"], "@@SUITE@@.ev"), "a", encoding="ascii") as f:
    f.write("HIJO pid=%d t=%d\\n" % (b.pid, int(time.time() * 1000)))
os._exit(0)
"""

_PY_HUERFANO = """
import subprocess
import sys

_a = subprocess.Popen([os.environ.get("T61_PY") or sys.executable, "-c", @@A@@,
                       "T61H-" + os.environ["T61_TOK"] + "-A"],
                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
_a.wait(timeout=60)
"""

_PY_ENSUCIA = """
# Ensucia el arbol del layout a proposito y no lo limpia: <ly>\\ensucia_t61.txt (la raiz sale de la ruta de este archivo).
_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
open(os.path.join(_raiz, "ensucia_t61.txt"), "w").close()
"""

_PS_TENEDOR = """param([string] $Ruta)
$fs = [System.IO.File]::Open($Ruta, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
$fs.Lock(0, 1)
[Console]::Out.WriteLine('LOCKED')
[Console]::Out.Flush()
Start-Sleep -Seconds 300
"""


def py_hijo(nombre, dur, vida):
    """Una suite Py que lanza un hijo vivo (duerme `vida` s, token en su argv) y sostiene `dur` s con su padre vivo."""
    antes = _PY_HIJO.replace("@@SUITE@@", nombre).replace("@@VIDA@@", str(int(vida)))
    cuerpo = "    time.sleep(%r)\n    t.verdadero(\"fila-01\", True)\n    _ev(\"FIN\")\n" % float(dur)
    return _suite_py(nombre, cuerpo, 1, antes=antes)


_PS_HIJO = """
$t61Psi = New-Object System.Diagnostics.ProcessStartInfo
$t61Psi.FileName = $env:T61_PY
$t61Psi.Arguments = '-c "import time; time.sleep(@@VIDA@@)" T61H-' + $env:T61_TOK + '-@@SUITE@@'
$t61Psi.UseShellExecute = $false
$t61Psi.CreateNoWindow = $true
$t61Hijo = [System.Diagnostics.Process]::Start($t61Psi)
[System.IO.File]::AppendAllText((Join-Path $env:T61_EV '@@SUITE@@.ev'), ('HIJO pid=' + $t61Hijo.Id + ' t=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + "`n"))
Set-Grupo '@@GRUPO@@'
Start-Sleep -Milliseconds @@MS@@
Assert-Verdadero 'fila-01' $true
Write-T61Ev 'FIN'
"""


def ps_hijo(nombre, dur, vida):
    """Una suite PS que lanza, al empezar, un hijo vivo (duerme `vida` s, token en su argv) y sostiene `dur` s con su padre (el
    worker, que corre la suite en proceso) vivo. Un .ps1 corre antes que un .py: no pasa por el arranque de Python."""
    grupo = nombre[:-len(".ps1")]
    texto = (_PS_EVENTOS.replace("@@SUITE@@", nombre) + "Write-T61Ev 'INICIO'\n"
             + _PS_HIJO.replace("@@SUITE@@", nombre).replace("@@VIDA@@", str(int(vida))).replace("@@GRUPO@@", grupo)
             .replace("@@MS@@", str(int(dur * 1000))))
    return {"nombre": nombre, "texto": texto, "motor": "ps", "filas": 1, "rojas": 0, "grupo": grupo}


def py_retiene(nombre):
    """VP-E21(a): una suite verde cuyo proceso R retiene retenido.bin del temporal de la suite y sobrevive a la suite."""
    antes = _PY_RETIENE.replace("@@SUITE@@", nombre).replace("@@R@@", repr(_R_CODE.replace("@@VIDA@@", "90")))
    cuerpo = "    t.verdadero(\"fila-01\", True)\n    _ev(\"FIN\")\n"
    return _suite_py(nombre, cuerpo, 1, antes=antes)


def py_huerfano(nombre):
    """VP-E20: suite -> A -> B; A muere con os._exit (B huerfano, retiene retenido.bin); la suite duerme hasta el corte."""
    codigo_a = _A_CODE.replace("@@SUITE@@", nombre).replace("@@B@@", repr(_R_CODE.replace("@@VIDA@@", "120")))
    antes = _PY_HUERFANO.replace("@@A@@", repr(codigo_a))
    cuerpo = "    time.sleep(60.0)\n    t.verdadero(\"fila-01\", True)\n    _ev(\"FIN\")\n"
    return _suite_py(nombre, cuerpo, 1, antes=antes)


def py_ensucia(nombre):
    """VP-E10: una suite verde que crea un archivo no ignorado en la raiz del layout durante la corrida."""
    return _suite_py(nombre, "    t.verdadero(\"fila-01\", True)\n    _ev(\"FIN\")\n", 1, antes=_PY_ENSUCIA)


def token_de(ly):
    """El token del layout: el nombre de su <tmp>. Esta en la linea de comandos del runner, de cada worker, de cada
    correr.py, y (por T61_TOK) en el argv de todo hijo que lanza una fixture."""
    return ly.tmp.name


def entorno_de_hijos(ly):
    """Lo que las fixtures de hijos leen: su token y el interprete del test (la MISMA imagen que el testigo)."""
    return {"T61_TOK": token_de(ly), "T61_PY": sys.executable}


def _evento_pid(ev, archivo, tipo):
    """El pid del primer evento `tipo` del archivo de eventos de la suite (None si todavia no hay)."""
    p = Path(ev) / (archivo + ".ev")
    if not p.exists():
        return None
    for linea in p.read_text(encoding="ascii").splitlines():
        m = re.match(r"^%s pid=(\d+) t=\d+$" % tipo, linea)
        if m:
            return int(m.group(1))
    return None


def matar_con(*tokens, tope=20):
    """Barrido por token de ESTE test (nunca por imagen): mata todo proceso cuya linea de comandos contiene alguno de los
    tokens (nombres de <tmp> t61_*) y espera a que no quede ninguno. Devuelve lo que sigue vivo al vencer `tope`."""
    tokens = [k for k in tokens if k and k.startswith("t61_") and len(k) >= 9]
    if not tokens:
        return []
    fin = time.time() + tope
    while True:
        restos = [p for p in procesos() if p[0] != os.getpid() and any(k in p[3] for k in tokens)]
        if not restos or time.time() >= fin:
            return restos
        for p in restos:
            subprocess.run(["taskkill", "/PID", str(p[0]), "/F"], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SIN_VENTANA)
        time.sleep(0.3)


def lanzar_testigo(ly):
    """Un proceso AJENO al runner con la misma imagen que los hijos de las fixtures (sys.executable) y otro token: si el
    runner matara por nombre de imagen, este moriria. Lo lanza el test, fuera de todo runner."""
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)", "T61W-" + token_de(ly)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=SIN_VENTANA)


def testigo_vivo(testigo):
    if testigo.poll() is not None:
        return False
    return any(p[0] == testigo.pid and "T61W-" in p[3] for p in procesos())


def soltar(proc):
    """Mata un Popen que lanzo este test (por su handle) y lo espera."""
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=30)
    except Exception:
        pass


def candado_estado(ruta):
    """libre | ocupado | no existe, con el mismo mecanismo del SO que el runner (un candado de rango de bytes sobre el
    byte 0): se intenta tomar sin esperar y se suelta. Es una sonda de un test, no es el runner."""
    import msvcrt
    try:
        fd = os.open(str(ruta), os.O_RDWR)
    except FileNotFoundError:
        return "no existe"
    except OSError:
        return "ilegible"
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return "ocupado"
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return "libre"
    finally:
        os.close(fd)


def lanzar_tenedor(ly, ruta):
    """Un proceso vivo que tiene tomado el candado del SO sobre `ruta` (FileStream.Lock(0, 1)). Devuelve (Popen, trozos);
    el script vive en el <tmp> del layout, asi su linea de comandos lleva el token."""
    script = ly.tmp / "ten.ps1"
    script.write_bytes(_PS_TENEDOR.encode("ascii"))
    proc = subprocess.Popen([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                             "-File", str(script), str(ruta)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, creationflags=SIN_VENTANA)
    trozos = []
    threading.Thread(target=_lector, args=(proc.stdout, trozos), daemon=True).start()
    return proc, trozos


def archivos_de_log_bajo(ly):
    """Los .out/.err/.log bajo la raiz del layout (sin .git): los logs del runner viven FUERA."""
    res = []
    for d, subs, files in os.walk(str(ly.ly)):
        subs[:] = [s for s in subs if s != ".git"]
        res += [os.path.join(d, f) for f in files if f.endswith((".out", ".err", ".log"))]
    return res


def ts_de_inicio(ev):
    """{archivo de eventos: ms del primer INICIO}"""
    return {k: next((e[2] for e in v if e[0] == "INICIO"), None) for k, v in Layout.eventos(ev).items()}


# ---- Etapa 6: helpers del candado (VP-E22) -------------------------------------------------------------------

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_EPOCA_FILETIME_MS = 11644473600000          # ms entre 1601-01-01 (FILETIME) y 1970-01-01 (time.time)


def _k32():
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                  ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
    k.GetProcessTimes.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    return k, ctypes, wintypes


def abrir_proceso(pid):
    """Un handle de consulta sobre un proceso VIVO: mientras este abierto el pid no se reusa y, cuando el proceso muere, el SO
    sigue dando su hora de salida (GetProcessTimes). None si no se pudo abrir."""
    k, _c, _w = _k32()
    h = k.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    return h or None


def hora_de_salida_ms(handle):
    """La hora de salida (ms de epoca Unix) del proceso detras del handle; None si todavia vive o no se pudo leer."""
    k, ctypes, wintypes = _k32()
    creacion, salida, nucleo, usuario = (wintypes.FILETIME() for _ in range(4))
    if not k.GetProcessTimes(handle, ctypes.byref(creacion), ctypes.byref(salida), ctypes.byref(nucleo), ctypes.byref(usuario)):
        return None
    ticks = (salida.dwHighDateTime << 32) | salida.dwLowDateTime
    if ticks == 0:
        return None
    return ticks // 10000 - _EPOCA_FILETIME_MS


def cerrar_handle(handle):
    if handle:
        try:
            _k32()[0].CloseHandle(handle)
        except Exception:
            pass


class MuestreoDeCandado:
    """Un hilo que mira `candado_estado(ruta)` cada ~10 ms y guarda lo que vio: el primer estado, el ultimo `ocupado` y la
    primera vez que dio `libre` (con la hora en ms de epoca Unix tomada DESPUES de la sonda). No es el runner: es la forma de
    observar el orden «el candado se suelta despues del ultimo worker», que con un segundo runner es una ventana de ms."""

    def __init__(self, ruta, paso=0.01):
        self.ruta, self.paso = ruta, paso
        self.primera = None
        self.ultima_ocupado_ms = None
        self.primera_libre_ms = None
        self.n = 0
        self.error = ""
        self._parar = threading.Event()
        self._hilo = threading.Thread(target=self._correr, daemon=True)

    def _correr(self):
        while not self._parar.is_set():
            try:
                estado = candado_estado(self.ruta)
            except Exception as e:                      # una sonda que explota se dice, no se traga
                self.error = "%s: %s" % (type(e).__name__, e)
                return
            ms = int(time.time() * 1000)
            self.n += 1
            if self.primera is None:
                self.primera = estado
            if estado == "ocupado":
                self.ultima_ocupado_ms = ms
            elif estado == "libre" and self.primera_libre_ms is None:
                self.primera_libre_ms = ms
            time.sleep(self.paso)

    def empezar(self):
        self._hilo.start()
        return self

    def parar(self):
        self._parar.set()
        if self._hilo.is_alive():
            self._hilo.join(timeout=10)


# ---- La corrida cancelada: una sola observacion que leen VP-E10 y VP-E19 ---------------------------
#
# E10 pide la huella despues de una corrida cancelada y E19 pide todo lo demas de esa misma cancelacion: se hace una
# vez, se guarda lo observado (datos, no el layout: se destruye al terminar) y los dos tests lo leen. VP-E22(d) lee de la misma
# observacion el orden de los eventos: la hora de salida de cada worker y cuando el candado dejo de estar ocupado.

_MEMO_CANCELADA = {}


def corrida_cancelada():
    """Dos suites vivas con hijos marcados con el token (N = 2), tres suites sin lanzar, y un -CancelFile creado a mano."""
    if "obs" in _MEMO_CANCELADA:
        return _MEMO_CANCELADA["obs"]
    obs = {"error": ""}
    suites = [py_hijo("can_1.py", 60, 120), py_hijo("can_2.py", 60, 120), ps_suite("ps_pen.ps1", 1),
              py_suite("pen_1.py", 1), py_suite("pen_2.py", 1)]
    manifest = manifest_texto([ent("can_1.py", maxs=100.0), ent("can_2.py", maxs=100.0), ent("ps_pen.ps1"),
                               ent("pen_1.py"), ent("pen_2.py")])
    ly = Layout(suites, con_runner=True, manifest=manifest)
    ej = None
    muestreo, handles = None, {}
    try:
        ly.crear()
        tok = token_de(ly)
        obs["h0"] = huella(ly)
        r = ly.rutas("e19")
        ej = correr_runner(ly, r, 2, extra=("-CancelFile", r["cancel"]), env_extra=entorno_de_hijos(ly))
        nacieron = esperar(lambda: all(_evento_pid(r["ev"], n, "HIJO") for n in ("can_1.py", "can_2.py")), 120)
        if not nacieron:
            obs["error"] = "precondicion: los dos hijos no llegaron a nacer en 120 s (inconcluso); salida: %r" % ej.texto[-400:]
            return obs
        obs["candado_control"] = candado_estado(r["lock"])      # con el runner vivo tiene que dar ocupado
        # control: antes de cancelar hay procesos con el token (los dos hijos entre ellos); si no, "ninguno vivo" no diria nada
        vivos = [p for p in procesos() if tok in p[3]]
        obs["vivos_antes"] = [p[3] for p in vivos]
        # VP-E22(d): los workers (hijos directos del runner que corren Invoke-Tests.ps1 -SoloCaso) con un handle abierto ANTES de
        # cancelar (su hora de salida se lee despues), y el candado muestreado desde antes hasta que el runner termina.
        obs["workers"] = sorted(p[0] for p in vivos if p[1] == ej.proc.pid and "-SoloCaso" in p[3])
        handles = {pid: abrir_proceso(pid) for pid in obs["workers"]}
        muestreo = MuestreoDeCandado(r["lock"]).empezar()
        esperar(lambda: muestreo.primera is not None, 10)
        r["cancel"].parent.mkdir(parents=True)
        r["cancel"].write_bytes(b"x")
        t_cancel = time.time()
        obs["t_cancel_ms"] = int(t_cancel * 1000)
        ej.esperar(90)
        muestreo.parar()
        obs["exit_ms"] = {pid: (hora_de_salida_ms(h) if h else None) for pid, h in handles.items()}
        obs["muestreo"] = {"primera": muestreo.primera, "ultima_ocupado_ms": muestreo.ultima_ocupado_ms,
                           "primera_libre_ms": muestreo.primera_libre_ms, "n": muestreo.n, "error": muestreo.error}
        obs["rc"], obs["texto"], obs["lineas"] = ej.rc, ej.texto, ej.lineas
        obs["segundos_hasta_salir"] = ej.t1 - t_cancel
        obs["eventos"] = ej.eventos
        restos = []
        while True:
            restos = [p for p in procesos() if tok in p[3]]
            if not restos or time.time() - t_cancel > 30:
                break
            time.sleep(0.5)
        obs["t_sin_procesos"] = time.time() - t_cancel
        obs["restos"] = [(p[0], p[3][:160]) for p in restos]
        obs["lock_pesada"] = candado_estado(r["lock"])
        obs["tb"] = tb_vacio(r)
        obs["lock_raiz"] = {n: candado_estado(Path(r["tb"]) / n) for n in obs["tb"] if n.endswith(".lock")}
        obs["dirs_s"] = [str(p) for p in Path(r["tb"]).glob("hpp-*/s[0-9][0-9][0-9]")]
        obs["logs"] = sorted(p.name for p in Path(r["tb"]).glob("hpp-*/logs/*"))
        obs["logs_en_ly"] = archivos_de_log_bajo(ly)
        obs["h1"] = huella(ly)
        obs["estado"] = ly.estado()
        obs["tb_ruta"] = str(r["tb"])
    except Exception as e:
        obs["error"] = "%s: %s" % (type(e).__name__, str(e)[:300])
    finally:
        if muestreo is not None:
            muestreo.parar()
        for h in handles.values():
            cerrar_handle(h)
        matar_con(token_de(ly))
        _borrar_layout(ly, *([ej] if ej else []))
        _MEMO_CANCELADA["obs"] = obs        # tambien si la observacion salio inconclusa: no se repite
    return obs


# ---- VP-E08: timeout ------------------------------------------------------------------------------

def test_vp_e08_el_timeout_corta_el_arbol_vivo_sale_timeout_y_con_null_no_corta(t):
    """VP-E08 - con un manifest sintetico que declara `timeoutSeconds: 9` (A4: tal cual la spec), una suite que duerme 30 s y
    tiene un hijo vivo con su padre vivo sale INFRA TIMEOUT en menos de 20 s; el hijo ya no existe; su archivo de eventos
    tiene un solo inicio; un testigo lanzado por el test, con la misma imagen, sigue vivo; exit 1. La misma suite de 10 s
    con `timeoutSeconds: null` termina sola y sale verde. Niega el vecino: ni WORKER_MUERTO ni SIN_RESUMEN."""
    ID = "VP-E08"
    l1 = Layout([ps_hijo("slow.ps1", 30, 60), py_suite("py_ok.py", 1)], con_runner=True,
                manifest=manifest_texto([ent("slow.ps1", to=9), ent("py_ok.py")]))
    l2 = Layout([ps_hijo("slow.ps1", 10, 5), py_suite("py_ok.py", 1)], con_runner=True,
                manifest=manifest_texto([ent("slow.ps1", to=None), ent("py_ok.py")]))
    ejs, testigo = [], None
    try:
        l1.crear()
        l2.crear()
        r1, r2 = l1.rutas("e08a"), l2.rutas("e08b")
        testigo = lanzar_testigo(l1)
        # La del timeout corre sola: con timeoutSeconds 9 el corte cae poco despues de que el worker arranque la suite, y otra
        # corrida a la vez le sacaria margen al nacimiento del hijo. La de null corre mientras se leen los resultados de esa.
        e1 = correr_runner(l1, r1, 2, env_extra=entorno_de_hijos(l1))
        ejs.append(e1)
        # El hijo tambien se mira MIENTRAS el runner vive: un handle abierto apenas nace (el SO da su hora de salida despues) y, en el
        # instante en que el runner imprime la linea de progreso de la suite cortada, ya tiene que estar muerto. Despues de que el
        # runner termina, un huerfano deja de existir por su cuenta en este entorno (etapa 9, VM-19a: matar solo al worker pasaba
        # en verde con la sola mirada de abajo, hecha despues de e1.esperar()).
        esperar(lambda: _evento_pid(r1["ev"], "slow.ps1", "HIJO") is not None or e1.proc.poll() is not None, 120, paso=0.02)
        pid_hijo = _evento_pid(r1["ev"], "slow.ps1", "HIJO")
        h_hijo = abrir_proceso(pid_hijo) if pid_hijo else None
        esperar(lambda: "INFRA slow.ps1 (" in e1.texto or e1.proc.poll() is not None, 120, paso=0.02)
        informado = "INFRA slow.ps1 (" in e1.texto
        salida_hijo = hora_de_salida_ms(h_hijo) if (h_hijo and informado) else None
        vivo_con_el_runner = e1.proc.poll() is None
        cerrar_handle(h_hijo)
        e1.esperar()
        e2 = correr_runner(l2, r2, 2, env_extra=entorno_de_hijos(l2))
        ejs.append(e2)

        # con timeoutSeconds: 9
        ini = ts_de_inicio(r1["ev"]).get("slow.ps1.ev")
        hijo = _evento_pid(r1["ev"], "slow.ps1", "HIJO")
        t.verdadero("%s precondicion: la suite empezo y su hijo nacio antes del corte (si no, el escenario esta inconcluso: "
                    "timeoutSeconds 9 es menos que el arranque del worker)" % ID, ini is not None and hijo is not None)
        if ini is None or hijo is None:
            return
        lineas = e1.lineas
        t.igual("%s exit 1" % ID, 1, e1.rc)
        t.igual("%s INFRA TIMEOUT slow.ps1 9 s, una sola linea del reporte" % ID, ["INFRA TIMEOUT slow.ps1 9 s"],
                [l for l in lineas if l == "INFRA TIMEOUT slow.ps1 9 s"])
        t.igual("%s en el progreso sale INFRA, y la otra suite OK" % ID, ("INFRA", "OK"),
                (estado_en_progreso(e1, "slow.ps1"), estado_en_progreso(e1, "py_ok.py")))
        t.verdadero("%s menos de 20 s desde el INICIO de la suite hasta que el runner termina (observado: %.1f s)"
                    % (ID, e1.t1 - ini / 1000.0), e1.t1 - ini / 1000.0 < 20)
        t.igual("%s el vecino: ni WORKER_MUERTO ni SIN_RESUMEN ni CANCELADA" % ID, [],
                lineas_con(e1, r"WORKER_MUERTO|SIN_RESUMEN|CANCELADA"))
        t.igual("%s una suite con error de infraestructura" % ID, ["1 suites con error de infraestructura."],
                lineas_con(e1, r"^\d+ suites con error de infraestructura\.$"))
        t.igual("%s un solo INICIO y ningun FIN (no se relanzo)" % ID, (1, 0),
                (e1.inicios().get("slow.ps1.ev"), e1.finales().get("slow.ps1.ev")))
        t.igual("%s el timeout no suma a ok: solo la otra suite cuenta (1/1, forma roja)" % ID,
                "1/1 pasaron. 0 fallaron.", e1.ultima)
        quedan = esperar(lambda: not [p for p in vivos_con("T61H-" + token_de(l1) + "-slow.ps1")], 5)
        t.verdadero("%s el hijo ya no existe (el corte alcanzo al arbol vivo, no solo al worker)" % ID, quedan)
        t.verdadero("%s y ya estaba muerto cuando el runner informo el corte, con el runner todavia vivo (handle abierto al nacer el hijo)" % ID,
                    bool(h_hijo) and bool(informado) and vivo_con_el_runner and salida_hijo is not None)
        t.verdadero("%s el testigo, lanzado fuera del runner con la misma imagen, sigue vivo (nunca por nombre de imagen)" % ID,
                    testigo_vivo(testigo))

        # con timeoutSeconds: null, la misma suite de 10 s
        e2.esperar()
        t.igual("%s null: exit 0 y verde (2/2)" % ID, (0, "2/2 pasaron."), (e2.rc, e2.ultima))
        t.igual("%s null: no se corta (ni TIMEOUT) ni se avisa lenta (ni LENTA)" % ID, [], lineas_con(e2, r"TIMEOUT|LENTA"))
        t.igual("%s null: termino sola, con su INICIO y su FIN" % ID, (1, 1),
                (e2.inicios().get("slow.ps1.ev"), e2.finales().get("slow.ps1.ev")))
        t.igual("%s null: slow.ps1 sale OK" % ID, "OK", estado_en_progreso(e2, "slow.ps1"))
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        soltar(testigo)
        restos = matar_con(token_de(l1), token_de(l2))
        t.igual("%s al terminar no queda vivo ningun proceso con el token del test" % ID, [], [p[0] for p in restos])
        _borrar_layout(l1, *ejs)
        _borrar_layout(l2, *ejs)


# ---- VP-E10: la huella del arbol ------------------------------------------------------------------

def test_vp_e10_la_huella_es_la_misma_tras_una_corrida_verde_y_una_cancelada_y_un_archivo_nuevo_da_arbol_cambiado(t):
    """VP-E10 - sobre un layout con repo git y `.gitignore` con `__pycache__/`, despues de una corrida verde y de una
    cancelada, la huella (spec 5.1, calculada por el test) es la misma que antes y los logs estan fuera de la raiz; si una
    fixture crea un archivo no ignorado en la raiz durante la corrida, el runner sale 1 con INFRA ARBOL_CAMBIADO nombrando
    ese archivo. La corrida cancelada es la de VP-E19 (misma observacion)."""
    ID = "VP-E10"
    lv = Layout([py_suite("py_ok.py", 3), ps_suite("ps_ok.ps1", 3)], con_runner=True)
    lx = Layout([py_ensucia("ensucia.py"), ps_suite("ps_ok.ps1", 1)], con_runner=True)
    ejs = []
    try:
        lv.crear()
        lx.crear()
        h0v, h0x = huella(lv), huella(lx)
        rv, rx = lv.rutas("e10v"), lx.rutas("e10x")
        ev_, ex_ = correr_runner(lv, rv, 2), correr_runner(lx, rx, 2)
        ejs += [ev_, ex_]
        ev_.esperar()
        ex_.esperar()

        # verde
        t.igual("%s verde: exit 0 y la linea final verde (6/6)" % ID, (0, "6/6 pasaron."), (ev_.rc, ev_.ultima))
        t.igual("%s verde: la huella al terminar es la del principio" % ID, h0v, huella(lv))
        t.igual("%s verde: git status limpio" % ID, "", lv.estado().strip())
        t.igual("%s verde: ningun log (.out/.err/.log) bajo la raiz del layout" % ID, [], archivos_de_log_bajo(lv))
        t.igual("%s verde: ni ARBOL_CAMBIADO ni HUELLA_NO_DISPONIBLE" % ID, [], lineas_con(ev_, r"ARBOL_CAMBIADO|HUELLA_NO_DISPONIBLE"))

        # una fixture ensucia el arbol
        lineas = ex_.lineas
        t.igual("%s sucia: exit 1" % ID, 1, ex_.rc)
        t.verdadero("%s sucia: INFRA ARBOL_CAMBIADO" % ID, "INFRA ARBOL_CAMBIADO" in lineas)
        i = lineas.index("INFRA ARBOL_CAMBIADO") if "INFRA ARBOL_CAMBIADO" in lineas else -1
        t.verdadero("%s sucia: y despues nombra el archivo, ensucia_t61.txt (la linea de git status que difiere)" % ID,
                    i >= 0 and any("ensucia_t61.txt" in l for l in lineas[i + 1:i + 10]))
        t.igual("%s sucia: el vecino: ni HUELLA_NO_DISPONIBLE ni una suite con error (la suite en si dio verde)" % ID, [],
                lineas_con(ex_, r"HUELLA_NO_DISPONIBLE|^INFRA (TIMEOUT|WORKER_MUERTO|SIN_RESUMEN)"))
        t.verdadero("%s sucia: la linea final no es la verde" % ID, re.match(r"^\d+/\d+ pasaron\.$", ex_.ultima) is None)
        t.verdadero("%s sucia: control, la huella del layout cambio de verdad" % ID, huella(lx) != h0x)

        # cancelada (la observacion de VP-E19)
        obs = corrida_cancelada()
        t.igual("%s cancelada: la observacion se hizo sin error" % ID, "", obs["error"])
        if not obs["error"]:
            t.igual("%s cancelada: la huella es la del principio" % ID, obs["h0"], obs["h1"])
            t.igual("%s cancelada: git status limpio" % ID, "", obs["estado"].strip())
            t.igual("%s cancelada: ningun log bajo la raiz del layout" % ID, [], obs["logs_en_ly"])
            t.verdadero("%s cancelada: los logs existen y estan en el TempBase, fuera de la raiz (%s)" % (ID, obs["logs"]),
                        len(obs["logs"]) >= 2 and obs["tb_ruta"] is not None)
            t.igual("%s cancelada: no es un cambio de arbol" % ID, [],
                    [l for l in obs["lineas"] if "ARBOL_CAMBIADO" in l or "HUELLA_NO_DISPONIBLE" in l])
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(lv, *ejs)
        _borrar_layout(lx, *ejs)


# ---- VP-E19: cancelacion --------------------------------------------------------------------------

def test_vp_e19_cancelar_no_lanza_mas_no_deja_hijos_limpia_suelta_el_candado_y_sale_distinto_de_cero(t):
    """VP-E19 - al crear el archivo de -CancelFile mientras corren dos suites con hijos marcados con un token y quedan suites
    sin lanzar: no se lanza ninguna mas; en menos de 30 s no queda vivo ningun proceso con el token; el temporal de cada
    suite se borro o figura en LIMPIEZA_INCOMPLETA; el candado inyectado queda libre; el exit es distinto de 0; la salida
    dice CANCELADO, lista terminadas, abortadas y sin lanzar, y no contiene la forma verde de la linea final."""
    ID = "VP-E19"
    obs = corrida_cancelada()
    t.igual("%s la observacion se hizo sin error" % ID, "", obs["error"])
    if obs["error"]:
        return
    lineas = obs["lineas"]
    t.igual("%s control del interop: con el runner vivo el candado pesada.lock da ocupado" % ID, "ocupado", obs["candado_control"])
    t.verdadero("%s control: antes de cancelar vivian el runner, los workers, correr.py y los dos hijos con el token (%d procesos)"
                % (ID, len(obs["vivos_antes"])),
                len(obs["vivos_antes"]) >= 5 and all(any("-" + n in l and "T61H-" in l for l in obs["vivos_antes"]) for n in ("can_1.py", "can_2.py")))
    t.verdadero("%s el exit es distinto de 0 (observado: %s)" % (ID, obs["rc"]), obs["rc"] != 0)
    t.verdadero("%s la salida dice CANCELADO y INCOMPLETO" % ID, "CANCELADO" in obs["texto"] and "INCOMPLETO" in obs["texto"])
    t.igual("%s sin la forma verde de la linea final (ninguna linea `N/M pasaron.`)" % ID, [],
            [l for l in lineas if re.match(r"^\d+/\d+ pasaron\.\s*$", l)])
    t.verdadero("%s la ultima linea es la de CANCELADO - INCOMPLETO" % ID,
                [l for l in lineas if l.strip()][-1].startswith("CANCELADO - INCOMPLETO"))
    m_t = next((re.match(r"^  Terminadas \((\d+)\): (.*)$", l) for l in lineas if re.match(r"^  Terminadas \(", l)), None)
    m_a = next((re.match(r"^  Abortadas \((\d+)\): (.*)$", l) for l in lineas if re.match(r"^  Abortadas \(", l)), None)
    m_s = next((re.match(r"^  Sin lanzar \((\d+)\): (.*)$", l) for l in lineas if re.match(r"^  Sin lanzar \(", l)), None)
    t.verdadero("%s lista terminadas, abortadas y sin lanzar" % ID, bool(m_t and m_a and m_s))
    if m_t and m_a and m_s:
        t.igual("%s terminadas: ninguna" % ID, ("0", ""), (m_t.group(1), m_t.group(2).strip()))
        t.igual("%s abortadas: las dos que vivian" % ID, ("2", "can_1.py, can_2.py"), (m_a.group(1), m_a.group(2).strip()))
        t.igual("%s sin lanzar: las tres que esperaban, en orden canonico" % ID,
                ("3", "ps_pen.ps1, pen_1.py, pen_2.py"), (m_s.group(1), m_s.group(2).strip()))
    t.igual("%s INFRA CANCELADA para cada abortada, una linea cada una" % ID,
            ["INFRA CANCELADA can_1.py", "INFRA CANCELADA can_2.py"], [l for l in lineas if l.startswith("INFRA CANCELADA ")])
    t.igual("%s el vecino: ni TIMEOUT ni WORKER_MUERTO ni SIN_RESUMEN" % ID, [],
            [l for l in lineas if re.search(r"TIMEOUT|WORKER_MUERTO|SIN_RESUMEN", l)])
    # no se lanza ninguna mas
    t.igual("%s solo las dos suites vivas tienen eventos: las sin lanzar nunca empezaron" % ID,
            ["can_1.py.ev", "can_2.py.ev"], sorted(obs["eventos"]))
    inicios = {k: [e[2] for e in v if e[0] == "INICIO"] for k, v in obs["eventos"].items()}
    t.verdadero("%s un solo INICIO por suite, los dos antes de crear el archivo de cancelacion" % ID,
                all(len(v) == 1 and v[0] <= obs["t_cancel_ms"] for v in inicios.values()))
    # ningun proceso con el token
    t.igual("%s en menos de 30 s no queda vivo ningun proceso con el token (workers, correr.py, hijos): quedan %s" % (ID, obs["restos"]),
            [], obs["restos"])
    t.verdadero("%s y fue en menos de 30 s desde la cancelacion (observado: %.1f s)" % (ID, obs["t_sin_procesos"]),
                obs["t_sin_procesos"] < 30)
    # temporales
    nombradas = [l[len("AVISO LIMPIEZA_INCOMPLETA "):] for l in lineas if l.startswith("AVISO LIMPIEZA_INCOMPLETA ")]
    sobran = [d for d in obs["dirs_s"] if not any(n == d or n.startswith(d + "\\") for n in nombradas)]
    t.igual("%s el temporal de cada suite se borro o figura en LIMPIEZA_INCOMPLETA (sin declarar: %s)" % (ID, sobran), [], sobran)
    # candados
    t.igual("%s pesada.lock queda libre" % ID, "libre", obs["lock_pesada"])
    t.verdadero("%s queda la raiz hpp-<id> y su .lock, y nada mas (la cancelada conserva sus logs: spec 19.5, caso 2)" % ID,
                len(obs["tb"]) == 2 and all(re.match(r"^hpp-[0-9a-f]{8}(\.lock)?$", n) for n in obs["tb"]))
    t.igual("%s y el hpp-<id>.lock queda liberado" % ID, ["libre"], list(obs["lock_raiz"].values()))


# ---- VP-E20: un nieto huerfano y un corte por timeout ---------------------------------------------

def test_vp_e20_un_nieto_huerfano_que_retiene_el_temporal_queda_declarado_y_no_se_mata_nada_ajeno(t):
    """VP-E20 - una suite que lanza A, A lanza B y A termina con os._exit (B huerfano), cortada por timeout: la suite sale
    TIMEOUT; B sigue vivo y retiene un archivo del temporal, asi que la salida trae AVISO LIMPIEZA_INCOMPLETA con esa ruta; el
    exit sigue la regla de 16.1 (1: hay un error de infraestructura); un proceso ajeno con la misma imagen que B sigue vivo; la
    huella no cambio. Al final el test mata a B por token. El limite es 8 s (la spec no fija el valor)."""
    ID = "VP-E20"
    ly = Layout([py_huerfano("orf.py"), ps_suite("ps_ok.ps1", 1)], con_runner=True,
                manifest=manifest_texto([ent("orf.py", to=8), ent("ps_ok.ps1")]))
    ej, testigo = None, None
    try:
        ly.crear()
        tok = token_de(ly)
        h0 = huella(ly)
        r = ly.rutas("e20")
        testigo = lanzar_testigo(ly)
        ej = correr_runner(ly, r, 2, env_extra=entorno_de_hijos(ly))
        ej.esperar()
        pid_b = _evento_pid(r["ev"], "orf.py", "HIJO")
        t.verdadero("%s precondicion: B nacio y tomo el archivo antes del corte (si no, el escenario esta inconcluso)" % ID, pid_b is not None)
        if pid_b is None:
            return
        lineas = ej.lineas
        vivos_b = [p for p in procesos() if p[0] == pid_b and "T61H-" + tok + "-orf.py" in p[3]]
        t.igual("%s B (el nieto huerfano) sigue vivo despues del corte: el corte no alcanza a un nieto cuyo padre murio" % ID,
                1, len(vivos_b))
        t.igual("%s la suite sale TIMEOUT, una sola linea del reporte" % ID, ["INFRA TIMEOUT orf.py 8 s"],
                [l for l in lineas if l == "INFRA TIMEOUT orf.py 8 s"])
        t.igual("%s el vecino: ni WORKER_MUERTO ni SIN_RESUMEN ni CANCELADA" % ID, [], lineas_con(ej, r"WORKER_MUERTO|SIN_RESUMEN|CANCELADA"))
        avisos = [l for l in lineas if l.startswith("AVISO LIMPIEZA_INCOMPLETA ")]
        t.verdadero("%s hay AVISO LIMPIEZA_INCOMPLETA con la ruta del archivo retenido (observado: %s)" % (ID, avisos),
                    len(avisos) == 1 and re.search(r"\\hpp-[0-9a-f]{8}\\s\d{3}\\retenido\.bin$", avisos[0]) is not None)
        t.igual("%s exit 1: la regla de 16.1, por el TIMEOUT (el aviso no lo cambia)" % ID, 1, ej.rc)
        t.verdadero("%s la linea final no es la verde" % ID, re.match(r"^\d+/\d+ pasaron\.$", ej.ultima) is None)
        t.igual("%s un solo INICIO de la suite (no se relanzo)" % ID, 1, ej.inicios().get("orf.py.ev"))
        t.verdadero("%s un proceso ajeno con la misma imagen que B (lanzado por el test) sigue vivo" % ID, testigo_vivo(testigo))
        t.igual("%s la huella no cambio" % ID, h0, huella(ly))
        t.igual("%s ni lo dice el runner (ningun ARBOL_CAMBIADO)" % ID, [], lineas_con(ej, r"ARBOL_CAMBIADO"))
        # B retiene el archivo hasta que el test lo mata (por token)
        retenido = list(Path(r["tb"]).glob("hpp-*/s[0-9][0-9][0-9]/retenido.bin"))
        t.igual("%s mientras B vive, el archivo retenido sigue ahi (no se borro a la fuerza)" % ID, 1, len(retenido))
    except Exception as e:
        t.verdadero("%s el layout y su corrida: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        soltar(testigo)
        restos = matar_con(token_de(ly))
        t.igual("%s al terminar (B muerto por token) no queda vivo ningun proceso con el token del test" % ID, [], [p[0] for p in restos])
        _borrar_layout(ly, *([ej] if ej else []))


# ---- VP-E21: limpieza y barrido ----------------------------------------------------------------------

def test_vp_e21_la_limpieza_declara_el_residuo_y_el_barrido_solo_toca_lo_de_un_dueno_muerto(t):
    """VP-E21 - (a) un proceso con un archivo abierto en el temporal de una suite verde: AVISO LIMPIEZA_INCOMPLETA <ruta> y
    exit 0. (b) Un runner matado con Stop-Process deja su raiz y su hpp-<id>.lock (liberado por el SO); la corrida siguiente
    con el mismo TempBase toma ese .lock, borra la raiz y despues el .lock. (c) Una raiz cuyo .lock tiene tomado otro proceso
    vivo no se toca. (d) Un junction dentro de una raiz a barrer, que apunta a una carpeta testigo fuera del TempBase, deja
    la testigo intacta con su contenido. (e) Una corrida verde y limpia no deja raiz ni .lock; la de (a) deja la raiz y su
    .lock liberado, y la siguiente los barre juntos. Corren en tres TempBase propios, con las corridas de limpieza a la vez."""
    ID = "VP-E21"
    la = Layout([py_retiene("ret.py"), ps_suite("ps_ok.ps1", 1)], con_runner=True)
    lb = Layout([ps_suite("dor_1.ps1", 1, dormir=40.0), py_suite("dor_2.py", 1, dormir=40.0)], con_runner=True)
    ls = Layout([ps_suite("ps_ok.ps1", 1)], con_runner=True)           # la corrida "siguiente", que barre
    ejs, tenedor, toks = [], None, []
    junction = None
    try:
        for ly in (la, lb, ls):
            ly.crear()
        toks = [token_de(x) for x in (la, lb, ls)]
        ra, rb, rc = la.rutas("e21a"), lb.rutas("e21b"), ls.rutas("e21c")

        # (c) y (d): dos raices a mano en un TempBase propio (rc)
        tbc = Path(rc["tb"])
        (tbc / "hpp-cafebabe" / "s000").mkdir(parents=True)
        (tbc / "hpp-cafebabe" / "s000" / "keep.txt").write_bytes(b"conservame")
        (tbc / "hpp-cafebabe.lock").write_bytes(b"")
        tenedor, trozos = lanzar_tenedor(ls, tbc / "hpp-cafebabe.lock")
        testigo_dir = ls.tmp / "ext" / "testigo"
        testigo_dir.mkdir(parents=True)
        (testigo_dir / "t.txt").write_bytes(b"intacto")
        (tbc / "hpp-d00dfeed" / "s000").mkdir(parents=True)
        junction = tbc / "hpp-d00dfeed" / "s000" / "jn"
        mk = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(testigo_dir)], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SIN_VENTANA)
        (tbc / "hpp-d00dfeed.lock").write_bytes(b"")
        t.igual("%s precondicion: el junction se creo" % ID, 0, mk.returncode)
        t.verdadero("%s precondicion: el junction lleva a la carpeta testigo (se ve t.txt a traves de el)" % ID,
                    (junction / "t.txt").is_file())
        t.verdadero("%s precondicion: el tenedor tomo el candado de hpp-cafebabe.lock" % ID,
                    bool(esperar(lambda: b"LOCKED" in b"".join(trozos), 60)))
        t.igual("%s control del interop: el candado de la raiz de (c) da ocupado y el de (d) libre" % ID, ("ocupado", "libre"),
                (candado_estado(tbc / "hpp-cafebabe.lock"), candado_estado(tbc / "hpp-d00dfeed.lock")))

        ea = correr_runner(la, ra, 1, env_extra=entorno_de_hijos(la))
        eb = correr_runner(lb, rb, 2)
        ec = correr_runner(ls, rc, 1)                                   # barre (c) y (d) mientras lo demas corre
        ejs += [ea, eb, ec]

        # (b) un runner matado con Stop-Process
        iniciaron = esperar(lambda: all(_inicio_de(rb["ev"], n) for n in ("dor_1.ps1", "dor_2.py")), 120)
        t.verdadero("%s (b) precondicion: las dos suites del runner a matar empezaron" % ID, iniciaron)
        if iniciaron:
            t.igual("%s (b) Stop-Process sobre el runner termina bien" % ID, 0, stop_process(eb.proc.pid))
        # los workers (sin Job Object) quedan huerfanos: se matan por token, y recien entonces se junta la salida del runner
        restos_b = matar_con(toks[1])
        t.igual("%s (b) los workers huerfanos se mataron por token (nada con el token de lb)" % ID, [], [p[0] for p in restos_b])
        eb.esperar(60)
        nb = tb_vacio(rb)
        t.verdadero("%s (b) el runner matado deja su raiz y su .lock, y nada mas (observado: %s)" % (ID, nb),
                    len(nb) == 2 and any(re.match(r"^hpp-[0-9a-f]{8}$", n) for n in nb)
                    and any(re.match(r"^hpp-[0-9a-f]{8}\.lock$", n) for n in nb))
        locks_b = [n for n in nb if n.endswith(".lock")]
        t.igual("%s (b) y el SO libero el candado del .lock (el dueno murio)" % ID, ["libre"],
                [candado_estado(Path(rb["tb"]) / n) for n in locks_b])
        t.igual("%s (b) el runner matado no imprimio la linea final verde" % ID, [],
                [l for l in eb.lineas if re.match(r"^\d+/\d+ pasaron\.$", l)])

        # (a) un proceso retiene un archivo del temporal de una suite verde
        ea.esperar()
        avisos = [l for l in ea.lineas if l.startswith("AVISO ")]
        t.igual("%s (a) exit 0 y la linea final verde (2/2)" % ID, (0, "2/2 pasaron."), (ea.rc, ea.ultima))
        t.verdadero("%s (a) un solo AVISO LIMPIEZA_INCOMPLETA, con la ruta de retenido.bin bajo el temporal de la suite (%s)" % (ID, avisos),
                    len(avisos) == 1 and re.match(r"^AVISO LIMPIEZA_INCOMPLETA .+\\hpp-[0-9a-f]{8}\\s\d{3}\\retenido\.bin$", avisos[0]) is not None)
        t.igual("%s (a) el vecino: ninguna linea INFRA (el residuo no es un error de la suite)" % ID, [], lineas_con(ea, r"^INFRA "))
        na = tb_vacio(ra)
        t.verdadero("%s (e) la corrida de (a) deja la raiz y su .lock, y nada mas (observado: %s)" % (ID, na),
                    len(na) == 2 and any(re.match(r"^hpp-[0-9a-f]{8}$", n) for n in na) and any(re.match(r"^hpp-[0-9a-f]{8}\.lock$", n) for n in na))
        t.igual("%s (e) y su .lock queda liberado (spec 19.5, caso 2)" % ID, ["libre"],
                [candado_estado(Path(ra["tb"]) / n) for n in na if n.endswith(".lock")])
        procs_r = [p for p in procesos() if "T61H-" + toks[0] + "-ret.py" in p[3]]
        t.igual("%s (a) el proceso que retiene sigue vivo hasta que el test lo mata" % ID, 1, len(procs_r))
        restos_a = matar_con(toks[0])
        t.igual("%s (a) el proceso retenedor se mato por token" % ID, [], [p[0] for p in restos_a])

        # (c) y (d): la corrida que barre
        ec.esperar()
        t.igual("%s (c)(d) el runner que barre sale 0, verde" % ID, (0, "1/1 pasaron."), (ec.rc, ec.ultima))
        t.verdadero("%s (c) la raiz con su .lock tomado por otro proceso vivo no se toca: carpeta, contenido y .lock" % ID,
                    (tbc / "hpp-cafebabe" / "s000" / "keep.txt").read_bytes() == b"conservame" and (tbc / "hpp-cafebabe.lock").is_file())
        t.verdadero("%s (c) el tenedor sigue vivo" % ID, tenedor.poll() is None)
        t.igual("%s (c) el runner no dijo nada de esa raiz" % ID, [], lineas_con(ec, r"cafebabe"))
        t.igual("%s (d) la raiz del junction y su .lock se barrieron" % ID, [False, False],
                [(tbc / "hpp-d00dfeed").exists(), (tbc / "hpp-d00dfeed.lock").exists()])
        t.igual("%s (d) la carpeta testigo, fuera del TempBase, sigue intacta con su contenido" % ID, [b"intacto"],
                [p.read_bytes() for p in testigo_dir.iterdir()])
        t.igual("%s (c)(d) en el TempBase solo queda la raiz de (c) y su .lock" % ID, ["hpp-cafebabe", "hpp-cafebabe.lock"], tb_vacio(rc))

        # (e) y (a)(b): la corrida siguiente, con el mismo TempBase, barre las dos cosas juntas
        r1, r2 = ls.rutas("e21s1"), ls.rutas("e21s2")
        r1["tb"], r1["lock"] = ra["tb"], ra["lock"]
        r2["tb"], r2["lock"] = rb["tb"], rb["lock"]
        s1, s2 = correr_runner(ls, r1, 1), correr_runner(ls, r2, 1)
        ejs += [s1, s2]
        s1.esperar()
        s2.esperar()
        t.igual("%s (e) la siguiente de (a): exit 0, verde, sin aviso" % ID, (0, "1/1 pasaron.", []),
                (s1.rc, s1.ultima, [l for l in s1.lineas if l.startswith("AVISO ")]))
        t.igual("%s (e) y barrio la raiz y el .lock de (a) juntos, y no dejo la propia: TempBase vacio" % ID, [], tb_vacio(ra))
        t.igual("%s (b) la siguiente del runner matado: exit 0, verde" % ID, (0, "1/1 pasaron."), (s2.rc, s2.ultima))
        t.igual("%s (b) tomo el .lock, borro la raiz y despues el .lock: TempBase vacio" % ID, [], tb_vacio(rb))
        t.verdadero("%s (e) pesada.lock existe y no se borra" % ID, Path(ra["lock"]).is_file() and Path(rb["lock"]).is_file())
    except Exception as e:
        t.verdadero("%s los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        soltar(tenedor)
        if junction is not None:
            try:
                os.rmdir(str(junction))
            except OSError:
                pass
        restos = matar_con(*toks)
        t.igual("%s al terminar no queda vivo ningun proceso con el token del test" % ID, [], [p[0] for p in restos])
        for ly in (la, lb, ls):
            _borrar_layout(ly, *ejs)


# ---- VP-E22: el candado pesada.lock ----------------------------------------------------------------------------------
#
# Etapa 6 (spec §29 paso 6, §19). «Ocupado» lo dice solo el candado del SO. Reglas de este tramo:
#  - Todo runner de prueba lleva SU -LockPath dentro del <tmp> del layout (ly.rutas): nunca el pesada.lock real del usuario.
#  - Cada sub-caso afirma el motivo y niega el vecino (LOCK_OCUPADO contra LOCK_ILEGIBLE, exit 2 contra exit 1).
#  - candado_estado es una sonda del test, no el runner: cada sub-caso la controla (con el runner vivo da `ocupado`; si no, el
#    interop no sirve y el sub-caso falla fuerte).

_RE_OCUPADO = r"^LOCK_OCUPADO desde .+ \(pid \d+, informativo\)$"


def info_del_candado(ruta):
    """pesada.json (informativo), como dict; None si no esta o no se lee."""
    try:
        return json.loads(Path(ruta).with_suffix(".json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def lanzar_a_la_vez(ly, rutas, workers):
    """Un runner por cada `rutas[i]`, con una barrera justo antes de los Popen (el desfase es de ms). Devuelve (ejecuciones, errores)."""
    barrera = threading.Barrier(len(rutas))
    ejs, errores = [None] * len(rutas), []

    def lanzar(i):
        try:
            barrera.wait(60)
            ejs[i] = correr_runner(ly, rutas[i], workers)
        except Exception as e:
            errores.append("%s: %s" % (type(e).__name__, str(e)[:200]))

    hilos = [threading.Thread(target=lanzar, args=(i,), daemon=True) for i in range(len(rutas))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(120)
    return ejs, errores


def _admision(t, ID, etiqueta, ej, motivo, vecinos):
    """Las afirmaciones comunes de un runner que NO corrio: exit 2, su motivo (una sola linea), ningun vecino, ninguna linea de
    suite ni `pasaron.`, stderr vacio y ningun evento en ninguna fixture."""
    lineas = ej.lineas
    t.igual("%s %s: exit 2 (no 1: no es un error de infraestructura)" % (ID, etiqueta), 2, ej.rc)
    t.igual("%s %s: una sola linea con el motivo" % (ID, etiqueta), 1, len([l for l in lineas if re.match(motivo, l)]))
    t.igual("%s %s: el vecino no sale (%s)" % (ID, etiqueta, vecinos), [], lineas_con(ej, vecinos))
    t.igual("%s %s: ninguna linea de suite ([k/n]) ni `pasaron.`" % (ID, etiqueta), [],
            [l for l in lineas if re.match(r"^\[\d+/\d+\] ", l) or "pasaron." in l])
    t.igual("%s %s: ningun evento en ninguna fixture" % (ID, etiqueta), [], sorted(ej.eventos))
    t.igual("%s %s: stderr vacio" % (ID, etiqueta), b"", ej.err)


def test_vp_e22_a_dos_runners_a_la_vez_corre_uno_y_el_otro_sale_2_y_correr_py_no_queda_excluido(t):
    """VP-E22 (a) y (e) - dos runners lanzados a la vez (barrera antes de los Popen) contra el mismo -LockPath: exactamente uno corre
    sus suites; el otro sale 2 en menos de 10 s con LOCK_OCUPADO, sin linea de suite ni `pasaron.` y sin eventos. (e) Un
    `python correr.py -k` que el test lanza sobre el layout mientras el dueno corre termina normal, con su resumen."""
    ID = "VP-E22"
    suites = [ps_suite("hold_1.ps1", 1, dormir=5.0), ps_suite("hold_2.ps1", 1, dormir=5.0), py_suite("ok_k.py", 2)]
    ly = Layout(suites, con_runner=True)
    ejs = []
    try:
        ly.crear()
        h0 = huella(ly)
        r1, r2 = ly.rutas("e22a1"), ly.rutas("e22a2")
        r2["lock"] = r1["lock"]                           # el MISMO candado; eventos y TempBase distintos
        ejs, errores = lanzar_a_la_vez(ly, [r1, r2], 2)
        ejs = [e for e in ejs if e is not None]
        t.igual("%s (a) precondicion: los dos runners se lanzaron" % ID, ([], 2), (errores, len(ejs)))
        if len(ejs) != 2:
            return
        primero = esperar(lambda: [e for e in ejs if e.proc.poll() is not None], 60)
        t.verdadero("%s (a) precondicion: uno de los dos termino en menos de 60 s (el que no corre)" % ID, bool(primero))
        if not primero:
            return
        perdedor = primero[0].esperar()                  # su fin se mide ahora: el otro sigue corriendo
        ganador = ejs[1] if perdedor is ejs[0] else ejs[0]
        t.verdadero("%s (a) el que no corre sale en menos de 10 s desde su Popen (observado: %.1f s)" % (ID, perdedor.t1 - perdedor.t0),
                    perdedor.t1 - perdedor.t0 < 10)

        # (e) el candado no frena a quien no lo toma: el dueno corre y un correr.py -k, lanzado por el test, termina normal
        en_marcha = esperar(lambda: _inicio_de(ganador.r["ev"], "hold_1.ps1") and _inicio_de(ganador.r["ev"], "hold_2.ps1"), 90)
        t.verdadero("%s (e) precondicion: el dueno esta corriendo (sus dos suites largas empezaron)" % ID, bool(en_marcha))
        t.igual("%s (a) control del interop: con el dueno vivo el candado da ocupado" % ID, "ocupado", candado_estado(ganador.r["lock"]))
        ev_e, tp_e = ly.aislamiento("e22e")
        k = subprocess.run([sys.executable, str(ly.ly / "tests" / "correr.py"), "-k", "ok_k.py"], cwd=str(ly.ly),
                           env=ly.entorno(ev_e, tp_e), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=120, creationflags=SIN_VENTANA)
        sigue = ganador.proc.poll() is None
        t.verdadero("%s (e) precondicion: el dueno seguia corriendo cuando correr.py -k termino (si no, no probo nada)" % ID, sigue)
        k_lineas = lineas_de(k.stdout)
        t.igual("%s (e) correr.py -k termina normal: exit 0" % ID, 0, k.returncode)
        t.igual("%s (e) y con su resumen: la ultima linea es 2/2 pasaron (con punto)" % ID, "2/2 pasaron.", ultima_linea(k.stdout))
        t.verdadero("%s (e) y con su grupo, OK" % ID, "  OK    ok_k  (2)" in k_lineas)
        t.igual("%s (e) la suite corrio de verdad: un INICIO en los eventos propios de correr.py" % ID, {"ok_k.py.ev": 1},
                {n: sum(1 for e in v if e[0] == "INICIO") for n, v in Layout.eventos(ev_e).items()})
        t.igual("%s (e) no menciona el candado (no lo toma ni lo espera) y stderr vacio" % ID, ([], b""),
                ([l for l in k_lineas if "LOCK" in l], k.stderr))
        t.igual("%s (e) el candado sigue ocupado por el dueno despues de correr.py" % ID, "ocupado", candado_estado(ganador.r["lock"]))

        ganador.esperar()
        # (a) exactamente uno corrio sus suites
        final, _rc = esperado_final(suites)
        t.igual("%s (a) exactamente uno corre: los exit son 0 (el dueno) y 2 (el otro)" % ID, (0, 2), (ganador.rc, perdedor.rc))
        t.igual("%s (a) el dueno corrio las tres suites, cada una una vez" % ID,
                {"hold_1.ps1.ev": 1, "hold_2.ps1.ev": 1, "ok_k.py.ev": 1}, ganador.inicios())
        t.igual("%s (a) y termino verde: la linea final es la de sus parametros" % ID, final, ganador.ultima)
        t.igual("%s (a) el dueno no imprimio ningun LOCK_" % ID, [], lineas_con(ganador, r"LOCK_"))
        t.igual("%s (a) el dueno dejo limpio su TempBase" % ID, [], tb_vacio(ganador.r))
        _admision(t, ID, "(a) el que no corre", perdedor, _RE_OCUPADO, r"LOCK_ILEGIBLE|MANIFEST_INVALIDO|^INFRA ")
        t.igual("%s (a) el que no corre no creo ni raiz ni sidecar en su TempBase" % ID, [], tb_vacio(perdedor.r))
        t.verdadero("%s (a) pesada.lock existe y no se borra, y al terminar los dos queda libre" % ID,
                    Path(r1["lock"]).is_file() and candado_estado(r1["lock"]) == "libre")
        t.igual("%s (a) pesada.json (informativo) es el del dueno y al lado del candado no hay nada mas" % ID,
                (ganador.proc.pid, ["pesada.json", "pesada.lock"]),
                ((info_del_candado(r1["lock"]) or {}).get("pid"), sorted(p.name for p in Path(r1["lock"]).parent.iterdir())))
        t.igual("%s (a) la huella del layout es la del principio (correr.py -k no ensucio el arbol)" % ID, h0, huella(ly))
    except Exception as e:
        t.verdadero("%s (a)(e) el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        restos = matar_con(token_de(ly))
        t.igual("%s (a)(e) al terminar no queda vivo ningun proceso con el token del test" % ID, [], [p[0] for p in restos])
        _borrar_layout(ly, *ejs)


def test_vp_e22_b_c_ilegible_sale_2_un_dueno_muerto_libera_y_pesada_json_no_decide(t):
    """VP-E22 (b) y (c) - (b) con -LockPath apuntando a un directorio el runner sale 2 con LOCK_ILEGIBLE (no LOCK_OCUPADO, no 1);
    con el candado tomado por otro proceso vivo y un pesada.json a mano que no cuenta nada cierto, sale 2 con LOCK_OCUPADO y muestra
    ese json como informativo. (c) Si se mata al dueno con Stop-Process, un runner nuevo toma el candado en menos de 10 s;
    pesada.lock sigue existiendo; un pesada.json viejo sobre un candado libre no se muestra como dueno."""
    ID = "VP-E22"
    lh = Layout([ps_suite("hold_k.ps1", 1, dormir=40.0)], con_runner=True)          # el dueno que se mata
    lt = Layout([ps_suite("ps_t.ps1", 1, dormir=4.0)], con_runner=True)            # el layout trivial: el runner nuevo y los que no corren
    ejs, tenedor = [], None
    try:
        lh.crear()
        lt.crear()
        r1, r2 = lh.rutas("e22c1"), lt.rutas("e22c2")
        r2["lock"] = r1["lock"]
        rb, rj = lt.rutas("e22b"), lt.rutas("e22j")
        e1 = correr_runner(lh, r1, 1)                        # R1: el dueno, ocupado con una suite larga
        ejs.append(e1)

        # (b) -LockPath es un directorio
        Path(rb["lock"]).mkdir(parents=True)
        eb = correr_runner(lt, rb, 1)
        ejs.append(eb)
        # (b) el vecino de la otra punta: el candado lo tiene OTRO PROCESO VIVO y pesada.json cuenta algo que no es cierto
        Path(rj["lock"]).parent.mkdir(parents=True)
        Path(rj["lock"]).with_suffix(".json").write_bytes(
            json.dumps({"pid": 424242, "desde": "1999-01-01 00:00:00", "raiz": "x", "workers": 2}).encode("ascii"))
        tenedor, trozos = lanzar_tenedor(lt, rj["lock"])
        t.verdadero("%s (b) precondicion: el tenedor tomo el candado" % ID, bool(esperar(lambda: b"LOCKED" in b"".join(trozos), 60)))
        t.igual("%s (b) control del interop: el candado del tenedor da ocupado" % ID, "ocupado", candado_estado(rj["lock"]))
        ej = correr_runner(lt, rj, 1)
        ejs.append(ej)
        eb.esperar()
        ej.esperar()

        _admision(t, ID, "(b) -LockPath es un directorio", eb, r"^LOCK_ILEGIBLE .+", r"LOCK_OCUPADO|MANIFEST_INVALIDO|ERROR_INTERNO")
        t.verdadero("%s (b) el directorio sigue siendo un directorio (no se borro ni se reemplazo)" % ID, Path(rb["lock"]).is_dir())
        t.igual("%s (b) no creo ni raiz ni sidecar en el TempBase" % ID, [], tb_vacio(rb))
        _admision(t, ID, "(b) candado tomado por otro proceso vivo", ej, _RE_OCUPADO, r"LOCK_ILEGIBLE|MANIFEST_INVALIDO|ERROR_INTERNO")
        t.igual("%s (b) lo ocupado lo dijo el candado del SO; pesada.json a mano solo se muestra, informativo" % ID,
                ["LOCK_OCUPADO desde 1999-01-01 00:00:00 (pid 424242, informativo)"], lineas_con(ej, r"^LOCK_OCUPADO"))
        t.igual("%s (b) el que no corre no reescribio pesada.json" % ID, 424242, (info_del_candado(rj["lock"]) or {}).get("pid"))
        t.verdadero("%s (b) el tenedor sigue vivo y con su candado" % ID, tenedor.poll() is None and candado_estado(rj["lock"]) == "ocupado")
        t.igual("%s (b) no creo ni raiz ni sidecar en el TempBase" % ID, [], tb_vacio(rj))

        # (c) el dueno muerto libera
        en_marcha = esperar(lambda: _inicio_de(r1["ev"], "hold_k.ps1"), 120)
        t.verdadero("%s (c) precondicion: R1 (el dueno) esta corriendo su suite" % ID, bool(en_marcha))
        if not en_marcha:
            return
        t.igual("%s (c) control del interop: con R1 vivo el candado da ocupado" % ID, "ocupado", candado_estado(r1["lock"]))
        t.igual("%s (c) pesada.json cuenta de R1 (informativo): su pid" % ID, e1.proc.pid, (info_del_candado(r1["lock"]) or {}).get("pid"))
        t.igual("%s (c) Stop-Process sobre R1 termina bien" % ID, 0, stop_process(e1.proc.pid))
        # R1 no tiene Job Object: su worker queda huerfano. Se mata por token (el del layout lh) antes de juntar la salida de R1.
        restos = matar_con(token_de(lh))
        t.igual("%s (c) los huerfanos de R1 se mataron por token (nada con el token de lh)" % ID, [], [p[0] for p in restos])
        e1.esperar(60)
        t.verdadero("%s (c) precondicion: el SO libero el candado al morir R1 (libre) y el archivo sigue ahi" % ID,
                    esperar(lambda: candado_estado(r1["lock"]) == "libre", 10) and Path(r1["lock"]).is_file())
        t.verdadero("%s (c) pesada.json de R1 sigue ahi, viejo, sobre un candado libre" % ID, info_del_candado(r1["lock"]) is not None)
        # un pesada.json viejo con marcas inconfundibles, sobre el candado libre
        Path(r1["lock"]).with_suffix(".json").write_bytes(
            json.dumps({"pid": 424242, "desde": "1999-01-01 00:00:00", "raiz": "x", "workers": 2}).encode("ascii"))
        e2 = correr_runner(lt, r2, 1)
        ejs.append(e2)
        # «toma el candado»: pesada.json (informativo) lo escribe el runner justo despues de tomarlo; sirve de reloj y solo de reloj
        # (el candado no se sondea mientras el runner nuevo intenta tomarlo: la sonda lo tendria tomado un instante).
        toma = esperar(lambda: (info_del_candado(r2["lock"]) or {}).get("pid") == e2.proc.pid, 30, paso=0.05)
        t_toma = time.time() - e2.t0
        t.verdadero("%s (c) precondicion: el runner nuevo tomo el candado (escribio su pesada.json)" % ID, bool(toma))
        if toma:
            t.verdadero("%s (c) el runner nuevo toma el candado en menos de 10 s desde su Popen (observado: %.1f s)" % (ID, t_toma),
                        t_toma < 10)
            t.igual("%s (c) control del interop: con el runner nuevo vivo el candado da ocupado" % ID, "ocupado", candado_estado(r2["lock"]))
        ini = esperar(lambda: ts_de_inicio(r2["ev"]).get("ps_t.ps1.ev"), 60)
        t.verdadero("%s (c) y corre su suite (un INICIO)" % ID, bool(ini))
        e2.esperar()
        t.igual("%s (c) el runner nuevo sale 0 y verde" % ID, (0, "1/1 pasaron."), (e2.rc, e2.ultima))
        t.igual("%s (c) el vecino: ni LOCK_OCUPADO ni LOCK_ILEGIBLE" % ID, [], lineas_con(e2, r"LOCK_"))
        t.igual("%s (c) el pesada.json viejo no se muestra como dueno: ni (pid ni 424242 ni 1999" % ID, [],
                [l for l in e2.lineas if "(pid " in l or "424242" in l or "1999" in l])
        t.verdadero("%s (c) pesada.lock existe y no se borra" % ID, Path(r1["lock"]).is_file())
        t.igual("%s (c) el runner nuevo escribio SU pesada.json (el viejo no decide nada)" % ID, e2.proc.pid,
                (info_del_candado(r1["lock"]) or {}).get("pid"))
        t.igual("%s (c) y el candado queda libre al terminar" % ID, "libre", candado_estado(r1["lock"]))
        t.igual("%s (c) al lado del candado solo hay pesada.lock y pesada.json: ningun temporal de la escritura de pesada.json" % ID,
                ["pesada.json", "pesada.lock"], sorted(p.name for p in Path(r1["lock"]).parent.iterdir()))
        t.igual("%s (c) el runner nuevo dejo limpio su TempBase" % ID, [], tb_vacio(r2))
    except Exception as e:
        t.verdadero("%s (b)(c) los layouts y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        soltar(tenedor)
        restos = matar_con(token_de(lh), token_de(lt))
        t.igual("%s (b)(c) al terminar no queda vivo ningun proceso con el token del test" % ID, [], [p[0] for p in restos])
        _borrar_layout(lh, *ejs)
        _borrar_layout(lt, *ejs)


def test_vp_e22_d_el_candado_del_dueno_cancelado_se_suelta_despues_del_ultimo_worker(t):
    """VP-E22 (d) - con el dueno cancelado por la senal inyectable (-CancelFile) mientras sus workers tardan en morir, el candado
    sigue ocupado hasta que murio el ultimo worker (A5: se observa como ORDEN DE EVENTOS, porque un segundo runner arranca en
    ~1 s y la ventana es de ms): un hilo mira el candado cada ~10 ms desde antes de cancelar y el test lee la hora de salida de
    cada worker con un handle abierto antes. Es la observacion de VP-E19 (corrida_cancelada), no una corrida nueva."""
    ID = "VP-E22"
    obs = corrida_cancelada()
    t.igual("%s (d) la observacion se hizo sin error" % ID, "", obs["error"])
    if obs["error"]:
        return
    m = obs.get("muestreo") or {}
    salidas = obs.get("exit_ms") or {}
    t.igual("%s (d) control del interop: con el dueno vivo el candado da ocupado" % ID, "ocupado", obs.get("candado_control"))
    t.igual("%s (d) el muestreo del candado no fallo" % ID, "", m.get("error"))
    t.igual("%s (d) control: el muestreo empezo viendo el candado ocupado (antes de cancelar)" % ID, "ocupado", m.get("primera"))
    t.verdadero("%s (d) el muestreo tomo muchas muestras (%s)" % (ID, m.get("n")), (m.get("n") or 0) >= 20)
    t.igual("%s (d) precondicion: dos workers con handle abierto antes de cancelar y hora de salida leida (si no, inconcluso)" % ID,
            2, len([v for v in salidas.values() if v]))
    libre, ultimo_ocupado = m.get("primera_libre_ms"), m.get("ultima_ocupado_ms")
    t.verdadero("%s (d) precondicion: el muestreo vio el candado libre despues (el dueno lo solto)" % ID, libre is not None)
    if len([v for v in salidas.values() if v]) != 2 or libre is None or ultimo_ocupado is None:
        return
    ultimo_worker = max(salidas.values())
    t.verdadero("%s (d) hubo ventana: el ultimo worker murio despues de pedir la cancelacion (+%d ms)"
                % (ID, ultimo_worker - obs["t_cancel_ms"]), ultimo_worker >= obs["t_cancel_ms"])
    t.verdadero("%s (d) el candado seguia ocupado despues de pedir la cancelacion" % ID, ultimo_ocupado >= obs["t_cancel_ms"])
    t.verdadero("%s (d) un segundo runner habria visto LOCK_OCUPADO hasta que murio el ultimo worker: el candado se vio ocupado "
                "hasta %d ms despues de esa muerte" % (ID, ultimo_ocupado - ultimo_worker), ultimo_ocupado >= ultimo_worker - 50)
    t.verdadero("%s (d) el candado no dio libre antes de que muriera el ultimo worker: libre %+d ms despues de esa muerte"
                % (ID, libre - ultimo_worker), libre >= ultimo_worker - 50)


# ---- VP-E15 a VP-E18: el comparador (etapa 7) -----------------------------------------------------------------
#
# Compare-TestRuns.ps1 se prueba por PROCESOS REALES, igual que el runner: el oraculo copiado y el runner sobre un layout
# sintetico (E15, E16, E18) y pares de textos adulterados a mano (E17, que arma sus entradas con el formato exacto del oraculo
# y no corre ni oraculo ni runner). El veredicto es la PRIMERA linea de la salida del comparador, sola; cada campo de 20.4 que
# difiere sale en una linea `  campo <nombre>: ...`; NO_COMPARABLE sale con lineas `  motivo: ...` y nunca con `  campo`.
# Todo el bloque es ASCII (los acentos, con escapes).

COMPARADOR = "Compare-TestRuns.ps1"
VEREDICTOS = ("EQUIVALENTE", "NO_EQUIVALENTE", "NO_COMPARABLE")
HUELLA_A = "A" * 64
HUELLA_B = "B" * 64
_SEP_PY = "\u2500\u2500 python tests/correr.py " + "\u2500" * 40
_SEP_FIN = "\u2550" * 66
_TILDE_E = "\u00e9"
_TILDE_N = "\u00f1"


class Veredicto:
    """Lo que dijo una corrida del comparador: rc, stdout (UTF-8), stderr, y su lectura."""

    def __init__(self, rc, out, err):
        self.rc, self.out, self.err = rc, out, err

    @property
    def lineas(self):
        return self.out.splitlines()

    @property
    def veredicto(self):
        """La primera linea que es una de las tres palabras SOLA (nunca `in`: EQUIVALENTE esta dentro de NO_EQUIVALENTE)."""
        for l in self.lineas:
            if re.match(r"^(EQUIVALENTE|NO_EQUIVALENTE|NO_COMPARABLE)$", l):
                return l
        return None

    @property
    def campos(self):
        return re.findall(r"(?m)^  campo (\S+):", self.out)

    def linea_de(self, campo):
        return next((l for l in self.lineas if l.startswith("  campo %s:" % campo)), "")

    @property
    def motivos(self):
        return [l for l in self.lineas if l.startswith("  motivo:")]

    def dice(self, palabra):
        """Hay una linea que ES esa palabra (el veredicto vecino se niega con esto)."""
        return any(l == palabra for l in self.lineas)


def comparar(carpeta, serial, paralelo, hs, hp, nombre="c", extra=()):
    """Compare-TestRuns.ps1 del arbol, por un powershell real, sobre dos archivos que escribe el test (bytes)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    fs, fp = carpeta / (nombre + "_s.txt"), carpeta / (nombre + "_p.txt")
    fs.write_bytes(serial)
    fp.write_bytes(paralelo)
    cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
           str(RAIZ / "tests" / COMPARADOR), "-Serial", str(fs), "-Paralelo", str(fp),
           "-HuellaSerial", hs, "-HuellaParalelo", hp] + [str(e) for e in extra]
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=TOPE_S, creationflags=SIN_VENTANA)
    return Veredicto(r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"))


def comparar_varios(carpeta, pares, simultaneas=8, tambien=None):
    """Cada par es un powershell aparte: en hilos, de a `simultaneas`. Devuelve los Veredicto en el orden de `pares` (un par puede
    traer su `nombre` y sus `extra`). `tambien` (una funcion sin argumentos) corre en otro hilo junto con ellos y se devuelve aparte."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=simultaneas + 1) as pool:
        otro = pool.submit(tambien) if tambien else None
        futuros = [pool.submit(comparar, carpeta, p["serial"], p["paralelo"], p["hs"], p["hp"],
                               p.get("nombre", "p%02d" % i), p.get("extra", ()))
                   for i, p in enumerate(pares)]
        resultados = [f.result() for f in futuros]
        return (resultados, otro.result()) if tambien else resultados


_LOTE_PS = """param([string] $Json)
$utf8 = New-Object System.Text.UTF8Encoding $false
try { [Console]::OutputEncoding = $utf8 } catch { }
$script = $env:T61_COMPARADOR
$casos = [System.IO.File]::ReadAllText($Json, $utf8) | ConvertFrom-Json
foreach ($c in $casos) {
    Write-Host ('@@PAR ' + $c.n)
    & $script -Serial $c.s -Paralelo $c.p -HuellaSerial $c.hs -HuellaParalelo $c.hp
    Write-Host ('@@RC ' + $LASTEXITCODE)
}
"""


def comparar_lote(carpeta, pares, procesos_a_la_vez=4):
    """Lo mismo que `comparar` para muchos pares, con muchos menos powershell: el arranque de un powershell cuesta ~1,5 s y con
    27 pares dominaba el tiempo. Cada proceso corre `& Compare-TestRuns.ps1 -Serial ... -Paralelo ... -HuellaSerial ... -HuellaParalelo ...`
    (el MISMO script con los MISMOS cuatro parametros) para su parte de los pares y deja el exit de cada uno (`$LASTEXITCODE`, que es
    el del `exit` del script). Devuelve los Veredicto en el orden de `pares`."""
    from concurrent.futures import ThreadPoolExecutor
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "lote.ps1").write_bytes(_LOTE_PS.encode("ascii"))
    partes = [list(range(i, len(pares), procesos_a_la_vez)) for i in range(procesos_a_la_vez)]

    def uno(k, indices):
        casos = []
        for i in indices:
            fs, fp = carpeta / ("l%02d_s.txt" % i), carpeta / ("l%02d_p.txt" % i)
            fs.write_bytes(pares[i]["serial"])
            fp.write_bytes(pares[i]["paralelo"])
            casos.append({"n": i, "s": str(fs), "p": str(fp), "hs": pares[i]["hs"], "hp": pares[i]["hp"]})
        ruta_json = carpeta / ("lote%d.json" % k)
        ruta_json.write_bytes(json.dumps(casos).encode("ascii"))
        env = os.environ.copy()
        env["T61_COMPARADOR"] = str(RAIZ / "tests" / COMPARADOR)
        r = subprocess.run([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                            str(carpeta / "lote.ps1"), "-Json", str(ruta_json)], env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TOPE_S, creationflags=SIN_VENTANA)
        out, err = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
        res = {}
        for m in re.finditer(r"(?s)@@PAR (\d+)\r?\n(.*?)@@RC (-?\d+)\r?\n", out):
            res[int(m.group(1))] = Veredicto(int(m.group(3)), m.group(2), err)
        return res

    with ThreadPoolExecutor(max_workers=procesos_a_la_vez) as pool:
        union = {}
        for parcial in [f.result() for f in [pool.submit(uno, k, ix) for k, ix in enumerate(partes) if ix]]:
            union.update(parcial)
    faltan = [i for i in range(len(pares)) if i not in union]
    if faltan:
        raise RuntimeError("el lote no devolvio los pares %r" % faltan)
    return [union[i] for i in range(len(pares))]


def _parametros_de_script(ruta, carpeta):
    """Los parametros que declara un script (por AST, sin ejecutarlo), sin los comunes de CmdletBinding."""
    env = os.environ.copy()
    env["T61_SCRIPT"] = str(ruta)
    cmd = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
           "$e = $null; $a = [System.Management.Automation.Language.Parser]::ParseFile($env:T61_SCRIPT, [ref]$null, [ref]$e); "
           "$a.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath + ':' + $_.StaticType.Name }"]
    r = subprocess.run(cmd, env=env, cwd=str(carpeta), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=TOPE_S, creationflags=SIN_VENTANA)
    return sorted(l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if l.strip())


# El texto del oraculo con su formato exacto (Invoke-Tests.ps1:190-223, 284-291 y correr.py:85-92), a partir de un modelo.

def modelo_base(rojo=True, detallado=False):
    """Un modelo de salida del oraculo. Todo explicito (resumenes y linea final incluidos), de modo que adulterar una
    parte no arrastra a las demas. `ps`: (grupo, n, malos); `filas_ps`: {grupo: [nombres]}; `fallos_ps`: (grupo, nombre,
    detalle); `py`: (stem, n, malos); `filas_py`: (stem, nombre, ok, detalle) en el orden en que corren."""
    if rojo:
        ps = [("ps_a", 3, 0), ("ps_b", 2, 1)]
        filas_ps = {"ps_a": ["fila-01", "fila-02", "fila-03"], "ps_b": ["fila-01", "fila-02"]}
        fallos_ps = [("ps_b", "fila-01", "esperado <1> / obtenido <2>")]
        py = [("py_a", 4, 0), ("py_b", 3, 1)]
        filas_py = [("py_a", "fila-%02d" % i, True, "") for i in range(1, 5)]
        filas_py += [("py_b", "fila-01", True, ""), ("py_b", "fila-02", False, "esperado <1> / obtenido <2>"),
                     ("py_b", "fila-03", True, "")]
        return {"ps": ps, "filas_ps": filas_ps, "fallos_ps": fallos_ps, "py": py, "filas_py": filas_py,
                "ps_resumen": (4, 5, 1), "py_resumen": (6, 7), "final": "10/12 pasaron. 2 fallaron.",
                "infra": [], "antes": [], "detallado": detallado}
    ps = [("ps_a", 3, 0), ("ps_b", 2, 0)]
    filas_ps = {"ps_a": ["fila-01", "fila-02", "fila-03"], "ps_b": ["fila-01", "fila-02"]}
    py = [("py_a", 4, 0), ("py_b", 3, 0)]
    filas_py = [("py_a", "fila-%02d" % i, True, "") for i in range(1, 5)]
    filas_py += [("py_b", "fila-%02d" % i, True, "") for i in range(1, 4)]
    return {"ps": ps, "filas_ps": filas_ps, "fallos_ps": [], "py": py, "filas_py": filas_py,
            "ps_resumen": (5, 5, 0), "py_resumen": (7, 7), "final": "12/12 pasaron.",
            "infra": [], "antes": [], "detallado": detallado}


def salida_oraculo(m, crlf=False):
    L = list(m["antes"]) + ["", "gcba-harness - tests", ""]
    for g, n, malos in m["ps"]:
        L.append("  OK    %s  (%d)" % (g, n) if not malos else "  FALLA %s  (%d/%d)" % (g, malos, n))
        if m["detallado"]:
            L += ["        \u00b7 " + x for x in m["filas_ps"].get(g, [])]
    if m["fallos_ps"]:
        L += ["", "Fallos:"]
        for g, n, det in m["fallos_ps"]:
            L += ["  [%s] %s" % (g, n), "      " + det]
    ok, total, malos = m["ps_resumen"]
    L += ["", "%d/%d pasaron (PowerShell)." % (ok, total) + (" %d fallaron." % malos if malos else "")]
    L += ["", _SEP_PY, "", "", "gcba-harness - tests (python)", ""]
    for g, n, malos in m["py"]:
        L.append("  %s %s  (%d)" % ("OK   " if not malos else "FALLA", g, n))
    for g, n, ok, det in m["filas_py"]:
        if not ok:
            L += ("    MAL %s / %s %s" % (g, n, det)).split("\n")
        elif m["detallado"]:
            L.append("    ok  %s / %s " % (g, n))
    ok, total = m["py_resumen"]
    L += ["", "%d/%d pasaron." % (ok, total), ""]
    L += list(m["infra"])
    if m["infra"]:
        L.append("%d suites con error de infraestructura." % len(m["infra"]))
    L += ["", _SEP_FIN, m["final"]]
    return (("\r\n" if crlf else "\n").join(L) + ("\r\n" if crlf else "\n")).encode("utf-8")


def con(m, **cambios):
    """Una copia del modelo con esas partes cambiadas."""
    import copy
    n = copy.deepcopy(m)
    n.update(cambios)
    return n


def _cambiar_fila(filas, grupo, nombre, nuevo=None, ok=None):
    res = []
    for g, n, o, d in filas:
        if g == grupo and n == nombre:
            n = nuevo or n
            if ok is not None:
                o, d = ok, ("" if ok else "esperado <1> / obtenido <2>")
        res.append((g, n, o, d))
    return res


def _guardar(carpeta, nombre, contenido):
    ruta = Path(carpeta) / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    return ruta


# El modelo de lo que dice una salida, calculado APARTE del comparador con las regex de los tests de arriba: asi E15 y E16 no
# dependen del comparador para afirmar que oraculo y runner coinciden (un comparador que mirara solo totales los daria
# equivalentes).

def modelo_de(salida):
    lineas = lineas_de(region(salida) or b"")
    grupo = None
    filas_ps, filas_py = [], []
    en_py = False
    for l in lineas:
        if l.startswith("gcba-harness - tests (python)"):
            en_py = True
            continue
        m = re.match(r"^  (?:OK    |FALLA )(.+?)  \((\d+(?:/\d+)?)\)$", l)
        if m and not en_py:
            grupo = m.group(1)
            continue
        m = re.match(r"^ {8}\u00b7 (.*)$", l)
        if m and not en_py and grupo is not None:
            filas_ps.append((grupo, m.group(1)))
            continue
        m = re.match(r"^    ok  (.+?) / (.*?) ?$", l)
        if m and en_py:
            filas_py.append((m.group(1), m.group(2), True))
    i_fallos = lineas.index("Fallos:") if "Fallos:" in lineas else None
    fallos_ps = []
    if i_fallos is not None:
        for l in lineas[i_fallos + 1:]:
            if l.startswith("gcba-harness - tests (python)"):
                break
            m = re.match(r"^  \[(.+?)\] (.*)$", l)
            if m:
                fallos_ps.append((m.group(1), m.group(2)))
    prefijos = (" esperado <", " no contiene <", " contiene <", " no esta vacio: <", " es falso", " Traceback")
    malas_py = []
    for l in lineas:
        m = re.match(r"^    MAL (.+?) / (.*)$", l)
        if m:
            cortes = [m.group(2).index(p) for p in prefijos if p in m.group(2)]
            malas_py.append((m.group(1), m.group(2)[:min(cortes)] if cortes else m.group(2)))
    return {"ps": list(grupos_ps(lineas).items()), "py": grupos_py(lineas), "filas_ps": sorted(filas_ps),
            "filas_py": sorted(filas_py), "fallos_ps": sorted(fallos_ps), "malas_py": sorted(malas_py),
            "final": ultima_linea(salida), "lineas": lineas}


def _par_oraculo_y_runner(ly, clave, extra=(), workers=4):
    """El oraculo (sin -SoloCaso, sobre el layout entero) y el runner, A LA VEZ: son dos procesos aparte, cada uno con sus
    eventos, su TEMP y sus rutas propios. Devuelve (corrida del oraculo, ejecucion del runner), las dos terminadas."""
    ej = correr_runner(ly, ly.rutas(clave + "r"), workers, extra)
    o = Corrida(ly, clave + "o", ly.oraculo, list(extra))
    try:
        o.correr()
    except Exception:
        ej.matar()
        raise
    ej.esperar()
    return o, ej


def ps_tilde(nombre):
    """VP-E15: un .ps1 cuyo grupo y cuya fila llevan tildes (escritas con [char]: el archivo es ASCII)."""
    texto = (_PS_EVENTOS.replace("@@SUITE@@", nombre) + "Write-T61Ev 'INICIO'\n"
             "Set-Grupo ('grupo-t' + [char]0x00E9 + 'cnico')\n"
             "Assert-Igual ('fila-' + [char]0x00F1) 1 1\n"
             "Assert-Contiene 'fila-02' 'a' 'abc'\n"
             "Write-T61Ev 'FIN'\n")
    return {"nombre": nombre, "texto": texto, "motor": "ps", "filas": 2, "rojas": 0, "grupo": "grupo-t%scnico" % _TILDE_E}


def py_tilde(nombre):
    """VP-E15: un .py cuyo stem (el nombre del archivo) y cuya fila llevan tildes. En el texto, solo escapes."""
    texto = _PY_EVENTOS.replace("@@SUITE@@", nombre.encode("unicode_escape").decode("ascii"))
    texto += ('\n\ndef test_filas(t):\n    t.igual("fila-\\u00f1", 1, 1)\n    t.verdadero("fila-02", True)\n'
              '    _ev("FIN")\n')
    return {"nombre": nombre, "texto": texto, "motor": "py", "filas": 2, "rojas": 0, "grupo": nombre[:-len(".py")]}


def test_vp_e15_el_oraculo_y_el_runner_sobre_un_layout_verde_son_equivalentes_con_detallado(t):
    """VP-E15 - sobre un layout sintetico verde con nombres de grupo con tildes (un .ps1 y un .py), dos .ps1 con el mismo grupo
    en otra capitalizacion, otro .ps1 y dos .py, el oraculo copiado (sin -SoloCaso, sobre el layout entero) y el runner, los dos
    con -Detallado, dan al comparador EQUIVALENTE: mismo exit, mismas lineas de grupo en el mismo orden, mismos conteos y mismo
    multiconjunto de filas. Esas igualdades se afirman ANTES y APARTE del comparador (un comparador que mirara solo totales las
    daria por buenas); despues, el veredicto y su vecino."""
    ID = "VP-E15"
    suites = [ps_tilde("ps_tilde.ps1"), ps_suite("ps_comp_a.ps1", 2, grupo="Compartido"),
              ps_suite("ps_comp_b.ps1", 3, grupo="compartido"), ps_suite("ps_ok.ps1", 4),
              py_tilde("py_t%scnico.py" % _TILDE_E), py_suite("py_ok1.py", 3), py_suite("py_ok2.py", 5)]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ly.crear()
        h0 = huella(ly)
        ej = correr_runner(ly, ly.rutas("e15r"), 4, ["-Detallado"])
        o = Corrida(ly, "e15o", ly.oraculo, ["-Detallado"]).correr()
        ej.esperar()
        h1 = huella(ly)
        total = sum(s["filas"] for s in suites)
        t.igual("%s control: la huella del layout es la misma despues de las dos corridas" % ID, h0, h1)
        t.igual("%s el oraculo sale 0 y el runner sale 0 (el mismo exit)" % ID, (0, 0), (o.rc, ej.rc))
        t.igual("%s las dos ultimas lineas son la combinada verde, de los parametros" % ID,
                ("%d/%d pasaron." % (total, total),) * 2, (o.ultima, ej.ultima))
        t.igual("%s stderr vacio en los dos" % ID, (b"", b""), (o.err, ej.err))
        mo, mr = modelo_de(o.out), modelo_de(ej.out)
        t.verdadero("%s control: los dos tienen su region comparable y filas -Detallado" % ID,
                    bool(mo["lineas"]) and bool(mr["lineas"]) and bool(mo["filas_ps"]) and bool(mo["filas_py"]))
        t.igual("%s mismas lineas de grupo PowerShell, en el mismo orden (nombre y cuenta)" % ID, mo["ps"], mr["ps"])
        t.igual("%s mismas lineas de grupo de Python, en el mismo orden (stem y cuenta)" % ID, mo["py"], mr["py"])
        t.igual("%s el grupo con tilde y el que se reagrupa salen como dice el oraculo (una sola vez, con la suma)" % ID,
                [("Compartido", ("OK", "5")), ("grupo-t%scnico" % _TILDE_E, ("OK", "2")), ("ps_ok", ("OK", "4"))],
                sorted(mr["ps"]))
        t.igual("%s los stems de Python, con su tilde y en el orden de sorted()" % ID,
                [("OK", "py_ok1", 3), ("OK", "py_ok2", 5), ("OK", "py_t%scnico" % _TILDE_E, 2)],
                sorted(mr["py"], key=lambda g: g[1]))
        t.igual("%s mismo multiconjunto de filas PowerShell (grupo, nombre)" % ID, mo["filas_ps"], mr["filas_ps"])
        t.igual("%s mismo multiconjunto de filas de Python (grupo, nombre, ok)" % ID, mo["filas_py"], mr["filas_py"])
        t.igual("%s las filas PowerShell salen de los parametros: 2 + 2 + 3 + 4 por grupo" % ID,
                {"Compartido": 5, "grupo-t%scnico" % _TILDE_E: 2, "ps_ok": 4},
                {g: sum(1 for x in mr["filas_ps"] if x[0] == g) for g in {x[0] for x in mr["filas_ps"]}})
        t.verdadero("%s la fila con tilde esta en las dos (PowerShell y Python)" % ID,
                    ("grupo-t%scnico" % _TILDE_E, "fila-%s" % _TILDE_N) in mr["filas_ps"]
                    and ("py_t%scnico" % _TILDE_E, "fila-%s" % _TILDE_N, True) in mr["filas_py"])
        t.igual("%s las dos corrieron las siete suites, una vez cada una" % ID,
                ({n: 1 for n in sorted(s["nombre"] + ".ev" for s in suites)},) * 2, (o.inicios(), ej.inicios()))
        t.vacio("%s sin lineas INFRA ni AVISO en el runner" % ID, lineas_con(ej, r"^(INFRA|AVISO) "))

        # El veredicto, y su vecina (el mismo par con otra huella no es EQUIVALENTE): dos powershell a la vez.
        v, w = comparar_varios(ly.tmp / "cmp", [
            {"serial": o.out, "paralelo": ej.out, "hs": h0, "hp": h1, "nombre": "par"},
            {"serial": o.out, "paralelo": ej.out, "hs": HUELLA_A, "hp": HUELLA_B, "nombre": "otra"}])
        t.igual("%s el comparador dice EQUIVALENTE" % ID, "EQUIVALENTE", v.veredicto)
        t.igual("%s y sale 0" % ID, 0, v.rc)
        t.vacio("%s sin ningun campo que difiera ni motivo" % ID, v.campos + v.motivos)
        t.verdadero("%s no dice NO_EQUIVALENTE ni NO_COMPARABLE" % ID,
                    not v.dice("NO_EQUIVALENTE") and not v.dice("NO_COMPARABLE"))
        t.igual("%s stderr del comparador vacio" % ID, "", v.err)
        t.igual("%s control: con otra huella el mismo par es NO_COMPARABLE" % ID, ("NO_COMPARABLE", 1), (w.veredicto, w.rc))
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def test_vp_e16_con_fallos_inyectados_el_oraculo_y_el_runner_salen_1_y_son_equivalentes(t):
    """VP-E16 - con una fila roja PowerShell, una Python y un .py que no carga, el oraculo copiado y el runner salen 1 los dos y
    el comparador da EQUIVALENTE, con el mismo multiconjunto de filas fallidas (grupo, nombre) en los dos: calculado aparte
    (Fallos: para PowerShell; MAL cortada en el primer prefijo de detalle conocido para Python) y comparado con lo que dicen los
    parametros de las fixtures."""
    ID = "VP-E16"
    suites = [ps_suite("ps_rojo.ps1", 4, rojas=1), py_suite("py_rojo.py", 5, rojas=1),
              py_suite("py_import_error.py", 0, no_carga=True), ps_suite("ps_ok.ps1", 3), py_suite("py_ok.py", 4)]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ly.crear()
        h0 = huella(ly)
        o, ej = _par_oraculo_y_runner(ly, "e16")
        h1 = huella(ly)
        final, rc_esperado = esperado_final(suites)
        t.igual("%s control: la huella del layout es la misma despues de las dos corridas" % ID, h0, h1)
        t.igual("%s los dos salen 1" % ID, (1, 1), (o.rc, ej.rc))
        t.igual("%s los dos dicen la misma linea final, la de los parametros" % ID,
                (final, final), (o.ultima, ej.ultima))
        mo, mr = modelo_de(o.out), modelo_de(ej.out)
        esperadas_ps = [("ps_rojo", "fila-01")]
        esperadas_py = sorted([("py_rojo", "fila-01"), ("py_import_error", "el archivo de casos se pudo cargar")])
        t.igual("%s las filas fallidas de PowerShell son la inyectada, en el oraculo y en el runner" % ID,
                (esperadas_ps, esperadas_ps), (mo["fallos_ps"], mr["fallos_ps"]))
        t.igual("%s las filas MAL de Python son la inyectada y la de carga, en el oraculo y en el runner" % ID,
                (esperadas_py, esperadas_py), (mo["malas_py"], mr["malas_py"]))
        t.igual("%s mismas lineas de grupo en los dos motores y mismo orden" % ID,
                (mo["ps"], mo["py"]), (mr["ps"], mr["py"]))
        t.igual("%s la suite que no carga es un grupo de una fila FALLA con su stem" % ID,
                ("FALLA", "py_import_error", 1), next((g for g in mr["py"] if g[1] == "py_import_error"), None))
        t.vacio("%s el runner no tiene INFRA: son filas rojas, no errores de infraestructura" % ID,
                lineas_con(ej, r"^INFRA "))
        # La vecina: sacarle al runner la fila de carga la hace NO_EQUIVALENTE (no es que el comparador mire solo el exit).
        sin_carga = "\n".join(l for l in ej.out.decode("utf-8", "replace").splitlines()
                              if "el archivo de casos se pudo cargar" not in l or not l.startswith("    MAL ")) + "\n"
        v, w = comparar_varios(ly.tmp / "cmp", [
            {"serial": o.out, "paralelo": ej.out, "hs": h0, "hp": h1, "nombre": "par"},
            {"serial": o.out, "paralelo": sin_carga.encode("utf-8"), "hs": h0, "hp": h1, "nombre": "sinc"}])
        t.igual("%s el comparador dice EQUIVALENTE" % ID, "EQUIVALENTE", v.veredicto)
        t.igual("%s y sale 0 (la equivalencia es del par, no de que las suites pasen)" % ID, 0, v.rc)
        t.vacio("%s sin ningun campo que difiera ni motivo" % ID, v.campos + v.motivos)
        t.verdadero("%s no dice NO_EQUIVALENTE ni NO_COMPARABLE" % ID,
                    not v.dice("NO_EQUIVALENTE") and not v.dice("NO_COMPARABLE"))
        t.igual("%s control: sin la fila MAL de carga el mismo par es NO_EQUIVALENTE y nombra las filas fallidas" % ID,
                ("NO_EQUIVALENTE", ["filas-fallidas"]), (w.veredicto, [c for c in w.campos if c == "filas-fallidas"]))
        t.contiene("%s y esa linea nombra la suite que no carga" % ID, "py_import_error", w.linea_de("filas-fallidas"))
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


def _pares_e17():
    """Los pares adulterados a mano: (id, serial, paralelo, huellas, veredicto esperado, campos esperados en orden,
    {campo: [textos que su linea nombra]}, textos que los motivos nombran)."""
    base, verde = modelo_base(), modelo_base(rojo=False)
    det, det_verde = modelo_base(detallado=True), modelo_base(rojo=False, detallado=True)
    S = salida_oraculo
    P = []

    def par(id_, s, p, v, campos=(), nombran=None, motivos=(), hs=HUELLA_A, hp=HUELLA_A, en_salida=()):
        P.append({"id": id_, "serial": s, "paralelo": p, "hs": hs, "hp": hp, "v": v, "campos": list(campos),
                  "nombran": nombran or {}, "motivos": list(motivos), "en_salida": list(en_salida)})

    par("el par identico", S(base), S(base), "EQUIVALENTE")
    par("el par identico verde", S(verde), S(verde), "EQUIVALENTE")
    # (1) el total, en la linea final y en el resumen de PowerShell
    par("total distinto en 1", S(base), S(con(base, ps_resumen=(4, 6, 1), final="10/13 pasaron. 2 fallaron.")),
        "NO_EQUIVALENTE", ["total-ps", "total"],
        {"total-ps": ["serial=5", "paralelo=6"], "total": ["serial=12", "paralelo=13"]})
    # (2) un grupo de mas en el runner
    par("un grupo de mas", S(base), S(con(base, ps=base["ps"] + [("ps_c", 2, 0)])), "NO_EQUIVALENTE", ["grupos-ps"],
        {"grupos-ps": ["solo en paralelo: ps_c (2)"]})
    # (3) mismo numero de fallos con otro nombre: PowerShell y Python
    par("mismo numero de fallos con otro nombre (PowerShell)",
        S(base), S(con(base, fallos_ps=[("ps_b", "fila-77", "esperado <1> / obtenido <2>")])),
        "NO_EQUIVALENTE", ["filas-fallidas"], {"filas-fallidas": ["ps [ps_b] fila-01", "ps [ps_b] fila-77"]})
    par("mismo numero de fallos con otro nombre (Python)",
        S(base), S(con(base, filas_py=_cambiar_fila(base["filas_py"], "py_b", "fila-02", "fila-99"))),
        "NO_EQUIVALENTE", ["filas-fallidas"], {"filas-fallidas": ["py py_b / fila-02", "py py_b / fila-99"]})
    # (4) exit distinto: la forma roja con N = 0 (16.4) contra la verde
    par("exit distinto", S(verde), S(con(verde, final="12/12 pasaron. 0 fallaron.")), "NO_EQUIVALENTE", ["exit"],
        {"exit": ["serial=0", "paralelo=1"]})
    # (5) grupos permutados
    par("grupos permutados (PowerShell)", S(base), S(con(base, ps=list(reversed(base["ps"])))), "NO_EQUIVALENTE",
        ["grupos-ps"], {"grupos-ps": ["mismo conjunto, otro orden", "ps_a (3)", "ps_b (1/2)"]})
    par("grupos permutados (Python)", S(base), S(con(base, py=list(reversed(base["py"])))), "NO_EQUIVALENTE",
        ["grupos-py"], {"grupos-py": ["mismo conjunto, otro orden", "py_a (4)", "py_b (3)"]})
    # (6) una linea INFRA en el runner
    par("una linea INFRA en el runner", S(base), S(con(base, infra=["INFRA SIN_RESUMEN py_x.py"])), "NO_EQUIVALENTE",
        ["infra"], {"infra": ["INFRA SIN_RESUMEN py_x.py"]})
    # NO_COMPARABLE: huellas distintas (con el mismo texto y con otro), y filas MAL ambiguas
    par("huellas distintas con el mismo texto", S(base), S(base), "NO_COMPARABLE", motivos=[HUELLA_A, HUELLA_B],
        hs=HUELLA_A, hp=HUELLA_B)
    par("huellas distintas con otro texto", S(base), S(con(base, final="10/13 pasaron. 2 fallaron.")), "NO_COMPARABLE",
        motivos=[HUELLA_A, HUELLA_B], hs=HUELLA_A, hp=HUELLA_B)
    ambigua = con(base, filas_py=base["filas_py"][:5] + [
        ("py_b", "fila-02", False, "algo raro sin prefijo conocido")] + base["filas_py"][6:])
    par("fila MAL sin prefijo de detalle conocido en los dos", S(ambigua), S(ambigua), "NO_COMPARABLE",
        motivos=["(serial)", "(paralelo)", "algo raro sin prefijo conocido"])
    par("fila MAL sin prefijo de detalle conocido solo en el runner", S(base), S(ambigua), "NO_COMPARABLE",
        motivos=["(paralelo)", "algo raro sin prefijo conocido"])
    # Los seis prefijos conocidos, con una traza de varias lineas: el par identico es EQUIVALENTE.
    detalles = ["esperado <1> / obtenido <2>", "no contiene <x>", "contiene <x>", "no esta vacio: <'a'>", "es falso",
                "Traceback (most recent call last):\n  File \"x.py\", line 3, in test_x\n    t.igual(1, 2)\nAssertionError: x"]
    seis = con(base, py=[("py_a", 4, 0), ("py_b", 6, 6)], py_resumen=(4, 10), final="8/15 pasaron. 7 fallaron.",
               filas_py=[("py_a", "fila-%02d" % i, True, "") for i in range(1, 5)]
               + [("py_b", "fila-%02d" % i, False, d) for i, d in enumerate(detalles, 1)])
    par("las seis formas de detalle conocidas, con una traza de varias lineas", S(seis), S(seis), "EQUIVALENTE")
    # Los detalles se muestran y no se comparan.
    otros = con(base, fallos_ps=[("ps_b", "fila-01", "otro detalle muy distinto")],
                filas_py=[(g, n, o, "esperado <1> / obtenido <3>" if not o else d) for g, n, o, d in base["filas_py"]])
    par("el mismo fallo con otro detalle (PowerShell y Python)", S(base), S(otros), "EQUIVALENTE")
    # La region comparable: lo anterior a la ultima cabecera no cuenta, ni el fin de linea.
    previo = ["Invoke-Tests-Parallel: workers=2 TempBase=C:\\tb bash=", "[1/4] OK ps_a.ps1 (3) 1.2 s",
              "", "gcba-harness - tests", "[2/4] FALLA py_b.py (3) 0.9 s", "AVISO LIMPIEZA_INCOMPLETA C:\\tb\\hpp-0\\s001"]
    par("el runner con su progreso antes, el oraculo con CRLF y su linea de corrida parcial",
        S(con(base, antes=["Corrida parcial (-SoloCaso x.py): no es la compuerta."]), crlf=True),
        S(con(base, antes=previo)), "EQUIVALENTE")
    # (5) con -Detallado en los dos
    par("con -Detallado, una fila PowerShell con otro nombre", S(det),
        S(con(det, filas_ps={"ps_a": ["fila-01", "fila-0X", "fila-03"], "ps_b": ["fila-01", "fila-02"]})),
        "NO_EQUIVALENTE", ["filas"], {"filas": ["ps [ps_a] fila-02", "ps [ps_a] fila-0X"]})
    par("con -Detallado, una fila Python con otro nombre", S(det),
        S(con(det, filas_py=_cambiar_fila(det["filas_py"], "py_a", "fila-03", "fila-0X"))),
        "NO_EQUIVALENTE", ["filas"], {"filas": ["py py_a / fila-03 (ok)", "py py_a / fila-0X (ok)"]})
    par("con -Detallado, una fila Python verde en uno y roja en el otro", S(det),
        S(con(det, filas_py=_cambiar_fila(det["filas_py"], "py_a", "fila-03", ok=False))),
        "NO_EQUIVALENTE", ["filas-fallidas", "filas"], {"filas-fallidas": ["py py_a / fila-03"],
                                                        "filas": ["py py_a / fila-03 (ok)", "py py_a / fila-03 (MAL)"]})
    par("-Detallado solo en el oraculo: las filas no se comparan y lo demas es igual", S(det), S(base), "EQUIVALENTE",
        en_salida=["nota: solo el oraculo corrio con -Detallado"])
    # Elecciones del builder sobre salidas sin la forma del reporte.
    cortada = S(base).decode("utf-8").rsplit("\n", 3)[0].encode("utf-8")
    par("el runner cortado antes de su linea final", S(base), cortada, "NO_COMPARABLE", motivos=["(paralelo)", "linea final"])
    par("el runner sin la cabecera del reporte", S(base), b"[1/4] OK ps_a.ps1 (3) 1.2 s\n", "NO_COMPARABLE",
        motivos=["(paralelo)", "gcba-harness - tests"])
    par("el runner con ERROR_INTERNO y sin reporte: su INFRA lo hace NO_EQUIVALENTE", S(base),
        b"INFRA ERROR_INTERNO boom\nERROR INTERNO del agregador: no hay resultado. 1 suites con error de infraestructura.\n",
        "NO_EQUIVALENTE", ["infra"], {"infra": ["INFRA ERROR_INTERNO boom"]})
    # Mayusculas y tildes: la comparacion es ordinal y el archivo se lee como UTF-8.
    mayus = con(base, ps=[("Compartido", 3, 0), ("ps_b", 2, 1)])
    par("el mismo grupo en otra capitalizacion", S(mayus), S(con(mayus, ps=[("compartido", 3, 0), ("ps_b", 2, 1)])),
        "NO_EQUIVALENTE", ["grupos-ps"], {"grupos-ps": ["Compartido (3)", "compartido (3)"]})
    tilde = con(base, ps=[("t%scnico" % _TILDE_E, 3, 0), ("ps_b", 2, 1)])
    par("un grupo con tilde, igual en los dos", S(tilde), S(tilde), "EQUIVALENTE")
    par("un grupo con tilde contra el mismo sin tilde", S(tilde), S(con(tilde, ps=[("tecnico", 3, 0), ("ps_b", 2, 1)])),
        "NO_EQUIVALENTE", ["grupos-ps"], {"grupos-ps": ["t%scnico (3)" % _TILDE_E, "tecnico (3)"]})
    return P


def test_vp_e17_el_comparador_con_pares_adulterados_a_mano_nombra_el_campo_que_difiere(t):
    """VP-E17 - el comparador, con pares adulterados a mano (sin correr ni el oraculo ni el runner), sale NO_EQUIVALENTE y nombra
    el campo en cada uno de: total distinto en 1; un grupo de mas; mismo numero de fallos con otro nombre; exit distinto; grupos
    permutados; una linea INFRA en el runner; sale NO_COMPARABLE con huellas distintas y con una fila MAL sin prefijo de detalle
    conocido; sale EQUIVALENTE con el par identico. En cada par se afirma el veredicto y se niegan los otros dos, y el conjunto
    EXACTO de campos que difieren (ni uno mas: un comparador que dijera `todo difiere` no pasa)."""
    ID = "VP-E17"
    carpeta = Path(tempfile.mkdtemp(prefix="t61_"))
    _CREADOS.append(carpeta)
    try:
        pares = _pares_e17()
        t.verdadero("%s control: hay pares de los tres veredictos" % ID, {p["v"] for p in pares} == set(VEREDICTOS))
        resultados = comparar_lote(carpeta / "lote", pares)
        # Control del lote: tres pares por un `powershell -File` aparte (el exit del proceso, no `$LASTEXITCODE`) dan lo mismo.
        elegidos = [i for i, p in enumerate(pares)
                    if p["id"] in ("el par identico", "total distinto en 1", "huellas distintas con el mismo texto")]
        reales = comparar_varios(carpeta / "reales", [dict(pares[i], nombre="r%d" % i) for i in elegidos])
        for i, real in zip(elegidos, reales):
            t.igual("%s control del lote [%s]: por -File el veredicto y el exit son los mismos" % (ID, pares[i]["id"]),
                    (resultados[i].veredicto, resultados[i].rc, resultados[i].campos), (real.veredicto, real.rc, real.campos))
        for p, v in zip(pares, resultados):
            etiqueta = "%s [%s]" % (ID, p["id"])
            rc = 0 if p["v"] == "EQUIVALENTE" else 1
            t.igual("%s el veredicto es %s" % (etiqueta, p["v"]), p["v"], v.veredicto)
            t.igual("%s el exit es %d" % (etiqueta, rc), rc, v.rc)
            for vecino in VEREDICTOS:
                if vecino != p["v"]:
                    t.verdadero("%s no dice %s" % (etiqueta, vecino), not v.dice(vecino))
            t.igual("%s los campos que difieren, exactos y en orden" % etiqueta, p["campos"], v.campos)
            for campo, textos in p["nombran"].items():
                for texto in textos:
                    t.contiene("%s la linea de %s nombra <%s>" % (etiqueta, campo, texto), texto, v.linea_de(campo))
            if p["v"] == "NO_COMPARABLE":
                t.verdadero("%s dice su motivo" % etiqueta, len(v.motivos) > 0)

                for texto in p["motivos"]:
                    t.contiene("%s un motivo nombra <%s>" % (etiqueta, texto), texto, "\n".join(v.motivos))
            else:
                t.vacio("%s sin motivos de no comparable" % etiqueta, v.motivos)
            for texto in p["en_salida"]:
                t.contiene("%s la salida dice <%s>" % (etiqueta, texto), texto, v.out)
            t.igual("%s stderr vacio" % etiqueta, "", v.err)
    except Exception as e:
        t.verdadero("%s los pares: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar(carpeta)


_PY_DERIVA = """
def test_filas(t):
    n = len(os.listdir(%r))
    for i in range(n):
        t.verdadero("fila-%%02d" %% (i + 1), True)
    _ev("FIN")
"""


def py_deriva(nombre, carpeta):
    """VP-E18: un .py cuyo conteo de filas es cuantos archivos hay en una carpeta EXTERNA al layout: la deriva de 30 y 33."""
    texto = _PY_EVENTOS.replace("@@SUITE@@", nombre) + _PY_DERIVA % str(carpeta)
    return {"nombre": nombre, "texto": texto, "motor": "py", "filas": 2, "rojas": 0, "grupo": nombre[:-len(".py")]}


def test_vp_e18_una_suite_que_deriva_entre_las_dos_corridas_es_no_equivalente_y_no_hay_tolerancia(t):
    """VP-E18 - una fixture cuyo conteo depende de cuantos archivos hay en una carpeta externa que el test cambia ENTRE la corrida
    del oraculo y la del runner: con la misma huella del layout, el comparador sale NO_EQUIVALENTE nombrando esa suite y los dos
    conteos; y el comparador no tiene ningun parametro que acepte una diferencia (sus parametros, por AST, son los cuatro de la
    spec; uno de tolerancia es un error de PowerShell, no un veredicto)."""
    ID = "VP-E18"
    suites = [ps_suite("ps_ok.ps1", 3), py_suite("py_ok.py", 2), py_suite("py_deriva.py", 2)]
    ly = Layout(suites, con_runner=True)
    ej = None
    try:
        ext = ly.tmp / "ext" / "deriva"
        ext.mkdir(parents=True)
        for i in (1, 2):
            (ext / ("a%d.txt" % i)).write_bytes(b"x")
        ly.suites[2] = py_deriva("py_deriva.py", ext)
        ly.crear()
        h0 = huella(ly)
        o = Corrida(ly, "e18o", ly.oraculo).correr()
        h1 = huella(ly)
        for i in (3, 4):
            (ext / ("b%d.txt" % i)).write_bytes(b"x")          # lo externo cambia; el layout no
        ej = correr_runner(ly, ly.rutas("e18r"), 3).esperar()
        h2 = huella(ly)
        t.igual("%s control: la huella del layout es la misma antes, entre las dos corridas y despues" % ID,
                (h0, h0), (h1, h2))
        t.igual("%s las dos corridas salen 0 (la deriva no pone nada rojo)" % ID, (0, 0), (o.rc, ej.rc))
        mo, mr = modelo_de(o.out), modelo_de(ej.out)
        t.igual("%s el oraculo vio 2 archivos y el runner 4 (la fixture los cuenta)" % ID,
                (("OK", "py_deriva", 2), ("OK", "py_deriva", 4)),
                (next((g for g in mo["py"] if g[1] == "py_deriva"), None), next((g for g in mr["py"] if g[1] == "py_deriva"), None)))
        t.igual("%s lo demas es igual: los grupos PowerShell y las otras suites Python" % ID,
                (mo["ps"], [g for g in mo["py"] if g[1] != "py_deriva"]),
                (mr["ps"], [g for g in mr["py"] if g[1] != "py_deriva"]))
        # El veredicto, la vecina (otra huella), tres parametros que pedirian aceptar la diferencia y los parametros por AST:
        # todo powershell aparte, a la vez.
        extras = (["-Tolerancia", "1"], ["-Ignorar", "py_deriva"], ["-Margen", "2"])
        pares = [{"serial": o.out, "paralelo": ej.out, "hs": h0, "hp": h2, "nombre": "par"},
                 {"serial": o.out, "paralelo": ej.out, "hs": h0, "hp": HUELLA_B, "nombre": "otra"}]
        pares += [{"serial": o.out, "paralelo": ej.out, "hs": h0, "hp": h2, "nombre": "x" + e[0][1:], "extra": e} for e in extras]
        (v, w, *con_extra), params = comparar_varios(
            ly.tmp / "cmp", pares, tambien=lambda: _parametros_de_script(RAIZ / "tests" / COMPARADOR, ly.tmp))
        t.igual("%s con la misma huella el comparador dice NO_EQUIVALENTE" % ID, "NO_EQUIVALENTE", v.veredicto)
        t.igual("%s y sale 1" % ID, 1, v.rc)
        t.verdadero("%s no dice EQUIVALENTE ni NO_COMPARABLE" % ID, not v.dice("EQUIVALENTE") and not v.dice("NO_COMPARABLE"))
        t.igual("%s los campos que difieren: el grupo de esa suite y las cuentas de Python y combinadas, ninguno mas" % ID,
                ["grupos-py", "ok-py", "total-py", "ok", "total"], v.campos)
        t.verdadero("%s la linea de grupos nombra esa suite y los dos conteos, 2 y 4" % ID,
                    "py_deriva (2)" in v.linea_de("grupos-py") and "py_deriva (4)" in v.linea_de("grupos-py"))
        t.verdadero("%s las cuentas dicen 4 -> 6 en Python y 7 -> 9 en total" % ID,
                    "serial=4" in v.linea_de("total-py") and "paralelo=6" in v.linea_de("total-py")
                    and "serial=7" in v.linea_de("total") and "paralelo=9" in v.linea_de("total"))
        # No hay parametro de tolerancia: los cuatro de la spec y ninguno mas.
        t.igual("%s los parametros del comparador son los cuatro de la spec, todos texto y ninguno switch" % ID,
                ["HuellaParalelo:String", "HuellaSerial:String", "Paralelo:String", "Serial:String"], params)
        # Un parametro que pidiera aceptar la diferencia no existe: PowerShell lo rechaza y no hay veredicto.
        for extra, x in zip(extras, con_extra):
            t.verdadero("%s %s es un error de parametros: sale distinto de 0 y no da ningun veredicto" % (ID, extra[0]),
                        x.rc != 0 and x.veredicto is None)
            t.verdadero("%s %s no vuelve equivalente el par" % (ID, extra[0]), not x.dice("EQUIVALENTE"))
        # La vecina: con las huellas distintas el mismo par es NO_COMPARABLE, nunca NO_EQUIVALENTE ni EQUIVALENTE.
        t.igual("%s control: con otra huella el mismo par es NO_COMPARABLE" % ID, ("NO_COMPARABLE", 1), (w.veredicto, w.rc))
        t.verdadero("%s y no dice NO_EQUIVALENTE" % ID, not w.dice("NO_EQUIVALENTE") and w.campos == [])
    except Exception as e:
        t.verdadero("%s el layout y sus corridas: %s: %s" % (ID, type(e).__name__, str(e)[:300]), False)
    finally:
        _borrar_layout(ly, *([ej] if ej else []))


# ---- El guardian del archivo ----------------------------------------------------------------------------------

def test_zz_el_archivo_no_deja_procesos_ni_carpetas_del_test(t):
    """El control del propio archivo, al final (el nombre ordena ultimo): ninguno de los <tmp> que creo este modulo sigue en
    disco y ningun proceso lleva su nombre en la linea de comandos."""
    tokens = [p.name for p in _CREADOS]
    restos = [str(p) for p in _CREADOS if p.exists()]
    t.igual("zz ninguna carpeta t61_* de este archivo sigue en disco", [], restos)
    vivos = [(p[0], p[3][:120]) for p in procesos() if any(k in p[3] for k in tokens)]
    t.igual("zz ningun proceso con el token de algun layout de este archivo sigue vivo", [], vivos)
