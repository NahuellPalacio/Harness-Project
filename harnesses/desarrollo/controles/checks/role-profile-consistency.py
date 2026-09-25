"""Check normativo: los perfiles efectivos respetan los roles asignados.

    source: ES0902 / 6.2 / 6 / Vu8

    "Los perfiles de usuarios armados en las aplicaciones deben respetar los roles asignados."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Lo asignado contra lo efectivo.** La fuente de los roles, el acceso esperado de cada rol o conjunto
de roles y el acceso efectivo salen de evidencia citada. El nombre de un rol no define permisos, y el
modulo no tiene ninguna lista de roles, frameworks, anotaciones ni claims.

🔴 **El servidor manda.** Un boton escondido no prueba que la API niegue una operacion protegida. Una
operacion que el cliente niega y el servidor permite es `DIRECT_ACCESS_BYPASSES_ROLE`.

🔴 **Nada se inventa.** Ni la semantica de varios roles -el mas alto gana, se suman, se intersecan- ni
un tiempo de propagacion de un cambio de rol. Salen de la evidencia del proyecto o quedan sin resolver.

🔴 **Autenticar no es autorizar.** Un login exitoso, un claim en el token o una validacion de entrada
no dicen nada de acceso. El check no lee ni escribe el resultado de ninguna otra regla.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Una prueba insegura o sin
objetivo no aprueba ni hace FAIL. El modulo no ejecuta nada. La salida lleva ids, roles, operaciones y
estados, nunca una credencial.
"""
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

CONTROL = "role-profile-consistency"
POLICY = "user-profile-role-enforcement-required"
TIPO = "CHECK"
REGLA = "Vu8"
CLAVE = "ES0902.Vu8"
SENAL = "applicationRolesPresent"

ARCHIVO = "role-profile-consistency.json"
SCHEMA = "role-profile-consistency.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = "Los perfiles de usuarios armados en las aplicaciones deben respetar los roles asignados."

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_FUENTE = "ROLE_ASSIGNMENT_SOURCE_UNRESOLVED"
SIN_MAPEO = "ROLE_PROFILE_MAPPING_UNRESOLVED"
SIN_VARIOS = "MULTI_ROLE_PROFILE_UNRESOLVED"
SIN_CAMBIO = "ROLE_CHANGE_PROPAGATION_UNRESOLVED"
DE_MAS = "OVER_PRIVILEGED_PROFILE"
DE_MENOS = "UNDER_PRIVILEGED_PROFILE"
SALTEO = "DIRECT_ACCESS_BYPASSES_ROLE"
PRUEBA_INSEGURA = "ROLE_PROFILE_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_FUENTE, SIN_MAPEO, SIN_VARIOS, SIN_CAMBIO,
           DE_MAS, DE_MENOS, SALTEO, PRUEBA_INSEGURA, SIN_OBJETIVO)
# Las formas de fallar, en el orden en que el agregado informa la primera.
ORDEN_DE_LAS_FALLAS = (SALTEO, DE_MAS, DE_MENOS)
FALLAS = (FALLA,) + ORDEN_DE_LAS_FALLAS
RESUELTAS = (PASA, NO_APLICA)
# Sin ninguna falla, el sin resolver que se informa es el primero de este orden: el de los pasos.
ORDEN_DE_LO_ABIERTO = (SIN_FUENTE, SIN_MAPEO, SIN_VARIOS, SIN_CAMBIO, PRUEBA_INSEGURA, SIN_OBJETIVO)

# El resultado de un mapping, el del registro.
CONSISTENTE = "CONSISTENT"
SIN_RESOLVER = "UNRESOLVED"

# -- lo que dice el registro ------------------------------------------------------------

RESUELTA = "RESOLVED"
NO_APLICABLE = "NOT_APPLICABLE"
SEMANTICAS_DECLARABLES = (RESUELTA, NO_APLICABLE)
SIN_VERIFICAR = "NOT_VERIFIED"

# -- lo que establece una evidencia ---------------------------------------------------------

ROLES = "APPLICATION_ROLES"                     # value PRESENT | ABSENT
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
FUENTE = "ROLE_ASSIGNMENT_SOURCE"               # value: el sourceRef; roles: los que asigna
MAPEO = "ROLE_PROFILE_MAPPING"                  # value: el perfil; operations, dataScopes
ACCESO = "ACCESS"                               # value ALLOWED | DENIED; operations, dataScopes
PERMITIDO, NEGADO = "ALLOWED", "DENIED"
VARIOS = "MULTI_ROLE_SEMANTICS"                 # value RESOLVED | NOT_APPLICABLE
CAMBIO = "ROLE_CHANGE_SEMANTICS"                # value RESOLVED | NOT_APPLICABLE
REVOCADO = "ROLE_CHANGE_ACCESS"                 # value: uno de los tres de abajo
MAS_ALLA = "REVOKED_ROLE_EFFECTIVE_BEYOND_REFRESH"
DENTRO = "REVOKED_ROLE_EFFECTIVE_WITHIN_REFRESH"
NO_VIGENTE = "REVOKED_ROLE_NOT_EFFECTIVE"

