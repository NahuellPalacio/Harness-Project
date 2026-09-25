"""La bienvenida del harness y el estado general de una instalacion: READY, PARTIAL o BLOCKED.

Es el resolvedor UNICO. Lo usan session-start.py, `dev-harness.py harness` y `dev-harness.py
setup`, y el instalador escribe con el el archivo de estado. Vive en la lib de los hooks porque
el hook tiene que poder leerlo sin importar `harnesses/`, y un proyecto de solo `analisis`
tambien tiene hooks.

Lee archivos locales y nada mas:

    .claude/harness.lock.json           la version y los harness instalados (install.ps1)
    .claude/harness.installation.json   el estado de la instalacion y la marca de la bienvenida
    .claude/harness.capacidades.json    el `estado` por integracion que dejo el ultimo `setup`
    .claude/harness.fuentes.json        el `state` por fuente que dejo el ultimo `fuentes`
    .claude/settings.json               el bloque `statusLine`, y nada mas de ese archivo
    .claude/runtime/contextbar.json     la senal de vida de la Context Bar (ver abajo)
    .claude/runtime/accounting/         si la carpeta del libro del Bloque 4 se puede usar
    y lo que hay en disco del harness: contabilidad/, reporte_seguridad/ y sus schemas.

Desde `harness-installation/1.1` resuelve tambien `runtimeComponents`: la contabilidad del
Bloque 4, la Context Bar y el reporte de seguridad. Un componente que no esta ACTIVE suma su
condicion a pendingConditions y deja el estado en PARTIAL, nunca en BLOCKED: la observabilidad
caida no hace inseguro al harness. La unica excepcion es CONFIGURED de la Context Bar -
registrada, probada y sin cambio pendiente, esperando su primer dibujo en esta sesion-, que no
pide nada a nadie. Ningun componente usa AVAILABLE, que es de las integraciones.

🔴 No hace red, no llama a ningun modelo y no importa nada de fuera de la biblioteca estandar.
Lo que muestra es tan viejo como el ultimo `setup` y el ultimo `fuentes`: es el precio de no
consultar Jira en SessionStart, y por eso cada dato lleva de cuando es.

🔴 No recalcula ninguna frescura. El estado de una fuente es el que dejo `fuentes`, tal cual.

🔴 Nunca devuelve READY si algo no se pudo leer. Un archivo roto, o con un tipo que no es el
que escribe su dueno, es una condicion pendiente con su id, no un "no hay nada que decir".

Los ids se guardan en ingles. Solo la etiqueta que se muestra se traduce.
"""
import datetime
import json
import os
import re

# _sha2 es el sha256 propio de CPython (3.12+): se importa en 0,1 ms. hashlib carga OpenSSL y
# cuesta 16 ms, que SessionStart pagaria en cada sesion por una sola huella. Si no esta, el de
# hashlib da el mismo resultado.
try:
    from _sha2 import sha256 as _sha256
except ImportError:                      # pragma: no cover - otro interprete
    from hashlib import sha256 as _sha256

ARCHIVO = "harness.installation.json"
VERSION_SCHEMA = "harness-installation/1.1"
# El que escribio 0.21.0. Se lee, se migra y se escribe como 1.1 la proxima vez que se escribe.
VERSION_SCHEMA_1_0 = "harness-installation/1.0"

READY = "READY"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"

# Las integraciones que el harness implementa. OpenShift entra cuando exista su adaptador:
# listarlo antes sugeriria que hay algo que configurar.
INTEGRACIONES = (("jira", "Jira Cloud", "Jira"), ("gitlab", "GitLab", "GitLab"))

AVAILABLE = "AVAILABLE"
# Una integracion que ningun `setup` verifico. Es el UNRESOLVED del paquete del Bloque 1.
NUNCA_VERIFICADA = "UNRESOLVED"

CURRENT = "CURRENT"
RETIRED = "RETIRED"
# Los estados de fuente que dan BLOCKED. Todos los demas, salvo CURRENT y RETIRED, son PARTIAL:
# FRESHNESS_UNVERIFIED incluido, porque hoy las seis fuentes gestionadas estan ahi.
FUENTE_BLOQUEA = ("SOURCE_INTEGRITY_ALERT", "SOURCE_CHANGED_SAME_VERSION", "VERSION_REGRESSION")
# Del mas grave al menos grave, para el resumen de una linea. Un estado que no esta aca va
# despues de todos los pendientes conocidos y antes de CURRENT: nunca se resume como ACTUAL.
_GRAVEDAD = FUENTE_BLOQUEA + (
    "SOURCE_MISSING", "VERSION_UNRESOLVED", "KNOWLEDGE_PROMOTION_INCOMPLETE",
    "UPDATE_AVAILABLE", "NEW_SOURCE", "ACKNOWLEDGED_PENDING", "FRESHNESS_UNVERIFIED")
ILEGIBLE = "UNREADABLE"

ETIQUETAS = {
    READY: "LISTO",
    PARTIAL: "PARCIAL",
    BLOCKED: "BLOQUEADO",
    AVAILABLE: "DISPONIBLE",
    "NOT_CONFIGURED": "SIN CONFIGURAR",
    "AUTHENTICATION_FAILED": "FALLA DE AUTENTICACIÓN",
    "CONNECTION_FAILED": "SIN CONEXIÓN",
    "PERMISSION_DENIED": "SIN PERMISOS",
    NUNCA_VERIFICADA: "SIN VERIFICAR",
    CURRENT: "ACTUAL",
    "UPDATE_AVAILABLE": "ACTUALIZACIÓN DISPONIBLE",
    "ACKNOWLEDGED_PENDING": "PENDIENTE ACEPTADO",
    "SOURCE_INTEGRITY_ALERT": "ALERTA DE INTEGRIDAD",
    "FRESHNESS_UNVERIFIED": "VIGENCIA SIN VERIFICAR",
    ILEGIBLE: "ESTADO ILEGIBLE",
    "ACTIVE": "ACTIVO",
    "CONFIGURED": "CONFIGURADO",
    "INSTALLED": "INSTALADO",
    "INACTIVE": "INACTIVO",
    "RELOAD_REQUIRED": "REQUIERE REINICIO",
    "ERROR": "ERROR",
}


# -- los componentes de runtime ------------------------------------------------

ACTIVE = "ACTIVE"
CONFIGURED = "CONFIGURED"
INSTALLED = "INSTALLED"
NOT_CONFIGURED = "NOT_CONFIGURED"
RELOAD_REQUIRED = "RELOAD_REQUIRED"
ERROR = "ERROR"
UNRESOLVED = "UNRESOLVED"
ESTADOS_DE_COMPONENTE = (INSTALLED, CONFIGURED, ACTIVE, "INACTIVE", NOT_CONFIGURED,
                         RELOAD_REQUIRED, ERROR, UNRESOLVED)

# (clave, como se muestra, como se nombra en la linea, femenino)
COMPONENTES = (("block4Accounting", "Block 4 Accounting", "Block 4", False),
               ("contextBar", "Context Bar", "Context Bar", True),
               ("securityReporting", "Security Reporting", "Security Reporting", False))

_ETIQUETAS_DE_COMPONENTE = {
    ACTIVE: ("ACTIVO", "ACTIVA"),
    CONFIGURED: ("CONFIGURADO", "CONFIGURADA"),
    INSTALLED: ("INSTALADO", "INSTALADA"),
    "INACTIVE": ("INACTIVO", "INACTIVA"),
}

# Lo que se muestra con RELOAD_REQUIRED, tal cual lo pide la spec.
REINICIAR = "Context Bar configurada. Reiniciá la sesión de Claude Code para activarla."

RENDERER = "claude-code-statusline"
FUENTE_DE_LA_BARRA = "block4"

