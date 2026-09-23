"""ES0902 O1: que normativa de TI del GCABA existe, en que estado esta, y que dice la revision.

    ES0902-3-O1   "Se deben respetar los principios y normativas vigentes de TI del GCABA."

Es la fila mas ancha del estandar y la unica que no se contesta mirando el sistema: se contesta
mirando **que normativa aplica** y **que se midio contra ella**. Por eso O1 no tiene check, tiene
una review, y por eso este modulo no evalua ningun control.

🔴 **La linea base no se adivina.** `gcba-it-normative-baseline.json` dice dos cosas de cada
fuente: si el harness tiene su contenido autoritativo cargado, y si consta que sigue vigente. Lo
que no dice se queda sin decir. ES0902 nombra tres resoluciones de la ASI cuyo contenido el harness
no tiene: entran con su titulo y su autoridad, y su contenido no se transcribe, no se resume y no
se deduce del texto que las cita.

🔴 **Falta contexto -> no cumple.** Una fuente aplicable sin cargar deja
`EXTERNAL_NORMATIVE_CONTEXT_REQUIRED`; una sin vigencia declarada deja
`NORMATIVE_SUPERSESSION_UNRESOLVED`. Las dos impiden `COMPLIANT`, y las dos estan hoy: la linea
base como viene deja toda corrida real en `REVIEW_INCOMPLETE`. Es incomodo y es cierto.

🔴 **`NON_COMPLIANT` le gana a `REVIEW_INCOMPLETE`, al reves que `revisiones.resolver`.** Es
deliberado: lo incompleto de O1 es permanente -las tres resoluciones no se van a cargar solas-, y
si titulara, un resultado normativo que falla quedaria escondido detras de un estado que no se
mueve nunca. Lo incompleto no desaparece, viaja en `states` y en `issues`.

🔴 **Nada se reejecuta.** Los resultados de ES0901 y de ES0902 entran declarados y se consumen tal
como salen. Volver a correr los controles bajo el nombre de O1 es tener dos respuestas a la misma
pregunta, y el dia que difieran las dos van a tener razon.

🔴 **Cumplir O1 no aprueba nada.** ES0902 §4 separa el control automatizado del circuito interno de
DGSEI, y esa frontera vive en `evaluacion.py`. Este modulo no emite ningun estado de ese flujo y no
tiene con que cruzarla.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import revisiones                         # noqa: E402
from . import roster                             # noqa: E402
from . import seguridad                          # noqa: E402

ARCHIVO = "gcba-it-normative-baseline.json"
SCHEMA = "gcba-it-normative-baseline.schema.json"

# La regla de la que sale todo esto. La seccion no esta en la matriz de ES0902 -que no las
# lleva- y si tiene que estar en la tupla normativa de un control y de una review.
ESTANDAR = seguridad.ESTANDAR
VERSION_DEL_ESTANDAR = seguridad.VERSION_ESPERADA
SECCION = "3"
REGLA = "O1"
CLAVE = seguridad.clave(REGLA)

POLICY = "gcba-it-security-normative-compliance-required"
REVIEW = "gcba-it-security-normative-review"

# -- el estado de una fuente ---------------------------------------------------

CARGADA = "LOADED"
NO_CARGADA = "DECLARED_EXTERNAL_NOT_LOADED"
ESTADOS_DE_FUENTE = (CARGADA, NO_CARGADA)

# 🔴 Ausente es `UNRESOLVED`, y ese es el default a proposito: que el harness tenga cargada una
# version no le consta que sea la vigente. Poner `CURRENT` por defecto seria firmar por nadie.
VIGENTE = "CURRENT"
REEMPLAZADA = "SUPERSEDED"
VIGENCIA_SIN_RESOLVER = "UNRESOLVED"
VIGENCIAS = (VIGENTE, REEMPLAZADA, VIGENCIA_SIN_RESOLVER)

# -- los estados que emite O1 --------------------------------------------------

# El primero es de ES0902 y se importa: un estado repetido se desincroniza en silencio.
CONTEXTO_EXTERNO = seguridad.CONTEXTO_NORMATIVO_EXTERNO
SUPERSESION_SIN_RESOLVER = "NORMATIVE_SUPERSESSION_UNRESOLVED"
LINEA_BASE_SIN_RESOLVER = "NORMATIVE_BASELINE_UNRESOLVED"
EVIDENCIA_INCOMPLETA = "EVIDENCE_INCOMPLETE"
SATISFECHA = "SATISFIED"

# Los seis resultados que la policy declara, en un solo lugar.
RESULTADOS_DE_POLICY = (SATISFECHA, revisiones.NO_CUMPLE, LINEA_BASE_SIN_RESOLVER,
                        CONTEXTO_EXTERNO, SUPERSESION_SIN_RESOLVER, EVIDENCIA_INCOMPLETA)

LINEA_BASE_VALIDA = "NORMATIVE_BASELINE_VALID"
LINEA_BASE_INVALIDA = "NORMATIVE_BASELINE_INVALID"

# -- el contrato de la review, importado y no redefinido -----------------------

CUMPLE = revisiones.CUMPLE
CUMPLE_CON_OBSERVACIONES = revisiones.CUMPLE_CON_OBSERVACIONES
NO_CUMPLE = revisiones.NO_CUMPLE
INCOMPLETA = revisiones.INCOMPLETA
RESULTADOS = (CUMPLE, CUMPLE_CON_OBSERVACIONES, NO_CUMPLE, INCOMPLETA)

# Los resultados por regla que una evidencia reusada puede traer. Son los de ES0902, que son
# tambien los que el harness usa para ES0901: uno solo de estos cinco, o no se entiende.
RESULTADOS_REUSABLES = seguridad.RESULTADOS


class LineaBaseInvalida(Exception):
    """La linea base no se carga a medias. Se falla cerrado."""


# -- carga y validacion --------------------------------------------------------

def cargar(desde=None):
    """La linea base como dato. Levanta si no esta o si no se puede leer."""
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        raise LineaBaseInvalida("no esta %s: sin linea base no se resuelve %s"
                                % (ARCHIVO, CLAVE))
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise LineaBaseInvalida("%s no se pudo leer: %s" % (ruta, e))


def cargar_schema(desde=None):
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise LineaBaseInvalida("no esta %s; la linea base no se valida sin su contrato."
                                % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(doc, desde=None):
    """Lista de errores contra el schema. Vacia es valido."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise LineaBaseInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def validar(doc=None, desde=None):
    """(estado, errores). `NORMATIVE_BASELINE_VALID` o `NORMATIVE_BASELINE_INVALID`.

    Los errores nombran la fuente por su id y no por su posicion: un error que dice
    `sources[2]` obliga a contar a mano para saber de cual habla.
    """
    documento = doc if doc is not None else cargar(desde)
    errores = list(validar_schema(documento, desde))

    ids = [f.get("id") for f in (documento or {}).get("sources") or []]
    repetidas = sorted({i for i in ids if ids.count(i) > 1 and i})
    if repetidas:
        errores.append("fuentes repetidas: %s" % ", ".join(repetidas))

    for f in (documento or {}).get("sources") or []:
        fid = f.get("id") or "(sin id)"
        if f.get("status") not in ESTADOS_DE_FUENTE:
            errores.append("%s declara el estado `%s`, que no existe: los dos son %s"
                           % (fid, f.get("status"), " y ".join(ESTADOS_DE_FUENTE)))
        vigencia = f.get("currency")
        if vigencia is not None and vigencia not in VIGENCIAS:
            errores.append("%s declara la vigencia `%s`, que no existe: las tres son %s"
                           % (fid, vigencia, ", ".join(VIGENCIAS)))
        reemplazo = f.get("supersededBy")
        if reemplazo and reemplazo not in ids:
            errores.append("%s dice que la reemplaza `%s`, que la linea base no declara"
                           % (fid, reemplazo))
        if not f.get("authority"):
            errores.append("%s no dice quien la dicta: sin autoridad es un documento" % fid)

    return (LINEA_BASE_INVALIDA if errores else LINEA_BASE_VALIDA), errores


