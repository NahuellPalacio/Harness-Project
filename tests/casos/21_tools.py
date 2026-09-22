# El contrato de una tool y el Tool Registry.
#
# Escenarios del evolutivo de dev-tool-builder, spec en docs/cambios/tool-builder/spec.md.
# Esta tanda cubre el contrato y el registro: E-01 a E-11, E-17 a E-31. Las compuertas
# (E-12 a E-16), la traza (E-32), los limites (E-33 a E-35) y el agente (E-36, E-37) son de
# las tandas siguientes.
import io
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from orquestacion import registro_tools as c_reg   # noqa: E402
from orquestacion import tools as c_tools          # noqa: E402


def _contrato(**extra):
    c = {
        "name": "repository-structure-inspector",
        "version": "1.0.0",
        "capabilities": ["repository.read"],
        "inputs": {"repositoryContext": "required"},
        "outputs": {"structuredModuleMap": "required"},
        "sideEffects": "READ_ONLY",
        "permissions": ["repository.read"],
        "secretsRequired": [],
        "networkAccess": False,
        "timeoutSeconds": 30,
        "idempotent": True,
        "retryPolicy": {"enabled": False},
        "riskLevel": "LOW",
        "blastRadius": {"scope": "repository", "environments": ["local"],
                        "productionImpact": False},
    }
    c.update(extra)
    return c


def _validaciones(**extra):
    # sandbox NOT_RUN es el estado real de hoy: no hay entorno aislado en el harness.
    v = {"static": "PASS", "unit": "PASS", "contract": "PASS", "security": "PASS",
         "sandbox": "NOT_RUN", "capability": "PASS"}
    v.update(extra)
    return v


def _evidencia(**extra):
    e = dict((k, True) for k in c_tools.EVIDENCIA_PARA_PROMOVER)
    e.update(extra)
    return e


def _entrada(nombre="ya-registrada", version="1.0.0", lifecycle="TEMPORARY",
             capacidades=("repository.structure.inspect",)):
    return {
        "name": nombre, "version": version, "lifecycle": lifecycle,
        "capabilities": list(capacidades), "sideEffects": "READ_ONLY", "riskLevel": "LOW",
        "permissions": ["repository.read"], "secretsRequired": [],
        "blastRadius": {"scope": "repository", "environments": ["local"],
                        "productionImpact": False},
        "validations": _validaciones(), "contractHash": "sha256:" + "0" * 64,
    }


def _registro(entradas=()):
    doc = c_reg.vacio()
    doc["tools"] = [dict(e) for e in entradas]
    return doc


# -- E-01 a E-04 — el contrato antes que el codigo -----------------------------

def test_e01_sin_contrato_valido_no_se_registra(t):
    """E-01 — una tool sin contrato valido no se registra y el registro queda igual."""
    doc = _registro()
    antes = json.dumps(doc, sort_keys=True)
    contrato = _contrato()
    del contrato["timeoutSeconds"]
    levanto = ""
    try:
        c_reg.registrar(doc, contrato, _validaciones())
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.verdadero("E-01 levanto", bool(levanto))
    t.igual("E-01 el registro no cambio", antes, json.dumps(doc, sort_keys=True))
    t.igual("E-01 no entro ninguna tool", 0, len(doc["tools"]))


def test_e02_falta_un_campo_obligatorio(t):
    """E-02 — CONTRACT_INVALID y el mensaje nombra el campo que falta."""
    contrato = _contrato()
    del contrato["timeoutSeconds"]
    veredicto = c_tools.evaluar(contrato)
    t.igual("E-02 el estado", "CONTRACT_INVALID", veredicto["status"])
    t.contiene("E-02 nombra el campo", "timeoutSeconds", " ".join(veredicto["errors"]))


def test_e03_side_effects_fuera_del_vocabulario(t):
    """E-03 — sideEffects fuera de READ_ONLY/MUTATING/DESTRUCTIVE es contrato invalido."""
    veredicto = c_tools.evaluar(_contrato(sideEffects="MAYBE"))
    t.igual("E-03 el estado", "CONTRACT_INVALID", veredicto["status"])
    t.contiene("E-03 nombra el campo", "sideEffects", " ".join(veredicto["errors"]))


