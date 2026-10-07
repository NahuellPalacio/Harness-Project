# Los escenarios de docs/cambios/harness-unico/spec.md que no instalan: el repositorio, la
# bienvenida, SessionStart, la CLI, los registros y la documentacion. Los que instalan de verdad
# van en tests/casos/63-harness-unico-instalador.ps1. Cada test nombra su E-nn.
#
# La linea de base es ea2dff7 (0.28.0 con Flow Governance integrado) y se saca de git en cada
# corrida, nunca de una copia versionada. Era e5d7a14, 0.28.0 sola: pisado por
# docs/cambios/integracion-flow-governance-0-31/spec.md, porque las Waves cambiaron la bienvenida
# y el schema de la instalacion antes de este cambio, y lo que este cambio promete es no cambiar
# nada para un proyecto con `desarrollo` respecto de la linea de la que parte. Sin esa historia -un clon superficial- los escenarios que comparan contra ella
# fallan en rojo con el motivo: no se saltean.
#
# Este archivo no escribe el nombre del parametro viejo del instalador con su guion: E-61 pide
# que adentro de los 63-* solo aparezca en E-08 y en las instalaciones con el instalador viejo.
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = "ea2dff7"
HOOKS = RAIZ / "comun" / "hooks"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
SCHEMA = RAIZ / "comun" / "schemas" / "harness-installation-state.schema.json"

# El parametro viejo, armado por partes (ver la cabecera).
PARAMETRO_VIEJO = re.compile(r"(?<![\w-])-" + "Harness" + r"\b")

MOMENTO = "2026-10-01T12:00:00"
SESION = "s-hu63"
USUARIO = "Ana"
VERSION_LOCK = "0.28.0"
TODAS = ("ES0901", "ES0902", "ES0903", "GuiaDGISIS", "Obelisco", "PC0901")


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


B = _cargar("bienvenida_hu63", HOOKS / "lib" / "bienvenida.py")
ARMADOR = _cargar("armador_hu63", RAIZ / "comun" / "bin" / "contexto-armar.py")


# -- git y la linea de base ------------------------------------------------------

def _git(*args):
    r = subprocess.run(["git", "-C", str(RAIZ)] + list(args),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout


def _archivos_del_repo():
    """Lo versionado y lo nuevo sin ignorar, que exista en el arbol de trabajo. Barras /."""
    _, salida = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    rutas = [p for p in salida.decode("utf-8", "replace").split("\0") if p]
    return sorted({p for p in rutas if (RAIZ / p).is_file()})


_BASE = {}


def _base():
    """(directorio con comun/ y harnesses/ de e5d7a14, None) o (None, motivo)."""
    if "dir" in _BASE:
        return _BASE["dir"], _BASE["motivo"]
    codigo, _ = _git("cat-file", "-e", BASE + "^{commit}")
    if codigo != 0:
        _BASE.update(dir=None, motivo="no esta el commit %s en este clon (un clon superficial?): "
                                      "no hay contra que comparar" % BASE)
        return None, _BASE["motivo"]
    codigo, crudo = _git("archive", "--format=tar", BASE, "comun", "harnesses")
    if codigo != 0:
        _BASE.update(dir=None, motivo="git archive %s fallo" % BASE)
        return None, _BASE["motivo"]
    destino = Path(tempfile.gettempdir()) / ("harness-hu63-base-" + uuid.uuid4().hex[:8])
    with tarfile.open(fileobj=io.BytesIO(crudo)) as tar:
        tar.extractall(str(destino))
    _BASE.update(dir=destino, motivo=None)
    return destino, None


def _sin_base(t, eid, motivo):
    t.igual("%s la linea de base %s esta disponible" % (eid, BASE), "disponible", motivo)


def _modulo_viejo():
    """El bienvenida.py de e5d7a14, importado desde su comun/ extraido, con schemas/ al lado:
    `_forma_fuentes` busca source-state.schema.json relativo a __file__."""
    base, motivo = _base()
    if base is None:
        return None, motivo
    if "viejo" not in _BASE:
        _BASE["viejo"] = _cargar("bienvenida_hu63_viejo",
                                 base / "comun" / "hooks" / "lib" / "bienvenida.py")
    return _BASE["viejo"], None


# -- el proyecto de prueba ---------------------------------------------------------

def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def _json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False))


