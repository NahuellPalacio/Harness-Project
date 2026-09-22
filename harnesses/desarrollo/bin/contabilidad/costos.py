"""El motor de costos. No hay ninguna tarifa adentro de este archivo, y no la va a haber.

Dos metodos de calculo y nada mas:

    PROVIDER_REPORTED   el proveedor reporto la plata y se la cita con su referencia
    RATE_TABLE          el proyecto declaro una tabla de tarifas en su politica

Sin ninguno de los dos: `PRICING_UNAVAILABLE`, y el costo del evento queda
`COST_UNRESOLVED`. Inventar una tarifa para que el reporte tenga un numero es el error que
estos estados existen para evitar: un numero inventado en un reporte administrativo se
convierte en el numero, y nadie vuelve a preguntar de donde salio.

🔴 `actual` y `apiEquivalentEstimated` son dos campos porque son dos cosas. Con una
suscripcion, lo que el proveedor informa en dolares NO se gasto: es lo que habria costado
por API. Presentarlo como gasto real es mentirle a quien firma el presupuesto.
"""
RESUELTO = "RESOLVED"
SIN_RESOLVER = "COST_UNRESOLVED"
SIN_PRECIO = "PRICING_UNAVAILABLE"

REPORTADO = "PROVIDER_REPORTED"
TABLA = "RATE_TABLE"
METODOS = (REPORTADO, TABLA)

API = "API"
SUSCRIPCION = "SUBSCRIPTION"
EMPRESA = "ENTERPRISE"
INTERNO = "INTERNAL"
DESCONOCIDO = "UNKNOWN"
MODOS = (API, SUSCRIPCION, EMPRESA, INTERNO, DESCONOCIDO)

# En estos modos la plata medida es equivalente de API, no gasto incremental.
MODOS_DE_PLAN = (SUSCRIPCION, EMPRESA, INTERNO)

PLAN_FIJO = "FIXED_PLAN"

# Los siete que todo calculo monetario conserva. Sin uno de los siete no hay costo: un
# numero sin su fuente, su version y su moneda no se puede contrastar contra nada.
CAMPOS = ("provider", "model", "pricingSource", "pricingVersionOrDate",
          "currency", "billingMode", "calculationMethod")

POR_MILLON = 1000000.0

# Que campo de la tarifa paga cada clase de token.
TARIFA_DE = {
    "inputTokens": "inputPerMillion",
    "outputTokens": "outputPerMillion",
    "cacheReadTokens": "cacheReadPerMillion",
    "cacheCreationTokens": "cacheCreationPerMillion",
}


def _vacio(estado, **campos):
    costo = {"state": estado, "actual": None, "apiEquivalentEstimated": None,
             "actualState": DESCONOCIDO}
    for nombre in CAMPOS:
        costo[nombre] = campos.get(nombre)
    return costo


def sin_precio(provider=None, model=None, billing_mode=DESCONOCIDO, currency=None):
    """No hay como calcular. El estado lo dice y el reporte lo muestra."""
    return _vacio(SIN_PRECIO, provider=provider, model=model,
                  billingMode=billing_mode, currency=currency)


def _ubicar(costo, monto, modo):
    """Donde cae la plata segun el modo de facturacion. Es la regla entera del bloque.

    🔴 Nunca se copia un campo en el otro, y NUNCA quedan los dos con un numero. Un
    `actual` que salio de un equivalente de API es un gasto que nadie hizo, y dos montos
    llenos en la misma fila son una invitacion a sumar los dos.
    """
    if modo == API:
        costo["actual"] = monto
        costo["actualState"] = RESUELTO
        costo["apiEquivalentEstimated"] = None
        return costo
    if modo in MODOS_DE_PLAN:
        costo["apiEquivalentEstimated"] = monto
        costo["actual"] = None
        costo["actualState"] = PLAN_FIJO if modo != INTERNO else DESCONOCIDO
        return costo
    # UNKNOWN: se midio el consumo y no se sabe como se factura. No se elige por el.
    costo["state"] = SIN_RESOLVER
    costo["apiEquivalentEstimated"] = monto
    costo["actual"] = None
    costo["actualState"] = DESCONOCIDO
    return costo


def del_proveedor(monto, provider, model, currency, billing_mode, fuente, version):
    """La plata que reporto el proveedor, citada.

    `fuente` y `version` son obligatorias: un monto del proveedor sin decir de donde se
    leyo no se distingue de uno inventado.
    """
    if monto is None or not fuente or not version or not currency:
        return sin_precio(provider, model, billing_mode, currency)
    if billing_mode not in MODOS:
        return sin_precio(provider, model, DESCONOCIDO, currency)
    costo = _vacio(RESUELTO, provider=provider, model=model, currency=currency,
                   billingMode=billing_mode, pricingSource=str(fuente),
                   pricingVersionOrDate=str(version), calculationMethod=REPORTADO)
    return _ubicar(costo, float(monto), billing_mode)


