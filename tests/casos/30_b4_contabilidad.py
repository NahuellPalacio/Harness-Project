# B4: contar lo que se gasto, sin inventar lo que no se pudo medir.
#
# Escenarios E-01 a E-39 de docs/cambios/bloque-4-contabilidad-de-ejecucion/spec.md. Entre
# parentesis, el B4-nn del pedido de instalacion.
#
# 🔴 Nada de esto ejecuta una unidad de trabajo ni llama a un modelo. Lo que se verifica es la
# CONTABILIDAD: que un hecho visto dos veces cuente una, que una foto de la ventana no se sume,
# que lo que no se pudo atribuir no se reparta, que un plan fijo no se presente como gasto y que
# el Bloque 4 no pueda aprobar nada.
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
PAQUETE = BIN / "contabilidad"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from contabilidad import agregacion as c_agr            # noqa: E402
from contabilidad import barra as c_barra               # noqa: E402
from contabilidad import costos as c_costos             # noqa: E402
from contabilidad import eventos as c_eventos           # noqa: E402
from contabilidad import libro as c_libro               # noqa: E402
from contabilidad import presupuesto as c_pres          # noqa: E402
from contabilidad import reporte as c_reporte           # noqa: E402
from contabilidad import tiempo as c_tiempo             # noqa: E402
from contabilidad.adaptadores import claude_code as c_cc    # noqa: E402
from contabilidad.adaptadores import codex as c_codex       # noqa: E402
from contabilidad.adaptadores import contrato as c_contrato  # noqa: E402
from contabilidad.adaptadores import registro as c_reg       # noqa: E402
from orquestacion import consumo as orq_consumo         # noqa: E402

TAREA = "GCBA-4321"
ADAPTADOR = "test"

POLITICA = {
    "policyId": "gcba", "currency": "USD", "billingMode": "SUBSCRIPTION",
    "task": {"softLimit": 5.0, "hardLimit": 20.0},
    "premiumModel": {"requiresHumanApproval": True, "projectedOverrunRequiresApproval": True},
    "statusBar": {"warningAt": 0.5, "errorAt": 0.9,
                  "contextWarningAt": 0.7, "contextErrorAt": 0.9},
}


# -- las piezas de los casos ---------------------------------------------------

def _uso(entrada=10, salida=100, lectura=1000, creacion=0, modelo="m-1", proveedor="p-1",
         contexto=None, limite=None, estado="RESOLVED"):
    return {"state": estado, "provider": proveedor, "model": modelo,
            "inputTokens": entrada, "outputTokens": salida,
            "cacheReadTokens": lectura, "cacheCreationTokens": creacion,
            "contextTokens": contexto, "contextLimit": limite}


def _costo(actual=None, equivalente=1.5, modo="SUBSCRIPTION"):
    return {"state": "RESOLVED", "actual": actual, "apiEquivalentEstimated": equivalente,
            "actualState": "FIXED_PLAN", "provider": "p-1", "model": "m-1",
            "pricingSource": "fuente", "pricingVersionOrDate": "2026-09-20",
            "currency": "USD", "billingMode": modo, "calculationMethod": "PROVIDER_REPORTED"}


def _ev(tipo="MODEL_CALL_COMPLETED", tarea=TAREA, adaptador=ADAPTADOR, **campos):
    return c_eventos.nuevo(tipo, tarea, adaptador, **campos)


def _tmp():
    return tempfile.mkdtemp(prefix="b4_")


def _transcripcion(carpeta, repeticiones=2, con_estado_de_costo=True, sesion="s-1",
                   modelo="m-grande"):
    """Una transcripcion con la forma real: una linea por bloque de contenido."""
    ruta = os.path.join(carpeta, "sesion.jsonl")
    uso = {"input_tokens": 10, "output_tokens": 100,
           "cache_read_input_tokens": 5000, "cache_creation_input_tokens": 200}
    lineas = []
    for _ in range(repeticiones):
        lineas.append({"type": "assistant", "sessionId": sesion,
                       "timestamp": "2026-09-20T10:00:00",
                       "message": {"id": "msg_1", "model": modelo, "usage": uso}})
    lineas.append({"type": "assistant", "sessionId": sesion,
                   "timestamp": "2026-09-20T10:01:00",
                   "message": {"id": "msg_2", "model": modelo,
                               "usage": {"input_tokens": 2, "output_tokens": 50,
                                         "cache_read_input_tokens": 6000,
                                         "cache_creation_input_tokens": 0}}})
    if con_estado_de_costo:
        # Dos estados acumulados: el segundo incluye al primero.
        for total, plata in ((1000, 1.0), (60000, 3.25)):
            lineas.append({"type": "cost-state", "sessionId": sesion,
                           "totalDuration": total, "totalAPIDuration": total // 2,
                           "totalToolDuration": total // 4, "hasUnknownModelCost": False,
                           "startTime": 1,
                           "modelUsage": {modelo: {"inputTokens": 40, "outputTokens": 900,
                                                   "cacheReadInputTokens": 90000,
                                                   "cacheCreationInputTokens": 900,
                                                   "costUSD": plata}}})
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        for dato in lineas:
            f.write(json.dumps(dato) + "\n")
    return ruta


