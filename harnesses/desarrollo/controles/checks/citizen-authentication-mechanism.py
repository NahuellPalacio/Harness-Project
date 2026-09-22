"""Check normativo: la aplicacion ciudadana usa el mecanismo de autenticacion del GCBA.

    source: ES0901 / 6.3 / 7.1 / D1

Contesta UNA pregunta: si el flujo ciudadano usa el mecanismo de autenticacion ciudadana del
GCBA o lo reemplaza por credenciales propias. Como esta integrado ese mecanismo -client ids,
claims, redirect URIs, endpoints, ambientes- es otra cosa, no hay material autoritativo para
verificarlo, y este check no lo promete.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de
latencia y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control
normativo: se evalua contra evidencia y devuelve su estado con el motivo.

🔴 **`PARTIAL` no es un aprobado, y por eso la evidencia ausente no es `FAIL`.** `FAIL` es
para la evidencia que contradice la regla; `PARTIAL`, para la que falta. Se resuelven con
personas distintas: una la arregla quien desarrolla, la otra la completa quien releva. Y no
afloja nada, porque el unico estado que aprueba es `PASS`.

🔴 **La autenticacion institucional no es autenticacion ciudadana.** El mismo apartado del
estandar manda Active Directory y el OpenID de la DGSEI para lo que NO es ciudadano. Son dos
mecanismos para dos publicos: un flujo institucional no satisface D1 y no se cuenta como
flujo ciudadano.

🔴 **D1 no es D2.** La delegacion del ingreso de credenciales tiene su propia regla, su
propia policy y su propio check. Que el apartado de autenticacion hable de OpenID Connect no
mueve esa verificacion aca.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "citizen-authentication-mechanism"
TIPO = "CHECK"
REGLA = "D1"
SENAL = "citizenFacing"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D1"}

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"

# El unico que aprueba es PASA. Los otros cuatro dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER)

CIUDADANO = "CITIZEN"
INTERNO = "INTERNAL"
AUDIENCIAS = (CIUDADANO, INTERNO, "UNRESOLVED")

GCBA = "GCBA_CITIZEN_AUTHENTICATION"
PROPIAS = "CUSTOM_LOCAL_CREDENTIALS"
INSTITUCIONAL = "INSTITUTIONAL_DIRECTORY"
MECANISMOS = (GCBA, PROPIAS, INSTITUCIONAL, "UNRESOLVED")

# Que prueba cada clase de fuente. Una dependencia en el repositorio prueba que algo esta
# instalado, no que el flujo ciudadano lo use: es el atajo mas comodo para dar por cumplido
# lo que nadie miro. La afirmacion de un agente, sola, tampoco alcanza.
FUENTES_SUFICIENTES = ("GCBA_NORMATIVE", "PROJECT_CONFIGURATION", "PROJECT_DOCUMENTATION",
                       "HUMAN_CONFIRMATION")
FUENTES_INSUFICIENTES = ("REPOSITORY_CONFIGURATION", "AGENT_STATEMENT")

SIN_FLUJO = "CITIZEN_AUTHENTICATION_FLOW_NOT_EVIDENCED"
MECANISMO_SIN_IDENTIFICAR = "CITIZEN_AUTHENTICATION_MECHANISM_UNIDENTIFIED"
MECANISMO_REEMPLAZADO = "CITIZEN_AUTHENTICATION_MECHANISM_REPLACED"
EVIDENCIA_INSUFICIENTE = "EVIDENCE_INCOMPLETE"
EVIDENCIA_AJENA = "EVIDENCE_OUT_OF_SCOPE"
HUECO_DE_SKILL = "SPECIALIZED_SKILL_GAP"

SKILL_DE_MIBA = "dev-miba"
AGENTE_DE_MIBA = "dev-integration"


def _valor_de_senal(senal):
    """El valor de `citizenFacing`, venga resuelto, crudo o como booleano viejo."""
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
    """Si la evidencia pertenece a esta aplicacion y a este ambiente.

    Una evidencia que no dice de que aplicacion es, es de esta. Una que lo dice y nombra otra,
    no: sostener un PASS con la configuracion de otro sistema es el error que mas facil pasa
    desapercibido, porque el documento existe y dice lo correcto.
    """
    for campo, esperado_en in (("application", "id"), ("environment", "environment")):
        esperado = (aplicacion or {}).get(esperado_en)
        declarado = evidencia.get(campo)
        if declarado and esperado and declarado != esperado:
            return False
    return True


def _evaluar_flujo(flujo, evidencias, aplicacion):
    """El estado de un flujo ciudadano, con su motivo y la evidencia que lo sostiene."""
    salida = {"flowId": flujo.get("flowId", ""), "mechanism": flujo.get("mechanism"),
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

    mecanismo = flujo.get("mechanism")

    if mecanismo == PROPIAS:
        salida.update({"state": FALLA, "reason": MECANISMO_REEMPLAZADO,
                       "detail": "el flujo ciudadano usa credenciales propias en lugar del "
                                 "mecanismo de autenticacion ciudadana del GCBA"})
        return salida

    if mecanismo == INSTITUCIONAL:
        salida.update({"state": FALLA, "reason": MECANISMO_REEMPLAZADO,
                       "detail": "el flujo ciudadano autentica contra el directorio "
                                 "institucional, que el estandar reserva para lo que no es "
                                 "de uso directo del ciudadano"})
        return salida

    if mecanismo != GCBA:
        salida.update({"state": PARCIAL, "reason": MECANISMO_SIN_IDENTIFICAR,
                       "detail": "hay un flujo ciudadano y la evidencia no identifica que "
                                 "mecanismo usa"})
        return salida

    suficientes = [e for e in usadas if e.get("sourceType") in FUENTES_SUFICIENTES]
    if not suficientes:
        salida.update({"state": PARCIAL, "reason": EVIDENCIA_INSUFICIENTE,
                       "detail": "el flujo declara el mecanismo del GCBA y no lo sostiene "
                                 "ninguna fuente que alcance: una dependencia del "
                                 "repositorio prueba que algo esta instalado, y la "
                                 "afirmacion de un agente no prueba nada"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "el flujo ciudadano usa el mecanismo de autenticacion "
                             "ciudadana del GCBA"})
    return salida


def evaluar(caso, senal=None, desde=None):
    """El estado de D1 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `caso` es lo que declara el relevamiento:

        {"application": {"id": ..., "environment": ...},
         "authenticationFlows": [{"flowId", "audience", "mechanism", "evidenceRefs"}],
         "evidence": [{"evidenceId", "sourceType", "reference", "claim"}]}

    La evidencia entra como dato. Detectarla del repositorio es otro cambio, y sin evidencia
    esto no contesta "cumple": contesta que falta.
    """
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "flows": [], "issues": []}

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [SENAL],
                       "reason": "no se sabe si la aplicacion interactua con el ciudadano, y "
                                 "lo que no se sabe no se convierte en que no aplica"})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA,
                       "reason": "la aplicacion no interactua directamente con el ciudadano"})
        return salida

    evidencias = _evidencias(caso)
    flujos = list((caso or {}).get("authenticationFlows") or [])
    aplicacion = (caso or {}).get("application") or {}

    ciudadanos = [f for f in flujos if f.get("audience") == CIUDADANO]
    otros = [f for f in flujos if f.get("audience") != CIUDADANO]

    if not ciudadanos:
        detalle = ("la aplicacion es ciudadana y no hay evidencia de ningun flujo de "
                   "autenticacion del ciudadano")
        if any(f.get("mechanism") == INSTITUCIONAL for f in otros):
            detalle += ("; la autenticacion institucional que si esta declarada no satisface "
                        "D1: el estandar la reserva para lo que no es de uso directo del "
                        "ciudadano")
        salida.update({"state": PARCIAL, "reason": SIN_FLUJO, "detail": detalle,
                       "ignoredFlows": [f.get("flowId", "") for f in otros]})
        return salida

    salida["ignoredFlows"] = [f.get("flowId", "") for f in otros]
    salida["flows"] = [_evaluar_flujo(f, evidencias, aplicacion) for f in ciudadanos]
    for f in salida["flows"]:
        salida["issues"].extend(f.get("issues") or [])

    estados = [f["state"] for f in salida["flows"]]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": MECANISMO_REEMPLAZADO})
    elif all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL,
                       "reason": next(f["reason"] for f in salida["flows"]
                                      if f["state"] != PASA)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def remediacion(resultado, desde=None):
    """Que hace falta para arreglarlo, cuando arreglarlo exige saber como se integra miBA.

    El estado sale del registro de agentes -`SPECIALIZED_SKILL_GAP` ya existe y no se
    inventa otro-. 🔴 Que el hueco este nombrado NO hace cumplir a D1: el control sigue sin
    pasar y esto dice por que no se puede cerrar hoy.

    🔴 Esto no crea `dev-miba`, no lo instala y no lo completa con informacion inventada.
    """
    estado = (resultado or {}).get("state")
    if estado not in (FALLA, PARCIAL):
        return None

    from orquestacion import registro_agentes as reg
    ruteo = reg.resolver_ruteo(AGENTE_DE_MIBA, SKILL_DE_MIBA, None, desde or __file__)
    if ruteo.get("routable"):
        return None

    return {"control": CONTROL, "source": dict(TRAZA), "state": HUECO_DE_SKILL,
            "skill": SKILL_DE_MIBA, "agent": AGENTE_DE_MIBA,
            "skillValidation": ruteo.get("result"),
            "compliant": False,
            "reason": "la remediacion de D1 exige conocimiento especifico de la integracion "
                      "con miBA, y esa skill esta declarada y todavia no instalada. El hueco "
                      "queda visible y D1 sigue sin cumplir"}
