"""Check normativo: el software de base esta configurado para no entregar datos privados.

    source: ES0902 / 6.2 / 6 / Vu7

    "Todo el software de base debe estar configurado para no entregar datos privados."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **ALWAYS.** No hay senal que lo apague y el check nunca dice que no aplica. Un registro vacio no
quiere decir que no hay software de base: quiere decir que no se sabe cual hay.

🔴 **Un registro por ambiente.** Lo que depende de la configuracion efectiva lo sostiene solo evidencia
del ambiente del registro, comparado en NFC. Sin ambiente nombrado, nada de eso se sostiene. Lo unico
que no depende del ambiente es la clasificacion de datos, el inventario y el alcance de superficies.

🔴 **Lo desplegado, no la intencion.** El default del repositorio, el codigo, el nombre de un endpoint,
el banner de version y la documentacion del producto no sostienen nada. Un override del ambiente que
establece la fuga le gana a un default que dice que no la hay.

🔴 **"Privado" lo dice el proyecto.** Una clase cuenta solo con evidencia autoritativa citada que la
clasifica con ese mismo valor. El modulo no tiene ninguna lista de productos, de tipos de componente,
de superficies ni de nombres de campo, y no busca nada en ningun texto.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Una prueba insegura o
sin objetivo no aprueba ni hace FAIL. El modulo no ejecuta nada: lee la evidencia de una prueba ya
hecha. La salida lleva ids, clases y estados, nunca el texto de una evidencia ni una muestra del dato.

El check no lee ni escribe el resultado de ninguna otra regla.
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

CONTROL = "base-software-data-disclosure-configuration"
POLICY = "base-software-private-data-disclosure-prohibited"
TIPO = "CHECK"
REGLA = "Vu7"
CLAVE = "ES0902.Vu7"

ARCHIVO = "base-software-data-disclosure.json"
SCHEMA = "base-software-data-disclosure.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = "Todo el software de base debe estar configurado para no entregar datos privados."

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
SIN_INVENTARIO = "BASE_SOFTWARE_INVENTORY_UNRESOLVED"
SIN_CLASIFICACION = "PRIVATE_DATA_CLASSIFICATION_UNRESOLVED"
SIN_COBERTURA = "DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED"
SIN_CONFIGURACION = "BASE_SOFTWARE_CONFIGURATION_UNRESOLVED"
FUGA = "UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE"
PRUEBA_INSEGURA = "BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Los nueve del procedimiento. No hay estado de "no aplica": la regla es ALWAYS.
ESTADOS = (PASA, FALLA, SIN_INVENTARIO, SIN_CLASIFICACION, SIN_COBERTURA, SIN_CONFIGURACION, FUGA,
           PRUEBA_INSEGURA, SIN_OBJETIVO)
FALLAS = (FALLA, FUGA)
# Sin ninguna falla, el sin resolver que se informa es el primero de este orden: el del procedimiento.
ORDEN_DE_LO_ABIERTO = (SIN_INVENTARIO, SIN_CLASIFICACION, SIN_COBERTURA, SIN_CONFIGURACION,
                       PRUEBA_INSEGURA, SIN_OBJETIVO)

# -- lo que dice el registro ------------------------------------------------------------

PRIVADA, NO_PRIVADA = "PRIVATE", "NOT_PRIVATE"
CLASES_RESUELTAS = (PRIVADA, NO_PRIVADA)
RESUELTA = "RESOLVED"
AUTORIZADO, NO_AUTORIZADO, PUBLICO = "AUTHORIZED", "UNAUTHORIZED", "PUBLIC"
SIN_FUGA = "NO_PRIVATE_DATA_DISCLOSURE"
ACCESO_AUTORIZADO = "AUTHORIZED_PRIVATE_DATA_ACCESS"

# -- lo que establece una evidencia ---------------------------------------------------------

INVENTARIO = "BASE_SOFTWARE_INVENTORY"          # values: los componentes del ambiente
ALCANCE = "DISCLOSURE_SURFACE_SCOPE"            # values: las superficies de un componente
CLASIFICACION = "DATA_CLASSIFICATION"           # value PRIVATE | NOT_PRIVATE; dataClasses
AUTORIZACION = "AUTHORIZATION_CONTEXT"          # value AUTHORIZED | UNAUTHORIZED | PUBLIC
ENTREGA = "DATA_DISCLOSURE"                     # value UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE | NO_...
# Lo que no depende del ambiente. Todo lo demas, si.
SIN_AMBIENTE = (CLASIFICACION, INVENTARIO, ALCANCE)

CONFIRMADA = "CONFIRMED"
OBSERVADA = "OBSERVED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, OBSERVADA)

# -- que clase sostiene que ------------------------------------------------------------------

PRUEBA = "AUTHORIZED_QA_RUNTIME_TEST"
# 🔴 Las de configuracion efectiva y de comportamiento: las unicas que sostienen una entrega o su
# ausencia. Las tablas son del harness, no del estandar.
EFECTIVAS = ("EFFECTIVE_CONFIGURATION", "DEPLOYED_MANIFEST", "ENVIRONMENT_OVERRIDE",
             "CONFIGURATION_TEST", PRUEBA, "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
# Las que no sostienen nada, nombradas para que la salida diga por que.
INSUFICIENTES = ("REPOSITORY_DEFAULT_CONFIGURATION", "SOURCE_CODE", "ENDPOINT_NAME", "VERSION_BANNER",
                 "PRODUCT_DOCUMENTATION", "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT")
# Las fuentes autoritativas del proyecto: seguridad, privacidad, arquitectura, evaluacion, contrato.
AUTORIDADES = ("SECURITY_DOCUMENTATION", "PRIVACY_DOCUMENTATION", "ARCHITECTURE_DOCUMENTATION",
               "ASSESSMENT_FINDING", "PROJECT_CONTRACT", "OTHER_AUTHORITATIVE_EVIDENCE")
# El inventario y el alcance salen tambien de lo desplegado.
DE_INVENTARIO = AUTORIDADES + ("DEPLOYMENT_DOCUMENTATION", "EFFECTIVE_CONFIGURATION",
                               "DEPLOYED_MANIFEST")
DE_AUTORIZACION = tuple(sorted(set(AUTORIDADES) | set(EFECTIVAS)))

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

# 🔴 No hay campo para un valor ni para una muestra: un item que lo trae queda mal formado.
FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "components": _ev.LISTA, "surfaces": _ev.LISTA,
         "dataClasses": _ev.LISTA, "value": _ev.TEXTO, "values": _ev.LISTA,
         "outcome": _ev.TEXTO, "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO,
         "syntheticFixtures": _ev.BOOLEANO, "destructive": _ev.BOOLEANO,
         "realPrivateDataAccessed": _ev.BOOLEANO, "rawSecretsLogged": _ev.BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def catalogo(caso):
    """El catalogo de `evidencia.py`, sin nada agregado."""
    return _ev.catalogo(caso, FORMA, OBLIGATORIOS)


def _ambiente(texto):
    """El ambiente en NFC, o `None` si no es un texto con algo."""
    return _ev.nfc(texto) if isinstance(texto, str) and texto.strip() else None


def prueba_segura(e, ambiente):
    """Los motivos por los que una prueba no era segura, o no era de este ambiente. Vacio es segura.

    No ejecuta nada. Ninguna condicion exige tocar un dato real: con fixtures sinteticos alcanza."""
    motivos = []
    if e.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    propio = e.get("environment")
    if propio in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    else:
        if _ev.igual(propio, PRODUCCION):
            motivos.append("PRODUCTION")
        elif _ev.nfc(propio) not in AMBIENTES_DE_PRUEBA:
            motivos.append("ENVIRONMENT_UNKNOWN")
        if ambiente is None or not _ev.igual(propio, ambiente):
            motivos.append("ENVIRONMENT_MISMATCH")
    if e.get("syntheticFixtures") is not True:
        motivos.append("NOT_SYNTHETIC_FIXTURES")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
    if e.get("realPrivateDataAccessed") is True:
        motivos.append("REAL_PRIVATE_DATA_ACCESSED")
    if e.get("rawSecretsLogged") is True:
        motivos.append("RAW_SECRETS_LOGGED")
    return sorted(motivos)


def _lectura(e, ambiente):
    """(cuenta, bloqueo, motivos). La misma compuerta para lo que dice que si y que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO, []
        motivos = prueba_segura(e, ambiente)
        if motivos:
            return False, PRUEBA_INSEGURA, motivos
    return e.get("outcome") in LEIBLES, None, []


