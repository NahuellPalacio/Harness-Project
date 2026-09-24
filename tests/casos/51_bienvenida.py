# La bienvenida del harness y el estado general de la instalacion: el resolvedor unico
# (comun/hooks/lib/bienvenida.py), sus dos renderizadores y session-start.py punta a punta.
#
# Spec: docs/cambios/bloque-1-bienvenida/spec.md. Cada test nombra su escenario.
#
# Lo del instalador (E-01, E-18 y E-19 del lado de install.ps1, E-24 y la mitad de E-02) va en
# tests/casos/03-instalador.ps1. Lo de `dev-harness.py harness` y `setup` (E-12 en la CLI, E-13,
# E-14, E-19 con --reiniciar-bienvenida, E-21) va al final de este archivo.
import ast
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"
HOOK = HOOKS / "session-start.py"
LIB = HOOKS / "lib" / "bienvenida.py"
SCHEMA = RAIZ / "comun" / "schemas" / "harness-installation-state.schema.json"
CATALOGO = RAIZ / "comun" / "reglas" / "secretos.patrones.json"

# El ultimo commit de session-start.py antes de este cambio. E-20 compara contra el hook de
# ESE commit y no contra HEAD: cuando este cambio se commitee, HEAD va a ser el hook nuevo y la
# comparacion pasaria contra si misma.
ANTES = "aeba455"

# Un token con la forma que el catalogo reconoce (token-gitlab), armado por partes: un fuente
# que dispara el detector de secretos no se puede editar donde el harness esta instalado.
TOKEN = "glp" + "at-" + "Q7w8E9r0T1y2U3i4O5p6A7s8"


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


B = _cargar("bienvenida_51", LIB)
ARMADOR = _cargar("armador_51", RAIZ / "comun" / "bin" / "contexto-armar.py")
SECRETOS_CATALOGO = json.loads(CATALOGO.read_text(encoding="utf-8"))

TODAS = ("ES0901", "ES0902", "ES0903", "GuiaDGISIS", "Obelisco", "PC0901")

# Los ids que la tabla de etiquetas traduce, mas el de la integracion nunca verificada.
IDS_TRADUCIDOS = ("READY", "PARTIAL", "BLOCKED", "AVAILABLE", "NOT_CONFIGURED",
                  "AUTHENTICATION_FAILED", "CONNECTION_FAILED", "PERMISSION_DENIED",
                  "UNRESOLVED", "CURRENT", "UPDATE_AVAILABLE", "ACKNOWLEDGED_PENDING",
                  "SOURCE_INTEGRITY_ALERT", "FRESHNESS_UNVERIFIED")

_LISTO = re.compile(r"list[oa]s?", re.IGNORECASE)


# -- el proyecto de prueba -----------------------------------------------------

def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def _json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False))


def _proyecto(harness=("comun", "desarrollo"), version="0.20.0", jira="AVAILABLE",
              gitlab="AVAILABLE", fuentes=None, capacidades=True, fuentes_archivo=True,
              instalacion=None, nombre=None, lock=True, usuario="Nahue"):
    """Un proyecto como lo deja install.ps1, en READY salvo lo que se pida.

    `jira`/`gitlab` en None: la integracion no figura en el registro. `fuentes` es
    {id: state}; por defecto las seis en CURRENT. `instalacion` es un dict o un texto crudo.
    """
    proy = Path(tempfile.gettempdir()) / ("harness-bv-" + uuid.uuid4().hex[:8])
    claude = proy / ".claude"
    _json(claude / "harness.config.json", {"usuario": usuario})
    if lock:
        _json(claude / "harness.lock.json",
              {"version": version, "harness": list(harness), "instalado": "2026-09-24 10:00:00",
               "archivos": []})
    if capacidades:
        integ = {}
        for n, e in (("jira", jira), ("gitlab", gitlab)):
            if e is not None:
                integ[n] = {"estado": e, "motivo": "", "verificado_en": "2026-09-24T10:00:00",
                            "capacidades": []}
        _json(claude / "harness.capacidades.json",
              {"schema_version": "integraciones/1.0", "version_harness": version,
               "integraciones": integ, "capacidades": {}})
    if fuentes_archivo:
        estados = fuentes if fuentes is not None else {s: "CURRENT" for s in TODAS}
        _json(claude / "harness.fuentes.json", _fuentes_doc(estados))
    if instalacion is not None:
        ruta = claude / "harness.installation.json"
        if isinstance(instalacion, str):
            _escribir(ruta, instalacion)
        else:
            _json(ruta, instalacion)
    if nombre is not None:
        _json(proy / "docs" / "codebase" / "project-context.json",
              {"project_profile": {"project_id": "x", "project_name": nombre}})
    return proy


def _fuentes_doc(estados):
    return {"schema_version": "sources-state/1.1", "verified_at": "2026-09-23T12:00:00",
            "ficha": None, "decisions": {}, "warnings": [],
            "pending_count": sum(1 for e in estados.values() if e not in ("CURRENT", "RETIRED")),
            "sources": {s: _fuente(e) for s, e in estados.items()}}


def _fuente(estado):
    """Una fuente con la forma que escribe frescura.resolver_una (source-state.schema.json)."""
    return {"state": estado, "registry_version": "6.3", "observed_version": None,
            "attachmentId": None, "filename": None, "size": None, "created": None,
            "observed_sha256": None, "registry_sha256": None, "downloaded": False,
            "effectiveRisk": "MEDIUM", "derived_impact": [], "stale_derived": [],
            "blocking": estado not in ("CURRENT", "RETIRED"), "evidence": []}


def _instalacion_vista(version="0.20.0", upgrade=None):
    doc = {"schema_version": "harness-installation/1.0", "installed": True,
           "harnessId": "desarrollo", "installedVersion": version,
           "installedAt": "2026-09-01T10:00:00",
           "bootstrap": {"status": "READY", "blockingConditions": [], "pendingConditions": []},
           "welcome": {"firstRunShown": True, "lastShownAt": "2026-09-20T10:00:00"}}
    if upgrade:
        doc["welcome"]["upgradeFrom"] = upgrade
    return doc


def _sesion(proy, env=None, hook=HOOK, comando=None):
    """Corre session-start.py como lo invoca Claude Code. (codigo, systemMessage, contexto)."""
    payload = {"session_id": "s-" + uuid.uuid4().hex[:6], "cwd": str(proy),
               "hook_event_name": "SessionStart", "source": "startup"}
    entorno = dict(os.environ)
    entorno.update(env or {})
    r = subprocess.run(comando or [sys.executable, str(hook)],
                       input=json.dumps(payload).encode("utf-8"),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=entorno)
    crudo = r.stdout.decode("utf-8")
    if not crudo.strip():
        return r.returncode, None, None, crudo
    salida = json.loads(crudo)
    ctx = (salida.get("hookSpecificOutput") or {}).get("additionalContext")
    return r.returncode, salida.get("systemMessage"), ctx, crudo


def _estado(proy):
    return json.loads((proy / ".claude" / "harness.installation.json").read_text(encoding="utf-8"))


def _textos(proy):
    doc = B.resolver(str(proy))
    return doc, B.renderizar_bienvenida(doc), B.renderizar_linea(doc)


def _validar(doc):
    esquema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ARMADOR.controlar_soporte(esquema)
    return ARMADOR.validar(doc, esquema)


def _linea_de(texto, rotulo):
    for linea in texto.split("\n"):
        if linea.strip().startswith(rotulo):
            return linea
    return ""


# -- E-02 — lo que escribe el hook valida contra el schema --------------------------------

def test_e02_el_estado_que_escribe_el_hook_valida(t):
    """E-02 (la mitad del hook) — el archivo que reescribe session-start.py valida contra
    harness-installation-state.schema.json, en los tres estados. La mitad del instalador va en
    su caso."""
    esquema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ARMADOR.controlar_soporte(esquema)
    t.verdadero("E-02 el schema declara pendingConditions",
                "pendingConditions" in esquema["properties"]["bootstrap"]["properties"])
    for rotulo, kwargs in (("READY", {}), ("PARTIAL", {"jira": "NOT_CONFIGURED"}),
                           ("BLOCKED", {"fuentes": dict({s: "CURRENT" for s in TODAS},
                                                        ES0902="SOURCE_INTEGRITY_ALERT")})):
        proy = _proyecto(**kwargs)
        codigo, _, _, _ = _sesion(proy)
        t.igual("E-02 %s: el hook sale 0" % rotulo, 0, codigo)
        doc = _estado(proy)
        t.igual("E-02 %s: el estado es el esperado" % rotulo, rotulo, doc["bootstrap"]["status"])
        t.vacio("E-02 %s: valida contra el schema" % rotulo, _validar(doc))
    # Y lo que va a llamar el instalador, la misma API.
    proy = _proyecto()
    doc = B.registrar_instalacion(str(proy))
    t.vacio("E-02 registrar_instalacion escribe algo que valida", _validar(_estado(proy)))
    t.igual("E-02 y es instalacion nueva", False, doc["welcome"]["firstRunShown"])


