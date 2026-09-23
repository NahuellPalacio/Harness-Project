# D5: verificar que el valor que la aplicacion USA sea el normalizado, sin inventar el contrato.
#
# Escenarios E-01 a E-37 de docs/cambios/d5-normalizacion-catastral-de-direcciones/spec.md. Entre
# parentesis, el D5-nn del pedido de instalacion.
#
# 🔴 Nada de esto ejecuta un frontend. Lo que se verifica es el CONTROL: que la identidad del
# proveedor entre como dato declarado, que un autocompletado no alcance, que la llamada al servicio
# no alcance -lo que alcanza es que el resultado normalizado se CONSUMA-, y que los cinco tipos de
# camino se declaren todos porque el silencio no es ausencia.
import importlib.util
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"

sys.path.insert(0, str(BIN))
from orquestacion import controles as c_controles    # noqa: E402
from orquestacion import matriz as c_matriz          # noqa: E402
from orquestacion import normativa as c_normativa    # noqa: E402
from orquestacion import registro_agentes as c_reg   # noqa: E402
from orquestacion import senales as c_senales        # noqa: E402


def _cargar(nombre, alias):
    spec = importlib.util.spec_from_file_location(alias, CONTROLES / "checks" / (nombre + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CHECK = _cargar("address-normalization-integration", "d5_check")

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D5"}

SENAL = "frontendAddressInputPresent"
SENAL_DE_FRONTEND = "frontendPresent"
POLICY = "gcba-cadastral-address-normalization-required"
CHEQUEO = "address-normalization-integration"

BUILD = {"id": "b-2026-09-21", "runtime": "chromium-129"}
ALCANCE = {"id": "PROY-1", "kind": "PROJECT", "reference": "ficha del proyecto"}
PROVEEDOR = {"id": "opcion-catastral-declarada", "source": "GCBA_NORMATIVE",
             "reference": "ES0901 6.3, pag. 19"}
CONTRATO = {"id": "contrato-de-integracion-catastral", "source": "ASI_INTEGRATION_CONTRACT",
            "reference": "acta de integracion del proyecto"}

CLASES = CHECK.CLASES_DE_CAMINO


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="s-1", tipo="PROJECT_DOCUMENTATION", ref="requisito de UX",
              claim="la pantalla permite buscar y cargar una direccion", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid=SENAL, alcance=ALCANCE, **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    if alcance is not None:
        s["scope"] = dict(alcance)
    s.update(extra)
    return s


def _ev(eid="e-1", tipo="NORMALIZED_ADDRESS_RUN", modo="REAL",
        proveedor="opcion-catastral-declarada", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": "corrida#1",
         "claim": "el flujo normalizo la direccion", "buildId": BUILD["id"],
         "runtime": BUILD["runtime"], "mode": modo, "provider": proveedor}
    e.update(extra)
    return e


def _cadena(crudo="v-crudo", normalizado="v-normalizado", consumido=None, sin=()):
    """La cadena de cinco etapas. `sin` saca etapas para armar los casos incompletos."""
    cadena = {CHECK.CRUDO: crudo, CHECK.PEDIDO: crudo, CHECK.RESPUESTA: normalizado,
              CHECK.NORMALIZADO: normalizado,
              CHECK.CONSUMIDO: normalizado if consumido is None else consumido}
    for etapa in sin:
        cadena.pop(etapa, None)
    return cadena


def _res(flujo="f-busqueda", clase="SEARCH", proveedor="opcion-catastral-declarada",
         cadena=None, desde=CHECK.NORMALIZADO, ejecucion="EXECUTED", refs=("e-1",)):
    return {"flowId": flujo, "kind": clase, "provider": proveedor,
            "execution": ejecucion, "chain": _cadena() if cadena is None else cadena,
            "consumedFrom": desde, "evidenceRefs": list(refs)}


def _caminos(flujos=None, fuente="ROUTE_INVENTORY", ausentes=None, sin=()):
    """El inventario con los cinco tipos: SEARCH con flujos y los otros cuatro ausentes.

    `ausentes` permite darle flujos a otro tipo; `sin` saca un tipo del inventario para el caso
    del camino en silencio.
    """
    flujos = [{"flowId": "f-busqueda"}] if flujos is None else flujos
    con_flujos = {"SEARCH": flujos}
    con_flujos.update(ausentes or {})
    caminos = []
    for clase in CLASES:
        if clase in sin:
            continue
        if con_flujos.get(clase):
            caminos.append({"kind": clase, "flows": list(con_flujos[clase])})
        else:
            caminos.append({"kind": clase, "absent": True, "source": "PROJECT_ARCHITECTURE"})
    return {"source": fuente, "paths": caminos}


def _caso(caminos=None, resultados=None, evidencia=None, **extra):
    caso = {
        "application": {"id": "tramites", "environment": "test"},
        "build": dict(BUILD),
        "scope": dict(ALCANCE),
        "testTarget": {"available": True},
        "cadastralProvider": dict(PROVEEDOR),
        "integrationContract": dict(CONTRATO),
        "addressFlows": _caminos() if caminos is None else caminos,
        "results": [_res()] if resultados is None else resultados,
        "evidence": [_ev()] if evidencia is None else evidencia,
    }
    caso.update(extra)
    return caso


def _con_evidencia_sola(tipo, eid="e-1"):
    """Un caso donde la unica evidencia del flujo es de la clase que se prueba."""
    return _caso(resultados=[_res(refs=(eid,))], evidencia=[_ev(eid, tipo=tipo)])


def _los_nueve_caminos():
    """Un caso por cada uno de los nueve estados. El sujeto de los invariantes de salida."""
    return {
        CHECK.PASA: (_caso(), _senal("TRUE")),
        CHECK.FALLA: (_caso(resultados=[_res(cadena=_cadena(consumido="v-crudo"))]),
                      _senal("TRUE")),
        CHECK.PARCIAL: (_caso(evidencia=[_ev(modo="MOCKED")]), _senal("TRUE")),
        CHECK.NO_APLICA: (_caso(), _senal("FALSE")),
        CHECK.SIN_RESOLVER: (_caso(), _senal("UNRESOLVED")),
        CHECK.SIN_COBERTURA: (_caso(caminos={}), _senal("TRUE")),
        CHECK.SIN_PROVEEDOR: (_caso(cadastralProvider={}), _senal("TRUE")),
        CHECK.SIN_CONTRATO: (_caso(integrationContract={}), _senal("TRUE")),
        CHECK.SIN_OBJETIVO: (_caso(testTarget={"available": False}), _senal("TRUE")),
    }


# -- E-01 a E-09 — la senal, la aplicabilidad y el alcance ---------------------

def test_e01_d5_sigue_conditional_sobre_su_senal(t):
    """E-01 (D5-01, D5-08) — la matriz ya lo declaraba y este cambio no la edita."""
    fila = c_matriz.regla("D5")
    t.igual("E-01 D5 es CONDITIONAL", "CONDITIONAL", fila["applicability"]["mode"])
    t.igual("E-01 sobre una sola senal", [SENAL], fila["applicability"]["signals"])
    t.igual("E-01 con su policy, exactamente", [POLICY], fila["policies"])
    t.igual("E-01 y su check, exactamente", [CHEQUEO], fila["checks"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", fila["status"])
    t.igual("E-01 con sus dos agentes primarios", ["dev-integration", "dev-frontend"],
            fila["primaryAgents"])

    # 🔴 Los ids del check y de la policy salen de LA MATRIZ, no de una constante de este test.
    t.igual("E-01 el check dice ser de D5", "D5", CHECK.REGLA)
    t.igual("E-01 y nombra la senal de la matriz", fila["applicability"]["signals"][0],
            CHECK.SENAL)
    t.igual("E-01 el id del control es el de la matriz", fila["checks"][0], CHECK.CONTROL)

    # Y la regla citable sigue siendo la misma.
    citable = c_normativa.reglas()
    d5 = [r for r in citable if r.get("rule") == "D5"]
    t.igual("E-01 hay una sola fila citable de D5", 1, len(d5))
    t.igual("E-01 con su pagina", 13, d5[0]["page"])
    t.contiene("E-01 y su texto", "opcion catastral", d5[0]["text"])


def test_e02_true_hace_aplicable(t):
    """E-02 (D5-02) — TRUE con evidencia hace aplicable a D5."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-02 D5 aplica", "D5" in bloque["applicableRules"])
    t.verdadero("E-02 con su policy declarada", POLICY in bloque["declaredPolicies"])
    t.verdadero("E-02 y su check", CHEQUEO in bloque["declaredChecks"])

    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-02 el check evalua", CHECK.PASA, salida["state"])
    t.igual("E-02 con la senal en TRUE", "TRUE", salida["signalValue"])


def test_e03_false_deja_no_aplicable(t):
    """E-03 (D5-03) — FALSE con evidencia deja NOT_APPLICABLE."""
    bloque = c_normativa.resolucion({SENAL: _senal("FALSE")})
    t.verdadero("E-03 D5 no aplica", "D5" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no queda sin resolver",
                "D5" not in {u["rule"] for u in bloque["unresolvedRules"]})

    salida = CHECK.evaluar(_caso(), _senal("FALSE"))
    t.igual("E-03 el check no aplica", CHECK.NO_APLICA, salida["state"])
    t.vacio("E-03 y no evalua ningun flujo", salida["flows"])


def test_e04_sin_evidencia_queda_sin_resolver(t):
    """E-04 (D5-04) — sin senal, APPLICABILITY_UNRESOLVED con el nombre de la que falta."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D5 queda sin resolver", "D5" in sin_resolver)
    t.verdadero("E-04 con el nombre de la senal que falta",
                SENAL in sin_resolver["D5"]["missingSignals"])
    t.verdadero("E-04 y no aparece como que no aplica", "D5" not in bloque["notApplicableRules"])

    salida = CHECK.evaluar(_caso(), None)
    t.igual("E-04 el check no resuelve", CHECK.SIN_RESOLVER, salida["state"])
    t.igual("E-04 y dice cual falta", [SENAL], salida["missingSignals"])


def test_e05_la_ausencia_nunca_es_false(t):
    """E-05 (D5-05) — lo ausente no se convierte en que no aplica, por ningun camino."""
    # 1. FALSE sin evidencia se degrada a UNRESOLVED.
    resuelta = c_senales.resolver_una(_senal("FALSE", evidencia=[]))
    t.igual("E-05 un FALSE sin evidencia no queda en FALSE", "UNRESOLVED", resuelta["value"])
    t.verdadero("E-05 con SIGNAL_EVIDENCE_MISSING", c_senales.SIN_EVIDENCIA in resuelta["states"])

    # 2. La ausencia de una palabra no sostiene FALSE. Una evidencia que afirma "no se encontro
    #    ningun campo llamado direccion" es una fuente debil y no sostiene nada.
    por_ausencia = _senal("FALSE", evidencia=[
        _ev_senal(tipo="AGENT_STATEMENT", claim="no encontre ningun input llamado direccion")])
    t.igual("E-05 la palabra de un agente sobre una ausencia no sostiene FALSE", "UNRESOLVED",
            c_senales.resolver_una(por_ausencia)["value"])
    por_dependencia = _senal("FALSE", evidencia=[
        _ev_senal(tipo="REPOSITORY_DEPENDENCY", claim="no hay libreria de direcciones instalada")])
    t.igual("E-05 ni una dependencia ausente", "UNRESOLVED",
            c_senales.resolver_una(por_dependencia)["value"])

    # 3. Una senal que la matriz no declara se rechaza.
    inventada = c_senales.resolver_una(_senal("TRUE", sid="addressFieldPresent"))
    t.igual("E-05 una senal inventada no resuelve", "UNRESOLVED", inventada["value"])
    t.verdadero("E-05 con SIGNAL_NOT_DECLARED", c_senales.NO_DECLARADA in inventada["states"])

    # 4. 🔴 Y en la resolucion, que es por donde viaja a un plan: una senal que no resuelve NO
    #    convierte a D5 en no aplicable. Lo tenian los cinco escenarios hermanos y este no: la
    #    pasada de mutaciones mostro que hacer entrar lo UNRESOLVED como False no ponia en rojo
    #    ningun test de D5, solo los de las otras reglas.
    for nombre, senal in (("UNRESOLVED", _senal("UNRESOLVED")),
                          ("sin evidencia", _senal("TRUE", evidencia=[])),
                          ("invalida", _senal("TRUE", sid="addressFieldPresent")),
                          ("con evidencia que no referencia nada",
                           _senal("TRUE", evidencia=[_ev_senal(ref="  ")]))):
        bloque = c_normativa.resolucion({SENAL: senal})
        t.verdadero("E-05 una senal %s no vuelve a D5 no aplicable" % nombre,
                    "D5" not in bloque["notApplicableRules"])
        t.verdadero("E-05 una senal %s la deja sin resolver" % nombre,
                    "D5" in {u["rule"] for u in bloque["unresolvedRules"]})
        t.verdadero("E-05 una senal %s no la hace aplicable" % nombre,
                    "D5" not in bloque["applicableRules"])

    # 5. Y en el check: sin senal no aplica nada, no se aprueba nada.
    for senal in (None, _senal("UNRESOLVED"), _senal("FALSE", evidencia=[])):
        salida = CHECK.evaluar(_caso(), senal if senal is None else
                               c_senales.resolver_una(senal))
        t.igual("E-05 %r no se convierte en NOT_APPLICABLE" % (senal and senal["value"]),
                CHECK.SIN_RESOLVER, salida["state"])
        t.igual("E-05 y no aprueba", False, CHECK.aprueba(salida))


def test_e06_frontend_present_solo_no_alcanza(t):
    """E-06 (D5-06) — un frontend no es un campo de direccion."""
    t.verdadero("E-06 la senal de frontend esta nombrada como la que no sustituye",
                SENAL_DE_FRONTEND in CHECK.SENALES_QUE_NO_SUSTITUYEN)
    t.verdadero("E-06 y no es la senal de D5", CHECK.SENAL != SENAL_DE_FRONTEND)

    # La matriz no la acepta para D5.
    bloque = c_normativa.resolucion({SENAL_DE_FRONTEND: _senal("TRUE", sid=SENAL_DE_FRONTEND)})
    t.verdadero("E-06 D5 no aplica por frontendPresent", "D5" not in bloque["applicableRules"])
    t.verdadero("E-06 y queda sin resolver",
                "D5" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-06 sin exigir la policy de D5", POLICY not in bloque["declaredPolicies"])

    # Y el check tampoco: frontendPresent en TRUE no hace nada.
    salida = CHECK.evaluar(_caso(), _senal("UNRESOLVED"),
                           _senal("TRUE", sid=SENAL_DE_FRONTEND))
    t.igual("E-06 el check sigue sin resolver", CHECK.SIN_RESOLVER, salida["state"])
    t.igual("E-06 y no deriva nada", None, salida.get("derivation"))

    # 🔴 Ni con la completitud de alcance declarada, que es lo unico que habilita la derivacion
    # desde el FALSE. La pasada de mutaciones encontro este hueco: sin este caso, invertir la
    # guarda de la derivacion no ponia nada en rojo, porque el caso feliz de E-06 no declara
    # completitud y caia igual en SIN_RESOLVER por otro motivo.
    completa = {"complete": True, "source": "WORKUNIT_SCOPE_DEFINITION",
                "reference": "definicion de alcance de la unidad"}
    con_completitud = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"),
                                    _senal("TRUE", sid=SENAL_DE_FRONTEND))
    t.igual("E-06 con completitud declarada y un frontend que existe, sigue sin resolver",
            CHECK.SIN_RESOLVER, con_completitud["state"])
    t.igual("E-06 y no se deriva un FALSE", None, con_completitud.get("derivation"))
    t.verdadero("E-06 no aparece como que no aplica",
                con_completitud["state"] != CHECK.NO_APLICA)

    # Y con frontendPresent sin resolver, tampoco: la derivacion sale del FALSE, no de la falta.
    sin_resolver = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"),
                                 _senal("UNRESOLVED", sid=SENAL_DE_FRONTEND))
    t.igual("E-06 con frontendPresent sin resolver tampoco deriva", None,
            sin_resolver.get("derivation"))
    t.igual("E-06 y queda sin resolver", CHECK.SIN_RESOLVER, sin_resolver["state"])


def test_e07_frontend_ausente_con_completitud_puede_resolver_false(t):
    """E-07 (D5-07) — la unica derivacion que hay, y lo que le falta cuando no alcanza."""
    completa = {"complete": True, "source": "WORKUNIT_SCOPE_DEFINITION",
                "reference": "definicion de alcance de la unidad"}
    sin_frontend = _senal("FALSE", sid=SENAL_DE_FRONTEND)

    salida = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"), sin_frontend)
    t.igual("E-07 con completitud declarada, D5 no aplica", CHECK.NO_APLICA, salida["state"])
    t.igual("E-07 y lo dice", CHECK.DERIVADA, salida["reason"])
    t.igual("E-07 la derivacion nombra de donde salio", SENAL_DE_FRONTEND,
            salida["derivation"]["from"])
    t.igual("E-07 con su fuente", "WORKUNIT_SCOPE_DEFINITION", salida["derivation"]["source"])
    t.contiene("E-07 y su referencia", "alcance", salida["derivation"]["reference"])

    # 🔴 Sin la completitud, o con una fuente que no esta en la lista, o sin referencia: no se
    # deriva nada. Un booleano suelto seria una puerta de salida que nadie tiene que respaldar.
    faltantes = {
        "sin completitud": {},
        "completitud en False": {"complete": False, "source": "PROJECT_ARCHITECTURE",
                                 "reference": "x"},
        "fuente que no esta en la lista": {"complete": True, "source": "AGENT_STATEMENT",
                                           "reference": "x"},
        "sin referencia": {"complete": True, "source": "PROJECT_ARCHITECTURE", "reference": " "},
    }
    for nombre, completitud in sorted(faltantes.items()):
        salida = CHECK.evaluar(_caso(scopeCompleteness=completitud), _senal("UNRESOLVED"),
                               sin_frontend)
        t.igual("E-07 %s no resuelve" % nombre, CHECK.SIN_RESOLVER, salida["state"])
        t.igual("E-07 %s lo dice" % nombre, CHECK.SIN_COMPLETITUD, salida["reason"])
        t.igual("E-07 %s no deriva" % nombre, None, salida.get("derivation"))

    # Y la senal propia manda sobre la derivacion: si D5 tiene su propia senal, no se deriva.
    propia = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("TRUE"), sin_frontend)
    t.igual("E-07 la senal propia en TRUE manda", CHECK.PASA, propia["state"])
    t.igual("E-07 y no hay derivacion", None, propia.get("derivation"))

    # 🔴 `complete` se exige `True`, no truthy. Es la unica guarda de esta regla cuyo sentido de
    # falla SACA A D5 DEL REPORTE, asi que un `complete: "no"` -escrito por quien queria decir
    # que no esta completo- no puede derivar un NOT_APPLICABLE.
    for valor in ("no", "false", "0", -1, 1, [1], {"a": 1}, "True"):
        salida = CHECK.evaluar(
            _caso(scopeCompleteness=dict(completa, complete=valor)),
            _senal("UNRESOLVED"), sin_frontend)
        t.igual("E-07 complete=%r no deriva" % (valor,), CHECK.SIN_RESOLVER, salida["state"])
        t.igual("E-07 complete=%r lo dice" % (valor,), CHECK.SIN_COMPLETITUD, salida["reason"])
        t.igual("E-07 complete=%r no saca la regla del reporte" % (valor,), None,
                salida.get("derivation"))

    # 🔴 Y tiene que ser LA senal de frontend. La version anterior no le miraba el `signalId` y
    # publicaba la constante como origen: pasarle cualquier otra senal en FALSE derivaba igual y
    # le atribuia el FALSE a `frontendPresent`. La derivacion mentia de donde salio.
    for sid in ("cualquierOtraSenal", SENAL, "georeferencedVisualizationPresent", ""):
        salida = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"),
                               _senal("FALSE", sid=sid))
        t.igual("E-07 un FALSE de `%s` no deriva a D5" % sid, CHECK.SIN_RESOLVER,
                salida["state"])
        t.igual("E-07 y no se le atribuye a frontendPresent" , None, salida.get("derivation"))

    # Y cuando si deriva, el origen que publica es el de la senal que entro.
    salida = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"), sin_frontend)
    t.igual("E-07 el origen publicado es el signalId de la senal que entro",
            sin_frontend["signalId"], salida["derivation"]["from"])