def test_e04_nivel_de_riesgo_fuera_del_vocabulario(t):
    """E-04 — riskLevel fuera de LOW/MEDIUM/HIGH/CRITICAL es contrato invalido."""
    veredicto = c_tools.evaluar(_contrato(riskLevel="EXTREME"))
    t.igual("E-04 el estado", "CONTRACT_INVALID", veredicto["status"])
    t.contiene("E-04 nombra el campo", "riskLevel", " ".join(veredicto["errors"]))


# -- E-05 a E-09 — el riesgo sale del contrato ---------------------------------

def test_e05_solo_lectura_local_es_bajo(t):
    """E-05 — READ_ONLY, sin red, sin secrets y con alcance repositorio deriva LOW."""
    t.igual("E-05 deriva LOW", "LOW", c_tools.derivar_riesgo(_contrato()))


def test_e06_salir_a_la_red_no_puede_quedar_bajo(t):
    """E-06 — el mismo contrato con networkAccess no puede quedar LOW."""
    riesgo = c_tools.derivar_riesgo(_contrato(networkAccess=True))
    t.verdadero("E-06 no es LOW", riesgo != "LOW")
    t.igual("E-06 deriva MEDIUM", "MEDIUM", riesgo)


def test_e07_destructivo_o_produccion_es_critico(t):
    """E-07 — DESTRUCTIVE, o mutar con impacto en produccion, deriva CRITICAL."""
    t.igual("E-07 destructivo", "CRITICAL",
            c_tools.derivar_riesgo(_contrato(sideEffects="DESTRUCTIVE")))
    en_produccion = _contrato(
        sideEffects="MUTATING",
        blastRadius={"scope": "external-system", "environments": ["production"],
                     "productionImpact": True})
    t.igual("E-07 mutando en produccion", "CRITICAL", c_tools.derivar_riesgo(en_produccion))
    # Y leer produccion sin mutarla no es lo mismo: es alto, no critico.
    solo_lee = _contrato(
        blastRadius={"scope": "external-system", "environments": ["production"],
                     "productionImpact": True})
    t.igual("E-07 leyendo produccion", "HIGH", c_tools.derivar_riesgo(solo_lee))


def test_e08_declarar_menos_riesgo_del_derivado_se_rechaza(t):
    """E-08 — el declarado por debajo del derivado se rechaza; por encima se respeta."""
    bajo = _contrato(networkAccess=True, riskLevel="LOW")
    veredicto = c_tools.evaluar(bajo)
    t.igual("E-08 se rechaza", "CONTRACT_INVALID", veredicto["status"])
    mensaje = " ".join(veredicto["errors"])
    t.contiene("E-08 muestra el declarado", "LOW", mensaje)
    t.contiene("E-08 y el derivado", "MEDIUM", mensaje)

    alto = _contrato(riskLevel="HIGH")
    t.igual("E-08 declarar de mas se acepta", "OK", c_tools.evaluar(alto)["status"])
    t.igual("E-08 y no se baja solo", "HIGH", alto["riskLevel"])


def test_e09_el_tier_de_modelo_no_entra_en_el_riesgo(t):
    """E-09 — el mismo contrato bajo low_cost y bajo premium da el mismo riskLevel."""
    barato = _contrato(modelTier="low_cost")
    caro = _contrato(modelTier="premium")
    t.igual("E-09 mismo riesgo", c_tools.derivar_riesgo(barato), c_tools.derivar_riesgo(caro))
    t.igual("E-09 y es el del contrato", "LOW", c_tools.derivar_riesgo(caro))


# -- E-10 y E-11 — least privilege ---------------------------------------------

def test_e10_permiso_que_la_capacidad_no_necesita(t):
    """E-10 — PERMISSION_SCOPE_TOO_BROAD y el mensaje nombra el permiso sobrante."""
    contrato = _contrato(permissions=["repository.read", "repository.write"])
    veredicto = c_tools.evaluar(contrato)
    t.igual("E-10 el estado", "PERMISSION_SCOPE_TOO_BROAD", veredicto["status"])
    t.contiene("E-10 nombra el sobrante", "repository.write", " ".join(veredicto["errors"]))


