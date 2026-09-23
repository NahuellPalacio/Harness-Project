# D8: el borde del servicio exige token, y no hay camino de al lado que lo esquive.
#
# Escenarios E-01 a E-39 de docs/cambios/d8-proteccion-de-servicios-con-token/spec.md. Entre
# parentesis, el D8-nn del pedido de instalacion.
#
# 🔴 Nada de esto llama a un servicio ni emite un token. Lo que se verifica es el CONTROL: que el
# binding salga de la matriz y falle cerrado, que una libreria instalada no alcance, que un camino
# se identifique por el comportamiento que alcanza y no por su direccion, y que ninguna categoria
# de endpoint se exima sola.
import ast
import copy
import importlib.util
import io
import os
import re
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
# `desde` se resuelve caminando hacia arriba desde un ARCHIVO, no desde un directorio.
RUTA_REG = str(BIN / "orquestacion" / "registro_agentes.py")

sys.path.insert(0, str(BIN))
from orquestacion import controles as c_controles    # noqa: E402
from orquestacion import matriz as c_matriz          # noqa: E402
from orquestacion import normativa as c_normativa    # noqa: E402
from orquestacion import registro_agentes as c_reg   # noqa: E402
from orquestacion import senales as c_senales        # noqa: E402

RUTA_CHECK = CONTROLES / "checks" / "service-token-protection.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar(RUTA_CHECK, "d8_check")

SENAL = "serviceEndpointPresent"
POLICY = "service-token-protection-required"
CHEQUEO = "service-token-protection"
AGENTES = ["dev-security", "dev-integration", "dev-backend"]

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D8"}

BUILD = {"id": "b-instalacion-de-d8", "runtime": "runtime-de-prueba"}
MECANISMO = {"id": "proteccion-de-token-del-proyecto", "source": "PROJECT_SECURITY_CONTRACT",
             "reference": "contrato de seguridad del proyecto",
             "enforcementPoint": "el borde del servicio",
             "tokenSupply": "la llamada lo entrega como el contrato declara"}


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="s-1", tipo="PROJECT_DOCUMENTATION", ref="ficha de proyecto",
              claim="la unidad expone un servicio propio", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid=SENAL, **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    s.update(extra)
    return s


def _sin_servicio():
    return _senal("FALSE", [_ev_senal(claim="el alcance esta completo y no expone servicios")])


def _ev(eid, tipo=None, modo="REAL", **extra):
    e = {"evidenceId": eid, "sourceType": tipo or CHECK.SONDA, "reference": "corrida#1",
         "claim": "lo que la sonda reporta", "buildId": BUILD["id"],
         "runtime": BUILD["runtime"], "mode": modo}
    e.update(extra)
    return e


def _sonda(caso, refs=None, **extra):
    s = {"case": caso, "evidenceRefs": ["p-" + caso] if refs is None else list(refs)}
    if caso in CHECK.NEGATIVAS:
        s["rejected"] = True
    else:
        s["succeeded"] = True
    s.update(extra)
    return s


def _sondas(casos=CHECK.SONDAS, **extra):
    return [_sonda(c, **extra) for c in casos]


def _endpoint(eid="e-primario", comportamiento="b-aprobar-tramite", clase="PRIMARY",
              activo=True, publico=False, exigencia=None, sondas=None, **extra):
    e = {"id": eid, "behaviorId": comportamiento, "kind": clase, "active": activo,
         "public": publico,
         "enforcement": {"required": True, "mechanism": MECANISMO["id"],
                         "point": "el borde del servicio"} if exigencia is None
         else exigencia,
         "probes": _sondas() if sondas is None else list(sondas)}
    e.update(extra)
    return e


def _abierto(eid="e-legacy", comportamiento="b-aprobar-tramite", clase="LEGACY_ROUTE"):
    """Un camino activo que declara que NO exige token. Es un bypass probado."""
    return {"id": eid, "behaviorId": comportamiento, "kind": clase, "active": True,
            "public": False, "enforcement": {"required": False}, "probes": []}


def _evidencias(modo="REAL"):
    return [_ev("p-" + c, modo=modo) for c in CHECK.SONDAS]


def _caso(items=None, evidencia=None, fuente="ROUTE_INVENTORY", completo=True, **extra):
    caso = {
        "application": {"id": "tramites", "environment": "test"},
        "build": dict(BUILD),
        "testTarget": {"available": True},
        "tokenMechanism": dict(MECANISMO),
        "endpoints": {"source": fuente, "complete": completo,
                      "items": [_endpoint()] if items is None else list(items)},
        "evidence": _evidencias() if evidencia is None else list(evidencia),
    }
    caso.update(extra)
    return caso


# -- la matriz de prueba, para las formas del binding --------------------------

def _matriz(**cambios):
    """La matriz real con la fila de D8 cambiada. El seam es el mismo que ya tiene `matriz`."""
    doc = copy.deepcopy(c_matriz.cargar())
    for r in doc["rules"]:
        if r["id"] == "D8":
            r.update(cambios)
    return doc


def _matriz_sin_fila():
    doc = copy.deepcopy(c_matriz.cargar())
    doc["rules"] = [r for r in doc["rules"] if r["id"] != "D8"]
    return doc


def _matriz_sin_estandar():
    doc = copy.deepcopy(c_matriz.cargar())
    doc.pop("standard", None)
    return doc


FORMAS_DEL_BINDING = {
    "sin matriz": {},
    "sin la fila de D8": None,          # se reemplaza abajo; None no es un doc valido
    "con dos senales": {"applicability": {"mode": "CONDITIONAL",
                                          "signals": [SENAL, "frontendPresent"]}},
    "sin senales": {"applicability": {"mode": "CONDITIONAL", "signals": []}},
    "sin declarar este check": {"checks": ["otro-check"]},
    "sin ninguna policy": {"policies": []},
}


def _docs_del_binding():
    """Las seis formas de una fila que no se puede resolver."""
    salida = {"sin matriz": {}, "sin la fila de D8": _matriz_sin_fila(),
              "sin el estandar": _matriz_sin_estandar()}
    for nombre, cambios in FORMAS_DEL_BINDING.items():
        if cambios:
            salida[nombre] = _matriz(**cambios)
    return salida


# -- los caminos del check, uno por estado -------------------------------------

def _publico_sin_excepcion():
    return _endpoint(eid="e-publico", comportamiento="b-consulta", publico=True, sondas=[])


def _caminos():
    return {
        "PASS": (_caso(), _senal(), None),
        "FAIL": (_caso(items=[_endpoint(), _abierto()]), _senal(), None),
        "PARTIAL": (_caso(items=[_endpoint(sondas=_sondas(("VALID_TOKEN",)))]), _senal(), None),
        "NOT_APPLICABLE": (_caso(), _sin_servicio(), None),
        "APPLICABILITY_UNRESOLVED": (_caso(), None, None),
        "D8_MATRIX_BINDING_UNRESOLVED": (_caso(), _senal(), {}),
        "SERVICE_ENDPOINT_COVERAGE_UNRESOLVED": (_caso(endpoints={}), _senal(), None),
        "TOKEN_MECHANISM_UNRESOLVED": (_caso(tokenMechanism={}), _senal(), None),
        "TOKEN_PROTECTION_EXCEPTION_UNRESOLVED": (
            _caso(items=[_endpoint(), _publico_sin_excepcion()]), _senal(), None),
        "TEST_TARGET_UNAVAILABLE": (_caso(testTarget={}), _senal(), None),
    }


def _evaluar(caso, senal=None, doc=None, desde=None):
    return CHECK.evaluar(caso, senal, desde, doc)


def _arbol_sin_matriz():
    """Un `desde` que apunta afuera de todo harness: la matriz no esta."""
    return os.path.join(tempfile.mkdtemp(), "nada.py")


def _arbol_con_matriz_rota():
    """Un `desde` cuyo harness tiene la matriz, y es JSON invalido."""
    raiz = tempfile.mkdtemp()
    reglas = os.path.join(raiz, "harness", "reglas")
    os.makedirs(reglas, exist_ok=True)
    with io.open(os.path.join(reglas, "es0901-7.1-normative-matrix.json"), "w",
                 encoding="utf-8") as f:
        f.write("{ esto no es json")
    binario = os.path.join(raiz, "harness", "bin")
    os.makedirs(binario, exist_ok=True)
    return os.path.join(binario, "x.py")


# -- E-01 a E-04 — la matriz y el binding --------------------------------------

