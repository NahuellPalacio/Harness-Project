# El conocimiento confiable se vuelve a mirar solo, en momentos controlados.
#
# Escenarios E-01 a E-72 de docs/cambios/conocimiento-auto-refresco/spec.md. Cada test nombra su
# escenario y el id del paquete entregado (KRF-nnn). E-68 instala de verdad y vive en
# 61-auto-refresco-instalador.ps1; E-70 a E-72 son la suite entera.
#
# 🔴 Los estados y los codigos van clavados por literal, como en 45_conocimiento_fuentes.py:
# leerlos del modulo y compararlos contra si mismos pasa con cualquier renombre.
import ast
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
LIB = RAIZ / "comun" / "hooks" / "lib" / "bienvenida.py"
SESSION_START = RAIZ / "comun" / "hooks" / "session-start.py"
MODULO = BIN / "orquestacion" / "auto_refresh.py"
POLITICA = RAIZ / "harnesses" / "desarrollo" / "reglas" / "knowledge-refresh-policy.json"
REGISTRO = RAIZ / "harnesses" / "desarrollo" / "reglas" / "source-registry.json"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
from orquestacion import auto_refresh as ar              # noqa: E402
from orquestacion import frescura as fr                  # noqa: E402
from orquestacion import registro_fuentes as rf          # noqa: E402

TOKEN = "token-secreto-de-prueba-KRF-9f3a"
USUARIO = "persona.krf@buenosaires.gob.ar"
URL_JIRA = "https://jira-krf.example.atlassian.net"
FICHA = "FICHA-1"
PDF_62 = "ES0902 - Estandar de Seguridad V6.2.pdf"
PDF_63 = "ES0902 - Estandar de Seguridad V6.3.pdf"
CAPACIDADES_OK = {"jira.issue.read": "ENABLED", "jira.issue.search": "ENABLED",
                  "jira.attachment.read": "ENABLED"}
ENV = ("HARNESS_JIRA_ENABLED=true\nJIRA_BASE_URL=%s\nJIRA_USER=%s\nJIRA_TOKEN=%s\n"
       "HARNESS_GITLAB_ENABLED=false\n") % (URL_JIRA, USUARIO, TOKEN)


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


B = _cargar("bienvenida_krf", LIB)


# -- andamios ------------------------------------------------------------------

def _escribir(ruta, contenido):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contenido, (dict, list)):
        contenido = json.dumps(contenido, ensure_ascii=False, indent=2)
    if isinstance(contenido, bytes):
        ruta.write_bytes(contenido)
    else:
        ruta.write_text(contenido, encoding="utf-8", newline="\n")


def _proyecto(archivos=None, env=None, capacidades=None, usuario="Ana Prueba"):
    """(base, proyecto, ficha). Un proyecto con `desarrollo` y una carpeta de originales."""
    base = Path(tempfile.gettempdir()) / ("harness-61-" + uuid.uuid4().hex[:8])
    proy, ficha = base / "proyecto", base / "ficha"
    _escribir(proy / ".claude" / "harness.config.json", {"usuario": usuario})
    _escribir(proy / ".claude" / "harness.lock.json",
              {"version": "0.27.0", "harness": ["comun", "desarrollo"],
               "instalado": "2026-09-29 10:00:00", "archivos": []})
    if env is not None:
        _escribir(proy / ".env", env)
    if capacidades is not None:
        _escribir(proy / ".claude" / "harness.capacidades.json",
                  {"schema_version": "integraciones/1.0", "integraciones": {},
                   "capacidades": capacidades})
    for nombre, contenido in (archivos if archivos is not None
                              else {PDF_62: "original ES0902 6.2"}).items():
        _escribir(ficha / nombre, contenido)
    return base, proy, ficha


def _limpiar(base):
    shutil.rmtree(str(base), ignore_errors=True)


def _fuentes(proy):
    ruta = proy / ".claude" / "harness.fuentes.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def _bytes_fuentes(proy):
    ruta = proy / ".claude" / "harness.fuentes.json"
    return ruta.read_bytes() if ruta.is_file() else None


def _agenda(proy):
    ruta = proy / ".claude" / "runtime" / "knowledge-refresh.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def _texto_agenda(proy):
    ruta = proy / ".claude" / "runtime" / "knowledge-refresh.json"
    return ruta.read_text(encoding="utf-8") if ruta.is_file() else ""


def _escribir_agenda(proy, **campos):
    agenda = {"schema_version": "knowledge-refresh-state/1.0", "state": "CURRENT",
              "lastAttemptAt": None, "lastSuccessfulCheckAt": None, "nextCheckDueAt": None,
              "trigger": None, "errorCode": None, "sources": []}
    agenda.update(campos)
    _escribir(proy / ".claude" / "runtime" / "knowledge-refresh.json", agenda)


def _estado(proy, sid="ES0902"):
    return _fuentes(proy)["sources"][sid]["state"]


def _cli(proy, *args, transporte=None, transporte_bytes=None):
    """dev-harness.py en proceso, con transportes falsos si se pasan. (codigo, stdout, stderr)."""
    modulo = _cargar("dev_harness_krf_%s" % uuid.uuid4().hex[:6], CLI)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(list(args) + ["--proyecto", str(proy)], transporte,
                             transporte_bytes)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _sha(texto):
    return hashlib.sha256(texto.encode("utf-8") if isinstance(texto, str) else texto).hexdigest()


class Jira(object):
    """Una Ficha falsa. `adjuntos` es lo que devuelve el issue; `contenidos`, lo que baja cada
    URL. Anota cada pedido, con sus cabeceras, para ver que no se sale a la red sin permiso."""

    def __init__(self, adjuntos, contenidos=None, error=None):
        self.adjuntos = adjuntos
        self.contenidos = contenidos or {}
        self.error = error
        self.llamadas = []
        self.bajadas = []

    def transporte(self, url, headers, timeout):
        self.llamadas.append((url, dict(headers)))
        if self.error is not None:
            raise self.error
        if "/rest/api/3/issue/%s" % FICHA in url:
            return 200, json.dumps({"key": FICHA, "fields": {"attachment": self.adjuntos,
                                                             "description": None}})
        return 404, ""

    def transporte_bytes(self, url, headers, timeout):
        self.bajadas.append((url, dict(headers)))
        return 200, self.contenidos.get(url, b""), {}


def _adjunto(nombre=PDF_62, aid="10001", tam=19, creado="2026-09-01T10:00:00.000+0000"):
    return {"id": aid, "filename": nombre, "size": tam, "created": creado,
            "content": "%s/rest/api/3/attachment/content/%s" % (URL_JIRA, aid)}


def _proyecto_jira(capacidades=None):
    """Un proyecto cuya ultima corrida de `fuentes` fue contra la Ficha FICHA-1."""
    base, proy, ficha = _proyecto(env=ENV, capacidades=capacidades or dict(CAPACIDADES_OK))
    _escribir(proy / ".claude" / "harness.fuentes.json",
              {"schema_version": "sources-state/1.1", "verified_at": "2026-09-01T10:00:00",
               "ficha": {"key": FICHA, "issue_type": "Ficha de Proyecto", "reachable": True,
                         "channel": "jira:" + FICHA},
               "sources": {}, "decisions": {}, "pending_count": 0, "warnings": []})
    return base, proy


def _auto_jira(proy, jira, *extra):
    return _cli(proy, "fuentes", "--auto", *extra, transporte=jira.transporte,
                transporte_bytes=jira.transporte_bytes)


def _politica(**cambios):
    p = json.loads(POLITICA.read_text(encoding="utf-8"))
    p.update(cambios)
    return p


