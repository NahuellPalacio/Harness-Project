# El nucleo de orquestacion: de un TaskContext a un OrchestrationPlan.
#
# Escenarios E-01 a E-33 de docs/cambios/orquestacion-nucleo/spec.md. E-34 y E-35 son del
# instalador y viven en tests/casos/20-orquestacion-instalador.ps1.
#
# Lo que decide el agente -objetivo, dominios, unidades, senales- entra como una propuesta
# escrita a mano. Es exactamente la costura que el diseno define: el agente no se invoca en
# este cambio, y lo que se prueba es que lo que se hace con la propuesta sea correcto.
import io
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from orquestacion import capacidades as c_cap       # noqa: E402
from orquestacion import consumo as c_consumo       # noqa: E402
from orquestacion import modelo as c_modelo         # noqa: E402
from orquestacion import normativa as c_normativa   # noqa: E402
from orquestacion import plan as c_plan             # noqa: E402
from orquestacion import roster as c_roster         # noqa: E402

CLI = BIN / "dev-harness.py"
CLAVE = "GCBA-1234"

CONTEXTO = {
    "meta": {"task_key": CLAVE, "context_hash": "sha256:" + "a" * 64},
    "task": {"key": CLAVE, "type": "Historia de Usuario",
             "title": "Filtro por fecha en el listado",
             "acceptance_criteria": ["Filtra por rango", "Muestra vacio"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["Un tramite no se borra, se anula"]}},
    "documentation": {"items": [{"doc_id": "10"}, {"doc_id": "11"}]},
    "repository": {"project": {"name": "tramites/backoffice"}},
}

REGISTRO = {"jira.issue.read": "ENABLED", "gitlab.project.read": "DISABLED"}


def _unidad(uid, dominio="backend", capacidades=(), dependencias=(), senales=(), **extra):
    u = {"id": uid, "objective": "hacer " + uid, "domain": dominio,
         "requiredCapabilities": list(capacidades), "dependencies": list(dependencias),
         "signals": list(senales)}
    u.update(extra)
    return u


def _propuesta(unidades=None, **extra):
    p = {"objective": "Implementar el filtro por fecha", "domains": ["backend"],
         "policies": [], "workUnits": unidades or [_unidad("analizar")]}
    p.update(extra)
    return p


def _armar(propuesta=None, registro=None, config=None, contexto=None):
    return c_plan.armar(propuesta or _propuesta(), contexto or CONTEXTO,
                        REGISTRO if registro is None else registro,
                        config or {}, "0.18.0", "docs/x.json")