# -- consultas -----------------------------------------------------------------

def fuentes(doc=None, desde=None):
    return list((doc if doc is not None else cargar(desde)).get("sources") or [])


def fuente(fuente_id, doc=None, desde=None):
    """La fuente por su id, o `None`. No levanta: preguntar por una que no esta es valido."""
    for f in fuentes(doc, desde):
        if f.get("id") == fuente_id:
            return f
    return None


def estado_de(f):
    """`LOADED` o `DECLARED_EXTERNAL_NOT_LOADED`. Lo que no es ninguno de los dos no es nada."""
    estado = (f or {}).get("status")
    return estado if estado in ESTADOS_DE_FUENTE else None


def vigencia_de(f):
    """La vigencia declarada. Ausente y desconocida son las dos `UNRESOLVED`."""
    vigencia = (f or {}).get("currency")
    return vigencia if vigencia in VIGENCIAS else VIGENCIA_SIN_RESOLVER


def cargadas(doc=None, desde=None):
    """Los ids de las fuentes cuyo contenido autoritativo esta."""
    return [f.get("id") for f in fuentes(doc, desde) if estado_de(f) == CARGADA]


def declaradas_no_cargadas(doc=None, desde=None):
    """Los ids de las que un estandar nombra y el harness no tiene."""
    return [f.get("id") for f in fuentes(doc, desde) if estado_de(f) == NO_CARGADA]