def test_e08_la_senal_sale_de_evidencia_de_un_flujo_de_direcciones(t):
    """E-08 — una dependencia o la palabra de un agente no encienden la senal."""
    for tipo in c_senales.FUENTES_DEBILES:
        sola = _senal("TRUE", evidencia=[_ev_senal(tipo=tipo)])
        resuelta = c_senales.resolver_una(sola)
        t.igual("E-08 %s sola no sostiene la senal" % tipo, "UNRESOLVED", resuelta["value"])
        t.verdadero("E-08 %s da SIGNAL_EVIDENCE_MISSING" % tipo,
                    c_senales.SIN_EVIDENCIA in resuelta["states"])

    # Las que si sostienen, sostienen.
    for tipo in ("TASK_CONTEXT", "PROJECT_CONTEXT", "REPOSITORY_CONFIGURATION",
                 "HUMAN_CONFIRMATION", "JIRA_FICHA_DE_PROYECTO", "PROJECT_DOCUMENTATION"):
        resuelta = c_senales.resolver_una(_senal("TRUE", evidencia=[_ev_senal(tipo=tipo)]))
        t.igual("E-08 %s sostiene la senal" % tipo, "TRUE", resuelta["value"])

    # Y una evidencia sin referencia o sin claim no cuenta, cualquiera sea su clase.
    for hueco in ("reference", "claim"):
        e = _ev_senal()
        e[hueco] = "   "
        t.igual("E-08 una evidencia sin %s no cuenta" % hueco, "UNRESOLVED",
                c_senales.resolver_una(_senal("TRUE", evidencia=[e]))["value"])


def test_e09_el_alcance_de_la_senal_y_de_la_evaluacion(t):
    """E-09 (§4) — mezclar alcances sin declarar la relacion deja la aplicabilidad sin resolver."""
    t.igual("E-09 hay tres clases de alcance", ("PROJECT", "WORKUNIT", "TASK"), CHECK.ALCANCES)
    # 🔴 No hay una relacion "el mismo": dos alcances iguales no declaran nada, y una relacion
    # que dijera "el mismo" sobre dos distintos seria una contradiccion declarable.
    t.igual("E-09 y dos relaciones posibles, ninguna de identidad", 2, len(CHECK.RELACIONES))

    # 1. La evaluacion sin alcance.
    salida = CHECK.evaluar(_caso(scope={}), _senal("TRUE"))
    t.igual("E-09 sin alcance de la evaluacion no resuelve", CHECK.SIN_RESOLVER, salida["state"])
    t.igual("E-09 y lo dice", CHECK.SIN_ALCANCE, salida["reason"])

    # 2. La senal sin alcance, y con un `kind` que no existe.
    for nombre, senal in (("sin alcance", _senal("TRUE", alcance=None)),
                          ("con un kind inventado",
                           _senal("TRUE", alcance={"id": "X", "kind": "SPRINT",
                                                   "reference": "y"})),
                          ("con el id en blancos",
                           _senal("TRUE", alcance={"id": "  ", "kind": "PROJECT",
                                                   "reference": "y"}))):
        salida = CHECK.evaluar(_caso(), senal)
        t.igual("E-09 la senal %s no resuelve" % nombre, CHECK.SIN_RESOLVER, salida["state"])
        t.igual("E-09 la senal %s lo dice" % nombre, CHECK.SIN_ALCANCE, salida["reason"])

    # 3. Alcances distintos sin relacion declarada: el caso que el pedido prohibe.
    de_la_unidad = {"id": "WU-7", "kind": "WORKUNIT", "reference": "unidad de trabajo"}
    salida = CHECK.evaluar(_caso(scope=de_la_unidad), _senal("TRUE"))
    t.igual("E-09 mezclar alcances no resuelve", CHECK.SIN_RESOLVER, salida["state"])
    t.igual("E-09 con SCOPE_MISMATCH", CHECK.ALCANCE_CRUZADO, salida["reason"])
    t.igual("E-09 y sin publicar ninguna relacion", None, salida.get("scopeRelation"))

    # 4. Con la relacion declarada pero sin citar donde: tampoco.
    sin_cita = CHECK.evaluar(
        _caso(scope=de_la_unidad,
              scopeRelation={"relation": "SIGNAL_SCOPE_CONTAINS_EVALUATION", "reference": "  "}),
        _senal("TRUE"))
    t.igual("E-09 una relacion sin cita no alcanza", CHECK.SIN_RESOLVER, sin_cita["state"])
    t.igual("E-09 y con una relacion que no existe tampoco", CHECK.SIN_RESOLVER,
            CHECK.evaluar(_caso(scope=de_la_unidad,
                                scopeRelation={"relation": "SAME", "reference": "acta"}),
                          _senal("TRUE"))["state"])

    # 5. Con la relacion declarada y citada: se evalua, Y LA RELACION APARECE EN LA SALIDA.
    relacion = {"relation": "SIGNAL_SCOPE_CONTAINS_EVALUATION",
                "reference": "acta de alcance del proyecto"}
    salida = CHECK.evaluar(_caso(scope=de_la_unidad, scopeRelation=relacion), _senal("TRUE"))
    t.igual("E-09 con la relacion declarada se evalua", CHECK.PASA, salida["state"])
    t.igual("E-09 y la relacion se publica", "SIGNAL_SCOPE_CONTAINS_EVALUATION",
            salida["scopeRelation"]["relation"])
    t.contiene("E-09 con su cita", "acta", salida["scopeRelation"]["reference"])
    t.igual("E-09 nombrando la senal cruzada", SENAL, salida["scopeRelation"]["signal"])
    t.igual("E-09 el alcance de la evaluacion tambien", "WORKUNIT", salida["scope"]["kind"])

    # 6. Y el alcance de la senal DERIVADA tambien se controla: derivar de un frontendPresent de
    #    todo el proyecto para una unidad, sin declarar la relacion, es la misma mezcla.
    completa = {"complete": True, "source": "WORKUNIT_SCOPE_DEFINITION", "reference": "alcance"}
    cruzada = CHECK.evaluar(
        _caso(scope=de_la_unidad, scopeCompleteness=completa),
        _senal("UNRESOLVED", alcance=de_la_unidad),
        _senal("FALSE", sid=SENAL_DE_FRONTEND))
    t.igual("E-09 la senal derivada tambien pasa por el alcance", CHECK.SIN_RESOLVER,
            cruzada["state"])
    t.igual("E-09 con SCOPE_MISMATCH", CHECK.ALCANCE_CRUZADO, cruzada["reason"])

    # 7. 🔴 La forma VIEJA de una senal -un booleano suelto, un string- no puede declarar alcance,
    #    asi que su alcance es ambiguo por construccion. La version anterior la salteaba con un
    #    `continue` y con eso la guarda entera se evadia: `evaluar(caso, True)` salia PASS.
    for nombre, suelta in (("un booleano", True), ("un string", "TRUE"), ("un 1", 1)):
        salida = CHECK.evaluar(_caso(), suelta)
        t.igual("E-09 %s no declara alcance y no resuelve" % nombre, CHECK.SIN_RESOLVER,
                salida["state"])
        t.igual("E-09 %s lo dice" % nombre, CHECK.SIN_ALCANCE, salida["reason"])
        t.igual("E-09 %s no aprueba" % nombre, False, CHECK.aprueba(salida))
    # Y en la derivacion, lo mismo: un frontendPresent booleano no saca la regla del reporte.
    por_booleano = CHECK.evaluar(_caso(scopeCompleteness=completa), _senal("UNRESOLVED"), False)
    t.igual("E-09 un frontendPresent booleano no deriva un NOT_APPLICABLE", CHECK.SIN_RESOLVER,
            por_booleano["state"])
    t.igual("E-09 y lo dice", CHECK.SIN_ALCANCE, por_booleano["reason"])

    # 8. 🔴 Y el camino por el que una senal viaja DE VERDAD tiene que llegar con su alcance.
    #    `senales.resolver_una` no copiaba `scope`, asi que el campo que este cambio le agrega al
    #    schema existia en el documento y desaparecia en la resolucion: toda corrida real salia
    #    SCOPE_UNDECLARED y la clausula de la relacion declarada era inalcanzable. El mecanismo
    #    quedaba estricto donde el dato no podia cumplir y laxo donde no se declaro nada.
    resuelta = c_senales.resolver_una(_senal("TRUE"))
    t.igual("E-09 la resolucion conserva el alcance", ALCANCE["id"], resuelta["scope"]["id"])
    t.igual("E-09 con su clase", "PROJECT", resuelta["scope"]["kind"])
    t.igual("E-09 y su referencia", ALCANCE["reference"], resuelta["scope"]["reference"])
    t.igual("E-09 una senal resuelta evalua sin SCOPE_UNDECLARED", CHECK.PASA,
            CHECK.evaluar(_caso(), resuelta)["state"])

    # Y por el bloque normativo, que es lo que llega a un plan.
    del_bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})["signals"][SENAL]
    t.igual("E-09 el bloque normativo tambien lo conserva", ALCANCE["id"],
            del_bloque["scope"]["id"])
    t.igual("E-09 y con eso el check evalua", CHECK.PASA,
            CHECK.evaluar(_caso(), del_bloque)["state"])
    # Con la relacion declarada, desde una senal resuelta de otro alcance.
    de_proyecto = c_senales.resolver_una(_senal("TRUE"))
    t.igual("E-09 la relacion declarada es alcanzable desde una senal resuelta", CHECK.PASA,
            CHECK.evaluar(_caso(scope=de_la_unidad, scopeRelation=relacion),
                          de_proyecto)["state"])
    # Y una senal resuelta SIN alcance sigue siendo SCOPE_UNDECLARED: el campo es opcional en el
    # schema, y esta regla lo exige.
    t.igual("E-09 una senal resuelta sin alcance no resuelve", CHECK.SIN_RESOLVER,
            CHECK.evaluar(_caso(), c_senales.resolver_una(
                _senal("TRUE", alcance=None)))["state"])


