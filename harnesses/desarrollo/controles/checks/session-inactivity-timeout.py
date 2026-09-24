"""Check normativo: una sesion inactiva vence sola, aparte del token de OpenID.

    source: ES0902 / 6.2 / 6 / Vu4

    "Toda sesion en stand by, tiene que tener un tiempo limite para su utilizacion. Esto,
     independientemente del limite de tiempo que posee el token de autenticacion del OpenID."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Juzga la sesion de la aplicacion inactiva, y solo esa.** El access token, el refresh token y la
sesion del proveedor se informan por separado y, solos, no aprueban nada. Que el SSO del proveedor
siga activo no es FAIL.

🔴 **La configuracion no es el comportamiento, y la pantalla no es el recurso.** Cuenta la evidencia
de que la sesion vieja deja de servir despues del intervalo. Un modal de "sesion expirada" con la API
aceptando la sesion vieja es una sesion viva.

🔴 **Ninguna duracion y ninguna actividad se inventan.** El valor se conserva como referencia, sin
juzgarlo; que cuenta como actividad lo dice una politica citada del proyecto o no se sabe.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Un FAIL exige evidencia
citada y legible, igual que un PASS. Una prueba insegura o sin objetivo no aprueba ni hace FAIL.

🔴 **No se prueba nada ni se guarda nada.** Una prueba cuenta si fue autorizada, fuera de produccion,
con una identidad de prueba dedicada, sin cuenta real, sin registrar secretos y sin debilitar el
timeout de produccion. Nada con forma de credencial sale.

🔴 **Vu4 no es Vu3 ni C1.** Las superficies son las de C1, con su cargador, y la senal de Vu3 enciende
la de Vu4; ninguno de los dos resultados aprueba a este.
"""
import importlib.util
import io
import json
import os
import sys

_CONTROLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN = os.path.join(os.path.dirname(_CONTROLES), "bin")
if _BIN not in sys.path:
    sys.path.insert(0, _BIN)
if os.path.join(_CONTROLES, "lib") not in sys.path:
    sys.path.insert(0, os.path.join(_CONTROLES, "lib"))

import rutas                                        # noqa: E402
import evidencia as _ev                             # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "session-inactivity-timeout"
POLICY = "session-inactivity-timeout-required"
TIPO = "CHECK"
REGLA = "Vu4"
CLAVE = "ES0902.Vu4"
SENAL = "sessionPresent"

ARCHIVO = "session-inactivity-timeout.json"
SCHEMA = "session-inactivity-timeout.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = ("Toda sesión en stand by, tiene que tener un tiempo límite para su utilización. "
                "Esto, independientemente del límite de tiempo que posee el token de autenticación "
                "del OpenID.")


# 🔴 Las superficies son las de C1, con su cargador, y la senal por superficie de Vu3 es la de Vu3.
# Se importan los modulos; no se corre su evaluacion.
def _modulo(archivo, alias):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_SUPERFICIES = _modulo("oidc-keycloak-integration.py", "_vu4_inventario_de_superficies")
_CIERRE = _modulo("browser-close-session-termination.py", "_vu4_senal_de_vu3")

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "SESSION_COVERAGE_UNRESOLVED"
SIN_COBERTURA_DE_ROLES = "SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED"
SIN_SEMANTICA = "SESSION_ACTIVITY_SEMANTICS_UNRESOLVED"
SIN_VENCIMIENTO = "SESSION_INACTIVITY_TIMEOUT_UNRESOLVED"
SOLO_TOKEN = "TOKEN_TIMEOUT_ONLY"
SESION_USABLE = "INACTIVE_SESSION_REMAINS_USABLE"
PRUEBA_INSEGURA = "SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_COBERTURA, SIN_COBERTURA_DE_ROLES,
           SIN_SEMANTICA, SIN_VENCIMIENTO, SOLO_TOKEN, SESION_USABLE, PRUEBA_INSEGURA, SIN_OBJETIVO)
# Las tres formas de fallar. El agregado informa la de la falla.
FALLAS = (FALLA, SOLO_TOKEN, SESION_USABLE)
RESUELTAS = (PASA, NO_APLICA)

# -- lo que dice el registro ------------------------------------------------------------

MODELO_SIN_RESOLVER = "UNRESOLVED"
CONFIGURADO, NO_CONFIGURADO = "CONFIGURED", "NOT_CONFIGURED"
SI, NO = "YES", "NO"
DEFINIDA, NO_REQUERIDA = "DEFINED", "NOT_REQUIRED"
SIN_RESOLVER = "UNRESOLVED"

RECHAZADA = "SESSION_REJECTED"
REAUTENTICAR = "REAUTHENTICATION_REQUIRED"
NUEVA = "NEW_SESSION_REQUIRED"
USABLE = "OLD_INACTIVE_SESSION_STILL_USABLE"
DEL_TOKEN = "TOKEN_TIMEOUT_ONLY"
CUMPLEN = (RECHAZADA, REAUTENTICAR, NUEVA)
NO_CUMPLEN = (USABLE, DEL_TOKEN)
RESULTADOS = CUMPLEN + NO_CUMPLEN