def _sucesion_resuelta(f, doc):
    """Si una fuente reemplazada dice por cual, y esa otra esta declarada."""
    reemplazo = (f or {}).get("supersededBy")
    return bool(reemplazo) and fuente(reemplazo, doc) is not None


def estado_de_fuente(f, doc=None):
    """(estados, motivos) de una fuente. Vacios es una fuente que no bloquea nada."""
    estados, motivos = [], []
    fid = (f or {}).get("id") or "(sin id)"
    if estado_de(f) != CARGADA:
        estados.append(CONTEXTO_EXTERNO)
        motivos.append("%s: la fuente esta declarada y su contenido autoritativo no esta "
                       "cargado" % fid)
    vigencia = vigencia_de(f)
    if vigencia == VIGENTE:
        return estados, motivos
    if vigencia == REEMPLAZADA and _sucesion_resuelta(f, doc):
        motivos.append("%s: fue reemplazada por %s, que la linea base declara"
                       % (fid, f.get("supersededBy")))
        return estados, motivos
    estados.append(SUPERSESION_SIN_RESOLVER)
    motivos.append("%s: no consta si sigue vigente" % fid
                   if vigencia != REEMPLAZADA
                   else "%s: consta reemplazada y no dice por cual" % fid)
    return estados, motivos


def resolver(doc=None, desde=None):
    """El estado de la linea base entera: que fuentes hay y cual bloquea que cosa.

    🔴 Todas las fuentes declaradas son aplicables. No hay filtro por alcance: elegir cuales le
    tocan a una unidad es interpretacion normativa, y es la misma que el paquete de ES0902
    prohibe cuando cruza D1 con C1.
    """
    documento = doc if doc is not None else cargar(desde)
    estados, motivos, filas = [], [], []
    for f in fuentes(documento):
        propios, razones = estado_de_fuente(f, documento)
        estados.extend(propios)
        motivos.extend(razones)
        filas.append({"id": f.get("id"), "title": f.get("title"),
                      "version": f.get("version"), "status": estado_de(f),
                      "currency": vigencia_de(f), "authority": f.get("authority"),
                      "states": propios})
    return {"version": documento.get("version"), "authority": documento.get("authority"),
            "sources": filas, "states": sorted(set(estados)), "issues": motivos,
            "loaded": cargadas(documento), "notLoaded": declaradas_no_cargadas(documento)}


# -- los resultados que ya existen, reusados -----------------------------------

def _campo(r, nombre):
    """Un campo de la tupla normativa, este arriba o adentro de `source`.

    🔴 Un resultado tal como sale de `seguridad.resultado` lleva la regla arriba y el estandar
    adentro de `source`. Pedirle otra forma seria pedir una traduccion, y una traduccion es el
    lugar donde se pierde de que estandar salio cada resultado.
    """
    return r.get(nombre) or (r.get("source") or {}).get(nombre)


def _clave_de(r):
    if r.get("ruleKey"):
        return r.get("ruleKey")
    return "%s.%s" % (_campo(r, "standard"), _campo(r, "rule"))


def _fila_reusada(r):
    return {"standard": _campo(r, "standard"), "version": _campo(r, "version"),
            "rule": _campo(r, "rule"), "ruleKey": _clave_de(r), "result": r.get("result")}