def test_e01_el_binding_sale_de_la_matriz(t):
    """E-01 (D8-01, D8-06, D8-07, D8-08) — los ids, la senal y los agentes salen de la fila."""
    datos, motivo = CHECK.binding()
    t.vacio("E-01 el binding resuelve", motivo)
    t.igual("E-01 la policy sale de la matriz", [POLICY], datos["policies"])
    t.igual("E-01 el check tambien", [CHEQUEO], datos["checks"])
    t.igual("E-01 la senal tambien", SENAL, datos["signal"])
    t.igual("E-01 los agentes duenos tambien", AGENTES, datos["agents"])
    t.igual("E-01 y la tupla normativa entera", TRAZA, datos["source"])

    # 🔴 Y el modulo NO los lleva escritos: es lo que distingue a D8 de las nueve anteriores.
    fuente = RUTA_CHECK.read_text(encoding="utf-8")
    t.verdadero("E-01 el modulo no escribe el id de su policy", POLICY not in fuente)
    t.verdadero("E-01 ni el nombre de su senal", SENAL not in fuente)
    # 🔴 Los agentes se comparan CITADOS: `dev-backend` es prefijo de
    # `dev-backend-implementation`, que es una skill y no un agente.
    t.verdadero("E-01 ni la lista de agentes que la matriz declara",
                not [a for a in AGENTES[1:] if ('"%s"' % a) in fuente])
    t.igual("E-01 lo unico escrito es su propio id", CHEQUEO, CHECK.CONTROL)
    t.verdadero("E-01 y su propio id esta en la fila", CHECK.CONTROL in datos["checks"])

    # El resultado publica el binding, para que quien lee un plan vea de donde salio.
    salida = _evaluar(_caso(), _senal())
    t.igual("E-01 el resultado publica la policy", [POLICY], salida["binding"]["policies"])
    t.igual("E-01 y los agentes", AGENTES, salida["binding"]["agents"])
    t.igual("E-01 y la senal de la que depende", SENAL, salida["signal"])


def test_e02_sin_fila_resoluble_falla_cerrado(t):
    """E-02 (§ binding) — las seis formas, y el unico resultado sin tupla."""
    # 🔴 Las dos primeras formas que el escenario nombra —la matriz ausente y la ilegible— no
    # entran por `doc`: entran por `desde`, que es el unico camino que ejercita el `except
    # MatrizInvalida` que envuelve a `matriz.cargar`. Sin ellas esa rama estaba muerta en la
    # suite, y la matriz ausente es justo la forma mas probable en un proyecto instalado.
    formas = dict(_docs_del_binding())
    t.igual("E-02 son siete formas por el documento", 7, len(formas))
    por_desde = {"la matriz ausente": _arbol_sin_matriz(),
                 "la matriz ilegible": _arbol_con_matriz_rota()}
    for nombre, desde in sorted(por_desde.items()):
        salida = _evaluar(_caso(), _senal(), None, desde)
        t.igual("E-02 %s deja el binding sin resolver" % nombre,
                "D8_MATRIX_BINDING_UNRESOLVED", salida["state"])
        t.igual("E-02 %s no inventa la tupla" % nombre, {}, salida["source"])
        t.verdadero("E-02 %s lo declara" % nombre, salida.get("sourceMissing") is True)
        t.verdadero("E-02 %s dice por que" % nombre,
                    "no se pudo leer" in (salida.get("detail") or ""))
        t.verdadero("E-02 %s no aprueba" % nombre, not CHECK.aprueba(salida))

    docs = formas
    for nombre, doc in sorted(docs.items()):
        salida = _evaluar(_caso(), _senal(), doc)
        t.igual("E-02 %s deja el binding sin resolver" % nombre,
                "D8_MATRIX_BINDING_UNRESOLVED", salida["state"])
        t.verdadero("E-02 %s no aprueba" % nombre, not CHECK.aprueba(salida))
        t.verdadero("E-02 %s dice por que" % nombre, bool(salida.get("detail")))
        # 🔴 El unico camino del harness cuyo resultado declara que le falta la tupla.
        t.igual("E-02 %s no inventa la tupla" % nombre, {}, salida["source"])
        t.verdadero("E-02 %s lo declara" % nombre, salida.get("sourceMissing") is True)
        t.igual("E-02 %s igual dice que control es" % nombre, CHEQUEO, salida["control"])
        t.igual("E-02 %s y de que regla" % nombre, "D8", salida["rule"])
        # Y no evalua nada mas: no hay endpoints, ni mecanismo, ni senal en la salida.
        for campo in ("endpoints", "tokenMechanism", "signalValue", "governedEndpoints"):
            t.verdadero("E-02 %s no evaluo %s" % (nombre, campo),
                        not salida.get(campo))

    # Una fila que SI resuelve, para que la premisa valga.
    t.igual("E-02 la premisa: con la matriz instalada resuelve", "PASS",
            _evaluar(_caso(), _senal())["state"])


def test_e03_el_binding_corre_antes_que_la_senal(t):
    """E-03 (§ binding) — sin matriz y sin senal, el estado es el del binding."""
    salida = _evaluar(_caso(), None, {})
    t.igual("E-03 manda el binding", "D8_MATRIX_BINDING_UNRESOLVED", salida["state"])
    t.verdadero("E-03 y no la aplicabilidad",
                salida["state"] != "APPLICABILITY_UNRESOLVED")
    t.verdadero("E-03 no se pregunto por la senal", "signalValue" not in salida)
    # Con la matriz puesta y sin senal, si es la aplicabilidad.
    t.igual("E-03 con matriz, manda la senal", "APPLICABILITY_UNRESOLVED",
            _evaluar(_caso(), None)["state"])


def test_e04_la_fila_no_se_edita(t):
    """E-04 (D8-01) — la fila de D8, entera, y con las claves de toda fila de diseno."""
    d8 = c_matriz.regla("D8")
    t.igual("E-04 el modo", "CONDITIONAL", d8["applicability"]["mode"])
    t.igual("E-04 la senal", [SENAL], d8["applicability"]["signals"])
    t.igual("E-04 la categoria", "DESIGN", d8["category"])
    t.igual("E-04 la intencion operativa no cambio",
            "Services must be protected by a token-based mechanism.", d8["operationalIntentEn"])
    t.igual("E-04 los tres duenos", AGENTES, d8["primaryAgents"])
    t.igual("E-04 la policy ya estaba declarada", [POLICY], d8["policies"])
    t.igual("E-04 y el check", [CHEQUEO], d8["checks"])
    t.igual("E-04 sigue CLASSIFIED", "CLASSIFIED", d8["status"])
    t.igual("E-04 la senal la declara D8 y nadie mas", ["D8"], c_senales.reglas_de(SENAL))

    otras = [r for r in c_matriz.reglas()
             if r.get("category") == "DESIGN" and r.get("id") != "D8"]
    comunes, todas = set(otras[0].keys()), set(otras[0].keys())
    for otra in otras:
        comunes &= set(otra.keys())
        todas |= set(otra.keys())
    t.igual("E-04 tiene las claves que tiene toda fila de diseno", sorted(comunes),
            sorted(d8.keys()))
    t.vacio("E-04 y ninguna que no exista en el resto", sorted(set(d8.keys()) - todas))
    t.verdadero("E-04 `reviews` es opcional y alguna otra fila lo trae",
                "reviews" in todas and "reviews" not in comunes)


# -- E-05 a E-09 — la senal y la aplicabilidad ---------------------------------

def test_e05_true_hace_aplicable(t):
    """E-05 (D8-02) — TRUE con evidencia deja D8 aplicable con sus dos controles."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-05 D8 aplica", "D8" in bloque["applicableRules"])
    t.verdadero("E-05 exige su policy", POLICY in bloque["declaredPolicies"])
    t.verdadero("E-05 y su check", CHEQUEO in bloque["declaredChecks"])
    t.igual("E-05 la senal resuelta viaja", "TRUE", bloque["signals"][SENAL]["value"])


def test_e06_false_hace_no_aplicable(t):
    """E-06 (D8-03) — FALSE con evidencia deja D8 fuera, y el check tambien."""
    bloque = c_normativa.resolucion({SENAL: _sin_servicio()})
    t.verdadero("E-06 D8 no aplica", "D8" in bloque["notApplicableRules"])
    salida = _evaluar(_caso(), _sin_servicio())
    t.igual("E-06 el check no aplica", "NOT_APPLICABLE", salida["state"])
    t.verdadero("E-06 no aprueba", not CHECK.aprueba(salida))


def test_e07_sin_senal_no_se_resuelve(t):
    """E-07 (D8-04) — APPLICABILITY_UNRESOLVED con el nombre de la que falta."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-07 D8 queda sin resolver", "D8" in sin_resolver)
    t.igual("E-07 con la senal que falta", [SENAL], sin_resolver["D8"]["missingSignals"])
    salida = _evaluar(_caso(), None)
    t.igual("E-07 el check tambien", "APPLICABILITY_UNRESOLVED", salida["state"])
    t.igual("E-07 y dice cual falta", [SENAL], salida["missingSignals"])
    t.verdadero("E-07 no aprueba", not CHECK.aprueba(salida))


