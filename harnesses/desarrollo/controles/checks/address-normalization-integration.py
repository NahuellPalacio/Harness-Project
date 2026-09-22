"""Check normativo: las direcciones del frontend se normalizan con la opcion catastral del GCBA.

    source: ES0901 / 6.3 / 7.1 / D5

Contesta sobre **que valor termina usando la aplicacion**, no sobre si se llamo al servicio. Que
exista un autocompletado, que se llame a una API de direcciones, que haya un regex, que este
instalada una libreria de codigos postales: todo eso se detecta en segundos y ninguno dice que la
direccion que la aplicacion guardo sea la normalizada. Un check que los mire se pone verde siempre.

🔴 **El defecto que esta regla existe para atrapar no es que falte la llamada. Es que la llamada
ocurra y despues se guarde el valor crudo.** Por eso se verifica la cadena entera:

    input crudo -> request -> response -> resultado normalizado -> valor CONSUMIDO

y se compara si el token consumido es el normalizado o es el crudo. La llamada es la parte visible,
y un control que la verifique aprueba una aplicacion que no cumple.

🔴 **La segunda mitad del problema es la cobertura.** El camino de busqueda con autocompletado es el
que alguien construye bien y el que alguien enumera; la carga manual de texto libre y la edicion de
una direccion guardada son los que nadie menciona. Los cinco tipos de camino se declaran TODOS, o
el resultado queda sin resolver: la ausencia de una palabra no es evidencia de ausencia.

🔴 **Este modulo no sabe como se usa la opcion catastral, y no lo inventa.** No hay un endpoint, un
campo de request, un campo de response, un identificador catastral, un campo de coordenadas, una
autenticacion, un timeout ni una URL de ambiente adentro de este archivo, y no los va a haber. La
identidad del proveedor entra como DATO DECLARADO con su fuente citada, y lo que el check compara
son identificadores. Nunca un mecanismo, y nunca el contenido de una direccion.

    sin identidad declarada  ->  CADASTRAL_PROVIDER_UNRESOLVED
    sin contrato declarado   ->  INTEGRATION_CONTRACT_MISSING

🔴 **Esta regla no contesta por ninguna otra.** Un resultado normalizado puede traer datos
geograficos y eso no dice nada sobre con que se dibujan; y esta verificacion mira el frontend, asi
que no informa nada sobre la validacion duplicada en otra capa. El resultado lleva solo la tupla de
D5, y ningun camino de este modulo nombra a otra regla ni a sus controles.

🔴 **Este modulo no ejecuta un frontend** y no crea ninguna skill. La corrida entra como dato y
quien la ejecute son las skills que ya estan instaladas.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "address-normalization-integration"
TIPO = "CHECK"
REGLA = "D5"
SENAL = "frontendAddressInputPresent"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D5"}

# La senal que NO sustituye a la de D5, por mas que este en TRUE. Un frontend no es un campo de
# direccion. Esta nombrada porque tiene un uso legitimo -la derivacion de mas abajo- y porque el
# error de usarla en lugar de la especifica tiene que tener nombre.
SENAL_DE_FRONTEND = "frontendPresent"
SENALES_QUE_NO_SUSTITUYEN = (SENAL_DE_FRONTEND,)

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "ADDRESS_FLOW_COVERAGE_UNRESOLVED"
SIN_PROVEEDOR = "CADASTRAL_PROVIDER_UNRESOLVED"
SIN_CONTRATO = "INTEGRATION_CONTRACT_MISSING"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Nueve, y el unico que aprueba es PASA. Los otros ocho dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_COBERTURA, SIN_PROVEEDOR,
           SIN_CONTRATO, SIN_OBJETIVO)

# De donde puede salir la identidad de la opcion catastral. La lista dice que fuentes son
# defendibles; NO dice cual es el mecanismo, que es lo que este harness no sabe.
#
# 📌 A diferencia de la regla vecina del mismo parrafo, aca GCBA_NORMATIVE es una fuente que un
# proyecto puede usar de verdad: la norma nombra el servicio del catalogo. Citar el nombre no es
# tener el contrato, asi que el hueco vivo de esta regla es SIN_CONTRATO y no SIN_PROVEEDOR.
FUENTES_DE_PROVEEDOR = ("GCBA_NORMATIVE", "GCBA_CATALOG_ENTRY", "ASI_INTEGRATION_CONTRACT",
                        "PROJECT_INTEGRATION_AGREEMENT", "HUMAN_CONFIRMATION")

# De donde puede salir el inventario de caminos, una ausencia declarada, un flujo inactivo y la
# completitud de alcance. Un camino que nadie enumero es un camino que nadie verifico, y eso no se
# disimula contando solo los que alguien eligio mirar.
FUENTES_DE_COBERTURA = ("PROJECT_UX_REQUIREMENT", "PROJECT_ARCHITECTURE", "ROUTE_INVENTORY",
                        "TEAM_APPROVED_TEST_PROFILE", "WORKUNIT_SCOPE_DEFINITION")

# Los cinco tipos de camino material. Los fija el pedido de instalacion; no son una lista que
# alguien de aca eligio. Lo que el proyecto enumera son sus flujos DENTRO de cada tipo.
BUSQUEDA = "SEARCH"
CARGA_MANUAL = "MANUAL_ENTRY"
SELECCION = "SELECTION"
EDICION = "EDIT_UPDATE"
ALTERNATIVO = "ALTERNATE_INPUT"
CLASES_DE_CAMINO = (BUSQUEDA, CARGA_MANUAL, SELECCION, EDICION, ALTERNATIVO)

# Las cinco etapas de la cadena. NO son campos del proveedor: son el modelo que este check tiene
# de la cadena, y por eso pueden estar escritas aca sin inventar nada. Lo que viaja por cada etapa
# es un token opaco -un hash, una etiqueta-, nunca el contenido de una direccion.
CRUDO = "RAW_INPUT"
PEDIDO = "PROVIDER_REQUEST"
RESPUESTA = "PROVIDER_RESPONSE"
NORMALIZADO = "NORMALIZED_RESULT"
CONSUMIDO = "CONSUMED_VALUE"
ETAPAS = (CRUDO, PEDIDO, RESPUESTA, NORMALIZADO, CONSUMIDO)

# Que prueba cada clase de evidencia. La particion es la razon de ser del check: las ocho ultimas
# son evidencia de lo que HAY, no de lo que se CONSUMIO, y no sostienen nada.
EVIDENCIA_DE_CORRIDA = ("NORMALIZED_ADDRESS_RUN",)
EVIDENCIA_DE_APOYO = ("SCREENSHOT", "HUMAN_CONFIRMATION", "INTEGRATION_TEST")
EVIDENCIA_QUE_NO_PRUEBA = ("AUTOCOMPLETE_COMPONENT_PRESENT", "ADDRESS_API_CALL",
                           "COORDINATE_DATA", "REGEX_VALIDATION", "POSTAL_CODE_LIBRARY",
                           "FRONTEND_FIELD_VALIDATION", "REPOSITORY_DEPENDENCY",
                           "AGENT_STATEMENT")

EJECUTADO = "EXECUTED"
NO_EJECUTADO = "NOT_EXECUTED"

# El modo de la corrida. Una corrida mockeada sirve para armar el caso y no prueba que la
# aplicacion consuma el valor normalizado: se distingue en el resultado, no se descarta en silencio.
REAL = "REAL"
MOCKEADO = "MOCKED"
MODOS = (REAL, MOCKEADO)

# El alcance, y la relacion entre el de la senal y el de la evaluacion. No hay una relacion "el
# mismo": dos alcances iguales no necesitan declarar nada, y una relacion que dijera "el mismo"
# sobre dos alcances distintos seria una contradiccion que alguien podria declarar.
ALCANCES = ("PROJECT", "WORKUNIT", "TASK")
RELACIONES = ("SIGNAL_SCOPE_CONTAINS_EVALUATION", "EVALUATION_SCOPE_CONTAINS_SIGNAL")
SIN_ALCANCE = "SCOPE_UNDECLARED"
ALCANCE_CRUZADO = "SCOPE_MISMATCH"

# La derivacion desde la senal de frontend, y lo que le falta cuando no alcanza.
DERIVADA = "DERIVED_FROM_FRONTEND_ABSENT"
SIN_COMPLETITUD = "SCOPE_COMPLETENESS_UNDECLARED"

NORMALIZADOR_ALTERNO = "ALTERNATE_NORMALIZER"
CRUDO_CONSUMIDO = "RAW_VALUE_CONSUMED"
CRUDO_COMO_NORMALIZADO = "RAW_INPUT_TREATED_AS_NORMALIZED"
CONSUMIDO_SIN_RASTRO = "CONSUMED_VALUE_UNTRACED"
ETAPA_SIN_DECLARAR = "CONSUMED_STAGE_UNDECLARED"
CADENA_INCOMPLETA = "NORMALIZATION_CHAIN_INCOMPLETE"
# Los tokens dicen una cosa y la etapa declarada dice la otra. Manda el token, asi que no es un
# incumplimiento probado; y no se confirma, asi que no aprueba.
DECLARACION_INCOHERENTE = "CHAIN_DECLARATION_INCOHERENT"
INDISTINGUIBLE = "NORMALIZATION_INDISTINGUISHABLE"
SIN_EJECUTAR = "GOVERNED_FLOW_NOT_EXECUTED"
SIN_EVIDENCIA_DE_CORRIDA = "NORMALIZATION_EVIDENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_MOCKEADA = "MOCKED_EVIDENCE_ONLY"
PROVEEDOR_SIN_DECLARAR = "FLOW_PROVIDER_UNDECLARED"
CORRIDA_SIN_PROVEEDOR = "RUN_PROVIDER_UNDECLARED"
CAMINO_EN_SILENCIO = "PATH_KIND_UNDECLARED"
INACTIVO_SIN_FUENTE = "INACTIVE_FLOW_UNSOURCED"
TODOS_INACTIVOS = "NO_ACTIVE_FLOW_IN_SCOPE"

HUECO_DE_SKILL = "SPECIALIZED_SKILL_GAP"
AGENTE_DE_INTEGRACION = "dev-integration"
SKILL_CATASTRAL = "dev-cadastral-address"


def _valor_de_senal(senal):
    """El valor de la senal, venga resuelta, cruda o como booleano viejo."""
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada.

    🔴 Un espacio NO es un dato declarado. `if not str(x or "")` deja pasar `" "`, que es truthy,
    y con eso un caso con toda la identidad en blancos llega a PASS: la regla informaria
    cumplimiento con un proveedor que no nombra nada y no cita en ningun lado.

    🔴 Y se aplica a LOS DOS LADOS de cada comparacion, siempre. Normalizar un solo lado es peor
    que no normalizar ninguno: en la regla vecina, el arreglo que dejo crudo el valor contra el
    que se compara hizo que un caso correcto saliera FAIL, y que un bypass probado se informara
    con el estado de un camino que no se ejecuto. Uno de los dos fue una regresion: la version
    cruda avisaba.
    """
    return str(valor or "").strip()