# -- E-10 a E-13 — el proveedor y el contrato, que no se inventan --------------

def test_e10_sin_proveedor_no_se_inventa(t):
    """E-10 (D5-13) — sin identidad declarada, CADASTRAL_PROVIDER_UNRESOLVED."""
    salida = CHECK.evaluar(_caso(cadastralProvider={}), _senal("TRUE"))
    t.igual("E-10 el estado", CHECK.SIN_PROVEEDOR, salida["state"])
    t.igual("E-10 y el motivo", CHECK.SIN_PROVEEDOR, salida["reason"])
    t.igual("E-10 no aprueba", False, CHECK.aprueba(salida))
    t.verdadero("E-10 y no publica un proveedor", "cadastralProvider" not in salida)

    t.igual("E-10 hay cinco fuentes defendibles", 5, len(CHECK.FUENTES_DE_PROVEEDOR))
    t.verdadero("E-10 la norma es una de ellas", "GCBA_NORMATIVE" in CHECK.FUENTES_DE_PROVEEDOR)
    # 📌 A diferencia de la regla vecina, aca GCBA_NORMATIVE se puede usar de verdad: la norma
    # nombra el servicio del catalogo. El hueco vivo de D5 es el contrato.
    citada = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-10 una identidad citada de la norma alcanza", CHECK.PASA, citada["state"])
    t.igual("E-10 y se publica normalizada", "opcion-catastral-declarada",
            citada["cadastralProvider"]["id"])


def test_e11_sin_contrato_no_se_inventa(t):
    """E-11 (D5-14) — sin contrato declarado, INTEGRATION_CONTRACT_MISSING."""
    salida = CHECK.evaluar(_caso(integrationContract={}), _senal("TRUE"))
    t.igual("E-11 el estado", CHECK.SIN_CONTRATO, salida["state"])
    t.igual("E-11 y el motivo", CHECK.SIN_CONTRATO, salida["reason"])
    t.igual("E-11 no aprueba", False, CHECK.aprueba(salida))
    t.verdadero("E-11 y no publica un contrato", "integrationContract" not in salida)
    # El proveedor si, porque se valido antes: son dos huecos distintos y se ve cual falta.
    t.verdadero("E-11 el proveedor ya estaba resuelto", "cadastralProvider" in salida)


def test_e12_un_blanco_no_es_un_dato_declarado(t):
    """E-12 — y se normalizan LOS DOS lados de cada comparacion.

    🔴 `if not str(x or "")` deja pasar `" "`, que es truthy. En la regla vecina, un caso con toda
    la identidad en blancos llegaba a PASS. Y el arreglo que normalizo un solo lado produjo dos
    defectos nuevos, uno de ellos una regresion.
    """
    BLANCOS = (" ", "  ", "\t", "\n", " \t ")

    # 1. La identidad del proveedor: id, fuente y referencia, los tres.
    for blanco in BLANCOS:
        for campo in ("id", "reference"):
            proveedor = dict(PROVEEDOR)
            proveedor[campo] = blanco
            salida = CHECK.evaluar(_caso(cadastralProvider=proveedor), _senal("TRUE"))
            t.igual("E-12 un proveedor con %s en %s no identifica" % (repr(blanco), campo),
                    CHECK.SIN_PROVEEDOR, salida["state"])
    sin_fuente = dict(PROVEEDOR, source="PROJECT_DOCUMENTATION")
    t.igual("E-12 una fuente que no esta en la lista no identifica", CHECK.SIN_PROVEEDOR,
            CHECK.evaluar(_caso(cadastralProvider=sin_fuente), _senal("TRUE"))["state"])

    # 2. El contrato, igual.
    for blanco in BLANCOS:
        for campo in ("id", "reference"):
            contrato = dict(CONTRATO)
            contrato[campo] = blanco
            t.igual("E-12 un contrato con %s en %s no identifica" % (repr(blanco), campo),
                    CHECK.SIN_CONTRATO,
                    CHECK.evaluar(_caso(integrationContract=contrato), _senal("TRUE"))["state"])

    # 3. El id de un flujo del inventario.
    for blanco in BLANCOS:
        t.igual("E-12 un flujo con el id en %s no esta identificado" % repr(blanco),
                CHECK.SIN_COBERTURA,
                CHECK.evaluar(_caso(caminos=_caminos(flujos=[{"flowId": blanco}])),
                              _senal("TRUE"))["state"])

    # 4. 🔴 Y los DOS lados: con padding en el proveedor, en el flujo y en la cadena, un caso
    #    correcto sigue siendo correcto. Normalizar un lado solo hacia salir FAIL a un caso bueno.
    padeado = CHECK.evaluar(
        _caso(cadastralProvider=dict(PROVEEDOR, id="  opcion-catastral-declarada  "),
              caminos=_caminos(flujos=[{"flowId": " f-busqueda "}]),
              resultados=[_res(flujo="f-busqueda ", proveedor=" opcion-catastral-declarada",
                               cadena=_cadena(crudo=" v-crudo ", normalizado="v-normalizado "),
                               refs=("e-1",))],
              evidencia=[_ev(proveedor="opcion-catastral-declarada ")]),
        _senal("TRUE"))
    t.igual("E-12 con blancos en todos los lados, un caso correcto pasa", CHECK.PASA,
            padeado["state"])
    t.igual("E-12 y publica el id normalizado", "opcion-catastral-declarada",
            padeado["cadastralProvider"]["id"])
    t.igual("E-12 y el flujo normalizado", ["f-busqueda"], padeado["governedFlows"])

    # 5. Y un bypass con el id padeado sigue siendo un bypass: no se cae por el agujero del medio.
    bypass = CHECK.evaluar(
        _caso(caminos=_caminos(flujos=[{"flowId": " f-busqueda "}]),
              resultados=[_res(flujo="f-busqueda", proveedor="otro-normalizador")]),
        _senal("TRUE"))
    t.igual("E-12 un bypass con el id padeado sigue fallando", CHECK.FALLA, bypass["state"])
    t.igual("E-12 por el motivo correcto", CHECK.NORMALIZADOR_ALTERNO, bypass["reason"])

    # 6. 🔴 **CADA** comparacion del modulo, no las que la spec enumero. El refutador encontro
    #    doce campos que se comparaban en crudo: padear un caso CORRECTO lo sacaba de PASS, y dos
    #    de ellos informaban un motivo que no era cierto —un `buildId` con un blanco decia "es de
    #    otro build", un `mode` con un blanco decia que la corrida era mockeada cuando declaraba
    #    REAL—. Ese es el lado de la leccion de la regla vecina que importa: la version cruda
    #    avisaba, y normalizar a medias convierte un motivo verdadero en uno falso.
    def _con(**cambios):
        """Un caso correcto con un campo padeado, armado desde las piezas."""
        base = dict(cambios)
        return CHECK.evaluar(_caso(**base), _senal("TRUE"))

    PADEADOS = (
        ("cadastralProvider.source",
         {"cadastralProvider": dict(PROVEEDOR, source=" GCBA_NORMATIVE ")}),
        ("integrationContract.source",
         {"integrationContract": dict(CONTRATO, source=" ASI_INTEGRATION_CONTRACT ")}),
        ("addressFlows.source", {"caminos": _caminos(fuente=" ROUTE_INVENTORY ")}),
        ("scope.id", {"scope": dict(ALCANCE, id="  PROY-1  ")}),
        ("scope.kind", {"scope": dict(ALCANCE, kind=" PROJECT ")}),
        ("evidence.buildId", {"evidencia": [_ev(buildId=" " + BUILD["id"] + " ")]}),
        ("evidence.runtime", {"evidencia": [_ev(runtime=" " + BUILD["runtime"] + " ")]}),
        ("evidence.mode", {"evidencia": [_ev(modo=" REAL ")]}),
        ("evidence.sourceType", {"evidencia": [_ev(tipo=" NORMALIZED_ADDRESS_RUN ")]}),
        ("evidence.evidenceId y la referencia",
         {"evidencia": [_ev(eid=" e-1 ")], "resultados": [_res(refs=("e-1 ",))]}),
        ("results.execution", {"resultados": [_res(ejecucion=" EXECUTED ")]}),
        ("results.consumedFrom", {"resultados": [_res(desde=" NORMALIZED_RESULT ")]}),
    )
    for nombre, cambios in PADEADOS:
        salida = _con(**cambios)
        t.igual("E-12 un caso correcto con %s padeado sigue pasando" % nombre, CHECK.PASA,
                salida["state"])
        t.vacio("E-12 y sin avisos por %s" % nombre, salida["issues"])

    # La fuente de una ausencia y la de un inactivo, que van adentro del inventario.
    con_blancos = _caminos(flujos=[{"flowId": "f-busqueda"},
                                   {"flowId": "f-viejo", "active": False,
                                    "source": " PROJECT_ARCHITECTURE "}])
    for camino in con_blancos["paths"]:
        if camino.get("absent"):
            camino["source"] = " PROJECT_ARCHITECTURE "
    salida = CHECK.evaluar(_caso(caminos=con_blancos), _senal("TRUE"))
    t.igual("E-12 las fuentes del inventario padeadas siguen pasando", CHECK.PASA,
            salida["state"])
    t.igual("E-12 el inactivo sigue siendo inactivo", ["f-viejo"],
            [f["flowId"] for f in salida["inactiveFlows"]])
    t.vacio("E-12 y sin el aviso de inactivo sin fuente", salida["issues"])

    # La fuente de la completitud, en el camino de la derivacion.
    derivada = CHECK.evaluar(
        _caso(scopeCompleteness={"complete": True, "source": " WORKUNIT_SCOPE_DEFINITION ",
                                 "reference": "alcance de la unidad"}),
        _senal("UNRESOLVED"), _senal("FALSE", sid=SENAL_DE_FRONTEND))
    t.igual("E-12 la fuente de la completitud padeada deriva igual", CHECK.NO_APLICA,
            derivada["state"])

    # Y la relacion de alcance, en el camino cruzado.
    cruzado = CHECK.evaluar(
        _caso(scope={"id": "WU-7", "kind": "WORKUNIT", "reference": "unidad"},
              scopeRelation={"relation": " SIGNAL_SCOPE_CONTAINS_EVALUATION ",
                             "reference": "acta"}),
        _senal("TRUE"))
    t.igual("E-12 la relacion de alcance padeada se acepta igual", CHECK.PASA, cruzado["state"])
    t.igual("E-12 y se publica normalizada", "SIGNAL_SCOPE_CONTAINS_EVALUATION",
            cruzado["scopeRelation"]["relation"])


# -- E-13 — el barrido del contrato --------------------------------------------

