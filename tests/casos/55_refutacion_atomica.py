# La refutacion atomica: compilador, alcance, huellas, checks, cache, frontera del refutador,
# agregado, Bloque 4, micro-lote y seguridad.
#
# Spec: docs/cambios/refutacion-atomica/spec.md. Cada test nombra su escenario E-nn, que es el
# AR-0nn del paquete con el mismo numero. E-61 es la suite misma.
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
AGENTE = RAIZ / "harnesses" / "desarrollo" / "agents" / "dev-refutador.md"
SCHEMAS = RAIZ / "comun" / "schemas"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from orquestacion import plan as orq_plan                 # noqa: E402
from orquestacion import refutacion as R                  # noqa: E402
from orquestacion import registro_agentes as reg          # noqa: E402
from contabilidad import libro as c_libro                 # noqa: E402
from reporte_seguridad import libro as s_libro            # noqa: E402
from reporte_seguridad import productores as s_prod       # noqa: E402

CLAVE = "GCBA-55"
OTRA = "GCBA-56"
TOKEN = "glpat-" + "a1B2c3D4e5F6g7H8i9J0"


# -- el proyecto de prueba -----------------------------------------------------

def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def _git(proy, *args):
    subprocess.run(["git", "-C", str(proy)] + list(args), stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, check=True)


def _bloque(reglas, sin_resolver=(), checks=(), reviews=()):
    return {"standard": {"id": "ES0902", "version": "6.2"},
            "applicableRules": list(reglas), "notApplicableRules": [],
            "unresolvedRules": [{"rule": r, "ruleKey": "ES0902." + r,
                                 "reason": "APPLICABILITY_UNRESOLVED",
                                 "missingSignals": ["x"]} for r in sin_resolver],
            "declaredPolicies": [], "declaredChecks": list(checks),
            "declaredReviews": list(reviews)}


_PLANES = {}


def _plan(clave, unidades):
    """Un plan real de plan.armar, con el bloque normativo de cada unidad controlado.

    `unidades` es {wu_id: bloque de ES0902}. El resto de la unidad es el que arma el plan. Se
    arma una vez por clave y juego de unidades: `plan.armar` cuesta un segundo.
    """
    llave = (clave, tuple(sorted(unidades)))
    if llave not in _PLANES:
        tc = {"meta": {"task_key": clave, "context_hash": "h"}, "task": {"title": "t"}}
        prop = {"objective": "o", "domains": ["backend"],
                "workUnits": [{"id": wu, "objective": "x", "domain": "backend"}
                              for wu in unidades]}
        _PLANES[llave] = json.dumps(orq_plan.armar(prop, tc, {}, {}))
    doc = json.loads(_PLANES[llave])
    for u in doc["workUnits"]:
        base = u["normative"]
        u["normative"] = dict(base, standards={"ES0902": unidades[u["id"]]})
    return doc


def _proyecto(unidades=None, scope="por-defecto", git=True, clave=CLAVE, proy=None):
    proy = proy or (Path(tempfile.gettempdir()) / ("harness-ra-" + uuid.uuid4().hex[:8]))
    if not (proy / "src").exists():
        shutil.copytree(str(_plantilla(git)), str(proy))
    unidades = unidades or {"WU-1": _bloque(["Vu4"], checks=["session-inactivity-timeout"])}
    _escribir(proy / ".claude" / "planes" / (clave + ".json"),
              json.dumps(_plan(clave, unidades), ensure_ascii=False))
    if scope == "por-defecto":
        scope = {wu: [{"scopeId": "sesion", "source": "workUnitFiles",
                       "paths": ["src/sesion.py"]}] for wu in unidades}
    if scope is not None:
        _escribir(proy / ".claude" / "refutaciones" / clave / "scope.json",
                  json.dumps({"schema_version": R.VERSION_ALCANCE, "workUnits": scope}))
    return proy


_PLANTILLAS = {}


