# Flow Governance, Wave 2: el estado del flujo por tarea.
#
# Spec: docs/cambios/estado-del-flujo/spec.md. Cada test nombra su escenario E-nn, que es el W2-0nn
# de la Wave con el mismo numero. E-28 a E-31 son 61, 55, 53 y 60 de la suite; E-32 es la suite.
#
# Se escribieron antes que flujo/estado.py y estado_de_tarea/persistencia.py. Los modulos se
# importan adentro de cada test (`_E()`, `_P()`), para que el rojo inicial sea de cada escenario
# y no un solo error al cargar el archivo. La derivacion vive en flujo/, que no escribe nada
# (E-18 de docs/cambios/flujo-precondiciones); la escritura, en estado_de_tarea/.
import builtins
import importlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
FLUJO = BIN / "flujo"
PERSISTENCIA = BIN / "estado_de_tarea"
SCHEMA = RAIZ / "comun" / "schemas" / "task-flow-state.schema.json"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from integraciones import entorno                         # noqa: E402
from orquestacion import refutacion as R                  # noqa: E402

A, B = "ABC-123", "ABC-456"
REPO_A = "https://gitlab.example/grupo/repo-a"
REPO_B = "https://gitlab.example/grupo/repo-b"
TOKEN_JIRA = "ATATT3xFfGF0" + "w2w2w2w2w2w2w2w2w2w2"
TOKEN_GITLAB = "glpat-" + "W2w2W2w2W2w2W2w2W2w2"
BASE = "https://jira-w2.example.atlassian.net"
USUARIO = "persona.w2@example.com"
TITULO = "Titulo distintivo de la tarea W2"
CRITERIO = "Criterio distintivo W2"
OBJETIVO = "Objetivo distintivo del plan W2"
UNIDAD = "unidad-distintiva-w2"


def _E():
    """La derivacion. Adentro de cada test: sin el modulo, cada escenario falla por su cuenta."""
    return importlib.import_module("flujo.estado")


def _P():
    """La persistencia: escribir, reconciliar y el puntero a la tarea activa."""
    return importlib.import_module("estado_de_tarea.persistencia")


# -- el proyecto de prueba -----------------------------------------------------

def _escribir(ruta, texto):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(texto.encode("utf-8"))


def _git(carpeta, *args):
    subprocess.run(["git", "-C", str(carpeta)] + list(args), stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, check=True)


def _tc(clave, ficha, titulo=TITULO):
    doc = {"meta": {"schema_version": "task-context/1.0", "context_id": "tsk_" + clave,
                    "context_hash": "", "generated_at": "2026-09-29T10:00:00",
                    "harness_version": "0.26.0", "task_key": clave, "capabilities_used": []},
           "sources": [],
           "task": {"key": clave, "type": "Historia de Usuario", "title": titulo,
                    "acceptance_criteria": [CRITERIO]},
           "project": {"ficha": {"key": "ABC-1", "summary": ficha, "rules": []}},
           "documentation": {"items": []},
           "repository": {"project": {"id": "", "name": "", "web_url": "", "default_branch": ""}},
           "gaps_and_conflicts": {"missing": [], "conflicts": [], "missing_capabilities": [],
                                  "redacted_secrets": [], "unresolved_questions": []}}
    doc["meta"]["context_hash"] = R._armador().hash_de(doc)
    return doc


ENV_COMPLETO = ("HARNESS_JIRA_ENABLED=true\nJIRA_BASE_URL=%s\nJIRA_USER=%s\nJIRA_TOKEN=%s\n"
                "HARNESS_GITLAB_ENABLED=false\nGITLAB_BASE_URL=https://gitlab.example\n"
                "GITLAB_TOKEN=%s\n" % (BASE, USUARIO, TOKEN_JIRA, TOKEN_GITLAB))


def _propuesta(senales=(), agente=None):
    u = {"id": UNIDAD, "objective": "x", "domain": "backend", "requiredCapabilities": [],
         "dependencies": [], "signals": list(senales)}
    if agente:
        u["assignedAgent"] = agente
    return {"objective": OBJETIVO, "domains": ["backend"], "policies": [], "workUnits": [u]}


def _proyecto(remoto=REPO_A + ".git", env=ENV_COMPLETO):
    p = Path(tempfile.gettempdir()) / ("harness-w2-" + uuid.uuid4().hex[:8])
    p.mkdir()
    _git(p, "init", "-q")
    if remoto:
        _git(p, "remote", "add", "origin", remoto)
    if env is not None:
        _escribir(p / ".env", env)
    _escribir(p / ".claude" / "harness.capacidades.json", json.dumps({"capacidades": {}}))
    _escribir(p / ".claude" / "harness.config.json",
              json.dumps({"campoCriteriosAceptacion": "cf_1"}))
    return p


def _contexto(p, clave, ficha="Repo: " + REPO_A, titulo=TITULO):
    _escribir(p / ".claude" / "contextos" / (clave + ".json"), json.dumps(_tc(clave, ficha, titulo)))