def reusados(evidencia):
    """Los resultados declarados, como lista. Lo que no es un dict no es un resultado."""
    bloque = (evidencia or {}).get("standardResults")
    if isinstance(bloque, dict):
        bloque = [bloque]
    return [r for r in (bloque or []) if isinstance(r, dict)]


# -- la review de O1 -----------------------------------------------------------

def trazabilidad():
    """De donde sale O1. Viaja en todo resultado, por todos los caminos."""
    return {"standard": ESTANDAR, "version": VERSION_DEL_ESTANDAR, "section": SECCION,
            "rule": REGLA, "ruleKey": CLAVE}


def revision(evidencia=None, doc=None, desde=None):
    """El resultado de la review de O1: `{result, states, issues, source, ...}`.

    Mismas claves y mismos cuatro resultados que `revisiones.resolver`, importados de ahi. El
    resultado NO lo declara quien revisa: se calcula, por la misma razon por la que se calcula
    el de cualquier otra review.
    """
    ev = evidencia if isinstance(evidencia, dict) else {}
    sujeto = ev.get("subject") if isinstance(ev.get("subject"), dict) else {}
    salida = {"result": INCOMPLETA, "states": [], "issues": [], "source": trazabilidad(),
              "subject": dict(sujeto), "baseline": None, "reusedResults": [], "overrides": []}
    estados, motivos = [], []
    incompleta = no_cumple = observaciones = False

    if not sujeto.get("id"):
        estados.append(EVIDENCIA_INCOMPLETA)
        motivos.append("la revision no dice sobre que es: una revision sin sujeto no es una "
                       "revision")
        incompleta = True

    documento = doc if doc is not None else ev.get("normativeBaseline")
    try:
        if documento is None:
            documento = cargar(desde)
        veredicto, errores = validar(documento, desde)
    except LineaBaseInvalida as e:
        veredicto, errores = LINEA_BASE_INVALIDA, [str(e)]
        documento = None
    if veredicto != LINEA_BASE_VALIDA:
        salida["states"] = sorted(set(estados + [LINEA_BASE_SIN_RESOLVER]))
        salida["issues"] = motivos + ["la linea base no se pudo resolver: %s" % e
                                      for e in errores]
        return salida

    linea = resolver(documento, desde)
    salida["baseline"] = linea
    # Los motivos de la linea base viajan siempre. Una sucesion RESUELTA no bloquea nada y
    # tiene que quedar escrita igual: que algo no bloquee no es razon para no decirlo.
    motivos.extend(linea["issues"])
    if linea["states"]:
        estados.extend(linea["states"])
        incompleta = True

    # -- los resultados que ya existen, consumidos y no recalculados
    declarados = reusados(ev)
    if not declarados:
        estados.append(EVIDENCIA_INCOMPLETA)
        motivos.append("no hay ningun resultado normativo declarado: O1 se contesta con lo que "
                       "ya se midio, y no hay nada que reusar")
        incompleta = True

    peticiones = ev.get("overrides") or []
    cargadas_ = set(linea["loaded"])
    for r in declarados:
        if not (_campo(r, "standard") and _campo(r, "rule")):
            estados.append(EVIDENCIA_INCOMPLETA)
            motivos.append("hay un resultado declarado que no dice de que estandar y de que "
                           "regla sale")
            incompleta = True
            continue
        fila = _fila_reusada(r)
        if fila["standard"] not in cargadas_:
            estados.append(CONTEXTO_EXTERNO)
            motivos.append("%s: el resultado cita una fuente que la linea base no declara "
                           "cargada" % fila["ruleKey"])
            incompleta = True
        resultado_ = r.get("result")
        if resultado_ not in RESULTADOS_REUSABLES:
            estados.append(EVIDENCIA_INCOMPLETA)
            motivos.append("%s: el resultado `%s` no es ninguno de los que una regla produce"
                           % (fila["ruleKey"], resultado_))
            incompleta = True
        elif resultado_ == seguridad.NO_CUMPLE:
            # 🔴 Solo la clave compuesta. `D1` no identifica una regla: los dos estandares
            # pueden traer el mismo id local, y una excepcion que se cobra la regla del otro
            # estandar es la peor forma de que una obligacion desaparezca.
            concedida = seguridad.excepcion_de(fila["ruleKey"], peticiones)
            if concedida:
                fila["override"] = concedida
                salida["overrides"].append({"ruleKey": fila["ruleKey"],
                                            "affectedRules": concedida.get("affectedRules"),
                                            "reason": concedida.get("reason")})
                motivos.append("%s: no cumple y hay una excepcion concedida con contrato y "
                               "aprobacion de ASI; queda como observacion" % fila["ruleKey"])
                observaciones = True
            else:
                motivos.append("%s: resultado normativo aplicable en %s"
                               % (fila["ruleKey"], seguridad.NO_CUMPLE))
                no_cumple = True
        elif resultado_ == seguridad.RESULTADO_SIN_RESOLVER:
            estados.append(EVIDENCIA_INCOMPLETA)
            motivos.append("%s: el resultado esta sin resolver" % fila["ruleKey"])
            incompleta = True
        elif resultado_ == seguridad.EXCEPTUADA:
            motivos.append("%s: la obligacion la levanto una excepcion con respaldo"
                           % fila["ruleKey"])
            observaciones = True
        salida["reusedResults"].append(fila)

    # 🔴 Lo que no se concedio tambien se dice. Una excepcion pedida y no otorgada que no deja
    # rastro es indistinguible de una que nadie pidio.
    for pedida in peticiones:
        sin_conceder = seguridad.excepcion(pedida)
        if sin_conceder.get("granted"):
            continue
        estados.append(seguridad.OVERRIDE_SIN_RESOLVER)
        motivos.extend(sin_conceder.get("reasons") or [])
        incompleta = True

    if no_cumple:
        salida["result"] = NO_CUMPLE
    elif incompleta:
        salida["result"] = INCOMPLETA
    elif observaciones:
        salida["result"] = CUMPLE_CON_OBSERVACIONES
    else:
        salida["result"] = CUMPLE
    salida["states"] = sorted(set(estados))
    salida["issues"] = motivos
    return salida