CAMPOS_DEL_TOKEN = ("accessTokenTimeoutRef", "refreshTokenTimeoutRef", "idpSessionTimeoutRef")

# -- los cinco dominios ----------------------------------------------------------------------

INACTIVIDAD = "APPLICATION_INACTIVITY"
ACCESS_TOKEN = "OIDC_ACCESS_TOKEN"
REFRESH_TOKEN = "OIDC_REFRESH_TOKEN"
SSO_DEL_PROVEEDOR = "IDP_SSO_SESSION"
DE_LA_APLICACION = "APPLICATION_SESSION"
DOMINIOS = (INACTIVIDAD, ACCESS_TOKEN, REFRESH_TOKEN, SSO_DEL_PROVEEDOR, DE_LA_APLICACION)
INFORMADOS = (ACCESS_TOKEN, REFRESH_TOKEN, SSO_DEL_PROVEEDOR)

# -- lo que establece una evidencia, y que clase lo sostiene ----------------------------------

SESION = "APPLICATION_SESSION"
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
ROLES = "SESSION_ROLE_SCOPE"
VENCIMIENTO = "INACTIVITY_TIMEOUT"
INDEPENDENCIA = "TIMEOUT_INDEPENDENCE"
SEMANTICA = "ACTIVITY_SEMANTICS"
OBSERVACION = "ACTIVITY_RESET_OBSERVATION"
COMPORTAMIENTO = "POST_TIMEOUT_BEHAVIOR"

# Lo que, si no se pudo leer, igual impide el PASS aunque no se lo cite: dice que no.
DICEN_QUE_NO = (NO_CONFIGURADO, NO) + NO_CUMPLEN

PRUEBA = "AUTHORIZED_RUNTIME_TEST"
# 🔴 Las tablas son del harness, no del estandar.
AUTORIDADES = ("ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT", "PROJECT_CONTRACT",
               "PROJECT_SESSION_POLICY", "OFFICIAL_ASSESSMENT_FINDING",
               "OTHER_AUTHORITATIVE_EVIDENCE")
FUENTES_DE_COMPORTAMIENTO = (PRUEBA, "INTEGRATION_TEST", "UNIT_TEST", "PROTECTED_ENDPOINT_CHECK",
                             "SESSION_STORE_OBSERVATION", "ASSESSMENT_FINDING",
                             "OTHER_AUTHORITATIVE_EVIDENCE")
FUENTES_DE_CONFIGURACION = AUTORIDADES + FUENTES_DE_COMPORTAMIENTO + ("CONFIGURATION",
                                                                      "SOURCE_CODE")
# Las que no sostienen el vencimiento, nombradas para que la salida diga por que.
INSUFICIENTES = ("CONFIGURATION", "SOURCE_CODE", "UI_OBSERVATION", "CLIENT_TIMER",
                 "OIDC_TOKEN_CONFIGURATION", "IDP_SSO_CONFIGURATION", "README_STATEMENT",
                 "AGENT_STATEMENT", "SKILL_OUTPUT")
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "REPOSITORY_DEPENDENCY")

CONFIRMADA = "CONFIRMED"
NO_DISPONIBLE = "UNAVAILABLE"
PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "domain": _ev.TEXTO, "targets": _ev.LISTA,
         "sessions": _ev.LISTA, "value": _ev.TEXTO, "values": _ev.LISTA, "outcome": _ev.TEXTO,
         "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO, "testIdentityRef": _ev.TEXTO,
         "realUserAccount": _ev.BOOLEANO, "rawSecretsLogged": _ev.BOOLEANO,
         "productionTimeoutWeakened": _ev.BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes", "domain")


def catalogo(caso):
    """El catalogo de `evidencia.py`, y un dominio que no es uno de los cinco lo deja mal formado."""
    cat, crudas, repetidos, torcidas = _ev.catalogo(caso, FORMA, OBLIGATORIOS)
    for ident in [i for i, e in cat.items() if e["domain"] not in DOMINIOS]:
        torcidas = sorted(set(torcidas) | {_ev.etiqueta(cat.pop(ident))})
    return cat, crudas, repetidos, torcidas


def prueba_segura(e, entrada):
    """Los motivos por los que una prueba no era segura. Vacio es segura. No ejecuta nada."""
    motivos = []
    if e.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    ambiente = e.get("environment")
    if ambiente in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    elif ambiente == PRODUCCION:
        motivos.append("PRODUCTION")
    elif ambiente not in AMBIENTES_DE_PRUEBA:
        motivos.append("ENVIRONMENT_UNKNOWN")
    elif entrada is None:
        motivos.append("SESSION_NOT_REGISTERED")
    elif ambiente != entrada.get("environment"):
        motivos.append("ENVIRONMENT_MISMATCH")
    if not (e.get("testIdentityRef") or "").strip():
        motivos.append("NO_DEDICATED_TEST_IDENTITY")
    if e.get("realUserAccount") is True:
        motivos.append("REAL_USER_ACCOUNT")
    if e.get("rawSecretsLogged") is True:
        motivos.append("RAW_SECRETS_LOGGED")
    if e.get("productionTimeoutWeakened") is True:
        motivos.append("PRODUCTION_TIMEOUT_WEAKENED")
    return sorted(motivos)


