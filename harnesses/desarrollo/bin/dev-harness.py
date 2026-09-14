#!/usr/bin/env python3
"""El bootstrap del harness de desarrollo: configurar, validar y descubrir.

    python .claude/harness/bin/desarrollo/dev-harness.py setup
    python .claude/harness/bin/desarrollo/dev-harness.py estado [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py reconfigurar jira|gitlab

Contesta una sola pregunta: que integraciones hay configuradas, cuales funcionan y
que capacidades se pueden usar. Lo que se haga despues con esas capacidades no es de
este archivo.

🔴 Este es el unico modulo que habla con la persona, y por eso es el unico que
imprime. Los adapters devuelven datos; si ellos imprimieran, cada uno seria una ruta
posible de fuga de un token.

🔴 El token no entra nunca por la linea de comandos. Un argumento queda en el
historial del shell, en la lista de procesos, en la transcripcion de una sesion de
Claude Code y en el texto que inspecciona el hook de PreToolUse. Se pide por getpass,
que no hace eco.

Codigos de salida:

    0  el bootstrap corrio. Puede haber integraciones caidas: eso no voltea al harness
    2  falla del harness que la persona tiene que arreglar antes de seguir
"""
import argparse
import getpass
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integraciones import base                                    # noqa: E402
from integraciones.almacen import AlmacenSecretos, ErrorDeAlmacen  # noqa: E402
from integraciones.config import ConfigIntegraciones, ConfigIlegible, ClaveProhibida  # noqa: E402
from integraciones.gitlab import IntegracionGitLab                # noqa: E402
from integraciones.jira import IntegracionJira                    # noqa: E402
from integraciones.registro import RegistroCapacidades            # noqa: E402

CLASES = (IntegracionJira, IntegracionGitLab)
NOMBRES = tuple(c.nombre for c in CLASES)

TIMEOUT_POR_DEFECTO = 5

# Etiqueta de cada campo que se le pide a la persona. Lo que no esta acá no se
# pregunta: el token va aparte, por getpass.
ETIQUETAS = {
    "baseUrl": "Base URL",
    "usuario": "Usuario / email",
}


class FallaDelHarness(Exception):
    """Sale con codigo 2. Nunca lleva un secreto adentro."""


# -- salida --------------------------------------------------------------------

class Consola(object):
    """Con --json el stdout queda para el documento y todo lo demas va a stderr."""

    def __init__(self, como_json):
        self.destino = sys.stderr if como_json else sys.stdout

    def linea(self, texto=""):
        self.destino.write(texto + "\n")
        self.destino.flush()

    def evento(self, nombre, **datos):
        partes = ["evento=%s" % nombre]
        partes += ["%s=%s" % (k, datos[k]) for k in sorted(datos)]
        self.linea("  " + " ".join(partes))


# -- rutas y contexto ----------------------------------------------------------

def rutas_de(proyecto):
    claude = os.path.join(proyecto, ".claude")
    return {
        "env": os.path.join(proyecto, ".env"),
        "config": os.path.join(claude, "harness.integraciones.json"),
        "capacidades": os.path.join(claude, "harness.capacidades.json"),
        "harness_config": os.path.join(claude, "harness.config.json"),
        "lock": os.path.join(claude, "harness.lock.json"),
    }


