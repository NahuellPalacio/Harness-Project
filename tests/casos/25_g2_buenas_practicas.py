# G2: buenas practicas reconocidas, revisadas con criterio y con evidencia.
#
# Escenarios E-01 a E-24 de docs/cambios/g2-buenas-practicas/spec.md. Entre parentesis, el
# G2-nn del pedido.
#
# Nada de esto evalua criterio tecnico: se comprueba que la ESTRUCTURA de una revision sea
# valida y que el resultado se derive de sus hallazgos. Que una practica sea efectivamente
# una buena practica de Angular es juicio, y ningun test lo puede contradecir.
import copy
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"

sys.path.insert(0, str(BIN))
from orquestacion import controles as c_controles      # noqa: E402
from orquestacion import matriz as c_matriz            # noqa: E402
from orquestacion import plan as c_plan                # noqa: E402
from orquestacion import revisiones as c_rev           # noqa: E402


def _check_g1(nombre):
    ruta = CONTROLES / "checks" / (nombre + ".py")
    spec = importlib.util.spec_from_file_location("g2_" + nombre.replace("-", "_"), ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "G2"}


def _revision(evidencia=None, hallazgos=None, **extra):
    """Una revision bien formada. Los casos la deforman de a una cosa por vez."""
    r = {
        "reviewId": "rev-001",
        "controlType": "REVIEW",
        "source": dict(TRAZA),
        "subject": {"type": "technology", "id": "angular", "version": "19.2.18"},
        "evidence": evidencia if evidencia is not None else [_evidencia()],
        "findings": hallazgos if hallazgos is not None else [_hallazgo()],
        "result": "COMPLIANT",
        "reviewer": {"ownerAgent": "dev-architecture", "supportingAgents": ["dev-frontend"],
                     "reviewMode": "AGENT_REVIEW"},
    }
    r.update(extra)
    return r


def _evidencia(eid="ev-1", tipo="OFFICIAL_TECHNOLOGY_DOCUMENTATION",
               claim="la guia oficial exige X", **extra):
    e = {"evidenceId": eid, "sourceType": tipo,
         "reference": "https://angular.dev/style-guide", "versionOrDate": "2026-01",
         "claim": claim}
    e.update(extra)
    return e


def _hallazgo(fid="f-1", estado="ADOPTED", fuerza="REQUIRED_BY_SOURCE",
              aplicabilidad="APPLICABLE", refs=("ev-1",), **extra):
    h = {"findingId": fid, "practice": "usar X", "applicability": aplicabilidad,
         "practiceStrength": fuerza, "status": estado, "evidenceRefs": list(refs),
         "rationale": "la guia oficial lo exige y el proyecto lo implementa"}
    h.update(extra)
    return h


# -- E-01 a E-04 — la regla y su tipo de control -------------------------------

def test_e01_g2_aplica_siempre(t):
    """E-01 (G2-01) — ALWAYS, sin ninguna senal."""
    g2 = c_matriz.regla("G2")
    t.igual("E-01 el modo", "ALWAYS", g2["applicability"]["mode"])
    t.vacio("E-01 sin senales", g2["applicability"]["signals"])
    t.verdadero("E-01 aplica con el contexto vacio",
                "G2" in c_matriz.resolver({})["applicableRules"])


def test_e02_una_policy_cero_checks_una_review(t):
    """E-02 (G2-02) — y los ceros son a proposito."""
    g2 = c_matriz.regla("G2")
    t.igual("E-02 una policy", ["industry-good-practices-required"], g2["policies"])
    t.igual("E-02 cero checks", [], g2["checks"])
    t.igual("E-02 una review", ["technology-practice-review"], g2.get("reviews"))


def test_e03_no_se_fabrico_un_check_para_simetria(t):
    """E-03 (G2-03) — la review se instala y ningun check de G2 aparece."""
    de_g2 = c_controles.de_la_regla("G2")
    t.igual("E-03 dos controles", 2, len(de_g2))
    t.igual("E-03 ningun CHECK", 0, len([c for c in de_g2 if c["type"] == "CHECK"]))
    t.igual("E-03 una POLICY", 1, len([c for c in de_g2 if c["type"] == "POLICY"]))
    t.igual("E-03 una REVIEW", 1, len([c for c in de_g2 if c["type"] == "REVIEW"]))
    t.verdadero("E-03 la review esta instalada",
                "technology-practice-review" in c_controles.instalados()["REVIEW"])


