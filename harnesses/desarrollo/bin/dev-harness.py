#!/usr/bin/env python3
"""La CLI del harness de desarrollo: las integraciones y el contexto de una tarea.

    python .claude/harness/bin/desarrollo/dev-harness.py setup
    python .claude/harness/bin/desarrollo/dev-harness.py estado [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py reconfigurar jira|gitlab
    python .claude/harness/bin/desarrollo/dev-harness.py contexto GCBA-1234 [--json]
    python .claude/harness/bin/desarrollo/dev-harness.py seguridad GCBA-1234 [--conocimiento] [--resumen] [--reporte]

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

from integraciones import fuentes as int_fuentes                # noqa: E402

from orquestacion import frescura as orq_frescura                # noqa: E402
from orquestacion import plan as orq_plan                         # noqa: E402
from orquestacion import registro_fuentes as orq_fuentes         # noqa: E402

from contabilidad import agregacion as cont_agregacion            # noqa: E402
from contabilidad import barra as cont_barra                      # noqa: E402
from contabilidad import libro as cont_libro                      # noqa: E402
from contabilidad import presupuesto as cont_presupuesto          # noqa: E402
from contabilidad import reporte as cont_reporte                  # noqa: E402
from contabilidad.adaptadores import contrato as cont_contrato    # noqa: E402
from contabilidad.adaptadores import registro as cont_registro    # noqa: E402

from reporte_seguridad import libro as seg_libro                  # noqa: E402
from reporte_seguridad import productores as seg_productores      # noqa: E402
from reporte_seguridad import reporte as seg_reporte              # noqa: E402
from reporte_seguridad import resumen as seg_resumen              # noqa: E402

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
        # El presupuesto es un archivo aparte y NO tiene default en el manifiesto. Que no
        # exista es la respuesta correcta hasta que alguien declare uno: BUDGET_UNDEFINED.
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

def resolver_fuentes(args, proyecto, rutas, config, almacen, timeout, consola,
                     transporte, transporte_bytes):
    """Bloque 1: del registro de fuentes al estado de frescura de cada una.

    🔴 Sale 0 aunque haya fuentes en alerta. Una fuente desactualizada no es una falla del
    harness: es justo lo que este comando existe para poder decir. El codigo 2 queda para lo
    que la persona tiene que arreglar antes de seguir.

    🔴 Sin canal que consultar -ni una clave de Jira ni un directorio local- no se declara
    que este todo bien: se declara que no se pudo verificar, que es otra cosa.
    """
    try:
        registro = orq_fuentes.cargar()
    except orq_fuentes.RegistroInvalido as e:
        # Un registro que no se puede leer entero no se lee a medias: es lo que la persona
        # tiene que arreglar antes de seguir, y por eso sale 2 y no 0.
        raise FallaDelHarness(str(e))
    entradas = orq_fuentes.gestionadas(registro)
    for hallazgo in orq_fuentes.hallazgos(registro):
        consola.linea("  aviso: " + hallazgo)

    destino = orq_frescura.ruta_por_defecto(proyecto)
    anterior = orq_frescura.leer(destino)
    previo = anterior.get("sources") or {}
    decisiones = anterior.get("decisions") or {}

    canal = None
    observaciones = []

    if args.archivo:
        directorio = os.path.abspath(args.archivo)
        if not os.path.isdir(directorio):
            raise FallaDelHarness("el directorio %s no existe." % directorio)
        observaciones = int_fuentes.observar_archivos(entradas, directorio)
        canal = {"reachable": True, "reason": "originales leidos de %s" % directorio}
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

    documento = orq_frescura.documento(entradas, observaciones, canal, decisiones)
    try:
        orq_frescura.escribir(documento, destino)
    except (ValueError, OSError) as e:
        raise FallaDelHarness(str(e))
    consola.evento("fuentes.listo", fuentes=len(documento["sources"]),
                   pendientes=documento["pending_count"])

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        mostrar_fuentes(consola, documento, destino)
    return 0


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
    return {"key": clave_ficha, "issue_type": tipo, "reachable": True}, observaciones


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
    registro = _json_o_vacio(rutas["capacidades"]).get("capacidades") or {}
    config = _config_harness(rutas)
    destino = os.path.join(proyecto, ".claude", "planes", clave + ".json")

    if args.plantilla:
        sys.stdout.write(json.dumps(plantilla_de_propuesta(task_context, registro),
                                    ensure_ascii=False, indent=2) + "\n")
        return 0

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
                                   version_de(rutas), _relativa(proyecto, ruta_contexto))
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
                                   version_de(rutas), _relativa(proyecto, ruta_contexto))

    consola.evento("plan.armado", tarea=clave, unidades=len(documento["workUnits"]),
                   version=documento["meta"]["plan_version"])
    orq_plan.escribir(documento, destino)
    consola.evento("plan.estado", estado=documento["status"])

    if args.json:
        sys.stdout.write(json.dumps(documento, ensure_ascii=False, indent=2,
                                    sort_keys=True) + "\n")
    else:
        mostrar_plan(consola, documento, destino)
    return 0


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
        eventos_nuevos = cont_contrato.a_eventos(
            registros, tarea, args.adaptador, politica,
            workUnitId=args.unidad or None, agentId=args.agente or None)
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


def mostrar_contabilidad(consola, resumen, destino):
    from contabilidad import tiempo as cont_tiempo

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
    consola.linea("Costo real   %s" % (
        ("%s %.4f" % (moneda, costo["actual"])) if costo.get("actual") is not None
        else "sin resolver"))
    consola.linea("Equivalente  %s  ← lo que habría costado por API, no lo gastado" % (
        ("%s %.4f" % (moneda, costo["apiEquivalentEstimated"]))
        if costo.get("apiEquivalentEstimated") is not None else "sin resolver"))

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

    if args.comando == "plan":
        return planificar(args, proyecto, rutas, consola)

    if args.comando == "contabilidad":
        return contabilizar(args, proyecto, rutas, consola)

    if args.comando == "seguridad":
        return reportar_seguridad(args, proyecto, consola)

    if args.comando == "contexto":
        return resolver_contexto(args, proyecto, rutas, config, almacen, timeout,
                                 consola, transporte, transporte_bytes)

    if args.comando == "fuentes":
        return resolver_fuentes(args, proyecto, rutas, config, almacen, timeout,
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
    p.add_argument("comando", choices=("setup", "estado", "reconfigurar", "contexto", "plan",
                                       "contabilidad", "fuentes", "seguridad"))
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
                   help="seguridad: escribe security-summary.json")
    p.add_argument("--barra", action="store_true",
                   help="contabilidad: muestra la barra de la sesion activa")
    p.add_argument("--sesion", default="",
                   help="contabilidad: que sesion es la activa, para la barra")
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
            contexto_ensamblador.ContratoInvalido,
            cont_presupuesto.PoliticaInvalida, cont_contrato.ContratoInvalido,
            seg_libro.EventoInvalido, seg_libro.TareaInvalida,
            seg_productores.ProductorInvalido, seg_resumen.ResumenInvalido) as e:
        sys.stderr.write("harness: %s\n" % e)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\nharness: cancelado. No se guardo nada de lo que faltaba.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
