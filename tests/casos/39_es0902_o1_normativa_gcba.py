# ES0902 §3 O1: la normativa de TI del GCABA como linea base, y la revision que la mide.
#
# Escenarios E-01 a E-28 de docs/cambios/es0902-o1-normativa-de-ti-del-gcba/spec.md. Entre
# parentesis, el O1-nn del pedido de instalacion.
#
# 🔴 Lo que se verifica es que O1 NO se pueda poner en verde barato. La fila declara dos controles
# y esos dos controles son su propia policy y su propia review: por el camino generico, dos
# `controlResults` en PASS la ponen en COMPLIANT sin que nadie mire que normativa aplica. Los
# escenarios que importan son los que sostienen el fallo cerrado —fuente sin cargar, vigencia sin
# constar, resultado que falla, excepcion sin las dos mitades— y la frontera de la aprobacion.
#
# 🔴 Los ids de la policy y de la review van CLAVADOS por literal. Leerlos de la matriz y
# compararlos contra si mismos es un test que pasa con cualquier id.
import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import linea_base as lb               # noqa: E402
from orquestacion import seguridad                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import revisiones                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import matriz as c_matriz             # noqa: E402
from orquestacion import normativa as c_normativa       # noqa: E402
from orquestacion import roster as c_roster             # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402

MATRIZ = seguridad.cargar()
LINEA = lb.cargar()
REGISTRO = c_controles.cargar()

# Los dos ids, escritos a mano. Es la unica forma de que renombrarlos rompa algo.
POLICY = "gcba-it-security-normative-compliance-required"
REVIEW = "gcba-it-security-normative-review"

# Las tres resoluciones que ES0902 nombra y el harness no tiene.
LAS_TRES = ("RES-177-ASINF-2013", "RES-239-ASINF-2014", "RES-12-ASINF-2017")

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": "O1",
         "ruleKey": "ES0902.O1"}


def _base(*fuentes):
    """Una linea base armada a mano. Sin fuentes se usan las dos cargadas y vigentes."""
    if not fuentes:
        fuentes = (_fuente("ES0901", "LOADED", "CURRENT"),
                   _fuente("ES0902", "LOADED", "CURRENT"))
    return {"version": "1.0", "authority": "GCBA / ASI", "sources": list(fuentes)}


def _fuente(fid, estado="LOADED", vigencia=None, **extra):
    f = {"id": fid, "title": "fuente %s" % fid, "status": estado,
         "authority": "Agencia de Sistemas de Informacion"}
    if vigencia is not None:
        f["currency"] = vigencia
    f.update(extra)
    return f


def _resultado(estandar="ES0901", regla="D1", resultado="COMPLIANT"):
    return {"standard": estandar, "version": "6.3" if estandar == "ES0901" else "6.2",
            "rule": regla, "ruleKey": "%s.%s" % (estandar, regla), "result": resultado}


def _evidencia(base=None, resultados=None, **extra):
    ev = {"subject": {"id": "u-1", "type": "WORK_UNIT"},
          "normativeBaseline": base if base is not None else _base(),
          "standardResults": list(resultados if resultados is not None
                                  else [_resultado()])}
    ev.update(extra)
    return ev


def _excepcion(reglas=("ES0901.D1",), contrato="PROJECT_CONTRACT", asi="ASI_APPROVAL"):
    doc = {"affectedRules": list(reglas), "reason": "el contrato lo permite"}
    if contrato:
        doc["contractEvidence"] = [{"source": contrato, "reference": "clausula 4"}]
    if asi:
        doc["asiApprovalEvidence"] = [{"source": asi, "reference": "acta-asi"}]
    return doc


def _valores(dato):
    """Todos los strings que hay adentro, a cualquier profundidad."""
    if isinstance(dato, dict):
        salida = []
        for k, v in dato.items():
            salida.extend(_valores(v))
        return salida
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


# -- La fila, que no se toca ---------------------------------------------------

def test_e01_o1_sigue_always_con_cero_senales(t):
    """E-01 (O1-01, O1-02) — `ALWAYS`, `signals` vacio, y aplica con el diccionario vacio."""
    o1 = seguridad.regla("O1", MATRIZ)
    aplic = o1["applicability"]
    t.igual("E-01 el modo es ALWAYS", "ALWAYS", aplic["mode"])
    t.igual("E-01 y no declara ninguna senal", [], aplic.get("signals"))
    estado, faltan = seguridad.resolver_regla(o1, {})
    t.igual("E-01 con cero senales igual aplica", "APPLICABLE", estado)
    t.igual("E-01 y no falta ninguna", [], faltan)

    # 🔴 Y no entra por la clave compuesta de otro estandar: `O1` es de ES0902.
    t.igual("E-01 la clave es la compuesta", "ES0902.O1", o1["ruleKey"])
    t.verdadero("E-01 ninguna senal de ES0902 sale de O1",
                "O1" not in [r["id"] for r in MATRIZ["rules"]
                             if (r.get("applicability") or {}).get("signals")])


def test_e02_el_dueno_sigue_siendo_dev_security(t):
    """E-02 (O1-03) — uno solo, y declarado en el registro de agentes."""
    o1 = seguridad.regla("O1", MATRIZ)
    t.igual("E-02 el dueno es dev-security", ["dev-security"], o1["primaryAgents"])
    declarados = {a["id"] for a in c_reg.cargar()["agents"]}
    t.verdadero("E-02 y esta declarado", "dev-security" in declarados)
    t.vacio("E-02 la fila no nombra a nadie que el registro no declare",
            [a for a in o1["primaryAgents"] if a not in declarados])


