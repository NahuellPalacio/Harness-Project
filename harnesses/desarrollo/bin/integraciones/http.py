"""Cliente HTTP minimo, sobre urllib. Biblioteca estandar y nada mas.

Tres cosas lo definen, y las tres estan para lo mismo:

1. El transporte se inyecta. En produccion es urllib; en la suite es una funcion
   que devuelve codigos fijos. Sin esto, probar los cinco estados de una
   integracion exigiria una instancia real de Jira y un token que venza a pedido.
2. No sigue redirecciones. urllib las sigue solo y reenvia los headers: una
   baseUrl mal escrita que redirige a otro host se llevaria el token puesto. Un
   3xx vuelve como respuesta, no como salto.

   La unica excepcion es `descargar`, que baja adjuntos: Jira Cloud sirve el binario
   desde una URL firmada a la que redirige con 303. `descargar` sigue UN salto, solo a
   https, y el segundo pedido va sin ningun header, asi que la credencial no viaja. Ver
   docs/cambios/adjuntos-de-jira-redirigidos/spec.md.
3. Nunca imprime, nunca registra y nunca guarda los headers. El token viaja adentro
   de `headers` y esa estructura no sale de la llamada.
"""
import http.client
import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_POR_DEFECTO = 5

SIN_ERROR = ""
ERROR_TIMEOUT = "timeout"
ERROR_DNS = "dns"
ERROR_TLS = "tls"
ERROR_RED = "red"
# Una URL que http.client no acepta (un espacio, un caracter de control). Su excepcion trae la
# URL en el mensaje, y la de un adjunto firmado lleva un token en la query: se convierte en este
# codigo y el mensaje se tira.
ERROR_URL = "url"

# Un cuerpo mas grande que esto no se lee entero. Ninguna respuesta de validacion
# necesita mas, y un servidor que devuelve un HTML de error de 3 MB no tiene por
# que costar 3 MB de memoria.
MAXIMO_CUERPO = 64 * 1024


class Respuesta(object):
    """Lo que devuelve una llamada. `codigo` 0 significa que no hubo respuesta."""

    def __init__(self, codigo, cuerpo="", error=SIN_ERROR):
        self.codigo = codigo
        self.cuerpo = cuerpo
        self.error = error

    @property
    def ok(self):
        return 200 <= self.codigo < 300

    def datos(self):
        """El cuerpo como JSON, o None si no lo es. Nunca levanta."""
        try:
            return json.loads(self.cuerpo)
        except (ValueError, TypeError):
            return None

    def __repr__(self):
        # El cuerpo queda afuera a proposito: un servidor puede devolver adentro
        # del error la credencial que recibio, y un repr termina en cualquier log.
        return "Respuesta(codigo=%d, error=%r)" % (self.codigo, self.error)


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _abridor():
    return urllib.request.build_opener(_SinRedirecciones())


def transporte_urllib(url, headers, timeout):
    """Devuelve (codigo, cuerpo). Un 4xx o 5xx tambien es una respuesta, no un error."""
    pedido = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with _abridor().open(pedido, timeout=timeout) as r:
            return r.getcode(), r.read(MAXIMO_CUERPO).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        cuerpo = ""
        try:
            cuerpo = e.read(MAXIMO_CUERPO).decode("utf-8", "replace")
        except Exception:
            pass
        return e.code, cuerpo


def _clase_de_error(e):
    motivo = getattr(e, "reason", e)
    if isinstance(motivo, socket.timeout):
        return ERROR_TIMEOUT
    if isinstance(motivo, socket.gaierror):
        return ERROR_DNS
    if isinstance(motivo, ssl.SSLError):
        return ERROR_TLS
    if isinstance(motivo, TimeoutError):
        return ERROR_TIMEOUT
    return ERROR_RED


