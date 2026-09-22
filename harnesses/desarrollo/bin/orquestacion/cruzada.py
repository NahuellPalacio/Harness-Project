"""El cruce entre ES0901 y ES0902: que se comparte, que se superpone y que no se decide solo.

Dos estandares de la misma autoridad se aplican a la misma unidad de trabajo y a veces piden lo
mismo. Este modulo dice cuando, y sobre todo cuando NO:

    OVERLAP_REUSE / CONTROL_REUSE      se comparte la EJECUCION de un control
    SUPPORTS / ADDITIONAL_GOVERNANCE   una regla agrega obligacion sobre la otra
    POTENTIAL_CONFLICT                 no se reconcilia sin evidencia autoritativa
    EQUIVALENCE_REVIEW_REQUIRED        no se deduplica sin comparar semantica
    NO_AUTO_PASS                       pasar de un lado nunca aprueba del otro

🔴 **Compartir ejecucion no es compartir resultado.** `authentication-delegation` sale de
ES0901 D2 y de ES0902 C1; se corre una vez y su resultado se anota por fuente normativa. Que D2
de PASS no pone en PASS a C1: la aplicabilidad de cada regla se resolvio por separado y la
evidencia que satisface a una puede no satisfacer a la otra.

🔴 **Una reconciliacion no se inventa.** ES0901 D1 pide autenticacion ciudadana del GCBA y
ES0902 C1 pide OpenID Connect con Keycloak de DGSEI. Decidir cual gana, o que son la misma,
es interpretacion normativa. Sin evidencia autoritativa queda
`CROSS_STANDARD_INTERPRETATION_REQUIRED` y ahi se queda.

🔴 **La clave es compuesta o no es clave.** `G1` no identifica una regla: los dos estandares
tienen G1 y no son la misma.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402
from . import seguridad                          # noqa: E402

ARCHIVO = "es0902-cross-standard-map.json"
SCHEMA = "es0902-cross-standard-map.schema.json"

REUSO = ("OVERLAP_REUSE", "CONTROL_REUSE")
SIN_DECIDIR = ("POTENTIAL_CONFLICT", "EQUIVALENCE_REVIEW_REQUIRED")
SIN_PASE_AUTOMATICO = "NO_AUTO_PASS"

SEPARADOR = "."
ES0901 = "ES0901"
ES0902 = "ES0902"
HARNESS = "HARNESS"

# Que evidencia reconcilia un cruce. La del proyecto sola no: que un equipo haya decidido como
# convive MIBA con Keycloak no vuelve normativa esa decision.
FUENTES_AUTORITATIVAS = ("GCBA_NORMATIVE", "ASI_APPROVAL", "GCBA_SECURITY_AUTHORITY")

RELACION_INVALIDA = "CROSS_STANDARD_RELATION_INVALID"


class CruzadaInvalida(Exception):
    """El mapa cruzado no se carga a medias. Se falla cerrado."""


# -- carga y validacion --------------------------------------------------------

def cargar(desde=None):
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        raise CruzadaInvalida("no esta %s" % ARCHIVO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise CruzadaInvalida("%s no se pudo leer: %s" % (ruta, e))


def validar_schema(doc=None, desde=None):
    documento = doc if doc is not None else cargar(desde)
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise CruzadaInvalida("no esta contexto-armar.py, de donde sale el validador.")
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise CruzadaInvalida("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def validar(doc=None, desde=None):
    """(valido, errores). Una relacion que necesita decidirse y no declara su estado es invalida."""
    documento = doc if doc is not None else cargar(desde)
    errores = list(validar_schema(documento, desde))
    for rel in documento.get("relations", []):
        tipo = rel.get("type")
        par = "%s -> %s" % (rel.get("from"), rel.get("to"))
        if tipo in SIN_DECIDIR and not rel.get("state"):
            errores.append("%s: %s es `%s` y no declara en que estado queda; una relacion que "
                           "no se decide sola tiene que decir donde espera"
                           % (RELACION_INVALIDA, par, tipo))
        if tipo in REUSO and not rel.get("sharedControls"):
            errores.append("%s: %s es `%s` y no nombra ningun control compartido"
                           % (RELACION_INVALIDA, par, tipo))
    return (not errores), errores


# -- consultas -----------------------------------------------------------------

def relaciones(doc=None, desde=None):
    return list((doc if doc is not None else cargar(desde)).get("relations", []))


def de(clave, doc=None, desde=None):
    """Las relaciones que tocan esta clave compuesta, de cualquiera de los dos lados."""
    return [r for r in relaciones(doc, desde)
            if clave in (r.get("from"), r.get("to"))]


def controles_compartidos(doc=None, desde=None):
    """{control_id: [claves compuestas]} — quien ejecuta una vez para mas de una regla."""
    salida = {}
    for r in relaciones(doc, desde):
        if r.get("type") not in REUSO:
            continue
        for cid in r.get("sharedControls") or []:
            claves = salida.setdefault(cid, [])
            for extremo in (r.get("from"), r.get("to")):
                if extremo and extremo not in claves:
                    claves.append(extremo)
    return {cid: sorted(claves) for cid, claves in sorted(salida.items())}


def fuentes_normativas_de(control_id, doc=None, desde=None):
    """Las claves compuestas que el mapa dice que comparten este control. Vacia si ninguna."""
    return controles_compartidos(doc, desde).get(control_id, [])


def _estandar_de(clave):
    return (clave or "").split(SEPARADOR)[0]


def _reconciliado(rel, contexto):
    """Si el contexto trae evidencia autoritativa que reconcilia justamente este par."""
    par = {rel.get("from"), rel.get("to")}
    for rec in (contexto or {}).get("reconciliations") or []:
        if not isinstance(rec, dict):
            continue
        if set(rec.get("between") or []) != par:
            continue
        if rec.get("source") in FUENTES_AUTORITATIVAS and rec.get("evidence"):
            return rec
    return None


# -- la resolucion cruzada -----------------------------------------------------

def resolver(aplicables_es0901=None, aplicables_es0902=None, contexto=None, doc=None,
             desde=None):
    """El bloque cruzado de una unidad: que se comparte y que quedo sin decidir.

    Una relacion solo se evalua si las dos reglas que toca estan APLICABLES. Dos reglas que no
    aplican no entran en conflicto, y emitir el estado igual llenaria todo reporte de cruces
    que no le pasan a nadie.
    """
    documento = doc if doc is not None else cargar(desde)
    ctx = contexto if isinstance(contexto, dict) else {}
    del1 = {"%s%s%s" % (ES0901, SEPARADOR, r) for r in (aplicables_es0901 or [])}
    del2 = {"%s%s%s" % (ES0902, SEPARADOR, r) for r in (aplicables_es0902 or [])}
    activas = del1 | del2

    salida = {"relations": [], "states": [], "sharedControls": {},
              "unresolved": []}

    for rel in relaciones(documento):
        origen, destino = rel.get("from"), rel.get("to")
        if origen not in activas:
            continue
        # Un destino del harness no es una regla y no se pregunta si aplica: existe siempre.
        if _estandar_de(destino) != HARNESS and destino not in activas:
            continue

        fila = {"from": origen, "to": destino, "type": rel.get("type"),
                "sharedControls": sorted(rel.get("sharedControls") or []),
                "rule": rel.get("rule"), "state": None, "reconciliation": None}

        if rel.get("type") in SIN_DECIDIR:
            reconciliacion = _reconciliado(rel, ctx)
            if reconciliacion is None:
                fila["state"] = rel.get("state")
                salida["unresolved"].append(fila["state"])
                if fila["state"] not in salida["states"]:
                    salida["states"].append(fila["state"])
            else:
                fila["reconciliation"] = {"source": reconciliacion.get("source"),
                                          "evidence": list(reconciliacion.get("evidence") or [])}
        for cid in fila["sharedControls"]:
            claves = salida["sharedControls"].setdefault(cid, [])
            for extremo in (origen, destino):
                if extremo not in claves:
                    claves.append(extremo)
        salida["relations"].append(fila)

    salida["sharedControls"] = {k: sorted(v) for k, v in sorted(salida["sharedControls"].items())}
    salida["unresolved"] = sorted(set(salida["unresolved"]))
    return salida


def resultado_por_fuente(control_id, resultado_del_control, claves, doc=None, desde=None):
    """El resultado de un control compartido, anotado por fuente normativa.

    🔴 Un resultado, varias fuentes, y ninguna hereda el veredicto de la otra. La ejecucion se
    comparte porque es la misma comprobacion tecnica; la aplicabilidad y la suficiencia de la
    evidencia son de cada regla. Propagar el PASS seria aprobar una regla que nadie evaluo.
    """
    salida = {"control": control_id, "executions": 1, "bySource": {}}
    for k in sorted(set(claves or [])):
        salida["bySource"][k] = {
            "standard": _estandar_de(k),
            "rule": k.split(SEPARADOR, 1)[1] if SEPARADOR in k else k,
            "controlResult": (resultado_del_control or {}).get("result"),
            "ruleResult": None,
            "reason": "el resultado del control no decide el de la regla: la regla se resuelve "
                      "con su propia aplicabilidad y su propia evidencia",
        }
    return salida


def prohibiciones(doc=None, desde=None):
    """Las relaciones `NO_AUTO_PASS`: donde pasar de un lado nunca aprueba del otro."""
    return [r for r in relaciones(doc, desde) if r.get("type") == SIN_PASE_AUTOMATICO]