def _plantilla(git):
    """El repositorio de prueba, armado una vez y copiado por test. `git init` y un commit por
    test eran un tercio del tiempo del archivo."""
    if git not in _PLANTILLAS:
        base = Path(tempfile.gettempdir()) / ("harness-ra-base-" + uuid.uuid4().hex[:8])
        _escribir(base / "src" / "sesion.py", "TIMEOUT = 900\n")
        _escribir(base / "src" / "error.py", "MENSAJE = 'Error generico'\n")
        _escribir(base / "otro" / "nada.py", "x = 1\n")
        if git:
            _git(base, "init", "-q")
            _git(base, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
            _git(base, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "i")
        _PLANTILLAS[git] = base
    return _PLANTILLAS[git]


def _borrar(proy):
    shutil.rmtree(str(proy), ignore_errors=True)


def _unidades(proy, clave=CLAVE):
    return R.leer(str(proy), clave)[1]


def _veredicto(u, veredicto="cumple", **cambios):
    v = {"schema_version": R.VERSION_VEREDICTO,
         "refutationUnitId": u["refutationUnitId"], "workUnitId": u["workUnitId"],
         "ruleKey": u["standard"]["ruleKey"], "verdict": veredicto, "reason": None,
         "citation": {"skillId": u["skillId"], "locator": "ES0902 §6, pág. 12"},
         "evidence": [{"path": u["evidenceScope"]["paths"][0], "line": 1,
                       "observed": "TIMEOUT = 900"}],
         "needed": None, "cacheKey": u["cacheKey"],
         "evidenceFingerprint": u["evidenceFingerprint"], "repoRevision": u["repoRevision"]}
    if veredicto == "sin-verificar":
        v.update({"reason": "EVIDENCE_INSUFFICIENT", "needed": "abrir config/app.yml",
                  "citation": None})
    v.update(cambios)
    return v


def _levanta(funcion, codigo=None):
    try:
        funcion()
    except R.RefutacionInvalida as e:
        return codigo is None or e.codigo == codigo
    return False


def _cli(proy, *args):
    salida = subprocess.run([sys.executable, str(CLI)] + list(args) + ["--proyecto", str(proy)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (salida.returncode, salida.stdout.decode("utf-8", "replace"),
            salida.stderr.decode("utf-8", "replace"))


def _checks(proy, resultados, clave=CLAVE):
    _escribir(proy / ".claude" / "refutaciones" / clave / "checks.json",
              json.dumps({"schema_version": R.VERSION_CHECKS, "results": resultados}))


def _check(u, estado="PASS", control="session-inactivity-timeout", **cambios):
    r = {"control": control, "ruleKey": u["standard"]["ruleKey"], "state": estado,
         "repoRevision": u["repoRevision"], "evidenceFingerprint": u["evidenceFingerprint"]}
    r.update(cambios)
    return r


def _claves(nodo):
    if isinstance(nodo, dict):
        return set(nodo) | set().union(*[_claves(v) for v in nodo.values()]) if nodo else set()
    if isinstance(nodo, list):
        return set().union(*[_claves(v) for v in nodo]) if nodo else set()
    return set()


# -- E-01 a E-04: un refutador, ninguna skill nueva ----------------------------

def test_e01_un_solo_refutador(t):
    doc = reg.cargar()
    de_refutacion = [a["id"] for a in doc["agents"] if a.get("domain") == "refutation"]
    t.igual("E-01 un solo agente de refutacion", ["dev-refutador"], de_refutacion)
    archivos = sorted(p.name for p in (RAIZ / "harnesses" / "desarrollo" / "agents").glob(
        "dev-refutador*"))
    t.igual("E-01 y un solo archivo dev-refutador*", ["dev-refutador.md"], archivos)


def test_e02_ninguna_skill_nueva(t):
    doc = reg.cargar()
    registradas = [s["id"] for a in doc["agents"] for s in a.get("skills") or []]
    en_disco = [p.name for base in (RAIZ / "harnesses", RAIZ / "comun")
                for p in base.rglob("*") if p.is_dir() and (p / "SKILL.md").is_file()]
    for nombre in registradas + en_disco:
        t.verdadero("E-02 `%s` no es una skill de refutacion" % nombre,
                    "refut" not in nombre.lower() and "atomic" not in nombre.lower())


def test_e03_el_registro_sigue_valido(t):
    doc = reg.cargar()
    t.igual("E-03 el registro valida contra su schema", [], reg.validar_schema(doc))
    agente = [a for a in doc["agents"] if a["id"] == "dev-refutador"][0]
    t.igual("E-03 sigue CRITIC_AGENT", "CRITIC_AGENT", agente["type"])
    t.igual("E-03 con cero skills", [], agente["skills"])
    t.igual("E-03 y valido", "VALID", reg.validar_registro(doc)["agents"]["dev-refutador"]["state"])


def test_e04_el_plan_no_cambia(t):
    esquema = json.loads((SCHEMAS / "orchestration-plan.schema.json").read_text(encoding="utf-8"))
    campos = [k for k in _claves(esquema.get("properties")) if "refut" in k.lower()]
    t.igual("E-04 el schema del plan no tiene campos de refutacion", [], campos)
    proy = _proyecto()
    try:
        ruta = proy / ".claude" / "planes" / (CLAVE + ".json")
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        real = orq_plan.armar({"objective": "o", "domains": ["backend"],
                               "workUnits": [{"id": "wu-1", "objective": "x",
                                              "domain": "backend"}]},
                              {"meta": {"task_key": CLAVE, "context_hash": "h"},
                               "task": {"title": "t"}}, {}, {})
        t.igual("E-04 un plan de plan.armar valida", [], orq_plan.validar(real))
        _escribir(ruta, json.dumps(real))
        antes = ruta.read_bytes()
        R.compilar(str(proy), CLAVE)
        t.igual("E-04 compilar no toca el plan", antes, ruta.read_bytes())
        t.verdadero("E-04 y el plan real compila en unidades", len(_unidades(proy)) > 0)
        del plan
    finally:
        _borrar(proy)


# -- E-05 a E-10: el compilador ------------------------------------------------

def test_e05_una_regla_un_alcance_una_unidad(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        us = _unidades(proy)
        t.igual("E-05 una sola unidad", 1, len(us))
        u = us[0]
        t.igual("E-05 workUnitId", "WU-1", u["workUnitId"])
        t.igual("E-05 ruleKey", "ES0902.Vu4", u["standard"]["ruleKey"])
        t.verdadero("E-05 skillId de una skill dev-*", (u["skillId"] or "").startswith("dev-"))
        t.igual("E-05 evidenceScope.paths", ["src/sesion.py"], u["evidenceScope"]["paths"])
    finally:
        _borrar(proy)


def test_e06_dos_reglas_dos_unidades(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"])})
    try:
        R.compilar(str(proy), CLAVE)
        claves = sorted(u["standard"]["ruleKey"] for u in _unidades(proy))
        t.igual("E-06 dos unidades, una por regla", ["ES0902.Vu4", "ES0902.Vu6"], claves)
    finally:
        _borrar(proy)


def test_e07_misma_regla_dos_alcances(t):
    scope = {"WU-1": [{"scopeId": "a", "source": "workUnitFiles", "paths": ["src/sesion.py"]},
                      {"scopeId": "b", "source": "workUnitFiles", "paths": ["src/error.py"]}]}
    proy = _proyecto(scope=scope)
    try:
        R.compilar(str(proy), CLAVE)
        us = _unidades(proy)
        t.igual("E-07 dos unidades", 2, len(us))
        t.igual("E-07 con scopeId distintos", ["a", "b"],
                sorted(u["evidenceScope"]["scopeId"] for u in us))
        t.igual("E-07 y la misma regla", {"ES0902.Vu4"},
                set(u["standard"]["ruleKey"] for u in us))
    finally:
        _borrar(proy)


def test_e08_sin_alcance_no_hay_repositorio_entero(t):
    for nombre, scope in (("sin scope.json", None),
                          ("con `.`", {"WU-1": [{"scopeId": "todo", "source": "workUnitFiles",
                                                 "paths": ["."]}]}),
                          ("con `/`", {"WU-1": [{"scopeId": "todo", "source": "workUnitFiles",
                                                 "paths": ["/"]}]})):
        proy = _proyecto(scope=scope)
        try:
            R.compilar(str(proy), CLAVE)
            for u in _unidades(proy):
                t.igual("E-08 %s: ninguna ruta" % nombre, [], u["evidenceScope"]["paths"])
        finally:
            _borrar(proy)


def test_e09_alcance_sin_resolver_bloquea(t):
    proy = _proyecto(scope=None)
    try:
        doc = R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        t.igual("E-09 scopeState", "EVIDENCE_SCOPE_UNRESOLVED", u["scopeState"])
        t.igual("E-09 status", "BLOCKED", u["status"])
        t.igual("E-09 failure", "REFUTATION_SCOPE_UNRESOLVED", u["failure"])
        t.verdadero("E-09 y la corrida no es PASS", doc["status"] != "PASS")
        t.igual("E-09 sino INCOMPLETE", "INCOMPLETE", doc["status"])
    finally:
        _borrar(proy)


def _fotos(proy):
    carpeta = proy / ".claude" / "refutaciones" / CLAVE
    return {p.relative_to(carpeta).as_posix(): p.read_bytes()
            for p in sorted(carpeta.rglob("*.json")) if p.name not in ("scope.json",
                                                                       "checks.json")}


def test_e10_el_compilador_es_determinista(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"], sin_resolver=["Vu1"]),
                      "WU-2": _bloque(["Vu4"])})
    try:
        R.compilar(str(proy), CLAVE)
        primera = _fotos(proy)
        R.compilar(str(proy), CLAVE)
        t.igual("E-10 los mismos archivos", sorted(primera), sorted(_fotos(proy)))
        t.verdadero("E-10 byte a byte", primera == _fotos(proy))
        t.verdadero("E-10 incluye run.json y las unidades",
                    "run.json" in primera and any(k.startswith("units/") for k in primera))
    finally:
        _borrar(proy)


# -- E-11 a E-15: el check primero ---------------------------------------------

def _con_check(t, estado="PASS", unidades=None, **cambios):
    proy = _proyecto(unidades)
    R.compilar(str(proy), CLAVE)
    u = _unidades(proy)[0]
    _checks(proy, [_check(u, estado, **cambios)])
    doc = R.compilar(str(proy), CLAVE)
    return proy, doc, _unidades(proy)[0]


def test_e11_check_concluyente_cierra_sin_modelo(t):
    proy, doc, u = _con_check(t)
    try:
        t.igual("E-11 resuelta", "RESOLVED", u["status"])
        t.igual("E-11 por check", "DETERMINISTIC_CHECK", u["resolutionPath"])
        t.igual("E-11 cumple", "cumple", doc["units"][0]["verdict"])
        t.igual("E-11 no queda pendiente del refutador", 0, doc["counts"]["pending"])
        t.igual("E-11 cuenta como resuelta por check", 1, doc["counts"]["checkResolved"])
        t.verdadero("E-11 y --unit no la entrega",
                    _levanta(lambda: R.para_refutar(str(proy), CLAVE, "REF-001")))
    finally:
        _borrar(proy)


def test_e12_check_sin_resolver_no_es_cumple(t):
    for estado in ("APPLICABILITY_UNRESOLVED", "NOT_APPLICABLE", "SESSION_TIMEOUT_UNRESOLVED"):
        proy, doc, u = _con_check(t, estado)
        try:
            t.igual("E-12 %s: pendiente del refutador" % estado, "PENDING_SEMANTIC", u["status"])
            t.igual("E-12 %s: sin veredicto" % estado, None, doc["units"][0]["verdict"])
            t.verdadero("E-12 %s: nunca PASS" % estado, doc["status"] != "PASS")
        finally:
            _borrar(proy)


def test_e13_check_viejo_no_cierra(t):
    for nombre, cambio in (("otra huella", {"evidenceFingerprint": "sha256:" + "0" * 64}),
                           ("otra revision", {"repoRevision": "f" * 40})):
        proy, doc, u = _con_check(t, "PASS", **cambio)
        try:
            t.igual("E-13 %s: no cierra" % nombre, "PENDING_SEMANTIC", u["status"])
            t.igual("E-13 %s: y se ve como no actual" % nombre, False,
                    u["checkRefs"][0]["current"])
        finally:
            _borrar(proy)


def test_e14_review_va_al_refutador(t):
    original = R._matrices

    def con_review(desde):
        m = original(desde)
        doc, version = m["ES0902"]
        doc = json.loads(json.dumps(doc))
        for r in doc["rules"]:
            if r["id"] == "Vu4":
                r["reviews"] = ["session-timeout-review"]
        m["ES0902"] = (doc, version)
        return m

    R._matrices = con_review
    try:
        proy, doc, u = _con_check(t)
        try:
            t.igual("E-14 modo REVIEW", "REVIEW", u["verificationMode"])
            t.igual("E-14 con check PASS actual, va al refutador", "PENDING_SEMANTIC",
                    u["status"])
            t.igual("E-14 el check si estaba atado, actual y concluyente",
                    [True, True, True], [u["checkRefs"][0][k] for k in
                                         ("bound", "current", "conclusive")])
        finally:
            _borrar(proy)
    finally:
        R._matrices = original


def test_e15_check_de_otra_regla_no_cierra(t):
    proy = _proyecto({"WU-1": _bloque(["Vu7"], checks=["session-inactivity-timeout"])})
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        # El control de Vu4 declarando un resultado de Vu7.
        _checks(proy, [_check(u, "PASS", control="session-inactivity-timeout")])
        doc = R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        t.igual("E-15 no cierra", "PENDING_SEMANTIC", u["status"])
        t.igual("E-15 porque el control no esta atado a la regla", False,
                u["checkRefs"][0]["bound"])
        t.verdadero("E-15 y no es PASS", doc["status"] != "PASS")
    finally:
        _borrar(proy)


# -- E-16 a E-25: la frontera del refutador ------------------------------------

def test_e16_el_refutador_recibe_una_unidad(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"], sin_resolver=["Vu1"])})
    try:
        R.compilar(str(proy), CLAVE)
        pendiente = [u for u in _unidades(proy) if u["status"] == "PENDING_SEMANTIC"][0]
        codigo, salida, _ = _cli(proy, "refute", CLAVE, "--unit", pendiente["refutationUnitId"])
        t.igual("E-16 sale con 0", 0, codigo)
        doc = json.loads(salida)
        t.verdadero("E-16 es un objeto, no una lista", isinstance(doc, dict))
        t.igual("E-16 valida contra refutation-unit/1.0", [], R.validar(doc, R.SCHEMA_UNIDAD))
        t.igual("E-16 es esa unidad", pendiente["refutationUnitId"], doc["refutationUnitId"])
        bloqueada = [u for u in _unidades(proy) if u["status"] == "BLOCKED"][0]
        t.igual("E-16 una bloqueada sale con 2", 2,
                _cli(proy, "refute", CLAVE, "--unit", bloqueada["refutationUnitId"])[0])
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(pendiente)))
        t.igual("E-16 una ya resuelta sale con 2", 2,
                _cli(proy, "refute", CLAVE, "--unit", pendiente["refutationUnitId"])[0])
    finally:
        _borrar(proy)


def _registro(t, nombre, v, codigo, proy=None):
    propio = proy is None
    proy = proy or _proyecto()
    try:
        if propio:
            R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        v = v(u) if callable(v) else v
        texto = v if isinstance(v, str) else json.dumps(v)
        t.verdadero("%s: se rechaza con %s" % (nombre, codigo),
                    _levanta(lambda: R.registrar(str(proy), CLAVE, texto), codigo))
        t.verdadero("%s: y no se guarda nada" % nombre,
                    not (proy / ".claude" / "refutaciones" / CLAVE / "verdicts").exists()
                    or not list((proy / ".claude" / "refutaciones" / CLAVE / "verdicts").glob(
                        "*.json")))
    finally:
        if propio:
            _borrar(proy)


def test_e17_no_lee_fuera_del_alcance(t):
    _registro(t, "E-17 evidencia fuera del alcance",
              lambda u: _veredicto(u, evidence=[{"path": "otro/nada.py", "line": 1,
                                                 "observed": "x = 1"}]),
              "REFUTATION_OUTPUT_INVALID")
    texto = AGENTE.read_text(encoding="utf-8")
    t.contiene("E-17 el agente dice que no lee fuera del alcance",
               "No leés fuera de `evidenceScope.paths`.", texto)
    t.contiene("E-17 y que no lo amplía", "**No lo amplíes.**", texto)


def test_e18_no_descubre_otras_reglas(t):
    _registro(t, "E-18 otra ruleKey", lambda u: _veredicto(u, ruleKey="ES0902.Vu6"),
              "REFUTATION_OUTPUT_INVALID")
    texto = AGENTE.read_text(encoding="utf-8")
    t.contiene("E-18 el agente no descubre reglas", "**No descubrís reglas.**", texto)
    t.contiene("E-18 ni agrega una segunda afirmacion", "no agregues una segunda afirmación",
               texto)


def test_e19_sigue_sin_escribir(t):
    texto = AGENTE.read_text(encoding="utf-8")
    m = re.search(r"^tools:\s*(.+)$", texto, re.MULTILINE)
    t.igual("E-19 tools exactas", ["Read", "Grep", "Glob", "Skill"],
            [h.strip() for h in m.group(1).split(",")] if m else None)
    t.contiene("E-19 no escribe ni corrige", "No escribís, no corregís, no refactorizás", texto)
    t.contiene("E-19 ni propone el parche", "Corregir el código, ni proponer el parche", texto)


def test_e20_cumple_exige_cita_y_linea(t):
    _registro(t, "E-20 cumple sin cita", lambda u: _veredicto(u, citation=None),
              "REFUTATION_OUTPUT_INVALID")
    _registro(t, "E-20 cumple sin evidencia", lambda u: _veredicto(u, evidence=[]),
              "REFUTATION_OUTPUT_INVALID")
    _registro(t, "E-20 cumple sin linea",
              lambda u: _veredicto(u, evidence=[{"path": "src/sesion.py", "line": None,
                                                 "observed": "TIMEOUT"}]),
              "REFUTATION_OUTPUT_INVALID")
    _registro(t, "E-20 cumple citando otra skill",
              lambda u: _veredicto(u, citation={"skillId": "dev-ui", "locator": "p. 1"}),
              "REFUTATION_OUTPUT_INVALID")
    texto = AGENTE.read_text(encoding="utf-8")
    t.igual("E-20 la regla sigue una sola vez", 1, texto.count(
        "Nunca declares `cumple` sin poder citar la regla con su página y señalar la línea."))


def test_e21_sin_regla_citable_es_sin_verificar(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        t.verdadero("E-21 un cumple sin cita no entra en su lugar",
                    _levanta(lambda: R.registrar(str(proy), CLAVE,
                                                 json.dumps(_veredicto(u, citation=None)))))
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(
            u, "sin-verificar", reason="RULE_NOT_CITABLE", needed="abrir ES0902 pág. 12")))
        doc = R.leer(str(proy), CLAVE)[0]
        t.igual("E-21 el sin-verificar entra", "sin-verificar", doc["units"][0]["verdict"])
        t.igual("E-21 y cuenta como sin-verificar", 1, doc["counts"]["sinVerificar"])
    finally:
        _borrar(proy)


def test_e22_evidencia_insuficiente(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        for nombre, cambio in (("sin motivo", {"reason": None}), ("sin needed", {"needed": " "})):
            t.verdadero("E-22 %s se rechaza" % nombre,
                        _levanta(lambda c=cambio: R.registrar(
                            str(proy), CLAVE, json.dumps(_veredicto(u, "sin-verificar", **c))),
                            "REFUTATION_OUTPUT_INVALID"))
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u, "sin-verificar")))
        t.igual("E-22 EVIDENCE_INSUFFICIENT entra", "sin-verificar",
                R.leer(str(proy), CLAVE)[0]["units"][0]["verdict"])
    finally:
        _borrar(proy)


