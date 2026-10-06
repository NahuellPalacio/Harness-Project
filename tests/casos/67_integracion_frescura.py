# La integracion de Flow Governance con 0.28.0: la frescura del conocimiento, con una sola
# autoridad.
#
# Escenarios I-01 a I-08 de docs/cambios/flow-governance/integracion-0.28.md, decision A del
# 05-10-2026: el refresco de 0.27 refresca, observa, registra y avisa; lo que frena `plan` o
# `refute --compile` lo decide la frescura de ESA operacion, sobre las fuentes que exige (Wave 5,
# fail-closed-hardening). KRF E-42 («una fuente cualquiera frena») queda
# SUPERSEDED_AT_INTEGRATION_BOUNDARY.
#
# Reusa los proyectos del flujo de 62_estado_del_flujo. Nada sale a la red.
import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


W2 = _cargar("caso_62_para_67", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")
A = W2.A
EXIGIDAS = ("ES0901", "ES0902")


def _escribir_fuentes(p, **estados):
    """harness.fuentes.json con esos estados. Las exigidas que no se nombran, CURRENT."""
    fuentes = dict((s, "CURRENT") for s in EXIGIDAS)
    fuentes.update(estados)
    ruta = p / ".claude" / "harness.fuentes.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"sources": dict((k, {"state": v}) for k, v in fuentes.items())}),
                    encoding="utf-8")


def _plan_de(p):
    ruta = p / ".claude" / "planes" / (A + ".json")
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _fuente(plan, estandar):
    return dict((f.get("standard"), f) for f in plan.get("knowledgeSources") or []).get(estandar, {})


def _hard_blocker(doc, codigo):
    return [(b["classification"], b["stage"], b["inputId"])
            for b in (doc or {}).get("blockedOn") or [] if b["code"] == codigo]


def _planificar(p, **estados):
    """contexto + fuentes + plan por la CLI. (codigo, salida, plan, estado del flujo)."""
    W2._contexto(p, A)
    _escribir_fuentes(p, **estados)
    codigo, salida, error = W2._plan(p, A)
    return codigo, salida + error, _plan_de(p), W2._estado(p, A)


def _compilar(p, **estados):
    """Un plan listo, despues las fuentes, despues refute --compile. (codigo, salida, run.json)."""
    W2._listo(p)
    _escribir_fuentes(p, **estados)
    codigo, salida, error = W2._cli(p, "refute", A, "--compile")
    run = p / ".claude" / "refutaciones" / A / "run.json"
    return codigo, salida + error, (json.loads(run.read_text(encoding="utf-8"))
                                    if run.exists() else None)


def test_i01_seguida_no_exigida_en_alerta_no_frena_el_plan(t):
    """I-01 (A) — ES0903 seguida, no exigida, en SOURCE_INTEGRITY_ALERT: el plan no queda BLOCKED
    por ella, y el flujo no la lleva como bloqueo."""
    p = W2._proyecto()
    try:
        codigo, salida, plan, flujo = _planificar(p, ES0903="SOURCE_INTEGRITY_ALERT")
        t.igual("I-01 plan sale 0", 0, codigo)
        t.verdadero("I-01 el plan quedo escrito y no BLOCKED",
                    plan.get("status") not in (None, "BLOCKED"))
        t.verdadero("I-01 ES0903 no esta entre las que exige",
                    "ES0903" not in [f.get("standard") for f in plan.get("knowledgeSources") or []])
        t.igual("I-01 el flujo no la lleva", [], _hard_blocker(flujo, "SOURCE_INTEGRITY_ALERT"))
        t.contiene("I-01 la alerta se avisa igual", "fuentes seguidas en alerta (ES0903)", salida)
        t.no_contiene("I-01 sin la compuerta global de 0.27",
                      "conocimiento normativo no se puede usar", salida)
    finally:
        W2._borrar(p)


def test_i02_exigida_en_alerta_plan_blocked_y_flujo_hard_blocker(t):
    """I-02 (B) — ES0901 exigida en SOURCE_INTEGRITY_ALERT: el plan se escribe BLOCKED y el flujo
    queda HARD_BLOCKER en PLANNING con ese codigo."""
    p = W2._proyecto()
    try:
        codigo, _, plan, flujo = _planificar(p, ES0901="SOURCE_INTEGRITY_ALERT")
        t.igual("I-02 el plan existe y esta BLOCKED", "BLOCKED", plan.get("status"))
        t.igual("I-02 la fuente exigida bloquea", True, _fuente(plan, "ES0901").get("blocking"))
        t.igual("I-02 el flujo BLOCKED", "BLOCKED", (flujo or {}).get("status"))
        t.igual("I-02 HARD_BLOCKER en PLANNING, por plan.knowledgeSources",
                [("HARD_BLOCKER", "PLANNING", "plan.knowledgeSources")],
                _hard_blocker(flujo, "SOURCE_INTEGRITY_ALERT"))
    finally:
        W2._borrar(p)