# ── El contrato de la senal de vida ────────────────────────────────────────────────────
#
# La Context Bar (bin/desarrollo/contabilidad/statusline.py) la escribe en cada dibujo, y este
# modulo la lee. Es lo UNICO que prueba que Claude Code cargo la barra en una sesion: que el
# archivo del renderizador exista, o que settings.json lo registre, no lo prueba.
#
#     <proyecto>/.claude/runtime/contextbar.json
#     {
#       "sessionId":                "<session_id que Claude Code le paso por stdin>",
#       "configurationFingerprint": "<la huella que el comando que corrio le paso como ultimo
#                                    argumento: huella_statusline() de su bloque> | null",
#       "integrationVersion":       "<INTEGRATION_VERSION del renderizador>",
#       "lastRenderedAt":           "<ahora(): YYYY-MM-DDTHH:MM:SS, hora local>",
#       "block4":                   "OK" | "SOURCE_UNAVAILABLE"
#     }
#
# 🔴 Esos cinco campos y ninguno mas: additionalProperties false. Un numero contable (tokens,
# costo, contexto) no entra aca, vive en el libro del Bloque 4. Una senal con otra forma no se
# toma por buena: la barra queda UNRESOLVED.
#
# La forma de escribirla sin equivocarse es `escribir_senal_de_vida`, con la huella que trajo el
# comando, y escribe con .tmp + os.replace. Quien la escribe a mano tiene que respetar el orden
# de `ahora()`: la senal se compara como texto contra `lastValidatedAt`, que tambien sale de
# `ahora()`, y tiene que ser ESTRICTAMENTE posterior. Una senal del mismo segundo que el
# registro no prueba nada: pudo dibujarla el comando viejo justo antes del cambio (E-41).
SENAL_DE_VIDA = (".claude", "runtime", "contextbar.json")
BLOCK4_OK = "OK"
BLOCK4_SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
CONTRATO_SENAL = {
    "type": "object",
    "required": ["sessionId", "configurationFingerprint", "integrationVersion",
                 "lastRenderedAt", "block4"],
    "additionalProperties": False,
    "properties": {
        "sessionId": {"type": "string", "pattern": "."},
        "configurationFingerprint": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
        "integrationVersion": {"type": "string"},
        "lastRenderedAt": {"type": "string",
                           "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"},
        "block4": {"type": "string", "enum": [BLOCK4_OK, BLOCK4_SOURCE_UNAVAILABLE]},
    },
}

# Lo que tiene que decir el comando del bloque statusLine para ser la barra del harness. Un
# statusLine de otra herramienta no es la Context Bar, y no se espera su senal de vida.
MARCA_DEL_COMANDO = "contabilidad/statusline.py"
# Como declara su version el renderizador. Se lee con esta expresion, sin importarlo.
_VERSION_DEL_RENDERIZADOR = re.compile(
    r"""^INTEGRATION_VERSION\s*=\s*["']([^"'\r\n]+)["']""", re.MULTILINE)

# Lo que tiene que estar en disco, relativo a bin/desarrollo/ o a schemas/.
_CONTABILIDAD = ("__init__.py", "libro.py", "barra.py")
_RENDERIZADOR = ("contabilidad", "statusline.py")
_ADAPTADOR = ("contabilidad", "adaptadores", "claude_code.py")
_REPORTE_SEGURIDAD = ("__init__.py", "libro.py", "resumen.py", "reporte.py")
SCHEMAS_DE_SEGURIDAD = ("security-ledger-event.schema.json", "security-summary.schema.json",
                        "security-report.schema.json")
_LIBROS = (".claude", "runtime", "accounting")
_LIBRO = "ledger.jsonl"

# Las condiciones de runtime van en "Acción requerida", no en "Estado general": son las que
# ya se ven, con su estado, en el bloque Observabilidad.
_PREFIJOS_DE_RUNTIME = ("CONTEXT_BAR_", "BLOCK4_", "SECURITY_REPORTING_")

_MARCA = {READY: "✓", PARTIAL: "◐", BLOCKED: "✕"}
_RAYA = "━" * 44
_CLI = "python .claude/harness/bin/desarrollo/dev-harness.py"
_COMANDOS = (("contexto", "Resolver contexto del proyecto"),
             ("plan", "Crear un plan de ejecución"),
             ("fuentes", "Revisar vigencia de fuentes"),
             ("harness", "Ver estado del Harness"))

# Las integraciones que se arreglan cargando otra vez la configuracion o el token. Las demas
# -sin conexion, sin verificar- se arreglan volviendo a mirar.
_SE_RECONFIGURA = ("NOT_CONFIGURED", "AUTHENTICATION_FAILED", "PERMISSION_DENIED")


def etiqueta(ident):
    """La etiqueta en castellano. Un id que la tabla no traduce sale tal cual, nunca como otro."""
    return ETIQUETAS.get(ident, str(ident))


def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


# -- lectura -------------------------------------------------------------------

def rutas(proyecto, ruta_codebase=None):
    claude = os.path.join(proyecto, ".claude")
    if not isinstance(ruta_codebase, str) or not ruta_codebase.strip():
        ruta_codebase = "docs/codebase"
    return {
        "lock": os.path.join(claude, "harness.lock.json"),
        "installation": os.path.join(claude, ARCHIVO),
        "capacidades": os.path.join(claude, "harness.capacidades.json"),
        "fuentes": os.path.join(claude, "harness.fuentes.json"),
        "contexto": os.path.join(proyecto, ruta_codebase, "project-context.json"),
    }


_FALTA = "missing"
_ROTO = "unreadable"


def _leer(ruta):
    """(dict, None) | (None, "missing") | (None, "unreadable"). Nunca levanta.

    Un JSON valido que no es un objeto es tan ilegible como uno roto: ningun dueno de estos
    archivos escribe otra cosa que un objeto.
    """
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            datos = json.load(f)
    except FileNotFoundError:
        return None, _FALTA
    except (OSError, ValueError):
        return None, _ROTO
    if not isinstance(datos, dict):
        return None, _ROTO
    return datos, None


def hay_harness(proyecto):
    """Si en este proyecto hay algo que decir. Sin lockfile y sin estado, el harness no esta
    instalado aca y la bienvenida calla."""
    r = rutas(proyecto)
    return os.path.isfile(r["lock"]) or os.path.isfile(r["installation"])


# -- la forma de cada archivo, la que escribe su dueno -------------------------
#
# 🔴 Un campo, en cualquier nivel, con un tipo distinto del que escribe su dueno es un archivo
# ilegible, lo use o no la bienvenida para decidir el estado. Mirar solo los campos que deciden
# deja pasar un archivo que nadie del harness escribio con el sello de READY puesto.
#
# Las formas se escriben en el mismo subconjunto de JSON Schema que interpreta contexto-armar.py.
# La de harness.fuentes.json NO se copia aca: se lee de source-state.schema.json, que es el
# contrato contra el que frescura valida antes de escribir. Asi hay una sola definicion.

_S, _SN, _B = {"type": "string"}, {"type": ["string", "null"]}, {"type": "boolean"}
_TEXTOS = {"type": "array", "items": _S}

# La que escribio 0.21.0, `harness-installation/1.0`. Solo se lee, para migrarla.
FORMA_INSTALACION_1_0 = {
    "type": "object",
    "required": ["schema_version", "installed", "harnessId", "installedAt", "bootstrap",
                 "welcome"],
    "properties": {
        "schema_version": {"type": "string", "enum": [VERSION_SCHEMA_1_0]},
        "installed": _B, "harnessId": _S, "installedVersion": _SN, "installedAt": _S,
        "project": {"type": "object", "properties": {"detected": _B, "name": _SN}},
        "bootstrap": {"type": "object",
                      "required": ["status", "blockingConditions", "pendingConditions"],
                      "properties": {"status": {"type": "string",
                                                "enum": [READY, PARTIAL, BLOCKED]},
                                     "blockingConditions": _TEXTOS,
                                     "pendingConditions": _TEXTOS}},
        "integrations": {"type": "array", "items": {
            "type": "object", "properties": {"id": _S, "status": _S, "verifiedAt": _SN}}},
        "knowledge": {"type": "object", "properties": {
            "applies": _B, "stateFile": _S, "verifiedAt": _SN, "summary": _SN,
            "sources": {"type": "array", "items": {"type": "object", "properties": {
                "id": _S, "state": _S, "blocking": {"type": ["boolean", "null"]}}}}}},
        "welcome": {"type": "object", "required": ["firstRunShown", "lastShownAt"],
                    "properties": {"firstRunShown": _B, "lastShownAt": _SN,
                                   "upgradeFrom": _S}},
    },
}

_FORMA_COMPONENTE = {
    "type": "object",
    "required": ["state", "installed", "configured"],
    "properties": {"state": {"type": "string", "enum": list(ESTADOS_DE_COMPONENTE)},
                   "installed": _B, "configured": _B, "version": _SN, "lastValidatedAt": _SN,
                   "errorCode": _SN},
}

# contextBar con las propiedades aplanadas en un solo objeto: el `allOf` del paquete no lo
# interpreta el validador de subconjunto. Es la divergencia declarada del schema 1.1.
_FORMA_BARRA = {
    "type": "object",
    "required": ["state", "installed", "configured", "reloadRequired", "activeInCurrentSession"],
    "properties": dict(_FORMA_COMPONENTE["properties"], **{
        "renderer": _SN, "source": {"enum": [FUENTE_DE_LA_BARRA, None]},
        "reloadRequired": _B, "activeInCurrentSession": _B,
        "configurationFingerprint": _SN, "integrationVersion": _SN,
        "commandTested": {"type": ["boolean", "null"]}, "lastSessionId": _SN,
        "fingerprints": {"type": ["object", "null"], "properties": {
            "statusLine": _SN, "renderer": _SN, "block4Adapter": _SN, "sessionStart": _SN}},
    }),
}

