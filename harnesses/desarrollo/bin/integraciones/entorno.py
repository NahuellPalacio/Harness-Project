"""El resolvedor de la configuracion de las integraciones: del `.env` a lo que recibe el adapter.

    cargar_contrato() -> resolver(contrato, ruta_env, ruta_proyeccion) -> Resolucion
    Resolucion.de(nombre)        la configuracion publica de una integracion, como ConfigIntegraciones
    Resolucion.proyeccion()      el documento sanitizado de .claude/harness.integraciones.json
    escribir_proyeccion(ruta, doc)

Codigo determinista del Bloque 1, no un agente ni una skill. La persona completa UN archivo, el
`.env` local, y de ahi sale todo:

    PROCESS_ENV > DOTENV > LEGACY > SAFE_DEFAULT > NOT_CONFIGURED

`LEGACY` es el `harness.integraciones.json` que la persona completaba antes de esta version. Se
lee solo para no dejar sin integraciones a un proyecto que todavia no migro: nunca le gana al
entorno ni al `.env`, solo aporta claves publicas del contrato, y cada entrada se consume cuando
el `.env` trae su variable. Una proyeccion que ya genero el harness no es fuente de nada.

🔴 Un SECRET no entra a ninguna estructura de este modulo. Se sabe si esta y de que capa viene;
el valor lo pide el adapter a `AlmacenSecretos.get`, que es el unico camino. Lo que se compara
en memoria -una variable repetida, un valor publico igual a un token- se compara y se tira.

🔴 Ningun mensaje lleva un valor del `.env`, tampoco uno publico: los mensajes terminan en la
consola, en la transcripcion de la sesion y en el contexto del modelo, y el `.env` entero esta
detras de permissions.deny.
"""
import io
import json
import os
import re

from . import almacen as _almacen
from .config import ConfigIntegraciones, es_clave_de_secreto

MODO = "ENVIRONMENT_FIRST"
VERSION_CONTRATO = "integration-environment-contract/1.0"
VERSION_PROYECCION = "integration-projection/1.0"
ARCHIVO_CONTRATO = "integration-environment-contract.json"

PUBLIC_CONFIG = "PUBLIC_CONFIG"
SECRET = "SECRET"

PROCESS_ENV = "PROCESS_ENV"
DOTENV = "DOTENV"
LEGACY = "LEGACY"
SAFE_DEFAULT = "SAFE_DEFAULT"
NOT_CONFIGURED = "NOT_CONFIGURED"

ENV_FILE_UNREADABLE = "ENV_FILE_UNREADABLE"
ENV_VALUE_INVALID = "ENV_VALUE_INVALID"
ENV_ENABLED_FLAG_INVALID = "ENV_ENABLED_FLAG_INVALID"
ENV_REQUIRED_VARIABLE_MISSING = "ENV_REQUIRED_VARIABLE_MISSING"
ENV_PUBLIC_PROJECTION_REJECTED_SECRET = "ENV_PUBLIC_PROJECTION_REJECTED_SECRET"
ENV_CONFIGURATION_CONFLICT = "ENV_CONFIGURATION_CONFLICT"
ENV_PROJECTION_WRITE_FAILED = "ENV_PROJECTION_WRITE_FAILED"
ENV_CONTRACT_INVALID = "ENV_CONTRACT_INVALID"

# Si una integracion junta mas de un problema, se dice el que hay que arreglar primero.
_PRIORIDAD = (ENV_ENABLED_FLAG_INVALID, ENV_CONFIGURATION_CONFLICT,
              ENV_PUBLIC_PROJECTION_REJECTED_SECRET, ENV_VALUE_INVALID,
              ENV_REQUIRED_VARIABLE_MISSING)

_VERDADEROS = ("true", "1", "yes", "on")
_FALSOS = ("false", "0", "no", "off")

_NOMBRE_DE_VARIABLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_URL = re.compile(r"^https?://([^/\s?#]+)(?:[/?#]\S*)?$", re.IGNORECASE)

QUE_HACER = "Completá las variables faltantes en el .env local."

