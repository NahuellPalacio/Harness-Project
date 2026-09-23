"""Check normativo: cada pagina de autenticacion tiene captcha o bloqueo de usuario activo.

    source: ES0902 / 6.2 / 6 / Vu1

    "Toda pagina de autenticacion debe contener captcha o bloqueo de usuarios por intentos de
     sesion, funcionalidad que se encuentra contenida en OpenID."

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de latencia
y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control normativo.

🔴 **Es una `o`.** Una pagina cumple con captcha activo, con bloqueo activo, o con los dos. Exigir
los dos inventa una exigencia; aceptar un WAF, un limite por IP, MFA o la complejidad de la
contrasena la vacia. Esos controles sirven y no son los que nombra Vu1.

🔴 **Las paginas salen del inventario de C1.** No hay un segundo inventario: el de C1 se lee con el
cargador de C1 y su schema, y el registro de Vu1 guarda evidencia de proteccion por `surfaceId`.
La senal `authenticationPagePresent` se deriva de ahi, y encenderla es mas barato que apagarla:
delegar el login al proveedor de identidad NO es no tener pagina, es tener la del proveedor.

🔴 **Activo, no soportado.** "El proveedor soporta proteccion contra fuerza bruta" no es un bloqueo
activo en esta pagina. Cuenta la evidencia de que el mecanismo esta activo, de la clase que el
mecanismo declara, atada a la pagina por su id.

🔴 **Ningun umbral.** El estandar no dice cuantos intentos, cuanto dura el bloqueo ni cuando aparece
el captcha, y este modulo tampoco. Lo que traiga la evidencia sale tal cual, como no normativo.

🔴 **No se prueba nada.** Probar un bloqueo es bloquear una cuenta. Este modulo no abre conexiones
ni lanza procesos: lee la evidencia de una prueba ya hecha y decide si era segura. Una prueba en
produccion, sin identidad dedicada o sin autorizacion no cuenta, y eso no es FAIL: es no saber.

🔴 **OpenID no es Vu1, y C1 no es Vu1.** Que el estandar diga que la funcionalidad esta contenida en
OpenID no hace pasar a Vu1 porque la aplicacion hable OIDC. Este check no recibe el resultado de
C1, y su PASS no dice nada de C1.
"""
import importlib.util
import io
import json
import os
import re
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

import rutas                                        # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "authentication-abuse-protection"
POLICY = "authentication-abuse-protection-required"
TIPO = "CHECK"
REGLA = "Vu1"
CLAVE = "ES0902.Vu1"
SENAL = "authenticationPagePresent"

ARCHIVO = "authentication-abuse-protection.json"
SCHEMA = "authentication-abuse-protection.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = ("Toda página de autenticación debe contener captcha o bloqueo de usuarios por "
                "intentos de sesión, funcionalidad que se encuentra contenida en OpenID.")


# 🔴 El inventario y el catalogo son los de C1, con su cargador. Se importa el modulo, no se corre
# su evaluacion ni se lee su resultado.
def _modulo_de_c1():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oidc-keycloak-integration.py")
    spec = importlib.util.spec_from_file_location("_vu1_inventario_de_superficies", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_C1 = _modulo_de_c1()

# -- los estados, con el nombre exacto que declara el paquete ----------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "AUTHENTICATION_PAGE_COVERAGE_UNRESOLVED"
SIN_PROTECCION = "AUTHENTICATION_ABUSE_PROTECTION_UNRESOLVED"
INACTIVA = "AUTHENTICATION_ABUSE_PROTECTION_INACTIVE"
PRUEBA_INSEGURA = "AUTH_ABUSE_RUNTIME_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_COBERTURA, SIN_PROTECCION, INACTIVA,
           PRUEBA_INSEGURA, SIN_OBJETIVO)

# Por pagina.
CAPTCHA_ACTIVO = "CAPTCHA_ACTIVE"
BLOQUEO_ACTIVO = "LOCKOUT_ACTIVE"
LOS_DOS = "BOTH_ACTIVE"
NINGUNO = "NO_ALLOWED_MECHANISM_ACTIVE"
SIN_RESOLVER = "PROTECTION_UNRESOLVED"
RESULTADOS_DE_PAGINA = (CAPTCHA_ACTIVO, BLOQUEO_ACTIVO, LOS_DOS, NINGUNO, SIN_RESOLVER)