CONFIRMADA = "CONFIRMED"
OBSERVADA = "OBSERVED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, OBSERVADA)

# -- que clase sostiene que ------------------------------------------------------------------
# 🔴 Las tablas son del harness, no del estandar.

PRUEBA = "AUTHORIZED_QA_ROLE_TEST"
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "NAMING_CONVENTION")
# Las autoritativas del proyecto.
AUTORIDADES = ("SECURITY_DOCUMENTATION", "ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT",
               "PROJECT_CONTRACT", "ACCESS_CONTROL_MATRIX", "ASSESSMENT_FINDING",
               "OTHER_AUTHORITATIVE_EVIDENCE")
DE_FUENTE = AUTORIDADES + ("APPLICATION_DATABASE_SCHEMA", "BACKOFFICE_ASSIGNMENT_CONFIGURATION",
                           "IDENTITY_PROVIDER_CONFIGURATION", "INTEGRATION_CONTRACT")
DE_MAPEO = AUTORIDADES + ("ROLE_PROFILE_CONFIGURATION",)
DE_VARIOS = AUTORIDADES + ("IDENTITY_PROVIDER_CONFIGURATION", "ROLE_PROFILE_CONFIGURATION")
DE_CAMBIO = DE_VARIOS + ("SESSION_CONFIGURATION",)
DEL_SERVIDOR = ("BACKEND_AUTHORIZATION_CODE", "BACKEND_AUTHORIZATION_CONFIGURATION",
                "UNIT_AUTHORIZATION_TEST", "INTEGRATION_AUTHORIZATION_TEST", "API_AUTHORIZATION_TEST",
                PRUEBA, "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
DEL_CLIENTE = ("FRONTEND_ROLE_GUARD", "UI_VISIBILITY_CONFIGURATION", "UI_TEST")
# Las que no sostienen nada de Vu8, nombradas para que la salida diga por que.
INSUFICIENTES = ("SOURCE_CODE", "NAMING_CONVENTION", "AUTHENTICATION_SUCCESS", "TOKEN_CLAIM_PRESENCE",
                 "INPUT_VALIDATION", "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT")

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

# 🔴 No hay campo para una credencial ni un dato personal: un item que lo trae queda mal formado.
# `severity` se acepta y no se lee nunca: la severidad no es el resultado.
FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "surfaces": _ev.LISTA, "mappings": _ev.LISTA,
         "roles": _ev.LISTA, "value": _ev.TEXTO, "operations": _ev.LISTA, "dataScopes": _ev.LISTA,
         "outcome": _ev.TEXTO, "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO,
         "syntheticIdentities": _ev.BOOLEANO, "destructive": _ev.BOOLEANO,
         "realPrivilegedAccount": _ev.BOOLEANO, "rawCredentialsLogged": _ev.BOOLEANO,
         "severity": _ev.TEXTO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def catalogo(caso):
    """El catalogo de `evidencia.py`, sin nada agregado."""
    return _ev.catalogo(caso, FORMA, OBLIGATORIOS)


def prueba_segura(e):
    """Los motivos por los que una prueba no era segura. Vacio es segura.

    No ejecuta nada. Ninguna condicion exige una cuenta real: con identidades sinteticas alcanza."""
    motivos = []
    if e.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    ambiente = e.get("environment")
    if ambiente in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    elif _ev.igual(ambiente, PRODUCCION):
        motivos.append("PRODUCTION")
    elif _ev.nfc(ambiente) not in AMBIENTES_DE_PRUEBA:
        motivos.append("ENVIRONMENT_UNKNOWN")
    if e.get("syntheticIdentities") is not True:
        motivos.append("NOT_SYNTHETIC_IDENTITIES")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
    if e.get("realPrivilegedAccount") is True:
        motivos.append("REAL_PRIVILEGED_ACCOUNT")
    if e.get("rawCredentialsLogged") is True:
        motivos.append("RAW_CREDENTIALS_LOGGED")
    return sorted(motivos)


def _lectura(e):
    """(cuenta, bloqueo, motivos). La misma compuerta para lo que dice que si y que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO, []
        motivos = prueba_segura(e)
        if motivos:
            return False, PRUEBA_INSEGURA, motivos
    return e.get("outcome") in LEIBLES, None, []


def _sostiene(e, que, clases):
    """Si el item legible, de una clase que puede decir `que`, lo establece."""
    return que in e["establishes"] and e["sourceType"] in clases and _lectura(e)[0]


def _citada(e, citados):
    return _ev.id_de(e) in citados


def _nombra(e, sid, mid, citada):
    """Si el item habla de ESTE mapping de ESTA superficie.

    Lo nombra por su id. Sin nombrar ningun mapping, lo nombra si nombra su superficie, y si no nombra
    nada, solo si se lo cita. Un item que nombra otra superficie habla de otra cosa."""
    superficies, mappings = e.get("surfaces"), e.get("mappings")
    if superficies and not _ev.en(sid, superficies):
        return False
    if mid is not None and mappings:
        return _ev.en(mid, mappings)
    return citada or bool(superficies)


def _nfcs(lista):
    return sorted({_ev.nfc(x) for x in (lista or []) if isinstance(x, str)})


# -- el registro ------------------------------------------------------------------------------

VACIO = {"version": "1.0", "surfaces": []}


def cargar(desde=None):
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return dict(VACIO)
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
    """(registro, problema). El del caso si viene; si no, el instalado."""
    declarado = (caso or {}).get("registry")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return dict(VACIO), "el registro de roles y perfiles no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return dict(VACIO), "el registro de roles y perfiles no se pudo validar"
    if errores:
        return dict(VACIO), ("el registro de roles y perfiles no valida contra su schema: %d errores"
                             % len(errores))
    return doc, ""


# -- la senal ---------------------------------------------------------------------------------

def derivar(caso, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    registro, problema = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    superficies = list(registro.get("surfaces") or [])
    citados = set()
    for s in superficies:
        citados |= _ev.claves(s.get("evidence"))
        for m in s.get("mappings") or []:
            citados |= _ev.claves(m.get("evidence"))

    sobre_roles = [e for e in cat.values() if ROLES in e["establishes"]]
    presentes = [e for e in sobre_roles if e.get("value") == PRESENTE and e["sourceType"] not in DEBILES
                 and _lectura(e)[0]]
    # 🔴 Cualquier PRESENT, legible o no y de la clase que sea, impide apagar la regla.
    dicen_que_si = [e for e in sobre_roles if e.get("value") == PRESENTE]
    ausentes = [e for e in sobre_roles if e.get("value") == AUSENTE and _sostiene(e, ROLES, AUTORIDADES)]
    ilegibles = _ev.ilegibles_sobre(ROLES, cat, crudas)
    if problema:
        valor = _senales.SIN_RESOLVER
    elif presentes:
        valor = _senales.VERDADERA
    elif ausentes and not dicen_que_si and not superficies and not ilegibles:
        valor = _senales.FALSA
    else:
        # Tambien el vacio: el vacio no es FALSE.
        valor = _senales.SIN_RESOLVER

    ids = [_ev.nfc(s.get("surfaceId")) for s in superficies]
    nombradas = _nfcs(x for e in presentes for x in e.get("surfaces") or [])
    cobertura = {"registered": sorted({str(i) for i in ids}),
                 "namedBySignal": [str(s) for s in nombradas],
                 "missingSurfaces": [str(s) for s in nombradas if s not in ids],
                 "duplicatedSurfaces": sorted({str(i) for i in ids if ids.count(i) > 1}),
                 "registryUnreadable": bool(problema)}
    return {"value": valor, "registry": registro, "problem": problema, "surfaces": superficies,
            "catalog": cat, "raw": crudas, "repeated": repetidos, "malformed": torcidas,
            "cited": citados, "present": presentes, "absent": ausentes, "coverage": cobertura}


def senal(caso, desde=None):
    d = derivar(caso, desde)
    usadas = d["present"] if d["value"] == _senales.VERDADERA else (
        d["absent"] if d["value"] == _senales.FALSA else [])
    evidencia = [{"evidenceId": "roles:%s" % e["evidenceId"], "sourceType": "REPOSITORY_CONFIGURATION",
                  "reference": "%s#%s" % (ARCHIVO, e["evidenceId"]),
                  "claim": ("una evidencia establece que la aplicacion tiene roles que gobiernan el "
                            "perfil" if d["value"] == _senales.VERDADERA else
                            "una evidencia autoritativa establece que no hay un modelo de roles"),
                  "supports": d["value"]} for e in usadas]
    return _ev.depurar(_senales.producir(SENAL, _ev.ordenadas(evidencia), {"type": "DETERMINISTIC"},
                                         d["value"], desde))


def _valor_de_senal(externo):
    if isinstance(externo, bool):
        return _senales.VERDADERA if externo else _senales.FALSA
    if isinstance(externo, dict):
        externo = externo.get("value")
    return externo if externo in _senales.VALORES else _senales.SIN_RESOLVER


def _combinar(derivado, externo):
    if externo is None:
        return derivado
    valor = _valor_de_senal(externo)
    if valor == derivado:
        return valor
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- el bloqueo, uno solo ----------------------------------------------------------------------

def _dice_falla(e, esperado=None):
    """🔴 La unica pregunta de si un item dice una falla del mapping. La usan el bloqueo, lo ilegible
    y lo no citado: tres respuestas distintas a la misma pregunta costaron dos pasadas.

    Dice una falla un item del servidor -de cualquier legibilidad- que permite algo no esperado,
    niega algo esperado, o dice que un rol revocado sigue vigente mas alla de la ventana. Sin lo
    esperado resuelto, cualquier permiso cuenta. El cliente nunca dice una falla por si solo: con
    servidor, manda el servidor; sin servidor, una operacion protegida queda sin resolver y una
    opcion local no falla."""
    if e.get("sourceType") not in DEL_SERVIDOR:
        return False
    if REVOCADO in e["establishes"] and e.get("value") == MAS_ALLA:
        return True
    if ACCESO not in e["establishes"] or e.get("value") not in (PERMITIDO, NEGADO):
        return False
    if esperado is None:
        return e.get("value") == PERMITIDO
    for campo in ("operations", "dataScopes"):
        for r in _nfcs(e.get(campo)):
            if (e.get("value") == PERMITIDO) != (r in esperado[campo]):
                return True
    return False


def _bloqueos(cat, citados, sid=None, mid=None, registrados=(), superficies=(), esperado=None):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan: las citadas, o las que dicen
    una falla (`_dice_falla`). Con `mid`, las que nombran ese mapping; sin el, las que nombran una
    superficie del registro y ningun mapping registrado."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        citada = _citada(e, citados)
        if mid is not None and not _nombra(e, sid, mid, citada):
            continue
        if mid is None and (any(_nombra(e, s, m, False) for s, m in registrados)
                            or not any(_ev.en(s, e.get("surfaces")) for s in superficies)):
            continue
        _, bloqueo, m = _lectura(e)
        if bloqueo and (citada or _dice_falla(e, esperado)):
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos, defecto=SIN_MAPEO):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return defecto


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan el mapping, el PASS y el NOT_APPLICABLE.

    Lo que no se pudo leer y pesa impide el PASS; un FAIL no se toca: bloquear impide aprobar, no
    tapa lo que falla. Tampoco reemplaza un sin resolver que ya estaba."""
    if estado not in RESUELTAS:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), "una prueba que se cita, o que dice que se permite algo, no se pudo leer"
    if ilegibles:
        return SIN_MAPEO, ("hay evidencia ilegible sobre la superficie o el mapping, y esa podia ser la "
                           "que decia que se permite algo")
    return estado, motivo


