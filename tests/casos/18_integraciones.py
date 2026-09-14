# Bootstrap e integraciones: el almacen, la configuracion, los adapters y el registro.
#
# Escenarios E-01 a E-28 de docs/cambios/integraciones-bootstrap/spec.md. Los del
# instalador -E-29 a E-33- viven en tests/casos/18-integraciones-instalador.ps1, y E-34
# en 04_secretos.py, que ya lee el .env.example entero.
#
# Ningun test sale a una red que no sea 127.0.0.1: el transporte HTTP se inyecta, que es
# justamente para lo que se hizo inyectable. E-10 es la unica excepcion y levanta su
# propio servidor local.
import io
import json
import os
import socket
import sys
import tempfile
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from integraciones import base                          # noqa: E402
from integraciones import http as httpmin               # noqa: E402
from integraciones.almacen import AlmacenSecretos, ErrorDeAlmacen   # noqa: E402
from integraciones.config import (ConfigIntegraciones, ConfigIlegible,  # noqa: E402
                                  ClaveProhibida)
from integraciones.gitlab import IntegracionGitLab      # noqa: E402
from integraciones.jira import IntegracionJira          # noqa: E402
from integraciones.registro import RegistroCapacidades  # noqa: E402

CLI = BIN / "dev-harness.py"

TOKEN = "un-token-que-no-tiene-que-aparecer-en-ningun-lado"

ENV_DE_EJEMPLO = """# Un comentario que tiene que sobrevivir.
JIRA_TOKEN=%s

# Otro comentario, con una linea vacia arriba.
GITLAB_TOKEN=<tu-personal-access-token-de-gitlab>
OTRA_COSA=valor-ajeno
""" % TOKEN


# -- andamios ------------------------------------------------------------------

def _proyecto(contenido_env=ENV_DE_EJEMPLO):
    """Un proyecto descartable con .env y .claude/."""
    raiz = tempfile.mkdtemp(prefix="harness-integ-")
    os.makedirs(os.path.join(raiz, ".claude"))
    with open(os.path.join(raiz, ".env"), "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido_env)
    return raiz


def _almacen(raiz, entorno=None):
    return AlmacenSecretos(os.path.join(raiz, ".env"), {} if entorno is None else entorno)


def _config(raiz, documento=None):
    ruta = os.path.join(raiz, ".claude", "harness.integraciones.json")
    if documento is not None:
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(documento))
    return ConfigIntegraciones(ruta)


class Transporte(object):
    """Un servidor falso. Guarda cada llamada y contesta segun la ruta."""

    def __init__(self, respuestas, por_defecto=(404, "")):
        self.respuestas = respuestas
        self.por_defecto = por_defecto
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append((url, headers, timeout))
        for fragmento, respuesta in self.respuestas.items():
            if fragmento in url:
                if isinstance(respuesta, Exception):
                    raise respuesta
                return respuesta
        return self.por_defecto


def _jira(raiz, transporte, config=None, token=TOKEN):
    documento = config if config is not None else {
        "jira": {"enabled": True, "baseUrl": "https://ejemplo.atlassian.net",
                 "usuario": "alguien@buenosaires.gob.ar"}}
    almacen = _almacen(raiz)
    if token:
        almacen.set("JIRA_TOKEN", token)
    return IntegracionJira(_config(raiz, documento).de("jira"), almacen, 5, transporte)


def _gitlab(raiz, transporte, config=None, token=TOKEN):
    documento = config if config is not None else {
        "gitlab": {"enabled": True, "baseUrl": "https://gitlab.ejemplo.gob.ar"}}
    almacen = _almacen(raiz)
    if token:
        almacen.set("GITLAB_TOKEN", token)
    return IntegracionGitLab(_config(raiz, documento).de("gitlab"), almacen, 5, transporte)


class _EntradaFalsa(io.StringIO):
    """Una terminal simulada: lo que la CLI exige antes de pedir credenciales."""

    def isatty(self):
        return True


def _correr_cli(argv, transporte=None, respuestas=None, tokens=None):
    """Corre dev-harness.py en proceso y devuelve (codigo, stdout, stderr).

    `respuestas` son las que la persona tipearia; `tokens`, lo que cargaria por getpass.
    Si se pasan, stdin simula una terminal.
    """
    import builtins
    import getpass as getpass_real
    import importlib.util

    spec = importlib.util.spec_from_file_location("dev_harness_cli", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr, sys.stdin, builtins.input, getpass_real.getpass)
    sys.stdout, sys.stderr = salida, error
    if respuestas is not None or tokens is not None:
        pendientes = list(respuestas or [])
        secretos = list(tokens or [])
        sys.stdin = _EntradaFalsa("")
        builtins.input = lambda prompt="": pendientes.pop(0)
        getpass_real.getpass = lambda prompt="": secretos.pop(0)
    try:
        codigo = modulo.main(argv, transporte)
    finally:
        (sys.stdout, sys.stderr, sys.stdin,
         builtins.input, getpass_real.getpass) = previos
    return codigo, salida.getvalue(), error.getvalue()


# -- E-01 a E-06 — el almacen de secretos --------------------------------------

def test_e01_get_devuelve_lo_que_hay(t):
    """E-01 — get de una variable presente devuelve su valor; de una ausente, None."""
    raiz = _proyecto()
    a = _almacen(raiz)
    t.igual("E-01 presente", TOKEN, a.get("JIRA_TOKEN"))
    t.igual("E-01 ausente", None, a.get("NO_EXISTE"))
    t.igual("E-01 valor ajeno", "valor-ajeno", a.get("OTRA_COSA"))


def test_e01b_placeholder_es_ausente(t):
    """E-01b — un valor vacio o un placeholder entre angulos se lee como ausente.

    Es el placeholder que reparte .env.example. Sin esto el harness saldria a validar
    "<tu-personal-access-token-de-gitlab>" como si fuera un token.
    """
    raiz = _proyecto()
    a = _almacen(raiz)
    t.igual("E-01b placeholder", None, a.get("GITLAB_TOKEN"))
    t.igual("E-01b exists sobre placeholder", False, a.exists("GITLAB_TOKEN"))


def test_e02_el_entorno_le_gana_al_archivo(t):
    """E-02 — con la variable en el .env y en el entorno, gana la del entorno."""
    raiz = _proyecto()
    a = _almacen(raiz, {"JIRA_TOKEN": "el-del-entorno"})
    t.igual("E-02", "el-del-entorno", a.get("JIRA_TOKEN"))


def test_e03_set_no_mueve_el_resto_del_archivo(t):
    """E-03 — set sobre una clave existente reescribe solo esa linea."""
    raiz = _proyecto()
    a = _almacen(raiz)
    a.set("JIRA_TOKEN", "otro-valor")
    texto = open(os.path.join(raiz, ".env"), encoding="utf-8").read()
    t.contiene("E-03 el comentario sigue", "# Un comentario que tiene que sobrevivir.", texto)
    t.contiene("E-03 el segundo comentario sigue", "# Otro comentario, con una linea vacia arriba.",
               texto)
    t.contiene("E-03 la variable ajena sigue", "OTRA_COSA=valor-ajeno", texto)
    t.no_contiene("E-03 el valor viejo se fue", TOKEN, texto)
    t.igual("E-03 el valor nuevo esta", "otro-valor", a.get("JIRA_TOKEN"))
    t.igual("E-03 no se duplico ninguna linea", 6, len(texto.splitlines()))
    orden = [l.split("=")[0] for l in texto.splitlines() if "=" in l]
    t.igual("E-03 el orden de las variables no cambia",
            ["JIRA_TOKEN", "GITLAB_TOKEN", "OTRA_COSA"], orden)


def test_e04_set_de_una_clave_nueva_la_agrega(t):
    """E-04 — set sobre una clave ausente la agrega y el resto no se mueve."""
    raiz = _proyecto()
    a = _almacen(raiz)
    antes = open(os.path.join(raiz, ".env"), encoding="utf-8").read()
    a.set("OPENSHIFT_TOKEN", "otro")
    despues = open(os.path.join(raiz, ".env"), encoding="utf-8").read()
    t.igual("E-04 lo viejo esta intacto", antes.strip(),
            despues.replace("OPENSHIFT_TOKEN=otro", "").strip())
    t.igual("E-04 se puede leer", "otro", a.get("OPENSHIFT_TOKEN"))


def test_e05_remove_borra_la_linea(t):
    """E-05 — remove borra la linea y exists devuelve falso despues."""
    raiz = _proyecto()
    a = _almacen(raiz)
    t.igual("E-05 borro algo", True, a.remove("JIRA_TOKEN"))
    t.igual("E-05 exists despues", False, a.exists("JIRA_TOKEN"))
    t.igual("E-05 borrar lo que no esta", False, a.remove("JIRA_TOKEN"))
    t.contiene("E-05 el resto quedo", "OTRA_COSA=valor-ajeno",
               open(os.path.join(raiz, ".env"), encoding="utf-8").read())


def test_e06_el_almacen_no_muestra_el_valor(t):
    """E-06 — ni el repr del almacen ni el texto de sus excepciones llevan el secreto."""
    raiz = _proyecto()
    a = _almacen(raiz)
    t.no_contiene("E-06 repr", TOKEN, repr(a))
    t.no_contiene("E-06 str", TOKEN, str(a))

    roto = AlmacenSecretos(os.path.join(raiz, "no", "existe", ".env"), {})
    texto = ""
    try:
        roto.set("JIRA_TOKEN", TOKEN)
    except ErrorDeAlmacen as e:
        texto = str(e)
    t.verdadero("E-06 la escritura imposible levanta ErrorDeAlmacen", texto != "")
    t.no_contiene("E-06 la excepcion no lleva el valor", TOKEN, texto)


# -- E-07 a E-09 — la configuracion --------------------------------------------

def test_e07_config_inexistente_no_es_error(t):
    """E-07 — un archivo que no existe es una configuracion vacia, y todo NOT_CONFIGURED."""
    raiz = _proyecto()
    config = ConfigIntegraciones(os.path.join(raiz, ".claude", "no-esta.json"))
    t.igual("E-07 leer", {}, config.leer())
    t.igual("E-07 de()", {}, config.de("jira"))
    transporte = Transporte({})
    integracion = IntegracionJira(config.de("jira"), _almacen(raiz), 5, transporte)
    resultado = integracion.validar_conexion()
    t.igual("E-07 estado", base.NOT_CONFIGURED, resultado.estado)
    t.igual("E-07 sin red", 0, len(transporte.llamadas))
    # "Nunca se configuro" y "alguien la apago" son dos cosas distintas y se arreglan
    # distinto. Si las dos dijeran lo mismo, el mensaje mandaria a apagar lo que nadie
    # prendio.
    t.contiene("E-07 el motivo dice que no se configuro", "todavia no se configuro",
               resultado.motivo)
    t.no_contiene("E-07 y no dice que este deshabilitada", "deshabilitada", resultado.motivo)


def test_e08_la_config_rechaza_una_clave_con_forma_de_secreto(t):
    """E-08 — guardar TOKEN/SECRET/PASSWORD/CREDENTIAL levanta y no toca el archivo."""
    raiz = _proyecto()
    config = _config(raiz, {"jira": {"enabled": True, "baseUrl": "https://x"}})
    antes = open(config.ruta, encoding="utf-8").read()
    for clave in ("jiraToken", "client_secret", "PASSWORD", "miCredential"):
        levanto = False
        try:
            config.guardar("jira", {"baseUrl": "https://x", clave: "algo"})
        except ClaveProhibida:
            levanto = True
        t.igual("E-08 rechaza %s" % clave, True, levanto)
    t.igual("E-08 el archivo no se toco", antes, open(config.ruta, encoding="utf-8").read())


def test_e09_guardar_no_pisa_lo_ajeno(t):
    """E-09 — guardar una integracion no toca las otras, ni lo que el harness no conoce."""
    raiz = _proyecto()
    config = _config(raiz, {
        "_comentario": ["algo que escribio la plantilla"],
        "jira": {"enabled": True, "baseUrl": "https://jira"},
        "sonarqube": {"enabled": True, "baseUrl": "https://sonar"}})
    config.guardar("gitlab", {"enabled": True, "baseUrl": "https://gitlab"})
    documento = config.leer()
    t.igual("E-09 jira intacto", "https://jira", documento["jira"]["baseUrl"])
    t.igual("E-09 una integracion desconocida sobrevive", "https://sonar",
            documento["sonarqube"]["baseUrl"])
    t.igual("E-09 el comentario sobrevive", ["algo que escribio la plantilla"],
            documento["_comentario"])
    t.igual("E-09 lo nuevo esta", "https://gitlab", documento["gitlab"]["baseUrl"])


def test_e28b_config_ilegible_levanta(t):
    """E-28 (la mitad de biblioteca) — un JSON roto levanta ConfigIlegible, no ValueError."""
    raiz = _proyecto()
    ruta = os.path.join(raiz, ".claude", "harness.integraciones.json")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("{ esto no es json")
    levanto = ""
    try:
        ConfigIntegraciones(ruta).leer()
    except ConfigIlegible as e:
        levanto = str(e)
    t.contiene("E-28 nombra el archivo", "harness.integraciones.json", levanto)
    t.contiene("E-28 y dice que hacer con el", "corre el setup", levanto)

    # ConfigIlegible tiene tres variantes y los tests recorrian una sola. Lo que las
    # ata hoy es que comparten la constante QUE_HACER, y una constante compartida es
    # una convencion, no una garantia: alguien escribe la cuarta variante a mano.
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('["esto es una lista, no un objeto"]')
    levanto = ""
    try:
        ConfigIntegraciones(ruta).leer()
    except ConfigIlegible as e:
        levanto = str(e)
    t.contiene("E-28 un JSON que no es objeto tambien dice que hacer", "corre el setup", levanto)


# -- E-10 y E-11 — el cliente HTTP ---------------------------------------------

class _Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        codigo = 401 if "privado" in self.path else 200
        cuerpo = b'{"ok": true}' if codigo == 200 else b'{"error": "no"}'
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


def test_e10_cliente_real_contra_servidor_local(t):
    """E-10 — contra 127.0.0.1, pedir devuelve el codigo y el cuerpo, para 200 y para 401."""
    servidor = HTTPServer(("127.0.0.1", 0), _Manejador)
    hilo = threading.Thread(target=servidor.serve_forever)
    hilo.daemon = True
    hilo.start()
    try:
        base_url = "http://127.0.0.1:%d" % servidor.server_address[1]
        ok = httpmin.pedir(base_url + "/publico", {"Accept": "application/json"}, 5)
        t.igual("E-10 codigo 200", 200, ok.codigo)
        t.igual("E-10 cuerpo", {"ok": True}, ok.datos())
        t.igual("E-10 sin error de red", "", ok.error)

        no = httpmin.pedir(base_url + "/privado", {}, 5)
        t.igual("E-10 codigo 401", 401, no.codigo)
        t.igual("E-10 401 no es ok", False, no.ok)
        # El cuerpo de un 4xx es la mitad fragil de urllib: llega adentro de la
        # excepcion HTTPError y es facil tirarlo sin querer. El descubrimiento de
        # capacidades de GitLab lee justo eso.
        t.igual("E-10 cuerpo del 401", {"error": "no"}, no.datos())
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_e11_un_error_de_red_no_sale_del_modulo(t):
    """E-11 — un error de red vuelve como Respuesta con codigo 0, nunca como excepcion."""
    casos = [
        (socket.timeout(), httpmin.ERROR_TIMEOUT),
        (urllib.error.URLError(socket.gaierror("no such host")), httpmin.ERROR_DNS),
        (urllib.error.URLError("algo"), httpmin.ERROR_RED),
    ]
    for excepcion, esperado in casos:
        def explota(url, headers, timeout, _e=excepcion):
            raise _e
        respuesta = httpmin.pedir("https://x", {}, 1, explota)
        t.igual("E-11 %s -> codigo 0" % esperado, 0, respuesta.codigo)
        t.igual("E-11 %s -> clase" % esperado, esperado, respuesta.error)
    t.no_contiene("E-11 el repr no lleva el cuerpo", "cuerpo",
                  repr(httpmin.Respuesta(500, "el cuerpo secreto")))


# -- E-12 a E-16 — el contrato de una integracion ------------------------------

def test_e12_sin_configuracion_no_sale_a_la_red(t):
    """E-12 — sin baseUrl o sin token, NOT_CONFIGURED y el transporte no se invoca."""
    raiz = _proyecto()
    transporte = Transporte({"myself": (200, "{}")})

    sin_url = _jira(raiz, transporte, {"jira": {"enabled": True, "baseUrl": "", "usuario": "a@b"}})
    t.igual("E-12 sin baseUrl", base.NOT_CONFIGURED, sin_url.validar_conexion().estado)

    raiz2 = _proyecto("# vacio\n")
    sin_token = _jira(raiz2, transporte, token=None)
    resultado = sin_token.validar_conexion()
    t.igual("E-12 sin token", base.NOT_CONFIGURED, resultado.estado)
    t.contiene("E-12 el motivo nombra lo que falta", "JIRA_TOKEN", resultado.motivo)
    t.igual("E-12 ni una llamada", 0, len(transporte.llamadas))


def test_e13_deshabilitada_no_sale_a_la_red(t):
    """E-13 — con enabled en falso, NOT_CONFIGURED con su motivo y sin red."""
    raiz = _proyecto()
    transporte = Transporte({"myself": (200, "{}")})
    apagada = _jira(raiz, transporte, {"jira": {"enabled": False, "baseUrl": "https://x",
                                                "usuario": "a@b"}})
    resultado = apagada.validar_conexion()
    t.igual("E-13 estado", base.NOT_CONFIGURED, resultado.estado)
    t.contiene("E-13 el motivo lo explica", "deshabilitada", resultado.motivo)
    t.igual("E-13 sin red", 0, len(transporte.llamadas))


def test_e14_el_codigo_de_respuesta_decide_el_estado(t):
    """E-14 — 200, 401, 403, timeout, DNS y 5xx dan los estados que corresponden."""
    raiz = _proyecto()
    casos = [
        ((200, '{"accountId":"x"}'), base.AVAILABLE),
        ((401, "unauthorized"), base.AUTHENTICATION_FAILED),
        ((403, "forbidden"), base.PERMISSION_DENIED),
        ((500, "boom"), base.CONNECTION_FAILED),
        ((302, ""), base.CONNECTION_FAILED),
    ]
    for respuesta, esperado in casos:
        integracion = _jira(raiz, Transporte({"myself": respuesta}))
        t.igual("E-14 %d" % respuesta[0], esperado, integracion.validar_conexion().estado)

    for excepcion in (socket.timeout(), urllib.error.URLError(socket.gaierror("x"))):
        integracion = _jira(raiz, Transporte({"myself": excepcion}))
        t.igual("E-14 %s" % type(excepcion).__name__, base.CONNECTION_FAILED,
                integracion.validar_conexion().estado)


def test_e15_cada_integracion_manda_su_credencial_donde_va(t):
    """E-15 — Jira usa Authorization Basic; GitLab usa PRIVATE-TOKEN. Nunca en la URL."""
    raiz = _proyecto()

    tj = Transporte({"myself": (200, "{}")})
    _jira(raiz, tj).validar_conexion()
    url, headers, _ = tj.llamadas[0]
    t.contiene("E-15 jira manda Basic", "Basic ", headers.get("Authorization", ""))
    t.no_contiene("E-15 jira no manda el token en claro", TOKEN, headers.get("Authorization", ""))
    t.no_contiene("E-15 jira no lo pone en la URL", TOKEN, url)
    import base64
    esperado = base64.b64encode(("alguien@buenosaires.gob.ar:%s" % TOKEN).encode()).decode()
    t.igual("E-15 jira codifica usuario:token", "Basic " + esperado, headers["Authorization"])

    tg = Transporte({"/user": (200, "{}")})
    _gitlab(raiz, tg).validar_conexion()
    url, headers, _ = tg.llamadas[0]
    t.igual("E-15 gitlab manda PRIVATE-TOKEN", TOKEN, headers.get("PRIVATE-TOKEN"))
    t.no_contiene("E-15 gitlab no lo pone en la URL", TOKEN, url)
    t.igual("E-15 gitlab no manda Authorization", None, headers.get("Authorization"))


def test_e16_ningun_motivo_lleva_el_token(t):
    """E-16 — ni cuando el servidor devuelve el token adentro del cuerpo del error."""
    raiz = _proyecto()
    cuerpo_traidor = '{"error":"token %s invalido"}' % TOKEN
    for codigo in (401, 403, 500, 302):
        integracion = _jira(raiz, Transporte({"myself": (codigo, cuerpo_traidor)}))
        resultado = integracion.validar_conexion()
        t.no_contiene("E-16 motivo %d" % codigo, TOKEN, resultado.motivo)
        t.verdadero("E-16 el motivo dice algo (%d)" % codigo, len(resultado.motivo) > 20)

    integracion = _jira(raiz, Transporte({"myself": (401, cuerpo_traidor)}))
    documento = integracion.estado()
    t.no_contiene("E-16 el documento entero", TOKEN,
                  json.dumps(documento, ensure_ascii=False))


# -- E-17 a E-20 — el descubrimiento -------------------------------------------

def test_e17_lo_que_no_esta_disponible_no_descubre_nada(t):
    """E-17 — sin AVAILABLE no hay capacidades ni una sola llamada de sondeo."""
    raiz = _proyecto()
    transporte = Transporte({"myself": (401, "no")})
    resultado = _jira(raiz, transporte).estado()
    t.igual("E-17 sin capacidades", [], resultado["capacidades"])
    t.igual("E-17 una sola llamada, la de validacion", 1, len(transporte.llamadas))


def test_e18_jira_declara_solo_lo_que_contesta(t):
    """E-18 — con adjuntos en 403 quedan issue.read e issue.search, y nada mas."""
    raiz = _proyecto()
    transporte = Transporte({
        "myself": (200, "{}"),
        "search/jql": (200, '{"issues":[]}'),
        "attachment/meta": (403, "no"),
    })
    resultado = _jira(raiz, transporte).estado()
    t.igual("E-18", ["jira.issue.read", "jira.issue.search"], resultado["capacidades"])


def test_e18b_jira_cae_al_endpoint_viejo_de_busqueda(t):
    """E-18b — si /search/jql no existe (410), se prueba /search y recien ahi se declara."""
    raiz = _proyecto()
    transporte = Transporte({
        "myself": (200, "{}"),
        "search/jql": (410, "gone"),
        "/rest/api/3/search?": (200, '{"issues":[]}'),
        "attachment/meta": (200, '{"enabled":true}'),
    })
    resultado = _jira(raiz, transporte).estado()
    t.igual("E-18b las tres", ["jira.attachment.read", "jira.issue.read", "jira.issue.search"],
            resultado["capacidades"])

    sin_busqueda = Transporte({
        "myself": (200, "{}"),
        "search/jql": (410, "gone"),
        "/rest/api/3/search?": (403, "no"),
        "attachment/meta": (200, "{}"),
    })
    t.igual("E-18b sin busqueda queda solo adjuntos", ["jira.attachment.read"],
            _jira(raiz, sin_busqueda).estado()["capacidades"])


def test_e19_gitlab_deriva_de_los_scopes(t):
    """E-19 — read_api habilita las cuatro; read_repository solo repository.read."""
    raiz = _proyecto()
    completo = Transporte({
        "/user": (200, "{}"),
        "personal_access_tokens/self": (200, '{"scopes":["read_api","read_user"]}'),
    })
    t.igual("E-19 read_api", ["gitlab.branch.read", "gitlab.merge_request.read",
                              "gitlab.project.read", "gitlab.repository.read"],
            _gitlab(raiz, completo).estado()["capacidades"])

    limitado = Transporte({
        "/user": (200, "{}"),
        "personal_access_tokens/self": (200, '{"scopes":["read_repository"]}'),
    })
    t.igual("E-19 read_repository", ["gitlab.repository.read"],
            _gitlab(raiz, limitado).estado()["capacidades"])


def test_e20_gitlab_viejo_cae_al_sondeo(t):
    """E-20 — sin endpoint de scopes (404) se sondea, y se registra lo que contesto 200."""
    raiz = _proyecto()
    transporte = Transporte({
        "/user": (200, "{}"),
        "personal_access_tokens/self": (404, "not found"),
        "/projects?": (200, "[]"),
        "/merge_requests?": (403, "no"),
    })
    resultado = _gitlab(raiz, transporte).estado()
    t.igual("E-20", ["gitlab.branch.read", "gitlab.project.read", "gitlab.repository.read"],
            resultado["capacidades"])
    t.verdadero("E-20 sondeo, no scopes",
                any("/projects?" in url for url, _, _ in transporte.llamadas))


# -- E-21 a E-23 — el registro -------------------------------------------------

def _registro():
    return RegistroCapacidades({"jira": IntegracionJira.CAPACIDADES,
                                "gitlab": IntegracionGitLab.CAPACIDADES})


def test_e21_lo_soportado_sin_validar_figura_disabled(t):
    """E-21 — una capacidad soportada cuya integracion no valido figura DISABLED."""
    registro = _registro()
    registro.anotar("jira", {"estado": base.AUTHENTICATION_FAILED, "motivo": "x",
                             "verificado_en": "2026-09-14T00:00:00", "capacidades": []})
    registro.anotar("gitlab", {"estado": base.AVAILABLE, "motivo": "",
                               "verificado_en": "2026-09-14T00:00:00",
                               "capacidades": ["gitlab.project.read"]})
    documento = registro.como_documento("0.16.0")
    t.igual("E-21 jira aparece", "DISABLED", documento["capacidades"]["jira.issue.read"])
    t.igual("E-21 gitlab validada", "ENABLED", documento["capacidades"]["gitlab.project.read"])
    t.igual("E-21 gitlab no validada", "DISABLED",
            documento["capacidades"]["gitlab.branch.read"])
    t.igual("E-21 estan las siete", 7, len(documento["capacidades"]))


def test_e22_el_registro_contesta_por_capacidad_y_por_integracion(t):
    """E-22 — disponibles() solo las ENABLED; por_integracion agrupa."""
    registro = _registro()
    registro.registrar("jira.issue.read", "jira")
    registro.registrar("gitlab.project.read", "gitlab")
    t.igual("E-22 disponibles", ["gitlab.project.read", "jira.issue.read"], registro.disponibles())
    t.igual("E-22 esta_disponible", True, registro.esta_disponible("jira.issue.read"))
    t.igual("E-22 no registrada", False, registro.esta_disponible("jira.issue.search"))
    t.igual("E-22 por integracion", ["jira.issue.read"], registro.por_integracion("jira"))
    t.igual("E-22 quitar", True, registro.quitar("jira.issue.read"))
    t.igual("E-22 despues de quitar", False, registro.esta_disponible("jira.issue.read"))

    rechazo = False
    try:
        registro.registrar("jira.issue.read", "gitlab")
    except ValueError:
        rechazo = True
    t.igual("E-22 no se registra una capacidad ajena", True, rechazo)


def test_e23_el_manifiesto_y_el_codigo_declaran_lo_mismo(t):
    """E-23 — capacidadesSoportadas del manifiesto == las de los adapters."""
    manifiesto = json.loads((RAIZ / "harnesses" / "desarrollo" / "manifest.json")
                            .read_text(encoding="utf-8"))
    del_codigo = sorted(list(IntegracionJira.CAPACIDADES) + list(IntegracionGitLab.CAPACIDADES))
    t.igual("E-23", del_codigo, sorted(manifiesto.get("capacidadesSoportadas", [])))


# -- E-24 a E-28 — la CLI ------------------------------------------------------

def test_e24_una_integracion_caida_no_voltea_el_harness(t):
    """E-24 — con Jira caido y GitLab valido: codigo 0, READY, y las de GitLab ENABLED."""
    raiz = _proyecto("JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    _config(raiz, {"jira": {"enabled": True, "baseUrl": "https://jira", "usuario": "a@b"},
                   "gitlab": {"enabled": True, "baseUrl": "https://gitlab"}})
    transporte = Transporte({
        "jira": socket.timeout(),
        # El cuerpo devuelve el token, que es lo que hace un servidor mal configurado.
        # Sin esto las dos assertions de mas abajo no tendrian nada que atrapar.
        "/user": (200, '{"username":"x","eco":"%s"}' % TOKEN),
        "personal_access_tokens/self": (200, '{"scopes":["read_api"]}'),
    })
    codigo, salida, _ = _correr_cli(["estado", "--proyecto", raiz], transporte)
    t.igual("E-24 codigo 0", 0, codigo)
    t.contiene("E-24 declara READY", "HARNESS READY", salida)
    t.contiene("E-24 jira caido", "CONNECTION_FAILED", salida)

    documento = json.loads(open(os.path.join(raiz, ".claude", "harness.capacidades.json"),
                                encoding="utf-8").read())
    t.igual("E-24 gitlab habilitado", "ENABLED", documento["capacidades"]["gitlab.project.read"])
    t.igual("E-24 jira deshabilitado", "DISABLED", documento["capacidades"]["jira.issue.read"])
    t.no_contiene("E-24 el documento no lleva el token", TOKEN, json.dumps(documento))
    t.no_contiene("E-24 la salida no lleva el token", TOKEN, salida)


def test_e25_con_todo_configurado_el_setup_no_pregunta(t):
    """E-25 — setup con la configuracion completa no lee de stdin: no falla ni se cuelga."""
    raiz = _proyecto("JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    _config(raiz, {"jira": {"enabled": True, "baseUrl": "https://jira", "usuario": "a@b"},
                   "gitlab": {"enabled": False, "baseUrl": ""}})
    transporte = Transporte({"jira": (200, "{}"), "search/jql": (200, "{}"),
                             "attachment/meta": (200, "{}")})
    stdin_previo = sys.stdin
    sys.stdin = io.StringIO("")   # leer de aca levantaria EOFError
    try:
        codigo, salida, _ = _correr_cli(["setup", "--proyecto", raiz], transporte)
    finally:
        sys.stdin = stdin_previo
    t.igual("E-25 codigo 0", 0, codigo)
    t.contiene("E-25 llego al final", "HARNESS READY", salida)
    t.contiene("E-25 reconoce que ya estaba configurado", "configuracion existente", salida)


def test_e26_reconfigurar_uno_no_toca_al_otro(t):
    """E-26 — reconfigurar gitlab deja la configuracion y el token de Jira como estaban."""
    raiz = _proyecto("JIRA_TOKEN=%s\nGITLAB_TOKEN=el-viejo-de-gitlab\n" % TOKEN)
    config = _config(raiz, {"jira": {"enabled": True, "baseUrl": "https://jira",
                                     "usuario": "a@b"},
                            "gitlab": {"enabled": True, "baseUrl": "https://viejo"}})
    transporte = Transporte({"jira": (200, "{}"), "search/jql": (200, "{}"),
                             "attachment/meta": (200, "{}"),
                             "/user": (200, "{}"),
                             "personal_access_tokens/self": (200, '{"scopes":["read_api"]}')})
    codigo, salida, _ = _correr_cli(
        ["reconfigurar", "gitlab", "--proyecto", raiz], transporte,
        respuestas=["s", "https://nuevo", "s"], tokens=["el-nuevo-de-gitlab"])

    almacen = _almacen(raiz)
    t.igual("E-26 codigo 0", 0, codigo)
    t.igual("E-26 jira baseUrl intacta", "https://jira", config.de("jira")["baseUrl"])
    t.igual("E-26 jira usuario intacto", "a@b", config.de("jira")["usuario"])
    t.igual("E-26 el token de jira intacto", TOKEN, almacen.get("JIRA_TOKEN"))
    t.igual("E-26 gitlab se reconfiguro", "https://nuevo", config.de("gitlab")["baseUrl"])
    t.igual("E-26 el token de gitlab cambio", "el-nuevo-de-gitlab", almacen.get("GITLAB_TOKEN"))
    t.no_contiene("E-26 el token nuevo no se imprime", "el-nuevo-de-gitlab", salida)


def test_e26b_el_setup_carga_lo_que_falta(t):
    """E-26b — una primera corrida real: se responden las preguntas y queda todo cargado.

    Es el unico test que recorre el camino entero del asistente: pregunta, guarda la
    configuracion, guarda el token por el almacen, valida y descubre.
    """
    raiz = _proyecto("# vacio\n")
    transporte = Transporte({
        "myself": (200, "{}"), "search/jql": (200, "{}"), "attachment/meta": (200, "{}"),
        "/user": (200, "{}"),
        "personal_access_tokens/self": (200, '{"scopes":["read_api"]}')})
    codigo, salida, error = _correr_cli(
        ["setup", "--proyecto", raiz], transporte,
        respuestas=["s", "https://jira.ejemplo", "yo@buenosaires.gob.ar",
                    "s", "https://gitlab.ejemplo"],
        tokens=["token-de-jira-cargado", "token-de-gitlab-cargado"])

    config = ConfigIntegraciones(os.path.join(raiz, ".claude", "harness.integraciones.json"))
    almacen = _almacen(raiz)
    t.igual("E-26b codigo 0", 0, codigo)
    t.contiene("E-26b dice que es la primera vez", "configuracion inicial", salida)
    t.igual("E-26b jira baseUrl", "https://jira.ejemplo", config.de("jira")["baseUrl"])
    t.igual("E-26b jira usuario", "yo@buenosaires.gob.ar", config.de("jira")["usuario"])
    t.igual("E-26b gitlab baseUrl", "https://gitlab.ejemplo", config.de("gitlab")["baseUrl"])
    t.igual("E-26b el token quedo en el .env", "token-de-jira-cargado", almacen.get("JIRA_TOKEN"))
    t.no_contiene("E-26b el token no se imprime", "token-de-jira-cargado", salida + error)
    t.no_contiene("E-26b la config no guarda el token", "token-de-jira-cargado",
                  open(config.ruta, encoding="utf-8").read())
    documento = json.loads(open(os.path.join(raiz, ".claude", "harness.capacidades.json"),
                                encoding="utf-8").read())
    t.igual("E-26b quedaron las siete habilitadas", 7,
            sum(1 for v in documento["capacidades"].values() if v == "ENABLED"))


def test_e27_el_token_por_linea_de_comandos_se_rechaza(t):
    """E-27 — --token sale distinto de 0, explica por que, y no escribe nada."""
    raiz = _proyecto("# vacio\n")
    antes = sorted(os.listdir(os.path.join(raiz, ".claude")))
    codigo, salida, error = _correr_cli(["setup", "--proyecto", raiz, "--token", TOKEN])
    t.verdadero("E-27 no sale con 0", codigo != 0)
    t.contiene("E-27 explica el motivo", "historial", error)
    t.no_contiene("E-27 no repite el token", TOKEN, error + salida)
    t.igual("E-27 no escribio nada", antes, sorted(os.listdir(os.path.join(raiz, ".claude"))))


def test_e28_config_ilegible_sale_con_2(t):
    """E-28 — codigo 2 y un mensaje que nombra el archivo, no una traza de Python."""
    raiz = _proyecto()
    with open(os.path.join(raiz, ".claude", "harness.integraciones.json"), "w",
              encoding="utf-8") as f:
        f.write("{ roto")
    codigo, salida, error = _correr_cli(["estado", "--proyecto", raiz], Transporte({}))
    t.igual("E-28 codigo 2", 2, codigo)
    t.contiene("E-28 nombra el archivo", "harness.integraciones.json", error)
    t.contiene("E-28 dice que hacer", "corre el setup", error)
    t.no_contiene("E-28 sin traza", "Traceback", error + salida)
