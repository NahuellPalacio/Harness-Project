# El registro de agentes: la existencia se declara y se valida.
#
# Escenarios de docs/cambios/agent-registry/spec.md: E-01 a E-25 son la Fase A -el registro,
# su validador y el diagnostico del disco- y E-26 a E-29 la Fase B, que es plan.py y la
# propagacion del estado a cada unidad de trabajo.
#
# Los estados de error se prueban contra registros FABRICADOS en memoria. Ninguno rompe el
# arbol: un test que rompe archivos versionados deja el arbol roto si la corrida se mata, y
# eso ya paso en este repositorio.
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from orquestacion import capacidades as c_cap          # noqa: E402
from orquestacion import registro_agentes as c_reg     # noqa: E402
from orquestacion import roster as c_roster            # noqa: E402


def _doc():
    return copy.deepcopy(c_reg.cargar())


def _agente(doc, agent_id):
    for a in doc["agents"]:
        if a["id"] == agent_id:
            return a
    raise AssertionError("no esta " + agent_id)


def _estado_agente(doc, agent_id):
    return c_reg.validar_registro(doc)["agents"][agent_id]["state"]


def _estado_skill(doc, agent_id, skill_id):
    return c_reg.validar_registro(doc)["skills"][(agent_id, skill_id)]["state"]


# -- E-01 a E-05 — el registro es la fuente ------------------------------------

def test_e01_los_diez_resuelven_del_registro(t):
    """E-01 — los 10 declarados resuelven, y la matriz de 7.1 no participa."""
    from orquestacion import normativa as c_normativa
    doc = _doc()
    informe = c_reg.validar_registro(doc)
    t.igual("E-01 diez declarados", 10, len(doc["agents"]))
    validos = [a for a in informe["agents"].values() if a["state"] in c_reg.AGENTE_RUTEABLE]
    t.igual("E-01 diez validos", 10, len(validos))

    # Y la matriz sigue sin clasificar: la existencia no dependio de ella.
    reglas = c_normativa.cargar()
    sin_clasificar = [r for r in reglas.get("rules", []) if not r.get("owners")]
    t.verdadero("E-01 la matriz sigue vacia", len(sin_clasificar) > 0)
    t.igual("E-01 y los diez siguen existiendo", 10, len(validos))


def test_e02_un_agente_que_no_esta_declarado(t):
    """E-02 — id desconocido y sin archivo: AGENT_NOT_FOUND, cerrado."""
    r = c_reg.resolver_ruteo("dev-inventado")
    t.igual("E-02 el resultado", "AGENT_NOT_FOUND", r["result"])
    t.igual("E-02 no existe", False, r["agentExists"])
    t.igual("E-02 no rutea", False, r["routable"])

    # La otra mitad: no declarado pero con archivo en disco es el huerfano de E-18, no
    # AGENT_NOT_FOUND. Tampoco rutea.
    t.verdadero("E-02 el archivo del no declarado esta",
                (RAIZ / "harnesses" / "desarrollo" / "agents" / "dev-iniciador-code.md").is_file())
    r = c_reg.resolver_ruteo("dev-iniciador-code")
    t.igual("E-02 con archivo es huerfano", "ORPHAN_AGENT", r["result"])
    t.igual("E-02 con archivo no existe", False, r["agentExists"])
    t.igual("E-02 con archivo no rutea", False, r["routable"])


def test_e03_un_archivo_no_declara_un_agente(t):
    """E-03 — el disco no da de alta: dev-iniciador-code esta y no es un agente."""
    doc = _doc()
    t.igual("E-03 no esta declarado", False, c_reg.hay_agente("dev-iniciador-code", doc))
    t.igual("E-03 y no existe para el harness", False,
            c_roster.existe_agente("dev-iniciador-code"))
    huerfanos = [h["id"] for h in c_reg.descubrir_huerfanos(doc)]
    t.verdadero("E-03 aparece como huerfano", "dev-iniciador-code" in huerfanos)