# 🔴 Los nombres del vocabulario catastral y las formas del contrato viven ACA, no en los
# artefactos. Es la misma resolucion que tomo la regla vecina con los nombres de proveedores: un
# contraejemplo escrito en la policy hace que el invariante no pueda distinguir una cita de una
# invencion.
#
# 🔴 TODOS los patrones llevan `(?i)`. En la regla vecina, cuatro no lo llevaban y una constante
# en mayuscula escapaba entera: era una dimension completa del barrido, no una forma suelta.
PROHIBIDOS = (
    # localizadores de red
    r"(?i)\b(?:https?|wss?|ftp)://",
    r"(?i)\b[a-z0-9][a-z0-9.-]*\.(?:gob\.ar|com\.ar|org\.ar|gov\.ar|com|net|org|io|dev|app"
    r"|ar|gov|local|interno|internal|svc|cloud)\b",
    r"(?i)\b[a-z][a-z0-9-]{2,}:\d{2,5}\b",
    r"(?i)\b\d{1,3}(?:\.\d{1,3}){3}\b",
    # credenciales
    r"(?i)\bbearer\s+[a-z0-9._-]{6,}",
    r"(?i)\btoken\b\s*[:=]\s*[\"']?[a-z0-9._-]{6,}",
    r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\b",
    # paquetes
    r"(?i)\b(?:npm|pnpm|yarn|pip|nuget|composer)\s+(?:i|install|add|require)\b",
    r"(?i)@[a-z0-9-]{2,}/[a-z0-9-]{2,}",
    r"(?i)\b(?:from|import)\s+[\"'][a-z0-9@./-]+[\"']",
    r"(?i)\brequire\(\s*[\"']",
    # sistemas de coordenadas
    r"(?i)\b(?:epsg|srid)\b",
    r"(?i)\bcrs\b\s*[:=]",
    r"(?i)\b(?:4326|3857|22185|22195|900913)\b",
    # campos de contrato
    r"(?i)\b(?:request|response|body|payload|params|query)\s*\.\s*[a-z_]",
    r"(?i)[\"'](?:altura|calle|puerta|piso|depto|dpto|localidad|barrio)[\"']\s*[:=]",
    r"(?i)\b(?:altura|calle|puerta|piso|depto|dpto)\b\s*[:=]\s*[\"']?[a-z0-9]",
    # tiempos y reintentos
    r"(?i)\b(?:timeout|retry|retries|backoff|ttl)\b\s*[:=]?\s*\d",
    r"(?i)\b\d+\s*(?:ms|milisegundos|segundos)\b",
    # mecanismo declarado
    # 🔴 `["']?` ANTES del separador: una clave JSON lleva la comilla pegada al nombre, y
    # `"sdk": "catastro-js"` escapaba al patron que esperaba la palabra pegada a los dos puntos.
    # Y el valor puede empezar con `/`, que es la forma normal de escribir una ruta.
    r"(?i)\b(?:endpoint|base\s*-?url|baseurl|sdk|client[_-]?id|tenant[_-]?id|layer[_-]?id)"
    r"[\"']?\s*[:=]\s*[\"']?[a-z0-9/]",
    # 🔴 Los doce de abajo los trajo el refutador: no eran fugas presentes, eran huecos de la
    # reja. Ninguno disparaba y los doce son formas crudas de contrato. Una reja con huecos
    # conocidos y sin tapar es una reja que el dia que alguien escriba el contrato no lo agarra.
    # 📌 El patron de "<numero en palabras> segundos" alcanza y NO adivina: la version
    # anterior tenia ademas `timeout|esperar?|reintentos?` seguido de un numero en palabras a
    # menos de 24 caracteres, y eso dispara con prosa castellana normal -"esperar un resultado
    # normalizado", "esperar dos cosas del mismo control"-. Un barrido que se pone en rojo con
    # texto correcto es un barrido que alguien apaga.
    r"(?i)\b(?:un|dos|tres|cuatro|cinco|diez|veinte|treinta|sesenta)\s+"
    r"(?:mili)?segundos?\b",
    r"(?i)\b\d+\s*(?:ms|segs?|s)\b(?![a-z0-9])",
    r"(?i)\b(?:GET|POST|PUT|PATCH|HEAD|OPTIONS)\s+/[a-z0-9{]",
    # 📌 El VALOR tiene que parecer un localizador -un punto, una barra o un numero-, no
    # cualquier palabra: `url: la que declare el proyecto` no es un endpoint.
    r"(?i)[\"']?\b(?:url|uri|host|hostname|port|puerto)[\"']?\s*[:=]\s*[\"']?"
    r"(?:[a-z0-9-]+\.[a-z0-9-]|/|\d)",
    r"(?i)\bbasic\s+[a-z0-9+/=]{8,}",
    r"\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}",
    # 📌 `usuario` y `contrasena` se sacaron: son palabras castellanas que la prosa de `docs/`
    # usa todo el tiempo —"usuario: quien lee el reporte"— y el patron disparaba con ellas. Un
    # campo de contrato inventado se escribe con el nombre INGLES, que es lo que queda. Y el
    # valor tiene que ser un token sin espacios, no una frase.
    r"(?i)\b(?:password|passwd|username)\b[\"']?\s*[:=]\s*[\"']?[^\s\"']{4,}",
    r"(?i)\b(?:wgs\s*-?84|posgar|gauss\s*-?kr[uü]g+er|inchauspe|utm\s*(?:zona|zone)?\s*\d+)",
    # 📌 `9001` se saco: es ISO 9001 en cualquier documento de normativa. Los otros codigos
    # de proyeccion no tienen ese doble uso.
    r"(?i)\b(?:5347|5348|4221|97803)\b",
    r"(?i)\b(?:dotnet|cargo|gem|mvn|gradle|brew)\s+(?:add|install|get|require|build)\b",
    r"(?i)\b[a-z][a-z0-9.-]{2,}@\d+\.\d+",
    # La unica SENSIBLE a mayusculas de todo el barrido, y a proposito: en prosa castellana
    # nadie escribe ALTURA ni MANZANA en mayuscula, y en un contrato es la forma normal de
    # nombrar un campo. Bajarla a `(?i)` la volveria inservible: "altura" suelta aparece en
    # cualquier texto que hable de alturas.
    r"\b(?:ALTURA|CALLE|PUERTA|PISO|DEPTO|NOMENCLATURA|MANZANA|PARCELA|SMP)\b",
)

# Distintivos del vocabulario catastral: se buscan SIN separadores, asi `cod-calle`, `cod_calle`
# y `codCalle` son lo mismo.
PEGADOS = ("codigocalle", "codcalle", "idcalle", "calleid", "nomenclatura", "circunscripcion",
           "seccioncatastral", "manzanaparcela", "codigopostal")

# Cortos, con borde de palabra: `smp` se forma adentro de cualquier cosa si se quitan los
# espacios, y `parcela` esta adentro de `parcelamiento`.
SUELTOS = ("smp", "manzana", "parcela")


def _secciones_de_d5_del_doc():
    """Las dos secciones que D5 agrego a `docs/normativa-7.1.md`.

    Se barren esas y no el archivo entero: el documento cubre las 24 reglas, y el dia que otra
    regla cite el endpoint de su servicio el barrido de D5 no tiene por que ponerse en rojo. Que
    los dos titulos existan se afirma aparte, asi que renombrarlos no achica el sujeto en silencio.
    """
    texto = (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8")
    titulos = ("## La cadena que D5 verifica, y por qué no es la llamada",
               "## El alcance de una señal, desde D5")
    trozos = []
    for titulo in titulos:
        if titulo not in texto:
            continue
        trozos.append(texto.split(titulo, 1)[1].split("\n## ", 1)[0])
    return titulos, trozos


def _artefactos_de_d5():
    """Los seis textos de D5, como los declara la tabla `Qué se construye` de la spec."""
    matriz_entera = (RAIZ / "harnesses" / "desarrollo" / "reglas"
                     / "es0901-7.1-normative-matrix.json").read_text(encoding="utf-8")
    titulos, trozos = _secciones_de_d5_del_doc()
    return {
        "la policy": (CONTROLES / "policies" / (POLICY + ".md")).read_text(encoding="utf-8"),
        "el check": (CONTROLES / "checks" / (CHEQUEO + ".py")).read_text(encoding="utf-8"),
        "el registro": repr(c_controles.de_la_regla("D5")),
        "la fila de la matriz": repr(c_matriz.regla("D5")),
        "la doc": "\n".join(trozos),
        "la matriz entera": matriz_entera,
    }


def _fugas_en(texto):
    sin_separadores = re.sub(r"[\s_\-]+", "", texto).lower()
    hallados = [p for p in PROHIBIDOS if re.search(p, texto)]
    hallados += [v for v in PEGADOS if v in sin_separadores]
    hallados += [v for v in SUELTOS
                 if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(v), texto.lower())]
    return sorted(set(hallados))


def test_e13_ningun_artefacto_lleva_el_contrato(t):
    """E-13 (§6) — el invariante sobre los SEIS textos, y las dos mitades que lo sostienen."""
    titulos, trozos = _secciones_de_d5_del_doc()
    t.igual("E-13 las dos secciones de D5 estan en la doc", len(titulos), len(trozos))
    t.verdadero("E-13 y tienen contenido", all(len(x) > 400 for x in trozos))

    artefactos = _artefactos_de_d5()
    t.igual("E-13 son seis textos los que se barren", 6, len(artefactos))
    for nombre, texto in sorted(artefactos.items()):
        t.igual("E-13 %s no lleva el contrato" % nombre, [], _fugas_en(texto))

    # Y los resultados que el check produce, que son lo que viaja a un plan.
    for estado, (caso, senal) in sorted(_los_nueve_caminos().items()):
        t.igual("E-13 el resultado de %s no lo lleva" % estado, [],
                _fugas_en(repr(CHECK.evaluar(caso, senal))))

    # 🔴 La segunda mitad. Las formas son CRUDAS: ninguna se escribio para que el patron la
    # agarre, y las mayusculas estan a proposito porque en codigo es la forma normal.
    FUGAS = (
        "el servicio esta en https://catastro.example.gob.ar/normalizar",
        "HTTPS://CATASTRO.EXAMPLE.GOB.AR/NORMALIZAR",
        "se configura catastro.example.com como host",
        "el host es catastro-api.buenosaires.gob.ar",
        "apuntar a servicio:8443 desde el frontend",
        "el ambiente de test es 10.20.30.40",
        "Authorization: Bearer eyJhbGciOiJIUzI1",
        "AUTHORIZATION: BEARER abc123def456",
        'token: "s3cr3t0largo"',
        "se manda el api_key en la cabecera",
        "API_KEY va en el header",
        "el access_token dura una hora",
        "guardar el client_secret en el vault",
        "npm install catastro-client",
        "PNPM ADD normalizador-gcba",
        "pip install geocoder-ar",
        "se importa @gcba/catastro-sdk",
        'import "catastro-client"',
        'from "@gcba/normalizacion"',
        'require("catastro")',
        "las coordenadas vienen en EPSG:4326",
        "el srid del catastro es otro",
        "SRID 22185 para la ciudad",
        "crs = 3857 para los tiles",
        "el response.calle trae el nombre normalizado",
        "leer request.altura antes de mandar",
        'la respuesta trae {"calle": "x", "altura": 1}',
        '{"ALTURA": 123}',
        "altura = 1234 en el payload",
        "calle: Av. Corrientes",
        "timeout: 3000",
        "TIMEOUT = 5000",
        "retry 3 veces",
        "esperar 250 ms entre reintentos",
        "el backoff: 2 segundos",
        "endpoint: /v1/normalizar",
        "ENDPOINT = /normalizar",
        "base-url: interno",
        "sdk = catastro-js",
        '"sdk": "catastro-js"',
        "client_id: app-tramites",
        "el smp identifica la parcela",
        "SMP se arma con seccion, manzana y parcela",
        "la nomenclatura parcelaria del inmueble",
        "el codigo_calle que devuelve el servicio",
        "COD-CALLE viene en la respuesta",
        "el idCalle se usa como clave",
        "la circunscripcion catastral",
        "seccion catastral 14",
        "la manzana y la parcela del lote",
        "el codigo postal normalizado",
        # Las doce formas que el refutador probo y el barrido no agarraba.
        "el timeout es de tres segundos",
        "esperar cinco segundos entre reintentos",
        "timeout de 2s",
        "espera de 250 ms",
        "POST /direcciones/normalizar",
        "GET /catastro/{id}",
        '"url": "/normalizar"',
        "host: catastro.interno",
        "puerto = 5432",
        "Authorization: Basic dXNlcjpwYXNzd29yZA==",
        "el token es eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0",
        'password: "muylargo123"',
        "username = svc_catastro",
        "las coordenadas vienen en WGS84",
        "proyeccion Gauss-Krugger faja 6",
        "POSGAR 2007 para la ciudad",
        "UTM zona 21",
        "el codigo 5347 de la ciudad",
        "dotnet add package Catastro.Client",
        "cargo add catastro",
        "gem install catastro",
        "catastro-client@2.1.0",
        "el campo ALTURA del formulario",
        "la columna CALLE de la respuesta",
        "el identificador SMP",
        "geo.buenosaires.ar",
        "servicios.buenosaires.gov",
        "catastro.interno/normalizar",
    )
    for fuga in FUGAS:
        t.verdadero("E-13 la fuga se detecta: %s" % fuga[:42], bool(_fugas_en(fuga)))

    # 🔴 La tercera mitad, y aca importa mas que en la regla vecina: LA CITA ESTA PERMITIDA. Un
    # barrido de D5 que se ponga en rojo con la transcripcion del estandar es un barrido que
    # alguien apaga el primer dia.
    LIMPIOS = (
        "Toda busqueda o carga de direcciones en un frontend tiene que validarse y normalizarse "
        "con la opcion catastral del GCABA.",
        "Las aplicaciones deben contar con direcciones de calles normalizadas y validadas a "
        "traves del servicio de API GEO disponible en el catalogo.",
        "la opcion catastral del GCBA, nombrada en la pagina 19",
        "API GEO esta en el catalogo y la norma lo nombra",
        "no hay un endpoint, un campo de request ni una autenticacion adentro de este archivo",
        "CADASTRAL_PROVIDER_UNRESOLVED / INTEGRATION_CONTRACT_MISSING",
        "controles/checks/address-normalization-integration.py y su policy",
        "docs/normativa-7.1.md, es0901-7.1.json y la matriz",
        "el valor crudo y el normalizado son el mismo token, asi que no discrimina",
        "RAW_INPUT PROVIDER_REQUEST PROVIDER_RESPONSE NORMALIZED_RESULT CONSUMED_VALUE",
        "ES0901 6.3, pag. 19, y la fila citable de la pagina 13",
        "27 skills instaladas y 31 controles declarados",
        "un timeout ni una URL de ambiente se atribuyen a esta regla",
        "la puerta de salida que la regla vecina tuvo que sacar",
        "direcciones de calles normalizadas, no una calle parseada",
        "SEARCH MANUAL_ENTRY SELECTION EDIT_UPDATE ALTERNATE_INPUT",
        # Y los que cuidan los patrones nuevos, que son los mas propensos a un falso positivo.
        "las cinco etapas de la cadena y los cinco tipos de camino",
        "el usuario escribe una direccion en un formulario del frontend",
        "ES0901 6.3, seccion 7.1, regla D5, pagina 13",
        "el alcance puede ser PROJECT, WORKUNIT o TASK",
        "CHAIN_DECLARATION_INCOHERENT y NORMALIZATION_INDISTINGUISHABLE",
        "ADDRESS_FLOW_COVERAGE_UNRESOLVED / NO_ACTIVE_FLOW_IN_SCOPE",
        "la validacion se hace en el frontend y esta regla no habla de otra capa",
        "una corrida REAL y una MOCKED se distinguen en el resultado",
        "hay 31 controles declarados y 24 filas en la matriz",
        "un token opaco: un hash, una etiqueta, lo que la corrida produzca",
        # Las tres formas de prosa legitima que la refutacion probo y que los patrones nuevos
        # disparaban. Van clavadas: son el tipo de texto que este repositorio escribe todo el
        # tiempo, y un barrido que las agarra es uno que alguien apaga.
        "hay que esperar un resultado normalizado antes de consumirlo",
        "se exigen dos cosas del mismo control: el token y la etapa",
        "url: la que declare el proyecto, con su fuente citada",
        "usuario: quien lee el reporte, no quien lo produce",
        "la norma ISO 9001 no tiene nada que ver con esta regla",
        "el proveedor responde en un tiempo que esta regla no mide",
    )
    for limpio in LIMPIOS:
        t.igual("E-13 no dispara con: %s" % limpio[:38], [], _fugas_en(limpio))