def _huellas_de(carpetas):
    salida = {}
    for carpeta in carpetas:
        for ruta in sorted(Path(carpeta).rglob("*")):
            if ruta.is_file() and "__pycache__" not in ruta.parts:
                salida[str(ruta)] = hashlib.sha256(ruta.read_bytes()).hexdigest()
    return salida


def _llamadas_de(ruta):
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            f = nodo.func
            nombres.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return nombres


def _importados(ruta):
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(nodo.module or "")
            nombres.update(a.name for a in nodo.names)
    return nombres


# El commit que cerro 0.26.0: contra el se compara lo que no tiene que cambiar.
BASE_0260 = "6cff4b4"


def _en_git(patrones):
    """Lo que git tenia versionado en 0.26.0 que cae en esos patrones, o None sin git."""
    import fnmatch
    try:
        r = subprocess.run(["git", "-C", str(RAIZ), "ls-tree", "-r", "--name-only", BASE_0260],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return sorted(l for l in r.stdout.decode("utf-8").splitlines()
                  if any(fnmatch.fnmatch(l, p) for p in patrones))


def _del_arbol(patrones):
    import fnmatch
    salida = []
    for ruta in RAIZ.rglob("*"):
        relativa = str(ruta.relative_to(RAIZ)).replace(os.sep, "/")
        if ruta.is_file() and not relativa.startswith(".git/") \
                and any(fnmatch.fnmatch(relativa, p) for p in patrones):
            salida.append(relativa)
    return sorted(salida)


# -- E-01 a E-06: que no cambia de lugar ----------------------------------------------

def test_e01_e02_ni_agent_ni_skill_nuevos(t):
    """E-01 (KRF-001), E-02 (KRF-002) — los mismos agents y skills que en 0.26.0."""
    for escenario, patrones in (("E-01 agents", ("comun/agents/*", "harnesses/*/agents/*")),
                                ("E-02 skills", ("comun/skills/*", "harnesses/*/skills/*"))):
        antes = _en_git(patrones)
        if antes is None:
            t.verdadero("%s: git disponible para comparar" % escenario, False)
            continue
        t.igual("%s: los mismos archivos que en 0.26.0" % escenario, antes, _del_arbol(patrones))


def test_e03_la_observacion_es_la_de_fuentes(t):
    """E-03 (KRF-003) — auto_refresh.py no observa por su cuenta."""
    importados = _importados(MODULO)
    llamadas = _llamadas_de(MODULO)
    t.verdadero("E-03 importa integraciones.fuentes", "integraciones" in importados
                and "fuentes" in importados)
    for nombre in ("re", "hashlib"):
        t.verdadero("E-03 no importa %s" % nombre, nombre not in importados)
    for nombre in ("sha256_de", "comparar", "reconoce", "version_en_nombre", "hay_que_bajar",
                   "search", "match"):
        t.verdadero("E-03 no llama a %s" % nombre, nombre not in llamadas)
    t.verdadero("E-03 observa con fuentes.observar_archivos", "observar_archivos" in llamadas)


def test_e04_el_estado_sale_de_frescura(t):
    """E-04 (KRF-004) — el documento del refresco es el de frescura.documento."""
    base, proy, ficha = _proyecto()
    try:
        r = ar.refrescar(str(proy), "EXPLICIT_SOURCES_COMMAND",
                         canal={"kind": "archivo", "dir": str(ficha)})
        t.verdadero("E-04 refresco", r["refreshed"])
        entradas = rf.gestionadas(rf.cargar())
        from integraciones import fuentes as desc
        canal = {"reachable": True, "reason": "originales leidos de %s" % ficha,
                 "channel": "archivo:%s" % ficha}
        esperado = fr.documento(entradas, desc.observar_archivos(entradas, str(ficha)), canal, {})
        escrito = _fuentes(proy)
        for d in (esperado, escrito):
            d.pop("verified_at", None)
        t.igual("E-04 igual campo por campo salvo verified_at", json.loads(json.dumps(esperado)),
                escrito)
    finally:
        _limpiar(base)


def test_e05_e32_el_registro_no_se_toca(t):
    """E-05 (KRF-005), E-32 (KRF-032) — ni una version nueva cambia source-registry.json."""
    antes = REGISTRO.read_bytes()
    base, proy, ficha = _proyecto(archivos={PDF_63: "original ES0902 6.3"})
    try:
        r = ar.refrescar(str(proy), "EXPLICIT_SOURCES_COMMAND",
                         canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-05 la version nueva se vio", "UPDATE_AVAILABLE", _estado(proy))
        t.verdadero("E-05 refresco", r["refreshed"])
    finally:
        _limpiar(base)
    t.igual("E-05 source-registry.json byte por byte", antes, REGISTRO.read_bytes())
    # Del registro solo se lee: cargar, gestionadas y su excepcion.
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))
    usados = sorted({n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)
                     and isinstance(n.value, ast.Name) and n.value.id == "registro_fuentes"})
    t.igual("E-32 del registro solo lee", ["RegistroInvalido", "cargar", "gestionadas"], usados)
    t.igual("E-32 abre un solo archivo para escribir: el temporal de la agenda", 1,
            MODULO.read_text(encoding="utf-8").count('"w"'))


def test_e06_el_canonico_gana(t):
    """E-06 (KRF-006) — una agenda que contradice a harness.fuentes.json se reconstruye."""
    base, proy, ficha = _proyecto()
    try:
        ar.refrescar(str(proy), "EXPLICIT_SOURCES_COMMAND",
                     canal={"kind": "archivo", "dir": str(ficha)})
        agenda = _agenda(proy)
        agenda["sources"] = [{"id": "ES0902", "acceptedVersion": "9.9", "observedVersion": "9.9",
                              "sourceState": "CURRENT"}]
        _escribir(proy / ".claude" / "runtime" / "knowledge-refresh.json", agenda)
        doc = B.resolver(str(proy))
        t.igual("E-06 la bienvenida muestra el canonico", "FRESHNESS_UNVERIFIED",
                [f["state"] for f in doc["knowledge"]["sources"] if f["id"] == "ES0902"][0])
        r = ar.refrescar(str(proy), "PRE_NORMATIVE_OPERATION_IF_STALE")
        t.igual("E-06 no hacia falta refrescar", "AUTO_REFRESH_NOT_DUE", r["errorCode"])
        es = [s for s in _agenda(proy)["sources"] if s["id"] == "ES0902"][0]
        t.igual("E-06 la agenda se reconstruyo desde el canonico",
                {"id": "ES0902", "acceptedVersion": "6.2", "observedVersion": "6.2",
                 "sourceState": "FRESHNESS_UNVERIFIED"}, es)
        t.igual("E-06 sin mover las fechas", agenda["lastSuccessfulCheckAt"],
                _agenda(proy)["lastSuccessfulCheckAt"])
    finally:
        _limpiar(base)


# -- E-07 a E-12: vencimiento ------------------------------------------------------