def test_e04_el_registro_valida_contra_su_schema(t):
    """E-04 — valida, y el schema entra entero en el subconjunto soportado."""
    t.vacio("E-04 sin errores de schema", c_reg.validar_schema(_doc()))
    doc = _doc()
    doc["registryType"] = "otra-cosa"
    t.verdadero("E-04 un registryType ajeno no valida", len(c_reg.validar_schema(doc)) > 0)


def test_e05_hay_un_solo_roster(t):
    """E-05 — roster.json ya no declara agentes ni skills."""
    ruta = c_roster.ruta_de_regla("roster.json")
    with open(ruta, encoding="utf-8-sig") as f:
        crudo = json.load(f)
    t.verdadero("E-05 sin agents", "agents" not in crudo)
    t.verdadero("E-05 sin skills", "skills" not in crudo)
    t.verdadero("E-05 conserva checks", "checks" in crudo)
    t.verdadero("E-05 conserva capacidadesLocales", "capacidadesLocales" in crudo)
    # Y lo que el planificador pide sigue contestandose, ahora desde el registro.
    t.verdadero("E-05 los agentes siguen saliendo", len(c_roster.agentes_para(["backend"])) > 0)
    t.verdadero("E-05 las skills tambien", len(c_roster.skills_para(["backend"])) > 0)


# -- E-06 a E-10c — tipos, politica de skills y duplicados ---------------------

def test_e06_infraestructura_con_cero_skills(t):
    """E-06 — dev-tool-builder es VALID con cero skills, sin inventarle ninguna."""
    doc = _doc()
    t.igual("E-06 cero skills", 0, len(_agente(doc, "dev-tool-builder")["skills"]))
    t.igual("E-06 y es valido", "VALID", _estado_agente(doc, "dev-tool-builder"))


def test_e07_orquestador_y_critico_con_cero_skills(t):
    """E-07 — ORCHESTRATOR_AGENT y CRITIC_AGENT valen con cero skills."""
    doc = _doc()
    for aid, tipo in (("dev-orchestrator", "ORCHESTRATOR_AGENT"),
                      ("dev-refutador", "CRITIC_AGENT")):
        t.igual("E-07 %s es %s" % (aid, tipo), tipo, _agente(doc, aid)["type"])
        t.igual("E-07 %s cero skills" % aid, 0, len(_agente(doc, aid)["skills"]))
        t.igual("E-07 %s valido" % aid, "VALID", _estado_agente(doc, aid))


def test_e08_un_especialista_sin_skills_instaladas(t):
    """E-08 — SPECIALIST_AGENT sin ninguna INSTALLED es AGENT_SKILL_POLICY_INVALID."""
    doc = _doc()
    _agente(doc, "dev-backend")["skills"] = []
    t.igual("E-08 sin ninguna skill", "AGENT_SKILL_POLICY_INVALID",
            _estado_agente(doc, "dev-backend"))

    # Y el caso que de verdad distingue la regla: declara skills, pero TODAS pendientes.
    # "Al menos una INSTALLED" no es "al menos una declarada": un especialista con seis
    # skills que todavia no existen no puede implementar nada.
    doc = _doc()
    for skill in _agente(doc, "dev-backend")["skills"]:
        skill["status"] = "DECLARED_NOT_INSTALLED"
        skill["reason"] = "todavia no"
    t.igual("E-08 con todas pendientes", "AGENT_SKILL_POLICY_INVALID",
            _estado_agente(doc, "dev-backend"))


def test_e09_un_tipo_que_no_existe(t):
    """E-09 — un tipo fuera de agentTypes es AGENT_TYPE_INVALID."""
    doc = _doc()
    _agente(doc, "dev-backend")["type"] = "SUPER_AGENT"
    t.igual("E-09 el estado", "AGENT_TYPE_INVALID", _estado_agente(doc, "dev-backend"))