def _copiar(origen, destino):
    shutil.copytree(str(origen), str(destino), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gitkeep"))


def _fuente(estado):
    return {"state": estado, "registry_version": "6.3", "observed_version": None,
            "attachmentId": None, "filename": None, "size": None, "created": None,
            "observed_sha256": None, "registry_sha256": None, "downloaded": False,
            "effectiveRisk": "MEDIUM", "derived_impact": [], "stale_derived": [],
            "blocking": estado not in ("CURRENT", "RETIRED"), "evidence": []}


def _lock_nuevo():
    return {"version": VERSION_LOCK, "instalado": "2026-09-30 10:00:00",
            "backup": ".claude\\.harness-backup\\20260930-100000", "archivos": []}


def _lock_con(harness):
    lock = _lock_nuevo()
    lock["harness"] = harness
    return lock


def _instalado(lock=None, config=None, indice=False):
    """Un proyecto con .claude/harness/ armado como lo deja install.ps1, desde los arboles de
    este repositorio: asi los dos modulos de E-27 y E-35 resuelven el runtime contra el mismo
    arbol. `lock` es un dict, un texto crudo, o None para no escribirlo."""
    proy = Path(tempfile.gettempdir()) / ("harness-hu63-" + uuid.uuid4().hex[:8])
    claude = proy / ".claude"
    h = claude / "harness"
    _copiar(HOOKS, h / "hooks")
    _copiar(RAIZ / "comun" / "schemas", h / "schemas")
    _copiar(RAIZ / "comun" / "reglas", h / "reglas")
    _copiar(RAIZ / "comun" / "bin", h / "bin")
    _copiar(RAIZ / "harnesses" / "desarrollo" / "reglas", h / "reglas" / "desarrollo")
    _copiar(BIN, h / "bin" / "desarrollo")
    renderizador = h / "bin" / "desarrollo" / "contabilidad" / "statusline.py"
    comando = "python '%s'" % renderizador.as_posix()
    _json(claude / "settings.json",
          {"permissions": {"deny": ["Read(./.env)", "Read(./.env.*)"]},
           "statusLine": {"type": "command", "command": comando}})
    B.escribir_senal_de_vida(str(proy), SESION, B.BLOCK4_OK,
                             B.version_del_renderizador(str(renderizador)),
                             momento="2026-10-01T11:00:00")
    _json(claude / "harness.config.json", dict({"usuario": USUARIO}, **(config or {})))
    integ = {n: {"estado": "AVAILABLE", "motivo": "", "verificado_en": "2026-10-01T10:00:00",
                 "capacidades": []} for n in ("jira", "gitlab")}
    _json(claude / "harness.capacidades.json",
          {"schema_version": "integraciones/1.0", "version_harness": VERSION_LOCK,
           "integraciones": integ, "capacidades": {}})
    _json(claude / "harness.fuentes.json",
          {"schema_version": "sources-state/1.1", "verified_at": "2026-10-01T09:00:00",
           "ficha": None, "decisions": {}, "warnings": [], "pending_count": 0,
           "sources": {s: _fuente("CURRENT") for s in TODAS}})
    if isinstance(lock, dict):
        _json(claude / "harness.lock.json", lock)
    elif isinstance(lock, str):
        _escribir(claude / "harness.lock.json", lock)
    if indice:
        _escribir(proy / "docs" / "codebase" / "indice.md", "# Indice\n")
    return proy


def _poner_lock(proy, lock):
    ruta = proy / ".claude" / "harness.lock.json"
    if lock is None:
        if ruta.exists():
            ruta.unlink()
    elif isinstance(lock, str):
        _escribir(ruta, lock)
    else:
        _json(ruta, lock)


def _sesion(proy):
    """session-start.py de este repositorio, como lo invoca Claude Code: (codigo, crudo, ctx)."""
    payload = {"session_id": SESION, "cwd": str(proy), "hook_event_name": "SessionStart",
               "source": "startup"}
    r = subprocess.run([sys.executable, str(HOOKS / "session-start.py")],
                       input=json.dumps(payload).encode("utf-8"),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    crudo = r.stdout.decode("utf-8", "replace")
    ctx = ""
    if crudo.strip():
        ctx = (json.loads(crudo).get("hookSpecificOutput") or {}).get("additionalContext") or ""
    return r.returncode, crudo, ctx


def _sesion_limpia(proy):
    """Una sesion que no deja rastro: harness.installation.json vuelve a como estaba."""
    ruta = proy / ".claude" / "harness.installation.json"
    antes = ruta.read_bytes() if ruta.exists() else None
    try:
        return _sesion(proy)
    finally:
        if antes is None:
            if ruta.exists():
                ruta.unlink()
        else:
            ruta.write_bytes(antes)


def _cli(proy, *args):
    entorno = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, str(CLI)] + list(args) + ["--proyecto", str(proy)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=entorno)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


def _validar(doc):
    esquema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ARMADOR.controlar_soporte(esquema)
    return ARMADOR.validar(doc, esquema)


def _texto(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)


# Los avisos del recorrido del codigo de SessionStart, los mismos de 13_contexto.py.
MARCAS_RECORRIDO = ("Sin indice del codigo todavia", "Hay fichas del codigo sin indice.md",
                    "no tiene su project-context.json")


# -- E-01 a E-03: un solo producto, un solo manifiesto ------------------------------

def test_e01_sin_analisis_y_un_solo_manifiesto(t):
    """E-01 — git ls-files no lista nada bajo harnesses/analisis/, y el unico manifest.json
    versionado es el de la raiz."""
    archivos = _archivos_del_repo()
    t.vacio("E-01 nada bajo harnesses/analisis/",
            [p for p in archivos if p.startswith("harnesses/analisis/")])
    _, indice = _git("ls-files", "harnesses/analisis")
    t.vacio("E-01 git ls-files harnesses/analisis no lista nada", indice.decode().strip())
    t.igual("E-01 el unico manifest.json es el de la raiz", ["manifest.json"],
            [p for p in archivos if p == "manifest.json" or p.endswith("/manifest.json")])


def _manifiesto():
    return json.loads((RAIZ / "manifest.json").read_text(encoding="utf-8-sig"))


def test_e02_el_manifiesto_tiene_solo_lo_que_alguien_lee(t):
    """E-02 — manifest.json tiene exactamente requiereClaudeCode, requierePython,
    capacidadesSoportadas y config, y ninguna otra clave."""
    if not (RAIZ / "manifest.json").is_file():
        t.verdadero("E-02 existe manifest.json en la raiz", False)
        return
    t.igual("E-02 las claves del manifiesto",
            sorted(["requiereClaudeCode", "requierePython", "capacidadesSoportadas", "config"]),
            sorted(_manifiesto().keys()))


def test_e03_la_config_es_la_de_comun_seguida_de_la_de_desarrollo(t):
    """E-03 — config de manifest.json es la de comun/manifest.json de e5d7a14 seguida de la de
    harnesses/desarrollo/manifest.json de e5d7a14: mismas claves, valores y orden, con
    usuario: "" primera."""
    base, motivo = _base()
    if base is None:
        _sin_base(t, "E-03", motivo)
        return
    if not (RAIZ / "manifest.json").is_file():
        t.verdadero("E-03 existe manifest.json en la raiz", False)
        return
    comun = json.loads((base / "comun" / "manifest.json").read_text(encoding="utf-8-sig"))
    dev = json.loads((base / "harnesses" / "desarrollo" / "manifest.json").read_text(encoding="utf-8-sig"))
    esperado = list(comun["config"].items())
    vistas = set(comun["config"])
    esperado += [(k, v) for k, v in dev["config"].items() if k not in vistas]
    obtenido = list(_manifiesto()["config"].items())
    t.igual("E-03 mismas claves, mismos valores, mismo orden", esperado, obtenido)
    t.igual("E-03 usuario vacio, primera", ("usuario", ""), obtenido[0] if obtenido else None)


# -- E-12, E-13 y E-62: lo que desaparece, en el texto --------------------------------

FORMAS_ANALISIS = ("harnesses/analisis", "harnesses\\analisis", "'analisis'", '"analisis"',
                   "`analisis`", "solo analisis", "hu-escribir", "hu-redactor", "hu-refutador",
                   "rutaHU", "rutaMaquetas", "gestorTickets")
EXCEPCION_E12 = ("harnesses/desarrollo/agents/dev-refutador.md",
                 "Hermano de harnesses/analisis/agents/hu-refutador.md")


def _leer_texto(ruta):
    return (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")


def test_e12_ninguna_referencia_funcional_a_analisis(t):
    """E-12 — install.ps1 no dice analisis en ninguna forma. En manifest.json, comun/ y
    harnesses/desarrollo/ no aparece ninguna de las formas de analisis como harness. La unica
    excepcion es el comentario de dev-refutador.md, cuya huella es la clave de la cache de la
    refutacion atomica."""
    instalador = _leer_texto("install.ps1")
    t.vacio("E-12 install.ps1 no dice analisis",
            [l.strip() for l in instalador.splitlines() if "analisis" in l.lower()])
    hallados = []
    for ruta in _archivos_del_repo():
        if not (ruta == "manifest.json" or ruta.startswith("comun/")
                or ruta.startswith("harnesses/desarrollo/")):
            continue
        for n, linea in enumerate(_leer_texto(ruta).splitlines(), 1):
            if ruta == EXCEPCION_E12[0] and EXCEPCION_E12[1] in linea:
                continue
            for forma in FORMAS_ANALISIS:
                if forma in linea:
                    hallados.append("%s:%d %s" % (ruta, n, forma))
    t.vacio("E-12 ninguna forma de analisis como harness en lo que se instala", hallados)
    t.contiene("E-12 la excepcion sigue siendo una sola linea, intacta", EXCEPCION_E12[1],
               _leer_texto(EXCEPCION_E12[0]))


def test_e13_la_documentacion_presenta_un_producto(t):
    """E-13 — docs/agregar-un-harness.md no existe; README.md, docs/instalacion.md y
    docs/memoria.md no tienen el parametro viejo ni las secciones de varios harnesses."""
    t.verdadero("E-13 docs/agregar-un-harness.md no existe",
                not (RAIZ / "docs" / "agregar-un-harness.md").exists())
    for ruta in ("README.md", "docs/instalacion.md", "docs/memoria.md"):
        texto = _leer_texto(ruta)
        t.vacio("E-13 %s no pasa el parametro viejo" % ruta,
                [l.strip() for l in texto.splitlines() if PARAMETRO_VIEJO.search(l)])
        for seccion in ("Los dos harness", "Agregar un tercer harness", "Sumar el segundo harness"):
            t.no_contiene("E-13 %s no tiene la seccion %s" % (ruta, seccion), seccion, texto)


PATRONES_E62 = (
    ("Get-HarnessDisponibles", r"Get-HarnessDisponibles"),
    ("la variable $Ids", r"\$Ids\b"),
    ("la variable $id", r"\$id\b"),
    ("la variable $Harness", r"\$Harness\b"),
    ("la variable $heredados", r"\$heredados\b"),
    ("la variable $disponibles", r"\$disponibles\b"),
    ("el argumento -Ids", r"(?<![\w$])-Ids\b"),
    ("partir ids por coma", r"-split\s*['\"]\s*,\s*['\"]"),
    ("harness leido como propiedad", r"\$\w+\.harness\b(?![-.])"),
    ("Properties['harness']", r"Properties\[\s*['\"]harness['\"]\s*\]"),
    ("la clave harness = del lock", r"(?m)^\s*harness\s*="),
    (".prefijo", r"\.prefijo\b"),
    ("['prefijo']", r"\[\s*['\"]prefijo['\"]\s*\]"),
    ("$prefijos", r"\$prefijos\b"),
    ("prefijos repetidos", r"prefijos repetidos"),
    ("manifiestos", r"manifiestos"),
    ("harnesses sin \\desarrollo", r"harnesses(?![\\/]desarrollo)"),
    ("una condicion sobre un id (operador, id)",
     r"-[ci]?(?:not)?(?:contains|in|eq|ne|like|match)\s+['\"](?:comun|desarrollo|analisis)['\"]"),
    ("una condicion sobre un id (id, operador)",
     r"['\"](?:comun|desarrollo|analisis)['\"]\s+-[ci]?(?:not)?(?:contains|in|eq|ne|like|match)\b"),
)


def test_e62_la_maquinaria_de_composicion_no_esta_ni_sin_usar(t):
    """E-62 — install.ps1 no conserva la maquinaria de composicion, comentarios incluidos y sin
    distinguir mayusculas. La palabra desarrollo en rutas no cuenta."""
    texto = _leer_texto("install.ps1")
    for nombre, patron in PATRONES_E62:
        hallados = [m.group(0) for m in re.finditer(patron, texto, re.IGNORECASE)]
        t.vacio("E-62 install.ps1 no tiene %s" % nombre, hallados)


# -- E-27 a E-35: la bienvenida, SessionStart y la CLI ------------------------------

def test_e27_el_resolvedor_da_lo_mismo_que_0_28_0_con_desarrollo(t):
    """E-27 — con un lock sin `harness`, el resolvedor de este cambio da el mismo documento que
    el de e5d7a14 con harness: ["comun", "desarrollo"]. Entre las dos llamadas solo se
    reescribe el lock."""
    viejo, motivo = _modulo_viejo()
    if viejo is None:
        _sin_base(t, "E-27", motivo)
        return
    proy = _instalado(_lock_nuevo())
    try:
        nuevo_doc = B.resolver(str(proy), momento=MOMENTO)
        _poner_lock(proy, _lock_con(["comun", "desarrollo"]))
        viejo_doc = viejo.resolver(str(proy), momento=MOMENTO)
        t.igual("E-27 el mismo documento", _texto(viejo_doc), _texto(nuevo_doc))
        t.igual("E-27 y no es un documento bloqueado", [],
                nuevo_doc["bootstrap"]["blockingConditions"])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


VARIANTES_E28 = (("analisis", _lock_con(["comun", "analisis"])),
                 ("datos", _lock_con(["comun", "datos"])),
                 ("lista vacia", _lock_con([])),
                 ("sin el campo", _lock_nuevo()))


def test_e28_el_campo_harness_no_cambia_nada(t):
    """E-28 — con ["comun","analisis"], ["comun","datos"], [] o sin el campo, el resolvedor da
    el mismo documento, y SessionStart el mismo encabezado y el mismo aviso del recorrido."""
    proy = _instalado(_lock_con(["comun", "desarrollo"]))
    try:
        referencia = _texto(B.resolver(str(proy), momento=MOMENTO))
        _, sesion_ref, _ = _sesion_limpia(proy)
        for rotulo, lock in VARIANTES_E28:
            _poner_lock(proy, lock)
            t.igual("E-28 %s: el mismo documento" % rotulo, referencia,
                    _texto(B.resolver(str(proy), momento=MOMENTO)))
            _, sesion, _ = _sesion_limpia(proy)
            t.igual("E-28 %s: SessionStart sale igual" % rotulo, sesion_ref, sesion)
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e29_harness_id_constante_y_schema_sin_cambios(t):
    """E-29 — harnessId es "desarrollo" en todo harness.installation.json que escriban el
    registro del instalador o session-start.py, diga lo que diga el lock, y valida contra el
    schema, que no cambia."""
    for rotulo, lock in VARIANTES_E28 + (("desarrollo", _lock_con(["comun", "desarrollo"])),):
        proy = _instalado(lock)
        try:
            doc = B.registrar_instalacion(str(proy), momento=MOMENTO)
            t.igual("E-29 %s: el registro escribe harnessId desarrollo" % rotulo,
                    "desarrollo", doc["harnessId"])
            t.vacio("E-29 %s: el registro valida contra el schema" % rotulo, _validar(doc))
            (proy / ".claude" / "harness.installation.json").unlink()
            codigo, _, _ = _sesion(proy)
            t.igual("E-29 %s: session-start sale 0" % rotulo, 0, codigo)
            escrito = json.loads((proy / ".claude" / "harness.installation.json")
                                 .read_text(encoding="utf-8"))
            t.igual("E-29 %s: session-start escribe harnessId desarrollo" % rotulo,
                    "desarrollo", escrito["harnessId"])
            t.vacio("E-29 %s: lo de session-start valida contra el schema" % rotulo,
                    _validar(escrito))
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)
    base, motivo = _base()
    if base is None:
        _sin_base(t, "E-29", motivo)
        return
    codigo, _ = _git("diff", "--quiet", BASE, "--",
                     "comun/schemas/harness-installation-state.schema.json")
    t.igual("E-29 harness-installation-state.schema.json no cambio desde %s" % BASE, 0, codigo)


def test_e30_sin_lock_bloquea_y_calcula_todo(t):
    """E-30 — sin lockfile, o con uno ilegible, el estado es BLOCKED con su condicion, y
    integraciones, knowledge (applies true) y los tres runtimeComponents se calculan con el
    mismo codigo que con un lock sano; la version sale de installedVersion."""
    proy = _instalado(_lock_nuevo())
    try:
        B.registrar_instalacion(str(proy), momento=MOMENTO)
        sano = B.resolver(str(proy), momento=MOMENTO)
        for rotulo, lock, condicion in (("sin lockfile", None, "LOCKFILE_MISSING"),
                                        ("JSON roto", "{no es json", "LOCKFILE_UNREADABLE"),
                                        ("un arreglo JSON", "[1, 2]", "LOCKFILE_UNREADABLE")):
            _poner_lock(proy, lock)
            doc = B.resolver(str(proy), momento=MOMENTO)
            t.igual("E-30 %s: BLOCKED" % rotulo, "BLOCKED", doc["bootstrap"]["status"])
            t.verdadero("E-30 %s: con %s" % (rotulo, condicion),
                        condicion in doc["bootstrap"]["blockingConditions"])
            t.igual("E-30 %s: knowledge.applies true" % rotulo, True,
                    (doc.get("knowledge") or {}).get("applies"))
            t.verdadero("E-30 %s: hay integraciones" % rotulo, bool(doc.get("integrations")))
            for clave in ("integrations", "knowledge", "runtimeComponents"):
                t.igual("E-30 %s: %s igual que con un lock sano" % (rotulo, clave),
                        _texto(sano.get(clave)), _texto(doc.get(clave)))
            t.igual("E-30 %s: la version sale de installedVersion" % rotulo,
                    VERSION_LOCK, doc.get("installedVersion"))
        _poner_lock(proy, "[1, 2]")
        codigo, _, ctx = _sesion_limpia(proy)
        t.igual("E-30 con un lock que es un arreglo, session-start sale 0", 0, codigo)
        t.contiene("E-30 y su bloque sale entero", "git:", ctx)
        t.vacio("E-30 sin encabezado de harness",
                [l for l in ctx.splitlines() if "harness v" in l or "harness:" in l])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def _encabezado(ctx):
    return [l for l in ctx.splitlines() if l.startswith(USUARIO + " - ") or l.startswith(USUARIO)]


def test_e31_el_encabezado_no_nombra_ids(t):
    """E-31 — el encabezado de SessionStart es `<usuario> - harness v<version>`, sin comun,
    desarrollo ni analisis, tambien con un lock 0.28.0."""
    for rotulo, lock in (("lock nuevo", _lock_nuevo()),
                         ("lock 0.28.0 con desarrollo", _lock_con(["comun", "desarrollo"])),
                         ("lock 0.28.0 con analisis", _lock_con(["comun", "analisis", "desarrollo"]))):
        proy = _instalado(lock)
        try:
            codigo, _, ctx = _sesion_limpia(proy)
            t.igual("E-31 %s: sale 0" % rotulo, 0, codigo)
            t.igual("E-31 %s: el encabezado" % rotulo,
                    ["%s - harness v%s" % (USUARIO, VERSION_LOCK)], _encabezado(ctx))
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)