# -- el alcance ----------------------------------------------------------------

def _alcance(dato):
    """Un alcance normalizado: {id, kind, reference}."""
    d = dato or {}
    return {"id": declarado(d.get("id")), "kind": declarado(d.get("kind")),
            "reference": declarado(d.get("reference"))}


def alcance_coherente(caso, *senales):
    """Si la senal y la evaluacion son del mismo alcance, o si la relacion esta declarada.

    Devuelve {"ok", "reason", "detail", "relation"}.

    🔴 Este modulo NO adjudica la logica de la contencion. Una evidencia de todo el proyecto
    sosteniendo la aplicabilidad de una sola unidad de trabajo es defendible o no segun el caso, y
    el que sabe es quien la declara. Lo que el check exige es que la relacion este declarada y
    citada, y la publica en el resultado: nadie puede leer un PASS sin ver que se apoyo en una
    afirmacion entre alcances.
    """
    de_la_evaluacion = _alcance((caso or {}).get("scope"))
    if not de_la_evaluacion["id"] or de_la_evaluacion["kind"] not in ALCANCES:
        return {"ok": False, "reason": SIN_ALCANCE, "relation": None,
                "detail": "la evaluacion no declara para que alcance de orquestacion corre, y un "
                          "alcance ambiguo deja la aplicabilidad sin resolver"}

    declarada = (caso or {}).get("scopeRelation") or {}
    publicada = None
    for senal in senales:
        if senal is None:
            continue
        # 🔴 Una senal que NO es un documento -un booleano suelto, un string- no puede declarar
        # alcance, asi que su alcance es ambiguo por construccion y eso es SCOPE_UNDECLARED, no
        # un salteo. La version anterior hacia `continue` y con eso `evaluar(caso, True)` salia
        # PASS: la guarda entera se evadia con la forma vieja de una senal.
        if not isinstance(senal, dict):
            return {"ok": False, "reason": SIN_ALCANCE, "relation": None,
                    "detail": "la senal entro como valor suelto y no como documento, asi que no "
                              "declara para que alcance se produjo"}
        de_la_senal = _alcance(senal.get("scope"))
        sid = declarado(senal.get("signalId")) or "la senal"
        if not de_la_senal["id"] or de_la_senal["kind"] not in ALCANCES:
            return {"ok": False, "reason": SIN_ALCANCE, "relation": None,
                    "detail": "%s no declara su alcance, asi que no se puede saber si es el "
                              "mismo que el de la evaluacion" % sid}
        if (de_la_senal["id"], de_la_senal["kind"]) == (de_la_evaluacion["id"],
                                                        de_la_evaluacion["kind"]):
            continue
        if (declarado(declarada.get("relation")) not in RELACIONES
                or not declarado(declarada.get("reference"))):
            return {"ok": False, "reason": ALCANCE_CRUZADO, "relation": None,
                    "detail": "%s es de otro alcance que la evaluacion y nadie declaro la "
                              "relacion entre los dos, o la declaro sin citar donde" % sid}
        publicada = {"relation": declarado(declarada.get("relation")),
                     "reference": declarado(declarada.get("reference")),
                     "signal": sid, "signalScope": de_la_senal,
                     "evaluationScope": de_la_evaluacion}
    return {"ok": True, "reason": "", "detail": "", "relation": publicada}


