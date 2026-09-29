# Flow Governance, Wave 1: precondiciones del flujo, identidad del repositorio y localizador.
#
# Spec: docs/cambios/flujo-precondiciones/spec.md. Cada test nombra su escenario E-nn, que es el
# W1-0nn de la Wave con el mismo numero. E-20 es la suite misma.
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
CLI = BIN / "dev-harness.py"
FLUJO = BIN / "flujo"
REGISTRO = RAIZ / "harnesses" / "desarrollo" / "reglas" / "flow-required-inputs.json"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from flujo import entrada_humana as EH                    # noqa: E402
from flujo import precondiciones as P                     # noqa: E402
from flujo import repositorio as REPO                     # noqa: E402
from flujo import requeridos as REQ                       # noqa: E402
from integraciones import entorno                         # noqa: E402
from orquestacion import plan as orq_plan                 # noqa: E402
from orquestacion import refutacion as R                  # noqa: E402

CLAVE = "GCBA-61"
URL = "https://gitlab.example/grupo/proyecto"
TOKEN = "glpat-" + "Z9y8X7w6V5u4T3s2R1q0"
JIRA = "ATATT3xFfGF0" + "q1w2e3r4t5y6u7i8o9p0"
BASE = "https://jira.example.atlassian.net"
USUARIO = "persona.de.prueba@example.com"
GITLAB = {"gitlabProyecto": "grupo/proyecto", "baseUrl": "https://gitlab.example"}


# -- el proyecto de prueba -----------------------------------------------------

def _tmp(prefijo):
    ruta = Path(tempfile.gettempdir()) / ("%s-%s" % (prefijo, uuid.uuid4().hex[:8]))
    ruta.mkdir(parents=True)
    return ruta


def _escribir(ruta, texto):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(texto.encode("utf-8"))


def _git(carpeta, *args):
    subprocess.run(["git", "-C", str(carpeta)] + list(args), stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, check=True)


def _repo(*remotos, git=True):
    """Una carpeta con `git init` y estos remotos. Ninguno existe: nadie sale a la red."""
    carpeta = _tmp("harness-fl")
    if git:
        _git(carpeta, "init", "-q")
        for i, url in enumerate(remotos):
            _git(carpeta, "remote", "add", "origin" if i == 0 else "otro%d" % i, url)
    return carpeta


def _borrar(*carpetas):
    for c in carpetas:
        shutil.rmtree(str(c), ignore_errors=True)


def _tc(ficha="", clave=CLAVE, **extra):
    """Un TaskContext con su hash bien calculado."""
    doc = {"meta": {"schema_version": "task-context/1.0", "context_id": "tsk_" + clave,
                    "context_hash": "", "generated_at": "2026-09-29T10:00:00",
                    "harness_version": "0.26.0", "task_key": clave, "capabilities_used": []},
           "sources": [],
           "task": {"key": clave, "type": "Historia de Usuario", "title": "Filtro por fecha",
                    "acceptance_criteria": ["Filtra por rango"]},
           "project": {"ficha": {"key": "GCBA-7", "summary": ficha, "rules": ["r"]}},
           "documentation": {"items": []},
           "repository": {"project": {"id": "", "name": "grupo/proyecto", "web_url": "",
                                      "default_branch": ""}},
           "gaps_and_conflicts": {"missing": [], "conflicts": [], "missing_capabilities": [],
                                  "redacted_secrets": [], "unresolved_questions": []}}
    doc.update(extra)
    doc["meta"]["context_hash"] = R._armador().hash_de(doc)
    return doc


def _todo_resuelto(**cambios):
    """Los hechos de PLANNING con todo resuelto, y un repositorio MATCHED."""
    hechos = {"planning.taskContext": True, "repository.task": True,
              "repository.unambiguous": True, "repository.local": True,
              "repository.match": True, "task.acceptanceCriteriaField": True}
    hechos.update(cambios)
    return {"facts": hechos,
            "repository": {"status": "MATCHED", "failureCode": None,
                           "taskRepository": "gitlab.example/grupo/proyecto",
                           "declaredBy": ["FICHA"], "candidates": ["gitlab.example/grupo/proyecto"],
                           "localRepositories": ["gitlab.example/grupo/proyecto"]}}


def _propuesta(unidades=None, **extra):
    p = {"objective": "o", "domains": ["backend"], "policies": [],
         "workUnits": unidades or [{"id": "u1", "objective": "x", "domain": "backend",
                                    "requiredCapabilities": [], "dependencies": [],
                                    "signals": []}]}
    p.update(extra)
    return p