# -- la superficie: fuente y semanticas ----------------------------------------------------------

def _fuente(superficie, cat):
    sid = _ev.nfc(superficie.get("surfaceId"))
    declarada = superficie.get("roleAssignmentSource") or {}
    ref = _ev.nfc(declarada.get("sourceRef")) if isinstance(declarada.get("sourceRef"), str) else None
    citados = _ev.claves(superficie.get("evidence"))
    candidatas = [e for e in cat.values() if _sostiene(e, FUENTE, DE_FUENTE)
                  and _nombra(e, sid, None, _citada(e, citados))]
    apoyo = sorted(e["evidenceId"] for e in candidatas if _citada(e, citados)
                   and ref is not None and _ev.igual(e.get("value"), ref))
    contra = sorted(e["evidenceId"] for e in candidatas if not _ev.igual(e.get("value"), ref))
    insuficientes = sorted(e["evidenceId"] for e in cat.values() if FUENTE in e["establishes"]
                           and _citada(e, citados) and e["sourceType"] not in DE_FUENTE)
    resuelta = bool(declarada.get("status") == RESUELTA and ref and apoyo and not contra)
    roles = _nfcs(r for e in cat.values() if e["evidenceId"] in apoyo for r in e.get("roles") or [])
    return {"status": declarada.get("status"), "sourceRef": ref, "resolved": resuelta,
            "roles": [str(r) for r in roles] if resuelta else [],
            "evidenceUsed": apoyo if resuelta else [], "contradictedBy": contra,
            "insufficient": insuficientes,
            "state": PASA if resuelta else SIN_FUENTE}


