"""Check normativo: el ingreso de credenciales se delega segun el apartado de autenticacion.

    source: ES0901 / 6.3 / 7.1 / D2

Contesta DOS preguntas y no una tercera: si el usuario escribe su credencial en la aplicacion o
en el servicio de identidad del GCBA, y si ese servicio es el que corresponde al contexto. Que
una aplicacion deba ser ciudadana lo decide D1; aca se toma el contexto como dato.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de latencia
y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control normativo.

🔴 **Delegar es donde se escribe la credencial, no quien la valida despues.** Un formulario
propio que llama a una API no es delegacion: la aplicacion vio la contrasena. Por eso
`credentialEntry` es un hecho separado del proveedor, y un `APPLICATION_OWNED` con proveedor
declarado sigue siendo `FAIL`.

🔴 **La audiencia no se adivina.** Si hay autenticacion y no se sabe a quien autentica, el
estado es `AUTHENTICATION_CONTEXT_UNRESOLVED`. No es un `PARTIAL`: un `PARTIAL` dice "falta
evidencia de esto que miro"; esto dice "no se que tengo que mirar".

🔴 **Lo que ES0901 delega en ES0902 no se inventa.** Este harness no tiene ES0902 como fuente
declarada -hay un extracto que no cerro como fiel y ningun `es0902*.json` en `reglas/`-. Lo que
dependa de ella sale `ES0902_CONTEXT_REQUIRED`, y eso NO anula la verificacion de la delegacion,
que ES0901 sostiene por si misma.

🔴 **D2 no es D1.** Este resultado no nombra el control de D1, no emite su veredicto y no
decide si la aplicacion es ciudadana.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "authentication-delegation"
TIPO = "CHECK"
REGLA = "D2"
SENAL = "authenticationPresent"
# Contexto secundario: se REUSA la senal de D1, no se redefine. Un segundo detector de lo mismo
# con otro nombre es la forma mas rapida de que dos reglas contesten distinto del mismo sistema.
SENAL_DE_CONTEXTO = "citizenFacing"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D2"}

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
CONTEXTO_SIN_RESOLVER = "AUTHENTICATION_CONTEXT_UNRESOLVED"
ES0902 = "ES0902_CONTEXT_REQUIRED"

# Siete, y el unico que aprueba es PASA. Los otros seis dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, CONTEXTO_SIN_RESOLVER, ES0902)

CIUDADANA = "CITIZEN"
INSTITUCIONAL = "INSTITUTIONAL"
AUDIENCIAS = (CIUDADANA, INSTITUCIONAL, "UNRESOLVED")

DELEGADO = "DELEGATED"
PROPIO = "APPLICATION_OWNED"
INGRESOS = (DELEGADO, PROPIO, "UNRESOLVED")

CIUDADANO = "GCBA_CITIZEN_AUTHENTICATION"
DGSEI = "DGSEI_OPENID_KEYCLOAK"
VIEJO = "LEGACY_OPENID_ENDPOINT"
LOCAL = "APPLICATION_LOCAL"
PROVEEDORES = (CIUDADANO, DGSEI, VIEJO, LOCAL, "UNRESOLVED")

# Que proveedor le corresponde a cada contexto. Es lo unico que el estandar dice por si mismo, y
# se mira porque el paquete exige que el mecanismo delegado corresponda al contexto aplicable.
ESPERADO = {CIUDADANA: CIUDADANO, INSTITUCIONAL: DGSEI}

# Que prueba cada clase de fuente. La misma particion que usa el check de D1: una dependencia
# prueba que algo esta instalado y la afirmacion de un agente no prueba nada.
FUENTES_SUFICIENTES = ("GCBA_NORMATIVE", "PROJECT_CONFIGURATION", "PROJECT_DOCUMENTATION",
                       "HUMAN_CONFIRMATION")
FUENTES_INSUFICIENTES = ("REPOSITORY_CONFIGURATION", "REPOSITORY_DEPENDENCY", "AGENT_STATEMENT")

CAPTURA_DIRECTA = "DIRECT_CREDENTIAL_CAPTURE"
PROVEEDOR_NO_AUTORIZADO = "LEGACY_PROVIDER_NOT_AUTHORIZED"
DESTINO_EQUIVOCADO = "DELEGATION_TARGET_MISMATCH"
PROVEEDOR_SIN_EVIDENCIA = "PROVIDER_NOT_EVIDENCED"
INGRESO_SIN_RESOLVER = "CREDENTIAL_ENTRY_UNRESOLVED"
EVIDENCIA_INSUFICIENTE = "EVIDENCE_INCOMPLETE"
EVIDENCIA_AJENA = "EVIDENCE_OUT_OF_SCOPE"
SIN_FLUJO = "AUTHENTICATION_FLOW_NOT_EVIDENCED"
HUECO_DE_SKILL = "SPECIALIZED_SKILL_GAP"

# Lo que ES0901 §8 remite a ES0902. La lista dice que preguntas este check NO contesta; no dice
# que exige ES0902, que es lo que no se puede saber sin la norma. Declararla es lo contrario de
# inventarla: sin ella, "esto suena a seguridad" quedaria a criterio de quien corre el check.
VALIDACIONES_DE_ES0902 = ("PASSWORD_POLICY", "TOKEN_SIGNING_REQUIREMENTS", "SESSION_SECURITY",
                          "CIPHER_REQUIREMENTS", "SECURITY_ASSESSMENT")

SKILL_DE_MIBA = "dev-miba"
SKILL_DE_OPENID = "dev-openid-connect"
AGENTE = "dev-integration"


def _valor_de_senal(senal):
    """El valor de una senal, venga resuelta, cruda o como booleano viejo."""
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def _evidencias(caso):
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def _del_alcance(evidencia, aplicacion):
    """Si la evidencia pertenece a esta aplicacion y a este ambiente."""
    for campo, esperado_en in (("application", "id"), ("environment", "environment")):
        esperado = (aplicacion or {}).get(esperado_en)
        declarado = evidencia.get(campo)
        if declarado and esperado and declarado != esperado:
            return False
    return True


def audiencia_de(flujo, contexto):
    """La audiencia del flujo, o la de la senal secundaria, o nada.

    🔴 El orden importa y no se invierte: lo que declara el flujo le gana al contexto general.
    Una aplicacion ciudadana puede tener un backoffice, y al reves.
    """
    declarada = (flujo or {}).get("audience")
    if declarada in (CIUDADANA, INSTITUCIONAL):
        return declarada, "flow"
    valor = _valor_de_senal(contexto)
    if valor == _senales.VERDADERA:
        return CIUDADANA, SENAL_DE_CONTEXTO
    if valor == _senales.FALSA:
        return INSTITUCIONAL, SENAL_DE_CONTEXTO
    return None, ""


def _evaluar_flujo(flujo, evidencias, aplicacion, contexto):
    """El estado de un flujo de autenticacion, con su motivo y su evidencia."""
    salida = {"flowId": flujo.get("flowId", ""),
              "credentialEntry": flujo.get("credentialEntry"),
              "provider": flujo.get("provider"),
              "evidenceUsed": [], "issues": []}

    usadas, ajenas, huerfanas = [], [], []
    for ref in flujo.get("evidenceRefs") or []:
        e = evidencias.get(ref)
        if e is None:
            huerfanas.append(ref)
        elif not _del_alcance(e, aplicacion):
            ajenas.append(ref)
        else:
            usadas.append(e)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: el flujo referencia evidencia que no existe: %s"
                                % (EVIDENCIA_INSUFICIENTE, ", ".join(sorted(huerfanas))))
    if ajenas:
        salida["issues"].append("%s: %s pertenece a otra aplicacion o a otro ambiente"
                                % (EVIDENCIA_AJENA, ", ".join(sorted(ajenas))))

    ingreso = flujo.get("credentialEntry")
    proveedor = flujo.get("provider")

    # La audiencia se resuelve siempre, aunque el estado se decida antes de necesitarla: quien
    # lea el resultado -y quien busque que skill remedia esto- tiene que saber de que contexto
    # era el flujo, y un FAIL temprano no es razon para perder ese dato.
    audiencia, origen = audiencia_de(flujo, contexto)
    salida["audience"] = audiencia
    salida["audienceFrom"] = origen

    # La captura directa esta prohibida en los dos contextos, asi que se decide sin saber la
    # audiencia: no hace falta saber a quien le sacan la contrasena para saber que no va.
    if ingreso == PROPIO:
        salida.update({"state": FALLA, "reason": CAPTURA_DIRECTA,
                       "detail": "la aplicacion recibe la credencial del usuario. Que despues "
                                 "la mande a otro lado no la vuelve delegada"})
        return salida

    if proveedor == LOCAL:
        salida.update({"state": FALLA, "reason": CAPTURA_DIRECTA,
                       "detail": "el flujo declara delegar y su proveedor es la propia "
                                 "aplicacion, que no es delegar"})
        return salida

    if proveedor == VIEJO:
        salida.update({"state": FALLA, "reason": PROVEEDOR_NO_AUTORIZADO,
                       "detail": "el endpoint de identidad anterior no emite credenciales "
                                 "nuevas: delegar ahi es delegar al lugar equivocado"})
        return salida

    if ingreso != DELEGADO:
        salida.update({"state": PARCIAL, "reason": INGRESO_SIN_RESOLVER,
                       "detail": "la evidencia no dice donde escribe la credencial el usuario"})
        return salida

    if audiencia is None:
        salida.update({"state": CONTEXTO_SIN_RESOLVER, "reason": CONTEXTO_SIN_RESOLVER,
                       "detail": "hay autenticacion y no se sabe si es del ciudadano o "
                                 "institucional, asi que no se sabe que mecanismo se le "
                                 "exige. No se adivina"})
        return salida

    salida["expectedProvider"] = ESPERADO[audiencia]

    if proveedor not in (CIUDADANO, DGSEI):
        salida.update({"state": PARCIAL, "reason": PROVEEDOR_SIN_EVIDENCIA,
                       "detail": "hay delegacion y la evidencia no identifica a que proveedor"})
        return salida

    if proveedor != ESPERADO[audiencia]:
        salida.update({"state": FALLA, "reason": DESTINO_EQUIVOCADO,
                       "detail": "se delega a un mecanismo autorizado del GCBA que no es el "
                                 "que corresponde a esta audiencia"})
        return salida

    suficientes = [e for e in usadas if e.get("sourceType") in FUENTES_SUFICIENTES]
    if not suficientes:
        salida.update({"state": PARCIAL, "reason": EVIDENCIA_INSUFICIENTE,
                       "detail": "el proveedor esta declarado y no lo sostiene ninguna fuente "
                                 "que alcance: una dependencia prueba que algo esta "
                                 "instalado, y la afirmacion de un agente no prueba nada"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "el ingreso de credenciales se delega al mecanismo que "
                             "corresponde a esta audiencia"})
    return salida


def diferidas(caso):
    """Las validaciones pedidas que dependen de ES0902. Se nombran; no se contestan."""
    salida = []
    for v in (caso or {}).get("requestedValidations") or []:
        vid = v.get("id") if isinstance(v, dict) else v
        fuente = v.get("standard") if isinstance(v, dict) else None
        if fuente == "ES0902" or vid in VALIDACIONES_DE_ES0902:
            salida.append({"id": vid, "state": ES0902,
                           "reason": "ES0901 remite este requisito a ES0902, que este harness "
                                     "no tiene como fuente declarada. No se infiere"})
    return salida


def evaluar(caso, senal=None, contexto=None, desde=None):
    """El estado de D2 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `senal` es `authenticationPresent`; `contexto` es `citizenFacing` y es secundario: no decide
    la aplicabilidad, sirve para saber que mecanismo se esperaba cuando el flujo no lo dice.
    """
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "flows": [], "issues": [], "deferred": diferidas(caso)}

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [SENAL],
                       "reason": "no se sabe si la aplicacion autentica usuarios, y lo que no "
                                 "se sabe no se convierte en que no aplica"})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA,
                       "reason": "la aplicacion no tiene responsabilidad de autenticacion"})
        return salida

    flujos = list((caso or {}).get("authenticationFlows") or [])
    pedidas = list((caso or {}).get("requestedValidations") or [])

    # Todo lo pedido es de ES0902: no hay nada que ES0901 sostenga por si mismo que contestar.
    if pedidas and len(salida["deferred"]) == len(pedidas) and not flujos:
        salida.update({"state": ES0902,
                       "reason": "lo unico que se pidio depende de ES0902"})
        return salida

    if not flujos:
        salida.update({"state": PARCIAL, "reason": SIN_FLUJO,
                       "detail": "hay autenticacion declarada y no hay evidencia de ningun "
                                 "flujo que mirar"})
        return salida

    evidencias = _evidencias(caso)
    aplicacion = (caso or {}).get("application") or {}
    salida["flows"] = [_evaluar_flujo(f, evidencias, aplicacion, contexto) for f in flujos]
    for f in salida["flows"]:
        salida["issues"].extend(f.get("issues") or [])

    estados = [f["state"] for f in salida["flows"]]
    # 🔴 El orden es deliberado: un camino directo activo manda sobre cualquier otro flujo que
    # cumpla. El que cumple no tapa al que no.
    if FALLA in estados:
        salida.update({"state": FALLA,
                       "reason": next(f["reason"] for f in salida["flows"]
                                      if f["state"] == FALLA)})
    elif all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    elif CONTEXTO_SIN_RESOLVER in estados and all(
            e in (PASA, CONTEXTO_SIN_RESOLVER) for e in estados):
        salida.update({"state": CONTEXTO_SIN_RESOLVER, "reason": CONTEXTO_SIN_RESOLVER})
    else:
        salida.update({"state": PARCIAL,
                       "reason": next(f["reason"] for f in salida["flows"]
                                      if f["state"] not in (PASA,))})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def remediacion(resultado, desde=None):
    """Que skill hace falta para arreglarlo, y si esta.

    Un flujo ciudadano necesita conocimiento operativo del servicio de autenticacion ciudadana,
    que es lo que `dev-miba` tendria y no tiene. Uno institucional necesita OpenID Connect, que
    `dev-openid-connect` si cubre.

    🔴 `dev-openid-connect` NO reemplaza a `dev-miba`. Rutear ahi el trabajo ciudadano seria
    fingir que el conocimiento especifico existe porque existe uno parecido.

    🔴 Que el hueco este nombrado no hace cumplir a D2.
    """
    estado = (resultado or {}).get("state")
    if estado not in (FALLA, PARCIAL, CONTEXTO_SIN_RESOLVER):
        return None

    # Si no se sabe de que contexto era, se asume el ciudadano: es el que tiene el hueco de
    # conocimiento, y suponer el otro seria rutear a una skill que no cubre lo que falta.
    audiencias = {f.get("audience") for f in (resultado or {}).get("flows") or []}
    ciudadano = CIUDADANA in audiencias or not audiencias - {None}

    from orquestacion import registro_agentes as reg
    skill = SKILL_DE_MIBA if ciudadano else SKILL_DE_OPENID
    ruteo = reg.resolver_ruteo(AGENTE, skill, None, desde or __file__)

    salida = {"control": CONTROL, "source": dict(TRAZA), "skill": skill, "agent": AGENTE,
              "skillValidation": ruteo.get("result"), "routable": bool(ruteo.get("routable")),
              "compliant": False}
    if ruteo.get("routable"):
        salida.update({"state": "ROUTABLE",
                       "reason": "la remediacion es trabajo de OpenID Connect institucional y "
                                 "la skill que lo cubre esta instalada"})
        return salida
    salida.update({"state": HUECO_DE_SKILL,
                   "reason": "la remediacion exige conocimiento operativo del servicio de "
                             "autenticacion ciudadana, y esa skill esta declarada y todavia "
                             "no instalada. No se rutea a la de OpenID institucional como si "
                             "fuera lo mismo"})
    return salida