def _correr_cli(argv):
    spec = importlib.util.spec_from_file_location("dev_harness_b4", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(argv)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _fuentes_del_paquete():
    return sorted(PAQUETE.rglob("*.py"))


def _relativo(ruta):
    return str(ruta.relative_to(PAQUETE)).replace(os.sep, "/")


# Verbos que pueden acortar o desaparecer un archivo. El barrido es sobre el PAQUETE ENTERO,
# no sobre una lista de nombres de funcion: un `def compactar(ruta): os.remove(ruta)` no lo
# agarraba ninguna lista de verbos prohibidos, y borra el libro igual.
DESTRUCTIVOS = ("os.remove", "os.unlink", "os.truncate", "os.rename", "os.replace",
                "shutil.rmtree", "shutil.move", ".truncate(", ".unlink(", "os.ftruncate")


def _destructivos_en(texto):
    return sorted(v for v in DESTRUCTIVOS if v in texto)


def _aperturas():
    """Cada `open`/`io.open` del paquete, con su modulo, su funcion y su modo.

    Se lee el AST y no el texto: es lo unico que distingue una apertura de lectura de una de
    escritura sin depender de como este escrita la linea.
    """
    import ast

    encontradas = []
    for fuente in _fuentes_del_paquete():
        arbol = ast.parse(fuente.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for interno in ast.walk(nodo):
                if not isinstance(interno, ast.Call):
                    continue
                func = interno.func
                es_open = (isinstance(func, ast.Name) and func.id == "open") or (
                    isinstance(func, ast.Attribute) and func.attr == "open")
                if not es_open:
                    continue
                modo = None
                if len(interno.args) > 1 and isinstance(interno.args[1], ast.Constant):
                    modo = interno.args[1].value
                for kw in interno.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        modo = kw.value.value
                encontradas.append((_relativo(fuente), nodo.name, modo or "r"))
    return sorted(set(encontradas))


def _contenedor_con_numero(valor, visto=None):
    """True si un contenedor guarda un numero en cualquier nivel.

    Una tabla de tarifas escrita a mano es necesariamente eso: un diccionario o una lista con
    numeros adentro. Buscar la palabra `PerMillion` no alcanzaba — `{"input": 3.0}` es una
    tarifa igual y no usa ninguna palabra que un patron pueda esperar.
    """
    visto = visto or set()
    if id(valor) in visto:
        return False
    visto.add(id(valor))
    if isinstance(valor, bool):
        return False
    if isinstance(valor, (int, float)):
        return True
    if isinstance(valor, dict):
        return any(_contenedor_con_numero(v, visto) for v in valor.values()) or any(
            _contenedor_con_numero(k, visto) for k in valor)
    if isinstance(valor, (list, tuple, set)):
        return any(_contenedor_con_numero(v, visto) for v in valor)
    return False


def _claves_json(nodo, buscadas):
    """Las claves de `buscadas` que aparecen en cualquier nivel del documento."""
    halladas = set()
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if str(clave) in buscadas:
                halladas.add(str(clave))
            halladas |= _claves_json(valor, buscadas)
    elif isinstance(nodo, list):
        for item in nodo:
            halladas |= _claves_json(item, buscadas)
    return halladas


RELLENO = "x" * 2000
MARCA_DE_RECORTE = "recortado por el harness"


# El entero y el flotante mas largos que el tope numerico deja pasar. `abs()` no mira el
# signo, asi que el negativo es un caracter mas largo que el positivo.
ENTERO_MAS_LARGO = -(10 ** c_eventos.DIGITOS - 1)
FLOTANTE_MAS_LARGO = -1.2345678901234567e-308


def _valor_maximo(sub, relleno=RELLENO):
    """El valor mas grande que ese pedazo del contrato permite. El MAS grande, no el primero."""
    if "enum" in sub:
        return max(sub["enum"], key=len)
    tipos = sub.get("type")
    tipos = tipos if isinstance(tipos, list) else [tipos]
    if "object" in tipos:
        return dict((k, _valor_maximo(v, relleno))
                    for k, v in (sub.get("properties") or {}).items())
    if "integer" in tipos:
        return ENTERO_MAS_LARGO
    if "number" in tipos:
        return FLOTANTE_MAS_LARGO
    if "boolean" in tipos:
        return True
    return relleno


def _maximo_del_contrato(relleno=RELLENO):
    """El evento mas grande que el contrato permite, ARMADO DESDE EL CONTRATO.

    🔴 No escrito a mano. Una version anterior de este test armaba un evento grande a mano y
    lo llamaba "el maximo": se olvidaba de `eventId`, `timestamp`, `taskId` y `source.adapter`,
    asi que medía 8.848 caracteres cuando el maximo eran 10.182. Derivarlo del schema es lo
    unico que hace que un campo nuevo del contrato entre en la medicion solo.

    `relleno` existe porque el techo se mide con VARIOS rellenos distintos: es la unica forma
    de mostrar que lo que se publica no depende de lo que haya adentro de los campos.
    """
    esquema = c_eventos.cargar_schema()
    evento = {}
    for clave, sub in (esquema.get("properties") or {}).items():
        if clave == "metadata":
            evento[clave] = dict((k, relleno) for k in c_eventos.CLAVES_DE_METADATA)
        else:
            evento[clave] = _valor_maximo(sub, relleno)
    return evento


def _contenido_de(nodo):
    """Cuanto TEXTO tiene el evento. La unica magnitud estable.

    🔴 El largo de la linea escrita no sirve como techo, y esto costo una pasada del
    refutador: `json.dumps` escapa, asi que una barra invertida ocupa dos caracteres y un
    caracter de control ocupa seis. Los mismos 26 campos en su tope dan 10.266 caracteres de
    linea con relleno ASCII, 18.066 con barras y 49.266 con caracteres de control — y las
    tres veces el contenido es el mismo. Un `\\u0001` repetido trescientas veces ocupa mil
    ochocientos caracteres de linea y sigue sin ser una conversacion.
    """
    if isinstance(nodo, dict):
        return sum(len(str(k)) + _contenido_de(v) for k, v in nodo.items())
    if isinstance(nodo, list):
        return sum(_contenido_de(v) for v in nodo)
    if isinstance(nodo, str):
        return len(nodo)
    return 0


def _todos_acotados(nodo, tope):
    if isinstance(nodo, dict):
        return all(_todos_acotados(v, tope) for v in nodo.values())
    if isinstance(nodo, list):
        return all(_todos_acotados(v, tope) for v in nodo)
    if isinstance(nodo, str):
        return len(nodo) <= tope
    return True


def _recortes_en(nodo):
    """Cuantos campos de texto llegaron recortados. Es el conteo de campos de texto reales."""
    if isinstance(nodo, dict):
        return sum(_recortes_en(v) for v in nodo.values())
    if isinstance(nodo, list):
        return sum(_recortes_en(v) for v in nodo)
    return 1 if isinstance(nodo, str) and MARCA_DE_RECORTE in nodo else 0


def _json_que_se_instalan():
    rutas = sorted((RAIZ / "comun").rglob("*.json"))
    rutas += sorted((RAIZ / "harnesses").rglob("*.json"))
    return [r for r in rutas if "__pycache__" not in str(r)]


# -- E-01 a E-05 — el contrato del evento y el libro ---------------------------

def test_e01_el_evento_valida_contra_su_contrato(t):
    """E-01 (B4-01) — un evento valido pasa; al que le falta un obligatorio no se escribe."""
    evento = _ev(usage=_uso(), dedupKey="k-1")
    t.igual("E-01 sin errores", [], c_eventos.validar(evento))
    t.igual("E-01 el tipo", "MODEL_CALL_COMPLETED", evento["eventType"])
    t.igual("E-01 la tarea", TAREA, evento["taskId"])
    t.verdadero("E-01 trae adaptador", evento["source"]["adapter"] == ADAPTADOR)

    for obligatorio in ("eventId", "eventType", "timestamp", "taskId", "source"):
        roto = dict(evento)
        del roto[obligatorio]
        errores = c_eventos.validar(roto)
        t.verdadero("E-01 sin %s no valida" % obligatorio, bool(errores))
        carpeta = _tmp()
        try:
            ruta = c_libro.ruta_de(carpeta, TAREA)
            try:
                c_libro.agregar(ruta, roto)
                escribio = True
            except c_eventos.EventoInvalido:
                escribio = False
            t.verdadero("E-01 sin %s no se escribe" % obligatorio, not escribio)
            t.verdadero("E-01 sin %s no quedo archivo" % obligatorio,
                        not os.path.isfile(ruta))
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)

    t.verdadero("E-01 un tipo inventado se rechaza",
                _levanta(lambda: _ev(tipo="TASK_EXPLODED")))
    t.verdadero("E-01 sin tarea se rechaza",
                _levanta(lambda: _ev(tarea="")))
    t.igual("E-01 son trece tipos", 13, len(c_eventos.TIPOS))


def _levanta(fn):
    try:
        fn()
    except Exception:
        return True
    return False


def test_e02_los_schemas_pasan_por_el_validador(t):
    """E-02 — los dos schemas enteros, sin una palabra que el interprete no lea."""
    armador = c_eventos._armador()
    t.verdadero("E-02 hay validador", armador is not None)
    for nombre in ("execution-accounting-event.schema.json", "budget-policy.schema.json"):
        ruta = SCHEMAS / nombre
        t.verdadero("E-02 existe %s" % nombre, ruta.is_file())
        with io.open(str(ruta), encoding="utf-8") as f:
            esquema = json.load(f)
        soportado = True
        try:
            armador.controlar_soporte(esquema)
        except Exception:
            soportado = False
        t.verdadero("E-02 %s es soportado" % nombre, soportado)
        t.verdadero("E-02 %s declara titulo" % nombre, bool(esquema.get("title")))
        t.verdadero("E-02 %s declara descripcion" % nombre, bool(esquema.get("description")))

    t.igual("E-02 la politica de ejemplo valida", [], c_pres.validar(POLITICA))


def test_e02b_el_validador_lee_type_como_lista(t):
    """E-02b — se amplio el validador en vez de aflojar el schema."""
    armador = c_eventos._armador()
    esquema = {"type": "object", "properties": {"x": {"type": ["integer", "null"]}}}
    t.igual("E-02b un entero pasa", [], armador.validar({"x": 3}, esquema))
    t.igual("E-02b null pasa", [], armador.validar({"x": None}, esquema))
    t.verdadero("E-02b un string no pasa", bool(armador.validar({"x": "3"}, esquema)))
    t.verdadero("E-02b un booleano no pasa", bool(armador.validar({"x": True}, esquema)))

    roto = {"type": ["integer", "fecha"]}
    t.verdadero("E-02b un tipo inventado se rechaza al controlar",
                _levanta(lambda: armador.controlar_soporte(roto)))
    t.verdadero("E-02b `null` es un tipo conocido", "null" in armador.TIPOS)
    # Lo que ya valia sigue valiendo, con el mismo texto.
    solo = {"type": "integer"}
    t.contiene("E-02b el mensaje viejo no cambio", "se esperaba integer y vino un booleano",
               " ".join(armador.validar(True, solo)))


def test_e03_el_libro_es_append_only(t):
    """E-03 (B4-02) — los bytes anteriores no se tocan, y no existe el verbo que los tocaria."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        primero = _ev(dedupKey="k-1", usage=_uso())
        c_libro.agregar(ruta, primero)
        with io.open(ruta, "rb") as f:
            antes = f.read()

        c_libro.agregar(ruta, _ev(dedupKey="k-2", usage=_uso(salida=200)))
        with io.open(ruta, "rb") as f:
            despues = f.read()
        t.verdadero("E-03 lo anterior quedo intacto", despues.startswith(antes))
        t.verdadero("E-03 el archivo crecio", len(despues) > len(antes))
        t.igual("E-03 hay dos lineas", 2, len(c_libro.leer(ruta)))

        # 🔴 El barrido es sobre el PAQUETE ENTERO y por lo que el codigo HACE, no por como se
        # llama. Un `def compactar(ruta): os.remove(ruta)` en un modulo nuevo pasaba en verde
        # contra una lista de once nombres de funcion.
        t.verdadero("E-03 hay modulos que barrer", len(_fuentes_del_paquete()) >= 13)
        for archivo in _fuentes_del_paquete():
            t.igual("E-03 %s no acorta ni borra nada" % _relativo(archivo), [],
                    _destructivos_en(archivo.read_text(encoding="utf-8")))

        # Y el barrido encuentra las formas de verdad, no las que le vienen bien.
        for fuga in ("def compactar(ruta):\n    os.remove(ruta)",
                     "os.unlink(ruta)", "shutil.rmtree(carpeta_de(p, t))",
                     "open(ruta).truncate(0)", "os.replace(nuevo, ruta)",
                     "Path(ruta).unlink()"):
            t.verdadero("E-03 se detecta: %s" % fuga.split("\n")[-1][:34],
                        bool(_destructivos_en(fuga)))
        base = (PAQUETE / "libro.py").read_text(encoding="utf-8")
        t.igual("E-03 la premisa: libro.py esta limpio", [], _destructivos_en(base))
        t.verdadero("E-03 y con un borrado adentro deja de estarlo",
                    bool(_destructivos_en(base + "\ndef compactar(r):\n    os.remove(r)\n")))

        # La otra puerta: los dos modulos que SI escriben en modo `w` se niegan a tocar el
        # libro. Que `agregar` sea append-only no sirve si el de al lado lo trunca.
        for quien, fn in (("el resumen", c_agr.escribir), ("el reporte", c_reporte.escribir)):
            t.verdadero("E-03 %s no escribe sobre el libro" % quien,
                        _levanta(lambda f=fn: f({"taskId": TAREA}, ruta)))
        t.verdadero("E-03 y sobre su propio archivo si",
                    not _levanta(lambda: c_agr.escribir(
                        c_agr.resumir(c_libro.leer(ruta), task_id=TAREA),
                        c_libro.ruta_de(carpeta, TAREA, c_libro.RESUMEN))))
        t.verdadero("E-03 el libro sigue entero", len(c_libro.leer(ruta)) == 2)
        t.verdadero("E-03 reconoce su archivo por nombre", c_libro.es_el_libro("x/ledger.jsonl"))
        t.verdadero("E-03 y no confunde otro", not c_libro.es_el_libro("x/summary.json"))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e04_un_evento_repetido_no_entra_dos_veces(t):
    """E-04 (B4-02) — reingerir la misma fuente es inofensivo."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        evento = _ev(dedupKey="k-1", usage=_uso())
        escrito, _ = c_libro.agregar(ruta, evento)
        t.verdadero("E-04 la primera vez se escribe", escrito)
        repetido, _ = c_libro.agregar(ruta, evento)
        t.verdadero("E-04 la segunda no", not repetido)
        t.igual("E-04 quedo una linea", 1, len(c_libro.leer(ruta)))

        escritos, salteados, _ = c_libro.agregar_varios(ruta, [evento, evento, evento])
        t.igual("E-04 ninguno se escribe de nuevo", 0, escritos)
        t.igual("E-04 los tres se saltean", 3, salteados)

        # El id es determinista: la misma fuente leida dos veces trae el mismo id.
        t.igual("E-04 el id se deriva", c_eventos.id_de("a", "MODEL_CALL_COMPLETED", "k"),
                c_eventos.id_de("a", "MODEL_CALL_COMPLETED", "k"))
        t.verdadero("E-04 y cambia con la clave",
                    c_eventos.id_de("a", "MODEL_CALL_COMPLETED", "k")
                    != c_eventos.id_de("a", "MODEL_CALL_COMPLETED", "k2"))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e05_una_correccion_es_un_evento_nuevo(t):
    """E-05 (B4-22) — el original queda byte a byte y la agregacion aplica la correccion."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        original = _ev(dedupKey="k-1", usage=_uso(salida=1000), workUnitId="u-1")
        c_libro.agregar(ruta, original)
        with io.open(ruta, "rb") as f:
            antes = f.read()

        correccion = c_eventos.corregir(
            original, "el proveedor reporto mal la salida", ADAPTADOR,
            usage=_uso(salida=100), workUnitId="u-1")
        t.igual("E-05 el tipo es una correccion", "ACCOUNTING_CORRECTION",
                correccion["eventType"])
        t.igual("E-05 dice que enmienda", original["eventId"], correccion["correctsEventId"])
        t.contiene("E-05 lleva el motivo", "reporto mal", correccion["metadata"]["reason"])
        t.verdadero("E-05 una correccion sin motivo se rechaza",
                    _levanta(lambda: c_eventos.corregir(original, "", ADAPTADOR)))
        t.verdadero("E-05 una correccion sin original se rechaza",
                    _levanta(lambda: _ev(tipo="ACCOUNTING_CORRECTION")))

        c_libro.agregar(ruta, correccion)
        with io.open(ruta, "rb") as f:
            despues = f.read()
        t.verdadero("E-05 el original quedo igual", despues.startswith(antes))

        resumen = c_agr.resumir(c_libro.leer(ruta), task_id=TAREA)
        t.igual("E-05 vale la correccion, no el original", 100,
                resumen["tokens"]["outputTokens"])
        t.igual("E-05 el original quedo contado como corregido", 1,
                resumen["events"]["corrected"])
        t.igual("E-05 hay una correccion", 1, resumen["events"]["corrections"])
        t.igual("E-05 el libro sigue teniendo las dos lineas", 2, len(c_libro.leer(ruta)))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- E-06 a E-10 — deduplicacion y ventana de contexto -------------------------

def test_e06_el_mismo_hecho_cuenta_una_vez(t):
    """E-06 (B4-03) — dos eventos distintos con la misma clave son el mismo hecho."""
    uno = _ev(dedupKey="msg|abc", usage=_uso(salida=100), eventId="ev_uno")
    otro = _ev(dedupKey="msg|abc", usage=_uso(salida=100), eventId="ev_otro")
    t.verdadero("E-06 son eventos distintos", uno["eventId"] != otro["eventId"])

    resumen = c_agr.resumir([uno, otro], task_id=TAREA)
    t.igual("E-06 se conto uno solo", 100, resumen["tokens"]["outputTokens"])
    t.igual("E-06 y el otro se descarto", 1, resumen["events"]["duplicates"])
    t.igual("E-06 eventos contados", 1, resumen["events"]["counted"])

    # Sin clave no se puede deduplicar, y eso NO se disimula: los dos cuentan.
    sin_clave_a = _ev(usage=_uso(salida=100), eventId="ev_a")
    sin_clave_b = _ev(usage=_uso(salida=100), eventId="ev_b")
    sin_clave = c_agr.resumir([sin_clave_a, sin_clave_b], task_id=TAREA)
    t.igual("E-06 sin clave cuentan los dos", 200, sin_clave["tokens"]["outputTokens"])

    # Y el contrato del adaptador no deja producir un uso resuelto sin clave.
    reg = c_contrato.registro(provider="p", model="m", tokens={"input": 1})
    t.verdadero("E-06 el contrato exige la clave",
                any("dedupKey" in e for e in c_contrato.validar_registro(reg)))


def test_e07_una_linea_por_bloque_no_duplica(t):
    """E-07 (B4-25) — la trampa real: 3 lineas, 2 mensajes, un total que no se dobla."""
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, repeticiones=2, con_estado_de_costo=False)
        crudo = 0
        with io.open(ruta, encoding="utf-8") as f:
            for linea in f:
                dato = json.loads(linea)
                crudo += (dato.get("message") or {}).get("usage", {}).get("output_tokens", 0)
        t.igual("E-07 la suma cruda dobla", 250, crudo)

        registros = c_cc.leer(ruta)
        t.igual("E-07 el adaptador da un registro por mensaje", 2, len(registros))
        eventos_ = c_contrato.a_eventos(registros, TAREA, "claude-code")
        resumen = c_agr.resumir(eventos_, task_id=TAREA)
        t.igual("E-07 el total es el deduplicado", 150, resumen["tokens"]["outputTokens"])
        t.igual("E-07 input", 12, resumen["tokens"]["inputTokens"])
        t.igual("E-07 cache read", 11000, resumen["tokens"]["cacheReadTokens"])

        # Con diez repeticiones de la misma linea, el total no se mueve.
        diez = _transcripcion(carpeta, repeticiones=10, con_estado_de_costo=False)
        muchos = c_agr.resumir(
            c_contrato.a_eventos(c_cc.leer(diez), TAREA, "claude-code"), task_id=TAREA)
        t.igual("E-07 diez repeticiones dan lo mismo", 150, muchos["tokens"]["outputTokens"])

        # Y el `cost-state` acumulado tampoco se suma dos veces: vale el ultimo.
        con_costo = _transcripcion(carpeta, repeticiones=2, con_estado_de_costo=True)
        registros = c_cc.leer(con_costo)
        agregados = [r for r in registros if r["kind"] == c_contrato.AGREGADO]
        montos = [r["reportedAmount"] for r in agregados if r["reportedAmount"] is not None]
        t.igual("E-07 vale el ultimo estado de costo", [3.25], montos)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e08_la_ventana_es_una_foto(t):
    """E-08 (B4-04) — contextTokens no se suma nunca."""
    eventos_ = [
        _ev(dedupKey="k-1", usage=_uso(contexto=10000, limite=200000),
            timestamp="2026-09-20T10:00:00"),
        _ev(dedupKey="k-2", usage=_uso(contexto=30000, limite=200000),
            timestamp="2026-09-20T10:01:00"),
        _ev(dedupKey="k-3", usage=_uso(contexto=45000, limite=200000),
            timestamp="2026-09-20T10:02:00"),
    ]
    resumen = c_agr.resumir(eventos_, task_id=TAREA)
    t.igual("E-08 vale la ultima foto", 45000, resumen["context"]["contextTokens"])
    t.igual("E-08 con su limite", 200000, resumen["context"]["contextLimit"])
    t.verdadero("E-08 no es la suma", resumen["context"]["contextTokens"] != 85000)
    t.verdadero("E-08 la ventana no esta entre los tokens facturables",
                "contextTokens" not in resumen["tokens"])
    for clase in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheCreationTokens"):
        t.verdadero("E-08 %s no se contamino con la ventana" % clase,
                    resumen["tokens"][clase] < 45000)

    sin_foto = c_agr.resumir([_ev(dedupKey="k-9", usage=_uso())], task_id=TAREA)
    t.igual("E-08 sin foto queda sin resolver", None, sin_foto["context"]["contextTokens"])


def test_e09_las_cuatro_clases_van_separadas(t):
    """E-09 (B4-05) — input, output, cache read y cache creation no se pisan."""
    eventos_ = [
        _ev(dedupKey="k-1", usage=_uso(entrada=1, salida=2, lectura=4, creacion=8)),
        _ev(dedupKey="k-2", usage=_uso(entrada=16, salida=32, lectura=64, creacion=128)),
    ]
    resumen = c_agr.resumir(eventos_, task_id=TAREA)
    esperado = {"inputTokens": 17, "outputTokens": 34,
                "cacheReadTokens": 68, "cacheCreationTokens": 136}
    t.igual("E-09 las cuatro sumas", esperado, resumen["tokens"])
    t.igual("E-09 son cuatro clases y no una", 4, len(resumen["tokens"]))
    t.igual("E-09 el modulo declara las cuatro", 4, len(c_eventos.CLASES_DE_TOKEN))
    # Potencias de dos: cualquier cruce entre clases daria un numero que no es el esperado.
    t.verdadero("E-09 ninguna clase es la suma de otras",
                resumen["tokens"]["inputTokens"] != resumen["tokens"]["outputTokens"])

    fila = resumen["byModel"][0]
    t.igual("E-09 tambien separadas por modelo", esperado, fila["tokens"])


def test_e10_un_uso_desconocido_no_es_cero(t):
    """E-10 (B4-06) — USAGE_UNRESOLVED, y se ve en el resumen."""
    uso = c_eventos.uso_sin_resolver("p-1", "m-1")
    t.igual("E-10 el estado", "USAGE_UNRESOLVED", uso["state"])
    for clase in c_eventos.CLASES_DE_TOKEN:
        t.igual("E-10 %s queda en None" % clase, None, uso[clase])
    t.igual("E-10 conserva el proveedor", "p-1", uso["provider"])

    # Un cero MEDIDO y un desconocido no se pueden confundir: es la diferencia entera.
    medido = _uso(entrada=0, salida=0, lectura=0, creacion=0)
    t.igual("E-10 un cero medido esta resuelto", "RESOLVED", medido["state"])
    t.verdadero("E-10 y no se confunde con lo desconocido", medido["state"] != uso["state"])
    for clase in c_eventos.CLASES_DE_TOKEN:
        t.verdadero("E-10 el cero medido es un numero, %s no" % clase,
                    medido[clase] == 0 and uso[clase] is None)

    resumen = c_agr.resumir([_ev(dedupKey="k-1", usage=uso)], task_id=TAREA)
    t.igual("E-10 no sumo nada", 0, resumen["tokens"]["outputTokens"])
    t.verdadero("E-10 y lo dice", "USAGE_UNRESOLVED" in resumen["unresolved"])

    reporte_ = c_reporte.generar(resumen)
    t.contiene("E-10 el reporte lo muestra", "USAGE_UNRESOLVED", reporte_)
    t.contiene("E-10 y explica que no es cero", "No es cero", reporte_)


# -- E-11 a E-15 — el motor de costos ------------------------------------------

def test_e11_costo_real_y_equivalente_son_dos(t):
    """E-11 (B4-07) — nunca los dos con un numero, y ninguno se copia del otro."""
    politica_api = dict(POLITICA, billingMode="API")
    por_api = c_costos.calcular(_uso(), politica_api, reportado=3.0, fuente="f", version="v")
    t.igual("E-11 con API la plata es real", 3.0, por_api["actual"])
    t.igual("E-11 y el equivalente queda vacio", None, por_api["apiEquivalentEstimated"])
    t.igual("E-11 el estado del real", "RESOLVED", por_api["actualState"])

    por_plan = c_costos.calcular(_uso(), POLITICA, reportado=3.0, fuente="f", version="v")
    t.igual("E-11 con plan el real queda vacio", None, por_plan["actual"])
    t.igual("E-11 y la plata va al equivalente", 3.0, por_plan["apiEquivalentEstimated"])

    for modo in c_costos.MODOS:
        politica = dict(POLITICA, billingMode=modo)
        costo = c_costos.calcular(_uso(), politica, reportado=7.0, fuente="f", version="v")
        llenos = [c for c in ("actual", "apiEquivalentEstimated") if costo[c] is not None]
        t.verdadero("E-11 en %s no hay dos montos llenos" % modo, len(llenos) <= 1)

    total = c_costos.sumar([por_api, por_plan])
    t.igual("E-11 el total real solo suma lo real", 3.0, total["actual"])
    t.igual("E-11 el total equivalente solo suma lo equivalente", 3.0,
            total["apiEquivalentEstimated"])


def test_e12_una_suscripcion_no_es_gasto(t):
    """E-12 (B4-08) — el equivalente de API no se presenta como plata gastada."""
    for modo in ("SUBSCRIPTION", "ENTERPRISE", "INTERNAL"):
        politica = dict(POLITICA, billingMode=modo)
        costo = c_costos.calcular(_uso(), politica, reportado=12.5, fuente="f", version="v")
        t.igual("E-12 %s: sin gasto real" % modo, None, costo["actual"])
        t.igual("E-12 %s: equivalente" % modo, 12.5, costo["apiEquivalentEstimated"])
        t.verdadero("E-12 %s: el real dice por que" % modo,
                    costo["actualState"] in ("FIXED_PLAN", "UNKNOWN"))

    resumen = c_agr.resumir(
        [_ev(dedupKey="k-1", usage=_uso(), cost=_costo(actual=None, equivalente=12.5))],
        task_id=TAREA)
    reporte_ = c_reporte.generar(resumen)
    t.contiene("E-12 el reporte separa los dos", "Equivalente de API estimado", reporte_)
    t.contiene("E-12 y avisa que no se gasto", "NO se gasto", reporte_)
    t.contiene("E-12 el costo real sale sin resolver", "| Costo real | sin resolver |", reporte_)

    estado = c_barra.de([_ev(dedupKey="k-1", sessionId="s-1", usage=_uso(),
                             cost=_costo(equivalente=12.5))], "s-1", POLITICA, TAREA)
    t.contiene("E-12 la barra marca el equivalente", "eq", c_barra.compacto(estado))


def test_e13_sin_tarifa_el_costo_no_se_resuelve(t):
    """E-13 (B4-09) — PRICING_UNAVAILABLE, y el harness no trae precios adentro."""
    politica = {"policyId": "p", "currency": "USD", "billingMode": "API"}
    costo = c_costos.calcular(_uso(), politica)
    t.igual("E-13 el estado", "PRICING_UNAVAILABLE", costo["state"])
    t.igual("E-13 sin plata real", None, costo["actual"])
    t.igual("E-13 sin equivalente", None, costo["apiEquivalentEstimated"])

    sin_politica = c_costos.calcular(_uso(), None)
    t.igual("E-13 sin politica tampoco", "PRICING_UNAVAILABLE", sin_politica["state"])

    # Una tabla que no cubre al modelo NO se aplica por parecido.
    tabla = [{"model": "otro-modelo", "source": "s", "versionOrDate": "v",
              "inputPerMillion": 1.0}]
    t.igual("E-13 una tarifa de otro modelo no se usa", "PRICING_UNAVAILABLE",
            c_costos.de_tabla(_uso(), tabla, "API", "USD")["state"])
    t.igual("E-13 no hay coincidencia parcial", None, c_costos.tarifa_para("m-10", tabla))

    # 🔴 El harness no envia tarifas. Se barre TODO lo que se instala, y por estructura, no
    # por una palabra: `{"input": 3.0}` es una tarifa igual y no dice `PerMillion`.
    claves = set(["rateTable"]) | set(c_costos.TARIFA_DE.values())
    t.igual("E-13 se buscan cinco claves de tarifa", 5, len(claves))
    archivos = _json_que_se_instalan()
    t.verdadero("E-13 hay json que barrer", len(archivos) >= 10)
    for archivo in archivos:
        with io.open(str(archivo), encoding="utf-8-sig") as f:
            try:
                documento = json.load(f)
            except ValueError:
                continue
        # El contrato del presupuesto NOMBRA las claves; lo que no puede traer es un valor.
        esperado = claves if archivo.name == "budget-policy.schema.json" else set()
        t.igual("E-13 %s no declara una tarifa" % archivo.name,
                sorted(esperado & _claves_json(documento, claves)),
                sorted(_claves_json(documento, claves)))

    # Y del lado del codigo: ningun contenedor publico del paquete guarda un numero. Una
    # tabla escrita a mano es necesariamente eso.
    import importlib
    modulos = {}
    for fuente in _fuentes_del_paquete():
        ruta = _relativo(fuente).replace(".py", "").replace("/", ".")
        if ruta.endswith("__init__"):
            ruta = ruta.rsplit(".", 1)[0] or "contabilidad"
        modulos["contabilidad." + ruta if ruta != "contabilidad" else ruta] = None
    for nombre in sorted(modulos):
        modulo = importlib.import_module(nombre)
        for atributo in sorted(a for a in dir(modulo) if not a.startswith("_")):
            valor = getattr(modulo, atributo)
            if not isinstance(valor, (dict, list, tuple, set)):
                continue
            t.verdadero("E-13 %s.%s no guarda un numero" % (nombre.split(".")[-1], atributo),
                        not _contenedor_con_numero(valor))

    # La premisa que hace valer lo de arriba: el barrido dispara con una tarifa de verdad.
    for tabla in ({"m-1": {"input": 3.0, "output": 15.0}},
                  [{"model": "m-1", "inputPerMillion": 3.0}],
                  ("m-1", 3.0), {"USD_POR_MILLON": 15}):
        t.verdadero("E-13 se detecta una tarifa en %s" % type(tabla).__name__,
                    _contenedor_con_numero(tabla))
    t.verdadero("E-13 y una tupla de strings no dispara",
                not _contenedor_con_numero(("PROVIDER_REPORTED", "RATE_TABLE")))
    t.igual("E-13 un json con rateTable se detecta", {"rateTable"},
            _claves_json({"config": {"rateTable": []}}, claves))
    t.igual("E-13 y uno con una tarifa suelta tambien", {"inputPerMillion"},
            _claves_json({"a": [{"inputPerMillion": 3.0}]}, claves))


def test_e14_todo_costo_conserva_los_siete_campos(t):
    """E-14 — sin uno de los siete no hay costo."""
    costo = c_costos.calcular(_uso(), dict(POLITICA, billingMode="API"),
                              reportado=1.0, fuente="transcripcion#L4", version="2026-09-20")
    t.igual("E-14 son siete", 7, len(c_costos.CAMPOS))
    t.verdadero("E-14 esta completo", c_costos.completo(costo))
    for campo in c_costos.CAMPOS:
        t.verdadero("E-14 lo trae: %s" % campo, costo.get(campo) not in (None, ""))
        mutilado = dict(costo)
        mutilado[campo] = None
        t.verdadero("E-14 sin %s no es un costo" % campo, not c_costos.completo(mutilado))

    t.verdadero("E-14 sin fuente no se calcula",
                c_costos.del_proveedor(1.0, "p", "m", "USD", "API", "", "v")["state"]
                == "PRICING_UNAVAILABLE")
    t.verdadero("E-14 sin version tampoco",
                c_costos.del_proveedor(1.0, "p", "m", "USD", "API", "f", "")["state"]
                == "PRICING_UNAVAILABLE")
    t.verdadero("E-14 sin moneda tampoco",
                c_costos.del_proveedor(1.0, "p", "m", "", "API", "f", "v")["state"]
                == "PRICING_UNAVAILABLE")
    t.igual("E-14 los metodos son dos", ("PROVIDER_REPORTED", "RATE_TABLE"), c_costos.METODOS)


def test_e15_lo_derivado_y_lo_reportado_se_guardan_los_dos(t):
    """E-15 — cuando difieren, el resumen guarda las dos y lo dice."""
    derivado = _ev(dedupKey="k-1", usage=_uso(entrada=10, salida=100, lectura=1000))
    reportado = _ev(tipo="SESSION_COMPLETED", dedupKey="agg|s-1",
                    usage=_uso(entrada=40, salida=900, lectura=90000),
                    metadata={"providerAggregate": True})
    resumen = c_agr.resumir([derivado, reportado], task_id=TAREA)

    t.igual("E-15 el total es lo derivado", 100, resumen["tokens"]["outputTokens"])
    conciliacion = resumen["reconciliation"]
    t.igual("E-15 el estado", "USAGE_RECONCILIATION_UNRESOLVED", conciliacion["state"])
    t.igual("E-15 guarda lo reportado", 900, conciliacion["providerReported"]["outputTokens"])
    t.igual("E-15 guarda lo derivado", 100, conciliacion["derived"]["outputTokens"])
    t.igual("E-15 y la diferencia", 800, conciliacion["differences"]["outputTokens"])
    t.verdadero("E-15 esta entre lo sin resolver",
                "USAGE_RECONCILIATION_UNRESOLVED" in resumen["unresolved"])
    t.verdadero("E-15 el agregado no se sumo al total",
                resumen["tokens"]["outputTokens"] != 1000)
    t.igual("E-15 se conto como agregado", 1, resumen["events"]["providerAggregates"])

    igual = c_agr.resumir(
        [derivado, _ev(tipo="SESSION_COMPLETED", dedupKey="agg|s-2",
                       usage=_uso(entrada=10, salida=100, lectura=1000),
                       metadata={"providerAggregate": True})], task_id=TAREA)
    t.igual("E-15 si coinciden, concilia", "RECONCILED", igual["reconciliation"]["state"])

    solo = c_agr.resumir([derivado], task_id=TAREA)
    t.igual("E-15 sin agregado no aplica", "NOT_APPLICABLE", solo["reconciliation"]["state"])


# -- E-16 y E-17 — el motor de tiempo ------------------------------------------

def test_e16_las_tres_clases_de_tiempo_van_separadas(t):
    """E-16 (B4-10) — pared, modelo y tool, y ninguna es la suma de las otras."""
    bloque = c_tiempo.medir(wall=60000, model=40000, tool=15000)
    t.igual("E-16 pared", 60000, bloque["wallMs"])
    t.igual("E-16 modelo", 40000, bloque["modelMs"])
    t.igual("E-16 tools", 15000, bloque["toolMs"])
    t.igual("E-16 resuelto", "RESOLVED", bloque["state"])

    total = c_tiempo.sumar([bloque, c_tiempo.medir(1000, 500, 200)])
    t.igual("E-16 pared sumada", 61000, total["wallMs"])
    t.igual("E-16 modelo sumado", 40500, total["modelMs"])
    t.igual("E-16 tools sumadas", 15200, total["toolMs"])
    t.verdadero("E-16 la pared no es modelo mas tools",
                total["wallMs"] != total["modelMs"] + total["toolMs"])
    t.igual("E-16 son tres clases", 3, len(c_tiempo.CLASES))

    resumen = c_agr.resumir([_ev(dedupKey="k-1", usage=_uso(), time=bloque)], task_id=TAREA)
    for clase in c_tiempo.CLASES:
        t.verdadero("E-16 %s llega al resumen" % clase, resumen["time"][clase] is not None)


def test_e17_la_pared_no_se_disfraza_de_modelo(t):
    """E-17 — sin evidencia de tiempo de modelo, queda TIME_ATTRIBUTION_UNRESOLVED."""
    solo_pared = c_tiempo.medir(wall=90000)
    t.igual("E-17 la pared esta", 90000, solo_pared["wallMs"])
    t.igual("E-17 el modelo no se rellena", None, solo_pared["modelMs"])
    t.igual("E-17 ni las tools", None, solo_pared["toolMs"])
    t.igual("E-17 el estado lo dice", "TIME_ATTRIBUTION_UNRESOLVED", solo_pared["state"])

    for valor in (1, 1000, 10 ** 9):
        t.igual("E-17 con pared %d el modelo sigue vacio" % valor, None,
                c_tiempo.medir(wall=valor)["modelMs"])

    total = c_tiempo.sumar([solo_pared, c_tiempo.medir(1000, 500, 200)])
    t.igual("E-17 el total avisa", "TIME_ATTRIBUTION_UNRESOLVED", total["state"])
    t.igual("E-17 y cuenta lo que falto", 1, total["modelMsMissing"])
    t.igual("E-17 el modelo suma solo lo que tenia", 500, total["modelMs"])

    resumen = c_agr.resumir([_ev(dedupKey="k-1", usage=_uso(), time=solo_pared)],
                            task_id=TAREA)
    t.verdadero("E-17 el resumen lo declara",
                "TIME_ATTRIBUTION_UNRESOLVED" in resumen["unresolved"])
    t.contiene("E-17 el reporte lo muestra", "sin resolver",
               c_reporte.generar(resumen))
    t.igual("E-17 sin milisegundos el texto no dice 0m", "sin resolver",
            c_tiempo.como_texto(None))


# -- E-18 a E-21 — la agregacion -----------------------------------------------

def test_e18_la_jerarquia_agrega(t):
    """E-18 — agente, unidad, sesion y modelo, cada uno con lo que tiene abajo."""
    eventos_ = [
        _ev(dedupKey="k-1", sessionId="s-1", workUnitId="u-1", agentId="dev-backend",
            usage=_uso(salida=100, modelo="m-a")),
        _ev(dedupKey="k-2", sessionId="s-1", workUnitId="u-1", agentId="dev-backend",
            usage=_uso(salida=200, modelo="m-a")),
        _ev(dedupKey="k-3", sessionId="s-2", workUnitId="u-2", agentId="dev-frontend",
            usage=_uso(salida=400, modelo="m-b")),
    ]
    resumen = c_agr.resumir(eventos_, task_id=TAREA)
    t.igual("E-18 dos agentes", 2, len(resumen["byAgent"]))
    t.igual("E-18 dos unidades", 2, len(resumen["byWorkUnit"]))
    t.igual("E-18 dos sesiones", 2, len(resumen["bySession"]))
    t.igual("E-18 dos modelos", 2, len(resumen["byModel"]))

    por_agente = dict((f["id"], f["tokens"]["outputTokens"]) for f in resumen["byAgent"])
    t.igual("E-18 backend suma sus dos", 300, por_agente["dev-backend"])
    t.igual("E-18 frontend la suya", 400, por_agente["dev-frontend"])
    por_unidad = dict((f["id"], f["tokens"]["outputTokens"]) for f in resumen["byWorkUnit"])
    t.igual("E-18 u-1", 300, por_unidad["u-1"])
    t.igual("E-18 u-2", 400, por_unidad["u-2"])
    t.igual("E-18 el total es la suma", 700, resumen["tokens"]["outputTokens"])
    t.igual("E-18 las filas salen ordenadas", ["dev-backend", "dev-frontend"],
            [f["id"] for f in resumen["byAgent"]])
    t.igual("E-18 el evento se cuenta en su fila", 2, resumen["byAgent"][0]["events"])


def test_e19_el_total_cierra(t):
    """E-19 (B4-13) — filas mas lo no atribuido es igual al total, en las tres dimensiones."""
    eventos_ = [
        _ev(dedupKey="k-1", sessionId="s-1", workUnitId="u-1", agentId="dev-backend",
            usage=_uso(salida=100)),
        _ev(dedupKey="k-2", sessionId="s-1", usage=_uso(salida=200)),
        _ev(dedupKey="k-3", usage=_uso(salida=400)),
    ]
    resumen = c_agr.resumir(eventos_, task_id=TAREA)
    t.igual("E-19 el total", 700, resumen["tokens"]["outputTokens"])
    for campo, fila in (("workUnitId", "byWorkUnit"), ("agentId", "byAgent"),
                        ("sessionId", "bySession")):
        t.verdadero("E-19 cierra por %s" % campo, c_agr.cierra(resumen, campo, fila))
    t.igual("E-19 sin unidad quedaron 600", 600,
            resumen["unattributed"]["workUnitId"]["tokens"]["outputTokens"])
    t.igual("E-19 sin sesion quedaron 400", 400,
            resumen["unattributed"]["sessionId"]["tokens"]["outputTokens"])
    t.igual("E-19 dos eventos sin unidad", 2, resumen["unattributed"]["workUnitId"]["events"])

    # Deduplicado: el repetido no rompe la invariante ni infla el total.
    con_repetido = c_agr.resumir(eventos_ + [dict(eventos_[0], eventId="ev_otro")],
                                 task_id=TAREA)
    t.igual("E-19 el repetido no suma", 700, con_repetido["tokens"]["outputTokens"])
    t.verdadero("E-19 y sigue cerrando", c_agr.cierra(con_repetido))


def test_e20_lo_no_atribuido_no_se_reparte(t):
    """E-20 (B4-14) — WORKUNIT_ATTRIBUTION_UNRESOLVED, y las filas conocidas no crecen."""
    conocido = _ev(dedupKey="k-1", workUnitId="u-1", usage=_uso(salida=100))
    huerfano = _ev(dedupKey="k-2", usage=_uso(salida=900))

    solo = c_agr.resumir([conocido], task_id=TAREA)
    con_huerfano = c_agr.resumir([conocido, huerfano], task_id=TAREA)

    t.igual("E-20 la fila conocida no se movio",
            solo["byWorkUnit"][0]["tokens"]["outputTokens"],
            con_huerfano["byWorkUnit"][0]["tokens"]["outputTokens"])
    t.igual("E-20 sigue habiendo una sola fila", 1, len(con_huerfano["byWorkUnit"]))
    t.igual("E-20 pero el total crecio", 1000, con_huerfano["tokens"]["outputTokens"])
    t.igual("E-20 lo huerfano se ve aparte", 900,
            con_huerfano["unattributed"]["workUnitId"]["tokens"]["outputTokens"])
    t.verdadero("E-20 y se declara",
                "WORKUNIT_ATTRIBUTION_UNRESOLVED" in con_huerfano["unresolved"])
    t.verdadero("E-20 tambien sin sesion",
                "SESSION_ATTRIBUTION_UNRESOLVED" in con_huerfano["unresolved"])
    t.verdadero("E-20 tambien sin agente",
                "AGENT_ATTRIBUTION_UNRESOLVED" in con_huerfano["unresolved"])
    t.contiene("E-20 el reporte lo dice", "no se reparte", c_reporte.generar(con_huerfano))
    t.verdadero("E-20 y cierra igual", c_agr.cierra(con_huerfano))


def test_e21_el_mismo_libro_da_el_mismo_resumen(t):
    """E-21 (B4-27) — byte a byte, dos veces."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        agentes = ("dev-backend", "dev-frontend", "dev-security", "dev-devops")
        for i in range(8):
            c_libro.agregar(ruta, _ev(
                dedupKey="k-%d" % i, sessionId="s-%d" % (i % 3), workUnitId="u-%d" % (i % 4),
                agentId=agentes[i % 4], usage=_uso(salida=100 * i, modelo="m-%d" % (i % 3)),
                time=c_tiempo.medir(1000 + i, 500 + i, 200 + i), cost=_costo()))
        # 🔴 Y eventos que dejan varios estados SIN RESOLVER. Con la lista vacia el orden no
        # puede variar, y el test de determinismo no probaba nada: es lo que dejaba pasar un
        # `list(abiertos)` en vez de `sorted`.
        c_libro.agregar(ruta, _ev(dedupKey="k-sin-uso",
                                  usage=c_eventos.uso_sin_resolver("p-1", "m-0")))
        c_libro.agregar(ruta, _ev(dedupKey="k-sin-tiempo", usage=_uso(),
                                  time=c_tiempo.medir(wall=9000)))
        c_libro.agregar(ruta, _ev(dedupKey="k-sin-unidad", usage=_uso(salida=7)))
        libro_leido = c_libro.leer(ruta)
        t.verdadero("E-21 hay varios estados sin resolver, o el orden no puede variar",
                    len(c_agr.resumir(libro_leido, task_id=TAREA)["unresolved"]) >= 4)
        t.verdadero("E-21 hay filas suficientes para que el orden importe",
                    len(c_agr.resumir(libro_leido, task_id=TAREA)["byAgent"]) >= 4)

        # 🔴 En PROCESOS DISTINTOS, y con el hash sembrado al azar. Dos llamadas adentro del
        # mismo proceso no prueban determinismo: un set iterado sin ordenar da el mismo orden
        # las dos veces. Con `return list(abiertos)` en vez de `sorted`, la comparacion
        # adentro de un proceso pasaba en verde y el summary.json cambiaba entre corridas.
        driver = os.path.join(carpeta, "resumir.py")
        with io.open(driver, "w", encoding="utf-8", newline="\n") as f:
            f.write("import io, json, sys\n"
                    "sys.path.insert(0, %r)\n" % str(BIN) +
                    "from contabilidad import agregacion, libro\n"
                    "l = libro.leer(%r)\n" % ruta +
                    "sys.stdout.write(json.dumps(agregacion.resumir(l, task_id=%r),\n"
                    % TAREA +
                    "                            ensure_ascii=False, sort_keys=True))\n")
        corridas = []
        for semilla in ("0", "random", "12345"):
            entorno = dict(os.environ, PYTHONHASHSEED=semilla)
            proceso = subprocess.run([sys.executable, driver], capture_output=True,
                                     text=True, env=entorno, cwd=carpeta)
            t.igual("E-21 la corrida con semilla %s sale bien" % semilla, 0, proceso.returncode)
            corridas.append(proceso.stdout)
        t.igual("E-21 tres procesos, tres semillas, el mismo texto", 1, len(set(corridas)))
        t.verdadero("E-21 y el texto no es vacio", len(corridas[0]) > 500)

        primero = json.dumps(c_agr.resumir(libro_leido, task_id=TAREA), sort_keys=True)
        segundo = json.dumps(c_agr.resumir(libro_leido, task_id=TAREA), sort_keys=True)
        t.igual("E-21 dos corridas, el mismo texto", primero, segundo)

        destino = c_libro.ruta_de(carpeta, TAREA, c_libro.RESUMEN)
        c_agr.escribir(c_agr.resumir(libro_leido, task_id=TAREA), destino)
        with io.open(destino, "rb") as f:
            bytes_uno = f.read()
        c_agr.escribir(c_agr.resumir(c_libro.leer(ruta), task_id=TAREA), destino)
        with io.open(destino, "rb") as f:
            bytes_dos = f.read()
        t.igual("E-21 el archivo sale igual", bytes_uno, bytes_dos)

        # Y el orden de lectura no lo cambia: las filas se ordenan, no se acumulan sueltas.
        revertido = c_agr.resumir(list(reversed(libro_leido)), task_id=TAREA)
        for tabla in ("byAgent", "byWorkUnit", "bySession", "byModel"):
            t.igual("E-21 %s no depende del orden" % tabla,
                    json.loads(primero)[tabla], revertido[tabla])
            t.igual("E-21 %s sale ordenado" % tabla,
                    sorted(f["id"] for f in revertido[tabla]),
                    [f["id"] for f in revertido[tabla]])
        t.igual("E-21 y los totales tampoco", json.loads(primero)["tokens"],
                revertido["tokens"])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- E-22 a E-26 — el presupuesto ----------------------------------------------

def test_e22_sin_politica_no_hay_limite(t):
    """E-22 (B4-28) — BUDGET_UNDEFINED, y no se inventa un numero."""
    for politica in (None, {}, {"policyId": "p", "currency": "USD"},
                     {"policyId": "p", "currency": "USD", "task": {}},
                     {"policyId": "p", "currency": "USD",
                      "task": {"softLimit": None, "hardLimit": None}}):
        decision = c_pres.evaluar(100.0, 50.0, politica)
        t.igual("E-22 sin limites es BUDGET_UNDEFINED", "BUDGET_UNDEFINED", decision["status"])
        t.igual("E-22 y no inventa un blando", None, decision["softLimit"])
        t.igual("E-22 ni un duro", None, decision["hardLimit"])
        t.contiene("E-22 lo explica", "No se inventa un limite", decision["reason"])

    t.verdadero("E-22 declarada es falsa sin limites", not c_pres.declarada(None))
    t.verdadero("E-22 y verdadera con uno", c_pres.declarada(POLITICA))

    carpeta = _tmp()
    try:
        t.igual("E-22 sin archivo no hay politica", None,
                c_pres.cargar(os.path.join(carpeta, "no-esta.json")))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)

    sin_costo = c_pres.evaluar(None, 1.0, POLITICA)
    t.igual("E-22 sin plata comparable", "COST_UNRESOLVED", sin_costo["status"])


