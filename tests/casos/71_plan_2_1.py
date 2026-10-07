# Los escenarios de docs/cambios/integracion-flow-governance-0-31/spec.md: el contrato
# orchestration-plan/2.1 y las resoluciones del merge de Flow Governance con 0.30.0. Cada test
# nombra su E-nn. E-20 es la suite entera y no tiene test propio.
import importlib.util
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
SCHEMA = RAIZ / "comun" / "schemas" / "orchestration-plan.schema.json"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from orquestacion import plan as P                        # noqa: E402


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M20 = _cargar("caso_20_para_71", RAIZ / "tests" / "casos" / "20_orquestacion.py")
W2 = _cargar("caso_62_para_71", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")
ARMADOR = P._armador()

V21, V20, V10 = "orchestration-plan/2.1", "orchestration-plan/2.0", "orchestration-plan/1.0"
ESTADOS_PLAN = ["BLOCKED", "CAPABILITY_RESOLUTION", "WAITING_FOR_HUMAN_APPROVAL",
                "READY_FOR_EXECUTION"]
ESTADOS_UNIDAD = ["PENDING", "BLOCKED", "WAITING_FOR_HUMAN_APPROVAL"]
RETIRADOS = ["RECEIVED", "ANALYZING", "PLANNING", "WAITING_FOR_TOOL", "READY_FOR_DELEGATION",
             "DELEGATING", "REPLANNING", "FAILED"]
CARA = ["ambiguity", "security_impact", "architectural_impact"]


def _esquema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _integraciones(jira="NOT_CONFIGURED", gitlab="NOT_CONFIGURED"):
    return {"jira": {"estado": jira}, "gitlab": {"estado": gitlab}}


def _armar(unidades, precondiciones=M20.PRECONDICIONES, integraciones=None, registro=None,
           config=None):
    dominios = sorted(set(u.get("domain", "backend") for u in unidades))
    return P.armar(M20._propuesta(unidades, domains=dominios), M20.CONTEXTO,
                   M20.REGISTRO if registro is None else registro, config or {}, "0.31.0",
                   "docs/x.json", precondiciones, integraciones=integraciones)


def _todas_disabled():
    """Lo soportado, deshabilitado: con la integracion caida, SUPPORTED_UNAVAILABLE (como en 65)."""
    from orquestacion import capacidades
    return dict((c, "DISABLED") for c in capacidades.registro_de_capacidades.soporte())


def _sin_ruteo():
    return M20._unidad("u-sin-ruteo", assignedAgent="dev-no-existe")


def _hueco():
    return M20._unidad("u-hueco", capacidades=["no.existe"])


def _caida():
    return M20._unidad("u-caida", capacidades=["jira.issue.read"])


def _lista():
    return M20._unidad("u-lista", capacidades=["repository.read"])


def _cara():
    return M20._unidad("u-cara", senales=CARA)


def _por_id(plan):
    return dict((u["id"], u) for u in plan["workUnits"])


def _combinaciones():
    """(rotulo, plan) sobre unidades, capacidades, aprobaciones y precondiciones."""
    tipos = {"lista": _lista, "hueco": _hueco, "caida": _caida, "cara": _cara,
             "sin-ruteo": _sin_ruteo}
    conjuntos = (("lista",), ("hueco",), ("caida",), ("cara",), ("sin-ruteo",),
                 ("lista", "hueco"), ("lista", "cara"), ("hueco", "cara"), ("caida", "cara"),
                 ("sin-ruteo", "hueco"), ("sin-ruteo", "caida", "cara"), ("lista", "caida"))
    previas = (("con precondiciones", M20.PRECONDICIONES), ("sin precondiciones", None))
    for conjunto in conjuntos:
        for rotulo_p, pre in previas:
            unidades = [tipos[n]() for n in conjunto]
            plan = _armar(unidades, precondiciones=pre,
                          integraciones=_integraciones(jira="AUTHENTICATION_FAILED"),
                          registro=_todas_disabled())
            yield "%s, %s" % ("+".join(conjunto), rotulo_p), plan


# -- E-01 a E-05: el contrato --------------------------------------------------------------

def test_e01_el_plan_es_2_1(t):
    """E-01 — $id y meta.schema_version dicen 2.1 y solo 2.1; plan --propuesta escribe 2.1."""
    esquema = _esquema()
    t.igual("E-01 $id", V21, esquema.get("$id"))
    t.igual("E-01 el enum de meta.schema_version es solo 2.1", [V21],
            esquema["properties"]["meta"]["properties"]["schema_version"].get("enum"))
    ARMADOR.controlar_soporte(esquema)
    plan = _armar([_lista()])
    t.igual("E-01 el plan armado dice 2.1", V21, plan["meta"]["schema_version"])
    t.igual("E-01 y valida", [], ARMADOR.validar(plan, esquema))
    for otra in (V20, V10, "orchestration-plan/3.0", ""):
        viejo = json.loads(json.dumps(plan))
        viejo["meta"]["schema_version"] = otra
        t.verdadero("E-01 meta.schema_version no acepta `%s`" % otra,
                    any("schema_version" in e for e in ARMADOR.validar(viejo, esquema)))
    raiz = M20._proyecto_con_contexto(repositorio=True)
    try:
        propuesta = os.path.join(raiz, "prop.json")
        io.open(propuesta, "w", encoding="utf-8").write(json.dumps(M20._propuesta()))
        codigo, _, error = M20._correr_cli(["plan", M20.CLAVE, "--proyecto", raiz,
                                            "--propuesta", propuesta])
        t.igual("E-01 plan --propuesta sale 0", 0, codigo)
        escrito = json.loads(io.open(os.path.join(raiz, ".claude", "planes", M20.CLAVE + ".json"),
                                     encoding="utf-8").read())
        t.igual("E-01 plan --propuesta escribe 2.1", V21, escrito["meta"]["schema_version"])
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def test_e02_el_status_del_plan_son_cuatro(t):
    """E-02 — el status del plan es exactamente los cuatro, y ninguno de los retirados."""
    estados = _esquema()["properties"]["status"].get("enum") or []
    t.igual("E-02 exactamente los cuatro", sorted(ESTADOS_PLAN), sorted(estados))
    t.igual("E-02 sin repetidos", len(set(estados)), len(estados))
    t.igual("E-02 ESTADOS_DEL_PLAN dice lo mismo", sorted(ESTADOS_PLAN), sorted(P.ESTADOS_DEL_PLAN))
    for retirado in RETIRADOS:
        t.verdadero("E-02 %s no esta" % retirado, retirado not in estados)


def test_e03_el_status_de_la_unidad_son_tres(t):
    """E-03 — el status de una unidad es exactamente PENDING, BLOCKED y WAITING_FOR_HUMAN_APPROVAL."""
    estados = _esquema()["properties"]["workUnits"]["items"]["properties"]["status"].get("enum")
    t.igual("E-03 exactamente los tres", sorted(ESTADOS_UNIDAD), sorted(estados or []))
    t.verdadero("E-03 READY no esta", "READY" not in (estados or []))


def test_e04_blockers_es_opcional_y_tiene_forma(t):
    """E-04 — una unidad sin blockers valida; cada item exige inputId y code, sin claves de mas, y
    un code en minusculas no valida."""
    esquema = _esquema()
    plan = _armar([_lista()])
    t.verdadero("E-04 la unidad lista no trae blockers", "blockers" not in plan["workUnits"][0])
    t.igual("E-04 y valida", [], ARMADOR.validar(plan, esquema))
    malos = (("sin code", [{"inputId": "agents.routing"}]),
             ("sin inputId", [{"code": "AGENT_NOT_FOUND"}]),
             ("con una clave de mas", [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND",
                                        "detalle": "x"}]),
             ("con un code en minusculas", [{"inputId": "agents.routing", "code": "no_ruteable"}]))
    for rotulo, bloqueos in malos:
        roto = json.loads(json.dumps(plan))
        roto["workUnits"][0]["blockers"] = bloqueos
        t.verdadero("E-04 un blockers %s no valida" % rotulo,
                    bool(ARMADOR.validar(roto, esquema)))
    bueno = json.loads(json.dumps(plan))
    bueno["workUnits"][0]["blockers"] = [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND"}]
    t.igual("E-04 uno bien formado valida", [], ARMADOR.validar(bueno, esquema))


def test_e05_un_2_0_de_0_30_0_valida_como_2_1(t):
    """E-05 — un plan 2.0 escrito por 0.30.0, con la cadena de version cambiada, valida bajo 2.1."""
    esquema = _esquema()
    for rotulo, unidades in (("listo", [_lista()]), ("con hueco", [_hueco()]),
                             ("con aprobacion", [_cara()])):
        plan = _armar(unidades)
        # Lo que escribia 0.30.0: sin BLOCKED en el plan ni blockers en las unidades.
        for u in plan["workUnits"]:
            u.pop("blockers", None)
        if plan["status"] == "BLOCKED":
            plan["status"] = "CAPABILITY_RESOLUTION"
        plan["meta"]["schema_version"] = V21
        t.igual("E-05 %s: un 2.0 sin blockers valida bajo 2.1" % rotulo, [],
                ARMADOR.validar(plan, esquema))


# -- E-06 a E-09: lo que escribe plan --------------------------------------------------------

def test_e06_toda_unidad_blocked_dice_por_que(t):
    """E-06 — una unidad BLOCKED lleva blockers no vacio con su input y su codigo; una PENDING o
    WAITING_FOR_HUMAN_APPROVAL no los lleva."""
    plan = _armar([_sin_ruteo(), _hueco(), _caida(), _lista(), _cara()],
                  integraciones=_integraciones(jira="AUTHENTICATION_FAILED"),
                  registro=_todas_disabled())
    u = _por_id(plan)
    t.igual("E-06 agente no ruteable", [{"inputId": "agents.routing", "code": "AGENT_NOT_FOUND"}],
            u["u-sin-ruteo"].get("blockers"))
    t.igual("E-06 capacidad no soportada",
            [{"inputId": "plan.capabilityGaps", "code": "CAPABILITY_GAP"}], u["u-hueco"].get("blockers"))
    t.igual("E-06 capacidad soportada y no disponible",
            [{"inputId": "plan.capabilityStatus", "code": "CAPABILITY_UNAVAILABLE"}],
            u["u-caida"].get("blockers"))
    for uid in ("u-sin-ruteo", "u-hueco", "u-caida"):
        t.igual("E-06 %s BLOCKED" % uid, "BLOCKED", u[uid]["status"])
    t.igual("E-06 la lista PENDING", "PENDING", u["u-lista"]["status"])
    t.verdadero("E-06 la PENDING sin blockers", "blockers" not in u["u-lista"])
    t.igual("E-06 la cara espera", "WAITING_FOR_HUMAN_APPROVAL", u["u-cara"]["status"])
    t.verdadero("E-06 la que espera sin blockers", "blockers" not in u["u-cara"])
    dos = _armar([M20._unidad("u-las-dos", assignedAgent="dev-no-existe", capacidades=["no.existe"])])
    t.igual("E-06 sin ruteo y con hueco: los dos, el ruteo primero",
            ["agents.routing", "plan.capabilityGaps"],
            [b["inputId"] for b in dos["workUnits"][0].get("blockers") or []])
    t.igual("E-06 el plan valida", [], P.validar(plan))


def test_e07_sin_precondiciones_el_plan_es_blocked(t):
    """E-07 — sin precondiciones evaluadas, o con una pregunta bloqueante, el plan es BLOCKED,
    valida contra 2.1 y flowPreconditions nombra la pregunta."""
    sin = _armar([_lista()], precondiciones=None)
    t.igual("E-07 sin evaluar: BLOCKED", "BLOCKED", sin["status"])
    t.igual("E-07 y valida", [], P.validar(sin))
    t.verdadero("E-07 flowPreconditions dice que bloquea",
                any(q.get("blocking") for q in sin["flowPreconditions"]["questions"]))
    previas = json.loads(json.dumps(M20.PRECONDICIONES))
    previas["facts"]["repository.match"] = False
    con = _armar([_lista()], precondiciones=previas)
    t.igual("E-07 con el repositorio que no coincide: BLOCKED", "BLOCKED", con["status"])
    t.igual("E-07 y valida", [], P.validar(con))
    t.verdadero("E-07 la pregunta del repositorio esta y bloquea",
                any(q["inputId"] == "repository.match" and q["blocking"]
                    for q in con["flowPreconditions"]["questions"]))
    t.igual("E-07 la unidad no se toca: sigue PENDING", "PENDING", con["workUnits"][0]["status"])


def _causa_escrita(plan):
    previas = plan.get("flowPreconditions") or {}
    return (previas.get("status") != "READY"
            or any(q.get("blocking") for q in previas.get("questions") or [])
            or bool(P.no_disponibles(plan)) or bool(P.fuentes_que_bloquean(plan))
            or any(u.get("blockers") for u in plan["workUnits"]))


def test_e08_lo_escrito_esta_en_el_contrato(t):
    """E-08 — sobre las combinaciones, los estados escritos estan en el contrato y todo plan
    BLOCKED tiene su causa escrita."""
    vistos = set()
    for rotulo, plan in _combinaciones():
        vistos.add(plan["status"])
        t.verdadero("E-08 %s: el status del plan esta entre los cuatro" % rotulo,
                    plan["status"] in ESTADOS_PLAN)
        t.verdadero("E-08 %s: el de cada unidad entre los tres" % rotulo,
                    all(u["status"] in ESTADOS_UNIDAD for u in plan["workUnits"]))
        t.igual("E-08 %s: valida" % rotulo, [], P.validar(plan))
        if plan["status"] == "BLOCKED":
            t.verdadero("E-08 %s: BLOCKED con la causa escrita" % rotulo, _causa_escrita(plan))
        for u in plan["workUnits"]:
            if u["status"] == "BLOCKED":
                t.verdadero("E-08 %s: la unidad %s BLOCKED lleva blockers" % (rotulo, u["id"]),
                            P._bloqueos_validos(u.get("blockers")))
    t.igual("E-08 las combinaciones llegan a los cuatro estados", sorted(ESTADOS_PLAN), sorted(vistos))


def test_e09_la_precedencia_de_estado_de(t):
    """E-09 — precondiciones, caida o fuente (BLOCKED); hueco; aprobacion; unidad BLOCKED; listo."""
    listas = {"status": "READY", "questions": []}

    def doc(previas=listas, caida=False, hueco=False, aprobacion=False, bloqueada=False):
        return {"flowPreconditions": previas,
                "capabilityStatus": [{"availability": "SUPPORTED_UNAVAILABLE"}] if caida else [],
                "knowledgeSources": [],
                "capabilityGaps": [{"capability": "no.existe"}] if hueco else [],
                "humanApprovals": [{"status": "PENDING" if aprobacion else "APPROVED"}],
                "workUnits": [{"id": "u1", "status": "BLOCKED" if bloqueada else "PENDING"}]}

    todo = dict(hueco=True, aprobacion=True, bloqueada=True)
    t.igual("E-09 sin precondiciones, aunque haya de todo: BLOCKED", "BLOCKED",
            P.estado_de(doc(previas=None, **todo)))
    t.igual("E-09 una pregunta bloqueante: BLOCKED", "BLOCKED", P.estado_de(
        doc(previas={"status": "READY", "questions": [{"blocking": True}]}, **todo)))
    t.igual("E-09 una capacidad caida: BLOCKED", "BLOCKED", P.estado_de(doc(caida=True, **todo)))
    t.igual("E-09 un hueco pesa mas que una aprobacion", "CAPABILITY_RESOLUTION",
            P.estado_de(doc(hueco=True, aprobacion=True, bloqueada=True)))
    t.igual("E-09 una aprobacion pesa mas que una unidad BLOCKED", "WAITING_FOR_HUMAN_APPROVAL",
            P.estado_de(doc(aprobacion=True, bloqueada=True)))
    t.igual("E-09 una unidad BLOCKED: CAPABILITY_RESOLUTION", "CAPABILITY_RESOLUTION",
            P.estado_de(doc(bloqueada=True)))
    t.igual("E-09 sin nada: READY_FOR_EXECUTION", "READY_FOR_EXECUTION", P.estado_de(doc()))


# -- E-10 y E-11: la compuerta -------------------------------------------------------------

def _propuesta_w2(unidad_extra):
    propuesta = W2._propuesta()
    propuesta["workUnits"][0].update(unidad_extra)
    return propuesta


def test_e10_una_capacidad_no_es_un_agente_sin_ruteo(t):
    """E-10 — una unidad bloqueada por una capacidad no hace falso agents.routing."""
    plan = _armar([_hueco()])
    pregunta = [q for q in plan["flowPreconditions"]["questions"] if q["inputId"] == "agents.routing"]
    t.verdadero("E-10 la unidad lleva blockers", bool(plan["workUnits"][0].get("blockers")))
    t.verdadero("E-10 flowPreconditions no reporta el ruteo",
                not any(q.get("blocking") for q in pregunta))
    t.igual("E-10 ruteo_bloqueado es falso", False, P.ruteo_bloqueado(plan["workUnits"]))
    p = W2._proyecto()
    try:
        W2._contexto(p, W2.A)
        W2._plan(p, W2.A, _propuesta_w2({"requiredCapabilities": ["no.existe"]}))
        codigos = W2._codigos(W2._derivar(p, W2.A))
        t.verdadero("E-10 la tarea no dice AGENT_NOT_ROUTABLE: %s" % codigos,
                    "AGENT_NOT_ROUTABLE" not in codigos)
        t.verdadero("E-10 dice CAPABILITY_GAP: %s" % codigos, "CAPABILITY_GAP" in codigos)
    finally:
        W2._borrar(p)


def test_e11_un_agente_sin_ruteo_bloquea_la_tarea(t):
    """E-11 — con un agente no ruteable: plan BLOCKED, blockers de ruteo y tarea BLOCKED en
    PLANNING con AGENT_NOT_ROUTABLE, sin llegar a EXECUTION."""
    p = W2._proyecto()
    try:
        W2._contexto(p, W2.A)
        W2._plan(p, W2.A, _propuesta_w2({"assignedAgent": "dev-no-existe"}))
        plan = json.loads((p / ".claude" / "planes" / (W2.A + ".json")).read_text(encoding="utf-8"))
        t.igual("E-11 el plan BLOCKED", "BLOCKED", plan["status"])
        t.igual("E-11 la unidad con el blocker de ruteo", ["agents.routing"],
                [b["inputId"] for b in plan["workUnits"][0].get("blockers") or []])
        doc = W2._derivar(p, W2.A)
        t.igual("E-11 la tarea BLOCKED en PLANNING", ["PLANNING", "BLOCKED"],
                [doc.get("stage"), doc.get("status")])
        t.verdadero("E-11 con AGENT_NOT_ROUTABLE", "AGENT_NOT_ROUTABLE" in W2._codigos(doc))
    finally:
        W2._borrar(p)


# -- E-12 a E-15: la regla de lectura --------------------------------------------------------

def _rechaza(t, nombre, documento, aguja):
    try:
        P.aceptar_guardado(documento, "GCBA-1")
        t.verdadero("%s se rechaza" % nombre, False)
    except P.PlanRechazado as e:
        t.contiene("%s se rechaza nombrando %s" % (nombre, aguja), aguja, str(e))


def _con(plan, version=None, status=None, unidad=None):
    doc = json.loads(json.dumps(plan))
    if version is not None:
        doc["meta"]["schema_version"] = version
    if status is not None:
        doc["status"] = status
    if unidad is not None:
        doc["workUnits"][0].update(unidad)
    return doc


def test_e12_se_leen_tres_versiones(t):
    """E-12 — se leen 2.1, 2.0 y 1.0; otra version, o ninguna, se rechaza nombrandola."""
    plan = _armar([_lista()])
    for version in (V21, V20, V10):
        t.verdadero("E-12 se lee %s" % version,
                    P.aceptar_guardado(_con(plan, version), "GCBA-1") is not None)
    _rechaza(t, "E-12 un 3.0", _con(plan, "orchestration-plan/3.0"), "orchestration-plan/3.0")
    sin = _con(plan)
    del sin["meta"]["schema_version"]
    _rechaza(t, "E-12 uno sin version", sin, "schema_version")


def test_e13_blocked_se_lee_y_lo_retirado_no(t):
    """E-13 — un 1.0 o 2.0 con status BLOCKED se lee; DELEGATING o READY se rechazan."""
    plan = _armar([_lista()])
    for version in (V10, V20):
        t.verdadero("E-13 un %s BLOCKED se lee" % version,
                    P.aceptar_guardado(_con(plan, version, "BLOCKED"), "GCBA-1") is not None)
        _rechaza(t, "E-13 un %s DELEGATING" % version, _con(plan, version, "DELEGATING"),
                 "status: DELEGATING")
        _rechaza(t, "E-13 un %s con una unidad READY" % version,
                 _con(plan, version, unidad={"status": "READY"}), "workUnits[0].status: READY")


def test_e14_un_2_1_blocked_sin_blockers_se_rechaza(t):
    """E-14 — un 2.1 con una unidad BLOCKED sin blockers, o con [], se rechaza con 2 nombrando la
    unidad y sin tocar el archivo; con version 2.0 se lee."""
    plan = _armar([_lista()])
    for rotulo, cambio in (("sin blockers", {"status": "BLOCKED"}),
                           ("con blockers vacio", {"status": "BLOCKED", "blockers": []})):
        doc = _con(plan, V21, unidad=cambio)
        _rechaza(t, "E-14 un 2.1 %s" % rotulo, doc, "u-lista")
        t.verdadero("E-14 el mismo con version 2.0 se lee",
                    P.aceptar_guardado(_con(doc, V20), "GCBA-1") is not None)
    raiz = M20._proyecto_con_contexto(repositorio=True)
    try:
        destino = Path(raiz) / ".claude" / "planes" / (M20.CLAVE + ".json")
        destino.parent.mkdir(parents=True, exist_ok=True)
        roto = _con(_armar([_lista()]), V21, unidad={"status": "BLOCKED"})
        destino.write_text(json.dumps(roto), encoding="utf-8")
        antes = destino.read_bytes()
        propuesta = Path(raiz) / "prop.json"
        propuesta.write_text(json.dumps(M20._propuesta()), encoding="utf-8")
        codigo, _, error = M20._correr_cli(["plan", M20.CLAVE, "--proyecto", raiz,
                                            "--replanificar", str(propuesta), "--motivo", "x"])
        t.igual("E-14 --replanificar sale 2", 2, codigo)
        t.contiene("E-14 y nombra la unidad", "u-lista", error)
        t.igual("E-14 el archivo no cambio", antes, destino.read_bytes())
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def test_e15_replanificar_un_2_0_escribe_2_1(t):
    """E-15 — --replanificar sobre un 2.0 escribe 2.1, sube plan_version en uno y conserva la
    historia."""
    raiz = M20._proyecto_con_contexto(repositorio=True)
    try:
        destino = Path(raiz) / ".claude" / "planes" / (M20.CLAVE + ".json")
        destino.parent.mkdir(parents=True, exist_ok=True)
        viejo = _con(_armar([_lista()]), V20)
        destino.write_text(json.dumps(viejo), encoding="utf-8")
        propuesta = Path(raiz) / "prop.json"
        propuesta.write_text(json.dumps(M20._propuesta()), encoding="utf-8")
        codigo, _, error = M20._correr_cli(["plan", M20.CLAVE, "--proyecto", raiz,
                                            "--replanificar", str(propuesta), "--motivo", "otra"])
        t.igual("E-15 sale 0", 0, codigo)
        nuevo = json.loads(destino.read_text(encoding="utf-8"))
        t.igual("E-15 escribe 2.1", V21, nuevo["meta"]["schema_version"])
        t.igual("E-15 plan_version + 1", viejo["meta"]["plan_version"] + 1,
                nuevo["meta"]["plan_version"])
        t.igual("E-15 conserva la historia", viejo["planHistory"],
                nuevo["planHistory"][:len(viejo["planHistory"])])
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


# -- E-16 a E-19: el merge -----------------------------------------------------------------

def test_e16_nadie_le_pasa_harness_al_instalador_de_la_fabrica(t):
    """E-16 — solo 63-harness-unico-instalador.ps1 nombra el parametro viejo."""
    # El nombre se arma por partes: E-61 de harness-unico pide que fuera de los 63-* no aparezca.
    viejo = "-" + "Harness"
    patron = re.compile(r"""(?i)(['"]%s['"]|\s%s\s)""" % (viejo, viejo))
    con = sorted(p.name for p in (RAIZ / "tests" / "casos").glob("*.ps1")
                 if patron.search(p.read_text(encoding="utf-8-sig")))
    t.igual("E-16 solo el 63", ["63-harness-unico-instalador.ps1"], con)


def test_e17_doctor_calcula_la_barra_sin_mirar_el_harness(t):
    """E-17 — -Doctor calcula la Context Bar con Get-BarraDelDoctor sin condicionar por harness, y
    CONFIGURED es un aviso."""
    texto = (RAIZ / "install.ps1").read_text(encoding="utf-8-sig")
    desde = texto.find("$barraDoctor = Get-BarraDelDoctor")
    t.verdadero("E-17 -Doctor llama a Get-BarraDelDoctor", desde >= 0)
    previo = texto[max(0, desde - 600):desde]
    t.verdadero("E-17 sin condicionar por el harness instalado",
                "'desarrollo'" not in previo and "$d.harness" not in previo)
    tramo = texto[desde:desde + 1500]
    t.verdadero("E-17 CONFIGURED es un aviso",
                re.search(r"-eq 'CONFIGURED'\)\s*\{\s*EscribirAviso", tramo) is not None)


def test_e18_un_ciclo_sale_con_2(t):
    """E-18 — plan con un ciclo de dependencias sale con 2, igual que con un id repetido."""
    for rotulo, unidades in (
            ("un ciclo", [M20._unidad("a", dependencias=["b"]), M20._unidad("b", dependencias=["a"])]),
            ("un id repetido", [M20._unidad("a"), M20._unidad("a")])):
        raiz = M20._proyecto_con_contexto(repositorio=True)
        try:
            propuesta = os.path.join(raiz, "prop.json")
            io.open(propuesta, "w", encoding="utf-8").write(json.dumps(M20._propuesta(unidades)))
            codigo, _, _ = M20._correr_cli(["plan", M20.CLAVE, "--proyecto", raiz,
                                            "--propuesta", propuesta])
            t.igual("E-18 %s sale 2" % rotulo, 2, codigo)
        finally:
            shutil.rmtree(raiz, ignore_errors=True)


def test_e19_la_documentacion_dice_2_1(t):
    """E-19 — modelo-canonico.md y orquestacion.md nombran 2.1, BLOCKED del plan y blockers."""
    for ruta in (RAIZ / "docs" / "dominio" / "modelo-canonico.md", RAIZ / "docs" / "orquestacion.md"):
        texto = ruta.read_text(encoding="utf-8")
        t.contiene("E-19 %s nombra 2.1" % ruta.name, V21, texto)
        t.contiene("E-19 %s nombra blockers" % ruta.name, "blockers", texto)
        t.verdadero("E-19 %s nombra BLOCKED como estado del plan" % ruta.name,
                    re.search(r"BLOCKED[^\n]*(plan|precondici)|(plan|precondici)[^\n]*BLOCKED",
                              texto) is not None)
