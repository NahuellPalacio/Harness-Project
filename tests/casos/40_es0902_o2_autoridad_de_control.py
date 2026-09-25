# ES0902 §3 O2: quien controla la seguridad, y por que el harness no puede ser.
#
# Escenarios E-01 a E-28 de docs/cambios/es0902-o2-autoridad-de-control-de-seguridad/spec.md.
#
# 🔴 Lo que se verifica es que O2 NO se pueda poner en verde barato. Las tres formas de hacerlo son
# confundir al que ejecuta con el que responde, deducir la pertenencia al GCABA de algo que
# cualquiera puede escribir, y reusar en silencio una asignacion vieja. Los escenarios que importan
# son esos tres, mas el unico camino a FAIL — que acusa a un organismo y por eso no se inventa.
#
# 🔴 E-24 es el que sostiene a los demas: se arma UN caso que aprueba y se lo rompe de siete
# maneras. Un archivo que solo arma casos que fallan pasa con un check que nunca aprueba.
import ast
import copy
import importlib.util
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
from orquestacion import seguridad                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import matriz as c_matriz             # noqa: E402
from orquestacion import roster as c_roster             # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "security-control-authority-evidence.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "o2_autoridad")
MATRIZ = seguridad.cargar()
REGISTRO = c_controles.cargar()

# Los dos ids, escritos a mano. Es la unica forma de que renombrarlos rompa algo.
POLICY = "gcba-security-control-authority-required"
CHEQUEO = "security-control-authority-evidence"

# Los nueve estados, clavados por literal. Un bucle sobre la constante se achica junto con lo que
# verifica, y renombrar un valor deja el test verde.
LOS_9 = ("PASS", "FAIL",
         "SECURITY_CONTROL_AUTHORITY_UNRESOLVED",
         "GCABA_MEMBERSHIP_UNRESOLVED",
         "SECURITY_AUTHORITY_SCOPE_UNRESOLVED",
         "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED",
         "SECURITY_AUTHORITY_EVIDENCE_EXPIRED",
         "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE",
         "AUTHORITY_EVIDENCE_INSUFFICIENT")

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": "O2"}

HOY = "2026-09-22"

OBJETIVO = {"id": "u-1", "scope": {"type": "PROJECT", "value": "tramites"}}

# 🔴 La autoridad que APRUEBA. Todo lo demas de este archivo sale de romperla. Si esta dejara de
# aprobar, los veintitantos escenarios que la rompen seguirian en verde sin verificar nada.
AUTORIDAD = {
    "authorityId": "aut-1",
    "organization": {"name": "Direccion General de Seguridad de la Informacion",
                     "gcabaMembership": "VERIFIED"},
    "responsibilities": ["SECURITY_CONTROL"],
    "scope": {"type": "PROJECT", "value": "tramites"},
    "effectiveFrom": "2026-01-01",
    "effectiveTo": "2027-01-01",
    "evidence": [{"sourceType": "OFFICIAL_GCBA_DOCUMENT",
                  "reference": "acta de asignacion 12/2026"}],
}


def _autoridad(**cambios):
    a = copy.deepcopy(AUTORIDAD)
    a.update(cambios)
    return a


def _ev(autoridades=None, objetivo=None, fecha=HOY):
    """El resultado del check. Sin autoridades, la que aprueba."""
    caso = {"target": copy.deepcopy(objetivo if objetivo is not None else OBJETIVO),
            "evaluationDate": fecha,
            "authorities": copy.deepcopy(
                [AUTORIDAD] if autoridades is None else autoridades)}
    return CHECK.evaluar(caso)


def _estado(autoridades=None, objetivo=None, fecha=HOY):
    return _ev(autoridades, objetivo, fecha)["state"]


def _valores(dato):
    """Todos los strings que hay adentro, a cualquier profundidad."""
    if isinstance(dato, dict):
        return [x for v in dato.values() for x in _valores(v)]
    if isinstance(dato, (list, tuple)):
        return [x for v in dato for x in _valores(v)]
    return [dato] if isinstance(dato, str) else []