def test_e23_el_limite_blando_avisa(t):
    """E-23 (B4-15) — BUDGET_WARNING, y no bloquea nada."""
    decision = c_pres.evaluar(4.0, 2.0, POLITICA)
    t.igual("E-23 el estado", "BUDGET_WARNING", decision["status"])
    t.igual("E-23 el proyectado", 6.0, decision["projectedAmount"])
    t.igual("E-23 el blando", 5.0, decision["softLimit"])
    t.contiene("E-23 dice que no bloquea", "no bloquea", decision["reason"])

    debajo = c_pres.evaluar(1.0, 1.0, POLITICA)
    t.igual("E-23 debajo queda dentro", "WITHIN_BUDGET", debajo["status"])
    t.igual("E-23 justo en el blando queda dentro", "WITHIN_BUDGET",
            c_pres.evaluar(5.0, 0.0, POLITICA)["status"])
    t.igual("E-23 un centavo arriba avisa", "BUDGET_WARNING",
            c_pres.evaluar(5.0, 0.01, POLITICA)["status"])
    t.contiene("E-23 el texto sale en espanol", "Evidencia de presupuesto",
               c_pres.texto_de_decision(decision))


def test_e24_el_limite_duro_y_el_proyectado(t):
    """E-24 (B4-16) — HUMAN_APPROVAL_REQUIRED si la politica lo pide; EXCEEDED si ya paso."""
    pide = c_pres.evaluar(15.0, 10.0, POLITICA)
    t.igual("E-24 el proyectado que pasa pide gente", "HUMAN_APPROVAL_REQUIRED",
            pide["status"])
    t.igual("E-24 con su proyectado", 25.0, pide["projectedAmount"])

    sin_pedir = dict(POLITICA, premiumModel={"requiresHumanApproval": False,
                                             "projectedOverrunRequiresApproval": False})
    t.igual("E-24 sin pedirlo, excede", "BUDGET_EXCEEDED",
            c_pres.evaluar(15.0, 10.0, sin_pedir)["status"])

    ya_paso = c_pres.evaluar(25.0, 1.0, POLITICA)
    t.igual("E-24 lo ya gastado no se aprueba", "BUDGET_EXCEEDED", ya_paso["status"])
    t.contiene("E-24 y lo explica", "no se puede aprobar", ya_paso["reason"])

    t.igual("E-24 premium pide gente", "HUMAN_APPROVAL_REQUIRED",
            c_pres.evaluar(1.0, 1.0, POLITICA, premium=True)["status"])
    t.igual("E-24 sin premium no", "WITHIN_BUDGET",
            c_pres.evaluar(1.0, 1.0, POLITICA, premium=False)["status"])
    t.igual("E-24 son seis estados", 6, len(c_pres.ESTADOS))