# -- la aplicabilidad ----------------------------------------------------------

def aplicabilidad(caso, senal=None, frontend=None):
    """El valor de la aplicabilidad de D5, con su razon y su derivacion si la hubo.

    Devuelve {"value", "reason", "derivation"}.

        frontendPresent = TRUE   ->  no implica NADA. Un frontend no es un campo de direccion
        frontendPresent = FALSE  +  completitud de alcance declarada  ->  puede resolver FALSE
        frontendPresent = FALSE  sin completitud                      ->  UNRESOLVED

    🔴 La completitud entra con `source` de la lista de cobertura y con una referencia. Un booleano
    suelto seria una puerta de salida de la regla que el proyecto se declara solo y que nadie tiene
    que respaldar, que es exactamente la que hubo que sacar de la regla vecina.
    """
    valor = _valor_de_senal(senal)
    if valor != _senales.SIN_RESOLVER:
        return {"value": valor, "reason": "", "derivation": None}

    if _valor_de_senal(frontend) != _senales.FALSA:
        return {"value": _senales.SIN_RESOLVER, "reason": "", "derivation": None}

    # 🔴 Y tiene que ser LA senal de frontend. La version anterior no le miraba el `signalId` y
    # publicaba la constante como origen, asi que pasarle cualquier otra senal en FALSE derivaba
    # igual y le atribuia el FALSE a `frontendPresent`: la derivacion mentia de donde salio.
    origen = declarado((frontend or {}).get("signalId")) if isinstance(frontend, dict) else ""
    if origen != SENAL_DE_FRONTEND:
        return {"value": _senales.SIN_RESOLVER, "reason": SIN_COMPLETITUD, "derivation": None}

    # 🔴 `complete` se exige `True`, no truthy. Con un truthy cualquiera, un `complete: "no"`
    # escrito por quien queria decir que NO esta completo sacaba la regla del reporte. Es la
    # unica guarda de esta regla cuyo sentido de falla hace desaparecer a D5.
    completitud = (caso or {}).get("scopeCompleteness") or {}
    if (completitud.get("complete") is not True
            or declarado(completitud.get("source")) not in FUENTES_DE_COBERTURA
            or not declarado(completitud.get("reference"))):
        return {"value": _senales.SIN_RESOLVER, "reason": SIN_COMPLETITUD, "derivation": None}

    return {"value": _senales.FALSA, "reason": DERIVADA,
            "derivation": {"from": origen, "value": _senales.FALSA,
                           "source": completitud.get("source"),
                           "reference": declarado(completitud.get("reference"))}}


# -- el proveedor, el contrato y la cobertura ----------------------------------

def proveedor_valido(caso):
    """(ok, motivo) de la identidad de la opcion catastral declarada.

    Exige un id, una fuente de la lista y una referencia. Sin los tres no identifica nada: un id
    sin fuente es un nombre que alguien escribio, y de eso se trata todo esto. La identidad no se
    infiere de una URL genérica, de un nombre de paquete ni de que haya autocompletado.
    """
    proveedor = (caso or {}).get("cadastralProvider") or {}
    if not declarado(proveedor.get("id")):
        return False, "no hay una identidad declarada de la opcion catastral"
    if declarado(proveedor.get("source")) not in FUENTES_DE_PROVEEDOR:
        return False, ("la identidad no declara de donde sale, y una identidad sin origen es un "
                       "nombre que alguien escribio")
    if not declarado(proveedor.get("reference")):
        return False, "la identidad no dice donde esta declarada"
    return True, ""


