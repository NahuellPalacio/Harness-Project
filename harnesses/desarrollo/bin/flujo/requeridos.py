"""El registro de inputs del flujo: que necesita cada etapa y como se consigue si falta.

Vive en `reglas/flow-required-inputs.json`, se instala con el harness y se pisa en cada
`-Update`. Este modulo lo carga y valida lo que el subconjunto de JSON Schema no puede
expresar: que la clasificacion, el bloqueo y la pregunta no se contradigan, y que una
variable del `.env` sea una del contrato de entorno.

🔴 La sensibilidad de una variable del `.env` sale de integration-environment-contract, no
de aca. Declararla dos veces es tener dos autoridades para el mismo dato, y la segunda es la
que un dia dice PUBLIC_CONFIG de un token.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

VERSION = "flow-required-inputs/1.0"
ARCHIVO = "flow-required-inputs.json"
SCHEMA = "flow-required-inputs.schema.json"

HARD_BLOCKER = "HARD_BLOCKER"
SOFT_DEPENDENCY = "SOFT_DEPENDENCY"
OPTIONAL = "OPTIONAL"
DERIVABLE = "DERIVABLE"

PERSISTENT_CONFIG_INPUT = "PERSISTENT_CONFIG_INPUT"
TASK_INPUT = "TASK_INPUT"
HUMAN_DECISION = "HUMAN_DECISION"

INVALIDO = "FLOW_REQUIRED_INPUTS_INVALID"
NO_ES_HUMANO = "FLOW_INPUT_TARGET_NOT_HUMAN"

# Lo que escribe el harness. Nunca es input de una persona: desde 0.26.0 la proyeccion de
# las integraciones se genera del `.env` (docs/cambios/entorno-primero/spec.md).
GENERADOS = ("harness.integraciones.json", "harness.capacidades.json")


class RegistroInvalido(Exception):
    """El registro no se usa a medias. Lleva el codigo canonico adelante."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


def es_generado(archivo):
    """Si el archivo es una salida del harness, se escriba como se escriba la ruta."""
    nombre = str(archivo or "").replace("\\", "/").rstrip("/").split("/")[-1]
    return nombre.lower() in GENERADOS


def ruta(desde=__file__):
    from orquestacion import roster
    return roster.ruta_de_regla(ARCHIVO, desde)


def _schema(desde):
    ruta_ = rutas.localizar(("schemas", SCHEMA), desde)
    if ruta_ is None:
        raise RegistroInvalido(INVALIDO, "no esta %s: el registro no se usa sin su contrato."
                               % SCHEMA)
    with io.open(ruta_, encoding="utf-8") as f:
        return json.load(f)


def _variables_de_entorno(contrato):
    from integraciones import entorno
    if contrato is None:
        contrato = entorno.cargar_contrato()
    return set(entorno.variables_del_contrato(contrato))


def validar(doc, contrato=None, desde=__file__):
    """Lista de errores. Vacia es valido. `contrato` es el de entorno; None lo carga."""
    from orquestacion import refutacion
    armador = refutacion._armador()
    esquema = _schema(desde)
    armador.controlar_soporte(esquema)
    errores = list(armador.validar(doc, esquema))
    if errores:
        return errores
    variables = _variables_de_entorno(contrato)
    vistos = set()
    for i, e in enumerate(doc["inputs"]):
        donde = "$.inputs[%d] (%s)" % (i, e["inputId"])
        if (e["stage"], e["inputId"]) in vistos:
            errores.append("%s: repetido en %s" % (donde, e["stage"]))
        vistos.add((e["stage"], e["inputId"]))
        clase, destino = e["classification"], e["persistentTarget"]
        if clase == HARD_BLOCKER and not e["blocking"]:
            errores.append("%s: un HARD_BLOCKER que no bloquea" % donde)
        if clase in (SOFT_DEPENDENCY, OPTIONAL) and e["blocking"]:
            errores.append("%s: un %s que bloquea" % (donde, clase))
        if clase == DERIVABLE:
            if e["askUser"]:
                errores.append("%s: a un DERIVABLE no se le pregunta a nadie" % donde)
            if not e["derivableFrom"]:
                errores.append("%s: un DERIVABLE sin derivableFrom" % donde)
        elif e["interactionType"] is None:
            errores.append("%s: sin interactionType y no es DERIVABLE" % donde)
        if e["interactionType"] == PERSISTENT_CONFIG_INPUT:
            if destino is None:
                errores.append("%s: un PERSISTENT_CONFIG_INPUT sin persistentTarget" % donde)
            if e["askUser"]:
                errores.append("%s: un PERSISTENT_CONFIG_INPUT se completa en un archivo, no "
                               "en el chat" % donde)
        elif destino is not None:
            errores.append("%s: persistentTarget va solo en un PERSISTENT_CONFIG_INPUT" % donde)
        if destino is None:
            continue
        if es_generado(destino["file"]):
            errores.append("%s: %s apunta a %s, que genera el harness y no es input humano"
                           % (NO_ES_HUMANO, donde, destino["file"]))
        if destino["format"] == "dotenv":
            if destino["key"] not in variables:
                errores.append("%s: %s no es una variable de integration-environment-contract"
                               % (donde, destino["key"]))
            if "sensitivity" in destino:
                errores.append("%s: la sensibilidad de una variable del .env sale del contrato"
                               % donde)
        elif "sensitivity" not in destino:
            errores.append("%s: fuera del .env, el destino declara su sensitivity" % donde)
    return errores


_CACHE = {}


def cargar(desde=__file__):
    """El registro de la instalacion, validado. Levanta RegistroInvalido si no sirve."""
    ruta_ = ruta(desde)
    if ruta_ is None:
        raise RegistroInvalido(INVALIDO, "no esta %s. Instalá de nuevo con install.ps1." % ARCHIVO)
    llave = (ruta_, os.path.getmtime(ruta_))
    if llave not in _CACHE:
        try:
            with io.open(ruta_, encoding="utf-8-sig") as f:
                doc = json.load(f)
        except (OSError, ValueError):
            raise RegistroInvalido(INVALIDO, "%s no es un JSON legible." % ruta_)
        _CACHE[llave] = comprobar(doc, desde=desde)
    return _CACHE[llave]


def comprobar(doc, contrato=None, desde=__file__):
    """El documento, si valida. Si no, RegistroInvalido con el codigo que corresponde."""
    errores = validar(doc, contrato, desde)
    if errores:
        codigo = NO_ES_HUMANO if any(x.startswith(NO_ES_HUMANO) for x in errores) else INVALIDO
        raise RegistroInvalido(codigo, "; ".join(errores[:4]))
    return doc


def de_etapa(doc, etapa):
    """Los inputs de una etapa, en el orden del registro."""
    return [e for e in doc["inputs"] if e["stage"] == etapa]


def buscar(doc, input_id):
    """El primero con ese id, de cualquier etapa, o None."""
    for e in doc["inputs"]:
        if e["inputId"] == input_id:
            return e
    return None