# -- E-03 / E-04 — la primera sesion y la segunda ----------------------------------------

def test_e03_la_primera_sesion_muestra_la_bienvenida_completa(t):
    """E-03 — systemMessage con los cinco bloques, y despues firstRunShown: true."""
    proy = _proyecto(nombre="Portal de Tramites", jira="NOT_CONFIGURED")
    codigo, mensaje, ctx, _ = _sesion(proy)
    t.igual("E-03 sale 0", 0, codigo)
    mensaje = mensaje or ""
    for bloque in ("Estado general", "Integraciones", "Conocimiento", "Comandos iniciales",
                   "Proyecto detectado: Portal de Tramites"):
        t.contiene("E-03 la bienvenida trae el bloque %s" % bloque, bloque, mensaje)
    t.contiene("E-03 es la del formato del paquete", "GCBA Development Harness", mensaje)
    t.verdadero("E-03 y va tambien al principio del contexto", (ctx or "").startswith(mensaje)
                and bool(mensaje))
    t.igual("E-03 deja firstRunShown: true", True, _estado(proy)["welcome"]["firstRunShown"])
    t.verdadero("E-03 y anota cuando se mostro", bool(_estado(proy)["welcome"]["lastShownAt"]))


def test_e04_la_segunda_sesion_muestra_una_sola_linea(t):
    """E-04 — una linea, y ninguna parte de la bienvenida completa."""
    proy = _proyecto(nombre="Portal de Tramites", jira="NOT_CONFIGURED")
    _sesion(proy)
    codigo, mensaje, ctx, _ = _sesion(proy)
    t.igual("E-04 sale 0", 0, codigo)
    mensaje = mensaje or ""
    t.verdadero("E-04 hay una linea", mensaje.startswith("Harness GCBA "))
    t.no_contiene("E-04 es UNA sola linea", "\n", mensaje)
    for parte in ("GCBA Development Harness", "━", "Estado general", "Comandos iniciales",
                  "Integraciones", "Proyecto detectado", "instalado correctamente"):
        t.no_contiene("E-04 el mensaje no trae %s" % parte, parte, mensaje)
        t.no_contiene("E-04 el contexto tampoco trae %s" % parte, parte, ctx)
    t.verdadero("E-04 y la linea encabeza el contexto", (ctx or "").startswith(mensaje + "\n"))


# -- E-05 / E-06 — sin red, sin modelo, sin integraciones --------------------------------

_ENVOLTORIO = r'''
import atexit, json, os, runpy, sys, types
HOOK, MARCA = sys.argv[1], sys.argv[2]
intentos = []

class _Prohibido(types.ModuleType):
    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        intentos.append("%s.%s" % (self.__name__, nombre))
        raise OSError("E-05: red prohibida (%s.%s)" % (self.__name__, nombre))

for n in ("socket", "_socket", "ssl", "_ssl", "urllib.request", "http.client",
          "urllib3", "requests", "httpx"):
    sys.modules[n] = _Prohibido(n)
import urllib
urllib.request = sys.modules["urllib.request"]

def _volcar():
    with open(MARCA, "w", encoding="utf-8") as f:
        json.dump({"intentos": intentos, "modulos": sorted(sys.modules)}, f)
atexit.register(_volcar)
sys.argv = [HOOK]
runpy.run_path(HOOK, run_name="__main__")
'''


def _sesion_sin_red(proy):
    tmp = Path(tempfile.mkdtemp(prefix="bv-red-"))
    envoltorio = tmp / "sin_red.py"
    marca = tmp / "marca.json"
    envoltorio.write_text(_ENVOLTORIO, encoding="utf-8")
    codigo, mensaje, ctx, _ = _sesion(
        proy, comando=[sys.executable, str(envoltorio), str(HOOK), str(marca)])
    datos = json.loads(marca.read_text(encoding="utf-8")) if marca.is_file() else None
    shutil.rmtree(str(tmp), ignore_errors=True)
    return codigo, mensaje, ctx, datos


def test_e05_session_start_no_abre_ninguna_conexion(t):
    """E-05 — con socket y urllib reemplazados por unos que fallan, la bienvenida sale igual
    y nadie intento usarlos."""
    for rotulo, proy in (("primera", _proyecto(jira="CONNECTION_FAILED")),
                         ("siguiente", _proyecto(jira="CONNECTION_FAILED",
                                                 instalacion=_instalacion_vista()))):
        codigo, mensaje, ctx, datos = _sesion_sin_red(proy)
        t.igual("E-05 %s: sale 0" % rotulo, 0, codigo)
        t.verdadero("E-05 %s: el envoltorio corrio" % rotulo, datos is not None)
        t.igual("E-05 %s: ningun intento de red" % rotulo, [], (datos or {}).get("intentos"))
        t.verdadero("E-05 %s: y la bienvenida salio" % rotulo,
                    (mensaje or "").startswith(("━", "Harness GCBA")))
        t.no_contiene("E-05 %s: sin falla del hook" % rotulo, "fallo el hook", mensaje or "")


_PROHIBIDOS = ("integraciones", "harnesses", "anthropic", "openai", "claude_agent_sdk",
               "google.generativeai", "orquestacion", "contexto")