def test_e10_archivo_que_falta_y_identidad_que_no_coincide(t):
    """E-10 — AGENT_FILE_MISSING y AGENT_ID_MISMATCH, sin deducir del nombre del archivo."""
    doc = _doc()
    _agente(doc, "dev-backend")["agentFile"] = "agents/dev-que-no-esta.md"
    t.igual("E-10 archivo ausente", "AGENT_FILE_MISSING", _estado_agente(doc, "dev-backend"))

    doc = _doc()
    # El archivo existe, pero dice ser otro agente.
    _agente(doc, "dev-backend")["agentFile"] = "agents/dev-frontend.md"
    t.igual("E-10 identidad ajena", "AGENT_ID_MISMATCH", _estado_agente(doc, "dev-backend"))


def test_e10b_dos_agentes_con_el_mismo_id(t):
    """E-10b — DUPLICATE_AGENT_ID."""
    doc = _doc()
    doc["agents"].append(copy.deepcopy(_agente(doc, "dev-backend")))
    informe = c_reg.validar_registro(doc)
    t.igual("E-10b el estado", "DUPLICATE_AGENT_ID", informe["agents"]["dev-backend"]["state"])


def test_e10c_dos_duenos_del_mismo_dominio(t):
    """E-10c — DUPLICATE_DOMAIN_OWNER, y no se elige uno en silencio."""
    doc = _doc()
    otro = copy.deepcopy(_agente(doc, "dev-backend"))
    otro["id"] = "dev-backend-bis"
    otro["agentFile"] = "agents/dev-backend.md"
    doc["agents"].append(otro)
    informe = c_reg.validar_registro(doc)
    t.igual("E-10c el segundo choca", "DUPLICATE_DOMAIN_OWNER",
            informe["agents"]["dev-backend-bis"]["state"])
    t.igual("E-10c el primero sigue valido", "VALID", informe["agents"]["dev-backend"]["state"])


# -- E-11 a E-17 — los estados de una skill ------------------------------------

def test_e11_una_skill_instalada(t):
    """E-11 — INSTALLED con su SKILL.md es SKILL_AVAILABLE y rutea."""
    doc = _doc()
    t.igual("E-11 el estado", "SKILL_AVAILABLE",
            _estado_skill(doc, "dev-backend", "dev-api"))
    r = c_reg.resolver_ruteo("dev-backend", "dev-api")
    t.igual("E-11 rutea", "ROUTABLE", r["result"])
    t.igual("E-11 y existe", True, r["skillExists"])


def test_e12_las_dos_pendientes(t):
    """E-12 — dev-miba y dev-esb: DECLARED_NOT_INSTALLED y SPECIALIZED_SKILL_GAP."""
    doc = _doc()
    for sid in ("dev-miba", "dev-esb"):
        declarada = c_reg.skill("dev-integration", sid, doc)
        t.igual("E-12 %s declarada" % sid, "DECLARED_NOT_INSTALLED", declarada["status"])
        t.verdadero("E-12 %s dice por que" % sid, bool(declarada.get("reason")))
        r = c_reg.resolver_ruteo("dev-integration", sid)
        t.igual("E-12 %s el resultado" % sid, "SPECIALIZED_SKILL_GAP", r["result"])
        t.igual("E-12 %s no rutea" % sid, False, r["routable"])
        t.igual("E-12 %s el agente sigue existiendo" % sid, True, r["agentExists"])