def test_e11_capacidad_sin_permisos_declarados_es_hueco(t):
    """E-11 — una capacidad que no figura en el mapa no se aprueba ni recibe todo."""
    contrato = _contrato(capabilities=["database.schema.inspect"],
                         permissions=["repository.read"])
    veredicto = c_tools.evaluar(contrato)
    t.igual("E-11 es un hueco, no un permiso", "MISSING_CONTEXT", veredicto["status"])
    t.verdadero("E-11 no queda aprobado", veredicto["status"] != "OK")
    t.contiene("E-11 nombra la capacidad", "database.schema.inspect",
               " ".join(veredicto["errors"]))
    t.igual("E-11 y el mapa no la tiene", None, c_tools.permisos_de("database.schema.inspect"))


# -- E-17 a E-20 — reusar antes que extender, extender antes que crear ---------

def test_e17_la_capacidad_ya_existe(t):
    """E-17 — si el Capability Registry ya la da, no se construye nada."""
    r = c_tools.resolver("repository.read", ["repository.read", "tests.run"], [])
    t.igual("E-17 el estado", "CAPABILITY_ALREADY_EXISTS", r["status"])
    t.igual("E-17 no hay estrategia de construccion", "", r["strategy"])


def test_e18_una_tool_registrada_se_reusa(t):
    """E-18 — si una tool seleccionable ya declara la capacidad, se reusa."""
    r = c_tools.resolver("repository.structure.inspect", [], [_entrada()])
    t.igual("E-18 reusa", "REUSE", r["strategy"])
    t.verdadero("E-18 no crea", r["strategy"] != "CREATE")
    t.igual("E-18 y dice cual", "ya-registrada", r["tool"]["name"])


def test_e19_crear_sin_haber_mirado_no_es_una_decision(t):
    """E-19 — strategy CREATE con alternativesEvaluated vacio es invalido."""
    errores = c_tools.validar_resolucion({"strategy": "CREATE", "alternativesEvaluated": []})
    t.verdadero("E-19 da error", len(errores) > 0)
    t.contiene("E-19 nombra lo que falta evaluar", "reuse", " ".join(errores))
    completa = {"strategy": "CREATE", "alternativesEvaluated": ["reuse", "extend", "create"]}
    t.vacio("E-19 con las alternativas escritas pasa", c_tools.validar_resolucion(completa))


def test_e20_deprecated_y_retired_no_se_eligen(t):
    """E-20 — una tool DEPRECATED o RETIRED no se selecciona para trabajo nuevo."""
    doc = _registro([_entrada(nombre="vieja", lifecycle="DEPRECATED"),
                     _entrada(nombre="muerta", lifecycle="RETIRED")])
    t.vacio("E-20 no hay seleccionables", c_reg.seleccionables(doc))
    t.vacio("E-20 ni para la capacidad",
            c_reg.para_capacidad(doc, "repository.structure.inspect"))
    r = c_tools.resolver("repository.structure.inspect", [], doc["tools"])
    t.igual("E-20 hay que crear", "CREATE", r["strategy"])


# -- E-21 a E-24 — ciclo de vida ------------------------------------------------

def test_e21_una_tool_generada_no_nace_aprobada(t):
    """E-21 — entra EXPERIMENTAL o TEMPORARY aunque todo este en verde."""
    doc = _registro()
    levanto = ""
    try:
        c_reg.registrar(doc, _contrato(), _validaciones(sandbox="PASS"),
                        lifecycle="APPROVED")
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.verdadero("E-21 APPROVED se rechaza", bool(levanto))
    t.igual("E-21 y no entro", 0, len(doc["tools"]))

    c_reg.registrar(doc, _contrato(), _validaciones())
    t.igual("E-21 entra TEMPORARY", "TEMPORARY", doc["tools"][0]["lifecycle"])


