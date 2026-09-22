"""Check normativo: los servicios exigen token en el borde, y no hay camino que lo esquive.

    source: ES0901 / 6.3 / 7.1 / D8

Contesta sobre **que pasa cuando llega una llamada sin token**, no sobre que esta instalado. Una
dependencia de tokens en el manifiesto, un middleware configurado, un endpoint de login que emite,
un header que se parsea, un gateway que existe, un documento que dice "ruta privada": los seis se
detectan en segundos y ninguno dice que la operacion protegida se rechace. Un check que los mire se
pone verde siempre — y en esta regla el falso verde tapa un servicio abierto.

🔴 **El binding sale de la matriz, y es la PRIMERA compuerta.** Este modulo no lleva escrito el id
de su policy ni el nombre de su senal: los deriva de la fila de D8, junto con los agentes duenos y
la tupla normativa entera. Lo unico escrito es su propio id, que es lo que el registro necesita para
encontrar el archivo — y se verifica contra la fila: si la matriz no lo declara como check de D8,
este modulo no se arroga el binding.

    sin fila resoluble  ->  D8_MATRIX_BINDING_UNRESOLVED, y no se evalua nada mas

Corre antes de la senal a proposito: sin saber de que senal depende la regla, preguntar por su valor
es preguntar por un nombre que el modulo se invento. Es el unico camino de D8 cuyo resultado no
lleva la tupla normativa, porque la tupla sale de la matriz que no se pudo leer — y lo dice.

🔴 **Este modulo no sabe que es un token en este proyecto, y no lo inventa.** Adentro de este archivo
no hay -ni va a haber- un mecanismo con nombre, un emisor, una audiencia, un algoritmo, un claim, un
tiempo de vida, un formato de encabezado, un rol, un scope, una regla de refresco, una
implementacion de puerta de enlace ni un codigo de rechazo. El mecanismo entra como DATO DECLARADO
con su fuente citada, y sin eso: `TOKEN_MECHANISM_UNRESOLVED`.

🔴 **Un camino se identifica por el comportamiento protegido que alcanza, no por su direccion.** Los
que comparten `behaviorId` son caminos al mismo comportamiento, asi que un bypass se DERIVA: un
camino activo que llega a un comportamiento protegido sin exigir token. No hace falta reconocer una
direccion vieja, parsear un verbo ni saber como se ve una puerta de enlace. Y el resultado informa
ids, nunca direcciones: un FAIL de D8 no publica el mapa de puertas abiertas de una aplicacion.

🔴 **Nada se exime solo.** No hay adentro de este archivo una lista de categorias exentas ni un
patron de direccion, y el modulo no ramifica por el nombre de un endpoint. Un endpoint
intencionalmente publico necesita su excepcion declarada; sin eso,
`TOKEN_PROTECTION_EXCEPTION_UNRESOLVED`.

🔴 **Un PASS de D8 dice una sola cosa**: el endpoint exige token y sin token no pasa. No dice que los
roles esten bien, no dice que otra regla se cumpla y no dice que haya una evaluacion de seguridad
aprobada. El resultado lleva solo la tupla de D8 y no nombra ninguna otra regla ni ningun otro
estandar.

🔴 **Este modulo no llama a ningun servicio** y no emite ningun token. Las sondas entran como dato y
quien las ejecute son las skills que ya estan instaladas.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "service-token-protection"
TIPO = "CHECK"
REGLA = "D8"

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
SIN_BINDING = "D8_MATRIX_BINDING_UNRESOLVED"
SIN_COBERTURA = "SERVICE_ENDPOINT_COVERAGE_UNRESOLVED"
SIN_MECANISMO = "TOKEN_MECHANISM_UNRESOLVED"
SIN_EXCEPCION = "TOKEN_PROTECTION_EXCEPTION_UNRESOLVED"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Diez, y el unico que aprueba es PASA. Los otros nueve dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_BINDING, SIN_COBERTURA,
           SIN_MECANISMO, SIN_EXCEPCION, SIN_OBJETIVO)

SENAL_AJENA = "SIGNAL_IDENTITY_MISMATCH"

# -- las clases de camino ------------------------------------------------------

# Las nueve clases de camino a un comportamiento protegido. El `kind` se informa para que quien lee
# sepa por donde entro; NO decide nada: las nueve se verifican igual. Tratar distinto a la primaria
# seria construir el agujero que esta regla busca.
PRIMARIO = "PRIMARY"
CLASES = (PRIMARIO, "ALTERNATE_URL", "ALTERNATE_METHOD", "LEGACY_ROUTE", "VERSIONED_ROUTE",
          "SECONDARY_CONTROLLER", "GATEWAY_EXPOSED", "ADMINISTRATIVE", "UPLOAD_DOWNLOAD")

# De donde puede salir el inventario de endpoints materiales. Un camino que nadie enumero es un
# camino que nadie verifico, y eso no se disimula contando solo los que alguien eligio mirar.
FUENTES_DE_COBERTURA = ("PROJECT_ARCHITECTURE", "SERVICE_CONTRACT", "ROUTE_INVENTORY",
                        "FRAMEWORK_MAPPING", "RUNTIME_ROUTE_DISCOVERY", "IMPACT_ANALYSIS",
                        "TEAM_APPROVED_TEST_PROFILE")

# De donde puede salir el mecanismo de token del proyecto, y una excepcion de endpoint publico. La
# lista dice que fuentes son defendibles; NO dice cual es el mecanismo, que es lo que este harness
# no sabe.
FUENTES_DE_IDENTIDAD = ("GCBA_NORMATIVE", "PROJECT_SECURITY_CONTRACT", "ASI_INTEGRATION_CONTRACT",
                        "PROJECT_INTEGRATION_AGREEMENT", "HUMAN_CONFIRMATION")

# -- las sondas ----------------------------------------------------------------

SIN_TOKEN = "NO_TOKEN"
TOKEN_INVALIDO = "INVALID_TOKEN"
TOKEN_VALIDO = "VALID_TOKEN"

# Las dos negativas son obligatorias. La positiva sola es el falso verde mas caro de esta regla: un
# token valido que funciona no dice nada sobre que pasa sin token.
NEGATIVAS = (SIN_TOKEN, TOKEN_INVALIDO)
SONDAS = (SIN_TOKEN, TOKEN_INVALIDO, TOKEN_VALIDO)

REAL = "REAL"
MOCKEADO = "MOCKED"
MODOS = (REAL, MOCKEADO)

# -- la particion de evidencia -------------------------------------------------

# La unica que prueba, y las dos que acompanan.
SONDA = "TOKEN_ENFORCEMENT_PROBE"
EVIDENCIA_QUE_PRUEBA = (SONDA,)
EVIDENCIA_DE_APOYO = ("HUMAN_CONFIRMATION", "CODE_PATH_REVIEW")

# 🔴 Lo que esta instalado no prueba lo que se rechaza. Las ocho son evidencia de lo que HAY o de lo
# que alguien SUPONE, y ninguna sostiene nada.
EVIDENCIA_QUE_NO_PRUEBA = ("REPOSITORY_DEPENDENCY", "SECURITY_MIDDLEWARE_CONFIG",
                           "TOKEN_ISSUANCE", "LOGIN_ENDPOINT", "AUTH_HEADER_PARSING",
                           "GATEWAY_PRESENT", "ROUTE_DOCUMENTATION", "AGENT_STATEMENT")

# -- los motivos ---------------------------------------------------------------

ALCANZA_SIN_TOKEN = "PROTECTED_BEHAVIOR_REACHED_WITHOUT_TOKEN"
BYPASS = "TOKEN_ENFORCEMENT_BYPASS"
SIN_APLICACION = "ENFORCEMENT_POINT_UNDECLARED"
EXIGENCIA_SIN_DECLARAR = "TOKEN_REQUIREMENT_UNDECLARED"
SIN_SONDA = "ENFORCEMENT_PROBE_MISSING"
SONDA_INCOMPLETA = "NEGATIVE_PROBE_COVERAGE_INCOMPLETE"
SONDA_MOCKEADA = "MOCKED_EVIDENCE_ONLY"
CODIGO_DISTINTO = "REJECTION_CONTRACT_MISMATCH"
ACTIVIDAD_SIN_DECLARAR = "ENDPOINT_ACTIVITY_UNDECLARED"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"

AGENTE_POR_DEFECTO = "dev-security"


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada.

    🔴 Un espacio NO es un dato declarado, y se aplica a LOS DOS LADOS de cada comparacion. Es la
    leccion de D6, donde normalizar un solo lado convirtio un caso correcto en un FAIL y un bypass
    probado en un aviso que nadie leia.
    """
    return str(valor or "").strip()


