"""La politica de presupuesto y el gate que devuelve evidencia.

🔴 Este modulo NO aprueba nada. No hay una funcion `aprobar`, y ninguno de los seis estados
que devuelve significa "adelante". La autoridad para escalar a un modelo caro sigue siendo
la compuerta humana del Bloque 3 —`orquestacion/consumo.decidir`—, que este paquete ni
siquiera importa. Lo unico que hace el Bloque 4 con un escalamiento es decir cuanta plata
lleva gastada la tarea, cuanta pide el escalamiento y contra que limite.

Sin politica declarada: `BUDGET_UNDEFINED`. No se inventa un limite por defecto. Un
presupuesto inventado es peor que ninguno: el que no existe se nota, el inventado se
respeta.
"""
import importlib.util
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas  # noqa: E402

from . import costos  # noqa: E402

SCHEMA = "budget-policy.schema.json"

DENTRO = "WITHIN_BUDGET"
AVISO = "BUDGET_WARNING"
EXCEDIDO = "BUDGET_EXCEEDED"
APROBACION = "HUMAN_APPROVAL_REQUIRED"
SIN_DEFINIR = "BUDGET_UNDEFINED"
SIN_COSTO = costos.SIN_RESOLVER

ESTADOS = (DENTRO, AVISO, EXCEDIDO, APROBACION, SIN_DEFINIR, SIN_COSTO)

NIVELES = ("NORMAL", "WARNING", "ERROR", "UNRESOLVED")


class PoliticaInvalida(Exception):
    """La politica no se usa. Comparar contra un limite mal leido es peor que no comparar."""


_CACHE = {}