# -- E-14 a E-17 — lo que no prueba nada ---------------------------------------

def test_e14_el_autocompletado_solo_no_pasa(t):
    """E-14 (D5-10) — un autocompletado que existe no es una direccion normalizada."""
    salida = CHECK.evaluar(_con_evidencia_sola("AUTOCOMPLETE_COMPONENT_PRESENT"), _senal("TRUE"))
    t.igual("E-14 no pasa", CHECK.PARCIAL, salida["state"])
    t.igual("E-14 y dice que falta la corrida", CHECK.SIN_EVIDENCIA_DE_CORRIDA, salida["reason"])
    t.igual("E-14 no aprueba", False, CHECK.aprueba(salida))
    t.verdadero("E-14 la clase es inerte",
                "AUTOCOMPLETE_COMPONENT_PRESENT" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e15_la_llamada_a_una_api_de_direcciones_sola_no_pasa(t):
    """E-15 (D5-11) — que se llame a una API de direcciones no dice cual, ni que se use."""
    salida = CHECK.evaluar(_con_evidencia_sola("ADDRESS_API_CALL"), _senal("TRUE"))
    t.igual("E-15 no pasa", CHECK.PARCIAL, salida["state"])
    t.igual("E-15 y dice que falta la corrida", CHECK.SIN_EVIDENCIA_DE_CORRIDA, salida["reason"])
    t.verdadero("E-15 la clase es inerte", "ADDRESS_API_CALL" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)

    # 🔴 Y la que si prueba es UNA sola: la corrida.
    t.igual("E-15 hay una sola clase que prueba", 1, len(CHECK.EVIDENCIA_DE_CORRIDA))
    t.igual("E-15 con la corrida real pasa", CHECK.PASA,
            CHECK.evaluar(_caso(), _senal("TRUE"))["state"])


def test_e16_un_regex_solo_no_pasa(t):
    """E-16 (D5-12) — un regex valida una forma, no valida una direccion."""
    for tipo in ("REGEX_VALIDATION", "FRONTEND_FIELD_VALIDATION"):
        salida = CHECK.evaluar(_con_evidencia_sola(tipo), _senal("TRUE"))
        t.igual("E-16 %s no pasa" % tipo, CHECK.PARCIAL, salida["state"])
        t.igual("E-16 %s no aprueba" % tipo, False, CHECK.aprueba(salida))
        t.verdadero("E-16 %s es inerte" % tipo, tipo in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e17_lo_que_hay_no_es_lo_que_se_consume(t):
    """E-17 — la particion entera: ocho clases inertes y tres que acompanan."""
    t.igual("E-17 ocho clases no prueban nada", 8, len(CHECK.EVIDENCIA_QUE_NO_PRUEBA))
    t.igual("E-17 tres acompanan", 3, len(CHECK.EVIDENCIA_DE_APOYO))

    # Ninguna de las inertes alcanza, ni sola ni todas juntas.
    for tipo in CHECK.EVIDENCIA_QUE_NO_PRUEBA:
        salida = CHECK.evaluar(_con_evidencia_sola(tipo), _senal("TRUE"))
        t.verdadero("E-17 %s sola no aprueba" % tipo, not CHECK.aprueba(salida))

    todas = [_ev("e-%d" % i, tipo=tipo)
             for i, tipo in enumerate(CHECK.EVIDENCIA_QUE_NO_PRUEBA + CHECK.EVIDENCIA_DE_APOYO)]
    juntas = CHECK.evaluar(
        _caso(resultados=[_res(refs=tuple(e["evidenceId"] for e in todas))], evidencia=todas),
        _senal("TRUE"))
    t.igual("E-17 ni todas juntas", CHECK.PARCIAL, juntas["state"])
    t.igual("E-17 y el motivo es la corrida que falta", CHECK.SIN_EVIDENCIA_DE_CORRIDA,
            juntas["reason"])

    # 🔴 Las clases no se solapan: una clase en dos listas seria una que prueba y no prueba.
    listas = (CHECK.EVIDENCIA_DE_CORRIDA, CHECK.EVIDENCIA_DE_APOYO, CHECK.EVIDENCIA_QUE_NO_PRUEBA)
    todas_las_clases = [c for lista in listas for c in lista]
    t.igual("E-17 ninguna clase esta en dos listas", len(todas_las_clases),
            len(set(todas_las_clases)))


# -- E-18 a E-22 — la cadena de cinco valores ----------------------------------

def test_e18_la_cadena_completa_con_el_normalizado_consumido_pasa(t):
    """E-18 (D5-15) — lo que la regla pide, entero."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-18 pasa", CHECK.PASA, salida["state"])
    t.igual("E-18 aprueba", True, CHECK.aprueba(salida))
    t.igual("E-18 con un solo flujo evaluado", 1, len(salida["flows"]))
    flujo = salida["flows"][0]
    t.igual("E-18 el flujo pasa", CHECK.PASA, flujo["state"])
    t.igual("E-18 y publica su cadena entera", 5, len(flujo["chain"]))
    t.igual("E-18 con la etapa que consume", CHECK.NORMALIZADO, flujo["consumedFrom"])
    t.vacio("E-18 sin avisos", salida["issues"])
    t.igual("E-18 las cinco etapas son las del pedido", 5, len(CHECK.ETAPAS))


def test_e19_la_llamada_ocurre_y_se_guarda_el_crudo(t):
    """E-19 (D5-16) — el defecto que esta regla existe para atrapar."""
    salida = CHECK.evaluar(_caso(resultados=[_res(cadena=_cadena(consumido="v-crudo"))]),
                           _senal("TRUE"))
    t.igual("E-19 falla", CHECK.FALLA, salida["state"])
    t.igual("E-19 con el motivo exacto", CHECK.CRUDO_CONSUMIDO, salida["reason"])
    t.igual("E-19 no aprueba", False, CHECK.aprueba(salida))

    # Y la corrida entera esta ahi: la llamada ocurrio, la evidencia es real, el proveedor es el
    # declarado. Nada de eso lo salva.
    flujo = salida["flows"][0]
    t.igual("E-19 el proveedor era el correcto", "opcion-catastral-declarada",
            flujo["declaredProvider"])
    t.igual("E-19 y la respuesta existia", "v-normalizado", flujo["chain"][CHECK.RESPUESTA])
    t.igual("E-19 pero el valor consumido es el crudo", "v-crudo", flujo["chain"][CHECK.CONSUMIDO])

    # Y cuando el flujo lo declara **y sus tokens no lo desmienten**, tambien: declararlo es lo
    # mismo que demostrarlo.
    # 🔴 La version anterior usaba la cadena feliz con `consumedFrom: RAW_INPUT` y afirmaba FAIL.
    # El refutador mostro que eso contradice la tabla de la spec: ahi los tokens dicen que se
    # consumio el normalizado y la etapa dice lo contrario, y cuando discrepan MANDA EL TOKEN.
    # Ese caso vive ahora en E-21 como CHAIN_DECLARATION_INCOHERENT.
    for nombre, cadena in (
            ("con los tokens de acuerdo", _cadena(consumido="v-crudo")),
            ("con tokens que no discriminan", _cadena(crudo="v-igual", normalizado="v-igual"))):
        salida = CHECK.evaluar(_caso(resultados=[_res(desde=CHECK.CRUDO, cadena=cadena)]),
                               _senal("TRUE"))
        t.igual("E-19 declararlo %s es lo mismo que demostrarlo" % nombre, CHECK.FALLA,
                salida["state"])
        t.igual("E-19 %s con el mismo motivo" % nombre, CHECK.CRUDO_CONSUMIDO, salida["reason"])

    # 🔴 Y el bypass PROBADO se informa como bypass aunque a la cadena le falte otra etapa. Con
    # el orden anterior de las guardas salia NORMALIZATION_CHAIN_INCOMPLETE: el estado de lo que
    # no se sabe, puesto sobre algo que si se sabe.
    a_medias = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(consumido="v-crudo", sin=(CHECK.PEDIDO,)))]),
        _senal("TRUE"))
    t.igual("E-19 el bypass probado no se disfraza de cadena incompleta", CHECK.FALLA,
            a_medias["state"])
    t.igual("E-19 con el motivo del valor crudo", CHECK.CRUDO_CONSUMIDO, a_medias["reason"])


def test_e20_un_valor_consumido_sin_rastro_no_pasa(t):
    """E-20 — si no es ni el crudo ni el normalizado, no se puede decir de donde salio."""
    salida = CHECK.evaluar(_caso(resultados=[_res(cadena=_cadena(consumido="v-tercero"))]),
                           _senal("TRUE"))
    t.igual("E-20 no pasa", CHECK.PARCIAL, salida["state"])
    t.igual("E-20 con el motivo", CHECK.CONSUMIDO_SIN_RASTRO, salida["reason"])
    t.igual("E-20 no aprueba", False, CHECK.aprueba(salida))
    # 🔴 Y no se convierte en FAIL: no se sabe que paso, y afirmar incumplimiento sin saberlo es
    # una afirmacion falsa con la tupla normativa adosada.
    t.verdadero("E-20 y no se informa como incumplimiento", salida["state"] != CHECK.FALLA)


def test_e21_se_exigen_el_token_y_la_etapa(t):
    """E-21 — pedir una sola de las dos deja pasar una corrida que dice la palabra correcta."""
    # 1. La etapa dice NORMALIZED_RESULT y el token es el crudo: manda el token.
    miente = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(consumido="v-crudo"), desde=CHECK.NORMALIZADO)]),
        _senal("TRUE"))
    t.igual("E-21 decir la palabra correcta no salva nada", CHECK.FALLA, miente["state"])
    t.igual("E-21 y el motivo es el valor crudo", CHECK.CRUDO_CONSUMIDO, miente["reason"])

    # 2. El token es el normalizado y la etapa no se declara: no llega a PASS.
    for etapa in ("", "   ", CHECK.RESPUESTA, CHECK.PEDIDO):
        salida = CHECK.evaluar(_caso(resultados=[_res(desde=etapa)]), _senal("TRUE"))
        t.igual("E-21 con la etapa %r no pasa" % etapa, CHECK.PARCIAL, salida["state"])
        t.igual("E-21 con la etapa %r lo dice" % etapa, CHECK.ETAPA_SIN_DECLARAR,
                salida["reason"])

    # 3. Y una cadena a medias no dice que valor usa la aplicacion.
    for falta in (CHECK.CRUDO, CHECK.PEDIDO):
        salida = CHECK.evaluar(_caso(resultados=[_res(cadena=_cadena(sin=(falta,)))]),
                               _senal("TRUE"))
        t.igual("E-21 sin %s la cadena esta incompleta" % falta, CHECK.PARCIAL, salida["state"])
        t.igual("E-21 sin %s lo dice" % falta, CHECK.CADENA_INCOMPLETA, salida["reason"])
    sin_consumido = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(sin=(CHECK.CONSUMIDO,)))]), _senal("TRUE"))
    t.igual("E-21 sin valor consumido tampoco pasa", CHECK.PARCIAL, sin_consumido["state"])

    # 4. 🔴 Cuando la etapa y el token se contradicen, MANDA EL TOKEN: el flujo declara que usa el
    #    crudo y sus tokens dicen que usa el normalizado. Eso no es un incumplimiento probado
    #    -afirmarlo seria una afirmacion falsa con la tupla normativa adosada, que es lo que dice
    #    E-20- y tampoco esta confirmado, asi que no pasa. La version anterior informaba FAIL
    #    por valor crudo consumido: ahi mandaba la etapa, al reves de lo que dice la spec.
    incoherente = CHECK.evaluar(_caso(resultados=[_res(desde=CHECK.CRUDO)]), _senal("TRUE"))
    t.igual("E-21 la contradiccion no pasa", CHECK.PARCIAL, incoherente["state"])
    t.igual("E-21 y no se informa como incumplimiento", CHECK.DECLARACION_INCOHERENTE,
            incoherente["reason"])
    t.igual("E-21 no aprueba", False, CHECK.aprueba(incoherente))

    # 5. 🔴 Y el estado que se informa tiene que ser cierto. Con la guarda vieja -un `or` entre
    #    "sin respuesta" y "sin resultado normalizado"- una cadena que SI llega al resultado
    #    normalizado y no declara la respuesta salia FAIL con un detalle que decia que no habia
    #    resultado normalizado. Se exigen LOS DOS, como dice la tabla de la doc.
    sin_respuesta = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(sin=(CHECK.RESPUESTA,)))]), _senal("TRUE"))
    t.igual("E-21 sin respuesta la cadena esta incompleta, no incumple", CHECK.PARCIAL,
            sin_respuesta["state"])
    t.igual("E-21 con el motivo de la cadena", CHECK.CADENA_INCOMPLETA, sin_respuesta["reason"])
    detalle = sin_respuesta["flows"][0]["detail"]
    t.verdadero("E-21 y el detalle no afirma algo falso",
                "resultado normalizado en la cadena" not in detalle)
    t.contiene("E-21 nombra la etapa que falta", CHECK.RESPUESTA, detalle)

    # Y sin ninguna de las dos, si: es el bypass de texto libre.
    sin_las_dos = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(sin=(CHECK.RESPUESTA, CHECK.NORMALIZADO)))]),
        _senal("TRUE"))
    t.igual("E-21 sin las dos etapas si es un bypass", CHECK.FALLA, sin_las_dos["state"])
    t.igual("E-21 con su motivo", CHECK.CRUDO_COMO_NORMALIZADO, sin_las_dos["reason"])


def test_e22_cuando_el_crudo_y_el_normalizado_son_el_mismo(t):
    """E-22 — el residuo, clavado en verde.

    🔴 Si el proveedor devolvio exactamente lo que la persona escribio, los tres tokens son
    iguales y *consumir el crudo* y *consumir el normalizado* son indistinguibles. Es un caso
    legitimo, asi que PASA, y el resultado lo dice. Bajarlo a PARCIAL pondria en rojo a todo
    proyecto que valide una direccion ya normalizada, y un check que se pone en rojo sin motivo es
    un check que alguien apaga. El dia que alguien quiera cerrarlo, este test obliga a hablarlo.
    """
    salida = CHECK.evaluar(
        _caso(resultados=[_res(cadena=_cadena(crudo="v-igual", normalizado="v-igual"))]),
        _senal("TRUE"))
    t.igual("E-22 el caso degenerado pasa", CHECK.PASA, salida["state"])
    t.igual("E-22 y aprueba", True, CHECK.aprueba(salida))
    t.verdadero("E-22 pero lo dice",
                any(CHECK.INDISTINGUIBLE in i for i in salida["issues"]))
    t.igual("E-22 el aviso viaja con el flujo", 1,
            len([i for i in salida["flows"][0]["issues"] if CHECK.INDISTINGUIBLE in i]))

    # Y cuando SI se distinguen, el aviso no aparece: un aviso que aparece siempre no avisa.
    distinto = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.verdadero("E-22 con tokens distintos no hay aviso",
                not any(CHECK.INDISTINGUIBLE in i for i in distinto["issues"]))


# -- E-23 a E-27 — los cinco caminos y el bypass -------------------------------

def test_e23_la_carga_manual_de_texto_libre_falla(t):
    """E-23 (D5-17) — un camino que trata texto crudo como si fuera una direccion normalizada."""
    manual = _caso(
        caminos=_caminos(flujos=[{"flowId": "f-busqueda"}],
                         ausentes={"MANUAL_ENTRY": [{"flowId": "f-carga-manual"}]}),
        resultados=[_res(),
                    _res(flujo="f-carga-manual", clase="MANUAL_ENTRY", proveedor="",
                         cadena={CHECK.CRUDO: "v-tipeado", CHECK.CONSUMIDO: "v-tipeado"},
                         desde="", refs=())])
    salida = CHECK.evaluar(manual, _senal("TRUE"))
    t.igual("E-23 falla", CHECK.FALLA, salida["state"])
    t.igual("E-23 con el motivo exacto", CHECK.CRUDO_COMO_NORMALIZADO, salida["reason"])

    # 🔴 Y el camino de busqueda seguia cumpliendo: un camino compliant no compensa el bypass.
    por_flujo = {f["flowId"]: f for f in salida["flows"]}
    t.igual("E-23 la busqueda pasaba", CHECK.PASA, por_flujo["f-busqueda"]["state"])
    t.igual("E-23 y la carga manual no", CHECK.FALLA, por_flujo["f-carga-manual"]["state"])
    t.igual("E-23 el tipo del camino queda en la salida", "MANUAL_ENTRY",
            por_flujo["f-carga-manual"]["kind"])


def test_e24_la_edicion_que_se_saltea_la_normalizacion_falla(t):
    """E-24 (D5-18) — el camino de edicion, y la llamada condicional que el flujo normal no hace."""
    edicion = _caso(
        caminos=_caminos(ausentes={"EDIT_UPDATE": [{"flowId": "f-edicion"}]}),
        resultados=[_res(),
                    _res(flujo="f-edicion", clase="EDIT_UPDATE",
                         cadena={CHECK.CRUDO: "v-editado", CHECK.PEDIDO: "v-editado",
                                 CHECK.CONSUMIDO: "v-editado"},
                         desde=CHECK.NORMALIZADO, refs=("e-1",))])
    salida = CHECK.evaluar(edicion, _senal("TRUE"))
    t.igual("E-24 la edicion sin normalizar falla", CHECK.FALLA, salida["state"])
    t.igual("E-24 con el motivo", CHECK.CRUDO_COMO_NORMALIZADO, salida["reason"])

    # La llamada condicional: hay request, no hay response, y el flujo igual consume un valor.
    condicional = _caso(resultados=[_res(cadena={CHECK.CRUDO: "v-x", CHECK.PEDIDO: "v-x",
                                                 CHECK.CONSUMIDO: "v-x"})])
    t.igual("E-24 una llamada que el flujo normal no hace falla", CHECK.FALLA,
            CHECK.evaluar(condicional, _senal("TRUE"))["state"])

    # Y un normalizador que no es el declarado, tambien.
    alterno = CHECK.evaluar(_caso(resultados=[_res(proveedor="otro-normalizador")]),
                            _senal("TRUE"))
    t.igual("E-24 un normalizador alterno falla", CHECK.FALLA, alterno["state"])
    t.igual("E-24 con su motivo", CHECK.NORMALIZADOR_ALTERNO, alterno["reason"])
    # 🔴 La corrida manda sobre lo declarado: el flujo dice el correcto y la corrida dice otro.
    por_la_corrida = CHECK.evaluar(_caso(evidencia=[_ev(proveedor="otro-normalizador")]),
                                   _senal("TRUE"))
    t.igual("E-24 la corrida manda sobre lo declarado", CHECK.FALLA, por_la_corrida["state"])
    t.igual("E-24 con el mismo motivo", CHECK.NORMALIZADOR_ALTERNO, por_la_corrida["reason"])
    # Y una corrida que no dice con que normalizo no prueba nada.
    muda = CHECK.evaluar(_caso(evidencia=[_ev(proveedor="  ")]), _senal("TRUE"))
    t.igual("E-24 una corrida muda no pasa", CHECK.PARCIAL, muda["state"])
    t.igual("E-24 y lo dice", CHECK.CORRIDA_SIN_PROVEEDOR, muda["reason"])


def test_e25_los_cinco_tipos_de_camino_se_declaran_todos(t):
    """E-25 (D5-19) — un tipo en silencio no es un tipo que no exista.

    🔴 Es la misma doctrina que sostiene la senal -la ausencia de una palabra no es evidencia de
    ausencia- aplicada a la cobertura, y es lo que impide disimular el bypass de carga manual no
    mencionandolo. Los CINCO tipos los fija el pedido, no este modulo.
    """
    t.igual("E-25 son cinco tipos", 5, len(CLASES))
    t.igual("E-25 y son los del pedido",
            ("SEARCH", "MANUAL_ENTRY", "SELECTION", "EDIT_UPDATE", "ALTERNATE_INPUT"), CLASES)

    # 1. Cada uno de los cinco, en silencio, deja la cobertura sin resolver.
    for clase in CLASES:
        salida = CHECK.evaluar(_caso(caminos=_caminos(sin=(clase,))), _senal("TRUE"))
        t.igual("E-25 sin declarar %s no se resuelve" % clase, CHECK.SIN_COBERTURA,
                salida["state"])
        t.contiene("E-25 y nombra el tipo que falta: %s" % clase, clase, salida["detail"])
        t.contiene("E-25 con el estado del silencio: %s" % clase, CHECK.CAMINO_EN_SILENCIO,
                   salida["detail"])

    # 2. Una ausencia sin fuente es una omision con formato de declaracion.
    sin_fuente = _caminos()
    for camino in sin_fuente["paths"]:
        if camino.get("absent"):
            camino.pop("source")
    t.igual("E-25 una ausencia sin fuente no alcanza", CHECK.SIN_COBERTURA,
            CHECK.evaluar(_caso(caminos=sin_fuente), _senal("TRUE"))["state"])

    mala_fuente = _caminos()
    for camino in mala_fuente["paths"]:
        if camino.get("absent"):
            camino["source"] = "AGENT_STATEMENT"
    t.igual("E-25 ni una fuente que no esta en la lista", CHECK.SIN_COBERTURA,
            CHECK.evaluar(_caso(caminos=mala_fuente), _senal("TRUE"))["state"])

    # 3. Un tipo declarado ni con flujos ni con ausencia: lo mismo.
    a_medias = {"source": "ROUTE_INVENTORY",
                "paths": [{"kind": c, "flows": [{"flowId": "f-1"}]} if c == "SEARCH"
                          else {"kind": c} for c in CLASES]}
    t.igual("E-25 un tipo vacio no declara nada", CHECK.SIN_COBERTURA,
            CHECK.evaluar(_caso(caminos=a_medias), _senal("TRUE"))["state"])

    # 4. Y un tipo inventado se rechaza: el inventario no define la taxonomia.
    inventado = _caminos()
    inventado["paths"].append({"kind": "VOICE_INPUT", "flows": [{"flowId": "f-voz"}]})
    t.igual("E-25 un tipo que no existe se rechaza", CHECK.SIN_COBERTURA,
            CHECK.evaluar(_caso(caminos=inventado), _senal("TRUE"))["state"])

    # 5. Con los cinco declarados -uno con flujos, cuatro ausentes con fuente- se evalua.
    t.igual("E-25 con los cinco declarados se evalua", CHECK.PASA,
            CHECK.evaluar(_caso(), _senal("TRUE"))["state"])
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-25 y el inventario se publica entero", 5, len(salida["addressFlows"]["paths"]))

    # 6. 🔴 Un tipo declarado DOS VECES no se sobrescribe. Con `por_clase[clase] = camino`, la
    #    primera entrada quedaba sin validar y `gobernados()` igual recorria las dos: un flujo
    #    sin id llegaba a ser gobernado con el id vacio, evadiendo la validacion de E-12
    #    simplemente duplicando el tipo.
    duplicado = _caminos()
    duplicado["paths"].insert(0, {"kind": "SEARCH",
                                  "flows": [{"sinid": 1},
                                            {"flowId": "f-oculto", "active": False}]})
    salida = CHECK.evaluar(_caso(caminos=duplicado), _senal("TRUE"))
    t.igual("E-25 un tipo duplicado se rechaza", CHECK.SIN_COBERTURA, salida["state"])
    t.contiene("E-25 y lo dice", "dos veces", salida["detail"])
    t.vacio("E-25 y ningun flujo sin id llega a gobernado", salida["governedFlows"])

    # 7. 🔴 `absent` se exige `True`, no truthy: un `"absent": "false"` escrito por quien queria
    #    decir que el camino NO esta ausente sacaba ese tipo entero de la verificacion.
    for valor in ("false", "no", "0", -1, {"a": 1}, [1], "True"):
        torcido = _caminos()
        for camino in torcido["paths"]:
            if camino.get("absent"):
                camino["absent"] = valor
        salida = CHECK.evaluar(_caso(caminos=torcido), _senal("TRUE"))
        t.igual("E-25 absent=%r no declara una ausencia" % (valor,), CHECK.SIN_COBERTURA,
                salida["state"])
        t.contiene("E-25 absent=%r cae en el silencio" % (valor,), CHECK.CAMINO_EN_SILENCIO,
                   salida["detail"])

    # 8. 🔴 Una entrada malformada sale por uno de los nueve estados, no por una excepcion. Un
    #    dato que rompe el modulo no es un dato que fallo cerrado.
    MALFORMADOS = (
        ("paths como diccionario", {"source": "ROUTE_INVENTORY", "paths": {"SEARCH": []}}),
        ("paths como texto", {"source": "ROUTE_INVENTORY", "paths": "SEARCH"}),
        ("un camino como texto", {"source": "ROUTE_INVENTORY", "paths": ["SEARCH"]}),
        ("flows como lista de textos",
         {"source": "ROUTE_INVENTORY",
          "paths": [{"kind": c, "flows": ["f-1"]} if c == "SEARCH"
                    else {"kind": c, "absent": True, "source": "PROJECT_ARCHITECTURE"}
                    for c in CLASES]}),
        ("flows como diccionario",
         {"source": "ROUTE_INVENTORY",
          "paths": [{"kind": c, "flows": {"f-1": {}}} if c == "SEARCH"
                    else {"kind": c, "absent": True, "source": "PROJECT_ARCHITECTURE"}
                    for c in CLASES]}),
        ("el inventario como texto", "ROUTE_INVENTORY"),
    )
    for nombre, caminos in MALFORMADOS:
        salida = CHECK.evaluar(_caso(caminos=caminos), _senal("TRUE"))
        t.verdadero("E-25 %s sale por un estado conocido" % nombre,
                    salida["state"] in CHECK.ESTADOS)
        t.igual("E-25 %s no aprueba" % nombre, False, CHECK.aprueba(salida))


def test_e26_la_cobertura_incompleta_no_pasa(t):
    """E-26 (D5-19) — sin inventario, sin fuente, con flujos sin id, o sin ejecutar."""
    for nombre, caminos in (("sin inventario", {}),
                            ("con paths vacio", {"source": "ROUTE_INVENTORY", "paths": []}),
                            ("sin fuente", _caminos(fuente=None)),
                            ("con una fuente que no esta en la lista",
                             _caminos(fuente="AGENT_STATEMENT"))):
        salida = CHECK.evaluar(_caso(caminos=caminos), _senal("TRUE"))
        t.igual("E-26 %s no resuelve la cobertura" % nombre, CHECK.SIN_COBERTURA,
                salida["state"])
        t.vacio("E-26 %s y no hay flujos gobernados" % nombre, salida["governedFlows"])

    t.igual("E-26 hay cinco fuentes de cobertura", 5, len(CHECK.FUENTES_DE_COBERTURA))

    # Un flujo enumerado y sin ningun resultado: PARCIAL, se cuenta, no se omite.
    sin_correr = CHECK.evaluar(
        _caso(caminos=_caminos(flujos=[{"flowId": "f-busqueda"}, {"flowId": "f-otra"}])),
        _senal("TRUE"))
    t.igual("E-26 un flujo sin resultado deja PARCIAL", CHECK.PARCIAL, sin_correr["state"])
    t.igual("E-26 con el motivo", CHECK.SIN_EJECUTAR, sin_correr["reason"])
    t.igual("E-26 y los dos flujos aparecen", 2, len(sin_correr["flows"]))
    t.igual("E-26 los dos estan gobernados", ["f-busqueda", "f-otra"],
            sin_correr["governedFlows"])

    # Y un flujo declarado como no ejecutado, tambien.
    no_ejecutado = CHECK.evaluar(_caso(resultados=[_res(ejecucion="NOT_EXECUTED")]),
                                 _senal("TRUE"))
    t.igual("E-26 un flujo no ejecutado deja PARCIAL", CHECK.PARCIAL, no_ejecutado["state"])
    t.igual("E-26 con su motivo", CHECK.SIN_EJECUTAR, no_ejecutado["reason"])


def test_e27_un_camino_que_cumple_no_tapa_otro(t):
    """E-27 — y declararlos todos inactivos no vacia el conjunto gobernado.

    🔴 Un flujo que el proyecto saca de la verificacion declarandolo inactivo es la puerta de
    salida que la regla vecina tuvo que sacar: alla una vista marcada como menor dibujando con
    otro mapa daba PASS y no aparecia en ningun campo de la salida. Aca la puerta tiene tres
    cerrojos, y los tres se prueban.
    """
    # 1. Un FAIL manda sobre cualquier cantidad de caminos que pasen.
    muchos = [{"flowId": "f-%d" % i} for i in range(6)] + [{"flowId": "f-bypass"}]
    resultados = [_res(flujo="f-%d" % i) for i in range(6)]
    resultados.append(_res(flujo="f-bypass", proveedor="otro-normalizador"))
    salida = CHECK.evaluar(_caso(caminos=_caminos(flujos=muchos), resultados=resultados),
                           _senal("TRUE"))
    t.igual("E-27 seis que pasan no tapan uno que no", CHECK.FALLA, salida["state"])
    t.igual("E-27 seis pasaron", 6, len([f for f in salida["flows"]
                                         if f["state"] == CHECK.PASA]))

    # 2. Un inactivo exige fuente: sin fuente se verifica como ACTIVO.
    sin_fuente = CHECK.evaluar(
        _caso(caminos=_caminos(flujos=[{"flowId": "f-busqueda"},
                                       {"flowId": "f-bypass", "active": False}]),
              resultados=[_res(), _res(flujo="f-bypass", proveedor="otro-normalizador")]),
        _senal("TRUE"))
    t.igual("E-27 un inactivo sin fuente se verifica", CHECK.FALLA, sin_fuente["state"])
    t.verdadero("E-27 y el aviso lo dice",
                any(CHECK.INACTIVO_SIN_FUENTE in i for i in sin_fuente["issues"]))
    t.verdadero("E-27 queda entre los gobernados", "f-bypass" in sin_fuente["governedFlows"])

    # 3. Un inactivo con fuente sale de la verificacion Y APARECE EN LA SALIDA.
    con_fuente = CHECK.evaluar(
        _caso(caminos=_caminos(flujos=[{"flowId": "f-busqueda"},
                                       {"flowId": "f-viejo", "active": False,
                                        "source": "PROJECT_ARCHITECTURE"}])),
        _senal("TRUE"))
    t.igual("E-27 un inactivo con fuente no bloquea", CHECK.PASA, con_fuente["state"])
    t.igual("E-27 pero aparece en la salida", ["f-viejo"],
            [f["flowId"] for f in con_fuente["inactiveFlows"]])
    t.igual("E-27 con su fuente", "PROJECT_ARCHITECTURE", con_fuente["inactiveFlows"][0]["source"])
    t.verdadero("E-27 y no cuenta como gobernado",
                "f-viejo" not in con_fuente["governedFlows"])

    # 4. 🔴 El tercer cerrojo: si no queda NINGUNO activo, no es PASS.
    todos_inactivos = CHECK.evaluar(
        _caso(caminos=_caminos(flujos=[{"flowId": "f-busqueda", "active": False,
                                        "source": "PROJECT_ARCHITECTURE"}]),
              resultados=[]),
        _senal("TRUE"))
    t.igual("E-27 declararlos todos inactivos no da PASS", CHECK.SIN_COBERTURA,
            todos_inactivos["state"])
    t.igual("E-27 con el motivo exacto", CHECK.TODOS_INACTIVOS, todos_inactivos["reason"])
    t.igual("E-27 no aprueba", False, CHECK.aprueba(todos_inactivos))

    # 5. Un resultado de un flujo FUERA del inventario que no pasa por la opcion catastral deja
    #    la cobertura sin resolver: o falta un flujo gobernado, o nadie declaro que no lo es.
    for nombre, extra in (
            ("declarando otro normalizador", _res(flujo="f-afuera", proveedor="otro")),
            ("con la corrida diciendolo",
             _res(flujo="f-afuera", proveedor="", refs=("e-2",))),
            ("consumiendo el crudo",
             _res(flujo="f-afuera", cadena=_cadena(consumido="v-crudo")))):
        salida = CHECK.evaluar(
            _caso(resultados=[_res(), extra],
                  evidencia=[_ev(), _ev("e-2", proveedor="otro")]),
            _senal("TRUE"))
        t.igual("E-27 un flujo de afuera %s deja sin resolver" % nombre, CHECK.SIN_COBERTURA,
                salida["state"])
        t.verdadero("E-27 y se nombra: %s" % nombre, "f-afuera" in salida["ignoredResults"])

    # 6. 🔴 El cuarto cerrojo, que faltaba: un RESULTADO sobre un flujo declarado inactivo es
    #    evidencia de que ese flujo corrio, asi que la declaracion se contradice. Antes ese
    #    resultado desaparecia por completo -no estaba en `flows`, no estaba en
    #    `ignoredResults`, no lo nombraba ningun aviso- y el conjunto salia PASS. Era la ultima
    #    forma que le quedaba a la puerta de salida que la regla vecina tuvo que sacar.
    inventario = _caminos(flujos=[{"flowId": "f-busqueda"},
                                  {"flowId": "f-bypass", "active": False,
                                   "source": "PROJECT_ARCHITECTURE"}])
    for nombre, extra in (
            ("declarando otro normalizador", _res(flujo="f-bypass", proveedor="otro")),
            ("con la corrida diciendolo",
             _res(flujo="f-bypass", proveedor="", refs=("e-2",))),
            ("consumiendo el crudo",
             _res(flujo="f-bypass", cadena=_cadena(consumido="v-crudo")))):
        salida = CHECK.evaluar(
            _caso(caminos=inventario, resultados=[_res(), extra],
                  evidencia=[_ev(), _ev("e-2", proveedor="otro")]),
            _senal("TRUE"))
        t.igual("E-27 un inactivo que corrio %s no da PASS" % nombre, CHECK.SIN_COBERTURA,
                salida["state"])
        t.verdadero("E-27 y el resultado no desaparece: %s" % nombre,
                    "f-bypass" in salida["ignoredResults"])
        t.verdadero("E-27 con un aviso que lo nombra: %s" % nombre,
                    any("f-bypass" in i for i in salida["issues"]))

    # Y un resultado LIMPIO sobre un inactivo se lista y no acusa nada: probar un camino muerto
    # no es un incumplimiento.
    limpio = CHECK.evaluar(
        _caso(caminos=inventario, resultados=[_res(), _res(flujo="f-bypass")]), _senal("TRUE"))
    t.igual("E-27 un inactivo con un resultado limpio no bloquea", CHECK.PASA, limpio["state"])
    t.verdadero("E-27 pero el resultado se lista", "f-bypass" in limpio["ignoredResults"])
    t.igual("E-27 y el flujo sigue fuera de los gobernados", ["f-busqueda"],
            limpio["governedFlows"])


# -- E-28 a E-30 — la corrida --------------------------------------------------

def test_e28_lo_mockeado_no_prueba(t):
    """E-28 (D5-20) — se distingue de lo real, y no llega a PASS."""
    salida = CHECK.evaluar(_caso(evidencia=[_ev(modo="MOCKED")]), _senal("TRUE"))
    t.igual("E-28 no pasa", CHECK.PARCIAL, salida["state"])
    t.igual("E-28 con el motivo", CHECK.EVIDENCIA_MOCKEADA, salida["reason"])
    t.igual("E-28 no aprueba", False, CHECK.aprueba(salida))
    t.igual("E-28 hay dos modos", ("REAL", "MOCKED"), CHECK.MODOS)

    # Una real junto a una mockeada alcanza: lo mockeado acompana.
    mixto = CHECK.evaluar(
        _caso(resultados=[_res(refs=("e-1", "e-2"))],
              evidencia=[_ev("e-1", modo="MOCKED"), _ev("e-2", modo="REAL")]),
        _senal("TRUE"))
    t.igual("E-28 con una real al lado pasa", CHECK.PASA, mixto["state"])

    # Y una evidencia sin modo declarado no es real.
    sin_modo = _ev()
    sin_modo.pop("mode")
    t.igual("E-28 una corrida sin modo no prueba", CHECK.PARCIAL,
            CHECK.evaluar(_caso(evidencia=[sin_modo]), _senal("TRUE"))["state"])

    # Y la evidencia de otro build o de otro runtime es de otro sistema.
    for campo, valor in (("buildId", "b-otro"), ("runtime", "chromium-otro")):
        ajena = CHECK.evaluar(_caso(evidencia=[_ev(**{campo: valor})]), _senal("TRUE"))
        t.igual("E-28 una evidencia con otro %s no cuenta" % campo, CHECK.PARCIAL,
                ajena["state"])
        t.verdadero("E-28 y se dice: %s" % campo,
                    any(CHECK.EVIDENCIA_DE_OTRA_CORRIDA in i for i in ajena["issues"]))

    # Y una referencia a una evidencia que no existe.
    huerfana = CHECK.evaluar(_caso(resultados=[_res(refs=("e-inexistente",))]), _senal("TRUE"))
    t.verdadero("E-28 una referencia huerfana se dice",
                any(CHECK.EVIDENCIA_HUERFANA in i for i in huerfana["issues"]))


def test_e29_sin_donde_correr_no_pasa(t):
    """E-29 — TEST_TARGET_UNAVAILABLE. Lo que no se ejecuto no pasa."""
    # 🔴 `available` se exige `True`, no truthy: con un truthy cualquiera, un `available: "no"`
    # daba PASS. Es la misma familia que `complete` de E-07 y `absent` de E-25.
    for objetivo in ({}, {"available": False}, None, {"available": "no"},
                     {"available": "false"}, {"available": 1}, {"available": "True"},
                     {"available": [1]}, {"otro": True}):
        salida = CHECK.evaluar(_caso(testTarget=objetivo), _senal("TRUE"))
        t.igual("E-29 con testTarget %r no pasa" % (objetivo,), CHECK.SIN_OBJETIVO,
                salida["state"])
        t.igual("E-29 con testTarget %r no aprueba" % (objetivo,), False, CHECK.aprueba(salida))

    # 🔴 Y no se convierte en NOT_APPLICABLE: que no haya donde correr no saca la regla.
    t.verdadero("E-29 sigue aplicando",
                CHECK.evaluar(_caso(testTarget={}), _senal("TRUE"))["signalValue"] == "TRUE")


def test_e30_nueve_estados_y_uno_aprueba(t):
    """E-30 (§13) — los nueve del pedido, alcanzables, y ninguno colapsado en PASS."""
    t.igual("E-30 son nueve estados", 9, len(CHECK.ESTADOS))
    t.igual("E-30 sin repetidos", 9, len(set(CHECK.ESTADOS)))
    for estado in ("PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                   "ADDRESS_FLOW_COVERAGE_UNRESOLVED", "CADASTRAL_PROVIDER_UNRESOLVED",
                   "INTEGRATION_CONTRACT_MISSING", "TEST_TARGET_UNAVAILABLE"):
        t.verdadero("E-30 %s existe" % estado, estado in CHECK.ESTADOS)

    caminos = _los_nueve_caminos()
    t.igual("E-30 los nueve son alcanzables", 9, len(caminos))
    for esperado, (caso, senal) in sorted(caminos.items()):
        salida = CHECK.evaluar(caso, senal)
        t.igual("E-30 se alcanza %s" % esperado, esperado, salida["state"])
        t.igual("E-30 y solo PASS aprueba: %s" % esperado, esperado == CHECK.PASA,
                CHECK.aprueba(salida))


# -- E-31 a E-33 — las fronteras -----------------------------------------------

def test_e31_d5_no_afirma_nada_de_la_regla_del_mapa(t):
    """E-31 (D5-21) — dos reglas del mismo parrafo, y ninguna contesta por la otra."""
    # 🔴 Sobre los NUEVE caminos, no sobre uno. Un solo resultado limpio no dice que el modulo no
    # pueda hablar de la otra regla: lo dice que ninguno de sus caminos lo haga.
    AJENOS = ("D6", "gcba-map-usage", "gcba-map-required", "georeferencedVisualizationPresent",
              "MAP_", "mapa", "map")
    for esperado, (caso, senal) in sorted(_los_nueve_caminos().items()):
        salida = CHECK.evaluar(caso, senal)
        t.igual("E-31 %s se alcanza" % esperado, esperado, salida["state"])
        t.igual("E-31 %s lleva la traza de D5" % esperado, TRAZA, salida["source"])
        texto = repr(salida)
        for ajeno in AJENOS:
            t.verdadero("E-31 %s no habla de %s" % (esperado, ajeno), ajeno not in texto)

    # Y un resultado normalizado con datos geograficos no cambia nada: las coordenadas son
    # evidencia INERTE para esta regla.
    t.verdadero("E-31 las coordenadas son inertes",
                "COORDINATE_DATA" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)
    con_coordenadas = CHECK.evaluar(
        _caso(resultados=[_res(refs=("e-1", "e-2"))],
              evidencia=[_ev(), _ev("e-2", tipo="COORDINATE_DATA")]),
        _senal("TRUE"))
    t.igual("E-31 un PASS de D5 con coordenadas sigue siendo de D5", CHECK.PASA,
            con_coordenadas["state"])
    for ajeno in AJENOS:
        t.verdadero("E-31 y no habla de %s" % ajeno, ajeno not in repr(con_coordenadas))

    # Resolver D5 no cambia la aplicabilidad de la otra regla.
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-31 D5 aplica", "D5" in bloque["applicableRules"])
    t.verdadero("E-31 y D6 no", "D6" not in bloque["applicableRules"])
    t.verdadero("E-31 D6 queda sin resolver",
                "D6" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-31 sin exigir su policy", "gcba-map-required" not in bloque["declaredPolicies"])

    # Y al reves: las dos senales en TRUE dan las dos reglas, cada una con lo suyo.
    dos = c_normativa.resolucion(
        {SENAL: _senal("TRUE"),
         "georeferencedVisualizationPresent": _senal(
             "TRUE", sid="georeferencedVisualizationPresent")})
    t.verdadero("E-31 las dos aplican", {"D5", "D6"} <= set(dos["applicableRules"]))
    t.verdadero("E-31 cada una con su policy",
                POLICY in dos["declaredPolicies"]
                and "gcba-map-required" in dos["declaredPolicies"])


def test_e32_d5_no_afirma_nada_de_la_validacion_duplicada(t):
    """E-32 (D5-22) — D5 mira el frontend y no contesta por la regla de las dos capas."""
    AJENOS = ("P5", "dual-layer-validation-required", "frontend-backend-validation",
              "frontendBackendValidationFlowPresent", "backend", "dual", "doble capa")
    for esperado, (caso, senal) in sorted(_los_nueve_caminos().items()):
        salida = CHECK.evaluar(caso, senal)
        texto = repr(salida)
        for ajeno in AJENOS:
            t.verdadero("E-32 %s no habla de %s" % (esperado, ajeno), ajeno not in texto)

    # La fila de P5 es otra fila, con otra senal y otros controles.
    p5 = c_matriz.regla("P5")
    d5 = c_matriz.regla("D5")
    t.verdadero("E-32 P5 tiene su propia senal",
                p5["applicability"]["signals"] != d5["applicability"]["signals"])
    t.vacio("E-32 y no comparten policies",
            [p for p in p5["policies"] if p in d5["policies"]])
    t.vacio("E-32 ni checks", [c for c in p5["checks"] if c in d5["checks"]])

    # Resolver D5 no hace aplicar a P5, y un PASS de D5 no instala su control.
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-32 P5 no aplica por la senal de D5", "P5" not in bloque["applicableRules"])
    t.verdadero("E-32 y queda sin resolver",
                "P5" in {u["rule"] for u in bloque["unresolvedRules"]})
    for control in p5["policies"] + p5["checks"]:
        t.verdadero("E-32 %s no se declara por D5" % control,
                    control not in bloque["declaredPolicies"] + bloque["declaredChecks"])

    # Y los controles de P5 siguen siendo un hueco: D5 no los construyo.
    faltantes = {h["id"] for h in c_matriz.controles_no_instalados(
        c_normativa.resolucion({SENAL: _senal("TRUE"),
                                "frontendBackendValidationFlowPresent": _senal(
                                    "TRUE", sid="frontendBackendValidationFlowPresent")}))}
    for control in p5["policies"] + p5["checks"]:
        t.verdadero("E-32 %s sigue sin instalar" % control, control in faltantes)


def test_e33_d5_no_crea_ni_declara_ninguna_skill(t):
    """E-33 (D5-09, §1) — el pedido lo prohibe, y lo prohibido se mide.

    Lo medible es esto y se dice: la cuenta de skills instaladas, que la fila de la matriz siga
    con cero referencias, que ningun artefacto de D5 declare una, y que las unicas que sus
    artefactos nombran sean las que resuelve el registro de agentes -incluida la que no existe-.
    """
    instaladas = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
    t.igual("E-33 siguen siendo 27 skills", 27, len(instaladas))
    t.verdadero("E-33 y ninguna es de direcciones ni de catastro",
                not [s for s in instaladas if "address" in s or "catastral" in s
                     or "cadastral" in s])

    # La fila de la matriz no tiene referencias a skills, y no las gano.
    fila = c_matriz.regla("D5")
    t.verdadero("E-33 la fila de la matriz no declara skills", not fila.get("skills"))
    t.vacio("E-33 ni por otro nombre",
            [k for k in fila if "skill" in k.lower()])

    # Ningun artefacto de D5 declara una skill: ni el frontmatter de la policy, ni el registro.
    policy = (CONTROLES / "policies" / (POLICY + ".md")).read_text(encoding="utf-8")
    frontmatter = policy.split("---")[1]
    t.verdadero("E-33 el frontmatter de la policy no declara skills",
                "skill" not in frontmatter.lower())
    for control in c_controles.de_la_regla("D5"):
        t.vacio("E-33 %s no declara skills en el registro" % control["id"],
                [k for k in control if "skill" in k.lower()])

    # Las unicas skills que los artefactos nombran son las que resuelve el registro de agentes.
    ruteos = CHECK.skills_de_ejecucion()
    t.igual("E-33 tres ruteos de ejecucion", 3, len(ruteos))
    for ruteo in ruteos:
        t.igual("E-33 %s sale del registro" % ruteo.get("skill"), CHEQUEO,
                ruteo["requestedFor"])
    # Y la del hueco: se pide, el registro la niega, y no se crea.
    ruteo = c_reg.resolver_ruteo("dev-integration", CHECK.SKILL_CATASTRAL)
    t.igual("E-33 la skill del hueco no es ruteable", False, ruteo["routable"])
    t.verdadero("E-33 y no existe en el disco",
                not (SKILLS / CHECK.SKILL_CATASTRAL).exists())


# -- E-34 a E-37 — la propagacion, el registro y la trazabilidad ---------------

def test_e34_la_unidad_propaga_senal_policy_y_check(t):
    """E-34 (D5-23) — y la forma vieja, con booleanos, sigue funcionando."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-34 la regla viaja", "D5" in bloque["applicableRules"])
    t.verdadero("E-34 la policy viaja", POLICY in bloque["declaredPolicies"])
    t.verdadero("E-34 el check viaja", CHEQUEO in bloque["declaredChecks"])
    t.verdadero("E-34 y la senal resuelta con su evidencia",
                bool(bloque["signals"][SENAL]["evidence"]))
    t.igual("E-34 con su valor", "TRUE", bloque["signals"][SENAL]["value"])

    # La forma vieja: un booleano suelto.
    viejo = c_normativa.resolucion({SENAL: True})
    t.verdadero("E-34 un booleano en TRUE sigue haciendo aplicar a D5",
                "D5" in viejo["applicableRules"])
    t.verdadero("E-34 con su policy", POLICY in viejo["declaredPolicies"])
    falso = c_normativa.resolucion({SENAL: False})
    t.verdadero("E-34 y en FALSE la deja afuera", "D5" in falso["notApplicableRules"])

    # 🔴 Y el campo `scope` es OPCIONAL: las senales que ya existen siguen validando sin el.
    sin_alcance = _senal("TRUE", alcance=None)
    t.vacio("E-34 una senal sin scope sigue siendo valida", c_senales.validar(sin_alcance))
    t.igual("E-34 y resuelve", "TRUE", c_senales.resolver_una(sin_alcance)["value"])
    con_alcance = _senal("TRUE")
    t.vacio("E-34 y una con scope tambien", c_senales.validar(con_alcance))

    # 🔴 Y el campo esta en EL SCHEMA, no solo en los datos. El validador no rechaza claves que no
    # declara, asi que una senal con `scope` valida igual si el schema no lo tiene: sin estas
    # aserciones, sacarlo del contrato no ponia nada en rojo.
    schema = c_senales.cargar_schema()
    alcance = schema["properties"]["scope"]
    t.igual("E-34 el schema declara scope como objeto", "object", alcance["type"])
    t.igual("E-34 con sus tres campos", ["id", "kind", "reference"],
            sorted(alcance["properties"]))
    t.igual("E-34 y las tres clases de alcance", list(CHECK.ALCANCES),
            alcance["properties"]["kind"]["enum"])
    t.verdadero("E-34 y no es obligatorio", "scope" not in schema.get("required", []))
    t.igual("E-34 el scope de la senal lo usa", "PROJECT", con_alcance["scope"]["kind"])


def test_e35_los_agentes_primarios_resuelven_por_el_registro(t):
    """E-35 (D5-24) — los agentes salen de la matriz y se resuelven contra el registro."""
    agentes = CHECK.agentes_primarios()
    t.igual("E-35 son dos", 2, len(agentes))
    t.igual("E-35 y son los que declara la matriz", c_matriz.regla("D5")["primaryAgents"],
            [a["agent"] for a in agentes])
    for a in agentes:
        t.igual("E-35 %s esta declarado en el registro" % a["agent"], True, a["declared"])
        t.igual("E-35 %s pide para este control" % a["agent"], CHEQUEO, a["requestedFor"])
        t.igual("E-35 %s lleva la traza" % a["agent"], TRAZA, a["source"])
        t.verdadero("E-35 %s existe como agente" % a["agent"], c_reg.hay_agente(a["agent"]))

    # 🔴 Se derivan de la matriz, no de una lista escrita en el check: si la matriz cambiara, esto
    # cambia con ella.
    fuente = (CONTROLES / "checks" / (CHEQUEO + ".py")).read_text(encoding="utf-8")
    t.verdadero("E-35 el check no guarda la lista de agentes en una constante",
                not hasattr(CHECK, "AGENTES_PRIMARIOS"))
    t.contiene("E-35 y los lee de la fila de la matriz", "matriz.regla(REGLA", fuente)

    # El check no redefine la propiedad: los agentes siguen siendo duenos de lo suyo.
    for a in agentes:
        declarado = c_reg.agente(a["agent"])
        t.verdadero("E-35 %s conserva su definicion" % a["agent"], bool(declarado))
        t.verdadero("E-35 %s no declara este control como suyo" % a["agent"],
                    CHEQUEO not in repr(declarado))


def test_e36_los_controles_dejan_de_ser_un_hueco(t):
    """E-36 (D5-25, §12) — instalados, declarados, sin archivos sueltos y sin cambiar la matriz."""
    reporte = c_controles.reporte()
    # 📌 Eran dieciocho cuando D5 cerro; D7 sumo seis. Exacto a proposito.
    t.igual("E-36 son cuarenta y dos controles", 42, reporte["summary"]["declaredControls"])
    t.verdadero("E-36 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-36 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-36 ningun archivo suelto", [], reporte["undeclared"])

    for control, tipo in ((POLICY, "POLICY"), (CHEQUEO, "CHECK")):
        t.igual("E-36 %s esta INSTALLED" % control, "INSTALLED", reporte["controls"][control])
        declarado = c_controles.control(control)
        t.igual("E-36 %s es del tipo que dice" % control, tipo, declarado["type"])
        t.igual("E-36 %s es de D5" % control, "D5", declarado["rule"])
        t.igual("E-36 %s trae su traza" % control, TRAZA, declarado["source"])
        t.verdadero("E-36 %s esta entre los instalados" % control,
                    control in c_controles.instalados()[tipo])

    t.igual("E-36 D5 tiene dos controles", 2, len(c_controles.de_la_regla("D5")))

    # 🔴 Y dejan de ser un hueco: la consulta que antes los reportaba como no instalados ya no.
    huecos = {h["id"]: h["state"] for h in c_matriz.controles_no_instalados(
        c_normativa.resolucion({SENAL: _senal("TRUE")}))}
    t.verdadero("E-36 la policy ya no es un hueco", POLICY not in huecos)
    t.verdadero("E-36 ni el check", CHEQUEO not in huecos)

    # Y la clasificacion de D5 en la matriz no cambio.
    fila = c_matriz.regla("D5")
    t.igual("E-36 D5 sigue CLASSIFIED", "CLASSIFIED", fila["status"])
    t.igual("E-36 y sigue CONDITIONAL", "CONDITIONAL", fila["applicability"]["mode"])
    t.igual("E-36 sobre la misma senal", [SENAL], fila["applicability"]["signals"])

    # 📌 Las reglas con TODOS sus controles construidos son las ocho instaladas, y D5 es la
    # ultima. Las otras dieciseis siguen declarando controles que no existen: es el estado normal
    # de una instalacion de a una regla, y va clavado en un numero exacto para que la proxima
    # regla obligue a tocar este test en vez de correr una banda floja.
    instalados = set(c_controles.instalados()["POLICY"] + c_controles.instalados()["CHECK"]
                     + c_controles.instalados()["REVIEW"])
    # 🔴 El sujeto se DERIVA de la matriz, no se escribe. La version anterior contaba
    # `policies + checks` y omitia `reviews`: hoy la cuenta sale igual porque los dos reviews que
    # la matriz declara -D3 y G2- estan instalados, asi que ninguna asercion lo notaba. Se afirma
    # en verde cuales son los tipos de control que una fila puede declarar, y el conteo usa esa
    # lista: el dia que la matriz gane un cuarto tipo, este test se pone en rojo y alguien mira.
    NO_SON_CONTROLES = {"id", "category", "operationalIntentEn", "applicability",
                        "primaryAgents", "status"}
    claves = set()
    for r in c_matriz.reglas():
        claves.update(r.keys())
    tipos = sorted(claves - NO_SON_CONTROLES)
    t.igual("E-36 una fila declara tres tipos de control", ["checks", "policies", "reviews"],
            tipos)
    t.verdadero("E-36 y los reviews que declara estan instalados",
                {r for regla in c_matriz.reglas() for r in regla.get("reviews") or []}
                <= instalados)

    completas, incompletas = [], []
    for r in c_matriz.reglas():
        suyos = set()
        for tipo in tipos:
            suyos.update(r.get(tipo) or [])
        if not suyos:
            continue
        (completas if suyos <= instalados else incompletas).append(r["id"])
    # 📌 Eran ocho cuando D5 cerro; D7 sumo seis controles, D8 dos y P1 cinco: once reglas.
    t.igual("E-36 once reglas tienen todos sus controles construidos",
            ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "G1", "G2", "P1"],
            sorted(completas))
    t.igual("E-36 y a las otras trece les falta alguno", 13, len(incompletas))
    t.verdadero("E-36 D5 ya no esta entre las que le falta", "D5" not in incompletas)