def _lectura(e, entrada):
    """(cuenta, bloqueo, motivos). La misma compuerta para lo que dice que si y que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO, []
        motivos = prueba_segura(e, entrada)
        if motivos:
            return False, PRUEBA_INSEGURA, motivos
        return e.get("outcome") == CONFIRMADA, None, []
    return e.get("outcome") in (None, CONFIRMADA), None, []


def _de_la_sesion(e, sid):
    return _ev.en(sid, e.get("sessions"))


def _de_la_superficie(e, sid):
    return _ev.en(sid, e.get("targets"))


def _legibles(cat, entrada, establece, dominio, fuentes, valores):
    """Lo legible sobre la sesion que establece `establece`, en `dominio`, de una clase que sirve."""
    sid = entrada.get("sessionId")
    return [e for e in sorted(cat.values(), key=lambda x: x["evidenceId"])
            if establece in e["establishes"] and _de_la_sesion(e, sid)
            and e["domain"] == dominio and e["sourceType"] in fuentes
            and e.get("value") in valores and _lectura(e, entrada)[0]]


# -- los registros ------------------------------------------------------------------------------

def cargar(desde=None):
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "sessions": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
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


def entradas(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del registro instalado."""
    declarado = (caso or {}).get("sessions")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el registro de vencimiento por inactividad no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de vencimiento por inactividad no se pudo validar"
    if errores:
        return [], ("el registro de vencimiento por inactividad no valida contra su schema: %d "
                    "errores" % len(errores))
    return list(doc.get("sessions") or []), ""


# -- la senal -------------------------------------------------------------------------------------

HAY, NO_HAY, NO_SE = "SESSION", "NO_SESSION", "UNRESOLVED"


def _sesion_de(superficie, propias, de_vu3, cat, crudas):
    sid = superficie.get("surfaceId")
    sobre = [e for e in cat.values() if SESION in e["establishes"] and _de_la_superficie(e, sid)
             and e["domain"] == DE_LA_APLICACION and e["sourceType"] not in DEBILES]
    legibles = [e for e in sobre if _lectura(e, superficie)[0]]
    enciende = (any(p.get("sessionModel") != MODELO_SIN_RESOLVER for p in propias)
                or de_vu3 or any(e.get("value") == PRESENTE for e in legibles))
    apaga = [e["evidenceId"] for e in legibles
             if e.get("value") == AUSENTE and e["sourceType"] in AUTORIDADES]
    # Lo que dice que HAY sesion y no se pudo leer -una prueba insegura- no deja apagar.
    if any(e.get("value") == PRESENTE and e not in legibles for e in sobre):
        apaga = []
    if enciende and apaga:
        return NO_SE
    if enciende:
        return HAY
    if apaga and not propias and not _ev.ilegibles_sobre(sid, cat, crudas):
        return NO_HAY
    return NO_SE