# La que escribe este mismo modulo (resolver / registrar_instalacion / marcar_mostrada).
FORMA_INSTALACION = {
    "type": "object",
    "required": FORMA_INSTALACION_1_0["required"] + ["runtimeComponents"],
    "properties": dict(FORMA_INSTALACION_1_0["properties"], **{
        "schema_version": {"type": "string", "enum": [VERSION_SCHEMA]},
        "updatedAt": _SN,
        "runtimeComponents": {
            "type": "object",
            "required": ["block4Accounting", "contextBar", "securityReporting"],
            "properties": {"block4Accounting": _FORMA_COMPONENTE, "contextBar": _FORMA_BARRA,
                           "securityReporting": _FORMA_COMPONENTE}},
    }),
}

# La que escribe RegistroCapacidades.como_documento (integraciones/registro.py), con cada
# integracion como la deja `anotar`.
FORMA_CAPACIDADES = {
    "type": "object",
    "required": ["schema_version", "integraciones", "capacidades"],
    "properties": {
        "schema_version": _S, "version_harness": _S,
        "integraciones": {"type": "object", "additionalProperties": {
            "type": "object", "required": ["estado", "motivo", "verificado_en", "capacidades"],
            "properties": {"estado": _S, "motivo": _S, "verificado_en": _S,
                           "capacidades": _TEXTOS}}},
        "capacidades": {"type": "object", "additionalProperties": _S},
    },
}

# Si source-state.schema.json no esta al lado -un arbol a medias-, lo minimo que se lee.
_FORMA_FUENTES_MINIMA = {
    "type": "object", "required": ["sources"],
    "properties": {"verified_at": _SN, "sources": {"type": "object", "additionalProperties": {
        "type": "object", "required": ["state"],
        "properties": {"state": _S, "blocking": _B}}}},
}

_TIPOS = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int,
          "number": (int, float), "null": type(None)}


def cumple(dato, forma, raiz=None):
    """Si `dato` tiene la forma. El subconjunto de contexto-armar.py: type, enum, pattern,
    required, properties, additionalProperties (false o una forma), items y $ref local."""
    raiz = raiz if raiz is not None else forma
    while "$ref" in forma:
        forma = raiz["$defs"][forma["$ref"][len("#/$defs/"):]]
    tipo = forma.get("type")
    if tipo:
        nombres = [tipo] if isinstance(tipo, str) else tipo
        # bool es subclase de int: un true no es un entero.
        if isinstance(dato, bool) and "boolean" not in nombres:
            return False
        if not any(isinstance(dato, _TIPOS[n]) for n in nombres):
            return False
    if "enum" in forma and dato not in forma["enum"]:
        return False
    if "pattern" in forma and isinstance(dato, str) and not re.search(forma["pattern"], dato):
        return False
    if isinstance(dato, dict):
        if any(r not in dato for r in forma.get("required") or ()):
            return False
        declaradas = forma.get("properties") or {}
        de_mas = forma.get("additionalProperties", True)
        for clave, valor in dato.items():
            if clave in declaradas:
                if not cumple(valor, declaradas[clave], raiz):
                    return False
            elif de_mas is False:
                return False
            elif isinstance(de_mas, dict) and not cumple(valor, de_mas, raiz):
                return False
    if isinstance(dato, list) and "items" in forma:
        return all(cumple(i, forma["items"], raiz) for i in dato)
    return True


def _forma_fuentes():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "schemas",
                        "source-state.schema.json")
    forma, _ = _leer(ruta)
    return forma or _FORMA_FUENTES_MINIMA


def _cumple_o_falso(dato, forma):
    """Una forma que no se puede interpretar no certifica nada."""
    try:
        return cumple(dato, forma)
    except (KeyError, TypeError, ValueError, re.error):
        return False


def _previo_valido(previo):
    """Si el estado anterior tiene, en todos sus campos, la forma que escribe este modulo: la
    de 1.1, o la de 1.0 que escribio 0.21.0. Cualquier otra version es ilegible."""
    version = previo.get("schema_version") if isinstance(previo, dict) else None
    if version == VERSION_SCHEMA_1_0:
        return _cumple_o_falso(previo, FORMA_INSTALACION_1_0)
    return _cumple_o_falso(previo, FORMA_INSTALACION)


def migrar(previo):
    """Un `harness-installation/1.0` como 1.1: todos sus campos, tal cual, con la version nueva.

    `runtimeComponents` no se inventa aca: lo resuelve `resolver` con lo que hay en disco, como
    en cualquier otra lectura. Un 1.1 vuelve igual. Un documento que no es ni un 1.0 ni un 1.1
    validos no se migra: None, y quien llama lo trata como ilegible.
    """
    if not isinstance(previo, dict) or not _previo_valido(previo):
        return None
    doc = json.loads(json.dumps(previo))
    if doc["schema_version"] == VERSION_SCHEMA_1_0:
        doc["schema_version"] = VERSION_SCHEMA
        doc.setdefault("updatedAt", None)
    return doc


def _leer_previo(ruta):
    """(documento 1.1 o None, problema). Un 1.0 sale migrado; uno que no se migra, ilegible."""
    previo, problema = _leer(ruta)
    if previo is not None:
        previo = migrar(previo)
        if previo is None:
            problema = _ROTO
    return previo, problema


def _integraciones(r, pendientes):
    capacidades, problema = _leer(r["capacidades"])
    registro = (capacidades or {}).get("integraciones")
    if problema == _ROTO or (capacidades is not None
                             and not _cumple_o_falso(capacidades, FORMA_CAPACIDADES)):
        pendientes.append("CAPABILITIES_STATE_UNREADABLE")
    if not isinstance(registro, dict):
        registro = {}
    salida = []
    for nombre, _, _ in INTEGRACIONES:
        datos = registro.get(nombre)
        estado = datos.get("estado") if isinstance(datos, dict) else None
        if not isinstance(estado, str) or not estado:
            estado = NUNCA_VERIFICADA
        verificado = datos.get("verificado_en") if isinstance(datos, dict) else None
        salida.append({"id": nombre, "status": estado,
                       "verifiedAt": verificado if isinstance(verificado, str) else None})
        if estado != AVAILABLE:
            pendientes.append("INTEGRATION_%s:%s" % (estado, nombre))
    return salida


# Los estados de fuente que ya empiezan con SOURCE_ y no se prefijan otra vez. Cualquier otro,
# conocido o no, lleva el prefijo: asi la inversa es exacta tambien para un estado nuevo.
_YA_PREFIJADOS = ("SOURCE_INTEGRITY_ALERT", "SOURCE_CHANGED_SAME_VERSION", "SOURCE_MISSING")


def _condicion_de_fuente(estado, sid):
    prefijo = estado if estado in _YA_PREFIJADOS else "SOURCE_" + estado
    return "%s:%s" % (prefijo, sid)


def _conocimiento(r, bloqueos, pendientes):
    doc, problema = _leer(r["fuentes"])
    fuentes = (doc or {}).get("sources")
    if problema == _FALTA:
        pendientes.append("SOURCES_STATE_MISSING")
        return {"applies": True, "stateFile": _FALTA, "verifiedAt": None, "summary": None,
                "sources": []}
    if problema == _ROTO or not isinstance(fuentes, dict):
        pendientes.append("SOURCES_STATE_UNREADABLE")
        return {"applies": True, "stateFile": _ROTO, "verifiedAt": None, "summary": None,
                "sources": []}
    # Lo que se puede leer se muestra igual; que el resto no tenga la forma de frescura queda
    # pendiente con su id.
    if not _cumple_o_falso(doc, _forma_fuentes()):
        pendientes.append("SOURCES_STATE_UNREADABLE")
    if not fuentes:
        # Con `desarrollo`, cero fuentes no es "todo al dia": es no saber nada.
        pendientes.append("SOURCES_STATE_EMPTY")

    lista = []
    for sid in sorted(fuentes):
        datos = fuentes[sid]
        estado = datos.get("state") if isinstance(datos, dict) else None
        if not isinstance(estado, str) or not estado:
            estado = ILEGIBLE
        bloquea = datos.get("blocking") if isinstance(datos, dict) else None
        lista.append({"id": str(sid), "state": estado,
                      "blocking": bloquea if isinstance(bloquea, bool) else None})
        if estado in (CURRENT, RETIRED):
            continue
        condicion = _condicion_de_fuente(estado, sid)
        (bloqueos if estado in FUENTE_BLOQUEA else pendientes).append(condicion)

    verificado = doc.get("verified_at")
    return {"applies": True, "stateFile": "present",
            "verifiedAt": verificado if isinstance(verificado, str) else None,
            "summary": resumen_de_fuentes(lista), "sources": lista}


def resumen_de_fuentes(lista):
    """El estado mas grave entre las fuentes que se siguen. None si no hay ninguna."""
    vigentes = [f["state"] for f in lista if f["state"] != RETIRED]
    if not vigentes:
        return None

    def rango(estado):
        if estado in _GRAVEDAD:
            return _GRAVEDAD.index(estado)
        return len(_GRAVEDAD) + (1 if estado == CURRENT else 0)
    return min(vigentes, key=rango)