def test_e37_todo_resultado_conserva_la_traza(t):
    """E-37 (D5-26) — ES0901 / 6.3 / 7.1 / D5, en los nueve caminos."""
    caminos = _los_nueve_caminos()
    t.igual("E-37 se prueban los nueve", 9, len(caminos))
    for esperado, (caso, senal) in sorted(caminos.items()):
        salida = CHECK.evaluar(caso, senal)
        t.igual("E-37 %s se alcanza" % esperado, esperado, salida["state"])
        t.igual("E-37 %s conserva la traza" % esperado, TRAZA, salida["source"])
        t.igual("E-37 %s dice de que control es" % esperado, CHEQUEO, salida["control"])
        t.igual("E-37 %s dice de que senal depende" % esperado, SENAL, salida["signal"])

    # Y la remediacion tambien, que es lo otro que sale de este modulo.
    remedio = CHECK.remediacion(CHECK.evaluar(_caso(cadastralProvider={}), _senal("TRUE")))
    t.igual("E-37 la remediacion conserva la traza", TRAZA, remedio["source"])
    t.igual("E-37 y dice que no cumple", False, remedio["compliant"])
    t.igual("E-37 con el estado del hueco", "SPECIALIZED_SKILL_GAP", remedio["state"])

    # La traza es la de la fila citable, no una escrita a mano.
    t.igual("E-37 la traza coincide con la de la matriz", c_matriz.trazabilidad("D5")["rule"],
            TRAZA["rule"])