def _entorno_limpio():
    variables = set(entorno.variables_del_contrato(entorno.cargar_contrato()))
    return dict((k, v) for k, v in os.environ.items() if k not in variables)


def _cli(p, *args):
    s = subprocess.run([sys.executable, str(CLI)] + list(args) + ["--proyecto", str(p)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_entorno_limpio())
    return s.returncode, s.stdout.decode("utf-8", "replace"), s.stderr.decode("utf-8", "replace")


def _plan(p, clave, propuesta=None):
    ruta = p / ("prop-%s.json" % clave)
    _escribir(ruta, json.dumps(propuesta or _propuesta()))
    return _cli(p, "plan", clave, "--propuesta", str(ruta))


def _estado(p, clave):
    ruta = p / ".claude" / "runtime" / "tasks" / clave / "state.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def _derivar(p, clave):
    return _E().derivar(str(p), clave, proceso={})


def _codigos(doc):
    return [b["code"] for b in (doc or {}).get("blockedOn") or []]


def _claves(nodo):
    if isinstance(nodo, dict):
        return set(nodo) | set().union(*[_claves(v) for v in nodo.values()]) if nodo else set()
    if isinstance(nodo, list):
        return set().union(*[_claves(v) for v in nodo]) if nodo else set()
    return set()


def _borrar(*carpetas):
    for c in carpetas:
        shutil.rmtree(str(c), ignore_errors=True)


def _falla(t, nombre, codigo, llamada):
    try:
        llamada()
        t.verdadero("%s levanta" % nombre, False)
    except Exception as e:                                   # noqa: BLE001
        t.igual("%s: %s" % (nombre, codigo), codigo, getattr(e, "codigo", repr(e)))


# -- E-01 a E-08: un estado por tarea ------------------------------------------

def test_e01_dos_tareas_dos_estados(t):
    p = _proyecto()
    try:
        for clave in (A, B):
            _contexto(p, clave)
            _plan(p, clave)
        ea, eb = _estado(p, A), _estado(p, B)
        t.verdadero("E-01 hay dos state.json", ea is not None and eb is not None)
        if ea and eb:
            t.igual("E-01 cada uno con su tarea", [A, B], [ea["taskKey"], eb["taskKey"]])
            t.verdadero("E-01 y su propio plan",
                        ea["planRef"]["path"] != eb["planRef"]["path"]
                        and A in ea["planRef"]["path"] and B in eb["planRef"]["path"])
            t.igual("E-01 validan contra task-flow-state/1.0", [[], []],
                    [_E().validar(ea), _E().validar(eb)])
    finally:
        _borrar(p)


def test_e02_no_hay_singleton(t):
    p = _proyecto()
    try:
        _contexto(p, A)
        _plan(p, A)
        _cli(p, "refute", A, "--compile")
        t.verdadero("E-02 no existe task-state.json",
                    not (p / ".claude" / "runtime" / "task-state.json").exists())
        t.verdadero("E-02 y el estado esta por tarea", _estado(p, A) is not None)
    finally:
        _borrar(p)
    nombran = [f.relative_to(BIN).as_posix() for f in BIN.rglob("*.py")
               if "__pycache__" not in f.parts
               and "task-state.json" in f.read_text(encoding="utf-8")]
    t.igual("E-02 ningun fuente lo nombra", [], nombran)


def test_e03_active_task_es_un_puntero(t):
    p = _proyecto()
    try:
        for clave in (A, B):
            _contexto(p, clave)
            _plan(p, clave)
        ruta = p / ".claude" / "runtime" / "active-task.json"
        t.verdadero("E-03 existe", ruta.exists())
        if ruta.exists():
            doc = json.loads(ruta.read_text(encoding="utf-8"))
            t.igual("E-03 solo el puntero", ["schema_version", "taskKey"], sorted(doc))
            t.igual("E-03 a la ultima tarea reconciliada", B, doc["taskKey"])
            t.igual("E-03 valida", [], _E().validar(doc, "activeTask"))
    finally:
        _borrar(p)


def test_e04_el_estado_se_reconstruye(t):
    p = _proyecto()
    vacio_con_jira, vacio_sin_jira = _proyecto(), _proyecto(env=None)
    try:
        _contexto(p, A)
        _plan(p, A)
        guardado = _estado(p, A)
        (p / ".claude" / "runtime" / "tasks" / A / "state.json").unlink()
        t.igual("E-04 el mismo estado logico", _E().logico(guardado),
                _E().logico(_derivar(p, A)) if guardado else None)
        con = _derivar(vacio_con_jira, A)
        sin = _derivar(vacio_sin_jira, A)
        t.igual("E-04 sin artefactos y con Jira: CONTEXT / NEW", ["CONTEXT", "NEW"],
                [con["stage"], con["status"]])
        t.igual("E-04 sin artefactos ni Jira: CONTEXT / BLOCKED", ["CONTEXT", "BLOCKED"],
                [sin["stage"], sin["status"]])
    finally:
        _borrar(p, vacio_con_jira, vacio_sin_jira)


def test_e05_no_copia_el_task_context(t):
    p = _proyecto()
    try:
        _contexto(p, A, ficha="Ficha distintiva W2, repo " + REPO_A)
        _plan(p, A)
        texto = json.dumps(_estado(p, A))
        for nombre, valor in (("el titulo", TITULO), ("el criterio", CRITERIO),
                              ("la ficha", "Ficha distintiva W2")):
            t.no_contiene("E-05 sin %s" % nombre, valor, texto)
        t.verdadero("E-05 y lo referencia", '"contextRef"' in texto and "contextHash" in texto)
    finally:
        _borrar(p)


def test_e06_no_copia_el_plan(t):
    p = _proyecto()
    try:
        _contexto(p, A)
        _plan(p, A)
        texto = json.dumps(_estado(p, A))
        t.no_contiene("E-06 sin el objetivo", OBJETIVO, texto)
        t.no_contiene("E-06 sin las unidades", UNIDAD, texto)
        t.no_contiene("E-06 sin workUnits", "workUnits", texto)
        t.verdadero("E-06 y lo referencia", "planFingerprint" in texto)
    finally:
        _borrar(p)


def test_e07_sin_valores_del_env(t):
    p = _proyecto()
    try:
        _contexto(p, A)
        _plan(p, A)
        texto = json.dumps(_estado(p, A)) + json.dumps(_derivar(p, A))
        for nombre, valor in (("token de Jira", TOKEN_JIRA), ("token de GitLab", TOKEN_GITLAB),
                              ("base URL", BASE), ("usuario", USUARIO)):
            t.no_contiene("E-07 sin el %s" % nombre, valor, texto)
    finally:
        _borrar(p)


def test_e08_un_secreto_pendiente_sin_valor_ni_posicion(t):
    p = _proyecto(env="HARNESS_JIRA_ENABLED=true\nJIRA_BASE_URL=%s\nJIRA_USER=%s\n" % (
        BASE, USUARIO))
    try:
        doc = _P().reconciliar(str(p), A, proceso={})
        pendiente = doc["pendingHumanInteraction"]
        t.igual("E-08 la interaccion pendiente",
                {"kind": "PERSISTENT_CONFIG_INPUT", "inputId": "jira.token", "target": ".env",
                 "key": "JIRA_TOKEN", "sensitivity": "SECRET"}, pendiente)
        guardado = _estado(p, A)
        prohibidas = {"value", "rawLine", "line", "column", "vscodeUri"}
        t.igual("E-08 ninguna clave prohibida en el guardado", [],
                sorted(prohibidas & _claves(guardado)))
        t.no_contiene("E-08 ni una URI", "vscode:", json.dumps(guardado))
    finally:
        _borrar(p)


# -- E-09 a E-14: permisos y transiciones --------------------------------------

AVANCE = ("planningAllowed", "delegationAllowed", "implementationAllowed", "refutationAllowed",
          "completionAllowed")
RECUPERACION = ["cancel", "inspectState", "locatePersistentInput", "renderPendingInteraction",
                "revalidate", "validate"]


def test_e09_bloqueado_no_avanza(t):
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        doc = _derivar(p, A)
        t.igual("E-09 esta BLOCKED", "BLOCKED", doc["status"])
        permisos = _E().permisos(doc)
        t.igual("E-09 ningun permiso de avance", [False] * 5, [permisos[k] for k in AVANCE])
        t.igual("E-09 solo la recuperacion", RECUPERACION, sorted(permisos["recovery"]))
    finally:
        _borrar(p)


def test_e10_esperando_una_aprobacion_no_avanza(t):
    p = _proyecto()
    try:
        _contexto(p, A)
        _plan(p, A, _propuesta(["ambiguity", "security_impact", "architectural_impact"]))
        doc = _derivar(p, A)
        t.igual("E-10 WAITING_FOR_HUMAN_APPROVAL", "WAITING_FOR_HUMAN_APPROVAL", doc["status"])
        permisos = _E().permisos(doc)
        t.igual("E-10 ningun permiso de avance", [False] * 5, [permisos[k] for k in AVANCE])
        t.igual("E-10 solo la recuperacion", RECUPERACION, sorted(permisos["recovery"]))
        _plan(p, A)
        listo = _E().permisos(_derivar(p, A))
        t.igual("E-10 y con el plan listo, implementar si", True, listo["implementationAllowed"])
    finally:
        _borrar(p)


def test_e11_una_transicion_no_se_declara(t):
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        bloqueado = _derivar(p, A)
        avanzado = dict(bloqueado, stage="EXECUTION", status="ACTIVE", blockedOn=[],
                        pendingHumanInteraction=None, resumeFrom=None)
        E = _E()
        _falla(t, "E-11 BLOCKED a EXECUTION sin reevaluar", "FLOW_TRANSITION_INVALID",
               lambda: E.validar_transicion(bloqueado, avanzado, revalidado=False))
        con_bloqueos = dict(bloqueado, status="ACTIVE")
        _falla(t, "E-11 un ACTIVE con bloqueos", "FLOW_TRANSITION_INVALID",
               lambda: E.validar_transicion(bloqueado, con_bloqueos, revalidado=True))
        sin_bloqueos = dict(bloqueado, blockedOn=[], resumeFrom=None, pendingHumanInteraction=None)
        _falla(t, "E-11 un BLOCKED sin bloqueos", "FLOW_TRANSITION_INVALID",
               lambda: E.validar_transicion(bloqueado, sin_bloqueos, revalidado=True))
        t.igual("E-11 reevaluar al mismo estado es valido", None,
                E.validar_transicion(bloqueado, bloqueado, revalidado=True))
    finally:
        _borrar(p)


def test_e12_resolver_reevalua_la_compuerta(t):
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        t.verdadero("E-12 arranca con REPOSITORY_MISMATCH",
                    "REPOSITORY_MISMATCH" in _codigos(_estado(p, A)))
        _git(p, "remote", "set-url", "origin", REPO_A + ".git")
        t.verdadero("E-12 el guardado no avanza solo", "REPOSITORY_MISMATCH" in _codigos(_estado(p, A)))
        doc = _P().reconciliar(str(p), A, proceso={})
        t.igual("E-12 la compuerta se reevaluo: queda regenerar el plan", ["PLAN_NOT_READY"],
                _codigos(doc))
        t.igual("E-12 y no llega a EXECUTION", ["PLANNING", "BLOCKED"], [doc["stage"], doc["status"]])
        _plan(p, A)
        despues = _estado(p, A)
        t.igual("E-12 con el plan nuevo, EXECUTION / ACTIVE", ["EXECUTION", "ACTIVE"],
                [despues["stage"], despues["status"]])
    finally:
        _borrar(p)


def test_e13_sin_resolver_sigue_bloqueado(t):
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        antes = _estado(p, A)
        doc = _P().reconciliar(str(p), A, proceso={})
        t.igual("E-13 sigue BLOCKED", "BLOCKED", doc["status"])
        t.igual("E-13 con el mismo bloqueo", _codigos(antes), _codigos(doc))
        t.verdadero("E-13 y es el del repositorio", "REPOSITORY_MISMATCH" in _codigos(doc))
    finally:
        _borrar(p)


def test_e14_resume_from_es_una_compuerta_canonica(t):
    casos = []
    p1 = _proyecto(remoto=REPO_B + ".git")                              # repositorio
    p2 = _proyecto(env="HARNESS_JIRA_ENABLED=true\n")                    # Jira
    p3 = _proyecto()                                                    # aprobacion
    try:
        _contexto(p1, A)
        _plan(p1, A)
        casos.append(_derivar(p1, A))
        casos.append(_derivar(p2, A))
        _contexto(p3, A)
        _plan(p3, A, _propuesta(["ambiguity", "security_impact", "architectural_impact"]))
        casos.append(_derivar(p3, A))
        E = _E()
        bloqueos = [b for d in casos for b in d["blockedOn"]]
        t.verdadero("E-14 hay bloqueos para mirar", len(bloqueos) >= 3)
        for b in bloqueos:
            t.igual("E-14 %s: resumeFrom es {stage, gate}" % b["code"], ["gate", "stage"],
                    sorted(b["resumeFrom"]))
            t.verdadero("E-14 %s: compuerta canonica" % b["code"], b["resumeFrom"]["gate"] in E.GATES)
            t.verdadero("E-14 %s: etapa conocida" % b["code"], b["resumeFrom"]["stage"] in E.STAGES)
            t.verdadero("E-14 %s: blockerId canonico" % b["code"],
                        bool(re.match(r"^FLOW-[A-Z]+-[0-9]{3}$", b["blockerId"])))
        for d in casos:
            t.igual("E-14 el resumeFrom del estado es el del primer bloqueo",
                    d["blockedOn"][0]["resumeFrom"], d["resumeFrom"])
    finally:
        _borrar(p1, p2, p3)


# -- E-15 a E-20: lo desactualizado --------------------------------------------

def _listo(p, clave=A):
    _contexto(p, clave)
    _plan(p, clave)
    return _estado(p, clave)


def test_e15_contexto_cambiado(t):
    p = _proyecto()
    try:
        guardado = _listo(p)
        _contexto(p, A, titulo="la tarea cambio en Jira")
        derivado = _derivar(p, A)
        t.verdadero("E-15 vigencia: TASK_CONTEXT_STALE",
                    "TASK_CONTEXT_STALE" in _E().vigencia(guardado, derivado))
        t.verdadero("E-15 el derivado lo lleva en stale", "TASK_CONTEXT_STALE" in derivado["stale"])
        t.verdadero("E-15 con un bloqueo CONTEXT_STALE", "CONTEXT_STALE" in _codigos(derivado))
    finally:
        _borrar(p)


def test_e16_plan_reescrito(t):
    p = _proyecto()
    try:
        guardado = _listo(p)
        ruta = p / ".claude" / "planes" / (A + ".json")
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        plan["warnings"].append("reescrito a mano")
        _escribir(ruta, json.dumps(plan))
        t.verdadero("E-16 vigencia: PLAN_STALE",
                    "PLAN_STALE" in _E().vigencia(guardado, _derivar(p, A)))
    finally:
        _borrar(p)


def test_e17_remoto_cambiado(t):
    p = _proyecto()
    try:
        guardado = _listo(p)
        _git(p, "remote", "set-url", "origin", "git@gitlab.example:grupo/otro.git")
        t.verdadero("E-17 vigencia: REPOSITORY_STATE_STALE",
                    "REPOSITORY_STATE_STALE" in _E().vigencia(guardado, _derivar(p, A)))
    finally:
        _borrar(p)


def test_e18_refutacion_de_otro_plan(t):
    p = _proyecto()
    try:
        _listo(p)
        codigo, _, _ = _cli(p, "refute", A, "--compile")
        t.igual("E-18 la corrida compila", 0, codigo)
        ruta = p / ".claude" / "planes" / (A + ".json")
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        plan["warnings"].append("otro plan")
        _escribir(ruta, json.dumps(plan))
        derivado = _derivar(p, A)
        t.verdadero("E-18 REFUTATION_STATE_STALE", "REFUTATION_STATE_STALE" in derivado["stale"])
        t.verdadero("E-18 con un bloqueo REFUTATION_PLAN_STALE",
                    "REFUTATION_PLAN_STALE" in _codigos(derivado))
        t.igual("E-18 en la etapa de refutacion", "REFUTATION", derivado["stage"])
    finally:
        _borrar(p)


def test_e19_un_estado_roto_no_vale(t):
    p = _proyecto()
    try:
        _listo(p)
        ruta = p / ".claude" / "runtime" / "tasks" / A / "state.json"
        E = _E()
        for nombre, contenido in (("JSON roto", '{"status": "ACTIVE", '),
                                  ("fuera del schema", json.dumps({
                                      "schema_version": "task-flow-state/1.0", "taskKey": A,
                                      "stage": "EXECUTION", "status": "READY"}))):
            _escribir(ruta, contenido)
            guardado, error = E.leer(str(p), A)
            t.igual("E-19 %s: TASK_FLOW_STATE_INVALID" % nombre, [None, "TASK_FLOW_STATE_INVALID"],
                    [guardado, error])
            derivado = _derivar(p, A)
            vig = E.vigencia(guardado, derivado, error)
            t.verdadero("E-19 %s: la vigencia lo dice" % nombre, "TASK_FLOW_STATE_INVALID" in vig)
            permisos = E.permisos(derivado, vig)
            t.igual("E-19 %s: ningun permiso de avance" % nombre, [False] * 5,
                    [permisos[k] for k in AVANCE])
            codigo, salida, _ = _cli(p, "flujo", A, "--status")
            t.igual("E-19 %s: flujo --status sale con 0" % nombre, 0, codigo)
            t.contiene("E-19 %s: y lo muestra" % nombre, "TASK_FLOW_STATE_INVALID", salida)
    finally:
        _borrar(p)


def test_e20_una_escritura_rota_no_deja_medio_archivo(t):
    p = _proyecto()
    try:
        _listo(p)
        E = _P()
        ruta = p / ".claude" / "runtime" / "tasks" / A / "state.json"
        antes = ruta.read_bytes()
        nuevo = dict(json.loads(antes.decode("utf-8")), updatedAt="2030-01-01T00:00:00")
        original = E.os.replace

        def roto(*_a, **_k):
            raise OSError("disco lleno a mitad de camino")
        E.os.replace = roto
        try:
            E.escribir(str(p), A, nuevo)
            t.verdadero("E-20 la escritura rota levanta", False)
        except OSError:
            pass
        finally:
            E.os.replace = original
        t.igual("E-20 el anterior queda entero", antes, ruta.read_bytes())
        t.igual("E-20 sin temporales", ["state.json"], sorted(os.listdir(str(ruta.parent))))
    finally:
        _borrar(p)


# -- E-21 a E-27: en los comandos ----------------------------------------------

def _contexto_19():
    ruta = RAIZ / "tests" / "casos" / "19_contexto.py"
    spec = importlib.util.spec_from_file_location("caso_19_para_62", str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_e21_contexto_reconcilia(t):
    c19 = _contexto_19()
    raiz = c19._proyecto_listo()
    try:
        transporte = c19.Transporte({"/issue/": (200, c19.ISSUE), "/search": (200, c19.FICHA)})
        codigo, _, _ = c19._correr_cli(["contexto", c19.CLAVE, "--proyecto", raiz], transporte,
                                       c19._Bytes({}))
        t.igual("E-21 contexto sale con 0", 0, codigo)
        doc = _estado(Path(raiz), c19.CLAVE)
        t.verdadero("E-21 dejo el estado", doc is not None)
        if doc:
            contexto = json.loads(io.open(os.path.join(raiz, ".claude", "contextos",
                                                       c19.CLAVE + ".json"), encoding="utf-8").read())
            t.igual("E-21 en PLANNING", "PLANNING", doc["stage"])
            t.igual("E-21 con el hash del contexto", contexto["meta"]["context_hash"],
                    doc["contextRef"]["contextHash"])
    finally:
        _borrar(raiz)


def test_e22_plan_bloqueado_es_tarea_bloqueada(t):
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        doc = _estado(p, A)
        t.igual("E-22 BLOCKED", "BLOCKED", (doc or {}).get("status"))
        t.verdadero("E-22 con REPOSITORY_MISMATCH", "REPOSITORY_MISMATCH" in _codigos(doc))
        t.igual("E-22 y el plan referenciado BLOCKED", "BLOCKED",
                ((doc or {}).get("planRef") or {}).get("planStatus"))
    finally:
        _borrar(p)


def test_e23_plan_listo_no_se_bloquea(t):
    p = _proyecto()
    try:
        doc = _listo(p)
        t.igual("E-23 EXECUTION / ACTIVE", ["EXECUTION", "ACTIVE"],
                [(doc or {}).get("stage"), (doc or {}).get("status")])
        t.igual("E-23 sin bloqueos", [], _codigos(doc))
        t.igual("E-23 el plan referenciado READY_FOR_EXECUTION", "READY_FOR_EXECUTION",
                ((doc or {}).get("planRef") or {}).get("planStatus"))
    finally:
        _borrar(p)


def test_e24_una_compuerta_fallida_deja_el_estado_coherente(t):
    p = _proyecto()
    q = _proyecto()
    try:
        _contexto(p, A)
        _plan(p, A, _propuesta(["ambiguity", "security_impact", "architectural_impact"]))
        codigo, _, error = _cli(p, "refute", A, "--compile")
        t.igual("E-24 aprobacion: sale con 2", 2, codigo)
        t.verdadero("E-24 aprobacion: sin run.json",
                    not (p / ".claude" / "refutaciones" / A / "run.json").exists())
        doc = _estado(p, A)
        t.igual("E-24 aprobacion: el estado espera la aprobacion", "WAITING_FOR_HUMAN_APPROVAL",
                (doc or {}).get("status"))
        t.verdadero("E-24 con HUMAN_APPROVAL_PENDING", "HUMAN_APPROVAL_PENDING" in _codigos(doc))

        _listo(q)
        _contexto(q, A, titulo="otro contexto")
        codigo, _, error = _cli(q, "refute", A, "--compile")
        t.igual("E-24 contexto vencido: sale con 2", 2, codigo)
        doc = _estado(q, A)
        t.verdadero("E-24 el estado lleva CONTEXT_STALE", "CONTEXT_STALE" in _codigos(doc))
        t.verdadero("E-24 sin run.json", not (q / ".claude" / "refutaciones" / A / "run.json").exists())
    finally:
        _borrar(p, q)


def _cli_en_proceso(argv):
    spec = importlib.util.spec_from_file_location("dev_harness_62", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(argv, _TransporteQueNoSeUsa(), _TransporteQueNoSeUsa())
    except SystemExit as e:
        # argparse sale asi con un comando que no conoce: es un codigo, no un corte de la suite.
        codigo = e.code
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


class _TransporteQueNoSeUsa(object):
    def __init__(self):
        self.llamadas = 0

    def __call__(self, *_a, **_k):
        self.llamadas += 1
        raise AssertionError("flujo --status salio a la red")


def test_e25_flujo_status_no_sale_a_la_red(t):
    p = _proyecto()
    try:
        _listo(p)
        original = socket.socket

        class _SinRed(object):
            def __init__(self, *_a, **_k):
                raise AssertionError("se abrio un socket")
        socket.socket = _SinRed
        try:
            codigo, salida, error = _cli_en_proceso(["flujo", A, "--status", "--proyecto", str(p)])
            codigo_json, salida_json, _ = _cli_en_proceso(
                ["flujo", A, "--status", "--json", "--proyecto", str(p)])
        finally:
            socket.socket = original
        t.igual("E-25 sale con 0 sin red", 0, codigo)
        for rotulo in ("Etapa", "Estado", "Bloqueos", "Interacción pendiente", "Retoma en",
                       "Contexto", "Plan", "Refutación"):
            t.contiene("E-25 muestra %s" % rotulo, rotulo, salida)
        t.igual("E-25 --json sale con 0", 0, codigo_json)
        doc = json.loads(salida_json) if codigo_json == 0 else {}
        t.igual("E-25 --json es task-flow-state/1.0", [], _E().validar(doc) if doc else ["vacio"])
    finally:
        _borrar(p)


def test_e26_flujo_no_importa_modelos_ni_http(t):
    prohibido = re.compile(r"^\s*(?:import|from)\s+(anthropic|openai|requests|socket|http|"
                           r"urllib\.request|integraciones\.http)\b", re.M)
    fuentes = sorted(FLUJO.glob("*.py")) + sorted(PERSISTENCIA.glob("*.py"))
    t.verdadero("E-26 esta estado.py", (FLUJO / "estado.py").exists())
    t.verdadero("E-26 esta persistencia.py", (PERSISTENCIA / "persistencia.py").exists())
    for fuente in fuentes:
        t.igual("E-26 %s no importa red ni modelo" % fuente.name, [],
                prohibido.findall(fuente.read_text(encoding="utf-8")))


def test_e27_el_bloque_4_no_gobierna(t):
    p = _proyecto()
    try:
        _listo(p)
        antes = _E().logico(_derivar(p, A))
        _escribir(p / ".claude" / "runtime" / "accounting" / A / "events.jsonl",
                  json.dumps({"eventType": "WORKUNIT_COMPLETED", "taskId": A,
                              "status": "COMPLETED", "stage": "COMPLETION"}) + "\n")
        t.igual("E-27 el libro no cambia el estado", antes, _E().logico(_derivar(p, A)))
    finally:
        _borrar(p)
    for fuente in sorted(FLUJO.glob("*.py")) + sorted(PERSISTENCIA.glob("*.py")):
        t.verdadero("E-27 %s no importa contabilidad" % fuente.name,
                    "contabilidad" not in fuente.read_text(encoding="utf-8"))


# -- Lo que la verificacion encontro sin test (docs/cambios/estado-del-flujo/verificacion.md) ----

def test_e23b_un_plan_escrito_bloqueado_no_llega_a_execution(t):
    """E-23b — el estado escrito del plan manda tanto como el recalculado: si cualquiera de los
    dos no es READY_FOR_EXECUTION, la tarea no esta en EXECUTION."""
    p = _proyecto(remoto=REPO_B + ".git")
    try:
        _contexto(p, A)
        _plan(p, A)
        _git(p, "remote", "set-url", "origin", REPO_A + ".git")
        ruta = p / ".claude" / "planes" / (A + ".json")
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        plan["flowPreconditions"]["status"] = "READY"
        plan["flowPreconditions"]["questions"] = []
        _escribir(ruta, json.dumps(plan))
        doc = _derivar(p, A)
        t.igual("E-23b el plan escrito sigue BLOCKED", "BLOCKED", doc["planRef"]["planStatus"])
        t.verdadero("E-23b la tarea no esta en EXECUTION", doc["stage"] != "EXECUTION")
        t.verdadero("E-23b con PLAN_NOT_READY", "PLAN_NOT_READY" in _codigos(doc))
        t.igual("E-23b y no se puede implementar", False,
                _E().permisos(doc)["implementationAllowed"])
        con_stale = dict(_derivar(p, A), stage="EXECUTION", status="ACTIVE", blockedOn=[],
                         pendingHumanInteraction=None, resumeFrom=None, stale=["PLAN_STALE"])
        t.igual("E-23b un stale entre artefactos tampoco deja avanzar", [False] * 5,
                [_E().permisos(con_stale)[k] for k in AVANCE])
    finally:
        _borrar(p)


def test_e19b_un_artefacto_roto_no_se_toma_por_ausente(t):
    """E-19b — un TaskContext, un plan o un run.json que estan y no se leen bloquean con un codigo
    que ya existia; no se leen como si no estuvieran."""
    for nombre, relativa, codigo in (
            ("TaskContext", (".claude", "contextos", A + ".json"), "TASK_CONTEXT_MISSING"),
            ("plan", (".claude", "planes", A + ".json"), "PLAN_NOT_READY"),
            ("run.json", (".claude", "refutaciones", A, "run.json"), "REFUTATION_OUTPUT_INVALID")):
        p = _proyecto()
        try:
            _listo(p)
            _cli(p, "refute", A, "--compile")
            _escribir(p.joinpath(*relativa), '{"roto": ')
            doc = _derivar(p, A)
            t.igual("E-19b %s roto: BLOCKED" % nombre, "BLOCKED", doc["status"])
            t.verdadero("E-19b %s roto: %s" % (nombre, codigo), codigo in _codigos(doc))
            t.igual("E-19b %s roto: sin permisos de avance" % nombre, [False] * 5,
                    [_E().permisos(doc)[k] for k in AVANCE])
        finally:
            _borrar(p)
    # Las dos variantes que encontro la verificacion: un run.json roto SIN plan, y un plan que
    # es JSON valido pero vacio.
    p = _proyecto()
    try:
        _contexto(p, A)
        _escribir(p / ".claude" / "refutaciones" / A / "run.json", '{"roto": ')
        doc = _derivar(p, A)
        t.verdadero("E-19b run.json roto sin plan: REFUTATION_OUTPUT_INVALID",
                    "REFUTATION_OUTPUT_INVALID" in _codigos(doc))
        (p / ".claude" / "refutaciones" / A / "run.json").unlink()
        _escribir(p / ".claude" / "planes" / (A + ".json"), "{}")
        doc = _derivar(p, A)
        t.verdadero("E-19b un plan {} no es un plan ausente: PLAN_NOT_READY",
                    "PLAN_NOT_READY" in _codigos(doc))
        t.verdadero("E-19b y queda referenciado", doc["planRef"] is not None)
    finally:
        _borrar(p)


def _huellas(p):
    return dict((f.relative_to(p).as_posix(), (f.stat().st_mtime_ns, f.read_bytes()))
                for f in p.rglob("*") if f.is_file() and ".git" not in f.parts)


def test_e25b_flujo_status_no_escribe(t):
    """E-25b — `flujo --status` no escribe nada: con el estado guardado, sin el, y sin artefactos."""
    p = _proyecto()
    vacio = _proyecto()
    try:
        _listo(p)
        for rotulo, proyecto in (("con estado", p), ("sin artefactos", vacio)):
            antes = _huellas(proyecto)
            codigo, salida, _ = _cli(proyecto, "flujo", A, "--status")
            t.igual("E-25b %s: sale con 0" % rotulo, 0, codigo)
            t.igual("E-25b %s: no cambio ningun archivo" % rotulo, antes, _huellas(proyecto))
        (p / ".claude" / "runtime" / "tasks" / A / "state.json").unlink()
        antes = _huellas(p)
        codigo, salida, _ = _cli(p, "flujo", A, "--status")
        t.contiene("E-25b sin state.json lo dice", "TASK_FLOW_STATE_MISSING", salida)
        t.igual("E-25b y no lo crea", antes, _huellas(p))
    finally:
        _borrar(p, vacio)


def test_e25c_un_estado_igual_no_se_reescribe(t):
    """E-25c — reconciliar dos veces sin cambios deja el mismo archivo, con su updatedAt."""
    p = _proyecto()
    try:
        _listo(p)
        ruta = p / ".claude" / "runtime" / "tasks" / A / "state.json"
        antes = (ruta.stat().st_mtime_ns, ruta.read_bytes())
        _P().reconciliar(str(p), A, proceso={})
        t.igual("E-25c mismo archivo y mismo mtime", antes, (ruta.stat().st_mtime_ns, ruta.read_bytes()))
    finally:
        _borrar(p)


def test_e25d_compile_y_record_reconcilian(t):
    """E-25d — `refute --compile` que pasa y `refute --record` dejan el estado al dia."""
    p = _proyecto()
    try:
        _listo(p)
        codigo, _, _ = _cli(p, "refute", A, "--compile")
        doc = _estado(p, A)
        t.igual("E-25d compile pasa", 0, codigo)
        t.verdadero("E-25d el estado referencia la corrida", (doc or {}).get("refutationRef") is not None)
        esperada = {"PASS": "COMPLETION", "NOTHING_TO_VERIFY": "COMPLETION"}.get(
            ((doc or {}).get("refutationRef") or {}).get("status"), "REFUTATION")
        t.igual("E-25d y esta en la etapa que dice la corrida", esperada, (doc or {}).get("stage"))
    finally:
        _borrar(p)
    ra = importlib.util.spec_from_file_location("c55_62", str(RAIZ / "tests" / "casos" /
                                                              "55_refutacion_atomica.py"))
    m = importlib.util.module_from_spec(ra)
    ra.loader.exec_module(m)
    proy = m._proyecto()
    try:
        R.compilar(str(proy), m.CLAVE)
        u = [x for x in m._unidades(proy) if x["status"] == "PENDING_SEMANTIC"][0]
        ruta_v = proy / "v.json"
        _escribir(ruta_v, json.dumps(m._veredicto(u)))
        t.verdadero("E-25d sin estado antes de --record", _estado(proy, m.CLAVE) is None)
        codigo, _, _ = m._cli(proy, "refute", m.CLAVE, "--record", str(ruta_v))
        t.igual("E-25d --record sale con 0", 0, codigo)
        doc = _estado(proy, m.CLAVE)
        t.verdadero("E-25d --record dejo el estado con la corrida",
                    doc is not None and doc.get("refutationRef") is not None)
    finally:
        m._borrar(proy)


def test_e25e_una_reconciliacion_que_falla_no_voltea_el_comando(t):
    """E-25e — si el estado no se puede guardar, el comando sale igual y lo avisa."""
    p = _proyecto()
    try:
        _contexto(p, A)
        _escribir(p / ".claude" / "runtime" / "tasks" / A, "un archivo donde va una carpeta")
        codigo, _, error = _plan(p, A)
        t.igual("E-25e plan sale con 0", 0, codigo)
        t.verdadero("E-25e el plan se escribio", (p / ".claude" / "planes" / (A + ".json")).exists())
        t.contiene("E-25e y avisa", "no se pudo actualizar el estado del flujo", error)
    finally:
        _borrar(p)