def _semantica(superficie, campo, que, clases, estado_abierto, cat):
    sid = _ev.nfc(superficie.get("surfaceId"))
    declarada = superficie.get(campo)
    citados = _ev.claves(superficie.get("evidence"))
    candidatas = [e for e in cat.values() if _sostiene(e, que, clases)
                  and _nombra(e, sid, None, _citada(e, citados))]
    apoyo = sorted(e["evidenceId"] for e in candidatas if _citada(e, citados)
                   and declarada in SEMANTICAS_DECLARABLES and e.get("value") == declarada)
    contra = sorted(e["evidenceId"] for e in candidatas if e.get("value") != declarada)
    resuelta = declarada if declarada in SEMANTICAS_DECLARABLES and apoyo and not contra else None
    return {"declared": declarada, "resolved": resuelta, "evidenceUsed": apoyo if resuelta else [],
            "contradictedBy": contra, "state": PASA if resuelta else estado_abierto}


# -- el mapping, en el orden de la spec ------------------------------------------------------------

def _ids(x, que, clases, valores=None, solo_citadas=True):
    """Los items legibles de `clases` que establecen `que` sobre el mapping."""
    return [e for e in x["cat"].values()
            if _sostiene(e, que, clases) and (valores is None or e.get("value") in valores)
            and (_citada(e, x["citados"]) or not solo_citadas)
            and _nombra(e, x["sid"], x["mid"], _citada(e, x["citados"]))]


def _paso_fuente(x):
    fuente = x["fuente"]
    if not fuente["resolved"]:
        return SIN_FUENTE, "la fuente autoritativa de los roles de la superficie no esta resuelta"
    fuera = [r for r in x["roles"] if r not in fuente["roles"]]
    if fuera:
        x["salida"]["issues"].append("roles que la fuente no asigna: %s" % ", ".join(map(str, fuera)))
        return SIN_FUENTE, "el mapping nombra roles que la fuente autoritativa no asigna"
    return None, ""


