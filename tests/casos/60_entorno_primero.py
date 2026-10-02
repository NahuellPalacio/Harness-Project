# La configuracion de las integraciones sale del .env: el resolvedor, la proyeccion, la CLI,
# la bienvenida y la frontera del modelo.
#
# Spec: docs/cambios/entorno-primero/spec.md. E-nn es ENV-0nn del paquete. Cada test nombra
# su escenario. Los del instalador -E-30, E-61, E-63 a E-65- van en
# tests/casos/60-entorno-instalador.ps1; E-71 es la corrida entera.
#
# Ningun test sale a la red: el transporte HTTP se inyecta. Los tokens de las fugas no tienen
# forma de credencial -el detector no los reconoce- salvo el de E-47, que se arma por partes:
# un fuente con un literal que dispara el propio detector no se puede editar donde el harness
# esta instalado.
import base64
import builtins
import getpass
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CASOS = RAIZ / "tests" / "casos"
sys.path.insert(0, str(BIN))

from integraciones import base                          # noqa: E402
from integraciones import entorno                       # noqa: E402
from integraciones.almacen import AlmacenSecretos       # noqa: E402
from integraciones.config import ClaveProhibida, ConfigIntegraciones  # noqa: E402
from integraciones.gitlab import IntegracionGitLab      # noqa: E402
from integraciones.jira import IntegracionJira          # noqa: E402

CLI = BIN / "dev-harness.py"
CONTRATO = RAIZ / "harnesses" / "desarrollo" / "reglas" / "integration-environment-contract.json"
SCHEMA_CONTRATO = RAIZ / "comun" / "schemas" / "integration-environment-contract.schema.json"
ENV_EXAMPLE = RAIZ / "harnesses" / "desarrollo" / ".env.example"
DENY = RAIZ / "comun" / "settings" / "permissions.deny.json"
ANTES = "426ebeb"

TOKEN_JIRA = "un-token-de-jira-que-no-tiene-que-aparecer"
TOKEN_GITLAB = "un-token-de-gitlab-que-no-tiene-que-aparecer"
URL_JIRA = "https://entorno-primero.atlassian.net"
USUARIO = "persona.de.prueba@buenosaires.gob.ar"
URL_GITLAB = "https://gitlab.entorno-primero.gob.ar"
AJENO = "valor-ajeno-que-nadie-copia"

ENV_COMPLETO = (
    "# un comentario de la persona\n"
    "HARNESS_JIRA_ENABLED=true\n"
    "JIRA_BASE_URL=%s\n"
    'JIRA_USER="%s"\n'
    "JIRA_TOKEN=%s\n"
    "\n"
    "HARNESS_GITLAB_ENABLED=on\n"
    "GITLAB_BASE_URL=%s\n"
    "GITLAB_TOKEN='%s'\n"
    "OTRA_VARIABLE=%s\n") % (URL_JIRA, USUARIO, TOKEN_JIRA, URL_GITLAB, TOKEN_GITLAB, AJENO)

TODAS = ("jira.attachment.read", "jira.issue.read", "jira.issue.search", "gitlab.branch.read",
         "gitlab.merge_request.read", "gitlab.project.read", "gitlab.repository.read")
VARIABLES = ("HARNESS_JIRA_ENABLED", "JIRA_BASE_URL", "JIRA_USER", "JIRA_TOKEN",
             "HARNESS_GITLAB_ENABLED", "GITLAB_BASE_URL", "GITLAB_PROJECT", "GITLAB_TOKEN")


# -- andamios ------------------------------------------------------------------

def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _proyecto(env=ENV_COMPLETO, proyeccion=None, lock=True):
    raiz = tempfile.mkdtemp(prefix="harness-entorno-")
    os.makedirs(os.path.join(raiz, ".claude"))
    if env is not None:
        with io.open(os.path.join(raiz, ".env"), "w", encoding="utf-8", newline="") as f:
            f.write(env)
    if proyeccion is not None:
        with io.open(_ruta_proyeccion(raiz), "w", encoding="utf-8") as f:
            f.write(json.dumps(proyeccion))
    if lock:
        with io.open(os.path.join(raiz, ".claude", "harness.lock.json"), "w",
                     encoding="utf-8") as f:
            f.write(json.dumps({"version": "0.26.0", "harness": ["comun", "desarrollo"],
                                "instalado": "2026-09-28 10:00:00", "archivos": []}))
    return raiz


def _ruta_proyeccion(raiz):
    return os.path.join(raiz, ".claude", "harness.integraciones.json")


def _leer(ruta):
    with io.open(ruta, encoding="utf-8") as f:
        return f.read()


def _bytes(ruta):
    with open(ruta, "rb") as f:
        return f.read()


def _contrato():
    return entorno.cargar_contrato(str(CONTRATO))


def _resolver(raiz, entorno_proceso=None, contrato=None):
    return entorno.resolver(contrato or _contrato(), os.path.join(raiz, ".env"),
                            _ruta_proyeccion(raiz), {} if entorno_proceso is None
                            else entorno_proceso)


def _variable(resolucion, integ, nombre):
    return [v for v in resolucion.integracion(integ).variables if v.nombre == nombre][0]


class Transporte(object):
    """Jira y GitLab falsos. Contestan por fragmento de URL y guardan cada llamada."""

    def __init__(self, respuestas=None, por_defecto=(404, "")):
        self.respuestas = respuestas if respuestas is not None else _TODO_OK
        self.por_defecto = por_defecto
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append((url, dict(headers)))
        for fragmento, respuesta in self.respuestas.items():
            if fragmento in url:
                return respuesta
        return self.por_defecto

    def urls(self, host=""):
        return [u for u, _ in self.llamadas if host in u]


_TODO_OK = {
    "/rest/api/3/myself": (200, "{}"), "search/jql": (200, '{"issues":[]}'),
    "attachment/meta": (200, "{}"),
    "mypermissions": (200, '{"permissions":{"BROWSE_PROJECTS":{"havePermission":true}}}'),
    "/api/v4/user": (200, "{}"),
    "personal_access_tokens/self": (200, '{"scopes":["read_api"]}'),
}


def _cli(argv, transporte=None, proceso=None):
    """Corre dev-harness.py en proceso. (codigo, stdout, stderr, llamadas a input/getpass).

    Las variables del contrato se sacan del entorno real mientras corre: una maquina con
    JIRA_BASE_URL exportada no puede cambiar lo que prueba la suite. `proceso` es lo que el
    test pone en el entorno del proceso.
    """
    modulo = _cargar("dev_harness_60", CLI)
    salida, error = io.StringIO(), io.StringIO()
    pedidos = []
    previos = (sys.stdout, sys.stderr, sys.stdin, builtins.input, getpass.getpass)
    guardado = dict((k, os.environ[k]) for k in VARIABLES if k in os.environ)
    for k in VARIABLES:
        os.environ.pop(k, None)
    for k, v in (proceso or {}).items():
        os.environ[k] = v
    sys.stdout, sys.stderr, sys.stdin = salida, error, io.StringIO("")

    def _pedir(*a, **k):
        pedidos.append(a)
        raise EOFError("la CLI no puede preguntar")
    builtins.input = _pedir
    getpass.getpass = _pedir
    try:
        codigo = modulo.main(argv, transporte)
    finally:
        (sys.stdout, sys.stderr, sys.stdin, builtins.input, getpass.getpass) = previos
        for k in list(proceso or {}) + list(VARIABLES):
            os.environ.pop(k, None)
        os.environ.update(guardado)
    return codigo, salida.getvalue(), error.getvalue(), pedidos


def _capacidades(raiz):
    return json.loads(_leer(os.path.join(raiz, ".claude", "harness.capacidades.json")))