def test_e13_el_agente_sigue_valido_con_pendientes(t):
    """E-13 — VALID_WITH_PENDING_SKILLS, y las instaladas se rutean igual."""
    doc = _doc()
    t.igual("E-13 el estado del agente", "VALID_WITH_PENDING_SKILLS",
            _estado_agente(doc, "dev-integration"))
    t.igual("E-13 existe", True, c_roster.existe_agente("dev-integration"))
    # Las otras cuatro salen del registro, no de una lista escrita en el test; el test solo
    # afirma cuantas y cuales son.
    instaladas = sorted(s["id"] for s in c_reg.skills_de("dev-integration", doc)
                        if s["status"] == "INSTALLED")
    t.igual("E-13 son cuatro instaladas", 4, len(instaladas))
    t.igual("E-13 y son estas", sorted(["dev-openid-connect", "dev-integration-implementation",
                                        "dev-service-integration", "dev-external-integration"]),
            instaladas)
    for sid in instaladas:
        r = c_reg.resolver_ruteo("dev-integration", sid)
        t.igual("E-13 %s rutea" % sid, "ROUTABLE", r["result"])
        t.igual("E-13 %s routable" % sid, True, r["routable"])


def test_e14_una_instalada_sin_su_archivo(t):
    """E-14 — SKILL_FILE_MISSING."""
    doc = _doc()
    _agente(doc, "dev-backend")["skills"][0]["file"] = "skills/dev-que-no-esta/SKILL.md"
    sid = _agente(doc, "dev-backend")["skills"][0]["id"]
    t.igual("E-14 el estado", "SKILL_FILE_MISSING", _estado_skill(doc, "dev-backend", sid))


def test_e15_la_misma_skill_bajo_dos_duenos(t):
    """E-15 — SKILL_OWNER_CONFLICT."""
    doc = _doc()
    robada = copy.deepcopy(_agente(doc, "dev-backend")["skills"][0])
    _agente(doc, "dev-frontend")["skills"].append(robada)
    informe = c_reg.validar_registro(doc)
    t.igual("E-15 el segundo dueno choca", "SKILL_OWNER_CONFLICT",
            informe["skills"][("dev-frontend", robada["id"])]["state"])


def test_e15b_una_skill_que_dice_ser_otra(t):
    """E-15b — SKILL_ID_MISMATCH: la identidad no sale del nombre del directorio."""
    doc = _doc()
    _agente(doc, "dev-backend")["skills"][0]["file"] = "skills/dev-ui/SKILL.md"
    sid = _agente(doc, "dev-backend")["skills"][0]["id"]
    t.igual("E-15b el estado", "SKILL_ID_MISMATCH", _estado_skill(doc, "dev-backend", sid))


def test_e16_una_skill_deprecada_no_rutea(t):
    """E-16 — DEPRECATED_SKILL, cerrado."""
    doc = _doc()
    _agente(doc, "dev-backend")["skills"][0]["status"] = "DEPRECATED"
    sid = _agente(doc, "dev-backend")["skills"][0]["id"]
    t.igual("E-16 el estado", "DEPRECATED_SKILL", _estado_skill(doc, "dev-backend", sid))
    t.verdadero("E-16 no esta entre los ruteables",
                "DEPRECATED_SKILL" not in c_reg.SKILL_RUTEABLE)


def test_e17_una_skill_que_el_agente_no_declara(t):
    """E-17 — SKILL_NOT_DECLARED_FOR_AGENT, distinto de UNDECLARED_SKILL."""
    r = c_reg.resolver_ruteo("dev-backend", "dev-ui")
    t.igual("E-17 el resultado", "SKILL_NOT_DECLARED_FOR_AGENT", r["result"])
    t.igual("E-17 no rutea", False, r["routable"])
    t.igual("E-17 pero el agente existe", True, r["agentExists"])


# -- E-18 a E-20 — el disco diagnostica ----------------------------------------

def test_e18_el_huerfano(t):
    """E-18 — ORPHAN_AGENT: visible, no adoptado, no ruteable."""
    r = c_reg.resolver_ruteo("dev-iniciador-code")
    t.igual("E-18 el resultado", "ORPHAN_AGENT", r["result"])
    t.igual("E-18 el archivo esta", True, r["fileExists"])
    t.igual("E-18 no existe como agente", False, r["agentExists"])
    t.igual("E-18 no rutea", False, r["routable"])


