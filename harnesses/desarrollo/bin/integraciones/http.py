"""Cliente HTTP minimo, sobre urllib. Biblioteca estandar y nada mas.

Tres cosas lo definen, y las tres estan para lo mismo:

1. El transporte se inyecta. En produccion es urllib; en la suite es una funcion
   que devuelve codigos fijos. Sin esto, probar los cinco estados de una
   integracion exigiria una instancia real de Jira y un token que venza a pedido.
2. No sigue redirecciones. urllib las sigue solo y reenvia los headers: una
   baseUrl mal escrita que redirige a otro host se llevaria el token puesto. Un
   3xx vuelve como respuesta, no como salto.
3. Nunca imprime, nunca registra y nunca guarda los headers. El token viaja adentro
   de `headers` y esa estructura no sale de la llamada.
"""
import json
import socket
import ssl
import urllib.error
import urllib.request

TIMEOUT_POR_DEFECTO = 5

SIN_ERROR = ""
ERROR_TIMEOUT = "timeout"
ERROR_DNS = "dns"
ERROR_TLS = "tls"
ERROR_RED = "red"

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
    except socket.timeout:
        return Respuesta(0, "", ERROR_TIMEOUT)
    except urllib.error.URLError as e:
        return Respuesta(0, "", _clase_de_error(e))
    except (OSError, ssl.SSLError) as e:
        return Respuesta(0, "", _clase_de_error(e))
    return Respuesta(codigo, cuerpo, SIN_ERROR)


class RespuestaBinaria(object):
    """Lo mismo, con los bytes crudos. Un PDF que pasa por un decode a str vuelve roto."""

    def __init__(self, codigo, datos=b"", error=SIN_ERROR):
        self.codigo = codigo
        self.datos = datos
        self.error = error

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


def transporte_bytes_urllib(url, headers, timeout):
    """Devuelve (codigo, bytes)."""
    pedido = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with _abridor().open(pedido, timeout=timeout) as r:
            return r.getcode(), r.read(MAXIMO_ADJUNTO)
    except urllib.error.HTTPError as e:
        return e.code, b""


def pedir_bytes(url, headers=None, timeout=TIMEOUT_POR_DEFECTO, transporte=None):
    """Una descarga. Nunca levanta, igual que `pedir`."""
    llamar = transporte or transporte_bytes_urllib
    try:
        codigo, datos = llamar(url, dict(headers or {}), timeout)
    except socket.timeout:
        return RespuestaBinaria(0, b"", ERROR_TIMEOUT)
    except urllib.error.URLError as e:
        return RespuestaBinaria(0, b"", _clase_de_error(e))
    except (OSError, ssl.SSLError) as e:
        return RespuestaBinaria(0, b"", _clase_de_error(e))
    return RespuestaBinaria(codigo, datos, SIN_ERROR)


def unir(base, camino):
    """Pega una ruta a una baseUrl sin duplicar ni comerse la barra."""
    return base.rstrip("/") + "/" + camino.lstrip("/")