def test_e25_el_bloque_4_no_aprueba(t):
    """E-25 (B4-17) — la compuerta del Bloque 3 sigue intacta y sin saber que existe esto."""
    publicos = [n for n in dir(c_pres) if not n.startswith("_")]
    for verbo in ("aprobar", "approve", "autorizar", "authorize", "permitir", "allow",
                  "habilitar"):
        t.verdadero("E-25 no existe `%s`" % verbo,
                    not any(verbo in n.lower() for n in publicos))
    for estado in c_pres.ESTADOS:
        t.verdadero("E-25 `%s` no es una aprobacion" % estado,
                    "APPROVED" not in estado and "ALLOWED" not in estado)

    politica_del_bloque_3 = orq_consumo.politica({})
    aprobada, solicitud, _ = orq_consumo.decidir(
        {"id": "u-1", "assignedAgent": "dev-security"}, "premium", "toca seguridad",
        politica_del_bloque_3)
    t.verdadero("E-25 premium sigue sin aprobarse solo", not aprobada)
    t.verdadero("E-25 y arma la solicitud", solicitud is not None)
    t.igual("E-25 que queda pendiente", "PENDING", solicitud["status"])

    dentro = c_pres.evaluar(0.0, 0.1, POLITICA)
    t.igual("E-25 aun con presupuesto de sobra", "WITHIN_BUDGET", dentro["status"])
    otra_vez, _, _ = orq_consumo.decidir(
        {"id": "u-1", "assignedAgent": "dev-security"}, "premium", dentro["status"],
        politica_del_bloque_3)
    t.verdadero("E-25 la compuerta no se movio", not otra_vez)

    # Y los dos bloques no se conocen: ni un import cruzado.
    for fuente in _fuentes_del_paquete():
        texto = fuente.read_text(encoding="utf-8")
        t.verdadero("E-25 %s no importa orquestacion" % fuente.name,
                    "import orquestacion" not in texto
                    and "from orquestacion" not in texto)
    for fuente in sorted((BIN / "orquestacion").glob("*.py")):
        texto = fuente.read_text(encoding="utf-8")
        t.verdadero("E-25 %s no importa contabilidad" % fuente.name,
                    "import contabilidad" not in texto
                    and "from contabilidad" not in texto)