def test_e08_la_ausencia_nunca_es_false(t):
    """E-08 (D8-05) — lo ausente queda UNRESOLVED, lo no declarado se rechaza, y el limite."""
    sin_evidencia = c_senales.resolver_una(_senal("FALSE", []))
    t.igual("E-08 FALSE sin evidencia no queda en FALSE", "UNRESOLVED", sin_evidencia["value"])
    t.verdadero("E-08 y lo dice", "SIGNAL_EVIDENCE_MISSING" in sin_evidencia["states"])

    no_declarada = c_senales.resolver_una(_senal("TRUE", sid="serviceEndpoint"))
    t.verdadero("E-08 una senal que la matriz no declara se rechaza",
                "SIGNAL_NOT_DECLARED" in no_declarada["states"])

    # 🔴 Las dos clases van CLAVADAS, no leidas de la constante que el escenario verifica: con
    # `for tipo in c_senales.FUENTES_DEBILES` el recorrido se achica junto con lo que prueba, y
    # sacar una clase de la lista dejaba el test verde.
    DEBILES = ("AGENT_STATEMENT", "REPOSITORY_DEPENDENCY")
    t.igual("E-08 son estas dos las clases debiles", DEBILES, c_senales.FUENTES_DEBILES)
    ausencias = ("no se encontro ningun controlador en el repositorio",
                 "no hay ningun archivo de contrato de servicio",
                 "no aparece ningun literal de ruta en el archivo que se leyo")
    for tipo in DEBILES:
        for claim in ausencias:
            resuelta = c_senales.resolver_una(_senal("FALSE", [
                _ev_senal(tipo=tipo, claim=claim, supports="FALSE")]))
            t.igual("E-08 %s no baja a FALSE: %s" % (tipo[:5], claim[:28]), "UNRESOLVED",
                    resuelta["value"])
            t.igual("E-08 y el check sigue sin resolver", "APPLICABILITY_UNRESOLVED",
                    _evaluar(_caso(), resuelta)["state"])

    # 🔴 El limite, dicho: el harness confia en la ETIQUETA de la fuente, igual que en D7.
    etiquetada = c_senales.resolver_una(_senal("FALSE", [
        _ev_senal(tipo="TASK_CONTEXT", claim=ausencias[0], supports="FALSE")]))
    t.igual("E-08 el limite: con una fuente de la lista, la misma frase apaga D8", "FALSE",
            etiquetada["value"])
    t.igual("E-08 y el check lo informa como no aplicable", "NOT_APPLICABLE",
            _evaluar(_caso(), etiquetada)["state"])
    t.verdadero("E-08 el limite esta anotado en la doc de D7, que es donde vive",
                "el harness confía en la etiqueta de la fuente"
                in (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8"))


def test_e09_ninguna_otra_senal_sustituye(t):
    """E-09 (§) — con cualquier otra senal en TRUE, el check sigue sin resolver."""
    otras = sorted(c_senales.declaradas() - {SENAL})
    t.verdadero("E-09 hay otras senales declaradas contra las que probar", len(otras) >= 10)
    for otra in otras:
        salida = _evaluar(_caso(), _senal("TRUE", sid=otra))
        t.igual("E-09 con %s sigue sin resolver" % otra, "APPLICABILITY_UNRESOLVED",
                salida["state"])
        t.igual("E-09 con %s dice que llego otra" % otra, "SIGNAL_IDENTITY_MISMATCH",
                salida["reason"])
        t.igual("E-09 con %s sigue pidiendo la suya" % otra, [SENAL], salida["missingSignals"])
        t.verdadero("E-09 con %s no aprueba" % otra, not CHECK.aprueba(salida))
        bloque = c_matriz.resolver({otra: True})
        t.verdadero("E-09 %s tampoco hace aplicable a D8" % otra,
                    "D8" in {u["rule"] for u in bloque["unresolvedRules"]})

    # Y el mapa `{id: resuelta}` de la unidad se lee por id.
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.igual("E-09 el mapa de la unidad se lee", "TRUE",
            _evaluar(_caso(), bloque["signals"])["signalValue"])
    ajeno = c_normativa.resolucion({otras[0]: _senal("TRUE", sid=otras[0])})
    t.igual("E-09 un mapa sin la senal de D8 no resuelve", "APPLICABILITY_UNRESOLVED",
            _evaluar(_caso(), ajeno["signals"])["state"])


# -- E-10 — ningun agente, ninguna skill ---------------------------------------

def test_e10_d8_no_crea_agente_ni_skill(t):
    """E-10 (D8-09) — ni la fila, ni los artefactos, ni el conteo de instaladas."""
    d8 = c_matriz.regla("D8")
    t.verdadero("E-10 la fila no declara skills", not d8.get("skills"))
    t.verdadero("E-10 ni la clave existe", "skills" not in d8)
    t.igual("E-10 los duenos son los que ya estaban", AGENTES, d8["primaryAgents"])

    registro = c_reg.cargar(RUTA_REG)
    agentes = {a["id"] for a in registro["agents"]}
    declaradas = {s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    for a in AGENTES:
        t.verdadero("E-10 %s ya estaba en el registro" % a, a in agentes)
    for nombre, texto in _artefactos_de_d8().items():
        t.vacio("E-10 %s no declara un inventario de skills" % nombre,
                re.findall(r"(?i)\bskills\s*[:=]\s*[\"'\[]", texto))
        for mencionada in sorted(set(re.findall(r"\bdev-[a-z-]+\b", texto))):
            t.verdadero("E-10 %s nombra %s, que el registro ya declara" % (nombre, mencionada),
                        mencionada in declaradas or mencionada in agentes)

    t.igual("E-10 siguen siendo 27 las skills instaladas", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))


# -- E-11 a E-14 — lo que no prueba nada ---------------------------------------

def _con_evidencia_sola(tipo):
    """Un caso donde la unica evidencia de las tres sondas es de la clase que se prueba."""
    return _caso(evidencia=[_ev("p-" + c, tipo=tipo) for c in CHECK.SONDAS])


def test_e11_la_dependencia_sola_no_pasa(t):
    """E-11 (D8-10) — una libreria de tokens en el manifiesto no es un endpoint protegido."""
    salida = _evaluar(_con_evidencia_sola("REPOSITORY_DEPENDENCY"), _senal())
    t.igual("E-11 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-11 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-11 la clase esta declarada inerte",
                "REPOSITORY_DEPENDENCY" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e12_el_middleware_solo_no_pasa(t):
    """E-12 (D8-11) — configurar no es rechazar."""
    salida = _evaluar(_con_evidencia_sola("SECURITY_MIDDLEWARE_CONFIG"), _senal())
    t.igual("E-12 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-12 no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-12 la clase esta declarada inerte",
                "SECURITY_MIDDLEWARE_CONFIG" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e13_la_emision_y_el_login_solos_no_pasan(t):
    """E-13 (D8-12) — emitir un token no protege nada."""
    for tipo in ("TOKEN_ISSUANCE", "LOGIN_ENDPOINT"):
        salida = _evaluar(_con_evidencia_sola(tipo), _senal())
        t.igual("E-13 %s no pasa" % tipo, "PARTIAL", salida["state"])
        t.verdadero("E-13 %s no aprueba" % tipo, not CHECK.aprueba(salida))
        t.verdadero("E-13 %s esta declarada inerte" % tipo,
                    tipo in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e14_las_ocho_clases_inertes(t):
    """E-14 (§) — el invariante sobre el producto, no ocho ejemplos."""
    t.igual("E-14 son ocho las clases inertes declaradas", 8,
            len(CHECK.EVIDENCIA_QUE_NO_PRUEBA))
    for tipo in CHECK.EVIDENCIA_QUE_NO_PRUEBA:
        salida = _evaluar(_con_evidencia_sola(tipo), _senal())
        t.igual("E-14 %s no da PASS" % tipo, "PARTIAL", salida["state"])
        t.igual("E-14 %s deja el motivo" % tipo, "ENFORCEMENT_PROBE_MISSING", salida["reason"])
        t.verdadero("E-14 %s no aprueba" % tipo, not CHECK.aprueba(salida))
    # Y la unica que prueba, prueba.
    t.igual("E-14 la clase que prueba es una", 1, len(CHECK.EVIDENCIA_QUE_PRUEBA))
    t.igual("E-14 y con ella pasa", "PASS", _evaluar(_caso(), _senal())["state"])


# -- E-15 a E-16 — la cobertura de endpoints -----------------------------------

def test_e15_el_inventario_incompleto_no_se_resuelve(t):
    """E-15 (D8-13) — las ocho formas de un inventario que no cierra."""
    formas = {
        "sin inventario": _caso(endpoints={}),
        "sin endpoints": _caso(items=[]),
        "sin fuente": _caso(fuente="PROJECT_CONVENTION"),
        "con un endpoint sin id": _caso(items=[_endpoint(eid="  ")]),
        "sin comportamiento": _caso(items=[_endpoint(comportamiento="")]),
        "con una clase desconocida": _caso(items=[_endpoint(clase="OTRA_COSA")]),
        "sin declarar la actividad": _caso(items=[_endpoint(activo=None)]),
        "declarado incompleto": _caso(completo=False),
    }
    t.igual("E-15 son ocho formas", 8, len(formas))
    for nombre, caso in sorted(formas.items()):
        salida = _evaluar(caso, _senal())
        t.igual("E-15 %s deja la cobertura sin resolver" % nombre,
                "SERVICE_ENDPOINT_COVERAGE_UNRESOLVED", salida["state"])
        t.verdadero("E-15 %s no aprueba" % nombre, not CHECK.aprueba(salida))


def test_e16_las_nueve_clases_de_camino(t):
    """E-16 (§) — las nueve entran, y ninguna se trata distinto."""
    # 🔴 Las nueve van CLAVADAS, no leidas de la constante que el escenario verifica. Con el
    # recorrido sobre `CHECK.CLASES`, renombrar `GATEWAY_EXPOSED` dejaba la suite verde y un
    # camino expuesto por la puerta de enlace dejaba de entrar al inventario — que es justo el
    # ejemplo que la spec pone como la trampa de esta regla.
    NUEVE = ("PRIMARY", "ALTERNATE_URL", "ALTERNATE_METHOD", "LEGACY_ROUTE", "VERSIONED_ROUTE",
             "SECONDARY_CONTROLLER", "GATEWAY_EXPOSED", "ADMINISTRATIVE", "UPLOAD_DOWNLOAD")
    t.igual("E-16 son estas nueve clases", NUEVE, CHECK.CLASES)
    t.igual("E-16 y la primaria es la primera", "PRIMARY", CHECK.PRIMARIO)
    for clase in NUEVE:
        cumple = _caso(items=[_endpoint(eid="e-" + clase, clase=clase)])
        t.igual("E-16 %s cumpliendo pasa" % clase, "PASS", _evaluar(cumple, _senal())["state"])
        abierto = _caso(items=[_abierto(eid="e-" + clase, clase=clase)])
        salida = _evaluar(abierto, _senal())
        t.igual("E-16 %s abierto falla" % clase, "FAIL", salida["state"])
        t.igual("E-16 %s con el mismo motivo" % clase, "TOKEN_ENFORCEMENT_BYPASS",
                salida["reason"])


# -- E-17 a E-19 — el mecanismo, que no se inventa -----------------------------

def test_e17_sin_mecanismo_no_se_inventa(t):
    """E-17 (D8-14) — las seis formas del hueco, y las cinco fuentes que sirven."""
    for nombre, mecanismo in (
            ("sin nada", {}),
            ("sin id", dict(MECANISMO, id="")),
            ("con una fuente que no esta en la lista", dict(MECANISMO, source="PROJECT_CONVENTION")),
            ("sin referencia", dict(MECANISMO, reference="")),
            ("sin punto de aplicacion", dict(MECANISMO, enforcementPoint="")),
            ("sin decir como se entrega", dict(MECANISMO, tokenSupply="")),
            ("todo en blancos", dict(MECANISMO, id="  ", reference=" "))):
        salida = _evaluar(_caso(tokenMechanism=mecanismo), _senal())
        t.igual("E-17 %s deja el mecanismo sin resolver" % nombre,
                "TOKEN_MECHANISM_UNRESOLVED", salida["state"])
        t.verdadero("E-17 %s no aprueba" % nombre, not CHECK.aprueba(salida))

    for fuente in CHECK.FUENTES_DE_IDENTIDAD:
        ok, _ = CHECK.mecanismo_valido(_caso(tokenMechanism=dict(MECANISMO, source=fuente)))
        t.verdadero("E-17 %s sirve como origen" % fuente, ok)


def test_e19_el_codigo_de_rechazo_no_se_exige(t):
    """E-19 (D8-24) — sin contrato alcanza el rechazo; con contrato, tiene que coincidir."""
    sin_contrato = _evaluar(_caso(), _senal())
    t.igual("E-19 sin contrato, el rechazo alcanza", "PASS", sin_contrato["state"])
    t.verdadero("E-19 y se informa que no hay contrato",
                sin_contrato["rejectionContract"]["defined"] is False)

    con_contrato = dict(MECANISMO,
                        rejectionContract={"defined": True, "status": "el-que-el-contrato-fija"})
    sondas = [_sonda(c, status="el-que-el-contrato-fija") for c in CHECK.SONDAS]
    t.igual("E-19 con contrato y coincidiendo, pasa", "PASS",
            _evaluar(_caso(items=[_endpoint(sondas=sondas)], tokenMechanism=con_contrato),
                     _senal())["state"])
    otras = [_sonda(c, status="otro-cualquiera") for c in CHECK.SONDAS]
    salida = _evaluar(_caso(items=[_endpoint(sondas=otras)], tokenMechanism=con_contrato),
                      _senal())
    t.igual("E-19 con contrato y sin coincidir, falla", "FAIL", salida["state"])
    t.igual("E-19 con el motivo", "REJECTION_CONTRACT_MISMATCH", salida["reason"])
    # Y sin contrato, un codigo distinto no cambia nada: no hay contra que comparar.
    t.igual("E-19 sin contrato el codigo no se juzga", "PASS",
            _evaluar(_caso(items=[_endpoint(sondas=otras)]), _senal())["state"])

    # 🔴 El modulo no declara ninguna constante numerica: no hay un codigo por defecto.
    numeros = sorted(n for n, v in vars(CHECK).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-19 el check no declara ninguna constante numerica", [], numeros)


# 🔴 El invariante de D8: un artefacto de la regla no lleva el contrato del token ni una direccion.
# Lo que se busca es ESTRUCTURAL —una tecnologia con nombre, un claim, un algoritmo, un formato de
# encabezado, un codigo de estado, una ruta, un verbo, un localizador de red—. El barrido de
# nombres de producto es la segunda red, y las dos se prueban con fugas crudas.
PROHIBIDOS = (
    # localizadores de red
    r"(?i)https?://",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*\.(ar|com|net|org|gov|gob|io|dev|app|cloud|bue|"
    r"tech|local)\b",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*:\d{2,5}\b",
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    # rutas y verbos
    r"[\"'`]/[a-z0-9{]",
    r"(?i)/(api|v\d+|rest|graphql|oauth\d?|realms)\b",
    r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b",
    # codigos de estado
    r"\b(200|201|202|204|301|302|400|401|403|404|405|409|415|422|429|500|502|503)\b",
    r"(?i)\b(status|http[_-]?code|statuscode)\b[\"']?\s*[:=]\s*\d",
    # el contrato del token: claims, algoritmos, tiempos, encabezados
    r"(?i)\b(iss|aud|exp|nbf|iat|jti|sub|kid|azp)\b[\"']?\s*[:=]",
    r"(?i)\b(hs256|rs256|es256|ps256|hmac|rsa|ecdsa|sha256)\b",
    r"(?i)\b(bearer|basic|x-api-key|www-authenticate)\b",
    r"(?i)\b(access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|"
    r"client[_-]?id|api[_-]?key)\b",
    r"(?i)\b(issuer|audience|algorithm|jwks|introspection)\b[\"']?\s*[:=]",
    r"(?i)[./]well[_-]?known\b",
    # 🔴 Roles y scopes. El escenario los enumera entre las quince cosas que no se atribuyen, y
    # eran los dos unicos sin patron: la policy promete en prosa que no se atribuyen y nada lo
    # sostenia. Tres formas, porque una sola deja afuera la prosa.
    # 🔴 `alcance` NO entra: es una palabra del idioma que este repositorio usa todo el tiempo
    # —«el alcance de la regla», «no hay endpoints en alcance»— y meterla convertia el barrido en
    # uno que se pone en rojo con prosa correcta. `scope` es la misma palabra en los artefactos
    # que estan en ingles, asi que las formas de discurso se sacan antes de barrer -ver
    # `_sin_discurso`- y una clave estructural `scope: {` tampoco dispara.
    r"(?i)\b(roles?|scopes?|rol)\b[\"']?\s*[:=]\s*(?=[\"'\[]?[a-z0-9])",
    r"(?i)\b(rol|role|roles|scope|scopes)\b[^\n]{0,30}[\"'\[]?[a-z0-9]+[-:][a-z0-9-]+",
    r"(?i)\b(el|la|the)\s+(rol|role|scope)\s+(de|of|requerido|required|necesario)\b",
    # duraciones: un tiempo de vida inventado
    r"(?i)\b\d+(\.\d+)?\s*(ms|s|seg|segundos?|seconds?|min|minutos?|minutes?|h|hs|horas?|"
    r"hours?|d[ií]as?|days?)\b",
    # paquetes
    r"(?i)\b(npm|pnpm|yarn|pip|composer|nuget|gem|go)\s+(i|install|add|require|get)\b",
    r"@[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*",
)

# Tecnologias de token y productos de puerta de enlace. Aca no se nombra ninguno: una lista de
# prohibidos envejece, corre el eje de la regla —que no es *no uses estos* sino *proteje con
# token*— y deja al invariante sin poder distinguir un contraejemplo de una invencion.
# 🔴 `auth0` va en los PEGADOS y no en los sueltos: `Auth 0` partido en dos escapaba al borde de
# palabra, y partir un nombre es la forma mas barata de esquivar un barrido.
PEGADOS = ("jsonwebtoken", "openidconnect", "keycloak", "pingidentity", "azuread",
           "activedirectoryfederation", "springsecurity", "passportjs", "identityserver",
           "auth0")
SUELTOS = ("jwt", "jwe", "jws", "oauth", "oauth2", "oidc", "openid", "saml", "paseto",
           "macaroon", "okta", "kong", "apigee", "nginx", "traefik", "envoy", "istio",
           "zuul", "ocelot", "haproxy")

# Las siete categorias que NO se eximen. Se nombran en prosa a proposito; lo que no puede haber es
# una estructura de datos que las agrupe.
CATEGORIAS = ("login", "health", "readiness", "liveness", "catalog", "webhook", "public")


def _seccion_de_d8_del_doc():
    """La seccion que D8 agrego a `docs/normativa-7.1.md`.

    Se barre esa y no el archivo entero: el documento cubre las 24 reglas, y el dia que P1 cite
    un framework el barrido de D8 no tiene por que ponerse en rojo.
    """
    texto = (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8")
    titulo = "## El binding sale de la matriz: D8"
    if titulo not in texto:
        return titulo, ""
    return titulo, texto.split(titulo, 1)[1].split("\n## ", 1)[0]


def _artefactos_de_d8():
    """Los cinco textos que la tabla `Qué se construye` de la spec declara como artefactos."""
    return {
        "la policy": (CONTROLES / "policies" / (POLICY + ".md")).read_text(encoding="utf-8"),
        "el check": RUTA_CHECK.read_text(encoding="utf-8"),
        "el registro": repr(c_controles.de_la_regla("D8")),
        "la fila de la matriz": repr(c_matriz.regla("D8")),
        "la doc": _seccion_de_d8_del_doc()[1],
    }


# 🔴 Las formas en las que `scope` y `role` son palabras del discurso y no un scope de token.
# Son las que este repositorio escribe todo el tiempo en sus artefactos en ingles —`In scope:`,
# `Out of scope:`, `the scope of the WorkUnit`—, y sin sacarlas el barrido se pone en rojo con
# prosa correcta el dia que la policy de D8 escriba una. Un barrido que falla sin motivo es un
# barrido que alguien apaga.
#
# 🔴 Solo las formas en INGLES. En castellano este repositorio escribe `alcance`, no `scope`, asi
# que `el scope de escritura` es una fuga y no discurso — sacar tambien los articulos castellanos
# la hacia invisible.
DISCURSO = re.compile(
    r"(?i)\b(in|out of|within|beyond|outside|the|this|that|its|their|of)\s+(scopes?|roles?)\b"
    r"|\b(scopes?|roles?)\s+of\b")


def _sin_discurso(texto):
    """El texto con las formas de discurso de `scope`/`role` en blanco."""
    return DISCURSO.sub(" ", texto)


def _fugas_en(texto):
    texto = _sin_discurso(texto)
    sin_separadores = re.sub(r"[\s_\-]+", "", texto).lower()
    hallados = [p for p in PROHIBIDOS if re.search(p, texto)]
    hallados += [v for v in PEGADOS if v in sin_separadores]
    hallados += [v for v in SUELTOS
                 if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(v), texto.lower())]
    return sorted(set(hallados))


def test_e18_ningun_artefacto_lleva_el_contrato(t):
    """E-18 (D8-23, D8-24) — el invariante sobre los cinco artefactos, y sus tres mitades."""
    titulo, seccion = _seccion_de_d8_del_doc()
    t.verdadero("E-18 la seccion de D8 esta en la doc", bool(seccion))
    t.verdadero("E-18 y tiene contenido", len(seccion) > 2000)

    artefactos = _artefactos_de_d8()
    t.igual("E-18 son cinco textos los que se barren", 5, len(artefactos))
    for nombre, texto in sorted(artefactos.items()):
        t.igual("E-18 %s no lleva el contrato del token" % nombre, [], _fugas_en(texto))

    for estado, (caso, senal, doc) in _caminos().items():
        t.igual("E-18 ni el resultado en %s" % estado, [],
                _fugas_en(repr(_evaluar(caso, senal, doc))))

    # 🔴 La segunda mitad. Las formas son CRUDAS: ninguna se escribio para que el patron la agarre.
    FUGAS = (
        'algorithm: RS256',
        'HS256 firma el token',
        '"alg": "ES256"',
        'iss: el emisor institucional',
        '"aud": "tramites"',
        'exp = 3600',
        'client_secret',
        'access_token',
        'refresh_token',
        'api_key',
        'X-API-Key',
        'Authorization: Bearer',
        'WWW-Authenticate',
        'issuer: el de siempre',
        'jwks: la url de claves',
        'el estandar exige JWT',
        'se usa OAuth2 con OIDC',
        'la implementacion es Keycloak',
        'Auth 0 como proveedor',
        '"json-web-token"',
        'SAML no alcanza',
        'el gateway es Kong',
        'detras de nginx',
        'Apigee expone la ruta',
        'Spring Security valida',
        'el rechazo es 401',
        'responde 403 sin token',
        'status: 401',
        'httpCode = 403',
        'POST /api/v1/tramites',
        'la ruta es "/api/tramites"',
        'GET sobre el recurso',
        'DELETE sin token',
        '/oauth2/token',
        '/.well-known/openid-configuration',
        'https://identidad.example/token',
        'identidad.gcba.gob.ar',
        'gateway-interno:8443',
        '10.20.30.40/token',
        'el token vive 30 minutos',
        'expira en 3600 s',
        'npm install passport-jwt',
        'pip install python-jose',
        '@nestjs/passport',
        # Roles y scopes: los dos que el escenario enumeraba y el barrido no sostenia.
        'scope: tramites-escritura',
        'role: administrador-de-tramites',
        'role: gestor',
        'roles: [admin, operador]',
        'scopes: ["tramites:write", "tramites:read"]',
        'el rol requerido es administrador-de-tramites',
        'el token tiene que traer el scope de escritura',
    )
    t.igual("E-18 son cincuenta y una formas de fuga", 51, len(FUGAS))
    for fuga in FUGAS:
        t.verdadero("E-18 se detecta: %s" % fuga[:40], bool(_fugas_en(fuga)))

    base = artefactos["la policy"]
    t.igual("E-18 la premisa: la policy esta limpia", [], _fugas_en(base))
    t.verdadero("E-18 y con una fuga adentro deja de estarlo",
                bool(_fugas_en(base + "\nalgorithm: RS256\n")))
    t.verdadero("E-18 y la doc tambien",
                bool(_fugas_en(artefactos["la doc"] + "\nEl rechazo es 401.\n")))

    # 🔴 La tercera mitad: lo que NO es una fuga. Un barrido que se pone en rojo con prosa correcta
    # es un barrido que alguien apaga la primera vez que lo ve fallar sin motivo.
    LIMPIOS = (
        "los servicios deben estar protegidos con sistema de token",
        "ES0901 6.3, seccion 7.1, regla D8, pagina 13",
        "no se declara ninguna tecnologia, ningun emisor y ningun codigo de rechazo",
        "el mecanismo entra como dato declarado con su fuente citada",
        "TOKEN_MECHANISM_UNRESOLVED / TOKEN_PROTECTION_EXCEPTION_UNRESOLVED",
        "D8_MATRIX_BINDING_UNRESOLVED y SERVICE_ENDPOINT_COVERAGE_UNRESOLVED",
        "un camino se identifica por el comportamiento protegido que alcanza",
        "la ruta vieja, la versionada y el controlador secundario entran igual",
        "el metodo alterno del mismo recurso es otro camino al mismo comportamiento",
        "un ingreso, un chequeo de salud o un catalogo no se eximen solos",
        "la puerta de enlace que expone un camino sin pasar por la validacion",
        "un token valido que funciona no dice nada sobre que pasa sin token",
        "NO_TOKEN INVALID_TOKEN VALID_TOKEN son las tres sondas",
        "controles/checks/service-token-protection.py y la policy de al lado",
        "docs/normativa-7.1.md, es0901-7.1.json y la matriz",
        "27 skills instaladas y 31 controles declarados",
        "el header que transporta el token lo declara el proyecto, no esta regla",
        "los roles y los scopes no se verifican en esta regla",
        "una evaluacion formal de seguridad es otra cosa y no sale de aca",
        "PRIMARY ALTERNATE_URL ALTERNATE_METHOD LEGACY_ROUTE VERSIONED_ROUTE",
        "AUTH_HEADER_PARSING y GATEWAY_PRESENT son clases inertes",
        "la fila declara tres agentes duenos y una sola senal",
        # 🔴 Las tres que cuidan los patrones de rol y scope, que son los mas propensos a un
        # falso positivo: `alcance` es una palabra del idioma, no un scope de token.
        "es el alcance de la regla, y esta dicho",
        "no hay endpoints de servicio en alcance",
        "los roles y los scopes no se atribuyen a esta regla",
        # 🔴 Y las mismas formas en ingles, que son las que este repositorio escribe en sus
        # artefactos y las que el barrido tenia mal: `scope` es `alcance`.
        "In scope: the service boundary of the WorkUnit.",
        "Out of scope: authorization, and everything ES0902 governs.",
        "that exceeds the scope of the WorkUnit under review",
        "the role of this policy is to state the obligation",
        "scope: {id, kind, reference}",
        "role: <optional, declared by the project>",
    )
    for limpio in LIMPIOS:
        t.igual("E-18 no dispara con: %s" % limpio[:38], [], _fugas_en(limpio))


# -- E-20 a E-24 — la ejecucion ------------------------------------------------

def test_e20_sin_token_llegando_falla(t):
    """E-20 (D8-15) — la operacion protegida no fue rechazada."""
    sondas = [_sonda("NO_TOKEN", rejected=False), _sonda("INVALID_TOKEN"),
              _sonda("VALID_TOKEN")]
    salida = _evaluar(_caso(items=[_endpoint(sondas=sondas)]), _senal())
    t.igual("E-20 el estado", "FAIL", salida["state"])
    t.igual("E-20 el motivo", "PROTECTED_BEHAVIOR_REACHED_WITHOUT_TOKEN", salida["reason"])
    t.verdadero("E-20 no aprueba", not CHECK.aprueba(salida))


def test_e21_token_invalido_llegando_falla(t):
    """E-21 (D8-16) — un token invalido que pasa es lo mismo que ninguno."""
    sondas = [_sonda("NO_TOKEN"), _sonda("INVALID_TOKEN", rejected=False),
              _sonda("VALID_TOKEN")]
    salida = _evaluar(_caso(items=[_endpoint(sondas=sondas)]), _senal())
    t.igual("E-21 el estado", "FAIL", salida["state"])
    t.igual("E-21 el motivo", "PROTECTED_BEHAVIOR_REACHED_WITHOUT_TOKEN", salida["reason"])
    t.verdadero("E-21 no aprueba", not CHECK.aprueba(salida))


def test_e22_el_token_valido_aporta_la_positiva(t):
    """E-22 (D8-17) — con las dos negativas y traza real, el camino pasa."""
    salida = _evaluar(_caso(), _senal())
    t.igual("E-22 el estado", "PASS", salida["state"])
    t.verdadero("E-22 aprueba", CHECK.aprueba(salida))
    t.igual("E-22 las tres sondas se evaluaron", 3, len(salida["endpoints"][0]["probes"]))
    t.igual("E-22 y las tres pasaron", ["PASS"] * 3,
            [s["state"] for s in salida["endpoints"][0]["probes"]])
    t.vacio("E-22 no falta ninguna negativa", salida["endpoints"][0]["missingProbes"])
    # Y el camino protegido que NO funciona con un token valido no completa la positiva.
    sondas = [_sonda("NO_TOKEN"), _sonda("INVALID_TOKEN"),
              _sonda("VALID_TOKEN", succeeded=False)]
    t.igual("E-22 sin camino protegido que funcione, no pasa", "PARTIAL",
            _evaluar(_caso(items=[_endpoint(sondas=sondas)]), _senal())["state"])


def test_e23_las_dos_negativas_son_obligatorias(t):
    """E-23 (§) — falta una y no pasa; sin objetivo, TEST_TARGET_UNAVAILABLE."""
    # 🔴 Las dos negativas van CLAVADAS por la misma razon que en E-08: leerlas de la constante
    # hace que sacar una del contrato achique el recorrido y el test siga verde.
    t.igual("E-23 las negativas son estas dos", ("NO_TOKEN", "INVALID_TOKEN"), CHECK.NEGATIVAS)
    t.igual("E-23 y las sondas son tres", ("NO_TOKEN", "INVALID_TOKEN", "VALID_TOKEN"),
            CHECK.SONDAS)
    for falta in ("NO_TOKEN", "INVALID_TOKEN"):
        casos = tuple(c for c in CHECK.SONDAS if c != falta)
        salida = _evaluar(_caso(items=[_endpoint(sondas=_sondas(casos))]), _senal())
        t.igual("E-23 sin %s no pasa" % falta, "PARTIAL", salida["state"])
        t.igual("E-23 sin %s deja el motivo" % falta, "NEGATIVE_PROBE_COVERAGE_INCOMPLETE",
                salida["reason"])
        t.verdadero("E-23 sin %s lo nombra" % falta,
                    falta in salida["endpoints"][0]["missingProbes"])
    # 🔴 La positiva sola es el falso verde mas caro de esta regla.
    solo_positiva = _caso(items=[_endpoint(sondas=_sondas(("VALID_TOKEN",)))])
    t.igual("E-23 la positiva sola no pasa", "PARTIAL", _evaluar(solo_positiva, _senal())["state"])

    salida = _evaluar(_caso(testTarget={}), _senal())
    t.igual("E-23 sin objetivo", "TEST_TARGET_UNAVAILABLE", salida["state"])
    t.verdadero("E-23 sin objetivo no aprueba", not CHECK.aprueba(salida))


def test_e24_lo_mockeado_no_llega_a_pass(t):
    """E-24 (D8-25) — se distingue de lo real y no prueba que el servicio rechace."""
    salida = _evaluar(_caso(evidencia=_evidencias(modo="MOCKED")), _senal())
    t.igual("E-24 el estado", "PARTIAL", salida["state"])
    t.igual("E-24 el motivo", "MOCKED_EVIDENCE_ONLY", salida["reason"])
    t.verdadero("E-24 no aprueba", not CHECK.aprueba(salida))
    t.igual("E-24 los dos modos estan declarados", ("REAL", "MOCKED"), CHECK.MODOS)
    t.igual("E-24 y con evidencia real pasa", "PASS", _evaluar(_caso(), _senal())["state"])
    # Una evidencia de otro build tampoco cuenta.
    ajena = [_ev("p-" + c, buildId="otro-build") for c in CHECK.SONDAS]
    t.igual("E-24 la evidencia de otro build no sostiene", "PARTIAL",
            _evaluar(_caso(evidencia=ajena), _senal())["state"])


# -- E-25 a E-29 — los bypasses ------------------------------------------------

def test_e25_el_camino_feliz_no_tapa_la_ruta_alterna(t):
    """E-25 (D8-18) — protegido mas abierto da FAIL; sin declarar, queda sin resolver."""
    salida = _evaluar(_caso(items=[_endpoint(), _abierto()]), _senal())
    t.igual("E-25 el estado", "FAIL", salida["state"])
    t.igual("E-25 el motivo", "TOKEN_ENFORCEMENT_BYPASS", salida["reason"])
    t.igual("E-25 y nombra el comportamiento con las dos puertas", ["b-aprobar-tramite"],
            salida["bypassedBehaviors"])
    estados = {e["endpointId"]: e["state"] for e in salida["endpoints"]}
    t.igual("E-25 el que cumple sigue en PASS", "PASS", estados["e-primario"])
    t.igual("E-25 y el abierto en FAIL", "FAIL", estados["e-legacy"])

    # 🔴 Sin declarar si exige, no es FAIL ni PASS: es un hueco.
    sin_declarar = {"id": "e-otro", "behaviorId": "b-aprobar-tramite", "kind": "ALTERNATE_URL",
                    "active": True, "public": False, "enforcement": {}, "probes": []}
    salida = _evaluar(_caso(items=[_endpoint(), sin_declarar]), _senal())
    t.igual("E-25 sin declarar queda sin resolver", "PARTIAL", salida["state"])
    t.igual("E-25 con su motivo propio", "TOKEN_REQUIREMENT_UNDECLARED", salida["reason"])
    t.verdadero("E-25 y no aprueba", not CHECK.aprueba(salida))


def test_e26_el_metodo_alterno(t):
    """E-26 (D8-19) — otro metodo sobre el mismo recurso es otro camino."""
    salida = _evaluar(_caso(items=[_endpoint(), _abierto(eid="e-metodo",
                                                         clase="ALTERNATE_METHOD")]), _senal())
    t.igual("E-26 el estado", "FAIL", salida["state"])
    t.igual("E-26 el motivo", "TOKEN_ENFORCEMENT_BYPASS", salida["reason"])
    t.igual("E-26 y el comportamiento queda nombrado", ["b-aprobar-tramite"],
            salida["bypassedBehaviors"])


def test_e27_la_ruta_vieja_y_la_versionada(t):
    """E-27 (D8-20) — legacy y versionada se detectan igual."""
    for clase in ("LEGACY_ROUTE", "VERSIONED_ROUTE"):
        salida = _evaluar(_caso(items=[_endpoint(), _abierto(eid="e-" + clase, clase=clase)]),
                          _senal())
        t.igual("E-27 %s falla" % clase, "FAIL", salida["state"])
        t.igual("E-27 %s con el motivo" % clase, "TOKEN_ENFORCEMENT_BYPASS", salida["reason"])


def test_e28_las_ocho_clases_que_no_son_la_primaria(t):
    """E-28 (D8-18, D8-19, D8-20) — el invariante sobre el producto, no ocho ejemplos."""
    # Las ocho van clavadas por la misma razon que las nueve de E-16.
    otras = ("ALTERNATE_URL", "ALTERNATE_METHOD", "LEGACY_ROUTE", "VERSIONED_ROUTE",
             "SECONDARY_CONTROLLER", "GATEWAY_EXPOSED", "ADMINISTRATIVE", "UPLOAD_DOWNLOAD")
    t.igual("E-28 son estas ocho las que no son la primaria", otras,
            tuple(c for c in CHECK.CLASES if c != CHECK.PRIMARIO))
    for clase in otras:
        salida = _evaluar(_caso(items=[_endpoint(), _abierto(eid="e-" + clase, clase=clase)]),
                          _senal())
        t.igual("E-28 %s alcanzando sin token falla" % clase, "FAIL", salida["state"])
        t.igual("E-28 %s con el mismo motivo" % clase, "TOKEN_ENFORCEMENT_BYPASS",
                salida["reason"])
        t.igual("E-28 %s nombra el comportamiento" % clase, ["b-aprobar-tramite"],
                salida["bypassedBehaviors"])
        t.verdadero("E-28 %s no aprueba" % clase, not CHECK.aprueba(salida))
    # Y un camino abierto a OTRO comportamiento falla igual, aunque no sea un bypass mixto.
    otro = _abierto(eid="e-solo", comportamiento="b-otro")
    salida = _evaluar(_caso(items=[_endpoint(), otro]), _senal())
    t.igual("E-28 un camino abierto solo tambien falla", "FAIL", salida["state"])
    t.vacio("E-28 y no es un comportamiento mixto", salida["bypassedBehaviors"])


def test_e29_un_camino_inactivo_no_es_un_bypass(t):
    """E-29 (§) — inactivo declarado sale; sin declarar, no se da por apagado."""
    inactivo = dict(_abierto(eid="e-apagado"), active=False)
    salida = _evaluar(_caso(items=[_endpoint(), inactivo]), _senal())
    t.igual("E-29 el inactivo no hace fallar", "PASS", salida["state"])
    t.igual("E-29 no se gobierna", ["e-primario"], salida["governedEndpoints"])
    t.igual("E-29 pero se informa", ["e-apagado"], salida["inventory"]["inactive"])

    sin_declarar = dict(_abierto(eid="e-quizas"))
    sin_declarar.pop("active")
    salida = _evaluar(_caso(items=[_endpoint(), sin_declarar]), _senal())
    t.igual("E-29 sin declarar la actividad, no se da por apagado",
            "SERVICE_ENDPOINT_COVERAGE_UNRESOLVED", salida["state"])
    t.verdadero("E-29 y lo dice", "ENDPOINT_ACTIVITY_UNDECLARED" in (salida.get("detail") or ""))


# -- E-30 a E-32 — los endpoints publicos --------------------------------------

def test_e30_el_publico_sin_excepcion(t):
    """E-30 (D8-21) — sin excepcion autoritativa, sin resolver."""
    salida = _evaluar(_caso(items=[_endpoint(), _publico_sin_excepcion()]), _senal())
    t.igual("E-30 el estado", "TOKEN_PROTECTION_EXCEPTION_UNRESOLVED", salida["state"])
    t.verdadero("E-30 no aprueba", not CHECK.aprueba(salida))

    for nombre, excepcion in (
            ("sin fuente", {"id": "x", "reference": "r"}),
            ("con una fuente que no esta", {"id": "x", "source": "PROJECT_CONVENTION",
                                            "reference": "r"}),
            ("sin referencia", {"id": "x", "source": "GCBA_NORMATIVE"}),
            ("en blancos", {"id": " ", "source": "GCBA_NORMATIVE", "reference": " "})):
        publico = _endpoint(eid="e-publico", comportamiento="b-consulta", publico=True,
                            sondas=[], exception=excepcion)
        t.igual("E-30 %s sigue sin resolver" % nombre, "TOKEN_PROTECTION_EXCEPTION_UNRESOLVED",
                _evaluar(_caso(items=[_endpoint(), publico]), _senal())["state"])

    # Con la excepcion declarada y citada, pasa.
    buena = {"id": "excepcion-declarada", "source": "PROJECT_SECURITY_CONTRACT",
             "reference": "acta del proyecto"}
    publico = _endpoint(eid="e-publico", comportamiento="b-consulta", publico=True, sondas=[],
                        exception=buena)
    salida = _evaluar(_caso(items=[_endpoint(), publico]), _senal())
    t.igual("E-30 con excepcion declarada, pasa", "PASS", salida["state"])
    t.igual("E-30 y la excepcion se informa", "excepcion-declarada",
            [e for e in salida["endpoints"] if e["endpointId"] == "e-publico"][0]
            ["exception"]["id"])


def test_e31_ninguna_categoria_se_exime_sola(t):
    """E-31 (D8-22) — las siete, una por una, con el mismo resultado."""
    t.igual("E-31 son siete categorias", 7, len(CATEGORIAS))
    for categoria in CATEGORIAS:
        publico = _endpoint(eid="e-" + categoria, comportamiento="b-" + categoria,
                            publico=True, sondas=[])
        salida = _evaluar(_caso(items=[_endpoint(), publico]), _senal())
        t.igual("E-31 %s no se exime solo" % categoria,
                "TOKEN_PROTECTION_EXCEPTION_UNRESOLVED", salida["state"])
        t.verdadero("E-31 %s no aprueba" % categoria, not CHECK.aprueba(salida))


def test_e32_no_hay_lista_de_exenciones(t):
    """E-32 (D8-22) — ni una estructura que las agrupe, ni una comparacion contra un nombre."""
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))

    # 🔴 Ninguna tupla ni lista literal del modulo agrupa dos categorias o mas. Una sola puede
    # aparecer —`LOGIN_ENDPOINT` es una CLASE DE EVIDENCIA, no una exencion—; dos juntas ya son
    # una lista de exentos.
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Tuple, ast.List)):
            continue
        textos = [e.value.lower() for e in nodo.elts
                  if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        juntas = sorted({c for c in CATEGORIAS
                         for x in textos if c in x})
        t.verdadero("E-32 ninguna lista agrupa categorias: %s" % ", ".join(juntas) or "ok",
                    len(juntas) <= 1)

    # Y ninguna comparacion del modulo es contra el nombre de una categoria.
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Compare):
            continue
        textos = [n.value.lower() for n in [nodo.left] + list(nodo.comparators)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        for texto in textos:
            for categoria in CATEGORIAS:
                t.verdadero("E-32 no compara contra `%s`" % categoria, categoria not in texto)

    # Ni un patron de ruta.
    fuente = RUTA_CHECK.read_text(encoding="utf-8")
    t.vacio("E-32 el check no lleva un patron de ruta",
            re.findall(r"[\"'`]/[a-z0-9{*]", fuente))
    t.vacio("E-32 ni la policy", re.findall(
        r"[\"'`]/[a-z0-9{*]",
        (CONTROLES / "policies" / (POLICY + ".md")).read_text(encoding="utf-8")))


# -- E-33 a E-35 — la frontera de lo que D8 afirma -----------------------------

def test_e33_un_pass_no_afirma_autorizacion(t):
    """E-33 (D8-26) — los roles sin verificar no impiden el PASS, y no se afirman."""
    caso = _caso(authorization={"rolesVerified": False, "scopesVerified": False})
    salida = _evaluar(caso, _senal())
    t.igual("E-33 pasa igual", "PASS", salida["state"])
    t.verdadero("E-33 aprueba", CHECK.aprueba(salida))
    # 🔴 Y no hay ningun veredicto de autorizacion en la salida: lo que no se verifica, no se dice.
    for campo in ("authorization", "roles", "scopes", "rolesVerified", "authorizationState"):
        t.verdadero("E-33 el resultado no declara %s" % campo, campo not in salida)
    texto = repr(salida)
    for palabra in ("role", "scope", "authoriz", "autoriza"):
        t.verdadero("E-33 el resultado no nombra `%s`" % palabra, palabra not in texto.lower())


def _literales_del_check(con_docstrings=False):
    """Las cadenas literales del check, sin los docstrings.

    🔴 Es lo que cierra el hueco de muestreo de E-34 y E-35. Barrer sólo los diez resultados de
    `_caminos()` deja afuera las ramas que ningun camino muestreado alcanza —el detalle de una
    sonda negativa que no fue rechazada, por ejemplo— y una fuga ahi no la ve nadie. Los
    docstrings quedan afuera porque ahi la regla SI puede decir de que no habla.
    """
    arbol = ast.parse(RUTA_CHECK.read_text(encoding="utf-8"))
    docs = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        cuerpo = getattr(nodo, "body", None) or []
        if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)):
            docs.add(id(cuerpo[0].value))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and (con_docstrings or id(n) not in docs)]


def test_e34_un_pass_no_implica_d1_ni_d2(t):
    """E-34 (D8-27) — ni la aplicabilidad, ni los controles, ni el nombre."""
    antes = c_normativa.resolucion({})
    salida = _evaluar(_caso(), _senal())
    t.igual("E-34 D8 pasa", "PASS", salida["state"])
    despues = c_normativa.resolucion({SENAL: _senal("TRUE")})

    for regla in ("D1", "D2"):
        t.verdadero("E-34 %s sigue sin resolver antes" % regla,
                    regla in {u["rule"] for u in antes["unresolvedRules"]})
        t.verdadero("E-34 %s sigue sin resolver despues" % regla,
                    regla in {u["rule"] for u in despues["unresolvedRules"]})
    for control in ("gcba-citizen-authentication-required", "citizen-authentication-mechanism",
                    "credential-entry-delegation-required", "authentication-delegation"):
        t.igual("E-34 %s sigue como estaba" % control, "INSTALLED",
                c_controles.reporte()["controls"].get(control))

    for estado, (caso, senal, doc) in _caminos().items():
        texto = repr(_evaluar(caso, senal, doc))
        for otra in ("D1", "D2", "D5", "D6", "D7"):
            t.verdadero("E-34 en %s no nombra %s" % (estado, otra), otra not in texto)

    # 🔴 La afirmacion es universal sobre los resultados y los diez caminos son un MUESTREO: una
    # rama que ningun camino muestreado alcanza puede nombrar otra regla y nadie lo ve. Se barre
    # entonces el texto que el modulo puede producir, que es el conjunto entero.
    literales = _literales_del_check()
    t.verdadero("E-34 hay literales que barrer", len(literales) > 40)
    for literal in literales:
        for otra in ("D1", "D2", "D3", "D4", "D5", "D6", "D7"):
            t.verdadero("E-34 ninguna cadena del modulo nombra %s: %s" % (otra, literal[:34]),
                        not re.search(r"\b%s\b" % otra, literal))


def test_e35_un_pass_no_implica_otro_estandar(t):
    """E-35 (D8-28) — ni ES0902, ni una aprobacion de seguridad."""
    # 🔴 `aprobacion` y `aprobación` estaban afuera de la lista, y son la palabra con la que el
    # escenario esta escrito: `la aprobacion de seguridad esta vigente` no disparaba nada.
    APROBACION = ("approv", "aprobad", "aprobacion", "aprobación", "assessment",
                  "evaluacion de seguridad", "evaluación de seguridad")
    OTROS = ("ES0902", "ES0903", "PC0901", "GuiaDGISIS", "Obelisco")
    # Las dos cadenas del modulo que llevan el vocabulario adentro por motivos legitimos: una
    # fuente de cobertura declarada y una skill instalada. Van nombradas, no deducidas.
    LEGITIMOS = ("TEAM_APPROVED_TEST_PROFILE", "dev-security-assessment")
    for estado, (caso, senal, doc) in _caminos().items():
        salida = _evaluar(caso, senal, doc)
        texto = repr(salida)
        for otro in OTROS:
            t.verdadero("E-35 en %s no nombra %s" % (estado, otro), otro not in texto)
        for palabra in APROBACION:
            t.verdadero("E-35 en %s no declara `%s`" % (estado, palabra),
                        palabra not in texto.lower())
        if salida.get("source"):
            t.igual("E-35 en %s la tupla es solo la de D8" % estado, TRAZA, salida["source"])

    # Y el conjunto entero de cadenas que el modulo puede producir, no el muestreo de diez.
    for literal in _literales_del_check():
        for otro in OTROS:
            t.verdadero("E-35 ninguna cadena nombra %s: %s" % (otro, literal[:30]),
                        otro not in literal)
        # 🔴 El vocabulario de aprobacion se barre sobre TODAS las cadenas, con una lista de
        # excepciones nombradas: `TEAM_APPROVED_TEST_PROFILE` es una fuente de cobertura y
        # `dev-security-assessment` es una skill instalada, y las dos son legitimas.
        #
        # La version anterior cortaba por "tiene un espacio", y esa frontera dejaba afuera los 329
        # literales sin espacio del modulo — entre ellos TODOS los `reason` y los `state`, que son
        # justo lo que un resultado publica. Dos excepciones nombradas cuestan menos y no dejan
        # nada afuera.
        if literal in LEGITIMOS:
            continue
        for palabra in APROBACION:
            t.verdadero("E-35 ninguna cadena declara `%s`: %s" % (palabra, literal[:30]),
                        palabra not in literal.lower())


# -- E-36 a E-39 — la propagacion, el registro y la traza ----------------------

def test_e36_la_unidad_propaga_los_controles_exactos(t):
    """E-36 (D8-29) — con evidencia y con la forma vieja de booleanos."""
    for nombre, senales in (("con evidencia", {SENAL: _senal("TRUE")}),
                            ("con un booleano", {SENAL: True})):
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-36 %s D8 aplica" % nombre, "D8" in bloque["applicableRules"])
        t.verdadero("E-36 %s propaga la policy" % nombre, POLICY in bloque["declaredPolicies"])
        t.verdadero("E-36 %s propaga el check" % nombre, CHEQUEO in bloque["declaredChecks"])
    # 🔴 Y son los ids EXACTOS de la matriz, no unos parecidos.
    d8 = c_matriz.regla("D8")
    bloque = c_normativa.resolucion({SENAL: True})
    for pid in d8["policies"]:
        t.verdadero("E-36 %s viene de la fila" % pid, pid in bloque["declaredPolicies"])
    for cid in d8["checks"]:
        t.verdadero("E-36 %s viene de la fila" % cid, cid in bloque["declaredChecks"])


def test_e37_los_controles_dejan_de_ser_un_hueco(t):
    """E-37 (D8-30) — instalados, declarados, treinta y cinco, y once reglas completas."""
    reporte = c_controles.reporte()
    t.igual("E-37 son cuarenta y dos controles", 42, reporte["summary"]["declaredControls"])
    t.verdadero("E-37 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-37 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-37 ningun archivo suelto", [], reporte["undeclared"])
    t.vacio("E-37 sin errores de schema", reporte["schemaErrors"])

    for control in (POLICY, CHEQUEO):
        t.igual("E-37 %s esta INSTALLED" % control, "INSTALLED",
                reporte["controls"].get(control))
    resolucion = c_matriz.resolver({SENAL: True})
    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    for control in (POLICY, CHEQUEO):
        t.verdadero("E-37 %s ya no figura como no instalado" % control, control not in faltan)

    instalados = set(c_controles.instalados()["POLICY"]) | set(
        c_controles.instalados()["CHECK"]) | set(c_controles.instalados()["REVIEW"])
    completas = []
    for r in c_matriz.reglas():
        suyos = set(r.get("policies") or []) | set(r.get("checks") or []) | set(
            r.get("reviews") or [])
        if suyos and suyos <= instalados:
            completas.append(r["id"])
    t.igual("E-37 once reglas tienen todos sus controles construidos",
            ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "G1", "G2", "P1"],
            sorted(completas))