def test_e23_incumple_exige_evidencia(t):
    _registro(t, "E-23 incumple sin evidencia",
              lambda u: _veredicto(u, "incumple", evidence=[]), "REFUTATION_OUTPUT_INVALID")
    _registro(t, "E-23 incumple con evidencia fuera del alcance",
              lambda u: _veredicto(u, "incumple", evidence=[{"path": "otro/nada.py", "line": 1,
                                                             "observed": "x"}]),
              "REFUTATION_OUTPUT_INVALID")


def test_e24_lo_guardado_valida(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"], checks=["session-inactivity-timeout"])})
    try:
        R.compilar(str(proy), CLAVE)
        us = _unidades(proy)
        _checks(proy, [_check(us[0])])
        R.compilar(str(proy), CLAVE)
        u = [x for x in _unidades(proy) if x["status"] == "PENDING_SEMANTIC"][0]
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u, "incumple")))
        guardados = list((proy / ".claude" / "refutaciones" / CLAVE / "verdicts").glob("*.json"))
        t.igual("E-24 dos veredictos guardados (check y refutador)", 2, len(guardados))
        for ruta in guardados:
            t.igual("E-24 %s valida" % ruta.name, [],
                    R.validar(json.loads(ruta.read_text(encoding="utf-8")), R.SCHEMA_VEREDICTO))
    finally:
        _borrar(proy)


