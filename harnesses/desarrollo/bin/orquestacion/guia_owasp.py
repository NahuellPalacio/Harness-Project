"""La review de ES0902 Vu10: la guia OWASP que aplica, revisada y con fuente vigente.

    source: ES0902 / 6.2 / 6 / Vu10

    "Para mejorar la seguridad en las aplicaciones, se debe tener en cuenta la informacion suministrada
    en los siguientes links: Aplicaciones Web: OWASP Top 10 - API's y/o Web Services: OWASP API
    Security - Aplicaciones Mobile: OWASP Mobile Top 10"

🔴 **Es una review, no un check.** La fila dice `checks: []`. Este modulo es la agregacion
determinista de la review, como `linea_base.py` lo es de la de O1: el modelo puede llenar el registro
-disposiciones, razones, evidencia-, nunca decide el estado.

🔴 **Nada de memoria.** La edicion de cada familia y sus puntos salen de una foto autoritativa de la
fuente, y su vigencia del mecanismo de fuentes confiables. El modulo no tiene ninguna lista de puntos
ni ningun id de OWASP: la proxima edicion entra sin tocarlo.

🔴 **Un hallazgo no es la cobertura.** `FINDING_PRESENT` es una disposicion valida. La severidad y la
confianza son del hallazgo y viajan al reporte de seguridad; el estado de la review no las lee.

🔴 **Omitir una familia es ignorarla.** Es el unico FAIL: una review hecha a la que le falta una familia
aplicable. Lo que falta o no se sostiene deja la review sin resolver, nunca en FAIL ni en PASS.
"""
import io
import json
import re

from . import roster
from . import senales as _senales

REVIEW = "owasp-security-guidance-review"
POLICY = "owasp-security-guidance-required"
TIPO = "REVIEW"
REGLA = "Vu10"
CLAVE = "ES0902.Vu10"
SENAL = "owaspApplicableAssetPresent"

ARCHIVO = "owasp-security-guidance-review.json"
SCHEMA = "owasp-security-guidance-review.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}

# -- los estados -------------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_ACTIVOS = "OWASP_ASSET_COVERAGE_UNRESOLVED"
SIN_FUENTE = "OWASP_GUIDANCE_SOURCE_UNAVAILABLE"
SIN_FRESCURA = "OWASP_GUIDANCE_FRESHNESS_UNRESOLVED"
INCOMPLETA = "OWASP_GUIDANCE_COVERAGE_INCOMPLETE"
PUNTO_ABIERTO = "OWASP_GUIDANCE_ITEM_UNRESOLVED"
REVISION_INCOMPLETA = "REVIEW_INCOMPLETE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_ACTIVOS, SIN_FUENTE, SIN_FRESCURA, INCOMPLETA,
           PUNTO_ABIERTO, REVISION_INCOMPLETA)
RESUELTAS = (PASA, NO_APLICA)
# Sin una familia omitida, el estado que se informa es el primero de este orden.
ORDEN_DE_LO_ABIERTO = (SIN_APLICABILIDAD, SIN_ACTIVOS, SIN_FUENTE, SIN_FRESCURA, INCOMPLETA,
                       REVISION_INCOMPLETA)

FAMILIAS = ("WEB", "API_OR_WEB_SERVICE", "MOBILE")

# -- lo que dice el registro ----------------------------------------------------------------

SIN_HALLAZGO = "REVIEWED_NO_FINDING"
CON_HALLAZGO = "FINDING_PRESENT"
NO_APLICABLE = "NOT_APPLICABLE_WITH_RATIONALE"
SIN_RESOLVER = "UNRESOLVED"
VIGENTE = "CURRENT"
NO_DISPONIBLE_FUENTE = "SOURCE_UNAVAILABLE"

# -- lo que establece una evidencia -----------------------------------------------------------