def test_i03_seguida_no_exigida_cambio_misma_version_no_frena(t):
    """I-03 (C) — ES0903 en SOURCE_CHANGED_SAME_VERSION: ni el plan ni la refutacion se frenan."""
    p = W2._proyecto()
    try:
        codigo, _, plan, flujo = _planificar(p, ES0903="SOURCE_CHANGED_SAME_VERSION")
        t.verdadero("I-03 el plan no queda BLOCKED", plan.get("status") not in (None, "BLOCKED"))
        t.igual("I-03 el flujo no la lleva", [], _hard_blocker(flujo, "SOURCE_CHANGED_SAME_VERSION"))
    finally:
        W2._borrar(p)
    p = W2._proyecto()
    try:
        codigo, _, run = _compilar(p, ES0903="SOURCE_CHANGED_SAME_VERSION")
        t.igual("I-03 refute --compile sale 0", 0, codigo)
        t.verdadero("I-03 y escribio run.json", run is not None)
    finally:
        W2._borrar(p)


def test_i04_exigida_cambio_misma_version_frena(t):
    """I-04 (D) — ES0902 exigida en SOURCE_CHANGED_SAME_VERSION: el plan BLOCKED con el flujo en
    HARD_BLOCKER, y refute --compile sale con 2 sin escribir."""
    p = W2._proyecto()
    try:
        _, _, plan, flujo = _planificar(p, ES0902="SOURCE_CHANGED_SAME_VERSION")
        t.igual("I-04 el plan BLOCKED", "BLOCKED", plan.get("status"))
        t.igual("I-04 HARD_BLOCKER con ese codigo",
                [("HARD_BLOCKER", "PLANNING", "plan.knowledgeSources")],
                _hard_blocker(flujo, "SOURCE_CHANGED_SAME_VERSION"))
    finally:
        W2._borrar(p)
    p = W2._proyecto()
    try:
        codigo, salida, run = _compilar(p, ES0901="SOURCE_CHANGED_SAME_VERSION")
        t.igual("I-04 refute --compile sale 2", 2, codigo)
        t.contiene("I-04 dice el codigo", "SOURCE_CHANGED_SAME_VERSION", salida)
        t.igual("I-04 sin run.json", None, run)
    finally:
        W2._borrar(p)


def test_i05_exigida_sin_verificar_se_marca_y_no_frena(t):
    """I-05 (E) — ES0901 exigida en FRESHNESS_UNVERIFIED: no es CURRENT, se informa, y no frena ni
    el plan ni la refutacion."""
    p = W2._proyecto()
    try:
        codigo, salida, plan, flujo = _planificar(p, ES0901="FRESHNESS_UNVERIFIED")
        f = _fuente(plan, "ES0901")
        t.igual("I-05 no CURRENT, no verificada, no bloquea",
                ("FRESHNESS_UNVERIFIED", False, False),
                (f.get("state"), f.get("verified"), f.get("blocking")))
        t.verdadero("I-05 el plan no queda BLOCKED", plan.get("status") not in (None, "BLOCKED"))
        t.verdadero("I-05 el plan lo avisa", any("ES0901" in a for a in plan.get("warnings") or []))
        t.contiene("I-05 el refresco lo informa", "SIN RESOLVER", salida)
        t.igual("I-05 el flujo no bloquea por eso", [], _hard_blocker(flujo, "FRESHNESS_UNVERIFIED"))
    finally:
        W2._borrar(p)
    p = W2._proyecto()
    try:
        codigo, _, run = _compilar(p, ES0901="FRESHNESS_UNVERIFIED")
        t.igual("I-05 refute --compile sale 0", 0, codigo)
        t.verdadero("I-05 la corrida lo marca",
                    "REFUTATION_SOURCE_UNVERIFIED:ES0901:FRESHNESS_UNVERIFIED"
                    in ((run or {}).get("warnings") or []))
    finally:
        W2._borrar(p)


def _con_canal_local(p, vencida, estandar="ES0902"):
    """`fuentes --archivo` sobre una carpeta con ES0902 6.2; despues `estandar` se pisa a mano con
    SOURCE_INTEGRITY_ALERT, y la agenda queda vencida o al dia. Lo que observa el canal no es una
    alerta: solo un refresco que corre ANTES de decidir la saca."""
    ficha = p.parent / (p.name + "-ficha")
    ficha.mkdir()
    (ficha / "ES0902 - Estandar de Seguridad V6.2.pdf").write_text("original ES0902 6.2",
                                                                   encoding="utf-8")
    W2._cli(p, "fuentes", "--archivo", str(ficha))
    ruta = p / ".claude" / "harness.fuentes.json"
    doc = json.loads(ruta.read_text(encoding="utf-8"))
    doc["sources"][estandar]["state"] = "SOURCE_INTEGRITY_ALERT"
    ruta.write_text(json.dumps(doc), encoding="utf-8")
    agenda = p / ".claude" / "runtime" / "knowledge-refresh.json"
    datos = json.loads(agenda.read_text(encoding="utf-8"))
    if vencida:
        datos.update(lastSuccessfulCheckAt="2026-09-01T00:00:00",
                     nextCheckDueAt="2026-09-02T00:00:00")
    else:
        datos.update(lastSuccessfulCheckAt="2099-01-01T00:00:00",
                     nextCheckDueAt="2099-01-02T00:00:00")
    agenda.write_text(json.dumps(datos), encoding="utf-8")
    return ficha