def contrato_valido(caso):
    """(ok, motivo) del contrato de integracion declarado.

    El contrato es lo que permite distinguir las cinco etapas de la cadena. Este modulo no mira que
    dice adentro -ahi es donde estarian los campos que no inventa-: mira que exista, que diga de
    donde sale y que este citado.
    """
    contrato = (caso or {}).get("integrationContract") or {}
    if not declarado(contrato.get("id")):
        return False, "no hay un contrato de integracion declarado para la opcion catastral"
    if declarado(contrato.get("source")) not in FUENTES_DE_PROVEEDOR:
        return False, "el contrato de integracion no declara de donde sale"
    if not declarado(contrato.get("reference")):
        return False, "el contrato de integracion no dice donde esta declarado"
    return True, ""


def cobertura_valida(caso):
    """(ok, motivo) del inventario de caminos de direccion.

    🔴 Los CINCO tipos se declaran todos: cada uno con sus flujos, o con una ausencia que declara
    de donde sale. Un tipo en silencio deja la cobertura sin resolver. Es la misma doctrina que
    sostiene la senal -la ausencia de una palabra no es evidencia de ausencia- aplicada a la
    cobertura, y es lo que impide disimular el bypass de carga manual no mencionandolo.
    """
    cobertura = (caso or {}).get("addressFlows") or {}
    if not isinstance(cobertura, dict):
        return False, "el inventario de caminos no tiene la forma de un inventario"
    caminos = cobertura.get("paths") or []
    # 🔴 La forma se controla antes de recorrerla. Un `paths` que viene como diccionario, o un
    # camino que viene como texto, tiene que salir por uno de los nueve estados y no por un
    # AttributeError: un dato malformado que rompe el modulo no es un dato que fallo cerrado.
    if not isinstance(caminos, list) or not caminos:
        return False, "no hay un inventario de caminos de direccion declarado"
    if not all(isinstance(c, dict) for c in caminos):
        return False, "hay entradas del inventario que no tienen la forma de un camino"
    if declarado(cobertura.get("source")) not in FUENTES_DE_COBERTURA:
        return False, ("el inventario no declara de donde sale, y un inventario sin origen no "
                       "dice cuantos caminos hay")

    por_clase = {}
    for camino in caminos:
        clase = declarado(camino.get("kind"))
        if clase not in CLASES_DE_CAMINO:
            return False, "el inventario declara un tipo de camino que no existe: `%s`" % clase
        # 🔴 Un tipo declarado dos veces no se sobrescribe. Con `por_clase[clase] = camino`, la
        # primera entrada quedaba sin validar y `gobernados()` igual recorria las dos: un flujo
        # sin id llegaba a ser gobernado con el id vacio, evadiendo la validacion duplicando el
        # tipo. Si un tipo tiene dos grupos de flujos, van en una entrada.
        if clase in por_clase:
            return False, ("el inventario declara %s dos veces, y lo que se declara dos veces se "
                           "verifica una" % clase)
        por_clase[clase] = camino

    faltan = [c for c in CLASES_DE_CAMINO if c not in por_clase]
    if faltan:
        return False, ("%s: %s no se declara, y un tipo de camino en silencio no es un tipo de "
                       "camino que no exista" % (CAMINO_EN_SILENCIO, ", ".join(faltan)))

    for clase in CLASES_DE_CAMINO:
        camino = por_clase[clase]
        flujos = camino.get("flows") or []
        if not isinstance(flujos, list) or not all(isinstance(f, dict) for f in flujos):
            return False, "los flujos de %s no tienen la forma de un flujo" % clase
        if flujos:
            if [f for f in flujos if not declarado(f.get("flowId"))]:
                return False, "hay flujos sin identificar en %s" % clase
            continue
        # 🔴 `absent` se exige `True`, no truthy. Un `"absent": "false"` escrito por quien queria
        # decir que el camino NO esta ausente sacaba ese tipo entero de la verificacion.
        if camino.get("absent") is not True:
            return False, ("%s: %s no declara flujos ni declara que no exista en alcance"
                           % (CAMINO_EN_SILENCIO, clase))
        if declarado(camino.get("source")) not in FUENTES_DE_COBERTURA:
            return False, ("la ausencia de %s no declara de donde sale, y una ausencia sin fuente "
                           "es una omision con formato de declaracion" % clase)
    return True, ""


def gobernados(caso):
    """(activos, inactivos, avisos) de los flujos del inventario.

    🔴 **El defecto por omision es ACTIVO.** Un flujo que el proyecto saca de la verificacion
    declarandolo inactivo es la puerta de salida que la regla vecina tuvo que sacar: alla fue una
    etiqueta de materialidad, y una vista marcada asi dibujando con otro mapa daba PASS y no
    aparecia en ningun campo de la salida.

    Aca la puerta existe con tres cerrojos: un inactivo exige `source` de la lista -sin fuente se
    verifica como activo-, todo inactivo aparece en la salida, y si no queda ningun activo el
    resultado no puede ser PASS.
    """
    activos, inactivos, avisos = [], [], []
    for camino in ((caso or {}).get("addressFlows") or {}).get("paths") or []:
        clase = declarado(camino.get("kind"))
        for flujo in camino.get("flows") or []:
            entrada = dict(flujo)
            entrada["kind"] = clase
            entrada["flowId"] = declarado(flujo.get("flowId"))
            if flujo.get("active") is False:
                if declarado(flujo.get("source")) in FUENTES_DE_COBERTURA:
                    inactivos.append(entrada)
                    continue
                avisos.append("%s: el flujo %s se declara inactivo sin decir de donde sale, asi "
                              "que se verifica como activo"
                              % (INACTIVO_SIN_FUENTE, entrada["flowId"]))
            activos.append(entrada)
    return activos, inactivos, avisos


