# D6: verificar con que mapa se dibuja, sin inventar cual es el Mapa del GCBA.
#
# Escenarios E-01 a E-31 de docs/cambios/d6-visualizacion-georreferenciada/spec.md. Entre
# parentesis, el D6-nn del pedido de instalacion.
#
# 🔴 Nada de esto renderiza un mapa. Lo que se verifica es el CONTROL: que la identidad del
# proveedor entre como dato declarado y no se invente, que una libreria instalada no alcance, que
# una llamada a API GEO sea D5 y no D6, y que una vista que cumple no tape otra que no.
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


CHECK = _cargar("gcba-map-usage", "d6_check")

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D6"}

SENAL = "georeferencedVisualizationPresent"
POLICY = "gcba-map-required"
CHEQUEO = "gcba-map-usage"

BUILD = {"id": "b-2026-09-21", "runtime": "chromium-129"}
PROVEEDOR = {"id": "mapa-institucional", "source": "GCBA_NORMATIVE",
             "reference": "ES0901 6.3, pag. 19"}
CONTRATO = {"id": "contrato-de-integracion-del-mapa", "source": "ASI_INTEGRATION_CONTRACT",
            "reference": "acta de integracion del proyecto"}


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="s-1", tipo="PROJECT_DOCUMENTATION", ref="requisito de UX",
              claim="la aplicacion muestra incidentes sobre un mapa", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid=SENAL, **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    s.update(extra)
    return s


def _ev(eid="e-1", tipo="RENDERED_MAP_RUN", modo="REAL", proveedor="mapa-institucional",
        **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": "corrida#1",
         "claim": "la vista se dibujo", "buildId": BUILD["id"], "runtime": BUILD["runtime"],
         "mode": modo, "provider": proveedor}
    e.update(extra)
    return e


def _res(vista="v-mapa", proveedor="mapa-institucional", ejecucion="EXECUTED", refs=("e-1",)):
    return {"viewId": vista, "provider": proveedor, "execution": ejecucion,
            "evidenceRefs": list(refs)}


def _caso(vistas=None, resultados=None, evidencia=None, **extra):
    caso = {
        "application": {"id": "tramites", "environment": "test"},
        "build": dict(BUILD),
        "testTarget": {"available": True},
        "mapProvider": dict(PROVEEDOR),
        "integrationContract": dict(CONTRATO),
        "mapViews": {"source": "ROUTE_INVENTORY",
                     "views": [{"id": "v-mapa"}] if vistas is None else vistas},
        "results": [_res()] if resultados is None else resultados,
        "evidence": [_ev()] if evidencia is None else evidencia,
    }
    caso.update(extra)
    return caso


def _levanta(fn):
    try:
        fn()
    except Exception:
        return True
    return False


def _los_nueve_caminos():
    """Un caso legal por cada uno de los nueve estados. Lo usan E-25 y E-31."""
    return {
        "PASS": (_caso(), _senal("TRUE")),
        "FAIL": (_caso(resultados=[_res(proveedor="otro")]), _senal("TRUE")),
        "PARTIAL": (_caso(resultados=[_res(ejecucion="NOT_EXECUTED")]), _senal("TRUE")),
        "NOT_APPLICABLE": (_caso(), _senal("FALSE", [_ev_senal(claim="no hay mapa")])),
        "APPLICABILITY_UNRESOLVED": (_caso(), None),
        "MAP_VIEW_COVERAGE_UNRESOLVED": (_caso(mapViews={}), _senal("TRUE")),
        "GCBA_MAP_PROVIDER_UNRESOLVED": (_caso(mapProvider={}), _senal("TRUE")),
        "MAP_INTEGRATION_CONTRACT_MISSING": (_caso(integrationContract={}), _senal("TRUE")),
        "TEST_TARGET_UNAVAILABLE": (_caso(testTarget={}), _senal("TRUE")),
    }


# -- E-01 a E-08 — la senal y la aplicabilidad ---------------------------------

def test_e01_d6_es_condicional(t):
    """E-01 (D6-01) — CONDITIONAL sobre la senal, y la matriz no la edito este cambio."""
    d6 = c_matriz.regla("D6")
    t.igual("E-01 el modo", "CONDITIONAL", d6["applicability"]["mode"])
    t.igual("E-01 la senal", [SENAL], d6["applicability"]["signals"])
    t.igual("E-01 el id", "D6", d6["id"])
    t.igual("E-01 la categoria", "DESIGN", d6["category"])
    t.igual("E-01 la intencion operativa no cambio",
            "Georeferenced visualizations must use the GCBA Map.", d6["operationalIntentEn"])
    t.igual("E-01 los agentes", ["dev-integration", "dev-frontend"], d6["primaryAgents"])
    t.igual("E-01 la policy ya estaba declarada", [POLICY], d6["policies"])
    t.igual("E-01 y el check", [CHEQUEO], d6["checks"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d6["status"])
    t.igual("E-01 la senal la declara D6 y nadie mas", ["D6"], c_senales.reglas_de(SENAL))


def test_e02_true_hace_aplicable(t):
    """E-02 (D6-02) — TRUE con evidencia deja D6 aplicable con sus dos controles."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-02 D6 aplica", "D6" in bloque["applicableRules"])
    t.verdadero("E-02 exige su policy", POLICY in bloque["declaredPolicies"])
    t.verdadero("E-02 y su check", CHEQUEO in bloque["declaredChecks"])
    t.igual("E-02 la senal resuelta viaja", "TRUE", bloque["signals"][SENAL]["value"])


def test_e03_false_hace_no_aplicable(t):
    """E-03 (D6-03) — FALSE con evidencia deja D6 fuera."""
    evidencia = [_ev_senal(claim="el alcance es backend, no expone ninguna vista de mapa")]
    bloque = c_normativa.resolucion({SENAL: _senal("FALSE", evidencia)})
    t.verdadero("E-03 D6 no aplica", "D6" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no esta entre las aplicables", "D6" not in bloque["applicableRules"])
    t.verdadero("E-03 su policy no se exige", POLICY not in bloque["declaredPolicies"])
    t.igual("E-03 el check tambien lo dice", "NOT_APPLICABLE",
            CHECK.evaluar(_caso(), _senal("FALSE", evidencia))["state"])


def test_e04_sin_senal_queda_sin_resolver(t):
    """E-04 (D6-04) — sin senal, D6 sin resolver con la que falta escrita."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D6 esta sin resolver", "D6" in sin_resolver)
    t.igual("E-04 con el motivo", "APPLICABILITY_UNRESOLVED", sin_resolver["D6"]["reason"])
    t.igual("E-04 y la senal que falta", [SENAL], sin_resolver["D6"]["missingSignals"])
    salida = CHECK.evaluar(_caso(), None)
    t.igual("E-04 el check tambien", "APPLICABILITY_UNRESOLVED", salida["state"])
    t.igual("E-04 y nombra la senal", [SENAL], salida["missingSignals"])


def test_e05_lo_ausente_nunca_es_falso(t):
    """E-05 (D6-05) — que no haya un componente llamado mapa no es evidencia de nada."""
    caminos = {
        "sin senal": {},
        "senal UNRESOLVED": {SENAL: _senal("UNRESOLVED", [])},
        "senal sin evidencia": {SENAL: _senal("TRUE", [])},
        "no se encontro componente": {SENAL: _senal("FALSE", [_ev_senal(
            tipo="AGENT_STATEMENT", ref="grep -ri mapa src/",
            claim="no aparecio ningun componente que se llame mapa")])},
        "no hay lat/lon": {SENAL: _senal("FALSE", [_ev_senal(
            tipo="AGENT_STATEMENT", ref="grep -ri latitud src/",
            claim="no aparece ninguna coordenada")])},
    }
    for nombre, senales in caminos.items():
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-05 %s no vuelve D6 no aplicable" % nombre,
                    "D6" not in bloque["notApplicableRules"])
        t.verdadero("E-05 %s la deja sin resolver" % nombre,
                    "D6" in {u["rule"] for u in bloque["unresolvedRules"]})

    # Una senal que la matriz no declara no vale: el inventario sale de la matriz.
    inventada = c_senales.producir("mapPresent", [_ev_senal()], {"type": "HUMAN"}, "TRUE")
    t.verdadero("E-05 una senal inventada se marca",
                c_senales.NO_DECLARADA in inventada["states"])
    t.igual("E-05 y no queda en TRUE", "UNRESOLVED", inventada["value"])
    declarada = c_senales.producir(SENAL, [_ev_senal()], {"type": "HUMAN"}, "TRUE")
    t.verdadero("E-05 la declarada no se marca",
                c_senales.NO_DECLARADA not in declarada["states"])


