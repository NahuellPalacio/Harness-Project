"""Check normativo: cada superficie de login habla OpenID Connect con el Keycloak de DGSEI.

    source: ES0902 / 6.2 / 3 / C1

Contesta, por superficie de autenticacion y con evidencia, siete preguntas: si habla OpenID
Connect, si el proveedor es el Keycloak que DGSEI autoriza para ese ambiente, si el cliente esta
registrado en ese servidor, si el flujo es el que corresponde, si el ingreso de credenciales esta
delegado, si hay politica de ASI a la que atarse, y si sigue activo el servicio OpenID anterior.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de latencia
y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control normativo.

🔴 **Por superficie, no por aplicacion.** Un login que cumple no tapa a otro que nadie miro, y un
frontend ciudadano con un backoffice institucional son dos cosas. El inventario es del proyecto y
se instala vacio; vacio con autenticacion presente no cubre nada.

🔴 **Nada se prueba por parecido.** Una dependencia de OIDC, una clase de configuracion del
framework, un README o un ejemplo copiado no prueban el protocolo. Un hostname con `keycloak`
adentro no prueba la autoridad. Un `client_id` no prueba el registro. El default del framework no
prueba el flujo. Cada dimension tiene su tabla de clases de fuente que la sostienen, y lo que no
esta en la tabla no la sostiene.

🔴 **No hay un flujo universal.** ES0902 no define uno y este modulo no nombra ninguno: el flujo lo
declara la superficie y lo sostiene una autoridad que nombre ese mismo flujo.

🔴 **La URL de produccion no se escribe.** El estandar nombra el portal de identidad de produccion;
escribirlo aca seria validarlo, y validarlo en DEV, QA o HML es inyectarlo donde no va. La autoridad
del proveedor es por ambiente y por valor. La unica URL que este modulo nombra es la del servicio
anterior, que es la que hay que detectar.

🔴 **D2 se consume, no se corre.** El ingreso de credenciales lo verifica `authentication-delegation`,
que se ejecuta una vez y sirve a ES0901 D2 y a ES0902 C1. Este check recibe su resultado y busca el
flujo con el id de la superficie. Que D2 pase no hace pasar a C1, y que C1 pase no dice nada de D2.

🔴 **Ciudadano no es institucional, y el harness no elige.** ES0901 v6.3 §8.2 separa los dos
contextos y describe el camino Keycloak/OIDC para el institucional. Una superficie que no es
institucional CON evidencia, y que no trae una reconciliacion autoritativa para ella, queda
`CROSS_STANDARD_INTERPRETATION_REQUIRED`: ni se le fuerza Keycloak ni se la declara fuera de C1. Lo
que la evidencia de un proyecto resuelve vale para esa superficie de ese proyecto y para nada mas.

🔴 **Autenticar no es autorizar.** El resultado lo dice (`authorization.evaluated: false`) y no lo
evalua. Los roles son de la aplicacion; los grupos de AD no se exigen; la restriccion por arbol o
grupo de AD es una recomendacion del estandar y sale como tal.

🔴 **No se inventa ningun parametro de identidad.** Ni tiempo de vida de token, ni claims, ni scopes,
ni algoritmos, ni emisor, ni logout, ni reglas de proteccion de recursos. Sin la politica de ASI,
`ASI_IDENTITY_POLICY_CONTEXT_REQUIRED`.

🔴 **`dev-openid-connect` ejecuta y no es fuente.** La salida de una skill o la afirmacion de un
agente no estan en ninguna tabla. Este modulo no lee el registro de agentes.

🔴 **PASS no aprueba nada mas.** No es C2, no es Vu8, no es D1 ni D8, y no es la aprobacion oficial
de seguridad. Es que las siete preguntas de C1 tienen evidencia en todas las superficies.
"""
import io
import json
import os
import re
import sys
from urllib.parse import urlsplit

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

import rutas                                        # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "oidc-keycloak-integration"
TIPO = "CHECK"
REGLA = "C1"
CLAVE = "ES0902.C1"
SENAL = "authenticationPresent"

ARCHIVO = "authentication-surfaces.json"
SCHEMA = "authentication-surface.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": REGLA}

# El control compartido con D2, por su id. No se importa ni se corre: se lee su resultado.
DELEGACION = "authentication-delegation"

