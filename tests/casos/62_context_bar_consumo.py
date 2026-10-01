# La Context Bar muestra el consumo de contexto desde la instalacion.
#
# Spec: docs/cambios/context-bar-consumo-desde-instalacion/spec.md. Cada asercion dice
# `consumo E-nn`, para no confundirse con los `E-nn` de bloque-1-context-bar y de
# context-bar-colores, que viven en 53_context_bar.py.
#
# Lo que instala de verdad -E-31, E-38 a E-40, E-62 a E-68 y E-75- esta en
# tests/casos/62-context-bar-consumo-instalador.ps1. Aca va el resto: contra el adaptador, la
# agregacion, `dibujar`, la CLI y el renderizador instalado, que corre como lo corre Claude Code
# -el statusline.py de un arbol armado con lo que copia install.ps1, un proceso por dibujo-.
#
# E-72, E-73 y E-74 no tienen una asercion propia: son la suite entera. E-72 son las aserciones
# `colores E-nn` de 53_context_bar.py y E-19 de 54-context-bar-instalador.ps1; E-73 son
# 30_b4_contabilidad.py, 30-contabilidad-instalador.ps1 y los escenarios de bloque-1-context-bar de
# 53_context_bar.py, con E-22 pisado; E-74 es que .\tests\Invoke-Tests.ps1 salga con 0.
import atexit
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
PAQUETE = BIN / "contabilidad"
CLI = BIN / "dev-harness.py"
PLANTILLA = RAIZ / "harnesses" / "desarrollo" / "reglas" / "budget-policy-context-default.json"
DOC = RAIZ / "docs" / "contabilidad.md"

sys.path.insert(0, str(BIN))
from contabilidad import agregacion as c_agr                 # noqa: E402
from contabilidad import barra as c_barra                    # noqa: E402
from contabilidad import eventos as c_eventos                # noqa: E402
from contabilidad import libro as c_libro                    # noqa: E402
from contabilidad import presupuesto as c_pres               # noqa: E402
from contabilidad.adaptadores import claude_code as c_cc     # noqa: E402
from contabilidad.adaptadores import contrato as c_contrato  # noqa: E402
from contabilidad.adaptadores import registro as c_reg       # noqa: E402


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


B = _cargar("bienvenida_62", RAIZ / "comun" / "hooks" / "lib" / "bienvenida.py")
SL = _cargar("statusline_62", PAQUETE / "statusline.py")
MEDIDOR = _cargar("medir_barra_62", RAIZ / "tests" / "medir_barra.py")

TAREA = "GCBA-62"
SESION = "s-cb62-sesion"
SIN_DATOS = "HARNESS | sin datos del Bloque 4"
FOTO = "CONTEXT_WINDOW_OBSERVED"
INCONSISTENTE = "CONTEXT_WINDOW_PROVIDER_INCONSISTENT"
LISTA = "La barra está lista para mostrar consumo porcentual y alertas."
TOKEN = "glp" + "at-" + "Z1x2C3v4B5n6M7a8S9d0"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_AMARILLO, _ROJO, _NEGRITA, _FIN = "\x1b[33m", "\x1b[31m", "\x1b[1m", "\x1b[0m"
_DENY_ENV = {"deny": ["Read(./.env)", "Read(./.env.*)"]}
TODAS = ("ES0901", "ES0902", "ES0903", "GuiaDGISIS", "Obelisco", "PC0901")


def _default():
    return json.loads(PLANTILLA.read_text(encoding="utf-8"))


# -- piezas ------------------------------------------------------------------------------------

def _escribir(ruta, texto):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(texto, encoding="utf-8")


def _json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False))


def _tmp(prefijo="cb62-"):
    carpeta = Path(tempfile.mkdtemp(prefix=prefijo))
    atexit.register(shutil.rmtree, str(carpeta), True)
    return carpeta


def _ventana(limite=200000, entrada=120000, salida=14000, uso=None, usado=None, libre=None):
    """Un `context_window` como el que manda Claude Code. `uso`: el `current_usage`, o None para
    dejarlo en null."""
    return {"context_window_size": limite, "total_input_tokens": entrada,
            "total_output_tokens": salida, "current_usage": uso,
            "used_percentage": usado, "remaining_percentage": libre}


def _uso_actual(entrada=12, salida=300, creacion=900, lectura=40000):
    return {"input_tokens": entrada, "output_tokens": salida,
            "cache_creation_input_tokens": creacion, "cache_read_input_tokens": lectura}


def _foto_de(ventana, sesion=SESION, cursor=0, **resto):
    """El registro que saca el adaptador de un stdin con esa ventana."""
    stdin = dict({"session_id": sesion, "context_window": ventana}, **resto)
    return c_cc.contexto_de_statusline(stdin, sesion=sesion, cursor=cursor)


def _evento_foto(tokens, limite=200000, sesion=SESION, cursor=0, usado=None, libre=None):
    """Una CONTEXT_WINDOW_OBSERVED como la anota la barra: del adaptador, pasada por el contrato."""
    reg = _foto_de(_ventana(limite=limite, entrada=tokens, salida=0, usado=usado, libre=libre),
                   sesion=sesion, cursor=cursor)
    return c_contrato.a_evento(reg, sesion, c_reg.DE_LA_BARRA, None, c_contrato.tipo_de(reg),
                               sessionId=sesion)


def _costo(equivalente=1.5):
    return {"state": "RESOLVED", "actual": None, "apiEquivalentEstimated": equivalente,
            "actualState": "FIXED_PLAN", "provider": "p-1", "model": "m-cb62",
            "pricingSource": "fuente", "pricingVersionOrDate": "2026-09-30",
            "currency": "USD", "billingMode": "SUBSCRIPTION",
            "calculationMethod": "PROVIDER_REPORTED"}


def _llamada(n, sesion=SESION, entrada=10, salida=100, lectura=1000, creacion=200,
             modelo="m-cb62", unidad="WU-1", agente="dev-backend", contexto=None):
    return c_eventos.nuevo(
        "MODEL_CALL_COMPLETED", TAREA, "test", sessionId=sesion, workUnitId=unidad,
        agentId=agente, dedupKey="k-%d" % n, timestamp="2026-09-30T10:%02d:00" % n,
        rawReference="t.jsonl#L%d" % n,
        usage={"state": "RESOLVED", "provider": "p-1", "model": modelo, "inputTokens": entrada,
               "outputTokens": salida, "cacheReadTokens": lectura, "cacheCreationTokens": creacion,
               "contextTokens": contexto, "contextLimit": None},
        cost=_costo())


def _agregado(sesion=SESION):
    """Lo que reporta el proveedor de la sesion entera: otra medicion, que se concilia."""
    return c_eventos.nuevo(
        "SESSION_COMPLETED", TAREA, "test", sessionId=sesion, dedupKey="agg-1",
        timestamp="2026-09-30T10:59:00", metadata={"providerAggregate": True},
        usage={"state": "RESOLVED", "provider": "p-1", "model": "m-cb62", "inputTokens": 30,
               "outputTokens": 300, "cacheReadTokens": 3000, "cacheCreationTokens": 600,
               "contextTokens": None, "contextLimit": None},
        cost=_costo(4.25))


def _b4():
    return SL._bloque4()


def _estado(libro_, politica=None, sesion=SESION):
    return c_barra.de(libro_, sesion, politica)


def _linea(libro_, politica=None, color=False, sesion=SESION):
    return SL.dibujar(_estado(libro_, politica, sesion), _b4(), color=color)


def _segmentos(linea):
    return linea.strip().split(" | ")


def _ctx(linea):
    """El fragmento `Ctx ...` de una linea, con sus secuencias si las tiene. '' si no hay."""
    for s in _segmentos(linea):
        if _ANSI_RE.sub("", s).startswith("Ctx "):
            return s
    return ""


def _porcentajes(texto):
    return [int(p) for p in re.findall(r"(\d+)%", _ANSI_RE.sub("", texto))]


class _NoColor(object):
    """NO_COLOR puesta (o sacada, con None) en el entorno del proceso, y devuelta como estaba."""

    def __init__(self, valor):
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get("NO_COLOR")
        if self.valor is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = self.valor

    def __exit__(self, *a):
        if self.antes is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = self.antes


# -- el renderizador instalado -----------------------------------------------------------------

_INSTALADO = []


def _instalado():
    """(proyecto, renderizador) del arbol instalado que arma tests/medir_barra.py. Uno por corrida."""
    if not _INSTALADO:
        proy = _tmp("cb62-inst-") / "proyecto con espacios"
        renderizador = Path(MEDIDOR.armar(str(proy)))
        _INSTALADO.append((proy, renderizador))
    return _INSTALADO[0]


def _nueva_sesion():
    return "s-cb62-" + uuid.uuid4().hex[:10]


def _transcripcion(ruta, sesion, turnos=2, modelo="m-cb62", costo=None, extra=()):
    """Una transcripcion con la forma real: el pedido, la llamada con su uso y el resultado."""
    lineas = []
    for n in range(1, turnos + 1):
        uso = {"input_tokens": 10 * n, "output_tokens": 100 * n,
               "cache_read_input_tokens": 5000 * n, "cache_creation_input_tokens": 200}
        base = {"sessionId": sesion, "timestamp": "2026-09-30T10:00:%02d" % n}
        lineas += [
            dict(base, type="user", message={"role": "user", "content": "pedido %d" % n}),
            dict(base, type="assistant", message={"id": "msg_%d" % n, "model": modelo, "usage": uso,
                                                  "content": [{"type": "text", "text": "hecho %d" % n}]}),
            dict(base, type="user", message={"role": "user", "content": [
                {"type": "tool_result", "content": "salida %d" % n}]}),
        ]
    if costo is not None:
        lineas.append({"type": "cost-state", "sessionId": sesion, "totalDuration": 61000,
                       "totalAPIDuration": 30000, "totalToolDuration": 9000,
                       "hasUnknownModelCost": False, "startTime": 1,
                       "modelUsage": {modelo: {"inputTokens": 30, "outputTokens": 300,
                                               "cacheReadInputTokens": 15000,
                                               "cacheCreationInputTokens": 400, "costUSD": costo}}})
    lineas += list(extra)
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(ruta), "w", encoding="utf-8", newline="\n") as f:
        for l in lineas:
            f.write(json.dumps(l) + "\n")
    return str(ruta)