def test_e22_promover_pide_la_evidencia_completa(t):
    """E-22 — falta un solo item de evidencia y no pasa a PROMOTION_CANDIDATE."""
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones(sandbox="PASS"))
    sin_tests = _evidencia(tests=False)
    levanto = ""
    try:
        c_reg.promover(doc, "repository-structure-inspector", "1.0.0",
                       "PROMOTION_CANDIDATE", "una-persona", sin_tests)
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.contiene("E-22 nombra lo que falta", "tests", levanto)
    t.igual("E-22 y el estado no se movio", "TEMPORARY", doc["tools"][0]["lifecycle"])

    c_reg.promover(doc, "repository-structure-inspector", "1.0.0",
                   "PROMOTION_CANDIDATE", "una-persona", _evidencia())
    t.igual("E-22 con todo pasa", "PROMOTION_CANDIDATE", doc["tools"][0]["lifecycle"])


def test_e23_el_constructor_no_aprueba_su_propia_tool(t):
    """E-23 — dev-tool-builder no puede mover una tool a APPROVED."""
    levanto = ""
    try:
        c_tools.transicionar("PROMOTION_CANDIDATE", "APPROVED", "dev-tool-builder")
    except c_tools.ToolInvalida as e:
        levanto = str(e)
    t.contiene("E-23 lo dice", "dev-tool-builder", levanto)
    t.igual("E-23 otro si puede", "APPROVED",
            c_tools.transicionar("PROMOTION_CANDIDATE", "APPROVED", "una-persona"))


def test_e24_una_transicion_que_no_existe(t):
    """E-24 — el salto que no esta en la maquina se rechaza y dice de donde a donde."""
    levanto = ""
    try:
        c_tools.transicionar("RETIRED", "APPROVED", "una-persona")
    except c_tools.ToolInvalida as e:
        levanto = str(e)
    t.contiene("E-24 nombra el estado actual", "RETIRED", levanto)
    t.contiene("E-24 y el pedido", "APPROVED", levanto)


# -- E-25 y E-26 — versionado ---------------------------------------------------

def test_e25_la_misma_version_con_otro_contrato(t):
    """E-25 — registrar name@version con un contrato distinto se rechaza."""
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones())
    otro = _contrato(timeoutSeconds=90)
    levanto = ""
    try:
        c_reg.registrar(doc, otro, _validaciones())
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.contiene("E-25 lo dice", "otro contrato", levanto)
    t.igual("E-25 sigue habiendo una sola", 1, len(doc["tools"]))


def test_e26_un_cambio_incompatible_pide_major_nueva(t):
    """E-26 — el cambio incompatible exige major, y las dos versiones conviven."""
    viejo = _contrato()
    saca_capacidad = _contrato(version="1.1.0", capabilities=[])
    t.verdadero("E-26 es incompatible", c_tools.es_cambio_incompatible(viejo, saca_capacidad))
    t.verdadero("E-26 y en la misma major se rechaza",
                len(c_tools.controlar_version(viejo, saca_capacidad)) > 0)

    con_major = _contrato(version="2.0.0", capabilities=[])
    t.vacio("E-26 con major nueva pasa", c_tools.controlar_version(viejo, con_major))

    doc = _registro()
    c_reg.registrar(doc, viejo, _validaciones())
    c_reg.registrar(doc, _contrato(version="2.0.0"), _validaciones())
    t.igual("E-26 conviven las dos", 2, len(doc["tools"]))
    t.igual("E-26 y se elige la mayor", "2.0.0",
            c_reg.para_capacidad(doc, "repository.read")[0]["version"])


# -- E-27 a E-29 — secrets ------------------------------------------------------

def test_e27_el_registro_guarda_el_nombre_del_secreto(t):
    """E-27 — secretsRequired lleva el nombre; el valor no aparece en ningun campo."""
    doc = _registro()
    contrato = _contrato(secretsRequired=["jira.token"], riskLevel="HIGH")
    c_reg.registrar(doc, contrato, _validaciones())
    entrada = doc["tools"][0]
    t.igual("E-27 guarda el nombre", ["jira.token"], entrada["secretsRequired"])
    t.no_contiene("E-27 y ningun valor", "glpat-", json.dumps(doc))