def test_e07_a_e10_vencimiento(t):
    """E-07 (KRF-007), E-08 (KRF-008), E-09 (KRF-009), E-10 (KRF-010)."""
    ttl = _politica()
    t.igual("E-07 sin revision previa esta vencido", True, ar.vencido(ttl, None, "2026-09-29T10:00:00"))
    t.igual("E-07 tampoco con una agenda sin lastSuccessfulCheckAt", True,
            ar.vencido(ttl, {"lastSuccessfulCheckAt": None}, "2026-09-29T10:00:00"))
    agenda = {"lastSuccessfulCheckAt": "2026-09-28T10:00:00",
              "nextCheckDueAt": "2026-09-29T10:00:00"}
    t.igual("E-08 un segundo antes no vence", False, ar.vencido(ttl, agenda, "2026-09-29T09:59:59"))
    t.igual("E-09 en el limite exacto vence", True, ar.vencido(ttl, agenda, "2026-09-29T10:00:00"))
    t.igual("E-09 despues vence", True, ar.vencido(ttl, agenda, "2026-10-02T00:00:00"))
    solo = _politica(mode="EVENT_ONLY")
    t.igual("E-10 EVENT_ONLY no vence sin revision", False, ar.vencido(solo, None, "2030-01-01T00:00:00"))
    t.igual("E-10 EVENT_ONLY no vence pasado el limite", False,
            ar.vencido(solo, agenda, "2030-01-01T00:00:00"))
    t.igual("E-10 EVENT_ONLY: un evento igual refresca", (True, None),
            ar.debe_refrescar(solo, "INSTALL", agenda, "2030-01-01T00:00:00"))
    t.igual("E-10 EVENT_ONLY: lo que depende del vencimiento no", (False, "AUTO_REFRESH_NOT_DUE"),
            ar.debe_refrescar(solo, "PRE_NORMATIVE_OPERATION_IF_STALE", agenda,
                              "2030-01-01T00:00:00"))


def test_e11_politica_invalida(t):
    """E-11 (KRF-011) — una politica que no valida cae a la segura con su codigo."""
    base, proy, _ = _proyecto()
    try:
        casos = (("ilegible", "{ no es json"),
                 ("sin triggers", {k: v for k, v in _politica().items() if k != "triggers"}),
                 ("mode fuera del enum", _politica(mode="SIEMPRE")),
                 ("maxAgeHours 0", _politica(maxAgeHours=0)))
        for rotulo, contenido in casos:
            ruta = proy / "politica.json"
            _escribir(ruta, contenido)
            politica, codigo = ar.cargar_politica(str(proy), str(ruta))
            t.igual("E-11 %s: AUTO_REFRESH_POLICY_INVALID" % rotulo,
                    "AUTO_REFRESH_POLICY_INVALID", codigo)
            t.igual("E-11 %s: cae a EVENT_ONLY" % rotulo, "EVENT_ONLY", politica["mode"])
            t.igual("E-11 %s: solo el disparador explicito" % rotulo,
                    ["explicitSources"], sorted(k for k, v in politica["triggers"].items() if v))
            t.igual("E-11 %s: sin red en SessionStart" % rotulo, False,
                    politica["sessionStartNetwork"])
        _, codigo = ar.cargar_politica(str(proy), str(POLITICA))
        t.igual("E-11 la instalada si valida", None, codigo)
    finally:
        _limpiar(base)


def test_e12_la_politica_por_defecto(t):
    """E-12 (KRF-012) — sessionStartNetwork false, EVENT_AND_TTL, 24 horas, y valida."""
    p = json.loads(POLITICA.read_text(encoding="utf-8"))
    t.igual("E-12 sessionStartNetwork false", False, p["sessionStartNetwork"])
    t.igual("E-12 EVENT_AND_TTL", "EVENT_AND_TTL", p["mode"])
    t.igual("E-12 24 horas", 24, p["maxAgeHours"])
    t.igual("E-12 los cinco disparadores encendidos", 5, sum(1 for v in p["triggers"].values() if v))
    from orquestacion import tools
    armador = tools._armador()
    esquema = json.loads((RAIZ / "comun" / "schemas" / "knowledge-refresh-policy.schema.json")
                         .read_text(encoding="utf-8"))
    armador.controlar_soporte(esquema)
    t.vacio("E-12 valida contra su schema", armador.validar(p, esquema))
    t.verdadero("E-12 el validador ya lee minimum", bool(armador.validar(dict(p, maxAgeHours=0), esquema)))


# -- E-13 a E-18: disparadores -------------------------------------------------------

def _al_dia(proy):
    _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-29T09:00:00",
                     nextCheckDueAt="2099-01-01T00:00:00", lastAttemptAt="2026-09-29T09:00:00")


def test_e13_a_e16_los_eventos_refrescan_aunque_no_venza(t):
    """E-13 (KRF-013), E-14 (KRF-014), E-15 (KRF-015), E-16 (KRF-016)."""
    for escenario, disparador in (("E-13", "INSTALL"), ("E-14", "HARNESS_UPDATE"),
                                  ("E-15", "EXPLICIT_SOURCES_COMMAND"),
                                  ("E-16", "PRE_KNOWLEDGE_PROMOTION")):
        base, proy, ficha = _proyecto()
        try:
            _al_dia(proy)
            r = ar.refrescar(str(proy), disparador, canal={"kind": "archivo", "dir": str(ficha)})
            t.verdadero("%s %s refresca con la agenda al dia" % (escenario, disparador),
                        r["refreshed"])
            t.igual("%s la agenda anota el disparador" % escenario, disparador,
                    _agenda(proy)["trigger"])
            apagado = _politica()
            apagado["triggers"] = dict(apagado["triggers"], **{ar._INTERRUPTOR[disparador]: False})
            r = ar.refrescar(str(proy), disparador, canal={"kind": "archivo", "dir": str(ficha)},
                             politica=apagado)
            t.igual("%s apagado en la politica no refresca" % escenario,
                    "AUTO_REFRESH_TRIGGER_DISABLED", r["errorCode"])
        finally:
            _limpiar(base)
    base, proy, ficha = _proyecto()
    try:
        codigo, _, _ = _cli(proy, "fuentes", "--archivo", str(ficha))
        t.igual("E-15 fuentes a mano sale 0", 0, codigo)
        t.igual("E-15 fuentes a mano deja EXPLICIT_SOURCES_COMMAND", "EXPLICIT_SOURCES_COMMAND",
                _agenda(proy)["trigger"])
        t.verdadero("E-15 y cuenta como revision que salio bien",
                    bool(_agenda(proy)["lastSuccessfulCheckAt"]))
    finally:
        _limpiar(base)


def test_e17_la_operacion_normativa_refresca_si_vencio(t):
    """E-17 (KRF-017) — refresca vencida, no sale al canal si no vencio, y plan refresca antes."""
    base, proy, ficha = _proyecto()
    try:
        _al_dia(proy)
        r = ar.refrescar(str(proy), "PRE_NORMATIVE_OPERATION_IF_STALE",
                         canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-17 al dia: AUTO_REFRESH_NOT_DUE", "AUTO_REFRESH_NOT_DUE", r["errorCode"])
        t.igual("E-17 al dia: no escribe harness.fuentes.json", None, _fuentes(proy))
        llamado = []
        r = ar.refrescar(str(proy), "PRE_NORMATIVE_OPERATION_IF_STALE",
                         observar_jira=lambda *a: llamado.append(a),
                         capacidades=CAPACIDADES_OK, canal={"kind": "jira-ficha", "key": FICHA})
        t.igual("E-17 al dia: ni siquiera con Jira se sale al canal", [], llamado)
        _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-01T00:00:00",
                         nextCheckDueAt="2026-09-02T00:00:00", lastAttemptAt="2026-09-01T00:00:00")
        r = ar.refrescar(str(proy), "PRE_NORMATIVE_OPERATION_IF_STALE",
                         canal={"kind": "archivo", "dir": str(ficha)})
        t.verdadero("E-17 vencida: refresca", r["refreshed"])
    finally:
        _limpiar(base)
    # plan: con la agenda vencida y el canal local que dejo `fuentes`, refresca antes de planear.
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-01T00:00:00",
                         nextCheckDueAt="2026-09-02T00:00:00", lastAttemptAt="2026-09-01T00:00:00",
                         channel="archivo:%s" % ficha)
        codigo, _, err = _cli(proy, "plan", "GCBA-1", "--propuesta", "no-existe.json")
        agenda = _agenda(proy)
        t.igual("E-17 plan refresco con PRE_NORMATIVE_OPERATION_IF_STALE",
                "PRE_NORMATIVE_OPERATION_IF_STALE", agenda["trigger"])
        t.verdadero("E-17 plan movio la ultima revision",
                    agenda["lastSuccessfulCheckAt"] > "2026-09-01T00:00:00")
        t.igual("E-17 y despues siguio al plan (falta el contexto)", 2, codigo)
        t.contiene("E-17 el error es del plan, no de la compuerta", "no hay contexto", err)
    finally:
        _limpiar(base)