def _todo_lo_de_claude(raiz):
    """Todo el texto que quedo bajo .claude/, junto."""
    partes = []
    for carpeta, _, archivos in os.walk(os.path.join(raiz, ".claude")):
        for a in archivos:
            with open(os.path.join(carpeta, a), "rb") as f:
                partes.append(f.read().decode("utf-8", "replace"))
    return "\n".join(partes)


# -- E-01 a E-05 — lo que no se agrega -------------------------------------------

def test_e01_el_modo_es_environment_first(t):
    """E-01 — setup, estado y reconfigurar dicen ENVIRONMENT_FIRST, y el registro lo guarda."""
    for argv in (["setup"], ["estado"], ["reconfigurar", "jira"]):
        raiz = _proyecto()
        codigo, salida, _, _ = _cli(argv + ["--proyecto", raiz], Transporte())
        t.igual("E-01 %s sale 0" % argv[0], 0, codigo)
        t.contiene("E-01 %s dice el modo" % argv[0], "Modo de configuración: ENVIRONMENT_FIRST",
                   salida)
        t.igual("E-01 %s lo registra" % argv[0], "ENVIRONMENT_FIRST",
                _capacidades(raiz).get("configurationMode"))


def _del_arbol(commit, patron):
    """Lo de ese commit, menos lo de un harness cuyo directorio ya no existe: lo retiro
    docs/cambios/harness-unico/spec.md, y eso no es un agente ni una skill nuevos."""
    salida = subprocess.run(["git", "-C", str(RAIZ), "ls-tree", "-r", "--name-only", commit],
                            stdout=subprocess.PIPE, check=True).stdout.decode("utf-8")
    return sorted(l for l in salida.splitlines() if re.search(patron, l)
                  and not (l.startswith("harnesses/") and not (RAIZ / "/".join(l.split("/")[:2])).is_dir()))


def _del_disco(patron):
    salida = []
    for base_ in ("comun", "harnesses", ".claude"):
        for carpeta, _, archivos in os.walk(str(RAIZ / base_)):
            for a in archivos:
                rel = os.path.relpath(os.path.join(carpeta, a), str(RAIZ)).replace("\\", "/")
                if re.search(patron, rel):
                    salida.append(rel)
    return sorted(salida)


def test_e02_ningun_agente_nuevo(t):
    """E-02 — los agents/*.md de la fabrica son los mismos que en 426ebeb."""
    patron = r"(^|/)agents/[^/]+\.md$"
    t.igual("E-02 mismos agentes", _del_arbol(ANTES, patron), _del_disco(patron))


def test_e03_ninguna_skill_nueva(t):
    """E-03 — los skills/*/SKILL.md de la fabrica son los mismos que en 426ebeb."""
    patron = r"(^|/)skills/[^/]+/SKILL\.md$"
    t.igual("E-03 mismas skills", _del_arbol(ANTES, patron), _del_disco(patron))


def test_e04_valida_con_los_adapters_de_siempre(t):
    """E-04 — con el .env completo, el bootstrap pide /myself y /api/v4/user."""
    raiz = _proyecto()
    transporte = Transporte()
    codigo, _, _, _ = _cli(["estado", "--proyecto", raiz], transporte)
    t.igual("E-04 sale 0", 0, codigo)
    t.verdadero("E-04 Jira valida con /rest/api/3/myself",
                URL_JIRA + "/rest/api/3/myself" in transporte.urls())
    t.verdadero("E-04 GitLab valida con /api/v4/user",
                URL_GITLAB + "/api/v4/user" in transporte.urls())


def test_e05_soportada_no_es_disponible(t):
    """E-05 — Jira sin validar deja sus capacidades DISABLED, y figuran las siete."""
    raiz = _proyecto(ENV_COMPLETO.replace("HARNESS_JIRA_ENABLED=true", "HARNESS_JIRA_ENABLED=false"))
    _cli(["estado", "--proyecto", raiz], Transporte())
    capacidades = _capacidades(raiz)["capacidades"]
    t.igual("E-05 estan las siete", sorted(TODAS), sorted(capacidades))
    t.igual("E-05 jira DISABLED", "DISABLED", capacidades["jira.issue.read"])
    t.igual("E-05 gitlab ENABLED", "ENABLED", capacidades["gitlab.project.read"])


# -- E-06 a E-10 — de donde sale cada valor --------------------------------------

def test_e06_e07_jira_publico_del_env(t):
    """E-06, E-07 — JIRA_BASE_URL y JIRA_USER del .env llegan como baseUrl y usuario."""
    r = _resolver(_proyecto())
    t.igual("E-06 baseUrl", URL_JIRA, r.de("jira").get("baseUrl"))
    t.igual("E-06 fuente DOTENV", "DOTENV", _variable(r, "jira", "JIRA_BASE_URL").fuente)
    t.igual("E-07 usuario, sin las comillas", USUARIO, r.de("jira").get("usuario"))
    t.igual("E-07 fuente DOTENV", "DOTENV", _variable(r, "jira", "JIRA_USER").fuente)


class _AlmacenEspia(AlmacenSecretos):
    def __init__(self, ruta):
        AlmacenSecretos.__init__(self, ruta, {})
        self.pedidos = []

    def get(self, nombre):
        self.pedidos.append(nombre)
        return AlmacenSecretos.get(self, nombre)


def _sin_token(t, id_, r, token, clave):
    t.no_contiene("%s la configuracion del adapter no lleva el token" % id_, token,
                  json.dumps(r.de(clave)))
    t.no_contiene("%s ni una clave de token" % id_, "token", json.dumps(r.de(clave)).lower())
    t.no_contiene("%s ni el repr de la resolucion" % id_, token, repr(r))
    t.no_contiene("%s ni las variables" % id_, token,
                  json.dumps([v.como_dict() for v in r.integracion(clave).variables]))
    t.no_contiene("%s ni la proyeccion" % id_, token, entorno.texto_de(r.proyeccion()))


def test_e08_el_token_de_jira_sale_del_almacen(t):
    """E-08 — el adapter de Jira pide JIRA_TOKEN al almacen; el resolvedor no lo tiene."""
    raiz = _proyecto()
    r = _resolver(raiz)
    _sin_token(t, "E-08", r, TOKEN_JIRA, "jira")
    almacen = _AlmacenEspia(os.path.join(raiz, ".env"))
    jira = IntegracionJira(r.de("jira"), almacen, 5, None, variables=r.variables_de("jira"))
    cabecera = jira.cabeceras()["Authorization"]
    t.verdadero("E-08 lo pidio al almacen", "JIRA_TOKEN" in almacen.pedidos)
    t.igual("E-08 y es el del .env", "Basic " + base64.b64encode(
        ("%s:%s" % (USUARIO, TOKEN_JIRA)).encode("utf-8")).decode("ascii"), cabecera)


def test_e09_gitlab_publico_del_env(t):
    """E-09 — GITLAB_BASE_URL del .env llega al adapter de GitLab como baseUrl."""
    r = _resolver(_proyecto())
    gitlab = IntegracionGitLab(r.de("gitlab"), AlmacenSecretos("x", {}), 5)
    t.igual("E-09 baseUrl", URL_GITLAB, gitlab.base_url())


def test_e10_el_token_de_gitlab_sale_del_almacen(t):
    """E-10 — igual que E-08 para GITLAB_TOKEN."""
    raiz = _proyecto()
    r = _resolver(raiz)
    _sin_token(t, "E-10", r, TOKEN_GITLAB, "gitlab")
    almacen = _AlmacenEspia(os.path.join(raiz, ".env"))
    gitlab = IntegracionGitLab(r.de("gitlab"), almacen, 5)
    t.igual("E-10 el header lleva el del .env", TOKEN_GITLAB, gitlab.cabeceras()["PRIVATE-TOKEN"])
    t.verdadero("E-10 lo pidio al almacen", "GITLAB_TOKEN" in almacen.pedidos)


# -- E-11 a E-14 — la precedencia -------------------------------------------------

