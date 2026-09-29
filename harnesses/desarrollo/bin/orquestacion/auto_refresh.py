"""El refresco del conocimiento confiable: CUANDO volver a mirar las fuentes, y con que permiso.

Contesta una sola pregunta: el conocimiento normativo que usa el harness, ¿sigue coincidiendo
con el canal autorizado? Para contestarla no trae nada propio:

    observar     integraciones/fuentes.py     la metadata primero, el documento si hace falta
    resolver     orquestacion/frescura.py     los doce estados, fallando cerrado
    derivados    orquestacion/procedencia.py  lo que frescura ya consulta
    agenda       lib/bienvenida.py            la politica, el vencimiento y la huella

Lo unico que es de este modulo es la agenda (.claude/runtime/knowledge-refresh.json): cuando se
intento, cuando salio bien, cuando vence, con que disparador y con que error. Spec:
docs/cambios/conocimiento-auto-refresco/spec.md.

🔴 **No es autoridad de nada.** La identidad de una fuente es de `source-registry.json`, lo
observado y lo decidido de `harness.fuentes.json`. La lista `sources` de la agenda es un resumen
que se reconstruye del canonico en cada escritura.

🔴 **No decide por una persona.** Ningun camino de aca acepta, pospone ni promueve: una version
nueva queda `UPDATE_AVAILABLE` hasta que alguien corra `fuentes --aceptar`.

🔴 **Una falla no borra lo que se sabia.** Si el canal no contesta, `harness.fuentes.json` no se
toca y `lastSuccessfulCheckAt` tampoco. Se anota el intento y el codigo.

🔴 **El permiso es el Registro de Capacidades.** Un canal de Jira pide las tres capacidades de
lectura en ENABLED; la autenticacion sola no alcanza. Sin ellas no se sale a la red. Este modulo
no arma adaptadores ni lee configuracion: el observador de Jira lo inyecta la CLI.
"""
import importlib.util
import io
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from integraciones import fuentes as int_fuentes  # noqa: E402
from . import frescura                           # noqa: E402
from . import registro_fuentes                   # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO_POLITICA = "knowledge-refresh-policy.json"
SCHEMA_AGENDA = "knowledge-refresh-state.schema.json"
VERSION_AGENDA = "knowledge-refresh-state/1.0"

# -- disparadores --------------------------------------------------------------

INSTALL = "INSTALL"
HARNESS_UPDATE = "HARNESS_UPDATE"
EXPLICIT_SOURCES_COMMAND = "EXPLICIT_SOURCES_COMMAND"
PRE_KNOWLEDGE_PROMOTION = "PRE_KNOWLEDGE_PROMOTION"
PRE_NORMATIVE_OPERATION_IF_STALE = "PRE_NORMATIVE_OPERATION_IF_STALE"
SESSION_START_IF_STALE = "SESSION_START_IF_STALE"
DISPARADORES = (INSTALL, HARNESS_UPDATE, EXPLICIT_SOURCES_COMMAND, PRE_KNOWLEDGE_PROMOTION,
                PRE_NORMATIVE_OPERATION_IF_STALE, SESSION_START_IF_STALE)

# Que interruptor de `triggers` habilita cada uno. SESSION_START_IF_STALE no tiene: lo habilita
# `sessionStartNetwork`, que por defecto es false.
_INTERRUPTOR = {INSTALL: "install", HARNESS_UPDATE: "harnessUpdate",
                EXPLICIT_SOURCES_COMMAND: "explicitSources",
                PRE_KNOWLEDGE_PROMOTION: "preKnowledgePromotion",
                PRE_NORMATIVE_OPERATION_IF_STALE: "preNormativeOperationIfStale"}
# Los que refrescan solo si la agenda vencio. Los otros son eventos: refrescan siempre.
_SOLO_SI_VENCE = (PRE_NORMATIVE_OPERATION_IF_STALE, SESSION_START_IF_STALE)

# -- codigos -------------------------------------------------------------------

