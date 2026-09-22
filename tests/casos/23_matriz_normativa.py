# La matriz normativa de ES0901 §7.1: que regla aplica y que todavia no se sabe.
#
# Escenarios E-01 a E-24 de docs/cambios/matriz-normativa/spec.md. Entre parentesis, el N-nn
# del pedido que cubre cada uno.
#
# Los casos negativos usan matrices FABRICADAS en memoria. La matriz instalada no se rompe
# para probar que el validador anda.
import copy
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from orquestacion import matriz as c_matriz              # noqa: E402
from orquestacion import normativa as c_normativa        # noqa: E402
from orquestacion import plan as c_plan                  # noqa: E402
from orquestacion import registro_agentes as c_reg       # noqa: E402


# El TaskContext minimo con el que otros casos arman un plan (25_g2, 26_d1...).
_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "a" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


def _doc():
    return copy.deepcopy(c_matriz.cargar())


def _regla(doc, rid):
    for r in doc["rules"]:
        if r["id"] == rid:
            return r
    raise AssertionError("no esta " + rid)


# -- E-01 a E-06 — el contrato de la matriz ------------------------------------

def test_e01_carga_y_valida(t):
    """E-01 (N-01) — valida contra su schema, y el schema entra en el subconjunto."""
    doc = _doc()
    t.vacio("E-01 sin errores de schema", c_matriz.validar_schema(doc))
    estado, errores = c_matriz.validar(doc)
    t.igual("E-01 la matriz es valida", "NORMATIVE_MATRIX_VALID", estado)
    t.vacio("E-01 y no hay errores", errores)


def test_e02_veinticuatro_reglas_sin_repetir(t):
    """E-02 (N-02) — exactamente 24, ningun id repetido."""
    ids = [r["id"] for r in _doc()["rules"]]
    t.igual("E-02 son 24", 24, len(ids))
    t.igual("E-02 y ninguno repetido", 24, len(set(ids)))