def test_e11_el_proceso_le_gana_al_env(t):
    """E-11 — gana el entorno del proceso, sin conflicto."""
    otra = "https://del-proceso.atlassian.net"
    r = _resolver(_proyecto(), {"JIRA_BASE_URL": otra})
    t.igual("E-11 gana el proceso", otra, r.de("jira")["baseUrl"])
    t.igual("E-11 fuente PROCESS_ENV", "PROCESS_ENV", _variable(r, "jira", "JIRA_BASE_URL").fuente)
    t.igual("E-11 no es conflicto", "", r.integracion("jira").codigo)
    # Y por la CLI, con el entorno real del proceso.
    raiz = _proyecto()
    transporte = Transporte()
    _cli(["estado", "--proyecto", raiz], transporte, proceso={"JIRA_BASE_URL": otra})
    t.verdadero("E-11 la CLI valida contra la del proceso", otra + "/rest/api/3/myself"
                in transporte.urls())


def test_e12_el_default_solo_sin_capas(t):
    """E-12 — enabled por default solo sin proceso, sin .env y sin el JSON viejo."""
    r = _resolver(_proyecto("JIRA_BASE_URL=%s\n" % URL_JIRA))
    t.igual("E-12 sin capas: default false", False, r.de("jira")["enabled"])
    t.igual("E-12 fuente SAFE_DEFAULT", "SAFE_DEFAULT", r.integracion("jira").fuente_habilitada)
    viejo = {"jira": {"enabled": True, "baseUrl": URL_JIRA, "usuario": USUARIO}}
    r = _resolver(_proyecto("", proyeccion=viejo))
    t.igual("E-12 con el JSON viejo: LEGACY", ("LEGACY", True),
            (r.integracion("jira").fuente_habilitada, r.de("jira")["enabled"]))
    r = _resolver(_proyecto("HARNESS_JIRA_ENABLED=false\n", proyeccion=viejo))
    t.igual("E-12 el .env le gana al JSON viejo", ("DOTENV", False),
            (r.integracion("jira").fuente_habilitada, r.de("jira")["enabled"]))
    r = _resolver(_proyecto("HARNESS_JIRA_ENABLED=false\n"), {"HARNESS_JIRA_ENABLED": "true"})
    t.igual("E-12 el proceso le gana a todos", ("PROCESS_ENV", True),
            (r.integracion("jira").fuente_habilitada, r.de("jira")["enabled"]))


def test_e13_no_se_inventa_nada(t):
    """E-13 — una variable que no esta en ninguna capa no aparece."""
    r = _resolver(_proyecto("HARNESS_JIRA_ENABLED=true\n"))
    t.igual("E-13 el adapter recibe solo enabled", {"enabled": True}, r.de("jira"))
    t.igual("E-13 y la proyeccion tambien", {"enabled": True}, r.proyeccion()["jira"])
    t.igual("E-13 y se dice que falta", ["JIRA_BASE_URL", "JIRA_USER", "JIRA_TOKEN"],
            r.integracion("jira").faltan)


def test_e14_vacio_y_placeholder_son_ausentes(t):
    """E-14 — un valor vacio, de espacios o <...> es ausente: bandera, publica y token."""
    r = _resolver(_proyecto("HARNESS_JIRA_ENABLED=<true-o-false>\nJIRA_BASE_URL=\n"
                            "JIRA_USER=   \nJIRA_TOKEN=<tu-api-token-de-jira>\n"))
    jira = r.integracion("jira")
    t.igual("E-14 la bandera placeholder es default", "SAFE_DEFAULT", jira.fuente_habilitada)
    t.igual("E-14 sin codigo de bandera invalida", "", jira.codigo)
    for nombre in ("JIRA_BASE_URL", "JIRA_USER", "JIRA_TOKEN"):
        t.igual("E-14 %s ausente" % nombre, False, _variable(r, "jira", nombre).presente)
    r = _resolver(_proyecto("HARNESS_JIRA_ENABLED=true\nJIRA_TOKEN=<tu-api-token-de-jira>\n"))
    t.verdadero("E-14 el token placeholder falta", "JIRA_TOKEN" in r.integracion("jira").faltan)


# -- E-15 a E-20 — las banderas ----------------------------------------------------

def test_e15_deshabilitada_no_sale_a_la_red(t):
    """E-15 — HARNESS_JIRA_ENABLED=false: NOT_CONFIGURED, sin faltantes y sin red."""
    raiz = _proyecto("HARNESS_JIRA_ENABLED=false\n")
    transporte = Transporte()
    _cli(["estado", "--proyecto", raiz], transporte)
    jira = _capacidades(raiz)["integraciones"]["jira"]
    t.igual("E-15 NOT_CONFIGURED", "NOT_CONFIGURED", jira["estado"])
    t.igual("E-15 sin faltantes", [], jira["faltan"])
    t.igual("E-15 sin red", [], transporte.urls("atlassian"))


def test_e16_completo_valida(t):
    """E-16 — con la bandera y las tres variables, Jira queda AVAILABLE."""
    raiz = _proyecto()
    _cli(["estado", "--proyecto", raiz], Transporte())
    t.igual("E-16 AVAILABLE", "AVAILABLE", _capacidades(raiz)["integraciones"]["jira"]["estado"])


def test_e17_e18_falta_una_variable(t):
    """E-17, E-18 — sin JIRA_USER: NOT_CONFIGURED sin red, y se nombra la variable."""
    raiz = _proyecto(re.sub(r'JIRA_USER=.*\n', "", ENV_COMPLETO))
    transporte = Transporte()
    codigo, salida, _, _ = _cli(["estado", "--proyecto", raiz], transporte)
    jira = _capacidades(raiz)["integraciones"]["jira"]
    t.igual("E-17 NOT_CONFIGURED", "NOT_CONFIGURED", jira["estado"])
    t.igual("E-17 sin red", [], transporte.urls("atlassian"))
    t.igual("E-18 el registro nombra la variable", ["JIRA_USER"], jira["faltan"])
    t.contiene("E-18 la salida la nombra", "Faltan: JIRA_USER", salida)
    t.contiene("E-18 y dice que hacer", "Completá las variables faltantes en el .env local.",
               jira["motivo"])


def test_e19_bandera_invalida(t):
    """E-19 — HARNESS_JIRA_ENABLED=quizas: ENV_ENABLED_FLAG_INVALID, sin red; GitLab sigue."""
    raiz = _proyecto(ENV_COMPLETO.replace("HARNESS_JIRA_ENABLED=true", "HARNESS_JIRA_ENABLED=quizas"))
    transporte = Transporte()
    codigo, salida, error, _ = _cli(["estado", "--proyecto", raiz], transporte)
    integ = _capacidades(raiz)["integraciones"]
    t.igual("E-19 sale 0", 0, codigo)
    t.igual("E-19 Jira NOT_CONFIGURED", "NOT_CONFIGURED", integ["jira"]["estado"])
    t.contiene("E-19 con el codigo", "ENV_ENABLED_FLAG_INVALID", integ["jira"]["motivo"])
    t.no_contiene("E-19 sin repetir el valor", "quizas", salida + error)
    t.igual("E-19 sin red a Jira", [], transporte.urls("atlassian"))
    t.igual("E-19 GitLab se resuelve igual", "AVAILABLE", integ["gitlab"]["estado"])


def test_e20_las_formas_del_booleano(t):
    """E-20 — las formas documentadas, sin distinguir mayusculas; el resto es invalido."""
    for texto in ("true", "TRUE", "1", "yes", "On"):
        t.igual("E-20 %s es verdadero" % texto, True, entorno.booleano(texto))
    for texto in ("false", "False", "0", "NO", "off"):
        t.igual("E-20 %s es falso" % texto, False, entorno.booleano(texto))
    for texto in ("si", "2", "enabled", "tru"):
        t.igual("E-20 %s es invalido" % texto, None, entorno.booleano(texto))