def _proyecto(r):
    contexto, _ = _leer(r["contexto"])
    perfil = (contexto or {}).get("project_profile")
    nombre = perfil.get("project_name") if isinstance(perfil, dict) else None
    # Un nombre que no es una linea corta de texto no se muestra: no es un nombre.
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre) > 120 \
            or "\n" in nombre or "\r" in nombre:
        return {"detected": False, "name": None}
    return {"detected": True, "name": nombre.strip()}


# -- los componentes de runtime: donde estan -------------------------------------

def raiz_del_harness(proyecto):
    """El arbol del harness de ESTE proyecto: `.claude/harness` si esta instalado; si no, el
    arbol del que se cargo este modulo (el repositorio, cuando se corre desde la fabrica)."""
    instalado = os.path.join(proyecto, ".claude", "harness")
    if os.path.isdir(instalado):
        return instalado
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def _rutas_de_runtime(raiz):
    """bin/desarrollo instalado es harnesses/desarrollo/bin en el repositorio."""
    bin_desarrollo = os.path.join(raiz, "bin", "desarrollo")
    if not os.path.isdir(bin_desarrollo):
        bin_desarrollo = os.path.join(os.path.dirname(raiz), "harnesses", "desarrollo", "bin")
    return {
        "contabilidad": os.path.join(bin_desarrollo, "contabilidad"),
        "renderizador": os.path.join(bin_desarrollo, *_RENDERIZADOR),
        "adaptador": os.path.join(bin_desarrollo, *_ADAPTADOR),
        "reporte_seguridad": os.path.join(bin_desarrollo, "reporte_seguridad"),
        "schemas": os.path.join(raiz, "schemas"),
        "session_start": os.path.join(raiz, "hooks", "session-start.py"),
    }


def ruta_de_la_senal(proyecto):
    return os.path.join(proyecto, *SENAL_DE_VIDA)


# -- la Context Bar: huella, settings y senal de vida ----------------------------

# El ultimo argumento del comando registrado es la huella del propio bloque, entre comillas
# simples: la barra la recibe y la escribe tal cual en la senal de vida.
_ARGUMENTO_HUELLA = re.compile(r"\s+'[0-9a-f]{64}'\s*$")


def sin_argumento_de_huella(comando):
    """El comando sin su ultimo argumento, si ese argumento es una huella ('<64 hex>')."""
    return _ARGUMENTO_HUELLA.sub("", comando) if isinstance(comando, str) else comando