def test_e25_prosa_o_json_roto_se_rechaza(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        bueno = json.dumps(_veredicto(u))
        for nombre, texto in (("prosa antes", "Este es el veredicto: " + bueno),
                              ("prosa despues", bueno + "\nEspero que sirva."),
                              ("bloque de codigo", "```json\n" + bueno + "\n```"),
                              ("JSON roto", bueno[:-3])):
            _registro(t, "E-25 %s" % nombre, texto, "REFUTATION_OUTPUT_INVALID", proy)
        ruta = proy / "v.json"
        _escribir(ruta, "```json\n" + bueno + "\n```")
        codigo, _, err = _cli(proy, "refute", CLAVE, "--record", str(ruta))
        t.igual("E-25 la CLI sale con 2", 2, codigo)
        t.contiene("E-25 y dice el codigo", "REFUTATION_OUTPUT_INVALID", err)
    finally:
        _borrar(proy)


# -- E-26 a E-31: huellas e invalidacion ---------------------------------------

def test_e26_un_byte_cambia_la_huella(t):
    proy = _proyecto(git=False)
    try:
        antes = R.huella_de_evidencia(str(proy), ["src/sesion.py"])
        _escribir(proy / "src" / "sesion.py", "TIMEOUT = 901\n")
        t.verdadero("E-26 otra huella", antes != R.huella_de_evidencia(str(proy),
                                                                      ["src/sesion.py"]))
    finally:
        _borrar(proy)


def test_e27_head_igual_y_archivo_tocado_invalida(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        head = R.revision_del_repo(str(proy))
        t.verdadero("E-27 hay HEAD", bool(head))
        _escribir(proy / "src" / "sesion.py", "TIMEOUT = 5\n")
        t.igual("E-27 HEAD no cambio", head, R.revision_del_repo(str(proy)))
        t.verdadero("E-27 --record sale con EVIDENCE_STALE",
                    _levanta(lambda: R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u))),
                             "REFUTATION_EVIDENCE_STALE"))
        t.igual("E-27 y no guarda nada", [], list(
            (proy / ".claude" / "refutaciones" / CLAVE).glob("verdicts/*.json")))
        # Un veredicto guardado deja de valer en la compilacion siguiente.
        _escribir(proy / "src" / "sesion.py", "TIMEOUT = 900\n")
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u, "sin-verificar")))
        _escribir(proy / "src" / "sesion.py", "TIMEOUT = 5\n")
        doc = R.compilar(str(proy), CLAVE)
        t.igual("E-27 el veredicto viejo ya no vale", "PENDING_SEMANTIC",
                _unidades(proy)[0]["status"])
        t.verdadero("E-27 y se avisa", any("REFUTATION_EVIDENCE_STALE" in a
                                           for a in doc["warnings"]))
    finally:
        _borrar(proy)


def _clave_con(u, **cambios):
    otra = json.loads(json.dumps(u))
    for campo, valor in cambios.items():
        otra[campo] = valor
    return R.clave_de_cache(otra)


