"""Check normativo: ningun dato sensible viaja en texto plano, salto por salto.

    source: ES0902 / 6.2 / 6 / Vu2

    "Todo dato sensible no puede ser enviado en texto plano."

🔴 **Esto no es un check del hook.** Es un control normativo: no corre en `PreToolUse` y no tiene
presupuesto de latencia.

🔴 **Sensible lo dice una autoridad, no un nombre de campo.** El estandar no define que es un dato
sensible y este modulo tampoco: no tiene ninguna lista de campos ni de categorias. Una clase cuenta
como sensible, o como no sensible, cuando el registro lo declara y una fuente autoritativa citada
dice lo mismo. Sin eso, `SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`.

🔴 **Salto por salto.** Un borde con TLS no protege un salto interno en claro. Cada salto de un
camino que lleva una clase sensible se evalua solo, y la cadena tiene que estar entera.

🔴 **Codificar no es cifrar, y un hash tampoco.** Base64, URL, hex, compresion, serializacion, un
JWT solo firmado y la ofuscacion viajan legibles.

🔴 **`https` es evidencia, no prueba.** La forma de la URL y el codigo fuente solo no prueban la
proteccion; la validacion de certificado o de hostname apagada la impide.

🔴 **Nada criptografico se inventa.** Ni version de TLS, ni suites, ni tamano de clave, ni mTLS.

🔴 **No se prueba nada ni se guarda nada.** El modulo no abre conexiones ni escribe archivos. Una
prueba cuenta si fue sintetica, autorizada y sin captura del payload. Y nada con forma de
credencial sale en el resultado, venga de donde venga.
"""
import io
import json
import os
import re
import sys
import unicodedata

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

import rutas                                        # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "sensitive-data-transport-protection"
POLICY = "sensitive-data-plaintext-transmission-prohibited"
TIPO = "CHECK"
REGLA = "Vu2"
CLAVE = "ES0902.Vu2"
SENAL = "sensitiveDataTransmissionPresent"

ARCHIVO = "sensitive-data-transmission.json"
SCHEMA = "sensitive-data-transmission.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": REGLA}
TEXTO_FUENTE = "Todo dato sensible no puede ser enviado en texto plano."

# -- los estados ----------------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
SIN_CLASIFICACION = "SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED"
SIN_COBERTURA = "TRANSMISSION_PATH_COVERAGE_UNRESOLVED"
SIN_PROTECCION = "TRANSPORT_PROTECTION_UNRESOLVED"
EN_CLARO = "PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED"
PRUEBA_INSEGURA = "SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, SIN_CLASIFICACION, SIN_COBERTURA,
           SIN_PROTECCION, EN_CLARO, PRUEBA_INSEGURA, SIN_OBJETIVO)

# Por salto.
PROTEGIDO = "PROTECTED"
PLANO = "PLAINTEXT"
NO_RESUELTO = "UNRESOLVED"
NO_MATERIAL = "NOT_MATERIAL_BOUNDARY"

# Por clase.
SENSIBLE = "SENSITIVE"
NO_SENSIBLE = "NOT_SENSITIVE"

# -- lo que establece una evidencia, y que clase de fuente lo sostiene ----------------

CLASIFICACION = "DATA_CLASSIFICATION"
SIN_TRANSMISION = "NO_SENSITIVE_TRANSMISSION"
CONFIDENCIALIDAD = "TRANSPORT_CONFIDENTIALITY"
# Un redirect o un downgrade que expone el payload es en claro, aunque el destino final cifre.
DEGRADACION = "REDIRECT_DOWNGRADE"
EXPONE = "EXPOSES_PAYLOAD"
FRONTERA = NO_MATERIAL

# 🔴 Las tablas son del harness, no del estandar, y por eso estan escritas.
AUTORIDADES_DE_CLASIFICACION = ("GCBA_DATA_CLASSIFICATION_POLICY", "ASI_POLICY",
                                "PROJECT_SECURITY_REQUIREMENT", "ARCHITECTURE_DOCUMENTATION",
                                "OFFICIAL_ASSESSMENT_FINDING", "PROJECT_CONTRACT",
                                "OTHER_AUTHORITATIVE_EVIDENCE")