def test_e18_session_start_no_sale_a_la_red(t):
    """E-18 (KRF-018) — SessionStart y la bienvenida no importan nada de red ni el refresco."""
    for ruta in (SESSION_START, LIB):
        importados = _importados(ruta)
        for prohibido in ("auto_refresh", "http", "urllib", "urllib.request", "socket",
                          "integraciones.jira", "jira"):
            t.verdadero("E-18 %s no importa %s" % (ruta.name, prohibido),
                        prohibido not in importados)
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-01T00:00:00",
                         nextCheckDueAt="2026-09-02T00:00:00", lastAttemptAt="2026-09-01T00:00:00",
                         channel="archivo:%s" % ficha)
        antes, agenda_antes = _bytes_fuentes(proy), _texto_agenda(proy)
        entrada = json.dumps({"hook_event_name": "SessionStart", "cwd": str(proy),
                              "session_id": "sesion-krf"})
        r = subprocess.run([sys.executable, str(SESSION_START)], input=entrada.encode("utf-8"),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(proy))
        t.igual("E-18 el hook sale 0", 0, r.returncode)
        t.igual("E-18 harness.fuentes.json no cambio", antes, _bytes_fuentes(proy))
        t.igual("E-18 la agenda no cambio", agenda_antes, _texto_agenda(proy))
    finally:
        _limpiar(base)


# -- E-19 a E-22: capacidades -------------------------------------------------------

def test_e19_a_e22_capacidades(t):
    """E-19 (KRF-019), E-20 (KRF-020), E-21 (KRF-021), E-22 (KRF-022)."""
    base, proy = _proyecto_jira()
    try:
        jira = Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        codigo, _, _ = _auto_jira(proy, jira)
        t.igual("E-22 con las tres capacidades sale 0", 0, codigo)
        t.verdadero("E-22 con las tres capacidades sale al canal", len(jira.llamadas) > 0)
        # Una revision buena de otro dia: si una falla la moviera, se veria.
        buena = dict(_agenda(proy), lastSuccessfulCheckAt="2026-01-01T00:00:00",
                     nextCheckDueAt="2026-01-02T00:00:00")
        _escribir(proy / ".claude" / "runtime" / "knowledge-refresh.json", buena)
        fuentes_antes = _bytes_fuentes(proy)
        for capacidad in ("jira.issue.read", "jira.issue.search", "jira.attachment.read"):
            caps = dict(CAPACIDADES_OK, **{capacidad: "DISABLED"})
            _escribir(proy / ".claude" / "harness.capacidades.json",
                      {"schema_version": "integraciones/1.0",
                       "integraciones": {"jira": {"estado": "AVAILABLE", "motivo": "",
                                                  "verificado_en": "2026-09-29T09:00:00",
                                                  "capacidades": []}},
                       "capacidades": caps})
            otra = Jira([_adjunto()])
            codigo, salida, _ = _auto_jira(proy, otra, "--json")
            r = json.loads(salida)
            t.igual("E-19 sin %s: AUTO_REFRESH_BLOCKED_CAPABILITY" % capacidad,
                    "AUTO_REFRESH_BLOCKED_CAPABILITY", r["errorCode"])
            t.igual("E-19 sin %s: ni un pedido a Jira" % capacidad, [], otra.llamadas)
            agenda = _agenda(proy)
            t.igual("E-20 sin %s: conserva lastSuccessfulCheckAt" % capacidad,
                    buena["lastSuccessfulCheckAt"], agenda["lastSuccessfulCheckAt"])
            t.igual("E-20 sin %s: conserva nextCheckDueAt" % capacidad,
                    buena["nextCheckDueAt"], agenda["nextCheckDueAt"])
            t.igual("E-20 sin %s: harness.fuentes.json igual" % capacidad, fuentes_antes,
                    _bytes_fuentes(proy))
            t.verdadero("E-20 sin %s: anota el intento" % capacidad, bool(agenda["lastAttemptAt"]))
        # E-21: Jira AVAILABLE -lo que dejo la autenticacion- y la lectura de adjuntos DISABLED.
        t.igual("E-21 AVAILABLE sin jira.attachment.read sigue bloqueado",
                ["jira.attachment.read"],
                ar.faltan_capacidades(dict(CAPACIDADES_OK, **{"jira.attachment.read": "DISABLED"})))
        _escribir(proy / ".claude" / "harness.capacidades.json",
                  {"schema_version": "integraciones/1.0", "integraciones": {},
                   "capacidades": dict(CAPACIDADES_OK)})
        otra = Jira([_adjunto()])
        _auto_jira(proy, otra)
        t.verdadero("E-22 recuperadas, el refresco siguiente sale al canal", len(otra.llamadas) > 0)
        t.igual("E-22 y limpia el errorCode", None, _agenda(proy)["errorCode"])
    finally:
        _limpiar(base)


# -- E-23 a E-30: primero la metadata ---------------------------------------------------

def test_e23_e29_sin_cambios_no_se_baja_nada(t):
    """E-23 (KRF-023), E-29 (KRF-029) — la segunda vez, con la misma metadata, cero descargas."""
    base, proy = _proyecto_jira()
    try:
        jira = Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, jira)
        t.igual("E-23 la primera vez se baja una vez (misma version, identidad nueva)", 1,
                len(jira.bajadas))
        estados_1 = {k: v["state"] for k, v in _fuentes(proy)["sources"].items()}
        otra = Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, otra)
        t.igual("E-23 con la metadata igual no se baja nada", [], otra.bajadas)
        t.igual("E-29 los mismos estados", estados_1,
                {k: v["state"] for k, v in _fuentes(proy)["sources"].items()})
        # La segunda deja otra evidencia ("no se baja nada"); de ahi en mas, nada cambia.
        bytes_2 = _bytes_fuentes(proy)
        time.sleep(1.1)                            # otro segundo: otro verified_at si reescribe
        tercera =Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, tercera)
        t.igual("E-29 la tercera tampoco baja", [], tercera.bajadas)
        t.igual("E-29 y harness.fuentes.json ya no se reescribe", bytes_2, _bytes_fuentes(proy))
    finally:
        _limpiar(base)


def test_e24_a_e26_una_version_posterior(t):
    """E-24 (KRF-024), E-25 (KRF-025), E-26 (KRF-026)."""
    base, proy = _proyecto_jira()
    try:
        jira = Jira([_adjunto(PDF_63, aid="20002")])
        _auto_jira(proy, jira)
        t.igual("E-24 UPDATE_AVAILABLE", "UPDATE_AVAILABLE", _estado(proy))
        t.igual("E-24 sin bajar el documento", [], jira.bajadas)
        t.igual("E-25 el registro sigue diciendo 6.2", "6.2", rf.version_de("ES0902"))
        t.igual("E-25 ninguna decision", {}, _fuentes(proy)["decisions"])
        es = [s for s in _agenda(proy)["sources"] if s["id"] == "ES0902"][0]
        t.igual("E-25 la aceptada en la agenda es 6.2", "6.2", es["acceptedVersion"])
        t.igual("E-26 la observada va aparte", "6.3", es["observedVersion"])
        t.igual("E-26 con su estado", "UPDATE_AVAILABLE", es["sourceState"])
    finally:
        _limpiar(base)