def _importados(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres += [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nombres.append(nodo.module or "")
            if nodo.module == "lib":
                nombres += ["lib." + a.name for a in nodo.names]
    return nombres


def test_e06_no_importa_clientes_de_modelo_ni_integraciones(t):
    """E-06 — ni en el fuente ni en lo que queda cargado despues de correr el hook."""
    for ruta in (HOOK, LIB):
        for nombre in _importados(ruta):
            prohibido = any(nombre == p or nombre.startswith(p + ".") for p in _PROHIBIDOS)
            t.verdadero("E-06 %s no importa %s" % (ruta.name, nombre), not prohibido)
    t.igual("E-06 bienvenida.py solo usa la biblioteca estandar",
            ["datetime", "json", "os", "re", "sys"], sorted(set(_importados(LIB))))
    _, _, _, datos = _sesion_sin_red(_proyecto())
    cargados = (datos or {}).get("modulos") or []
    t.verdadero("E-06 el hook corrio", bool(cargados))
    for p in _PROHIBIDOS:
        t.igual("E-06 despues de la sesion no hay %s cargado" % p, [],
                [m for m in cargados if m == p or m.startswith(p + ".")])


# -- E-07 — los tres estados con su etiqueta ---------------------------------------------

def test_e07_ready_dice_listo_y_la_frase_final(t):
    """E-07 — READY: LISTO y "El Harness está listo para trabajar."."""
    doc, completa, linea = _textos(_proyecto())
    t.igual("E-07 READY", "READY", doc["bootstrap"]["status"])
    t.contiene("E-07 READY dice LISTO en la bienvenida", "LISTO", completa)
    t.contiene("E-07 READY dice la frase final", "El Harness está listo para trabajar.", completa)
    t.verdadero("E-07 READY en la linea", linea.startswith("Harness GCBA ✓ LISTO"))


def test_e07_partial_dice_parcial_y_nombra_cada_pendiente(t):
    """E-07 — PARTIAL: PARCIAL y cada pendiente con su nombre."""
    fuentes = dict({s: "CURRENT" for s in TODAS}, ES0901="UPDATE_AVAILABLE",
                   Obelisco="FRESHNESS_UNVERIFIED")
    doc, completa, linea = _textos(_proyecto(jira="NOT_CONFIGURED", fuentes=fuentes))
    t.igual("E-07 PARTIAL", "PARTIAL", doc["bootstrap"]["status"])
    t.contiene("E-07 PARTIAL dice PARCIAL", "PARCIAL", completa)
    t.verdadero("E-07 PARTIAL en la linea", linea.startswith("Harness GCBA ◐ PARCIAL"))
    general = completa.split("Estado general", 1)[1].split("Integraciones", 1)[0]
    for nombre in ("Jira Cloud SIN CONFIGURAR", "ES0901", "Obelisco"):
        t.contiene("E-07 PARTIAL nombra %s en el estado general" % nombre, nombre, general)
    t.contiene("E-07 la linea nombra la integracion pendiente", "Jira SIN CONFIGURAR", linea)
    t.contiene("E-07 y el conocimiento pendiente", "ACTUALIZACIÓN DISPONIBLE", linea)
    t.no_contiene("E-07 PARTIAL no dice la frase final", "listo para trabajar", completa)


def test_e07_blocked_dice_que_lo_bloquea_y_nunca_listo(t):
    """E-07 — BLOCKED: BLOQUEADO, la condicion, y "listo" en ninguna forma."""
    casos = (
        ("alerta", _proyecto(fuentes=dict({s: "CURRENT" for s in TODAS},
                                          ES0902="SOURCE_INTEGRITY_ALERT")), "ES0902"),
        ("sin lockfile", _proyecto(lock=False, instalacion=_instalacion_vista()),
         "harness.lock.json"),
        ("installed false", _proyecto(instalacion=dict(_instalacion_vista(), installed=False)),
         "install.ps1"),
    )
    for rotulo, proy, condicion in casos:
        doc, completa, linea = _textos(proy)
        t.igual("E-07 BLOCKED %s" % rotulo, "BLOCKED", doc["bootstrap"]["status"])
        t.contiene("E-07 %s dice BLOQUEADO" % rotulo, "BLOQUEADO", completa)
        t.verdadero("E-07 %s la linea dice BLOQUEADO" % rotulo,
                    linea.startswith("Harness GCBA ✕ BLOQUEADO"))
        t.contiene("E-07 %s nombra lo que bloquea" % rotulo, condicion, completa)
        t.igual("E-07 %s: ni la bienvenida dice listo" % rotulo, None, _LISTO.search(completa))
        t.igual("E-07 %s: ni la linea" % rotulo, None, _LISTO.search(linea))
    # Y punta a punta, lo que ve la persona.
    proy = casos[0][1]
    _, mensaje, ctx, _ = _sesion(proy)
    t.igual("E-07 el systemMessage de BLOCKED no dice listo", None, _LISTO.search(mensaje or "x"))
    _, mensaje, _, _ = _sesion(proy)
    t.igual("E-07 ni la linea de la sesion siguiente", None, _LISTO.search(mensaje or "x"))


def test_e07_el_nombre_del_proyecto_queda_afuera_de_la_busqueda(t):
    """E-07 (enmendado) — el nombre del proyecto es un dato: "Portal Listo" se muestra igual, y
    la busqueda de "listo" en BLOCKED corre sobre el texto sin ese nombre."""
    proy = _proyecto(nombre="Portal Listo",
                     fuentes=dict({s: "CURRENT" for s in TODAS}, ES0902="SOURCE_INTEGRITY_ALERT"))
    doc, completa, linea = _textos(proy)
    t.igual("E-07 Portal Listo: BLOCKED", "BLOCKED", doc["bootstrap"]["status"])
    t.contiene("E-07 Portal Listo: el nombre se muestra igual",
               "Proyecto detectado: Portal Listo", completa)
    sin_nombre = completa.replace("Portal Listo", "")
    t.igual("E-07 Portal Listo: sin el nombre, la bienvenida no dice listo", None,
            _LISTO.search(sin_nombre))
    t.igual("E-07 Portal Listo: ni la linea", None, _LISTO.search(linea.replace("Portal Listo", "")))
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-07 Portal Listo: la persona ve el nombre", "Portal Listo", mensaje or "")
    t.igual("E-07 Portal Listo: y fuera del nombre no dice listo", None,
            _LISTO.search((mensaje or "listo").replace("Portal Listo", "")))


# -- E-08 — una integracion que no esta disponible ---------------------------------------

def test_e08_integracion_no_disponible_sin_tilde_ni_disponible(t):
    """E-08 — NOT_CONFIGURED, CONNECTION_FAILED o nunca verificada: sin ✓ ni DISPONIBLE, y
    PARTIAL."""
    casos = (("NOT_CONFIGURED", {"jira": "NOT_CONFIGURED"}),
             ("CONNECTION_FAILED", {"jira": "CONNECTION_FAILED"}),
             ("nunca verificada, sin entrada", {"jira": None}),
             ("nunca verificada, sin setup", {"capacidades": False}))
    for rotulo, kwargs in casos:
        doc, completa, linea = _textos(_proyecto(**kwargs))
        t.igual("E-08 %s deja PARTIAL" % rotulo, "PARTIAL", doc["bootstrap"]["status"])
        fila = _linea_de(completa.split("Integraciones", 1)[1], "Jira Cloud")
        t.verdadero("E-08 %s tiene su fila" % rotulo, bool(fila))
        t.no_contiene("E-08 %s: la fila no lleva ✓" % rotulo, "✓", fila)
        t.no_contiene("E-08 %s: la fila no dice DISPONIBLE" % rotulo, "DISPONIBLE", fila)
        segmento = [p for p in linea.split(" · ") if p.startswith("Jira ")]
        t.igual("E-08 %s: la linea nombra a Jira una vez" % rotulo, 1, len(segmento))
        t.no_contiene("E-08 %s: y no como DISPONIBLE" % rotulo, "DISPONIBLE",
                      segmento[0] if segmento else "DISPONIBLE")
        t.no_contiene("E-08 %s: sin ✓ en la linea" % rotulo, "✓", linea)
    doc, completa, _ = _textos(_proyecto(jira=None))
    t.contiene("E-08 la nunca verificada dice SIN VERIFICAR", "SIN VERIFICAR",
               _linea_de(completa.split("Integraciones", 1)[1], "Jira Cloud"))


# -- E-09 — el conocimiento sale de harness.fuentes.json --------------------------------

def test_e09_el_conocimiento_sale_del_state_de_cada_fuente(t):
    """E-09 — cambiar harness.fuentes.json cambia lo que se muestra, y bienvenida.py no
    calcula frescura."""
    proy = _proyecto()
    _, antes_c, antes_l = _textos(proy)
    t.contiene("E-09 todo CURRENT se muestra ACTUAL", "Normativa    ✓ ACTUAL", antes_c)
    _json(proy / ".claude" / "harness.fuentes.json",
          _fuentes_doc(dict({s: "CURRENT" for s in TODAS}, ES0903="UPDATE_AVAILABLE")))
    doc, despues_c, despues_l = _textos(proy)
    t.contiene("E-09 el cambio del archivo se ve en la bienvenida",
               "ACTUALIZACIÓN DISPONIBLE: ES0903", despues_c)
    t.contiene("E-09 y en la linea", "Conocimiento ACTUALIZACIÓN DISPONIBLE", despues_l)
    t.verdadero("E-09 lo que se muestra cambio", antes_c != despues_c and antes_l != despues_l)
    t.igual("E-09 el state de la fuente se copia tal cual", "UPDATE_AVAILABLE",
            [f["state"] for f in doc["knowledge"]["sources"] if f["id"] == "ES0903"][0])
    # No calcula frescura: no importa el modulo que la calcula ni lee la evidencia con la que
    # se calcula (version observada, hashes).
    fuente = LIB.read_text(encoding="utf-8")
    t.verdadero("E-09 no importa frescura", not any("frescura" in n for n in _importados(LIB)))
    for campo in ("observed_version", "registry_version", "sha256", "observed_sha256",
                  "attachmentId", "evidence"):
        t.no_contiene("E-09 no lee %s" % campo, campo, fuente)


# -- E-10 — una alerta de integridad ------------------------------------------------------

def test_e10_alerta_de_integridad_bloquea_y_se_nombra(t):
    """E-10 — SOURCE_INTEGRITY_ALERT da BLOQUEADO y la fuente sale con su id en las dos."""
    proy = _proyecto(fuentes=dict({s: "CURRENT" for s in TODAS},
                                  ES0902="SOURCE_INTEGRITY_ALERT"))
    doc, completa, linea = _textos(proy)
    t.igual("E-10 BLOCKED", "BLOCKED", doc["bootstrap"]["status"])
    t.igual("E-10 la condicion con su id", ["SOURCE_INTEGRITY_ALERT:ES0902"],
            doc["bootstrap"]["blockingConditions"])
    t.contiene("E-10 la bienvenida la nombra", "ES0902 ALERTA DE INTEGRIDAD", completa)
    t.contiene("E-10 la linea la nombra", "ES0902 ALERTA DE INTEGRIDAD", linea)
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-10 y la persona la ve en la primera sesion", "ES0902", mensaje or "")
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-10 y en la siguiente", "ES0902 ALERTA DE INTEGRIDAD", mensaje or "")


# -- E-11 / E-12 — ningun secreto -----------------------------------------------------------

def _proyecto_con_token():
    proy = _proyecto(jira="AUTHENTICATION_FAILED", nombre="Portal")
    _escribir(proy / ".env", "JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    return proy, {"JIRA_TOKEN": TOKEN, "GITLAB_TOKEN": TOKEN}


def _importar_secretos():
    sys.path.insert(0, str(HOOKS))
    try:
        from lib import secretos
    finally:
        sys.path.remove(str(HOOKS))
    return secretos


def test_e11_el_estado_no_guarda_ningun_secreto(t):
    """E-11 — con el token en el .env y en el entorno (el almacen lee los dos), el archivo de
    estado no tiene el token ni nada que el catalogo reconozca."""
    secretos = _importar_secretos()
    proy, env = _proyecto_con_token()
    t.verdadero("E-11 el catalogo reconoce el token (si no, el test no prueba nada)",
                secretos.buscar_secreto((proy / ".env").read_text(encoding="utf-8"),
                                        SECRETOS_CATALOGO) is not None)
    for n in (1, 2):
        _sesion(proy, env=env)
        texto = (proy / ".claude" / "harness.installation.json").read_text(encoding="utf-8")
        t.no_contiene("E-11 sesion %d: no esta el token" % n, TOKEN, texto)
        t.igual("E-11 sesion %d: el catalogo no reconoce nada" % n, None,
                secretos.buscar_secreto(texto, SECRETOS_CATALOGO))
    B.registrar_instalacion(str(proy))
    texto = (proy / ".claude" / "harness.installation.json").read_text(encoding="utf-8")
    t.no_contiene("E-11 lo que registra el instalador tampoco", TOKEN, texto)


def test_e12_la_bienvenida_y_la_linea_no_imprimen_el_token(t):
    """E-12 (la mitad del hook) — ni la bienvenida ni la linea. La CLI la cubre quien la
    construye."""
    proy, env = _proyecto_con_token()
    for n in (1, 2):
        codigo, mensaje, ctx, crudo = _sesion(proy, env=env)
        t.igual("E-12 sesion %d sale 0" % n, 0, codigo)
        t.verdadero("E-12 sesion %d dijo algo" % n, bool(mensaje))
        t.no_contiene("E-12 sesion %d: la salida no tiene el token" % n, TOKEN, crudo)


# -- E-15 — castellano ----------------------------------------------------------------------

def test_e15_la_salida_humana_esta_en_castellano(t):
    """E-15 — las etiquetas de la tabla, y ningun id en ingles de los que la tabla traduce."""
    casos = (
        _proyecto(),
        _proyecto(jira="NOT_CONFIGURED", gitlab="AUTHENTICATION_FAILED",
                  fuentes=dict({s: "CURRENT" for s in TODAS}, ES0901="UPDATE_AVAILABLE",
                               ES0903="ACKNOWLEDGED_PENDING", Obelisco="FRESHNESS_UNVERIFIED")),
        _proyecto(jira="CONNECTION_FAILED", gitlab="PERMISSION_DENIED",
                  fuentes=dict({s: "CURRENT" for s in TODAS}, ES0902="SOURCE_INTEGRITY_ALERT")),
        _proyecto(jira=None, capacidades=True),
    )
    vistas = set()
    for proy in casos:
        _, completa, linea = _textos(proy)
        for texto, cual in ((completa, "bienvenida"), (linea, "linea")):
            for ident in IDS_TRADUCIDOS:
                t.igual("E-15 la %s no dice %s" % (cual, ident), None,
                        re.search(r"\b%s\b" % ident, texto))
            vistas.update(e for e in B.ETIQUETAS.values() if e in texto)
    for etiqueta in ("LISTO", "PARCIAL", "BLOQUEADO", "DISPONIBLE", "SIN CONFIGURAR",
                     "FALLA DE AUTENTICACIÓN", "SIN CONEXIÓN", "SIN PERMISOS", "SIN VERIFICAR",
                     "ACTUAL", "ACTUALIZACIÓN DISPONIBLE", "PENDIENTE ACEPTADO",
                     "ALERTA DE INTEGRIDAD", "VIGENCIA SIN VERIFICAR"):
        t.verdadero("E-15 la etiqueta %s sale en algun caso" % etiqueta, etiqueta in vistas)
    # Y lo que llega a la persona, con sus tildes y sin escapar.
    _, _, _, crudo = _sesion(casos[1])
    t.contiene("E-15 la tilde llega sin escapar", "ACTUALIZACIÓN", crudo)


# -- E-16 / E-17 — el proyecto ---------------------------------------------------------------

def test_e16_con_contexto_dice_el_nombre(t):
    """E-16 — con project-context.json, "Proyecto detectado: <nombre>"."""
    proy = _proyecto(nombre="Mi Barrio Digital")
    doc, completa, _ = _textos(proy)
    t.contiene("E-16 lo dice", "✓ Proyecto detectado: Mi Barrio Digital", completa)
    t.igual("E-16 y lo guarda", {"detected": True, "name": "Mi Barrio Digital"}, doc["project"])
    # Con la ruta del codebase que declara la persona, la misma que lee session-start.py.
    proy = _proyecto()
    _json(proy / "otra" / "project-context.json",
          {"project_profile": {"project_name": "En Otra Ruta"}})
    _json(proy / ".claude" / "harness.config.json", {"usuario": "Nahue", "rutaCodebase": "otra"})
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-16 respeta rutaCodebase", "Proyecto detectado: En Otra Ruta", mensaje or "")


def test_e17_sin_contexto_no_inventa_un_nombre(t):
    """E-17 — sin contexto: no detectado, sin ✓, detected false. La carpeta no es el nombre."""
    proy = _proyecto()
    doc, completa, _ = _textos(proy)
    t.igual("E-17 detected false y sin nombre", {"detected": False, "name": None}, doc["project"])
    t.no_contiene("E-17 no dice detectado", "Proyecto detectado", completa)
    fila = _linea_de(completa, "· Proyecto")
    t.contiene("E-17 dice que no se detecto", "Proyecto no detectado", fila)
    t.no_contiene("E-17 sin ✓", "✓", fila)
    t.no_contiene("E-17 no usa el nombre de la carpeta", proy.name, completa)
    _sesion(proy)
    t.igual("E-17 el archivo queda en false", False, _estado(proy)["project"]["detected"])


# -- E-18 / E-19 — la actualizacion y el reinicio, del lado del hook ------------------------

def test_e18_la_actualizacion_se_avisa_una_vez(t):
    """E-18 (la mitad del hook) — con upgradeFrom y firstRunShown: true, el aviso y la linea,
    una vez, y sin la bienvenida. El -Update que lo escribe es del caso del instalador."""
    proy = _proyecto(version="0.20.0", instalacion=_instalacion_vista("0.19.0", upgrade="0.19.0"))
    _, mensaje, ctx, _ = _sesion(proy)
    mensaje = mensaje or ""
    lineas = mensaje.split("\n")
    t.igual("E-18 el aviso", "Harness GCBA actualizado: 0.19.0 → 0.20.0 ✓", lineas[0])
    t.igual("E-18 y la linea, nada mas", 2, len(lineas))
    t.verdadero("E-18 la segunda es la linea", len(lineas) > 1
                and lineas[1].startswith("Harness GCBA ✓ LISTO"))
    t.no_contiene("E-18 no repite la bienvenida", "GCBA Development Harness", mensaje)
    t.igual("E-18 despues se borra upgradeFrom", None, _estado(proy)["welcome"].get("upgradeFrom"))
    _, mensaje, _, _ = _sesion(proy)
    t.no_contiene("E-18 la sesion siguiente no lo repite", "actualizado", mensaje or "")
    # La API que va a llamar install.ps1 en un -Update.
    proy = _proyecto(version="0.21.0", instalacion=_instalacion_vista("0.20.0"))
    doc = B.registrar_instalacion(str(proy))
    t.igual("E-18 registrar conserva firstRunShown", True, doc["welcome"]["firstRunShown"])
    t.igual("E-18 y anota de donde viene", "0.20.0", doc["welcome"].get("upgradeFrom"))
    t.igual("E-18 misma version, sin aviso", None,
            B.registrar_instalacion(str(_proyecto(version="0.20.0", instalacion=_instalacion_vista(
                "0.20.0"))))["welcome"].get("upgradeFrom"))


def test_e19_borrar_el_estado_vuelve_a_mostrar_la_bienvenida(t):
    """E-19 (lo que hace el hook) — sin el archivo, o reiniciado, vuelve la bienvenida
    completa. El comando --reiniciar-bienvenida lo cubre quien construye la CLI."""
    proy = _proyecto()
    _sesion(proy)
    _, mensaje, _, _ = _sesion(proy)
    t.no_contiene("E-19 ya se habia mostrado", "GCBA Development Harness", mensaje or "")
    (proy / ".claude" / "harness.installation.json").unlink()
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-19 borrado: vuelve la bienvenida", "GCBA Development Harness", mensaje or "")
    B.reiniciar_bienvenida(str(proy))
    t.igual("E-19 reiniciar pone firstRunShown: false", False,
            _estado(proy)["welcome"]["firstRunShown"])
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-19 reiniciada: vuelve la bienvenida", "GCBA Development Harness", mensaje or "")


# -- E-20 — el bloque de siempre, igual y en el mismo orden ------------------------------

def _hook_de_antes(destino):
    """El session-start.py de ANTES y su lib, sacados de git. None si no se pudo."""
    archivos = ("session-start.py", "lib/__init__.py", "lib/hook.py", "lib/reglas.py",
                "lib/zonas.py", "lib/secretos.py")
    for rel in archivos:
        r = subprocess.run(["git", "-C", str(RAIZ), "show", "%s:comun/hooks/%s" % (ANTES, rel)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            return None
        ruta = destino / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(r.stdout)
    return destino / "session-start.py"


def _proyecto_completo():
    """Todo lo que el bloque de siempre sabe decir: usuario y harness, git con commits, cache,
    definiciones pendientes y el aviso del recorrido del codigo."""
    proy = _proyecto(jira="NOT_CONFIGURED")
    _json(proy / ".claude" / "harness.config.json",
          {"usuario": "Nahue", "rutaDefinicionesPendientes": "PENDIENTES.md"})
    _escribir(proy / "CLAUDE.md", "# CLAUDE.md\n\n<!-- ZONA CACHE -->\n- la nota de la cache\n"
                                  "<!-- /ZONA CACHE -->\n")
    _escribir(proy / "PENDIENTES.md", "- [ ] una\n- [ ] dos\n")
    _escribir(proy / ".gitignore", ".claude/\n")
    for args in (["init", "-q"], ["config", "user.email", "p@gcba.gob.ar"],
                 ["config", "user.name", "Prueba"], ["add", "-A"],
                 ["commit", "-q", "-m", "el primer commit"]):
        subprocess.run(["git", "-C", str(proy)] + args, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proy


def test_e20_el_bloque_de_siempre_sale_igual_despues_de_la_bienvenida(t):
    """E-20 — el contexto es la bienvenida (o la linea) y despues, byte a byte, lo que escribia
    el hook de antes de este cambio."""
    proy = _proyecto_completo()
    tmp = Path(tempfile.mkdtemp(prefix="bv-antes-"))
    viejo = _hook_de_antes(tmp)
    t.verdadero("E-20 se pudo sacar el hook de %s de git" % ANTES, viejo is not None)
    if viejo is None:
        return
    _, mensaje_viejo, antes, _ = _sesion(proy, hook=viejo)
    t.igual("E-20 el hook de antes no mostraba nada a la persona", None, mensaje_viejo)
    t.verdadero("E-20 el hook de antes dijo algo", bool(antes))
    orden = ("Nahue - harness: comun, desarrollo v0.20.0", "git: ", "Ultimo trabajo:",
             "el primer commit", "En la cache quedo anotado:", "2 definiciones pendientes",
             "Sin indice del codigo todavia")
    posiciones = [(antes or "").find(p) for p in orden]
    t.verdadero("E-20 el caso ejercita las cinco secciones", all(p >= 0 for p in posiciones))
    for rotulo in ("primera", "siguiente"):
        _, mensaje, ctx, _ = _sesion(proy)
        t.verdadero("E-20 %s: hay bienvenida" % rotulo, bool(mensaje))
        t.igual("E-20 %s: bienvenida y despues el bloque de antes, igual" % rotulo,
                "%s\n%s" % (mensaje, antes), ctx)
    shutil.rmtree(str(tmp), ignore_errors=True)


# -- E-22 — archivos rotos -------------------------------------------------------------------

def test_e22_un_archivo_roto_no_rompe_el_hook_ni_da_ready(t):
    """E-22 — sobre un proyecto que sin la rotura es READY."""
    base = _proyecto()
    t.igual("E-22 el proyecto sin romper es READY", "READY", B.resolver(str(base))["bootstrap"]["status"])
    roturas = (
        ("installation", "harness.installation.json", "{ no es json"),
        ("installation", "harness.installation.json", "[1, 2]"),
        ("installation", "harness.installation.json", json.dumps({"welcome": "si"})),
        ("installation", "harness.installation.json", json.dumps({"installed": "yes"})),
        ("installation", "harness.installation.json",
         json.dumps({"welcome": {"firstRunShown": "true"}})),
        ("capacidades", "harness.capacidades.json", "{ no es json"),
        ("capacidades", "harness.capacidades.json", "\"texto\""),
        ("capacidades", "harness.capacidades.json", json.dumps({"integraciones": "x"})),
        ("capacidades", "harness.capacidades.json",
         json.dumps({"integraciones": {"jira": "AVAILABLE", "gitlab": {"estado": 1}}})),
        ("fuentes", "harness.fuentes.json", "{ no es json"),
        ("fuentes", "harness.fuentes.json", "null"),
        ("fuentes", "harness.fuentes.json", json.dumps({"sources": []})),
        ("fuentes", "harness.fuentes.json",
         json.dumps({"sources": {"ES0901": "CURRENT", "ES0902": {"state": None}}})),
    )
    for n, (cual, archivo, contenido) in enumerate(roturas):
        proy = _proyecto()
        _escribir(proy / ".claude" / archivo, contenido)
        rotulo = "%s #%d" % (cual, n)
        estado = B.resolver(str(proy))["bootstrap"]["status"]
        t.verdadero("E-22 %s: el resolvedor no da READY (%s)" % (rotulo, estado),
                    estado != "READY")
        codigo, mensaje, ctx, _ = _sesion(proy)
        t.igual("E-22 %s: el hook sale 0" % rotulo, 0, codigo)
        t.verdadero("E-22 %s: la persona ve un estado" % rotulo,
                    (mensaje or "").startswith(("━", "Harness GCBA")))
        t.igual("E-22 %s: y no dice listo" % rotulo, None, _LISTO.search(mensaje or ""))
        t.contiene("E-22 %s: el bloque de siempre sigue" % rotulo, "Nahue - harness:", ctx)
        t.no_contiene("E-22 %s: sin falla del hook" % rotulo, "fallo el hook", mensaje)
    # Un lockfile roto tambien: BLOCKED, y el hook sigue.
    _e22_tipos_en_cualquier_nivel(t)
    proy = _proyecto()
    _escribir(proy / ".claude" / "harness.lock.json", "{ roto")
    codigo, mensaje, _, _ = _sesion(proy)
    t.igual("E-22 lockfile roto: sale 0", 0, codigo)
    t.contiene("E-22 lockfile roto: BLOQUEADO", "BLOQUEADO", mensaje or "")


def _e22_tipos_en_cualquier_nivel(t):
    """E-22 (enmendado) — un campo con un tipo distinto del que escribe su dueno, en cualquier
    nivel y decida o no el estado, queda como *_STATE_UNREADABLE. Los cinco primeros son las
    sondas del primer pase del refutador; todos salian READY."""
    vista = _instalacion_vista()
    todas_al_dia = {s: _fuente("CURRENT") for s in TODAS}

    def fuentes_con(**cambio):
        doc = _fuentes_doc({s: "CURRENT" for s in TODAS})
        doc.update(cambio)
        return json.dumps(doc)

    def una_fuente(**cambio):
        sources = dict(todas_al_dia)
        sources["ES0901"] = dict(_fuente("CURRENT"), **cambio)
        return fuentes_con(sources=sources)

    def capacidades(**cambio_jira):
        integ = {n: {"estado": "AVAILABLE", "motivo": "", "verificado_en": "2026-09-24T10:00:00",
                     "capacidades": []} for n in ("jira", "gitlab")}
        integ["jira"].update(cambio_jira)
        return json.dumps({"schema_version": "integraciones/1.0", "version_harness": "0.20.0",
                           "integraciones": integ, "capacidades": {}})

    def instalacion(**cambio):
        return json.dumps(dict(vista, **cambio))

    def bienvenida_con(**cambio):
        return json.dumps(dict(vista, welcome=dict(vista["welcome"], **cambio)))

    casos = (
        ("INSTALLATION", "harness.installation.json", instalacion(bootstrap=5)),
        ("INSTALLATION", "harness.installation.json", "{}"),
        ("CAPABILITIES", "harness.capacidades.json", capacidades(verificado_en=5)),
        ("SOURCES", "harness.fuentes.json", una_fuente(blocking="si")),
        ("SOURCES", "harness.fuentes.json", fuentes_con(verified_at=5)),
        # Y mas abajo, en campos que no deciden el estado.
        ("INSTALLATION", "harness.installation.json",
         instalacion(bootstrap={"status": "READY", "blockingConditions": [5],
                                "pendingConditions": []})),
        ("INSTALLATION", "harness.installation.json",
         instalacion(bootstrap={"status": "READY", "blockingConditions": []})),
        ("INSTALLATION", "harness.installation.json", instalacion(project={"detected": "si"})),
        ("INSTALLATION", "harness.installation.json",
         instalacion(integrations=[{"id": "jira", "status": 7}])),
        ("INSTALLATION", "harness.installation.json",
         instalacion(knowledge={"sources": [{"id": "ES0901", "blocking": "si"}]})),
        ("INSTALLATION", "harness.installation.json", bienvenida_con(upgradeFrom=19)),
        ("INSTALLATION", "harness.installation.json", instalacion(harnessId=None)),
        ("INSTALLATION", "harness.installation.json", instalacion(schema_version="otra/9")),
        ("CAPABILITIES", "harness.capacidades.json", capacidades(motivo=None)),
        ("CAPABILITIES", "harness.capacidades.json", capacidades(capacidades=[1])),
        ("CAPABILITIES", "harness.capacidades.json", capacidades(capacidades="jira.issue.read")),
        ("SOURCES", "harness.fuentes.json", una_fuente(evidence="texto")),
        ("SOURCES", "harness.fuentes.json", una_fuente(size="grande")),
        ("SOURCES", "harness.fuentes.json", una_fuente(derived_impact=[{"x": 1}])),
        ("SOURCES", "harness.fuentes.json", fuentes_con(pending_count=True)),
        ("SOURCES", "harness.fuentes.json", fuentes_con(warnings="uno")),
        ("SOURCES", "harness.fuentes.json", fuentes_con(ficha=[])),
    )
    for n, (prefijo, archivo, contenido) in enumerate(casos):
        proy = _proyecto()
        _escribir(proy / ".claude" / archivo, contenido)
        rotulo = "tipo %s #%d" % (prefijo.lower(), n)
        doc = B.resolver(str(proy))
        t.igual("E-22 %s: PARTIAL" % rotulo, "PARTIAL", doc["bootstrap"]["status"])
        t.verdadero("E-22 %s: con %s_STATE_UNREADABLE" % (rotulo, prefijo),
                    "%s_STATE_UNREADABLE" % prefijo in doc["bootstrap"]["pendingConditions"])
        codigo, mensaje, _, _ = _sesion(proy)
        t.igual("E-22 %s: el hook sale 0" % rotulo, 0, codigo)
        t.igual("E-22 %s: lo que queda escrito no es READY" % rotulo, "PARTIAL",
                _estado(proy)["bootstrap"]["status"])
        t.igual("E-22 %s: y no dice listo" % rotulo, None, _LISTO.search(mensaje or ""))
    # El control no es un falso positivo: lo que escriben los duenos de verdad pasa.
    t.verdadero("E-22 el estado que escribe resolver cumple su forma",
                B.cumple(B.resolver(str(_proyecto())), B.FORMA_INSTALACION))
    reales = RAIZ / ".claude" / "harness.fuentes.json"
    if reales.is_file():
        t.verdadero("E-22 el harness.fuentes.json que escribio frescura en este repo cumple",
                    B.cumple(json.loads(reales.read_text(encoding="utf-8")), B._forma_fuentes()))


# -- E-26 — sin fuentes, y el resumen del conocimiento ---------------------------------------

def test_e26_sin_fuentes_es_parcial(t):
    """E-26 — con desarrollo, harness.fuentes.json con sources: {} es PARTIAL."""
    proy = _proyecto(fuentes={})
    doc, completa, linea = _textos(proy)
    t.igual("E-26 sin fuentes: PARTIAL", "PARTIAL", doc["bootstrap"]["status"])
    t.verdadero("E-26 con su condicion", "SOURCES_STATE_EMPTY" in doc["bootstrap"]["pendingConditions"])
    t.no_contiene("E-26 la linea no dice ACTUAL", "ACTUAL", linea)
    t.no_contiene("E-26 la bienvenida no dice la frase final", "listo para trabajar", completa)
    t.contiene("E-26 la bienvenida nombra lo pendiente", "no tiene ninguna fuente", completa)
    _, mensaje, _, _ = _sesion(proy)
    t.igual("E-26 lo que queda escrito es PARTIAL", "PARTIAL", _estado(proy)["bootstrap"]["status"])
    # Solo analisis no tiene conocimiento: ahi no aplica.
    solo = _proyecto(harness=("comun", "analisis"), fuentes={})
    t.igual("E-26 solo analisis sigue READY", "READY", B.resolver(str(solo))["bootstrap"]["status"])


def test_e26_actual_solo_si_todas_estan_al_dia(t):
    """E-26 — el resumen dice ACTUAL solo con todas en CURRENT o RETIRED."""
    al_dia = {s: "CURRENT" for s in TODAS}
    casos = (
        ("una en alerta", dict(al_dia, ES0902="SOURCE_INTEGRITY_ALERT")),
        ("una que cambio igual version", dict(al_dia, ES0902="SOURCE_CHANGED_SAME_VERSION")),
        ("una con actualizacion", dict(al_dia, ES0902="UPDATE_AVAILABLE")),
        ("una sin verificar", dict(al_dia, ES0902="FRESHNESS_UNVERIFIED")),
    )
    for rotulo, fuentes in casos:
        doc, completa, linea = _textos(_proyecto(fuentes=fuentes))
        # Con limite de palabra: "Conocimiento ACTUALIZACIÓN DISPONIBLE" no es ACTUAL.
        t.igual("E-26 %s: la linea no dice Conocimiento ACTUAL" % rotulo, None,
                re.search(r"Conocimiento ACTUAL\b", linea))
        t.verdadero("E-26 %s: ni ACTUAL suelto en la linea" % rotulo,
                    re.search(r"\bACTUAL\b", linea) is None)
        t.verdadero("E-26 %s: la normativa no se resume como ACTUAL" % rotulo,
                    "ACTUAL" not in _linea_de(completa, "Normativa").replace("ACTUALIZACIÓN", ""))
    doc, completa, linea = _textos(_proyecto(fuentes=dict(al_dia, Obelisco="RETIRED")))
    t.contiene("E-26 CURRENT y RETIRED: ACTUAL", "Conocimiento ACTUAL", linea)
    t.contiene("E-26 CURRENT y RETIRED: la normativa ACTUAL", "✓ ACTUAL", _linea_de(completa, "Normativa"))
    t.igual("E-26 CURRENT y RETIRED: READY", "READY", doc["bootstrap"]["status"])


# -- E-23 — solo analisis ------------------------------------------------------------------

def test_e23_solo_analisis_no_lista_integraciones_ni_conocimiento(t):
    """E-23 — sin integraciones ni conocimiento, y READY."""
    proy = _proyecto(harness=("comun", "analisis"), capacidades=False, fuentes_archivo=False)
    doc, completa, linea = _textos(proy)
    t.igual("E-23 READY", "READY", doc["bootstrap"]["status"])
    for parte in ("Integraciones", "Conocimiento", "Jira", "GitLab", "Normativa", "Fuentes"):
        t.no_contiene("E-23 la bienvenida no trae %s" % parte, parte, completa)
        t.no_contiene("E-23 la linea no trae %s" % parte, parte, linea)
    t.igual("E-23 la linea", "Harness GCBA ✓ LISTO", linea)
    t.igual("E-23 sin integraciones en el estado", [], doc["integrations"])


# -- E-25 — un estado que la tabla no traduce -------------------------------------------------

def test_e25_un_estado_desconocido_sale_con_su_id_y_nunca_como_actual(t):
    """E-25 — NEW_SOURCE (de frescura.ESTADOS, sin etiqueta) y uno que ni existe hoy."""
    for estado in ("NEW_SOURCE", "KNOWLEDGE_PROMOTION_INCOMPLETE", "UN_ESTADO_QUE_NO_EXISTE",
                   "SOURCE_OTRO_NUEVO"):
        fuentes = dict({s: "CURRENT" for s in TODAS}, ES0901=estado)
        doc, completa, linea = _textos(_proyecto(fuentes=fuentes))
        t.igual("E-25 %s: PARTIAL" % estado, "PARTIAL", doc["bootstrap"]["status"])
        t.contiene("E-25 %s: la bienvenida lo nombra con su id" % estado,
                   "%s: ES0901" % estado, completa)
        t.contiene("E-25 %s: la linea tambien" % estado, estado, linea)
        t.igual("E-25 %s: la normativa no se resume como ACTUAL" % estado,
                "  Normativa    %s" % estado, _linea_de(completa, "Normativa"))
        t.no_contiene("E-25 %s: la linea no dice Conocimiento ACTUAL" % estado,
                      "Conocimiento ACTUAL", linea)
        pend = [c for c in doc["bootstrap"]["pendingConditions"] if c.endswith(":ES0901")]
        t.igual("E-25 %s: la condicion lleva el id tal cual" % estado,
                ["SOURCE_%s:ES0901" % estado], pend)
    t.igual("E-25 la etiqueta de un id desconocido es el id", "NEW_SOURCE",
            B.etiqueta("NEW_SOURCE"))


# -- el contrato del hook -------------------------------------------------------------------

def test_sin_harness_instalado_no_hay_bienvenida(t):
    """Sin lockfile ni estado, el harness no esta aca: nada de bienvenida, y el bloque de
    siempre como antes."""
    proy = _proyecto(lock=False, capacidades=False, fuentes_archivo=False)
    codigo, mensaje, ctx, _ = _sesion(proy)
    t.igual("sale 0", 0, codigo)
    t.igual("sin systemMessage", None, mensaje)
    t.no_contiene("sin linea en el contexto", "Harness GCBA", ctx)
    t.igual("y no escribe el archivo", False,
            (proy / ".claude" / "harness.installation.json").exists())


def test_la_escritura_es_atomica_y_no_deja_temporales(t):
    """.tmp y os.replace: despues de escribir no queda ningun temporal al lado."""
    proy = _proyecto()
    _sesion(proy)
    _sesion(proy)
    sobrantes = [p.name for p in (proy / ".claude").iterdir() if p.name.endswith(".tmp")]
    t.igual("no quedan temporales", [], sobrantes)


def test_si_no_se_puede_escribir_la_bienvenida_vuelve(t):
    """Si la marca no se pudo escribir, la bienvenida sale de nuevo: es mejor que perderla.
    Se fuerza con un directorio en el lugar del archivo."""
    proy = _proyecto()
    (proy / ".claude" / "harness.installation.json").mkdir()
    for n in (1, 2):
        codigo, mensaje, _, _ = _sesion(proy)
        t.igual("sesion %d sale 0" % n, 0, codigo)
        t.contiene("sesion %d muestra la bienvenida" % n, "GCBA Development Harness",
                   mensaje or "")


# -- la CLI: `dev-harness.py harness` y `setup` ------------------------------------------------
#
# En proceso, como 18_integraciones: la CLI recibe el transporte HTTP por parametro, y asi el
# test ve cada llamada que habria salido a la red.

CLI = RAIZ / "harnesses" / "desarrollo" / "bin" / "dev-harness.py"
_CLI_CARGADA = []


def _modulo_cli():
    if not _CLI_CARGADA:
        _CLI_CARGADA.append(_cargar("dev_harness_51", CLI))
    return _CLI_CARGADA[0]


class _Transporte(object):
    """Un servidor falso que anota cada llamada. `respuestas`: fragmento de URL -> respuesta."""

    def __init__(self, respuestas=None):
        self.respuestas = respuestas or {}
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append(url)
        for fragmento, respuesta in self.respuestas.items():
            if fragmento in url:
                if isinstance(respuesta, Exception):
                    raise respuesta
                return respuesta
        return (404, "")


class _SinRed(object):
    """Los sockets reemplazados por unos que anotan el intento y fallan."""

    def __enter__(self):
        import socket
        self.socket = socket
        self.intentos = []
        self.previos = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)

        def prohibido(nombre):
            def f(*a, **k):
                self.intentos.append(nombre)
                raise OSError("red prohibida (%s)" % nombre)
            return f
        socket.socket.connect = prohibido("connect")
        socket.create_connection = prohibido("create_connection")
        socket.getaddrinfo = prohibido("getaddrinfo")
        return self

    def __exit__(self, *exc):
        (self.socket.socket.connect, self.socket.create_connection,
         self.socket.getaddrinfo) = self.previos
        return False


def _cli(argv, transporte=None, env=None):
    """(codigo, stdout, stderr) de dev-harness.py corrido en proceso, sin terminal."""
    modulo = _modulo_cli()
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr, sys.stdin)
    entorno_previo = {k: os.environ.get(k) for k in (env or {})}
    sys.stdout, sys.stderr, sys.stdin = salida, error, io.StringIO("")
    os.environ.update(env or {})
    try:
        codigo = modulo.main(argv, transporte)
    finally:
        sys.stdout, sys.stderr, sys.stdin = previos
        for k, v in entorno_previo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return codigo, salida.getvalue(), error.getvalue()


def _sin_mostrar():
    return dict(_instalacion_vista(), welcome={"firstRunShown": False, "lastShownAt": None})


def test_e12_la_cli_no_imprime_el_token(t):
    """E-12 (la mitad de la CLI) — ni `harness`, ni `--json`, ni `--verbose`, con el token en
    el .env y en el entorno."""
    proy, env = _proyecto_con_token()
    for argv in (["harness"], ["harness", "--json"], ["harness", "--verbose"],
                 ["harness", "--json", "--verbose"]):
        codigo, salida, error = _cli(argv + ["--proyecto", str(proy)], env=env)
        rotulo = " ".join(argv)
        t.igual("E-12 %s sale 0" % rotulo, 0, codigo)
        t.verdadero("E-12 %s dijo algo" % rotulo, bool(salida.strip()))
        t.no_contiene("E-12 %s: stdout no tiene el token" % rotulo, TOKEN, salida)
        t.no_contiene("E-12 %s: stderr tampoco" % rotulo, TOKEN, error)


def test_e13_harness_muestra_lo_de_ahora_sin_red_y_sin_tocar_la_marca(t):
    """E-13 — el estado que dan los archivos de ahora, sin red, y firstRunShown como estaba."""
    proy = _proyecto(jira="NOT_CONFIGURED", instalacion=_sin_mostrar())
    ruta = proy / ".claude" / "harness.installation.json"
    antes = ruta.read_bytes()
    transporte = _Transporte()
    with _SinRed() as red:
        codigo, salida, _ = _cli(["harness", "--proyecto", str(proy)], transporte)
        t.igual("E-13 sale 0", 0, codigo)
        t.contiene("E-13 muestra la bienvenida completa", "GCBA Development Harness", salida)
        t.contiene("E-13 con Jira como dice harness.capacidades.json", "SIN CONFIGURAR",
                   _linea_de(salida.split("Integraciones", 1)[-1], "Jira Cloud"))
        _json(proy / ".claude" / "harness.capacidades.json",
              {"schema_version": "integraciones/1.0", "version_harness": "0.20.0",
               "integraciones": {n: {"estado": "AVAILABLE", "motivo": "",
                                     "verificado_en": "2026-09-24T11:00:00", "capacidades": []}
                                 for n in ("jira", "gitlab")}, "capacidades": {}})
        codigo, despues, _ = _cli(["harness", "--proyecto", str(proy)], transporte)
        t.contiene("E-13 cambiar el archivo cambia lo que muestra", "✓ DISPONIBLE",
                   _linea_de(despues.split("Integraciones", 1)[-1], "Jira Cloud"))
        t.contiene("E-13 y el estado general pasa a LISTO", "El Harness está listo para trabajar.",
                   despues)
        _cli(["harness", "--verbose", "--proyecto", str(proy)], transporte)
        _cli(["harness", "--json", "--proyecto", str(proy)], transporte)
    t.igual("E-13 ningun intento de red", [], red.intentos)
    t.igual("E-13 ninguna llamada HTTP", [], transporte.llamadas)
    t.verdadero("E-13 harness.installation.json no cambio, byte a byte", ruta.read_bytes() == antes)
    t.igual("E-13 firstRunShown sigue en false", False, _estado(proy)["welcome"]["firstRunShown"])
    # Y con la bienvenida ya vista, tampoco la vuelve a poner en false.
    proy = _proyecto(instalacion=_instalacion_vista())
    _cli(["harness", "--proyecto", str(proy)])
    t.igual("E-13 firstRunShown true sigue en true", True, _estado(proy)["welcome"]["firstRunShown"])


def test_e13_verbose_agrega_el_detalle(t):
    """E-13 / --verbose — la version, la fecha, cada condicion con su id y cada archivo leido."""
    fuentes = dict({s: "CURRENT" for s in TODAS}, ES0902="FRESHNESS_UNVERIFIED")
    proy = _proyecto(jira="NOT_CONFIGURED", fuentes=fuentes, instalacion=_instalacion_vista())
    codigo, salida, _ = _cli(["harness", "--verbose", "--proyecto", str(proy)])
    t.igual("--verbose sale 0", 0, codigo)
    detalle = salida.split("\nDetalle\n", 1)[-1]
    t.contiene("--verbose la version", "0.20.0", detalle)
    t.contiene("--verbose la fecha de instalacion", "2026-09-01T10:00:00", detalle)
    for condicion in ("INTEGRATION_NOT_CONFIGURED:jira", "SOURCE_FRESHNESS_UNVERIFIED:ES0902"):
        t.contiene("--verbose la condicion %s con su id" % condicion, condicion, detalle)
    leidos = detalle.split("Archivos leídos", 1)[-1].split("\n")
    for archivo in ("harness.lock.json", "harness.installation.json", "harness.capacidades.json",
                    "harness.fuentes.json", "project-context.json"):
        t.verdadero("--verbose la ruta completa de %s" % archivo,
                    any(os.path.normpath(str(proy)) in l and archivo in l for l in leidos))


def test_e14_harness_json_usa_los_ids_en_ingles_y_valida(t):
    """E-14 — READY, NOT_CONFIGURED y FRESHNESS_UNVERIFIED tal cual, en harness-installation/1.0."""
    fuentes = dict({s: "CURRENT" for s in TODAS}, ES0902="FRESHNESS_UNVERIFIED")
    codigo, salida, _ = _cli(["harness", "--json", "--proyecto",
                              str(_proyecto(jira="NOT_CONFIGURED", fuentes=fuentes))])
    t.igual("E-14 sale 0", 0, codigo)
    doc = json.loads(salida)
    t.igual("E-14 schema_version", "harness-installation/1.0", doc.get("schema_version"))
    t.igual("E-14 PARTIAL en ingles", "PARTIAL", doc["bootstrap"]["status"])
    t.igual("E-14 NOT_CONFIGURED en ingles", "NOT_CONFIGURED",
            [i["status"] for i in doc["integrations"] if i["id"] == "jira"][0])
    t.igual("E-14 FRESHNESS_UNVERIFIED en ingles", "FRESHNESS_UNVERIFIED",
            [f["state"] for f in doc["knowledge"]["sources"] if f["id"] == "ES0902"][0])
    t.verdadero("E-14 la condicion con su id",
                "SOURCE_FRESHNESS_UNVERIFIED:ES0902" in doc["bootstrap"]["pendingConditions"])
    t.vacio("E-14 valida contra el schema", _validar(doc))
    for etiqueta in ("PARCIAL", "SIN CONFIGURAR", "VIGENCIA SIN VERIFICAR"):
        t.no_contiene("E-14 no trae la etiqueta %s" % etiqueta, etiqueta, salida)
    codigo, salida, _ = _cli(["harness", "--json", "--proyecto", str(_proyecto())])
    doc = json.loads(salida)
    t.igual("E-14 READY en ingles", "READY", doc["bootstrap"]["status"])
    t.vacio("E-14 el READY tambien valida", _validar(doc))


def test_e19_reiniciar_bienvenida_la_vuelve_a_mostrar(t):
    """E-19 (la mitad de la CLI) — `harness --reiniciar-bienvenida` pone firstRunShown en false
    y la sesion siguiente muestra la bienvenida completa."""
    proy = _proyecto()
    _sesion(proy)
    _, mensaje, _, _ = _sesion(proy)
    t.no_contiene("E-19 ya se habia mostrado", "GCBA Development Harness", mensaje or "")
    codigo, salida, _ = _cli(["harness", "--reiniciar-bienvenida", "--proyecto", str(proy)])
    t.igual("E-19 --reiniciar-bienvenida sale 0", 0, codigo)
    t.contiene("E-19 y dice que va a pasar", "bienvenida completa", salida)
    t.igual("E-19 deja firstRunShown: false", False, _estado(proy)["welcome"]["firstRunShown"])
    t.vacio("E-19 lo que escribe valida", _validar(_estado(proy)))
    _, mensaje, _, _ = _sesion(proy)
    t.contiene("E-19 la sesion siguiente muestra la bienvenida", "GCBA Development Harness",
               mensaje or "")
    # Donde el harness no esta instalado no escribe nada.
    vacio = Path(tempfile.mkdtemp(prefix="bv-sin-harness-"))
    codigo, _, _ = _cli(["harness", "--reiniciar-bienvenida", "--proyecto", str(vacio)])
    t.igual("E-19 sin harness instalado sale 2", 2, codigo)
    t.igual("E-19 y no crea el estado", False,
            (vacio / ".claude" / "harness.installation.json").exists())
    shutil.rmtree(str(vacio), ignore_errors=True)


def _setup(proy, transporte):
    """setup con la configuracion completa: no pregunta nada."""
    _escribir(proy / ".env", "JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    _json(proy / ".claude" / "harness.integraciones.json",
          {"jira": {"enabled": True, "baseUrl": "https://jira", "usuario": "a@b"},
           "gitlab": {"enabled": True, "baseUrl": "https://gitlab"}})
    return _cli(["setup", "--proyecto", str(proy)], transporte)


def _seccion_estado(salida):
    partes = salida.split("Estado\n" + "-" * 48 + "\n", 1)
    return partes[1] if len(partes) == 2 else ""


# Lo que contesta GitLab cuando el token sirve.
_GITLAB_OK = {"/user": (200, '{"username":"x"}'),
              "personal_access_tokens/self": (200, '{"scopes":["read_api"]}')}


def test_e21_setup_imprime_el_estado_del_resolvedor(t):
    """E-21 — setup ya no dice HARNESS READY fijo: dice el estado del resolvedor. Con una
    integracion caida, ni READY ni "listo"."""
    import socket
    transporte = _Transporte(dict(_GITLAB_OK, jira=socket.timeout()))
    codigo, salida, _ = _setup(_proyecto(), transporte)
    t.igual("E-21 caida: setup sale 0", 0, codigo)
    t.verdadero("E-21 caida: jira se intento de verdad",
                any("jira" in u for u in transporte.llamadas))
    t.no_contiene("E-21 caida: no dice HARNESS READY", "HARNESS READY", salida)
    estado = _seccion_estado(salida)
    t.verdadero("E-21 caida: la seccion Estado es la linea del resolvedor",
                estado.startswith("Harness GCBA ◐ PARCIAL"))
    t.contiene("E-21 caida: nombra a Jira caido", "Jira SIN CONEXIÓN", estado)
    # "listo" en cualquier forma, en todo lo que lee la persona. Las lineas `evento=` son el
    # registro estable de eventos del bootstrap (integraciones-bootstrap): `harness.listo` es
    # el nombre de un evento, no algo que se le dice a la persona.
    humano = "\n".join(l for l in salida.split("\n") if not l.strip().startswith("evento="))
    t.igual("E-21 caida: nada dice listo", None, _LISTO.search(humano))
    t.igual("E-21 caida: nada dice READY", None, re.search(r"\bREADY\b", humano))
    # Con todo disponible dice LISTO: la palabra sale del estado, no esta fija.
    codigo, salida, _ = _setup(_proyecto(), _Transporte(dict(
        _GITLAB_OK, **{"jira": (200, "{}"), "search/jql": (200, "{}"),
                       "attachment/meta": (200, "{}")})))
    t.igual("E-21 todo disponible: sale 0", 0, codigo)
    t.verdadero("E-21 todo disponible: la linea dice LISTO",
                _seccion_estado(salida).startswith("Harness GCBA ✓ LISTO"))