def test_e38_todo_resultado_conserva_la_traza(t):
    """E-38 (D8-31) — en todos los caminos menos el del binding, que lo dice."""
    for estado, (caso, senal, doc) in _caminos().items():
        salida = _evaluar(caso, senal, doc)
        t.igual("E-38 %s dice que control es" % estado, CHEQUEO, salida["control"])
        t.igual("E-38 %s dice de que regla" % estado, "D8", salida["rule"])
        if estado == "D8_MATRIX_BINDING_UNRESOLVED":
            t.igual("E-38 el binding sin resolver no inventa la tupla", {}, salida["source"])
            t.verdadero("E-38 y declara que falta", salida["sourceMissing"] is True)
        else:
            t.igual("E-38 %s conserva la tupla" % estado, TRAZA, salida["source"])
            t.verdadero("E-38 %s no declara que falte" % estado,
                        "sourceMissing" not in salida)
    # 🔴 Y la tupla sale de la matriz, no de una constante del modulo.
    doc = copy.deepcopy(c_matriz.cargar())
    doc["standard"]["section"] = "7.1"
    t.igual("E-38 la tupla se deriva", TRAZA, _evaluar(_caso(), _senal(), doc)["source"])


def test_e39_los_estados_existen_y_solo_pasa_uno(t):
    """E-39 (§ estados) — los diez se alcanzan, y ninguno sin resolver aprueba."""
    t.igual("E-39 son diez estados declarados", 10, len(CHECK.ESTADOS))
    caminos = _caminos()
    t.igual("E-39 hay un camino por estado", sorted(CHECK.ESTADOS), sorted(caminos))
    for estado, (caso, senal, doc) in sorted(caminos.items()):
        salida = _evaluar(caso, senal, doc)
        t.igual("E-39 se alcanza %s" % estado, estado, salida["state"])
        t.igual("E-39 %s aprueba solo si es PASS" % estado, estado == "PASS",
                CHECK.aprueba(salida))