def test_e32_el_aviso_del_recorrido_con_cualquier_lock_legible(t):
    """E-32 — SessionStart da el aviso del recorrido del codigo con cualquier lockfile legible,
    diga o no `desarrollo`. Sin lockfile no da ninguno. (E-16 y E-17 de 13_contexto.py lo prueban
    con el aviso entero; aca, el lock sin el campo y el caso sin lock.)"""
    proy = _instalado(_lock_nuevo())
    try:
        _, _, ctx = _sesion_limpia(proy)
        t.contiene("E-32 lock sin el campo harness: avisa que no hay indice",
                   MARCAS_RECORRIDO[0], ctx)
        _poner_lock(proy, None)
        _, _, ctx = _sesion_limpia(proy)
        for marca in MARCAS_RECORRIDO:
            t.no_contiene("E-32 sin lockfile no avisa: %s" % marca, marca, ctx)
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e34_la_cli_muestra_el_runtime_siempre(t):
    """E-34 — dev-harness.py harness, con y sin --verbose, muestra Runtime / Observabilidad con
    los tres componentes en cualquier proyecto instalado, y ningun comando de la CLI imprime
    `sin el harness de desarrollo`."""
    t.no_contiene("E-34 la CLI no tiene el texto", "sin el harness de desarrollo",
                  CLI.read_text(encoding="utf-8"))
    for rotulo, lock in (("lock nuevo", _lock_nuevo()),
                         ("lock 0.28.0 con analisis", _lock_con(["comun", "analisis"]))):
        proy = _instalado(lock)
        try:
            for args in (("harness",), ("harness", "--verbose")):
                codigo, salida = _cli(proy, *args)
                nombre = "%s %s" % (rotulo, " ".join(args))
                t.igual("E-34 %s: sale 0" % nombre, 0, codigo)
                t.contiene("E-34 %s: Runtime / Observabilidad" % nombre,
                           "Runtime / Observabilidad", salida)
                for _, mostrado, _, _ in B.COMPONENTES:
                    t.contiene("E-34 %s: %s" % (nombre, mostrado), mostrado, salida)
                t.no_contiene("E-34 %s: no dice sin el harness de desarrollo" % nombre,
                              "sin el harness de desarrollo", salida)
        finally:
            shutil.rmtree(str(proy), ignore_errors=True)