NO_VENCIDO = "AUTO_REFRESH_NOT_DUE"
DISPARADOR_APAGADO = "AUTO_REFRESH_TRIGGER_DISABLED"
SIN_CAPACIDAD = "AUTO_REFRESH_BLOCKED_CAPABILITY"
SIN_CANAL = "AUTO_REFRESH_CHANNEL_UNAVAILABLE"
TIMEOUT = "AUTO_REFRESH_TIMEOUT"
OBSERVACION_FALLIDA = "AUTO_REFRESH_SOURCE_OBSERVATION_FAILED"
AGENDA_ILEGIBLE = "AUTO_REFRESH_STATE_UNREADABLE"
AGENDA_SIN_ESCRIBIR = "AUTO_REFRESH_STATE_WRITE_FAILED"
POLITICA_INVALIDA = "AUTO_REFRESH_POLICY_INVALID"
# Los que no son una falla: no habia que refrescar.
_SIN_FALLA = (None, NO_VENCIDO, DISPARADOR_APAGADO)

# Lo que un canal de Jira necesita, en ENABLED en harness.capacidades.json. La lectura del adjunto
# esta a proposito: sin ella la integridad de una fuente no se puede verificar, y Jira puede estar
# AVAILABLE igual.
CAPACIDADES_DE_JIRA = ("jira.issue.read", "jira.issue.search", "jira.attachment.read")

# -- la compuerta --------------------------------------------------------------

PERMITIDO = "allowed"
BLOQUEADO = "blocked"
SIN_RESOLVER = "unresolved"


class ObservacionFallida(Exception):
    """Lo que levanta un observador que no pudo mirar. Lleva un codigo, nunca una respuesta."""

    def __init__(self, codigo, motivo=""):
        Exception.__init__(self, motivo or codigo)
        self.codigo = codigo


# -- la biblioteca de la bienvenida ------------------------------------------------

_BIENVENIDA = []