def test_e28_a_e31_cada_huella_entra_en_la_clave(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        base = R.clave_de_cache(u)
        t.igual("E-28..31 la clave guardada es la calculada", u["cacheKey"], base)
        t.verdadero("E-28 otra revision, otra clave", base != _clave_con(u, repoRevision="f" * 40))
        t.verdadero("E-29 otra skill, otra clave",
                    base != _clave_con(u, skillFingerprint="sha256:" + "1" * 64))
        t.verdadero("E-30 otra fuente normativa, otra clave",
                    base != _clave_con(u, normativeSourceFingerprint="sha256:" + "2" * 64))
        t.verdadero("E-31 otro contrato, otra clave",
                    base != _clave_con(u, refuterContract={"version": R.CONTRATO,
                                                           "fingerprint": "sha256:" + "3" * 64}))
        t.verdadero("E-31 y otra version del contrato, otra clave",
                    base != _clave_con(u, refuterContract={
                        "version": "dev-refutador/9.9",
                        "fingerprint": u["refuterContract"]["fingerprint"]}))
        # Y las huellas son de los archivos de verdad, no un numero cualquiera.
        t.igual("E-29 skillFingerprint son los bytes del SKILL.md",
                R.huella_de_archivo(reg._ruta_de("skills/%s/SKILL.md" % u["skillId"],
                                                 reg.__file__)), u["skillFingerprint"])
        t.igual("E-31 refuterContract son los bytes de dev-refutador.md",
                R.huella_de_archivo(str(AGENTE)), u["refuterContract"]["fingerprint"])
    finally:
        _borrar(proy)


def test_e29_e31_un_archivo_distinto_da_otra_clave_de_punta_a_punta(t):
    """E-29 y E-31 por el compilador: la skill o el contrato cambian en disco -en una copia- y
    la clave de la unidad cambia sola."""
    proy = _proyecto()
    temporal = Path(tempfile.mkdtemp())
    original_skill, original_contrato = R.skill_para, R.contrato_del_refutador
    try:
        R.compilar(str(proy), CLAVE)
        base = _unidades(proy)[0]["cacheKey"]
        skill = temporal / "SKILL.md"
        _escribir(skill, "otra skill\n")
        R.skill_para = lambda e, s, d: ("dev-appsec-review", str(skill))
        R.compilar(str(proy), CLAVE)
        t.verdadero("E-29 otra SKILL.md, otra cacheKey", base != _unidades(proy)[0]["cacheKey"])
        R.skill_para = original_skill
        R.contrato_del_refutador = lambda desde=None: {
            "version": R.CONTRATO, "fingerprint": R.huella_de_bytes(b"otro contrato")}
        R.compilar(str(proy), CLAVE)
        t.verdadero("E-31 otro dev-refutador.md, otra cacheKey",
                    base != _unidades(proy)[0]["cacheKey"])
    finally:
        R.skill_para, R.contrato_del_refutador = original_skill, original_contrato
        _borrar(proy)
        shutil.rmtree(str(temporal), ignore_errors=True)


def test_e30_otra_entrada_de_matriz_da_otra_clave_de_punta_a_punta(t):
    """E-30 por el compilador: la entrada de la regla en la matriz cambia -en memoria, sin tocar
    el archivo instalado- y cambian la huella normativa y la clave. La afirmacion no, asi que
    lo que mueve la clave es la fuente normativa."""
    proy = _proyecto()
    original = R._matrices
    try:
        R.compilar(str(proy), CLAVE)
        antes = _unidades(proy)[0]
        entrada, version = R.regla_de_matriz(original(R.__file__), "ES0902", "Vu4")
        t.igual("E-30 la huella normativa es la de la entrada de la matriz",
                R.huella({"standard": "ES0902", "version": version, "rule": entrada}),
                antes["normativeSourceFingerprint"])

        def otra_matriz(desde):
            m = original(desde)
            doc, v = m["ES0902"]
            doc = json.loads(json.dumps(doc))
            for r in doc["rules"]:
                if r["id"] == "Vu4":
                    r["policies"] = list(r.get("policies") or []) + ["otra-politica"]
            m["ES0902"] = (doc, v)
            return m

        R._matrices = otra_matriz
        R.compilar(str(proy), CLAVE)
        despues = _unidades(proy)[0]
        t.verdadero("E-30 otra entrada, otra huella normativa",
                    antes["normativeSourceFingerprint"] != despues["normativeSourceFingerprint"])
        t.verdadero("E-30 y otra cacheKey", antes["cacheKey"] != despues["cacheKey"])
        t.igual("E-30 con la misma afirmacion", antes["claim"], despues["claim"])
    finally:
        R._matrices = original
        _borrar(proy)


# -- E-32 a E-36: la cache -----------------------------------------------------

def _dos_tareas(t, veredicto):
    proy = _proyecto()
    R.compilar(str(proy), CLAVE)
    u = _unidades(proy)[0]
    v = _veredicto(u, veredicto)
    R.registrar(str(proy), CLAVE, json.dumps(v))
    _proyecto(clave=OTRA, proy=proy)
    doc = R.compilar(str(proy), OTRA)
    return proy, v, doc


def test_e32_e33_cumple_e_incumple_se_reusan(t):
    for ide, veredicto in (("E-32", "cumple"), ("E-33", "incumple")):
        proy, v, doc = _dos_tareas(t, veredicto)
        try:
            u = _unidades(proy, OTRA)[0]
            guardado = R.leer(str(proy), OTRA)[2][0]
            t.igual("%s resuelta por cache" % ide, "CACHE", u["resolutionPath"])
            t.igual("%s cacheHit" % ide, True, guardado["cacheHit"])
            t.igual("%s el veredicto" % ide, veredicto, guardado["verdict"])
            t.igual("%s las evidencias originales" % ide, v["evidence"], guardado["evidence"])
            t.igual("%s la huella original" % ide, v["evidenceFingerprint"],
                    guardado["evidenceFingerprint"])
            t.igual("%s cuenta un acierto" % ide, 1, doc["counts"]["cacheHits"])
        finally:
            _borrar(proy)


def test_e34_sin_verificar_no_se_reusa(t):
    proy, _, doc = _dos_tareas(t, "sin-verificar")
    try:
        t.igual("E-34 la otra tarea queda pendiente", "PENDING_SEMANTIC",
                _unidades(proy, OTRA)[0]["status"])
        t.igual("E-34 sin aciertos", 0, doc["counts"]["cacheHits"])
    finally:
        _borrar(proy)


def test_e35_e46_un_acierto_no_escribe_consumo(t):
    proy, _, _ = _dos_tareas(t, "cumple")
    try:
        t.verdadero("E-35 no hay libro del Bloque 4 en la tarea resuelta por cache",
                    not os.path.exists(c_libro.ruta_de(str(proy), OTRA)))
        t.verdadero("E-46 ni en la que la refuto, porque nadie ingirio nada",
                    not os.path.exists(c_libro.ruta_de(str(proy), CLAVE)))
        from contabilidad import eventos as c_eventos
        t.verdadero("E-46 y un evento con cacheHit=true no se puede escribir",
                    bool(c_eventos.validar_metadata({"metadata": {"cacheHit": True}})))
    finally:
        _borrar(proy)


def test_e36_cache_adulterada_no_se_usa(t):
    def adulterar_clave(d):
        d["cacheKey"] = "sha256:" + "9" * 64

    def adulterar_huella(d):
        d["evidenceFingerprint"] = "sha256:" + "8" * 64

    for nombre, adulterar in (("otra cacheKey", adulterar_clave),
                              ("otra huella", adulterar_huella),
                              ("JSON roto", None)):
        proy, _, _ = _dos_tareas(t, "cumple")
        try:
            ruta = list((proy / ".claude" / "refutaciones" / "cache").glob("*.json"))[0]
            if adulterar is None:
                ruta.write_text("{roto", encoding="utf-8")
            else:
                d = json.loads(ruta.read_text(encoding="utf-8"))
                adulterar(d)
                ruta.write_text(json.dumps(d), encoding="utf-8")
            shutil.rmtree(str(proy / ".claude" / "refutaciones" / OTRA / "verdicts"))
            doc = R.compilar(str(proy), OTRA)
            t.igual("E-36 %s: no se usa" % nombre, "PENDING_SEMANTIC",
                    _unidades(proy, OTRA)[0]["status"])
            t.verdadero("E-36 %s: y se avisa" % nombre,
                        any("REFUTATION_CACHE_INVALID" in a for a in doc["warnings"]))
        finally:
            _borrar(proy)


# -- E-37 a E-42: el agregador -------------------------------------------------

def test_e37_sin_modelo_ni_red(t):
    texto = (BIN / "orquestacion" / "refutacion.py").read_text(encoding="utf-8")
    for prohibido in ("anthropic", "openai", "urllib", "http.client", "requests", "socket"):
        t.verdadero("E-37 no importa %s" % prohibido,
                    not re.search(r"^\s*(import|from)\s+%s\b" % re.escape(prohibido), texto,
                                  re.MULTILINE))


def _u(i, estado="RESOLVED", camino="SEMANTIC_REFUTATION"):
    return {"refutationUnitId": "REF-%03d" % i, "status": estado, "resolutionPath": camino}


def _v(i, veredicto, camino="SEMANTIC_REFUTATION"):
    return {"refutationUnitId": "REF-%03d" % i, "verdict": veredicto, "resolutionPath": camino}


def test_e38_a_e41_el_estado(t):
    t.igual("E-38 todo cumple es PASS", "PASS",
            R.agregar([_u(1), _u(2)], [_v(1, "cumple"), _v(2, "cumple")])[0])
    t.igual("E-39 un incumple es FAIL aunque haya sin resolver", "FAIL",
            R.agregar([_u(1), _u(2, "BLOCKED", None), _u(3, "PENDING_SEMANTIC", None)],
                      [_v(1, "incumple")])[0])
    t.igual("E-40 sin incumple y con una sin resolver es INCOMPLETE", "INCOMPLETE",
            R.agregar([_u(1), _u(2, "PENDING_SEMANTIC", None)], [_v(1, "cumple")])[0])
    t.igual("E-40 y con un sin-verificar tambien", "INCOMPLETE",
            R.agregar([_u(1), _u(2)], [_v(1, "cumple"), _v(2, "sin-verificar")])[0])
    t.igual("E-41 cero unidades es NOTHING_TO_VERIFY", "NOTHING_TO_VERIFY", R.agregar([], [])[0])
    proy = _proyecto({"WU-1": {"standard": {"id": "ES0902"}, "applicableRules": [],
                               "notApplicableRules": ["Vu4"], "unresolvedRules": [],
                               "declaredPolicies": [], "declaredChecks": []}})
    try:
        base = json.loads((proy / ".claude" / "planes" / (CLAVE + ".json")).read_text(
            encoding="utf-8"))
        for wu in base["workUnits"]:
            wu["normative"] = wu["normative"]["standards"]["ES0902"]
        _escribir(proy / ".claude" / "planes" / (CLAVE + ".json"), json.dumps(base))
        doc = R.compilar(str(proy), CLAVE)
        t.igual("E-41 un plan sin reglas es NOTHING_TO_VERIFY", "NOTHING_TO_VERIFY",
                doc["status"])
    finally:
        _borrar(proy)


def test_e42_contadores_deterministas(t):
    us = [_u(1), _u(2, "RESOLVED", "CACHE"), _u(3, "RESOLVED", "DETERMINISTIC_CHECK"),
          _u(4, "BLOCKED", None), _u(5, "PENDING_SEMANTIC", None)]
    vs = [_v(1, "cumple"), _v(2, "incumple", "CACHE"), _v(3, "cumple", "DETERMINISTIC_CHECK")]
    a = R.agregar(us, vs)
    t.igual("E-42 dos veces, lo mismo", a, R.agregar(us, vs))
    t.igual("E-42 en otro orden, lo mismo", a, R.agregar(list(reversed(us)), list(reversed(vs))))
    t.igual("E-42 los contadores", {"units": 5, "cumple": 2, "incumple": 1, "sinVerificar": 2,
                                    "cacheHits": 1, "checkResolved": 1, "semanticRuns": 1,
                                    "pending": 1, "blocked": 1}, a[1])


# -- E-43 a E-47: el Bloque 4 --------------------------------------------------

def _transcripcion(carpeta):
    ruta = carpeta / "sesion.jsonl"
    lineas = [{"type": "assistant", "sessionId": "s-ra", "timestamp": "2026-09-25T10:00:00",
               "message": {"id": "msg_ra_%d" % i, "model": "m",
                           "usage": {"input_tokens": 10, "output_tokens": 20,
                                     "cache_read_input_tokens": 0,
                                     "cache_creation_input_tokens": 0}}} for i in (1, 2)]
    _escribir(ruta, "\n".join(json.dumps(x) for x in lineas) + "\n")
    return ruta


def test_e43_a_e45_atribucion_de_la_refutacion(t):
    proy = _proyecto({"WU-7": _bloque(["Vu4"])})
    try:
        R.compilar(str(proy), CLAVE)
        fuente = _transcripcion(proy)
        codigo, _, err = _cli(proy, "contabilidad", CLAVE, "--ingerir", str(fuente),
                              "--refutacion", "REF-001")
        t.igual("E-43 la ingesta sale con 0", 0, codigo)
        eventos = [e for e in c_libro.leer(c_libro.ruta_de(str(proy), CLAVE))
                   if e.get("eventType") == "MODEL_CALL_COMPLETED"]
        t.igual("E-43 dos llamadas", 2, len(eventos))
        t.igual("E-43 workUnitId original", {"WU-7"}, set(e["workUnitId"] for e in eventos))
        t.igual("E-45 agentId dev-refutador", {"dev-refutador"},
                set(e["agentId"] for e in eventos))
        for e in eventos:
            m = e["metadata"]
            t.igual("E-44 phase", "refutation", m.get("phase"))
            t.igual("E-44 refutationUnitId", "REF-001", m.get("refutationUnitId"))
            t.igual("E-44 resolutionPath", "SEMANTIC_REFUTATION", m.get("resolutionPath"))
            t.igual("E-44 cacheHit", False, m.get("cacheHit"))
        t.igual("E-45 otro --agente sale con 2", 2,
                _cli(proy, "contabilidad", CLAVE, "--ingerir", str(fuente), "--refutacion",
                     "REF-001", "--agente", "dev-backend")[0])
        t.igual("E-43 otra --unidad sale con 2", 2,
                _cli(proy, "contabilidad", CLAVE, "--ingerir", str(fuente), "--refutacion",
                     "REF-001", "--unidad", "WU-1")[0])
    finally:
        _borrar(proy)


def test_e47_resuelta_por_check_no_escribe_consumo(t):
    proy, doc, u = _con_check(t)
    try:
        t.igual("E-47 resuelta por check", "DETERMINISTIC_CHECK", u["resolutionPath"])
        t.verdadero("E-47 sin libro del Bloque 4",
                    not os.path.exists(c_libro.ruta_de(str(proy), CLAVE)))
        t.verdadero("E-47 y no se le puede atribuir consumo",
                    _levanta(lambda: R.atribucion(str(proy), CLAVE, "REF-001")))
    finally:
        _borrar(proy)


# -- E-48 a E-50: el micro-lote ------------------------------------------------

def test_e48_reglas_distintas_no_van_juntas(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"])})
    try:
        R.compilar(str(proy), CLAVE)
        t.igual("E-48 --unit con dos reglas sale con 2", 2,
                _cli(proy, "refute", CLAVE, "--unit", "REF-001,REF-002")[0])
        t.verdadero("E-48 y la funcion dice por que",
                    _levanta(lambda: R.micro_lote(_unidades(proy)), "REFUTATION_BATCH_INVALID"))
    finally:
        _borrar(proy)


def test_e49_huellas_distintas_no_van_juntas(t):
    scope = {"WU-1": [{"scopeId": "a", "source": "workUnitFiles", "paths": ["src/sesion.py"]},
                      {"scopeId": "b", "source": "workUnitFiles", "paths": ["src/error.py"]}]}
    proy = _proyecto(scope=scope)
    try:
        R.compilar(str(proy), CLAVE)
        t.igual("E-49 misma regla, otra huella: sale con 2", 2,
                _cli(proy, "refute", CLAVE, "--unit", "REF-001,REF-002")[0])
    finally:
        _borrar(proy)


def test_e50_un_veredicto_por_unidad_del_lote(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4"]), "WU-2": _bloque(["Vu4"])})
    try:
        R.compilar(str(proy), CLAVE)
        codigo, salida, _ = _cli(proy, "refute", CLAVE, "--unit", "REF-001,REF-002")
        t.igual("E-50 un lote valido sale con 0", 0, codigo)
        sobre = json.loads(salida)
        t.igual("E-50 con las dos unidades", 2, len(sobre["units"]))
        a, b = _unidades(proy)
        t.verdadero("E-50 repetido no entra",
                    _levanta(lambda: R.registrar(str(proy), CLAVE,
                                                 json.dumps([_veredicto(a), _veredicto(a)]))))
        t.verdadero("E-50 uno invalido voltea al lote entero",
                    _levanta(lambda: R.registrar(str(proy), CLAVE, json.dumps(
                        [_veredicto(a), _veredicto(b, citation=None)]))))
        t.igual("E-50 y no se guardo ninguno", [], list(
            (proy / ".claude" / "refutaciones" / CLAVE).glob("verdicts/*.json")))
        R.registrar(str(proy), CLAVE, json.dumps([_veredicto(a), _veredicto(b, "incumple")]))
        guardados = sorted(p.name for p in (proy / ".claude" / "refutaciones" / CLAVE).glob(
            "verdicts/*.json"))
        t.igual("E-50 con los dos, uno por unidad", ["REF-001.json", "REF-002.json"], guardados)
    finally:
        _borrar(proy)


# -- E-51 a E-55: lo que no cambia ---------------------------------------------

def _plan_por_cli(proy):
    _escribir(proy / ".claude" / "contextos" / (CLAVE + ".json"), json.dumps(
        {"meta": {"task_key": CLAVE, "context_hash": "h"}, "task": {"title": "t"}}))
    _escribir(proy / "prop.json", json.dumps(
        {"objective": "o", "domains": ["backend"],
         "workUnits": [{"id": "wu-1", "objective": "x", "domain": "backend"}]}))
    codigo, salida, _ = _cli(proy, "plan", CLAVE, "--propuesta", str(proy / "prop.json"),
                             "--json")
    doc = json.loads(salida) if codigo == 0 else None
    for n in ("generated_at",):
        (doc or {}).get("meta", {}).pop(n, None)
    for h in (doc or {}).get("planHistory", []):
        h.pop("timestamp", None)
    return codigo, doc


def test_e51_el_comando_plan_no_cambia(t):
    proy = Path(tempfile.mkdtemp())
    try:
        c1, sin = _plan_por_cli(proy)
        _escribir(proy / ".claude" / "refutaciones" / CLAVE / "run.json", "{}")
        c2, con = _plan_por_cli(proy)
        t.igual("E-51 plan sale con 0", [0, 0], [c1, c2])
        t.verdadero("E-51 el mismo plan con y sin refutaciones", sin == con and sin is not None)
    finally:
        _borrar(proy)


def test_e52_session_start_no_cambia(t):
    for ruta in (RAIZ / "comun" / "hooks" / "session-start.py",
                 RAIZ / "comun" / "hooks" / "lib" / "bienvenida.py"):
        t.verdadero("E-52 %s no nombra refut" % ruta.name,
                    "refut" not in ruta.read_text(encoding="utf-8").lower())


def test_e53_e55_la_refutacion_no_escribe_seguridad(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(_unidades(proy)[0])))
        t.verdadero("E-53 nada bajo .claude/runtime/security",
                    not (proy / ".claude" / "runtime" / "security").exists())
        nombres = [p.name.lower() for p in (proy / ".claude" / "refutaciones").rglob("*")]
        t.igual("E-55 nada de seguridad bajo refutaciones", [],
                [n for n in nombres if "security" in n or "ledger" in n or "seguridad" in n])
        definen = [p.relative_to(BIN).as_posix() for p in BIN.rglob("*.py")
                   if "__pycache__" not in str(p)
                   and '"security-ledger-event/1.0"' in p.read_text(encoding="utf-8")]
        t.igual("E-55 un solo modulo define el libro de seguridad",
                ["reporte_seguridad/libro.py"], definen)
    finally:
        _borrar(proy)


def test_e53_e55_corrida_completa_por_cli(t):
    """E-53 y E-55 sobre la corrida entera por la CLI, incluido el unico camino que SI escribe
    seguridad (`seguridad --refutacion`). Sin ese paso, la entrada elegia el caso donde no se
    podia fallar."""
    proy = _proyecto()
    try:
        c1 = _cli(proy, "refute", CLAVE, "--compile")[0]
        u = _unidades(proy)[0]
        ruta = proy / "v.json"
        _escribir(ruta, json.dumps(_veredicto(u, "incumple")))
        c2 = _cli(proy, "refute", CLAVE, "--record", str(ruta))[0]
        t.igual("E-53 compile y record salen con 0", [0, 0], [c1, c2])
        t.verdadero("E-53 compile y record no escriben seguridad",
                    not (proy / ".claude" / "runtime" / "security").exists())
        c3 = _cli(proy, "contabilidad", CLAVE, "--ingerir", str(_transcripcion(proy)),
                  "--refutacion", u["refutationUnitId"])[0]
        c4 = _cli(proy, "seguridad", CLAVE, "--refutacion")[0]
        c5 = _cli(proy, "refute", CLAVE, "--summary")[0]
        t.igual("E-55 contabilidad, seguridad y summary salen con 0", [0, 0, 0], [c3, c4, c5])
        t.verdadero("E-55 seguridad escribio en su libro de siempre",
                    os.path.isfile(s_libro.ruta_de(str(proy), CLAVE)))
        nombres = [p.relative_to(proy).as_posix().lower()
                   for p in (proy / ".claude" / "refutaciones").rglob("*")]
        t.igual("E-55 y nada de seguridad bajo refutaciones", [],
                [n for n in nombres if "security" in n or "ledger" in n or "seguridad" in n])
    finally:
        _borrar(proy)


def test_e54_es0902_entra_al_libro_de_seguridad_existente(t):
    unidades = {"WU-1": _bloque(["Vu4"])}
    proy = _proyecto(unidades)
    try:
        plan = json.loads((proy / ".claude" / "planes" / (CLAVE + ".json")).read_text(
            encoding="utf-8"))
        # Una regla de ES0901 al lado, que no tiene que entrar al libro de seguridad.
        plan["workUnits"][0]["normative"]["standards"]["ES0901"] = {
            "standard": {"id": "ES0901", "version": "6.3"}, "applicableRules": ["G1"],
            "notApplicableRules": [], "unresolvedRules": [], "declaredPolicies": [],
            "declaredChecks": []}
        _escribir(proy / ".claude" / "planes" / (CLAVE + ".json"), json.dumps(plan))
        R.compilar(str(proy), CLAVE)
        us = _unidades(proy)
        for u in us:
            R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u, "incumple")))
        codigo, _, err = _cli(proy, "seguridad", CLAVE, "--refutacion")
        t.igual("E-54 seguridad --refutacion sale con 0", 0, codigo)
        eventos = s_libro.leer(s_libro.ruta_de(str(proy), CLAVE))
        revisiones = [e for e in eventos if e.get("eventType") == "REVIEW_EVALUATION"]
        t.igual("E-54 una review por la unidad ES0902", 1, len(revisiones))
        if revisiones:
            t.igual("E-54 con la regla", "Vu4", revisiones[0]["normative"]["rule"])
            t.igual("E-54 y el resultado", "FAIL", revisiones[0]["result"])
            t.igual("E-54 del productor de la refutacion", "desde_refutacion",
                    revisiones[0]["details"]["producer"])
        t.igual("E-54 ninguna de ES0901", [],
                [e for e in eventos if (e.get("normative") or {}).get("standard") == "ES0901"])
        t.verdadero("E-54 y nada de un RULE_EVALUATION inventado",
                    not [e for e in eventos if e.get("eventType") == "RULE_EVALUATION"])
        u902 = [u for u in us if u["standard"]["id"] == "ES0902"][0]
        u901 = [u for u in us if u["standard"]["id"] == "ES0901"][0]
        t.verdadero("E-54 el productor rechaza una unidad de ES0901",
                    _raises(lambda: s_prod.desde_refutacion(
                        _veredicto(u901), u901, CLAVE, {"project": "p", "environment": None})))
        t.verdadero("E-54 y acepta la de ES0902", bool(s_prod.desde_refutacion(
            _veredicto(u902), u902, CLAVE, {"project": "p", "environment": None})))
    finally:
        _borrar(proy)