def test_e35_los_renderizadores_dan_el_mismo_texto(t):
    """E-35 — para un mismo documento, los renderizadores de este cambio y los de e5d7a14 dan
    el mismo texto. Se compara solo el renderizado: cada documento se arma una vez, con el
    resolvedor nuevo, y se les pasa a los dos modulos."""
    viejo, motivo = _modulo_viejo()
    if viejo is None:
        _sin_base(t, "E-35", motivo)
        return
    proy = _instalado(_lock_nuevo())
    try:
        de_e27 = B.resolver(str(proy), momento=MOMENTO)
        _poner_lock(proy, None)
        bloqueado = B.resolver(str(proy), momento=MOMENTO)
        actualizado = json.loads(json.dumps(de_e27))
        actualizado["welcome"] = {"firstRunShown": True, "lastShownAt": "2026-09-30T10:00:00",
                                  "upgradeFrom": "0.27.0"}
        for rotulo, doc in (("el de E-27", de_e27), ("BLOCKED sin lockfile", bloqueado),
                            ("con una actualizacion pendiente", actualizado)):
            for funcion in ("renderizar_bienvenida", "renderizar_actualizacion",
                            "renderizar_linea", "renderizar"):
                t.igual("E-35 %s: %s da el mismo texto" % (rotulo, funcion),
                        getattr(viejo, funcion)(json.loads(json.dumps(doc))),
                        getattr(B, funcion)(json.loads(json.dumps(doc))))
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