# -- la evidencia y la cadena --------------------------------------------------

def _evidencias(caso):
    """La evidencia por id, con el id normalizado en los dos lados."""
    return {declarado(e.get("evidenceId")): e for e in (caso or {}).get("evidence") or []
            if isinstance(e, dict) and declarado(e.get("evidenceId"))}


def es_de_corrida(evidencia):
    """Si la evidencia es de la clase que prueba. Normalizada, como todo lo que se compara."""
    return declarado((evidencia or {}).get("sourceType")) in EVIDENCIA_DE_CORRIDA


def es_real(evidencia):
    """Si la corrida se declara real. Un blanco alrededor no la vuelve mockeada."""
    return declarado((evidencia or {}).get("mode")) == REAL


def _de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron.

    🔴 Los dos lados normalizados. Sin esto, un `buildId` con un blanco alrededor informaba
    EVIDENCE_OUT_OF_BUILD —"es de otro build"— sobre una evidencia que era de este: un motivo
    que no es cierto, que es la mitad de la leccion de la regla vecina que si importa.
    """
    # 🔴 La variable NO se llama `declarado`: ese es el nombre de la funcion del modulo, y pisarla
    # en un alcance donde algun dia se la necesite es la trampa que ya rompio esta comparacion en
    # la regla vecina. El nombre largo cuesta menos que volver a buscarlo.
    for campo, clave in (("buildId", "id"), ("runtime", "runtime")):
        esperado = declarado((build or {}).get(clave))
        por_la_evidencia = declarado(evidencia.get(campo))
        if por_la_evidencia and esperado and por_la_evidencia != esperado:
            return False
    return True


def _cadena(resultado):
    """Los tokens de la cadena, normalizados, solo para las etapas que existen."""
    cruda = (resultado or {}).get("chain") or {}
    return {etapa: declarado(cruda.get(etapa)) for etapa in ETAPAS
            if declarado(cruda.get(etapa))}


def _proveedores_de_la_corrida(resultado, evidencias, build):
    """Con que proveedor dice la CORRIDA que se normalizo ese flujo."""
    vistos = set()
    for ref in (resultado or {}).get("evidenceRefs") or []:
        evidencia = evidencias.get(declarado(ref))
        if evidencia is None or not _de_esta_corrida(evidencia, build):
            continue
        if not es_de_corrida(evidencia):
            continue
        if declarado(evidencia.get("provider")):
            vistos.add(declarado(evidencia.get("provider")))
    return vistos


def _consume_el_crudo(resultado):
    """Si el flujo declara o demuestra que el valor que usa es el crudo.

    Sirve para los flujos de afuera del inventario, donde no hay evaluacion por flujo y la unica
    forma de ver un bypass probado es preguntarle a lo que el resultado declara.
    """
    cadena = _cadena(resultado)
    if declarado((resultado or {}).get("consumedFrom")) == CRUDO:
        return True
    consumido, crudo = cadena.get(CONSUMIDO), cadena.get(CRUDO)
    if consumido and crudo and consumido == crudo and cadena.get(NORMALIZADO) != crudo:
        return True
    return bool(consumido) and not cadena.get(NORMALIZADO)


# -- la evaluacion de un flujo -------------------------------------------------

def _evaluar_flujo(resultado, evidencias, build, proveedor_id):
    """El estado de un flujo gobernado, con su motivo y su evidencia."""
    salida = {"flowId": declarado(resultado.get("flowId")),
              "kind": declarado(resultado.get("kind")),
              "declaredProvider": declarado(resultado.get("provider")),
              "evidenceUsed": [], "issues": []}

    usadas, ajenas, huerfanas = [], [], []
    for ref in resultado.get("evidenceRefs") or []:
        e = evidencias.get(declarado(ref))
        if e is None:
            huerfanas.append(ref)
        elif not _de_esta_corrida(e, build):
            ajenas.append(ref)
        else:
            usadas.append(e)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe"
                                % (EVIDENCIA_HUERFANA, ", ".join(sorted(huerfanas))))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(sorted(ajenas))))

    # El nombre es largo a proposito: `declarado` es la funcion del modulo.
    por_el_flujo = declarado(resultado.get("provider"))
    cadena = _cadena(resultado)
    salida["chain"] = dict(cadena)
    salida["consumedFrom"] = declarado(resultado.get("consumedFrom"))

    # 🔴 El bypass se decide ANTES de mirar si se ejecuto. Un flujo que declara otro normalizador
    # ya es un incumplimiento: que ademas no se haya corrido no lo mejora.
    if por_el_flujo and por_el_flujo != proveedor_id:
        salida.update({"state": FALLA, "reason": NORMALIZADOR_ALTERNO,
                       "detail": "el flujo declara un normalizador distinto de la opcion "
                                 "catastral declarada para este proyecto"})
        return salida

    crudo = cadena.get(CRUDO)
    normalizado = cadena.get(NORMALIZADO)
    consumido = cadena.get(CONSUMIDO)
    etapa = salida["consumedFrom"]

    # 🔴 Sin response NI resultado normalizado no hubo normalizacion. Si igual hay un valor
    # consumido, la aplicacion esta tratando texto crudo como si fuera una direccion normalizada:
    # es el bypass de carga manual, el de edicion, y el de la llamada condicional que el flujo
    # normal no hace.
    #
    # 🔴 Los DOS, no uno. Con un `or`, una cadena que llega al resultado normalizado y no declara
    # la respuesta salia FAIL con un detalle falso —"no hay resultado normalizado" cuando si lo
    # habia—: una afirmacion de incumplimiento contra los propios tokens del caso.
    if RESPUESTA not in cadena and not normalizado:
        if consumido:
            salida.update({"state": FALLA, "reason": CRUDO_COMO_NORMALIZADO,
                           "detail": "el flujo usa un valor de direccion sin que haya pasado por "
                                     "la normalizacion: no hay respuesta del proveedor ni "
                                     "resultado normalizado en la cadena"})
        else:
            salida.update({"state": PARCIAL, "reason": CADENA_INCOMPLETA,
                           "detail": "la cadena no llega a un resultado normalizado, y lo que no "
                                     "llega no se verifica"})
        return salida

    # 🔴 El valor crudo consumido se decide ANTES de mirar si la cadena esta completa. Con el
    # orden anterior, un bypass PROBADO —la llamada ocurrio, hay respuesta, y el token consumido
    # es el crudo— se informaba como cadena incompleta porque le faltaba otra etapa: el estado
    # de lo que NO se sabe, puesto sobre algo que si se sabe. Es la especie contra la que avisa
    # el docstring de `declarado`, un nivel mas abajo.
    if consumido and crudo:
        # El token discrimina solo cuando el crudo y el normalizado son distintos. Cuando son el
        # mismo no dice nada, y entonces lo unico que queda es lo que el flujo declara.
        discrimina = bool(normalizado) and crudo != normalizado
        if consumido == crudo and discrimina:
            salida.update({"state": FALLA, "reason": CRUDO_CONSUMIDO,
                           "detail": "la llamada al proveedor ocurrio y el valor que la "
                                     "aplicacion usa es el crudo, no el normalizado"})
            return salida
        if etapa == CRUDO and (consumido == crudo or not discrimina):
            salida.update({"state": FALLA, "reason": CRUDO_CONSUMIDO,
                           "detail": "el flujo declara que el valor que usa es el crudo, aunque "
                                     "haya llamado al proveedor"})
            return salida
        if etapa == CRUDO and consumido == normalizado:
            # 🔴 Manda el TOKEN: el flujo declara que usa el crudo y sus tokens muestran que usa
            # el normalizado. Eso no es un incumplimiento probado —afirmarlo seria una afirmacion
            # falsa con la tupla normativa adosada— y tampoco esta confirmado, asi que no pasa.
            salida.update({"state": PARCIAL, "reason": DECLARACION_INCOHERENTE,
                           "detail": "el flujo declara que usa el valor crudo y sus tokens dicen "
                                     "que usa el normalizado: la evidencia se contradice y no "
                                     "se elige una"})
            return salida

    faltan = [e for e in ETAPAS if e not in cadena]
    if faltan:
        salida.update({"state": PARCIAL, "reason": CADENA_INCOMPLETA,
                       "detail": "la cadena no declara %s, y una cadena a medias no dice que "
                                 "valor usa la aplicacion" % ", ".join(faltan)})
        return salida

    # Se exigen LAS DOS cosas: el token y la etapa declarada. Pedir solo la etapa deja que una
    # corrida diga la palabra correcta; pedir solo el token deja pasar una que consume el
    # normalizado por casualidad y no lo declara. Cuando discrepan, manda el token.
    if consumido != normalizado:
        salida.update({"state": PARCIAL, "reason": CONSUMIDO_SIN_RASTRO,
                       "detail": "el valor que la aplicacion usa no es ni el crudo ni el "
                                 "normalizado, asi que no se puede decir de donde salio"})
        return salida
    if etapa != NORMALIZADO:
        salida.update({"state": PARCIAL, "reason": ETAPA_SIN_DECLARAR,
                       "detail": "el flujo no declara que el valor que usa sea el resultado "
                                 "normalizado, y lo que no se dice no se verifica"})
        return salida

    if not por_el_flujo:
        salida.update({"state": PARCIAL, "reason": PROVEEDOR_SIN_DECLARAR,
                       "detail": "el flujo no dice con que se normaliza, y lo que no se dice no "
                                 "se verifica"})
        return salida

    if declarado(resultado.get("execution")) != EJECUTADO:
        salida.update({"state": PARCIAL, "reason": SIN_EJECUTAR,
                       "detail": "el flujo gobernado no se ejecuto, y lo que no se ejecuto no "
                                 "pasa por que el resto haya pasado"})
        return salida

    de_corrida = [e for e in usadas if es_de_corrida(e)]
    if not de_corrida:
        salida.update({"state": PARCIAL, "reason": SIN_EVIDENCIA_DE_CORRIDA,
                       "detail": "el flujo dice normalizar con la opcion catastral y no lo "
                                 "sostiene ninguna evidencia de corrida: un autocompletado, una "
                                 "llamada a una API de direcciones, un regex, una libreria "
                                 "instalada o la validacion de un campo no alcanzan"})
        return salida

    ajenos = [e for e in de_corrida if declarado(e.get("provider"))
              and declarado(e.get("provider")) != proveedor_id]
    if ajenos:
        salida.update({"state": FALLA, "reason": NORMALIZADOR_ALTERNO,
                       "detail": "la corrida reporta que el flujo se normalizo con otro "
                                 "proveedor, sin importar lo que declare el flujo"})
        return salida

    if [e for e in de_corrida if not declarado(e.get("provider"))]:
        salida.update({"state": PARCIAL, "reason": CORRIDA_SIN_PROVEEDOR,
                       "detail": "la corrida no declara con que proveedor se normalizo, y lo que "
                                 "no se dice no se verifica"})
        return salida

    reales = [e for e in de_corrida if es_real(e)]
    if not reales:
        salida.update({"state": PARCIAL, "reason": EVIDENCIA_MOCKEADA,
                       "detail": "la unica evidencia de corrida esta declarada como mockeada: "
                                 "documenta el caso y no prueba que la aplicacion consuma el "
                                 "valor normalizado"})
        return salida

    # 🔴 El residuo, dicho y no escondido. Si el proveedor devolvio exactamente lo que la persona
    # escribio, los tres tokens son iguales y *consumir el crudo* y *consumir el normalizado* son
    # indistinguibles. Es un caso legitimo y frecuente, asi que pasa; y queda anotado para que se
    # lea que la comparacion fue degenerada. Bajarlo a PARCIAL pondria en rojo a todo proyecto que
    # valide una direccion ya normalizada, y un check que se pone en rojo sin motivo es un check
    # que alguien apaga.
    if crudo == normalizado:
        salida["issues"].append("%s: el valor crudo y el normalizado son el mismo token, asi que "
                                "la comparacion no distingue cual de los dos se consumio"
                                % INDISTINGUIBLE)

    salida.update({"state": PASA, "reason": "",
                   "detail": "el flujo corrio de verdad, normalizo con la opcion catastral "
                             "declarada y la aplicacion usa el valor normalizado"})
    return salida


# -- la evaluacion -------------------------------------------------------------

def evaluar(caso, senal=None, frontend=None, desde=None):
    """El estado de D5 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `caso` es el reporte de una corrida:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "scope": {"id", "kind", "reference"},
         "scopeRelation": {"relation", "reference"},
         "scopeCompleteness": {"complete", "source", "reference"},
         "testTarget": {"available": bool},
         "cadastralProvider": {"id", "source", "reference"},
         "integrationContract": {"id", "source", "reference"},
         "addressFlows": {"source", "paths": [{"kind", "absent", "source",
                                               "flows": [{"flowId", "active", "source"}]}]},
         "results": [{"flowId", "kind", "provider", "execution", "chain", "consumedFrom",
                      "evidenceRefs"}],
         "evidence": [{"evidenceId", "sourceType", "reference", "claim", "buildId", "runtime",
                       "provider", "mode"}]}

    🔴 Para un build, un proveedor, un inventario y unos datos fijos, esto devuelve siempre lo
    mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "build": dict(build), "flows": [], "issues": []}

    alcance = alcance_coherente(caso, senal, frontend)
    salida["scope"] = _alcance((caso or {}).get("scope"))
    if alcance["relation"]:
        salida["scopeRelation"] = alcance["relation"]
    if not alcance["ok"]:
        salida.update({"state": SIN_RESOLVER, "reason": alcance["reason"],
                       "detail": alcance["detail"], "signalValue": _senales.SIN_RESOLVER,
                       "missingSignals": [SENAL]})
        return salida

    resuelta = aplicabilidad(caso, senal, frontend)
    valor = resuelta["value"]
    salida["signalValue"] = valor
    if resuelta["derivation"]:
        salida["derivation"] = resuelta["derivation"]

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [SENAL],
                       "reason": resuelta["reason"] or SIN_RESOLVER,
                       "detail": "no se sabe si hay un flujo de direcciones en el frontend, y lo "
                                 "que no se sabe no se convierte en que no aplica"})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA, "reason": resuelta["reason"],
                       "detail": "no hay un flujo de direcciones del frontend en alcance"})
        return salida

    objetivo = (caso or {}).get("testTarget") or {}
    # 🔴 `True`, no truthy: un `available: "no"` daba PASS.
    if objetivo.get("available") is not True:
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo "
                                 "que no se ejecuto no pasa"})
        return salida

    ok, motivo = proveedor_valido(caso)
    if not ok:
        salida.update({"state": SIN_PROVEEDOR, "reason": SIN_PROVEEDOR, "detail": motivo})
        return salida

    proveedor = caso["cadastralProvider"]
    # El id que se informa es el normalizado: es el que el modulo usa para comparar, y publicar
    # uno distinto del que se compara es como se lee un FAIL que no se entiende.
    proveedor_id = declarado(proveedor.get("id"))
    salida["cadastralProvider"] = {"id": proveedor_id, "source": proveedor.get("source")}

    ok, motivo = contrato_valido(caso)
    if not ok:
        salida.update({"state": SIN_CONTRATO, "reason": SIN_CONTRATO, "detail": motivo})
        return salida

    salida["integrationContract"] = {"id": declarado(caso["integrationContract"].get("id")),
                                     "source": caso["integrationContract"].get("source")}

    ok, motivo = cobertura_valida(caso)
    if not ok:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA, "detail": motivo,
                       "governedFlows": []})
        return salida

    activos, inactivos, avisos = gobernados(caso)
    salida["issues"].extend(avisos)
    salida["governedFlows"] = [f["flowId"] for f in activos]
    salida["inactiveFlows"] = [{"flowId": f["flowId"], "kind": f.get("kind"),
                                "source": f.get("source")} for f in inactivos]
    salida["addressFlows"] = {
        "source": caso["addressFlows"].get("source"),
        "paths": [{"kind": declarado(c.get("kind")), "absent": bool(c.get("absent")),
                   "flows": [declarado(f.get("flowId")) for f in c.get("flows") or []]}
                  for c in caso["addressFlows"]["paths"]]}

    # 🔴 Declararlos todos inactivos no vacia el conjunto gobernado. La senal afirma que hay un
    # flujo de direcciones en alcance, y que no quede ninguno activo contradice la senal: no se
    # sabe, y eso no es PASS.
    if not activos:
        salida.update({"state": SIN_COBERTURA, "reason": TODOS_INACTIVOS,
                       "detail": "la senal dice que hay un flujo de direcciones en alcance y "
                                 "todos los declarados estan inactivos: o la senal esta mal, o "
                                 "falta un flujo, y ninguna de las dos cosas se verifico"})
        return salida

    evidencias = _evidencias(caso)
    resultados = list((caso or {}).get("results") or [])
    por_flujo = {}
    for r in resultados:
        por_flujo.setdefault(declarado(r.get("flowId")), []).append(r)

    # Un flujo del inventario sin ningun resultado es un flujo que no se verifico: se cuenta, no
    # se omite. Omitirlo seria dejar pasar una corrida que probo solo lo que le convenia.
    flujos = []
    for f in activos:
        fid = f["flowId"]
        if not por_flujo.get(fid):
            flujos.append({"flowId": fid, "kind": f.get("kind"), "declaredProvider": "",
                           "state": PARCIAL, "reason": SIN_EJECUTAR, "evidenceUsed": [],
                           "issues": [], "chain": {}, "consumedFrom": "",
                           "detail": "el flujo esta en el inventario y no tiene ningun "
                                     "resultado"})
            continue
        for r in por_flujo[fid]:
            flujos.append(_evaluar_flujo(r, evidencias, build, proveedor_id))

    # Un resultado de un flujo que el inventario no declara no cuenta como flujo gobernado.
    # 🔴 Pero si declara otro normalizador, o si su corrida lo reporta, o si consume el valor
    # crudo, el inventario deja de ser creible y el resultado no puede ser PASA: o falta un flujo
    # gobernado, o ese flujo no lo es y nadie lo dijo. No se sabe. Se mira lo que el resultado
    # declara Y lo que su corrida reporta: si solo se mirara lo declarado, dejar ese campo vacio
    # desarmaria la guarda entera.
    # 🔴 Los flujos declarados INACTIVOS entran en esta cuenta. Un resultado sobre un flujo que
    # el proyecto declaro inactivo es evidencia de que ese flujo corrio, asi que la declaracion
    # se contradice: si ademas ese resultado prueba un bypass, desaparecia por completo —no
    # estaba en `flows`, no estaba en `ignoredResults`, no lo nombraba ningun aviso— y el
    # resultado salia PASS. Era la ultima forma que le quedaba a la puerta de salida que la regla
    # vecina tuvo que sacar. Un resultado limpio sobre un inactivo se lista y no acusa nada.
    ids = set(salida["governedFlows"])
    afuera = [r for r in resultados if declarado(r.get("flowId")) not in ids]
    salida["ignoredResults"] = [declarado(r.get("flowId")) for r in afuera]
    sospechosos = []
    for r in afuera:
        candidatos = ({declarado(r.get("provider"))}
                      | _proveedores_de_la_corrida(r, evidencias, build))
        candidatos.discard("")
        if (candidatos - {proveedor_id}) or _consume_el_crudo(r):
            sospechosos.append(declarado(r.get("flowId")))
    for fid in sospechosos:
        salida["issues"].append(
            "%s: el flujo %s no esta en el inventario y no pasa por la opcion catastral"
            % (SIN_COBERTURA, fid))

    salida["flows"] = flujos
    for f in flujos:
        salida["issues"].extend(f.get("issues") or [])

    estados = [f["state"] for f in flujos]
    if FALLA in estados:
        salida.update({"state": FALLA,
                       "reason": next(f["reason"] for f in flujos if f["state"] == FALLA)})
    elif sospechosos:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": "hay un flujo fuera del inventario que no pasa por la opcion "
                                 "catastral: o el inventario esta incompleto, o ese flujo no "
                                 "esta gobernado y nadie lo declaro"})
    elif estados and all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL,
                       "reason": next((f["reason"] for f in flujos if f["state"] != PASA),
                                      SIN_EJECUTAR)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