def _json_o_vacio(ruta):
    if not os.path.isfile(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (ValueError, OSError):
        return {}


def timeout_de(rutas):
    valor = _json_o_vacio(rutas["harness_config"]).get("timeoutIntegraciones", TIMEOUT_POR_DEFECTO)
    try:
        return max(1, int(valor))
    except (TypeError, ValueError):
        return TIMEOUT_POR_DEFECTO


def version_de(rutas):
    return str(_json_o_vacio(rutas["lock"]).get("version", ""))


def armar(clase, config, almacen, timeout, transporte=None):
    return clase(config.de(clase.nombre), almacen, timeout, transporte)


# -- preguntas -----------------------------------------------------------------

def _exigir_terminal():
    if not sys.stdin.isatty():
        raise FallaDelHarness(
            "el setup necesita una terminal interactiva para pedir las credenciales, y la "
            "entrada esta redirigida. Corrélo a mano en tu consola.")


def _preguntar(texto, valor_actual=""):
    sufijo = " [%s]" % valor_actual if valor_actual else ""
    while True:
        respuesta = input("%s%s: " % (texto, sufijo)).strip()
        if respuesta:
            return respuesta
        if valor_actual:
            return valor_actual


def _preguntar_si(texto):
    respuesta = input("%s [S/n]: " % texto).strip().lower()
    return respuesta in ("", "s", "si", "sí", "y", "yes")


def configurar(clase, config, almacen, consola):
    """Pide lo que falta de una integracion y lo guarda. El token va al almacen."""
    _exigir_terminal()
    bloque = dict(config.de(clase.nombre))
    consola.linea("")
    consola.linea(clase.etiqueta)

    if not _preguntar_si("  ¿Configurar %s?" % clase.etiqueta):
        bloque["enabled"] = False
        config.guardar(clase.nombre, bloque)
        consola.evento("integracion.deshabilitada", integracion=clase.nombre)
        return

    for campo in clase.campos:
        etiqueta = ETIQUETAS.get(campo, campo)
        bloque[campo] = _preguntar("  " + etiqueta, str(bloque.get(campo, "") or ""))
    bloque["enabled"] = True
    config.guardar(clase.nombre, bloque)

    if almacen.exists(clase.clave_token):
        if not _preguntar_si("  Ya hay un token cargado. ¿Reemplazarlo?"):
            consola.evento("integracion.configurada", integracion=clase.nombre)
            return

    token = getpass.getpass("  API Token (no se muestra): ").strip()
    if not token:
        raise FallaDelHarness("no se cargo ningun token para %s: el setup no puede seguir."
                              % clase.etiqueta)
    almacen.set(clase.clave_token, token)
    del token
    consola.evento("integracion.configurada", integracion=clase.nombre)


def hay_que_preguntar(clase, config, almacen):
    """Primera corrida o configuracion incompleta. Un `false` explicito es una decision."""
    bloque = config.de(clase.nombre)
    if bloque.get("enabled") is None:
        return True
    if not bloque.get("enabled"):
        return False
    return bool(armar(clase, config, almacen, 1).campos_faltantes())


# -- el bootstrap --------------------------------------------------------------

def correr_bootstrap(config, almacen, timeout, consola, transporte=None):
    registro = RegistroCapacidades({c.nombre: c.CAPACIDADES for c in CLASES})
    for clase in CLASES:
        integracion = armar(clase, config, almacen, timeout, transporte)
        consola.evento("validacion.inicio", integracion=clase.nombre)
        resultado = integracion.estado()
        if resultado["estado"] == base.AVAILABLE:
            consola.evento("validacion.ok", integracion=clase.nombre,
                           capacidades=len(resultado["capacidades"]))
        else:
            consola.evento("validacion.falla", integracion=clase.nombre,
                           estado=resultado["estado"])
        registro.anotar(clase.nombre, resultado)
    for capacidad in registro.soportadas():
        consola.evento("capacidad.habilitada" if registro.esta_disponible(capacidad)
                       else "capacidad.deshabilitada", capacidad=capacidad)
    return registro


def mostrar(consola, documento):
    ancho = max(len(c.etiqueta) for c in CLASES) + 2
    consola.linea("")
    consola.linea("GCBA Development Harness")
    consola.linea("")
    consola.linea("Integraciones")
    consola.linea("-" * 48)
    for clase in CLASES:
        datos = documento["integraciones"][clase.nombre]
        consola.linea("%s%s" % (clase.etiqueta.ljust(ancho), datos["estado"]))
        if datos["motivo"]:
            consola.linea("  " + datos["motivo"])
    consola.linea("")
    consola.linea("Capacidades")
    consola.linea("-" * 48)
    for capacidad, situacion in sorted(documento["capacidades"].items()):
        consola.linea("  %-9s %s" % (situacion, capacidad))
    consola.linea("")
    consola.linea("Estado")
    consola.linea("-" * 48)
    consola.linea("HARNESS READY")
    caidas = [c.etiqueta for c in CLASES
              if documento["integraciones"][c.nombre]["estado"] != base.AVAILABLE]
    if caidas:
        consola.linea("Sin: %s. Sus capacidades quedan deshabilitadas; el resto del harness "
                      "funciona." % ", ".join(caidas))
        consola.linea("Para reconfigurar: dev-harness.py reconfigurar <%s>" % "|".join(NOMBRES))


# -- comandos ------------------------------------------------------------------

def comando(args, transporte=None):
    proyecto = os.path.abspath(args.proyecto)
    if not os.path.isdir(proyecto):
        raise FallaDelHarness("el proyecto %s no existe." % proyecto)

    rutas = rutas_de(proyecto)
    consola = Consola(args.json)
    config = ConfigIntegraciones(rutas["config"])
    almacen = AlmacenSecretos(rutas["env"])
    timeout = timeout_de(rutas)

    if args.comando == "reconfigurar":
        configurar(dict((c.nombre, c) for c in CLASES)[args.integracion],
                   config, almacen, consola)
    elif args.comando == "setup":
        primera = not os.path.isfile(rutas["config"])
        consola.linea("GCBA Development Harness — %s" % (
            "configuracion inicial" if primera else "configuracion existente"))
        for clase in CLASES:
            if hay_que_preguntar(clase, config, almacen):
                configurar(clase, config, almacen, consola)

    consola.linea("")
    registro = correr_bootstrap(config, almacen, timeout, consola, transporte)
    documento = registro.escribir(rutas["capacidades"], version_de(rutas))
    consola.evento("harness.listo", disponibles=len(registro.disponibles()))

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        mostrar(consola, documento)
    return 0


def parser():
    p = argparse.ArgumentParser(
        prog="dev-harness.py",
        description="Bootstrap de las integraciones del harness de desarrollo.")
    p.add_argument("comando", choices=("setup", "estado", "reconfigurar"))
    p.add_argument("integracion", nargs="?", choices=NOMBRES,
                   help="solo para reconfigurar")
    p.add_argument("--proyecto", default=os.getcwd(),
                   help="raiz del proyecto (por defecto, el directorio actual)")
    p.add_argument("--json", action="store_true",
                   help="el registro de capacidades por stdout, para consumirlo")
    p.add_argument("--token", default=None,
                   help=argparse.SUPPRESS)
    return p


def main(argv=None, transporte=None):
    # La consola de Windows no es UTF-8 por defecto y esta salida lleva acentos. Va acá
    # y no al importar: la suite importa este archivo, y reconfigurar la salida del
    # proceso de tests desde un import es un efecto que nadie pidió.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    args = parser().parse_args(argv)

    if args.token is not None:
        sys.stderr.write(
            "El token no se pasa por la linea de comandos: queda en el historial del shell, en "
            "la lista de procesos y en la transcripcion de la sesion. Corre `setup` y cargalo "
            "cuando te lo pida, o dejalo en la variable de entorno correspondiente.\n")
        return 2

    if args.comando == "reconfigurar" and not args.integracion:
        sys.stderr.write("reconfigurar necesita que le digas cual: %s\n" % ", ".join(NOMBRES))
        return 2

    try:
        return comando(args, transporte)
    except (FallaDelHarness, ConfigIlegible, ClaveProhibida, ErrorDeAlmacen) as e:
        sys.stderr.write("harness: %s\n" % e)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\nharness: cancelado. No se guardo nada de lo que faltaba.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