def derivar(caso, autenticacion=None, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    lista, problema = _SUPERFICIES.superficies(entrada, desde)
    registradas, problema_registro = entradas(entrada, desde)
    # La senal de Vu3, superficie por superficie, con SU registro y su catalogo.
    vu3 = _CIERRE.derivar({"inventory": entrada.get("inventory"),
                           "sessions": entrada.get("browserSessions"),
                           "evidence": entrada.get("evidence"),
                           "detectedSurfaces": entrada.get("detectedSurfaces")}, autenticacion, desde)
    con_vu3 = {_ev.nfc(p["surfaceId"]) for p in vu3["surfaces"] if p["session"] == _CIERRE.HAY}
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    # 🔴 Los ids se normalizan UNA vez, antes de contar (Vu2, tercer pase).
    ids = [_ev.nfc(s.get("surfaceId")) for s in lista]
    sesiones = [_ev.nfc(e.get("sessionId")) for e in registradas]
    detectadas = entrada.get("detectedSurfaces")
    detectadas_torcidas = detectadas is not None and not (
        isinstance(detectadas, list) and all(isinstance(d, str) and d for d in detectadas))
    vistas = sorted({_ev.nfc(d) for d in detectadas or []}) if not detectadas_torcidas else []
    superficies = []
    for s in lista:
        propias = [e for e in registradas if _ev.igual(e.get("surfaceRef"), s.get("surfaceId"))]
        superficies.append({"surfaceId": s.get("surfaceId"), "scope": s.get("scope"),
                            "environment": s.get("environment"),
                            "session": _sesion_de(s, propias, _ev.nfc(s.get("surfaceId")) in con_vu3,
                                                  cat, crudas),
                            "entries": len(propias)})
    conocidas = {str(i) for i in ids}
    cobertura = {
        "inventoried": sorted(conocidas), "detected": vistas,
        "missing": sorted(set(vistas) - conocidas),
        "duplicated": sorted({str(i) for i in ids if ids.count(i) > 1}),
        "detectedMalformed": detectadas_torcidas,
        "duplicatedSessions": sorted({str(i) for i in sesiones if sesiones.count(i) > 1}),
        "sessionsOutsideInventory": sorted({str(e.get("sessionId")) for e in registradas
                                            if str(_ev.nfc(e.get("surfaceRef"))) not in conocidas}),
        "surfacesWithoutSession": sorted({str(p["surfaceId"]) for p in superficies
                                          if p["session"] == HAY and not p["entries"]}),
        "registryUnreadable": bool(problema_registro),
        "browserRegistryUnreadable": bool(vu3["registryProblem"]),
        "unresolved": sorted(str(p["surfaceId"]) for p in superficies if p["session"] == NO_SE)}
    completa = not (cobertura["missing"] or cobertura["duplicated"] or detectadas_torcidas
                    or cobertura["duplicatedSessions"] or problema_registro
                    or vu3["registryProblem"])
    vacios = not registradas and not vu3["registry"]
    if problema:
        valor = _senales.SIN_RESOLVER
    elif (any(e.get("sessionModel") != MODELO_SIN_RESOLVER for e in registradas)
          or any(p["session"] == HAY for p in superficies)):
        valor = _senales.VERDADERA
    elif superficies and completa and vacios and all(p["session"] == NO_HAY for p in superficies):
        valor = _senales.FALSA
    elif (not superficies and completa and vacios and not vistas and not (repetidos or torcidas)
          and _SUPERFICIES._valor_de_senal(autenticacion) == _senales.FALSA):
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    for p in superficies:
        del p["entries"]
    return {"value": valor, "surfaces": _ev.ordenadas(superficies), "inventory": lista,
            "registry": registradas, "coverage": cobertura, "complete": completa,
            "problem": problema, "registryProblem": problema_registro, "catalog": cat,
            "raw": crudas, "repeated": repetidos, "malformed": torcidas}


def senal(caso, autenticacion=None, desde=None):
    d = derivar(caso, autenticacion, desde)
    evidencia = []
    if d["value"] in (_senales.VERDADERA, _senales.FALSA):
        buscada = HAY if d["value"] == _senales.VERDADERA else NO_HAY
        for p in d["surfaces"]:
            if p["session"] != buscada:
                continue
            evidencia.append({"evidenceId": "surface:%s" % p["surfaceId"],
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "authentication-surfaces.json#%s" % p["surfaceId"],
                              "claim": "la superficie `%s` (%s, %s) %s sesion de la aplicacion" % (
                                  p["surfaceId"], p["scope"], p["environment"],
                                  "tiene" if buscada == HAY else "no tiene"),
                              "supports": d["value"]})
        if buscada == HAY:
            for e in d["registry"]:
                if e.get("sessionModel") == MODELO_SIN_RESOLVER:
                    continue
                evidencia.append({"evidenceId": "session:%s" % e.get("sessionId"),
                                  "sourceType": "REPOSITORY_CONFIGURATION",
                                  "reference": "%s#%s" % (ARCHIVO, e.get("sessionId")),
                                  "claim": "la sesion `%s` (%s) esta declarada en el registro" % (
                                      e.get("sessionId"), e.get("sessionModel")),
                                  "supports": d["value"]})
        if not evidencia:
            evidencia.append({"evidenceId": "authenticationPresent",
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "authenticationPresent",
                              "claim": "la aplicacion no autentica usuarios", "supports": d["value"]})
    return _ev.depurar(_senales.producir(SENAL, _ev.ordenadas(evidencia), {"type": "DETERMINISTIC"},
                                         d["value"], desde))


def _combinar(derivado, externo):
    if externo is None:
        return derivado
    valor = _SUPERFICIES._valor_de_senal(externo)
    if valor == derivado:
        return valor
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- el bloqueo, uno solo ----------------------------------------------------------------------

def _bloqueos(cat, entrada, citados, registradas=()):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan: las que se citan, o las que
    dicen que no. Con `entrada`, las de esa sesion; sin ella, las que no nombran ninguna registrada.

    Una prueba ajena e insegura que dice que la sesion vence no mueve nada."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        if entrada is not None and not _de_la_sesion(e, entrada.get("sessionId")):
            continue
        if entrada is None and any(_de_la_sesion(e, r.get("sessionId")) for r in registradas):
            continue
        _, bloqueo, m = _lectura(e, entrada)
        if bloqueo and (_ev.id_de(e) in citados or e.get("value") in DICEN_QUE_NO):
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return SIN_VENCIMIENTO


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan la sesion, el PASS y el NOT_APPLICABLE.

    Lo que no se pudo leer y pesa impide el PASS y tambien el NOT_APPLICABLE; un FAIL no se toca:
    bloquear impide aprobar, no tapa lo que falla. Parchar una rama sola dejo pasar en Vu3 un
    NOT_APPLICABLE contra una prueba insegura (refutador, pase 2)."""
    if estado in FALLAS:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), ("una prueba que se cita, o que dice que la sesion no vence, no se "
                                    "pudo leer")
    if ilegibles and estado in RESUELTAS:
        return SIN_VENCIMIENTO, ("hay evidencia ilegible sobre la sesion, y esa podia ser la que "
                                 "decia que no vence")
    return estado, motivo


# -- una sesion, en el orden de la spec -----------------------------------------------------------

def _paso_modelo(entrada, *_):
    if entrada.get("sessionModel") == MODELO_SIN_RESOLVER:
        return SIN_VENCIMIENTO, "el modelo de la sesion no esta resuelto"
    return None, ""


def _paso_vencimiento(entrada, cat, citados, salida):
    vence = entrada.get("inactivityTimeout") or {}
    refs = salida["tokenRefs"]
    falla_sin_vencimiento = SOLO_TOKEN if refs else FALLA
    declarado = vence.get("status")
    estados = _legibles(cat, entrada, VENCIMIENTO, INACTIVIDAD, FUENTES_DE_CONFIGURACION,
                        (CONFIGURADO, NO_CONFIGURADO))
    no = [e["evidenceId"] for e in estados if e["value"] == NO_CONFIGURADO]
    si = [e["evidenceId"] for e in estados if e["value"] == CONFIGURADO]
    no_citadas = [i for i in no if _ev.nfc(i) in citados]
    if declarado == NO_CONFIGURADO:
        if no_citadas and not si:
            salida["evidenceUsed"]["inactivityTimeout"] = no_citadas
            return falla_sin_vencimiento, ("una evidencia citada establece que la aplicacion no tiene "
                                           "vencimiento propio" + (", solo el del token" if refs else ""))
        if si:
            salida["contradictedBy"].extend(si)
            return SIN_VENCIMIENTO, ("el registro dice que no hay vencimiento propio y una evidencia "
                                     "dice que si; no se elige")
        return SIN_VENCIMIENTO, "que no haya vencimiento propio no consta con evidencia citada"
    if declarado != CONFIGURADO:
        return SIN_VENCIMIENTO, "el vencimiento por inactividad no esta resuelto"
    if no_citadas:
        salida["evidenceUsed"]["inactivityTimeout"] = no_citadas
        return falla_sin_vencimiento, ("una evidencia citada establece que la aplicacion no tiene "
                                       "vencimiento propio")
    if no:
        salida["contradictedBy"].extend(no)
        return SIN_VENCIMIENTO, ("una evidencia dice que no hay vencimiento propio y el registro dice "
                                 "que si; no se elige")
    valor = vence.get("valueRef")
    if not isinstance(valor, str) or not valor.strip():
        return SIN_VENCIMIENTO, "el valor del vencimiento no consta, y no se infiere"
    if _ev.nfc(valor) in refs:
        return SOLO_TOKEN, "el valor del vencimiento es el del token: salio del token"
    salida["evidenceUsed"]["inactivityTimeout"] = [i for i in si if _ev.nfc(i) in citados]

    independiente = vence.get("independentFromOidcTokenTimeout")
    dichas = _legibles(cat, entrada, INDEPENDENCIA, INACTIVIDAD, FUENTES_DE_CONFIGURACION, (SI, NO))
    dependen = [e["evidenceId"] for e in dichas if e["value"] == NO]
    no_dependen = [e["evidenceId"] for e in dichas if e["value"] == SI]
    dependen_citadas = [i for i in dependen if _ev.nfc(i) in citados]
    if independiente == NO:
        if dependen_citadas and not no_dependen:
            salida["evidenceUsed"]["independence"] = dependen_citadas
            return SOLO_TOKEN, "una evidencia citada establece que el vencimiento es el del token"
        if no_dependen:
            salida["contradictedBy"].extend(no_dependen)
            return SIN_VENCIMIENTO, ("el registro dice que el vencimiento depende del token y una "
                                     "evidencia dice que no; no se elige")
        return SIN_VENCIMIENTO, "que el vencimiento dependa del token no consta con evidencia citada"
    if independiente != SI:
        return SIN_VENCIMIENTO, "no consta si el vencimiento es independiente del token"
    if dependen_citadas:
        salida["evidenceUsed"]["independence"] = dependen_citadas
        return SOLO_TOKEN, "una evidencia citada establece que el vencimiento es el del token"
    if dependen:
        salida["contradictedBy"].extend(dependen)
        return SIN_VENCIMIENTO, ("una evidencia dice que el vencimiento es el del token y el registro "
                                 "dice que no; no se elige")
    salida["evidenceUsed"]["independence"] = [i for i in no_dependen if _ev.nfc(i) in citados]
    return None, ""


def _paso_semantica(entrada, cat, citados, salida):
    actividad = entrada.get("activitySemantics") or {}
    declarada = actividad.get("status")
    if declarada not in (DEFINIDA, NO_REQUERIDA):
        return SIN_SEMANTICA, "que cuenta como actividad no esta resuelto"
    ref = actividad.get("sourceRef")
    e = cat.get(_ev.nfc(ref)) if isinstance(ref, str) else None
    sid = entrada.get("sessionId")
    # Lo que se declara observacion no es politica, aunque tambien diga ACTIVITY_SEMANTICS (E-61).
    if not (e is not None and SEMANTICA in e["establishes"]
            and OBSERVACION not in e["establishes"] and e["sourceType"] in AUTORIDADES
            and e["domain"] == INACTIVIDAD and e.get("value") == declarada
            and (not e.get("sessions") or _de_la_sesion(e, sid)) and _lectura(e, entrada)[0]):
        return SIN_SEMANTICA, ("que cuenta como actividad lo define solo una politica citada del "
                               "proyecto; una observacion del mouse, del polling o del refresh no")
    salida["evidenceUsed"]["activitySemantics"] = [e["evidenceId"]]
    salida["activitySemantics"]["events"] = sorted(e.get("values") or [])
    return None, ""


def _paso_comportamiento(entrada, cat, citados, salida):
    declarado = (entrada.get("verification") or {}).get("result")
    sid = entrada.get("sessionId")
    cumplen, fallan, dudosas = [], [], []
    for e in sorted(cat.values(), key=lambda x: x["evidenceId"]):
        if (COMPORTAMIENTO not in e["establishes"] or not _de_la_sesion(e, sid)
                or e["domain"] != INACTIVIDAD or e["sourceType"] not in FUENTES_DE_COMPORTAMIENTO
                or e.get("value") not in RESULTADOS):
            continue
        cuenta, bloqueo, _ = _lectura(e, entrada)
        if bloqueo:
            continue
        if not cuenta:
            salida["issues"].append("`%s` no esta confirmada" % e["evidenceId"])
            if e["value"] in NO_CUMPLEN:
                dudosas.append(e["evidenceId"])
            continue
        (fallan if e["value"] in NO_CUMPLEN else cumplen).append(e)
    contra = sorted([e["evidenceId"] for e in fallan] + dudosas)
    fallan_citadas = [e for e in fallan if _ev.id_de(e) in citados]
    if fallan_citadas:
        salida["evidenceUsed"]["behavior"] = sorted(e["evidenceId"] for e in fallan_citadas)
        if any(e["value"] == USABLE for e in fallan_citadas):
            return SESION_USABLE, ("una evidencia citada muestra que un recurso protegido acepta la "
                                   "sesion vieja despues del intervalo")
        return SOLO_TOKEN, "una evidencia citada muestra que solo vence el token"
    if declarado in NO_CUMPLEN:
        if cumplen:
            salida["contradictedBy"].extend(e["evidenceId"] for e in cumplen)
            return SIN_VENCIMIENTO, ("el registro dice que la sesion vieja sigue sirviendo y una "
                                     "evidencia dice que no; no se elige")
        return _abierto(salida["blockedBy"]), ("el registro dice que la sesion vieja sigue sirviendo "
                                               "y ninguna evidencia citada y legible lo establece")
    if declarado in CUMPLEN:
        apoyo = sorted(e["evidenceId"] for e in cumplen
                       if _ev.id_de(e) in citados and e["value"] == declarado)
        if apoyo and not contra:
            salida["evidenceUsed"]["behavior"] = apoyo
            return None, ""
        salida["contradictedBy"].extend(contra)
    return _abierto(salida["blockedBy"]), (
        "no consta con evidencia de comportamiento que la sesion vieja deje de servir despues del "
        "intervalo; la configuracion, la pantalla o el reloj del cliente no alcanzan")


PASOS = (_paso_modelo, _paso_vencimiento, _paso_semantica, _paso_comportamiento)


def _contexto(entrada, cat):
    """Lo que se informa y no decide: los otros dominios, las observaciones y lo insuficiente."""
    sid = entrada.get("sessionId")
    salida = {d: [] for d in INFORMADOS}
    salida.update({"activityObservations": [], "insufficient": []})
    for e in sorted(cat.values(), key=lambda x: x["evidenceId"]):
        if not _de_la_sesion(e, sid):
            continue
        if e["domain"] in salida:
            salida[e["domain"]].append(e["evidenceId"])
        if OBSERVACION in e["establishes"]:
            salida["activityObservations"].append(e["evidenceId"])
        if e["sourceType"] in INSUFICIENTES:
            salida["insufficient"].append(e["evidenceId"])
    return salida


def evaluar_sesion(entrada, d):
    """Una sesion del registro, sola: su estado y la evidencia que lo sostiene, por id."""
    cat, crudas = d["catalog"], d["raw"]
    sid = entrada.get("sessionId")
    vence = entrada.get("inactivityTimeout") or {}
    token = entrada.get("oidcTimeouts") or {}
    actividad = entrada.get("activitySemantics") or {}
    prueba = entrada.get("verification") or {}
    citados = _ev.claves(entrada.get("evidence")) | _ev.claves([actividad.get("sourceRef")])
    conocidas = {_ev.nfc(s.get("surfaceId")) for s in d["inventory"]}
    salida = {"sessionId": sid, "surfaceRef": entrada.get("surfaceRef"),
              "inInventory": _ev.nfc(entrada.get("surfaceRef")) in conocidas,
              "roles": sorted(r for r in entrada.get("roles") or [] if isinstance(r, str)),
              "environment": entrada.get("environment"),
              "sessionModel": entrada.get("sessionModel"),
              # 🔴 El vencimiento de la aplicacion y los del token, por separado.
              "applicationInactivityTimeout": {
                  "status": vence.get("status"), "valueRef": vence.get("valueRef"),
                  "independentFromOidcTokenTimeout": vence.get("independentFromOidcTokenTimeout"),
                  "enforcementLayer": vence.get("enforcementLayer")},
              "oidcTimeouts": {c: token.get(c) for c in CAMPOS_DEL_TOKEN},
              "activitySemantics": {"status": actividad.get("status"),
                                    "sourceRef": actividad.get("sourceRef"), "events": []},
              "verification": {"result": prueba.get("result"),
                               "evidenceMode": prueba.get("evidenceMode")},
              "evidenceUsed": {"inactivityTimeout": [], "independence": [],
                               "activitySemantics": [], "behavior": []},
              "contradictedBy": [], "issues": [],
              "supportingContext": _contexto(entrada, cat),
              "tokenRefs": sorted({_ev.nfc(v) for v in (token.get(c) for c in CAMPOS_DEL_TOKEN)
                                   if isinstance(v, str) and v.strip()})}
    if not salida["inInventory"]:
        salida["issues"].append("la superficie `%s` no esta en el inventario de C1"
                                % entrada.get("surfaceRef"))
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, entrada, citados)
    pasos = [paso(entrada, cat, citados, salida) for paso in PASOS]
    # 🔴 En el orden de la spec, y lo que falla no lo tapa un paso anterior sin resolver.
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = [p for p in pasos if p[0] is not None]
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | set(_ev.ilegibles_sobre(sid, cat, crudas)))
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre la sesion: %s" % ", ".join(ilegibles))
    final, motivo = _bloquear(estado, motivo, salida["blockedBy"], ilegibles)
    if final != estado:
        # Lo bloqueado no se sostiene con nada: no queda evidencia usada.
        salida["evidenceUsed"] = {k: [] for k in salida["evidenceUsed"]}
    salida["contradictedBy"] = sorted(set(salida["contradictedBy"]))
    salida["issues"] = sorted(set(salida["issues"]))
    del salida["tokenRefs"]
    salida["state"] = final
    salida["states"] = sorted(({p[0] for p in pasos if p[0] is not None} | {final}) - {PASA})
    salida["reason"] = motivo
    return salida


def _roles_sin_politica(d, cat):
    """Los roles que una evidencia autoritativa citada da para una superficie y ninguna entrada cubre."""
    faltan = {}
    for s in d["inventory"]:
        sup = s.get("surfaceId")
        propias = [e for e in d["registry"] if _ev.igual(e.get("surfaceRef"), sup)]
        citados = set()
        for p in propias:
            citados |= _ev.claves(p.get("evidence"))
        cubiertos = {_ev.nfc(r) for p in propias for r in p.get("roles") or []
                     if isinstance(r, str)}
        for e in cat.values():
            if (ROLES in e["establishes"] and _de_la_superficie(e, sup)
                    and e["domain"] == DE_LA_APLICACION and e["sourceType"] in AUTORIDADES
                    and _ev.id_de(e) in citados and _lectura(e, s)[0]):
                sin = sorted({_ev.nfc(r) for r in e.get("values") or []} - cubiertos)
                if sin:
                    faltan.setdefault(str(sup), set()).update(sin)
    return {k: sorted(v) for k, v in sorted(faltan.items())}


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, autenticacion=None, desde=None):
    """El estado de Vu4, sesion por sesion.

    `caso`:

        {"inventory": {...},        # el de C1; opcional
         "sessions": {...},         # el registro de Vu4; opcional
         "browserSessions": {...},  # el registro de Vu3; opcional
         "evidence": [...],         # el catalogo, cerrado
         "detectedSurfaces": [...]}
    """
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "sessions": [], "issues": [], "coverage": {}}
    d = derivar(caso, autenticacion, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    for problema in (d["problem"], d["registryProblem"]):
        if problema:
            salida["issues"].append("el inventario de superficies no valida contra su schema"
                                    if problema.startswith("el inventario de superficies no valida")
                                    else problema)
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    for sid in d["coverage"]["sessionsOutsideInventory"]:
        salida["issues"].append("la sesion `%s` no tiene su superficie en el inventario de C1" % sid)
    salida["issues"].sort()
    d["coverage"]["rolesWithoutPolicy"] = _roles_sin_politica(d, d["catalog"])
    salida["coverage"] = d["coverage"]
    citados = set()
    for e in d["registry"]:
        citados |= _ev.claves(e.get("evidence")) | _ev.claves(
            [(e.get("activitySemantics") or {}).get("sourceRef")])
    sueltos, motivos = _bloqueos(d["catalog"], None, citados, d["registry"])
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos

    if valor == _senales.SIN_RESOLVER:
        estado, motivo = SIN_APLICABILIDAD, "no consta si hay una sesion de la aplicacion"
    elif valor == _senales.FALSA:
        estado, motivo = NO_APLICA, "no hay sesion de la aplicacion"
    elif d["problem"]:
        estado, motivo = SIN_COBERTURA, "el inventario de superficies no se pudo leer"
    else:
        # 🔴 Cada entrada es una sesion y se evalua sola, tambien la que C1 no inventaria.
        salida["sessions"] = _ev.ordenadas(evaluar_sesion(e, d) for e in d["registry"])
        estado, motivo = _agregado(salida["sessions"], d)
    final, motivo = _bloquear(estado, motivo, sueltos, [])
    return _cerrar(salida, final, motivo, estado)


def _agregado(sesiones, d):
    estados = [s["state"] for s in sesiones]
    fallas = sorted({e for e in estados if e in FALLAS})
    if fallas:
        return (fallas[0] if len(fallas) == 1 else FALLA,
                "al menos una sesion falla; las que cumplen no la tapan")
    c = d["coverage"]
    # Una sesion fuera del inventario de C1 tambien: registro e inventario no coinciden (E-61).
    if (not d["complete"] or not sesiones or c["surfacesWithoutSession"] or c["unresolved"]
            or c["sessionsOutsideInventory"]):
        return SIN_COBERTURA, ("no constan todas las sesiones: superficies sin entrada %s, sin "
                               "resolver %s, sesiones fuera del inventario %s" % (
                                   c["surfacesWithoutSession"] or "-", c["unresolved"] or "-",
                                   c["sessionsOutsideInventory"] or "-"))
    if c["rolesWithoutPolicy"]:
        return SIN_COBERTURA_DE_ROLES, "hay roles sin politica de vencimiento: %s" % ", ".join(
            "%s (%s)" % (k, ", ".join(v)) for k, v in c["rolesWithoutPolicy"].items())
    abiertos = sorted({e for e in estados if e != PASA})
    if not abiertos:
        return PASA, ""
    return (abiertos[0] if len(abiertos) == 1 else SIN_VENCIMIENTO,
            "sesiones sin resolver: %s" % ", ".join(
                "%s (%s)" % (s["sessionId"], s["state"]) for s in sesiones if s["state"] != PASA))


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None,) + RESUELTAS:
        todos.add(previo)
    for r in salida["sessions"]:
        todos.update(r.get("states") or [])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


# -- hacia seguridad.resultado ----------------------------------------------------------------------

# La clase de `inactivityTimeout` que `seguridad._vu4` reconoce como propia; las del token las nombra
# `seguridad.EVIDENCIA_QUE_NO_ES_INACTIVIDAD`. El SSO del proveedor no es el tiempo de vida de un token:
# se informa en la sesion y no viaja aca.
PROPIA = "APPLICATION_INACTIVITY_TIMEOUT"
PRESTADAS = {"accessTokenTimeoutRef": "ACCESS_TOKEN_EXPIRY",
             "refreshTokenTimeoutRef": "REFRESH_TOKEN_EXPIRY"}


def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu4", ...)`, desde la salida de `evaluar`.

    Los dos controles de la fila llevan el estado del check: PASS, FAIL o el estado abierto tal
    cual, con la evidencia por id. `inactivityTimeout` lleva la evidencia propia de cada sesion que
    llego a una conclusion, y los vencimientos del token aparte, con su clase prestada: solos no
    alcanzan. Un resultado que no dice ser de este check no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return {}, {}
    estado = r["state"]
    control = FALLA if estado in FALLAS else estado
    ids, propias, prestadas = set(), [], []
    for s in r.get("sessions") or []:
        usada = [i for v in (s.get("evidenceUsed") or {}).values() for i in v]
        ids.update(usada)
        if s.get("state") == PASA or s.get("state") in FALLAS:
            propias.append({"kind": PROPIA, "session": s.get("sessionId"),
                            "evidence": sorted(usada) or ["%s#%s" % (ARCHIVO, s.get("sessionId"))]})
        for campo, clase in PRESTADAS.items():
            ref = (s.get("oidcTimeouts") or {}).get(campo)
            if isinstance(ref, str) and ref.strip():
                prestadas.append({"kind": clase, "session": s.get("sessionId"), "evidence": [ref]})
    evidencia = sorted(ids) or (["check:%s" % CONTROL] if estado in RESUELTAS + FALLAS else [])
    doc = {"controlResults": {c: {"result": control, "evidence": evidencia}
                              for c in (POLICY, CONTROL)},
           "inactivityTimeout": _ev.ordenadas(propias) + _ev.ordenadas(prestadas)}
    valor = r.get("signalValue")
    # 🔴 Un NOT_APPLICABLE que el bloqueo impidio no vuelve a entrar por la senal: sin el estado
    # NOT_APPLICABLE, la senal en FALSE no se entrega y la regla queda sin resolver.
    senales = ({SENAL: True} if valor == _senales.VERDADERA
               else {SENAL: False} if valor == _senales.FALSA and estado == NO_APLICA else {})
    return _ev.depurar(doc), senales