def test_e06_frontend_no_alcanza(t):
    """E-06 (D6-06) — un frontend no es un mapa."""
    bloque = c_normativa.resolucion({"frontendPresent": _senal("TRUE", sid="frontendPresent")})
    t.verdadero("E-06 D6 no aplica por frontendPresent", "D6" not in bloque["applicableRules"])
    t.verdadero("E-06 queda sin resolver",
                "D6" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-06 y D4 si aplica, que es la que mira el frontend",
                "D4" in bloque["applicableRules"])
    t.verdadero("E-06 la senal del frontend no es la de D6",
                "frontendPresent" in CHECK.SENALES_QUE_NO_SUSTITUYEN)
    t.igual("E-06 el check sigue pidiendo la suya", "APPLICABILITY_UNRESOLVED",
            CHECK.evaluar(_caso(), None)["state"])


def test_e07_el_campo_de_direccion_no_alcanza(t):
    """E-07 (D6-07) — un campo de direccion es D5, no D6."""
    bloque = c_normativa.resolucion(
        {"frontendAddressInputPresent": _senal("TRUE", sid="frontendAddressInputPresent")})
    t.verdadero("E-07 D5 aplica", "D5" in bloque["applicableRules"])
    t.verdadero("E-07 D6 no", "D6" not in bloque["applicableRules"])
    t.verdadero("E-07 y queda sin resolver",
                "D6" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-07 la senal de la direccion no es la de D6",
                "frontendAddressInputPresent" in CHECK.SENALES_QUE_NO_SUSTITUYEN)
    t.igual("E-07 son las dos que no sustituyen", 2, len(CHECK.SENALES_QUE_NO_SUSTITUYEN))
    t.verdadero("E-07 y la de D6 no esta entre ellas",
                SENAL not in CHECK.SENALES_QUE_NO_SUSTITUYEN)


def test_e08_la_senal_sale_de_evidencia_de_una_visualizacion(t):
    """E-08 — una dependencia o la palabra de un agente no la sostienen solas."""
    debiles = ("AGENT_STATEMENT", "REPOSITORY_DEPENDENCY")
    for tipo in debiles:
        t.verdadero("E-08 %s es una fuente debil" % tipo, tipo in c_senales.FUENTES_DEBILES)
        resuelta = c_senales.resolver_una(_senal("TRUE", [_ev_senal(
            tipo=tipo, ref="package.json", claim="hay una libreria de mapas instalada")]))
        t.igual("E-08 %s deja la senal sin resolver" % tipo, "UNRESOLVED", resuelta["value"])

    # Con documentacion del proyecto que describe la visualizacion, si.
    resuelta = c_senales.resolver_una(_senal("TRUE"))
    t.igual("E-08 la documentacion del proyecto la sostiene", "TRUE", resuelta["value"])
    t.verdadero("E-08 y conserva su evidencia", bool(resuelta["evidence"]))


# -- E-09 a E-12 — el proveedor, que no se inventa -----------------------------

def test_e09_sin_identidad_no_hay_con_que_comparar(t):
    """E-09 (D6-12) — GCBA_MAP_PROVIDER_UNRESOLVED, y no se adivina."""
    for nombre, proveedor in (("vacio", {}), ("sin id", {"source": "GCBA_NORMATIVE",
                                                         "reference": "x"})):
        salida = CHECK.evaluar(_caso(mapProvider=proveedor), _senal("TRUE"))
        t.igual("E-09 %s da GCBA_MAP_PROVIDER_UNRESOLVED" % nombre,
                "GCBA_MAP_PROVIDER_UNRESOLVED", salida["state"])
        t.verdadero("E-09 %s no pasa" % nombre, not CHECK.aprueba(salida))
        t.verdadero("E-09 %s dice por que" % nombre, bool(salida.get("detail")))
    t.verdadero("E-09 y no inventa un proveedor",
                "mapProvider" not in CHECK.evaluar(_caso(mapProvider={}), _senal("TRUE")))


def test_e10_sin_contrato_no_hay_como_reconocer_el_uso(t):
    """E-10 (D6-13) — MAP_INTEGRATION_CONTRACT_MISSING, que es otro hueco."""
    for nombre, contrato in (("vacio", {}), ("sin fuente", {"id": "c", "reference": "r"}),
                             ("sin referencia", {"id": "c", "source": "GCBA_NORMATIVE"})):
        salida = CHECK.evaluar(_caso(integrationContract=contrato), _senal("TRUE"))
        t.igual("E-10 %s da MAP_INTEGRATION_CONTRACT_MISSING" % nombre,
                "MAP_INTEGRATION_CONTRACT_MISSING", salida["state"])
        t.verdadero("E-10 %s no pasa" % nombre, not CHECK.aprueba(salida))
    # 🔴 Son dos estados distintos y no uno: se arreglan preguntandole a personas distintas.
    t.verdadero("E-10 el proveedor se resolvio antes",
                CHECK.evaluar(_caso(integrationContract={}),
                              _senal("TRUE")).get("mapProvider") is not None)
    t.verdadero("E-10 y los dos estados existen por separado",
                CHECK.SIN_PROVEEDOR != CHECK.SIN_CONTRATO)


def test_e11_una_identidad_sin_fuente_no_identifica(t):
    """E-11 — un id sin origen citado es un nombre que alguien escribio."""
    casos = {
        "sin fuente": {"id": "mapa-institucional", "reference": "x"},
        "fuente inventada": {"id": "mapa-institucional", "source": "ME_LO_DIJERON",
                             "reference": "x"},
        "sin referencia": {"id": "mapa-institucional", "source": "GCBA_NORMATIVE"},
        "referencia vacia": {"id": "mapa-institucional", "source": "GCBA_NORMATIVE",
                             "reference": ""},
    }
    for nombre, proveedor in casos.items():
        ok, motivo = CHECK.proveedor_valido({"mapProvider": proveedor})
        t.verdadero("E-11 %s no es valido" % nombre, not ok)
        t.verdadero("E-11 %s dice por que" % nombre, bool(motivo))
    ok, _ = CHECK.proveedor_valido({"mapProvider": dict(PROVEEDOR)})
    t.verdadero("E-11 con los tres campos si", ok)

    # 🔴 Un espacio NO es un dato declarado. La primera version comparaba contra la cadena
    # vacia, y `" "` es truthy: un caso con toda la identidad en blancos llegaba a PASS, o sea
    # D6 informaba cumplimiento con una identidad que no nombra nada y no cita en ningun lado.
    blancos = (" ", "\t", "\n", "   ", "\t\n ")
    for blanco in blancos:
        t.verdadero("E-11 un id en blanco (%r) no identifica" % blanco,
                    not CHECK.proveedor_valido(
                        {"mapProvider": dict(PROVEEDOR, id=blanco)})[0])
        t.verdadero("E-11 ni una referencia en blanco (%r)" % blanco,
                    not CHECK.proveedor_valido(
                        {"mapProvider": dict(PROVEEDOR, reference=blanco)})[0])
        t.verdadero("E-11 ni un contrato en blanco (%r)" % blanco,
                    not CHECK.contrato_valido(
                        {"integrationContract": dict(CONTRATO, id=blanco)})[0])
        t.verdadero("E-11 ni una vista con id en blanco (%r)" % blanco,
                    not CHECK.cobertura_valida(
                        {"mapViews": {"source": "ROUTE_INVENTORY",
                                      "views": [{"id": blanco}]}})[0])
    t.igual("E-11 la funcion que lo decide saca los blancos", "", CHECK.declarado("  \t\n "))
    t.igual("E-11 y conserva lo que hay", "mapa", CHECK.declarado("  mapa  "))
    # 🔴 Es `strip`, no un aplastado: no junta dos ids que difieren por dentro.
    t.verdadero("E-11 un blanco interno no se toca",
                CHECK.declarado(" v mapa ") != CHECK.declarado(" v  mapa "))

    # Y lo que se informa sale normalizado, los dos: publicar un id distinto del que se compara
    # es como se lee un FAIL que no se entiende.
    informado = CHECK.evaluar(
        _caso(mapProvider=dict(PROVEEDOR, id=" mapa-institucional "),
              integrationContract=dict(CONTRATO, id=" contrato "),
              resultados=[_res(proveedor=" mapa-institucional ", refs=("e-1",))],
              evidencia=[_ev(proveedor=" mapa-institucional ")]), _senal("TRUE"))
    t.igual("E-11 el proveedor se informa normalizado", "mapa-institucional",
            informado["mapProvider"]["id"])
    t.igual("E-11 y el contrato tambien", "contrato",
            informado["integrationContract"]["id"])

    # De punta a punta: todo en blancos no puede terminar en PASS.
    en_blanco = _caso(
        mapProvider=dict(PROVEEDOR, id=" ", reference=" "),
        integrationContract=dict(CONTRATO, id=" ", reference=" "),
        vistas=[{"id": " "}],
        resultados=[_res(" ", proveedor=" ", refs=("e-1",))],
        evidencia=[_ev(proveedor=" ")])
    salida = CHECK.evaluar(en_blanco, _senal("TRUE"))
    t.igual("E-11 una identidad en blancos no llega a PASS",
            "GCBA_MAP_PROVIDER_UNRESOLVED", salida["state"])
    t.verdadero("E-11 y no aprueba", not CHECK.aprueba(salida))
    t.igual("E-11 son cinco fuentes defendibles", 5, len(CHECK.FUENTES_DE_PROVEEDOR))
    for fuente in CHECK.FUENTES_DE_PROVEEDOR:
        ok, _ = CHECK.proveedor_valido(
            {"mapProvider": {"id": "x", "source": fuente, "reference": "r"}})
        t.verdadero("E-11 %s sirve como origen" % fuente, ok)