# -- los dos mecanismos, y nada mas -------------------------------------------------

CAPTCHA = "CAPTCHA"
BLOQUEO = "USER_LOCKOUT_AFTER_FAILED_ATTEMPTS"
MECANISMOS = (CAPTCHA, BLOQUEO)

ACTIVO = "ACTIVE"
INACTIVO = "INACTIVE"
NO_DECLARADO = "NOT_DECLARED"

# Las clases de fuente que sostienen un mecanismo: las del enum `evidenceMode` del registro. La
# evidencia tiene que ser de la clase que el mecanismo declara.
PRUEBA = "AUTHORIZED_RUNTIME_TEST"
DE_LA_APLICACION = "APPLICATION_CONFIGURATION"
MODOS = ("PROVIDER_CONFIGURATION", DE_LA_APLICACION, "OFFICIAL_PROVIDER_EVIDENCE",
         "OFFICIAL_ASSESSMENT_EVIDENCE", PRUEBA, "OTHER_AUTHORITATIVE_EVIDENCE")

# Lo que dice que algo PUEDE hacerse, no que se hace. Nombrado para que la salida diga por que no
# alcanza.
CAPACIDADES = ("PROVIDER_CAPABILITY", "LIBRARY_CAPABILITY", "FRAMEWORK_CAPABILITY",
               "REPOSITORY_DEPENDENCY", "OIDC_CONFIGURED")
VALORES_DE_CAPACIDAD = ("SUPPORTED", "AVAILABLE")
INSUFICIENTES = CAPACIDADES + ("README_STATEMENT", "SCREENSHOT", "INFORMAL_STATEMENT",
                               "AGENT_STATEMENT", "SKILL_OUTPUT", "FRAMEWORK_DEFAULT")

# 🔴 Los controles que sirven y no son Vu1. No satisfacen nada; se informan.
SUSTITUTOS = ("WAF", "IP_RATE_LIMITING", "GENERIC_THROTTLING", "GATEWAY_QUOTA",
              "DEVICE_FINGERPRINTING", "BOT_SCORING", "MFA", "PASSWORD_COMPLEXITY")
EQUIVALENCIA = "MECHANISM_EQUIVALENCE"
AUTORIDADES_DE_EQUIVALENCIA = ("GCBA_NORMATIVE", "ASI_POLICY")

# -- la pagina ----------------------------------------------------------------------

PAGINA = "AUTHENTICATION_PAGE"
INTERACTIVA = "INTERACTIVE"
NO_INTERACTIVA = "NON_INTERACTIVE"
HAY_PAGINA = "PAGE"
NO_HAY_PAGINA = "NO_PAGE"

# Apagar la regla exige autoridad. Encenderla, no.
AUTORITATIVAS_PARA_APAGAR = ("DGSEI_IDENTITY_REGISTRATION", "IDENTITY_TICKET",
                             "ARCHITECTURE_DECISION", "PROJECT_CONTRACT",
                             "OFFICIAL_IDENTITY_GUIDANCE", "PROVIDER_CONFIGURATION",
                             "PROJECT_CONFIGURATION")

DE_LA_APP = "APPLICATION"
DEL_PROVEEDOR = "IDENTITY_PROVIDER"
DUENO_SIN_RESOLVER = "UNRESOLVED"

# -- la prueba en ejecucion ----------------------------------------------------------

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")
CONFIRMADA = "CONFIRMED"
NO_DISPONIBLE = "UNAVAILABLE"

# -- lo que no se guarda ---------------------------------------------------------------