# -- E-21 a E-29 — la proyeccion -----------------------------------------------------

def _proyeccion_de(raiz):
    _cli(["estado", "--proyecto", raiz], Transporte())
    return _leer(_ruta_proyeccion(raiz))


def test_e21_a_e24_lo_que_lleva_y_lo_que_no(t):
    """E-21 a E-24 — base URL y usuario si; tokens no."""
    texto = _proyeccion_de(_proyecto())
    doc = json.loads(texto)
    t.igual("E-21 jira.baseUrl", URL_JIRA, doc["jira"]["baseUrl"])
    t.igual("E-21 jira.usuario", USUARIO, doc["jira"]["usuario"])
    t.no_contiene("E-22 sin JIRA_TOKEN", TOKEN_JIRA, texto)
    t.no_contiene("E-22 sin campo token", '"token"', texto)
    t.igual("E-23 gitlab.baseUrl", URL_GITLAB, doc["gitlab"]["baseUrl"])
    t.no_contiene("E-24 sin GITLAB_TOKEN", TOKEN_GITLAB, texto)


def _contrato_con(campo):
    doc = json.loads(_leer(str(CONTRATO)))
    doc["integrations"][0]["fields"].append(campo)
    return doc


def test_e25_un_secret_nunca_se_proyecta(t):
    """E-25 — un campo SECRET no se proyecta, aunque su nombre no parezca secreto."""
    contrato = _contrato_con({"name": "codigo", "env": "JIRA_CODIGO", "classification": "SECRET",
                              "requiredWhenEnabled": False, "legacyConfigKey": None})
    t.igual("E-25 el contrato es valido", [], entorno.validar_contrato(contrato))
    r = _resolver(_proyecto(ENV_COMPLETO + "JIRA_CODIGO=valor-del-codigo-oculto\n"),
                  contrato=contrato)
    texto = entorno.texto_de(r.proyeccion())
    t.no_contiene("E-25 sin el valor", "valor-del-codigo-oculto", texto)
    t.no_contiene("E-25 sin el campo", '"codigo"', texto)
    t.igual("E-25 pero se sabe que esta", True, _variable(r, "jira", "JIRA_CODIGO").presente)


def test_e26_la_heuristica_sigue_de_segunda_linea(t):
    """E-26 — un PUBLIC_CONFIG con forma de secreto no se proyecta; guardar sigue rechazando."""
    for campo in ({"name": "apiKey", "env": "JIRA_ALGO"}, {"name": "extra", "env": "JIRA_PASSWORD"}):
        campo.update({"classification": "PUBLIC_CONFIG", "requiredWhenEnabled": False,
                      "legacyConfigKey": None})
        contrato = _contrato_con(campo)
        r = _resolver(_proyecto(ENV_COMPLETO + "%s=valor-publico-sospechoso\n" % campo["env"]),
                      contrato=contrato)
        t.igual("E-26 %s rechazado" % campo["env"], "ENV_PUBLIC_PROJECTION_REJECTED_SECRET",
                r.integracion("jira").codigo)
        t.no_contiene("E-26 %s no se proyecta" % campo["env"], "valor-publico-sospechoso",
                      entorno.texto_de(r.proyeccion()))
    # Un valor publico que es el token, o una URL con credencial adentro.
    r = _resolver(_proyecto(ENV_COMPLETO.replace('JIRA_USER="%s"' % USUARIO,
                                                 "JIRA_USER=%s" % TOKEN_JIRA)))
    t.igual("E-26 un usuario igual al token", "ENV_PUBLIC_PROJECTION_REJECTED_SECRET",
            r.integracion("jira").codigo)
    t.no_contiene("E-26 y no se proyecta", TOKEN_JIRA, entorno.texto_de(r.proyeccion()))
    r = _resolver(_proyecto(ENV_COMPLETO.replace(URL_JIRA, "https://alguien:clave-en-url@x.net")))
    t.igual("E-26 una URL con credencial", "ENV_PUBLIC_PROJECTION_REJECTED_SECRET",
            r.integracion("jira").codigo)
    raiz = _proyecto()
    levanto = False
    try:
        ConfigIntegraciones(_ruta_proyeccion(raiz)).guardar("jira", {"token": "x"})
    except ClaveProhibida:
        levanto = True
    t.verdadero("E-26 ClaveProhibida sigue", levanto)
    levanto = ""
    try:
        entorno.escribir_proyeccion(_ruta_proyeccion(raiz), {"jira": {"apiToken": "x"}})
    except entorno.ErrorDeEntorno as e:
        levanto = e.codigo
    t.igual("E-26 la escritura de la proyeccion tambien rechaza",
            "ENV_PUBLIC_PROJECTION_REJECTED_SECRET", levanto)


def test_e27_una_proyeccion_vieja_no_le_gana_al_env(t):
    """E-27 — la base URL de una proyeccion generada no vuelve como fuente."""
    raiz = _proyecto()
    _proyeccion_de(raiz)
    doc = json.loads(_leer(_ruta_proyeccion(raiz)))
    doc["jira"]["baseUrl"] = "https://vieja.atlassian.net"
    with io.open(_ruta_proyeccion(raiz), "w", encoding="utf-8") as f:
        f.write(json.dumps(doc))
    t.igual("E-27 despues del bootstrap vale el .env", URL_JIRA,
            json.loads(_proyeccion_de(raiz))["jira"]["baseUrl"])
    # Y sin la variable en el .env, la proyeccion vieja no la completa.
    with io.open(os.path.join(raiz, ".env"), "w", encoding="utf-8") as f:
        f.write(re.sub(r"JIRA_BASE_URL=.*\n", "", ENV_COMPLETO))
    r = _resolver(raiz)
    t.verdadero("E-27 la generada no es fuente", "baseUrl" not in r.de("jira"))


def test_e28_determinista(t):
    """E-28 — la misma entrada da el mismo texto, byte a byte."""
    raiz = _proyecto()
    uno = entorno.texto_de(_resolver(raiz).proyeccion())
    dos = entorno.texto_de(_resolver(raiz).proyeccion())
    t.igual("E-28 igual", uno, dos)


def test_e29_sin_cambios_no_se_reescribe(t):
    """E-29 — un segundo bootstrap sin cambios no toca el archivo."""
    raiz = _proyecto()
    _proyeccion_de(raiz)
    ruta = _ruta_proyeccion(raiz)
    os.utime(ruta, (1000000000, 1000000000))
    antes = os.stat(ruta).st_mtime_ns
    _proyeccion_de(raiz)
    t.igual("E-29 la fecha no cambio", antes, os.stat(ruta).st_mtime_ns)


# -- E-31 a E-34 — el .env de la persona ------------------------------------------

def test_e31_el_bootstrap_no_toca_el_env(t):
    """E-31 — setup, estado y reconfigurar dejan el .env byte a byte igual."""
    crudo = ENV_COMPLETO.replace("\n", "\r\n") + "  # sangria y comillas 'raras'\r\nZ=\"a b\"\r\n"
    raiz = _proyecto(crudo)
    antes = _bytes(os.path.join(raiz, ".env"))
    for argv in (["setup"], ["estado"], ["reconfigurar", "gitlab"], ["estado", "--resumen"]):
        _cli(argv + ["--proyecto", raiz], Transporte())
    t.igual("E-31 el .env sigue igual", antes, _bytes(os.path.join(raiz, ".env")))