def _del_ambiente(e, que, ambiente):
    """Si el item es del ambiente del registro. Sin ambiente propio, solo lo que no depende de el."""
    propio = e.get("environment")
    if propio is None:
        return que in SIN_AMBIENTE
    return ambiente is not None and _ev.igual(propio, ambiente)


def _sostiene(e, que, clases, ambiente):
    """Si el item legible, de una clase que sostiene `que` y del ambiente, establece `que`."""
    return (que in e["establishes"] and e["sourceType"] in clases and _lectura(e, ambiente)[0]
            and _del_ambiente(e, que, ambiente))


def _citada(e, citados):
    return _ev.id_de(e) in citados


def _nombra(e, cid, sid, citada):
    """Si el item habla de ESTA superficie de ESTE componente.

    La nombra por su id. Sin nombrar ninguna superficie, la nombra si nombra su componente, y si no
    nombra nada, solo si se la cita. Un item que nombra otro componente habla de otra cosa. La regla
    es la misma para lo que dice que hay fuga y para lo que dice que no: lo no citado nunca sostiene
    nada, pero lo que dice que hay fuga en el componente pesa aunque no se lo cite."""
    componentes, superficies = e.get("components"), e.get("surfaces")
    if componentes and not _ev.en(cid, componentes):
        return False
    if superficies:
        return _ev.en(sid, superficies)
    return citada or bool(componentes)