def test_e27_e28_misma_version_otra_identidad(t):
    """E-27 (KRF-027), E-28 (KRF-028)."""
    base, proy = _proyecto_jira()
    try:
        primero = _adjunto()
        jira = Jira([primero], {primero["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, jira)
        otro = _adjunto(aid="30003", tam=25)
        jira = Jira([otro], {otro["content"]: b"otro contenido, misma version"})
        _auto_jira(proy, jira)
        t.igual("E-27 otra identidad con la misma version se baja una vez", 1, len(jira.bajadas))
        t.igual("E-27 y se hashea el original bajado",
                _sha(b"otro contenido, misma version"),
                _fuentes(proy)["sources"]["ES0902"]["observed_sha256"])
        t.verdadero("E-28 no queda CURRENT", _estado(proy) != "CURRENT")
    finally:
        _limpiar(base)
    # Con hash de fabrica, por el camino compartido: SOURCE_INTEGRITY_ALERT.
    tmp = Path(tempfile.mkdtemp(prefix="harness-61-"))
    try:
        entrada = dict(rf.buscar("ES0902"), sha256=_sha("el aceptado"))
        from integraciones import fuentes as desc

        def bajar(url, destino):
            _escribir(destino, b"reemplazado sin subir la version")
            return True, 1
        obs = desc.observar([entrada], [_adjunto()], {}, bajar, str(tmp / "d"))
        doc = ar.resolver_y_escribir([entrada], obs, {"reachable": True, "channel": "jira:X"}, {},
                                     str(tmp / "harness.fuentes.json"))
        t.igual("E-28 con hash de fabrica: SOURCE_INTEGRITY_ALERT", "SOURCE_INTEGRITY_ALERT",
                doc["sources"]["ES0902"]["state"])
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def test_e30_e66_misma_evidencia_mismos_estados(t):
    """E-30 (KRF-030), E-66 (KRF-066) — dos proyectos, manual y automatico, mismos estados."""
    archivos = {PDF_63: "original 6.3", "ES0901 - Estandar de Desarrollo V6.3.pdf": "es0901"}
    base1, p1, f1 = _proyecto(archivos=archivos)
    base2, p2, f2 = _proyecto(archivos=archivos)
    try:
        _cli(p1, "fuentes", "--archivo", str(f1))
        _cli(p2, "fuentes", "--auto", "--archivo", str(f2))
        e1 = {k: v["state"] for k, v in _fuentes(p1)["sources"].items()}
        e2 = {k: v["state"] for k, v in _fuentes(p2)["sources"].items()}
        t.igual("E-66 manual y automatico dan los mismos estados", e1, e2)
        t.igual("E-30 la misma evidencia da lo mismo en dos proyectos", e1, e2)
        t.igual("E-66 los dos terminan en la agenda", ["EXPLICIT_SOURCES_COMMAND"] * 2,
                [_agenda(p1)["trigger"], _agenda(p2)["trigger"]])
    finally:
        _limpiar(base1)
        _limpiar(base2)


# -- E-31 a E-35: decision humana -------------------------------------------------------

def test_e31_nunca_acepta(t):
    """E-31 (KRF-031) — el refresco no llama a nada que acepte."""
    llamadas = _llamadas_de(MODULO)
    for nombre in ("aceptable", "decision_de_aceptacion", "_aceptar", "aceptacion_vigente"):
        t.verdadero("E-31 no llama a %s" % nombre, nombre not in llamadas)
    base, proy, ficha = _proyecto(archivos={PDF_63: "original 6.3"})
    try:
        ar.refrescar(str(proy), "HARNESS_UPDATE", canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-31 UPDATE_AVAILABLE", "UPDATE_AVAILABLE", _estado(proy))
        t.igual("E-31 decisions queda vacio", {}, _fuentes(proy)["decisions"])
    finally:
        _limpiar(base)


def test_e33_e34_las_decisiones_se_conservan(t):
    """E-33 (KRF-033), E-34 (KRF-034)."""
    base, proy, ficha = _proyecto(archivos={PDF_63: "original 6.3"})
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        doc = _fuentes(proy)
        doc["decisions"]["ES0902"] = {"decision": "POSTPONE", "observed_version": "6.3",
                                      "observed_sha256": _sha("original 6.3"),
                                      "at": "2026-09-29T09:00:00"}
        _escribir(proy / ".claude" / "harness.fuentes.json", doc)
        ar.refrescar(str(proy), "EXPLICIT_SOURCES_COMMAND",
                     canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-33 pospuesta sigue ACKNOWLEDGED_PENDING", "ACKNOWLEDGED_PENDING", _estado(proy))
        t.igual("E-33 la decision POSTPONE sigue", "POSTPONE",
                _fuentes(proy)["decisions"]["ES0902"]["decision"])
    finally:
        _limpiar(base)
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902", "--por", "Ana Prueba")
        antes = _fuentes(proy)["decisions"]
        ar.refrescar(str(proy), "INSTALL", canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-34 la aceptacion se conserva con su by y su at", antes,
                _fuentes(proy)["decisions"])
        t.igual("E-34 atribuida a una persona", "Ana Prueba",
                _fuentes(proy)["decisions"]["ES0902"]["by"])
        t.igual("E-34 no aparece ninguna decision nueva", ["ES0902"],
                sorted(_fuentes(proy)["decisions"]))
    finally:
        _limpiar(base)


def test_e35_la_ficha_es_de_lectura(t):
    """E-35 (KRF-035) — el observador de Jira solo lee."""
    base, proy = _proyecto_jira()
    try:
        jira = Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, jira)
        t.verdadero("E-35 hubo pedidos", len(jira.llamadas) > 0)
        t.verdadero("E-35 todos a lecturas de la API", all(
            "/rest/api/3/issue/" in url for url, _ in jira.llamadas))
    finally:
        _limpiar(base)
    llamadas = _llamadas_de(MODULO)
    for verbo in ("post", "put", "delete", "comentar", "transicionar", "subir"):
        t.verdadero("E-35 auto_refresh.py no llama a %s" % verbo, verbo not in llamadas)


# -- E-36 a E-40: promocion --------------------------------------------------------

def test_e36_promocion_incompleta(t):
    """E-36 (KRF-036) — aceptada 6.3 y el extracto en 6.2: KNOWLEDGE_PROMOTION_INCOMPLETE."""
    base, proy, ficha = _proyecto(archivos={PDF_63: "original 6.3"})
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902", "--por", "Ana")
        ar.refrescar(str(proy), "EXPLICIT_SOURCES_COMMAND",
                     canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-36 KNOWLEDGE_PROMOTION_INCOMPLETE", "KNOWLEDGE_PROMOTION_INCOMPLETE",
                _estado(proy))
    finally:
        _limpiar(base)


def test_e37_a_e40_nada_derivado_se_reescribe(t):
    """E-37 (KRF-037), E-38 (KRF-038), E-39 (KRF-039), E-40 (KRF-040)."""
    carpetas = [RAIZ / "harnesses", RAIZ / "comun" / "checks", RAIZ / "comun" / "agents",
                RAIZ / "comun" / "skills", RAIZ / "comun" / "reglas", RAIZ / "normativa"]
    antes = _huellas_de(carpetas)
    base, proy, ficha = _proyecto(archivos={PDF_63: "original 6.3"})
    try:
        for disparador in ("INSTALL", "HARNESS_UPDATE", "PRE_KNOWLEDGE_PROMOTION"):
            ar.refrescar(str(proy), disparador, canal={"kind": "archivo", "dir": str(ficha)})
        _cli(proy, "fuentes", "--auto", "--archivo", str(ficha))
    finally:
        _limpiar(base)
    despues = _huellas_de(carpetas)
    cambiados = sorted(k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k))
    for escenario, que in (("E-37", "reglas"), ("E-38", "policies"), ("E-39", "checks"),
                           ("E-40", "agents")):
        t.igual("%s ningun archivo de %s cambio" % (escenario, que), [],
                [c for c in cambiados if que in c.replace("\\", "/")])
    t.igual("E-40 ni skills, reviews ni nada del arbol", [], cambiados)


# -- E-41 a E-45: la compuerta ------------------------------------------------------

def _fuentes_doc(estados, canal=None):
    return {"schema_version": "sources-state/1.1", "verified_at": "2026-09-29T09:00:00",
            "ficha": canal, "decisions": {}, "pending_count": 0, "warnings": [],
            "sources": {sid: {"state": e, "registry_version": "1.0", "observed_version": "1.0",
                              "blocking": e not in ("CURRENT", "RETIRED")}
                        for sid, e in estados.items()}}


def test_e41_a_e43_la_compuerta(t):
    """E-41 (KRF-041), E-42 (KRF-042), E-43 (KRF-043)."""
    base, proy, _ = _proyecto()
    try:
        _escribir(proy / ".claude" / "harness.fuentes.json",
                  _fuentes_doc({"ES0901": "CURRENT", "ES0902": "CURRENT", "Viejo": "RETIRED"}))
        _al_dia(proy)
        v = ar.ensure_normative_knowledge_fresh(str(proy))
        t.igual("E-41 todo CURRENT o RETIRED y al dia: allowed", "allowed", v["decision"])
        for estado in ("SOURCE_INTEGRITY_ALERT", "SOURCE_CHANGED_SAME_VERSION",
                       "VERSION_REGRESSION"):
            _escribir(proy / ".claude" / "harness.fuentes.json",
                      _fuentes_doc({"ES0901": "CURRENT", "ES0902": estado}))
            v = ar.ensure_normative_knowledge_fresh(str(proy))
            t.igual("E-42 %s: blocked" % estado, "blocked", v["decision"])
            codigo, _, err = _cli(proy, "plan", "GCBA-1", "--propuesta", "x.json")
            t.igual("E-42 %s: plan sale 2" % estado, 2, codigo)
            t.contiene("E-42 %s: por la compuerta" % estado, "conocimiento normativo no se puede usar", err)
            t.verdadero("E-42 %s: sin plan escrito" % estado,
                        not (proy / ".claude" / "planes").exists())
        _escribir(proy / ".claude" / "harness.fuentes.json",
                  _fuentes_doc({"ES0901": "CURRENT", "ES0902": "CURRENT"}))
        _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-01T00:00:00",
                         nextCheckDueAt="2026-09-02T00:00:00", lastAttemptAt="2026-09-01T00:00:00")
        v = ar.ensure_normative_knowledge_fresh(str(proy))
        t.igual("E-43 vencida y sin poder refrescar: unresolved", "unresolved", v["decision"])
        t.igual("E-43 con el codigo del refresco", "AUTO_REFRESH_CHANNEL_UNAVAILABLE",
                v["refresh"]["errorCode"])
        t.igual("E-43 y el estado conocido sigue CURRENT, sin reinterpretar", "CURRENT",
                _estado(proy))
    finally:
        _limpiar(base)


def test_e44_lo_que_no_es_normativo_no_pasa(t):
    """E-44 (KRF-044) — contexto, estado y harness no llaman a la compuerta; plan en unresolved sigue."""
    modulo = _cargar("dev_harness_krf_fuente", CLI)
    for nombre in ("resolver_contexto", "mostrar_harness", "mostrar", "correr_bootstrap",
                   "contabilizar"):
        t.verdadero("E-44 %s no llama a la compuerta" % nombre,
                    "compuerta_normativa" not in inspect.getsource(getattr(modulo, nombre)))
    fuente = inspect.getsource(modulo.comando)
    t.igual("E-44 comando llama a la compuerta tres veces: plan, seguridad, refute", 3,
            fuente.count("compuerta_normativa("))
    base, proy, _ = _proyecto()
    try:
        codigo, salida, err = _cli(proy, "plan", "GCBA-1", "--propuesta", "x.json")
        t.contiene("E-44 sin estado: la compuerta avisa", "SIN RESOLVER", salida + err)
        t.contiene("E-44 y el plan sigue hasta su propio error", "no hay contexto", err)
        codigo, _, _ = _cli(proy, "harness")
        t.igual("E-44 harness sale 0 sin canal", 0, codigo)
    finally:
        _limpiar(base)


def test_e45_e60_una_falla_conserva_lo_sabido(t):
    """E-45 (KRF-045), E-60 (KRF-060)."""
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902", "--por", "Ana")
        antes, agenda = _bytes_fuentes(proy), _agenda(proy)
        shutil.rmtree(str(ficha))
        r = ar.refrescar(str(proy), "INSTALL", canal={"kind": "archivo", "dir": str(ficha)},
                         momento="2030-01-01T00:00:00")
        t.verdadero("E-45 el refresco no pudo", not r["refreshed"])
        t.igual("E-45 harness.fuentes.json igual byte por byte", antes, _bytes_fuentes(proy))
        t.igual("E-45 la version aceptada sigue", "6.2",
                _fuentes(proy)["decisions"]["ES0902"]["observed_version"])
        t.igual("E-60 lastSuccessfulCheckAt no se movio", agenda["lastSuccessfulCheckAt"],
                _agenda(proy)["lastSuccessfulCheckAt"])
    finally:
        _limpiar(base)


# -- E-46 a E-52: bienvenida ----------------------------------------------------------

def _bienvenida_con(proy, estados_versiones):
    doc = {"schema_version": "sources-state/1.1", "verified_at": "2026-09-29T09:00:00",
           "ficha": None, "decisions": {}, "pending_count": 0, "warnings": [], "sources": {}}
    for sid, (estado, registro, observada, aceptada) in estados_versiones.items():
        e = {"state": estado, "registry_version": registro, "observed_version": observada,
             "blocking": estado not in ("CURRENT", "RETIRED"), "attachmentId": "1",
             "filename": sid + ".pdf", "size": 1, "created": None, "observed_sha256": None}
        if aceptada:
            e["acceptance"] = {"version": aceptada}
        doc["sources"][sid] = e
    _escribir(proy / ".claude" / "harness.fuentes.json", doc)


def _linea(texto, aguja):
    for l in texto.splitlines():
        if aguja in l:
            return l
    return ""


def test_e46_a_e48_versiones(t):
    """E-46 (KRF-046), E-47 (KRF-047), E-48 (KRF-048)."""
    base, proy, _ = _proyecto()
    try:
        _bienvenida_con(proy, {"ES0901": ("UPDATE_AVAILABLE", "6.3", "6.4", None),
                               "ES0902": ("CURRENT", "6.1", "6.2", "6.2")})
        doc = B.resolver(str(proy))
        completa = B.renderizar_bienvenida(doc)
        t.contiene("E-47 la linea de ES0901", "ES0901 6.3    ACTUALIZACIÓN DISPONIBLE → 6.4",
                   completa)
        l02 = _linea(completa, "ES0902 6.")
        t.contiene("E-46 ES0902 muestra la aceptada del proyecto, no la de fabrica", "ES0902 6.2", l02)
        t.contiene("E-46 ACTUAL", "ACTUAL", l02)
        l01 = _linea(completa, "ES0901 6.")
        t.verdadero("E-48 la observada no va a la izquierda", l01.strip().startswith("ES0901 6.3")
                    or "Versiones" in l01 and "ES0901 6.3" in l01)
        t.verdadero("E-48 ni junto a ACTUAL", "6.4" not in l01.split("→")[0])
        es = [f for f in doc["knowledge"]["sources"] if f["id"] == "ES0901"][0]
        t.igual("E-46 knowledge lleva acceptedVersion", "6.3", es["acceptedVersion"])
        t.igual("E-47 y observedVersion aparte", "6.4", es["observedVersion"])
    finally:
        _limpiar(base)


def test_e49_e50_vencida_y_sin_verificar(t):
    """E-49 (KRF-049), E-50 (KRF-050)."""
    base, proy, _ = _proyecto()
    try:
        _bienvenida_con(proy, {"ES0902": ("FRESHNESS_UNVERIFIED", "6.2", "6.2", None)})
        _escribir_agenda(proy, lastSuccessfulCheckAt="2026-09-01T00:00:00",
                         nextCheckDueAt="2026-09-02T00:00:00", lastAttemptAt="2026-09-01T00:00:00")
        antes = _bytes_fuentes(proy)
        doc = B.resolver(str(proy))
        completa = B.renderizar_bienvenida(doc)
        t.contiene("E-49 la revision vencida se ve", "Revisión     VENCIDA", completa)
        t.no_contiene("E-49 sin decir que se verifico", "al día hasta", completa)
        t.igual("E-49 due en el estado", True, doc["knowledgeRefresh"]["due"])
        t.igual("E-49 el estado de la fuente no cambia", "FRESHNESS_UNVERIFIED",
                doc["knowledge"]["sources"][0]["state"])
        t.igual("E-49 y harness.fuentes.json tampoco", antes, _bytes_fuentes(proy))
        t.contiene("E-50 FRESHNESS_UNVERIFIED se ve", "VIGENCIA SIN VERIFICAR", completa)
        _escribir_agenda(proy, state="UNRESOLVED", errorCode="AUTO_REFRESH_TIMEOUT",
                         lastAttemptAt="2026-09-29T09:00:00")
        doc = B.resolver(str(proy))
        t.verdadero("E-50 el refresco fallido queda pendiente con su codigo",
                    "KNOWLEDGE_REFRESH_UNRESOLVED:AUTO_REFRESH_TIMEOUT"
                    in doc["bootstrap"]["pendingConditions"])
        t.igual("E-50 PARTIAL, no BLOCKED", "PARTIAL", doc["bootstrap"]["status"])
        t.contiene("E-50 y la bienvenida lo dice", "AUTO_REFRESH_TIMEOUT",
                   B.renderizar_bienvenida(doc))
    finally:
        _limpiar(base)


def test_e51_e52_un_aviso_por_novedad(t):
    """E-51 (KRF-051), E-52 (KRF-052) — por session-start.py, sesion tras sesion."""
    base, proy, _ = _proyecto()

    def sesion():
        entrada = json.dumps({"hook_event_name": "SessionStart", "cwd": str(proy),
                              "session_id": "s-" + uuid.uuid4().hex[:6]})
        r = subprocess.run([sys.executable, str(SESSION_START)], input=entrada.encode("utf-8"),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(proy))
        return r.stdout.decode("utf-8", "replace")
    try:
        _bienvenida_con(proy, {"ES0901": ("UPDATE_AVAILABLE", "6.3", "6.4", None)})
        sesion()                                   # la bienvenida completa, la primera vez
        segunda = sesion()
        t.no_contiene("E-51 ya avisado en la completa, la segunda no lo repite",
                      "hay novedades", segunda)
        tercera = sesion()
        t.no_contiene("E-51 la tercera tampoco", "hay novedades", tercera)
        _bienvenida_con(proy, {"ES0901": ("UPDATE_AVAILABLE", "6.3", "6.5", None)})
        cuarta = sesion()
        t.contiene("E-52 otra version observada vuelve a avisar", "hay novedades", cuarta)
        t.contiene("E-52 con la version nueva", "6.5", cuarta)
        t.no_contiene("E-51 y despues vuelve a callar", "hay novedades", sesion())
        h1 =B.huella_de_notificacion(_fuentes(proy))
        otra = _fuentes(proy)
        otra["sources"]["ES0901"]["attachmentId"] = "999"
        t.verdadero("E-52 otro adjunto cambia la huella", h1 != B.huella_de_notificacion(otra))
    finally:
        _limpiar(base)


# -- E-53 a E-58: secretos ------------------------------------------------------------

def test_e53_a_e57_la_agenda_no_lleva_secretos(t):
    """E-53 (KRF-053), E-54 (KRF-054), E-55 (KRF-055), E-56 (KRF-056), E-57 (KRF-057)."""
    import base64
    base, proy = _proyecto_jira()
    try:
        jira = Jira([_adjunto()], {_adjunto()["content"]: b"original ES0902 6.2"})
        _auto_jira(proy, jira)
        texto = _texto_agenda(proy)
        credencial = base64.b64encode(("%s:%s" % (USUARIO, TOKEN)).encode()).decode()
        t.verdadero("E-57 el pedido llevo la credencial del adaptador",
                    any(h.get("Authorization") == "Basic " + credencial for _, h in jira.llamadas))
        t.no_contiene("E-53 sin el token", TOKEN, texto)
        t.no_contiene("E-54 sin Authorization", "Authorization", texto)
        t.no_contiene("E-54 sin Basic", "Basic ", texto)
        t.no_contiene("E-54 sin la credencial", credencial, texto)
        t.no_contiene("E-55 sin el cuerpo de Jira", '"fields"', texto)
        t.no_contiene("E-55 ni la URL del adjunto", "attachment/content", texto)
        claves = set(json.loads(texto))
        t.igual("E-55 solo las claves de la agenda", {
            "schema_version", "state", "lastAttemptAt", "lastSuccessfulCheckAt", "nextCheckDueAt",
            "trigger", "errorCode", "channel", "notificationFingerprint", "sources"}, claves)
    finally:
        _limpiar(base)
    fuente = MODULO.read_text(encoding="utf-8")
    for prohibido in (".env", "AlmacenSecretos", "entorno", "almacen"):
        t.no_contiene("E-56 auto_refresh.py no menciona %s" % prohibido, prohibido, fuente)
    cli = _cargar("dev_harness_krf_e57", CLI)
    observador = inspect.getsource(cli._observador_de_jira)
    t.contiene("E-57 el observador arma el adaptador con armar", "armar(IntegracionJira", observador)
    t.contiene("E-57 y las capacidades salen del registro", 'rutas["capacidades"]',
               inspect.getsource(cli._capacidades))
    t.contiene("E-57 que es harness.capacidades.json", "harness.capacidades.json",
               inspect.getsource(cli.rutas_de))


def test_e58_las_protecciones_no_cambian(t):
    """E-58 (KRF-058) — pre-tool-use.py, secretos.py y permisos-por-capacidad.json como en 0.26.0."""
    for relativa in ("comun/hooks/pre-tool-use.py", "comun/hooks/lib/secretos.py",
                     "harnesses/desarrollo/reglas/permisos-por-capacidad.json"):
        r = subprocess.run(["git", "-C", str(RAIZ), "diff", "--quiet", BASE_0260, "--", relativa])
        t.igual("E-58 %s sin cambios desde 0.26.0" % relativa, 0, r.returncode)


# -- E-59 a E-64: fallas y escritura -----------------------------------------------------

def test_e59_timeout(t):
    """E-59 (KRF-059) — un timeout del canal queda AUTO_REFRESH_TIMEOUT y UNRESOLVED."""
    import socket
    base, proy = _proyecto_jira()
    try:
        jira = Jira([], error=socket.timeout("lento"))
        codigo, salida, _ = _auto_jira(proy, jira, "--json")
        t.igual("E-59 sale 0", 0, codigo)
        t.igual("E-59 AUTO_REFRESH_TIMEOUT", "AUTO_REFRESH_TIMEOUT", json.loads(salida)["errorCode"])
        t.igual("E-59 la agenda UNRESOLVED", "UNRESOLVED", _agenda(proy)["state"])
        t.igual("E-59 con el codigo", "AUTO_REFRESH_TIMEOUT", _agenda(proy)["errorCode"])
    finally:
        _limpiar(base)


def test_e61_e62_fechas(t):
    """E-61 (KRF-061), E-62 (KRF-062)."""
    base, proy, ficha = _proyecto()
    try:
        ar.refrescar(str(proy), "INSTALL", canal={"kind": "archivo", "dir": str(ficha)},
                     momento="2026-09-29T08:00:00")
        a = _agenda(proy)
        t.igual("E-61 lastSuccessfulCheckAt es la hora del refresco", "2026-09-29T08:00:00",
                a["lastSuccessfulCheckAt"])
        t.igual("E-62 nextCheckDueAt es mas 24 horas", "2026-09-30T08:00:00", a["nextCheckDueAt"])
        ar.refrescar(str(proy), "INSTALL", canal={"kind": "archivo", "dir": str(ficha)},
                     momento="2026-09-29T09:30:00", politica=_politica(mode="EVENT_ONLY"))
        t.igual("E-62 EVENT_ONLY: sin proxima", None, _agenda(proy)["nextCheckDueAt"])
        ar.refrescar(str(proy), "INSTALL", canal={"kind": "archivo", "dir": str(ficha)},
                     momento="2026-09-29T09:30:00", politica=_politica(maxAgeHours=6))
        t.igual("E-62 con 6 horas", "2026-09-29T15:30:00", _agenda(proy)["nextCheckDueAt"])
    finally:
        _limpiar(base)


def test_e63_agenda_rota(t):
    """E-63 (KRF-063) — rota se informa, cuenta como nunca revisada, y se reescribe."""
    base, proy, ficha = _proyecto()
    try:
        _escribir(proy / ".claude" / "runtime" / "knowledge-refresh.json", "{ roto")
        agenda, codigo = ar.leer_agenda(str(proy))
        t.igual("E-63 AUTO_REFRESH_STATE_UNREADABLE", "AUTO_REFRESH_STATE_UNREADABLE", codigo)
        t.igual("E-63 cuenta como nunca revisada", True,
                ar.vencido(_politica(), agenda, "2026-09-29T10:00:00"))
        doc = B.resolver(str(proy))
        t.verdadero("E-63 la bienvenida lo muestra",
                    "KNOWLEDGE_REFRESH_STATE_UNREADABLE" in doc["bootstrap"]["pendingConditions"])
        r = ar.refrescar(str(proy), "PRE_NORMATIVE_OPERATION_IF_STALE",
                         canal={"kind": "archivo", "dir": str(ficha)})
        t.igual("E-63 el resultado lo dice", "AUTO_REFRESH_STATE_UNREADABLE", r["stateError"])
        _, codigo = ar.leer_agenda(str(proy))
        t.igual("E-63 y el refresco la reescribe valida", None, codigo)
    finally:
        _limpiar(base)


def test_e64_escrituras_concurrentes(t):
    """E-64 (KRF-064) — ocho escritores a la vez dejan un JSON valido y ningun temporal."""
    base, proy, _ = _proyecto()
    try:
        ruta = str(proy / ".claude" / "runtime" / "knowledge-refresh.json")
        errores = []

        def escritor(n):
            for i in range(10):
                agenda = {"schema_version": "knowledge-refresh-state/1.0", "state": "CURRENT",
                          "lastAttemptAt": "2026-09-29T10:00:%02d" % i,
                          "lastSuccessfulCheckAt": None, "nextCheckDueAt": None,
                          "trigger": "INSTALL", "errorCode": None,
                          "sources": [{"id": "H%d" % n, "acceptedVersion": None,
                                       "observedVersion": None, "sourceState": "CURRENT"}] * 50}
                try:
                    ar.escribir_agenda(ruta, agenda)
                except Exception as e:             # noqa: BLE001
                    errores.append(repr(e))
        hilos = [threading.Thread(target=escritor, args=(n,)) for n in range(8)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        t.igual("E-64 ninguna escritura fallo", [], errores)
        _, codigo = ar.leer_agenda(str(proy))
        t.igual("E-64 el JSON valida", None, codigo)
        t.igual("E-64 ningun temporal", [], [n for n in os.listdir(os.path.dirname(ruta))
                                             if n.endswith(".tmp")])
    finally:
        _limpiar(base)


# -- E-65 a E-69: CLI ------------------------------------------------------------------

def test_e65_fuentes_a_mano_como_siempre(t):
    """E-65 (KRF-065) — con --archivo y sin canal, lo mismo que en 0.26.0."""
    base, proy, ficha = _proyecto()
    try:
        codigo, salida, _ = _cli(proy, "fuentes", "--archivo", str(ficha))
        t.igual("E-65 --archivo sale 0", 0, codigo)
        t.contiene("E-65 muestra las fuentes", "Fuentes gestionadas", salida)
        t.igual("E-65 ES0902 como siempre", "FRESHNESS_UNVERIFIED", _estado(proy))
        codigo, salida, _ = _cli(proy, "fuentes")
        t.igual("E-65 sin canal sale 0", 0, codigo)
        t.contiene("E-65 sin canal lo dice", "no hay canal que consultar", salida)
        t.verdadero("E-65 y cada fuente queda sin verificar", all(
            f["state"] in ("FRESHNESS_UNVERIFIED", "RETIRED")
            for f in _fuentes(proy)["sources"].values()))
        t.igual("E-65 la agenda anota el intento sin canal", "AUTO_REFRESH_CHANNEL_UNAVAILABLE",
                _agenda(proy)["errorCode"])
    finally:
        _limpiar(base)


def test_e67_harness_verbose(t):
    """E-67 (KRF-067) — la agenda y las versiones, sin un valor del .env."""
    base, proy, ficha = _proyecto(env=ENV, archivos={PDF_63: "original 6.3"})
    try:
        _cli(proy, "fuentes", "--auto", "--archivo", str(ficha))
        codigo, salida, _ = _cli(proy, "harness", "--verbose")
        t.igual("E-67 sale 0", 0, codigo)
        for etiqueta in ("Revisión: modo", "EVENT_AND_TTL", "Última que salió", "Próxima",
                         "Disparador", "EXPLICIT_SOURCES_COMMAND", "Error de revisión"):
            t.contiene("E-67 muestra %s" % etiqueta, etiqueta, salida)
        t.contiene("E-67 las versiones de ES0902", "ES0902 UPDATE_AVAILABLE, aceptada 6.2, observada 6.3",
                   salida)
        for valor in (TOKEN, USUARIO, URL_JIRA):
            t.no_contiene("E-67 sin %s" % valor[:12], valor, salida)
    finally:
        _limpiar(base)


def test_e69_el_update_no_acepta(t):
    """E-69 (KRF-069) — HARNESS_UPDATE con una version nueva no acepta nada."""
    base, proy, ficha = _proyecto(archivos={PDF_63: "original 6.3"})
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        codigo, _, _ = _cli(proy, "fuentes", "--auto", "--disparador", "HARNESS_UPDATE")
        t.igual("E-69 sale 0", 0, codigo)
        t.igual("E-69 sigue UPDATE_AVAILABLE", "UPDATE_AVAILABLE", _estado(proy))
        t.igual("E-69 sin decisiones", {}, _fuentes(proy)["decisions"])
        t.igual("E-69 con el disparador", "HARNESS_UPDATE", _agenda(proy)["trigger"])
        codigo, _, err = _cli(proy, "fuentes", "--auto", "--disparador", "APPLY")
        t.igual("E-69 un disparador inventado sale 2", 2, codigo)
    finally:
        _limpiar(base)