PRUEBA = "AUTHORIZED_SYNTHETIC_TEST"
FUENTES_DE_TRANSPORTE = ("DEPLOYMENT_CONFIGURATION", "RUNTIME_TRANSPORT_CONFIGURATION",
                         "NETWORK_CONFIGURATION", "APPLICATION_CONFIGURATION",
                         "CONNECTION_METADATA", "ARCHITECTURE_DOCUMENTATION",
                         "OFFICIAL_ASSESSMENT_FINDING", PRUEBA, "OTHER_AUTHORITATIVE_EVIDENCE")
# El paquete pide "authoritative architecture evidence": arquitectura y nada mas.
AUTORIDADES_DE_FRONTERA = ("ARCHITECTURE_DOCUMENTATION",)
# Las que no sostienen nada, nombradas para que la salida pueda decir por que.
INSUFICIENTES = ("FIELD_NAME_PATTERN", "SECRET_SCANNER", "URL_SCHEME", "SOURCE_CODE",
                 "README_STATEMENT", "AGENT_STATEMENT", "SKILL_OUTPUT", "REPOSITORY_DEPENDENCY")

CONFIRMADA = "CONFIRMED"
NO_DISPONIBLE = "UNAVAILABLE"

# -- el transporte ---------------------------------------------------------------------

# 🔴 Los unicos transportes que este modulo reconoce como explicitamente sin cifrar. Otros quedan
# sin resolver: nombrarlos es empezar un catalogo de protocolos que el estandar no trae.
TRANSPORTES_EN_CLARO = ("http", "ws")
CIFRADO_DE_APLICACION = "APPLICATION_LEVEL_ENCRYPTION"
CODIFICACIONES = ("BASE64", "URL_ENCODING", "HEX", "HEX_ENCODING", "COMPRESSION", "SERIALIZATION",
                  "JWT_SIGNED", "SIGNED_JWT", "JWS", "OBFUSCATION")
HASHES = ("HASH", "HASHING")
APAGADO = "DISABLED"

# -- lo que no sale ---------------------------------------------------------------------