def pedir(url, headers=None, timeout=TIMEOUT_POR_DEFECTO, transporte=None):
    """Una llamada GET. Nunca levanta: un error de red vuelve como Respuesta."""
    llamar = transporte or transporte_urllib
    try:
        codigo, cuerpo = llamar(url, dict(headers or {}), timeout)
    except (http.client.InvalidURL, ValueError):
        return Respuesta(0, "", ERROR_URL)
    except socket.timeout:
        return Respuesta(0, "", ERROR_TIMEOUT)
    except urllib.error.URLError as e:
        return Respuesta(0, "", _clase_de_error(e))
    except (OSError, ssl.SSLError) as e:
        return Respuesta(0, "", _clase_de_error(e))
    return Respuesta(codigo, cuerpo, SIN_ERROR)


class RespuestaBinaria(object):
    """Lo mismo, con los bytes crudos. Un PDF que pasa por un decode a str vuelve roto."""

    def __init__(self, codigo, datos=b"", error=SIN_ERROR, cabeceras=None):
        self.codigo = codigo
        self.datos = datos
        self.error = error
        # Solo las que hacen falta para seguir una redireccion. Nunca las del pedido.
        self.cabeceras = dict(cabeceras or {})
        # El host al que se salto, si hubo salto. El host y nada mas: el camino y la query de
        # una URL firmada llevan un token.
        self.redirigida_a = None

    @property
    def ok(self):
        return 200 <= self.codigo < 300

    def __repr__(self):
        return "RespuestaBinaria(codigo=%d, bytes=%d, error=%r)" % (
            self.codigo, len(self.datos), self.error)


# Un adjunto mas grande que esto no se baja entero. Los documentos de un proyecto no
# llegan a esto y un video sin querer si: el tope evita que una resolucion de contexto
# se traiga medio Jira a disco.
MAXIMO_ADJUNTO = 25 * 1024 * 1024


# Los errores propios de una descarga. Salen en el motivo, nunca con la URL.
ERROR_TOPE = "ATTACHMENT_TOO_LARGE"
ERROR_REDIRECCION_NO_HTTPS = "REDIRECT_NOT_HTTPS"
ERROR_REDIRECCION_SIN_DESTINO = "REDIRECT_WITHOUT_LOCATION"
ERROR_REDIRECCIONES_DE_MAS = "REDIRECT_TOO_MANY"

REDIRECCIONES = (301, 302, 303, 307, 308)


def transporte_bytes_urllib(url, headers, timeout):
    """Devuelve (codigo, bytes, cabeceras). No sigue redirecciones: un 3xx vuelve con su
    `Location`, y decidir si se sigue es de `descargar`.

    🔴 Lee un byte mas que el tope. Leer exactamente el tope guardaba un adjunto mas grande
    TRUNCADO y sin aviso, y se hasheaba como si fuera el original.
    """
    pedido = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with _abridor().open(pedido, timeout=timeout) as r:
            return r.getcode(), r.read(MAXIMO_ADJUNTO + 1), {}
    except urllib.error.HTTPError as e:
        destino = e.headers.get("Location") if e.headers is not None else None
        return e.code, b"", ({"Location": destino} if destino else {})


def pedir_bytes(url, headers=None, timeout=TIMEOUT_POR_DEFECTO, transporte=None):
    """Una descarga, sin seguir redirecciones. Nunca levanta, igual que `pedir`.

    Acepta transportes de dos elementos (codigo, bytes) y de tres (con cabeceras). Uno de dos
    no dice a donde redirige, y entonces un 3xx suyo no se puede seguir.
    """
    llamar = transporte or transporte_bytes_urllib
    try:
        vuelta = llamar(url, dict(headers or {}), timeout)
    except (http.client.InvalidURL, ValueError):
        return RespuestaBinaria(0, b"", ERROR_URL)
    except socket.timeout:
        return RespuestaBinaria(0, b"", ERROR_TIMEOUT)
    except urllib.error.URLError as e:
        return RespuestaBinaria(0, b"", _clase_de_error(e))
    except (OSError, ssl.SSLError) as e:
        return RespuestaBinaria(0, b"", _clase_de_error(e))
    codigo, datos = vuelta[0], vuelta[1]
    cabeceras = vuelta[2] if len(vuelta) > 2 and isinstance(vuelta[2], dict) else {}
    if datos is not None and len(datos) > MAXIMO_ADJUNTO:
        return RespuestaBinaria(codigo, b"", ERROR_TOPE)
    return RespuestaBinaria(codigo, datos or b"", SIN_ERROR, cabeceras)