# -- los agentes, el ruteo y la remediacion ------------------------------------

def agentes_primarios(desde=None):
    """Quien es responsable, resuelto contra el registro de agentes.

    🔴 Los agentes salen de LA MATRIZ, no de una lista escrita aca: la fila de D5 los declara y
    este check no redefine la propiedad. Si alguno no estuviera en el registro, se ve.
    """
    from orquestacion import matriz, registro_agentes as reg
    fila = matriz.regla(REGLA, None, desde or __file__) or {}
    salida = []
    for agente in fila.get("primaryAgents") or []:
        salida.append({"agent": agente, "requestedFor": CONTROL, "source": dict(TRAZA),
                       "declared": reg.hay_agente(agente, None, desde or __file__)})
    return salida


def remediacion(resultado, desde=None):
    """Que hace falta para arreglarlo, cuando arreglarlo exige saber como se usa la integracion.

    El estado sale del registro de agentes -`SPECIALIZED_SKILL_GAP` ya existe y no se inventa
    otro-. 🔴 Que el hueco este nombrado NO hace cumplir a D5: el control sigue sin pasar y esto
    dice por que no se puede cerrar hoy.

    🔴 Esto no crea la skill, no la instala y no la completa con informacion inventada. El pedido
    lo prohibe explicitamente, y el contrato tampoco se sabe.
    """
    estado = (resultado or {}).get("state")
    if estado not in (FALLA, PARCIAL, SIN_PROVEEDOR, SIN_CONTRATO):
        return None

    from orquestacion import registro_agentes as reg
    ruteo = reg.resolver_ruteo(AGENTE_DE_INTEGRACION, SKILL_CATASTRAL, None, desde or __file__)
    if ruteo.get("routable"):
        return None

    return {"control": CONTROL, "source": dict(TRAZA), "state": HUECO_DE_SKILL,
            "skill": SKILL_CATASTRAL, "agent": AGENTE_DE_INTEGRACION,
            "skillValidation": ruteo.get("result"),
            "compliant": False,
            "reason": "la remediacion de D5 exige conocimiento especifico de como se integra la "
                      "opcion catastral, y esa skill no esta instalada. El hueco queda visible y "
                      "D5 sigue sin cumplir"}


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills: dice cuales de las instaladas cubren la ejecucion. Si alguna no esta,
    se ve; no se inventa una.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTE_DE_INTEGRACION, "dev-external-integration"),
               ("dev-frontend", "dev-frontend-implementation"),
               ("dev-quality", "dev-test-automation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