def estado_de_policy(revision_resuelta):
    """El resultado de la policy que O1 declara, derivado del de la review.

    Son dos vocabularios y no uno: la policy dice si el requisito esta satisfecho, la review
    dice en que termino la revision. Colapsarlos deja a la policy sin manera de decir POR QUE
    no esta satisfecho.
    """
    resuelta = revision_resuelta or {}
    resultado_ = resuelta.get("result")
    if resultado_ in (CUMPLE, CUMPLE_CON_OBSERVACIONES):
        return SATISFECHA
    if resultado_ == NO_CUMPLE:
        return revisiones.NO_CUMPLE
    for estado in (LINEA_BASE_SIN_RESOLVER, CONTEXTO_EXTERNO, SUPERSESION_SIN_RESOLVER):
        if estado in (resuelta.get("states") or []):
            return estado
    return EVIDENCIA_INCOMPLETA


# -- el resultado de la fila, que sale de la review ----------------------------

def regla_o1(r, evidencia, salida):
    """El noveno algoritmo de ES0902: O1 sale de su review y no del camino generico.

    🔴 El camino generico pondria O1 en `COMPLIANT` con dos `controlResults` en `PASS`, y esos
    dos ids son **la policy y la review de O1 misma**: O1 cumpliria porque alguien declaro que
    O1 cumple. Es la regla mas ancha del estandar y seria la mas barata de poner en verde.
    """
    resuelta = revision(evidencia)
    salida["review"] = {"id": REVIEW, "result": resuelta["result"],
                        "states": resuelta["states"], "issues": resuelta["issues"],
                        "source": resuelta["source"]}
    salida["policy"] = {"id": POLICY, "result": estado_de_policy(resuelta)}
    salida["baseline"] = resuelta["baseline"]
    salida["reusedResults"] = resuelta["reusedResults"]
    salida["states"].extend(resuelta["states"])
    salida["reasons"].extend(resuelta["issues"])

    if resuelta["result"] == NO_CUMPLE:
        salida["result"] = seguridad.NO_CUMPLE
    elif resuelta["result"] in (CUMPLE, CUMPLE_CON_OBSERVACIONES):
        salida["result"] = seguridad.CUMPLE
    else:
        salida["result"] = seguridad.RESULTADO_SIN_RESOLVER
    return salida