def _agregar_turno(ruta, sesion, n, modelo="m-cb62"):
    with io.open(str(ruta), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"type": "assistant", "sessionId": sesion,
                            "timestamp": "2026-09-30T11:00:%02d" % n,
                            "message": {"id": "msg_nuevo_%d" % n, "model": modelo,
                                        "usage": {"input_tokens": 1, "output_tokens": 1}}}) + "\n")


def _dibujar(entrada, color=False, no_color="1"):
    """(codigo, stdout) del renderizador instalado. `entrada`: dict, bytes o None (sin stdin).

    Sin `color` corre con NO_COLOR=1. Con `color=True` sin NO_COLOR, salvo que `no_color` diga
    otra cosa: `no_color=""` es NO_COLOR definida y vacia."""
    crudo = entrada if isinstance(entrada, bytes) or entrada is None \
        else json.dumps(entrada).encode("utf-8")
    entorno = dict(os.environ)
    entorno.pop("CLAUDE_PROJECT_DIR", None)
    entorno.pop("NO_COLOR", None)
    if not color:
        entorno["NO_COLOR"] = no_color
    elif no_color != "1":
        entorno["NO_COLOR"] = no_color
    r = subprocess.run([sys.executable, str(_instalado()[1])], input=crudo or b"",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       cwd=tempfile.gettempdir(), env=entorno, timeout=60)
    return r.returncode, r.stdout.decode("utf-8", "replace").rstrip("\r\n")


def _libro_de(proy, sesion):
    return proy / ".claude" / "runtime" / "accounting" / sesion / "ledger.jsonl"


def _leido(proy, sesion):
    return c_libro.leer(str(_libro_de(proy, sesion)))


def _fotos(proy, sesion):
    return [e for e in _leido(proy, sesion) if e.get("eventType") == FOTO]


def _senal(proy):
    ruta = proy / ".claude" / "runtime" / "contextbar.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


class _Politica(object):
    """La politica del proyecto instalado mientras dura el bloque. None: sin archivo."""

    def __init__(self, politica):
        self.politica = politica

    def __enter__(self):
        self.ruta = _instalado()[0] / ".claude" / "harness.presupuesto.json"
        if self.ruta.exists():
            self.ruta.unlink()
        if self.politica is not None:
            _json(self.ruta, self.politica)

    def __exit__(self, *a):
        if self.ruta.exists():
            self.ruta.unlink()


# ══ El adaptador de Claude Code ════════════════════════════════════════════════════════════════

def test_e01_el_limite_sale_de_context_window_size(t):
    """E-01 — el limite de la foto es `context_window_size`, y sale del stdin y de ningun otro lado."""
    for limite in (200000, 1000000, 123457):
        foto = _foto_de(_ventana(limite=limite, entrada=1000, salida=10))
        t.igual("consumo E-01 context_window_size %d da contextLimit %d" % (limite, limite),
                limite, (foto or {}).get("tokens", {}).get("contextLimit"))
    t.igual("consumo E-01 sin context_window el adaptador no inventa uno", None,
            c_cc.contexto_de_statusline({"session_id": SESION}))
    # Instalado: la foto del libro lleva el limite que mando el stdin, y la transcripcion sola no.
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    fuente = _transcripcion(_tmp() / "t.jsonl", sesion)
    _dibujar({"session_id": sesion, "transcript_path": fuente})
    t.igual("consumo E-01 la transcripcion sola no trae limite", None,
            c_agr.resumir(_leido(proy, sesion))["context"]["contextLimit"])
    _dibujar({"session_id": sesion, "transcript_path": fuente,
              "context_window": _ventana(limite=1000000, entrada=50000, salida=500)})
    fotos = _fotos(proy, sesion)
    t.igual("consumo E-01 el renderizador anota la foto con contextLimit 1000000", [1000000],
            [f["contextWindow"]["contextLimit"] for f in fotos])
    t.igual("consumo E-01 y el resumen tiene ese limite", 1000000,
            c_agr.resumir(_leido(proy, sesion))["context"]["contextLimit"])


def test_e02_los_tokens_son_los_dos_totales(t):
    """E-02 — 120000 de entrada y 4000 de salida dan contextTokens 124000."""
    foto = _foto_de(_ventana(entrada=120000, salida=4000))
    t.igual("consumo E-02 contextTokens es 124000", 124000, (foto or {}).get("tokens", {}).get("context"))
    evento = c_contrato.a_evento(foto, SESION, c_reg.DE_LA_BARRA, None, c_contrato.tipo_de(foto),
                                 sessionId=SESION)
    t.igual("consumo E-02 y la CONTEXT_WINDOW_OBSERVED lo lleva", 124000,
            evento["contextWindow"]["contextTokens"])


def test_e03_la_cache_no_se_suma_dos_veces(t):
    """E-03 — con los dos totales y la cache de current_usage distinta de cero, contextTokens es la
    suma de los dos totales, exactamente."""
    uso = _uso_actual(entrada=12, salida=300, creacion=9000, lectura=80000)
    foto = _foto_de(_ventana(entrada=120000, salida=4000, uso=uso))
    t.igual("consumo E-03 la cache de current_usage no se suma otra vez", 124000,
            (foto or {}).get("tokens", {}).get("context"))


def test_e04_current_usage_solo_sin_los_dos_totales(t):
    """E-04 — sin los dos totales, la suma de los cuatro campos de current_usage, una vez cada uno.
    Con los totales, current_usage no cambia nada."""
    uso = _uso_actual(entrada=12, salida=300, creacion=900, lectura=40000)
    for rotulo, ventana in (
            ("sin las claves", {"context_window_size": 200000, "current_usage": uso}),
            ("con los totales en null", dict(_ventana(uso=uso), total_input_tokens=None,
                                             total_output_tokens=None))):
        foto = _foto_de(ventana)
        t.igual("consumo E-04 %s: la suma de los cuatro, cada uno una vez" % rotulo,
                12 + 300 + 900 + 40000, (foto or {}).get("tokens", {}).get("context"))
    con = [(_foto_de(_ventana(entrada=120000, salida=4000, uso=u)) or {}).get("tokens", {}).get("context")
           for u in (None, uso, _uso_actual(entrada=99999, salida=1, creacion=5, lectura=7))]
    t.igual("consumo E-04 con los totales, cambiar current_usage no cambia contextTokens",
            [124000] * 3, con)


def test_e05_sin_observacion_no_hay_foto(t):
    """E-05 — sin context_window, con context_window null, o con current_usage null y los dos
    totales en 0: ninguna foto en el libro, y la linea sin `Ctx 0%` ni ningun `%`."""
    casos = (("sin context_window", {}),
             ("con context_window null", {"context_window": None}),
             ("con current_usage null y los dos totales en 0",
              {"context_window": _ventana(entrada=0, salida=0, uso=None)}))
    for rotulo, extra in casos:
        stdin = dict({"session_id": SESION}, **extra)
        t.igual("consumo E-05 %s: el adaptador no devuelve observacion" % rotulo, None,
                c_cc.contexto_de_statusline(stdin, sesion=SESION))
    proy, _ = _instalado()
    with _Politica(_default()):
        for rotulo, extra in casos:
            sesion = _nueva_sesion()
            fuente = _transcripcion(_tmp() / "t.jsonl", sesion)
            codigo, linea = _dibujar(dict({"session_id": sesion, "transcript_path": fuente}, **extra))
            t.igual("consumo E-05 %s: sale 0" % rotulo, 0, codigo)
            t.igual("consumo E-05 %s: ninguna foto en el libro" % rotulo, [], _fotos(proy, sesion))
            t.no_contiene("consumo E-05 %s: la linea no tiene Ctx 0%%" % rotulo, "Ctx 0%", linea)
            t.no_contiene("consumo E-05 %s: ni ningun %%" % rotulo, "%", linea)
            t.contiene("consumo E-05 %s: y dibuja la ventana de la transcripcion en tokens" % rotulo,
                       " | Ctx 10k | ", linea)


def test_e06_un_limite_invalido_deja_la_foto_sin_limite(t):
    """E-06 — con context_window_size 0, -1, 1.5, "200000", true o null: contextLimit null, y la
    linea dibuja `Ctx <tokens>` sin `%`."""
    for limite in (0, -1, 1.5, "200000", True, None):
        foto = _foto_de(_ventana(limite=limite, entrada=120000, salida=4000))
        t.igual("consumo E-06 context_window_size %r: la foto no tiene limite" % (limite,), None,
                (foto or {}).get("tokens", {}).get("contextLimit", "sin foto"))
        evento = c_contrato.a_evento(foto, SESION, c_reg.DE_LA_BARRA, None, c_contrato.tipo_de(foto),
                                     sessionId=SESION)
        linea = _linea([_llamada(1), evento], _default())
        t.igual("consumo E-06 context_window_size %r: la linea dibuja Ctx 124k" % (limite,),
                "Ctx 124k", _ctx(linea))
        t.no_contiene("consumo E-06 context_window_size %r: sin %%" % (limite,), "%", linea)
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    codigo, linea = _dibujar({"session_id": sesion,
                              "transcript_path": _transcripcion(_tmp() / "t.jsonl", sesion),
                              "context_window": _ventana(limite="200000", entrada=120000, salida=4000)})
    t.igual("consumo E-06 instalado: la foto del libro va sin limite", [None],
            [f["contextWindow"]["contextLimit"] for f in _fotos(proy, sesion)])
    t.igual("consumo E-06 instalado: y la linea dibuja tokens", "Ctx 124k", _ctx(linea))