def test_e03_la_policy_y_la_review_con_su_id_literal(t):
    """E-03 (O1-04, O1-05) — una de cada una, con estos ids escritos a mano."""
    o1 = seguridad.regla("O1", MATRIZ)
    t.igual("E-03 una sola policy", [POLICY], o1["policies"])
    t.igual("E-03 una sola review", [REVIEW], o1["reviews"])
    t.igual("E-03 la policy se llama asi", "gcba-it-security-normative-compliance-required",
            o1["policies"][0])
    t.igual("E-03 la review se llama asi", "gcba-it-security-normative-review",
            o1["reviews"][0])

    # Y el modulo los nombra con el mismo id: dos nombres para el mismo control es no tenerlo.
    t.igual("E-03 el modulo usa el id de la policy", POLICY, lb.POLICY)
    t.igual("E-03 el modulo usa el id de la review", REVIEW, lb.REVIEW)

    controles = {c["id"]: c["type"] for c in seguridad.controles_de("O1", MATRIZ)}
    t.igual("E-03 son dos controles y nada mas", 2, len(controles))
    t.igual("E-03 la policy es POLICY", "POLICY", controles[POLICY])
    t.igual("E-03 la review es REVIEW", "REVIEW", controles[REVIEW])


def test_e04_o1_no_declara_ni_instala_ningun_check(t):
    """E-04 (O1-06) — ni en la matriz, ni en el registro, ni en disco."""
    o1 = seguridad.regla("O1", MATRIZ)
    t.igual("E-04 la matriz no declara ningun check", [], o1["checks"])

    de_o1 = [c for c in REGISTRO["controls"] if c["rule"] == "O1"]
    t.igual("E-04 el registro declara dos controles de O1", 2, len(de_o1))
    t.igual("E-04 y ninguno es CHECK", [], [c["id"] for c in de_o1 if c["type"] == "CHECK"])
    t.igual("E-04 son la policy y la review", ["POLICY", "REVIEW"],
            sorted(c["type"] for c in de_o1))

    # 🔴 Y no aparece uno en disco por su cuenta: un archivo que aparece solo no da de alta un
    # control, pero un archivo que aparece solo tampoco puede estar.
    #
    # 🔴 El barrido es sobre los literales del modulo, no sobre una grafia. Los trece checks de
    # este repositorio declaran la regla por constante -`REGLA = "D8"`- y la tupla por
    # referencia -`{"rule": REGLA}`-, asi que buscar `"rule": "O1"` en el texto no encuentra un
    # check de O1 escrito como se escriben todos los demas.
    archivos = sorted((CONTROLES / "checks").glob("*.py"))
    t.igual("E-04 hay diecisiete checks para barrer", 17, len(archivos))
    por_archivo = {c["file"]: c for c in REGISTRO["controls"]}
    for archivo in archivos:
        literales = {n.value for n in ast.walk(ast.parse(archivo.read_text(encoding="utf-8")))
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        t.verdadero("E-04 %s no nombra la regla O1" % archivo.name, "O1" not in literales)
        declarado = por_archivo.get("controles/checks/%s" % archivo.name)
        t.verdadero("E-04 %s esta declarado" % archivo.name, declarado is not None)
        t.verdadero("E-04 %s no sale de O1" % archivo.name, declarado["rule"] != "O1")


def test_e05_instalar_o1_no_agrega_una_fila_ni_un_estandar(t):
    """E-05 — 21 reglas, 24 reglas, y dos estandares. No tres."""
    t.igual("E-05 ES0902 sigue con 21 reglas", 21, len(MATRIZ["rules"]))
    t.igual("E-05 ES0901 sigue con 24", 24, len(c_matriz.reglas()))
    bloque = c_normativa.resolucion({})
    t.igual("E-05 el bloque normativo expone dos estandares", ["ES0901", "ES0902"],
            sorted(bloque["standards"]))
    t.verdadero("E-05 y la linea base no es uno de ellos",
                "GCBA" not in bloque["standards"])
    veredicto, errores = seguridad.validar(MATRIZ)
    t.igual("E-05 la matriz sigue valida", "NORMATIVE_MATRIX_VALID", veredicto)
    t.vacio("E-05 sin errores", errores)


# -- La linea base, que es un registro de apoyo --------------------------------

def test_e06_la_linea_base_carga_y_valida(t):
    """E-06 — cinco fuentes, la autoridad, el schema, y tambien instalada."""
    t.igual("E-06 son cinco fuentes", 5, len(lb.fuentes(LINEA)))
    t.igual("E-06 con su autoridad", "GCBA / ASI", LINEA["authority"])
    veredicto, errores = lb.validar(LINEA)
    t.igual("E-06 valida", "NORMATIVE_BASELINE_VALID", veredicto)
    t.vacio("E-06 sin errores", errores)
    t.vacio("E-06 y sin errores de schema", lb.validar_schema(LINEA))

    # 🔴 Instalada, `reglas/` cuelga a distinta altura. Verde donde corre la suite y muerta
    # donde corre el harness es el defecto que esto esta para encontrar.
    fuente = (BIN / "orquestacion" / "linea_base.py").read_text(encoding="utf-8")
    t.contiene("E-06 el modulo busca con roster", "roster.ruta_de_regla", fuente)
    tmp = tempfile.mkdtemp(prefix="o1-inst")
    try:
        binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "orquestacion"
        reglas_d = Path(tmp) / ".claude" / "harness" / "reglas" / "desarrollo"
        esquemas = Path(tmp) / ".claude" / "harness" / "schemas"
        for d in (binario, reglas_d, esquemas):
            d.mkdir(parents=True)
        (reglas_d.parent / "secretos.patrones.json").write_text("{}", encoding="utf-8")
        shutil.copy(str(REGLAS / lb.ARCHIVO), str(reglas_d / lb.ARCHIVO))
        for esquema in SCHEMAS.glob("*.schema.json"):
            shutil.copy(str(esquema), str(esquemas / esquema.name))
        desde = binario / "linea_base.py"
        desde.write_text("# marcador\n", encoding="utf-8")
        t.verdadero("E-06 roster la encuentra instalada",
                    bool(c_roster.ruta_de_regla(lb.ARCHIVO, str(desde))))
        t.igual("E-06 y carga instalada", 5, len(lb.fuentes(lb.cargar(str(desde)))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e07_es0901_y_es0902_son_las_dos_cargadas(t):
    """E-07 (O1-07, O1-08) — con su version y su autoridad, y son las unicas dos."""
    t.igual("E-07 las cargadas son dos", ["ES0901", "ES0902"], sorted(lb.cargadas(LINEA)))
    for fid, version in (("ES0901", "6.3"), ("ES0902", "6.2")):
        f = lb.fuente(fid, LINEA)
        t.verdadero("E-07 %s esta en la linea base" % fid, f is not None)
        t.igual("E-07 %s es LOADED" % fid, "LOADED", lb.estado_de(f))
        t.igual("E-07 %s con su version" % fid, version, f.get("version"))
        t.contiene("E-07 %s con su autoridad" % fid, "Agencia de Sistemas de", f["authority"])
    t.igual("E-07 ES0902 declara la fecha de su fuente", "2025-08",
            lb.fuente("ES0902", LINEA).get("sourceDate"))


def test_e08_las_tres_resoluciones_entran_sin_contenido(t):
    """E-08 (O1-09) — titulo y autoridad. Version, fecha, vigencia y texto NO."""
    t.igual("E-08 son tres las declaradas y no cargadas", sorted(LAS_TRES),
            sorted(lb.declaradas_no_cargadas(LINEA)))
    for fid in LAS_TRES:
        f = lb.fuente(fid, LINEA)
        t.verdadero("E-08 %s esta declarada" % fid, f is not None)
        t.igual("E-08 %s no esta cargada" % fid, "DECLARED_EXTERNAL_NOT_LOADED",
                lb.estado_de(f))
        # 🔴 Las claves exactas. Un campo de mas es contenido que alguien invento.
        t.igual("E-08 %s trae cuatro claves y no una mas" % fid,
                ["authority", "id", "status", "title"], sorted(f.keys()))
        t.igual("E-08 %s no dice si sigue vigente" % fid, "UNRESOLVED", lb.vigencia_de(f))
        t.verdadero("E-08 %s no esta entre las cargadas" % fid,
                    fid not in lb.cargadas(LINEA))
    t.igual("E-08 las tres tienen titulo",
            ["N° 12/ASINF/17", "Resolución 177-ASINF-2013", "Resolución 239-ASINF/2014"],
            sorted(lb.fuente(f, LINEA)["title"] for f in LAS_TRES))


def test_e09_la_linea_base_no_es_una_matriz_normativa(t):
    """E-09 — no declara reglas, no la carga ningun estandar, no aporta controles."""
    t.verdadero("E-09 no declara `rules`", "rules" not in LINEA)
    t.verdadero("E-09 no declara un conteo de reglas", "expectedRuleCount" not in LINEA)
    for f in lb.fuentes(LINEA):
        for campo in ("policies", "checks", "reviews", "signals", "applicability",
                      "primaryAgents"):
            t.verdadero("E-09 %s no declara `%s`" % (f["id"], campo), campo not in f)

    # Los dos estandares siguen cargando lo suyo, y ninguno carga esto.
    t.igual("E-09 seguridad sigue cargando la matriz de ES0902", "ES0902",
            seguridad.cargar()["standard"])
    t.igual("E-09 matriz sigue cargando la de ES0901", "ES0901",
            c_matriz.cargar()["standard"]["id"])
    t.verdadero("E-09 y la linea base no tiene un `standard`", "standard" not in LINEA)
    t.vacio("E-09 no aporta ninguna senal",
            [f for f in lb.fuentes(LINEA) if f.get("signals")])

    # 🔴 Y no aparece bajo `standards`: la clausula se afirma aca, no en el escenario vecino.
    bloque = c_normativa.resolucion({})
    t.igual("E-09 el bloque normativo no la expone como estandar", ["ES0901", "ES0902"],
            sorted(bloque["standards"]))
    for fid in [f["id"] for f in lb.fuentes(LINEA)]:
        t.verdadero("E-09 `%s` no es un estandar del bloque" % fid,
                    fid not in bloque["standards"] or fid in ("ES0901", "ES0902"))
    for modulo in ("matriz.py", "seguridad.py", "normativa.py"):
        fuente = (BIN / "orquestacion" / modulo).read_text(encoding="utf-8")
        t.verdadero("E-09 %s no carga la linea base" % modulo, lb.ARCHIVO not in fuente)


def test_e10_un_estado_o_una_vigencia_que_no_existen_no_validan(t):
    """E-10 — y el error nombra la fuente por su id, no por su posicion."""
    casos = (
        ("estado", _base(_fuente("X1", "MEDIO_CARGADA")), "X1"),
        ("vigencia", _base(_fuente("X2", "LOADED", "CASI")), "X2"),
        ("sucesion", _base(_fuente("X3", "LOADED", "SUPERSEDED", supersededBy="X9")), "X3"),
        ("autoridad", _base({"id": "X4", "title": "t", "status": "LOADED", "authority": ""}),
         "X4"),
    )
    for caso, doc, fid in casos:
        veredicto, errores = lb.validar(doc)
        t.igual("E-10 %s: no valida" % caso, "NORMATIVE_BASELINE_INVALID", veredicto)
        t.contiene("E-10 %s: el error nombra la fuente" % caso, fid, " | ".join(errores))

    repetida = _base(_fuente("X5"), _fuente("X5"))
    veredicto, errores = lb.validar(repetida)
    t.igual("E-10 repetida: no valida", "NORMATIVE_BASELINE_INVALID", veredicto)
    t.contiene("E-10 repetida: se dice cual", "X5", " | ".join(errores))

    # Y una bien formada si valida: el test que solo prueba el rechazo pasa con un validador
    # que rechaza todo.
    t.igual("E-10 una bien formada valida", "NORMATIVE_BASELINE_VALID", lb.validar(_base())[0])


# -- El fallo cerrado ----------------------------------------------------------

def test_e11_una_fuente_sin_cargar_exige_contexto_externo(t):
    """E-11 (O1-10) — con el id de la fuente escrito al lado."""
    doc = _base(_fuente("ES0901", "LOADED", "CURRENT"),
                _fuente("RES-9", "DECLARED_EXTERNAL_NOT_LOADED", "CURRENT"))
    rev = lb.revision(_evidencia(doc))
    t.contiene("E-11 el estado es el del contexto externo",
               "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED", " ".join(rev["states"]))
    t.contiene("E-11 y se dice cual fuente", "RES-9", " | ".join(rev["issues"]))
    t.verdadero("E-11 no cumple", rev["result"] != "COMPLIANT")
    t.igual("E-11 queda incompleta", "REVIEW_INCOMPLETE", rev["result"])

    # Con las dos cargadas y vigentes, ese estado no aparece: el test que solo mira que
    # aparezca pasa con un modulo que lo pone siempre.
    limpia = lb.revision(_evidencia())
    t.verdadero("E-11 sin fuentes sin cargar no aparece",
                "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED" not in limpia["states"])


def test_e12_sin_vigencia_la_supersesion_queda_sin_resolver(t):
    """E-12 (O1-11) — ausente, y reemplazada sin decir por cual."""
    for caso, fuente in (("ausente", _fuente("ES0901", "LOADED")),
                         ("reemplazada", _fuente("ES0901", "LOADED", "SUPERSEDED"))):
        rev = lb.revision(_evidencia(_base(fuente)))
        t.contiene("E-12 %s: el estado" % caso, "NORMATIVE_SUPERSESSION_UNRESOLVED",
                   " ".join(rev["states"]))
        t.contiene("E-12 %s: con el id de la fuente" % caso, "ES0901",
                   " | ".join(rev["issues"]))
        t.verdadero("E-12 %s: no cumple" % caso, rev["result"] != "COMPLIANT")

    # Reemplazada Y diciendo por cual, con esa otra declarada: la sucesion queda resuelta.
    doc = _base(_fuente("ES0901", "LOADED", "SUPERSEDED", supersededBy="ES0901-NUEVA"),
                _fuente("ES0901-NUEVA", "LOADED", "CURRENT"))
    rev = lb.revision(_evidencia(doc))
    t.verdadero("E-12 con sucesor declarado se resuelve",
                "NORMATIVE_SUPERSESSION_UNRESOLVED" not in rev["states"])
    t.contiene("E-12 y queda dicho por cual", "ES0901-NUEVA", " | ".join(rev["issues"]))

    # 🔴 Y el default de la vigencia es UNRESOLVED, tambien para lo que esta cargado.
    t.igual("E-12 ausente es UNRESOLVED", "UNRESOLVED", lb.vigencia_de({"status": "LOADED"}))
    t.igual("E-12 desconocida tambien", "UNRESOLVED", lb.vigencia_de({"currency": "QUIZAS"}))


def test_e13_la_linea_base_como_vino_nunca_cumple(t):
    """E-13 (O1-12) — REVIEW_INCOMPLETE, y se nombran las tres resoluciones."""
    rev = lb.revision({"subject": {"id": "u-1"},
                       "standardResults": [_resultado(), _resultado("ES0902", "Vu2")]})
    t.igual("E-13 la review esta incompleta", "REVIEW_INCOMPLETE", rev["result"])
    t.contiene("E-13 falta contexto externo", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
               " ".join(rev["states"]))
    t.contiene("E-13 y no consta la vigencia", "NORMATIVE_SUPERSESSION_UNRESOLVED",
               " ".join(rev["states"]))
    motivos = " | ".join(rev["issues"])
    for fid in LAS_TRES:
        t.contiene("E-13 se nombra %s" % fid, fid, motivos)

    # 🔴 Con CUALQUIER combinacion de resultados reusados, nunca COMPLIANT.
    for resultado in seguridad.RESULTADOS:
        r = lb.revision({"subject": {"id": "u-1"},
                         "standardResults": [_resultado("ES0901", "D1", resultado)]})
        t.verdadero("E-13 con %s tampoco cumple" % resultado, r["result"] != "COMPLIANT")

    # Y la fila entera tampoco: el resultado de O1 sale de la review.
    fila = seguridad.resultado("O1", {"subject": {"id": "u-1"},
                                      "standardResults": [_resultado()]}, {})
    t.igual("E-13 la fila queda sin resolver", "UNRESOLVED", fila["result"])
    t.igual("E-13 y su review esta incompleta", "REVIEW_INCOMPLETE", fila["review"]["result"])


def test_e14_una_review_sin_sujeto_esta_incompleta(t):
    """E-14 — una revision que no dice sobre que es no es una revision."""
    for caso, sujeto in (("sin sujeto", None), ("sujeto vacio", {}), ("sujeto sin id", {"t": 1})):
        ev = _evidencia()
        if sujeto is None:
            ev.pop("subject")
        else:
            ev["subject"] = sujeto
        rev = lb.revision(ev)
        t.igual("E-14 %s: incompleta" % caso, "REVIEW_INCOMPLETE", rev["result"])
        t.contiene("E-14 %s: con el estado" % caso, "EVIDENCE_INCOMPLETE",
                   " ".join(rev["states"]))
        t.contiene("E-14 %s: y el motivo" % caso, "sobre que es", " | ".join(rev["issues"]))

    t.igual("E-14 con sujeto cumple", "COMPLIANT", lb.revision(_evidencia())["result"])


def test_e15_sin_linea_base_no_se_cumple_al_vacio(t):
    """E-15 — ausente, ilegible o invalida: `NORMATIVE_BASELINE_UNRESOLVED`."""
    for caso, doc in (("vacia", {}),
                      ("sin fuentes", {"version": "1.0", "authority": "x"}),
                      ("invalida", _base(_fuente("X", "NO_EXISTE")))):
        rev = lb.revision(_evidencia(), doc=doc)
        t.igual("E-15 %s: incompleta" % caso, "REVIEW_INCOMPLETE", rev["result"])
        t.contiene("E-15 %s: con el estado" % caso, "NORMATIVE_BASELINE_UNRESOLVED",
                   " ".join(rev["states"]))
        t.verdadero("E-15 %s: nunca cumple" % caso, rev["result"] != "COMPLIANT")

    # Ausente de verdad: un arbol sin el archivo.
    tmp = tempfile.mkdtemp(prefix="o1-sin-linea")
    try:
        binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "orquestacion"
        reglas_h = Path(tmp) / ".claude" / "harness" / "reglas"
        (reglas_h / "desarrollo").mkdir(parents=True)
        (reglas_h / "secretos.patrones.json").write_text("{}", encoding="utf-8")
        binario.mkdir(parents=True)
        desde = binario / "linea_base.py"
        desde.write_text("# marcador\n", encoding="utf-8")
        try:
            lb.cargar(str(desde))
            t.verdadero("E-15 ausente: se rechaza", False)
        except lb.LineaBaseInvalida as e:
            t.contiene("E-15 ausente: se rechaza con su motivo", lb.ARCHIVO, str(e))
        rev = lb.revision({"subject": {"id": "u"}, "standardResults": [_resultado()]},
                          desde=str(desde))
        t.igual("E-15 ausente: la review queda incompleta", "REVIEW_INCOMPLETE", rev["result"])
        t.contiene("E-15 ausente: con el estado", "NORMATIVE_BASELINE_UNRESOLVED",
                   " ".join(rev["states"]))

        # Ilegible: el archivo esta y no es JSON. Es la otra mitad de la palabra del escenario.
        roto = Path(tmp) / ".claude" / "harness" / "reglas" / "desarrollo" / lb.ARCHIVO
        roto.write_text("{ esto no es json", encoding="utf-8")
        try:
            lb.cargar(str(desde))
            t.verdadero("E-15 ilegible: se rechaza", False)
        except lb.LineaBaseInvalida as e:
            t.contiene("E-15 ilegible: se rechaza con su motivo", lb.ARCHIVO, str(e))
        rev = lb.revision({"subject": {"id": "u"}, "standardResults": [_resultado()]},
                          desde=str(desde))
        t.igual("E-15 ilegible: la review queda incompleta", "REVIEW_INCOMPLETE", rev["result"])
        t.contiene("E-15 ilegible: con el estado", "NORMATIVE_BASELINE_UNRESOLVED",
                   " ".join(rev["states"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- El reuso de los resultados que ya existen ---------------------------------

def test_e16_los_resultados_de_es0901_entran_como_evidencia(t):
    """E-16 (O1-13) — con su estandar, su regla y su resultado, y se cuentan."""
    declarados = [_resultado("ES0901", "D1"), _resultado("ES0901", "G1"),
                  _resultado("ES0901", "P1", "NOT_APPLICABLE")]
    rev = lb.revision(_evidencia(resultados=declarados))
    t.igual("E-16 entran los tres", 3, len(rev["reusedResults"]))
    t.igual("E-16 con sus reglas", ["D1", "G1", "P1"],
            sorted(r["rule"] for r in rev["reusedResults"]))
    t.igual("E-16 y sus claves compuestas", ["ES0901.D1", "ES0901.G1", "ES0901.P1"],
            sorted(r["ruleKey"] for r in rev["reusedResults"]))
    t.igual("E-16 conservando su resultado", "NOT_APPLICABLE",
            [r for r in rev["reusedResults"] if r["rule"] == "P1"][0]["result"])
    t.igual("E-16 la review cumple", "COMPLIANT", rev["result"])

    # Un resultado que no dice de que estandar sale no es evidencia de nada.
    roto = lb.revision(_evidencia(resultados=[{"result": "COMPLIANT"}]))
    t.igual("E-16 sin estandar ni regla: incompleta", "REVIEW_INCOMPLETE", roto["result"])
    t.contiene("E-16 con el estado", "EVIDENCE_INCOMPLETE", " ".join(roto["states"]))


def test_e17_los_resultados_de_es0902_entran_igual(t):
    """E-17 (O1-14) — y uno tal como sale de `seguridad.resultado` se consume sin traducir."""
    senales = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    crudo = seguridad.resultado("Vu2", {"controlResults": {
        c["id"]: {"result": "PASS", "evidence": ["acta"]}
        for c in seguridad.controles_de("Vu2", MATRIZ)}}, senales, MATRIZ)
    t.igual("E-17 el resultado crudo cumple", "COMPLIANT", crudo["result"])

    base = _base(_fuente("ES0902", "LOADED", "CURRENT"))
    rev = lb.revision(_evidencia(base, resultados=[crudo]))
    t.igual("E-17 entra tal como vino", 1, len(rev["reusedResults"]))
    fila = rev["reusedResults"][0]
    t.igual("E-17 con su estandar", "ES0902", fila["standard"])
    t.igual("E-17 con su regla", "Vu2", fila["rule"])
    t.igual("E-17 con su clave compuesta", "ES0902.Vu2", fila["ruleKey"])
    t.igual("E-17 y su resultado", "COMPLIANT", fila["result"])
    t.igual("E-17 la review cumple", "COMPLIANT", rev["result"])

    # 🔴 Un resultado que cita una fuente que la linea base no declara cargada no alcanza.
    ajeno = lb.revision(_evidencia(base, resultados=[_resultado("ES0901", "D1")]))
    t.contiene("E-17 una fuente no cargada se dice", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
               " ".join(ajeno["states"]))
    t.verdadero("E-17 y no cumple", ajeno["result"] != "COMPLIANT")


def test_e18_o1_no_reejecuta_ningun_control(t):
    """E-18 — con `seguridad.resultado` roto la review sigue; y el modulo no mira controles."""
    original = seguridad.resultado

    def explota(*a, **k):
        raise AssertionError("O1 no puede reejecutar un control")

    seguridad.resultado = explota
    try:
        rev = lb.revision(_evidencia())
        t.igual("E-18 la review resuelve sin reejecutar nada", "COMPLIANT", rev["result"])
    finally:
        seguridad.resultado = original

    fuente = (BIN / "orquestacion" / "linea_base.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    literales = {n.value for n in ast.walk(arbol)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    literales -= docs
    t.verdadero("E-18 el modulo no lee `controlResults`", "controlResults" not in literales)
    t.verdadero("E-18 no conoce PASS", "PASS" not in literales)
    t.verdadero("E-18 ni FAIL", "FAIL" not in literales)
    for archivo in sorted((CONTROLES / "checks").glob("*.py")):
        t.verdadero("E-18 no nombra a %s" % archivo.stem, archivo.stem not in fuente)


def test_e19_sin_resultados_no_hay_nada_que_reusar(t):
    """E-19 — O1 se contesta con lo que ya se midio; sin nada medido, incompleta."""
    for caso, resultados in (("lista vacia", []), ("sin la clave", None)):
        ev = _evidencia(resultados=resultados or [])
        if caso == "sin la clave":
            ev.pop("standardResults")
        rev = lb.revision(ev)
        t.igual("E-19 %s: incompleta" % caso, "REVIEW_INCOMPLETE", rev["result"])
        t.contiene("E-19 %s: con el estado" % caso, "EVIDENCE_INCOMPLETE",
                   " ".join(rev["states"]))
        t.contiene("E-19 %s: y el motivo" % caso, "nada que reusar", " | ".join(rev["issues"]))
        t.verdadero("E-19 %s: nunca cumple" % caso, rev["result"] != "COMPLIANT")


def test_e20_un_resultado_que_falla_impide_cumplir(t):
    """E-20 (O1-15) — NON_COMPLIANT titula, aun con estados sin resolver al lado."""
    rev = lb.revision(_evidencia(resultados=[_resultado("ES0901", "D1", "COMPLIANT"),
                                             _resultado("ES0901", "D7", "NON_COMPLIANT")]))
    t.igual("E-20 la review no cumple", "NON_COMPLIANT", rev["result"])
    t.contiene("E-20 y nombra la regla que falla", "ES0901.D7", " | ".join(rev["issues"]))

    # 🔴 Con la linea base como vino —incompleta para siempre— el fallo sigue titulando.
    mezcla = lb.revision({"subject": {"id": "u"},
                          "standardResults": [_resultado("ES0901", "D7", "NON_COMPLIANT")]})
    t.igual("E-20 con la linea base real tambien titula", "NON_COMPLIANT", mezcla["result"])
    t.contiene("E-20 y lo incompleto no desaparece", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
               " ".join(mezcla["states"]))

    # Un resultado sin resolver no es un fallo: deja la review incompleta.
    sin_resolver = lb.revision(_evidencia(resultados=[_resultado("ES0901", "D7", "UNRESOLVED")]))
    t.igual("E-20 un resultado sin resolver deja incompleta", "REVIEW_INCOMPLETE",
            sin_resolver["result"])

    # Y la fila de O1 hereda el NON_COMPLIANT.
    fila = seguridad.resultado("O1", _evidencia(
        resultados=[_resultado("ES0901", "D7", "NON_COMPLIANT")]), {})
    t.igual("E-20 la fila no cumple", "NON_COMPLIANT", fila["result"])


# -- La excepcion contractual --------------------------------------------------

def test_e21_contrato_solo_no_levanta_nada(t):
    """E-21 (O1-16) — sin aprobacion de ASI la obligacion sigue en pie."""
    ev = _evidencia(resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
                    overrides=[_excepcion(asi=None)])
    rev = lb.revision(ev)
    t.igual("E-21 la review no cumple", "NON_COMPLIANT", rev["result"])
    t.contiene("E-21 la excepcion queda sin resolver", "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED",
               " ".join(rev["states"]))
    t.contiene("E-21 y se dice que falta", "aprobacion de ASI", " | ".join(rev["issues"]))
    t.vacio("E-21 no se concedio ninguna", rev["overrides"])
    t.contiene("E-21 el resultado que falla sigue pesando", "ES0901.D1",
               " | ".join(rev["issues"]))

    # Y al reves: aprobacion de ASI sin contrato tampoco.
    sin_contrato = lb.revision(_evidencia(
        resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
        overrides=[_excepcion(contrato=None)]))
    t.igual("E-21 ASI sin contrato tampoco", "NON_COMPLIANT", sin_contrato["result"])
    t.vacio("E-21 y no concede", sin_contrato["overrides"])


def test_e22_contrato_y_asi_conceden_la_excepcion(t):
    """E-22 (O1-17) — queda como observacion, con la excepcion pegada. No desaparece."""
    ev = _evidencia(resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
                    overrides=[_excepcion()])
    rev = lb.revision(ev)
    t.igual("E-22 cumple con observaciones", "COMPLIANT_WITH_OBSERVATIONS", rev["result"])
    t.igual("E-22 la excepcion viaja en el resultado", 1, len(rev["overrides"]))
    t.igual("E-22 con la regla que alcanza", "ES0901.D1", rev["overrides"][0]["ruleKey"])
    t.contiene("E-22 y su motivo", "el contrato lo permite", rev["overrides"][0]["reason"])
    fila = [r for r in rev["reusedResults"] if r["rule"] == "D1"][0]
    t.verdadero("E-22 el resultado exceptuado la lleva adentro", bool(fila.get("override")))
    t.verdadero("E-22 y la excepcion esta concedida", fila["override"]["granted"])
    t.contiene("E-22 el motivo dice que quedo como observacion", "observacion",
               " | ".join(rev["issues"]))

    # 🔴 Y no barre el fallo: sin la excepcion, el mismo caso no cumple.
    t.igual("E-22 sin la excepcion no cumple", "NON_COMPLIANT",
            lb.revision(_evidencia(
                resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")]))["result"])


def test_e23_el_mecanismo_es_el_de_es0902(t):
    """E-23 — lo local no sostiene ninguna mitad, y una excepcion no derrama."""
    for local in seguridad.FUENTES_LOCALES:
        rev = lb.revision(_evidencia(
            resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
            overrides=[_excepcion(contrato=local, asi=local)]))
        t.verdadero("E-23 `%s` no exime" % local, rev["result"] != "COMPLIANT_WITH_OBSERVATIONS")
        t.vacio("E-23 `%s` no concede nada" % local, rev["overrides"])

    # Una excepcion alcanza solo a las reglas que nombra.
    otra = lb.revision(_evidencia(resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
                                  overrides=[_excepcion(reglas=("ES0901.D7",))]))
    t.igual("E-23 no alcanza a una regla que no nombra", "NON_COMPLIANT", otra["result"])

    # 🔴 Ni por el id local: `D1` no identifica una regla, y la de ES0902 no se cobra la otra.
    ajena = lb.revision(_evidencia(resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
                                   overrides=[_excepcion(reglas=("ES0902.D1",))]))
    t.igual("E-23 la clave del otro estandar no alcanza", "NON_COMPLIANT", ajena["result"])

    # Y es el mismo codigo: la excepcion se resuelve con `seguridad.excepcion`.
    fuente = (BIN / "orquestacion" / "linea_base.py").read_text(encoding="utf-8")
    t.contiene("E-23 se reusa `seguridad.excepcion_de`", "seguridad.excepcion_de", fuente)
    t.verdadero("E-23 y no hay una lista de fuentes propia",
                "FUENTES_DE_CONTRATO" not in fuente and "ASI_APPROVAL" not in fuente)


# -- La frontera de la aprobacion ----------------------------------------------

def test_e24_cumplir_o1_no_aprueba_nada(t):
    """E-24 (O1-18) — ningun valor del resultado es un estado oficial."""
    ev = _evidencia()
    rev = lb.revision(ev)
    t.igual("E-24 la review cumple", "COMPLIANT", rev["result"])
    fila = seguridad.resultado("O1", ev, {})
    t.igual("E-24 y la fila tambien", "COMPLIANT", fila["result"])

    for nombre, dato in (("review", rev), ("fila", fila)):
        valores = set(_valores(dato))
        oficiales = sorted(valores & set(evaluacion.ESTADOS_OFICIALES))
        t.igual("E-24 el %s no lleva ningun estado oficial" % nombre, [], oficiales)
        serializado = json.dumps(dato, ensure_ascii=False, default=str)
        t.no_contiene("E-24 el %s no dice APPROVED" % nombre, "APPROVED", serializado)
        t.no_contiene("E-24 el %s no dice SECURITY_APPROVED" % nombre, "SECURITY_APPROVED",
                      serializado)

    # 🔴 Y el estado oficial no se mueve: sigue exigiendo procedencia externa con evidencia.
    for productor in evaluacion.PRODUCTORES_INTERNOS:
        estado = evaluacion.estado_oficial({"state": "APPROVED", "producer": productor,
                                            "evidence": ["review-o1-compliant"]})
        t.igual("E-24 `%s` no puede aprobar" % productor, "OFFICIAL_STATUS_UNRESOLVED",
                estado["state"])
        t.verdadero("E-24 `%s` con su estado" % productor,
                    "SECURITY_INTERNAL_PRODUCER_CANNOT_SET_OFFICIAL_STATE" in estado["states"])
    t.verdadero("E-24 el modulo no nombra ningun estado oficial",
                not any(e in (BIN / "orquestacion" / "linea_base.py").read_text(encoding="utf-8")
                        for e in ("APPROVED", "REJECTED", "IN_ASSESSMENT")))


def test_e25_los_cuatro_resultados_son_los_de_revisiones(t):
    """E-25 — importados y no redefinidos, y no hay un quinto."""
    t.igual("E-25 son cuatro", 4, len(lb.RESULTADOS))
    t.igual("E-25 y son estos",
            ["COMPLIANT", "COMPLIANT_WITH_OBSERVATIONS", "NON_COMPLIANT", "REVIEW_INCOMPLETE"],
            sorted(lb.RESULTADOS))
    t.igual("E-25 el que cumple es el de revisiones", revisiones.CUMPLE, lb.CUMPLE)
    t.igual("E-25 el de observaciones tambien", revisiones.CUMPLE_CON_OBSERVACIONES,
            lb.CUMPLE_CON_OBSERVACIONES)
    t.igual("E-25 el que no cumple tambien", revisiones.NO_CUMPLE, lb.NO_CUMPLE)
    t.igual("E-25 y el incompleto tambien", revisiones.INCOMPLETA, lb.INCOMPLETA)

    fuente = (BIN / "orquestacion" / "linea_base.py").read_text(encoding="utf-8")
    for literal in ('"COMPLIANT"', '"NON_COMPLIANT"', '"REVIEW_INCOMPLETE"',
                    '"COMPLIANT_WITH_OBSERVATIONS"'):
        t.verdadero("E-25 %s no se redefine" % literal, literal not in fuente)

    # Los cuatro salen de casos reales, no de leer la constante.
    emitidos = {lb.revision(_evidencia())["result"],
                lb.revision(_evidencia(resultados=[_resultado("ES0901", "D1", "OVERRIDDEN")])
                            )["result"],
                lb.revision(_evidencia(
                    resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")]))["result"],
                lb.revision(_evidencia(resultados=[]))["result"]}
    t.igual("E-25 los cuatro se emiten", sorted(lb.RESULTADOS), sorted(emitidos))


# -- La traza, los agentes y el registro ---------------------------------------

def test_e26_todo_resultado_conserva_la_traza(t):
    """E-26 (O1-20) — ES0902 / 6.2 / §3 / O1 y la clave compuesta, por todos los caminos."""
    caminos = (
        ("cumple", _evidencia()),
        ("no cumple", _evidencia(resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")])),
        ("observaciones", _evidencia(
            resultados=[_resultado("ES0901", "D1", "NON_COMPLIANT")],
            overrides=[_excepcion()])),
        ("incompleta", {"subject": {"id": "u"}, "standardResults": [_resultado()]}),
        ("sin sujeto", {"standardResults": [_resultado()]}),
        ("sin linea base", {"subject": {"id": "u"}, "normativeBaseline": {},
                            "standardResults": [_resultado()]}),
    )
    for nombre, ev in caminos:
        rev = lb.revision(ev)
        t.igual("E-26 %s: la traza entera" % nombre, TRAZA, rev["source"])
        fila = seguridad.resultado("O1", ev, {})
        t.igual("E-26 %s: la fila cita la regla" % nombre, "O1", fila["rule"])
        t.igual("E-26 %s: con la clave compuesta" % nombre, "ES0902.O1", fila["ruleKey"])
        t.igual("E-26 %s: y su estandar" % nombre, "ES0902", fila["source"]["standard"])
        t.igual("E-26 %s: con su version" % nombre, "6.2", fila["source"]["version"])
        t.igual("E-26 %s: la review lleva la traza adentro" % nombre, TRAZA,
                fila["review"]["source"])

    t.igual("E-26 la trazabilidad del modulo es la misma", TRAZA, lb.trazabilidad())
    t.igual("E-26 y la seccion es la 3", "3", lb.SECCION)


def test_e27_no_se_crea_ningun_agente_ni_skill(t):
    """E-27 (O1-19) — los mismos diez agentes, las mismas cuatro skills de dev-security."""
    registro = c_reg.cargar()
    ids = sorted(a["id"] for a in registro["agents"])
    t.igual("E-27 siguen siendo diez", 10, len(ids))
    t.igual("E-27 y son los mismos",
            ["dev-architecture", "dev-backend", "dev-devops", "dev-frontend", "dev-integration",
             "dev-orchestrator", "dev-quality", "dev-refutador", "dev-security",
             "dev-tool-builder"], ids)
    de_security = [a for a in registro["agents"] if a["id"] == "dev-security"][0]
    t.igual("E-27 las cuatro skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in de_security.get("skills") or []))

    # 🔴 Y ningun artefacto de O1 nombra un agente o una skill que no exista.
    artefactos = (CONTROLES / "policies" / ("%s.md" % POLICY),
                  CONTROLES / "reviews" / ("%s.md" % REVIEW),
                  REGLAS / "es0902-o1-governance.md",
                  BIN / "orquestacion" / "linea_base.py")
    conocidos = set(ids) | {s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    for archivo in artefactos:
        t.verdadero("E-27 %s existe" % archivo.name, archivo.is_file())
        texto = archivo.read_text(encoding="utf-8")
        nombrados = {p.strip("`*_.,:;()[]\"'") for p in texto.split()
                     if p.strip("`*_.,:;()[]\"'").startswith("dev-")}
        t.vacio("E-27 %s no nombra ninguno nuevo" % archivo.name,
                sorted(nombrados - conocidos))


def test_e28_los_dos_controles_quedan_instalados(t):
    """E-28 — 40 en el registro, sin archivos sueltos, y el hueco de O1 desaparece."""
    reporte = c_controles.reporte()
    t.igual("E-28 son cuarenta y dos controles", 42, reporte["summary"]["declaredControls"])
    t.verdadero("E-28 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-28 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-28 ningun archivo suelto", [], reporte["undeclared"])
    t.vacio("E-28 sin errores de schema", reporte["schemaErrors"])
    for control in (POLICY, REVIEW):
        t.igual("E-28 %s esta INSTALLED" % control, "INSTALLED", reporte["controls"].get(control))

    resolucion = seguridad.resolver({s: True for s in seguridad.senales_declaradas(MATRIZ)})
    faltan = {f["id"] for f in seguridad.controles_no_instalados(resolucion)}
    for control in (POLICY, REVIEW):
        t.verdadero("E-28 %s ya no figura como hueco" % control, control not in faltan)
    t.igual("E-28 quedan veintisiete huecos", 27,
            len(seguridad.controles_no_instalados(resolucion)))

    # La tupla normativa de los dos es la de O1, con su seccion.
    for control in (POLICY, REVIEW):
        fuentes = c_controles.fuentes_de(c_controles.control(control, REGISTRO))
        t.igual("E-28 %s tiene una fuente" % control, 1, len(fuentes))
        t.igual("E-28 %s sale de ES0902" % control, "ES0902", fuentes[0]["standard"])
        t.igual("E-28 %s de la version 6.2" % control, "6.2", fuentes[0]["version"])
        t.igual("E-28 %s de la seccion 3" % control, "3", fuentes[0]["section"])
        t.igual("E-28 %s de la regla O1" % control, "O1", fuentes[0]["rule"])