# -- los diecisiete estados, con el nombre exacto que declara el paquete ---------

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "AUTHENTICATION_SURFACE_COVERAGE_UNRESOLVED"
SIN_PROTOCOLO = "OIDC_PROTOCOL_EVIDENCE_UNRESOLVED"
SIN_AUTORIDAD = "KEYCLOAK_PROVIDER_AUTHORITY_UNRESOLVED"
SIN_REGISTRO = "OIDC_CLIENT_REGISTRATION_UNRESOLVED"
SIN_FLUJO = "OIDC_FLOW_CONTEXT_UNRESOLVED"
FLUJO_SIN_AUTORIDAD = "OIDC_FLOW_AUTHORITY_UNRESOLVED"
SIN_POLITICA_ASI = "ASI_IDENTITY_POLICY_CONTEXT_REQUIRED"
ANTERIOR_DETECTADO = "LEGACY_OPENID_PROVIDER_DETECTED"
MIGRACION = "OIDC_MIGRATION_REQUIRED"
SIN_AMBIENTE = "ENVIRONMENT_IDENTITY_CONTEXT_UNRESOLVED"
INTERPRETACION_CRUZADA = "CROSS_STANDARD_INTERPRETATION_REQUIRED"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Diecisiete, y el unico que aprueba es PASA.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_APLICABILIDAD, SIN_COBERTURA, SIN_PROTOCOLO,
           SIN_AUTORIDAD, SIN_REGISTRO, SIN_FLUJO, FLUJO_SIN_AUTORIDAD, SIN_POLITICA_ASI,
           ANTERIOR_DETECTADO, MIGRACION, SIN_AMBIENTE, INTERPRETACION_CRUZADA, SIN_OBJETIVO)

# Motivos que no son estados: dicen por que una superficie quedo donde quedo.
CAPTURA_DIRECTA = "DIRECT_CREDENTIAL_CAPTURE"
DELEGACION_SIN_RESOLVER = "CREDENTIAL_DELEGATION_UNRESOLVED"
PROTOCOLO_AJENO = "NON_OIDC_PROTOCOL"
GOBERNADA_POR_D1 = "ES0901.D1"

SATISFECHA = "SATISFIED"

# -- las dimensiones, y que clase de fuente sostiene cada una --------------------

PROTOCOLO = "OIDC_PROTOCOL"
AUTORIDAD = "PROVIDER_AUTHORITY"
REGISTRO = "CLIENT_REGISTRATION"
AMBIENTE = "ENVIRONMENT_IDENTITY"
FLUJO = "FLOW_AUTHORITY"
POLITICA_ASI = "ASI_IDENTITY_POLICY"
AUDIENCIA = "AUDIENCE"
RECONCILIACION = "CROSS_STANDARD_RECONCILIATION"
DIMENSIONES = (PROTOCOLO, AUTORIDAD, REGISTRO, AMBIENTE, FLUJO, POLITICA_ASI, AUDIENCIA,
               RECONCILIACION)

# 🔴 La tabla es del harness, no del estandar, y por eso esta escrita y no deducida. La metadata
# del proveedor prueba que se habla OIDC con ESE emisor; no prueba que ese emisor sea el de DGSEI,
# y por eso esta en la primera fila y no en la segunda.
SUFICIENTES = {
    PROTOCOLO: ("PROJECT_CONFIGURATION", "PROVIDER_METADATA", "RUNTIME_INTEGRATION_TEST",
                "DGSEI_IDENTITY_REGISTRATION", "IDENTITY_TICKET"),
    AUTORIDAD: ("DGSEI_IDENTITY_REGISTRATION", "IDENTITY_TICKET", "OFFICIAL_IDENTITY_GUIDANCE",
                "ENVIRONMENT_IDENTITY_CONTRACT"),
    REGISTRO: ("DGSEI_IDENTITY_REGISTRATION", "IDENTITY_TICKET"),
    AMBIENTE: ("ENVIRONMENT_IDENTITY_CONTRACT", "DGSEI_IDENTITY_REGISTRATION",
               "OFFICIAL_IDENTITY_GUIDANCE"),
    FLUJO: ("ASI_POLICY", "OFFICIAL_IDENTITY_GUIDANCE", "DGSEI_IDENTITY_REGISTRATION",
            "IDENTITY_TICKET"),
    POLITICA_ASI: ("ASI_POLICY",),
    AUDIENCIA: ("PROJECT_CONTRACT", "IDENTITY_TICKET", "IDENTITY_CHECKPOINT",
                "ARCHITECTURE_DECISION", "OFFICIAL_IDENTITY_GUIDANCE",
                "DGSEI_IDENTITY_REGISTRATION"),
    RECONCILIACION: ("IDENTITY_CHECKPOINT", "IDENTITY_TICKET", "PROJECT_CONTRACT",
                     "ARCHITECTURE_DECISION", "OFFICIAL_IDENTITY_GUIDANCE", "GCBA_NORMATIVE"),
}