def tarifa_para(modelo, tabla):
    """La fila de la tabla que aplica a este modelo, o None. Coincidencia exacta.

    No hay coincidencia parcial ni prefijo: un modelo no es el modelo de al lado porque
    compartan las primeras letras, y una tarifa aplicada al modelo equivocado es peor que
    ninguna porque el reporte sale con un numero.
    """
    for fila in tabla or []:
        if str(fila.get("model") or "") == str(modelo or ""):
            return fila
    return None


def de_tabla(uso, tabla, billing_mode, currency):
    """El costo calculado con la tabla que declaro el proyecto."""
    modelo = (uso or {}).get("model")
    fila = tarifa_para(modelo, tabla)
    provider = (uso or {}).get("provider")
    if fila is None:
        return sin_precio(provider, modelo, billing_mode, currency)
    if billing_mode not in MODOS:
        return sin_precio(provider, modelo, DESCONOCIDO, currency)

    monto = 0.0
    usadas = 0
    for clase, campo in sorted(TARIFA_DE.items()):
        cantidad = (uso or {}).get(clase)
        precio = fila.get(campo)
        if cantidad is None or precio is None:
            continue
        monto += (float(cantidad) / POR_MILLON) * float(precio)
        usadas += 1
    if not usadas:
        return sin_precio(provider, modelo, billing_mode, currency)

    costo = _vacio(RESUELTO, provider=provider or fila.get("provider"), model=modelo,
                   currency=currency, billingMode=billing_mode,
                   pricingSource=str(fila.get("source") or ""),
                   pricingVersionOrDate=str(fila.get("versionOrDate") or ""),
                   calculationMethod=TABLA)
    return _ubicar(costo, round(monto, 6), billing_mode)


def calcular(uso, politica, reportado=None, fuente="", version=""):
    """El costo de un uso. Primero lo que reporto el proveedor; despues la tabla.

    Lo reportado gana porque es una medicion del que factura, no una estimacion nuestra.
    Si no hay ninguno de los dos, el costo sale sin resolver y el reporte lo muestra.
    """
    politica = politica or {}
    modo = str(politica.get("billingMode") or DESCONOCIDO)
    moneda = politica.get("currency")
    provider = (uso or {}).get("provider")
    modelo = (uso or {}).get("model")

    if reportado is not None and fuente and version:
        return del_proveedor(reportado, provider, modelo, moneda, modo, fuente, version)
    if politica.get("rateTable"):
        return de_tabla(uso, politica.get("rateTable"), modo, moneda)
    return sin_precio(provider, modelo, modo, moneda)


def completo(costo):
    """True si el costo conserva los siete campos. Sin los siete no es un costo."""
    if not costo or costo.get("state") != RESUELTO:
        return False
    return all(costo.get(c) not in (None, "") for c in CAMPOS)


def sumar(bloques):
    """Los dos montos por separado, con lo que no se pudo calcular contado aparte."""
    resueltos = [b for b in bloques if b and b.get("state") == RESUELTO]
    sin_resolver = [b for b in bloques if b and b.get("state") != RESUELTO]

    reales = [b["actual"] for b in resueltos if b.get("actual") is not None]
    equivalentes = [b["apiEquivalentEstimated"] for b in resueltos
                    if b.get("apiEquivalentEstimated") is not None]
    monedas = sorted(set(str(b.get("currency") or "") for b in resueltos if b.get("currency")))
    modos = sorted(set(str(b.get("billingMode") or "") for b in resueltos if b.get("billingMode")))

    total = {
        "actual": round(sum(reales), 6) if reales else None,
        "apiEquivalentEstimated": round(sum(equivalentes), 6) if equivalentes else None,
        "currency": monedas[0] if len(monedas) == 1 else None,
        "billingModes": modos,
        "unresolved": len(sin_resolver),
        "state": RESUELTO if (resueltos and not sin_resolver) else SIN_RESOLVER,
    }
    # 🔴 Dos monedas en el mismo total no se suman. Un numero que mezcla pesos y dolares
    # es un numero con el que despues alguien decide.
    if len(monedas) > 1:
        total["actual"] = None
        total["apiEquivalentEstimated"] = None
        total["state"] = SIN_RESOLVER
        total["currency"] = None
    return total