def _raises(funcion):
    try:
        funcion()
    except Exception:                     # noqa: BLE001
        return True
    return False


# -- E-56 a E-60: presentacion y datos -----------------------------------------

def _textos(nodo):
    if isinstance(nodo, dict):
        return [x for v in nodo.values() for x in _textos(v)] + [k for k in nodo]
    if isinstance(nodo, list):
        return [x for v in nodo for x in _textos(v)]
    return [nodo] if isinstance(nodo, str) else []


def test_e56_e57_espanol_para_personas_canonico_para_maquinas(t):
    """E-57 con una corrida que TIENE avisos: un check sin resolver, una unidad bloqueada y un
    veredicto que quedo viejo. Una corrida sin avisos no puede fallar esto (lo encontro el
    refutador: los avisos iban en espanol y sin tildes, y la regex de tildes no los veia)."""
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"], sin_resolver=["Vu1"],
                                      checks=["session-inactivity-timeout"])})
    try:
        R.compilar(str(proy), CLAVE)
        us = {u["standard"]["ruleKey"]: u for u in _unidades(proy)}
        _checks(proy, [_check(us["ES0902.Vu4"], "APPLICABILITY_UNRESOLVED")])
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(us["ES0902.Vu6"], "sin-verificar")))
        _escribir(proy / "src" / "sesion.py", "TIMEOUT = 5\n")
        R.compilar(str(proy), CLAVE)
        u = [x for x in _unidades(proy) if x["status"] == "PENDING_SEMANTIC"][0]
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u)))
        codigo, texto, _ = _cli(proy, "refute", CLAVE, "--summary")
        t.igual("E-56 --summary sale con 0", 0, codigo)
        for palabra in ("Refutación", "cumple", "incumple", "sin verificar", "Estado"):
            t.contiene("E-56 dice «%s»" % palabra, palabra, texto)
        t.contiene("E-56 y los avisos tambien en espanol", "va al refutador", texto)
        for accion in ("--summary", "--status"):
            codigo, salida, _ = _cli(proy, "refute", CLAVE, accion, "--json")
            doc = json.loads(salida)
            t.igual("E-57 %s --json: estado canonico" % accion, "INCOMPLETE", doc["status"])
            if accion == "--status":
                avisos = doc["warnings"]
                t.verdadero("E-57 la corrida tiene avisos para mirar", len(avisos) >= 2)
                t.verdadero("E-57 incluye el del check y el viejo",
                            any(a.startswith("REFUTATION_CHECK_UNRESOLVED") for a in avisos)
                            and any(a.startswith("REFUTATION_EVIDENCE_STALE") for a in avisos))
                for a in avisos:
                    t.verdadero("E-57 aviso canonico: %s" % a, bool(R.AVISO.match(a)))
                t.igual("E-57 la corrida valida contra su schema", [],
                        R.validar(doc, R.SCHEMA_CORRIDA))
                for prosa_ in ("REFUTATION_CHECK_UNRESOLVED: va al refutador",
                               "hay checks que no cierran", "va-al-refutador"):
                    otra = dict(doc, warnings=[prosa_])
                    t.verdadero("E-57 el schema de la corrida rechaza «%s»" % prosa_,
                                bool(R.validar(otra, R.SCHEMA_CORRIDA)))
                veredictos = set(u["verdict"] for u in doc["units"])
                t.verdadero("E-57 veredictos canonicos",
                            veredictos <= {"cumple", "incumple", "sin-verificar", None})
                t.verdadero("E-57 estados canonicos",
                            set(u["status"] for u in doc["units"]) <= {
                                "PENDING_SEMANTIC", "RESOLVED", "BLOCKED"})
            # Ningun texto con espacios: los ids, estados y huellas no tienen, la prosa si,
            # con tildes o sin ellas.
            prosa = [x for x in _textos(doc) if " " in x]
            t.igual("E-57 %s --json sin prosa" % accion, [], prosa)
    finally:
        _borrar(proy)