# 🔴 Formas de credencial. No es el detector del hook: es una regla del registro, y falla cerrado.
# La clave TERMINA en la palabra: `DB_PASSWORD=`, `api_token:` y `mysecret:` son la forma de
# `password=`; `passwordPolicy:`, `tokenLifespan=`, `Bypass:` y el `:secret:` de un ARN no lo son.
SECRETOS = tuple(re.compile(p) for p in (
    r"(?i)(?<![:/\w-])[\w-]*?(password|passwd|pwd|secret|token|api[_-]?key)[\"']?\s*[:=]\s*\S",
    r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}",
    r"://[^/\s:@]+:[^/\s@]+@",
    r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"))


# -- el registro ----------------------------------------------------------------------

def cargar(desde=None):
    """El registro del proyecto. Vacio si no esta: vacio es valido y no protege nada."""
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


def _textos(dato, camino="$"):
    if isinstance(dato, dict):
        for k, v in dato.items():
            yield camino, str(k)
            yield from _textos(v, "%s.%s" % (camino, k))
    elif isinstance(dato, list):
        for i, v in enumerate(dato):
            yield from _textos(v, "%s[%d]" % (camino, i))
    elif isinstance(dato, str):
        yield camino, dato


def _sin_secreto(valor):
    """El valor, o `[redactado]` si tiene forma de credencial. Lo del inventario tambien sale."""
    if isinstance(valor, str) and any(p.search(valor) for p in SECRETOS):
        return "[redactado]"
    return valor


def con_secretos(doc):
    """Donde hay un texto con forma de credencial: `surfaces[i]` o `$`. Nunca el texto, ni una
    clave: una clave tambien puede ser el secreto."""
    def tiene(dato):
        return any(any(p.search(t) for p in SECRETOS) for _, t in _textos(dato))
    if not isinstance(doc, dict):
        return ["$"] if tiene(doc) else []
    salida = set()
    for k, v in doc.items():
        if k == "surfaces" and isinstance(v, list):
            salida.update("surfaces[%d]" % i for i, x in enumerate(v) if tiene(x))
        elif tiene({k: v}):
            salida.add("$")
    return sorted(salida)


def _depurar(dato):
    """🔴 La regla de salida, una sola: nada con forma de credencial sale, venga de donde venga
    -el inventario de C1, el registro, el catalogo, `detectedSurfaces`, un mensaje de error-."""
    if isinstance(dato, dict):
        return {k: _depurar(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [_depurar(v) for v in dato]
    return _sin_secreto(dato)


def entradas(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del registro instalado."""
    declarado = (caso or {}).get("protection")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el registro de proteccion no se pudo leer"
    secretos = con_secretos(doc)
    if secretos:
        return [], ("el registro de proteccion trae textos con forma de credencial en %s; no se "
                    "lee ni se repite" % ", ".join(secretos))
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de proteccion no se pudo validar: falta su schema o el validador"
    if errores:
        # 🔴 Los errores del validador repiten valores del registro, y un valor puede ser un secreto
        # sin forma conocida metido en un enum. Se dice cuantos, no cuales.
        return [], "el registro de proteccion no valida contra su schema: %d errores" % len(errores)
    return list(doc.get("surfaces") or []), ""


# -- la senal ---------------------------------------------------------------------------

def _nombra(evidencia, superficie):
    nombradas = evidencia.get("surfaceIds")
    return (isinstance(nombradas, list) and superficie.get("surfaceId") in nombradas
            and evidencia.get("scope") == superficie.get("scope")
            and bool((evidencia.get("reference") or "").strip()))


def pagina_de(superficie, catalogo):
    """(estado, dueno, evidencia). Si la superficie tiene pagina de autenticacion, y de quien."""
    delegada = superficie.get("credentialEntryDelegated")
    dueno = {True: DEL_PROVEEDOR, False: DE_LA_APP}.get(delegada)
    citadas = superficie.get("evidence") or []
    propias = [catalogo[r] for r in citadas if r in catalogo]
    sobre_pagina = [e for e in propias if PAGINA in (e.get("establishes") or [])
                    and _nombra(e, superficie)]
    encienden = sorted(e["evidenceId"] for e in sobre_pagina if e.get("value") == INTERACTIVA)
    apagan = sorted(e["evidenceId"] for e in sobre_pagina if e.get("value") == NO_INTERACTIVA
                    and e.get("sourceType") in AUTORITATIVAS_PARA_APAGAR)
    enciende = isinstance(delegada, bool) or bool(encienden)
    if enciende and apagan:
        return "UNRESOLVED", dueno, encienden + apagan
    if enciende:
        return HAY_PAGINA, dueno, encienden
    # Lo ilegible podia ser el que decia que hay pagina: sin leerlo, no se apaga.
    if apagan and delegada is None and all(r in catalogo for r in citadas):
        return NO_HAY_PAGINA, None, apagan
    return "UNRESOLVED", dueno, []


def derivar(caso, autenticacion=None, desde=None):
    """La senal derivada del inventario de C1, con cada superficie y la cobertura."""
    entrada = caso if isinstance(caso, dict) else {}
    lista, problema = _C1.superficies(entrada, desde)
    catalogo, repetidos, torcidas = _C1._catalogo(entrada)
    ids = [s.get("surfaceId") for s in lista]
    detectadas = entrada.get("detectedSurfaces")
    detectadas_torcidas = detectadas is not None and not (
        isinstance(detectadas, list) and all(isinstance(d, str) and d for d in detectadas))
    vistas = sorted(set(detectadas or [])) if not detectadas_torcidas else []
    paginas = []
    for s in lista:
        estado, dueno, usada = pagina_de(s, catalogo)
        paginas.append({"surfaceId": s.get("surfaceId"), "scope": _sin_secreto(s.get("scope")),
                        "environment": s.get("environment"),
                        "provider": _sin_secreto(s.get("currentProvider")), "page": estado,
                        "pageOwnership": dueno, "evidence": usada,
                        "sourceReference": "%s#%s" % (_C1.ARCHIVO, s.get("surfaceId"))})
    paginas.sort(key=lambda p: (str(p["surfaceId"]), json.dumps(p, sort_keys=True, default=str)))
    cobertura = {"inventoried": sorted({str(i) for i in ids}), "detected": vistas,
                 "missing": sorted(set(vistas) - {str(i) for i in ids}),
                 "duplicated": sorted({str(i) for i in ids if ids.count(i) > 1}),
                 "detectedMalformed": detectadas_torcidas,
                 "unresolved": sorted(str(p["surfaceId"]) for p in paginas
                                      if p["page"] == "UNRESOLVED")}
    completa = not (cobertura["missing"] or cobertura["duplicated"] or detectadas_torcidas
                    or cobertura["unresolved"])
    if problema:
        valor = _senales.SIN_RESOLVER
    elif any(p["page"] == HAY_PAGINA for p in paginas):
        valor = _senales.VERDADERA
    elif paginas and completa:
        valor = _senales.FALSA
    elif (not paginas and completa and not vistas
          and _C1._valor_de_senal(autenticacion) == _senales.FALSA):
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    # 🔴 Una entrada del registro de proteccion dice "aca hay una pagina". Puede ser la que
    # contradice al FALSE, y un registro ilegible tambien: con cualquiera de las dos no se apaga.
    registradas, ilegible = entradas(entrada, desde)
    sin_pagina = sorted({str(e.get("surfaceId")) for e in registradas}
                        - {str(p["surfaceId"]) for p in paginas if p["page"] == HAY_PAGINA})
    cobertura["protectionEntriesWithoutPage"] = sin_pagina
    if valor == _senales.FALSA and (sin_pagina or ilegible):
        valor = _senales.SIN_RESOLVER
    return {"value": valor, "pages": paginas, "coverage": cobertura, "problem": problema,
            "catalog": catalogo, "repeated": repetidos, "malformed": torcidas,
            "surfaces": lista}


def senal(caso, autenticacion=None, desde=None):
    """`authenticationPagePresent` como documento de senal, resuelto por `senales`."""
    d = derivar(caso, autenticacion, desde)
    evidencia = []
    if d["value"] == _senales.VERDADERA:
        base = [p for p in d["pages"] if p["page"] == HAY_PAGINA]
    elif d["value"] == _senales.FALSA:
        base = d["pages"]
    else:
        base = []
    for p in base:
        evidencia.append({"evidenceId": "surface:%s" % _sin_secreto(p["surfaceId"]),
                          "sourceType": "REPOSITORY_CONFIGURATION",
                          "reference": p["sourceReference"],
                          "claim": "la superficie `%s` %s pagina de autenticacion (%s)"
                                   % (p["surfaceId"],
                                      "tiene" if p["page"] == HAY_PAGINA else "no tiene",
                                      p["pageOwnership"] or "-"),
                          "supports": d["value"]})
    if d["value"] == _senales.FALSA and not base:
        evidencia.append({"evidenceId": "authenticationPresent",
                          "sourceType": "REPOSITORY_CONFIGURATION",
                          "reference": "authenticationPresent",
                          "claim": "la aplicacion no autentica usuarios y el inventario esta "
                                   "vacio", "supports": d["value"]})
    return _depurar(_senales.producir(SENAL, evidencia, {"type": "DETERMINISTIC"}, d["value"],
                                      desde))


def _combinar(derivado, externo):
    """El valor de la senal: el derivado, salvo que quien llama traiga otro."""
    if externo is None:
        return derivado
    valor = _C1._valor_de_senal(externo)
    if valor == derivado:
        return valor
    # Encender sobre lo que no se sabe es seguro. Cualquier otro desacuerdo no se elige.
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- un mecanismo -------------------------------------------------------------------------

def _de_la_pagina(e, superficie, dueno):
    if not _nombra(e, superficie):
        return False
    if e.get("sourceType") not in MODOS:
        return False
    if dueno == DEL_PROVEEDOR and e.get("sourceType") == DE_LA_APLICACION:
        return False
    ambiente = e.get("environment")
    if ambiente is not None and ambiente != superficie.get("environment"):
        return False
    return True


def prueba_segura(prueba, superficie):
    """(motivos, resultado). Sin motivos, la prueba era segura. No ejecuta nada."""
    if not isinstance(prueba, dict):
        return ["NO_RUNTIME_TEST_RECORD"], None
    motivos = []
    if prueba.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    ambiente = prueba.get("environment")
    if ambiente in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    elif ambiente == PRODUCCION:
        motivos.append("PRODUCTION")
    elif ambiente not in AMBIENTES_DE_PRUEBA:
        motivos.append("ENVIRONMENT_UNKNOWN")
    elif ambiente != superficie.get("environment"):
        motivos.append("ENVIRONMENT_MISMATCH")
    identidad = prueba.get("dedicatedTestIdentityRef")
    if not (isinstance(identidad, str) and identidad.strip()):
        motivos.append("NO_DEDICATED_TEST_IDENTITY")
    return sorted(motivos), prueba.get("result")


def _lectura(e, motivos, resultado):
    """(cuenta, bloqueo). Si una evidencia se puede leer por lo que dice, o que la bloquea.

    🔴 La misma regla para la que dice ACTIVE y para la que dice INACTIVE. Una prueba insegura o
    sin objetivo no cuenta para ninguno de los dos lados: ni aprueba, ni hace FAIL.
    """
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE or resultado == NO_DISPONIBLE:
            return False, SIN_OBJETIVO
        if motivos:
            return False, PRUEBA_INSEGURA
        if e.get("outcome") != CONFIRMADA or resultado not in (None, CONFIRMADA):
            return False, "UNREADABLE"
        return True, None
    if e.get("outcome") not in (None, CONFIRMADA):
        return False, "UNREADABLE"
    return True, None


def _mecanismo(tipo, declarados, citadas, catalogo, superficie, dueno, prueba):
    """El estado de un mecanismo en una pagina, con lo que lo sostiene y lo que lo bloquea."""
    salida = {"type": tipo, "status": NO_DECLARADO, "declared": [], "evidenceUsed": [],
              "contradictedBy": [], "blockedBy": [], "thresholds": []}
    propias = [e for e in citadas if tipo in (e.get("establishes") or [])
               and _de_la_pagina(e, superficie, dueno)]
    motivos, resultado = prueba_segura(prueba, superficie)
    # 🔴 Lo que dice que NO se busca en todo el catalogo, no solo en lo citado: quien arma el
    # registro no elige que contradiccion se lee. Pero lo que la entrada no cita no se lee con la
    # prueba de ESTA entrada: puede impedir el PASS, y nunca hace FAIL.
    citados = {e["evidenceId"] for e in citadas}
    contra, dudosas = [], []
    for e in sorted(catalogo.values(), key=lambda x: x["evidenceId"]):
        if (tipo not in (e.get("establishes") or []) or e.get("value") != INACTIVO
                or not _de_la_pagina(e, superficie, dueno)):
            continue
        if e["evidenceId"] not in citados:
            dudosas.append(e["evidenceId"])
            continue
        cuenta, bloqueo = _lectura(e, motivos, resultado)
        if cuenta:
            contra.append(e["evidenceId"])
        else:
            dudosas.append(e["evidenceId"])
            if bloqueo in (PRUEBA_INSEGURA, SIN_OBJETIVO):
                salida["blockedBy"].append(bloqueo)
                if bloqueo == PRUEBA_INSEGURA:
                    salida["unsafe"] = motivos
    salida["contradictedBy"] = contra
    salida["unreadableContradictions"] = dudosas
    sostenidos = []
    for m in declarados:
        salida["declared"].append({"status": m.get("status"), "evidenceMode": m.get("evidenceMode")})
        if m.get("details") is not None:
            salida["thresholds"].append({"text": m["details"], "source": m.get("evidenceMode"),
                                         "normative": False})
        if m.get("status") != ACTIVO:
            continue
        for e in propias:
            if e.get("value") != ACTIVO or e.get("sourceType") != m.get("evidenceMode"):
                continue
            cuenta, bloqueo = _lectura(e, motivos, resultado)
            if bloqueo in (PRUEBA_INSEGURA, SIN_OBJETIVO):
                salida["blockedBy"].append(bloqueo)
                if bloqueo == PRUEBA_INSEGURA:
                    salida["unsafe"] = motivos
            if cuenta:
                sostenidos.append(e["evidenceId"])
    salida["declared"].sort(key=lambda d: json.dumps(d, sort_keys=True, default=str))
    salida["thresholds"].sort(key=lambda d: json.dumps(d, sort_keys=True, default=str))
    salida["blockedBy"] = sorted(set(salida["blockedBy"]))
    salida["evidenceUsed"] = sorted(set(sostenidos))
    estados = {m.get("status") for m in declarados}
    if sostenidos:
        limpio = not (contra or dudosas or INACTIVO in estados)
        salida["status"] = ACTIVO if limpio else "UNRESOLVED"
    elif estados == {INACTIVO}:
        # Simetrico: un INACTIVE declarado contra una evidencia legible que dice ACTIVE no se
        # elige. Ni FAIL ni PASS.
        a_favor = [e for e in catalogo.values() if tipo in (e.get("establishes") or [])
                   and e.get("value") == ACTIVO and _de_la_pagina(e, superficie, dueno)
                   and _lectura(e, motivos, resultado)[0]]
        salida["status"] = "UNRESOLVED" if a_favor else INACTIVO
    elif contra and not dudosas and ACTIVO not in estados:
        salida["status"] = INACTIVO
    elif declarados or propias or dudosas or contra:
        salida["status"] = "UNRESOLVED"
    return salida


# -- una pagina ---------------------------------------------------------------------------

def evaluar_pagina(pagina, superficie, propias, catalogo, registro_ilegible, crudas=()):
    """El estado de una pagina: sus dos mecanismos, lo que se informa y lo que la bloquea."""
    salida = {"surfaceId": pagina["surfaceId"], "scope": pagina["scope"],
              "environment": pagina["environment"], "provider": pagina["provider"],
              "pageOwnership": pagina["pageOwnership"], "mechanisms": {},
              "mechanismResult": SIN_RESOLVER, "substitutesObserved": [],
              "capabilityClaims": [], "equivalenceClaims": [], "issues": [],
              "runtimeTest": {"executed": False, "unsafe": []}}
    if registro_ilegible:
        return _con(salida, SIN_PROTECCION, "el registro de proteccion no se pudo leer")
    if not propias:
        return _con(salida, SIN_PROTECCION, "no hay evidencia de proteccion para esta pagina")
    if len(propias) > 1:
        return _con(salida, SIN_PROTECCION, "hay mas de una entrada de proteccion para esta "
                                            "pagina; no se elige una")
    entrada = propias[0]
    declarado = entrada.get("pageOwnership")
    derivado = pagina["pageOwnership"]
    # 🔴 El dueno sale del inventario (`credentialEntryDelegated`). El registro lo tiene que
    # repetir; no lo puede poner donde el inventario no lo dice.
    if declarado == DUENO_SIN_RESOLVER or derivado is None:
        return _con(salida, SIN_PROTECCION, "no se sabe de quien es la pagina: el inventario no "
                                            "dice si el ingreso de credenciales esta delegado")
    if declarado != derivado:
        return _con(salida, SIN_PROTECCION, "el registro dice que la pagina es de `%s` y el "
                                            "inventario de superficies dice `%s`"
                    % (declarado, derivado))
    dueno = salida["pageOwnership"]

    ids = entrada.get("evidence") or []
    citadas = [catalogo[r] for r in ids if r in catalogo]
    ilegibles = sorted({r for r in ids if r not in catalogo})
    # 🔴 Lo ilegible que nombra la pagina impide el PASS aunque nadie lo cite: una evidencia
    # repetida o mal formada que dice "inactivo" no se descarta en silencio.
    sid = str(pagina["surfaceId"])
    for e in (crudas if isinstance(crudas, list) else []):
        legible = isinstance(e, dict) and catalogo.get(e.get("evidenceId")) is e
        if not legible and sid in json.dumps(e, sort_keys=True, default=str):
            ilegibles.append(str(e.get("evidenceId")) if isinstance(e, dict) else "malformed-evidence")
    ilegibles = sorted(set(ilegibles))
    for e in sorted(catalogo.values(), key=lambda x: x["evidenceId"]):
        # Las equivalencias se leen en todo el catalogo, como las contradicciones.
        if (EQUIVALENCIA in (e.get("establishes") or [])
                and e.get("sourceType") in AUTORIDADES_DE_EQUIVALENCIA
                and isinstance(e.get("value"), str) and e["value"].strip()
                and e["value"] not in MECANISMOS + (ACTIVO, INACTIVO) and _nombra(e, pagina)):
            salida["equivalenceClaims"].append(e["evidenceId"])
    for e in citadas:
        for s in (e.get("establishes") or []) + [e.get("sourceType")]:
            if s in SUSTITUTOS:
                salida["substitutesObserved"].append(s)
        if any(m in (e.get("establishes") or []) for m in MECANISMOS) and (
                e.get("sourceType") in CAPACIDADES or e.get("value") in VALORES_DE_CAPACIDAD):
            salida["capabilityClaims"].append(e["evidenceId"])
    for campo in ("substitutesObserved", "capabilityClaims", "equivalenceClaims"):
        salida[campo] = sorted(set(salida[campo]))

    prueba = entrada.get("runtimeTest")
    por_tipo = {t: _mecanismo(t, [m for m in entrada.get("mechanisms") or []
                                  if m.get("type") == t],
                              citadas, catalogo, pagina, dueno, prueba) for t in MECANISMOS}
    salida["mechanisms"] = por_tipo
    salida["runtimeTest"]["unsafe"] = sorted({u for m in por_tipo.values()
                                              for u in m.get("unsafe") or []})

    if ilegibles:
        salida["issues"].append("hay evidencia que nombra la pagina y no se pudo leer: %s"
                                % ", ".join(ilegibles))
        return _con(salida, SIN_PROTECCION, "hay evidencia ilegible sobre la pagina, y esa podia "
                                            "ser la que decia que el mecanismo esta inactivo")
    captcha, bloqueo = por_tipo[CAPTCHA]["status"], por_tipo[BLOQUEO]["status"]
    if captcha == ACTIVO and bloqueo == ACTIVO:
        salida["mechanismResult"] = LOS_DOS
    elif captcha == ACTIVO:
        salida["mechanismResult"] = CAPTCHA_ACTIVO
    elif bloqueo == ACTIVO:
        salida["mechanismResult"] = BLOQUEO_ACTIVO
    if salida["mechanismResult"] != SIN_RESOLVER:
        return _con(salida, PASA, "")
    if captcha == INACTIVO and bloqueo == INACTIVO:
        if salida["equivalenceClaims"]:
            return _con(salida, SIN_PROTECCION, "ninguno de los dos mecanismos esta activo y hay "
                                                "una equivalencia declarada; decidirla no le toca "
                                                "al harness")
        salida["mechanismResult"] = NINGUNO
        return _con(salida, FALLA, "ni captcha ni bloqueo de usuario estan activos", [INACTIVA])
    bloqueos = {b for m in por_tipo.values() for b in m["blockedBy"]}
    estado = (PRUEBA_INSEGURA if PRUEBA_INSEGURA in bloqueos
              else SIN_OBJETIVO if SIN_OBJETIVO in bloqueos else SIN_PROTECCION)
    return _con(salida, estado, "no consta que captcha o bloqueo de usuario esten activos en "
                                "esta pagina; una capacidad o un control sustituto no alcanzan")


def _con(salida, estado, motivo, estados=None):
    salida["state"] = estado
    salida["states"] = sorted(estados or ([estado] if estado != PASA else []))
    salida["reason"] = motivo
    return salida


# -- la evaluacion ------------------------------------------------------------------------

def evaluar(caso, senal=None, autenticacion=None, desde=None):
    """El estado de Vu1 para un proyecto, pagina por pagina.

    `caso`:

        {"inventory": {...},            # el de C1; opcional: reemplaza el instalado
         "protection": {...},           # el de Vu1; opcional: reemplaza el instalado
         "evidence": [...],             # el catalogo, con la forma del de C1
         "detectedSurfaces": [...]}     # lo que otra fuente vio

    `senal` es `authenticationPagePresent` si quien llama la trae; si no, se deriva.
    `autenticacion` es `authenticationPresent`, y solo sirve para apagar con el inventario vacio.

    🔴 Para el mismo caso, esto devuelve siempre lo mismo, en cualquier orden que venga todo.
    """
    entrada = caso if isinstance(caso, dict) else {}
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "pages": [], "issues": [], "coverage": {}}
    d = derivar(entrada, autenticacion, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    salida["signalDerivation"] = {"value": d["value"], "pages": d["pages"]}
    salida["coverage"] = d["coverage"]
    if valor == _senales.SIN_RESOLVER:
        return _cerrar(salida, SIN_APLICABILIDAD, "no consta si hay una pagina de autenticacion, "
                                                  "y lo que no se sabe no es que no aplica")
    if valor == _senales.FALSA:
        return _cerrar(salida, NO_APLICA, "no hay pagina de autenticacion en el alcance")

    if d["problem"]:
        # El mensaje del cargador de C1 repite los valores que no validan. Se dice que no valida.
        problema = ("el inventario de superficies no valida contra su schema"
                    if d["problem"].startswith("el inventario de superficies no valida")
                    else d["problem"])
        salida["issues"].append(problema)
        return _cerrar(salida, SIN_COBERTURA, problema)
    lista, problema = entradas(entrada, desde)
    if problema:
        salida["issues"].append(problema)
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos, que no cuentan en ninguna de sus "
                                "versiones: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia que no tiene la forma declarada, y que por eso no "
                                "cuenta: %s" % ", ".join(d["malformed"]))
    if d["coverage"]["detectedMalformed"]:
        salida["issues"].append("`detectedSurfaces` no tiene la forma declarada; no se lee, y la "
                                "cobertura queda sin resolver")

    conocidas = {str(s.get("surfaceId")) for s in d["surfaces"]}
    sin_pagina = {str(p["surfaceId"]) for p in d["pages"] if p["page"] == NO_HAY_PAGINA}
    ajenas = sorted({str(e.get("surfaceId")) for e in lista
                     if str(e.get("surfaceId")) not in conocidas or
                     str(e.get("surfaceId")) in sin_pagina})
    salida["coverage"] = dict(d["coverage"], unknownProtectionEntries=ajenas)
    if ajenas:
        salida["issues"].append("el registro de proteccion nombra superficies que el inventario "
                                "de superficies no tiene como pagina: %s" % ", ".join(ajenas))

    por_id = {s.get("surfaceId"): s for s in d["surfaces"]}
    salida["pages"] = sorted(
        (evaluar_pagina(p, por_id.get(p["surfaceId"]) or {},
                        [e for e in lista if e.get("surfaceId") == p["surfaceId"]],
                        d["catalog"], bool(problema), entrada.get("evidence") or [])
         for p in d["pages"] if p["page"] == HAY_PAGINA),
        key=lambda r: (str(r.get("surfaceId")), json.dumps(r, sort_keys=True, default=str)))
    salida["issues"].sort()

    estados = [r["state"] for r in salida["pages"]]
    if FALLA in estados:
        return _cerrar(salida, FALLA, "hay al menos una pagina sin captcha ni bloqueo activos; "
                                      "las que cumplen no la tapan")
    c = salida["coverage"]
    if (not salida["pages"] or c["missing"] or c["duplicated"] or c["detectedMalformed"]
            or c["unresolved"] or ajenas):
        return _cerrar(salida, SIN_COBERTURA,
                       "no constan todas las paginas: sin resolver %s, faltan %s, repetidas %s, "
                       "ajenas %s" % (", ".join(c["unresolved"]) or "-",
                                      ", ".join(c["missing"]) or "-",
                                      ", ".join(c["duplicated"]) or "-",
                                      ", ".join(ajenas) or "-"))
    abiertos = sorted({e for e in estados if e != PASA})
    if not abiertos:
        return _cerrar(salida, PASA, "")
    return _cerrar(salida, abiertos[0] if len(abiertos) == 1 else SIN_PROTECCION,
                   "paginas sin resolver: %s" % ", ".join(
                       "%s (%s)" % (r["surfaceId"], r["state"])
                       for r in salida["pages"] if r["state"] != PASA))


def _cerrar(salida, estado, motivo):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    for r in salida["pages"]:
        todos.update(r.get("states") or [])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _depurar(salida)


def aprueba(resultado):
    """El unico estado que aprueba."""
    return (resultado or {}).get("state") == PASA