# -- los registros ------------------------------------------------------------------------------

VACIO = {"version": "1.0", "environment": None, "deploymentBinding": None, "dataClasses": [],
         "components": []}


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
        return dict(VACIO), "el registro del software de base no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return dict(VACIO), "el registro del software de base no se pudo validar"
    if errores:
        return dict(VACIO), ("el registro del software de base no valida contra su schema: %d errores"
                             % len(errores))
    return doc, ""


# -- la clasificacion, el inventario y el alcance --------------------------------------------------

def _nombra_la_clase(e, clase, citada):
    nombradas = e.get("dataClasses")
    return _ev.en(clase, nombradas) if nombradas else citada


def _clases(registro, cat, crudas, ambiente):
    """Cada clase del registro, resuelta solo con una `DATA_CLASSIFICATION` autoritativa citada con
    el mismo valor, y que nada legible contradice. Un nombre no clasifica nada."""
    declaradas = list(registro.get("dataClasses") or [])
    ids = [_ev.nfc(c.get("dataClassId")) for c in declaradas]
    salida = {}
    # Ordenadas: con una clase repetida, la que queda no depende del orden del registro.
    for c in _ev.ordenadas(declaradas):
        clase = _ev.nfc(c.get("dataClassId"))
        valor = c.get("classification")
        citados = _ev.claves(c.get("evidence"))
        autoritativas = [e for e in cat.values() if _sostiene(e, CLASIFICACION, AUTORIDADES, ambiente)
                         and e.get("value") in CLASES_RESUELTAS]
        apoyo = sorted(e["evidenceId"] for e in autoritativas if valor in CLASES_RESUELTAS
                       and e.get("value") == valor and _citada(e, citados)
                       and _nombra_la_clase(e, clase, True))
        contra = sorted(e["evidenceId"] for e in autoritativas if e.get("value") != valor
                        and _nombra_la_clase(e, clase, _citada(e, citados)))
        insuficientes = sorted(e["evidenceId"] for e in cat.values()
                               if CLASIFICACION in e["establishes"] and _citada(e, citados)
                               and e["sourceType"] not in AUTORIDADES)
        ilegibles = sorted(set(r for r in citados if r not in cat)
                           | set(_ev.ilegibles_sobre(clase, cat, crudas)))
        issues = []
        if ids.count(clase) > 1:
            issues.append("la clase `%s` esta repetida" % clase)
        if ilegibles:
            issues.append("hay evidencia ilegible sobre la clase: %s" % ", ".join(ilegibles))
        if contra:
            issues.append("una evidencia autoritativa clasifica la clase con otro valor")
        resuelta = (valor if valor in CLASES_RESUELTAS and apoyo and not contra and not ilegibles
                    and ids.count(clase) == 1 else None)
        salida[clase] = {"dataClassId": clase, "classification": valor, "resolved": resuelta,
                         "evidenceUsed": apoyo if resuelta else [], "contradictedBy": contra,
                         "insufficient": insuficientes, "issues": sorted(issues),
                         "state": PASA if resuelta else SIN_CLASIFICACION}
    return salida


def _citas_de_componente(componente):
    return _ev.claves(componente.get("evidence"))


