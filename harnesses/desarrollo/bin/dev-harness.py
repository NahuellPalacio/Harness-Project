#!/usr/bin/env python3
"""La CLI del harness de desarrollo: las integraciones y el contexto de una tarea.

    python .claude/harness/bin/desarrollo/dev-harness.py setup
    python .claude/harness/bin/desarrollo/dev-harness.py estado [--json] [--resumen]
    python .claude/harness/bin/desarrollo/dev-harness.py reconfigurar jira|gitlab
    python .claude/harness/bin/desarrollo/dev-harness.py contexto GCBA-1234 [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py seguridad GCBA-1234 [--conocimiento] [--resumen] [--reporte] [--refutacion]
    python .claude/harness/bin/desarrollo/dev-harness.py refute GCBA-1234 --compile|--status|--unit REF-001|--record <v.json>|--summary
    python .claude/harness/bin/desarrollo/dev-harness.py flujo GCBA-1234 --status [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py harness [--json] [--verbose] [--reiniciar-bienvenida]
    python .claude/harness/bin/desarrollo/dev-harness.py presupuesto [--context-defaults]

Los tres primeros son el Bloque 1 y contestan una sola pregunta: que integraciones hay
configuradas, cuales funcionan y que capacidades se pueden usar. La configuracion sale del
`.env` local y de nada mas (docs/cambios/entorno-primero/spec.md): ninguno de los tres pregunta,
y `setup` y `reconfigurar` dicen que variables faltan, por nombre y sin mostrar un valor.

`contexto` es el Bloque 2 y contesta otra: que hay que hacer en esta tarea, por que, a que
proyecto pertenece y cual es su estado tecnico. Consume el registro que dejo el bootstrap
y no vuelve a validar nada salvo que se lo pidan con --revalidar.

🔴 Este es el unico modulo que habla con la persona, y por eso es el unico que
imprime. Los adapters devuelven datos; si ellos imprimieran, cada uno seria una ruta
posible de fuga de un token.

🔴 El token no entra nunca por la linea de comandos. Un argumento queda en el
historial del shell, en la lista de procesos, en la transcripcion de una sesion de
Claude Code y en el texto que inspecciona el hook de PreToolUse. Va en el `.env` local,
que Claude no puede leer, o en el entorno del proceso.

Codigos de salida:

    0  el bootstrap corrio. Puede haber integraciones caidas: eso no voltea al harness
    2  falla del harness que la persona tiene que arreglar antes de seguir
"""
import argparse
import importlib.util
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rutas as rutas_bin                                         # noqa: E402
from integraciones import base                                    # noqa: E402
from integraciones import entorno                                 # noqa: E402
from integraciones.almacen import AlmacenSecretos, ErrorDeAlmacen  # noqa: E402
from integraciones.config import ConfigIlegible, ClaveProhibida      # noqa: E402
from integraciones.gitlab import IntegracionGitLab                # noqa: E402
from integraciones.jira import IntegracionJira                    # noqa: E402
from integraciones import registro as int_registro               # noqa: E402
from integraciones.registro import RegistroCapacidades            # noqa: E402

from contexto import comun as contexto_comun                      # noqa: E402
from contexto import documentos as contexto_documentos            # noqa: E402
from contexto import ensamblador as contexto_ensamblador          # noqa: E402
from contexto import limpieza                                     # noqa: E402
from contexto import proyecto as contexto_proyecto                # noqa: E402
from contexto import repositorio as contexto_repositorio          # noqa: E402
from contexto import tarea as contexto_tarea                      # noqa: E402

from integraciones import fuentes as int_fuentes                # noqa: E402

from flujo import precondiciones as flujo_precondiciones          # noqa: E402
from flujo import requeridos as flujo_requeridos                  # noqa: E402
from flujo import estado as flujo_estado                          # noqa: E402
from estado_de_tarea import persistencia as estado_persistencia   # noqa: E402
from estado_de_tarea import decisiones as estado_decisiones       # noqa: E402

from integraciones import http as int_http                        # noqa: E402

from orquestacion import auto_refresh as orq_refresco             # noqa: E402
from orquestacion import frescura as orq_frescura                # noqa: E402
from orquestacion import plan as orq_plan                         # noqa: E402
from orquestacion import refutacion as orq_refutacion             # noqa: E402
from orquestacion import registro_fuentes as orq_fuentes         # noqa: E402
from orquestacion import roster as orq_roster                     # noqa: E402

from contabilidad import agregacion as cont_agregacion            # noqa: E402
from contabilidad import barra as cont_barra                      # noqa: E402
from contabilidad import libro as cont_libro                      # noqa: E402
from contabilidad import presentacion as cont_presentacion        # noqa: E402
from contabilidad import presupuesto as cont_presupuesto          # noqa: E402
from contabilidad import reporte as cont_reporte                  # noqa: E402
from contabilidad.adaptadores import contrato as cont_contrato    # noqa: E402
from contabilidad.adaptadores import registro as cont_registro    # noqa: E402

from reporte_seguridad import libro as seg_libro                  # noqa: E402
from reporte_seguridad import productores as seg_productores      # noqa: E402
from reporte_seguridad import reporte as seg_reporte              # noqa: E402
from reporte_seguridad import resumen as seg_resumen              # noqa: E402

CLASES = int_registro.clases()      # lo que soporta cada una: su tupla CAPACIDADES
NOMBRES = tuple(c.nombre for c in CLASES)

TIMEOUT_POR_DEFECTO = 5

CLAVE_JIRA = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")

# `--refutacion` sin valor: en `seguridad`, todas las unidades de la corrida.
TODAS_LAS_REFUTACIONES = "*"

class FallaDelHarness(Exception):
    """Sale con codigo 2. Nunca lleva un secreto adentro."""


# -- salida --------------------------------------------------------------------

class Consola(object):
    """Con --json el stdout queda para el documento y todo lo demas va a stderr."""

    def __init__(self, como_json, eventos=True):
        self.destino = sys.stderr if como_json else sys.stdout
        self.eventos = eventos

    def linea(self, texto=""):
        self.destino.write(texto + "\n")
        self.destino.flush()

    def evento(self, nombre, **datos):
        if not self.eventos:
            return
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
        # El presupuesto es un archivo aparte y NO tiene default en el manifiesto. install.ps1
        # siembra, si falta, la politica por defecto de la Context Bar: solo umbrales de
        # contexto, ningun limite de plata. Sin limite declarado el gate sigue en BUDGET_UNDEFINED.
        "presupuesto": os.path.join(claude, "harness.presupuesto.json"),
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
    """El adapter, con la configuracion publica y los nombres de variable del contrato.

    `config` es la Resolucion del `.env` (tiene `variables_de`) o, en la suite, un
    ConfigIntegraciones a mano. El token no viaja aca: el adapter lo pide al almacen.
    """
    variables = config.variables_de(clase.nombre) if hasattr(config, "variables_de") else None
    return clase(config.de(clase.nombre), almacen, timeout, transporte, variables=variables)


# -- la configuracion desde el .env ------------------------------------------------

ADAPTADORES = dict((c.nombre, c) for c in CLASES)


def resolver_configuracion(rutas):
    """Contrato -> .env -> proyeccion sanitizada. Devuelve la Resolucion.

    Es lo primero de cada comando que toca integraciones. La proyeccion se regenera cada vez
    que cambio, y una vieja no le gana nunca al `.env`: el `.env` se lee siempre.
    """
    contrato = entorno.cargar_contrato(adaptadores=ADAPTADORES)
    resolucion = entorno.resolver(contrato, rutas["env"], rutas["config"])
    entorno.escribir_proyeccion(rutas["config"], resolucion.proyeccion())
    return resolucion


def mostrar_configuracion(consola, resolucion, solo=None):
    """Que variables hay, de que capa y cuales faltan. Nombres y capas, nunca valores."""
    consola.linea("Modo de configuración: %s" % entorno.MODO)
    consola.linea("Archivo: %s (%s)" % (resolucion.ruta_env,
                                        "presente" if resolucion.env_presente else "no existe"))
    ancho = max(len(v) for v in entorno.variables_del_contrato(resolucion.contrato)) + 2
    for clase in CLASES:
        if solo and clase.nombre != solo:
            continue
        integ = resolucion.integracion(clase.nombre)
        consola.linea("")
        consola.linea(clase.etiqueta)
        for v in integ.variables:
            fuente = "" if v.fuente == entorno.NOT_CONFIGURED else v.fuente
            if v.presente and not v.valida:
                fuente += "  (valor invalido)"
            estado = "presente" if v.presente else "ausente"
            consola.linea(("  %s%s %s" % (v.nombre.ljust(ancho), estado.ljust(9), fuente)).rstrip())
        if integ.codigo and integ.codigo != entorno.ENV_REQUIRED_VARIABLE_MISSING:
            consola.linea("  " + integ.motivo(clase.etiqueta))
        legado = integ.de_legado()
        if legado:
            consola.linea("  Migración: %s sale del harness.integraciones.json viejo. Pasalo al "
                          ".env para terminar de migrar." % ", ".join(legado))
    nuevas = resolucion.variables_nuevas()
    if nuevas:
        consola.linea("")
        consola.linea("Variables nuevas del contrato: %s (ver .env.example)." % ", ".join(nuevas))


# -- el bootstrap --------------------------------------------------------------

def _sin_validar(motivo):
    """El resultado de una integracion que el resolvedor ya descarto: sin red."""
    return {"estado": base.NOT_CONFIGURED, "motivo": motivo, "verificado_en": base.ahora(),
            "capacidades": [], "diagnostico": []}


def correr_bootstrap(config, almacen, timeout, consola, transporte=None):
    registro = RegistroCapacidades({c.nombre: c.CAPACIDADES for c in CLASES},
                                   modo=entorno.MODO if hasattr(config, "integracion") else None)
    for clase in CLASES:
        integracion = armar(clase, config, almacen, timeout, transporte)
        consola.evento("validacion.inicio", integracion=clase.nombre)
        resuelta = config.integracion(clase.nombre) if hasattr(config, "integracion") else None
        codigo = resuelta.codigo if resuelta else ""
        if codigo and codigo != entorno.ENV_REQUIRED_VARIABLE_MISSING:
            # Una bandera invalida, un conflicto o un valor rechazado: el adapter no sale a la
            # red con una configuracion que el resolvedor ya dijo que no sirve.
            resultado = _sin_validar(resuelta.motivo(clase.etiqueta))
        else:
            resultado = integracion.estado()
        resultado["faltan"] = list(resuelta.faltan) if resuelta else []
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


def registrar_capacidades(config, almacen, timeout, consola, rutas, transporte=None):
    """El camino autoritativo de Environment First: una sonda por integracion con la
    configuracion que ya resolvio el `.env`, y el registro de capacidades escrito. Lo usan
    `estado`, `setup`, `reconfigurar`, `contexto --revalidar` y `flujo --resume`: uno solo."""
    registro = correr_bootstrap(config, almacen, timeout, consola, transporte)
    return registro, registro.escribir(rutas["capacidades"], version_de(rutas))


# -- el estado general del harness ----------------------------------------------

_MODULO_BIENVENIDA = []


