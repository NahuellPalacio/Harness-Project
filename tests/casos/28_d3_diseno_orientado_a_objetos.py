# D3: la primera regla que es condicional y ademas no se puede comprobar.
#
# Escenarios E-01 a E-28 de docs/cambios/d3-diseno-orientado-a-objetos/spec.md. Entre
# parentesis, el D3-nn del pedido de instalacion.
#
# Ninguno evalua criterio tecnico: no se comprueba que una revision acierte sobre el diseño de un
# sistema, porque eso es juicio y ningun test lo puede contradecir. Lo que se comprueba es que la
# estructura sea valida, que el resultado se derive de los hallazgos y de la evidencia, y que las
# cuatro formas de falso positivo que el pedido nombra no lleguen a cumplir.
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"

sys.path.insert(0, str(BIN))
from orquestacion import anexo2 as c_anexo2            # noqa: E402
from orquestacion import controles as c_controles      # noqa: E402
from orquestacion import matriz as c_matriz            # noqa: E402
from orquestacion import normativa as c_normativa      # noqa: E402
from orquestacion import plan as c_plan                # noqa: E402
from orquestacion import revisiones as c_rev           # noqa: E402
from orquestacion import senales as c_senales          # noqa: E402

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D3"}

CONSUMIDORES = ("D3", "P2", "P3", "C2")


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="ev-1", tipo="TASK_CONTEXT", ref="task.type",
              claim="la unidad modifica codigo de aplicacion", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid="applicationCodePresent", **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    s.update(extra)
    return s


def _ev(eid="ev-1", tipo="PROJECT_IMPLEMENTATION", ref="src/dominio/Tramite.java",
        claim="la entidad concentra su comportamiento y no expone su estado", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref,
         "versionOrDate": "2026-09", "claim": claim}
    e.update(extra)
    return e


def _hallazgo(fid="f-1", estado="ADOPTED", materialidad="MINOR", aplicabilidad="APPLICABLE",
              refs=("ev-1",), dimension="responsibility-encapsulation", **extra):
    h = {"findingId": fid, "practice": "responsabilidades encapsuladas",
         "applicability": aplicabilidad, "materiality": materialidad, "status": estado,
         "dimension": dimension, "evidenceRefs": list(refs),
         "rationale": "lo muestra el archivo referenciado"}
    h.update(extra)
    return h