# -- E-52: el registro de agentes en la fabrica -------------------------------------

def test_e52_el_registro_de_agentes_de_la_fabrica_sigue_valido(t):
    """E-52 — en la fabrica, registro_agentes.reporte() da registryValid true, con 11 agentes
    declarados y validos, 27 skills instaladas y 2 pendientes. Eran 10: la Wave 5 de Flow
    Governance registro dev-iniciador-code (integracion-flow-governance-0-31)."""
    if str(BIN) not in sys.path:
        sys.path.insert(0, str(BIN))
    from orquestacion import registro_agentes
    r = registro_agentes.reporte()
    t.igual("E-52 registryValid", True, r["result"]["registryValid"])
    t.igual("E-52 agentes declarados", 11, r["summary"]["declaredAgents"])
    t.igual("E-52 agentes validos", 11, r["summary"]["validAgents"])
    t.igual("E-52 skills instaladas", 27, r["summary"]["installedSkills"])
    t.igual("E-52 skills pendientes", 2, r["summary"]["pendingSkills"])


# -- E-56 a E-59: documentacion y fabrica --------------------------------------------

def _seccion(texto, titulo):
    """El texto de la seccion `## ...titulo...` hasta la siguiente `## `."""
    salida, adentro = [], False
    for linea in texto.splitlines():
        if linea.startswith("## "):
            if adentro:
                break
            adentro = titulo.lower() in linea.lower()
            continue
        if adentro:
            salida.append(linea)
    return "\n".join(salida)