def _proyecto_con_contexto(contexto=None):
    raiz = tempfile.mkdtemp(prefix="harness-orq-")
    os.makedirs(os.path.join(raiz, ".claude", "contextos"))
    with io.open(os.path.join(raiz, ".claude", "contextos", CLAVE + ".json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps(contexto or CONTEXTO))
    with io.open(os.path.join(raiz, ".claude", "harness.capacidades.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"capacidades": REGISTRO}))
    return raiz


def _correr_cli(argv):
    import importlib.util
    spec = importlib.util.spec_from_file_location("dev_harness_orq", str(CLI))
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


# -- E-01 a E-05 — el contrato -------------------------------------------------

def test_e01_el_plan_valida(t):
    """E-01 — valida contra orchestration-plan/1.0, con el validador que ya existia."""
    documento = _armar()
    t.igual("E-01 sin errores", [], c_plan.validar(documento))
    t.igual("E-01 la version", "orchestration-plan/1.0", documento["meta"]["schema_version"])
    t.igual("E-01 el id", "pln_" + CLAVE, documento["meta"]["plan_id"])


def test_e02_el_estado_se_calcula(t):
    """E-02 — huecos, aprobaciones o nada pendiente: tres estados, del contenido."""
    listo = _armar(_propuesta([_unidad("u1", capacidades=["repository.read"])]))
    t.igual("E-02 sin nada pendiente", "READY_FOR_EXECUTION", listo["status"])

    con_hueco = _armar(_propuesta([_unidad("u1", capacidades=["no.existe"])]))
    t.igual("E-02 con hueco de capacidad", "CAPABILITY_RESOLUTION", con_hueco["status"])

    caro = _armar(_propuesta([_unidad("u1", capacidades=["repository.read"],
                                      senales=["ambiguity", "security_impact",
                                               "architectural_impact"])]))
    t.igual("E-02 con aprobacion pendiente", "WAITING_FOR_HUMAN_APPROVAL", caro["status"])

    # Y no se puede declarar a mano: el calculo pisa lo que venga.
    caro["status"] = "READY_FOR_EXECUTION"
    t.igual("E-02 el calculo manda sobre lo declarado", "WAITING_FOR_HUMAN_APPROVAL",
            c_plan.estado_de(caro))

    # El caso que decide cual de los dos gana: una unidad que ademas de necesitar
    # aprobacion pide una capacidad que no existe. Manda el hueco — ninguna aprobacion
    # arregla una capacidad que falta, y el orden inverso dejaria un plan esperando una
    # firma para algo que despues no se va a poder hacer igual.
    los_dos = _armar(_propuesta([_unidad("u1", capacidades=["no.existe"],
                                         senales=["ambiguity", "security_impact",
                                                  "architectural_impact"])]))
    t.igual("E-02 el hueco de capacidad le gana a la aprobacion pendiente",
            "CAPABILITY_RESOLUTION", los_dos["status"])
    t.igual("E-02 y la aprobacion sigue anotada igual", 1, len(los_dos["humanApprovals"]))


def test_e03_una_dependencia_que_no_existe(t):
    """E-03 — el plan no se escribe, y el error nombra la unidad y la dependencia."""
    levanto = ""
    try:
        _armar(_propuesta([_unidad("u1", dependencias=["fantasma"])]))
    except c_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-03 nombra la unidad", "u1", levanto)
    t.contiene("E-03 y la dependencia", "fantasma", levanto)


def test_e04_un_ciclo_de_dependencias(t):
    """E-04 — se rechaza nombrando las unidades enredadas."""
    levanto = ""
    try:
        _armar(_propuesta([_unidad("a", dependencias=["b"]), _unidad("b", dependencias=["a"])]))
    except c_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-04 lo dice", "ciclo", levanto)
    t.contiene("E-04 nombra a", "a", levanto)
    t.contiene("E-04 nombra b", "b", levanto)


def test_e05_el_orden_es_topologico_y_determinista(t):
    """E-05 — sale de las dependencias, y dos corridas dan el mismo orden."""
    unidades = [_unidad("tercera", dependencias=["segunda"]),
                _unidad("primera"),
                _unidad("segunda", dependencias=["primera"])]
    uno = _armar(_propuesta(unidades))
    dos = _armar(_propuesta(unidades))
    t.igual("E-05 el orden respeta las dependencias",
            ["primera", "segunda", "tercera"], uno["executionOrder"])
    t.igual("E-05 y es el mismo en dos corridas", uno["executionOrder"], dos["executionOrder"])

    # Sin dependencias entre si, el desempate es estable y no depende del orden de entrada.
    sueltas = _armar(_propuesta([_unidad("zeta"), _unidad("alfa")]))
    t.igual("E-05 el desempate es estable", ["alfa", "zeta"], sueltas["executionOrder"])


# -- E-06 a E-10 — las capacidades ---------------------------------------------

def test_e06_una_capacidad_del_registro(t):
    """E-06 — ENABLED en el registro es disponible, y se anota quien la pidio."""
    capacidades, huecos = c_cap.resolver(
        [_unidad("u1", capacidades=["jira.issue.read"])], REGISTRO)
    t.igual("E-06 disponible", ["jira.issue.read"], capacidades["available"])
    t.igual("E-06 sin huecos", [], huecos)


def test_e07_una_capacidad_local_del_runtime(t):
    """E-07 — la que declara el roster no pasa por el registro de integraciones."""
    capacidades, huecos = c_cap.resolver(
        [_unidad("u1", capacidades=["repository.read"])], {})
    t.igual("E-07 disponible sin registro", ["repository.read"], capacidades["available"])
    t.verdadero("E-07 el roster la declara", "repository.read" in c_roster.capacidades_locales())


def test_e08_una_capacidad_que_no_esta_en_ninguna_fuente(t):
    """E-08 — sale faltante y el hueco nombra la unidad que la pidio."""
    capacidades, huecos = c_cap.resolver(
        [_unidad("implementar", capacidades=["api.routes.inspect"]),
         _unidad("otra", capacidades=["api.routes.inspect"])], REGISTRO)
    t.igual("E-08 faltante", ["api.routes.inspect"], capacidades["missing"])
    t.igual("E-08 un hueco", 1, len(huecos))
    t.igual("E-08 con las dos unidades que la piden",
            ["implementar", "otra"], huecos[0]["workUnits"])


def test_e09_el_hueco_se_deriva(t):
    """E-09 — va a dev-tool-builder y la tool nace temporal, no permanente."""
    _, huecos = c_cap.resolver([_unidad("u1", capacidades=["no.existe"])], REGISTRO)
    t.igual("E-09 derivado", "dev-tool-builder", huecos[0]["derivedTo"])
    t.igual("E-09 temporal", "TEMPORARY", huecos[0]["toolClass"])


def test_e10_una_capacidad_deshabilitada_es_faltante(t):
    """E-10 — DISABLED no es disponible: el bootstrap ya dijo que esa integracion no anda."""
    capacidades, huecos = c_cap.resolver(
        [_unidad("u1", capacidades=["gitlab.project.read"])], REGISTRO)
    t.igual("E-10 faltante", ["gitlab.project.read"], capacidades["missing"])
    t.igual("E-10 y no disponible", [], capacidades["available"])


# -- E-11 a E-14 — el roster ---------------------------------------------------

def test_e11_un_agente_declarado_sin_md(t):
    """E-11 — aparece como hueco mientras no exista su archivo."""
    documento = _armar()
    backend = [a for a in documento["agents"] if a["name"] == "dev-backend"]
    t.igual("E-11 el roster lo declara", 1, len(backend))
    t.igual("E-11 y todavia no existe", False, backend[0]["exists"])
    t.verdadero("E-11 el aviso lo dice",
                any("dev-backend" in w and "no tiene su .md" in w
                    for w in documento["warnings"]))
    # Y la unidad tambien: un especialista recibe su unidad suelta, sin la lista de avisos.
    t.igual("E-11 la unidad asignada lo dice", False, documento["workUnits"][0]["agentExists"])
    t.igual("E-11 y nombra al agente igual", "dev-backend",
            documento["workUnits"][0]["assignedAgent"])


def test_e12_una_skill_declarada_sin_archivo(t):
    """E-12 — dev-data esta declarada y no existe: hueco."""
    documento = _armar()
    data = [s for s in documento["skills"] if s["name"] == "dev-data"]
    t.igual("E-12 declarada", 1, len(data))
    t.igual("E-12 y no existe", False, data[0]["exists"])
    t.verdadero("E-12 el aviso lo dice",
                any("dev-data" in w for w in documento["warnings"]))


def test_e13_la_existencia_la_dice_el_disco(t):
    """E-13 — un check que si existe no aparece como hueco."""
    documento = _armar()
    rutas = [c for c in documento["checks"] if c["name"] == "dev-api-rutas"]
    t.igual("E-13 declarado", 1, len(rutas))
    t.igual("E-13 y existe de verdad", True, rutas[0]["exists"])
    t.verdadero("E-13 no figura como hueco",
                not any("dev-api-rutas" in w for w in documento["warnings"]))
    # Y una skill que existe tampoco.
    api = [s for s in documento["skills"] if s["name"] == "dev-api"]
    t.igual("E-13 la skill dev-api existe", True, api[0]["exists"])


def test_e14_el_ruteo_no_trae_a_todos(t):
    """E-14 — un plan de backend no asigna dev-frontend a ninguna unidad."""
    documento = _armar(_propuesta([_unidad("u1", dominio="backend",
                                           capacidades=["repository.read"])]))
    nombres = [a["name"] for a in documento["agents"]]
    t.verdadero("E-14 esta el de backend", "dev-backend" in nombres)
    t.verdadero("E-14 no esta el de frontend", "dev-frontend" not in nombres)
    t.igual("E-14 la unidad va al de su dominio", "dev-backend",
            documento["workUnits"][0]["assignedAgent"])
    t.verdadero("E-14 ninguna unidad es de frontend",
                all(u["domain"] != "frontend" for u in documento["workUnits"]))


# -- E-15 a E-19 — el ruteo de modelo ------------------------------------------

def test_e15_sin_senales_el_tier_mas_barato(t):
    """E-15 — el default es el mas barato, y hay que justificar subir."""
    ruteo = c_modelo.enrutar([])
    t.igual("E-15 low_cost", "low_cost", ruteo["requiredTier"])
    t.igual("E-15 sin senales", [], ruteo["signals"])


def test_e16_las_senales_suben_el_tier(t):
    """E-16 — ambiguedad mas impacto arquitectonico pasa de standard."""
    ruteo = c_modelo.enrutar(["ambiguity", "architectural_impact"])
    t.verdadero("E-16 por encima de standard",
                c_modelo.TIERS.index(ruteo["requiredTier"]) > c_modelo.TIERS.index("standard"))
    t.igual("E-16 una sola senal chica no lo sube",
            "standard", c_modelo.enrutar(["many_components", "large_context"])["requiredTier"])


def test_e17_el_motivo_nombra_las_senales(t):
    """E-17 — un motivo generico no permite discutir la decision."""
    ruteo = c_modelo.enrutar(["security_impact", "novelty"])
    t.contiene("E-17 nombra la de seguridad", "seguridad", ruteo["reason"])
    t.contiene("E-17 y la de novedad", "antecedente", ruteo["reason"])
    t.contiene("E-17 y dice el tier", ruteo["requiredTier"], ruteo["reason"])

    # Una senal que nadie definio no puede empujar el tier en silencio.
    inventada = c_modelo.enrutar(["esto_no_existe"])
    t.igual("E-17 una senal inventada no suma", "low_cost", inventada["requiredTier"])
    t.contiene("E-17 y se dice que se ignoro", "esto_no_existe", inventada["reason"])


def test_e18_la_escalada_es_explicita_y_no_saltea(t):
    """E-18 — un tier por vez, con que fallo y cuantos intentos."""
    paso = c_modelo.escalar("low_cost", "el test no paso", 2)
    t.igual("E-18 sube uno solo", "standard", paso["to"])
    t.contiene("E-18 dice que fallo", "el test no paso", paso["reason"])
    t.contiene("E-18 y cuantos intentos", "2 intento", paso["reason"])
    t.igual("E-18 no saltea", "reasoning", c_modelo.escalar("standard", "x", 1)["to"])
    t.igual("E-18 desde el ultimo no escala", "premium",
            c_modelo.escalar("premium", "x", 1)["to"])
    t.igual("E-18 y lo declara agotado", True, c_modelo.escalar("premium", "x", 1)["exhausted"])


def test_e19_un_perfil_sin_modelo_es_un_hueco(t):
    """E-19 — no se inventa un nombre: el harness no sabe que modelos hay del otro lado."""
    documento = _armar()
    perfiles = {p["tier"]: p for p in documento["modelRouting"]["profiles"]}
    t.igual("E-19 estan los cuatro perfiles", 4, len(perfiles))
    t.igual("E-19 sin modelo declarado", False, perfiles["premium"]["declared"])
    t.igual("E-19 y sin inventarlo", "", perfiles["premium"]["model"])
    t.verdadero("E-19 el aviso lo dice",
                any("no hay modelo declarado" in w for w in documento["warnings"]))

    con_modelos = _armar(config={"modelRouting": {"perfiles": {"low_cost": "el-barato"}}})
    declarados = {p["tier"]: p for p in con_modelos["modelRouting"]["profiles"]}
    t.igual("E-19 el declarado se respeta", "el-barato", declarados["low_cost"]["model"])
    t.igual("E-19 y se marca declarado", True, declarados["low_cost"]["declared"])


# -- E-20 a E-24 — el consumo --------------------------------------------------

def test_e20_los_baratos_se_autoaprueban(t):
    """E-20 — low_cost y standard no preguntan."""
    politica = c_consumo.politica({})
    for tier in ("low_cost", "standard"):
        aprobada, solicitud, _ = c_consumo.decidir({"id": "u1"}, tier, "x", politica)
        t.igual("E-20 %s se autoaprueba" % tier, True, aprobada)
        t.igual("E-20 %s sin solicitud" % tier, None, solicitud)


def test_e21_premium_detiene_el_plan(t):
    """E-21 — sin presupuesto, el plan queda esperando y no se ejecuta nada."""
    documento = _armar(_propuesta([_unidad("u1", capacidades=["repository.read"],
                                           senales=["ambiguity", "security_impact",
                                                    "architectural_impact"])]))
    t.igual("E-21 el estado", "WAITING_FOR_HUMAN_APPROVAL", documento["status"])
    t.igual("E-21 la unidad tambien", "WAITING_FOR_HUMAN_APPROVAL",
            documento["workUnits"][0]["status"])
    t.igual("E-21 una solicitud pendiente", 1, len(documento["humanApprovals"]))
    t.igual("E-21 pendiente", "PENDING", documento["humanApprovals"][0]["status"])


def test_e22_la_solicitud_trae_la_alternativa(t):
    """E-22 — agente, unidad, tier, motivo, consumo y alternativa mas barata."""
    documento = _armar(_propuesta([_unidad("analisis", dominio="security",
                                           capacidades=["repository.read"],
                                           senales=["ambiguity", "security_impact",
                                                    "architectural_impact"])],
                                  domains=["security"]))
    solicitud = documento["humanApprovals"][0]
    t.igual("E-22 la unidad", "analisis", solicitud["workUnit"])
    t.igual("E-22 el agente", "dev-security", solicitud["agent"])
    t.igual("E-22 el tier", "premium", solicitud["tier"])
    t.igual("E-22 el consumo esperado", "ALTO", solicitud["expectedConsumption"])
    t.contiene("E-22 la alternativa es el tier de abajo", "reasoning",
               solicitud["cheaperAlternative"])
    t.contiene("E-22 el motivo nombra una senal", "seguridad", solicitud["reason"])

    texto = c_consumo.texto_de_solicitud(solicitud)
    t.contiene("E-22 el texto para la persona ofrece las tres acciones", "CANCELAR", texto)
    t.contiene("E-22 y no promete un modelo", "lo resuelve el runtime", texto)


def test_e23_el_presupuesto_se_gasta(t):
    """E-23 — dos llamadas autorizadas son dos, y la tercera vuelve a preguntar."""
    config = {"consumptionPolicy": {"sessionBudget": {"premiumCallsAllowed": 2}}}
    politica = c_consumo.politica(config)
    gastos = []
    for _ in range(3):
        aprobada, solicitud, presupuesto = c_consumo.decidir({"id": "u"}, "premium", "x", politica)
        politica = dict(politica, sessionBudget=presupuesto)
        gastos.append(aprobada)
    t.igual("E-23 las dos primeras pasan", [True, True, False], gastos)
    t.igual("E-23 y quedaron contadas", 2, politica["sessionBudget"]["premiumCallsSpent"])

    documento = _armar(_propuesta([_unidad("u1", capacidades=["repository.read"],
                                           senales=["ambiguity", "security_impact",
                                                    "architectural_impact"])]),
                       config=config)
    t.igual("E-23 con presupuesto el plan no se detiene", "READY_FOR_EXECUTION",
            documento["status"])
    t.igual("E-23 y se gasto una", 1,
            documento["consumptionPolicy"]["sessionBudget"]["premiumCallsSpent"])


def test_e24_la_politica_sale_de_la_configuracion(t):
    """E-24 — cambiar que se autoaprueba cambia el resultado, sin tocar el codigo."""
    config = {"consumptionPolicy": {"autoApprove": ["low_cost"],
                                    "requireHumanApproval": ["standard", "reasoning", "premium"]}}
    documento = _armar(_propuesta([_unidad("u1", capacidades=["repository.read"],
                                           senales=["novelty"])]),
                       config=config)
    t.igual("E-24 standard ahora pregunta", "WAITING_FOR_HUMAN_APPROVAL", documento["status"])
    t.igual("E-24 y el techo bajo", "low_cost",
            documento["workUnits"][0]["modelPolicy"]["maxTierWithoutApproval"])


# -- E-25 a E-28 — la normativa ------------------------------------------------

def test_e25_las_reglas_estan(t):
    """E-25 — las 26 de §7.1, con id, texto y pagina."""
    reglas = c_normativa.reglas()
    t.igual("E-25 son 26", 26, len(reglas))
    ids = [r["rule"] for r in reglas]
    for regla in ("G1", "G2", "D1", "D8", "P1", "P2", "P7", "C1", "C4", "M1", "M3"):
        t.verdadero("E-25 esta %s" % regla, regla in ids)
    t.igual("E-25 P1 tiene sus tres clausulas", 3, ids.count("P1"))
    for regla in reglas:
        t.verdadero("E-25 %s tiene texto" % regla["id"], len(regla["text"]) > 20)
        t.verdadero("E-25 %s tiene pagina" % regla["id"], regla["page"] in (12, 13, 14))


def test_e25b_las_reglas_salen_del_extracto_citable(t):
    """E-25 — el texto de cada regla es el del extracto, no una parafrasis.

    El extracto es el destilado citable del PDF. Si el dato se escribiera aparte, un dia
    dirian cosas distintas y la que se cita en un plan seria la copia.
    """
    extracto = (RAIZ / "normativa" / "extractos" / "ES0901.md").read_text(encoding="utf-8")
    catalogo = c_normativa.cargar()
    t.igual("E-25 apunta al extracto", "normativa/extractos/ES0901.md", catalogo["extract"])
    t.igual("E-25 la version", "6.3", catalogo["version"])
    # Un par de anclas textuales: si el extracto cambia, esto se entera.
    t.contiene("E-25 G1 sale del extracto",
               "herramientas y versiones homologadas", extracto)
    g1 = [r for r in c_normativa.reglas() if r["rule"] == "G1"][0]
    t.contiene("E-25 y el dato dice lo mismo", "herramientas y versiones homologadas",
               g1["text"])

    # El escenario dice "el texto de CADA regla", asi que se comparan las 26 contra el
    # extracto. Una sola ancla dejaba pasar dos parafrasis, y las dejo pasar: las encontro
    # el refutador comparandolas todas.
    import re
    import unicodedata

    def _plano(texto):
        sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto)
                             if unicodedata.category(c) != "Mn")
        # Las comillas se normalizan: el extracto alterna narracion y cita, asi que el
        # texto de una regla puede venir cosido de los dos lados de una comilla. Exigir un
        # span literal seria mas estricto que lo que el escenario pide.
        sin_comillas = re.sub(r'["“”«»]', "", sin_tildes)
        return re.sub(r"\s+", " ", sin_comillas).strip().lower()

    extracto_plano = _plano(extracto)
    ajenas = []
    for regla in c_normativa.reglas():
        # Se comparan tramos de la cita: el extracto alterna narracion y comillas, asi que
        # el texto de una regla puede venir cosido de dos citas.
        for tramo in [t for t in _plano(regla["text"]).split(". ") if len(t) > 40]:
            if tramo.rstrip(".") not in extracto_plano:
                ajenas.append("%s: %s" % (regla["id"], tramo[:60]))
    t.igual("E-25b ninguna regla parafrasea al extracto", [], ajenas)


def test_e26_una_regla_sin_condiciones_no_se_cita(t):
    """E-26 — sin conditions declaradas, nunca aplica."""
    t.igual("E-26 hoy no aplica ninguna", [], c_normativa.aplicables(["backend", "security"]))
    t.igual("E-26 porque estan todas sin clasificar", 26, len(c_normativa.sin_clasificar()))
    documento = _armar()
    t.igual("E-26 y el plan no cita ninguna", [], documento["applicableStandards"])


def test_e27_una_regla_con_condicion_se_cita(t):
    """E-27 — cuando la condicion coincide con un dominio, entra con su id."""
    catalogo = {"rules": [
        {"id": "ES0901-7.1-P4", "conditions": {"domains": ["backend"]}},
        {"id": "ES0901-7.1-D4", "conditions": {"domains": ["frontend"]}},
        {"id": "ES0901-7.1-G1", "conditions": {}}]}
    previo = c_normativa._CACHE.get("normativa")
    c_normativa._CACHE["normativa"] = catalogo
    try:
        t.igual("E-27 la de backend", ["ES0901-7.1-P4"], c_normativa.aplicables(["backend"]))
        t.igual("E-27 las dos", ["ES0901-7.1-D4", "ES0901-7.1-P4"],
                c_normativa.aplicables(["backend", "frontend"]))
        t.igual("E-27 la sin condiciones nunca", [], c_normativa.aplicables(["devops"]))
    finally:
        if previo is None:
            c_normativa._CACHE.pop("normativa", None)
        else:
            c_normativa._CACHE["normativa"] = previo


def test_e28_el_plan_declara_la_matriz_pendiente(t):
    """E-28 — cuantas quedan sin clasificar, en cada corrida."""
    documento = _armar()
    avisos = [w for w in documento["warnings"] if "sin clasificar" in w]
    t.igual("E-28 el aviso esta", 1, len(avisos))
    t.contiene("E-28 dice cuantas", "26 de las 26", avisos[0])


# -- E-29 y E-30 — el aislamiento y los secretos -------------------------------

def test_e29_cada_unidad_lleva_lo_suyo(t):
    """E-29 — una unidad de backend no lleva los criterios de accesibilidad."""
    documento = _armar(_propuesta(
        [_unidad("back", dominio="backend", capacidades=["repository.read"]),
         _unidad("devops", dominio="devops", capacidades=["repository.read"])],
        domains=["backend", "devops"]))
    por_id = {u["id"]: u for u in documento["workUnits"]}

    back = por_id["back"]["context"]
    t.igual("E-29 backend ve los criterios", ["Filtra por rango", "Muestra vacio"],
            back["acceptance_criteria"])
    t.igual("E-29 y las reglas del proyecto", ["Un tramite no se borra, se anula"], back["rules"])

    devops = por_id["devops"]["context"]
    t.igual("E-29 devops no ve los criterios", [], devops["acceptance_criteria"])
    t.igual("E-29 ni las reglas", [], devops["rules"])
    t.igual("E-29 ni los documentos", [], devops["documents"])
    t.verdadero("E-29 y lo que quedo afuera se declara",
                any("acceptance_criteria" in o for o in devops["omitted"]))
    t.verdadero("E-29 el aislamiento es auditable", len(devops["omitted"]) == 3)

    # 🔴 Lo que se escapaba: un dominio fuera de la tabla caia al default y se llevaba las
    # cuatro categorias con `omitted` vacio — indistinguible de un dominio que tiene
    # derecho a todo. Ahora no se arma el plan.
    levanto = ""
    try:
        _armar(_propuesta([_unidad("u1", dominio="inventado",
                                   capacidades=["repository.read"])],
                          domains=["inventado"]))
    except c_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-29 un dominio desconocido no pasa", "inventado", levanto)
    t.contiene("E-29 y dice cuales son los conocidos", "backend", levanto)

    # Los transversales del roster son dominios validos y tienen su propia fila: sin eso
    # caian al default igual que uno inventado.
    for dominio in ("tooling", "orchestration", "refutation"):
        t.verdadero("E-29 %s esta en la tabla" % dominio,
                    dominio in c_plan.CONTEXTO_POR_DOMINIO)
    declarados = sorted(a["domain"] for a in c_roster.cargar()["agents"])
    sin_fila = [d for d in declarados if d not in c_plan.CONTEXTO_POR_DOMINIO]
    t.igual("E-29 ningun dominio del roster queda sin fila", [], sin_fila)


def test_e30_ningun_token_llega_al_plan(t):
    """E-30 — el objetivo lo escribe un agente, y por ahi tambien se limpia."""
    fuga = "glpat" + "-A1b2C3D4E5F6G7H8I9J0"
    propuesta = _propuesta([_unidad("u1", capacidades=["repository.read"],
                                    objective="Probar con el token %s" % fuga)])
    propuesta["objective"] = "Usar %s para el filtro" % fuga
    documento = _armar(propuesta)
    t.no_contiene("E-30 no esta en el objetivo", fuga, documento["objective"])
    t.no_contiene("E-30 ni en la unidad", fuga, json.dumps(documento["workUnits"]))
    t.no_contiene("E-30 ni en el documento entero", fuga, json.dumps(documento))
    t.contiene("E-30 queda la marca", "secreto redactado", documento["objective"])

    # 🔴 Y el motivo de una replanificacion, que lo escribe una persona en la linea de
    # comandos y no existia cuando se armo el plan. Ahi quedaba en claro.
    raiz = _proyecto_con_contexto()
    propuesta = os.path.join(raiz, "prop.json")
    with io.open(propuesta, "w", encoding="utf-8") as f:
        f.write(json.dumps(_propuesta([_unidad("u1", capacidades=["repository.read"])])))
    _correr_cli(["plan", CLAVE, "--proyecto", raiz, "--propuesta", propuesta])
    codigo, _, _ = _correr_cli(["plan", CLAVE, "--proyecto", raiz,
                                "--replanificar", propuesta,
                                "--motivo", "el token %s dejo de andar" % fuga])
    t.igual("E-30 la replanificacion sale bien", 0, codigo)
    escrito = io.open(os.path.join(raiz, ".claude", "planes", CLAVE + ".json"),
                      encoding="utf-8").read()
    t.no_contiene("E-30 el motivo no lleva el token al plan escrito", fuga, escrito)
    t.contiene("E-30 y queda la marca en el historial", "secreto redactado", escrito)

    # 🔴 Que la limpieza salga de las claves del documento y no de una lista escrita a
    # mano. Una seccion nueva manana tiene que quedar cubierta por existir: la primera
    # version se escapaba por `planHistory` y la segunda -una lista de dieciseis- se
    # habria escapado por la proxima.
    documento = _armar()
    documento["seccion_que_no_existia_ayer"] = "el token %s" % fuga
    c_plan._limpiar(documento)
    t.no_contiene("E-30 una seccion nueva queda cubierta por existir", fuga,
                  documento["seccion_que_no_existia_ayer"])
    t.igual("E-30 y meta es lo unico que no se limpia", ("meta",), c_plan.SIN_LIMPIAR)


def test_e29b_el_dominio_del_plan_tambien_se_valida(t):
    """E-29 — no solo el de cada unidad: un plan que declara un dominio inventado y
    unidades en otro es un plan que dice dos cosas."""
    levanto = ""
    try:
        _armar(_propuesta([_unidad("u1", dominio="backend",
                                   capacidades=["repository.read"])],
                          domains=["backend", "inventado"]))
    except c_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-29 el dominio del plan tambien se valida", "inventado", levanto)
    t.contiene("E-29 y lista los conocidos", "backend", levanto)


# -- E-31 a E-33 — la CLI ------------------------------------------------------

def test_e31_sin_contexto_no_hay_plan(t):
    """E-31 — codigo 2, dice que corran contexto, y no escribe nada."""
    raiz = tempfile.mkdtemp(prefix="harness-orq-")
    os.makedirs(os.path.join(raiz, ".claude"))
    codigo, salida, error = _correr_cli(["plan", CLAVE, "--proyecto", raiz])
    t.igual("E-31 codigo 2", 2, codigo)
    t.contiene("E-31 manda a correr contexto", "dev-harness.py contexto", error)
    t.verdadero("E-31 sin escribir nada",
                not os.path.isdir(os.path.join(raiz, ".claude", "planes")))


def test_e32_la_plantilla_trae_lo_que_hace_falta(t):
    """E-32 — el esqueleto con el resumen de la tarea, las capacidades y los dominios."""
    raiz = _proyecto_con_contexto()
    codigo, salida, _ = _correr_cli(["plan", CLAVE, "--proyecto", raiz, "--plantilla"])
    plantilla = json.loads(salida)
    t.igual("E-32 codigo 0", 0, codigo)
    t.igual("E-32 trae la tarea", "Filtro por fecha en el listado", plantilla["_tarea"]["title"])
    t.igual("E-32 y sus criterios", 2, len(plantilla["_tarea"]["acceptance_criteria"]))
    t.verdadero("E-32 trae las capacidades disponibles",
                "repository.read" in plantilla["_capacidadesDisponibles"])
    t.verdadero("E-32 y los dominios conocidos",
                "backend" in plantilla["_dominiosConocidos"])
    t.verdadero("E-32 deja los campos a completar vacios",
                plantilla["objective"] == "" and plantilla["domains"] == [])
    t.verdadero("E-32 no escribio ningun plan",
                not os.path.isdir(os.path.join(raiz, ".claude", "planes")))


def test_e33_replanificar_sube_la_version_y_guarda_el_motivo(t):
    """E-33 — el historial es el unico lugar donde 'por que este plan' tiene respuesta."""
    raiz = _proyecto_con_contexto()
    primera = os.path.join(raiz, "p1.json")
    with io.open(primera, "w", encoding="utf-8") as f:
        f.write(json.dumps(_propuesta([_unidad("analizar", capacidades=["repository.read"])])))
    codigo, _, _ = _correr_cli(["plan", CLAVE, "--proyecto", raiz, "--propuesta", primera])
    t.igual("E-33 la primera sale bien", 0, codigo)

    segunda = os.path.join(raiz, "p2.json")
    with io.open(segunda, "w", encoding="utf-8") as f:
        f.write(json.dumps(_propuesta([
            _unidad("analizar", capacidades=["repository.read"]),
            _unidad("crear-query", capacidades=["repository.write"],
                    dependencias=["analizar"])])))
    codigo, salida, error = _correr_cli(
        ["plan", CLAVE, "--proyecto", raiz, "--replanificar", segunda,
         "--motivo", "el repositorio usa CQRS"])
    t.igual("E-33 la replanificacion sale bien", 0, codigo)

    documento = json.loads(io.open(os.path.join(raiz, ".claude", "planes", CLAVE + ".json"),
                                   encoding="utf-8").read())
    t.igual("E-33 subio la version", 2, documento["meta"]["plan_version"])
    t.igual("E-33 el historial tiene las dos", 2, len(documento["planHistory"]))
    t.igual("E-33 con el motivo", "el repositorio usa CQRS", documento["planHistory"][1]["reason"])
    t.verdadero("E-33 y dice que cambio",
                any("crear-query" in c for c in documento["planHistory"][1]["changes"]))

    codigo, _, error = _correr_cli(
        ["plan", CLAVE, "--proyecto", raiz, "--replanificar", segunda])
    t.igual("E-33 sin motivo no se replanifica", 2, codigo)
    t.contiene("E-33 y lo explica", "no se puede auditar", error)


def test_e33b_un_plan_completo_sale_listo(t):
    """E-33b — el camino feliz entero, contra la CLI y validando el archivo escrito."""
    raiz = _proyecto_con_contexto()
    propuesta = os.path.join(raiz, "prop.json")
    with io.open(propuesta, "w", encoding="utf-8") as f:
        f.write(json.dumps(_propuesta([
            _unidad("analizar", capacidades=["repository.read"]),
            _unidad("implementar", capacidades=["repository.write"],
                    dependencias=["analizar"], senales=["novelty"])])))
    codigo, salida, _ = _correr_cli(["plan", CLAVE, "--proyecto", raiz,
                                     "--propuesta", propuesta])
    t.igual("E-33b codigo 0", 0, codigo)
    t.contiene("E-33b el resumen dice el estado", "READY_FOR_EXECUTION", salida)

    documento = json.loads(io.open(os.path.join(raiz, ".claude", "planes", CLAVE + ".json"),
                                   encoding="utf-8").read())
    t.igual("E-33b valida", [], c_plan.validar(documento))
    t.igual("E-33b listo", "READY_FOR_EXECUTION", documento["status"])
    t.igual("E-33b dos unidades", 2, len(documento["workUnits"]))
    t.igual("E-33b en orden", ["analizar", "implementar"], documento["executionOrder"])
    t.igual("E-33b el barato queda barato", "low_cost",
            documento["workUnits"][0]["modelPolicy"]["requiredTier"])