def test_e18b_conocido_es_aviso_y_nuevo_es_error(t):
    """E-18b — el reconocimiento distingue, y no vuelve ruteable a nadie."""
    doc = _doc()
    conocidos = c_reg.descubrir_huerfanos(doc)
    t.igual("E-18b hay uno", 1, len(conocidos))
    t.igual("E-18b reconocido", True, conocidos[0]["acknowledged"])
    t.igual("E-18b y es aviso", "WARNING", conocidos[0]["severity"])
    t.igual("E-18b sigue sin rutear", False, conocidos[0]["routable"])

    # Uno nuevo: se saca del registro un agente cuyo archivo esta en disco.
    doc["agents"] = [a for a in doc["agents"] if a["id"] != "dev-quality"]
    nuevos = {h["id"]: h for h in c_reg.descubrir_huerfanos(doc)}
    t.verdadero("E-18b aparece el nuevo", "dev-quality" in nuevos)
    t.igual("E-18b y es error", "ERROR", nuevos["dev-quality"]["severity"])
    t.igual("E-18b el reconocido sigue siendo aviso", "WARNING",
            nuevos["dev-iniciador-code"]["severity"])


def test_e19_una_skill_en_disco_sin_declarar(t):
    """E-19 — UNDECLARED_SKILL."""
    doc = _doc()
    t.vacio("E-19 hoy no hay ninguna", c_reg.descubrir_no_declaradas(doc))
    _agente(doc, "dev-backend")["skills"] = [
        s for s in _agente(doc, "dev-backend")["skills"] if s["id"] != "dev-api"]
    no_declaradas = {s["id"]: s for s in c_reg.descubrir_no_declaradas(doc)}
    t.verdadero("E-19 aparece", "dev-api" in no_declaradas)
    t.igual("E-19 el estado", "UNDECLARED_SKILL", no_declaradas["dev-api"]["state"])
    t.igual("E-19 y es error", "ERROR", no_declaradas["dev-api"]["severity"])


def test_e20_las_cuentas_se_calculan(t):
    """E-20 — ninguna cifra del reporte esta escrita en el codigo."""
    r = c_reg.reporte()
    doc = _doc()
    t.igual("E-20 agentes declarados", len(doc["agents"]), r["summary"]["declaredAgents"])
    instaladas = sum(1 for a in doc["agents"] for s in a["skills"]
                     if s["status"] == "INSTALLED")
    t.igual("E-20 skills instaladas", instaladas, r["summary"]["installedSkills"])

    # Y si el registro cambia, las cuentas cambian solas.
    doc["agents"] = [a for a in doc["agents"] if a["id"] != "dev-quality"]
    otro = c_reg.reporte(doc)
    t.igual("E-20 un agente menos", len(doc["agents"]), otro["summary"]["declaredAgents"])
    t.verdadero("E-20 y no es la misma cifra de antes",
                otro["summary"]["declaredAgents"] != r["summary"]["declaredAgents"])


# -- E-21 a E-23 — el ruteo ----------------------------------------------------

def test_e21_dev_backend_rutea(t):
    """E-21 — agente valido con skills instaladas."""
    r = c_reg.resolver_ruteo("dev-backend")
    t.igual("E-21 rutea", "ROUTABLE", r["result"])
    t.igual("E-21 existe", True, r["agentExists"])
    t.igual("E-21 valido", "VALID", r["agentValidation"])


def test_e22_quality_con_su_skill(t):
    """E-22 — dev-quality + dev-test-automation es ROUTABLE."""
    r = c_reg.resolver_ruteo("dev-quality", "dev-test-automation")
    t.igual("E-22 el resultado", "ROUTABLE", r["result"])
    t.igual("E-22 rutea", True, r["routable"])


