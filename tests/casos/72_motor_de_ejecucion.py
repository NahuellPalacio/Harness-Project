"""Los escenarios de docs/cambios/minimal-execution-engine/spec.md (Task 4), menos ME-E26, que
instala de verdad (72-motor-de-ejecucion-instalador.ps1), y ME-E50, que es una lectura. Cada
asercion nombra su ME-Enn.

El Host es un proceso externo, tests/fixtures/host_falso.py, que el motor encuentra por
`ejecucion.comandoHost` de harness.config.json, como encontraria a `claude`: no hay monkeypatch del
motor. Lo que cambia entre la creacion y la entrega lo hace el punto de encuentro
`antes_de_entregar`; la ventana de la carrera de EX-F01, `antes_de_reservar`, en dos procesos del
sistema operativo.

🔴 Ningun test lanza el Claude Code real: todo proyecto de prueba declara el Host falso, y los que
miran el default de `comandoHost` ponen un `claude` falso primero en el PATH.
"""
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import _thread
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CASOS = RAIZ / "tests" / "casos"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
EJECUCION = BIN / "ejecucion"
HOST = RAIZ / "tests" / "fixtures" / "host_falso.py"
CLI = BIN / "dev-harness.py"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M64 = _cargar("modelo_para_72", CASOS / "64_modelo_de_dominio.py")

from contexto import limpieza                            # noqa: E402
from ejecucion import admision                           # noqa: E402
from ejecucion import contrato as C                      # noqa: E402
from ejecucion import evidencia                          # noqa: E402
from ejecucion import host_claude_code as H              # noqa: E402
from ejecucion import motor                              # noqa: E402
from ejecucion import proceso                            # noqa: E402
from ejecucion import registro                           # noqa: E402

CLAVE = "GCBA-72"
PIDE = "Persona de prueba"
# Armado en dos partes para que ningun archivo de la fabrica lleve un secreto entero.
SECRETO = "ghp_" + "Z9y8X7w6V5u4T3s2R1q0P9o8N7m6L5k4J3i2"
# El marcador de la redaccion deja ver los primeros 12 caracteres del secreto: 13 ya es una fuga, y es
# lo que queda de un secreto partido por un recorte hecho antes de redactar.
FUGA = SECRETO[:13]
UNIDADES = [M64._unidad("analizar-api"),
            M64._unidad("implementar-endpoint", capacidades=("repository.write",),
                        dependencias=("analizar-api",))]


# -- el proyecto de prueba -------------------------------------------------------------------

_PLANTILLA = []