_GENERADO = [
    "Proyeccion sanitizada que genera el harness desde el .env local. No se edita a mano:",
    "se vuelve a escribir en cada setup, estado o reconfigurar. No lleva ningun secreto.",
    "La configuracion se completa en el .env (ver .env.example).",
]


class ErrorDeEntorno(Exception):
    """Un problema que para a la CLI. Lleva su codigo; nunca un valor del `.env`."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


def booleano(texto):
    """True, False, o None si no es una de las formas aceptadas. Sin distinguir mayusculas."""
    limpio = str(texto).strip().lower()
    if limpio in _VERDADEROS:
        return True
    if limpio in _FALSOS:
        return False
    return None


# -- el contrato -----------------------------------------------------------------

def ruta_del_contrato(desde=__file__):
    """Donde esta el contrato, en el repositorio y en un proyecto instalado. None si no esta."""
    from orquestacion import roster
    return roster.ruta_de_regla(ARCHIVO_CONTRATO, desde)


def _es_texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def validar_contrato(doc, adaptadores=None):
    """La lista de problemas del contrato. Vacia es que se puede usar.

    `adaptadores` es {id: clase}: el contrato y el codigo tienen que nombrar las mismas
    integraciones, y cada campo que el adapter lee tiene que estar declarado.
    """
    if not isinstance(doc, dict):
        return ["el contrato no es un objeto JSON"]
    errores = []
    if doc.get("schema_version") != VERSION_CONTRATO:
        errores.append("schema_version tiene que ser %s" % VERSION_CONTRATO)
    integraciones = doc.get("integrations")
    if not isinstance(integraciones, list) or not integraciones:
        return errores + ["falta la lista integrations"]
    ids, variables = [], []
    for n, integ in enumerate(integraciones):
        donde = "integrations[%d]" % n
        if not isinstance(integ, dict):
            errores.append("%s no es un objeto" % donde)
            continue
        ident = integ.get("id")
        if not _es_texto(ident):
            errores.append("%s no tiene id" % donde)
            continue
        donde = "la integracion %s" % ident
        ids.append(ident)
        bandera = integ.get("enabled")
        if not isinstance(bandera, dict) or not _es_texto(bandera.get("env")) \
                or not isinstance(bandera.get("default"), bool):
            errores.append("%s no declara enabled.env y enabled.default" % donde)
        else:
            variables.append(bandera["env"])
        campos = integ.get("fields")
        if not isinstance(campos, list) or not campos:
            errores.append("%s no tiene fields" % donde)
            continue
        nombres = []
        for campo in campos:
            if not isinstance(campo, dict) or not _es_texto(campo.get("name")) \
                    or not _es_texto(campo.get("env")):
                errores.append("%s tiene un campo sin name o sin env" % donde)
                continue
            nombres.append(campo["name"])
            variables.append(campo["env"])
            if campo.get("classification") not in (PUBLIC_CONFIG, SECRET):
                errores.append("%s: %s no esta clasificado PUBLIC_CONFIG ni SECRET"
                               % (donde, campo["env"]))
            if not isinstance(campo.get("requiredWhenEnabled"), bool):
                errores.append("%s: %s no dice si es requiredWhenEnabled" % (donde, campo["env"]))
            legado = campo.get("legacyConfigKey")
            if legado is not None and not _es_texto(legado):
                errores.append("%s: %s tiene un legacyConfigKey invalido" % (donde, campo["env"]))
            if legado is not None and campo.get("classification") == SECRET:
                errores.append("%s: %s es SECRET y no puede venir del JSON viejo"
                               % (donde, campo["env"]))
            if campo.get("format") not in (None, "url", "text"):
                errores.append("%s: %s tiene un format desconocido" % (donde, campo["env"]))
            if campo["name"] == "enabled":
                errores.append("%s: 'enabled' es un nombre reservado" % donde)
        if len(set(nombres)) != len(nombres):
            errores.append("%s repite un campo" % donde)
        if adaptadores and ident in adaptadores:
            clase = adaptadores[ident]
            declarados = dict((c.get("name"), c) for c in campos if isinstance(c, dict))
            for leido in clase.campos:
                if leido not in declarados:
                    errores.append("%s no declara %s, que el adapter lee" % (donde, leido))
            secretos = [c.get("env") for c in declarados.values()
                        if c.get("classification") == SECRET]
            if clase.clave_token not in secretos:
                errores.append("%s no declara %s como SECRET" % (donde, clase.clave_token))
    for v in variables:
        if isinstance(v, str) and not _NOMBRE_DE_VARIABLE.match(v):
            errores.append("%s no es un nombre de variable" % v)
    repetidas = sorted(set(v for v in variables if variables.count(v) > 1))
    if repetidas:
        errores.append("variables repetidas: %s" % ", ".join(repetidas))
    if len(set(ids)) != len(ids):
        errores.append("integraciones repetidas")
    if adaptadores is not None:
        sin_adapter = sorted(set(ids) - set(adaptadores))
        sin_contrato = sorted(set(adaptadores) - set(ids))
        if sin_adapter:
            errores.append("integraciones sin adapter: %s" % ", ".join(sin_adapter))
        if sin_contrato:
            errores.append("adapters sin contrato: %s" % ", ".join(sin_contrato))
    return errores


def cargar_contrato(ruta=None, adaptadores=None):
    """El contrato validado. Levanta ErrorDeEntorno(ENV_CONTRACT_INVALID) si no sirve."""
    ruta = ruta or ruta_del_contrato()
    if not ruta or not os.path.isfile(ruta):
        raise ErrorDeEntorno(ENV_CONTRACT_INVALID,
                             "no se encontro %s. Instalá de nuevo con install.ps1." % ARCHIVO_CONTRATO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        raise ErrorDeEntorno(ENV_CONTRACT_INVALID,
                             "%s no es un JSON legible. Instalá de nuevo con install.ps1." % ruta)
    errores = validar_contrato(doc, adaptadores)
    if errores:
        raise ErrorDeEntorno(ENV_CONTRACT_INVALID, "%s: %s." % (ruta, "; ".join(errores[:4])))
    return doc


def variables_del_contrato(contrato):
    """Todos los nombres de variable, banderas incluidas, ordenados."""
    salida = []
    for integ in contrato["integrations"]:
        salida.append(integ["enabled"]["env"])
        salida.extend(c["env"] for c in integ["fields"])
    return sorted(salida)


# -- la proyeccion ---------------------------------------------------------------

def leer_proyeccion(ruta):
    """(documento, generada). Un archivo que no existe es ({}, False).

    `generada` es que lleva la marca de la proyeccion: lo escribio el harness. Sin la marca es
    el archivo que completaba la persona antes de esta version. Un JSON roto levanta
    ConfigIlegible, como siempre: puede ser el archivo viejo con valores que alguien cargo.
    """
    doc = ConfigIntegraciones(ruta).leer()
    return doc, doc.get("schema_version") == VERSION_PROYECCION


def _legado(doc, generada, contrato):
    """Las claves publicas del JSON viejo que todavia sirven, por integracion y por campo."""
    fuente = doc.get("legado") if generada else doc
    if not isinstance(fuente, dict):
        return {}
    salida = {}
    for integ in contrato["integrations"]:
        bloque = fuente.get(integ["id"])
        if not isinstance(bloque, dict):
            continue
        propio = {}
        if isinstance(bloque.get("enabled"), bool):
            propio["enabled"] = bloque["enabled"]
        for campo in integ["fields"]:
            clave = campo.get("legacyConfigKey")
            if campo["classification"] != PUBLIC_CONFIG or not clave:
                continue
            # La proyeccion guarda por nombre de campo; el archivo viejo, por su clave.
            leida = campo["name"] if generada else clave
            if es_clave_de_secreto(leida) or es_clave_de_secreto(campo["name"]):
                continue
            valor = bloque.get(leida)
            if isinstance(valor, str) and valor.strip():
                propio[campo["name"]] = valor.strip()
        if propio:
            salida[integ["id"]] = propio
    return salida


def texto_de(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def escribir_proyeccion(ruta, doc):
    """Escribe la proyeccion si cambio. Devuelve si escribio.

    Un archivo temporal y `os.replace`: abrir el destino con "w" lo trunca antes de que la
    escritura pueda fallar, y lo que quedaria es un JSON vacio que la proxima corrida lee roto.
    """
    for nombre, bloque in doc.items():
        if nombre == "legado" or not isinstance(bloque, dict):
            continue
        for clave in bloque:
            if es_clave_de_secreto(clave):
                raise ErrorDeEntorno(ENV_PUBLIC_PROJECTION_REJECTED_SECRET,
                                     "'%s' tiene forma de secreto y no se proyecta." % clave)
    texto = texto_de(doc)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            if f.read() == texto:
                return False
    except (OSError, ValueError):
        pass
    temporal = ruta + ".tmp"
    try:
        carpeta = os.path.dirname(os.path.abspath(ruta))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with io.open(temporal, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        os.replace(temporal, ruta)
    except OSError as e:
        try:
            os.remove(temporal)
        except OSError:
            pass
        raise ErrorDeEntorno(ENV_PROJECTION_WRITE_FAILED,
                             "no se pudo escribir %s (%s)." % (ruta, e.strerror))
    return True


# -- la resolucion ---------------------------------------------------------------

class Variable(object):
    """Una variable del contrato, sin su valor: si esta, de que capa, y si sirvio."""

    def __init__(self, nombre, campo, clasificacion, requerida, presente, fuente, valida=True):
        self.nombre = nombre
        self.campo = campo
        self.clasificacion = clasificacion
        self.requerida = requerida
        self.presente = presente
        self.fuente = fuente
        self.valida = valida

    def como_dict(self):
        return {"variable": self.nombre, "campo": self.campo,
                "clasificacion": self.clasificacion, "requerida": self.requerida,
                "presente": self.presente, "fuente": self.fuente, "valida": self.valida}

    def __repr__(self):
        return "Variable(%s, %s)" % (self.nombre, self.fuente)


class IntegracionResuelta(object):
    def __init__(self, ident, bandera):
        self.id = ident
        self.bandera = bandera
        self.habilitada = False
        self.fuente_habilitada = SAFE_DEFAULT
        self.variables = []
        self.publico = {}
        self.faltan = []
        self._codigos = []
        self._detalles = {}

    def anotar(self, codigo, variable):
        if codigo not in self._codigos:
            self._codigos.append(codigo)
        self._detalles.setdefault(codigo, [])
        if variable not in self._detalles[codigo]:
            self._detalles[codigo].append(variable)

    @property
    def codigo(self):
        for codigo in _PRIORIDAD:
            if codigo in self._codigos:
                return codigo
        return ""

    def motivo(self, etiqueta):
        """Por que no se valida, en una linea, con nombres de variable y nunca con valores."""
        codigo = self.codigo
        nombres = ", ".join(self._detalles.get(codigo, []))
        if codigo == ENV_ENABLED_FLAG_INVALID:
            return ("%s: %s no es un booleano reconocido (true/false, 1/0, yes/no, on/off). "
                    "Corregilo en el .env local." % (codigo, nombres))
        if codigo == ENV_CONFIGURATION_CONFLICT:
            return ("%s: %s esta definida mas de una vez en el .env con valores distintos. "
                    "Dejá una sola." % (codigo, nombres))
        if codigo == ENV_PUBLIC_PROJECTION_REJECTED_SECRET:
            return ("%s: %s tiene forma de secreto y no se proyecta. Revisá que no hayas "
                    "pegado un token en una variable publica." % (codigo, nombres))
        if codigo == ENV_VALUE_INVALID:
            return ("%s: %s no tiene un valor valido (una URL http o https, sin espacios ni "
                    "caracteres de control)." % (codigo, nombres))
        if codigo == ENV_REQUIRED_VARIABLE_MISSING:
            return "Falta configurar %s: %s. %s" % (etiqueta, nombres, QUE_HACER)
        return ""

    def configuracion(self):
        """Lo que recibe el adapter: `enabled` y los campos publicos. Ningun secreto."""
        datos = dict(self.publico)
        datos["enabled"] = self.habilitada
        return datos

    def variables_de_campo(self):
        return dict((v.campo, v.nombre) for v in self.variables if v.campo)

    def de_legado(self):
        return [v.nombre for v in self.variables if v.fuente == LEGACY]

    def __repr__(self):
        return "IntegracionResuelta(%s, habilitada=%s, faltan=%s)" % (
            self.id, self.habilitada, self.faltan)


class Resolucion(object):
    def __init__(self, contrato, ruta_env, env_presente, integraciones, legado, previas):
        self.contrato = contrato
        self.ruta_env = ruta_env
        self.env_presente = env_presente
        self.integraciones = integraciones
        self.legado = legado
        self._previas = previas

    # La misma interfaz que ConfigIntegraciones: quien armaba un adapter con `config.de`
    # sigue armandolo igual.
    def de(self, nombre):
        integ = self.integraciones.get(nombre)
        return integ.configuracion() if integ else {}

    def integracion(self, nombre):
        return self.integraciones.get(nombre)

    def variables_de(self, nombre):
        integ = self.integraciones.get(nombre)
        return integ.variables_de_campo() if integ else {}

    def variables_nuevas(self):
        """Las del contrato que la proyeccion anterior no conocia. [] si no habia proyeccion."""
        if self._previas is None:
            return []
        return sorted(set(variables_del_contrato(self.contrato)) - set(self._previas))

    def proyeccion(self):
        doc = {
            "schema_version": VERSION_PROYECCION,
            "_generado": list(_GENERADO),
            "configurationMode": MODO,
            "contrato": self.contrato["schema_version"],
            "variables": variables_del_contrato(self.contrato),
        }
        for ident, integ in self.integraciones.items():
            doc[ident] = integ.configuracion()
        if self.legado:
            doc["legado"] = self.legado
        return doc

    def __repr__(self):
        return "Resolucion(%s)" % ", ".join(repr(i) for i in self.integraciones.values())


def _catalogo():
    try:
        from contexto import limpieza
        return limpieza, limpieza.cargar_catalogo()
    except Exception:                     # noqa: BLE001 - sin catalogo queda la heuristica
        return None, None


def _tiene_forma_de_secreto(valor, limpieza, catalogo):
    if limpieza is None or catalogo is None:
        return False
    try:
        return bool(limpieza.redactar(valor, catalogo, "entorno")[1])
    except Exception:                     # noqa: BLE001
        return False


def resolver(contrato, ruta_env, ruta_proyeccion, entorno=None, etiquetas=None):
    """La configuracion de cada integracion del contrato, con la fuente de cada variable.

    Levanta ErrorDeEntorno(ENV_FILE_UNREADABLE) si el `.env` existe y no se puede leer, y
    ConfigIlegible si la proyeccion esta rota. Los problemas de una integracion no levantan:
    quedan en su codigo, y la otra se resuelve igual.
    """
    entorno = os.environ if entorno is None else entorno
    try:
        asignaciones = _almacen.asignaciones(_almacen.leer_lineas(ruta_env))
    except _almacen.ErrorDeAlmacen as e:
        raise ErrorDeEntorno(ENV_FILE_UNREADABLE, "%s. Revisá el archivo a mano." % e)

    del_archivo, repetidas = {}, set()
    for nombre, valor in asignaciones:
        if nombre in del_archivo:
            if del_archivo[nombre] != valor:
                repetidas.add(nombre)
            continue
        del_archivo[nombre] = valor
    del asignaciones

    previa, generada = leer_proyeccion(ruta_proyeccion)
    legado = _legado(previa, generada, contrato)
    previas = previa.get("variables") if generada else None
    previas = [v for v in previas if isinstance(v, str)] if isinstance(previas, list) else None
    limpieza, catalogo = _catalogo()

    def capa(nombre):
        del_proceso = entorno.get(nombre)
        if not _almacen.es_valor_vacio(del_proceso):
            return del_proceso.strip(), PROCESS_ENV
        del_env = del_archivo.get(nombre)
        if not _almacen.es_valor_vacio(del_env):
            return del_env.strip(), DOTENV
        return None, None

    integraciones = {}
    legado_nuevo = {}
    for integ in contrato["integrations"]:
        ident = integ["id"]
        propio = dict(legado.get(ident) or {})
        r = IntegracionResuelta(ident, integ["enabled"]["env"])

        bandera = integ["enabled"]["env"]
        texto, fuente = capa(bandera)
        if bandera in repetidas:
            r.anotar(ENV_CONFIGURATION_CONFLICT, bandera)
        if texto is not None:
            leido = booleano(texto)
            if leido is None:
                r.anotar(ENV_ENABLED_FLAG_INVALID, bandera)
                r.habilitada = False
            else:
                r.habilitada = leido
                if fuente == DOTENV:
                    propio.pop("enabled", None)
            r.fuente_habilitada = fuente
        elif "enabled" in propio:
            r.habilitada, r.fuente_habilitada = propio["enabled"], LEGACY
        else:
            r.habilitada, r.fuente_habilitada = integ["enabled"]["default"], SAFE_DEFAULT
        del texto
        r.variables.append(Variable(bandera, None, PUBLIC_CONFIG, True,
                                    r.fuente_habilitada in (PROCESS_ENV, DOTENV, LEGACY),
                                    r.fuente_habilitada,
                                    ENV_ENABLED_FLAG_INVALID not in r._codigos))

        secretos = [c["env"] for c in integ["fields"] if c["classification"] == SECRET]
        for campo in integ["fields"]:
            nombre = campo["env"]
            if nombre in repetidas:
                r.anotar(ENV_CONFIGURATION_CONFLICT, nombre)
            valor, fuente = capa(nombre)
            if campo["classification"] == SECRET:
                presente = valor is not None
                del valor
                r.variables.append(Variable(nombre, campo["name"], SECRET,
                                            campo["requiredWhenEnabled"], presente,
                                            fuente or NOT_CONFIGURED))
                if r.habilitada and campo["requiredWhenEnabled"] and not presente:
                    r.faltan.append(nombre)
                    r.anotar(ENV_REQUIRED_VARIABLE_MISSING, nombre)
                continue

            if valor is None and campo["name"] in propio:
                valor, fuente = propio[campo["name"]], LEGACY
            elif valor is not None and fuente == DOTENV:
                propio.pop(campo["name"], None)

            problema = None
            if valor is not None:
                problema = _problema_de(campo, valor, secretos, capa, limpieza, catalogo)
            if valor is not None and problema is None:
                r.publico[campo["name"]] = valor
            elif problema and r.habilitada:
                r.anotar(problema, nombre)
            presente = valor is not None
            del valor
            r.variables.append(Variable(nombre, campo["name"], PUBLIC_CONFIG,
                                        campo["requiredWhenEnabled"], presente,
                                        fuente or NOT_CONFIGURED, problema is None))
            if r.habilitada and campo["requiredWhenEnabled"] and not presente:
                r.faltan.append(nombre)
                r.anotar(ENV_REQUIRED_VARIABLE_MISSING, nombre)

        integraciones[ident] = r
        if propio:
            legado_nuevo[ident] = propio

    return Resolucion(contrato, ruta_env, os.path.isfile(ruta_env), integraciones,
                      legado_nuevo, previas)


def _problema_de(campo, valor, secretos, capa, limpieza, catalogo):
    """El codigo del problema de un valor publico, o None. Nunca devuelve el valor."""
    if es_clave_de_secreto(campo["name"]) or es_clave_de_secreto(campo["env"]):
        return ENV_PUBLIC_PROJECTION_REJECTED_SECRET
    if _CONTROL.search(valor):
        return ENV_VALUE_INVALID
    if campo.get("format") == "url":
        m = _URL.match(valor)
        if m and "@" in m.group(1):
            # https://usuario:clave@host es una credencial adentro de una URL.
            return ENV_PUBLIC_PROJECTION_REJECTED_SECRET
        if not m:
            return ENV_VALUE_INVALID
    for nombre in secretos:
        secreto, _ = capa(nombre)
        igual = secreto is not None and secreto == valor
        del secreto
        if igual:
            return ENV_PUBLIC_PROJECTION_REJECTED_SECRET
    if _tiene_forma_de_secreto(valor, limpieza, catalogo):
        return ENV_PUBLIC_PROJECTION_REJECTED_SECRET
    return None