def test_e32_lo_ajeno_no_se_lee(t):
    """E-32 — una variable fuera del contrato no aparece en nada de lo que escribe el bootstrap."""
    raiz = _proyecto()
    _cli(["setup", "--proyecto", raiz], Transporte())
    todo = _todo_lo_de_claude(raiz)
    t.no_contiene("E-32 ni su valor", AJENO, todo)
    t.no_contiene("E-32 ni su nombre", "OTRA_VARIABLE", todo)
    # Y no entra a la resolucion: ni un atributo de la Resolucion ni de sus integraciones.
    r = _resolver(raiz)
    adentro = repr([vars(r)] + [vars(i) for i in r.integraciones.values()] +
                   [v.como_dict() for i in r.integraciones.values() for v in i.variables])
    t.no_contiene("E-32 la resolucion no lleva el valor", AJENO, adentro)
    t.no_contiene("E-32 ni el nombre", "OTRA_VARIABLE", adentro)


def _asignaciones_del_ejemplo():
    from integraciones import almacen
    return almacen.asignaciones(_leer(str(ENV_EXAMPLE)).splitlines())


def test_e33_el_ejemplo_solo_tiene_nombres(t):
    """E-33 — cada asignacion es una variable del contrato con vacio, false o placeholder."""
    contrato = set(entorno.variables_del_contrato(_contrato()))
    asignaciones = _asignaciones_del_ejemplo()
    t.igual("E-33 las variables son las del contrato", sorted(contrato),
            sorted(n for n, _ in asignaciones))
    for nombre, valor in asignaciones:
        t.verdadero("E-33 %s sin valor real" % nombre,
                    valor in ("", "false") or re.match(r"^<[^>]*>$", valor) is not None)


def test_e34_el_ejemplo_no_tiene_credenciales(t):
    """E-34 — ningun valor con forma de credencial, y nada de OpenShift."""
    from contexto import limpieza
    catalogo = limpieza.cargar_catalogo()
    t.verdadero("E-34 hay catalogo", catalogo is not None)
    texto = _leer(str(ENV_EXAMPLE))
    t.igual("E-34 el detector no encuentra nada", [], limpieza.redactar(texto, catalogo, "e34")[1])
    t.no_contiene("E-34 sin OpenShift", "OPENSHIFT", texto.upper())


# -- E-35 a E-40 — sin preguntas y sin valores -----------------------------------

def test_e35_setup_no_pregunta(t):
    """E-35 — setup sin terminal y con el .env vacio sale 0 y no llama a input ni getpass."""
    raiz = _proyecto("")
    codigo, salida, _, pedidos = _cli(["setup", "--proyecto", raiz], Transporte())
    t.igual("E-35 sale 0", 0, codigo)
    t.igual("E-35 no pregunto nada", [], pedidos)
    t.no_contiene("E-35 no pide un token", "API Token", salida)


def test_e36_setup_lista_presente_y_ausente(t):
    """E-36 — cada variable del contrato con presente/ausente."""
    raiz = _proyecto(re.sub(r"GITLAB_TOKEN=.*\n", "", ENV_COMPLETO))
    _, salida, _, _ = _cli(["setup", "--proyecto", raiz], Transporte())
    for nombre in VARIABLES:
        t.verdadero("E-36 %s figura" % nombre,
                    re.search(r"^  %s\s+(presente|ausente)" % nombre, salida, re.M) is not None)
    t.verdadero("E-36 GITLAB_TOKEN ausente",
                re.search(r"^  GITLAB_TOKEN\s+ausente", salida, re.M) is not None)
    t.verdadero("E-36 JIRA_TOKEN presente",
                re.search(r"^  JIRA_TOKEN\s+presente\s+DOTENV", salida, re.M) is not None)


def test_e37_reconfigurar_no_muestra_valores(t):
    """E-37 — variables, capa y estado de Jira; que editar; ningun valor del .env."""
    raiz = _proyecto()
    codigo, salida, error, _ = _cli(["reconfigurar", "jira", "--proyecto", raiz], Transporte())
    t.igual("E-37 sale 0", 0, codigo)
    t.verdadero("E-37 JIRA_BASE_URL con su capa",
                re.search(r"^  JIRA_BASE_URL\s+presente\s+DOTENV", salida, re.M) is not None)
    t.contiene("E-37 dice que se edita el .env", "editá", salida)
    t.contiene("E-37 y el estado", "AVAILABLE", salida)
    for valor in (URL_JIRA, USUARIO, TOKEN_JIRA, URL_GITLAB, TOKEN_GITLAB, AJENO):
        t.no_contiene("E-37 sin %s" % valor[:20], valor, salida + error)


def test_e38_el_token_por_argumento_sigue_rechazado(t):
    """E-38 — --token sale 2, no repite el valor y no escribe nada."""
    raiz = _proyecto()
    antes = sorted(os.listdir(os.path.join(raiz, ".claude")))
    codigo, salida, error, _ = _cli(["setup", "--proyecto", raiz, "--token", TOKEN_JIRA])
    t.igual("E-38 sale 2", 2, codigo)
    t.no_contiene("E-38 no lo repite", TOKEN_JIRA, salida + error)
    t.contiene("E-38 manda al .env", ".env", error)
    t.igual("E-38 no escribio nada", antes, sorted(os.listdir(os.path.join(raiz, ".claude"))))


def test_e39_e40_ningun_token_en_la_salida(t):
    """E-39, E-40 — ni stdout ni stderr, tampoco con un servidor que devuelve el token."""
    eco = {"/rest/api/3/myself": (401, json.dumps({"error": TOKEN_JIRA})),
           "/api/v4/user": (401, json.dumps({"message": TOKEN_GITLAB}))}
    for argv in (["setup"], ["estado"], ["reconfigurar", "jira"], ["estado", "--resumen"]):
        for respuestas in (None, eco):
            raiz = _proyecto()
            _, salida, error, _ = _cli(argv + ["--proyecto", raiz], Transporte(respuestas))
            for token in (TOKEN_JIRA, TOKEN_GITLAB):
                t.no_contiene("E-39 %s stdout" % " ".join(argv), token, salida)
                t.no_contiene("E-40 %s stderr" % " ".join(argv), token, error)
    # Un .env ilegible y un contrato roto, las dos rutas de error que nombran archivos.
    raiz = _proyecto(None)
    with open(os.path.join(raiz, ".env"), "wb") as f:
        f.write(("JIRA_TOKEN=%s\n" % TOKEN_JIRA).encode("utf-8") + b"\xff\xfe\n")
    _, salida, error, _ = _cli(["estado", "--proyecto", raiz], Transporte())
    t.contiene("E-40 ENV_FILE_UNREADABLE", "ENV_FILE_UNREADABLE", error)
    t.no_contiene("E-40 sin el token", TOKEN_JIRA, salida + error)
    roto = _contrato_roto({"schema_version": "otra"})
    _, salida, error, _ = _con_contrato(roto, ["estado", "--proyecto", _proyecto()])
    t.contiene("E-40 ENV_CONTRACT_INVALID", "ENV_CONTRACT_INVALID", error)
    t.no_contiene("E-40 sin el token", TOKEN_JIRA, salida + error)


# -- E-41 a E-47 — la frontera del modelo ---------------------------------------

def test_e41_e42_el_env_sigue_negado(t):
    """E-41, E-42 — permissions.deny sigue negando .env y .env.*."""
    deny = json.loads(_leer(str(DENY)))["permissions"]["deny"]
    t.verdadero("E-41 Read(./.env)", "Read(./.env)" in deny)
    t.verdadero("E-42 Read(./.env.*)", "Read(./.env.*)" in deny)


def test_e43_session_start_no_trae_el_env(t):
    """E-43 — lo que imprime session-start.py no lleva ningun valor del .env."""
    m51 = _cargar("bienvenida_para_60", CASOS / "51_bienvenida.py")
    proy = m51._proyecto()
    (proy / ".env").write_text(ENV_COMPLETO, encoding="utf-8")
    for n in range(2):                  # la bienvenida completa y la linea compacta
        codigo, _, _, crudo = m51._sesion(proy)
        t.igual("E-43 sale 0 (%d)" % n, 0, codigo)
        for valor in (URL_JIRA, USUARIO, TOKEN_JIRA, URL_GITLAB, TOKEN_GITLAB, AJENO):
            t.no_contiene("E-43 sin %s (%d)" % (valor[:20], n), valor, crudo)
    t.no_contiene("E-43 el estado escrito tampoco", TOKEN_JIRA,
                  (proy / ".claude" / "harness.installation.json").read_text(encoding="utf-8"))