def test_e58_no_se_guardan_prompts(t):
    proy = _proyecto({"WU-1": _bloque(["Vu4", "Vu6"])})
    try:
        R.compilar(str(proy), CLAVE)
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(_unidades(proy)[0])))
        claves = set()
        for ruta in (proy / ".claude" / "refutaciones").rglob("*.json"):
            claves |= _claves(json.loads(ruta.read_text(encoding="utf-8")))
        t.igual("E-58 ninguna clave de conversacion", [], sorted(
            claves & {"prompt", "messages", "conversation", "transcript"}))
        u = _unidades(proy)[1]
        t.verdadero("E-58 el schema del veredicto no admite claves de mas",
                    bool(R.validar(dict(_veredicto(u), prompt="Sos el refutador..."),
                                   R.SCHEMA_VEREDICTO)))
        t.verdadero("E-58 y --record lo rechaza",
                    _levanta(lambda: R.registrar(str(proy), CLAVE, json.dumps(
                        dict(_veredicto(u), prompt="Sos el refutador..."))),
                        "REFUTATION_OUTPUT_INVALID"))
    finally:
        _borrar(proy)


def test_e59_secretos_fuera(t):
    proy = _proyecto()
    try:
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        R.registrar(str(proy), CLAVE, json.dumps(_veredicto(u, evidence=[
            {"path": "src/sesion.py", "line": 1, "observed": "token " + TOKEN}])))
        guardado = (proy / ".claude" / "refutaciones" / CLAVE / "verdicts" /
                    "REF-001.json").read_text(encoding="utf-8")
        t.no_contiene("E-59 el token no queda entero en el veredicto", TOKEN, guardado)
        t.contiene("E-59 y se ve que se redacto", "redactado", guardado)
    finally:
        _borrar(proy)
    proy = _proyecto(scope={"WU-1": [{"scopeId": "s", "source": "workUnitFiles",
                                      "paths": ["src/sesion.py", ".env"]}]})
    try:
        _escribir(proy / ".env", "CLAVE=" + TOKEN + "\n")
        R.compilar(str(proy), CLAVE)
        u = _unidades(proy)[0]
        t.igual("E-59 un .env en el alcance bloquea la unidad", "BLOCKED", u["status"])
        t.igual("E-59 y no entra ninguna ruta", [], u["evidenceScope"]["paths"])
    finally:
        _borrar(proy)