def _alcance_de(componente, cat, ambiente):
    """(ids de la evidencia, superficies) del alcance autoritativo citado por el componente."""
    cid = componente.get("componentId")
    citados = _citas_de_componente(componente)
    usadas = [e for e in cat.values() if _sostiene(e, ALCANCE, DE_INVENTARIO, ambiente)
              and _citada(e, citados)
              and (not e.get("components") or _ev.en(cid, e.get("components")))]
    return (sorted(e["evidenceId"] for e in usadas),
            sorted({_ev.nfc(v) for e in usadas for v in e.get("values") or []}))


def derivar(caso, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    registro, problema = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    ambiente = _ambiente(registro.get("environment"))
    componentes = list(registro.get("components") or [])
    citados = set()
    for c in componentes:
        citados |= _citas_de_componente(c)
        for s in c.get("surfaces") or []:
            citados |= _ev.claves(s.get("evidence"))
    for c in registro.get("dataClasses") or []:
        citados |= _ev.claves(c.get("evidence"))

    # 🔴 Los ids se normalizan UNA vez, antes de contar (Vu2, tercer pase).
    del_inventario = [e for e in cat.values() if _sostiene(e, INVENTARIO, DE_INVENTARIO, ambiente)
                      and any(_citada(e, _citas_de_componente(c)) for c in componentes)]
    inventario = sorted({_ev.nfc(v) for e in del_inventario for v in e.get("values") or []})
    ids = [_ev.nfc(c.get("componentId")) for c in componentes]

    # Un componente repetido junta su alcance y sus superficies: el resultado no depende del orden.
    alcances, registradas = {}, {}
    for c in componentes:
        cid = _ev.nfc(c.get("componentId"))
        evid, superficies = _alcance_de(c, cat, ambiente)
        previo = alcances.get(cid) or {"evidence": [], "surfaces": []}
        alcances[cid] = {"evidence": sorted(set(previo["evidence"]) | set(evid)),
                         "surfaces": sorted(set(previo["surfaces"]) | set(superficies))}
        registradas.setdefault(cid, []).extend(_ev.nfc(s.get("surfaceId"))
                                               for s in c.get("surfaces") or [])
    sin_alcance, faltan, fuera, repetidas = [], [], [], []
    for cid, alcance in alcances.items():
        alcance["found"] = bool(alcance["evidence"])
        propias = registradas[cid]
        if not alcance["found"]:
            sin_alcance.append(cid)
        faltan.extend("%s/%s" % (cid, s) for s in alcance["surfaces"] if s not in propias)
        fuera.extend("%s/%s" % (cid, s) for s in set(propias) if s not in alcance["surfaces"])
        repetidas.extend("%s/%s" % (cid, s) for s in set(propias) if propias.count(s) > 1)

    clases = _clases(registro, cat, crudas, ambiente)
    referidas = sorted({_ev.nfc(r) for c in componentes for s in c.get("surfaces") or []
                        for r in s.get("dataClassRefs") or []})
    cobertura = {
        "inventory": [str(i) for i in inventario],
        "inventoryEvidence": sorted(e["evidenceId"] for e in del_inventario),
        "registered": sorted({str(i) for i in ids}),
        "duplicatedComponents": sorted({str(i) for i in ids if ids.count(i) > 1}),
        "missingComponents": [str(i) for i in inventario if i not in ids],
        "componentsOutsideInventory": sorted({str(i) for i in ids if i not in inventario}),
        "componentsWithoutSurfaceScope": sorted(str(i) for i in set(sin_alcance)),
        "missingSurfaces": sorted(set(faltan)),
        "surfacesOutsideScope": sorted(set(fuera)),
        "duplicatedSurfaces": sorted(set(repetidas)),
        "undeclaredDataClasses": [str(r) for r in referidas if r not in clases],
        "registryUnreadable": bool(problema)}
    return {"registry": registro, "problem": problema, "environment": ambiente,
            "components": componentes, "catalog": cat, "raw": crudas, "repeated": repetidos,
            "malformed": torcidas, "cited": citados, "coverage": cobertura, "scopes": alcances,
            "classes": clases, "inventory": inventario}


# -- el bloqueo, uno solo ----------------------------------------------------------------------

def _dice_fuga(e):
    """Si el item dice que hay fuga: pesa aunque no se lo cite."""
    return ENTREGA in e["establishes"] and e.get("value") == FUGA


def _bloqueos(cat, citados, ambiente, cid=None, sid=None, registradas=(), componentes=(),
              superficies=()):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan: las que se citan, o las que
    dicen que hay fuga. Con `sid`, las que nombran esa superficie; sin el, las que nombran un
    componente o una superficie del registro, del inventario o del alcance, y ninguna superficie
    registrada.

    🔴 Una prueba que nombra solamente algo que no esta en el registro, el inventario ni el alcance
    no mueve nada, y una ajena e insegura que dice que no hay fuga tampoco."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        citada = _citada(e, citados)
        if sid is not None and not _nombra(e, cid, sid, citada):
            continue
        if sid is None and (any(_nombra(e, c, s, False) for c, s in registradas)
                            or not (any(_ev.en(c, e.get("components")) for c in componentes)
                                    or any(_ev.en(s, e.get("surfaces")) for s in superficies))):
            continue
        _, bloqueo, m = _lectura(e, ambiente)
        if bloqueo and (citada or _dice_fuga(e)):
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return SIN_CONFIGURACION


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan la superficie y el PASS del agregado.

    Lo que no se pudo leer y pesa impide el PASS; un FAIL no se toca: bloquear impide aprobar, no
    tapa lo que falla. Tampoco reemplaza un sin resolver que ya estaba: ese es el estado que sale, y
    el del bloqueo queda en `states`."""
    if estado != PASA:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), ("una prueba que se cita, o que dice que hay fuga, no se pudo leer")
    if ilegibles:
        return SIN_CONFIGURACION, ("hay evidencia ilegible sobre el componente o la superficie, y esa "
                                   "podia ser la que decia que hay fuga")
    return estado, motivo


# -- una superficie, en el orden de la spec -----------------------------------------------------

def _ids(x, que, valores, clases, solo_citadas=True):
    """Los ids de lo que sostiene `que` con uno de `valores` sobre la superficie.

    Sin citar, cuenta solo lo que nombra la superficie o su componente."""
    return sorted(e["evidenceId"] for e in x["cat"].values()
                  if _sostiene(e, que, clases, x["ambiente"]) and e.get("value") in valores
                  and (_citada(e, x["citados"]) or not solo_citadas)
                  and _nombra(e, x["cid"], x["sid"], _citada(e, x["citados"])))


def _paso_configuracion(x):
    if x["ambiente"] is None:
        return SIN_CONFIGURACION, ("el registro no nombra su ambiente: nada que dependa de la "
                                   "configuracion efectiva se puede sostener")
    if x["componente"].get("configurationStatus") != RESUELTA:
        return SIN_CONFIGURACION, "la configuracion efectiva del componente no esta resuelta"
    return None, ""


def _autorizado_establecido(x):
    """Las evidencias que sostienen un contexto AUTHORIZED declarado, o [] si no lo esta."""
    if x["superficie"].get("authorizationContext") != AUTORIZADO:
        return []
    return _ids(x, AUTORIZACION, (AUTORIZADO,), DE_AUTORIZACION)


def _paso_fuga(x):
    salida = x["salida"]
    refs = sorted({_ev.nfc(r) for r in x["superficie"].get("dataClassRefs") or []})
    resueltas = {r: (x["clases"].get(r) or {}).get("resolved") for r in refs}
    privadas = [r for r in refs if resueltas[r] == PRIVADA]
    sin_resolver = [r for r in refs if resueltas[r] is None]
    fugas = _ids(x, ENTREGA, (FUGA,), EFECTIVAS)
    if fugas and privadas:
        autorizado = _autorizado_establecido(x)
        if autorizado:
            # Dos cosas establecidas que no pueden ser ciertas a la vez: ni FAIL ni PASS.
            salida["contradictedBy"].extend(fugas + autorizado)
            return SIN_CONFIGURACION, ("una evidencia citada establece la fuga y otra establece que el "
                                       "consumidor esta autorizado")
        # 🔴 La falla establecida gana siempre: diga lo que diga el registro y diga lo que diga otra
        # evidencia. Declarar la fuga con honestidad nunca da algo mas blando que declarar que no hay.
        salida["evidenceUsed"]["disclosure"] = fugas
        salida["contradictedBy"].extend(_ids(x, ENTREGA, (SIN_FUGA,), EFECTIVAS, False))
        return FUGA, ("una evidencia citada de configuracion efectiva o de comportamiento, del ambiente "
                      "del registro, establece que se entrega una clase privada a un consumidor no "
                      "autorizado")
    if sin_resolver:
        salida["issues"].append("clases sin resolver: %s" % ", ".join(str(r) for r in sin_resolver))
        return SIN_CLASIFICACION, "la superficie nombra una clase de datos sin clasificacion autoritativa"
    if fugas:
        # Una entrega de datos no privados no es una fuga de Vu7.
        salida["notPrivateDisclosure"] = fugas
    no_citadas = [i for i in _ids(x, ENTREGA, (FUGA,), EFECTIVAS, False) if i not in fugas]
    if no_citadas and privadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_CONFIGURACION, ("una evidencia dice que hay fuga y no se la cita: lo no citado nunca "
                                   "hace FAIL, y tampoco se elige")
    return None, ""


def _paso_acceso_autorizado(x):
    if x["superficie"].get("result") != ACCESO_AUTORIZADO:
        return None, ""
    salida = x["salida"]
    contra = sorted(set(_ids(x, AUTORIZACION, (NO_AUTORIZADO, PUBLICO), DE_AUTORIZACION, False)))
    if contra:
        salida["contradictedBy"].extend(contra)
        return SIN_CONFIGURACION, "una evidencia dice que el consumidor no esta autorizado"
    apoyo = _autorizado_establecido(x)
    if not apoyo:
        return _abierto(salida["blockedBy"]), (
            "el acceso autorizado exige `authorizationContext: AUTHORIZED` y una evidencia citada "
            "`AUTHORIZATION_CONTEXT` que lo establece para esta superficie")
    salida["evidenceUsed"]["authorization"] = apoyo
    return None, ""


def _paso_sin_fuga(x):
    declarado = x["superficie"].get("result")
    if declarado == ACCESO_AUTORIZADO:
        return None, ""
    salida = x["salida"]
    if declarado != SIN_FUGA:
        # Declarar la fuga sin la evidencia que la establece no es FAIL: lo que dice que no pasa por
        # la misma compuerta que lo que dice que si.
        return _abierto(salida["blockedBy"]), ("el resultado de la superficie no consta con evidencia "
                                               "citada de configuracion efectiva o de comportamiento")
    apoyo = _ids(x, ENTREGA, (SIN_FUGA,), EFECTIVAS)
    if not apoyo:
        return _abierto(salida["blockedBy"]), (
            "que no haya fuga no consta con evidencia citada de configuracion efectiva o de "
            "comportamiento del ambiente del registro; el default del repositorio, el codigo o el "
            "nombre no alcanzan")
    salida["evidenceUsed"]["noDisclosure"] = apoyo
    return None, ""


PASOS = (_paso_configuracion, _paso_fuga, _paso_acceso_autorizado, _paso_sin_fuga)
LO_QUE_SE_SOSTIENE = {ENTREGA: EFECTIVAS, AUTORIZACION: DE_AUTORIZACION}


def evaluar_superficie(componente, superficie, d):
    """Una superficie de un componente, sola: su estado y la evidencia que lo sostiene, por id."""
    cat, crudas, ambiente = d["catalog"], d["raw"], d["environment"]
    cid, sid = _ev.nfc(componente.get("componentId")), _ev.nfc(superficie.get("surfaceId"))
    citados = _citas_de_componente(componente) | _ev.claves(superficie.get("evidence"))
    salida = {"surfaceId": sid, "authorizationContext": superficie.get("authorizationContext"),
              "dataClassRefs": sorted({_ev.nfc(r) for r in superficie.get("dataClassRefs") or []}),
              "result": superficie.get("result"),
              "verificationMode": superficie.get("verificationMode"),
              "inScope": sid in d["scopes"][cid]["surfaces"],
              "evidenceUsed": {"disclosure": [], "authorization": [], "noDisclosure": []},
              "contradictedBy": [], "issues": [], "notPrivateDisclosure": [],
              # Lo citado que dice algo de la superficie y no es de una clase que lo sostenga.
              "insufficient": sorted(e["evidenceId"] for e in cat.values() if _citada(e, citados)
                                     and any(q in e["establishes"] and e["sourceType"] not in c
                                             for q, c in LO_QUE_SE_SOSTIENE.items())),
              # Lo citado de una clase que sostiene, y de otro ambiente.
              "otherEnvironment": sorted(e["evidenceId"] for e in cat.values() if _citada(e, citados)
                                         and any(q in e["establishes"] and e["sourceType"] in c
                                                 and not _del_ambiente(e, q, ambiente)
                                                 for q, c in LO_QUE_SE_SOSTIENE.items()))}
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, citados, ambiente, cid, sid)
    x = {"cat": cat, "citados": citados, "ambiente": ambiente, "cid": cid, "sid": sid,
         "componente": componente, "superficie": superficie, "clases": d["classes"],
         "salida": salida}
    pasos = [paso(x) for paso in PASOS]
    # 🔴 En el orden de la spec, y lo que falla no lo tapa un paso anterior sin resolver.
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = [p for p in pasos if p[0] is not None]
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]
    ilegibles = sorted(set(r for r in citados if r not in cat)
                       | set(_ev.ilegibles_sobre(sid, cat, crudas))
                       | set(_ev.ilegibles_sobre(cid, cat, crudas)))
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre la superficie o su componente: %s"
                                % ", ".join(str(i) for i in ilegibles))
    if not salida["inScope"]:
        salida["issues"].append("la superficie no esta en el alcance citado del componente")
    final, motivo = _bloquear(estado, motivo, salida["blockedBy"], ilegibles)
    if final != estado:
        # Lo bloqueado no se sostiene con nada: no queda evidencia usada.
        salida["evidenceUsed"] = {k: [] for k in salida["evidenceUsed"]}
    salida["contradictedBy"] = sorted(set(salida["contradictedBy"]))
    salida["issues"] = sorted(set(salida["issues"]))
    salida["state"] = final
    queda = set(salida["blockedBy"]) if final not in FALLAS else set()
    salida["states"] = sorted(({p[0] for p in pasos if p[0] is not None} | {final} | queda) - {PASA})
    salida["reason"] = motivo
    return salida


def _de_lo_evaluado(estados):
    """(estado, motivo) de un conjunto de estados."""
    if any(e in FALLAS for e in estados):
        return FUGA, "al menos una superficie entrega datos privados; las que cumplen no lo tapan"
    abiertos = {e for e in estados if e != PASA}
    for e in ORDEN_DE_LO_ABIERTO:
        if e in abiertos:
            return e, "hay algo material sin resolver"
    return PASA, ""


def evaluar_componente(componente, d):
    """Un componente con sus superficies. Una superficie en verde no tapa otra."""
    cid = _ev.nfc(componente.get("componentId"))
    alcance = d["scopes"][cid]
    superficies = _ev.ordenadas(evaluar_superficie(componente, s, d)
                                for s in componente.get("surfaces") or [])
    c = d["coverage"]
    abiertos = []
    if cid not in d["inventory"] or cid in c["duplicatedComponents"]:
        abiertos.append(SIN_INVENTARIO)
    if (not alcance["found"] or any(x.startswith(cid + "/") for x in
                                    c["missingSurfaces"] + c["surfacesOutsideScope"]
                                    + c["duplicatedSurfaces"])):
        abiertos.append(SIN_COBERTURA)
    if d["environment"] is None or componente.get("configurationStatus") != RESUELTA:
        abiertos.append(SIN_CONFIGURACION)
    estado, motivo = _de_lo_evaluado([s["state"] for s in superficies] + abiertos)
    return {"componentId": cid, "inInventory": cid in d["inventory"],
            "configurationStatus": componente.get("configurationStatus"),
            "surfaceScope": list(alcance["surfaces"]), "scopeEvidence": list(alcance["evidence"]),
            "surfaces": superficies, "state": estado, "reason": motivo}


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, desde=None):
    """El estado de Vu7, componente por componente y superficie por superficie.

    `caso`:

        {"registry": {...},         # el registro de Vu7, de un ambiente; opcional
         "evidence": [...]}         # el catalogo, cerrado
    """
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    registro = d["registry"]
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE,
              "environment": d["environment"],
              "deploymentBinding": _ambiente(registro.get("deploymentBinding")),
              "components": [], "dataClasses": [], "issues": [], "coverage": d["coverage"]}
    if d["problem"]:
        salida["issues"].append(d["problem"])
    if d["environment"] is None:
        salida["issues"].append("el registro no nombra su ambiente")
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    salida["issues"].sort()
    salida["dataClasses"] = _ev.ordenadas(d["classes"].values())
    # 🔴 Cada componente y cada superficie se evaluan solos, tambien lo que esta afuera.
    salida["components"] = _ev.ordenadas(evaluar_componente(c, d) for c in d["components"])

    registradas = [(_ev.nfc(c.get("componentId")), _ev.nfc(s.get("surfaceId")))
                   for c in d["components"] for s in c.get("surfaces") or []]
    c = d["coverage"]
    componentes = sorted(set(c["registered"]) | set(c["inventory"]))
    superficies = sorted({s for _, s in registradas}
                         | {s for a in d["scopes"].values() for s in a["surfaces"]})
    sueltos, motivos = _bloqueos(d["catalog"], d["cited"], d["environment"], registradas=registradas,
                                 componentes=componentes, superficies=superficies)
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos
    ilegibles = sorted({i for cid in c["registered"] for i in _ev.ilegibles_sobre(cid, d["catalog"],
                                                                                   d["raw"])}
                       | {r for comp in d["components"] for r in _citas_de_componente(comp)
                          if r not in d["catalog"]})
    estado, motivo = _agregado(salida, d)
    final, motivo = _bloquear(estado, motivo, sueltos, ilegibles)
    return _cerrar(salida, final, motivo, estado)


def _agregado(salida, d):
    c = d["coverage"]
    estados = [s["state"] for comp in salida["components"] for s in comp["surfaces"]]
    if any(e in FALLAS for e in estados):
        return _de_lo_evaluado(estados)
    abiertos = []
    if (d["problem"] or not c["inventoryEvidence"] or c["missingComponents"]
            or c["componentsOutsideInventory"] or c["duplicatedComponents"]):
        abiertos.append(SIN_INVENTARIO)
    if c["undeclaredDataClasses"] or any(x["state"] != PASA for x in salida["dataClasses"]):
        abiertos.append(SIN_CLASIFICACION)
    if (c["componentsWithoutSurfaceScope"] or c["missingSurfaces"] or c["surfacesOutsideScope"]
            or c["duplicatedSurfaces"]):
        abiertos.append(SIN_COBERTURA)
    if d["environment"] is None or any(comp.get("configurationStatus") != RESUELTA
                                       for comp in d["components"]):
        abiertos.append(SIN_CONFIGURACION)
    estado, motivo = _de_lo_evaluado(estados + abiertos)
    if estado != PASA and estado in abiertos and estado not in estados:
        motivo = ("no esta entero: inventario %s, fuera del inventario %s, superficies sin entrada %s, "
                  "fuera del alcance %s" % (c["missingComponents"] or "-",
                                            c["componentsOutsideInventory"] or "-",
                                            c["missingSurfaces"] or "-",
                                            c["surfacesOutsideScope"] or "-"))
    return estado, motivo


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None, PASA):
        todos.add(previo)
    for comp in salida["components"]:
        if comp["state"] != PASA:
            todos.add(comp["state"])
        for s in comp["surfaces"]:
            todos.update(s.get("states") or [])
    for x in salida["dataClasses"]:
        if x["state"] != PASA:
            todos.add(x["state"])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


def evidencia_usada(resultado):
    """Los ids que sostienen el resultado: inventario, alcance, clases y superficies."""
    r = resultado if isinstance(resultado, dict) else {}
    ids = set((r.get("coverage") or {}).get("inventoryEvidence") or [])
    for x in r.get("dataClasses") or []:
        ids.update(x.get("evidenceUsed") or [])
    for comp in r.get("components") or []:
        ids.update(comp.get("scopeEvidence") or [])
        for s in comp.get("surfaces") or []:
            for u in (s.get("evidenceUsed") or {}).values():
                ids.update(u)
    return sorted(i for i in ids if isinstance(i, str))


# -- hacia seguridad.resultado ----------------------------------------------------------------------

def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu7", ...)`, desde la salida de `evaluar`.

    Vu7 no tiene algoritmo propio en `seguridad.py`: va por el generico. Los dos controles de la
    fila llevan el estado del check -PASS, FAIL o el estado abierto tal cual- con la evidencia por
    id. No hay senales: la regla es ALWAYS. Un resultado que no dice ser de este check no se
    traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("control") != CONTROL or r.get("state") not in ESTADOS:
        return {}, {}
    estado = r["state"]
    control = FALLA if estado in FALLAS else estado
    evidencia = evidencia_usada(r) or (["check:%s" % CONTROL] if estado in (PASA,) + FALLAS else [])
    doc = {"controlResults": {c: {"result": control, "evidence": evidencia}
                              for c in (POLICY, CONTROL)}}
    return _ev.depurar(doc), {}