def test_i06_el_refresco_corre_antes_de_decidir(t):
    """I-06 (F) — con la agenda vencida, el refresco vuelve a mirar el canal ANTES de que el plan
    decida, y el plan decide con lo observado. Control: al dia, no hay refresco y decide con la
    alerta que estaba."""
    p = W2._proyecto()
    ficha = None
    try:
        ficha = _con_canal_local(p, vencida=True)
        W2._contexto(p, A)
        W2._plan(p, A)
        agenda = json.loads((p / ".claude" / "runtime" / "knowledge-refresh.json")
                            .read_text(encoding="utf-8"))
        t.igual("I-06 el plan refresco con PRE_NORMATIVE_OPERATION_IF_STALE",
                "PRE_NORMATIVE_OPERATION_IF_STALE", agenda.get("trigger"))
        plan = _plan_de(p)
        t.verdadero("I-06 el plan decidio con lo observado: no BLOCKED",
                    plan.get("status") not in (None, "BLOCKED"))
        t.verdadero("I-06 ES0902 ya no esta en alerta",
                    _fuente(plan, "ES0902").get("state") != "SOURCE_INTEGRITY_ALERT")
    finally:
        W2._borrar(p, *([ficha] if ficha else []))
    p = W2._proyecto()
    ficha = None
    try:
        ficha = _con_canal_local(p, vencida=False)
        W2._contexto(p, A)
        W2._plan(p, A)
        t.igual("I-06 control: al dia no refresca, y la alerta frena", "BLOCKED",
                _plan_de(p).get("status"))
    finally:
        W2._borrar(p, *([ficha] if ficha else []))


def test_i08_refute_refresca_antes_de_decidir(t):
    """I-08 (F, para la refutacion) — con la agenda vencida, `refute --compile` vuelve a mirar el
    canal ANTES de que su compuerta decida: la alerta escrita a mano en ES0901, que el canal no
    confirma, no frena la compilacion. Control: al dia no hay refresco, y la misma alerta frena."""
    for vencida, esperado in ((True, 0), (False, 2)):
        p = W2._proyecto()
        ficha = None
        try:
            W2._listo(p)
            ficha = _con_canal_local(p, vencida=vencida, estandar="ES0901")
            codigo, salida, error = W2._cli(p, "refute", A, "--compile")
            run = p / ".claude" / "refutaciones" / A / "run.json"
            agenda = json.loads((p / ".claude" / "runtime" / "knowledge-refresh.json")
                                .read_text(encoding="utf-8"))
            rotulo = "vencida" if vencida else "control al dia"
            t.igual("I-08 %s: refute --compile sale %d" % (rotulo, esperado), esperado, codigo)
            t.igual("I-08 %s: run.json %s" % (rotulo, "si" if vencida else "no"), vencida,
                    run.exists())
            t.igual("I-08 %s: disparador" % rotulo,
                    "PRE_NORMATIVE_OPERATION_IF_STALE" if vencida else "EXPLICIT_SOURCES_COMMAND",
                    agenda.get("trigger"))
            if not vencida:
                t.contiene("I-08 control: frena por la alerta que estaba", "SOURCE_INTEGRITY_ALERT",
                           salida + error)
        finally:
            W2._borrar(p, *([ficha] if ficha else []))


def test_i07_refute_usa_el_alcance_de_la_unidad(t):
    """I-07 (G) — refute --compile decide por el estandar que compila, no por la lista de fuentes
    seguidas: la misma alerta frena en ES0901 y no en ES0903 ni en PC0901."""
    for estandar, esperado in (("ES0901", 2), ("ES0903", 0), ("PC0901", 0)):
        p = W2._proyecto()
        try:
            codigo, salida, run = _compilar(p, **{estandar: "SOURCE_INTEGRITY_ALERT"})
            t.igual("I-07 alerta en %s: refute --compile sale %d" % (estandar, esperado),
                    esperado, codigo)
            t.igual("I-07 alerta en %s: run.json %s" % (estandar, "no" if esperado else "si"),
                    esperado == 0, run is not None)
        finally:
            W2._borrar(p)