def test_e28_un_valor_con_forma_de_secreto_no_se_escribe(t):
    """E-28 — el catalogo del hook detecta el secreto en el documento y lo redacta."""
    raiz = tempfile.mkdtemp(prefix="harness-tools-")
    ruta = c_reg.ruta_por_defecto(raiz)
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones())
    doc["tools"][0]["registeredAt"] = "token glpat-ABCDEFGHIJKLMNOPQRSTUV en el campo"
    hallazgos = c_reg.escribir(doc, ruta)
    with io.open(ruta, encoding="utf-8") as f:
        escrito = f.read()
    t.verdadero("E-28 hubo hallazgo", len(hallazgos) > 0)
    t.no_contiene("E-28 el valor no quedo en disco", "glpat-ABCDEFGHIJKLMNOPQRSTUV", escrito)
    t.contiene("E-28 y quedo la marca", "secreto redactado", escrito)


def test_e29_la_limpieza_recorre_el_documento_entero(t):
    """E-29 — un campo que nadie nombro en ninguna lista igual queda limpio."""
    raiz = tempfile.mkdtemp(prefix="harness-tools-")
    ruta = c_reg.ruta_por_defecto(raiz)
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones())
    # Una clave inventada, que no existe en el schema ni en ninguna lista del codigo.
    doc["notasDeQuienLaConstruyo"] = {"pegado": ["glpat-ZYXWVUTSRQPONMLKJIHG"]}
    c_reg.escribir(doc, ruta)
    with io.open(ruta, encoding="utf-8") as f:
        escrito = f.read()
    t.no_contiene("E-29 tambien se limpio", "glpat-ZYXWVUTSRQPONMLKJIHG", escrito)


# -- E-30 y E-31 — el pipeline --------------------------------------------------

def test_e30_not_run_no_cuenta_como_pass(t):
    """E-30 — una etapa que no se pudo correr no vale como aprobada."""
    t.verdadero("E-30 todo PASS es verde",
                c_tools.todas_en_verde(_validaciones(sandbox="PASS")))
    t.verdadero("E-30 con NOT_RUN no lo es",
                not c_tools.todas_en_verde(_validaciones(sandbox="NOT_RUN")))

    # Y donde se decide algo con eso: no se promueve con una etapa sin correr.
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones(sandbox="NOT_RUN"))
    levanto = ""
    try:
        c_reg.promover(doc, "repository-structure-inspector", "1.0.0",
                       "PROMOTION_CANDIDATE", "una-persona", _evidencia())
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.contiene("E-30 y lo dice por etapa", "pipeline:sandbox", levanto)
    t.igual("E-30 el estado no se movio", "TEMPORARY", doc["tools"][0]["lifecycle"])


def test_e31_con_una_validacion_en_rojo_no_se_registra(t):
    """E-31 — una tool con alguna validacion en FAIL no entra al registro."""
    doc = _registro()
    levanto = ""
    try:
        c_reg.registrar(doc, _contrato(), _validaciones(unit="FAIL"))
    except c_reg.RegistroInvalido as e:
        levanto = str(e)
    t.contiene("E-31 nombra la etapa", "unit", levanto)
    t.igual("E-31 y no entro", 0, len(doc["tools"]))


# -- el registro contra su schema ----------------------------------------------

def test_el_registro_valida_contra_su_schema(t):
    """Lo que se escribe valida contra tool-registry/1.0, o no se escribe."""
    doc = _registro()
    c_reg.registrar(doc, _contrato(), _validaciones())
    t.vacio("el registro valida", c_reg.validar(doc))

    doc["tools"][0]["lifecycle"] = "FLAMANTE"
    t.verdadero("un estado inventado no valida", len(c_reg.validar(doc)) > 0)


def test_un_registro_que_no_existe_no_es_un_error(t):
    """Cargar un registro ausente devuelve uno vacio: todavia nadie construyo nada."""
    raiz = tempfile.mkdtemp(prefix="harness-tools-")
    doc = c_reg.cargar(c_reg.ruta_por_defecto(raiz))
    t.igual("la version del schema", "tool-registry/1.0", doc["schema_version"])
    t.vacio("y no hay tools", doc["tools"])
    t.vacio("ni capacidades que dar", c_reg.capacidades_que_da(doc))