# 🔴 El invariante de D6: un artefacto de la regla no lleva el mecanismo del Mapa del GCBA. Lo
# que se busca es ESTRUCTURAL -una URL, un CRS, una plantilla de tiles, un encabezado de
# autenticacion, un especificador de paquete, una declaracion de sdk/endpoint/layer-. El barrido
# de nombres de proveedor es la segunda red, y las dos se prueban con fugas crudas.
PROHIBIDOS = (
    # localizadores de red: con esquema, sin esquema, con puerto —con o sin punto— o una IP.
    #
    # 🔴 Todos con `(?i)`. Cuatro de estos patrones no lo llevaban, y en codigo la forma normal
    # de escribir esto es una constante en MAYUSCULA: `HTTPS://MAPA.GCBA.GOB.AR/BASE` y
    # `/tiles/{Z}/{X}/{Y}.png` escapaban enteros. Era una dimension completa, no una forma.
    r"(?i)https?://",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*\.(ar|com|net|org|gov|gob|io|dev|app|gl|bue|tech)\b",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*:\d{2,5}\b",
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    r"(?i)\{z\}|\{x\}|\{y\}",
    # servicios geoespaciales
    r"(?i)\b(wmts|wms|wfs|tile[_ -]?matrix(set)?|tile[_ -]?grid|geoserver|geoportal)\b",
    # sistemas de coordenadas, con etiqueta o sueltos
    r"(?i)\b(epsg|srid|crs)\b\s*[:=]?\s*\d{3,6}",
    r"\b(4326|3857|900913|22195|22185|4269)\b",
    # credenciales. El numero es parte del patron a proposito: `token adentro` es prosa
    # -esta en el propio check- y `Token 8f3a2b9c` es una credencial.
    r"(?i)\b(bearer|token)\s+[A-Za-z0-9._-]*\d[A-Za-z0-9._-]*",
    r"(?i)\b(api[_-]?key|access[_-]?token|client[_-]?secret|subscription[_-]?key)\b\s*[:=]",
    # paquetes: por el gestor, por el scope, o por como se importa —que es la forma mas comun
    # del frontend y la que faltaba.
    r"(?i)\b(npm|pnpm|yarn|pip|composer|nuget|gem)\s+(i|install|add|require)\b",
    r"@[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*",
    r"(?i)\b(import|require)\b[^\n]{0,40}[\"'][a-z0-9@][a-z0-9@/._-]*"
    r"(js|gl|sdk|map|mapa|leaflet)[\"']",
    # declaraciones del mecanismo. El separador es parte del patron: la policy dice "no se
    # declara ningun endpoint" y eso es prosa, no una declaracion.
    #
    # 🔴 La comilla opcional no es cosmetica: en un json o en un `repr` la clave viene citada
    # -`"sdk": "..."`- y sin ella el patron no veia una `sdk` inyectada en la fila de la matriz.
    r"(?i)\b(sdk|tile[_-]?source|tile[_-]?url|endpoint|layer[_-]?id|capa[_-]?id)\b[\"']?\s*[:=]",
    r"(?i)\bse llama\b[^\n]{0,40}[a-z0-9]+-[a-z0-9-]+",
)

# Proveedores de mapas, incluidos los que el pedido nombraba como contraejemplos. Acá no se
# nombra ninguno: una lista de prohibidos envejece, corre el eje de la regla y deja al
# invariante sin poder distinguir un contraejemplo de una invencion.
#
# 🔴 Los distintivos se buscan sobre el texto SIN separadores, asi `Open Layers`, `open-layers`
# y `openlayers` son lo mismo: partir un nombre en dos era una de las formas que escapaban.
PEGADOS = ("openlayers", "openstreetmap", "googlemaps", "googlemap", "heremaps",
           "maplibre", "mapbox", "leaflet", "arcgis", "deckgl")
# Los cortos o ambiguos van con borde de palabra y sin normalizar: `carto` esta adentro de
# `cartografia` y `esri` se forma entre `materiales` y `rigen` si se quitan los espacios.
SUELTOS = ("esri", "carto", "osm", "cesium", "tomtom", "here maps")