def huella_statusline(bloque):
    """El sha256 del bloque `statusLine` SIN el argumento de huella del comando, o None si no
    hay bloque.

    El comando registrado lleva como ultimo argumento su propia huella (E-41), y una huella no
    puede contenerse a si misma: se calcula sobre el bloque con `command` sin ese argumento
    (sin_argumento_de_huella). Todo lo demas del bloque -otros argumentos, padding, type- entra.

    JSON canonico: claves ordenadas, sin espacios, UTF-8 sin escapar. El instalador, la barra y
    este resolvedor la calculan con ESTA funcion; una segunda implementacion "igual" es como un
    dia un espacio de mas hace que la barra nunca quede activa.
    """
    if not isinstance(bloque, dict):
        return None
    bloque = dict(bloque)
    if "command" in bloque:
        bloque["command"] = sin_argumento_de_huella(bloque["command"])
    canonico = json.dumps(bloque, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _sha256(canonico.encode("utf-8")).hexdigest()


def leer_statusline(proyecto):
    """(bloque statusLine o None, problema). settings.json es de la persona y de Claude Code:
    de ahi se lee solo este bloque, y un statusLine que no es un objeto es como no tener uno."""
    settings, problema = _leer(os.path.join(proyecto, ".claude", "settings.json"))
    if problema:
        return None, problema
    bloque = settings.get("statusLine")
    return (bloque if isinstance(bloque, dict) else None), None


def es_la_barra_del_harness(bloque):
    comando = bloque.get("command") if isinstance(bloque, dict) else None
    return isinstance(comando, str) and MARCA_DEL_COMANDO in comando.replace("\\", "/")


def leer_senal_de_vida(proyecto):
    """(senal, problema). Una senal que no cumple CONTRATO_SENAL es ilegible."""
    senal, problema = _leer(ruta_de_la_senal(proyecto))
    if senal is not None and not _cumple_o_falso(senal, CONTRATO_SENAL):
        return None, _ROTO
    return senal, problema


_DE_SETTINGS = object()


def escribir_senal_de_vida(proyecto, session_id, block4, integration_version, momento=None,
                           huella=_DE_SETTINGS):
    """Lo que llama la barra despues de dibujar. `block4` es BLOCK4_OK o
    BLOCK4_SOURCE_UNAVAILABLE. Levanta ValueError con algo fuera del contrato, y OSError si no
    pudo escribir: la barra decide, y nunca por eso deja de dibujar.

    🔴 `huella` es la del comando que CORRIO, la que le paso su ultimo argumento, y se escribe
    tal cual (None si el comando no traia ninguna). Calcularla del settings.json de ahora
    haria que un comando viejo, todavia corriendo en una sesion sin reiniciar, probara la
    configuracion nueva (E-41). Sin el argumento se lee settings.json: es para quien escribe
    una senal sin ser un comando registrado, como la suite."""
    if huella is _DE_SETTINGS:
        bloque, _ = leer_statusline(proyecto)
        huella = huella_statusline(bloque)
    senal = {"sessionId": str(session_id or ""),
             "configurationFingerprint": huella,
             "integrationVersion": str(integration_version or ""),
             "lastRenderedAt": momento or ahora(),
             "block4": block4}
    if not _cumple_o_falso(senal, CONTRATO_SENAL):
        raise ValueError("la senal de vida no cumple el contrato de bienvenida.CONTRATO_SENAL")
    return escribir_estado(ruta_de_la_senal(proyecto), senal)


def _sha256_de(ruta):
    try:
        with open(ruta, "rb") as f:
            return _sha256(f.read()).hexdigest()
    except (OSError, ValueError):
        return None


def version_del_renderizador(ruta):
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            m = _VERSION_DEL_RENDERIZADOR.search(f.read())
    except (OSError, ValueError):
        return None
    return m.group(1) if m else None


def huellas_de_la_barra(proyecto, raiz=None):
    """Lo que la barra necesita para correr, como lo compara un -Update: el bloque statusLine,
    el renderizador, el adaptador claude_code y session-start.py. Lo calcula el registro de la
    instalacion, nunca la sesion."""
    rt = _rutas_de_runtime(raiz or raiz_del_harness(proyecto))
    bloque, _ = leer_statusline(proyecto)
    return {"statusLine": huella_statusline(bloque) if es_la_barra_del_harness(bloque) else None,
            "renderer": _sha256_de(rt["renderizador"]),
            "block4Adapter": _sha256_de(rt["adaptador"]),
            "sessionStart": _sha256_de(rt["session_start"])}


# -- los componentes de runtime: su estado ---------------------------------------

def _componente(estado, instalado, configurado, version, validado, codigo):
    return {"state": estado, "installed": instalado, "configured": configurado,
            "version": version, "lastValidatedAt": validado, "errorCode": codigo}


def _validado(previo_rc, clave, estado, codigo, momento):
    """La fecha de la ultima vez que el componente cambio de estado. Sin cambio, la de antes:
    resolver dos veces lo mismo no reescribe runtimeComponents."""
    antes = (previo_rc or {}).get(clave) or {}
    if antes.get("state") == estado and antes.get("errorCode") == codigo \
            and isinstance(antes.get("lastValidatedAt"), str):
        return antes["lastValidatedAt"]
    return momento


def libro_de_la_sesion(proyecto, session_id):
    """El libro que alimenta la barra: la sesion es la tarea mientras nadie declare una.

    Es la ruta de contabilidad.libro.carpeta_de(proyecto, session_id), escrita aca porque este
    modulo no importa nada de harnesses/. La barra ingiere ahi y este resolvedor mira ese.
    """
    return os.path.join(proyecto, *(_LIBROS + (str(session_id), _LIBRO)))


def _libro_legible(ruta):
    """False si el libro existe y no se abre. Solo se abre: un libro que se abre ya es uno que
    el Bloque 4 lee, y leerlo entero en cada sesion cuesta lo que pese."""
    if ruta is None or not os.path.lexists(ruta):
        return True
    try:
        with open(ruta, "rb"):
            pass
    except (OSError, ValueError):
        return False
    return True


def _se_puede_escribir(carpeta):
    """La carpeta, o la primera que existe hacia arriba, es un directorio escribible."""
    d = carpeta
    while not os.path.lexists(d):
        arriba = os.path.dirname(d)
        if arriba == d:
            return False
        d = arriba
    return os.path.isdir(d) and os.access(d, os.W_OK)


def _block4(proyecto, rt, version, previo_rc, momento, sesion_vista):
    """ERROR si el libro de la ultima sesion que vio la barra existe y no se abre. Mirar todos
    los libros costaria una apertura por sesion vieja -la carpeta crece una por sesion, y 300
    son 43 ms en SessionStart-, y el que la barra lee es ese."""
    clave = "block4Accounting"
    instalado = all(os.path.isfile(os.path.join(rt["contabilidad"], n)) for n in _CONTABILIDAD)
    carpeta = os.path.join(proyecto, *_LIBROS)
    if not instalado:
        estado, codigo = ERROR, "BLOCK4_NOT_INSTALLED"
    elif not _se_puede_escribir(carpeta):
        estado, codigo = ERROR, "BLOCK4_LEDGER_NOT_WRITABLE"
    elif not _libro_legible(libro_de_la_sesion(proyecto, sesion_vista) if sesion_vista
                            else None):
        estado, codigo = ERROR, "BLOCK4_LEDGER_UNREADABLE"
    else:
        estado, codigo = ACTIVE, None
    return _componente(estado, instalado, True, version,
                       _validado(previo_rc, clave, estado, codigo, momento), codigo)


def _seguridad(rt, version, previo_rc, momento):
    """ACTIVE es que el pipeline del reporte esta disponible. No dice nada de la aprobacion de
    seguridad del proyecto: ni la lee ni la toca."""
    clave = "securityReporting"
    instalado = all(os.path.isfile(os.path.join(rt["reporte_seguridad"], n))
                    for n in _REPORTE_SEGURIDAD)
    if not instalado:
        estado, codigo = ERROR, "SECURITY_REPORTING_NOT_INSTALLED"
    elif any(_leer(os.path.join(rt["schemas"], n))[0] is None for n in SCHEMAS_DE_SEGURIDAD):
        estado, codigo = ERROR, "SECURITY_REPORTING_SCHEMA_UNREADABLE"
    else:
        estado, codigo = ACTIVE, None
    return _componente(estado, instalado, True, version,
                       _validado(previo_rc, clave, estado, codigo, momento), codigo)


def _guardado_de_la_barra(previo):
    """Lo que dejo el ultimo registro de la instalacion: las huellas, la version del
    renderizador, si el comando corrio en los dos shells y si quedo un reinicio pendiente."""
    barra = ((previo or {}).get("runtimeComponents") or {}).get("contextBar") or {}
    return {"configurationFingerprint": barra.get("configurationFingerprint"),
            "integrationVersion": barra.get("integrationVersion"),
            "fingerprints": barra.get("fingerprints"),
            "commandTested": barra.get("commandTested"),
            "reloadRequired": bool(barra.get("reloadRequired", False)),
            "lastValidatedAt": barra.get("lastValidatedAt")}


def _barra(proyecto, rt, version, guardado, sesion, block4_activo, lectura):
    """El estado de la Context Bar. `sesion` es el session_id del SessionStart; None es la CLI,
    que no tiene sesion y mira la ultima vista.

    🔴 ACTIVE solo con una senal de vida de la sesion actual, con la huella del bloque que esta
    registrado y block4 OK. Nada de lo que hay en disco, solo, alcanza.
    """
    def salida(estado, codigo=None, instalado=True, configurado=True, recarga=False,
               activa=False, huella=None, sesion_vista=None):
        doc = _componente(estado, instalado, configurado, version,
                          guardado.get("lastValidatedAt"), codigo)
        doc.update({"renderer": RENDERER, "source": FUENTE_DE_LA_BARRA,
                    "reloadRequired": recarga, "activeInCurrentSession": activa,
                    "configurationFingerprint": huella,
                    "integrationVersion": guardado.get("integrationVersion"),
                    "fingerprints": guardado.get("fingerprints"),
                    "commandTested": guardado.get("commandTested"),
                    "lastSessionId": sesion_vista})
        return doc

    en_disco = os.path.isfile(rt["renderizador"])
    bloque, problema = leer_statusline(proyecto)
    if problema == _ROTO:
        return salida(UNRESOLVED, "CONTEXT_BAR_VALIDATION_UNRESOLVED", en_disco, False,
                      huella=guardado.get("configurationFingerprint"))
    if not es_la_barra_del_harness(bloque):
        if en_disco:
            return salida(INSTALLED, "CONTEXT_BAR_NOT_CONFIGURED", True, False)
        return salida(NOT_CONFIGURED, "CONTEXT_BAR_NOT_INSTALLED", False, False)
    huella = huella_statusline(bloque)
    if not en_disco:
        return salida(ERROR, "CONTEXT_BAR_NOT_INSTALLED", False, True, huella=huella)
    if guardado.get("commandTested") is False \
            and guardado.get("configurationFingerprint") == huella:
        return salida(NOT_CONFIGURED, "CONTEXT_BAR_CONFIGURATION_INVALID", True, False,
                      huella=huella)

    senal, problema = lectura
    if problema == _ROTO:
        return salida(UNRESOLVED, "CONTEXT_BAR_VALIDATION_UNRESOLVED",
                      huella=guardado.get("configurationFingerprint") or huella)
    vista = senal.get("sessionId") if senal else None

    # La senal prueba ESTA configuracion si trae la huella de ahora, la version que registro
    # el instalador, y se dibujo despues de ese registro.
    version_esperada = guardado.get("integrationVersion")
    desde = guardado.get("lastValidatedAt")
    prueba = bool(senal) and senal["configurationFingerprint"] == huella \
        and (version_esperada is None or senal["integrationVersion"] == version_esperada) \
        and (not isinstance(desde, str) or senal["lastRenderedAt"] > desde)
    cambio = guardado.get("reloadRequired") or guardado.get("configurationFingerprint") != huella
    if cambio and not prueba:
        return salida(RELOAD_REQUIRED, None, recarga=True,
                      huella=guardado.get("configurationFingerprint"), sesion_vista=vista)

    de_esta_sesion = bool(senal) and (sesion is None or senal["sessionId"] == sesion)
    if de_esta_sesion and prueba:
        if senal["block4"] != BLOCK4_OK or not block4_activo:
            return salida(ERROR, "CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE", huella=huella,
                          sesion_vista=vista)
        return salida(ACTIVE, None, activa=sesion is not None, huella=huella,
                      sesion_vista=vista)
    return salida(CONFIGURED, None, huella=huella, sesion_vista=vista)


def _sin_desarrollo(version):
    """Sin `desarrollo` no hay Bloque 4, ni barra, ni reporte de seguridad: NOT_CONFIGURED, sin
    condicion. Un proyecto de solo analisis no tiene nada que activar."""
    barra = _componente(NOT_CONFIGURED, False, False, version, None, None)
    barra.update({"renderer": None, "source": None, "reloadRequired": False,
                  "activeInCurrentSession": False, "configurationFingerprint": None,
                  "integrationVersion": None, "fingerprints": None, "commandTested": None,
                  "lastSessionId": None})
    return {"block4Accounting": _componente(NOT_CONFIGURED, False, False, version, None, None),
            "contextBar": barra,
            "securityReporting": _componente(NOT_CONFIGURED, False, False, version, None, None)}


def _runtime(proyecto, desarrollo, version, previo, guardado, sesion, momento):
    if not desarrollo:
        return _sin_desarrollo(version)
    rt = _rutas_de_runtime(raiz_del_harness(proyecto))
    previo_rc = (previo or {}).get("runtimeComponents")
    lectura = leer_senal_de_vida(proyecto)
    senal = lectura[0]
    block4 = _block4(proyecto, rt, version, previo_rc, momento,
                     senal.get("sessionId") if senal else None)
    return {"block4Accounting": block4,
            "contextBar": _barra(proyecto, rt, version, guardado, sesion,
                                 block4["state"] == ACTIVE, lectura),
            "securityReporting": _seguridad(rt, version, previo_rc, momento)}


def condicion_de_componente(clave, componente):
    """La condicion pendiente de un componente que no esta ACTIVE, o None.

    CONFIGURED no suma ninguna: la barra esta registrada, probada y sin cambio pendiente, y lo
    unico que falta es que se dibuje por primera vez en esta sesion. Si sumara, toda sesion
    nueva arrancaria en PARCIAL, y un aviso que sale siempre se deja de leer.
    """
    estado = componente.get("state")
    if estado in (ACTIVE, CONFIGURED) or (estado == NOT_CONFIGURED
                                          and not componente.get("errorCode")):
        return None
    if estado == RELOAD_REQUIRED:
        return "CONTEXT_BAR_RELOAD_REQUIRED"
    if componente.get("errorCode"):
        return componente["errorCode"]
    prefijo = {"block4Accounting": "BLOCK4", "contextBar": "CONTEXT_BAR",
               "securityReporting": "SECURITY_REPORTING"}[clave]
    return "%s_%s" % (prefijo, estado)


def resolver(proyecto, ruta_codebase=None, momento=None, sesion=None):
    """El estado de ahora, armado con los archivos locales. No escribe nada.

    Devuelve un documento `harness-installation/1.1` completo, que valida contra
    harness-installation-state.schema.json. La marca de la bienvenida (`welcome`) sale del
    archivo anterior si se pudo leer; si no, es una primera vez.

    `sesion` es el session_id del evento SessionStart. Sin sesion -la CLI- la sesion actual es
    la ultima vista, y la barra puede salir ACTIVE pero nunca `activeInCurrentSession`.
    """
    return _resolver(proyecto, ruta_codebase, momento, sesion, None)


def _resolver(proyecto, ruta_codebase, momento, sesion, guardado):
    momento = momento or ahora()
    r = rutas(proyecto, ruta_codebase)
    bloqueos, pendientes = [], []

    previo, problema_previo = _leer_previo(r["installation"])
    if problema_previo == _ROTO:
        pendientes.append("INSTALLATION_STATE_UNREADABLE")
    previo = previo or {}

    lock, problema_lock = _leer(r["lock"])
    ids = (lock or {}).get("harness")
    if problema_lock == _FALTA:
        bloqueos.append("LOCKFILE_MISSING")
    elif problema_lock == _ROTO or not isinstance(ids, list):
        bloqueos.append("LOCKFILE_UNREADABLE")
        lock = None
    ids = [str(i) for i in ids] if lock is not None else []

    instalado = previo.get("installed", True)
    if instalado is False:
        bloqueos.append("NOT_INSTALLED")

    version = (lock or {}).get("version")
    version = str(version) if version not in (None, "") else previo.get("installedVersion")

    instalado_en = previo.get("installedAt")
    if not instalado_en:
        sello = (lock or {}).get("instalado")
        instalado_en = sello if isinstance(sello, str) and sello else momento

    desarrollo = "desarrollo" in ids
    integraciones = _integraciones(r, pendientes) if desarrollo else []
    if desarrollo:
        conocimiento = _conocimiento(r, bloqueos, pendientes)
    else:
        conocimiento = {"applies": False}

    if guardado is None:
        guardado = _guardado_de_la_barra(previo)
    componentes = _runtime(proyecto, desarrollo, version, previo, guardado, sesion, momento)
    for clave, _, _, _ in COMPONENTES:
        condicion = condicion_de_componente(clave, componentes[clave])
        if condicion:
            pendientes.append(condicion)

    if bloqueos:
        estado = BLOCKED
    elif pendientes:
        estado = PARTIAL
    else:
        estado = READY

    bienvenida_previa = previo.get("welcome") or {}
    bienvenida = {"firstRunShown": bool(bienvenida_previa.get("firstRunShown", False)),
                  "lastShownAt": bienvenida_previa.get("lastShownAt")}
    if bienvenida_previa.get("upgradeFrom"):
        bienvenida["upgradeFrom"] = bienvenida_previa["upgradeFrom"]

    doc = {
        "schema_version": VERSION_SCHEMA,
        "installed": instalado,
        "harnessId": "+".join(i for i in ids if i != "comun") or "comun",
        "installedVersion": version,
        "installedAt": instalado_en,
        "updatedAt": momento,
        "project": _proyecto(r),
        "bootstrap": {"status": estado, "blockingConditions": bloqueos,
                      "pendingConditions": pendientes},
        "integrations": integraciones,
        "knowledge": conocimiento,
        "welcome": bienvenida,
        "runtimeComponents": componentes,
    }
    # Un campo del archivo anterior que este modulo no calcula se conserva: migrar de 1.0 a 1.1
    # no pierde ninguno, y un 1.1 tampoco los pierde en la escritura siguiente.
    for clave, valor in previo.items():
        if clave not in doc:
            doc[clave] = valor
    return doc


# -- escritura -----------------------------------------------------------------

def escribir_estado(ruta, doc):
    """Escribe el estado con .tmp y os.replace. Levanta OSError si no pudo: quien llama decide.

    El .tmp lleva el pid: dos sesiones que arrancan juntas no se pisan el temporal.
    """
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    tmp = "%s.%d.tmp" % (ruta, os.getpid())
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, ruta)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return ruta