# 🔴 La forma de una credencial, con los dos arreglos que dejo Vu1: la clave termina en la palabra
# (`DB_PASSWORD=` si, `passwordPolicy:` no), un `:` o una `/` antes no la esconde
# (`app:password=`), y un ARN entero no es un secreto.
SECRETOS = tuple(re.compile(p) for p in (
    r"(?i)(?<![\w-])[\w-]*?(password|passwd|pwd|secret|token|api[_-]?key)[\"']?\s*[:=]\s*\S",
    r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}",
    r"://[^/\s:@]+:[^/\s@]+@",
    r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"))
# 🔴 Un ARN no exime el texto: se saca SOLO el prefijo que nombra un secreto de un gestor
# (`arn:aws:secretsmanager:<region>:<cuenta>:secret:`), y el resto se mira igual. `arn:password=`
# no es un ARN, y un ARN con `password=` adentro sigue siendo una credencial. (Refutador, pase 1:
# E-36.)
PREFIJO_DE_GESTOR = re.compile(r"arn:aws[\w-]*:secretsmanager:[a-z0-9-]+:[0-9]+:secret:")
REDACTADO = "[redactado]"


def es_secreto(texto):
    if not isinstance(texto, str):
        return False
    resto = PREFIJO_DE_GESTOR.sub("", texto)
    return any(p.search(resto) for p in SECRETOS)


def _depurar(dato):
    """🔴 La regla de salida, una sola: nada con forma de credencial sale, venga de donde venga."""
    if isinstance(dato, dict):
        return {k: _depurar(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [_depurar(v) for v in dato]
    return REDACTADO if es_secreto(dato) else dato


def _textos(dato):
    if isinstance(dato, dict):
        for k, v in dato.items():
            yield str(k)
            yield from _textos(v)
    elif isinstance(dato, list):
        for v in dato:
            yield from _textos(v)
    elif isinstance(dato, str):
        yield dato


def _n(texto):
    return unicodedata.normalize("NFC", texto) if isinstance(texto, str) else texto


def _igual(a, b):
    """🔴 La unica comparacion de ids del modulo, en NFC. Lo legible y lo ilegible se nombran con la
    misma regla: si no, un "no" legible pesa menos que uno mal formado. (Refutador, pase 2.)"""
    return _n(a) == _n(b)


def _en(ident, lista):
    return any(_igual(ident, x) for x in (lista or []))


def _menciona(dato, ident):
    """Si algun texto del dato ES el id. Igualdad, no subcadena: `ciudadano-v2` no es `ciudadano`,
    y un id con acentos o comillas se compara igual que cualquier otro."""
    buscado = unicodedata.normalize("NFC", ident) if isinstance(ident, str) else ident
    return any(unicodedata.normalize("NFC", t) == buscado for t in _textos(dato))


# -- el catalogo de evidencia -------------------------------------------------------------

TEXTO, LISTA, BOOLEANO = "text", "list-of-text", "bool"
# 🔴 Cerrado: un campo que no esta aca -un `payload`, un `sample`- deja el item mal formado. No hay
# donde guardar un valor sensible.
FORMA = {"evidenceId": TEXTO, "sourceType": TEXTO, "reference": TEXTO, "establishes": LISTA,
         "scope": TEXTO, "targets": LISTA, "hop": TEXTO, "value": TEXTO, "outcome": TEXTO,
         "syntheticData": BOOLEANO, "authorized": BOOLEANO, "payloadCaptured": BOOLEANO}
OBLIGATORIOS = ("evidenceId", "sourceType", "reference", "establishes", "scope", "targets")


def bien_formada(e):
    if not isinstance(e, dict) or set(e) - set(FORMA):
        return False
    for campo, forma in FORMA.items():
        valor = e.get(campo)
        if valor is None:
            if campo in OBLIGATORIOS:
                return False
            continue
        if forma == TEXTO and not isinstance(valor, str):
            return False
        if forma == LISTA and not (isinstance(valor, list)
                                   and all(isinstance(v, str) for v in valor)):
            return False
        if forma == BOOLEANO and not isinstance(valor, bool):
            return False
    return bool(e["reference"].strip())


def catalogo(caso):
    """(catalogo, crudas, repetidos, torcidas). Lo repetido o mal formado no cuenta."""
    crudas = (caso or {}).get("evidence")
    crudas = crudas if isinstance(crudas, list) else []
    ids = [e.get("evidenceId") for e in crudas
           if isinstance(e, dict) and isinstance(e.get("evidenceId"), str)]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    torcidas = sorted({str(e.get("evidenceId")) if isinstance(e, dict) else "malformed-evidence"
                       for e in crudas if not bien_formada(e)})
    sanas = {e["evidenceId"]: e for e in crudas
             if bien_formada(e) and e["evidenceId"] not in repetidos}
    return sanas, crudas, repetidos, torcidas


def _ilegibles_sobre(ident, catalogo_, crudas):
    """Los items que nombran `ident` y no se pueden leer: repetidos o mal formados."""
    salida = set()
    for e in crudas:
        legible = isinstance(e, dict) and catalogo_.get(e.get("evidenceId")) is e
        if not legible and _menciona(e, ident):
            salida.add(str(e.get("evidenceId")) if isinstance(e, dict) else "malformed-evidence")
    return sorted(salida)


def _lectura(e):
    """(cuenta, bloqueo). La misma compuerta para lo que dice que si y lo que dice que no."""
    if e.get("sourceType") == PRUEBA:
        if e.get("outcome") == NO_DISPONIBLE:
            return False, SIN_OBJETIVO
        if (e.get("syntheticData") is not True or e.get("authorized") is not True
                or e.get("payloadCaptured") is True):
            return False, PRUEBA_INSEGURA
        return e.get("outcome") == CONFIRMADA, None
    return e.get("outcome") in (None, CONFIRMADA), None


# -- el registro ---------------------------------------------------------------------------

def cargar(desde=None):
    """El registro del proyecto. Vacio si no esta: vacio es valido y no cubre nada."""
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "dataClasses": [], "paths": []}
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


def inventario(caso, desde=None):
    """(doc, problema). El del caso si viene; si no, el instalado."""
    declarado = (caso or {}).get("inventory")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return None, "el registro de transmision no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return None, "el registro de transmision no se pudo validar: falta su schema o el validador"
    if errores:
        # Los errores del validador repiten valores. Se dice cuantos, no cuales.
        return None, "el registro de transmision no valida contra su schema: %d errores" % len(errores)
    return doc, ""


# -- la clasificacion ------------------------------------------------------------------------

def _del_alcance(e, alcance):
    return isinstance(alcance, str) and bool(alcance.strip()) and _igual(e.get("scope"), alcance)


def clasificar(clase, catalogo_, crudas, alcance):
    """(estado, evidencia, motivo). SENSITIVE, NOT_SENSITIVE o UNRESOLVED, con autoridad."""
    cid = clase.get("dataClassId")
    declarado = clase.get("classification")
    citadas = clase.get("classificationEvidence") or []
    legibles = [e for e in catalogo_.values()
                if CLASIFICACION in e["establishes"] and _en(cid, e["targets"])
                and e["sourceType"] in AUTORIDADES_DE_CLASIFICACION and _del_alcance(e, alcance)
                and e.get("value") in (SENSIBLE, NO_SENSIBLE) and _lectura(e)[0]]
    a_favor = sorted(e["evidenceId"] for e in legibles
                     if e["evidenceId"] in citadas and e.get("value") == declarado)
    en_contra = sorted(e["evidenceId"] for e in legibles if e.get("value") != declarado)
    ilegibles = sorted(set([r for r in citadas if r not in catalogo_])
                       | set(_ilegibles_sobre(cid, catalogo_, crudas)))
    if declarado not in (SENSIBLE, NO_SENSIBLE):
        return NO_RESUELTO, [], "la clase no esta clasificada"
    if en_contra:
        return NO_RESUELTO, [], "hay evidencia autoritativa que dice lo contrario: %s" % ", ".join(
            en_contra)
    if ilegibles:
        return NO_RESUELTO, [], "hay evidencia ilegible sobre la clase: %s" % ", ".join(ilegibles)
    if not a_favor:
        return NO_RESUELTO, [], ("ninguna fuente autoritativa citada clasifica la clase; un nombre "
                                 "de campo no la clasifica")
    return declarado, a_favor, ""


# -- la senal ----------------------------------------------------------------------------------

def _texto_de(valor):
    return valor if isinstance(valor, str) else ""


def derivar(caso, desde=None):
    """La senal derivada del registro, con cada clase, cada camino y la cobertura."""
    entrada = caso if isinstance(caso, dict) else {}
    alcance = entrada.get("scope")
    doc, problema = inventario(entrada, desde)
    cat, crudas, repetidos, torcidas = catalogo(entrada)
    clases_doc = list((doc or {}).get("dataClasses") or [])
    caminos_doc = list((doc or {}).get("paths") or [])

    ids_clase = [c.get("dataClassId") for c in clases_doc]
    ids_camino = [p.get("pathId") for p in caminos_doc]
    clases = {}
    for c in clases_doc:
        estado, usada, motivo = clasificar(c, cat, crudas, alcance)
        if ids_clase.count(c.get("dataClassId")) > 1:
            estado, usada, motivo = NO_RESUELTO, [], "el id de la clase esta repetido"
        clases[_n(c.get("dataClassId"))] = {"dataClassId": c.get("dataClassId"),
                                        "classification": estado, "evidenceUsed": usada,
                                        "reason": motivo}

    detectados = entrada.get("detectedPaths")
    detectados_torcidos = detectados is not None and not (
        isinstance(detectados, list) and all(isinstance(d, str) and d for d in detectados))
    vistos = sorted(set(detectados or [])) if not detectados_torcidos else []
    sin_saltos, cortados, sin_clase, ajenos, ambiguos = [], [], [], [], []
    for p in caminos_doc:
        pid = str(p.get("pathId"))
        saltos = p.get("hops") or []
        if not saltos:
            sin_saltos.append(pid)
        if any(saltos[i].get("to") != saltos[i + 1].get("from") for i in range(len(saltos) - 1)):
            cortados.append(pid)
        # Dos saltos del mismo camino con el mismo `from->to` no se distinguen: una evidencia
        # valdria para los dos.
        hids = ["%s->%s" % (x.get("from"), x.get("to")) for x in saltos]
        if len(set(hids)) != len(hids):
            ambiguos.append(pid)
        if any(_n(r) not in clases for r in p.get("dataClassRefs") or []):
            sin_clase.append(pid)
        if p.get("scope") is not None and p.get("scope") != alcance:
            ajenos.append(pid)
    cobertura = {"inventoried": sorted({str(i) for i in ids_camino}), "detected": vistos,
                 "missing": sorted(set(vistos) - {str(i) for i in ids_camino}),
                 "duplicatedPaths": sorted({str(i) for i in ids_camino if ids_camino.count(i) > 1}),
                 "duplicatedClasses": sorted({str(i) for i in ids_clase
                                              if ids_clase.count(i) > 1}),
                 "detectedMalformed": detectados_torcidos, "withoutHops": sorted(sin_saltos),
                 "brokenChain": sorted(cortados), "ambiguousHops": sorted(ambiguos),
                 "undefinedClassRefs": sorted(sin_clase),
                 "outOfScope": sorted(ajenos)}
    completa = not any(v for k, v in cobertura.items() if k not in ("inventoried", "detected"))

    def de_camino(p):
        return [clases[_n(r)]["classification"] for r in p.get("dataClassRefs") or []
                if _n(r) in clases]

    lleva_sensible = [p for p in caminos_doc if (p.get("hops") or [])
                      and SENSIBLE in de_camino(p)]
    todas = [c["classification"] for c in clases.values()]
    sin_transmision = [e for e in cat.values()
                       if SIN_TRANSMISION in e["establishes"] and _del_alcance(e, alcance)
                       and _en(alcance, e["targets"]) and e["sourceType"] in AUTORIDADES_DE_CLASIFICACION
                       and _lectura(e)[0]]
    motivos = []
    if problema:
        valor = _senales.SIN_RESOLVER
    elif lleva_sensible:
        valor = _senales.VERDADERA
    elif (completa and not (repetidos or torcidas) and NO_RESUELTO not in todas
          and SENSIBLE not in todas
          and ((caminos_doc and all(de_camino(p) for p in caminos_doc)) or
               (not caminos_doc and sin_transmision))):
        valor = _senales.FALSA
    else:
        valor = _senales.SIN_RESOLVER
    if valor == _senales.SIN_RESOLVER and not problema:
        if NO_RESUELTO in todas:
            motivos.append(SIN_CLASIFICACION)
        if not completa or not caminos_doc:
            motivos.append(SIN_COBERTURA)
    return {"value": valor, "reasons": sorted(set(motivos)), "problem": problema,
            "classes": clases, "paths": caminos_doc, "coverage": cobertura, "complete": completa,
            "catalog": cat, "raw": crudas, "repeated": repetidos, "malformed": torcidas,
            "scope": alcance}


def senal(caso, desde=None):
    """`sensitiveDataTransmissionPresent` como documento de senal, resuelto por `senales`."""
    d = derivar(caso, desde)
    evidencia = []
    if d["value"] in (_senales.VERDADERA, _senales.FALSA):
        for p in sorted(d["paths"], key=lambda x: str(x.get("pathId"))):
            evidencia.append({"evidenceId": "path:%s" % p.get("pathId"),
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "%s#%s" % (ARCHIVO, p.get("pathId")),
                              "claim": "el camino `%s` (alcance %s) lleva %s por %s" % (
                                  p.get("pathId"), p.get("scope") or d["scope"], ", ".join(sorted(
                                      "%s=%s [%s]" % (
                                          r, d["classes"].get(_n(r), {}).get("classification"),
                                          ", ".join(d["classes"].get(_n(r), {}).get("evidenceUsed")
                                                    or []) or "-")
                                      for r in p.get("dataClassRefs") or [])),
                                  " | ".join("%s->%s" % (x.get("from"), x.get("to"))
                                             for x in p.get("hops") or []) or "-"),
                              "supports": d["value"]})
        if not d["paths"]:
            evidencia.append({"evidenceId": "scope:%s" % d["scope"],
                              "sourceType": "REPOSITORY_CONFIGURATION",
                              "reference": "%s#scope" % ARCHIVO,
                              "claim": "una fuente autoritativa establece que el alcance no "
                                       "transmite datos sensibles", "supports": d["value"]})
    doc = _senales.producir(SENAL, evidencia, {"type": "DETERMINISTIC"}, d["value"], desde)
    doc["reasons"] = d["reasons"]
    return _depurar(doc)


def _valor(externo):
    if isinstance(externo, dict):
        return externo.get("value") or _senales.SIN_RESOLVER
    if isinstance(externo, bool):
        return _senales.VERDADERA if externo else _senales.FALSA
    return externo if externo in (_senales.VERDADERA, _senales.FALSA) else _senales.SIN_RESOLVER


def _combinar(derivado, externo):
    if externo is None:
        return derivado
    valor = _valor(externo)
    if valor == derivado:
        return valor
    if valor == _senales.VERDADERA and derivado == _senales.SIN_RESOLVER:
        return valor
    return _senales.SIN_RESOLVER


# -- un salto --------------------------------------------------------------------------------

def _normal(texto):
    return re.sub(r"[\s-]+", "_", _texto_de(texto).strip()).upper()


def _esquema(transporte):
    t = _texto_de(transporte).strip().lower()
    return t.split("://", 1)[0] if "://" in t else t


def evaluar_salto(salto, camino, cat, alcance):
    """El estado de un salto: PROTECTED, PLAINTEXT, NOT_MATERIAL_BOUNDARY o UNRESOLVED."""
    pid = camino.get("pathId")
    hid = "%s->%s" % (salto.get("from"), salto.get("to"))
    citados = set(salto.get("evidence") or []) | set(camino.get("evidence") or [])
    mecanismo = _normal(salto.get("protectionMechanism"))
    salida = {"from": salto.get("from"), "to": salto.get("to"), "transport": salto.get("transport"),
              "protectionMechanism": salto.get("protectionMechanism"),
              "declared": salto.get("protectionStatus"), "evidenceUsed": [],
              "contradictedBy": [], "blockedBy": [], "issues": []}

    def sobre_el_salto(e, fuentes):
        return (_en(pid, e["targets"]) and _igual(e.get("hop"), hid) and e["sourceType"] in fuentes
                and _del_alcance(e, alcance))

    frontera = sorted(e["evidenceId"] for e in cat.values()
                      if FRONTERA in e["establishes"] and e["evidenceId"] in citados
                      and sobre_el_salto(e, AUTORIDADES_DE_FRONTERA) and _lectura(e)[0])
    if frontera:
        salida["evidenceUsed"] = frontera
        return _con(salida, NO_MATERIAL, "una fuente autoritativa dice que este salto no es una "
                                         "frontera de transmision")

    protegen, exponen, dudosas = [], [], []
    for e in sorted(cat.values(), key=lambda x: x["evidenceId"]):
        if not sobre_el_salto(e, FUENTES_DE_TRANSPORTE):
            continue
        if CONFIDENCIALIDAD in e["establishes"] and e.get("value") in (PROTEGIDO, PLANO):
            dice_que_no = e["value"] == PLANO
        elif DEGRADACION in e["establishes"] and e.get("value") == EXPONE:
            dice_que_no = True
        else:
            continue
        cuenta, bloqueo = _lectura(e)
        if bloqueo:
            salida["blockedBy"].append(bloqueo)
            continue
        if not cuenta:
            # 🔴 Un "no" que no se confirmo -`outcome: PENDING`- no se descarta: impide el PASS.
            salida["issues"].append("`%s` no esta confirmada" % e["evidenceId"])
            if dice_que_no:
                dudosas.append(e["evidenceId"])
            continue
        (exponen if dice_que_no else protegen).append(e["evidenceId"])
    salida["blockedBy"] = sorted(set(salida["blockedBy"]))
    exponen_citadas = [i for i in exponen if i in citados]
    protegen_citadas = [i for i in protegen if i in citados]
    declarado = salto.get("protectionStatus")

    # En claro es un hecho: declarado, por el transporte, o por evidencia citada.
    if exponen_citadas:
        salida["evidenceUsed"] = exponen_citadas
        return _con(salida, PLANO, "una evidencia citada establece que el salto va en claro")
    if declarado == PLANO:
        if protegen:
            salida["contradictedBy"] = protegen
            return _con(salida, NO_RESUELTO, "el registro dice en claro y una evidencia dice "
                                             "protegido; no se elige")
        return _con(salida, PLANO, "el registro declara el salto en claro")
    if _esquema(salto.get("transport")) in TRANSPORTES_EN_CLARO:
        if not (mecanismo == CIFRADO_DE_APLICACION and protegen_citadas):
            return _con(salida, PLANO, "el transporte `%s` no cifra, y no hay cifrado de "
                                       "aplicacion con evidencia" % _esquema(salto.get("transport")))
    if mecanismo in CODIFICACIONES:
        return _con(salida, NO_RESUELTO, "`%s` es una codificacion, no un cifrado" % mecanismo)
    if mecanismo in HASHES:
        return _con(salida, NO_RESUELTO, "un hash no es cifrar el transporte; hay que mirar el "
                                         "valor que viaja")
    for campo in ("certificateValidation", "hostnameVerification"):
        if salto.get(campo) == APAGADO:
            return _con(salida, NO_RESUELTO, "`%s` esta apagada: no se puede decir que el salto "
                                             "este protegido" % campo)
    if (declarado == PROTEGIDO and protegen_citadas and not exponen and not dudosas
            and not salida["blockedBy"]):
        salida["evidenceUsed"] = protegen_citadas
        return _con(salida, PROTEGIDO, "")
    if exponen or dudosas:
        salida["contradictedBy"] = sorted(exponen + dudosas)
    return _con(salida, NO_RESUELTO, "no consta que el salto este protegido; `https`, el codigo "
                                     "fuente o lo que declara el registro no alcanzan")


def _con(salida, estado, motivo):
    salida["state"] = estado
    salida["reason"] = motivo
    return salida


def _estado_de_salto(s):
    if s["state"] != NO_RESUELTO:
        return None
    if PRUEBA_INSEGURA in s["blockedBy"]:
        return PRUEBA_INSEGURA
    if SIN_OBJETIVO in s["blockedBy"]:
        return SIN_OBJETIVO
    return SIN_PROTECCION


# -- un camino ---------------------------------------------------------------------------------

def evaluar_camino(camino, d):
    pid = camino.get("pathId")
    refs = sorted(r for r in camino.get("dataClassRefs") or [] if isinstance(r, str))
    clases = [{"dataClassId": r, "classification": d["classes"].get(_n(r), {}).get("classification")}
              for r in refs]
    estados = [c["classification"] for c in clases]
    salida = {"pathId": pid, "scope": camino.get("scope"), "dataClasses": clases,
              "evaluated": SENSIBLE in estados or NO_RESUELTO in estados or None in estados,
              "hops": [], "issues": []}
    if not salida["evaluated"]:
        return _cierre(salida, NO_APLICA, [], "el camino no lleva datos sensibles, con autoridad")
    salida["hops"] = [evaluar_salto(s, camino, d["catalog"], d["scope"])
                      for s in camino.get("hops") or []]
    citados = set(camino.get("evidence") or []) | {r for s in camino.get("hops") or []
                                                   for r in s.get("evidence") or []}
    # 🔴 Un "no" sobre el camino que no dice de que salto habla -sin `hop`, o con uno que el camino
    # no tiene- o que no dice que valor establece, tampoco se descarta: bloquea el camino.
    saltos_propios = ["%s->%s" % (s.get("from"), s.get("to")) for s in camino.get("hops") or []]
    sueltas = {e["evidenceId"] for e in d["catalog"].values()
               if (CONFIDENCIALIDAD in e["establishes"] or DEGRADACION in e["establishes"])
               and _en(pid, e["targets"]) and _del_alcance(e, d["scope"])
               and (not _en(e.get("hop"), saltos_propios)
                    or e.get("value") not in (PROTEGIDO, PLANO, EXPONE))}
    ilegibles = sorted(set(r for r in citados if r not in d["catalog"])
                       | set(_ilegibles_sobre(pid, d["catalog"], d["raw"])) | sueltas)
    planos = ["%s->%s" % (s["from"], s["to"]) for s in salida["hops"] if s["state"] == PLANO]
    if planos and SENSIBLE in estados:
        return _cierre(salida, FALLA, [EN_CLARO],
                       "un dato sensible viaja en claro en: %s" % ", ".join(planos))
    if ilegibles:
        salida["issues"].append("hay evidencia ilegible sobre el camino: %s" % ", ".join(ilegibles))
        return _cierre(salida, SIN_PROTECCION, [SIN_PROTECCION],
                       "hay evidencia ilegible sobre el camino, y esa podia ser la que decia que va "
                       "en claro")
    if SENSIBLE not in estados:
        return _cierre(salida, SIN_CLASIFICACION, [SIN_CLASIFICACION],
                       "no consta si lo que viaja es sensible")
    if NO_RESUELTO in estados or None in estados:
        return _cierre(salida, SIN_CLASIFICACION, [SIN_CLASIFICACION],
                       "el camino lleva una clase sin clasificar")
    abiertos = sorted({e for e in (_estado_de_salto(s) for s in salida["hops"]) if e})
    if not abiertos:
        return _cierre(salida, PASA, [], "")
    return _cierre(salida, abiertos[0] if len(abiertos) == 1 else SIN_PROTECCION, abiertos,
                   "saltos sin resolver: %s" % ", ".join(
                       "%s->%s" % (s["from"], s["to"]) for s in salida["hops"]
                       if s["state"] == NO_RESUELTO))


def _cierre(salida, estado, estados, motivo):
    salida["state"] = estado
    salida["states"] = sorted(set(estados))
    salida["reason"] = motivo
    return salida


# -- la evaluacion -----------------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de Vu2 para un proyecto, camino por camino y salto por salto.

    `caso`:

        {"scope": "...",                 # el alcance; la evidencia de otro no cuenta
         "inventory": {...},             # opcional: reemplaza el registro instalado
         "evidence": [...],              # el catalogo, cerrado
         "detectedPaths": [...]}         # lo que otra fuente vio

    🔴 Para el mismo caso devuelve siempre lo mismo, en cualquier orden que venga todo.
    """
    salida = {"control": CONTROL, "policy": POLICY, "rule": REGLA, "ruleKey": CLAVE,
              "source": dict(TRAZA), "sourceText": TEXTO_FUENTE, "signal": SENAL,
              "dataClasses": [], "paths": [], "issues": [], "coverage": {}}
    d = derivar(caso, desde)
    valor = _combinar(d["value"], senal)
    salida["signalValue"] = valor
    salida["coverage"] = d["coverage"]
    salida["dataClasses"] = sorted(d["classes"].values(),
                                   key=lambda c: json.dumps(c, sort_keys=True, default=str))
    if d["repeated"]:
        salida["issues"].append("ids de evidencia repetidos, que no cuentan: %s"
                                % ", ".join(d["repeated"]))
    if d["malformed"]:
        salida["issues"].append("evidencia mal formada, que no cuenta: %s"
                                % ", ".join(d["malformed"]))
    if d["problem"]:
        salida["issues"].append(d["problem"])
    salida["issues"].sort()
    if valor == _senales.SIN_RESOLVER:
        return _cerrar(salida, SIN_APLICABILIDAD, d["reasons"],
                       "no consta si viaja un dato sensible, y lo que no se sabe no es que no "
                       "aplica")
    if valor == _senales.FALSA:
        return _cerrar(salida, NO_APLICA, [], "no viajan datos sensibles en el alcance")
    if d["problem"]:
        return _cerrar(salida, SIN_COBERTURA, [], d["problem"])

    salida["paths"] = sorted((evaluar_camino(p, d) for p in d["paths"]),
                             key=lambda r: (str(r.get("pathId")),
                                            json.dumps(r, sort_keys=True, default=str)))
    estados = [r["state"] for r in salida["paths"]]
    evaluados = [r for r in salida["paths"] if r["state"] != NO_APLICA]
    if FALLA in estados:
        return _cerrar(salida, FALLA, [], "un dato sensible viaja en claro; lo que esta protegido "
                                          "no lo tapa")
    if not d["complete"] or not evaluados:
        return _cerrar(salida, SIN_COBERTURA, [], "no constan todos los caminos ni sus saltos")
    if SIN_CLASIFICACION in estados:
        return _cerrar(salida, SIN_CLASIFICACION, [], "hay caminos con clases sin clasificar")
    abiertos = sorted({e for e in estados if e not in (PASA, NO_APLICA)})
    if not abiertos:
        return _cerrar(salida, PASA, [], "")
    return _cerrar(salida, abiertos[0] if len(abiertos) == 1 else SIN_PROTECCION, [],
                   "caminos sin resolver: %s" % ", ".join(
                       "%s (%s)" % (r["pathId"], r["state"]) for r in salida["paths"]
                       if r["state"] not in (PASA, NO_APLICA)))


def _cerrar(salida, estado, extra, motivo):
    salida["state"] = estado
    todos = set(extra) | ({estado} if estado != PASA else set())
    for r in salida["paths"]:
        todos.update(r.get("states") or [])
    salida["states"] = sorted(todos)
    salida["reason"] = motivo
    return _depurar(salida)


def aprueba(resultado):
    """El unico estado que aprueba."""
    return (resultado or {}).get("state") == PASA