def _paso_varios(x):
    if len(x["roles"]) < 2:
        return None, ""
    if x["varios"]["resolved"] != RESUELTA:
        return SIN_VARIOS, ("el mapping tiene varios roles y la semantica de varios roles no consta con "
                            "evidencia citada")
    return None, ""


def _paso_esperado(x):
    salida = x["salida"]
    ref = x["mapping"].get("expectedProfileRef")
    ref = _ev.nfc(ref) if isinstance(ref, str) else None
    todas = _ids(x, MAPEO, DE_MAPEO, solo_citadas=False)
    apoyo = [e for e in todas if _citada(e, x["citados"]) and ref is not None
             and _ev.igual(e.get("value"), ref)]
    salida["insufficient"].extend(e["evidenceId"] for e in x["cat"].values()
                                  if MAPEO in e["establishes"] and _citada(e, x["citados"])
                                  and e["sourceType"] not in DE_MAPEO)
    formas = {(_ev.nfc(e.get("value")), tuple(_nfcs(e.get("operations"))),
               tuple(_nfcs(e.get("dataScopes")))) for e in todas}
    if not apoyo:
        return SIN_MAPEO, ("el acceso esperado del mapping no consta con un `ROLE_PROFILE_MAPPING` "
                           "citado con su perfil; el nombre del rol no define permisos")
    if len(formas) > 1:
        salida["contradictedBy"].extend(e["evidenceId"] for e in todas)
        return SIN_MAPEO, "dos evidencias del mapeo no coinciden en perfil, operaciones o alcances"
    _, ops, alcances = formas.pop()
    x["esperado"] = {"operations": list(ops), "dataScopes": list(alcances)}
    salida["expected"] = {"operations": [str(o) for o in ops], "dataScopes": [str(a) for a in alcances]}
    salida["evidenceUsed"]["mapping"] = sorted(e["evidenceId"] for e in apoyo)
    return None, ""


def _de_acceso(x, campo, ref, clases):
    """(permiten, niegan) citados y legibles de `clases` sobre `ref` en `campo`."""
    items = [e for e in _ids(x, ACCESO, clases, (PERMITIDO, NEGADO)) if _ev.en(ref, e.get(campo))]
    return (sorted(e["evidenceId"] for e in items if e.get("value") == PERMITIDO),
            sorted(e["evidenceId"] for e in items if e.get("value") == NEGADO))


def _comparar(x, campo, ref, esperada, protegida):
    """(resultado, detalle) de una operacion o un alcance, con la tabla de la spec."""
    srv_si, srv_no = _de_acceso(x, campo, ref, DEL_SERVIDOR)
    cli_si, cli_no = _de_acceso(x, campo, ref, DEL_CLIENTE)
    detalle = {"dimension": "operation" if campo == "operations" else "dataScope", "ref": str(ref),
               "expected": esperada, "protected": protegida,
               "server": {"allowed": srv_si, "denied": srv_no},
               "client": {"allowed": cli_si, "denied": cli_no}}
    if srv_si and srv_no:
        resultado = SIN_RESOLVER
    elif srv_si or srv_no:
        # 🔴 Cuando hay servidor, manda el servidor.
        if esperada:
            resultado = CONSISTENTE if srv_si else DE_MENOS
        elif srv_si:
            resultado = SALTEO if cli_no else DE_MAS
        else:
            resultado = CONSISTENTE
    elif protegida or (cli_si and cli_no) or not (cli_si or cli_no):
        # Un boton escondido no prueba que el servidor niegue.
        resultado = SIN_RESOLVER
    else:
        # 🔴 Una opcion de presentacion local, sin recurso protegido: se resuelve con el cliente y una
        # diferencia ahi no es una falla de Vu8.
        resultado = CONSISTENTE
    detalle["result"] = resultado
    return resultado, detalle


