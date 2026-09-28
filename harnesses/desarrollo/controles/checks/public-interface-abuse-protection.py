"""Check normativo: lo publico sin autenticacion tiene control de uso.

    source: ES0902 / 6.2 / 6 / Vu9

    "Las aplicaciones que expongan funcionalidades accesibles sin autenticacion a traves de interfaces
    publicas (web o API), deberan contemplar mecanismos de control de uso que mitiguen riesgos por
    consumo excesivo o automatizado de recursos y garanticen la estabilidad del servicio."

🔴 **Esto no es un check del hook.** Es un control normativo.

🔴 **Superficie por superficie.** Cada funcionalidad publica sin autenticacion se evalua sola: una
protegida no tapa otra sin control. El inventario tiene que estar entero.

🔴 **Nada se inventa.** Ni un mecanismo, ni un producto, ni un numero de pedidos, una cuota, una
concurrencia o un SLA. El modulo no tiene ninguna lista de mecanismos: mira si el control existe del
lado del servidor, si el camino publico lo atraviesa y si sus tres dimensiones -consumo excesivo,
consumo automatizado y estabilidad- constan con evidencia citada.

🔴 **La configuracion no es el camino.** Un control configurado cubre la superficie solo si una
evidencia del camino dice que la ruta publica lo atraviesa. Un origen alcanzable por detras es
`ABUSE_CONTROL_BYPASS_PRESENT`. Lo que corre en el navegador nunca es un control.

🔴 **Lo que dice que no pasa por la misma compuerta que lo que dice que si.** Una prueba insegura o sin
objetivo no aprueba ni hace FAIL. El modulo no ejecuta nada ni genera un solo pedido. La salida lleva
ids, capas, huellas y estados, nunca un payload ni una credencial.
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

CONTROL = "public-interface-abuse-protection"
POLICY = "public-interface-abuse-control-required"
TIPO = "CHECK"
REGLA = "Vu9"
CLAVE = "ES0902.Vu9"
SENAL = "unauthenticatedPublicInterfacePresent"

ARCHIVO = "public-interface-abuse-protection.json"
SCHEMA = "public-interface-abuse-protection.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = ("Las aplicaciones que expongan funcionalidades accesibles sin autenticación a través "
                "de interfaces públicas (web o API), deberán contemplar mecanismos de control de uso "
                "que mitiguen riesgos por consumo excesivo o automatizado de recursos y garanticen la "
                "estabilidad del servicio.")

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_SUPERFICIE = "PUBLIC_UNAUTHENTICATED_SURFACE_COVERAGE_UNRESOLVED"
SIN_COBERTURA = "PUBLIC_USE_CONTROL_COVERAGE_UNRESOLVED"
FALTA = "ABUSE_CONTROL_MISSING"
SALTEO = "ABUSE_CONTROL_BYPASS_PRESENT"
SIN_EXCESIVO = "EXCESSIVE_CONSUMPTION_MITIGATION_UNRESOLVED"
SIN_AUTOMATIZADO = "AUTOMATED_CONSUMPTION_MITIGATION_UNRESOLVED"
SIN_ESTABILIDAD = "SERVICE_STABILITY_EVIDENCE_UNRESOLVED"
PRUEBA_INSEGURA = "PUBLIC_ABUSE_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_SUPERFICIE, SIN_COBERTURA, FALTA, SALTEO,
           SIN_EXCESIVO, SIN_AUTOMATIZADO, SIN_ESTABILIDAD, PRUEBA_INSEGURA, SIN_OBJETIVO)
# Las formas de fallar, en el orden en que el agregado informa la primera.
ORDEN_DE_LAS_FALLAS = (SALTEO, FALTA)
FALLAS = (FALLA,) + ORDEN_DE_LAS_FALLAS
RESUELTAS = (PASA, NO_APLICA)
# Sin ninguna falla, el sin resolver que se informa es el primero de este orden: el de los pasos.
ORDEN_DE_LO_ABIERTO = (SIN_SUPERFICIE, SIN_COBERTURA, SIN_EXCESIVO, SIN_AUTOMATIZADO, SIN_ESTABILIDAD,
                       PRUEBA_INSEGURA, SIN_OBJETIVO)

# -- lo que dice el registro ------------------------------------------------------------

SI, NO, SIN_RESOLVER = "YES", "NO", "UNRESOLVED"
ATADO = "BOUND"
SALTEADO = "BYPASS_PRESENT"
NO_ATADO = "NOT_BOUND"
EVIDENCIADA = "EVIDENCED"
NO_EVIDENCIADA = "NOT_EVIDENCED"
PROTEGIDA = "PROTECTED"
SIN_VERIFICAR = "NOT_VERIFIED"
CAPAS = ("APPLICATION", "API_GATEWAY", "REVERSE_PROXY", "WAF", "OPENSHIFT_ROUTER", "OTHER")

# -- lo que establece una evidencia ---------------------------------------------------------

FUNCIONALIDAD = "PUBLIC_UNAUTHENTICATED_FUNCTIONALITY"    # value PRESENT | ABSENT
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
INVENTARIO = "PUBLIC_SURFACE_INVENTORY"                   # value COMPLETE | INCOMPLETE; surfaces
ENTERO, INCOMPLETO = "COMPLETE", "INCOMPLETE"
ALCANZABLE = "PUBLIC_REACHABILITY"                        # value YES | NO
AUTENTICACION = "AUTHENTICATION_REQUIRED"                 # value YES | NO
USO = "USE_CONTROL"                                       # value PRESENT | ABSENT
CAMINO = "PATH_BINDING"                                   # value BOUND | BYPASS_PRESENT | NOT_BOUND
EXCESIVO = "EXCESSIVE_CONSUMPTION_MITIGATION"             # value EVIDENCED | NOT_EVIDENCED
AUTOMATIZADO = "AUTOMATED_CONSUMPTION_MITIGATION"
ESTABILIDAD = "SERVICE_STABILITY"

CONFIRMADA = "CONFIRMED"
OBSERVADA = "OBSERVED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, OBSERVADA)

# -- que clase sostiene que ------------------------------------------------------------------
# 🔴 Las tablas son del harness, no del estandar. Ninguna nombra un mecanismo.

PRUEBA = "AUTHORIZED_QA_BOUNDED_TEST"
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "NAMING_CONVENTION")
# Lo que no habla de funcionalidad: un DNS, un asset estatico, un endpoint de salud.
NO_FUNCIONALES = ("PUBLIC_DNS_RECORD", "STATIC_ASSET_EXPOSURE", "HEALTH_ENDPOINT")
AUTORIDADES = ("SECURITY_DOCUMENTATION", "ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT",
               "PROJECT_CONTRACT", "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
DE_INVENTARIO = AUTORIDADES + ("ROUTE_INVENTORY", "API_SPECIFICATION", "NETWORK_TOPOLOGY")
DEL_SERVIDOR = AUTORIDADES + ("APPLICATION_CODE", "APPLICATION_CONFIGURATION", "GATEWAY_CONFIGURATION",
                              "REVERSE_PROXY_CONFIGURATION", "WAF_CONFIGURATION",
                              "INGRESS_CONFIGURATION", "UNIT_TEST", "INTEGRATION_TEST", PRUEBA)
DEL_CAMINO = tuple(c for c in DEL_SERVIDOR if c != "UNIT_TEST") + ("NETWORK_TOPOLOGY",)
DE_ESTABILIDAD = DEL_SERVIDOR + ("PERFORMANCE_TEST_REPORT", "CAPACITY_CONFIGURATION",
                                 "OBSERVABILITY_RECORD")
DEL_CLIENTE = ("CLIENT_SIDE_CONTROL", "FRONTEND_CODE", "UI_TEST")
# Las que no sostienen nada de Vu9, nombradas para que la salida diga por que.
INSUFICIENTES = DEL_CLIENTE + DEBILES + NO_FUNCIONALES

DIMENSIONES = ((EXCESIVO, "excessiveConsumptionMitigation", DEL_SERVIDOR, SIN_EXCESIVO),
               (AUTOMATIZADO, "automatedConsumptionMitigation", DEL_SERVIDOR, SIN_AUTOMATIZADO),
               (ESTABILIDAD, "stabilityEvidence", DE_ESTABILIDAD, SIN_ESTABILIDAD))
HUELLAS = ("routeVersion", "configFingerprint", "buildId", "imageDigest")

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

# -- el catalogo, cerrado ----------------------------------------------------------------------

# 🔴 No hay campo para un payload, un script, una credencial ni un dato personal: un item que lo trae
# queda mal formado. `severity` y `readOnly` se aceptan y no se leen nunca.
FORMA = {"evidenceId": _ev.TEXTO, "sourceType": _ev.TEXTO, "reference": _ev.TEXTO,
         "establishes": _ev.LISTA, "surfaces": _ev.LISTA, "controls": _ev.LISTA, "value": _ev.TEXTO,
         "outcome": _ev.TEXTO, "environment": _ev.TEXTO, "authorized": _ev.BOOLEANO,
         "bounded": _ev.BOOLEANO, "stopConditions": _ev.BOOLEANO, "syntheticData": _ev.BOOLEANO,
         "destructive": _ev.BOOLEANO, "routeVersion": _ev.TEXTO, "configFingerprint": _ev.TEXTO,
         "buildId": _ev.TEXTO, "imageDigest": _ev.TEXTO, "readOnly": _ev.BOOLEANO,
         "severity": _ev.TEXTO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def catalogo(caso):
    """El catalogo de `evidencia.py`, sin nada agregado."""
    return _ev.catalogo(caso, FORMA, OBLIGATORIOS)


def prueba_segura(e):
    """Los motivos por los que una prueba no era segura. Vacio es segura.

    No ejecuta nada: lee lo que la prueba declara de si misma."""
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
    if e.get("bounded") is not True:
        motivos.append("NOT_BOUNDED")
    if e.get("stopConditions") is not True:
        motivos.append("NO_STOP_CONDITIONS")
    if e.get("syntheticData") is not True:
        motivos.append("NOT_SYNTHETIC_DATA")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
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


def _del_ambiente(e, ambiente):
    """Si el item vale para el ambiente del registro. Sin ambiente, vale para cualquiera."""
    propio = e.get("environment")
    return ambiente is None or propio is None or _ev.igual(propio, ambiente)


def _sostiene(e, que, clases, ambiente=None):
    """Si el item legible, de una clase que puede decir `que` y del ambiente, lo establece."""
    return (que in e["establishes"] and e["sourceType"] in clases and _lectura(e)[0]
            and _del_ambiente(e, ambiente))


def _citada(e, citados):
    return _ev.id_de(e) in citados


def _nombra(e, sid, cid):
    """Si el item habla de ESTE control de ESTA superficie, por sus ids.

    🔴 Citarlo no alcanza: tiene que nombrarlos (refutador, pase 1). Nombra el control si lo lista en
    `controls`; sin `controls`, habla de la superficie entera si la lista en `surfaces`. Un item que
    nombra otra superficie habla de otra cosa."""
    superficies, controles = e.get("surfaces"), e.get("controls")
    if superficies and not _ev.en(sid, superficies):
        return False
    if cid is not None and controles:
        return _ev.en(cid, controles)
    return bool(superficies)


def _toca(e, sid, cids):
    """Si el item nombra la superficie o uno de sus controles. Es la pregunta de si lo que no se pudo
    leer pesa: pesa si se lo cita o si toca la superficie, diga lo que diga."""
    # 🔴 Nombrar otra superficie no lo saca: si nombra un control suyo, lo toca (refutador, pase 2).
    return _ev.en(sid, e.get("surfaces")) or any(_ev.en(c, e.get("controls")) for c in cids if c)


def _nfcs(lista):
    return sorted({_ev.nfc(x) for x in (lista or []) if isinstance(x, str)})


def _texto(x):
    return _ev.nfc(x) if isinstance(x, str) else None


# -- el registro ------------------------------------------------------------------------------

VACIO = {"version": "1.0", "environment": None, "surfaces": []}


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
        return dict(VACIO), "el registro del control de uso publico no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return dict(VACIO), "el registro del control de uso publico no se pudo validar"
    if errores:
        return dict(VACIO), ("el registro del control de uso publico no valida contra su schema: %d "
                             "errores" % len(errores))
    return doc, ""


# -- la senal y el inventario ------------------------------------------------------------------

def derivar(caso, desde=None):
    entrada = caso if isinstance(caso, dict) else {}
    registro, problema = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    superficies = list(registro.get("surfaces") or [])
    ambiente = _texto(registro.get("environment"))
    citados = set()
    for s in superficies:
        citados |= _ev.claves(s.get("evidence"))
        for c in s.get("controls") or []:
            citados |= _ev.claves(c.get("evidence"))

    sobre = [e for e in cat.values() if FUNCIONALIDAD in e["establishes"]]
    # 🔴 `readOnly` no se lee: una funcionalidad de solo lectura tambien se abusa.
    presentes = [e for e in sobre if e.get("value") == PRESENTE
                 and e["sourceType"] not in DEBILES + NO_FUNCIONALES and _lectura(e)[0]]
    # Cualquier PRESENT, legible o no y de la clase que sea, impide apagar la regla.
    dicen_que_si = [e for e in sobre if e.get("value") == PRESENTE]
    ausentes = [e for e in sobre if e.get("value") == AUSENTE and _sostiene(e, FUNCIONALIDAD, AUTORIDADES)]
    ilegibles = _ev.ilegibles_sobre(FUNCIONALIDAD, cat, crudas)
    if problema:
        valor = _senales.SIN_RESOLVER
    elif presentes:
        valor = _senales.VERDADERA
    elif ausentes and not dicen_que_si and not superficies and not ilegibles:
        valor = _senales.FALSA
    else:
        # Tambien el vacio: el vacio no es FALSE.
        valor = _senales.SIN_RESOLVER

    enteros = [e for e in cat.values() if _sostiene(e, INVENTARIO, DE_INVENTARIO, ambiente)
               and e.get("value") == ENTERO]
    incompletos = sorted(e["evidenceId"] for e in cat.values() if INVENTARIO in e["establishes"]
                         and e.get("value") == INCOMPLETO and _lectura(e)[0]
                         and e["sourceType"] not in DEBILES and _del_ambiente(e, ambiente))
    formas = {tuple(_nfcs(e.get("surfaces"))) for e in enteros}
    inventario = list(formas)[0] if len(formas) == 1 else ()
    ids = [_ev.nfc(s.get("surfaceId")) for s in superficies]
    nombradas = _nfcs([x for e in presentes for x in e.get("surfaces") or []] + list(inventario))
    cobertura = {"registered": sorted({str(i) for i in ids}),
                 "namedBySignal": [str(s) for s in _nfcs(x for e in presentes
                                                         for x in e.get("surfaces") or [])],
                 "inventory": {"complete": bool(enteros) and len(formas) == 1 and not incompletos,
                               "evidence": sorted(e["evidenceId"] for e in enteros),
                               "incomplete": incompletos,
                               "conflicting": len(formas) > 1,
                               "surfaces": [str(s) for s in inventario]},
                 "missingSurfaces": [str(s) for s in nombradas if s not in ids],
                 "duplicatedSurfaces": sorted({str(i) for i in ids if ids.count(i) > 1}),
                 "registryUnreadable": bool(problema)}
    return {"value": valor, "registry": registro, "problem": problema, "surfaces": superficies,
            "environment": ambiente, "catalog": cat, "raw": crudas, "repeated": repetidos,
            "malformed": torcidas, "cited": citados, "present": presentes, "absent": ausentes,
            "coverage": cobertura}


def senal(caso, desde=None):
    d = derivar(caso, desde)
    usadas = d["present"] if d["value"] == _senales.VERDADERA else (
        d["absent"] if d["value"] == _senales.FALSA else [])
    evidencia = [{"evidenceId": "publico:%s" % e["evidenceId"], "sourceType": "REPOSITORY_CONFIGURATION",
                  "reference": "%s#%s" % (ARCHIVO, e["evidenceId"]),
                  "claim": ("una evidencia establece una funcionalidad publica sin autenticacion"
                            if d["value"] == _senales.VERDADERA else
                            "una evidencia autoritativa establece que no hay funcionalidad publica sin "
                            "autenticacion"),
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

def _dice_falla(e):
    """🔴 La unica pregunta de si un item dice una falla de la superficie. La usan el bloqueo, lo
    ilegible, lo no citado y lo de otro ambiente.

    Dice una falla un item del servidor, la infraestructura o el camino -de cualquier legibilidad- que
    dice que no hay control, que el camino lo saltea, o que el camino no lo atraviesa. El cliente, una
    de estabilidad y un NOT_EVIDENCED nunca dicen una falla."""
    if e.get("sourceType") not in DEL_SERVIDOR + DEL_CAMINO:
        return False
    if USO in e["establishes"] and e.get("value") == AUSENTE:
        return True
    return CAMINO in e["establishes"] and e.get("value") in (SALTEADO, NO_ATADO)


def _bloqueos(cat, citados, sid=None, registradas=(), nombradas=(), cids=()):
    """(estados, motivos) de las pruebas que no se pudieron leer y pesan. Con `sid`, las citadas o las
    que tocan esa superficie o uno de sus controles, digan lo que digan; sin el, las que nombran una
    superficie que el registro no tiene y la senal o el inventario si."""
    estados, motivos = set(), set()
    for e in cat.values():
        if e["sourceType"] != PRUEBA:
            continue
        citada = _citada(e, citados)
        if sid is not None and not (citada or _toca(e, sid, cids)):
            continue
        if sid is None and (any(_ev.en(s, e.get("surfaces")) for s in registradas)
                            or not any(_ev.en(s, e.get("surfaces")) for s in nombradas)):
            continue
        _, bloqueo, m = _lectura(e)
        if bloqueo:
            estados.add(bloqueo)
            motivos.update(m)
    return sorted(estados), sorted(motivos)


def _abierto(bloqueos, defecto=SIN_COBERTURA):
    if PRUEBA_INSEGURA in bloqueos:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in bloqueos:
        return SIN_OBJETIVO
    return defecto


def _bloquear(estado, motivo, bloqueos, ilegibles):
    """🔴 El unico paso de bloqueo. Por aca pasan la superficie, el PASS y el NOT_APPLICABLE.

    Lo que no se pudo leer y pesa impide el PASS; un FAIL no se toca: bloquear impide aprobar, no
    tapa lo que falla. Tampoco reemplaza un sin resolver que ya estaba."""
    if estado not in RESUELTAS:
        return estado, motivo
    if bloqueos:
        return _abierto(bloqueos), "una prueba que se cita, o que dice que falta un control, no se pudo leer"
    if ilegibles:
        return SIN_COBERTURA, ("hay evidencia ilegible, o de otro ambiente, sobre la superficie o un "
                               "control, y esa podia ser la que decia que falta")
    return estado, motivo


# -- la superficie, en el orden de la spec ------------------------------------------------------

def _items(x, que, clases, cid=None, valores=None, solo_citadas=True, citados=None):
    """Los items legibles, del ambiente, de `clases` que establecen `que` sobre la superficie o el
    control."""
    citados = x["citados"] if citados is None else citados
    return [e for e in x["cat"].values()
            if _sostiene(e, que, clases, x["ambiente"]) and (valores is None or e.get("value") in valores)
            and (_citada(e, citados) or not solo_citadas)
            and _nombra(e, x["sid"], cid)]


def _ids(items):
    return sorted(e["evidenceId"] for e in items)


def _paso_alcance(x):
    s, salida = x["superficie"], x["salida"]
    publica, autenticada = s.get("publiclyReachable"), s.get("authenticationRequired")
    alcance = {"publiclyReachable": publica, "authenticationRequired": autenticada,
               "evidenceUsed": [], "contradictedBy": []}
    salida["scope"] = alcance
    if publica == SI and autenticada == NO:
        # 🔴 Entrar al alcance no cuesta nada: es pedir mas control, no menos.
        alcance["state"] = "IN_SCOPE"
        return None, ""
    if publica not in (SI, NO) or autenticada not in (SI, NO):
        alcance["state"] = SIN_RESOLVER
        return SIN_SUPERFICIE, "no consta si la superficie es publica y sin autenticacion"
    apoyo, contra = [], []
    for campo, que, fuera in (("publiclyReachable", ALCANZABLE, NO),
                              ("authenticationRequired", AUTENTICACION, SI)):
        if s.get(campo) != fuera:
            continue
        todas = _items(x, que, DEL_CAMINO, valores=(SI, NO), solo_citadas=False)
        apoyo += [e for e in todas if _citada(e, x["citados"]) and e.get("value") == fuera]
        contra += [e for e in todas if e.get("value") != fuera]
    # Una evidencia que dice que la superficie es publica sin autenticacion tambien contradice.
    contra += [e for e in x["presentes"] if _ev.en(x["sid"], e.get("surfaces"))]
    alcance["contradictedBy"] = _ids(contra)
    if apoyo and not contra:
        alcance["state"] = "OUT_OF_SCOPE"
        alcance["evidenceUsed"] = _ids(apoyo)
        return NO_APLICA, "una evidencia establece que la superficie no es publica o pide autenticacion"
    alcance["state"] = SIN_RESOLVER
    return SIN_SUPERFICIE, ("la superficie sale del alcance sin una evidencia que lo sostenga, o con una "
                            "que dice lo contrario")


def _control(x, c):
    """Un control: si existe del lado del servidor, si el camino lo atraviesa, y sus dimensiones."""
    cid = _texto(c.get("controlId"))
    citados = x["citados"] | _ev.claves(c.get("evidence"))
    capa = c.get("enforcementLayer")
    # 🔴 Que el control existe lo dice un item que lo nombra; uno de la superficie habla de la superficie.
    existe = [e for e in _items(x, USO, DEL_SERVIDOR, cid, (PRESENTE,), citados=citados)
              if _ev.en(cid, e.get("controls"))]
    niega = [e for e in _items(x, USO, DEL_SERVIDOR, cid, (AUSENTE,), solo_citadas=False, citados=citados)
             if e.get("controls")]
    # 🔴 El camino se prueba por superficie: el item tiene que nombrarla, no solo al control.
    camino = [e for e in _items(x, CAMINO, DEL_CAMINO, cid, (ATADO, SALTEADO, NO_ATADO), solo_citadas=False,
                                citados=citados) if _ev.en(x["sid"], e.get("surfaces"))]
    citado = {v: _ids(e for e in camino if e.get("value") == v and _citada(e, citados))
              for v in (ATADO, SALTEADO, NO_ATADO)}
    no_citadas = _ids(e for e in camino if not _citada(e, citados) and e.get("value") != ATADO)
    # `controlType` es texto libre y no sale: el resultado no lo necesita y ahi puede ir cualquier cosa.
    salida = {"controlId": cid, "enforcementLayer": capa,
              "declared": {"pathBinding": c.get("pathBinding"),
                           "excessiveConsumptionMitigation": c.get("excessiveConsumptionMitigation"),
                           "automatedConsumptionMitigation": c.get("automatedConsumptionMitigation"),
                           "stabilityEvidence": c.get("stabilityEvidence")},
              "existence": _ids(existe), "contradictedBy": _ids(niega) + no_citadas,
              # 🔴 Lo del navegador queda a la vista y no sostiene nada.
              "clientSide": sorted(e["evidenceId"] for e in x["cat"].values()
                                   if USO in e["establishes"] and e["sourceType"] in DEL_CLIENTE
                                   and _citada(e, citados)),
              "path": {"bound": citado[ATADO], "bypass": citado[SALTEADO], "notBound": citado[NO_ATADO]},
              "dimensions": {}}
    if citado[SALTEADO]:
        salida["coverage"] = SALTEO
    elif citado[ATADO] and (citado[NO_ATADO] or no_citadas):
        salida["coverage"] = SIN_RESOLVER
    elif citado[NO_ATADO]:
        salida["coverage"] = NO_ATADO
    elif (citado[ATADO] and c.get("pathBinding") == ATADO and existe and not niega and capa in CAPAS):
        salida["coverage"] = ATADO
    else:
        salida["coverage"] = SIN_RESOLVER
    usadas = set(salida["existence"]) | set(citado[ATADO]) if salida["coverage"] == ATADO else set()
    for que, campo, clases, _ in DIMENSIONES:
        todas = [e for e in _items(x, que, clases, cid, (EVIDENCIADA, NO_EVIDENCIADA), solo_citadas=False,
                                   citados=citados) if _ev.en(cid, e.get("controls"))]
        apoyo = [e for e in todas if _citada(e, citados) and e.get("value") == EVIDENCIADA]
        contra = [e for e in todas if e.get("value") == NO_EVIDENCIADA]
        sostenida = bool(c.get(campo) == EVIDENCIADA and apoyo and not contra)
        salida["dimensions"][campo] = {"evidenced": sostenida,
                                       "evidenceUsed": _ids(apoyo) if sostenida else [],
                                       "contradictedBy": _ids(contra)}
    salida["insufficient"] = sorted(e["evidenceId"] for e in x["cat"].values() if _citada(e, citados)
                                    and e["sourceType"] in INSUFICIENTES)
    salida["_usadas"] = usadas
    salida["_citados"] = citados
    return salida


def _paso_control(x):
    s, salida = x["superficie"], x["salida"]
    controles = [_control(x, c) for c in s.get("controls") or []]
    x["controles"] = controles
    ids = [c["controlId"] for c in controles]
    ausente = _items(x, USO, DEL_SERVIDOR, valores=(AUSENTE,))
    salida["missingControlEvidence"] = _ids(e for e in ausente if not e.get("controls"))
    if any(c["coverage"] == SALTEO for c in controles):
        return SALTEO, "el camino publico saltea un control declarado de la superficie"
    if not controles:
        return FALTA, "la superficie publica sin autenticacion no declara ningun control de uso"
    if salida["missingControlEvidence"]:
        return FALTA, "una evidencia del servidor establece que la superficie no tiene control de uso"
    if all(c["coverage"] == NO_ATADO for c in controles):
        return FALTA, "ningun control declarado esta en el camino publico de la superficie"
    # Lo no citado que dice que falta un control, o que el camino lo saltea, nunca hace FAIL.
    no_citadas = _ids(e for e in _items(x, USO, DEL_SERVIDOR, valores=(AUSENTE,), solo_citadas=False)
                      if not _citada(e, x["citados"]) and not e.get("controls"))
    if no_citadas:
        salida["contradictedBy"].extend(no_citadas)
        return SIN_COBERTURA, "una evidencia no citada dice que la superficie no tiene control"
    if len(set(ids)) != len(ids):
        salida["issues"].append("controles repetidos: %s" % ", ".join(
            sorted({str(i) for i in ids if ids.count(i) > 1})))
        return SIN_COBERTURA, "la superficie declara dos veces el mismo control"
    if any(c["contradictedBy"] for c in controles):
        return SIN_COBERTURA, "una evidencia contradice un control o su camino"
    if not any(c["coverage"] == ATADO for c in controles):
        # Si lo que faltaba era una prueba que no se pudo leer, se dice eso.
        faltan = set()
        for c in controles:
            if not c["existence"]:
                faltan.add(USO)
            elif not c["path"]["bound"]:
                faltan.add(CAMINO)
        return _faltaba(x, tuple(sorted(faltan)), SIN_COBERTURA), ("ningun control consta del lado del servidor y en el camino publico; la "
                               "configuracion sola, o el navegador, no alcanzan")
    return None, ""


def _paso_dimensiones(x):
    salida = x["salida"]
    cubren = [c for c in x["controles"] if c["coverage"] == ATADO]
    abiertos = []
    for que, campo, _, estado in DIMENSIONES:
        quienes = sorted(str(c["controlId"]) for c in cubren if c["dimensions"][campo]["evidenced"])
        salida["dimensions"][campo] = {"evidenced": bool(quienes), "controls": quienes,
                                       "state": PASA if quienes else estado}
        if not quienes:
            abiertos.append((que, estado))
    if abiertos:
        return _faltaba(x, (abiertos[0][0],), abiertos[0][1]), ("una dimension del control de uso no consta "
                                                            "con evidencia citada")
    return None, ""


def _faltaba(x, ques, defecto):
    """El estado de un paso sin resolver. Si lo que faltaba es lo que decia una prueba citada que no se
    pudo leer -insegura o sin objetivo- sobre eso mismo, se dice eso; si no, el sin resolver del paso.
    🔴 No es un bloqueo: una prueba que habla de otra cosa no cambia lo que falta aca."""
    estados = {_lectura(e)[1] for e in x["cat"].values() if e["sourceType"] == PRUEBA
               and _citada(e, x["todos"]) and any(q in e["establishes"] for q in ques)}
    return _abierto(estados - {None}, defecto)


def _paso_declarado(x):
    s = x["superficie"]
    if s.get("result") != PROTEGIDA:
        # Declarar la falla sin la evidencia que la establece no es FAIL.
        return SIN_COBERTURA, "el registro no declara la superficie protegida, y la evidencia no lo establece"
    if s.get("verificationMode") == SIN_VERIFICAR:
        return SIN_COBERTURA, "el registro dice que la superficie no se verifico"
    return None, ""


def evaluar_superficie(superficie, d):
    """Una superficie, sola: su alcance, sus controles, sus dimensiones y la evidencia por id."""
    cat, crudas = d["catalog"], d["raw"]
    sid = _ev.nfc(superficie.get("surfaceId"))
    citados = _ev.claves(superficie.get("evidence"))
    todos_los_citados = set(citados)
    for c in superficie.get("controls") or []:
        todos_los_citados |= _ev.claves(c.get("evidence"))
    salida = {"surfaceId": sid, "interfaceType": superficie.get("interfaceType"),
              "declaredResult": superficie.get("result"),
              "verificationMode": superficie.get("verificationMode"),
              "controls": [], "dimensions": {}, "contradictedBy": [], "issues": [],
              "insufficient": sorted(e["evidenceId"] for e in cat.values() if _citada(e, citados)
                                     and e["sourceType"] in INSUFICIENTES)}
    controles_ids = [_texto(c.get("controlId")) for c in superficie.get("controls") or []]
    salida["blockedBy"], salida["unsafe"] = _bloqueos(cat, todos_los_citados, sid, cids=controles_ids)
    x = {"cat": cat, "citados": citados, "todos": todos_los_citados, "sid": sid, "superficie": superficie,
         "salida": salida, "ambiente": d["environment"], "presentes": d["present"], "controles": []}
    alcance = _paso_alcance(x)
    if alcance[0] is not None:
        # 🔴 Sin el alcance resuelto la superficie no falla; fuera sostenido, no pesa.
        pasos = [alcance]
    else:
        pasos = [_paso_control(x)]
        if pasos[0][0] is None or pasos[0][0] not in FALLAS:
            if any(c["coverage"] == ATADO for c in x["controles"]):
                pasos.append(_paso_dimensiones(x))
            pasos.append(_paso_declarado(x))
    fallas = [p for p in pasos if p[0] in FALLAS]
    abiertos = sorted((p for p in pasos if p[0] is not None),
                      key=lambda p: ORDEN_DE_LO_ABIERTO.index(p[0]) if p[0] in ORDEN_DE_LO_ABIERTO else -1)
    estado, motivo = (fallas or abiertos or [(PASA, "")])[0]

    # Lo que dice una falla desde otro ambiente no hace FAIL e impide el PASS, si pesa.
    otro_ambiente = sorted(e["evidenceId"] for e in cat.values() if _dice_falla(e) and _lectura(e)[0]
                           and not _del_ambiente(e, d["environment"])
                           and (_citada(e, todos_los_citados) or _ev.en(sid, e.get("surfaces"))))
    if otro_ambiente:
        salida["contradictedBy"].extend(otro_ambiente)
        salida["issues"].append("evidencia de otro ambiente dice que falta un control o que se saltea: %s"
                                % ", ".join(map(str, otro_ambiente)))
    # 🔴 Lo que no se pudo leer y pesa impide el PASS: un item con `outcome` fuera de lo legible es
    # ilegible igual que uno mal formado. Pesa si se lo cita, o si toca la superficie o un control suyo,
    # diga lo que diga: un "no" ilegible no pesa menos que uno legible (refutador, pase 1).
    sin_leer = [e for e in cat.values() if _lectura(e)[:2] == (False, None)
                and (_citada(e, todos_los_citados) or _toca(e, sid, controles_ids))]
    ilegibles = sorted(set(r for r in todos_los_citados if r not in cat)
                       | set(_ev.ilegibles_sobre(sid, cat, crudas))
                       | {i for cid in controles_ids if cid for i in _ev.ilegibles_sobre(cid, cat, crudas)}
                       | {e["evidenceId"] for e in sin_leer})
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre la superficie o un control: %s"
                                % ", ".join(str(i) for i in ilegibles))
    final, motivo = _bloquear(estado, motivo, salida["blockedBy"], ilegibles + otro_ambiente)

    usadas = set(salida["scope"].get("evidenceUsed") or [])
    fallidas = set(salida.get("missingControlEvidence") or [])
    for c in x["controles"]:
        usadas |= c.pop("_usadas")
        c.pop("_citados")
        if c["coverage"] == ATADO:
            for dim in c["dimensions"].values():
                usadas |= set(dim["evidenceUsed"])
        fallidas |= set(c["path"]["bypass"]) | set(c["path"]["notBound"])
        # Las huellas de despliegue de lo que sostiene el control, para atarlo a lo que corre.
        propias = [cat[_ev.nfc(i)] for i in set(c["existence"]) | set(c["path"]["bound"])
                   | {j for dim in c["dimensions"].values() for j in dim["evidenceUsed"]}
                   if _ev.nfc(i) in cat]
        c["deployment"] = {h: sorted({e[h] for e in propias if isinstance(e.get(h), str)})
                           for h in HUELLAS}
        salida["controls"].append(c)
    salida["controls"] = _ev.ordenadas(salida["controls"])
    # Un PASS o un NOT_APPLICABLE se sostienen con lo que los establecio, y un FAIL con lo que dice la
    # falla. Lo bloqueado o abierto no se sostiene con nada.
    salida["evidenceUsed"] = (sorted(usadas) if final in RESUELTAS and final == estado
                              else sorted(fallidas) if final in FALLAS else [])
    salida["contradictedBy"] = sorted(set(salida["contradictedBy"]))
    salida["issues"] = sorted(set(salida["issues"]))
    salida["state"] = final
    salida["result"] = (PROTEGIDA if final == PASA else final if final in ORDEN_DE_LAS_FALLAS + (NO_APLICA,)
                        else SIN_RESOLVER)
    queda = set(salida["blockedBy"]) if final not in FALLAS else set()
    salida["states"] = sorted(({p[0] for p in pasos if p[0] is not None} | {final} | queda)
                              - {PASA, NO_APLICA})
    salida["reason"] = motivo
    return salida


def _de_lo_evaluado(estados):
    """(estado, motivo) de un conjunto de estados."""
    for falla in ORDEN_DE_LAS_FALLAS:
        if falla in estados:
            return falla, "al menos una superficie publica no tiene un control de uso que valga"
    if FALLA in estados:
        return FALLA, "al menos una superficie publica no tiene un control de uso que valga"
    for e in ORDEN_DE_LO_ABIERTO:
        if e in estados:
            return e, "hay algo material sin resolver"
    return PASA, ""


# -- la evaluacion -------------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de Vu9, superficie por superficie.

    `caso`:

        {"registry": {...},         # el registro de Vu9; opcional
         "evidence": [...]}         # el catalogo, cerrado
    """
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    valor = _combinar(d["value"], senal)
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "signalValue": valor, "environment": d["environment"], "surfaces": [], "issues": [],
              "coverage": d["coverage"]}
    if d["problem"]:
        salida["issues"].append(d["problem"])
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    salida["issues"].sort()
    c = d["coverage"]
    nombradas = sorted(set(c["namedBySignal"]) | set(c["inventory"]["surfaces"]))
    sueltos, motivos = _bloqueos(d["catalog"], d["cited"], registradas=c["registered"],
                                 nombradas=nombradas)
    salida["blockedBy"], salida["unsafe"] = sueltos, motivos

    if valor == _senales.SIN_RESOLVER:
        estado, motivo = SIN_APLICABILIDAD, ("no consta si la aplicacion expone funcionalidad publica sin "
                                             "autenticacion")
    elif valor == _senales.FALSA:
        estado, motivo = NO_APLICA, ("una evidencia autoritativa establece que no hay funcionalidad "
                                     "publica sin autenticacion")
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
    estados = [s["state"] for s in superficies if s["state"] != NO_APLICA]
    c = d["coverage"]
    # 🔴 El inventario entero nombra toda superficie en alcance, y toda superficie que nombra esta.
    c["notInInventory"] = sorted(str(s["surfaceId"]) for s in superficies
                                 if s["scope"].get("state") == "IN_SCOPE"
                                 and s["surfaceId"] not in c["inventory"]["surfaces"])
    abiertos = []
    # Sin superficie en alcance, con una nombrada sin entrada, repetida, o sin el inventario entero.
    if (not estados or c["missingSurfaces"] or c["duplicatedSurfaces"] or c["notInInventory"]
            or not c["inventory"]["complete"]):
        abiertos.append(SIN_SUPERFICIE)
    estado, motivo = _de_lo_evaluado(estados + abiertos)
    if estado in abiertos and estado not in estados:
        motivo = ("la superficie publica no esta entera: inventario entero %s, superficies sin entrada "
                  "%s, repetidas %s" % ("si" if c["inventory"]["complete"] else "no",
                                        c["missingSurfaces"] or "-", c["duplicatedSurfaces"] or "-"))
    return estado, motivo


def _cerrar(salida, estado, motivo, previo=None):
    salida["state"] = estado
    todos = {estado} if estado != PASA else set()
    # Lo que el bloqueo reemplazo sin resolver sigue a la vista.
    if previo not in (None,) + RESUELTAS:
        todos.add(previo)
    for s in salida["surfaces"]:
        todos.update(s.get("states") or [])
    if salida["blockedBy"] and estado not in FALLAS:
        todos.update(salida["blockedBy"])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _ev.depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


def evidencia_usada(resultado):
    """Los ids que sostienen el resultado: alcance, controles, caminos y dimensiones."""
    r = resultado if isinstance(resultado, dict) else {}
    ids = set()
    for s in r.get("surfaces") or []:
        ids.update(s.get("evidenceUsed") or [])
    return sorted(i for i in ids if isinstance(i, str))


# -- hacia seguridad.resultado ----------------------------------------------------------------------

def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu9", ...)`, desde la salida de `evaluar`.

    Vu9 no tiene algoritmo propio en `seguridad.py`: va por el generico. Los dos controles de la fila
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
    """La entrada de `checks.json` para una unidad de `ES0902.Vu9`, o `None`.

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