def _armador():
    """Se carga una vez por proceso, como en `eventos`."""
    if "armador" not in _CACHE:
        ruta = rutas.localizar(("bin", "contexto-armar.py"), __file__)
        if ruta is None:
            return None
        spec = importlib.util.spec_from_file_location("contexto_armar_presupuesto", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CACHE["armador"] = modulo
    return _CACHE.get("armador")


def cargar_schema():
    if "schema" not in _CACHE:
        ruta = rutas.localizar(("schemas", SCHEMA), __file__)
        if ruta is None:
            raise PoliticaInvalida("no esta %s." % SCHEMA)
        with io.open(ruta, encoding="utf-8") as f:
            _CACHE["schema"] = json.load(f)
    return json.loads(json.dumps(_CACHE["schema"]))


def validar(politica):
    armador = _armador()
    if armador is None:
        raise PoliticaInvalida(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    return armador.validar(politica, esquema)


def cargar(ruta):
    """La politica del proyecto, o None. Un archivo roto NO se degrada a un default."""
    if not ruta or not os.path.isfile(ruta):
        return None
    with io.open(ruta, encoding="utf-8-sig") as f:
        politica = json.load(f)
    errores = validar(politica)
    if errores:
        raise PoliticaInvalida(
            "la politica no valida contra %s:\n  - %s" % (SCHEMA, "\n  - ".join(errores[:5])))
    return politica


def declarada(politica, ambito="task"):
    """True si hay al menos un limite declarado para ese ambito."""
    limites = (politica or {}).get(ambito) or {}
    return any(limites.get(k) is not None for k in ("softLimit", "hardLimit"))


def consumido(resumen, politica):
    """La plata que se compara contra el limite, segun como se factura.

    Con API se compara el gasto real. Con un plan fijo se compara el equivalente de API,
    que es lo unico que hay — y queda dicho en la decision, para que nadie lea el numero
    como plata gastada.
    """
    total = (resumen or {}).get("cost") or {}
    modo = str((politica or {}).get("billingMode") or costos.DESCONOCIDO)
    if modo == costos.API:
        return total.get("actual"), "actual"
    if modo in costos.MODOS_DE_PLAN:
        return total.get("apiEquivalentEstimated"), "apiEquivalentEstimated"
    return None, "unknown"


def evaluar(actual, incremento, politica, ambito="task", premium=False):
    """La decision de presupuesto, con sus numeros. Es EVIDENCIA, no un permiso.

    El orden de precedencia esta escrito y no se reordena por conveniencia:

        1. sin politica                      -> BUDGET_UNDEFINED
        2. sin costo comparable              -> COST_UNRESOLVED
        3. ya se paso el limite duro         -> BUDGET_EXCEEDED
        4. premium y la politica pide gente  -> HUMAN_APPROVAL_REQUIRED
        5. el proyectado pasa el duro        -> HUMAN_APPROVAL_REQUIRED o BUDGET_EXCEEDED
        6. el proyectado pasa el blando      -> BUDGET_WARNING
        7. lo demas                          -> WITHIN_BUDGET

    El 3 va antes que el 4 a proposito: lo que ya se gasto no se puede aprobar.
    """
    limites = (politica or {}).get(ambito) or {}
    blando = limites.get("softLimit")
    duro = limites.get("hardLimit")
    premium_cfg = (politica or {}).get("premiumModel") or {}

    decision = {
        "scope": ambito,
        "currency": (politica or {}).get("currency"),
        "billingMode": (politica or {}).get("billingMode"),
        "currentAmount": actual,
        "estimatedIncrement": incremento,
        "projectedAmount": None,
        "softLimit": blando,
        "hardLimit": duro,
        "status": SIN_DEFINIR,
        "reason": "",
    }

    if not declarada(politica, ambito):
        decision["reason"] = (
            "no hay presupuesto declarado para %s. No se inventa un limite por defecto."
            % ambito)
        return decision

    if actual is None:
        decision["status"] = SIN_COSTO
        decision["reason"] = (
            "no hay un costo comparable: sin plata resuelta no se puede decir si un limite "
            "se pasa.")
        return decision

    proyectado = float(actual) + float(incremento or 0)
    decision["projectedAmount"] = round(proyectado, 6)

    if duro is not None and float(actual) > float(duro):
        decision["status"] = EXCEDIDO
        decision["reason"] = ("ya se paso el limite duro: lo que se gasto no se puede "
                              "aprobar despues.")
        return decision

    if premium and bool(premium_cfg.get("requiresHumanApproval")):
        decision["status"] = APROBACION
        decision["reason"] = ("la politica pide que un escalamiento caro lo decida una "
                              "persona. El Bloque 4 no aprueba: esto es la evidencia.")
        return decision

    if duro is not None and proyectado > float(duro):
        if bool(premium_cfg.get("projectedOverrunRequiresApproval")):
            decision["status"] = APROBACION
            decision["reason"] = ("el proyectado pasa el limite duro y la politica pide "
                                  "aprobacion humana antes de seguir.")
        else:
            decision["status"] = EXCEDIDO
            decision["reason"] = "el proyectado pasa el limite duro."
        return decision

    if blando is not None and proyectado > float(blando):
        decision["status"] = AVISO
        decision["reason"] = ("el proyectado pasa el limite blando. Un aviso avisa: no "
                              "bloquea nada.")
        return decision

    decision["status"] = DENTRO
    decision["reason"] = "el proyectado queda debajo de los limites declarados."
    return decision


def consumo_relativo(actual, politica, ambito="task"):
    """Fraccion del limite duro —o del blando si no hay duro— ya consumida, o None."""
    limites = (politica or {}).get(ambito) or {}
    techo = limites.get("hardLimit")
    if techo is None:
        techo = limites.get("softLimit")
    if techo in (None, 0) or actual is None:
        return None
    return float(actual) / float(techo)


def nivel(fraccion, umbrales):
    """NORMAL / WARNING / ERROR / UNRESOLVED.

    🔴 Los umbrales llegan de la configuracion. Sin umbrales declarados el nivel es
    UNRESOLVED y no un verde inventado: un umbral escondido en el codigo de la barra es un
    numero que nadie puede cambiar sin tocar la barra.
    """
    umbrales = umbrales or {}
    aviso = umbrales.get("warningAt")
    error = umbrales.get("errorAt")
    if fraccion is None or (aviso is None and error is None):
        return "UNRESOLVED"
    if error is not None and fraccion >= float(error):
        return "ERROR"
    if aviso is not None and fraccion >= float(aviso):
        return "WARNING"
    return "NORMAL"


def texto_de_decision(decision):
    """La decision como la lee una persona. En espanol, por ADR-0011."""
    def monto(valor):
        if valor is None:
            return "sin resolver"
        return "%s %.2f" % (decision.get("currency") or "", float(valor))

    return "\n".join([
        "Evidencia de presupuesto (el Bloque 4 no aprueba)",
        "",
        "  Ambito:      %s" % decision["scope"],
        "  Facturacion: %s" % (decision.get("billingMode") or "sin declarar"),
        "  Consumido:   %s" % monto(decision.get("currentAmount")),
        "  Incremento:  %s" % monto(decision.get("estimatedIncrement")),
        "  Proyectado:  %s" % monto(decision.get("projectedAmount")),
        "  Limites:     blando %s / duro %s" % (monto(decision.get("softLimit")),
                                                monto(decision.get("hardLimit"))),
        "  Estado:      %s" % decision["status"],
        "  Motivo:      %s" % decision["reason"],
    ])