def test_e23_todo_error_rutea_cerrado(t):
    """E-23 — ningun estado estructural de error deja rutear."""
    t.igual("E-23 dos estados de agente rutean", ("VALID", "VALID_WITH_PENDING_SKILLS"),
            c_reg.AGENTE_RUTEABLE)
    t.igual("E-23 uno de skill", ("SKILL_AVAILABLE",), c_reg.SKILL_RUTEABLE)

    cerrados = ("AGENT_NOT_FOUND", "ORPHAN_AGENT", "AGENT_FILE_MISSING", "AGENT_ID_MISMATCH",
                "AGENT_TYPE_INVALID", "AGENT_SKILL_POLICY_INVALID", "DUPLICATE_AGENT_ID",
                "DUPLICATE_DOMAIN_OWNER", "SKILL_FILE_MISSING", "SKILL_ID_MISMATCH",
                "SKILL_OWNER_CONFLICT", "SKILL_NOT_DECLARED_FOR_AGENT", "UNDECLARED_SKILL",
                "DEPRECATED_AGENT", "DEPRECATED_SKILL")
    for estado in cerrados:
        t.verdadero("E-23 %s no es ruteable" % estado,
                    estado not in c_reg.AGENTE_RUTEABLE and estado not in c_reg.SKILL_RUTEABLE)
        t.igual("E-23 %s es error" % estado, "ERROR", c_reg.SEVERIDAD.get(estado, "ERROR"))

    # Y en una corrida real: un agente invalido no rutea aunque este declarado.
    doc = _doc()
    _agente(doc, "dev-backend")["type"] = "SUPER_AGENT"
    r = c_reg.resolver_ruteo("dev-backend", None, doc)
    t.igual("E-23 no rutea", False, r["routable"])
    t.igual("E-23 y dice por que", "AGENT_TYPE_INVALID", r["result"])


# -- E-24 y E-25 — la frontera con la capacidad --------------------------------

def test_e24_un_hueco_de_skill_no_llama_al_constructor(t):
    """E-24 — SPECIALIZED_SKILL_GAP no deriva a dev-tool-builder."""
    r = c_reg.resolver_ruteo("dev-integration", "dev-miba")
    t.igual("E-24 el resultado", "SPECIALIZED_SKILL_GAP", r["result"])
    t.verdadero("E-24 no nombra al constructor",
                "dev-tool-builder" not in json.dumps(r))
    t.verdadero("E-24 ni pide una tool", "toolClass" not in r and "derivedTo" not in r)


def test_e25_un_hueco_de_capacidad_si_deriva(t):
    """E-25 — CAPABILITY_GAP sigue derivando, y los dos huecos no se mezclan."""
    _, huecos = c_cap.resolver(
        [{"id": "u1", "requiredCapabilities": ["adr.read"]}], {})
    t.igual("E-25 un hueco de capacidad", 1, len(huecos))
    t.igual("E-25 deriva al constructor", "dev-tool-builder", huecos[0]["derivedTo"])
    t.igual("E-25 y la tool nace temporal", "TEMPORARY", huecos[0]["toolClass"])

    # El de skill, en la misma corrida, no produce ninguno.
    skill = c_reg.resolver_ruteo("dev-integration", "dev-miba")
    t.igual("E-25 el de skill es otro", "SPECIALIZED_SKILL_GAP", skill["result"])
    t.verdadero("E-25 y no aparece entre los de capacidad",
                not any(h["capability"] == "dev-miba" for h in huecos))


# -- E-26 a E-29 — la Fase B: plan.py y la unidad de trabajo -------------------

from orquestacion import plan as c_plan                # noqa: E402

_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "a" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "tramites/backoffice"}},
}


def _plan(dominio="integration"):
    unidad = {"id": "u1", "objective": "o", "domain": dominio,
              "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": []}
    return c_plan.armar({"objective": "x", "domains": [dominio], "policies": [],
                         "workUnits": [unidad]}, _CONTEXTO, {}, None)