def _revision(hallazgos=None, evidencia=None, regla="D3", **extra):
    r = {"reviewId": "rev-d3-001", "controlType": "REVIEW",
         "source": {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": regla},
         "subject": {"type": "component", "id": "api-tramites", "version": "1.4.0"},
         "evidence": [_ev()] if evidencia is None else evidencia,
         "findings": [_hallazgo()] if hallazgos is None else hallazgos,
         "result": "COMPLIANT",
         "reviewer": {"ownerAgent": "dev-architecture", "supportingAgents": ["dev-backend"],
                      "reviewMode": "AGENT_REVIEW"}}
    r.update(extra)
    return r


def _revision_g2(hallazgos=None, evidencia=None):
    """Una revision de G2 bien formada, para los escenarios de frontera."""
    return {"reviewId": "rev-g2-001", "controlType": "REVIEW",
            "source": {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "G2"},
            "subject": {"type": "technology", "id": "angular", "version": "19.2.18"},
            "evidence": evidencia or [_ev("ev-1", "OFFICIAL_TECHNOLOGY_DOCUMENTATION",
                                          "https://angular.dev/style-guide",
                                          "la guia oficial exige X")],
            "findings": hallazgos or [{"findingId": "f-1", "practice": "usar X",
                                       "applicability": "APPLICABLE",
                                       "practiceStrength": "REQUIRED_BY_SOURCE",
                                       "status": "ADOPTED", "evidenceRefs": ["ev-1"],
                                       "rationale": "x"}],
            "result": "COMPLIANT",
            "reviewer": {"ownerAgent": "dev-architecture", "reviewMode": "AGENT_REVIEW"}}


_CONTEXTO = {
    "meta": {"task_key": "GCBA-1234", "context_hash": "sha256:" + "c" * 64},
    "task": {"key": "GCBA-1234", "type": "Historia de Usuario", "title": "t",
             "acceptance_criteria": ["x"]},
    "project": {"ficha": {"key": "GCBA-7", "rules": ["r"]}},
    "documentation": {"items": []},
    "repository": {"project": {"name": "p"}},
}


# -- la senal ------------------------------------------------------------------

def test_e01_d3_es_condicional(t):
    """E-01 (D3-01) — CONDITIONAL sobre applicationCodePresent, identidad intacta."""
    d3 = c_matriz.regla("D3")
    t.igual("E-01 el modo", "CONDITIONAL", d3["applicability"]["mode"])
    t.igual("E-01 la senal", ["applicationCodePresent"], d3["applicability"]["signals"])
    t.igual("E-01 el id", "D3", d3["id"])
    t.igual("E-01 la categoria", "DESIGN", d3["category"])
    t.igual("E-01 la intencion operativa no cambio",
            "Use object-oriented, high-level coding and good practices.",
            d3["operationalIntentEn"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d3["status"])


def test_e02_true_hace_aplicable(t):
    """E-02 (D3-02) — TRUE con evidencia deja D3 aplicable."""
    bloque = c_normativa.resolucion({"applicationCodePresent": _senal("TRUE")})
    t.verdadero("E-02 D3 aplica", "D3" in bloque["applicableRules"])
    t.verdadero("E-02 exige su policy",
                "high-level-oop-design-required" in bloque["declaredPolicies"])
    t.verdadero("E-02 y su review",
                "object-oriented-design-review" in bloque["declaredReviews"])


def test_e03_false_hace_no_aplicable(t):
    """E-03 (D3-03) — FALSE con evidencia deja D3 fuera."""
    evidencia = [_ev_senal(tipo="PROJECT_CONTEXT", ref="task.scope",
                           claim="la unidad solo toca documentacion")]
    bloque = c_normativa.resolucion({"applicationCodePresent": _senal("FALSE", evidencia)})
    t.verdadero("E-03 D3 no aplica", "D3" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no esta entre las aplicables", "D3" not in bloque["applicableRules"])
    t.verdadero("E-03 su policy no se exige",
                "high-level-oop-design-required" not in bloque["declaredPolicies"])
    t.verdadero("E-03 ni su review",
                "object-oriented-design-review" not in bloque["declaredReviews"])


def test_e04_sin_senal_queda_sin_resolver(t):
    """E-04 (D3-04) — sin senal, D3 sin resolver con la que falta escrita."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D3 esta sin resolver", "D3" in sin_resolver)
    t.igual("E-04 con el motivo", "APPLICABILITY_UNRESOLVED", sin_resolver["D3"]["reason"])
    t.igual("E-04 y la senal que falta", ["applicationCodePresent"],
            sin_resolver["D3"]["missingSignals"])


def test_e05_lo_ausente_nunca_es_falso(t):
    """E-05 (D3-05) — cuatro caminos, ninguno vuelve D3 no aplicable."""
    caminos = {
        "sin senal": {},
        "senal UNRESOLVED": {"applicationCodePresent": _senal("UNRESOLVED", [])},
        "senal sin evidencia": {"applicationCodePresent": _senal("TRUE", [])},
        "evidencia que no referencia nada": {
            "applicationCodePresent": _senal("TRUE", [_ev_senal(ref="   ")])},
    }
    for nombre, senales in caminos.items():
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-05 %s no vuelve D3 no aplicable" % nombre,
                    "D3" not in bloque["notApplicableRules"])
        t.verdadero("E-05 %s la deja sin resolver" % nombre,
                    "D3" in {u["rule"] for u in bloque["unresolvedRules"]})


def test_e06_la_senal_la_reusan_sus_cuatro_consumidores(t):
    """E-06 (D3-06) — se resuelve una vez y las cuatro reglas leen lo mismo."""
    t.igual("E-06 la matriz ata la senal a cuatro reglas", list(CONSUMIDORES),
            c_senales.reglas_de("applicationCodePresent"))

    senal = _senal("TRUE")
    bloque = c_normativa.resolucion({"applicationCodePresent": senal})
    for regla in CONSUMIDORES:
        t.verdadero("E-06 %s aplica" % regla, regla in bloque["applicableRules"])

    # Un solo resultado resuelto, no uno por regla.
    t.igual("E-06 hay una sola senal resuelta", 1, len(bloque["signals"]))
    resuelta = bloque["signals"]["applicationCodePresent"]
    t.igual("E-06 con un solo valor", "TRUE", resuelta["value"])
    t.igual("E-06 y una sola evidencia", "task.type", resuelta["evidence"][0]["reference"])

    # Y en FALSE, las cuatro se apagan juntas.
    apagada = c_normativa.resolucion({"applicationCodePresent": _senal("FALSE")})
    for regla in CONSUMIDORES:
        t.verdadero("E-06 %s no aplica cuando la senal es FALSE" % regla,
                    regla in apagada["notApplicableRules"])


# -- la forma del control ------------------------------------------------------

def test_e07_una_policy_cero_checks_una_review(t):
    """E-07 (D3-07) — la forma exacta que el pedido exige preservar."""
    d3 = c_matriz.regla("D3")
    t.igual("E-07 la policy", ["high-level-oop-design-required"], d3["policies"])
    t.igual("E-07 cero checks", [], d3["checks"])
    t.igual("E-07 la review", ["object-oriented-design-review"], d3["reviews"])


def test_e08_no_se_fabrica_un_check_de_oop(t):
    """E-08 (D3-08) — ni en la matriz, ni en el registro, ni en el disco."""
    t.igual("E-08 la matriz no declara ningun check de D3", [],
            c_matriz.regla("D3")["checks"])

    de_d3 = c_controles.de_la_regla("D3")
    t.igual("E-08 D3 tiene dos controles", 2, len(de_d3))
    t.igual("E-08 y ninguno es un CHECK", [],
            [c["id"] for c in de_d3 if c["type"] == "CHECK"])
    t.igual("E-08 son una policy y una review", ["POLICY", "REVIEW"],
            sorted(c["type"] for c in de_d3))

    # Y no aparecio ningun archivo de check que el registro no declare: si alguien dejara
    # uno de D3 en el disco -con el nombre que fuera- el registro lo delata.
    t.igual("E-08 no hay ningun check sin declarar en el disco", [],
            c_controles.descubrir_no_declarados())
    declarados = {c["file"] for c in c_controles.cargar()["controls"]
                  if c["type"] == "CHECK"}
    t.verdadero("E-08 y ninguno de los declarados es de D3",
                not [f for f in declarados
                     if c_controles.control(Path(f).stem) is not None
                     and c_controles.control(Path(f).stem)["rule"] == "D3"])


def test_e09_la_review_reusa_la_infraestructura_de_g2(t):
    """E-09 — mismo registro, mismo schema, mismo modulo."""
    t.verdadero("E-09 REVIEW ya era un tipo del registro",
                "REVIEW" in c_controles.TIPOS)
    hay = c_controles.instalados()
    t.igual("E-09 las reviews estan en el mismo registro",
            ["object-oriented-design-review", "technology-practice-review"],
            sorted(hay["REVIEW"]))

    # Un solo contrato de review para las dos.
    t.vacio("E-09 la revision de D3 valida contra el schema de G2",
            "; ".join(c_rev.validar_schema(_revision())))
    t.vacio("E-09 y la de G2 sigue validando",
            "; ".join(c_rev.validar_schema(_revision_g2())))
    t.igual("E-09 no hay un segundo schema de review", 1,
            len(list((RAIZ / "comun" / "schemas").glob("*review*.json"))))


# -- lo que no alcanza, y lo que si --------------------------------------------

def _solo_dice(claim, tipo="PROJECT_IMPLEMENTATION"):
    """Una revision cuyo unico respaldo es esa afirmacion."""
    return _revision(evidencia=[_ev(claim=claim, tipo=tipo)])


def _conteo(claim, fid="f-1"):
    """Un hallazgo que solo reporta un hecho del codigo: no tiene dimension que declarar."""
    h = _hallazgo(fid)
    del h["dimension"]
    h["practice"] = claim
    return h


def test_e10_un_conteo_de_clases_no_es_un_hallazgo(t):
    """E-10 (D3-09) — un hallazgo tiene que decir que dimension del diseño evalua."""
    r = _revision(hallazgos=[_conteo("el modulo define 240 clases")],
                  evidencia=[_ev(claim="el modulo define 240 clases")])
    problemas = c_rev.validar_estructura(r)
    t.verdadero("E-10 sin dimension la revision es invalida",
                any("dimension del diseño" in p for p in problemas))
    t.igual("E-10 y no cumple", "REVIEW_INCOMPLETE", c_rev.resolver(r)["result"])

    # Un conteo tampoco entra como dimension: el vocabulario es cerrado.
    inventada = _revision(hallazgos=[_hallazgo(dimension="class-count")])
    t.verdadero("E-10 una dimension fuera del vocabulario tampoco",
                any("no esta en el vocabulario" in p
                    for p in c_rev.validar_estructura(inventada)))
    t.igual("E-10 y no cumple", "REVIEW_INCOMPLETE", c_rev.resolver(inventada)["result"])

    t.verdadero("E-10 ningun conteo esta en el vocabulario",
                not [d for d in c_rev.DIMENSIONES
                     if any(x in d for x in ("count", "conteo", "class", "inherit"))])
    t.verdadero("E-10 la convencion del proyecto tampoco alcanza como fuente",
                "PROJECT_CONVENTION" not in c_rev.FUENTES_DE_IMPLEMENTACION)


def test_e11_una_jerarquia_de_herencia_tampoco(t):
    """E-11 (D3-10) — tres niveles de herencia son un hecho, no una propiedad del diseño."""
    r = _revision(hallazgos=[_conteo("hay una jerarquia de herencia de tres niveles")],
                  evidencia=[_ev(claim="hay una jerarquia de herencia de tres niveles")])
    t.verdadero("E-11 sin dimension es invalida",
                any("dimension del diseño" in p for p in c_rev.validar_estructura(r)))
    t.igual("E-11 y no cumple", "REVIEW_INCOMPLETE", c_rev.resolver(r)["result"])

    # Y si se la cuelga de una dimension real, la conclusion es sobre la dimension y la
    # firma quien revisa: eso es juicio, y este cambio no promete atraparlo.
    colgada = _revision(hallazgos=[_hallazgo(dimension="abstraction-boundaries")])
    t.igual("E-11 colgada de una dimension real, la estructura la acepta", "COMPLIANT",
            c_rev.resolver(colgada)["result"])
    t.verdadero("E-11 y esa dimension si esta en el vocabulario",
                "abstraction-boundaries" in c_rev.DIMENSIONES)


def test_e12_el_framework_elegido_no_alcanza(t):
    """E-12 (D3-11) — que el framework sea OO no dice nada de este codigo."""
    r = _solo_dice("Spring Boot es orientado a objetos",
                   tipo="OFFICIAL_TECHNOLOGY_DOCUMENTATION")
    salida = c_rev.resolver(r)
    t.igual("E-12 no cumple", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-12 y dice por que",
                any("implementacion" in i for i in salida["issues"]))
    t.verdadero("E-12 una guia externa no es evidencia de este sistema",
                "OFFICIAL_TECHNOLOGY_DOCUMENTATION" not in c_rev.FUENTES_DE_IMPLEMENTACION)


def test_e13_la_afirmacion_de_un_agente_no_alcanza(t):
    """E-13 — sin evidencia de la implementacion no hay resultado que cumpla."""
    sin_nada = _revision(evidencia=[], hallazgos=[_hallazgo(refs=())])
    t.igual("E-13 sin evidencia", "REVIEW_INCOMPLETE", c_rev.resolver(sin_nada)["result"])

    # Y una que dice que reviso y esta bien, sin referenciar el sistema.
    opinion = _solo_dice("revise el diseño y esta limpio", tipo="PROJECT_CONVENTION")
    t.igual("E-13 con una opinion", "REVIEW_INCOMPLETE", c_rev.resolver(opinion)["result"])

    # Una referencia a evidencia que no existe es estructuralmente invalida.
    huerfana = _revision(hallazgos=[_hallazgo(refs=("ev-99",))])
    t.verdadero("E-13 una referencia huerfana no vale",
                any("no existe" in p for p in c_rev.validar_estructura(huerfana)))


def test_e14_la_evidencia_de_la_implementacion_cumple(t):
    """E-14 (D3-12) — estructura OO respaldada por el sistema: COMPLIANT."""
    evidencia = [_ev("ev-1", claim="la entidad concentra su comportamiento"),
                 _ev("ev-2", tipo="PROJECT_ARCHITECTURE", ref="docs/arquitectura.md",
                     claim="las fronteras entre dominio, aplicacion y servicio estan escritas")]
    salida = c_rev.resolver(_revision(
        hallazgos=[_hallazgo("f-1", refs=("ev-1",)),
                   _hallazgo("f-2", refs=("ev-2",), practice="fronteras de abstraccion")],
        evidencia=evidencia))
    t.igual("E-14 cumple", "COMPLIANT", salida["result"])
    t.igual("E-14 sin estados pendientes", [], salida["states"])
    t.verdadero("E-14 la arquitectura es evidencia del sistema",
                "PROJECT_ARCHITECTURE" in c_rev.FUENTES_DE_IMPLEMENTACION)


def test_e15_evidencia_incompleta_no_cumple(t):
    """E-15 (D3-13) — REVIEW_INCOMPLETE, nunca cumple."""
    salida = c_rev.resolver(_revision(hallazgos=[_hallazgo(estado="EVIDENCE_MISSING")]))
    t.igual("E-15 el resultado", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-15 y lo dice",
                "REVIEW_EVIDENCE_INCOMPLETE" in salida["states"])

    sin_hallazgos = c_rev.resolver(_revision(hallazgos=[]))
    t.igual("E-15 una revision sin hallazgos tampoco cumple", "REVIEW_INCOMPLETE",
            sin_hallazgos["result"])


def test_e16_un_desvio_material_no_cumple(t):
    """E-16 (D3-14) — logica concentrada de forma procedural: NON_COMPLIANT."""
    salida = c_rev.resolver(_revision(
        hallazgos=[_hallazgo(estado="DEVIATION", materialidad="MATERIAL",
                             practice="concentracion procedural")],
        evidencia=[_ev(claim="toda la logica vive en un helper de 3000 lineas")]))
    t.igual("E-16 el resultado", "NON_COMPLIANT", salida["result"])


def test_e17_un_desvio_sin_materialidad_no_se_ablanda(t):
    """E-17 — sin el eje declarado no se resuelve hacia el lado suave."""
    sin_eje = _hallazgo(estado="DEVIATION")
    del sin_eje["materiality"]
    salida = c_rev.resolver(_revision(hallazgos=[sin_eje]))
    t.igual("E-17 el resultado", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-17 no se ablanda a observaciones",
                salida["result"] != "COMPLIANT_WITH_OBSERVATIONS")
    t.verdadero("E-17 y es estructuralmente invalida",
                any("materiality" in p for p in c_rev.validar_estructura(
                    _revision(hallazgos=[sin_eje]))))

    # UNRESOLVED explicito tampoco se ablanda.
    t.igual("E-17 con materialidad sin resolver", "REVIEW_INCOMPLETE",
            c_rev.resolver(_revision(
                hallazgos=[_hallazgo(estado="DEVIATION",
                                     materialidad="UNRESOLVED")]))["result"])

    # Y el eje de D3 no es el de G2.
    t.igual("E-17 el eje de D3", "materiality", c_rev.eje_de(_revision()))
    t.igual("E-17 el eje de G2", "practiceStrength", c_rev.eje_de(_revision_g2()))


# -- el conflicto de paradigma -------------------------------------------------

def test_e18_el_conflicto_se_expone(t):
    """E-18 (D3-15) — con su estado propio, no disfrazado de otra cosa."""
    salida = c_rev.resolver(_revision(
        hallazgos=[_hallazgo(estado="TECHNOLOGY_PARADIGM_CONFLICT",
                             practice="el paradigma elegido no permite demostrar la regla")],
        evidencia=[_ev(claim="el componente es un script de transformacion sin objetos")]))
    t.verdadero("E-18 el estado se expone",
                "TECHNOLOGY_PARADIGM_CONFLICT" in salida["states"])
    t.verdadero("E-18 y se explica",
                any("arquitectura o una persona" in i for i in salida["issues"]))
    t.igual("E-18 el estado tiene nombre propio", "TECHNOLOGY_PARADIGM_CONFLICT",
            c_rev.CONFLICTO_DE_PARADIGMA)


def test_e19_el_conflicto_no_se_autoaprueba(t):
    """E-19 (D3-16) — ni COMPLIANT, ni NOT_APPLICABLE, ni excepcion aprobada."""
    revision = _revision(hallazgos=[_hallazgo(estado="TECHNOLOGY_PARADIGM_CONFLICT")])
    salida = c_rev.resolver(revision)
    t.igual("E-19 el resultado", "REVIEW_INCOMPLETE", salida["result"])
    t.verdadero("E-19 no cumple", salida["result"] != "COMPLIANT")
    t.verdadero("E-19 ni con observaciones",
                salida["result"] != "COMPLIANT_WITH_OBSERVATIONS")

    # La regla sigue aplicando: el conflicto no la apaga.
    bloque = c_normativa.resolucion({"applicationCodePresent": _senal("TRUE")})
    t.verdadero("E-19 D3 sigue aplicando", "D3" in bloque["applicableRules"])
    t.verdadero("E-19 y no paso a no aplicable", "D3" not in bloque["notApplicableRules"])

    # Y un conflicto junto a hallazgos que cumplen no se compensa.
    mezcla = _revision(hallazgos=[_hallazgo("f-1"),
                                  _hallazgo("f-2", estado="TECHNOLOGY_PARADIGM_CONFLICT")])
    t.igual("E-19 un hallazgo bueno no lo compensa", "REVIEW_INCOMPLETE",
            c_rev.resolver(mezcla)["result"])

    # No existe ningun resultado de excepcion aprobada.
    t.verdadero("E-19 no hay un resultado de excepcion aprobada",
                "APPROVED_EXCEPTION" not in io.open(
                    BIN / "orquestacion" / "revisiones.py", encoding="utf-8").read())


# -- las fronteras -------------------------------------------------------------

def test_e20_g2_compliant_no_es_d3_compliant(t):
    """E-20 (D3-17) — dos reviews sobre el mismo sistema, resultados independientes."""
    # Las dos sobre la MISMA evidencia: cada una toma la que su regla admite.
    compartida = [_ev("ev-1", claim="la logica esta concentrada en un helper"),
                  _ev("ev-2", tipo="OFFICIAL_TECHNOLOGY_DOCUMENTATION",
                      ref="https://angular.dev/style-guide", claim="la guia oficial exige X")]
    g2 = c_rev.resolver(_revision_g2(
        hallazgos=[{"findingId": "f-1", "practice": "usar X", "applicability": "APPLICABLE",
                    "practiceStrength": "REQUIRED_BY_SOURCE", "status": "ADOPTED",
                    "evidenceRefs": ["ev-2"], "rationale": "x"}],
        evidencia=compartida))
    t.igual("E-20 G2 cumple", "COMPLIANT", g2["result"])

    d3 = c_rev.resolver(_revision(
        hallazgos=[_hallazgo(estado="DEVIATION", materialidad="MATERIAL",
                             dimension="procedural-concentration", refs=("ev-1",))],
        evidencia=compartida))
    t.igual("E-20 y D3 no", "NON_COMPLIANT", d3["result"])
    t.igual("E-20 cada una con su regla", "G2", g2["source"]["rule"])
    t.igual("E-20 y la otra con la suya", "D3", d3["source"]["rule"])

    # La exigencia de evidencia de cada una es distinta, y por eso no se heredan.
    t.verdadero("E-20 lo que alcanza en G2 no alcanza en D3",
                set(c_rev.FUENTES_RECONOCIDAS) & set(c_rev.FUENTES_DE_IMPLEMENTACION) == set())


def test_e21_un_patron_no_es_d3_compliant(t):
    """E-21 (D3-18) — P2 es otra regla, y su presencia no rescata un desvio."""
    con_patron = _revision(
        hallazgos=[_hallazgo(estado="DEVIATION", materialidad="MATERIAL", refs=("ev-1",))],
        evidencia=[_ev("ev-1", claim="la logica esta concentrada en un helper"),
                   _ev("ev-2", claim="hay un Strategy en el modulo de calculo")])
    salida = c_rev.resolver(con_patron)
    t.igual("E-21 el patron no rescata el desvio", "NON_COMPLIANT", salida["result"])

    # Y D3 no emite ningun veredicto de P2.
    texto = repr(salida)
    for ajeno in ("P2", "standard-design-patterns-required"):
        t.verdadero("E-21 el resultado no habla de %s" % ajeno, ajeno not in texto)
    t.verdadero("E-21 P2 tiene su propia policy",
                "standard-design-patterns-required" in c_matriz.regla("P2")["policies"])
    t.verdadero("E-21 y no es la de D3",
                "standard-design-patterns-required" not in c_matriz.regla("D3")["policies"])


def test_e22_el_estilo_no_es_d3_compliant(t):
    """E-22 (D3-19) — P3 es otra regla, y el linter en verde no rescata un desvio."""
    con_lint = _revision(
        hallazgos=[_hallazgo(estado="DEVIATION", materialidad="MATERIAL")],
        evidencia=[_ev("ev-1", claim="la logica esta concentrada en un helper"),
                   _ev("ev-2", tipo="PROJECT_CONVENTION", ref=".eslintrc",
                       claim="el linter pasa sin advertencias")])
    salida = c_rev.resolver(con_lint)
    t.igual("E-22 el lint no rescata el desvio", "NON_COMPLIANT", salida["result"])

    texto = repr(salida)
    for ajeno in ("P3", "standard-code-style-required", "code-style-compliance"):
        t.verdadero("E-22 el resultado no habla de %s" % ajeno, ajeno not in texto)
    t.verdadero("E-22 el check de estilo es de P3",
                "code-style-compliance" in c_matriz.regla("P3")["checks"])
    t.igual("E-22 y D3 no tiene checks", [], c_matriz.regla("D3")["checks"])


def test_e23_el_inventario_de_g1_se_reusa(t):
    """E-23 (D3-20) — un solo inventario, un solo lugar donde arreglarlo."""
    catalogos = sorted(p.name for p in REGLAS.glob("*technology*.json"))
    t.igual("E-23 hay un solo catalogo de tecnologias",
            ["annex-ii-technology-catalog.json"], catalogos)

    doc = c_anexo2.cargar()
    t.verdadero("E-23 y el modulo de G1 lo lee", bool(doc.get("entries")))
    t.igual("E-23 con la traza de G1", "G1", c_anexo2.TRAZA["rule"])

    # D3 no trajo un segundo detector.
    modulos = sorted(p.name for p in (BIN / "orquestacion").glob("*.py")
                     if any(x in p.name for x in ("inventario", "inventory", "stack",
                                                  "tecnolog")))
    t.igual("E-23 no hay un segundo detector de stack", [], modulos)

    # Y el contrato de la review lo dice.
    contrato = io.open(CONTROLES / "reviews" / "object-oriented-design-review.md",
                       encoding="utf-8").read()
    t.contiene("E-23 la review declara de donde sale el inventario", "from G1", contrato)


def test_e24_la_evidencia_de_g2_apoya_y_no_aprueba(t):
    """E-24 — se reusa como apoyo; el resultado no se hereda."""
    # Sola, una fuente de G2 no sostiene un hallazgo de D3.
    sola = _revision(evidencia=[_ev(tipo="RECOGNIZED_INDUSTRY_GUIDANCE",
                                    ref="https://guia", claim="la guia recomienda Y")])
    t.igual("E-24 sola no alcanza", "REVIEW_INCOMPLETE", c_rev.resolver(sola)["result"])

    # Al lado de evidencia del sistema, acompana y no molesta.
    con_apoyo = _revision(
        hallazgos=[_hallazgo(refs=("ev-1", "ev-2"))],
        evidencia=[_ev("ev-1"),
                   _ev("ev-2", tipo="RECOGNIZED_INDUSTRY_GUIDANCE", ref="https://guia",
                       claim="la guia recomienda Y")])
    t.igual("E-24 acompanada cumple", "COMPLIANT", c_rev.resolver(con_apoyo)["result"])

    # Y el resultado de G2 no entra en el de D3 por ningun lado.
    t.igual("E-24 G2 cumple por su cuenta", "COMPLIANT",
            c_rev.resolver(_revision_g2())["result"])
    t.igual("E-24 y D3 decide con lo suyo", "NON_COMPLIANT",
            c_rev.resolver(_revision(
                hallazgos=[_hallazgo(estado="DEVIATION", materialidad="MATERIAL")]))["result"])


# -- los agentes, la propagacion y la instalacion ------------------------------

def test_e25_los_agentes_salen_del_registro(t):
    """E-25 (D3-22) — dueno y apoyos declarados; uno desconocido invalida."""
    t.vacio("E-25 dev-architecture y dev-backend estan declarados",
            "; ".join(c_rev.validar_agentes(_revision())))

    con_frontend = _revision()
    con_frontend["reviewer"]["supportingAgents"] = ["dev-backend", "dev-frontend"]
    t.vacio("E-25 dev-frontend tambien",
            "; ".join(c_rev.validar_agentes(con_frontend)))

    inventado = _revision()
    inventado["reviewer"]["ownerAgent"] = "dev-inventado"
    problemas = c_rev.validar_agentes(inventado)
    t.verdadero("E-25 uno que el registro no declara invalida", bool(problemas))
    t.verdadero("E-25 y lo dice", any("no declara" in p for p in problemas))
    t.igual("E-25 la revision con ese agente no se interpreta", "REVIEW_INCOMPLETE",
            c_rev.resolver(inventado)["result"])

    # Y no se creo ningun agente.
    t.verdadero("E-25 dev-inventado no existe",
                not (RAIZ / "harnesses" / "desarrollo" / "agents" / "dev-inventado.md").exists())


def test_e26_la_unidad_propaga_senal_policy_y_review(t):
    """E-26 (D3-21) — y declaredChecks no gana ninguno por D3."""
    unidad = {"id": "u1", "objective": "o", "domain": "backend",
              "requiredCapabilities": [], "dependencies": [], "signals": [],
              "normativeSignals": {"applicationCodePresent": _senal("TRUE")}}
    documento = c_plan.armar({"objective": "x", "domains": ["backend"], "policies": [],
                              "workUnits": [unidad]}, _CONTEXTO, {}, None)
    n = documento["workUnits"][0]["normative"]

    t.igual("E-26 el valor viaja", "TRUE",
            n["signals"]["applicationCodePresent"]["value"])
    t.igual("E-26 la evidencia tambien", "task.type",
            n["signals"]["applicationCodePresent"]["evidence"][0]["reference"])
    t.verdadero("E-26 D3 aplica", "D3" in n["applicableRules"])
    t.verdadero("E-26 con su policy",
                "high-level-oop-design-required" in n["declaredPolicies"])
    t.verdadero("E-26 y su review",
                "object-oriented-design-review" in n["declaredReviews"])
    t.verdadero("E-26 D3 no agrega ningun check",
                not set(c_matriz.regla("D3")["checks"]) & set(n["declaredChecks"]))
    t.vacio("E-26 el plan valida", c_plan.validar(documento))


def test_e27_los_controles_dejan_de_faltar(t):
    """E-27 (D3-23) — sin tocar el texto normativo de la regla."""
    resolucion = c_matriz.resolver({"applicationCodePresent": True})

    sin_nada = c_matriz.controles_no_instalados(resolucion, policies_instaladas=[],
                                                checks_instalados=[], reviews_instaladas=[])
    estados = {f["id"]: f["state"] for f in sin_nada}
    t.igual("E-27 antes la policy", "DECLARED_POLICY_NOT_INSTALLED",
            estados.get("high-level-oop-design-required"))
    t.igual("E-27 antes la review", "DECLARED_REVIEW_NOT_INSTALLED",
            estados.get("object-oriented-design-review"))

    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    t.verdadero("E-27 despues la policy no falta",
                "high-level-oop-design-required" not in faltan)
    t.verdadero("E-27 despues la review no falta",
                "object-oriented-design-review" not in faltan)

    # El texto citable de la regla no se toco.
    citable = c_normativa.reglas()
    d3 = [r for r in citable if r.get("rule") == "D3"]
    t.igual("E-27 la regla citable sigue estando", 1, len(d3))
    t.contiene("E-27 con su texto intacto", "programacion orientada a objetos",
               d3[0]["text"].replace("ó", "o"))
    t.igual("E-27 y su pagina", "12", str(d3[0]["page"]))


def test_e28_la_traza_se_conserva(t):
    """E-28 (D3-24) — ES0901 / 6.3 / 7.1 / D3 en todo lo que D3 emite."""
    salida = c_rev.resolver(_revision())
    for campo, esperado in TRAZA.items():
        t.igual("E-28 la review: %s" % campo, esperado, salida["source"][campo])

    t.igual("E-28 la trazabilidad de la matriz", TRAZA, c_matriz.trazabilidad("D3"))

    policy = io.open(CONTROLES / "policies" / "high-level-oop-design-required.md",
                     encoding="utf-8").read()
    t.contiene("E-28 la policy dice su regla", "rule: D3", policy)
    t.contiene("E-28 y su estandar", "standard: ES0901", policy)

    for cid in ("high-level-oop-design-required", "object-oriented-design-review"):
        declarado = c_controles.control(cid)
        t.igual("E-28 el registro: %s" % cid, "D3", declarado["source"]["rule"])
        t.igual("E-28 con su version: %s" % cid, "6.3", declarado["source"]["version"])

    # Una revision sin la tupla completa no se interpreta.
    rota = _revision()
    del rota["source"]["rule"]
    t.verdadero("E-28 sin regla no vale",
                any("tupla normativa" in p for p in c_rev.validar_estructura(rota)))