# -- el binding contra la matriz -----------------------------------------------

def binding(desde=None, doc=None):
    """(datos, motivo) del binding contra la fila de D8 de la matriz instalada.

    Devuelve el id de la policy, el id del check, la senal, los agentes duenos y la tupla
    normativa. `None` con su motivo cuando la fila no se puede resolver, que es lo que deja el
    resultado en `D8_MATRIX_BINDING_UNRESOLVED`.

    🔴 Falla cerrado en las cinco formas: sin matriz, ilegible, sin la fila, con una cantidad de
    senales distinta de una, o sin declarar a este modulo entre sus checks. La ultima es la que
    importa mas: un modulo que se arroga un binding que la matriz no declara es un control que
    nadie dio de alta.
    """
    from orquestacion import matriz
    try:
        documento = doc if doc is not None else matriz.cargar(desde or __file__)
    except matriz.MatrizInvalida as e:
        return None, "la matriz normativa no se pudo leer: %s" % e
    try:
        fila = matriz.regla(REGLA, documento, desde or __file__)
    except matriz.MatrizInvalida as e:
        return None, "la matriz no declara la fila de %s: %s" % (REGLA, e)

    policies = [declarado(p) for p in fila.get("policies") or [] if declarado(p)]
    checks = [declarado(c) for c in fila.get("checks") or [] if declarado(c)]
    aplic = fila.get("applicability") or {}
    senales = [declarado(s) for s in aplic.get("signals") or [] if declarado(s)]

    if len(senales) != 1:
        return None, ("la fila declara %d senales de aplicabilidad y este check se resuelve con "
                      "una sola; no se elige" % len(senales))
    if CONTROL not in checks:
        return None, ("la fila no declara `%s` entre sus checks, asi que este modulo no es el "
                      "check de %s y no se arroga el binding" % (CONTROL, REGLA))
    if not policies:
        return None, "la fila no declara ninguna policy"

    traza = matriz.trazabilidad(REGLA, documento, desde or __file__)
    if not all(declarado(traza.get(k)) for k in ("standard", "version", "section", "rule")):
        return None, "la matriz no declara el estandar entero, y sin eso no hay trazabilidad"

    return {"rule": REGLA, "policies": policies, "checks": checks, "signal": senales[0],
            "agents": [declarado(a) for a in fila.get("primaryAgents") or [] if declarado(a)],
            "source": traza}, ""