ACTIVO = "OWASP_APPLICABLE_ASSET"          # value PRESENT | ABSENT
PRESENTE, AUSENTE = "PRESENT", "ABSENT"
TIPO_DE_ACTIVO = "ASSET_TYPE"              # value WEB | API_OR_WEB_SERVICE | MOBILE; assets
INVENTARIO = "ASSET_INVENTORY"             # value COMPLETE | INCOMPLETE; assets
ENTERO = "COMPLETE"
FUENTE = "OWASP_GUIDANCE_SOURCE"           # value: la edicion; reference, families, items
FRESCURA = "SOURCE_FRESHNESS"              # value: el estado de frescura; reference, version
HALLAZGO = "SECURITY_FINDING"              # evidenceId: el id del hallazgo; severity, confidence
PUNTO = "GUIDANCE_ITEM_EVIDENCE"           # lo que sostiene una disposicion

CONFIRMADA = "CONFIRMED"
OBSERVADA = "OBSERVED"
NO_DISPONIBLE = "UNAVAILABLE"
LEIBLES = (None, CONFIRMADA, OBSERVADA)

# -- que clase sostiene que --------------------------------------------------------------------
# 🔴 Las tablas son del harness, no del estandar. Ninguna nombra un marco, un scanner ni un punto.

PRUEBA = "AUTHORIZED_DYNAMIC_TEST"
DEBILES = ("README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "NAMING_CONVENTION", "MODEL_KNOWLEDGE")
AUTORIDADES = ("SECURITY_DOCUMENTATION", "ARCHITECTURE_DOCUMENTATION", "PROJECT_REQUIREMENT",
               "PROJECT_CONTRACT", "ASSESSMENT_FINDING", "OTHER_AUTHORITATIVE_EVIDENCE")
DE_TIPO = AUTORIDADES + ("ASSET_INVENTORY", "API_SPECIFICATION", "ROUTE_INVENTORY",
                         "MOBILE_BUILD_CONFIGURATION", "APPLICATION_CODE")
DE_INVENTARIO = AUTORIDADES + ("ASSET_INVENTORY",)
DE_FUENTE = ("AUTHORITATIVE_SOURCE_SNAPSHOT", "TRUSTED_KNOWLEDGE_REGISTRY")
DE_FRESCURA = ("TRUSTED_KNOWLEDGE_REGISTRY",)
# 🔴 Lo que sostiene lo decide la clase, no lo que el item dice de si mismo (refutador, pase 2). El
# resultado final de otra regla no se copia, y la foto o el registro de fuentes dicen la fuente, nunca un
# punto ni un hallazgo.
NO_SOSTIENEN_PUNTO = DEBILES + ("RULE_RESULT",) + DE_FUENTE

PRODUCCION = "PRD"
AMBIENTES_DE_PRUEBA = ("DEV", "QA", "HML", "OTHER")

TEXTO, LISTA, BOOLEANO = "text", "list-of-text", "bool"
# 🔴 Cerrado: no hay campo para una credencial, un payload ni un exploit. `severity`, `confidence`,
# `internal` y `authenticated` se aceptan y el estado no los lee nunca.
FORMA = {"evidenceId": TEXTO, "sourceType": TEXTO, "reference": TEXTO, "establishes": LISTA,
         "assets": LISTA, "families": LISTA, "items": LISTA, "value": TEXTO, "version": TEXTO,
         "sourceFingerprint": TEXTO, "resolvedAt": TEXTO, "outcome": TEXTO, "environment": TEXTO,
         "authorized": BOOLEANO, "bounded": BOOLEANO, "syntheticData": BOOLEANO, "destructive": BOOLEANO,
         "reusedFrom": TEXTO, "title": TEXTO, "severity": TEXTO, "confidence": TEXTO,
         "blocking": BOOLEANO, "internal": BOOLEANO, "authenticated": BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes")


def _ev():
    """La lib de evidencia de los controles: catalogo cerrado, NFC y regla de salida."""
    import importlib.util
    import os
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "controles", "lib", "evidencia.py")
    if "_evidencia_vu10" not in _CACHE:
        spec = importlib.util.spec_from_file_location("_evidencia_vu10", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CACHE["_evidencia_vu10"] = modulo
    return _CACHE["_evidencia_vu10"]


_CACHE = {}


def catalogo(caso):
    return _ev().catalogo(caso, FORMA, OBLIGATORIOS)


def prueba_segura(e):
    """Los motivos por los que una prueba dinamica no era segura. Vacio es segura. No ejecuta nada."""
    ev = _ev()
    motivos = []
    if e.get("authorized") is not True:
        motivos.append("NOT_AUTHORIZED")
    ambiente = e.get("environment")
    if ambiente in (None, "", "UNRESOLVED"):
        motivos.append("ENVIRONMENT_UNRESOLVED")
    elif ev.igual(ambiente, PRODUCCION):
        motivos.append("PRODUCTION")
    elif ev.nfc(ambiente) not in AMBIENTES_DE_PRUEBA:
        motivos.append("ENVIRONMENT_UNKNOWN")
    if e.get("bounded") is not True:
        motivos.append("NOT_BOUNDED")
    if e.get("syntheticData") is not True:
        motivos.append("NOT_SYNTHETIC_DATA")
    if e.get("destructive") is True:
        motivos.append("DESTRUCTIVE")
    return sorted(motivos)


def _legible(e):
    """La misma compuerta para todo: una prueba insegura o sin objetivo no se lee."""
    if e.get("sourceType") == PRUEBA and (e.get("outcome") == NO_DISPONIBLE or prueba_segura(e)):
        return False
    return e.get("outcome") in LEIBLES


def _sostiene(e, que, clases):
    return que in e["establishes"] and e["sourceType"] in clases and _legible(e)


def _nfcs(lista):
    ev = _ev()
    return sorted({ev.nfc(x) for x in (lista or []) if isinstance(x, str)})


def _texto(x):
    return _ev().nfc(x) if isinstance(x, str) else None


# -- el registro --------------------------------------------------------------------------------

VACIO = {"version": "1.0", "evaluatedAt": None, "assets": [], "families": [],
         "overall": REVISION_INCOMPLETA}


def cargar(desde=None):
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return dict(VACIO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
    import rutas
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return None
    from . import tools
    armador = tools._armador()
    if armador is None:
        return None
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def entradas(caso, desde=None):
    declarado = (caso or {}).get("registry")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return dict(VACIO), "el registro de la review OWASP no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return dict(VACIO), "el registro de la review OWASP no se pudo validar"
    if errores:
        return dict(VACIO), "el registro de la review OWASP no valida contra su schema: %d errores" % len(errores)
    return doc, ""


# -- la senal y los activos -----------------------------------------------------------------------

def derivar(caso, desde=None):
    ev = _ev()
    entrada = caso if isinstance(caso, dict) else {}
    registro, problema = entradas(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    activos = [a for a in registro.get("assets") or [] if isinstance(a, dict)]

    sobre = [e for e in cat.values() if ACTIVO in e["establishes"]]
    presentes = [e for e in sobre if e.get("value") == PRESENTE and e["sourceType"] not in DEBILES
                 and _legible(e)]
    dicen_que_si = [e for e in sobre if e.get("value") == PRESENTE]
    ausentes = [e for e in sobre if e.get("value") == AUSENTE and _sostiene(e, ACTIVO, AUTORIDADES)]
    # 🔴 Lo que no se pudo leer sobre la pregunta impide apagarla, sea mal formado o con un `outcome` fuera
    # de lo legible (refutador, pase 1).
    ilegibles = (ev.ilegibles_sobre(ACTIVO, cat, crudas) + [e["evidenceId"] for e in sobre if not _legible(e)]
                 + [e["evidenceId"] for e in sobre if e.get("value") not in (PRESENTE, AUSENTE)])
    if presentes:
        valor = _senales.VERDADERA
    elif ausentes and not dicen_que_si and not activos and not ilegibles:
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    if problema and valor == _senales.FALSA:
        valor = _senales.SIN_RESOLVER
    return {"value": valor, "registry": registro, "problem": problema, "assets": activos, "catalog": cat,
            "raw": crudas, "repeated": repetidos, "malformed": torcidas, "present": presentes,
            "absent": ausentes}


def senal(caso, desde=None):
    ev = _ev()
    d = derivar(caso, desde)
    usadas = d["present"] if d["value"] == _senales.VERDADERA else (
        d["absent"] if d["value"] == _senales.FALSA else [])
    evidencia = [{"evidenceId": "owasp:%s" % e["evidenceId"], "sourceType": "REPOSITORY_CONFIGURATION",
                  "reference": "%s#%s" % (ARCHIVO, e["evidenceId"]),
                  "claim": ("una evidencia establece un activo web, API o mobile gobernado"
                            if d["value"] == _senales.VERDADERA else
                            "una evidencia autoritativa establece que no hay activos web, API ni mobile"),
                  "supports": d["value"]} for e in usadas]
    return ev.depurar(_senales.producir(SENAL, ev.ordenadas(evidencia), {"type": "DETERMINISTIC"},
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
    if valor == derivado or (valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER):
        return valor
    return _senales.SIN_RESOLVER


def _activos(d):
    """(familias, salida, abierto). Las familias aplicables son la union de los tipos sostenidos."""
    ev = _ev()
    cat = d["catalog"]
    salida, abierto, familias = [], False, set()
    ids = [_texto(a.get("assetId")) for a in d["assets"]]
    for a in d["assets"]:
        aid = _texto(a.get("assetId"))
        declarados = _nfcs(a.get("assetTypes"))
        # 🔴 `internal` y `authenticated` no se leen: un activo interno o autenticado cuenta igual.
        tipos = [e for e in cat.values() if _sostiene(e, TIPO_DE_ACTIVO, DE_TIPO) and ev.en(aid, e.get("assets"))]
        dichos = _nfcs(e.get("value") for e in tipos)
        otros_dichos = _nfcs(e.get("value") for e in cat.values() if TIPO_DE_ACTIVO in e["establishes"]
                             and ev.en(aid, e.get("assets")) and _legible(e) and e["sourceType"] not in DEBILES)
        sostenidos = [t for t in declarados if t in dichos]
        faltan = [t for t in declarados if t not in dichos]
        de_mas = [t for t in otros_dichos if t not in declarados and t in FAMILIAS]
        # Lo que no se pudo leer sobre el activo pesa en todas sus formas.
        ilegibles = sorted(set(ev.ilegibles_sobre(aid, cat, d["raw"]))
                           | {e["evidenceId"] for e in cat.values()
                              if (TIPO_DE_ACTIVO in e["establishes"] or INVENTARIO in e["establishes"])
                              and ev.en(aid, e.get("assets")) and not _legible(e)}
                           # Regla 2: un tipo que no dice una de las tres familias no dice ni si ni no.
                           | {e["evidenceId"] for e in cat.values() if TIPO_DE_ACTIVO in e["establishes"]
                              and ev.en(aid, e.get("assets")) and _legible(e) and e["sourceType"] not in DEBILES
                              and e.get("value") not in FAMILIAS})
        if faltan or de_mas or ilegibles:
            abierto = True
        familias.update(sostenidos)
        salida.append({"assetId": aid, "assetTypes": declarados, "supported": sostenidos,
                       "unsupported": faltan, "undeclared": de_mas, "unreadable": [str(i) for i in ilegibles],
                       "evidenceUsed": sorted(e["evidenceId"] for e in tipos if _texto(e.get("value")) in sostenidos)})
    enteros = [e for e in cat.values() if _sostiene(e, INVENTARIO, DE_INVENTARIO) and e.get("value") == ENTERO]
    listas = {tuple(_nfcs(e.get("assets"))) for e in enteros}
    otros = [e for e in cat.values() if INVENTARIO in e["establishes"] and e.get("value") != ENTERO
             and _legible(e) and e["sourceType"] not in DEBILES]
    completo = (len(listas) == 1 and not otros and sorted(set(ids)) == list(listas.pop()) and len(set(ids)) == len(ids))
    if not completo or not d["assets"]:
        abierto = True
    cobertura = {"inventoryComplete": completo, "inventory": sorted(e["evidenceId"] for e in enteros),
                 "duplicatedAssets": sorted({str(i) for i in ids if ids.count(i) > 1})}
    return sorted(familias), ev.ordenadas(salida), abierto, cobertura


# -- la familia ------------------------------------------------------------------------------------

def _foto(familia, fuente, cat):
    """(foto, puntos) de la fuente declarada, o (None, [])."""
    ev = _ev()
    ref, edicion = _texto(fuente.get("sourceRef")), _texto(fuente.get("edition"))
    huella = _texto(fuente.get("sourceFingerprint"))
    if not ref or not edicion:
        return [], None
    fotos = [e for e in cat.values() if _sostiene(e, FUENTE, DE_FUENTE) and ev.igual(e.get("reference"), ref)
             and ev.igual(e.get("value"), edicion) and ev.en(familia, e.get("families"))
             and (huella is None or e.get("sourceFingerprint") is None
                  or ev.igual(e.get("sourceFingerprint"), huella))]
    formas = {tuple(_nfcs(e.get("items"))) for e in fotos}
    return fotos, (list(formas.pop()) if len(formas) == 1 else None)


def _frescura(fuente, cat, crudas=()):
    ev = _ev()
    ref, edicion = _texto(fuente.get("sourceRef")), _texto(fuente.get("edition"))
    de_la_fuente = [e for e in cat.values() if FRESCURA in e["establishes"] and ev.igual(e.get("reference"), ref)]
    sobre = [e for e in de_la_fuente if _legible(e)]
    vigentes = [e for e in sobre if e["sourceType"] in DE_FRESCURA and e.get("value") == VIGENTE
                and ev.igual(e.get("version"), edicion)]
    # 🔴 Un "no" de cualquier clase quita el CURRENT; lo ilegible sobre la fuente tambien (refutador, pase 1).
    contra = ([e for e in sobre if not (e.get("value") == VIGENTE and ev.igual(e.get("version"), edicion))]
              + [e for e in de_la_fuente if not _legible(e)])
    torcidos = sorted(set(ev.ilegibles_sobre(ref, cat, crudas) if ref else [])
                      | {e["evidenceId"] for e in cat.values() if ref and ev.igual(e.get("reference"), ref)
                         and not _legible(e)})
    ok = fuente.get("freshness") == VIGENTE and bool(vigentes) and not contra and not torcidos
    return ok, {"declared": fuente.get("freshness"),
                "observed": sorted({str(e.get("value")) for e in sobre}),
                "evidenceUsed": sorted(e["evidenceId"] for e in vigentes) if ok else [],
                "contradictedBy": sorted({e["evidenceId"] for e in contra} | set(torcidos))}


def _punto(p, cat):
    """(estado, salida) de un punto: PASS si su disposicion vale."""
    ev = _ev()
    disposicion = p.get("disposition")
    refs = _nfcs(p.get("evidenceRefs"))
    # 🔴 Sostiene un punto un item que dice algo del punto (`GUIDANCE_ITEM_EVIDENCE`): la foto de OWASP, la
    # frescura o el inventario no son evidencia de haber revisado nada (refutador, pase 1).
    usadas = [cat[r] for r in refs if r in cat and cat[r]["sourceType"] not in NO_SOSTIENEN_PUNTO
              and PUNTO in cat[r]["establishes"] and _legible(cat[r])]
    ilegibles = [r for r in refs if r not in cat or not _legible(cat[r])]
    hallazgos = _nfcs(p.get("findingIds"))
    # Un hallazgo que el catalogo no tiene, legible, no es un hallazgo: es un nombre.
    reales = [h for h in hallazgos if h in cat and HALLAZGO in cat[h]["establishes"] and _legible(cat[h])
              and cat[h]["sourceType"] not in NO_SOSTIENEN_PUNTO]
    razon = p.get("rationale")
    if disposicion == SIN_HALLAZGO:
        vale = bool(usadas)
    elif disposicion == CON_HALLAZGO:
        vale = bool(hallazgos) and len(reales) == len(hallazgos)
    elif disposicion == NO_APLICABLE:
        vale = isinstance(razon, str) and bool(razon.strip()) and bool(usadas)
    else:
        vale = False
    if ilegibles:
        # Lo que se cita y no se puede leer impide dar el punto por revisado.
        vale = False
    return (PASA if vale else PUNTO_ABIERTO), {
        "itemId": _texto(p.get("itemId")), "title": p.get("title"), "disposition": disposicion,
        "rationale": razon if isinstance(razon, str) else None,
        "evidenceUsed": sorted(e["evidenceId"] for e in usadas) if vale else [],
        "unreadable": [str(r) for r in ilegibles],
        # Solo un hallazgo real de un FINDING_PRESENT es un hallazgo: un nombre no llega al reporte.
        "findingIds": [str(h) for h in reales] if disposicion == CON_HALLAZGO else [],
        "unknownFindingIds": [str(h) for h in hallazgos if h not in reales or disposicion != CON_HALLAZGO],
        "state": PASA if vale else PUNTO_ABIERTO}


def evaluar_familia(f, cat, crudas=()):
    ev = _ev()
    familia = f.get("family")
    fuente = f.get("source") if isinstance(f.get("source"), dict) else {}
    fotos, esperados = _foto(familia, fuente, cat)
    salida = {"family": familia,
              "source": {"edition": fuente.get("edition"), "sourceRef": fuente.get("sourceRef"),
                         "resolvedAt": fuente.get("resolvedAt"),
                         "sourceFingerprint": fuente.get("sourceFingerprint"),
                         "snapshot": sorted(e["evidenceId"] for e in fotos)},
              "expectedItems": [str(i) for i in esperados or []], "items": [], "missingItems": [],
              "unexpectedItems": [], "duplicatedItems": []}
    if fuente.get("freshness") == NO_DISPONIBLE_FUENTE or not fotos or esperados is None:
        salida["freshness"] = {"declared": fuente.get("freshness")}
        salida["state"] = SIN_FUENTE
        return salida
    vigente, salida["freshness"] = _frescura(fuente, cat, crudas)
    puntos = [p for p in f.get("items") or [] if isinstance(p, dict)]
    ids = [_texto(p.get("itemId")) for p in puntos]
    salida["missingItems"] = [str(i) for i in esperados if i not in ids]
    salida["unexpectedItems"] = sorted({str(i) for i in ids if i not in esperados})
    salida["duplicatedItems"] = sorted({str(i) for i in ids if ids.count(i) > 1})
    estados = []
    for p in puntos:
        estado, detalle = _punto(p, cat)
        estados.append(estado)
        salida["items"].append(detalle)
    salida["items"] = ev.ordenadas(salida["items"])
    if not vigente:
        salida["state"] = SIN_FRESCURA
    elif salida["missingItems"] or salida["unexpectedItems"] or salida["duplicatedItems"]:
        salida["state"] = INCOMPLETA
    elif PUNTO_ABIERTO in estados:
        salida["state"] = PUNTO_ABIERTO
    else:
        salida["state"] = PASA
    return salida


# -- la evaluacion -----------------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de la review de Vu10.

    `caso`:

        {"registry": {...},     # el registro de la review; opcional
         "evidence": [...]}     # el catalogo, cerrado
    """
    ev = _ev()
    entrada = caso if isinstance(caso, dict) else {}
    d = derivar(entrada, desde)
    valor = _combinar(d["value"], senal)
    salida = {"review": REVIEW, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE, "source": dict(TRAZA),
              "signal": SENAL, "signalValue": valor, "assets": [], "families": [], "applicableFamilies": [],
              "omittedFamilies": [], "findings": [], "issues": []}
    if d["problem"]:
        salida["issues"].append(d["problem"])
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos: %s" % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada: %s" % ", ".join(d["malformed"]))
    salida["issues"].sort()
    if valor == _senales.SIN_RESOLVER:
        return _cerrar(salida, SIN_APLICABILIDAD, "no consta si hay activos web, API o mobile gobernados")
    if valor == _senales.FALSA:
        return _cerrar(salida, NO_APLICA, "una evidencia autoritativa establece que no hay activos web, API ni mobile")
    if d["problem"]:
        # Un punto sin disposicion, o cualquier cosa que el schema rechaza: la review no esta hecha.
        return _cerrar(salida, REVISION_INCOMPLETA, d["problem"])
    familias, salida["assets"], activos_abiertos, salida["coverage"] = _activos(d)
    salida["applicableFamilies"] = familias
    declaradas = [f for f in d["registry"].get("families") or [] if isinstance(f, dict)]
    nombres = [f.get("family") for f in declaradas]
    salida["families"] = ev.ordenadas(evaluar_familia(f, d["catalog"], d["raw"]) for f in declaradas)
    salida["omittedFamilies"] = [f for f in familias if f not in nombres]
    hallazgos = sorted({h for f in salida["families"] for p in f["items"] for h in p["findingIds"]})
    salida["findings"] = hallazgos
    estados = [f["state"] for f in salida["families"] if f["family"] in familias]
    repetidas = len(set(nombres)) != len(nombres)
    if declaradas and salida["omittedFamilies"]:
        # 🔴 La review esta hecha y una familia aplicable no esta: la guia se ignoro.
        return _cerrar(salida, FALLA, "la review omite una familia OWASP aplicable: %s"
                       % ", ".join(salida["omittedFamilies"]), estados)
    abiertos = list(estados)
    if activos_abiertos:
        abiertos.append(SIN_ACTIVOS)
    if not declaradas:
        abiertos.append(REVISION_INCOMPLETA)
    if repetidas:
        abiertos.append(INCOMPLETA)
    if PUNTO_ABIERTO in abiertos:
        abiertos.append(REVISION_INCOMPLETA)
    for e in ORDEN_DE_LO_ABIERTO:
        if e in abiertos:
            return _cerrar(salida, e, "hay algo material de la review sin resolver", estados)
    if d["repeated"] or d["malformed"]:
        return _cerrar(salida, REVISION_INCOMPLETA, "hay evidencia ilegible en el catalogo", estados)
    return _cerrar(salida, PASA, "", estados)


def _cerrar(salida, estado, motivo, estados=()):
    salida["state"] = estado
    salida["states"] = sorted(({estado} | set(estados)) - {PASA})
    salida["reason"] = motivo
    return _ev().depurar(salida)


def aprueba(resultado):
    return (resultado or {}).get("state") == PASA


def evidencia_usada(resultado):
    r = resultado if isinstance(resultado, dict) else {}
    ids = set()
    for a in r.get("assets") or []:
        ids.update(a.get("evidenceUsed") or [])
    for f in r.get("families") or []:
        ids.update((f.get("source") or {}).get("snapshot") or [])
        ids.update((f.get("freshness") or {}).get("evidenceUsed") or [])
        for p in f.get("items") or []:
            ids.update(p.get("evidenceUsed") or [])
    return sorted(i for i in ids if isinstance(i, str))


# -- hacia la frescura, seguridad, el reporte y la refutacion -----------------------------------------

def evidencia_de_frescura(sid, entrada, referencia, edicion):
    """El item `SOURCE_FRESHNESS` de una entrada de `.claude/harness.fuentes.json`.

    El estado es el que resolvio `frescura.py`, tal cual: este modulo no lo recalcula."""
    e = entrada if isinstance(entrada, dict) else {}
    estado = e.get("state") if isinstance(e.get("state"), str) else "FRESHNESS_UNVERIFIED"
    return {"evidenceId": "frescura:%s" % sid, "sourceType": "TRUSTED_KNOWLEDGE_REGISTRY",
            "reference": referencia, "establishes": [FRESCURA], "value": estado, "version": edicion}


def para_seguridad(resultado):
    """(evidencia, senales) para `seguridad.resultado("Vu10", ...)`: la policy y la review llevan el
    estado de la review. Un resultado que no dice ser de esta review no se traduce."""
    r = resultado if isinstance(resultado, dict) else {}
    if r.get("review") != REVIEW or r.get("state") not in ESTADOS:
        return {}, {}
    evidencia = evidencia_usada(r) or (["review:%s" % REVIEW] if r["state"] in RESUELTAS + (FALLA,) else [])
    doc = {"controlResults": {c: {"result": r["state"], "evidence": evidencia} for c in (POLICY, REVIEW)}}
    valor = r.get("signalValue")
    senales = ({SENAL: True} if valor == _senales.VERDADERA
               else {SENAL: False} if valor == _senales.FALSA and r["state"] == NO_APLICA else {})
    return _ev().depurar(doc), senales


def hallazgos_para_reporte(resultado, caso, existentes, task_id, alcance, cuando=None):
    """Los eventos de hallazgo por el camino de siempre (`desde_hallazgo`).

    Un hallazgo que ya esta en el libro (`existentes`) se referencia y no se crea. Uno que citan dos
    puntos sale una vez. La severidad y la confianza son las del hallazgo."""
    from reporte_seguridad import productores
    r = resultado if isinstance(resultado, dict) else {}
    cat = catalogo(caso if isinstance(caso, dict) else {})[0]
    ya = {_texto(x) for x in existentes or []}
    eventos = []
    for fid in r.get("findings") or []:
        if _texto(fid) in ya:
            continue
        e = cat.get(_texto(fid)) if _texto(fid) in cat and HALLAZGO in cat[_texto(fid)]["establishes"] else {}
        hallazgo = {"findingId": fid, "rule": CLAVE, "title": e.get("title"), "severity": e.get("severity"),
                    "confidence": e.get("confidence"), "blocking": e.get("blocking") is True,
                    "evidence": [fid]}
        eventos.extend(productores.desde_hallazgo(hallazgo, "CREATED", task_id, alcance, cuando=cuando))
    return eventos


def alcance_de_punto(familia, punto, activo, paths):
    """El alcance de una unidad de refutacion para UN punto de UN activo, o `None`.

    Rechaza un alcance vacio o del repositorio entero: nunca se refuta el repo."""
    rutas = [p for p in (paths or []) if isinstance(p, str) and p.strip()]
    enteros = {".", "./", "/", "*", "**", "**/*", ""}
    if (familia not in FAMILIAS or not isinstance(punto, str) or not punto.strip()
            or not isinstance(activo, str) or not activo.strip() or not rutas
            or any(p.strip() in enteros for p in rutas)):
        return None
    # El id sigue el patron de `scope.json` (`^[A-Za-z0-9][A-Za-z0-9._-]*$`): un punto como `X:2031` o un
    # activo con espacios se escriben con `-`.
    ident = ".".join(re.sub(r"[^A-Za-z0-9._-]", "-", _ev().nfc(x).strip()) for x in (familia, punto, activo))
    return [{"scopeId": "owasp." + ident, "source": "workUnitFiles", "paths": sorted(set(rutas))}]