def _guardado_al_registrar(proyecto, previo, momento, barra_probada):
    """Las huellas de ahora contra las del registro anterior. Si alguna cambio -el bloque
    statusLine, el renderizador, el adaptador claude_code o session-start.py-, reloadRequired
    queda en true hasta que llegue una senal de vida dibujada despues de este registro. Si
    ninguna cambio, lo guardado queda tal cual: un -Update igual no toca runtimeComponents."""
    guardado = _guardado_de_la_barra(previo)
    raiz = raiz_del_harness(proyecto)
    huellas = huellas_de_la_barra(proyecto, raiz)
    rt = _rutas_de_runtime(raiz)
    if huellas != guardado.get("fingerprints"):
        guardado.update({"fingerprints": huellas, "reloadRequired": True,
                         "lastValidatedAt": momento, "commandTested": None})
    if huellas["statusLine"] is not None:
        guardado["configurationFingerprint"] = huellas["statusLine"]
    guardado["integrationVersion"] = version_del_renderizador(rt["renderizador"])
    if barra_probada is not None:
        guardado["commandTested"] = bool(barra_probada)
    return guardado


def registrar_instalacion(proyecto, momento=None, barra_probada=None):
    """Lo que llama install.ps1 al terminar bien, despues de verificar los hooks.

    Sin archivo anterior es una instalacion nueva: firstRunShown false. Con archivo anterior
    es un -Update: se conserva firstRunShown y, si la version cambio, se anota upgradeFrom con
    la anterior. Un upgradeFrom que nadie vio todavia se conserva: la sesion siguiente dice
    desde donde se vino de verdad. Un -Update conserva tambien installedAt: lo que cambia es
    updatedAt.

    `barra_probada` es lo que probo el instalador con el comando de la Context Bar: True si
    corrio con `bash -c` y con `powershell.exe -NoProfile -Command`, False si no corrio en
    alguno de los dos (NOT_CONFIGURED con CONTEXT_BAR_CONFIGURATION_INVALID), None si no se
    probo. Las huellas no las pasa el instalador: las calcula `huellas_de_la_barra`, la misma
    funcion con la que se comparan.
    """
    momento = momento or ahora()
    r = rutas(proyecto)
    previo, _ = _leer_previo(r["installation"])
    version_previa = (previo or {}).get("installedVersion")

    lock, _ = _leer(r["lock"])
    ids = (lock or {}).get("harness")
    if isinstance(ids, list) and "desarrollo" in [str(i) for i in ids]:
        guardado = _guardado_al_registrar(proyecto, previo, momento, barra_probada)
    else:
        guardado = None
    doc = _resolver(proyecto, None, momento, None, guardado)
    doc["installed"] = True
    if previo is None:
        doc["installedAt"] = momento
    # Lo que este registro corrige no queda como condicion: la instalacion termino, y el
    # archivo roto es justo el que se esta reescribiendo.
    doc["bootstrap"]["blockingConditions"] = [
        c for c in doc["bootstrap"]["blockingConditions"] if c != "NOT_INSTALLED"]
    doc["bootstrap"]["pendingConditions"] = [
        c for c in doc["bootstrap"]["pendingConditions"] if c != "INSTALLATION_STATE_UNREADABLE"]
    _recalcular(doc)
    if previo is None:
        doc["welcome"] = {"firstRunShown": False, "lastShownAt": None}
    elif (version_previa and doc["installedVersion"]
          and version_previa != doc["installedVersion"]
          and not doc["welcome"].get("upgradeFrom")):
        doc["welcome"]["upgradeFrom"] = version_previa
    escribir_estado(r["installation"], doc)
    return doc


def reiniciar_bienvenida(proyecto):
    """`harness --reiniciar-bienvenida`: la sesion siguiente muestra la bienvenida completa."""
    r = rutas(proyecto)
    doc = resolver(proyecto)
    doc["welcome"] = {"firstRunShown": False, "lastShownAt": doc["welcome"].get("lastShownAt")}
    escribir_estado(r["installation"], doc)
    return doc


def _recalcular(doc):
    b = doc["bootstrap"]
    b["status"] = (BLOCKED if b["blockingConditions"]
                   else PARTIAL if b["pendingConditions"] else READY)


def marcar_mostrada(doc, momento=None):
    """La marca despues de mostrar: firstRunShown true, lastShownAt ahora, sin upgradeFrom."""
    doc["welcome"] = {"firstRunShown": True, "lastShownAt": momento or ahora()}
    return doc


# -- que decir -----------------------------------------------------------------

