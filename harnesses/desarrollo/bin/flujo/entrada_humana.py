"""Donde completa la persona lo que falta. Ubica y explica; nunca escribe, nunca ve el valor.

    localizar(inputId, proyecto)  ->  archivo, linea, columna, si esta cargado, y la URI de
                                      VS Code que abre el archivo en ese lugar
    renderizar(ubicacion)         ->  la instruccion en espanol, con un placeholder donde va
                                      el valor

La linea la calcula este codigo, no el modelo: un modelo que "calcula" la linea de un
archivo que no puede leer la inventa.

🔴 La salida tiene once campos y ni uno mas (`CAMPOS`). No hay `value`, ni `rawLine`, ni nada
que traiga un pedazo del archivo: una linea cruda del `.env` es un secreto con su nombre al
lado. El valor se mira para decir si esta cargado, y se tira.

🔴 El `.env` se recorre con el parser de `integraciones/almacen.py`. Un segundo parser con
reglas parecidas encuentra la variable en otra linea que la que lee `AlmacenSecretos.get`.
"""
import io
import json
import os
import re
import sys

try:
    from urllib.parse import quote
except ImportError:                                    # pragma: no cover - Python 2
    from urllib import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integraciones import almacen                      # noqa: E402
from integraciones.config import es_clave_de_secreto   # noqa: E402
from . import requeridos                               # noqa: E402

# `vscodeUri` es un enlace que abre el archivo en esa linea. No es una integracion nativa
# con VS Code: la Context Bar sigue siendo de la terminal (docs/cambios/bloque-1-context-bar).
CAMPOS = ("inputId", "file", "absolutePath", "line", "column", "key", "present", "format",
          "sensitivity", "vscodeUri", "fallback")
PROHIBIDOS = ("value", "rawline", "token", "password", "secret", "credential")

SECRET = "SECRET"
PUBLIC_CONFIG = "PUBLIC_CONFIG"

FORMATO_SIN_RESOLVER = "INPUT_FORMAT_UNRESOLVED"
SIN_DESTINO = "INPUT_NOT_PERSISTENT"
ILEGIBLE = "INPUT_FILE_UNREADABLE"

# Como se escribe una clave en cada formato. `{k}` es la clave, `{v}` el placeholder.
SINTAXIS = {
    "dotenv": "{k}={v}",
    "json": '"{k}": "{v}"',
    "yaml": '{k}: "{v}"',
    "toml": '{k} = "{v}"',
    "properties": "{k}={v}",
    "ini": "{k} = {v}",
}

# Como se encuentra la clave en un formato que no es el `.env`: al principio de la linea,
# sin mirar secciones. `(.*)` es el resto, que se mira para `present` y se tira.
_CLAVE_EN = {
    "json": lambda k: re.compile(r'^(\s*)"%s"\s*:(.*)$' % re.escape(k)),
    "yaml": lambda k: re.compile(r"^()%s\s*:(.*)$" % re.escape(k)),
    "toml": lambda k: re.compile(r"^(\s*)%s\s*=(.*)$" % re.escape(k)),
    "properties": lambda k: re.compile(r"^(\s*)%s\s*[=:](.*)$" % re.escape(k)),
    "ini": lambda k: re.compile(r"^(\s*)%s\s*=(.*)$" % re.escape(k)),
}