def test_e07_un_total_invalido_no_es_un_total_que_falta(t):
    """E-07 — total_input_tokens en true, -1, "12000", una lista o un no finito del JSON: ninguna foto
    lleva contextTokens 0, y la observacion no cae a current_usage."""
    uso = _uso_actual()
    suma_del_uso = sum(uso.values())
    crudos = ("true", "-1", '"12000"', "[12000]", "NaN", "Infinity", "-Infinity")
    for crudo in crudos:
        texto = ('{"session_id": "%s", "context_window": {"context_window_size": 200000, '
                 '"total_input_tokens": %s, "total_output_tokens": 4000, "current_usage": %s}}'
                 % (SESION, crudo, json.dumps(uso)))
        stdin = json.loads(texto)
        foto = c_cc.contexto_de_statusline(stdin, sesion=SESION)
        contexto = (foto or {}).get("tokens", {}).get("context")
        t.verdadero("consumo E-07 total_input_tokens %s: ninguna foto con contextTokens 0" % crudo,
                    contexto != 0)
        t.verdadero("consumo E-07 total_input_tokens %s: no cae a current_usage" % crudo,
                    contexto != suma_del_uso)
        t.igual("consumo E-07 total_input_tokens %s: queda sin resolver, sin foto" % crudo, None, foto)
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    fuente = _transcripcion(_tmp() / "t.jsonl", sesion)
    crudo = ('{"session_id": "%s", "transcript_path": %s, "context_window": {"context_window_size": '
             '200000, "total_input_tokens": NaN, "total_output_tokens": 4000, "current_usage": %s}}'
             % (sesion, json.dumps(fuente), json.dumps(uso))).encode("utf-8")
    codigo, linea = _dibujar(crudo)
    t.igual("consumo E-07 instalado, con un NaN del JSON: sale 0", 0, codigo)
    t.igual("consumo E-07 instalado: ninguna foto en el libro", [], _fotos(proy, sesion))
    t.no_contiene("consumo E-07 instalado: y la linea no dibuja un 0%", "Ctx 0%", linea)


def test_e08_el_costo_del_stdin_no_entra(t):
    """E-08 — con cost.total_cost_usd 99.99 y sin cost: el mismo libro y la misma linea, byte a byte."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    fuente = _transcripcion(_tmp() / "t.jsonl", sesion, costo=0.5)
    base = {"session_id": sesion, "transcript_path": fuente, "context_window": _ventana()}
    resultados = []
    with _Politica(_default()):
        for stdin in (dict(base, cost={"total_cost_usd": 99.99, "total_duration_ms": 5}), base):
            ruta = _libro_de(proy, sesion)
            if ruta.exists():
                ruta.unlink()
            _, linea = _dibujar(stdin)
            resultados.append((ruta.read_bytes(), linea))
    t.verdadero("consumo E-08 el libro es el mismo, byte a byte", resultados[0][0] == resultados[1][0])
    t.igual("consumo E-08 y la linea tambien", resultados[1][1], resultados[0][1])
    t.no_contiene("consumo E-08 ningun evento del libro lleva 99.99", "99.99",
                  resultados[0][0].decode("utf-8"))
    t.no_contiene("consumo E-08 ni la linea", "99.99", resultados[0][1])


_CAMPOS_DE_VENTANA = ("context_window", "context_window_size", "used_percentage",
                      "remaining_percentage", "current_usage", "total_input_tokens",
                      "total_output_tokens")


def _py_de_contabilidad(paquete=None):
    return sorted(p for p in (paquete or PAQUETE).rglob("*.py") if "__pycache__" not in p.parts)


def _campos_en(texto):
    return sorted(c for c in _CAMPOS_DE_VENTANA if re.search(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])"
                                                             % re.escape(c), texto))


def test_e09_los_campos_de_la_ventana_viven_en_el_adaptador(t):
    """E-09 — statusline.py no nombra ningun campo de context_window, y entre los .py de
    contabilidad/ solo los nombra adaptadores/claude_code.py."""
    t.igual("consumo E-09 statusline.py no nombra ninguno", [],
            _campos_en((PAQUETE / "statusline.py").read_text(encoding="utf-8")))
    donde = sorted(p.relative_to(PAQUETE).as_posix() for p in _py_de_contabilidad()
                   if _campos_en(p.read_text(encoding="utf-8")))
    t.igual("consumo E-09 el unico .py que los nombra es adaptadores/claude_code.py",
            ["adaptadores/claude_code.py"], donde)
    t.igual("consumo E-09 y los nombra a todos", list(sorted(_CAMPOS_DE_VENTANA)),
            _campos_en((PAQUETE / "adaptadores" / "claude_code.py").read_text(encoding="utf-8")))
    t.igual("consumo E-09 el barrido agarra una fuga", ["used_percentage"],
            _campos_en("x = entrada['context_windowX'] or datos.get('used_percentage')"))


_LITERALES = ("200000", "1000000", "200_000", "1_000_000")


def _literales_en(texto):
    return sorted(l for l in _LITERALES if l in texto) + (
        ["exceeds_200k_tokens"] if "exceeds_200k_tokens" in texto else [])


def test_e10_ningun_tamano_de_ventana_escrito_en_el_codigo(t):
    """E-10 — ningun .py de contabilidad/, adaptadores incluidos, lleva 200000, 1000000, 200_000 ni
    1_000_000, y ninguno lee exceeds_200k_tokens."""
    archivos = _py_de_contabilidad()
    t.verdadero("consumo E-10 el barrido mira el paquete entero, con los adaptadores",
                len(archivos) >= 14 and any(p.name == "claude_code.py" for p in archivos))
    for p in archivos:
        t.igual("consumo E-10 %s no lleva un tamano de ventana" % p.relative_to(PAQUETE).as_posix(),
                [], _literales_en(p.read_text(encoding="utf-8")))
    t.igual("consumo E-10 el barrido agarra una fuga", ["200000", "exceeds_200k_tokens"],
            _literales_en("LIMITE = 200000\nif d.get('exceeds_200k_tokens'): pass"))


def test_e77_los_porcentajes_del_proveedor_son_evidencia(t):
    """E-77 — used_percentage y remaining_percentage se guardan como los mando el proveedor, y uno
    que contradice a los tokens y al limite no cambia contextTokens ni el % de la linea."""
    evento = _evento_foto(134000, usado=12.5, libre=87.5)
    t.igual("consumo E-77 la foto guarda used_percentage tal cual", 12.5,
            evento["contextWindow"]["reportedUsedPercentage"])
    t.igual("consumo E-77 y remaining_percentage", 87.5,
            evento["contextWindow"]["reportedRemainingPercentage"])
    enteros = _evento_foto(134000, usado=60, libre=40)
    t.igual("consumo E-77 un entero sigue siendo el entero que mando", (60, 40),
            (enteros["contextWindow"]["reportedUsedPercentage"],
             enteros["contextWindow"]["reportedRemainingPercentage"]))
    contra = _evento_foto(134000, usado=99, libre=1)
    t.igual("consumo E-77 un used_percentage que contradice no cambia contextTokens", 134000,
            contra["contextWindow"]["contextTokens"])
    t.igual("consumo E-77 ni el % de la linea: 67, no 99", "Ctx 67%",
            _ctx(_linea([_llamada(1), contra], _default())))
    t.igual("consumo E-77 y el resumen los conserva como evidencia", (99, 1),
            (c_agr.resumir([contra])["context"]["reportedUsedPercentage"],
             c_agr.resumir([contra])["context"]["reportedRemainingPercentage"]))


# ══ Una foto no es consumo ═════════════════════════════════════════════════════════════════════

def _con_y_sin_fotos():
    llamadas = [_llamada(1), _llamada(2, entrada=20, salida=200, lectura=3000, creacion=0),
                _llamada(3, entrada=5, salida=50, lectura=500, creacion=100, modelo="m-otro"),
                _agregado()]
    fotos = [_evento_foto(150000, cursor=1), _evento_foto(60000, cursor=2),
             _evento_foto(90000, cursor=3)]
    con = [llamadas[0], fotos[0], llamadas[1], fotos[1], llamadas[2], fotos[2], llamadas[3]]
    return c_agr.resumir(con, task_id=TAREA), c_agr.resumir(llamadas, task_id=TAREA), fotos


def test_e11_a_e14_las_fotos_no_se_suman(t):
    """E-11 / E-12 / E-13 / E-14 — input, output, cache y plata iguales con y sin fotos, y ninguna
    foto lleva un monto."""
    con, sin, fotos = _con_y_sin_fotos()
    t.igual("consumo E-11 tokens.input igual con y sin fotos", sin["tokens"]["inputTokens"],
            con["tokens"]["inputTokens"])
    t.igual("consumo E-12 tokens.output igual con y sin fotos", sin["tokens"]["outputTokens"],
            con["tokens"]["outputTokens"])
    t.igual("consumo E-13 cacheRead igual con y sin fotos", sin["tokens"]["cacheReadTokens"],
            con["tokens"]["cacheReadTokens"])
    t.igual("consumo E-13 cacheCreation igual con y sin fotos", sin["tokens"]["cacheCreationTokens"],
            con["tokens"]["cacheCreationTokens"])
    t.igual("consumo E-14 el costo actual igual con y sin fotos", sin["cost"]["actual"],
            con["cost"]["actual"])
    t.igual("consumo E-14 y apiEquivalentEstimated", sin["cost"]["apiEquivalentEstimated"],
            con["cost"]["apiEquivalentEstimated"])
    t.verdadero("consumo E-14 el costo del libro no es cero: la comparacion compara algo",
                con["cost"]["apiEquivalentEstimated"])
    for i, foto in enumerate(fotos):
        t.igual("consumo E-14 la foto %d no lleva cost, ni usage, ni time" % i,
                [None, None, None], [foto.get("cost"), foto.get("usage"), foto.get("time")])
        t.verdadero("consumo E-14 ni un monto en ningun lado de la foto %d" % i,
                    "actual" not in json.dumps(foto) and "apiEquivalent" not in json.dumps(foto))


def test_e15_las_fotos_no_se_cuentan(t):
    """E-15 — events.counted y el events de cada fila de byAgent, byWorkUnit, bySession y byModel,
    iguales con y sin fotos."""
    con, sin, _ = _con_y_sin_fotos()
    t.igual("consumo E-15 events.counted igual con y sin fotos", sin["events"]["counted"],
            con["events"]["counted"])
    t.igual("consumo E-15 las fotos se cuentan aparte, como fotos", 3, con["events"]["contextSnapshots"])
    for filas in ("byAgent", "byWorkUnit", "bySession", "byModel"):
        t.igual("consumo E-15 %s: el events de cada fila igual" % filas,
                [(f["id"], f["events"]) for f in sin[filas]],
                [(f["id"], f["events"]) for f in con[filas]])
        t.verdadero("consumo E-15 %s: y hay filas que comparar" % filas, len(con[filas]) >= 1)


def test_e16_las_fotos_no_se_atribuyen(t):
    """E-16 — con todo el uso atribuido a una unidad y a un agente, las fotos no agregan
    WORKUNIT_... ni AGENT_ATTRIBUTION_UNRESOLVED."""
    con, sin, _ = _con_y_sin_fotos()
    t.igual("consumo E-16 sin fotos no habia nada sin atribuir", [],
            [u for u in sin["unresolved"] if u.startswith("WORKUNIT_") or u.startswith("AGENT_")])
    t.igual("consumo E-16 con fotos tampoco", [],
            [u for u in con["unresolved"] if u.startswith("WORKUNIT_") or u.startswith("AGENT_")])
    t.igual("consumo E-16 y lo no atribuido queda igual", sin["unattributed"], con["unattributed"])


def test_e17_el_contexto_es_la_ultima_foto(t):
    """E-17 — con tres fotos, el contexto es la ultima anotada: ni la suma ni la mayor."""
    con, _, _ = _con_y_sin_fotos()
    t.igual("consumo E-17 la ultima foto: 90000", 90000, con["context"]["contextTokens"])
    t.verdadero("consumo E-17 no es la suma", con["context"]["contextTokens"] != 300000)
    t.verdadero("consumo E-17 ni la mayor", con["context"]["contextTokens"] != 150000)
    t.igual("consumo E-17 y la fuente es la de la foto", "CLAUDE_CODE_STATUSLINE",
            con["context"]["source"])


def test_e18_la_misma_observacion_deja_una_foto(t):
    """E-18 — diez dibujos con el mismo stdin sobre la misma transcripcion: una sola foto."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    stdin = {"session_id": sesion, "transcript_path": _transcripcion(_tmp() / "t.jsonl", sesion),
             "context_window": _ventana()}
    for _ in range(10):
        _dibujar(stdin)
    t.igual("consumo E-18 diez dibujos, una foto", 1, len(_fotos(proy, sesion)))
    t.igual("consumo E-18 y ningun eventId repetido en el libro",
            len(_leido(proy, sesion)), len(set(e["eventId"] for e in _leido(proy, sesion))))


