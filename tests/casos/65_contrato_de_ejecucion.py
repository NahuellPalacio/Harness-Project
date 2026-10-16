# Los escenarios de docs/cambios/execution-contract/spec.md que no instalan: los dos schemas, el
# validador puro de bin/ejecucion/contrato.py, el modelo canonico, ADR-0014, la compatibilidad con
# Task 2, lo que queda fuera de alcance y los pendientes. EX-E53 instala de verdad y vive en
# tests/casos/65-contrato-de-ejecucion-instalador.ps1; EX-E55 es la compuerta entera. Cada
# asercion empieza con su EX-Enn. EX-F01 y EX-F02 son de la Task siguiente y no estan aca.
#
# La linea de base es f9393cf (0.30.0, el cierre de Task 2) y se lee de git en cada corrida. Sin
# esa historia -un clon superficial- los escenarios que comparan contra ella fallan en rojo con el
# motivo: no se saltean. Lo que 0.31.0 cambio a proposito (el plan 2.1, E-13 a E-17 y E-41 de 64,
# los subcomandos) se compara contra fdca5ce, el cierre de 0.31.0: es la integracion de la seccion
# "Integracion con HARNESS 0.31.0" de la spec, y sus escenarios son los EX-Gnn.
#
# El proyecto de prueba, el CLI en proceso y la lectura del documento canonico son los de
# 64_modelo_de_dominio.py, con sus mismas funciones. Los tests de Task 2 que esta Task promete no
# tocar (E-13 a E-17, E-40 a E-42) se corren desde aca y se comparan con su fuente en la base.
import ast
import copy
import importlib.util
import inspect
import json
import re
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = "f9393cf"
BASE_031 = "fdca5ce"
CASOS = RAIZ / "tests" / "casos"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
EJECUCION = BIN / "ejecucion"
CONTRATO = EJECUCION / "contrato.py"
SCHEMAS = RAIZ / "comun" / "schemas"
SCHEMA_REQUEST = SCHEMAS / "execution-request.schema.json"
SCHEMA_RESULT = SCHEMAS / "execution-result.schema.json"
SCHEMA_PLAN = SCHEMAS / "orchestration-plan.schema.json"
SPEC = RAIZ / "docs" / "cambios" / "execution-contract" / "spec.md"
DOC = RAIZ / "docs" / "dominio" / "modelo-canonico.md"
ADR = RAIZ / "docs" / "adr" / "0014-el-contrato-de-ejecucion.md"
PENDIENTES = RAIZ / "Pendientes" / "Fix-Harness" / "PENDIENTES-FH.md"
CASO_64 = "tests/casos/64_modelo_de_dominio.py"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from ejecucion import contrato as C                     # noqa: E402
from orquestacion import refutacion as R                # noqa: E402


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# El proyecto, el CLI, el documento y los escenarios de Task 2; y el colector de resultados.
M64 = _cargar("modelo_para_65", CASOS / "64_modelo_de_dominio.py")
CORRER = _cargar("correr_para_65", RAIZ / "tests" / "correr.py")
ARMADOR = M64.ARMADOR

CLAVE = "GCBA-65"
# DELEGATION_NOT_ALLOWED es de la integracion con 0.31.0 (EX-G06): eran 22 y 14 en la precedencia.
CODIGOS = ["CONTRACT_INVALID", "PLAN_UNREADABLE", "TASK_KEY_MISMATCH", "PLAN_CHANGED",
           "PLAN_NOT_READY", "DELEGATION_NOT_ALLOWED", "WORK_UNIT_NOT_FOUND",
           "WORK_UNIT_NOT_PENDING", "NORMATIVE_GATE_BLOCKED", "AGENT_UNAVAILABLE",
           "AGENT_NOT_EXECUTABLE", "AGENT_DOMAIN_MISMATCH", "CAPABILITY_UNAVAILABLE",
           "DEPENDENCY_NOT_SATISFIED", "DUPLICATE_EXECUTION", "HOST_FAILURE", "HOST_INTERRUPTED",
           "PROVIDER_FAILURE", "TIMEOUT", "OUTPUT_INVALID", "AGENT_DECLARED_NOT_COMPLETE",
           "ENGINE_FAILURE", "CANCELLED"]
PRECEDENCIA = CODIGOS[:15]
DE_CORRIDA = ["HOST_FAILURE", "HOST_INTERRUPTED", "PROVIDER_FAILURE", "TIMEOUT",
              "OUTPUT_INVALID", "AGENT_DECLARED_NOT_COMPLETE", "ENGINE_FAILURE"]