def test_e26_la_decision_queda_en_el_libro(t):
    """E-26 — BUDGET_DECISION_RECORDED, con su estado y su motivo."""
    decision = c_pres.evaluar(15.0, 10.0, POLITICA)
    evento = _ev(tipo="BUDGET_DECISION_RECORDED", workUnitId="u-1", dedupKey="dec-1",
                 metadata={"status": decision["status"], "reason": decision["reason"]})
    escalamiento = _ev(tipo="MODEL_ESCALATION_REQUESTED", workUnitId="u-1",
                       agentId="dev-security", dedupKey="esc-1",
                       metadata={"tier": "premium", "reason": "toca seguridad"})

    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        c_libro.agregar_varios(ruta, [evento, escalamiento])
        resumen = c_agr.resumir(c_libro.leer(ruta), task_id=TAREA, presupuesto=decision)
        t.igual("E-26 hay una decision", 1, len(resumen["budgetEvents"]))
        t.igual("E-26 con su estado", "HUMAN_APPROVAL_REQUIRED",
                resumen["budgetEvents"][0]["status"])
        t.igual("E-26 y su unidad", "u-1", resumen["budgetEvents"][0]["workUnitId"])
        t.igual("E-26 hay un escalamiento", 1, len(resumen["premiumEscalations"]))
        t.igual("E-26 con su tier", "premium", resumen["premiumEscalations"][0]["tier"])

        texto = c_reporte.generar(resumen)
        t.contiene("E-26 el reporte tiene la seccion", "## Escalamientos caros", texto)
        t.contiene("E-26 y muestra el estado", "HUMAN_APPROVAL_REQUIRED", texto)
        t.contiene("E-26 y el presupuesto", "## Presupuesto", texto)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- E-27 a E-31 — el reporte y la barra ---------------------------------------

def test_e27_el_reporte_sale_del_resumen(t):
    """E-27 (B4-20) — los numeros del Markdown son los del summary.json."""
    eventos_ = [
        _ev(dedupKey="k-1", sessionId="s-1", workUnitId="u-1", agentId="dev-backend",
            usage=_uso(entrada=123, salida=4567, lectura=89012, creacion=345),
            time=c_tiempo.medir(60000, 40000, 15000), cost=_costo(equivalente=2.75)),
    ]
    resumen = c_agr.resumir(eventos_, task_id=TAREA)
    texto = c_reporte.generar(resumen)

    t.contiene("E-27 la tarea", TAREA, texto)
    t.contiene("E-27 el input", "123", texto)
    t.contiene("E-27 el output", "4.567", texto)
    t.contiene("E-27 el cache read", "89.012", texto)
    t.contiene("E-27 el cache creation", "345", texto)
    t.contiene("E-27 el equivalente", "2.7500", texto)
    t.contiene("E-27 el agente", "dev-backend", texto)
    t.contiene("E-27 la unidad", "u-1", texto)
    t.contiene("E-27 la sesion", "s-1", texto)
    t.contiene("E-27 el tiempo de modelo", "40s", texto)
    for seccion in ("## Resumen administrativo", "## Por agente", "## Por unidad de trabajo",
                    "## Por sesion", "## Por modelo", "## Presupuesto",
                    "## Sin atribuir", "## Conciliacion con el proveedor",
                    "## Contabilidad sin resolver", "## Trazabilidad"):
        t.contiene("E-27 esta %s" % seccion, seccion, texto)
    t.contiene("E-27 dice que no es la fuente", "no la fuente contable", texto)