def que_mostrar(doc):
    """"completa", "actualizacion" o "linea", segun la marca de la bienvenida."""
    bienvenida = doc.get("welcome") or {}
    if not bienvenida.get("firstRunShown"):
        return "completa"
    if bienvenida.get("upgradeFrom"):
        return "actualizacion"
    return "linea"


def _nombre_de(integracion):
    for nombre, largo, corto in INTEGRACIONES:
        if nombre == integracion:
            return largo, corto
    return integracion, integracion


def describir(condicion):
    """Una condicion, en castellano y con lo que hay que hacer. Sin ids de estado en ingles."""
    base, _, sujeto = condicion.partition(":")
    if base == "LOCKFILE_MISSING":
        return "falta .claude/harness.lock.json: instalá de nuevo con install.ps1"
    if base == "LOCKFILE_UNREADABLE":
        return "no se puede leer .claude/harness.lock.json: instalá de nuevo con install.ps1"
    if base == "NOT_INSTALLED":
        return "la instalación no terminó: corré install.ps1 de nuevo"
    if base == "INSTALLATION_STATE_UNREADABLE":
        return "harness.installation.json estaba roto: se reescribe con el estado de ahora"
    if base == "CAPABILITIES_STATE_UNREADABLE":
        return "no se puede leer .claude/harness.capacidades.json: corré `dev-harness.py setup`"
    if base == "SOURCES_STATE_MISSING":
        return "no hay estado del conocimiento todavía: corré `dev-harness.py fuentes`"
    if base == "SOURCES_STATE_UNREADABLE":
        return "no se puede leer .claude/harness.fuentes.json: corré `dev-harness.py fuentes`"
    if base == "SOURCES_STATE_EMPTY":
        return ".claude/harness.fuentes.json no tiene ninguna fuente: corré `dev-harness.py fuentes`"
    if base.startswith("INTEGRATION_") and sujeto:
        estado = base[len("INTEGRATION_"):]
        largo, _ = _nombre_de(sujeto)
        if estado in _SE_RECONFIGURA:
            accion = "`dev-harness.py reconfigurar %s`" % sujeto
        else:
            accion = "`dev-harness.py setup`"
        return "%s %s: corré %s" % (largo, etiqueta(estado), accion)
    if base.startswith("SOURCE_") and sujeto:
        return "%s %s: revisalo con `dev-harness.py fuentes`" % (sujeto, etiqueta(_estado_de_condicion(base)))
    if base in _DESCRIPCIONES_DE_RUNTIME:
        return _DESCRIPCIONES_DE_RUNTIME[base]
    return condicion


_UPDATE = "corré install.ps1 -Update"
_DESCRIPCIONES_DE_RUNTIME = {
    "CONTEXT_BAR_RELOAD_REQUIRED": REINICIAR,
    "CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE":
        "la Context Bar no puede leer el Bloque 4: revisá .claude/runtime/accounting/ con "
        "`dev-harness.py harness --verbose`",
    "CONTEXT_BAR_NOT_CONFIGURED":
        "la Context Bar está en disco y no está registrada en .claude/settings.json: " + _UPDATE,
    "CONTEXT_BAR_NOT_INSTALLED": "falta el renderizador de la Context Bar: " + _UPDATE,
    "CONTEXT_BAR_CONFIGURATION_INVALID":
        "el comando de la Context Bar no corre en Git Bash y en PowerShell: " + _UPDATE,
    "CONTEXT_BAR_VALIDATION_UNRESOLVED":
        "no se puede leer .claude/settings.json o .claude/runtime/contextbar.json: revisá "
        "settings.json, o borrá contextbar.json y la barra lo vuelve a escribir",
    "BLOCK4_NOT_INSTALLED": "falta el paquete contabilidad/ del Bloque 4: " + _UPDATE,
    "BLOCK4_LEDGER_NOT_WRITABLE":
        "no se puede escribir en .claude/runtime/accounting/: revisá los permisos de la carpeta",
    "BLOCK4_LEDGER_UNREADABLE":
        "hay un libro del Bloque 4 en .claude/runtime/accounting/ que no se puede abrir: "
        "revisá sus permisos",
    "SECURITY_REPORTING_NOT_INSTALLED": "falta el paquete reporte_seguridad/: " + _UPDATE,
    "SECURITY_REPORTING_SCHEMA_UNREADABLE":
        "falta o no se puede leer un schema del reporte de seguridad: " + _UPDATE,
}


def es_de_runtime(condicion):
    return str(condicion).startswith(_PREFIJOS_DE_RUNTIME)


def etiqueta_de_componente(clave, componente):
    """ACTIVA la barra, ACTIVO los otros dos. Los estados sin genero salen de ETIQUETAS."""
    estado = componente.get("state")
    femenino = any(c == clave and f for c, _, _, f in COMPONENTES)
    if estado in _ETIQUETAS_DE_COMPONENTE:
        return _ETIQUETAS_DE_COMPONENTE[estado][1 if femenino else 0]
    return etiqueta(estado)


def _ultima_sesion(componente):
    """ACTIVE en la CLI es de la ultima sesion vista, y se dice cual."""
    vista = componente.get("lastSessionId")
    if componente.get("state") == ACTIVE and not componente.get("activeInCurrentSession") \
            and isinstance(vista, str) and vista:
        return " (última sesión: %s)" % vista[:8]
    return ""


def _con_desarrollo(doc):
    return bool((doc.get("knowledge") or {}).get("applies"))


def _estado_de_condicion(base):
    """SOURCE_INTEGRITY_ALERT -> SOURCE_INTEGRITY_ALERT; SOURCE_FRESHNESS_UNVERIFIED ->
    FRESHNESS_UNVERIFIED. La inversa de `_condicion_de_fuente`."""
    if base in _YA_PREFIJADOS:
        return base
    return base[len("SOURCE_"):] or base


def _fuentes_por_estado(conocimiento):
    grupos = {}
    orden = []
    for f in conocimiento.get("sources") or []:
        if f["state"] == RETIRED:
            continue
        if f["state"] not in grupos:
            grupos[f["state"]] = []
            orden.append(f["state"])
        grupos[f["state"]].append(f["id"])
    return [(e, grupos[e]) for e in sorted(orden, key=lambda e: _rango_de(e))]


def _rango_de(estado):
    if estado in _GRAVEDAD:
        return _GRAVEDAD.index(estado)
    return len(_GRAVEDAD) + (1 if estado == CURRENT else 0)


def _con_marca(estado_id):
    """La tilde va solo delante de lo que esta disponible."""
    texto = etiqueta(estado_id)
    return ("✓ " + texto) if estado_id in (AVAILABLE, CURRENT) else texto


def _pendientes_agrupados(pendientes):
    """Las fuentes pendientes del mismo estado van en una linea: seis fuentes sin verificar son
    una sola cosa que hacer, no seis."""
    salida, por_estado, orden = [], {}, []
    for c in pendientes:
        base, _, sujeto = c.partition(":")
        if es_de_runtime(c):
            continue
        if base.startswith("SOURCE_") and sujeto:
            estado = _estado_de_condicion(base)
            if estado not in por_estado:
                por_estado[estado] = []
                orden.append(estado)
            por_estado[estado].append(sujeto)
        else:
            salida.append(describir(c))
    for estado in orden:
        salida.append("%s en %s: revisalo con `dev-harness.py fuentes`"
                      % (etiqueta(estado), ", ".join(por_estado[estado])))
    return salida


