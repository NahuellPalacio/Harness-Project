#!/usr/bin/env python3
"""La CLI del harness de desarrollo: las integraciones y el contexto de una tarea.

    python .claude/harness/bin/desarrollo/dev-harness.py setup
    python .claude/harness/bin/desarrollo/dev-harness.py estado [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py reconfigurar jira|gitlab
    python .claude/harness/bin/desarrollo/dev-harness.py contexto GCBA-1234 [--json]

Los tres primeros son el Bloque 1 y contestan una sola pregunta: que integraciones hay
configuradas, cuales funcionan y que capacidades se pueden usar.

`contexto` es el Bloque 2 y contesta otra: que hay que hacer en esta tarea, por que, a que
proyecto pertenece y cual es su estado tecnico. Consume el registro que dejo el bootstrap
y no vuelve a validar nada salvo que se lo pidan con --revalidar.

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
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integraciones import base                                    # noqa: E402
from integraciones.almacen import AlmacenSecretos, ErrorDeAlmacen  # noqa: E402
from integraciones.config import ConfigIntegraciones, ConfigIlegible, ClaveProhibida  # noqa: E402
from integraciones.gitlab import IntegracionGitLab                # noqa: E402
from integraciones.jira import IntegracionJira                    # noqa: E402
from integraciones.registro import RegistroCapacidades            # noqa: E402

from contexto import comun as contexto_comun                      # noqa: E402
from contexto import documentos as contexto_documentos            # noqa: E402
from contexto import ensamblador as contexto_ensamblador          # noqa: E402
from contexto import limpieza                                     # noqa: E402
from contexto import proyecto as contexto_proyecto                # noqa: E402
from contexto import repositorio as contexto_repositorio          # noqa: E402
from contexto import tarea as contexto_tarea                      # noqa: E402

CLASES = (IntegracionJira, IntegracionGitLab)
NOMBRES = tuple(c.nombre for c in CLASES)

TIMEOUT_POR_DEFECTO = 5

CLAVE_JIRA = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")

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


# -- contexto de tarea ---------------------------------------------------------

def resolver_contexto(args, proyecto, rutas, config, almacen, timeout, consola,
                      transporte, transporte_bytes):
    """Bloque 2: de una clave de Jira a un TaskContext.

    El registro de capacidades se LEE, no se revalida: revalidar agrega entre dos y seis
    llamadas HTTP antes del trabajo real, en el camino caliente. El precio es que puede
    estar viejo, y por eso cada llamada maneja su propio fallo.
    """
    clave = args.argumento
    capacidades = _json_o_vacio(rutas["capacidades"]).get("capacidades") or {}

    if args.revalidar or not capacidades:
        if not capacidades:
            consola.linea("No hay registro de capacidades todavia: se valida una vez.")
        registro = correr_bootstrap(config, almacen, timeout, consola, transporte)
        documento = registro.escribir(rutas["capacidades"], version_de(rutas))
        capacidades = documento["capacidades"]
        consola.linea("")

    jira = armar(IntegracionJira, config, almacen, timeout, transporte)
    gitlab = armar(IntegracionGitLab, config, almacen, timeout, transporte)
    jira.transporte_bytes = transporte_bytes
    gitlab.transporte_bytes = transporte_bytes

    acumulador = contexto_comun.Acumulador(capacidades)
    consola.evento("contexto.inicio", tarea=clave)

    try:
        task, campos_tarea = contexto_tarea.resolver(jira, clave, CATALOGO(),
                                                     _config_harness(rutas), acumulador)
    except contexto_tarea.TareaNoResuelta as e:
        raise FallaDelHarness(str(e))
    consola.evento("contexto.tarea", tipo=task["type"] or "sin-tipo")

    project, campos_ficha = contexto_proyecto.resolver(
        jira, campos_tarea, CATALOGO(), _config_harness(rutas), acumulador)
    consola.evento("contexto.ficha", ficha=project["ficha"]["key"] or "ninguna")

    dir_adjuntos = os.path.join(proyecto, ".claude", "contextos", clave + "-adjuntos")
    documentation = contexto_documentos.resolver(
        jira, campos_tarea, campos_ficha, CATALOGO(), _config_harness(rutas), acumulador,
        dir_adjuntos)
    consola.evento("contexto.documentos", documentos=len(documentation["items"]))

    repository = contexto_repositorio.resolver(
        gitlab, clave, config.de("gitlab"), project["ficha"], acumulador, proyecto,
        str(_config_harness(rutas).get("rutaCodebase") or "docs/codebase"))
    consola.evento("contexto.repositorio",
                   ramas=len(repository["branches"]), mrs=len(repository["merge_requests"]))

    documento = contexto_ensamblador.armar(clave, task, project, documentation, repository,
                                           acumulador, version_de(rutas), CATALOGO())
    destino = os.path.join(proyecto, ".claude", "contextos", clave + ".json")
    contexto_ensamblador.escribir(documento, destino)
    consola.evento("contexto.listo", huecos=_cuantos_huecos(documento))

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        mostrar_contexto(consola, documento, destino)
    return 0


def _cuantos_huecos(documento):
    huecos = documento["gaps_and_conflicts"]
    return sum(len(huecos[c]) for c in huecos)


def _config_harness(rutas):
    return _json_o_vacio(rutas["harness_config"])


def CATALOGO():
    """El catalogo de secretos, una vez por proceso. None si no se encontro."""
    return limpieza.cargar_catalogo()


def mostrar_contexto(consola, documento, destino):
    task = documento["task"]
    ficha = documento["project"]["ficha"]
    huecos = documento["gaps_and_conflicts"]
    consola.linea("")
    consola.linea("%s — %s" % (task["key"], task["title"] or "(sin titulo)"))
    consola.linea("-" * 60)
    consola.linea("Tipo        %s" % (task["type"] or "—"))
    consola.linea("Estado      %s" % (task["status"] or "—"))
    consola.linea("Criterios   %d" % len(task["acceptance_criteria"]))
    consola.linea("Proyecto    %s%s" % (
        documento["project"]["jira_key"] or "—",
        "  ·  ficha %s" % ficha["key"] if ficha["key"] else "  ·  sin ficha"))
    consola.linea("Documentos  %d" % len(documento["documentation"]["items"]))
    consola.linea("Repositorio %s" % (documento["repository"]["project"]["name"] or "—"))
    consola.linea("Ramas / MR  %d / %d" % (len(documento["repository"]["branches"]),
                                           len(documento["repository"]["merge_requests"])))
    consola.linea("")
    if huecos["redacted_secrets"]:
        consola.linea("Se redactaron %d secretos antes de escribir el contexto."
                      % len(huecos["redacted_secrets"]))
    total = _cuantos_huecos(documento)
    if total:
        consola.linea("Huecos declarados: %d. Estan en gaps_and_conflicts." % total)
        for linea in (huecos["conflicts"] + huecos["missing_capabilities"])[:3]:
            consola.linea("  · " + linea)
    consola.linea("")
    consola.linea("TaskContext: %s" % destino)


# -- comandos ------------------------------------------------------------------

def comando(args, transporte=None, transporte_bytes=None):
    proyecto = os.path.abspath(args.proyecto)
    if not os.path.isdir(proyecto):
        raise FallaDelHarness("el proyecto %s no existe." % proyecto)

    rutas = rutas_de(proyecto)
    consola = Consola(args.json)
    config = ConfigIntegraciones(rutas["config"])
    almacen = AlmacenSecretos(rutas["env"])
    timeout = timeout_de(rutas)

    if args.comando == "contexto":
        return resolver_contexto(args, proyecto, rutas, config, almacen, timeout,
                                 consola, transporte, transporte_bytes)

    if args.comando == "reconfigurar":
        configurar(dict((c.nombre, c) for c in CLASES)[args.argumento],
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
        description="Integraciones y contexto de tarea del harness de desarrollo.")
    p.add_argument("comando", choices=("setup", "estado", "reconfigurar", "contexto"))
    p.add_argument("argumento", nargs="?",
                   help="la integracion, para reconfigurar; la clave de Jira, para contexto")
    p.add_argument("--revalidar", action="store_true",
                   help="revalida las integraciones antes de resolver el contexto")
    p.add_argument("--proyecto", default=os.getcwd(),
                   help="raiz del proyecto (por defecto, el directorio actual)")
    p.add_argument("--json", action="store_true",
                   help="el registro de capacidades por stdout, para consumirlo")
    p.add_argument("--token", default=None,
                   help=argparse.SUPPRESS)
    return p


def main(argv=None, transporte=None, transporte_bytes=None):
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

    if args.comando == "reconfigurar" and args.argumento not in NOMBRES:
        sys.stderr.write("reconfigurar necesita que le digas cual: %s\n" % ", ".join(NOMBRES))
        return 2

    if args.comando == "contexto" and not CLAVE_JIRA.match(str(args.argumento or "")):
        sys.stderr.write(
            "contexto necesita una clave de Jira, con la forma PROYECTO-123. "
            "Ejemplo: dev-harness.py contexto GCBA-1234\n")
        return 2

    try:
        return comando(args, transporte, transporte_bytes)
    except (FallaDelHarness, ConfigIlegible, ClaveProhibida, ErrorDeAlmacen,
            contexto_ensamblador.ContratoInvalido) as e:
        sys.stderr.write("harness: %s\n" % e)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\nharness: cancelado. No se guardo nada de lo que faltaba.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
