"""El Tool Registry: que tools hay, en que version y en que punto de su vida.

Vive en `.claude/harness.tools.json`, al lado de `harness.capacidades.json`. El Capability
Registry contesta que capacidades DA el harness; este contesta con QUE las da.

🔴 **Nada entra con una validacion en rojo, y `NOT_RUN` no es verde.** Una etapa que nadie
pudo correr no dice que la tool ande: dice que nadie la miro. Hoy `sandbox` sale `NOT_RUN`
en toda corrida real porque el harness no tiene entorno aislado, y esa diferencia tiene que
quedar escrita en la entrada — un booleano `sandboxValidated: false` se lee igual que uno
que fallo, y no son lo mismo.

🔴 **Una tool generada nace TEMPORARY o EXPERIMENTAL.** APPROVED no se alcanza pasando los
propios tests: lo mueve otro, con evidencia.

🔴 **La misma `name@version` con otro contrato se rechaza.** El contrato es lo que otras
skills atan; pisarlo en el lugar rompe a distancia y sin ruido. Se sube la major y conviven.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from contexto import limpieza                    # noqa: E402
from . import tools                              # noqa: E402

VERSION_SCHEMA = "tool-registry/1.0"
ARCHIVO = "harness.tools.json"

NO_SELECCIONABLES = ("DEPRECATED", "RETIRED")


class RegistroInvalido(Exception):
    """El registro no se escribe a medias."""


def vacio():
    return {"schema_version": VERSION_SCHEMA, "tools": []}


def ruta_por_defecto(raiz_proyecto):
    return os.path.join(raiz_proyecto, ".claude", ARCHIVO)


def cargar(ruta):
    """El registro, o uno vacio si todavia no existe. Un registro ausente no es un error."""
    if not ruta or not os.path.isfile(ruta):
        return vacio()
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, ValueError) as e:
        raise RegistroInvalido("%s no se pudo leer: %s" % (ruta, e))
    if not isinstance(datos, dict):
        raise RegistroInvalido("%s no tiene la forma de un registro" % ruta)
    datos.setdefault("schema_version", VERSION_SCHEMA)
    datos.setdefault("tools", [])
    return datos


def validar(documento):
    """Lista de errores contra tool-registry/1.0. Vacia es valido."""
    armador = tools._armador()
    if armador is None:
        raise RegistroInvalido(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = tools.cargar_schema("tool-registry.schema.json")
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def _limpiar(documento):
    """Redacta el documento ENTERO antes de escribirlo. Devuelve los hallazgos.

    🔴 Recorre las claves del documento, no una lista de campos por nombre. Es la leccion
    que el Bloque 2 aprendio, el Bloque 3 volvio a romper un bloque despues con una lista de
    cuatro nombres, y que no se vuelve a escribir de la forma vieja: el campo numero veinte
    lo agrega alguien que no leyo esta discusion.
    """
    catalogo = limpieza.cargar_catalogo()
    if catalogo is None:
        return []
    hallazgos = []
    for clave in list(documento):
        limpio, h = limpieza.redactar_arbol(documento[clave], catalogo, "$." + clave)
        documento[clave] = limpio
        hallazgos.extend(h)
    return hallazgos


def escribir(documento, ruta):
    """Valida, limpia y escribe. Devuelve los hallazgos de limpieza."""
    hallazgos = _limpiar(documento)
    errores = validar(documento)
    if errores:
        raise RegistroInvalido(
            "el registro no valida contra %s:\n  - %s"
            % (VERSION_SCHEMA, "\n  - ".join(errores[:5])))
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8") as f:
        f.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True))
        f.write(u"\n")
    return hallazgos


# -- consultas -----------------------------------------------------------------

def seleccionables(documento):
    """Las que se pueden elegir para trabajo nuevo. DEPRECATED y RETIRED no."""
    return [e for e in (documento.get("tools") or [])
            if e.get("lifecycle") not in NO_SELECCIONABLES]


def para_capacidad(documento, capacidad):
    """Las tools seleccionables que declaran esa capacidad, de mayor a menor version."""
    hay = [e for e in seleccionables(documento)
           if capacidad in (e.get("capabilities") or [])]
    return sorted(hay, key=lambda e: _clave_version(e.get("version", "0.0.0")), reverse=True)


def buscar(documento, nombre, version):
    for entrada in documento.get("tools") or []:
        if entrada.get("name") == nombre and entrada.get("version") == version:
            return entrada
    return None


def capacidades_que_da(documento):
    """Lo que el registro aporta al Capability Registry. Solo lo seleccionable."""
    salida = set()
    for entrada in seleccionables(documento):
        salida.update(entrada.get("capabilities") or [])
    return sorted(salida)


def _clave_version(version):
    try:
        return tuple(int(p) for p in version.split("."))
    except (AttributeError, ValueError):
        return (0, 0, 0)


# -- alta ----------------------------------------------------------------------

def entrada_de(contrato, validaciones, lifecycle="TEMPORARY", registrado_en=""):
    """La entrada del registro que le corresponde a un contrato."""
    return {
        "name": contrato.get("name"),
        "version": contrato.get("version"),
        "lifecycle": lifecycle,
        "capabilities": list(contrato.get("capabilities") or []),
        "sideEffects": contrato.get("sideEffects"),
        "riskLevel": contrato.get("riskLevel"),
        "permissions": list(contrato.get("permissions") or []),
        "secretsRequired": list(contrato.get("secretsRequired") or []),
        "blastRadius": dict(contrato.get("blastRadius") or {}),
        "validations": dict(validaciones or {}),
        "contractHash": tools.hash_de_contrato(contrato),
        "registeredAt": registrado_en,
    }


def registrar(documento, contrato, validaciones, lifecycle="TEMPORARY", registrado_en="",
              desde=None):
    """Agrega la tool al registro en memoria. Levanta y no toca nada si algo no da.

    Cinco razones para no registrar, y ninguna se degrada a aviso: el contrato no vale, el
    riesgo declarado es menor que el real, los permisos exceden la capacidad, alguna
    validacion esta en FAIL, o ya hay una `name@version` con otro contrato.
    """
    veredicto = tools.evaluar(contrato, desde or tools.__file__)
    if veredicto["status"] != "OK":
        raise RegistroInvalido(
            "%s: %s" % (veredicto["status"], "; ".join(veredicto["errors"]) or "sin detalle"))

    if lifecycle not in tools.AL_NACER:
        raise RegistroInvalido(
            "una tool generada entra %s, no %s. A APPROVED se llega con evidencia y lo mueve "
            "otro." % (" o ".join(tools.AL_NACER), lifecycle))

    faltan = [e for e in tools.ETAPAS_PIPELINE if e not in (validaciones or {})]
    if faltan:
        raise RegistroInvalido(
            "faltan etapas del pipeline en las validaciones: %s. Una etapa que no se declara "
            "es una etapa que nadie sabe si corrio." % ", ".join(faltan))

    invalidas = sorted(e for e, r in (validaciones or {}).items()
                       if r not in tools.RESULTADOS_ETAPA)
    if invalidas:
        raise RegistroInvalido(
            "resultado de etapa desconocido en: %s. Los valores son %s."
            % (", ".join(invalidas), ", ".join(tools.RESULTADOS_ETAPA)))

    fallidas = sorted(e for e, r in (validaciones or {}).items() if r == "FAIL")
    if fallidas:
        raise RegistroInvalido(
            "no se registra con validaciones en rojo: %s." % ", ".join(fallidas))

    nueva = entrada_de(contrato, validaciones, lifecycle, registrado_en)
    ya = buscar(documento, nueva["name"], nueva["version"])
    if ya is not None:
        if ya.get("contractHash") != nueva["contractHash"]:
            raise RegistroInvalido(
                "%s@%s ya esta registrada con otro contrato. Un contrato distinto es una "
                "version distinta: se sube la version, no se pisa la que otros atan."
                % (nueva["name"], nueva["version"]))
        return documento

    documento.setdefault("tools", []).append(nueva)
    return documento


def promover(documento, nombre, version, hacia, por_quien="", evidencia=None):
    """Mueve el ciclo de vida de una entrada. Levanta si la transicion no corresponde."""
    entrada = buscar(documento, nombre, version)
    if entrada is None:
        raise RegistroInvalido("%s@%s no esta en el registro" % (nombre, version))

    if hacia == "PROMOTION_CANDIDATE":
        listo, faltan = tools.puede_promover(evidencia, entrada.get("validations"))
        if not listo:
            raise RegistroInvalido(
                "sin evidencia de %s no se promueve: una evidencia parcial es como una tool "
                "temporal se vuelve permanente sin que nadie lo decida." % ", ".join(faltan))

    entrada["lifecycle"] = tools.transicionar(entrada.get("lifecycle"), hacia, por_quien)
    if por_quien:
        entrada["promotedBy"] = por_quien
    return entrada