# -- la senal ------------------------------------------------------------------

def valor_de_senal(senal, signal_id):
    """El valor de LA senal de D8, venga resuelta, cruda o como booleano viejo.

    🔴 Se mira el `signalId`, que es la leccion de D7: sin eso, pasarle la senal de otra regla en
    TRUE hacia que el check evaluara el caso y publicara la senal propia como origen, o sea
    cumplimiento atribuido a una senal que nunca llego.
    """
    if isinstance(senal, dict):
        if isinstance(senal.get(signal_id), dict):
            return valor_de_senal(senal[signal_id], signal_id)
        sid = declarado(senal.get("signalId"))
        if sid and sid != signal_id:
            return _senales.SIN_RESOLVER
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def identidad_de_senal(senal, signal_id):
    """El `signalId` que el dato trae, o "" si no trae ninguno."""
    if not isinstance(senal, dict):
        return ""
    if isinstance(senal.get(signal_id), dict):
        return signal_id
    return declarado(senal.get("signalId"))


# -- el inventario -------------------------------------------------------------

def inventario_valido(caso):
    """(ok, motivo) del inventario de endpoints materiales."""
    inventario = (caso or {}).get("endpoints") or {}
    lista = inventario.get("items") or []
    if not lista:
        return False, "no hay un inventario de endpoints declarado"
    if inventario.get("source") not in FUENTES_DE_COBERTURA:
        return False, ("el inventario no declara de donde sale, y un inventario sin origen no "
                       "dice cuantos caminos hay")
    if [e for e in lista if not declarado(e.get("id"))]:
        return False, "hay endpoints sin identificar en el inventario"
    if [e for e in lista if not declarado(e.get("behaviorId"))]:
        return False, ("hay endpoints que no declaran a que comportamiento protegido llegan, y "
                       "sin eso un bypass no se puede derivar")
    if [e for e in lista if e.get("kind") not in CLASES]:
        return False, "hay endpoints sin una clase de camino de las nueve declaradas"
    sin_actividad = [declarado(e.get("id")) for e in lista
                     if not isinstance(e.get("active"), bool)]
    if sin_actividad:
        # 🔴 Un camino que no dice si esta activo NO se da por desactivado. Dar por muerta una ruta
        # que nadie apago es exactamente el defecto que esta regla busca.
        return False, ("%s: %s no declara si esta activo, y lo que no se declara no se da por "
                       "apagado" % (ACTIVIDAD_SIN_DECLARAR, ", ".join(sorted(sin_actividad))))
    return True, ""