def test_e56_instalacion_dice_que_cambio_al_actualizar(t):
    """E-56 — docs/instalacion.md dice, en su paso de actualizacion, que el parametro viejo ya
    no existe y que sale de un proyecto que tenia analisis."""
    seccion = _seccion(_leer_texto("docs/instalacion.md"), "Actualizar")
    t.verdadero("E-56 hay un paso de actualizacion", bool(seccion.strip()))
    t.contiene("E-56 nombra el parametro", "Harness", seccion)
    t.contiene("E-56 dice que ya no existe", "ya no existe", seccion)
    for nombre in ("hu-escribir", "hu-redactor", "hu-refutador", "Trabajo funcional"):
        t.contiene("E-56 dice que sale %s" % nombre, nombre, seccion)


def test_e57_la_fabrica_nombra_un_solo_manifiesto(t):
    """E-57 — harness-backend-engineer.md no tiene ningun comando con el parametro viejo, y
    ningun archivo de .claude/, ni el CLAUDE.md de la fabrica, nombra comun/manifest.json o
    harnesses/*/manifest.json."""
    t.vacio("E-57 harness-backend-engineer.md sin el parametro viejo",
            [l.strip() for l in _leer_texto(".claude/agents/harness-backend-engineer.md").splitlines()
             if PARAMETRO_VIEJO.search(l)])
    viejo = re.compile(r"comun[/\\]manifest\.json|harnesses[/\\](?:\*|[\w.-]+)[/\\]manifest\.json")
    hallados = []
    for ruta in _archivos_del_repo():
        if ruta.startswith(".claude/") or ruta == "CLAUDE.md":
            for n, linea in enumerate(_leer_texto(ruta).splitlines(), 1):
                if viejo.search(linea):
                    hallados.append("%s:%d" % (ruta, n))
    t.vacio("E-57 nadie en .claude/ ni CLAUDE.md nombra un manifiesto viejo", hallados)


def test_e58_las_adaptaciones_retiradas_dicen_que_se_retiraron(t):
    """E-58 — cada entrada de adaptadoEn de terceros.lock.json que nombra un archivo que git no
    conoce dice que se retiro, en que version y con que cambio."""
    lock = json.loads(_leer_texto("terceros/terceros.lock.json"))
    conocidos = set(_archivos_del_repo())
    vistas = 0
    for origen in lock["origenes"]:
        for entrada in origen.get("adaptadoEn", []):
            ruta = entrada.split(" ", 1)[0]
            if ruta in conocidos:
                continue
            vistas += 1
            t.verdadero("E-58 %s dice que se retiro y en que version" % ruta,
                        re.search(r"retirad[oa] en \d+\.\d+\.\d+", entrada, re.IGNORECASE))
            t.contiene("E-58 %s dice con que cambio" % ruta, "harness-unico", entrada)
    t.igual("E-58 son las dos adaptaciones de analisis", 2, vistas)


def test_e59_el_adr_de_un_solo_harness(t):
    """E-59 — existe docs/adr/0012-un-solo-harness.md, aceptado, y nombra las tres decisiones de
    producto."""
    ruta = RAIZ / "docs" / "adr" / "0012-un-solo-harness.md"
    t.verdadero("E-59 existe el ADR", ruta.is_file())
    if not ruta.is_file():
        return
    texto = ruta.read_text(encoding="utf-8")
    t.contiene("E-59 esta aceptado", "estado: aceptada", texto)
    t.contiene("E-59 desarrollo es el harness", "`desarrollo` es el harness", texto)
    t.contiene("E-59 analisis se retira", "`analisis` se retira", texto)
    t.contiene("E-59 la composicion sale", "composición", texto)


# -- E-61: la suite --------------------------------------------------------------------

PROPIOS = ("tests/casos/63-harness-unico-instalador.ps1", "tests/casos/63_harness_unico.py")
# E-61 nombra estas dos: `analisis` como nombre de una unidad de trabajo, no como harness.
PALABRAS_SUELTAS = (("tests/casos/20_orquestacion.py", '_unidad("analisis"'),
                    ("tests/casos/20_orquestacion.py", '"E-22 la unidad", "analisis"'))


def test_e61_la_suite_no_compone_harnesses(t):
    """E-61 — 06-composicion.ps1 no existe; fuera de los 63-*, ningun archivo de tests/ pasa el
    parametro viejo ni tiene las formas de analisis como harness de E-12. Adentro de los 63-*,
    el parametro viejo solo aparece en E-08 y en las instalaciones con el instalador de e5d7a14."""
    t.verdadero("E-61 06-composicion.ps1 no existe",
                not (RAIZ / "tests" / "casos" / "06-composicion.ps1").exists())
    parametro, formas = [], []
    for ruta in _archivos_del_repo():
        if not ruta.startswith("tests/") or ruta in PROPIOS:
            continue
        for n, linea in enumerate(_leer_texto(ruta).splitlines(), 1):
            if PARAMETRO_VIEJO.search(linea):
                parametro.append("%s:%d" % (ruta, n))
            if any(ruta == r and s in linea for r, s in PALABRAS_SUELTAS):
                continue
            for forma in FORMAS_ANALISIS:
                if forma in linea:
                    formas.append("%s:%d %s" % (ruta, n, forma))
    t.vacio("E-61 fuera de los 63-*, nadie pasa el parametro viejo", parametro)
    t.vacio("E-61 fuera de los 63-*, ninguna forma de analisis como harness", formas)
    ajenos = [n for n, l in enumerate(_leer_texto(PROPIOS[0]).splitlines(), 1)
              if PARAMETRO_VIEJO.search(l) and "E-08" not in l and "huViejo" not in l]
    t.vacio("E-61 en el 63 de PowerShell, el parametro viejo solo en E-08 y con el instalador viejo",
            ajenos)
    t.vacio("E-61 en este archivo no aparece el parametro viejo",
            [n for n, l in enumerate(_leer_texto(PROPIOS[1]).splitlines(), 1)
             if PARAMETRO_VIEJO.search(l)])