def bienvenida():
    """comun/hooks/lib/bienvenida.py, el resolvedor unico del estado general.

    Se carga por ruta y no por import: vive en la lib de los hooks, que en el arbol instalado
    es .claude/harness/hooks/lib/ y en el repositorio comun/hooks/lib/, y ninguna de las dos
    esta en sys.path. Tampoco se agrega: `lib` es un nombre que los hooks usan como paquete.
    """
    if _MODULO_BIENVENIDA:
        return _MODULO_BIENVENIDA[0]
    raiz = rutas_bin.raiz_del_harness(__file__)
    ruta = os.path.join(raiz, "hooks", "lib", "bienvenida.py") if raiz else None
    if not ruta or not os.path.isfile(ruta):
        raise FallaDelHarness(
            "no se encontro hooks/lib/bienvenida.py al lado del harness instalado. "
            "Instalá de nuevo con install.ps1.")
    spec = importlib.util.spec_from_file_location("harness_bienvenida", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _MODULO_BIENVENIDA.append(modulo)
    return modulo


def estado_general(proyecto, rutas):
    """El documento harness-installation/1.1 de ahora. No escribe nada ni hace red."""
    return bienvenida().resolver(proyecto, _json_o_vacio(rutas["harness_config"]).get("rutaCodebase"))


def linea_de_estado(proyecto, rutas):
    """La linea compacta del resolvedor, la misma que ve la persona al abrir una sesion.

    Si el resolvedor no se pudo cargar no se inventa un estado: se dice que no se sabe.
    """
    try:
        return bienvenida().renderizar_linea(estado_general(proyecto, rutas))
    except Exception as e:                    # noqa: BLE001 - el bootstrap ya corrio
        return "Harness GCBA: no se pudo calcular el estado general (%s)" % e


def mostrar_harness(args, proyecto, rutas):
    """`harness`: el estado de ahora, sin red y sin tocar la marca de la bienvenida.

    Con --reiniciar-bienvenida es lo unico que escribe: firstRunShown false, para que la
    proxima sesion muestre la bienvenida completa.
    """
    b = bienvenida()
    if args.reiniciar_bienvenida:
        # Sin lockfile ni estado el harness no esta instalado aca: escribir el estado haria
        # aparecer una bienvenida en un proyecto que no tiene harness.
        if not b.hay_harness(proyecto):
            raise FallaDelHarness("el harness no esta instalado en %s: no hay bienvenida que "
                                  "reiniciar." % proyecto)
        doc = b.reiniciar_bienvenida(proyecto)
        destino = sys.stderr if args.json else sys.stdout
        destino.write("La próxima sesión de Claude Code muestra la bienvenida completa.\n")
    else:
        doc = estado_general(proyecto, rutas)

    if args.json:
        sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        return 0
    if args.reiniciar_bienvenida:
        return 0

    # La bienvenida sin su bloque Observabilidad: lo dice, con mas detalle, la seccion de
    # abajo, y dos veces lo mismo es ruido. El estado general no cambia: sale del documento.
    sys.stdout.write(b.renderizar_bienvenida(dict(doc, runtimeComponents={})) + "\n")
    sys.stdout.write(seccion_de_runtime(b, doc, proyecto) + "\n")
    if args.verbose:
        sys.stdout.write("\n" + detalle_verbose(b, doc, proyecto, rutas) + "\n")
    return 0


def seccion_de_runtime(b, doc, proyecto):
    """"Runtime / Observabilidad": los tres componentes, si hace falta reiniciar Claude Code y
    si la ultima sesion vista cargo la barra.

    `harness` no tiene sesion: la de ahora es la ultima que dejo senal de vida. Por eso una
    barra ACTIVE dice de que sesion, y nunca queda activa "en esta".
    """
    rc = doc.get("runtimeComponents") or {}
    lineas = ["", "Runtime / Observabilidad"]
    if not rc or not (doc.get("knowledge") or {}).get("applies"):
        lineas.append("  sin el harness de desarrollo: no hay Bloque 4, ni Context Bar, ni "
                      "reporte de seguridad")
        return "\n".join(lineas)

    ancho = len("Reinicio de Claude Code") + 3
    acciones = []
    for clave, nombre, _, _ in b.COMPONENTES:
        comp = rc.get(clave) or {}
        marca = "✓ " if comp.get("state") == b.ACTIVE else ""
        texto = b.etiqueta_de_componente(clave, comp)
        vista = comp.get("lastSessionWithData") or comp.get("lastSessionId")
        if comp.get("state") == b.ACTIVE and not comp.get("activeInCurrentSession") and vista:
            texto += " (última sesión: %s)" % str(vista)[:8]
        lineas.append("  %s%s%s" % (nombre.ljust(ancho), marca, texto))
        condicion = b.condicion_de_componente(clave, comp)
        if condicion:
            acciones.append(b.describir(condicion))

    barra = rc.get("contextBar") or {}
    lineas.append("  %s%s" % ("Reinicio de Claude Code".ljust(ancho),
                              "hace falta" if barra.get("reloadRequired") else "no hace falta"))
    senal, _ = b.leer_senal_de_vida(proyecto)
    vista = barra.get("lastSessionId")
    if vista and senal:
        lineas.append("  %s%s cargó la Context Bar (último dibujo: %s)"
                      % ("Última sesión vista".ljust(ancho), str(vista)[:8],
                         senal.get("lastRenderedAt")))
    else:
        lineas.append("  %s%s" % ("Última sesión vista".ljust(ancho),
                                  "ninguna sesión cargó la Context Bar todavía"))
    if acciones:
        lineas += ["", "Acción requerida"] + ["  " + a for a in acciones]
    return "\n".join(lineas)


def detalle_verbose(b, doc, proyecto, rutas):
    """La version, la fecha, cada condicion con su id y de que archivo sale cada dato."""
    boot = doc["bootstrap"]
    lineas = ["Detalle",
              "  Versión instalada   %s" % (doc.get("installedVersion") or "desconocida"),
              "  Instalado el        %s" % (doc.get("installedAt") or "desconocido"),
              "  Estado              %s (%s)" % (b.etiqueta(boot["status"]), boot["status"])]
    for titulo, clave in (("Lo bloquea", "blockingConditions"), ("Pendiente", "pendingConditions")):
        for c in boot.get(clave) or []:
            lineas.append("  %-19s %s — %s" % (titulo, c, b.describir(c)))
    for i in doc.get("integrations") or []:
        lineas.append("  Integración         %s %s, verificada: %s"
                      % (i["id"], i["status"], i.get("verifiedAt") or "nunca"))
    conocimiento = doc.get("knowledge") or {}
    if conocimiento.get("applies"):
        lineas.append("  Conocimiento        verificado: %s" % (conocimiento.get("verifiedAt") or "nunca"))
        for f in conocimiento.get("sources") or []:
            lineas.append("  Fuente              %s %s, aceptada %s, observada %s"
                          % (f["id"], f["state"], f.get("acceptedVersion") or "—",
                             f.get("observedVersion") or "—"))
    lineas += _detalle_de_refresco(doc)
    lineas += _detalle_de_runtime(b, doc, proyecto)
    lineas += _detalle_de_consumo(b, doc, proyecto, rutas)
    archivos = b.rutas(proyecto, _json_o_vacio(rutas["harness_config"]).get("rutaCodebase"))
    lineas.append("Archivos leídos")
    leidos = [archivos[c] for c in ("lock", "installation", "capacidades", "fuentes", "contexto")]
    if (doc.get("knowledge") or {}).get("applies"):
        # El libro de la sesion no se lista: su ruta lleva el sessionId de la senal, que llega por
        # stdin y nadie eligio, y esta lista no pasa por el catalogo de secretos.
        leidos += [os.path.join(proyecto, ".claude", "settings.json"), b.ruta_de_la_senal(proyecto),
                   b.ruta_de_la_agenda(proyecto), rutas["presupuesto"]]
    for ruta in leidos:
        lineas.append("  %s%s" % (os.path.normpath(ruta), "" if os.path.isfile(ruta) else "  (no existe)"))
    return "\n".join(lineas)


def _detalle_de_refresco(doc):
    """La agenda de la revision automatica: modo, fechas, disparador y error. Son ids y fechas;
    el canal es una clave de Ficha o un directorio, y pasa por el catalogo de secretos igual."""
    kr = doc.get("knowledgeRefresh")
    if not isinstance(kr, dict):
        return []
    lineas = [
        "  %-19s %s%s" % ("Revisión: modo", kr.get("mode") or "desconocido",
                          " (%s)" % kr["policyError"] if kr.get("policyError") else ""),
        "  %-19s %s" % ("Red en SessionStart", "sí" if kr.get("sessionStartNetwork") else "no"),
        "  %-19s %s" % ("Estado de revisión", kr.get("state") or "NEVER_CHECKED"),
        "  %-19s %s" % ("Vencida", "sí" if kr.get("due") else "no"),
        "  %-19s %s" % ("Última que salió", kr.get("lastSuccessfulCheckAt") or "nunca"),
        "  %-19s %s" % ("Último intento", kr.get("lastAttemptAt") or "nunca"),
        "  %-19s %s" % ("Próxima", kr.get("nextCheckDueAt") or "a pedido"),
        "  %-19s %s" % ("Disparador", kr.get("trigger") or "ninguno"),
        "  %-19s %s" % ("Error de revisión", kr.get("errorCode") or "ninguno"),
        "  %-19s %s" % ("Canal", kr.get("channel") or "ninguno"),
    ]
    catalogo = limpieza.cargar_catalogo()
    return [limpieza.redactar(l, catalogo, "harness --verbose")[0] for l in lineas]


def _detalle_de_runtime(b, doc, proyecto):
    """Las huellas, las versiones y las fechas de los componentes de runtime. Son sha256 y
    fechas: ningun secreto, y ninguna ruta que no se vea ya en "Archivos leídos"."""
    rc = doc.get("runtimeComponents") or {}
    if not rc or not (doc.get("knowledge") or {}).get("applies"):
        return []
    lineas = []
    for clave, nombre, _, _ in b.COMPONENTES:
        comp = rc.get(clave) or {}
        lineas.append("  %-21s %s%s, versión %s, validado: %s"
                      % (nombre, comp.get("state"),
                         " (%s)" % comp["errorCode"] if comp.get("errorCode") else "",
                         comp.get("version") or "desconocida",
                         comp.get("lastValidatedAt") or "nunca"))
    barra = rc.get("contextBar") or {}
    probada = {True: "sí", False: "no"}.get(barra.get("commandTested"), "sin probar")
    huellas = barra.get("fingerprints") or {}
    lineas += ["  %-21s %s" % ("Renderizador", barra.get("renderer") or "ninguno"),
               "  %-21s %s" % ("Versión de la barra", barra.get("integrationVersion") or "desconocida"),
               "  %-21s %s" % ("Probada en shells", probada),
               "  %-21s %s" % ("Huella statusLine", barra.get("configurationFingerprint") or "ninguna")]
    for nombre, clave in (("renderizador", "renderer"), ("adaptador", "block4Adapter"),
                          ("session-start", "sessionStart")):
        lineas.append("  %-21s %s" % ("Huella " + nombre, huellas.get(clave) or "ninguna"))
    senal, problema = b.leer_senal_de_vida(proyecto)
    if senal:
        lineas.append("  %-21s sesión %s, %s, Bloque 4 %s"
                      % ("Señal de vida", senal["sessionId"], senal["lastRenderedAt"],
                         senal["block4"]))
    else:
        lineas.append("  %-21s %s" % ("Señal de vida",
                                      "ilegible" if problema == "unreadable" else "no hay"))
    # El sessionId de la senal llega por stdin a la barra y nadie lo eligio: pasa por el
    # catalogo de secretos como todo lo que se imprime sin haberlo escrito el harness. El
    # comando registrado no se imprime nunca: su huella alcanza para saber si cambio.
    catalogo = limpieza.cargar_catalogo()
    return [limpieza.redactar(l, catalogo, "harness --verbose")[0] for l in lineas]


# -- la politica de la Context Bar -----------------------------------------------
#
# docs/cambios/context-bar-consumo-desde-instalacion. `setup`, `estado` y `harness` la leen y
# no la escriben nunca; el unico que escribe es `presupuesto --context-defaults`.

_CLI_INSTALADA = "python .claude/harness/bin/desarrollo/dev-harness.py"
_SESION_DE_LA_BARRA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# El id del resumen, y como lo lee una persona.
_FUENTES_DE_CONTEXTO = {cont_agregacion.SIN_FUENTE: "SIN RESOLVER"}
_ANSI = {"ENABLED": "HABILITADO", "DISABLED_NO_COLOR": "DESHABILITADO POR NO_COLOR",
         "UNVERIFIED": "SIN VERIFICAR"}
_NIVEL_DE = {"contextWarningAt": "WARNING", "contextErrorAt": "ERROR"}
LISTA_PARA_CONSUMO = "La barra está lista para mostrar consumo porcentual y alertas."


def _porciento(valor):
    return "%d%%" % int(round(float(valor) * 100))


def plantilla_de_contexto():
    """(ruta, politica) de la plantilla de la politica por defecto, o (ruta o None, None)."""
    ruta = orq_roster.ruta_de_regla(cont_presupuesto.PLANTILLA_DE_CONTEXTO)
    if not ruta:
        return None, None
    try:
        return ruta, cont_presupuesto.cargar(ruta)
    except (ValueError, OSError, cont_presupuesto.PoliticaInvalida):
        return ruta, None


def politica_de_la_barra(rutas):
    """(clase, politica o None, motivo, umbrales que faltan) de la politica instalada."""
    _, plantilla = plantilla_de_contexto()
    clase, politica, motivo = cont_presupuesto.clase_de_politica(rutas["presupuesto"], plantilla)
    faltan = list(cont_presupuesto.UMBRALES_DE_CONTEXTO)
    if politica is not None:
        faltan = cont_presupuesto.umbrales_de_contexto_que_faltan(politica)
    return clase, politica, motivo, faltan


def _motivo_en_una_linea(motivo):
    """El error de validacion, que trae una linea por campo, en una sola y recortada."""
    texto = " ".join(str(motivo or "").split())
    return texto if len(texto) <= 240 else texto[:237] + "..."


def _plata_declarada(politica):
    """'SIN CONFIGURAR', o los limites de plata que declara la politica, por ambito."""
    partes = []
    for ambito in ("task", "project"):
        if not cont_presupuesto.declarada(politica, ambito):
            continue
        limites = (politica or {}).get(ambito) or {}
        partes.append("%s: blando %s / duro %s" % (ambito, *(
            "sin declarar" if limites.get(k) is None
            else "%s %.2f" % ((politica or {}).get("currency") or "", float(limites[k]))
            for k in ("softLimit", "hardLimit"))))
    return "CONFIGURADO (%s)" % "; ".join(partes) if partes else "SIN CONFIGURAR"


def clase_en_texto(clase, motivo):
    """Lo que sigue a `política` en `setup` y en `harness --verbose`: la clase que dio
    `politica_de_la_barra`, y el por que cuando hace falta. Una sola, para que los dos no digan
    cosas distintas del mismo archivo."""
    if clase == cont_presupuesto.POLITICA_DEFAULT:
        return "DEFAULT (la del harness: umbrales de contexto y nada más)"
    if clase == cont_presupuesto.POLITICA_AUSENTE:
        return "MISSING (no existe .claude/harness.presupuesto.json)"
    if clase == cont_presupuesto.POLITICA_INVALIDA:
        return "INVALID: %s" % _motivo_en_una_linea(motivo)
    return "PROJECT"


def lineas_de_la_politica(rutas):
    """El bloque `Context Bar` de `setup`: que politica hay, sus umbrales de contexto y si hay
    plata. Informa; no pregunta y no escribe."""
    clase, politica, motivo, faltan = politica_de_la_barra(rutas)
    lineas = ["política %s" % clase_en_texto(clase, motivo)]
    barra = (politica or {}).get("statusBar") or {}
    for clave in cont_presupuesto.UMBRALES_DE_CONTEXTO:
        if clase == cont_presupuesto.POLITICA_INVALIDA:
            lineas.append("contexto %s SIN RESOLVER (la política no valida)" % _NIVEL_DE[clave])
        elif clave in faltan:
            lineas.append("contexto %s SIN CONFIGURAR (falta statusBar.%s)"
                          % (_NIVEL_DE[clave], clave))
        else:
            lineas.append("contexto %s %s" % (_NIVEL_DE[clave], _porciento(barra[clave])))
    if clase == cont_presupuesto.POLITICA_INVALIDA:
        lineas.append("presupuesto monetario SIN RESOLVER (la política no valida)")
        lineas.append("La barra dibuja `presupuesto ilegible` hasta que la política valide. "
                      "Se arregla a mano: el harness no la reescribe.")
    else:
        lineas.append("presupuesto monetario %s" % _plata_declarada(politica))
    if clase == cont_presupuesto.POLITICA_AUSENTE:
        lineas.append("Para crear la política por defecto: %s presupuesto --context-defaults"
                      % _CLI_INSTALADA)
    elif clase != cont_presupuesto.POLITICA_INVALIDA and faltan:
        lineas.append("Sin esos umbrales Ctx no toma color. Para agregarlos sin tocar el resto "
                      "de la política: %s presupuesto --context-defaults" % _CLI_INSTALADA)
    catalogo = limpieza.cargar_catalogo()
    return [limpieza.redactar(l, catalogo, "setup")[0] for l in lineas]


def mostrar_politica_de_la_barra(consola, rutas):
    consola.linea("")
    consola.linea("Context Bar")
    consola.linea("-" * 48)
    for linea in lineas_de_la_politica(rutas):
        consola.linea("  " + linea)


def _campo_del_limite():
    adaptador = cont_registro.resolver(cont_registro.DE_LA_BARRA)
    return getattr(adaptador, "CAMPO_DEL_LIMITE", None) or "el tamaño de la ventana"


def _detalle_de_consumo(b, doc, proyecto, rutas):
    """Por que la barra puede, o no, mostrar un porcentaje y colores: su estado, de donde sale el
    contexto, el limite, los umbrales y el color que vio el proceso de la statusLine.

    La sesion es la de la ultima senal de vida: `harness` no tiene una. Ningun numero de la
    transcripcion ni ningun texto de la sesion se imprime: el estado, la fuente, el limite y los
    umbrales, y nada mas.
    """
    rc = doc.get("runtimeComponents") or {}
    if not rc or not (doc.get("knowledge") or {}).get("applies"):
        return []
    comp = rc.get("contextBar") or {}
    senal, _ = b.leer_senal_de_vida(proyecto)
    ansi = b.ansi_de_la_senal(senal)
    clase, politica, motivo, faltan = politica_de_la_barra(rutas)
    sesion = senal.get("sessionId") if isinstance(senal, dict) else None

    contexto = {}
    if isinstance(sesion, str) and _SESION_DE_LA_BARRA.match(sesion) and sesion not in (".", ".."):
        try:
            libro_leido = cont_libro.leer(cont_libro.ruta_de(proyecto, sesion))
            if cont_barra.de_sesion(libro_leido, sesion):
                contexto = cont_barra.de(libro_leido, sesion, politica)["context"]
        except (ValueError, OSError):
            contexto = {}
    fuente = contexto.get("source") or cont_agregacion.SIN_FUENTE
    limite = contexto.get("limit")
    inconsistente = contexto.get("diagnostic") == cont_agregacion.VENTANA_INCONSISTENTE

    # La misma clase que muestra `setup` (E-43), del mismo `politica_de_la_barra`: solo lee.
    lineas = ["Consumo de la Context Bar",
              "  Estado %s" % b.etiqueta_de_componente("contextBar", comp),
              "  Política %s" % clase_en_texto(clase, motivo),
              "  Fuente de contexto %s" % _FUENTES_DE_CONTEXTO.get(fuente, fuente)]
    if limite:
        lineas.append("  Límite de ventana %d" % int(limite))
    else:
        lineas.append("  Límite de ventana SIN RESOLVER: el proveedor todavía no informó %s en "
                      "la statusLine, y el harness no tiene una tabla de modelos para inventarlo. "
                      "Sin límite, Ctx se muestra en tokens." % _campo_del_limite())
    if inconsistente:
        lineas.append("  Ventana %s: el proveedor informó más tokens que la ventana. La barra "
                      "muestra tokens, sin porcentaje ni color." % cont_agregacion.VENTANA_INCONSISTENTE)
    barra = (politica or {}).get("statusBar") or {}
    for clave in cont_presupuesto.UMBRALES_DE_CONTEXTO:
        if clase == cont_presupuesto.POLITICA_INVALIDA:
            lineas.append("  Umbral %s SIN CONFIGURAR (la política no valida)" % _NIVEL_DE[clave])
        elif clave in faltan:
            lineas.append("  Umbral %s SIN CONFIGURAR (falta %s)" % (_NIVEL_DE[clave], clave))
        else:
            lineas.append("  Umbral %s %s" % (_NIVEL_DE[clave], _porciento(barra[clave])))
    if clase != cont_presupuesto.POLITICA_INVALIDA and faltan:
        lineas.append("  Para agregar los umbrales que faltan: %s presupuesto --context-defaults"
                      % _CLI_INSTALADA)
    texto_ansi = "  Color ANSI %s" % _ANSI.get(ansi, _ANSI["UNVERIFIED"])
    if ansi == "DISABLED_NO_COLOR":
        texto_ansi += ": NO_COLOR está definido en el proceso de la statusLine, y la barra sale sin colores."
    elif ansi != "ENABLED" and not isinstance(senal, dict):
        texto_ansi += ": ninguna sesión dibujó la barra todavía."
    elif ansi != "ENABLED":
        texto_ansi += ": la última señal de vida no dice si el proceso de la statusLine tiene NO_COLOR."
    lineas.append(texto_ansi)

    falta = []
    if comp.get("state") != b.ACTIVE:
        falta.append("que la barra esté ACTIVA")
    if not limite:
        falta.append("el límite de la ventana")
    if inconsistente:
        falta.append("una ventana coherente")
    if clase == cont_presupuesto.POLITICA_INVALIDA or faltan:
        falta.append("los umbrales de contexto")
    if ansi not in ("ENABLED", "DISABLED_NO_COLOR"):
        falta.append("saber si hay colores")
    if falta:
        lineas.append("  Para mostrar consumo porcentual y alertas falta: %s." % ", ".join(falta))
    else:
        lineas.append("  " + LISTA_PARA_CONSUMO)
    catalogo = limpieza.cargar_catalogo()
    return [limpieza.redactar(l, catalogo, "harness --verbose")[0] for l in lineas]


def acceso_del_modelo(proyecto):
    """BLOQUEADO si permissions.deny le niega el .env a Claude, LEGIBLE si no, o SIN VERIFICAR."""
    try:
        legible = bienvenida().acceso_al_env(proyecto)
    except Exception:                         # noqa: BLE001 - la tabla no se cae por esto
        legible = None
    if legible is None:
        return "SIN VERIFICAR"
    return "LEGIBLE" if legible else "BLOQUEADO"


def mostrar_resumen(documento, resolucion):
    """`estado --resumen`: una linea por integracion. Es lo que dice el instalador al terminar."""
    sys.stdout.write("Configuración: %s (.env local)\n" % entorno.MODO)
    ancho = max(len(c.etiqueta) for c in CLASES) + 4
    for clase in CLASES:
        datos = documento["integraciones"][clase.nombre]
        resuelta = resolucion.integracion(clase.nombre)
        if datos["estado"] == base.AVAILABLE:
            texto = "OK"
        elif datos.get("faltan"):
            texto = "falta " + ", ".join(datos["faltan"])
        elif not resuelta.habilitada and not resuelta.codigo:
            texto = "deshabilitada (%s)" % resuelta.bandera
        else:
            texto = datos["estado"] + (" (%s)" % resuelta.codigo if resuelta.codigo else "")
        sys.stdout.write("  %s%s\n" % (clase.etiqueta.ljust(ancho), texto))
        legado = resuelta.de_legado()
        if legado:
            sys.stdout.write("  %sen migración: falta pasar %s al .env\n"
                             % (" " * ancho, ", ".join(legado)))
    nuevas = resolucion.variables_nuevas()
    if nuevas:
        sys.stdout.write("Variables nuevas del contrato: %s (ver .env.example)\n"
                         % ", ".join(nuevas))


def mostrar(consola, documento, proyecto, rutas):
    ancho = len("Acceso del modelo") + 3
    consola.linea("")
    consola.linea("GCBA Development Harness")
    consola.linea("")
    consola.linea("Configuración")
    consola.linea("-" * 48)
    consola.linea("%s%s" % ("Fuente".ljust(ancho), ".env local"))
    consola.linea("%s%s" % ("Acceso del modelo".ljust(ancho), acceso_del_modelo(proyecto)))
    consola.linea("")
    consola.linea("Integraciones")
    consola.linea("-" * 48)
    for clase in CLASES:
        datos = documento["integraciones"][clase.nombre]
        consola.linea("%s%s" % (clase.etiqueta.ljust(ancho), datos["estado"]))
        if datos.get("faltan"):
            consola.linea("  Faltan: " + ", ".join(datos["faltan"]))
        if datos["motivo"]:
            consola.linea("  " + datos["motivo"])
        for linea in datos.get("diagnostico") or []:
            consola.linea("  sin " + linea)
    consola.linea("")
    consola.linea("Capacidades")
    consola.linea("-" * 48)
    for capacidad, situacion in sorted(documento["capacidades"].items()):
        consola.linea("  %-9s %s" % (situacion, capacidad))
    consola.linea("")
    consola.linea("Estado")
    consola.linea("-" * 48)
    # El estado del resolvedor, no una palabra fija: con una integracion caida es PARCIAL.
    consola.linea(linea_de_estado(proyecto, rutas))
    caidas = [c.etiqueta for c in CLASES
              if documento["integraciones"][c.nombre]["estado"] != base.AVAILABLE]
    if caidas:
        consola.linea("Sin: %s. Sus capacidades quedan deshabilitadas; el resto del harness "
                      "funciona." % ", ".join(caidas))
        consola.linea("Para ver que falta: dev-harness.py reconfigurar <%s>. Se completa en el "
                      ".env local." % "|".join(NOMBRES))


# -- contexto de tarea ---------------------------------------------------------

def resolver_fuentes(args, proyecto, rutas, config, almacen, timeout, consola,
                     transporte, transporte_bytes):
    """Bloque 1: del registro de fuentes al estado de frescura de cada una.

    🔴 Sale 0 aunque haya fuentes en alerta. Una fuente desactualizada no es una falla del
    harness: es justo lo que este comando existe para poder decir. El codigo 2 queda para lo
    que la persona tiene que arreglar antes de seguir.

    🔴 Sin canal que consultar -ni una clave de Jira ni un directorio local- no se declara
    que este todo bien: se declara que no se pudo verificar, que es otra cosa.

    Con --auto o --si-vence es el refresco controlado (orquestacion/auto_refresh.py): mismo
    camino de observacion y resolucion, con la agenda, las capacidades y sin escribir nada si el
    canal no contesta.
    """
    if args.auto or args.si_vence:
        return refrescar_fuentes(args, proyecto, rutas, consola, transporte, transporte_bytes)
    try:
        registro = orq_fuentes.cargar()
        entradas, destino, previo, decisiones = orq_refresco.contexto_de_fuentes(proyecto)
    except orq_fuentes.RegistroInvalido as e:
        # Un registro que no se puede leer entero no se lee a medias: es lo que la persona
        # tiene que arreglar antes de seguir, y por eso sale 2 y no 0.
        raise FallaDelHarness(str(e))
    hallazgos = orq_fuentes.hallazgos(registro)

    canal = None
    observaciones = []

    if args.archivo:
        directorio = os.path.abspath(args.archivo)
        if not os.path.isdir(directorio):
            raise FallaDelHarness("el directorio %s no existe." % directorio)
        observaciones = int_fuentes.observar_archivos(entradas, directorio)
        canal = {"reachable": True, "reason": "originales leidos de %s" % directorio,
                 "channel": "archivo:%s" % directorio}
        consola.evento("fuentes.local", directorio=directorio)

    elif args.argumento:
        clave = str(args.argumento)
        if not CLAVE_JIRA.match(clave):
            raise FallaDelHarness(
                "fuentes necesita una clave de Jira con la forma PROYECTO-123, o --archivo "
                "con el directorio de los originales.")
        canal, observaciones = _observar_por_ficha(
            clave, args, proyecto, rutas, config, almacen, timeout, consola,
            transporte, transporte_bytes, entradas, previo)

    else:
        consola.linea("Sin clave de Jira ni --archivo no hay canal que consultar: cada fuente "
                      "queda sin verificar.")

    aceptadas = []
    if args.aceptar:
        # Antes de escribir nada: si una no se puede aceptar, no se acepta ninguna.
        aceptadas = _aceptar(args, rutas, entradas, observaciones, canal, decisiones)

    try:
        documento = orq_refresco.resolver_y_escribir(entradas, observaciones, canal, decisiones,
                                                     destino)
    except (ValueError, OSError) as e:
        raise FallaDelHarness(str(e))
    _anotar_agenda(proyecto, consola, documento, canal)
    # El aviso de fabrica "no tiene hash aceptado" no se repite para una fuente que el proyecto
    # ya acepto: la referencia de esa fuente ahora es la aceptacion, y el aviso diria lo contrario.
    con_aceptacion = [sid for sid, f in documento["sources"].items() if f.get("acceptance")]
    for hallazgo in hallazgos:
        if any(("la fuente %s no tiene hash aceptado" % sid) in hallazgo
               for sid in con_aceptacion):
            continue
        consola.linea("  aviso: " + hallazgo)
    consola.evento("fuentes.listo", fuentes=len(documento["sources"]),
                   pendientes=documento["pending_count"])

    for sid in aceptadas:
        consola.evento("fuentes.aceptada", fuente=sid, estado=documento["sources"][sid]["state"])

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        for sid in aceptadas:
            d = decisiones[sid]
            consola.linea("")
            consola.linea("Aceptada %s %s" % (sid, d["observed_version"]))
            consola.linea("  SHA-256   %s" % d["observed_sha256"])
            consola.linea("  Canal     %s" % d["channel"])
            consola.linea("  Aceptó    %s, el %s" % (d["by"], d["at"]))
            if d.get("overridesRegistryVersion"):
                consola.linea("  Ojo: es anterior a la %s que trae el harness de fábrica. Queda "
                              "registrado que se pisó." % d["overridesRegistryVersion"])
            consola.linea("  Estado    %s" % documento["sources"][sid]["state"])
        mostrar_fuentes(consola, documento, destino)
    return 0


def _aceptar(args, rutas, entradas, observaciones, canal, decisiones):
    """Registra como aceptada la identidad observada EN ESTA CORRIDA de cada fuente pedida.

    🔴 Se acepta lo que se acaba de mirar, nunca un estado guardado: la version, el SHA-256 del
    original, el adjunto o el archivo, y el canal. Sin quien acepta no hay aceptacion. Si una
    no se puede aceptar, levanta antes de tocar `decisions`, y no se escribe nada.
    """
    por = str(args.por or _config_harness(rutas).get("usuario") or "").strip()
    if not por:
        raise FallaDelHarness(
            "una aceptacion necesita quien la da. Pasá --por <persona>, o configurá `usuario` "
            "en .claude/harness.config.json.")
    disponible = bool(canal) and bool(canal.get("reachable", True))
    por_id = {str(o.get("id")): o for o in observaciones}
    entradas_por_id = {str(e.get("id")): e for e in entradas}
    pedidas = [x.strip() for x in str(args.aceptar).split(",") if x.strip()]
    nuevas = {}
    for sid in pedidas:
        entrada = entradas_por_id.get(sid)
        if entrada is None:
            raise FallaDelHarness("%s no es una fuente gestionada. Son: %s."
                                  % (sid, ", ".join(sorted(entradas_por_id))))
        obs = por_id.get(sid)
        codigo, motivo = orq_frescura.aceptable(entrada, obs, disponible, args.regresion)
        if codigo:
            raise FallaDelHarness("%s no se puede aceptar (%s): %s. No se escribio nada."
                                  % (sid, codigo, motivo))
        nuevas[sid] = orq_frescura.decision_de_aceptacion(
            entrada, obs, canal.get("channel"), por, orq_frescura.ahora(), args.regresion)
    decisiones.update(nuevas)
    return sorted(nuevas)


def _observar_por_ficha(clave, args, proyecto, rutas, config, almacen, timeout, consola,
                        transporte, transporte_bytes, entradas, previo):
    """Los adjuntos de la Ficha de Proyecto del ticket. Devuelve (canal, observaciones).

    La Ficha se resuelve con el mismo resolvedor del Bloque 2. Una segunda busqueda con un
    criterio parecido es como un dia una encuentra la Ficha y la otra no.
    """
    capacidades = _json_o_vacio(rutas["capacidades"]).get("capacidades") or {}
    jira = armar(IntegracionJira, config, almacen, timeout, transporte)
    jira.transporte_bytes = transporte_bytes
    acumulador = contexto_comun.Acumulador(capacidades)

    try:
        _tarea, campos_tarea = contexto_tarea.resolver(
            jira, clave, CATALOGO(), _config_harness(rutas), acumulador)
    except contexto_tarea.TareaNoResuelta as e:
        raise FallaDelHarness(str(e))

    ficha, campos_ficha = contexto_proyecto.resolver(
        jira, campos_tarea, CATALOGO(), _config_harness(rutas), acumulador)
    clave_ficha = ficha["ficha"]["key"]
    consola.evento("fuentes.ficha", ficha=clave_ficha or "ninguna")

    if not clave_ficha or campos_ficha is None:
        return {"reachable": False,
                "reason": "no se pudo resolver la Ficha de Proyecto del ticket %s" % clave}, []

    adjuntos = [a for a in (campos_ficha.get("attachment") or []) if isinstance(a, dict)]
    texto = contexto_comun.texto_de_adf(campos_ficha.get("description"))
    descargas = os.path.join(proyecto, ".claude", "conocimiento", "fuentes")
    observaciones = int_fuentes.observar(entradas, adjuntos, previo, jira.bajar_adjunto,
                                         descargas, texto)
    tipo = str(_config_harness(rutas).get("fichaTipoDeIssue")
               or contexto_proyecto.TIPO_POR_DEFECTO)
    return {"key": clave_ficha, "issue_type": tipo, "reachable": True,
            "channel": "jira:%s" % clave_ficha}, observaciones


def mostrar_fuentes(consola, documento, destino):
    consola.linea("")
    consola.linea("Fuentes gestionadas")
    for sid in sorted(documento["sources"]):
        f = documento["sources"][sid]
        versiones = "%s -> %s" % (f["registry_version"] or "sin version",
                                  f["observed_version"] or "sin observar")
        derivados = "%d derivados" % len(f["derived_impact"])
        if f["stale_derived"]:
            derivados += ", %d desactualizados" % len(f["stale_derived"])
        consola.linea("  %-12s %-22s %-28s %s" % (sid, versiones, f["state"], derivados))
    consola.linea("")
    if documento["pending_count"]:
        consola.linea("%d de %d fuentes no se pueden tratar como vigentes."
                      % (documento["pending_count"], len(documento["sources"])))
    else:
        consola.linea("Las %d fuentes estan verificadas contra el canal configurado."
                      % len(documento["sources"]))
    consola.linea("Estado en %s" % destino)


# -- el refresco controlado del conocimiento --------------------------------------

def _anotar_agenda(proyecto, consola, documento, canal):
    """`fuentes` a mano deja la agenda como EXPLICIT_SOURCES_COMMAND. Sin canal que contestara es
    un intento que no salio bien: no mueve la ultima revision. Si la agenda no se puede escribir
    se avisa y el comando sigue: harness.fuentes.json ya quedo escrito."""
    politica, _ = orq_refresco.cargar_politica(proyecto)
    disponible = bool(canal) and bool(canal.get("reachable", True))
    codigo = None if disponible else orq_refresco.SIN_CANAL
    try:
        orq_refresco.registrar(proyecto, orq_frescura.ahora(),
                               orq_refresco.EXPLICIT_SOURCES_COMMAND, politica, codigo,
                               documento)
    except (OSError, ValueError) as e:
        consola.linea("  aviso: no se pudo escribir la agenda de revisión (%s): %s"
                      % (orq_refresco.AGENDA_SIN_ESCRIBIR, e))


def _observar_ficha_directa(jira, clave_ficha, rutas):
    """La Ficha leida por su clave: sus adjuntos y su descripcion. Es el canal que dejo la ultima
    corrida, y se lee con el mismo `fuentes.observar` que `_observar_por_ficha`."""
    respuesta = jira.issue(clave_ficha)
    if not respuesta.ok:
        codigo = (orq_refresco.TIMEOUT if respuesta.error == int_http.ERROR_TIMEOUT
                  else orq_refresco.SIN_CANAL)
        raise orq_refresco.ObservacionFallida(codigo, "Jira contesto %d" % respuesta.codigo)
    campos = (respuesta.datos() or {}).get("fields") or {}
    return campos


def _observador_de_jira(args, proyecto, rutas, consola, transporte, transporte_bytes):
    """El observador que el refresco inyecta: el adaptador de Jira que arma `armar`, con la
    configuracion del .env que resuelve `resolver_configuracion`. Se arma recien cuando hace
    falta salir al canal: un refresco que no vence no toca la configuracion."""
    def observar(canal, entradas, previo):
        config = resolver_configuracion(rutas)
        almacen = AlmacenSecretos(rutas["env"])
        timeout = timeout_de(rutas)
        if canal["kind"] == "jira-tarea":
            try:
                canal_doc, observaciones = _observar_por_ficha(
                    canal["key"], args, proyecto, rutas, config, almacen, timeout, consola,
                    transporte, transporte_bytes, entradas, previo)
            except FallaDelHarness as e:
                raise orq_refresco.ObservacionFallida(orq_refresco.OBSERVACION_FALLIDA, str(e))
            return canal_doc, observaciones
        jira = armar(IntegracionJira, config, almacen, timeout, transporte)
        jira.transporte_bytes = transporte_bytes
        campos = _observar_ficha_directa(jira, canal["key"], rutas)
        adjuntos = [a for a in (campos.get("attachment") or []) if isinstance(a, dict)]
        texto = contexto_comun.texto_de_adf(campos.get("description"))
        descargas = os.path.join(proyecto, ".claude", "conocimiento", "fuentes")
        observaciones = int_fuentes.observar(entradas, adjuntos, previo, jira.bajar_adjunto,
                                             descargas, texto)
        tipo = str(_config_harness(rutas).get("fichaTipoDeIssue")
                   or contexto_proyecto.TIPO_POR_DEFECTO)
        return {"key": canal["key"], "issue_type": tipo, "reachable": True,
                "channel": "jira:%s" % canal["key"]}, observaciones
    return observar


def _capacidades(rutas):
    return _json_o_vacio(rutas["capacidades"]).get("capacidades") or {}


def _refresco_de(args, proyecto, rutas, consola, transporte, transporte_bytes, disparador,
                 clave=None):
    canal = orq_refresco.canal_previsto(proyecto, clave, getattr(args, "archivo", "") or None)
    return orq_refresco.refrescar(
        proyecto, disparador,
        _observador_de_jira(args, proyecto, rutas, consola, transporte, transporte_bytes),
        _capacidades(rutas), canal)


def refrescar_fuentes(args, proyecto, rutas, consola, transporte, transporte_bytes):
    """`fuentes --auto [--disparador X]` y `fuentes --si-vence`. Sale 0 aunque no se haya podido
    mirar: no poder mirar es un estado que se informa, no una falla del harness."""
    if args.si_vence:
        disparador = orq_refresco.PRE_NORMATIVE_OPERATION_IF_STALE
    else:
        disparador = args.disparador or orq_refresco.EXPLICIT_SOURCES_COMMAND
    if disparador not in orq_refresco.DISPARADORES:
        raise FallaDelHarness("--disparador tiene que ser uno de: %s."
                              % ", ".join(orq_refresco.DISPARADORES))
    clave = str(args.argumento) if args.argumento else None
    if clave and not CLAVE_JIRA.match(clave):
        raise FallaDelHarness("fuentes necesita una clave de Jira con la forma PROYECTO-123.")
    resultado = _refresco_de(args, proyecto, rutas, consola, transporte, transporte_bytes,
                             disparador, clave)
    consola.evento("fuentes.refresco", disparador=disparador,
                   refrescado="si" if resultado["refreshed"] else "no",
                   codigo=resultado["errorCode"] or "ninguno")
    if args.json:
        sys.stdout.write(json.dumps(resultado, ensure_ascii=False, indent=2, sort_keys=True)
                         + "\n")
    else:
        mostrar_refresco(consola, resultado)
    return 0


def mostrar_refresco(consola, resultado):
    consola.linea("")
    if resultado["refreshed"]:
        consola.linea("Fuentes revisadas contra %s." % resultado["channel"])
    elif orq_refresco.fallo(resultado):
        consola.linea("Las fuentes no se pudieron revisar (%s): queda el último estado conocido."
                      % resultado["errorCode"])
    else:
        consola.linea("No hacía falta revisar las fuentes (%s)." % resultado["errorCode"])
    for f in resultado["sources"]:
        consola.linea("  %-12s %-8s %-8s %s" % (f["id"], f["acceptedVersion"] or "—",
                                               f["observedVersion"] or "—", f["sourceState"]))
    consola.linea("Última revisión que salió bien: %s · próxima: %s"
                  % (resultado.get("lastSuccessfulCheckAt") or "nunca",
                     resultado.get("nextCheckDueAt") or "a pedido"))


def compuerta_normativa(args, proyecto, rutas, consola, clave, transporte=None,
                        transporte_bytes=None):
    """Antes de una operacion que usa conocimiento normativo: refresca si vencio, y avisa.

    🔴 No corta nunca. Integrado con Flow Governance (docs/cambios/flow-governance/
    integracion-0.28.md, decision A): el refresco refresca, observa, registra y avisa, y lo que
    frena `plan` o `refute --compile` lo decide despues la frescura de ESA operacion, sobre las
    fuentes que exige (Wave 5): el plan queda BLOCKED y el flujo en HARD_BLOCKER, la refutacion
    sale con 2 sin escribir. Una fuente seguida que la operacion no exige no la frena. Cortar aca
    -la letra de KRF E-42- terminaba `plan` antes de que el flujo dejara el bloqueo escrito, y con
    una fuente que el plan no usa. Lo que no es normativo no pasa por aca.

    🔴 El canal es el que dejo la ultima corrida de `fuentes`, no la clave de esta tarea: volver
    a mirar es volver al canal que ya funciono, no buscar una Ficha nueva a partir de un plan.
    """
    del clave
    canal = orq_refresco.canal_previsto(proyecto)
    veredicto = orq_refresco.ensure_normative_knowledge_fresh(
        proyecto, _observador_de_jira(args, proyecto, rutas, consola, transporte,
                                      transporte_bytes),
        _capacidades(rutas), canal)
    consola.evento("conocimiento.compuerta", decision=veredicto["decision"],
                   refrescado="si" if veredicto["refresh"]["refreshed"] else "no")
    if veredicto["decision"] != orq_refresco.PERMITIDO:
        consola.linea("  aviso: conocimiento normativo SIN RESOLVER: %s" % veredicto["reason"])
    if veredicto.get("alerts"):
        consola.linea("  aviso: fuentes seguidas en alerta (%s): la operación decide por las "
                      "fuentes que exige." % ", ".join(veredicto["alerts"]))
    return veredicto


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
        _, documento = registrar_capacidades(config, almacen, timeout, consola, rutas, transporte)
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
    reconciliar_estado(consola, proyecto, rutas, clave)

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


# -- el plan de trabajo --------------------------------------------------------

def planificar(args, proyecto, rutas, consola):
    """Bloque 3: de un TaskContext a un OrchestrationPlan.

    No decide que hacer — eso lo decide dev-orchestrator y llega como propuesta. Lo que
    hace este comando es todo lo mecanico, que es lo que se puede testear.
    """
    clave = args.argumento
    ruta_contexto = os.path.join(proyecto, ".claude", "contextos", clave + ".json")
    if not os.path.isfile(ruta_contexto):
        raise FallaDelHarness(
            "no hay contexto para %s. Corre primero:\n"
            "    dev-harness.py contexto %s" % (clave, clave))

    task_context = _json_o_vacio(ruta_contexto)
    del_registro = _json_o_vacio(rutas["capacidades"])
    registro = del_registro.get("capacidades") or {}
    # El estado de cada integracion: con eso lo soportado y caido no se deriva como un hueco.
    integraciones = del_registro.get("integraciones") or {}
    # La frescura de las fuentes, local: lo que el plan exige se declara con su estado.
    fuentes = orq_frescura.leer(orq_frescura.ruta_por_defecto(proyecto))
    config = _config_harness(rutas)
    destino = os.path.join(proyecto, ".claude", "planes", clave + ".json")

    if args.plantilla:
        sys.stdout.write(json.dumps(plantilla_de_propuesta(task_context, registro),
                                    ensure_ascii=False, indent=2) + "\n")
        return 0

    # Las precondiciones de PLANNING: de que repositorio es la tarea, si este checkout es ese
    # y que falta. Solo lectura: el .env, el TaskContext y `git remote -v`.
    precondiciones = flujo_precondiciones.de_planificacion(
        task_context, gitlab_de_entorno(rutas), proyecto, config)

    if args.replanificar:
        if not os.path.isfile(destino):
            raise FallaDelHarness(
                "no hay un plan de %s para replanificar. Corre `plan %s --propuesta ...` "
                "primero." % (clave, clave))
        if not args.motivo:
            raise FallaDelHarness(
                "replanificar sin motivo no se puede: un plan que cambia solo no se puede "
                "auditar despues. Pasa --motivo.")
        anterior = _json_o_vacio(destino)
        nueva = _json_o_vacio(args.replanificar)
        documento = orq_plan.armar(nueva, task_context, registro, config,
                                   version_de(rutas), _relativa(proyecto, ruta_contexto),
                                   precondiciones, integraciones=integraciones, fuentes=fuentes)
        documento["meta"]["plan_version"] = anterior.get("meta", {}).get("plan_version", 1)
        documento["planHistory"] = anterior.get("planHistory", [])
        documento = orq_plan.replanificar(
            documento, _que_cambio(anterior, documento), args.motivo, "replanificacion manual")
    else:
        if not args.propuesta:
            raise FallaDelHarness(
                "plan necesita una propuesta. Sacá el esqueleto con `--plantilla`, que lo "
                "complete dev-orchestrator, y pasalo con `--propuesta <ruta>`.")
        if not os.path.isfile(args.propuesta):
            raise FallaDelHarness("no existe la propuesta %s." % args.propuesta)
        propuesta = _json_o_vacio(args.propuesta)
        documento = orq_plan.armar(propuesta, task_context, registro, config,
                                   version_de(rutas), _relativa(proyecto, ruta_contexto),
                                   precondiciones, integraciones=integraciones, fuentes=fuentes)

    consola.evento("plan.armado", tarea=clave, unidades=len(documento["workUnits"]),
                   version=documento["meta"]["plan_version"])
    orq_plan.escribir(documento, destino)
    consola.evento("plan.estado", estado=documento["status"])
    reconciliar_estado(consola, proyecto, rutas, clave)

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        mostrar_plan(consola, documento, destino)
    return 0


def gitlab_de_entorno(rutas):
    """La configuracion publica de GitLab resuelta del .env, sin escribir la proyeccion.

    Es el camino de 0.26.0 (.env -> contrato -> entorno.py) y nada mas: la proyeccion no se
    lee como fuente, y un .env roto hace fallar el comando en vez de dar una identidad del
    repositorio sin su declaracion principal.
    """
    contrato = entorno.cargar_contrato(adaptadores=ADAPTADORES)
    return entorno.resolver(contrato, rutas["env"], rutas["config"]).de("gitlab")


def _relativa(proyecto, ruta):
    return os.path.relpath(ruta, proyecto).replace(os.sep, "/")


def _que_cambio(anterior, nuevo):
    cambios = []
    antes = {u["id"] for u in anterior.get("workUnits", [])}
    ahora = {u["id"] for u in nuevo.get("workUnits", [])}
    for uid in sorted(ahora - antes):
        cambios.append("se agrego la unidad %s" % uid)
    for uid in sorted(antes - ahora):
        cambios.append("se saco la unidad %s" % uid)
    if anterior.get("objective") != nuevo.get("objective"):
        cambios.append("cambio el objetivo")
    if sorted(anterior.get("domains", [])) != sorted(nuevo.get("domains", [])):
        cambios.append("cambiaron los dominios")
    return cambios or ["el plan se rearmo sin cambios en las unidades"]


def plantilla_de_propuesta(task_context, registro):
    """El esqueleto que dev-orchestrator tiene que completar.

    Lleva adentro lo que necesita para decidir —el resumen de la tarea, que capacidades hay
    y que roster existe— para que no tenga que ir a buscarlo a cuatro archivos.
    """
    tarea = task_context.get("task") or {}
    ficha = (task_context.get("project") or {}).get("ficha") or {}
    return {
        "_comentario": [
            "Completa objective, domains y workUnits. El resto lo resuelve el harness.",
            "Cada unidad: id, objective, domain, requiredCapabilities, dependencies y signals.",
            "signals validas: " + ", ".join(sorted(orq_plan.modelo.PESOS)),
            "No pongas el tier: lo decide el router a partir de las signals.",
        ],
        "_tarea": {
            "key": tarea.get("key", ""),
            "type": tarea.get("type", ""),
            "title": tarea.get("title", ""),
            "acceptance_criteria": tarea.get("acceptance_criteria", []),
            "ficha": ficha.get("key", ""),
        },
        "_capacidadesDisponibles": orq_plan.cap.disponibles(registro),
        "_dominiosConocidos": orq_plan.roster.dominios_declarados(),
        "objective": "",
        "domains": [],
        "policies": [],
        "workUnits": [{
            "id": "", "objective": "", "domain": "",
            "requiredCapabilities": [], "dependencies": [], "signals": [],
        }],
    }


def mostrar_plan(consola, documento, destino):
    consola.linea("")
    consola.linea("%s — %s" % (documento["meta"]["task_key"], documento["objective"] or "(sin objetivo)"))
    consola.linea("-" * 60)
    consola.linea("Dominios     %s" % (", ".join(documento["domains"]) or "—"))
    consola.linea("Estándares   %s" % (", ".join(documento["applicableStandards"]) or "ninguno aplicable todavía"))
    consola.linea("")
    consola.linea("Unidades de trabajo (orden de ejecución)")
    por_id = {u["id"]: u for u in documento["workUnits"]}
    for uid in documento["executionOrder"]:
        u = por_id[uid]
        consola.linea("  %-20s %-12s %-10s %s" % (
            u["id"], u["domain"], u["modelPolicy"]["requiredTier"], u["status"]))
        consola.linea("      %s · %s" % (u["assignedAgent"] or "sin agente", u["objective"]))
    bloqueantes = flujo_precondiciones.bloqueantes(documento.get("flowPreconditions"))
    if bloqueantes:
        consola.linea("")
        consola.linea("Lo que falta para avanzar")
        for p in bloqueantes:
            consola.linea("  %s (%s)%s" % (p["inputId"], p["failureCode"],
                                           " · hay que preguntarle a la persona"
                                           if p["askUser"] else ""))
    caidas = orq_plan.no_disponibles(documento)
    if caidas:
        consola.linea("")
        consola.linea("Capacidades soportadas y no disponibles (no se construye nada: se revalida "
                      "la integracion)")
        for d in caidas:
            consola.linea("  %s · %s %s, la piden: %s" % (
                d["capabilityId"], d["integration"] or "sin integracion",
                d["reasonCode"], ", ".join(d["workUnits"])))
    if documento["capabilityGaps"]:
        consola.linea("")
        consola.linea("Capacidades que faltan")
        for hueco in documento["capabilityGaps"]:
            consola.linea("  %s → %s (%s), la piden: %s" % (
                hueco["capability"], hueco["derivedTo"], hueco["toolClass"],
                ", ".join(hueco["workUnits"])))
    pendientes = [a for a in documento["humanApprovals"] if a["status"] == "PENDING"]
    if pendientes:
        consola.linea("")
        for solicitud in pendientes:
            consola.linea(consumo_texto(solicitud))
    if documento["warnings"]:
        consola.linea("")
        consola.linea("Avisos")
        for aviso in documento["warnings"]:
            consola.linea("  · " + aviso)
    consola.linea("")
    consola.linea("Estado: %s" % documento["status"])
    consola.linea("Plan: %s" % destino)


def consumo_texto(solicitud):
    from orquestacion import consumo as orq_consumo
    return orq_consumo.texto_de_solicitud(solicitud)


# -- bloque 4: la contabilidad -------------------------------------------------

def contabilizar(args, proyecto, rutas, consola):
    """Bloque 4: del libro de una tarea a su resumen, su reporte y su barra.

    No ejecuta nada y no aprueba nada. Ingiere lo que una fuente reporta, agrega, y
    muestra. La compuerta humana del Bloque 3 sigue siendo la que decide.
    """
    tarea = str(args.argumento or "")
    if not tarea:
        raise FallaDelHarness(
            "contabilidad necesita la tarea. Ejemplo:\n"
            "    dev-harness.py contabilidad GCBA-1234")

    ruta_libro = cont_libro.ruta_de(proyecto, tarea)
    politica = cont_presupuesto.cargar(rutas["presupuesto"])

    if args.ingerir:
        if not os.path.exists(args.ingerir):
            raise FallaDelHarness("no existe la fuente %s." % args.ingerir)
        try:
            registros = cont_registro.leer(args.adaptador, args.ingerir)
        except KeyError as e:
            raise FallaDelHarness(str(e).strip('"'))
        atribucion = {"workUnitId": args.unidad or None, "agentId": args.agente or None}
        if args.refutacion:
            atribucion = _atribucion_de_refutacion(args, proyecto, tarea)
        eventos_nuevos = cont_contrato.a_eventos(
            registros, tarea, args.adaptador, politica, **atribucion)
        escritos, salteados, hallazgos = cont_libro.agregar_varios(ruta_libro, eventos_nuevos)
        consola.evento("contabilidad.ingesta", adaptador=args.adaptador,
                       escritos=escritos, repetidos=salteados)
        for hallazgo in hallazgos:
            consola.linea("  · " + hallazgo)

    libro_leido = cont_libro.leer(ruta_libro)
    if not libro_leido:
        raise FallaDelHarness(
            "no hay libro contable para %s. Ingerí una fuente primero:\n"
            "    dev-harness.py contabilidad %s --ingerir <ruta>" % (tarea, tarea))

    decision = {}
    if politica is not None:
        resumen_previo = cont_agregacion.resumir(libro_leido, task_id=tarea)
        gastado, _ = cont_presupuesto.consumido(resumen_previo, politica)
        decision = cont_presupuesto.evaluar(gastado, 0, politica)

    resumen = cont_agregacion.resumir(libro_leido, task_id=tarea, presupuesto=decision)
    destino = cont_agregacion.escribir(
        resumen, cont_libro.ruta_de(proyecto, tarea, cont_libro.RESUMEN))
    consola.evento("contabilidad.resumen", eventos=resumen["events"]["counted"],
                   duplicados=resumen["events"]["duplicates"])

    if args.reporte:
        ruta_reporte = cont_reporte.escribir(
            resumen, cont_libro.ruta_de(proyecto, tarea, cont_libro.REPORTE))
        consola.evento("contabilidad.reporte", destino=_relativa(proyecto, ruta_reporte))

    if args.barra:
        sesion = args.sesion or (cont_barra.sesiones(libro_leido) or [""])[0]
        estado = cont_barra.de(libro_leido, sesion, politica, tarea)
        if args.json:
            sys.stdout.write(json.dumps(estado, ensure_ascii=False, indent=2,
                                        sort_keys=True) + "\n")
        else:
            consola.linea("")
            consola.linea(cont_barra.compacto(estado))
        return 0

    if args.json:
        sys.stdout.write(json.dumps(resumen, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        mostrar_contabilidad(consola, resumen, destino)
    return 0


def _atribucion_de_refutacion(args, proyecto, tarea):
    """La atribucion de una corrida de dev-refutador. `--unidad` y `--agente` no la contradicen."""
    if args.refutacion == TODAS_LAS_REFUTACIONES:
        raise FallaDelHarness(
            "contabilidad --refutacion necesita la unidad: una corrida del refutador es de una "
            "sola. Ejemplo:\n    dev-harness.py contabilidad %s --ingerir <ruta> "
            "--refutacion REF-001" % tarea)
    atribucion = orq_refutacion.atribucion(proyecto, tarea, args.refutacion)
    if args.unidad and args.unidad != atribucion["workUnitId"]:
        raise FallaDelHarness(
            "--unidad dice %s y %s es de la unidad de trabajo %s." % (
                args.unidad, args.refutacion, atribucion["workUnitId"]))
    if args.agente and args.agente != atribucion["agentId"]:
        raise FallaDelHarness(
            "--agente dice %s y una refutacion la corre %s." % (
                args.agente, atribucion["agentId"]))
    return atribucion


def _plata_o_nd(moneda, valor):
    if valor is None:
        return "sin resolver"
    if valor == cont_presentacion.ND:
        return valor                                  # un piso no es el total
    return "%s %.4f" % (moneda, valor)


def mostrar_contabilidad(consola, resumen, destino):
    from contabilidad import tiempo as cont_tiempo

    # Lo que una persona lee: un numero de una familia sin resolver es N/D (Wave 5).
    resumen = cont_presentacion.para_mostrar(resumen)
    costo = resumen["cost"]
    moneda = costo.get("currency") or ""
    consola.linea("")
    consola.linea("%s — contabilidad de ejecución" % (resumen["taskId"] or "(sin tarea)"))
    consola.linea("-" * 60)
    consola.linea("Eventos      %d contados · %d duplicados descartados · %d correcciones"
                  % (resumen["events"]["counted"], resumen["events"]["duplicates"],
                     resumen["events"]["corrections"]))
    consola.linea("Tokens       input %s · output %s · cache read %s · cache creation %s" % (
        resumen["tokens"]["inputTokens"], resumen["tokens"]["outputTokens"],
        resumen["tokens"]["cacheReadTokens"], resumen["tokens"]["cacheCreationTokens"]))
    consola.linea("Ventana      %s (es una foto, no una suma)"
                  % (resumen["context"]["contextTokens"]
                     if resumen["context"]["contextTokens"] is not None else "sin resolver"))
    consola.linea("Tiempo       pared %s · modelo %s · tools %s  [%s]" % (
        cont_tiempo.como_texto(resumen["time"].get("wallMs")),
        cont_tiempo.como_texto(resumen["time"].get("modelMs")),
        cont_tiempo.como_texto(resumen["time"].get("toolMs")),
        resumen.get("timeSource", "")))
    consola.linea("Costo real   %s" % _plata_o_nd(moneda, costo.get("actual")))
    consola.linea("Equivalente  %s  ← lo que habría costado por API, no lo gastado"
                  % _plata_o_nd(moneda, costo.get("apiEquivalentEstimated")))

    for titulo, filas in (("Por agente", resumen["byAgent"]),
                          ("Por unidad de trabajo", resumen["byWorkUnit"]),
                          ("Por modelo", resumen["byModel"])):
        if filas:
            consola.linea("")
            consola.linea(titulo)
            for fila in filas:
                consola.linea("  %-28s %6d ev · in %s / out %s" % (
                    fila["id"], fila["events"], fila["tokens"]["inputTokens"],
                    fila["tokens"]["outputTokens"]))

    sin_unidad = resumen["unattributed"]["workUnitId"]
    if sin_unidad["events"]:
        consola.linea("")
        consola.linea("Sin atribuir a una unidad: %d eventos, %s tokens de output. "
                      "No se reparten." % (sin_unidad["events"],
                                           sin_unidad["tokens"]["outputTokens"]))

    if resumen.get("budget"):
        consola.linea("")
        consola.linea(cont_presupuesto.texto_de_decision(resumen["budget"]))

    if resumen["unresolved"]:
        consola.linea("")
        consola.linea("Sin resolver")
        for estado in resumen["unresolved"]:
            consola.linea("  · " + estado)

    consola.linea("")
    consola.linea("Resumen: %s" % destino)


# -- el reporte de seguridad ---------------------------------------------------

def reportar_seguridad(args, proyecto, consola):
    """Del libro de seguridad de una tarea a su resumen y su tablero.

    No corre ningun check y no aprueba nada. `--conocimiento` agrega al libro el estado de
    ES0902 que dejo `fuentes`; `--resumen` escribe `security-summary.json`; `--reporte` escribe
    ademas el md y el html. Sin ninguno, muestra el estado sin escribir nada.
    """
    tarea = seg_libro.validar_tarea(str(args.argumento or ""))
    ruta_libro = seg_libro.ruta_de(proyecto, tarea)

    if args.conocimiento:
        doc = orq_frescura.leer(orq_frescura.ruta_por_defecto(proyecto))
        if not doc:
            raise FallaDelHarness(
                "no hay %s en el proyecto: el estado del conocimiento sale de ahi. Corré "
                "primero:\n    dev-harness.py fuentes" % orq_frescura.ARCHIVO)
        alcance = {"project": os.path.basename(os.path.normpath(proyecto)), "environment": None}
        eventos = seg_productores.desde_frescura(doc, tarea, alcance)
        escritos, salteados, hallazgos = seg_libro.agregar_varios(ruta_libro, eventos)
        consola.evento("seguridad.conocimiento", escritos=escritos, repetidos=salteados)
        for hallazgo in hallazgos:
            consola.linea("  · " + hallazgo)

    if args.refutacion:
        eventos = _eventos_de_refutacion(proyecto, tarea)
        escritos, salteados, hallazgos = seg_libro.agregar_varios(ruta_libro, eventos)
        consola.evento("seguridad.refutacion", escritos=escritos, repetidos=salteados)
        for hallazgo in hallazgos:
            consola.linea("  · " + hallazgo)

    resumen = seg_resumen.generar(proyecto, tarea)
    destinos = []
    if args.resumen or args.reporte:
        destinos.append(seg_resumen.escribir(
            resumen, seg_libro.ruta_de(proyecto, tarea, seg_libro.RESUMEN)))
        consola.evento("seguridad.resumen", eventos=resumen["ledger"]["events"],
                       estado=resumen["systemSecurityState"])
    if args.reporte:
        destinos.extend(seg_reporte.escribir(resumen, seg_libro.carpeta_de(proyecto, tarea)))
        consola.evento("seguridad.reporte", destino=_relativa(
            proyecto, seg_libro.carpeta_de(proyecto, tarea)))

    if args.json:
        sys.stdout.write(seg_resumen.como_texto(resumen))
    else:
        mostrar_seguridad(consola, resumen, [_relativa(proyecto, d) for d in destinos])
    return 0


def _eventos_de_refutacion(proyecto, tarea):
    """Los veredictos de las unidades ES0902, como eventos del libro de seguridad de siempre."""
    _, unidades, veredictos = orq_refutacion.leer(proyecto, tarea)
    por_id = {v["refutationUnitId"]: v for v in veredictos}
    eventos = []
    for u in unidades:
        v = por_id.get(u["refutationUnitId"])
        if v is None or u["status"] != orq_refutacion.RESUELTA:
            continue
        if u["standard"]["id"] != "ES0902":
            continue
        alcance = {"project": os.path.basename(os.path.normpath(proyecto)), "environment": None,
                   "commitSha": u.get("repoRevision")}
        eventos.extend(seg_productores.desde_refutacion(v, u, tarea, alcance))
    return eventos


def mostrar_seguridad(consola, resumen, destinos):
    cobertura = resumen["coverage"]
    consola.linea("")
    consola.linea("%s — estado de seguridad" % resumen["taskId"])
    consola.linea("-" * 60)
    consola.linea("Sistema      %s" % resumen["systemSecurityState"])
    consola.linea("Bloqueos     %d" % len(resumen["blockingConditions"]))
    consola.linea("Cobertura    evaluada %s · resuelta %s  (%d aplicables)" % (
        seg_reporte.porciento(cobertura["assessmentCoveragePct"]),
        seg_reporte.porciento(cobertura["evidenceResolutionPct"]),
        cobertura["applicableRules"]))
    consola.linea("Evaluación   %s" % resumen["assessmentState"])
    consola.linea("Aprobación   %s" % resumen["officialApprovalStatus"])
    consola.linea("ES0902       %s · frescura %s" % (
        seg_reporte.texto(resumen["knowledge"].get("version")),
        seg_reporte.texto(resumen["knowledge"].get("freshness"))))
    for bloqueo in resumen["blockingConditions"][:5]:
        consola.linea("  · %s  %s" % (bloqueo["source"], bloqueo["title"]))
    if resumen["officialApprovalStatus"] != seg_reporte.EXTERNA:
        consola.linea("")
        consola.linea(seg_reporte.AVISO_OFICIAL)
    for destino in destinos:
        consola.linea("Escrito: %s" % destino)


# -- la refutacion atomica -----------------------------------------------------

def refutar(args, proyecto, consola):
    """Bloque 3: la refutacion atomica. No llama a ningun modelo.

    `--compile` arma las unidades y resuelve lo que un check o la cache ya resuelven;
    `--unit` entrega una unidad a dev-refutador; `--record` valida y guarda lo que devolvio;
    `--status` y `--summary` muestran. La sesion corre al refutador; esto no.
    """
    clave = args.argumento
    elegidos = [n for n in ("compile", "status", "unit", "record", "summary")
                if getattr(args, "refutar_" + n)]
    if len(elegidos) != 1:
        raise FallaDelHarness(
            "refute necesita exactamente una de --compile, --status, --unit, --record o "
            "--summary. Ejemplo:\n    dev-harness.py refute %s --compile" % clave)
    accion = elegidos[0]

    if accion == "compile":
        # La compuerta de REFUTATION va antes de tocar nada: si no pasa, no se crea ni se
        # cambia run.json (docs/cambios/flujo-precondiciones/spec.md).
        # La compuerta la evalua compilar mismo, con su propia lectura del .env (Wave 6): aca
        # solo se convierte el rechazo en el mensaje de siempre.
        try:
            doc = orq_refutacion.compilar(proyecto, clave)
        except orq_refutacion.CompuertaCerrada as cerrada:
            # El estado dice por que no se compilo antes de que el comando salga.
            reconciliar_estado(consola, proyecto, rutas_de(proyecto), clave)
            raise FallaDelHarness(
                "no se compila la refutacion de %s: %s. Resolvé eso y volvé a correr "
                "`refute %s --compile`." % (clave, ", ".join(cerrada.codigos), clave))
        consola.evento("refutacion.compilada", unidades=doc["counts"]["units"],
                       estado=doc["status"])
        reconciliar_estado(consola, proyecto, rutas_de(proyecto), clave)
        return _mostrar_refutacion(args, consola, doc, orq_refutacion.texto_de_estado(doc))

    if accion == "unit":
        entrega = orq_refutacion.para_refutar(proyecto, clave, args.refutar_unit)
        sys.stdout.write(json.dumps(entrega, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 0

    if accion == "record":
        if not os.path.isfile(args.refutar_record):
            raise FallaDelHarness("no existe el veredicto %s." % args.refutar_record)
        with io.open(args.refutar_record, encoding="utf-8-sig") as f:
            texto = f.read()
        guardados = orq_refutacion.registrar(proyecto, clave, texto)
        reconciliar_estado(consola, proyecto, rutas_de(proyecto), clave)
        for v in guardados:
            consola.evento("refutacion.registrada", unidad=v["refutationUnitId"],
                           veredicto=v["verdict"])
        doc, _, _ = orq_refutacion.leer(proyecto, clave)
        return _mostrar_refutacion(args, consola, doc, orq_refutacion.texto_de_estado(doc))

    doc, _, _ = orq_refutacion.leer(proyecto, clave)
    if accion == "status":
        return _mostrar_refutacion(args, consola, doc, orq_refutacion.texto_de_estado(doc))

    bloque4 = _bloque4_de_refutacion(proyecto, clave)
    if args.json:
        sys.stdout.write(json.dumps({"taskKey": doc["meta"]["taskKey"], "status": doc["status"],
                                     "counts": doc["counts"], "block4": bloque4},
                                    ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 0
    consola.linea(orq_refutacion.texto_de_resumen(doc, bloque4))
    return 0


def reconciliar_estado(consola, proyecto, rutas, clave):
    """Deja el estado del flujo de la tarea al dia con lo que el comando acaba de escribir.

    Una falla se avisa y no voltea el comando: el estado es derivado, se reconstruye, y el
    comando ya aplico sus propias compuertas (docs/cambios/estado-del-flujo/spec.md).
    """
    try:
        estado_persistencia.reconciliar(proyecto, clave, version_de(rutas))
    except Exception as e:                              # noqa: BLE001 - derivado, no voltea
        sys.stderr.write("harness: aviso: no se pudo actualizar el estado del flujo de %s: %s\n"
                         % (clave, e))


_DECISIONES_DEL_FLUJO = (("flujo_approve", "APPROVE"), ("flujo_alternative", "USE_ALTERNATIVE"),
                         ("flujo_choose", "CHOOSE"), ("flujo_cancel", "CANCEL"),
                         ("flujo_answer", "ANSWER"))


def mostrar_flujo(args, proyecto, rutas, consola=None, almacen=None, timeout=None, transporte=None):
    """`flujo <KEY>`: --status muestra y no escribe; --resume revalida y reconcilia; --approve,
    --alternative, --choose, --cancel y --answer aplican una decision que la persona dejo
    registrada (human-intent/1.0). Ninguna lee un valor por la linea de comandos ni por consola."""
    clave = args.argumento
    decisiones_pedidas = [(accion, getattr(args, dest)) for dest, accion in _DECISIONES_DEL_FLUJO
                          if getattr(args, dest)]
    elegidas = int(bool(args.refutar_status)) + int(bool(args.flujo_resume)) + len(decisiones_pedidas)
    if elegidas != 1:
        raise FallaDelHarness(
            "flujo necesita exactamente una de --status, --resume, --approve, --alternative, "
            "--choose, --cancel o --answer. Ejemplo:\n    dev-harness.py flujo %s --status" % clave)
    if args.flujo_resume:
        # Retomar es revalidar la fuente de lo que estaba pendiente. Si era la configuracion de una
        # integracion (jira.*, gitlab.*, o su disponibilidad), se revalida por el camino de
        # siempre: el `.env` y una sonda, que es lo unico de --resume que sale a la red.
        guardado, _ = flujo_estado.leer(proyecto, clave)
        nombres = estado_decisiones.integraciones_a_revalidar(
            guardado, _json_o_vacio(os.path.join(proyecto, ".claude", "planes", clave + ".json")))
        if nombres:
            sys.stdout.write("Revalidando %s, la fuente de lo pendiente.\n" % ", ".join(nombres))
            registrar_capacidades(resolver_configuracion(rutas), almacen, timeout, consola, rutas,
                                  transporte)
        doc = estado_decisiones.retomar(proyecto, clave, version_de(rutas))
        sys.stdout.write(flujo_estado.texto(doc, [], proyecto) + "\n")
        return 0
    if decisiones_pedidas:
        accion, interaction_id = decisiones_pedidas[0]
        if not args.sesion:
            raise estado_decisiones.ErrorDeDecision(
                "HUMAN_INTENT_REQUIRED", "falta --sesion: la decision es de la sesion donde la "
                "escribio la persona.")
        record, doc = estado_decisiones.aplicar(
            proyecto, clave, accion, interaction_id, args.sesion, args.flujo_option or None,
            args.flujo_value or None, version_de(rutas))
        sys.stdout.write("Decisión aplicada: %s sobre %s de %s.\n" % (
            record["action"], record["interactionId"], clave))
        sys.stdout.write(flujo_estado.texto(doc, [], proyecto) + "\n")
        return 0
    # STATUS READS AUTHORITY: el texto y el JSON muestran el estado guardado, el mismo que lee la
    # compuerta (estado.leer). Nada de aca lo recalcula ni lo escribe; lo cambia --resume.
    guardado, error = flujo_estado.leer(proyecto, clave)
    if args.json:
        if guardado is None:
            raise FallaDelHarness(flujo_estado.texto_sin_autoridad(clave, error or flujo_estado.AUSENTE))
        sys.stdout.write(json.dumps(guardado, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 0
    derivado = flujo_estado.derivar(proyecto, clave, version_de(rutas))
    vigencia = flujo_estado.vigencia(guardado, derivado, error)
    if guardado is None:
        # Sin autoridad: se dice, y lo derivado va rotulado como lo que es, una vista previa.
        sys.stdout.write(flujo_estado.texto(derivado, vigencia, proyecto) + "\n")
        sys.stdout.write(flujo_estado.texto_sin_autoridad(clave, error or flujo_estado.AUSENTE) + "\n")
        return 0
    sys.stdout.write(flujo_estado.texto(guardado, vigencia, proyecto) + "\n")
    if flujo_estado.difiere(guardado, derivado):
        sys.stdout.write(flujo_estado.texto_de_revalidacion(derivado) + "\n")
    return 0


def _mostrar_refutacion(args, consola, doc, texto):
    if args.json:
        sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        consola.linea(texto)
    return 0


def _bloque4_de_refutacion(proyecto, clave):
    """Lo que el Bloque 4 tiene de la fase de refutacion, o None si no hay libro.

    Es la medicion de antes y despues: llamadas, tokens, tiempo y costo del refutador. Un
    acierto de cache o un check no aparecen, porque no son llamadas.
    """
    ruta = cont_libro.ruta_de(proyecto, clave)
    if not os.path.isfile(ruta):
        return None
    eventos = orq_refutacion.de_refutacion(cont_libro.leer(ruta))
    if not eventos:
        return {"events": 0}
    # Un numero de una familia sin resolver sale N/D, no como un cero medido (Wave 5).
    return cont_presentacion.para_refutacion(cont_agregacion.resumir(eventos, task_id=clave))


# -- presupuesto --context-defaults ----------------------------------------------

def _escribir_politica(ruta, datos):
    """Los bytes, con .tmp y os.replace: una politica a medio escribir no valida, y la barra la
    dibujaria como `presupuesto ilegible`."""
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    temporal = ruta + ".tmp"
    with io.open(temporal, "wb") as f:
        f.write(datos)
    os.replace(temporal, ruta)


def presupuesto(args, proyecto, rutas, consola):
    """`presupuesto`: la politica de la Context Bar. Con --context-defaults es lo UNICO del harness
    que escribe `.claude/harness.presupuesto.json`:

      · sin archivo, crea la politica por defecto, igual a la plantilla;
      · con una politica valida, le agrega solo contextWarningAt y contextErrorAt que falten, y
        deja el resto de las claves con sus valores y en su orden;
      · con una que no valida, no toca nada y lo dice.

    Nunca crea un softLimit ni un hardLimit.
    """
    ruta = rutas["presupuesto"]
    if not args.context_defaults:
        mostrar_politica_de_la_barra(consola, rutas)
        return 0

    ruta_plantilla, plantilla = plantilla_de_contexto()
    if plantilla is None or cont_presupuesto.umbrales_de_contexto_que_faltan(plantilla):
        raise FallaDelHarness(
            "no está la plantilla %s, no valida o no trae los dos umbrales de contexto. "
            "Instalá de nuevo con install.ps1." % cont_presupuesto.PLANTILLA_DE_CONTEXTO)
    clase, politica, motivo, faltan = politica_de_la_barra(rutas)
    umbrales = "WARNING %s / ERROR %s" % tuple(
        _porciento(plantilla["statusBar"][k]) for k in cont_presupuesto.UMBRALES_DE_CONTEXTO)

    if clase == cont_presupuesto.POLITICA_INVALIDA:
        raise FallaDelHarness(
            ".claude/harness.presupuesto.json no valida, y no se toca: %s\nArreglala a mano y "
            "volvé a correr `presupuesto --context-defaults`." % _motivo_en_una_linea(motivo))
    if clase == cont_presupuesto.POLITICA_AUSENTE:
        with io.open(ruta_plantilla, "rb") as f:
            _escribir_politica(ruta, f.read())
        consola.linea("Se creó .claude/harness.presupuesto.json con la política por defecto: "
                      "contexto %s, sin presupuesto monetario." % umbrales)
        return 0
    if not faltan:
        consola.linea("La política ya tiene los dos umbrales de contexto: no se tocó.")
        return 0
    nueva = cont_presupuesto.con_umbrales_de_contexto(politica, plantilla)
    _escribir_politica(ruta, (json.dumps(nueva, ensure_ascii=False, indent=2) + "\n")
                       .encode("utf-8"))
    consola.linea("Se agregó a .claude/harness.presupuesto.json: %s. El resto de la política "
                  "quedó igual." % ", ".join(
                      "%s %s" % (k, nueva["statusBar"][k]) for k in faltan))
    return 0


# -- comandos ------------------------------------------------------------------

def comando(args, transporte=None, transporte_bytes=None):
    proyecto = os.path.abspath(args.proyecto)
    if not os.path.isdir(proyecto):
        raise FallaDelHarness("el proyecto %s no existe." % proyecto)

    rutas = rutas_de(proyecto)

    # Antes de armar la configuracion de las integraciones: `harness` no las necesita, y un
    # harness.integraciones.json roto no puede impedir ver el estado.
    if args.comando == "harness":
        return mostrar_harness(args, proyecto, rutas)

    consola = Consola(args.json, eventos=not (args.comando == "estado" and args.resumen))
    almacen = AlmacenSecretos(rutas["env"])
    timeout = timeout_de(rutas)

    # 🔴 El refresco normativo, solo donde se usa conocimiento normativo: armar un plan,
    # compilar una refutacion, el estado de seguridad. Ninguno corta aca: refresca y avisa, y la
    # operacion decide despues por las fuentes que exige (integracion-0.28.md, decision A).
    if args.comando == "plan":
        if not args.plantilla:
            compuerta_normativa(args, proyecto, rutas, consola, args.argumento, transporte,
                                transporte_bytes)
        return planificar(args, proyecto, rutas, consola)

    if args.comando == "contabilidad":
        return contabilizar(args, proyecto, rutas, consola)

    if args.comando == "presupuesto":
        return presupuesto(args, proyecto, rutas, consola)

    if args.comando == "seguridad":
        compuerta_normativa(args, proyecto, rutas, consola, args.argumento, transporte,
                            transporte_bytes)
        return reportar_seguridad(args, proyecto, consola)

    if args.comando == "refute":
        if args.refutar_compile:
            compuerta_normativa(args, proyecto, rutas, consola, args.argumento, transporte,
                                transporte_bytes)
        return refutar(args, proyecto, consola)

    if args.comando == "flujo":
        return mostrar_flujo(args, proyecto, rutas, consola, almacen, timeout, transporte)

    # Todo lo que sigue toca integraciones: primero el .env, despues el resto.
    config = resolver_configuracion(rutas)

    if args.comando == "contexto":
        return resolver_contexto(args, proyecto, rutas, config, almacen, timeout,
                                 consola, transporte, transporte_bytes)

    if args.comando == "fuentes":
        return resolver_fuentes(args, proyecto, rutas, config, almacen, timeout,
                                consola, transporte, transporte_bytes)

    if args.comando in ("setup", "reconfigurar"):
        # Muestra, no pregunta: la configuracion se completa en el .env.
        consola.linea("GCBA Development Harness — configuración")
        consola.linea("")
        mostrar_configuracion(consola, config,
                              args.argumento if args.comando == "reconfigurar" else None)
        consola.linea("")
        consola.linea("Para cambiar algo, editá %s (Claude no puede leerlo) y volvé a correr "
                      "`dev-harness.py %s`: se revalida." % (
                          rutas["env"], "reconfigurar " + args.argumento
                          if args.comando == "reconfigurar" else "setup"))
    elif not args.json and not args.resumen:
        consola.linea("Modo de configuración: %s" % entorno.MODO)

    if consola.eventos:
        consola.linea("")
    registro, documento = registrar_capacidades(config, almacen, timeout, consola, rutas, transporte)
    consola.evento("harness.listo", disponibles=len(registro.disponibles()))

    if args.comando == "estado" and args.resumen and not args.json:
        mostrar_resumen(documento, config)
        return 0
    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        mostrar(consola, documento, proyecto, rutas)
    if args.comando == "setup":
        mostrar_politica_de_la_barra(consola, rutas)
    return 0


def parser():
    p = argparse.ArgumentParser(
        prog="dev-harness.py",
        description="Integraciones y contexto de tarea del harness de desarrollo.")
    p.add_argument("comando", choices=("setup", "estado", "reconfigurar", "contexto", "plan",
                                       "contabilidad", "fuentes", "seguridad", "harness",
                                       "refute", "flujo", "presupuesto"))
    p.add_argument("argumento", nargs="?",
                   help="la integracion, para reconfigurar; la clave de Jira, para contexto")
    p.add_argument("--archivo", default="",
                   help="fuentes: el directorio con los originales, para resolver sin Jira")
    p.add_argument("--revalidar", action="store_true",
                   help="revalida las integraciones antes de resolver el contexto")
    p.add_argument("--plantilla", action="store_true",
                   help="plan: emite el esqueleto de la propuesta que el agente tiene que completar")
    p.add_argument("--propuesta", default="",
                   help="plan: la propuesta que escribio dev-orchestrator")
    p.add_argument("--replanificar", default="",
                   help="plan: la propuesta nueva, sobre un plan que ya existe")
    p.add_argument("--motivo", default="",
                   help="plan: por que se replanifica. Sin esto no se replanifica")
    p.add_argument("--ingerir", default="",
                   help="contabilidad: la fuente de uso que se ingiere al libro")
    p.add_argument("--adaptador", default="claude-code",
                   help="contabilidad: que adaptador lee la fuente")
    p.add_argument("--unidad", default="",
                   help="contabilidad: a que unidad de trabajo se atribuye lo ingerido")
    p.add_argument("--agente", default="",
                   help="contabilidad: a que agente se atribuye lo ingerido")
    p.add_argument("--reporte", action="store_true",
                   help="contabilidad: genera execution-cost.md; seguridad: el md y el html")
    p.add_argument("--conocimiento", action="store_true",
                   help="seguridad: agrega al libro el estado de ES0902 de harness.fuentes.json")
    p.add_argument("--resumen", action="store_true",
                   help="seguridad: escribe security-summary.json; estado: una linea por "
                        "integracion, sin eventos")
    p.add_argument("--barra", action="store_true",
                   help="contabilidad: muestra la barra de la sesion activa")
    p.add_argument("--sesion", default="",
                   help="contabilidad: que sesion es la activa, para la barra")
    p.add_argument("--compile", dest="refutar_compile", action="store_true",
                   help="refute: compila las unidades de refutacion del plan")
    p.add_argument("--status", dest="refutar_status", action="store_true",
                   help="refute: muestra cada unidad y como se resolvio")
    p.add_argument("--unit", dest="refutar_unit", default="",
                   help="refute: la unidad REF-001 (o un micro-lote REF-001,REF-002) para dev-refutador")
    p.add_argument("--record", dest="refutar_record", default="",
                   help="refute: el veredicto que devolvio dev-refutador, para validarlo y guardarlo")
    p.add_argument("--resume", dest="flujo_resume", action="store_true",
                   help="flujo: revalida desde las fuentes y reconcilia el estado")
    p.add_argument("--approve", dest="flujo_approve", default="",
                   help="flujo: aplica la aprobacion que la persona escribio (HARNESS APPROVE)")
    p.add_argument("--alternative", dest="flujo_alternative", default="",
                   help="flujo: aplica la alternativa que la persona eligio (HARNESS ALTERNATIVE)")
    p.add_argument("--choose", dest="flujo_choose", default="",
                   help="flujo: aplica el repositorio que la persona eligio (HARNESS CHOOSE)")
    p.add_argument("--cancel", dest="flujo_cancel", default="",
                   help="flujo: aplica la cancelacion que la persona escribio (HARNESS CANCEL)")
    p.add_argument("--answer", dest="flujo_answer", default="",
                   help="flujo: aplica la respuesta que la persona escribio (HARNESS ANSWER)")
    p.add_argument("--option", dest="flujo_option", default="",
                   help="flujo: la opcion de --alternative o --choose")
    p.add_argument("--value", dest="flujo_value", default="",
                   help="flujo: el valor de --answer; nunca un secreto")
    p.add_argument("--summary", dest="refutar_summary", action="store_true",
                   help="refute: el agregado y lo que el Bloque 4 tiene de la refutacion")
    p.add_argument("--refutacion", default="", nargs="?", const=TODAS_LAS_REFUTACIONES,
                   help="contabilidad: la unidad REF-001 a la que se atribuye lo ingerido; "
                        "seguridad: pasa los veredictos de ES0902 al libro de seguridad")
    p.add_argument("--aceptar", default="",
                   help="fuentes: acepta la identidad observada en esta corrida (ES0902 o "
                        "ES0902,ES0903): version, SHA-256, adjunto y canal")
    p.add_argument("--por", default="",
                   help="fuentes --aceptar: quien acepta. Por defecto, el usuario configurado")
    p.add_argument("--regresion", action="store_true",
                   help="fuentes --aceptar: admite una version anterior a la de fabrica, y deja "
                        "registrado cual se piso")
    p.add_argument("--auto", action="store_true",
                   help="fuentes: el refresco controlado, contra el canal que dejo la ultima corrida "
                        "(o la clave o --archivo que se pasen). No acepta nada")
    p.add_argument("--si-vence", action="store_true",
                   help="fuentes: refresca solo si la revision vencio segun la politica")
    p.add_argument("--disparador", default="",
                   help="fuentes --auto: INSTALL, HARNESS_UPDATE, EXPLICIT_SOURCES_COMMAND o "
                        "PRE_KNOWLEDGE_PROMOTION. Por defecto, EXPLICIT_SOURCES_COMMAND")
    p.add_argument("--proyecto", default=os.getcwd(),
                   help="raiz del proyecto (por defecto, el directorio actual)")
    p.add_argument("--json", action="store_true",
                   help="el registro de capacidades por stdout, para consumirlo; harness: el "
                        "estado en harness-installation/1.1")
    p.add_argument("--verbose", action="store_true",
                   help="harness: la version, la fecha, cada condicion con su id y los archivos leidos")
    p.add_argument("--reiniciar-bienvenida", action="store_true",
                   help="harness: la proxima sesion vuelve a mostrar la bienvenida completa")
    p.add_argument("--context-defaults", dest="context_defaults", action="store_true",
                   help="presupuesto: crea la politica por defecto de la Context Bar si falta, o le "
                        "agrega a la del proyecto los umbrales de contexto que no tenga. Nunca un "
                        "limite de plata")
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
            "la lista de procesos y en la transcripcion de la sesion. Ponelo en el .env local "
            "(JIRA_TOKEN, GITLAB_TOKEN) o en la variable de entorno correspondiente.\n")
        return 2

    if args.comando == "reconfigurar" and args.argumento not in NOMBRES:
        sys.stderr.write("reconfigurar necesita que le digas cual: %s\n" % ", ".join(NOMBRES))
        return 2

    if args.comando == "contexto" and not CLAVE_JIRA.match(str(args.argumento or "")):
        sys.stderr.write(
            "contexto necesita una clave de Jira, con la forma PROYECTO-123. "
            "Ejemplo: dev-harness.py contexto GCBA-1234\n")
        return 2

    if args.comando == "refute" and not CLAVE_JIRA.match(str(args.argumento or "")):
        sys.stderr.write(
            "refute necesita una clave de Jira, con la forma PROYECTO-123. "
            "Ejemplo: dev-harness.py refute GCBA-1234 --compile\n")
        return 2

    if args.comando == "flujo" and not CLAVE_JIRA.match(str(args.argumento or "")):
        sys.stderr.write(
            "flujo necesita una clave de Jira, con la forma PROYECTO-123. "
            "Ejemplo: dev-harness.py flujo GCBA-1234 --status\n")
        return 2

    if args.comando == "seguridad":
        # Antes de tocar el disco: un `..` o una barra sacarian la carpeta de la tarea de
        # `.claude/runtime/security/`.
        try:
            seg_libro.validar_tarea(str(args.argumento or ""))
        except seg_libro.TareaInvalida as e:
            sys.stderr.write("harness: %s Ejemplo: dev-harness.py seguridad GCBA-1234\n" % e)
            return 2

    try:
        return comando(args, transporte, transporte_bytes)
    except (FallaDelHarness, ConfigIlegible, ClaveProhibida, ErrorDeAlmacen,
            entorno.ErrorDeEntorno,
            contexto_ensamblador.ContratoInvalido,
            cont_presupuesto.PoliticaInvalida, cont_contrato.ContratoInvalido,
            seg_libro.EventoInvalido, seg_libro.TareaInvalida,
            seg_productores.ProductorInvalido, seg_resumen.ResumenInvalido,
            orq_refutacion.RefutacionInvalida, flujo_requeridos.RegistroInvalido,
            flujo_estado.ErrorDeEstado, estado_decisiones.ErrorDeDecision,
            orq_plan.PlanInvalido) as e:
        sys.stderr.write("harness: %s\n" % e)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\nharness: cancelado.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