def test_e28_el_markdown_nunca_es_la_fuente(t):
    """E-28 (B4-21) — se corrompe el reporte y el resumen no cambia."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        c_libro.agregar(ruta, _ev(dedupKey="k-1", usage=_uso(salida=777)))
        libro_leido = c_libro.leer(ruta)
        antes = c_agr.resumir(libro_leido, task_id=TAREA)

        destino = c_reporte.escribir(antes, c_libro.ruta_de(carpeta, TAREA, c_libro.REPORTE))
        t.verdadero("E-28 el reporte se escribio", os.path.isfile(destino))

        with io.open(destino, "w", encoding="utf-8") as f:
            f.write("# Mentira\n\n| Tokens de output | 999999999 |\n")
        despues = c_agr.resumir(c_libro.leer(ruta), task_id=TAREA)
        t.igual("E-28 el resumen no se movio", antes["tokens"], despues["tokens"])
        t.igual("E-28 sigue siendo 777", 777, despues["tokens"]["outputTokens"])

        os.remove(destino)
        sin_reporte = c_agr.resumir(c_libro.leer(ruta), task_id=TAREA)
        t.igual("E-28 sin el .md el resumen sale igual", antes["tokens"],
                sin_reporte["tokens"])
        t.contiene("E-28 y se regenera igual", "777", c_reporte.generar(sin_reporte))

        # 🔴 La mitad de arriba no discrimina sola —`resumir` recibe eventos, no una ruta—,
        # asi que la afirmacion se sostiene con un invariante sobre el paquete: CADA lectura
        # del paquete esta clavada, con su modulo y su funcion. Agregar un lector en
        # cualquier lado rompe esto, que es exactamente lo que no pasaba antes.
        lecturas = sorted((m, f) for m, f, modo in _aperturas() if str(modo).startswith("r"))
        escrituras = sorted((m, f, modo) for m, f, modo in _aperturas()
                            if not str(modo).startswith("r"))
        t.igual("E-28 las lecturas del paquete son estas y ninguna mas", [
            ("adaptadores/claude_code.py", "_lineas"),
            ("eventos.py", "cargar_schema"),
            ("libro.py", "leer"),
            ("presupuesto.py", "cargar"),
            ("presupuesto.py", "cargar_schema"),
        ], lecturas)
        t.igual("E-28 y las escrituras", [
            ("agregacion.py", "escribir", "w"),
            ("libro.py", "agregar", "a"),
            ("reporte.py", "escribir", "w"),
        ], escrituras)
        for modulo in ("reporte.py", "barra.py", "agregacion.py", "costos.py", "tiempo.py"):
            t.verdadero("E-28 %s no lee ningun archivo" % modulo,
                        modulo not in [m for m, _ in lecturas])
        t.igual("E-28 el libro solo lee su jsonl", "ledger.jsonl", c_libro.LIBRO)
        t.verdadero("E-28 lo unico que se lee son json y jsonl",
                    all(f in ("leer", "cargar", "cargar_schema", "_lineas")
                        for _, f in lecturas))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e29_la_barra_es_de_la_sesion_activa(t):
    """E-29 (B4-11) — cambiar de sesion cambia los numeros."""
    eventos_ = [
        _ev(dedupKey="k-1", sessionId="s-1", usage=_uso(salida=100, contexto=1000,
                                                        limite=10000, modelo="m-a")),
        _ev(dedupKey="k-2", sessionId="s-2", usage=_uso(salida=900, contexto=9000,
                                                        limite=10000, modelo="m-b")),
    ]
    t.igual("E-29 hay dos sesiones", ("s-1", "s-2"), c_barra.sesiones(eventos_))

    uno = c_barra.de(eventos_, "s-1", POLITICA, TAREA)
    dos = c_barra.de(eventos_, "s-2", POLITICA, TAREA)
    t.igual("E-29 la primera", 100, uno["tokens"]["outputTokens"])
    t.igual("E-29 la segunda", 900, dos["tokens"]["outputTokens"])
    t.igual("E-29 su modelo", "m-a", uno["model"])
    t.igual("E-29 el otro", "m-b", dos["model"])
    t.igual("E-29 su ventana", 1000, uno["context"]["tokens"])
    t.igual("E-29 la otra", 9000, dos["context"]["tokens"])
    t.igual("E-29 el nivel de contexto de la primera", "NORMAL", uno["context"]["level"])
    t.igual("E-29 y el de la segunda", "ERROR", dos["context"]["level"])
    t.contiene("E-29 la linea nombra el modelo", "m-b", c_barra.compacto(dos))
    t.verdadero("E-29 y no el de la otra sesion", "m-a" not in c_barra.compacto(dos))


def test_e30_cambiar_de_sesion_no_borra_nada(t):
    """E-30 (B4-12) — el libro es uno solo y la sesion anterior se vuelve a pedir igual."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        c_libro.agregar(ruta, _ev(dedupKey="k-1", sessionId="s-1",
                                  usage=_uso(salida=100, contexto=1000, limite=10000)))
        primera = c_barra.de(c_libro.leer(ruta), "s-1", POLITICA, TAREA)

        c_libro.agregar(ruta, _ev(dedupKey="k-2", sessionId="s-2",
                                  usage=_uso(salida=900, contexto=9000, limite=10000)))
        libro_leido = c_libro.leer(ruta)
        t.igual("E-30 el libro tiene las dos", 2, len(libro_leido))

        de_nuevo = c_barra.de(libro_leido, "s-1", POLITICA, TAREA)
        t.igual("E-30 la sesion vieja da lo mismo", primera["tokens"], de_nuevo["tokens"])
        t.igual("E-30 con su ventana", 1000, de_nuevo["context"]["tokens"])
        t.igual("E-30 y sus eventos siguen", 1, len(c_barra.de_sesion(libro_leido, "s-1")))

        total = c_agr.resumir(libro_leido, task_id=TAREA)
        t.igual("E-30 el total de la tarea las suma", 1000, total["tokens"]["outputTokens"])
        t.igual("E-30 y las dos tienen fila", 2, len(total["bySession"]))

        vacia = c_barra.de(libro_leido, "s-99", POLITICA, TAREA)
        t.igual("E-30 una sesion que no existe no inventa", 0,
                vacia["tokens"]["outputTokens"])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e31_contexto_y_presupuesto_son_dos_cosas(t):
    """E-31 — separados, y con los umbrales en configuracion."""
    eventos_ = [_ev(dedupKey="k-1", sessionId="s-1",
                    usage=_uso(salida=100, contexto=9500, limite=10000),
                    cost=_costo(equivalente=1.0))]
    estado = c_barra.de(eventos_, "s-1", POLITICA, TAREA)
    t.verdadero("E-31 son dos bloques", "context" in estado and "budget" in estado)
    t.igual("E-31 la ventana casi llena", "ERROR", estado["context"]["level"])
    t.igual("E-31 y el presupuesto tranquilo", "NORMAL", estado["budget"]["level"])
    t.verdadero("E-31 una cosa no implica la otra",
                estado["context"]["level"] != estado["budget"]["level"])

    linea = c_barra.compacto(estado)
    t.contiene("E-31 la linea muestra contexto", "Ctx", linea)
    t.contiene("E-31 y presupuesto", "Budget", linea)
    t.contiene("E-31 y no suelta el estado", "ERROR", linea)
    t.contiene("E-31 tampoco cuando no entra", "ERROR", c_barra.compacto(estado, ancho=10))

    # Los umbrales salen de la politica: sin ellos, el nivel no se inventa.
    sin_umbrales = dict(POLITICA)
    sin_umbrales.pop("statusBar")
    apagada = c_barra.de(eventos_, "s-1", sin_umbrales, TAREA)
    t.igual("E-31 sin umbrales el contexto no se pinta", "UNRESOLVED",
            apagada["context"]["level"])
    t.igual("E-31 ni el presupuesto", "UNRESOLVED", apagada["budget"]["level"])
    t.igual("E-31 pero el numero sigue", 9500, apagada["context"]["tokens"])
    for fraccion in (0.0, 0.5, 0.99, 1.5):
        t.igual("E-31 con %s y sin umbrales sigue sin resolver" % fraccion, "UNRESOLVED",
                c_pres.nivel(fraccion, {}))
    t.igual("E-31 con umbrales declarados si", "WARNING",
            c_pres.nivel(0.6, {"warningAt": 0.5, "errorAt": 0.9}))
    t.igual("E-31 son cuatro niveles", 4, len(c_pres.NIVELES))


# -- E-32 a E-34 — los adaptadores ---------------------------------------------

# 🔴 `.claude` es el directorio del harness en un proyecto instalado, no una referencia a un
# proveedor. Es la unica excepcion del barrido, y se saca del texto ANTES de buscar para que
# el barrido siga siendo un invariante y no una lista de perdones que crece.
#
# 🔴 Y se saca como SEGMENTO DE RUTA cerrado: `.claude` vale como excepcion solo si lo que
# sigue es una barra, una comilla, un espacio o el final. Dos versiones anteriores de esta
# linea dejaron pasar fugas reales que la propia excepcion tapaba:
#
#     .claude_code   la primera version lo perdonaba (excluia cualquier `.claude`)
#     .claude-code   la segunda tambien (excluia solo [A-Za-z0-9_] despues)
#     .claude.code   idem
#
# Las tres se detectan ahora, y estan clavadas abajo con una asercion en verde.
DIRECTORIO_DEL_HARNESS = re.compile(r"\.claude(?=[/\\'\"\s,)\]}]|$)")

# Proveedores que el registro no declara hoy. Estan acá para que agregar una rama por uno de
# ellos al nucleo tampoco pase, aunque nadie haya escrito su adaptador. Tambien las familias
# de modelo: `if model.startswith("opus")` en el nucleo es la misma fuga con otro nombre.
#
# 📌 `llama` NO esta en la lista, y es la unica ausencia deliberada: en castellano es un
# verbo que el nucleo usa —"quien llama", "sin llamador"— y ponerlo convertiria el barrido en
# uno que falla sin motivo, que es el barrido que alguien apaga.
OTROS_PROVEEDORES = ("anthropic", "openai", "gpt", "gemini", "bedrock", "vertex",
                     "mistral", "cohere", "ollama", "copilot", "deepseek", "grok",
                     "azure", "qwen", "groq", "sonnet", "opus", "haiku")


def _archivos_del_nucleo():
    """Todo `.py` del paquete MENOS el registro y los adaptadores que el registro declara.

    La lista de exentos sale del registro, no de una tupla escrita a mano: un `nucleo_extra.py`
    nuevo entra al barrido solo, y un adaptador nuevo sale solo. La version anterior tenia once
    nombres fijos, y un modulo nuevo con `if adapter == "claude-code"` adentro pasaba en verde.
    """
    exentos = set()
    for modulo in c_reg.ADAPTADORES.values():
        exentos.add(Path(modulo.__file__).resolve())
    exentos.add((PAQUETE / "adaptadores" / "registro.py").resolve())
    return [f for f in _fuentes_del_paquete() if f.resolve() not in exentos], exentos


def _proveedores_en(texto):
    # camelCase se parte antes de bajar a minusculas: `claudeAdapter` no esconde a nadie
    # atras de una mayuscula, y separar ahi no crea falsos positivos en castellano.
    texto = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", texto)
    limpio = DIRECTORIO_DEL_HARNESS.sub("<dir-del-harness>", texto).lower()
    nombres = set(n.lower() for n in c_reg.PROVEEDORES) | set(OTROS_PROVEEDORES)
    # Los compuestos se buscan enteros y por sus partes largas: `claude-code` no se esconde
    # escribiendo `claude_code`. Las partes de cuatro letras o menos quedan afuera porque no
    # identifican a nadie — `code` esta adentro de `encode` y de `VS Code`, y un barrido que
    # salta con eso se apaga la primera vez que alguien lo ve fallar sin motivo.
    partes = set()
    for nombre in nombres:
        partes.add(nombre)
        for pedazo in nombre.replace("_", "-").split("-"):
            if len(pedazo) > 4:
                partes.add(pedazo)
    # Con bordes: `opus` no matchea adentro de una palabra, y `anthropic` si adentro de
    # `ANTHROPIC_CONTEXT`, porque el guion bajo no es letra ni digito.
    return sorted(p for p in partes
                  if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(p), limpio))


def test_e32_el_nucleo_no_nombra_ningun_proveedor(t):
    """E-32 (B4-23) — invariante sobre el paquete, no una lista de ramas prohibidas."""
    t.verdadero("E-32 el registro declara proveedores", len(c_reg.PROVEEDORES) >= 2)

    nucleo, exentos = _archivos_del_nucleo()
    t.igual("E-32 el barrido cubre el paquete menos los adaptadores",
            len(_fuentes_del_paquete()) - len(exentos), len(nucleo))
    t.igual("E-32 los exentos son el registro y los adaptadores declarados",
            len(c_reg.ADAPTADORES) + 1, len(exentos))
    t.verdadero("E-32 y son once o mas archivos de nucleo", len(nucleo) >= 11)
    for archivo in nucleo:
        encontrados = _proveedores_en(archivo.read_text(encoding="utf-8"))
        t.igual("E-32 %s no nombra a nadie" % _relativo(archivo), [], encontrados)

    # La otra mitad: el barrido tiene que encontrar una fuga de verdad. Las formas son
    # crudas a proposito — ninguna se escribio para que el patron la agarre.
    fugas = (
        'if provider == "claude-code":',
        "if evento['source']['adapter'] == 'codex':",
        "# para Claude Code esto viene en message.usage",
        "ANTHROPIC_CONTEXT = 200000",
        "elif proveedor in (OPENAI, GEMINI):",
        "def _es_codex(evento):",
        "PRECIOS = {'gpt-5': 1.0}",
        "from .adaptadores.claude_code import NOMBRE",
        "usar_bedrock = False",
        "# el copilot de github no reporta tokens",
        'if modelo.startswith("opus"): return 1',
        "PROVEEDOR_DEEPSEEK = 3",
        "ruta = os.path.join('.claude-code', 'sesiones')",
        'MODULO = ".claude.code"',
        "from .claude_code import NOMBRE",
        "url = 'https://azure.example/api'",
    )
    for fuga in fugas:
        t.verdadero("E-32 se detecta: %s" % fuga[:38], bool(_proveedores_en(fuga)))

    # Y la premisa que hace valer la mitad de arriba: el texto real, con una fuga metida,
    # deja de estar limpio.
    base = (PAQUETE / "costos.py").read_text(encoding="utf-8")
    t.igual("E-32 la premisa: el archivo esta limpio", [], _proveedores_en(base))
    t.verdadero("E-32 y con una fuga adentro deja de estarlo",
                bool(_proveedores_en(base + "\nif provider == 'claude-code': pass\n")))
    # El directorio del harness no es una fuga, y sacarlo no apaga el barrido.
    t.igual("E-32 `.claude` no cuenta", [], _proveedores_en('BASE = (".claude", "runtime")'))
    t.igual("E-32 ni con una barra atras", [],
            _proveedores_en('ruta = ".claude/runtime/accounting"'))
    t.verdadero("E-32 pero `claude` suelto si",
                bool(_proveedores_en('adaptador = "claude"')))
    # Las tres formas que dos versiones de la excepcion dejaron pasar, clavadas en verde.
    for forma in (".claude_code", ".claude-code", ".claude.code"):
        t.verdadero("E-32 la excepcion no tapa `%s`" % forma,
                    bool(_proveedores_en("import %s" % forma)))
    t.verdadero("E-32 ni un identificador",
                bool(_proveedores_en("self.claudeAdapter = None")))
    # Y `llama`, que quedo deliberadamente afuera, no rompe el castellano del nucleo.
    t.igual("E-32 `llaman` en castellano no dispara", [],
            _proveedores_en("Un agente y una skill NUNCA llaman a esto."))


