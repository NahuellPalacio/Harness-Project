# Flow Governance, Wave 4: la persona responde, decide y retoma.
#
# Spec: docs/cambios/interaccion-humana/spec.md. Cada test nombra su escenario E-nn, que es el W4-0nn
# con el mismo numero; de E-43 en adelante los pidio la implementacion. E-34 a E-42 son archivos de
# la suite y la compuerta entera.
#
# Se escribieron antes que flujo/interaccion.py, estado_de_tarea/decisiones.py y
# lib/human_intent.py. Los modulos se importan adentro de cada test. Los hooks y la CLI corren como
# procesos hijos, con proyectos temporales, remotos que no existen y secretos sinteticos.
import importlib
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = "python .claude/harness/bin/desarrollo/dev-harness.py"

for _ruta in (str(BIN), str(HOOKS)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


W2 = _cargar("caso_62_para_64", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")
W3 = _cargar("caso_63_para_64", RAIZ / "tests" / "casos" / "63_compuerta_del_flujo.py")

A, B = "ABC-123", "ABC-456"
SECRETO = "ATATT3xFfGF0" + "w4w4w4w4w4w4w4w4w4w4"
SECRETO_ALTO = "Server=s;Pass" + "word=Tr4ns4cc10n;"
IXN = re.compile(r"ixn-[0-9a-f]{16}")


def _I():
    return importlib.import_module("flujo.interaccion")


def _D():
    return importlib.import_module("estado_de_tarea.decisiones")


def _H():
    return importlib.import_module("lib.human_intent")


# -- los proyectos -------------------------------------------------------------

def _propuesta(unidades):
    return {"objective": W2.OBJETIVO, "domains": ["backend"], "policies": [],
            "workUnits": [{"id": u, "objective": "x", "domain": "backend",
                           "requiredCapabilities": [], "dependencies": [], "signals": s}
                          for u, s in unidades]}


REASONING = ["ambiguity", "novelty"]


def _esperando(unidades=(("u1", REASONING),), clave=A, p=None):
    """Una tarea en PLANNING / WAITING_FOR_HUMAN_APPROVAL: una aprobacion por unidad."""
    p = p or W2._proyecto()
    W2._contexto(p, clave)
    W2._plan(p, clave, _propuesta(unidades))
    return p


_REPLANES = [0]


def _replanificar(p, clave=A, unidades=(("u1", REASONING),)):
    """Otro plan de verdad: el objetivo cambia en cada llamada. Dos planes iguales en el mismo
    segundo son el mismo plan, y su interaccion tiene que tener el mismo id."""
    _REPLANES[0] += 1
    propuesta = _propuesta(unidades)
    propuesta["objective"] = "%s, version %d" % (W2.OBJETIVO, _REPLANES[0])
    return W2._plan(p, clave, propuesta)


def _conflicto():
    """PLANNING / BLOCKED por REPOSITORY_CONFLICT: la ficha declara dos repositorios."""
    p = W2._proyecto()
    W2._contexto(p, A, ficha="Repo: %s y Repo: %s" % (W2.REPO_A, W2.REPO_B))
    W3._reconciliar(p, A)
    return p


def _estado(p, clave=A):
    return W2._estado(p, clave)


def _plan(p, clave=A):
    return json.loads((p / ".claude" / "planes" / (clave + ".json")).read_text(encoding="utf-8"))


def _interacciones(p, clave=A):
    try:
        return _I().interacciones(str(p), clave)
    except Exception as e:                                   # noqa: BLE001
        return [{"interactionId": "error", "error": repr(e), "actions": [], "options": []}]


def _iid(p, clave=A, tipo=None, input_id=None):
    for i in _interacciones(p, clave):
        if (tipo is None or i.get("kind") == tipo) and (input_id is None or i.get("inputId") == input_id):
            return i["interactionId"]
    return "ixn-0000000000000000"


def _intent(p, sesion):
    ruta = p / ".claude" / "runtime" / "sessions" / sesion / "human-intent.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def _decisiones(p, clave=A):
    carpeta = p / ".claude" / "runtime" / "tasks" / clave / "decisions"
    return sorted(f.name for f in carpeta.glob("*.json")) if carpeta.is_dir() else []


def _prompt(p, sesion, texto):
    return W3._prompt(p, sesion, texto)


def _cli(p, *args):
    return W2._cli(p, *args)


def _aplicar(p, accion, iid, sesion, clave=A, opcion=None, valor=None):
    args = ["flujo", clave, "--" + accion, iid, "--sesion", sesion]
    if opcion is not None:
        args += ["--option", opcion]
    if valor is not None:
        args += ["--value", valor]
    return _cli(p, *args)


def _comando(accion, iid, sesion, clave=A, opcion=None):
    extra = " --option %s" % opcion if opcion else ""
    return W3._bash("%s flujo %s --%s %s%s --sesion %s" % (CLI, clave, accion, iid, extra, sesion))


def _runtime(p):
    todo = ""
    carpeta = p / ".claude" / "runtime"
    for f in (carpeta.rglob("*") if carpeta.is_dir() else []):
        if f.is_file():
            todo += f.read_text(encoding="utf-8", errors="replace")
    return todo


_borrar = W2._borrar
_sesion = W3._sesion


# -- E-01 a E-05: configuracion persistente --------------------------------------

def test_e01_persistente_no_acepta_answer(t):
    """E-01 — ANSWER sobre jira.token no crea intent ni decision; --answer sin intent falla."""
    p = W3._por_token()
    try:
        s = _sesion("e01")
        W3._vincular(p, s, A)
        iid = _iid(p, input_id="jira.token")
        t.verdadero("E-01 hay una interaccion para jira.token", iid != "ixn-0000000000000000")
        salida = _prompt(p, s, "HARNESS ANSWER %s %s algo" % (A, iid))
        t.igual("E-01 no se escribe intent", None, _intent(p, s))
        t.contiene("E-01 se dice por que", "HUMAN_ANSWER_NOT_ACCEPTED", W3._todo(salida))
        codigo, _, error = _aplicar(p, "answer", iid, s, valor="algo")
        t.verdadero("E-01 --answer sin intent falla", codigo != 0)
        t.contiene("E-01 HUMAN_INTENT_REQUIRED", "HUMAN_INTENT_REQUIRED", error)
        t.igual("E-01 sin decision record", [], _decisiones(p))
    finally:
        _borrar(p)


def test_e02_un_secreto_no_pasa(t):
    """E-02 — un token en HARNESS ANSWER o en --value no queda en el runtime ni se repite."""
    p = W3._por_token()
    try:
        s = _sesion("e02")
        W3._vincular(p, s, A)
        iid = _iid(p, input_id="jira.token")
        salida = _prompt(p, s, "HARNESS ANSWER %s %s %s" % (A, iid, SECRETO))
        t.igual("E-02 no se escribe intent", None, _intent(p, s))
        t.no_contiene("E-02 la salida del hook no repite el token", SECRETO, W3._todo(salida))
        codigo, salida_cli, error = _aplicar(p, "answer", iid, s, valor=SECRETO)
        t.verdadero("E-02 --value con un token se rechaza", codigo != 0)
        t.no_contiene("E-02 la CLI no repite el token", SECRETO, salida_cli + error)
        t.no_contiene("E-02 el token no queda en el runtime", SECRETO, _runtime(p))
    finally:
        _borrar(p)


def _con_token(p):
    env = (p / ".env").read_text(encoding="utf-8")
    (p / ".env").write_text(env.replace("JIRA_TOKEN=\n", "JIRA_TOKEN=%s\n" % W2.TOKEN_JIRA),
                            encoding="utf-8")


def test_e03_editar_y_retomar_desbloquea(t):
    """E-03 — con JIRA_TOKEN cargado, --resume reconcilia y la tarea deja de estar BLOCKED."""
    p = W3._por_token()
    try:
        t.igual("E-03 arranca BLOCKED", "BLOCKED", (_estado(p) or {}).get("status"))
        _con_token(p)
        codigo, salida, error, _ = _resume_en_proceso(p, M60.Transporte())
        t.igual("E-03 --resume sale 0", 0, codigo)
        doc = _estado(p) or {}
        t.igual("E-03 ya no esta bloqueada", ["CONTEXT", "NEW"], [doc.get("stage"), doc.get("status")])
    finally:
        _borrar(p)


def test_e04_editar_mal_sigue_bloqueado(t):
    """E-04 — con el .env todavia incompleto, --resume deja BLOCKED y vuelve a mostrar el input."""
    p = W3._por_token()
    try:
        codigo, salida, _, _ = _resume_en_proceso(p, M60.Transporte())
        t.igual("E-04 --resume sale 0", 0, codigo)
        t.igual("E-04 sigue BLOCKED", "BLOCKED", (_estado(p) or {}).get("status"))
        t.contiene("E-04 y dice que falta JIRA_TOKEN", "JIRA_TOKEN", salida)
    finally:
        _borrar(p)


def test_e05_resume_no_imprime_valores(t):
    """E-05 — ni con el token cargado ni sin el, --resume imprime un valor del .env."""
    p = W3._por_token()
    try:
        _, antes, e1, _ = _resume_en_proceso(p, M60.Transporte())
        _con_token(p)
        _, despues, e2, _ = _resume_en_proceso(p, M60.Transporte())
        todo = antes + e1 + despues + e2
        for valor in (W2.TOKEN_JIRA, W2.TOKEN_GITLAB, W2.USUARIO):
            t.no_contiene("E-05 sin %s" % valor[:10], valor, todo)
    finally:
        _borrar(p)


# -- E-06 a E-09: TASK_INPUT y repositorio -----------------------------------------

def test_e06_la_clave_de_jira_es_task_input(t):
    """E-06 — task.key es TASK_INPUT en el registro; se declara por el prompt, no por ANSWER."""
    requeridos = importlib.import_module("flujo.requeridos")
    entrada = requeridos.buscar(requeridos.cargar(), "task.key")
    t.igual("E-06 task.key es TASK_INPUT", "TASK_INPUT", (entrada or {}).get("interactionType"))
    p = W3._dos()
    try:
        s = _sesion("e06")
        salida = _prompt(p, s, "HARNESS ANSWER %s ixn-0123456789abcdef ABC-999" % A)
        t.igual("E-06 ANSWER sin interaccion abierta no crea intent", None, _intent(p, s))
        t.contiene("E-06 y dice que no esta abierta", "HUMAN_INTERACTION_NOT_OPEN", W3._todo(salida))
        _prompt(p, s, "Seguimos con ABC-456")
        t.igual("E-06 la clave se declara como en la Wave 3", B,
                (W3._binding(p, s) or {}).get("taskKey"))
    finally:
        _borrar(p)


def test_e07_task_input_de_otra_interaccion(t):
    """E-07 — ANSWER sobre repository.match o sobre un id que no existe no desbloquea."""
    p = W3._dos()
    try:
        s = _sesion("e07")
        W3._vincular(p, s, A)
        iid = _iid(p, input_id="repository.match")
        t.verdadero("E-07 hay una interaccion para repository.match", iid != "ixn-0000000000000000")
        salida = _prompt(p, s, "HARNESS ANSWER %s %s gitlab.example/grupo/repo-b" % (A, iid))
        t.igual("E-07 no se escribe intent", None, _intent(p, s))
        t.contiene("E-07 HUMAN_ANSWER_NOT_ACCEPTED", "HUMAN_ANSWER_NOT_ACCEPTED", W3._todo(salida))
        _prompt(p, s, "HARNESS ANSWER %s ixn-0123456789abcdef x" % A)
        t.igual("E-07 otro id: tampoco", None, _intent(p, s))
        codigo, _, error = _aplicar(p, "answer", iid, s, valor="x")
        t.verdadero("E-07 --answer falla", codigo != 0)
        t.igual("E-07 la tarea sigue BLOCKED", "BLOCKED", (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)


def test_e08_elegir_repositorio_para_esta_tarea(t):
    """E-08 — CHOOSE resuelve REPOSITORY_CONFLICT para la tarea y no toca el .env."""
    p = _conflicto()
    try:
        t.igual("E-08 arranca con REPOSITORY_CONFLICT", ["REPOSITORY_CONFLICT"],
                W2._codigos(_estado(p)))
        s = _sesion("e08")
        W3._vincular(p, s, A)
        iid = _iid(p, input_id="repository.unambiguous")
        opciones = next((i["options"] for i in _interacciones(p) if i["interactionId"] == iid), [])
        t.igual("E-08 las opciones son los candidatos", ["gitlab.example/grupo/repo-a",
                                                         "gitlab.example/grupo/repo-b"], opciones)
        env = (p / ".env").read_bytes()
        _prompt(p, s, "HARNESS CHOOSE %s %s gitlab.example/grupo/repo-a" % (A, iid))
        t.igual("E-08 intent CHOOSE", "CHOOSE", (_intent(p, s) or {}).get("action"))
        codigo, salida, error = _aplicar(p, "choose", iid, s, opcion="gitlab.example/grupo/repo-a")
        t.igual("E-08 --choose sale 0", 0, codigo)
        t.verdadero("E-08 sin REPOSITORY_CONFLICT", "REPOSITORY_CONFLICT" not in W2._codigos(_estado(p)))
        t.igual("E-08 el repositorio de la tarea es el elegido", "gitlab.example/grupo/repo-a",
                ((_estado(p) or {}).get("repositoryRef") or {}).get("taskRepository"))
        t.igual("E-08 el .env no cambio", env, (p / ".env").read_bytes())
    finally:
        _borrar(p)


def test_e09_cambiar_el_default_muestra_el_env(t):
    """E-09 — REPOSITORY_UNRESOLVED (GITLAB_PROJECT) muestra su lugar en el .env."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A, ficha="sin repositorio declarado")
        W3._reconciliar(p, A)
        t.verdadero("E-09 REPOSITORY_UNRESOLVED", "REPOSITORY_UNRESOLVED" in W2._codigos(_estado(p)))
        salida = W3._vincular(p, _sesion("e09"), A)
        texto = W3._todo(salida)
        t.contiene("E-09 nombra GITLAB_PROJECT", "GITLAB_PROJECT", texto)
        t.contiene("E-09 con el enlace al .env", "vscode://file/", texto)
    finally:
        _borrar(p)


# -- E-10 a E-18: la intencion y la aprobacion ------------------------------------

def test_e10_el_prompt_crea_el_intent(t):
    """E-10 — HARNESS APPROVE ABC-123 <id> crea el intent de esa sesion."""
    p = _esperando()
    try:
        t.igual("E-10 la tarea espera", "WAITING_FOR_HUMAN_APPROVAL", (_estado(p) or {}).get("status"))
        s = _sesion("e10")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        doc = _intent(p, s) or {}
        t.igual("E-10 human-intent/1.0", "human-intent/1.0", doc.get("schema_version"))
        t.igual("E-10 APPROVE sobre esa interaccion", ["APPROVE", iid, A, s, None],
                [doc.get("action"), doc.get("interactionId"), doc.get("taskKey"), doc.get("sessionId"),
                 doc.get("consumedAt")])
    finally:
        _borrar(p)


def test_e11_el_lenguaje_ambiguo_no_aprueba(t):
    """E-11 — «dale», «ok», minusculas o el comando en un parrafo no crean intent."""
    p = _esperando()
    try:
        iid = _iid(p, tipo="HUMAN_DECISION")
        for texto in ("dale", "ok", "sí, aprobá", "hacelo", "seguí",
                      "harness approve %s %s" % (A, iid),
                      "Te pido: HARNESS APPROVE %s %s por favor" % (A, iid),
                      "HARNESS APPROVE %s %s\nHARNESS CANCEL %s %s" % (A, iid, A, iid),
                      "HARNESS APPROVE %s" % A, "HARNESS APROBAR %s %s" % (A, iid)):
            s = _sesion("e11")
            _prompt(p, s, texto)
            t.igual("E-11 «%s» no crea intent" % texto.replace("\n", " / ")[:40], None, _intent(p, s))
        try:
            analizado = _H().analizar("dale")
        except Exception as e:                               # noqa: BLE001
            analizado = repr(e)
        t.igual("E-11 analizar(«dale») es None", None, analizado)
    finally:
        _borrar(p)


def test_e12_el_modelo_no_se_aprueba_solo(t):
    """E-12 — --approve sin intent: HUMAN_INTENT_REQUIRED, nada cambia, y PreToolUse lo niega."""
    p = _esperando()
    try:
        s = _sesion("e12")
        W3._vincular(p, s, A)
        iid = _iid(p, tipo="HUMAN_DECISION")
        plan, estado = (p / ".claude" / "planes" / (A + ".json")).read_bytes(), _estado(p)
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.verdadero("E-12 falla", codigo != 0)
        t.contiene("E-12 HUMAN_INTENT_REQUIRED", "HUMAN_INTENT_REQUIRED", error)
        t.igual("E-12 el plan no cambio", plan, (p / ".claude" / "planes" / (A + ".json")).read_bytes())
        t.igual("E-12 el estado no cambio", (estado or {}).get("status"), (_estado(p) or {}).get("status"))
        salida = W3._pre(p, s, *_comando("approve", iid, s))
        t.igual("E-12 PreToolUse: deny", "deny", W3._decision(salida))
        t.contiene("E-12 PreToolUse: HUMAN_INTENT_REQUIRED", "HUMAN_INTENT_REQUIRED", W3._motivo(salida))
    finally:
        _borrar(p)


def _aprobar(p, s, clave=A, iid=None):
    iid = iid or _iid(p, clave, tipo="HUMAN_DECISION")
    _prompt(p, s, "HARNESS APPROVE %s %s" % (clave, iid))
    return iid, _aplicar(p, "approve", iid, s, clave=clave)


def test_e13_aprobar_consume_una_vez(t):
    """E-13 — APPROVE valido: APPROVED, intent consumido, y la tarea retoma."""
    p = _esperando()
    try:
        s = _sesion("e13")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        t.igual("E-13 PreToolUse deja pasar el comando", None,
                W3._decision(W3._pre(p, s, *_comando("approve", iid, s))))
        codigo, salida, error = _aplicar(p, "approve", iid, s)
        t.igual("E-13 --approve sale 0", 0, codigo)
        t.igual("E-13 la aprobacion quedo APPROVED", ["APPROVED"],
                [a["status"] for a in _plan(p)["humanApprovals"]])
        t.verdadero("E-13 el intent quedo consumido", bool((_intent(p, s) or {}).get("consumedAt")))
        t.igual("E-13 la tarea retoma", ["EXECUTION", "ACTIVE"],
                [(_estado(p) or {}).get("stage"), (_estado(p) or {}).get("status")])
        t.igual("E-13 un decision record", [iid + ".json"], _decisiones(p))
    finally:
        _borrar(p)


def test_e14_un_intent_consumido_no_se_reusa(t):
    """E-14 — aplicar otra vez el mismo intent: HUMAN_INTENT_ALREADY_CONSUMED."""
    p = _esperando()
    try:
        s = _sesion("e14")
        iid, _ = _aprobar(p, s)
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.verdadero("E-14 falla", codigo != 0)
        t.contiene("E-14 HUMAN_INTENT_ALREADY_CONSUMED", "HUMAN_INTENT_ALREADY_CONSUMED", error)
        salida = W3._pre(p, s, *_comando("approve", iid, s))
        t.igual("E-14 PreToolUse: deny", "deny", W3._decision(salida))
    finally:
        _borrar(p)


def test_e15_una_aprobacion_de_otro_plan_es_vieja(t):
    """E-15 — intent sobre el plan A, aplicado con el plan B: HUMAN_DECISION_STALE."""
    p = _esperando()
    try:
        s = _sesion("e15")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        _replanificar(p)
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.verdadero("E-15 falla", codigo != 0)
        t.contiene("E-15 HUMAN_DECISION_STALE", "HUMAN_DECISION_STALE", error)
        t.igual("E-15 la tarea sigue esperando", "WAITING_FOR_HUMAN_APPROVAL",
                (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)


def test_e16_la_tarea_tiene_que_coincidir(t):
    """E-16 — un intent de ABC-123 aplicado a ABC-456: HUMAN_INTENT_TASK_MISMATCH."""
    p = _esperando()
    _esperando(clave=B, p=p)
    try:
        s = _sesion("e16")
        iid = _iid(p, A, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        codigo, _, error = _aplicar(p, "approve", iid, s, clave=B)
        t.verdadero("E-16 falla", codigo != 0)
        t.contiene("E-16 HUMAN_INTENT_TASK_MISMATCH", "HUMAN_INTENT_TASK_MISMATCH", error)
        t.igual("E-16 ABC-456 sigue esperando", "WAITING_FOR_HUMAN_APPROVAL",
                (_estado(p, B) or {}).get("status"))
    finally:
        _borrar(p)


def test_e17_la_sesion_tiene_que_coincidir(t):
    """E-17 — el intent de session-A aplicado desde session-B: HUMAN_INTENT_SESSION_MISMATCH."""
    p = _esperando()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, sa, "HARNESS APPROVE %s %s" % (A, iid))
        codigo, _, error = _aplicar(p, "approve", iid, sb)
        t.verdadero("E-17 falla", codigo != 0)
        t.contiene("E-17 HUMAN_INTENT_SESSION_MISMATCH", "HUMAN_INTENT_SESSION_MISMATCH", error)
        t.igual("E-17 el intent de A sigue sin consumir", None, (_intent(p, sa) or {}).get("consumedAt"))
    finally:
        _borrar(p)


def test_e18_la_alternativa_es_una_opcion_declarada(t):
    """E-18 — ALTERNATIVE con la opcion declarada pasa; con otra: HUMAN_OPTION_INVALID."""
    p = _esperando()
    try:
        iid = _iid(p, tipo="HUMAN_DECISION")
        opciones = next((i["options"] for i in _interacciones(p) if i["interactionId"] == iid), [])
        t.igual("E-18 la unica opcion es el tier mas barato", ["standard"], opciones)
        s = _sesion("e18")
        salida = _prompt(p, s, "HARNESS ALTERNATIVE %s %s premium" % (A, iid))
        t.igual("E-18 una opcion que no esta: sin intent", None, _intent(p, s))
        t.contiene("E-18 HUMAN_OPTION_INVALID", "HUMAN_OPTION_INVALID", W3._todo(salida))
        _prompt(p, s, "HARNESS ALTERNATIVE %s %s standard" % (A, iid))
        codigo, _, error = _aplicar(p, "alternative", iid, s, opcion="premium")
        t.verdadero("E-18 --option distinta del intent: falla", codigo != 0)
        codigo, _, error = _aplicar(p, "alternative", iid, s, opcion="standard")
        t.igual("E-18 --option standard sale 0", 0, codigo)
        plan = _plan(p)
        t.igual("E-18 la aprobacion quedo DOWNGRADED", ["DOWNGRADED"],
                [a["status"] for a in plan["humanApprovals"]])
        t.igual("E-18 la unidad corre en standard", "standard",
                plan["workUnits"][0]["modelPolicy"]["requiredTier"])
    finally:
        _borrar(p)


# -- E-19 a E-26: cancelar, replanificar, reiniciar, retomar ------------------------

def _cancelar(p, s, clave=A):
    iid = _iid(p, clave)
    _prompt(p, s, "HARNESS CANCEL %s %s" % (clave, iid))
    return iid, _aplicar(p, "cancel", iid, s, clave=clave)


def test_e19_cancelar(t):
    """E-19 — CANCEL valido: CANCELLED y ningun permiso de avance."""
    p = _esperando()
    try:
        _, (codigo, _, error) = _cancelar(p, _sesion("e19"))
        t.igual("E-19 --cancel sale 0", 0, codigo)
        doc = _estado(p) or {}
        t.igual("E-19 CANCELLED", "CANCELLED", doc.get("status"))
        permisos = W2._E().permisos(doc)
        t.igual("E-19 ningun permiso de avance", [False] * 5,
                [permisos[k] for k in W2.AVANCE])
    finally:
        _borrar(p)


def test_e20_cancelar_no_borra_evidencia(t):
    """E-20 — despues de cancelar siguen el TaskContext, el plan, la refutacion y el decision record."""
    p = _esperando()
    try:
        evidencia = p / ".claude" / "refutaciones" / A / "evidencia-previa.json"
        evidencia.parent.mkdir(parents=True, exist_ok=True)
        evidencia.write_text('{"nota": "artefacto de refutacion previo"}', encoding="utf-8")
        iid, _ = _cancelar(p, _sesion("e20"))
        t.verdadero("E-20 la refutacion sigue", evidencia.exists())
        t.verdadero("E-20 el TaskContext sigue", (p / ".claude" / "contextos" / (A + ".json")).exists())
        t.verdadero("E-20 el plan sigue", (p / ".claude" / "planes" / (A + ".json")).exists())
        t.igual("E-20 el decision record esta", [iid + ".json"], _decisiones(p))
    finally:
        _borrar(p)


def test_e21_replanificar_vuelve_a_pedir_aprobacion(t):
    """E-21 — aprobar y despues replanificar: la tarea vuelve a esperar."""
    p = _esperando()
    try:
        _aprobar(p, _sesion("e21"))
        t.igual("E-21 aprobada, retoma", "ACTIVE", (_estado(p) or {}).get("status"))
        _replanificar(p)
        t.igual("E-21 replanificada, vuelve a esperar", "WAITING_FOR_HUMAN_APPROVAL",
                (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)


def test_e22_reiniciar_conserva_la_decision(t):
    """E-22 — con state.json borrado, la decision se reconstruye: APPROVE y CANCEL."""
    p = _esperando()
    q = _esperando()
    try:
        _aprobar(p, _sesion("e22a"))
        (p / ".claude" / "runtime" / "tasks" / A / "state.json").unlink()
        t.igual("E-22 aprobada y reconstruida", ["EXECUTION", "ACTIVE"],
                [(W3._reconciliar(p, A) or {}).get(k) for k in ("stage", "status")])
        _cancelar(q, _sesion("e22c"))
        (q / ".claude" / "runtime" / "tasks" / A / "state.json").unlink()
        t.igual("E-22 cancelada y reconstruida", "CANCELLED", (W3._reconciliar(q, A) or {}).get("status"))
    finally:
        _borrar(p, q)


def test_e23_reiniciar_no_aprueba_un_intent_pendiente(t):
    """E-23 — un intent sin consumir no aprueba nada en un proceso nuevo, y otra sesion no lo ve."""
    p = _esperando()
    try:
        sa = _sesion("a")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, sa, "HARNESS APPROVE %s %s" % (A, iid))
        t.igual("E-23 reconciliado en un proceso nuevo, sigue esperando", "WAITING_FOR_HUMAN_APPROVAL",
                (W3._reconciliar(p, A) or {}).get("status"))
        sb = _sesion("b")
        salida = W3._pre(p, sb, *_comando("approve", iid, sb))
        t.igual("E-23 una sesion nueva no lo usa", "deny", W3._decision(salida))
    finally:
        _borrar(p)


def test_e24_el_id_cambia_con_el_bloqueo_o_el_plan(t):
    """E-24 — replanificar cambia el interactionId; otro bloqueo tambien."""
    p = _esperando()
    q = W3._por_token()
    try:
        antes = _iid(p, tipo="HUMAN_DECISION")
        t.igual("E-24 estable mientras no cambia nada", antes, _iid(p, tipo="HUMAN_DECISION"))
        _replanificar(p)
        t.verdadero("E-24 con otro plan, otro id", _iid(p, tipo="HUMAN_DECISION") != antes)
        token = _iid(q, input_id="jira.token")
        env = (q / ".env").read_text(encoding="utf-8")
        (q / ".env").write_text(env.replace("JIRA_TOKEN=\n", "JIRA_TOKEN=%s\n" % W2.TOKEN_JIRA).replace(
            "JIRA_USER=%s" % W2.USUARIO, "JIRA_USER="), encoding="utf-8")
        W3._reconciliar(q, A)
        usuario = _iid(q, input_id="jira.user")
        t.verdadero("E-24 otro bloqueo, otro id", usuario != token and IXN.match(usuario))
    finally:
        _borrar(p, q)


def test_e25_retoma_desde_su_compuerta(t):
    """E-25 — antes de aprobar, resumeFrom es PLANNING / plan-human-approvals; despues, EXECUTION."""
    p = _esperando()
    try:
        t.igual("E-25 retoma en la aprobacion", {"stage": "PLANNING", "gate": "plan-human-approvals"},
                (_estado(p) or {}).get("resumeFrom"))
        _aprobar(p, _sesion("e25"))
        doc = _estado(p) or {}
        t.igual("E-25 despues, la proxima compuerta", ["EXECUTION", None],
                [doc.get("stage"), doc.get("resumeFrom")])
    finally:
        _borrar(p)


def test_e26_una_respuesta_no_salta_otras(t):
    """E-26 — con dos aprobaciones, aprobar una deja la tarea esperando la otra."""
    p = _esperando(unidades=(("u1", REASONING), ("u2", REASONING)))
    try:
        abiertas = [i for i in _interacciones(p) if i.get("kind") == "HUMAN_DECISION"]
        t.igual("E-26 dos interacciones", 2, len(abiertas))
        _aprobar(p, _sesion("e26"), iid=abiertas[0]["interactionId"] if abiertas else None)
        t.igual("E-26 sigue esperando", "WAITING_FOR_HUMAN_APPROVAL", (_estado(p) or {}).get("status"))
        t.igual("E-26 queda una", 1, len([i for i in _interacciones(p) if i.get("kind") == "HUMAN_DECISION"]))
    finally:
        _borrar(p)


# -- E-27 a E-33: la compuerta, los secretos, la sesion ----------------------------

def test_e27_mientras_espera_la_compuerta_niega(t):
    """E-27 — con la tarea esperando, Write y Agent siguen en deny."""
    p = _esperando()
    try:
        s = _sesion("e27")
        W3._vincular(p, s, A)
        for herramienta in (W3._write(), ("Agent", {"prompt": "x", "subagent_type": "y"})):
            t.igual("E-27 %s deny" % herramienta[0], "deny", W3._decision(W3._pre(p, s, *herramienta)))
    finally:
        _borrar(p)


def test_e28_el_secret_guard_sigue_primero(t):
    """E-28 — un secreto alto en un comando de aplicacion es deny del Secret Guard."""
    p = _esperando()
    try:
        s = _sesion("e28")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        salida = W3._pre(p, s, *W3._bash("%s flujo %s --approve %s --sesion %s --motivo '%s'" % (
            CLI, A, iid, s, SECRETO_ALTO)))
        t.igual("E-28 deny", "deny", W3._decision(salida))
        t.contiene("E-28 y es el del secreto", "archivo externo al codigo", W3._motivo(salida))
        t.verdadero("E-28 solo el del secreto: el flujo ni se evalua",
                    not W3._motivo(salida).startswith("Flujo"))
    finally:
        _borrar(p)


def test_e29_setup_no_pregunta(t):
    """E-29 — setup y reconfigurar no leen de la consola: con stdin cerrado, terminan."""
    p = W2._proyecto()
    try:
        for args in (["setup"], ["reconfigurar", "jira"]):
            r = subprocess.run([sys.executable, str(W2.CLI)] + args + ["--proyecto", str(p)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=W2._entorno_limpio(), timeout=120)
            t.igual("E-29 %s termina sin preguntar" % args[0], 0, r.returncode)
    finally:
        _borrar(p)


def test_e30_active_task_no_autoriza(t):
    """E-30 — con el puntero en la tarea, --approve sin intent sigue siendo HUMAN_INTENT_REQUIRED."""
    p = _esperando()
    try:
        W2._P().marcar_activa(str(p), A)
        s = _sesion("e30")
        iid = _iid(p, tipo="HUMAN_DECISION")
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.contiene("E-30 HUMAN_INTENT_REQUIRED", "HUMAN_INTENT_REQUIRED", error)
        t.igual("E-30 sigue esperando", "WAITING_FOR_HUMAN_APPROVAL", (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)
    for nombre in ("human_intent.py",):
        ruta = HOOKS / "lib" / nombre
        texto = ruta.read_text(encoding="utf-8") if ruta.exists() else "active-task"
        t.verdadero("E-30 lib/%s no nombra active-task" % nombre,
                    not re.search(r"active[-_]task|ruta_activa|marcar_activa", texto))


def test_e31_dos_sesiones_no_se_consumen(t):
    """E-31 — session-B no consume el intent de session-A; A si."""
    p = _esperando()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, sa, "HARNESS APPROVE %s %s" % (A, iid))
        codigo, _, error = _aplicar(p, "approve", iid, sb)
        t.verdadero("E-31 B no puede", codigo != 0)
        codigo, _, error = _aplicar(p, "approve", iid, sa)
        t.igual("E-31 A si", 0, codigo)
    finally:
        _borrar(p)


def test_e32_e33_no_guardan_prompt_ni_secretos(t):
    """E-32 y E-33 — intent y decision record sin el prompt ni un secreto."""
    p = _esperando()
    try:
        s = _sesion("e32")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "Seguimos con ABC-123. Frase distintiva W4 con %s" % SECRETO)
        _aprobar(p, s, iid=iid)
        archivos = [p / ".claude" / "runtime" / "sessions" / s / "human-intent.json"] + [
            p / ".claude" / "runtime" / "tasks" / A / "decisions" / n for n in _decisiones(p)]
        todo = "".join(f.read_text(encoding="utf-8") for f in archivos if f.exists())
        t.verdadero("E-32 hay que mirar", len(todo) > 50)
        t.no_contiene("E-32 sin el prompt", "HARNESS APPROVE", todo)
        t.no_contiene("E-32 sin la frase", "Frase distintiva", todo)
        for valor in (SECRETO, W2.TOKEN_JIRA, W2.TOKEN_GITLAB):
            t.no_contiene("E-33 sin %s" % valor[:10], valor, todo)
    finally:
        _borrar(p)


# -- E-43 a E-47 -----------------------------------------------------------------

def test_e43_el_prompt_muestra_como_decidir(t):
    """E-43 — UserPromptSubmit sobre una tarea que espera muestra el id y la linea exacta."""
    p = _esperando()
    try:
        salida = W3._vincular(p, _sesion("e43"), A)
        texto = W3._todo(salida)
        iid = _iid(p, tipo="HUMAN_DECISION")
        t.contiene("E-43 el id", iid, texto)
        t.contiene("E-43 la linea para aprobar", "HARNESS APPROVE %s %s" % (A, iid), texto)
        t.contiene("E-43 la alternativa", "HARNESS ALTERNATIVE %s %s standard" % (A, iid), texto)
        t.contiene("E-43 cancelar", "HARNESS CANCEL %s %s" % (A, iid), texto)
    finally:
        _borrar(p)


def test_e44_la_compuerta_mira_la_sesion_del_evento(t):
    """E-44 — un --sesion que no es el del evento: deny HUMAN_INTENT_SESSION_MISMATCH."""
    p = _esperando()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, sa, "HARNESS APPROVE %s %s" % (A, iid))
        salida = W3._pre(p, sb, *_comando("approve", iid, sa))
        t.igual("E-44 deny", "deny", W3._decision(salida))
        t.contiene("E-44 HUMAN_INTENT_SESSION_MISMATCH", "HUMAN_INTENT_SESSION_MISMATCH", W3._motivo(salida))
        t.igual("E-44 desde su sesion, pasa", None, W3._decision(W3._pre(p, sa, *_comando("approve", iid, sa))))
    finally:
        _borrar(p)


def test_e45_validan_contra_sus_schemas(t):
    """E-45 — intent y decision record validan contra sus schemas."""
    p = _esperando()
    try:
        s = _sesion("e45")
        iid, _ = _aprobar(p, s)
        refutacion = importlib.import_module("orquestacion.refutacion")
        intent = _intent(p, s)
        record = json.loads((p / ".claude" / "runtime" / "tasks" / A / "decisions" / (iid + ".json")).read_text(
            encoding="utf-8")) if _decisiones(p) else None
        t.igual("E-45 human-intent/1.0", [], refutacion.validar(intent, "human-intent.schema.json")
                if intent else ["sin intent"])
        t.igual("E-45 human-decision-record/1.0", [],
                refutacion.validar(record, "human-decision-record.schema.json") if record else ["sin record"])
    finally:
        _borrar(p)


def test_e46_elegir_un_candidato_que_no_esta(t):
    """E-46 — CHOOSE con un candidato fuera de la lista: HUMAN_OPTION_INVALID, sin decision."""
    p = _conflicto()
    try:
        s = _sesion("e46")
        iid = _iid(p, input_id="repository.unambiguous")
        salida = _prompt(p, s, "HARNESS CHOOSE %s %s gitlab.example/otro/repo" % (A, iid))
        t.igual("E-46 sin intent", None, _intent(p, s))
        t.contiene("E-46 HUMAN_OPTION_INVALID", "HUMAN_OPTION_INVALID", W3._todo(salida))
        _prompt(p, s, "HARNESS CHOOSE %s %s gitlab.example/grupo/repo-a" % (A, iid))
        codigo, _, error = _aplicar(p, "choose", iid, s, opcion="gitlab.example/otro/repo")
        t.verdadero("E-46 --option fuera del intent: falla", codigo != 0)
        t.igual("E-46 sin decision record", [], _decisiones(p))
    finally:
        _borrar(p)


def test_e47_aplicar_no_sale_a_la_red(t):
    """E-47 — --approve con sockets que fallan: aplica igual."""
    p = _esperando()
    try:
        s = _sesion("e47")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        original = socket.socket

        class _SinRed(object):
            def __init__(self, *_a, **_k):
                raise AssertionError("se abrio un socket")
        socket.socket = _SinRed
        try:
            codigo, salida, error = W2._cli_en_proceso(
                ["flujo", A, "--approve", iid, "--sesion", s, "--proyecto", str(p)])
        finally:
            socket.socket = original
        t.igual("E-47 sale 0 sin red", 0, codigo)
        t.igual("E-47 aprobada", ["APPROVED"], [a["status"] for a in _plan(p)["humanApprovals"]])
    finally:
        _borrar(p)


# -- E-48 a E-51: lo que encontro la verificacion --------------------------------

def test_e48_la_autoridad_no_se_escribe_con_una_herramienta(t):
    """E-48 — con estado del flujo, ninguna herramienta que escribe toca runtime/, planes/,
    contextos/ ni refutaciones/: FLOW_AUTHORITY_PROTECTED, aunque la sesion trabaje una tarea sana.
    Leerlos si se puede. Sin estado del flujo, nada cambia."""
    p = _esperando()
    _esperando(clave=B, p=p)
    try:
        s = _sesion("e48")
        # La sesion trabaja una tarea sana: ABC-456 aprobada y en EXECUTION.
        _aprobar(p, s, clave=B)
        t.igual("E-48 la sesion trabaja una tarea en curso", "ACTIVE", (_estado(p, B) or {}).get("status"))
        intento = p / ".claude" / "runtime" / "sessions" / s / "human-intent.json"
        for tool, entrada in (
                ("Write", {"file_path": str(intento), "content": "{}"}),
                ("Write", {"file_path": str(p / ".claude" / "runtime" / "tasks" / A / "decisions" /
                                            "ixn-0000000000000000.json"), "content": "{}"}),
                ("Edit", {"file_path": str(p / ".claude" / "planes" / (A + ".json")),
                          "old_string": "PENDING", "new_string": "APPROVED"}),
                ("Write", {"file_path": str(p / ".claude" / "contextos" / (A + ".json")), "content": "{}"}),
                W3._bash("python -c \"open('.claude/runtime/tasks/ABC-123/decisions/x.json','w')\""),
                W3._bash("rm .claude/runtime/tasks/ABC-123/decisions/*.json"),
                W3._bash("cp falso.json .claude/runtime/sessions/%s/human-intent.json" % s),
                W3._ps("Set-Content .claude\\planes\\ABC-123.json '{}'")):
            salida = W3._pre(p, s, tool, entrada)
            rotulo = entrada.get("command") or entrada.get("file_path")
            t.igual("E-48 %s %s: deny" % (tool, str(rotulo)[-40:]), "deny", W3._decision(salida))
            t.contiene("E-48 %s %s: FLOW_AUTHORITY_PROTECTED" % (tool, str(rotulo)[-40:]),
                       "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida))
        for tool, entrada in (W3._bash("cat .claude/runtime/tasks/ABC-123/state.json"),
                              ("Read", {"file_path": str(p / ".claude" / "planes" / (A + ".json"))})):
            t.igual("E-48 leer %s: pasa" % tool, None, W3._decision(W3._pre(p, s, tool, entrada)))
        t.igual("E-48 ABC-123 sigue esperando", "WAITING_FOR_HUMAN_APPROVAL",
                (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)
    vacio = W2._proyecto()
    try:
        salida = W3._pre(vacio, _sesion("e48v"), "Write",
                         {"file_path": str(vacio / ".claude" / "runtime" / "algo.json"), "content": "{}"})
        t.igual("E-48 sin estado del flujo: nada cambia", None, W3._decision(salida))
    finally:
        _borrar(vacio)


def test_e49_un_flag_repetido_no_se_resuelve(t):
    """E-49 — dos --sesion (PreToolUse leeria uno y la CLI otro): UNRESOLVED, deny."""
    p = _esperando()
    try:
        sa, sb = _sesion("a"), _sesion("b")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, sa, "HARNESS APPROVE %s %s" % (A, iid))
        salida = W3._pre(p, sa, *W3._bash("%s flujo %s --approve %s --sesion %s --sesion %s" % (
            CLI, A, iid, sa, sb)))
        t.igual("E-49 deny", "deny", W3._decision(salida))
        try:
            clase = W3._TP().clasificar(*W3._bash("%s flujo %s --approve %s --sesion %s --sesion %s" % (
                CLI, A, iid, sa, sb)))["class"]
        except Exception as e:                               # noqa: BLE001
            clase = repr(e)
        t.igual("E-49 UNRESOLVED_TOOL_CLASS", "UNRESOLVED_TOOL_CLASS", clase)
    finally:
        _borrar(p)


def test_e50_consumir_es_atomico(t):
    """E-50 — dos aplicaciones a la vez del mismo intent: una sola sale 0."""
    p = _esperando()
    try:
        s = _sesion("e50")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS CANCEL %s %s" % (A, iid))
        procesos = [subprocess.Popen([sys.executable, str(W2.CLI), "flujo", A, "--cancel", iid, "--sesion",
                                      s, "--proyecto", str(p)], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, env=W2._entorno_limpio()) for _ in range(4)]
        codigos = [pr.wait(timeout=120) for pr in procesos]
        t.igual("E-50 una sola aplicacion sale 0", 1, codigos.count(0))
        t.igual("E-50 un solo decision record", [iid + ".json"], _decisiones(p))
    finally:
        _borrar(p)


class _Interaccion(object):
    """Un flujo.interaccion de mentira, con una interaccion que si acepta ANSWER."""

    def __init__(self, sensibilidad):
        self.sensibilidad = sensibilidad

    def interacciones(self, proyecto, clave):
        return [{"interactionId": "ixn-00000000000000aa", "kind": "TASK_INPUT", "inputId": "x.y",
                 "actions": ["ANSWER", "RESUME", "CANCEL"], "options": [],
                 "sensitivity": self.sensibilidad}]

    def buscar(self, abiertas, iid):
        return next((i for i in abiertas if i["interactionId"] == iid), None)

    def huella_de_estado(self, doc):
        return None

    def huella_del_plan(self, plan):
        return None

    def _plan(self, proyecto, clave):
        return None


class _Estado(object):
    def leer(self, proyecto, clave):
        return None, None


def test_e51_answer_rechaza_un_secreto(t):
    """E-51 — un ANSWER sobre un input SECRET, o con un valor con forma de secreto, no se registra;
    uno publico si, con su valor."""
    p = W2._proyecto()
    try:
        H = _H()
        casos = (("SECRET", "valor-corto", None), ("PUBLIC_CONFIG", SECRETO, None),
                 ("PUBLIC_CONFIG", "valor-corto", "valor-corto"))
        for sensibilidad, valor, esperado in casos:
            s = _sesion("e51")
            try:
                H.registrar(str(p), s, "HARNESS ANSWER %s ixn-00000000000000aa %s" % (A, valor), _Estado(),
                            _Interaccion(sensibilidad))
                doc = _intent(p, s)
            except Exception as e:                           # noqa: BLE001
                doc = {"value": repr(e)}
            t.igual("E-51 %s / %s" % (sensibilidad, valor[:6]), esperado, (doc or {}).get("value"))
        t.no_contiene("E-51 el secreto no queda en el runtime", SECRETO, _runtime(p))
    finally:
        _borrar(p)


# -- E-52 a E-55: lo que encontro la segunda pasada -------------------------------

def _dos_con_una_que_espera(s):
    """ABC-123 esperando una aprobacion; ABC-456 aprobada y en curso, que es la de la sesion."""
    p = _esperando()
    _esperando(clave=B, p=p)
    _aprobar(p, s, clave=B)
    W3._vincular(p, s, B)
    return p


def test_e52_una_ruta_no_normalizada_tambien_es_autoridad(t):
    """E-52 — ./, //, x/.., un punto final, mayusculas o barras mezcladas: deny igual."""
    s = _sesion("e52")
    p = _dos_con_una_que_espera(s)
    try:
        base = str(p)
        destino = "runtime/sessions/%s/human-intent.json" % s
        for forma in (base + "/.claude/./" + destino, base + "/.claude//" + destino,
                      base + "/.claude/x/../" + destino, base + "/.claude./" + destino,
                      base + "\\.CLAUDE\\RUNTIME\\sessions\\" + s + "\\human-intent.json",
                      ".claude/./" + destino):
            salida = W3._pre(p, s, "Write", {"file_path": forma, "content": "{}"})
            t.igual("E-52 %s: deny" % forma[-48:], "deny", W3._decision(salida))
            t.contiene("E-52 %s: FLOW_AUTHORITY_PROTECTED" % forma[-48:], "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida))
        t.igual("E-52 un archivo comun sigue pasando", None,
                W3._decision(W3._pre(p, s, *W3._write("src/app.py"))))
    finally:
        _borrar(p)


def test_e53_con_una_decision_pendiente_el_shell_solo_lee(t):
    """E-53 — mientras alguna tarea espera a una persona, en cualquier sesion el shell solo lee o
    corre el Harness: cd + redireccion, un script, Set-Location + Set-Content, npm test: deny
    FLOW_HUMAN_DECISION_PENDING. Resuelta la decision, vuelve a pasar."""
    s = _sesion("e53")
    p = _dos_con_una_que_espera(s)
    try:
        destino = "runtime/sessions/%s/human-intent.json" % s
        for tool, entrada in (W3._bash("cd tmp && echo x > forja.txt"),
                              W3._bash("python tmp/forja.py"), W3._bash("npm test"),
                              W3._ps("Set-Location tmp; Set-Content -Path forja.txt -Value x"),
                              W3._bash("echo hola > notas.txt")):
            salida = W3._pre(p, s, tool, entrada)
            t.igual("E-53 %s: deny" % entrada["command"][:40], "deny", W3._decision(salida))
            t.contiene("E-53 %s: FLOW_HUMAN_DECISION_PENDING" % entrada["command"][:40],
                       "FLOW_HUMAN_DECISION_PENDING", W3._motivo(salida))
        for tool, entrada in (W3._bash("git status"), W3._harness("flujo %s --status" % A),
                              W3._write("src/app.py")):
            t.igual("E-53 %s: pasa" % (entrada.get("command") or tool)[:40], None,
                    W3._decision(W3._pre(p, s, tool, entrada)))
        _cancelar(p, _sesion("e53c"))
        t.igual("E-53 resuelta la decision, npm test vuelve a pasar", None,
                W3._decision(W3._pre(p, s, *W3._bash("npm test"))))
    finally:
        _borrar(p)


def test_e54_un_candado_viejo_no_traba_la_sesion(t):
    """E-54 — un candado de consumo huerfano de hace mas de 60 s se reclama; uno fresco no."""
    import time
    p = _esperando()
    try:
        s = _sesion("e54")
        iid = _iid(p, tipo="HUMAN_DECISION")
        _prompt(p, s, "HARNESS APPROVE %s %s" % (A, iid))
        candado = p / ".claude" / "runtime" / "sessions" / s / "human-intent.json.lock"
        candado.write_text("", encoding="utf-8")
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.verdadero("E-54 con un candado fresco no se consume", codigo != 0)
        t.igual("E-54 y el intent sigue sin consumir", None, (_intent(p, s) or {}).get("consumedAt"))
        viejo = time.time() - 120
        os.utime(str(candado), (viejo, viejo))
        codigo, _, error = _aplicar(p, "approve", iid, s)
        t.igual("E-54 con un candado viejo, se reclama y aplica", 0, codigo)
    finally:
        _borrar(p)


def test_e55_las_interacciones_dicen_su_sensibilidad(t):
    """E-55 — una interaccion real de un input secreto declara SECRET."""
    p = W3._por_token()
    try:
        i = next((x for x in _interacciones(p) if x.get("inputId") == "jira.token"), {})
        t.igual("E-55 jira.token es SECRET", "SECRET", i.get("sensitivity"))
        u = next((x for x in _interacciones(p) if x.get("inputId") == "jira.user"), None)
        if u is not None:
            t.igual("E-55 jira.user no es SECRET", "PUBLIC_CONFIG", u.get("sensitivity"))
    finally:
        _borrar(p)


# -- E-56: .claude/ y .git/ enteros ------------------------------------------------

def test_e56_claude_y_git_no_se_escriben_con_una_herramienta(t):
    """E-56 — con estado del flujo, ninguna herramienta escribe en .claude/** ni .git/**: ni la
    configuracion de git (core.fsmonitor), ni la CLI o los hooks instalados, ni los settings. La CLI
    reconocida, leer, .gitignore y .github/ siguen pasando. Sin estado del flujo, nada cambia."""
    s = _sesion("e56")
    p = _dos_con_una_que_espera(s)
    try:
        base = str(p)
        for tool, entrada in (
                ("Write", {"file_path": base + "/.git/config", "content": "[core]\n"}),
                ("Edit", {"file_path": base + "/.git/config", "old_string": "[core]",
                          "new_string": "[core]\n\tfsmonitor = x"}),
                ("Write", {"file_path": base + "/.git/hooks/pre-commit", "content": "x"}),
                ("Write", {"file_path": base + "/.claude/harness/bin/desarrollo/dev-harness.py",
                           "content": "x"}),
                ("Write", {"file_path": base + "/.claude/harness/hooks/lib/flow_gate.py", "content": "x"}),
                ("Write", {"file_path": base + "/.claude/settings.json", "content": "{}"}),
                ("Write", {"file_path": ".claude/settings.local.json", "content": "{}"}),
                W3._bash("echo x >> .git/config"), W3._bash("cd .claude && echo x > y.txt"),
                W3._ps("Set-Content .git\\config 'x'")):
            salida = W3._pre(p, s, tool, entrada)
            rotulo = str(entrada.get("command") or entrada.get("file_path"))[-40:]
            t.igual("E-56 %s %s: deny" % (tool, rotulo), "deny", W3._decision(salida))
            t.contiene("E-56 %s %s: FLOW_AUTHORITY_PROTECTED" % (tool, rotulo),
                       "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida))
        for tool, entrada in (W3._write(".gitignore"), W3._write(".github/workflows/ci.yml"),
                              W3._bash("cat .git/config"), W3._harness("flujo %s --status" % A),
                              W3._harness("flujo %s --status" % B)):
            rotulo = str(entrada.get("command") or entrada.get("file_path"))[-40:]
            t.igual("E-56 %s %s: pasa" % (tool, rotulo), None, W3._decision(W3._pre(p, s, tool, entrada)))
    finally:
        _borrar(p)
    vacio = W2._proyecto()
    try:
        t.igual("E-56 sin estado del flujo: .git/config se puede escribir", None, W3._decision(W3._pre(
            vacio, _sesion("e56v"), "Write", {"file_path": str(vacio / ".git" / "config"), "content": "x"})))
    finally:
        _borrar(vacio)



def test_e56b_separadores_pegados_tambien(t):
    """E-56 — sin decision pendiente, con una sola tarea en curso: `cd .claude;`, `cd .claude&&`,
    `cd .git;`, `Set-Location .claude;` tambien son deny FLOW_AUTHORITY_PROTECTED."""
    p = _esperando()
    try:
        s = _sesion("e56b")
        _aprobar(p, s)
        t.igual("E-56b una sola tarea, en curso", "ACTIVE", (_estado(p) or {}).get("status"))
        for tool, entrada in (W3._bash("cd .claude; echo x > y.txt"), W3._bash("cd .claude&&echo x > y.txt"),
                              W3._bash("cd .git; echo x > y.txt"),
                              W3._bash("cd .CLAUDE; echo x > y.txt"),
                              W3._ps("Set-Location .claude; Set-Content -Path y.txt -Value x"),
                              W3._ps("Set-Location .git\\hooks; Set-Content -Path pre-commit -Value x")):
            salida = W3._pre(p, s, tool, entrada)
            t.igual("E-56b %s: deny" % entrada["command"][:40], "deny", W3._decision(salida))
            t.contiene("E-56b %s: FLOW_AUTHORITY_PROTECTED" % entrada["command"][:40],
                       "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida))
        for tool, entrada in (W3._bash("cd .github; ls"), W3._bash("echo x > .gitignore.bak"),
                              W3._bash("cd .claude|cat"),
                              W3._bash("cat .claude/runtime/tasks/ABC-123/state.json")):
            t.igual("E-56b %s: pasa" % entrada["command"][:40], None, W3._decision(W3._pre(p, s, tool, entrada)))
    finally:
        _borrar(p)


# -- E-57 a E-64: la aceptacion manual de la configuracion persistente -------------
#
# Bug A: el hook aplica el estado guardado y `flujo --status` mostraba solo el derivado.
# Bug B: retomar despues de editar el .env no revalidaba el registro de capacidades.

M60 = _cargar("caso_60_para_64", RAIZ / "tests" / "casos" / "60_entorno_primero.py")


def _resume_en_proceso(p, transporte):
    """--resume en proceso, con un Jira falso. (codigo, stdout, stderr, pedidos a input/getpass)."""
    return M60._cli(["flujo", A, "--resume", "--proyecto", str(p)], transporte)


def _capacidades(p):
    ruta = p / ".claude" / "harness.capacidades.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _estado_jira(p):
    return ((_capacidades(p).get("integraciones") or {}).get("jira") or {}).get("estado")


def test_e57_hook_y_status_dicen_el_mismo_bloqueo(t):
    """E-57 — con jira.token pendiente, y despues con el .env ya editado pero sin retomar, el hook y
    `flujo --status` dicen lo mismo: bloqueada por JIRA_NOT_CONFIGURED, y que falta retomar."""
    p = W3._por_token()
    try:
        s = _sesion("e57")
        hook = W3._contexto(_prompt(p, s, "Seguimos con ABC-123"))
        _, status, _ = _cli(p, "flujo", A, "--status")
        for rotulo, texto in (("hook", hook), ("status", status)):
            t.contiene("E-57 antes, %s: JIRA_NOT_CONFIGURED" % rotulo, "JIRA_NOT_CONFIGURED", texto)
        _con_token(p)
        hook = W3._todo(_prompt(p, s, "listo, ya lo guardé"))
        _, status, _ = _cli(p, "flujo", A, "--status")
        for rotulo, texto in (("hook", hook), ("status", status)):
            t.contiene("E-57 editado sin retomar, %s: sigue JIRA_NOT_CONFIGURED" % rotulo,
                       "JIRA_NOT_CONFIGURED", texto)
            t.contiene("E-57 editado sin retomar, %s: dice que falta retomar" % rotulo, "--resume", texto)
        t.contiene("E-57 el status dice lo que aplica la compuerta", "BLOCKED", status)
        t.contiene("E-57 el hook dice que el valor ya esta cargado", "ya está cargado", hook)
        t.contiene("E-57 el status dice que revalidar lo cambia", "Revalidado ahora", status)
    finally:
        _borrar(p)


def test_e58_retomar_revalida_el_registro(t):
    """E-58 — editar el .env y retomar revalida Jira por el camino de siempre (el bootstrap de
    `estado`/`reconfigurar`): el registro de capacidades queda AVAILABLE y jira.token desaparece,
    sin correr `reconfigurar` a mano."""
    p = W3._por_token()
    try:
        _con_token(p)
        transporte = M60.Transporte()
        codigo, salida, error, pedidos = _resume_en_proceso(p, transporte)
        t.igual("E-58 --resume sale 0", 0, codigo)
        t.verdadero("E-58 se revalido Jira (myself)", any("/rest/api/3/myself" in u for u in transporte.urls()))
        t.igual("E-58 el registro quedo AVAILABLE", "AVAILABLE", _estado_jira(p))
        doc = _estado(p) or {}
        t.verdadero("E-58 sin jira.token", "jira.token" not in [b["inputId"] for b in doc.get("blockedOn") or []])
        t.igual("E-58 CONTEXT / NEW", ["CONTEXT", "NEW"], [doc.get("stage"), doc.get("status")])
        t.igual("E-58 sin preguntar por consola", [], pedidos)
    finally:
        _borrar(p)


def test_e59_una_conexion_que_falla_es_un_bloqueo_nuevo(t):
    """E-59 — si la sonda da CONNECTION_FAILED, jira.token desaparece y la tarea sigue bloqueada,
    ahora por CONNECTION_FAILED."""
    p = W3._por_token()
    try:
        _con_token(p)
        codigo, salida, error, _ = _resume_en_proceso(p, M60.Transporte({"/rest/api/3/myself": (500, "")}))
        t.igual("E-59 --resume sale 0", 0, codigo)
        t.igual("E-59 el registro dice CONNECTION_FAILED", "CONNECTION_FAILED", _estado_jira(p))
        doc = _estado(p) or {}
        codigos = W2._codigos(doc)
        t.verdadero("E-59 sin JIRA_NOT_CONFIGURED", "JIRA_NOT_CONFIGURED" not in codigos)
        t.igual("E-59 bloqueada por CONNECTION_FAILED", ["BLOCKED", ["CONNECTION_FAILED"]],
                [doc.get("status"), codigos])
        t.contiene("E-59 y lo dice", "CONNECTION_FAILED", salida)
    finally:
        _borrar(p)


def test_e60_resolver_un_input_no_salta_otros(t):
    """E-60 — con jira.token y jira.user pendientes, cargar solo el token y retomar deja jira.user."""
    env = W2.ENV_COMPLETO.replace("JIRA_TOKEN=%s" % W2.TOKEN_JIRA, "JIRA_TOKEN=").replace(
        "JIRA_USER=%s" % W2.USUARIO, "JIRA_USER=")
    p = W3._por_token(env=env)
    try:
        _con_token(p)
        _resume_en_proceso(p, M60.Transporte())
        entradas = [b["inputId"] for b in (_estado(p) or {}).get("blockedOn") or []]
        t.verdadero("E-60 jira.token se resolvio", "jira.token" not in entradas)
        t.verdadero("E-60 jira.user sigue", "jira.user" in entradas)
        t.igual("E-60 sigue BLOCKED", "BLOCKED", (_estado(p) or {}).get("status"))
    finally:
        _borrar(p)


def test_e61_retomar_no_imprime_ni_guarda_el_valor(t):
    """E-61 — --resume no imprime el token ni lo deja en el runtime."""
    p = W3._por_token()
    try:
        _con_token(p)
        codigo, salida, error, _ = _resume_en_proceso(p, M60.Transporte())
        t.no_contiene("E-61 stdout/stderr sin el token", W2.TOKEN_JIRA, salida + error)
        t.no_contiene("E-61 runtime sin el token", W2.TOKEN_JIRA, _runtime(p))
        t.no_contiene("E-61 el registro sin el token", W2.TOKEN_JIRA, json.dumps(_capacidades(p)))
    finally:
        _borrar(p)


def test_e62_retomar_no_debilita_tls(t):
    """E-62 — nada de lo que corre --resume apaga la verificacion de certificados."""
    prohibido = re.compile(r"verify\s*=\s*False|CERT_NONE|_create_unverified_context|check_hostname\s*=\s*False")
    archivos = sorted((BIN / "integraciones").glob("*.py")) + [
        BIN / "estado_de_tarea" / "decisiones.py", BIN / "flujo" / "estado.py", W2.CLI]
    for archivo in archivos:
        t.igual("E-62 %s no debilita TLS" % archivo.name, [], prohibido.findall(archivo.read_text(encoding="utf-8")))


def test_e63_retomar_no_pregunta(t):
    """E-63 — --resume, como setup y reconfigurar, no lee de la consola."""
    p = W3._por_token()
    try:
        _con_token(p)
        _, _, _, pedidos = _resume_en_proceso(p, M60.Transporte())
        t.igual("E-63 ni input ni getpass", [], pedidos)
    finally:
        _borrar(p)


def test_e64_el_camino_de_retomar_es_resume(t):
    """E-64 — el bloque de un input persistente y HARNESS RESUME mandan a `flujo --resume`, no a
    `contexto`."""
    p = W3._por_token()
    try:
        s = _sesion("e64")
        bloque = W3._todo(_prompt(p, s, "Seguimos con ABC-123"))
        t.contiene("E-64 el bloque revalida con --resume", "flujo %s --resume" % A, bloque)
        t.no_contiene("E-64 y no con contexto", "contexto %s" % A, bloque)
        retomar = W3._todo(_prompt(p, s, "HARNESS RESUME %s" % A))
        t.contiene("E-64 HARNESS RESUME manda a --resume", "flujo %s --resume" % A, retomar)
    finally:
        _borrar(p)



def test_e65_otro_bloqueo_no_sale_a_la_red(t):
    """E-65 — --resume sobre un bloqueo que no es de una integracion (REPOSITORY_MISMATCH) no hace
    ninguna sonda: solo reconcilia."""
    p = W3._dos()
    try:
        transporte = M60.Transporte()
        codigo, salida, error, _ = M60._cli(["flujo", A, "--resume", "--proyecto", str(p)], transporte)
        t.igual("E-65 --resume sale 0", 0, codigo)
        t.igual("E-65 ninguna llamada a una integracion", [], transporte.urls())
        t.contiene("E-65 sigue bloqueada por el repositorio", "REPOSITORY_MISMATCH", salida)
    finally:
        _borrar(p)


def test_e66_un_programa_de_lectura_que_escribe_no_es_lectura(t):
    """E-66 — `sort -uo`, `sort -o<ruta>`, `sort --out=`, `uniq <entrada> <salida>`, `find -fprint0`,
    `tree -o` y `file -C` escriben: sobre .claude/ o .git/ son deny FLOW_AUTHORITY_PROTECTED, en modo
    pendiente y fuera de el. Leer con esos mismos programas sigue pasando."""
    intent = ".claude/runtime/sessions/x/human-intent.json"
    escriben = (W3._bash("echo '{}' | sort -uo %s" % intent), W3._bash("echo x | sort -o%s" % intent),
                W3._bash("echo x | sort --out=%s" % intent), W3._bash("echo '[core]' | sort -uo .git/config"),
                W3._bash("uniq README.md .git/config"), W3._bash("uniq -c README.md %s" % intent),
                W3._bash("find . -maxdepth 0 -fprint0 %s" % intent), W3._bash("tree -o .git/config"),
                W3._bash("tree -no .git/config"), W3._bash("file -C -m .claude/magia"),
                W3._ps("sort -uo .git\\config README.md"))
    leen = (W3._bash("sort .claude/runtime/tasks/ABC-123/state.json"),
            W3._bash("sort -u .git/config"), W3._bash("uniq .git/config"),
            W3._bash("uniq -c .claude/planes/ABC-123.json"), W3._bash("find .claude -name '*.json'"),
            W3._bash("tree .claude"), W3._bash("file .git/config"))
    s = _sesion("e66")
    pendiente = _dos_con_una_que_espera(s)
    activa = _esperando()
    try:
        _aprobar(activa, _sesion("e66a"))
        for nombre, p in (("pendiente", pendiente), ("activa", activa)):
            for tool, entrada in escriben:
                salida = W3._pre(p, s, tool, entrada)
                rotulo = "E-66 %s %s" % (nombre, entrada["command"][:44])
                t.igual(rotulo + ": deny", "deny", W3._decision(salida))
                t.contiene(rotulo + ": FLOW_AUTHORITY_PROTECTED", "FLOW_AUTHORITY_PROTECTED",
                           W3._motivo(salida))
            for tool, entrada in leen:
                t.igual("E-66 %s %s: pasa" % (nombre, entrada["command"][:44]), None,
                        W3._decision(W3._pre(p, s, tool, entrada)))
    finally:
        _borrar(pendiente)
        _borrar(activa)


# -- E-67 a E-71: --status y --status --json leen la misma autoridad --------------

def _status_json(p):
    """(codigo, documento o None, stderr) de `flujo --status --json`, en un proceso nuevo."""
    codigo, salida, error = _cli(p, "flujo", A, "--status", "--json")
    try:
        doc = json.loads(salida) if salida.strip() else None
    except ValueError:
        doc = None
    return codigo, doc, error


def _guardado_crudo(p):
    ruta = p / ".claude" / "runtime" / "tasks" / A / "state.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def test_e67_status_json_y_compuerta_ven_lo_mismo(t):
    """E-67 — guardado BLOCKED por jira.token, el .env ya con el valor, sin --resume: el texto, el
    JSON y la compuerta dicen BLOCKED; el JSON es el state.json tal cual."""
    p = W3._por_token()
    try:
        _con_token(p)
        _, texto, _ = _cli(p, "flujo", A, "--status")
        codigo, doc, _ = _status_json(p)
        doc = doc or {}
        t.contiene("E-67 el texto dice BLOCKED", "(BLOCKED)", texto)
        t.igual("E-67 --json sale 0", 0, codigo)
        t.igual("E-67 el JSON dice BLOCKED", ["CONTEXT", "BLOCKED"], [doc.get("stage"), doc.get("status")])
        t.igual("E-67 el JSON tiene el mismo bloqueo", ["JIRA_NOT_CONFIGURED"], W2._codigos(doc))
        t.igual("E-67 el JSON es el state.json tal cual", _guardado_crudo(p), doc)
        t.verdadero("E-67 nunca NEW sin bloqueos mientras lo guardado esta bloqueado",
                    not (doc.get("status") == "NEW" and not doc.get("blockedOn")))
        s = _sesion("e67")
        salida = W3._pre(p, s, *W3._write("src/app.py"))
        t.igual("E-67 la compuerta niega", "deny", W3._decision(salida))
        t.contiene("E-67 por el mismo bloqueo", "JIRA_NOT_CONFIGURED", W3._motivo(salida))
    finally:
        _borrar(p)


def test_e68_status_json_valida_contra_su_schema(t):
    """E-68 — --status --json es task-flow-state/1.0 valido, sin campos de mas."""
    p = W3._por_token()
    try:
        _con_token(p)
        _, doc, _ = _status_json(p)
        doc = doc or {}
        t.igual("E-68 schema_version", "task-flow-state/1.0", doc.get("schema_version"))
        t.igual("E-68 valida contra el schema", [], W2._E().validar(doc) if doc else ["vacio"])
    finally:
        _borrar(p)


def test_e69_status_json_no_revalida(t):
    """E-69 — --status --json no sale a la red, no toca el registro ni el estado, no muestra el valor."""
    p = W3._por_token()
    try:
        _con_token(p)
        estado_antes = (p / ".claude" / "runtime" / "tasks" / A / "state.json").read_bytes()
        registro = p / ".claude" / "harness.capacidades.json"
        registro_antes = registro.read_bytes() if registro.exists() else None
        transporte = M60.Transporte()
        codigo, salida, error, pedidos = M60._cli(["flujo", A, "--status", "--json", "--proyecto", str(p)],
                                                  transporte)
        t.igual("E-69 sale 0", 0, codigo)
        t.igual("E-69 ninguna llamada a una integracion", [], transporte.urls())
        t.igual("E-69 el state.json no cambio",
                estado_antes, (p / ".claude" / "runtime" / "tasks" / A / "state.json").read_bytes())
        t.igual("E-69 el registro de capacidades no cambio", registro_antes,
                registro.read_bytes() if registro.exists() else None)
        t.verdadero("E-69 el valor no aparece", W2.TOKEN_JIRA not in salida + error)
        t.igual("E-69 sin preguntar por consola", [], pedidos)
    finally:
        _borrar(p)


def test_e70_despues_de_retomar_los_dos_muestran_lo_nuevo(t):
    """E-70 — despues de --resume, el texto y el JSON muestran el estado nuevo persistido."""
    p = W3._por_token()
    try:
        _con_token(p)
        _resume_en_proceso(p, M60.Transporte({"/rest/api/3/myself": (500, "")}))
        _, texto, _ = _cli(p, "flujo", A, "--status")
        _, doc, _ = _status_json(p)
        doc = doc or {}
        t.contiene("E-70 el texto dice jira.availability", "jira.availability (CONNECTION_FAILED)", texto)
        t.igual("E-70 el JSON dice CONNECTION_FAILED", ["BLOCKED", ["CONNECTION_FAILED"]],
                [doc.get("status"), W2._codigos(doc)])
        t.igual("E-70 el JSON dice jira.availability", ["jira.availability"],
                [b.get("inputId") for b in doc.get("blockedOn") or []])
        t.igual("E-70 es el state.json nuevo", _guardado_crudo(p), doc)
        t.verdadero("E-70 sin vista previa: lo guardado ya es lo de ahora", "Revalidado ahora" not in texto)
    finally:
        _borrar(p)


def test_e71_sin_estado_guardado_no_hay_documento(t):
    """E-71 — sin state.json, o con uno roto, --status --json sale con 2 y dice el codigo; el texto
    lo dice y rotula lo derivado como no aplicado."""
    p = W2._proyecto()
    try:
        codigo, doc, error = _status_json(p)
        t.igual("E-71 sin estado: sale 2", 2, codigo)
        t.igual("E-71 sin estado: sin documento", None, doc)
        t.contiene("E-71 sin estado: TASK_FLOW_STATE_MISSING", "TASK_FLOW_STATE_MISSING", error)
        t.verdadero("E-71 --status no lo creo", not (p / ".claude" / "runtime" / "tasks" / A / "state.json").exists())
        _, texto, _ = _cli(p, "flujo", A, "--status")
        t.contiene("E-71 el texto dice que falta", "TASK_FLOW_STATE_MISSING", texto)
        t.contiene("E-71 el texto rotula lo derivado", "no aplicado", texto)
    finally:
        _borrar(p)
    p = W3._por_token()
    try:
        (p / ".claude" / "runtime" / "tasks" / A / "state.json").write_text("{roto", encoding="utf-8")
        codigo, doc, error = _status_json(p)
        t.igual("E-71 roto: sale 2", 2, codigo)
        t.igual("E-71 roto: sin documento", None, doc)
        t.contiene("E-71 roto: TASK_FLOW_STATE_INVALID", "TASK_FLOW_STATE_INVALID", error)
    finally:
        _borrar(p)