def _paso_comparacion(x):
    salida = x["salida"]
    mapping = x["mapping"]
    protegidas = _nfcs(mapping.get("protectedOperationRefs"))
    permitidas = _ids(x, ACCESO, DEL_SERVIDOR + DEL_CLIENTE, (PERMITIDO,))
    resultados = []
    for campo, esperadas, del_registro in (
            ("operations", x["esperado"]["operations"], protegidas),
            ("dataScopes", x["esperado"]["dataScopes"], _nfcs(mapping.get("dataScopeRefs")))):
        universo = sorted(set(esperadas) | set(del_registro)
                          | set(_nfcs(r for e in permitidas for r in e.get(campo) or [])))
        for ref in universo:
            protegida = campo == "dataScopes" or ref in protegidas
            resultado, detalle = _comparar(x, campo, ref, ref in esperadas, protegida)
            resultados.append(resultado)
            salida["comparison"].append(detalle)
            if resultado != SIN_RESOLVER:
                salida["evidenceUsed"]["access"].extend(
                    detalle["server"]["allowed"] + detalle["server"]["denied"]
                    + detalle["client"]["allowed"] + detalle["client"]["denied"])
    for falla in ORDEN_DE_LAS_FALLAS:
        if falla in resultados:
            return falla, "el acceso efectivo no coincide con el esperado: %s" % falla
    if not resultados:
        return _abierto(salida["blockedBy"]), ("no hay ninguna operacion ni alcance que comparar: el "
                                               "acceso efectivo no consta")
    if SIN_RESOLVER in resultados:
        # Si lo que faltaba era una prueba que no se pudo leer, se dice eso.
        return _abierto(salida["blockedBy"]), ("el acceso efectivo de alguna operacion o alcance no "
                                               "consta con evidencia citada")
    # Lo no citado que dice que hay una falla -de mas o de menos- nunca hace FAIL, y tampoco se elige.
    no_citadas = [e["evidenceId"] for e in _ids(x, ACCESO, DEL_SERVIDOR + DEL_CLIENTE, (PERMITIDO, NEGADO),
                                                solo_citadas=False)
                  if not _citada(e, x["citados"]) and _dice_falla(e, x["esperado"])]
    if no_citadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_MAPEO, "una evidencia no citada dice que el acceso no es el esperado"
    return None, ""


def _paso_cambio(x):
    salida = x["salida"]
    items = _ids(x, REVOCADO, DEL_SERVIDOR, (MAS_ALLA, DENTRO, NO_VIGENTE))
    mas_alla = sorted(e["evidenceId"] for e in items if e.get("value") == MAS_ALLA)
    no_citadas = sorted(e["evidenceId"] for e in _ids(x, REVOCADO, DEL_SERVIDOR, (MAS_ALLA,),
                                                      solo_citadas=False)
                        if not _citada(e, x["citados"]))
    semantica = x["cambio"]["resolved"]
    if mas_alla and semantica == RESUELTA:
        salida["evidenceUsed"]["roleChange"] = mas_alla
        return DE_MAS, ("un rol revocado sigue vigente mas alla de la ventana de refresco que el "
                        "proyecto documenta")
    if semantica is None:
        return SIN_CAMBIO, "la semantica de cambio de rol no consta con evidencia citada"
    if mas_alla:
        salida["contradictedBy"].extend(mas_alla)
        return SIN_CAMBIO, "la semantica dice que los roles no cambian en sesion y una evidencia dice que si"
    if no_citadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_CAMBIO, "una evidencia no citada dice que un rol revocado sigue vigente"
    salida["evidenceUsed"]["roleChange"] = sorted(e["evidenceId"] for e in items)
    return None, ""


def _paso_declarado(x):
    m = x["mapping"]
    if m.get("result") != CONSISTENTE:
        # Declarar la falla sin la evidencia que la establece no es FAIL.
        return SIN_MAPEO, "el registro no declara el mapping consistente, y la evidencia no lo establece"
    if m.get("verificationMode") == SIN_VERIFICAR:
        return SIN_MAPEO, "el registro dice que el mapping no se verifico"
    return None, ""