def test_e33_el_adaptador_conserva_modelo_y_sesion(t):
    """E-33 (B4-24) — lo que la fuente trae se conserva; lo que no trae queda sin resolver."""
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, repeticiones=1, con_estado_de_costo=False,
                              sesion="s-42", modelo="m-especifico")
        registros = c_cc.leer(ruta)
        usos = [r for r in registros if r["kind"] == c_contrato.USO]
        t.igual("E-33 dos mensajes", 2, len(usos))
        for reg in usos:
            t.igual("E-33 conserva el modelo", "m-especifico", reg["model"])
            t.igual("E-33 conserva la sesion", "s-42", reg["session"]["providerSessionId"])
            t.verdadero("E-33 conserva el proveedor", bool(reg["provider"]))
            t.contiene("E-33 y de donde salio", "sesion.jsonl", reg["reference"])
            t.contiene("E-33 la clave sale del mensaje", "msg|", reg["dedupKey"])
            t.verdadero("E-33 con su marca de tiempo", bool(reg["timestamp"]))

        eventos_ = c_contrato.a_eventos(registros, TAREA, "claude-code")
        t.igual("E-33 la sesion llega al evento", "s-42", eventos_[0]["sessionId"])
        t.igual("E-33 y el modelo", "m-especifico", eventos_[0]["usage"]["model"])

        # Una transcripcion sin modelo ni sesion no los inventa.
        pelada = os.path.join(carpeta, "pelada.jsonl")
        with io.open(pelada, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"type": "assistant", "timestamp": "2026-09-20T10:00:00",
                                "message": {"id": "m1", "usage": {"output_tokens": 5}}}) + "\n")
        sin_datos = c_cc.leer(pelada)[0]
        t.igual("E-33 sin modelo no se inventa", None, sin_datos["model"])
        t.igual("E-33 sin sesion tampoco", None, sin_datos["session"]["providerSessionId"])
        t.igual("E-33 lo que si trae se conserva", 5, sin_datos["tokens"]["output"])
        t.igual("E-33 lo que no trae queda en None", None, sin_datos["tokens"]["input"])

        faltante = c_cc.leer(os.path.join(carpeta, "no-existe.jsonl"))
        t.igual("E-33 una fuente que no esta da un registro", 1, len(faltante))
        t.igual("E-33 sin resolver", "USAGE_UNRESOLVED", faltante[0]["state"])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e34_sin_fuente_autoritativa_queda_sin_resolver(t):
    """E-34 — el mismo contrato, y `USAGE_UNRESOLVED` en vez de cero o de nada."""
    registros = c_codex.leer()
    t.igual("E-34 devuelve un registro, no una lista vacia", 1, len(registros))
    reg = registros[0]
    t.igual("E-34 el estado", "USAGE_UNRESOLVED", reg["state"])
    t.igual("E-34 cumple el contrato", [], [e for e in c_contrato.validar_registro(reg)
                                            if "dedupKey" not in e])
    for clase in ("input", "output", "cacheRead", "cacheCreation"):
        t.igual("E-34 %s no es cero" % clase, None, reg["tokens"][clase])
    t.contiene("E-34 dice por que", "no hay una fuente", reg["reason"])

    evento = c_contrato.a_evento(reg, TAREA, "codex")
    t.igual("E-34 el evento tambien", "USAGE_UNRESOLVED", evento["usage"]["state"])
    resumen = c_agr.resumir([evento], task_id=TAREA)
    t.igual("E-34 no sumo nada", 0, resumen["tokens"]["outputTokens"])
    t.verdadero("E-34 y quedo declarado", "USAGE_UNRESOLVED" in resumen["unresolved"])

    t.verdadero("E-34 esta en el registro", "codex" in c_reg.nombres())
    t.verdadero("E-34 un adaptador que nadie declaro no se parece al mas cercano",
                c_reg.resolver("codexx") is None)
    t.verdadero("E-34 y leer con uno inventado levanta",
                _levanta(lambda: c_reg.leer("inventado", "")))


# -- E-35 a E-37 — el desacople y los secretos ---------------------------------

SENAS_DE_CONTABILIDAD = (
    "contabilidad", "accounting", "ledger.jsonl", "execution-cost",
    "budget-policy", "summary.json", "agregacion", "presupuesto.evaluar",
    "libro.agregar", "eventos.nuevo",
)


def _contabilidad_en(texto):
    bajo = texto.lower()
    return sorted(s for s in SENAS_DE_CONTABILIDAD if s.lower() in bajo)


def test_e35_ningun_agente_llama_a_la_contabilidad(t):
    """E-35 (B4-18) — si un agente tuviera que acordarse, el que se olvide no existe."""
    agentes = sorted((RAIZ / "harnesses" / "desarrollo" / "agents").glob("*.md"))
    t.verdadero("E-35 hay agentes que revisar", len(agentes) >= 8)
    for agente in agentes:
        t.igual("E-35 %s no la nombra" % agente.name, [],
                _contabilidad_en(agente.read_text(encoding="utf-8")))
    t.verdadero("E-35 el barrido encuentra una fuga",
                bool(_contabilidad_en("Antes de terminar, corre libro.agregar con tu uso.")))
    t.verdadero("E-35 tambien un import",
                bool(_contabilidad_en("from contabilidad import libro")))


def test_e36_ninguna_skill_llama_a_la_contabilidad(t):
    """E-36 (B4-19) — lo mismo del lado de los procedimientos."""
    skills = sorted((RAIZ / "harnesses" / "desarrollo" / "skills").glob("*/SKILL.md"))
    t.verdadero("E-36 hay skills que revisar", len(skills) >= 20)
    for skill in skills:
        t.igual("E-36 %s no la nombra" % skill.parent.name, [],
                _contabilidad_en(skill.read_text(encoding="utf-8")))
    t.verdadero("E-36 el barrido encuentra una fuga",
                bool(_contabilidad_en("Registra el costo en summary.json al terminar.")))
    # Y el paquete no depende de ningun agente ni de ninguna skill para funcionar.
    for fuente in _fuentes_del_paquete():
        texto = fuente.read_text(encoding="utf-8")
        t.verdadero("E-36 %s no importa el roster" % fuente.name,
                    "registro_agentes" not in texto and "import roster" not in texto)


def test_e37_el_libro_no_guarda_ni_prompts_ni_secretos(t):
    """E-37 (B4-26) — pasa por la limpieza del Bloque 2 y `rawReference` es una referencia."""
    carpeta = _tmp()
    try:
        ruta = c_libro.ruta_de(carpeta, TAREA)
        token = "glpat-" + "A" * 20
        evento = _ev(dedupKey="k-1", usage=_uso(),
                     rawReference="sesion.jsonl#L42",
                     metadata={"reason": "el token es %s y no tiene que quedar" % token})
        escrito, hallazgos = c_libro.agregar(ruta, evento)
        t.verdadero("E-37 se escribio", escrito)

        with io.open(ruta, encoding="utf-8") as f:
            crudo = f.read()
        t.verdadero("E-37 el token no quedo en el libro", token not in crudo)
        t.verdadero("E-37 y la limpieza lo dijo", bool(hallazgos))

        leido = c_libro.leer(ruta)[0]
        t.igual("E-37 la referencia es local", "sesion.jsonl#L42",
                leido["source"]["rawReference"])
        t.verdadero("E-37 la referencia no es contenido", "\n" not in
                    str(leido["source"]["rawReference"]))

        # 🔴 El contrato no tiene donde guardar una conversacion, y eso NO se prueba mirando
        # que el schema no declare un campo `prompt`: el interprete de subconjunto ignora lo
        # que no esta declarado, asi que no declararlo no lo prohibe. Lo que hay que afirmar
        # es que un evento con una clave que nadie declaro NO SE ESCRIBE — en la raiz y
        # adentro de cada objeto, porque `usage`, `time`, `cost` y `source` eran tan libres
        # como lo era `metadata` y el cierre se habia aplicado a uno solo de los cinco.
        turno = ("El usuario dijo: la clave del admin es Verano2026 y la base esta en "
                 "10.20.30.40. ") * 3
        base = _ev(dedupKey="k-base", usage=_uso(), time=c_tiempo.medir(1, 2, 3),
                   cost=_costo())
        for donde, clave in (("$", "conversacion"), ("$", "prompt"), ("$", "messages"),
                             ("usage", "turno01"), ("usage", "content"),
                             ("cost", "prompt"), ("time", "conversacion"),
                             ("source", "transcript")):
            suelto = json.loads(json.dumps(base))
            if donde == "$":
                suelto[clave] = turno
            else:
                suelto[donde][clave] = turno
            ruta_de_la_clave = clave if donde == "$" else "%s.%s" % (donde, clave)
            t.verdadero("E-37 `%s` no valida" % ruta_de_la_clave,
                        bool(c_eventos.validar_estructura(suelto)))
            t.verdadero("E-37 y no se escribe",
                        _levanta(lambda e=suelto: c_libro.agregar(ruta, e)))

        # Y la estructura anidada por la raiz, que es el camino que el test usaba para probar
        # que `metadata` estaba cerrado y que en la raiz pasaba igual.
        con_chat = json.loads(json.dumps(base))
        con_chat["conversacion"] = [{"role": "user", "text": turno}] * 10
        t.verdadero("E-37 una conversacion en la raiz no se escribe",
                    _levanta(lambda: c_libro.agregar(ruta, con_chat)))

        # El texto tampoco entra por el NOMBRE de un campo: una clave de dos mil caracteres
        # guardaba la conversacion donde el recorte de valores no la miraba.
        por_la_clave = json.loads(json.dumps(base))
        por_la_clave["usage"][turno * 10] = 1
        t.verdadero("E-37 una clave de dos mil caracteres no se escribe",
                    _levanta(lambda: c_libro.agregar(ruta, por_la_clave)))

        # Ni codificado como entero: `int` es escalar y el recorte solo toca `str`.
        numero = int.from_bytes(turno.encode("utf-8"), "big")
        t.verdadero("E-37 el entero gigante tiene cientos de digitos", len(str(numero)) > 500)
        t.verdadero("E-37 y no se puede construir",
                    _levanta(lambda: _ev(dedupKey="k-int", metadata={"reason": numero})))
        t.verdadero("E-37 ni en un campo de uso",
                    bool(c_eventos.validar_estructura(
                        dict(base, usage=dict(base["usage"], inputTokens=numero)))))
        t.igual("E-37 pero una cantidad normal si", [],
                c_eventos.validar_estructura(
                    dict(base, usage=dict(base["usage"], inputTokens=10 ** 12))))
        t.igual("E-37 el tope son dieciocho digitos", 18, c_eventos.DIGITOS)
        # NaN aparte: toda comparacion con NaN es falsa, asi que el control del tope no lo ve.
        for raro in (float("nan"), float("inf"), float("-inf"), -(10 ** 40)):
            t.verdadero("E-37 %r no es una cantidad" % raro,
                        _levanta(lambda v=raro: _ev(dedupKey="k-raro",
                                                    metadata={"reason": v})))
        t.igual("E-37 y un numero normal si lo es", [],
                c_eventos.validar_metadata({"metadata": {"reason": 42}}))

        # La premisa: el evento que el harness produce de verdad pasa el cierre entero.
        t.igual("E-37 un evento normal valida", [], c_eventos.validar_estructura(base))
        reales = c_contrato.a_eventos(
            c_cc.leer(_transcripcion(carpeta, repeticiones=2)), TAREA, "claude-code", POLITICA)
        for evento_real in reales:
            t.igual("E-37 y uno del adaptador tambien", [],
                    c_eventos.validar_estructura(evento_real))

        # 🔴 Y `metadata` tampoco, que era por donde entraba. El schema lo declara como objeto
        # libre porque el interprete de subconjunto no sabe decir "nada mas que esto"; el
        # cierre vive en `eventos.CLAVES_DE_METADATA` y lo aplica la misma validacion que el
        # schema. Antes de esto, un prompt entero —con una IP interna y una clave adentro—
        # quedaba textual en el ledger y la limpieza devolvia cero hallazgos: un prompt no es
        # un patron de secreto, y ningun catalogo lo iba a encontrar.
        prompt = ("Sos el arquitecto. El usuario dijo: la base de produccion esta en "
                  "10.20.30.40 y la clave del admin es Verano2026. Resolve el ticket.")
        for clave in ("prompt", "messages", "content", "conversacion", "respuesta", "nota"):
            t.verdadero("E-37 `metadata.%s` no se puede construir" % clave,
                        _levanta(lambda c=clave: _ev(dedupKey="x", metadata={c: prompt})))
            suelto = dict(_ev(dedupKey="x-2", usage=_uso()))
            suelto["metadata"] = {clave: prompt}
            t.verdadero("E-37 ni escribir a mano con `%s`" % clave,
                        _levanta(lambda e=suelto: c_libro.agregar(ruta, e)))
            t.verdadero("E-37 y la validacion lo dice: %s" % clave,
                        bool(c_eventos.validar_metadata({"metadata": {clave: "x"}})))
        for declarada in c_eventos.CLAVES_DE_METADATA:
            t.igual("E-37 pero `metadata.%s` si vale" % declarada, [],
                    c_eventos.validar_metadata({"metadata": {declarada: "x"}}))
        t.verdadero("E-37 son pocas claves y estan cerradas",
                    len(c_eventos.CLAVES_DE_METADATA) <= 8)

        # 🔴 Y el cierre BAJA: los valores son escalares. Cerrar solo el primer nivel no
        # cerraba nada — `{"reason": {"prompt": ...}}` pasaba limpio, y una lista de veinte
        # turnos de doscientos caracteres guardaba cuatro mil caracteres de conversacion sin
        # que el recorte por string disparara una sola vez.
        anidados = (
            {"reason": {"prompt": prompt}},
            {"reason": {"turnos": [{"rol": "user", "texto": prompt}]}},
            {"status": [prompt, prompt, prompt]},
            {"reason": [prompt[:200]] * 20},
            {"tier": {"a": {"b": {"c": prompt}}}},
        )
        for anidado in anidados:
            clave = sorted(anidado)[0]
            t.verdadero("E-37 `metadata.%s` anidado no se puede construir" % clave,
                        _levanta(lambda m=anidado: _ev(dedupKey="x", metadata=m)))
            suelto = dict(_ev(dedupKey="x-3", usage=_uso()))
            suelto["metadata"] = anidado
            t.verdadero("E-37 ni escribirlo a mano",
                        _levanta(lambda e=suelto: c_libro.agregar(ruta, e)))
            t.contiene("E-37 y la validacion dice por que", "solo valores escalares",
                       " ".join(c_eventos.validar_metadata({"metadata": anidado})))
        for escalar in ("texto", 3, 3.5, True, None):
            t.igual("E-37 un %s si vale" % type(escalar).__name__, [],
                    c_eventos.validar_metadata({"metadata": {"reason": escalar}}))

        # La segunda mitad: ningun campo aguanta un parrafo. Un motivo largo se recorta y el
        # recorte se dice, asi que una conversacion no entra ni por el campo que si existe.
        largo = _ev(dedupKey="k-largo", usage=_uso(), metadata={"reason": prompt * 4})
        t.verdadero("E-37 el motivo largo entra al evento",
                    len(largo["metadata"]["reason"]) > c_libro.TOPE_DE_TEXTO)
        _, recortes = c_libro.agregar(ruta, largo)
        guardado = [e for e in c_libro.leer(ruta) if e["eventId"] == largo["eventId"]][0]
        t.verdadero("E-37 pero al libro llega recortado",
                    len(guardado["metadata"]["reason"]) <= c_libro.TOPE_DE_TEXTO + 60)
        t.verdadero("E-37 y el recorte se declara", bool(recortes))
        t.contiene("E-37 diciendo por que", "no conversacion", " ".join(recortes))
        with io.open(ruta, encoding="utf-8") as f:
            todo = f.read()
        t.verdadero("E-37 del parrafo de cuatro copias no quedaron cuatro",
                    0 < todo.count("Verano2026") < 4)

        # 🔴 El techo se MIDE sobre el evento mas grande que el contrato permite, y ese
        # evento se ARMA DESDE EL CONTRATO. La version anterior lo escribia a mano, se
        # olvidaba cuatro campos y medía 8.848 donde el maximo eran 10.193: la proposicion
        # vecina otra vez, un nivel mas chico.
        #
        # 🔴 Y en CARACTERES, no en bytes. `recortar` cuenta caracteres y el libro se escribe
        # con `ensure_ascii=False`: el mismo evento maximo pesa 10.193 bytes en ASCII, 17.993
        # en castellano con tildes y 33.593 con emoji. El techo en bytes no es estable; el de
        # caracteres si.
        # 🔴 Se mide el CONTENIDO, no la linea. El largo de la linea escrita no es un techo:
        # `json.dumps` escapa, y los mismos 26 campos en su tope dan 10.266 caracteres de
        # linea con relleno ASCII, 11.514 con una ruta de Windows —que es la forma real de
        # `rawReference` en esta plataforma—, 18.066 con barras invertidas y 49.266 con
        # caracteres de control. El contenido es el mismo las cuatro veces.
        rellenos = {
            "ascii": "x" * 2000,
            "ruta de Windows": ("C:\\Users\\proyecto\\sesion.jsonl#L4 " * 60)[:2000],
            "barras invertidas": "\\" * 2000,
            "comillas": '"' * 2000,
            "caracteres de control": "\u0001" * 2000,
            "castellano": "á" * 2000,
            "emoji": "\U0001F600" * 2000,
        }
        t.igual("E-37 son los siete rellenos que publica la spec", 7, len(rellenos))
        contenidos, lineas = {}, {}
        for nombre, relleno in sorted(rellenos.items()):
            evento_maximo = _maximo_del_contrato(relleno)
            t.igual("E-37 el maximo con %s valida" % nombre, [],
                    c_eventos.validar(evento_maximo))
            carpeta_suelta = _tmp()
            try:
                otra = c_libro.ruta_de(carpeta_suelta, TAREA)
                c_libro.agregar(otra, evento_maximo)
                linea = io.open(otra, encoding="utf-8").read().splitlines()[-1]
            finally:
                shutil.rmtree(carpeta_suelta, ignore_errors=True)
            contenidos[nombre] = _contenido_de(json.loads(linea))
            lineas[nombre] = len(linea)

        t.igual("E-37 el contenido del maximo no depende de lo que haya adentro",
                1, len(set(contenidos.values())))
        techo = sorted(contenidos.values())[0]
        t.verdadero("E-37 y el largo de la linea si depende, por eso no es el techo",
                    len(set(lineas.values())) > 1)
        # 🔴 El numero exacto, no una banda. Una banda de 8.000 a 10.000 no discrimina: con
        # `enum[0]` en vez del enum mas largo, o sin contar los nombres de los campos, el
        # techo medido baja y la banda lo deja pasar — y el numero que publica la spec queda
        # mal. Clavarlo obliga a volver a medir cuando el contrato cambia, igual que la
        # cuenta de 26 campos.
        t.igual("E-37 el techo medido el 20-09-2026", 9643, techo)
        t.verdadero("E-37 y esta debajo de los 10.000 que publica la spec", techo < 10000)

        maximo = _maximo_del_contrato()
        c_libro.agregar(ruta, maximo)
        escrito = json.loads(io.open(ruta, encoding="utf-8").read().splitlines()[-1])

        # Si alguien agrega un campo de texto al contrato, esto se pone en rojo y obliga a
        # volver a medir en vez de dejar que el techo suba en silencio.
        t.igual("E-37 el contrato tiene 26 campos de texto", 26, _recortes_en(escrito))
        t.verdadero("E-37 el techo cabe en los campos que el contrato declara",
                    techo <= 26 * (c_libro.TOPE_DE_TEXTO + 60) + 600)
        t.verdadero("E-37 ningun campo suyo pasa el tope mas su marca",
                    _todos_acotados(escrito, c_libro.TOPE_DE_TEXTO + 60))

        campos = escrito["metadata"]
        t.igual("E-37 son los siete campos de metadata y nada mas",
                len(c_eventos.CLAVES_DE_METADATA), len(campos))
        t.verdadero("E-37 y cada uno lleva su marca de recorte",
                    all(MARCA_DE_RECORTE in v for v in campos.values()))
        # Contra los cientos de miles de caracteres de una sesion real. Es el orden lo que
        # hace verdadera la frase, no el numero exacto.
        t.verdadero("E-37 el techo es un orden menor que una conversacion real",
                    techo < 100000)

        # 📌 Lo que este mecanismo NO cierra, clavado en verde para que el dia que alguien lo
        # cierre el test obligue a hablarlo: un FRAGMENTO de hasta 300 caracteres en un campo
        # declarado pasa, con lo que traiga adentro, salvo que sea un secreto de confianza
        # alta. La limpieza del Bloque 2 redacta solo eso —un falso positivo que mutila un
        # texto es peor que un aviso, y ahi no hay a quien preguntarle— y una IP no lo es.
        # Anotado en Pendientes/Fix-Harness/PENDIENTES-FH.md.
        corto = _ev(dedupKey="k-corto", usage=_uso(),
                    metadata={"reason": "la base esta en 10.20.30.40"})
        c_libro.agregar(ruta, corto)
        with io.open(ruta, encoding="utf-8") as f:
            despues = f.read()
        t.contiene("E-37 una ip en un motivo corto SI queda, y esto lo deja dicho",
                   "10.20.30.40", despues)
        t.verdadero("E-37 lo que si se redacta es lo de confianza alta", token not in despues)
        # Y lo que NO pasa aunque sea un fragmento: repartirlo en varios campos no acumula
        # una conversacion, porque no hay donde ponerla.
        t.verdadero("E-37 no hay una octava clave donde seguir",
                    _levanta(lambda: _ev(dedupKey="x-4", metadata={"turno2": "sigo diciendo"})))
        t.verdadero("E-37 el adaptador no copia contenido",
                    "content" not in (PAQUETE / "adaptadores" / "claude_code.py").read_text(
                        encoding="utf-8").replace("bloque de contenido", ""))

        # Y lo que el adaptador si guarda de una transcripcion real es la referencia.
        con_texto = os.path.join(carpeta, "conversacion.jsonl")
        with io.open(con_texto, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({
                "type": "assistant", "sessionId": "s-1", "timestamp": "2026-09-20T10:00:00",
                "message": {"id": "m1", "model": "m", "usage": {"output_tokens": 5},
                            "content": [{"type": "text",
                                         "text": "la clave de produccion es 1234"}]}}) + "\n")
        reg = c_cc.leer(con_texto)[0]
        t.verdadero("E-37 el registro no trae el texto",
                    "produccion" not in json.dumps(reg, ensure_ascii=False))
        t.contiene("E-37 trae la referencia", "conversacion.jsonl", reg["reference"])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- E-38 y E-39 — la CLI y la instalacion -------------------------------------

