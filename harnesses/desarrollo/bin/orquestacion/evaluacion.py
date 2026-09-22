"""La evaluacion de seguridad de ES0902: en que estado esta, y quien puede moverla.

ES0902 §4 separa dos actividades y el harness solo hace una:

    1. el sistema automatizado          esto es el harness
    2. el circuito interno de DGSEI     esto NO es el harness

🔴 **El harness no fabrica una aprobacion de seguridad.** Puede decir que su revision interna
termino, que el paquete esta listo para pedir, que el umbral de G2 da, que hay que reenviar. No
puede decir `APPROVED`. Y la guarda no es una convencion: un estado oficial exige **procedencia
externa declarada con evidencia**, y un productor interno no la tiene por construccion. Una
lista de estados prohibidos por productor se desactualiza en silencio el dia que aparece un
productor nuevo, y el productor nuevo queda permitido.

🔴 **Controles en PASS no es una evaluacion aprobada.** Es ES0902 G1 y es la razon por la que
`estado_oficial` no mira ningun resultado de control: no hay agregacion de PASS que lo mueva.

🔴 **El umbral de G2 es un calculo, y no es una aprobacion.** Se calcula solo si las
severidades del escaner estan mapeadas de forma autoritativa a las categorias de riesgo de
ES0902; sin ese mapeo no se calcula, y satisfecho el umbral el estado oficial no se mueve.

🔴 **La union, no el conjunto mas chico.** Un sistema que es aplicacion web y servicio web
exige los entregables de los dos. Elegir el mas chico es el sesgo que deja la preparacion mas
corta y no deja rastro.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402
from . import seguridad                          # noqa: E402

ARCHIVO_DE_ENTREGABLES = "es0902-security-deliverables.json"
SCHEMA_DE_ENTREGABLES = "es0902-security-deliverables.schema.json"

# -- el flujo ------------------------------------------------------------------

NO_EMPEZADA = "NOT_STARTED"
EVALUACION_INTERNA = "INTERNAL_ASSESSMENT"
LISTO_PARA_PEDIR = "READY_TO_REQUEST"
PEDIDA = "REQUESTED"
EN_EVALUACION = "IN_ASSESSMENT"
HALLAZGOS_RECIBIDOS = "FINDINGS_RECEIVED"
REMEDIACION = "REMEDIATION"
LISTO_PARA_REENVIAR = "READY_TO_RESUBMIT"
REENVIADA = "RESUBMITTED"
APROBADA = "APPROVED"
RECHAZADA = "REJECTED"
SIN_RESOLVER = seguridad.ESTADO_OFICIAL_SIN_RESOLVER

ESTADOS = (NO_EMPEZADA, EVALUACION_INTERNA, LISTO_PARA_PEDIR, PEDIDA, EN_EVALUACION,
           HALLAZGOS_RECIBIDOS, REMEDIACION, LISTO_PARA_REENVIAR, REENVIADA, APROBADA,
           RECHAZADA, SIN_RESOLVER)

# Los que son del harness y los que solo pueden llegar con evidencia externa. La particion es
# del documento de flujo provisto, no una interpretacion de aca.
ESTADOS_DEL_HARNESS = (NO_EMPEZADA, EVALUACION_INTERNA, LISTO_PARA_PEDIR, HALLAZGOS_RECIBIDOS,
                       REMEDIACION, LISTO_PARA_REENVIAR)
ESTADOS_OFICIALES = (PEDIDA, EN_EVALUACION, REENVIADA, APROBADA, RECHAZADA)

# Lo que un productor interno si puede declarar. `INTERNAL_REVIEW_COMPLETE` y
# `G2_THRESHOLD_SATISFIED` no son estados del flujo: son resultados internos, y por eso viven
# en su propia lista. Confundirlos con el flujo es como se fabrica una aprobacion.
REVISION_INTERNA_COMPLETA = "INTERNAL_REVIEW_COMPLETE"
UMBRAL_SATISFECHO = "G2_THRESHOLD_SATISFIED"
RESULTADOS_INTERNOS = (REVISION_INTERNA_COMPLETA, LISTO_PARA_PEDIR, LISTO_PARA_REENVIAR,
                       UMBRAL_SATISFECHO)

# -- quien produce que ---------------------------------------------------------

PRODUCTORES_INTERNOS = ("AUTOMATED_SCAN", "INTERNAL_SECURITY_REVIEW", "HARNESS_CHECK",
                        "HARNESS_THRESHOLD_CALCULATION", "DEV_SECURITY_AGENT")
PRODUCTORES_EXTERNOS = ("GCBA_DGSEI", "GCBA_SECURITY_AUTHORITY", "ASI")

PRODUCTOR_INTERNO = "SECURITY_INTERNAL_PRODUCER_CANNOT_SET_OFFICIAL_STATE"
ESTADO_DESCONOCIDO = "SECURITY_ASSESSMENT_STATE_UNKNOWN"

# -- C2 ------------------------------------------------------------------------

AMBIENTE_DE_HOMOLOGACION = "QA"
C2_FUERA_DE_QA = "SECURITY_APPROVAL_OUTSIDE_QA"

# -- G2 ------------------------------------------------------------------------

# 🔴 ES0902 nombra `LOW` y "por encima de LOW". Las bandas superiores NO se enumeran aca: el
# umbral no depende de cual sea, solo de que no sea LOW, y escribir una escala que el estandar
# no da la vuelve normativa. Lo que el mapeo autoritativo produzca y no sea LOW es mayor.
CATEGORIA_MINIMA = "LOW"
MAXIMO_DE_BAJOS = 10

# -- G3 y G4 -------------------------------------------------------------------

ALCANCE_COMPLETO = "FULL"
ALCANCE_SOLO_PREVIOS = "PREVIOUS_FINDINGS_ONLY"

_CACHE = {}


class EvaluacionInvalida(Exception):
    """Los entregables no se cargan a medias. Se falla cerrado."""


# -- la frontera de la aprobacion oficial --------------------------------------

def es_oficial(estado):
    return estado in ESTADOS_OFICIALES


def puede_emitir(productor, estado):
    """Si este productor puede poner la evaluacion en este estado.

    Estructural: no hay una tabla de estados prohibidos por productor. Un estado oficial exige
    procedencia externa, y un productor interno no es externo. Un productor que nadie declaro
    tampoco lo es.
    """
    if not es_oficial(estado):
        return estado in ESTADOS
    return productor in PRODUCTORES_EXTERNOS


def estado_oficial(declaracion=None):
    """El estado oficial de la evaluacion, con la guarda puesta.

    La declaracion trae `state`, `producer` y `evidence`. Sin procedencia externa CON evidencia
    no hay estado oficial: queda `OFFICIAL_STATUS_UNRESOLVED` y se dice quien lo intento.
    """
    doc = declaracion if isinstance(declaracion, dict) else {}
    pedido = doc.get("state")
    productor = doc.get("producer")
    evidencia = doc.get("evidence") or []
    salida = {"state": SIN_RESOLVER, "requestedState": pedido, "producer": productor,
              "states": [], "reasons": [], "evidence": list(evidencia)}

    if pedido is None:
        salida["reasons"].append("no se declaro ningun estado")
        salida["states"].append(SIN_RESOLVER)
        return salida
    if pedido not in ESTADOS:
        # Desconocido falla cerrado: no cae en aprobado y no cae en nada parecido.
        salida["states"].extend([ESTADO_DESCONOCIDO, SIN_RESOLVER])
        salida["reasons"].append("`%s` no es un estado del flujo de ES0902" % pedido)
        return salida

    if not es_oficial(pedido):
        salida["state"] = pedido
        return salida

    if productor in PRODUCTORES_INTERNOS or productor not in PRODUCTORES_EXTERNOS:
        salida["states"].extend([PRODUCTOR_INTERNO, SIN_RESOLVER])
        salida["reasons"].append("`%s` es un estado oficial y `%s` no es una autoridad externa: "
                                 "el harness prepara y mide, no homologa"
                                 % (pedido, productor))
        return salida
    if not evidencia:
        salida["states"].append(SIN_RESOLVER)
        salida["reasons"].append("`%s` exige evidencia de la autoridad externa y no vino ninguna"
                                 % pedido)
        return salida

    salida["state"] = pedido
    return salida


def resultado_interno(declaracion=None):
    """Lo que un productor interno si puede declarar. Nunca un estado oficial."""
    doc = declaracion if isinstance(declaracion, dict) else {}
    pedido = doc.get("result")
    productor = doc.get("producer")
    salida = {"result": None, "requestedResult": pedido, "producer": productor,
              "states": [], "reasons": []}
    if pedido in RESULTADOS_INTERNOS and productor in PRODUCTORES_INTERNOS:
        salida["result"] = pedido
        return salida
    if pedido in ESTADOS_OFICIALES:
        salida["states"].extend([PRODUCTOR_INTERNO, SIN_RESOLVER])
        salida["reasons"].append("`%s` es un estado oficial: un productor interno no lo emite"
                                 % pedido)
        return salida
    salida["states"].append(ESTADO_DESCONOCIDO)
    salida["reasons"].append("`%s` no es un resultado interno de ES0902" % pedido)
    return salida


# -- los entregables de la seccion 5 -------------------------------------------

def cargar_entregables(desde=None):
    """El archivo de entregables como dato. Levanta si no esta o no se lee."""
    ruta = roster.ruta_de_regla(ARCHIVO_DE_ENTREGABLES, desde or __file__)
    if ruta is None:
        raise EvaluacionInvalida("no esta %s" % ARCHIVO_DE_ENTREGABLES)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise EvaluacionInvalida("%s no se pudo leer: %s" % (ruta, e))


def validar_entregables(doc=None, desde=None):
    """Lista de errores contra el schema. Vacia es valido."""
    documento = doc if doc is not None else cargar_entregables(desde)
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise EvaluacionInvalida("no esta contexto-armar.py, de donde sale el validador.")
    ruta = rutas.localizar(("schemas", SCHEMA_DE_ENTREGABLES), desde or __file__)
    if ruta is None:
        raise EvaluacionInvalida("no esta %s" % SCHEMA_DE_ENTREGABLES)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def tipos_de_activo(desde=None):
    return sorted(cargar_entregables(desde).get("assetTypes", {}))


def entregables(tipos, contexto=None, doc=None, desde=None):
    """Los entregables exigidos por los tipos de activo, en union, con el requisito de WAF.

    🔴 La union, siempre. Y nunca el del primero ni el mas chico: un sistema que es dos cosas
    tiene que entregar lo de las dos.
    """
    documento = doc if doc is not None else cargar_entregables(desde)
    ctx = contexto if isinstance(contexto, dict) else {}
    catalogo = documento.get("assetTypes") or {}
    pedidos = [t for t in (tipos or []) if isinstance(t, str)]

    salida = {"assetTypes": sorted(set(pedidos)), "sourceIds": [], "requirements": [],
              "unknownAssetTypes": sorted({t for t in pedidos if t not in catalogo}),
              "missing": [], "states": [], "waf": None,
              "union": bool(documento.get("unionWhenMultipleAssetTypes"))}

    requisitos = []
    for t in salida["assetTypes"]:
        bloque = catalogo.get(t)
        if not isinstance(bloque, dict):
            continue
        salida["sourceIds"].append(bloque.get("sourceId"))
        for req in bloque.get("requirements") or []:
            if req not in requisitos:
                requisitos.append(req)
    salida["sourceIds"] = sorted(s for s in salida["sourceIds"] if s)
    salida["requirements"] = sorted(requisitos)

    if salida["unknownAssetTypes"]:
        salida["states"].append(seguridad.CONTEXTO_NORMATIVO_EXTERNO)

    entregados = {r for r in (ctx.get("providedDeliverables") or []) if isinstance(r, str)}
    salida["missing"] = sorted(r for r in salida["requirements"] if r not in entregados)
    if salida["missing"]:
        salida["states"].append(seguridad.ENTREGABLES_INCOMPLETOS)

    salida["waf"] = requisito_de_waf(salida["assetTypes"], ctx, documento)
    for e in salida["waf"].get("states") or []:
        if e not in salida["states"]:
            salida["states"].append(e)
    return salida


def requisito_de_waf(tipos, contexto=None, doc=None, desde=None):
    """Si estos tipos de activo exigen el formulario de WAF, y si esta su plantilla.

    🔴 Ningun campo del formulario se inventa. Lo unico que sale de aca es el NOMBRE del
    artefacto que trae el archivo, y si la plantilla no esta, el estado que lo dice.
    """
    documento = doc if doc is not None else cargar_entregables(desde)
    ctx = contexto if isinstance(contexto, dict) else {}
    bloque = documento.get("waf") or {}
    exigido_para = [t for t in (bloque.get("requiredFor") or [])]
    alcanzados = sorted({t for t in (tipos or []) if t in exigido_para})

    salida = {"required": bool(alcanzados), "requiredFor": alcanzados,
              "artifact": bloque.get("artifact") if alcanzados else None,
              "templateAvailable": None, "states": [], "reasons": []}
    if not alcanzados:
        return salida

    plantilla = ctx.get("wafFormTemplate")
    salida["templateAvailable"] = bool(plantilla)
    if not plantilla:
        salida["states"].append(bloque.get("missingTemplateState") or seguridad.WAF_SIN_CONTEXTO)
        salida["reasons"].append("el formulario de WAF lo provee el equipo de Prevencion y su "
                                 "plantilla no esta; sus campos no se inventan")
        return salida
    if not ctx.get("wafFormCompleted"):
        salida["states"].append(seguridad.ENTREGABLES_INCOMPLETOS)
        salida["reasons"].append("la plantilla de WAF esta y el formulario no se completo")
    return salida


def listo_para_pedir(tipos, contexto=None, doc=None, desde=None):
    """Si el paquete llega a `READY_TO_REQUEST`, o que lo bloquea.

    Exige que todos los entregables aplicables y el requisito de WAF esten resueltos. Un estado
    abierto no se negocia: bloquea.
    """
    resueltos = entregables(tipos, contexto, doc, desde)
    bloqueos = list(resueltos.get("states") or [])
    salida = {"state": LISTO_PARA_PEDIR if not bloqueos else None,
              "blockedBy": sorted(set(bloqueos)), "deliverables": resueltos}
    if bloqueos:
        salida["reasons"] = ["no se llega a %s con estados sin resolver: %s"
                             % (LISTO_PARA_PEDIR, ", ".join(sorted(set(bloqueos))))]
    return salida


# -- el umbral de aceptacion de G2 ---------------------------------------------

def _categoria(hallazgo, mapeo):
    """La categoria de riesgo de un hallazgo, si el mapeo autoritativo la da. `None` si no."""
    tabla = (mapeo or {}).get("map") or {}
    severidad = (hallazgo or {}).get("scannerSeverity")
    if severidad in tabla:
        return tabla[severidad]
    return None


def umbral(hallazgos, mapeo=None):
    """`G2_THRESHOLD_SATISFIED`, o por que no, o que el mapeo no alcanza.

    🔴 Sin mapeo autoritativo NO se calcula. Calcularlo con las etiquetas crudas del escaner es
    decidir que `medium` de una herramienta es el `LOW` de ES0902, y esa equivalencia la tiene
    que firmar alguien.
    """
    abiertos = [f for f in (hallazgos or []) if isinstance(f, dict)
                and (f.get("status") or "OPEN") != "CLOSED"]
    salida = {"satisfied": False, "states": [], "reasons": [],
              "lowCount": None, "aboveLowCount": None, "maxLowAllowed": MAXIMO_DE_BAJOS}

    # 🔴 `is True`, no verdad. `{"authoritative": "false"}` es un string no vacio y Python lo da
    # por verdadero: un productor que mandara el flag malformado habilitaba el calculo del umbral
    # con las etiquetas crudas del escaner, que es exactamente lo que este bloque impide.
    if (not isinstance(mapeo, dict) or mapeo.get("authoritative") is not True
            or not mapeo.get("evidence")):
        salida["states"].append(seguridad.MAPEO_DE_RIESGO_SIN_RESOLVER)
        salida["reasons"].append("las severidades del escaner no tienen un mapeo autoritativo a "
                                 "las categorias de riesgo de ES0902")
        return salida

    sin_mapear = [f for f in abiertos if _categoria(f, mapeo) is None]
    if sin_mapear:
        salida["states"].append(seguridad.MAPEO_DE_RIESGO_SIN_RESOLVER)
        salida["reasons"].append("hallazgos con severidad que el mapeo no cubre: %s"
                                 % ", ".join(sorted(str(f.get("id")) for f in sin_mapear)))
        return salida

    categorias = [_categoria(f, mapeo) for f in abiertos]
    bajos = [c for c in categorias if c == CATEGORIA_MINIMA]
    mayores = [c for c in categorias if c != CATEGORIA_MINIMA]
    salida["lowCount"] = len(bajos)
    salida["aboveLowCount"] = len(mayores)

    if mayores:
        salida["reasons"].append("hay %d hallazgo(s) por encima de %s"
                                 % (len(mayores), CATEGORIA_MINIMA))
        return salida
    if len(bajos) > MAXIMO_DE_BAJOS:
        salida["reasons"].append("hay %d hallazgos %s y el maximo es %d"
                                 % (len(bajos), CATEGORIA_MINIMA, MAXIMO_DE_BAJOS))
        return salida

    salida["satisfied"] = True
    salida["result"] = UMBRAL_SATISFECHO
    # 🔴 Y no se mueve nada mas. Satisfacer el umbral no es una aprobacion: son dos hechos
    # distintos y ES0902 los separa en dos reglas.
    salida["officialState"] = SIN_RESOLVER
    return salida


# -- los cuatro algoritmos que ES0902 declara y `seguridad.py` delega ----------

def regla_c2(r, evidencia, salida):
    """La aprobacion de seguridad tiene que estar evidenciada EN QA, y ser oficial."""
    ambiente = evidencia.get("environment")
    declaracion = evidencia.get("officialApproval")
    oficial = estado_oficial(declaracion)

    salida["environment"] = ambiente
    salida["officialState"] = oficial.get("state")
    for e in oficial.get("states") or []:
        if e not in salida["states"]:
            salida["states"].append(e)
    salida["reasons"].extend(oficial.get("reasons") or [])

    if ambiente != AMBIENTE_DE_HOMOLOGACION:
        salida["states"].append(C2_FUERA_DE_QA)
        salida["reasons"].append("la aprobacion de seguridad se evidencia en %s y el ambiente "
                                 "declarado es `%s`" % (AMBIENTE_DE_HOMOLOGACION, ambiente))
        return salida
    if oficial.get("state") != APROBADA:
        salida["reasons"].append("en QA, pero sin aprobacion oficial: una revision interna en "
                                 "QA no es una aprobacion")
        return salida
    return seguridad._generico(r, evidencia, salida)


def regla_g2(r, evidencia, salida):
    """El umbral de aceptacion. Nunca produce una aprobacion."""
    resuelto = umbral(evidencia.get("findings"), evidencia.get("riskMapping"))
    salida["threshold"] = resuelto
    for e in resuelto.get("states") or []:
        if e not in salida["states"]:
            salida["states"].append(e)
    salida["reasons"].extend(resuelto.get("reasons") or [])
    if not resuelto.get("satisfied"):
        if not resuelto.get("states"):
            salida["result"] = seguridad.NO_CUMPLE
        return salida
    salida["result"] = seguridad.CUMPLE
    salida["internalResult"] = UMBRAL_SATISFECHO
    # El estado oficial sigue donde estaba. Esta linea es ES0902 G1 escrita en el unico lugar
    # donde alguien tendria la tentacion de moverlo.
    salida["officialState"] = SIN_RESOLVER
    return salida


def regla_g3(r, evidencia, salida):
    """En un reenvio se recontrola el 100% de los hallazgos previos. Y G2 sigue aplicando."""
    previos = [f for f in (evidencia.get("previousFindings") or []) if isinstance(f, dict)]
    retests = {t.get("findingId"): t for t in (evidencia.get("retests") or [])
               if isinstance(t, dict)}
    ids = [f.get("id") for f in previos]
    sin_recontrolar = [i for i in ids
                       if i not in retests or not (retests.get(i) or {}).get("evidence")]

    salida["previousFindingCount"] = len(ids)
    salida["retestedCount"] = len(ids) - len(sin_recontrolar)
    salida["notRetested"] = sorted(str(i) for i in sin_recontrolar)

    if not previos:
        salida["states"].append(seguridad.SIN_EVIDENCIA_DE_CONTROL)
        salida["reasons"].append("un reenvio sin el reporte previo no se puede recontrolar")
        return salida
    if sin_recontrolar:
        salida["result"] = seguridad.NO_CUMPLE
        salida["reasons"].append("quedan %d hallazgo(s) previos sin recontrolar: %s"
                                 % (len(sin_recontrolar),
                                    ", ".join(salida["notRetested"])))
        return _con_g2(evidencia, salida)
    return _con_g2(evidencia, salida, seguridad._generico(r, evidencia, salida))


def regla_g4(r, evidencia, salida):
    """Un reporte previo obliga a una evaluacion de alcance completo. Y G2 sigue aplicando."""
    alcance = evidencia.get("assessmentScope")
    salida["assessmentScope"] = alcance
    salida["newFindingsAllowed"] = True

    if alcance == ALCANCE_SOLO_PREVIOS:
        salida["result"] = seguridad.NO_CUMPLE
        salida["reasons"].append("con un reporte previo, una evaluacion nueva es de alcance "
                                 "completo: limitarla a los hallazgos previos deja afuera todo "
                                 "lo que cambio desde entonces")
        return _con_g2(evidencia, salida)
    if alcance != ALCANCE_COMPLETO:
        salida["states"].append(seguridad.SIN_EVIDENCIA_DE_CONTROL)
        salida["reasons"].append("no se declaro el alcance de la evaluacion")
        return _con_g2(evidencia, salida)
    return _con_g2(evidencia, salida, seguridad._generico(r, evidencia, salida))


def _con_g2(evidencia, salida, base=None):
    """G2 sigue aplicando: recontrolar todo, o reevaluar entero, no exime del umbral."""
    destino = base if base is not None else salida
    resuelto = umbral(evidencia.get("findings"), evidencia.get("riskMapping"))
    destino["threshold"] = resuelto
    destino["g2Applies"] = True
    for e in resuelto.get("states") or []:
        if e not in destino["states"]:
            destino["states"].append(e)
    if not resuelto.get("satisfied"):
        destino["reasons"].extend(resuelto.get("reasons") or [])
        if destino.get("result") == seguridad.CUMPLE:
            destino["result"] = (seguridad.RESULTADO_SIN_RESOLVER if resuelto.get("states")
                                 else seguridad.NO_CUMPLE)
    return destino