def test_e60_nunca_mas_rutas_que_las_declaradas(t):
    casos = (("una ruta que no existe", ["src/sesion.py", "src/no-existe.py"]),
             ("una que sube", ["src/sesion.py", "../fuera.py"]),
             ("un comodin", ["src/*.py"]),
             ("absoluta", ["C:/Windows/win.ini"]))
    for nombre, rutas in casos:
        proy = _proyecto(scope={"WU-1": [{"scopeId": "s", "source": "workUnitFiles",
                                          "paths": rutas}]})
        try:
            R.compilar(str(proy), CLAVE)
            u = _unidades(proy)[0]
            t.igual("E-60 %s: cero rutas" % nombre, [], u["evidenceScope"]["paths"])
            t.igual("E-60 %s: bloqueada" % nombre, "REFUTATION_SCOPE_UNRESOLVED", u["failure"])
        finally:
            _borrar(proy)
    proy = _proyecto(scope={"WU-1": [{"scopeId": "s", "source": "workUnitFiles",
                                      "paths": ["src"]}]})
    try:
        R.compilar(str(proy), CLAVE)
        t.igual("E-60 un directorio da sus archivos y nada mas",
                ["src/error.py", "src/sesion.py"], _unidades(proy)[0]["evidenceScope"]["paths"])
    finally:
        _borrar(proy)