def renderizar_bienvenida(doc):
    """La bienvenida completa, en el formato del paquete del Bloque 1."""
    b = doc["bootstrap"]
    estado = b["status"]
    lineas = [_RAYA, " GCBA Development Harness", _RAYA, ""]

    rota = any(c in ("LOCKFILE_MISSING", "LOCKFILE_UNREADABLE", "NOT_INSTALLED")
               for c in b["blockingConditions"])
    version = doc.get("installedVersion")
    if rota:
        lineas.append("✕ La instalación del Harness no está completa")
    else:
        lineas.append("✓ Harness instalado correctamente" + (" (v%s)" % version if version else ""))
    proyecto = doc.get("project") or {}
    if proyecto.get("detected") and proyecto.get("name"):
        lineas.append("✓ Proyecto detectado: %s" % proyecto["name"])
    else:
        # Sin nombrar al agente ni al archivo: eso ya lo dice, una sola vez, el aviso del
        # recorrido del codigo en el bloque de siempre.
        lineas.append("· Proyecto no detectado: todavía no hay un contexto del proyecto")

    lineas += ["", "Estado general", "  " + etiqueta(estado)]
    for c in b["blockingConditions"]:
        lineas.append("  Lo bloquea: " + describir(c))
    for texto in _pendientes_agrupados(b.get("pendingConditions") or []):
        lineas.append("  Pendiente: " + texto)

    integraciones = doc.get("integrations") or []
    if integraciones:
        ancho = max(len(largo) for _, largo, _ in INTEGRACIONES) + 3
        lineas += ["", "Integraciones"]
        for i in integraciones:
            largo, _ = _nombre_de(i["id"])
            lineas.append("  %s%s" % (largo.ljust(ancho), _con_marca(i["status"])))

    conocimiento = doc.get("knowledge") or {}
    if conocimiento.get("applies"):
        lineas += ["", "Conocimiento"]
        archivo = conocimiento.get("stateFile")
        if archivo == _FALTA:
            lineas.append("  Normativa    sin estado: todavía no corrió `dev-harness.py fuentes`")
        elif archivo == _ROTO:
            lineas.append("  Normativa    sin estado: no se puede leer harness.fuentes.json")
        elif conocimiento.get("summary") is None:
            lineas.append("  Normativa    sin fuentes gestionadas")
        else:
            lineas.append("  Normativa    " + _con_marca(conocimiento["summary"]))
            grupos = _fuentes_por_estado(conocimiento)
            for n, (e, ids) in enumerate(grupos):
                lineas.append("  %s%s: %s" % ("Fuentes      " if n == 0 else " " * 13,
                                               _con_marca(e), ", ".join(ids)))

        lineas += _observabilidad(doc)
        lineas += ["", "Comandos iniciales   (%s <comando>)" % _CLI]
        for nombre, que in _COMANDOS:
            lineas.append("  %s%s" % (nombre.ljust(13), que))

    if estado == READY:
        lineas += ["", "El Harness está listo para trabajar."]
    lineas.append(_RAYA)
    return "\n".join(lineas)


def _observabilidad(doc):
    """El bloque Observabilidad, y abajo lo que hay que hacer. Solo con `desarrollo`.

    La ✓ va solo con ACTIVE: REQUIERE REINICIO, CONFIGURADA o ERROR no la llevan.
    """
    rc = doc.get("runtimeComponents") or {}
    if not _con_desarrollo(doc) or not rc:
        return []
    ancho = max(len(nombre) for _, nombre, _, _ in COMPONENTES) + 3
    lineas, acciones = ["", "Observabilidad"], []
    for clave, nombre, _, _ in COMPONENTES:
        comp = rc.get(clave) or {}
        texto = etiqueta_de_componente(clave, comp) + _ultima_sesion(comp)
        marca = "✓ " if comp.get("state") == ACTIVE else ""
        lineas.append("  %s%s%s" % (nombre.ljust(ancho), marca, texto))
        condicion = condicion_de_componente(clave, comp)
        if condicion:
            acciones.append("  " + describir(condicion))
    if acciones:
        lineas += ["", "Acción requerida"] + acciones
    return lineas


def _segmentos_de_runtime(doc, con_barra=True):
    """En la linea: el estado de la Context Bar y ningun numero de la barra, que la barra ya
    los muestra siempre. Block 4 y Security Reporting solo se nombran si no estan ACTIVE."""
    rc = doc.get("runtimeComponents") or {}
    if not _con_desarrollo(doc) or not rc:
        return []
    partes = []
    for clave, _, corto, _ in COMPONENTES:
        comp = rc.get(clave) or {}
        if clave == "contextBar":
            if con_barra:
                partes.append("%s %s%s" % (corto, etiqueta_de_componente(clave, comp),
                                           _ultima_sesion(comp)))
        elif comp.get("state") != ACTIVE:
            partes.append("%s %s" % (corto, etiqueta_de_componente(clave, comp)))
    return partes


def renderizar_linea(doc, con_barra=True):
    """Una sola linea: el estado, lo que lo bloquea y lo que queda pendiente."""
    b = doc["bootstrap"]
    estado = b["status"]
    partes = ["Harness GCBA %s %s" % (_MARCA[estado], etiqueta(estado))]

    for c in b["blockingConditions"]:
        base, _, sujeto = c.partition(":")
        if base.startswith("SOURCE_") and sujeto:
            partes.append("%s %s" % (sujeto, etiqueta(_estado_de_condicion(base))))
        elif base == "LOCKFILE_MISSING":
            partes.append("falta harness.lock.json")
        elif base == "LOCKFILE_UNREADABLE":
            partes.append("harness.lock.json ilegible")
        elif base == "NOT_INSTALLED":
            partes.append("instalación incompleta")
        else:
            partes.append(describir(c))

    conocimiento = doc.get("knowledge") or {}
    if conocimiento.get("applies"):
        archivo = conocimiento.get("stateFile")
        if archivo == _FALTA:
            partes.append("Conocimiento SIN ESTADO")
        elif archivo == _ROTO:
            partes.append("Conocimiento ILEGIBLE")
        else:
            # 🔴 ACTUAL solo si TODAS las que se siguen estan en CURRENT. Si no, se nombra lo que
            # no esta al dia, sin repetir lo que ya salio como bloqueo: "ES0902 ALERTA DE
            # INTEGRIDAD · Conocimiento ACTUAL" diria dos cosas que no pueden ser ciertas juntas.
            estados = [e for e, _ in _fuentes_por_estado(conocimiento)]
            if not estados:
                partes.append("Conocimiento SIN FUENTES")
            elif estados == [CURRENT]:
                partes.append("Conocimiento " + etiqueta(CURRENT))
            else:
                pendientes = [e for e in estados if e != CURRENT and e not in FUENTE_BLOQUEA]
                if pendientes:
                    partes.append("Conocimiento " + ", ".join(etiqueta(e) for e in pendientes))

    for i in doc.get("integrations") or []:
        _, corto = _nombre_de(i["id"])
        partes.append("%s %s" % (corto, etiqueta(i["status"])))

    partes += _segmentos_de_runtime(doc, con_barra)

    if (conocimiento.get("stateFile") == "present"
            and "SOURCES_STATE_UNREADABLE" in (b.get("pendingConditions") or [])):
        partes.append("harness.fuentes.json ilegible")
    if "CAPABILITIES_STATE_UNREADABLE" in (b.get("pendingConditions") or []):
        partes.append("harness.capacidades.json ilegible")
    if "INSTALLATION_STATE_UNREADABLE" in (b.get("pendingConditions") or []):
        partes.append("harness.installation.json se reescribió")
    return " · ".join(partes)


def linea_de_la_barra_actualizada(doc):
    """La segunda linea del aviso de actualizacion, o None sin `desarrollo`."""
    barra = (doc.get("runtimeComponents") or {}).get("contextBar") or {}
    if not _con_desarrollo(doc) or not barra:
        return None
    estado = barra.get("state")
    if estado == RELOAD_REQUIRED:
        return "Context Bar actualizada · reinicio de Claude Code requerido."
    if estado == ACTIVE:
        return "Context Bar activa."
    return "Context Bar %s." % etiqueta_de_componente("contextBar", barra)


def renderizar_actualizacion(doc):
    """El aviso de una actualizacion, una vez: la version, la Context Bar, y la linea compacta,
    que entonces no repite la barra."""
    vieja = (doc.get("welcome") or {}).get("upgradeFrom") or "?"
    nueva = doc.get("installedVersion") or "?"
    lineas = ["Harness GCBA actualizado: %s → %s ✓" % (vieja, nueva)]
    barra = linea_de_la_barra_actualizada(doc)
    if barra:
        lineas.append(barra)
    lineas.append(renderizar_linea(doc, con_barra=barra is None))
    return "\n".join(lineas)


def renderizar(doc):
    """Lo que corresponde mostrar en esta sesion, segun la marca."""
    que = que_mostrar(doc)
    if que == "completa":
        return renderizar_bienvenida(doc)
    if que == "actualizacion":
        return renderizar_actualizacion(doc)
    return renderizar_linea(doc)


# El instalador es PowerShell: llama a este archivo por ruta, sin paquete ni sys.path.
#     python .claude/harness/hooks/lib/bienvenida.py registrar <proyecto> [--barra-probada|--barra-invalida]
#     python .claude/harness/hooks/lib/bienvenida.py huella <proyecto>
_BARRA_PROBADA = {"--barra-probada": True, "--barra-invalida": False}

if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    if len(argv) in (2, 3) and argv[0] == "registrar" \
            and (len(argv) == 2 or argv[2] in _BARRA_PROBADA):
        doc = registrar_instalacion(os.path.abspath(argv[1]),
                                    barra_probada=_BARRA_PROBADA.get(argv[2]) if len(argv) == 3
                                    else None)
        sys.stdout.write(doc["bootstrap"]["status"] + "\n")
        sys.exit(0)
    if len(argv) == 2 and argv[0] == "huella":
        bloque, _ = leer_statusline(os.path.abspath(argv[1]))
        sys.stdout.write((huella_statusline(bloque) or "") + "\n")
        sys.exit(0)
    sys.stderr.write("uso: bienvenida.py registrar <proyecto> [--barra-probada|--barra-invalida]\n"
                     "     bienvenida.py huella <proyecto>\n")
    sys.exit(2)
