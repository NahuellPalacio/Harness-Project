"""El contrato de una integracion, y los cinco estados.

    nombre / esta_configurada() / validar_conexion() / descubrir_capacidades() / estado()

El nucleo del harness depende de esta clase y no de la API de Jira ni de la de GitLab.
Agregar SonarQube, Confluence o una API interna del GCBA es escribir una subclase con
su auth, su llamada de validacion y su sondeo de capacidades: el bootstrap no cambia.

🔴 Cinco estados, nunca un booleano. "No anda" contesta a cuatro preguntas distintas
que se arreglan de cuatro formas distintas: completar la configuracion, generar un
token nuevo, revisar la red o la VPN, o pedir permisos.

🔴 El motivo sale de un diccionario fijo de este modulo, jamas del cuerpo de la
respuesta. Un servidor puede devolver la credencial que recibio adentro de un mensaje
de error, y ese texto terminaria en la consola, en el registro y en el contexto del
modelo. Se pierde detalle de diagnostico; se gana que no haya ruta de fuga.

La unica excepcion es un 400, que es cuando el cuerpo ES la explicacion: Jira Cloud rechaza
ahi una JQL ilimitada, y sin su `errorMessages` el diagnostico no dice nada. Se leen solo esos
strings, hasta tres, y cada uno pasa por `mensajes_de_rechazo`: se reemplazan el token exacto,
la credencial y el usuario configurados, despues el catalogo de secretos del Bloque 2, y se
recorta a 200 caracteres. Ver docs/cambios/sonda-de-jira-acotada/spec.md.
"""
import datetime
import re

from . import http

NOT_CONFIGURED = "NOT_CONFIGURED"
AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
CONNECTION_FAILED = "CONNECTION_FAILED"
PERMISSION_DENIED = "PERMISSION_DENIED"
AVAILABLE = "AVAILABLE"

ESTADOS = (NOT_CONFIGURED, AUTHENTICATION_FAILED, CONNECTION_FAILED, PERMISSION_DENIED, AVAILABLE)

_MOTIVOS_DE_RED = {
    http.ERROR_TIMEOUT: "no respondio a tiempo. Revisa la red, la VPN o subi timeoutIntegraciones",
    http.ERROR_DNS: "no se pudo resolver el nombre del servidor. Revisa la baseUrl",
    http.ERROR_TLS: "fallo la conexion segura (TLS). Revisa el certificado del servidor",
    http.ERROR_RED: "no se pudo conectar. Revisa la red o la VPN",
}


def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


TOPE_DE_MENSAJE = 200
MENSAJES_COMO_MAXIMO = 3
REDACTADO = "[redactado]"


def mensajes_de_rechazo(respuesta, secretos=()):
    """Los `errorMessages` de un 400, sin nada de lo que el harness mando. Lista, quiza vacia.

    🔴 Primero lo que se sabe exacto -el token, la credencial, el usuario- y despues el
    catalogo, que reconoce formas y no valores. Al reves, un token que el catalogo no reconoce
    pasaria entero.
    """
    if getattr(respuesta, "codigo", None) != 400:
        return []
    datos = respuesta.datos()
    crudos = datos.get("errorMessages") if isinstance(datos, dict) else None
    if not isinstance(crudos, list):
        return []
    exactos = sorted((s for s in secretos if isinstance(s, str) and len(s) >= 4),
                     key=len, reverse=True)
    catalogo = None
    try:
        from contexto import limpieza
        catalogo = limpieza.cargar_catalogo()
    except Exception:                     # noqa: BLE001 - sin catalogo, sin mensaje
        return []
    if catalogo is None:
        return []
    salida = []
    for texto in [m for m in crudos if isinstance(m, str)][:MENSAJES_COMO_MAXIMO]:
        for secreto in exactos:
            texto = texto.replace(secreto, REDACTADO)
        texto = limpieza.redactar_arbol(texto, catalogo, "$")[0]
        texto = re.sub(r"\s+", " ", texto).strip()[:TOPE_DE_MENSAJE]
        if texto:
            salida.append(texto)
    return salida


def diagnostico_de(capacidad, que, respuesta, etiqueta, secretos=()):
    """Por que una capacidad no quedo habilitada, en una linea. El texto es fijo salvo el 400."""
    if respuesta.error:
        return "%s: %s %s." % (capacidad, que, _MOTIVOS_DE_RED.get(
            respuesta.error, "no se pudo hacer (%s)" % respuesta.error))
    if respuesta.codigo == 400:
        linea = "%s: %s rechazo %s (400)" % (capacidad, etiqueta, que)
        mensajes = mensajes_de_rechazo(respuesta, secretos)
        return linea + (": " + " | ".join(mensajes) if mensajes else ".")
    if respuesta.codigo in (401, 403):
        return ("%s: %s contesto %d a %s: el token no tiene permiso para esto."
                % (capacidad, etiqueta, respuesta.codigo, que))
    if respuesta.codigo in (404, 410):
        return ("%s: %s contesto %d a %s: el endpoint no existe en esta instancia."
                % (capacidad, etiqueta, respuesta.codigo, que))
    return "%s: %s contesto %d a %s." % (capacidad, etiqueta, respuesta.codigo, que)