def bienvenida():
    """lib/bienvenida.py, por ruta, como la carga la CLI. Ahi viven la politica, el vencimiento y
    la huella: una sola definicion para lo que muestra SessionStart y lo que decide este modulo."""
    if _BIENVENIDA:
        return _BIENVENIDA[0]
    raiz = rutas.raiz_del_harness(__file__)
    ruta = os.path.join(raiz, "hooks", "lib", "bienvenida.py") if raiz else None
    if not ruta or not os.path.isfile(ruta):
        raise RuntimeError("no se encontro hooks/lib/bienvenida.py al lado del harness")
    spec = importlib.util.spec_from_file_location("harness_bienvenida_refresco", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _BIENVENIDA.append(modulo)
    return modulo


# -- politica y agenda -------------------------------------------------------------

def cargar_politica(proyecto, ruta=None):
    """(politica, codigo). Una politica que no valida cae a la segura: solo el pedido explicito."""
    ruta = ruta or roster.ruta_de_regla(ARCHIVO_POLITICA, __file__)
    b = bienvenida()
    if not ruta:
        return dict(b.POLITICA_SEGURA), POLITICA_INVALIDA
    return b.leer_politica(proyecto, ruta)


def ruta_de_la_agenda(proyecto):
    return bienvenida().ruta_de_la_agenda(proyecto)


def leer_agenda(proyecto):
    """(agenda, codigo). Rota es (None, AUTO_REFRESH_STATE_UNREADABLE): cuenta como nunca revisada."""
    return bienvenida().leer_agenda(proyecto)


def vencido(politica, agenda, momento):
    return bienvenida().vencido(politica, agenda, momento)


def debe_refrescar(politica, disparador, agenda, momento):
    """(True, None) si este disparador sale al canal ahora; si no, (False, codigo)."""
    if disparador not in DISPARADORES:
        raise ValueError("disparador desconocido: %s" % disparador)
    if disparador == SESSION_START_IF_STALE:
        if politica.get("sessionStartNetwork") is not True:
            return False, DISPARADOR_APAGADO
    elif not (politica.get("triggers") or {}).get(_INTERRUPTOR[disparador]):
        return False, DISPARADOR_APAGADO
    if disparador in _SOLO_SI_VENCE and not vencido(politica, agenda, momento):
        return False, NO_VENCIDO
    return True, None


def faltan_capacidades(capacidades):
    """Las de CAPACIDADES_DE_JIRA que no estan ENABLED en el registro."""
    capacidades = capacidades or {}
    return [c for c in CAPACIDADES_DE_JIRA if capacidades.get(c) != "ENABLED"]


# -- el canal ------------------------------------------------------------------

def canal_previsto(proyecto, clave=None, directorio=None):
    """A donde se mira, o None si no hay adonde.

    Un directorio o una clave de tarea que se pasaron ganan. Si no, el canal que dejo la ultima
    corrida en harness.fuentes.json: `archivo:<dir>` si el directorio sigue estando, `jira:<FICHA>`.
    """
    if directorio:
        return {"kind": "archivo", "dir": os.path.abspath(directorio)}
    if clave:
        return {"kind": "jira-tarea", "key": str(clave)}
    anterior = frescura.leer(frescura.ruta_por_defecto(proyecto))
    canal = str((anterior.get("ficha") or {}).get("channel") or "")
    if canal.startswith("archivo:") and os.path.isdir(canal[len("archivo:"):]):
        return {"kind": "archivo", "dir": canal[len("archivo:"):]}
    if canal.startswith("jira:") and canal[len("jira:"):]:
        return {"kind": "jira-ficha", "key": canal[len("jira:"):]}
    return None


def es_de_jira(canal):
    return bool(canal) and str(canal.get("kind", "")).startswith("jira")


def texto_de_canal(canal):
    if not canal:
        return None
    if canal.get("kind") == "archivo":
        return "archivo:%s" % canal["dir"]
    return "jira:%s" % canal.get("key")


def _observar_archivos(canal, entradas, previo):
    del previo
    # Un directorio que ya no esta es un canal que no contesta, no seis fuentes que faltan.
    if not os.path.isdir(canal["dir"]):
        raise ObservacionFallida(SIN_CANAL, "el directorio %s no existe" % canal["dir"])
    observaciones = int_fuentes.observar_archivos(entradas, canal["dir"])
    return ({"reachable": True, "reason": "originales leidos de %s" % canal["dir"],
             "channel": "archivo:%s" % canal["dir"]}, observaciones)


# -- el camino compartido con `fuentes` -------------------------------------------

def contexto_de_fuentes(proyecto):
    """(entradas, destino, previo, decisiones). Lo mismo que lee `fuentes` a mano.

    Levanta registro_fuentes.RegistroInvalido: un registro que no se lee entero no se lee a medias.
    """
    entradas = registro_fuentes.gestionadas(registro_fuentes.cargar())
    destino = frescura.ruta_por_defecto(proyecto)
    anterior = frescura.leer(destino)
    return (entradas, destino, anterior.get("sources") or {},
            anterior.get("decisions") or {})


def _sin_fecha(doc):
    return {k: v for k, v in (doc or {}).items() if k != "verified_at"}


def resolver_y_escribir(entradas, observaciones, canal, decisiones, destino,
                        solo_si_cambia=False):
    """frescura.documento + frescura.escribir. El UNICO camino del manual y del automatico:
    misma evidencia, mismos estados.

    Con `solo_si_cambia` -el automatico- un documento igual al que ya esta, salvo la fecha, no
    se reescribe: una revision sin novedades no toca harness.fuentes.json. Cuando se miro lo dice
    la agenda. `fuentes` a mano escribe siempre, como siempre.
    """
    documento = frescura.documento(entradas, observaciones, canal, decisiones)
    if solo_si_cambia:
        anterior = frescura.leer(destino)
        if anterior and _sin_fecha(json.loads(json.dumps(documento))) == _sin_fecha(anterior):
            return anterior
    frescura.escribir(documento, destino)
    return documento


# -- la agenda -----------------------------------------------------------------

def resumen_de_fuentes(doc_fuentes):
    """La lista `sources` de la agenda, reconstruida del canonico."""
    b = bienvenida()
    fuentes = (doc_fuentes or {}).get("sources")
    salida = []
    for sid in sorted(fuentes if isinstance(fuentes, dict) else {}):
        e = fuentes[sid] if isinstance(fuentes[sid], dict) else {}
        aceptada, observada = b.versiones_de(e)
        salida.append({"id": str(sid), "acceptedVersion": aceptada, "observedVersion": observada,
                       "sourceState": str(e.get("state") or "UNREADABLE")})
    return salida


def _estado_de_exito(doc_fuentes):
    fuentes = (doc_fuentes or {}).get("sources") or {}
    al_dia = all(isinstance(f, dict) and f.get("state") in frescura.NO_BLOQUEAN
                 for f in fuentes.values())
    return "CURRENT" if al_dia else "SUCCEEDED_WITH_UPDATES"


def registrar(proyecto, momento, disparador, politica, codigo=None, documento=None, canal=None):
    """Escribe la agenda de este intento. Devuelve la agenda escrita.

    Con `codigo` es una falla: se anota el intento y se CONSERVAN lastSuccessfulCheckAt y
    nextCheckDueAt. Sin codigo salio bien: los dos se mueven.
    """
    b = bienvenida()
    previa, _ = leer_agenda(proyecto)
    previa = previa or {}
    doc_fuentes = documento if documento is not None else \
        frescura.leer(frescura.ruta_por_defecto(proyecto))
    salio_bien = codigo is None
    if salio_bien:
        ultima = momento
        proxima = b.mas_horas(momento, politica.get("maxAgeHours")) \
            if politica.get("mode") == b.EVENT_AND_TTL else None
        estado = _estado_de_exito(doc_fuentes)
    else:
        ultima = previa.get("lastSuccessfulCheckAt")
        proxima = previa.get("nextCheckDueAt")
        estado = "UNRESOLVED"
    agenda = {
        "schema_version": VERSION_AGENDA,
        "state": estado,
        "lastAttemptAt": momento,
        "lastSuccessfulCheckAt": ultima,
        "nextCheckDueAt": proxima,
        "trigger": disparador,
        "errorCode": codigo,
        "channel": canal or previa.get("channel"),
        "notificationFingerprint": b.huella_de_notificacion(doc_fuentes),
        "sources": resumen_de_fuentes(doc_fuentes),
    }
    escribir_agenda(ruta_de_la_agenda(proyecto), agenda)
    return agenda


def reconstruir_si_difiere(proyecto):
    """Si la lista `sources` de la agenda no es la del canonico, se reescribe desde el canonico.
    Nada de la agenda de fechas cambia. Devuelve True si reescribio."""
    agenda, _ = leer_agenda(proyecto)
    if agenda is None:
        return False
    doc_fuentes = frescura.leer(frescura.ruta_por_defecto(proyecto))
    canonico = resumen_de_fuentes(doc_fuentes)
    huella = bienvenida().huella_de_notificacion(doc_fuentes)
    if agenda.get("sources") == canonico and agenda.get("notificationFingerprint") == huella:
        return False
    agenda = dict(agenda, sources=canonico, notificationFingerprint=huella)
    escribir_agenda(ruta_de_la_agenda(proyecto), agenda)
    return True


def validar_agenda(agenda):
    from . import tools
    armador = tools._armador()
    if armador is None:
        return ["no esta contexto-armar.py, de donde sale el validador"]
    ruta = rutas.localizar(("schemas", SCHEMA_AGENDA), __file__)
    if ruta is None:
        return ["no esta %s" % SCHEMA_AGENDA]
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(agenda, esquema)


def escribir_agenda(ruta, agenda):
    """Valida y escribe con un temporal propio + fsync + os.replace. Una agenda que no valida no
    se escribe. Levanta OSError o ValueError: quien llama lo convierte en su codigo.

    El temporal lleva pid y un uuid: dos escritores del mismo proceso tampoco se lo pisan. En
    Windows os.replace puede chocar con otro replace del mismo destino: se reintenta un poco.
    """
    errores = validar_agenda(agenda)
    if errores:
        raise ValueError("la agenda no valida contra %s: %s" % (VERSION_AGENDA, errores[0]))
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta, exist_ok=True)
    tmp = "%s.%d.%s.tmp" % (ruta, os.getpid(), uuid.uuid4().hex[:8])
    try:
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(agenda, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        for intento in range(20):
            try:
                os.replace(tmp, ruta)
                break
            except PermissionError:
                if intento == 19:
                    raise
                time.sleep(0.01)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return ruta


# -- el refresco ---------------------------------------------------------------

def refrescar(proyecto, disparador, observar_jira=None, capacidades=None, canal=None,
              momento=None, politica=None):
    """Refresca si corresponde. Devuelve el resultado, nunca levanta por una falla del canal.

    `observar_jira(canal, entradas, previo) -> (canal_doc, observaciones)` lo pasa la CLI: es el
    adaptador de Jira ya armado. Puede levantar ObservacionFallida con su codigo.
    `capacidades` es el mapa `capacidades` de harness.capacidades.json.
    """
    momento = momento or frescura.ahora()
    codigo_politica = None
    if politica is None:
        politica, codigo_politica = cargar_politica(proyecto)
    agenda, codigo_agenda = leer_agenda(proyecto)
    resultado = {"trigger": disparador, "refreshed": False, "errorCode": None,
                 "policyError": codigo_politica, "stateError": codigo_agenda,
                 "due": vencido(politica, agenda, momento), "mode": politica.get("mode"),
                 "channel": texto_de_canal(canal), "sources": [], "downloads": 0}

    corre, codigo = debe_refrescar(politica, disparador, agenda, momento)
    if not corre:
        resultado["errorCode"] = codigo
        try:
            reconstruir_si_difiere(proyecto)
        except (OSError, ValueError):
            resultado["errorCode"] = AGENDA_SIN_ESCRIBIR
        return _cerrar(resultado, proyecto)

    def falla(codigo_falla):
        resultado["errorCode"] = codigo_falla
        try:
            registrar(proyecto, momento, disparador, politica, codigo_falla,
                      canal=texto_de_canal(canal))
        except (OSError, ValueError):
            resultado["stateError"] = AGENDA_SIN_ESCRIBIR
        return _cerrar(resultado, proyecto)

    if canal is None:
        return falla(SIN_CANAL)
    if es_de_jira(canal):
        if faltan_capacidades(capacidades):
            # 🔴 Antes de la red: el observador no se llama.
            resultado["missingCapabilities"] = faltan_capacidades(capacidades)
            return falla(SIN_CAPACIDAD)
        if observar_jira is None:
            return falla(SIN_CANAL)
        observador = observar_jira
    else:
        observador = _observar_archivos

    try:
        entradas, destino, previo, decisiones = contexto_de_fuentes(proyecto)
    except registro_fuentes.RegistroInvalido:
        return falla(OBSERVACION_FALLIDA)
    try:
        canal_doc, observaciones = observador(canal, entradas, previo)
    except ObservacionFallida as e:
        return falla(e.codigo)
    except Exception:                         # noqa: BLE001 - una falla del canal no voltea nada
        return falla(OBSERVACION_FALLIDA)
    if not canal_doc or not canal_doc.get("reachable", True):
        return falla(SIN_CANAL)

    try:
        documento = resolver_y_escribir(entradas, observaciones, canal_doc, decisiones, destino,
                                        solo_si_cambia=True)
    except (OSError, ValueError):
        return falla(OBSERVACION_FALLIDA)
    resultado["refreshed"] = True
    resultado["downloads"] = sum(1 for o in observaciones if o.get("downloaded"))
    resultado["channel"] = canal_doc.get("channel") or texto_de_canal(canal)
    try:
        registrar(proyecto, momento, disparador, politica, None, documento, resultado["channel"])
    except (OSError, ValueError):
        resultado["stateError"] = AGENDA_SIN_ESCRIBIR
    return _cerrar(resultado, proyecto)


def _cerrar(resultado, proyecto):
    agenda, _ = leer_agenda(proyecto)
    agenda = agenda or {}
    doc_fuentes = frescura.leer(frescura.ruta_por_defecto(proyecto))
    resultado.update({
        "sources": resumen_de_fuentes(doc_fuentes),
        "state": agenda.get("state") or "NEVER_CHECKED",
        "lastAttemptAt": agenda.get("lastAttemptAt"),
        "lastSuccessfulCheckAt": agenda.get("lastSuccessfulCheckAt"),
        "nextCheckDueAt": agenda.get("nextCheckDueAt"),
        "notificationFingerprint": bienvenida().huella_de_notificacion(doc_fuentes),
    })
    return resultado


def fallo(resultado):
    """Si el refresco tenia que correr y no pudo."""
    return resultado.get("errorCode") not in _SIN_FALLA


# -- la compuerta normativa ----------------------------------------------------

def ensure_normative_knowledge_fresh(proyecto, observar_jira=None, capacidades=None, canal=None,
                                     disparador=PRE_NORMATIVE_OPERATION_IF_STALE, momento=None,
                                     politica=None):
    """Refresca si vencio y dice si el conocimiento normativo se puede usar.

    `allowed`     todas las fuentes que se siguen en CURRENT o RETIRED, y la agenda al dia
    `blocked`     alguna en un estado que la bienvenida ya trata como BLOCKED (una alerta de
                  integridad, un cambio con la misma version, una regresion)
    `unresolved`  todo lo demas: sin estado, pendiente, o vencida y sin poder refrescar

    🔴 No es una segunda regla de frescura: los estados son los de frescura.py y la gravedad es
    la de la bienvenida. Lo unico que agrega es no dar por vigente lo que no se pudo volver a mirar.
    """
    momento = momento or frescura.ahora()
    refresco = refrescar(proyecto, disparador, observar_jira, capacidades, canal, momento,
                         politica)
    if politica is None:
        politica, _ = cargar_politica(proyecto)
    agenda, _ = leer_agenda(proyecto)
    doc = frescura.leer(frescura.ruta_por_defecto(proyecto))
    fuentes = doc.get("sources") if isinstance(doc.get("sources"), dict) else {}
    estados = {sid: (f.get("state") if isinstance(f, dict) else None) for sid, f in fuentes.items()}
    bloquean = sorted(sid for sid, e in estados.items() if e in bienvenida().FUENTE_BLOQUEA)
    pendientes = sorted(sid for sid, e in estados.items() if e not in frescura.NO_BLOQUEAN)

    if bloquean:
        decision, motivo = BLOQUEADO, "fuentes en alerta: %s" % ", ".join(
            "%s %s" % (s, estados[s]) for s in bloquean)
    elif not estados:
        decision, motivo = SIN_RESOLVER, "no hay estado del conocimiento (corré `fuentes`)"
    elif fallo(refresco) or vencido(politica, agenda, momento):
        decision, motivo = SIN_RESOLVER, "la revisión venció y no se pudo volver a mirar (%s)" % (
            refresco.get("errorCode") or "sin refresco")
    elif pendientes:
        decision, motivo = SIN_RESOLVER, "fuentes no vigentes: %s" % ", ".join(
            "%s %s" % (s, estados[s]) for s in pendientes)
    else:
        decision, motivo = PERMITIDO, "todas las fuentes vigentes"
    return {"decision": decision, "reason": motivo, "sources": estados, "blocking": bloquean,
            "refresh": refresco}