# Las que no sostienen ninguna, nombradas para que el motivo pueda decir POR QUE no alcanzan.
INSUFICIENTES = ("REPOSITORY_DEPENDENCY", "FRAMEWORK_CONFIGURATION_CLASS", "README_STATEMENT",
                 "SAMPLE_CONFIGURATION", "HOSTNAME_PATTERN", "CLIENT_ID_LITERAL",
                 "FRAMEWORK_DEFAULT", "AGENT_STATEMENT", "SKILL_OUTPUT", "HISTORICAL_REFERENCE")

HISTORICA = "HISTORICAL_REFERENCE"
PRUEBA_DE_INTEGRACION = "RUNTIME_INTEGRATION_TEST"
NO_DISPONIBLE = "UNAVAILABLE"
CONFIRMADA = "CONFIRMED"

# Las dimensiones cuya evidencia nombra un VALOR que tiene que ser el de la superficie. Una
# autoridad sobre otro proveedor no autoriza a este; una sobre otro flujo no sostiene este.
VALOR_DE_LA_SUPERFICIE = {AUTORIDAD: "currentProvider", FLUJO: "flow",
                          REGISTRO: "clientIdReference", AUDIENCIA: "audience"}

# Y las que ademas tienen que nombrar el ambiente. Sin ambiente no hay proveedor autorizado.
EXIGEN_AMBIENTE = (AUTORIDAD, AMBIENTE)

# 🔴 Y las que tienen que nombrar la SUPERFICIE. Quien resuelve a que publico sirve un login, o
# como se reconcilia con ES0901, lo resuelve para las superficies que nombra: una evidencia sin
# `surfaceIds` valdria para toda superficie del proyecto que la cite, y la cita la escribe quien
# arma el inventario. Eso es una declaracion, no evidencia.
EXIGEN_SUPERFICIE = (AUDIENCIA, RECONCILIACION)

# -- lo que la superficie declara ----------------------------------------------

INSTITUCIONAL = "INSTITUTIONAL"
AMBIENTE_SIN_RESOLVER = "UNRESOLVED"
PROTOCOLOS_OIDC = ("OIDC", "OPENID_CONNECT")
DUENO_DE_ROLES = "APPLICATION"

# Lo que una reconciliacion puede decir de una superficie. Nada mas.
RESUELTA_A_OIDC = "KEYCLOAK_OIDC"
RESUELTA_A_D1 = "ES0901_D1"

# 🔴 El servicio OpenID anterior. Es la UNICA URL del GCBA que este modulo nombra, y se compara por
# host: un host que solo la contiene no es ella.
SERVICIO_ANTERIOR = "https://oauth2-server.apps.buenosaires.gob.ar/"
HOST_ANTERIOR = urlsplit(SERVICIO_ANTERIOR).hostname

RECOMENDACIONES = ({"id": "AD_TREE_GROUP_RESTRICTION", "binding": "RECOMMENDATION",
                    "note": "el estandar recomienda restringir por arbol o grupo de AD; sin una "
                            "politica de ASI que lo vuelva obligatorio, no mueve ningun estado"},)


# -- el inventario --------------------------------------------------------------