ESTADOS = ["REQUESTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "REJECTED"]
TERMINALES = ["SUCCEEDED", "FAILED", "CANCELLED", "REJECTED"]
TRANSICIONES = {("REQUESTED", "RUNNING"), ("REQUESTED", "REJECTED"), ("REQUESTED", "CANCELLED"),
                ("RUNNING", "SUCCEEDED"), ("RUNNING", "FAILED"), ("RUNNING", "CANCELLED")}
DECLARACIONES = ["COMPLETE", "PARTIAL", "BLOCKED", "FAILED"]
OTRO = "exe_" + "f" * 32
DEPENDENCIA = "exe_" + "2" * 32


# -- schemas ----------------------------------------------------------------------------------

def _esquema(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _propiedades(esquema, ruta="$", saltear=()):
    """[(ruta, nombre)] de cada clave de cada `properties`, en todo el schema y sus `$defs`.
    `saltear` son rutas cuyo subarbol no se recorre."""
    salida = []

    def recorrer(nodo, donde):
        if not isinstance(nodo, dict) or donde in saltear:
            return
        for nombre, sub in (nodo.get("properties") or {}).items():
            salida.append((donde, nombre))
            recorrer(sub, "%s.%s" % (donde, nombre))
        if isinstance(nodo.get("items"), dict):
            recorrer(nodo["items"], donde + "[]")
        for nombre, sub in (nodo.get("$defs") or {}).items():
            recorrer(sub, "%s.$defs.%s" % (donde, nombre))
    recorrer(esquema, ruta)
    return salida


def _valores(esquema, clave):
    """Todos los valores de `enum` (aplanados) o de `pattern` de un schema."""
    salida = []

    def recorrer(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                if k == clave:
                    salida.extend(v if isinstance(v, list) else [v])
                else:
                    recorrer(v)
        elif isinstance(nodo, list):
            for v in nodo:
                recorrer(v)
    recorrer(esquema)
    return salida


def _nombres_con(esquema, agujas, saltear=()):
    agujas = [a.lower() for a in agujas]
    return sorted("%s.%s" % (d, n) for d, n in _propiedades(esquema, saltear=saltear)
                  if any(a in n.lower() for a in agujas))


# -- el plan de prueba y los documentos del contrato ------------------------------------------

UNIDADES = [M64._unidad("analizar-api"),
            M64._unidad("implementar-endpoint", capacidades=("repository.write",),
                        dependencias=("analizar-api",))]
_PLAN = {}


def _plan_escrito(proy, numero):
    codigo, _, error = M64._cli(["plan", CLAVE, "--proyecto", proy,
                                 "--propuesta", proy / ("prop-%d.json" % numero)])
    if codigo != 0:
        raise AssertionError("plan --propuesta salio %s: %s" % (codigo, error[-400:]))
    return M64._leer_json(M64._plan_de(proy, CLAVE))


def _proyecto_listo(propuestas):
    """Un proyecto donde `plan --propuesta` puede dejar el plan listo. Pisado por la integracion con
    0.31.0 (EX-E02): con Flow Governance, un plan sin el repositorio de la tarea resuelto es BLOCKED
    (flowPreconditions), asi que el checkout es el de la tarea, como en 64 (`repositorio=True`)."""
    return M64._proyecto(clave=CLAVE, propuestas=propuestas, repositorio=True)


def _plan():
    """El plan READY_FOR_EXECUTION que escribe `plan --propuesta`, con dos unidades de backend y
    una dependencia entre ellas."""
    if "plan" not in _PLAN:
        proy = _proyecto_listo([M64._propuesta(UNIDADES)])
        _PLAN["proyecto"] = proy
        _PLAN["plan"] = _plan_escrito(proy, 1)
    return _PLAN["plan"]


def _unidad_del(plan, uid):
    return copy.deepcopy(next(u for u in plan["workUnits"] if u["id"] == uid))


def _firmar(req):
    """Vuelve a calcular las dos huellas derivadas: un caso rompe una cosa, no tres."""
    req["workUnitFingerprint"] = C.huella(req["workUnit"])
    req["idempotencyKey"] = C.clave_de_idempotencia(req["taskKey"], req["plan"]["planFingerprint"],
                                                    req["workUnit"]["id"])
    return req


def _request(uid="implementar-endpoint", plan=None):
    """Un ExecutionRequest valido, armado desde el plan escrito: la WorkUnit copiada tal cual, sus
    huellas, su clave y una admision que pasa."""
    plan = plan or _plan()
    unidad = _unidad_del(plan, uid)
    meta = plan["meta"]
    req = {"schema_version": C.VERSION_REQUEST,
           "executionId": "exe_" + "1" * 32,
           "createdAt": "2026-10-20T14:00:00Z",
           "requestedBy": "Persona de prueba",
           "taskKey": meta["task_key"],
           "plan": {"planId": meta["plan_id"], "planVersion": meta["plan_version"],
                    "planFingerprint": C.huella(plan), "schemaVersion": meta["schema_version"]},
           "taskContextRef": {"path": meta["task_context_ref"]["path"],
                              "contextHash": meta["task_context_ref"]["context_hash"]},
           "workUnit": unidad,
           "admission": {"planStatus": plan["status"],
                         "flow": "DELEGATION_ALLOWED",
                         "agent": {"validation": unidad["agentValidation"],
                                   "type": "SPECIALIST_AGENT", "domain": unidad["domain"]},
                         "capabilities": "ALL_AVAILABLE",
                         "normativeGate": "allowed",
                         "dependencies": [{"workUnitId": d, "executionId": DEPENDENCIA}
                                          for d in unidad["dependencies"]]}}
    return _firmar(req)


SHA = "sha256:" + "c" * 64
EVIDENCIA = {"repoRevisionBefore": "abc123", "repoRevisionAfter": "def456",
             "changes": {"state": "RESOLVED",
                         "files": [{"path": "src/app.py", "change": "MODIFIED", "fingerprint": SHA}]}}
SALIDA = {"path": ".claude/ejecuciones/GCBA-65/exe_1/output.md", "fingerprint": SHA}
HOST = {"kind": "claude-code", "sessionRef": str(uuid.UUID(int=65)), "runRef": None}


def _error(codigo, detalle="detalle de prueba"):
    return {"code": codigo, "detail": detalle}


def _resultado(req, estado="SUCCEEDED", **cambios):
    """Un resultado valido para cada terminal, y lo que el caso cambie encima."""
    res = {"schema_version": C.VERSION_RESULT, "executionId": req["executionId"],
           "requestFingerprint": C.huella(req), "status": estado, "error": None,
           "startedAt": "2026-10-20T14:00:05Z", "endedAt": "2026-10-20T14:09:00Z",
           "agentDeclaredStatus": None, "output": None, "evidence": copy.deepcopy(EVIDENCIA),
           "host": dict(HOST)}
    if estado == "SUCCEEDED":
        res.update(agentDeclaredStatus="COMPLETE", output=dict(SALIDA))
    elif estado == "FAILED":
        res.update(error=_error("AGENT_DECLARED_NOT_COMPLETE"), agentDeclaredStatus="PARTIAL",
                   output=dict(SALIDA))
    elif estado == "CANCELLED":
        res.update(error=_error("CANCELLED"), startedAt=None, evidence=None)
    elif estado == "REJECTED":
        res.update(error=_error("PLAN_CHANGED"), startedAt=None, evidence=None)
    res.update(cambios)
    return res


def _nombra(errores, campo):
    return any(e.startswith(campo) for e in errores)


def _pasa(t, eid, rotulo, errores):
    t.igual("%s %s: pasa" % (eid, rotulo), [], errores)


def _falla(t, eid, rotulo, errores, campo):
    t.verdadero("%s %s: no pasa" % (eid, rotulo), len(errores) > 0)
    t.verdadero("%s %s: el error nombra %s" % (eid, rotulo, campo), _nombra(errores, campo))


def _con(req, ruta, valor, firmar=False):
    """Una copia de `req` con `valor` en la ruta (lista de claves). `None` como valor borra si la
    ultima clave es `-`."""
    otro = copy.deepcopy(req)
    nodo = otro
    for clave in ruta[:-1]:
        nodo = nodo[clave]
    if valor == "-":
        del nodo[ruta[-1]]
    else:
        nodo[ruta[-1]] = valor
    return _firmar(otro) if firmar else otro


# -- git, la linea de base y los tests de Task 2 ----------------------------------------------

def _hay_base(base=BASE):
    codigo, _ = M64._git("cat-file", "-e", base + "^{commit}")
    return codigo == 0


def _sin_base(t, eid, base=BASE):
    t.igual("%s la linea de base %s esta disponible" % (eid, base), "disponible",
            "no esta el commit %s en este clon: no hay contra que comparar" % base)


def _igual_a_la_base(ruta, base=BASE):
    """Si el archivo es el de la base, con la normalizacion de fin de linea de git."""
    codigo, _ = M64._git("diff", "--quiet", base, "--", ruta)
    return codigo == 0


def _fuente_de(texto, funcion):
    arbol = ast.parse(texto)
    for n in arbol.body:
        if isinstance(n, ast.FunctionDef) and n.name == funcion:
            return (ast.get_source_segment(texto, n) or "").replace("\r\n", "\n")
    return None


def _fuente_base_de_64(base=BASE):
    codigo, crudo = M64._git("show", "%s:%s" % (base, CASO_64))
    return crudo.decode("utf-8") if codigo == 0 else ""


def _corre_de_64(t, eid, funciones, base=BASE):
    """Corre tests de Task 2 desde aca: que sigan en verde, y que su fuente sea la de la base."""
    fuente = _fuente_base_de_64(base)
    ahora = (RAIZ / CASO_64).read_text(encoding="utf-8")
    for funcion in funciones:
        t.verdadero("%s %s existe en la base y ahora" % (eid, funcion),
                    _fuente_de(fuente, funcion) is not None and _fuente_de(ahora, funcion) is not None)
        t.igual("%s %s no cambio respecto de %s" % (eid, funcion, base),
                _fuente_de(fuente, funcion), _fuente_de(ahora, funcion))
        r = CORRER.Resultados()
        try:
            getattr(M64, funcion)(r)
            caidas = []
        except Exception as e:            # noqa: BLE001 - el motivo es el detalle
            caidas = ["%s: %s" % (type(e).__name__, e)]
        t.verdadero("%s %s tiene aserciones" % (eid, funcion), len(r.filas) > 0)
        t.vacio("%s %s sigue en verde" % (eid, funcion),
                caidas + ["%s %s" % (n, d) for _, n, ok, d in r.filas if not ok])


# -- codigo: lectura estatica -----------------------------------------------------------------

def _py_de(carpeta):
    return sorted(p for p in Path(carpeta).rglob("*.py") if "__pycache__" not in p.parts)


def _arbol(ruta):
    return ast.parse(Path(ruta).read_text(encoding="utf-8-sig"))


def _importados(ruta):
    """Los modulos que importa un fuente, por su primer segmento, y los `from x import y` por y."""
    salida = set()
    for n in ast.walk(_arbol(ruta)):
        if isinstance(n, ast.Import):
            salida |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                salida.add(n.module.split(".")[0])
            salida |= {a.name for a in n.names}
    return salida


def _constantes(ruta):
    return [n.value for n in ast.walk(_arbol(ruta))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _nombre(nodo):
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return _nombre(nodo.value) + "." + nodo.attr
    return ""


def _de_produccion():
    return [p for p in _py_de(BIN) + _py_de(RAIZ / "comun") if EJECUCION not in p.parents]


# -- el modelo canonico, el ADR y la spec -----------------------------------------------------

def _tabla_8_2():
    """{concepto: (contexto, clasificacion)} de la tabla de 8.2 de la spec."""
    tablas = M64._tablas(M64._seccion(M64._texto(SPEC), "8.2 El modelo", nivel=3))
    return {f[0]: (f[1], f[2]) for f in (tablas[0][1:] if tablas else []) if len(f) >= 3}


def _desigualdades_nuevas():
    """Los seis titulos en negrita de la lista de 26.1 de la spec, sin el punto final."""
    lineas = M64._seccion(M64._texto(SPEC), "26.1 `docs/dominio/modelo-canonico.md`", nivel=3)
    salida = []
    for linea in lineas:
        m = re.match(r"^\d+\.\s+\*\*(.+?)\*\*", linea)
        if m:
            salida.append(m.group(1).rstrip(".").strip())
    return salida


def _decisiones_del_adr():
    texto = M64._texto(ADR) if ADR.is_file() else ""
    return [(m.group(1), m.group(2)) for m in re.finditer(r"(?m)^### (\d+)\. (.+)$", texto)]


# =============================================================================================
# El contrato
# =============================================================================================

def test_ex_e01_los_dos_schemas(t):
    """EX-E01 — los dos schemas existen, con su $id, schema_version de un solo valor igual al $id,
    la raiz cerrada, y pasan controlar_soporte."""
    for ruta, version in ((SCHEMA_REQUEST, "execution-request/1.0"),
                          (SCHEMA_RESULT, "execution-result/1.0")):
        t.verdadero("EX-E01 existe %s" % ruta.name, ruta.is_file())
        esquema = _esquema(ruta) if ruta.is_file() else {}
        t.igual("EX-E01 %s tiene $id %s" % (ruta.name, version), version, esquema.get("$id"))
        t.igual("EX-E01 %s: schema_version es un enum de un valor igual al $id" % ruta.name,
                [version], ((esquema.get("properties") or {}).get("schema_version") or {}).get("enum"))
        t.igual("EX-E01 %s: la raiz esta cerrada" % ruta.name, False,
                esquema.get("additionalProperties"))
        try:
            ARMADOR.controlar_soporte(esquema)
            error = ""
        except Exception as e:            # noqa: BLE001 - el motivo es el detalle
            error = "%s: %s" % (type(e).__name__, e)
        t.igual("EX-E01 %s pasa controlar_soporte" % ruta.name, "", error)
    t.igual("EX-E01 contrato.py nombra las dos versiones",
            ["execution-request/1.0", "execution-result/1.0"], [C.VERSION_REQUEST, C.VERSION_RESULT])


def test_ex_e02_un_request_armado_desde_un_plan_real(t):
    """EX-E02 — plan --propuesta escribe un plan READY_FOR_EXECUTION; el request armado desde ese
    plan valida contra el schema y validar_request devuelve []."""
    plan = _plan()
    t.igual("EX-E02 el plan escrito esta READY_FOR_EXECUTION", "READY_FOR_EXECUTION", plan["status"])
    req = _request()
    t.igual("EX-E02 la WorkUnit es la del plan, tal cual",
            _unidad_del(plan, "implementar-endpoint"), req["workUnit"])
    t.igual("EX-E02 el request valida contra execution-request/1.0", [],
            ARMADOR.validar(req, _esquema(SCHEMA_REQUEST)))
    t.igual("EX-E02 validar_request devuelve []", [], C.validar_request(req))
    t.igual("EX-E02 tambien la unidad sin dependencias", [],
            C.validar_request(_request("analizar-api")))


OBLIGATORIOS_REQUEST = ["schema_version", "executionId", "idempotencyKey", "createdAt",
                        "requestedBy", "taskKey", "plan", "taskContextRef", "workUnit",
                        "workUnitFingerprint", "admission"]


def test_ex_e03_un_request_roto_no_pasa(t):
    """EX-E03 — el request de EX-E02 deja de pasar si le falta un obligatorio, si trae una clave de
    mas en la raiz, en plan o en admission, o si workUnit es una lista de dos unidades."""
    req = _request()
    t.igual("EX-E03 el schema pide exactamente los once obligatorios", sorted(OBLIGATORIOS_REQUEST),
            sorted(_esquema(SCHEMA_REQUEST)["required"]))
    for campo in OBLIGATORIOS_REQUEST:
        _falla(t, "EX-E03", "sin %s" % campo, C.validar_request(_con(req, [campo], "-")),
               "$.%s" % campo)
    for ruta in (["sobrante"], ["plan", "sobrante"], ["admission", "sobrante"]):
        _falla(t, "EX-E03", "con una clave de mas en %s" % ".".join(ruta),
               C.validar_request(_con(req, ruta, 1)), "$." + ".".join(ruta))
    dos = [_unidad_del(_plan(), "analizar-api"), _unidad_del(_plan(), "implementar-endpoint")]
    _falla(t, "EX-E03", "con workUnit como una lista de dos", C.validar_request(_con(req, ["workUnit"], dos)),
           "$.workUnit")


def test_ex_e04_un_resultado_por_terminal(t):
    """EX-E04 — un resultado valido por cada terminal pasa validar_resultado; uno REQUESTED o
    RUNNING no valida."""
    req = _request()
    for estado in TERMINALES:
        _pasa(t, "EX-E04", "un %s" % estado, C.validar_resultado(_resultado(req, estado), req))
    for estado in ("REQUESTED", "RUNNING"):
        _falla(t, "EX-E04", "un resultado %s" % estado,
               C.validar_resultado(_resultado(req, status=estado), req), "$.status")
    t.igual("EX-E04 el enum de status son los cuatro terminales", TERMINALES,
            _esquema(SCHEMA_RESULT)["properties"]["status"]["enum"])


def test_ex_e05_el_error_estructurado(t):
    """EX-E05 — $defs.error tiene exactamente code y detail, cerrado; code es uno de los 23, en
    orden; no validan otro codigo, un texto ni un objeto sin code; ningun codigo empieza con TOOL_.
    Pisado por la integracion con 0.31.0: eran 22, y DELEGATION_NOT_ALLOWED es el sexto (EX-G06)."""
    esquema = _esquema(SCHEMA_RESULT)
    error = esquema["$defs"]["error"]
    t.igual("EX-E05 $defs.error tiene exactamente code y detail", ["code", "detail"],
            sorted(error["properties"]))
    t.igual("EX-E05 $defs.error esta cerrado", False, error.get("additionalProperties"))
    t.igual("EX-E05 los dos son obligatorios", ["code", "detail"], sorted(error.get("required")))
    t.igual("EX-E05 code: los 23 de 14, en ese orden", CODIGOS, error["properties"]["code"]["enum"])
    t.igual("EX-E05 contrato.CODIGOS son los mismos 23, en el mismo orden", CODIGOS, list(C.CODIGOS))

    def contra_def(dato):
        return ARMADOR.validar(dato, error, "$", esquema)
    _pasa(t, "EX-E05", "un error con un codigo de la lista", contra_def(_error("TIMEOUT")))
    for rotulo, dato in (("un codigo fuera de la lista", _error("OTRO_CODIGO")),
                         ("un texto en lugar del objeto", "fallo la ejecucion"),
                         ("un objeto sin code", {"detail": "sin codigo"})):
        t.verdadero("EX-E05 %s no valida" % rotulo, len(contra_def(dato)) > 0)
    t.vacio("EX-E05 ningun codigo empieza con TOOL_", [c for c in CODIGOS if c.startswith("TOOL_")])


# =============================================================================================
# Identidad
# =============================================================================================

def test_ex_e06_execution_id(t):
    """EX-E06 — executionId cumple ^exe_[0-9a-f]{32}$ en request y resultado; un session_id de
    Claude Code (un UUID con guiones) no valida."""
    patron = "^exe_[0-9a-f]{32}$"
    t.igual("EX-E06 el patron del request", patron,
            _esquema(SCHEMA_REQUEST)["properties"]["executionId"]["pattern"])
    t.igual("EX-E06 el patron del resultado", patron,
            _esquema(SCHEMA_RESULT)["properties"]["executionId"]["pattern"])
    sesion = str(uuid.UUID(int=6565))
    req = _request()
    _falla(t, "EX-E06", "un request con un session_id como executionId",
           C.validar_request(_con(req, ["executionId"], sesion)), "$.executionId")
    res = _resultado(req)
    res["executionId"] = sesion
    _falla(t, "EX-E06", "un resultado con un session_id como executionId",
           C.validar_resultado(res, req), "$.executionId")


def test_ex_e07_el_plan_es_de_la_task(t):
    """EX-E07 — un planId que no es pln_ mas la taskKey no pasa; una taskKey sin forma no valida."""
    req = _request()
    _falla(t, "EX-E07", "con el planId de otra clave",
           C.validar_request(_con(req, ["plan", "planId"], "pln_OTRA-1")), "$.plan.planId")
    _falla(t, "EX-E07", "con una taskKey sin forma",
           C.validar_request(_con(req, ["taskKey"], "gcba 65")), "$.taskKey")


def test_ex_e08_la_huella_del_plan(t):
    """EX-E08 — contrato.huella es refutacion.huella sin importarla; dos plan --propuesta dejan el
    mismo plan_id y plan_version 1 con huellas distintas."""
    for rotulo, valor in (("el plan", _plan()), ("un texto con tildes", {"ñ": "acción", "a": [1, 2]}),
                          ("una lista", ["GCBA-65", "sha256:x", "u"]), ("un numero", 65)):
        t.igual("EX-E08 contrato.huella == refutacion.huella para %s" % rotulo,
                R.huella(valor), C.huella(valor))
    t.vacio("EX-E08 bin/ejecucion/ no importa refutacion",
            [p.name for p in _py_de(EJECUCION) if "refutacion" in _importados(p)])
    proy = M64._proyecto(clave=CLAVE, propuestas=[
        M64._propuesta(UNIDADES), M64._propuesta(UNIDADES, objective="Otro objetivo")])
    primero = _plan_escrito(proy, 1)
    segundo = _plan_escrito(proy, 2)
    t.igual("EX-E08 los dos tienen el mismo plan_id", primero["meta"]["plan_id"],
            segundo["meta"]["plan_id"])
    t.igual("EX-E08 los dos tienen plan_version 1", [1, 1],
            [primero["meta"]["plan_version"], segundo["meta"]["plan_version"]])
    t.verdadero("EX-E08 y planFingerprint distintos", C.huella(primero) != C.huella(segundo))


def test_ex_e09_la_clave_de_idempotencia(t):
    """EX-E09 — idempotencyKey es clave_de_idempotencia(taskKey, planFingerprint, workUnit.id);
    otra clave no pasa; dos intentos comparten clave; otro plan da otra clave."""
    req = _request()
    t.igual("EX-E09 es la huella de [taskKey, planFingerprint, workUnit.id]",
            C.huella([CLAVE, req["plan"]["planFingerprint"], "implementar-endpoint"]),
            req["idempotencyKey"])
    _falla(t, "EX-E09", "con otra clave",
           C.validar_request(_con(req, ["idempotencyKey"], C.huella(["otra"]))), "$.idempotencyKey")
    otro = _con(req, ["executionId"], OTRO)
    _pasa(t, "EX-E09", "otro intento de la misma WorkUnit", C.validar_request(otro))
    t.igual("EX-E09 dos intentos de la misma WorkUnit del mismo plan tienen la misma clave",
            req["idempotencyKey"], otro["idempotencyKey"])
    t.verdadero("EX-E09 la misma WorkUnit en un plan con otra huella da otra clave",
                C.clave_de_idempotencia(CLAVE, C.huella({"otro": "plan"}), "implementar-endpoint")
                != req["idempotencyKey"])


def test_ex_e10_la_huella_de_la_workunit(t):
    """EX-E10 — cambiar un campo de workUnit sin recalcular su huella hace fallar validar_request."""
    _falla(t, "EX-E10", "con el objetivo cambiado y la huella vieja",
           C.validar_request(_con(_request(), ["workUnit", "objective"], "otra cosa")),
           "$.workUnitFingerprint")


def test_ex_e11_el_resultado_es_de_su_request(t):
    """EX-E11 — validar_resultado exige el executionId del request y la huella del request."""
    req = _request()
    res = _resultado(req)
    _pasa(t, "EX-E11", "el resultado de su request", C.validar_resultado(res, req))
    _falla(t, "EX-E11", "con el executionId de otro", C.validar_resultado(
        dict(res, executionId=OTRO), req), "$.executionId")
    tocado = _con(req, ["requestedBy"], "Otra persona")
    _falla(t, "EX-E11", "con el request tocado despues", C.validar_resultado(res, tocado),
           "$.requestFingerprint")


# =============================================================================================
# Lo que la admision deja escrito
# =============================================================================================

def test_ex_e12_el_plan_no_esta_listo(t):
    """EX-E12 — admission.planStatus CAPABILITY_RESOLUTION, WAITING_FOR_HUMAN_APPROVAL o BLOCKED no
    valida. Pisado por la integracion con 0.31.0: BLOCKED es estado publico del plan en 2.1."""
    for estado in ("CAPABILITY_RESOLUTION", "WAITING_FOR_HUMAN_APPROVAL", "BLOCKED"):
        _falla(t, "EX-E12", "con planStatus %s" % estado,
               C.validar_request(_con(_request(), ["admission", "planStatus"], estado)),
               "$.admission.planStatus")


def test_ex_e13_la_unidad_no_esta_pending(t):
    """EX-E13 — workUnit.status BLOCKED o WAITING_FOR_HUMAN_APPROVAL no valida."""
    for estado in ("BLOCKED", "WAITING_FOR_HUMAN_APPROVAL"):
        _falla(t, "EX-E13", "con la unidad %s" % estado,
               C.validar_request(_con(_request(), ["workUnit", "status"], estado, firmar=True)),
               "$.workUnit.status")


def test_ex_e14_agente_inexistente(t):
    """EX-E14 — los nueve agentValidation que no son ruteables no validan; ni un assignedAgent
    vacio o sin la forma del registro."""
    todos = (_esquema(SCHEMA_PLAN)["properties"]["workUnits"]["items"]["properties"]
             ["agentValidation"]["enum"])
    malos = [v for v in todos if v not in ("VALID", "VALID_WITH_PENDING_SKILLS")]
    t.igual("EX-E14 son nueve", 9, len(malos))
    for valor in malos:
        _falla(t, "EX-E14", "con agent.validation %s" % valor,
               C.validar_request(_con(_request(), ["admission", "agent", "validation"], valor)),
               "$.admission.agent.validation")
    for agente in ("", "backend-agent", "dev-Backend"):
        _falla(t, "EX-E14", "con assignedAgent `%s`" % agente,
               C.validar_request(_con(_request(), ["workUnit", "assignedAgent"], agente, firmar=True)),
               "$.workUnit.assignedAgent")


def test_ex_e15_decide_el_registro_al_admitir(t):
    """EX-E15 — con agentExists false en la unidad y VALID en la admision, el request pasa."""
    req = _request()
    req["workUnit"]["agentExists"] = False
    req["workUnit"]["agentValidation"] = "AGENT_NOT_FOUND"
    _pasa(t, "EX-E15", "agentExists false en el plan y VALID al admitir",
          C.validar_request(_firmar(req)))


def test_ex_e16_ni_el_orquestador_ni_el_refutador(t):
    """EX-E16 — admission.agent.type ORCHESTRATOR_AGENT o CRITIC_AGENT no valida."""
    for tipo in ("ORCHESTRATOR_AGENT", "CRITIC_AGENT"):
        _falla(t, "EX-E16", "con agent.type %s" % tipo,
               C.validar_request(_con(_request(), ["admission", "agent", "type"], tipo)),
               "$.admission.agent.type")
    for tipo in ("SPECIALIST_AGENT", "INFRASTRUCTURE_AGENT"):
        _pasa(t, "EX-E16", "con agent.type %s" % tipo,
              C.validar_request(_con(_request(), ["admission", "agent", "type"], tipo)))
    t.igual("EX-E16 contrato.TIPOS_EJECUTABLES", ("SPECIALIST_AGENT", "INFRASTRUCTURE_AGENT"),
            C.TIPOS_EJECUTABLES)


def test_ex_e17_el_dominio_equivocado(t):
    """EX-E17 — admission.agent.domain distinto de workUnit.domain no pasa."""
    _falla(t, "EX-E17", "con el agente de otro dominio",
           C.validar_request(_con(_request(), ["admission", "agent", "domain"], "frontend")),
           "$.admission.agent.domain")


def test_ex_e18_capability_ausente(t):
    """EX-E18 — admission.capabilities distinto de ALL_AVAILABLE no valida; Read o Glob en
    requiredCapabilities tampoco."""
    _falla(t, "EX-E18", "con capabilities SOME_MISSING",
           C.validar_request(_con(_request(), ["admission", "capabilities"], "SOME_MISSING")),
           "$.admission.capabilities")
    for herramienta in ("Read", "Glob"):
        _falla(t, "EX-E18", "con %s en requiredCapabilities" % herramienta,
               C.validar_request(_con(_request(), ["workUnit", "requiredCapabilities"],
                                      [herramienta], firmar=True)),
               "$.workUnit.requiredCapabilities")
    _pasa(t, "EX-E18", "con una capability de integracion",
          C.validar_request(_con(_request(), ["workUnit", "requiredCapabilities"],
                                 ["gitlab.merge_request.read"], firmar=True)))


def test_ex_e19_las_dependencias_satisfechas(t):
    """EX-E19 — admission.dependencies nombra exactamente las de la WorkUnit, una vez, con un
    executionId valido distinto del propio."""
    req = _request()
    una = {"workUnitId": "analizar-api", "executionId": DEPENDENCIA}
    for rotulo, deps in (("con una de menos", []),
                         ("con una de mas", [una, {"workUnitId": "otra", "executionId": DEPENDENCIA}]),
                         ("con una repetida", [una, dict(una)]),
                         ("con el propio id", [dict(una, executionId=req["executionId"])]),
                         ("con un executionId sin forma", [dict(una, executionId="exe-1")])):
        _falla(t, "EX-E19", rotulo,
               C.validar_request(_con(req, ["admission", "dependencies"], deps)),
               "$.admission.dependencies")


def test_ex_e20_la_precedencia_y_el_rechazo_al_pedir(t):
    """EX-E20 — contrato.PRECEDENCIA es la lista de 9.2; validar_rechazo acepta esos codigos salvo
    PLAN_CHANGED, y rechaza los de corrida y CANCELLED. Pisado por la integracion con 0.31.0: son
    quince, con DELEGATION_NOT_ALLOWED despues de PLAN_NOT_READY."""
    t.igual("EX-E20 PRECEDENCIA es la de 9.2, en orden", PRECEDENCIA, list(C.PRECEDENCIA))
    for codigo in PRECEDENCIA:
        errores = C.validar_rechazo(_error(codigo))
        if codigo == "PLAN_CHANGED":
            _falla(t, "EX-E20", "un rechazo al pedir con PLAN_CHANGED", errores, "$.code")
        else:
            _pasa(t, "EX-E20", "un rechazo al pedir con %s" % codigo, errores)
    for codigo in DE_CORRIDA + ["CANCELLED"]:
        _falla(t, "EX-E20", "un rechazo al pedir con %s" % codigo,
               C.validar_rechazo(_error(codigo)), "$.code")
    _falla(t, "EX-E20", "un rechazo sin detalle", C.validar_rechazo(_error("PLAN_NOT_READY", "")),
           "$.detail")


# =============================================================================================
# La compuerta normativa y Governance
# =============================================================================================

def test_ex_e21_compuerta_allowed(t):
    """EX-E21 — normativeGate allowed valida."""
    _pasa(t, "EX-E21", "con normativeGate allowed",
          C.validar_request(_con(_request(), ["admission", "normativeGate"], "allowed")))


def test_ex_e22_compuerta_unresolved(t):
    """EX-E22 — normativeGate unresolved valida: la compuerta no corta con unresolved."""
    _pasa(t, "EX-E22", "con normativeGate unresolved",
          C.validar_request(_con(_request(), ["admission", "normativeGate"], "unresolved")))


def test_ex_e23_compuerta_blocked(t):
    """EX-E23 — blocked no valida; NORMATIVE_GATE_BLOCKED va al pedir y en REJECTED, nunca en
    FAILED; ningun codigo empieza con GOVERNANCE."""
    _falla(t, "EX-E23", "con normativeGate blocked",
           C.validar_request(_con(_request(), ["admission", "normativeGate"], "blocked")),
           "$.admission.normativeGate")
    _pasa(t, "EX-E23", "un rechazo al pedir con NORMATIVE_GATE_BLOCKED",
          C.validar_rechazo(_error("NORMATIVE_GATE_BLOCKED")))
    req = _request()
    _pasa(t, "EX-E23", "un REJECTED con NORMATIVE_GATE_BLOCKED",
          C.validar_resultado(_resultado(req, "REJECTED", error=_error("NORMATIVE_GATE_BLOCKED")), req))
    _falla(t, "EX-E23", "un FAILED con NORMATIVE_GATE_BLOCKED",
           C.validar_resultado(_resultado(req, "FAILED", error=_error("NORMATIVE_GATE_BLOCKED"),
                                          agentDeclaredStatus=None, output=None), req),
           "$.error.code")
    t.vacio("EX-E23 ningun codigo empieza con GOVERNANCE",
            [c for c in list(C.CODIGOS) + _valores(_esquema(SCHEMA_RESULT), "enum")
             if isinstance(c, str) and c.startswith("GOVERNANCE")])


def test_ex_e24_sin_aprobaciones_presupuesto_ni_permisos(t):
    """EX-E24 — ningun schema tiene una propiedad con approval, budget, timeout o permission."""
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        t.vacio("EX-E24 %s no tiene aprobaciones, presupuesto, timeout ni permisos" % ruta.name,
                _nombres_con(_esquema(ruta), ("approval", "budget", "timeout", "permission")))


# =============================================================================================
# Ciclo de vida
# =============================================================================================

def test_ex_e25_las_seis_transiciones(t):
    """EX-E25 — TRANSICIONES tiene exactamente seis pares; transicion_valida es True para esos y
    False para los otros treinta."""
    t.igual("EX-E25 contrato.ESTADOS son los seis", ESTADOS, list(C.ESTADOS))
    t.igual("EX-E25 TRANSICIONES son los seis pares", TRANSICIONES, set(C.TRANSICIONES))
    t.igual("EX-E25 sin pares repetidos", 6, len(C.TRANSICIONES))
    validas = {(a, b) for a in ESTADOS for b in ESTADOS if C.transicion_valida(a, b)}
    t.igual("EX-E25 transicion_valida es True exactamente para los seis", TRANSICIONES, validas)
    t.igual("EX-E25 y False para los otros treinta", 30,
            len([(a, b) for a in ESTADOS for b in ESTADOS if not C.transicion_valida(a, b)]))


def test_ex_e26_camino_feliz(t):
    """EX-E26 — un SUCCEEDED con startedAt, endedAt posterior, COMPLETE, output y evidencia pasa;
    sin output, sin COMPLETE o sin startedAt no pasa."""
    req = _request()
    _pasa(t, "EX-E26", "un SUCCEEDED completo", C.validar_resultado(_resultado(req), req))
    for rotulo, cambios, campo in (
            ("sin output", {"output": None}, "$.output"),
            ("con agentDeclaredStatus null", {"agentDeclaredStatus": None}, "$.output"),
            ("con agentDeclaredStatus null y sin output",
             {"agentDeclaredStatus": None, "output": None}, "$.agentDeclaredStatus"),
            ("con PARTIAL", {"agentDeclaredStatus": "PARTIAL"}, "$.agentDeclaredStatus"),
            ("sin startedAt", {"startedAt": None}, "$.startedAt"),
            ("con endedAt antes de startedAt", {"endedAt": "2026-10-20T14:00:01Z"}, "$.endedAt")):
        _falla(t, "EX-E26", "un SUCCEEDED %s" % rotulo,
               C.validar_resultado(_resultado(req, **cambios), req), campo)


def test_ex_e27_rechazo(t):
    """EX-E27 — un REJECTED con startedAt, evidence, output o agentDeclaredStatus no pasa; con los
    cuatro nulos y un codigo de rechazo, pasa."""
    req = _request()
    _pasa(t, "EX-E27", "un REJECTED sin nada", C.validar_resultado(_resultado(req, "REJECTED"), req))
    for campo, valor in (("startedAt", "2026-10-20T14:00:05Z"), ("evidence", copy.deepcopy(EVIDENCIA)),
                         ("output", dict(SALIDA)), ("agentDeclaredStatus", "FAILED")):
        _falla(t, "EX-E27", "un REJECTED con %s" % campo,
               C.validar_resultado(_resultado(req, "REJECTED", **{campo: valor}), req), "$." + campo)


def test_ex_e28_falla(t):
    """EX-E28 — FAILED: sin error, sin startedAt o con un codigo de admision no pasa;
    HOST_INTERRUPTED pasa; el AgentReport decide AGENT_DECLARED_NOT_COMPLETE y OUTPUT_INVALID."""
    req = _request()
    sin_informe = {"agentDeclaredStatus": None, "output": None}
    _falla(t, "EX-E28", "un FAILED sin error",
           C.validar_resultado(_resultado(req, "FAILED", error=None), req), "$.error")
    _falla(t, "EX-E28", "un FAILED sin startedAt",
           C.validar_resultado(_resultado(req, "FAILED", startedAt=None, evidence=None), req),
           "$.startedAt")
    _falla(t, "EX-E28", "un FAILED con PLAN_NOT_READY",
           C.validar_resultado(_resultado(req, "FAILED", error=_error("PLAN_NOT_READY"),
                                          **sin_informe), req), "$.error.code")
    _pasa(t, "EX-E28", "un FAILED con HOST_INTERRUPTED",
          C.validar_resultado(_resultado(req, "FAILED", error=_error("HOST_INTERRUPTED"),
                                         **sin_informe), req))
    for declarado in ("PARTIAL", "BLOCKED", "FAILED"):
        _pasa(t, "EX-E28", "AGENT_DECLARED_NOT_COMPLETE con %s" % declarado,
              C.validar_resultado(_resultado(req, "FAILED", agentDeclaredStatus=declarado), req))
    _falla(t, "EX-E28", "AGENT_DECLARED_NOT_COMPLETE sin AgentReport",
           C.validar_resultado(_resultado(req, "FAILED", **sin_informe), req), "$.agentDeclaredStatus")
    _falla(t, "EX-E28", "AGENT_DECLARED_NOT_COMPLETE con COMPLETE",
           C.validar_resultado(_resultado(req, "FAILED", agentDeclaredStatus="COMPLETE"), req),
           "$.agentDeclaredStatus")
    _pasa(t, "EX-E28", "OUTPUT_INVALID sin AgentReport",
          C.validar_resultado(_resultado(req, "FAILED", error=_error("OUTPUT_INVALID"),
                                         **sin_informe), req))
    _falla(t, "EX-E28", "OUTPUT_INVALID con agentDeclaredStatus",
           C.validar_resultado(_resultado(req, "FAILED", error=_error("OUTPUT_INVALID")), req),
           "$.agentDeclaredStatus")
    _falla(t, "EX-E28", "un FAILED con un AgentReport y TIMEOUT",
           C.validar_resultado(_resultado(req, "FAILED", error=_error("TIMEOUT")), req),
           "$.agentDeclaredStatus")


def test_ex_e29_cancelacion(t):
    """EX-E29 — CANCELLED lleva CANCELLED y ningun otro codigo, y AgentReport nulo; sin startedAt
    no tiene evidencia, con startedAt la tiene."""
    req = _request()
    _pasa(t, "EX-E29", "un CANCELLED antes de entregar", C.validar_resultado(_resultado(req, "CANCELLED"), req))
    _pasa(t, "EX-E29", "un CANCELLED durante la corrida",
          C.validar_resultado(_resultado(req, "CANCELLED", startedAt="2026-10-20T14:00:05Z",
                                         evidence=copy.deepcopy(EVIDENCIA)), req))
    _falla(t, "EX-E29", "un CANCELLED con HOST_INTERRUPTED",
           C.validar_resultado(_resultado(req, "CANCELLED", error=_error("HOST_INTERRUPTED")), req),
           "$.error.code")
    _falla(t, "EX-E29", "un CANCELLED con un AgentReport",
           C.validar_resultado(_resultado(req, "CANCELLED", startedAt="2026-10-20T14:00:05Z",
                                          evidence=copy.deepcopy(EVIDENCIA), agentDeclaredStatus="PARTIAL",
                                          output=dict(SALIDA)), req), "$.agentDeclaredStatus")
    _falla(t, "EX-E29", "un CANCELLED con startedAt y sin evidencia",
           C.validar_resultado(_resultado(req, "CANCELLED", startedAt="2026-10-20T14:00:05Z"), req),
           "$.evidence")
    _falla(t, "EX-E29", "un CANCELLED sin startedAt y con evidencia",
           C.validar_resultado(_resultado(req, "CANCELLED", evidence=copy.deepcopy(EVIDENCIA)), req),
           "$.evidence")


def test_ex_e30_un_terminal_no_cambia(t):
    """EX-E30 — desde cada terminal, transicion_valida es False hacia los seis estados, y
    TERMINALES son exactamente esos cuatro."""
    t.igual("EX-E30 contrato.TERMINALES son los cuatro", TERMINALES, list(C.TERMINALES))
    for terminal in TERMINALES:
        t.vacio("EX-E30 desde %s no sale ninguna transicion" % terminal,
                [e for e in ESTADOS if C.transicion_valida(terminal, e)])


def test_ex_e31_succeeded_si_y_solo_si_no_hay_error(t):
    """EX-E31 — un SUCCEEDED con error no pasa, ni un FAILED, CANCELLED o REJECTED sin error."""
    req = _request()
    _falla(t, "EX-E31", "un SUCCEEDED con error",
           C.validar_resultado(_resultado(req, error=_error("TIMEOUT")), req), "$.error")
    for estado in ("FAILED", "CANCELLED", "REJECTED"):
        _falla(t, "EX-E31", "un %s sin error" % estado,
               C.validar_resultado(_resultado(req, estado, error=None), req), "$.error")


def test_ex_e32_execution_no_tiene_blocked(t):
    """EX-E32 — ni ESTADOS ni el status del resultado tienen BLOCKED, PENDING ni
    WAITING_FOR_HUMAN_APPROVAL; BLOCKED aparece solo en agentDeclaredStatus."""
    esquema = _esquema(SCHEMA_RESULT)
    ajenos = ("BLOCKED", "PENDING", "WAITING_FOR_HUMAN_APPROVAL")
    t.vacio("EX-E32 contrato.ESTADOS no tiene estados de la WorkUnit",
            [e for e in C.ESTADOS if e in ajenos])
    t.vacio("EX-E32 el status del resultado no los tiene",
            [e for e in esquema["properties"]["status"]["enum"] if e in ajenos])
    t.verdadero("EX-E32 BLOCKED esta en agentDeclaredStatus",
                "BLOCKED" in esquema["properties"]["agentDeclaredStatus"]["enum"])
    otros = dict(esquema["properties"], **{"$defs": esquema.get("$defs") or {}})
    t.vacio("EX-E32 BLOCKED no aparece en otro enum del resultado",
            [n for n, sub in otros.items() if n != "agentDeclaredStatus"
             and "BLOCKED" in _valores(sub, "enum")])


# =============================================================================================
# Evidencia y AgentReport
# =============================================================================================

def test_ex_e33_la_evidencia_dice_su_estado(t):
    """EX-E33 — con startedAt la evidencia no es nula; changes.state es uno de tres; un estado que
    no es RESOLVED va con files vacio; RESOLVED con files vacio pasa."""
    req = _request()
    estados = (_esquema(SCHEMA_RESULT)["properties"]["evidence"]["properties"]["changes"]
               ["properties"]["state"]["enum"])
    t.igual("EX-E33 los tres estados de los cambios",
            ["RESOLVED", "CHANGES_UNRESOLVED", "CHANGES_UNATTRIBUTABLE"], estados)
    _falla(t, "EX-E33", "con startedAt y evidence null",
           C.validar_resultado(_resultado(req, evidence=None), req), "$.evidence")
    for estado in ("CHANGES_UNRESOLVED", "CHANGES_UNATTRIBUTABLE"):
        con_archivos = copy.deepcopy(EVIDENCIA)
        con_archivos["changes"]["state"] = estado
        _falla(t, "EX-E33", "%s con archivos" % estado,
               C.validar_resultado(_resultado(req, evidence=con_archivos), req),
               "$.evidence.changes.files")
        vacia = {"repoRevisionBefore": None, "repoRevisionAfter": None,
                 "changes": {"state": estado, "files": []}}
        _pasa(t, "EX-E33", "%s sin archivos" % estado,
              C.validar_resultado(_resultado(req, evidence=vacia), req))
    nada = copy.deepcopy(EVIDENCIA)
    nada["changes"]["files"] = []
    _pasa(t, "EX-E33", "RESOLVED con files vacio: no cambio nada",
          C.validar_resultado(_resultado(req, evidence=nada), req))


def test_ex_e33b_una_sola_autoridad_para_el_tiempo(t):
    """EX-E33b — evidence es un objeto cerrado de repoRevisionBefore, repoRevisionAfter y
    changes, sin ningun campo de tiempo; los unicos tiempos del resultado estan en su raiz."""
    esquema = _esquema(SCHEMA_RESULT)
    evidencia = esquema["properties"]["evidence"]
    t.igual("EX-E33b evidence tiene exactamente tres propiedades",
            ["changes", "repoRevisionAfter", "repoRevisionBefore"], sorted(evidencia["properties"]))
    t.igual("EX-E33b evidence esta cerrada", False, evidencia.get("additionalProperties"))
    dentro = [n for _, n in _propiedades(evidencia)]
    t.vacio("EX-E33b ninguna propiedad de evidence es un tiempo",
            [n for n in dentro if n in ("startedAt", "endedAt") or "time" in n.lower() or "At" in n])
    req = _request()
    con_tiempo = copy.deepcopy(EVIDENCIA)
    con_tiempo["startedAt"] = "2026-10-20T14:00:05Z"
    _falla(t, "EX-E33b", "un startedAt adentro de evidence",
           C.validar_resultado(_resultado(req, evidence=con_tiempo), req), "$.evidence.startedAt")
    tiempos = sorted(n for _, n in _propiedades(esquema) if "time" in n.lower() or "At" in n)
    t.igual("EX-E33b los unicos campos de tiempo del resultado", ["endedAt", "startedAt"], tiempos)
    t.igual("EX-E33b y estan en su raiz", ["endedAt", "startedAt"],
            sorted(n for n in esquema["properties"] if n in tiempos))


def test_ex_e34_succeeded_lleva_evidencia(t):
    """EX-E34 — un SUCCEEDED con evidence null no pasa; un REJECTED sin evidencia si."""
    req = _request()
    _falla(t, "EX-E34", "un SUCCEEDED sin evidencia",
           C.validar_resultado(_resultado(req, evidence=None), req), "$.evidence")
    _pasa(t, "EX-E34", "un REJECTED sin evidencia", C.validar_resultado(_resultado(req, "REJECTED"), req))


def test_ex_e35_el_texto_del_agente_no_entra(t):
    """EX-E35 — output es {path, fingerprint} cerrado; ninguna propiedad se llama artifact,
    prompt, transcript, message, text o content; una ruta absoluta, con .. o con barras de Windows
    no pasa, en output ni en los archivos; una ruta repetida tampoco."""
    esquema = _esquema(SCHEMA_RESULT)
    salida = esquema["properties"]["output"]
    t.igual("EX-E35 output tiene path y fingerprint", ["fingerprint", "path"], sorted(salida["properties"]))
    t.igual("EX-E35 output esta cerrado", False, salida.get("additionalProperties"))
    prohibidos = {"artifact", "prompt", "transcript", "message", "text", "content"}
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        t.vacio("EX-E35 %s no tiene una propiedad de texto del agente" % ruta.name,
                sorted("%s.%s" % (d, n) for d, n in _propiedades(_esquema(ruta))
                       if n.lower() in prohibidos))
    req = _request()
    for mala in ("/etc/salida.md", "C:/salida.md", "a/../salida.md", ".claude\\salida.md", ""):
        _falla(t, "EX-E35", "output.path `%s`" % mala,
               C.validar_resultado(_resultado(req, output=dict(SALIDA, path=mala)), req), "$.output.path")
        archivos = copy.deepcopy(EVIDENCIA)
        archivos["changes"]["files"][0]["path"] = mala
        _falla(t, "EX-E35", "un archivo `%s`" % mala,
               C.validar_resultado(_resultado(req, evidence=archivos), req),
               "$.evidence.changes.files[0].path")
    repetidos = copy.deepcopy(EVIDENCIA)
    repetidos["changes"]["files"].append(dict(repetidos["changes"]["files"][0]))
    _falla(t, "EX-E35", "un archivo repetido",
           C.validar_resultado(_resultado(req, evidence=repetidos), req), "$.evidence.changes.files")


def _result_statuses_propios():
    """Los valores de las secciones "Result Statuses" de las skills que no son de los cuatro."""
    valores = set()
    for skill in sorted((RAIZ / "harnesses" / "desarrollo" / "skills").glob("*/SKILL.md")):
        texto = skill.read_text(encoding="utf-8")
        m = re.search(r"(?s)## Result Statuses\s*(.*?)\n## ", texto)
        if m:
            valores |= set(re.findall(r"`([A-Z_]+)`", m.group(1)))
    return sorted(valores - set(DECLARACIONES))


def test_ex_e36_el_contrato_del_agentreport(t):
    """EX-E36 — validar_informe acepta exactamente {declaredStatus, artifact} con uno de los
    cuatro y texto, vacio incluido; rechaza lo demas; agentDeclaredStatus son los cuatro y null;
    ningun valor propio de los "Result Statuses" aparece en los schemas ni en contrato.py."""
    t.igual("EX-E36 DECLARACIONES_DEL_AGENTE", DECLARACIONES, list(C.DECLARACIONES_DEL_AGENTE))
    for declarado in DECLARACIONES:
        for artifact in ("", "informe del agente"):
            _pasa(t, "EX-E36", "un AgentReport %s con artifact `%s`" % (declarado, artifact),
                  C.validar_informe({"declaredStatus": declarado, "artifact": artifact}))
    for rotulo, informe, campo in (
            ("sin declaredStatus", {"artifact": "x"}, "$.declaredStatus"),
            ("con DONE", {"declaredStatus": "DONE", "artifact": "x"}, "$.declaredStatus"),
            ("con complete en minusculas", {"declaredStatus": "complete", "artifact": "x"},
             "$.declaredStatus"),
            ("sin artifact", {"declaredStatus": "COMPLETE"}, "$.artifact"),
            ("con un artifact que no es texto", {"declaredStatus": "COMPLETE", "artifact": 5},
             "$.artifact"),
            ("con artifact null", {"declaredStatus": "COMPLETE", "artifact": None}, "$.artifact"),
            ("con una clave de mas", {"declaredStatus": "COMPLETE", "artifact": "", "agent": "dev-backend"},
             "$.agent")):
        _falla(t, "EX-E36", "un AgentReport %s" % rotulo, C.validar_informe(informe), campo)
    _falla(t, "EX-E36", "un AgentReport que no es un objeto", C.validar_informe("COMPLETE"), "$")
    t.igual("EX-E36 agentDeclaredStatus: los cuatro y null", DECLARACIONES + [None],
            _esquema(SCHEMA_RESULT)["properties"]["agentDeclaredStatus"]["enum"])
    propios = _result_statuses_propios()
    t.verdadero("EX-E36 hay Result Statuses propios para buscar", len(propios) > 5)
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT, CONTRATO):
        texto = ruta.read_text(encoding="utf-8")
        t.vacio("EX-E36 %s no nombra ningun Result Status propio de las skills" % ruta.name,
                [v for v in propios if re.search(r"\b%s\b" % v, texto)])


def test_ex_e36b_execution_no_interpreta_el_artifact(t):
    """EX-E36b — un AgentReport sin declaredStatus sigue invalido aunque el artifact diga
    `status: COMPLETE` o traiga un bloque agentResult; COMPLETE con un artifact que dice FAILED es
    valido; el artifact no cambia la validacion."""
    bloque = ("## Output\n\n```yaml\nagentResult:\n  agent: dev-backend\n  status: COMPLETE\n```\n")
    for rotulo, artifact in (("status: COMPLETE", "status: COMPLETE"), ("un bloque agentResult", bloque)):
        _falla(t, "EX-E36b", "sin declaredStatus y con un artifact que dice %s" % rotulo,
               C.validar_informe({"artifact": artifact}), "$.declaredStatus")
    _pasa(t, "EX-E36b", "COMPLETE con un artifact que dice FAILED",
          C.validar_informe({"declaredStatus": "COMPLETE", "artifact": "FAILED"}))
    for declarado in ("PARTIAL", "NO_VALE"):
        t.igual("EX-E36b el artifact no cambia la validacion de %s" % declarado,
                C.validar_informe({"declaredStatus": declarado, "artifact": "status: COMPLETE"}),
                C.validar_informe({"declaredStatus": declarado, "artifact": bloque + "\nFAILED"}))


# =============================================================================================
# Contabilidad
# =============================================================================================

def test_ex_e37_sin_consumo_ni_referencias_contables(t):
    """EX-E37 — ningun schema tiene una propiedad con usage, cost, token, eventId, ledger o
    accounting."""
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        t.vacio("EX-E37 %s no tiene consumo ni referencias contables" % ruta.name,
                _nombres_con(_esquema(ruta), ("usage", "cost", "token", "eventid", "ledger",
                                              "accounting")))


def test_ex_e38_ejecucion_no_lee_la_contabilidad(t):
    """EX-E38 — bin/ejecucion/ no importa contabilidad ni nombra .claude/runtime/accounting; E-40 y
    E-42 de 64 siguen en verde sin cambios."""
    t.verdadero("EX-E38 hay modulos en bin/ejecucion/", len(_py_de(EJECUCION)) >= 2)
    t.vacio("EX-E38 bin/ejecucion/ no importa contabilidad",
            [p.name for p in _py_de(EJECUCION) if "contabilidad" in _importados(p)])
    t.vacio("EX-E38 bin/ejecucion/ no nombra accounting",
            ["%s: %s" % (p.name, c) for p in _py_de(EJECUCION) for c in _constantes(p)
             if re.search(r"(^|[\\/])accounting([\\/]|$)", c) or c == "accounting"])
    if not _hay_base():
        _sin_base(t, "EX-E38")
        return
    _corre_de_64(t, "EX-E38", ("test_e40_nadie_emite_los_eventos_del_ciclo",
                               "test_e42_orquestacion_no_lee_la_contabilidad"))


# =============================================================================================
# Independencia del Host
# =============================================================================================

def test_ex_e39_nada_del_host_en_el_request(t):
    """EX-E39 — fuera de workUnit, ninguna propiedad del request tiene session, transcript, tool,
    provider, model o claude; ningun enum ni pattern de los dos schemas nombra a Claude Code."""
    t.vacio("EX-E39 el request no tiene nada del Host fuera de workUnit",
            _nombres_con(_esquema(SCHEMA_REQUEST), ("session", "transcript", "tool", "provider",
                                                    "model", "claude"), saltear=("$.workUnit",)))
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        esquema = _esquema(ruta)
        t.vacio("EX-E39 ningun enum ni pattern de %s nombra a Claude Code" % ruta.name,
                [v for v in _valores(esquema, "enum") + _valores(esquema, "pattern")
                 if isinstance(v, str) and "claude" in v.lower()])


def test_ex_e40_el_unico_bloque_del_host(t):
    """EX-E40 — el unico bloque del Host es result.host, nullable, con kind, sessionRef y runRef
    de texto sin enum; un resultado con host null pasa, y con otro host tambien."""
    esquema = _esquema(SCHEMA_RESULT)
    t.igual("EX-E40 la unica propiedad del Host es host", ["host"],
            [n for n in esquema["properties"] if "host" in n.lower()])
    host = esquema["properties"]["host"]
    t.verdadero("EX-E40 host puede ser null", "null" in host.get("type", []))
    t.igual("EX-E40 host tiene kind, sessionRef y runRef", ["kind", "runRef", "sessionRef"],
            sorted(host["properties"]))
    t.vacio("EX-E40 ninguno tiene enum", [n for n, s in host["properties"].items() if "enum" in s])
    req = _request()
    _pasa(t, "EX-E40", "un resultado con host null", C.validar_resultado(_resultado(req, host=None), req))
    _pasa(t, "EX-E40", "un resultado de otro host",
          C.validar_resultado(_resultado(req, host={"kind": "otro-host", "sessionRef": None,
                                                    "runRef": "corrida-7"}), req))


# =============================================================================================
# Compatibilidad
# =============================================================================================

def test_ex_e41_el_plan_2_1_no_cambia(t):
    """EX-E41 — orchestration-plan.schema.json y plan.py son los de fdca5ce, y E-13 a E-17 de 64
    siguen en verde sin cambios respecto de fdca5ce. Reemplazado por la integracion con 0.31.0:
    afirmaba lo mismo del plan 2.0 contra f9393cf, y el plan 2.1 lo cambio 0.31.0, no esta Task."""
    if not _hay_base(BASE_031):
        _sin_base(t, "EX-E41", BASE_031)
        return
    for ruta in ("comun/schemas/orchestration-plan.schema.json",
                 "harnesses/desarrollo/bin/orquestacion/plan.py"):
        t.verdadero("EX-E41 %s es el de %s" % (ruta, BASE_031), _igual_a_la_base(ruta, BASE_031))
    _corre_de_64(t, "EX-E41", ("test_e13_el_plan_es_orchestration_plan_2_1",
                               "test_e14_el_status_de_una_workunit",
                               "test_e15_ningun_documento_escrito_tiene_un_estado_que_salio",
                               "test_e16_un_1_0_de_4c6f0f3_se_acepta_y_se_migra_al_escribirlo",
                               "test_e16b_un_1_0_con_un_estado_que_salio_se_rechaza",
                               "test_e16c_otra_version_o_ninguna_se_rechaza",
                               "test_e17_el_productor_escribe_lo_mismo_que_4c6f0f3"), BASE_031)


def test_ex_e42_los_contratos_que_la_ejecucion_va_a_alimentar(t):
    """EX-E42 — los schemas de contabilidad, del ledger de seguridad y de la RefutationUnit son
    los de f9393cf."""
    if not _hay_base():
        _sin_base(t, "EX-E42")
        return
    for nombre in ("execution-accounting-event", "security-ledger-event", "refutation-unit"):
        ruta = "comun/schemas/%s.schema.json" % nombre
        t.verdadero("EX-E42 %s es el de %s" % (ruta, BASE), _igual_a_la_base(ruta))


def test_ex_e43_la_workunit_la_valida_el_schema_del_plan(t):
    """EX-E43 — validar_request valida workUnit contra workUnits.items del plan: sin modelPolicy no
    pasa aunque el request no la pida; el request declara en workUnit exactamente seis campos."""
    unidad = _esquema(SCHEMA_REQUEST)["properties"]["workUnit"]
    seis = ["assignedAgent", "dependencies", "domain", "id", "requiredCapabilities", "status"]
    t.igual("EX-E43 el request restringe exactamente seis campos de la WorkUnit", seis,
            sorted(unidad["properties"]))
    t.igual("EX-E43 y pide esos seis", seis, sorted(unidad["required"]))
    t.verdadero("EX-E43 el request no pide modelPolicy", "modelPolicy" not in unidad["properties"])
    req = _request()
    sin = _con(req, ["workUnit", "modelPolicy"], "-", firmar=True)
    t.igual("EX-E43 sin modelPolicy, el schema del request solo no se queja", [],
            ARMADOR.validar(sin, _esquema(SCHEMA_REQUEST)))
    _falla(t, "EX-E43", "una WorkUnit sin modelPolicy", C.validar_request(sin), "$.workUnit.modelPolicy")


# =============================================================================================
# El modelo canonico y el ADR
# =============================================================================================

def test_ex_e44_execution_es_el_decimo_contexto(t):
    """EX-E44 — el documento declara diez contextos, Execution entre ellos, y ya no dice que es un
    limite reservado; los ocho conceptos de 8.2 tienen fila y bloque, con los diez campos,
    Contexto Execution y su clasificacion."""
    m = M64._modelo()
    mapa = M64._tablas(M64._seccion(m["texto"], "Mapa de contextos"))
    contextos = [f[0] for f in mapa[0][1:]] if mapa else []
    t.igual("EX-E44 el mapa declara diez contextos", sorted(M64.NUEVE + ["Execution"]), sorted(contextos))
    t.no_contiene("EX-E44 el documento ya no dice que Execution es un limite reservado",
                  "Execution no es un contexto: es un límite reservado", m["texto"])
    esperados = _tabla_8_2()
    t.igual("EX-E44 la spec trae los ocho conceptos",
            ["AgentReport", "Execution", "ExecutionAdmission", "ExecutionError", "ExecutionEvidence",
             "ExecutionId", "ExecutionRequest", "ExecutionResult"], sorted(esperados))
    filas = {f[0]: f for f in m["filas"] if len(f) >= 3}
    for concepto, (contexto, clasificacion) in sorted(esperados.items()):
        t.verdadero("EX-E44 %s esta en la tabla" % concepto, concepto in filas)
        t.igual("EX-E44 %s: tabla, contexto y clasificacion" % concepto, [contexto, clasificacion],
                (filas.get(concepto) or [None, None, None])[1:3])
        campos = m["lista_campos"].get(concepto) or []
        t.igual("EX-E44 %s tiene los diez campos en orden" % concepto, list(M64.CAMPOS),
                [r for r, _ in campos])
        valores = dict(campos)
        t.igual("EX-E44 %s: Contexto Execution" % concepto, "Execution",
                M64._valor(valores.get("Contexto")))
        t.igual("EX-E44 %s: Clasificación" % concepto, clasificacion,
                M64._valor(valores.get("Clasificación")))
        t.verdadero("EX-E44 %s: una de las doce" % concepto, clasificacion in M64.DOCE)


def test_ex_e45_los_schemas_nuevos_en_su_concepto(t):
    """EX-E45 — execution-request en ExecutionRequest, execution-result en ExecutionResult, y el
    documento nombra los 55 schemas. Pisado por la integracion con 0.31.0: eran 48, y Flow
    Governance trajo seis (D7 de docs/cambios/integracion-flow-governance-0-31/spec.md). Pisado
    por Task 5 / GD-23: el del GraphRun, graph-run-result.schema.json, hace 55."""
    m = M64._modelo()
    for concepto, schema in (("ExecutionRequest", "execution-request.schema.json"),
                             ("ExecutionResult", "execution-result.schema.json")):
        t.contiene("EX-E45 %s nombra %s en Persistencia y contrato" % (concepto, schema), schema,
                   (m["campos"].get(concepto) or {}).get("Persistencia y contrato"))
    en_disco = sorted(p.name for p in SCHEMAS.iterdir() if p.is_file())
    # Task 5 / GD-23: graph-run-result.schema.json entra a comun/schemas/ a proposito (docs/cambios/
    # graph-execution/spec.md, GD-23 y 27.1 A): de 54 a 55.
    t.igual("EX-E45 son 55 schemas", 55, len(en_disco))
    nombrados = set()
    for campos in m["campos"].values():
        nombrados |= set(M64.SCHEMA_NOMBRADO.findall(campos.get("Persistencia y contrato") or ""))
    t.vacio("EX-E45 cada schema figura en Persistencia y contrato de algun concepto",
            [s for s in en_disco if s not in nombrados])


def test_ex_e46_las_seis_desigualdades_nuevas(t):
    """EX-E46 — Lo que no es lo mismo tiene las seis de 26.1 y conserva las catorce de Task 2."""
    nuevas = _desigualdades_nuevas()
    t.igual("EX-E46 la spec trae seis desigualdades nuevas", 6, len(nuevas))
    titulos = [a for a, _ in M64._apartados(M64._seccion(M64._modelo()["texto"], "Lo que no es lo mismo"))]
    t.vacio("EX-E46 cada una tiene su apartado", [d for d in nuevas if d not in titulos])
    viejas = M64._desigualdades_de_la_spec()
    t.igual("EX-E46 las de Task 2 son catorce", 14, len(viejas))
    t.vacio("EX-E46 y se conservan", [d for d in viejas if d not in titulos])
    t.igual("EX-E46 no hay otras", sorted(viejas + nuevas), sorted(titulos))


# Pisado por docs/cambios/minimal-execution-engine/spec.md (§24, §26.2): ADR-0015 hizo existir el
# motor, la admision, el almacenamiento y el Host Adapter. Siguen sin existir el reintento y el
# scheduler. "sin productor" sigue: es lo que dejo ADR-0014.
LIMITE_EXISTE = ("ExecutionRequest", "execution-request.schema.json", "execution-result.schema.json",
                 "contrato.py", "sin productor", "motor", "admisión", "almacenamiento", "Host Adapter")
LIMITE_NO_EXISTE = ("reintento", "scheduler")


def test_ex_e47_el_limite_de_la_ejecucion(t):
    """EX-E47 — El límite de la ejecución dice que existe el contrato sin productor, que no existen
    el motor, la admision implementada, el almacenamiento, el reintento ni el scheduler, y que
    siguen los dos invariantes de ADR-0013 §4."""
    partes = dict(M64._apartados(M64._seccion(M64._modelo()["texto"], "El límite de la ejecución")))
    existe = " ".join(partes.get("Lo que existe ahora") or [])
    no_existe = " ".join(partes.get("Lo que todavía no existe") or [])
    intacto = " ".join(partes.get("Lo que sigue intacto") or [])
    for ancla in LIMITE_EXISTE:
        t.contiene("EX-E47 lo que existe nombra %s" % ancla, ancla, existe)
    for ancla in LIMITE_NO_EXISTE:
        t.contiene("EX-E47 lo que todavía no existe nombra %s" % ancla, ancla, no_existe)
    for frase in ("La contabilidad no es estado de ejecución",
                  "El estado del Plan se deriva del contenido del Plan"):
        t.contiene("EX-E47 sigue intacto: %s" % frase, frase, intacto)


ANCLAS_ADR = (("contexto", "Execution"), ("WorkUnit", "intento"),
              ("READY_FOR_EXECUTION", "PENDING", "admisión"), ("estados", "BLOCKED"),
              ("AgentReport", "Host Adapter"), ("Plan", "contabilidad"),
              ("orchestration-plan/2.0", "huella"))


def test_ex_e48_el_adr_0014(t):
    """EX-E48 — ADR-0014 existe, aceptado, con siete decisiones numeradas que nombran lo de 26.2,
    y dice que revisa el punto 4 de ADR-0013 sin tocar sus dos invariantes."""
    t.verdadero("EX-E48 existe el ADR", ADR.is_file())
    texto = M64._texto(ADR) if ADR.is_file() else ""
    frente = re.match(r"^---\n(.*?)\n---\n", texto.replace("\r\n", "\n"), re.S)
    t.verdadero("EX-E48 estado: aceptada", frente and re.search(r"(?m)^estado:\s*aceptada\s*$",
                                                               frente.group(1)))
    decisiones = _decisiones_del_adr()
    t.igual("EX-E48 siete decisiones, de la 1 a la 7", [str(i) for i in range(1, 8)],
            [n for n, _ in decisiones])
    bloques = re.split(r"(?m)^### \d+\. ", texto)[1:]
    for i, anclas in enumerate(ANCLAS_ADR):
        cuerpo = bloques[i] if i < len(bloques) else ""
        for ancla in anclas:
            t.contiene("EX-E48 la decision %d nombra %s" % (i + 1, ancla), ancla, cuerpo)
    for frase in ("ADR-0013", "punto 4", "La contabilidad no es estado de ejecución",
                  "El estado del Plan se deriva del contenido del Plan"):
        t.contiene("EX-E48 el ADR nombra: %s" % frase, frase, texto)


# =============================================================================================
# Fuera de alcance
# =============================================================================================

PROHIBIDOS = ("threading", "multiprocessing", "asyncio", "concurrent", "sched", "queue")
MODELOS = ("anthropic", "openai", "langchain", "langgraph", "claude_agent_sdk")


def _subcomandos(texto):
    for n in ast.walk(ast.parse(texto)):
        if (isinstance(n, ast.Call) and _nombre(n.func).endswith("add_argument") and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == "comando"):
            for k in n.keywords:
                if k.arg == "choices":
                    return list(ast.literal_eval(k.value))
    return None


def test_ex_e49_no_hay_motor(t):
    """EX-E49 — dev-harness.py sigue con los doce subcomandos de 0.31.0, sin ejecutar, run ni
    execute; nada de bin/ ni comun/ importa threading, multiprocessing, asyncio, concurrent, sched
    ni queue. Pisado por la integracion con 0.31.0: eran los once de 0.30.0, y Flow Governance sumo
    `flujo`. Pisado por docs/cambios/minimal-execution-engine/spec.md (§26.2, MD-01): son trece, los
    de 0.31.0 y `ejecutar`, que corre una WorkUnit por invocacion; sigue sin `run` ni `execute`, y
    sin concurrencia (ME-E47)."""
    ahora = _subcomandos((BIN / "dev-harness.py").read_text(encoding="utf-8"))
    t.igual("EX-E49 son trece subcomandos", 13, len(ahora or []))
    t.vacio("EX-E49 ninguno se llama run ni execute",
            [c for c in ahora or [] if c in ("run", "execute")])
    if _hay_base(BASE_031):
        codigo, crudo = M64._git("show", "%s:harnesses/desarrollo/bin/dev-harness.py" % BASE_031)
        t.igual("EX-E49 son los de %s mas ejecutar" % BASE_031,
                (_subcomandos(crudo.decode("utf-8")) or []) + ["ejecutar"] if codigo == 0 else None,
                ahora)
    else:
        _sin_base(t, "EX-E49", BASE_031)
    t.vacio("EX-E49 nada de bin/ ni comun/ importa concurrencia",
            ["%s: %s" % (p.relative_to(RAIZ).as_posix(), m) for p in _py_de(BIN) + _py_de(RAIZ / "comun")
             for m in sorted(_importados(p) & set(PROHIBIDOS))])


def test_ex_e50_no_hay_reintento(t):
    """EX-E50 — los schemas no tienen propiedades de reintento, y bin/ejecucion/ no nombra
    maxRetries, allowEscalation, retryPolicy ni timeoutSeconds."""
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        t.vacio("EX-E50 %s no tiene reintentos" % ruta.name,
                _nombres_con(_esquema(ruta), ("retry", "attempt", "backoff")))
    for p in _py_de(EJECUCION):
        texto = p.read_text(encoding="utf-8")
        t.vacio("EX-E50 %s no nombra los campos de reintento" % p.name,
                [c for c in ("maxRetries", "allowEscalation", "retryPolicy", "timeoutSeconds")
                 if c in texto])


def test_ex_e51_no_hay_llamadas_a_modelos(t):
    """EX-E51 — nada de bin/ ni comun/ importa un SDK de modelos, y E-41 sigue en verde. Pisado por
    la integracion con 0.31.0: E-41 se compara con fdca5ce, que suma `taskkill` desde
    flujo/repositorio.py. Pisado por docs/cambios/minimal-execution-engine/spec.md (§26.2): E-41 es
    el de Task 4, que suma el Host desde ejecucion/proceso.py, por pedido de host_claude_code.py, y
    `taskkill` desde ahi. Se corre el de ahora, y se mira que sea ese."""
    t.vacio("EX-E51 nada de bin/ ni comun/ importa un SDK de modelos",
            ["%s: %s" % (p.relative_to(RAIZ).as_posix(), m) for p in _py_de(BIN) + _py_de(RAIZ / "comun")
             for m in sorted(_importados(p) & set(MODELOS))])
    funcion = "test_e41_todo_subprocess_lanza_git_o_markitdown"
    fuente = _fuente_de((RAIZ / CASO_64).read_text(encoding="utf-8"), funcion) or ""
    t.contiene("EX-E51 E-41 es el de Task 4: mira quien lanza el Host", "LANZA_EL_HOST", fuente)
    t.igual("EX-E51 y el Host lo lanza solo host_claude_code.py",
            "harnesses/desarrollo/bin/ejecucion/host_claude_code.py", getattr(M64, "LANZA_EL_HOST", None))
    r = CORRER.Resultados()
    try:
        getattr(M64, funcion)(r)
        caidas = []
    except Exception as e:                # noqa: BLE001 - el motivo es el detalle
        caidas = ["%s: %s" % (type(e).__name__, e)]
    t.verdadero("EX-E51 %s tiene aserciones" % funcion, len(r.filas) > 0)
    t.vacio("EX-E51 %s sigue en verde" % funcion,
            caidas + ["%s %s" % (n, d) for _, n, ok, d in r.filas if not ok])


ESCRITURAS = ("os.replace", "os.rename", "os.makedirs", "os.mkdir", "os.remove", "os.unlink",
              "os.rmdir", "os.system")


def _escrituras(ruta):
    salida = []
    for n in ast.walk(_arbol(ruta)):
        if not isinstance(n, ast.Call):
            continue
        nombre = _nombre(n.func)
        if nombre in ESCRITURAS or nombre.startswith("shutil.") or nombre.split(".")[-1] in (
                "write", "write_text", "write_bytes", "writelines", "dump", "mkdir", "touch"):
            salida.append("%s:%d %s" % (ruta.name, n.lineno, nombre))
        if nombre.split(".")[-1] == "open":
            modo = n.args[1] if len(n.args) > 1 else next(
                (k.value for k in n.keywords if k.arg == "mode"), None)
            if modo is not None and not (isinstance(modo, ast.Constant) and set(str(modo.value)) <= set("rbt")):
                salida.append("%s:%d open para escribir" % (ruta.name, n.lineno))
    return salida


def test_ex_e52_no_hay_ejecucion_persistida(t):
    """EX-E52 — contrato.py no escribe ni lanza procesos; nada de bin/ ni comun/ nombra
    .claude/ejecuciones; ningun modulo de produccion importa ejecucion. Pisado por
    docs/cambios/minimal-execution-engine/spec.md (§26.2, MD-03): contrato.py sigue sin escribir, sin
    lanzar y sin importar la refutacion ni la contabilidad (ME-E46); los demas modulos de
    bin/ejecucion/ escriben, solo bajo .claude/ejecuciones/, y fuera de bin/ejecucion/ nadie lo
    nombra; de produccion, solo dev-harness.py importa ejecucion, y es ejecucion.motor."""
    t.vacio("EX-E52 contrato.py no escribe", _escrituras(CONTRATO))
    t.vacio("EX-E52 contrato.py no lanza procesos ni importa la refutacion ni la contabilidad",
            sorted(_importados(CONTRATO) & {"subprocess", "refutacion", "contabilidad"}))
    from ejecucion import registro as registro_de_ejecuciones
    t.igual("EX-E52 el registro de bin/ejecucion/ vive bajo .claude/ejecuciones",
            (".claude", "ejecuciones"), registro_de_ejecuciones.RAIZ)
    t.vacio("EX-E52 fuera de bin/ejecucion/ nada nombra .claude/ejecuciones",
            ["%s: %s" % (p.relative_to(RAIZ).as_posix(), c) for p in _de_produccion()
             for c in _constantes(p) if c == "ejecuciones" or re.search(r"\.claude[\\/]ejecuciones", c)])
    t.igual("EX-E52 de produccion, solo dev-harness.py importa ejecucion",
            ["harnesses/desarrollo/bin/dev-harness.py"],
            [p.relative_to(RAIZ).as_posix() for p in _de_produccion() if "ejecucion" in _importados(p)])
    t.verdadero("EX-E52 y lo que importa es ejecucion.motor",
                any(isinstance(n, ast.ImportFrom) and n.module == "ejecucion"
                    and [a.name for a in n.names] == ["motor"]
                    for n in ast.walk(_arbol(BIN / "dev-harness.py"))))


# =============================================================================================
# Pendientes
# =============================================================================================

TITULOS = ("An executing agent cannot reach the integration capabilities the plan counts as available",
           "The agent registry gives two answers for the same orphan agent",
           "A plan accepts an agent from another domain without a word",
           "Agent prompts describe a result flow and an existence check that belong to someone else",
           "Two texts still say the disk decides whether an agent exists")


def test_ex_e54_los_cinco_pendientes(t):
    """EX-E54 — PENDIENTES-FH.md tiene los cinco titulos de 33, como entradas ###."""
    encabezados = [l[4:].strip() for l in M64._texto(PENDIENTES).splitlines() if l.startswith("### ")]
    for titulo in TITULOS:
        t.verdadero("EX-E54 PENDIENTES-FH.md tiene: %s" % titulo, titulo in encabezados)
    t.vacio("EX-E54 la spec trae los mismos cinco",
            [x for x in TITULOS if x not in M64._texto(SPEC)])


# =============================================================================================
# La integracion con HARNESS 0.31.0 (seccion 37 de la spec)
# =============================================================================================
#
# Los EX-Gnn son de la integracion con 0.31.0 (fdca5ce): Flow Governance y orchestration-plan/2.1.
# Los que miran el flujo de verdad corren `plan --propuesta` y leen el TaskFlowState con
# flujo/estado.py, que es de Planning: Execution no lo importa (EX-G06), el test si.

HOOKS = RAIZ / "comun" / "hooks"
ADR_0013 = RAIZ / "docs" / "adr" / "0013-modelo-de-dominio-canonico.md"
IDEAS = RAIZ / "Pendientes" / "Ideas-Harness" / "PENDIENTES-I.md"
SECCION_37 = "37. Integración con HARNESS 0.31.0"


def _flujo():
    from flujo import estado
    return estado


def _hooks_lib(nombre):
    if str(HOOKS) not in sys.path:
        sys.path.insert(0, str(HOOKS))
    return importlib.import_module("lib." + nombre)


def _con_contexto_cambiado(proy):
    """El TaskContext de la tarea cambia despues de planificar, con su hash de verdad."""
    ruta = proy / ".claude" / "contextos" / (CLAVE + ".json")
    contexto = json.loads(ruta.read_text(encoding="utf-8"))
    contexto["task"]["title"] = "Otro titulo, despues de planificar"
    contexto["meta"]["context_hash"] = ARMADOR.hash_de(contexto)
    ruta.write_text(json.dumps(contexto), encoding="utf-8")


def test_ex_g01_un_plan_2_1_listo_y_una_unidad_pending(t):
    """EX-G01 — el request armado desde un plan 2.1 READY_FOR_EXECUTION real, con su WorkUnit
    PENDING, valida y dice orchestration-plan/2.1; con 2.0 o 1.0 en plan.schemaVersion no valida."""
    plan = _plan()
    t.igual("EX-G01 plan --propuesta escribe orchestration-plan/2.1", "orchestration-plan/2.1",
            plan["meta"]["schema_version"])
    req = _request()
    t.igual("EX-G01 la unidad del request esta PENDING", "PENDING", req["workUnit"]["status"])
    t.igual("EX-G01 el request dice orchestration-plan/2.1", "orchestration-plan/2.1",
            req["plan"]["schemaVersion"])
    _pasa(t, "EX-G01", "el request de un plan 2.1 listo", C.validar_request(req))
    t.igual("EX-G01 plan.schemaVersion admite solo 2.1", ["orchestration-plan/2.1"],
            _esquema(SCHEMA_REQUEST)["properties"]["plan"]["properties"]["schemaVersion"]["enum"])
    for version in ("orchestration-plan/2.0", "orchestration-plan/1.0"):
        _falla(t, "EX-G01", "con plan.schemaVersion %s" % version,
               C.validar_request(_con(req, ["plan", "schemaVersion"], version)), "$.plan.schemaVersion")


def test_ex_g02_un_plan_o_una_unidad_bloqueados_no_se_admiten(t):
    """EX-G02 — con un agente que el registro no rutea, plan --propuesta escribe un plan BLOCKED y
    la unidad BLOCKED con el blocker agents.routing; ni ese planStatus ni el snapshot de esa unidad
    validan en un request."""
    proy = _proyecto_listo([M64._propuesta([M64._unidad("analizar-api", assignedAgent="dev-inexistente")])])
    plan = _plan_escrito(proy, 1)
    unidad = _unidad_del(plan, "analizar-api")
    t.igual("EX-G02 el plan queda BLOCKED", "BLOCKED", plan["status"])
    t.igual("EX-G02 la unidad queda BLOCKED", "BLOCKED", unidad["status"])
    t.igual("EX-G02 con el blocker de ruteo", ["agents.routing"],
            [b.get("inputId") for b in unidad.get("blockers") or []])
    req = _request("analizar-api", _plan())
    _falla(t, "EX-G02", "con planStatus BLOCKED",
           C.validar_request(_con(req, ["admission", "planStatus"], "BLOCKED")), "$.admission.planStatus")
    bloqueada = _con(req, ["workUnit"], unidad, firmar=True)
    errores = C.validar_request(bloqueada)
    _falla(t, "EX-G02", "con la unidad BLOCKED del plan", errores, "$.workUnit.status")
    t.verdadero("EX-G02 y el error nombra sus blockers", _nombra(errores, "$.workUnit.blockers"))


def test_ex_g03_los_blockers_viajan_solo_en_el_snapshot(t):
    """EX-G03 — ni la raiz, ni admission, ni las seis propiedades que el request declara de workUnit
    tienen blockers; una WorkUnit PENDING con blockers, vacios o no, no pasa, y sin ellos si."""
    esquema = _esquema(SCHEMA_REQUEST)
    t.vacio("EX-G03 el request no declara blockers en ningun lado",
            [r for r in ("%s.%s" % (d, n) for d, n in _propiedades(esquema)) if "blocker" in r.lower()])
    req = _request()
    t.verdadero("EX-G03 la unidad admitida no trae blockers", "blockers" not in req["workUnit"])
    _pasa(t, "EX-G03", "una WorkUnit PENDING sin blockers", C.validar_request(req))
    for rotulo, valor in (("vacios", []),
                          ("con uno", [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND"}])):
        _falla(t, "EX-G03", "una WorkUnit PENDING con blockers %s" % rotulo,
               C.validar_request(_con(req, ["workUnit", "blockers"], valor, firmar=True)),
               "$.workUnit.blockers")


def test_ex_g04_el_dato_del_flujo(t):
    """EX-G04 — admission.flow es obligatorio y su unico valor es DELEGATION_ALLOWED: sin el, o con
    otro valor, el request no valida."""
    admision = _esquema(SCHEMA_REQUEST)["properties"]["admission"]
    t.verdadero("EX-G04 admission.flow es obligatorio", "flow" in admision["required"])
    t.igual("EX-G04 su unico valor es DELEGATION_ALLOWED", ["DELEGATION_ALLOWED"],
            admision["properties"]["flow"]["enum"])
    req = _request()
    _falla(t, "EX-G04", "sin admission.flow", C.validar_request(_con(req, ["admission", "flow"], "-")),
           "$.admission.flow")
    for valor in ("BLOCKED", "WAITING_FOR_HUMAN_APPROVAL", "CANCELLED", "EXECUTION", "ALLOWED", True):
        _falla(t, "EX-G04", "con admission.flow %r" % (valor,),
               C.validar_request(_con(req, ["admission", "flow"], valor)), "$.admission.flow")


def test_ex_g05_el_flujo_frena_una_tarea_con_el_plan_listo(t):
    """EX-G05 — con el plan READY_FOR_EXECUTION por los dos lados, el TaskFlowState da
    delegationAllowed en EXECUTION; si el TaskContext cambia despues de planificar, el plan sigue
    READY por los dos lados y el flujo queda BLOCKED con CONTEXT_STALE, sin delegationAllowed."""
    from orquestacion import plan as orq_plan
    estado = _flujo()
    proy = _proyecto_listo([M64._propuesta(UNIDADES)])
    plan = _plan_escrito(proy, 1)
    antes = estado.derivar(str(proy), CLAVE)
    t.igual("EX-G05 con el contexto intacto, la tarea esta en EXECUTION", "EXECUTION", antes["stage"])
    t.verdadero("EX-G05 y puede delegar", estado.permisos(antes)["delegationAllowed"])
    _con_contexto_cambiado(proy)
    despues = estado.derivar(str(proy), CLAVE)
    plan_ahora = M64._leer_json(M64._plan_de(proy, CLAVE))
    t.igual("EX-G05 el plan no cambio", C.huella(plan), C.huella(plan_ahora))
    t.igual("EX-G05 el plan sigue READY por los dos lados",
            ["READY_FOR_EXECUTION", "READY_FOR_EXECUTION"],
            [plan_ahora["status"], orq_plan.estado_de(plan_ahora)])
    t.igual("EX-G05 el flujo queda BLOCKED", "BLOCKED", despues["status"])
    t.verdadero("EX-G05 por CONTEXT_STALE",
                "CONTEXT_STALE" in [b["code"] for b in despues["blockedOn"]])
    t.verdadero("EX-G05 y ya no puede delegar", not estado.permisos(despues)["delegationAllowed"])


def _codigos_de(ruta):
    """Los textos en mayusculas asignados a un nombre de modulo: los codigos que define un modulo."""
    salida = set()
    for n in _arbol(ruta).body:
        if (isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str) and re.match(r"^[A-Z][A-Z0-9_]+$", n.value.value)):
            salida.add(n.value.value)
    return salida


MODULOS_DEL_FLUJO = ("flow_gate", "tool_policy", "task_binding", "human_intent", "flow_context",
                     "flujo", "estado_de_tarea")


def _del_flujo(ruta):
    """[(modulo, nombre)] de lo que un fuente importa del paquete flujo."""
    salida = []
    for n in ast.walk(_arbol(ruta)):
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "flujo":
            salida += [(n.module, a.name) for a in n.names]
        if isinstance(n, ast.Import):
            salida += [(a.name, None) for a in n.names if a.name.split(".")[0] == "flujo"]
    return salida


def test_ex_g06_la_compuerta_del_flujo_no_es_la_admision(t):
    """EX-G06 — con la tarea vigente, la compuerta del flujo de PreToolUse deja pasar Agent; con la
    tarea frenada lo niega con un codigo FLOW_. Ninguno de sus codigos, ni los de task_binding,
    human_intent o tool_policy, esta entre los 23 de Execution, ninguno de los 23 empieza con FLOW_,
    y bin/ejecucion/ no importa ni un hook ni el flujo."""
    from estado_de_tarea import persistencia
    compuerta = _hooks_lib("flow_gate")
    proy = _proyecto_listo([M64._propuesta(UNIDADES)])
    _plan_escrito(proy, 1)
    evento = {"tool_name": "Agent", "tool_input": {"prompt": "hacer analizar-api",
                                                   "subagent_type": "dev-backend"},
              "cwd": str(proy), "session_id": "sesion-ex-g06"}
    t.igual("EX-G06 con la tarea vigente, la compuerta deja pasar Agent", "allow",
            compuerta.decidir(evento)["decision"])
    _con_contexto_cambiado(proy)
    persistencia.reconciliar(str(proy), CLAVE)
    negada = compuerta.decidir(evento)
    t.igual("EX-G06 con la tarea frenada, lo niega", "deny", negada["decision"])
    t.verdadero("EX-G06 con un codigo de la compuerta del flujo", str(negada["code"]).startswith("FLOW_"))
    ajenos = set()
    for nombre in ("flow_gate", "tool_policy", "task_binding", "human_intent"):
        ajenos |= _codigos_de(HOOKS / "lib" / (nombre + ".py"))
    t.verdadero("EX-G06 se leyeron los codigos de los hooks", "FLOW_HARD_BLOCKER" in ajenos
                and "SESSION_TASK_AMBIGUOUS" in ajenos and "HUMAN_INTENT_REQUIRED" in ajenos)
    t.vacio("EX-G06 ningun codigo de Execution es de la compuerta, del vinculo ni de la intencion",
            sorted(set(C.CODIGOS) & ajenos))
    t.vacio("EX-G06 ninguno de los 23 empieza con FLOW_", [c for c in C.CODIGOS if c.startswith("FLOW_")])
    # Pisado por docs/cambios/minimal-execution-engine/spec.md (MD-12, §26.2): la admision lee el
    # TaskFlowState guardado con flujo/estado.py (leer, vigencia_local y permisos), y no lo escribe.
    # Ese es el unico import del flujo, y solo desde admision.py; un hook o estado_de_tarea, ninguno.
    t.vacio("EX-G06 bin/ejecucion/ no importa un hook ni el flujo, salvo flujo/estado.py en "
            "admision.py",
            ["%s: %s" % (p.name, m) for p in _py_de(EJECUCION)
             for m in sorted(_importados(p) & set(MODULOS_DEL_FLUJO + ("lib",)))
             if not (p.name == "admision.py" and m == "flujo"
                     and _del_flujo(p) == [("flujo", "estado")])])
    t.vacio("EX-G06 bin/ejecucion/ no lee el estado del flujo",
            ["%s: %s" % (p.name, c) for p in _py_de(EJECUCION) for c in _constantes(p)
             if re.search(r"runtime[\\/]tasks|state\.json|task\.json|human-intent\.json", c)])


def test_ex_g07_delegation_not_allowed(t):
    """EX-G07 — DELEGATION_NOT_ALLOWED es el sexto de los 23 y va entre PLAN_NOT_READY y
    WORK_UNIT_NOT_FOUND en una precedencia de quince; va al pedir y en REJECTED, nunca en FAILED ni
    en CANCELLED; NORMATIVE_GATE_BLOCKED sigue siendo otro codigo, de la compuerta normativa."""
    codigo = "DELEGATION_NOT_ALLOWED"
    t.igual("EX-G07 es el sexto de los 23", (5, 23), (list(C.CODIGOS).index(codigo), len(C.CODIGOS)))
    t.igual("EX-G07 la precedencia tiene quince", 15, len(C.PRECEDENCIA))
    i = list(C.PRECEDENCIA).index(codigo)
    t.igual("EX-G07 despues de PLAN_NOT_READY y antes de WORK_UNIT_NOT_FOUND",
            ["PLAN_NOT_READY", codigo, "WORK_UNIT_NOT_FOUND"], list(C.PRECEDENCIA[i - 1:i + 2]))
    t.igual("EX-G07 va al pedir y en REJECTED", (C.AL_PEDIR, "REJECTED"), C.CODIGOS[codigo])
    _pasa(t, "EX-G07", "un rechazo al pedir con %s" % codigo, C.validar_rechazo(_error(codigo)))
    req = _request()
    _pasa(t, "EX-G07", "un REJECTED con %s" % codigo,
          C.validar_resultado(_resultado(req, "REJECTED", error=_error(codigo)), req))
    _falla(t, "EX-G07", "un FAILED con %s" % codigo,
           C.validar_resultado(_resultado(req, "FAILED", error=_error(codigo),
                                          agentDeclaredStatus=None, output=None), req), "$.error.code")
    _falla(t, "EX-G07", "un CANCELLED con %s" % codigo,
           C.validar_resultado(_resultado(req, "CANCELLED", error=_error(codigo)), req), "$.error.code")
    t.verdadero("EX-G07 NORMATIVE_GATE_BLOCKED sigue, y es otro codigo",
                "NORMATIVE_GATE_BLOCKED" in C.CODIGOS and codigo != "NORMATIVE_GATE_BLOCKED")


def test_ex_g08_la_huella_del_plan_2_1(t):
    """EX-G08 — planFingerprint es la huella que el TaskFlowState guarda en planRef.planFingerprint
    para ese plan, y cambia si cambia un dato de 2.1: flowPreconditions, capabilityStatus,
    knowledgeSources o los blockers de una unidad. Con ella cambia la idempotencyKey."""
    estado = _flujo()
    proy = _proyecto_listo([M64._propuesta(UNIDADES)])
    plan = _plan_escrito(proy, 1)
    req = _request(plan=plan)
    t.igual("EX-G08 es la huella que guarda el TaskFlowState", req["plan"]["planFingerprint"],
            estado.derivar(str(proy), CLAVE)["planRef"]["planFingerprint"])
    for campo in ("flowPreconditions", "capabilityStatus", "knowledgeSources"):
        t.verdadero("EX-G08 el plan 2.1 trae %s" % campo, campo in plan)
        otro = copy.deepcopy(plan)
        otro[campo] = {"cambiado": True}
        t.verdadero("EX-G08 cambiar %s cambia la huella" % campo, C.huella(otro) != C.huella(plan))
    otro = copy.deepcopy(plan)
    otro["workUnits"][0]["blockers"] = [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND"}]
    t.verdadero("EX-G08 sumar blockers a una unidad cambia la huella", C.huella(otro) != C.huella(plan))
    t.verdadero("EX-G08 y con otra huella, otra idempotencyKey",
                C.clave_de_idempotencia(CLAVE, C.huella(otro), "implementar-endpoint")
                != req["idempotencyKey"])


def test_ex_g09_el_vinculo_de_sesion_no_es_identidad(t):
    """EX-G09 — la idempotencyKey sale de taskKey, planFingerprint y workUnit.id, y de nada mas;
    ninguna propiedad del request nombra una sesion o un vinculo, y en el resultado la unica es
    host.sessionRef, que no es identidad."""
    t.igual("EX-G09 clave_de_idempotencia toma tres datos, ninguno del flujo",
            ["task_key", "plan_fingerprint", "work_unit_id"],
            list(inspect.signature(C.clave_de_idempotencia).parameters))
    t.vacio("EX-G09 el request no nombra una sesion ni un vinculo",
            _nombres_con(_esquema(SCHEMA_REQUEST), ("session", "binding", "sesion", "vinculo")))
    t.igual("EX-G09 en el resultado, solo host.sessionRef",
            ["$.host.sessionRef"],
            _nombres_con(_esquema(SCHEMA_RESULT), ("session", "binding", "sesion", "vinculo")))
    req = _request()
    otro = _con(req, ["requestedBy"], "Otra persona, en otra sesion")
    t.igual("EX-G09 otra persona en otra sesion, la misma clave", req["idempotencyKey"],
            otro["idempotencyKey"])


NADA_DEL_FLUJO = ("stage", "blockedon", "stale", "resumefrom", "taskflow", "flowstate",
                  "statefingerprint", "pendinghuman", "intent", "interaction", "decision",
                  "humanapproval")


def test_ex_g10_ni_la_intencion_ni_el_estado_del_flujo_viajan(t):
    """EX-G10 — ninguna propiedad de los dos schemas nombra la etapa, los bloqueos, la vigencia, la
    reanudacion, el estado del flujo, la intencion humana, una interaccion o una decision; del flujo,
    la unica propiedad es admission.flow."""
    for ruta in (SCHEMA_REQUEST, SCHEMA_RESULT):
        t.vacio("EX-G10 %s no copia el flujo ni la intencion humana" % ruta.name,
                _nombres_con(_esquema(ruta), NADA_DEL_FLUJO))
    t.igual("EX-G10 del flujo viaja solo admission.flow", ["$.admission.flow"],
            [r for r in ("%s.%s" % (d, n) for d, n in _propiedades(_esquema(SCHEMA_REQUEST)))
             if "flow" in r.lower()])


# Pisado por docs/cambios/minimal-execution-engine/spec.md (MD-01): dev-harness.py suma el
# subcomando `ejecutar`, y sale de esta lista. Que el resto de dev-harness.py no cambio de
# subcomandos lo cuida EX-E49; lo demas de 0.31.0 sigue protegido aca y en ME-E49.
PROTEGIDOS_031 = ("comun/hooks", "harnesses/desarrollo/bin/flujo", "harnesses/desarrollo/bin/estado_de_tarea",
                  "harnesses/desarrollo/bin/orquestacion", "harnesses/desarrollo/bin/contabilidad",
                  "harnesses/desarrollo/reglas",
                  "comun/schemas/agent-registry.schema.json", "install.ps1", "manifest.json",
                  "docs/adr/0013-modelo-de-dominio-canonico.md",
                  "comun/schemas/orchestration-plan.schema.json",
                  "comun/schemas/task-flow-state.schema.json",
                  "comun/schemas/flow-required-inputs.schema.json",
                  "comun/schemas/human-intent.schema.json",
                  "comun/schemas/human-decision-record.schema.json",
                  "comun/schemas/session-task-binding.schema.json",
                  "comun/schemas/session-flow-notice.schema.json")


def test_ex_g11_lo_de_0_31_no_se_toca(t):
    """EX-G11 — los hooks, el flujo, las decisiones, la orquestacion (plan.py y el registro de
    agentes), la contabilidad, dev-harness.py, las reglas, install.ps1, el manifiesto, ADR-0013 y los
    siete schemas de 0.31.0 son los de fdca5ce, y no hay archivos nuevos entre ellos."""
    if not _hay_base(BASE_031):
        _sin_base(t, "EX-G11", BASE_031)
        return
    existentes = [r for r in PROTEGIDOS_031 if (RAIZ / r).exists()]
    t.igual("EX-G11 todo lo protegido existe", list(PROTEGIDOS_031), existentes)
    for ruta in existentes:
        t.verdadero("EX-G11 %s es el de %s" % (ruta, BASE_031), _igual_a_la_base(ruta, BASE_031))
    codigo, crudo = M64._git("ls-files", "--others", "--exclude-standard", "--", *existentes)
    t.igual("EX-G11 no hay archivos nuevos en lo protegido", (0, ""),
            (codigo, crudo.decode("utf-8").strip()))


CONTEXTOS_DEL_FLUJO = {"SessionTaskBinding": "Work Intake", "FlowRequiredInput": "Planning",
                       "TaskFlowState": "Planning", "HumanIntent": "Planning",
                       "HumanDecisionRecord": "Planning", "SessionFlowNotice": "Guardrails"}


def test_ex_g12_el_modelo_canonico_integrado(t):
    """EX-G12 — el mapa tiene diez contextos y ninguno es el flujo; los seis conceptos de Flow
    Governance siguen en los contextos de 0.31.0; Planning -> Execution nombra el TaskFlowState y
    delegationAllowed; ExecutionAdmission dice que no es la compuerta del flujo; Execution, que no es
    la etapa EXECUTION; ExecutionError cuenta veintitres; y la idea del flujo como contexto ya no
    dice decimo y nombra ADR-0014."""
    m = M64._modelo()
    mapa = M64._tablas(M64._seccion(m["texto"], "Mapa de contextos"))
    contextos = [f[0] for f in mapa[0][1:]] if mapa else []
    t.igual("EX-G12 diez contextos", 10, len(contextos))
    t.vacio("EX-G12 ninguno es el flujo", [c for c in contextos if re.search(r"(?i)flow|flujo", c)])
    t.igual("EX-G12 los seis de Flow Governance, en sus contextos de 0.31.0", CONTEXTOS_DEL_FLUJO,
            {n: M64._valor((m["campos"].get(n) or {}).get("Contexto")) for n in CONTEXTOS_DEL_FLUJO})
    relaciones = [f for tb in M64._tablas(M64._seccion(m["texto"], "Relaciones", nivel=3)) for f in tb]
    fila = next((f for f in relaciones if f and f[0] == "Planning → Execution"), [])
    for ancla in ("TaskFlowState", "delegationAllowed", "2.1"):
        t.contiene("EX-G12 Planning -> Execution nombra %s" % ancla, ancla, " ".join(fila))
    t.contiene("EX-G12 ExecutionAdmission no es la compuerta del flujo", "comun/hooks/lib/flow_gate.py",
               (m["campos"].get("ExecutionAdmission") or {}).get("No es"))
    t.contiene("EX-G12 Execution no es la etapa EXECUTION", "etapa `EXECUTION`",
               (m["campos"].get("Execution") or {}).get("No es"))
    t.contiene("EX-G12 ExecutionError cuenta veintitres", "veintitrés",
               (m["campos"].get("ExecutionError") or {}).get("Ciclo y estados"))
    encabezados = [l[4:].strip() for l in M64._texto(IDEAS).splitlines() if l.startswith("### ")]
    t.vacio("EX-G12 ninguna idea dice que el flujo seria el decimo contexto",
            [e for e in encabezados if "tenth bounded context" in e])
    idea = M64._seccion(M64._texto(IDEAS), "Flow governance as its own bounded context", nivel=3)
    t.contiene("EX-G12 la idea nombra ADR-0014", "ADR-0014", "\n".join(idea))


ANCLAS_DE_LA_INTEGRACION = ("orchestration-plan/2.1", "DELEGATION_NOT_ALLOWED", "TaskFlowState",
                            "compuerta del flujo", "fdca5ce")
CLASES = ("**A**", "**B**", "**C**", "**D**", "**E**")
IMPACTOS = ("sin cambio", "actualizar fixture", "actualizar expectativa", "reemplazar")


def _ids_historicos():
    """Los 57 ids EX-Enn de la seccion 30, en orden."""
    lineas = M64._seccion(M64._texto(SPEC), "30. Escenarios verificables")
    return [m.group(1) for l in lineas for m in [re.match(r"^- \*\*(EX-E\d+b?)\*\*", l)] if m]


def test_ex_g13_el_adr_y_la_spec_integrados(t):
    """EX-G13 — ADR-0014 tiene la seccion Integracion con HARNESS 0.31.0 y ADR-0013 es el de
    fdca5ce; la spec tiene la seccion 37, con la tabla de cambios clasificados de A a E y cada uno de
    los 57 escenarios historicos clasificado una sola vez."""
    texto = M64._texto(ADR) if ADR.is_file() else ""
    seccion = "\n".join(M64._seccion(texto, "Integración con HARNESS 0.31.0"))
    for ancla in ANCLAS_DE_LA_INTEGRACION:
        t.contiene("EX-G13 la integracion del ADR nombra %s" % ancla, ancla, seccion)
    t.igual("EX-G13 el ADR conserva sus siete decisiones", [str(i) for i in range(1, 8)],
            [n for n, _ in _decisiones_del_adr()])
    if _hay_base(BASE_031):
        t.verdadero("EX-G13 ADR-0013 es el de %s" % BASE_031,
                    _igual_a_la_base("docs/adr/0013-modelo-de-dominio-canonico.md", BASE_031))
    else:
        _sin_base(t, "EX-G13", BASE_031)
    lineas = M64._seccion(M64._texto(SPEC), SECCION_37)
    t.verdadero("EX-G13 la spec tiene la seccion 37", len(lineas) > 0)
    tablas = M64._tablas(lineas)
    cambios = next((tb for tb in tablas if tb and tb[0][:4] == ["#", "Cambio de 0.31.0", "Dónde", "Clase"]), [])
    t.verdadero("EX-G13 la tabla de cambios tiene filas", len(cambios) > 1)
    t.vacio("EX-G13 cada cambio tiene una clase de A a E",
            [f[0] for f in cambios[1:] if not any(c in f[3] for c in CLASES)])
    impacto = next((tb for tb in tablas if tb and tb[0][:2] == ["Escenario", "Impacto"]), [])
    historicos = _ids_historicos()
    t.igual("EX-G13 son 57 escenarios historicos", 57, len(historicos))
    clasificados = [f[0].strip("`*") for f in impacto[1:]]
    t.igual("EX-G13 cada historico, clasificado una sola vez", sorted(historicos), sorted(clasificados))
    t.vacio("EX-G13 con uno de los cuatro impactos",
            [f[0] for f in impacto[1:] if f[1] not in IMPACTOS])
