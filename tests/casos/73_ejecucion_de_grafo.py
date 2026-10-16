"""Los escenarios de docs/cambios/graph-execution/spec.md (Task 5), menos los que instalan de verdad
(73-ejecucion-de-grafo-instalador.ps1) y los que son una lectura. Cada asercion nombra su GE-Enn.

Se arma por grupos, como la suite 72, y cada etapa de la construccion suma el suyo sin reescribir lo
que ya esta:

    N1  GE-E53 a GE-E55   ninguna sonda de candado toca una carpeta en creacion (GD-20)
    R5  GE-E56 a GE-E59   `provee` conoce la plataforma: en win32 `tests.run` sale REJECTED (GD-21)
    ADM GE-E25 y la mitad del motor de GE-E24: `leer_plan` publico, `huella_esperada` en
        `al_entregar` y `execution_id` + `huella_esperada` en `motor.ejecutar` (GD-16, GD-27 pasos 3 y 4)
    REG GE-E60, GE-E61 y GE-E62 en lo que toca al registro, y GD-03, GD-04, GD-12 y GD-20: el id del
        GraphRun, las cuatro marcas de una sola escritura, el candado de la tarea, lo que el registro
        ofrece para cerrar huerfanos, y que `grafos/` no lo ve ninguna funcion de Execution
        (GD-27 paso 5)
    HOST el Host falso con `por_unidad` y su bitacora (GD-27 paso 6): la infraestructura con que GE-E02,
        GE-E40, GE-E44 y GE-E71 cuentan invocaciones y comparan intervalos
    GRAFO el conductor, `ejecucion/grafo.py`, y `graph-run-result.schema.json` (GD-27 pasos 7 y 8, etapa
        5a): GE-E01 a GE-E27, GE-E60 en lo que toca al schema y a `result.json`, GE-E64, GE-E68 y GE-E69, y
        las mitades del GraphRun de GE-E24, GE-E56, GE-E58 y GE-E59
    5b  la recuperacion, la cancelacion y la exclusividad del conductor (GD-10, GD-11, GD-14, GD-15;
        secciones 14 a 17): GE-E28 a GE-E52, GE-E71, y de GE-E70 lo que hace `estado_de_grafos`. Con procesos
        hijos reales y cortes con `os._exit`
    6A  la CLI (GD-24, GD-27 paso 9): `ejecutar <KEY> --grafo`, `--grafo --estado` y `--cancelar grf_...`.
        Completa por el comando lo que la 5a y la 5b dejaron probado por funcion: GE-E63, GE-E69, GE-E70,
        las salidas 0 o 2 de GE-E01, GE-E06, GE-E08, GE-E09 y GE-E18, `ejecutar --unidad` y `--cancelar
        <exe>` de verdad en GE-E05, GE-E19 y GE-E20, y `--cancelar grf_...` en GE-E46, GE-E47, GE-E50 y GE-E51.
        Todos llevan `por_cli` en el nombre. GE-E65 y GE-E67 no estan: son de la etapa 7
    7   la integracion (27.1 F, G y H; GD-25, seccion 28): GE-E65, lo que no se toca de Task 3 y los tres ADR
        anteriores, y GE-E67, el modelo canonico y ADR-0016. La parte nueva de GE-E70 (un GraphRun ILEGIBLE) la
        lleva, con su id, `test_gd10_un_graphrun_ilegible_no_se_cierra_ni_se_reabre`

R5 y ADM prueban solo las mitades del motor, de la admision y del adaptador: REG, solo las primitivas
del registro, sin el conductor. Lo que nombra a `ejecutar --grafo` como comando es de la 6A.

El proyecto de prueba, el guion del Host falso y el motor en otro proceso son los de la suite 72: la
cargo como modulo, igual que la 72 carga la 64. Las carreras son entre procesos reales del sistema
operativo, que se paran en una ventana por marcas en una carpeta compartida: ninguna se simula con un
mock en memoria. Lo que un hijo levanta lo ve el escenario en el campo `exc` de su salida.

🔴 Ningun test lanza el Claude Code real: todo proyecto de prueba declara el Host falso.
"""
import ast
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CASOS = RAIZ / "tests" / "casos"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M72 = _cargar("motor_para_73", CASOS / "72_motor_de_ejecucion.py")
M64 = M72.M64

from contexto import limpieza                            # noqa: E402
from ejecucion import admision                           # noqa: E402
from ejecucion import contrato                           # noqa: E402
from ejecucion import grafo                              # noqa: E402
from ejecucion import host_claude_code as H             # noqa: E402
from ejecucion import motor                              # noqa: E402
from ejecucion import proceso                            # noqa: E402
from ejecucion import registro                           # noqa: E402

CLAVE = M72.CLAVE
PIDE = M72.PIDE


# -- el proyecto de prueba -------------------------------------------------------------------

def _requested_sin_motor(proy, unidad="analizar-api"):
    """Una Execution REQUESTED publicada cuyo motor ya no esta: carpeta, request y turno, con el
    candado libre. Es lo que deja un motor que murio despues de publicar y antes de entregar."""
    request, error, leido, _ = admision.al_pedir(str(proy), CLAVE, unidad, PIDE,
                                                 limpieza.cargar_catalogo())
    if error is not None:
        raise AssertionError("la admision de la Execution de prueba fallo: %s" % (error,))
    vida = registro.crear(str(proy), request, leido)
    vida.soltar()
    return request


def _envejecer(ruta, segundos):
    """Le pone a la ruta una fecha de hace `segundos`."""
    hace = time.time() - segundos
    os.utime(str(ruta), (hace, hace))


class _Sondas(object):
    """Anota cada carpeta cuyo candado se sondea, sin cambiar lo que `candado_libre` contesta."""

    def __enter__(self):
        self.carpetas = []
        self._real = registro.candado_libre
        registro.candado_libre = self._sondear
        return self

    def _sondear(self, carpeta):
        self.carpetas.append(os.path.basename(carpeta))
        return self._real(carpeta)

    def __exit__(self, *_):
        registro.candado_libre = self._real


# -- procesos: dos del sistema operativo que se paran en una ventana --------------------------

HIJO = r'''
import json, os, sys, time
bin_dir, modo, proyecto, clave, marcas = sys.argv[1:6]
extra = sys.argv[6:]
sys.path.insert(0, bin_dir)
from ejecucion import grafo, motor, registro


def marca(nombre):
    with open(os.path.join(marcas, nombre), "w") as f:
        f.write(str(os.getpid()))


def esperar(*nombres):
    fin = time.time() + 60
    while time.time() < fin:
        if any(os.path.exists(os.path.join(marcas, n)) for n in nombres):
            return True
        time.sleep(0.02)
    return False


def esperar_cuantas(prefijo, cuantas):
    fin = time.time() + 60
    while time.time() < fin:
        if len([n for n in os.listdir(marcas) if n.startswith(prefijo)]) >= cuantas:
            return True
        time.sleep(0.02)
    return False


def admitir():
    # A: entre el O_EXCL de `Vida` y su candado. La primera vez que se pide un candado en este
    # proceso es la de `Vida`: el proyecto es nuevo y no hay carpetas que sondear antes.
    real = registro._bloquear
    primera = []

    def _bloquear(descriptor):
        if primera:
            return real(descriptor)
        primera.append(1)
        marca("a.creado")
        esperar("b.sondeo", "b.fin")
        try:
            real(descriptor)
        finally:
            marca("a.bloqueo")

    registro._bloquear = _bloquear
    try:
        res, err = motor.ejecutar(proyecto, clave, extra[0], "Persona de prueba")
        return {"res": res, "err": err, "exc": None}
    except Exception as e:
        return {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}


def recuperar_con_sonda():
    # B: la recuperacion de la misma tarea, con la sonda detenida mientras tiene el candado.
    sondeadas = []
    real_libre, real_soltar = registro.candado_libre, registro._soltar

    def candado_libre(carpeta):
        sondeadas.append(os.path.basename(carpeta))
        return real_libre(carpeta)

    def _soltar(descriptor):
        marca("b.sondeo")
        esperar("a.bloqueo")
        real_soltar(descriptor)

    registro.candado_libre = candado_libre
    registro._soltar = _soltar
    esperar("a.creado")
    vistas = registro.residuos(proyecto, clave)
    try:
        cerradas = motor.recuperar(proyecto, clave)
        return {"cerradas": cerradas, "sondeadas": sondeadas, "residuos": vistas, "exc": None}
    except Exception as e:
        return {"cerradas": None, "sondeadas": sondeadas, "residuos": vistas,
                "exc": "%s: %s" % (type(e).__name__, e)}
    finally:
        marca("b.fin")


def cancelar():
    # C: `--cancelar exe_...`, parado entre el temporal de cancelacion.json y su os.link.
    real = os.link

    def link(origen, destino, *a, **k):
        if os.path.basename(str(destino)) == "cancelacion.json":
            marca("c.temporal")
            esperar("r.fin")
        return real(origen, destino, *a, **k)

    os.link = link
    try:
        return {"res": motor.cancelar(proyecto, clave, extra[0], "Persona de prueba"), "exc": None}
    except Exception as e:
        return {"res": None, "exc": "%s: %s" % (type(e).__name__, e)}


def recuperar_en_el_instante():
    # R: la recuperacion de otro proceso, justo en ese instante.
    esperar("c.temporal")
    try:
        return {"cerradas": motor.recuperar(proyecto, clave), "exc": None}
    except Exception as e:
        return {"cerradas": None, "exc": "%s: %s" % (type(e).__name__, e)}
    finally:
        marca("r.fin")


def competir():
    # K1 y K2: dos procesos escriben la misma marca de una sola escritura, parados en la misma puerta:
    # los dos llegan, y despues los dos escriben. Gana uno.
    que, graph_run_id, valor = extra
    marca("listo.%d" % os.getpid())
    fin = time.time() + 60
    while time.time() < fin and len([n for n in os.listdir(marcas) if n.startswith("listo.")]) < 2:
        time.sleep(0.002)
    try:
        if que == "cancelacion":
            registro.marcar_cancelacion(proyecto, clave, graph_run_id, valor)
        else:
            registro.escribir_terminal(proyecto, clave, graph_run_id,
                                       {"graphRunId": graph_run_id, "taskKey": clave, "status": valor})
        return {"gano": True, "exc": None}
    except FileExistsError:
        return {"gano": False, "exc": None}
    except Exception as e:
        return {"gano": None, "exc": "%s: %s" % (type(e).__name__, e)}


def candado():
    # L: toma el candado de la tarea y avisa. `esperar` lo suelta cuando le dicen; `morir` sale sin
    # soltarlo, como un proceso que se cae: lo suelta el sistema operativo.
    c = registro.CandadoDeTarea(proyecto, clave)
    tomado = bool(c)
    marca("l.tomado" if tomado else "l.no_tomado")
    if tomado and extra[0] == "morir":
        os._exit(0)
    if tomado:
        esperar("l.soltar")
        c.soltar()
    return {"tomado": tomado}


def cancelar_en_curso():
    # K: lo que hace `ejecutar <KEY> --cancelar <exe>` desde otro proceso, cuando la Execution ya lanzo su
    # Host: `motor.cancelar` por el camino de Task 4. El conductor, que es el que la corre, sigue su camino.
    carpeta = os.path.join(proyecto, ".claude", "ejecuciones", clave, extra[0])
    fin = time.time() + 60
    while time.time() < fin and not os.path.exists(os.path.join(carpeta, "proceso.json")):
        time.sleep(0.02)
    try:
        return {"res": motor.cancelar(proyecto, clave, extra[0], "Persona de prueba"), "exc": None}
    except Exception as e:
        return {"res": None, "exc": "%s: %s" % (type(e).__name__, e)}


def hacer(nombre, accion):
    # Lo que un punto de encuentro hace (etapa 5b): avisa que llego, espera lo que le digan, y despues se
    # corta como un Ctrl-C, o como un corte de luz: `os._exit` no corre un `finally` ni suelta un candado,
    # lo suelta el sistema operativo.
    marca(accion.get("marca") or nombre)
    if accion.get("esperar"):
        esperar(*accion["esperar"])
    if accion.get("esperar_cuantas"):
        esperar_cuantas(*accion["esperar_cuantas"])
    if accion.get("ctrl_c"):
        raise KeyboardInterrupt
    if accion.get("morir"):
        os._exit(77)


def unidad_de(args):
    # La unidad de un gancho: la marca de despacho la trae, y `antes_de_entregar` recibe la carpeta de la
    # Execution, que la lleva en su request.json.
    dato = args[0] if args else None
    if isinstance(dato, dict):
        return dato.get("workUnitId")
    if isinstance(dato, str) and os.path.isfile(os.path.join(dato, "request.json")):
        with open(os.path.join(dato, "request.json"), encoding="utf-8") as f:
            return json.load(f)["workUnit"]["id"]
    return None


def gancho(nombre, accion):
    def punto(*args):
        unidad = unidad_de(args)
        if accion.get("unidad") and accion["unidad"] != unidad:
            return
        hacer(nombre + ("." + unidad if unidad else ""), accion)
    return punto


def conducir():
    # El conductor en otro proceso. extra[0] es el JSON de lo que hace en cada punto de encuentro:
    # {"ganchos": {nombre: accion}, "antes_del_motor": accion, "encuentro": bool}. `antes_del_motor` es el
    # instante entre la lectura de la marca de cancelacion (7f) y la llamada al motor (7g): el conductor no
    # tiene un gancho ahi, y el test lo hace envolviendo a `motor.ejecutar`.
    plan = json.loads(extra[0]) if extra else {}
    ganchos = dict((n, gancho(n, a)) for n, a in plan.get("ganchos", {}).items())
    if plan.get("antes_del_motor"):
        accion, ejecutar_real = plan["antes_del_motor"], motor.ejecutar

        def ejecutar_envuelto(proyecto_, clave_, unidad, *a, **k):
            if not accion.get("unidad") or accion["unidad"] == unidad:
                hacer("antes_del_motor." + unidad, accion)
            return ejecutar_real(proyecto_, clave_, unidad, *a, **k)

        motor.ejecutar = ejecutar_envuelto
    if plan.get("encuentro"):
        # Dos conductores se paran antes de tomar el candado de la tarea, y salen juntos (GE-E28).
        candado_real = registro.CandadoDeTarea

        class Encuentro(candado_real):
            def __init__(self, proyecto_, clave_):
                marca("listo.%d" % os.getpid())
                esperar_cuantas("listo.", 2)
                candado_real.__init__(self, proyecto_, clave_)
                marca("intento.%d" % os.getpid())

        registro.CandadoDeTarea = Encuentro
    try:
        res, err = grafo.conducir(proyecto, clave, plan.get("pedido_por", "Persona de prueba"),
                                  ganchos=ganchos)
        return {"res": res, "err": err, "exc": None}
    except BaseException as e:
        return {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}


def cancelar_grafo():
    # `ejecutar <KEY> --cancelar grf_...` desde otro proceso: extra = [graphRunId, espera en segundos, intervalo
    # en segundos (0.2 si no viene)]. Al terminar cada vuelta en que mira las Executions propias deja la marca
    # `barrido.N`: el escenario que necesita saber que la primera vuelta ya paso la espera (GE-E48 c).
    real_las_propias, vueltas = grafo._cancelar_las_propias, []

    def las_propias(*a, **k):
        pedidas = real_las_propias(*a, **k)
        vueltas.append(1)
        marca("barrido.%d" % len(vueltas))
        return pedidas

    grafo._cancelar_las_propias = las_propias
    intervalo = float(extra[2]) if len(extra) > 2 else 0.2
    try:
        return {"res": grafo.cancelar_grafo(proyecto, clave, extra[0], "Persona de prueba",
                                            espera=float(extra[1]), intervalo=intervalo), "exc": None}
    except BaseException as e:
        return {"res": None, "exc": "%s: %s" % (type(e).__name__, e)}


def ejecutar():
    # `ejecutar <KEY> --unidad <w>`: extra = [unidad]. La TaskKey es la que se le pase, no solo la de siempre.
    try:
        res, err = motor.ejecutar(proyecto, clave, extra[0], "Persona de prueba")
        return {"res": res, "err": err, "exc": None}
    except BaseException as e:
        return {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}


MODOS = {"admitir": admitir, "recuperar_con_sonda": recuperar_con_sonda, "cancelar": cancelar,
         "recuperar_en_el_instante": recuperar_en_el_instante, "competir": competir,
         "candado": candado, "cancelar_en_curso": cancelar_en_curso, "conducir": conducir,
         "cancelar_grafo": cancelar_grafo, "ejecutar": ejecutar}
sys.stdout.write(json.dumps(MODOS[modo]()))
'''

_SCRIPT = []


def _script_hijo():
    """El script de los hijos, en una carpeta temporal que se borra al terminar la suite."""
    if not _SCRIPT:
        ruta = M64._tmp("ge73-hijo-") / "hijo.py"
        ruta.write_text(HIJO, encoding="utf-8")
        _SCRIPT.append(ruta)
    return _SCRIPT[0]


def _lanzar(modo, proy, marcas, *extra, clave=CLAVE):
    """Un hijo con la API del motor, que se para en las marcas de `marcas`."""
    entorno = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.Popen([sys.executable, str(_script_hijo()), str(BIN), modo, str(proy), clave,
                             str(marcas)] + list(extra), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=entorno)


def _salida(hijo, limite=120):
    """Lo que el hijo devolvio por stdout. Un hijo que no contesta se mata."""
    try:
        salida, error = hijo.communicate(timeout=limite)
    except subprocess.TimeoutExpired:
        hijo.kill()
        salida, error = hijo.communicate()
    try:
        return json.loads(salida.decode("utf-8"))
    except ValueError:
        return {"exc": "sin salida: " + error.decode("utf-8", "replace")[-300:]}


def _marcas(marcas):
    return sorted(p.name for p in Path(marcas).iterdir())


# =============================================================================================
# N1: ninguna sonda de candado toca una carpeta en creacion (GD-20, GE-I25)
# =============================================================================================

def test_ge_e53_la_sonda_no_toca_la_carpeta_en_creacion(t):
    """GE-E53 — Dos procesos: A, detenido entre `os.open(O_EXCL)` y `_bloquear` de `Vida`; B corre
    `motor.recuperar` sobre la misma tarea con su sonda detenida mientras tiene el candado. A publica
    su Execution y B nunca sondea la carpeta de A. Con F1 revertido, A sale con un error del comando.
    (F1, barrer: la edad va antes que el candado.)"""
    proy = M72._proyecto()
    M72._guion(proy)
    marcas = M64._tmp("ge73-marcas-")
    a = _lanzar("admitir", proy, marcas, "analizar-api")
    b = _lanzar("recuperar_con_sonda", proy, marcas)
    sal_b = _salida(b)
    sal_a = _salida(a)

    t.igual("GE-E53 A no sale con un error del comando", None, sal_a.get("exc"))
    t.igual("GE-E53 A publica su Execution y termina SUCCEEDED", "SUCCEEDED",
            (sal_a.get("res") or {}).get("status"))
    t.igual("GE-E53 y A no devuelve un ExecutionError", None, sal_a.get("err"))
    eid = (sal_a.get("res") or {}).get("executionId") or "exe_" + "0" * 32
    t.igual("GE-E53 el turno 1 nombra a la Execution de A", [(1, eid)],
            M72._turnos(proy, "analizar-api"))
    t.igual("GE-E53 una sola carpeta", [eid], M72._carpetas(proy))

    t.igual("GE-E53 B no levanto", None, sal_b.get("exc"))
    t.igual("GE-E53 B vio la carpeta de A como un residuo sin turno: la ventana era real", 1,
            len(sal_b.get("residuos") or []))
    t.vacio("GE-E53 B nunca sondeo una carpeta", sal_b.get("sondeadas"))
    t.verdadero("GE-E53 y su sonda nunca tuvo el candado de A", "b.sondeo" not in _marcas(marcas))
    t.vacio("GE-E53 B no cerro nada", sal_b.get("cerradas"))

    # El mismo F1, sin carrera: una carpeta nueva no se sondea, una vieja si.
    otro = M72._proyecto()
    carpeta, _ = M72._residuo(otro, "analizar-api")
    with _Sondas() as sondas:
        borrados = registro.barrer(str(otro), CLAVE)
    t.vacio("GE-E53 barrer no sondea una carpeta nueva sin turno", sondas.carpetas)
    t.vacio("GE-E53 y no la borra", borrados)
    t.verdadero("GE-E53 la carpeta nueva sigue", carpeta.is_dir())
    M72._viejo(carpeta / registro.VIVO, carpeta)
    with _Sondas() as sondas:
        borrados = registro.barrer(str(otro), CLAVE)
    t.igual("GE-E53 una carpeta de mas de diez minutos si se sondea", [carpeta.name],
            sondas.carpetas)
    t.igual("GE-E53 y con el candado libre se borra", [carpeta.name], borrados)


def test_ge_e54_limpiar_temporales_respeta_la_edad(t):
    """GE-E54 — `limpiar_temporales` no sondea ni borra un temporal de menos de diez minutos en una
    carpeta con el candado libre, y si borra uno envejecido a once. Una carpeta sin temporales viejos
    no se sondea. (F2', limpiar_temporales: mira primero los temporales viejos.)"""
    proy = M72._proyecto()
    request = _requested_sin_motor(proy)
    carpeta = M72._carpeta(proy, request["executionId"])
    t.verdadero("GE-E54 el candado de la carpeta esta libre",
                registro.candado_libre(str(carpeta)) is True)

    with _Sondas() as sondas:
        borrados = registro.limpiar_temporales(str(proy), CLAVE)
    t.igual("GE-E54 una carpeta sin temporales no borra nada", 0, borrados)
    t.vacio("GE-E54 y no se sondea", sondas.carpetas)

    nuevo = carpeta / ".request.json.n3w000.tmp"
    nuevo.write_text("{a medias", encoding="utf-8")
    _envejecer(nuevo, 590)
    with _Sondas() as sondas:
        borrados = registro.limpiar_temporales(str(proy), CLAVE)
    t.igual("GE-E54 un temporal de menos de diez minutos no se borra", 0, borrados)
    t.verdadero("GE-E54 y sigue ahi", nuevo.is_file())
    t.vacio("GE-E54 una carpeta sin temporales viejos no se sondea", sondas.carpetas)

    viejo = carpeta / ".cancelacion.json.0ld000.tmp"
    viejo.write_text("{a medias", encoding="utf-8")
    _envejecer(viejo, 660)
    with _Sondas() as sondas:
        borrados = registro.limpiar_temporales(str(proy), CLAVE)
    t.igual("GE-E54 uno envejecido a once minutos si se borra, y solo ese", 1, borrados)
    t.verdadero("GE-E54 el viejo ya no esta", not viejo.exists())
    t.verdadero("GE-E54 el nuevo sigue", nuevo.is_file())
    t.igual("GE-E54 con uno viejo se sondea la carpeta, una vez", [carpeta.name], sondas.carpetas)

    viejo.write_text("{a medias", encoding="utf-8")
    _envejecer(viejo, 660)
    tomado = registro.Tomado(str(carpeta))
    try:
        t.verdadero("GE-E54 el candado se pudo tomar", bool(tomado))
        with _Sondas() as sondas:
            borrados = registro.limpiar_temporales(str(proy), CLAVE)
    finally:
        tomado.soltar()
    t.igual("GE-E54 con el candado tomado un temporal viejo tampoco se borra", 0, borrados)
    t.verdadero("GE-E54 y sigue ahi", viejo.is_file())
    t.igual("GE-E54 el candado decide: se sondeo", [carpeta.name], sondas.carpetas)


def test_ge_e55_cancelar_no_pierde_su_temporal(t):
    """GE-E55 — Un `--cancelar exe_...` sobre una REQUESTED sin motor, con un `recuperar` de otro
    proceso en el instante entre su temporal y su `os.link`, termina sin excepcion y deja la Execution
    CANCELLED. (F2': el temporal nuevo de una escritura en curso no se borra.)"""
    proy = M72._proyecto()
    request = _requested_sin_motor(proy)
    eid = request["executionId"]
    carpeta = M72._carpeta(proy, eid)
    t.verdadero("GE-E55 antes de cancelar esta REQUESTED y sin motor",
                registro.estado(str(proy), CLAVE, eid)["estado"] == registro.REQUESTED
                and registro.candado_libre(str(carpeta)) is True)
    marcas = M64._tmp("ge73-marcas-")
    c = _lanzar("cancelar", proy, marcas, eid)
    r = _lanzar("recuperar_en_el_instante", proy, marcas)
    sal_r = _salida(r)
    sal_c = _salida(c)

    t.verdadero("GE-E55 el instante era real: el temporal existia y la recuperacion corrio",
                {"c.temporal", "r.fin"} <= set(_marcas(marcas)))
    t.igual("GE-E55 el cancelar termina sin excepcion", None, sal_c.get("exc"))
    t.igual("GE-E55 y dice que pidio la cancelacion", True, (sal_c.get("res") or {}).get("pedido"))
    t.igual("GE-E55 y que la Execution quedo CANCELLED", "CANCELLED",
            (sal_c.get("res") or {}).get("despues"))
    t.igual("GE-E55 la recuperacion de otro proceso no levanto", None, sal_r.get("exc"))
    t.vacio("GE-E55 ni cerro nada", sal_r.get("cerradas"))
    t.igual("GE-E55 en el registro la Execution esta CANCELLED", "CANCELLED",
            registro.estado(str(proy), CLAVE, eid)["estado"])
    t.verdadero("GE-E55 y cancelacion.json esta escrito", (carpeta / registro.CANCELACION).is_file())
    t.vacio("GE-E55 no queda ningun temporal", M72._temporales(proy))


# =============================================================================================
# R5: `provee` conoce la plataforma (GD-21, GE-I26)
# =============================================================================================

def _adaptador(plataforma):
    """El adaptador de siempre, con el Host falso, y la plataforma inyectada."""
    return H.Adaptador([sys.executable, str(M72.HOST)], 60, plataforma=plataforma)


def _proyecto_con_tests():
    """A lee y B corre tests, y depende de A: el agente es dev-backend, que tiene Bash en su tools:."""
    return M72._proyecto([M64._unidad("analizar-api"),
                          M64._unidad("correr-tests", capacidades=("tests.run",),
                                      dependencias=("analizar-api",))])


def _de_la_execution(proy, execution_id):
    """{ruta: huella} de lo que hay en la carpeta de una Execution."""
    prefijo = "%s/%s/" % (CLAVE, execution_id)
    return {ruta: huella for ruta, huella in M72._arbol(proy).items() if ruta.startswith(prefijo)}


def _a_y_despues_b(proy, plataforma, eco_b):
    """Corre A (que lee) y despues B (que corre tests) con el adaptador en `plataforma`. Devuelve
    (A, lo que A dejo en disco, B, eco de A): el eco de A prueba que la senal del Host falso es real."""
    adaptador = _adaptador(plataforma)
    eco_a = M72._eco(proy, "eco-a")
    M72._guion(proy, eco=str(eco_a))
    a = M72._corrida(proy, "analizar-api", adaptador=adaptador)
    dejado = _de_la_execution(proy, M72._de(a, "executionId") or "exe_" + "0" * 32)
    M72._guion(proy, eco=str(eco_b))
    b = M72._corrida(proy, "correr-tests", adaptador=adaptador)
    return a, dejado, b, eco_a


def test_ge_e56_en_windows_tests_run_sale_rechazada_antes_de_la_entrega(t):
    """GE-E56 — Con el adaptador en `win32`, una unidad B con `tests.run` y un agente con Bash en su
    `tools:`: B queda REJECTED CAPABILITY_UNAVAILABLE, sin entrega.json; el Host no recibe la
    invocacion de B; el detail nombra Bash y la plataforma; A, ya SUCCEEDED, queda identica. (La mitad
    del GraphRun, WORK_UNIT_NOT_SUCCEEDED con executionCode, se agrego en la etapa 5a, al final.)"""
    proy = _proyecto_con_tests()
    eco_b = M72._eco(proy, "eco-b")
    a, dejado_por_a, b, eco_a = _a_y_despues_b(proy, "win32", eco_b)

    t.igual("GE-E56 A termina SUCCEEDED", "SUCCEEDED", M72._de(a, "status"))
    t.verdadero("GE-E56 el Host falso recibio la invocacion de A: la senal del eco es real",
                eco_a.is_file())
    t.igual("GE-E56 el motor no levanta con B", None, b["exc"])
    t.igual("GE-E56 B queda REJECTED", "REJECTED", M72._de(b, "status"))
    t.igual("GE-E56 con CAPABILITY_UNAVAILABLE", "CAPABILITY_UNAVAILABLE", M72._codigo(b))
    t.igual("GE-E56 y no es un ExecutionError al pedir: B tiene su Execution", None, b["err"])
    eid_b = M72._de(b, "executionId") or "exe_" + "0" * 32
    carpeta_b = M72._carpeta(proy, eid_b)
    t.igual("GE-E56 B se admitio al pedir: tiene su turno", [(1, eid_b)],
            M72._turnos(proy, "correr-tests"))
    t.verdadero("GE-E56 B tiene su request.json", (carpeta_b / registro.REQUEST).is_file())
    t.verdadero("GE-E56 sin entrega.json", not (carpeta_b / registro.ENTREGA).exists())
    t.verdadero("GE-E56 ni el prompt de sistema, que escribe el adaptador al entregar",
                not (carpeta_b / H.PROMPT_DE_SISTEMA).exists())
    t.verdadero("GE-E56 el Host no recibio la invocacion de B", not eco_b.exists())
    detalle = (M72._de(b, "error") or {}).get("detail") or ""
    t.contiene("GE-E56 el detail nombra Bash", "Bash", detalle)
    t.contiene("GE-E56 el detail nombra la plataforma", "win32", detalle)
    t.contiene("GE-E56 y la capability", "tests.run", detalle)
    t.igual("GE-E56 A queda identica", dejado_por_a,
            _de_la_execution(proy, M72._de(a, "executionId") or "exe_" + "0" * 32))

    adaptador = _adaptador("win32")
    backend = {"tools": ["Read", "Glob", "Grep", "Edit", "Write", "Bash", "Skill"]}
    t.verdadero("GE-E56 provee: tests.run no se provee en win32 aunque el agente tenga Bash",
                len(adaptador.provee(["tests.run"], backend)) == 1
                and adaptador.provee(["tests.run"], backend)[0].startswith("tests.run"))
    t.vacio("GE-E56 provee: lo que no usa Bash se provee en win32",
            adaptador.provee(["repository.read", "repository.search", "repository.write"], backend))
    t.igual("GE-E56 provee: una capability de integracion sigue sin proveerse, con su id",
            ["jira.issue.read"], adaptador.provee(["jira.issue.read"], backend))
    t.igual("GE-E56 provee: un agente sin Write sigue sin proveer repository.write, con su id",
            ["repository.write"],
            adaptador.provee(["repository.write"], {"tools": ["Read", "Bash", "Skill"]}))
    t.igual("GE-E56 herramientas no cambia (ME-E40): sigue armando Bash para tests.run",
            ["Bash", "Skill"], adaptador.herramientas(["tests.run"], backend))

    # La mitad del GraphRun (etapa 5a): el conductor, ciego a capacidades, despacha B; la admision lo
    # rechaza al entregar y el GraphRun cierra con WORK_UNIT_NOT_SUCCEEDED y el codigo de la admision.
    proy_g = _proyecto_con_tests()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy_g, bitacora=str(bitacora))
    de_a = {}

    def foto_de_a(marca):
        if marca["workUnitId"] == "analizar-api":
            de_a.update(_de_la_execution(proy_g, marca["executionId"]))

    res = _grafo(proy_g, adaptador=_adaptador("win32"), ganchos={"despues_del_retorno": foto_de_a})["res"] or {}
    eid_b = _eid_de(proy_g, "correr-tests")
    t.igual("GE-E56 GraphRun: cierra FAILED con WORK_UNIT_NOT_SUCCEEDED por B, REJECTED y "
            "CAPABILITY_UNAVAILABLE",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "correr-tests", eid_b, "REJECTED",
                        "CAPABILITY_UNAVAILABLE")), (res.get("status"), _causa_de(res)))
    t.verdadero("GE-E56 GraphRun: B sin entrega.json, y el Host solo recibio la invocacion de A",
                _sin_entrega(proy_g, eid_b)
                and ["analizar-api"] == [i["workUnitId"] for i in _intervalos(bitacora)])
    t.igual("GE-E56 GraphRun: A, ya SUCCEEDED, queda identica", de_a,
            _de_la_execution(proy_g, _eid_de(proy_g, "analizar-api")))
    _valida(t, "GE-E56 GraphRun", proy_g, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e57_en_linux_tests_run_se_admite_y_se_entrega_con_bash(t):
    """GE-E57 — La misma unidad con el adaptador en `linux` se admite y se entrega con Bash en
    `--tools`. Es el comportamiento de antes de R5, en cualquier plataforma que ofrezca Bash."""
    for plataforma in ("linux", "darwin"):
        proy = _proyecto_con_tests()
        eco_b = M72._eco(proy, "eco-b")
        a, _, b, _ = _a_y_despues_b(proy, plataforma, eco_b)
        t.igual("GE-E57 %s: A termina SUCCEEDED" % plataforma, "SUCCEEDED", M72._de(a, "status"))
        t.igual("GE-E57 %s: B se admite y termina SUCCEEDED" % plataforma, "SUCCEEDED",
                M72._de(b, "status"))
        eid_b = M72._de(b, "executionId") or "exe_" + "0" * 32
        t.verdadero("GE-E57 %s: B se entrego" % plataforma,
                    (M72._carpeta(proy, eid_b) / registro.ENTREGA).is_file())
        t.verdadero("GE-E57 %s: el Host recibio la invocacion de B" % plataforma, eco_b.is_file())
        argv = M72._argv(proy, eco_b)
        for bandera in ("--tools", "--allowedTools"):
            i = argv.index(bandera) if bandera in argv else -1
            valor = argv[i + 1] if i >= 0 else ""
            t.igual("GE-E57 %s: %s de B lleva Bash" % (plataforma, bandera), "Bash,Skill", valor)

    adaptador = _adaptador("linux")
    backend = {"tools": ["Read", "Glob", "Grep", "Edit", "Write", "Bash", "Skill"]}
    t.vacio("GE-E57 provee: tests.run se provee en linux con Bash en el tools: del agente",
            adaptador.provee(["tests.run"], backend))
    t.igual("GE-E57 provee: sin Bash en el tools: del agente, no, con el id de la capability",
            ["tests.run"], adaptador.provee(["tests.run"], {"tools": ["Read", "Skill"]}))
    t.igual("GE-E57 la plataforma por defecto es la de este proceso", sys.platform,
            H.Adaptador([sys.executable, str(M72.HOST)], 60).plataforma)
    por_defecto = H.Adaptador([sys.executable, str(M72.HOST)], 60)
    explicito = _adaptador(sys.platform)
    t.igual("GE-E57 y sin inyectarla, provee contesta lo mismo que con esa plataforma",
            explicito.provee(["tests.run"], backend), por_defecto.provee(["tests.run"], backend))
    for invalida in ("", 7, ["win32"]):
        try:
            _adaptador(invalida)
            levanto = False
        except ValueError:
            levanto = True
        t.verdadero("GE-E57 una plataforma que no es un texto no vacio (%r) levanta ValueError" % (
            invalida,), levanto)


def test_ge_e58_un_plan_sin_tests_run_en_windows_termina_succeeded(t):
    """GE-E58 — Un plan sin `tests.run`, con el adaptador en `win32`, termina SUCCEEDED: R5 no
    rechaza una unidad por la plataforma, solo la que pide una herramienta que el Host no ofrece."""
    proy = M72._proyecto()
    M72._guion(proy)
    adaptador = _adaptador("win32")
    for unidad in ("analizar-api", "implementar-endpoint"):
        corrida = M72._corrida(proy, unidad, adaptador=adaptador)
        t.igual("GE-E58 %s: el motor no levanta" % unidad, None, corrida["exc"])
        t.igual("GE-E58 %s termina SUCCEEDED" % unidad, "SUCCEEDED", M72._de(corrida, "status"))
        t.igual("GE-E58 %s sin un codigo de error" % unidad, None, M72._codigo(corrida))
        eid = M72._de(corrida, "executionId") or "exe_" + "0" * 32
        t.verdadero("GE-E58 %s se entrego" % unidad,
                    (M72._carpeta(proy, eid) / registro.ENTREGA).is_file())

    # La mitad del GraphRun (etapa 5a): el mismo plan, conducido, con el adaptador en `win32`.
    otro = M72._proyecto()
    M72._guion(otro)
    res = _grafo(otro, adaptador=adaptador)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E58 GraphRun: un plan sin tests.run, con el adaptador en win32, termina SUCCEEDED",
            ("SUCCEEDED", None, [(1, "analizar-api"), (2, "implementar-endpoint")]),
            (res.get("status"), res.get("error"), _despachos(otro, graph_run_id)))
    _valida(t, "GE-E58 GraphRun", otro, graph_run_id)


def test_ge_e59_la_mitad_del_motor_de_me_i29_sigue_en_pie(t):
    """GE-E59 — ME-E42 (el repo lo tiene como ME-E57 y en el ultimo bloque de ME-E42) sigue verde: un
    adaptador que devuelve CAPABILITY_UNAVAILABLE despues de la entrega da ENGINE_FAILURE, tambien con
    el adaptador en `win32`. (La mitad del GraphRun, un FAILED CAPABILITY_UNAVAILABLE armado en el
    registro, se agrego en la etapa 5a, al final.)"""
    proy = M72._proyecto(M72._unidades("uno"))
    M72._guion(proy)
    rompe = M72._AdaptadorQueRompeElContrato(
        "CAPABILITY_UNAVAILABLE", [sys.executable, str(M72.HOST)], 60, plataforma="win32")
    corrida = M72._corrida(proy, "uno", adaptador=rompe)
    eid = M72._de(corrida, "executionId") or "exe_" + "0" * 32
    t.verdadero("GE-E59 la Execution se entrego",
                (M72._carpeta(proy, eid) / registro.ENTREGA).is_file())
    t.igual("GE-E59 un adaptador en win32 que devuelve CAPABILITY_UNAVAILABLE despues de la entrega: "
            "FAILED con ENGINE_FAILURE", ("FAILED", "ENGINE_FAILURE"),
            (M72._de(corrida, "status"), M72._codigo(corrida)))
    t.vacio("GE-E59 despues de la entrega el adaptador de Claude Code no nombra el codigo: R5 lo "
            "dice al admitir, por provee, y el codigo lo escribe la admision",
            ["%s" % n.value for n in ast.walk(ast.parse(
                (M72.EJECUCION / "host_claude_code.py").read_text(encoding="utf-8")))
             if isinstance(n, ast.Constant) and n.value in ("AGENT_UNAVAILABLE",
                                                            "CAPABILITY_UNAVAILABLE")])

    # La mitad del GraphRun (etapa 5a): un registro armado donde el ultimo turno de A es un FAILED
    # CAPABILITY_UNAVAILABLE valido por contrato (`contrato.py:69` lo permite, aunque el motor no lo emita).
    # El GraphRun lo trata como una unidad no exitosa: no despacha, y no lo toma por satisfecho.
    armado = M72._proyecto([M64._unidad("a"), M64._unidad("b", dependencias=("a",))])
    bitacora = _ruta_de_bitacora()
    M72._guion(armado, bitacora=str(bitacora))
    request = _requested_sin_motor(armado, "a")
    carpeta = M72._carpeta(armado, request["executionId"])
    fallida = motor._resultado(
        request, contrato.huella(request), "FAILED", "CAPABILITY_UNAVAILABLE",
        "un registro armado: el Host dejo de proveer la capability", limpieza.cargar_catalogo(),
        inicio=registro.ahora(), evidencia_={"repoRevisionBefore": None, "repoRevisionAfter": None,
                                             "changes": {"state": "CHANGES_UNRESOLVED", "files": []}})
    t.igual("GE-E59 GraphRun: el FAILED CAPABILITY_UNAVAILABLE armado valida por contrato", [],
            contrato.validar_resultado(fallida, request))
    registro.escribir_json(str(carpeta / registro.RESULT), fallida)
    t.igual("GE-E59 GraphRun: y el ultimo turno de A queda FAILED", "FAILED", _estado_de(armado, "a"))
    antes = _bytes_de(armado, request["executionId"])
    res = _grafo(armado)["res"] or {}
    t.igual("GE-E59 GraphRun: cierra FAILED con WORK_UNIT_NOT_SUCCEEDED por A FAILED, con "
            "CAPABILITY_UNAVAILABLE",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "a", request["executionId"], "FAILED",
                        "CAPABILITY_UNAVAILABLE")), (res.get("status"), _causa_de(res)))
    t.igual("GE-E59 GraphRun: sin despachar: ni marca, ni turno nuevo, ni invocacion al Host",
            ([], [(1, request["executionId"])], [], antes),
            (_despachos(armado, res.get("graphRunId") or "grf_" + "0" * 32), M72._turnos(armado, "a"),
             _invocaciones(bitacora), _bytes_de(armado, request["executionId"])))
    _valida(t, "GE-E59 GraphRun", armado, res.get("graphRunId") or "grf_" + "0" * 32)


# =============================================================================================
# ADM: `leer_plan`, `huella_esperada` y `execution_id` hasta la admision y el motor
# (GD-16, GD-27 pasos 3 y 4, GE-I04)
# =============================================================================================

OTRA_HUELLA = "sha256:" + "0" * 64


def _huella_del_plan(proy):
    return contrato.huella(M64._leer_json(M64._plan_de(proy, CLAVE)))


def _objetivo_cambiado(proy, unidad_id):
    """Reescribe el plan en el lugar y cambia solo el objetivo de una unidad: otra huella del plan."""
    def cambio(plan):
        for unidad in plan["workUnits"]:
            if unidad["id"] == unidad_id:
                unidad["objective"] = "otro objetivo, despues de planificar"
    M72._reescribir_plan(proy, cambio)


def _plan_replanificado(proy, unidad_id):
    """Como lo deja quien planifica: el plan reescrito en el lugar y el estado del flujo reconciliado
    con el plan nuevo. Sin la reconciliacion, la vigencia del flujo ya dice PLAN_STALE."""
    from estado_de_tarea import persistencia
    _objetivo_cambiado(proy, unidad_id)
    persistencia.reconciliar(str(proy), CLAVE)


def _eid(corrida):
    return M72._de(corrida, "executionId") or "exe_" + "0" * 32


def _request_de(proy, execution_id):
    return M64._leer_json(M72._carpeta(proy, execution_id) / registro.REQUEST)


def _sin_entrega(proy, execution_id, eco=None):
    """True si la Execution se rechazo antes de entregarse: ni entrega.json, ni prompt de sistema, ni
    proceso.json, y (con `eco`) el Host falso no recibio la invocacion."""
    carpeta = M72._carpeta(proy, execution_id)
    return (not (carpeta / registro.ENTREGA).exists() and not (carpeta / H.PROMPT_DE_SISTEMA).exists()
            and not (carpeta / registro.PROCESO).exists() and (eco is None or not Path(eco).exists()))


def _parametros(funcion):
    return [(p.name, p.default) for p in inspect.signature(funcion).parameters.values()]


def _nombres_llamados(nodo):
    return set(c.func.id if isinstance(c.func, ast.Name) else c.func.attr
               for c in ast.walk(nodo)
               if isinstance(c, ast.Call) and isinstance(c.func, (ast.Name, ast.Attribute)))


def test_ge_e25_las_firmas_solo_suman_parametros_opcionales_al_final(t):
    """GE-E25 (c) — Sin los parametros nuevos, Task 4 igual que hoy: `motor.ejecutar` suma
    `execution_id` y `huella_esperada`, y `al_entregar` suma `huella_esperada`, siempre al final y con
    `None`, sin mover ninguno de los que ya estaban. `al_pedir` no cambia (ya acepta `execution_id`) y
    `leer_plan` es publico, de dos parametros."""
    vacio = inspect.Parameter.empty
    t.igual("GE-E25 motor.ejecutar: los once de siempre, en su orden, y los dos nuevos al final con None",
            [("proyecto", vacio), ("clave", vacio), ("unidad", vacio), ("pedido_por", vacio),
             ("adaptador", None), ("config", None), ("catalogo", None), ("compuerta", None),
             ("cargar_registro", None), ("antes_de_reservar", None), ("antes_de_entregar", None),
             ("execution_id", None), ("huella_esperada", None)], _parametros(motor.ejecutar))
    t.igual("GE-E25 al_entregar: los seis de siempre, en su orden, y huella_esperada al final con None",
            [("proyecto", vacio), ("request", vacio), ("adaptador", vacio), ("compuerta", None),
             ("cargar_registro", None), ("huella", None), ("huella_esperada", None)],
            _parametros(admision.al_entregar))
    t.igual("GE-E25 al_pedir no cambia: no recibe huella_esperada, y ya aceptaba execution_id",
            [("proyecto", vacio), ("clave", vacio), ("unidad_id", vacio), ("pedido_por", vacio),
             ("catalogo", vacio), ("compuerta", None), ("cargar_registro", None),
             ("execution_id", None)], _parametros(admision.al_pedir))
    t.igual("GE-E25 leer_plan es publico y de dos parametros",
            [("proyecto", vacio), ("clave", vacio)], _parametros(admision.leer_plan))


def test_ge_e25_leer_plan_es_publico_y_es_el_unico_lector(t):
    """GE-E25 (paso 3) — `admision.leer_plan(proyecto, clave)` tiene la semantica de siempre de la regla
    de lectura: el plan, o Rechazo(PLAN_UNREADABLE) si falta, no es JSON, no es un objeto o repite
    unidades. Es el unico lector: `_regla` lo llama, `al_pedir` informa lo mismo que el, y la admision no
    abre el plan en otra funcion. Nadie mas referenciaba `_leer_plan` de la admision (la de la refutacion
    es otra), asi que no queda un alias."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    ruta = M64._plan_de(proy, CLAVE)
    crudo = ruta.read_bytes()
    t.igual("GE-E25 leer_plan devuelve el plan guardado", M64._leer_json(ruta),
            admision.leer_plan(str(proy), CLAVE))

    repetido = M64._leer_json(ruta)
    repetido["workUnits"].append(dict(repetido["workUnits"][0]))
    casos = (("sin plan guardado", None),
             ("un JSON cortado", b'{"meta": {"task_key": '),
             ("un JSON que no es un objeto", b"[1, 2]"),
             ("una unidad repetida", json.dumps(repetido).encode("utf-8")))
    catalogo = limpieza.cargar_catalogo()
    for nombre, contenido in casos:
        if contenido is None:
            ruta.unlink()
        else:
            ruta.write_bytes(contenido)
        try:
            admision.leer_plan(str(proy), CLAVE)
            rechazo = None
        except admision.Rechazo as r:
            rechazo = r
        t.igual("GE-E25 leer_plan %s: Rechazo con PLAN_UNREADABLE" % nombre, "PLAN_UNREADABLE",
                rechazo.codigo if rechazo else None)
        _, error, _, _ = admision.al_pedir(str(proy), CLAVE, "uno", PIDE, catalogo)
        t.igual("GE-E25 %s: al_pedir informa el mismo codigo y el mismo detalle que leer_plan" % nombre,
                (rechazo.codigo, rechazo.detalle) if rechazo else None,
                (error["code"], error["detail"]) if error else None)
    ruta.write_bytes(crudo)

    arbol = ast.parse((M72.EJECUCION / "admision.py").read_text(encoding="utf-8"))
    funciones = {n.name: n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}
    t.verdadero("GE-E25 la admision tiene leer_plan, y ya no un _leer_plan aparte",
                "leer_plan" in funciones and "_leer_plan" not in funciones)
    t.verdadero("GE-E25 la regla de las quince condiciones lee el plan con leer_plan",
                "leer_plan" in _nombres_llamados(funciones["_regla"]))
    t.igual("GE-E25 solo leer_plan abre archivos y pasa el plan por aceptar_guardado: un lector",
            (["leer_plan"], ["leer_plan"]),
            ([n for n, f in funciones.items() if "open" in _nombres_llamados(f)
              and n not in ("_capacidades",)],
             [n for n, f in funciones.items() if "aceptar_guardado" in _nombres_llamados(f)]))


def test_ge_e25_con_la_huella_esperada_igual_corre_como_siempre(t):
    """GE-E25 (a) — `motor.ejecutar` con `huella_esperada` igual a la del plan corre como siempre: la
    Execution se admite, se entrega, el Host la recibe y termina SUCCEEDED, con los mismos archivos que
    una corrida sin el parametro."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    eco = M72._eco(proy, "eco-con")
    M72._guion(proy, eco=str(eco))
    huella = _huella_del_plan(proy)
    con = M72._corrida(proy, "uno", huella_esperada=huella)
    eid = _eid(con)

    t.igual("GE-E25 (a) el motor no levanta ni devuelve un ExecutionError", (None, None),
            (con["exc"], con["err"]))
    t.igual("GE-E25 (a) termina SUCCEEDED, sin codigo de error", ("SUCCEEDED", None),
            (M72._de(con, "status"), M72._codigo(con)))
    t.verdadero("GE-E25 (a) se entrego: hay entrega.json", (M72._carpeta(proy, eid) / registro.ENTREGA).is_file())
    t.verdadero("GE-E25 (a) y el Host falso recibio la invocacion", eco.is_file())
    t.igual("GE-E25 (a) la request lleva la huella del plan, que es la esperada", huella,
            _request_de(proy, eid)["plan"]["planFingerprint"])
    t.igual("GE-E25 (a) un turno nombra a la Execution", [(1, eid)], M72._turnos(proy, "uno"))

    otro = M72._proyecto(M72._unidades("uno", "dos"))
    M72._guion(otro, eco=str(M72._eco(otro, "eco-sin")))
    sin = M72._corrida(otro, "uno")
    t.igual("GE-E25 (a) sin el parametro termina igual", ("SUCCEEDED", None),
            (M72._de(sin, "status"), M72._codigo(sin)))
    t.igual("GE-E25 (a) y deja los mismos archivos que con el",
            sorted(p.name for p in M72._carpeta(otro, _eid(sin)).iterdir()),
            sorted(p.name for p in M72._carpeta(proy, eid).iterdir()))
    t.igual("GE-E25 (a) y el mismo resultado, campo por campo",
            sorted(sin["res"]), sorted(con["res"]))


def test_ge_e25_con_otra_huella_la_execution_termina_rejected_plan_changed(t):
    """GE-E25 (b) — Con `huella_esperada` distinta de la del plan, la Execution se crea y termina
    REJECTED con PLAN_CHANGED, sin entrega.json y sin que el Host reciba la invocacion. Ocupa un turno de
    una clave que admite reintento (GD-16)."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    eco = M72._eco(proy, "eco-otra")
    M72._guion(proy, eco=str(eco))
    huella = _huella_del_plan(proy)
    corrida = M72._corrida(proy, "uno", huella_esperada=OTRA_HUELLA)
    eid = _eid(corrida)

    t.igual("GE-E25 (b) el motor no levanta, y no es un rechazo al pedir: hay Execution", (None, None),
            (corrida["exc"], corrida["err"]))
    t.igual("GE-E25 (b) REJECTED con PLAN_CHANGED", ("REJECTED", "PLAN_CHANGED"),
            (M72._de(corrida, "status"), M72._codigo(corrida)))
    t.igual("GE-E25 (b) un turno nombra a la Execution y su estado derivado es REJECTED",
            ([(1, eid)], "REJECTED"),
            (M72._turnos(proy, "uno"), registro.estado(str(proy), CLAVE, eid)["estado"]))
    t.verdadero("GE-E25 (b) sin entrega.json, sin prompt de sistema, sin proceso y sin invocacion al Host",
                _sin_entrega(proy, eid, eco))
    resultado = corrida["res"]
    t.igual("GE-E25 (b) sin inicio, sin evidencia, sin host y sin AgentReport", (None,) * 5,
            tuple(resultado[c] for c in ("startedAt", "evidence", "host", "agentDeclaredStatus",
                                         "output")))
    t.contiene("GE-E25 (b) el detail habla de la huella", "huella", resultado["error"]["detail"])
    t.igual("GE-E25 (b) la request es la del plan de hoy: el que no coincide es lo esperado", huella,
            _request_de(proy, eid)["plan"]["planFingerprint"])
    t.igual("GE-E25 (b) el resultado valida contra su request", [],
            contrato.validar_resultado(resultado, _request_de(proy, eid)))

    de_nuevo = M72._corrida(proy, "uno")
    t.igual("GE-E25 (b) un REJECTED admite el reintento: sin el parametro, SUCCEEDED en el turno 2",
            ("SUCCEEDED", [(1, eid), (2, _eid(de_nuevo))]),
            (M72._de(de_nuevo, "status"), M72._turnos(proy, "uno")))
    t.verdadero("GE-E25 (b) y ahora si el Host recibio la invocacion", eco.is_file())


def test_ge_e25_plan_changed_va_en_el_lugar_de_la_condicion_4(t):
    """GE-E25 — La comprobacion de `huella_esperada` es la condicion 4 de la regla, en su lugar de la
    precedencia: la condicion 1 (CONTRACT_INVALID) y la 2 (PLAN_UNREADABLE) le ganan, y le gana a la 6
    (DELEGATION_NOT_ALLOWED) y a la 10 (AGENT_UNAVAILABLE). Se prueba sobre `al_entregar` directo: es lo
    que el motor llama."""
    lugar = list(contrato.PRECEDENCIA).index
    t.verdadero("GE-E25 en PRECEDENCIA: CONTRACT_INVALID < PLAN_UNREADABLE < PLAN_CHANGED < "
                "DELEGATION_NOT_ALLOWED < AGENT_UNAVAILABLE",
                lugar("CONTRACT_INVALID") < lugar("PLAN_UNREADABLE") < lugar("PLAN_CHANGED")
                < lugar("DELEGATION_NOT_ALLOWED") < lugar("AGENT_UNAVAILABLE"))

    def con_request():
        proy = M72._proyecto(M72._unidades("uno"))
        return proy, _requested_sin_motor(proy, "uno"), _adaptador(sys.platform)

    def entregar(proy, request, adaptador, **kw):
        rechazo, derivado = admision.al_entregar(str(proy), request, adaptador, **kw)
        return (rechazo.codigo if rechazo else None), derivado

    proy, request, adaptador = con_request()
    huella = _huella_del_plan(proy)
    t.igual("GE-E25 sin huella_esperada se puede entregar, como hoy", None,
            entregar(proy, request, adaptador)[0])
    t.igual("GE-E25 con la huella del plan tambien", None,
            entregar(proy, request, adaptador, huella_esperada=huella)[0])
    codigo, derivado = entregar(proy, request, adaptador, huella_esperada=OTRA_HUELLA)
    t.igual("GE-E25 con otra, PLAN_CHANGED y nada derivado", ("PLAN_CHANGED", None), (codigo, derivado))

    M72._contexto_cambiado(proy)
    t.igual("GE-E25 con el flujo que ya no permite delegar y sin el parametro, DELEGATION_NOT_ALLOWED",
            "DELEGATION_NOT_ALLOWED", entregar(proy, request, adaptador)[0])
    t.igual("GE-E25 pero con otra huella esperada gana PLAN_CHANGED (4 antes que 6)", "PLAN_CHANGED",
            entregar(proy, request, adaptador, huella_esperada=OTRA_HUELLA)[0])

    proy, request, adaptador = con_request()
    (Path(proy) / ".claude" / "agents" / "dev-backend.md").unlink()
    t.igual("GE-E25 con el agente borrado y sin el parametro, AGENT_UNAVAILABLE", "AGENT_UNAVAILABLE",
            entregar(proy, request, adaptador)[0])
    t.igual("GE-E25 pero con otra huella esperada gana PLAN_CHANGED (4 antes que 10)", "PLAN_CHANGED",
            entregar(proy, request, adaptador, huella_esperada=OTRA_HUELLA)[0])

    proy, request, adaptador = con_request()
    tocada = json.loads(json.dumps(request))
    tocada["workUnit"]["objective"] = "otro objetivo, que el plan no tiene"
    tocada["workUnitFingerprint"] = contrato.huella(tocada["workUnit"])
    t.igual("GE-E25 una request que valida pero con otra WorkUnit que la del plan: CONTRACT_INVALID, "
            "con o sin el parametro (1 antes que 4)", ["CONTRACT_INVALID"] * 2,
            [entregar(proy, tocada, adaptador)[0],
             entregar(proy, tocada, adaptador, huella_esperada=OTRA_HUELLA)[0]])

    M64._plan_de(proy, CLAVE).unlink()
    t.igual("GE-E25 sin plan guardado, PLAN_UNREADABLE con o sin el parametro (2 antes que 4)",
            ["PLAN_UNREADABLE"] * 2,
            [entregar(proy, request, adaptador)[0],
             entregar(proy, request, adaptador, huella_esperada=OTRA_HUELLA)[0]])


def test_ge_e24_mitad_del_motor_el_plan_cambio_antes_de_que_el_motor_lo_lea(t):
    """GE-E24 (la mitad del motor, y al final la del GraphRun) — El plan se reescribe cambiando solo una
    unidad C sin dependencias despues de que el llamador leyo la huella F y antes de que el motor lea el
    plan: con `huella_esperada=F`, o no hay Execution (la admision al pedir ya rechaza), o la Execution de
    C queda REJECTED PLAN_CHANGED sin entrega.json. En los dos casos el Host no recibe la invocacion. La
    mitad del GraphRun (que cierre con PLAN_FINGERPRINT_CHANGED) se agrego en la etapa 5a, al final."""
    proy = M72._proyecto(M72._unidades("a", "c"))
    eco = M72._eco(proy, "eco-c")
    M72._guion(proy, eco=str(eco))
    huella = _huella_del_plan(proy)
    _objetivo_cambiado(proy, "c")
    nueva = _huella_del_plan(proy)
    t.verdadero("GE-E24 la reescritura cambio la huella del plan", nueva != huella)

    # Reescrito a mano, sin reconciliar el flujo: ya la admision al pedir lo rechaza. No hay Execution.
    a_mano = M72._corrida(proy, "c", huella_esperada=huella)
    t.igual("GE-E24 sin reconciliar el flujo, al pedir da DELEGATION_NOT_ALLOWED: no hay Execution",
            (None, None, "DELEGATION_NOT_ALLOWED", [], False),
            (a_mano["exc"], a_mano["res"], M72._codigo(a_mano), M72._carpetas(proy), eco.exists()))

    # Reescrito por quien planifica, con el flujo al dia: la admision al pedir lo admite con la huella
    # nueva, y es `huella_esperada` la que lo detiene al entregar.
    from estado_de_tarea import persistencia
    persistencia.reconciliar(str(proy), CLAVE)
    plan_antes = M64._plan_de(proy, CLAVE).read_bytes()

    corrida = M72._corrida(proy, "c", huella_esperada=huella)
    eid = _eid(corrida)
    t.igual("GE-E24 hay Execution de C y termina REJECTED con PLAN_CHANGED", ((None, None), "REJECTED",
            "PLAN_CHANGED"), ((corrida["exc"], corrida["err"]), M72._de(corrida, "status"),
                              M72._codigo(corrida)))
    t.igual("GE-E24 su request es la del plan nuevo, no la de la huella esperada", nueva,
            _request_de(proy, eid)["plan"]["planFingerprint"])
    t.verdadero("GE-E24 sin entrega.json y el Host no recibio la invocacion",
                _sin_entrega(proy, eid, eco))
    t.igual("GE-E24 el archivo del plan es el que dejo la reescritura, sin cambios del motor",
            plan_antes, M64._plan_de(proy, CLAVE).read_bytes())
    t.igual("GE-E24 ninguna otra unidad tiene Execution", [eid], M72._carpetas(proy))

    sin = M72._corrida(proy, "c")
    t.igual("GE-E24 sin huella_esperada el motor entregaria esa misma unidad bajo la huella nueva: "
            "lo que el parametro evita", ("SUCCEEDED", nueva),
            (M72._de(sin, "status"), _request_de(proy, _eid(sin))["plan"]["planFingerprint"]))

    # La otra rama: una unidad que depende de otra ya SUCCEEDED bajo F. Bajo la huella nueva nada esta
    # satisfecho, y la admision rechaza al pedir: no hay Execution.
    otro = M72._proyecto([M64._unidad("a"), M64._unidad("b", dependencias=("a",))])
    eco_b = M72._eco(otro, "eco-b")
    M72._guion(otro)
    base = _huella_del_plan(otro)
    de_a = M72._corrida(otro, "a", huella_esperada=base)
    t.igual("GE-E24 con la huella esperada de siempre, A termina SUCCEEDED", "SUCCEEDED",
            M72._de(de_a, "status"))
    _plan_replanificado(otro, "b")
    M72._guion(otro, eco=str(eco_b))
    de_b = M72._corrida(otro, "b", huella_esperada=base)
    t.igual("GE-E24 al pedir, B bajo la huella nueva da DEPENDENCY_NOT_SATISFIED: no hay Execution",
            (None, None, "DEPENDENCY_NOT_SATISFIED"),
            (de_b["exc"], de_b["res"], M72._codigo(de_b)))
    t.igual("GE-E24 y no hay otra carpeta que la de A, ni invocacion al Host", ([_eid(de_a)], False),
            (M72._carpetas(otro), eco_b.exists()))

    # Entre la creacion y la entrega rige la regla de hoy: PLAN_CHANGED por la huella de la request.
    tercero = M72._proyecto(M72._unidades("a", "c"))
    eco_t = M72._eco(tercero, "eco-t")
    M72._guion(tercero, eco=str(eco_t))
    esperada = _huella_del_plan(tercero)
    entre = M72._corrida(tercero, "c", huella_esperada=esperada,
                         antes_de_entregar=lambda carpeta: _objetivo_cambiado(tercero, "c"))
    t.igual("GE-E24 con el plan cambiado entre la creacion y la entrega: REJECTED PLAN_CHANGED, sin "
            "entrega.json ni Host", ("REJECTED", "PLAN_CHANGED", True),
            (M72._de(entre, "status"), M72._codigo(entre), _sin_entrega(tercero, _eid(entre), eco_t)))

    # La mitad del GraphRun (etapa 5a): con un gancho que reescribe el plan despues del paso 7b y antes de
    # que el motor lo lea, el conductor cierra con PLAN_FINGERPRINT_CHANGED, con o sin Execution de C, y el
    # Host no recibe la invocacion de C.
    for reconciliado in (False, True):
        proy_g = M72._proyecto(M72._unidades("a", "c"))
        bitacora = _ruta_de_bitacora()
        M72._guion(proy_g, bitacora=str(bitacora))
        viejo = _huella_del_plan(proy_g)
        cambiar = _plan_replanificado if reconciliado else _objetivo_cambiado
        nombre = "reconciliando el flujo" if reconciliado else "sin reconciliar el flujo"

        def al_despachar(marca, proy_g=proy_g, cambiar=cambiar):
            if marca["workUnitId"] == "c":
                cambiar(proy_g, "c")

        res = _grafo(proy_g, ganchos={"despues_del_despacho": al_despachar})["res"] or {}
        t.igual("GE-E24 GraphRun, %s: cierra FAILED con PLAN_FINGERPRINT_CHANGED, atado a la huella de "
                "antes" % nombre, ("FAILED", "PLAN_FINGERPRINT_CHANGED", viejo),
                (res.get("status"), _causa_de(res)[0], res.get("planFingerprint")))
        t.igual("GE-E24 GraphRun, %s: el Host no recibio la invocacion de C" % nombre, ["a"],
                [i["workUnitId"] for i in _intervalos(bitacora)])
        nueva = _huella_del_plan(proy_g)
        if reconciliado:
            eid_c = _eid_de(proy_g, "c", nueva)
            t.igual("GE-E24 GraphRun, %s: la Execution de C queda REJECTED PLAN_CHANGED, sin entrega.json"
                    % nombre, ("REJECTED", "PLAN_CHANGED", True),
                    (_estado_de(proy_g, "c", nueva),
                     ((registro.estado(str(proy_g), CLAVE, eid_c)["resultado"] or {}).get("error") or {})
                     .get("code"), _sin_entrega(proy_g, eid_c)))
            t.igual("GE-E24 GraphRun, %s: la request de esa Execution es la del plan nuevo" % nombre,
                    nueva, _request_de(proy_g, eid_c)["plan"]["planFingerprint"])
        else:
            t.igual("GE-E24 GraphRun, %s: no hay Execution de C, bajo ninguna huella" % nombre,
                    [None, None], [_estado_de(proy_g, "c", viejo), _estado_de(proy_g, "c", nueva)])
        _valida(t, "GE-E24 GraphRun, %s" % nombre, proy_g, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e25_execution_id_preasignado_es_el_de_la_execution(t):
    """GE-E25 (paso 4) — Con `execution_id`, ese es el id de la Execution creada: su carpeta, su
    request.json, su turno y su resultado. Tambien cuando termina REJECTED por `huella_esperada`: es lo
    que el GraphRun usa para derivar por un id que conoce antes del motor. Sin el, lo genera el
    registro, como hoy."""
    proy = M72._proyecto(M72._unidades("uno", "dos", "tres"))
    M72._guion(proy)
    exe = "exe_" + "0123456789abcdef" * 2
    corrida = M72._corrida(proy, "uno", execution_id=exe)
    t.igual("GE-E25 el resultado es de la Execution preasignada y SUCCEEDED", (None, exe, "SUCCEEDED"),
            (corrida["exc"], M72._de(corrida, "executionId"), M72._de(corrida, "status")))
    t.igual("GE-E25 su carpeta, su turno y su request son los de ese id",
            ([exe], [(1, exe)], exe, registro.estado(str(proy), CLAVE, exe)["estado"]),
            (M72._carpetas(proy), M72._turnos(proy, "uno"), _request_de(proy, exe)["executionId"],
             registro.estado(str(proy), CLAVE, exe)["estado"]))

    otro = "exe_" + "fedcba9876543210" * 2
    rechazada = M72._corrida(proy, "dos", execution_id=otro, huella_esperada=OTRA_HUELLA)
    t.igual("GE-E25 con huella_esperada distinta, la Execution REJECTED lleva el id preasignado",
            (None, otro, "REJECTED", "PLAN_CHANGED", [(1, otro)]),
            (rechazada["exc"], M72._de(rechazada, "executionId"), M72._de(rechazada, "status"),
             M72._codigo(rechazada), M72._turnos(proy, "dos")))

    sin = M72._corrida(proy, "tres")
    t.verdadero("GE-E25 sin el parametro, el id es uno nuevo de exe_ y 32 hexadecimales",
                registro.es(registro.ID, _eid(sin)) and _eid(sin) not in (exe, otro))


def test_ge_e25_un_execution_id_invalido_o_usado_es_lo_que_hace_hoy_la_admision(t):
    """GE-E25 (paso 4) — Un `execution_id` invalido da lo que `admision.al_pedir` ya da con un id
    externo: CONTRACT_INVALID al pedir, sin Execution, y el motor devuelve ese mismo error. Uno ya
    usado no lo mira `al_pedir`: lo detiene `registro.crear` (la carpeta ya existe) y el motor lo
    levanta como error del comando, sin tocar la Execution que ya estaba. El motor no inventa nada."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    eco = M72._eco(proy, "eco-malo")
    M72._guion(proy, eco=str(eco))
    catalogo = limpieza.cargar_catalogo()
    malos = ("exe_corto", "exe_" + "A" * 32, "EXE_" + "a" * 32, "exe_" + "g" * 32, "exe_" + "a" * 33,
             "../" + "a" * 36, 7)
    for malo in malos:
        _, directo, _, _ = admision.al_pedir(str(proy), CLAVE, "uno", PIDE, catalogo,
                                             execution_id=malo)
        corrida = M72._corrida(proy, "uno", execution_id=malo)
        t.igual("GE-E25 %r: al_pedir rechaza con CONTRACT_INVALID" % (malo,), "CONTRACT_INVALID",
                (directo or {}).get("code"))
        t.igual("GE-E25 %r: el motor devuelve el mismo ExecutionError, sin resultado ni excepcion"
                % (malo,), (None, None, directo), (corrida["exc"], corrida["res"], corrida["err"]))
    t.igual("GE-E25 ningun id invalido dejo carpeta ni turno, ni llego al Host",
            ([], [], False), (M72._carpetas(proy), M72._turnos(proy, "uno"), eco.exists()))

    exe = "exe_" + "ab" * 16
    primera = M72._corrida(proy, "uno", execution_id=exe)
    t.igual("GE-E25 con un id valido, la primera Execution termina SUCCEEDED", "SUCCEEDED",
            M72._de(primera, "status"))
    antes, arbol = _de_la_execution(proy, exe), M72._arbol(proy)
    eco_dos = M72._eco(proy, "eco-usado")
    M72._guion(proy, eco=str(eco_dos))
    segunda = M72._corrida(proy, "dos", execution_id=exe)
    t.verdadero("GE-E25 con el id ya usado, el motor levanta el error del comando de registro.crear",
                (segunda["exc"] or "").startswith("ErrorDelComando")
                and "FileExistsError" in segunda["exc"])
    t.igual("GE-E25 sin resultado ni ExecutionError", (None, None), (segunda["res"], segunda["err"]))
    t.igual("GE-E25 la Execution que ya estaba queda identica, y no se crea nada mas",
            (antes, arbol, [(1, exe)], False),
            (_de_la_execution(proy, exe), M72._arbol(proy), M72._turnos(proy, "uno"),
             eco_dos.exists()))
    t.igual("GE-E25 y la unidad dos no tiene turno", [], M72._turnos(proy, "dos"))


# =============================================================================================
# REG: el registro del GraphRun (GD-03, GD-12, GD-20, §14.1 y §16; GD-27 paso 5)
# =============================================================================================
#
# Solo las primitivas de `registro.py`, sin conductor. Lo que nombra al conductor es de las etapas 5 y
# 6: GE-E28, GE-E29 y GE-E43 (dos procesos que se disputan el candado con un `--grafo`), GE-E36 a
# GE-E42 (los cortes), GE-E46 a GE-E52 (la cancelacion), GE-E60 en lo que toca a `result.json` contra
# su schema (etapa 8), y GE-E61 y GE-E62 con un GraphRun de verdad.

HUELLA_F = "sha256:" + "f" * 64
GRAFOS = registro.GRAFOS
REGISTRO_PY = M72.EJECUCION / "registro.py"


def _vacio():
    """Un proyecto sin nada, para lo que prueba solo las primitivas del registro."""
    return M64._tmp("ge73-reg-")


def _inicio(nodos=(("a", ()), ("b", ("a",))), **pisa):
    """El `inicio.json` de un GraphRun de prueba, con la forma que le pone el conductor: el plan A->B."""
    doc = {"graphRunId": registro.nuevo_id_de_grafo(), "taskKey": CLAVE, "planFingerprint": HUELLA_F,
           "planId": "pln_" + CLAVE, "planVersion": 1, "requestedBy": PIDE,
           "startedAt": registro.ahora(),
           "nodes": [{"workUnitId": n, "dependencies": list(d)} for n, d in nodos],
           "order": [n for n, _ in nodos]}
    doc.update(pisa)
    return doc


def _terminal(graph_run_id, estado="SUCCEEDED", **pisa):
    """Un `result.json` minimo: lo que el registro lee para derivar el estado. El resto de
    graph-run-result/1.0 lo arma el conductor (etapa 5) y lo valida su schema (etapa 8)."""
    doc = {"graphRunId": graph_run_id, "taskKey": CLAVE, "status": estado}
    doc.update(pisa)
    return doc


def _grafo_completo(proy, estado="FAILED"):
    """Un GraphRun hecho solo con las primitivas, con las cinco marcas y el orden de un conductor:
    toma el candado, crea, despacha dos, cancela, cierra y suelta. Devuelve (graphRunId, [executionId])."""
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    if not candado:
        raise AssertionError("el candado de la tarea de prueba estaba tomado")
    try:
        inicio = _inicio()
        gid = inicio["graphRunId"]
        registro.crear_grafo(str(proy), inicio)
        ejecuciones = [registro.nuevo_id(), registro.nuevo_id()]
        registro.registrar_despacho(str(proy), CLAVE, gid, "a", ejecuciones[0])
        registro.registrar_despacho(str(proy), CLAVE, gid, "b", ejecuciones[1])
        registro.marcar_cancelacion(str(proy), CLAVE, gid, PIDE)
        registro.escribir_terminal(str(proy), CLAVE, gid, _terminal(gid, estado))
    finally:
        candado.soltar()
    return gid, ejecuciones


def _levanta(funcion):
    """El nombre del tipo de la excepcion que levanta `funcion`, o None."""
    try:
        funcion()
    except Exception as e:                       # noqa: BLE001 - el tipo se mira
        return type(e).__name__
    return None


def _grafos_de(proy):
    """{ruta: huella} de lo que hay bajo grafos/ de la tarea."""
    prefijo = "%s/%s/" % (CLAVE, GRAFOS)
    return {k: v for k, v in M72._arbol(proy).items() if k.startswith(prefijo)}


def _de_grafos(proy, solo=Path.is_file):
    base = M72._ejecuciones(proy) / CLAVE
    return sorted(p.relative_to(base).as_posix() for p in (base / GRAFOS).rglob("*") if solo(p))


def _definicion(nombre):
    for n in ast.walk(ast.parse(REGISTRO_PY.read_text(encoding="utf-8"))):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == nombre:
            return n
    return None


def _nombres(nodo):
    """Los nombres y los atributos que aparecen adentro de un nodo."""
    return (set(n.id for n in ast.walk(nodo) if isinstance(n, ast.Name))
            | set(n.attr for n in ast.walk(nodo) if isinstance(n, ast.Attribute)))


def _tomar_pronto(proy, limite=10):
    """El candado de la tarea, esperando a que el sistema suelte el de un proceso que acaba de morir:
    en Windows el sistema operativo lo suelta cuando puede."""
    fin = time.time() + limite
    while True:
        candado = registro.CandadoDeTarea(str(proy), CLAVE)
        if candado or time.time() > fin:
            return candado
        time.sleep(0.05)


def test_ge_e61_un_graphrun_hecho_con_las_primitivas_deja_exactamente_sus_archivos(t):
    """GE-E61 (primitivas) — Un GraphRun creado solo con las funciones del registro deja exactamente
    `vivo.lock`, `inicio.json`, `despachos/<NNN>.json`, `cancelacion.json` y `result.json`, y nada mas:
    ningun `state.json`, ningun temporal, nada fuera de `grafos/`. (GD-12, GE-I17, GE-I29.) La mitad
    del GraphRun, con un conductor que lo escribe, es de las etapas 5 y 6."""
    proy = _vacio()
    antes = M72._proyecto_sin_git(proy)
    gid, _ = _grafo_completo(proy)
    base = M72._ejecuciones(proy) / CLAVE
    marcas = ["grafos/%s/%s" % (gid, m) for m in ("inicio.json", "despachos/001.json",
                                                   "despachos/002.json", "cancelacion.json",
                                                   "result.json")]

    t.igual("GE-E61 los archivos son exactamente el candado y las cuatro marcas",
            sorted(["grafos/vivo.lock"] + marcas), _de_grafos(proy))
    t.igual("GE-E61 y las carpetas de grafos/, la del GraphRun y la de sus despachos",
            sorted(["grafos/%s" % gid, "grafos/%s/despachos" % gid]),
            _de_grafos(proy, Path.is_dir))
    t.vacio("GE-E61 no hay un archivo de estado: ni state.json ni ninguno que no sea una marca",
            [r for r in _de_grafos(proy) if r.rsplit("/", 1)[-1] not in (
                "vivo.lock", "inicio.json", "001.json", "002.json", "cancelacion.json", "result.json")
             or r.endswith("state.json")])
    t.vacio("GE-E61 ni un state.json en ningun lugar de la tarea", list(base.rglob("state.json")))
    t.igual("GE-E61 lo unico que cambio en el proyecto esta bajo grafos/", [],
            [d for d in M64._diferencias(antes, M72._proyecto_sin_git(proy))
             if not d.split(" ", 1)[1].startswith(".claude/ejecuciones/%s/grafos/" % CLAVE)])
    t.igual("GE-E61 la carpeta de la tarea no tiene mas que grafos/: ni claves/ ni una exe_",
            ["grafos"], sorted(os.listdir(str(base))))
    t.vacio("GE-E61 sin temporales de escritura", M72._temporales(proy))
    t.igual("GE-E61 vivo.lock esta vacio: sin pid ni fecha", 0,
            (base / GRAFOS / registro.VIVO).stat().st_size)


def test_ge_e61_ninguna_marca_se_puede_escribir_dos_veces(t):
    """GE-E61 (primitivas) — Cada marca rechaza una segunda escritura y no toca la que estaba: gana la
    primera. `result.json` no se reescribe con `os.replace` (GM-34), y el registro no escribe de
    ninguna forma que no sea la primitiva de una sola vez. (GD-12, GE-I14, GE-I17.)"""
    proy = _vacio()
    gid, _ = _grafo_completo(proy, "FAILED")
    leido = registro.leer_grafo(str(proy), CLAVE, gid)
    antes = _grafos_de(proy)
    intentos = (
        ("inicio.json", lambda: registro.crear_grafo(str(proy), leido["inicio"])),
        ("la marca de despacho 001", lambda: registro.escribir_json(
            registro.ruta_del_despacho(str(proy), CLAVE, gid, 1), {"numero": 1})),
        ("cancelacion.json", lambda: registro.marcar_cancelacion(str(proy), CLAVE, gid, "otra")),
        ("result.json", lambda: registro.escribir_terminal(str(proy), CLAVE, gid,
                                                           _terminal(gid, "SUCCEEDED"))),
    )
    for nombre, intento in intentos:
        t.igual("GE-E61 %s: una segunda escritura levanta FileExistsError" % nombre,
                "FileExistsError", _levanta(intento))
    t.igual("GE-E61 y no toca ni un byte de lo que habia", antes, _grafos_de(proy))
    t.vacio("GE-E61 ni deja un temporal", M72._temporales(proy))
    t.igual("GE-E61 el terminal sigue siendo el primero: gana el primero", "FAILED",
            registro.leer_grafo(str(proy), CLAVE, gid)["estado"])

    nueva = registro.registrar_despacho(str(proy), CLAVE, gid, "c", registro.nuevo_id())
    ahora = _grafos_de(proy)
    t.igual("GE-E61 registrar_despacho nunca pisa: la siguiente es la 003", 3, nueva["numero"])
    t.igual("GE-E61 y la 001 y la 002 quedan como estaban", antes, {k: ahora[k] for k in antes})
    t.igual("GE-E61 y lo unico nuevo es la 003",
            ["%s/%s/%s/despachos/003.json" % (CLAVE, GRAFOS, gid)], sorted(set(ahora) - set(antes)))

    permitidas = {"os.makedirs", "os.mkdir", "os.write", "os.link", "os.unlink", "tempfile.mkstemp",
                  "shutil.rmtree", "os.open para escribir"}
    t.vacio("GE-E61 registro.py no escribe con os.replace, os.rename ni open para escribir: solo con "
            "la primitiva de una sola vez (GM-34)",
            sorted(set(que for _, que in M72._escribe(REGISTRO_PY)) - permitidas))
    t.igual("GE-E61 y esa primitiva, os.link, se llama en un solo lugar", 1,
            len([n for n in ast.walk(ast.parse(REGISTRO_PY.read_text(encoding="utf-8")))
                 if isinstance(n, ast.Call) and M72._nombre(n.func) == "os.link"]))


def test_gd12_dos_procesos_que_escriben_la_misma_marca_gana_uno(t):
    """GD-12 y GE-E61 (primitivas) — Dos procesos del sistema operativo, parados en la misma puerta,
    escriben la misma marca (`cancelacion.json`, `result.json`): gana exactamente uno, el otro recibe
    FileExistsError, y la marca es la del que gano. La carrera de ME-E18, sobre las marcas del
    GraphRun."""
    proy = _vacio()
    for que, valores in (("cancelacion", ("ana", "beto")), ("terminal", ("SUCCEEDED", "FAILED"))):
        for ronda in range(1, 4):
            inicio = _inicio()
            gid = inicio["graphRunId"]
            registro.crear_grafo(str(proy), inicio)
            marcas = M64._tmp("ge73-marcas-")
            a = _lanzar("competir", proy, marcas, que, gid, valores[0])
            b = _lanzar("competir", proy, marcas, que, gid, valores[1])
            sal = (_salida(a), _salida(b))
            etiqueta = "GD-12 %s, ronda %d" % (que, ronda)
            t.igual("%s: ninguno levanta otra cosa que FileExistsError" % etiqueta, [None, None],
                    [s.get("exc") for s in sal])
            t.igual("%s: exactamente uno gana" % etiqueta, 1, len([s for s in sal if s.get("gano")]))
            ganador = valores[0] if sal[0].get("gano") else valores[1]
            leido = registro.leer_grafo(str(proy), CLAVE, gid)
            escrito = ((leido["cancelacion"] or {}).get("pedidoPor") if que == "cancelacion"
                       else (leido["resultado"] or {}).get("status"))
            t.igual("%s: la marca es la del que gano" % etiqueta, ganador, escrito)
    t.vacio("GD-12 ninguna carrera dejo un temporal", M72._temporales(proy))


def test_gd03_el_id_del_graphrun_es_grf_y_32_hexadecimales_al_azar(t):
    """GD-03 — `grf_` y 32 hexadecimales, del generador criptografico: no de la TaskKey, de la huella,
    del pid, de la sesion ni de la hora. Un GraphRun que se vuelve a lanzar es otro (GE-E07)."""
    ids = [registro.nuevo_id_de_grafo() for _ in range(300)]
    t.vacio("GD-03 todos son grf_ y 32 hexadecimales, por fullmatch",
            [i for i in ids if not registro.es(registro.ID_DE_GRAFO, i)])
    t.igual("GD-03 son 300 ids distintos", 300, len(set(ids)))
    t.vacio("GD-03 y ninguno es un exe_", [i for i in ids if i.startswith("exe_")])

    real = registro.secrets.token_hex
    registro.secrets.token_hex = lambda n: "ab" * n
    try:
        fijo = registro.nuevo_id_de_grafo()
    finally:
        registro.secrets.token_hex = real
    t.igual("GD-03 es grf_ mas lo que da el generador, 16 bytes: no se arma con nada mas",
            "grf_" + "ab" * 16, fijo)
    t.vacio("GD-03 y la funcion no nombra la TaskKey, la huella, el pid, la sesion ni la hora",
            sorted(_nombres(_definicion("nuevo_id_de_grafo")) & {
                "clave", "taskKey", "huella", "planFingerprint", "getpid", "time", "ahora", "uuid",
                "uuid1", "uuid4", "random", "hashlib", "session", "sessionRef"}))


def test_gd03_un_id_o_una_taskkey_que_no_son_lo_que_dicen_no_se_vuelven_ruta(t):
    """GD-03 — Los ids se validan con `fullmatch` antes de volverse rutas, como un executionId
    (T4 MD-15): ningun `\\n` final, mayusculas, otra longitud, otro prefijo ni un tramo de ruta. Vale
    para toda funcion del registro que reciba un graphRunId o una TaskKey."""
    proy = str(_vacio())
    bueno = registro.nuevo_id_de_grafo()
    malos = (bueno + "\n", bueno.upper(), "grf_" + "a" * 31, "grf_" + "a" * 33, "grf_" + "g" * 32,
             "exe_" + "a" * 32, "../" + "a" * 36, bueno + "/x", "", None, 7)
    exe = registro.nuevo_id()
    funciones = (
        ("carpeta_de_grafo", lambda g: registro.carpeta_de_grafo(proy, CLAVE, g)),
        ("ruta_del_despacho", lambda g: registro.ruta_del_despacho(proy, CLAVE, g, 1)),
        ("leer_grafo", lambda g: registro.leer_grafo(proy, CLAVE, g)),
        ("despachos", lambda g: registro.despachos(proy, CLAVE, g)),
        ("cancelada", lambda g: registro.cancelada(proy, CLAVE, g)),
        ("propias", lambda g: registro.propias(proy, CLAVE, g)),
        ("registrar_despacho", lambda g: registro.registrar_despacho(proy, CLAVE, g, "a", exe)),
        ("marcar_cancelacion", lambda g: registro.marcar_cancelacion(proy, CLAVE, g, "ana")),
        ("escribir_terminal", lambda g: registro.escribir_terminal(proy, CLAVE, g, _terminal(g))),
        ("crear_grafo", lambda g: registro.crear_grafo(proy, dict(_inicio(), graphRunId=g))),
    )
    t.vacio("GD-03 el id bueno se acepta como ruta",
            [] if _levanta(lambda: registro.carpeta_de_grafo(proy, CLAVE, bueno)) is None else ["no"])
    t.vacio("GD-03 ninguna funcion acepta un graphRunId malo: todas levantan RegistroInvalido",
            ["%s(%r)" % (nombre, malo) for nombre, funcion in funciones for malo in malos
             if _levanta(lambda: funcion(malo)) != "RegistroInvalido"])
    t.igual("GD-03 y no se creo nada en el proyecto", {}, M72._arbol(proy))

    claves_malas = ("../x", CLAVE + "\n", "", "GCBA", "GCBA-72/../x", None)
    t.vacio("GD-03 una TaskKey mala tampoco se vuelve ruta: ni la carpeta, ni el candado",
            ["%s(%r)" % (nombre, clave) for clave in claves_malas for nombre, funcion in (
                ("carpeta_de_grafos", lambda c: registro.carpeta_de_grafos(proy, c)),
                ("CandadoDeTarea", lambda c: registro.CandadoDeTarea(proy, c)),
                ("grafos_de", lambda c: registro.grafos_de(proy, c)),
                ("activos", lambda c: registro.activos(proy, c)))
             if _levanta(lambda: funcion(clave)) != "RegistroInvalido"])
    t.igual("GD-03 y no se creo nada con ninguna", {}, M72._arbol(proy))


def test_ge_e60_cada_marca_tiene_exactamente_sus_claves(t):
    """GE-E60 (registro) — Cada marca tiene exactamente sus claves, que son cerradas, y lo que se
    escribe se valida: una clave de mas, una de menos o un tipo malo levantan RegistroInvalido y no
    dejan nada. Las marcas no tienen schema (GD-12). (La otra mitad de GE-E60, `result.json` contra
    `graph-run-result.schema.json`, `inicio.json` con los `workUnitId` del plan y cada `error.code`,
    es de las etapas 5 y 8.)"""
    proy = _vacio()
    gid, _ = _grafo_completo(proy)
    base = Path(registro.carpeta_de_grafo(str(proy), CLAVE, gid))
    leido = registro.leer_grafo(str(proy), CLAVE, gid)

    t.igual("GE-E60 inicio.json: las nueve claves, y nada mas",
            sorted(("graphRunId", "taskKey", "planFingerprint", "planId", "planVersion",
                    "requestedBy", "startedAt", "nodes", "order")),
            sorted(M64._leer_json(base / registro.INICIO)))
    t.igual("GE-E60 cada nodo de inicio.json: workUnitId y dependencies",
            [["dependencies", "workUnitId"]] * 2,
            [sorted(n) for n in M64._leer_json(base / registro.INICIO)["nodes"]])
    t.igual("GE-E60 la marca de despacho: numero, workUnitId, executionId y dispatchedAt",
            ["dispatchedAt", "executionId", "numero", "workUnitId"],
            sorted(M64._leer_json(base / registro.DESPACHOS / "001.json")))
    t.igual("GE-E60 cancelacion.json: pedidoEn y pedidoPor", ["pedidoEn", "pedidoPor"],
            sorted(M64._leer_json(base / registro.CANCELACION)))
    t.igual("GE-E60 el nodo y el orden de inicio.json son los que se escribieron",
            (["a", "b"], [{"workUnitId": "a", "dependencies": []},
                          {"workUnitId": "b", "dependencies": ["a"]}]),
            (leido["inicio"]["order"], leido["inicio"]["nodes"]))

    vacio = _vacio()
    base_inicio = _inicio()
    rotos = [("una clave de mas", dict(base_inicio, extra=1))]
    rotos += [("sin %s" % c, {k: v for k, v in base_inicio.items() if k != c}) for c in base_inicio]
    rotos += [("%s: %r" % (c, v), dict(base_inicio, **{c: v})) for c, v in (
        ("graphRunId", "exe_" + "a" * 32), ("taskKey", "x"), ("planFingerprint", "sha256:abc"),
        ("planId", 7), ("planVersion", 0), ("planVersion", True), ("planVersion", "1"),
        ("requestedBy", "  "), ("startedAt", "ayer"), ("startedAt", "2026-10-14T10:00:00Z\n"),
        ("nodes", []), ("nodes", "a"), ("order", ["a"]), ("order", ["a", "z"]), ("order", "ab"),
        ("nodes", [{"workUnitId": "a", "dependencies": [], "x": 1}]),
        ("nodes", [{"workUnitId": "a"}]),
        ("nodes", [{"workUnitId": "a", "dependencies": [7]}, {"workUnitId": "b", "dependencies": []}]),
        ("nodes", [{"workUnitId": "a", "dependencies": []}, {"workUnitId": "a", "dependencies": []}]))]
    t.vacio("GE-E60 un inicio.json con una clave de mas, de menos o de un tipo malo no se crea",
            [nombre for nombre, doc in rotos
             if _levanta(lambda: registro.crear_grafo(str(vacio), doc)) != "RegistroInvalido"])
    t.igual("GE-E60 y no dejo ni la carpeta de la tarea", {}, M72._arbol(vacio))

    despachos_antes = registro.despachos(str(proy), CLAVE, gid)
    t.vacio("GE-E60 una marca de despacho con workUnitId o executionId malos no se escribe",
            [repr(c) for c in ((7, registro.nuevo_id()), ("", registro.nuevo_id()),
                               ("a", "exe_corto"), ("a", None), ("a", "grf_" + "a" * 32),
                               ("a", registro.nuevo_id() + "\n"))
             if _levanta(lambda: registro.registrar_despacho(str(proy), CLAVE, gid, *c))
             != "RegistroInvalido"])
    t.igual("GE-E60 y no escribio ninguna", despachos_antes, registro.despachos(str(proy), CLAVE, gid))

    otro = _inicio()
    registro.crear_grafo(str(proy), otro)
    t.vacio("GE-E60 un cancelacion.json sin un pedidoPor de texto no se escribe",
            [repr(p) for p in ("", "   ", None, 7, ["ana"])
             if _levanta(lambda: registro.marcar_cancelacion(
                 str(proy), CLAVE, otro["graphRunId"], p)) != "RegistroInvalido"])
    t.igual("GE-E60 y no escribio la marca", False, registro.cancelada(str(proy), CLAVE,
                                                                    otro["graphRunId"]))
    g = otro["graphRunId"]
    t.vacio("GE-E60 un terminal con otro status, de otro GraphRun, de otra tarea o que no es un objeto "
            "no se escribe",
            [repr(d) for d in (_terminal(g, "BLOCKED"), _terminal(g, "ACTIVE"), _terminal(g, None),
                               _terminal(registro.nuevo_id_de_grafo()), _terminal(g, taskKey="GCBA-1"),
                               {"graphRunId": g, "taskKey": CLAVE}, [], "SUCCEEDED", None)
             if _levanta(lambda: registro.escribir_terminal(str(proy), CLAVE, g, d))
             != "RegistroInvalido"])
    t.verdadero("GE-E60 y el GraphRun sigue ACTIVE, sin result.json",
                registro.leer_grafo(str(proy), CLAVE, g)["estado"] == registro.ACTIVE)

    inexistente = registro.nuevo_id_de_grafo()
    t.igual("GE-E60 un despacho, una cancelacion o un terminal de un GraphRun que no existe: "
            "RegistroInvalido, y no se crea su carpeta",
            (["RegistroInvalido"] * 3, False),
            ([_levanta(lambda: registro.registrar_despacho(str(proy), CLAVE, inexistente, "a",
                                                           registro.nuevo_id())),
              _levanta(lambda: registro.marcar_cancelacion(str(proy), CLAVE, inexistente, "ana")),
              _levanta(lambda: registro.escribir_terminal(str(proy), CLAVE, inexistente,
                                                          _terminal(inexistente)))],
             Path(registro.carpeta_de_grafo(str(proy), CLAVE, inexistente)).exists()))


def test_ge_e60_las_marcas_de_despacho_son_consecutivas_desde_001(t):
    """GE-E60 (registro) — Las marcas de despacho son consecutivas desde `001`, una por despacho, con
    tres cifras. Sin un contador ni un puntero: el numero es el siguiente al ultimo archivo."""
    proy = _vacio()
    inicio = _inicio(nodos=(("a", ()), ("b", ()), ("c", ())))
    gid = inicio["graphRunId"]
    registro.crear_grafo(str(proy), inicio)
    carpeta = Path(registro.carpeta_de_grafo(str(proy), CLAVE, gid)) / registro.DESPACHOS
    t.igual("GE-E60 sin despachos, no hay marcas", [], registro.despachos(str(proy), CLAVE, gid))

    marcas = [registro.registrar_despacho(str(proy), CLAVE, gid, w, registro.nuevo_id())
              for w in ("a", "b", "c")]
    t.igual("GE-E60 los numeros son 1, 2 y 3", [1, 2, 3], [m["numero"] for m in marcas])
    t.igual("GE-E60 y los archivos, 001, 002 y 003", ["001.json", "002.json", "003.json"],
            sorted(os.listdir(str(carpeta))))
    t.igual("GE-E60 se leen en orden, con la unidad de cada una", [(1, "a"), (2, "b"), (3, "c")],
            [(n, m["workUnitId"]) for n, m, _ in registro.despachos(str(proy), CLAVE, gid)])
    t.igual("GE-E60 y el executionId que nombra cada una es el que se paso",
            [m["executionId"] for m in marcas],
            [m["executionId"] for _, m, _ in registro.despachos(str(proy), CLAVE, gid)])

    for malo in (0, 1000, -1, True, "1", 1.0, None):
        t.igual("GE-E60 un numero de despacho %r no se vuelve ruta" % (malo,), "RegistroInvalido",
                _levanta(lambda: registro.ruta_del_despacho(str(proy), CLAVE, gid, malo)))
    ultima = registro.ruta_del_despacho(str(proy), CLAVE, gid, 999)
    registro.escribir_json(ultima, dict(marcas[0], numero=999))
    t.igual("GE-E60 pasada la 999 no se escribe otra: el nombre tiene tres cifras", "RegistroInvalido",
            _levanta(lambda: registro.registrar_despacho(str(proy), CLAVE, gid, "a",
                                                         registro.nuevo_id())))
    t.igual("GE-E60 y no dejo nada", ["001.json", "002.json", "003.json", "999.json"],
            sorted(os.listdir(str(carpeta))))


def test_ge_i15_el_candado_de_la_tarea_es_un_archivo_estable(t):
    """GE-I15 y GD-20 (primitiva; GE-E28, GE-E29 y GE-E43 son del conductor) — El candado de la
    tarea, `grafos/vivo.lock`, se toma, no se puede tomar dos veces, y el archivo sigue existiendo al
    soltarlo: se abre con O_CREAT y sin O_EXCL, y no se borra. Que exista no dice nada: solo cuenta si
    esta tomado, y no lleva pid ni fecha."""
    proy = _vacio()
    ruta = Path(registro.carpeta_de_grafos(str(proy), CLAVE)) / registro.VIVO
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 se toma", bool(candado))
    t.igual("GE-I15 es grafos/vivo.lock de la tarea", str(ruta), candado.ruta)
    t.verdadero("GE-I15 el archivo existe y esta vacio: sin pid ni fecha",
                ruta.is_file() and ruta.stat().st_size == 0)
    segundo = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 no se puede tomar dos veces", not segundo)
    t.verdadero("GE-I15 y el segundo intento no le saco el candado al primero", bool(candado))
    t.vacio("GE-I15 el candado y su archivo no hacen existir un GraphRun",
            registro.grafos_de(str(proy), CLAVE) + registro.activos(str(proy), CLAVE)
            + registro.residuos_de_grafos(str(proy), CLAVE))

    candado.soltar()
    t.verdadero("GE-I15 al soltarlo el archivo sigue existiendo", ruta.is_file())
    t.verdadero("GE-I15 y el objeto ya no dice tomado", not candado)
    candado.soltar()
    t.verdadero("GE-I15 soltar dos veces no levanta nada", not candado)
    de_nuevo = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 soltado, se puede volver a tomar: no hay un O_EXCL que lo impida",
                bool(de_nuevo))
    de_nuevo.soltar()

    otro = _vacio()
    carpeta = Path(registro.carpeta_de_grafos(str(otro), CLAVE))
    carpeta.mkdir(parents=True)
    (carpeta / registro.VIVO).write_bytes(b"pid 4242 desde 2020-01-01")
    tomado = registro.CandadoDeTarea(str(otro), CLAVE)
    t.verdadero("GE-I15 que el archivo exista, sin estar tomado y con lo que sea adentro, no significa "
                "nada: se toma", bool(tomado))
    tomado.soltar()
    t.igual("GE-I15 y lo que tenia adentro no se toca", b"pid 4242 desde 2020-01-01",
            (carpeta / registro.VIVO).read_bytes())

    clase = _definicion("CandadoDeTarea")
    aperturas = [c for c in ast.walk(clase) if isinstance(c, ast.Call)
                 and M72._nombre(c.func) == "os.open"]
    t.igual("GE-I15 el candado de la tarea abre su archivo en un solo lugar", 1, len(aperturas))
    banderas = _nombres(aperturas[0].args[1]) if aperturas else set()
    t.verdadero("GE-I15 con O_CREAT y sin O_EXCL (GM-12)",
                "O_CREAT" in banderas and "O_EXCL" not in banderas)
    t.vacio("GE-I15 y la clase no borra ni renombra nada: el archivo no se borra al soltar (GM-12)",
            sorted(_nombres(clase) & {"unlink", "remove", "rmtree", "rename", "replace", "rmdir"}))
    t.verdadero("GE-I15 Vida, el candado de una Execution, sigue con O_EXCL: no cambia (GD-20)",
                "O_EXCL" in _nombres(_definicion("Vida")))


def test_ge_i15_el_candado_de_la_tarea_entre_procesos(t):
    """GE-I15 (primitiva) — Con el candado tomado por este proceso, otro del sistema operativo no lo
    toma; con el tomado por otro, este no; y el de un proceso que muere sin soltarlo lo suelta el
    sistema, sin fechas ni pids. El archivo sigue existiendo siempre."""
    proy = _vacio()
    ruta = Path(registro.carpeta_de_grafos(str(proy), CLAVE)) / registro.VIVO

    mio = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 este proceso lo toma", bool(mio))
    marcas = M64._tmp("ge73-marcas-")
    t.igual("GE-I15 con el candado tomado, otro proceso no lo toma", {"tomado": False},
            _salida(_lanzar("candado", proy, marcas, "esperar")))
    t.igual("GE-I15 y lo dijo: no lo tomo", ["l.no_tomado"], _marcas(marcas))
    mio.soltar()

    marcas = M64._tmp("ge73-marcas-")
    hijo = _lanzar("candado", proy, marcas, "esperar")
    t.verdadero("GE-I15 el otro proceso lo tomo", M72._esperar(
        lambda: (Path(marcas) / "l.tomado").exists()))
    intento = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 con el candado en otro proceso, este no lo toma", not intento)
    (Path(marcas) / "l.soltar").write_text("", encoding="utf-8")
    t.igual("GE-I15 el otro lo solto al terminar", {"tomado": True}, _salida(hijo))
    despues = registro.CandadoDeTarea(str(proy), CLAVE)
    t.verdadero("GE-I15 soltado por el otro, este lo toma", bool(despues))
    despues.soltar()
    t.verdadero("GE-I15 y el archivo sigue existiendo", ruta.is_file())

    marcas = M64._tmp("ge73-marcas-")
    muerto = _lanzar("candado", proy, marcas, "morir")
    _salida(muerto)
    t.verdadero("GE-I15 un proceso tomo el candado y murio sin soltarlo (os._exit)",
                "l.tomado" in _marcas(marcas) and muerto.returncode == 0)
    tras = _tomar_pronto(proy)
    t.verdadero("GE-I15 al morir el proceso lo suelta el sistema operativo: sin fechas ni pids, "
                "este lo toma", bool(tras))
    tras.soltar()
    t.verdadero("GE-I15 y vivo.lock sigue existiendo", ruta.is_file())


def test_gd04_barrer_grafos_cierra_lo_que_el_conductor_no_alcanzo_a_publicar(t):
    """GD-04, §14.1 y §16.2 (G1; primitiva de GE-E36) — Una carpeta `grf_...` sin `inicio.json` no es
    un GraphRun: es un residuo de la creacion, y la barre quien tiene el candado de la tarea, sin mirar
    la edad: con el candado tomado no hay otro conductor creando. Sin el candado, nadie borra nada: una
    carpeta sin `inicio.json` puede ser la de un conductor vivo. `vivo.lock` y los GraphRuns quedan."""
    proy = _vacio()
    gid, _ = _grafo_completo(proy)
    nuevo, viejo = registro.nuevo_id_de_grafo(), registro.nuevo_id_de_grafo()
    for residuo in (nuevo, viejo):
        carpeta = Path(registro.carpeta_de_grafo(str(proy), CLAVE, residuo))
        (carpeta / registro.DESPACHOS).mkdir(parents=True)
        (carpeta / ".inicio.json.r3s1d0.tmp").write_text("{a medias", encoding="utf-8")
    _envejecer(Path(registro.carpeta_de_grafo(str(proy), CLAVE, viejo)), 1200)
    antes = _grafos_de(proy)

    t.igual("GD-04 los residuos no son GraphRuns: grafos_de no los ve y residuos_de_grafos si",
            ([gid], sorted([nuevo, viejo])),
            (registro.grafos_de(str(proy), CLAVE), registro.residuos_de_grafos(str(proy), CLAVE)))
    t.igual("GD-04 leer_grafo de un residuo: no existe", [None, None],
            [registro.leer_grafo(str(proy), CLAVE, r) for r in (nuevo, viejo)])
    soltado = registro.CandadoDeTarea(str(proy), CLAVE)
    soltado.soltar()
    de_otra = registro.CandadoDeTarea(str(proy), "GCBA-99")
    for que, candado in (("sin candado", None), ("con uno ya soltado", soltado),
                         ("con el de otra tarea", de_otra), ("con algo que no es un candado", True)):
        t.igual("GD-04 %s levanta RegistroInvalido" % que, "RegistroInvalido",
                _levanta(lambda: registro.barrer_grafos(str(proy), CLAVE, candado)))
    de_otra.soltar()
    t.igual("GD-04 y no borro nada", antes, _grafos_de(proy))

    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    barridos = registro.barrer_grafos(str(proy), CLAVE, candado)
    t.igual("GD-04 con el candado de la tarea se barren los dos, el nuevo y el viejo",
            sorted([nuevo, viejo]), sorted(barridos))
    t.igual("GD-04 el GraphRun con inicio.json sigue, con todas sus marcas", [gid],
            registro.grafos_de(str(proy), CLAVE))
    t.igual("GD-04 y no queda ningun residuo", [], registro.residuos_de_grafos(str(proy), CLAVE))
    t.igual("GD-04 lo que quedo bajo grafos/ es lo de antes menos los dos residuos",
            {k: v for k, v in antes.items() if nuevo not in k and viejo not in k}, _grafos_de(proy))
    t.verdadero("GD-04 vivo.lock sigue existiendo", (Path(candado.ruta)).is_file())
    t.igual("GD-04 barrer otra vez no encuentra nada", [], registro.barrer_grafos(str(proy), CLAVE,
                                                                                candado))
    candado.soltar()


def test_gd20_limpiar_temporales_de_grafos_respeta_la_edad_y_pide_el_candado(t):
    """GD-20 (F2' para las carpetas `grf_...`, §15.3) — Los temporales de escritura de un GraphRun los
    limpia solo quien tiene el candado de la tarea, y solo los de mas de diez minutos, por su propia
    fecha: un `--cancelar` escribe `cancelacion.json` sin el candado, y su temporal nuevo no se toca."""
    proy = _vacio()
    gid, _ = _grafo_completo(proy)
    carpeta = Path(registro.carpeta_de_grafo(str(proy), CLAVE, gid))
    nuevos = [carpeta / ".cancelacion.json.n3w000.tmp", carpeta / registro.DESPACHOS / ".003.json.n3w000.tmp"]
    viejos = [carpeta / ".result.json.0ld000.tmp", carpeta / registro.DESPACHOS / ".003.json.0ld000.tmp"]
    for ruta in nuevos + viejos:
        ruta.write_text("{a medias", encoding="utf-8")
    for ruta in nuevos:
        _envejecer(ruta, 590)
    for ruta in viejos:
        _envejecer(ruta, 660)
    marcas_antes = {k: v for k, v in _grafos_de(proy).items() if not k.rsplit("/", 1)[-1].startswith(".")}

    t.igual("GD-20 sin el candado de la tarea levanta RegistroInvalido y no borra nada",
            ("RegistroInvalido", True),
            (_levanta(lambda: registro.limpiar_temporales_de_grafos(str(proy), CLAVE, None)),
             all(r.is_file() for r in nuevos + viejos)))
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    t.igual("GD-20 con el candado borra solo los dos de mas de diez minutos", 2,
            registro.limpiar_temporales_de_grafos(str(proy), CLAVE, candado))
    t.verdadero("GD-20 los viejos ya no estan", not any(r.exists() for r in viejos))
    t.verdadero("GD-20 los de menos de diez minutos siguen", all(r.is_file() for r in nuevos))
    t.igual("GD-20 las marcas y el candado, intactos", marcas_antes,
            {k: v for k, v in _grafos_de(proy).items() if not k.rsplit("/", 1)[-1].startswith(".")})
    t.igual("GD-20 limpiar otra vez no borra nada", 0,
            registro.limpiar_temporales_de_grafos(str(proy), CLAVE, candado))
    candado.soltar()


def test_gd10_la_lectura_del_graphrun_que_cierra_huerfanos(t):
    """GD-04, GD-10 y §16.1 — Lo que el registro ofrece para cerrar un huerfano: si el GraphRun existe,
    su estado derivado (ACTIVE, un terminal, o ILEGIBLE si una marca no valida: no se cierra), sus
    marcas leidas, `cancelada` y la lista de los ACTIVE. Un residuo sin `inicio.json` no existe."""
    proy = _vacio()
    inicio = _inicio()
    gid = inicio["graphRunId"]
    t.igual("GD-04 un GraphRun que no existe: None", None, registro.leer_grafo(str(proy), CLAVE, gid))
    registro.crear_grafo(str(proy), inicio)
    g = registro.leer_grafo(str(proy), CLAVE, gid)
    t.igual("GD-04 leer_grafo da esas claves, y ninguna mas",
            sorted(("graphRunId", "estado", "motivo", "inicio", "cancelada", "cancelacion", "resultado",
                    "despachos")), sorted(g))
    t.igual("GD-04 con inicio.json y sin result.json es ACTIVE: existe desde su inicio.json",
            ("ACTIVE", None, inicio), (g["estado"], g["motivo"], g["inicio"]))
    t.igual("GD-04 sin cancelacion, sin resultado y sin despachos", (False, None, None, []),
            (g["cancelada"], g["cancelacion"], g["resultado"], g["despachos"]))
    t.igual("GD-10 activos lo lista: es lo que cierra quien toma el candado", [gid],
            registro.activos(str(proy), CLAVE))

    exe = registro.nuevo_id()
    registro.registrar_despacho(str(proy), CLAVE, gid, "a", exe)
    registro.marcar_cancelacion(str(proy), CLAVE, gid, "ana")
    g = registro.leer_grafo(str(proy), CLAVE, gid)
    t.igual("GD-11 la marca de cancelacion se lee, y cancelada la ve", (True, "ana"),
            (g["cancelada"], (g["cancelacion"] or {}).get("pedidoPor")))
    t.igual("GD-11 y cancelada sin leer el contenido", True, registro.cancelada(str(proy), CLAVE, gid))
    t.igual("GD-11 la cancelacion no es un terminal: sigue ACTIVE", "ACTIVE", g["estado"])
    t.igual("GD-12 el despacho se lee con su numero, su unidad y su executionId",
            [(1, "a", exe)],
            [(n, m["workUnitId"], m["executionId"]) for n, m, _ in g["despachos"]])

    terminales = {}
    for estado in ("SUCCEEDED", "FAILED", "CANCELLED"):
        otro = _inicio()
        registro.crear_grafo(str(proy), otro)
        registro.escribir_terminal(str(proy), CLAVE, otro["graphRunId"],
                                   _terminal(otro["graphRunId"], estado))
        terminales[estado] = otro["graphRunId"]
        leido = registro.leer_grafo(str(proy), CLAVE, otro["graphRunId"])
        t.igual("GD-04 %s: el estado es el del result.json" % estado, estado, leido["estado"])
        t.igual("GD-04 %s: y el resultado se lee" % estado, estado, (leido["resultado"] or {}).get("status"))
    t.igual("GD-10 un terminal no es un huerfano: activos solo trae el que no cerro", [gid],
            registro.activos(str(proy), CLAVE))
    t.igual("GD-04 grafos_de lista los cuatro, por id", sorted([gid] + list(terminales.values())),
            registro.grafos_de(str(proy), CLAVE))

    def roto(que, escribir):
        """Un GraphRun con una marca que no valida: lo que deja una mano o un disco, no el registro."""
        doc = _inicio()
        registro.crear_grafo(str(proy), doc)
        carpeta = Path(registro.carpeta_de_grafo(str(proy), CLAVE, doc["graphRunId"]))
        escribir(carpeta, doc["graphRunId"])
        return doc["graphRunId"], registro.leer_grafo(str(proy), CLAVE, doc["graphRunId"])

    def pisar(nombre, contenido):
        def escribir(carpeta, graph_run_id):
            ruta = carpeta / nombre
            if ruta.exists():
                ruta.unlink()
            ruta.write_bytes(contenido(graph_run_id) if callable(contenido) else contenido)
        return escribir

    casos = (
        ("inicio.json con una clave de mas", pisar("inicio.json", lambda g: registro.bytes_de(
            dict(_inicio(), graphRunId=g, extra=1)))),
        ("inicio.json que no es JSON", pisar("inicio.json", b"{a medias")),
        ("inicio.json de otro GraphRun", pisar("inicio.json", registro.bytes_de(_inicio()))),
        ("result.json con un status que no es de GraphRun", pisar("result.json", lambda g: registro.bytes_de(
            _terminal(g, "BLOCKED")))),
        ("result.json de otro GraphRun", pisar("result.json", registro.bytes_de(
            _terminal(registro.nuevo_id_de_grafo())))),
        ("result.json que no es JSON", pisar("result.json", b"[")),
    )
    for nombre, escribir in casos:
        graph_run_id, leido = roto(nombre, escribir)
        t.igual("GD-04 %s: ILEGIBLE, con su motivo, y no se cierra" % nombre,
                (registro.ILEGIBLE, True), (leido["estado"], bool(leido["motivo"])))
        t.verdadero("GD-04 %s: existe (tiene inicio.json) pero no es ACTIVE: activos no lo trae" % nombre,
                    graph_run_id in registro.grafos_de(str(proy), CLAVE)
                    and graph_run_id not in registro.activos(str(proy), CLAVE))

    graph_run_id, leido = roto("cancelacion", pisar("cancelacion.json", b"{a medias"))
    t.igual("GD-11 una cancelacion.json ilegible cuenta como pedida, como la de una Execution: existe",
            (True, None, "ACTIVE"), (leido["cancelada"], leido["cancelacion"], leido["estado"]))
    graph_run_id, leido = roto("despacho", pisar("despachos/001.json", registro.bytes_de(
        {"numero": 2, "workUnitId": "a", "executionId": registro.nuevo_id(),
         "dispatchedAt": registro.ahora()})))
    t.igual("GD-12 una marca de despacho que no es la de su archivo se lee sin marca y con motivo",
            (1, None, True), (leido["despachos"][0][0], leido["despachos"][0][1],
                              bool(leido["despachos"][0][2])))


def test_gd03_las_propias_son_las_que_una_marca_y_un_turno_nombran(t):
    """GD-03, ME-I21 y §16.1 (paso 2) — Una Execution es del GraphRun si y solo si una marca de
    despacho suya la nombra y un turno la nombra. La marca que ningun turno nombra (G2) no es una
    Execution, y una Execution de la tarea que ninguna marca nombra (una manual) no es del GraphRun:
    el cierre de un huerfano solo cancela lo propio (GE-E52)."""
    proy = M72._proyecto(M72._unidades("uno", "dos", "tres", "cuatro"))
    M72._guion(proy)
    exe_uno = registro.nuevo_id()
    corrida = M72._corrida(proy, "uno", execution_id=exe_uno)
    pedida = _requested_sin_motor(proy, "dos")["executionId"]
    sin_turno = registro.nuevo_id()
    manual = _eid(M72._corrida(proy, "cuatro"))
    t.igual("GD-03 la Execution preasignada del GraphRun termina SUCCEEDED", ("SUCCEEDED", exe_uno),
            (M72._de(corrida, "status"), M72._de(corrida, "executionId")))

    inicio = _inicio(nodos=(("uno", ()), ("dos", ()), ("tres", ()), ("cuatro", ())))
    gid = inicio["graphRunId"]
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    registro.crear_grafo(str(proy), inicio)
    registro.registrar_despacho(str(proy), CLAVE, gid, "uno", exe_uno)
    registro.registrar_despacho(str(proy), CLAVE, gid, "dos", pedida)
    registro.registrar_despacho(str(proy), CLAVE, gid, "tres", sin_turno)
    candado.soltar()

    propias = registro.propias(str(proy), CLAVE, gid)
    t.igual("GD-03 son las dos que una marca y un turno nombran, con su estado derivado",
            [(1, "uno", exe_uno, "SUCCEEDED"), (2, "dos", pedida, "REQUESTED")],
            [(p["numero"], p["workUnitId"], p["executionId"], p["estado"]) for p in propias])
    t.verdadero("GD-03 la marca 003 nombra un executionId que ningun turno nombra: el corte G2",
                sin_turno not in set(e for _, _, e, _ in registro.nombradas(str(proy), CLAVE) if e))
    t.verdadero("GD-03 y no es propia", sin_turno not in [p["executionId"] for p in propias])
    t.verdadero("GE-I19 la manual de la tarea, que ninguna marca nombra, no es propia",
                manual not in [p["executionId"] for p in propias]
                and manual in set(e for _, _, e, _ in registro.nombradas(str(proy), CLAVE) if e))
    t.igual("GD-03 un GraphRun distinto, sin marcas, no tiene Executions propias", [],
            registro.propias(str(proy), CLAVE, registro.nuevo_id_de_grafo()))

    motor.cancelar(str(proy), CLAVE, pedida, PIDE)
    t.igual("GD-03 el estado de una propia es el derivado de ahora: la REQUESTED cancelada",
            ["SUCCEEDED", "CANCELLED"],
            [p["estado"] for p in registro.propias(str(proy), CLAVE, gid)])


def test_ge_e62_con_grafos_lleno_las_funciones_de_execution_no_lo_ven(t):
    """GE-E62 — Con `grafos/` lleno, `registro.carpetas`, `residuos`, `barrer`, `limpiar_temporales` y
    `otras_entregadas` no lo nombran ni lo tocan, ni tampoco la recuperacion del motor, aunque el
    candado de la tarea este tomado; y ninguna funcion de Task 4 nombra `grafos/` (GE-I29). Los
    temporales y las carpetas viejas de `grafos/` quedan donde estaban."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    M72._guion(proy)
    exe_uno = _eid(M72._corrida(proy, "uno"))
    exe_dos = _requested_sin_motor(proy, "dos")["executionId"]
    gid, _ = _grafo_completo(proy)

    sucio = registro.nuevo_id_de_grafo()
    carpeta_sucia = Path(registro.carpeta_de_grafo(str(proy), CLAVE, sucio))
    (carpeta_sucia / registro.DESPACHOS).mkdir(parents=True)
    carpeta_de_gid = Path(registro.carpeta_de_grafo(str(proy), CLAVE, gid))
    temporales = [carpeta_sucia / ".inicio.json.v13j0.tmp",
                  carpeta_de_gid / registro.DESPACHOS / ".003.json.v13j0.tmp",
                  Path(registro.carpeta_de_grafos(str(proy), CLAVE)) / ".algo.v13j0.tmp"]
    for ruta in temporales:
        ruta.write_text("{a medias", encoding="utf-8")
    grafos = Path(registro.carpeta_de_grafos(str(proy), CLAVE))
    for ruta in temporales + [carpeta_sucia, grafos / registro.VIVO, grafos]:
        _envejecer(ruta, 1200)
    antes = _grafos_de(proy)
    t.verdadero("GE-E62 grafos/ esta lleno: el GraphRun, un residuo, tres temporales viejos y vivo.lock",
                len(antes) >= 9 and all(r.is_file() for r in temporales))

    t.igual("GE-E62 carpetas ve las dos Executions y nada de grafos/", sorted([exe_uno, exe_dos]),
            registro.carpetas(str(proy), CLAVE))
    t.vacio("GE-E62 residuos no ve nada: grafos/ no es una carpeta sin turno",
            registro.residuos(str(proy), CLAVE))
    with _Sondas() as sondas:
        barridos = registro.barrer(str(proy), CLAVE)
        limpiados = registro.limpiar_temporales(str(proy), CLAVE)
        recuperadas = motor.recuperar(str(proy), CLAVE)
    t.vacio("GE-E62 barrer no borra nada, ni grafos/ ni una carpeta grf_ vieja", barridos)
    t.igual("GE-E62 limpiar_temporales no borra ni un temporal viejo de grafos/", 0, limpiados)
    t.vacio("GE-E62 la recuperacion del motor no cierra ni toca nada", recuperadas)
    t.vacio("GE-E62 y ninguna sonda de candado miro grafos/ ni una carpeta grf_",
            [c for c in sondas.carpetas if c == GRAFOS or c.startswith("grf_")])
    t.verdadero("GE-E62 otras_entregadas no cuenta nada de grafos/ como una entrega",
                registro.otras_entregadas(str(proy), exe_dos, time.time() + 3600) is False)
    t.igual("GE-E62 grafos/ queda como estaba, byte a byte", antes, _grafos_de(proy))
    t.verdadero("GE-E62 los temporales viejos y la carpeta sin inicio.json siguen donde estaban",
                all(r.is_file() for r in temporales) and (carpeta_sucia / registro.DESPACHOS).is_dir())

    vivo = registro.CandadoDeTarea(str(proy), CLAVE)
    registro.barrer(str(proy), CLAVE)
    motor.recuperar(str(proy), CLAVE)
    t.verdadero("GE-E62 con el candado de la tarea tomado, ni barrer ni la recuperacion se lo sacan",
                bool(vivo) and not registro.CandadoDeTarea(str(proy), CLAVE))
    vivo.soltar()
    t.igual("GE-E62 y grafos/ sigue igual", antes, _grafos_de(proy))

    solo = _vacio()
    _grafo_completo(solo)
    t.igual("GE-E62 una tarea con solo grafos/ aparece en tareas, sin Executions ni residuos",
            ([CLAVE], [], [], [], [], 0, [], False),
            (registro.tareas(str(solo)), registro.carpetas(str(solo), CLAVE),
             registro.claves_de(str(solo), CLAVE), registro.nombradas(str(solo), CLAVE),
             registro.barrer(str(solo), CLAVE), registro.limpiar_temporales(str(solo), CLAVE),
             motor.recuperar(str(solo), CLAVE),
             registro.otras_entregadas(str(solo), "exe_" + "0" * 32, 0)))

    sin_grafos = ("carpeta_de_tarea", "carpeta_de", "carpeta_de_clave", "ruta_del_turno", "turnos",
                  "ultimo_turno", "reservar", "nombrada", "crear", "estado", "claves_de", "nombradas",
                  "carpetas", "tareas", "entregada_en", "otras_entregadas", "_edad", "residuos",
                  "barrer", "_temporales", "_vencido", "limpiar_temporales", "candado_libre",
                  "Vida", "Tomado")
    del_grafo = {"GRAFOS", "DESPACHOS", "INICIO", "ID_DE_GRAFO", "DESPACHO", "carpeta_de_grafos",
                 "carpeta_de_grafo", "ruta_del_despacho", "grafos_de", "residuos_de_grafos",
                 "leer_grafo", "despachos", "activos", "propias", "cancelada", "CandadoDeTarea"}
    t.vacio("GE-I29 ninguna funcion de Task 4 de registro.py nombra nada del GraphRun (GM-36)",
            ["%s: %s" % (nombre, sorted(_nombres(_definicion(nombre)) & del_grafo))
             for nombre in sin_grafos if _nombres(_definicion(nombre)) & del_grafo])


def test_ge_e62_la_evidencia_de_una_execution_no_lista_nada_de_grafos(t):
    """GE-E62 — La evidencia de una Execution que corrio durante un GraphRun no lista nada de
    `grafos/`. Con `.claude/` sin ignorar por git, lo unico que lo esconde es la exclusion de
    `.claude/ejecuciones/`: el Host falso escribe adentro de `grafos/` mientras la Execution corre, y
    la evidencia lista su cambio real y un archivo de control de otro lugar de `.claude/`."""
    proy = M72._proyecto(M72._unidades("uno"))
    M64._escribir(proy / ".gitignore", "prop-*.json\n")
    gid, _ = _grafo_completo(proy, "SUCCEEDED")
    de_grafos = ".claude/ejecuciones/%s/grafos/%s/despachos/003.json" % (CLAVE, gid)
    control = ".claude/otra-carpeta/control.json"
    M72._guion(proy, cambios=[{"ruta": "src/app.py", "contenido": "VALOR = 2\n"},
                              {"ruta": de_grafos, "contenido": "{}\n"},
                              {"ruta": control, "contenido": "{}\n"}])

    foto = M72.evidencia.instantanea(str(proy))
    t.vacio("GE-E62 la foto de antes no nombra nada de .claude/ejecuciones/ aunque git lo ve",
            [r for r in foto["sucios"] if r.startswith(".claude/ejecuciones")])
    t.verdadero("GE-E62 pero si ve el resto de .claude/: el control es real",
                ".claude/harness.config.json" in foto["sucios"])
    corrida = M72._corrida(proy, "uno")
    t.igual("GE-E62 la Execution termina SUCCEEDED", ("SUCCEEDED", None),
            (M72._de(corrida, "status"), corrida["exc"]))
    cambios = corrida["res"]["evidence"]["changes"]
    t.igual("GE-E62 la evidencia se resuelve", "RESOLVED", cambios["state"])
    t.igual("GE-E62 lista el cambio real y el de control, y nada de grafos/",
            sorted(["src/app.py", control]), sorted(f["path"] for f in cambios["files"]))
    t.verdadero("GE-E62 lo que el Host escribio en grafos/ esta en disco: no se lo lleva nadie",
                (Path(proy) / Path(*de_grafos.split("/"))).is_file())


# =============================================================================================
# HOST: el Host falso con `por_unidad` y una bitacora (GD-27 paso 6)
# =============================================================================================
#
# La infraestructura con que GE-E02 (intervalos sin solape), GE-E40 y GE-E44 (cuantas invocaciones),
# GE-E71 (intervalos que se solapan) y las cuentas de «el Host recibe n invocaciones» de la spec miden.
# No es un escenario. Con las claves viejas el Host falso hace lo de siempre: la suite 72 es el control.

def _prompt_de(proy, unidad):
    """El prompt que `host_claude_code` le arma al Host para esa unidad, el de verdad."""
    request, error, _, _ = admision.al_pedir(str(proy), CLAVE, unidad, PIDE, limpieza.cargar_catalogo())
    if error is not None:
        raise AssertionError("la admision del prompt de prueba fallo: %s" % (error,))
    return _adaptador(sys.platform).prompt(request)


def _invocar_host(proy, prompt):
    """Una invocacion directa del Host falso, con `prompt` por stdin y el guion de HOST_FALSO_GUION:
    (codigo de salida, stdout)."""
    hecho = subprocess.run([sys.executable, str(M72.HOST), "-p"], input=prompt.encode("utf-8"),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(proy),
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return hecho.returncode, hecho.stdout.decode("utf-8")


def _ruta_de_bitacora(nombre="bitacora"):
    """Una bitacora nueva, en una carpeta temporal que se borra al terminar la suite: fuera del
    proyecto, para que la evidencia de una Execution no la vea."""
    return M64._tmp("ge73-bitacora-") / (nombre + ".jsonl")


def _invocaciones(ruta):
    """Las invocaciones de la bitacora del Host falso, en el orden en que empezaron:
    [{id, workUnitId, pid, inicio, fin}]. Cada invocacion escribe una linea al empezar, con `fin: null`,
    y la misma con el `fin` al terminar: la ultima de cada `id` manda."""
    if not Path(ruta).is_file():
        return []
    por_id = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if linea.strip():
            doc = json.loads(linea)
            por_id[doc["id"]] = doc
    return list(por_id.values())


def _solapadas(a, b):
    """Si los intervalos de dos invocaciones que terminaron se solapan: las dos estuvieron a la vez."""
    return a["inicio"] < b["fin"] and b["inicio"] < a["fin"]


def test_gd27_el_host_falso_elige_el_guion_por_workunitid(t):
    """GD-27 paso 6 (infraestructura de GE-E71 y de los escenarios que fallan una sola unidad) —
    `por_unidad` da un guion distinto por `workUnitId`, que el Host lee del prompt: las claves de la
    unidad pisan las de arriba, y la que no figura, o un prompt sin WorkUnit legible, usa el de arriba."""
    proy = M72._proyecto(M72._unidades("uno", "dos", "tres"))
    eco_base, eco_dos = M72._eco(proy, "eco-base"), M72._eco(proy, "eco-dos")
    M72._guion(proy, eco=str(eco_base), resultado=M72._informe("COMPLETE", "# base\n"),
               por_unidad={"dos": {"eco": str(eco_dos),
                                   "resultado": M72._informe("PARTIAL", "# dos\n")},
                           "tres": {"sin_json": "no es JSON", "salida": 3}})

    def declarado(salida):
        informe = json.loads(salida)["structured_output"]
        return informe["declaredStatus"], informe["artifact"]

    codigo, salida = _invocar_host(proy, _prompt_de(proy, "uno"))
    t.igual("GD-27 uno no figura en por_unidad: el guion de arriba", (0, ("COMPLETE", "# base\n")),
            (codigo, declarado(salida)))
    t.contiene("GD-27 y dejo el eco de arriba, con su WorkUnit en el prompt", '"id": "uno"',
               (M72._leer_eco(eco_base) or {}).get("stdin"))
    codigo, salida = _invocar_host(proy, _prompt_de(proy, "dos"))
    t.igual("GD-27 dos tiene su propio guion", (0, ("PARTIAL", "# dos\n")), (codigo, declarado(salida)))
    t.contiene("GD-27 y su eco propio lleva la WorkUnit dos", '"id": "dos"',
               (M72._leer_eco(eco_dos) or {}).get("stdin"))
    t.contiene("GD-27 el eco de arriba no lo pisa la unidad dos", '"id": "uno"',
               (M72._leer_eco(eco_base) or {}).get("stdin"))
    t.igual("GD-27 tres tiene el suyo: sin JSON y con otro codigo de salida", (3, "no es JSON"),
            _invocar_host(proy, _prompt_de(proy, "tres")))
    t.igual("GD-27 un prompt sin una WorkUnit legible usa el guion de arriba",
            (0, ("COMPLETE", "# base\n")), (lambda c, s: (c, declarado(s)))(
                *_invocar_host(proy, "Seguimos con GCBA-72.\n```json\n{a medias\n```\n")))

    corridas = {u: M72._corrida(proy, u) for u in ("uno", "dos", "tres")}
    t.igual("GD-27 con el motor y su prompt real: uno, SUCCEEDED", ("SUCCEEDED", None),
            (M72._de(corridas["uno"], "status"), M72._codigo(corridas["uno"])))
    t.igual("GD-27 con el motor: dos, FAILED porque el agente declara PARTIAL",
            ("FAILED", "AGENT_DECLARED_NOT_COMPLETE"),
            (M72._de(corridas["dos"], "status"), M72._codigo(corridas["dos"])))
    t.igual("GD-27 con el motor: tres, FAILED, y no por lo que declara dos", "FAILED",
            M72._de(corridas["tres"], "status"))
    t.verdadero("GD-27 con el motor: el codigo de tres no es el de dos",
                M72._codigo(corridas["tres"]) not in (None, "AGENT_DECLARED_NOT_COMPLETE"))


def test_gd27_la_bitacora_del_host_falso_cuenta_invocaciones_e_intervalos(t):
    """GD-27 paso 6 (infraestructura de GE-E02, GE-E40, GE-E44 y GE-E71) — La bitacora lleva una linea
    por invocacion, con workUnitId, inicio y fin, escrita al empezar y al terminar: en serie los
    intervalos no se solapan, con dos motores a la vez si, y una invocacion que muere desde afuera
    igual cuenta, con `fin: null`. Una que se corta por senal anota su fin antes de morir."""
    proy = M72._proyecto(M72._unidades("uno", "dos"))
    prompt_uno, prompt_dos = _prompt_de(proy, "uno"), _prompt_de(proy, "dos")
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), dormir=0.3)
    M72._corrida(proy, "uno")
    M72._corrida(proy, "dos")
    invocaciones = _invocaciones(bitacora)
    t.igual("GD-27 una invocacion por corrida, en el orden en que empezaron", ["uno", "dos"],
            [i["workUnitId"] for i in invocaciones])
    t.verdadero("GD-27 cada una trae su inicio, su fin y su pid, y termino",
                all(i["fin"] is not None and i["inicio"] <= i["fin"] and isinstance(i["pid"], int)
                    for i in invocaciones))
    t.verdadero("GD-27 duro lo que dormia el guion", all(i["fin"] - i["inicio"] >= 0.25
                                                       for i in invocaciones))
    t.verdadero("GD-27 en serie, la segunda empieza cuando la primera ya termino: no se solapan",
                invocaciones[0]["fin"] <= invocaciones[1]["inicio"]
                and not _solapadas(invocaciones[0], invocaciones[1]))
    t.igual("GD-27 y son cuatro lineas: una al empezar y otra al terminar, por invocacion", 4,
            len(bitacora.read_text(encoding="utf-8").splitlines()))

    muerta = _ruta_de_bitacora("muerta")
    M72._guion(proy, bitacora=str(muerta), dormir=60)
    host = subprocess.Popen([sys.executable, str(M72.HOST), "-p"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(proy),
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    try:
        host.stdin.write(prompt_uno.encode("utf-8"))
        host.stdin.close()
        empezo = M72._esperar(lambda: len(_invocaciones(muerta)) == 1)
    finally:
        host.kill()
        host.communicate()
    invocaciones = _invocaciones(muerta)
    t.verdadero("GD-27 el Host empezo y lo anoto antes de dormir", empezo)
    t.igual("GD-27 una invocacion muerta desde afuera cuenta: con su unidad, su inicio y `fin: null`",
            [("uno", True, None)],
            [(i["workUnitId"], i["inicio"] > 0, i["fin"]) for i in invocaciones])

    cortada = _ruta_de_bitacora("senal")
    M72._guion(proy, bitacora=str(cortada), senal=True)
    codigo, _ = _invocar_host(proy, prompt_dos)
    t.verdadero("GD-27 un Host con senal muere como un Host cortado desde afuera",
                codigo in (143, -15))
    t.igual("GD-27 y anota su fin antes de morir", [("dos", True)],
            [(i["workUnitId"], i["fin"] is not None and i["inicio"] <= i["fin"])
             for i in _invocaciones(cortada)])

    a_la_vez = M72._proyecto(M72._unidades("uno", "dos"))
    solapada = _ruta_de_bitacora("solapada")
    M72._guion(a_la_vez, bitacora=str(solapada),
               por_unidad={"uno": {"dormir": 3}, "dos": {"dormir": 1.5}})
    uno, _ = M72._lanzar_motor(a_la_vez, "uno")
    dos, _ = M72._lanzar_motor(a_la_vez, "dos")
    salidas = [M72._salida_del_hijo(uno), M72._salida_del_hijo(dos)]
    t.igual("GD-27 dos motores a la vez, cada uno con el guion de su unidad: los dos SUCCEEDED",
            ["SUCCEEDED", "SUCCEEDED"], [(s["res"] or {}).get("status") for s in salidas])
    por_unidad = {i["workUnitId"]: i for i in _invocaciones(solapada)}
    t.igual("GD-27 la bitacora tiene las dos invocaciones, una por unidad", ["dos", "uno"],
            sorted(por_unidad))
    t.verdadero("GD-27 y sus intervalos se solapan: las dos estuvieron RUNNING a la vez",
                len(por_unidad) == 2 and _solapadas(por_unidad["uno"], por_unidad["dos"]))
    t.verdadero("GD-27 cada una duro lo que dormia su guion",
                por_unidad["uno"]["fin"] - por_unidad["uno"]["inicio"] >= 2.9
                and por_unidad["dos"]["fin"] - por_unidad["dos"]["inicio"] >= 1.4)


def test_gd27_sin_las_claves_nuevas_el_host_falso_hace_lo_de_siempre(t):
    """GD-27 paso 6 — Sin `por_unidad` ni `bitacora`, el Host falso hace lo de antes: contesta el
    resultado de siempre, no deja ninguna bitacora y no lee el prompt. La suite 72 entera, que usa solo
    los modos viejos, es el control de que nada se rompio."""
    proy = M72._proyecto(M72._unidades("uno"))
    M72._guion(proy)
    antes = M72._proyecto_sin_git(proy)
    codigo, salida = _invocar_host(proy, "un prompt que no tiene ninguna WorkUnit")
    documento = json.loads(salida)
    t.igual("GD-27 sin las claves nuevas, el resultado de siempre y salida 0",
            (0, "result", "success", False, {"declaredStatus": "COMPLETE", "artifact": "# Informe\n"}),
            (codigo, documento["type"], documento["subtype"], documento["is_error"],
             documento["structured_output"]))
    t.igual("GD-27 y no deja nada en el proyecto, ni una bitacora", [],
            M64._diferencias(antes, M72._proyecto_sin_git(proy)))
    M72._guion(proy, por_unidad={})
    t.igual("GD-27 un `por_unidad` vacio tampoco cambia nada", (0, "COMPLETE"),
            (lambda c, s: (c, json.loads(s)["structured_output"]["declaredStatus"]))(
                *_invocar_host(proy, "un prompt que no tiene ninguna WorkUnit")))


# =============================================================================================
# GRAFO: el conductor y su resultado (GD-04 a GD-09, GD-15 a GD-19, GD-22, GD-23; GD-27 pasos 7 y 8)
# =============================================================================================
#
# `grafo.conducir` en este proceso, con el Host falso de siempre. Lo que un escenario cambia a mitad del
# GraphRun lo cambia un gancho (`ganchos`), en el estilo de `antes_de_reservar` del motor. Lo que nombra a
# `ejecutar --grafo` como comando (la salida 0 o 2, `--json`) es de la etapa 6: aca se mira lo que el
# conductor devuelve y lo que deja en disco. Las carreras y los cortes con `os._exit`, de la 5b.

GRAFO_PY = M72.EJECUCION / "grafo.py"
SCHEMA_DE_GRAFO = RAIZ / "comun" / "schemas" / "graph-run-result.schema.json"
LOS_NUEVE = ("GRAPH_ALREADY_ACTIVE", "GRAPH_PLAN_UNREADABLE", "GRAPH_STRUCTURE_INVALID",
             "WORK_UNIT_NOT_SUCCEEDED", "ADMISSION_REJECTED", "TASK_EXECUTION_OPEN",
             "PLAN_FINGERPRINT_CHANGED", "DISPATCH_FAILED", "GRAPH_INTERRUPTED")


def _grafo(proy, pedido_por=PIDE, **kw):
    """{res, err, exc}: lo que devolvio el conductor, o la excepcion, que el escenario mira."""
    try:
        res, err = grafo.conducir(str(proy), CLAVE, pedido_por, **kw)
        return {"res": res, "err": err, "exc": None}
    except Exception as e:                       # noqa: BLE001 - la excepcion se mira
        return {"res": None, "err": None, "exc": "%s: %s" % (type(e).__name__, e)}


def _grafos(proy):
    return registro.grafos_de(str(proy), CLAVE)


def _leido(proy, graph_run_id):
    return registro.leer_grafo(str(proy), CLAVE, graph_run_id)


def _despachos(proy, graph_run_id):
    """[(numero, workUnitId)] de las marcas de despacho, en orden."""
    return [(n, (m or {}).get("workUnitId")) for n, m, _ in
            registro.despachos(str(proy), CLAVE, graph_run_id)]


def _ultimo(proy, unidad, huella=None):
    """El ultimo turno de la unidad bajo la huella (la del plan de hoy, por defecto), o None."""
    huella = huella or _huella_del_plan(proy)
    return registro.ultimo_turno(str(proy), CLAVE,
                                 contrato.clave_de_idempotencia(CLAVE, huella, unidad))


def _estado_de(proy, unidad, huella=None):
    ultimo = _ultimo(proy, unidad, huella)
    return ultimo["estado"] if ultimo else None


def _con_turno(proy, unidades, huella=None):
    """Las unidades que ya tienen un turno bajo la huella."""
    return [u for u in unidades if _ultimo(proy, u, huella) is not None]


def _eid_de(proy, unidad, huella=None):
    return (_ultimo(proy, unidad, huella) or {}).get("executionId") or "exe_" + "0" * 32


def _nodos(res):
    return dict((n["workUnitId"], n) for n in (res or {}).get("nodes") or [])


def _unidades_abc():
    return [M64._unidad("a"), M64._unidad("b", dependencias=("a",)),
            M64._unidad("c", dependencias=("b",))]


def _proyecto_abc(**kw):
    """El plan A->B->C: tres unidades PENDING de un agente ejecutable, con capacidades que el adaptador
    provee."""
    return M72._proyecto(_unidades_abc(), **kw)


def _intervalos(bitacora):
    """Las invocaciones del Host falso, ordenadas por cuando empezaron."""
    return sorted(_invocaciones(bitacora), key=lambda i: i["inicio"])


def _valida(t, ide, proy, graph_run_id):
    """El `result.json` del GraphRun valida contra el schema y sus coherencias (GE-E60), por la funcion
    del conductor y por el validador de subconjunto del repo, directo. Devuelve el resultado leido."""
    leido = _leido(proy, graph_run_id)
    doc = leido["resultado"]
    t.verdadero("%s el GraphRun tiene su result.json" % ide, doc is not None)
    if doc is None:
        return None
    t.igual("%s result.json valida contra graph-run-result.schema.json y sus coherencias" % ide, [],
            grafo.validar_resultado(doc, leido["inicio"]))
    esquema = json.loads(SCHEMA_DE_GRAFO.read_text(encoding="utf-8"))
    t.igual("%s y por el validador de subconjunto, directo" % ide, [],
            M64.ARMADOR.validar(doc, esquema))
    t.verdadero("%s y su error.code, si lo hay, es uno de los nueve" % ide,
                doc["error"] is None or doc["error"]["code"] in LOS_NUEVE)
    return doc


def test_ge_e01_camino_feliz(t):
    """GE-E01 — Con el plan A->B->C y un Host falso que devuelve COMPLETE para las tres, el conductor crea
    un GraphRun, deja tres marcas de despacho 001, 002 y 003 para A, B y C, tres Executions SUCCEEDED cuyas
    requests tienen `plan.planFingerprint` igual al `planFingerprint` de `inicio.json`, y un `result.json`
    SUCCEEDED con los tres nodos SATISFIED y `dispatched: true`. (Que `ejecutar <KEY> --grafo` salga con 0
    es de la etapa 6.)"""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    corrida = _grafo(proy)
    res = corrida["res"] or {}

    t.igual("GE-E01 el conductor no levanta ni rechaza al arrancar", (None, None),
            (corrida["exc"], corrida["err"]))
    t.igual("GE-E01 el GraphRun termina SUCCEEDED, sin error y sin pedido de cancelacion",
            ("SUCCEEDED", None, False), (res.get("status"), res.get("error"), res.get("cancelRequested")))
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E01 hay exactamente un GraphRun, y es el del resultado", [graph_run_id], _grafos(proy))
    t.igual("GE-E01 tres marcas de despacho, 001 a 003, para A, B y C", [(1, "a"), (2, "b"), (3, "c")],
            _despachos(proy, graph_run_id))
    leido = _leido(proy, graph_run_id)
    t.igual("GE-E01 el resultado que vuelve es el result.json que quedo escrito", res, leido["resultado"])
    t.igual("GE-E01 el GraphRun terminal no es ACTIVE", "SUCCEEDED", leido["estado"])

    huella = leido["inicio"]["planFingerprint"]
    t.igual("GE-E01 el inicio.json lleva la huella del plan", _huella_del_plan(proy), huella)
    for unidad in ("a", "b", "c"):
        eid = _eid_de(proy, unidad)
        t.igual("GE-E01 %s tiene un solo turno, de su Execution" % unidad, [(1, eid)],
                M72._turnos(proy, unidad))
        t.igual("GE-E01 %s termino SUCCEEDED" % unidad, "SUCCEEDED",
                registro.estado(str(proy), CLAVE, eid)["estado"])
        t.igual("GE-E01 la request de %s tiene plan.planFingerprint igual al de inicio.json" % unidad,
                huella, _request_de(proy, eid)["plan"]["planFingerprint"])
    nodos = _nodos(res)
    t.igual("GE-E01 los tres nodos estan SATISFIED y dispatched: true",
            [("a", "SATISFIED", True), ("b", "SATISFIED", True), ("c", "SATISFIED", True)],
            [(u, nodos.get(u, {}).get("state"), nodos.get(u, {}).get("dispatched"))
             for u in ("a", "b", "c")])
    t.igual("GE-E01 cada marca nombra la Execution de su turno",
            [_eid_de(proy, u) for u in ("a", "b", "c")],
            [m["executionId"] for _, m, _ in registro.despachos(str(proy), CLAVE, graph_run_id)])
    t.igual("GE-E01 el Host recibio una invocacion por unidad, en orden", ["a", "b", "c"],
            [i["workUnitId"] for i in _intervalos(bitacora)])
    _valida(t, "GE-E01", proy, graph_run_id)


def test_ge_e02_las_unidades_se_despachan_de_a_una(t):
    """GE-E02 — Con A->{B, C}, los despachos son A, B, C en ese orden; ni B ni C tienen turno antes de que
    exista el `result.json` de A; y los intervalos de las tres invocaciones del Host, registrados por la
    bitacora, no se solapan."""
    # El plan trae las unidades en otro orden que el topologico: lo que se despacha es el de
    # `orden_de_ejecucion`, no el de `workUnits` (GE-I08).
    proy = M72._proyecto([M64._unidad("c", dependencias=("a",)), M64._unidad("b", dependencias=("a",)),
                          M64._unidad("a")])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), dormir=0.2)
    visto = {}

    def al_despachar(marca):
        visto[marca["workUnitId"]] = (_con_turno(proy, ("a", "b", "c")),
                                      [u for u in ("a", "b", "c") if _estado_de(proy, u) == "SUCCEEDED"])

    res = _grafo(proy, ganchos={"despues_del_despacho": al_despachar})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E02 termina SUCCEEDED", "SUCCEEDED", res.get("status"))
    t.igual("GE-E02 los despachos son A, B, C en ese orden", [(1, "a"), (2, "b"), (3, "c")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E02 al despachar A no hay ningun turno", ([], []), visto.get("a"))
    t.igual("GE-E02 al despachar B, solo A tiene turno y esta SUCCEEDED: C no tiene", (["a"], ["a"]),
            visto.get("b"))
    t.igual("GE-E02 al despachar C, A y B tienen turno y estan SUCCEEDED", (["a", "b"], ["a", "b"]),
            visto.get("c"))
    resultado_de = {u: M72._carpeta(proy, _eid_de(proy, u)) / registro.RESULT for u in ("a", "b", "c")}
    turno_de = {u: Path(registro.ruta_del_turno(str(proy), CLAVE, _llave_de(proy, u), 1))
                for u in ("a", "b", "c")}
    t.verdadero("GE-E02 el turno de B y el de C son posteriores al result.json de A, y el de C al de B",
                turno_de["b"].stat().st_mtime_ns >= resultado_de["a"].stat().st_mtime_ns
                and turno_de["c"].stat().st_mtime_ns >= resultado_de["a"].stat().st_mtime_ns
                and turno_de["c"].stat().st_mtime_ns >= resultado_de["b"].stat().st_mtime_ns)
    invocaciones = _intervalos(bitacora)
    t.igual("GE-E02 el Host recibio tres invocaciones, en el orden de los despachos", ["a", "b", "c"],
            [i["workUnitId"] for i in invocaciones])
    t.verdadero("GE-E02 las tres terminaron, y duraron lo que dormia el guion",
                len(invocaciones) == 3 and all(i["fin"] is not None and i["fin"] - i["inicio"] >= 0.15
                                               for i in invocaciones))
    t.verdadero("GE-E02 los intervalos no se solapan: cada una empieza cuando la anterior termino",
                len(invocaciones) == 3 and all(
                    invocaciones[i]["fin"] <= invocaciones[i + 1]["inicio"]
                    and not _solapadas(invocaciones[i], invocaciones[i + 1]) for i in range(2)))
    _valida(t, "GE-E02", proy, graph_run_id)


def _llave_de(proy, unidad, huella=None):
    return contrato.clave_de_idempotencia(CLAVE, huella or _huella_del_plan(proy), unidad)


def test_ge_e03_una_unidad_espera_a_todas_sus_dependencias(t):
    """GE-E03 — Con {B, C}->D, D no tiene turno mientras B o C no esten SUCCEEDED, y la request de D lleva
    en `admission.dependencies` los `executionId` de B y de C. La elegibilidad (GD-08, GE-I09) la decide el
    conductor con `dependencies` y el ultimo turno bajo F, no la admision: con el registro de B alterado
    despues de que B termino, D no se despacha, y no es la condicion 14 la que lo detiene."""
    unidades = [M64._unidad("b"), M64._unidad("c"), M64._unidad("d", dependencias=("b", "c"))]
    proy = M72._proyecto(unidades)
    M72._guion(proy)
    visto = {}

    def al_despachar(marca):
        visto[marca["workUnitId"]] = (_con_turno(proy, ("b", "c", "d")),
                                      [u for u in ("b", "c") if _estado_de(proy, u) == "SUCCEEDED"])

    res = _grafo(proy, ganchos={"despues_del_despacho": al_despachar})["res"] or {}
    t.igual("GE-E03 termina SUCCEEDED, despachando b, c y d en ese orden",
            ("SUCCEEDED", [(1, "b"), (2, "c"), (3, "d")]),
            (res.get("status"), _despachos(proy, res.get("graphRunId") or "grf_" + "0" * 32)))
    t.igual("GE-E03 al despachar D, B y C estan SUCCEEDED y D no tiene turno", (["b", "c"], ["b", "c"]),
            visto.get("d"))
    t.igual("GE-E03 la request de D nombra, en admission.dependencies, las Executions de B y de C",
            [{"workUnitId": "b", "executionId": _eid_de(proy, "b")},
             {"workUnitId": "c", "executionId": _eid_de(proy, "c")}],
            _request_de(proy, _eid_de(proy, "d"))["admission"]["dependencies"])

    otro = M72._proyecto(unidades)
    bitacora = _ruta_de_bitacora()
    M72._guion(otro, bitacora=str(bitacora))

    def borrar_el_turno_de_b(marca):
        if marca["workUnitId"] == "c":
            for ruta in Path(registro.carpeta_de_clave(str(otro), CLAVE, _llave_de(otro, "b"))).iterdir():
                ruta.unlink()

    alterado = _grafo(otro, ganchos={"despues_del_retorno": borrar_el_turno_de_b})["res"] or {}
    graph_run_id = alterado.get("graphRunId") or "grf_" + "0" * 32
    error = alterado.get("error") or {}
    t.igual("GE-E03 con B sin turno despues de C, el GraphRun cierra FAILED con WORK_UNIT_NOT_SUCCEEDED "
            "por B", ("FAILED", "WORK_UNIT_NOT_SUCCEEDED", "b"),
            (alterado.get("status"), error.get("code"), error.get("workUnitId")))
    t.igual("GE-E03 D no tiene marca de despacho ni turno, y el Host no la recibio",
            ([(1, "b"), (2, "c")], [], ["b", "c"]),
            (_despachos(otro, graph_run_id), _con_turno(otro, ("d",)),
             [i["workUnitId"] for i in _intervalos(bitacora)]))
    t.igual("GE-E03 no fue la admision (DEPENDENCY_NOT_SATISFIED) la que lo detuvo", None,
            error.get("executionCode"))
    t.igual("GE-E03 el nodo de B esta NOT_STARTED y el de D tambien",
            ("NOT_STARTED", "NOT_STARTED"),
            (_nodos(alterado)["b"]["state"], _nodos(alterado)["d"]["state"]))
    _valida(t, "GE-E03", proy, (res.get("graphRunId") or "grf_" + "0" * 32))
    _valida(t, "GE-E03 (registro alterado)", otro, graph_run_id)


def test_ge_e04_los_despachos_siguen_el_orden_de_orden_de_ejecucion(t):
    """GE-E04 — Con tres unidades sin dependencias, `zeta`, `alfa` y `medio`, los despachos son `alfa`,
    `medio`, `zeta`: el orden de `orden_de_ejecucion`, por punto de codigo, no el del plan."""
    proy = M72._proyecto([M64._unidad("zeta"), M64._unidad("alfa"), M64._unidad("medio")])
    M72._guion(proy)
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E04 el plan trae las unidades en otro orden que el de los despachos",
            ["zeta", "alfa", "medio"], [u["id"] for u in plan["workUnits"]])
    t.igual("GE-E04 los despachos son alfa, medio, zeta", [(1, "alfa"), (2, "medio"), (3, "zeta")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E04 inicio.json congela el mismo orden, y `nodes` en el del plan",
            (["alfa", "medio", "zeta"], ["zeta", "alfa", "medio"]),
            (_leido(proy, graph_run_id)["inicio"]["order"],
             [n["workUnitId"] for n in _leido(proy, graph_run_id)["inicio"]["nodes"]]))
    t.igual("GE-E04 y `nodes` del resultado va en el orden de `order`", ["alfa", "medio", "zeta"],
            [n["workUnitId"] for n in res.get("nodes") or []])
    _valida(t, "GE-E04", proy, graph_run_id)


def _bytes_de(proy, execution_id):
    """{ruta: huella} de lo que hay en la carpeta de una Execution."""
    return _de_la_execution(proy, execution_id)


def test_ge_e05_una_unidad_ya_succeeded_se_adopta(t):
    """GE-E05 — Con A ya SUCCEEDED bajo F por una ejecucion anterior (`ejecutar --unidad`), el GraphRun no
    crea un turno para A, los archivos de la Execution de A quedan identicos byte a byte, el Host recibe dos
    invocaciones (B y C), y el nodo A del resultado esta SATISFIED con `dispatched: false`."""
    proy = _proyecto_abc()
    M72._guion(proy)
    de_a = M72._corrida(proy, "a")
    eid_a = _eid(de_a)
    t.igual("GE-E05 A queda SUCCEEDED por la ejecucion manual", "SUCCEEDED", M72._de(de_a, "status"))
    antes = _bytes_de(proy, eid_a)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32

    t.igual("GE-E05 el GraphRun termina SUCCEEDED", "SUCCEEDED", res.get("status"))
    t.igual("GE-E05 A conserva su unico turno, el de la manual", [(1, eid_a)], M72._turnos(proy, "a"))
    t.igual("GE-E05 los archivos de la Execution de A quedan identicos", antes, _bytes_de(proy, eid_a))
    t.igual("GE-E05 solo B y C se despachan", [(1, "b"), (2, "c")], _despachos(proy, graph_run_id))
    t.igual("GE-E05 el Host recibe dos invocaciones, B y C", ["b", "c"],
            [i["workUnitId"] for i in _intervalos(bitacora)])
    nodo_a = _nodos(res).get("a") or {}
    t.igual("GE-E05 el nodo A esta SATISFIED, con el turno y la Execution de la manual, y dispatched: false",
            ("SATISFIED", 1, eid_a, False),
            (nodo_a.get("state"), nodo_a.get("turn"), nodo_a.get("executionId"), nodo_a.get("dispatched")))
    t.igual("GE-E05 B y C estan dispatched: true", [True, True],
            [(_nodos(res).get(u) or {}).get("dispatched") for u in ("b", "c")])
    _valida(t, "GE-E05", proy, graph_run_id)


def test_ge_e06_con_todo_succeeded_no_hay_despachos(t):
    """GE-E06 — Con las tres unidades ya SUCCEEDED bajo F, el conductor crea un GraphRun sin marcas de
    despacho, con `result.json` SUCCEEDED, y el Host no recibe invocaciones: queda constancia de que ese
    plan llego a termino (§9.1)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    previas = [_eid(M72._corrida(proy, u)) for u in ("a", "b", "c")]
    antes = dict((e, _bytes_de(proy, e)) for e in previas)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32

    t.igual("GE-E06 SUCCEEDED, sin error", ("SUCCEEDED", None), (res.get("status"), res.get("error")))
    t.igual("GE-E06 el GraphRun existe y no tiene marcas de despacho", ([graph_run_id], []),
            (_grafos(proy), _despachos(proy, graph_run_id)))
    t.igual("GE-E06 el Host no recibe invocaciones", [], _invocaciones(bitacora))
    t.igual("GE-E06 ninguna Execution nueva: las tres de siempre, identicas",
            (sorted(previas), antes),
            (M72._carpetas(proy), dict((e, _bytes_de(proy, e)) for e in previas)))
    t.igual("GE-E06 los tres nodos SATISFIED y dispatched: false",
            [("SATISFIED", False)] * 3,
            [(n["state"], n["dispatched"]) for n in res.get("nodes") or []])
    _valida(t, "GE-E06", proy, graph_run_id)


def test_ge_e07_dos_graphruns_seguidos(t):
    """GE-E07 — Dos `--grafo` seguidos sobre el mismo plan dejan dos GraphRuns con ids distintos, los dos
    SUCCEEDED, y el segundo no crea ninguna Execution: un terminal es terminal, y relanzar no es reanudar
    (GD-13)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    primero = _grafo(proy)["res"] or {}
    arbol = M72._arbol(proy)
    segundo = _grafo(proy)["res"] or {}
    ids = [primero.get("graphRunId"), segundo.get("graphRunId")]

    t.igual("GE-E07 dos GraphRuns, con ids distintos", (2, True),
            (len(_grafos(proy)), len(set(ids)) == 2 and None not in ids))
    t.igual("GE-E07 los dos SUCCEEDED", ["SUCCEEDED", "SUCCEEDED"],
            [primero.get("status"), segundo.get("status")])
    t.igual("GE-E07 el segundo no despacha nada", ([(1, "a"), (2, "b"), (3, "c")], []),
            (_despachos(proy, ids[0]), _despachos(proy, ids[1] or "grf_" + "0" * 32)))
    t.igual("GE-E07 ninguna Execution nueva: sigue una por unidad", 3, len(M72._carpetas(proy)))
    t.igual("GE-E07 y el Host recibio las tres invocaciones del primero y ninguna del segundo", 3,
            len(_invocaciones(bitacora)))
    t.igual("GE-E07 todo lo que cambio fue el GraphRun nuevo, bajo grafos/",
            [], [d for d in M64._diferencias(arbol, M72._arbol(proy))
                 if "/%s/" % GRAFOS not in d.split(" ", 1)[1]])
    t.igual("GE-E07 el segundo lista los tres nodos como SATISFIED, con dispatched: false",
            [("SATISFIED", False)] * 3, [(n["state"], n["dispatched"]) for n in segundo.get("nodes") or []])
    for graph_run_id in ids:
        _valida(t, "GE-E07", proy, graph_run_id or "grf_" + "0" * 32)


def _plan_original(proy):
    return M64._plan_de(proy, CLAVE).read_bytes()


def _nada_creado(t, ide, proy):
    """Un rechazo al arrancar no crea un GraphRun ni una Execution (GD-04, §9.1, GE-I07): ni una carpeta
    `grf_...`, ni un residuo de una, ni una Execution, ni un turno."""
    base = M72._ejecuciones(proy) / CLAVE
    t.igual("%s no hay un GraphRun, ni una carpeta grf_ sin inicio.json" % ide, ([], []),
            (_grafos(proy), registro.residuos_de_grafos(str(proy), CLAVE)))
    t.igual("%s ni una Execution, ni un residuo de una, ni un turno" % ide, ([], []),
            (M72._carpetas(proy), registro.nombradas(str(proy), CLAVE)))
    t.vacio("%s y la carpeta de la tarea no tiene nada mas que `grafos/` con el candado" % ide,
            [p.name for p in base.iterdir() if p.name not in (GRAFOS, registro.CLAVES)])


def test_ge_e08_estructura_invalida(t):
    """GE-E08 — Un plan guardado a mano con un ciclo, con una unidad que depende de si misma, con una
    dependencia a una unidad inexistente, con una dependencia repetida (`["a", "a"]`) o sin unidades: el
    conductor no empieza, con GRAPH_STRUCTURE_INVALID, y no queda ninguna carpeta `grf_...`, ningun turno ni
    ninguna Execution. (Que `--grafo` salga con 2 es de la etapa 6.)"""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    original = _plan_original(proy)

    def deps(unidad, dependencias):
        def cambio(plan):
            next(u for u in plan["workUnits"] if u["id"] == unidad)["dependencies"] = dependencias
        return cambio

    casos = (("un ciclo", deps("a", ["c"])), ("una unidad que depende de si misma", deps("a", ["a"])),
             ("una dependencia a una unidad inexistente", deps("a", ["no-existe"])),
             ("una dependencia repetida", deps("b", ["a", "a"])),
             ("un plan sin unidades", lambda plan: plan.update(workUnits=[])))
    for nombre, cambio in casos:
        M72._reescribir_plan(proy, cambio)
        corrida = _grafo(proy)
        t.igual("GE-E08 %s: no empieza, con GRAPH_STRUCTURE_INVALID y sin resultado ni excepcion" % nombre,
                (None, None, "GRAPH_STRUCTURE_INVALID"),
                (corrida["exc"], corrida["res"], (corrida["err"] or {}).get("code")))
        t.verdadero("GE-E08 %s: el rechazo trae un detail de hasta 300 caracteres" % nombre,
                    0 < len((corrida["err"] or {}).get("detail", "")) <= 300)
        _nada_creado(t, "GE-E08 %s:" % nombre, proy)
        M64._plan_de(proy, CLAVE).write_bytes(original)
    t.igual("GE-E08 el Host no recibio ninguna invocacion", [], _invocaciones(bitacora))
    t.contiene("GE-E08 un ciclo nombra las unidades enredadas", "a, b, c",
               (lambda: (M72._reescribir_plan(proy, deps("a", ["c"])), _grafo(proy)["err"]["detail"])[1])())
    M64._plan_de(proy, CLAVE).write_bytes(original)
    t.contiene("GE-E08 una dependencia repetida nombra la unidad y la dependencia", "b repite su dependencia a",
               (lambda: (M72._reescribir_plan(proy, deps("b", ["a", "a"])), _grafo(proy)["err"]["detail"])[1])())


def test_ge_e09_plan_ilegible(t):
    """GE-E09 — Sin plan, con un plan que no es JSON, con un plan de otra TaskKey o con dos unidades del
    mismo id: el conductor no empieza, con GRAPH_PLAN_UNREADABLE, sin carpeta `grf_...` ni Execution. (Que
    `--grafo` salga con 2 es de la etapa 6.)"""
    proy = _proyecto_abc()
    M72._guion(proy)
    original = _plan_original(proy)
    ruta = M64._plan_de(proy, CLAVE)

    def repetida(plan):
        plan["workUnits"].append(dict(plan["workUnits"][0]))

    def otra_tarea(plan):
        plan["meta"]["task_key"] = "GCBA-99"

    casos = (("sin plan guardado", lambda: ruta.unlink()),
             ("un plan que no es JSON", lambda: ruta.write_bytes(b'{"meta": {"task_key": ')),
             ("un plan de otra TaskKey", lambda: M72._reescribir_plan(proy, otra_tarea)),
             ("dos unidades con el mismo id", lambda: M72._reescribir_plan(proy, repetida)))
    for nombre, preparar in casos:
        preparar()
        corrida = _grafo(proy)
        t.igual("GE-E09 %s: no empieza, con GRAPH_PLAN_UNREADABLE y sin resultado ni excepcion" % nombre,
                (None, None, "GRAPH_PLAN_UNREADABLE"),
                (corrida["exc"], corrida["res"], (corrida["err"] or {}).get("code")))
        t.verdadero("GE-E09 %s: el rechazo trae un detail de hasta 300 caracteres" % nombre,
                    0 < len((corrida["err"] or {}).get("detail", "")) <= 300)
        _nada_creado(t, "GE-E09 %s:" % nombre, proy)
        ruta.write_bytes(original)


def test_ge_e10_el_orden_es_determinista(t):
    """GE-E10 — El mismo plan de cinco unidades, con dos niveles y fan-in, en dos proyectos recien armados,
    da la misma secuencia de `workUnitId` en las marcas de despacho: la del orden topologico de
    `orden_de_ejecucion`, y no la del plan guardado ni el `executionOrder` del documento (GE-I08)."""
    unidades = [M64._unidad("cierre", dependencias=("hoja", "medio")),
                M64._unidad("hoja", dependencias=("raiz-a", "raiz-b")),
                M64._unidad("raiz-b"), M64._unidad("raiz-a"),
                M64._unidad("medio", dependencias=("raiz-a",))]
    secuencias, ordenes = [], []
    for _ in range(2):
        proy = M72._proyecto(unidades)
        M72._guion(proy)
        res = _grafo(proy)["res"] or {}
        graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
        secuencias.append([u for _, u in _despachos(proy, graph_run_id)])
        ordenes.append((res.get("status"), [u["id"] for u in M64._leer_json(
            M64._plan_de(proy, CLAVE))["workUnits"]]))
        _valida(t, "GE-E10", proy, graph_run_id)
    esperada = ["raiz-a", "raiz-b", "hoja", "medio", "cierre"]
    t.igual("GE-E10 la secuencia es la del orden topologico, por punto de codigo en cada nivel",
            [esperada, esperada], secuencias)
    t.igual("GE-E10 los dos GraphRuns terminan SUCCEEDED", ["SUCCEEDED", "SUCCEEDED"],
            [s for s, _ in ordenes])
    t.verdadero("GE-E10 y el plan guardado no trae las unidades en ese orden: no es el orden del plan",
                all(orden != esperada for _, orden in ordenes))


# -- la admision: el GraphRun elige, la admision decide (GD-17, GD-18, GD-19) ---------------------

def _proyecto_a_y_b_frontend():
    """B es de otro dominio que A, con su propio agente: lo que se le quita a B no le toca a A."""
    return M72._proyecto([M64._unidad("a"), M64._unidad("b", dominio="frontend", dependencias=("a",))],
                         dominios=("backend", "frontend"), agentes=("dev-backend", "dev-frontend"))


def _al_retornar(unidad, accion):
    """Un gancho `despues_del_retorno` que hace `accion` cuando vuelve el motor de `unidad`."""
    return lambda marca: accion() if marca["workUnitId"] == unidad else None


def _causa_de(res):
    """(code, workUnitId, executionId, executionStatus, executionCode) del error de un resultado."""
    error = (res or {}).get("error") or {}
    return tuple(error.get(c) for c in ("code", "workUnitId", "executionId", "executionStatus",
                                        "executionCode"))


def test_ge_e11_el_flujo_deja_de_permitir_delegar(t):
    """GE-E11 — Con A->B->C y un gancho que, despues de que A queda SUCCEEDED, deja al flujo sin permiso de
    delegar: B no tiene turno, C tampoco, y el GraphRun cierra FAILED con ADMISSION_REJECTED, `workUnitId:
    b`, `executionId: null` y `executionCode: DELEGATION_NOT_ALLOWED`. La Execution de A queda identica.
    El GraphRun no guarda el flujo: lo decide la admision en cada despacho (GD-17)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    de_a = {}

    def cortar(marca):
        if marca["workUnitId"] == "a":
            de_a.update(_bytes_de(proy, marca["executionId"]))
            M72._contexto_cambiado(proy)

    corrida = _grafo(proy, ganchos={"despues_del_retorno": cortar})
    res = corrida["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E11 cierra FAILED con ADMISSION_REJECTED por B, sin Execution y con el codigo de la admision",
            ("FAILED", ("ADMISSION_REJECTED", "b", None, None, "DELEGATION_NOT_ALLOWED")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E11 B y C no tienen turno, y el Host solo recibio a A", ([], ["a"]),
            (_con_turno(proy, ("b", "c"), _huella_del_plan_viejo(res)), [i["workUnitId"] for i in _intervalos(bitacora)]))
    t.igual("GE-E11 la Execution de A queda identica", de_a, _bytes_de(proy, _eid_de(proy, "a")))
    t.igual("GE-E11 B tiene su marca de despacho, que ningun turno nombra, y C no", [(1, "a"), (2, "b")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E11 los nodos: A SATISFIED y los otros NOT_STARTED", ["SATISFIED", "NOT_STARTED", "NOT_STARTED"],
            [n["state"] for n in res.get("nodes") or []])
    t.contiene("GE-E11 el detail nombra la unidad", "b", (res.get("error") or {}).get("detail"))
    _valida(t, "GE-E11", proy, graph_run_id)


def _huella_del_plan_viejo(res):
    """La huella F del GraphRun, que es la del plan que se conduce."""
    return (res or {}).get("planFingerprint")


def _normas(proy, unidad_id, estandares):
    """Le pone a la unidad las normas `estandares` y reconcilia el flujo con el plan nuevo."""
    from estado_de_tarea import persistencia

    def cambio(plan):
        for unidad in plan["workUnits"]:
            if unidad["id"] == unidad_id:
                unidad.setdefault("normative", {})["standards"] = dict((e, {}) for e in estandares)
    M72._reescribir_plan(proy, cambio)
    persistencia.reconciliar(str(proy), CLAVE)


def test_ge_e12_la_compuerta_corre_por_cada_unidad_con_sus_normas(t):
    """GE-E12 — Con una compuerta que bloquea solo las normas de B, el GraphRun cierra con
    ADMISSION_REJECTED y `executionCode: NORMATIVE_GATE_BLOCKED`; la compuerta se llamo con las normas de A
    al despachar A y con las de B al despachar B, nunca una sola vez para el GraphRun entero (GD-18)."""
    from orquestacion import auto_refresh
    proy = M72._proyecto(_unidades_abc()[:2])
    _normas(proy, "b", ["ES0903"])
    M72._guion(proy)
    plan = M64._leer_json(M64._plan_de(proy, CLAVE))
    normas_a = admision.normas_de(next(u for u in plan["workUnits"] if u["id"] == "a"))
    llamadas = []
    real = admision.compuerta_por_defecto(str(proy))

    def compuerta(requeridas):
        llamadas.append(list(requeridas))
        if "ES0903" in requeridas:
            return {"decision": auto_refresh.BLOQUEADO, "reason": "ES0903 SOURCE_INTEGRITY_ALERT"}
        return real(requeridas)

    res = _grafo(proy, compuerta=compuerta)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E12 cierra FAILED con ADMISSION_REJECTED por B y NORMATIVE_GATE_BLOCKED",
            ("FAILED", ("ADMISSION_REJECTED", "b", None, None, "NORMATIVE_GATE_BLOCKED")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E12 la compuerta se llamo con las normas de A al pedir y al entregar A, y con las de B al "
            "despachar B: tres veces, cada una con las de su unidad",
            [normas_a, normas_a, ["ES0903"]], llamadas)
    t.igual("GE-E12 B no tiene turno, y A quedo SUCCEEDED", (None, "SUCCEEDED"),
            (_estado_de(proy, "b"), _estado_de(proy, "a")))
    _valida(t, "GE-E12", proy, graph_run_id)


def test_ge_e13_el_agente_de_b_deja_de_rutear(t):
    """GE-E13 — Con el agente de B que deja de rutear despues de A, el GraphRun cierra con
    ADMISSION_REJECTED y `executionCode: AGENT_UNAVAILABLE`, sin turno para B."""
    from orquestacion import registro_agentes
    proy = _proyecto_a_y_b_frontend()
    M72._guion(proy)
    real = registro_agentes.cargar()
    estado = {"quitar": False}

    def cargar():
        doc = copy.deepcopy(real)
        if estado["quitar"]:
            doc["agents"] = [a for a in doc["agents"] if a.get("id") != "dev-frontend"]
        return doc

    res = _grafo(proy, cargar_registro=cargar, ganchos={
        "despues_del_retorno": _al_retornar("a", lambda: estado.update(quitar=True))})["res"] or {}
    t.igual("GE-E13 cierra FAILED con ADMISSION_REJECTED por B y AGENT_UNAVAILABLE",
            ("FAILED", ("ADMISSION_REJECTED", "b", None, None, "AGENT_UNAVAILABLE")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E13 B no tiene turno, y A quedo SUCCEEDED", (None, "SUCCEEDED"),
            (_estado_de(proy, "b"), _estado_de(proy, "a")))
    _valida(t, "GE-E13", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e14_una_capability_de_b_deja_de_estar(t):
    """GE-E14 — Con una capability de B que deja de estar disponible despues de A, el GraphRun cierra con
    ADMISSION_REJECTED y `executionCode: CAPABILITY_UNAVAILABLE`, sin turno para B. Elige por elegibles, no
    por capacidades: la condicion 13 es de la admision (GD-19)."""
    proy = M72._proyecto([M64._unidad("a"), M64._unidad("b", capacidades=("jira.issue.read",),
                                                           dependencias=("a",))])
    M72._guion(proy)

    def apagar():
        M64._json(Path(proy) / ".claude" / "harness.capacidades.json",
                  {"capacidades": dict(M64.REGISTRO, **{"jira.issue.read": "DISABLED"})})

    res = _grafo(proy, adaptador=M72._ProveeTodo([sys.executable, str(M72.HOST)], 60),
                 ganchos={"despues_del_retorno": _al_retornar("a", apagar)})["res"] or {}
    t.igual("GE-E14 cierra FAILED con ADMISSION_REJECTED por B y CAPABILITY_UNAVAILABLE",
            ("FAILED", ("ADMISSION_REJECTED", "b", None, None, "CAPABILITY_UNAVAILABLE")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E14 B no tiene turno, y A quedo SUCCEEDED", (None, "SUCCEEDED"),
            (_estado_de(proy, "b"), _estado_de(proy, "a")))
    _valida(t, "GE-E14", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e15_el_agente_de_b_desaparece_antes_de_entregar(t):
    """GE-E15 — Con un gancho `antes_de_entregar` que borra `.claude/agents/<agente de B>.md`, B queda
    REJECTED con AGENT_UNAVAILABLE, sin entrega.json, y el GraphRun cierra con WORK_UNIT_NOT_SUCCEEDED,
    `executionId` el de B, `executionStatus: REJECTED`."""
    proy = _proyecto_a_y_b_frontend()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))

    def borrar(carpeta):
        if M64._leer_json(Path(carpeta) / registro.REQUEST)["workUnit"]["id"] == "b":
            (Path(proy) / ".claude" / "agents" / "dev-frontend.md").unlink()

    res = _grafo(proy, ganchos={"antes_de_entregar": borrar})["res"] or {}
    eid_b = _eid_de(proy, "b")
    t.igual("GE-E15 cierra FAILED con WORK_UNIT_NOT_SUCCEEDED, con la Execution de B, REJECTED, por "
            "AGENT_UNAVAILABLE",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "REJECTED", "AGENT_UNAVAILABLE")),
            (res.get("status"), _causa_de(res)))
    t.verdadero("GE-E15 B se admitio al pedir y se rechazo antes de entregarse: sin entrega.json ni Host",
                _sin_entrega(proy, eid_b) and ["a"] == [i["workUnitId"] for i in _intervalos(bitacora)])
    t.igual("GE-E15 B, un turno, REJECTED; C no existe", [(1, eid_b)], M72._turnos(proy, "b"))
    t.igual("GE-E15 el nodo de B esta NOT_SATISFIED, con su Execution, dispatched: true",
            ("NOT_SATISFIED", eid_b, True),
            tuple(_nodos(res).get("b", {}).get(c) for c in ("state", "executionId", "dispatched")))
    _valida(t, "GE-E15", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e16_un_plan_que_no_esta_listo(t):
    """GE-E16 — Con un plan que no esta READY_FOR_EXECUTION, el GraphRun se crea, ninguna Execution existe,
    y cierra con ADMISSION_REJECTED y `executionCode: PLAN_NOT_READY`: la estructura valida, y es la
    admision la que no deja pedir."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    M72._reescribir_plan(proy, lambda plan: plan.update(status="WAITING_FOR_HUMAN_APPROVAL"))
    corrida = _grafo(proy)
    res = corrida["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E16 el GraphRun se crea y cierra FAILED con ADMISSION_REJECTED por A y PLAN_NOT_READY",
            (None, [graph_run_id], "FAILED", ("ADMISSION_REJECTED", "a", None, None, "PLAN_NOT_READY")),
            (corrida["exc"], _grafos(proy), res.get("status"), _causa_de(res)))
    t.igual("GE-E16 ninguna Execution, ningun turno, y el Host no recibio nada", ([], [], []),
            (M72._carpetas(proy), registro.nombradas(str(proy), CLAVE), _invocaciones(bitacora)))
    t.igual("GE-E16 los tres nodos NOT_STARTED", ["NOT_STARTED"] * 3,
            [n["state"] for n in res.get("nodes") or []])
    _valida(t, "GE-E16", proy, graph_run_id)


def _llamadas_de(ruta):
    """[(linea, nombre)] de cada llamada de un fuente, con el nombre completo de lo que llama."""
    return [(n.lineno, M72._nombre(n.func)) for n in ast.walk(ast.parse(
        Path(ruta).read_text(encoding="utf-8"))) if isinstance(n, ast.Call)]


def test_ge_e17_el_conductor_no_evalua_ni_lee_texto(t):
    """GE-E17 — `ejecucion/grafo.py` no importa `flujo`, `auto_refresh`, `registro_agentes`,
    `capacidades`, `contabilidad` ni `refutacion`; no llama a `admision._regla`, `admision.al_pedir`,
    `admision.al_entregar`, `adaptador.provee` ni `plan.escribir`; y no lee `detail` ni `artifact` de un
    resultado o un rechazo: ningun acceso `["detail"]`, `.get("detail")`, `["artifact"]` ni
    `.get("artifact")` (GE-I06, GE-I20, GE-I26)."""
    t.verdadero("GE-E17 grafo.py existe en bin/ejecucion/", GRAFO_PY.is_file())
    t.vacio("GE-E17 no importa flujo, auto_refresh, registro_agentes, capacidades, contabilidad ni "
            "refutacion",
            sorted(M72._importados(GRAFO_PY) & {"flujo", "auto_refresh", "registro_agentes",
                                                "capacidades", "contabilidad", "refutacion"}))
    llamadas = _llamadas_de(GRAFO_PY)
    t.vacio("GE-E17 no llama a la regla, a las admisiones ni a provee ni escribe el plan",
            ["%d %s" % (linea, n) for linea, n in llamadas
             if n.split(".")[-1] in ("_regla", "al_pedir", "al_entregar", "provee")
             or (n.split(".")[-1] == "escribir" and "plan" in n)])
    t.verdadero("GE-E17 y lee el plan con la funcion de la admision: el control no es vacuo",
                any(n == "admision.leer_plan" for _, n in llamadas)
                and any(n == "motor.ejecutar" for _, n in llamadas))
    # Task 5 / etapa 5b, GD-11 y 16.1: propagar una cancelacion es `motor.cancelar` sobre una Execution propia
    # (GE-I18), asi que el conductor puede llamarla, y solo desde un lugar (la guarda de la 5a, sin cancelar,
    # no podia verla).
    t.vacio("GE-E17 del motor llama solo a ejecutar, recuperar, configuracion y cancelar",
            sorted(set(n for _, n in llamadas if n.startswith("motor."))
                   - {"motor.ejecutar", "motor.recuperar", "motor.configuracion", "motor.ErrorDelComando",
                      "motor.cancelar"}))
    t.igual("GE-E17 y `motor.cancelar` se llama en un solo lugar, `_cancelar_las_propias`: la que cancela "
            "solo lo propio", ["_cancelar_las_propias"],
            sorted(set(f.name for f in ast.walk(ast.parse(GRAFO_PY.read_text(encoding="utf-8")))
                       if isinstance(f, ast.FunctionDef)
                       and any(isinstance(c, ast.Call) and M72._nombre(c.func) == "motor.cancelar"
                               for c in ast.walk(f)))))
    malos = []
    for n in ast.walk(ast.parse(GRAFO_PY.read_text(encoding="utf-8"))):
        if (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                and n.slice.value in ("detail", "artifact")):
            malos.append("%d [%r]" % (n.lineno, n.slice.value))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get"
                and n.args and isinstance(n.args[0], ast.Constant)
                and n.args[0].value in ("detail", "artifact")):
            malos.append("%d .get(%r)" % (n.lineno, n.args[0].value))
    t.vacio("GE-E17 ningun acceso a detail ni a artifact", malos)
    t.vacio("GE-E17 ni lee `result` (ME-E29), ni el texto del artifact",
            M72._lee_result(GRAFO_PY) + M72._usos_del_artifact(GRAFO_PY))
    t.vacio("GE-E17 ni nombra un campo de reintento (EX-E50)",
            [c for c in ("maxRetries", "allowEscalation", "retryPolicy", "timeoutSeconds")
             if c in GRAFO_PY.read_text(encoding="utf-8")])


# -- dependencias y fallas (GD-08, GD-09) ------------------------------------------------------

def test_ge_e18_la_primera_falla_cierra_el_graphrun(t):
    """GE-E18 — Con A->B->C mas una unidad D que depende solo de A y va despues de B en el orden, y un Host
    falso que declara PARTIAL para B: B queda FAILED AGENT_DECLARED_NOT_COMPLETE, ni C ni D tienen turno, y
    el GraphRun cierra con WORK_UNIT_NOT_SUCCEEDED, `workUnitId: b`, `executionCode:
    AGENT_DECLARED_NOT_COMPLETE`. Ni una unidad independiente de B que viene despues se despacha: fail-fast,
    GC-17. (Que `--grafo` salga con 2 es de la etapa 6.) D depende de A porque una unidad sin dependencias
    iria antes que B: `orden_de_ejecucion` ordena por niveles."""
    proy = M72._proyecto(_unidades_abc() + [M64._unidad("d", dependencias=("a",))])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"resultado": M72._informe("PARTIAL")}})
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_b = _eid_de(proy, "b")
    t.igual("GE-E18 el orden es A, B, D, C: D va despues de B", ["a", "b", "d", "c"],
            _leido(proy, graph_run_id)["inicio"]["order"])
    t.igual("GE-E18 B queda FAILED, y el GraphRun cierra FAILED con WORK_UNIT_NOT_SUCCEEDED por B",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "FAILED", "AGENT_DECLARED_NOT_COMPLETE")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E18 ni C ni D tienen turno, ni marca de despacho", ([], [(1, "a"), (2, "b")]),
            (_con_turno(proy, ("c", "d")), _despachos(proy, graph_run_id)))
    t.igual("GE-E18 el Host solo recibio a A y a B", ["a", "b"], [i["workUnitId"] for i in _intervalos(bitacora)])
    t.igual("GE-E18 los nodos: A SATISFIED, B NOT_SATISFIED y los demas NOT_STARTED",
            ["SATISFIED", "NOT_SATISFIED", "NOT_STARTED", "NOT_STARTED"],
            [n["state"] for n in res.get("nodes") or []])
    _valida(t, "GE-E18", proy, graph_run_id)


def test_ge_e19_una_unidad_cancelada_desde_afuera_no_cancela_el_grafo(t):
    """GE-E19 — Con B RUNNING y una cancelacion de su Execution desde otro proceso (la que hace `ejecutar
    <KEY> --cancelar <exe de B>`, por `motor.cancelar`), B queda CANCELLED, C no tiene turno, y el GraphRun
    cierra FAILED con WORK_UNIT_NOT_SUCCEEDED y `executionStatus: CANCELLED`: no CANCELLED, porque nadie
    cancelo el grafo (GC-22). El comando `--cancelar <exe>` como CLI es de la etapa 6."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    marcas = M64._tmp("ge73-marcas-")
    hijos = []

    def cancelar_la_de_b(marca):
        if marca["workUnitId"] == "b":
            hijos.append(_lanzar("cancelar_en_curso", proy, marcas, marca["executionId"]))

    res = _grafo(proy, ganchos={"despues_del_despacho": cancelar_la_de_b})["res"] or {}
    cancelacion = _salida(hijos[0]) if hijos else {"exc": "no se lanzo el cancelador"}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_b = _eid_de(proy, "b")
    t.igual("GE-E19 el cancelador de otro proceso no levanto", None, cancelacion["exc"])
    t.igual("GE-E19 B queda CANCELLED, con el pedido de la cancelacion de su Execution",
            ("CANCELLED", True), (registro.estado(str(proy), CLAVE, eid_b)["estado"],
                                  (M72._carpeta(proy, eid_b) / registro.CANCELACION).is_file()))
    t.igual("GE-E19 el GraphRun cierra FAILED, no CANCELLED, con WORK_UNIT_NOT_SUCCEEDED por B CANCELLED",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "CANCELLED", "CANCELLED"), False),
            (res.get("status"), _causa_de(res), res.get("cancelRequested")))
    t.igual("GE-E19 C no tiene turno ni marca, y no hay marca de cancelacion del grafo",
            ([], [(1, "a"), (2, "b")], False),
            (_con_turno(proy, ("c",)), _despachos(proy, graph_run_id),
             registro.cancelada(str(proy), CLAVE, graph_run_id)))
    t.igual("GE-E19 el Host recibio a A y a B, y no a C", ["a", "b"],
            [i["workUnitId"] for i in _intervalos(bitacora)])
    _valida(t, "GE-E19", proy, graph_run_id)


def test_ge_e20_una_unidad_fallida_no_se_reintenta_sola(t):
    """GE-E20 — Con A FAILED bajo F por un `--unidad` anterior, el GraphRun no crea un turno para A y cierra
    con WORK_UNIT_NOT_SUCCEEDED, `dispatched: false`. Despues de un `ejecutar --unidad a` que la deja
    SUCCEEDED, un GraphRun nuevo despacha B y C y termina SUCCEEDED (GD-09, GE-I10)."""
    proy = _proyecto_abc()
    M72._guion(proy, por_unidad={"a": {"resultado": M72._informe("PARTIAL")}})
    fallida = M72._corrida(proy, "a")
    eid_a = _eid(fallida)
    t.igual("GE-E20 A queda FAILED por la ejecucion manual", "FAILED", M72._de(fallida, "status"))
    antes = _bytes_de(proy, eid_a)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E20 el GraphRun cierra FAILED con WORK_UNIT_NOT_SUCCEEDED por A FAILED",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "a", eid_a, "FAILED", "AGENT_DECLARED_NOT_COMPLETE")),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E20 no crea un turno para A, ni una marca de despacho, y el Host no recibe nada",
            ([(1, eid_a)], [], []),
            (M72._turnos(proy, "a"), _despachos(proy, graph_run_id), _invocaciones(bitacora)))
    t.igual("GE-E20 la Execution de A queda identica", antes, _bytes_de(proy, eid_a))
    nodo_a = _nodos(res).get("a") or {}
    t.igual("GE-E20 el nodo A esta NOT_SATISFIED, dispatched: false", ("NOT_SATISFIED", eid_a, False),
            (nodo_a.get("state"), nodo_a.get("executionId"), nodo_a.get("dispatched")))
    t.igual("GE-E20 B y C estan NOT_STARTED", ["NOT_STARTED"] * 2,
            [(_nodos(res).get(u) or {}).get("state") for u in ("b", "c")])
    _valida(t, "GE-E20", proy, graph_run_id)

    M72._guion(proy, bitacora=str(bitacora))
    reintento = M72._corrida(proy, "a")
    t.igual("GE-E20 el `--unidad a` de una persona la deja SUCCEEDED en el turno 2", ("SUCCEEDED", 2),
            (M72._de(reintento, "status"), (_ultimo(proy, "a") or {}).get("numero")))
    otro = _grafo(proy)["res"] or {}
    otro_id = otro.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E20 un GraphRun nuevo adopta A, despacha B y C y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "b"), (2, "c")], False),
            (otro.get("status"), _despachos(proy, otro_id), (_nodos(otro).get("a") or {}).get("dispatched")))
    _valida(t, "GE-E20 (despues del reintento)", proy, otro_id)


def test_ge_e21_lo_que_quedo_bajo_otra_huella_no_se_adopta(t):
    """GE-E21 — Con A SUCCEEDED bajo una huella F' de una version anterior del plan, el GraphRun sobre F
    despacha A otra vez, y los archivos de la Execution de F' quedan identicos byte a byte: la identidad del
    plan es su huella (GD-03, GE-I03)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    viejo = _huella_del_plan(proy)
    de_a = M72._corrida(proy, "a")
    eid_viejo = _eid(de_a)
    t.igual("GE-E21 A queda SUCCEEDED bajo la huella vieja", "SUCCEEDED", M72._de(de_a, "status"))
    antes = _bytes_de(proy, eid_viejo)
    _plan_replanificado(proy, "c")
    nueva = _huella_del_plan(proy)
    t.verdadero("GE-E21 el plan se replanifico: otra huella", nueva != viejo)
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E21 el GraphRun, atado a la huella nueva, termina SUCCEEDED", ("SUCCEEDED", nueva),
            (res.get("status"), res.get("planFingerprint")))
    t.igual("GE-E21 despacha A otra vez, y B y C", [(1, "a"), (2, "b"), (3, "c")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E21 los archivos de la Execution de la huella vieja quedan identicos", antes,
            _bytes_de(proy, eid_viejo))
    t.verdadero("GE-E21 y A tiene dos Executions, una por huella, y la nueva no es la vieja",
                _eid_de(proy, "a", nueva) != eid_viejo and _eid_de(proy, "a", viejo) == eid_viejo)
    t.igual("GE-E21 el nodo A es de la Execution nueva, dispatched: true", (_eid_de(proy, "a", nueva), True),
            ((_nodos(res).get("a") or {}).get("executionId"), (_nodos(res).get("a") or {}).get("dispatched")))
    _valida(t, "GE-E21", proy, graph_run_id)


def test_ge_e22_una_falla_bajo_otra_huella_no_cuenta(t):
    """GE-E22 — Con A FAILED bajo F', el GraphRun sobre F despacha A normalmente: la falla de otra huella
    no es de este plan."""
    proy = _proyecto_abc()
    M72._guion(proy, por_unidad={"a": {"resultado": M72._informe("PARTIAL")}})
    t.igual("GE-E22 A queda FAILED bajo la huella vieja", "FAILED",
            M72._de(M72._corrida(proy, "a"), "status"))
    _plan_replanificado(proy, "c")
    M72._guion(proy)
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E22 el GraphRun despacha A, B y C y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "a"), (2, "b"), (3, "c")]),
            (res.get("status"), _despachos(proy, graph_run_id)))
    _valida(t, "GE-E22", proy, graph_run_id)


# -- la huella del plan (GD-16) ------------------------------------------------------------------

def test_ge_e23_un_plan_que_cambia_detiene_el_graphrun(t):
    """GE-E23 — Con un gancho que reescribe el plan, con otro contenido, despues de que A queda SUCCEEDED: B
    no tiene turno bajo ninguna huella, el GraphRun cierra con PLAN_FINGERPRINT_CHANGED, y el archivo del
    plan es el que dejo el gancho, sin cambios del GraphRun (GE-I05, GE-I06)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    dejado = []

    def reescribir():
        _objetivo_cambiado(proy, "c")
        dejado.append(M64._plan_de(proy, CLAVE).read_bytes())

    res = _grafo(proy, ganchos={"despues_del_retorno": _al_retornar("a", reescribir)})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E23 cierra FAILED con PLAN_FINGERPRINT_CHANGED, sin Execution de la causa",
            ("FAILED", "PLAN_FINGERPRINT_CHANGED", None, None, None),
            (res.get("status"), _causa_de(res)[0], _causa_de(res)[2], _causa_de(res)[3],
             _causa_de(res)[4]))
    t.igual("GE-E23 B no tiene turno bajo ninguna huella: el unico turno de la tarea es el de A", 1,
            len(registro.nombradas(str(proy), CLAVE)))
    t.igual("GE-E23 y no hay una marca de despacho para B", [(1, "a")], _despachos(proy, graph_run_id))
    t.igual("GE-E23 el archivo del plan es el que dejo el gancho", dejado[0], M64._plan_de(proy, CLAVE).read_bytes())
    t.igual("GE-E23 el GraphRun sigue atado a la huella de antes, no a la nueva",
            (_leido(proy, graph_run_id)["inicio"]["planFingerprint"], True),
            (res.get("planFingerprint"), res.get("planFingerprint") != _huella_del_plan(proy)))
    t.igual("GE-E23 el Host solo recibio a A", ["a"], [i["workUnitId"] for i in _intervalos(bitacora)])
    _valida(t, "GE-E23", proy, graph_run_id)

    # El paso 7b, solo: el plan cambia despues de crear el GraphRun y antes del primer despacho, donde no hay
    # un 7h de una unidad anterior que lo vea. No hay Execution ni marca de despacho: el conductor ni pide.
    otro = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(otro, bitacora=str(bitacora))
    res = _grafo(otro, ganchos={"despues_de_inicio": lambda gid: _objetivo_cambiado(otro, "c")})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E23 7b: cierra FAILED con PLAN_FINGERPRINT_CHANGED por A, sin despachar nada",
            ("FAILED", ("PLAN_FINGERPRINT_CHANGED", "a", None, None, None), [], [], 0),
            (res.get("status"), _causa_de(res), _despachos(otro, graph_run_id), _invocaciones(bitacora),
             len(registro.nombradas(str(otro), CLAVE))))
    t.igual("GE-E23 7b: ninguna Execution, ni carpeta, bajo ninguna huella", [], M72._carpetas(otro))
    _valida(t, "GE-E23 7b", otro, graph_run_id)


def test_ge_e26_el_mismo_plan_reescrito_no_detiene_el_graphrun(t):
    """GE-E26 — Con un gancho que reescribe el plan con el mismo contenido, otra indentacion y otro orden de
    claves, el GraphRun sigue y termina SUCCEEDED: la huella es del contenido, no de los bytes."""
    proy = _proyecto_abc()
    M72._guion(proy)
    antes = {}

    def reescribir():
        ruta = M64._plan_de(proy, CLAVE)
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        antes["bytes"], antes["huella"] = ruta.read_bytes(), contrato.huella(plan)
        invertido = dict((k, plan[k]) for k in reversed(list(plan)))
        ruta.write_text(json.dumps(invertido, ensure_ascii=False, indent=4), encoding="utf-8",
                        newline="\n")

    res = _grafo(proy, ganchos={"despues_del_retorno": _al_retornar("a", reescribir)})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.verdadero("GE-E26 el gancho reescribio el archivo: otros bytes, la misma huella",
                antes.get("bytes") != M64._plan_de(proy, CLAVE).read_bytes()
                and antes.get("huella") == _huella_del_plan(proy))
    t.igual("GE-E26 el GraphRun sigue y termina SUCCEEDED, con las tres unidades", ("SUCCEEDED", None,
            [(1, "a"), (2, "b"), (3, "c")]),
            (res.get("status"), res.get("error"), _despachos(proy, graph_run_id)))
    _valida(t, "GE-E26", proy, graph_run_id)


def test_ge_e27_un_plan_cortado_a_la_mitad_detiene_el_graphrun(t):
    """GE-E27 — Con un gancho que deja el plan cortado a la mitad despues de A, el GraphRun cierra con
    GRAPH_PLAN_UNREADABLE sin despachar B: `plan.py` no escribe de forma atomica, y relanzar lo resuelve."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    original = _plan_original(proy)

    def cortar():
        M64._plan_de(proy, CLAVE).write_bytes(original[:len(original) // 2])

    res = _grafo(proy, ganchos={"despues_del_retorno": _al_retornar("a", cortar)})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E27 cierra FAILED con GRAPH_PLAN_UNREADABLE, por B", ("FAILED", "GRAPH_PLAN_UNREADABLE", "b"),
            (res.get("status"), _causa_de(res)[0], _causa_de(res)[1]))
    t.igual("GE-E27 B no tiene marca de despacho ni turno, y el Host solo recibio a A",
            ([(1, "a")], 1, ["a"]),
            (_despachos(proy, graph_run_id), len(registro.nombradas(str(proy), CLAVE)),
             [i["workUnitId"] for i in _intervalos(bitacora)]))
    M64._plan_de(proy, CLAVE).write_bytes(original)
    otro = _grafo(proy)["res"] or {}
    t.igual("GE-E27 con el plan entero, relanzar lo resuelve: adopta A y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "b"), (2, "c")]),
            (otro.get("status"), _despachos(proy, otro.get("graphRunId") or "grf_" + "0" * 32)))
    _valida(t, "GE-E27", proy, graph_run_id)


# -- el contrato del resultado y de las marcas (GD-12, GD-22, GD-23) --------------------------------

def _objetos_del_schema(nodo, ruta="$"):
    """[(ruta, schema)] de cada objeto con `properties` del schema, `$defs` incluidos."""
    salida = []
    if isinstance(nodo, dict):
        if isinstance(nodo.get("properties"), dict):
            salida.append((ruta, nodo))
        for clave, valor in nodo.items():
            if clave == "properties":
                for propiedad, sub in valor.items():
                    salida += _objetos_del_schema(sub, "%s.properties.%s" % (ruta, propiedad))
            elif isinstance(valor, dict):
                salida += _objetos_del_schema(valor, "%s.%s" % (ruta, clave))
    return salida


def _dos_graphruns(estado_b="COMPLETE"):
    """Un GraphRun SUCCEEDED (A->B->C) y uno FAILED (B declara PARTIAL): (proy, id, proy, id)."""
    exito = _proyecto_abc()
    M72._guion(exito)
    ok = _grafo(exito)["res"] or {}
    falla = _proyecto_abc()
    M72._guion(falla, por_unidad={"b": {"resultado": M72._informe("PARTIAL")}})
    mal = _grafo(falla)["res"] or {}
    return exito, ok.get("graphRunId") or "grf_" + "0" * 32, falla, mal.get("graphRunId") or "grf_" + "0" * 32


def test_ge_e60_el_resultado_valida_contra_su_schema_y_rechaza_claves_de_mas(t):
    """GE-E60 (el schema y `result.json`) — El `result.json` de un GraphRun valida contra
    `graph-run-result.schema.json` y sus coherencias; el schema pasa `controlar_soporte`, es
    `graph-run-result/1.0`, cierra cada objeto con `additionalProperties: false`, y rechaza claves de mas;
    lo que el schema no puede decir lo dice `validar_resultado` (GD-23). Cada `error.code` es uno de los
    nueve, y el schema lleva los 23 de ExecutionError solo en `executionCode`."""
    esquema = json.loads(SCHEMA_DE_GRAFO.read_text(encoding="utf-8"))
    try:
        M64.ARMADOR.controlar_soporte(esquema)
        soporte = ""
    except Exception as e:                       # noqa: BLE001 - el motivo es el detalle
        soporte = "%s: %s" % (type(e).__name__, e)
    t.igual("GE-E60 el schema pasa controlar_soporte", "", soporte)
    t.igual("GE-E60 es graph-run-result/1.0", ("graph-run-result/1.0", ["graph-run-result/1.0"]),
            (esquema["$id"], esquema["properties"]["schema_version"]["enum"]))
    t.vacio("GE-E60 todo objeto del schema, $defs incluidos, cierra con additionalProperties: false",
            [r for r, n in _objetos_del_schema(esquema) if n.get("additionalProperties") is not False])
    t.igual("GE-E60 la raiz exige todas sus propiedades", sorted(esquema["properties"]),
            sorted(esquema["required"]))
    error = esquema["$defs"]["error"]
    t.igual("GE-E60 el schema nombra los nueve codigos del GraphRun, los mismos de grafo.CODIGOS",
            (list(LOS_NUEVE), list(LOS_NUEVE)), (error["properties"]["code"]["enum"], list(grafo.CODIGOS)))
    t.igual("GE-E60 y executionCode lleva los 23 de ExecutionError, o null: los de contrato.CODIGOS",
            list(contrato.CODIGOS) + [None], error["properties"]["executionCode"]["enum"])
    t.igual("GE-E60 el estado de un nodo es uno de los cinco de 9.2",
            ["SATISFIED", "NOT_SATISFIED", "OPEN", "UNREADABLE", "NOT_STARTED"],
            esquema["$defs"]["nodo"]["properties"]["state"]["enum"])
    t.vacio("GE-E60 el schema no lleva evidence, files, output ni artifact",
            [c for c in ("evidence", "files", "output", "artifact", "agentDeclaredStatus")
             if c in json.dumps(esquema["properties"]) or c in json.dumps(esquema["$defs"])])

    exito, id_exito, falla, id_falla = _dos_graphruns()
    bueno, malo = _valida(t, "GE-E60 SUCCEEDED", exito, id_exito), _valida(t, "GE-E60 FAILED", falla, id_falla)
    inicio_bueno, inicio_malo = _leido(exito, id_exito)["inicio"], _leido(falla, id_falla)["inicio"]
    t.igual("GE-E60 los dos son los que se esperaba: SUCCEEDED y FAILED", ("SUCCEEDED", "FAILED"),
            ((bueno or {}).get("status"), (malo or {}).get("status")))

    def rechazado(base, inicio, cambio):
        doc = copy.deepcopy(base)
        cambio(doc)
        return grafo.validar_resultado(doc, inicio), M64.ARMADOR.validar(doc, esquema)

    def pisa(clave, valor):
        return lambda d: d.update({clave: valor})

    casos = (
        ("una clave de mas en la raiz", malo, inicio_malo, pisa("evidence", {}), True),
        ("una clave de mas en error", malo, inicio_malo, lambda d: d["error"].update(extra=1), True),
        ("una clave de mas en un nodo", bueno, inicio_bueno, lambda d: d["nodes"][0].update(artifact="x"), True),
        ("falta cancelRequested", bueno, inicio_bueno, lambda d: d.pop("cancelRequested"), True),
        ("falta una clave de error", malo, inicio_malo, lambda d: d["error"].pop("executionCode"), True),
        ("un status que no es un terminal", bueno, inicio_bueno, pisa("status", "RUNNING"), True),
        ("una version que no es la 1.0", bueno, inicio_bueno, pisa("schema_version", "graph-run-result/2.0"), True),
        ("un graphRunId que no es grf_ y 32 hexadecimales", bueno, inicio_bueno, pisa("graphRunId", "grf_x"), True),
        ("una huella que no es sha256", bueno, inicio_bueno, pisa("planFingerprint", "x"), True),
        ("una fecha que no es UTC", bueno, inicio_bueno, pisa("endedAt", "ayer"), True),
        ("un codigo que no es de los nueve", malo, inicio_malo, lambda d: d["error"].update(code="PLAN_CHANGED"), True),
        ("un executionCode que no es de ExecutionError", malo, inicio_malo,
         lambda d: d["error"].update(executionCode="GRAPH_INTERRUPTED"), True),
        ("un estado de nodo inventado", bueno, inicio_bueno, lambda d: d["nodes"][0].update(state="DONE"), True),
        ("un turno que no es un entero", bueno, inicio_bueno, lambda d: d["nodes"][0].update(turn="1"), True),
        ("un dispatched que no es booleano", bueno, inicio_bueno, lambda d: d["nodes"][0].update(dispatched=1), True),
        # Lo que el schema no puede decir: solo `validar_resultado`.
        ("SUCCEEDED con un nodo que no esta SATISFIED", malo, inicio_malo,
         lambda d: d.update(status="SUCCEEDED", error=None), False),
        ("FAILED sin error", malo, inicio_malo, pisa("error", None), False),
        ("SUCCEEDED con un error", bueno, inicio_bueno,
         pisa("error", dict(malo["error"])), False),
        ("CANCELLED con un error", bueno, inicio_bueno,
         lambda d: d.update(status="CANCELLED", error=dict(malo["error"])), False),
        ("un error cuyo workUnitId no es un nodo", malo, inicio_malo,
         lambda d: d["error"].update(workUnitId="no-es-un-nodo"), False),
        ("nodes en otro orden que `order`", bueno, inicio_bueno, lambda d: d["nodes"].reverse(), False),
        ("nodes sin una unidad de inicio.json", bueno, inicio_bueno, lambda d: d["nodes"].pop(), False),
        ("un graphRunId que no es el de su inicio.json", bueno, inicio_bueno,
         pisa("graphRunId", "grf_" + "1" * 32), False),
        ("una huella que no es la de su inicio.json", bueno, inicio_bueno,
         pisa("planFingerprint", "sha256:" + "1" * 64), False),
        ("un detail de 301 caracteres", malo, inicio_malo,
         lambda d: d["error"].update(detail="x" * 301), False),
        ("un detail vacio", malo, inicio_malo, lambda d: d["error"].update(detail="  "), False),
        ("endedAt anterior a startedAt", bueno, inicio_bueno,
         lambda d: d.update(startedAt="2030-01-01T00:00:00Z", endedAt="2029-01-01T00:00:00Z"), False),
    )
    for nombre, base, inicio, cambio, del_schema in casos:
        propios, del_armador = rechazado(base, inicio, cambio)
        t.verdadero("GE-E60 se rechaza %s" % nombre, bool(propios))
        t.verdadero("GE-E60 %s: %s" % (nombre, "el schema lo rechaza, tambien directo" if del_schema
                                       else "el schema solo no lo dice, y valida_resultado si"),
                    bool(del_armador) == del_schema)
    t.igual("GE-E60 un documento que no es un objeto no levanta, y se rechaza", True,
            bool(grafo.validar_resultado([], inicio_bueno)) and bool(grafo.validar_resultado(None, None)))

    plan = M64._leer_json(M64._plan_de(exito, CLAVE))
    inicio = _leido(exito, id_exito)["inicio"]
    t.igual("GE-E60 inicio.json tiene exactamente sus claves, y cada nodo las suyas",
            (sorted(registro.CLAVES_DE_INICIO), [sorted(registro.CLAVES_DE_NODO)] * 3),
            (sorted(inicio), [sorted(n) for n in inicio["nodes"]]))
    t.igual("GE-E60 inicio.json trae los workUnitId y las dependencies del plan",
            [(u["id"], u["dependencies"]) for u in plan["workUnits"]],
            [(n["workUnitId"], n["dependencies"]) for n in inicio["nodes"]])
    t.igual("GE-E60 y trae quien lo pidio, la huella y el plan", (PIDE, _huella_del_plan(exito),
            plan["meta"]["plan_id"], plan["meta"]["plan_version"]),
            (inicio["requestedBy"], inicio["planFingerprint"], inicio["planId"], inicio["planVersion"]))
    marcas = registro.despachos(str(exito), CLAVE, id_exito)
    t.igual("GE-E60 las marcas de despacho tienen exactamente sus claves y son consecutivas desde 001",
            ([1, 2, 3], [sorted(registro.CLAVES_DE_DESPACHO)] * 3),
            ([n for n, _, _ in marcas], [sorted(m) for _, m, _ in marcas]))
    t.igual("GE-E60 un GraphRun sin cancelacion no tiene cancelacion.json", False,
            registro.cancelada(str(exito), CLAVE, id_exito))
    t.igual("GE-E60 y los archivos del GraphRun son exactamente los de GD-12",
            sorted(["%s/%s/inicio.json" % (GRAFOS, id_exito), "%s/%s/result.json" % (GRAFOS, id_exito),
                    "%s/vivo.lock" % GRAFOS]
                   + ["%s/%s/despachos/%03d.json" % (GRAFOS, id_exito, n) for n in (1, 2, 3)]),
            _de_grafos(exito))
    t.igual("GE-E60 los nueve codigos son los que el conductor define", sorted(LOS_NUEVE),
            sorted(grafo.CODIGOS))


def test_ge_e64_las_guardas_de_task_4_siguen_en_pie_con_grafo_py(t):
    """GE-E64 — ME-E47 y E-41 siguen verdes con `grafo.py`: sin modulos de concurrencia, sin SDK de modelos
    ni LangGraph, sin `subprocess`, sin `proceso.lanzar`, y trece subcomandos. ME-E46 (solo `registro.py`
    escribe en disco) y ME-E29 tambien: se corren aca, con el conductor ya en `bin/ejecucion/`. EX-E50 (nadie
    nombra un campo de reintento) esta en GE-E17 para este archivo y en la suite 65 para todos."""
    t.verdadero("GE-E64 grafo.py esta entre los fuentes de bin/ejecucion/ que ME-E47 recorre",
                GRAFO_PY in M72._py(M72.BIN) and GRAFO_PY in M72._py(M72.EJECUCION))
    importados = M72._importados(GRAFO_PY)
    t.vacio("GE-E64 grafo.py no importa concurrencia", sorted(importados & set(M72.PROHIBIDOS)))
    t.vacio("GE-E64 ni un SDK de modelos, LangChain o LangGraph", sorted(importados & set(M72.MODELOS)))
    t.vacio("GE-E64 ni subprocess", sorted(importados & {"subprocess"}))
    t.vacio("GE-E64 y no llama a proceso.lanzar ni a nada de proceso",
            [n for _, n in _llamadas_de(GRAFO_PY) if n.startswith("proceso.")])
    t.vacio("GE-E64 ni importa el modulo del Host ni el que lanza procesos",
            sorted(importados & {"proceso", "host_claude_code"}))
    t.vacio("GE-E64 y no escribe en disco (ME-E46): solo registro.py lo hace", M72._escribe(GRAFO_PY))
    t.igual("GE-E64 dev-harness.py sigue con trece subcomandos", 13, len(M72._subcomandos() or []))
    r = M72._resultados()
    for nombre in ("test_me_e47_una_corrida_por_invocacion", "test_me_e46_que_escribe_cada_modulo",
                   "test_me_e29_nadie_interpreta_texto"):
        try:
            getattr(M72, nombre)(r)
            caida = None
        except Exception as e:                   # noqa: BLE001 - el motivo es el detalle
            caida = "%s: %s" % (type(e).__name__, e)
        t.igual("GE-E64 %s corre con grafo.py y no levanta" % nombre, None, caida)
    t.igual("GE-E64 y tienen sus aserciones: 8 de ME-E47, 9 de ME-E46 y 9 de ME-E29", 26, len(r.filas))
    t.vacio("GE-E64 ninguna de las tres cae", ["%s %s" % (n, d) for _, n, ok, d in r.filas if not ok])


def test_ge_e68_el_resultado_no_copia_nada_de_las_executions(t):
    """GE-E68 — Ningun `result.json` de GraphRun tiene claves `evidence`, `files`, `output` ni `artifact`, y
    su `detail` no contiene el texto que el Host falso puso en el `artifact` ni en el `detail` de una
    Execution (GE-I23). Tampoco lo tiene ninguna marca del GraphRun."""
    proy = _proyecto_abc()
    M72._guion(proy, resultado=M72._informe("COMPLETE", "# TEXTO-DEL-ARTIFACT-DE-A\n"),
               por_unidad={"b": {"sin_json": "TEXTO-DEL-HOST-DE-B", "stderr": "TEXTO-DEL-STDERR-DE-B",
                                 "salida": 3}})
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_b = _eid_de(proy, "b")
    de_b = registro.estado(str(proy), CLAVE, eid_b)["resultado"] or {}
    detalle_de_b = (de_b.get("error") or {}).get("detail") or ""
    textos = ("TEXTO-DEL-ARTIFACT-DE-A", "TEXTO-DEL-HOST-DE-B", "TEXTO-DEL-STDERR-DE-B")
    t.igual("GE-E68 B termina FAILED por el Host, y el GraphRun lo cierra con WORK_UNIT_NOT_SUCCEEDED",
            ("FAILED", "WORK_UNIT_NOT_SUCCEEDED", "b"),
            (res.get("status"), _causa_de(res)[0], _causa_de(res)[1]))
    t.verdadero("GE-E68 el detail de la Execution de B si trae texto del Host: el control no es vacuo",
                bool(detalle_de_b) and any(x in detalle_de_b for x in textos))
    t.verdadero("GE-E68 y el artifact de A esta en su output.md", "TEXTO-DEL-ARTIFACT-DE-A" in
                (M72._carpeta(proy, _eid_de(proy, "a")) / registro.OUTPUT).read_text(encoding="utf-8"))

    def claves(nodo):
        if isinstance(nodo, dict):
            return set(nodo) | set().union(*[claves(v) for v in nodo.values()] or [set()])
        if isinstance(nodo, list):
            return set().union(*[claves(v) for v in nodo] or [set()])
        return set()

    t.vacio("GE-E68 el resultado no tiene claves evidence, files, output ni artifact, a ningun nivel",
            sorted(claves(res) & {"evidence", "files", "output", "artifact", "agentDeclaredStatus",
                                  "host", "changes"}))
    archivos = [p for p in (M72._ejecuciones(proy) / CLAVE / GRAFOS).rglob("*")
                if p.is_file() and p.name != registro.VIVO]
    t.igual("GE-E68 hay cuatro archivos del GraphRun que mirar: inicio, dos marcas y el resultado", 4,
            len(archivos))
    for texto in textos + (detalle_de_b,):
        t.vacio("GE-E68 ningun archivo del GraphRun contiene %r" % texto[:40],
                [p.name for p in archivos if texto in p.read_text(encoding="utf-8")])
    t.no_contiene("GE-E68 el detail del error no copia el de la Execution", detalle_de_b,
                  (res.get("error") or {}).get("detail"))
    _valida(t, "GE-E68", proy, graph_run_id)


def test_ge_e69_requestedby_es_el_del_graphrun(t):
    """GE-E69 — Con `--pedido-por ana`, cada request que despacha el GraphRun tiene `requestedBy: ana`, y
    tambien `inicio.json` y el resultado (GE-I24). Lo que pide una persona con un secreto se redacta con
    el catalogo, igual en la request y en `inicio.json`. (La opcion `--pedido-por` como CLI es de la etapa 6.)"""
    proy = _proyecto_abc()
    M72._guion(proy)
    res = _grafo(proy, pedido_por="ana")["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E69 cada request de A, B y C tiene requestedBy ana", ["ana"] * 3,
            [_request_de(proy, _eid_de(proy, u))["requestedBy"] for u in ("a", "b", "c")])
    t.igual("GE-E69 inicio.json y el resultado tambien", ("ana", "ana"),
            (_leido(proy, graph_run_id)["inicio"]["requestedBy"], res.get("requestedBy")))
    _valida(t, "GE-E69", proy, graph_run_id)

    otro = _proyecto_abc()
    M72._guion(otro)
    con_secreto = "ana " + M72.SECRETO
    res = _grafo(otro, pedido_por=con_secreto)["res"] or {}
    por = _leido(otro, res.get("graphRunId") or "grf_" + "0" * 32)["inicio"]["requestedBy"]
    t.no_contiene("GE-E69 con un secreto en `pedido_por`, inicio.json no lo lleva", M72.FUGA, por)
    t.igual("GE-E69 y es lo mismo que redacta la request", por,
            _request_de(otro, _eid_de(otro, "a"))["requestedBy"])
    t.no_contiene("GE-E69 ni el resultado", M72.FUGA, json.dumps(res))


# -- las ramas del conductor que no son un escenario de la 5a: GD-04, GD-07, GD-10, GD-11, GD-15 -------

def test_gd07_los_ganchos_son_los_puntos_de_encuentro_de_los_tests(t):
    """GD-07, §24 — Los ganchos corren en este orden: despues de `inicio.json`, despues de cada marca de
    despacho (con la marca escrita y sin turno), despues de cada retorno del motor (con la Execution
    terminal) y antes del terminal (sin `result.json`). Un gancho que el conductor no tiene es un error."""
    proy = M72._proyecto(_unidades_abc()[:2])
    M72._guion(proy)
    orden, visto = [], {}
    graph_run_id = []

    def inicio(gid):
        graph_run_id.append(gid)
        orden.append("inicio")
        visto["inicio"] = (os.path.isfile(str(M72._ejecuciones(proy) / CLAVE / GRAFOS / gid / registro.INICIO)),
                           _despachos(proy, gid))

    def despacho(marca):
        orden.append("despacho " + marca["workUnitId"])
        visto["despacho " + marca["workUnitId"]] = (
            _despachos(proy, graph_run_id[0]), _ultimo(proy, marca["workUnitId"]),
            registro.es(registro.ID, marca["executionId"]))

    def retorno(marca):
        orden.append("retorno " + marca["workUnitId"])
        visto["retorno " + marca["workUnitId"]] = _estado_de(proy, marca["workUnitId"])

    def terminal(gid):
        orden.append("terminal")
        visto["terminal"] = (gid == graph_run_id[0], _leido(proy, gid)["estado"])

    res = _grafo(proy, ganchos={"despues_de_inicio": inicio, "despues_del_despacho": despacho,
                                "despues_del_retorno": retorno, "antes_del_terminal": terminal})["res"] or {}
    t.igual("GD-07 el orden de los ganchos", ["inicio", "despacho a", "retorno a", "despacho b",
                                              "retorno b", "terminal"], orden)
    t.igual("GD-07 despues de inicio.json el GraphRun existe y no tiene marcas", (True, []),
            visto.get("inicio"))
    t.igual("GD-07 despues de la marca de A: la marca esta escrita, A no tiene turno, y el id es exe_",
            ([(1, "a")], None, True), visto.get("despacho a"))
    t.igual("GD-07 despues de la de B: ya hay dos marcas, y B no tiene turno todavia",
            ([(1, "a"), (2, "b")], None, True), visto.get("despacho b"))
    t.igual("GD-07 despues del retorno, cada Execution esta terminal", ("SUCCEEDED", "SUCCEEDED"),
            (visto.get("retorno a"), visto.get("retorno b")))
    t.igual("GD-07 antes del terminal el GraphRun sigue ACTIVE", (True, "ACTIVE"), visto.get("terminal"))
    t.igual("GD-07 y despues termina SUCCEEDED", ("SUCCEEDED", "SUCCEEDED"),
            (res.get("status"), _leido(proy, graph_run_id[0])["estado"]))
    desconocido = _grafo(proy, ganchos={"despues_de_nada": lambda *a: None})
    t.verdadero("GD-07 un gancho que el conductor no tiene es un ValueError, sin crear un GraphRun mas",
                (desconocido["exc"] or "").startswith("ValueError") and len(_grafos(proy)) == 1)


def test_gd07_un_error_del_comando_no_crea_nada(t):
    """GD-07 paso 0 — Si fallan la configuracion, el catalogo de secretos, la TaskKey o quien pide, el
    conductor levanta `ErrorDelComando` y no crea nada: ni un GraphRun, ni siquiera el candado."""
    proy = _proyecto_abc()
    M72._guion(proy)
    antes = M72._arbol(proy)
    casos = (("sin catalogo de secretos", {"catalogo": lambda: None}, PIDE, CLAVE),
             ("sin quien pide", {}, "   ", CLAVE),
             ("con una TaskKey que no lo es", {}, PIDE, "no-es-una-clave"),
             ("con una TaskKey con un salto de linea", {}, PIDE, CLAVE + "\n"))
    for nombre, kw, pide, clave in casos:
        try:
            grafo.conducir(str(proy), clave, pide, **kw)
            levanto = None
        except motor.ErrorDelComando as e:
            levanto = str(e)
        t.verdadero("GD-07 %s: ErrorDelComando" % nombre, levanto is not None)
        t.igual("GD-07 %s: no se creo nada" % nombre, antes, M72._arbol(proy))
    (Path(proy) / ".claude" / "harness.config.json").write_text("{no es json", encoding="utf-8")
    corrida = _grafo(proy)
    t.verdadero("GD-07 con una configuracion que no se lee, ErrorDelComando y no cae al default",
                (corrida["exc"] or "").startswith("ErrorDelComando") and corrida["res"] is None
                and corrida["err"] is None)
    t.igual("GD-07 y no se creo nada", antes, M72._arbol(proy))


def _libre(proy):
    """Si el candado de la tarea esta libre: se toma y se suelta."""
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    libre = bool(candado)
    candado.soltar()
    return libre


def test_gd04_el_candado_de_la_tarea_lo_toma_el_conductor(t):
    """GD-04, §14.1 — Sin poder tomar el candado de la tarea el conductor no crea nada y devuelve
    GRAPH_ALREADY_ACTIVE; con el candado, lo suelta al salir, sea cual sea el final: un terminal, un rechazo
    al arrancar o una excepcion que sale sin cerrar (el GraphRun queda ACTIVE, y lo cerrara quien tome el
    candado). Los dos procesos que se disputan el candado son de la etapa 5b (GE-E28, GE-E29)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    candado = registro.CandadoDeTarea(str(proy), CLAVE)
    ocupado = _grafo(proy)
    candado.soltar()
    t.igual("GD-04 con el candado tomado: no empieza, con GRAPH_ALREADY_ACTIVE", (None, None,
            "GRAPH_ALREADY_ACTIVE"), (ocupado["exc"], ocupado["res"], (ocupado["err"] or {}).get("code")))
    _nada_creado(t, "GD-04 con el candado tomado:", proy)
    t.contiene("GD-04 el detail del rechazo dice que el candado esta tomado", "candado", ocupado["err"]["detail"])
    t.verdadero("GD-04 y el candado de la tarea queda libre despues", _libre(proy))

    res = _grafo(proy)["res"] or {}
    t.igual("GD-04 con el candado libre, el GraphRun termina SUCCEEDED, y suelta el candado",
            ("SUCCEEDED", True), (res.get("status"), _libre(proy)))
    t.igual("GD-04 un rechazo al arrancar tambien lo suelta", (True, True),
            (lambda: (M64._plan_de(proy, CLAVE).unlink(), _grafo(proy)["err"] is not None, _libre(proy))[1:])())

    otro = _proyecto_abc()
    M72._guion(otro)

    def explota(gid):
        raise RuntimeError("un bug del gancho, que no es Ctrl-C")

    corrida = _grafo(otro, ganchos={"despues_de_inicio": explota})
    t.verdadero("GD-04 una excepcion que no es Ctrl-C sale del conductor", (corrida["exc"] or "").startswith(
        "RuntimeError") and corrida["res"] is None)
    t.igual("GD-04 sin cerrar: el GraphRun queda ACTIVE, sin result.json, sin disfrazar el bug",
            (1, [_grafos(otro)[0]], [None]), (len(_grafos(otro)), registro.activos(str(otro), CLAVE),
                                              [_leido(otro, g)["resultado"] for g in _grafos(otro)]))
    t.verdadero("GD-04 y el candado esta libre", _libre(otro))
    t.igual("GD-04 no despacho nada", [], M72._carpetas(otro))


def test_gd05_el_terminal_se_escribe_una_vez_y_gana_el_primero(t):
    """GD-05, GD-04 — El `result.json` se escribe una sola vez: si ya hay uno cuando el conductor cierra,
    gana el primero, y el conductor devuelve ese sin pisarlo (como `motor._escribir_resultado`)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    previo = {}

    def primero(gid):
        previo.update({"graphRunId": gid, "taskKey": CLAVE, "status": "CANCELLED", "primero": True})
        registro.escribir_terminal(str(proy), CLAVE, gid, previo)

    res = _grafo(proy, ganchos={"antes_del_terminal": primero})["res"]
    graph_run_id = previo.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GD-05 el conductor devuelve el terminal que ya estaba", previo, res)
    t.igual("GD-05 y result.json es ese, sin pisar", previo, _leido(proy, graph_run_id)["resultado"])


def test_gd05_la_regla_de_cierre(t):
    """GD-05 — Quien cierra aplica la regla en este orden: todos los nodos SATISFIED es SUCCEEDED, haya o no
    marca de cancelacion; con la marca es CANCELLED; si no, FAILED con el codigo de la causa. Una cancelacion
    que llega con todo terminado deja SUCCEEDED con `cancelRequested: true` (§17.3, GC-23)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    res = _grafo(proy, ganchos={"antes_del_terminal": lambda gid: registro.marcar_cancelacion(
        str(proy), CLAVE, gid, PIDE)})["res"] or {}
    t.igual("GD-05 todo SATISFIED y la marca de cancelacion: SUCCEEDED, con cancelRequested: true",
            ("SUCCEEDED", None, True), (res.get("status"), res.get("error"), res.get("cancelRequested")))
    _valida(t, "GD-05 SUCCEEDED con la marca", proy, res.get("graphRunId") or "grf_" + "0" * 32)

    otro = _proyecto_abc()
    M72._guion(otro, por_unidad={"b": {"resultado": M72._informe("PARTIAL")}})
    res = _grafo(otro, ganchos={"despues_del_retorno": _al_retornar(
        "b", lambda: registro.marcar_cancelacion(str(otro), CLAVE, _grafos(otro)[0], PIDE))})["res"] or {}
    t.igual("GD-05 una unidad fallida y la marca de cancelacion: CANCELLED, sin error", ("CANCELLED", None, True),
            (res.get("status"), res.get("error"), res.get("cancelRequested")))
    _valida(t, "GD-05 CANCELLED", otro, res.get("graphRunId") or "grf_" + "0" * 32)


def test_gd11_el_conductor_mira_la_marca_de_cancelacion_antes_de_despachar(t):
    """GD-11, §17.1 (la mitad del conductor de GE-E46 y GE-E48; quien cancela, en la 5b) — El conductor mira
    la marca antes de cada despacho (7a) y otra vez despues de escribir la marca de despacho y antes de
    llamar al motor (7f). Si esta, no llama al motor y cierra CANCELLED, con `cancelRequested: true`: no se
    inventa una Execution CANCELLED."""
    def con_marca(gancho, nombre):
        proy = _proyecto_abc()
        bitacora = _ruta_de_bitacora()
        M72._guion(proy, bitacora=str(bitacora))
        marca = lambda gid: registro.marcar_cancelacion(str(proy), CLAVE, gid, PIDE)  # noqa: E731
        ganchos = {"despues_de_inicio": marca} if gancho == "7a inicial" else {
            "despues_del_retorno": _al_retornar("a", lambda: marca(_grafos(proy)[0]))} \
            if gancho == "7a" else {"despues_del_despacho": lambda m: marca(_grafos(proy)[0])
                                    if m["workUnitId"] == "b" else None}
        res = _grafo(proy, ganchos=ganchos)["res"] or {}
        t.igual("GD-11 %s: cierra CANCELLED, sin error y con cancelRequested: true" % nombre,
                ("CANCELLED", None, True), (res.get("status"), res.get("error"), res.get("cancelRequested")))
        _valida(t, "GD-11 %s" % nombre, proy, res.get("graphRunId") or "grf_" + "0" * 32)
        return proy, res, [i["workUnitId"] for i in _intervalos(bitacora)]

    proy, res, host = con_marca("7a inicial", "con la marca antes del primer despacho (7a)")
    t.igual("GD-11 7a inicial: ni marca de despacho, ni Execution, ni Host", ([], [], []),
            (_despachos(proy, res["graphRunId"]), M72._carpetas(proy), host))
    proy, res, host = con_marca("7a", "con la marca despues de A (7a de B)")
    t.igual("GD-11 7a de B: A quedo SUCCEEDED y B no se despacho: una marca, una Execution, un Host",
            ([(1, "a")], 1, ["a"], ["SATISFIED", "NOT_STARTED", "NOT_STARTED"]),
            (_despachos(proy, res["graphRunId"]), len(M72._carpetas(proy)), host,
             [n["state"] for n in res["nodes"]]))
    proy, res, host = con_marca("7f", "con la marca despues de la de B y antes del motor (7f)")
    t.igual("GD-11 7f: B tiene su marca de despacho pero ninguna Execution ni turno, y el Host no la recibio",
            ([(1, "a"), (2, "b")], [], ["a"], ["SATISFIED", "NOT_STARTED", "NOT_STARTED"]),
            (_despachos(proy, res["graphRunId"]), _con_turno(proy, ("b", "c")), host,
             [n["state"] for n in res["nodes"]]))
    t.igual("GD-11 7f: ninguna Execution propia queda abierta, y la marca de B no la nombra ningun turno",
            [], [p for p in registro.propias(str(proy), CLAVE, res["graphRunId"])
                 if p["estado"] in registro.ABIERTOS or p["workUnitId"] == "b"])


def test_gd10_ctrl_c_en_el_conductor_cierra_y_deja_salir_la_interrupcion(t):
    """GD-10, §16.3 (en proceso; la mitad con el Host que muere desde afuera de GE-E44, en la 5b) — Un
    `KeyboardInterrupt` en el conductor cierra el GraphRun por la regla de cierre, suelta el candado y deja
    salir la interrupcion: GRAPH_INTERRUPTED si no esta todo satisfecho, y no hay otro despacho (GE-I21).
    Con todo satisfecho, SUCCEEDED: no disfraza lo que ya llego a termino."""
    def interrumpido(unidad):
        proy = _proyecto_abc()
        bitacora = _ruta_de_bitacora()
        M72._guion(proy, bitacora=str(bitacora))

        def ctrl_c():
            raise KeyboardInterrupt

        try:
            grafo.conducir(str(proy), CLAVE, PIDE, ganchos={
                "despues_del_retorno": _al_retornar(unidad, ctrl_c)})
            levanto = False
        except KeyboardInterrupt:
            levanto = True
        return proy, levanto, [i["workUnitId"] for i in _intervalos(bitacora)]

    proy, levanto, host = interrumpido("a")
    graph_run_id = _grafos(proy)[0]
    res = _valida(t, "GD-10 Ctrl-C despues de A", proy, graph_run_id) or {}
    t.igual("GD-10 la interrupcion sale, y el GraphRun queda FAILED con GRAPH_INTERRUPTED", (True, "FAILED",
            "GRAPH_INTERRUPTED"), (levanto, res.get("status"), (res.get("error") or {}).get("code")))
    t.igual("GD-10 sin despacho de B: una marca, un turno, una invocacion", ([(1, "a")], 1, ["a"]),
            (_despachos(proy, graph_run_id), len(registro.nombradas(str(proy), CLAVE)), host))
    t.igual("GD-10 el candado esta libre, y ningun GraphRun queda ACTIVE", (True, []),
            (_libre(proy), registro.activos(str(proy), CLAVE)))
    proy, levanto, _ = interrumpido("c")
    res = _valida(t, "GD-10 Ctrl-C despues de C", proy, _grafos(proy)[0]) or {}
    t.igual("GD-10 con las tres SUCCEEDED, la interrupcion sale y el GraphRun cierra SUCCEEDED, sin error",
            (True, "SUCCEEDED", None), (levanto, res.get("status"), res.get("error")))


def test_gd10_un_error_del_comando_del_motor_es_dispatch_failed(t):
    """GD-10, §16.3 (en proceso; GE-E45 en la 5b) — Un `ErrorDelComando` del motor no se lee como «no hay
    Execution»: el conductor deriva por el `executionId` preasignado y cierra con DISPATCH_FAILED, con ese id
    aunque ningun turno lo nombre, y con su estado derivado si uno lo nombra (GE-I22). El texto del error no
    se copia."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    real = registro.crear

    def sin_disco(*a, **k):
        raise OSError("TEXTO-DEL-DISCO-QUE-NO-SE-COPIA")

    registro.crear = sin_disco
    try:
        res = _grafo(proy)["res"] or {}
    finally:
        registro.crear = real
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    exe = (registro.despachos(str(proy), CLAVE, graph_run_id)[0][1] or {}).get("executionId")
    t.igual("GD-10 con registro.crear fallando antes del turno: DISPATCH_FAILED con el executionId de la "
            "marca, sin estado ni codigo", ("FAILED", ("DISPATCH_FAILED", "a", exe, None, None)),
            (res.get("status"), _causa_de(res)))
    t.verdadero("GD-10 ningun turno nombra ese id, y la carpeta de la Execution no quedo",
                exe is not None and exe not in [e for _, _, e, _ in registro.nombradas(str(proy), CLAVE)]
                and M72._carpetas(proy) == [] and _invocaciones(bitacora) == [])
    t.no_contiene("GD-10 el detail no copia el texto del error", "TEXTO-DEL-DISCO", (res.get("error") or {}).get("detail"))
    _valida(t, "GD-10 DISPATCH_FAILED antes del turno", proy, graph_run_id)

    otro = _proyecto_abc()
    M72._guion(otro)
    real_resultado = motor._escribir_resultado

    def explota(carpeta, resultado, request):
        raise motor.ErrorDelComando("TEXTO-DEL-MOTOR-QUE-NO-SE-COPIA")

    motor._escribir_resultado = explota
    try:
        res = _grafo(otro)["res"] or {}
    finally:
        motor._escribir_resultado = real_resultado
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_a = _eid_de(otro, "a")
    t.igual("GD-10 con un error del comando despues de publicar: DISPATCH_FAILED con la Execution y su "
            "estado derivado", ("FAILED", ("DISPATCH_FAILED", "a", eid_a, "RUNNING", None)),
            (res.get("status"), _causa_de(res)))
    t.verdadero("GD-10 esa Execution tiene turno: es la de la marca", eid_a == registro.despachos(
        str(otro), CLAVE, graph_run_id)[0][1]["executionId"])
    t.no_contiene("GD-10 el detail no copia el texto del error", "TEXTO-DEL-MOTOR", (res.get("error") or {}).get("detail"))
    t.igual("GD-10 sin otro despacho", [(1, "a")], _despachos(otro, graph_run_id))
    _valida(t, "GD-10 DISPATCH_FAILED despues de publicar", otro, graph_run_id)


def test_gd15_una_execution_abierta_o_ilegible_detiene_al_conductor(t):
    """GD-15, GD-06, §15.4 (la parte en proceso de GE-E31 a GE-E34; las que exigen un proceso vivo, GE-E30,
    GE-E31, GE-E32, GE-E35 y GE-E71, son de la 5b) — Una Execution abierta o ilegible de la TaskKey, de
    cualquier clave, observada antes del despacho (7c o 7d), cierra con TASK_EXECUTION_OPEN, nombrandola: el
    conductor no la cancela, no la espera y no la toma como propia. Su `detail` trae el comando que la
    cancela."""
    def abierta(unidad_abierta):
        proy = M72._proyecto(M72._unidades("a", "x"))
        bitacora = _ruta_de_bitacora()
        M72._guion(proy, bitacora=str(bitacora))
        request = _requested_sin_motor(proy, unidad_abierta)
        res = _grafo(proy)["res"] or {}
        return proy, request["executionId"], res, bitacora

    # Una REQUESTED sin motor de otra unidad (R2): se ve en 7d.
    proy, exe, res, bitacora = abierta("x")
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GD-15 7d: TASK_EXECUTION_OPEN por A, con la Execution de X, REQUESTED",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", exe, "REQUESTED", None)),
            (res.get("status"), _causa_de(res)))
    t.contiene("GD-15 7d: el detail trae el comando para cancelarla", "ejecutar %s --cancelar %s" % (CLAVE, exe),
               (res.get("error") or {}).get("detail"))
    t.igual("GD-15 7d: ni marca de despacho, ni turno para A, ni Host; la REQUESTED sigue REQUESTED, sin "
            "cancelacion.json", ([], None, [], "REQUESTED", False),
            (_despachos(proy, graph_run_id), _estado_de(proy, "a"), _invocaciones(bitacora),
             registro.estado(str(proy), CLAVE, exe)["estado"],
             (M72._carpeta(proy, exe) / registro.CANCELACION).exists()))
    t.igual("GD-15 7d: el nodo de X esta OPEN y no es propio: dispatched: false",
            ("OPEN", False), tuple((_nodos(res).get("x") or {}).get(c) for c in ("state", "dispatched")))
    _valida(t, "GD-15 7d", proy, graph_run_id)

    # La Execution abierta es la de la misma unidad: se ve en 7c.
    proy, exe, res, _ = abierta("a")
    t.igual("GD-15 7c: la unidad A esta OPEN por su propia REQUESTED: TASK_EXECUTION_OPEN por A",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", exe, "REQUESTED", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GD-15 7c: y no se despacho nada", ([], 1), (_despachos(proy, res.get("graphRunId") or "grf_" + "0" * 32),
                                                        len(M72._carpetas(proy))))
    _valida(t, "GD-15 7c", proy, res.get("graphRunId") or "grf_" + "0" * 32)

    # Una ilegible: su result.json no valida.
    proy = M72._proyecto(M72._unidades("a", "x"))
    M72._guion(proy)
    request = _requested_sin_motor(proy, "x")
    (M72._carpeta(proy, request["executionId"]) / registro.RESULT).write_text("no es un resultado",
                                                                              encoding="utf-8")
    res = _grafo(proy)["res"] or {}
    t.igual("GD-15 una ilegible cuenta como abierta: TASK_EXECUTION_OPEN con executionStatus ILEGIBLE",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", request["executionId"], "ILEGIBLE", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GD-15 y el nodo de X esta UNREADABLE", "UNREADABLE", (_nodos(res).get("x") or {}).get("state"))
    _valida(t, "GD-15 ilegible", proy, res.get("graphRunId") or "grf_" + "0" * 32)


# =============================================================================================
# 5b: exclusividad, recuperacion y cancelacion (GD-10, GD-11, GD-14, GD-15; secciones 14 a 17)
# =============================================================================================
#
# Los conductores que se cortan, se paran o corren a la par son procesos hijos del sistema operativo (modo
# `conducir` del script de hijos), y los cortes son `os._exit` en un gancho: ningun crash se simula con un
# mock en memoria, ni hay hilos. Despues de un corte, el conductor siguiente corre en este proceso, que no
# es el que murio. Lo que nombra a `ejecutar --grafo` o `--cancelar grf_...` como comando (la salida 0 o 2,
# `--json`) es de la etapa 6: aca se mira lo que devuelve la funcion y lo que deja en disco.

OTRA = "GCBA-73"


def _esperar_marca(marcas, nombre, limite=90):
    return M72._esperar(lambda: (Path(marcas) / nombre).exists(), limite)


def _dejar_marca(marcas, nombre):
    (Path(marcas) / nombre).write_text("1", encoding="utf-8")


def _conductor(proy, marcas, **plan):
    """El conductor en otro proceso: {"ganchos": {nombre: accion}, "antes_del_motor": accion,
    "encuentro": bool}. Una accion es {"unidad", "marca", "esperar", "esperar_cuantas", "ctrl_c", "morir"}."""
    return _lanzar("conducir", proy, marcas, json.dumps(plan))


def _esperar_libre(proy, carpetas=()):
    """Espera a que el sistema operativo suelte los candados de un proceso que acaba de morir (el de la tarea y
    el de vida de las Executions que se le pasen): en Windows los suelta cuando puede, y despues de un corte lo
    primero que hace el conductor siguiente es tomarlos."""
    carpetas = list(carpetas)
    return M72._esperar(lambda: _libre(proy) and all(
        registro.candado_libre(str(c)) is not False for c in carpetas), 15)


def _cortado(t, ide, proy, ganchos, **plan):
    """Un conductor en otro proceso que muere con `os._exit` en un gancho: las marcas, y lo que devolvio
    (nada: murio sin cerrar el GraphRun). Vuelve cuando el sistema ya solto sus candados."""
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, ganchos=ganchos, **plan)
    salida = _salida(hijo)
    t.igual("%s el conductor murio en el gancho con `os._exit`, sin devolver nada ni cerrar" % ide,
            (77, None), (hijo.returncode, salida.get("res")))
    t.verdadero("%s y el sistema solto el candado de la tarea y los de vida de lo que dejo" % ide, _esperar_libre(
        proy, M72._ejecuciones(proy).glob(CLAVE + "/exe_*")))
    return marcas


def _foto_de_grafo(proy, graph_run_id):
    """{ruta: sha256} de lo que hay en la carpeta de un GraphRun: para ver que nadie lo reabre."""
    base = M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id
    return dict((p.relative_to(base).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(base.rglob("*")) if p.is_file())


def _cerrado_por_el_siguiente(t, ide, proy, graph_run_id, antes, estado="FAILED",
                              codigo="GRAPH_INTERRUPTED"):
    """El GraphRun cortado lo cerro quien tomo el candado despues, y nadie lo reanudo (GD-10, GE-I16): su
    `result.json` es lo unico que se agrego, valida, y todo lo que ya tenia quedo identico byte a byte."""
    ahora = _foto_de_grafo(proy, graph_run_id)
    t.igual("%s el GraphRun cortado solo gano su result.json: nadie lo reanudo" % ide,
            ["result.json"], sorted(set(ahora) - set(antes)))
    t.verdadero("%s y lo que ya tenia quedo identico byte a byte" % ide,
                all(ahora.get(r) == h for r, h in antes.items()))
    doc = _valida(t, ide, proy, graph_run_id) or {}
    t.igual("%s lo cerro como huerfano: status y codigo" % ide, (estado, codigo),
            (doc.get("status"), (doc.get("error") or {}).get("code")))
    return doc


def _con_otra_tarea(proy, unidad="z"):
    """Una segunda TaskKey en el mismo proyecto, con su contexto y su plan de una unidad."""
    proy = Path(proy)
    M64._json(proy / ".claude" / "contextos" / (OTRA + ".json"), M64._contexto(OTRA, True))
    M64._json(proy / "prop-2.json", M64._propuesta([M64._unidad(unidad)]))
    codigo, _, error = M64._cli(["plan", OTRA, "--proyecto", proy, "--propuesta", proy / "prop-2.json"])
    if codigo != 0:
        raise AssertionError("plan --propuesta de %s salio %s: %s" % (OTRA, codigo, error[-300:]))


def _manual(proy, unidad, clave=CLAVE):
    """`ejecutar <KEY> --unidad <w>` en otro proceso: el hijo, que se espera con `_salida`."""
    return _lanzar("ejecutar", proy, M64._tmp("ge73-marcas-"), unidad, clave=clave)


def _running_de(proy, unidad):
    """Espera a que la Execution manual de la unidad este RUNNING (entrega y Host lanzado), y devuelve su
    carpeta."""
    M72._esperar(lambda: M72._corriendo_de(proy, unidad) is not None)
    return M72._corriendo_de(proy, unidad)


def _bitacoras(bitacora):
    return [i["workUnitId"] for i in _intervalos(bitacora)]


# -- exclusividad: un conductor por tarea (GD-14, §14) ----------------------------------------------

def test_ge_e28_dos_conductores_solo_uno_tiene_el_candado(t):
    """GE-E28 — Dos procesos del sistema operativo corren el conductor sobre la misma TaskKey, con un punto de
    encuentro antes de tomar el candado: queda exactamente un GraphRun; el otro devuelve GRAPH_ALREADY_ACTIVE
    sin crear nada (que `--grafo` salga con 2 es de la etapa 6); cada unidad tiene exactamente una Execution, y
    el Host recibe tantas invocaciones como unidades. El que tomo el candado lo sostiene hasta que el otro
    intento, para que no corran uno despues del otro."""
    proy = M72._proyecto(_unidades_abc()[:2])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    espera = {"esperar_cuantas": ["intento.", 2]}
    hijos = [_conductor(proy, marcas, encuentro=True, ganchos={"despues_de_inicio": espera})
             for _ in range(2)]
    salidas = [_salida(h) for h in hijos]
    ganador = [s for s in salidas if s.get("res")]
    perdedor = [s for s in salidas if s.get("err")]

    t.igual("GE-E28 el encuentro fue real: los dos llegaron antes del candado y los dos lo intentaron",
            (2, 2), (len([n for n in _marcas(marcas) if n.startswith("listo.")]),
                     len([n for n in _marcas(marcas) if n.startswith("intento.")])))
    t.igual("GE-E28 ninguno levanto", [None, None], [s.get("exc") for s in salidas])
    t.igual("GE-E28 uno devuelve el resultado y el otro un rechazo: ni dos GraphRuns ni dos rechazos", (1, 1),
            (len(ganador), len(perdedor)))
    t.igual("GE-E28 el que perdio devuelve GRAPH_ALREADY_ACTIVE y ningun resultado",
            ("GRAPH_ALREADY_ACTIVE", None),
            ((perdedor[0]["err"] if perdedor else {}).get("code"), (perdedor[0]["res"] if perdedor else 0)))
    res = ganador[0]["res"] if ganador else {}
    t.igual("GE-E28 el que gano termina SUCCEEDED", "SUCCEEDED", res.get("status"))
    t.igual("GE-E28 queda exactamente un GraphRun, el del que gano, y ninguna carpeta grf_ sin inicio.json",
            ([res.get("graphRunId")], []), (_grafos(proy), registro.residuos_de_grafos(str(proy), CLAVE)))
    t.igual("GE-E28 cada unidad tiene exactamente una Execution y un turno", [(1, _eid_de(proy, "a"))],
            M72._turnos(proy, "a"))
    t.igual("GE-E28 la otra unidad tambien, y no hay otras carpetas", ([(1, _eid_de(proy, "b"))], 2),
            (M72._turnos(proy, "b"), len(M72._carpetas(proy))))
    t.igual("GE-E28 el Host recibe tantas invocaciones como unidades: una por cada una", ["a", "b"],
            _bitacoras(bitacora))
    _valida(t, "GE-E28", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e29_veinte_veces_dos_conductores_a_la_par(t):
    """GE-E29 — Lo mismo, veinte veces, sin punto de encuentro: en cada vuelta, a lo sumo un GraphRun sin
    terminal en todo momento (se mira desde este proceso mientras los dos corren), una Execution por unidad y
    un turno por clave. Los dos pueden salir bien, uno despues del otro: el segundo adopta lo que dejo el
    primero y no crea ninguna Execution; o el segundo no entra, con GRAPH_ALREADY_ACTIVE."""
    base = M72._proyecto(_unidades_abc()[:2])
    maximo_general = 0
    for vuelta in range(20):
        ide = "GE-E29 vuelta %d" % vuelta
        proy = M64._copia(base, "ge73-vuelta-")
        bitacora = _ruta_de_bitacora("vuelta-%d" % vuelta)
        M72._guion(proy, bitacora=str(bitacora))
        marcas = M64._tmp("ge73-marcas-")
        hijos = [_conductor(proy, marcas) for _ in range(2)]
        maximo = 0
        while any(h.poll() is None for h in hijos):
            maximo = max(maximo, len(registro.activos(str(proy), CLAVE)))
            time.sleep(0.01)
        salidas = [_salida(h) for h in hijos]
        maximo_general = max(maximo_general, maximo)
        resultados = [s["res"] for s in salidas if s.get("res")]
        rechazos = [s["err"]["code"] for s in salidas if s.get("err")]
        grafos = _grafos(proy)

        t.verdadero("%s a lo sumo un GraphRun sin terminal en todo momento" % ide, maximo <= 1)
        t.igual("%s ninguno levanto, y cada uno devolvio un resultado o un GRAPH_ALREADY_ACTIVE" % ide,
                ([None, None], True), ([s.get("exc") for s in salidas],
                                       all(c == "GRAPH_ALREADY_ACTIVE" for c in rechazos)))
        t.verdadero("%s al menos uno termino SUCCEEDED, y todos los resultados lo son" % ide,
                    resultados and all(r["status"] == "SUCCEEDED" for r in resultados))
        t.igual("%s un GraphRun por resultado, todos con terminal, y ninguna carpeta grf_ sin inicio.json" % ide,
                (len(resultados), [], []),
                (len(grafos), registro.activos(str(proy), CLAVE),
                 registro.residuos_de_grafos(str(proy), CLAVE)))
        t.igual("%s una Execution por unidad, un turno por clave, y el Host recibe una invocacion por unidad"
                % ide, ([1, 1], 2, ["a", "b"]),
                ([len(M72._turnos(proy, u)) for u in ("a", "b")], len(M72._carpetas(proy)),
                 _bitacoras(bitacora)))
    t.verdadero("GE-E29 las veinte vueltas corrieron, y en ninguna hubo dos GraphRuns sin terminal",
                maximo_general <= 1)


def test_ge_e30_una_manual_de_la_misma_unidad_en_vuelo(t):
    """GE-E30 — Con un `ejecutar --unidad b` corriendo en otro proceso (candado de vida tomado) cuando el
    GraphRun llega a B: el GraphRun no crea turno para B, cierra con TASK_EXECUTION_OPEN y el `executionId`
    de la manual, y la manual termina con su propio resultado, sin `cancelacion.json`. La manual arranca
    cuando A termino, en el gancho, y el GraphRun no la espera, no la cancela y no la toma como propia: no le
    escribe una marca de despacho a B (7c, antes de 7e)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 4}})
    manual = []

    def arrancar_la_de_b(marca):
        if marca["workUnitId"] == "a":
            manual.append(_manual(proy, "b"))
            _running_de(proy, "b")

    res = _grafo(proy, ganchos={"despues_del_retorno": arrancar_la_de_b})["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    carpeta = M72._corriendo_de(proy, "b")
    eid_manual = carpeta.name if carpeta is not None else "exe_" + "0" * 32
    t.igual("GE-E30 el GraphRun cierra FAILED con TASK_EXECUTION_OPEN por B y la Execution de la manual, RUNNING",
            ("FAILED", ("TASK_EXECUTION_OPEN", "b", eid_manual, "RUNNING", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E30 no crea turno para B: tiene el de la manual, y ninguna marca de despacho es de B",
            ([(1, eid_manual)], [(1, "a")]), (M72._turnos(proy, "b"), _despachos(proy, graph_run_id)))
    t.igual("GE-E30 el nodo de B es de la manual: OPEN, dispatched: false, y C no tiene turno",
            ("OPEN", eid_manual, False, None),
            (lambda n: (n.get("state"), n.get("executionId"), n.get("dispatched"), _ultimo(proy, "c")))(
                _nodos(res).get("b") or {}))
    sal_manual = _salida(manual[0]) if manual else {"exc": "no se lanzo la manual"}
    t.igual("GE-E30 la manual termina con su propio resultado, SUCCEEDED", (None, "SUCCEEDED"),
            (sal_manual.get("exc"), (sal_manual.get("res") or {}).get("status")))
    t.verdadero("GE-E30 sin cancelacion.json en la Execution de la manual",
                not (M72._carpeta(proy, eid_manual) / registro.CANCELACION).exists())
    t.igual("GE-E30 el Host recibio a A y a la manual de B, y a nadie mas", ["a", "b"], _bitacoras(bitacora))
    _valida(t, "GE-E30", proy, graph_run_id)


def test_ge_e31_una_manual_running_de_otra_unidad_detiene_al_grafo(t):
    """GE-E31 — Con una Execution manual RUNNING de otra unidad de la misma TaskKey, el GraphRun cierra con
    TASK_EXECUTION_OPEN sin ninguna marca de despacho (7d, el chequeo preventivo). No la cancela: la manual
    termina con su propio resultado."""
    proy = M72._proyecto(M72._unidades("a", "x"))
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"x": {"dormir": 4}})
    manual = _manual(proy, "x")
    carpeta = _running_de(proy, "x")
    eid_x = carpeta.name if carpeta is not None else "exe_" + "0" * 32
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E31 la manual de X estaba RUNNING cuando el GraphRun la miro", "RUNNING",
            registro.estado(str(proy), CLAVE, eid_x)["estado"] if carpeta is not None else None)
    t.igual("GE-E31 el GraphRun cierra FAILED con TASK_EXECUTION_OPEN, por A, nombrando a X RUNNING",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", eid_x, "RUNNING", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E31 sin ninguna marca de despacho, y A sin turno", ([], None),
            (_despachos(proy, graph_run_id), _ultimo(proy, "a")))
    sal = _salida(manual)
    t.igual("GE-E31 la manual de X termina con su propio resultado, SUCCEEDED, sin cancelacion.json",
            (None, "SUCCEEDED", False),
            (sal.get("exc"), (sal.get("res") or {}).get("status"),
             (M72._carpeta(proy, eid_x) / registro.CANCELACION).exists()))
    t.igual("GE-E31 el Host recibio solo a la manual de X", ["x"], _bitacoras(bitacora))
    t.igual("GE-E31 el nodo de X esta OPEN y no es propio: dispatched: false", ("OPEN", False),
            tuple((_nodos(res).get("x") or {}).get(c) for c in ("state", "dispatched")))
    _valida(t, "GE-E31", proy, graph_run_id)


def test_ge_e32_una_manual_de_la_misma_clave_gana_el_turno(t):
    """GE-E32 — Con un gancho, despues de la marca de despacho de B y antes del motor, que corre un
    `ejecutar --unidad b` completo en otro proceso: B tiene exactamente una Execution, la de la manual; el
    `executionId` de la marca del GraphRun no lo nombra ningun turno; y el GraphRun sigue con C si la manual
    quedo SUCCEEDED, o cierra con TASK_EXECUTION_OPEN si sigue abierta (7h). Nunca hay dos entregas de la misma
    clave."""
    def con_la_manual(nombre, dormir):
        proy = _proyecto_abc()
        bitacora = _ruta_de_bitacora()
        M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": dormir}} if dormir else {})
        manual = []

        def correr_la_manual(marca):
            if marca["workUnitId"] == "b":
                manual.append(_manual(proy, "b"))
                if dormir:
                    _running_de(proy, "b")
                else:
                    manual.append(_salida(manual[0]))

        res = _grafo(proy, ganchos={"despues_del_despacho": correr_la_manual})["res"] or {}
        graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
        marca_b = [m for _, m, _ in registro.despachos(str(proy), CLAVE, graph_run_id)
                   if m and m["workUnitId"] == "b"]
        exe_marca = marca_b[0]["executionId"] if marca_b else "exe_" + "0" * 32
        turnos_de_b = M72._turnos(proy, "b")
        t.igual("GE-E32 %s: B tiene exactamente una Execution, la de la manual, y la marca del GraphRun no la "
                "nombra ningun turno" % nombre, (1, True),
                (len(turnos_de_b), exe_marca not in [e for _, _, e, _ in registro.nombradas(str(proy), CLAVE)]))
        t.igual("GE-E32 %s: el nodo de B es de la manual, no del GraphRun: dispatched: false" % nombre, False,
                (_nodos(res).get("b") or {}).get("dispatched"))
        _valida(t, "GE-E32 %s" % nombre, proy, graph_run_id)
        return proy, res, graph_run_id, manual, bitacora

    proy, res, graph_run_id, manual, bitacora = con_la_manual("la manual termino SUCCEEDED", 0)
    t.igual("GE-E32 la manual termino SUCCEEDED, y el GraphRun sigue con C y termina SUCCEEDED",
            ("SUCCEEDED", "SUCCEEDED", "SATISFIED", True),
            ((manual[1].get("res") or {}).get("status"), res.get("status"),
             (_nodos(res).get("b") or {}).get("state"), (_nodos(res).get("c") or {}).get("dispatched")))
    t.igual("GE-E32 el Host recibio una invocacion por unidad: la de B es la de la manual", ["a", "b", "c"],
            _bitacoras(bitacora))

    proy, res, graph_run_id, manual, bitacora = con_la_manual("la manual sigue abierta", 4)
    eid_manual = M72._turnos(proy, "b")[0][1] or "exe_" + "0" * 32
    t.igual("GE-E32 la manual sigue abierta: el GraphRun cierra FAILED con TASK_EXECUTION_OPEN por B, "
            "nombrandola RUNNING", ("FAILED", ("TASK_EXECUTION_OPEN", "b", eid_manual, "RUNNING", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E32 C no tiene turno, y el Host recibio solo a A y a la manual de B", (None, ["a", "b"]),
            (_ultimo(proy, "c"), _bitacoras(bitacora)))
    sal = _salida(manual[0])
    t.igual("GE-E32 la manual termina con su propio resultado, sin cancelacion.json", ("SUCCEEDED", False),
            ((sal.get("res") or {}).get("status"), (M72._carpeta(proy, eid_manual) / registro.CANCELACION).exists()))


def test_ge_e33_una_requested_sin_motor_detiene_al_grafo(t):
    """GE-E33 — Con una REQUESTED sin motor en la TaskKey (R2), el GraphRun cierra con TASK_EXECUTION_OPEN, su
    `detail` trae `ejecutar <KEY> --cancelar <exe>`, y la REQUESTED sigue REQUESTED: el GraphRun no la
    cancela. (La Execution de otra unidad la ve 7d: antes de despachar nada.)"""
    proy = M72._proyecto(M72._unidades("a", "x"))
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    request = _requested_sin_motor(proy, "x")
    eid = request["executionId"]
    antes = _bytes_de(proy, eid)
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E33 cierra FAILED con TASK_EXECUTION_OPEN por A, nombrando a la REQUESTED",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", eid, "REQUESTED", None)),
            (res.get("status"), _causa_de(res)))
    t.contiene("GE-E33 el detail trae el comando que la cancela", "ejecutar %s --cancelar %s" % (CLAVE, eid),
               (res.get("error") or {}).get("detail"))
    t.igual("GE-E33 la REQUESTED sigue REQUESTED, sin cancelacion.json y sin un byte cambiado",
            ("REQUESTED", False, antes),
            (registro.estado(str(proy), CLAVE, eid)["estado"],
             (M72._carpeta(proy, eid) / registro.CANCELACION).exists(), _bytes_de(proy, eid)))
    t.igual("GE-E33 ni marca de despacho, ni turno para A, ni Host", ([], None, []),
            (_despachos(proy, graph_run_id), _ultimo(proy, "a"), _invocaciones(bitacora)))
    _valida(t, "GE-E33", proy, graph_run_id)


def test_ge_e34_una_execution_ilegible_detiene_al_grafo(t):
    """GE-E34 — Con una Execution de la TaskKey cuyo `result.json` no valida, el GraphRun cierra con
    TASK_EXECUTION_OPEN y `executionStatus: ILEGIBLE`: una ilegible cuenta como abierta, y no se cancela."""
    proy = M72._proyecto(M72._unidades("a", "x"))
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    request = _requested_sin_motor(proy, "x")
    eid = request["executionId"]
    (M72._carpeta(proy, eid) / registro.RESULT).write_text("no es un resultado", encoding="utf-8")
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E34 cierra FAILED con TASK_EXECUTION_OPEN por A, nombrando a la ilegible",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", eid, "ILEGIBLE", None)),
            (res.get("status"), _causa_de(res)))
    t.igual("GE-E34 ni marca de despacho ni Host, y la ilegible quedo como estaba, sin pedido de cancelar",
            ([], [], False),
            (_despachos(proy, graph_run_id), _invocaciones(bitacora),
             (M72._carpeta(proy, eid) / registro.CANCELACION).exists()))
    _valida(t, "GE-E34", proy, graph_run_id)


def test_ge_e35_una_running_de_otra_taskkey_no_detiene_al_grafo(t):
    """GE-E35 — Con una Execution RUNNING de OTRA TaskKey del mismo proyecto, el GraphRun corre y termina
    SUCCEEDED: el chequeo de 7d mira la TaskKey, no el proyecto entero (GD-06)."""
    proy = _proyecto_abc()
    _con_otra_tarea(proy, "z")
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"z": {"dormir": 5}})
    otra = _manual(proy, "z", clave=OTRA)
    corriendo = M72._esperar(lambda: any(
        (c / registro.ENTREGA).is_file() and (c / registro.PROCESO).is_file()
        for c in (M72._ejecuciones(proy) / OTRA).glob("exe_*")))
    t.verdadero("GE-E35 la Execution de la otra TaskKey esta RUNNING cuando el GraphRun arranca", corriendo)
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E35 el GraphRun corre y termina SUCCEEDED, sin error", ("SUCCEEDED", None),
            (res.get("status"), res.get("error")))
    t.igual("GE-E35 despacho las tres unidades", [(1, "a"), (2, "b"), (3, "c")], _despachos(proy, graph_run_id))
    sal = _salida(otra)
    t.igual("GE-E35 y la otra TaskKey termina con su propio resultado", (None, "SUCCEEDED"),
            (sal.get("exc"), (sal.get("res") or {}).get("status")))
    t.igual("GE-E35 el Host recibio a las tres unidades del GraphRun y a la de la otra tarea",
            ["a", "b", "c", "z"], sorted(_bitacoras(bitacora)))
    _valida(t, "GE-E35", proy, graph_run_id)


# -- la carrera residual con una manual de otra unidad (GD-06, GD-15, §15.4, GE-I31) --------------------

def _evidencia_de(proy, unidad):
    """(state, paths) de la evidencia de cambios de la Execution de la unidad, de su result.json."""
    cambios = ((registro.estado(str(proy), CLAVE, _eid_de(proy, unidad))["resultado"] or {})
               .get("evidence") or {}).get("changes") or {}
    return cambios.get("state"), [f["path"] for f in cambios.get("files") or []]


def test_ge_e71_la_carrera_residual_con_una_manual_de_otra_unidad(t):
    """GE-E71 — Plan con B y X independientes (orden b, x), en un proyecto en git como los de la suite 72. En
    el gancho posterior a la marca de despacho de B (ya superado el chequeo 7d), otro proceso del sistema
    operativo corre `ejecutar --unidad x` con un Host falso que duerme, y el gancho vuelve cuando X tiene
    `entrega.json`. El conductor sigue y despacha B. Los intervalos de B y de X en la bitacora se solapan; la
    unica marca de despacho que existe antes del result.json de B es la 001, que nombra a B, y ninguna marca
    nombra a X; X no tiene cancelacion.json y no termina REJECTED; B y X tienen un turno cada una. Sobre la
    evidencia: ninguna atribuye cambios de la otra, y toda evidencia que detecta a la otra por la regla de
    Task 4 (`registro.otras_entregadas`) queda CHANGES_UNATTRIBUTABLE con `files: []`, aunque B quede SUCCEEDED;
    el escenario NO exige simetria, porque Task 4 no la garantiza (15.4). Despues del terminal de B, dos
    variantes que elige el gancho posterior al retorno: (i) con X todavia RUNNING, el GraphRun cierra con
    TASK_EXECUTION_OPEN nombrando a X, sin marca de despacho para x, y X termina despues con su resultado;
    (ii) dejando que X termine SUCCEEDED antes de seguir, el nodo x queda SATISFIED con `dispatched: false`, el
    GraphRun termina SUCCEEDED y el Host recibe dos invocaciones, una por unidad."""
    def la_carrera(esperar_a_x):
        proy = M72._proyecto(M72._unidades("b", "x"))
        bitacora = _ruta_de_bitacora()
        M72._guion(proy, bitacora=str(bitacora), por_unidad={
            "b": {"dormir": 1.5, "cambios": [{"ruta": "src/b.py", "contenido": "B = 1\n"}]},
            "x": {"dormir": 8, "cambios": [{"ruta": "src/x.py", "contenido": "X = 1\n"}]}})
        visto = {}
        manual = []
        graph_run_id = []

        def arrancar_x(marca):
            if marca["workUnitId"] == "b":
                graph_run_id.append(_grafos(proy)[0])
                visto["marcas_al_arrancar"] = _despachos(proy, graph_run_id[0])
                manual.append(_manual(proy, "x"))
                visto["x_corriendo"] = _running_de(proy, "x") is not None

        def despues_de_b(marca):
            if marca["workUnitId"] == "b":
                visto["marcas_con_b_terminal"] = _despachos(proy, graph_run_id[0])
                carpeta_x = M72._corriendo_de(proy, "x")
                visto["x_al_retornar_b"] = registro.estado(str(proy), CLAVE, carpeta_x.name)["estado"] \
                    if carpeta_x is not None else None
                if esperar_a_x:
                    visto["x_termino"] = M72._esperar(lambda: registro.estado(
                        str(proy), CLAVE, carpeta_x.name)["estado"] == "SUCCEEDED")

        res = _grafo(proy, ganchos={"despues_del_despacho": arrancar_x,
                                    "despues_del_retorno": despues_de_b})["res"] or {}
        sal_x = _salida(manual[0]) if manual else {"exc": "no se lanzo la manual"}
        return proy, bitacora, visto, res, sal_x

    def mirar(t, ide, proy, bitacora, visto, res, sal_x):
        graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
        eid_b, eid_x = _eid_de(proy, "b"), _eid_de(proy, "x")
        por_unidad = dict((i["workUnitId"], i) for i in _invocaciones(bitacora))
        t.verdadero("%s la manual de X estaba RUNNING cuando el conductor despacho B" % ide,
                    visto.get("x_corriendo") is True)
        t.verdadero("%s los intervalos de B y de X en la bitacora se solapan: las dos estuvieron RUNNING a la vez"
                    % ide, len(por_unidad) == 2 and all(i["fin"] is not None for i in por_unidad.values())
                    and _solapadas(por_unidad["b"], por_unidad["x"]))
        t.igual("%s la unica marca antes del result.json de B es la 001, que nombra a B" % ide, [(1, "b")],
                visto.get("marcas_con_b_terminal"))
        t.igual("%s y la 001 ya estaba cuando el gancho arranco a X" % ide, [(1, "b")],
                visto.get("marcas_al_arrancar"))
        t.verdadero("%s ninguna marca nombra el executionId de X" % ide, eid_x not in [
            (m or {}).get("executionId") for _, m, _ in registro.despachos(str(proy), CLAVE, graph_run_id)])
        t.igual("%s X no tiene cancelacion.json y termina con su propio resultado, no REJECTED"
                % ide, (False, None, "SUCCEEDED"),
                ((M72._carpeta(proy, eid_x) / registro.CANCELACION).exists(), sal_x.get("exc"),
                 (sal_x.get("res") or {}).get("status")))
        t.igual("%s la clave de B y la de X tienen un turno cada una, y la de B es del GraphRun" % ide,
                ([(1, eid_b)], [(1, eid_x)], [eid_b]),
                (M72._turnos(proy, "b"), M72._turnos(proy, "x"),
                 [p["executionId"] for p in registro.propias(str(proy), CLAVE, graph_run_id)
                  if p["workUnitId"] == "b"]))
        t.igual("%s B queda SUCCEEDED, aunque su evidencia no se pueda atribuir" % ide, "SUCCEEDED",
                registro.estado(str(proy), CLAVE, eid_b)["estado"])
        for unidad, otra in (("b", "x"), ("x", "b")):
            eid = eid_b if unidad == "b" else eid_x
            detecta = registro.otras_entregadas(str(proy), eid, registro.entregada_en(
                M72._carpeta(proy, eid)))
            estado, archivos = _evidencia_de(proy, unidad)
            t.verdadero("%s ninguna atribuye a %s cambios de %s" % (ide, unidad, otra),
                        "src/%s.py" % otra not in archivos)
            t.verdadero("%s la evidencia de %s que detecta a la otra por la regla de Task 4 es "
                        "CHANGES_UNATTRIBUTABLE con files: []" % (ide, unidad),
                        not detecta or (estado, archivos) == ("CHANGES_UNATTRIBUTABLE", []))
            t.verdadero("%s y en ningun caso %s recibe una atribucion que no pueda sostener: o no atribuye "
                        "nada, o solo lo suyo" % (ide, unidad),
                        estado == "CHANGES_UNATTRIBUTABLE" and archivos == []
                        or all(a == "src/%s.py" % unidad for a in archivos))
        t.igual("%s B detecta a X, que seguia RUNNING al cerrar: su evidencia es CHANGES_UNATTRIBUTABLE, sin "
                "archivos" % ide, ("CHANGES_UNATTRIBUTABLE", []), _evidencia_de(proy, "b"))
        _valida(t, ide, proy, graph_run_id)
        return graph_run_id, eid_x

    proy, bitacora, visto, res, sal_x = la_carrera(esperar_a_x=False)
    graph_run_id, eid_x = mirar(t, "GE-E71 (i)", proy, bitacora, visto, res, sal_x)
    t.igual("GE-E71 (i) con X todavia RUNNING cuando vuelve B, el GraphRun cierra FAILED con TASK_EXECUTION_OPEN "
            "por X, nombrandola", ("RUNNING", "FAILED", ("TASK_EXECUTION_OPEN", "x", eid_x, "RUNNING", None)),
            (visto.get("x_al_retornar_b"), res.get("status"), _causa_de(res)))
    t.igual("GE-E71 (i) sin marca de despacho para x: solo la 001, de B", [(1, "b")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E71 (i) el Host recibio dos invocaciones: B, y la manual de X", ["b", "x"],
            sorted(_bitacoras(bitacora)))
    t.igual("GE-E71 (i) el nodo de X esta OPEN, y no lo despacho este GraphRun",
            ("OPEN", False), ((_nodos(res).get("x") or {}).get("state"), (_nodos(res).get("x") or {}).get("dispatched")))

    proy, bitacora, visto, res, sal_x = la_carrera(esperar_a_x=True)
    graph_run_id, eid_x = mirar(t, "GE-E71 (ii)", proy, bitacora, visto, res, sal_x)
    t.igual("GE-E71 (ii) dejando que X termine SUCCEEDED antes de seguir: el GraphRun termina SUCCEEDED, sin "
            "error", (True, "SUCCEEDED", None), (visto.get("x_termino"), res.get("status"), res.get("error")))
    nodo_x = _nodos(res).get("x") or {}
    t.igual("GE-E71 (ii) el nodo x queda SATISFIED, con la Execution de la manual y dispatched: false",
            ("SATISFIED", eid_x, False), (nodo_x.get("state"), nodo_x.get("executionId"), nodo_x.get("dispatched")))
    t.igual("GE-E71 (ii) sin marca de despacho para x: solo la 001, de B", [(1, "b")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E71 (ii) el Host recibe dos invocaciones en total, una por unidad", ["b", "x"],
            sorted(_bitacoras(bitacora)))


# -- recuperacion: las ventanas de corte (GD-10, §16) ------------------------------------------------
#
# Cada corte es un proceso hijo que corre el conductor y muere con `os._exit` en un gancho. Despues se corre
# otro conductor (el `--grafo` siguiente) en este proceso: cierra al huerfano, no vuelve a despachar nada de lo
# ya entregado, y no reanuda (GE-I16).

def test_ge_e36_g1_corte_despues_de_inicio_json(t):
    """GE-E36 — G1: corte despues de `inicio.json` y antes del primer despacho. El conductor siguiente deja el
    GraphRun cortado FAILED con GRAPH_INTERRUPTED, crea otro, y ese termina SUCCEEDED con una Execution por
    unidad."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E36", proy, {"despues_de_inicio": {"morir": True}})
    (cortado,) = _grafos(proy)
    t.igual("GE-E36 en disco: el GraphRun cortado esta ACTIVE, sin marcas ni Executions, y el candado libre",
            ("ACTIVE", [], [], True),
            (_leido(proy, cortado)["estado"], _despachos(proy, cortado), M72._carpetas(proy), _libre(proy)))
    antes = _foto_de_grafo(proy, cortado)

    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.verdadero("GE-E36 el siguiente es otro GraphRun, y termina SUCCEEDED", graph_run_id != cortado
                and res.get("status") == "SUCCEEDED")
    _cerrado_por_el_siguiente(t, "GE-E36", proy, cortado, antes)
    t.igual("GE-E36 el nuevo dispatcho las tres, una Execution por unidad", [(1, "a"), (2, "b"), (3, "c")],
            _despachos(proy, graph_run_id))
    t.igual("GE-E36 un turno por clave, tres carpetas, y el Host recibio una invocacion por unidad",
            ([1, 1, 1], 3, ["a", "b", "c"]),
            ([len(M72._turnos(proy, u)) for u in ("a", "b", "c")], len(M72._carpetas(proy)),
             _bitacoras(bitacora)))
    t.igual("GE-E36 ningun GraphRun queda ACTIVE", [], registro.activos(str(proy), CLAVE))
    _valida(t, "GE-E36 el nuevo", proy, graph_run_id)


def test_ge_e37_g2_corte_con_la_marca_de_despacho_y_sin_motor(t):
    """GE-E37 — G2: corte despues de la marca de despacho de A y antes del motor. Ningun turno nombra el
    `executionId` de esa marca; el GraphRun siguiente despacha A con otro id, una sola vez, y el Host recibe una
    invocacion por unidad en total."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E37", proy, {"despues_del_despacho": {"unidad": "a", "morir": True}})
    (cortado,) = _grafos(proy)
    exe_huerfano = (registro.despachos(str(proy), CLAVE, cortado)[0][1] or {}).get("executionId")
    t.igual("GE-E37 en disco: la marca 001 de A existe, ningun turno la nombra, y no hay carpeta de Execution",
            ([(1, "a")], False, []),
            (_despachos(proy, cortado), exe_huerfano in [e for _, _, e, _ in registro.nombradas(str(proy), CLAVE)],
             M72._carpetas(proy)))
    antes = _foto_de_grafo(proy, cortado)

    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    _cerrado_por_el_siguiente(t, "GE-E37", proy, cortado, antes)
    t.igual("GE-E37 el siguiente termina SUCCEEDED y despacha A, B y C", ("SUCCEEDED", [(1, "a"), (2, "b"), (3, "c")]),
            (res.get("status"), _despachos(proy, graph_run_id)))
    marca_a = (registro.despachos(str(proy), CLAVE, graph_run_id)[0][1] or {}).get("executionId")
    t.verdadero("GE-E37 despacha A con otro id: el de la marca huerfana no lo nombra ningun turno",
                marca_a != exe_huerfano and exe_huerfano not in
                [e for _, _, e, _ in registro.nombradas(str(proy), CLAVE)])
    t.igual("GE-E37 A se despacha una sola vez: un turno, una Execution por unidad, y una invocacion del Host "
            "por unidad en total", ([(1, marca_a)], 3, ["a", "b", "c"]),
            (M72._turnos(proy, "a"), len(M72._carpetas(proy)), _bitacoras(bitacora)))
    _valida(t, "GE-E37 el nuevo", proy, graph_run_id)


def test_ge_e38_g3a_corte_dentro_de_crear_antes_del_turno(t):
    """GE-E38 — G3a: corte en el gancho `antes_de_reservar` del motor, durante el despacho de A. Queda una
    carpeta `exe_...` sin turno (un residuo previo a la publicacion); A sigue sin turno; el GraphRun siguiente
    despacha A una sola vez y termina SUCCEEDED. El residuo se barre pasados los diez minutos."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E38", proy, {"antes_de_reservar": {"morir": True}})
    (cortado,) = _grafos(proy)
    residuo = registro.residuos(str(proy), CLAVE)
    t.igual("GE-E38 en disco: una carpeta exe_ sin turno, que es la de la marca 001, y A sin turno",
            (1, [(registro.despachos(str(proy), CLAVE, cortado)[0][1] or {}).get("executionId")], None),
            (len(residuo), residuo, _ultimo(proy, "a")))
    antes = _foto_de_grafo(proy, cortado)

    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    _cerrado_por_el_siguiente(t, "GE-E38", proy, cortado, antes)
    t.igual("GE-E38 el siguiente despacha A, B y C, una sola vez cada una, y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "a"), (2, "b"), (3, "c")], [1, 1, 1], ["a", "b", "c"]),
            (res.get("status"), _despachos(proy, graph_run_id),
             [len(M72._turnos(proy, u)) for u in ("a", "b", "c")], _bitacoras(bitacora)))
    t.igual("GE-E38 el residuo sigue ahi, sin turno: es nuevo, y el barrido espera a los diez minutos",
            residuo, registro.residuos(str(proy), CLAVE))
    _envejecer(M72._carpeta(proy, residuo[0]), 700)
    _envejecer(M72._carpeta(proy, residuo[0]) / registro.VIVO, 700)
    t.igual("GE-E38 pasados los diez minutos, la recuperacion lo barre", ([residuo[0]], []),
            (registro.barrer(str(proy), CLAVE), registro.residuos(str(proy), CLAVE)))
    _valida(t, "GE-E38 el nuevo", proy, graph_run_id)


def test_ge_e39_g3b_g4_corte_con_el_turno_y_sin_entrega(t):
    """GE-E39 — G3b y G4: corte en el gancho `antes_de_entregar` del motor, durante A. A queda REQUESTED sin
    motor (R2). El conductor siguiente cierra el GraphRun cortado FAILED GRAPH_INTERRUPTED, nombrando a la
    REQUESTED y el comando que la cancela, y el nuevo cierra con TASK_EXECUTION_OPEN nombrando a A, sin
    cancelarla ni entregarla. Despues de `--cancelar <exe de A>`, otro conductor cierra con
    WORK_UNIT_NOT_SUCCEEDED (A esta CANCELLED); despues de `ejecutar --unidad a`, otro termina SUCCEEDED."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E39", proy, {"antes_de_entregar": {"morir": True}})
    (cortado,) = _grafos(proy)
    eid_a = _eid_de(proy, "a")
    t.igual("GE-E39 en disco: A esta REQUESTED sin motor (candado libre), sin entrega.json", ("REQUESTED", True, False),
            (registro.estado(str(proy), CLAVE, eid_a)["estado"],
             registro.candado_libre(str(M72._carpeta(proy, eid_a))),
             (M72._carpeta(proy, eid_a) / registro.ENTREGA).exists()))
    antes = _foto_de_grafo(proy, cortado)
    antes_de_a = _bytes_de(proy, eid_a)

    segundo = _grafo(proy)["res"] or {}
    doc = _cerrado_por_el_siguiente(t, "GE-E39", proy, cortado, antes)
    t.igual("GE-E39 el cortado nombra a la REQUESTED de A: unidad, Execution y estado",
            ("a", eid_a, "REQUESTED"), tuple((doc.get("error") or {}).get(c) for c in (
                "workUnitId", "executionId", "executionStatus")))
    t.contiene("GE-E39 y su detail trae el comando que la cancela", "ejecutar %s --cancelar %s" % (CLAVE, eid_a),
               (doc.get("error") or {}).get("detail"))
    t.igual("GE-E39 el nuevo cierra FAILED con TASK_EXECUTION_OPEN por A, nombrandola REQUESTED",
            ("FAILED", ("TASK_EXECUTION_OPEN", "a", eid_a, "REQUESTED", None)),
            (segundo.get("status"), _causa_de(segundo)))
    t.igual("GE-E39 sin cancelarla ni entregarla: sigue REQUESTED, sin cancelacion.json y sin un byte cambiado, "
            "y el Host no recibio nada", ("REQUESTED", False, antes_de_a, []),
            (registro.estado(str(proy), CLAVE, eid_a)["estado"],
             (M72._carpeta(proy, eid_a) / registro.CANCELACION).exists(), _bytes_de(proy, eid_a),
             _invocaciones(bitacora)))
    t.igual("GE-E39 el nuevo no despacho nada", [], _despachos(proy, segundo.get("graphRunId") or "grf_" + "0" * 32))

    cancelada = motor.cancelar(str(proy), CLAVE, eid_a, PIDE)
    t.igual("GE-E39 `--cancelar <exe de A>` la deja CANCELLED", "CANCELLED", cancelada["despues"])
    tercero = _grafo(proy)["res"] or {}
    t.igual("GE-E39 otro conductor cierra con WORK_UNIT_NOT_SUCCEEDED: A esta CANCELLED",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "a", eid_a, "CANCELLED", "CANCELLED")),
            (tercero.get("status"), _causa_de(tercero)))

    reintento = M72._corrida(proy, "a")
    t.igual("GE-E39 `ejecutar --unidad a` la deja SUCCEEDED en el turno 2", ("SUCCEEDED", 2),
            (M72._de(reintento, "status"), (_ultimo(proy, "a") or {}).get("numero")))
    cuarto = _grafo(proy)["res"] or {}
    t.igual("GE-E39 otro conductor adopta A, despacha B y C y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "b"), (2, "c")], False),
            (cuarto.get("status"), _despachos(proy, cuarto.get("graphRunId") or "grf_" + "0" * 32),
             (_nodos(cuarto).get("a") or {}).get("dispatched")))
    t.igual("GE-E39 ningun GraphRun queda ACTIVE", [], registro.activos(str(proy), CLAVE))
    for res in (segundo, tercero, cuarto):
        _valida(t, "GE-E39", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e40_g5_el_conductor_muere_con_el_host_de_b_dormido(t):
    """GE-E40 — G5: el proceso del conductor se mata (a la fuerza, sin su arbol) mientras el Host falso de B
    duerme. El conductor siguiente deja B FAILED HOST_INTERRUPTED por la recuperacion de Task 4, cierra el
    GraphRun cortado con GRAPH_INTERRUPTED, y el nuevo cierra con WORK_UNIT_NOT_SUCCEEDED para B sin despachar
    nada: el Host no recibe ninguna invocacion nueva."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas)
    corriendo = _running_de(proy, "b")
    t.verdadero("GE-E40 B esta RUNNING, con su Host dormido, cuando se mata al conductor", corriendo is not None)
    pid_del_host = ((M64._leer_json(corriendo / registro.PROCESO) or {}).get("pid")
                    if corriendo is not None else None)
    M72._matar(hijo.pid)
    hijo.communicate(timeout=60)
    _esperar_libre(proy, [corriendo] if corriendo is not None else [])
    try:
        (cortado,) = _grafos(proy)
        eid_b = _eid_de(proy, "b")
        t.igual("GE-E40 en disco: el GraphRun esta ACTIVE y B RUNNING, con el candado de la tarea libre",
                ("ACTIVE", "RUNNING", True),
                (_leido(proy, cortado)["estado"], registro.estado(str(proy), CLAVE, eid_b)["estado"], _libre(proy)))
        antes = _foto_de_grafo(proy, cortado)
        invocaciones_antes = len(_invocaciones(bitacora))

        res = _grafo(proy)["res"] or {}
        graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
        derivado_b = registro.estado(str(proy), CLAVE, eid_b)
        t.igual("GE-E40 la recuperacion de Task 4 deja B FAILED con HOST_INTERRUPTED",
                ("FAILED", "HOST_INTERRUPTED"),
                (derivado_b["estado"], ((derivado_b["resultado"] or {}).get("error") or {}).get("code")))
        _cerrado_por_el_siguiente(t, "GE-E40", proy, cortado, antes)
        t.igual("GE-E40 el nuevo cierra FAILED con WORK_UNIT_NOT_SUCCEEDED para B, HOST_INTERRUPTED",
                ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "FAILED", "HOST_INTERRUPTED")),
                (res.get("status"), _causa_de(res)))
        t.igual("GE-E40 sin despachar nada: ninguna marca, y el Host no recibe ninguna invocacion nueva",
                ([], invocaciones_antes), (_despachos(proy, graph_run_id), len(_invocaciones(bitacora))))
        t.igual("GE-E40 el Host recibio dos invocaciones en total: A y B", ["a", "b"], _bitacoras(bitacora))
        t.igual("GE-E40 B no se reintento: un solo turno, y C no tiene", ([(1, eid_b)], None),
                (M72._turnos(proy, "b"), _ultimo(proy, "c")))
        _valida(t, "GE-E40 el nuevo", proy, graph_run_id)
    finally:
        M72._terminar(pid_del_host)


def test_ge_e41_g6_corte_con_b_ya_succeeded(t):
    """GE-E41 — G6: corte en el gancho posterior al retorno del motor, con B ya SUCCEEDED. El GraphRun siguiente
    adopta B, despacha solo C, y el Host recibe tres invocaciones en total."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E41", proy, {"despues_del_retorno": {"unidad": "b", "morir": True}})
    (cortado,) = _grafos(proy)
    t.igual("GE-E41 en disco: A y B SUCCEEDED, C sin turno, y el GraphRun ACTIVE",
            ("SUCCEEDED", "SUCCEEDED", None, "ACTIVE"),
            (_estado_de(proy, "a"), _estado_de(proy, "b"), _ultimo(proy, "c"), _leido(proy, cortado)["estado"]))
    antes = _foto_de_grafo(proy, cortado)

    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    _cerrado_por_el_siguiente(t, "GE-E41", proy, cortado, antes)
    t.igual("GE-E41 el siguiente adopta A y B (dispatched: false), despacha solo C y termina SUCCEEDED",
            ("SUCCEEDED", [(1, "c")], [("a", False), ("b", False), ("c", True)]),
            (res.get("status"), _despachos(proy, graph_run_id),
             [(u, (_nodos(res).get(u) or {}).get("dispatched")) for u in ("a", "b", "c")]))
    t.igual("GE-E41 el Host recibe tres invocaciones en total, una por unidad, y cada una tiene un solo turno",
            (["a", "b", "c"], [1, 1, 1]),
            (_bitacoras(bitacora), [len(M72._turnos(proy, u)) for u in ("a", "b", "c")]))
    _valida(t, "GE-E41 el nuevo", proy, graph_run_id)


def test_ge_e42_g7_corte_con_todo_succeeded_y_sin_terminal(t):
    """GE-E42 — G7: corte en el gancho anterior al terminal, con las tres SUCCEEDED. El conductor siguiente cierra
    el GraphRun cortado SUCCEEDED, no GRAPH_INTERRUPTED, y el nuevo termina SUCCEEDED sin despachos."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E42", proy, {"antes_del_terminal": {"morir": True}})
    (cortado,) = _grafos(proy)
    t.igual("GE-E42 en disco: las tres SUCCEEDED, y el GraphRun sin terminal", (["SUCCEEDED"] * 3, "ACTIVE"),
            ([_estado_de(proy, u) for u in ("a", "b", "c")], _leido(proy, cortado)["estado"]))
    antes = _foto_de_grafo(proy, cortado)

    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    doc = _cerrado_por_el_siguiente(t, "GE-E42", proy, cortado, antes, estado="SUCCEEDED", codigo=None)
    t.igual("GE-E42 el cortado cierra SUCCEEDED, no GRAPH_INTERRUPTED: sin error, con los tres nodos SATISFIED "
            "y dispatched: true", (None, ["SATISFIED"] * 3, [True] * 3),
            (doc.get("error"), [n["state"] for n in doc.get("nodes") or []],
             [n["dispatched"] for n in doc.get("nodes") or []]))
    t.igual("GE-E42 el nuevo termina SUCCEEDED sin despachos, y el Host no recibio nada nuevo",
            ("SUCCEEDED", [], ["a", "b", "c"]),
            (res.get("status"), _despachos(proy, graph_run_id), _bitacoras(bitacora)))
    t.igual("GE-E42 sus tres nodos estan adoptados: dispatched: false", [False] * 3,
            [n["dispatched"] for n in res.get("nodes") or []])
    _valida(t, "GE-E42 el nuevo", proy, graph_run_id)


def test_ge_e43_un_conductor_vivo_no_se_cierra_desde_afuera(t):
    """GE-E43 — Con un conductor vivo, detenido en un gancho, otro conductor sale con GRAPH_ALREADY_ACTIVE y un
    `--cancelar grf_...` escribe la marca y no el terminal: el GraphRun vivo no tiene result.json hasta que su
    conductor sigue (GD-10: solo quien tiene el candado cierra). Cuando sigue, ve la marca y cierra CANCELLED."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, ganchos={"despues_del_retorno": {"unidad": "a", "esperar": ["seguir"]}})
    try:
        t.verdadero("GE-E43 el conductor llego al gancho posterior a A", _esperar_marca(marcas, "despues_del_retorno.a"))
        (vivo,) = _grafos(proy)
        antes = _foto_de_grafo(proy, vivo)

        otro = _grafo(proy)
        t.igual("GE-E43 otro conductor sale con GRAPH_ALREADY_ACTIVE, sin resultado y sin levantar",
                (None, None, "GRAPH_ALREADY_ACTIVE"),
                (otro["exc"], otro["res"], (otro["err"] or {}).get("code")))
        t.igual("GE-E43 y no crea nada: el mismo unico GraphRun, ACTIVE, sin un archivo mas", ([vivo], "ACTIVE", antes),
                (_grafos(proy), _leido(proy, vivo)["estado"], _foto_de_grafo(proy, vivo)))
        t.vacio("GE-E43 ni una carpeta grf_ sin inicio.json", registro.residuos_de_grafos(str(proy), CLAVE))

        cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, vivo, PIDE, espera=1.0, intervalo=0.2)
        t.igual("GE-E43 `--cancelar grf_...` escribe la marca, ve al conductor vivo, y el GraphRun sigue ACTIVE",
                ("ACTIVE", True, True, True, False, True),
                (cancelacion["despues"], cancelacion["pedido"], cancelacion["marcaNueva"],
                 cancelacion["conductorVivo"], cancelacion["cerradoAqui"], cancelacion["sigue"]))
        leido = _leido(proy, vivo)
        t.igual("GE-E43 la marca esta escrita y el terminal no: el GraphRun vivo no tiene result.json",
                (True, None, "ACTIVE"), (leido["cancelada"], leido["resultado"], leido["estado"]))
        t.igual("GE-E43 y quien cancelo no toco nada mas: A sigue SUCCEEDED, B sin turno",
                ("SUCCEEDED", None), (_estado_de(proy, "a"), _ultimo(proy, "b")))
    finally:
        _dejar_marca(marcas, "seguir")
    sal = _salida(hijo)
    res = sal.get("res") or {}
    t.igual("GE-E43 cuando su conductor sigue, ve la marca: cierra CANCELLED, con cancelRequested, sin despachar B",
            (None, "CANCELLED", None, True, [(1, "a")]),
            (sal.get("exc"), res.get("status"), res.get("error"), res.get("cancelRequested"),
             _despachos(proy, res.get("graphRunId") or "grf_" + "0" * 32)))
    t.igual("GE-E43 ningun GraphRun queda ACTIVE, y el candado esta libre", ([], True),
            (registro.activos(str(proy), CLAVE), _libre(proy)))
    _valida(t, "GE-E43", proy, res.get("graphRunId") or "grf_" + "0" * 32)


def test_ge_e44_ctrl_c_y_un_host_cortado_desde_afuera(t):
    """GE-E44 — Un `KeyboardInterrupt` levantado en el gancho posterior al retorno del motor, con A SUCCEEDED,
    deja el GraphRun FAILED con GRAPH_INTERRUPTED y sin despacho de B, y la interrupcion sale. Un Host falso
    con `senal: true`, que muere como un Host cortado desde afuera (sale con 143), deja B FAILED
    HOST_INTERRUPTED, y el GraphRun cierra con WORK_UNIT_NOT_SUCCEEDED sin despachar C (GE-I21)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))

    def ctrl_c():
        raise KeyboardInterrupt

    try:
        grafo.conducir(str(proy), CLAVE, PIDE, ganchos={"despues_del_retorno": _al_retornar("a", ctrl_c)})
        salio = False
    except KeyboardInterrupt:
        salio = True
    (graph_run_id,) = _grafos(proy)
    doc = _valida(t, "GE-E44 Ctrl-C", proy, graph_run_id) or {}
    t.igual("GE-E44 la interrupcion sale del conductor, y el GraphRun queda FAILED con GRAPH_INTERRUPTED",
            (True, "FAILED", "GRAPH_INTERRUPTED"),
            (salio, doc.get("status"), (doc.get("error") or {}).get("code")))
    t.igual("GE-E44 sin despacho de B: una marca, un turno, una invocacion, y el candado libre",
            ([(1, "a")], None, ["a"], True),
            (_despachos(proy, graph_run_id), _ultimo(proy, "b"), _bitacoras(bitacora), _libre(proy)))

    otro = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(otro, bitacora=str(bitacora), por_unidad={"b": {"senal": True}})
    res = _grafo(otro)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_b = _eid_de(otro, "b")
    derivado = registro.estado(str(otro), CLAVE, eid_b)
    t.igual("GE-E44 un Host que sale con 143 deja B FAILED con HOST_INTERRUPTED",
            ("FAILED", "HOST_INTERRUPTED"),
            (derivado["estado"], ((derivado["resultado"] or {}).get("error") or {}).get("code")))
    t.igual("GE-E44 el GraphRun cierra FAILED con WORK_UNIT_NOT_SUCCEEDED por B, sin despachar C",
            ("FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "FAILED", "HOST_INTERRUPTED"), None, [(1, "a"), (2, "b")]),
            (res.get("status"), _causa_de(res), _ultimo(otro, "c"), _despachos(otro, graph_run_id)))
    t.igual("GE-E44 el Host recibio a A y a B, y el de B anoto su fin antes de morir", (["a", "b"], True),
            (_bitacoras(bitacora), all(i["fin"] is not None for i in _intervalos(bitacora))))
    _valida(t, "GE-E44 Host cortado", otro, graph_run_id)


def test_ge_e45_un_error_del_comando_cierra_con_dispatch_failed(t):
    """GE-E45 — Con `registro.crear` forzado a fallar con OSError antes del turno, el GraphRun cierra con
    DISPATCH_FAILED y un `executionId` que ningun turno nombra. Con un error del comando forzado despues de
    publicar la Execution, cierra con DISPATCH_FAILED, el `executionId` de esa Execution y su estado derivado:
    un error del comando no se lee como «no hay Execution» (GE-I22)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    real = registro.crear

    def sin_disco(*a, **k):
        raise OSError("TEXTO-DEL-DISCO")

    registro.crear = sin_disco
    try:
        res = _grafo(proy)["res"] or {}
    finally:
        registro.crear = real
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    exe = (registro.despachos(str(proy), CLAVE, graph_run_id)[0][1] or {}).get("executionId")
    t.igual("GE-E45 con registro.crear fallando antes del turno: DISPATCH_FAILED con el executionId de la marca, "
            "sin estado", ("FAILED", ("DISPATCH_FAILED", "a", exe, None, None)), (res.get("status"), _causa_de(res)))
    t.verdadero("GE-E45 ningun turno nombra ese id, no quedo una carpeta, y el Host no recibio nada",
                exe is not None and exe not in [e for _, _, e, _ in registro.nombradas(str(proy), CLAVE)]
                and M72._carpetas(proy) == [] and _invocaciones(bitacora) == [])
    t.no_contiene("GE-E45 el detail no copia el texto del error", "TEXTO-DEL-DISCO", (res.get("error") or {}).get("detail"))
    _valida(t, "GE-E45 antes del turno", proy, graph_run_id)

    otro = _proyecto_abc()
    M72._guion(otro)
    real_resultado = motor._escribir_resultado

    def explota(carpeta, resultado, request):
        raise motor.ErrorDelComando("TEXTO-DEL-MOTOR")

    motor._escribir_resultado = explota
    try:
        res = _grafo(otro)["res"] or {}
    finally:
        motor._escribir_resultado = real_resultado
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_a = _eid_de(otro, "a")
    t.igual("GE-E45 con un error del comando despues de publicar: DISPATCH_FAILED con la Execution y su estado "
            "derivado", ("FAILED", ("DISPATCH_FAILED", "a", eid_a, "RUNNING", None)),
            (res.get("status"), _causa_de(res)))
    t.verdadero("GE-E45 esa Execution tiene turno, es la de la marca, y no se despacho otra",
                eid_a == registro.despachos(str(otro), CLAVE, graph_run_id)[0][1]["executionId"]
                and _despachos(otro, graph_run_id) == [(1, "a")])
    t.no_contiene("GE-E45 el detail no copia el texto del error", "TEXTO-DEL-MOTOR", (res.get("error") or {}).get("detail"))
    _valida(t, "GE-E45 despues de publicar", otro, graph_run_id)


# -- cancelacion: una marca, propagada solo a lo propio (GD-11, §17) ----------------------------------

def _sin_propias_abiertas(proy, graph_run_id):
    """Ninguna Execution del GraphRun queda abierta (REQUESTED o RUNNING)."""
    return [p for p in registro.propias(str(proy), CLAVE, graph_run_id) if p["estado"] in registro.ABIERTOS]


def _cancelador(proy, marcas, graph_run_id, espera, intervalo=0.2):
    """`--cancelar grf_...` en otro proceso, que espera hasta `espera` segundos a un conductor vivo y mira sus
    Executions cada `intervalo`. Deja en `marcas` un `barrido.N` por cada vuelta que mira las propias."""
    return _lanzar("cancelar_grafo", proy, marcas, graph_run_id, str(espera), str(intervalo))


def test_ge_e46_cancelar_con_el_conductor_detenido_despues_de_a(t):
    """GE-E46 — Con el conductor detenido en el gancho posterior a A, `--cancelar grf_...` desde otro proceso
    escribe `cancelacion.json`; al seguir, el conductor no despacha B y cierra CANCELLED, con
    `cancelRequested: true`; A queda identica."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, ganchos={"despues_del_retorno": {"unidad": "a", "esperar": ["seguir"]}})
    try:
        t.verdadero("GE-E46 el conductor llego al gancho posterior a A", _esperar_marca(marcas, "despues_del_retorno.a"))
        (graph_run_id,) = _grafos(proy)
        eid_a = _eid_de(proy, "a")
        a_antes = _bytes_de(proy, eid_a)
        cancelador = _cancelador(proy, M64._tmp("ge73-marcas-"), graph_run_id, 1.0)
        sal_c = _salida(cancelador)
        cancelacion = sal_c.get("res") or {}
        t.igual("GE-E46 `--cancelar` desde otro proceso escribe la marca y no cierra: el conductor sigue vivo",
                (None, True, True, "ACTIVE", True),
                (sal_c.get("exc"), cancelacion.get("marcaNueva"), cancelacion.get("conductorVivo"),
                 cancelacion.get("despues"), cancelacion.get("sigue")))
        pedido = M64._leer_json(M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id / registro.CANCELACION)
        t.igual("GE-E46 cancelacion.json trae las claves cerradas, y quien pidio", (["pedidoEn", "pedidoPor"], PIDE),
                (sorted(pedido), pedido.get("pedidoPor")))
    finally:
        _dejar_marca(marcas, "seguir")
    sal = _salida(hijo)
    res = sal.get("res") or {}
    t.igual("GE-E46 al seguir, el conductor no despacha B y cierra CANCELLED, sin error y con cancelRequested",
            (None, "CANCELLED", None, True, [(1, "a")], None),
            (sal.get("exc"), res.get("status"), res.get("error"), res.get("cancelRequested"),
             _despachos(proy, graph_run_id), _ultimo(proy, "b")))
    t.igual("GE-E46 A queda identica, byte a byte, y el Host solo recibio a A", (a_antes, ["a"]),
            (_bytes_de(proy, eid_a), _bitacoras(bitacora)))
    t.igual("GE-E46 los nodos: A SATISFIED y los otros NOT_STARTED", ["SATISFIED", "NOT_STARTED", "NOT_STARTED"],
            [n["state"] for n in res.get("nodes") or []])
    _valida(t, "GE-E46", proy, graph_run_id)


def test_ge_e47_cancelar_con_b_running(t):
    """GE-E47 — Con B RUNNING y el Host falso durmiendo, `--cancelar grf_...` deja B CANCELLED por el camino de
    Task 4, con el arbol del Host terminado; C no tiene turno; el GraphRun queda CANCELLED; y el comando vuelve
    con el terminal ya escrito."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas)
    corriendo = _running_de(proy, "b")
    t.verdadero("GE-E47 B esta RUNNING, con el Host dormido", corriendo is not None)
    (graph_run_id,) = _grafos(proy)
    eid_b = _eid_de(proy, "b")
    pid_del_host = ((M64._leer_json(corriendo / registro.PROCESO) or {}).get("pid") if corriendo is not None else None)
    try:
        cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE, espera=60, intervalo=0.2)
        sal = _salida(hijo)
        res = sal.get("res") or {}
        t.igual("GE-E47 el comando vuelve con el terminal ya escrito: CANCELLED, y el conductor ya no sigue",
                ("ACTIVE", "CANCELLED", True, False, [eid_b]),
                (cancelacion["antes"], cancelacion["despues"], cancelacion["conductorVivo"],
                 cancelacion["sigue"], cancelacion["canceladas"]))
        t.igual("GE-E47 B queda CANCELLED por el camino de Task 4: con su cancelacion.json",
                ("CANCELLED", True),
                (registro.estado(str(proy), CLAVE, eid_b)["estado"],
                 (M72._carpeta(proy, eid_b) / registro.CANCELACION).is_file()))
        t.verdadero("GE-E47 con el arbol del Host terminado", pid_del_host is not None
                    and M72._esperar(lambda: not proceso.pid_vivo(pid_del_host), 20))
        t.igual("GE-E47 C no tiene turno, y no se despacho: marcas de A y de B", (None, [(1, "a"), (2, "b")]),
                (_ultimo(proy, "c"), _despachos(proy, graph_run_id)))
        t.igual("GE-E47 el GraphRun queda CANCELLED, sin error y con cancelRequested, y lo escribio su conductor",
                (None, "CANCELLED", None, True),
                (sal.get("exc"), res.get("status"), res.get("error"), res.get("cancelRequested")))
        t.igual("GE-E47 ningun GraphRun ACTIVE, ninguna Execution propia abierta, y el candado libre",
                ([], [], True), (registro.activos(str(proy), CLAVE), _sin_propias_abiertas(proy, graph_run_id),
                                 _libre(proy)))
        _valida(t, "GE-E47", proy, graph_run_id)
    finally:
        M72._terminar(pid_del_host)


def test_ge_e48_la_ventana_entre_cancelar_y_despachar(t):
    """GE-E48 — Con el conductor detenido entre la marca de despacho de B y su lectura de la cancelacion (7e a
    7f), y `--cancelar grf_...` completo en ese hueco: B no tiene turno. Con el conductor detenido despues de
    esa lectura y antes del motor (7f a 7g), y un Host de B que sobrevive a varios tramos despues del pedido (60 s):
    B queda CANCELLED sin `entrega.json`, o con el Host terminado. Con el mismo conductor detenido, pero un
    Host de B inmediato y un cancelador que mira cada 5 s (27.1 J, c): B queda SUCCEEDED y el GraphRun
    SUCCEEDED con `cancelRequested: true`. En ninguno de los tres casos una Execution del GraphRun queda abierta despues de
    su `result.json` (17.3, observacion 3; 17.4, limite 8). El rango intermedio (el Host termina en el mismo tramo
    que el pedido) NO tiene resultado unico y este test no lo asevera (17.3, observacion 2; 27.1 L)."""
    # a) el hueco antes de la lectura: el cancelador escribe la marca y mira los despachos, y B no tiene turno
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, ganchos={"despues_del_despacho": {"unidad": "b", "esperar": ["seguir"]}})
    try:
        t.verdadero("GE-E48 a) el conductor llego despues de la marca de B", _esperar_marca(marcas, "despues_del_despacho.b"))
        (graph_run_id,) = _grafos(proy)
        t.igual("GE-E48 a) hay marca de despacho de B y ningun turno la nombra", ([(1, "a"), (2, "b")], None),
                (_despachos(proy, graph_run_id), _ultimo(proy, "b")))
        cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE, espera=1.0, intervalo=0.2)
        t.igual("GE-E48 a) el cancelador, completo en el hueco, no encuentra nada que cancelar: la marca quedo escrita",
                ([], True, "ACTIVE"), (cancelacion["canceladas"], cancelacion["marcaNueva"], cancelacion["despues"]))
    finally:
        _dejar_marca(marcas, "seguir")
    sal = _salida(hijo)
    res = sal.get("res") or {}
    t.igual("GE-E48 a) al seguir, el conductor ve la marca en 7f y cierra CANCELLED: B no tiene turno ni Host",
            (None, "CANCELLED", None, ["a"]),
            (sal.get("exc"), res.get("status"), _ultimo(proy, "b"), _bitacoras(bitacora)))
    _valida(t, "GE-E48 a)", proy, graph_run_id)

    # b) el hueco despues de la lectura: el conductor no vio la marca y llama al motor; el cancelador la ve en los despachos
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, antes_del_motor={"unidad": "b", "esperar": ["seguir"]})
    cancelador = None
    try:
        t.verdadero("GE-E48 b) el conductor llego despues de 7f y antes del motor, con B sin turno",
                    _esperar_marca(marcas, "antes_del_motor.b") and _ultimo(proy, "b") is None)
        (graph_run_id,) = _grafos(proy)
        t.igual("GE-E48 b) el conductor todavia no vio ninguna marca de cancelacion: no la hay", False,
                registro.cancelada(str(proy), CLAVE, graph_run_id))
        cancelador = _cancelador(proy, M64._tmp("ge73-marcas-"), graph_run_id, 60)
        t.verdadero("GE-E48 b) el cancelador escribio la marca, ya despues de la lectura del conductor",
                    M72._esperar(lambda: registro.cancelada(str(proy), CLAVE, graph_run_id)))
    finally:
        _dejar_marca(marcas, "seguir")
    sal_c = _salida(cancelador, 90) if cancelador is not None else {"exc": "no se lanzo"}
    sal = _salida(hijo)
    res = sal.get("res") or {}
    eid_b = (_ultimo(proy, "b") or {}).get("executionId")
    cancelacion = sal_c.get("res") or {}
    t.igual("GE-E48 b) el cancelador vuelve con el terminal escrito, habiendo cancelado la de B",
            (None, "CANCELLED", [eid_b]),
            (sal_c.get("exc"), cancelacion.get("despues"), cancelacion.get("canceladas")))
    t.igual("GE-E48 b) B queda CANCELLED, el GraphRun CANCELLED, y ninguna Execution propia queda abierta",
            ("CANCELLED", "CANCELLED", []),
            (registro.estado(str(proy), CLAVE, eid_b or "exe_" + "0" * 32)["estado"], res.get("status"),
             _sin_propias_abiertas(proy, graph_run_id)))
    sin_entrega = not (M72._carpeta(proy, eid_b or "exe_" + "0" * 32) / registro.ENTREGA).exists()
    pids_de_b = [i["pid"] for i in _invocaciones(bitacora) if i["workUnitId"] == "b"]
    t.verdadero("GE-E48 b) con un Host que sobrevive a varios tramos despues del pedido: sin entrega.json, o con el Host terminado",
                sin_entrega or (pids_de_b and M72._esperar(lambda: not any(proceso.pid_vivo(p) for p in pids_de_b), 20)))
    for pid in pids_de_b:
        M72._terminar(pid)
    _valida(t, "GE-E48 b)", proy, graph_run_id)

    # c) el Host de B termina de inmediato y el intervalo del cancelador supera lo que tardan B y el terminal
    # (17.3, observacion 2; 27.1 J): la primera vuelta no encuentra turno de B, y la segunda llega con todo cerrado
    proy = M72._proyecto(_unidades_abc()[:2])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    marcas_c = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, antes_del_motor={"unidad": "b", "esperar": ["seguir"]})
    cancelador = None
    try:
        t.verdadero("GE-E48 c) el conductor llego despues de 7f y antes del motor, con B sin turno",
                    _esperar_marca(marcas, "antes_del_motor.b") and _ultimo(proy, "b") is None)
        (graph_run_id,) = _grafos(proy)
        cancelador = _cancelador(proy, marcas_c, graph_run_id, 60, 5)
        t.verdadero("GE-E48 c) el cancelador completo su primera vuelta, y B todavia no tenia turno que cancelar",
                    _esperar_marca(marcas_c, "barrido.1") and _ultimo(proy, "b") is None
                    and registro.cancelada(str(proy), CLAVE, graph_run_id))
    finally:
        _dejar_marca(marcas, "seguir")
    sal = _salida(hijo)
    res = sal.get("res") or {}
    sal_c = _salida(cancelador, 90) if cancelador is not None else {"exc": "no se lanzo"}
    cancelacion = sal_c.get("res") or {}
    eid_b = _eid_de(proy, "b")
    carpeta_b = M72._carpeta(proy, eid_b)
    t.igual("GE-E48 c) el cancelador sale sin excepcion, sin haberle pedido cancelar a nadie, y con el terminal escrito",
            (None, [], True, "SUCCEEDED"),
            (sal_c.get("exc"), cancelacion.get("canceladas"), cancelacion.get("marcaNueva"),
             cancelacion.get("despues")))
    t.igual("GE-E48 c) B queda SUCCEEDED, con entrega.json y sin cancelacion.json propio",
            ("SUCCEEDED", True, False),
            (_estado_de(proy, "b"), (carpeta_b / registro.ENTREGA).is_file(),
             (carpeta_b / registro.CANCELACION).exists()))
    t.igual("GE-E48 c) la bitacora registra una sola invocacion del Host para B", 1, _bitacoras(bitacora).count("b"))
    t.igual("GE-E48 c) el conductor cierra SUCCEEDED, sin error y con cancelRequested: true",
            (None, "SUCCEEDED", None, True),
            (sal.get("exc"), res.get("status"), res.get("error"), res.get("cancelRequested")))
    t.verdadero("GE-E48 c) el cancelacion.json del grafo existe",
                (M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id / registro.CANCELACION).is_file())
    t.igual("GE-E48 c) ninguna Execution propia queda abierta despues del result.json", [],
            _sin_propias_abiertas(proy, graph_run_id))
    _valida(t, "GE-E48 c)", proy, graph_run_id)


def test_ge_e49_una_cancelacion_tardia_no_le_gana_a_un_succeeded(t):
    """GE-E49 — Con las tres SUCCEEDED y el conductor detenido antes del terminal, `--cancelar grf_...` deja el
    GraphRun SUCCEEDED con `cancelRequested: true` (GD-05, GC-23: un SUCCEEDED observado gana sobre una
    cancelacion tardia). Con el conductor vivo (el que escribe el terminal) y con el conductor muerto (el que
    cierra al huerfano)."""
    # a) vivo: el cancelador espera, el conductor sigue y escribe el terminal, y el cancelador lo encuentra
    proy = _proyecto_abc()
    M72._guion(proy)
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas, ganchos={"antes_del_terminal": {"esperar": ["seguir"]}})
    cancelador = None
    try:
        t.verdadero("GE-E49 a) el conductor llego al gancho anterior al terminal", _esperar_marca(marcas, "antes_del_terminal"))
        (graph_run_id,) = _grafos(proy)
        t.igual("GE-E49 a) las tres estan SUCCEEDED y el GraphRun sin terminal", (["SUCCEEDED"] * 3, "ACTIVE"),
                ([_estado_de(proy, u) for u in ("a", "b", "c")], _leido(proy, graph_run_id)["estado"]))
        cancelador = _cancelador(proy, M64._tmp("ge73-marcas-"), graph_run_id, 60)
        t.verdadero("GE-E49 a) el cancelador escribio la marca", M72._esperar(
            lambda: registro.cancelada(str(proy), CLAVE, graph_run_id)))
    finally:
        _dejar_marca(marcas, "seguir")
    sal_c = _salida(cancelador, 90) if cancelador is not None else {"exc": "no se lanzo"}
    res = _salida(hijo).get("res") or {}
    t.igual("GE-E49 a) el conductor cierra SUCCEEDED, con cancelRequested: true y sin error",
            ("SUCCEEDED", None, True), (res.get("status"), res.get("error"), res.get("cancelRequested")))
    t.igual("GE-E49 a) y el cancelador encuentra el terminal ya escrito: informa SUCCEEDED, sin cancelar nada",
            (None, "SUCCEEDED", [], False), (sal_c.get("exc"), (sal_c.get("res") or {}).get("despues"),
                                             (sal_c.get("res") or {}).get("canceladas"),
                                             (sal_c.get("res") or {}).get("sigue")))
    _valida(t, "GE-E49 a)", proy, graph_run_id)

    # b) muerto: el cancelador toma el candado y cierra al huerfano: la regla de cierre da SUCCEEDED
    proy = _proyecto_abc()
    M72._guion(proy)
    _cortado(t, "GE-E49 b)", proy, {"antes_del_terminal": {"morir": True}})
    (graph_run_id,) = _grafos(proy)
    antes_de_las_tres = [_bytes_de(proy, _eid_de(proy, u)) for u in ("a", "b", "c")]
    cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE)
    t.igual("GE-E49 b) toma el candado, cierra al huerfano, y queda SUCCEEDED", ("ACTIVE", "SUCCEEDED", True, False),
            (cancelacion["antes"], cancelacion["despues"], cancelacion["cerradoAqui"], cancelacion["sigue"]))
    doc = _valida(t, "GE-E49 b)", proy, graph_run_id) or {}
    t.igual("GE-E49 b) con cancelRequested: true, sin error, y las tres Executions identicas: no se cancelo nada",
            ("SUCCEEDED", None, True, antes_de_las_tres),
            (doc.get("status"), doc.get("error"), doc.get("cancelRequested"),
             [_bytes_de(proy, _eid_de(proy, u)) for u in ("a", "b", "c")]))


def test_ge_e50_cancelar_es_idempotente_y_un_terminal_no_se_toca(t):
    """GE-E50 — `--cancelar grf_...` sobre un GraphRun terminal no escribe ningun archivo. Dos `--cancelar`
    sobre uno ACTIVE dejan un solo `cancelacion.json`, y el segundo vuelve normalmente (sale con 0)."""
    proy = _proyecto_abc()
    M72._guion(proy)
    res = _grafo(proy)["res"] or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    antes = M72._proyecto_sin_git(proy)
    cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE)
    t.igual("GE-E50 sobre un terminal lo informa: SUCCEEDED antes y despues, sin pedido ni marca nueva",
            ("SUCCEEDED", "SUCCEEDED", False, False, False),
            (cancelacion["antes"], cancelacion["despues"], cancelacion["pedido"], cancelacion["marcaNueva"],
             cancelacion["cerradoAqui"]))
    t.igual("GE-E50 y no escribio ningun archivo en el proyecto", [], M64._diferencias(antes, M72._proyecto_sin_git(proy)))
    t.verdadero("GE-E50 ni una cancelacion.json", not (M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id
                                                      / registro.CANCELACION).exists())

    # sobre uno ACTIVE, con el conductor vivo: la segunda no escribe otra marca ni cambia la primera
    otro = _proyecto_abc()
    M72._guion(otro)
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(otro, marcas, ganchos={"despues_del_retorno": {"unidad": "a", "esperar": ["seguir"]}})
    try:
        t.verdadero("GE-E50 el conductor llego al gancho posterior a A", _esperar_marca(marcas, "despues_del_retorno.a"))
        (activo,) = _grafos(otro)
        ruta = M72._ejecuciones(otro) / CLAVE / GRAFOS / activo / registro.CANCELACION
        primera = grafo.cancelar_grafo(str(otro), CLAVE, activo, PIDE, espera=0.4, intervalo=0.2)
        bytes_de_la_primera = ruta.read_bytes() if ruta.exists() else None
        segunda = grafo.cancelar_grafo(str(otro), CLAVE, activo, "otra persona", espera=0.4, intervalo=0.2)
        t.igual("GE-E50 la primera escribe la marca; la segunda no escribe otra y vuelve normalmente",
                (True, False, True, True), (primera["marcaNueva"], segunda["marcaNueva"], segunda["pedido"],
                                           segunda["sigue"]))
        t.igual("GE-E50 queda un solo cancelacion.json, con los bytes de la primera", (True, bytes_de_la_primera),
                (ruta.is_file(), ruta.read_bytes() if ruta.exists() else None))
        t.igual("GE-E50 y de quien lo pidio primero", PIDE, M64._leer_json(ruta).get("pedidoPor"))
    finally:
        _dejar_marca(marcas, "seguir")
    _salida(hijo)

    # sobre uno ACTIVE sin conductor: la primera lo cierra, la segunda ya es un terminal y no escribe nada
    cortado = _proyecto_abc()
    M72._guion(cortado)
    _cortado(t, "GE-E50", cortado, {"despues_del_retorno": {"unidad": "a", "morir": True}})
    (huerfano,) = _grafos(cortado)
    primera = grafo.cancelar_grafo(str(cortado), CLAVE, huerfano, PIDE)
    t.igual("GE-E50 sin conductor, la primera cierra al huerfano: CANCELLED", ("ACTIVE", "CANCELLED", True),
            (primera["antes"], primera["despues"], primera["cerradoAqui"]))
    antes = M72._proyecto_sin_git(cortado)
    segunda = grafo.cancelar_grafo(str(cortado), CLAVE, huerfano, PIDE)
    t.igual("GE-E50 la segunda lo informa terminal y no escribe nada", ("CANCELLED", "CANCELLED", False, []),
            (segunda["antes"], segunda["despues"], segunda["pedido"],
             M64._diferencias(antes, M72._proyecto_sin_git(cortado))))
    t.igual("GE-E50 un solo cancelacion.json", 1, len(list((M72._ejecuciones(cortado) / CLAVE / GRAFOS / huerfano)
                                                          .glob(registro.CANCELACION))))


def test_ge_e51_cancelar_un_huerfano_con_su_requested_sin_motor(t):
    """GE-E51 — Con el conductor muerto y su Execution de B REQUESTED sin motor, `--cancelar grf_...` toma el
    candado, deja B CANCELLED y el GraphRun CANCELLED (cumple un pedido persistido: 16.1, paso 2)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    _cortado(t, "GE-E51", proy, {"antes_de_entregar": {"unidad": "b", "morir": True}})
    (graph_run_id,) = _grafos(proy)
    eid_b = _eid_de(proy, "b")
    t.igual("GE-E51 en disco: B esta REQUESTED sin motor y el candado de la tarea esta libre",
            ("REQUESTED", True, True), (registro.estado(str(proy), CLAVE, eid_b)["estado"],
                                        registro.candado_libre(str(M72._carpeta(proy, eid_b))), _libre(proy)))
    cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE)
    t.igual("GE-E51 toma el candado y cierra al huerfano: ACTIVE antes, CANCELLED despues",
            ("ACTIVE", "CANCELLED", True, False, True),
            (cancelacion["antes"], cancelacion["despues"], cancelacion["cerradoAqui"], cancelacion["sigue"],
             cancelacion["pedido"]))
    t.igual("GE-E51 B queda CANCELLED, por el pedido que cumplio el cierre", ("CANCELLED", True),
            (registro.estado(str(proy), CLAVE, eid_b)["estado"], (M72._carpeta(proy, eid_b) / registro.CANCELACION).is_file()))
    doc = _valida(t, "GE-E51", proy, graph_run_id) or {}
    t.igual("GE-E51 el GraphRun queda CANCELLED, sin error y con cancelRequested", ("CANCELLED", None, True),
            (doc.get("status"), doc.get("error"), doc.get("cancelRequested")))
    t.igual("GE-E51 A sigue SUCCEEDED y C no tiene turno, no se despacho nada mas, y el candado queda libre",
            ("SUCCEEDED", None, [(1, "a"), (2, "b")], True),
            (_estado_de(proy, "a"), _ultimo(proy, "c"), _despachos(proy, graph_run_id), _libre(proy)))


def test_ge_e52_cancelar_el_grafo_no_toca_a_una_manual_de_la_tarea(t):
    """GE-E52 — Con una Execution manual abierta de la misma TaskKey, `--cancelar grf_...` no escribe su
    `cancelacion.json`, y la manual termina con su propio resultado. Se cancela solo lo propio: la de B, que
    es del GraphRun y esta RUNNING, y no la manual de Y, que esta abierta a su lado (GD-11, GE-I19)."""
    proy = M72._proyecto([M64._unidad("a"), M64._unidad("b", dependencias=("a",)),
                          M64._unidad("y", dependencias=("a",))])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}, "y": {"dormir": 6}})
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas)
    carpeta_b = _running_de(proy, "b")
    t.verdadero("GE-E52 B, del GraphRun, esta RUNNING", carpeta_b is not None)
    (graph_run_id,) = _grafos(proy)
    manual = _manual(proy, "y")
    carpeta_y = _running_de(proy, "y")
    t.verdadero("GE-E52 y la manual de Y esta abierta a su lado (de otra clave, y despues del chequeo 7d)",
                carpeta_y is not None)
    eid_b = carpeta_b.name if carpeta_b is not None else "exe_" + "0" * 32
    eid_y = carpeta_y.name if carpeta_y is not None else "exe_" + "0" * 32
    pid_de_b = ((M64._leer_json(carpeta_b / registro.PROCESO) or {}).get("pid") if carpeta_b is not None else None)
    try:
        cancelacion = grafo.cancelar_grafo(str(proy), CLAVE, graph_run_id, PIDE, espera=60, intervalo=0.2)
        sal_y = _salida(manual)
        sal = _salida(hijo)
        t.igual("GE-E52 se cancela solo la propia: la de B", [eid_b], cancelacion["canceladas"])
        t.igual("GE-E52 la manual de Y no recibe un `cancelacion.json`, y termina con su propio resultado "
                "(SUCCEEDED)", (False, None, "SUCCEEDED"),
                ((M72._carpeta(proy, eid_y) / registro.CANCELACION).exists(), sal_y.get("exc"),
                 (sal_y.get("res") or {}).get("status")))
        t.igual("GE-E52 B queda CANCELLED y el GraphRun CANCELLED", ("CANCELLED", "CANCELLED"),
                (registro.estado(str(proy), CLAVE, eid_b)["estado"], (sal.get("res") or {}).get("status")))
        t.igual("GE-E52 el nodo de Y es de la manual: dispatched: false, y ninguna marca de despacho la nombra",
                (False, [(1, "a"), (2, "b")]),
                ((_nodos(sal.get("res") or {}).get("y") or {}).get("dispatched"), _despachos(proy, graph_run_id)))
        _valida(t, "GE-E52", proy, graph_run_id)
    finally:
        M72._terminar(pid_de_b)


# -- el estado de los GraphRuns: solo lee (GE-E70, GE-I30) -----------------------------------------------

class _SinSondas(object):
    """Hace que cualquier sonda de candado, cualquier recuperacion y cualquier escritura del registro levante,
    para que un `estado` que las use no pase: lo que se mira es lo que NO llama."""

    NOMBRES = (("registro", "CandadoDeTarea"), ("registro", "candado_libre"), ("registro", "Tomado"),
               ("registro", "escribir_una_vez"), ("registro", "escribir_json"), ("motor", "recuperar"),
               ("motor", "cancelar"), ("grafo", "cerrar_grafo"), ("grafo", "cerrar_huerfano"),
               ("grafo", "cerrar_huerfanos"))

    def __enter__(self):
        modulos = {"registro": registro, "motor": motor, "grafo": grafo}
        self.guardado = []

        def prohibido(nombre):
            def _(*a, **k):
                raise AssertionError("`estado_de_grafos` llamo a %s: solo puede leer" % nombre)
            return _

        try:
            for modulo, nombre in self.NOMBRES:
                self.guardado.append((modulos[modulo], nombre, getattr(modulos[modulo], nombre)))
                setattr(modulos[modulo], nombre, prohibido("%s.%s" % (modulo, nombre)))
        except BaseException:
            self.__exit__()                      # un nombre que no existe no deja parcheado a nadie
            raise
        return self

    def __exit__(self, *_):
        for modulo, nombre, real in self.guardado:
            setattr(modulo, nombre, real)
        self.guardado = []


def test_ge_e70_el_estado_de_los_graphruns_solo_lee(t):
    """GE-E70 (la parte de `estado_de_grafos`; `--grafo --estado` como comando es de la etapa 6) — Con un
    GraphRun huerfano, lo muestra ACTIVE, con el comando para cerrarlo, y despues de correrlo no cambio ningun
    archivo del proyecto: no recupera, no cierra huerfanos, no sondea el candado de la tarea ni el de ninguna
    Execution, y no escribe (GE-I30)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    marcas = M64._tmp("ge73-marcas-")
    hijo = _conductor(proy, marcas)
    corriendo = _running_de(proy, "b")
    pid_del_host = ((M64._leer_json(corriendo / registro.PROCESO) or {}).get("pid") if corriendo is not None else None)
    M72._matar(hijo.pid)
    hijo.communicate(timeout=60)
    _esperar_libre(proy, [corriendo] if corriendo is not None else [])
    try:
        (huerfano,) = _grafos(proy)
        eid_a, eid_b = _eid_de(proy, "a"), _eid_de(proy, "b")
        otro = _proyecto_abc()
        M72._guion(otro)
        terminado = (_grafo(otro)["res"] or {}).get("graphRunId") or "grf_" + "0" * 32
        antes = M72._proyecto_sin_git(proy)
        antes_de_otro = M72._proyecto_sin_git(otro)

        with _SinSondas():
            filas = grafo.estado_de_grafos(str(proy), CLAVE)
            terminados = grafo.estado_de_grafos(str(otro), CLAVE)
        t.igual("GE-E70 despues de correrlo no cambio ningun archivo del proyecto", [],
                M64._diferencias(antes, M72._proyecto_sin_git(proy)))
        t.igual("GE-E70 ni del otro proyecto, con un GraphRun terminal", [],
                M64._diferencias(antes_de_otro, M72._proyecto_sin_git(otro)))
        t.igual("GE-E70 el huerfano se muestra ACTIVE, con su id, su huella, quien lo pidio, y sin terminal",
                (1, huerfano, "ACTIVE", _huella_del_plan(proy), PIDE, None, None, False),
                (len(filas), filas[0]["graphRunId"], filas[0]["estado"], filas[0]["planFingerprint"],
                 filas[0]["requestedBy"], filas[0]["error"], filas[0]["endedAt"], filas[0]["cancelRequested"]))
        t.igual("GE-E70 con el comando que lo cierra, si su proceso murio: el proximo --grafo o --cancelar grf_",
                ["ejecutar %s --grafo" % CLAVE, "ejecutar %s --cancelar %s" % (CLAVE, huerfano)],
                filas[0]["comandos"])
        t.igual("GE-E70 y sus despachos, con el estado derivado de cada Execution: A SUCCEEDED, B RUNNING (sin "
                "motor, y sin cerrarla: no recupera)",
                [(1, "a", eid_a, "SUCCEEDED"), (2, "b", eid_b, "RUNNING")],
                [(d["numero"], d["workUnitId"], d["executionId"], d["estado"]) for d in filas[0]["despachos"]])
        t.igual("GE-E70 un terminal se muestra con su estado, sin comandos", (terminado, "SUCCEEDED", None, []),
                (terminados[0]["graphRunId"], terminados[0]["estado"], terminados[0]["error"],
                 terminados[0]["comandos"]))
        t.igual("GE-E70 el candado de la tarea sigue libre, y la RUNNING sin motor sigue RUNNING",
                (True, "RUNNING"), (_libre(proy), registro.estado(str(proy), CLAVE, eid_b)["estado"]))
        t.igual("GE-E70 una TaskKey que no lo es, o una tarea sin GraphRuns", (True, []),
                (_levanta(lambda: grafo.estado_de_grafos(str(proy), "no-es-una-clave")) is not None,
                 grafo.estado_de_grafos(str(_proyecto_abc()), CLAVE)))
    finally:
        M72._terminar(pid_del_host)


# -- las ramas del conductor que la spec no numera: GD-04, GD-10 ------------------------------------------

def test_gd10_un_graphrun_ilegible_no_se_cierra_ni_se_reabre(t):
    """GE-E70 (la parte de la enmienda del 14-10-2026, 27.1 G: un GraphRun ILEGIBLE), GD-10, GD-04 — Un GraphRun
    cuyo `inicio.json` o `result.json` no valida es ILEGIBLE: no es ACTIVE, asi que
    ni el conductor nuevo ni `--cancelar` lo cierran, lo reabren o lo tocan: no hay un inicio.json del que sacar
    sus nodos, o ya tiene un terminal que no se lee. El conductor nuevo sigue de largo, y `estado_de_grafos` lo
    muestra ILEGIBLE con el motivo. (La seccion 16 no dice que hace el conductor con uno: se toma la lectura que
    ya fija `registro.leer_grafo`, que no lo cierra.)"""
    proy = _proyecto_abc()
    M72._guion(proy)
    base = M72._ejecuciones(proy) / CLAVE / GRAFOS
    sin_inicio_valido = "grf_" + "1" * 32
    sin_terminal_valido = "grf_" + "2" * 32
    (base / sin_inicio_valido / registro.DESPACHOS).mkdir(parents=True)
    (base / sin_inicio_valido / registro.INICIO).write_text("{no es un inicio", encoding="utf-8")
    inicio = _inicio(graphRunId=sin_terminal_valido, taskKey=CLAVE)
    (base / sin_terminal_valido / registro.DESPACHOS).mkdir(parents=True)
    (base / sin_terminal_valido / registro.INICIO).write_text(json.dumps(inicio), encoding="utf-8")
    (base / sin_terminal_valido / registro.RESULT).write_text("no es un resultado", encoding="utf-8")
    t.igual("GD-10 los dos estan ILEGIBLES, ninguno ACTIVE",
            ({sin_inicio_valido: "ILEGIBLE", sin_terminal_valido: "ILEGIBLE"}, []),
            ({g: _leido(proy, g)["estado"] for g in (sin_inicio_valido, sin_terminal_valido)},
             registro.activos(str(proy), CLAVE)))
    antes = {g: _foto_de_grafo(proy, g) for g in (sin_inicio_valido, sin_terminal_valido)}

    res = _grafo(proy)["res"] or {}
    t.igual("GD-10 el conductor nuevo sigue de largo y termina SUCCEEDED", "SUCCEEDED", res.get("status"))
    t.igual("GD-10 y no toco ninguno de los dos: ni un archivo mas, ni uno cambiado", antes,
            {g: _foto_de_grafo(proy, g) for g in (sin_inicio_valido, sin_terminal_valido)})
    filas = {f["graphRunId"]: f for f in grafo.estado_de_grafos(str(proy), CLAVE)}
    t.igual("GD-10 `estado_de_grafos` los muestra ILEGIBLES, con el motivo, sin comandos y sin inventar lo que no se lee",
            [("ILEGIBLE", True, [], None)] * 2,
            [(filas[g]["estado"], bool(filas[g]["motivo"]), filas[g]["comandos"], filas[g]["error"])
             for g in (sin_inicio_valido, sin_terminal_valido)])
    for g in (sin_inicio_valido, sin_terminal_valido):
        try:
            grafo.cancelar_grafo(str(proy), CLAVE, g, PIDE)
            mensaje = None
        except motor.ErrorDelComando as e:
            mensaje = str(e)
        t.verdadero("GD-10 `--cancelar` sobre uno ilegible es un error del comando que dice que no se lee",
                    mensaje is not None and "ilegible" in mensaje)
    t.igual("GD-10 y `--cancelar` no escribio nada en ninguno: ni la marca", antes,
            {g: _foto_de_grafo(proy, g) for g in (sin_inicio_valido, sin_terminal_valido)})


def test_gd04_el_conductor_barre_lo_que_el_anterior_no_alcanzo_a_publicar(t):
    """GD-04, §16.2 — Una carpeta `grf_...` sin `inicio.json` no es un GraphRun: es un residuo de la creacion, y
    la barre el proximo que toma el candado (el paso 2 de `conducir`). Los temporales de escritura de los
    GraphRuns con mas de diez minutos tambien (GD-20, F2'): los nuevos no."""
    proy = _proyecto_abc()
    M72._guion(proy)
    base = M72._ejecuciones(proy) / CLAVE / GRAFOS
    residuo = base / ("grf_" + "4" * 32)
    (residuo / registro.DESPACHOS).mkdir(parents=True)
    t.igual("GD-04 una carpeta grf_ sin inicio.json no es un GraphRun", ([], ["grf_" + "4" * 32]),
            (_grafos(proy), registro.residuos_de_grafos(str(proy), CLAVE)))
    cortado = _proyecto_abc()
    M72._guion(cortado)
    _cortado(t, "GD-04", cortado, {"despues_de_inicio": {"morir": True}})
    (huerfano,) = _grafos(cortado)
    carpeta = M72._ejecuciones(cortado) / CLAVE / GRAFOS / huerfano
    viejo, nuevo = carpeta / ".cancelacion.json.0ld000.tmp", carpeta / ".cancelacion.json.n3w000.tmp"
    for ruta, edad in ((viejo, 700), (nuevo, 5)):
        ruta.write_text("{a medias", encoding="utf-8")
        _envejecer(ruta, edad)
    res = _grafo(proy)["res"] or {}
    t.igual("GD-04 el conductor termina SUCCEEDED, y barrio el residuo", ("SUCCEEDED", [], False),
            (res.get("status"), registro.residuos_de_grafos(str(proy), CLAVE), residuo.exists()))
    _grafo(cortado)
    t.igual("GD-04 y limpia los temporales de mas de diez minutos de los GraphRuns, no los nuevos", (False, True),
            (viejo.exists(), nuevo.exists()))


def test_gd10_cerrar_un_huerfano_exige_el_candado_de_esa_tarea(t):
    """GD-10, §14.1 — Solo quien tiene el candado de la tarea puede afirmar que el conductor murio, y por eso
    cerrar: `cerrar_huerfano` sin candado, con uno soltado o con el de otra tarea levanta, y no escribe nada. Un
    conductor vivo (que tiene el candado) no se cierra desde afuera: `--grafo` sale con GRAPH_ALREADY_ACTIVE."""
    cortado = _proyecto_abc()
    M72._guion(cortado)
    _cortado(t, "GD-10", cortado, {"despues_del_retorno": {"unidad": "a", "morir": True}})
    (huerfano,) = _grafos(cortado)
    antes = _foto_de_grafo(cortado, huerfano)
    ajeno = registro.CandadoDeTarea(str(cortado), "GCBA-99")
    soltado = registro.CandadoDeTarea(str(cortado), CLAVE)
    soltado.soltar()
    try:
        for nombre, candado in (("ninguno", None), ("uno soltado", soltado), ("el de otra tarea", ajeno)):
            try:
                grafo.cerrar_huerfano(str(cortado), CLAVE, huerfano, candado, PIDE)
                levanto = None
            except registro.RegistroInvalido as e:
                levanto = str(e)
            t.verdadero("GD-10 cerrar un huerfano con %s levanta RegistroInvalido, y dice que falta el candado"
                        % nombre, levanto is not None and "candado" in levanto)
    finally:
        ajeno.soltar()
    t.igual("GD-10 y no escribio nada: el GraphRun sigue ACTIVE, identico", ("ACTIVE", antes),
            (_leido(cortado, huerfano)["estado"], _foto_de_grafo(cortado, huerfano)))
    candado = _tomar_pronto(cortado)
    try:
        cerrado = grafo.cerrar_huerfano(str(cortado), CLAVE, huerfano, candado, PIDE)
        otra_vez = grafo.cerrar_huerfano(str(cortado), CLAVE, huerfano, candado, PIDE)
    finally:
        candado.soltar()
    t.igual("GD-10 con el candado de la tarea lo cierra, FAILED con GRAPH_INTERRUPTED; y uno ya cerrado no se toca",
            ("FAILED", "GRAPH_INTERRUPTED", None),
            (cerrado["status"], cerrado["error"]["code"], otra_vez))
    _valida(t, "GD-10 con el candado", cortado, huerfano)


# =============================================================================================
# 6A: la CLI (GD-24, GD-27 paso 9) -- `ejecutar <KEY> --grafo`, `--grafo --estado` y `--cancelar grf_...`
# =============================================================================================
#
# Lo que la 5a y la 5b probaron por funcion, aca se prueba por el comando. `dev-harness.main` corre en este
# proceso (`_cli`) cuando lo que se mira es la salida y el codigo; `dev-harness.py` corre en un proceso aparte
# (`_cli_aparte`, `_cli_vivo`) cuando lo que se mira es el codigo de salida del proceso, o cuando hay otro
# proceso vivo de por medio: el conductor, el cancelador, el que tiene el candado. El Host es el falso de
# siempre. Todos los tests de este grupo llevan `por_cli` en el nombre.

CLI = M72.CLI
BASE_0_32_0 = "e33b41b0e897bb1bf09bc961882faae07f785135"
_CLI_EN_ESTE_PROCESO = {}


def _modulo_del_cli(nombre, ruta):
    """El dev-harness.py de `ruta` como modulo, una vez por proceso."""
    if nombre not in _CLI_EN_ESTE_PROCESO:
        _CLI_EN_ESTE_PROCESO[nombre] = _cargar(nombre, ruta)
    return _CLI_EN_ESTE_PROCESO[nombre]


def _correr_cli(modulo, argv):
    """`modulo.main` en este proceso: (codigo, stdout, stderr). Un `SystemExit` es el de argparse, ante una
    opcion que el parser no conoce: es el codigo de salida del comando, no el de la suite."""
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main([str(a) for a in argv])
    except SystemExit as e:
        codigo = e.code
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _cli(proy, *args):
    """`ejecutar <KEY> ...` por `dev-harness.main`, en este proceso: (codigo, stdout, stderr)."""
    return _correr_cli(_modulo_del_cli("dev_harness_ge73", CLI),
                       ["ejecutar", CLAVE] + list(args) + ["--proyecto", proy])


def _cli_aparte(proy, *args):
    """`ejecutar <KEY> ...` por `dev-harness.py`, en un proceso aparte: (codigo, stdout, stderr)."""
    return M64._cli_de(BIN, proy, "ejecutar", CLAVE, *args)


def _cli_vivo(proy, *args):
    """`dev-harness.py ejecutar <KEY> ...` en un proceso aparte, que se deja corriendo: el Popen."""
    entorno = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    entorno.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.Popen([sys.executable, str(CLI), "ejecutar", CLAVE] + list(args)
                            + ["--proyecto", str(proy)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=entorno)


def _fin_del_cli(hijo, limite=120):
    """(codigo, stdout, stderr) de un `_cli_vivo` cuando termina. Uno que no termina se mata."""
    try:
        salida, error = hijo.communicate(timeout=limite)
    except subprocess.TimeoutExpired:
        hijo.kill()
        salida, error = hijo.communicate()
    return hijo.returncode, salida.decode("utf-8", "replace"), error.decode("utf-8", "replace")


def _doc(salida):
    """El documento de un `--json`, o None si el stdout no es un solo documento."""
    try:
        return json.loads(salida)
    except ValueError:
        return None


def test_ge_e01_por_cli_un_grafo_que_llega_a_succeeded_sale_con_0(t):
    """GE-E01 por el comando — `ejecutar <KEY> --grafo`, con el plan A->B->C y un Host falso que devuelve
    COMPLETE para las tres, crea un GraphRun, deja las marcas 001 a 003 y tres Executions SUCCEEDED, un
    `result.json` SUCCEEDED, y sale con 0. Imprime el id, el estado y el de cada nodo."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    codigo, salida, error = _cli(proy, "--grafo")
    ids = _grafos(proy)
    graph_run_id = ids[0] if ids else "grf_" + "0" * 32
    leido = _leido(proy, graph_run_id) or {"estado": None}
    t.igual("GE-E01 por CLI `--grafo` sale con 0 y no dice nada por stderr", (0, ""), (codigo, error))
    t.igual("GE-E01 por CLI hay un GraphRun SUCCEEDED, con las marcas 001 a 003 para A, B y C",
            (1, "SUCCEEDED", [(1, "a"), (2, "b"), (3, "c")]),
            (len(ids), leido["estado"], _despachos(proy, graph_run_id)))
    t.igual("GE-E01 por CLI tres Executions SUCCEEDED, y el Host recibio una invocacion por unidad",
            (["SUCCEEDED"] * 3, ["a", "b", "c"]),
            ([registro.estado(str(proy), CLAVE, _eid_de(proy, u))["estado"] for u in ("a", "b", "c")],
             _bitacoras(bitacora)))
    t.contiene("GE-E01 por CLI la primera linea dice el id, la tarea y SUCCEEDED",
               "%s %s: SUCCEEDED\n" % (graph_run_id, CLAVE), salida)
    for unidad in ("a", "b", "c"):
        t.contiene("GE-E01 por CLI el nodo %s sale SATISFIED, con su Execution y que la despacho este GraphRun"
                   % unidad, "  %s  SATISFIED  %s  (la despachó este GraphRun)\n"
                   % (unidad, _eid_de(proy, unidad)), salida)
    _valida(t, "GE-E01 por CLI", proy, graph_run_id)


def test_ge_e06_por_cli_con_todo_succeeded_no_hay_despachos_y_sale_con_0(t):
    """GE-E06 por el comando — Con las tres unidades ya SUCCEEDED bajo F, por tres `ejecutar --unidad` de
    verdad, `--grafo` crea un GraphRun sin marcas de despacho, con `result.json` SUCCEEDED, el Host no recibe
    invocaciones y sale con 0."""
    proy = _proyecto_abc()
    M72._guion(proy)
    previas = []
    for unidad in ("a", "b", "c"):
        codigo, _, _ = _cli(proy, "--unidad", unidad)
        previas.append((unidad, codigo, _eid_de(proy, unidad)))
    t.igual("GE-E06 por CLI las tres `--unidad` salen con 0", [("a", 0), ("b", 0), ("c", 0)],
            [(u, c) for u, c, _ in previas])
    antes = dict((e, _bytes_de(proy, e)) for _, _, e in previas)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    codigo, salida, _ = _cli(proy, "--grafo", "--json")
    res = _doc(salida) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E06 por CLI `--grafo` sale con 0, SUCCEEDED y sin error", (0, "SUCCEEDED", None),
            (codigo, res.get("status"), res.get("error")))
    t.igual("GE-E06 por CLI el GraphRun existe y no tiene marcas de despacho", ([graph_run_id], []),
            (_grafos(proy), _despachos(proy, graph_run_id)))
    t.igual("GE-E06 por CLI el Host no recibe invocaciones, y las tres Executions quedan identicas",
            ([], antes),
            (_invocaciones(bitacora), dict((e, _bytes_de(proy, e)) for e in antes)))
    t.igual("GE-E06 por CLI los tres nodos SATISFIED y dispatched: false", [("SATISFIED", False)] * 3,
            [(n["state"], n["dispatched"]) for n in res.get("nodes") or []])
    _valida(t, "GE-E06 por CLI", proy, graph_run_id)


def test_ge_e08_por_cli_una_estructura_invalida_sale_con_2_y_no_crea_nada(t):
    """GE-E08 por el comando — Un plan guardado a mano con un ciclo, con una unidad que depende de si misma,
    con una dependencia a una unidad inexistente, con una dependencia repetida o sin unidades: `--grafo` sale
    con 2 y GRAPH_STRUCTURE_INVALID, y no queda ninguna carpeta `grf_...`, ningun turno ni ninguna Execution.
    Con `--json` imprime el rechazo, `{code, detail}`."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    original = _plan_original(proy)

    def deps(unidad, dependencias):
        def cambio(plan):
            next(u for u in plan["workUnits"] if u["id"] == unidad)["dependencies"] = dependencias
        return cambio

    casos = (("un ciclo", deps("a", ["c"])), ("una unidad que depende de si misma", deps("a", ["a"])),
             ("una dependencia a una unidad inexistente", deps("a", ["no-existe"])),
             ("una dependencia repetida", deps("b", ["a", "a"])),
             ("un plan sin unidades", lambda plan: plan.update(workUnits=[])))
    for nombre, cambio in casos:
        M72._reescribir_plan(proy, cambio)
        codigo, salida, _ = _cli(proy, "--grafo", "--json")
        rechazo = _doc(salida) or {}
        t.igual("GE-E08 por CLI %s: sale con 2 y --json imprime el rechazo, con sus dos claves" % nombre,
                (2, ["code", "detail"], "GRAPH_STRUCTURE_INVALID"),
                (codigo, sorted(rechazo), rechazo.get("code")))
        _nada_creado(t, "GE-E08 por CLI %s:" % nombre, proy)
        M64._plan_de(proy, CLAVE).write_bytes(original)
    t.igual("GE-E08 por CLI el Host no recibio ninguna invocacion", [], _invocaciones(bitacora))
    M72._reescribir_plan(proy, deps("b", ["a", "a"]))
    codigo, salida, _ = _cli(proy, "--grafo")
    t.igual("GE-E08 por CLI sin --json, dice que no arranco, con el codigo y el motivo, y sale con 2", 2, codigo)
    t.contiene("GE-E08 por CLI y lo dice en una linea", "No arrancó el GraphRun de %s: GRAPH_STRUCTURE_INVALID · "
               "la unidad b repite su dependencia a" % CLAVE, salida)


def test_ge_e09_por_cli_un_plan_ilegible_sale_con_2_y_no_crea_nada(t):
    """GE-E09 por el comando — Sin plan, con un plan que no es JSON, con un plan de otra TaskKey o con dos
    unidades del mismo id: `--grafo` sale con 2 y GRAPH_PLAN_UNREADABLE, sin carpeta `grf_...` ni Execution."""
    proy = _proyecto_abc()
    M72._guion(proy)
    original = _plan_original(proy)
    ruta = M64._plan_de(proy, CLAVE)

    def repetida(plan):
        plan["workUnits"].append(dict(plan["workUnits"][0]))

    def otra_tarea(plan):
        plan["meta"]["task_key"] = "GCBA-99"

    casos = (("sin plan guardado", lambda: ruta.unlink()),
             ("un plan que no es JSON", lambda: ruta.write_bytes(b'{"meta": {"task_key": ')),
             ("un plan de otra TaskKey", lambda: M72._reescribir_plan(proy, otra_tarea)),
             ("dos unidades con el mismo id", lambda: M72._reescribir_plan(proy, repetida)))
    for nombre, preparar in casos:
        preparar()
        codigo, salida, _ = _cli(proy, "--grafo", "--json")
        rechazo = _doc(salida) or {}
        t.igual("GE-E09 por CLI %s: sale con 2 y --json imprime el rechazo, con sus dos claves" % nombre,
                (2, ["code", "detail"], "GRAPH_PLAN_UNREADABLE"),
                (codigo, sorted(rechazo), rechazo.get("code")))
        _nada_creado(t, "GE-E09 por CLI %s:" % nombre, proy)
        ruta.write_bytes(original)


def test_ge_e18_por_cli_la_primera_falla_cierra_el_graphrun_y_sale_con_2(t):
    """GE-E18 por el comando — Con A->B->C mas una unidad D que depende solo de A y va despues de B, y un Host
    falso que declara PARTIAL para B: `--grafo` sale con 2, y su `--json` es el `result.json`: FAILED con
    WORK_UNIT_NOT_SUCCEEDED por B. Ni C ni D tienen turno."""
    proy = M72._proyecto(_unidades_abc() + [M64._unidad("d", dependencias=("a",))])
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"resultado": M72._informe("PARTIAL")}})
    codigo, salida, _ = _cli(proy, "--grafo", "--json")
    res = _doc(salida) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    eid_b = _eid_de(proy, "b")
    t.igual("GE-E18 por CLI sale con 2, con el GraphRun FAILED por B", (2, "FAILED", (
        "WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "FAILED", "AGENT_DECLARED_NOT_COMPLETE")),
            (codigo, res.get("status"), _causa_de(res)))
    t.igual("GE-E18 por CLI y lo que imprime es el result.json que quedo escrito",
            (_leido(proy, graph_run_id) or {}).get("resultado"), res)
    t.igual("GE-E18 por CLI ni C ni D tienen turno, y el Host solo recibio a A y a B", ([], ["a", "b"]),
            (_con_turno(proy, ("c", "d")), _bitacoras(bitacora)))
    _valida(t, "GE-E18 por CLI", proy, graph_run_id)
    codigo, salida, _ = _cli(proy, "--grafo")
    t.igual("GE-E18 por CLI sin --json, un segundo `--grafo` tambien sale con 2: B FAILED no se reintenta", 2, codigo)
    t.contiene("GE-E18 por CLI y dice FAILED, la causa y el nodo de B", "  b  NOT_SATISFIED  %s\n" % eid_b, salida)
    t.contiene("GE-E18 por CLI con el codigo de la causa", "  WORK_UNIT_NOT_SUCCEEDED · ", salida)


def test_ge_e05_por_cli_una_unidad_succeeded_por_ejecutar_unidad_se_adopta(t):
    """GE-E05 por el comando — Con A ya SUCCEEDED bajo F por un `ejecutar --unidad a` de verdad, `--grafo` no
    crea un turno para A, los archivos de la Execution de A quedan identicos byte a byte, el Host recibe dos
    invocaciones (B y C), el nodo A esta SATISFIED con `dispatched: false`, y sale con 0."""
    proy = _proyecto_abc()
    M72._guion(proy)
    codigo_a, salida_a, _ = _cli(proy, "--unidad", "a")
    eid_a = _eid_de(proy, "a")
    t.igual("GE-E05 por CLI `ejecutar --unidad a` sale con 0 y A queda SUCCEEDED", (0, "SUCCEEDED"),
            (codigo_a, registro.estado(str(proy), CLAVE, eid_a)["estado"]))
    t.contiene("GE-E05 por CLI y lo dice con la Execution", "%s a: SUCCEEDED" % eid_a, salida_a)
    antes = _bytes_de(proy, eid_a)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    codigo, salida, _ = _cli(proy, "--grafo", "--json")
    res = _doc(salida) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E05 por CLI `--grafo` sale con 0, SUCCEEDED", (0, "SUCCEEDED"), (codigo, res.get("status")))
    t.igual("GE-E05 por CLI A conserva su unico turno, el de la manual, y la Execution queda identica",
            ([(1, eid_a)], antes), (M72._turnos(proy, "a"), _bytes_de(proy, eid_a)))
    t.igual("GE-E05 por CLI solo B y C se despachan, y el Host recibe dos invocaciones", (
        [(1, "b"), (2, "c")], ["b", "c"]), (_despachos(proy, graph_run_id), _bitacoras(bitacora)))
    nodo_a = _nodos(res).get("a") or {}
    t.igual("GE-E05 por CLI el nodo A esta SATISFIED, con la Execution de la manual y dispatched: false",
            ("SATISFIED", 1, eid_a, False),
            (nodo_a.get("state"), nodo_a.get("turn"), nodo_a.get("executionId"), nodo_a.get("dispatched")))
    _valida(t, "GE-E05 por CLI", proy, graph_run_id)


def test_ge_e20_por_cli_una_unidad_fallida_no_se_reintenta_sola(t):
    """GE-E20 por el comando — Con A FAILED bajo F por un `ejecutar --unidad a` de verdad (sale con 2),
    `--grafo` no crea un turno para A, cierra con WORK_UNIT_NOT_SUCCEEDED, `dispatched: false`, y sale con 2.
    Despues de un `ejecutar --unidad a` que la deja SUCCEEDED, un `--grafo` nuevo despacha B y C, termina
    SUCCEEDED y sale con 0."""
    proy = _proyecto_abc()
    M72._guion(proy, por_unidad={"a": {"resultado": M72._informe("PARTIAL")}})
    codigo_a, _, _ = _cli(proy, "--unidad", "a")
    eid_a = _eid_de(proy, "a")
    t.igual("GE-E20 por CLI `ejecutar --unidad a` sale con 2 y A queda FAILED", (2, "FAILED"),
            (codigo_a, registro.estado(str(proy), CLAVE, eid_a)["estado"]))
    antes = _bytes_de(proy, eid_a)
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    codigo, salida, _ = _cli(proy, "--grafo", "--json")
    res = _doc(salida) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E20 por CLI `--grafo` sale con 2: FAILED con WORK_UNIT_NOT_SUCCEEDED por A FAILED",
            (2, "FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "a", eid_a, "FAILED", "AGENT_DECLARED_NOT_COMPLETE")),
            (codigo, res.get("status"), _causa_de(res)))
    t.igual("GE-E20 por CLI no crea un turno para A ni una marca, el Host no recibe nada, y A queda identica",
            ([(1, eid_a)], [], [], antes),
            (M72._turnos(proy, "a"), _despachos(proy, graph_run_id), _invocaciones(bitacora),
             _bytes_de(proy, eid_a)))
    t.igual("GE-E20 por CLI el nodo A esta NOT_SATISFIED, dispatched: false", ("NOT_SATISFIED", False),
            ((_nodos(res).get("a") or {}).get("state"), (_nodos(res).get("a") or {}).get("dispatched")))

    M72._guion(proy, bitacora=str(bitacora))
    reintento, _, _ = _cli(proy, "--unidad", "a")
    t.igual("GE-E20 por CLI el `--unidad a` de una persona sale con 0 y deja a A SUCCEEDED en el turno 2",
            (0, "SUCCEEDED", 2), (reintento, _estado_de(proy, "a"), (_ultimo(proy, "a") or {}).get("numero")))
    codigo, salida, _ = _cli(proy, "--grafo", "--json")
    otro = _doc(salida) or {}
    otro_id = otro.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E20 por CLI un `--grafo` nuevo adopta A, despacha B y C, termina SUCCEEDED y sale con 0",
            (0, "SUCCEEDED", [(1, "b"), (2, "c")], False),
            (codigo, otro.get("status"), _despachos(proy, otro_id), (_nodos(otro).get("a") or {}).get("dispatched")))
    _valida(t, "GE-E20 por CLI", proy, otro_id)


def test_ge_e19_por_cli_una_unidad_cancelada_con_cancelar_exe_no_cancela_el_grafo(t):
    """GE-E19 por el comando — Con B RUNNING bajo un `--grafo` de verdad (un proceso aparte), un `ejecutar
    <KEY> --cancelar <exe de B>` de verdad deja a B CANCELLED, C sin turno, y el `--grafo` sale con 2 con el
    GraphRun FAILED, WORK_UNIT_NOT_SUCCEEDED y `executionStatus: CANCELLED`: no CANCELLED, porque nadie
    cancelo el grafo (GC-22). `--cancelar exe_...` sale con 0, como siempre."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    conductor = _cli_vivo(proy, "--grafo", "--json")
    corriendo = _running_de(proy, "b")
    pid_del_host = ((M64._leer_json(corriendo / registro.PROCESO) or {}).get("pid")
                    if corriendo is not None else None)
    try:
        t.verdadero("GE-E19 por CLI B esta RUNNING, con el Host dormido", corriendo is not None)
        eid_b = _eid_de(proy, "b")
        codigo_c, salida_c, _ = _cli(proy, "--cancelar", eid_b, "--pedido-por", "ana", "--json")
        codigo_g, salida_g, _ = _fin_del_cli(conductor)
    finally:
        M72._terminar(pid_del_host)
        if conductor.poll() is None:
            conductor.kill()
    pedido, res = _doc(salida_c) or {}, _doc(salida_g) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E19 por CLI `--cancelar <exe de B>` sale con 0, y pidio cancelar esa Execution", (0, True, eid_b),
            (codigo_c, pedido.get("pedido"), pedido.get("executionId")))
    cancelacion = M72._carpeta(proy, eid_b) / registro.CANCELACION
    t.igual("GE-E19 por CLI B queda CANCELLED, con la cancelacion de `ana`", ("CANCELLED", "ana"),
            (registro.estado(str(proy), CLAVE, eid_b)["estado"],
             (M64._leer_json(cancelacion) if cancelacion.is_file() else {}).get("pedidoPor")))
    t.igual("GE-E19 por CLI el `--grafo` sale con 2: FAILED, no CANCELLED, con WORK_UNIT_NOT_SUCCEEDED por B CANCELLED",
            (2, "FAILED", ("WORK_UNIT_NOT_SUCCEEDED", "b", eid_b, "CANCELLED", "CANCELLED"), False),
            (codigo_g, res.get("status"), _causa_de(res), res.get("cancelRequested")))
    t.igual("GE-E19 por CLI C no tiene turno, no hay marca de cancelacion del grafo, y el Host recibio a A y a B",
            ([], False, ["a", "b"]),
            (_con_turno(proy, ("c",)), registro.cancelada(str(proy), CLAVE, graph_run_id), _bitacoras(bitacora)))
    _valida(t, "GE-E19 por CLI", proy, graph_run_id)


def test_ge_e69_por_cli_pedido_por_llega_a_cada_request_y_a_inicio_json(t):
    """GE-E69 por el comando — Con `--pedido-por ana`, cada request que despacha el GraphRun tiene
    `requestedBy: ana`, y tambien `inicio.json` y el resultado. Sin la opcion, es el `usuario` de
    harness.config.json. Una persona con un secreto se redacta igual en la request y en `inicio.json`, y el
    secreto no sale por stdout. En `--cancelar grf_...` la opcion es `pedidoPor` de `cancelacion.json`."""
    proy = _proyecto_abc()
    M72._guion(proy)
    codigo, salida, _ = _cli(proy, "--grafo", "--pedido-por", "ana", "--json")
    res = _doc(salida) or {}
    graph_run_id = res.get("graphRunId") or "grf_" + "0" * 32
    t.igual("GE-E69 por CLI cada request de A, B y C tiene requestedBy ana", (0, ["ana"] * 3),
            (codigo, [_request_de(proy, _eid_de(proy, u))["requestedBy"] for u in ("a", "b", "c")]))
    t.igual("GE-E69 por CLI inicio.json y el resultado tambien", ("ana", "ana"),
            ((_leido(proy, graph_run_id) or {"inicio": {}})["inicio"].get("requestedBy"), res.get("requestedBy")))
    _valida(t, "GE-E69 por CLI", proy, graph_run_id)

    de_config = _proyecto_abc()
    M72._config(de_config, usuario="Luisa de la config")
    M72._guion(de_config)
    codigo, salida, _ = _cli(de_config, "--grafo", "--json")
    res = _doc(salida) or {}
    t.igual("GE-E69 por CLI sin --pedido-por, es el `usuario` de harness.config.json, en la request y en inicio.json",
            (0, ["Luisa de la config"] * 3, "Luisa de la config"),
            (codigo, [_request_de(de_config, _eid_de(de_config, u))["requestedBy"] for u in ("a", "b", "c")],
             (_leido(de_config, res.get("graphRunId") or "grf_" + "0" * 32) or {"inicio": {}})
             ["inicio"].get("requestedBy")))

    con_secreto = _proyecto_abc()
    M72._guion(con_secreto)
    codigo, salida, error = _cli(con_secreto, "--grafo", "--pedido-por", "ana " + M72.SECRETO, "--json")
    res = _doc(salida) or {}
    por = (_leido(con_secreto, res.get("graphRunId") or "grf_" + "0" * 32) or {"inicio": {}})["inicio"].get(
        "requestedBy") or ""
    t.igual("GE-E69 por CLI con un secreto en --pedido-por, el GraphRun igual termina y sale con 0",
            (0, "SUCCEEDED"), (codigo, res.get("status")))
    t.no_contiene("GE-E69 por CLI inicio.json no lleva el secreto", M72.FUGA, por)
    t.igual("GE-E69 por CLI y es lo mismo que redacta la request", por,
            _request_de(con_secreto, _eid_de(con_secreto, "a"))["requestedBy"])
    t.no_contiene("GE-E69 por CLI ni stdout ni stderr lo nombran", M72.FUGA, salida + error)

    cortado = _proyecto_abc()
    M72._guion(cortado)
    _cortado(t, "GE-E69 por CLI", cortado, {"despues_del_retorno": {"unidad": "a", "morir": True}})
    (huerfano,) = _grafos(cortado)
    codigo, _, _ = _cli(cortado, "--cancelar", huerfano, "--pedido-por", "ana")
    pedido = M72._ejecuciones(cortado) / CLAVE / GRAFOS / huerfano / registro.CANCELACION
    t.igual("GE-E69 por CLI `--cancelar grf_... --pedido-por ana` sale con 0 y escribe pedidoPor: ana",
            (0, "ana"), (codigo, (M64._leer_json(pedido) if pedido.is_file() else {}).get("pedidoPor")))


def test_ge_e70_por_cli_grafo_estado_solo_lee_y_dice_como_cerrar_al_huerfano(t):
    """GE-E70 por el comando — `ejecutar <KEY> --grafo --estado`, con un GraphRun huerfano, lo muestra ACTIVE,
    con el comando que lo cierra, y despues de correrlo no cambio ningun archivo del proyecto: no recupera, no
    cierra huerfanos, no sondea el candado y no escribe. Sale con 0, en este proceso y en uno aparte."""
    proy = _proyecto_abc()
    M72._guion(proy)
    _cortado(t, "GE-E70 por CLI", proy, {"despues_del_retorno": {"unidad": "a", "morir": True}})
    (huerfano,) = _grafos(proy)
    eid_a = _eid_de(proy, "a")
    terminado = _proyecto_abc()
    M72._guion(terminado)
    _cli(terminado, "--grafo")
    antes, antes_del_terminado = M72._proyecto_sin_git(proy), M72._proyecto_sin_git(terminado)

    with _SinSondas():
        codigo_j, salida_j, error_j = _cli(proy, "--grafo", "--estado", "--json")
        codigo_h, salida_h, error_h = _cli(proy, "--grafo", "--estado")
        codigo_t, salida_t, _ = _cli(terminado, "--grafo", "--estado")
    t.igual("GE-E70 por CLI despues de correrlo no cambio ningun archivo del proyecto", [],
            M64._diferencias(antes, M72._proyecto_sin_git(proy)))
    t.igual("GE-E70 por CLI ni el del GraphRun terminal", [],
            M64._diferencias(antes_del_terminado, M72._proyecto_sin_git(terminado)))
    t.igual("GE-E70 por CLI sale con 0, con --json y sin el, y por stderr solo hay un documento limpio",
            (0, 0, 0, ""), (codigo_j, codigo_h, codigo_t, error_h))
    filas = _doc(salida_j)
    t.igual("GE-E70 por CLI --json es lo mismo que devuelve `estado_de_grafos`",
            grafo.estado_de_grafos(str(proy), CLAVE), filas)
    fila = (filas or [{}])[0]
    t.igual("GE-E70 por CLI el huerfano esta ACTIVE, con el comando para cerrarlo y su despacho de A SUCCEEDED",
            (huerfano, "ACTIVE", ["ejecutar %s --grafo" % CLAVE, "ejecutar %s --cancelar %s" % (CLAVE, huerfano)],
             [(1, "a", eid_a, "SUCCEEDED")]),
            (fila.get("graphRunId"), fila.get("estado"), fila.get("comandos"),
             [(d["numero"], d["workUnitId"], d["executionId"], d["estado"]) for d in fila.get("despachos") or []]))
    t.contiene("GE-E70 por CLI el texto lo muestra ACTIVE", "  %s  ACTIVE\n" % huerfano, salida_h)
    t.contiene("GE-E70 por CLI con su despacho, la Execution y el estado derivado",
               "      despacho 001  a  %s  SUCCEEDED\n" % eid_a, salida_h)
    t.contiene("GE-E70 por CLI y con el comando que lo cierra, si su proceso murio",
               "si su proceso murió, lo cierra `ejecutar %s --grafo` o `ejecutar %s --cancelar %s`"
               % (CLAVE, CLAVE, huerfano), salida_h)
    t.contiene("GE-E70 por CLI el terminal se muestra SUCCEEDED", "SUCCEEDED\n", salida_t)
    t.no_contiene("GE-E70 por CLI y sin el comando para cerrarlo", "si su proceso murió", salida_t)

    codigo_a, salida_a, _ = _cli_aparte(proy, "--grafo", "--estado", "--json")
    t.igual("GE-E70 por CLI en un proceso aparte tambien sale con 0, muestra lo mismo y no cambia nada",
            (0, filas, []),
            (codigo_a, _doc(salida_a), M64._diferencias(antes, M72._proyecto_sin_git(proy))))
    t.igual("GE-E70 por CLI el huerfano sigue ACTIVE y el candado de la tarea, libre", ("ACTIVE", True),
            ((_leido(proy, huerfano) or {}).get("estado"), _libre(proy)))


def test_ge_e51_por_cli_cancelar_un_huerfano_lo_cierra_cancelled_y_no_escribe_dos_veces(t):
    """GE-E51 y GE-E50 por el comando — Con el conductor muerto y el GraphRun ACTIVE, `--cancelar grf_...`
    toma el candado, escribe `cancelacion.json`, cierra el GraphRun CANCELLED y sale con 0. Un segundo
    `--cancelar` sobre el terminal lo informa y no escribe ningun archivo."""
    proy = _proyecto_abc()
    M72._guion(proy)
    _cortado(t, "GE-E51 por CLI", proy, {"despues_del_retorno": {"unidad": "a", "morir": True}})
    (huerfano,) = _grafos(proy)
    antes = _foto_de_grafo(proy, huerfano)
    codigo, salida, _ = _cli(proy, "--cancelar", huerfano, "--json")
    pedido = _doc(salida) or {}
    t.igual("GE-E51 por CLI sale con 0: estaba ACTIVE, queda CANCELLED, lo cerro este comando",
            (0, "ACTIVE", "CANCELLED", True, True, True, False, False),
            (codigo, pedido.get("antes"), pedido.get("despues"), pedido.get("pedido"), pedido.get("marcaNueva"),
             pedido.get("cerradoAqui"), pedido.get("conductorVivo"), pedido.get("sigue")))
    ahora = _foto_de_grafo(proy, huerfano)
    t.igual("GE-E51 por CLI el GraphRun solo gano su cancelacion.json y su result.json",
            ["cancelacion.json", "result.json"], sorted(set(ahora) - set(antes)))
    t.verdadero("GE-E51 por CLI y lo que ya tenia quedo identico", all(ahora.get(r) == h for r, h in antes.items()))
    doc = _valida(t, "GE-E51 por CLI", proy, huerfano) or {}
    t.igual("GE-E51 por CLI CANCELLED, sin error y con cancelRequested; A SATISFIED y los otros NOT_STARTED",
            ("CANCELLED", None, True, ["SATISFIED", "NOT_STARTED", "NOT_STARTED"]),
            (doc.get("status"), doc.get("error"), doc.get("cancelRequested"),
             [n["state"] for n in doc.get("nodes") or []]))
    antes_del_segundo = M72._proyecto_sin_git(proy)
    codigo, salida, _ = _cli(proy, "--cancelar", huerfano)
    t.igual("GE-E50 por CLI un segundo `--cancelar` sale con 0 y dice que no cambio nada",
            (0, "%s ya era CANCELLED: no se cambió nada.\n" % huerfano), (codigo, salida))
    t.igual("GE-E50 por CLI y no escribio ningun archivo: el GraphRun y el proyecto, identicos", ([], ahora),
            (M64._diferencias(antes_del_segundo, M72._proyecto_sin_git(proy)),
             _foto_de_grafo(proy, huerfano)))


def test_ge_e50_por_cli_cancelar_un_terminal_no_escribe_y_un_graphrun_que_no_existe_es_un_error(t):
    """GE-E50 por el comando — `--cancelar grf_...` sobre un GraphRun terminal sale con 0, lo informa y no
    escribe ningun archivo. Sobre uno que no existe, o que es de otra tarea, es un error del comando: sale con
    2 y no escribe nada."""
    proy = _proyecto_abc()
    M72._guion(proy)
    _, salida, _ = _cli(proy, "--grafo", "--json")
    graph_run_id = (_doc(salida) or {}).get("graphRunId") or "grf_" + "0" * 32
    antes = M72._proyecto_sin_git(proy)
    codigo, texto, error = _cli(proy, "--cancelar", graph_run_id)
    t.igual("GE-E50 por CLI sobre un terminal sale con 0, dice que ya era SUCCEEDED y no cambia nada",
            (0, "%s ya era SUCCEEDED: no se cambió nada.\n" % graph_run_id, ""), (codigo, texto, error))
    codigo, salida, _ = _cli(proy, "--cancelar", graph_run_id, "--json")
    informe = _doc(salida) or {}
    t.igual("GE-E50 por CLI con --json imprime el informe: no hubo pedido ni marca, ya era terminal",
            (0, "SUCCEEDED", False, False), (codigo, informe.get("antes"), informe.get("pedido"),
                                             informe.get("marcaNueva")))
    t.igual("GE-E50 por CLI no escribio ningun archivo, ni la marca", ([], False),
            (M64._diferencias(antes, M72._proyecto_sin_git(proy)),
             (M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id / registro.CANCELACION).exists()))
    codigo, salida, error = _cli(proy, "--cancelar", "grf_" + "e" * 32)
    t.igual("GE-E50 por CLI sobre uno que no existe sale con 2, como error del comando, sin nada por stdout",
            (2, ""), (codigo, salida))
    t.contiene("GE-E50 por CLI y dice que no es un GraphRun de la tarea", "no es un GraphRun de %s" % CLAVE, error)
    codigo, salida, error = _correr_cli(_modulo_del_cli("dev_harness_ge73", CLI),
                                        ["ejecutar", "GCBA-99", "--cancelar", graph_run_id, "--proyecto", proy])
    t.igual("GE-E50 por CLI sobre un GraphRun de otra tarea tambien: sale con 2, sin stdout",
            (2, ""), (codigo, salida))
    t.contiene("GE-E50 por CLI y dice que no es un GraphRun de esa tarea", "no es un GraphRun de GCBA-99", error)
    t.igual("GE-E50 por CLI y los dos errores no escribieron nada", [],
            M64._diferencias(antes, M72._proyecto_sin_git(proy)))


def test_ge_e46_por_cli_cancelar_con_el_conductor_detenido_despues_de_a(t):
    """GE-E46 por el comando — Con el conductor detenido en el gancho posterior a A, `ejecutar --cancelar
    grf_...` de verdad, desde otro proceso, escribe `cancelacion.json` y no el terminal; al seguir, el
    conductor no despacha B y cierra CANCELLED, con `cancelRequested: true`; A queda identica, y el comando
    vuelve con el terminal ya escrito y sale con 0."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora))
    marcas = M64._tmp("ge73-marcas-")
    conductor = _conductor(proy, marcas, ganchos={"despues_del_retorno": {"unidad": "a", "esperar": ["seguir"]}})
    cancelador = None
    try:
        t.verdadero("GE-E46 por CLI el conductor llego al gancho posterior a A",
                    _esperar_marca(marcas, "despues_del_retorno.a"))
        (graph_run_id,) = _grafos(proy)
        eid_a = _eid_de(proy, "a")
        a_antes = _bytes_de(proy, eid_a)
        carpeta = M72._ejecuciones(proy) / CLAVE / GRAFOS / graph_run_id
        cancelador = _cli_vivo(proy, "--cancelar", graph_run_id, "--pedido-por", "ana")
        t.verdadero("GE-E46 por CLI el comando escribe cancelacion.json", M72._esperar(
            lambda: (carpeta / registro.CANCELACION).is_file(), 60))
        t.igual("GE-E46 por CLI y no el terminal: el conductor sigue vivo, y el GraphRun, ACTIVE",
                (False, "ACTIVE"), ((carpeta / registro.RESULT).exists(), (_leido(proy, graph_run_id) or {}).get("estado")))
    finally:
        _dejar_marca(marcas, "seguir")
    sal = _salida(conductor)
    res = sal.get("res") or {}
    codigo, texto, error = _fin_del_cli(cancelador) if cancelador is not None else (None, "", "")
    t.igual("GE-E46 por CLI al seguir, el conductor no despacha B y cierra CANCELLED, con cancelRequested",
            (None, "CANCELLED", None, True, [(1, "a")], None),
            (sal.get("exc"), res.get("status"), res.get("error"), res.get("cancelRequested"),
             _despachos(proy, graph_run_id), _ultimo(proy, "b")))
    t.igual("GE-E46 por CLI el comando vuelve con el terminal ya escrito y sale con 0", (0, ""), (codigo, error))
    t.contiene("GE-E46 por CLI y lo dice: CANCELLED", "Se pidió cancelar %s: ahora está CANCELLED." % graph_run_id,
               texto)
    t.igual("GE-E46 por CLI cancelacion.json trae quien pidio, y A queda identica", ("ana", a_antes),
            (M64._leer_json(carpeta / registro.CANCELACION).get("pedidoPor"), _bytes_de(proy, eid_a)))
    _valida(t, "GE-E46 por CLI", proy, graph_run_id)


def test_ge_e47_por_cli_cancelar_con_b_running_y_el_grafo_sale_con_2(t):
    """GE-E47 por el comando — Con B RUNNING bajo un `--grafo` de verdad, `ejecutar --cancelar grf_...` de
    verdad deja a B CANCELLED por el camino de Task 4, con el arbol del Host terminado; C no tiene turno; el
    comando vuelve con el terminal ya escrito y sale con 0; y el `--grafo` sale con 2 con el GraphRun
    CANCELLED (CANCELLED sale con 2, como FAILED)."""
    proy = _proyecto_abc()
    bitacora = _ruta_de_bitacora()
    M72._guion(proy, bitacora=str(bitacora), por_unidad={"b": {"dormir": 60}})
    conductor = _cli_vivo(proy, "--grafo", "--json")
    corriendo = _running_de(proy, "b")
    pid_del_host = ((M64._leer_json(corriendo / registro.PROCESO) or {}).get("pid")
                    if corriendo is not None else None)
    try:
        t.verdadero("GE-E47 por CLI B esta RUNNING, con el Host dormido", corriendo is not None)
        (graph_run_id,) = _grafos(proy)
        eid_b = _eid_de(proy, "b")
        codigo_c, salida_c, _ = _cli(proy, "--cancelar", graph_run_id, "--json")
        codigo_g, salida_g, _ = _fin_del_cli(conductor)
        t.verdadero("GE-E47 por CLI con el arbol del Host terminado",
                    pid_del_host is not None and M72._esperar(lambda: not proceso.pid_vivo(pid_del_host), 20))
    finally:
        M72._terminar(pid_del_host)
        if conductor.poll() is None:
            conductor.kill()
    pedido, res = _doc(salida_c) or {}, _doc(salida_g) or {}
    t.igual("GE-E47 por CLI `--cancelar grf_...` sale con 0, con el terminal ya escrito: el conductor vivo, "
            "y la unica Execution propia abierta, la de B", (0, "ACTIVE", "CANCELLED", True, False, [eid_b]),
            (codigo_c, pedido.get("antes"), pedido.get("despues"), pedido.get("conductorVivo"),
             pedido.get("sigue"), pedido.get("canceladas")))
    t.igual("GE-E47 por CLI el `--grafo` sale con 2, con el GraphRun CANCELLED, sin error y con cancelRequested",
            (2, "CANCELLED", None, True),
            (codigo_g, res.get("status"), res.get("error"), res.get("cancelRequested")))
    t.igual("GE-E47 por CLI B queda CANCELLED con su cancelacion.json, y C no tiene turno ni marca",
            ("CANCELLED", True, None, [(1, "a"), (2, "b")]),
            (registro.estado(str(proy), CLAVE, eid_b)["estado"],
             (M72._carpeta(proy, eid_b) / registro.CANCELACION).is_file(), _ultimo(proy, "c"),
             _despachos(proy, graph_run_id)))
    t.igual("GE-E47 por CLI ningun GraphRun ACTIVE, ninguna Execution propia abierta, y el candado libre",
            ([], [], True), (registro.activos(str(proy), CLAVE), _sin_propias_abiertas(proy, graph_run_id),
                             _libre(proy)))
    _valida(t, "GE-E47 por CLI", proy, graph_run_id)


def test_ge_e63_por_cli_grafo_sale_con_0_solo_con_succeeded_y_json_imprime_el_resultado(t):
    """GE-E63 — `--grafo` sale con 0 solo con SUCCEEDED, con 2 con FAILED y con 2 con un rechazo al arrancar
    (con CANCELLED tambien: GE-E47); con `--json` imprime en stdout el `result.json` o el rechazo, y nada mas:
    los eventos van a stderr. Corre en un proceso aparte, que es lo que ve quien lo corre."""
    proy = _proyecto_abc()
    M72._guion(proy)
    codigo, salida, error = _cli_aparte(proy, "--grafo", "--json")
    ids = _grafos(proy)
    t.igual("GE-E63 SUCCEEDED sale con 0, y --json imprime ese estado", (0, "SUCCEEDED"),
            (codigo, (_doc(salida) or {}).get("status")))
    t.igual("GE-E63 y lo que imprime es el result.json que quedo escrito",
            (_leido(proy, ids[0]) or {}).get("resultado") if ids else None, _doc(salida))
    t.contiene("GE-E63 los eventos van a stderr", "evento=grafo.pedido", error)
    t.no_contiene("GE-E63 y no a stdout, que es el documento", "evento=", salida)

    fallido = _proyecto_abc()
    M72._guion(fallido, por_unidad={"b": {"resultado": M72._informe("PARTIAL")}})
    codigo, salida, _ = _cli_aparte(fallido, "--grafo", "--json")
    doc = _doc(salida) or {}
    t.igual("GE-E63 FAILED sale con 2, con el documento FAILED", (2, "FAILED", "WORK_UNIT_NOT_SUCCEEDED"),
            (codigo, doc.get("status"), (doc.get("error") or {}).get("code")))
    codigo, salida, _ = _cli(fallido, "--grafo")
    t.igual("GE-E63 sin --json tambien sale con 2, y el texto dice FAILED con su causa", (2, 2, True, True), (
        codigo, len(_grafos(fallido)),
        any("%s %s: FAILED\n" % (g, CLAVE) in salida for g in _grafos(fallido)),
        "  WORK_UNIT_NOT_SUCCEEDED · " in salida))

    ya = _proyecto_abc()
    M72._guion(ya)
    marcas = M64._tmp("ge73-marcas-")
    dueno = _lanzar("candado", ya, marcas, "esperar")
    try:
        t.verdadero("GE-E63 otro proceso tiene el candado de la tarea", _esperar_marca(marcas, "l.tomado"))
        codigo, salida, _ = _cli_aparte(ya, "--grafo", "--json")
        rechazo = _doc(salida) or {}
        t.igual("GE-E63 un rechazo al arrancar sale con 2, y --json imprime el rechazo: GRAPH_ALREADY_ACTIVE",
                (2, ["code", "detail"], "GRAPH_ALREADY_ACTIVE"), (codigo, sorted(rechazo), rechazo.get("code")))
        codigo, salida, _ = _cli(ya, "--grafo")
        t.igual("GE-E63 sin --json lo dice en una linea y sale con 2", (2, True), (
            codigo, ("No arrancó el GraphRun de %s: GRAPH_ALREADY_ACTIVE · " % CLAVE) in salida))
        t.igual("GE-E63 y no creo un GraphRun ni una Execution", ([], []), (_grafos(ya), M72._carpetas(ya)))
    finally:
        _dejar_marca(marcas, "l.soltar")
        _salida(dueno)


def test_ge_e63_por_cli_una_sola_opcion_y_un_id_que_no_es_valido_es_un_error_del_comando(t):
    """GE-E63 — `--grafo --unidad b` es un error del comando, como toda combinacion que no sea `--grafo
    --estado`; `--cancelar` con un id que no es `exe_...` ni `grf_...` valido es un error del comando; y sin
    catalogo de secretos el GraphRun no arranca. Salen con 2, sin crear ni cambiar nada."""
    proy = _proyecto_abc()
    M72._guion(proy)
    antes = M72._proyecto_sin_git(proy)
    exe, grf = "exe_" + "0" * 32, "grf_" + "0" * 32
    combinaciones = (["--grafo", "--unidad", "b"], ["--grafo", "--cancelar", grf], ["--grafo", "--recuperar"],
                     ["--grafo", "--estado", "--unidad", "b"], ["--grafo", "--estado", "--recuperar"],
                     ["--grafo", "--estado", "--cancelar", grf], ["--estado", "--unidad", "b"],
                     ["--estado", "--recuperar"], ["--unidad", "a", "--cancelar", exe], [])
    for args in combinaciones:
        codigo, salida, error = _cli(proy, *args)
        t.igual("GE-E63 por CLI `ejecutar %s`: sale con 2, sin salida, y pide una sola opcion" % " ".join(args),
                (2, "", True), (codigo, salida, "ejecutar necesita una sola de" in error))
    t.igual("GE-E63 por CLI ninguna combinacion invalida toco el proyecto ni creo `.claude/ejecuciones`",
            (antes, False), (M72._proyecto_sin_git(proy), M72._ejecuciones(proy).exists()))
    codigo, salida, _ = _cli(proy, "--grafo", "--estado")
    t.igual("GE-E63 por CLI `--grafo --estado` si se admite: sale con 0, y no hay GraphRuns", (0, True, False),
            (codigo, "GraphRuns de %s: 0\n" % CLAVE in salida, M72._ejecuciones(proy).exists()))

    invalidos = ("basura", "exe_", "exe_" + "0" * 31, "EXE_" + "0" * 32, "../" + grf, "grf_", "grf_basura",
                 "grf_" + "0" * 31, "grf_" + "0" * 31 + "G", "grf_" + "0" * 33, "GRF_" + "0" * 32, grf + "/..")
    for valor in invalidos:
        codigo, salida, error = _cli(proy, "--cancelar", valor)
        t.igual("GE-E63 por CLI `--cancelar %s` es un error del comando: sale con 2, sin stdout" % valor,
                (2, "", True), (codigo, salida, error.startswith("harness: ")))
    for valor, texto in ((exe, "no es una Execution de %s" % CLAVE), (grf, "no es un GraphRun de %s" % CLAVE)):
        codigo, salida, error = _cli(proy, "--cancelar", valor)
        t.igual("GE-E63 por CLI `--cancelar %s` valido y sin dueno: sale con 2 y dice por que" % valor[:8],
                (2, True), (codigo, texto in error))
    t.igual("GE-E63 por CLI y ninguno de los ids invalidos toco el proyecto", antes, M72._proyecto_sin_git(proy))

    real = limpieza.cargar_catalogo

    def sin_catalogo(*a, **k):
        raise OSError("sin catalogo de secretos")

    limpieza.cargar_catalogo = sin_catalogo
    try:
        codigo, salida, error = _cli(proy, "--grafo")
    finally:
        limpieza.cargar_catalogo = real
    t.igual("GE-E63 por CLI sin catalogo de secretos `--grafo` no arranca: error del comando, sale con 2 "
            "(antes del error, dice el evento, como `--unidad`)",
            (2, "  evento=grafo.pedido tarea=%s\n" % CLAVE, True),
            (codigo, salida, error.startswith("harness: ") and "catalogo de secretos" in error))
    t.igual("GE-E63 por CLI y no creo un GraphRun, ni una Execution", ([], []), (_grafos(proy), M72._carpetas(proy)))


def _normalizar(texto, proy):
    """La salida de un comando sin lo que cambia de un proyecto a otro igual: la ruta, los ids de Execution,
    las fechas y las huellas."""
    for ruta in (str(proy), str(proy).replace("\\", "/")):
        texto = texto.replace(ruta, "<proyecto>")
    texto = re.sub(r"exe_[0-9a-f]{32}", "exe_X", texto)
    texto = re.sub(r"\d{4}-\d\d-\d\dT[\d:.]+Z", "<fecha>", texto)
    return re.sub(r"sha256:[0-9a-f]{64}", "sha256:<huella>", texto)


def _secuencia_de_siempre(viejo, ahora):
    """Las opciones de `ejecutar` que no cambian, una detras de otra, con el `dev-harness.main` de 0.32.0
    (`viejo`) y el de ahora: [(opciones, codigo de 0.32.0, el de ahora, salida de 0.32.0, la de ahora)].

    Lo que escribe en disco corre en dos proyectos gemelos, cada CLI en el suyo, y se compara normalizado.
    Lo que solo lee corre las dos CLI sobre el mismo proyecto: el orden de los turnos de `--estado` sale de
    la huella del plan, que cambia de un proyecto a otro."""
    unidades = [M64._unidad("a"), M64._unidad("b", dependencias=("a",)), M64._unidad("d")]
    gemelos = (M72._proyecto(unidades), M72._proyecto(unidades))
    por_unidad = {"b": {"resultado": M72._informe("PARTIAL")}}
    pasos = []

    def correr(modulo, proy, args):
        M72._guion(proy, por_unidad=por_unidad)
        codigo, salida, error = _correr_cli(modulo, ["ejecutar", CLAVE] + list(args) + ["--proyecto", proy])
        return codigo, _normalizar(salida, proy), _normalizar(error, proy)

    def escribe(args_de):
        """Lo que escribe: 0.32.0 en el primer proyecto, el de ahora en el segundo."""
        (c0, s0, e0), (c1, s1, e1) = (correr(viejo, gemelos[0], args_de(gemelos[0])),
                                      correr(ahora, gemelos[1], args_de(gemelos[1])))
        pasos.append((_normalizar(" ".join(args_de(gemelos[1])), gemelos[1]), c0, c1, (s0, e0), (s1, e1)))

    def lee(*args):
        """Lo que solo lee: las dos CLI sobre el segundo proyecto."""
        (c0, s0, e0), (c1, s1, e1) = (correr(viejo, gemelos[1], args), correr(ahora, gemelos[1], args))
        pasos.append((_normalizar(" ".join(args), gemelos[1]), c0, c1, (s0, e0), (s1, e1)))

    escribe(lambda p: ["--unidad", "a"])
    escribe(lambda p: ["--unidad", "b"])
    escribe(lambda p: ["--unidad", "no-existe"])
    lee("--estado")
    lee("--estado", "--json")
    lee("--cancelar", _eid_de(gemelos[1], "b"))
    lee("--cancelar", _eid_de(gemelos[1], "a"), "--pedido-por", "ana")
    lee("--cancelar", "basura")
    lee("--cancelar", "exe_" + "0" * 32)
    lee("--recuperar")
    lee("--recuperar", "--json")
    huerfanas = [_requested_sin_motor(p, "d")["executionId"] for p in gemelos]
    lee("--estado")
    escribe(lambda p: ["--cancelar", huerfanas[gemelos.index(p)]])
    lee("--estado")
    lee("--recuperar")
    return gemelos, pasos


def test_ge_e63_por_cli_las_opciones_de_siempre_dan_la_misma_salida_que_en_0_32_0(t):
    """GE-E63 — `ejecutar --unidad`, `--estado`, `--recuperar` y `--cancelar exe_...` dan la misma salida y el
    mismo codigo que en 0.32.0: el `dev-harness.py` de `e33b41b`, tal cual esta en git, corre contra los
    mismos modulos de bin/ la misma secuencia sobre un proyecto gemelo, y se comparan paso a paso (ids de
    Execution, fechas y huellas normalizados). Lo unico que cambia es el texto del error de «una sola
    opcion», que ahora nombra `--grafo`."""
    codigo, _ = M72._git_raiz("cat-file", "-e", BASE_0_32_0 + "^{commit}")
    t.igual("GE-E63 la base 0.32.0 (%s) esta en este clon" % BASE_0_32_0[:7], 0, codigo)
    if codigo != 0:
        return
    git = subprocess.run(["git", "-C", str(RAIZ), "show", "%s:harnesses/desarrollo/bin/dev-harness.py"
                          % BASE_0_32_0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ruta = M64._tmp("ge73-cli-0-32-0-") / "dev-harness.py"
    ruta.write_bytes(git.stdout)
    t.verdadero("GE-E63 el dev-harness.py de 0.32.0 no tiene `--grafo`", b"--grafo" not in git.stdout)
    viejo = _modulo_del_cli("dev_harness_0_32_0", ruta)
    ahora = _modulo_del_cli("dev_harness_ge73", CLI)
    (proy_viejo, proy_nuevo), pasos = _secuencia_de_siempre(viejo, ahora)
    t.igual("GE-E63 por CLI los codigos de salida de 0.32.0 y los de ahora son los mismos, paso a paso",
            [(o, c0) for o, c0, _, _, _ in pasos], [(o, c1) for o, _, c1, _, _ in pasos])
    t.igual("GE-E63 por CLI y son los esperados: --unidad 0, 2 y 2; --estado 0; --cancelar 0, 0, 2 y 2; "
            "--recuperar 0", [0, 2, 2, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0], [c1 for _, _, c1, _, _ in pasos])
    for opciones, _, _, de_0_32_0, de_ahora in pasos:
        t.igual("GE-E63 por CLI `ejecutar %s` da la misma salida (stdout y stderr) que en 0.32.0" % opciones,
                de_0_32_0, de_ahora)
    t.verdadero("GE-E63 por CLI y la secuencia es de verdad: cada paso que sale con 0 imprimio algo",
                all(s for _, _, c1, _, (s, _) in pasos if c1 == 0))
    t.igual("GE-E63 por CLI y los dos proyectos terminaron con tres Executions: A, B y la REQUESTED de D",
            (3, 3), (len(M72._carpetas(proy_viejo)), len(M72._carpetas(proy_nuevo))))

    exe = "exe_" + "0" * 32
    for args in (["--unidad", "a", "--estado"], ["--cancelar", exe, "--recuperar"], []):
        resultados = []
        for modulo in (viejo, ahora):
            resultados.append(_correr_cli(modulo, ["ejecutar", CLAVE] + args + ["--proyecto", proy_nuevo]))
        t.igual("GE-E63 por CLI `ejecutar %s` (dos opciones, o ninguna) sale con 2 en las dos, sin salida"
                % " ".join(args), ((2, ""), (2, "")), tuple((c, s) for c, s, _ in resultados))
        t.contiene("GE-E63 por CLI y el error de ahora nombra --grafo", "--recuperar o --grafo",
                   resultados[1][2])
        t.contiene("GE-E63 por CLI mientras el de 0.32.0 no lo conocia", "ejecutar necesita una sola de "
                   "--unidad, --cancelar, --estado o --recuperar.", resultados[0][2])


def test_ge_e64_por_cli_siguen_los_trece_subcomandos_y_grafo_es_una_opcion_de_ejecutar(t):
    """GE-E64 en lo que toca a la CLI — dev-harness.py sigue con trece subcomandos, con `ejecutar`, sin un
    subcomando nuevo: `--grafo` es una opcion de `ejecutar`, y la unica opcion nueva del parser (`--estado`
    y `--cancelar` ya existian). De `ejecucion` importa `motor` y `grafo`, y nada mas."""
    subcomandos = M72._subcomandos() or []
    t.igual("GE-E64 por CLI dev-harness.py tiene trece subcomandos, con ejecutar", (13, True),
            (len(subcomandos), "ejecutar" in subcomandos))
    t.vacio("GE-E64 por CLI y ninguno se llama grafo ni nada que lo nombre", [s for s in subcomandos if "graf" in s])
    ahora = _modulo_del_cli("dev_harness_ge73", CLI)
    uno = ahora.parser().parse_args(["ejecutar", CLAVE, "--grafo"])
    dos = ahora.parser().parse_args(["ejecutar", CLAVE, "--grafo", "--estado", "--json"])
    t.igual("GE-E64 por CLI `--grafo` es una opcion de `ejecutar`, y se combina con `--estado` y `--json`",
            (("ejecutar", True, False, ""), (True, True, True)),
            ((uno.comando, uno.ejecutar_grafo, uno.ejecutar_estado, uno.ejecutar_cancelar),
             (dos.ejecutar_grafo, dos.ejecutar_estado, dos.json)))

    def opciones(modulo):
        return sorted(o for a in modulo.parser()._actions for o in a.option_strings)

    codigo, _ = M72._git_raiz("cat-file", "-e", BASE_0_32_0 + "^{commit}")
    if codigo == 0:
        git = subprocess.run(["git", "-C", str(RAIZ), "show", "%s:harnesses/desarrollo/bin/dev-harness.py"
                              % BASE_0_32_0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ruta = M64._tmp("ge73-cli-0-32-0-") / "dev-harness.py"
        ruta.write_bytes(git.stdout)
        t.igual("GE-E64 por CLI las opciones del parser son las de 0.32.0 mas `--grafo`, y ninguna otra",
                sorted(opciones(_modulo_del_cli("dev_harness_0_32_0", ruta)) + ["--grafo"]), opciones(ahora))
    else:
        t.verdadero("GE-E64 por CLI la base 0.32.0 esta en este clon", False)
    importados = sorted(a.name for n in ast.walk(ast.parse(CLI.read_text(encoding="utf-8")))
                        if isinstance(n, ast.ImportFrom) and n.module == "ejecucion" for a in n.names)
    t.igual("GE-E64 por CLI de `ejecucion`, dev-harness.py importa motor y grafo, y nada mas",
            ["grafo", "motor"], importados)


# =============================================================================================
# 7: la integracion -- lo que no se toca y lo que dicen los documentos (GE-E65, GE-E67)
# =============================================================================================
#
# GE-E65 compara contra `e33b41b` (el clon tiene .git, como ME-E49 de la 72). GE-E67 lee el modelo canonico
# con los lectores de la 64, y corre E-09 de la 64 sobre un `Resultados` aparte para ver que sigue verde sin
# contarlo dos veces. Las dos frases de MC de la enmienda 27.1 H (la introduccion y la apertura de «El limite de
# la ejecucion») se leen aca, con el texto exacto de la fila de la seccion 28 de la spec, sin los realces.

PROTEGIDOS_DE_LA_BASE = (
    "harnesses/desarrollo/bin/ejecucion/contrato.py",
    "comun/schemas/execution-request.schema.json",
    "comun/schemas/execution-result.schema.json",
    "docs/adr/0013-modelo-de-dominio-canonico.md",
    "docs/adr/0014-el-contrato-de-ejecucion.md",
    "docs/adr/0015-el-motor-minimo-de-ejecucion.md",
)
ADR_16 = RAIZ / "docs" / "adr" / "0016-la-ejecucion-de-un-grafo.md"


def _sha_sin_cr(datos):
    """El sha256 de unos bytes con los finales de linea en LF: el arbol de trabajo puede tenerlos CRLF y el blob
    de git, no."""
    return hashlib.sha256(datos.replace(b"\r\n", b"\n")).hexdigest()


def _sin_realces(texto):
    """El texto en una sola linea y sin los `*` ni los acentos graves del markdown."""
    return " ".join(re.sub(r"[*`]", "", texto or "").split())


def test_ge_e65_contrato_los_dos_schemas_y_los_tres_adr_tienen_la_huella_de_0_32_0(t):
    """GE-E65 (GE-I02) — `contrato.py`, `execution-request.schema.json`, `execution-result.schema.json` y ADR-0013,
    ADR-0014 y ADR-0015 tienen la misma huella que en `e33b41b`: el sha256 del archivo es el del blob de esa base
    (sin contar CRLF o LF), y git no ve una diferencia contra ella."""
    codigo, _ = M72._git_raiz("cat-file", "-e", BASE_0_32_0 + "^{commit}")
    t.igual("GE-E65 la base 0.32.0 (%s) esta en este clon" % BASE_0_32_0[:7], 0, codigo)
    if codigo != 0:
        return
    for ruta in PROTEGIDOS_DE_LA_BASE:
        git = subprocess.run(["git", "-C", str(RAIZ), "show", "%s:%s" % (BASE_0_32_0, ruta)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        archivo = RAIZ / ruta
        t.igual("GE-E65 %s esta en la base, y su huella es la de %s" % (ruta, BASE_0_32_0[:7]),
                (0, _sha_sin_cr(git.stdout)),
                (git.returncode, _sha_sin_cr(archivo.read_bytes()) if archivo.is_file() else None))
        diferencia, _ = M72._git_raiz("diff", "--quiet", BASE_0_32_0, "--", ruta)
        t.igual("GE-E65 %s no tiene una diferencia contra %s en git" % (ruta, BASE_0_32_0[:7]), 0, diferencia)


def test_ge_e67_el_modelo_canonico_tiene_la_ficha_de_graphrun_y_la_fila_de_run_enmendada(t):
    """GE-E67 — MC tiene la ficha de GraphRun (y la de GraphRunError) en el contexto Execution, la fila «run /
    corrida» enmendada y la fila nueva «grafo / GraphRun»; E-09 de t64 sigue verde; y las dos frases que la
    enmienda 27.1 H cambia (la introduccion y la apertura de «El limite de la ejecucion») dicen `--unidad` y el
    GraphRun, con el texto exacto de la seccion 28 de la spec."""
    m = M64._modelo()
    filas = {f[0]: f for f in m["filas"] if f}
    for concepto, clasificacion in (("GraphRun", "Aggregate Root"), ("GraphRunError", "Value Object")):
        campos = m["campos"].get(concepto) or {}
        t.igual("GE-E67 %s esta en el catalogo, en el contexto Execution, como %s" % (concepto, clasificacion),
                ("Execution", clasificacion), tuple((filas.get(concepto) or [])[1:3]))
        t.igual("GE-E67 y su ficha dice lo mismo: Contexto y Clasificacion de %s" % concepto,
                ("Execution", clasificacion),
                (M64._valor(campos.get("Contexto")), M64._valor(campos.get("Clasificación"))))
    ficha = m["campos"].get("GraphRun") or {}
    for invariante in ("GE-I03", "GE-I10", "GE-I13", "GE-I15", "GE-I16"):
        t.contiene("GE-E67 la ficha de GraphRun nombra %s" % invariante, invariante,
                   ficha.get("Invariantes"))
    t.contiene("GE-E67 la ficha de GraphRun nombra su schema en «Persistencia y contrato»",
               "graph-run-result.schema.json", ficha.get("Persistencia y contrato"))
    t.contiene("GE-E67 y a `grafo.py` como el que lo crea y lo lee", "grafo.py", ficha.get("Crea / cambia / lee"))
    t.contiene("GE-E67 y la ficha de GraphRunError dice que son nueve codigos", "nueve códigos",
               (m["campos"].get("GraphRunError") or {}).get("Ciclo y estados"))

    vocabulario = {f[0]: f for tabla in M64._tablas(M64._seccion(m["texto"], "Vocabulario")) for f in tabla if f}
    run = _sin_realces(" | ".join(vocabulario.get("run / corrida") or []))
    t.contiene("GE-E67 la fila «run / corrida» dice que en Execution se usa solo como GraphRun, nunca para una "
               "Execution", "en Execution se usa solo como GraphRun, nunca para una Execution", run)
    t.no_contiene("GE-E67 y ya no dice que en Execution no se usa", "en Execution no se usa", run)
    t.contiene("GE-E67 y sigue siendo de Refutation fuera de Execution", "Refutation", run)
    t.contiene("GE-E67 la fila «grafo / GraphRun» dice que no es una Execution ni un estado del Plan",
               "no es una Execution ni un estado del Plan",
               _sin_realces(" | ".join(vocabulario.get("grafo / GraphRun") or [])))

    r = M72._resultados()
    M64.test_e09_el_limite_de_la_ejecucion(r)
    t.verdadero("GE-E67 E-09 de t64 corrio: puso sus aserciones", len(r.filas) > 0)
    t.vacio("GE-E67 E-09 de t64 sigue verde", [(nombre, detalle) for _, nombre, ok, detalle in r.filas if not ok])

    introduccion = _sin_realces(m["texto"].split("\n## Conceptos", 1)[0])
    t.contiene("GE-E67 (27.1 H) la introduccion dice que el motor corre una WorkUnit por invocacion de `ejecutar "
               "--unidad`, y que desde Task 5 tiene tambien el GraphRun",
               "una WorkUnit por invocación de ejecutar --unidad. Desde Task 5 tiene también el GraphRun "
               "([docs/cambios/graph-execution/spec.md](../cambios/graph-execution/spec.md) y "
               "[ADR-0016](../adr/0016-la-ejecucion-de-un-grafo.md)):", introduccion)
    t.contiene("GE-E67 (27.1 H) y que `ejecutar --grafo` lleva un plan entero a un terminal, de a una WorkUnit por "
               "vez", "ejecutar --grafo lleva un plan entero a un terminal, de a una WorkUnit por vez.", introduccion)
    t.no_contiene("GE-E67 (27.1 H) y la introduccion ya no dice una WorkUnit por invocacion de `ejecutar` a secas",
                  "una WorkUnit por invocación de ejecutar.", introduccion)
    apertura = []
    for linea in M64._seccion(m["texto"], "El límite de la ejecución"):
        if linea.startswith("### "):
            break
        apertura.append(linea)
    apertura = _sin_realces("\n".join(apertura))
    for frase in ("Desde ADR-0014, Execution es un contexto; desde ADR-0015 tiene un motor mínimo, y desde "
                  "ADR-0016, el GraphRun.",
                  "HARNESS ejecuta una WorkUnit por invocación de dev-harness.py ejecutar --unidad, un intento, "
                  "sincrónico: la admite, crea la Execution, la entrega al Host y deja su resultado.",
                  "Con ejecutar --grafo, un GraphRun elige la siguiente, en el orden de orden_de_ejecucion, de a "
                  "una: cada una pasa por el mismo motor y por las mismas dos admisiones. Más de una a la vez no "
                  "existe."):
        t.contiene("GE-E67 (27.1 H) la apertura de «El limite de la ejecucion» dice: %s" % frase[:50], frase,
                   apertura)
    t.no_contiene("GE-E67 (27.1 H) y ya no deja la siguiente en manos de quien invoca, y de Task 5",
                  "es de quien invoca, y de Task 5", apertura)


def test_ge_e67_adr_0016_existe_y_nombra_la_revision_de_adr_0015(t):
    """GE-E67 (GD-26) — `docs/adr/0016-la-ejecucion-de-un-grafo.md` existe, y su apartado «Revision» dice que
    revisa ADR-0015; registra las siete decisiones de la seccion 29, de la 1 a la 7."""
    texto = ADR_16.read_text(encoding="utf-8") if ADR_16.is_file() else ""
    t.verdadero("GE-E67 ADR-0016 existe", ADR_16.is_file())
    t.contiene("GE-E67 su apartado Revision dice que revisa ADR-0015", "Revisa ADR-0015",
               _sin_realces("\n".join(M64._seccion(texto, "Revisión"))))
    t.igual("GE-E67 ADR-0016 tiene siete decisiones, de la 1 a la 7", [str(i) for i in range(1, 8)],
            re.findall(r"(?m)^### (\d+)\. ", texto.replace("\r\n", "\n")))