def _literales(ruta):
    """Las cadenas literales del modulo, sin los docstrings.

    🔴 Un docstring puede explicar de que NO habla la regla; lo que el modulo no puede es
    devolverlo. Barrer el texto entero confunde las dos cosas, que es como se apaga un guard.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    return {n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)} - docs


# -- La fila, que no se toca ---------------------------------------------------

def test_e01_o2_sigue_always_con_cero_senales(t):
    """E-01 — `ALWAYS`, `signals` vacio, y aplica con el diccionario vacio."""
    o2 = seguridad.regla("O2", MATRIZ)
    t.igual("E-01 el modo es ALWAYS", "ALWAYS", o2["applicability"]["mode"])
    t.igual("E-01 y no declara ninguna senal", [], o2["applicability"].get("signals"))
    estado, faltan = seguridad.resolver_regla(o2, {})
    t.igual("E-01 con cero senales igual aplica", "APPLICABLE", estado)
    t.igual("E-01 y no falta ninguna", [], faltan)
    t.igual("E-01 la clave es la compuesta", "ES0902.O2", o2["ruleKey"])


def test_e02_el_dueno_sigue_siendo_dev_security(t):
    """E-02 — uno solo, y declarado en el registro de agentes."""
    o2 = seguridad.regla("O2", MATRIZ)
    t.igual("E-02 el dueno es dev-security", ["dev-security"], o2["primaryAgents"])
    declarados = {a["id"] for a in c_reg.cargar()["agents"]}
    t.verdadero("E-02 y esta declarado", "dev-security" in declarados)


def test_e03_la_policy_y_el_check_con_su_id_literal(t):
    """E-03 — una policy, un check, cero reviews, con estos ids escritos a mano."""
    o2 = seguridad.regla("O2", MATRIZ)
    t.igual("E-03 una sola policy", [POLICY], o2["policies"])
    t.igual("E-03 un solo check", [CHEQUEO], o2["checks"])
    t.igual("E-03 y ninguna review", [], o2["reviews"])
    t.igual("E-03 la policy se llama asi", "gcba-security-control-authority-required",
            o2["policies"][0])
    t.igual("E-03 el check se llama asi", "security-control-authority-evidence", o2["checks"][0])
    t.igual("E-03 el modulo usa el id del check", CHEQUEO, CHECK.CONTROL)
    t.igual("E-03 y se declara del tipo CHECK", "CHECK", CHECK.TIPO)


def test_e04_o2_no_entra_en_los_algoritmos(t):
    """E-04 — O2 no es una de las de la tabla: sale por el camino generico.

    La tabla tenia nueve cuando O2 se instalo; ES0902 C3 agrego la decima, con su razon declarada
    en su spec. Lo que este escenario verifica no cambio: O2 no esta.
    """
    t.igual("E-04 diez algoritmos", 10, len(seguridad.ALGORITMOS))
    t.verdadero("E-04 O2 no tiene algoritmo propio", "O2" not in seguridad.ALGORITMOS)
    t.igual("E-04 y son estos", ["C2", "C3", "G2", "G3", "G4", "O1", "Ve2", "Vu10", "Vu4", "Vu9"],
            sorted(seguridad.ALGORITMOS))

    # 🔴 Y el resultado de la fila sale del camino generico: contra el resultado del control.
    senales = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    ids = [c["id"] for c in seguridad.controles_de("O2", MATRIZ)]
    con_pass = {"controlResults": {cid: {"result": "PASS", "evidence": ["acta-%s" % cid]}
                                   for cid in ids}}
    t.igual("E-04 con evidencia de PASS la fila cumple", "COMPLIANT",
            seguridad.resultado("O2", con_pass, senales, MATRIZ)["result"])
    con_fail = {"controlResults": {ids[0]: {"result": "FAIL", "evidence": ["acta"]}}}
    t.igual("E-04 con un control en FAIL no cumple", "NON_COMPLIANT",
            seguridad.resultado("O2", con_fail, senales, MATRIZ)["result"])
    t.igual("E-04 y sin evidencia queda sin resolver", "UNRESOLVED",
            seguridad.resultado("O2", {}, senales, MATRIZ)["result"])


def test_e05_instalar_o2_no_agrega_filas(t):
    """E-05 — 21 y 24, y la matriz sigue valida."""
    t.igual("E-05 ES0902 sigue con 21 reglas", 21, len(MATRIZ["rules"]))
    t.igual("E-05 ES0901 sigue con 24", 24, len(c_matriz.reglas()))
    veredicto, errores = seguridad.validar(MATRIZ)
    t.igual("E-05 la matriz sigue valida", "NORMATIVE_MATRIX_VALID", veredicto)
    t.vacio("E-05 sin errores", errores)


# -- El registro, que es del proyecto -----------------------------------------

def test_e06_el_registro_se_instala_vacio(t):
    """E-06 — cero autoridades, valida contra su schema, y carga instalado."""
    doc = CHECK.cargar()
    t.igual("E-06 se instala vacio", [], doc["authorities"])
    t.igual("E-06 con su version", "1.0", doc["version"])
    t.vacio("E-06 valida contra el schema", CHECK.validar_schema(doc))

    # 🔴 Instalado, `reglas/` cuelga a otra altura. Verde donde corre la suite y muerto donde
    # corre el harness es el defecto que esto esta para encontrar.
    fuente = RUTA_CHECK.read_text(encoding="utf-8")
    t.contiene("E-06 el check busca con roster", "ruta_de_regla", fuente)
    tmp = tempfile.mkdtemp(prefix="o2-inst")
    try:
        binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "controles"
        reglas_h = Path(tmp) / ".claude" / "harness" / "reglas"
        (reglas_h / "desarrollo").mkdir(parents=True)
        binario.mkdir(parents=True)
        (reglas_h / "secretos.patrones.json").write_text("{}", encoding="utf-8")
        shutil.copy(str(REGLAS / CHECK.ARCHIVO), str(reglas_h / "desarrollo" / CHECK.ARCHIVO))
        desde = binario / "check.py"
        desde.write_text("# marcador\n", encoding="utf-8")
        t.verdadero("E-06 roster lo encuentra instalado",
                    bool(c_roster.ruta_de_regla(CHECK.ARCHIVO, str(desde))))
        t.igual("E-06 y carga instalado", [], CHECK.cargar(str(desde))["authorities"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e07_sin_autoridad_declarada_queda_sin_resolver(t):
    """E-07 — ni PASS ni FAIL: `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`."""
    r = _ev([])
    t.igual("E-07 el estado", "SECURITY_CONTROL_AUTHORITY_UNRESOLVED", r["state"])
    t.verdadero("E-07 no aprueba", not CHECK.aprueba(r))
    t.verdadero("E-07 y no reprueba", r["state"] != "FAIL")
    t.contiene("E-07 con su motivo", "no hay ninguna autoridad de control declarada", r["reason"])
    t.igual("E-07 y no informa ninguna autoridad", None, r["authority"])

    # Y con el registro instalado tal como viene, lo mismo.
    instalado = CHECK.evaluar({"target": OBJETIVO, "evaluationDate": HOY})
    t.igual("E-07 el registro instalado da lo mismo",
            "SECURITY_CONTROL_AUTHORITY_UNRESOLVED", instalado["state"])


def test_e08_el_schema_rechaza_lo_que_no_declara(t):
    """E-08 — las cuatro capas, con un valor invalido cada una."""
    def doc(autoridad):
        return {"version": "1.0", "authorities": [autoridad]}

    t.vacio("E-08 la autoridad buena valida", CHECK.validar_schema(doc(AUTORIDAD)))

    casos = (
        ("clave de mas", _autoridad(executedBy="proveedor")),
        ("sourceType ajeno", _autoridad(evidence=[{"sourceType": "README", "reference": "x"}])),
        ("membresia inventada", _autoridad(
            organization={"name": "X", "gcabaMembership": "PROBABLEMENTE"})),
        ("tipo de alcance inventado", _autoridad(scope={"type": "AREA", "value": "x"})),
    )
    for caso, autoridad in casos:
        errores = CHECK.validar_schema(doc(autoridad))
        t.verdadero("E-08 %s: no valida" % caso, bool(errores))

    # Y el registro entero tambien: una clave de mas arriba de todo se rechaza igual.
    t.verdadero("E-08 una clave de mas en la raiz no valida",
                bool(CHECK.validar_schema({"version": "1.0", "authorities": [], "extra": 1})))


# -- La autoridad no es quien ejecuta -----------------------------------------

def test_e09_ejecutar_no_es_controlar(t):
    """E-09 — las cinco responsabilidades de ejecucion, una por una."""
    for responsabilidad in ("SECURITY_SCANNING", "SECURITY_REMEDIATION", "DEVELOPMENT",
                            "HOSTING", "CONSULTING"):
        r = _ev([_autoridad(responsibilities=[responsabilidad])])
        t.igual("E-09 `%s` no establece autoridad" % responsabilidad,
                "AUTHORITY_EVIDENCE_INSUFFICIENT", r["state"])
        t.contiene("E-09 `%s` y se dice por que" % responsabilidad, "ejecutar no es controlar",
                   r["reason"])

    # Una responsabilidad que el check no conoce tampoco cuenta: no se asume que sea control.
    t.igual("E-09 una responsabilidad desconocida tampoco",
            "AUTHORITY_EVIDENCE_INSUFFICIENT", _estado([_autoridad(responsibilities=["OTRA"])]))
    t.igual("E-09 ni la lista vacia",
            "AUTHORITY_EVIDENCE_INSUFFICIENT", _estado([_autoridad(responsibilities=[])]))
    # Y la que si cuenta, cuenta.
    t.igual("E-09 SECURITY_CONTROL si", "PASS", _estado())


def test_e10_un_ejecutor_externo_no_invalida_la_autoridad(t):
    """E-10 — delegar la ejecucion no mueve quien responde."""
    proveedor = _autoridad(authorityId="aut-proveedor",
                           organization={"name": "Proveedor SA", "gcabaMembership": "NOT_GCABA"},
                           responsibilities=["SECURITY_SCANNING", "SECURITY_REMEDIATION"])
    r = _ev([AUTORIDAD, proveedor])
    t.igual("E-10 sigue aprobando", "PASS", r["state"])
    t.igual("E-10 y la autoridad es el organismo",
            "Direccion General de Seguridad de la Informacion", r["authority"]["organization"])
    t.verdadero("E-10 el proveedor se consideró y no controla",
                any(c["authorityId"] == "aut-proveedor" for c in r["considered"]))

    # 🔴 Y al reves: el proveedor solo, sin el organismo, no aprueba y tampoco reprueba por ser
    # ajeno — lo que falta es la responsabilidad de control, no la pertenencia.
    t.igual("E-10 el proveedor solo no alcanza", "AUTHORITY_EVIDENCE_INSUFFICIENT",
            _estado([proveedor]))


def test_e11_el_harness_no_puede_ser_la_autoridad(t):
    """E-11 — no hay camino de un id de agente a una autoridad, y decir que se es uno no alcanza.

    🔴 El barrido es sobre los literales OPERATIVOS. La prosa del modulo nombra a `dev-security`
    a proposito —es donde la frontera queda declarada— y prohibirselo seria prohibir la linea que
    dice que el harness no puede ser la autoridad. Lo que no puede es DEVOLVERLO ni LEERLO.
    """
    literales = _literales(RUTA_CHECK)
    registro = c_reg.cargar()
    agentes = {a["id"] for a in registro["agents"]}
    skills = {s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    t.verdadero("E-11 hay agentes y skills que barrer", bool(agentes) and bool(skills))
    for nombre in sorted(agentes | skills):
        t.verdadero("E-11 ningun literal operativo nombra a `%s`" % nombre,
                    nombre not in literales)

    # 🔴 Y la mitad que importa: el modulo NO LEE el registro de agentes. Sin esa lectura no hay
    # camino de un id de agente a una autoridad, y eso no depende de como este escrita la prosa.
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")
            importados.update(a.name for a in nodo.names)
    t.verdadero("E-11 no importa el registro de agentes",
                "registro_agentes" not in importados)
    t.igual("E-11 y lo que importa es esto", ["io", "json", "orquestacion", "os", "re", "roster",
                                              "rutas", "sys", "tools"], sorted(importados))
    t.verdadero("E-11 ningun literal operativo nombra el archivo del registro de agentes",
                not any("agent-registry" in lit for lit in literales))

    # Una autoridad que dice ser el agente no establece nada por decirlo.
    agente = _autoridad(organization={"name": "dev-security", "gcabaMembership": "VERIFIED"},
                        evidence=[])
    t.igual("E-11 decir que se es dev-security no establece pertenencia",
            "GCABA_MEMBERSHIP_UNRESOLVED", _estado([agente]))
    # Ni con evidencia: lo que la evidencia sostiene es la pertenencia de la ORGANIZACION, y un
    # agente que trae un acta del GCABA sigue sin ser un organismo — pero eso no lo decide este
    # modulo, lo decide quien firma el acta. Lo que se verifica aca es que el nombre no abre
    # ningun camino propio.
    t.igual("E-11 el nombre del agente no tiene ningun camino propio", "PASS",
            _estado([_autoridad(organization={"name": "dev-security",
                                              "gcabaMembership": "VERIFIED"})]))


# -- La pertenencia al GCABA --------------------------------------------------

def test_e12_verified_sin_evidencia_no_alcanza(t):
    """E-12 — la etiqueta la escribe quien edita el archivo."""
    r = _ev([_autoridad(evidence=[])])
    t.igual("E-12 el estado", "GCABA_MEMBERSHIP_UNRESOLVED", r["state"])
    t.contiene("E-12 y se dice por que", "la etiqueta del archivo no establece la pertenencia",
               r["reason"])
    t.verdadero("E-12 no aprueba", not CHECK.aprueba(r))

    # Una evidencia sin referencia tampoco: una clase sin a que apuntar no es evidencia.
    t.igual("E-12 una evidencia sin referencia tampoco", "GCABA_MEMBERSHIP_UNRESOLVED",
            _estado([_autoridad(evidence=[{"sourceType": "OFFICIAL_GCBA_DOCUMENT",
                                           "reference": "  "}])]))
    # Y con evidencia de una de las seis clases, si.
    t.igual("E-12 con evidencia autoritativa si", "PASS", _estado())


def test_e13_la_pertenencia_no_se_deduce(t):
    """E-13 — las cinco formas de adivinarla, ninguna cambia el resultado."""
    formas = (
        ("el nombre del organismo", {"name": "Gobierno de la Ciudad de Buenos Aires - ASI",
                                     "gcabaMembership": "UNRESOLVED"}),
        ("el dominio del correo", {"name": "seguridad@buenosaires.gob.ar",
                                   "gcabaMembership": "UNRESOLVED"}),
        ("el namespace del repositorio", {"name": "gcba/seguridad",
                                          "gcabaMembership": "UNRESOLVED"}),
        ("el texto del proyecto", {"name": "Security: DGSEI",
                                   "gcabaMembership": "UNRESOLVED"}),
        ("el empleador declarado", {"name": "empleado del GCABA",
                                    "gcabaMembership": "UNRESOLVED"}),
    )
    for caso, organizacion in formas:
        t.igual("E-13 %s no establece pertenencia" % caso, "GCABA_MEMBERSHIP_UNRESOLVED",
                _estado([_autoridad(organization=organizacion)]))

    # 🔴 Y el modulo no lleva adentro ninguna de esas formas: ni un dominio, ni un namespace, ni
    # el nombre de un organismo. Cablear `DGSEI` seria normativa que ES0902 no da.
    literales = _literales(RUTA_CHECK)
    # Ningun literal ES el nombre de un organismo. `ASI_DGSEI_PROJECT_EVIDENCE` y
    # `GCABA_MEMBERSHIP_UNRESOLVED` llevan esas palabras adentro y son vocabulario del contrato:
    # lo que no puede haber es el organismo suelto, que seria normativa que ES0902 no da.
    for organismo in ("DGSEI", "ASI", "GCBA", "GCABA", "dev-security"):
        t.verdadero("E-13 el modulo no cablea el organismo `%s`" % organismo,
                    organismo not in literales)
    # Y ninguna de las formas de deducir: un dominio, un correo, un namespace, una direccion.
    for fuga in ("buenosaires", ".gob.ar", "@", "gcba/", "://"):
        t.verdadero("E-13 el modulo no lleva `%s`" % fuga,
                    not any(fuga in lit for lit in literales))


def test_e14_ajena_al_gcaba_es_el_unico_camino_a_fail(t):
    """E-14 — y acusa a alguien, asi que no sale de ningun otro lado."""
    ajena = _autoridad(organization={"name": "Proveedor SA", "gcabaMembership": "NOT_GCABA"})
    r = _ev([ajena])
    t.igual("E-14 el estado es FAIL", "FAIL", r["state"])
    t.contiene("E-14 y nombra a la organizacion", "Proveedor SA", r["reason"])
    t.contiene("E-14 y dice que consta ajena", "consta ajena al GCABA", r["reason"])

    # 🔴 Con un organismo del GCABA controlando al lado, una ajena NO reprueba: lo que hay son
    # dos organizaciones sin precedencia, y eso es un conflicto, no una acusacion.
    al_lado = _estado([AUTORIDAD, _autoridad(
        authorityId="aut-2",
        organization={"name": "Proveedor SA", "gcabaMembership": "NOT_GCABA"})])
    t.verdadero("E-14 con un organismo del GCABA al lado no reprueba", al_lado != "FAIL")
    t.igual("E-14 y lo que hay es un conflicto", "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE",
            al_lado)
    # 🔴 El barrido que importa: de todas las formas de que falte algo, ninguna da FAIL.
    faltantes = (
        ("sin registro", []),
        ("sin responsabilidad de control", [_autoridad(responsibilities=["SECURITY_SCANNING"])]),
        ("sin evidencia", [_autoridad(evidence=[])]),
        ("sin fecha de fin", [_autoridad(effectiveTo=None)]),
        ("vencida", [_autoridad(effectiveTo="2020-01-01")]),
        ("de otro alcance", [_autoridad(scope={"type": "PROJECT", "value": "otro"})]),
        ("en conflicto", [_autoridad(), _autoridad(authorityId="aut-2", organization={
            "name": "Otra", "gcabaMembership": "VERIFIED"})]),
    )
    for caso, autoridades in faltantes:
        t.verdadero("E-14 %s no es FAIL" % caso, _estado(autoridades) != "FAIL")


def test_e15_lo_que_falta_tiene_su_propio_estado(t):
    """E-15 — los siete que no aprueban y no acusan, cada uno desde su caso."""
    esperados = {
        "SECURITY_CONTROL_AUTHORITY_UNRESOLVED": [],
        "AUTHORITY_EVIDENCE_INSUFFICIENT": [_autoridad(responsibilities=["HOSTING"])],
        "GCABA_MEMBERSHIP_UNRESOLVED": [_autoridad(evidence=[])],
        "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED": [_autoridad(effectiveTo=None)],
        "SECURITY_AUTHORITY_EVIDENCE_EXPIRED": [_autoridad(effectiveTo="2020-01-01")],
        "SECURITY_AUTHORITY_SCOPE_UNRESOLVED": [
            _autoridad(scope={"type": "PROJECT", "value": "otro"})],
        "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE": [
            _autoridad(), _autoridad(authorityId="aut-2", organization={
                "name": "Otra Direccion", "gcabaMembership": "VERIFIED"})],
    }
    t.igual("E-15 son siete", 7, len(esperados))
    for estado, autoridades in sorted(esperados.items()):
        t.igual("E-15 %s se emite" % estado, estado, _estado(autoridades))
    t.igual("E-15 y son exactamente los siete que no aprueban ni acusan",
            sorted(esperados), sorted(CHECK.SIN_RESOLVER))


# -- El alcance ----------------------------------------------------------------

def test_e16_la_autoridad_de_otro_proyecto_no_cubre(t):
    """E-16 — `SECURITY_AUTHORITY_SCOPE_UNRESOLVED`, y se dice por que."""
    r = _ev([_autoridad(scope={"type": "PROJECT", "value": "otro-proyecto"})])
    t.igual("E-16 el estado", "SECURITY_AUTHORITY_SCOPE_UNRESOLVED", r["state"])
    t.contiene("E-16 y se dice que la contencion la declara el objetivo",
               "la contencion la declara", r["reason"])
    t.verdadero("E-16 la autoridad se considero y no cubre",
                any(c["covers"] is False for c in r["considered"]))

    # Un objetivo sin alcance valido tampoco resuelve.
    for caso, objetivo in (("sin scope", {"id": "u"}),
                           ("tipo inventado", {"id": "u", "scope": {"type": "AREA",
                                                                    "value": "x"}}),
                           ("valor vacio", {"id": "u", "scope": {"type": "PROJECT",
                                                                 "value": "  "}})):
        t.igual("E-16 %s: sin alcance" % caso, "SECURITY_AUTHORITY_SCOPE_UNRESOLVED",
                _estado(objetivo=objetivo))


def test_e17_la_contencion_la_declara_el_objetivo(t):
    """E-17 — y `GLOBAL` no es una excepcion."""
    global_ = _autoridad(scope={"type": "GLOBAL", "value": "GCABA"})
    aplicacion = {"id": "u", "scope": {"type": "APPLICATION", "value": "tramites-web"}}
    con_cadena = dict(aplicacion, within=[{"type": "PROJECT", "value": "tramites"},
                                          {"type": "GLOBAL", "value": "GCABA"}])

    t.igual("E-17 GLOBAL no cubre a quien no lo declara",
            "SECURITY_AUTHORITY_SCOPE_UNRESOLVED", _estado([global_], objetivo=aplicacion))
    t.igual("E-17 y cubre a quien lo declara en su cadena", "PASS",
            _estado([global_], objetivo=con_cadena))
    t.igual("E-17 la autoridad de proyecto cubre a la aplicacion que la declara", "PASS",
            _estado([AUTORIDAD], objetivo=con_cadena))
    t.igual("E-17 pero no a la que no la declara", "SECURITY_AUTHORITY_SCOPE_UNRESOLVED",
            _estado([AUTORIDAD], objetivo=aplicacion))

    # 🔴 No hay orden implicito: el objetivo de proyecto no queda cubierto por una de aplicacion.
    de_aplicacion = _autoridad(scope={"type": "APPLICATION", "value": "tramites-web"})
    t.igual("E-17 ni al reves", "SECURITY_AUTHORITY_SCOPE_UNRESOLVED", _estado([de_aplicacion]))
    r = _ev([global_], objetivo=con_cadena)
    t.igual("E-17 la cadena resuelta viaja en el resultado", 3, len(r["scopeChain"]))


def test_e18_varias_autoridades_con_alcances_explicitos_conviven(t):
    """E-18 — cada objetivo resuelve contra la que lo alcanza."""
    de_infra = _autoridad(authorityId="aut-infra",
                          organization={"name": "Direccion de Infraestructura",
                                        "gcabaMembership": "VERIFIED"},
                          scope={"type": "SYSTEM", "value": "infra-comun"})
    registro = [AUTORIDAD, de_infra]
    infra = {"id": "u-infra", "scope": {"type": "SYSTEM", "value": "infra-comun"}}

    r_app = _ev(registro)
    t.igual("E-18 el proyecto resuelve con la suya", "PASS", r_app["state"])
    t.igual("E-18 y es la del proyecto", "aut-1", r_app["authority"]["authorityId"])

    r_infra = _ev(registro, objetivo=infra)
    t.igual("E-18 el sistema resuelve con la suya", "PASS", r_infra["state"])
    t.igual("E-18 y es la de infraestructura", "aut-infra", r_infra["authority"]["authorityId"])

    # Y ninguna de las dos se pisa con la otra: no hay conflicto.
    t.verdadero("E-18 ninguna en conflicto",
                "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE" not in (r_app["state"],
                                                                  r_infra["state"]))


# -- La vigencia ---------------------------------------------------------------

def test_e19_una_autoridad_vencida_no_rige(t):
    """E-19 — `SECURITY_AUTHORITY_EVIDENCE_EXPIRED`, con las dos fechas en el motivo."""
    r = _ev([_autoridad(effectiveTo="2026-09-21")])
    t.igual("E-19 el estado", "SECURITY_AUTHORITY_EVIDENCE_EXPIRED", r["state"])
    t.contiene("E-19 con la fecha de vencimiento", "2026-09-21", r["reason"])
    t.contiene("E-19 y la de evaluacion", HOY, r["reason"])
    # El mismo dia todavia rige: el corte es estricto y esta puesto a proposito.
    t.igual("E-19 el mismo dia todavia rige", "PASS", _estado([_autoridad(effectiveTo=HOY)]))


def test_e20_sin_fecha_de_fin_no_hay_vigencia(t):
    """E-20 — las cuatro formas, y ninguna autoridad para siempre."""
    sin_clave = copy.deepcopy(AUTORIDAD)
    del sin_clave["effectiveTo"]
    casos = (
        ("sin la clave", sin_clave),
        ("nula", _autoridad(effectiveTo=None)),
        ("mal formada", _autoridad(effectiveTo="2027")),
        ("todavia no rige", _autoridad(effectiveFrom="2027-01-01")),
    )
    for caso, autoridad in casos:
        r = _ev([autoridad])
        t.igual("E-20 %s: sin vigencia" % caso,
                "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED", r["state"])
        t.verdadero("E-20 %s: no aprueba" % caso, not CHECK.aprueba(r))
    t.contiene("E-20 y se dice por que", "no es una asignacion vigente",
               _ev([_autoridad(effectiveTo=None)])["reason"])

    # Una fecha de evaluacion que no es una fecha tampoco resuelve nada.
    for fecha in (None, "", "ayer", "22-09-2026"):
        t.igual("E-20 la fecha de evaluacion `%s` no sirve" % fecha,
                "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED", _estado(fecha=fecha))
    # Y un `effectiveFrom` mal formado tampoco.
    t.igual("E-20 un effectiveFrom mal formado tampoco",
            "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED",
            _estado([_autoridad(effectiveFrom="01/01/2026")]))


# -- El conflicto --------------------------------------------------------------

def test_e21_dos_organizaciones_sobre_el_mismo_objetivo(t):
    """E-21 — y tambien cuando sus alcances declarados son distintos."""
    otra = _autoridad(authorityId="aut-2",
                      organization={"name": "Otra Direccion", "gcabaMembership": "VERIFIED"})
    r = _ev([AUTORIDAD, otra])
    t.igual("E-21 el estado", "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE", r["state"])
    t.contiene("E-21 y nombra a las dos", "Otra Direccion", r["reason"])
    t.contiene("E-21 y a la primera", "Direccion General de Seguridad de la Informacion",
               r["reason"])
    t.verdadero("E-21 no aprueba", not CHECK.aprueba(r))

    # 🔴 Alcances distintos que los dos alcanzan al objetivo: sigue siendo conflicto. Elegir el
    # mas especifico exigiria el orden entre tipos que este cambio se niega a inventar.
    con_cadena = {"id": "u", "scope": {"type": "APPLICATION", "value": "tramites-web"},
                  "within": [{"type": "PROJECT", "value": "tramites"},
                             {"type": "GLOBAL", "value": "GCABA"}]}
    global_otra = _autoridad(authorityId="aut-3",
                             organization={"name": "Tercera", "gcabaMembership": "VERIFIED"},
                             scope={"type": "GLOBAL", "value": "GCABA"})
    t.igual("E-21 alcances distintos, los dos alcanzan", "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE",
            _estado([AUTORIDAD, global_otra], objetivo=con_cadena))


def test_e22_dos_registros_de_la_misma_organizacion_no_son_conflicto(t):
    """E-22 — no hay nada que resolver."""
    segunda = _autoridad(authorityId="aut-2")
    r = _ev([AUTORIDAD, segunda])
    t.igual("E-22 aprueba", "PASS", r["state"])
    t.igual("E-22 y resuelve con una de las dos", "Direccion General de Seguridad de la Informacion",
            r["authority"]["organization"])


def test_e23_si_solo_una_rige_no_hay_conflicto(t):
    """E-23 — resuelve la vigente, que es lo que `current assignment` quiere decir."""
    vieja = _autoridad(authorityId="aut-vieja",
                       organization={"name": "Direccion Anterior", "gcabaMembership": "VERIFIED"},
                       effectiveFrom="2019-01-01", effectiveTo="2024-12-31")
    r = _ev([AUTORIDAD, vieja])
    t.igual("E-23 aprueba", "PASS", r["state"])
    t.igual("E-23 y resuelve la vigente", "aut-1", r["authority"]["authorityId"])

    # Con las dos vencidas, no hay ninguna: el estado es el del vencimiento, no el del conflicto.
    otra_vieja = _autoridad(authorityId="aut-vieja-2", effectiveTo="2023-01-01")
    t.igual("E-23 con las dos vencidas es vencimiento",
            "SECURITY_AUTHORITY_EVIDENCE_EXPIRED", _estado([vieja, otra_vieja]))


# -- El PASS, y lo que no aprueba ---------------------------------------------

def test_e24_pass_exige_las_siete_condiciones(t):
    """E-24 — el caso que aprueba, roto de siete maneras."""
    t.igual("E-24 el caso base aprueba", "PASS", _estado())
    t.verdadero("E-24 y `aprueba` lo dice", CHECK.aprueba(_ev()))

    siete = (
        ("existe un registro", [], "SECURITY_CONTROL_AUTHORITY_UNRESOLVED"),
        ("hay identidad", [_autoridad(organization={"name": "   ",
                                                    "gcabaMembership": "VERIFIED"})],
         "AUTHORITY_EVIDENCE_INSUFFICIENT"),
        ("la pertenencia esta evidenciada", [_autoridad(evidence=[])],
         "GCABA_MEMBERSHIP_UNRESOLVED"),
        ("la responsabilidad es de control", [_autoridad(responsibilities=["CONSULTING"])],
         "AUTHORITY_EVIDENCE_INSUFFICIENT"),
        ("el alcance cubre al objetivo", [_autoridad(scope={"type": "PROJECT",
                                                            "value": "ajeno"})],
         "SECURITY_AUTHORITY_SCOPE_UNRESOLVED"),
        ("rige a la fecha", [_autoridad(effectiveTo=None)],
         "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED"),
        ("no hay conflicto", [_autoridad(), _autoridad(authorityId="aut-2", organization={
            "name": "Otra", "gcabaMembership": "VERIFIED"})],
         "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE"),
    )
    t.igual("E-24 son siete condiciones", 7, len(siete))
    for condicion, autoridades, esperado in siete:
        estado = _estado(autoridades)
        t.igual("E-24 sin `%s` no aprueba" % condicion, esperado, estado)
        t.verdadero("E-24 sin `%s` no es PASS" % condicion, estado != "PASS")


def test_e25_pass_de_o2_no_aprueba_nada_mas(t):
    """E-25 — ni C2, ni el estado oficial de la evaluacion."""
    r = _ev()
    t.igual("E-25 aprueba", "PASS", r["state"])
    valores = set(_valores(r))
    t.igual("E-25 ningun valor es un estado oficial", [],
            sorted(valores & set(evaluacion.ESTADOS_OFICIALES)))
    serializado = json.dumps(r, ensure_ascii=False, default=str)
    t.no_contiene("E-25 no dice APPROVED", "APPROVED", serializado)
    t.no_contiene("E-25 no dice SECURITY_APPROVED", "SECURITY_APPROVED", serializado)
    t.no_contiene("E-25 y no dice C2", '"C2"', serializado)

    # 🔴 Literales OPERATIVOS. El docstring nombra a `C2` a proposito, para decir que PASS no es
    # C2; prohibirselo seria prohibir la linea que declara la frontera.
    literales = _literales(RUTA_CHECK)
    for prohibido in ("APPROVED", "REJECTED", "IN_ASSESSMENT", "C2"):
        t.verdadero("E-25 ningun literal operativo nombra `%s`" % prohibido,
                    prohibido not in literales)
    t.verdadero("E-25 y ninguno lo lleva adentro",
                not any(p in lit for lit in literales
                        for p in ("APPROVED", "IN_ASSESSMENT")))

    # Y el estado oficial sigue exigiendo procedencia externa.
    for productor in evaluacion.PRODUCTORES_INTERNOS:
        estado = evaluacion.estado_oficial({"state": "APPROVED", "producer": productor,
                                            "evidence": ["o2-pass"]})
        t.igual("E-25 `%s` no puede aprobar" % productor, "OFFICIAL_STATUS_UNRESOLVED",
                estado["state"])


def test_e26_los_nueve_estados_con_ese_nombre(t):
    """E-26 — los nueve emitidos desde un caso real, y uno solo aprueba."""
    t.igual("E-26 son nueve", 9, len(CHECK.ESTADOS))
    t.igual("E-26 y son estos", sorted(LOS_9), sorted(CHECK.ESTADOS))

    emitidos = {
        _estado(),
        _estado([_autoridad(organization={"name": "Ajena SA", "gcabaMembership": "NOT_GCABA"})]),
        _estado([]),
        _estado([_autoridad(evidence=[])]),
        _estado([_autoridad(scope={"type": "PROJECT", "value": "ajeno"})]),
        _estado([_autoridad(effectiveTo=None)]),
        _estado([_autoridad(effectiveTo="2020-01-01")]),
        _estado([_autoridad(), _autoridad(authorityId="aut-2", organization={
            "name": "Otra", "gcabaMembership": "VERIFIED"})]),
        _estado([_autoridad(responsibilities=["DEVELOPMENT"])]),
    }
    t.igual("E-26 los nueve se emiten desde un caso real", sorted(LOS_9), sorted(emitidos))
    t.igual("E-26 el unico que aprueba es PASS", "PASS", CHECK.PASA)
    for estado in LOS_9:
        t.igual("E-26 `%s` aprueba solo si es PASS" % estado, estado == "PASS",
                CHECK.aprueba({"state": estado}))


def test_e27_todo_resultado_conserva_la_traza(t):
    """E-27 — ES0902 / 6.2 / §3 / O2, por todos los caminos."""
    caminos = (
        ("aprueba", None, OBJETIVO, HOY),
        ("sin registro", [], OBJETIVO, HOY),
        ("falla", [_autoridad(organization={"name": "Ajena", "gcabaMembership": "NOT_GCABA"})],
         OBJETIVO, HOY),
        ("sin alcance", None, {"id": "u"}, HOY),
        ("sin fecha", None, OBJETIVO, None),
        ("en conflicto", [_autoridad(), _autoridad(authorityId="a2", organization={
            "name": "Otra", "gcabaMembership": "VERIFIED"})], OBJETIVO, HOY),
    )
    for nombre, autoridades, objetivo, fecha in caminos:
        r = _ev(autoridades, objetivo, fecha)
        t.igual("E-27 %s: la traza entera" % nombre, TRAZA, r["source"])
        t.igual("E-27 %s: la regla" % nombre, "O2", r["rule"])
        t.igual("E-27 %s: la clave compuesta" % nombre, "ES0902.O2", r["ruleKey"])
        t.igual("E-27 %s: el control" % nombre, CHEQUEO, r["control"])
        t.verdadero("E-27 %s: y trae un estado de los nueve" % nombre, r["state"] in LOS_9)
    t.igual("E-27 la constante del modulo es la misma", TRAZA, CHECK.TRAZA)


def test_e28_no_se_crea_ningun_agente_y_los_controles_quedan(t):
    """E-28 — los mismos diez agentes, las mismas cuatro skills, 54 controles."""
    registro = c_reg.cargar()
    ids = sorted(a["id"] for a in registro["agents"])
    t.igual("E-28 siguen siendo diez", 10, len(ids))
    de_security = [a for a in registro["agents"] if a["id"] == "dev-security"][0]
    t.igual("E-28 las cuatro skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"],
            sorted(s["id"] for s in de_security.get("skills") or []))

    reporte = c_controles.reporte()
    t.igual("E-28 son cincuenta y cuatro controles", 54, reporte["summary"]["declaredControls"])
    t.verdadero("E-28 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-28 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-28 ningun archivo suelto", [], reporte["undeclared"])
    for control in (POLICY, CHEQUEO):
        t.igual("E-28 %s esta INSTALLED" % control, "INSTALLED", reporte["controls"].get(control))
        fuentes = c_controles.fuentes_de(c_controles.control(control, REGISTRO))
        t.igual("E-28 %s tiene una fuente" % control, 1, len(fuentes))
        t.igual("E-28 %s sale de ES0902 6.2 §3 O2" % control,
                ["ES0902", "6.2", "3", "O2"],
                [fuentes[0]["standard"], fuentes[0]["version"], fuentes[0]["section"],
                 fuentes[0]["rule"]])

    resolucion = seguridad.resolver({s: True for s in seguridad.senales_declaradas(MATRIZ)})
    faltan = {f["id"] for f in seguridad.controles_no_instalados(resolucion)}
    for control in (POLICY, CHEQUEO):
        t.verdadero("E-28 %s ya no figura como hueco" % control, control not in faltan)
    t.igual("E-28 quedan quince huecos", 15,
            len(seguridad.controles_no_instalados(resolucion)))
