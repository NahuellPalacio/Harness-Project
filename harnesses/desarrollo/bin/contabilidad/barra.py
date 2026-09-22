"""Lo que la barra de estado muestra de la sesion ACTIVA.

Este modulo no dibuja nada: devuelve el resumen normalizado que una barra consume. La UI
-una extension de VS Code, una linea de la terminal- lee esto y no toca una transcripcion
nunca. Parsear el formato de un proveedor desde el renderizado es como termina una UI
siendo la fuente de verdad contable.

🔴 Contexto y presupuesto son dos cosas y se muestran separadas. Una ventana al 78% no dice
nada sobre la plata, y una tarea al 90% del presupuesto puede tener la ventana vacia.

🔴 Los umbrales salen de la politica. Sin umbrales declarados el nivel es `UNRESOLVED` y se
muestra el numero igual: un verde inventado es peor que un signo de pregunta.
"""
from . import agregacion
from . import presupuesto
from . import tiempo

SIN_LIMITE = None


def sesiones(libro):
    """Las sesiones que aparecen en el libro, ordenadas. Ninguna se borra al cambiar."""
    vistas = set()
    for evento in libro:
        sid = evento.get("sessionId")
        if sid:
            vistas.add(str(sid))
    return tuple(sorted(vistas))


def de_sesion(libro, session_id):
    """Los eventos de una sesion. El resto del libro sigue donde estaba."""
    return [e for e in libro if str(e.get("sessionId") or "") == str(session_id or "")]


def de(libro, session_id, politica=None, task_id=""):
    """El estado de la barra para la sesion activa.

    Cambiar de sesion cambia los numeros porque se vuelve a calcular sobre los eventos de
    esa sesion. Lo que ya estaba en el libro no se toca: la sesion anterior se vuelve a
    pedir igual, con los mismos numeros.
    """
    eventos_de_sesion = de_sesion(libro, session_id)
    resumen = agregacion.resumir(eventos_de_sesion, task_id=task_id)

    foto = resumen["context"]
    limite = foto.get("contextLimit")
    fraccion_contexto = None
    if foto.get("contextTokens") is not None and limite:
        fraccion_contexto = float(foto["contextTokens"]) / float(limite)

    gastado, campo = presupuesto.consumido(resumen, politica)
    fraccion_presupuesto = presupuesto.consumo_relativo(gastado, politica)
    umbrales = (politica or {}).get("statusBar") or {}

    return {
        "sessionId": str(session_id or ""),
        "taskId": resumen["taskId"],
        "model": foto.get("model"),
        "context": {
            "tokens": foto.get("contextTokens"),
            "limit": limite,
            "fraction": fraccion_contexto,
            "level": presupuesto.nivel(
                fraccion_contexto,
                {"warningAt": umbrales.get("contextWarningAt"),
                 "errorAt": umbrales.get("contextErrorAt")}),
        },
        "budget": {
            "amount": gastado,
            "field": campo,
            "currency": (politica or {}).get("currency"),
            "fraction": fraccion_presupuesto,
            "level": presupuesto.nivel(fraccion_presupuesto, umbrales),
        },
        "time": {
            "wallMs": resumen["time"].get("wallMs"),
            "modelMs": resumen["time"].get("modelMs"),
            "toolMs": resumen["time"].get("toolMs"),
        },
        "tokens": resumen["tokens"],
        "unresolved": resumen["unresolved"],
    }


def _porcentaje(fraccion):
    if fraccion is None:
        return "?"
    return "%d%%" % int(round(fraccion * 100))


def _plata(estado):
    """La plata, con `eq` cuando es equivalente de API y no gasto.

    🔴 La marca no es decorativa. Un numero sin ella, en un proyecto con suscripcion, se lee
    como plata que se gasto.
    """
    monto = estado["budget"]["amount"]
    if monto is None:
        return "sin resolver"
    moneda = estado["budget"]["currency"] or ""
    marca = "" if estado["budget"]["field"] == "actual" else " eq"
    return ("%s %.2f%s" % (moneda, float(monto), marca)).strip()


# De menos a mas informativo. Es el orden en el que se caen las piezas cuando no entran, y
# esta escrito acá y no adentro del bucle para que se pueda leer sin seguir un indice.
DEGRADA = ("time", "money", "model")


def compacto(estado, ancho=60):
    """Una linea. Degrada de a pedazos y NUNCA suelta un estado de aviso o de error."""
    alerta = [n for n in (estado["context"]["level"], estado["budget"]["level"])
              if n in ("WARNING", "ERROR")]
    piezas = {
        "model": estado.get("model") or "sin modelo",
        "context": "Ctx " + _porcentaje(estado["context"]["fraction"]),
        "budget": "Budget " + _porcentaje(estado["budget"]["fraction"]),
        "money": _plata(estado),
        "time": tiempo.como_texto(estado["time"].get("wallMs")),
    }
    orden = ["model", "context", "budget", "money", "time"]
    if alerta:
        piezas["alert"] = "ERROR" if "ERROR" in alerta else "WARNING"
        orden.append("alert")

    def texto():
        return " · ".join(piezas[k] for k in orden)

    for candidato in DEGRADA:
        if len(texto()) <= ancho:
            break
        orden.remove(candidato)
    return texto()