def test_e26_la_unidad_sale_del_registro(t):
    """E-26 — agente y skills de la unidad salen del registro, no del disco."""
    documento = _plan("backend")
    unidad = documento["workUnits"][0]
    t.igual("E-26 el agente", c_reg.agente_de_dominio("backend"), unidad["assignedAgent"])
    t.igual("E-26 existe segun el registro", True, unidad["agentExists"])
    t.igual("E-26 y dice con que estado", "VALID", unidad["agentValidation"])

    del_registro = sorted(s["id"] for s in c_reg.skills_de("dev-backend"))
    t.igual("E-26 las skills son las declaradas", del_registro, sorted(unidad["skills"]))


def test_e27_la_unidad_lleva_el_estado_de_cada_skill(t):
    """E-27 — skillStates al lado, sin cambiarle el tipo a skills."""
    unidad = _plan("integration")["workUnits"][0]

    # El contrato viejo no cambia: sigue siendo una lista de nombres.
    t.verdadero("E-27 skills sigue siendo una lista de strings",
                all(isinstance(x, str) for x in unidad["skills"]))

    estados = {s["id"]: s for s in unidad["skillStates"]}
    t.igual("E-27 hay un estado por skill", len(unidad["skills"]), len(estados))
    t.igual("E-27 la pendiente se ve pendiente", "DECLARED_NOT_INSTALLED",
            estados["dev-miba"]["status"])
    t.igual("E-27 y con su motivo de hueco", "SPECIALIZED_SKILL_GAP",
            estados["dev-miba"]["validation"])
    t.igual("E-27 la instalada se ve disponible", "SKILL_AVAILABLE",
            estados["dev-openid-connect"]["validation"])
    # Y el agente sigue valido y ruteable con una pendiente adentro.
    t.igual("E-27 el agente sigue valido", "VALID_WITH_PENDING_SKILLS",
            unidad["agentValidation"])
    t.igual("E-27 y existe", True, unidad["agentExists"])


def test_e28_la_matriz_vacia_no_borra_agentes(t):
    """E-28 — con 7.1 sin clasificar, ningun agente declarado y valido deja de existir."""
    from orquestacion import normativa as c_normativa
    documento = _plan("backend")
    sin_clasificar = [r for r in c_normativa.cargar().get("rules", []) if not r.get("owners")]
    t.verdadero("E-28 la matriz sigue sin clasificar", len(sin_clasificar) > 0)
    t.igual("E-28 y el plan no cita estandares", [], documento["applicableStandards"])
    t.igual("E-28 el agente existe igual", True, documento["workUnits"][0]["agentExists"])
    t.verdadero("E-28 ningun agente del plan sale inexistente",
                all(a["exists"] for a in documento["agents"]))


def test_e29_la_compuerta_mira_registro_contra_disco(t):
    """E-29 — el arbol de hoy esta limpio salvo el huerfano reconocido, y una divergencia
    lo pone en rojo: es lo que hace que agregar, borrar o renombrar un .md sin tocar el
    registro se note en la corrida."""
    r = c_reg.reporte()
    t.igual("E-29 el registro es valido", True, r["result"]["registryValid"])
    t.igual("E-29 sin skills sin declarar", 0, r["summary"]["undeclaredSkills"])
    t.igual("E-29 el unico huerfano es el reconocido", 1, r["summary"]["orphanAgents"])
    t.igual("E-29 y por eso el disco no esta limpio", False, r["result"]["filesystemClean"])
    t.verdadero("E-29 ningun agente ni skill en error",
                not any(a["severity"] == "ERROR" for a in r["agents"])
                and not any(s["severity"] == "ERROR" for s in r["skills"]))

    # Una divergencia: un .md declarado que se renombro sin avisarle al registro.
    doc = _doc()
    _agente(doc, "dev-quality")["agentFile"] = "agents/dev-quality-renombrado.md"
    roto = c_reg.reporte(doc)
    t.igual("E-29 el registro deja de ser valido", False, roto["result"]["registryValid"])
    t.igual("E-29 y dice cual", "AGENT_FILE_MISSING",
            [a["state"] for a in roto["agents"] if a["id"] == "dev-quality"][0])