def cargar(desde=None):
    """El inventario del proyecto. Vacio si no esta: vacio es valido y no cubre nada."""
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "surfaces": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
    """Errores contra el contrato. Vacio es valido; `None` es que no se pudo validar."""
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return None
    from orquestacion import tools
    armador = tools._armador()
    if armador is None:
        return None
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def superficies(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del inventario instalado."""
    declarado = (caso or {}).get("inventory")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el inventario de superficies no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el inventario de superficies no se pudo validar: falta su schema o el validador"
    if errores:
        return [], "el inventario de superficies no valida: %s" % "; ".join(errores)
    return [s for s in (doc.get("surfaces") or []) if isinstance(s, dict)], ""


# -- la evidencia ---------------------------------------------------------------

# 🔴 La forma de una evidencia del catalogo. El catalogo no pasa por ningun schema, asi que la
# forma se controla aca: un campo que no tiene la forma declarada NO CUENTA. Sin esto, un
# `surfaceIds` escrito como string se compara por substring y nombra superficies que no nombra.
TEXTO, LISTA_DE_TEXTOS = "text", "list-of-text"
FORMA = {"evidenceId": TEXTO, "sourceType": TEXTO, "reference": TEXTO,
         "establishes": LISTA_DE_TEXTOS, "scope": TEXTO, "surfaceIds": LISTA_DE_TEXTOS,
         "environment": TEXTO, "value": TEXTO, "outcome": TEXTO, "resolution": TEXTO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes", "scope")


def bien_formada(evidencia):
    """Si la evidencia tiene la forma declarada: los obligatorios estan, y nada viene torcido."""
    if not isinstance(evidencia, dict):
        return False
    for campo, forma in FORMA.items():
        valor = evidencia.get(campo)
        if valor is None:
            if campo in OBLIGATORIOS:
                return False
            continue
        if forma == TEXTO and not isinstance(valor, str):
            return False
        if forma == LISTA_DE_TEXTOS and not (isinstance(valor, list)
                                            and all(isinstance(v, str) for v in valor)):
            return False
    return True


def _catalogo(caso):
    """(catalogo, repetidos, torcidas). Lo repetido y lo mal formado no cuenta.

    🔴 Un id repetido no cuenta en NINGUNA de sus versiones: elegir una -la primera, la ultima-
    haria depender el resultado del orden de la entrada, y un README con el mismo id que una
    politica de ASI podria taparla o ser tapado segun venga.
    """
    todas = [e for e in (caso or {}).get("evidence") or []]
    torcidas = sorted({str(e.get("evidenceId")) if isinstance(e, dict) else repr(e)
                       for e in todas if not bien_formada(e)})
    sanas = [e for e in todas if bien_formada(e)]
    # El repetido se cuenta sobre TODO lo que trae un id, sano o torcido: una version mal formada
    # con el mismo id tambien deja al id sin saber cual es.
    ids = [e["evidenceId"] for e in todas
           if isinstance(e, dict) and isinstance(e.get("evidenceId"), str)]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    return ({e["evidenceId"]: e for e in sanas if e["evidenceId"] not in repetidos},
            repetidos, torcidas)


def _citadas(superficie, catalogo, campo):
    return [catalogo[r] for r in superficie.get(campo) or [] if r in catalogo]


def _del_alcance(evidencia, superficie):
    """Si la evidencia es de esta superficie de este proyecto. Lo de otro no resuelve esto."""
    if evidencia.get("scope") != superficie.get("scope"):
        return False
    nombradas = evidencia.get("surfaceIds")
    if nombradas is not None and superficie.get("surfaceId") not in nombradas:
        return False
    ambiente = evidencia.get("environment")
    if ambiente is not None and ambiente != superficie.get("environment"):
        return False
    return True


def sostiene(evidencia, dimension, superficie):
    """Si esta evidencia sostiene esta dimension de esta superficie. Las seis condiciones."""
    if dimension not in (evidencia.get("establishes") or []):
        return False
    if evidencia.get("sourceType") not in SUFICIENTES[dimension]:
        return False
    if not (evidencia.get("reference") or "").strip():
        return False
    # 🔴 Una prueba puede decir que NO. Cuenta solo si dice que confirmo: ni la que no tuvo
    # objetivo, ni la que fallo, ni la que no declara resultado. Para el resto de las clases, un
    # `outcome` declarado tiene que ser la confirmacion.
    if evidencia.get("sourceType") == PRUEBA_DE_INTEGRACION or evidencia.get("outcome") is not None:
        if evidencia.get("outcome") != CONFIRMADA:
            return False
    if not _del_alcance(evidencia, superficie):
        return False
    if dimension in EXIGEN_AMBIENTE and evidencia.get("environment") is None:
        return False
    if dimension in EXIGEN_SUPERFICIE and superficie.get("surfaceId") not in (
            evidencia.get("surfaceIds") or []):
        return False
    campo = VALOR_DE_LA_SUPERFICIE.get(dimension)
    if campo is not None:
        propio = superficie.get(campo)
        if dimension == REGISTRO:
            # El registro puede no nombrar el cliente; si lo nombra, tiene que ser este.
            if evidencia.get("value") is not None and evidencia.get("value") != propio:
                return False
        elif propio is None or evidencia.get("value") != propio:
            return False
    return True


def _que_sostiene(dimension, superficie, catalogo):
    campo = "registrationEvidence" if dimension == REGISTRO else "evidence"
    return sorted(e["evidenceId"] for e in _citadas(superficie, catalogo, campo)
                  if sostiene(e, dimension, superficie))


def _es_anterior(proveedor):
    if not isinstance(proveedor, str) or not proveedor.strip():
        return False
    texto = proveedor.strip()
    try:
        host = urlsplit(texto if "//" in texto else "//" + texto).hostname
    except ValueError:
        return False
    return (host or "").rstrip(".") == HOST_ANTERIOR


def _referencias_historicas(superficie, catalogo):
    salida = []
    for e in _citadas(superficie, catalogo, "evidence"):
        if e.get("sourceType") != HISTORICA:
            continue
        if _es_anterior(e.get("value")) or HOST_ANTERIOR in (e.get("reference") or ""):
            salida.append(e["evidenceId"])
    return sorted(salida)


# -- una superficie ---------------------------------------------------------------

def _flujo_bien_formado(flujo):
    return (isinstance(flujo, dict) and isinstance(flujo.get("flowId"), str)
            and bool(flujo["flowId"]) and isinstance(flujo.get("state"), str))


def d2_torcido(delegacion):
    """Si el resultado de D2 viene con algo que no tiene la forma declarada.

    🔴 Un flujo de D2 puede decir que NO. Descartar el torcido y quedarse con los sanos es fallar
    abierto: un FAIL con el `flowId` mal escrito desaparece y el PASS de al lado aprueba. Asi que
    un resultado de D2 torcido en cualquier parte no se lee: la delegacion queda sin resolver en
    todas las superficies, y se dice.
    """
    if delegacion is None:
        return False
    if not isinstance(delegacion, dict) or not isinstance(delegacion.get("flows"), list):
        return True
    return not all(_flujo_bien_formado(f) for f in delegacion["flows"])


def _flujos_de_d2(delegacion):
    """Los flujos de D2, o ninguno si el resultado viene torcido en cualquier parte."""
    if delegacion is None or d2_torcido(delegacion):
        return []
    return list(delegacion["flows"])


def _flujo_de_d2(superficie, delegacion):
    """Lo que D2 dice de esta superficie, juntando TODOS sus flujos con ese id, o `None`.

    🔴 No el primero: D2 evalua por separado dos flujos con el mismo id, y tomar el primero hace
    que uno delegado tape a uno que captura la contrasena segun el orden en que vengan. Cualquier
    FAIL manda; PASS solo si todos pasan; si no, lo que no paso.
    """
    propios = [f for f in _flujos_de_d2(delegacion) if f["flowId"] == superficie.get("surfaceId")]
    if not propios:
        return None
    fallados = sorted((str(f.get("reason") or "") for f in propios if f.get("state") == FALLA))
    if fallados:
        return {"state": FALLA, "reason": fallados[0]}
    if all(f.get("state") == PASA for f in propios):
        return {"state": PASA, "reason": ""}
    otros = sorted(str(f.get("state")) for f in propios if f.get("state") != PASA)
    return {"state": otros[0], "reason": ""}


def _audiencia(superficie, catalogo, descartadas=()):
    """(camino, evidencia). `EVALUATE`, `D1` o el estado cruzado, y lo que lo sostiene.

    🔴 Una reconciliacion puede contradecir a otra, y eso es un "no". Si la superficie cita
    evidencia que no se pudo leer -mal formada o con el id repetido-, no se sabe si esa era la que
    contradecia, asi que la reconciliacion no resuelve: descartarla en silencio le sacaria a ese
    "no" la fuerza que tendria bien escrito.
    """
    if superficie.get("audience") == INSTITUCIONAL:
        usada = _que_sostiene(AUDIENCIA, superficie, catalogo)
        if usada:
            return "EVALUATE", usada
    # Ilegible es todo id citado que no resuelve en el catalogo: mal formado, repetido, con el
    # propio id torcido, o ausente. Cualquiera de esos podia ser la reconciliacion contraria.
    if any(r not in catalogo for r in superficie.get("evidence") or []):
        return INTERPRETACION_CRUZADA, []
    candidatas = [e for e in _citadas(superficie, catalogo, "evidence")
                  if sostiene(e, RECONCILIACION, superficie)]
    # Una reconciliacion con autoridad cuya resolucion no se reconoce -`es0901_d1`, `ES0901-D1`-
    # tambien puede ser la contraria: no se descarta, bloquea.
    if any(e.get("resolution") not in (RESUELTA_A_OIDC, RESUELTA_A_D1) for e in candidatas):
        return INTERPRETACION_CRUZADA, []
    reconciliaciones = candidatas
    resoluciones = sorted({e.get("resolution") for e in reconciliaciones})
    if len(resoluciones) == 1:
        camino = "EVALUATE" if resoluciones[0] == RESUELTA_A_OIDC else "D1"
        return camino, sorted(e["evidenceId"] for e in reconciliaciones)
    return INTERPRETACION_CRUZADA, []


def evaluar_superficie(superficie, catalogo, delegacion, descartadas=()):
    """El estado de una superficie, con cada dimension, su evidencia y sus observaciones."""
    rol = superficie.get("applicationRoleOwnership")
    salida = {"surfaceId": superficie.get("surfaceId"), "scope": superficie.get("scope"),
              "audience": superficie.get("audience"),
              "environment": superficie.get("environment"),
              "dimensions": {}, "evidenceUsed": {}, "states": [], "issues": [],
              "migration": {"required": False, "applied": False},
              "legacyReferences": _referencias_historicas(superficie, catalogo),
              "authorization": {"evaluated": False, "roleAssignmentOwner": rol},
              "recommendations": [dict(r) for r in RECOMENDACIONES]}
    if rol is not None and rol != DUENO_DE_ROLES:
        salida["issues"].append("la asignacion de roles figura a cargo de `%s`; es "
                                "responsabilidad de la aplicacion, y autenticar no la prueba"
                                % rol)

    flujo_d2 = _flujo_de_d2(superficie, delegacion)
    salida["credentialDelegation"] = {"control": DELEGACION,
                                      "flowState": (flujo_d2 or {}).get("state"),
                                      "flowReason": (flujo_d2 or {}).get("reason")}

    # 🔴 Los dos FAIL que no dependen de la audiencia van primero: estan prohibidos en los dos
    # contextos, y no hace falta saber de quien es el login para saber que no va.
    if _es_anterior(superficie.get("currentProvider")):
        salida["migration"]["required"] = True
        return _con(salida, FALLA, [ANTERIOR_DETECTADO, MIGRACION],
                    "el proveedor activo es el servicio OpenID anterior (%s); una version nueva "
                    "tiene que migrar. No se toca ninguna configuracion" % HOST_ANTERIOR)
    if superficie.get("credentialEntryDelegated") is False:
        return _con(salida, FALLA, [], "%s: la aplicacion recibe la credencial del usuario"
                    % CAPTURA_DIRECTA)
    if flujo_d2 is not None and flujo_d2.get("state") == FALLA:
        return _con(salida, FALLA, [], "%s en FAIL para este flujo: %s"
                    % (DELEGACION, flujo_d2.get("reason") or "-"))

    camino, usada = _audiencia(superficie, catalogo, descartadas)
    salida["evidenceUsed"][AUDIENCIA] = usada
    if camino == INTERPRETACION_CRUZADA:
        return _con(salida, INTERPRETACION_CRUZADA, [],
                    "la superficie no es institucional con evidencia y no hay reconciliacion "
                    "autoritativa entre ES0902 C1 y ES0901 para ella. No se le fuerza Keycloak "
                    "ni se la declara fuera de C1")
    if camino == "D1":
        salida["governedBy"] = GOBERNADA_POR_D1
        return _con(salida, NO_APLICA, [],
                    "la evidencia de este proyecto resuelve esta superficie por el camino "
                    "ciudadano. Vale para esta superficie y para nada mas")

    pendientes = []

    # Vacio o nulo es no saberlo, no otro protocolo. La grafia no decide: `oidc` es OIDC.
    protocolo = re.sub(r"[\s-]+", "_", (superficie.get("protocol") or "").strip()).upper() or None
    if protocolo is not None and protocolo not in PROTOCOLOS_OIDC:
        return _con(salida, FALLA, [], "%s: la superficie declara `%s`, y C1 exige OpenID "
                    "Connect" % (PROTOCOLO_AJENO, protocolo))
    _dimension(salida, PROTOCOLO, superficie, catalogo, pendientes, SIN_PROTOCOLO,
               "no hay evidencia de configuracion real, del proveedor o de una prueba de "
               "integracion de que esto sea OpenID Connect; una libreria no lo prueba")
    if salida["dimensions"][PROTOCOLO] == SIN_PROTOCOLO and any(
            e.get("sourceType") == PRUEBA_DE_INTEGRACION and e.get("outcome") == NO_DISPONIBLE
            and _del_alcance(e, superficie)
            for e in _citadas(superficie, catalogo, "evidence")):
        salida["dimensions"][PROTOCOLO] = SIN_OBJETIVO
        pendientes[-1] = (SIN_OBJETIVO, "la prueba de integracion no tuvo objetivo disponible")

    if superficie.get("environment") == AMBIENTE_SIN_RESOLVER:
        salida["dimensions"][AMBIENTE] = SIN_AMBIENTE
        salida["evidenceUsed"][AMBIENTE] = []
        pendientes.append((SIN_AMBIENTE, "no se sabe de que ambiente es la superficie"))
    else:
        _dimension(salida, AMBIENTE, superficie, catalogo, pendientes, SIN_AMBIENTE,
                   "no hay contrato de identidad para este ambiente; la URL de otro ambiente "
                   "no se trae")
    _dimension(salida, AUTORIDAD, superficie, catalogo, pendientes, SIN_AUTORIDAD,
               "no consta que `%s` sea el Keycloak que DGSEI autoriza para %s; la forma del "
               "hostname no lo prueba" % (superficie.get("currentProvider"),
                                          superficie.get("environment")))
    _dimension(salida, REGISTRO, superficie, catalogo, pendientes, SIN_REGISTRO,
               "no hay evidencia de registro del cliente en el servidor que corresponde; un "
               "`client_id` no lo prueba")
    if superficie.get("flow") is None:
        salida["dimensions"][FLUJO] = SIN_FLUJO
        salida["evidenceUsed"][FLUJO] = []
        pendientes.append((SIN_FLUJO, "la superficie no declara que flujo usa"))
    else:
        _dimension(salida, FLUJO, superficie, catalogo, pendientes, FLUJO_SIN_AUTORIDAD,
                   "ninguna autoridad dice que `%s` sea el flujo que corresponde a este "
                   "cliente; el default del framework no lo dice" % superficie.get("flow"))

    if (flujo_d2 or {}).get("state") == PASA:
        salida["dimensions"]["CREDENTIAL_DELEGATION"] = SATISFECHA
    else:
        salida["dimensions"]["CREDENTIAL_DELEGATION"] = PARCIAL
        pendientes.append((PARCIAL, "%s: no hay resultado de `%s` en PASS para este flujo; "
                           "lo que el inventario declara no alcanza"
                           % (DELEGACION_SIN_RESOLVER, DELEGACION)))

    _dimension(salida, POLITICA_ASI, superficie, catalogo, pendientes, SIN_POLITICA_ASI,
               "no hay politica de ASI de autenticacion, autorizacion y proteccion de recursos "
               "a la que atar esta superficie; no se inventa")

    if pendientes:
        estados = []
        for estado, _ in pendientes:
            if estado not in estados:
                estados.append(estado)
        return _con(salida, pendientes[0][0], estados,
                    " | ".join(motivo for _, motivo in pendientes))
    return _con(salida, PASA, [], "")


def _dimension(salida, dimension, superficie, catalogo, pendientes, estado, motivo):
    usada = _que_sostiene(dimension, superficie, catalogo)
    salida["evidenceUsed"][dimension] = usada
    if usada:
        salida["dimensions"][dimension] = SATISFECHA
    else:
        salida["dimensions"][dimension] = estado
        pendientes.append((estado, motivo))


def _con(salida, estado, estados, motivo):
    salida["state"] = estado
    salida["states"] = list(estados) if estados else ([estado] if estado != PASA else [])
    salida["reason"] = motivo
    return salida


# -- la evaluacion ----------------------------------------------------------------

def _valor_de_senal(senal):
    """El valor de `authenticationPresent`, venga resuelta, cruda o como booleano."""
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def evaluar(caso, senal=None, delegacion=None, desde=None):
    """El estado de C1 para un proyecto, superficie por superficie.

    `caso`:

        {"inventory": {"version", "surfaces": [...]},   # opcional: reemplaza el instalado
         "evidence": [{"evidenceId", "sourceType", "reference", "establishes": [...],
                       "scope", "surfaceIds"?, "environment"?, "value"?, "outcome"?,
                       "resolution"?}],
         "detectedSurfaces": [surfaceId, ...]}           # lo que otra fuente vio

    `senal` es `authenticationPresent`. `delegacion` es el resultado de `authentication-delegation`
    ya ejecutado: este check no lo corre.

    🔴 Para el mismo caso, la misma senal y la misma delegacion, esto devuelve siempre lo mismo,
    en cualquier orden que vengan las superficies y la evidencia.
    """
    entrada = caso if isinstance(caso, dict) else {}
    salida = {"control": CONTROL, "rule": REGLA, "ruleKey": CLAVE, "source": dict(TRAZA),
              "signal": SENAL, "surfaces": [], "issues": [],
              "coverage": {"inventoried": [], "detected": [], "missing": [], "duplicated": []}}

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor
    if valor == _senales.SIN_RESOLVER:
        return _cerrar(salida, SIN_APLICABILIDAD,
                       "no se sabe si la aplicacion autentica usuarios, y lo que no se sabe no "
                       "se convierte en que no aplica")
    if valor == _senales.FALSA:
        return _cerrar(salida, NO_APLICA, "la aplicacion no autentica usuarios")

    lista, problema = superficies(entrada, desde)
    if problema:
        salida["issues"].append(problema)
        return _cerrar(salida, SIN_COBERTURA, problema)

    ids = [s.get("surfaceId") for s in lista]
    # 🔴 `detectedSurfaces` dice "hay una superficie que no cubriste": puede decir que no. Si viene
    # torcido no se descarta: la cobertura queda sin resolver.
    detectadas = entrada.get("detectedSurfaces")
    detectadas_torcidas = detectadas is not None and not (
        isinstance(detectadas, list) and all(isinstance(d, str) and d for d in detectadas))
    vistas = sorted({f["flowId"] for f in _flujos_de_d2(delegacion)}
                    | ({d for d in detectadas or []} if not detectadas_torcidas else set()))
    # Con D2 ilegible no se sabe que superficies vio, asi que la cobertura tampoco consta.
    salida["coverage"] = {"inventoried": sorted(set(ids)), "detected": vistas,
                          "missing": sorted(set(vistas) - set(ids)),
                          "duplicated": sorted({i for i in ids if ids.count(i) > 1}),
                          "detectedMalformed": detectadas_torcidas,
                          "delegationUnreadable": d2_torcido(delegacion)}
    if detectadas_torcidas:
        salida["issues"].append("`detectedSurfaces` no tiene la forma declarada -una lista de "
                                "ids-; no se lee, y la cobertura queda sin resolver")

    if d2_torcido(delegacion):
        salida["issues"].append("el resultado de `%s` trae flujos que no tienen la forma "
                                "declarada; no se lee, y la delegacion queda sin resolver en "
                                "todas las superficies" % DELEGACION)
    catalogo, repetidos, torcidas = _catalogo(entrada)
    if repetidos:
        salida["issues"].append("ids de evidencia repetidos, que no cuentan en ninguna de sus "
                                "versiones: %s" % ", ".join(repetidos))
    if torcidas:
        salida["issues"].append("evidencia que no tiene la forma declarada, y que por eso no "
                                "cuenta: %s" % ", ".join(torcidas))
    descartadas = set(repetidos) | set(torcidas)
    for s in lista:
        huerfanas = sorted(r for campo in ("evidence", "registrationEvidence")
                           for r in s.get(campo) or []
                           if r not in catalogo and r not in descartadas)
        if huerfanas:
            salida["issues"].append("`%s` cita evidencia que no existe: %s"
                                    % (s.get("surfaceId"), ", ".join(huerfanas)))
    salida["issues"].sort()
    salida["surfaces"] = sorted((evaluar_superficie(s, catalogo, delegacion, descartadas)
                                 for s in lista),
                                key=lambda r: (str(r.get("surfaceId")),
                                               json.dumps(r, sort_keys=True, default=str)))

    estados = [r["state"] for r in salida["surfaces"]]
    if FALLA in estados:
        return _cerrar(salida, FALLA, "hay al menos una superficie en FAIL; las que cumplen no "
                                      "la tapan")
    if not lista:
        return _cerrar(salida, SIN_COBERTURA, "hay autenticacion y el inventario de superficies "
                                              "esta vacio")
    if (salida["coverage"]["missing"] or salida["coverage"]["duplicated"]
            or detectadas_torcidas or salida["coverage"]["delegationUnreadable"]):
        return _cerrar(salida, SIN_COBERTURA,
                       "el inventario no cubre todas las superficies: faltan %s, repetidas %s"
                       % (", ".join(salida["coverage"]["missing"]) or "-",
                          ", ".join(salida["coverage"]["duplicated"]) or "-"))
    abiertos = [e for e in estados if e not in (PASA, NO_APLICA)]
    if not abiertos:
        if PASA in estados:
            return _cerrar(salida, PASA, "")
        return _cerrar(salida, NO_APLICA, "todas las superficies estan resueltas por el camino "
                                          "ciudadano con evidencia de su proyecto")
    distintos = sorted(set(abiertos))
    return _cerrar(salida, distintos[0] if len(distintos) == 1 else PARCIAL,
                   "superficies sin resolver: %s"
                   % ", ".join("%s (%s)" % (r["surfaceId"], r["state"])
                               for r in salida["surfaces"] if r["state"] in abiertos))


def _cerrar(salida, estado, motivo):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    for r in salida["surfaces"]:
        todos.update(r.get("states") or [])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA
