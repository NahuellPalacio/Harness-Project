# La Context Bar, del lado del resolvedor: harness-installation/1.1, la migracion desde 1.0,
# los tres componentes de runtime, la senal de vida y lo que se muestra.
#
# Spec: docs/cambios/bloque-1-context-bar/spec.md. Cada test nombra su escenario.
#
# La segunda mitad, al final del archivo: el renderizador de la barra (E-10, E-16, E-21, E-22,
# E-23, E-37, E-38, E-39), la seccion de `harness` (E-18, E-19, E-20) y los textos (E-24, E-25).
# Lo del instalador de verdad (E-07, E-08, E-26, E-31, E-32, E-36) esta en
# tests/casos/54-context-bar-instalador.ps1, que instala.
import importlib.util
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
HOOK = RAIZ / "comun" / "hooks" / "session-start.py"
LIB = RAIZ / "comun" / "hooks" / "lib" / "bienvenida.py"
SCHEMA = RAIZ / "comun" / "schemas" / "harness-installation-state.schema.json"


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


B = _cargar("bienvenida_53", LIB)
ARMADOR = _cargar("armador_53", RAIZ / "comun" / "bin" / "contexto-armar.py")

TODAS = ("ES0901", "ES0902", "ES0903", "GuiaDGISIS", "Obelisco", "PC0901")
SESION = "s-cb-53-actual"
OTRA = "s-cb-53-anterior"
VERSION_BARRA = "1.0.0"
_LISTO = re.compile(r"list[oa]s?", re.IGNORECASE)


# -- el proyecto de prueba -----------------------------------------------------

def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def _json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False))


def _fuente(estado):
    return {"state": estado, "registry_version": "6.3", "observed_version": None,
            "attachmentId": None, "filename": None, "size": None, "created": None,
            "observed_sha256": None, "registry_sha256": None, "downloaded": False,
            "effectiveRisk": "MEDIUM", "derived_impact": [], "stale_derived": [],
            "blocking": estado not in ("CURRENT", "RETIRED"), "evidence": []}


def _comando(proy):
    return "python '%s/.claude/harness/bin/desarrollo/contabilidad/statusline.py'" % proy.as_posix()


def _proyecto(harness=("comun", "desarrollo"), version="0.22.0", fuentes=None, registrada=True,
              renderizador=True, senal=None, instalacion=None, schemas_seguridad=True,
              contabilidad=True):
    """Un proyecto instalado, en READY salvo la barra: registrada en settings.json y con el
    renderizador en disco, sin senal de vida salvo que se pida.

    `senal`: None (no hay), un dict con lo que cambia sobre una senal buena de SESION, o un
    texto crudo.
    """
    proy = Path(tempfile.gettempdir()) / ("harness-cb-" + uuid.uuid4().hex[:8])
    claude = proy / ".claude"
    _json(claude / "harness.config.json", {"usuario": "Nahue"})
    _json(claude / "harness.lock.json", {"version": version, "harness": list(harness),
                                         "instalado": "2026-09-24 10:00:00", "archivos": []})
    _json(claude / "harness.capacidades.json", {
        "schema_version": "integraciones/1.0", "version_harness": version,
        "integraciones": {n: {"estado": "AVAILABLE", "motivo": "",
                              "verificado_en": "2026-09-24T10:00:00", "capacidades": []}
                          for n in ("jira", "gitlab")}, "capacidades": {}})
    estados = fuentes or {s: "CURRENT" for s in TODAS}
    _json(claude / "harness.fuentes.json", {
        "schema_version": "sources-state/1.1", "verified_at": "2026-09-23T12:00:00",
        "ficha": None, "decisions": {}, "warnings": [], "pending_count": 0,
        "sources": {s: _fuente(e) for s, e in estados.items()}})
    h = claude / "harness"
    bin_d = h / "bin" / "desarrollo"
    if contabilidad:
        for n in ("__init__.py", "libro.py", "barra.py"):
            _escribir(bin_d / "contabilidad" / n, "# prueba\n")
    _escribir(bin_d / "contabilidad" / "adaptadores" / "claude_code.py", "# adaptador\n")
    if renderizador:
        _escribir(bin_d / "contabilidad" / "statusline.py",
                  'INTEGRATION_VERSION = "%s"\n' % VERSION_BARRA)
    for n in ("__init__.py", "libro.py", "resumen.py", "reporte.py"):
        _escribir(bin_d / "reporte_seguridad" / n, "# prueba\n")
    if schemas_seguridad:
        for n in B.SCHEMAS_DE_SEGURIDAD:
            _escribir(h / "schemas" / n, (RAIZ / "comun" / "schemas" / n).read_text(encoding="utf-8"))
    _escribir(h / "hooks" / "session-start.py", "# el hook\n")
    if registrada:
        _json(claude / "settings.json", {"statusLine": {"type": "command", "command": _comando(proy)}})
    if instalacion is not None:
        ruta = claude / "harness.installation.json"
        if isinstance(instalacion, str):
            _escribir(ruta, instalacion)
        else:
            _json(ruta, instalacion)
    if senal is not None:
        _senal(proy, **senal) if isinstance(senal, dict) else _escribir(
            claude / "runtime" / "contextbar.json", senal)
    return proy


def _senal(proy, sesion=SESION, block4=B.BLOCK4_OK, version=VERSION_BARRA,
           momento="2099-01-01T00:00:00", **de_mas):
    """Una senal de vida como la escribe la barra, con escribir_senal_de_vida. `momento` por
    defecto es posterior a cualquier registro de la instalacion."""
    B.escribir_senal_de_vida(str(proy), sesion, block4, version, momento=momento)
    if de_mas:
        ruta = proy / ".claude" / "runtime" / "contextbar.json"
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        doc.update(de_mas)
        _json(ruta, doc)


def _cambiar_statusline(proy, sufijo=" '--otro'"):
    _json(proy / ".claude" / "settings.json",
          {"statusLine": {"type": "command", "command": _comando(proy) + sufijo}})


def _estado(proy):
    return json.loads((proy / ".claude" / "harness.installation.json").read_text(encoding="utf-8"))


def _barra(doc):
    return doc["runtimeComponents"]["contextBar"]


def _sesion(proy, sesion=SESION, comando=None):
    """Corre session-start.py como lo invoca Claude Code. (codigo, systemMessage, crudo)."""
    payload = {"session_id": sesion, "cwd": str(proy), "hook_event_name": "SessionStart",
               "source": "startup"}
    r = subprocess.run(comando or [sys.executable, str(HOOK)],
                       input=json.dumps(payload).encode("utf-8"),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    crudo = r.stdout.decode("utf-8")
    if not crudo.strip():
        return r.returncode, None, crudo
    return r.returncode, json.loads(crudo).get("systemMessage"), crudo


def _claves(nodo, nombre, ruta="$"):
    """Donde aparece `nombre` como clave, en cualquier nivel. La prosa de `description` no
    cuenta: el schema puede nombrar allOf para decir por que no lo usa."""
    salida = []
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k == nombre:
                salida.append("%s.%s" % (ruta, k))
            salida += _claves(v, nombre, "%s.%s" % (ruta, k))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            salida += _claves(v, nombre, "%s[%d]" % (ruta, i))
    return salida


def _validar(doc):
    esquema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ARMADOR.controlar_soporte(esquema)
    return ARMADOR.validar(doc, esquema)


def _fila(texto, rotulo):
    for linea in texto.split("\n"):
        if linea.strip().startswith(rotulo):
            return linea
    return ""


def _registrado_y_visto(**kwargs):
    """Instalado con la barra probada, y una senal de vida de otra sesion, dibujada despues
    del registro: sin reinicio pendiente. Es el punto de partida de casi todo."""
    proy = _proyecto(**kwargs)
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-24T10:00:00")
    _senal(proy, sesion=OTRA, momento="2026-09-24T10:00:01")
    return proy


# -- E-01 — la migracion ---------------------------------------------------------------

def _un_1_0(proy):
    """Lo que 0.21.0 dejaba en disco para este mismo proyecto: el 1.1 de hoy sin lo nuevo."""
    doc = B.resolver(str(proy), momento="2026-09-20T10:00:00")
    for clave in ("runtimeComponents", "updatedAt"):
        doc.pop(clave)
    doc["schema_version"] = "harness-installation/1.0"
    doc["welcome"] = {"firstRunShown": True, "lastShownAt": "2026-09-20T10:00:00",
                      "upgradeFrom": "0.20.0"}
    doc["installedAt"] = "2026-09-01T09:00:00"
    doc["notaDeOtraHerramienta"] = {"x": 1}
    return doc


def test_e01_un_1_0_pasa_a_1_1_sin_perder_ningun_campo(t):
    """E-01 — migrar conserva todo; y el registro de un -Update lo escribe como 1.1 con cada
    campo del 1.0 y su valor."""
    proy = _registrado_y_visto()
    viejo = _un_1_0(proy)
    t.vacio("E-01 el 1.0 armado tiene la forma de 0.21.0",
            [] if B._previo_valido(viejo) else ["no es un 1.0 valido"])
    migrado = B.migrar(viejo)
    t.igual("E-01 migrar da 1.1", "harness-installation/1.1", migrado["schema_version"])
    for clave, valor in viejo.items():
        if clave != "schema_version":
            t.igual("E-01 migrar conserva %s" % clave, valor, migrado.get(clave))

    _json(proy / ".claude" / "harness.installation.json", viejo)
    B.registrar_instalacion(str(proy), barra_probada=True)
    escrito = _estado(proy)
    t.igual("E-01 se escribe como 1.1", "harness-installation/1.1", escrito["schema_version"])
    for clave, valor in viejo.items():
        if clave not in ("schema_version", "bootstrap"):
            t.igual("E-01 el 1.1 escrito conserva %s" % clave, valor, escrito.get(clave))
    # bootstrap se recalcula siempre: lo que sale del 1.0 sigue igual, y lo unico nuevo es la
    # condicion de la barra, que 0.21.0 no tenia y este registro acaba de ver por primera vez.
    boot = escrito["bootstrap"]
    t.igual("E-01 el 1.1 escrito conserva los bloqueos", viejo["bootstrap"]["blockingConditions"],
            boot["blockingConditions"])
    t.igual("E-01 y los pendientes del 1.0", viejo["bootstrap"]["pendingConditions"],
            [c for c in boot["pendingConditions"] if not B.es_de_runtime(c)])
    t.igual("E-01 lo nuevo es solo la barra recien vista", ["CONTEXT_BAR_RELOAD_REQUIRED"],
            [c for c in boot["pendingConditions"] if B.es_de_runtime(c)])
    t.verdadero("E-01 y suma runtimeComponents", "runtimeComponents" in escrito)
    t.vacio("E-01 y valida contra el schema", _validar(escrito))


def test_e01_un_1_0_que_no_se_migra_es_ilegible(t):
    """E-01 — un 1.0 roto, o una version desconocida: INSTALLATION_STATE_UNREADABLE, como hoy,
    y la sesion lo reescribe como 1.1."""
    casos = (("1.0 con un tipo roto", dict(_un_1_0(_proyecto()), installed="si")),
             ("1.0 sin bootstrap", {k: v for k, v in _un_1_0(_proyecto()).items()
                                    if k != "bootstrap"}),
             ("version desconocida", dict(_un_1_0(_proyecto()),
                                          schema_version="harness-installation/9.9")))
    for rotulo, doc in casos:
        proy = _registrado_y_visto(instalacion=doc)
        _json(proy / ".claude" / "harness.installation.json", doc)
        t.igual("E-01 %s: migrar no lo toma" % rotulo, None, B.migrar(doc))
        res = B.resolver(str(proy))
        t.verdadero("E-01 %s: INSTALLATION_STATE_UNREADABLE" % rotulo,
                    "INSTALLATION_STATE_UNREADABLE" in res["bootstrap"]["pendingConditions"])
        codigo, _, _ = _sesion(proy)
        t.igual("E-01 %s: el hook sale 0" % rotulo, 0, codigo)
        t.igual("E-01 %s: y queda un 1.1" % rotulo, "harness-installation/1.1",
                _estado(proy).get("schema_version"))


# -- E-02 / E-03 — el 1.1 valida y los tres componentes tienen estado ------------------

def test_e02_el_1_1_que_escriben_el_hook_el_registro_y_la_cli_valida(t):
    """E-02 — el hook en cada estado de la barra, el registro que llama install.ps1 y el
    `--reiniciar-bienvenida` de la CLI escriben algo que valida contra el schema 1.1."""
    esquema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ARMADOR.controlar_soporte(esquema)
    t.igual("E-02 el schema es 1.1", ["harness-installation/1.1"],
            esquema["properties"]["schema_version"]["enum"])
    t.vacio("E-02 sin allOf: el validador de subconjunto no lo lee", _claves(esquema, "allOf"))
    t.verdadero("E-02 el schema declara runtimeComponents con los tres",
                esquema["properties"]["runtimeComponents"]["required"]
                == ["block4Accounting", "contextBar", "securityReporting"])
    casos = (("ACTIVE", _registrado_y_visto(), {"sesion": OTRA}),
             ("CONFIGURED", _registrado_y_visto(), {}),
             ("RELOAD_REQUIRED", _proyecto(), {}),
             ("ERROR", _proyecto(senal={"block4": B.BLOCK4_SOURCE_UNAVAILABLE}), {}),
             ("solo analisis", _proyecto(harness=("comun", "analisis")), {}))
    for rotulo, proy, kw in casos:
        codigo, _, _ = _sesion(proy, **kw)
        t.igual("E-02 %s: el hook sale 0" % rotulo, 0, codigo)
        t.vacio("E-02 %s: lo que escribe el hook valida" % rotulo, _validar(_estado(proy)))
        t.verdadero("E-02 %s: y lo vuelve a leer como propio" % rotulo,
                    B._previo_valido(_estado(proy)))
    esperado = {"ACTIVE": "ACTIVE", "CONFIGURED": "CONFIGURED", "RELOAD_REQUIRED": "RELOAD_REQUIRED",
                "ERROR": "ERROR"}
    for rotulo, proy, _ in casos[:4]:
        t.igual("E-02 %s: el caso es el que dice" % rotulo, esperado[rotulo],
                _barra(_estado(proy))["state"])
    proy = _proyecto()
    B.registrar_instalacion(str(proy), barra_probada=True)
    t.vacio("E-02 lo que escribe el registro de la instalacion valida", _validar(_estado(proy)))
    B.reiniciar_bienvenida(str(proy))
    t.vacio("E-02 lo que escribe --reiniciar-bienvenida valida", _validar(_estado(proy)))


def test_e03_despues_de_instalar_los_tres_componentes_tienen_estado(t):
    """E-03 — con y sin `desarrollo`, cada componente tiene un estado de componente, nunca
    AVAILABLE."""
    for rotulo, proy in (("desarrollo", _proyecto()),
                         ("solo analisis", _proyecto(harness=("comun", "analisis")))):
        doc = B.registrar_instalacion(str(proy), barra_probada=True)
        for clave, _, _, _ in B.COMPONENTES:
            estado = (doc["runtimeComponents"].get(clave) or {}).get("state")
            t.verdadero("E-03 %s: %s tiene estado" % (rotulo, clave),
                        estado in B.ESTADOS_DE_COMPONENTE)
            t.verdadero("E-03 %s: %s no usa AVAILABLE" % (rotulo, clave), estado != "AVAILABLE")
    doc = B.registrar_instalacion(str(_proyecto()), barra_probada=True)
    t.igual("E-03 con desarrollo: Block 4 ACTIVE", "ACTIVE",
            doc["runtimeComponents"]["block4Accounting"]["state"])
    t.igual("E-03 con desarrollo: Security Reporting ACTIVE", "ACTIVE",
            doc["runtimeComponents"]["securityReporting"]["state"])
    t.igual("E-03 y la barra recien registrada pide reinicio", "RELOAD_REQUIRED",
            _barra(doc)["state"])


# -- E-04 / E-05 / E-06 / E-34 — la activacion se prueba con la senal de vida ---------

def test_e04_sin_senal_de_vida_la_barra_no_es_active(t):
    """E-04 — renderizador en disco y statusLine registrado, sin senal de vida: no es ACTIVE,
    ni en la sesion ni en la CLI, tampoco sin reinicio pendiente."""
    proy = _registrado_y_visto()
    _sesion(proy, sesion=OTRA)          # la sesion que vio la barra deja el reinicio saldado
    t.igual("E-04 el reinicio quedo saldado", False, _barra(_estado(proy))["reloadRequired"])
    (proy / ".claude" / "runtime" / "contextbar.json").unlink()
    for rotulo, sesion in (("sesion", SESION), ("CLI", None)):
        barra = _barra(B.resolver(str(proy), sesion=sesion))
        t.verdadero("E-04 %s: no es ACTIVE" % rotulo, barra["state"] != "ACTIVE")
        t.igual("E-04 %s: es CONFIGURED" % rotulo, "CONFIGURED", barra["state"])
        t.igual("E-04 %s: installed y configured" % rotulo, (True, True),
                (barra["installed"], barra["configured"]))
    barra = _barra(B.resolver(str(_proyecto()), sesion=SESION))
    t.verdadero("E-04 recien instalada sin senal tampoco", barra["state"] != "ACTIVE")


def test_e05_registrada_y_probada_sin_senal_de_esta_sesion(t):
    """E-05 — CONFIGURED sin cambio pendiente; RELOAD_REQUIRED si la huella cambio, por un
    registro nuevo o por un statusLine distinto del registrado."""
    proy = _registrado_y_visto()
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-05 senal de otra sesion, sin cambio: CONFIGURED", "CONFIGURED", _barra(doc)["state"])
    t.igual("E-05 y sin reinicio", False, _barra(doc)["reloadRequired"])
    t.igual("E-05 CONFIGURED no suma condicion", [],
            [c for c in doc["bootstrap"]["pendingConditions"] if B.es_de_runtime(c)])

    proy = _proyecto()
    doc = B.registrar_instalacion(str(proy), barra_probada=True)
    t.igual("E-05 registro nuevo sin senal: RELOAD_REQUIRED", "RELOAD_REQUIRED", _barra(doc)["state"])
    t.igual("E-05 con reloadRequired", True, _barra(doc)["reloadRequired"])
    t.verdadero("E-05 y su condicion", "CONTEXT_BAR_RELOAD_REQUIRED" in doc["bootstrap"]["pendingConditions"])

    proy = _registrado_y_visto()
    _cambiar_statusline(proy)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-05 statusLine distinto del registrado: RELOAD_REQUIRED", "RELOAD_REQUIRED",
            _barra(doc)["state"])
    t.igual("E-05 PARTIAL, nunca BLOCKED", "PARTIAL", doc["bootstrap"]["status"])


def test_e06_senal_de_esta_sesion_con_la_huella_y_block4_ok_es_active(t):
    """E-06 — ACTIVE y activeInCurrentSession: true, sin condicion y READY."""
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-06 ACTIVE", "ACTIVE", _barra(doc)["state"])
    t.igual("E-06 activeInCurrentSession", True, _barra(doc)["activeInCurrentSession"])
    t.igual("E-06 READY", "READY", doc["bootstrap"]["status"])
    _sesion(proy, sesion=SESION)
    t.igual("E-06 y asi queda escrito por el hook", (("ACTIVE", True)),
            (_barra(_estado(proy))["state"], _barra(_estado(proy))["activeInCurrentSession"]))
    _senal(proy, sesion=SESION, version="0.9.0")
    t.verdadero("E-06 con otra version del renderizador que la registrada, no",
                _barra(B.resolver(str(proy), sesion=SESION))["state"] != "ACTIVE")


def test_e34_active_en_la_sesion_va_aparte_de_installed_y_configured(t):
    """E-34 — la senal de otra sesion: instalada y configurada, no activa en esta. En la CLI
    es ACTIVE de la ultima sesion vista, y activeInCurrentSession sigue en false."""
    proy = _registrado_y_visto()
    barra = _barra(B.resolver(str(proy), sesion=SESION))
    t.igual("E-34 installed", True, barra["installed"])
    t.igual("E-34 configured", True, barra["configured"])
    t.igual("E-34 no activa en esta sesion", False, barra["activeInCurrentSession"])
    t.verdadero("E-34 ni ACTIVE", barra["state"] != "ACTIVE")
    cli = _barra(B.resolver(str(proy)))
    t.igual("E-34 la CLI: ACTIVE de la ultima sesion", ("ACTIVE", False, OTRA),
            (cli["state"], cli["activeInCurrentSession"], cli["lastSessionId"]))
    t.contiene("E-34 y lo dice", "Context Bar ACTIVA (última sesión: %s)" % OTRA[:8],
               B.renderizar_linea(B.resolver(str(proy))))


# -- E-09 / E-14 — ERROR y PARTIAL -------------------------------------------------------

def test_e09_block4_no_disponible_es_error(t):
    """E-09 — la senal de esta sesion con SOURCE_UNAVAILABLE, o el Bloque 4 en ERROR: la barra
    no es ACTIVE, es ERROR con CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE."""
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION, block4=B.BLOCK4_SOURCE_UNAVAILABLE)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-09 ERROR", "ERROR", _barra(doc)["state"])
    t.igual("E-09 con su codigo", "CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE", _barra(doc)["errorCode"])
    t.verdadero("E-09 y su condicion",
                "CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE" in doc["bootstrap"]["pendingConditions"])
    # El libro de la sesion que vio la barra existe y no se abre: el Bloque 4 esta en ERROR, y
    # una senal OK de la barra no alcanza.
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION)
    (proy / ".claude" / "runtime" / "accounting" / SESION / "ledger.jsonl").mkdir(parents=True)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-09 libro ilegible: Block 4 ERROR", ("ERROR", "BLOCK4_LEDGER_UNREADABLE"),
            (doc["runtimeComponents"]["block4Accounting"]["state"],
             doc["runtimeComponents"]["block4Accounting"]["errorCode"]))
    t.igual("E-09 y la barra no es ACTIVE", ("ERROR", "CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE"),
            (_barra(doc)["state"], _barra(doc)["errorCode"]))


def test_e14_error_sale_como_error_sin_tilde_y_deja_partial(t):
    """E-14 — la barra, el Bloque 4 y el reporte de seguridad en ERROR: ERROR sin ✓, PARTIAL."""
    casos = (("contextBar", "Context Bar",
              lambda: _proyecto(senal={"block4": B.BLOCK4_SOURCE_UNAVAILABLE})),
             ("block4Accounting", "Block 4 Accounting", lambda: _proyecto(contabilidad=False)),
             ("securityReporting", "Security Reporting",
              lambda: _proyecto(schemas_seguridad=False)))
    for clave, nombre, armar in casos:
        proy = armar()
        doc = B.resolver(str(proy), sesion=SESION)
        t.igual("E-14 %s: ERROR" % clave, "ERROR", doc["runtimeComponents"][clave]["state"])
        t.igual("E-14 %s: PARTIAL" % clave, "PARTIAL", doc["bootstrap"]["status"])
        t.igual("E-14 %s: nada bloquea" % clave, [], doc["bootstrap"]["blockingConditions"])
        fila = _fila(B.renderizar_bienvenida(doc).split("Observabilidad", 1)[-1], nombre)
        t.contiene("E-14 %s: la fila dice ERROR" % clave, "ERROR", fila)
        t.no_contiene("E-14 %s: sin ✓" % clave, "✓", fila)
        t.contiene("E-14 %s: y la accion" % clave, "Acción requerida", B.renderizar_bienvenida(doc))


# -- E-11 / E-12 / E-13 — la bienvenida ----------------------------------------------------

def test_e11_la_bienvenida_con_desarrollo_muestra_observabilidad(t):
    """E-11 — el bloque, con los tres, solo con `desarrollo`."""
    _, mensaje, _ = _sesion(_registrado_y_visto())
    t.contiene("E-11 la primera sesion muestra Observabilidad", "Observabilidad", mensaje or "")
    for nombre in ("Block 4 Accounting", "Context Bar", "Security Reporting"):
        t.verdadero("E-11 con %s" % nombre,
                    bool(_fila((mensaje or "").split("Observabilidad", 1)[-1], nombre)))
    completa = B.renderizar_bienvenida(B.resolver(str(_proyecto(harness=("comun", "analisis")))))
    t.no_contiene("E-11 sin desarrollo, no", "Observabilidad", completa)


def test_e12_reload_required_sale_como_requiere_reinicio(t):
    """E-12 — REQUIERE REINICIO sin ✓, y abajo la accion con el texto de la spec."""
    proy = _proyecto()
    B.registrar_instalacion(str(proy), barra_probada=True)
    completa = B.renderizar_bienvenida(B.resolver(str(proy), sesion=SESION))
    fila = _fila(completa.split("Observabilidad", 1)[-1], "Context Bar")
    t.contiene("E-12 REQUIERE REINICIO", "REQUIERE REINICIO", fila)
    t.no_contiene("E-12 sin ✓", "✓", fila)
    accion = completa.split("Acción requerida", 1)
    t.igual("E-12 hay Acción requerida", 2, len(accion))
    t.contiene("E-12 con el texto de la spec", B.REINICIAR, accion[-1])
    t.igual("E-12 el texto de la spec, literal",
            "Context Bar configurada. Reiniciá la sesión de Claude Code para activarla.", B.REINICIAR)
    t.no_contiene("E-12 y no se repite en el estado general", "Reiniciá",
                  completa.split("Estado general", 1)[1].split("Integraciones", 1)[0])


def test_e13_active_sale_como_activa_o_activo_con_tilde(t):
    """E-13 — ✓ ACTIVA la barra, ✓ ACTIVO los otros dos."""
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION)
    obs = B.renderizar_bienvenida(B.resolver(str(proy), sesion=SESION)).split("Observabilidad", 1)[-1]
    for nombre, texto in (("Context Bar", "✓ ACTIVA"), ("Block 4 Accounting", "✓ ACTIVO"),
                          ("Security Reporting", "✓ ACTIVO")):
        t.verdadero("E-13 %s: %s" % (nombre, texto), _fila(obs, nombre).endswith(texto))
    t.no_contiene("E-13 sin accion requerida", "Acción requerida", obs)


# -- E-15 / E-16 — sin red y sin modelo ------------------------------------------------

_ENVOLTORIO = r'''
import atexit, json, os, runpy, sys, types
HOOK, MARCA = sys.argv[1], sys.argv[2]
intentos = []

class _Prohibido(types.ModuleType):
    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        intentos.append("%s.%s" % (self.__name__, nombre))
        raise OSError("red prohibida (%s.%s)" % (self.__name__, nombre))

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


def test_e15_session_start_no_abre_ninguna_conexion_con_la_barra(t):
    """E-15 — con socket y urllib reemplazados por unos que fallan, en cada estado de la barra,
    nadie intento usarlos y la barra salio en el mensaje."""
    activa = _registrado_y_visto()
    _senal(activa, sesion=SESION)
    for rotulo, proy in (("ACTIVE", activa), ("RELOAD_REQUIRED", _proyecto()),
                         ("ERROR", _proyecto(senal={"block4": B.BLOCK4_SOURCE_UNAVAILABLE}))):
        tmp = Path(tempfile.mkdtemp(prefix="cb-red-"))
        (tmp / "sin_red.py").write_text(_ENVOLTORIO, encoding="utf-8")
        codigo, mensaje, _ = _sesion(proy, comando=[sys.executable, str(tmp / "sin_red.py"),
                                                    str(HOOK), str(tmp / "marca.json")])
        datos = json.loads((tmp / "marca.json").read_text(encoding="utf-8")) \
            if (tmp / "marca.json").is_file() else None
        shutil.rmtree(str(tmp), ignore_errors=True)
        t.igual("E-15 %s: sale 0" % rotulo, 0, codigo)
        t.verdadero("E-15 %s: el envoltorio corrio" % rotulo, datos is not None)
        t.igual("E-15 %s: ningun intento de red" % rotulo, [], (datos or {}).get("intentos"))
        t.contiene("E-15 %s: y la barra esta en el mensaje" % rotulo, "Context Bar", mensaje or "")


# -- E-17 — la linea compacta -----------------------------------------------------------------

def test_e17_la_linea_no_repite_los_numeros_de_la_barra(t):
    """E-17 — con la barra ACTIVE la linea dice solo `Context Bar ACTIVA`, y ningun numero,
    aunque el libro de la sesion los tenga."""
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION)
    libro = proy / ".claude" / "runtime" / "accounting" / SESION
    _escribir(libro / "ledger.jsonl", json.dumps({"tokens": 128000, "costUsd": 1.82}) + "\n")
    _json(libro / "summary.json", {"tokens": 128000, "costUsd": 1.82, "contextPercent": 43})
    _sesion(proy, sesion=SESION)
    _, mensaje, _ = _sesion(proy, sesion=SESION)
    mensaje = mensaje or ""
    t.verdadero("E-17 es la linea", mensaje.startswith("Harness GCBA ✓ LISTO"))
    t.igual("E-17 la barra es un segmento, y dice solo eso", ["Context Bar ACTIVA"],
            [p for p in mensaje.split(" · ") if p.startswith("Context Bar")])
    t.igual("E-17 ningun numero en la linea", None, re.search(r"\d", mensaje))
    for parte in ("tok", "USD", "%", "Contexto", "Presupuesto", "Block 4", "Security"):
        t.no_contiene("E-17 no dice %s" % parte, parte, mensaje)


# -- E-27 / E-28 — el reinicio y el aviso de actualizacion ---------------------------------

def test_e27_el_aviso_de_reinicio_se_va_con_la_senal_de_la_huella_nueva(t):
    """E-27 — despues de un registro que cambio las huellas, una senal con la huella vieja o de
    antes del registro no lo saca; una con la nueva, dibujada despues, si, y queda escrito."""
    proy = _registrado_y_visto()
    _cambiar_statusline(proy)
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-25T10:00:00")
    t.igual("E-27 el registro marco reinicio", True, _barra(_estado(proy))["reloadRequired"])
    B.escribir_senal_de_vida(str(proy), SESION, B.BLOCK4_OK, VERSION_BARRA,
                             momento="2026-09-25T09:59:59")
    t.igual("E-27 una senal de antes del registro no alcanza", "RELOAD_REQUIRED",
            _barra(B.resolver(str(proy), sesion=SESION))["state"])
    ruta = proy / ".claude" / "runtime" / "contextbar.json"
    vieja = json.loads(ruta.read_text(encoding="utf-8"))
    vieja.update(lastRenderedAt="2026-09-25T10:00:05",
                 configurationFingerprint=B.huella_statusline({"type": "command",
                                                               "command": _comando(proy)}))
    _json(ruta, vieja)
    t.igual("E-27 ni una con la huella vieja", "RELOAD_REQUIRED",
            _barra(B.resolver(str(proy), sesion=SESION))["state"])
    B.escribir_senal_de_vida(str(proy), OTRA, B.BLOCK4_OK, VERSION_BARRA,
                             momento="2026-09-25T10:00:05")
    _, mensaje, _ = _sesion(proy, sesion=SESION)
    t.no_contiene("E-27 con la nueva el aviso se va", "REINICIO", mensaje or "")
    t.no_contiene("E-27 y no pide reiniciar", "Reiniciá", mensaje or "")
    t.igual("E-27 y queda escrito", False, _barra(_estado(proy))["reloadRequired"])
    (ruta).unlink()
    t.igual("E-27 aunque despues la senal se borre", "CONFIGURED",
            _barra(B.resolver(str(proy), sesion=SESION))["state"])


def test_e28_el_aviso_de_actualizacion_tiene_dos_lineas(t):
    """E-28 — un -Update: la version, la linea de la Context Bar, y la linea compacta sin
    repetir la barra."""
    proy = _registrado_y_visto(version="0.21.0")
    _sesion(proy, sesion=OTRA)
    _json(proy / ".claude" / "harness.lock.json", {"version": "0.22.0",
                                                   "harness": ["comun", "desarrollo"],
                                                   "instalado": "2026-09-25 10:00:00",
                                                   "archivos": []})
    _escribir(proy / ".claude" / "harness" / "bin" / "desarrollo" / "contabilidad" / "statusline.py",
              'INTEGRATION_VERSION = "%s"\n# renderizador nuevo\n' % VERSION_BARRA)
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2030-01-01T00:00:00")
    _, mensaje, _ = _sesion(proy, sesion=SESION)
    lineas = (mensaje or "").split("\n")
    t.igual("E-28 la version", "Harness GCBA actualizado: 0.21.0 → 0.22.0 ✓", lineas[0])
    t.igual("E-28 renderizador cambiado: la segunda pide reinicio",
            "Context Bar actualizada · reinicio de Claude Code requerido.",
            lineas[1] if len(lineas) > 1 else None)
    t.igual("E-28 y despues la linea, nada mas", 3, len(lineas))
    t.no_contiene("E-28 la linea no repite la barra", "Context Bar", lineas[-1])

    proy = _registrado_y_visto(version="0.21.0")
    _sesion(proy, sesion=OTRA)
    _json(proy / ".claude" / "harness.lock.json", {"version": "0.22.0",
                                                   "harness": ["comun", "desarrollo"],
                                                   "instalado": "2026-09-25 10:00:00",
                                                   "archivos": []})
    B.registrar_instalacion(str(proy), barra_probada=True)
    _senal(proy, sesion=SESION)
    _, mensaje, _ = _sesion(proy, sesion=SESION)
    lineas = (mensaje or "").split("\n")
    t.igual("E-28 sin cambio de huellas y la barra viva: activa", "Context Bar activa.",
            lineas[1] if len(lineas) > 1 else None)
    t.verdadero("E-28 y la linea", len(lineas) == 3 and lineas[2].startswith("Harness GCBA ✓ LISTO"))


# -- E-29 / E-30 — lo que no se dice ------------------------------------------------------

def test_e29_bloqueado_nada_dice_listo(t):
    """E-29 — con una alerta de integridad y la barra ACTIVE: ni la bienvenida, ni la linea, ni
    el aviso de actualizacion dicen que algo este listo."""
    fuentes = dict({s: "CURRENT" for s in TODAS}, ES0902="SOURCE_INTEGRITY_ALERT")
    proy = _registrado_y_visto(fuentes=fuentes)
    _senal(proy, sesion=SESION)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-29 BLOCKED", "BLOCKED", doc["bootstrap"]["status"])
    t.igual("E-29 con la barra ACTIVE", "ACTIVE", _barra(doc)["state"])
    doc["welcome"]["upgradeFrom"] = "0.21.0"
    for rotulo, texto in (("bienvenida", B.renderizar_bienvenida(doc)),
                          ("linea", B.renderizar_linea(doc)),
                          ("aviso de actualizacion", B.renderizar_actualizacion(doc))):
        t.igual("E-29 la %s no dice listo" % rotulo, None, _LISTO.search(texto))
    _, mensaje, _ = _sesion(proy, sesion=SESION)
    t.contiene("E-29 la persona ve BLOQUEADO", "BLOQUEADO", mensaje or "")
    t.igual("E-29 y nada listo", None, _LISTO.search(mensaje or "listo"))


def _huellas_del_arbol(raiz, salvo):
    salida = {}
    for dirpath, _, archivos in os.walk(str(raiz)):
        for n in archivos:
            ruta = os.path.join(dirpath, n)
            if os.path.normpath(ruta) != os.path.normpath(str(salvo)):
                with open(ruta, "rb") as f:
                    salida[os.path.relpath(ruta, str(raiz))] = f.read()
    return salida


def test_e30_security_reporting_active_no_dice_nada_de_la_aprobacion(t):
    """E-30 — ACTIVE es el pipeline disponible: ningun texto habla de aprobacion, y resolver,
    registrar y la sesion no tocan ningun archivo fuera de harness.installation.json, la
    evidencia de C2 incluida."""
    proy = _registrado_y_visto()
    _senal(proy, sesion=SESION)
    c2 = proy / ".claude" / "security" / "approval-evidence.json"
    _json(c2, {"control": "ES0902-C2", "state": "PENDING"})
    instalacion = proy / ".claude" / "harness.installation.json"
    antes = _huellas_del_arbol(proy, instalacion)
    doc = B.resolver(str(proy), sesion=SESION)
    t.igual("E-30 ACTIVE", "ACTIVE", doc["runtimeComponents"]["securityReporting"]["state"])
    B.registrar_instalacion(str(proy), barra_probada=True)
    _sesion(proy, sesion=SESION)
    _sesion(proy, sesion=SESION)
    t.igual("E-30 nada cambio fuera del estado de la instalacion", antes,
            _huellas_del_arbol(proy, instalacion))
    textos = (B.renderizar_bienvenida(doc), B.renderizar_linea(doc),
              json.dumps(doc["runtimeComponents"]["securityReporting"], ensure_ascii=False))
    for texto in textos:
        t.igual("E-30 ningun texto dice aprobado", None,
                re.search(r"aprob|approv|APROB|APPROV", texto))
    t.no_contiene("E-30 el modulo no nombra la evidencia de aprobacion", "approval",
                  LIB.read_text(encoding="utf-8"))


# -- E-33 / E-35 — sin churn y deterministico -------------------------------------------

def test_e33_dos_registros_iguales_dejan_el_archivo_igual(t):
    """E-33 — dos -Update sin cambios: el archivo igual byte a byte salvo updatedAt, y
    runtimeComponents intacto. Dos sesiones iguales tampoco lo reescriben."""
    proy = _registrado_y_visto()
    _sesion(proy, sesion=OTRA)
    ruta = proy / ".claude" / "harness.installation.json"
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-25T10:00:00")
    uno = ruta.read_bytes()
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-26T10:00:00")
    dos = ruta.read_bytes()
    sin_fecha = re.compile(rb'\n  "updatedAt": "[^"]*",')
    t.verdadero("E-33 updatedAt cambio", uno != dos)
    t.igual("E-33 lo demas, byte a byte", sin_fecha.sub(b"", uno), sin_fecha.sub(b"", dos))
    _sesion(proy, sesion=SESION)
    rc = _estado(proy)["runtimeComponents"]
    _sesion(proy, sesion=SESION)
    t.igual("E-33 dos sesiones iguales: runtimeComponents igual", rc,
            _estado(proy)["runtimeComponents"])


def test_e35_los_mismos_archivos_dan_los_mismos_estados(t):
    """E-35 — resolver en momentos distintos, sobre los mismos archivos, da los mismos estados y
    las mismas condiciones, para cada estado de la barra."""
    casos = (("ACTIVE", _registrado_y_visto(), OTRA), ("CONFIGURED", _registrado_y_visto(), SESION),
             ("RELOAD_REQUIRED", _proyecto(), SESION),
             ("ERROR", _proyecto(senal={"block4": B.BLOCK4_SOURCE_UNAVAILABLE}), SESION))
    for rotulo, proy, sesion in casos:
        vistas = []
        for momento in ("2026-09-24T10:00:00", "2026-09-24T10:00:01", "2031-01-01T00:00:00"):
            doc = B.resolver(str(proy), momento=momento, sesion=sesion)
            vistas.append(([doc["runtimeComponents"][c]["state"] for c, _, _, _ in B.COMPONENTES],
                           doc["bootstrap"]["pendingConditions"]))
        t.igual("E-35 %s: los mismos estados" % rotulo, [vistas[0]] * 3, vistas)
        t.igual("E-35 %s: la barra en el estado del caso" % rotulo, rotulo, vistas[0][0][1])


# -- la tabla de estados, fila por fila --------------------------------------------------

def test_la_tabla_de_estados_de_la_barra(t):
    """Las filas de la tabla de la spec que no tienen escenario propio."""
    doc = B.resolver(str(_proyecto(registrada=False)))
    t.igual("tabla: renderizador en disco y sin registrar: INSTALLED",
            ("INSTALLED", "CONTEXT_BAR_NOT_CONFIGURED"), (_barra(doc)["state"], _barra(doc)["errorCode"]))
    doc = B.resolver(str(_proyecto(registrada=False, renderizador=False)))
    t.igual("tabla: sin statusLine ni renderizador: NOT_CONFIGURED",
            ("NOT_CONFIGURED", "CONTEXT_BAR_NOT_INSTALLED"), (_barra(doc)["state"], _barra(doc)["errorCode"]))
    proy = _proyecto()
    _json(proy / ".claude" / "settings.json", {"statusLine": {"type": "command", "command": "npx ccstatusline"}})
    t.igual("tabla: un statusLine de otra herramienta no es la barra", "INSTALLED",
            _barra(B.resolver(str(proy)))["state"])
    proy = _proyecto()
    doc = B.registrar_instalacion(str(proy), barra_probada=False)
    t.igual("tabla: el comando no corre en los dos shells: NOT_CONFIGURED",
            ("NOT_CONFIGURED", "CONTEXT_BAR_CONFIGURATION_INVALID"),
            (_barra(doc)["state"], _barra(doc)["errorCode"]))
    t.igual("tabla: y la instalacion sigue: PARTIAL", "PARTIAL", doc["bootstrap"]["status"])
    proy = _proyecto()
    _escribir(proy / ".claude" / "settings.json", "{ roto")
    t.igual("tabla: settings.json ilegible: UNRESOLVED", ("UNRESOLVED", "CONTEXT_BAR_VALIDATION_UNRESOLVED"),
            (_barra(B.resolver(str(proy)))["state"], _barra(B.resolver(str(proy)))["errorCode"]))
    for rotulo, senal in (("rota", "{ no"), ("con un numero contable", None)):
        proy = _registrado_y_visto()
        if senal is None:
            _senal(proy, sesion=SESION, tokens=128000)
        else:
            _escribir(proy / ".claude" / "runtime" / "contextbar.json", senal)
        t.igual("tabla: senal %s: UNRESOLVED" % rotulo, "UNRESOLVED",
                _barra(B.resolver(str(proy), sesion=SESION))["state"])
    doc = B.resolver(str(_proyecto(harness=("comun", "analisis"))))
    t.igual("tabla: sin desarrollo, los tres NOT_CONFIGURED y ninguna condicion",
            (["NOT_CONFIGURED"] * 3, "READY"),
            ([doc["runtimeComponents"][c]["state"] for c, _, _, _ in B.COMPONENTES],
             doc["bootstrap"]["status"]))


def test_el_contrato_de_la_senal_de_vida(t):
    """La senal que escribe escribir_senal_de_vida: los cinco campos, la huella de settings.json
    y ninguno mas. Algo fuera del contrato no se escribe."""
    proy = _proyecto()
    B.escribir_senal_de_vida(str(proy), SESION, B.BLOCK4_OK, VERSION_BARRA)
    senal = json.loads((proy / ".claude" / "runtime" / "contextbar.json").read_text(encoding="utf-8"))
    t.igual("contrato: los cinco campos", sorted(B.CONTRATO_SENAL["required"]), sorted(senal))
    t.igual("contrato: la huella es la del bloque registrado",
            B.huella_statusline({"type": "command", "command": _comando(proy)}),
            senal["configurationFingerprint"])
    t.vacio("contrato: no deja temporales",
            [n for n in os.listdir(str(proy / ".claude" / "runtime")) if n.endswith(".tmp")])
    try:
        B.escribir_senal_de_vida(str(proy), SESION, "MAS_O_MENOS", VERSION_BARRA)
        t.verdadero("contrato: un block4 fuera del contrato levanta", False)
    except ValueError:
        t.verdadero("contrato: un block4 fuera del contrato levanta", True)
    a = B.huella_statusline({"type": "command", "command": "x", "padding": 0})
    t.igual("contrato: la huella no depende del orden de las claves", a,
            B.huella_statusline({"padding": 0, "command": "x", "type": "command"}))
    t.igual("contrato: y es sha256 de 64", 64, len(a or ""))


# ══ La segunda mitad: el renderizador, `harness` y los textos ═══════════════════════════════
#
# El renderizador corre como lo corre Claude Code: el statusline.py de un arbol instalado, un
# proceso por dibujo, con el JSON por stdin y sin CLAUDE_PROJECT_DIR. El arbol lo arma
# tests/medir_barra.py con lo mismo que copia install.ps1, compilado como lo deja install.ps1.
# Cada test usa su propia sesion: el libro de cada una es una carpeta aparte.

import atexit
import io

MEDIDOR = _cargar("medir_barra_53", RAIZ / "tests" / "medir_barra.py")
SL = _cargar("statusline_53", RAIZ / "harnesses" / "desarrollo" / "bin" / "contabilidad" / "statusline.py")
CLI = RAIZ / "harnesses" / "desarrollo" / "bin" / "dev-harness.py"
SIN_DATOS = "HARNESS | sin datos del Bloque 4"
TOKEN = "glp" + "at-" + "Q7w8E9r0T1y2U3i4O5p6A7s8"
POLITICA = {
    "policyId": "gcba", "currency": "USD", "billingMode": "SUBSCRIPTION",
    "task": {"softLimit": 5.0, "hardLimit": 20.0},
    "premiumModel": {"requiresHumanApproval": True, "projectedOverrunRequiresApproval": True},
    "statusBar": {"warningAt": 0.5, "errorAt": 0.9, "contextWarningAt": 0.7,
                  "contextErrorAt": 0.9},
}
_INSTALADO = []


def _instalado():
    """(proyecto, renderizador) del arbol instalado. Uno por corrida de la suite."""
    if not _INSTALADO:
        base = Path(tempfile.mkdtemp(prefix="cb53-"))
        atexit.register(shutil.rmtree, str(base), True)
        proy = base / "proyecto con espacios"
        renderizador = Path(MEDIDOR.armar(str(proy)))
        _json(proy / ".claude" / "settings.json", {"statusLine": {
            "type": "command", "command": "python '%s'" % renderizador.as_posix()}})
        _INSTALADO.append((proy, renderizador, base))
    return _INSTALADO[0][:2]


def _nueva_sesion():
    return "s-cb53-" + uuid.uuid4().hex[:10]


def _transcripcion(ruta, sesion, turnos=2, modelo="m-cb53", costo=None, extra=()):
    """Una transcripcion con la forma real: el pedido, la llamada con su uso, el resultado de la
    herramienta y el texto del mismo mensaje. `costo`: el USD de una linea cost-state."""
    lineas = []
    for n in range(1, turnos + 1):
        uso = {"input_tokens": 10 * n, "output_tokens": 100 * n,
               "cache_read_input_tokens": 5000 * n, "cache_creation_input_tokens": 200}
        base = {"sessionId": sesion, "timestamp": "2026-09-24T10:00:%02d" % n}
        lineas += [
            dict(base, type="user", message={"role": "user", "content": "pedido %d" % n}),
            dict(base, type="assistant", message={"id": "msg_%d" % n, "model": modelo,
                                                  "usage": uso, "content": [
                                                      {"type": "text", "text": "hecho %d" % n}]}),
            dict(base, type="user", message={"role": "user", "content": [
                {"type": "tool_result", "content": "salida %d" % n}]}),
        ]
    if costo is not None:
        lineas.append({"type": "cost-state", "sessionId": sesion, "totalDuration": 61000,
                       "totalAPIDuration": 30000, "totalToolDuration": 9000,
                       "hasUnknownModelCost": False, "startTime": 1,
                       "modelUsage": {modelo: {"inputTokens": 30, "outputTokens": 300,
                                               "cacheReadInputTokens": 15000,
                                               "cacheCreationInputTokens": 400,
                                               "costUSD": costo}}})
    lineas += list(extra)
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(ruta), "w", encoding="utf-8", newline="\n") as f:
        for l in lineas:
            f.write(json.dumps(l) + "\n")
    return str(ruta)


def _dibujar(entrada, renderizador=None, comando=None):
    """(codigo, stdout, stderr) del renderizador instalado. `entrada`: dict, bytes o None
    (sin stdin)."""
    if renderizador is None:
        renderizador = _instalado()[1]
    crudo = entrada if isinstance(entrada, bytes) or entrada is None \
        else json.dumps(entrada).encode("utf-8")
    entorno = dict(os.environ)
    entorno.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run(comando or [sys.executable, str(renderizador)],
                       input=crudo if crudo is not None else b"",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       cwd=tempfile.gettempdir(), env=entorno, timeout=60)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def _libro(proy, sesion):
    return proy / ".claude" / "runtime" / "accounting" / sesion / "ledger.jsonl"


def _senal_de(proy):
    ruta = proy / ".claude" / "runtime" / "contextbar.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def _b4():
    """Los modulos del Bloque 4 del repositorio: con ellos se calcula lo que la barra tiene
    que dibujar, sin pasar por la barra."""
    return SL._bloque4()


def _foto(raiz):
    """Cada archivo bajo `raiz`, con su tamano y su fecha de modificacion."""
    foto = {}
    for d, _, archivos in os.walk(str(raiz)):
        for n in archivos:
            ruta = os.path.join(d, n)
            st = os.stat(ruta)
            foto[os.path.relpath(ruta, str(raiz)).replace(os.sep, "/")] = (st.st_size, st.st_mtime_ns)
    return foto


# -- E-10 — la barra escribe su libro y su senal, y nada mas ------------------------------------

def test_e10_la_barra_escribe_solo_el_libro_y_la_senal(t):
    """E-10 — antes y despues de dibujar, cada archivo del proyecto: lo unico nuevo o cambiado
    es el libro de la sesion y contextbar.json. Ni bytecode. Y la senal no tiene ningun numero."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    fuente = _transcripcion(Path(tempfile.mkdtemp(prefix="cb53-t-")) / "t.jsonl", sesion, costo=0.5)
    _json(proy / ".claude" / "harness.presupuesto.json", POLITICA)
    try:
        antes = _foto(proy)
        codigo, salida, _ = _dibujar({"session_id": sesion, "transcript_path": fuente})
        despues = _foto(proy)
    finally:
        os.remove(str(proy / ".claude" / "harness.presupuesto.json"))
    t.igual("E-10 sale 0", 0, codigo)
    t.verdadero("E-10 y dibujo lo del Bloque 4", salida.startswith("HARNESS | m-cb53"))
    tocados = sorted(k for k in despues if antes.get(k) != despues[k])
    t.igual("E-10 lo unico que escribio: el libro de la sesion y la senal de vida",
            [".claude/runtime/accounting/%s/ledger.jsonl" % sesion, ".claude/runtime/contextbar.json"],
            tocados)
    t.igual("E-10 y no borro nada", [], sorted(k for k in antes if k not in despues))
    senal = _senal_de(proy)
    t.igual("E-10 la senal tiene los cinco campos del contrato",
            sorted(B.CONTRATO_SENAL["required"]), sorted(senal or {}))
    t.igual("E-10 y ningun numero", [], [k for k, v in (senal or {}).items()
                                         if isinstance(v, (int, float)) and not isinstance(v, bool)])
    t.vacio("E-10 la senal cumple el contrato", [] if B.cumple(senal, B.CONTRATO_SENAL) else ["no"])
    # La segunda vez, sin nada nuevo en la transcripcion: el libro no se toca.
    antes = _foto(proy)
    _dibujar({"session_id": sesion, "transcript_path": fuente})
    despues = _foto(proy)
    t.igual("E-10 dibujar otra vez solo reescribe la senal", [".claude/runtime/contextbar.json"],
            sorted(k for k in despues if antes.get(k) != despues[k]))


# -- E-16 — sin un cliente de modelo ------------------------------------------------------------

_ENVOLTORIO_SIN_MODELO = r'''
import atexit, builtins, importlib, json, runpy, sys, types
SCRIPT, MARCA = sys.argv[1], sys.argv[2]
usos, pedidos = [], []
CLIENTES = ("anthropic", "openai", "claude_agent_sdk", "claude_code_sdk", "google.generativeai",
            "google.genai", "litellm", "langchain", "cohere", "mistralai", "groq", "ollama")

class _Prohibido(types.ModuleType):
    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        usos.append("%s.%s" % (self.__name__, nombre))
        raise OSError("prohibido (%s.%s)" % (self.__name__, nombre))

for n in CLIENTES + ("socket", "_socket", "ssl", "_ssl", "urllib.request", "http.client",
                     "urllib3", "requests", "httpx"):
    sys.modules[n] = _Prohibido(n)

# Cada import que se pide, aunque el modulo ya este en sys.modules: un `import anthropic` que
# nadie usa tambien es un cliente de modelo importado.
_importar = builtins.__import__
def _anotado(nombre, *a, **k):
    pedidos.append(nombre)
    return _importar(nombre, *a, **k)
builtins.__import__ = _anotado
_por_nombre = importlib.import_module
def _anotado_por_nombre(nombre, *a, **k):
    pedidos.append(nombre)
    return _por_nombre(nombre, *a, **k)
importlib.import_module = _anotado_por_nombre

def _volcar():
    with open(MARCA, "w", encoding="utf-8") as f:
        json.dump({"usos": usos,
                   "clientes": sorted(set(p for p in pedidos
                                          if any(p == c or p.startswith(c + ".") for c in CLIENTES))),
                   "pedidos": len(pedidos)}, f)
atexit.register(_volcar)
sys.argv = [SCRIPT]
runpy.run_path(SCRIPT, run_name="__main__")
'''

_CLIENTES_DE_MODELO = ("anthropic", "openai", "claude_agent_sdk", "claude_code_sdk", "litellm",
                       "langchain", "google.generativeai", "google.genai", "mistralai", "cohere")


def _sin_modelo(correr, script):
    """Corre `script` con el envoltorio y devuelve (codigo, salida, marca)."""
    tmp = Path(tempfile.mkdtemp(prefix="cb53-m-"))
    (tmp / "envoltorio.py").write_text(_ENVOLTORIO_SIN_MODELO, encoding="utf-8")
    codigo, salida = correr([sys.executable, str(tmp / "envoltorio.py"), str(script),
                             str(tmp / "marca.json")])
    datos = json.loads((tmp / "marca.json").read_text(encoding="utf-8")) \
        if (tmp / "marca.json").is_file() else {}
    shutil.rmtree(str(tmp), ignore_errors=True)
    return codigo, salida, datos


def _importa_un_cliente(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    return [c for c in _CLIENTES_DE_MODELO
            if re.search(r"^\s*(import|from)\s+%s\b" % re.escape(c), texto, re.M)
            or re.search(r"import_module\(\s*['\"]%s" % re.escape(c), texto)]


def test_e16_ni_la_barra_ni_session_start_importan_un_cliente_de_modelo(t):
    """E-16 — con los clientes de modelo y la red reemplazados por modulos que fallan, y cada
    import anotado: la barra dibuja lo del Bloque 4 y session-start.py da su mensaje, y ninguno
    de los dos pidio un cliente de modelo. Y su codigo no importa ninguno."""
    proy, renderizador = _instalado()
    sesion = _nueva_sesion()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-16-"))
    fuente = _transcripcion(tmp / "t.jsonl", sesion)

    def barra(comando):
        codigo, salida, _ = _dibujar({"session_id": sesion, "transcript_path": fuente},
                                     comando=comando)
        return codigo, salida

    def hook(comando):
        codigo, mensaje, _ = _sesion(_registrado_y_visto(), comando=comando)
        return codigo, mensaje or ""

    for rotulo, correr, script, dijo in (("la barra", barra, renderizador, "HARNESS | m-cb53"),
                                         ("session-start.py", hook, HOOK, "GCBA")):
        codigo, salida, datos = _sin_modelo(correr, script)
        t.igual("E-16 %s: sale 0" % rotulo, 0, codigo)
        t.contiene("E-16 %s: y hizo su trabajo" % rotulo, dijo, salida)
        t.verdadero("E-16 %s: el envoltorio anoto los imports" % rotulo, datos.get("pedidos", 0) > 0)
        t.igual("E-16 %s: no pidio ningun cliente de modelo" % rotulo, [], datos.get("clientes"))
        t.igual("E-16 %s: ni uso uno, ni la red" % rotulo, [], datos.get("usos"))
    shutil.rmtree(str(tmp), ignore_errors=True)

    lib = RAIZ / "comun" / "hooks" / "lib"
    for ruta in [renderizador, HOOK] + sorted(lib.glob("*.py")):
        t.igual("E-16 %s no importa un cliente de modelo" % ruta.name, [], _importa_un_cliente(ruta))


# -- E-21 / E-22 / E-23 — lo que dibuja sale del Bloque 4, y lo que no tiene no aparece ----------

def _segmentos(linea):
    return linea.strip().split(" | ")


def test_e21_lo_que_el_bloque_4_no_tiene_no_aparece(t):
    """E-21 — sin politica, sin limite de ventana y sin costo: ni USD, ni Budget, ni un
    porcentaje, ni un 0, ni un `?`. Con politica y sin precio -COST_UNRESOLVED-: no sale USD 0."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-21-"))
    codigo, salida, _ = _dibujar({"session_id": sesion,
                                  "transcript_path": _transcripcion(tmp / "t.jsonl", sesion)})
    segmentos = _segmentos(salida)
    t.igual("E-21 sale 0", 0, codigo)
    t.igual("E-21 la linea tiene lo que hay: modelo, ventana en tokens y tokens",
            ["HARNESS", "m-cb53", "Ctx 10k", "Tok 15k in / 300 out"], segmentos)
    for ausente in ("USD", "Budget", "%", "?", "sin resolver", "Tarea", "Agente"):
        t.no_contiene("E-21 sin %s" % ausente, ausente, salida)
    t.vacio("E-21 ningun campo es un 0",
            [s for s in segmentos if re.search(r"(^|\s)0+(\.0+)?(\s|$|%)", s)])

    # Con politica y sin tabla de precios ni cost-state: el costo es COST_UNRESOLVED.
    _json(proy / ".claude" / "harness.presupuesto.json", POLITICA)
    try:
        sesion = _nueva_sesion()
        fuente = _transcripcion(tmp / "u.jsonl", sesion)
        codigo, salida, _ = _dibujar({"session_id": sesion, "transcript_path": fuente})
        b4 = _b4()
        estado = b4["barra"].de(b4["libro"].leer(str(_libro(proy, sesion))), sesion, POLITICA)
    finally:
        os.remove(str(proy / ".claude" / "harness.presupuesto.json"))
    t.verdadero("E-21 el Bloque 4 dice COST_UNRESOLVED", "COST_UNRESOLVED" in estado["unresolved"])
    t.igual("E-21 y no tiene monto", None, estado["budget"]["amount"])
    t.no_contiene("E-21 COST_UNRESOLVED no sale como USD 0", "USD 0", salida)
    t.no_contiene("E-21 ni como USD", "USD", salida)
    t.no_contiene("E-21 ni como 0.00", "0.00", salida)

    # Un total que es un piso tampoco: algo resuelto y algo sin resolver adentro.
    parcial = dict(estado, budget=dict(estado["budget"], amount=1.25, field="apiEquivalentEstimated"))
    t.no_contiene("E-21 un monto con COST_UNRESOLVED adentro no se muestra", "USD",
                  SL.dibujar(parcial, b4))
    t.contiene("E-21 y sin COST_UNRESOLVED si", "USD 1.25 eq",
               SL.dibujar(dict(parcial, unresolved=[]), b4))
    shutil.rmtree(str(tmp), ignore_errors=True)


def test_e22_tokens_y_costo_son_los_del_bloque_4_y_no_los_de_stdin(t):
    """E-22 — lo que dibuja es barra.de sobre el libro; el costo, el contexto y el modelo que
    llegan por stdin no cambian nada."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-22-"))
    fuente = _transcripcion(tmp / "t.jsonl", sesion, costo=0.75)
    base = {"session_id": sesion, "transcript_path": fuente}
    _json(proy / ".claude" / "harness.presupuesto.json", POLITICA)
    try:
        _, primera, _ = _dibujar(base)
        b4 = _b4()
        estado = b4["barra"].de(b4["libro"].leer(str(_libro(proy, sesion))), sesion, POLITICA)
        otras = []
        for engano in ({"cost": {"total_cost_usd": 999.99, "total_duration_ms": 1}},
                       {"cost": {"total_cost_usd": 0}, "context_window": {"used_percentage": 99,
                                                                           "total_input_tokens": 7}},
                       {"model": {"id": "otro-modelo", "display_name": "Otro"},
                        "exceeds_200k_tokens": True}):
            otras.append(_dibujar(dict(base, **engano))[1])
    finally:
        os.remove(str(proy / ".claude" / "harness.presupuesto.json"))
    tokens = estado["tokens"]
    entrada = tokens["inputTokens"] + tokens["cacheReadTokens"] + tokens["cacheCreationTokens"]
    t.contiene("E-22 los tokens son los de barra.de",
               "Tok %s in / %s out" % (SL._cantidad(entrada), SL._cantidad(tokens["outputTokens"])),
               primera)
    t.contiene("E-22 el costo es el de barra.de", "USD %.2f eq" % estado["budget"]["amount"], primera)
    t.igual("E-22 y es el del cost-state, que es lo que reporto el proveedor", 0.75,
            estado["budget"]["amount"])
    t.contiene("E-22 el tiempo tambien", b4["tiempo"].como_texto(estado["time"]["wallMs"]), primera)
    for n, otra in enumerate(otras):
        t.igual("E-22 cambiar stdin (%d) no cambia lo que dibuja" % n, primera, otra)
    for dato in ("999", "otro-modelo", "Otro", "99%"):
        t.no_contiene("E-22 nada de stdin en la linea: %s" % dato, dato, "".join(otras))
    shutil.rmtree(str(tmp), ignore_errors=True)


def test_e23_agente_tarea_y_presupuesto_salen_del_bloque_4(t):
    """E-23 — sin tarea declarada la tarea no aparece; el presupuesto es el de barra.de; y el
    agente y una tarea declarada salen del libro, no de otro lado."""
    proy, _ = _instalado()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-23-"))
    politica = dict(POLITICA, task={"softLimit": 1.0, "hardLimit": 2.0})
    _json(proy / ".claude" / "harness.presupuesto.json", politica)
    try:
        sesion = _nueva_sesion()
        fuente = _transcripcion(tmp / "t.jsonl", sesion, costo=1.5)
        _, sin_declarar, _ = _dibujar({"session_id": sesion, "transcript_path": fuente})
        b4 = _b4()
        estado = b4["barra"].de(b4["libro"].leer(str(_libro(proy, sesion))), sesion, politica)

        # Una tarea y un agente que el Bloque 4 tiene en el libro de la sesion.
        otra = _nueva_sesion()
        c_eventos = sys.modules["contabilidad.eventos"]
        evento = c_eventos.nuevo("MODEL_CALL_COMPLETED", "GCBA-7", "manual", sessionId=otra,
                                 agentId="dev-backend", dedupKey="k-cb53-23",
                                 timestamp="2026-09-24T09:00:00",
                                 usage={"state": "RESOLVED", "provider": "p", "model": "m-cb53",
                                        "inputTokens": 1, "outputTokens": 2, "cacheReadTokens": 0,
                                        "cacheCreationTokens": 0, "contextTokens": None,
                                        "contextLimit": None})
        b4["libro"].agregar(str(_libro(proy, otra)), evento)
        _, declarada, _ = _dibujar({"session_id": otra,
                                    "transcript_path": _transcripcion(tmp / "u.jsonl", otra)})
    finally:
        os.remove(str(proy / ".claude" / "harness.presupuesto.json"))
    t.igual("E-23 la sesion es la tarea mientras nadie declare una", sesion, estado["taskId"])
    t.no_contiene("E-23 y la tarea no aparece", "Tarea", sin_declarar)
    t.no_contiene("E-23 sin agente en el libro, tampoco el agente", "Agente", sin_declarar)
    t.contiene("E-23 el presupuesto es el de barra.de",
               "Budget %d%%" % int(round(estado["budget"]["fraction"] * 100)), sin_declarar)
    t.contiene("E-23 con su nivel, que sale de la politica", estado["budget"]["level"], sin_declarar)
    t.contiene("E-23 la tarea declarada en el libro aparece", "Tarea GCBA-7", declarada)
    t.contiene("E-23 y el agente", "Agente dev-backend", declarada)
    shutil.rmtree(str(tmp), ignore_errors=True)


# -- E-37 / E-38 / E-39 — nunca en blanco, sin duplicar y sin texto de la transcripcion ----------

def test_e37_sin_datos_la_barra_sale_0_y_lo_dice(t):
    """E-37 — sin stdin, con stdin roto, sin libro, con la transcripcion rota o con el Bloque 4
    roto: sale 0 y dibuja `HARNESS | sin datos del Bloque 4`, nunca una linea vacia."""
    proy, renderizador = _instalado()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-37-"))
    invalida = tmp / "invalida.jsonl"
    invalida.write_bytes(b'{"type":"assistant","message":{"id":"m\xff\xfe"}}\n')
    basura = tmp / "basura.jsonl"
    basura.write_text("esto no es json\n{ tampoco\n", encoding="utf-8")
    sesion_libro_roto = _nueva_sesion()
    _libro(proy, sesion_libro_roto).mkdir(parents=True)          # el libro es una carpeta
    casos = (
        ("sin stdin", None, None),
        ("stdin que no es JSON", b"{ esto no", None),
        ("stdin sin session_id", {"transcript_path": str(basura)}, None),
        ("session_id que sale del libro", {"session_id": "../../afuera",
                                           "transcript_path": str(basura)}, None),
        ("sin transcripcion ni libro", {"session_id": _nueva_sesion()}, "OK"),
        ("transcripcion que no existe", {"session_id": _nueva_sesion(),
                                         "transcript_path": str(tmp / "no-existe.jsonl")}, "OK"),
        ("transcripcion que no es json", {"session_id": _nueva_sesion(),
                                          "transcript_path": str(basura)}, "OK"),
        ("transcripcion con bytes que no son UTF-8", {"session_id": _nueva_sesion(),
                                                      "transcript_path": str(invalida)},
         "SOURCE_UNAVAILABLE"),
        ("transcripcion que es una carpeta", {"session_id": _nueva_sesion(),
                                              "transcript_path": str(tmp)}, "OK"),
        ("libro que no se puede escribir", {"session_id": sesion_libro_roto,
                                            "transcript_path": _transcripcion(
                                                tmp / "buena.jsonl", sesion_libro_roto)},
         "SOURCE_UNAVAILABLE"),
    )
    for rotulo, entrada, block4 in casos:
        previa = (proy / ".claude" / "runtime" / "contextbar.json").read_bytes() \
            if (proy / ".claude" / "runtime" / "contextbar.json").is_file() else None
        codigo, salida, _ = _dibujar(entrada)
        t.igual("E-37 %s: sale 0" % rotulo, 0, codigo)
        t.igual("E-37 %s: dice que no hay datos, en una linea" % rotulo, SIN_DATOS + "\n",
                salida.replace("\r\n", "\n"))
        senal = _senal_de(proy)
        if block4 is None:
            ahora_ = (proy / ".claude" / "runtime" / "contextbar.json").read_bytes() \
                if (proy / ".claude" / "runtime" / "contextbar.json").is_file() else None
            t.verdadero("E-37 %s: sin sesion no deja senal" % rotulo, ahora_ == previa)
        else:
            t.igual("E-37 %s: la senal dice %s" % (rotulo, block4), (entrada["session_id"], block4),
                    ((senal or {}).get("sessionId"), (senal or {}).get("block4")))
    t.verdadero("E-37 y nada salio del libro", not (proy / ".claude" / "afuera").exists()
                and not (proy / "afuera").exists())

    # El Bloque 4 que no se puede cargar: un modulo roto en el arbol instalado.
    # El bytecode, si hubiera, se aparta: uno viejo del mismo tamano taparia la rotura.
    roto = renderizador.parent / "barra.py"
    original = roto.read_bytes()
    cache = renderizador.parent / "__pycache__"
    respaldo = Path(tempfile.mkdtemp(prefix="cb53-pyc-")) / "pyc"
    if cache.is_dir():
        shutil.move(str(cache), str(respaldo))
    try:
        roto.write_bytes(b"def de(:\n")
        sesion = _nueva_sesion()
        codigo, salida, _ = _dibujar({"session_id": sesion,
                                      "transcript_path": _transcripcion(tmp / "t.jsonl", sesion)})
    finally:
        roto.write_bytes(original)
        shutil.rmtree(str(cache), ignore_errors=True)
        if respaldo.is_dir():
            shutil.move(str(respaldo), str(cache))
    t.igual("E-37 Bloque 4 roto: sale 0", 0, codigo)
    t.igual("E-37 Bloque 4 roto: dice que no hay datos", SIN_DATOS, salida.strip())
    t.igual("E-37 Bloque 4 roto: y la senal dice SOURCE_UNAVAILABLE", "SOURCE_UNAVAILABLE",
            (_senal_de(proy) or {}).get("block4"))
    shutil.rmtree(str(tmp), ignore_errors=True)


def test_e38_ingerir_dos_veces_deja_el_libro_igual(t):
    """E-38 — la misma transcripcion dos veces, y copiada a otra ruta: el libro igual byte a
    byte. Un mensaje nuevo suma exactamente un evento. Y una transcripcion sin consumo no deja
    un evento sin resolver por dibujo."""
    proy, _ = _instalado()
    sesion = _nueva_sesion()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-38-"))
    fuente = _transcripcion(tmp / "t.jsonl", sesion, turnos=3, costo=0.4)
    entrada = {"session_id": sesion, "transcript_path": fuente}
    _dibujar(entrada)
    uno = _libro(proy, sesion).read_bytes()
    _dibujar(entrada)
    dos = _libro(proy, sesion).read_bytes()
    copia = tmp / "otra ruta" / "copia.jsonl"
    copia.parent.mkdir()
    shutil.copy(fuente, str(copia))
    _dibujar(dict(entrada, transcript_path=str(copia)))
    tres = _libro(proy, sesion).read_bytes()
    t.verdadero("E-38 el libro tiene eventos", uno.count(b"\n") >= 4)
    t.verdadero("E-38 dibujar dos veces deja el libro igual, byte a byte", uno == dos)
    t.verdadero("E-38 la misma transcripcion en otra ruta, tambien", uno == tres)
    ids = [json.loads(l)["eventId"] for l in uno.decode("utf-8").splitlines()]
    t.igual("E-38 ningun eventId repetido", len(ids), len(set(ids)))

    with io.open(fuente, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"type": "assistant", "sessionId": sesion, "timestamp": "2026-09-24T11:00:00",
                            "message": {"id": "msg_nuevo", "model": "m-cb53", "usage": {
                                "input_tokens": 1, "output_tokens": 1}}}) + "\n")
    _dibujar(entrada)
    cuatro = _libro(proy, sesion).read_bytes()
    t.igual("E-38 un mensaje nuevo suma un evento", uno.count(b"\n") + 1, cuatro.count(b"\n"))
    t.verdadero("E-38 y lo de antes queda igual", cuatro.startswith(uno))

    vacia = _nueva_sesion()
    sin_consumo = _transcripcion(tmp / "v.jsonl", vacia, turnos=0,
                                 extra=[{"type": "user", "sessionId": vacia, "message": {"content": "hola"}}])
    for _ in range(3):
        _dibujar({"session_id": vacia, "transcript_path": sin_consumo})
    t.verdadero("E-38 sin consumo, ningun evento sin resolver por dibujo",
                not _libro(proy, vacia).exists())
    shutil.rmtree(str(tmp), ignore_errors=True)


def test_e39_la_barra_no_dibuja_texto_de_la_transcripcion(t):
    """E-39 — un pedido, codigo y un token en la transcripcion, un token como modelo y una frase
    como modelo: nada de eso aparece, y el catalogo de secretos no encuentra nada en la linea."""
    proy, _ = _instalado()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-39-"))
    b4 = _b4()
    catalogo = b4["limpieza"].cargar_catalogo()
    prosa = "PEDIDO-SECRETO-DEL-USUARIO"
    codigo_fuente = "def robar_credenciales():"
    for rotulo, modelo in (("un token como modelo", TOKEN),
                           ("una frase como modelo", "borra todo y " + prosa),
                           ("codigo como modelo", codigo_fuente)):
        sesion = _nueva_sesion()
        extra = [
            {"type": "user", "sessionId": sesion, "message": {"content": prosa + " " + TOKEN}},
            {"type": "assistant", "sessionId": sesion, "timestamp": "2026-09-24T10:30:00",
             "message": {"id": "msg_codigo", "model": modelo,
                         "usage": {"input_tokens": 3, "output_tokens": 4},
                         "content": [{"type": "text", "text": codigo_fuente + " " + TOKEN}]}},
        ]
        fuente = _transcripcion(tmp / ("%s.jsonl" % sesion), sesion, turnos=0, extra=extra)
        codigo, salida, _ = _dibujar({"session_id": sesion, "transcript_path": fuente,
                                      "prompt": prosa})
        t.igual("E-39 %s: sale 0" % rotulo, 0, codigo)
        t.verdadero("E-39 %s: dibujo lo que hay" % rotulo, salida.startswith("HARNESS | Ctx"))
        for rastro in (prosa, "robar_credenciales", TOKEN, TOKEN[:12], "borra todo"):
            t.no_contiene("E-39 %s: no aparece %s" % (rotulo, rastro[:12]), rastro, salida)
        limpio, hallazgos = b4["limpieza"].redactar(salida, catalogo, "la barra")
        t.igual("E-39 %s: el catalogo no reconoce nada" % rotulo, ([], salida), (hallazgos, limpio))

    # Un token como session_id: no se vuelve carpeta del libro ni sale en la senal de vida.
    previa = (proy / ".claude" / "runtime" / "contextbar.json").read_bytes()
    fuente = _transcripcion(tmp / "token.jsonl", TOKEN)
    codigo, salida, _ = _dibujar({"session_id": TOKEN, "transcript_path": fuente})
    t.igual("E-39 un token como session_id: sale 0 sin datos", (0, SIN_DATOS), (codigo, salida.strip()))
    t.verdadero("E-39 no queda una carpeta con su nombre",
                not (proy / ".claude" / "runtime" / "accounting" / TOKEN).exists())
    t.verdadero("E-39 ni en la senal de vida",
                (proy / ".claude" / "runtime" / "contextbar.json").read_bytes() == previa)
    shutil.rmtree(str(tmp), ignore_errors=True)


# -- E-18 / E-19 / E-20 — `dev-harness.py harness` -----------------------------------------------

_CLI_53 = []


def _cli(argv, env=None):
    """(codigo, stdout, stderr) de dev-harness.py en proceso, sin terminal."""
    if not _CLI_53:
        _CLI_53.append(_cargar("dev_harness_53", CLI))
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr, sys.stdin)
    entorno_previo = {k: os.environ.get(k) for k in (env or {})}
    sys.stdout, sys.stderr, sys.stdin = salida, error, io.StringIO("")
    os.environ.update(env or {})
    try:
        codigo = _CLI_53[0].main(argv)
    finally:
        sys.stdout, sys.stderr, sys.stdin = previos
        for k, v in entorno_previo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return codigo, salida.getvalue(), error.getvalue()


def _seccion(texto):
    return texto.split("Runtime / Observabilidad", 1)[-1] if "Runtime / Observabilidad" in texto else ""


def test_e18_harness_muestra_los_tres_el_reinicio_y_la_ultima_sesion(t):
    """E-18 — recien instalada: los tres, reinicio pendiente y ninguna sesion vista. Despues de
    dibujarse: ACTIVA de la ultima sesion, sin reinicio, y cual fue."""
    proy = _proyecto()
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-24T10:00:00")
    codigo, salida, _ = _cli(["harness", "--proyecto", str(proy)])
    seccion = _seccion(salida)
    t.igual("E-18 sale 0", 0, codigo)
    t.igual("E-18 la seccion esta una vez", 1, salida.count("Runtime / Observabilidad"))
    t.igual("E-18 y la bienvenida no repite el bloque Observabilidad", 0,
            len([l for l in salida.split("\n") if l.strip() == "Observabilidad"]))
    for nombre, esperado in (("Block 4 Accounting", "✓ ACTIVO"), ("Context Bar", "REQUIERE REINICIO"),
                             ("Security Reporting", "✓ ACTIVO")):
        t.verdadero("E-18 %s: %s" % (nombre, esperado), _fila(seccion, nombre).endswith(esperado))
    t.verdadero("E-18 el reinicio pendiente", _fila(seccion, "Reinicio de Claude Code").endswith("hace falta")
                and "no hace falta" not in _fila(seccion, "Reinicio de Claude Code"))
    t.contiene("E-18 ninguna sesion vista todavia", "ninguna sesión cargó la Context Bar todavía",
               _fila(seccion, "Última sesión vista"))
    t.contiene("E-18 y la accion", B.REINICIAR, seccion.split("Acción requerida", 1)[-1])

    _senal(proy, sesion=OTRA, momento="2026-09-24T10:00:05")
    _, salida, _ = _cli(["harness", "--proyecto", str(proy)])
    seccion = _seccion(salida)
    t.verdadero("E-18 despues de dibujarse: ACTIVA de la ultima sesion",
                _fila(seccion, "Context Bar").endswith("✓ ACTIVA (última sesión: %s)" % OTRA[:8]))
    t.verdadero("E-18 sin reinicio", _fila(seccion, "Reinicio de Claude Code").endswith("no hace falta"))
    t.contiene("E-18 la ultima sesion vista cargo la barra",
               "%s cargó la Context Bar (último dibujo: 2026-09-24T10:00:05)" % OTRA[:8],
               _fila(seccion, "Última sesión vista"))
    t.no_contiene("E-18 y ya no hay accion", "Acción requerida", seccion)


def test_e19_harness_json_usa_los_estados_en_ingles(t):
    """E-19 — `--json`: los estados de los tres componentes con sus ids, nunca la etiqueta."""
    for rotulo, proy, esperado in (
            ("recien instalada", _proyecto(), "RELOAD_REQUIRED"),
            ("dibujada", _registrado_y_visto(), "ACTIVE"),
            ("con error", _proyecto(senal={"block4": B.BLOCK4_SOURCE_UNAVAILABLE}), "ERROR")):
        if rotulo == "recien instalada":
            B.registrar_instalacion(str(proy), barra_probada=True)
        codigo, salida, _ = _cli(["harness", "--json", "--proyecto", str(proy)])
        t.igual("E-19 %s: sale 0" % rotulo, 0, codigo)
        doc = json.loads(salida)
        rc = doc["runtimeComponents"]
        t.igual("E-19 %s: la barra en ingles" % rotulo, esperado, rc["contextBar"]["state"])
        for clave, _, _, _ in B.COMPONENTES:
            t.verdadero("E-19 %s: %s es un id" % (rotulo, clave),
                        rc[clave]["state"] in B.ESTADOS_DE_COMPONENTE)
        for etiqueta in ("ACTIVA", "ACTIVO", "REQUIERE REINICIO", "CONFIGURADA", "SIN CONFIGURAR"):
            t.no_contiene("E-19 %s: sin la etiqueta %s" % (rotulo, etiqueta), '"%s"' % etiqueta, salida)
        t.vacio("E-19 %s: valida contra el schema 1.1" % rotulo, _validar(doc))
        t.verdadero("E-19 %s: dice si hace falta reiniciar" % rotulo,
                    isinstance(rc["contextBar"]["reloadRequired"], bool))


def test_e20_harness_verbose_no_imprime_secretos(t):
    """E-20 — con un token en el .env, en el entorno, en el comando registrado y como sessionId
    de la senal de vida: --verbose da huellas, versiones y fechas, y el token no sale."""
    proy = _proyecto()
    B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-09-24T10:00:00")
    _escribir(proy / ".env", "JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    env = {"JIRA_TOKEN": TOKEN, "GITLAB_TOKEN": TOKEN}
    _senal(proy, sesion=TOKEN, momento="2026-09-24T10:00:05")
    codigo, salida, error = _cli(["harness", "--verbose", "--proyecto", str(proy)], env=env)
    detalle = salida.split("\nDetalle\n", 1)[-1]
    t.igual("E-20 sale 0", 0, codigo)
    t.no_contiene("E-20 stdout no tiene el token", TOKEN, salida)
    t.no_contiene("E-20 stderr tampoco", TOKEN, error)
    barra = _barra(_estado(proy))
    t.contiene("E-20 da la huella del statusLine", barra["configurationFingerprint"], detalle)
    for clave in ("renderer", "block4Adapter", "sessionStart"):
        t.contiene("E-20 y la huella %s" % clave, barra["fingerprints"][clave], detalle)
    t.contiene("E-20 la version de la barra", "Versión de la barra   %s" % VERSION_BARRA, detalle)
    t.contiene("E-20 la fecha de validacion", "validado: 2026-09-24T10:00:00", detalle)
    t.contiene("E-20 y la del ultimo dibujo", "2026-09-24T10:00:05", detalle)
    t.no_contiene("E-20 el comando registrado no se imprime", "statusline.py'", salida)

    # Un comando registrado con un token adentro -alguien lo edito a mano- tampoco sale.
    _json(proy / ".claude" / "settings.json",
          {"statusLine": {"type": "command", "command": _comando(proy) + " '--token=%s'" % TOKEN}})
    codigo, salida, error = _cli(["harness", "--verbose", "--proyecto", str(proy)], env=env)
    t.igual("E-20 con el token en el comando: sale 0", 0, codigo)
    t.no_contiene("E-20 con el token en el comando: no sale", TOKEN, salida + error)
    _, salida, error = _cli(["harness", "--proyecto", str(proy)], env=env)
    t.no_contiene("E-20 harness sin --verbose tampoco lo imprime", TOKEN, salida + error)


# -- E-24 / E-25 — lo que dicen los textos -------------------------------------------------------

DOC_CONTABILIDAD = RAIZ / "docs" / "contabilidad.md"


def test_e24_la_doc_dice_que_la_barra_es_de_la_terminal(t):
    """E-24 — docs/contabilidad.md: la Context Bar es la statusLine de la terminal de Claude
    Code, y la integracion nativa con VS Code no se provee."""
    texto = DOC_CONTABILIDAD.read_text(encoding="utf-8")
    seccion = texto.split("### La Context Bar, en la terminal de Claude Code", 1)
    t.igual("E-24 tiene la seccion de la Context Bar", 2, len(seccion))
    seccion = seccion[-1].split("\n## ", 1)[0]
    t.contiene("E-24 es la statusLine de Claude Code", "La Context Bar es la `statusLine` de Claude Code",
               seccion)
    t.contiene("E-24 al pie de la terminal", "al pie de la terminal", seccion)
    t.contiene("E-24 y es de la terminal nada mas", "Es de la terminal, y nada más", seccion)
    t.contiene("E-24 VS Code no tiene integracion nativa",
               "La extensión de VS Code no tiene una integración nativa", seccion)
    t.contiene("E-24 y el harness no la provee", "el harness no la provee", seccion)


# Donde vive el texto del harness: lo que se instala, lo que se lee y lo que se publica.
_TEXTOS = ("comun", "harnesses", "docs", "Pendientes", "README.md", "CHANGELOG.md", "UPGRADE.md",
           "install.ps1")
_EXTENSIONES = (".md", ".py", ".ps1", ".psm1", ".json", ".txt", ".html", ".sh", ".plantilla")
# Un parrafo que nombra VS Code tiene que decir que no, que queda afuera o que es una
# posibilidad. Uno que no dice nada de eso es uno que lo afirma.
_VSCODE = re.compile(r"vs ?code|visual studio code", re.IGNORECASE)
_NIEGA = re.compile(r"\b(no|sin|ni|nunca|ning[uú]n[ao]?|ser[ií]a|afuera|fuera de|si)\b", re.IGNORECASE)


def _parrafos_con_vscode():
    salida = []
    for nombre in _TEXTOS:
        raiz = RAIZ / nombre
        archivos = [raiz] if raiz.is_file() else sorted(p for p in raiz.rglob("*") if p.is_file())
        for archivo in archivos:
            if archivo.suffix not in _EXTENSIONES or "__pycache__" in archivo.parts:
                continue
            try:
                texto = archivo.read_text(encoding="utf-8-sig")
            except (UnicodeDecodeError, OSError):
                continue
            for parrafo in re.split(r"\n\s*\n", texto):
                if _VSCODE.search(parrafo):
                    salida.append((archivo.relative_to(RAIZ).as_posix(), parrafo))
    return salida


def test_e25_ningun_texto_afirma_una_integracion_nativa_con_vs_code(t):
    """E-25 — cada parrafo del harness que nombra VS Code lo niega o lo deja afuera. El barrido
    tiene que encontrar algo -si no, no mira nada- y tiene que agarrar una afirmacion."""
    parrafos = _parrafos_con_vscode()
    t.verdadero("E-25 el barrido encuentra los parrafos que nombran VS Code",
                any(a == "docs/contabilidad.md" for a, _ in parrafos))
    for archivo, parrafo in parrafos:
        t.verdadero("E-25 %s: «%s» no afirma VS Code" % (archivo, " ".join(parrafo.split())[:60]),
                    _NIEGA.search(parrafo))
    for afirmacion in ("La Context Bar se ve también en la barra de estado de VS Code.",
                       "Integración nativa con la status bar de VSCode, lista para usar."):
        t.verdadero("E-25 el barrido agarra «%s»" % afirmacion[:30],
                    _VSCODE.search(afirmacion) and not _NIEGA.search(afirmacion))


# -- E-40 — la plata y el tiempo siguen al ultimo estado acumulado ---------------------------------

def _estado_de_costo(sesion, usd, segundos, modelo="m-cb53"):
    return {"type": "cost-state", "sessionId": sesion, "totalDuration": segundos * 1000,
            "totalAPIDuration": segundos * 500, "totalToolDuration": segundos * 250,
            "hasUnknownModelCost": False, "startTime": 1,
            "modelUsage": {modelo: {"inputTokens": 30, "outputTokens": 300,
                                    "cacheReadInputTokens": 15000, "cacheCreationInputTokens": 400,
                                    "costUSD": usd}}}


def _agregar_lineas(ruta, lineas):
    with io.open(str(ruta), "a", encoding="utf-8", newline="\n") as f:
        for l in lineas:
            f.write(json.dumps(l) + "\n")


def test_e40_costo_y_tiempo_siguen_al_ultimo_estado(t):
    """E-40 — un cost-state de 0.50 y 60 s, y despues uno de 2.75 y 600 s: ingerido de a poco
    -la barra en cada mensaje, o `contabilidad --ingerir` dos veces- o de una vez, el libro y la
    barra dan 2.75 y 10 min. Y el libro guarda los dos estados: append-only."""
    proy, _ = _instalado()
    tmp = Path(tempfile.mkdtemp(prefix="cb53-40-"))
    _json(proy / ".claude" / "harness.presupuesto.json", POLITICA)
    try:
        b4 = _b4()
        # De a poco, como la dibuja la barra.
        poco = _nueva_sesion()
        fuente = _transcripcion(tmp / "poco.jsonl", poco, turnos=1,
                                extra=[_estado_de_costo(poco, 0.50, 60)])
        _, primera, _ = _dibujar({"session_id": poco, "transcript_path": fuente})
        _agregar_lineas(fuente, [
            {"type": "assistant", "sessionId": poco, "timestamp": "2026-09-24T10:05:00",
             "message": {"id": "msg_2", "model": "m-cb53",
                         "usage": {"input_tokens": 5, "output_tokens": 50}}},
            _estado_de_costo(poco, 2.75, 600)])
        _, segunda, _ = _dibujar({"session_id": poco, "transcript_path": fuente})
        de_a_poco = b4["barra"].de(b4["libro"].leer(str(_libro(proy, poco))), poco, POLITICA)

        # De una vez, la misma transcripcion en un libro nuevo.
        una = _nueva_sesion()
        entera = tmp / "entera.jsonl"
        entera.write_text(Path(fuente).read_text(encoding="utf-8").replace(poco, una),
                          encoding="utf-8")
        _, de_una_linea, _ = _dibujar({"session_id": una, "transcript_path": str(entera)})
        de_una = b4["barra"].de(b4["libro"].leer(str(_libro(proy, una))), una, POLITICA)

        # Y el Bloque 4 solo, sin la barra: `contabilidad --ingerir` de la mitad y del total.
        mitad = tmp / "mitad.jsonl"
        lineas = Path(fuente).read_text(encoding="utf-8").splitlines(True)
        mitad.write_text("".join(lineas[:4]), encoding="utf-8")
        _cli(["contabilidad", "GCBA-40", "--ingerir", str(mitad), "--proyecto", str(proy)])
        _, crudo, _ = _cli(["contabilidad", "GCBA-40", "--ingerir", fuente, "--json",
                            "--proyecto", str(proy)])
        resumen = json.loads(crudo)
    finally:
        os.remove(str(proy / ".claude" / "harness.presupuesto.json"))
    t.contiene("E-40 con el primer estado: 0.50", "USD 0.50 eq", primera)
    t.contiene("E-40 y 1 min", "1m 00s", primera)
    t.contiene("E-40 de a poco, la barra sigue al ultimo: 2.75", "USD 2.75 eq", segunda)
    t.contiene("E-40 y 10 min", "10m 00s", segunda)
    t.igual("E-40 de a poco, el Bloque 4 da 2.75", 2.75, de_a_poco["budget"]["amount"])
    t.igual("E-40 y 600 s", 600000, de_a_poco["time"]["wallMs"])
    t.igual("E-40 de una vez da lo mismo", (2.75, 600000),
            (de_una["budget"]["amount"], de_una["time"]["wallMs"]))
    t.igual("E-40 y la barra dibuja lo mismo", segunda.split(" | ")[2:],
            de_una_linea.split(" | ")[2:])
    t.igual("E-40 contabilidad --ingerir de la mitad y del total: 2.75", 2.75,
            resumen["cost"]["apiEquivalentEstimated"])
    t.igual("E-40 y 10 min", 600000, resumen["time"]["wallMs"])
    agregados = [json.loads(l) for l in _libro(proy, poco).read_text(encoding="utf-8").splitlines()
                 if (json.loads(l).get("metadata") or {}).get("providerAggregate")]
    t.igual("E-40 el libro guarda los dos estados, de modelo y de tiempo: append-only", 4,
            len(agregados))
    t.igual("E-40 los tokens se deduplican como antes: los dos mensajes, una vez cada uno",
            (10 + 5, 100 + 50),
            (de_a_poco["tokens"]["inputTokens"], de_a_poco["tokens"]["outputTokens"]))
    shutil.rmtree(str(tmp), ignore_errors=True)


# -- E-41 — la huella de la senal es la del comando que corrio ------------------------------------

def test_e41_la_huella_de_la_senal_es_la_del_comando_que_corrio(t):
    """E-41 — despues de un cambio del statusLine, el comando viejo que sigue corriendo no saca
    RELOAD_REQUIRED, y el nuevo si. Una senal del mismo segundo que el registro no prueba nada."""
    import time
    proy = _proyecto()
    MEDIDOR.armar(str(proy))
    renderizador = proy / ".claude" / "harness" / "bin" / "desarrollo" / "contabilidad" / "statusline.py"
    base = "%s '%s'" % (Path(sys.executable).as_posix(), renderizador.as_posix())
    sesion = _nueva_sesion()

    def registrar(comando, momento=None):
        huella = B.huella_statusline({"type": "command", "command": comando})
        _json(proy / ".claude" / "settings.json",
              {"statusLine": {"type": "command", "command": "%s '%s'" % (comando, huella)}})
        B.registrar_instalacion(str(proy), barra_probada=True, momento=momento)
        return huella

    def correr(*argumentos):
        return _dibujar({"session_id": sesion},
                        comando=[sys.executable, str(renderizador)] + list(argumentos))

    vieja = registrar(base)
    t.igual("E-41 la huella no cambia al escribirse como argumento", vieja,
            B.huella_statusline(B.leer_statusline(str(proy))[0]))
    time.sleep(1.1)
    correr(vieja)
    t.igual("E-41 la senal lleva la huella que paso el comando", vieja,
            _senal_de(proy)["configurationFingerprint"])
    t.igual("E-41 con el comando registrado, ACTIVE", "ACTIVE",
            _barra(B.resolver(str(proy), sesion=sesion))["state"])

    nueva = registrar(base + " '--otro'")
    time.sleep(1.1)
    correr(vieja)
    for rotulo, en in (("en la sesion", sesion), ("en la CLI", None)):
        barra = _barra(B.resolver(str(proy), sesion=en))
        t.igual("E-41 el comando viejo despues del cambio (%s): RELOAD_REQUIRED" % rotulo,
                ("RELOAD_REQUIRED", True), (barra["state"], barra["reloadRequired"]))
    correr("--otro", nueva)
    barra = _barra(B.resolver(str(proy), sesion=sesion))
    t.igual("E-41 el comando nuevo lo saca: ACTIVE y sin reinicio", ("ACTIVE", False),
            (barra["state"], barra["reloadRequired"]))
    correr()
    t.igual("E-41 un comando sin huella deja null", None, _senal_de(proy)["configurationFingerprint"])

    tercera = registrar(base + " '--tercero'", momento="2030-01-01T00:00:00")
    B.escribir_senal_de_vida(str(proy), sesion, B.BLOCK4_OK, "1.0.0",
                             momento="2030-01-01T00:00:00", huella=tercera)
    t.igual("E-41 una senal del mismo segundo que el registro no prueba nada", "RELOAD_REQUIRED",
            _barra(B.resolver(str(proy), sesion=sesion))["state"])
    B.escribir_senal_de_vida(str(proy), sesion, B.BLOCK4_OK, "1.0.0",
                             momento="2030-01-01T00:00:01", huella=tercera)
    t.igual("E-41 un segundo despues, si", "ACTIVE",
            _barra(B.resolver(str(proy), sesion=sesion))["state"])