def test_e38_la_cli_ingiere_resume_reporta_y_muestra(t):
    """E-38 — las cuatro acciones, y un mensaje util cuando falta lo que necesita."""
    carpeta = _tmp()
    try:
        os.makedirs(os.path.join(carpeta, ".claude"))
        fuente = _transcripcion(carpeta, repeticiones=2, con_estado_de_costo=True)
        with io.open(os.path.join(carpeta, ".claude", "harness.presupuesto.json"), "w",
                     encoding="utf-8") as f:
            f.write(json.dumps(POLITICA))

        codigo, salida, error = _correr_cli(
            ["contabilidad", TAREA, "--ingerir", fuente, "--unidad", "u-api",
             "--agente", "dev-backend", "--reporte", "--proyecto", carpeta])
        t.igual("E-38 sale bien", 0, codigo)
        t.contiene("E-38 avisa la ingesta", "contabilidad.ingesta", salida)
        t.contiene("E-38 y el resumen", "contabilidad.resumen", salida)
        t.contiene("E-38 muestra la ventana como foto", "es una foto", salida)
        t.contiene("E-38 separa el equivalente", "no lo gastado", salida)

        t.verdadero("E-38 escribio el libro",
                    os.path.isfile(c_libro.ruta_de(carpeta, TAREA)))
        t.verdadero("E-38 escribio el resumen",
                    os.path.isfile(c_libro.ruta_de(carpeta, TAREA, c_libro.RESUMEN)))
        t.verdadero("E-38 escribio el reporte",
                    os.path.isfile(c_libro.ruta_de(carpeta, TAREA, c_libro.REPORTE)))

        codigo, salida, _ = _correr_cli(
            ["contabilidad", TAREA, "--barra", "--sesion", "s-1", "--json",
             "--proyecto", carpeta])
        t.igual("E-38 la barra sale bien", 0, codigo)
        estado = json.loads(salida)
        t.igual("E-38 es la sesion pedida", "s-1", estado["sessionId"])
        t.verdadero("E-38 con su presupuesto", "budget" in estado)

        # Reingerir no duplica nada.
        codigo, salida, _ = _correr_cli(
            ["contabilidad", TAREA, "--ingerir", fuente, "--proyecto", carpeta])
        t.igual("E-38 reingerir sale bien", 0, codigo)
        t.contiene("E-38 y no escribe nada nuevo", "escritos=0", salida)

        codigo, _, error = _correr_cli(["contabilidad", "--proyecto", carpeta])
        t.igual("E-38 sin tarea sale 2", 2, codigo)
        t.contiene("E-38 y dice que falta la tarea", "necesita la tarea", error)
        t.contiene("E-38 y como se usa", "dev-harness.py contabilidad GCBA-1234", error)

        codigo, _, error = _correr_cli(
            ["contabilidad", "OTRA-1", "--proyecto", carpeta])
        t.igual("E-38 sin libro sale 2", 2, codigo)
        t.contiene("E-38 y manda a ingerir", "--ingerir", error)

        codigo, _, error = _correr_cli(
            ["contabilidad", TAREA, "--ingerir", fuente, "--adaptador", "no-existe",
             "--proyecto", carpeta])
        t.igual("E-38 un adaptador inventado sale 2", 2, codigo)
        t.contiene("E-38 y lista los que hay", "claude-code", error)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e39_todo_llega_a_un_proyecto_instalado(t):
    """E-39 — los schemas y el paquete cuelgan de lo que el instalador copia."""
    instalador = (RAIZ / "install.ps1").read_text(encoding="utf-8")
    t.contiene("E-39 el instalador copia comun/schemas", "'schemas'", instalador)
    t.contiene("E-39 y el bin de cada harness", "'bin'", instalador)

    for nombre in ("execution-accounting-event.schema.json", "budget-policy.schema.json"):
        t.verdadero("E-39 %s esta en comun/schemas" % nombre, (SCHEMAS / nombre).is_file())

    esperados = ("__init__.py", "eventos.py", "libro.py", "agregacion.py", "costos.py",
                 "tiempo.py", "presupuesto.py", "reporte.py", "barra.py")
    for nombre in esperados:
        t.verdadero("E-39 esta %s" % nombre, (PAQUETE / nombre).is_file())
    for nombre in ("__init__.py", "contrato.py", "registro.py", "claude_code.py", "codex.py"):
        t.verdadero("E-39 esta adaptadores/%s" % nombre,
                    (PAQUETE / "adaptadores" / nombre).is_file())

    t.verdadero("E-39 el paquete cuelga de bin/", PAQUETE.parent.name == "bin")
    t.verdadero("E-39 y bin/ es del harness de desarrollo",
                PAQUETE.parent.parent.name == "desarrollo")

    # Las rutas se resuelven igual instalado o desde el repositorio.
    t.verdadero("E-39 el schema del evento se localiza", c_eventos.cargar_schema() is not None)
    t.verdadero("E-39 y el del presupuesto", c_pres.cargar_schema() is not None)
    t.igual("E-39 el libro vive bajo .claude", (".claude", "runtime", "accounting"),
            c_libro.BASE)
    t.contiene("E-39 y la ruta lo refleja", os.path.join(".claude", "runtime"),
               c_libro.carpeta_de("proyecto", TAREA))