def endpoints(caso):
    """Los endpoints del inventario. TODOS.

    🔴 No hay un segundo filtro. El inventario ES la lista de caminos materiales —eso es lo que su
    `source` respalda—, asi que una etiqueta que el proyecto ponga sola no saca a ninguno de la
    verificacion.
    """
    return list(((caso or {}).get("endpoints") or {}).get("items") or [])


def gobernados(caso):
    """Los caminos activos. Un camino declarado inactivo no alcanza ningun comportamiento."""
    return [e for e in endpoints(caso) if e.get("active") is True]


def clasificacion_completa(caso):
    """(completa, motivo) del inventario: declarado completo, y nada mas."""
    inventario = (caso or {}).get("endpoints") or {}
    if inventario.get("complete") is False:
        return False, "el inventario de endpoints se declara incompleto"
    return True, ""


# -- la identidad declarada ----------------------------------------------------

def identidad_valida(bloque, que):
    """(ok, motivo) de un dato de identidad declarado: id, fuente de la lista y referencia."""
    datos = bloque or {}
    if not declarado(datos.get("id")):
        return False, "no hay %s declarado" % que
    if datos.get("source") not in FUENTES_DE_IDENTIDAD:
        return False, ("%s no declara de donde sale, y una identidad sin origen es un nombre que "
                       "alguien escribio" % que)
    if not declarado(datos.get("reference")):
        return False, "%s no dice donde esta declarado" % que
    return True, ""


def mecanismo_valido(caso):
    """(ok, motivo) del mecanismo de token declarado por el proyecto.

    Ademas de identificarse, tiene que decir DONDE se aplica y COMO se entrega el token: sin esas
    dos cosas no hay contra que verificar un endpoint, y el check no las puede suponer.
    """
    ok, motivo = identidad_valida((caso or {}).get("tokenMechanism"),
                                  "el mecanismo de token del proyecto")
    if not ok:
        return False, motivo
    datos = caso["tokenMechanism"]
    if not declarado(datos.get("enforcementPoint")):
        return False, ("el mecanismo no declara donde se aplica, y sin punto de aplicacion no hay "
                       "borde de servicio que verificar")
    if not declarado(datos.get("tokenSupply")):
        return False, "el mecanismo no declara como se entrega el token"
    return True, ""


def codigo_exigido(caso):
    """El codigo de rechazo que el contrato autoritativo define, o "" si no define ninguno.

    🔴 D8 no exige un codigo. Si el contrato lo declara, la sonda tiene que coincidir; si no, el
    rechazo alcanza. Ninguna constante de este modulo es un codigo de estado, y no hay un default.
    """
    contrato = ((caso or {}).get("tokenMechanism") or {}).get("rejectionContract") or {}
    if contrato.get("defined") is not True:
        return ""
    return declarado(contrato.get("status"))


# -- la evidencia --------------------------------------------------------------

