"""La bienvenida del harness y el estado general de una instalacion: READY, PARTIAL o BLOCKED.

Es el resolvedor UNICO. Lo usan session-start.py, `dev-harness.py harness` y `dev-harness.py
setup`, y el instalador escribe con el el archivo de estado. Vive en la lib de los hooks porque
el hook tiene que poder leerlo sin importar `harnesses/`, y un proyecto de solo `analisis`
tambien tiene hooks.

Lee cuatro archivos locales y nada mas:

    .claude/harness.lock.json           la version y los harness instalados (install.ps1)
    .claude/harness.installation.json   el estado de la instalacion y la marca de la bienvenida
    .claude/harness.capacidades.json    el `estado` por integracion que dejo el ultimo `setup`
    .claude/harness.fuentes.json        el `state` por fuente que dejo el ultimo `fuentes`

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

ARCHIVO = "harness.installation.json"
VERSION_SCHEMA = "harness-installation/1.0"

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
}

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

# La que escribe este mismo modulo (resolver / registrar_instalacion / marcar_mostrada).
FORMA_INSTALACION = {
    "type": "object",
    "required": ["schema_version", "installed", "harnessId", "installedAt", "bootstrap",
                 "welcome"],
    "properties": {
        "schema_version": {"type": "string", "enum": [VERSION_SCHEMA]},
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
    """Si el estado anterior tiene, en todos sus campos, la forma que escribe este modulo."""
    return _cumple_o_falso(previo, FORMA_INSTALACION)


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


def resolver(proyecto, ruta_codebase=None, momento=None):
    """El estado de ahora, armado con los cuatro archivos. No escribe nada.

    Devuelve un documento `harness-installation/1.0` completo, que valida contra
    harness-installation-state.schema.json. La marca de la bienvenida (`welcome`) sale del
    archivo anterior si se pudo leer; si no, es una primera vez.
    """
    momento = momento or ahora()
    r = rutas(proyecto, ruta_codebase)
    bloqueos, pendientes = [], []

    previo, problema_previo = _leer(r["installation"])
    if previo is not None and not _previo_valido(previo):
        previo, problema_previo = None, _ROTO
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

    return {
        "schema_version": VERSION_SCHEMA,
        "installed": instalado,
        "harnessId": "+".join(i for i in ids if i != "comun") or "comun",
        "installedVersion": version,
        "installedAt": instalado_en,
        "project": _proyecto(r),
        "bootstrap": {"status": estado, "blockingConditions": bloqueos,
                      "pendingConditions": pendientes},
        "integrations": integraciones,
        "knowledge": conocimiento,
        "welcome": bienvenida,
    }


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


def registrar_instalacion(proyecto, momento=None):
    """Lo que llama install.ps1 al terminar bien, despues de verificar los hooks.

    Sin archivo anterior es una instalacion nueva: firstRunShown false. Con archivo anterior
    es un -Update: se conserva firstRunShown y, si la version cambio, se anota upgradeFrom con
    la anterior. Un upgradeFrom que nadie vio todavia se conserva: la sesion siguiente dice
    desde donde se vino de verdad.
    """
    momento = momento or ahora()
    r = rutas(proyecto)
    previo, _ = _leer(r["installation"])
    if previo is not None and not _previo_valido(previo):
        previo = None
    version_previa = (previo or {}).get("installedVersion")

    doc = resolver(proyecto, momento=momento)
    doc["installed"] = True
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
    return condicion


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

        lineas += ["", "Comandos iniciales   (%s <comando>)" % _CLI]
        for nombre, que in _COMANDOS:
            lineas.append("  %s%s" % (nombre.ljust(13), que))

    if estado == READY:
        lineas += ["", "El Harness está listo para trabajar."]
    lineas.append(_RAYA)
    return "\n".join(lineas)


def renderizar_linea(doc):
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

    if (conocimiento.get("stateFile") == "present"
            and "SOURCES_STATE_UNREADABLE" in (b.get("pendingConditions") or [])):
        partes.append("harness.fuentes.json ilegible")
    if "CAPABILITIES_STATE_UNREADABLE" in (b.get("pendingConditions") or []):
        partes.append("harness.capacidades.json ilegible")
    if "INSTALLATION_STATE_UNREADABLE" in (b.get("pendingConditions") or []):
        partes.append("harness.installation.json se reescribió")
    return " · ".join(partes)


def renderizar_actualizacion(doc):
    """El aviso de una actualizacion, una vez, y la linea compacta."""
    vieja = (doc.get("welcome") or {}).get("upgradeFrom") or "?"
    nueva = doc.get("installedVersion") or "?"
    return "Harness GCBA actualizado: %s → %s ✓\n%s" % (vieja, nueva, renderizar_linea(doc))


def renderizar(doc):
    """Lo que corresponde mostrar en esta sesion, segun la marca."""
    que = que_mostrar(doc)
    if que == "completa":
        return renderizar_bienvenida(doc)
    if que == "actualizacion":
        return renderizar_actualizacion(doc)
    return renderizar_linea(doc)


# El instalador es PowerShell: llama a este archivo por ruta, sin paquete ni sys.path.
#     python .claude/harness/hooks/lib/bienvenida.py registrar <proyecto>
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "registrar":
        doc = registrar_instalacion(os.path.abspath(sys.argv[2]))
        sys.stdout.write(doc["bootstrap"]["status"] + "\n")
        sys.exit(0)
    sys.stderr.write("uso: bienvenida.py registrar <proyecto>\n")
    sys.exit(2)