class EntradaNoUbicable(Exception):
    """No se puede ubicar. Lleva el codigo adelante y nunca un pedazo del archivo."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


# -- la URI --------------------------------------------------------------------

def ruta_con_barras(ruta_absoluta):
    """`C:\\Work\\app\\.env` -> `C:/Work/app/.env`, con la unidad en mayuscula."""
    ruta = str(ruta_absoluta).replace("\\", "/")
    if re.match(r"^[A-Za-z]:", ruta):
        ruta = ruta[0].upper() + ruta[1:]
    return ruta


def uri_de(ruta_absoluta, linea, columna):
    """(vscodeUri, fallback). No toca el disco: la misma entrada da siempre lo mismo."""
    ruta = ruta_con_barras(ruta_absoluta)
    codificada = quote(ruta, safe="/:")
    uri = "vscode://file%s%s:%d:%d" % ("" if codificada.startswith("/") else "/", codificada,
                                       linea, columna)
    return uri, "%s:%d:%d" % (ruta, linea, columna)


# -- la sensibilidad -----------------------------------------------------------

def _sensibilidad_del_contrato(variable, contrato):
    """La del contrato de entorno. Una bandera `HARNESS_*_ENABLED` es publica."""
    for integ in contrato.get("integrations") or []:
        if (integ.get("enabled") or {}).get("env") == variable:
            return PUBLIC_CONFIG
        for campo in integ.get("fields") or []:
            if campo.get("env") == variable:
                return campo.get("classification")
    return None


def sensibilidad(destino, contrato=None):
    """SECRET o PUBLIC_CONFIG. Una clave con forma de secreto es SECRET diga lo que diga."""
    if destino["format"] == "dotenv":
        if contrato is None:
            from integraciones import entorno
            contrato = entorno.cargar_contrato()
        declarada = _sensibilidad_del_contrato(destino["key"], contrato)
    else:
        declarada = destino.get("sensitivity")
    if declarada != PUBLIC_CONFIG or es_clave_de_secreto(destino["key"]):
        return SECRET
    return PUBLIC_CONFIG


# -- la linea ------------------------------------------------------------------

def _lineas(ruta):
    """Las lineas del archivo, o None si no existe. El error no lleva ningun byte."""
    try:
        return almacen.leer_lineas(ruta) if os.path.exists(ruta) else None
    except almacen.ErrorDeAlmacen:
        raise EntradaNoUbicable(ILEGIBLE, "no se pudo leer %s. Revisalo a mano."
                                % os.path.basename(ruta))


def _cargado(resto):
    """Si lo que sigue a la clave es un valor que sirve. Se mira y se tira."""
    valor = resto.strip().rstrip(",").strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1]
    return not almacen.es_valor_vacio(valor) and valor not in ("null", "~")


def _posicion(lineas, destino):
    """(linea, columna, present). Si la clave no esta, donde agregarla sin romper nada."""
    formato, clave = destino["format"], destino["key"]
    if lineas is None:
        return 1, 1, False
    if formato == "dotenv":
        for numero, columna, nombre, cargada in almacen.posiciones(lineas):
            if nombre == clave:
                return numero, columna, cargada
        return len(lineas) + 1, 1, False
    patron = _CLAVE_EN[formato](clave)
    for numero, linea in enumerate(lineas, 1):
        m = patron.match(linea)
        if m:
            return numero, len(m.group(1)) + 1, _cargado(m.group(2))
    if formato == "json":
        # Adentro del objeto, justo despues de la llave que lo abre: agregar ahi con su coma
        # es valido haya o no otras claves.
        for numero, linea in enumerate(lineas, 1):
            if "{" in linea:
                return numero + 1, 1, False
        return 1, 1, False
    return len(lineas) + 1, 1, False


def localizar(input_id, proyecto, registro=None, contrato=None):
    """La ubicacion de un input persistente, con exactamente los campos de `CAMPOS`."""
    registro = registro if registro is not None else requeridos.cargar()
    entrada = requeridos.buscar(registro, input_id)
    if entrada is None or entrada.get("persistentTarget") is None:
        raise EntradaNoUbicable(SIN_DESTINO, "%s no se completa en un archivo." % input_id)
    destino = entrada["persistentTarget"]
    if requeridos.es_generado(destino["file"]):
        raise EntradaNoUbicable(requeridos.NO_ES_HUMANO,
                                "%s lo genera el harness: no se edita a mano." % destino["file"])
    if destino["format"] not in SINTAXIS:
        raise EntradaNoUbicable(FORMATO_SIN_RESOLVER, "no se sabe ubicar el formato %s."
                                % destino["format"])
    absoluta = os.path.abspath(os.path.join(proyecto, *destino["file"].split("/")))
    linea, columna, cargada = _posicion(_lineas(absoluta), destino)
    uri, respaldo = uri_de(absoluta, linea, columna)
    salida = {"inputId": input_id,
              "file": destino["file"],
              "absolutePath": ruta_con_barras(absoluta),
              "line": linea,
              "column": columna,
              "key": destino["key"],
              "present": cargada,
              "format": destino["format"],
              "sensitivity": sensibilidad(destino, contrato),
              "vscodeUri": uri,
              "fallback": respaldo}
    return controlar(salida)


def controlar(salida):
    """La salida, si tiene exactamente sus campos. Si no, levanta: no se entrega de mas."""
    if tuple(sorted(salida)) != tuple(sorted(CAMPOS)):
        raise EntradaNoUbicable(SIN_DESTINO, "la ubicacion no tiene la forma del contrato.")
    return salida


# -- la instruccion ------------------------------------------------------------

def placeholder(clave):
    """`JIRA_TOKEN` -> `<jira-token>`. Un placeholder que se pega tal cual sigue siendo ausente."""
    return "<%s>" % clave.lower().replace("_", "-")


def sintaxis(formato, clave):
    if formato not in SINTAXIS:
        raise EntradaNoUbicable(FORMATO_SIN_RESOLVER, "no se sabe escribir el formato %s."
                                % formato)
    return SINTAXIS[formato].format(k=clave, v=placeholder(clave))


def renderizar(ubicacion, revalidar=""):
    """La instruccion para la persona, en espanol. Nunca lleva un valor: no lo conoce."""
    linea = sintaxis(ubicacion["format"], ubicacion["key"])
    texto = ["%s `%s`." % ("Falta" if not ubicacion["present"] else "Revisá", ubicacion["key"]),
             "",
             "Abrí:",
             "",
             "    %s" % ubicacion["vscodeUri"],
             "",
             "Si el enlace no abre, el archivo es %s" % ubicacion["fallback"],
             "",
             "Agregá o reemplazá:",
             "",
             "    %s" % linea]
    if ubicacion["format"] == "json":
        texto.append("")
        texto.append("Con una coma al final si no es la última clave del objeto.")
    if ubicacion["sensitivity"] == SECRET:
        texto.append("")
        texto.append("No pegues el valor en este chat.")
    texto.append("")
    texto.append("Guardá el archivo y después revalidamos%s."
                 % (" con `%s`" % revalidar if revalidar else ""))
    return "\n".join(texto)


def como_json(ubicacion):
    """El JSON canonico de una ubicacion: claves ordenadas, la misma entrada da los mismos bytes."""
    return json.dumps(controlar(ubicacion), ensure_ascii=False, sort_keys=True)
