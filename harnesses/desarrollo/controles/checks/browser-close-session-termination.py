"""Check normativo: cerrar la aplicacion o el browser no deja viva la sesion anterior.

    source: ES0902 / 6.2 / 6 / Vu3

    "Toda aplicacion que se cierra a traves de las ventanas o en forma directa del browser, no
     debe dejar la sesion activa."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Juzga la sesion de la aplicacion, y solo esa.** La sesion del proveedor de identidad, el tiempo
de vida del token y lo que queda en el almacenamiento del browser se informan por separado. Que el
SSO del proveedor siga activo no es FAIL: al volver, un intercambio nuevo puede crear una sesion
nueva, y eso no es la sesion vieja.

🔴 **El logout no es el cierre, y el hook no es el comportamiento.** Que el boton de salir funcione,
o que exista un `beforeunload`, no dice que pasa cuando el usuario cierra la ventana. Cuenta la
evidencia de comportamiento sobre la sesion vieja, y la pantalla de login sola no alcanza.

🔴 **Ventana y browser, no cualquier pestana.** La pestana se exige solo con evidencia de que es un
cierre equivalente para esa superficie.

🔴 **Los clientes los dice el proyecto.** Este modulo no nombra ningun browser.

🔴 **No se prueba nada ni se guarda nada.** Una prueba cuenta si fue autorizada, fuera de produccion,
con una identidad de prueba dedicada y sin registrar secretos. Nada con forma de credencial sale.

🔴 **Vu3 no es Vu4 ni C1.** Un timeout por inactividad no reemplaza el cierre, y el protocolo de
autenticacion no dice nada del cierre.
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

CONTROL = "browser-close-session-termination"
POLICY = "browser-close-session-termination-required"
TIPO = "CHECK"
REGLA = "Vu3"
CLAVE = "ES0902.Vu3"
SENAL = "browserSessionPresent"

ARCHIVO = "browser-session-termination.json"
SCHEMA = "browser-session-termination.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = ("Toda aplicación que se cierra a través de las ventanas o en forma directa del "
                "browser, no debe dejar la sesión activa.")


# 🔴 Las superficies son las de C1, con su cargador. Se importa el modulo; no se corre su evaluacion.
def _modulo_de_superficies():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oidc-keycloak-integration.py")
    spec = importlib.util.spec_from_file_location("_vu3_inventario_de_superficies", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_SUPERFICIES = _modulo_de_superficies()

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_ALCANCE = "SUPPORTED_BROWSER_SCOPE_UNRESOLVED"
SIN_MODELO = "BROWSER_SESSION_MODEL_UNRESOLVED"
SIN_COMPORTAMIENTO = "BROWSER_CLOSE_BEHAVIOR_UNRESOLVED"
SESION_VIVA = "OLD_APPLICATION_SESSION_REMAINS_ACTIVE"
PRUEBA_INSEGURA = "BROWSER_SESSION_TERMINATION_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_ALCANCE, SIN_MODELO,
           SIN_COMPORTAMIENTO, SESION_VIVA, PRUEBA_INSEGURA, SIN_OBJETIVO)

# -- lo que dice el registro ------------------------------------------------------------

VENTANA = "APPLICATION_WINDOW_CLOSE"
BROWSER = "BROWSER_CLOSE"
PESTANA = "TAB_CLOSE"
EXIGIDOS = (VENTANA, BROWSER)

RECHAZADA = "OLD_SESSION_REJECTED"
NUEVA = "NEW_SESSION_ESTABLISHED_AFTER_AUTH"
VIVA = "OLD_SESSION_STILL_ACTIVE"
SIN_RESOLVER = "UNRESOLVED"
NO_CORRESPONDE = "NOT_APPLICABLE"
CUMPLEN = (RECHAZADA, NUEVA)
RESULTADOS = CUMPLEN + (VIVA,)

# El estado de una combinacion, ademas de FAIL y de los de arriba.
CUMPLIDA = "COMPLIANT"
FALTA = "MISSING"
RESUELTAS = (CUMPLIDA, NO_CORRESPONDE)

MODELO_SIN_RESOLVER = "UNRESOLVED"

# -- los dominios ---------------------------------------------------------------------------

DE_LA_APLICACION = "APPLICATION_SESSION"
DEL_PROVEEDOR = "IDENTITY_PROVIDER"
DEL_TOKEN = "TOKEN_LIFETIME"
DEL_ALMACENAMIENTO = "BROWSER_STORAGE"
DOMINIOS = (DE_LA_APLICACION, DEL_PROVEEDOR, DEL_TOKEN, DEL_ALMACENAMIENTO)

# -- lo que establece una evidencia, y que clase lo sostiene ----------------------------------

SESION = "BROWSER_SESSION"
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
MODELO = "SESSION_MODEL"
ALCANCE = "SUPPORTED_CLIENT_SCOPE"
EQUIVALENTE = "TAB_CLOSE_EQUIVALENT"
COMPORTAMIENTO = "CLOSE_BEHAVIOR"
NO_APLICABLE = "CLOSE_EVENT_NOT_APPLICABLE"

PRUEBA = "AUTHORIZED_RUNTIME_TEST"
# 🔴 Las tablas son del harness, no del estandar.
AUTORIDADES = ("ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT", "PROJECT_CONTRACT",
               "OFFICIAL_ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
FUENTES_DE_MODELO = AUTORIDADES + ("APPLICATION_CONFIGURATION", "DEPLOYMENT_CONFIGURATION",
                                   "OIDC_SESSION_EVIDENCE")
FUENTES_DE_ALCANCE = AUTORIDADES + ("QA_TEST_PLAN",)
FUENTES_DE_COMPORTAMIENTO = (PRUEBA, "SESSION_STORE_OBSERVATION", "PROTECTED_ENDPOINT_CHECK",
                             "OFFICIAL_ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
# Las que no sostienen el cierre, nombradas para que la salida diga por que.
INSUFICIENTES = ("IMPLEMENTATION_HOOK", "SOURCE_CODE", "UI_OBSERVATION", "STORAGE_INSPECTION",
                 "EXPLICIT_LOGOUT_TEST", "OIDC_LOGOUT_EVIDENCE", "TOKEN_LIFETIME_CONFIGURATION",
                 "IDP_SESSION_OBSERVATION", "INACTIVITY_TIMEOUT_CONFIGURATION",
                 "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT")
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "REPOSITORY_DEPENDENCY")

CONFIRMADA = "CONFIRMED"
NO_DISPONIBLE = "UNAVAILABLE"
PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "scope": _ev.TEXTO, "targets": _ev.LISTA,
         "domain": _ev.TEXTO, "client": _ev.TEXTO, "event": _ev.TEXTO, "value": _ev.TEXTO,
         "values": _ev.LISTA, "outcome": _ev.TEXTO, "environment": _ev.TEXTO,
         "authorized": _ev.BOOLEANO, "testIdentityRef": _ev.TEXTO,
         "realUserAccount": _ev.BOOLEANO, "rawSecretsLogged": _ev.BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes", "scope", "targets")


def prueba_segura(e, superficie):
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
    elif ambiente != superficie.get("environment"):
        motivos.append("ENVIRONMENT_MISMATCH")
    if not (e.get("testIdentityRef") or "").strip():
        motivos.append("NO_DEDICATED_TEST_IDENTITY")
    if e.get("realUserAccount") is True:
        motivos.append("REAL_USER_ACCOUNT")
    if e.get("rawSecretsLogged") is True:
        motivos.append("RAW_SECRETS_LOGGED")
    return sorted(motivos)


def _lectura(e, superficie):
    """(cuenta, bloqueo, motivos). La misma compuerta para lo que dice que si y que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO, []
        motivos = prueba_segura(e, superficie)
        if motivos:
            return False, PRUEBA_INSEGURA, motivos
        return e.get("outcome") == CONFIRMADA, None, []
    return e.get("outcome") in (None, CONFIRMADA), None, []