def test_e44_el_task_context_no_trae_el_env(t):
    """E-44 — el TaskContext de `contexto` no lleva ningun token ni variable ajena."""
    m19 = _cargar("contexto_para_60", CASOS / "19_contexto.py")
    raiz = _proyecto(ENV_COMPLETO + "GITLAB_PROJECT=tramites/backoffice\n")
    with io.open(os.path.join(raiz, ".claude", "harness.capacidades.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"capacidades": dict((c, "ENABLED") for c in TODAS)}))
    transporte = m19.Transporte({"/issue/": (200, m19.ISSUE), "/search": (200, m19.FICHA),
                                 "/projects/": (200, m19.PROYECTO_GITLAB),
                                 "branches": (200, m19.RAMAS), "merge_requests": (200, m19.MRS)})
    modulo = _cargar("dev_harness_60_ctx", CLI)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(["contexto", m19.CLAVE, "--proyecto", raiz], transporte,
                             m19._Bytes({}))
    finally:
        sys.stdout, sys.stderr = previos
    destino = os.path.join(raiz, ".claude", "contextos", m19.CLAVE + ".json")
    t.igual("E-44 contexto sale 0", 0, codigo)
    texto = _leer(destino)
    for valor in (TOKEN_JIRA, TOKEN_GITLAB, AJENO, "OTRA_VARIABLE"):
        t.no_contiene("E-44 sin %s" % valor[:20], valor, texto)
    t.no_contiene("E-44 ni en todo .claude", TOKEN_JIRA, _todo_lo_de_claude(raiz))


def test_e45_el_libro_del_bloque_4_no_trae_el_env(t):
    """E-45 — lo que deja la contabilidad no lleva ningun token del .env."""
    m30 = _cargar("contabilidad_para_60", CASOS / "30_b4_contabilidad.py")
    raiz = _proyecto()
    fuente = m30._transcripcion(raiz)
    codigo, _, _, _ = _cli(["contabilidad", m30.TAREA, "--ingerir", fuente, "--reporte",
                            "--proyecto", raiz])
    t.igual("E-45 contabilidad sale 0", 0, codigo)
    todo = _todo_lo_de_claude(raiz)
    t.verdadero("E-45 hay libro", os.path.isfile(m30.c_libro.ruta_de(raiz, m30.TAREA)))
    for token in (TOKEN_JIRA, TOKEN_GITLAB, AJENO):
        t.no_contiene("E-45 sin %s" % token[:20], token, todo)


def test_e46_el_libro_de_seguridad_no_trae_el_env(t):
    """E-46 — lo que deja `seguridad` no lleva ningun token del .env."""
    m48 = _cargar("seguridad_para_60", CASOS / "48_reporte_de_seguridad.py")
    raiz = m48._proyecto_con_fuentes()
    with io.open(os.path.join(raiz, ".env"), "w", encoding="utf-8") as f:
        f.write(ENV_COMPLETO)
    codigo, _, _, _ = _cli(["seguridad", m48.TAREA, "--conocimiento", "--resumen", "--reporte",
                            "--proyecto", raiz])
    t.igual("E-46 seguridad sale 0", 0, codigo)
    todo = _todo_lo_de_claude(raiz)
    t.verdadero("E-46 hay libro", os.path.isfile(m48.libro.ruta_de(raiz, m48.TAREA)))
    for token in (TOKEN_JIRA, TOKEN_GITLAB, AJENO):
        t.no_contiene("E-46 sin %s" % token[:20], token, todo)


def test_e47_pre_tool_use_sigue_bloqueando(t):
    """E-47 — escribir un token literal en el .env sigue siendo deny."""
    token = "glp" + "at-" + "Q7w8E9r0T1y2U3i4O5p6A7s8"
    payload = {"session_id": "s60", "hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": ".env", "content": "GITLAB_TOKEN=%s\n" % token}}
    r = subprocess.run([sys.executable, str(RAIZ / "comun" / "hooks" / "pre-tool-use.py")],
                       input=json.dumps(payload).encode("utf-8"), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    salida = json.loads(r.stdout.decode("utf-8"))
    t.igual("E-47 sale 0", 0, r.returncode)
    t.igual("E-47 deny", "deny", salida["hookSpecificOutput"]["permissionDecision"])


# -- E-48 a E-52 — lo que no cambia en los adapters -------------------------------

def test_e48_jira_auth_igual(t):
    """E-48 — Basic con usuario:token del .env, y 401 es AUTHENTICATION_FAILED."""
    raiz = _proyecto()
    transporte = Transporte()
    _cli(["estado", "--proyecto", raiz], transporte)
    headers = [h for u, h in transporte.llamadas if u.endswith("/rest/api/3/myself")][0]
    t.igual("E-48 Basic", "Basic " + base64.b64encode(
        ("%s:%s" % (USUARIO, TOKEN_JIRA)).encode("utf-8")).decode("ascii"),
        headers["Authorization"])
    raiz = _proyecto()
    _cli(["estado", "--proyecto", raiz], Transporte({"/rest/api/3/myself": (401, "")}))
    t.igual("E-48 401", "AUTHENTICATION_FAILED", _capacidades(raiz)["integraciones"]["jira"]["estado"])


def test_e49_gitlab_auth_igual(t):
    """E-49 — PRIVATE-TOKEN del .env, sin Authorization, y 401 es AUTHENTICATION_FAILED."""
    raiz = _proyecto()
    transporte = Transporte()
    _cli(["estado", "--proyecto", raiz], transporte)
    headers = [h for u, h in transporte.llamadas if u.endswith("/api/v4/user")][0]
    t.igual("E-49 PRIVATE-TOKEN", TOKEN_GITLAB, headers["PRIVATE-TOKEN"])
    t.igual("E-49 sin Authorization", None, headers.get("Authorization"))
    raiz = _proyecto()
    _cli(["estado", "--proyecto", raiz], Transporte({"/api/v4/user": (401, "")}))
    t.igual("E-49 401", "AUTHENTICATION_FAILED",
            _capacidades(raiz)["integraciones"]["gitlab"]["estado"])


def test_e50_descubrimiento_igual(t):
    """E-50 — read_api habilita las cuatro de GitLab."""
    raiz = _proyecto()
    _cli(["estado", "--proyecto", raiz], Transporte())
    capacidades = _capacidades(raiz)["capacidades"]
    t.igual("E-50 cuatro de GitLab", 4, sum(1 for c, v in capacidades.items()
                                            if c.startswith("gitlab.") and v == "ENABLED"))


def test_e51_e52_sin_configurar_deshabilitadas(t):
    """E-51, E-52 — sin configurar, cada integracion deja sus capacidades DISABLED."""
    raiz = _proyecto("")
    _cli(["estado", "--proyecto", raiz], Transporte())
    capacidades = _capacidades(raiz)["capacidades"]
    t.igual("E-51 tres de Jira DISABLED", ["DISABLED"] * 3,
            [v for c, v in sorted(capacidades.items()) if c.startswith("jira.")])
    t.igual("E-52 cuatro de GitLab DISABLED", ["DISABLED"] * 4,
            [v for c, v in sorted(capacidades.items()) if c.startswith("gitlab.")])


# -- E-53 a E-56 — la migracion -----------------------------------------------------

VIEJO = {"_comentario": ["el archivo que completaba la persona"],
         "jira": {"enabled": True, "baseUrl": URL_JIRA, "usuario": USUARIO},
         "gitlab": {"enabled": None, "baseUrl": "", "gitlabProyecto": ""}}


def test_e53_el_json_viejo_ayuda_a_migrar(t):
    """E-53 — JSON viejo + solo JIRA_TOKEN en el .env: valida, con fuente LEGACY."""
    raiz = _proyecto("JIRA_TOKEN=%s\n" % TOKEN_JIRA, proyeccion=VIEJO)
    transporte = Transporte()
    codigo, salida, _, _ = _cli(["setup", "--proyecto", raiz], transporte)
    t.igual("E-53 sale 0", 0, codigo)
    t.igual("E-53 Jira AVAILABLE", "AVAILABLE", _capacidades(raiz)["integraciones"]["jira"]["estado"])
    t.verdadero("E-53 con la baseUrl vieja", URL_JIRA + "/rest/api/3/myself" in transporte.urls())
    t.verdadero("E-53 la capa es LEGACY",
                re.search(r"^  JIRA_BASE_URL\s+presente\s+LEGACY", salida, re.M) is not None)
    t.contiene("E-53 dice que falta migrar", "Migración: HARNESS_JIRA_ENABLED, JIRA_BASE_URL, "
               "JIRA_USER", salida)
    t.no_contiene("E-53 sin el valor", URL_JIRA, salida)


def test_e54_el_env_le_gana_al_json_viejo(t):
    """E-54 — con la variable en el .env gana el .env, y el valor viejo no vuelve."""
    otra = "https://la-del-env.atlassian.net"
    raiz = _proyecto("JIRA_TOKEN=%s\nJIRA_BASE_URL=%s\n" % (TOKEN_JIRA, otra), proyeccion=VIEJO)
    _cli(["estado", "--proyecto", raiz], Transporte())
    t.igual("E-54 gana el .env", otra, json.loads(_leer(_ruta_proyeccion(raiz)))["jira"]["baseUrl"])
    with io.open(os.path.join(raiz, ".env"), "w", encoding="utf-8") as f:
        f.write("JIRA_TOKEN=%s\n" % TOKEN_JIRA)
    transporte = Transporte()
    _cli(["estado", "--proyecto", raiz], transporte)
    jira = _capacidades(raiz)["integraciones"]["jira"]
    t.igual("E-54 el viejo no vuelve", ["JIRA_BASE_URL"], jira["faltan"])
    t.igual("E-54 y no se sale a la red con el", [], transporte.urls(URL_JIRA))


def test_e55_la_migracion_no_copia_secretos(t):
    """E-55 — un JSON viejo con token o apiKey no se lee, no se imprime, no se copia."""
    viejo = json.loads(json.dumps(VIEJO))
    viejo["jira"]["token"] = "valor-legado-que-es-secreto"
    viejo["jira"]["apiKey"] = "otro-valor-legado-secreto"
    raiz = _proyecto("JIRA_TOKEN=%s\n" % TOKEN_JIRA, proyeccion=viejo)
    _, salida, error, _ = _cli(["setup", "--proyecto", raiz], Transporte())
    texto = _leer(_ruta_proyeccion(raiz))
    for valor in ("valor-legado-que-es-secreto", "otro-valor-legado-secreto"):
        t.no_contiene("E-55 no se imprime", valor, salida + error)
        t.no_contiene("E-55 no se copia", valor, texto)
    # No se lee: sin JIRA_TOKEN en el .env, el token del JSON viejo no lo reemplaza.
    raiz = _proyecto("", proyeccion=viejo)
    transporte = Transporte()
    _, salida, error, _ = _cli(["estado", "--proyecto", raiz], transporte)
    jira = _capacidades(raiz)["integraciones"]["jira"]
    t.igual("E-55 no se lee: NOT_CONFIGURED", "NOT_CONFIGURED", jira["estado"])
    t.igual("E-55 no se lee: falta JIRA_TOKEN", ["JIRA_TOKEN"], jira["faltan"])
    t.igual("E-55 no se lee: sin red", [], transporte.llamadas)
    t.no_contiene("E-55 tampoco en esta corrida", "valor-legado-que-es-secreto", salida + error)


def test_e56_la_proyeccion_queda_en_su_lugar(t):
    """E-56 — despues de migrar el archivo sigue ahi, con la marca de proyeccion."""
    raiz = _proyecto("JIRA_TOKEN=%s\n" % TOKEN_JIRA, proyeccion=VIEJO)
    _cli(["estado", "--proyecto", raiz], Transporte())
    doc = json.loads(_leer(_ruta_proyeccion(raiz)))
    t.igual("E-56 con la marca", "integration-projection/1.0", doc.get("schema_version"))
    t.igual("E-56 y lo que falta migrar", URL_JIRA, doc["legado"]["jira"]["baseUrl"])


# -- E-57 a E-60 — el estado general ------------------------------------------------

def _harness_json(raiz):
    codigo, salida, _, _ = _cli(["harness", "--json", "--proyecto", raiz])
    return codigo, json.loads(salida), salida


def test_e57_e58_harness_json(t):
    """E-57, E-58 — el modo, si hay .env, y ningun valor."""
    m51 = _cargar("bienvenida_para_60b", CASOS / "51_bienvenida.py")
    proy = m51._proyecto()
    (proy / ".env").write_text(ENV_COMPLETO, encoding="utf-8")
    codigo, doc, texto = _harness_json(str(proy))
    t.igual("E-57 sale 0", 0, codigo)
    configuracion = doc.get("integrationConfiguration") or {}
    t.igual("E-57 modo", "ENVIRONMENT_FIRST", configuracion.get("configurationMode"))
    t.igual("E-57 el documento cumple el schema", [], m51._validar(doc))
    t.igual("E-58 hay .env", True, configuracion.get("envFilePresent"))
    t.igual("E-58 el modelo no lo lee", False, configuracion.get("envModelReadable"))
    for valor in (URL_JIRA, USUARIO, TOKEN_JIRA, TOKEN_GITLAB, AJENO):
        t.no_contiene("E-58 sin %s" % valor[:20], valor, texto)
    (proy / ".env").unlink()
    _, doc, _ = _harness_json(str(proy))
    t.igual("E-58 sin .env", False, doc["integrationConfiguration"]["envFilePresent"])


def test_e59_la_bienvenida_dice_que_falta(t):
    """E-59 — la seccion Configuracion, y Faltan: con los nombres."""
    m51 = _cargar("bienvenida_para_60c", CASOS / "51_bienvenida.py")
    proy = m51._proyecto()
    (proy / ".env").write_text(re.sub(r"GITLAB_(BASE_URL|TOKEN)=.*\n", "", ENV_COMPLETO),
                               encoding="utf-8")
    _cli(["estado", "--proyecto", str(proy)], Transporte())
    codigo, salida, _, _ = _cli(["harness", "--proyecto", str(proy)])
    t.igual("E-59 sale 0", 0, codigo)
    t.contiene("E-59 seccion", "Configuración", salida)
    t.verdadero("E-59 Fuente", re.search(r"^  Fuente\s+\.env local$", salida, re.M) is not None)
    t.verdadero("E-59 Acceso del modelo",
                re.search(r"^  Acceso del modelo\s+BLOQUEADO$", salida, re.M) is not None)
    t.contiene("E-59 Faltan", "Faltan: GITLAB_BASE_URL, GITLAB_TOKEN", salida)
    t.no_contiene("E-59 sin valores", TOKEN_JIRA, salida)


def test_e60_listo_parcial_y_env_legible(t):
    """E-60 — LISTO con todo disponible, PARCIAL con una sin configurar o con el .env legible."""
    m51 = _cargar("bienvenida_para_60d", CASOS / "51_bienvenida.py")
    t.igual("E-60 todo disponible: READY", "READY", m51.B.resolver(str(m51._proyecto()))
            ["bootstrap"]["status"])
    doc = m51.B.resolver(str(m51._proyecto(gitlab="NOT_CONFIGURED")))
    t.igual("E-60 una sin configurar: PARTIAL", "PARTIAL", doc["bootstrap"]["status"])
    proy = m51._proyecto()
    settings = json.loads((proy / ".claude" / "settings.json").read_text(encoding="utf-8"))
    settings.pop("permissions")
    (proy / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    doc = m51.B.resolver(str(proy))
    t.igual("E-60 .env legible: PARTIAL", "PARTIAL", doc["bootstrap"]["status"])
    t.verdadero("E-60 con ENV_MODEL_READABLE",
                "ENV_MODEL_READABLE" in doc["bootstrap"]["pendingConditions"])


# -- E-62 — variables nuevas --------------------------------------------------------

def test_e62_variables_nuevas(t):
    """E-62 — una proyeccion con una lista mas corta hace que se nombren las nuevas."""
    raiz = _proyecto()
    _proyeccion_de(raiz)
    doc = json.loads(_leer(_ruta_proyeccion(raiz)))
    doc["variables"] = [v for v in doc["variables"] if v != "GITLAB_PROJECT"]
    with io.open(_ruta_proyeccion(raiz), "w", encoding="utf-8") as f:
        f.write(json.dumps(doc))
    codigo, salida, _, _ = _cli(["estado", "--resumen", "--proyecto", raiz], Transporte())
    t.igual("E-62 sale 0", 0, codigo)
    t.contiene("E-62 nombra la nueva", "Variables nuevas del contrato: GITLAB_PROJECT", salida)
    t.contiene("E-62 y el resumen", "Jira Cloud    OK", salida)
    codigo, salida, _, _ = _cli(["estado", "--resumen", "--proyecto", raiz], Transporte())
    t.no_contiene("E-62 la segunda vez ya no es nueva", "Variables nuevas", salida)


# -- E-66 a E-70 — contratos rotos y archivos que no se leen -----------------------

def test_e66_solo_jira_y_gitlab(t):
    """E-66 — el contrato tiene jira y gitlab, y ninguna variable de OpenShift."""
    contrato = _contrato()
    t.igual("E-66 integraciones", ["gitlab", "jira"], sorted(i["id"] for i in contrato["integrations"]))
    t.igual("E-66 sin OPENSHIFT", [], [v for v in entorno.variables_del_contrato(contrato)
                                       if v.startswith("OPENSHIFT")])
    esquema = json.loads(_leer(str(SCHEMA_CONTRATO)))
    m51 = _cargar("bienvenida_para_60e", CASOS / "51_bienvenida.py")
    t.igual("E-66 el contrato cumple su schema", True, m51.B.cumple(contrato, esquema))


def _contrato_roto(cambios=None, texto=None):
    ruta = os.path.join(tempfile.mkdtemp(prefix="contrato-60-"), "c.json")
    if texto is None:
        doc = json.loads(_leer(str(CONTRATO)))
        doc.update(cambios or {})
        texto = json.dumps(doc)
    with io.open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    return ruta


def _con_contrato(ruta, argv):
    original = entorno.ruta_del_contrato
    entorno.ruta_del_contrato = lambda desde=None: ruta
    try:
        return _cli(argv, Transporte())
    finally:
        entorno.ruta_del_contrato = original


def test_e67_una_integracion_sin_adapter(t):
    """E-67 — openshift en el contrato: ENV_CONTRACT_INVALID, sale 2, sin capacidades."""
    doc = json.loads(_leer(str(CONTRATO)))
    doc["integrations"].append({"id": "openshift",
                                "enabled": {"env": "HARNESS_OPENSHIFT_ENABLED", "default": False},
                                "fields": [{"name": "token", "env": "OPENSHIFT_TOKEN",
                                            "classification": "SECRET",
                                            "requiredWhenEnabled": True}]})
    raiz = _proyecto()
    codigo, _, error, _ = _con_contrato(_contrato_roto(texto=json.dumps(doc)),
                                        ["estado", "--proyecto", raiz])
    t.igual("E-67 sale 2", 2, codigo)
    t.contiene("E-67 el codigo", "ENV_CONTRACT_INVALID", error)
    t.contiene("E-67 lo nombra", "openshift", error)
    t.verdadero("E-67 no escribe capacidades",
                not os.path.exists(os.path.join(raiz, ".claude", "harness.capacidades.json")))


def test_e68_contratos_rotos(t):
    """E-68 — JSON invalido, sin integrations, clasificacion desconocida, variable repetida."""
    doc = json.loads(_leer(str(CONTRATO)))
    mala = json.loads(json.dumps(doc))
    mala["integrations"][0]["fields"][0]["classification"] = "PUBLICO"
    repetida = json.loads(json.dumps(doc))
    repetida["integrations"][1]["fields"][0]["env"] = "JIRA_BASE_URL"
    for nombre, ruta in (("JSON invalido", _contrato_roto(texto="{ roto")),
                         ("sin integrations", _contrato_roto(texto='{"schema_version": '
                                                             '"integration-environment-contract/1.0"}')),
                         ("clasificacion desconocida", _contrato_roto(texto=json.dumps(mala))),
                         ("variable repetida", _contrato_roto(texto=json.dumps(repetida)))):
        codigo = ""
        try:
            entorno.cargar_contrato(ruta)
        except entorno.ErrorDeEntorno as e:
            codigo = e.codigo
        t.igual("E-68 %s" % nombre, "ENV_CONTRACT_INVALID", codigo)
        codigo, _, error, _ = _con_contrato(ruta, ["estado", "--proyecto", _proyecto()])
        t.igual("E-68 %s por la CLI sale 2" % nombre, 2, codigo)
        t.no_contiene("E-68 %s sin traza" % nombre, "Traceback", error)


def test_e69_env_ilegible(t):
    """E-69 — un .env directorio o que no es UTF-8: ENV_FILE_UNREADABLE sin contenido."""
    raiz = _proyecto(None)
    os.makedirs(os.path.join(raiz, ".env"))
    codigo, _, error, _ = _cli(["estado", "--proyecto", raiz], Transporte())
    t.igual("E-69 directorio sale 2", 2, codigo)
    t.contiene("E-69 directorio: el codigo", "ENV_FILE_UNREADABLE", error)
    t.contiene("E-69 directorio: nombra el archivo", ".env", error)
    raiz = _proyecto(None)
    with open(os.path.join(raiz, ".env"), "wb") as f:
        f.write(b"JIRA_BASE_URL=https://byte-que-no-es-utf8-\xe9-aca\n")
    codigo, salida, error, _ = _cli(["estado", "--proyecto", raiz], Transporte())
    t.igual("E-69 no UTF-8 sale 2", 2, codigo)
    t.contiene("E-69 no UTF-8: el codigo", "ENV_FILE_UNREADABLE", error)
    for pedazo in ("byte-que-no-es-utf8", "0xe9", "position", "JIRA_BASE_URL"):
        t.no_contiene("E-69 sin %s" % pedazo, pedazo, salida + error)


def test_e70_la_advertencia_no_trae_valores(t):
    """E-70 — ENV_MODEL_READABLE se describe sin ningun valor del .env."""
    m51 = _cargar("bienvenida_para_60f", CASOS / "51_bienvenida.py")
    proy = m51._proyecto()
    (proy / ".env").write_text(ENV_COMPLETO, encoding="utf-8")
    (proy / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    doc = m51.B.resolver(str(proy))
    bienvenida = m51.B.renderizar_bienvenida(doc)
    t.contiene("E-70 la bienvenida lo advierte", "el modelo puede leer el .env", bienvenida)
    texto = bienvenida + json.dumps(doc) + m51.B.renderizar_linea(doc)
    for valor in (URL_JIRA, USUARIO, TOKEN_JIRA, TOKEN_GITLAB, AJENO):
        t.no_contiene("E-70 sin %s" % valor[:20], valor, texto)