def _evidencias(caso):
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def _de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron."""
    for campo, clave in (("buildId", "id"), ("runtime", "runtime")):
        esperado = (build or {}).get(clave)
        por_la_evidencia = evidencia.get(campo)
        if por_la_evidencia and esperado and por_la_evidencia != esperado:
            return False
    return True


def _usables(refs, indice, build):
    """(usadas, huerfanas, ajenas) de una lista de referencias a evidencia."""
    usadas, huerfanas, ajenas = [], [], []
    for ref in refs or []:
        e = indice.get(ref)
        if e is None:
            huerfanas.append(ref)
        elif not _de_esta_corrida(e, build):
            ajenas.append(ref)
        else:
            usadas.append(e)
    return usadas, sorted(huerfanas), sorted(ajenas)


# -- un endpoint ---------------------------------------------------------------

def _evaluar_sonda(sonda, indice, build, esperado):
    """El estado de una sonda declarada, con su motivo."""
    caso = declarado(sonda.get("case"))
    salida = {"case": caso, "evidenceUsed": [], "issues": []}

    usadas, huerfanas, ajenas = _usables(sonda.get("evidenceRefs"), indice, build)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe" % (EVIDENCIA_HUERFANA, ", ".join(huerfanas)))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(ajenas)))

    pruebas = [e for e in usadas if e.get("sourceType") in EVIDENCIA_QUE_PRUEBA]
    if not pruebas:
        salida.update({"state": PARCIAL, "reason": SIN_SONDA,
                       "detail": "la sonda no la sostiene ninguna evidencia de ejecucion: una "
                                 "dependencia, un middleware configurado, un login, un header "
                                 "parseado, un gateway o un documento no alcanzan"})
        return salida

    reales = [e for e in pruebas if e.get("mode") == REAL]
    if not reales:
        salida.update({"state": PARCIAL, "reason": SONDA_MOCKEADA,
                       "detail": "la unica evidencia de la sonda esta declarada como mockeada: "
                                 "documenta el caso y no prueba que el servicio rechace"})
        return salida

    if caso in NEGATIVAS:
        if sonda.get("rejected") is not True:
            salida.update({"state": FALLA, "reason": ALCANZA_SIN_TOKEN,
                           "detail": "la operacion protegida no fue rechazada"})
            return salida
        # El codigo se compara SOLO si el contrato lo define. Sin contrato, el rechazo alcanza.
        if esperado and declarado(sonda.get("status")) != esperado:
            salida.update({"state": FALLA, "reason": CODIGO_DISTINTO,
                           "detail": "el contrato autoritativo define un codigo de rechazo y la "
                                     "sonda reporta otro"})
            return salida
    elif sonda.get("succeeded") is not True:
        salida.update({"state": PARCIAL, "reason": SIN_SONDA,
                       "detail": "el camino protegido previsto no funciono con un token valido, "
                                 "asi que la verificacion positiva no quedo hecha"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "la sonda corrio de verdad y el borde del servicio se comporto como "
                             "el contrato declara"})
    return salida


def _evaluar_endpoint(endpoint, indice, build, mecanismo_id, esperado):
    """El estado de un camino activo, con su motivo, sus sondas y su evidencia."""
    salida = {"endpointId": declarado(endpoint.get("id")),
              "behaviorId": declarado(endpoint.get("behaviorId")),
              "kind": endpoint.get("kind"),
              "public": endpoint.get("public") is True,
              "probes": [], "issues": []}

    # 🔴 El endpoint publico se resuelve ANTES de mirar la aplicacion del token: lo que hay que
    # saber primero es si esta regla lo gobierna, y eso no lo decide este modulo — lo decide una
    # excepcion declarada con su fuente. Nada se exime solo, y no hay lista de categorias.
    if endpoint.get("public") is True:
        ok, motivo = identidad_valida(endpoint.get("exception"),
                                      "la excepcion de endpoint publico")
        if not ok:
            salida.update({"state": SIN_EXCEPCION, "reason": SIN_EXCEPCION, "detail": motivo})
            return salida
        salida["exception"] = {"id": declarado(endpoint["exception"].get("id")),
                               "source": endpoint["exception"].get("source")}
        salida.update({"state": PASA, "reason": "",
                       "detail": "el endpoint es publico con una excepcion declarada y citada"})
        return salida

    aplicacion = endpoint.get("enforcement") or {}
    por_el_endpoint = declarado(aplicacion.get("mechanism"))
    salida["declaredMechanism"] = por_el_endpoint

    # 🔴 Tres respuestas y no dos, y la del medio es la que importa. Un camino que declara que NO
    # exige token es un camino abierto probado: FALLA. Un camino que no declara si exige es un
    # hueco: queda sin resolver, y el agregado no puede pasar. Convertir lo segundo en lo primero
    # seria inventar el hecho; convertirlo en un PASS seria el falso verde que esta regla busca.
    if aplicacion.get("required") is False:
        salida.update({"state": FALLA, "reason": BYPASS,
                       "detail": "el camino esta activo, llega a un comportamiento protegido y "
                                 "declara que no exige token"})
        return salida
    if aplicacion.get("required") is not True or not por_el_endpoint:
        salida.update({"state": PARCIAL, "reason": EXIGENCIA_SIN_DECLARAR,
                       "detail": "el camino no declara si exige token ni con que mecanismo, y lo "
                                 "que no se declara no se da por protegido ni por abierto"})
        return salida
    if por_el_endpoint != mecanismo_id:
        salida.update({"state": FALLA, "reason": BYPASS,
                       "detail": "el camino declara un mecanismo distinto del que el proyecto "
                                 "declara como su proteccion con token"})
        return salida
    if not declarado(aplicacion.get("point")):
        salida.update({"state": PARCIAL, "reason": SIN_APLICACION,
                       "detail": "el camino no dice donde se aplica la exigencia, y lo que no se "
                                 "dice no se verifica"})
        return salida

    sondas = [s for s in endpoint.get("probes") or [] if declarado(s.get("case")) in SONDAS]
    salida["probes"] = [_evaluar_sonda(s, indice, build, esperado) for s in sondas]
    for s in salida["probes"]:
        salida["issues"].extend(s.get("issues") or [])

    estados = [s["state"] for s in salida["probes"]]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            s["reason"] for s in salida["probes"] if s["state"] == FALLA)})
        return salida

    # 🔴 Una sonda que corrio y no probo nada manda sobre la cuenta de sondas que faltan: el
    # motivo de la raiz -no hay evidencia de ejecucion, o la unica es mockeada- le dice a quien
    # remedia que hacer, y "falta la negativa" lo mandaria a escribir una sonda que ya existe.
    if PARCIAL in estados:
        salida.update({"state": PARCIAL, "reason": next(
            s["reason"] for s in salida["probes"] if s["state"] == PARCIAL)})
        return salida

    # 🔴 Las DOS negativas son obligatorias. La positiva sola es el falso verde mas caro de esta
    # regla: un token valido que funciona no dice nada sobre que pasa sin token.
    cubiertas = {s["case"] for s in salida["probes"] if s["state"] == PASA}
    faltan = [c for c in NEGATIVAS if c not in cubiertas]
    salida["missingProbes"] = faltan
    if faltan:
        salida.update({"state": PARCIAL, "reason": SONDA_INCOMPLETA,
                       "detail": "falta la verificacion negativa de %s, y sin ella no se sabe que "
                                 "pasa cuando la llamada no trae token" % ", ".join(faltan)})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "el camino exige el token del proyecto y las dos llamadas sin token "
                             "valido fueron rechazadas"})
    return salida


# -- el check ------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None, doc=None):
    """El estado de D8 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `caso` es el reporte de una corrida:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "testTarget": {"available": bool},
         "tokenMechanism": {"id", "source", "reference", "enforcementPoint", "tokenSupply",
                            "rejectionContract": {"defined": bool, "status"}},
         "endpoints": {"source", "complete",
                       "items": [{"id", "behaviorId", "kind", "active", "public",
                                  "exception": {"id", "source", "reference"},
                                  "enforcement": {"mechanism", "point"},
                                  "probes": [{"case", "rejected", "succeeded", "status",
                                              "evidenceRefs"}]}]},
         "evidence": [{"evidenceId", "sourceType", "reference", "claim", "buildId", "runtime",
                       "mode"}]}

    `doc` reemplaza la matriz instalada. Es el mismo seam que `matriz.reglas(doc, desde)` y
    `controles.validar(doc, desde)` ya tienen, y es lo unico para lo que esta.

    🔴 Para un build, un mecanismo, un inventario y unos datos fijos, esto devuelve siempre lo
    mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "rule": REGLA, "build": dict(build),
              "endpoints": [], "issues": []}

    # 🔴 El binding primero. Sin la fila no se sabe de que senal depende la regla, y preguntar por
    # el valor de una senal cuyo nombre el modulo se invento es peor que no preguntar.
    datos, motivo = binding(desde, doc)
    if datos is None:
        salida.update({"state": SIN_BINDING, "reason": SIN_BINDING, "detail": motivo,
                       "source": {}, "sourceMissing": True,
                       "issues": ["%s: %s" % (SIN_BINDING, motivo)]})
        return salida

    salida.update({"source": dict(datos["source"]), "signal": datos["signal"],
                   "binding": {"policies": list(datos["policies"]),
                               "checks": list(datos["checks"]),
                               "agents": list(datos["agents"])}})

    senal_id = datos["signal"]
    valor = valor_de_senal(senal, senal_id)
    salida["signalValue"] = valor

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [senal_id],
                       "reason": "no se sabe si el alcance expone un servicio, y lo que no se "
                                 "sabe no se convierte en que no aplica"})
        ajena = identidad_de_senal(senal, senal_id)
        if ajena and ajena != senal_id:
            salida.update({"reason": SENAL_AJENA,
                           "detail": "el dato que llego es la senal `%s`, que no es la de esta "
                                     "regla y no la sustituye" % ajena,
                           "issues": ["%s: llego `%s` en lugar de `%s`"
                                      % (SENAL_AJENA, ajena, senal_id)]})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA,
                       "reason": "no hay endpoints de servicio en alcance"})
        return salida

    if not ((caso or {}).get("testTarget") or {}).get("available"):
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo "
                                 "que no se ejecuto no pasa"})
        return salida

    ok, motivo = inventario_valido(caso)
    if not ok:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA, "detail": motivo,
                       "governedEndpoints": []})
        return salida

    inventario = caso["endpoints"]
    salida["inventory"] = {"source": inventario.get("source"),
                           "endpoints": [declarado(e.get("id")) for e in endpoints(caso)],
                           "inactive": [declarado(e.get("id")) for e in endpoints(caso)
                                        if e.get("active") is not True]}
    completa, motivo_cobertura = clasificacion_completa(caso)

    ok, motivo = mecanismo_valido(caso)
    if not ok:
        salida.update({"state": SIN_MECANISMO, "reason": SIN_MECANISMO, "detail": motivo})
        return salida

    mecanismo = caso["tokenMechanism"]
    # El id que se informa es el normalizado: es el que el modulo usa para comparar, y publicar
    # uno distinto del que se compara es como se lee un FAIL que no se entiende.
    salida["tokenMechanism"] = {"id": declarado(mecanismo.get("id")),
                                "source": mecanismo.get("source"),
                                "enforcementPoint": declarado(mecanismo.get("enforcementPoint"))}
    mecanismo_id = declarado(mecanismo.get("id"))
    esperado = codigo_exigido(caso)
    salida["rejectionContract"] = {"defined": bool(esperado)}

    activos = gobernados(caso)
    salida["governedEndpoints"] = [declarado(e.get("id")) for e in activos]

    indice = _evidencias(caso)
    evaluados = [_evaluar_endpoint(e, indice, build, mecanismo_id, esperado) for e in activos]
    salida["endpoints"] = evaluados
    for e in evaluados:
        salida["issues"].extend(e.get("issues") or [])

    # 🔴 El bypass se DERIVA del comportamiento, no se busca por forma. Un comportamiento que tiene
    # un camino que cumple y otro que no es exactamente el defecto tipico de esta regla, y el
    # agregado no lo puede promediar: un FAIL en cualquier camino manda.
    por_comportamiento = {}
    for e in evaluados:
        por_comportamiento.setdefault(e["behaviorId"], []).append(e)
    mixtos = sorted(b for b, caminos in por_comportamiento.items()
                    if any(c["state"] == FALLA for c in caminos)
                    and any(c["state"] == PASA for c in caminos))
    salida["bypassedBehaviors"] = mixtos
    for b in mixtos:
        salida["issues"].append(
            "%s: el comportamiento %s tiene un camino que exige token y otro que no" % (BYPASS, b))

    estados = [e["state"] for e in evaluados]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            e["reason"] for e in evaluados if e["state"] == FALLA)})
    elif not completa:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": motivo_cobertura})
    elif SIN_EXCEPCION in estados:
        salida.update({"state": SIN_EXCEPCION, "reason": SIN_EXCEPCION,
                       "detail": "hay endpoints declarados publicos sin una excepcion "
                                 "autoritativa, y D8 no exime ninguna categoria por si misma"})
    elif not estados:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": "el inventario no tiene ningun camino activo, y un inventario "
                                 "sin caminos activos no verifica ningun servicio"})
    elif all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL, "reason": next(
            e["reason"] for e in evaluados if e["state"] != PASA)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None, doc=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    Los agentes salen del BINDING, no de una constante: los duenos de la regla los declara la
    matriz. 🔴 Esto no crea skills y no las modifica: dice cuales de las instaladas cubren la
    ejecucion. Si alguna no esta, se ve; no se inventa una.
    """
    from orquestacion import registro_agentes as reg
    datos, _motivo = binding(desde, doc)
    duenos = (datos or {}).get("agents") or [AGENTE_POR_DEFECTO]
    pedidos = [(duenos[0], "dev-security-assessment"),
               (duenos[-1], "dev-backend-implementation"),
               ("dev-quality", "dev-test-automation")]
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