def _sobre(e, superficie):
    return (_ev.en(superficie.get("surfaceId"), e.get("targets"))
            and _ev.igual(e.get("scope"), superficie.get("scope")))


# -- el registro --------------------------------------------------------------------------------

def cargar(desde=None):
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "surfaces": []}
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
        return [], "el registro de cierre de sesion no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de cierre de sesion no se pudo validar"
    if errores:
        return [], "el registro de cierre de sesion no valida contra su schema: %d errores" % len(
            errores)
    return list(doc.get("surfaces") or []), ""


# -- la senal -------------------------------------------------------------------------------------

HAY, NO_HAY, NO_SE = "SESSION", "NO_SESSION", "UNRESOLVED"


def _sesion_de(superficie, propias, cat, crudas):
    sid = superficie.get("surfaceId")
    legibles = [e for e in cat.values() if SESION in e["establishes"] and _sobre(e, superficie)
                and e["sourceType"] not in DEBILES and _lectura(e, superficie)[0]]
    enciende = (any(p.get("sessionModel") != MODELO_SIN_RESOLVER for p in propias)
                or any(e.get("value") == PRESENTE for e in legibles))
    apaga = [e["evidenceId"] for e in legibles
             if e.get("value") == AUSENTE and e["sourceType"] in AUTORIDADES]
    # Lo que dice que HAY sesion y no se pudo leer -una prueba insegura- no deja apagar.
    dudosa = any(SESION in e["establishes"] and _sobre(e, superficie) and e.get("value") == PRESENTE
                 and not _lectura(e, superficie)[0] for e in cat.values())
    if dudosa:
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
    cat, crudas, repetidos, torcidas = _ev.catalogo(entrada, FORMA, OBLIGATORIOS)
    # 🔴 Los ids se normalizan UNA vez, antes de contar: contar crudo y buscar en NFC deja pasar dos
    # superficies iguales como distintas (Vu2, tercer pase).
    ids = [_ev.nfc(s.get("surfaceId")) for s in lista]
    detectadas = entrada.get("detectedSurfaces")
    detectadas_torcidas = detectadas is not None and not (
        isinstance(detectadas, list) and all(isinstance(d, str) and d for d in detectadas))
    vistas = sorted({_ev.nfc(d) for d in detectadas or []}) if not detectadas_torcidas else []
    superficies = []
    for s in lista:
        propias = [e for e in registradas if _ev.igual(e.get("surfaceId"), s.get("surfaceId"))]
        superficies.append({"surfaceId": s.get("surfaceId"), "scope": s.get("scope"),
                            "environment": s.get("environment"),
                            "session": _sesion_de(s, propias, cat, crudas)})
    conocidas = {str(i) for i in ids}
    ajenas = sorted({str(e.get("surfaceId")) for e in registradas
                     if _ev.nfc(str(e.get("surfaceId"))) not in conocidas})
    cobertura = {"inventoried": sorted({str(i) for i in ids}), "detected": vistas,
                 "missing": sorted(set(vistas) - {str(i) for i in ids}),
                 "duplicated": sorted({str(i) for i in ids if ids.count(i) > 1}),
                 "detectedMalformed": detectadas_torcidas, "unknownRegistryEntries": ajenas,
                 "registryUnreadable": bool(problema_registro),
                 "unresolved": sorted(str(p["surfaceId"]) for p in superficies
                                      if p["session"] == NO_SE)}
    completa = not (cobertura["missing"] or cobertura["duplicated"] or detectadas_torcidas
                    or ajenas or problema_registro)
    if problema:
        valor = _senales.SIN_RESOLVER
    elif any(p["session"] == HAY for p in superficies):
        valor = _senales.VERDADERA
    elif superficies and completa and all(p["session"] == NO_HAY for p in superficies):
        valor = _senales.FALSA
    elif (not superficies and completa and not registradas and not vistas
          and not (repetidos or torcidas)
          and _SUPERFICIES._valor_de_senal(autenticacion) == _senales.FALSA):
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    return {"value": valor, "surfaces": _ev.ordenadas(superficies), "surfacesInOrder": superficies,
            "inventory": lista, "registry": registradas,
            "coverage": cobertura, "complete": completa, "problem": problema,
            "registryProblem": problema_registro, "catalog": cat, "raw": crudas,
            "repeated": repetidos, "malformed": torcidas}


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
                              "claim": "la superficie `%s` (%s, %s) %s sesion en el browser" % (
                                  p["surfaceId"], p["scope"], p["environment"],
                                  "tiene" if buscada == HAY else "no tiene"),
                              "supports": d["value"]})
        if not evidencia:
            evidencia.append({"evidenceId": "authenticationPresent",
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "authenticationPresent",
                              "claim": "la aplicacion no autentica usuarios", "supports": d["value"]})
    return _ev.depurar(_senales.producir(SENAL, evidencia, {"type": "DETERMINISTIC"}, d["value"],
                                         desde))