def test_e03_el_inventario_exacto(t):
    """E-03 (N-03) — G1..M3, ni una de mas ni una renombrada."""
    ids = sorted(r["id"] for r in _doc()["rules"])
    t.igual("E-03 el inventario", sorted(c_matriz.INVENTARIO), ids)
    for esperado in ("G1", "G2", "D1", "D8", "P1", "P7", "C1", "C4", "M1", "M3"):
        t.verdadero("E-03 esta %s" % esperado, esperado in ids)

    # Y el inventario lo comprueba el VALIDADOR, no solo este test: una matriz a la que le
    # falta una regla no se usa, y el error dice cual falta en vez de cuantas hay.
    doc = _doc()
    doc["rules"] = [r for r in doc["rules"] if r["id"] != "C3"]
    estado, errores = c_matriz.validar(doc)
    t.igual("E-03 sin una regla no vale", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-03 y dice cual falta", "C3", " ".join(errores))

    # Una regla que no es de 7.1 tampoco entra de contrabando.
    doc = _doc()
    doc["rules"].append(dict(doc["rules"][0], id="G9"))
    estado, errores = c_matriz.validar(doc)
    t.igual("E-03 una ajena no vale", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-03 y la nombra", "G9", " ".join(errores))


def test_e04_una_regla_duplicada_invalida_la_matriz(t):
    """E-04 (N-09) — NORMATIVE_MATRIX_INVALID, y nombra el id repetido."""
    doc = _doc()
    doc["rules"].append(copy.deepcopy(_regla(doc, "G1")))
    estado, errores = c_matriz.validar(doc)
    t.igual("E-04 el estado", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-04 nombra la repetida", "G1", " ".join(errores))


def test_e05_otra_version_del_estandar(t):
    """E-05 — NORMATIVE_STANDARD_VERSION_MISMATCH, y no se carga."""
    doc = _doc()
    doc["standard"]["version"] = "7.0"
    estado, errores = c_matriz.validar(doc)
    t.igual("E-05 el estado", "NORMATIVE_STANDARD_VERSION_MISMATCH", estado)
    t.contiene("E-05 dice que esperaba", "6.3", " ".join(errores))
    t.verdadero("E-05 y lo que encontro", "7.0" in " ".join(errores))


def test_e06_una_regla_que_no_existe(t):
    """E-06 — NORMATIVE_RULE_NOT_FOUND."""
    levanto = ""
    try:
        c_matriz.regla("Z9")
    except c_matriz.MatrizInvalida as e:
        levanto = str(e)
    t.contiene("E-06 el estado", "NORMATIVE_RULE_NOT_FOUND", levanto)


# -- E-07 a E-13 — la aplicabilidad --------------------------------------------

def test_e07_always_aplica_sin_senales(t):
    """E-07 (N-04) — una ALWAYS resuelve APPLICABLE sin que haga falta ninguna senal."""
    doc = _doc()
    estado, faltan = c_matriz.resolver_regla(_regla(doc, "G1"), {})
    t.igual("E-07 el estado", "APPLICABLE", estado)
    t.vacio("E-07 no pide ninguna senal", faltan)


def test_e08_condicional_con_senal_verdadera(t):
    """E-08 (N-05) — APPLICABLE."""
    doc = _doc()
    estado, _ = c_matriz.resolver_regla(_regla(doc, "D1"), {"citizenFacing": True})
    t.igual("E-08 el estado", "APPLICABLE", estado)


def test_e09_condicional_con_senal_falsa(t):
    """E-09 (N-06) — NOT_APPLICABLE."""
    doc = _doc()
    estado, _ = c_matriz.resolver_regla(_regla(doc, "D1"), {"citizenFacing": False})
    t.igual("E-09 el estado", "NOT_APPLICABLE", estado)


def test_e10_condicional_sin_la_senal(t):
    """E-10 (N-07) — APPLICABILITY_UNRESOLVED, y dice que senal falta."""
    doc = _doc()
    estado, faltan = c_matriz.resolver_regla(_regla(doc, "D1"), {})
    t.igual("E-10 el estado", "APPLICABILITY_UNRESOLVED", estado)
    t.igual("E-10 y nombra la senal", ["citizenFacing"], faltan)


def test_e11_lo_desconocido_nunca_es_falso(t):
    """E-11 (N-08) — con el contexto vacio, ninguna condicional cae a NOT_APPLICABLE."""
    doc = _doc()
    r = c_matriz.resolver({}, doc)
    condicionales = [x["id"] for x in doc["rules"]
                     if x["applicability"]["mode"] == "CONDITIONAL"]
    t.verdadero("E-11 hay condicionales", len(condicionales) > 0)
    t.vacio("E-11 ninguna dice que no aplica", r["notApplicableRules"])
    t.igual("E-11 todas quedan sin resolver", len(condicionales), len(r["unresolvedRules"]))
    # Y un valor que no es booleano tampoco alcanza para decidir.
    estado, _ = c_matriz.resolver_regla(_regla(doc, "D1"), {"citizenFacing": "si"})
    t.igual("E-11 un string no decide", "APPLICABILITY_UNRESOLVED", estado)


def test_e12_dos_senales_sin_modo_de_combinacion(t):
    """E-12 — hoy ninguna tiene dos; si apareciera, no se inventa un AND ni un OR."""
    doc = _doc()
    multi = [r["id"] for r in doc["rules"]
             if len(r["applicability"].get("signals") or []) > 1]
    t.vacio("E-12 hoy ninguna declara dos senales", multi)

    # "El cargador lo afirma": lo dice el VALIDADOR, no el conteo de arriba. Una matriz
    # fabricada en memoria con D1 en dos senales y sin `combination` no se usa, y el error
    # nombra la regla.
    doble = _doc()
    _regla(doble, "D1")["applicability"]["signals"] = ["citizenFacing", "frontendPresent"]
    estado, errores = c_matriz.validar(doble)
    t.igual("E-12 el validador la rechaza", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-12 y nombra la regla", "D1 declara 2 senales", " ".join(errores))
    t.contiene("E-12 y dice que falta", "combination", " ".join(errores))
    _regla(doble, "D1")["applicability"]["combination"] = "ANY"
    estado, errores = c_matriz.validar(doble)
    t.igual("E-12 con combination declarada el validador la acepta",
            "NORMATIVE_MATRIX_VALID", estado)
    t.vacio("E-12 y sin errores", errores)

    r = _regla(doc, "D1")
    r["applicability"]["signals"] = ["citizenFacing", "frontendPresent"]
    estado, faltan = c_matriz.resolver_regla(r, {"citizenFacing": True,
                                                 "frontendPresent": True})
    t.igual("E-12 el estado", "APPLICABILITY_EXPRESSION_UNRESOLVED", estado)
    t.igual("E-12 y dice cuales son", ["citizenFacing", "frontendPresent"], faltan)

    # Con el modo declarado si se resuelve: lo que falta es la declaracion, no el dato.
    r["applicability"]["combination"] = "ALL"
    estado, _ = c_matriz.resolver_regla(r, {"citizenFacing": True, "frontendPresent": True})
    t.igual("E-12 con combination declarada resuelve", "APPLICABLE", estado)


def test_e13_d8_en_sus_tres_estados(t):
    """E-13 (N-14, N-15, N-16) — el mismo id, tres respuestas segun la senal."""
    doc = _doc()
    d8 = _regla(doc, "D8")
    t.igual("E-13 la senal de D8", ["serviceEndpointPresent"], d8["applicability"]["signals"])
    t.igual("E-13 con endpoint", "APPLICABLE",
            c_matriz.resolver_regla(d8, {"serviceEndpointPresent": True})[0])
    t.igual("E-13 sin endpoint", "NOT_APPLICABLE",
            c_matriz.resolver_regla(d8, {"serviceEndpointPresent": False})[0])
    t.igual("E-13 sin saber", "APPLICABILITY_UNRESOLVED",
            c_matriz.resolver_regla(d8, {})[0])


# -- E-14 a E-16 — las referencias ---------------------------------------------

def test_e14_un_agente_que_el_registro_no_declara(t):
    """E-14 (N-10) — NORMATIVE_AGENT_REFERENCE_INVALID, y no se crea nada."""
    doc = _doc()
    _regla(doc, "G1")["primaryAgents"] = ["dev-inventado"]
    estado, errores = c_matriz.validar(doc)
    t.igual("E-14 la matriz no vale", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-14 el estado", "NORMATIVE_AGENT_REFERENCE_INVALID", " ".join(errores))
    t.igual("E-14 y el agente sigue sin existir", False, c_reg.hay_agente("dev-inventado"))


def test_e15_una_skill_desconocida_y_una_pendiente(t):
    """E-15 (N-17) — la desconocida invalida; la pendiente es valida y sigue pendiente."""
    doc = _doc()
    _regla(doc, "G1")["skills"] = ["dev-que-no-existe"]
    estado, errores = c_matriz.validar(doc)
    t.igual("E-15 no vale", "NORMATIVE_MATRIX_INVALID", estado)
    t.contiene("E-15 el estado", "NORMATIVE_SKILL_REFERENCE_INVALID", " ".join(errores))

    doc = _doc()
    _regla(doc, "G1")["skills"] = ["dev-miba"]
    estado, _ = c_matriz.validar(doc)
    t.igual("E-15 una pendiente es referencia valida", "NORMATIVE_MATRIX_VALID", estado)
    declarada = c_reg.skill("dev-integration", "dev-miba")
    t.igual("E-15 y sigue pendiente despues", "DECLARED_NOT_INSTALLED", declarada["status"])


def test_e16_resolver_no_toca_el_registro(t):
    """E-16 (N-11) — mismos validos y mismas pendientes antes y despues."""
    antes = c_reg.reporte()["summary"]
    c_matriz.resolver({"citizenFacing": True, "databasePresent": True})
    despues = c_reg.reporte()["summary"]
    t.igual("E-16 los agentes validos", antes["validAgents"], despues["validAgents"])
    t.igual("E-16 las skills instaladas", antes["installedSkills"], despues["installedSkills"])
    t.igual("E-16 y las pendientes", antes["pendingSkills"], despues["pendingSkills"])


# -- E-17 a E-19 — policies y checks -------------------------------------------

def test_e17_g1_resuelve_sus_controles(t):
    """E-17 (N-12) — G1 declara sus dos policies y sus dos checks."""
    r = c_matriz.resolver({})
    t.verdadero("E-17 G1 aplica siempre", "G1" in r["applicableRules"])
    for pid in ("approved-technology-required", "homologated-version-required"):
        t.verdadero("E-17 declara %s" % pid, pid in r["declaredPolicies"])
    for cid in ("technology-homologation", "technology-version-compliance"):
        t.verdadero("E-17 declara %s" % cid, cid in r["declaredChecks"])


def test_e18_una_regla_con_varios_controles(t):
    """E-18 (N-13) — D7 resuelve varias policies y varios checks de una sola regla."""
    doc = _doc()
    d7 = _regla(doc, "D7")
    t.verdadero("E-18 D7 declara mas de una policy", len(d7["policies"]) > 1)
    senal = d7["applicability"]["signals"][0]
    r = c_matriz.resolver({senal: True}, doc)
    t.verdadero("E-18 aplica", "D7" in r["applicableRules"])
    for pid in d7["policies"]:
        t.verdadero("E-18 esta %s" % pid, pid in r["declaredPolicies"])
    for cid in d7["checks"]:
        t.verdadero("E-18 esta %s" % cid, cid in r["declaredChecks"])


def test_e19_los_ids_no_fingen_estar_implementados(t):
    """E-19 (N-18) — se reportan como no instalados, y eso no invalida la matriz."""
    r = c_matriz.resolver({})
    t.verdadero("E-19 hay controles declarados", len(r["declaredPolicies"]) > 0)

    # Con NADA instalado faltan todos. Se pasan las listas a mano a proposito: el escenario
    # es sobre la regla, no sobre cuantos controles haya instalados hoy — y hoy G1 ya instalo
    # los suyos, que es justamente lo que E-22 de g1-tecnologias-homologadas afirma.
    faltantes = c_matriz.controles_no_instalados(r, policies_instaladas=[],
                                                 checks_instalados=[])
    t.igual("E-19 con nada instalado faltan todos",
            len(r["declaredPolicies"]) + len(r["declaredChecks"]), len(faltantes))
    estados = {f["state"] for f in faltantes}
    t.verdadero("E-19 el estado de una policy",
                "DECLARED_POLICY_NOT_INSTALLED" in estados)
    t.verdadero("E-19 el de un check", "DECLARED_CHECK_NOT_INSTALLED" in estados)
    t.igual("E-19 la matriz sigue siendo valida", "NORMATIVE_MATRIX_VALID",
            c_matriz.validar(_doc())[0])

    # Y el dia que uno se instale, sale de la lista sin tocar la matriz.
    con_uno = c_matriz.controles_no_instalados(
        r, policies_instaladas=["approved-technology-required"], checks_instalados=[])
    t.igual("E-19 uno menos", len(faltantes) - 1, len(con_uno))
    t.verdadero("E-19 y es el que se instalo",
                "approved-technology-required" not in {f["id"] for f in con_uno})


# -- E-20 a E-22 — la union con el texto citado --------------------------------

def test_e20_cada_fila_tiene_su_cita(t):
    """E-20 — las 24 filas tienen cita, y ninguna cita quedo sin fila."""
    citables = c_normativa.reglas()
    sufijos = [r["id"].split("-")[-1] for r in citables]
    de_la_matriz = {r["id"] for r in _doc()["rules"]}

    sin_cita = [rid for rid in de_la_matriz if rid not in sufijos]
    t.vacio("E-20 ninguna fila sin cita", sin_cita)

    # Las citables que no son fila son las derivadas, y heredan.
    sin_fila = [s for s in sufijos if s not in de_la_matriz]
    t.igual("E-20 las unicas sin fila son las derivadas", ["P1.node", "P1.plataformas"],
            sorted(sin_fila))
    t.verdadero("E-20 y todas las derivadas tienen madre",
                all("." in s for s in sin_fila))


def test_e21_las_clausulas_derivadas_heredan(t):
    """E-21 — P1.node y P1.plataformas toman la clasificacion de P1, declarada."""
    madre = c_matriz.regla("P1")
    for derivada in ("P1.node", "P1.plataformas"):
        r = c_matriz.regla(derivada)
        t.igual("E-21 %s hereda de P1" % derivada, "P1", r["inheritedFrom"])
        t.igual("E-21 %s mismas policies" % derivada, madre["policies"], r["policies"])
        t.igual("E-21 %s mismos agentes" % derivada, madre["primaryAgents"],
                r["primaryAgents"])
        t.igual("E-21 %s conserva su propio id" % derivada, derivada, r["id"])

    # Una derivada cuya madre no esta no hereda nada: levanta.
    levanto = ""
    try:
        c_matriz.regla("Z9.algo")
    except c_matriz.MatrizInvalida as e:
        levanto = str(e)
    t.contiene("E-21 sin madre no hereda", "NORMATIVE_RULE_NOT_FOUND", levanto)


def test_e22_la_cita_no_sale_de_la_matriz(t):
    """E-22 — el texto sigue viniendo del archivo citable, en espanol."""
    citable = [r for r in c_normativa.reglas() if r["id"].endswith("-G1")][0]
    t.verdadero("E-22 la cita tiene texto", bool(citable.get("text")))
    t.verdadero("E-22 y pagina", bool(citable.get("page")))

    de_la_matriz = c_matriz.regla("G1")
    t.verdadero("E-22 la matriz no trae el texto", "text" not in de_la_matriz)
    t.verdadero("E-22 trae una parafrasis aparte",
                bool(de_la_matriz.get("operationalIntentEn")))
    t.verdadero("E-22 y no es la cita",
                de_la_matriz.get("operationalIntentEn") != citable.get("text"))


# -- E-23 y E-24 — compatibilidad y determinismo -------------------------------

def test_e23_applicable_standards_no_cambio(t):
    """E-23 (N-19) — lo que ya se consumia sigue igual, y normative entra al lado."""
    t.igual("E-23 sigue siendo una lista", list, type(c_normativa.aplicables(["backend"])))
    t.igual("E-23 y contesta lo mismo que antes", [], c_normativa.aplicables(["backend"]))
    t.verdadero("E-23 el aviso de matriz sigue existiendo",
                bool(c_normativa.aviso_de_matriz()))

    bloque = c_normativa.resolucion({})
    for campo in ("standard", "applicableRules", "notApplicableRules", "unresolvedRules",
                  "declaredPolicies", "declaredChecks"):
        t.verdadero("E-23 el bloque trae %s" % campo, campo in bloque)

    # Y en un plan de verdad, armado por el mismo punto de entrada que usa la orquestacion.
    # `applicableStandards` queda en la raiz con su forma de antes -una lista de ids, la que
    # contesta `aplicables` para los dominios del plan-; `normative` va en CADA unidad.
    unidades = [
        {"id": "u1", "objective": "o", "domain": "backend",
         "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": []},
        {"id": "u2", "objective": "o", "domain": "frontend",
         "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": [],
         "normativeSignals": {"citizenFacing": True}},
    ]
    documento = c_plan.armar({"objective": "x", "domains": ["backend", "frontend"],
                              "policies": [], "workUnits": unidades}, _CONTEXTO, {}, None)
    t.vacio("E-23 el plan valida", c_plan.validar(documento))
    t.igual("E-23 applicableStandards sigue siendo una lista", list,
            type(documento["applicableStandards"]))
    t.igual("E-23 y dice lo mismo que antes",
            c_normativa.aplicables(["backend", "frontend"]), documento["applicableStandards"])
    t.igual("E-23 que hoy es vacia", [], documento["applicableStandards"])
    t.verdadero("E-23 normative no desplaza a nadie en la raiz", "normative" not in documento)
    t.igual("E-23 hay dos unidades", 2, len(documento["workUnits"]))
    for unidad in documento["workUnits"]:
        t.verdadero("E-23 %s trae normative" % unidad["id"], "normative" in unidad)
        n = unidad.get("normative") or {}
        t.igual("E-23 %s con su traza" % unidad["id"], "ES0901", (n.get("standard") or {}).get("id"))
    por_id = {u["id"]: u["normative"] for u in documento["workUnits"]}
    t.verdadero("E-23 y cada unidad resuelve con sus senales",
                "D1" in por_id["u2"]["applicableRules"]
                and "D1" not in por_id["u1"]["applicableRules"])


def test_e24_misma_entrada_mismo_resultado(t):
    """E-24 (N-20) — determinista: ningun modelo participa."""
    senales = {"serviceEndpointPresent": True, "citizenFacing": False,
               "databasePresent": True}
    uno = c_matriz.resolver(senales)
    dos = c_matriz.resolver(dict(senales))
    t.igual("E-24 mismas aplicables", uno["applicableRules"], dos["applicableRules"])
    t.igual("E-24 mismas no aplicables", uno["notApplicableRules"], dos["notApplicableRules"])
    t.igual("E-24 mismas sin resolver", uno["unresolvedRules"], dos["unresolvedRules"])
    t.igual("E-24 mismos controles", uno["declaredPolicies"], dos["declaredPolicies"])
    t.igual("E-24 y la evidencia dice con que senales", senales, uno["evidence"]["signals"])