def _armar(precondiciones, propuesta=None):
    return orq_plan.armar(propuesta or _propuesta(), _tc(URL), {}, {}, "0.26.0", "x.json",
                          precondiciones)


def _entorno_limpio():
    """El entorno del proceso sin ninguna variable del contrato de entorno."""
    variables = set(entorno.variables_del_contrato(entorno.cargar_contrato()))
    return dict((k, v) for k, v in os.environ.items() if k not in variables)


def _cli(proy, *args):
    salida = subprocess.run([sys.executable, str(CLI)] + list(args) + ["--proyecto", str(proy)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=_entorno_limpio())
    return (salida.returncode, salida.stdout.decode("utf-8", "replace"),
            salida.stderr.decode("utf-8", "replace"))


def _proyecto_cli(remoto=URL + ".git", ficha=URL, env="", propuesta=None):
    """Un checkout con su TaskContext, su registro de capacidades y su propuesta."""
    proy = _repo(remoto) if remoto else _repo()
    _escribir(proy / ".claude" / "contextos" / (CLAVE + ".json"), json.dumps(_tc(ficha)))
    _escribir(proy / ".claude" / "harness.capacidades.json", json.dumps({"capacidades": {}}))
    _escribir(proy / ".claude" / "harness.config.json",
              json.dumps({"campoCriteriosAceptacion": "customfield_10001"}))
    _escribir(proy / "prop.json", json.dumps(propuesta or _propuesta()))
    if env:
        _escribir(proy / ".env", env)
    return proy


def _plan_escrito(proy):
    return json.loads((proy / ".claude" / "planes" / (CLAVE + ".json")).read_text(
        encoding="utf-8"))


def _run(proy):
    return proy / ".claude" / "refutaciones" / CLAVE / "run.json"


# -- E-01 a E-05: la identidad del repositorio ---------------------------------

def test_e01_ssh_y_https_son_el_mismo_repositorio(t):
    formas = ["git@gitlab.example:Grupo/Proyecto.git",
              "ssh://git@gitlab.example:22/grupo/proyecto.git",
              "https://usuario@gitlab.example/grupo/proyecto/"]
    t.igual("E-01 las tres normalizan igual", [("gitlab.example", "grupo/proyecto")] * 3,
            [REPO.normalizar(f) for f in formas])
    for forma in formas:
        proy = _repo(forma)
        try:
            ident = REPO.identidad(_tc(URL), {}, str(proy))
            t.igual("E-01 %s es MATCHED" % forma, "MATCHED", ident["status"])
            t.igual("E-01 %s sin codigo" % forma, None, ident["failureCode"])
        finally:
            _borrar(proy)


def test_e02_otro_repositorio_es_mismatch(t):
    proy = _repo("git@gitlab.example:grupo/b.git")
    try:
        ident = REPO.identidad(_tc("https://gitlab.example/grupo/a"), {}, str(proy))
        t.igual("E-02 MISMATCH", "MISMATCH", ident["status"])
        t.igual("E-02 con su codigo", "REPOSITORY_MISMATCH", ident["failureCode"])
        t.igual("E-02 y el hecho que falla", False, ident["facts"]["repository.match"])
    finally:
        _borrar(proy)


def test_e03_sin_remoto_no_hay_identidad_local(t):
    sin_remoto, sin_git = _repo(), _repo(git=False)
    try:
        for nombre, proy in (("git sin remotos", sin_remoto), ("sin git", sin_git)):
            ident = REPO.identidad(_tc(URL), {}, str(proy))
            t.igual("E-03 %s es UNRESOLVED" % nombre, "UNRESOLVED", ident["status"])
            t.igual("E-03 %s: LOCAL_REPOSITORY_UNRESOLVED" % nombre,
                    "LOCAL_REPOSITORY_UNRESOLVED", ident["failureCode"])
            t.igual("E-03 %s: ningun repositorio local" % nombre, [],
                    ident["localRepositories"])
    finally:
        _borrar(sin_remoto, sin_git)


def test_e04_sin_repositorio_de_la_tarea_el_plan_bloquea(t):
    ident = REPO.identidad(_tc("sin url"), {}, str(RAIZ))
    t.igual("E-04 UNRESOLVED", "UNRESOLVED", ident["status"])
    t.igual("E-04 REPOSITORY_UNRESOLVED", "REPOSITORY_UNRESOLVED", ident["failureCode"])
    t.igual("E-04 sin repositorio de la tarea", None, ident["taskRepository"])

    proy = _proyecto_cli(ficha="la ficha no nombra ningun repositorio")
    try:
        codigo, salida, error = _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        t.igual("E-04 plan sale con 0 y escribe el plan", 0, codigo)
        plan = _plan_escrito(proy)
        t.igual("E-04 el plan es BLOCKED", "BLOCKED", plan["status"])
        t.igual("E-04 valida contra su schema", [], orq_plan.validar(plan))
        pregunta = [p for p in plan["flowPreconditions"]["questions"]
                    if p["inputId"] == "repository.task"]
        t.igual("E-04 con la pregunta repository.task", 1, len(pregunta))
        if pregunta:
            t.igual("E-04 HARD_BLOCKER", "HARD_BLOCKER", pregunta[0]["classification"])
            t.igual("E-04 que bloquea", True, pregunta[0]["blocking"])
        t.contiene("E-04 y la salida lo dice", "REPOSITORY_UNRESOLVED", salida)
    finally:
        _borrar(proy)


def test_e05_dos_declaraciones_distintas_son_conflicto(t):
    proy = _repo(URL + ".git")
    try:
        ident = REPO.identidad(_tc("https://gitlab.example/grupo/b"),
                               {"gitlabProyecto": "grupo/a", "baseUrl": "https://gitlab.example"},
                               str(proy))
        t.igual("E-05 REPOSITORY_CONFLICT", "REPOSITORY_CONFLICT", ident["failureCode"])
        t.igual("E-05 no elige ninguna", None, ident["taskRepository"])
        t.igual("E-05 y muestra las dos", ["gitlab.example/grupo/a", "gitlab.example/grupo/b"],
                ident["candidates"])
        evaluacion = P.evaluar("PLANNING", dict(ident["facts"], **{
            "planning.taskContext": True, "task.acceptanceCriteriaField": True,
            "agents.routing": True}))
        pregunta = [p for p in evaluacion["questions"] if p["inputId"] == "repository.unambiguous"]
        t.igual("E-05 la etapa bloquea", "BLOCKED", evaluacion["status"])
        t.verdadero("E-05 con un HARD_BLOCKER de conflicto",
                    pregunta and pregunta[0]["classification"] == "HARD_BLOCKER"
                    and pregunta[0]["failureCode"] == "REPOSITORY_CONFLICT")

        dos = REPO.identidad(_tc("https://gitlab.example/grupo/a y https://gitlab.example/grupo/b"),
                             {}, str(proy))
        t.igual("E-05 dos URLs en la Ficha tambien", "REPOSITORY_CONFLICT", dos["failureCode"])
        t.igual("E-05 y tampoco elige", None, dos["taskRepository"])
        t.igual("E-05 con el hecho que bloquea", False, dos["facts"]["repository.unambiguous"])
    finally:
        _borrar(proy)

    # Y por la CLI, con GITLAB_PROJECT en el .env: la declaracion sale de entorno.py.
    proy = _proyecto_cli(ficha="https://gitlab.example/grupo/b",
                         env="GITLAB_BASE_URL=https://gitlab.example\nGITLAB_PROJECT=grupo/a\n")
    try:
        codigo, _, _ = _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        plan = _plan_escrito(proy)
        t.igual("E-05 por la CLI el plan es BLOCKED", [0, "BLOCKED"], [codigo, plan["status"]])
        t.igual("E-05 con REPOSITORY_CONFLICT", "REPOSITORY_CONFLICT",
                plan["flowPreconditions"]["repository"]["failureCode"])
    finally:
        _borrar(proy)


# -- E-06 a E-08: el estado del plan -------------------------------------------

def test_e06_un_hard_blocker_nunca_deja_el_plan_listo(t):
    derivable = _armar(_todo_resuelto(**{"planning.taskContext": False}))
    t.igual("E-06 un DERIVABLE bloqueante: BLOCKED", "BLOCKED", derivable["status"])
    plan = _armar(_todo_resuelto(**{"repository.match": False}))
    t.igual("E-06 un HARD_BLOCKER: BLOCKED", "BLOCKED", plan["status"])
    preguntas = plan["flowPreconditions"]["questions"]
    t.igual("E-06 una sola pregunta, y es el HARD_BLOCKER",
            [("repository.match", "HARD_BLOCKER", True)],
            [(p["inputId"], p["classification"], p["blocking"]) for p in preguntas])
    plan["status"] = "READY_FOR_EXECUTION"
    plan["flowPreconditions"]["status"] = "READY"
    t.igual("E-06 el calculo manda sobre lo escrito a mano", "BLOCKED", orq_plan.estado_de(plan))
    t.igual("E-06 sin precondiciones evaluadas tambien", "BLOCKED", _armar(None)["status"])
    sin_bloque = _armar(_todo_resuelto())
    del sin_bloque["flowPreconditions"]
    t.igual("E-06 un plan de antes, sin el bloque, es BLOCKED", "BLOCKED",
            orq_plan.estado_de(sin_bloque))


def test_e07_un_soft_no_bloquea_solo(t):
    plan = _armar(_todo_resuelto(**{"task.acceptanceCriteriaField": False}))
    t.igual("E-07 READY_FOR_EXECUTION", "READY_FOR_EXECUTION", plan["status"])
    pregunta = [p for p in plan["flowPreconditions"]["questions"]
                if p["inputId"] == "task.acceptanceCriteriaField"]
    t.igual("E-07 la pregunta esta", 1, len(pregunta))
    if pregunta:
        t.igual("E-07 SOFT_DEPENDENCY", "SOFT_DEPENDENCY", pregunta[0]["classification"])
        t.igual("E-07 y no bloquea", False, pregunta[0]["blocking"])
    t.igual("E-07 valida", [], orq_plan.validar(plan))


def test_e08_un_agente_no_ruteable_bloquea_la_unidad(t):
    plan = _armar(_todo_resuelto(), _propuesta([
        {"id": "u1", "objective": "x", "domain": "backend", "assignedAgent": "dev-no-existe",
         "requiredCapabilities": [], "dependencies": [], "signals": []},
        {"id": "u2", "objective": "y", "domain": "backend",
         "requiredCapabilities": [], "dependencies": [], "signals": []}]))
    por_id = dict((u["id"], u) for u in plan["workUnits"])
    t.igual("E-08 la unidad queda BLOCKED", "BLOCKED", por_id["u1"]["status"])
    t.igual("E-08 con el codigo exacto del registro",
            [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND"}], por_id["u1"]["blockers"])
    t.igual("E-08 la otra sigue", "PENDING", por_id["u2"]["status"])
    t.verdadero("E-08 y no lleva blockers", "blockers" not in por_id["u2"])
    t.igual("E-08 el plan es BLOCKED", "BLOCKED", plan["status"])
    pregunta = [p for p in plan["flowPreconditions"]["questions"]
                if p["inputId"] == "agents.routing"]
    t.verdadero("E-08 DERIVABLE, no se le pregunta a nadie",
                pregunta and pregunta[0]["askUser"] is False
                and pregunta[0]["classification"] == "DERIVABLE")
    t.igual("E-08 valida", [], orq_plan.validar(plan))


# -- E-09 a E-12: la compuerta de la refutacion --------------------------------

def test_e09_una_aprobacion_pendiente_no_compila(t):
    cara = _propuesta([{"id": "u1", "objective": "x", "domain": "backend",
                        "requiredCapabilities": [], "dependencies": [],
                        "signals": ["ambiguity", "security_impact", "architectural_impact"]}])
    proy = _proyecto_cli(propuesta=cara)
    try:
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        t.igual("E-09 el plan espera la aprobacion", "WAITING_FOR_HUMAN_APPROVAL",
                _plan_escrito(proy)["status"])
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-09 sale con 2", 2, codigo)
        t.contiene("E-09 PLAN_NOT_READY", "PLAN_NOT_READY", error)
        t.verdadero("E-09 no hay run.json", not _run(proy).exists())
    finally:
        _borrar(proy)


def test_e10_un_contexto_distinto_es_stale(t):
    proy = _proyecto_cli()
    try:
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        t.igual("E-10 el plan de partida esta listo", "READY_FOR_EXECUTION",
                _plan_escrito(proy)["status"])
        ruta = proy / ".claude" / "contextos" / (CLAVE + ".json")

        editado = json.loads(ruta.read_text(encoding="utf-8"))
        editado["task"]["title"] = "otro titulo, sin recalcular el hash"
        _escribir(ruta, json.dumps(editado))
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-10 editado a mano: sale con 2", 2, codigo)
        t.contiene("E-10 editado a mano: CONTEXT_STALE", "CONTEXT_STALE", error)

        otro = _tc(URL)
        otro["task"]["title"] = "un contexto nuevo, con su hash"
        otro["meta"]["context_hash"] = R._armador().hash_de(otro)
        _escribir(ruta, json.dumps(otro))
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-10 otro hash que el del plan: sale con 2", 2, codigo)
        t.contiene("E-10 otro hash: CONTEXT_STALE", "CONTEXT_STALE", error)
        t.verdadero("E-10 no hay run.json", not _run(proy).exists())
    finally:
        _borrar(proy)


def test_e11_otro_checkout_no_compila(t):
    proy = _proyecto_cli()
    try:
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-11 en el checkout correcto compila", 0, codigo)
        antes = _run(proy).read_bytes() if _run(proy).exists() else None
        t.verdadero("E-11 y deja run.json", antes is not None)

        _git(proy, "remote", "set-url", "origin", "git@gitlab.example:grupo/otro.git")
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-11 en otro checkout sale con 2", 2, codigo)
        t.contiene("E-11 REPOSITORY_MISMATCH", "REPOSITORY_MISMATCH", error)
        t.igual("E-11 run.json queda byte a byte igual", antes,
                _run(proy).read_bytes() if _run(proy).exists() else None)
    finally:
        _borrar(proy)

    proy = _proyecto_cli()
    try:
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        _git(proy, "remote", "set-url", "origin", "git@gitlab.example:grupo/otro.git")
        codigo, _, error = _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-11 sin corrida previa tambien sale con 2", 2, codigo)
        t.verdadero("E-11 y no crea run.json", not _run(proy).exists())
    finally:
        _borrar(proy)


def _refutacion_atomica():
    """Los helpers de 55_refutacion_atomica.py: el proyecto con una unidad pendiente."""
    ruta = RAIZ / "tests" / "casos" / "55_refutacion_atomica.py"
    spec = importlib.util.spec_from_file_location("caso_55_para_61", str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_e12_un_plan_reescrito_vence_la_corrida(t):
    ra = _refutacion_atomica()
    proy = ra._proyecto()
    try:
        R.compilar(str(proy), ra.CLAVE)
        u = [x for x in ra._unidades(proy) if x["status"] == "PENDING_SEMANTIC"][0]
        ruta_plan = proy / ".claude" / "planes" / (ra.CLAVE + ".json")
        plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
        plan["warnings"].append("el plan se reescribio despues de compilar")
        _escribir(ruta_plan, json.dumps(plan))

        for nombre, llamada in (
                ("para_refutar", lambda: R.para_refutar(str(proy), ra.CLAVE,
                                                        u["refutationUnitId"])),
                ("registrar", lambda: R.registrar(str(proy), ra.CLAVE,
                                                  json.dumps(ra._veredicto(u))))):
            try:
                llamada()
                t.verdadero("E-12 %s levanta" % nombre, False)
            except R.RefutacionInvalida as e:
                t.igual("E-12 %s: REFUTATION_PLAN_STALE" % nombre, "REFUTATION_PLAN_STALE",
                        e.codigo)

        ruta_v = proy / "v.json"
        _escribir(ruta_v, json.dumps(ra._veredicto(u)))
        for accion in (["--unit", u["refutationUnitId"]], ["--record", str(ruta_v)]):
            codigo, _, error = ra._cli(proy, "refute", ra.CLAVE, *accion)
            t.igual("E-12 %s sale con 2" % accion[0], 2, codigo)
            t.contiene("E-12 %s lo dice" % accion[0], "REFUTATION_PLAN_STALE", error)
        veredictos = proy / ".claude" / "refutaciones" / ra.CLAVE / "verdicts"
        t.igual("E-12 no se escribio ningun veredicto", [],
                sorted(os.listdir(str(veredictos))) if veredictos.is_dir() else [])
    finally:
        ra._borrar(proy)


# -- E-13 a E-19: el localizador -----------------------------------------------

_ENV = ("# Configuracion local\n"
        "HARNESS_JIRA_ENABLED=true\n"
        "JIRA_BASE_URL=%s\n"
        "JIRA_USER=%s\n"
        "JIRA_TOKEN=%s\n"
        "GITLAB_TOKEN=%s\n" % (BASE, USUARIO, JIRA, TOKEN))


def test_e13_el_localizador_da_la_linea_sin_el_valor(t):
    proy = _tmp("harness-fl-loc")
    try:
        _escribir(proy / ".env", _ENV)
        u = EH.localizar("jira.token", str(proy))
        t.igual("E-13 linea 5", 5, u["line"])
        t.igual("E-13 columna 1", 1, u["column"])
        t.igual("E-13 la clave", "JIRA_TOKEN", u["key"])
        t.igual("E-13 dotenv", "dotenv", u["format"])
        t.igual("E-13 SECRET, del contrato", "SECRET", u["sensitivity"])
        t.igual("E-13 cargado", True, u["present"])
        t.igual("E-13 el archivo relativo", ".env", u["file"])
        for vacio in ("JIRA_TOKEN=", "JIRA_TOKEN=<tu-api-token-de-jira>"):
            _escribir(proy / ".env", _ENV.replace("JIRA_TOKEN=" + JIRA, vacio))
            u = EH.localizar("jira.token", str(proy))
            t.igual("E-13 %s: misma linea" % vacio, 5, u["line"])
            t.igual("E-13 %s: no cargado" % vacio, False, u["present"])
        t.igual("E-13 una variable publica es PUBLIC_CONFIG", "PUBLIC_CONFIG",
                EH.localizar("jira.baseUrl", str(proy))["sensitivity"])
    finally:
        _borrar(proy)


def test_e14_el_localizador_nunca_expone_un_valor(t):
    proy = _tmp("harness-fl-loc")
    try:
        _escribir(proy / ".env", _ENV)
        for input_id in ("jira.token", "jira.user", "jira.baseUrl", "gitlab.token",
                         "jira.enabled"):
            u = EH.localizar(input_id, str(proy))
            t.igual("E-14 %s: exactamente sus campos" % input_id, sorted(EH.CAMPOS), sorted(u))
            t.igual("E-14 %s: ningun campo prohibido" % input_id, [],
                    [k for k in u if k.lower() in EH.PROHIBIDOS])
            texto = EH.como_json(u) + EH.renderizar(u, "dev-harness.py reconfigurar jira")
            for nombre, valor in (("token de Jira", JIRA), ("token de GitLab", TOKEN),
                                  ("base URL", BASE), ("usuario", USUARIO)):
                t.no_contiene("E-14 %s: sin el %s" % (input_id, nombre), valor, texto)
    finally:
        _borrar(proy)


def test_e15_sin_la_clave_da_donde_agregarla(t):
    proy = _tmp("harness-fl-loc")
    try:
        _escribir(proy / ".env", "JIRA_BASE_URL=%s\nJIRA_USER=%s\n" % (BASE, USUARIO))
        u = EH.localizar("jira.token", str(proy))
        t.igual("E-15 la linea siguiente a la ultima", 3, u["line"])
        t.igual("E-15 columna 1", 1, u["column"])
        t.igual("E-15 no esta", False, u["present"])
        os.remove(str(proy / ".env"))
        u = EH.localizar("jira.token", str(proy))
        t.igual("E-15 sin .env, la linea 1", [1, 1, False],
                [u["line"], u["column"], u["present"]])

        _escribir(proy / ".claude" / "harness.config.json",
                  '{\n  "rutaCodebase": "docs/codebase"\n}\n')
        u = EH.localizar("task.acceptanceCriteriaField", str(proy))
        t.igual("E-15 en JSON, adentro del objeto", [2, 1, False],
                [u["line"], u["column"], u["present"]])
    finally:
        _borrar(proy)


def test_e16_la_uri_de_vscode_en_windows(t):
    t.igual("E-16 la ruta de la Wave",
            ("vscode://file/C:/Work/app/.env:12:1", "C:/Work/app/.env:12:1"),
            EH.uri_de("C:\\Work\\app\\.env", 12, 1))
    uri, respaldo = EH.uri_de("c:\\Mis Proyectos\\app\\.env", 3, 1)
    t.igual("E-16 un espacio va codificado y la unidad en mayuscula",
            "vscode://file/C:/Mis%20Proyectos/app/.env:3:1", uri)
    t.igual("E-16 el respaldo va sin codificar", "C:/Mis Proyectos/app/.env:3:1", respaldo)
    t.igual("E-16 una ruta POSIX", "vscode://file/home/p/app/.env:1:1",
            EH.uri_de("/home/p/app/.env", 1, 1)[0])
    t.igual("E-16 dos llamadas, lo mismo", EH.uri_de("C:\\Work\\app\\.env", 12, 1),
            EH.uri_de("C:\\Work\\app\\.env", 12, 1))


def test_e17_el_renderizador_usa_placeholder(t):
    proy = _tmp("harness-fl-loc")
    try:
        _escribir(proy / ".env", _ENV)
        u = EH.localizar("jira.token", str(proy))
        texto = EH.renderizar(u, "dev-harness.py reconfigurar jira")
        t.contiene("E-17 la linea con placeholder", "JIRA_TOKEN=<jira-token>", texto)
        t.no_contiene("E-17 sin el valor", JIRA, texto)
        t.contiene("E-17 no pegar un SECRET en el chat", "No pegues", texto)
        t.contiene("E-17 con la URI", u["vscodeUri"], texto)
        t.contiene("E-17 y como revalidar", "reconfigurar jira", texto)
        publica = EH.renderizar(EH.localizar("jira.baseUrl", str(proy)))
        t.no_contiene("E-17 una publica no dice lo del chat", "No pegues", publica)
    finally:
        _borrar(proy)
    esperado = {"dotenv": "JIRA_TOKEN=<jira-token>", "json": '"JIRA_TOKEN": "<jira-token>"',
                "yaml": 'JIRA_TOKEN: "<jira-token>"', "toml": 'JIRA_TOKEN = "<jira-token>"',
                "properties": "JIRA_TOKEN=<jira-token>", "ini": "JIRA_TOKEN = <jira-token>"}
    for formato, linea in sorted(esperado.items()):
        t.igual("E-17 %s" % formato, linea, EH.sintaxis(formato, "JIRA_TOKEN"))
        ubicacion = {"inputId": "jira.token", "file": "x", "absolutePath": "C:/x", "line": 1,
                     "column": 1, "key": "JIRA_TOKEN", "present": False, "format": formato,
                     "sensitivity": "SECRET", "vscodeUri": "vscode://file/C:/x:1:1",
                     "fallback": "C:/x:1:1"}
        rendido = EH.renderizar(ubicacion)
        t.contiene("E-17 %s: renderizar lleva la linea" % formato, linea, rendido)
        t.contiene("E-17 %s: y lo del chat" % formato, "No pegues", rendido)
    try:
        EH.sintaxis("xml", "JIRA_TOKEN")
        t.verdadero("E-17 un formato desconocido levanta", False)
    except EH.EntradaNoUbicable as e:
        t.igual("E-17 INPUT_FORMAT_UNRESOLVED", "INPUT_FORMAT_UNRESOLVED", e.codigo)


def test_e18_nadie_escribe_el_env(t):
    proy = _proyecto_cli(env=_ENV)
    try:
        antes = (proy / ".env").read_bytes()
        for input_id in ("jira.token", "jira.user", "repository.task"):
            EH.localizar(input_id, str(proy))
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        _cli(proy, "refute", CLAVE, "--compile")
        t.igual("E-18 el .env queda byte a byte igual", antes, (proy / ".env").read_bytes())
    finally:
        _borrar(proy)
    escribe = re.compile(r"""open\([^)]*["'][wax]|\.write\(|\.write_text\(|\.write_bytes\(|"""
                         r"""json\.dump\(|os\.replace|os\.remove|os\.rename|\.set\(|"""
                         r"""\.remove\(|shutil\.|os\.makedirs|\.mkdir\(""")
    for fuente in sorted(FLUJO.glob("*.py")):
        t.igual("E-18 %s no escribe" % fuente.name, [],
                escribe.findall(fuente.read_text(encoding="utf-8")))


def test_e19_la_proyeccion_no_es_input_humano(t):
    doc = json.loads(REGISTRO.read_text(encoding="utf-8"))
    t.igual("E-19 ningun input de la fabrica apunta a lo generado", [],
            [e["inputId"] for e in doc["inputs"] if e["persistentTarget"]
             and REQ.es_generado(e["persistentTarget"]["file"])])
    roto = json.loads(json.dumps(doc))
    destino = [e for e in roto["inputs"] if e["inputId"] == "task.acceptanceCriteriaField"][0]
    destino["persistentTarget"]["file"] = ".claude/harness.integraciones.json"
    try:
        REQ.comprobar(roto)
        t.verdadero("E-19 el cargador lo rechaza", False)
    except REQ.RegistroInvalido as e:
        t.igual("E-19 FLOW_INPUT_TARGET_NOT_HUMAN", "FLOW_INPUT_TARGET_NOT_HUMAN", e.codigo)
    proy = _tmp("harness-fl-loc")
    try:
        EH.localizar("task.acceptanceCriteriaField", str(proy), registro=roto)
        t.verdadero("E-19 el localizador no lo ubica", False)
    except EH.EntradaNoUbicable as e:
        t.igual("E-19 el localizador tampoco", "FLOW_INPUT_TARGET_NOT_HUMAN", e.codigo)
    finally:
        _borrar(proy)


# -- E-21 a E-24: el registro y lo que no cambia -------------------------------

def test_e21_el_registro_valida_y_rechaza_contradicciones(t):
    doc = json.loads(REGISTRO.read_text(encoding="utf-8"))
    t.igual("E-21 el de la fabrica valida", [], REQ.validar(doc))

    def con(input_id, **cambios):
        otro = json.loads(json.dumps(doc))
        e = [x for x in otro["inputs"] if x["inputId"] == input_id][0]
        for k, v in cambios.items():
            if k == "key":
                e["persistentTarget"]["key"] = v
            else:
                e[k] = v
        return otro

    casos = {"un HARD_BLOCKER que no bloquea": con("repository.task", blocking=False),
             "un DERIVABLE que pregunta": con("agents.routing", askUser=True),
             "un PERSISTENT_CONFIG_INPUT sin destino": con("jira.token", persistentTarget=None),
             "una variable fuera del contrato": con("jira.token", key="OPENSHIFT_TOKEN"),
             "una clasificacion desconocida": con("jira.token", classification="CASI_BLOQUEA")}
    for nombre, roto in sorted(casos.items()):
        try:
            REQ.comprobar(roto)
            t.verdadero("E-21 rechaza %s" % nombre, False)
        except REQ.RegistroInvalido as e:
            t.igual("E-21 %s: FLOW_REQUIRED_INPUTS_INVALID" % nombre,
                    "FLOW_REQUIRED_INPUTS_INVALID", e.codigo)


def test_e22_la_misma_entrada_da_los_mismos_bytes(t):
    # Varias preguntas a la vez: con una sola, el orden no puede fallar.
    hechos = _todo_resuelto(**{"task.acceptanceCriteriaField": False,
                               "planning.taskContext": False, "repository.local": False})["facts"]
    hechos["agents.routing"] = False
    t.igual("E-22 la evaluacion",
            json.dumps(P.evaluar("PLANNING", hechos), sort_keys=True),
            json.dumps(P.evaluar("PLANNING", dict(reversed(list(hechos.items())))),
                       sort_keys=True))
    proy = _repo(URL + ".git", "git@gitlab.example:grupo/otro.git")
    try:
        _escribir(proy / ".env", _ENV)
        t.igual("E-22 la identidad",
                json.dumps(REPO.identidad(_tc(URL), GITLAB, str(proy)), sort_keys=True),
                json.dumps(REPO.identidad(_tc(URL), GITLAB, str(proy)), sort_keys=True))
        t.igual("E-22 la ubicacion", EH.como_json(EH.localizar("jira.token", str(proy))),
                EH.como_json(EH.localizar("jira.token", str(proy))))
    finally:
        _borrar(proy)


def test_e23_un_token_en_el_remoto_no_llega_a_ningun_lado(t):
    remoto = "https://oauth2:%s@gitlab.example/grupo/proyecto.git" % TOKEN
    proy = _proyecto_cli(remoto=remoto)
    try:
        ident = REPO.identidad(_tc(URL), {}, str(proy))
        texto = json.dumps(ident)
        t.igual("E-23 igual es MATCHED", "MATCHED", ident["status"])
        t.no_contiene("E-23 la identidad no tiene el token", TOKEN, texto)
        t.no_contiene("E-23 ni el usuario del remoto", "oauth2", texto)
        con_arroba = REPO.normalizar("https://usuario:p@ss@gitlab.example/grupo/proyecto.git")
        t.igual("E-23 una contrasena con @ tampoco deja un pedazo",
                ("gitlab.example", "grupo/proyecto"), con_arroba)
        _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"))
        escrito = (proy / ".claude" / "planes" / (CLAVE + ".json")).read_text(encoding="utf-8")
        t.no_contiene("E-23 el plan escrito no tiene el token", TOKEN, escrito)
        t.no_contiene("E-23 ni oauth2", "oauth2", escrito)
    finally:
        _borrar(proy)


def test_e24_el_contrato_de_entorno_no_cambia(t):
    for relativa in ("harnesses/desarrollo/reglas/integration-environment-contract.json",
                     "harnesses/desarrollo/bin/integraciones/entorno.py",
                     "harnesses/desarrollo/bin/integraciones/base.py"):
        salida = subprocess.run(["git", "-C", str(RAIZ), "show", "6cff4b4:" + relativa],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if salida.returncode != 0:
            t.verdadero("E-24 %s: git show no pudo leer 6cff4b4" % relativa, False)
            continue
        actual = (RAIZ / relativa).read_bytes().replace(b"\r\n", b"\n")
        t.igual("E-24 %s igual que en 6cff4b4" % relativa,
                salida.stdout.replace(b"\r\n", b"\n"), actual)
