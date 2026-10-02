# Flow Governance, Wave 5: fallar cerrado.
#
# Escenarios E-01 a E-24 y E-35 a E-41 de docs/cambios/fail-closed-hardening/spec.md. E-25 a E-33
# son los archivos de la suite que nombran; E-34 es la compuerta entera.
#
# Reusa los fixtures de los casos que ya los tienen: el plan de 20, el reporte de seguridad de 48,
# el Bloque 4 de 30, la Context Bar de 53 y los proyectos del flujo de 62. Nada sale a la red.
import importlib
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
sys.path.insert(0, str(BIN))


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M20 = _cargar("caso_20_para_65", RAIZ / "tests" / "casos" / "20_orquestacion.py")
M30 = _cargar("caso_30_para_65", RAIZ / "tests" / "casos" / "30_b4_contabilidad.py")
M48 = _cargar("caso_48_para_65", RAIZ / "tests" / "casos" / "48_reporte_de_seguridad.py")
M53 = _cargar("caso_53_para_65", RAIZ / "tests" / "casos" / "53_context_bar.py")
W2 = _cargar("caso_62_para_65", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")

A = W2.A
ESTADOS_DE_INTEGRACION = ("NOT_CONFIGURED", "AUTHENTICATION_FAILED", "CONNECTION_FAILED",
                          "PERMISSION_DENIED", "AVAILABLE")
INTEGRIDAD = ("SOURCE_INTEGRITY_ALERT", "SOURCE_CHANGED_SAME_VERSION", "VERSION_REGRESSION")


def _registro():
    return importlib.import_module("integraciones.registro")


def _cap():
    return importlib.import_module("orquestacion.capacidades")


def _plan_mod():
    return importlib.import_module("orquestacion.plan")


def _frescura():
    return importlib.import_module("orquestacion.frescura")


def _cli_mod():
    return _cargar("dev_harness_65", CLI)


class _Consola(object):
    def __init__(self):
        self.lineas = []

    def linea(self, texto=""):
        self.lineas.append(str(texto))

    def evento(self, *_a, **_k):
        pass

    def texto(self):
        return "\n".join(self.lineas)


def _todas_disabled():
    return dict((c, "DISABLED") for c in _registro().soporte())


def _integraciones(jira="NOT_CONFIGURED", gitlab="NOT_CONFIGURED"):
    return {"jira": {"estado": jira}, "gitlab": {"estado": gitlab}}


def _disp(capacidad, capacidades=None, integraciones=None, locales=()):
    try:
        return _registro().disponibilidad(capacidad, capacidades, integraciones, locales)
    except Exception as e:                                     # noqa: BLE001
        return {"error": repr(e)}


def _armar(unidades, capacidades=None, integraciones=None, fuentes=None):
    try:
        return _plan_mod().armar(M20._propuesta(unidades), M20.CONTEXTO,
                                 _todas_disabled() if capacidades is None else capacidades, {},
                                 "0.26.0", "docs/x.json", M20.PRECONDICIONES,
                                 integraciones=integraciones, fuentes=fuentes)
    except Exception as e:                                     # noqa: BLE001
        return {"error": repr(e), "capabilityGaps": [], "workUnits": [], "status": None,
                "capabilityStatus": [], "knowledgeSources": [], "warnings": []}


def _estado_de(plan, capacidad):
    for e in plan.get("capabilityStatus") or []:
        if e.get("capabilityId") == capacidad:
            return e
    return {}


def _fuentes(**estados):
    return {"sources": dict((k, {"state": v}) for k, v in estados.items())}


def _escribir_fuentes(p, **estados):
    ruta = p / ".claude" / "harness.fuentes.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(_fuentes(**estados)), encoding="utf-8")


def _escribir_registro(p, capacidades, integraciones):
    (p / ".claude" / "harness.capacidades.json").write_text(json.dumps(
        {"schema_version": "integraciones/1.0", "capacidades": capacidades,
         "integraciones": integraciones}), encoding="utf-8")


def _propuesta_con(capacidades):
    u = {"id": W2.UNIDAD, "objective": "x", "domain": "backend",
         "requiredCapabilities": list(capacidades), "dependencies": [], "signals": []}
    return {"objective": W2.OBJETIVO, "domains": ["backend"], "policies": [], "workUnits": [u]}


def _plan_json(p, clave=A):
    ruta = p / ".claude" / "planes" / (clave + ".json")
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _derivar(p):
    return W2._E().derivar(str(p), A, proceso={})


def _borrar(p):
    shutil.rmtree(str(p), ignore_errors=True)


# -- E-01 a E-09: la disponibilidad de una capacidad --------------------------------

def test_e01_soportada_y_habilitada_esta_disponible(t):
    """E-01 — soportada y ENABLED: SUPPORTED_AVAILABLE."""
    d = _disp("jira.issue.read", {"jira.issue.read": "ENABLED"}, _integraciones(jira="AVAILABLE"))
    t.igual("E-01 SUPPORTED_AVAILABLE", "SUPPORTED_AVAILABLE", d.get("availability"))
    t.igual("E-01 supported y available", [True, True], [d.get("supported"), d.get("available")])
    t.igual("E-01 de jira", "jira", d.get("integration"))
    t.igual("E-01 CAPABILITY_AVAILABLE", "CAPABILITY_AVAILABLE", d.get("reasonCode"))


def _caida(t, escenario, estado):
    d = _disp("jira.issue.read", _todas_disabled(), _integraciones(jira=estado))
    t.igual("%s SUPPORTED_UNAVAILABLE" % escenario, "SUPPORTED_UNAVAILABLE", d.get("availability"))
    t.igual("%s soportada, no disponible" % escenario, [True, False],
            [d.get("supported"), d.get("available")])
    t.igual("%s la integracion" % escenario, "jira", d.get("integration"))
    t.igual("%s su estado" % escenario, estado, d.get("integrationState"))
    t.igual("%s el motivo es el estado" % escenario, estado, d.get("reasonCode"))
    t.verdadero("%s nunca NOT_SUPPORTED" % escenario, d.get("availability") != "NOT_SUPPORTED")


def test_e02_autenticacion_fallida(t):
    """E-02 — soportada y AUTHENTICATION_FAILED: SUPPORTED_UNAVAILABLE."""
    _caida(t, "E-02", "AUTHENTICATION_FAILED")


def test_e03_conexion_fallida(t):
    """E-03 — soportada y CONNECTION_FAILED: SUPPORTED_UNAVAILABLE."""
    _caida(t, "E-03", "CONNECTION_FAILED")


def test_e04_permiso_denegado(t):
    """E-04 — soportada y PERMISSION_DENIED: SUPPORTED_UNAVAILABLE."""
    _caida(t, "E-04", "PERMISSION_DENIED")


def test_e05_sin_configurar(t):
    """E-05 — soportada y NOT_CONFIGURED: SUPPORTED_UNAVAILABLE."""
    _caida(t, "E-05", "NOT_CONFIGURED")


def test_e06_lo_que_nadie_declara_no_esta_soportado(t):
    """E-06 — ningun adapter la declara ni es local: NOT_SUPPORTED."""
    d = _disp("confluence.page.read", _todas_disabled(), _integraciones())
    t.igual("E-06 NOT_SUPPORTED", "NOT_SUPPORTED", d.get("availability"))
    t.igual("E-06 ni soportada ni disponible", [False, False], [d.get("supported"), d.get("available")])
    t.igual("E-06 sin integracion", None, d.get("integration"))
    t.igual("E-06 CAPABILITY_NOT_SUPPORTED", "CAPABILITY_NOT_SUPPORTED", d.get("reasonCode"))
    local = _disp("repository.read", {}, {}, locales=("repository.read",))
    t.igual("E-06 una local esta disponible", "SUPPORTED_AVAILABLE", local.get("availability"))


def test_e07_caida_no_se_deriva_al_constructor(t):
    """E-07 — un plan que pide algo SUPPORTED_UNAVAILABLE: sin hueco, unidad y plan BLOCKED."""
    plan = _armar([M20._unidad("u1", capacidades=["jira.issue.read"])],
                  integraciones=_integraciones(jira="AUTHENTICATION_FAILED"))
    t.igual("E-07 sin hueco", [], plan.get("capabilityGaps"))
    t.igual("E-07 la unidad BLOCKED", ["BLOCKED"], [u.get("status") for u in plan["workUnits"]])
    t.igual("E-07 el plan BLOCKED", "BLOCKED", plan.get("status"))
    t.verdadero("E-07 nunca CAPABILITY_RESOLUTION", plan.get("status") != "CAPABILITY_RESOLUTION")
    senales = [s for u in plan["workUnits"] for s in (u.get("modelPolicy") or {}).get("signals") or []]
    t.verdadero("E-07 sin la senal capability_gap", "capability_gap" not in senales)
    t.igual("E-07 dice SUPPORTED_UNAVAILABLE", "SUPPORTED_UNAVAILABLE",
            _estado_de(plan, "jira.issue.read").get("availability"))
    t.igual("E-07 el plan valida contra su schema", [],
            _plan_mod().validar(plan) if "error" not in plan else [plan["error"]])
    huecos = _cap().resolver([M20._unidad("u1", capacidades=["jira.issue.read"])], _todas_disabled(),
                             integraciones=_integraciones(jira="CONNECTION_FAILED"))[1]
    t.igual("E-07 resolver tampoco lo deriva", [], huecos)


def test_e08_lo_no_soportado_se_sigue_derivando(t):
    """E-08 — NOT_SUPPORTED se deriva a dev-tool-builder, TEMPORARY, como hasta ahora."""
    plan = _armar([M20._unidad("u1", capacidades=["no.existe"])], integraciones=_integraciones())
    huecos = plan.get("capabilityGaps") or [{}]
    t.igual("E-08 un hueco", ["no.existe"], [h.get("capability") for h in plan.get("capabilityGaps") or []])
    t.igual("E-08 derivado", "dev-tool-builder", huecos[0].get("derivedTo"))
    t.igual("E-08 temporal", "TEMPORARY", huecos[0].get("toolClass"))
    t.igual("E-08 CAPABILITY_RESOLUTION", "CAPABILITY_RESOLUTION", plan.get("status"))
    e = _estado_de(plan, "no.existe")
    t.igual("E-08 capabilityStatus NOT_SUPPORTED", "NOT_SUPPORTED", e.get("availability"))
    t.igual("E-08 y dice a quien se deriva", ["dev-tool-builder", "TEMPORARY"],
            [e.get("derivedTo"), e.get("toolClass")])


def test_e09_capability_status_no_miente(t):
    """E-09 — derivedTo/toolClass en null para una integracion caida; mostrar_plan nombra la
    integracion y su estado, no dev-tool-builder."""
    plan = _armar([M20._unidad("u1", capacidades=["gitlab.project.read"])],
                  integraciones=_integraciones(gitlab="PERMISSION_DENIED"))
    e = _estado_de(plan, "gitlab.project.read")
    for campo in ("capabilityId", "supported", "available", "availability", "integration",
                  "integrationState", "reasonCode", "derivedTo", "toolClass"):
        t.verdadero("E-09 trae %s" % campo, campo in e)
    t.igual("E-09 derivedTo y toolClass null", [None, None], [e.get("derivedTo"), e.get("toolClass")])
    consola = _Consola()
    try:
        _cli_mod().mostrar_plan(consola, plan, "x.json")
    except Exception as ex:                                    # noqa: BLE001
        consola.linea(repr(ex))
    texto = consola.texto()
    t.contiene("E-09 nombra la capacidad", "gitlab.project.read", texto)
    t.contiene("E-09 y el estado de la integracion", "PERMISSION_DENIED", texto)
    t.no_contiene("E-09 no la manda al constructor", "dev-tool-builder", texto)


# -- E-10 a E-13: un hallazgo sin resolver no deja pasar ---------------------------------

def _seguridad(*hallazgos):
    eventos = M48._conocimiento() + M48._reglas()
    for h in hallazgos:
        eventos += h
    return M48._resumir(eventos)


def _bloqueos_de_hallazgo(r):
    return [(b["state"], b["effect"]) for b in r["blockingConditions"] if b["source"] == "finding"]


def test_e10_critico_abierto_bloquea(t):
    """E-10 — CRITICAL OPEN: ACTION_REQUIRED."""
    r = _seguridad(M48._hallazgo_ev(M48._hallazgo("SEC-A", "CRITICAL")))
    t.igual("E-10 ACTION_REQUIRED", "ACTION_REQUIRED", r["systemSecurityState"])
    t.igual("E-10 un bloqueo de finding", [("OPEN", "ACTION_REQUIRED")], _bloqueos_de_hallazgo(r))


def test_e11_critico_reabierto_bloquea(t):
    """E-11 — CRITICAL REOPENED: ACTION_REQUIRED."""
    h = M48._hallazgo("SEC-R", "CRITICAL")
    r = _seguridad(M48._hallazgo_ev(h), M48._hallazgo_ev(h, "RESOLVED"),
                   M48._hallazgo_ev(h, "UPDATED", "OPEN"))
    t.igual("E-11 el estado es REOPENED", "REOPENED", r["findings"]["items"][0]["state"])
    t.igual("E-11 ACTION_REQUIRED", "ACTION_REQUIRED", r["systemSecurityState"])
    t.igual("E-11 un bloqueo de finding", [("REOPENED", "ACTION_REQUIRED")], _bloqueos_de_hallazgo(r))


def test_e12_critico_sin_resolver_es_incompleto(t):
    """E-12 — CRITICAL UNRESOLVED: REVIEW_INCOMPLETE con un bloqueo de finding; nunca READY."""
    h = M48._hallazgo("SEC-U", "CRITICAL")
    r = _seguridad(M48._hallazgo_ev(h), M48._hallazgo_ev(h, "UPDATED", "UNRESOLVED"))
    t.igual("E-12 REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE", r["systemSecurityState"])
    t.verdadero("E-12 nunca READY", r["systemSecurityState"] != "READY_FOR_SECURITY_REVIEW")
    t.igual("E-12 un bloqueo de finding", [("UNRESOLVED", "REVIEW_INCOMPLETE")], _bloqueos_de_hallazgo(r))
    con_abierto = _seguridad(M48._hallazgo_ev(h), M48._hallazgo_ev(h, "UPDATED", "UNRESOLVED"),
                             M48._hallazgo_ev(M48._hallazgo("SEC-A", "CRITICAL")))
    t.igual("E-12 incompleto gana sobre ACTION_REQUIRED", "REVIEW_INCOMPLETE",
            con_abierto["systemSecurityState"])
    _, md, _ = M48._todo(M48._conocimiento() + M48._reglas() + M48._hallazgo_ev(h)
                         + M48._hallazgo_ev(h, "UPDATED", "UNRESOLVED"))
    t.contiene("E-12 el reporte lo dice", "REVIEW_INCOMPLETE", md)


def test_e13_unresolved_no_es_open(t):
    """E-13 — UNRESOLVED no se convierte en OPEN: el item y los contadores lo conservan."""
    h = M48._hallazgo("SEC-U", "CRITICAL")
    r = _seguridad(M48._hallazgo_ev(h), M48._hallazgo_ev(h, "UPDATED", "UNRESOLVED"))
    t.igual("E-13 el item sigue UNRESOLVED", "UNRESOLVED", r["findings"]["items"][0]["state"])
    t.igual("E-13 cuenta en unresolved", 1, r["findings"]["unresolved"])
    t.igual("E-13 y no en open", 0, r["findings"]["open"])
    t.igual("E-13 ni en reopened", 0, r["findings"]["reopened"])


# -- E-14 a E-18: la frescura compuerta la operacion que depende de la fuente ------------

def test_e14_vigente_deja_planificar(t):
    """E-14 — ES0901 CURRENT: el plan no se bloquea por la fuente y la declara verificada."""
    plan = _armar([M20._unidad("u1")], capacidades={}, fuentes=_fuentes(ES0901="CURRENT"))
    fuentes = dict((f.get("standard"), f) for f in plan.get("knowledgeSources") or [])
    t.igual("E-14 ES0901 verificada", [True, False, "CURRENT"],
            [fuentes.get("ES0901", {}).get(k) for k in ("verified", "blocking", "state")])
    t.verdadero("E-14 el plan no queda BLOCKED", plan.get("status") not in ("BLOCKED", None))


def test_e15_sin_verificar_sigue_marcado(t):
    """E-15 — FRESHNESS_UNVERIFIED o sin harness.fuentes.json: el plan sigue, marcado y avisado;
    refute --compile compila y agrega REFUTATION_SOURCE_UNVERIFIED. Nunca CURRENT."""
    for rotulo, fuentes in (("sin archivo", None), ("FRESHNESS_UNVERIFIED",
                                                     _fuentes(ES0901="FRESHNESS_UNVERIFIED"))):
        plan = _armar([M20._unidad("u1")], capacidades={}, fuentes=fuentes)
        f = dict((x.get("standard"), x) for x in plan.get("knowledgeSources") or []).get("ES0901", {})
        t.igual("E-15 %s: no verificada, no bloquea" % rotulo, [False, False],
                [f.get("verified"), f.get("blocking")])
        t.igual("E-15 %s: estado FRESHNESS_UNVERIFIED" % rotulo, "FRESHNESS_UNVERIFIED", f.get("state"))
        t.verdadero("E-15 %s: el plan no queda BLOCKED" % rotulo, plan.get("status") not in ("BLOCKED", None))
        t.verdadero("E-15 %s: lo avisa" % rotulo, any("ES0901" in a for a in plan.get("warnings") or []))
    p = W2._proyecto()
    try:
        W2._listo(p)
        codigo, _, error = W2._cli(p, "refute", A, "--compile")
        t.igual("E-15 refute --compile sale 0", 0, codigo)
        run = p / ".claude" / "refutaciones" / A / "run.json"
        avisos = json.loads(run.read_text(encoding="utf-8")).get("warnings") if run.exists() else []
        t.verdadero("E-15 la corrida lo avisa",
                    "REFUTATION_SOURCE_UNVERIFIED:ES0901:FRESHNESS_UNVERIFIED" in avisos)
    finally:
        _borrar(p)


def test_e16_alerta_de_integridad_bloquea_la_operacion(t):
    """E-16 — un estado de integridad en ES0901: el plan BLOCKED, el flujo bloquea con ese codigo y
    refute --compile sale 2 sin escribir nada."""
    for estado in INTEGRIDAD:
        plan = _armar([M20._unidad("u1")], capacidades={}, fuentes=_fuentes(ES0901=estado))
        f = dict((x.get("standard"), x) for x in plan.get("knowledgeSources") or []).get("ES0901", {})
        t.igual("E-16 %s: bloquea" % estado, True, f.get("blocking"))
        t.igual("E-16 %s: el plan BLOCKED" % estado, "BLOCKED", plan.get("status"))
    p = W2._proyecto()
    try:
        _escribir_fuentes(p, ES0901="SOURCE_INTEGRITY_ALERT")
        W2._contexto(p, A)
        W2._plan(p, A)
        doc = W2._estado(p, A) or {}
        t.igual("E-16 el flujo BLOCKED", "BLOCKED", doc.get("status"))
        t.verdadero("E-16 con el codigo del estado", "SOURCE_INTEGRITY_ALERT" in W2._codigos(doc))
        b = [x for x in doc.get("blockedOn") or [] if x["code"] == "SOURCE_INTEGRITY_ALERT"]
        t.igual("E-16 HARD_BLOCKER en PLANNING", [("HARD_BLOCKER", "PLANNING", "plan.knowledgeSources")],
                [(x["classification"], x["stage"], x["inputId"]) for x in b])
    finally:
        _borrar(p)
    p = W2._proyecto()
    try:
        W2._listo(p)
        _escribir_fuentes(p, ES0901="VERSION_REGRESSION")
        codigo, salida, error = W2._cli(p, "refute", A, "--compile")
        t.igual("E-16 refute --compile sale 2", 2, codigo)
        t.contiene("E-16 dice el codigo", "VERSION_REGRESSION", salida + error)
        t.verdadero("E-16 no escribio run.json",
                    not (p / ".claude" / "refutaciones" / A / "run.json").exists())
    finally:
        _borrar(p)


def test_e17_una_fuente_que_no_se_exige_no_bloquea(t):
    """E-17 — una alerta en ES0903 o PC0901 no frena el plan ni la refutacion; una en ES0901 no
    bloquea el conocimiento del reporte de seguridad, que mira solo ES0902."""
    for estandar in ("ES0903", "PC0901"):
        plan = _armar([M20._unidad("u1")], capacidades={}, fuentes=_fuentes(
            **{"ES0901": "CURRENT", "ES0902": "CURRENT", estandar: "SOURCE_INTEGRITY_ALERT"}))
        t.verdadero("E-17 alerta en %s: el plan no queda BLOCKED" % estandar,
                    plan.get("status") not in ("BLOCKED", None))
        t.verdadero("E-17 %s no esta entre las que exige" % estandar,
                    estandar not in [f.get("standard") for f in plan.get("knowledgeSources") or []])
    p = W2._proyecto()
    try:
        W2._listo(p)
        _escribir_fuentes(p, ES0901="CURRENT", ES0902="CURRENT", ES0903="SOURCE_INTEGRITY_ALERT")
        codigo, _, _ = W2._cli(p, "refute", A, "--compile")
        t.igual("E-17 refute --compile con alerta en ES0903 sale 0", 0, codigo)
    finally:
        _borrar(p)
    doc = M48._fuentes()
    doc["sources"]["ES0901"] = dict(doc["sources"]["ES0902"], state="SOURCE_INTEGRITY_ALERT",
                                    blocking=True)
    r = M48._resumir(M48.prod.desde_frescura(doc, M48.TAREA, M48.ALCANCE) + M48._reglas())
    t.igual("E-17 una alerta en ES0901 no bloquea el conocimiento del reporte", False,
            r["knowledge"].get("blocking"))


def test_e18_plan_y_refute_bloquean_por_lo_mismo(t):
    """E-18 — una sola lista de estados que bloquean la operacion, y es la de la bienvenida."""
    F = _frescura()
    sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
    bienvenida = importlib.import_module("lib.bienvenida")
    t.igual("E-18 BLOQUEAN_OPERACION es FUENTE_BLOQUEA", sorted(bienvenida.FUENTE_BLOQUEA),
            sorted(getattr(F, "BLOQUEAN_OPERACION", ())))
    fuente_flujo = (BIN / "flujo" / "estado.py").read_text(encoding="utf-8")
    for codigo in INTEGRIDAD:
        t.no_contiene("E-18 flujo/estado.py no repite %s" % codigo, '"%s"' % codigo, fuente_flujo)
        try:
            b = W2._E()._bloqueo_propio(codigo)
        except Exception as e:                                 # noqa: BLE001
            b = {"inputId": repr(e)}
        t.igual("E-18 el flujo bloquea por %s" % codigo, "plan.knowledgeSources", b.get("inputId"))
    for estado in F.ESTADOS:
        salida = F.de_la_operacion(_fuentes(ES0901=estado), ["ES0901"]) \
            if hasattr(F, "de_la_operacion") else [{}]
        t.igual("E-18 %s bloquea solo si es de integridad" % estado, estado in INTEGRIDAD,
                salida[0].get("blocking"))
        t.igual("E-18 %s verificada solo si CURRENT" % estado, estado == "CURRENT",
                salida[0].get("verified"))


# -- E-19 a E-22: el Bloque 4 no muestra un cero que no midio -----------------------------

def _resumen_sin_uso():
    uso = M30.c_eventos.uso_sin_resolver("p-1", "m-1")
    return M30.c_agr.resumir([M30._ev(dedupKey="k-1", usage=uso)], task_id=M30.TAREA)


def _resumen_cero():
    return M30.c_agr.resumir([M30._ev(dedupKey="k-0", usage=M30._uso(0, 0, 0, 0))],
                             task_id=M30.TAREA)


def _contabilidad_texto(resumen):
    consola = _Consola()
    try:
        _cli_mod().mostrar_contabilidad(consola, resumen, "summary.json")
    except Exception as e:                                     # noqa: BLE001
        consola.linea(repr(e))
    return consola.texto()


def _linea_de(texto, prefijo):
    return next((l for l in texto.splitlines() if l.startswith(prefijo)), "")


def test_e19_tokens_sin_resolver_son_nd(t):
    """E-19 — con USAGE_UNRESOLVED los tokens salen N/D en contabilidad, execution-cost.md, el
    resumen de la refutacion y el reporte de seguridad."""
    resumen = _resumen_sin_uso()
    tokens = _linea_de(_contabilidad_texto(resumen), "Tokens")
    t.contiene("E-19 contabilidad: input N/D", "input N/D", tokens)
    t.contiene("E-19 contabilidad: output N/D", "output N/D", tokens)
    md = M30.c_reporte.generar(resumen)
    t.contiene("E-19 md: output N/D", "| Tokens de output | N/D |", md)
    t.no_contiene("E-19 md: nunca 0", "| Tokens de output | 0 |", md)
    try:
        P = importlib.import_module("contabilidad.presentacion")
        bloque4 = P.para_refutacion(resumen)
    except Exception as e:                                     # noqa: BLE001
        bloque4 = {"events": 1, "error": repr(e)}
    R = importlib.import_module("orquestacion.refutacion")
    doc = {"meta": {"taskKey": A}, "status": "INCOMPLETE", "warnings": [],
           "counts": dict((k, 0) for k in ("units", "cumple", "incumple", "sinVerificar",
                                           "checkResolved", "cacheHits", "semanticRuns",
                                           "pending", "blocked"))}
    texto = R.texto_de_resumen(doc, bloque4)
    t.contiene("E-19 refutacion: input N/D", "input N/D", texto)
    t.no_contiene("E-19 refutacion: nunca input 0", "input 0", texto)
    r = M48._resumir(M48._conocimiento() + M48._reglas(),
                     bloque4=json.dumps(resumen).encode("utf-8"))
    ejecucion = r.get("block4Execution") or {}
    t.igual("E-19 seguridad: los tokens no son 0", [None, None],
            [ejecucion.get("tokens", {}).get("inputTokens"),
             ejecucion.get("tokens", {}).get("outputTokens")])
    md_seg = M48.reporte.generar_md(r)
    t.contiene("E-19 seguridad: Tokens de output N/D", "| Tokens de output | N/D |", md_seg)
    t.contiene("E-19 seguridad html: N/D", 'data-field="block4Execution.tokens.outputTokens">N/D<',
               M48.reporte.generar_html(r))
    viejo = dict((k, v) for k, v in resumen.items() if k != "resolved")
    r = M48._resumir(M48._conocimiento() + M48._reglas(), bloque4=json.dumps(viejo).encode("utf-8"))
    t.contiene("E-19 summary.json sin resolved: md N/D", "| Tokens de output | N/D |",
               M48.reporte.generar_md(r))
    t.contiene("E-19 summary.json sin resolved: html N/D",
               'data-field="block4Execution.tokens.outputTokens">N/D<', M48.reporte.generar_html(r))


def test_e20_un_cero_medido_es_cero(t):
    """E-20 — un cero medido sale 0."""
    resumen = _resumen_cero()
    tokens = _linea_de(_contabilidad_texto(resumen), "Tokens")
    t.contiene("E-20 contabilidad: output 0", "output 0", tokens)
    t.contiene("E-20 md: output 0", "| Tokens de output | 0 |", M30.c_reporte.generar(resumen))
    P = importlib.import_module("contabilidad.presentacion")
    t.igual("E-20 refutacion: output 0", 0, P.para_refutacion(resumen).get("outputTokens"))


def test_e21_no_hay_segundo_ledger(t):
    """E-21 — summary.json conserva su 0 con su unresolved; presentacion no escribe nada."""
    resumen = _resumen_sin_uso()
    t.igual("E-21 summary.json sigue con 0", 0, resumen["tokens"]["outputTokens"])
    t.verdadero("E-21 y con su unresolved", "USAGE_UNRESOLVED" in resumen["unresolved"])
    fuente = (BIN / "contabilidad" / "presentacion.py")
    texto = fuente.read_text(encoding="utf-8") if fuente.exists() else "open("
    for prohibido in ("open(", ".write(", "libro", "ndjson"):
        t.no_contiene("E-21 presentacion no toca %s" % prohibido, prohibido, texto)


def test_e22_la_barra_no_confunde_sin_resolver_con_cero(t):
    """E-22 — la Context Bar no muestra Budget % sobre un costo sin resolver, ni un tiempo con
    TIME_ATTRIBUTION_UNRESOLVED; resueltos, si."""
    b4 = M53._b4()
    tiempo = b4["tiempo"].como_texto(65000)
    estado = {"model": "m-65", "context": {}, "tokens": {},
              "budget": {"amount": 1.0, "fraction": 0.5, "field": "actual", "currency": "USD",
                         "level": "NORMAL"},
              "time": {"wallMs": 65000}, "unresolved": []}
    resuelto = M53.SL.dibujar(estado, b4)
    t.contiene("E-22 resuelto: Budget", "Budget 50%", resuelto)
    t.contiene("E-22 resuelto: tiempo", tiempo, resuelto)
    linea = M53.SL.dibujar(dict(estado, unresolved=["COST_UNRESOLVED"]), b4)
    t.no_contiene("E-22 COST_UNRESOLVED: sin Budget", "Budget", linea)
    t.no_contiene("E-22 COST_UNRESOLVED: sin USD", "USD", linea)
    linea = M53.SL.dibujar(dict(estado, time={"wallMs": 65000, "wallMsMissing": 2}), b4)
    t.no_contiene("E-22 tiempo con faltantes: no aparece", tiempo, linea)
    linea = M53.SL.dibujar(dict(estado, unresolved=["TIME_ATTRIBUTION_UNRESOLVED"]), b4)
    t.no_contiene("E-22 tiempo sin resolver, sin conteo: no aparece", tiempo, linea)
    tiempo_mod = importlib.import_module("contabilidad.tiempo")
    barra = importlib.import_module("contabilidad.barra")
    completo = [M30._ev(dedupKey="t-1", sessionId="s-65", time=tiempo_mod.medir(60000, None, None))]
    con_faltante = completo + [M30._ev(dedupKey="t-2", sessionId="s-65",
                                       time=tiempo_mod.medir(None, 1000, None))]
    t.contiene("E-22 barra.de, pared completa sin modelo: la pared aparece", "1m 00s",
               M53.SL.dibujar(barra.de(completo, "s-65"), b4))
    t.no_contiene("E-22 barra.de, pared con faltantes: no aparece", "1m 00s",
                  M53.SL.dibujar(barra.de(con_faltante, "s-65"), b4))
    linea = M53.SL.dibujar(dict(estado, unresolved=["USAGE_UNRESOLVED"],
                                tokens={"inputTokens": 0, "outputTokens": 0}), b4)
    t.no_contiene("E-22 tokens sin resolver: no aparecen", "Tok", linea)


# -- E-23 y E-24: los estados de integracion ------------------------------------------------

def test_e23_cinco_estados_exactos(t):
    """E-23 — los cinco estados de integracion siguen siendo esos cinco."""
    base = importlib.import_module("integraciones.base")
    t.igual("E-23 los cinco", ESTADOS_DE_INTEGRACION, tuple(base.ESTADOS))


def test_e24_no_hay_not_required(t):
    """E-24 — NOT_REQUIRED no es un estado de integracion ni una disponibilidad."""
    base = importlib.import_module("integraciones.base")
    t.verdadero("E-24 no es un estado", "NOT_REQUIRED" not in base.ESTADOS)
    disponibilidades = tuple(getattr(_registro(), "DISPONIBILIDADES", ()))
    t.igual("E-24 las tres disponibilidades",
            ("SUPPORTED_AVAILABLE", "SUPPORTED_UNAVAILABLE", "NOT_SUPPORTED"), disponibilidades)
    for archivo in sorted((BIN / "integraciones").glob("*.py")) + [BIN / "orquestacion" / "capacidades.py"]:
        t.no_contiene("E-24 %s no lo nombra" % archivo.name, "NOT_REQUIRED",
                      archivo.read_text(encoding="utf-8"))


# -- E-35 a E-41: lo que pidio la implementacion ---------------------------------------------

def test_e35_el_flujo_dice_que_la_integracion_esta_caida(t):
    """E-35 — un plan BLOCKED por una capacidad no disponible da CAPABILITY_UNAVAILABLE en el
    flujo, nunca CAPABILITY_GAP; --resume revalida solo esa integracion; habilitada, el plan
    quedo viejo."""
    p = W2._proyecto()
    try:
        _escribir_registro(p, _todas_disabled(), _integraciones(jira="AVAILABLE",
                                                                gitlab="CONNECTION_FAILED"))
        W2._contexto(p, A)
        W2._plan(p, A, _propuesta_con(["gitlab.project.read"]))
        doc = W2._estado(p, A) or {}
        t.igual("E-35 el plan BLOCKED", "BLOCKED", _plan_json(p).get("status"))
        t.verdadero("E-35 CAPABILITY_UNAVAILABLE", "CAPABILITY_UNAVAILABLE" in W2._codigos(doc))
        t.verdadero("E-35 nunca CAPABILITY_GAP", "CAPABILITY_GAP" not in W2._codigos(doc))
        b = [x for x in doc.get("blockedOn") or [] if x["code"] == "CAPABILITY_UNAVAILABLE"]
        t.igual("E-35 HARD_BLOCKER en PLANNING", [("HARD_BLOCKER", "PLANNING")],
                [(x["classification"], x["stage"]) for x in b])
        decisiones = importlib.import_module("estado_de_tarea.decisiones")
        try:
            nombres = decisiones.integraciones_a_revalidar(doc, _plan_json(p))
        except TypeError as e:
            nombres = [repr(e)]
        t.igual("E-35 --resume revalida solo gitlab", ["gitlab"], nombres)
        habilitadas = dict(_todas_disabled(), **{"gitlab.project.read": "ENABLED"})
        _escribir_registro(p, habilitadas, _integraciones(jira="AVAILABLE", gitlab="AVAILABLE"))
        ahora = _derivar(p)
        t.verdadero("E-35 habilitada: ya no CAPABILITY_UNAVAILABLE",
                    "CAPABILITY_UNAVAILABLE" not in W2._codigos(ahora))
        t.verdadero("E-35 y el plan quedo viejo", "PLAN_STALE" in ahora.get("stale", []))
        t.verdadero("E-35 hay que regenerarlo", "PLAN_NOT_READY" in W2._codigos(ahora))
    finally:
        _borrar(p)


def test_e36_sin_resolver_bloqueante_o_resuelto_que_vuelve(t):
    """E-36 — UNRESOLVED con blocking, y RESOLVED que pasa a UNRESOLVED: REVIEW_INCOMPLETE."""
    h = M48._hallazgo("SEC-B", "HIGH", bloquea=True)
    r = _seguridad(M48._hallazgo_ev(h), M48._hallazgo_ev(h, "UPDATED", "UNRESOLVED"))
    t.igual("E-36 blocking UNRESOLVED: REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE", r["systemSecurityState"])
    c = M48._hallazgo("SEC-C", "CRITICAL")
    r = _seguridad(M48._hallazgo_ev(c), M48._hallazgo_ev(c, "RESOLVED"),
                   M48._hallazgo_ev(c, "UPDATED", "UNRESOLVED"))
    t.igual("E-36 resuelto que vuelve sin resolver: UNRESOLVED", "UNRESOLVED",
            r["findings"]["items"][0]["state"])
    t.igual("E-36 y REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE", r["systemSecurityState"])


def test_e37_severidad_desconocida_y_resuelto(t):
    """E-37 — un hallazgo vigente de severidad desconocida: REVIEW_INCOMPLETE; RESOLVED no bloquea;
    un HIGH abierto sin blocking sigue sin bloquear."""
    r = _seguridad(M48._hallazgo_ev(M48._hallazgo("SEC-X", "UNRESOLVED")))
    t.igual("E-37 severidad desconocida: REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE", r["systemSecurityState"])
    t.igual("E-37 con su bloqueo", [("OPEN", "REVIEW_INCOMPLETE")], _bloqueos_de_hallazgo(r))
    c = M48._hallazgo("SEC-C", "CRITICAL")
    r = _seguridad(M48._hallazgo_ev(c), M48._hallazgo_ev(c, "RESOLVED"))
    t.igual("E-37 resuelto: sin bloqueo de finding", [], _bloqueos_de_hallazgo(r))
    t.igual("E-37 resuelto: READY", "READY_FOR_SECURITY_REVIEW", r["systemSecurityState"])
    r = _seguridad(M48._hallazgo_ev(M48._hallazgo("SEC-H", "HIGH")))
    t.igual("E-37 HIGH abierto sin blocking: sin bloqueo", [], _bloqueos_de_hallazgo(r))


def test_e38_la_alerta_que_llega_despues_bloquea(t):
    """E-38 — una alerta de integridad que aparece despues de planificar bloquea el flujo;
    resuelta, el plan que se armo con la alerta queda viejo."""
    p = W2._proyecto()
    try:
        W2._listo(p)
        _escribir_fuentes(p, ES0901="SOURCE_CHANGED_SAME_VERSION")
        doc = _derivar(p)
        t.verdadero("E-38 despues de planificar: bloquea", "SOURCE_CHANGED_SAME_VERSION" in W2._codigos(doc))
        t.igual("E-38 BLOCKED", "BLOCKED", doc.get("status"))
    finally:
        _borrar(p)
    p = W2._proyecto()
    try:
        _escribir_fuentes(p, ES0901="SOURCE_INTEGRITY_ALERT")
        W2._contexto(p, A)
        W2._plan(p, A)
        _escribir_fuentes(p, ES0901="CURRENT")
        doc = _derivar(p)
        t.verdadero("E-38 resuelta: sin el codigo", "SOURCE_INTEGRITY_ALERT" not in W2._codigos(doc))
        t.verdadero("E-38 el plan quedo viejo", "PLAN_STALE" in doc.get("stale", []))
        t.verdadero("E-38 hay que regenerarlo", "PLAN_NOT_READY" in W2._codigos(doc))
    finally:
        _borrar(p)


def test_e39_un_parcial_no_es_el_total(t):
    """E-39 — un costo o un tiempo con algo sin resolver adentro sale N/D, no como el total."""
    base = _resumen_cero()
    parcial = dict(base, cost=dict(base["cost"], state="COST_UNRESOLVED", actual=1.25,
                                   apiEquivalentEstimated=2.5, currency="USD"),
                   time=dict(base["time"], state="TIME_ATTRIBUTION_UNRESOLVED", wallMs=65000,
                             wallMsMissing=1))
    texto = _contabilidad_texto(parcial)
    t.contiene("E-39 contabilidad: costo real N/D", "N/D", _linea_de(texto, "Costo real"))
    t.no_contiene("E-39 contabilidad: no el piso", "1.25", _linea_de(texto, "Costo real"))
    t.no_contiene("E-39 contabilidad: ni el equivalente parcial", "2.5", _linea_de(texto, "Equivalente"))
    t.contiene("E-39 contabilidad: tiempo N/D", "pared N/D", _linea_de(texto, "Tiempo"))
    md = M30.c_reporte.generar(parcial)
    t.contiene("E-39 md: costo real N/D", "| Costo real | N/D |", md)
    t.contiene("E-39 md: tiempo de pared N/D", "| Tiempo de pared | N/D |", md)
    viejo = dict((k, v) for k, v in parcial.items() if k != "resolved")
    r = M48._resumir(M48._conocimiento() + M48._reglas(), bloque4=json.dumps(viejo).encode("utf-8"))
    md_seg = M48.reporte.generar_md(r)
    t.contiene("E-39 seguridad, summary viejo: costo real N/D", "| Costo real | N/D |", md_seg)
    t.no_contiene("E-39 seguridad, summary viejo: no el piso", "1.25", md_seg)
    barra = importlib.import_module("contabilidad.barra")
    estado = {"model": "m", "context": {"fraction": None, "level": "NORMAL"},
              "budget": {"amount": 1.25, "fraction": 0.25, "field": "actual", "currency": "USD",
                         "level": "NORMAL"},
              "time": {"wallMs": 65000}, "unresolved": ["COST_UNRESOLVED", "TIME_ATTRIBUTION_UNRESOLVED"]}
    linea = barra.compacto(estado, ancho=200)
    t.no_contiene("E-39 --barra: no el piso", "1.25", linea)
    t.no_contiene("E-39 --barra: ni el porcentaje del piso", "25%", linea)
    t.contiene("E-39 --barra: N/D", "N/D", linea)


def test_e40_no_descubierta_o_sin_registro(t):
    """E-40 — AVAILABLE pero no descubierta: CAPABILITY_NOT_DISCOVERED; sin registro:
    CAPABILITY_REGISTRY_ABSENT. Nunca NOT_SUPPORTED."""
    d = _disp("jira.attachment.read", dict(_todas_disabled(), **{"jira.issue.read": "ENABLED"}),
              _integraciones(jira="AVAILABLE"))
    t.igual("E-40 no descubierta", ["SUPPORTED_UNAVAILABLE", "CAPABILITY_NOT_DISCOVERED", "AVAILABLE"],
            [d.get("availability"), d.get("reasonCode"), d.get("integrationState")])
    d = _disp("gitlab.branch.read", None, None)
    t.igual("E-40 sin registro", ["SUPPORTED_UNAVAILABLE", "CAPABILITY_REGISTRY_ABSENT", None],
            [d.get("availability"), d.get("reasonCode"), d.get("integrationState")])
    plan = _armar([M20._unidad("u1", capacidades=["jira.issue.read"])], capacidades={},
                  integraciones=None)
    t.igual("E-40 un plan sin registro no lo deriva", [], plan.get("capabilityGaps"))


def test_e41_una_sola_autoridad_de_lo_soportado(t):
    """E-41 — registro.soporte() sale de los CAPACIDADES de los adapters; dev-harness usa esas
    clases y el manifiesto dice lo mismo."""
    from integraciones.gitlab import IntegracionGitLab
    from integraciones.jira import IntegracionJira
    esperado = dict((c, k.nombre) for k in (IntegracionJira, IntegracionGitLab) for c in k.CAPACIDADES)
    t.igual("E-41 soporte() es la de los adapters", esperado, _registro().soporte())
    t.igual("E-41 dev-harness usa las mismas clases", tuple(_registro().clases()),
            tuple(_cli_mod().CLASES))
    manifiesto = json.loads((RAIZ / "harnesses" / "desarrollo" / "manifest.json").read_text(
        encoding="utf-8"))
    t.igual("E-41 el manifiesto dice lo mismo", sorted(esperado),
            sorted(manifiesto.get("capacidadesSoportadas") or []))


def test_e42_un_plan_viejo_con_un_hueco_soportado_quedo_viejo(t):
    """E-42 — un plan de antes de la Wave 5 (sin capabilityStatus) con un hueco de una capacidad
    soportada: el flujo no dice CAPABILITY_GAP; el plan quedo viejo y hay que regenerarlo."""
    p = W2._proyecto()
    try:
        W2._listo(p)
        ruta = p / ".claude" / "planes" / (A + ".json")
        plan = json.loads(ruta.read_text(encoding="utf-8"))
        plan.pop("capabilityStatus", None)
        plan.pop("knowledgeSources", None)
        plan["capabilityGaps"] = [{"capability": "jira.issue.read", "workUnits": [W2.UNIDAD],
                                   "derivedTo": "dev-tool-builder", "toolClass": "TEMPORARY"}]
        plan["status"] = "CAPABILITY_RESOLUTION"
        ruta.write_text(json.dumps(plan), encoding="utf-8")
        doc = _derivar(p)
        t.verdadero("E-42 nunca CAPABILITY_GAP", "CAPABILITY_GAP" not in W2._codigos(doc))
        t.verdadero("E-42 el plan quedo viejo", "PLAN_STALE" in doc.get("stale", []))
        t.verdadero("E-42 hay que regenerarlo", "PLAN_NOT_READY" in W2._codigos(doc))
        plan["capabilityGaps"][0]["capability"] = "no.existe"
        ruta.write_text(json.dumps(plan), encoding="utf-8")
        t.verdadero("E-42 un hueco de verdad sigue siendo CAPABILITY_GAP",
                    "CAPABILITY_GAP" in W2._codigos(_derivar(p)))
    finally:
        _borrar(p)


def _con_tiempo(wall, model, tool):
    t_ = importlib.import_module("contabilidad.tiempo")
    return M30.c_agr.resumir([M30._ev(dedupKey="t-43", usage=M30._uso(5, 7, 0, 0),
                                      time=t_.medir(wall, model, tool))], task_id=M30.TAREA)


def _tabla_md(md, nombre):
    return next((l for l in md.splitlines() if l.startswith("| %s |" % nombre)), "")


def test_e43_toda_metrica_sin_resolver_es_nd(t):
    """E-43 — una metrica del Bloque 4 sin resolver es N/D tambien cuando su valor es nulo, nunca
    `sin resolver` ni 0; resuelta, su valor, 0 incluido. Cada una por su cuenta: pared resuelta y
    modelo sin resolver da la pared visible y el modelo N/D."""
    tiempo = importlib.import_module("contabilidad.tiempo")
    for rotulo, modelo, esperado in (("modelo sin resolver", None, "N/D"),
                                     ("modelo resuelto en 0", 0, tiempo.como_texto(0)),
                                     ("modelo resuelto", 5000, tiempo.como_texto(5000))):
        resumen = _con_tiempo(60000, modelo, 0)
        texto = _linea_de(_contabilidad_texto(resumen), "Tiempo")
        t.contiene("E-43 %s: la pared visible" % rotulo, "pared 1m 00s", texto)
        t.contiene("E-43 %s: el modelo" % rotulo, "modelo %s " % esperado, texto)
        md = M30.c_reporte.generar(resumen)
        t.igual("E-43 %s: md pared" % rotulo, "| Tiempo de pared | 1m 00s |", _tabla_md(md, "Tiempo de pared"))
        t.igual("E-43 %s: md modelo" % rotulo, "| Tiempo de modelo | %s |" % esperado,
                _tabla_md(md, "Tiempo de modelo"))
        P = importlib.import_module("contabilidad.presentacion")
        R_ = importlib.import_module("orquestacion.refutacion")
        doc = {"meta": {"taskKey": A}, "status": "INCOMPLETE", "warnings": [],
               "counts": dict((k, 0) for k in ("units", "cumple", "incumple", "sinVerificar",
                                               "checkResolved", "cacheHits", "semanticRuns",
                                               "pending", "blocked"))}
        refutacion = R_.texto_de_resumen(doc, P.para_refutacion(resumen))
        t.contiene("E-43 %s: refutacion pared" % rotulo, "pared 60000 ms", refutacion)
        t.contiene("E-43 %s: refutacion modelo" % rotulo,
                   "modelo %s ms" % ("N/D" if modelo is None else modelo), refutacion)
    resumen = _resumen_sin_uso()
    texto = _contabilidad_texto(resumen)
    md = M30.c_reporte.generar(resumen)
    for prefijo in ("Tokens", "Ventana", "Tiempo", "Costo real", "Equivalente"):
        t.no_contiene("E-43 contabilidad %s: nunca `sin resolver`" % prefijo, "sin resolver",
                      _linea_de(texto, prefijo))
        t.contiene("E-43 contabilidad %s: N/D" % prefijo, "N/D", _linea_de(texto, prefijo))
    for nombre in ("Tokens de input", "Tokens de output", "Tiempo de pared", "Tiempo de modelo",
                   "Tiempo de tools", "Ventana al final", "Costo real", "Equivalente de API estimado"):
        fila = _tabla_md(md, nombre)
        t.no_contiene("E-43 md %s: nunca `sin resolver`" % nombre, "sin resolver", fila)
        t.no_contiene("E-43 md %s: nunca 0" % nombre, "| 0 |", fila)
        t.contiene("E-43 md %s: N/D" % nombre, "N/D", fila)
    barra = importlib.import_module("contabilidad.barra")
    estado = {"model": "m", "context": {"fraction": None, "level": "NORMAL"},
              "budget": {"amount": None, "fraction": None, "field": "actual", "currency": "USD",
                         "level": "NORMAL"},
              "time": {"wallMs": None}, "unresolved": ["COST_UNRESOLVED"]}
    linea = barra.compacto(estado, ancho=200)
    t.no_contiene("E-43 --barra: nunca `sin resolver`", "sin resolver", linea)
    t.no_contiene("E-43 --barra: nunca `?`", "?", linea)


def _con_presupuesto(resumen):
    """El resumen con la decision de presupuesto que el Bloque 4 calcula sobre su costo."""
    presupuesto = importlib.import_module("contabilidad.presupuesto")
    politica = dict(M30.POLITICA, billingMode="API")
    decision = presupuesto.evaluar(presupuesto.consumido(resumen, politica)[0], 0, politica)
    return dict(resumen, budget=decision)


def test_e39b_el_presupuesto_no_muestra_un_piso(t):
    """E-39 — en la seccion de presupuesto, el consumido y el proyectado de un costo parcial salen
    N/D, en contabilidad y en execution-cost.md, como la linea de Costo real."""
    base = _resumen_cero()
    parcial = _con_presupuesto(dict(base, cost=dict(base["cost"], state="COST_UNRESOLVED", actual=1.25,
                                                    apiEquivalentEstimated=2.5, currency="USD")))
    texto = _contabilidad_texto(parcial)
    for prefijo in ("  Consumido:", "  Proyectado:"):
        linea = _linea_de(texto, prefijo)
        t.contiene("E-39 presupuesto %s N/D" % prefijo.strip(), "N/D", linea)
        t.no_contiene("E-39 presupuesto %s: no el piso" % prefijo.strip(), "1.25", linea)
    md = M30.c_reporte.generar(parcial)
    t.igual("E-39 md: Consumido N/D", "| Consumido | N/D |", _tabla_md(md, "Consumido"))


def test_e43b_el_presupuesto_tampoco_dice_sin_resolver(t):
    """E-43 — con todo sin resolver, la seccion de presupuesto dice N/D, nunca `sin resolver`."""
    resumen = _con_presupuesto(_resumen_sin_uso())
    texto = _contabilidad_texto(resumen)
    for prefijo in ("  Consumido:", "  Proyectado:"):
        linea = _linea_de(texto, prefijo)
        t.no_contiene("E-43 presupuesto %s: nunca `sin resolver`" % prefijo.strip(), "sin resolver", linea)
        t.contiene("E-43 presupuesto %s: N/D" % prefijo.strip(), "N/D", linea)
    md = M30.c_reporte.generar(resumen)
    t.igual("E-43 md: Consumido N/D", "| Consumido | N/D |", _tabla_md(md, "Consumido"))