def _destino_de(respuesta):
    for nombre, valor in respuesta.cabeceras.items():
        if str(nombre).lower() == "location" and valor:
            return str(valor)
    return None


def descargar(url, headers=None, timeout=TIMEOUT_POR_DEFECTO, transporte=None):
    """Una descarga que sigue UNA redireccion, solo a https y sin ningun header.

    🔴 El segundo pedido va con `{}`: ni `Authorization` ni ninguna cabecera que haya armado
    la integracion. Es lo que hace seguro seguir el salto sin restringir el host: al destino le
    llega un GET anonimo, y la credencial no sale nunca del host configurado.
    """
    primera = pedir_bytes(url, headers, timeout, transporte)
    if primera.error or primera.codigo not in REDIRECCIONES:
        return primera
    destino = _destino_de(primera)
    if not destino:
        return RespuestaBinaria(primera.codigo, b"", ERROR_REDIRECCION_SIN_DESTINO)
    absoluta = urllib.parse.urljoin(url, destino)
    partes = urllib.parse.urlsplit(absoluta)
    if partes.scheme.lower() != "https":
        vuelta = RespuestaBinaria(primera.codigo, b"", ERROR_REDIRECCION_NO_HTTPS)
        vuelta.redirigida_a = partes.hostname
        return vuelta
    segunda = pedir_bytes(absoluta, {}, timeout, transporte)
    segunda.redirigida_a = partes.hostname
    if not segunda.error and segunda.codigo in REDIRECCIONES:
        vuelta = RespuestaBinaria(segunda.codigo, b"", ERROR_REDIRECCIONES_DE_MAS)
        vuelta.redirigida_a = partes.hostname
        return vuelta
    return segunda


_MOTIVOS_DE_DESCARGA = {
    ERROR_TOPE: "el adjunto pasa el tope de %d MB y no se guarda, ni entero ni cortado"
                % (MAXIMO_ADJUNTO // (1024 * 1024)),
    ERROR_REDIRECCION_NO_HTTPS: "la redireccion apunta a una URL que no es https: no se siguio",
    ERROR_REDIRECCION_SIN_DESTINO: "el servidor redirigio sin decir a donde: no se siguio",
    ERROR_REDIRECCIONES_DE_MAS: "hubo mas de una redireccion: se sigue una sola",
    ERROR_TIMEOUT: "no respondio a tiempo",
    ERROR_DNS: "no se pudo resolver el nombre del servidor",
    ERROR_TLS: "fallo la conexion segura (TLS)",
    ERROR_RED: "no se pudo conectar",
    ERROR_URL: "la URL no es valida y no se pidio",
}


def motivo_de_descarga(respuesta):
    """Por que no se bajo, en una linea. Con el host del salto si hubo, nunca con su URL."""
    if respuesta.error:
        texto = _MOTIVOS_DE_DESCARGA.get(respuesta.error, "no se pudo bajar (%s)" % respuesta.error)
    elif respuesta.codigo in REDIRECCIONES:
        texto = "el servidor contesto %d y no se siguio" % respuesta.codigo
    else:
        texto = "el servidor contesto %d" % respuesta.codigo
    if respuesta.redirigida_a:
        texto += " (redireccion a %s)" % respuesta.redirigida_a
    return texto


def unir(base, camino):
    """Pega una ruta a una baseUrl sin duplicar ni comerse la barra."""
    return base.rstrip("/") + "/" + camino.lstrip("/")