def test_e04_review_es_un_tipo_y_reviews_es_opcional(t):
    """E-04 (G2-20) — el registro lo conoce, y una fila sin reviews sigue valida."""
    doc = c_controles.cargar()
    t.verdadero("E-04 el registro conoce REVIEW", "REVIEW" in doc["controlTypes"])
    t.vacio("E-04 y el registro valida", c_controles.validar_schema(doc))

    matriz_doc = c_matriz.cargar()
    con_reviews = [r["id"] for r in matriz_doc["rules"] if "reviews" in r]
    sin_reviews = [r["id"] for r in matriz_doc["rules"] if "reviews" not in r]
    # El campo es opcional y lo prueba la mayoria que no lo trae, no un numero fijo: el
    # conteo bajaba de 23 a 22 el dia que D3 declaro su review, y lo que el escenario
    # afirma no cambio. Un test que se rompe porque otra regla se construyo estaba
    # midiendo el calendario, no la opcionalidad.
    t.verdadero("E-04 casi ninguna fila lo trae", len(sin_reviews) > len(con_reviews))
    t.verdadero("E-04 las dos listas cubren la matriz entera",
                len(sin_reviews) + len(con_reviews) == len(matriz_doc["rules"]))
    t.verdadero("E-04 G2 si lo trae", "G2" in con_reviews)
    t.igual("E-04 y la matriz sigue valida", "NORMATIVE_MATRIX_VALID",
            c_matriz.validar(matriz_doc)[0])


# -- E-05 a E-09 — el contrato de la evidencia ---------------------------------

def test_e05_el_schema_de_revision(t):
    """E-05 (G2-04) — valida, y entra en el subconjunto soportado."""
    t.vacio("E-05 una revision bien formada valida", c_rev.validar_schema(_revision()))
    rota = _revision()
    rota["result"] = "MAS_O_MENOS"
    t.verdadero("E-05 un resultado inventado no valida", len(c_rev.validar_schema(rota)) > 0)
    del rota["reviewer"]
    t.verdadero("E-05 sin revisor tampoco", len(c_rev.validar_schema(rota)) > 0)


def test_e06_la_opinion_del_agente_no_alcanza(t):
    """E-06 (G2-05) — sin fuente reconocida no se llega a COMPLIANT."""
    r = _revision(evidencia=[_evidencia(tipo="PROJECT_IMPLEMENTATION",
                                        claim="lo hacemos asi")])
    salida = c_rev.resolver(r)
    t.verdadero("E-06 no cumple", salida["result"] != "COMPLIANT")
    t.igual("E-06 esta incompleta", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-06 y dice por que",
                any("fuente reconocida" in i for i in salida["issues"]))


def test_e07_la_documentacion_oficial_si_alcanza(t):
    """E-07 (G2-06) — es fuente reconocida."""
    salida = c_rev.resolver(_revision())
    t.igual("E-07 cumple", "COMPLIANT", salida["result"])
    t.verdadero("E-07 la clase esta entre las reconocidas",
                "OFFICIAL_TECHNOLOGY_DOCUMENTATION" in c_rev.FUENTES_RECONOCIDAS)


def test_e08_la_convencion_del_proyecto_no_prueba_reconocimiento(t):
    """E-08 (G2-07) — que el proyecto lo haga no lo vuelve practica de la industria."""
    t.verdadero("E-08 no esta entre las reconocidas",
                "PROJECT_CONVENTION" not in c_rev.FUENTES_RECONOCIDAS)
    r = _revision(evidencia=[_evidencia(tipo="PROJECT_CONVENTION",
                                        claim="en este proyecto se hace asi")])
    salida = c_rev.resolver(r)
    t.igual("E-08 no cumple", "REVIEW_INCOMPLETE", salida["result"])


def test_e09_un_hallazgo_que_referencia_evidencia_que_no_existe(t):
    """E-09 — estructuralmente invalido."""
    r = _revision(hallazgos=[_hallazgo(refs=("ev-99",))])
    problemas = c_rev.validar_estructura(r)
    t.verdadero("E-09 hay problema", len(problemas) > 0)
    t.verdadero("E-09 y nombra la evidencia fantasma",
                any("ev-99" in p for p in problemas))
    t.igual("E-09 la revision no cumple", "REVIEW_INCOMPLETE", c_rev.resolver(r)["result"])