def _combinar(derivado, externo):
    if externo is None:
        return derivado
    valor = _SUPERFICIES._valor_de_senal(externo)
    if valor == derivado:
        return valor
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- una combinacion ---------------------------------------------------------------------------

def evaluar_combinacion(registro, superficie, cliente, evento, citados_de_entrada, cat):
    """El estado de un cliente y un evento de cierre: COMPLIANT, FAIL, NOT_APPLICABLE o UNRESOLVED."""
    citados = _ev.claves(citados_de_entrada) | _ev.claves(registro.get("evidence"))
    salida = {"client": cliente, "event": evento, "declared": registro.get("result"),
              "evidenceUsed": [], "contradictedBy": [], "blockedBy": [], "unsafe": [], "issues": []}
    cumplen, viven, dudosas = [], [], []
    for e in sorted(cat.values(), key=lambda x: x["evidenceId"]):
        if (COMPORTAMIENTO not in e["establishes"] or not _sobre(e, superficie)
                or e.get("domain") != DE_LA_APLICACION
                or not _ev.igual(e.get("client"), cliente) or e.get("event") != evento
                or e["sourceType"] not in FUENTES_DE_COMPORTAMIENTO
                or e.get("value") not in RESULTADOS):
            continue
        cuenta, bloqueo, motivos = _lectura(e, superficie)
        if bloqueo:
            # Lo que no se pudo leer impide el PASS si la entrada lo cita, o si decia que NO. Una
            # prueba ajena e insegura que dice "rechazada" no mueve nada.
            if _ev.id_de(e) in citados or e["value"] == VIVA:
                salida["blockedBy"].append(bloqueo)
                salida["unsafe"].extend(motivos)
            continue
        if not cuenta:
            salida["issues"].append("`%s` no esta confirmada" % e["evidenceId"])
            if e["value"] == VIVA:
                dudosas.append(e["evidenceId"])
            continue
        (viven if e["value"] == VIVA else cumplen).append(e)
    salida["blockedBy"] = sorted(set(salida["blockedBy"]))
    salida["unsafe"] = sorted(set(salida["unsafe"]))
    declarado = registro.get("result")
    contra = sorted([e["evidenceId"] for e in viven] + dudosas)
    viven_citadas = sorted(e["evidenceId"] for e in viven if _ev.id_de(e) in citados)
    if viven_citadas:
        salida["evidenceUsed"] = viven_citadas
        estado, motivo = FALLA, ("una evidencia de comportamiento muestra la sesion vieja activa "
                                 "despues del cierre")
    elif declarado == VIVA and cumplen:
        salida["contradictedBy"] = sorted(e["evidenceId"] for e in cumplen)
        estado, motivo = SIN_RESOLVER, ("el registro dice que la sesion vieja sigue activa y una "
                                        "evidencia dice que no; no se elige")
    elif declarado == VIVA:
        estado, motivo = FALLA, "el registro declara que la sesion vieja sigue activa"
    elif declarado == NO_CORRESPONDE and contra:
        salida["contradictedBy"] = contra
        estado, motivo = SIN_RESOLVER, ("el registro dice que este cierre no corresponde y una "
                                        "evidencia dice que la sesion vieja sigue viva")
    elif declarado == NO_CORRESPONDE:
        razones = sorted(e["evidenceId"] for e in cat.values()
                         if NO_APLICABLE in e["establishes"] and _ev.id_de(e) in citados
                         and _sobre(e, superficie) and e["sourceType"] in AUTORIDADES
                         and _ev.igual(e.get("client"), cliente)
                         and e.get("event") == evento and _lectura(e, superficie)[0])
        salida["evidenceUsed"] = razones
        estado, motivo = ((NO_CORRESPONDE, "") if razones
                          else (SIN_RESOLVER, "no consta que este cierre no corresponda"))
    else:
        apoyo = sorted(e["evidenceId"] for e in cumplen
                       if _ev.id_de(e) in citados and e.get("value") == declarado)
        if declarado in CUMPLEN and apoyo and not contra:
            salida["evidenceUsed"] = apoyo
            estado, motivo = CUMPLIDA, ""
        else:
            salida["contradictedBy"] = contra
            estado, motivo = SIN_RESOLVER, (
                "no consta con evidencia de comportamiento que la sesion vieja deje de servir; el "
                "logout, el hook, la pantalla o el almacenamiento no alcanzan")
    # 🔴 Un solo paso de bloqueo, el mismo para todas las ramas: lo que no se pudo leer y la
    # entrada cita, o que dice que la sesion vieja sigue viva, impide cumplir y tambien no
    # corresponder. Parchar una rama sola dejaba pasar un NOT_APPLICABLE contra una prueba
    # insegura (refutador, pase 2). Un FAIL no se toca: bloquear impide el PASS, no tapa lo que
    # falla.
    if salida["blockedBy"] and estado in RESUELTAS:
        salida["evidenceUsed"] = []
        estado, motivo = SIN_RESOLVER, ("una prueba que la entrada cita, o que dice que la sesion "
                                        "vieja sigue viva, no se pudo leer")
    salida["state"] = estado
    salida["reason"] = motivo
    return salida


