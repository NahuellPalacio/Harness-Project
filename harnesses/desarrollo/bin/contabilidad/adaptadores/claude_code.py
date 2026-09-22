"""Adaptador de transcripciones JSONL de Claude Code.

Lee un archivo de transcripcion y devuelve registros normalizados. No arma eventos, no
calcula plata y no sabe que existe un libro: eso es de `contrato.py`, del lado que no
conoce ningun proveedor.

🔴 La transcripcion escribe UNA LINEA POR BLOQUE DE CONTENIDO, y todas las lineas del mismo
mensaje repiten el mismo `usage`. Medido el 20-09-2026 sobre una transcripcion real de este
repositorio: 438 lineas de asistente, 252 ids de mensaje distintos, 186 repetidas. Sumar
linea por linea daba 739.096 tokens de salida contra 370.919 reales. La clave de
deduplicacion es el id del mensaje, y por eso existe.

🔴 `cost-state` es ACUMULADO. Aparece varias veces en el mismo archivo y cada aparicion
incluye a la anterior: se queda la ultima. Sumarlas seria contar la sesion entera tantas
veces como veces se escribio la linea.

🔴 La foto de la ventana -input + cache read + cache creation- NO es un consumo adicional.
Viaja como `context` para que la barra la muestre, y la agregacion sabe que no se suma.
"""
import io
import json
import os

from . import contrato

NOMBRE = "claude-code"
PROVEEDOR = "anthropic"

ASISTENTE = "assistant"
ESTADO_DE_COSTO = "cost-state"

# Del nombre del proveedor al del contrato normalizado. Es la unica tabla de traduccion, y
# vive acá: el nucleo no conoce ninguno de los nombres de la izquierda.
DE_USO = (
    ("input", "input_tokens"),
    ("output", "output_tokens"),
    ("cacheRead", "cache_read_input_tokens"),
    ("cacheCreation", "cache_creation_input_tokens"),
)
DE_AGREGADO = (
    ("input", "inputTokens"),
    ("output", "outputTokens"),
    ("cacheRead", "cacheReadInputTokens"),
    ("cacheCreation", "cacheCreationInputTokens"),
)

# Lo que ocupa la ventana ahora: lo que entro en esta llamada, no lo que salio.
DEL_CONTEXTO = ("input", "cacheRead", "cacheCreation")

MONEDA = "USD"


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _lineas(ruta):
    with io.open(ruta, encoding="utf-8") as f:
        for numero, linea in enumerate(f, 1):
            linea = linea.strip()
            if not linea:
                continue
            try:
                yield numero, json.loads(linea)
            except ValueError:
                continue


def _tokens_de(uso, tabla):
    tokens = {}
    for normalizado, crudo in tabla:
        tokens[normalizado] = _entero(uso.get(crudo))
    presentes = [tokens[c] for c in DEL_CONTEXTO if tokens.get(c) is not None]
    tokens["context"] = sum(presentes) if presentes else None
    tokens["contextLimit"] = None
    return tokens


def leer(ruta):
    """Los registros normalizados de una transcripcion. Deduplicados por id de mensaje."""
    if not ruta or not os.path.isfile(ruta):
        return [contrato.sin_resolver(
            reference=str(ruta or ""),
            motivo="no hay transcripcion en esa ruta: el consumo existe y no se pudo leer",
            provider=PROVEEDOR)]

    archivo = os.path.basename(ruta)
    registros = []
    vistos = set()
    ultimo_costo = None

    for numero, dato in _lineas(ruta):
        tipo = dato.get("type")
        if tipo == ESTADO_DE_COSTO:
            ultimo_costo = (numero, dato)
            continue
        if tipo != ASISTENTE:
            continue
        mensaje = dato.get("message") or {}
        mid = str(mensaje.get("id") or "")
        if not mid or mid in vistos:
            continue
        vistos.add(mid)
        uso = mensaje.get("usage") or {}
        registros.append(contrato.registro(
            provider=PROVEEDOR,
            model=mensaje.get("model"),
            tokens=_tokens_de(uso, DE_USO),
            session={"providerSessionId": dato.get("sessionId")},
            dedup_key="msg|" + mid,
            reference="%s#L%d" % (archivo, numero),
            timestamp=dato.get("timestamp"),
        ))

    if ultimo_costo is not None:
        registros.extend(_del_estado_de_costo(ultimo_costo, archivo))
    if not registros:
        return [contrato.sin_resolver(
            reference=archivo,
            motivo="la transcripcion no trae ninguna linea con consumo",
            provider=PROVEEDOR)]
    return registros


def _del_estado_de_costo(ultimo, archivo):
    """Lo que reporta el proveedor sobre la sesion entera: tokens, plata y tiempo.

    Los tokens salen como AGREGADO -otra medicion del mismo periodo, no un hecho
    adicional- y por eso la agregacion los concilia en vez de sumarlos. La plata y el
    tiempo tambien vienen acá porque no existen en ningun otro lado de la transcripcion.
    """
    numero, dato = ultimo
    sesion = str(dato.get("sessionId") or "")
    referencia = "%s#L%d" % (archivo, numero)
    marca = dato.get("timestamp") or str(dato.get("startTime") or "")
    registros = []

    for modelo in sorted((dato.get("modelUsage") or {})):
        crudo = (dato.get("modelUsage") or {})[modelo]
        registros.append(contrato.registro(
            provider=PROVEEDOR,
            model=modelo,
            tokens=_tokens_de(crudo, DE_AGREGADO),
            session={"providerSessionId": sesion},
            dedup_key="agg|%s|%s" % (sesion, modelo),
            reference=referencia,
            timestamp=marca,
            kind=contrato.AGREGADO,
            reported_amount=(None if dato.get("hasUnknownModelCost")
                             else crudo.get("costUSD")),
            currency=MONEDA,
        ))

    registros.append(contrato.registro(
        provider=PROVEEDOR,
        session={"providerSessionId": sesion},
        time={"wallMs": _entero(dato.get("totalDuration")),
              "modelMs": _entero(dato.get("totalAPIDuration")),
              "toolMs": _entero(dato.get("totalToolDuration"))},
        dedup_key="agg|%s|time" % sesion,
        reference=referencia,
        timestamp=marca,
        kind=contrato.AGREGADO,
    ))
    return registros