def evaluar_mapping(superficie, mapping, contexto, d):
    """Un mapping, solo: su resultado y la evidencia que lo sostiene, por id."""
    cat, crudas = d["catalog"], d["raw"]
    sid, mid = _ev.nfc(superficie.get("surfaceId")), _ev.nfc(mapping.get("mappingId"))
    citados = _ev.claves(superficie.get("evidence")) | _ev.claves(mapping.get("evidence"))
    roles = _nfcs(mapping.get("assignedRoleRefs"))
    salida = {"mappingId": mid, "assignedRoleRefs": [str(r) for r in roles],
              "expectedProfileRef": mapping.get("expectedProfileRef"),
              "observedProfileRef": mapping.get("observedProfileRef"),
              "declaredResult": mapping.get("result"),
              "verificationMode": mapping.get("verificationMode"),
              # 🔴 `testIdentityRef` no sale: es texto libre, no hace falta para el resultado, y la
              # regla de salida compartida no reconoce toda credencial que alguien pueda poner ahi.
              "expected": {"operations": [], "dataScopes": []}, "comparison": [],
              "evidenceUsed": {"mapping": [], "access": [], "roleChange": []},
              "contradictedBy": [], "issues": [],
              # Lo citado que dice algo de acceso o del mapeo y no es de una clase que lo sostenga.
              "insufficient": sorted(e["evidenceId"] for e in cat.values() if _citada(e, citados)
                                     and e["sourceType"] in INSUFICIENTES)}
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, citados, sid, mid)
    x = {"cat": cat, "citados": citados, "sid": sid, "mid": mid, "roles": roles, "mapping": mapping,
         "salida": salida, "esperado": None}
    x.update(contexto)
    pasos = [_paso_fuente(x), _paso_varios(x), _paso_esperado(x)]
    if x["esperado"] is not None:
        # Con lo esperado a la vista, pesa tambien la prueba no citada que niega algo esperado.
        salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, citados, sid, mid,
                                                          esperado=x["esperado"])
        pasos.append(_paso_comparacion(x))
    pasos += [_paso_cambio(x), _paso_declarado(x)]
    # 🔴 En el orden de la spec, y lo que falla no lo tapa un paso anterior sin resolver.
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = [p for p in pasos if p[0] is not None]
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]
    # 🔴 Lo que no se pudo leer y pesa impide el PASS: un item con `outcome` fuera de lo legible es
    # ilegible igual que uno mal formado, de la clase que sea. Pesa si se lo cita, o si nombra el
    # mapping y dice una falla. Una prueba insegura o sin objetivo pasa por el bloqueo, que dice por que.
    sin_leer = [e for e in cat.values() if _lectura(e)[:2] == (False, None)
                and (_citada(e, citados) or (_nombra(e, sid, mid, False)
                                             and _dice_falla(e, x["esperado"])))]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | set(_ev.ilegibles_sobre(mid, cat, crudas))
                       | set(_ev.ilegibles_sobre(sid, cat, crudas))
                       | {e["evidenceId"] for e in sin_leer})
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre el mapping o su superficie: %s"
                                % ", ".join(str(i) for i in ilegibles))
    final, motivo = _bloquear(estado, motivo, salida["blockedBy"], ilegibles)
    if final != estado:
        # Lo bloqueado no se sostiene con nada: no queda evidencia usada.
        salida["evidenceUsed"] = {k: [] for k in salida["evidenceUsed"]}
    salida["evidenceUsed"] = {k: sorted(set(v)) for k, v in salida["evidenceUsed"].items()}
    salida["contradictedBy"] = sorted(set(salida["contradictedBy"]))
    salida["insufficient"] = sorted(set(salida["insufficient"]))
    salida["issues"] = sorted(set(salida["issues"]))
    salida["comparison"] = _ev.ordenadas(salida["comparison"])
    salida["state"] = final
    salida["result"] = (CONSISTENTE if final == PASA else final if final in ORDEN_DE_LAS_FALLAS
                        else SIN_RESOLVER)
    queda = set(salida["blockedBy"]) if final not in FALLAS else set()
    salida["states"] = sorted(({p[0] for p in pasos if p[0] is not None} | {final} | queda) - {PASA})
    salida["reason"] = motivo
    return salida


def _de_lo_evaluado(estados):
    """(estado, motivo) de un conjunto de estados."""
    for falla in ORDEN_DE_LAS_FALLAS:
        if falla in estados:
            return falla, "al menos un mapping no respeta los roles; los que cumplen no lo tapan"
    if FALLA in estados:
        return FALLA, "al menos un mapping no respeta los roles"
    for e in ORDEN_DE_LO_ABIERTO:
        if e in estados:
            return e, "hay algo material sin resolver"
    return PASA, ""