def test_e19_otra_observacion_deja_otra_foto(t):
    """E-19 — otros tokens u otro limite dejan una foto nueva. Los valores de la primera, repetidos
    despues de que avanzo la transcripcion, tambien, y el contexto es esa ultima."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    ruta = _tmp() / "t.jsonl"
    fuente = _transcripcion(ruta, sesion)
    base = {"session_id": sesion, "transcript_path": fuente}
    _dibujar(dict(base, context_window=_ventana(entrada=100000, salida=0)))
    t.igual("consumo E-19 la primera", 1, len(_fotos(proy, sesion)))
    _dibujar(dict(base, context_window=_ventana(entrada=150000, salida=0)))
    t.igual("consumo E-19 otros tokens: otra foto", 2, len(_fotos(proy, sesion)))
    _dibujar(dict(base, context_window=_ventana(limite=1000000, entrada=150000, salida=0)))
    t.igual("consumo E-19 otro limite: otra foto", 3, len(_fotos(proy, sesion)))
    _agregar_turno(ruta, sesion, 1)
    _, linea = _dibujar(dict(base, context_window=_ventana(entrada=100000, salida=0)))
    fotos = _fotos(proy, sesion)
    t.igual("consumo E-19 los valores de la primera, con la transcripcion avanzada: otra foto", 4,
            len(fotos))
    resumen = c_agr.resumir(_leido(proy, sesion))
    t.igual("consumo E-19 el contexto es esa ultima: 100000 de 200000", (100000, 200000),
            (resumen["context"]["contextTokens"], resumen["context"]["contextLimit"]))
    t.igual("consumo E-19 y es la de ahora, no la primera", "2026-09-30T11:00:01",
            resumen["context"]["at"])
    t.igual("consumo E-19 la linea la dibuja", "Ctx 50%", _ctx(linea))


def test_e20_la_conciliacion_no_ve_las_fotos(t):
    """E-20 — el estado de conciliacion y sus totales, iguales con y sin fotos."""
    con, sin, _ = _con_y_sin_fotos()
    t.verdadero("consumo E-20 hay algo que conciliar", sin["reconciliation"]["state"] != "NOT_APPLICABLE")
    t.igual("consumo E-20 el estado igual con y sin fotos", sin["reconciliation"]["state"],
            con["reconciliation"]["state"])
    for clave in ("providerReported", "derived", "differences"):
        t.igual("consumo E-20 %s igual con y sin fotos" % clave, sin["reconciliation"][clave],
                con["reconciliation"][clave])


# ══ Lo que dibuja la barra ═════════════════════════════════════════════════════════════════════

def _libro_con(tokens, limite=200000):
    return [_llamada(1), _evento_foto(tokens, limite=limite)]


def test_e21_con_limite_es_un_porcentaje(t):
    """E-21 — 134000 de 200000: `Ctx 67%`."""
    t.igual("consumo E-21 Ctx 67%", "Ctx 67%", _ctx(_linea(_libro_con(134000), _default())))
    t.igual("consumo E-21 tambien sin politica", "Ctx 67%", _ctx(_linea(_libro_con(134000))))


def test_e22_sin_limite_son_tokens(t):
    """E-22 — 134000 con el limite sin resolver: `Ctx 134k`, sin `%` en ese fragmento."""
    fragmento = _ctx(_linea(_libro_con(134000, limite=0), _default()))
    t.igual("consumo E-22 Ctx 134k", "Ctx 134k", fragmento)
    t.no_contiene("consumo E-22 sin %", "%", fragmento)


def test_e23_mas_tokens_que_ventana(t):
    """E-23 — 270000 de 200000: `Ctx 270k`, el resumen lleva CONTEXT_WINDOW_PROVIDER_INCONSISTENT, y
    ni la linea ni `contabilidad --barra` muestran un porcentaje mayor que 100."""
    libro_ = _libro_con(270000)
    linea = _linea(libro_, _default(), color=True)
    t.igual("consumo E-23 la linea dibuja Ctx 270k", "Ctx 270k", _ANSI_RE.sub("", _ctx(linea)))
    resumen = c_agr.resumir(libro_)
    t.igual("consumo E-23 el resumen lleva el diagnostico", INCONSISTENTE, resumen["context"]["diagnostic"])
    t.verdadero("consumo E-23 y lo cuenta entre lo abierto", INCONSISTENTE in resumen["unresolved"])
    t.igual("consumo E-23 la barra no calcula fraccion", None,
            _estado(libro_, _default())["context"]["fraction"])
    t.vacio("consumo E-23 la linea no muestra un porcentaje mayor que 100",
            [p for p in _porcentajes(linea) if p > 100])
    # contabilidad --barra, sobre el mismo libro puesto como el de una tarea.
    proy = _tmp("cb62-23-")
    (proy / ".claude").mkdir(parents=True)
    for evento in libro_:
        c_libro.agregar(str(c_libro.ruta_de(str(proy), TAREA)), evento)
    _json(proy / ".claude" / "harness.presupuesto.json", _default())
    codigo, salida, error = _cli(["contabilidad", TAREA, "--barra", "--sesion", SESION,
                                  "--proyecto", str(proy)])
    t.igual("consumo E-23 contabilidad --barra sale 0", 0, codigo)
    t.contiene("consumo E-23 contabilidad --barra dibuja Ctx", "Ctx", salida)
    t.vacio("consumo E-23 y ningun porcentaje mayor que 100", [p for p in _porcentajes(salida) if p > 100])
    _, crudo, _ = _cli(["contabilidad", TAREA, "--barra", "--json", "--sesion", SESION,
                        "--proyecto", str(proy)])
    t.igual("consumo E-23 contabilidad --barra --json: sin fraccion", None,
            json.loads(crudo)["context"]["fraction"])
    t.igual("consumo E-23 contabilidad --barra --json: con el diagnostico", INCONSISTENTE,
            json.loads(crudo)["context"]["diagnostic"])


def test_e24_mas_tokens_que_ventana_no_tiene_color(t):
    """E-24 — con 270000 de 200000 y la politica por defecto: Ctx sin ninguna secuencia de color, y
    ninguna etiqueta WARNING ni ERROR."""
    linea = _linea(_libro_con(270000), _default(), color=True)
    t.no_contiene("consumo E-24 Ctx sin ninguna secuencia", "\x1b", _ctx(linea))
    t.igual("consumo E-24 el nivel de contexto no sale de esa fraccion", "UNRESOLVED",
            _estado(_libro_con(270000), _default())["context"]["level"])
    for etiqueta in ("WARNING", "ERROR"):
        t.vacio("consumo E-24 sin la etiqueta %s" % etiqueta,
                [s for s in _segmentos(linea) if _ANSI_RE.sub("", s) == etiqueta])


def test_e25_normal_no_tiene_color(t):
    """E-25 — 50% con la politica por defecto: `Ctx 50%` sin color, y la unica secuencia de la
    linea es la negrita de HARNESS."""
    linea = _linea(_libro_con(100000), _default(), color=True)
    t.igual("consumo E-25 Ctx 50% sin secuencia", "Ctx 50%", _ctx(linea))
    t.igual("consumo E-25 la unica secuencia es la negrita de HARNESS", [_NEGRITA, _FIN],
            _ANSI_RE.findall(linea))
    t.verdadero("consumo E-25 y va sobre HARNESS", linea.startswith(_NEGRITA + "HARNESS" + _FIN + " | "))


def _nivel(tokens, politica=None):
    return _estado(_libro_con(tokens), _default() if politica is None else politica)["context"]["level"]


def test_e26_e27_los_umbrales_por_defecto(t):
    """E-26 / E-27 — con la politica por defecto: 70% WARNING y 69% NORMAL; 90% ERROR y 89% WARNING."""
    t.igual("consumo E-26 70% da WARNING", "WARNING", _nivel(140000))
    t.igual("consumo E-26 69% da NORMAL", "NORMAL", _nivel(138000))
    t.igual("consumo E-27 90% da ERROR", "ERROR", _nivel(180000))
    t.igual("consumo E-27 89% da WARNING", "WARNING", _nivel(178000))
    t.igual("consumo E-26 / E-27 sin politica no hay nivel", "UNRESOLVED", _nivel(180000, {}))


def test_e28_e29_los_bytes_de_colores(t):
    """E-28 / E-29 — Ctx y la etiqueta en WARNING y en ERROR son, byte a byte, los de E-02, E-07,
    E-03 y E-08 de context-bar-colores: amarillo o rojo, el texto, y su propio reset."""
    def etiqueta(linea, texto):
        return [s for s in _segmentos(linea) if _ANSI_RE.sub("", s) == texto]

    aviso = _linea(_libro_con(140000), _default(), color=True)
    t.igual("consumo E-28 Ctx en WARNING: los bytes de colores E-02", _AMARILLO + "Ctx 70%" + _FIN,
            _ctx(aviso))
    t.igual("consumo E-28 la etiqueta WARNING: los bytes de colores E-07", [_AMARILLO + "WARNING" + _FIN],
            etiqueta(aviso, "WARNING"))
    error = _linea(_libro_con(180000), _default(), color=True)
    t.igual("consumo E-29 Ctx en ERROR: los bytes de colores E-03", _ROJO + "Ctx 90%" + _FIN, _ctx(error))
    t.igual("consumo E-29 la etiqueta ERROR: los bytes de colores E-08", [_ROJO + "ERROR" + _FIN],
            etiqueta(error, "ERROR"))


def test_e30_la_linea_sin_datos(t):
    """E-30 — LINEA_SIN_DATOS es `HARNESS | sin datos del Bloque 4`, y el renderizador instalado sin
    stdin dibuja exactamente eso."""
    t.igual("consumo E-30 la constante", SIN_DATOS, SL.LINEA_SIN_DATOS)
    for rotulo, color in (("sin colores", False), ("con colores", True)):
        codigo, salida = _dibujar(None, color=color)
        t.igual("consumo E-30 el renderizador instalado sin stdin, %s" % rotulo, (0, SIN_DATOS),
                (codigo, salida))


# ══ La politica por defecto ════════════════════════════════════════════════════════════════════

def _claves(nodo):
    if isinstance(nodo, dict):
        return set(nodo) | set(k for v in nodo.values() for k in _claves(v))
    if isinstance(nodo, list):
        return set(k for v in nodo for k in _claves(v))
    return set()


def test_e32_a_e36_la_plantilla(t):
    """E-32 a E-36 — la politica que se instala valida con el validador del harness, tiene 0.7 y 0.9
    como umbrales de contexto, y ni un softLimit ni un hardLimit."""
    texto = PLANTILLA.read_text(encoding="utf-8")
    politica = json.loads(texto)
    t.igual("consumo E-32 valida contra budget-policy.schema.json", [], c_pres.validar(politica))
    cargada = None
    try:
        cargada = c_pres.cargar(str(PLANTILLA))
    except c_pres.PoliticaInvalida:
        cargada = None
    t.igual("consumo E-32 y presupuesto.cargar la acepta, como la carga la barra", politica, cargada)
    # La que crea `presupuesto --context-defaults` en un proyecto sin politica es la misma.
    proy = _proyecto_cli(politica=None)
    codigo, _, _ = _cli(["presupuesto", "--context-defaults", "--proyecto", proy])
    creada = Path(proy) / ".claude" / "harness.presupuesto.json"
    t.igual("consumo E-32 la politica creada sale 0", 0, codigo)
    t.verdadero("consumo E-32 la creada es la plantilla, byte a byte",
                creada.is_file() and creada.read_bytes() == PLANTILLA.read_bytes())
    t.igual("consumo E-32 y valida", [],
            c_pres.validar(json.loads(creada.read_text(encoding="utf-8"))) if creada.is_file()
            else ["no se creo"])
    barra = politica.get("statusBar") or {}
    t.igual("consumo E-33 contextWarningAt 0.7", 0.7, barra.get("contextWarningAt"))
    t.igual("consumo E-34 contextErrorAt 0.9", 0.9, barra.get("contextErrorAt"))
    t.verdadero("consumo E-35 ni una clave softLimit", "softLimit" not in _claves(politica))
    t.no_contiene("consumo E-35 ni el texto softLimit en ninguna parte del archivo", "softLimit", texto)
    t.verdadero("consumo E-36 ni una clave hardLimit", "hardLimit" not in _claves(politica))
    t.no_contiene("consumo E-36 ni el texto hardLimit en ninguna parte del archivo", "hardLimit", texto)
    t.igual("consumo E-35 / E-36 y ningun limite de plata declarado", (False, False),
            (c_pres.declarada(politica, "task"), c_pres.declarada(politica, "project")))


def test_e37_la_politica_por_defecto_no_cambia_el_costo(t):
    """E-37 — con solo la politica por defecto no hay `Budget`, y el costo se dibuja igual que sin
    politica."""
    proy, _ = _instalado()
    tmp = _tmp()
    lineas = {}
    for rotulo, politica in (("sin politica", None), ("con la por defecto", _default())):
        sesion = _nueva_sesion()
        fuente = _transcripcion(tmp / ("%s.jsonl" % sesion), sesion, costo=0.75)
        with _Politica(politica):
            _, lineas[rotulo] = _dibujar({"session_id": sesion, "transcript_path": fuente,
                                          "context_window": _ventana()})
    t.no_contiene("consumo E-37 con la politica por defecto no hay Budget", "Budget",
                  lineas["con la por defecto"])
    t.igual("consumo E-37 y la linea es la misma que sin politica, costo incluido",
            lineas["sin politica"], lineas["con la por defecto"])
    t.contiene("consumo E-37 y la comparacion compara una linea con datos", "Ctx 67%",
               lineas["con la por defecto"])


# ══ setup y presupuesto --context-defaults ═════════════════════════════════════════════════════

_CLI_62 = []


def _sin_integraciones():
    """El entorno sin ninguna variable de Jira ni de GitLab: la suite no sale a la red."""
    return dict((k, v) for k, v in os.environ.items()
                if not (k.startswith("JIRA_") or k.startswith("GITLAB_")))


def _cli(argv):
    """(codigo, stdout, stderr) de dev-harness.py en proceso, sin terminal y sin integraciones.
    input() y getpass() levantan: la CLI no puede preguntar."""
    import builtins
    import getpass
    if not _CLI_62:
        _CLI_62.append(_cargar("dev_harness_62", CLI))
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr, sys.stdin, builtins.input, getpass.getpass)
    guardado = dict(os.environ)
    pedidos = []

    def _pedir(*a, **k):
        pedidos.append(a)
        raise EOFError("la CLI no puede preguntar")
    limpio = _sin_integraciones()
    os.environ.clear()
    os.environ.update(limpio)
    sys.stdout, sys.stderr, sys.stdin = salida, error, io.StringIO("")
    builtins.input, getpass.getpass = _pedir, _pedir
    try:
        codigo = _CLI_62[0].main(argv)
    finally:
        (sys.stdout, sys.stderr, sys.stdin, builtins.input, getpass.getpass) = previos
        os.environ.clear()
        os.environ.update(guardado)
    _PEDIDOS.append(pedidos)
    return codigo, salida.getvalue(), error.getvalue()


_PEDIDOS = []


def _proyecto_cli(politica="DEFAULT"):
    """Un proyecto con el harness de desarrollo, sin .env, y la politica que se pida: "DEFAULT" es la
    plantilla byte a byte, None es sin archivo, un texto va tal cual y un dict como JSON."""
    raiz = _tmp("cb62-cli-")
    _json(raiz / ".claude" / "harness.lock.json", {"version": "0.28.0", "harness": ["comun", "desarrollo"],
                                                   "instalado": "2026-09-30 10:00:00", "archivos": []})
    ruta = raiz / ".claude" / "harness.presupuesto.json"
    if politica == "DEFAULT":
        shutil.copy(str(PLANTILLA), str(ruta))
    elif isinstance(politica, str):
        _escribir(ruta, politica)
    elif politica is not None:
        ruta.write_text(json.dumps(politica, indent=2), encoding="utf-8")
    return str(raiz)


def _bloque_de_setup(salida):
    return salida.split("\nContext Bar\n", 1)[-1] if "\nContext Bar\n" in salida else ""


_PROYECTO_SIN_UMBRALES = {
    "policyId": "gcba-tramites", "currency": "USD", "billingMode": "SUBSCRIPTION",
    "task": {"softLimit": 5.0, "hardLimit": 20.0}, "project": None,
    "premiumModel": {"requiresHumanApproval": True, "projectedOverrunRequiresApproval": True},
    "statusBar": {"warningAt": 0.5, "errorAt": 0.9},
}


def test_e41_setup_no_pregunta(t):
    """E-41 — setup con stdin cerrado termina con 0 y no espera ninguna respuesta."""
    proy = _proyecto_cli()
    r = subprocess.run([sys.executable, str(CLI), "setup", "--proyecto", proy],
                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=_sin_integraciones(), timeout=120)
    t.igual("consumo E-41 setup con stdin cerrado sale 0", 0, r.returncode)
    t.contiene("consumo E-41 y termina mostrando el bloque Context Bar", "política DEFAULT",
               r.stdout.decode("utf-8", "replace"))
    _PEDIDOS[:] = []
    codigo, _, _ = _cli(["setup", "--proyecto", proy])
    t.igual("consumo E-41 en proceso tambien sale 0", 0, codigo)
    t.igual("consumo E-41 y no llamo a input ni a getpass", [[]], _PEDIDOS)


def test_e42_el_bloque_context_bar_de_setup(t):
    """E-42 — con la politica por defecto, setup muestra el bloque Context Bar con la politica, los
    dos umbrales y el presupuesto monetario sin configurar."""
    codigo, salida, _ = _cli(["setup", "--proyecto", _proyecto_cli()])
    bloque = _bloque_de_setup(salida)
    t.igual("consumo E-42 sale 0", 0, codigo)
    t.verdadero("consumo E-42 hay un bloque Context Bar", bool(bloque))
    for texto in ("política DEFAULT", "contexto WARNING 70%", "contexto ERROR 90%",
                  "presupuesto monetario SIN CONFIGURAR"):
        t.contiene("consumo E-42 dice %s" % texto, texto, bloque)


def test_e43_default_project_missing_invalid(t):
    """E-43 — setup dice DEFAULT con la plantilla, PROJECT con otra politica valida, MISSING sin
    archivo e INVALID con una que no valida."""
    otra = dict(_default(), policyId="gcba-harness-context-bar-default",
                task={"softLimit": None, "hardLimit": 50.0})
    for rotulo, esperado, politica in (
            ("la plantilla", "DEFAULT", "DEFAULT"),
            ("el id del harness con un hardLimit", "PROJECT", otra),
            ("una del proyecto sin umbrales de contexto", "PROJECT", _PROYECTO_SIN_UMBRALES),
            ("sin archivo", "MISSING", None),
            ("una sin currency", "INVALID", {"policyId": "sin-moneda"}),
            ("una que no es JSON", "INVALID", "{ no es json")):
        codigo, salida, _ = _cli(["setup", "--proyecto", _proyecto_cli(politica)])
        t.igual("consumo E-43 %s: sale 0" % rotulo, 0, codigo)
        t.contiene("consumo E-43 %s: dice política %s" % (rotulo, esperado), "política %s" % esperado,
                   _bloque_de_setup(salida))


def test_e44_e45_setup_nombra_el_umbral_que_falta(t):
    """E-44 / E-45 — con una politica PROJECT sin contextWarningAt, o sin contextErrorAt, setup lo
    nombra y el archivo queda igual byte a byte."""
    for escenario, falta, queda in (("E-44", "contextWarningAt", "contextErrorAt"),
                                    ("E-45", "contextErrorAt", "contextWarningAt")):
        politica = json.loads(json.dumps(_PROYECTO_SIN_UMBRALES))
        politica["statusBar"][queda] = 0.8
        proy = _proyecto_cli(politica)
        ruta = Path(proy) / ".claude" / "harness.presupuesto.json"
        antes = ruta.read_bytes()
        _, salida, _ = _cli(["setup", "--proyecto", proy])
        bloque = _bloque_de_setup(salida)
        t.contiene("consumo %s setup nombra %s" % (escenario, falta), falta, bloque)
        t.no_contiene("consumo %s y no nombra el que esta" % escenario, "falta statusBar.%s" % queda, bloque)
        t.contiene("consumo %s el que esta sale en porcentaje" % escenario, "80%", bloque)
        t.verdadero("consumo %s el archivo queda igual byte a byte" % escenario, ruta.read_bytes() == antes)


def test_e46_solo_context_defaults_escribe(t):
    """E-46 — sobre una politica PROJECT sin umbrales de contexto, setup, estado y harness no cambian
    el archivo; `presupuesto --context-defaults` le agrega los dos, con 0.7 y 0.9, y el resto queda
    con sus valores y en su orden. -Update, en 62-context-bar-consumo-instalador.ps1."""
    proy = _proyecto_cli(_PROYECTO_SIN_UMBRALES)
    ruta = Path(proy) / ".claude" / "harness.presupuesto.json"
    antes = ruta.read_bytes()
    for argv in (["setup"], ["estado"], ["estado", "--resumen"], ["harness"], ["harness", "--verbose"],
                 ["presupuesto"]):
        codigo, _, _ = _cli(argv + ["--proyecto", proy])
        t.igual("consumo E-46 %s sale 0" % " ".join(argv), 0, codigo)
        t.verdadero("consumo E-46 %s no cambia el archivo" % " ".join(argv), ruta.read_bytes() == antes)
    codigo, salida, _ = _cli(["presupuesto", "--context-defaults", "--proyecto", proy])
    t.igual("consumo E-46 presupuesto --context-defaults sale 0", 0, codigo)
    nueva = json.loads(ruta.read_text(encoding="utf-8"))
    original = json.loads(antes.decode("utf-8"))
    t.igual("consumo E-46 agrego contextWarningAt 0.7 y contextErrorAt 0.9", (0.7, 0.9),
            (nueva["statusBar"].get("contextWarningAt"), nueva["statusBar"].get("contextErrorAt")))
    t.igual("consumo E-46 las claves de arriba, en su orden", list(original), list(nueva))
    t.igual("consumo E-46 las de statusBar, en su orden, y las dos nuevas al final",
            list(original["statusBar"]) + ["contextWarningAt", "contextErrorAt"], list(nueva["statusBar"]))
    t.igual("consumo E-46 todas las demas con su valor",
            dict((k, v) for k, v in original.items() if k != "statusBar"),
            dict((k, v) for k, v in nueva.items() if k != "statusBar"))
    t.igual("consumo E-46 y las de statusBar tambien", original["statusBar"],
            dict((k, v) for k, v in nueva["statusBar"].items() if k in original["statusBar"]))
    t.contiene("consumo E-46 y dice que agrego", "contextWarningAt", salida)
    despues = ruta.read_bytes()
    _cli(["presupuesto", "--context-defaults", "--proyecto", proy])
    t.verdadero("consumo E-46 correrlo otra vez no cambia nada", ruta.read_bytes() == despues)
    # Una que no valida no se toca.
    rota = _proyecto_cli({"policyId": "sin-moneda"})
    ruta_rota = Path(rota) / ".claude" / "harness.presupuesto.json"
    antes_rota = ruta_rota.read_bytes()
    codigo, _, error = _cli(["presupuesto", "--context-defaults", "--proyecto", rota])
    t.igual("consumo E-46 con una politica INVALID sale 2", 2, codigo)
    t.verdadero("consumo E-46 y no la toca", ruta_rota.read_bytes() == antes_rota)
    t.contiene("consumo E-46 y dice por que", "no valida", error)


def test_e47_context_defaults_nunca_agrega_plata(t):
    """E-47 — `presupuesto --context-defaults` no agrega softLimit ni hardLimit: task y project en null
    siguen en null, y los limites que ya habia quedan con su valor."""
    nulos = dict(_PROYECTO_SIN_UMBRALES, task=None, project=None, statusBar=None)
    for rotulo, politica in (("con task y project en null", nulos),
                             ("con limites declarados", _PROYECTO_SIN_UMBRALES)):
        proy = _proyecto_cli(politica)
        ruta = Path(proy) / ".claude" / "harness.presupuesto.json"
        antes = json.loads(ruta.read_text(encoding="utf-8"))
        codigo, _, _ = _cli(["presupuesto", "--context-defaults", "--proyecto", proy])
        nueva = json.loads(ruta.read_text(encoding="utf-8"))
        t.igual("consumo E-47 %s: sale 0" % rotulo, 0, codigo)
        t.igual("consumo E-47 %s: task y project quedan como estaban" % rotulo,
                (antes["task"], antes["project"]), (nueva["task"], nueva["project"]))
        cuantos = lambda d, k: json.dumps(d).count('"%s"' % k)  # noqa: E731
        t.igual("consumo E-47 %s: ningun softLimit nuevo" % rotulo, cuantos(antes, "softLimit"),
                cuantos(nueva, "softLimit"))
        t.igual("consumo E-47 %s: ningun hardLimit nuevo" % rotulo, cuantos(antes, "hardLimit"),
                cuantos(nueva, "hardLimit"))
        barra = nueva.get("statusBar") or {}
        t.igual("consumo E-47 %s: y los umbrales de contexto si" % rotulo, (0.7, 0.9),
                (barra.get("contextWarningAt"), barra.get("contextErrorAt")))
    creada = _proyecto_cli(None)
    _cli(["presupuesto", "--context-defaults", "--proyecto", creada])
    ruta_creada = Path(creada) / ".claude" / "harness.presupuesto.json"
    t.verdadero("consumo E-47 sin archivo, el default tampoco trae plata",
                ruta_creada.is_file() and not ({"softLimit", "hardLimit"} & _claves(json.loads(
                    ruta_creada.read_text(encoding="utf-8")))))


# ══ harness --verbose ══════════════════════════════════════════════════════════════════════════

def _fuente_de_conocimiento(estado):
    return {"state": estado, "registry_version": "6.3", "observed_version": None,
            "attachmentId": None, "filename": None, "size": None, "created": None,
            "observed_sha256": None, "registry_sha256": None, "downloaded": False,
            "effectiveRisk": "MEDIUM", "derived_impact": [], "stale_derived": [],
            "blocking": False, "evidence": []}


def _proyecto_instalado(politica="DEFAULT"):
    """Un proyecto con el harness de desarrollo instalado, la barra registrada y probada, y el
    renderizador de esta version en disco. Sin senal de vida: la deja `_dibujar_en`."""
    proy = _tmp("harness-cb62-")
    claude = proy / ".claude"
    _json(claude / "harness.config.json", {"usuario": "Nahue"})
    _json(claude / "harness.lock.json", {"version": "0.28.0", "harness": ["comun", "desarrollo"],
                                         "instalado": "2026-09-24 10:00:00", "archivos": []})
    _json(claude / "harness.capacidades.json", {
        "schema_version": "integraciones/1.0", "version_harness": "0.28.0",
        "integraciones": {n: {"estado": "AVAILABLE", "motivo": "", "verificado_en": "2026-09-24T10:00:00",
                              "capacidades": []} for n in ("jira", "gitlab")}, "capacidades": {}})
    _json(claude / "harness.fuentes.json", {
        "schema_version": "sources-state/1.1", "verified_at": "2026-09-23T12:00:00", "ficha": None,
        "decisions": {}, "warnings": [], "pending_count": 0,
        "sources": dict((s, _fuente_de_conocimiento("CURRENT")) for s in TODAS)})
    h = claude / "harness"
    bin_d = h / "bin" / "desarrollo"
    for n in ("__init__.py", "libro.py", "barra.py"):
        _escribir(bin_d / "contabilidad" / n, "# prueba\n")
    _escribir(bin_d / "contabilidad" / "adaptadores" / "claude_code.py", "# adaptador\n")
    _escribir(bin_d / "contabilidad" / "statusline.py",
              'INTEGRATION_VERSION = "%s"\n' % SL.INTEGRATION_VERSION)
    for n in ("__init__.py", "libro.py", "resumen.py", "reporte.py"):
        _escribir(bin_d / "reporte_seguridad" / n, "# prueba\n")
    for n in B.SCHEMAS_DE_SEGURIDAD:
        _escribir(h / "schemas" / n, (RAIZ / "comun" / "schemas" / n).read_text(encoding="utf-8"))
    _escribir(h / "hooks" / "session-start.py", "# el hook\n")
    comando = "python '%s/.claude/harness/bin/desarrollo/contabilidad/statusline.py'" % proy.as_posix()
    _json(claude / "settings.json", {"permissions": _DENY_ENV,
                                     "statusLine": {"type": "command", "command": comando}})
    ruta = claude / "harness.presupuesto.json"
    if politica == "DEFAULT":
        shutil.copy(str(PLANTILLA), str(ruta))
    elif politica is not None:
        _json(ruta, politica)
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-24T10:00:00")
    return proy


def _dibujar_en(proy, stdin, no_color=None, momento="2026-09-24T10:00:05"):
    """Un dibujo de la barra de este repositorio sobre `proy`, en proceso, con la huella del comando
    registrado: deja el libro y la senal de vida como las deja el comando de verdad."""
    huella = B.huella_statusline(B.leer_statusline(str(proy))[0])
    with _NoColor(no_color):
        return SL.correr(json.dumps(stdin).encode("utf-8"), str(proy), momento=momento, huella=huella)[0]


def _verbose(proy):
    codigo, salida, error = _cli(["harness", "--verbose", "--proyecto", str(proy)])
    bloque = salida.split("\nConsumo de la Context Bar\n", 1)[-1].split("\nArchivos leídos", 1)[0] \
        if "\nConsumo de la Context Bar\n" in salida else ""
    return codigo, salida, error, bloque


def _con_ventana(proy, sesion=SESION, ventana=None, turnos=2, **de_mas):
    stdin = {"session_id": sesion,
             "transcript_path": _transcripcion(_tmp() / "t.jsonl", sesion, turnos=turnos)}
    if ventana is not None:
        stdin["context_window"] = ventana
    stdin.update(de_mas)
    return stdin


def test_e48_activa_no_es_lista(t):
    """E-48 — ACTIVA y sin limite de ventana: dice `Estado ACTIVA` y no que la barra esta lista. Con
    todo resuelto, lo dice."""
    proy = _proyecto_instalado()
    _dibujar_en(proy, _con_ventana(proy))
    codigo, _, _, bloque = _verbose(proy)
    t.igual("consumo E-48 sale 0", 0, codigo)
    t.igual("consumo E-48 la barra esta ACTIVE", "ACTIVE",
            B.resolver(str(proy))["runtimeComponents"]["contextBar"]["state"])
    t.contiene("consumo E-48 dice Estado ACTIVA", "Estado ACTIVA", bloque)
    t.no_contiene("consumo E-48 sin limite no dice que esta lista", LISTA, bloque)
    t.no_contiene("consumo E-48 ni con otras palabras", "está lista", bloque)
    _dibujar_en(proy, _con_ventana(proy, ventana=_ventana()), momento="2026-09-24T10:00:06")
    _, _, _, bloque = _verbose(proy)
    t.contiene("consumo E-48 con todo resuelto dice la linea de lista", LISTA, bloque)


def test_e49_el_limite_sin_resolver_se_explica(t):
    """E-49 — sin limite, dice `Límite de ventana SIN RESOLVER` y que el proveedor todavia no informo
    context_window_size."""
    for rotulo, ventana in (("solo la transcripcion", None),
                            ("una foto sin limite", _ventana(limite=0))):
        proy = _proyecto_instalado()
        _dibujar_en(proy, _con_ventana(proy, ventana=ventana))
        _, _, _, bloque = _verbose(proy)
        t.contiene("consumo E-49 %s: Límite de ventana SIN RESOLVER" % rotulo,
                   "Límite de ventana SIN RESOLVER", bloque)
        t.contiene("consumo E-49 %s: el proveedor todavia no informo context_window_size" % rotulo,
                   "el proveedor todavía no informó context_window_size", bloque)


_NOMBRES_DE_POLITICA = re.compile(r"\b(contextWarningAt|contextErrorAt|warningAt|errorAt|softLimit|"
                                  r"hardLimit)\b")


def test_e50_los_umbrales_que_faltan(t):
    """E-50 — sin umbrales de contexto: `Umbral WARNING SIN CONFIGURAR` y `Umbral ERROR SIN
    CONFIGURAR`, y nombra los que faltan, contextWarningAt y contextErrorAt, y solo esos."""
    for rotulo, politica in (("PROJECT sin umbrales de contexto", _PROYECTO_SIN_UMBRALES),
                             ("sin politica", None)):
        proy = _proyecto_instalado(politica)
        _dibujar_en(proy, _con_ventana(proy, ventana=_ventana()))
        _, _, _, bloque = _verbose(proy)
        t.contiene("consumo E-50 %s: Umbral WARNING SIN CONFIGURAR" % rotulo,
                   "Umbral WARNING SIN CONFIGURAR", bloque)
        t.contiene("consumo E-50 %s: Umbral ERROR SIN CONFIGURAR" % rotulo, "Umbral ERROR SIN CONFIGURAR",
                   bloque)
        t.igual("consumo E-50 %s: nombra contextWarningAt y contextErrorAt, y solo esos" % rotulo,
                ["contextErrorAt", "contextWarningAt"], sorted(set(_NOMBRES_DE_POLITICA.findall(bloque))))
        t.no_contiene("consumo E-50 %s: y no dice que esta lista" % rotulo, LISTA, bloque)
    proy = _proyecto_instalado(dict(_PROYECTO_SIN_UMBRALES, statusBar={"contextErrorAt": 0.95}))
    _dibujar_en(proy, _con_ventana(proy, ventana=_ventana()))
    _, _, _, bloque = _verbose(proy)
    t.igual("consumo E-50 falta uno solo: nombra ese", ["contextWarningAt"],
            sorted(set(_NOMBRES_DE_POLITICA.findall(bloque))))
    t.contiene("consumo E-50 y el otro en porcentaje", "Umbral ERROR 95%", bloque)


def test_e51_con_todo_resuelto(t):
    """E-51 — con limite, umbrales y presentation.ansi ENABLED: el limite, los dos umbrales en
    porcentaje, `Color ANSI HABILITADO` y la linea de lista."""
    proy = _proyecto_instalado()
    _dibujar_en(proy, _con_ventana(proy, ventana=_ventana()))
    t.igual("consumo E-51 la senal dice ENABLED", "ENABLED", (_senal(proy) or {}).get("presentation", {}).get("ansi"))
    _, _, _, bloque = _verbose(proy)
    for texto in ("Límite de ventana 200000", "Umbral WARNING 70%", "Umbral ERROR 90%",
                  "Color ANSI HABILITADO", LISTA):
        t.contiene("consumo E-51 dice %s" % texto, texto, bloque)


def test_e52_la_ventana_inconsistente_se_dice(t):
    """E-52 — con la ultima foto en CONTEXT_WINDOW_PROVIDER_INCONSISTENT, lo dice con ese codigo y
    no dice que la barra esta lista."""
    proy = _proyecto_instalado()
    _dibujar_en(proy, _con_ventana(proy, ventana=_ventana(entrada=260000, salida=10000)))
    _, _, _, bloque = _verbose(proy)
    t.contiene("consumo E-52 lo dice con su codigo", INCONSISTENTE, bloque)
    t.no_contiene("consumo E-52 y no dice que esta lista", LISTA, bloque)
    t.vacio("consumo E-52 ni muestra un porcentaje mayor que 100",
            [p for p in _porcentajes(bloque) if p > 100])


def test_e53_e54_el_color_que_vio_la_statusline(t):
    """E-53 / E-54 — con DISABLED_NO_COLOR dice que NO_COLOR esta en el proceso de la statusLine; con
    una senal sin presentation, SIN VERIFICAR, y la barra en el mismo estado que con esa senal."""
    proy = _proyecto_instalado()
    _dibujar_en(proy, _con_ventana(proy, ventana=_ventana()), no_color="1")
    t.igual("consumo E-53 la senal dice DISABLED_NO_COLOR", "DISABLED_NO_COLOR",
            (_senal(proy) or {}).get("presentation", {}).get("ansi"))
    _, _, _, bloque = _verbose(proy)
    t.contiene("consumo E-53 Color ANSI DESHABILITADO POR NO_COLOR", "Color ANSI DESHABILITADO POR NO_COLOR",
               bloque)
    t.contiene("consumo E-53 y que NO_COLOR esta definido en el proceso de la statusLine",
               "NO_COLOR está definido en el proceso de la statusLine", bloque)

    estados = {}
    for rotulo, presentacion in (("con presentation", B.ANSI_ENABLED), ("sin presentation", None)):
        B.escribir_senal_de_vida(str(proy), SESION, B.BLOCK4_OK, SL.INTEGRATION_VERSION,
                                 momento="2026-09-24T10:00:09",
                                 huella=B.huella_statusline(B.leer_statusline(str(proy))[0]),
                                 presentacion=presentacion)
        estados[rotulo] = B.resolver(str(proy))["runtimeComponents"]["contextBar"]
        _, _, _, estados[rotulo + " verbose"] = _verbose(proy)
    t.verdadero("consumo E-54 la senal sin presentation es la de 1.1.0: sin la clave",
                "presentation" not in (_senal(proy) or {}))
    t.contiene("consumo E-54 dice Color ANSI SIN VERIFICAR", "Color ANSI SIN VERIFICAR",
               estados["sin presentation verbose"])
    t.igual("consumo E-54 el estado de la barra es el mismo con y sin presentation",
            estados["con presentation"], estados["sin presentation"])
    t.igual("consumo E-54 y es ACTIVE, el de una senal buena de 1.1.0", "ACTIVE",
            estados["sin presentation"]["state"])


def test_e55_e56_verbose_no_imprime_la_sesion(t):
    """E-55 / E-56 — la salida de harness --verbose no tiene una marca del prompt de la transcripcion,
    ni el token del .env, ni uno puesto en el stdin de la barra."""
    marca = "MARCA-DEL-PROMPT-CB62-" + uuid.uuid4().hex[:6]
    proy = _proyecto_instalado()
    _escribir(proy / ".env", "JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    extra = [{"type": "user", "sessionId": SESION, "message": {"role": "user", "content": marca}},
             {"type": "assistant", "sessionId": SESION, "timestamp": "2026-09-30T10:05:00",
              "message": {"id": "msg_marca", "model": "m-cb62", "usage": {"input_tokens": 1,
                                                                        "output_tokens": 1},
                          "content": [{"type": "text", "text": marca + " " + TOKEN}]}}]
    stdin = {"session_id": SESION, "context_window": _ventana(),
             "transcript_path": _transcripcion(_tmp() / "t.jsonl", SESION, extra=extra),
             "model": {"id": TOKEN, "display_name": TOKEN}, "prompt": marca + TOKEN,
             "workspace": {"current_dir": TOKEN}}
    _dibujar_en(proy, stdin)
    codigo, salida, error, bloque = _verbose(proy)
    t.igual("consumo E-55 sale 0", 0, codigo)
    t.verdadero("consumo E-55 el bloque de consumo esta", bool(bloque))
    t.no_contiene("consumo E-55 no sale la marca del prompt", marca, salida + error)
    t.no_contiene("consumo E-56 no sale el token", TOKEN, salida + error)
    t.no_contiene("consumo E-56 ni un pedazo", TOKEN[:12], salida + error)
    t.no_contiene("consumo E-56 y el libro tampoco lo guardo", TOKEN,
                  _libro_de(proy, SESION).read_text(encoding="utf-8"))


def test_e76_la_fuente_de_contexto(t):
    """E-76 — `Fuente de contexto CLAUDE_CODE_STATUSLINE` con una foto, TRANSCRIPT_ONLY sin fotos y con
    llamadas al modelo, y SIN RESOLVER sin ninguna de las dos."""
    casos = (("con una foto", {"ventana": _ventana()}, "CLAUDE_CODE_STATUSLINE"),
             ("sin fotos y con llamadas", {}, "TRANSCRIPT_ONLY"),
             ("sin ninguna de las dos", {"turnos": 0}, "SIN RESOLVER"))
    for rotulo, de_mas, esperado in casos:
        proy = _proyecto_instalado()
        _dibujar_en(proy, _con_ventana(proy, **de_mas))
        _, _, _, bloque = _verbose(proy)
        t.contiene("consumo E-76 %s: Fuente de contexto %s" % (rotulo, esperado),
                   "Fuente de contexto %s" % esperado, bloque)
    proy = _proyecto_instalado()
    _, _, _, bloque = _verbose(proy)
    t.contiene("consumo E-76 sin senal de vida tampoco hay fuente: SIN RESOLVER",
               "Fuente de contexto SIN RESOLVER", bloque)


def test_e78_verbose_dice_que_politica_hay(t):
    """E-78 — harness --verbose dice `Política DEFAULT` con la plantilla, PROJECT con otra valida,
    MISSING sin archivo e INVALID con una que no valida: lo mismo que setup (E-43) sobre el mismo
    archivo, y sin cambiarlo."""
    con_el_id = dict(_default(), task={"softLimit": None, "hardLimit": 50.0})
    casos = (("la plantilla", "DEFAULT", "DEFAULT"),
             ("el id del harness con un hardLimit", "PROJECT", con_el_id),
             ("una del proyecto sin umbrales de contexto", "PROJECT", _PROYECTO_SIN_UMBRALES),
             ("sin archivo", "MISSING", None),
             ("una sin currency", "INVALID", {"policyId": "sin-moneda"}),
             ("una que no es JSON", "INVALID", "{ no es json"))
    for rotulo, esperado, politica in casos:
        proy = _proyecto_instalado(None if isinstance(politica, str) and politica != "DEFAULT"
                                   else politica)
        ruta = proy / ".claude" / "harness.presupuesto.json"
        if isinstance(politica, str) and politica != "DEFAULT":
            _escribir(ruta, politica)
        antes = ruta.read_bytes() if ruta.is_file() else None
        codigo, _, _, bloque = _verbose(proy)
        t.igual("consumo E-78 %s: harness --verbose sale 0" % rotulo, 0, codigo)
        t.contiene("consumo E-78 %s: dice Política %s" % (rotulo, esperado), "Política %s" % esperado,
                   bloque)
        otras = [c for c in ("DEFAULT", "PROJECT", "MISSING", "INVALID") if c != esperado]
        t.vacio("consumo E-78 %s: y ninguna otra clase" % rotulo,
                [c for c in otras if "Política %s" % c in bloque])
        t.verdadero("consumo E-78 %s: el archivo queda igual byte a byte" % rotulo,
                    (ruta.read_bytes() if ruta.is_file() else None) == antes)
        _, salida_setup, _ = _cli(["setup", "--proyecto", str(proy)])
        t.contiene("consumo E-78 %s: con el mismo criterio que setup" % rotulo,
                   "política %s" % esperado, _bloque_de_setup(salida_setup))
        t.verdadero("consumo E-78 %s: y setup tampoco lo cambia" % rotulo,
                    (ruta.read_bytes() if ruta.is_file() else None) == antes)


# ══ La senal de vida ═══════════════════════════════════════════════════════════════════════════

def test_e57_a_e60_la_senal_dice_el_color(t):
    """E-57 / E-58 / E-59 / E-60 — el renderizador instalado escribe presentation.ansi segun NO_COLOR de
    su propio proceso, y la senal tiene las seis claves y ningun numero."""
    proy, _ = _instalado()
    for escenario, rotulo, color, no_color, esperado in (
            ("E-57", "sin NO_COLOR", True, "1", "ENABLED"),
            ("E-58", "con NO_COLOR=1", False, "1", "DISABLED_NO_COLOR"),
            ("E-59", "con NO_COLOR= vacia", False, "", "DISABLED_NO_COLOR")):
        sesion = _nueva_sesion()
        _dibujar({"session_id": sesion, "transcript_path": _transcripcion(_tmp() / "t.jsonl", sesion),
                  "context_window": _ventana()}, color=color, no_color=no_color)
        senal = _senal(proy) or {}
        t.igual("consumo %s %s: la senal es de ese dibujo" % (escenario, rotulo), sesion, senal.get("sessionId"))
        t.igual("consumo %s %s: presentation.ansi %s" % (escenario, rotulo, esperado), {"ansi": esperado},
                senal.get("presentation"))
        t.igual("consumo E-60 %s: las seis claves" % rotulo,
                sorted(["sessionId", "configurationFingerprint", "integrationVersion", "lastRenderedAt",
                        "block4", "presentation"]), sorted(senal))
        numeros = [k for k, v in senal.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        numeros += [k for k, v in (senal.get("presentation") or {}).items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool)]
        t.igual("consumo E-60 %s: ningun valor es un numero" % rotulo, [], numeros)
        t.verdadero("consumo E-60 %s: y cumple el contrato" % rotulo, B.cumple(senal, B.CONTRATO_SENAL))


def test_e61_una_senal_de_1_1_0_cumple(t):
    """E-61 — una senal con las cinco claves de 1.1.0 cumple el contrato nuevo."""
    vieja = {"sessionId": SESION, "configurationFingerprint": None, "integrationVersion": "1.1.0",
             "lastRenderedAt": "2026-09-24T10:00:01", "block4": "OK"}
    t.verdadero("consumo E-61 cumple CONTRATO_SENAL", B.cumple(vieja, B.CONTRATO_SENAL))
    t.igual("consumo E-61 y su color es SIN VERIFICAR, no un color inventado", B.ANSI_UNVERIFIED,
            B.ansi_de_la_senal(vieja))
    proy = _proyecto_instalado()
    _json(proy / ".claude" / "runtime" / "contextbar.json", vieja)
    senal, problema = B.leer_senal_de_vida(str(proy))
    t.igual("consumo E-61 leer_senal_de_vida la toma", (vieja, None), (senal, problema))


# ══ La documentacion ═══════════════════════════════════════════════════════════════════════════

def _seccion_de_la_barra():
    """El cuerpo de `### La Context Bar...` hasta el proximo titulo de su nivel o de uno mayor, como
    lo lee colores E-21. Los `#` de un bloque de codigo no son titulos."""
    lineas, inicio, en_codigo = DOC.read_text(encoding="utf-8").splitlines(), None, False
    for i, linea in enumerate(lineas):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue
        if inicio is None:
            if re.match(r"###\s+La Context Bar\b", linea):
                inicio = i
        elif re.match(r"#{1,3}\s", linea):
            return " ".join(" ".join(lineas[inicio + 1:i]).split())
    return None if inicio is None else " ".join(" ".join(lineas[inicio + 1:]).split())


def test_e69_ctx_y_tok_son_dos_metricas(t):
    """E-69 — la seccion dice que Ctx es la ocupacion de la ventana actual y Tok los tokens
    acumulados de la sesion en el libro, y que son dos metricas distintas."""
    seccion = _seccion_de_la_barra() or ""
    t.verdadero("consumo E-69 la seccion esta", bool(seccion))
    t.contiene("consumo E-69 Ctx es la ocupacion de la ventana actual",
               "`Ctx` es la ocupación de la ventana actual", seccion)
    t.contiene("consumo E-69 Tok son los tokens acumulados de la sesion en el libro",
               "`Tok` son los tokens acumulados de la sesión en el libro", seccion)
    t.contiene("consumo E-69 y son dos metricas distintas", "son dos métricas distintas", seccion)


def test_e70_despues_de_compactar_ctx_baja_y_tok_sube(t):
    """E-70 — una foto de 150000, mas transcripcion y una foto de 60000: Ctx baja mientras Tok sube. Y
    la seccion dice que despues de compactar eso es lo esperable."""
    antes = [_llamada(1), _evento_foto(150000, cursor=1)]
    despues = antes + [_llamada(2, entrada=40, salida=900, lectura=20000), _evento_foto(60000, cursor=2)]
    uno, dos = _estado(antes, _default()), _estado(despues, _default())
    t.verdadero("consumo E-70 Ctx baja", dos["context"]["tokens"] < uno["context"]["tokens"])
    suma = lambda e: sum(e["tokens"][c] for c in ("inputTokens", "outputTokens", "cacheReadTokens",  # noqa: E731
                                                  "cacheCreationTokens"))
    t.verdadero("consumo E-70 mientras Tok sube", suma(dos) > suma(uno))
    t.igual("consumo E-70 en la linea: de 75% a 30%", ("Ctx 75%", "Ctx 30%"),
            (_ctx(_linea(antes, _default())), _ctx(_linea(despues, _default()))))
    seccion = _seccion_de_la_barra() or ""
    frase = [f for f in re.split(r"(?<=[.;])\s+", seccion) if "compactar" in f]
    t.verdadero("consumo E-70 la seccion dice que despues de compactar Ctx baja, Tok sube, y es lo esperable",
                any("Ctx" in f and "baje" in f and "Tok" in f and re.search(r"\bsub(e|iendo)\b", f)
                    and "esperable" in f for f in frase))


def test_e71_los_umbrales_son_defaults_del_harness(t):
    """E-71 — la seccion dice que 70% y 90% son defaults operativos del harness, no reglas de ES0901
    ni de ES0902."""
    seccion = _seccion_de_la_barra() or ""
    frases = [f for f in re.split(r"(?<=[.;:])\s+", seccion) if "defaults operativos" in f]
    t.verdadero("consumo E-71 70% y 90% son defaults operativos del harness, no reglas de ES0901 ni ES0902",
                any("70%" in f and "90%" in f and "del harness" in f and "no reglas de ES0901 ni de ES0902" in f
                    for f in frases))