def _estado_abierto(c):
    if PRUEBA_INSEGURA in c.get("blockedBy") or []:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in c.get("blockedBy") or []:
        return SIN_OBJETIVO
    return SIN_COMPORTAMIENTO


# -- una superficie ------------------------------------------------------------------------------

def _contexto(superficie, cat, citados):
    """Lo que se informa y no decide: los otros dominios, el logout y los hooks."""
    salida = {d: [] for d in DOMINIOS if d != DE_LA_APLICACION}
    salida.update({"explicitLogout": [], "implementation": []})
    for e in sorted(cat.values(), key=lambda x: x["evidenceId"]):
        if not _sobre(e, superficie):
            continue
        if e.get("domain") in salida:
            salida[e["domain"]].append(e["evidenceId"])
        if e["sourceType"] in ("EXPLICIT_LOGOUT_TEST", "OIDC_LOGOUT_EVIDENCE"):
            salida["explicitLogout"].append(e["evidenceId"])
        if e["sourceType"] in ("IMPLEMENTATION_HOOK", "SOURCE_CODE"):
            salida["implementation"].append(e["evidenceId"])
    return salida


def evaluar_superficie(superficie, propias, d):
    cat, crudas = d["catalog"], d["raw"]
    sid = superficie.get("surfaceId")
    salida = {"surfaceId": sid, "scope": superficie.get("scope"),
              "environment": superficie.get("environment"), "sessionModel": None,
              "combinations": [], "ignoredEvents": [], "outOfScopeClients": [],
              "supportingContext": {}, "issues": [], "evidenceUsed": {},
              "domains": {DE_LA_APLICACION: None}}
    if d["registryProblem"]:
        return _cierre(salida, SIN_COMPORTAMIENTO, "el registro de cierre de sesion no se pudo leer")
    if not propias:
        return _cierre(salida, SIN_MODELO, "no hay entrada del registro para esta superficie")
    if len(propias) > 1:
        return _cierre(salida, SIN_MODELO, "hay mas de una entrada para esta superficie; no se elige")
    entrada = propias[0]
    citados = _ev.claves(entrada.get("evidence"))
    salida["supportingContext"] = _contexto(superficie, cat, citados)
    salida["supportingContext"]["explicitLogoutRefs"] = sorted(
        r for r in entrada.get("explicitLogoutEvidenceRefs") or [] if isinstance(r, str))

    # El modelo de sesion.
    declarado = entrada.get("sessionModel")
    salida["sessionModel"] = declarado
    modelos = [e for e in cat.values() if MODELO in e["establishes"] and _sobre(e, superficie)
               and e["sourceType"] in FUENTES_DE_MODELO and _lectura(e, superficie)[0]]
    apoyo_modelo = [e for e in modelos if _ev.id_de(e) in citados and e.get("value") == declarado]
    contra_modelo = [e for e in modelos if e.get("value") != declarado]
    modelo_ok = declarado != MODELO_SIN_RESOLVER and apoyo_modelo and not contra_modelo

    # El alcance de clientes.
    alcances = [e for e in cat.values() if ALCANCE in e["establishes"] and _sobre(e, superficie)
                and e["sourceType"] in FUENTES_DE_ALCANCE and e.get("values")
                and _lectura(e, superficie)[0]]
    conjuntos = {tuple(sorted({_ev.nfc(v) for v in e["values"]})) for e in alcances}
    citado_alcance = any(_ev.id_de(e) in citados for e in alcances)
    alcance = list(conjuntos)[0] if len(conjuntos) == 1 and citado_alcance else None

    pestana = any(EQUIVALENTE in e["establishes"] and _ev.id_de(e) in citados
                  and _sobre(e, superficie) and e["sourceType"] in AUTORIDADES
                  and _lectura(e, superficie)[0] for e in cat.values())
    exigidos = EXIGIDOS + ((PESTANA,) if pestana else ())
    salida["evidenceUsed"] = {
        "sessionModel": sorted(e["evidenceId"] for e in apoyo_modelo) if modelo_ok else [],
        "clientScope": sorted(e["evidenceId"] for e in alcances
                              if _ev.id_de(e) in citados) if alcance is not None else []}

    clientes = [c for c in entrada.get("clients") or []]
    por_cliente = {}
    for c in clientes:
        por_cliente.setdefault(_ev.nfc(c.get("clientId")), []).append(c)
    a_evaluar = sorted(alcance) if alcance is not None else sorted(por_cliente)
    salida["outOfScopeClients"] = sorted(k for k in por_cliente if alcance is not None
                                         and k not in alcance)
    for cliente in a_evaluar:
        registros_de_cliente = por_cliente.get(cliente) or []
        eventos = [ev for c in registros_de_cliente for ev in c.get("closeEvents") or []]
        if len(registros_de_cliente) > 1:
            salida["combinations"].append({"client": cliente, "event": None,
                                           "state": SIN_RESOLVER, "blockedBy": [],
                                           "reason": "el cliente esta repetido en el registro"})
            continue
        for evento in exigidos:
            del_evento = [ev for ev in eventos if ev.get("event") == evento]
            if not del_evento:
                salida["combinations"].append({"client": cliente, "event": evento,
                                               "state": FALTA, "blockedBy": [],
                                               "reason": "no hay evidencia de este cierre"})
            elif len(del_evento) > 1:
                salida["combinations"].append({"client": cliente, "event": evento,
                                               "state": SIN_RESOLVER, "blockedBy": [],
                                               "reason": "el evento esta repetido para el cliente"})
            else:
                salida["combinations"].append(
                    evaluar_combinacion(del_evento[0], superficie, cliente, evento, citados, cat))
        if not pestana:
            salida["ignoredEvents"].extend(
                "%s/%s" % (cliente, ev.get("event")) for ev in eventos if ev.get("event") == PESTANA)
    salida["combinations"] = _ev.ordenadas(salida["combinations"])
    salida["ignoredEvents"] = sorted(salida["ignoredEvents"])

    # Las referencias colgadas cuentan en lo que se evalua: un TAB_CLOSE no exigido o un cliente
    # fuera del alcance no mueven nada, tampoco por una referencia que no existe.
    evaluados = [ev for c in clientes if _ev.nfc(c.get("clientId")) in set(a_evaluar)
                 for ev in c.get("closeEvents") or [] if ev.get("event") in exigidos]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | {_ev.nfc(r) for ev in evaluados for r in ev.get("evidence") or []
                          if isinstance(r, str) and _ev.nfc(r) not in cat}
                       | set(_ev.ilegibles_sobre(sid, cat, crudas)))
    estados = [c["state"] for c in salida["combinations"]]
    salida["domains"][DE_LA_APLICACION] = sorted(set(estados))
    if FALLA in estados:
        return _cierre(salida, FALLA, "la sesion vieja sigue activa despues de un cierre",
                       [SESION_VIVA])
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre la superficie: %s"
                                % ", ".join(ilegibles))
        return _cierre(salida, SIN_COMPORTAMIENTO, "hay evidencia ilegible, y esa podia ser la que "
                                                   "decia que la sesion vieja sigue activa")
    if not modelo_ok:
        return _cierre(salida, SIN_MODELO, "el modelo de sesion no consta con evidencia")
    if alcance is None:
        return _cierre(salida, SIN_ALCANCE, "los clientes soportados no constan con evidencia del "
                                            "proyecto")
    abiertos = sorted({_estado_abierto(c) for c in salida["combinations"]
                       if c["state"] not in RESUELTAS})
    if not abiertos:
        return _cierre(salida, PASA, "")
    return _cierre(salida, abiertos[0] if len(abiertos) == 1 else SIN_COMPORTAMIENTO,
                   "combinaciones sin resolver: %s" % ", ".join(
                       "%s/%s" % (c["client"], c["event"]) for c in salida["combinations"]
                       if c["state"] not in RESUELTAS))