class Resultado(object):
    def __init__(self, estado, motivo=""):
        self.estado = estado
        self.motivo = motivo

    def __repr__(self):
        return "Resultado(%s)" % self.estado


def estado_de_respuesta(respuesta, etiqueta):
    """El mapeo, unico para todas las integraciones."""
    if respuesta.error:
        return Resultado(CONNECTION_FAILED, "%s %s." % (etiqueta, _MOTIVOS_DE_RED.get(
            respuesta.error, "no se pudo conectar")))
    if respuesta.ok:
        return Resultado(AVAILABLE, "")
    if respuesta.codigo == 401:
        return Resultado(AUTHENTICATION_FAILED,
                         "El token de %s no fue aceptado (401). Puede estar vencido o mal copiado: "
                         "genera uno nuevo y volve a configurarlo." % etiqueta)
    if respuesta.codigo == 403:
        return Resultado(PERMISSION_DENIED,
                         "El token de %s es valido pero no tiene permisos para esta operacion (403). "
                         "Pedi los permisos de lectura que falten." % etiqueta)
    if 300 <= respuesta.codigo < 400:
        return Resultado(CONNECTION_FAILED,
                         "La baseUrl de %s redirige a otro lado (%d). El harness no sigue "
                         "redirecciones a proposito: corregi la URL." % (etiqueta, respuesta.codigo))
    return Resultado(CONNECTION_FAILED,
                     "%s contesto %d, que no es una respuesta esperada. Revisa la baseUrl."
                     % (etiqueta, respuesta.codigo))


class Integracion(object):
    """La clase base. Una subclase declara su nombre, su etiqueta y sus capacidades."""

    nombre = ""
    etiqueta = ""
    clave_token = ""
    campos = ()
    CAPACIDADES = ()

    def __init__(self, configuracion, almacen, timeout=http.TIMEOUT_POR_DEFECTO,
                 transporte=None, transporte_bytes=None):
        self.configuracion = dict(configuracion or {})
        self.almacen = almacen
        self.timeout = timeout
        self.transporte = transporte
        # El de texto y el de bytes se inyectan por separado: una descarga de un PDF y
        # una llamada a la API no son la misma operacion, y un solo transporte falso
        # para las dos obliga a que el test adivine cual esta simulando.
        self.transporte_bytes = transporte_bytes

    # -- configuracion ---------------------------------------------------------

    @property
    def decidida(self):
        """Alguien dijo que si o que no. `null` -o ausente- es que todavia nadie miro."""
        return self.configuracion.get("enabled") is not None

    @property
    def habilitada(self):
        return bool(self.configuracion.get("enabled", False))

    def campos_faltantes(self):
        faltan = [c for c in self.campos if not str(self.configuracion.get(c, "") or "").strip()]
        if not self.token():
            faltan.append(self.clave_token)
        return faltan

    def token(self):
        return self.almacen.get(self.clave_token)

    def secretos(self):
        """Lo que el harness manda y no puede volver en un diagnostico."""
        return [s for s in (self.token(),) if s]

    def esta_configurada(self):
        return self.habilitada and not self.campos_faltantes()

    def base_url(self):
        return str(self.configuracion.get("baseUrl", "") or "").rstrip("/")

    # -- red -------------------------------------------------------------------

    def cabeceras(self):
        raise NotImplementedError

    def pedir(self, camino):
        return http.pedir(http.unir(self.base_url(), camino), self.cabeceras(),
                          self.timeout, self.transporte)

    def validar_conexion(self):
        """El estado de la integracion. No sale a la red si no esta configurada."""
        if not self.decidida:
            return Resultado(NOT_CONFIGURED,
                             "%s todavia no se configuro. Corre el setup del harness."
                             % self.etiqueta)
        if not self.habilitada:
            return Resultado(NOT_CONFIGURED,
                             "%s esta deshabilitada en la configuracion." % self.etiqueta)
        faltan = self.campos_faltantes()
        if faltan:
            return Resultado(NOT_CONFIGURED,
                             "Falta configurar %s: %s. Corre el setup del harness."
                             % (self.etiqueta, ", ".join(faltan)))
        return estado_de_respuesta(self.pedir(self.camino_de_validacion), self.etiqueta)

    camino_de_validacion = "/"

    def descubrir_capacidades(self):
        raise NotImplementedError

    # -- resultado -------------------------------------------------------------

    def estado(self):
        """Valida y, solo si esta disponible, descubre. Devuelve un dict serializable."""
        resultado = self.validar_conexion()
        capacidades = []
        self.diagnostico = []
        if resultado.estado == AVAILABLE:
            capacidades = self.descubrir_capacidades()
        return {
            "estado": resultado.estado,
            "motivo": resultado.motivo,
            "verificado_en": ahora(),
            "capacidades": sorted(capacidades),
            # Por que cada capacidad que falta no quedo habilitada. Vacio es que no falta ninguna.
            "diagnostico": list(getattr(self, "diagnostico", None) or []),
        }