def evaluar_superficie(superficie, d):
    """Una superficie con sus mappings. Un mapping en verde no tapa otro."""
    cat = d["catalog"]
    sid = _ev.nfc(superficie.get("surfaceId"))
    contexto = {"fuente": _fuente(superficie, cat),
                "varios": _semantica(superficie, "multiRoleSemantics", VARIOS, DE_VARIOS, SIN_VARIOS,
                                     cat),
                "cambio": _semantica(superficie, "roleChangeSemantics", CAMBIO, DE_CAMBIO, SIN_CAMBIO,
                                     cat)}
    mappings = list(superficie.get("mappings") or [])
    evaluados = _ev.ordenadas(evaluar_mapping(superficie, m, contexto, d) for m in mappings)
    ids = [m["mappingId"] for m in evaluados]
    cubiertos = {r for m in evaluados for r in m["assignedRoleRefs"]}
    faltan = [r for r in contexto["fuente"]["roles"] if r not in cubiertos]
    abiertos = [contexto["fuente"]["state"], contexto["varios"]["state"], contexto["cambio"]["state"]]
    if not mappings or faltan or len(set(ids)) != len(ids):
        abiertos.append(SIN_MAPEO)
    ambiente = superficie.get("environment")
    estado, motivo = _de_lo_evaluado([m["state"] for m in evaluados] + abiertos)
    return {"surfaceId": sid, "environment": ambiente if isinstance(ambiente, str) else None,
            "roleAssignmentSource": contexto["fuente"], "multiRoleSemantics": contexto["varios"],
            "roleChangeSemantics": contexto["cambio"],
            "coverage": {"sourceRoles": list(contexto["fuente"]["roles"]),
                         "missingRoles": [str(r) for r in faltan],
                         "duplicatedMappings": sorted({str(i) for i in ids if ids.count(i) > 1})},
            "mappings": evaluados, "state": estado, "reason": motivo}


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de Vu8, superficie por superficie y mapping por mapping.

    `caso`:

        {"registry": {...},         # el registro de Vu8; opcional
         "evidence": [...]}         # el catalogo, cerrado
    """
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    valor = _combinar(d["value"], senal)
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "signalValue": valor, "surfaces": [], "issues": [], "coverage": d["coverage"]}
    if d["problem"]:
        salida["issues"].append(d["problem"])
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    salida["issues"].sort()
    registrados = [(_ev.nfc(s.get("surfaceId")), _ev.nfc(m.get("mappingId")))
                   for s in d["surfaces"] for m in s.get("mappings") or []]
    c = d["coverage"]
    sueltos, motivos = _bloqueos(d["catalog"], d["cited"], registrados=registrados,
                                 superficies=sorted(set(c["registered"]) | set(c["namedBySignal"])))
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos

    if valor == _senales.SIN_RESOLVER:
        estado, motivo = SIN_APLICABILIDAD, "no consta si la aplicacion tiene roles que gobiernan el perfil"
    elif valor == _senales.FALSA:
        estado, motivo = NO_APLICA, "una evidencia autoritativa establece que no hay un modelo de roles"
    else:
        # 🔴 Cada superficie se evalua sola.
        salida["surfaces"] = _ev.ordenadas(evaluar_superficie(s, d) for s in d["surfaces"])
        estado, motivo = _agregado(salida["surfaces"], d)
    ilegibles = sorted({i for s in c["registered"] for i in _ev.ilegibles_sobre(s, d["catalog"], d["raw"])}
                       | {r for s in d["surfaces"] for r in _ev.claves(s.get("evidence"))
                          if r not in d["catalog"]})
    final, motivo = _bloquear(estado, motivo, sueltos, ilegibles)
    return _cerrar(salida, final, motivo, estado)


def _agregado(superficies, d):
    estados = [s["state"] for s in superficies]
    c = d["coverage"]
    abiertos = []
    # Sin superficies, o con una que la senal nombra y no esta: la fuente no consta.
    if not superficies or c["missingSurfaces"]:
        abiertos.append(SIN_FUENTE)
    if c["duplicatedSurfaces"]:
        abiertos.append(SIN_MAPEO)
    estado, motivo = _de_lo_evaluado(estados + abiertos)
    if estado in abiertos and estado not in estados:
        motivo = ("no esta entero: superficies sin entrada %s, repetidas %s"
                  % (c["missingSurfaces"] or "-", c["duplicatedSurfaces"] or "-"))
    return estado, motivo


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None,) + RESUELTAS:
        todos.add(previo)
    for s in salida["surfaces"]:
        if s["state"] != PASA:
            todos.add(s["state"])
        for m in s["mappings"]:
            todos.update(m.get("states") or [])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


def evidencia_usada(resultado):
    """Los ids que sostienen el resultado: fuente, semanticas y mappings."""
    r = resultado if isinstance(resultado, dict) else {}
    ids = set()
    for s in r.get("surfaces") or []:
        for campo in ("roleAssignmentSource", "multiRoleSemantics", "roleChangeSemantics"):
            ids.update((s.get(campo) or {}).get("evidenceUsed") or [])
        for m in s.get("mappings") or []:
            for u in (m.get("evidenceUsed") or {}).values():
                ids.update(u)
    return sorted(i for i in ids if isinstance(i, str))


# -- hacia seguridad.resultado ----------------------------------------------------------------------

def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu8", ...)`, desde la salida de `evaluar`.

    Vu8 no tiene algoritmo propio en `seguridad.py`: va por el generico. Los dos controles de la fila
    llevan el estado del check -PASS, FAIL o el estado abierto tal cual- con la evidencia por id. Un
    resultado que no dice ser de este check no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return {}, {}
    estado = r["state"]
    control = FALLA if estado in FALLAS else estado
    evidencia = evidencia_usada(r) or (["check:%s" % CONTROL] if estado in RESUELTAS + FALLAS else [])
    doc = {"controlResults": {c: {"result": control, "evidence": evidencia}
                              for c in (POLICY, CONTROL)}}
    valor = r.get("signalValue")
    # 🔴 Un NOT_APPLICABLE que el bloqueo impidio no vuelve a entrar por la senal.
    senales = ({SENAL: True} if valor == _senales.VERDADERA
               else {SENAL: False} if valor == _senales.FALSA and estado == NO_APLICA else {})
    return _ev.depurar(doc), senales


# -- hacia la refutacion atomica --------------------------------------------------------------------

def para_refutacion(resultado, unidad):
    """La entrada de `checks.json` para una unidad de `ES0902.Vu8`, o `None`.

    Atada a la unidad de trabajo, a la huella de la evidencia y a la revision de esa unidad. El
    estado es PASS o FAIL, que cierran la unidad sin refutador; un sin resolver viaja tal cual y la
    deja pendiente. Un resultado ajeno, o una unidad de otra regla, no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    u = unidad if isinstance(unidad, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return None
    if (u.get("standard") or {}).get("ruleKey") != CLAVE or not u.get("evidenceFingerprint"):
        return None
    estado = FALLA if r["state"] in FALLAS else r["state"]
    return _ev.depurar({"control": CONTROL, "ruleKey": CLAVE, "workUnitId": u.get("workUnitId"),
                        "state": estado, "repoRevision": u.get("repoRevision"),
                        "evidenceFingerprint": u["evidenceFingerprint"],
                        "evidence": evidencia_usada(r)})