def _cierre(salida, estado, motivo, extra=()):
    salida["state"] = estado
    salida["states"] = sorted(set(extra) | ({estado} if estado != PASA else set()))
    salida["reason"] = motivo
    return salida


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, autenticacion=None, desde=None):
    """El estado de Vu3, superficie por superficie y combinacion por combinacion.

    `caso`:

        {"inventory": {...},       # el de C1; opcional
         "sessions": {...},        # el registro de Vu3; opcional
         "evidence": [...],        # el catalogo, cerrado
         "detectedSurfaces": [...]}
    """
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "surfaces": [], "issues": [], "coverage": {}}
    d = derivar(caso, autenticacion, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    salida["coverage"] = d["coverage"]
    for problema in (d["problem"], d["registryProblem"]):
        if problema:
            salida["issues"].append("el inventario de superficies no valida contra su schema"
                                    if problema.startswith("el inventario de superficies no valida")
                                    else problema)
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    salida["issues"].sort()
    if valor == _senales.SIN_RESOLVER:
        return _cerrar(salida, SIN_APLICABILIDAD, "no consta si hay una sesion de la aplicacion en "
                                                  "el browser")
    if valor == _senales.FALSA:
        return _cerrar(salida, NO_APLICA, "no hay sesion de la aplicacion en el browser")
    if d["problem"]:
        return _cerrar(salida, SIN_COMPORTAMIENTO, "el inventario de superficies no se pudo leer")

    # 🔴 Cada superficie del inventario se evalua con SU ambiente y su alcance, tambien cuando el id
    # esta repetido: tomar la primera hace depender el resultado del orden (refutador, pase 1).
    salida["surfaces"] = _ev.ordenadas(
        evaluar_superficie(s, [e for e in d["registry"]
                               if _ev.igual(e.get("surfaceId"), s.get("surfaceId"))], d)
        for s, p in zip(d["inventory"], d["surfacesInOrder"]) if p["session"] == HAY)
    estados = [r["state"] for r in salida["surfaces"]]
    if FALLA in estados:
        return _cerrar(salida, FALLA, "la sesion vieja sigue activa en al menos un cierre; lo que "
                                      "cumple no lo tapa")
    if not d["complete"] or not salida["surfaces"]:
        return _cerrar(salida, SIN_COMPORTAMIENTO, "no constan todas las superficies ni el registro")
    if d["coverage"]["unresolved"]:
        return _cerrar(salida, SIN_MODELO, "hay superficies de las que no se sabe si tienen sesion "
                                           "en el browser: %s"
                       % ", ".join(d["coverage"]["unresolved"]))
    abiertos = sorted({e for e in estados if e != PASA})
    if not abiertos:
        return _cerrar(salida, PASA, "")
    return _cerrar(salida, abiertos[0] if len(abiertos) == 1 else SIN_COMPORTAMIENTO,
                   "superficies sin resolver: %s" % ", ".join(
                       "%s (%s)" % (r["surfaceId"], r["state"]) for r in salida["surfaces"]
                       if r["state"] != PASA))


def _cerrar(salida, estado, motivo):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    for r in salida["surfaces"]:
        todos.update(r.get("states") or [])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA
