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
import re
import os
import socket
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
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


def _lock(raiz, harness=("comun", "desarrollo")):
    """El lockfile que deja install.ps1. Sin el, el resolvedor del estado general dice
    BLOQUEADO por falta de instalacion, y E-24 no podria distinguir "una integracion caida
    voltea al harness" de "el harness no esta instalado"."""
    with open(os.path.join(raiz, ".claude", "harness.lock.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"version": "0.20.0", "harness": list(harness),
                            "instalado": "2026-09-24 10:00:00", "archivos": []}))


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
    """E-18 — con adjuntos en 403 quedan issue.read e issue.search, y nada mas.

    Desde docs/cambios/sonda-de-jira-acotada/spec.md, issue.read se sondea sola: sin issue en
    la busqueda, por el permiso BROWSE_PROJECTS."""
    raiz = _proyecto()
    transporte = Transporte({
        "myself": (200, "{}"),
        "search/jql": (200, '{"issues":[]}'),
        "mypermissions": (200, '{"permissions":{"BROWSE_PROJECTS":{"havePermission":true}}}'),
        "attachment/meta": (403, "no"),
    })
    resultado = _jira(raiz, transporte).estado()
    t.igual("E-18", ["jira.issue.read", "jira.issue.search"], resultado["capacidades"])


def test_e18b_sin_caida_al_endpoint_viejo(t):
    """E-18b — pisado por docs/cambios/sonda-de-jira-acotada/spec.md (E-05).

    La version anterior probaba que con 410 en /search/jql se caia a /search. En Jira Cloud
    /search contesta 410 igual, y la caida tapaba el codigo verdadero. Ahora no se cae: la
    busqueda queda deshabilitada con su diagnostico, aunque /search contestara 200."""
    raiz = _proyecto()
    transporte = Transporte({
        "myself": (200, "{}"),
        "search/jql": (410, "gone"),
        "/rest/api/3/search?": (200, '{"issues":[]}'),
        "mypermissions": (200, '{"permissions":{"BROWSE_PROJECTS":{"havePermission":true}}}'),
        "attachment/meta": (200, '{"enabled":true}'),
    })
    resultado = _jira(raiz, transporte).estado()
    t.igual("E-18b sin busqueda, aunque /search contestara", ["jira.attachment.read",
                                                              "jira.issue.read"],
            resultado["capacidades"])
    t.verdadero("E-18b y /search no se llamo",
                not any("/rest/api/3/search?" in u for u, _, _ in transporte.llamadas))


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
    """E-24 — con Jira caido y GitLab valido: codigo 0, el harness sigue en pie y las de GitLab
    ENABLED.

    Hasta bloque-1-bienvenida esto afirmaba "HARNESS READY", una palabra fija. Ahora el estado
    sale del resolvedor (E-21 de esa spec): con Jira caido es PARCIAL, que es exactamente "no
    voltea al harness". Lo que sigue prohibido es BLOQUEADO."""
    raiz = _proyecto("JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    _lock(raiz)
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
    t.contiene("E-24 el harness sigue en pie: PARCIAL", "Harness GCBA ◐ PARCIAL", salida)
    t.no_contiene("E-24 y no BLOQUEADO", "BLOQUEADO", salida)
    t.contiene("E-24 la linea nombra a Jira caido", "Jira SIN CONEXIÓN", salida)
    t.contiene("E-24 y a GitLab disponible", "GitLab DISPONIBLE", salida)
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
    _lock(raiz)
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
    # El final del setup es la seccion Estado, que abre con la linea del estado general
    # (bloque-1-bienvenida E-21).
    estado = salida.split("Estado\n" + "-" * 48 + "\n", 1)
    t.verdadero("E-25 llego al final: la seccion Estado abre con el estado general",
                len(estado) == 2 and estado[1].startswith("Harness GCBA "))
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
        "mypermissions": (200, '{"permissions":{"BROWSE_PROJECTS":{"havePermission":true}}}'),
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


# -- docs/cambios/sonda-de-jira-acotada/spec.md --------------------------------
#
# El transporte de abajo contesta segun la JQL DECODIFICADA, no solo segun el camino: es lo
# que la version anterior no podia distinguir, y por eso una JQL ilimitada pasaba verde contra
# el falso y rompia contra Jira Cloud.
from urllib.parse import parse_qs, urlparse                        # noqa: E402

from integraciones import jira as jira_mod                          # noqa: E402

JQL_ILIMITADA = "Aquí no se permiten las consultas JQL ilimitadas. Añade una restricción de búsqueda a tu consulta."
PERMISO_SI = '{"permissions":{"BROWSE_PROJECTS":{"havePermission":true}}}'
PERMISO_NO = '{"permissions":{"BROWSE_PROJECTS":{"havePermission":false}}}'
ISSUE = '{"issues":[{"key":"APPLICDCON-1"}]}'


class TransporteJql(object):
    """Un Jira Cloud falso que decide por la JQL, como el real."""

    def __init__(self, busqueda_acotada=(200, ISSUE), busqueda_ilimitada=None, viejo=(410, "gone"),
                 issue=(200, '{"key":"APPLICDCON-1"}'), permisos=(200, PERMISO_SI),
                 adjuntos=(200, '{"enabled":true}')):
        self.busqueda_acotada = busqueda_acotada
        self.busqueda_ilimitada = busqueda_ilimitada or (
            400, json.dumps({"errorMessages": [JQL_ILIMITADA], "errors": {}}))
        self.viejo, self.issue, self.permisos, self.adjuntos = viejo, issue, permisos, adjuntos
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append((url, headers, timeout))
        partes = urlparse(url)
        if partes.path.endswith("/myself"):
            return (200, "{}")
        if partes.path.endswith("/search/jql"):
            jql = (parse_qs(partes.query).get("jql") or [""])[0]
            # Criterio propio, no el del modulo: si el falso usara `jql_acotada`, una rotura
            # ahi romperia tambien al falso y el test no la veria.
            antes_del_orden = re.split(r"(?i)\border\s+by\b", jql.strip(), 1)[0]
            return self.busqueda_acotada if antes_del_orden.strip() else self.busqueda_ilimitada
        if partes.path.endswith("/rest/api/3/search"):
            return self.viejo
        if "/rest/api/3/issue/" in partes.path:
            return self.issue
        if partes.path.endswith("/mypermissions"):
            return self.permisos
        if partes.path.endswith("/attachment/meta"):
            return self.adjuntos
        return (404, "")

    def jqls(self):
        return [(parse_qs(urlparse(u).query).get("jql") or [""])[0]
                for u, _, _ in self.llamadas if urlparse(u).path.endswith("/search/jql")]

    def a_search_viejo(self):
        return [u for u, _, _ in self.llamadas if urlparse(u).path.endswith("/rest/api/3/search")]


def test_sonda_e01_la_consulta_de_la_sonda_esta_acotada(t):
    """E-01 (sonda-de-jira-acotada) — created >= -30d, maxResults=1, y nada ilimitado."""
    raiz = _proyecto()
    transporte = TransporteJql()
    _jira(raiz, transporte).estado()
    jqls = transporte.jqls()
    t.igual("E-01 (sonda) una sola busqueda", ["created >= -30d order by created DESC"], jqls)
    t.verdadero("E-01 (sonda) ninguna ilimitada",
                all(re.split(r"(?i)\border\s+by\b", j, 1)[0].strip() for j in jqls))
    t.verdadero("E-01 (sonda) con maxResults=1",
                any("maxResults=1" in u for u, _, _ in transporte.llamadas if "search/jql" in u))


def test_sonda_e02_e03_busqueda_disponible(t):
    """E-02 y E-03 (sonda-de-jira-acotada) — 400 a la ilimitada, 200 a la acotada; y vacia."""
    raiz = _proyecto()
    r = _jira(raiz, TransporteJql()).estado()
    t.verdadero("E-02 (sonda) con 400 a la ilimitada y 200 a la acotada, hay busqueda",
                "jira.issue.search" in r["capacidades"])
    r = _jira(raiz, TransporteJql(busqueda_acotada=(200, '{"issues":[]}'))).estado()
    t.verdadero("E-03 (sonda) issues vacio sigue siendo busqueda disponible",
                "jira.issue.search" in r["capacidades"])


def test_sonda_e04_un_400_no_cae_y_se_explica(t):
    """E-04 (sonda-de-jira-acotada) — 400 en search/jql: sin /search, sin busqueda, con motivo."""
    raiz = _proyecto()
    transporte = TransporteJql(busqueda_acotada=(400, json.dumps(
        {"errorMessages": [JQL_ILIMITADA]})))
    r = _jira(raiz, transporte).estado()
    t.verdadero("E-04 (sonda) sin busqueda", "jira.issue.search" not in r["capacidades"])
    t.igual("E-04 (sonda) sin llamada a /search", [], transporte.a_search_viejo())
    linea = " ".join(x for x in r["diagnostico"] if x.startswith("jira.issue.search"))
    t.contiene("E-04 (sonda) el diagnostico dice que Jira rechazo la consulta",
               "Jira Cloud rechazo la busqueda de prueba (400)", linea)
    t.contiene("E-04 (sonda) con el errorMessages", "consultas JQL ilimitadas", linea)


def test_sonda_e05_e06_sin_caida_con_404_o_410(t):
    """E-05 y E-06 (sonda-de-jira-acotada) — ni la sonda ni buscar caen a /search."""
    raiz = _proyecto()
    for codigo in (404, 410):
        transporte = TransporteJql(busqueda_acotada=(codigo, "no"), viejo=(200, ISSUE))
        r = _jira(raiz, transporte).estado()
        t.igual("E-05 (sonda) %d: sin llamada a /search" % codigo, [], transporte.a_search_viejo())
        t.contiene("E-05 (sonda) %d: el diagnostico nombra el codigo" % codigo,
                   "contesto %d" % codigo, " ".join(r["diagnostico"]))
    transporte = TransporteJql(busqueda_acotada=(410, "gone"), viejo=(200, ISSUE))
    respuesta = _jira(raiz, transporte).buscar('project = "X"')
    t.igual("E-06 (sonda) buscar devuelve el 410", 410, respuesta.codigo)
    t.igual("E-06 (sonda) sin llamada a /search", [], transporte.a_search_viejo())


def test_sonda_e07_issue_read_por_el_issue(t):
    """E-07 (sonda-de-jira-acotada) — con un issue en la busqueda, issue.read sale de /issue."""
    raiz = _proyecto()
    transporte = TransporteJql()
    r = _jira(raiz, transporte).estado()
    t.verdadero("E-07 (sonda) con 200 en /issue hay issue.read", "jira.issue.read" in r["capacidades"])
    t.verdadero("E-07 (sonda) se pidio el issue de la busqueda",
                any("/rest/api/3/issue/APPLICDCON-1" in u for u, _, _ in transporte.llamadas))
    r = _jira(raiz, TransporteJql(issue=(403, "no"), permisos=(200, PERMISO_SI))).estado()
    t.verdadero("E-07 (sonda) con 403 en /issue no hay issue.read aunque la busqueda ande",
                "jira.issue.read" not in r["capacidades"] and "jira.issue.search" in r["capacidades"])


def test_sonda_e08_e09_issue_read_con_la_busqueda_rota(t):
    """E-08 y E-09 (sonda-de-jira-acotada) — la busqueda rota no se lleva puesta la lectura."""
    raiz = _proyecto()
    rota = (400, json.dumps({"errorMessages": ["otra politica"]}))
    r = _jira(raiz, TransporteJql(busqueda_acotada=rota)).estado()
    t.verdadero("E-08 (sonda) issue.read por el permiso", "jira.issue.read" in r["capacidades"])
    t.verdadero("E-08 (sonda) y sin busqueda", "jira.issue.search" not in r["capacidades"])
    for nombre, permisos in (("false", (200, PERMISO_NO)), ("403", (403, "no")),
                             ("sin JSON", (200, "no es json"))):
        r = _jira(raiz, TransporteJql(busqueda_acotada=rota, permisos=permisos)).estado()
        t.verdadero("E-09 (sonda) permisos %s: sin issue.read" % nombre,
                    "jira.issue.read" not in r["capacidades"])
        t.verdadero("E-09 (sonda) permisos %s: con su linea de diagnostico" % nombre,
                    any(x.startswith("jira.issue.read") for x in r["diagnostico"]))


def test_sonda_e10_el_diagnostico_no_fuga(t):
    """E-10 (sonda-de-jira-acotada) — token, credencial y usuario redactados; tope; sin JSON."""
    import base64
    raiz = _proyecto()
    usuario = "alguien@buenosaires.gob.ar"
    credencial = base64.b64encode(("%s:%s" % (usuario, TOKEN)).encode()).decode()
    traidor = json.dumps({"errorMessages": [
        "token %s rechazado" % TOKEN, "Basic %s no sirve" % credencial,
        "el usuario %s no puede" % usuario, "x" * 900]})
    r = _jira(raiz, TransporteJql(busqueda_acotada=(400, traidor))).estado()
    todo = json.dumps(r, ensure_ascii=False)
    for nombre, valor in (("token", TOKEN), ("credencial", credencial), ("usuario", usuario)):
        t.no_contiene("E-10 (sonda) sin %s" % nombre, valor, todo)
    linea = [x for x in r["diagnostico"] if x.startswith("jira.issue.search")][0]
    t.contiene("E-10 (sonda) se ve que se redacto", "[redactado]", linea)
    t.verdadero("E-10 (sonda) como mucho tres mensajes", "x" * 50 not in linea)
    for m in linea.split(": ", 2)[-1].split(" | "):
        t.verdadero("E-10 (sonda) ningun mensaje pasa de 200", len(m) <= 200)
    # El tope de 200 con el mensaje largo ADENTRO de los tres primeros. Con el largo cuarto, el
    # tope de tres lo descartaba antes de recortarlo y un tope de un millon pasaba verde (lo
    # encontro el refutador).
    largo = json.dumps({"errorMessages": ["y" * 900, "corto"]})
    r = _jira(raiz, TransporteJql(busqueda_acotada=(400, largo))).estado()
    linea = [x for x in r["diagnostico"] if x.startswith("jira.issue.search")][0]
    mensajes = linea.split("(400): ", 1)[1].split(" | ")
    t.igual("E-10 (sonda) el largo se recorta a 200 exactos", 200, len(mensajes[0]))
    t.igual("E-10 (sonda) y el corto queda entero", "corto", mensajes[1])
    r = _jira(raiz, TransporteJql(busqueda_acotada=(400, "<html>no</html>"))).estado()
    linea = [x for x in r["diagnostico"] if x.startswith("jira.issue.search")][0]
    t.verdadero("E-10 (sonda) sin JSON queda el texto fijo", linea.endswith("(400)."))
    t.no_contiene("E-10 (sonda) y nada del cuerpo", "html", linea)


def test_sonda_e11_estado_muestra_el_diagnostico(t):
    """E-11 (sonda-de-jira-acotada) — `estado` dice por que falta cada capacidad."""
    raiz = _proyecto("JIRA_TOKEN=%s\n" % TOKEN)
    _lock(raiz)
    _config(raiz, {"jira": {"enabled": True, "baseUrl": "https://ejemplo.atlassian.net",
                            "usuario": "a@b.gob.ar"},
                   "gitlab": {"enabled": False, "baseUrl": ""}})
    transporte = TransporteJql(busqueda_acotada=(400, json.dumps(
        {"errorMessages": [JQL_ILIMITADA]})), permisos=(200, PERMISO_NO))
    codigo, salida, _ = _correr_cli(["estado", "--proyecto", raiz], transporte)
    t.igual("E-11 (sonda) estado sale 0", 0, codigo)
    t.contiene("E-11 (sonda) la busqueda, con su motivo",
               "sin jira.issue.search: Jira Cloud rechazo la busqueda de prueba (400)", salida)
    t.contiene("E-11 (sonda) la lectura, con el suyo",
               "sin jira.issue.read: Jira Cloud dice que el token no tiene el permiso", salida)
    # Abajo de Jira Cloud y antes de GitLab: la posicion es parte del escenario.
    i_jira, i_gitlab = salida.find("Jira Cloud"), salida.find("GitLab")
    posiciones = [salida.find("sin jira.issue.search"), salida.find("sin jira.issue.read")]
    t.verdadero("E-11 (sonda) las lineas van abajo de Jira Cloud y antes de GitLab",
                i_jira != -1 and i_gitlab != -1
                and all(i_jira < p < i_gitlab for p in posiciones))


def test_sonda_e12_buscar_no_sale_con_una_jql_ilimitada(t):
    """E-12 (sonda-de-jira-acotada) — sin restriccion no hay llamada, hay JQL_UNBOUNDED."""
    raiz = _proyecto()
    for jql in ("order by created DESC", "", "   ", " ORDER BY key", None):
        transporte = TransporteJql()
        respuesta = _jira(raiz, transporte).buscar(jql)
        t.igual("E-12 (sonda) %r: sin llamadas" % (jql,), [], transporte.llamadas)
        t.igual("E-12 (sonda) %r: JQL_UNBOUNDED" % (jql,), "JQL_UNBOUNDED", respuesta.error)
        t.verdadero("E-12 (sonda) %r: no es ok" % (jql,), not respuesta.ok)


def test_sonda_e13_la_jql_de_la_ficha_esta_acotada(t):
    """E-13 (sonda-de-jira-acotada) — la unica JQL que arma contexto/ tiene restriccion."""
    from contexto import comun as c_comun
    from contexto import proyecto as c_proyecto

    class JiraQueAnota(object):
        def __init__(self):
            self.jqls = []

        def buscar(self, jql, maximo=10):
            self.jqls.append(jql)
            return httpmin.Respuesta(200, '{"issues":[]}')

    jira = JiraQueAnota()
    acumulador = c_comun.Acumulador({"jira.issue.search": "ENABLED", "jira.issue.read": "ENABLED"})
    c_proyecto.resolver(jira, {"project": {"key": "APPLICDCON", "name": "x"}}, {}, {}, acumulador)
    t.igual("E-13 (sonda) contexto busco una vez", 1, len(jira.jqls))
    t.verdadero("E-13 (sonda) y la JQL esta acotada",
                all(re.split(r"(?i)\border\s+by\b", j, 1)[0].strip() for j in jira.jqls))
    fuentes = [p for p in (BIN / "contexto").glob("*.py")]
    llamadas = [p.name for p in fuentes if ".buscar(" in p.read_text(encoding="utf-8")]
    t.igual("E-13 (sonda) proyecto.py es el unico de contexto/ que busca", ["proyecto.py"], llamadas)


def test_sonda_e14_la_corrida_real(t):
    """E-14 (sonda-de-jira-acotada) — la tabla del 25-09-2026: quedan las tres capacidades."""
    raiz = _proyecto()
    transporte = TransporteJql(busqueda_acotada=(200, ISSUE), viejo=(410, "gone"),
                               issue=(200, "{}"), adjuntos=(200, "{}"))
    r = _jira(raiz, transporte).estado()
    t.igual("E-14 (sonda) AVAILABLE", "AVAILABLE", r["estado"])
    t.igual("E-14 (sonda) las tres", ["jira.attachment.read", "jira.issue.read",
                                      "jira.issue.search"], r["capacidades"])
    t.igual("E-14 (sonda) sin diagnostico", [], r["diagnostico"])


# -- docs/cambios/adjuntos-de-jira-redirigidos/spec.md -------------------------
#
# El transporte de bytes de abajo devuelve cabeceras, como el real, y anota los headers de
# CADA pedido: el escenario central es que la credencial no llegue al segundo.
CONTENT = "https://ejemplo.atlassian.net/rest/api/3/attachment/content/10001"
FIRMADA = "https://api.media.atlassian.com/file/abc/binary?token=FIRMA-SECRETA-123&client=x"


class BytesConCabeceras(object):
    """Contesta por URL exacta: (codigo, bytes, cabeceras). Anota url y headers."""

    def __init__(self, por_url, tres=True):
        self.por_url = por_url
        self.tres = tres
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append((url, dict(headers)))
        codigo, datos, cabeceras = self.por_url.get(url, (404, b"", {}))
        return (codigo, datos, cabeceras) if self.tres else (codigo, datos)


def _jira_bytes(raiz, bytes_):
    jira = _jira(raiz, Transporte({}))
    jira.transporte_bytes = bytes_
    return jira


def _redirige(codigo=303, a=FIRMADA, datos=b"%PDF-1.7 original"):
    return BytesConCabeceras({CONTENT: (codigo, b"", {"Location": a}),
                              urllib.parse.urljoin(CONTENT, a): (200, datos, {})})


def test_adj_e01_e02_sigue_un_salto_sin_credencial(t):
    """E-01 y E-02 (adjuntos-de-jira-redirigidos) — 301/302/303/307/308 a https."""
    raiz = _proyecto()
    for codigo in (303, 301, 302, 307, 308):
        bytes_ = _redirige(codigo)
        destino = os.path.join(raiz, "bajado-%d.pdf" % codigo)
        vuelta = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, destino)
        ide = "E-01" if codigo == 303 else "E-02"
        t.igual("%s (adjuntos) %d: ok" % (ide, codigo), True, vuelta[0])
        t.igual("%s (adjuntos) %d: dos pedidos" % (ide, codigo), 2, len(bytes_.llamadas))
        t.igual("%s (adjuntos) %d: el segundo va a la URL firmada" % (ide, codigo),
                FIRMADA, bytes_.llamadas[1][0])
        t.verdadero("%s (adjuntos) %d: el primero SI lleva Authorization" % (ide, codigo),
                    "Authorization" in bytes_.llamadas[0][1])
        t.verdadero("%s (adjuntos) %d: el segundo NO lleva Authorization" % (ide, codigo),
                    "Authorization" not in bytes_.llamadas[1][1])
        t.igual("%s (adjuntos) %d: el segundo no lleva ningun header" % (ide, codigo),
                {}, bytes_.llamadas[1][1])
        t.no_contiene("%s (adjuntos) %d: ni el token en ningun lado del segundo" % (ide, codigo),
                      TOKEN, json.dumps(bytes_.llamadas[1]))
        with open(destino, "rb") as f:
            t.igual("%s (adjuntos) %d: el archivo son los bytes del segundo" % (ide, codigo),
                    b"%PDF-1.7 original", f.read())


def test_adj_e03_a_http_no(t):
    """E-03 (adjuntos-de-jira-redirigidos) — 303 a http: ni segundo pedido ni archivo."""
    raiz = _proyecto()
    bytes_ = _redirige(a="http://api.media.atlassian.com/file/abc/binary?token=X")
    destino = os.path.join(raiz, "no.pdf")
    ok, _, motivo = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, destino)
    t.igual("E-03 (adjuntos) no ok", False, ok)
    t.igual("E-03 (adjuntos) un solo pedido", 1, len(bytes_.llamadas))
    t.verdadero("E-03 (adjuntos) sin archivo", not os.path.exists(destino))
    t.contiene("E-03 (adjuntos) el motivo dice que no es https", "no es https", motivo)


def test_adj_e04_dos_saltos_no(t):
    """E-04 (adjuntos-de-jira-redirigidos) — el segundo contesta otro 3xx: se corta ahi."""
    raiz = _proyecto()
    otra = "https://tercero.example/x"
    bytes_ = BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}),
                                FIRMADA: (302, b"", {"Location": otra}),
                                otra: (200, b"no deberia", {})})
    destino = os.path.join(raiz, "no.pdf")
    ok, _, motivo = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, destino)
    t.igual("E-04 (adjuntos) no ok", False, ok)
    t.igual("E-04 (adjuntos) sin tercer pedido", 2, len(bytes_.llamadas))
    t.contiene("E-04 (adjuntos) el motivo dice mas de una", "mas de una redireccion", motivo)
    t.verdadero("E-04 (adjuntos) sin archivo", not os.path.exists(destino))


def test_adj_e05_sin_location_no(t):
    """E-05 (adjuntos-de-jira-redirigidos) — sin Location, o de un transporte de dos."""
    raiz = _proyecto()
    for nombre, bytes_ in (("sin Location", BytesConCabeceras({CONTENT: (303, b"", {})})),
                           ("transporte de dos", BytesConCabeceras(
                               {CONTENT: (303, b"", {"Location": FIRMADA})}, tres=False))):
        ok, _, motivo = _jira_bytes(raiz, bytes_).bajar_adjunto(
            CONTENT, os.path.join(raiz, "no.pdf"))
        t.igual("E-05 (adjuntos) %s: no ok" % nombre, False, ok)
        t.igual("E-05 (adjuntos) %s: sin segundo pedido" % nombre, 1, len(bytes_.llamadas))
        t.verdadero("E-05 (adjuntos) %s: con motivo" % nombre, bool(motivo))


def test_adj_e06_location_relativo(t):
    """E-06 (adjuntos-de-jira-redirigidos) — relativo: contra la URL original, sin credencial."""
    raiz = _proyecto()
    bytes_ = _redirige(a="/media/firmada?token=Y")
    ok, _, _ = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, os.path.join(raiz, "r.pdf"))
    t.igual("E-06 (adjuntos) ok", True, ok)
    t.igual("E-06 (adjuntos) resuelto contra el host original",
            "https://ejemplo.atlassian.net/media/firmada?token=Y", bytes_.llamadas[1][0])
    t.verdadero("E-06 (adjuntos) sin Authorization", "Authorization" not in bytes_.llamadas[1][1])


def test_adj_e07_la_api_sigue_sin_redirecciones(t):
    """E-07 (adjuntos-de-jira-redirigidos) — pedir no sigue: una llamada y CONNECTION_FAILED."""
    raiz = _proyecto()
    transporte = Transporte({"myself": (302, "")})
    resultado = _jira(raiz, transporte).validar_conexion()
    t.igual("E-07 (adjuntos) CONNECTION_FAILED", "CONNECTION_FAILED", resultado.estado)
    t.igual("E-07 (adjuntos) una sola llamada", 1, len(transporte.llamadas))
    manejadores = [type(h) for h in httpmin._abridor().handlers]
    t.verdadero("E-07 (adjuntos) el abridor real no redirige",
                httpmin._SinRedirecciones in manejadores)


def test_adj_e08_el_tope_vale_para_los_dos(t):
    """E-08 (adjuntos-de-jira-redirigidos) — de mas, redirigido o directo: falla, nada escrito."""
    raiz = _proyecto()
    tope = httpmin.MAXIMO_ADJUNTO
    grande = b"x" * (tope + 1)
    for nombre, bytes_ in (("redirigido", _redirige(datos=grande)),
                           ("directo", BytesConCabeceras({CONTENT: (200, grande, {})}))):
        destino = os.path.join(raiz, "grande-%s.pdf" % nombre)
        ok, _, motivo = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, destino)
        t.igual("E-08 (adjuntos) %s: no ok" % nombre, False, ok)
        t.verdadero("E-08 (adjuntos) %s: nada escrito, ni truncado" % nombre,
                    not os.path.exists(destino))
        t.contiene("E-08 (adjuntos) %s: el motivo es el tope" % nombre, "tope", motivo)
    justo = BytesConCabeceras({CONTENT: (200, b"y" * tope, {})})
    t.igual("E-08 (adjuntos) justo el tope si entra", True, _jira_bytes(raiz, justo).bajar_adjunto(
        CONTENT, os.path.join(raiz, "justo.pdf"))[0])


def test_adj_e09_el_motivo_llega_a_fuentes(t):
    """E-09 (adjuntos-de-jira-redirigidos) — la evidencia de la fuente dice por que."""
    from integraciones import fuentes as int_fuentes
    from orquestacion import registro_fuentes as rf
    raiz = _proyecto()
    entrada = [e for e in rf.gestionadas(rf.cargar()) if e["id"] == "ES0902"][0]
    adjunto = {"id": "10001", "filename": "ES0902 - Estandar de Seguridad V6.2.pdf",
               "size": 10, "created": "2026-09-25T10:00:00.000+0000", "content": CONTENT}
    bytes_ = _redirige(a="http://api.media.atlassian.com/file/abc/binary?token=FIRMA-SECRETA-123")
    jira = _jira_bytes(raiz, bytes_)
    obs = int_fuentes.observar([dict(entrada, sha256="a" * 64)], [adjunto], {}, jira.bajar_adjunto,
                               os.path.join(raiz, "descargas"))
    evidencia = " | ".join(obs[0]["evidence"])
    t.contiene("E-09 (adjuntos) dice que no se pudo bajar, con el motivo",
               "el documento no se pudo bajar: la redireccion apunta a una URL que no es https",
               evidencia)
    t.no_contiene("E-09 (adjuntos) sin la firma", "FIRMA-SECRETA-123", evidencia)


def test_adj_e10_el_motivo_llega_al_contexto(t):
    """E-10 (adjuntos-de-jira-redirigidos) — el faltante del adjunto dice por que."""
    from contexto import comun as c_comun
    from contexto import documentos as c_documentos
    raiz = _proyecto()
    bytes_ = BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}),
                                FIRMADA: (403, b"", {})})
    jira = _jira_bytes(raiz, bytes_)
    acumulador = c_comun.Acumulador({"jira.attachment.read": "ENABLED"})
    campos = {"attachment": [{"id": "10001", "filename": "Ficha.pdf", "size": 10,
                              "mimeType": "application/pdf", "created": "2026-09-25T10:00:00",
                              "content": CONTENT}]}
    from contexto import limpieza as c_limpieza
    c_documentos.resolver(jira, {}, campos, c_limpieza.cargar_catalogo(), {}, acumulador,
                          os.path.join(raiz, "docs"), ejecutar=lambda a: (1, ""))
    faltas = json.dumps(acumulador.__dict__, ensure_ascii=False, default=str)
    t.contiene("E-10 (adjuntos) dice que no se pudo bajar, con el motivo",
               "no se pudo bajar el adjunto Ficha.pdf: el servidor contesto 403", faltas)
    t.contiene("E-10 (adjuntos) con el host del salto", "api.media.atlassian.com", faltas)
    t.no_contiene("E-10 (adjuntos) sin la firma", "FIRMA-SECRETA-123", faltas)


def test_adj_e11_ninguna_url_firmada_en_los_motivos(t):
    """E-11 (adjuntos-de-jira-redirigidos) — como mucho el host, nunca camino ni query."""
    raiz = _proyecto()
    casos = (
        BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}), FIRMADA: (500, b"", {})}),
        BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}),
                           FIRMADA: (302, b"", {"Location": FIRMADA + "&otra=1"})}),
        _redirige(a=FIRMADA.replace("https", "http")),
        _redirige(datos=b"x" * (httpmin.MAXIMO_ADJUNTO + 1)),
    )
    for i, bytes_ in enumerate(casos):
        _, _, motivo = _jira_bytes(raiz, bytes_).bajar_adjunto(CONTENT, os.path.join(raiz, "n"))
        for pedazo in ("FIRMA-SECRETA-123", "/file/abc/binary", "token=", "?"):
            t.no_contiene("E-11 (adjuntos) caso %d: sin %s" % (i, pedazo), pedazo, motivo)


class _ManejadorDeBytes(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/redirige"):
            self.send_response(303)
            self.send_header("Location", "https://api.media.atlassian.com/file/x?token=T")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        cuerpo = b"z" * (httpmin.MAXIMO_ADJUNTO + 10)
        self.send_response(200)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


def test_adj_e12_el_transporte_real(t):
    """E-12 (adjuntos-de-jira-redirigidos) — urllib no sigue el 303 y trae el Location; y lee
    un byte de mas que el tope, para que el tope se pueda ver."""
    viejo = httpmin.MAXIMO_ADJUNTO
    httpmin.MAXIMO_ADJUNTO = 1000
    servidor = HTTPServer(("127.0.0.1", 0), _ManejadorDeBytes)
    hilo = threading.Thread(target=servidor.serve_forever)
    hilo.daemon = True
    hilo.start()
    try:
        base = "http://127.0.0.1:%d" % servidor.server_address[1]
        codigo, datos, cabeceras = httpmin.transporte_bytes_urllib(base + "/redirige", {}, 5)
        t.igual("E-12 (adjuntos) el 303 vuelve como 303", 303, codigo)
        t.igual("E-12 (adjuntos) con su Location",
                "https://api.media.atlassian.com/file/x?token=T", cabeceras.get("Location"))
        codigo, datos, _ = httpmin.transporte_bytes_urllib(base + "/grande", {}, 5)
        t.igual("E-12 (adjuntos) lee el tope mas uno", 1001, len(datos))
        r = httpmin.pedir_bytes(base + "/grande", {}, 5)
        t.igual("E-12 (adjuntos) y pedir_bytes lo rechaza por tope", "ATTACHMENT_TOO_LARGE", r.error)
    finally:
        httpmin.MAXIMO_ADJUNTO = viejo
        servidor.shutdown()
        servidor.server_close()



class _ManejadorQueRedirige(BaseHTTPRequestHandler):
    pedidos = []

    def do_GET(self):
        _ManejadorQueRedirige.pedidos.append(self.path)
        if self.path.startswith("/api"):
            self.send_response(302)
            self.send_header("Location", "/otro-lado")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


def test_adj_e07b_transporte_urllib_no_sigue_de_verdad(t):
    """E-07 (adjuntos-de-jira-redirigidos) — contra un servidor local que redirige: urllib
    devuelve el 302 y el servidor ve UN pedido. El abridor sin redirecciones tiene que estar
    en uso, no solo existir (lo pidio el refutador)."""
    _ManejadorQueRedirige.pedidos = []
    servidor = HTTPServer(("127.0.0.1", 0), _ManejadorQueRedirige)
    hilo = threading.Thread(target=servidor.serve_forever)
    hilo.daemon = True
    hilo.start()
    try:
        base = "http://127.0.0.1:%d" % servidor.server_address[1]
        r = httpmin.pedir(base + "/api/myself", {"Authorization": "Basic x"}, 5)
        t.igual("E-07 (adjuntos) pedir devuelve el 302", 302, r.codigo)
        t.igual("E-07 (adjuntos) y el servidor vio un solo pedido", ["/api/myself"],
                _ManejadorQueRedirige.pedidos)
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_adj_e11b_nada_escrito_lleva_la_url_firmada(t):
    """E-11 (adjuntos-de-jira-redirigidos) — lo que se ESCRIBE: el estado de fuentes y la
    salida del contexto, despues de una descarga fallida (lo pidio el refutador)."""
    from contexto import comun as c_comun
    from contexto import documentos as c_documentos
    from contexto import limpieza as c_limpieza
    from integraciones import fuentes as int_fuentes
    from orquestacion import frescura as c_frescura
    from orquestacion import registro_fuentes as rf
    raiz = _proyecto()
    fallas = (
        BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}), FIRMADA: (500, b"", {})}),
        _redirige(a=FIRMADA.replace("https", "http")),
        BytesConCabeceras({CONTENT: (303, b"", {"Location": FIRMADA}),
                           FIRMADA: (302, b"", {"Location": FIRMADA + "&otra=1"})}),
    )
    entrada = [e for e in rf.gestionadas(rf.cargar()) if e["id"] == "ES0902"][0]
    adjunto = {"id": "10001", "filename": "ES0902 - Estandar de Seguridad V6.2.pdf",
               "size": 10, "created": "2026-09-25T10:00:00.000+0000", "content": CONTENT}
    for i, bytes_ in enumerate(fallas):
        jira = _jira_bytes(raiz, bytes_)
        obs = int_fuentes.observar([dict(entrada, sha256="a" * 64)], [adjunto], {},
                                   jira.bajar_adjunto, os.path.join(raiz, "d%d" % i))
        doc = c_frescura.documento([dict(entrada, sha256="a" * 64)], obs, {"reachable": True})
        ruta = os.path.join(raiz, "fuentes-%d.json" % i)
        c_frescura.escribir(doc, ruta)
        escrito = open(ruta, encoding="utf-8").read()
        acumulador = c_comun.Acumulador({"jira.attachment.read": "ENABLED"})
        campos = {"attachment": [{"id": "10001", "filename": "Ficha.pdf", "size": 10,
                                  "mimeType": "application/pdf",
                                  "created": "2026-09-25T10:00:00", "content": CONTENT}]}
        salida = c_documentos.resolver(jira, {}, campos, c_limpieza.cargar_catalogo(), {},
                                       acumulador, os.path.join(raiz, "c%d" % i),
                                       ejecutar=lambda a: (1, ""))
        contexto = json.dumps([salida, acumulador.__dict__], ensure_ascii=False, default=str)
        for pedazo in ("FIRMA-SECRETA-123", "/file/abc/binary", "token="):
            t.no_contiene("E-11 (adjuntos) estado de fuentes %d sin %s" % (i, pedazo), pedazo,
                          escrito)
            t.no_contiene("E-11 (adjuntos) contexto %d sin %s" % (i, pedazo), pedazo, contexto)


def test_adj_e14_una_url_invalida_no_revienta_ni_fuga(t):
    """E-14 (adjuntos-de-jira-redirigidos) — un Location con espacio o control: http.client
    levanta InvalidURL con la URL en el mensaje. Tiene que volver como error, sin traceback y
    sin la query (lo encontro el refutador)."""
    raiz = _proyecto()
    for rara in ("https://media.example/file x?token=SECRETO-DEL-SALTO",
                 "https://media.example/file\x01?token=SECRETO-DEL-SALTO"):
        bytes_ = BytesConCabeceras({CONTENT: (303, b"", {"Location": rara})})

        def real_para_el_salto(url, headers, timeout, _b=bytes_):
            if url == CONTENT:
                return _b(url, headers, timeout)
            return httpmin.transporte_bytes_urllib(url, headers, timeout)

        jira = _jira_bytes(raiz, real_para_el_salto)
        try:
            ok, _, motivo = jira.bajar_adjunto(CONTENT, os.path.join(raiz, "rara.pdf"))
            levanto = None
        except Exception as e:                # noqa: BLE001
            ok, motivo, levanto = False, "", repr(e)
        t.igual("E-14 (adjuntos) %r: no levanta" % rara[-20:], None, levanto)
        t.igual("E-14 (adjuntos) %r: no ok" % rara[-20:], False, ok)
        t.no_contiene("E-14 (adjuntos) %r: sin el token en el motivo" % rara[-20:],
                      "SECRETO-DEL-SALTO", motivo)
        t.contiene("E-14 (adjuntos) %r: dice que la URL no es valida" % rara[-20:],
                   "no es valida", motivo)
    r = httpmin.pedir("https://ejemplo/api x?token=SECRETO", {}, 1)
    t.igual("E-14 (adjuntos) pedir tampoco levanta con una URL invalida", "url", r.error)