def _git(carpeta, *args):
    return subprocess.run(["git", "-C", str(carpeta), "-c", "user.email=t@t", "-c", "user.name=t",
                           "-c", "core.autocrlf=false"] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _plantilla():
    """Un repositorio con dos archivos versionados, `.claude/` ignorado como en un proyecto
    instalado, y `origin` en la URL que nombra la Ficha: el checkout es el de la tarea."""
    if not _PLANTILLA:
        base = M64._tmp("me72-git-")
        M64._escribir(base / ".gitignore", ".claude/\nprop-*.json\n")
        M64._escribir(base / "src" / "app.py", "VALOR = 1\n")
        M64._escribir(base / "src" / "viejo.py", "VIEJO = 1\n")
        for args in (["init", "-q"], ["config", "core.autocrlf", "false"], ["add", "-A"],
                     ["commit", "-q", "-m", "inicial"],
                     ["remote", "add", "origin", M64.URL_DEL_REPO + ".git"]):
            _git(base, *args)
        _PLANTILLA.append(base)
    return _PLANTILLA[0]


def _config(proy, ejecucion=None, **extra):
    """harness.config.json con el Host falso como comando, salvo que `ejecucion` diga otra cosa."""
    doc = {"ejecucion": {"comandoHost": [sys.executable, str(HOST)], "limiteSegundos": 60}}
    if ejecucion is not None:
        doc["ejecucion"] = ejecucion
    doc.update(extra)
    M64._json(Path(proy) / ".claude" / "harness.config.json", doc)


def _proyecto(unidades=None, dominios=("backend",), agentes=("dev-backend",), config=True,
              registro_=None):
    """Un proyecto con un plan 2.1 READY_FOR_EXECUTION y la tarea en EXECUTION, que puede delegar."""
    proy = M64._tmp("me72-")
    shutil.copytree(str(_plantilla()), str(proy), dirs_exist_ok=True)
    M64._json(proy / ".claude" / "contextos" / (CLAVE + ".json"), M64._contexto(CLAVE, True))
    M64._json(proy / ".claude" / "harness.capacidades.json",
              {"capacidades": registro_ or M64.REGISTRO})
    M64._json(proy / "prop-1.json", M64._propuesta(unidades or UNIDADES, dominios=dominios))
    if config:
        _config(proy)
    (proy / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    for agente in agentes:
        shutil.copy(str(RAIZ / "harnesses" / "desarrollo" / "agents" / (agente + ".md")),
                    str(proy / ".claude" / "agents"))
    codigo, _, error = M64._cli(["plan", CLAVE, "--proyecto", proy, "--propuesta",
                                 proy / "prop-1.json"])
    if codigo != 0:
        raise AssertionError("plan --propuesta salio %s: %s" % (codigo, error[-400:]))
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    if plan["status"] != "READY_FOR_EXECUTION":
        raise AssertionError("el plan de prueba no quedo listo: %s" % plan["status"])
    return proy


def _guion(proy, nombre="guion", **guion):
    """El guion del Host falso, en un archivo fuera del proyecto. Lo lee de HOST_FALSO_GUION."""
    ruta = Path(proy).parent / ("%s.%s.json" % (Path(proy).name, nombre))
    ruta.write_text(json.dumps(guion, ensure_ascii=False), encoding="utf-8")
    os.environ["HOST_FALSO_GUION"] = str(ruta)
    return ruta


def _eco(proy, nombre="eco"):
    return Path(proy).parent / ("%s.%s.json" % (Path(proy).name, nombre))


def _leer_eco(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8")) if Path(ruta).is_file() else None


def _informe(estado="COMPLETE", artifact="# Informe\n"):
    return {"structured_output": {"declaredStatus": estado, "artifact": artifact}}


def _corrida(proy, unidad="analizar-api", pedido_por=PIDE, **kw):
    """{res, err, exc}: lo que devolvio el motor, o la excepcion, que el escenario mira."""
    try:
        res, err = motor.ejecutar(str(proy), CLAVE, unidad, pedido_por, **kw)
        return {"res": res, "err": err, "exc": None}
    except Exception as e:                       # noqa: BLE001 - la excepcion se mira
        return {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}


def _de(corrida, campo):
    return (corrida["res"] or {}).get(campo)


def _codigo(corrida):
    if corrida["err"]:
        return corrida["err"]["code"]
    return ((corrida["res"] or {}).get("error") or {}).get("code")


def _ejecuciones(proy):
    return Path(proy) / ".claude" / "ejecuciones"


def _carpeta(proy, execution_id):
    return _ejecuciones(proy) / CLAVE / execution_id


def _arbol(proy):
    """{ruta: sha256} de lo que hay bajo .claude/ejecuciones/. `vivo.lock` es un archivo vacio que
    nadie lee, y en Windows su candado es obligatorio: con el motor vivo no se puede leer. Se anota
    que existe y su tamano."""
    raiz = _ejecuciones(proy)
    salida = {}
    if not raiz.exists():
        return salida
    for p in sorted(raiz.rglob("*")):
        rel = p.relative_to(raiz).as_posix()
        if p.is_dir():
            salida[rel + "/"] = "dir"
        elif p.name == registro.VIVO:
            salida[rel] = "candado de %d bytes" % p.stat().st_size
        else:
            salida[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return salida


def _llave(proy, unidad):
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    return C.clave_de_idempotencia(CLAVE, C.huella(plan), unidad)


def _turnos(proy, unidad):
    return [(n, registro.leer_turno(r)[0]) for n, r in
            registro.turnos(str(proy), CLAVE, _llave(proy, unidad))]


def _carpetas(proy):
    return registro.carpetas(str(proy), CLAVE)


def _temporales(proy):
    return [p.relative_to(proy).as_posix() for p in _ejecuciones(proy).rglob("*")
            if p.is_file() and registro.es(registro.TEMPORAL, p.name)]


def _viejo(*rutas):
    """Le pone a cada ruta una fecha de hace veinte minutos: pasa el umbral del barrido."""
    hace = time.time() - 1200
    for ruta in rutas:
        os.utime(str(ruta), (hace, hace))


def _sha(ruta):
    return "sha256:" + hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


# -- procesos: el motor en otro proceso del sistema operativo --------------------------------

HIJO = r'''
import json, os, sys, time
bin_dir, proyecto, clave, unidad, modo, marca = sys.argv[1:7]
sys.path.insert(0, bin_dir)
from ejecucion import motor

def encuentro():
    open(marca + ".leyo." + str(os.getpid()), "w").close()
    fin = time.time() + 60
    while time.time() < fin and len([n for n in os.listdir(os.path.dirname(marca))
                                     if n.startswith(os.path.basename(marca) + ".leyo.")]) < 2:
        time.sleep(0.02)

def colgar(carpeta):
    with open(marca + ".colgado", "w") as f:
        f.write(carpeta)
    time.sleep(300)

kw = {}
if modo == "encuentro":
    kw["antes_de_reservar"] = encuentro
if modo == "colgar":
    kw["antes_de_entregar"] = colgar
try:
    res, err = motor.ejecutar(proyecto, clave, unidad, "Persona de prueba", **kw)
    salida = {"res": res, "err": err, "exc": None}
except Exception as e:
    salida = {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}
sys.stdout.write(json.dumps(salida))
'''


def _script_hijo():
    ruta = Path(tempfile.gettempdir()) / ("me72-hijo-%d.py" % os.getpid())
    if not ruta.is_file():
        ruta.write_text(HIJO, encoding="utf-8")
    return ruta


def _lanzar_motor(proy, unidad, modo="normal", marca=None, guion=None):
    """El motor en un proceso aparte, con la API: (proceso, marca)."""
    marca = marca or str(Path(proy).parent / ("%s.marca-%s" % (Path(proy).name, unidad)))
    entorno = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    if guion is not None:
        entorno["HOST_FALSO_GUION"] = str(guion)
    hijo = subprocess.Popen([sys.executable, str(_script_hijo()), str(BIN), str(proy), CLAVE,
                             unidad, modo, marca], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=entorno)
    return hijo, marca


def _salida_del_hijo(hijo, limite=120):
    salida, error = hijo.communicate(timeout=limite)
    try:
        return json.loads(salida.decode("utf-8"))
    except ValueError:
        return {"res": None, "err": None, "exc": "sin salida: " + error.decode("utf-8", "replace")[-300:]}


def _esperar(condicion, limite=60):
    fin = time.time() + limite
    while time.time() < fin:
        if condicion():
            return True
        time.sleep(0.1)
    return False


def _matar(pid):
    """Termina un proceso a la fuerza, sin su arbol: el motor muere y el Host puede seguir."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    else:
        os.kill(pid, 9)


def _corriendo(proy):
    """La carpeta de la Execution que ya esta RUNNING, con el pid del Host, o None."""
    for carpeta in _ejecuciones(proy).glob(CLAVE + "/exe_*"):
        if (carpeta / registro.ENTREGA).is_file() and (carpeta / registro.PROCESO).is_file():
            return carpeta
    return None


def _huerfana(proy, unidad, cambios=None, dormir=60):
    """Una RUNNING cuyo motor murio a la fuerza, y el Host que le sobrevivio: (carpeta, pid)."""
    return _huerfanas(proy, [(unidad, cambios)], dormir)[unidad]


def _huerfanas(proy, unidades, dormir=60):
    """Varias RUNNING a la vez, y despues sus motores muertos a la fuerza: {unidad: (carpeta, pid)}.
    A la vez porque cada `ejecutar` recupera primero: una segunda corrida cerraria la huerfana de
    la primera."""
    hijos = {}
    for unidad, cambios in unidades:
        guion = _guion(proy, "guion-" + unidad, dormir=dormir, cambios=cambios or [],
                       eco=str(_eco(proy, "eco-" + unidad)))
        hijos[unidad] = _lanzar_motor(proy, unidad, guion=guion)[0]
    salida = {}
    for unidad, hijo in hijos.items():
        carpeta = None
        if _esperar(lambda: _corriendo_de(proy, unidad) is not None
                    and _leer_eco(_eco(proy, "eco-" + unidad)) is not None):
            carpeta = _corriendo_de(proy, unidad)
        salida[unidad] = carpeta
    for unidad, hijo in hijos.items():
        _matar(hijo.pid)
        hijo.communicate(timeout=60)
    return dict((u, (salida[u], (_leer_eco(_eco(proy, "eco-" + u)) or {}).get("pid")))
                for u in hijos)


def _corriendo_de(proy, unidad):
    llave = _llave(proy, unidad)
    for carpeta in _ejecuciones(proy).glob(CLAVE + "/exe_*"):
        req = M64._leer_json(carpeta / registro.REQUEST) if (carpeta / registro.REQUEST).is_file() \
            else {}
        if req.get("idempotencyKey") == llave and (carpeta / registro.ENTREGA).is_file() \
                and (carpeta / registro.PROCESO).is_file():
            return carpeta
    return None


def _terminar(pid):
    if pid and proceso.pid_vivo(pid):
        _matar(pid)


# =============================================================================================
# Persistencia: la escritura de una sola vez, los ids, los turnos y el barrido
# =============================================================================================

def test_me_e21_escribir_una_vez(t):
    """ME-E21 — Escribir otra vez un archivo del registro falla sin cambiar un byte y sin dejar
    temporales; una falla a mitad de escritura no deja ni el destino ni el temporal."""
    proy = _proyecto()
    _guion(proy)
    corrida = _corrida(proy)
    eid = _de(corrida, "executionId")
    carpeta = _carpeta(proy, eid or "exe_" + "0" * 32)
    for nombre in (registro.REQUEST, registro.ENTREGA, registro.RESULT, registro.OUTPUT,
                   H.PROMPT_DE_SISTEMA):
        ruta = carpeta / nombre
        antes = M64._bytes(ruta)
        levanto = None
        try:
            registro.escribir_una_vez(str(ruta), b'{"otro": true}\n')
        except FileExistsError:
            levanto = "FileExistsError"
        t.igual("ME-E21 escribir otra vez %s falla" % nombre, "FileExistsError", levanto)
        t.igual("ME-E21 y %s no cambia un byte" % nombre, antes, M64._bytes(ruta))
    turno = registro.ruta_del_turno(str(proy), CLAVE, _llave(proy, "analizar-api"), 1)
    antes = M64._bytes(turno)
    t.verdadero("ME-E21 reservar otra vez el turno 1 falla",
                registro.reservar(str(proy), CLAVE, _llave(proy, "analizar-api"), 1,
                                  "exe_" + "f" * 32) is False)
    t.igual("ME-E21 y el turno no cambia", antes, M64._bytes(turno))
    t.vacio("ME-E21 no quedan temporales", _temporales(proy))

    destino = carpeta.parent / "a-medias.json"
    original = os.fsync

    def _corta(_):
        raise OSError("disco lleno a mitad de la escritura")

    os.fsync = _corta
    try:
        registro.escribir_una_vez(str(destino), b"{}")
    except OSError:
        pass
    finally:
        os.fsync = original
    t.verdadero("ME-E21 una falla a mitad de escritura no deja el destino", not destino.exists())
    t.vacio("ME-E21 ni el temporal", _temporales(proy))


def test_me_e22_un_resultado_tardio_no_pisa(t):
    """ME-E22 — Un resultado tardio, despues de que otro ya escribio result.json, no lo pisa."""
    proy = _proyecto()
    _guion(proy)
    corrida = _corrida(proy)
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    carpeta = _carpeta(proy, eid)
    ruta = carpeta / registro.RESULT
    antes = M64._bytes(ruta)
    request = M64._leer_json(carpeta / registro.REQUEST) if (carpeta / registro.REQUEST).is_file() \
        else {}
    tardio = dict(json.loads(antes.decode("utf-8")) if antes else {}, status="FAILED",
                  agentDeclaredStatus=None, output=None,
                  error={"code": "HOST_INTERRUPTED", "detail": "un resultado tardio"})
    t.vacio("ME-E22 el resultado tardio es valido por si mismo", C.validar_resultado(tardio, request))
    try:
        quedo = motor._escribir_resultado(str(carpeta), tardio, request)
    except Exception as e:                       # noqa: BLE001
        quedo = {"exc": str(e)}
    t.igual("ME-E22 el motor devuelve el primero", "SUCCEEDED", (quedo or {}).get("status"))
    t.igual("ME-E22 result.json no cambio", antes, M64._bytes(ruta))
    t.igual("ME-E22 y sigue SUCCEEDED", "SUCCEEDED",
            registro.estado(str(proy), CLAVE, eid)["estado"])


def test_me_e36_los_ids_que_se_vuelven_rutas(t):
    """ME-E36 — Los executionId cumplen ^exe_[0-9a-f]{32}$ con fullmatch y no se repiten en 10 000;
    un id, una TaskKey o una clave con un \\n final no se usan como ruta."""
    ids = [registro.nuevo_id() for _ in range(10000)]
    t.vacio("ME-E36 todos cumplen el patron con fullmatch",
            [i for i in ids if not re.fullmatch(r"exe_[0-9a-f]{32}", i)][:3])
    t.igual("ME-E36 ninguno se repite en 10 000", 10000, len(set(ids)))
    proy = M64._tmp("me72-ids-")
    malos = {"el executionId": lambda: registro.carpeta_de(str(proy), CLAVE, "exe_" + "a" * 32 + "\n"),
             "la TaskKey": lambda: registro.carpeta_de_tarea(str(proy), CLAVE + "\n"),
             "la idempotencyKey": lambda: registro.carpeta_de_clave(str(proy), CLAVE,
                                                                     "sha256:" + "b" * 64 + "\n")}
    for que, armar in malos.items():
        try:
            armar()
            levanto = False
        except registro.RegistroInvalido:
            levanto = True
        t.verdadero("ME-E36 %s con \\n final no se usa como ruta" % que, levanto)
    res, err = motor.ejecutar(str(proy), CLAVE + "\n", "analizar-api", PIDE,
                              config={"comando": [sys.executable, str(HOST)], "limite": 5,
                                      "perfiles": {}, "usuario": ""})
    t.igual("ME-E36 ejecutar con una TaskKey con \\n final es CONTRACT_INVALID", "CONTRACT_INVALID",
            (err or {}).get("code"))
    t.verdadero("ME-E36 y no escribe nada", not _ejecuciones(proy).exists())
    try:
        motor.cancelar(str(proy), CLAVE, "exe_" + "a" * 32 + "\n", PIDE)
        levanto = False
    except motor.ErrorDelComando:
        levanto = True
    t.verdadero("ME-E36 cancelar un executionId con \\n final es un error del comando", levanto)


def _residuo(proy, unidad="analizar-api", con_turno=False):
    """Una carpeta como la que deja un motor muerto entre crear la carpeta y publicar: vivo.lock
    libre, un request.json completo y valido, y un temporal de escritura. Con `con_turno`, un turno
    la nombra: es una REQUESTED real."""
    catalogo = limpieza.cargar_catalogo()
    request, error, _, _ = admision.al_pedir(str(proy), CLAVE, unidad, PIDE, catalogo)
    if error is not None:
        raise AssertionError("la admision del residuo fallo: %s" % error)
    carpeta = Path(registro.carpeta_de(str(proy), CLAVE, request["executionId"]))
    carpeta.mkdir(parents=True)
    (carpeta / registro.VIVO).write_bytes(b"")
    registro.escribir_json(str(carpeta / registro.REQUEST), request)
    temporal = carpeta / (".request.json.k3j2h1.tmp")
    temporal.write_text("{a medias", encoding="utf-8")
    if con_turno:
        os.makedirs(registro.carpeta_de_clave(str(proy), CLAVE, request["idempotencyKey"]),
                    exist_ok=True)
        registro.reservar(str(proy), CLAVE, request["idempotencyKey"], 1, request["executionId"])
    return carpeta, request


def test_me_e37_el_barrido_es_seguro(t):
    """ME-E37 — Una carpeta sin turno con el candado tomado no se barre aunque tenga mas de 10
    minutos; una con el candado libre y menos de 10 minutos tampoco."""
    proy = _proyecto()
    tomada, _ = _residuo(proy, "analizar-api")
    (tomada / registro.VIVO).unlink()
    vida = registro.Vida(str(tomada))
    try:
        _viejo(tomada / registro.VIVO, tomada)
        t.verdadero("ME-E37 el candado de la admision en curso esta tomado",
                    registro.candado_libre(str(tomada)) is False)
        motor.recuperar(str(proy), CLAVE)
        t.verdadero("ME-E37 con el candado tomado no se barre, aunque tenga mas de 10 minutos",
                    tomada.is_dir() and (tomada / registro.REQUEST).is_file())
    finally:
        vida.soltar()
    nueva, _ = _residuo(proy, "analizar-api")
    t.verdadero("ME-E37 el candado de la nueva esta libre", registro.candado_libre(str(nueva)) is True)
    motor.recuperar(str(proy), CLAVE)
    t.verdadero("ME-E37 con el candado libre y menos de 10 minutos no se barre", nueva.is_dir())
    _viejo(nueva / registro.VIVO, nueva)
    motor.recuperar(str(proy), CLAVE)
    t.verdadero("ME-E37 con el candado libre y mas de 10 minutos, si", not nueva.exists())


def test_me_e52_un_corte_antes_de_publicar(t):
    """ME-E52 — Una carpeta con vivo.lock, request.json valido, un temporal y ningun turno, con el
    candado libre: no aparece en --estado, no bloquea una admision nueva de la misma clave, y la
    recuperacion la borra entera pasados los 10 minutos. Con turno es una REQUESTED real: bloquea y
    no se borra."""
    proy = _proyecto()
    carpeta, request = _residuo(proy, "analizar-api")
    t.vacio("ME-E52 el request del residuo valida", C.validar_request(request))
    filas = motor.estado(str(proy), CLAVE)
    t.vacio("ME-E52 el residuo no aparece en --estado",
            [f for f in filas if f["executionId"] == request["executionId"]])
    t.verdadero("ME-E52 ni cuenta como REQUESTED: la clave no tiene turnos",
                registro.ultimo_turno(str(proy), CLAVE, request["idempotencyKey"]) is None)
    _guion(proy)
    corrida = _corrida(proy, "analizar-api")
    t.igual("ME-E52 una admision nueva de la misma clave pasa los duplicados y termina",
            "SUCCEEDED", _de(corrida, "status"))
    t.igual("ME-E52 y crea el turno 1, que la nombra a ella",
            [(1, _de(corrida, "executionId"))], _turnos(proy, "analizar-api"))
    t.verdadero("ME-E52 antes de los 10 minutos el residuo sigue", carpeta.is_dir())
    _viejo(carpeta / registro.VIVO, carpeta)
    motor.recuperar(str(proy), CLAVE)
    t.verdadero("ME-E52 pasados los 10 minutos la recuperacion lo borra entero, temporal incluido",
                not carpeta.exists())

    otro = _proyecto()
    real, req_real = _residuo(otro, "analizar-api", con_turno=True)
    _viejo(real / registro.VIVO, real)
    _guion(otro)
    corrida = _corrida(otro, "analizar-api")
    t.igual("ME-E52 una REQUESTED real con turno bloquea la clave", "DUPLICATE_EXECUTION",
            _codigo(corrida))
    motor.recuperar(str(otro), CLAVE)
    t.verdadero("ME-E52 y la recuperacion no la borra", (real / registro.REQUEST).is_file())
    t.igual("ME-E52 sigue REQUESTED", "REQUESTED",
            registro.estado(str(otro), CLAVE, req_real["executionId"])["estado"])


def test_me_e18_ex_f01_dos_procesos_la_misma_clave(t):
    """ME-E18 — EX-F01: dos procesos del sistema operativo admiten la misma clave con un punto de
    encuentro entre la lectura del ultimo turno y la reserva. Queda una Execution, un
    DUPLICATE_EXECUTION, un turno, una carpeta y ningun temporal. Veinte veces sin punto de
    encuentro, lo mismo."""
    proy = _proyecto()
    guion = _guion(proy)
    marca = str(Path(proy).parent / ("%s.encuentro" % Path(proy).name))
    hijos = [_lanzar_motor(proy, "analizar-api", "encuentro", marca, guion)[0] for _ in range(2)]
    salidas = [_salida_del_hijo(h) for h in hijos]
    t.vacio("ME-E18 ningun proceso levanto", [s["exc"] for s in salidas if s["exc"]])
    t.igual("ME-E18 los dos leyeron antes de reservar", 2,
            len([n for n in os.listdir(os.path.dirname(marca))
                 if n.startswith(os.path.basename(marca) + ".leyo.")]))
    t.igual("ME-E18 exactamente una Execution", 1, len([s for s in salidas if s["res"]]))
    t.igual("ME-E18 exactamente un DUPLICATE_EXECUTION", ["DUPLICATE_EXECUTION"],
            [s["err"]["code"] for s in salidas if s["err"]])
    t.igual("ME-E18 un solo turno", 1, len(_turnos(proy, "analizar-api")))
    t.igual("ME-E18 una sola carpeta", 1, len(_carpetas(proy)))
    t.vacio("ME-E18 ningun temporal", _temporales(proy))

    unidades = [M64._unidad("carrera-%02d" % i) for i in range(20)]
    proy = _proyecto(unidades)
    guion = _guion(proy)
    malas = []
    for tanda in range(0, 20, 5):
        lanzados = []
        for i in range(tanda, tanda + 5):
            uid = "carrera-%02d" % i
            lanzados.append((uid, [_lanzar_motor(proy, uid, "normal", None, guion)[0]
                                   for _ in range(2)]))
        for uid, hijos in lanzados:
            salidas = [_salida_del_hijo(h) for h in hijos]
            exitos = len([s for s in salidas if s["res"]])
            duplicados = [s["err"]["code"] for s in salidas if s["err"]]
            turnos = _turnos(proy, uid)
            if exitos != 1 or duplicados != ["DUPLICATE_EXECUTION"] or len(turnos) != 1 \
                    or any(s["exc"] for s in salidas):
                malas.append("%s: %d Execution(s), %s, %d turno(s)" % (uid, exitos, duplicados,
                                                                    len(turnos)))
    t.vacio("ME-E18 veinte carreras sin punto de encuentro: una Execution, un duplicado y un "
            "turno cada vez", malas)
    t.igual("ME-E18 una carpeta por carrera", 20, len(_carpetas(proy)))
    t.vacio("ME-E18 ningun temporal en las veinte", _temporales(proy))


def _otra_abierta(proy, request):
    """Arma a mano una Execution REQUESTED de la misma clave, con otro executionId, y su turno
    siguiente: un registro editado a mano, el unico caso en que el ultimo turno nombra a otra."""
    otro = dict(copy.deepcopy(request), executionId="exe_" + "e" * 32)
    carpeta = Path(registro.carpeta_de(str(proy), CLAVE, otro["executionId"]))
    carpeta.mkdir(parents=True)
    (carpeta / registro.VIVO).write_bytes(b"")
    registro.escribir_json(str(carpeta / registro.REQUEST), otro)
    numero = registro.turnos(str(proy), CLAVE, request["idempotencyKey"])[-1][0] + 1
    registro.reservar(str(proy), CLAVE, request["idempotencyKey"], numero, otro["executionId"])
    return otro


def test_me_e19_ex_f02_no_es_duplicado_de_si_misma(t):
    """ME-E19 — EX-F02: una Execution REQUESTED pasa la condicion 15 al entregar y llega a RUNNING;
    si el ultimo turno de su clave nombra a otra abierta, termina REJECTED con DUPLICATE_EXECUTION."""
    proy = _proyecto()
    _guion(proy)
    vistos = {}

    def mirar(carpeta):
        vistos["estado"] = registro.estado(str(proy), CLAVE, Path(carpeta).name)["estado"]

    corrida = _corrida(proy, "analizar-api", antes_de_entregar=mirar)
    t.igual("ME-E19 antes de entregar estaba REQUESTED", "REQUESTED", vistos.get("estado"))
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    t.verdadero("ME-E19 paso la condicion 15 y llego a RUNNING: hay entrega.json",
                (_carpeta(proy, eid) / registro.ENTREGA).is_file())
    t.igual("ME-E19 y termino SUCCEEDED", "SUCCEEDED", _de(corrida, "status"))

    def otra(carpeta):
        request = M64._leer_json(Path(carpeta) / registro.REQUEST)
        _otra_abierta(proy, request)

    corrida = _corrida(proy, "implementar-endpoint", antes_de_entregar=otra)
    t.igual("ME-E19 con el ultimo turno de otra abierta: REJECTED", "REJECTED",
            _de(corrida, "status"))
    t.igual("ME-E19 con DUPLICATE_EXECUTION", "DUPLICATE_EXECUTION", _codigo(corrida))
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    t.verdadero("ME-E19 y sin entrega.json", not (_carpeta(proy, eid) / registro.ENTREGA).exists())


# =============================================================================================
# El camino feliz y el AgentReport
# =============================================================================================

def test_me_e01_camino_feliz(t):
    """ME-E01 — Un plan 2.1 listo y un Host que devuelve structured_output COMPLETE: turno 1,
    request valida, entrega.json, output.md y un result.json SUCCEEDED valido, con output de la huella
    de los bytes de output.md, host.sessionRef igual al --session-id y requestFingerprint igual a la
    huella del request.json en disco. Sale con 0."""
    proy = _proyecto()
    eco = _eco(proy)
    _guion(proy, eco=str(eco), **{"resultado": _informe(
        "COMPLETE", "# Informe\r\nEl token que encontre: " + SECRETO + "\r\n")})
    codigo, salida, error = M64._cli(["ejecutar", CLAVE, "--unidad", "analizar-api",
                                      "--pedido-por", "Persona " + SECRETO, "--proyecto", proy,
                                      "--json"])
    t.igual("ME-E01 sale con 0", 0, codigo)
    try:
        res = json.loads(salida)
    except ValueError:
        res = {}
    eid = res.get("executionId") or "exe_" + "0" * 32
    carpeta = _carpeta(proy, eid)
    t.igual("ME-E01 un turno 1 que la nombra", [(1, eid)], _turnos(proy, "analizar-api"))
    request = M64._leer_json(carpeta / registro.REQUEST) if (carpeta / registro.REQUEST).is_file() \
        else None
    t.vacio("ME-E01 la request pasa validar_request", C.validar_request(request))
    t.verdadero("ME-E01 hay entrega.json", (carpeta / registro.ENTREGA).is_file())
    t.verdadero("ME-E01 hay output.md", (carpeta / registro.OUTPUT).is_file())
    en_disco = M64._leer_json(carpeta / registro.RESULT) if (carpeta / registro.RESULT).is_file() \
        else None
    t.igual("ME-E01 el resultado de stdout es el de result.json", en_disco, res)
    t.vacio("ME-E01 result.json pasa validar_resultado", C.validar_resultado(en_disco, request))
    t.igual("ME-E01 SUCCEEDED", "SUCCEEDED", res.get("status"))
    t.verdadero("ME-E01 con startedAt y endedAt", res.get("startedAt") and res.get("endedAt"))
    t.igual("ME-E01 agentDeclaredStatus COMPLETE", "COMPLETE", res.get("agentDeclaredStatus"))
    t.igual("ME-E01 output.fingerprint es la huella de los bytes de output.md",
            _sha(carpeta / registro.OUTPUT) if (carpeta / registro.OUTPUT).is_file() else "",
            (res.get("output") or {}).get("fingerprint"))
    argv = (_leer_eco(eco) or {}).get("argv") or []
    sesion = argv[argv.index("--session-id") + 1] if "--session-id" in argv[:-1] else None
    t.verdadero("ME-E01 el Host recibio un --session-id", sesion)
    t.igual("ME-E01 host.sessionRef es el --session-id que recibio el Host", sesion,
            (res.get("host") or {}).get("sessionRef"))
    t.igual("ME-E01 requestFingerprint es la huella del request.json en disco",
            C.huella(request), res.get("requestFingerprint"))


def _unidades(*ids, **kw):
    return [M64._unidad(i, **kw) for i in ids]


def test_me_e02_el_agente_declara_que_no_termino(t):
    """ME-E02 — PARTIAL, BLOCKED o FAILED dan FAILED con AGENT_DECLARED_NOT_COMPLETE, con
    agentDeclaredStatus y output."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    for unidad, declarado in (("uno", "PARTIAL"), ("dos", "BLOCKED"), ("tres", "FAILED")):
        _guion(proy, resultado=_informe(declarado, "# %s\n" % declarado))
        corrida = _corrida(proy, unidad)
        t.verdadero("ME-E02 %s: el motor no levanta" % declarado, corrida["exc"] is None)
        t.igual("ME-E02 %s da FAILED" % declarado, "FAILED", _de(corrida, "status"))
        t.igual("ME-E02 %s con AGENT_DECLARED_NOT_COMPLETE" % declarado,
                "AGENT_DECLARED_NOT_COMPLETE", _codigo(corrida))
        t.igual("ME-E02 %s con agentDeclaredStatus" % declarado, declarado,
                _de(corrida, "agentDeclaredStatus"))
        salida = _de(corrida, "output") or {}
        t.verdadero("ME-E02 %s con output" % declarado,
                    salida.get("path") and (proy / salida["path"]).is_file())


def test_me_e03_sin_un_agentreport_valido(t):
    """ME-E03 — Sin structured_output, con error_max_structured_output_retries, con una clave de
    mas o con un declaredStatus fuera del enum: FAILED con OUTPUT_INVALID, sin agentDeclaredStatus
    ni output."""
    proy = _proyecto(_unidades("uno", "dos", "tres", "cuatro"))
    casos = (("uno", "sin structured_output", {"structured_output": None}),
             ("dos", "error_max_structured_output_retries",
              {"subtype": "error_max_structured_output_retries", "is_error": True,
               "structured_output": None}),
             ("tres", "una clave de mas",
              {"structured_output": {"declaredStatus": "COMPLETE", "artifact": "x", "extra": 1}}),
             ("cuatro", "un declaredStatus fuera del enum",
              {"structured_output": {"declaredStatus": "DONE", "artifact": "x"}}))
    for unidad, que, resultado in casos:
        _guion(proy, resultado=resultado)
        corrida = _corrida(proy, unidad)
        t.igual("ME-E03 %s da FAILED" % que, "FAILED", _de(corrida, "status"))
        t.igual("ME-E03 %s da OUTPUT_INVALID" % que, "OUTPUT_INVALID", _codigo(corrida))
        t.verdadero("ME-E03 %s: sin agentDeclaredStatus ni output" % que,
                    corrida["res"] is not None and _de(corrida, "agentDeclaredStatus") is None
                    and _de(corrida, "output") is None)
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        t.verdadero("ME-E03 %s: no hay output.md" % que,
                    not (_carpeta(proy, eid) / registro.OUTPUT).exists())


def _lee_result(ruta):
    """Las lecturas del campo `result` de un JSON: `x["result"]` o `x.get("result")`. La de
    `ruteo`, la respuesta de `registro_agentes.resolver_ruteo`, es del AgentRegistry y no del Host."""
    salida = []
    for n in ast.walk(ast.parse(Path(ruta).read_text(encoding="utf-8"))):
        if isinstance(n, ast.Subscript):
            clave = n.slice.value if isinstance(n.slice, ast.Constant) else None
            if clave == "result" and not (isinstance(n.value, ast.Name) and n.value.id == "ruteo"):
                salida.append("%s:%d [\"result\"]" % (Path(ruta).name, n.lineno))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in
                ("get", "pop") and n.args and isinstance(n.args[0], ast.Constant)
                and n.args[0].value == "result"
                and not (isinstance(n.func.value, ast.Name) and n.func.value.id == "ruteo")):
            salida.append("%s:%d .%s(\"result\")" % (Path(ruta).name, n.lineno, n.func.attr))
    return salida


def _usos_del_artifact(ruta):
    """Lo que se hace con el texto del artifact fuera de copiarlo y redactarlo: un `in`, un metodo
    de texto, una expresion regular. El artifact es opaco."""
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    padres = {}
    for n in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(n):
            padres[id(hijo)] = n
    malos = []
    for n in ast.walk(arbol):
        es_artifact = (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                       and n.slice.value == "artifact") or (isinstance(n, ast.Name)
                                                             and n.id == "artifact")
        if not es_artifact or isinstance(getattr(n, "ctx", None), ast.Store):
            continue
        padre = padres.get(id(n))
        if isinstance(padre, ast.Compare) or (isinstance(padre, ast.Attribute)):
            malos.append("%s:%d" % (Path(ruta).name, n.lineno))
        if isinstance(padre, ast.Call) and getattr(padre.func, "attr", "") in (
                "search", "match", "findall", "fullmatch", "find", "split", "startswith"):
            malos.append("%s:%d %s" % (Path(ruta).name, n.lineno, padre.func.attr))
    return malos


def test_me_e29_nadie_interpreta_texto(t):
    """ME-E29 — Un Host que devuelve result "agentResult status: COMPLETE" sin structured_output da
    OUTPUT_INVALID. Ningun modulo de bin/ejecucion/ lee `result` ni el contenido del artifact. Las
    normas que se le pasan a la compuerta son las de refutacion.estandares_de_unidades para la misma
    unidad, sin pedirselas a la refutacion."""
    proy = _proyecto()
    _guion(proy, resultado={"result": "agentResult status: COMPLETE", "structured_output": None})
    pedidas = []
    real = admision.compuerta_por_defecto(str(proy))

    def compuerta(requeridas):
        pedidas.append(list(requeridas))
        return real(requeridas)

    corrida = _corrida(proy, "analizar-api", compuerta=compuerta)
    t.igual("ME-E29 un result que dice COMPLETE sin structured_output da OUTPUT_INVALID",
            "OUTPUT_INVALID", _codigo(corrida))
    t.igual("ME-E29 y FAILED", "FAILED", _de(corrida, "status"))
    t.vacio("ME-E29 ningun modulo de bin/ejecucion/ lee el campo result",
            [m for p in sorted(EJECUCION.glob("*.py")) for m in _lee_result(p)])
    t.vacio("ME-E29 ni interpreta el contenido del artifact",
            [m for p in sorted(EJECUCION.glob("*.py")) for m in _usos_del_artifact(p)])
    from orquestacion import refutacion
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    unidad = next(u for u in plan["workUnits"] if u["id"] == "analizar-api")
    t.igual("ME-E29 la compuerta recibio las normas de la unidad, al pedir y al entregar",
            [refutacion.estandares_de_unidades([unidad])] * 2, pedidas)
    variantes = [unidad, {"normative": {"standard": {"id": "ES0903"}}}, {"normative": {}}, {},
                 {"normative": {"standards": {"ES0902": {"x": 1}, "ES0901": {}, "ES0909": "roto"}}}]
    t.vacio("ME-E29 normas_de da lo mismo que estandares_de_unidades",
            [v for v in variantes if admision.normas_de(v) != refutacion.estandares_de_unidades([v])])
    nombres = set(n.id if isinstance(n, ast.Name) else n.attr
                  for n in ast.walk(ast.parse((EJECUCION / "admision.py").read_text(encoding="utf-8")))
                  if isinstance(n, (ast.Name, ast.Attribute)))
    t.verdadero("ME-E29 la admision no le pide las normas a la refutacion",
                "estandares_de_unidades" not in nombres)
    t.vacio("ME-E29 ningun modulo de bin/ejecucion/ importa la refutacion",
            [p.name for p in sorted(EJECUCION.glob("*.py")) if "refutacion" in _importados(p)])
    t.igual("ME-E29 la ruta del plan de la admision es la de la refutacion",
            refutacion.ruta_del_plan(str(proy), CLAVE), admision.ruta_del_plan(str(proy), CLAVE))


# =============================================================================================
# Fallas del Host, cancelacion e interrupcion
# =============================================================================================

def test_me_e04_fallas_del_host(t):
    """ME-E04 — Despues de la entrega: un comando que el sistema operativo no puede ejecutar, un Host
    sin JSON legible, error_during_execution, un Host que no carga el agente y un subtype
    desconocido dan FAILED con HOST_FAILURE, con startedAt y evidencia."""
    proy = _proyecto(_unidades("uno", "dos", "tres", "cuatro", "cinco"))
    no_ejecutable = Path(proy).parent / ("%s.no-ejecutable.txt" % Path(proy).name)
    no_ejecutable.write_text("esto no es un programa\n", encoding="utf-8")
    casos = (("uno", "un comando que el sistema no puede ejecutar", None,
              {"comandoHost": [str(no_ejecutable)], "limiteSegundos": 60}),
             ("dos", "un Host sin JSON legible", {"sin_json": "Error: algo salio mal", "salida": 1},
              None),
             ("tres", "error_during_execution",
              {"resultado": {"subtype": "error_during_execution", "is_error": True,
                             "structured_output": None}}, None),
             ("cuatro", "un Host que no carga el agente",
              {"sin_json": "", "stderr": "Error: agent 'dev-backend' could not be loaded",
               "salida": 1}, None),
             ("cinco", "un subtype desconocido",
              {"resultado": {"subtype": "error_que_no_existe", "is_error": True,
                             "structured_output": None}}, None))
    for unidad, que, guion, ejecucion in casos:
        _config(proy, ejecucion)
        _guion(proy, **(guion or {}))
        corrida = _corrida(proy, unidad)
        t.igual("ME-E04 %s da FAILED" % que, "FAILED", _de(corrida, "status"))
        t.igual("ME-E04 %s da HOST_FAILURE" % que, "HOST_FAILURE", _codigo(corrida))
        t.verdadero("ME-E04 %s: con startedAt y evidencia" % que,
                    _de(corrida, "startedAt") and _de(corrida, "evidence"))
    _config(proy)


def test_me_e32_falla_del_proveedor(t):
    """ME-E32 — enmendado en §34.4: un Host que termina con is_error y api_error_status, o con
    terminal_reason api_error, da PROVIDER_FAILURE, tambien con subtype success y codigo 1; uno con
    is_error sin esas marcas da HOST_FAILURE."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    # La forma que dio el Claude Code real el 09-10-2026 (§34.2, ME-E50): no trae error.type.
    real = {"subtype": "success", "is_error": True, "structured_output": None,
            "api_error_status": 404, "terminal_reason": "api_error",
            "result": "There's an issue with the selected model"}
    casos = (("uno", "la forma real del Host, con codigo 1", dict(real), 1, "PROVIDER_FAILURE"),
             ("dos", "terminal_reason api_error, con codigo 0",
              {"subtype": "success", "is_error": True, "structured_output": None,
               "terminal_reason": "api_error"}, 0, "PROVIDER_FAILURE"),
             ("tres", "un is_error sin marcas del proveedor",
              {"subtype": "success", "is_error": True, "structured_output": None,
               "result": "API Error: 529 overloaded"}, 1, "HOST_FAILURE"))
    for unidad, que, resultado, salida, codigo in casos:
        _guion(proy, resultado=resultado, salida=salida)
        corrida = _corrida(proy, unidad)
        t.igual("ME-E32 %s da %s" % (que, codigo), codigo, _codigo(corrida))
        t.igual("ME-E32 %s: FAILED" % que, "FAILED", _de(corrida, "status"))


def _interrumpir_en(segundos):
    temporizador = threading.Timer(segundos, _thread.interrupt_main)
    temporizador.start()
    return temporizador


def test_me_e05_una_interrupcion_sin_pedido(t):
    """ME-E05 — Sin cancelacion.json, un Host que termina por una senal que el motor no mando, o un
    Ctrl-C sobre el motor, dan FAILED con HOST_INTERRUPTED, y el motor mata el arbol del Host."""
    proy = _proyecto(_unidades("uno", "dos"))
    _guion(proy, senal=True)
    corrida = _corrida(proy, "uno")
    t.igual("ME-E05 un Host terminado por una senal da FAILED", "FAILED", _de(corrida, "status"))
    t.igual("ME-E05 con HOST_INTERRUPTED", "HOST_INTERRUPTED", _codigo(corrida))

    eco, nieto = _eco(proy, "eco-dos"), _eco(proy, "nieto-dos")
    _guion(proy, eco=str(eco), hijo=str(nieto), dormir=60)
    temporizador = _interrumpir_en(4)
    try:
        corrida = _corrida(proy, "dos")
    except KeyboardInterrupt:
        corrida = {"res": None, "err": None, "exc": "KeyboardInterrupt"}
    finally:
        temporizador.cancel()
    t.igual("ME-E05 un Ctrl-C sobre el motor da FAILED", "FAILED", _de(corrida, "status"))
    t.igual("ME-E05 con HOST_INTERRUPTED", "HOST_INTERRUPTED", _codigo(corrida))
    pid = (_leer_eco(eco) or {}).get("pid")
    pid_nieto = int(nieto.read_text()) if nieto.is_file() else None
    t.verdadero("ME-E05 el Host murio", pid and _esperar(lambda: not proceso.pid_vivo(pid), 15))
    t.verdadero("ME-E05 y su arbol tambien",
                pid_nieto and _esperar(lambda: not proceso.pid_vivo(pid_nieto), 15))
    _terminar(pid)
    _terminar(pid_nieto)


def test_me_e31_el_limite(t):
    """ME-E31 — Un Host que no termina antes de limiteSegundos da FAILED con TIMEOUT, el detail nombra
    el limite, y el arbol del Host termina."""
    proy = _proyecto()
    _config(proy, {"comandoHost": [sys.executable, str(HOST)], "limiteSegundos": 3})
    eco, nieto = _eco(proy), _eco(proy, "nieto")
    _guion(proy, eco=str(eco), hijo=str(nieto), dormir=60)
    inicio = time.time()
    corrida = _corrida(proy)
    t.igual("ME-E31 da FAILED", "FAILED", _de(corrida, "status"))
    t.igual("ME-E31 con TIMEOUT", "TIMEOUT", _codigo(corrida))
    t.contiene("ME-E31 el detail nombra el limite aplicado", "3 s",
               ((corrida["res"] or {}).get("error") or {}).get("detail"))
    t.verdadero("ME-E31 cortado en el limite, no al final del Host", time.time() - inicio < 40)
    pid = (_leer_eco(eco) or {}).get("pid")
    pid_nieto = int(nieto.read_text()) if nieto.is_file() else None
    t.verdadero("ME-E31 el Host termino", pid and _esperar(lambda: not proceso.pid_vivo(pid), 15))
    t.verdadero("ME-E31 y su arbol", pid_nieto and _esperar(lambda: not proceso.pid_vivo(pid_nieto),
                                                             15))
    _terminar(pid)
    _terminar(pid_nieto)


def test_me_e33_sin_catalogo_no_hay_output(t):
    """ME-E33 — Sin catalogo de secretos, con el AgentReport ya recibido: FAILED con ENGINE_FAILURE,
    sin output, y no queda output.md."""
    proy = _proyecto()
    _guion(proy, resultado=_informe("COMPLETE", "# Informe con " + SECRETO + "\n"))
    estado = {"sin": False}

    def catalogo():
        return None if estado["sin"] else limpieza.cargar_catalogo()

    def perder(_carpeta):
        estado["sin"] = True

    corrida = _corrida(proy, catalogo=catalogo, antes_de_entregar=perder)
    t.igual("ME-E33 da FAILED", "FAILED", _de(corrida, "status"))
    t.igual("ME-E33 con ENGINE_FAILURE", "ENGINE_FAILURE", _codigo(corrida))
    t.verdadero("ME-E33 sin output", corrida["res"] is not None and _de(corrida, "output") is None)
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    t.verdadero("ME-E33 y no queda output.md", not (_carpeta(proy, eid) / registro.OUTPUT).exists())
    t.no_contiene("ME-E33 el detail no lleva nada del agente", SECRETO,
                  json.dumps(corrida["res"] or {}))


def test_me_e06_cancelar(t):
    """ME-E06 — Con el motor vivo, --cancelar desde otro proceso sobre una RUNNING escribe
    cancelacion.json, y el motor termina el Host y deja CANCELLED con startedAt y evidencia. Sobre
    una REQUESTED con el motor vivo, la deja CANCELLED sin entregarla. Sobre una terminal no cambia
    nada y lo dice."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    eco, nieto = _eco(proy, "eco-uno"), _eco(proy, "nieto-uno")
    guion = _guion(proy, "guion-uno", eco=str(eco), hijo=str(nieto), dormir=40)
    hijo, _ = _lanzar_motor(proy, "uno", guion=guion)
    t.verdadero("ME-E06 la Execution llego a RUNNING",
                _esperar(lambda: _corriendo_de(proy, "uno") is not None and _leer_eco(eco)))
    carpeta = _corriendo_de(proy, "uno")
    eid = carpeta.name if carpeta else "exe_" + "0" * 32
    try:
        pedido = motor.cancelar(str(proy), CLAVE, eid, "Otra persona")
    except motor.ErrorDelComando as e:
        pedido = {"exc": str(e)}
    t.verdadero("ME-E06 --cancelar escribio cancelacion.json",
                pedido.get("pedido") and (_carpeta(proy, eid) / registro.CANCELACION).is_file())
    salida = _salida_del_hijo(hijo)
    res = salida["res"] or {}
    t.igual("ME-E06 el motor deja CANCELLED", "CANCELLED", res.get("status"))
    t.igual("ME-E06 con codigo CANCELLED", "CANCELLED", (res.get("error") or {}).get("code"))
    t.verdadero("ME-E06 con startedAt y evidencia", res.get("startedAt") and res.get("evidence"))
    pid = (_leer_eco(eco) or {}).get("pid")
    pid_nieto = int(nieto.read_text()) if nieto.is_file() else None
    t.verdadero("ME-E06 el motor termino el arbol del Host",
                pid and pid_nieto and _esperar(lambda: not proceso.pid_vivo(pid)
                                               and not proceso.pid_vivo(pid_nieto), 15))
    _terminar(pid)
    _terminar(pid_nieto)

    eco_dos = _eco(proy, "eco-dos")
    _guion(proy, "guion-dos", eco=str(eco_dos))

    def cancelar_desde_otro_proceso(carpeta):
        M64._proceso([sys.executable, str(CLI), "ejecutar", CLAVE, "--cancelar", Path(carpeta).name,
                      "--proyecto", str(proy)])

    corrida = _corrida(proy, "dos", antes_de_entregar=cancelar_desde_otro_proceso)
    t.igual("ME-E06 una REQUESTED con el motor vivo queda CANCELLED", "CANCELLED",
            _de(corrida, "status"))
    t.verdadero("ME-E06 sin startedAt ni evidencia", corrida["res"] is not None
                and _de(corrida, "startedAt") is None and _de(corrida, "evidence") is None)
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    t.verdadero("ME-E06 sin entregarla: no hay entrega.json",
                not (_carpeta(proy, eid) / registro.ENTREGA).exists())
    t.verdadero("ME-E06 y el Host no se lanzo", not eco_dos.exists())

    _guion(proy, "guion-tres")
    corrida = _corrida(proy, "tres")
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    antes = M64._bytes(_carpeta(proy, eid) / registro.RESULT)
    codigo, salida_cli, _ = M64._cli(["ejecutar", CLAVE, "--cancelar", eid, "--proyecto", proy])
    t.igual("ME-E06 --cancelar sobre una terminal sale con 0", 0, codigo)
    t.contiene("ME-E06 y dice que no cambio nada", "no se cambió nada", salida_cli)
    t.igual("ME-E06 result.json no cambio", antes, M64._bytes(_carpeta(proy, eid) / registro.RESULT))
    t.verdadero("ME-E06 y no escribio cancelacion.json",
                not (_carpeta(proy, eid) / registro.CANCELACION).exists())


def test_me_e34_una_requested_huerfana_y_un_pedido_tardio(t):
    """ME-E34 — Una REQUESTED real cuyo motor murio no la cierra la recuperacion, bloquea la clave
    con DUPLICATE_EXECUTION, y --cancelar la deja CANCELLED sin startedAt ni evidencia. Una RUNNING
    cuyo motor ya habia muerto, con --cancelar, queda FAILED con HOST_INTERRUPTED, sin
    cancelacion.json."""
    proy = _proyecto(_unidades("uno", "dos"))
    guion = _guion(proy, "guion-uno")
    hijo, marca = _lanzar_motor(proy, "uno", "colgar", guion=guion)
    t.verdadero("ME-E34 el motor quedo entre la creacion y la entrega",
                _esperar(lambda: os.path.exists(marca + ".colgado")))
    eid = Path(Path(marca + ".colgado").read_text()).name if os.path.exists(marca + ".colgado") \
        else "exe_" + "0" * 32
    _matar(hijo.pid)
    hijo.communicate(timeout=60)
    t.igual("ME-E34 es una REQUESTED real, con turno", [(1, eid)], _turnos(proy, "uno"))
    t.igual("ME-E34 la recuperacion no la cierra", [], motor.recuperar(str(proy), CLAVE))
    t.igual("ME-E34 sigue REQUESTED", "REQUESTED", registro.estado(str(proy), CLAVE, eid)["estado"])
    corrida = _corrida(proy, "uno")
    t.igual("ME-E34 bloquea la clave", "DUPLICATE_EXECUTION", _codigo(corrida))
    t.contiene("ME-E34 y el detail dice como cancelarla", "--cancelar %s" % eid,
               (corrida["err"] or {}).get("detail"))
    salida = motor.cancelar(str(proy), CLAVE, eid, "Otra persona")
    res = salida.get("resultado") or {}
    t.igual("ME-E34 --cancelar la deja CANCELLED", "CANCELLED", res.get("status"))
    t.verdadero("ME-E34 sin startedAt ni evidencia",
                res and res.get("startedAt") is None and res.get("evidence") is None)

    carpeta, pid = _huerfana(proy, "dos")
    eid = carpeta.name if carpeta else "exe_" + "0" * 32
    try:
        salida = motor.cancelar(str(proy), CLAVE, eid, "Otra persona")
    except motor.ErrorDelComando as e:
        salida = {"exc": str(e)}
    res = salida.get("resultado") or {}
    t.igual("ME-E34 una RUNNING con el motor muerto queda FAILED", "FAILED", res.get("status"))
    t.igual("ME-E34 con HOST_INTERRUPTED", "HOST_INTERRUPTED", (res.get("error") or {}).get("code"))
    t.verdadero("ME-E34 y no se escribio cancelacion.json: el corte precedio al pedido",
                carpeta is not None and not (carpeta / registro.CANCELACION).exists())
    _terminar(pid)


# =============================================================================================
# La admision al entregar
# =============================================================================================

def _reescribir_plan(proy, cambio):
    ruta = M64._plan_de(proy, CLAVE)
    plan = M64._leer_json(ruta)
    cambio(plan)
    ruta.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def test_me_e07_el_plan_cambio(t):
    """ME-E07 — Si el plan cambia entre la creacion y la entrega, por cualquier campo, uno de 2.1
    incluido, la Execution termina REJECTED con PLAN_CHANGED aunque plan_id y plan_version
    coincidan."""
    proy = _proyecto()
    _guion(proy)

    def cambiar(_carpeta):
        _reescribir_plan(proy, lambda p: p["flowPreconditions"].update(nota="cambiada a mano"))

    corrida = _corrida(proy, antes_de_entregar=cambiar)
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    request = M64._leer_json(_carpeta(proy, _de(corrida, "executionId") or "exe_" + "0" * 32)
                             / registro.REQUEST) if corrida["res"] else {}
    t.igual("ME-E07 plan_id y plan_version siguen iguales",
            ((request.get("plan") or {}).get("planId"), (request.get("plan") or {}).get("planVersion")),
            (plan["meta"]["plan_id"], plan["meta"]["plan_version"]))
    t.igual("ME-E07 REJECTED", "REJECTED", _de(corrida, "status"))
    t.igual("ME-E07 con PLAN_CHANGED", "PLAN_CHANGED", _codigo(corrida))


def _contexto_cambiado(proy):
    ruta = Path(proy) / ".claude" / "contextos" / (CLAVE + ".json")
    contexto = json.loads(ruta.read_text(encoding="utf-8"))
    contexto["task"]["title"] = "Otro titulo, despues de planificar"
    contexto["meta"]["context_hash"] = M64.ARMADOR.hash_de(contexto)
    ruta.write_text(json.dumps(contexto), encoding="utf-8")


def test_me_e08_el_flujo_deja_de_permitir(t):
    """ME-E08 — Si el TaskFlowState deja de permitir delegar entre la creacion y la entrega (la
    tarea cancelada, un TaskContext cambiado), termina REJECTED con DELEGATION_NOT_ALLOWED, y el
    detail nombra el bloqueo."""
    proy = _proyecto(_unidades("uno", "dos"))
    _guion(proy)
    corrida = _corrida(proy, "uno", antes_de_entregar=lambda c: _contexto_cambiado(proy))
    t.igual("ME-E08 con el TaskContext cambiado: REJECTED", "REJECTED", _de(corrida, "status"))
    t.igual("ME-E08 con DELEGATION_NOT_ALLOWED", "DELEGATION_NOT_ALLOWED", _codigo(corrida))
    t.contiene("ME-E08 el detail nombra el bloqueo", "TASK_CONTEXT_STALE",
               ((corrida["res"] or {}).get("error") or {}).get("detail"))

    otro = _proyecto(_unidades("uno"))
    _guion(otro)
    estado = Path(otro) / ".claude" / "runtime" / "tasks" / CLAVE / "state.json"

    def cancelar_la_tarea(_carpeta):
        doc = json.loads(estado.read_text(encoding="utf-8"))
        doc["status"] = "CANCELLED"
        estado.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    corrida = _corrida(otro, "uno", antes_de_entregar=cancelar_la_tarea)
    t.igual("ME-E08 con la tarea cancelada: REJECTED", "REJECTED", _de(corrida, "status"))
    t.igual("ME-E08 con DELEGATION_NOT_ALLOWED", "DELEGATION_NOT_ALLOWED", _codigo(corrida))
    t.contiene("ME-E08 el detail nombra el estado", "CANCELLED",
               ((corrida["res"] or {}).get("error") or {}).get("detail"))


def _fuentes(proy, estandar, estado="SOURCE_INTEGRITY_ALERT"):
    M64._json(Path(proy) / ".claude" / "harness.fuentes.json",
              {"sources": {estandar: {"state": estado}}})


def test_me_e09_la_compuerta_normativa_con_las_normas_de_la_unidad(t):
    """ME-E09 — Con una fuente de la unidad en SOURCE_INTEGRITY_ALERT en harness.fuentes.json y el
    state.json sin reflejarlo, la admision da NORMATIVE_GATE_BLOCKED y el detail nombra la fuente y
    su estado. Con la alerta sobre una fuente que la unidad no exige, admite."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    _guion(proy)
    _fuentes(proy, "ES0901")
    antes = _arbol(proy)
    corrida = _corrida(proy, "uno")
    t.igual("ME-E09 al pedir: NORMATIVE_GATE_BLOCKED", "NORMATIVE_GATE_BLOCKED", _codigo(corrida))
    t.contiene("ME-E09 el detail nombra la fuente y su estado", "ES0901 SOURCE_INTEGRITY_ALERT",
               (corrida["err"] or {}).get("detail"))
    t.igual("ME-E09 y no se escribio nada", antes, _arbol(proy))
    (Path(proy) / ".claude" / "harness.fuentes.json").unlink()
    corrida = _corrida(proy, "dos", antes_de_entregar=lambda c: _fuentes(proy, "ES0901"))
    t.igual("ME-E09 al entregar: REJECTED con NORMATIVE_GATE_BLOCKED",
            ("REJECTED", "NORMATIVE_GATE_BLOCKED"), (_de(corrida, "status"), _codigo(corrida)))
    _fuentes(proy, "ES0903")
    corrida = _corrida(proy, "tres")
    t.igual("ME-E09 con la alerta en una fuente que la unidad no exige, admite", "SUCCEEDED",
            _de(corrida, "status"))


def test_me_e10_el_agente_deja_de_ser_ruteable(t):
    """ME-E10 — Si el agente deja de ser ruteable entre la creacion y la entrega, termina REJECTED
    con AGENT_UNAVAILABLE."""
    from orquestacion import registro_agentes
    proy = _proyecto()
    _guion(proy)
    real = registro_agentes.cargar()
    estado = {"quitar": False}

    def cargar():
        doc = copy.deepcopy(real)
        if estado["quitar"]:
            doc["agents"] = [a for a in doc["agents"] if a.get("id") != "dev-backend"]
        return doc

    corrida = _corrida(proy, cargar_registro=cargar,
                       antes_de_entregar=lambda c: estado.update(quitar=True))
    t.igual("ME-E10 REJECTED", "REJECTED", _de(corrida, "status"))
    t.igual("ME-E10 con AGENT_UNAVAILABLE", "AGENT_UNAVAILABLE", _codigo(corrida))


class _ProveeTodo(H.Adaptador):
    """Un adaptador que dice proveer toda capability: aisla la condicion 13 de Catalog de la del
    adaptador, que para jira.* siempre dice que no (ME-E41)."""

    def provee(self, capacidades, definicion):
        return []


def test_me_e11_una_capability_deja_de_estar(t):
    """ME-E11 — Si una capability deja de estar disponible entre la creacion y la entrega, termina
    REJECTED con CAPABILITY_UNAVAILABLE."""
    proy = _proyecto([M64._unidad("leer-jira", capacidades=("jira.issue.read",))])
    _guion(proy)

    def apagar(_carpeta):
        M64._json(Path(proy) / ".claude" / "harness.capacidades.json",
                  {"capacidades": dict(M64.REGISTRO, **{"jira.issue.read": "DISABLED"})})

    corrida = _corrida(proy, "leer-jira", adaptador=_ProveeTodo([sys.executable, str(HOST)], 60),
                       antes_de_entregar=apagar)
    t.igual("ME-E11 REJECTED", "REJECTED", _de(corrida, "status"))
    t.igual("ME-E11 con CAPABILITY_UNAVAILABLE", "CAPABILITY_UNAVAILABLE", _codigo(corrida))


def test_me_e12_las_dependencias(t):
    """ME-E12 — Una unidad con una dependencia sin SUCCEEDED en la misma huella se rechaza al pedir
    con DEPENDENCY_NOT_SATISFIED; con la dependencia SUCCEEDED, se admite y admission.dependencies
    nombra esa Execution."""
    proy = _proyecto()
    _guion(proy)
    antes = _arbol(proy)
    corrida = _corrida(proy, "implementar-endpoint")
    t.igual("ME-E12 sin ejecutar la dependencia: DEPENDENCY_NOT_SATISFIED",
            "DEPENDENCY_NOT_SATISFIED", _codigo(corrida))
    t.igual("ME-E12 y no se escribio nada", antes, _arbol(proy))
    _guion(proy, resultado=_informe("PARTIAL"))
    fallida = _corrida(proy, "analizar-api")
    t.igual("ME-E12 la dependencia quedo FAILED", "FAILED", _de(fallida, "status"))
    corrida = _corrida(proy, "implementar-endpoint")
    t.igual("ME-E12 con la dependencia FAILED: DEPENDENCY_NOT_SATISFIED",
            "DEPENDENCY_NOT_SATISFIED", _codigo(corrida))
    _guion(proy)
    dependencia = _corrida(proy, "analizar-api")
    t.igual("ME-E12 la dependencia quedo SUCCEEDED", "SUCCEEDED", _de(dependencia, "status"))
    corrida = _corrida(proy, "implementar-endpoint")
    t.igual("ME-E12 con la dependencia SUCCEEDED se admite y termina", "SUCCEEDED",
            _de(corrida, "status"))
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    request = M64._leer_json(_carpeta(proy, eid) / registro.REQUEST) \
        if (_carpeta(proy, eid) / registro.REQUEST).is_file() else {}
    t.igual("ME-E12 admission.dependencies nombra esa Execution",
            [{"workUnitId": "analizar-api", "executionId": _de(dependencia, "executionId")}],
            (request.get("admission") or {}).get("dependencies"))


def test_me_e27_la_precedencia_al_pedir(t):
    """ME-E27 — Al pedir, la regla corre en el orden de T3 §37.5 y gana la primera falla: con dos
    condiciones rotas a la vez sale el codigo de la anterior. Ningun rechazo al pedir deja algo
    escrito."""
    proy = _proyecto([M64._unidad("leer-jira", capacidades=("jira.issue.read",)),
                      M64._unidad("uno")])
    _guion(proy)
    casos = []
    M64._json(Path(proy) / ".claude" / "harness.capacidades.json",
              {"capacidades": dict(M64.REGISTRO, **{"jira.issue.read": "DISABLED"})})
    _fuentes(proy, "ES0901")
    casos.append(("la compuerta normativa (9) y una capability (13)", "leer-jira",
                  "NORMATIVE_GATE_BLOCKED", "CAPABILITY_UNAVAILABLE"))
    for que, unidad, gana, pierde in casos:
        antes = _arbol(proy)
        corrida = _corrida(proy, unidad)
        t.igual("ME-E27 %s: gana %s" % (que, gana), gana, _codigo(corrida))
        t.vacio("ME-E27 %s: el rechazo pasa validar_rechazo" % que,
                C.validar_rechazo(corrida["err"]) if corrida["err"] else ["no hubo rechazo"])
        t.igual("ME-E27 %s: no se escribio nada" % que, antes, _arbol(proy))
    (Path(proy) / ".claude" / "harness.fuentes.json").unlink()
    _contexto_cambiado(proy)
    antes = _arbol(proy)
    corrida = _corrida(proy, "no-existe")
    t.igual("ME-E27 el flujo (6) y una unidad que no esta (7): gana DELEGATION_NOT_ALLOWED",
            "DELEGATION_NOT_ALLOWED", _codigo(corrida))
    t.igual("ME-E27 y no se escribio nada", antes, _arbol(proy))
    _reescribir_plan(proy, lambda p: p["meta"].update(task_key="GCBA-99",
                                                      schema_version="orchestration-plan/2.0"))
    corrida = _corrida(proy, "uno")
    t.igual("ME-E27 la TaskKey (3) y el plan no listo (5): gana TASK_KEY_MISMATCH",
            "TASK_KEY_MISMATCH", _codigo(corrida))
    t.igual("ME-E27 y no se escribio nada", antes, _arbol(proy))


def test_me_e28_una_request_adulterada(t):
    """ME-E28 — fortalecido en §34.4: un request.json cambiado entre la creacion y la entrega, en
    requestedBy, createdAt, admission, workUnit o plan, termina REJECTED con CONTRACT_INVALID, sin
    entrega.json y sin Host, con el requestFingerprint de lo que el motor escribio. Reescrito con el
    mismo contenido, se entrega."""
    unidades = ["c%02d" % i for i in range(len(ADULTERACIONES))] + ["igual"]
    proy = _proyecto(_unidades(*unidades))
    for unidad, (que, cambio) in zip(unidades, ADULTERACIONES):
        eco = _eco(proy, "eco-" + unidad)
        _guion(proy, eco=str(eco))
        original = {}

        def adulterar(carpeta, _cambio=cambio, _original=original):
            _original["huella"] = C.huella(M64._leer_json(Path(carpeta) / registro.REQUEST))
            _reescribir_request(carpeta, _cambio)

        corrida = _corrida(proy, unidad, antes_de_entregar=adulterar)
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        en_disco = M64._leer_json(_carpeta(proy, eid) / registro.RESULT) \
            if (_carpeta(proy, eid) / registro.RESULT).is_file() else {}
        t.igual("ME-E28 %s cambiado: REJECTED con CONTRACT_INVALID" % que,
                ("REJECTED", "CONTRACT_INVALID"), (_de(corrida, "status"), _codigo(corrida)))
        t.verdadero("ME-E28 %s cambiado: sin entrega.json ni Host" % que,
                    not (_carpeta(proy, eid) / registro.ENTREGA).exists() and not eco.exists())
        t.igual("ME-E28 %s cambiado: result.json lleva la huella de lo que escribio el motor" % que,
                original.get("huella"), en_disco.get("requestFingerprint"))
    eco = _eco(proy, "eco-igual")
    _guion(proy, eco=str(eco))
    corrida = _corrida(proy, "igual", antes_de_entregar=lambda c: _reescribir_request(
        c, lambda r: None, indent=4, ordenada=False))
    t.igual("ME-E28 reescrito con el mismo contenido, se entrega", "SUCCEEDED", _de(corrida, "status"))


def test_me_e30_planes_que_no_se_admiten(t):
    """ME-E30 — Un plan 2.0 legible con status READY_FOR_EXECUTION escrito da PLAN_NOT_READY; un JSON
    cortado, PLAN_UNREADABLE; un plan de otra TaskKey, TASK_KEY_MISMATCH; dos unidades con el mismo
    id, PLAN_UNREADABLE."""
    proy = _proyecto()
    _guion(proy)
    ruta = M64._plan_de(proy, CLAVE)
    original = ruta.read_bytes()

    def dos_iguales(plan):
        plan["workUnits"].append(copy.deepcopy(plan["workUnits"][0]))

    casos = (("un plan 2.0 legible y READY", "PLAN_NOT_READY",
              lambda: _reescribir_plan(proy, lambda p: p["meta"].update(
                  schema_version="orchestration-plan/2.0"))),
             ("un JSON cortado", "PLAN_UNREADABLE", lambda: ruta.write_bytes(original[:len(original) // 2])),
             ("un plan de otra TaskKey", "TASK_KEY_MISMATCH",
              lambda: _reescribir_plan(proy, lambda p: p["meta"].update(task_key="GCBA-99"))),
             ("dos unidades con el mismo id", "PLAN_UNREADABLE",
              lambda: _reescribir_plan(proy, dos_iguales)))
    for que, codigo, romper in casos:
        romper()
        antes = _arbol(proy)
        corrida = _corrida(proy, "analizar-api")
        t.igual("ME-E30 %s da %s" % (que, codigo), codigo, _codigo(corrida))
        t.igual("ME-E30 %s: no se escribio nada" % que, antes, _arbol(proy))
        ruta.write_bytes(original)


def test_me_e41_lo_que_el_adaptador_no_provee(t):
    """ME-E41 — Una unidad que pide jira.issue.read, disponible para Catalog, se admite al pedir y
    termina REJECTED con CAPABILITY_UNAVAILABLE al entregar, porque el adaptador no la provee. Una
    que pide repository.write con un agente sin Write, tambien."""
    proy = _proyecto([M64._unidad("leer-jira", capacidades=("jira.issue.read",)),
                      M64._unidad("arq", dominio="architecture", capacidades=("repository.write",))],
                     dominios=("backend", "architecture"), agentes=("dev-backend", "dev-architecture"))
    _guion(proy)
    for unidad, que in (("leer-jira", "jira.issue.read"), ("arq", "repository.write sin Write")):
        corrida = _corrida(proy, unidad)
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        t.igual("ME-E41 %s se admite al pedir: hay turno" % que, [(1, eid)], _turnos(proy, unidad))
        t.igual("ME-E41 %s termina REJECTED" % que, "REJECTED", _de(corrida, "status"))
        t.igual("ME-E41 %s con CAPABILITY_UNAVAILABLE" % que, "CAPABILITY_UNAVAILABLE",
                _codigo(corrida))
        t.verdadero("ME-E41 %s sin entrega" % que,
                    not (_carpeta(proy, eid) / registro.ENTREGA).exists())


def test_me_e42_la_definicion_del_agente(t):
    """ME-E42 — Sin .claude/agents/<agente>.md, o con otro name:, REJECTED con AGENT_UNAVAILABLE,
    sin entrega.json y sin lanzar el Host. Con la definicion y un Host que no la puede cargar,
    FAILED con HOST_FAILURE. Ningun resultado del motor tiene FAILED con AGENT_UNAVAILABLE o
    CAPABILITY_UNAVAILABLE."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    agente = Path(proy) / ".claude" / "agents" / "dev-backend.md"
    original = agente.read_bytes()
    resultados = []
    for unidad, que, romper in (("uno", "sin el archivo del agente", lambda: agente.unlink()),
                                ("dos", "con otro name:",
                                 lambda: agente.write_bytes(original.replace(
                                     b"name: dev-backend", b"name: dev-otro")))):
        romper()
        eco = _eco(proy, "eco-" + unidad)
        _guion(proy, eco=str(eco))
        corrida = _corrida(proy, unidad)
        resultados.append(corrida["res"])
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        t.igual("ME-E42 %s: REJECTED con AGENT_UNAVAILABLE" % que,
                ("REJECTED", "AGENT_UNAVAILABLE"), (_de(corrida, "status"), _codigo(corrida)))
        t.verdadero("ME-E42 %s: sin entrega.json" % que,
                    not (_carpeta(proy, eid) / registro.ENTREGA).exists())
        t.verdadero("ME-E42 %s: el Host no se lanzo" % que, not eco.exists())
        agente.write_bytes(original)
    _guion(proy, sin_json="", stderr="Error: agent 'dev-backend' could not be loaded", salida=1)
    corrida = _corrida(proy, "tres")
    resultados.append(corrida["res"])
    t.igual("ME-E42 un Host que no carga el agente despues de la entrega: FAILED con HOST_FAILURE",
            ("FAILED", "HOST_FAILURE"), (_de(corrida, "status"), _codigo(corrida)))
    t.vacio("ME-E42 ningun resultado tiene FAILED con AGENT_UNAVAILABLE o CAPABILITY_UNAVAILABLE",
            [r for r in resultados if (r or {}).get("status") == "FAILED"
             and ((r or {}).get("error") or {}).get("code") in ("AGENT_UNAVAILABLE",
                                                                 "CAPABILITY_UNAVAILABLE")])
    t.vacio("ME-E42 despues de la entrega el motor no nombra esos dos codigos",
            ["%s: %s" % (p.name, n.value) for p in (EJECUCION / "motor.py",
                                                     EJECUCION / "host_claude_code.py",
                                                     EJECUCION / "proceso.py",
                                                     EJECUCION / "evidencia.py")
             for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
             if isinstance(n, ast.Constant) and n.value in ("AGENT_UNAVAILABLE",
                                                            "CAPABILITY_UNAVAILABLE")])


# =============================================================================================
# Idempotencia y reintento
# =============================================================================================

def test_me_e13_una_abierta_bloquea(t):
    """ME-E13 — Con una Execution REQUESTED o RUNNING de la misma clave, una request nueva da
    DUPLICATE_EXECUTION al pedir y no escribe nada."""
    proy = _proyecto(_unidades("uno", "dos"))
    _guion(proy)
    vistos = {}

    def pedir_otra(_carpeta):
        antes = _arbol(proy)
        vistos["otra"] = _corrida(proy, "uno")
        vistos["igual"] = antes == _arbol(proy)

    _corrida(proy, "uno", antes_de_entregar=pedir_otra)
    t.igual("ME-E13 con una REQUESTED: DUPLICATE_EXECUTION", "DUPLICATE_EXECUTION",
            _codigo(vistos.get("otra") or {"err": None, "res": None}))
    t.verdadero("ME-E13 y no escribio nada", vistos.get("igual"))

    guion = _guion(proy, "guion-dos", dormir=30)
    hijo, _ = _lanzar_motor(proy, "dos", guion=guion)
    t.verdadero("ME-E13 la otra llego a RUNNING", _esperar(lambda: _corriendo_de(proy, "dos")))
    antes = _arbol(proy)
    corrida = _corrida(proy, "dos")
    t.igual("ME-E13 con una RUNNING: DUPLICATE_EXECUTION", "DUPLICATE_EXECUTION", _codigo(corrida))
    t.igual("ME-E13 y no escribio nada", antes, _arbol(proy))
    carpeta = _corriendo_de(proy, "dos")
    if carpeta is not None:
        motor.cancelar(str(proy), CLAVE, carpeta.name, PIDE)
    _salida_del_hijo(hijo)


def test_me_e14_un_succeeded_cierra_la_clave(t):
    """ME-E14 — Con una SUCCEEDED de la misma clave, una request nueva da DUPLICATE_EXECUTION, aunque
    despues haya pasado cualquier cosa."""
    proy = _proyecto()
    _guion(proy)
    primera = _corrida(proy)
    t.igual("ME-E14 la primera queda SUCCEEDED", "SUCCEEDED", _de(primera, "status"))
    corrida = _corrida(proy)
    t.igual("ME-E14 una request nueva: DUPLICATE_EXECUTION", "DUPLICATE_EXECUTION", _codigo(corrida))
    eid = _de(primera, "executionId") or "exe_" + "0" * 32
    registro.escribir_json(str(_carpeta(proy, eid) / registro.CANCELACION),
                           {"pedidoEn": registro.ahora(), "pedidoPor": "alguien, tarde"})
    motor.recuperar(str(proy), CLAVE)
    corrida = _corrida(proy, pedido_por="Otra persona")
    t.igual("ME-E14 aunque despues haya un pedido de cancelar, otra persona y una recuperacion",
            "DUPLICATE_EXECUTION", _codigo(corrida))
    t.igual("ME-E14 y sigue un solo turno", 1, len(_turnos(proy, "analizar-api")))


def _reintento(t, eid_escenario, proy, primera, estado):
    t.igual("%s la primera quedo %s" % (eid_escenario, estado), estado, _de(primera, "status"))
    _guion(proy)
    segunda = _corrida(proy)
    turnos = _turnos(proy, "analizar-api")
    t.igual("%s una request nueva crea el turno 2" % eid_escenario, [1, 2], [n for n, _ in turnos])
    t.verdadero("%s con otro executionId" % eid_escenario,
                _de(segunda, "executionId") and _de(segunda, "executionId") != _de(primera,
                                                                                   "executionId"))
    llaves = set()
    for _, eid in turnos:
        ruta = _carpeta(proy, eid or "exe_" + "0" * 32) / registro.REQUEST
        llaves.add(M64._leer_json(ruta)["idempotencyKey"] if ruta.is_file() else None)
    t.igual("%s y la misma idempotencyKey" % eid_escenario, {_llave(proy, "analizar-api")}, llaves)


def test_me_e15_reintento_despues_de_failed(t):
    """ME-E15 — Despues de una FAILED, una request nueva crea el turno 2, con otro executionId y la
    misma idempotencyKey."""
    proy = _proyecto()
    _guion(proy, resultado=_informe("FAILED"))
    _reintento(t, "ME-E15", proy, _corrida(proy), "FAILED")


def test_me_e16_reintento_despues_de_cancelled(t):
    """ME-E16 — Lo mismo despues de una CANCELLED."""
    proy = _proyecto()
    _guion(proy)
    primera = _corrida(proy, antes_de_entregar=lambda c: motor.cancelar(str(proy), CLAVE,
                                                                       Path(c).name, PIDE))
    _reintento(t, "ME-E16", proy, primera, "CANCELLED")


def test_me_e17_reintento_despues_de_rejected(t):
    """ME-E17 — Lo mismo despues de una REJECTED."""
    proy = _proyecto()
    _guion(proy)
    agente = Path(proy) / ".claude" / "agents" / "dev-backend.md"
    original = agente.read_bytes()
    primera = _corrida(proy, antes_de_entregar=lambda c: agente.unlink())
    agente.write_bytes(original)
    _reintento(t, "ME-E17", proy, primera, "REJECTED")


# =============================================================================================
# Persistencia y recuperacion
# =============================================================================================

def test_me_e20_una_running_huerfana(t):
    """ME-E20 — Una RUNNING sin cancelacion.json cuyo motor murio la cierra la recuperacion con
    FAILED y HOST_INTERRUPTED, startedAt de la entrega y evidencia UNATTRIBUTABLE si el arbol cambio
    o RESOLVED vacia si no. Con el motor vivo, no la toca. No se vuelve a entregar y no se mata ningun
    proceso."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    guion = _guion(proy, "guion-uno", dormir=30)
    hijo, _ = _lanzar_motor(proy, "uno", guion=guion)
    t.verdadero("ME-E20 la Execution llego a RUNNING", _esperar(lambda: _corriendo_de(proy, "uno")))
    carpeta = _corriendo_de(proy, "uno")
    t.igual("ME-E20 con el motor vivo la recuperacion no la toca", [],
            motor.recuperar(str(proy), CLAVE))
    eid = carpeta.name if carpeta else "exe_" + "0" * 32
    t.igual("ME-E20 y sigue RUNNING", "RUNNING", registro.estado(str(proy), CLAVE, eid)["estado"])
    motor.cancelar(str(proy), CLAVE, eid, PIDE)
    _salida_del_hijo(hijo)

    for unidad, cambios, estado in (("dos", None, "RESOLVED"),
                                    ("tres", [{"ruta": "src/viejo.py", "contenido": "OTRO = 2\n"}],
                                     "CHANGES_UNATTRIBUTABLE")):
        carpeta, pid = _huerfana(proy, unidad, cambios)
        eid = carpeta.name if carpeta else "exe_" + "0" * 32
        eco = _eco(proy, "eco-" + unidad)
        eco_antes = M64._bytes(eco)
        cerradas = motor.recuperar(str(proy), CLAVE)
        res = (registro.estado(str(proy), CLAVE, eid)["resultado"] or {})
        entrega = M64._leer_json(carpeta / registro.ENTREGA) if carpeta else {}
        t.igual("ME-E20 %s: la recuperacion la cierra" % unidad, [eid],
                [c["executionId"] for c in cerradas])
        t.igual("ME-E20 %s: FAILED con HOST_INTERRUPTED" % unidad, ("FAILED", "HOST_INTERRUPTED"),
                (res.get("status"), (res.get("error") or {}).get("code")))
        t.igual("ME-E20 %s: startedAt es el de la entrega" % unidad, entrega.get("deliveredAt"),
                res.get("startedAt"))
        t.igual("ME-E20 %s: la evidencia es %s" % (unidad, estado), estado,
                ((res.get("evidence") or {}).get("changes") or {}).get("state"))
        t.igual("ME-E20 %s: no se volvio a entregar" % unidad, eco_antes, M64._bytes(eco))
        t.verdadero("ME-E20 %s: la recuperacion no mato al Host que sobrevivio" % unidad,
                    pid and proceso.pid_vivo(pid))
        _terminar(pid)


def test_me_e53_una_cancelacion_persistida_gana(t):
    """ME-E53 — Dos RUNNING cuyo motor murio, iguales salvo por cancelacion.json: la que lo tiene
    queda CANCELLED con codigo CANCELLED, la otra FAILED con HOST_INTERRUPTED. Las dos con startedAt
    de entrega.json y evidencia, sin agentDeclaredStatus ni output aunque haya quedado un output.md.
    Ninguna se vuelve a entregar, y no se mata ningun proceso."""
    proy = _proyecto(_unidades("uno", "dos"))
    huerfanas = _huerfanas(proy, [("uno", None), ("dos", None)])
    for unidad, (carpeta, _) in huerfanas.items():
        if carpeta is not None:
            (carpeta / registro.OUTPUT).write_text("# quedo a medias\n", encoding="utf-8")
    carpeta_uno = huerfanas["uno"][0]
    if carpeta_uno is not None:
        registro.escribir_json(str(carpeta_uno / registro.CANCELACION),
                               {"pedidoEn": registro.ahora(), "pedidoPor": "Otra persona"})
    ecos = dict((u, M64._bytes(_eco(proy, "eco-" + u))) for u in huerfanas)
    motor.recuperar(str(proy), CLAVE)
    for unidad, estado, codigo in (("uno", "CANCELLED", "CANCELLED"),
                                   ("dos", "FAILED", "HOST_INTERRUPTED")):
        carpeta, pid = huerfanas[unidad]
        eid = carpeta.name if carpeta else "exe_" + "0" * 32
        res = registro.estado(str(proy), CLAVE, eid)["resultado"] or {}
        entrega = M64._leer_json(carpeta / registro.ENTREGA) if carpeta else {}
        t.igual("ME-E53 %s queda %s con %s" % ("la del pedido" if unidad == "uno" else "la otra",
                                               estado, codigo),
                (estado, codigo), (res.get("status"), (res.get("error") or {}).get("code")))
        t.igual("ME-E53 %s: startedAt de entrega.json" % unidad, entrega.get("deliveredAt"),
                res.get("startedAt"))
        t.verdadero("ME-E53 %s: con evidencia" % unidad, res.get("evidence"))
        t.verdadero("ME-E53 %s: sin agentDeclaredStatus ni output, aunque quedo output.md" % unidad,
                    res and res.get("agentDeclaredStatus") is None and res.get("output") is None)
        t.igual("ME-E53 %s: no se volvio a entregar" % unidad, ecos[unidad],
                M64._bytes(_eco(proy, "eco-" + unidad)))
        t.verdadero("ME-E53 %s: no se mato al Host" % unidad, pid and proceso.pid_vivo(pid))
        _terminar(pid)


def _junction(enlace, destino):
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(enlace), str(destino)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.symlink(str(destino), str(enlace))
    return Path(enlace).exists()


def test_me_e23_la_ruta_canonica(t):
    """ME-E23 — Una ruta de evidencia o de output que no es canonica no se persiste; dos que solo
    difieren en mayusculas cuentan como repetidas en Windows."""
    proy = M64._tmp("me72-rutas-")
    (proy / "src").mkdir()
    (proy / "src" / "a.py").write_text("x\n", encoding="utf-8")
    afuera = M64._tmp("me72-afuera-")
    (afuera / "x.txt").write_text("afuera\n", encoding="utf-8")
    t.verdadero("ME-E23 se armo un enlace que sale del proyecto", _junction(proy / "fuera", afuera))
    malas = ["./a", "a/./b", "a//b", "a/", ".", "~/x", "file:///x", "C:/x", "\\\\srv\\x", "../x",
             "fuera/x.txt", "", "a\nb"]
    t.vacio("ME-E23 ninguna ruta no canonica pasa",
            [r for r in malas if registro.ruta_mala(str(proy), r) is None])
    t.vacio("ME-E23 una ruta canonica pasa", registro.ruta_mala(str(proy), "src/a.py"))
    foto = {"ok": True, "revision": None, "sucios": {}}
    for ruta in ("./a", "fuera/x.txt"):
        ev = evidencia.armar(str(proy), foto, {"ok": True, "revision": None,
                                               "sucios": {ruta: "sha256:" + "a" * 64}})
        t.igual("ME-E23 %s no se persiste: la evidencia queda CHANGES_UNRESOLVED" % ruta,
                ("CHANGES_UNRESOLVED", []), (ev["changes"]["state"], ev["changes"]["files"]))
    dobles = registro.repetidas(["src/A.py", "src/a.py"])
    if sys.platform in ("win32", "darwin"):
        t.igual("ME-E23 en Windows, dos rutas que difieren en mayusculas son repetidas", ["src/a.py"],
                dobles)
    else:
        t.igual("ME-E23 en Linux no lo son", [], dobles)


def test_me_e24_se_redacta_lo_que_se_persiste(t):
    """ME-E24 — fortalecido en §34.4: un artifact con un secreto se guarda redactado en output.md, con
    la huella del texto redactado; un requestedBy con un secreto queda redactado en request.json y
    requestFingerprint es la huella de esa request; un detail con un secreto se redacta, tambien si el
    secreto empieza despues del caracter 166 de stderr, y un structured_output invalido con un secreto
    no lo deja en el detail, con catalogo o sin el; si la redaccion cambiaria la workUnit,
    CONTRACT_INVALID sin Execution."""
    proy = _proyecto(_unidades("uno", "dos", "tres", "cuatro", "cinco", "seis", "siete"))
    _guion(proy, resultado=_informe("COMPLETE", "# Informe\nEl token es " + SECRETO + "\n"))
    corrida = _corrida(proy, "uno", pedido_por="Ana " + SECRETO)
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    salida = _carpeta(proy, eid) / registro.OUTPUT
    texto = salida.read_text(encoding="utf-8") if salida.is_file() else ""
    t.no_contiene("ME-E24 output.md no tiene el secreto", SECRETO, texto)
    t.contiene("ME-E24 output.md lo dice redactado", "secreto redactado", texto)
    t.igual("ME-E24 la huella del output es la del texto redactado",
            _sha(salida) if salida.is_file() else "", (_de(corrida, "output") or {}).get("fingerprint"))
    pedido = (_carpeta(proy, eid) / registro.REQUEST)
    crudo = pedido.read_text(encoding="utf-8") if pedido.is_file() else SECRETO
    t.no_contiene("ME-E24 request.json no tiene el secreto del requestedBy", SECRETO, crudo)
    t.igual("ME-E24 requestFingerprint es la huella de la request redactada",
            C.huella(json.loads(crudo)) if pedido.is_file() else None,
            _de(corrida, "requestFingerprint"))
    _guion(proy, sin_json="", stderr="fallo con el token " + SECRETO, salida=1)
    corrida = _corrida(proy, "dos")
    detalle = ((corrida["res"] or {}).get("error") or {}).get("detail") or ""
    t.igual("ME-E24 una falla del Host con un secreto en stderr", "HOST_FAILURE", _codigo(corrida))
    t.no_contiene("ME-E24 el detail no lleva el secreto", SECRETO, detalle)
    t.contiene("ME-E24 y lo dice redactado", "secreto redactado", detalle)

    # El secreto empieza despues del caracter 166 de stderr: recortar antes de redactar lo partia
    # y lo dejaba pasar (la refutacion del 09-10-2026).
    _guion(proy, sin_json="", stderr="x" * 170 + " token " + SECRETO, salida=1)
    corrida = _corrida(proy, "cuatro")
    detalle = ((corrida["res"] or {}).get("error") or {}).get("detail") or ""
    t.igual("ME-E24 stderr con el secreto despues del corte: HOST_FAILURE", "HOST_FAILURE",
            _codigo(corrida))
    t.no_contiene("ME-E24 ni un pedazo del secreto despues del corte llega al detail", FUGA, detalle)

    estado = {"sin": False}

    def catalogo():
        return None if estado["sin"] else limpieza.cargar_catalogo()

    def perder(_carpeta):
        estado["sin"] = True

    casos = (("cinco", "un secreto como clave de mas, con catalogo",
              {"declaredStatus": "COMPLETE", "artifact": "x", SECRETO: 1}, False),
             ("seis", "un secreto como clave de mas, sin catalogo",
              {"declaredStatus": "COMPLETE", "artifact": "x", SECRETO: 1}, True),
             ("siete", "un secreto como declaredStatus, sin catalogo",
              {"declaredStatus": SECRETO, "artifact": "x"}, True))
    for unidad, que, informe, sin_catalogo in casos:
        estado["sin"] = False
        _guion(proy, resultado={"structured_output": informe})
        corrida = _corrida(proy, unidad, catalogo=catalogo,
                           antes_de_entregar=perder if sin_catalogo else None)
        detalle = ((corrida["res"] or {}).get("error") or {}).get("detail") or ""
        t.igual("ME-E24 %s: OUTPUT_INVALID" % que, "OUTPUT_INVALID", _codigo(corrida))
        t.no_contiene("ME-E24 %s: el detail no lo lleva" % que, FUGA, detalle)

    from estado_de_tarea import persistencia
    _reescribir_plan(proy, lambda p: next(u for u in p["workUnits"] if u["id"] == "tres").update(
        objective="hacer tres con " + SECRETO))
    persistencia.reconciliar(str(proy), CLAVE)
    antes = _arbol(proy)
    corrida = _corrida(proy, "tres")
    t.igual("ME-E24 si la redaccion cambiaria la workUnit: CONTRACT_INVALID", "CONTRACT_INVALID",
            _codigo(corrida))
    t.igual("ME-E24 y no se crea la Execution", antes, _arbol(proy))


def test_me_e35_el_estado_solo_lee(t):
    """ME-E35 — --estado no escribe ningun archivo; lista los turnos con su estado derivado, marca una
    huerfana sin cerrarla e informa como ilegible una Execution cuyo result.json no valida, que
    ademas cuenta como abierta para los duplicados."""
    proy = _proyecto(_unidades("uno", "dos", "tres", "cuatro"))
    _guion(proy)
    bien = _corrida(proy, "uno")
    rota = _corrida(proy, "tres")
    eid_rota = _de(rota, "executionId") or "exe_" + "0" * 32
    ruta = _carpeta(proy, eid_rota) / registro.RESULT
    doc = M64._leer_json(ruta) if ruta.is_file() else {}
    doc["status"] = "FAILED"
    ruta.unlink()
    ruta.write_text(json.dumps(doc), encoding="utf-8")
    catalogo = limpieza.cargar_catalogo()
    request, _, leido, _ = admision.al_pedir(str(proy), CLAVE, "dos", PIDE, catalogo)
    vida = registro.crear(str(proy), request, leido)
    vida.soltar()
    residuo, _ = _residuo(proy, "cuatro")
    _viejo(residuo / registro.VIVO, residuo)

    antes = _arbol(proy)
    filas = motor.estado(str(proy), CLAVE)
    codigo, salida, _ = M64._cli(["ejecutar", CLAVE, "--estado", "--json", "--proyecto", proy])
    t.igual("ME-E35 --estado no escribe ningun archivo", antes, _arbol(proy))
    t.igual("ME-E35 y sale con 0", 0, codigo)
    try:
        por_cli = json.loads(salida)
    except ValueError:
        por_cli = None
    t.igual("ME-E35 el CLI muestra lo mismo que la API", filas, por_cli)
    por_id = dict((f["executionId"], f) for f in filas)
    t.igual("ME-E35 lista los turnos con su estado derivado", "SUCCEEDED",
            (por_id.get(_de(bien, "executionId")) or {}).get("estado"))
    huerfana = por_id.get(request["executionId"]) or {}
    t.igual("ME-E35 la huerfana sigue REQUESTED", "REQUESTED", huerfana.get("estado"))
    t.verdadero("ME-E35 marcada como sospechada", huerfana.get("huerfana") is True)
    ilegible = por_id.get(eid_rota) or {}
    t.igual("ME-E35 informa como ilegible la de result.json roto", "ILEGIBLE", ilegible.get("estado"))
    t.contiene("ME-E35 y dice por que", "result.json", ilegible.get("motivo"))
    t.verdadero("ME-E35 el residuo sin turno no aparece", residuo.name not in por_id)
    corrida = _corrida(proy, "tres")
    t.igual("ME-E35 la ilegible cuenta como abierta para los duplicados", "DUPLICATE_EXECUTION",
            _codigo(corrida))


# =============================================================================================
# Evidencia
# =============================================================================================

def test_me_e25_el_repo_sucio(t):
    """ME-E25 — Con el repo sucio: si el Host cambia solo archivos limpios, RESOLVED con esos y sin
    los sucios; si cambia uno que ya estaba sucio, CHANGES_UNATTRIBUTABLE con files vacio. El motor
    no limpia ni resetea nada."""
    proy = _proyecto(_unidades("uno", "dos"))
    sucio = Path(proy) / "src" / "app.py"
    sucio.write_text("VALOR = 2  # a mano, sin commitear\n", encoding="utf-8")
    antes = sucio.read_bytes()
    _guion(proy, cambios=[{"ruta": "src/viejo.py", "contenido": "VIEJO = 2\n"}])
    corrida = _corrida(proy, "uno")
    cambios = (_de(corrida, "evidence") or {}).get("changes") or {}
    t.igual("ME-E25 el Host cambio solo un archivo limpio: RESOLVED", "RESOLVED", cambios.get("state"))
    t.igual("ME-E25 con ese archivo y sin el sucio",
            [("src/viejo.py", "MODIFIED", _sha(Path(proy) / "src" / "viejo.py"))],
            [(f["path"], f["change"], f["fingerprint"]) for f in cambios.get("files") or []])
    t.igual("ME-E25 el sucio que no se toco quedo igual", antes, sucio.read_bytes())
    _guion(proy, cambios=[{"ruta": "src/app.py", "contenido": "VALOR = 3\n"}])
    corrida = _corrida(proy, "dos")
    cambios = (_de(corrida, "evidence") or {}).get("changes") or {}
    t.igual("ME-E25 el Host cambio uno que ya estaba sucio: CHANGES_UNATTRIBUTABLE con files vacio",
            ("CHANGES_UNATTRIBUTABLE", []), (cambios.get("state"), cambios.get("files")))
    t.igual("ME-E25 y el motor no lo reseteo", b"VALOR = 3\n", sucio.read_bytes())


def test_me_e43_sin_git_y_con_un_commit(t):
    """ME-E43 — Sin git, la evidencia es CHANGES_UNRESOLVED con files vacio. Con un commit del Host,
    los archivos del commit estan en files y las dos revisiones difieren."""
    suelto = M64._tmp("me72-sin-git-")
    (suelto / "a.txt").write_text("a\n", encoding="utf-8")
    foto = evidencia.instantanea(str(suelto))
    ev = evidencia.armar(str(suelto), foto, evidencia.instantanea(str(suelto)))
    t.igual("ME-E43 fuera de un repositorio: CHANGES_UNRESOLVED con files vacio",
            ("CHANGES_UNRESOLVED", []), (ev["changes"]["state"], ev["changes"]["files"]))
    proy = _proyecto()
    _guion(proy, cambios=[{"ruta": "src/nuevo.py", "contenido": "NUEVO = 1\n"},
                          {"ruta": "src/viejo.py", "contenido": "VIEJO = 3\n"}], commit=True)
    corrida = _corrida(proy)
    ev = _de(corrida, "evidence") or {}
    t.verdadero("ME-E43 con un commit del Host las dos revisiones difieren",
                ev.get("repoRevisionBefore") and ev.get("repoRevisionAfter")
                and ev["repoRevisionBefore"] != ev["repoRevisionAfter"])
    t.igual("ME-E43 y los archivos del commit estan en files",
            [("src/nuevo.py", "ADDED"), ("src/viejo.py", "MODIFIED")],
            [(f["path"], f["change"]) for f in (ev.get("changes") or {}).get("files") or []])
    t.igual("ME-E43 RESOLVED", "RESOLVED", (ev.get("changes") or {}).get("state"))


def test_me_e44_otra_execution_corriendo(t):
    """ME-E44 — Con otra Execution del mismo proyecto RUNNING durante la corrida, la evidencia es
    CHANGES_UNATTRIBUTABLE."""
    proy = _proyecto(_unidades("uno", "dos"))
    guion = _guion(proy, "guion-dos", dormir=30)
    hijo, _ = _lanzar_motor(proy, "dos", guion=guion)
    t.verdadero("ME-E44 la otra esta RUNNING", _esperar(lambda: _corriendo_de(proy, "dos")))
    _guion(proy, cambios=[{"ruta": "src/viejo.py", "contenido": "VIEJO = 9\n"}])
    corrida = _corrida(proy, "uno")
    t.igual("ME-E44 la evidencia es CHANGES_UNATTRIBUTABLE", "CHANGES_UNATTRIBUTABLE",
            (((_de(corrida, "evidence") or {}).get("changes")) or {}).get("state"))
    carpeta = _corriendo_de(proy, "dos")
    if carpeta is not None:
        motor.cancelar(str(proy), CLAVE, carpeta.name, PIDE)
    _salida_del_hijo(hijo)
    otro = _proyecto(_unidades("uno", "dos"))
    _guion(otro)
    primera = _corrida(otro, "uno")
    _guion(otro, cambios=[{"ruta": "src/viejo.py", "contenido": "VIEJO = 8\n"}])
    segunda = _corrida(otro, "dos")
    t.igual("ME-E44 una que termino antes de la entrega, aunque en el mismo segundo, no cuenta",
            ("SUCCEEDED", "RESOLVED"),
            (_de(primera, "status"),
             (((_de(segunda, "evidence") or {}).get("changes")) or {}).get("state")))


# =============================================================================================
# Flow Governance y el Host
# =============================================================================================

def _argv(proy, eco):
    return (_leer_eco(eco) or {}).get("argv") or []


def test_me_e38_el_modelo_por_perfil(t):
    """ME-E38 — Con modelRouting.perfiles[<requiredTier>] declarado, el adaptador pasa --model con ese
    perfil; sin declarar, no. Nunca --max-budget-usd. El tier sale de la unidad y no entra al
    request."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    tier = plan["workUnits"][0]["modelPolicy"]["requiredTier"]
    casos = (("uno", {"perfiles": {tier: "modelo-del-perfil"}}, ["--model", "modelo-del-perfil"]),
             ("dos", {"perfiles": {tier: ""}}, None),
             ("tres", None, None))
    for unidad, ruteo, esperado in casos:
        if ruteo is None:
            _config(proy)
        else:
            _config(proy, modelRouting=ruteo)
        eco = _eco(proy, "eco-" + unidad)
        _guion(proy, eco=str(eco))
        corrida = _corrida(proy, unidad)
        argv = _argv(proy, eco)
        if esperado:
            i = argv.index("--model") if "--model" in argv else -1
            t.igual("ME-E38 con el perfil declarado pasa --model con el perfil", esperado,
                    argv[i:i + 2] if i >= 0 else [])
        else:
            t.verdadero("ME-E38 sin perfil declarado (%s) no pasa --model" % unidad,
                        argv and "--model" not in argv)
        t.verdadero("ME-E38 nunca --max-budget-usd (%s)" % unidad, argv and
                    "--max-budget-usd" not in argv)
        request = M64._leer_json(_carpeta(proy, _de(corrida, "executionId") or "exe_" + "0" * 32)
                                 / registro.REQUEST) if corrida["res"] else {}
        afuera = dict((k, v) for k, v in request.items() if k != "workUnit")
        t.vacio("ME-E38 el tier no entra al request fuera de la unidad (%s)" % unidad,
                [k for k in re.findall(r'"([A-Za-z]+)"', json.dumps(afuera))
                 if k.lower() in ("tier", "requiredtier", "model", "modelo")])
    _config(proy)


def _task_binding():
    hooks = RAIZ / "comun" / "hooks"
    if str(hooks) not in sys.path:
        sys.path.insert(0, str(hooks))
    return importlib.import_module("lib.task_binding")


def test_me_e39_los_argumentos_del_host(t):
    """ME-E39 — enmendado en §34.4: los argumentos nunca tienen --bare,
    --dangerously-skip-permissions, --allow-dangerously-skip-permissions, bypassPermissions ni
    --agent, y siempre tienen -p, --output-format json, --json-schema, --session-id, --permission-mode
    dontAsk, --permission-prompts none, --system-prompt-file con el cuerpo del agente, --tools,
    --allowedTools y --strict-mcp-config. Una configuracion que intente meter una de esas banderas por
    comandoHost o por un perfil de modelo falla con exit 2 antes de crear la Execution. La primera
    linea del prompt hace que task_binding.clave_declarada devuelva la TaskKey."""
    proy = _proyecto()
    eco = _eco(proy)
    _guion(proy, eco=str(eco))
    corrida = _corrida(proy)
    argv = _argv(proy, eco)
    t.verdadero("ME-E39 el Host recibio sus argumentos", argv)
    t.vacio("ME-E39 nunca --bare, saltear permisos ni --agent",
            [a for a in argv if a.lower() in ("--bare", "--dangerously-skip-permissions",
                                              "--allow-dangerously-skip-permissions", "--agent",
                                              "--agents")
             or "bypasspermissions" in a.lower()])
    pares = [argv[i:i + 2] for i in range(len(argv))]
    for par in (["--permission-mode", "dontAsk"], ["--permission-prompts", "none"],
                ["--output-format", "json"]):
        t.verdadero("ME-E39 tiene %s" % " ".join(par), par in pares)
    for bandera in ("-p", "--json-schema", "--session-id", "--system-prompt-file", "--tools",
                    "--allowedTools", "--strict-mcp-config"):
        t.verdadero("ME-E39 tiene %s" % bandera, bandera in argv)
    cuerpo = _cuerpo_del_agente(proy)
    t.verdadero("ME-E39 el agente tiene texto", cuerpo and "dev-backend" in cuerpo)
    t.igual("ME-E39 el prompt de sistema es el cuerpo del agente, sin su frente", cuerpo,
            (_leer_eco(eco) or {}).get("sistema"))
    eid = _de(corrida, "executionId") or "exe_" + "0" * 32
    guardado = _carpeta(proy, eid) / H.PROMPT_DE_SISTEMA
    t.igual("ME-E39 y queda en el registro de la Execution", cuerpo,
            guardado.read_text(encoding="utf-8") if guardado.is_file() else None)
    entrada = (_leer_eco(eco) or {}).get("stdin") or ""
    t.igual("ME-E39 la primera linea del prompt vincula la sesion a la TaskKey", CLAVE,
            _task_binding().clave_declarada(entrada))
    t.igual("ME-E39 es Seguimos con <KEY>.", "Seguimos con %s." % CLAVE, entrada.split("\n")[0])

    unidades = ["a%02d" % i for i in range(len(ADVERSARIAS))]
    otro = _proyecto(_unidades(*unidades))
    plan = M64._leer_json(M64._plan_de(otro, CLAVE))
    tier = plan["workUnits"][0]["modelPolicy"]["requiredTier"]
    _guion(otro)
    for unidad, (que, extra, perfil) in zip(unidades, ADVERSARIAS):
        _config(otro, {"comandoHost": [sys.executable, str(HOST)] + extra, "limiteSegundos": 60},
                **({"modelRouting": {"perfiles": {tier: perfil}}} if perfil else {}))
        antes = _arbol(otro)
        codigo, salida, error = M64._cli(["ejecutar", CLAVE, "--unidad", unidad, "--json",
                                          "--proyecto", otro])
        try:
            doc = json.loads(salida) if salida.strip() else None
        except ValueError:
            doc = None
        t.igual("ME-E39 %s: sale con 2" % que, 2, codigo)
        t.verdadero("ME-E39 %s: falla antes de crear la Execution" % que,
                    antes == _arbol(otro) and _turnos(otro, unidad) == []
                    and not (isinstance(doc, dict) and "code" in doc))
    _config(otro)


def _shim(carpeta, nombre="host-falso.cmd"):
    """Un shim .cmd como el de npm, que llama al Host falso con %*."""
    ruta = Path(carpeta) / nombre
    ruta.write_text('@"%s" "%s" %%*\r\n' % (sys.executable, HOST), encoding="utf-8")
    return ruta


def test_me_e40_las_herramientas_y_el_shim(t):
    """ME-E40 — enmendado en §34.4: --tools y --allowedTools llevan el mismo conjunto, la union de
    las herramientas de las capabilities de la unidad, intersecada con el tools: del agente, mas
    Skill si la tiene. El schema llega intacto a traves de un shim .cmd y el Host lo parsea como
    JSON. El prompt llega por stdin."""
    adaptador = H.Adaptador([sys.executable, str(HOST)], 60)
    backend = {"tools": ["Read", "Glob", "Grep", "Edit", "Write", "Bash", "Skill"]}
    arquitectura = {"tools": ["Read", "Glob", "Grep", "Skill"]}
    for capacidades, definicion, esperado in (
            (["repository.read"], backend, ["Read", "Glob", "Grep", "Skill"]),
            (["repository.write"], backend, ["Edit", "Write", "Skill"]),
            (["tests.run", "repository.search"], backend, ["Glob", "Grep", "Bash", "Skill"]),
            (["repository.read", "repository.write"], arquitectura, ["Read", "Glob", "Grep", "Skill"]),
            (["repository.read"], {"tools": ["Read", "Glob", "Grep"]}, ["Read", "Glob", "Grep"])):
        t.igual("ME-E40 %s con %s" % ("+".join(capacidades), ",".join(definicion["tools"])), esperado,
                adaptador.herramientas(capacidades, definicion))
    proy = _proyecto()
    eco = _eco(proy)
    _guion(proy, eco=str(eco))
    if os.name == "nt":
        _config(proy, {"comandoHost": [str(_shim(_shim_dir(proy)))], "limiteSegundos": 60})
    corrida = _corrida(proy)
    argv = _argv(proy, eco)
    t.igual("ME-E40 la corrida llego al Host por %s" % ("el shim .cmd" if os.name == "nt" else "el comando"),
            "SUCCEEDED", _de(corrida, "status"))
    for bandera in ("--tools", "--allowedTools"):
        i = argv.index(bandera) if bandera in argv else -1
        t.igual("ME-E40 %s es el conjunto de la unidad con el tools: de dev-backend" % bandera,
                "Read,Glob,Grep,Skill", argv[i + 1] if i >= 0 else None)
    j = argv.index("--json-schema") if "--json-schema" in argv else -1
    try:
        esquema = json.loads(argv[j + 1]) if j >= 0 else None
    except ValueError:
        esquema = "no es JSON: " + argv[j + 1]
    t.igual("ME-E40 el schema llega intacto y el Host lo parsea como JSON", H.esquema_del_informe(),
            esquema)
    entrada = (_leer_eco(eco) or {}).get("stdin") or ""
    t.verdadero("ME-E40 el prompt llega por stdin", entrada.startswith("Seguimos con %s." % CLAVE)
                and "analizar-api" in entrada)
    t.vacio("ME-E40 y no por argv", [a for a in argv if "Seguimos con" in a])
    _config(proy)


def _shim_dir(proy):
    carpeta = Path(proy).parent / ("%s-shim" % Path(proy).name)
    carpeta.mkdir(exist_ok=True)
    return carpeta


def test_me_e45_el_motor_no_reconcilia(t):
    """ME-E45 — Una corrida entera no cambia state.json ni active-task.json. Con state.json ausente,
    la admision da DELEGATION_NOT_ALLOWED y el detail dice como reconciliar. La admision no necesita
    una sesion."""
    proy = _proyecto(_unidades("uno", "dos"))
    _guion(proy)
    runtime = Path(proy) / ".claude" / "runtime"
    estado = runtime / "tasks" / CLAVE / "state.json"
    activa = runtime / "active-task.json"
    antes = (M64._bytes(estado), M64._bytes(activa))
    corrida = _corrida(proy, "uno")
    t.igual("ME-E45 la corrida termino", "SUCCEEDED", _de(corrida, "status"))
    t.igual("ME-E45 state.json y active-task.json no cambiaron", antes,
            (M64._bytes(estado), M64._bytes(activa)))
    t.verdadero("ME-E45 sin ninguna sesion: no hay vinculos de sesion en el proyecto",
                not (runtime / "sessions").exists())
    estado.unlink()
    corrida = _corrida(proy, "dos")
    t.igual("ME-E45 sin state.json: DELEGATION_NOT_ALLOWED", "DELEGATION_NOT_ALLOWED",
            _codigo(corrida))
    t.contiene("ME-E45 y el detail dice como reconciliar", "flujo %s --status" % CLAVE,
               (corrida["err"] or {}).get("detail"))
    t.verdadero("ME-E45 y el motor no lo recreo", not estado.exists())


# =============================================================================================
# La configuracion del motor
# =============================================================================================

def _claude_falso():
    """Una carpeta con un `claude` falso, que llama al Host falso: va primera en el PATH."""
    carpeta = M64._tmp("me72-path-")
    if os.name == "nt":
        (carpeta / "claude.cmd").write_text('@"%s" "%s" %%*\r\n' % (sys.executable, HOST),
                                            encoding="utf-8")
    else:
        ruta = carpeta / "claude"
        ruta.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, HOST), encoding="utf-8")
        os.chmod(str(ruta), 0o755)
    return carpeta


def _con_path(carpeta, accion, solo=False):
    previo = os.environ.get("PATH", "")
    os.environ["PATH"] = str(carpeta) if solo else str(carpeta) + os.pathsep + previo
    try:
        return accion()
    finally:
        os.environ["PATH"] = previo


def _falla_antes(t, eid, que, proy):
    codigo, salida, error = M64._cli(["ejecutar", CLAVE, "--unidad", "analizar-api", "--json",
                                      "--proyecto", proy])
    t.igual("%s %s: sale con 2" % (eid, que), 2, codigo)
    t.verdadero("%s %s: no queda nada bajo .claude/ejecuciones" % (eid, que),
                not _ejecuciones(proy).exists())
    try:
        doc = json.loads(salida) if salida.strip() else None
    except ValueError:
        doc = None
    t.verdadero("%s %s: la salida no es un ExecutionError" % (eid, que),
                not (isinstance(doc, dict) and "code" in doc))
    t.contiene("%s %s: lo dice el comando" % (eid, que), "harness:", error)


def test_me_e54_el_comando_del_host(t):
    """ME-E54 — ejecucion.comandoHost: ausente, el motor usa shutil.which("claude"); presente y
    valido, ese; presente e invalido (lista vacia, texto suelto, elemento vacio, programa que no
    existe), exit 2 antes de crear la Execution. Ausente y sin claude en el PATH, tambien. Sin
    carpeta, turno, temporal ni result.json, y la salida no es un ExecutionError."""
    proy = _proyecto(config=False)
    falso = _claude_falso()
    _config(proy, {})
    config = _con_path(falso, lambda: motor.configuracion(str(proy)))
    t.igual("ME-E54 ausente: usa lo que da shutil.which(\"claude\")",
            os.path.normcase(_con_path(falso, lambda: shutil.which("claude"))),
            os.path.normcase(config["comando"][0]))
    _config(proy)
    t.igual("ME-E54 presente y valido: usa ese comando", [sys.executable, str(HOST)],
            motor.configuracion(str(proy))["comando"])
    for que, comando in (("una lista vacia", []), ("un texto suelto", "claude -p"),
                         ("un elemento vacio", ["", str(HOST)]),
                         ("un programa que no existe", ["programa-que-no-existe-72"])):
        _config(proy, {"comandoHost": comando, "limiteSegundos": 60})
        _con_path(falso, lambda: _falla_antes(t, "ME-E54", que, proy))
    _config(proy, {})
    vacia = M64._tmp("me72-path-vacio-")
    _con_path(vacia, lambda: _falla_antes(t, "ME-E54", "ausente y sin claude en el PATH", proy),
              solo=True)
    _config(proy)


def test_me_e55_el_limite_del_motor(t):
    """ME-E55 — ejecucion.limiteSegundos: ausente, 1800; un entero positivo, ese; 0, -5, "60", true o
    1.5, exit 2 antes de crear la Execution. Un harness.config.json que no es un objeto JSON legible
    tambien falla antes, sin caer al default."""
    proy = _proyecto(config=False)
    falso = _claude_falso()
    _config(proy, {"comandoHost": [sys.executable, str(HOST)]})
    t.igual("ME-E55 ausente: 1800", 1800, motor.configuracion(str(proy))["limite"])
    _config(proy, {"comandoHost": [sys.executable, str(HOST)], "limiteSegundos": 45})
    t.igual("ME-E55 un entero positivo: ese", 45, motor.configuracion(str(proy))["limite"])
    for valor in (0, -5, "60", True, 1.5):
        _config(proy, {"comandoHost": [sys.executable, str(HOST)], "limiteSegundos": valor})
        _con_path(falso, lambda: _falla_antes(t, "ME-E55", "limiteSegundos %r" % (valor,), proy))
    config = Path(proy) / ".claude" / "harness.config.json"
    for que, texto in (("un harness.config.json que no es un objeto", "[1, 2]"),
                       ("un harness.config.json roto", "{roto")):
        config.write_text(texto, encoding="utf-8")
        _con_path(falso, lambda: _falla_antes(t, "ME-E55", que, proy))
    _config(proy)


# =============================================================================================
# Instalacion, alcance y documentos
# =============================================================================================

BASE = "fdca5ce"
ESCRITURAS = ("os.replace", "os.rename", "os.makedirs", "os.mkdir", "os.remove", "os.unlink",
              "os.rmdir", "os.system", "os.link", "os.write", "os.symlink", "os.truncate",
              "tempfile.mkstemp", "tempfile.mkdtemp", "shutil.rmtree", "shutil.copy",
              "shutil.copy2", "shutil.copyfile", "shutil.copytree", "shutil.move")


def _nombre(nodo):
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return _nombre(nodo.value) + "." + nodo.attr
    return ""


def _escribe(ruta):
    """Las llamadas de un fuente que escriben en disco: [(linea, que)]."""
    salida = []
    for n in ast.walk(ast.parse(Path(ruta).read_text(encoding="utf-8"))):
        if not isinstance(n, ast.Call):
            continue
        nombre = _nombre(n.func)
        if nombre in ESCRITURAS or nombre.split(".")[-1] in ("write", "write_text", "write_bytes",
                                                             "writelines", "dump", "touch"):
            salida.append((n.lineno, nombre))
        if nombre.split(".")[-1] == "open" and nombre != "os.open":
            modo = n.args[1] if len(n.args) > 1 else next(
                (k.value for k in n.keywords if k.arg == "mode"), None)
            if modo is not None and not (isinstance(modo, ast.Constant)
                                         and set(str(modo.value)) <= set("rbt")):
                salida.append((n.lineno, "open para escribir"))
        if nombre == "os.open" and any("O_CREAT" in _nombre(x) or "O_WRONLY" in _nombre(x)
                                       or "O_RDWR" in _nombre(x)
                                       for a in n.args[1:] for x in ast.walk(a)):
            salida.append((n.lineno, "os.open para escribir"))
    return salida


def _importados(ruta):
    salida = set()
    for n in ast.walk(ast.parse(Path(ruta).read_text(encoding="utf-8-sig"))):
        if isinstance(n, ast.Import):
            salida |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                salida.add(n.module.split(".")[0])
            salida |= {a.name for a in n.names}
    return salida


def _py(carpeta):
    return sorted(p for p in Path(carpeta).rglob("*.py") if "__pycache__" not in p.parts)


def _proyecto_sin_git(proy):
    salida = {}
    for p in sorted(Path(proy).rglob("*")):
        rel = p.relative_to(proy).as_posix()
        if rel == ".git" or rel.startswith(".git/") or not p.is_file():
            continue
        salida[rel] = "candado" if p.name == registro.VIVO else hashlib.sha256(
            p.read_bytes()).hexdigest()
    return salida


def test_me_e46_que_escribe_cada_modulo(t):
    """ME-E46 — contrato.py no escribe, no lanza procesos y no importa la refutacion ni la
    contabilidad; ningun modulo de bin/ejecucion/ importa contabilidad ni lee .claude/runtime/
    accounting; los modulos que escriben lo hacen solo bajo .claude/ejecuciones/."""
    contrato_py = EJECUCION / "contrato.py"
    t.vacio("ME-E46 contrato.py no escribe", _escribe(contrato_py))
    t.vacio("ME-E46 contrato.py no lanza procesos ni importa la refutacion ni la contabilidad",
            sorted(_importados(contrato_py) & {"subprocess", "refutacion", "contabilidad",
                                                "orquestacion"}))
    t.vacio("ME-E46 ningun modulo de bin/ejecucion/ importa contabilidad",
            [p.name for p in _py(EJECUCION) if "contabilidad" in _importados(p)])
    t.vacio("ME-E46 ni nombra .claude/runtime/accounting",
            ["%s: %s" % (p.name, n.value) for p in _py(EJECUCION)
             for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and re.search(r"(^|[\\/])accounting([\\/]|$)|^accounting$", n.value)])
    fuera = ["%s:%d %s" % (p.name, linea, que) for p in _py(EJECUCION)
             if p.name not in ("registro.py",) for linea, que in _escribe(p)
             if not (p.name == "host_claude_code.py" and que == "entrada.write")]
    t.vacio("ME-E46 fuera de registro.py nada escribe en disco (salvo el prompt, a un temporal "
            "anonimo del sistema)", fuera)
    t.igual("ME-E46 registro.py escribe bajo .claude/ejecuciones", (".claude", "ejecuciones"),
            registro.RAIZ)
    arbol = ast.parse((EJECUCION / "registro.py").read_text(encoding="utf-8"))
    raices = [n for n in ast.walk(arbol) if isinstance(n, ast.Call)
              and _nombre(n.func) == "os.path.join" and n.args
              and isinstance(n.args[0], ast.Name) and n.args[0].id == "proyecto"]
    t.vacio("ME-E46 y toda ruta del proyecto que arma registro.py empieza en .claude/ejecuciones",
            [n.lineno for n in raices if len(n.args) < 2 or not isinstance(n.args[1], ast.Starred)
             or "RAIZ" not in ast.dump(n.args[1])])
    proy = _proyecto()
    _guion(proy)
    antes = _proyecto_sin_git(proy)
    corrida = _corrida(proy)
    t.igual("ME-E46 la corrida termino", "SUCCEEDED", _de(corrida, "status"))
    distintos = M64._diferencias(antes, _proyecto_sin_git(proy))
    t.vacio("ME-E46 en el proyecto cambio solo .claude/ejecuciones (y la agenda de la compuerta "
            "normativa, que es suya)",
            [d for d in distintos if not d.split(" ", 1)[1].startswith(".claude/ejecuciones/")
             and d.split(" ", 1)[1] != ".claude/runtime/knowledge-refresh.json"])


PROHIBIDOS = ("threading", "multiprocessing", "asyncio", "concurrent", "sched", "queue")
MODELOS = ("anthropic", "openai", "langchain", "langgraph", "claude_agent_sdk")


def _subcomandos():
    for n in ast.walk(ast.parse(CLI.read_text(encoding="utf-8"))):
        if (isinstance(n, ast.Call) and _nombre(n.func).endswith("add_argument") and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == "comando"):
            for k in n.keywords:
                if k.arg == "choices":
                    return list(ast.literal_eval(k.value))
    return None


def test_me_e47_una_corrida_por_invocacion(t):
    """ME-E47 — Nada de bin/ ni de comun/ importa threading, multiprocessing, asyncio, concurrent,
    sched, queue, un SDK de modelos ni LangGraph. dev-harness.py tiene trece subcomandos, con
    ejecutar. claude solo lo lanza host_claude_code.py (E-41 adaptado)."""
    fuentes = _py(BIN) + _py(RAIZ / "comun")
    t.vacio("ME-E47 nada importa concurrencia",
            ["%s: %s" % (p.relative_to(RAIZ).as_posix(), m) for p in fuentes
             for m in sorted(_importados(p) & set(PROHIBIDOS))])
    t.vacio("ME-E47 ni un SDK de modelos, LangChain o LangGraph",
            ["%s: %s" % (p.relative_to(RAIZ).as_posix(), m) for p in fuentes
             for m in sorted(_importados(p) & set(MODELOS))])
    subcomandos = _subcomandos() or []
    t.igual("ME-E47 dev-harness.py tiene trece subcomandos", 13, len(subcomandos))
    t.verdadero("ME-E47 con ejecutar", "ejecutar" in subcomandos)
    lanzan = sorted(set(p.relative_to(BIN).as_posix() for p in fuentes
                        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8-sig")))
                        if isinstance(n, ast.Call) and _nombre(n.func).endswith("proceso.lanzar")))
    t.igual("ME-E47 el Host lo lanza solo host_claude_code.py, por proceso.lanzar",
            ["ejecucion/host_claude_code.py"], lanzan)
    t.contiene("ME-E47 y el Host por defecto es claude", 'shutil.which("claude")',
               (EJECUCION / "host_claude_code.py").read_text(encoding="utf-8"))
    r = M64.CORRER.Resultados() if hasattr(M64, "CORRER") else _resultados()
    try:
        M64.test_e41_todo_subprocess_lanza_git_o_markitdown(r)
        caidas = []
    except Exception as e:                       # noqa: BLE001 - el motivo es el detalle
        caidas = ["%s: %s" % (type(e).__name__, e)]
    t.verdadero("ME-E47 E-41 adaptado tiene aserciones", len(r.filas) > 0)
    t.vacio("ME-E47 E-41 adaptado sigue en verde",
            caidas + ["%s %s" % (n, d) for _, n, ok, d in r.filas if not ok])


def _resultados():
    correr = _cargar("correr_para_72", RAIZ / "tests" / "correr.py")
    return correr.Resultados()


MODELO = RAIZ / "docs" / "dominio" / "modelo-canonico.md"
ADR_15 = RAIZ / "docs" / "adr" / "0015-el-motor-minimo-de-ejecucion.md"
ADR_13 = "docs/adr/0013-modelo-de-dominio-canonico.md"
ADR_14 = RAIZ / "docs" / "adr" / "0014-el-contrato-de-ejecucion.md"
# ADR-0014 es de Task 3, todavia sin commitear: su huella es la del arbol de la base de Task 4.
HUELLA_ADR_14 = "446b2e1d2aae65eaa2a45ecaa57c71d6e1f625c036b3e9a267ed2c419bb62a79"
CONCEPTOS = 83


def _git_raiz(*args):
    r = subprocess.run(["git", "-C", str(RAIZ)] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def test_me_e48_el_modelo_canonico_y_el_adr(t):
    """ME-E48 — El modelo canonico dice el invariante nuevo de ### Host, no agrega conceptos, y
    ## El limite de la ejecucion pone el motor, la admision, el almacenamiento y el Host Adapter en
    Lo que existe ahora. ADR-0015 existe, aceptado, con siete decisiones; ADR-0013 y ADR-0014 no
    cambian."""
    m = M64._modelo()
    host = " ".join(" ".join((m["campos"].get("Host") or {}).values()).split())
    t.contiene("ME-E48 ### Host dice que HARNESS no llama a ningun modelo",
               "HARNESS no llama a ningún modelo", host)
    t.contiene("ME-E48 y que desde Task 4 el motor puede lanzar el Host",
               "Desde Task 4, el motor de Execution puede lanzar el Host", host)
    t.igual("ME-E48 no se agregan conceptos", CONCEPTOS, len(m["campos"]))
    partes = dict(M64._apartados(M64._seccion(m["texto"], "El límite de la ejecución")))
    existe = " ".join(partes.get("Lo que existe ahora") or [])
    no_existe = " ".join(partes.get("Lo que todavía no existe") or [])
    for ancla in ("motor", "admisión", "almacenamiento", "Host Adapter"):
        t.contiene("ME-E48 lo que existe ahora nombra %s" % ancla, ancla, existe)
    for ancla in ("scheduler", "reintento", "reanudación", "cliente de modelo"):
        t.contiene("ME-E48 lo que todavia no existe nombra %s" % ancla, ancla, no_existe)
    texto = ADR_15.read_text(encoding="utf-8") if ADR_15.is_file() else ""
    frente = re.match(r"^---\n(.*?)\n---\n", texto.replace("\r\n", "\n"), re.S)
    t.verdadero("ME-E48 ADR-0015 existe", ADR_15.is_file())
    t.verdadero("ME-E48 aceptado", frente and re.search(r"(?m)^estado:\s*aceptada\s*$",
                                                        frente.group(1)))
    t.igual("ME-E48 con siete decisiones, de la 1 a la 7", [str(i) for i in range(1, 8)],
            re.findall(r"(?m)^### (\d+)\. ", texto))
    codigo, _ = _git_raiz("diff", "--quiet", BASE, "--", ADR_13)
    t.igual("ME-E48 ADR-0013 es el de la base", 0, codigo)
    t.igual("ME-E48 ADR-0014 es el de la base de Task 4", HUELLA_ADR_14,
            hashlib.sha256(ADR_14.read_bytes()).hexdigest() if ADR_14.is_file() else None)


PROTEGIDOS = ("harnesses/desarrollo/bin/flujo", "harnesses/desarrollo/bin/estado_de_tarea",
              "harnesses/desarrollo/bin/orquestacion", "harnesses/desarrollo/bin/contabilidad",
              "comun/hooks", "harnesses/desarrollo/agents", "harnesses/desarrollo/skills",
              "comun/agents", "comun/skills", "harnesses/desarrollo/reglas", "install.ps1",
              "manifest.json", ADR_13, "comun/schemas/orchestration-plan.schema.json",
              "comun/schemas/task-flow-state.schema.json")
# Los de Task 3, todavia sin commitear: su huella es la del arbol de la base de Task 4.
HUELLAS_DE_TASK_3 = {
    "harnesses/desarrollo/bin/ejecucion/contrato.py":
        "968c78310f09a9e19389828df6c2e8e244958c4556dde5c140577c40a93506aa",
    "comun/schemas/execution-request.schema.json":
        "df3a4bc117b53fe096d4511614d258054a76b6159d921f27180478e68b0fd644",
    "comun/schemas/execution-result.schema.json":
        "266304c6dcb9c17a3c02ac0aeb790107e47a913df260d6dd2c56a61ad3f1c1fb",
}


def test_me_e49_lo_que_no_se_toca(t):
    """ME-E49 — Flow Governance, el plan 2.1, los hooks, el registro de agentes, la contabilidad,
    install.ps1 y manifest.json son los de la base, sin archivos nuevos entre ellos; contrato.py y
    los dos schemas de Task 3, tambien."""
    codigo, _ = _git_raiz("cat-file", "-e", BASE + "^{commit}")
    t.igual("ME-E49 la base %s esta en este clon" % BASE, 0, codigo)
    for ruta in PROTEGIDOS:
        codigo, _ = _git_raiz("diff", "--quiet", BASE, "--", ruta)
        t.igual("ME-E49 %s es el de %s" % (ruta, BASE), 0, codigo)
    codigo, nuevos = _git_raiz("ls-files", "--others", "--exclude-standard", "--", *PROTEGIDOS)
    t.igual("ME-E49 no hay archivos nuevos entre ellos", (0, ""), (codigo, nuevos.strip()))
    for ruta, huella in sorted(HUELLAS_DE_TASK_3.items()):
        t.igual("ME-E49 %s es el de Task 3" % ruta, huella,
                hashlib.sha256((RAIZ / ruta).read_bytes()).hexdigest())


def test_me_e51_la_compuerta(t):
    """ME-E51 — Invoke-Tests.ps1 sale con 0, con los escenarios de esta Task y los de Task 3 que no
    reemplaza §26.2. Lo que se puede ver desde adentro: que la compuerta junta este caso y su
    instalador, y que los tests adaptados siguen ahi. El veredicto es la corrida de la compuerta."""
    invocar = (RAIZ / "tests" / "Invoke-Tests.ps1").read_text(encoding="utf-8-sig")
    t.contiene("ME-E51 la compuerta corre los casos de Python", "correr.py", invocar)
    t.verdadero("ME-E51 este caso esta en tests/casos/", Path(__file__).parent == CASOS)
    t.verdadero("ME-E51 y su instalador tambien",
                (CASOS / "72-motor-de-ejecucion-instalador.ps1").is_file())
    for caso, funcion in (("64_modelo_de_dominio.py", "test_e41_todo_subprocess_lanza_git_o_markitdown"),
                          ("64_modelo_de_dominio.py", "test_e09_el_limite_de_la_ejecucion"),
                          ("65_contrato_de_ejecucion.py", "test_ex_e49_no_hay_motor"),
                          ("65_contrato_de_ejecucion.py", "test_ex_e52_no_hay_ejecucion_persistida")):
        t.contiene("ME-E51 %s sigue teniendo %s" % (caso, funcion), "def %s(" % funcion,
                   (CASOS / caso).read_text(encoding="utf-8"))


def _reescribir_request(carpeta, cambio, indent=2, ordenada=True):
    """Edita request.json a mano: lo que la escritura de una sola vez no deja hacer al motor."""
    ruta = Path(carpeta) / registro.REQUEST
    request = M64._leer_json(ruta)
    cambio(request)
    ruta.unlink()
    ruta.write_text(json.dumps(request, ensure_ascii=False, indent=indent, sort_keys=ordenada),
                    encoding="utf-8")


def _otro_valor(actual, uno, otro):
    return otro if actual == uno else uno


def _clave_de_mas(request):
    request["workUnit"]["agregada"] = "a mano"
    request["workUnitFingerprint"] = C.huella(request["workUnit"])


ADULTERACIONES = (
    ("requestedBy", lambda r: r.update(requestedBy="Otra persona, a mano")),
    ("createdAt", lambda r: r.update(createdAt="2026-01-01T00:00:00Z")),
    ("admission.normativeGate", lambda r: r["admission"].update(
        normativeGate=_otro_valor(r["admission"]["normativeGate"], "allowed", "unresolved"))),
    ("admission.agent.validation", lambda r: r["admission"]["agent"].update(
        validation=_otro_valor(r["admission"]["agent"]["validation"], "VALID",
                               "VALID_WITH_PENDING_SKILLS"))),
    ("admission.agent.type", lambda r: r["admission"]["agent"].update(type="INFRASTRUCTURE_AGENT")),
    ("admission.agent.domain", lambda r: r["admission"]["agent"].update(domain="frontend")),
    ("admission.capabilities", lambda r: r["admission"].update(capabilities="SOME_MISSING")),
    ("admission.dependencies", lambda r: r["admission"].update(
        dependencies=[{"workUnitId": "otra", "executionId": "exe_" + "a" * 32}])),
    ("workUnit", _clave_de_mas),
    ("plan", lambda r: r["plan"].update(planVersion=r["plan"]["planVersion"] + 1)),
)


def _cuerpo_del_agente(proy, agente="dev-backend"):
    texto = (Path(proy) / ".claude" / "agents" / (agente + ".md")).read_text(encoding="utf-8")
    partes = texto.replace("\r\n", "\n").split("\n---\n", 1)
    return partes[1].strip("\n") + "\n" if len(partes) == 2 else None


ADVERSARIAS = (
    ("comandoHost con --bare", ["--bare"], None),
    ("comandoHost con --dangerously-skip-permissions", ["--dangerously-skip-permissions"], None),
    ("comandoHost con --permission-mode bypassPermissions", ["--permission-mode",
                                                             "bypassPermissions"], None),
    ("comandoHost con --permission-mode=bypassPermissions", ["--permission-mode=bypassPermissions"],
     None),
    ("comandoHost con --allowedTools", ["--allowedTools", "Bash"], None),
    ("comandoHost con --agent", ["--agent", "dev-backend"], None),
    ("comandoHost con --model=x", ["--model=opus"], None),
    ("comandoHost con -p", ["-p"], None),
    ("comandoHost con --BARE", ["--BARE"], None),
    ("comandoHost con --mcp-config", ["--mcp-config", "servidores.json"], None),
    ("perfil de modelo --dangerously-skip-permissions", [], "--dangerously-skip-permissions"),
    ("perfil de modelo --model", [], "--model"),
)


def test_me_e56_un_codigo_distinto_de_cero_nunca_es_succeeded(t):
    """ME-E56 — Un Host que termina con un codigo de salida distinto de 0 nunca deja SUCCEEDED, aunque
    su JSON diga success y traiga un structured_output COMPLETE: con 1 da HOST_FAILURE; con 143,
    HOST_INTERRUPTED; con 1 y api_error_status, PROVIDER_FAILURE."""
    proy = _proyecto(_unidades("uno", "dos", "tres"))
    completo = _informe("COMPLETE", "# listo\n")
    casos = (("uno", "codigo 1", dict(completo), 1, "HOST_FAILURE"),
             ("dos", "codigo 143", dict(completo), 143, "HOST_INTERRUPTED"),
             ("tres", "codigo 1 con api_error_status", dict(completo, api_error_status=529), 1,
              "PROVIDER_FAILURE"))
    for unidad, que, resultado, salida, codigo in casos:
        _guion(proy, resultado=resultado, salida=salida)
        corrida = _corrida(proy, unidad)
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        t.igual("ME-E56 success con %s: FAILED con %s" % (que, codigo), ("FAILED", codigo),
                (_de(corrida, "status"), _codigo(corrida)))
        t.verdadero("ME-E56 %s: sin AgentReport ni output.md" % que,
                    corrida["res"] is not None and _de(corrida, "agentDeclaredStatus") is None
                    and not (_carpeta(proy, eid) / registro.OUTPUT).exists())


class _AdaptadorQueRompeElContrato(H.Adaptador):
    """Devuelve despues de la entrega un codigo que no es de corrida: lo que el motor no escribe."""

    def __init__(self, codigo, *args, **kwargs):
        H.Adaptador.__init__(self, *args, **kwargs)
        self.codigo = codigo

    def entregar(self, proyecto, request, carpeta, definicion, host, cancelada, al_lanzar=None):
        return None, {"code": self.codigo, "motor": "el agente no esta", "host": None}, \
            proceso.TERMINO


def test_me_e57_el_motor_no_escribe_un_codigo_de_admision_despues_de_entregar(t):
    """ME-E57 — Si un Host Adapter devuelve despues de la entrega un codigo que no es de corrida
    (AGENT_UNAVAILABLE o CAPABILITY_UNAVAILABLE), el motor deja FAILED con ENGINE_FAILURE, nunca ese
    codigo."""
    proy = _proyecto(_unidades("uno", "dos"))
    _guion(proy)
    for unidad, codigo in (("uno", "AGENT_UNAVAILABLE"), ("dos", "CAPABILITY_UNAVAILABLE")):
        corrida = _corrida(proy, unidad, adaptador=_AdaptadorQueRompeElContrato(
            codigo, [sys.executable, str(HOST)], 60))
        eid = _de(corrida, "executionId") or "exe_" + "0" * 32
        t.verdadero("ME-E57 %s: la Execution se entrego" % codigo,
                    (_carpeta(proy, eid) / registro.ENTREGA).is_file())
        t.igual("ME-E57 un adaptador que devuelve %s despues de la entrega: FAILED con ENGINE_FAILURE"
                % codigo, ("FAILED", "ENGINE_FAILURE"), (_de(corrida, "status"), _codigo(corrida)))