def _secciones_de_d6_del_doc():
    """Las dos secciones que D6 agrego a `docs/normativa-7.1.md`.

    Se barren esas y no el archivo entero: el documento cubre las 24 reglas, y el dia que D7
    cite el endpoint del storage el barrido de D6 no tiene por que ponerse en rojo. Que los dos
    titulos existan se afirma aparte, asi que renombrarlos no achica el sujeto en silencio.
    """
    texto = (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8")
    titulos = ("## Dos reglas en el mismo párrafo: D5 y D6",
               "## El mecanismo que el harness no sabe")
    trozos = []
    for titulo in titulos:
        if titulo not in texto:
            continue
        resto = texto.split(titulo, 1)[1]
        trozos.append(resto.split("\n## ", 1)[0])
    return titulos, trozos


def _artefactos_de_d6():
    """Los cinco artefactos de D6, como los declara la tabla `Qué se construye` de la spec."""
    matriz_entera = (RAIZ / "harnesses" / "desarrollo" / "reglas"
                     / "es0901-7.1-normative-matrix.json").read_text(encoding="utf-8")
    titulos, trozos = _secciones_de_d6_del_doc()
    return {
        "la policy": (CONTROLES / "policies" / (POLICY + ".md")).read_text(encoding="utf-8"),
        "el check": (CONTROLES / "checks" / (CHEQUEO + ".py")).read_text(encoding="utf-8"),
        "el registro": repr(c_controles.de_la_regla("D6")),
        "la fila de la matriz": repr(c_matriz.regla("D6")),
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


def test_e12_ningun_artefacto_lleva_el_mecanismo(t):
    """E-12 (§5) — el invariante sobre los CINCO artefactos, y las dos mitades que lo sostienen.

    🔴 El sujeto es lo que fallaba antes: el barrido leia dos de los cinco. `docs/normativa-7.1.md`
    y la fila de la matriz son artefactos de D6 segun la tabla `Qué se construye` de la spec, y
    nadie los miraba.
    """
    titulos, trozos = _secciones_de_d6_del_doc()
    t.igual("E-12 las dos secciones de D6 estan en la doc", len(titulos), len(trozos))
    t.verdadero("E-12 y tienen contenido", all(len(x) > 400 for x in trozos))

    artefactos = _artefactos_de_d6()
    t.igual("E-12 son seis textos los que se barren", 6, len(artefactos))
    for nombre, texto in sorted(artefactos.items()):
        t.igual("E-12 %s no lleva el mecanismo" % nombre, [], _fugas_en(texto))

    # Y el resultado que el check produce, que es lo que viaja a un plan.
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-12 el resultado no lo lleva tampoco", [],
            _fugas_en(repr({k: v for k, v in salida.items() if k != "mapProvider"})))
    for estado in ("GCBA_MAP_PROVIDER_UNRESOLVED", "MAP_INTEGRATION_CONTRACT_MISSING"):
        t.igual("E-12 ni el resultado de %s" % estado, [], _fugas_en(repr(
            CHECK.evaluar(_caso(mapProvider={}) if "PROVIDER" in estado
                          else _caso(integrationContract={}), _senal("TRUE")))))

    # 🔴 La otra mitad. Las formas son CRUDAS: ninguna se escribio para que el patron la agarre.
    FUGAS = (
        'tileUrl: https://mapa.example/tiles/{z}/{x}/{y}.png',
        'CRS = "EPSG:4326"',
        'npm install @gcba/mapa-sdk',
        'headers = {"Authorization": "Bearer abc123def"}',
        'LAYER_ID = "capa_base_2024"',
        'SDK = "el sdk institucional"',
        'sdk: mapa-gcba-js',
        'endpoint: /api/v1/mapa',
        'TILE_SOURCE = "tiles.example/base"',
        'access_token = "pk.eyJ1IjoiZ2NiYSJ9"',
        'api_key: 8f3a2b',
        'ENDPOINT = "https://mapa-gcba.apps.buenosaires.gob.ar/api"',
        'provider = "leaflet"',
        "se dibuja con OpenLayers sobre una capa propia",
        "no alcanza con Google Maps ni con Mapbox",
        'IMPORT = "@arcgis/core/Map"',
        "el fallback usa OpenStreetMap",
        'CAPA_ID = "gcba_base"',
        # 🔴 Las quince formas que escapaban a la primera version del barrido. Ninguna se
        # escribio para que el patron la agarre: son las que alguien escribiria de verdad.
        "mapas.gcba.gov.ar/base",
        '"mapa-institucional:8080/wmts"',
        "10.20.30.40/geoserver",
        "servicio wmts institucional",
        'tileMatrixSet = "GCBA-base-3857"',
        "CRS = 4326",
        "srid 22195",
        '"Open Layers"',
        '"Leaf let"',
        '"open-layers"',
        '"googlemap"',
        "pnpm add mapa-gcba-sdk",
        "el SDK institucional se llama mapa-gcba-js",
        "Authorization: Token 8f3a2b9c",
        "mapa.gcba.gob.ar",
        # La forma citada, que es como entraria en la matriz o en el registro.
        '"sdk": "mapa-gcba-js"',
        '{"endpoint": "/mapa/v1"}',
        # En MAYUSCULA, que es como se escribe una constante en codigo.
        'URL = "HTTPS://MAPA.GCBA.GOB.AR/BASE"',
        'PLANTILLA = "/tiles/{Z}/{X}/{Y}.png"',
        'HOST = "MAPA.GCBA.GOB.AR"',
        # Host sin punto con puerto, y TLD fuera de la lista original.
        'servidor = "mapa-interno:8443"',
        'dev = "localhost:8080"',
        "mapa.gcba.bue",
        "mapa.gcba.tech",
        # La forma mas comun del frontend.
        'import Mapa from "gcba-mapa-js"',
        'require("gcba-mapa-js")',
    )
    t.igual("E-12 son cuarenta y cuatro formas de fuga", 44, len(FUGAS))
    for fuga in FUGAS:
        t.verdadero("E-12 se detecta: %s" % fuga[:40], bool(_fugas_en(fuga)))

    # La premisa que hace valer la mitad de arriba: el texto real, con una fuga adentro, deja de
    # estar limpio.
    base = artefactos["la policy"]
    t.igual("E-12 la premisa: la policy esta limpia", [], _fugas_en(base))
    t.verdadero("E-12 y con una fuga adentro deja de estarlo",
                bool(_fugas_en(base + '\nTILE_URL = "https://t.example/{z}/{x}/{y}.png"\n')))
    t.verdadero("E-12 y la doc tambien",
                bool(_fugas_en(artefactos["la doc"] + "\nEl mapa esta en mapa.gcba.gob.ar.\n")))

    # 🔴 La tercera mitad: lo que NO es una fuga. Un barrido que se pone en rojo con texto
    # correcto es un barrido que alguien apaga la primera vez que lo ve fallar sin motivo.
    LIMPIOS = (
        "API GEO del catalogo, que es de D5 y no de D6",
        "no se declara ningun endpoint, ningun sdk y ningun tile source",
        "la identidad entra como dato declarado con su fuente citada",
        "ES0901 6.3, pag. 19",
        "las vistas materiales rigen la verificacion de la regla",
        "la cartografia institucional no es el tema de esta regla",
        "GCBA_MAP_PROVIDER_UNRESOLVED / MAP_INTEGRATION_CONTRACT_MISSING",
        "controles/checks/gcba-map-usage.py y gcba-map-required.md",
        "docs/normativa-7.1.md, es0901-7.1.json y la matriz",
        "no hay un token adentro de este archivo",
        "27 skills instaladas y 16 controles declarados",
    )
    for limpio in LIMPIOS:
        t.igual("E-12 no dispara con: %s" % limpio[:38], [], _fugas_en(limpio))


# -- E-13 a E-17 — lo que no prueba nada ---------------------------------------

def _con_evidencia_sola(tipo, eid="e-1"):
    """Un caso donde la unica evidencia de la vista es de la clase que se prueba."""
    return _caso(resultados=[_res(refs=(eid,))], evidencia=[_ev(eid, tipo=tipo)])


def test_e13_las_coordenadas_solas_no_pasan(t):
    """E-13 (D6-08) — hay coordenadas en cualquier base de datos."""
    salida = CHECK.evaluar(_con_evidencia_sola("COORDINATE_DATA"), _senal("TRUE"))
    t.igual("E-13 el estado", "PARTIAL", salida["state"])
    t.igual("E-13 con el motivo", "RENDERED_EVIDENCE_MISSING", salida["reason"])
    t.verdadero("E-13 no pasa", not CHECK.aprueba(salida))
    t.verdadero("E-13 y la clase esta declarada inerte",
                "COORDINATE_DATA" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)


def test_e14_la_libreria_instalada_no_pasa(t):
    """E-14 (D6-09) — un paquete en el manifiesto no es un mapa dibujado."""
    salida = CHECK.evaluar(_con_evidencia_sola("REPOSITORY_DEPENDENCY"), _senal("TRUE"))
    t.igual("E-14 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-14 no pasa", not CHECK.aprueba(salida))
    t.verdadero("E-14 la dependencia es inerte",
                "REPOSITORY_DEPENDENCY" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)
    # Y un componente que existe tampoco: existir no es usarse.
    salida = CHECK.evaluar(_con_evidencia_sola("MAP_COMPONENT_PRESENT"), _senal("TRUE"))
    t.igual("E-14 un componente declarado tampoco", "PARTIAL", salida["state"])


def test_e15_api_geo_es_d5(t):
    """E-15 (D6-10) — llamar a API GEO no dice con que mapa se dibuja."""
    salida = CHECK.evaluar(_con_evidencia_sola("GEO_API_CALL"), _senal("TRUE"))
    t.igual("E-15 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-15 no pasa", not CHECK.aprueba(salida))
    t.verdadero("E-15 API GEO es inerte para D6",
                "GEO_API_CALL" in CHECK.EVIDENCIA_QUE_NO_PRUEBA)
    t.verdadero("E-15 y no esta entre las que prueban",
                "GEO_API_CALL" not in CHECK.EVIDENCIA_DE_CORRIDA)
    # Ni sumando todas las inertes juntas.
    todas = _caso(resultados=[_res(refs=tuple("e-%d" % i for i in range(
        len(CHECK.EVIDENCIA_QUE_NO_PRUEBA))))],
        evidencia=[_ev("e-%d" % i, tipo=tipo)
                   for i, tipo in enumerate(CHECK.EVIDENCIA_QUE_NO_PRUEBA)])
    salida = CHECK.evaluar(todas, _senal("TRUE"))
    t.igual("E-15 las seis inertes juntas tampoco", "PARTIAL", salida["state"])
    t.igual("E-15 son seis", 6, len(CHECK.EVIDENCIA_QUE_NO_PRUEBA))


def test_e16_la_captura_sola_no_pasa(t):
    """E-16 (D6-11) — una captura acompana y no prueba."""
    salida = CHECK.evaluar(_con_evidencia_sola("SCREENSHOT"), _senal("TRUE"))
    t.igual("E-16 el estado", "PARTIAL", salida["state"])
    t.verdadero("E-16 no pasa", not CHECK.aprueba(salida))
    t.verdadero("E-16 la captura acompana", "SCREENSHOT" in CHECK.EVIDENCIA_DE_APOYO)
    t.verdadero("E-16 y no prueba", "SCREENSHOT" not in CHECK.EVIDENCIA_DE_CORRIDA)
    # Una confirmacion humana tampoco, y es la otra de apoyo.
    t.igual("E-16 la confirmacion humana tampoco", "PARTIAL",
            CHECK.evaluar(_con_evidencia_sola("HUMAN_CONFIRMATION"), _senal("TRUE"))["state"])
    t.igual("E-16 son dos de apoyo", 2, len(CHECK.EVIDENCIA_DE_APOYO))


def test_e17_la_palabra_de_un_agente_no_pasa(t):
    """E-17 — una opinion con formato de evidencia, y una configuracion que no renderiza."""
    for tipo in ("AGENT_STATEMENT", "TILE_CONFIGURATION"):
        salida = CHECK.evaluar(_con_evidencia_sola(tipo), _senal("TRUE"))
        t.igual("E-17 %s deja PARTIAL" % tipo, "PARTIAL", salida["state"])
        t.verdadero("E-17 %s no pasa" % tipo, not CHECK.aprueba(salida))
        t.verdadero("E-17 %s esta declarada inerte" % tipo,
                    tipo in CHECK.EVIDENCIA_QUE_NO_PRUEBA)
    t.igual("E-17 la unica que prueba es una", 1, len(CHECK.EVIDENCIA_DE_CORRIDA))
    t.igual("E-17 y es la corrida renderizada", ("RENDERED_MAP_RUN",),
            CHECK.EVIDENCIA_DE_CORRIDA)


# -- E-18 a E-24 — la cobertura, el bypass y la corrida ------------------------

def test_e18_todas_las_vistas_con_el_mapa_pasan(t):
    """E-18 (D6-14) — con evidencia de corrida real, PASS."""
    salida = CHECK.evaluar(_caso(), _senal("TRUE"))
    t.igual("E-18 el estado", "PASS", salida["state"])
    t.verdadero("E-18 aprueba", CHECK.aprueba(salida))
    t.igual("E-18 con su vista", ["v-mapa"], salida["governedViews"])
    t.igual("E-18 y el proveedor declarado", "mapa-institucional", salida["mapProvider"]["id"])
    t.vacio("E-18 sin avisos", salida["issues"])

    # Tres vistas, las tres corridas, las tres con el mapa institucional.
    tres = _caso(
        vistas=[{"id": "v-%d" % i} for i in range(3)],
        resultados=[_res("v-%d" % i, refs=("e-%d" % i,)) for i in range(3)],
        evidencia=[_ev("e-%d" % i) for i in range(3)])
    salida = CHECK.evaluar(tres, _senal("TRUE"))
    t.igual("E-18 tres vistas tambien pasan", "PASS", salida["state"])
    t.igual("E-18 y las tres se contaron", 3, len(salida["views"]))

    # 🔴 Un proveedor con blancos alrededor, coherente de punta a punta, TIENE que pasar. La
    # primera version de `declarado` normalizaba un solo lado de la comparacion: la identidad
    # pasaba `proveedor_valido` y despues ninguna comparacion del modulo podia igualarla, asi que
    # un caso correcto salia FAIL por proveedor alterno. Normalizar un lado es peor que no
    # normalizar ninguno.
    padeado = _caso(
        mapProvider=dict(PROVEEDOR, id=" mapa-institucional "),
        resultados=[_res(proveedor=" mapa-institucional ", refs=("e-1",))],
        evidencia=[_ev(proveedor=" mapa-institucional ")])
    salida = CHECK.evaluar(padeado, _senal("TRUE"))
    t.igual("E-18 un proveedor con blancos alrededor pasa igual", "PASS", salida["state"])
    t.igual("E-18 y se informa normalizado", "mapa-institucional", salida["mapProvider"]["id"])
    # Y en cualquier combinacion de los tres lados.
    for prov, vista, corrida in ((" mapa-institucional ", "mapa-institucional",
                                  "mapa-institucional"),
                                 ("mapa-institucional", " mapa-institucional ",
                                  "mapa-institucional"),
                                 ("mapa-institucional", "mapa-institucional",
                                  " mapa-institucional ")):
        mezcla = _caso(mapProvider=dict(PROVEEDOR, id=prov),
                       resultados=[_res(proveedor=vista, refs=("e-1",))],
                       evidencia=[_ev(proveedor=corrida)])
        t.igual("E-18 coherente con blancos en un lado pasa", "PASS",
                CHECK.evaluar(mezcla, _senal("TRUE"))["state"])


def test_e19_un_mapa_alterno_falla(t):
    """E-19 (D6-15) — otro proveedor en un camino gobernado es FAIL."""
    alterno = _caso(resultados=[_res(proveedor="otro-mapa")])
    salida = CHECK.evaluar(alterno, _senal("TRUE"))
    t.igual("E-19 el estado", "FAIL", salida["state"])
    t.igual("E-19 con el motivo", "ALTERNATE_MAP_PROVIDER", salida["reason"])
    t.verdadero("E-19 no pasa", not CHECK.aprueba(salida))

    # 🔴 Y falla igual si la corrida dice una cosa y la vista otra: manda la corrida.
    miente = _caso(resultados=[_res(proveedor="mapa-institucional")],
                   evidencia=[_ev(proveedor="otro-mapa")])
    salida = CHECK.evaluar(miente, _senal("TRUE"))
    t.igual("E-19 la corrida manda sobre lo declarado", "FAIL", salida["state"])

    # Y una vista que no dice con que se dibuja no se verifica: no pasa.
    muda = _caso(resultados=[_res(proveedor="")])
    salida = CHECK.evaluar(muda, _senal("TRUE"))
    t.igual("E-19 sin proveedor declarado queda PARTIAL", "PARTIAL", salida["state"])
    t.igual("E-19 con su motivo", "VIEW_PROVIDER_UNDECLARED", salida["reason"])
    t.igual("E-19 un espacio no es un proveedor declarado", "PARTIAL",
            CHECK.evaluar(_caso(resultados=[_res(proveedor=" ")]), _senal("TRUE"))["state"])

    # 🔴 Y la CORRIDA tambien tiene que decir con que dibujo. La primera version se salteaba la
    # comparacion cuando el campo venia vacio, asi que un PASS podia apoyarse en una corrida que
    # nunca dijo con que mapa se habia dibujado — al lado de E-22, que si exige declarar el modo.
    corrida_muda = _caso(evidencia=[_ev(proveedor="")])
    salida = CHECK.evaluar(corrida_muda, _senal("TRUE"))
    t.igual("E-19 una corrida muda no prueba", "PARTIAL", salida["state"])
    t.igual("E-19 con su motivo", "RUN_PROVIDER_UNDECLARED", salida["reason"])
    t.igual("E-19 un espacio tampoco", "PARTIAL",
            CHECK.evaluar(_caso(evidencia=[_ev(proveedor=" ")]), _senal("TRUE"))["state"])

    # 🔴 Y el bypass se ve aunque el id de la vista venga con blancos, de cualquiera de los dos
    # lados. Una version anterior normalizaba `ids` y no las claves del cruce, asi que el
    # resultado se caia por el agujero del medio: no entraba como vista gobernada ni como de
    # afuera, y un bypass probado se informaba como GOVERNED_VIEW_NOT_EXECUTED — un estado que
    # avisaba se convirtio en uno que callaba.
    for inventario, resultado in ((" v-vieja ", "v-vieja"), ("v-vieja", " v-vieja "),
                                  (" v-vieja ", " v-vieja ")):
        cruzado = _caso(vistas=[{"id": inventario}],
                        resultados=[_res(resultado, proveedor="otro-mapa", refs=("e-1",))],
                        evidencia=[_ev(proveedor="otro-mapa")])
        salida = CHECK.evaluar(cruzado, _senal("TRUE"))
        t.igual("E-19 con id %r/%r el bypass falla" % (inventario, resultado), "FAIL",
                salida["state"])
        t.igual("E-19 y dice que es un proveedor alterno", "ALTERNATE_MAP_PROVIDER",
                salida["reason"])
        t.verdadero("E-19 y el rastro queda",
                    "otro-mapa" in repr(salida))


def test_e20_una_vista_que_cumple_no_tapa_otra(t):
    """E-20 (D6-16) — un FAIL manda sobre cualquier cantidad de vistas que pasen."""
    mixto = _caso(
        vistas=[{"id": "v-mapa"}, {"id": "v-vieja"}],
        resultados=[_res("v-mapa", refs=("e-1",)),
                    _res("v-vieja", proveedor="otro-mapa", refs=("e-2",))],
        evidencia=[_ev("e-1"), _ev("e-2", proveedor="otro-mapa")])
    salida = CHECK.evaluar(mixto, _senal("TRUE"))
    t.igual("E-20 el estado", "FAIL", salida["state"])
    estados = {v["viewId"]: v["state"] for v in salida["views"]}
    t.igual("E-20 la que cumple cumple", "PASS", estados["v-mapa"])
    t.igual("E-20 y la que no, no", "FAIL", estados["v-vieja"])

    # Nueve vistas bien y una mal siguen siendo FAIL.
    muchas = _caso(
        vistas=[{"id": "v-%d" % i} for i in range(10)],
        resultados=[_res("v-%d" % i, refs=("e-%d" % i,)) for i in range(9)] +
                   [_res("v-9", proveedor="otro-mapa", refs=("e-9",))],
        evidencia=[_ev("e-%d" % i) for i in range(9)] +
                  [_ev("e-9", proveedor="otro-mapa")])
    t.igual("E-20 nueve bien y una mal es FAIL", "FAIL",
            CHECK.evaluar(muchas, _senal("TRUE"))["state"])

    # 🔴 Y una vista fuera del inventario dibujando con otro proveedor no deja PASS: o falta una
    # vista gobernada, o esa vista no lo esta y nadie lo dijo.
    oculta = _caso(resultados=[_res(), _res("v-oculta", proveedor="otro-mapa", refs=())])
    salida = CHECK.evaluar(oculta, _senal("TRUE"))
    t.igual("E-20 la de afuera no queda tapada", "MAP_VIEW_COVERAGE_UNRESOLVED",
            salida["state"])
    t.igual("E-20 y se nombra", ["v-oculta"], salida["ignoredResults"])
    t.verdadero("E-20 con su aviso",
                any("v-oculta" in i for i in salida["issues"]))

    # 🔴 Y tampoco dejando el campo vacio. La primera version miraba solo `provider` del
    # resultado, asi que una vista de afuera con el campo en blanco y una corrida REAL que
    # reportaba otro mapa terminaba en PASS, sin un solo aviso: la doctrina de E-19 —la corrida
    # manda sobre lo declarado— valia unicamente para las vistas gobernadas.
    muda_afuera = _caso(
        resultados=[_res(refs=("e-1",)),
                    {"viewId": "v-oculta", "provider": "", "evidenceRefs": ["e-2"]}],
        evidencia=[_ev("e-1"), _ev("e-2", proveedor="otro-mapa")])
    salida = CHECK.evaluar(muda_afuera, _senal("TRUE"))
    t.igual("E-20 la corrida delata a la vista de afuera", "MAP_VIEW_COVERAGE_UNRESOLVED",
            salida["state"])
    t.verdadero("E-20 y no aprueba", not CHECK.aprueba(salida))
    t.verdadero("E-20 con su aviso nombrado", any("v-oculta" in i for i in salida["issues"]))
    t.verdadero("E-20 la corrida de afuera se lee",
                "otro-mapa" in CHECK._proveedores_de_la_corrida(
                    {"evidenceRefs": ["e-2"]},
                    {"e-2": _ev("e-2", proveedor="otro-mapa")}, BUILD))

    # Una vista de afuera sin proveedor y sin evidencia no prueba nada: ahi no hay
    # incumplimiento, y queda como resultado ignorado.
    sin_nada = _caso(resultados=[_res(),
                                 {"viewId": "v-suelta", "provider": "", "evidenceRefs": []}])
    salida = CHECK.evaluar(sin_nada, _senal("TRUE"))
    t.igual("E-20 una de afuera sin nada no inventa un incumplimiento", "PASS",
            salida["state"])
    t.igual("E-20 pero queda anotada", ["v-suelta"], salida["ignoredResults"])

    # Dos resultados para la misma vista con proveedores distintos: falla.
    doble = _caso(resultados=[_res(refs=("e-1",)),
                              _res(proveedor="otro-mapa", refs=("e-2",))],
                  evidencia=[_ev("e-1"), _ev("e-2", proveedor="otro-mapa")])
    t.igual("E-20 dos resultados de la misma vista en conflicto fallan", "FAIL",
            CHECK.evaluar(doble, _senal("TRUE"))["state"])

    # 🔴 Y una etiqueta en la vista no la saca de la regla. Una version anterior aceptaba
    # `materiality: MINOR` y la excluia de la verificacion: la vista incumplidora daba PASS y no
    # aparecia en ningun campo de la salida.
    etiquetada = _caso(
        vistas=[{"id": "v-mapa"}, {"id": "v-chica", "materiality": "MINOR"}],
        resultados=[_res("v-mapa", refs=("e-1",)),
                    _res("v-chica", proveedor="otro-mapa", refs=("e-2",))],
        evidencia=[_ev("e-1"), _ev("e-2", proveedor="otro-mapa")])
    salida = CHECK.evaluar(etiquetada, _senal("TRUE"))
    t.igual("E-20 una etiqueta no esconde el bypass", "FAIL", salida["state"])
    t.verdadero("E-20 y la vista aparece en la salida",
                "v-chica" in [v["viewId"] for v in salida["views"]])


def test_e21_la_cobertura_incompleta_no_pasa(t):
    """E-21 (D6-17) — sin inventario, sin resolver; enumerada y sin correr, PARTIAL."""
    sin_inventario = dict(_caso())
    del sin_inventario["mapViews"]
    for nombre, caso in (("sin bloque", sin_inventario),
                         ("bloque vacio", _caso(mapViews={})),
                         ("sin vistas", _caso(mapViews={"source": "ROUTE_INVENTORY",
                                                        "views": []})),
                         ("sin fuente", _caso(mapViews={"views": [{"id": "v-mapa"}]})),
                         ("fuente inventada", _caso(mapViews={"source": "ME_PARECE",
                                                              "views": [{"id": "v-mapa"}]})),
                         ("vista sin id", _caso(mapViews={"source": "ROUTE_INVENTORY",
                                                          "views": [{"label": "mapa"}]}))):
        salida = CHECK.evaluar(caso, _senal("TRUE"))
        t.igual("E-21 %s da MAP_VIEW_COVERAGE_UNRESOLVED" % nombre,
                "MAP_VIEW_COVERAGE_UNRESOLVED", salida["state"])
        t.verdadero("E-21 %s no pasa" % nombre, not CHECK.aprueba(salida))

    # Enumerada y sin ningun resultado: PARTIAL, no PASS por lo que corrio el resto.
    incompleta = _caso(vistas=[{"id": "v-mapa"}, {"id": "v-nueva"}])
    salida = CHECK.evaluar(incompleta, _senal("TRUE"))
    t.igual("E-21 una vista sin resultado deja PARTIAL", "PARTIAL", salida["state"])
    t.igual("E-21 con su motivo", "GOVERNED_VIEW_NOT_EXECUTED", salida["reason"])
    t.igual("E-21 y las dos se contaron", 2, len(salida["views"]))

    # 🔴 El inventario ES la lista de vistas materiales: no hay un segundo filtro por vista.
    # Una version anterior aceptaba `materiality: MINOR` y sacaba esa vista de la verificacion,
    # asi que una vista marcada menor dibujando con otro mapa daba PASS y no aparecia en ningun
    # campo de la salida. Un campo que nadie exige respaldar no puede sacar a una vista de la
    # regla; la materialidad se decide al armar el inventario, que si tiene que declarar su
    # fuente.
    con_etiqueta = _caso(vistas=[{"id": "v-mapa"}, {"id": "v-chica", "materiality": "MINOR"}])
    t.igual("E-21 una vista etiquetada menor entra igual como gobernada",
            ["v-mapa", "v-chica"], CHECK.evaluar(con_etiqueta, _senal("TRUE"))["governedViews"])
    t.igual("E-21 y sin resultado deja PARTIAL", "PARTIAL",
            CHECK.evaluar(con_etiqueta, _senal("TRUE"))["state"])
    t.igual("E-21 gobernadas() no filtra nada del inventario", 2,
            len(CHECK.gobernadas(con_etiqueta)))
    # Y si esa vista dibuja con otro mapa, falla: no se esconde.
    escondida = _caso(
        vistas=[{"id": "v-mapa"}, {"id": "v-chica", "materiality": "MINOR"}],
        resultados=[_res("v-mapa", refs=("e-1",)),
                    _res("v-chica", proveedor="otro-mapa", refs=("e-2",))],
        evidencia=[_ev("e-1"), _ev("e-2", proveedor="otro-mapa")])
    t.igual("E-21 una vista menor no esconde un incumplimiento", "FAIL",
            CHECK.evaluar(escondida, _senal("TRUE"))["state"])
    t.verdadero("E-21 y aparece en la salida",
                "v-chica" in [v["viewId"] for v in
                              CHECK.evaluar(escondida, _senal("TRUE"))["views"]])


def test_e22_lo_mockeado_no_prueba(t):
    """E-22 (D6-18) — se distingue de lo real y no llega a PASS."""
    mockeado = _caso(evidencia=[_ev(modo="MOCKED")])
    salida = CHECK.evaluar(mockeado, _senal("TRUE"))
    t.igual("E-22 el estado", "PARTIAL", salida["state"])
    t.igual("E-22 con el motivo", "MOCKED_EVIDENCE_ONLY", salida["reason"])
    t.verdadero("E-22 no pasa", not CHECK.aprueba(salida))

    # Mockeado mas real si pasa: lo mockeado acompana.
    los_dos = _caso(resultados=[_res(refs=("e-1", "e-2"))],
                    evidencia=[_ev("e-1", modo="MOCKED"), _ev("e-2", modo="REAL")])
    t.igual("E-22 con una real al lado pasa", "PASS",
            CHECK.evaluar(los_dos, _senal("TRUE"))["state"])

    # Sin modo declarado tampoco alcanza: lo que no se dice no se asume real.
    sin_modo = _caso(evidencia=[dict(_ev(), mode=None)])
    t.igual("E-22 sin modo declarado no pasa", "PARTIAL",
            CHECK.evaluar(sin_modo, _senal("TRUE"))["state"])
    t.igual("E-22 los modos son dos", ("REAL", "MOCKED"), CHECK.MODOS)

    # Y una corrida de otro build no cuenta, mockeada o no.
    ajena = _caso(evidencia=[_ev(buildId="b-vieja")])
    salida = CHECK.evaluar(ajena, _senal("TRUE"))
    t.igual("E-22 otra corrida no cuenta", "PARTIAL", salida["state"])
    t.verdadero("E-22 y se dice", any("EVIDENCE_OUT_OF_BUILD" in i for i in salida["issues"]))


def test_e23_sin_donde_correr_no_pasa(t):
    """E-23 — TEST_TARGET_UNAVAILABLE."""
    salida = CHECK.evaluar(_caso(testTarget={"available": False}), _senal("TRUE"))
    t.igual("E-23 el estado", "TEST_TARGET_UNAVAILABLE", salida["state"])
    t.verdadero("E-23 no pasa", not CHECK.aprueba(salida))
    t.igual("E-23 sin bloque tampoco", "TEST_TARGET_UNAVAILABLE",
            CHECK.evaluar(_caso(testTarget={}), _senal("TRUE"))["state"])
    # 🔴 Y se decide antes de mirar el proveedor: sin donde correr, el resto no importa.
    t.igual("E-23 antes que el proveedor", "TEST_TARGET_UNAVAILABLE",
            CHECK.evaluar(_caso(testTarget={"available": False}, mapProvider={}),
                          _senal("TRUE"))["state"])


def test_e24_solo_pass_aprueba(t):
    """E-24 (§9) — nueve estados, uno solo aprueba."""
    t.igual("E-24 son nueve", 9, len(CHECK.ESTADOS))
    for estado in CHECK.ESTADOS:
        t.igual("E-24 %s" % estado, str(estado == "PASS"),
                str(CHECK.aprueba({"state": estado})))
    esperados = ("PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                 "MAP_VIEW_COVERAGE_UNRESOLVED", "GCBA_MAP_PROVIDER_UNRESOLVED",
                 "MAP_INTEGRATION_CONTRACT_MISSING", "TEST_TARGET_UNAVAILABLE")
    t.igual("E-24 y son los que el pedido pide", sorted(esperados), sorted(CHECK.ESTADOS))


# -- E-25 y E-26 — la frontera con D5 ------------------------------------------

def test_e25_d6_no_afirma_nada_de_d5(t):
    """E-25 (D6-19) — dos reglas del mismo parrafo, y ninguna contesta por la otra."""
    # 🔴 Sobre los NUEVE caminos, no sobre uno. Un solo resultado limpio no dice que el modulo
    # no pueda hablar de D5: lo dice que ninguno de sus caminos lo haga.
    AJENOS = ("D5", "address-normalization-integration",
              "gcba-cadastral-address-normalization-required",
              "frontendAddressInputPresent", "normaliz", "catastral")
    for esperado, (caso, senal) in sorted(_los_nueve_caminos().items()):
        salida = CHECK.evaluar(caso, senal)
        t.igual("E-25 %s se alcanza" % esperado, esperado, salida["state"])
        t.igual("E-25 %s lleva la traza de D6" % esperado, TRAZA, salida["source"])
        texto = repr(salida)
        for ajeno in AJENOS:
            t.verdadero("E-25 %s no habla de %s" % (esperado, ajeno), ajeno not in texto)

    # 📌 `API GEO` queda afuera de la lista a proposito: el camino de
    # RENDERED_EVIDENCE_MISSING dice que una llamada a API GEO no alcanza, y decir que no
    # alcanza ES la separacion, no su perdida. Se afirma en verde para que quede dicho.
    detalle = repr(CHECK.evaluar(_con_evidencia_sola("GEO_API_CALL"), _senal("TRUE")))
    t.contiene("E-25 el check nombra API GEO para decir que no alcanza", "API GEO", detalle)
    for ajeno in AJENOS:
        t.verdadero("E-25 y ahi tampoco habla de %s" % ajeno, ajeno not in detalle)

    # Resolver D6 no cambia la aplicabilidad de D5.
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-25 D6 aplica", "D6" in bloque["applicableRules"])
    t.verdadero("E-25 y D5 no", "D5" not in bloque["applicableRules"])
    t.verdadero("E-25 D5 queda sin resolver",
                "D5" in {u["rule"] for u in bloque["unresolvedRules"]})
    t.verdadero("E-25 sin exigir la policy de D5",
                "gcba-cadastral-address-normalization-required"
                not in bloque["declaredPolicies"])

    # Y al revés: las dos senales en TRUE dan las dos reglas, cada una con lo suyo.
    dos = c_normativa.resolucion(
        {SENAL: _senal("TRUE"),
         "frontendAddressInputPresent": _senal("TRUE", sid="frontendAddressInputPresent")})
    t.verdadero("E-25 las dos aplican", {"D5", "D6"} <= set(dos["applicableRules"]))
    t.verdadero("E-25 cada una con su policy",
                POLICY in dos["declaredPolicies"]
                and "gcba-cadastral-address-normalization-required"
                in dos["declaredPolicies"])


def test_e26_d5_esta_instalado_y_d6_no_cambio(t):
    """E-26 — la proposicion sucesora: el hueco de D5 se cerro y esto no se movio.

    🔴 Este test afirmaba en verde que los dos controles de D5 NO estaban en el registro, y estaba
    escrito asi a proposito: instalar D5 lo ponia en rojo. D5 se instalo -ver
    docs/cambios/d5-normalizacion-catastral-de-direcciones/spec.md-, asi que la proposicion se
    reescribio a la que la sigue. Lo que E-26 cuidaba era LA FRONTERA, y la frontera sigue viva:
    los dos controles de D5 existen, y el resultado de D6 no dice una palabra sobre ellos.
    """
    informe = c_controles.validar()
    instalados = c_controles.instalados()
    t.vacio("E-26 el registro no tiene errores de schema", informe["schemaErrors"])

    d5 = c_controles.de_la_regla("D5")
    t.igual("E-26 D5 tiene sus dos controles en el registro", 2, len(d5))
    for control, tipo in (("gcba-cadastral-address-normalization-required", "POLICY"),
                          ("address-normalization-integration", "CHECK")):
        t.verdadero("E-26 %s esta instalado" % control, control in instalados[tipo])
        declarado = c_controles.control(control)
        t.igual("E-26 %s es de D5" % control, "D5", declarado["rule"])
        t.igual("E-26 %s es del tipo que dice" % control, tipo, declarado["type"])

    # La matriz los declaraba desde el principio, y su fila no cambio al instalarlos.
    d5_matriz = c_matriz.regla("D5")
    t.igual("E-26 la matriz declara su policy",
            ["gcba-cadastral-address-normalization-required"], d5_matriz["policies"])
    t.igual("E-26 y su check", ["address-normalization-integration"], d5_matriz["checks"])
    t.igual("E-26 y sigue CLASSIFIED", "CLASSIFIED", d5_matriz["status"])

    faltantes = c_matriz.controles_no_instalados(
        c_normativa.resolucion({SENAL: _senal("TRUE"),
                                "frontendAddressInputPresent": _senal(
                                    "TRUE", sid="frontendAddressInputPresent")}))
    huecos = {h["id"]: h["state"] for h in faltantes}
    for control in d5_matriz["policies"] + d5_matriz["checks"]:
        t.verdadero("E-26 %s ya no es un hueco" % control, control not in huecos)
    t.verdadero("E-26 la policy de D6 tampoco", POLICY not in huecos)
    t.verdadero("E-26 ni su check", CHEQUEO not in huecos)

    # 🔴 Y la frontera: instalar D5 no le cambio una coma al resultado de D6, en ningun camino.
    for esperado, (caso, senal) in sorted(_los_nueve_caminos().items()):
        texto = repr(CHECK.evaluar(caso, senal))
        for ajeno in d5_matriz["policies"] + d5_matriz["checks"] + ["D5"]:
            t.verdadero("E-26 el camino %s no habla de %s" % (esperado, ajeno),
                        ajeno not in texto)


# -- E-27 y E-28 — las skills y el ruteo ---------------------------------------

def test_e27_d6_no_crea_ni_declara_una_skill(t):
    """E-27 (D6-20) — y lo que se afirma es lo que se puede medir.

    🔴 La version anterior decia "las 27 quedan identicas" y lo unico que medía era el conteo.
    Un conteo ve un alta o una baja; no ve una modificacion, y ningun test de este repositorio
    puede afirmar que un archivo no cambio nunca — las skills evolucionan por motivos que no
    tienen nada que ver con D6. Asi que el escenario afirma cuatro cosas medibles, y las cuatro
    estan medidas.
    """
    instaladas = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
    # Si alguien agrega o saca una skill, esto se pone en rojo y obliga a mirar si fue D6.
    t.igual("E-27 siguen siendo 27 skills", 27, len(instaladas))
    t.vacio("E-27 y ninguna es de mapas",
            [s for s in instaladas if "map" in s or "geo" in s])
    t.verdadero("E-27 la skill que D6 pediria no existe",
                not (SKILLS / CHECK.SKILL_DE_MAPA).exists())
    t.verdadero("E-27 y el registro de agentes no la declara",
                not c_reg.hay_skill(CHECK.AGENTE_DE_INTEGRACION, CHECK.SKILL_DE_MAPA))

    artefactos = {"la policy": (CONTROLES / "policies" / (POLICY + ".md")).read_text(
                      encoding="utf-8"),
                  "el check": (CONTROLES / "checks" / (CHEQUEO + ".py")).read_text(
                      encoding="utf-8")}
    for nombre, texto in sorted(artefactos.items()):
        # Una declaracion, no la palabra: `skills` al principio de una linea es lo que daria de
        # alta una skill. En una frase, es prosa.
        t.vacio("E-27 %s no declara una skill" % nombre,
                re.findall(r"(?m)^\s*skills\s*:", texto))
        t.verdadero("E-27 %s no trae un SKILL.md" % nombre, "SKILL.md" not in texto)

    # 🔴 Y las unicas skills que los artefactos nombran son las que se resuelven por el
    # registro. Cualquier otra skill instalada nombrada en un artefacto de D6 seria una opinion
    # de D6 sobre una skill, que es lo que "no modifica ninguna" quiere decir en la practica.
    por_el_registro = {s["requestedSkill"] for s in CHECK.skills_de_ejecucion()}
    por_el_registro.add(CHECK.SKILL_DE_MAPA)
    for nombre, texto in sorted(artefactos.items()):
        nombradas = {s for s in instaladas if s in texto}
        t.vacio("E-27 %s no nombra ninguna skill fuera del registro" % nombre,
                sorted(nombradas - por_el_registro))
    t.igual("E-27 las que se resuelven por el registro son cuatro", 4, len(por_el_registro))
    t.verdadero("E-27 tres instaladas y una que falta",
                len([s for s in por_el_registro if (SKILLS / s).exists()]) == 3)

    # Y el check no trae automatizacion propia.
    fuente = artefactos["el check"]
    for libreria in ("playwright", "selenium", "puppeteer", "webdriver", "requests",
                     "urllib", "subprocess"):
        t.verdadero("E-27 el check no importa %s" % libreria,
                    ("import %s" % libreria) not in fuente
                    and ("from %s" % libreria) not in fuente)


def test_e28_el_hueco_se_declara_y_no_se_llena(t):
    """E-28 — la remediacion rutea por el registro y no inventa la skill."""
    for estado_previo in ("FAIL", "PARTIAL", "GCBA_MAP_PROVIDER_UNRESOLVED",
                          "MAP_INTEGRATION_CONTRACT_MISSING"):
        rem = CHECK.remediacion({"state": estado_previo})
        t.verdadero("E-28 %s pide remediacion" % estado_previo, rem is not None)
        t.igual("E-28 %s con el estado que ya existia" % estado_previo,
                "SPECIALIZED_SKILL_GAP", rem["state"])
        t.verdadero("E-28 %s y no hace cumplir a D6" % estado_previo, not rem["compliant"])
        t.igual("E-28 %s la traza sigue siendo de D6" % estado_previo, TRAZA, rem["source"])

    for estado_previo in ("PASS", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED"):
        t.igual("E-28 %s no pide remediacion" % estado_previo, None,
                CHECK.remediacion({"state": estado_previo}))

    rem = CHECK.remediacion({"state": "FAIL"})
    t.igual("E-28 nombra al agente", "dev-integration", rem["agent"])
    t.verdadero("E-28 y dice que le pasa a la skill", bool(rem["skillValidation"]))
    # 🔴 El estado sale del registro, no de una constante del check: es exactamente lo que
    # `resolver_ruteo` contesta hoy, y el dia que la skill se instale cambia sin tocar D6.
    t.igual("E-28 el estado es el que contesta el registro",
            c_reg.resolver_ruteo(CHECK.AGENTE_DE_INTEGRACION, CHECK.SKILL_DE_MAPA)["result"],
            rem["skillValidation"])

    # Las skills de ejecucion son las instaladas y se rutean.
    skills = CHECK.skills_de_ejecucion()
    t.igual("E-28 son tres", 3, len(skills))
    for s in skills:
        t.igual("E-28 %s se rutea" % s["requestedSkill"], "ROUTABLE", s["result"])
        t.verdadero("E-28 %s existe de verdad" % s["requestedSkill"],
                    (SKILLS / s["requestedSkill"] / "SKILL.md").is_file())
        t.igual("E-28 %s se pidio para este control" % s["requestedSkill"], CHEQUEO,
                s["requestedFor"])


# -- E-29 a E-31 — la propagacion, el registro y la trazabilidad ---------------

def test_e29_la_unidad_propaga_senal_policy_y_check(t):
    """E-29 (D6-21) — y la forma vieja, con booleanos, sigue funcionando."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-29 la regla viaja", "D6" in bloque["applicableRules"])
    t.verdadero("E-29 la policy viaja", POLICY in bloque["declaredPolicies"])
    t.verdadero("E-29 el check viaja", CHEQUEO in bloque["declaredChecks"])
    t.verdadero("E-29 y la senal resuelta con su evidencia", bool(
        bloque["signals"][SENAL]["evidence"]))
    t.igual("E-29 con su valor", "TRUE", bloque["signals"][SENAL]["value"])

    # La forma vieja: un booleano suelto.
    viejo = c_normativa.resolucion({SENAL: True})
    t.verdadero("E-29 un booleano en TRUE sigue haciendo aplicar a D6",
                "D6" in viejo["applicableRules"])
    t.verdadero("E-29 con su policy", POLICY in viejo["declaredPolicies"])
    falso = c_normativa.resolucion({SENAL: False})
    t.verdadero("E-29 y en FALSE la deja afuera", "D6" in falso["notApplicableRules"])


def test_e30_los_controles_dejan_de_ser_un_hueco(t):
    """E-30 (D6-22) — instalados, declarados, y sin archivos sueltos."""
    reporte = c_controles.reporte()
    # 📌 Eran dieciseis cuando D6 cerro; D5 sumo dos y D7 sumo seis. El numero va exacto a
    # proposito: una banda floja deja pasar la regla que se instala sin tocar este test.
    t.igual("E-30 son cincuenta y dos controles", 52, reporte["summary"]["declaredControls"])
    t.verdadero("E-30 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-30 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-30 ningun archivo suelto", [], reporte["undeclared"])

    for control, tipo in ((POLICY, "POLICY"), (CHEQUEO, "CHECK")):
        t.igual("E-30 %s esta INSTALLED" % control, "INSTALLED",
                reporte["controls"][control])
        declarado = c_controles.control(control)
        t.igual("E-30 %s es del tipo que dice" % control, tipo, declarado["type"])
        t.igual("E-30 %s es de D6" % control, "D6", declarado["rule"])
        t.igual("E-30 %s trae su traza" % control, TRAZA, declarado["source"])
        t.verdadero("E-30 %s esta entre los instalados" % control,
                    control in c_controles.instalados()[tipo])

    t.igual("E-30 D6 tiene dos controles", 2, len(c_controles.de_la_regla("D6")))


def test_e31_todo_resultado_conserva_la_traza(t):
    """E-31 (D6-23) — ES0901 / 6.3 / 7.1 / D6, en los nueve caminos."""
    caminos = _los_nueve_caminos()
    t.igual("E-31 se recorren los nueve estados", 9, len(caminos))
    t.igual("E-31 y son los nueve que el modulo declara", sorted(CHECK.ESTADOS),
            sorted(caminos))
    for esperado, (caso, senal) in caminos.items():
        salida = CHECK.evaluar(caso, senal)
        t.igual("E-31 %s se alcanza" % esperado, esperado, salida["state"])
        t.igual("E-31 %s conserva la traza" % esperado, TRAZA, salida["source"])
        t.igual("E-31 %s nombra su control" % esperado, CHEQUEO, salida["control"])
        t.igual("E-31 %s nombra su senal" % esperado, SENAL, salida["signal"])

    t.igual("E-31 el modulo declara la regla", "D6", CHECK.REGLA)
    t.igual("E-31 y su tipo", "CHECK", CHECK.TIPO)
    t.igual("E-31 la fila citable existe", "D6", c_matriz.regla("D6")["id"])