# -- E-10 a E-13 — aplicabilidad y fuerza --------------------------------------

def test_e10_aplicabilidad_sin_resolver(t):
    """E-10 (G2-10) — UNRESOLVED, nunca NOT_APPLICABLE."""
    r = _revision(hallazgos=[_hallazgo(aplicabilidad="UNRESOLVED")])
    salida = c_rev.resolver(r)
    t.igual("E-10 la revision queda incompleta", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-10 y lo dice", "REVIEW_SOURCE_UNRESOLVED" in salida["states"])
    t.verdadero("E-10 UNRESOLVED es un valor del contrato",
                "UNRESOLVED" in c_rev.APLICABILIDAD)


def test_e11_no_aplicable_exige_motivo(t):
    """E-11 (G2-09) — sin motivo es indistinguible de una que nadie miro."""
    h = _hallazgo(aplicabilidad="NOT_APPLICABLE", estado="NOT_APPLICABLE")
    h["rationale"] = ""
    problemas = c_rev.validar_estructura(_revision(hallazgos=[h]))
    t.verdadero("E-11 da problema", any("no dice por que" in p for p in problemas))

    h["rationale"] = "el proyecto no usa esa capacidad de la libreria"
    t.vacio("E-11 con motivo pasa", c_rev.validar_estructura(_revision(hallazgos=[h])))


def test_e12_la_modalidad_de_la_fuente_se_conserva(t):
    """E-12 (G2-11) — lo recomendado no se exige y lo exigido no se rebaja."""
    exigida = _revision(hallazgos=[_hallazgo(estado="DEVIATION",
                                             fuerza="REQUIRED_BY_SOURCE")])
    recomendada = _revision(hallazgos=[_hallazgo(estado="DEVIATION",
                                                 fuerza="RECOMMENDED_BY_SOURCE")])
    t.igual("E-12 apartarse de lo exigido no cumple", "NON_COMPLIANT",
            c_rev.resolver(exigida)["result"])
    t.igual("E-12 apartarse de lo recomendado observa", "COMPLIANT_WITH_OBSERVATIONS",
            c_rev.resolver(recomendada)["result"])
    t.verdadero("E-12 y los dos son resultados distintos",
                c_rev.resolver(exigida)["result"] != c_rev.resolver(recomendada)["result"])


def test_e13_falta_el_contexto_de_version(t):
    """E-13 (G2-08) — REVIEW_INCOMPLETE cuando la guia depende de la version y no hay version.

    Cada mitad se arma sola, con el resto de la revision en COMPLIANT: si el resultado cambia,
    lo cambio la combinacion `versionDependent` + sujeto sin version y nada mas.
    """
    estado = "REVIEW_VERSION_CONTEXT_MISSING"

    def sin_version(r, como):
        if como == "ausente":
            del r["subject"]["version"]
        else:
            r["subject"]["version"] = como
        return r

    # Depende de la version y el sujeto no la trae: incompleta, con su motivo nombrado.
    for como in (None, "", "ausente"):
        r = sin_version(_revision(hallazgos=[_hallazgo(versionDependent=True)]), como)
        salida = c_rev.resolver(r)
        t.igual("E-13 dependiente y version %r: incompleta" % (como,), "REVIEW_INCOMPLETE",
                salida["result"])
        t.verdadero("E-13 dependiente y version %r: el estado lo nombra" % (como,),
                    estado in salida["states"])
        t.verdadero("E-13 dependiente y version %r: el motivo nombra el hallazgo" % (como,),
                    any(i.startswith("f-1:") and "version" in i for i in salida["issues"]))

    # Tampoco se puede decir que no aplica sin saber la version.
    r = sin_version(_revision(hallazgos=[_hallazgo(
        versionDependent=True, aplicabilidad="NOT_APPLICABLE", estado="NOT_APPLICABLE")]), None)
    t.igual("E-13 dependiente, sin version, 'no aplica' tampoco cierra", "REVIEW_INCOMPLETE",
            c_rev.resolver(r)["result"])

    # Depende de la version y el sujeto la trae: ese motivo no aparece.
    salida = c_rev.resolver(_revision(hallazgos=[_hallazgo(versionDependent=True)]))
    t.igual("E-13 dependiente con version: cumple", "COMPLIANT", salida["result"])
    t.verdadero("E-13 dependiente con version: sin el estado", estado not in salida["states"])

    # No depende de la version y el sujeto no la trae: tampoco.
    for declarado in ({}, {"versionDependent": False}):
        r = sin_version(_revision(hallazgos=[_hallazgo(**declarado)]), None)
        salida = c_rev.resolver(r)
        t.igual("E-13 no dependiente %s sin version: cumple" % (declarado,), "COMPLIANT",
                salida["result"])
        t.verdadero("E-13 no dependiente %s sin version: sin el estado" % (declarado,),
                    estado not in salida["states"])

    # La mitad de la tecnologia: un sujeto sin `id` no dice sobre que tecnologia es, y eso lo
    # frenan DOS guardas distintas —el `required` del schema y el control de
    # validar_estructura—. Cada una se afirma por su mensaje, asi que sacar cualquiera de las
    # dos por separado pone esto en rojo: la otra seguiria dando incompleta y taparia el hueco.
    for como in ("ausente", None, ""):
        r = _revision()
        if como == "ausente":
            del r["subject"]["id"]
        else:
            r["subject"]["id"] = como
        salida = c_rev.resolver(r)
        t.igual("E-13 tecnologia %r: incompleta" % (como,), "REVIEW_INCOMPLETE",
                salida["result"])
        t.verdadero("E-13 tecnologia %r: schema invalido" % (como,),
                    "REVIEW_SCHEMA_INVALID" in salida["states"])
        t.verdadero("E-13 tecnologia %r: la estructura dice que falta el sujeto" % (como,),
                    "REVIEW_SCHEMA_INVALID: la revision no dice sobre que es" in salida["issues"])
    r = _revision()
    del r["subject"]["id"]
    t.verdadero("E-13 tecnologia ausente: el schema la exige",
                "$.subject.id: falta y es obligatorio" in c_rev.resolver(r)["issues"])

    # Y el campo es del contrato: booleano, opcional.
    t.vacio("E-13 versionDependent valida en el schema",
            c_rev.validar_schema(_revision(hallazgos=[_hallazgo(versionDependent=True)])))
    t.verdadero("E-13 versionDependent no booleano no valida",
                len(c_rev.validar_schema(_revision(
                    hallazgos=[_hallazgo(versionDependent="si")]))) > 0)


# -- E-14 a E-18 — el resultado ------------------------------------------------

def test_e14_apartarse_de_lo_exigido(t):
    """E-14 (G2-12) — NON_COMPLIANT sin resolucion autoritativa."""
    salida = c_rev.resolver(_revision(hallazgos=[_hallazgo(estado="DEVIATION")]))
    t.igual("E-14 el resultado", "NON_COMPLIANT", salida["result"])


def test_e15_apartarse_de_una_recomendacion(t):
    """E-15 (G2-13) — COMPLIANT_WITH_OBSERVATIONS con la evidencia completa."""
    salida = c_rev.resolver(_revision(hallazgos=[
        _hallazgo(fid="f-1", estado="ADOPTED"),
        _hallazgo(fid="f-2", estado="DEVIATION", fuerza="RECOMMENDED_BY_SOURCE")]))
    t.igual("E-15 el resultado", "COMPLIANT_WITH_OBSERVATIONS", salida["result"])


def test_e16_falta_evidencia_material(t):
    """E-16 (G2-14) — REVIEW_INCOMPLETE, y nunca COMPLIANT."""
    salida = c_rev.resolver(_revision(hallazgos=[_hallazgo(estado="EVIDENCE_MISSING")]))
    t.igual("E-16 el resultado", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-16 no cumple", salida["result"] != "COMPLIANT")
    t.vacio("E-16 sin hallazgos tampoco cumple",
            [x for x in [c_rev.resolver(_revision(hallazgos=[]))["result"]]
             if x == "COMPLIANT"])


def test_e17_una_justificacion_no_aprueba_la_excepcion(t):
    """E-17 (G2-15) — JUSTIFICATION_PENDING, y el resultado no pasa a cumplir."""
    salida = c_rev.resolver(_revision(hallazgos=[
        _hallazgo(estado="JUSTIFICATION_PENDING")]))
    t.verdadero("E-17 el estado aparece", "JUSTIFICATION_PENDING" in salida["states"])
    t.igual("E-17 y no cumple", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-17 lo dice", any("aprobo" in i for i in salida["issues"]))


def test_e18_dos_fuentes_que_se_contradicen(t):
    """E-18 (G2-16) — SOURCE_CONFLICT, con las dos conservadas."""
    r = _revision(
        evidencia=[_evidencia("ev-1", "OFFICIAL_TECHNOLOGY_DOCUMENTATION", "hay que hacer X"),
                   _evidencia("ev-2", "FORMAL_STANDARD", "hay que hacer lo contrario de X")],
        hallazgos=[_hallazgo(refs=("ev-1", "ev-2"))])
    conflicto = c_rev.conflicto_de_fuentes(r, r["findings"][0])
    t.verdadero("E-18 lo detecta", conflicto is not None)
    t.igual("E-18 el estado", "SOURCE_CONFLICT", conflicto["state"])
    t.igual("E-18 conserva las dos", 2, len(conflicto["sources"]))
    salida = c_rev.resolver(r)
    t.verdadero("E-18 y sale en la resolucion", "SOURCE_CONFLICT" in salida["states"])
    t.verdadero("E-18 no elige la que hace pasar", salida["result"] != "COMPLIANT")


# -- E-19 a E-21 — los limites -------------------------------------------------

def test_e19_g1_no_hace_cumplir_a_g2(t):
    """E-19 (G2-17) — homologada no es bien usada."""
    homologacion = _check_g1("technology-version-compliance")
    g1 = homologacion.evaluar({"technology": "php", "version": "8.2.30"})
    t.igual("E-19 G1 dice homologada", "HOMOLOGATED", g1["state"])
    t.igual("E-19 pero la traza de G1 es G1", "G1", g1["source"]["rule"])

    # Y una revision de G2 sin evidencia sigue sin cumplir, con G1 en verde.
    salida = c_rev.resolver(_revision(hallazgos=[_hallazgo(estado="EVIDENCE_MISSING")]))
    t.igual("E-19 G2 sigue incompleta", "REVIEW_INCOMPLETE", salida["result"])
    t.igual("E-19 y su traza es G2", "G2", salida["source"]["rule"])


# Los archivos de los que un detector de stack saca las tecnologias. Si alguno aparece en
# revisiones.py o en el documento de la review, alguien empezo a escribir el segundo detector.
_MANIFIESTOS = ("package.json", "package-lock.json", "pom.xml", "build.gradle",
                "requirements.txt", "pyproject.toml", "composer.json", "go.mod",
                "Cargo.toml", ".csproj", "Gemfile", "angular.json")

# Lo que lee el sistema de archivos. Una revision no tiene por que leer nada mas que su schema.
_LECTURAS = ("open", "walk", "listdir", "scandir", "glob", "iglob", "rglob", "read_text",
             "read_bytes", "exists", "isfile", "isdir")


def test_e20_el_inventario_de_g1_se_reusa(t):
    """E-20 (G2-18) — un solo inventario, no dos detectores.

    No hay todavia un camino de codigo que lleve el inventario de G1 a una revision: nadie
    produce el inventario (ver el riesgo en la spec). Lo que se puede sostener es estructural:
    que la review manda a reusar el de G1, y que ni la review ni revisiones.py detectan nada.
    """
    import ast
    fuente = (BIN / "orquestacion" / "revisiones.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    # 1. revisiones.py no lee el sistema de archivos, salvo su propio schema.
    lecturas = []
    for funcion in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
        for nodo in ast.walk(funcion):
            if isinstance(nodo, ast.Call):
                f = nodo.func
                nombre = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                if nombre in _LECTURAS:
                    lecturas.append((funcion.name, nombre))
    t.igual("E-20 revisiones.py solo abre su schema", [("cargar_schema", "open")], lecturas)

    # 2. Ni nombra un manifiesto de dependencias.
    literales = [n.value for n in ast.walk(arbol)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    t.vacio("E-20 revisiones.py no nombra manifiestos",
            [m for m in _MANIFIESTOS for x in literales if m in x])

    # 3. Ni define algo con forma de detector.
    t.vacio("E-20 revisiones.py no define un detector",
            [n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)
             and any(p in n.name.lower()
                     for p in ("detect", "stack", "inventario", "inventory", "manifiesto"))])

    # 4. El documento de la review manda a reusar el inventario de G1, y no explica como
    #    sacar uno propio.
    doc = (CONTROLES / "reviews" / "technology-practice-review.md").read_text(encoding="utf-8")
    t.contiene("E-20 la review toma el inventario de G1",
               "The technology inventory comes from **G1**", doc)
    t.contiene("E-20 la review prohibe el segundo detector",
               "Do not build a second stack detector", doc)
    t.vacio("E-20 la review no nombra manifiestos", [m for m in _MANIFIESTOS if m in doc])

    # 5. Y en el directorio de reviews no hay codigo: una review no trae su propio detector.
    t.vacio("E-20 las reviews son documentos, no codigo",
            sorted(p.name for p in (CONTROLES / "reviews").iterdir()
                   if p.is_file() and p.suffix != ".md"))


def test_e21_los_agentes_tienen_que_estar_declarados(t):
    """E-21 (G2-19) — uno desconocido invalida, y no se crea."""
    from orquestacion import registro_agentes as c_reg
    r = _revision()
    r["reviewer"]["ownerAgent"] = "dev-inventado"
    problemas = c_rev.validar_agentes(r)
    t.verdadero("E-21 da problema", len(problemas) > 0)
    t.verdadero("E-21 lo nombra", any("dev-inventado" in p for p in problemas))
    t.igual("E-21 y no se creo", False, c_reg.hay_agente("dev-inventado"))

    r = _revision()
    r["reviewer"]["supportingAgents"] = ["dev-frontend", "dev-fantasma"]
    t.verdadero("E-21 los de apoyo tambien se validan",
                any("dev-fantasma" in p for p in c_rev.validar_agentes(r)))

    t.vacio("E-21 los declarados pasan", c_rev.validar_agentes(_revision()))


# -- E-22 a E-24 — la propagacion ----------------------------------------------

_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "a" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


def test_e22_la_unidad_lleva_declared_reviews(t):
    """E-22 (G2-20) — sin romper policies ni checks."""
    unidad = {"id": "u1", "objective": "o", "domain": "backend",
              "requiredCapabilities": ["repository.read"], "dependencies": [], "signals": []}
    documento = c_plan.armar({"objective": "x", "domains": ["backend"], "policies": [],
                              "workUnits": [unidad]}, _CONTEXTO, {}, None)
    n = documento["workUnits"][0]["normative"]
    t.igual("E-22 la review viaja", ["technology-practice-review"], n["declaredReviews"])
    t.verdadero("E-22 las policies siguen", len(n["declaredPolicies"]) > 0)
    t.verdadero("E-22 los checks siguen", len(n["declaredChecks"]) > 0)
    t.verdadero("E-22 y las tres son listas de strings",
                all(isinstance(x, str)
                    for x in n["declaredPolicies"] + n["declaredChecks"] + n["declaredReviews"]))
    t.vacio("E-22 el plan valida", c_plan.validar(documento))


def test_e23_la_review_deja_de_faltar(t):
    """E-23 (G2-21) — desaparece de la lista sin tocar la regla."""
    r = c_matriz.resolver({})
    t.verdadero("E-23 G2 la declara", "technology-practice-review" in r["declaredReviews"])

    sin_nada = c_matriz.controles_no_instalados(r, policies_instaladas=[],
                                                checks_instalados=[], reviews_instaladas=[])
    estados = {f["id"]: f["state"] for f in sin_nada}
    t.igual("E-23 antes de instalar", "DECLARED_REVIEW_NOT_INSTALLED",
            estados.get("technology-practice-review"))

    faltan = {f["id"] for f in c_matriz.controles_no_instalados(r)}
    t.verdadero("E-23 despues ya no falta",
                "technology-practice-review" not in faltan)
    t.verdadero("E-23 ni la policy", "industry-good-practices-required" not in faltan)

    # Y la regla de la matriz no cambio.
    g2 = c_matriz.regla("G2")
    t.igual("E-23 G2 sigue sin checks", [], g2["checks"])
    t.igual("E-23 y con su review", ["technology-practice-review"], g2["reviews"])


def test_e24_la_revision_conserva_su_traza(t):
    """E-24 (G2-22) — ES0901 / 6.3 / 7.1 / G2."""
    salida = c_rev.resolver(_revision())
    for campo, esperado in (("standard", "ES0901"), ("version", "6.3"),
                            ("section", "7.1"), ("rule", "G2")):
        t.igual("E-24 %s" % campo, esperado, salida["source"][campo])

    # Y una revision sin la tupla completa no se interpreta.
    rota = _revision()
    del rota["source"]["rule"]
    problemas = c_rev.validar_estructura(rota)
    t.verdadero("E-24 sin regla no vale", any("tupla normativa" in p for p in problemas))
