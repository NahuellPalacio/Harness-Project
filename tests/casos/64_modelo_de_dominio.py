# Los escenarios de docs/cambios/canonical-domain-model/spec.md que no instalan: el documento
# canonico, el ADR, el plan y la regla de lectura, la TaskKey, los checks, las capabilities, el
# limite de la ejecucion y la documentacion. E-44 y E-45 instalan de verdad y viven en
# tests/casos/64-modelo-de-dominio-instalador.ps1. E-49 es la compuerta entera. Cada asercion
# empieza con su E-nn.
#
# La linea de base es 4c6f0f3 (0.29.0) y se saca de git en cada corrida con `git archive`, nunca
# de una copia versionada. Su codigo corre SIEMPRE en un proceso aparte, con su propio
# `harnesses/desarrollo/bin` adelante en sys.path: los paquetes `orquestacion` y `contabilidad`
# de la base y los de ahora se llaman igual, y en un mismo interprete el segundo import devolveria
# el primero. Sin esa historia -un clon superficial- los escenarios que comparan contra ella
# fallan en rojo con el motivo: no se saltean.
#
# Las integraciones se simulan como en 19_contexto.py y 20_orquestacion.py: el transporte falso de
# 19 entra por `dev-harness.main`. Los casos de cierre de E-32 son los de 55_refutacion_atomica.py,
# con sus mismas funciones: el escenario los nombra.
import ast
import atexit
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = "4c6f0f3"
CASOS = RAIZ / "tests" / "casos"
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
SCHEMAS = RAIZ / "comun" / "schemas"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
DOC = RAIZ / "docs" / "dominio" / "modelo-canonico.md"
ADR = RAIZ / "docs" / "adr" / "0013-modelo-de-dominio-canonico.md"
SPEC = RAIZ / "docs" / "cambios" / "canonical-domain-model" / "spec.md"
SCHEMA_PLAN = SCHEMAS / "orchestration-plan.schema.json"
SCHEMA_CONTABLE = SCHEMAS / "execution-accounting-event.schema.json"
SCHEMA_SENAL = SCHEMAS / "normative-signal.schema.json"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from orquestacion import plan as orq_plan               # noqa: E402
from orquestacion import refutacion as R                # noqa: E402
from orquestacion import seguridad as seg_matriz        # noqa: E402
from contexto import tarea as c_tarea                   # noqa: E402
from contexto.comun import Acumulador                   # noqa: E402


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ARMADOR = _cargar("armador_dm64", RAIZ / "comun" / "bin" / "contexto-armar.py")
MEDIDOR = _cargar("medir_barra_dm64", RAIZ / "tests" / "medir_barra.py")
# Los casos de cierre de la refutacion atomica y el Jira falso del contexto de tarea.
M55 = _cargar("refutacion_para_64", CASOS / "55_refutacion_atomica.py")
M19 = _cargar("contexto_para_64", CASOS / "19_contexto.py")

CLAVE = "GCBA-64"
REGISTRO = {"jira.issue.read": "ENABLED", "gitlab.project.read": "DISABLED"}

ESTADOS_PLAN = ["CAPABILITY_RESOLUTION", "WAITING_FOR_HUMAN_APPROVAL", "READY_FOR_EXECUTION"]
ESTADOS_UNIDAD = ["PENDING", "BLOCKED", "WAITING_FOR_HUMAN_APPROVAL"]
# Los que salen del contrato (D4): ocho del plan y READY de la unidad.
QUE_SALEN = ("RECEIVED", "ANALYZING", "PLANNING", "WAITING_FOR_TOOL", "READY_FOR_DELEGATION",
             "DELEGATING", "REPLANNING", "FAILED", "READY")

# Los nueve contextos de 5.1 y las doce clasificaciones de la seccion 6 de la spec.
NUEVE = ["Work Intake", "Project Knowledge", "Normative Sources", "Planning", "Catalog",
         "Governance", "Guardrails", "Observability", "Host Integration"]
DOCE = ["Aggregate Root", "Entity", "Value Object", "Snapshot", "Record", "Domain Service",
        "Domain Policy", "Application Service", "DTO / Contract", "Configuration", "External",
        "Infrastructure"]
CAMPOS = ("Qué es", "Contexto", "Clasificación", "Identidad", "Ciclo y estados", "Invariantes",
          "Crea / cambia / lee", "Persistencia y contrato", "Dónde vive", "No es")
HERRAMIENTAS_DEL_HOST = ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "PowerShell",
                         "Glob", "Grep", "WebFetch", "WebSearch", "Skill", "Task", "Agent")
FORMA_DE_CAPABILITY = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,2}$")
CICLO = ("TASK_STARTED", "TASK_COMPLETED", "WORKUNIT_STARTED", "WORKUNIT_COMPLETED",
         "AGENT_RUN_STARTED", "AGENT_RUN_COMPLETED")


# -- temporales -------------------------------------------------------------------------------

def _quitar_solo_lectura(funcion, ruta, _):
    """git deja sus objetos de solo lectura, y en Windows rmtree no los puede borrar asi."""
    try:
        os.chmod(ruta, stat.S_IWRITE)
        funcion(ruta)
    except OSError:
        pass


def _borrar(ruta):
    shutil.rmtree(str(ruta), onerror=_quitar_solo_lectura)


def _tmp(prefijo="dm64-"):
    carpeta = Path(tempfile.mkdtemp(prefix=prefijo))
    atexit.register(_borrar, carpeta)
    return carpeta


def _escribir(ruta, texto):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(texto, encoding="utf-8", newline="\n")


def _json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False))


def _leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8-sig"))


def _copia(origen, prefijo="dm64-copia-"):
    destino = _tmp(prefijo)
    shutil.copytree(str(origen), str(destino), dirs_exist_ok=True)
    return destino


def _sha(datos):
    return hashlib.sha256(datos).hexdigest()


def _arbol(raiz, excluir=()):
    """{ruta relativa con /: sha256} de cada archivo bajo `raiz`, y cada carpeta como `<dir>/`.
    `excluir` son prefijos relativos que no entran. Una carpeta que no existe es {}."""
    raiz = Path(raiz)
    salida = {}
    if not raiz.exists():
        return salida
    for p in sorted(raiz.rglob("*")):
        rel = p.relative_to(raiz).as_posix()
        if any(rel == e or rel.startswith(e.rstrip("/") + "/") for e in excluir):
            continue
        salida[rel + ("/" if p.is_dir() else "")] = _sha(p.read_bytes()) if p.is_file() else "dir"
    return salida


def _diferencias(antes, despues):
    """Lo creado, modificado o borrado entre dos `_arbol`."""
    salida = []
    for k in sorted(set(antes) | set(despues)):
        if k not in despues:
            salida.append("borrado " + k)
        elif k not in antes:
            salida.append("creado " + k)
        elif antes[k] != despues[k]:
            salida.append("modificado " + k)
    return salida


# -- git y la linea de base -------------------------------------------------------------------

def _git(*args):
    r = subprocess.run(["git", "-C", str(RAIZ)] + list(args),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout


def _archivos_del_repo():
    """Lo versionado y lo nuevo sin ignorar, que exista en el arbol de trabajo. Barras /."""
    _, salida = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    rutas = [p for p in salida.decode("utf-8", "replace").split("\0") if p]
    return sorted({p for p in rutas if (RAIZ / p).is_file()})


def _extraer(crudo, destino):
    with tarfile.open(fileobj=io.BytesIO(crudo)) as tar:
        try:
            tar.extractall(str(destino), filter="data")
        except TypeError:                 # Python sin el filtro de tarfile (anterior a 3.12)
            tar.extractall(str(destino))


_BASE = {}


def _base():
    """(directorio con comun/ y harnesses/ de 4c6f0f3, None) o (None, motivo)."""
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
    destino = _tmp("dm64-base-")
    _extraer(crudo, destino)
    _BASE.update(dir=destino, motivo=None)
    return destino, None


def _sin_base(t, eid, motivo):
    t.igual("%s la linea de base %s esta disponible" % (eid, BASE), "disponible", motivo)


def _bin_base():
    base, motivo = _base()
    return (base / "harnesses" / "desarrollo" / "bin", None) if base else (None, motivo)


# -- procesos y CLI ---------------------------------------------------------------------------

def _proceso(argv, entrada=None, cwd=None, entorno=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.update(entorno or {})
    r = subprocess.run(argv, input=entrada, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env, cwd=cwd, timeout=600)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def _cli_de(bin_dir, proy, *args):
    """dev-harness.py de `bin_dir`, en un proceso aparte. (codigo, stdout, stderr)."""
    return _proceso([sys.executable, str(Path(bin_dir) / "dev-harness.py")] + list(args)
                    + ["--proyecto", str(proy)])


_MODULO_CLI = {}


def _cli(argv, transporte=None, transporte_bytes=None):
    """dev-harness.main de este arbol, en este proceso. (codigo, stdout, stderr)."""
    if "m" not in _MODULO_CLI:
        _MODULO_CLI["m"] = _cargar("dev_harness_dm64", CLI)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = _MODULO_CLI["m"].main([str(a) for a in argv], transporte, transporte_bytes)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


# -- el proyecto de prueba --------------------------------------------------------------------

def _contexto(clave=CLAVE):
    return {"meta": {"task_key": clave, "context_hash": "sha256:" + "a" * 64},
            "task": {"key": clave, "type": "Historia de Usuario",
                     "title": "Filtro por fecha en el listado",
                     "acceptance_criteria": ["Filtra por rango", "Muestra vacio"]},
            "project": {"ficha": {"key": "GCBA-7", "rules": ["Un tramite no se borra, se anula"]}},
            "documentation": {"items": [{"doc_id": "10"}, {"doc_id": "11"}]},
            "repository": {"project": {"name": "tramites/backoffice"}}}


def _unidad(uid, dominio="backend", capacidades=("repository.read",), dependencias=(),
            senales=(), **extra):
    u = {"id": uid, "objective": "hacer " + uid, "domain": dominio,
         "requiredCapabilities": list(capacidades), "dependencies": list(dependencias),
         "signals": list(senales)}
    u.update(extra)
    return u


def _propuesta(unidades, dominios=("backend",), **extra):
    p = {"objective": "Implementar el filtro por fecha", "domains": list(dominios),
         "policies": [], "workUnits": list(unidades)}
    p.update(extra)
    return p


CARA = ("ambiguity", "security_impact", "architectural_impact")   # premium: pide aprobacion


def _proyecto(clave=CLAVE, propuestas=None, config=None, git=False):
    """Un proyecto con el TaskContext de `clave`, el registro de capacidades y, si vienen, las
    propuestas como prop-<n>.json. `git`: sobre el repositorio de prueba, con src/sesion.py."""
    proy = _tmp("dm64-proy-")
    if git:
        shutil.copytree(str(_plantilla_git()), str(proy), dirs_exist_ok=True)
    _json(proy / ".claude" / "contextos" / (clave + ".json"), _contexto(clave))
    _json(proy / ".claude" / "harness.capacidades.json", {"capacidades": REGISTRO})
    if config is not None:
        _json(proy / ".claude" / "harness.config.json", config)
    for i, p in enumerate(propuestas or [], 1):
        _json(proy / ("prop-%d.json" % i), p)
    return proy


_PLANTILLA = []


def _plantilla_git():
    if not _PLANTILLA:
        base = _tmp("dm64-git-")
        _escribir(base / "src" / "sesion.py", "TIMEOUT = 900\n")
        _escribir(base / "src" / "error.py", "MENSAJE = 'Error generico'\n")
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "i"]):
            subprocess.run(["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t"]
                           + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        _PLANTILLA.append(base)
    return _PLANTILLA[0]


def _plan_de(proy, clave=CLAVE):
    return proy / ".claude" / "planes" / (clave + ".json")


def _bytes(ruta):
    ruta = Path(ruta)
    return ruta.read_bytes() if ruta.is_file() else None


# -- el documento canonico: lectura por secciones ---------------------------------------------

def _texto(ruta):
    return Path(ruta).read_text(encoding="utf-8")


def _seccion(texto, titulo, nivel=2):
    """Las lineas de la seccion `## titulo` (o `### titulo` con nivel=3), sin el encabezado,
    hasta el siguiente encabezado del mismo nivel o de uno mayor."""
    marca = "#" * nivel + " "
    salida, adentro = [], False
    for linea in texto.splitlines():
        m = re.match(r"^(#{1,6}) ", linea)
        if m and len(m.group(1)) <= nivel:
            if adentro:
                break
            adentro = linea.startswith(marca) and linea[len(marca):].strip() == titulo
            continue
        if adentro:
            salida.append(linea)
    return salida


def _apartados(lineas):
    """[(titulo, lineas)] de cada `### ` de una seccion, en orden."""
    salida = []
    for linea in lineas:
        if linea.startswith("### "):
            salida.append((linea[4:].strip(), []))
        elif salida:
            salida[-1][1].append(linea)
    return salida


def _celdas(linea):
    cuerpo = linea.strip()
    cuerpo = cuerpo[1:] if cuerpo.startswith("|") else cuerpo
    cuerpo = cuerpo[:-1] if cuerpo.endswith("|") and not cuerpo.endswith("\\|") else cuerpo
    return [c.strip() for c in re.split(r"(?<!\\)\|", cuerpo)]


def _tablas(lineas):
    """Las tablas de un trozo, en orden. Cada una es una lista de filas, encabezado incluido y
    sin la fila de guiones."""
    tablas, actual = [], None
    for linea in lineas:
        if linea.strip().startswith("|"):
            celdas = _celdas(linea)
            if actual is None:
                actual = []
                tablas.append(actual)
            if celdas and all(re.fullmatch(r":?-{3,}:?", c) for c in celdas if c):
                continue
            actual.append(celdas)
        else:
            actual = None
    return tablas


def _campos(lineas):
    """[(rotulo, valor)] de los items de primer nivel de un concepto. Una linea con sangria sigue
    al item anterior. Un item sin rotulo entra como ('<sin rotulo>', texto)."""
    campos = []
    for linea in lineas:
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", linea)
        if m:
            campos.append([m.group(1), m.group(2)])
        elif linea.startswith("- "):
            campos.append(["<sin rotulo>", linea[2:]])
        elif linea.strip() and campos and linea[:1] in (" ", "\t"):
            campos[-1][1] += "\n" + linea.strip()
        elif linea.strip() and campos:
            campos[-1][1] += "\n" + linea.strip()
    return [(r, v) for r, v in campos]


_DOC = {}


def _modelo():
    """El documento canonico leido una vez: texto, tabla del catalogo y bloques por concepto."""
    if "m" in _DOC:
        return _DOC["m"]
    texto = _texto(DOC) if DOC.is_file() else ""
    conceptos = _seccion(texto, "Conceptos")
    tablas = _tablas(conceptos)
    tabla = tablas[0] if tablas else []
    bloques = _apartados(conceptos)
    m = {"texto": texto, "encabezado": tabla[0] if tabla else [], "filas": tabla[1:],
         "bloques": bloques,
         "campos": {nombre: dict(_campos(lineas)) for nombre, lineas in bloques},
         "lista_campos": {nombre: _campos(lineas) for nombre, lineas in bloques}}
    m["catalogo"] = [f[0] for f in m["filas"] if f]
    _DOC["m"] = m
    return m


def _valor(texto):
    """El valor de un campo corto, sin punto final ni espacios."""
    return (texto or "").strip().rstrip(".").strip()


def _plano(texto):
    sin = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin).lower()


# -- E-01 a E-11: el documento canonico -------------------------------------------------------

def test_e01_el_catalogo_es_la_tabla_y_cada_concepto_tiene_su_encabezado(t):
    """E-01 — docs/dominio/modelo-canonico.md existe; `## Conceptos` abre con la tabla indice;
    cada concepto de la tabla aparece una sola vez como `### <Concepto>`, ningun `###` nombra uno
    que no este, y ningun nombre se repite sin distinguir mayusculas. No se exige cantidad."""
    t.verdadero("E-01 existe docs/dominio/modelo-canonico.md", DOC.is_file())
    m = _modelo()
    t.igual("E-01 la seccion Conceptos abre con la tabla indice",
            ["Concepto", "Contexto", "Clasificación", "Qué es"], m["encabezado"])
    primera = next((l for l in _seccion(m["texto"], "Conceptos") if l.strip()
                    and not l.startswith("|")), "")
    t.verdadero("E-01 la tabla va antes del primer concepto", primera.startswith("### "))
    tabla, encabezados = m["catalogo"], [n for n, _ in m["bloques"]]
    t.verdadero("E-01 la tabla tiene conceptos", len(tabla) > 0)
    t.vacio("E-01 cada concepto de la tabla aparece exactamente una vez como ###",
            [n for n in tabla if encabezados.count(n) != 1])
    t.vacio("E-01 ningun ### de la seccion nombra un concepto que no esta en la tabla",
            [h for h in encabezados if h not in tabla])
    for donde, nombres in (("la tabla", tabla), ("los encabezados", encabezados)):
        bajos = [n.lower() for n in nombres]
        t.vacio("E-01 ningun nombre se repite en %s, sin distinguir mayusculas" % donde,
                sorted({n for n in bajos if bajos.count(n) > 1}))


def test_e02_cada_concepto_tiene_los_diez_campos(t):
    """E-02 — cada concepto tiene los diez campos rotulados, en orden; uno que no aplica dice
    `no aplica` y no se omite: ningun campo queda vacio."""
    m = _modelo()
    t.verdadero("E-02 hay conceptos para revisar", len(m["bloques"]) > 0)
    for nombre, campos in m["lista_campos"].items():
        t.igual("E-02 %s tiene los diez campos rotulados, en orden" % nombre, list(CAMPOS),
                [r for r, _ in campos])
        t.vacio("E-02 %s no deja ningun campo vacio" % nombre,
                [r for r, v in campos if not v.strip()])


# La precedencia de `plan.estado_de`, de la que mas pesa a la que menos (S5 de la primera
# verificacion): un hueco de capacidad, una aprobacion PENDING, una unidad BLOCKED. Sin ninguna,
# el plan esta listo.
PRECEDENCIA_S5 = (("hueco", "CAPABILITY_RESOLUTION"), ("aprobacion", "WAITING_FOR_HUMAN_APPROVAL"),
                  ("bloqueada", "CAPABILITY_RESOLUTION"))


def _documento_s5(hueco, aprobacion, bloqueada):
    """Lo minimo que lee `plan.estado_de`, con cada freno prendido o apagado."""
    return {"capabilityGaps": [{"capability": "no.existe"}] if hueco else [],
            "humanApprovals": [{"workUnit": "u1", "status": "PENDING" if aprobacion else "APPROVED"}],
            "workUnits": [{"id": "u1", "status": "BLOCKED" if bloqueada else "PENDING"}]}


def test_e02_s5_un_hueco_pesa_mas_que_una_aprobacion_pendiente(t):
    """E-02 (S5) — el Invariantes de ModelTierApproval describe una regla que existe: una
    aprobacion PENDING deja el plan en WAITING_FOR_HUMAN_APPROVAL solo si no hay un
    CapabilityGap. Se prueba en el codigo -`plan.estado_de` sobre las ocho combinaciones de
    frenos, y los planes que escribe `plan --propuesta` sobre las combinaciones de E-21- y el
    campo del documento tiene que decir esa misma precedencia, en ese orden."""
    for hueco in (False, True):
        for aprobacion in (False, True):
            for bloqueada in (False, True):
                prendidos = dict(hueco=hueco, aprobacion=aprobacion, bloqueada=bloqueada)
                esperado = next((estado for freno, estado in PRECEDENCIA_S5 if prendidos[freno]),
                                "READY_FOR_EXECUTION")
                rotulo = ", ".join(f for f, _ in PRECEDENCIA_S5 if prendidos[f]) or "sin frenos"
                t.igual("E-02 S5 estado_de con %s da %s" % (rotulo, esperado), esperado,
                        orq_plan.estado_de(_documento_s5(hueco, aprobacion, bloqueada)))

    con_los_dos, solo_aprobacion = [], []
    for rotulo, codigo, _, doc in _combinaciones():
        if doc is None:
            continue
        hueco = bool(doc.get("capabilityGaps"))
        pendiente = any(a.get("status") == "PENDING" for a in doc.get("humanApprovals") or [])
        if hueco and pendiente:
            con_los_dos.append(rotulo)
            t.igual("E-02 S5 %s: con un hueco y una aprobacion PENDING, el plan escrito queda en "
                    "CAPABILITY_RESOLUTION" % rotulo, "CAPABILITY_RESOLUTION", doc.get("status"))
        elif pendiente:
            solo_aprobacion.append(rotulo)
            t.igual("E-02 S5 %s: con una aprobacion PENDING y sin hueco, el plan escrito queda en "
                    "WAITING_FOR_HUMAN_APPROVAL" % rotulo, "WAITING_FOR_HUMAN_APPROVAL",
                    doc.get("status"))
    t.verdadero("E-02 S5 las combinaciones de E-21 escriben planes con un hueco y una aprobacion "
                "PENDING a la vez", con_los_dos)
    t.verdadero("E-02 S5 y planes con una aprobacion PENDING sin hueco", solo_aprobacion)

    invariantes = _plano((_modelo()["campos"].get("ModelTierApproval") or {}).get("Invariantes"))
    for aguja in ("capabilitygap", "capability_resolution", "waiting_for_human_approval",
                  "estado_de"):
        t.contiene("E-02 S5 el Invariantes de ModelTierApproval nombra %s" % aguja, aguja,
                   invariantes)
    # Desde `estado_de`, el campo nombra los frenos en el orden en que el codigo los mira.
    desde = invariantes[invariantes.find("estado_de"):] if "estado_de" in invariantes else ""
    orden = ("capabilitygap", "aprobaciones", "blocked", "ready_for_execution")
    t.igual("E-02 S5 el Invariantes de ModelTierApproval dice la precedencia de estado_de: hueco, "
            "aprobaciones, BLOCKED y recien entonces READY_FOR_EXECUTION", list(orden),
            [a for p, a in sorted((desde.find(a), a) for a in orden) if p >= 0])


def test_e03_nueve_contextos_y_execution_reservado(t):
    """E-03 — el mapa declara nueve contextos y, aparte, Execution como limite reservado. El
    Contexto de cada concepto es uno de los nueve o External; External solo para un concepto
    External; cada contexto tiene al menos un concepto; ninguno es de Execution."""
    m = _modelo()
    mapa = _seccion(m["texto"], "Mapa de contextos")
    tablas = _tablas(mapa)
    contextos = [f[0] for f in tablas[0][1:]] if tablas else []
    t.igual("E-03 el mapa declara los nueve contextos", sorted(NUEVE), sorted(contextos))
    t.igual("E-03 son nueve, sin repetir", 9, len(set(contextos)))
    texto_mapa = "\n".join(mapa)
    t.verdadero("E-03 Execution figura aparte, como limite reservado y no como contexto",
                re.search(r"Execution no es un contexto: es un límite reservado", texto_mapa))
    t.vacio("E-03 Execution no esta en la tabla de contextos",
            [c for c in contextos if "Execution" in c])
    por_contexto = {}
    malos, externos, de_execution, distintos = [], [], [], []
    filas = {f[0]: f for f in m["filas"] if len(f) >= 3}
    for nombre, campos in m["campos"].items():
        ctx, cls = _valor(campos.get("Contexto")), _valor(campos.get("Clasificación"))
        por_contexto.setdefault(ctx, []).append(nombre)
        if ctx not in NUEVE + ["External"]:
            malos.append("%s: %s" % (nombre, ctx))
        if ctx == "External" and cls != "External":
            externos.append(nombre)
        if "Execution" in ctx:
            de_execution.append(nombre)
        if nombre in filas and filas[nombre][1] != ctx:
            distintos.append("%s: tabla %s, bloque %s" % (nombre, filas[nombre][1], ctx))
    t.vacio("E-03 el Contexto de cada concepto es uno de los nueve o External", malos)
    t.vacio("E-03 solo un concepto External tiene Contexto External", externos)
    t.vacio("E-03 cada uno de los nueve tiene al menos un concepto",
            [c for c in NUEVE if not por_contexto.get(c)])
    t.vacio("E-03 ningun concepto tiene Execution como contexto", de_execution)
    t.vacio("E-03 la tabla y el bloque dicen el mismo contexto", distintos)


def test_e04_la_clasificacion_es_una_de_las_doce(t):
    """E-04 — la Clasificacion de cada concepto es una de las doce de `## Clasificaciones`, y
    ninguno dice Domain Event."""
    m = _modelo()
    tablas = _tablas(_seccion(m["texto"], "Clasificaciones"))
    doce = [f[0] for f in tablas[0][1:]] if tablas else []
    t.igual("E-04 Clasificaciones tiene las doce de la spec", DOCE, doce)
    filas = {f[0]: f for f in m["filas"] if len(f) >= 3}
    fuera, distintas = [], []
    for nombre, campos in m["campos"].items():
        cls = _valor(campos.get("Clasificación"))
        if cls not in doce:
            fuera.append("%s: %s" % (nombre, cls))
        if nombre in filas and filas[nombre][2] != cls:
            distintas.append("%s: tabla %s, bloque %s" % (nombre, filas[nombre][2], cls))
    t.vacio("E-04 cada concepto tiene una de las doce", fuera)
    t.vacio("E-04 ningun concepto dice Domain Event",
            [n for n, c in m["campos"].items() if "Domain Event" in (c.get("Clasificación") or "")]
            + [f[0] for f in m["filas"] if len(f) >= 3 and "Domain Event" in f[2]])
    t.vacio("E-04 la tabla y el bloque dicen la misma clasificacion", distintas)


SCHEMA_NOMBRADO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.schema\.json")


def test_e05_cada_schema_tiene_su_concepto(t):
    """E-05 — cada uno de los 46 archivos de comun/schemas/ figura en Persistencia y contrato de
    al menos un concepto, y todo schema que nombra el documento existe en disco."""
    m = _modelo()
    en_disco = sorted(p.name for p in SCHEMAS.iterdir() if p.is_file())
    t.igual("E-05 son los 46 de comun/schemas/", 46, len(en_disco))
    nombrados = set()
    for campos in m["campos"].values():
        nombrados |= set(SCHEMA_NOMBRADO.findall(campos.get("Persistencia y contrato") or ""))
    t.vacio("E-05 cada schema figura en Persistencia y contrato de algun concepto",
            [s for s in en_disco if s not in nombrados])
    t.vacio("E-05 todo schema que nombra el documento existe en disco",
            sorted({s for s in SCHEMA_NOMBRADO.findall(m["texto"]) if s not in en_disco}))


def _conceptos_de_la_spec_3_2(catalogo):
    """{schema: [conceptos]} de la columna Concepto de la tabla de 3.2 de la spec. De cada celda
    entran los nombres que estan en el catalogo del documento, sin lo que va entre parentesis:
    `NormativeMatrix (Anexo II)` es NormativeMatrix, `Plan, WorkUnit` son los dos."""
    tablas = _tablas(_seccion(_texto(SPEC), "3.2 Los 46 schemas", nivel=3))
    salida = {}
    for fila in (tablas[0][1:] if tablas else []):
        if len(fila) < 2:
            continue
        schema = fila[0].strip().strip("`") + ".schema.json"
        nombres = [n.strip() for n in re.sub(r"\([^)]*\)", "", fila[1]).split(",")]
        salida[schema] = [n for n in nombres if n in catalogo]
    return salida


SCHEMAS_DE_BASES = ("database-environment-access-policy.schema.json", "database-profile.schema.json")


def _importa(ruta, modulo):
    """Si el fuente importa `modulo` (`import x`, `from . import x`, `from paquete import x`)."""
    for n in ast.walk(_arbol_py(ruta)):
        if isinstance(n, ast.Import) and any(a.name.split(".")[-1] == modulo for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and ((n.module or "").split(".")[-1] == modulo
                                              or any(a.name == modulo for a in n.names)):
            return True
    return False


def test_e05_s4_cada_schema_esta_en_el_concepto_que_dice_la_spec(t):
    """E-05 (S4) — el schema esta mapeado al concepto al que pertenece. Para cada schema cuya
    celda Concepto de 3.2 de la spec nombra un concepto, ese concepto lo nombra en su
    Persistencia y contrato. database-environment-access-policy no esta bajo NormativeMatrix: en
    el codigo, solo bases.py nombra los dos schemas de bases, nadie importa bases.py, y ni las
    matrices normativas ni el registro de controles los nombran -bases.py:3-4 dice que no es una
    regla de ES0901-."""
    m = _modelo()
    de_la_spec = _conceptos_de_la_spec_3_2(m["catalogo"])
    en_disco = sorted(p.name for p in SCHEMAS.iterdir() if p.is_file())
    t.igual("E-05 S4 la tabla de 3.2 de la spec tiene los schemas de comun/schemas/", en_disco,
            sorted(de_la_spec))
    t.vacio("E-05 S4 cada celda Concepto de 3.2 nombra un concepto del documento",
            sorted(s for s, c in de_la_spec.items() if not c))
    persistencia = {n: set(SCHEMA_NOMBRADO.findall(c.get("Persistencia y contrato") or ""))
                    for n, c in m["campos"].items()}
    t.vacio("E-05 S4 cada concepto que 3.2 de la spec le da a un schema lo nombra en su "
            "Persistencia y contrato",
            ["%s: %s" % (s, c) for s, conceptos in sorted(de_la_spec.items()) for c in conceptos
             if s not in persistencia.get(c, set())])
    for schema in SCHEMAS_DE_BASES:
        t.igual("E-05 S4 la spec mapea %s a DatabaseAccessPolicy" % schema,
                ["DatabaseAccessPolicy"], de_la_spec.get(schema))
    t.verdadero("E-05 S4 database-environment-access-policy.schema.json no esta bajo NormativeMatrix",
                SCHEMAS_DE_BASES[0] not in persistencia.get("NormativeMatrix", {SCHEMAS_DE_BASES[0]}))
    t.vacio("E-05 S4 ningun concepto de Governance nombra los schemas de bases",
            sorted("%s: %s" % (n, s) for n, c in m["campos"].items()
                   if _valor(c.get("Contexto")) == "Governance"
                   for s in SCHEMAS_DE_BASES if s in persistencia.get(n, set())))
    # Lo que dice el codigo, y lo que hace que eso sea cierto.
    t.contiene("E-05 S4 bases.py dice que no es una regla de ES0901", "No es una regla de ES0901",
               _texto(BIN / "orquestacion" / "bases.py"))
    t.igual("E-05 S4 en bin/, solo orquestacion/bases.py nombra los schemas de bases",
            ["orquestacion/bases.py"],
            sorted({p.relative_to(BIN).as_posix() for p in _py_de(BIN)
                    for c in _constantes(p) if any(s in c for s in SCHEMAS_DE_BASES)}))
    t.vacio("E-05 S4 ningun modulo de bin/ ni de comun/ importa bases.py",
            [p.relative_to(RAIZ).as_posix() for p in _py_de(BIN) + _py_de(RAIZ / "comun")
             if _importa(p, "bases")])
    normativos = sorted(REGLAS.glob("es090*.json")) + [REGLAS / "control-registry.json"]
    t.verdadero("E-05 S4 hay matrices normativas para revisar",
                len([p for p in normativos if p.name.startswith("es090")]) >= 2)
    t.vacio("E-05 S4 ni las matrices normativas ni el registro de controles nombran las bases",
            sorted(p.name for p in normativos
                   if re.search(r"database-(environment-access-policy|profile)", _texto(p))))


def _desigualdades_de_la_spec():
    tablas = _tablas(_seccion(_texto(SPEC), "4.3 Lo que no es lo mismo", nivel=3))
    return [f[0] for f in tablas[0][1:]] if tablas else []


def test_e06_las_catorce_desigualdades(t):
    """E-06 — `## Lo que no es lo mismo` tiene un apartado por cada una de las catorce
    desigualdades de 4.3, y cada apartado cita al menos una ruta del repo que existe."""
    m = _modelo()
    esperadas = _desigualdades_de_la_spec()
    t.igual("E-06 la spec trae catorce desigualdades", 14, len(esperadas))
    apartados = _apartados(_seccion(m["texto"], "Lo que no es lo mismo"))
    titulos = [a for a, _ in apartados]
    t.igual("E-06 un apartado por cada desigualdad de 4.3", sorted(esperadas), sorted(titulos))
    t.igual("E-06 son catorce apartados", 14, len(titulos))
    for titulo, lineas in apartados:
        rutas = [r for r in re.findall(r"`([^`\s]+)`", "\n".join(lineas))
                 if "/" in r and (RAIZ / r).exists()]
        t.verdadero("E-06 %s cita una ruta del repo que existe" % titulo, len(rutas) > 0)


def _desigualdad(titulo):
    """El texto del apartado `### titulo` de `## Lo que no es lo mismo`, o ''."""
    apartados = dict(_apartados(_seccion(_modelo()["texto"], "Lo que no es lo mismo")))
    return "\n".join(apartados.get(titulo) or [])


def _bloques(lineas):
    """Los parrafos y los items de primer nivel de un trozo, cada uno en una sola linea: un item
    arranca con `- `, y una linea en blanco corta el parrafo."""
    bloques, actual = [], None
    for linea in lineas:
        if not linea.strip():
            actual = None
        elif linea.startswith("- ") or actual is None:
            actual = [linea.strip()]
            bloques.append(actual)
        else:
            actual.append(linea.strip())
    return [" ".join(b) for b in bloques]


PROHIBE = re.compile(r"\b(prohib\w*|rechaz\w*|impid\w*|imped\w*|impon\w*)")
NIEGAN = {"no", "ni", "nada", "nadie", "ningun", "ninguna", "ninguno", "nunca", "sin"}


def _afirma(patron, texto):
    """Las frases de `texto` donde aparece `patron` sin una negacion en las cinco palabras de
    antes."""
    salida = []
    for frase in re.split(r"[.;:](?:\s|$)", _plano(texto)):
        for m in patron.finditer(frase):
            if not NIEGAN & set(re.findall(r"[a-z_]+", frase[:m.start()])[-5:]):
                salida.append(frase.strip())
    return salida


def _afirma_prohibicion(texto):
    """Las frases que dicen que algo prohibe, rechaza o impide, sin una negacion en las cinco
    palabras de antes: "el plan lo prohibe" si, "no se rechaza" y "nada impide" no."""
    return _afirma(PROHIBE, texto)


def test_e06_s1_una_herramienta_del_host_pedida_es_un_hueco(t):
    """E-06 (S1) — Capability ≠ Tool no se sostiene en una prohibicion, porque no la hay. Una
    propuesta que pide `Glob` y `Read` no se rechaza: el plan se escribe en CAPABILITY_RESOLUTION
    con los dos como CapabilityGap, y valida, porque requiredCapabilities no tiene patron. El
    apartado, y los Invariantes de Capability y de HostTool, dicen eso y no una prohibicion."""
    proy = _proyecto(propuestas=[_propuesta([_unidad("leer", capacidades=("Glob", "Read"))])])
    # En su propio proceso: si algo lo rechazara con un PlanInvalido que `main` no atrapa, aca
    # se ve el codigo de salida y no una excepcion que corta el resto de las aserciones.
    codigo, _, error = _cli_de(BIN, proy, "plan", CLAVE, "--propuesta", proy / "prop-1.json")
    t.igual("E-06 S1 una propuesta que pide Glob y Read no se rechaza: sale 0", 0, codigo)
    doc = _leer_json(_plan_de(proy)) if _plan_de(proy).is_file() else {}
    t.verdadero("E-06 S1 el plan se escribe", bool(doc))
    t.igual("E-06 S1 el plan queda en CAPABILITY_RESOLUTION", "CAPABILITY_RESOLUTION",
            doc.get("status"))
    t.igual("E-06 S1 Glob y Read quedan como CapabilityGap", ["Glob", "Read"],
            sorted(h.get("capability") for h in doc.get("capabilityGaps") or []))
    t.igual("E-06 S1 el plan escrito valida contra orchestration-plan/2.0", [],
            ARMADOR.validar(doc, _esquema_plan()) if doc else ["no hay plan"])
    pedidas = (_esquema_plan()["properties"]["workUnits"]["items"]["properties"]
               ["requiredCapabilities"])
    t.vacio("E-06 S1 requiredCapabilities no tiene patron ni enum en el schema",
            sorted(k for k in ("pattern", "enum") if k in (pedidas.get("items") or {}))
            + sorted(k for k in ("pattern", "enum") if k in pedidas))

    m = _modelo()
    textos = (("el apartado Capability ≠ Tool", _desigualdad("Capability ≠ Tool")),
              ("el Invariantes de Capability", (m["campos"].get("Capability") or {}).get("Invariantes")),
              ("el Invariantes de HostTool", (m["campos"].get("HostTool") or {}).get("Invariantes")))
    for rotulo, texto in textos:
        t.contiene("E-06 S1 %s nombra CapabilityGap" % rotulo, "CapabilityGap", texto)
        t.vacio("E-06 S1 %s no dice que algo lo prohibe, lo rechaza o lo impide" % rotulo,
                _afirma_prohibicion(texto))
    apartado = _desigualdad("Capability ≠ Tool")
    t.contiene("E-06 S1 el apartado dice que el plan queda en CAPABILITY_RESOLUTION",
               "CAPABILITY_RESOLUTION", apartado)
    t.contiene("E-06 S1 el apartado dice que requiredCapabilities no tiene patron",
               "no tiene patron", _plano(apartado))


COPIA_DEL_INSTALADOR = re.compile(r"Copy-Arbol\s+\(Join-Path\s+(\$[\w:]+)\s+'([^']+)'\)")


def test_e06_s2_controles_no_se_instala(t):
    """E-06 (S2) — Check ≠ development test no se sostiene en que los dos checks se instalen:
    install.ps1 no copia `controles/`. Cada Copy-Arbol del instalador copia una carpeta nombrada,
    ninguna es `controles`, y ningun literal del instalador la nombra. El apartado dice que
    `controles/` no se instala y no dice que ControlCheck se instale."""
    instalador = (RAIZ / "install.ps1").read_text(encoding="utf-8-sig")
    llamadas = [l for l in instalador.splitlines()
                if re.search(r"\bCopy-Arbol\b", l) and not re.match(r"\s*function\s", l)]
    copias = [(m.group(1), m.group(2).replace("\\", "/")) for l in llamadas
              for m in [COPIA_DEL_INSTALADOR.search(l)] if m]
    t.verdadero("E-06 S2 install.ps1 copia bin/ del producto con Copy-Arbol (se lee el mapa)",
                ("$origenProducto", "bin") in copias)
    t.igual("E-06 S2 cada Copy-Arbol de install.ps1 copia una carpeta nombrada", len(llamadas),
            len(copias))
    t.vacio("E-06 S2 ningun Copy-Arbol de install.ps1 copia controles",
            ["%s/%s" % c for c in copias if "controles" in c[1].lower()])
    t.vacio("E-06 S2 ningun literal de install.ps1 nombra controles",
            sorted({l.strip() for l in instalador.splitlines()
                    if re.search(r"['\"][^'\"\r\n]*controles[^'\"\r\n]*['\"]", l, re.I)}))

    apartado = _desigualdad("Check ≠ development test")
    bloques = [_plano(b) for b in _bloques(apartado.splitlines())]
    de_control = [b for b in bloques if "controlcheck" in b or "controles/" in b]
    t.verdadero("E-06 S2 el apartado dice que controles/ no se instala",
                any(re.search(r"controles/`?\s+no se instala\b", b) for b in de_control))
    t.vacio("E-06 S2 el apartado no dice que ControlCheck se instale",
            [b for b in de_control if re.search(r"(?<!no )(?<!si )\bse instalan?\b", b)])


def test_e06_s3_el_id_compartido_es_un_defecto_reportado(t):
    """E-06 (S3) — Policy ≠ Check no se sostiene en una excepcion deliberada: seguridad.py trata
    un id declarado con dos tipos como un defecto de los datos y lo reporta como
    SECURITY_CONTROL_ID_TYPE_COLLISION. El apartado nombra ese codigo y el id que el codigo
    reporta hoy sobre la matriz provista, y no dice "a proposito"."""
    matriz = {"rules": [{"id": "X1", "policies": ["compartido"], "checks": ["compartido", "check"]},
                        {"id": "X2", "policies": ["policy"], "reviews": ["review"]}]}
    t.igual("E-06 S3 seguridad.py reporta el id compartido con sus dos tipos y "
            "SECURITY_CONTROL_ID_TYPE_COLLISION, y nada mas",
            [{"id": "compartido", "types": ["CHECK", "POLICY"],
              "state": "SECURITY_CONTROL_ID_TYPE_COLLISION"}],
            seg_matriz.colisiones_de_id(matriz))
    provistas = [c["id"] for c in seg_matriz.colisiones_de_id()]
    t.verdadero("E-06 S3 la matriz provista tiene hoy un id compartido", provistas)
    apartado = _desigualdad("Policy ≠ Check")
    t.contiene("E-06 S3 el apartado nombra SECURITY_CONTROL_ID_TYPE_COLLISION",
               "SECURITY_CONTROL_ID_TYPE_COLLISION", apartado)
    for cid in provistas:
        t.contiene("E-06 S3 el apartado nombra el id que reporta el codigo: %s" % cid, cid, apartado)
    t.no_contiene("E-06 S3 el apartado no dice que es a proposito", "a proposito", _plano(apartado))


def test_e07_el_vocabulario_apunta_a_conceptos(t):
    """E-07 — cada fila de `## Vocabulario` apunta a un concepto del documento o dice `no es un
    concepto`."""
    m = _modelo()
    tablas = _tablas(_seccion(m["texto"], "Vocabulario"))
    filas = tablas[0][1:] if tablas else []
    t.verdadero("E-07 el vocabulario tiene filas", len(filas) > 0)
    malas = []
    for fila in filas:
        canon = fila[3] if len(fila) > 3 else ""
        negritas = re.findall(r"\*\*(.+?)\*\*", canon)
        if negritas:
            ajenas = [n for n in negritas if n not in m["catalogo"]]
            if ajenas:
                malas.append("%s: %s" % (fila[0], ", ".join(ajenas)))
        elif "no es un concepto" not in canon:
            malas.append("%s: %s" % (fila[0], canon))
    t.vacio("E-07 cada fila nombra conceptos del documento o dice no es un concepto", malas)


def test_e08_el_host_no_es_claude_code(t):
    """E-08 — no hay un `### Claude Code`; existe `### Host`, External, con sus seis papeles."""
    m = _modelo()
    t.vacio("E-08 no hay un ### Claude Code",
            [l for l in m["texto"].splitlines() if re.fullmatch(r"###\s+Claude Code\s*", l)])
    t.verdadero("E-08 Claude Code no es un concepto del catalogo", "Claude Code" not in m["catalogo"])
    host = m["campos"].get("Host") or {}
    t.verdadero("E-08 existe ### Host", "Host" in m["campos"])
    t.igual("E-08 Host se clasifica External", "External", _valor(host.get("Clasificación")))
    que_es = host.get("Qué es") or ""
    t.igual("E-08 Host nombra seis papeles", 6, len(re.findall(r"(?m)^\d+\.\s", que_es)))
    for papel in ("hooks", "UI", "agentes", "herramientas", "transcripción", "modelo"):
        t.contiene("E-08 Host nombra el papel de %s" % papel, papel, que_es)


def _items(lineas, patron=r"^- "):
    """Los items de primer nivel de una lista, con sus lineas de continuacion."""
    salida = []
    for linea in lineas:
        if re.match(patron, linea):
            salida.append(linea)
        elif salida and linea.strip() and linea[:1] in (" ", "\t"):
            # Con sangria sigue al item, aunque venga despues de una linea en blanco.
            salida[-1] += " " + linea.strip()
    return salida


def _limite_de_la_spec():
    lineas = _seccion(_texto(SPEC), "10.1 El límite de la ejecución", nivel=3)
    existe, no_existe, actual = [], [], None
    for linea in lineas:
        if linea.startswith("**Lo que existe en 0.29.0:**"):
            actual = existe
        elif linea.startswith("**Lo que no existe:**"):
            actual = no_existe
        elif linea.startswith("**Lo que este cambio deja fijado"):
            actual = None
        elif actual is not None:
            actual.append(linea)
    return _items(existe), _items(no_existe)


ANCLAS_EXISTE = ("READY_FOR_EXECUTION", "PENDING", "executionOrder", "ModelPolicy",
                 "TASK_STARTED", "agentResult", "maxRetries", "refutación",
                 "revisión automática de fuentes")
ANCLAS_NO_EXISTE = ("`Execution`", "ExecutionRequest", "posterior a `READY_FOR_EXECUTION`",
                    "ejecutor", "estado de corrida persistido", "PENDING → RUNNING → terminal",
                    "reintento", "cliente de modelo", "`--unidad`")


def test_e09_el_limite_de_la_ejecucion(t):
    """E-09 — `## El límite de la ejecución` tiene, como items, lo que existe y lo que no de 10.1,
    los dos invariantes y las tres preguntas."""
    m = _modelo()
    limite = _seccion(m["texto"], "El límite de la ejecución")
    partes = dict(_apartados(limite))
    for titulo in ("Lo que existe en 0.29", "Lo que no existe",
                   "Lo que queda fijado para la próxima Task"):
        t.verdadero("E-09 tiene el apartado %s" % titulo, titulo in partes)
    existe_spec, no_existe_spec = _limite_de_la_spec()
    existe = _items(partes.get("Lo que existe en 0.29", []))
    no_existe = _items(partes.get("Lo que no existe", []))
    t.verdadero("E-09 la spec trae los items de 10.1", existe_spec and no_existe_spec)
    t.igual("E-09 lo que existe: tantos items como en 10.1", len(existe_spec), len(existe))
    t.igual("E-09 lo que no existe: tantos items como en 10.1", len(no_existe_spec), len(no_existe))
    for nombre, anclas, items in (("existe", ANCLAS_EXISTE, existe),
                                  ("no existe", ANCLAS_NO_EXISTE, no_existe)):
        for ancla in anclas:
            t.verdadero("E-09 lo que %s nombra %s" % (nombre, ancla),
                        any(ancla in i for i in items))
    fijado = partes.get("Lo que queda fijado para la próxima Task", [])
    numerados = [l for l in fijado if re.match(r"^\d+\.\s", l)]
    t.igual("E-09 dos invariantes y tres preguntas", 5, len(numerados))
    texto = " ".join(fijado)
    for frase in ("La contabilidad no es estado de ejecución",
                  "El estado del Plan se deriva del contenido del Plan",
                  "Dónde vive el estado de una ejecución",
                  "Qué forma tiene lo que vuelve de un agente",
                  "contrato de salida"):
        t.contiene("E-09 lo fijado dice: %s" % frase, frase, texto)


VEREDICTOS_SDD = ("sostenido", "contradicho", "leído", "sin sustento")


def test_e10_los_veredictos_sdd_son_de_la_fabrica(t):
    """E-10 — sostenido, contradicho, leido y sin sustento figuran como de la fabrica, fuera del
    producto, y separados de RefutationVerdict."""
    m = _modelo()
    fuera = "\n".join(_seccion(m["texto"], "Fuera del producto"))
    for v in VEREDICTOS_SDD:
        t.contiene("E-10 Fuera del producto nombra %s" % v, v, fuera)
    t.contiene("E-10 y dice que son de la fabrica", "fábrica", fuera)
    t.contiene("E-10 y los separa de RefutationVerdict", "RefutationVerdict", fuera)
    ciclo = (m["campos"].get("RefutationVerdict") or {}).get("Ciclo y estados") or ""
    t.verdadero("E-10 RefutationVerdict tiene sus propios valores", "cumple" in ciclo)
    for v in VEREDICTOS_SDD:
        t.no_contiene("E-10 %s no es un valor de RefutationVerdict" % v, v, ciclo)
        t.verdadero("E-10 %s no es un concepto del catalogo" % v,
                    v not in [c.lower() for c in m["catalogo"]])


def test_e11_el_readme_enlaza_el_documento(t):
    """E-11 — README.md enlaza docs/dominio/modelo-canonico.md."""
    t.verdadero("E-11 README.md enlaza el documento canonico",
                re.search(r"\]\(docs/dominio/modelo-canonico\.md\)", _texto(RAIZ / "README.md")))


# -- E-12: el ADR -----------------------------------------------------------------------------

DECISIONES = (("1.", ("contextos",) + tuple(NUEVE)),
              ("2.", ("Task", "TaskKey")),
              ("3.", ("Host",)),
              ("4.", ("Execution", "límite reservado")),
              ("5.", ("GuardrailCheck", "ControlCheck", "CheckSpecification")),
              ("6.", ("schema_version", "orchestration-plan/2.0")))


def test_e12_el_adr_registra_las_seis_decisiones(t):
    """E-12 — docs/adr/0013-modelo-de-dominio-canonico.md existe, aceptado, con las seis
    decisiones de D14."""
    t.verdadero("E-12 existe el ADR", ADR.is_file())
    texto = _texto(ADR) if ADR.is_file() else ""
    frente = re.match(r"^---\n(.*?)\n---\n", texto.replace("\r\n", "\n"), re.S)
    t.verdadero("E-12 tiene frontmatter", frente)
    t.contiene("E-12 estado: aceptada", "estado: aceptada", frente.group(1) if frente else "")
    decision = _apartados(_seccion(texto, "Decisión"))
    t.igual("E-12 la Decision tiene seis apartados numerados",
            ["1.", "2.", "3.", "4.", "5.", "6."], [a.split(" ", 1)[0] for a, _ in decision])
    for (numero, claves), (titulo, lineas) in zip(DECISIONES, decision):
        cuerpo = titulo + "\n" + "\n".join(lineas)
        for clave in claves:
            t.contiene("E-12 la decision %s nombra %s" % (numero, clave), clave, cuerpo)


# -- E-13 y E-14: el contrato del plan --------------------------------------------------------

def _esquema_plan():
    return _leer_json(SCHEMA_PLAN)


def _armar(propuesta=None, config=None):
    return orq_plan.armar(propuesta or _propuesta([_unidad("analizar")]), _contexto(), REGISTRO,
                          config or {}, "0.30.0", ".claude/contextos/%s.json" % CLAVE)


def test_e13_el_plan_es_orchestration_plan_2_0(t):
    """E-13 — el schema se identifica como orchestration-plan/2.0 en $id y en el enum de
    meta.schema_version, que no acepta otro valor; el status del plan es exactamente los tres."""
    esquema = _esquema_plan()
    t.igual("E-13 $id", "orchestration-plan/2.0", esquema.get("$id"))
    enum = esquema["properties"]["meta"]["properties"]["schema_version"].get("enum")
    t.igual("E-13 el enum de meta.schema_version es solo orchestration-plan/2.0",
            ["orchestration-plan/2.0"], enum)
    ARMADOR.controlar_soporte(esquema)
    documento = _armar()
    t.igual("E-13 un plan armado valida", [], ARMADOR.validar(documento, esquema))
    for otra in ("orchestration-plan/1.0", "orchestration-plan/2.1", ""):
        viejo = json.loads(json.dumps(documento))
        viejo["meta"]["schema_version"] = otra
        t.verdadero("E-13 meta.schema_version no acepta `%s`" % otra,
                    any("schema_version" in e for e in ARMADOR.validar(viejo, esquema)))
    estados = esquema["properties"]["status"].get("enum") or []
    t.igual("E-13 el status del plan es exactamente los tres", sorted(ESTADOS_PLAN), sorted(estados))
    t.igual("E-13 sin repetidos", len(set(estados)), len(estados))


def test_e14_el_status_de_una_workunit(t):
    """E-14 — el status de una WorkUnit es exactamente PENDING, BLOCKED y
    WAITING_FOR_HUMAN_APPROVAL, y la descripcion define PENDING."""
    unidad = _esquema_plan()["properties"]["workUnits"]["items"]["properties"]["status"]
    estados = unidad.get("enum") or []
    t.igual("E-14 el status de la unidad es exactamente los tres", sorted(ESTADOS_UNIDAD),
            sorted(estados))
    t.igual("E-14 sin repetidos", len(set(estados)), len(estados))
    descripcion = unidad.get("description") or ""
    t.contiene("E-14 la descripcion define PENDING", "PENDING: planificada y sin nada que la frene",
               descripcion)


# -- E-15 y E-21: los documentos que se escriben ----------------------------------------------

TIPOS_DE_UNIDAD = {
    "lista": {"capacidades": ("repository.read",)},
    "hueco": {"capacidades": ("no.existe",)},
    "cara": {"capacidades": ("repository.read",), "senales": CARA},
    "cara-y-hueco": {"capacidades": ("no.existe",), "senales": CARA},
}
CONJUNTOS = (("lista",), ("hueco",), ("cara",), ("cara-y-hueco",), ("lista", "hueco"),
             ("lista", "cara"), ("hueco", "cara"), ("cara", "cara"), ("lista", "cara-y-hueco"))
PRESUPUESTOS = (("sin presupuesto premium", None),
                ("con una llamada premium", {"consumptionPolicy": {
                    "sessionBudget": {"premiumCallsAllowed": 1}}}))

_COMBINACIONES = []


def _propuesta_de(conjunto):
    return _propuesta([_unidad("u%d-%s" % (n, tipo), **TIPOS_DE_UNIDAD[tipo])
                       for n, tipo in enumerate(conjunto, 1)])


def _combinaciones():
    """[(rotulo, codigo, stderr, documento escrito o None)]: `plan --propuesta` y
    `--replanificar` sobre cada combinacion de huecos, aprobaciones y unidades bloqueadas."""
    if _COMBINACIONES:
        return _COMBINACIONES
    for nombre, config in PRESUPUESTOS:
        for i, conjunto in enumerate(CONJUNTOS):
            siguiente = CONJUNTOS[(i + 1) % len(CONJUNTOS)]
            proy = _proyecto(propuestas=[_propuesta_de(conjunto), _propuesta_de(siguiente)],
                             config=config)
            rotulo = "%s, %s" % ("+".join(conjunto), nombre)
            for accion, argv in (("plan --propuesta", ["--propuesta", proy / "prop-1.json"]),
                                 ("--replanificar a " + "+".join(siguiente),
                                  ["--replanificar", proy / "prop-2.json", "--motivo", "cambia"])):
                codigo, _, error = _cli(["plan", CLAVE, "--proyecto", proy] + argv)
                doc = _leer_json(_plan_de(proy)) if codigo == 0 and _plan_de(proy).is_file() else None
                _COMBINACIONES.append(("%s, %s" % (rotulo, accion), codigo, error, doc))
    return _COMBINACIONES


def test_e15_ningun_documento_escrito_tiene_un_estado_que_salio(t):
    """E-15 — ningun documento que escriben `plan --propuesta` o `--replanificar`, sobre las
    combinaciones de E-21, tiene un status fuera de los conjuntos de E-13 y E-14."""
    for rotulo, codigo, error, doc in _combinaciones():
        t.igual("E-15 %s: se escribe" % rotulo, 0, codigo)
        if doc is None:
            continue
        t.verdadero("E-15 %s: el status del plan es uno de los tres" % rotulo,
                    doc.get("status") in ESTADOS_PLAN)
        t.vacio("E-15 %s: el status de cada unidad es uno de los tres" % rotulo,
                [u.get("status") for u in doc.get("workUnits") or []
                 if u.get("status") not in ESTADOS_UNIDAD])


def test_e21_el_estado_del_plan_se_deriva_del_contenido(t):
    """E-21 — sobre las combinaciones de huecos, aprobaciones y unidades bloqueadas, ningun plan
    queda en READY_FOR_EXECUTION con un hueco, una aprobacion PENDING o una unidad que no este en
    PENDING. Y al reves: sin nada de eso, esta listo."""
    vistos = set()
    for rotulo, codigo, _, doc in _combinaciones():
        if doc is None:
            t.igual("E-21 %s: se escribe" % rotulo, 0, codigo)
            continue
        vistos.add(doc["status"])
        frenos = ([("hueco", h.get("capability")) for h in doc.get("capabilityGaps") or []]
                  + [("aprobacion", a.get("workUnit")) for a in doc.get("humanApprovals") or []
                     if a.get("status") == "PENDING"]
                  + [("unidad", u.get("id")) for u in doc.get("workUnits") or []
                     if u.get("status") != "PENDING"])
        if doc["status"] == "READY_FOR_EXECUTION":
            t.vacio("E-21 %s: READY_FOR_EXECUTION sin huecos, aprobaciones ni unidades frenadas"
                    % rotulo, frenos)
        else:
            t.verdadero("E-21 %s: %s porque algo lo frena" % (rotulo, doc["status"]), frenos)
    for estado in ESTADOS_PLAN:
        t.verdadero("E-21 las combinaciones llegan a %s" % estado, estado in vistos)


# -- E-16, E-16b y E-16c: la regla de lectura de un plan guardado -----------------------------

PROPUESTA_E16 = _propuesta([_unidad("wu-1"),
                            _unidad("wu-2", dominio="security", dependencias=["wu-1"])],
                           dominios=("backend", "security"))
PROPUESTA_E16_NUEVA = _propuesta([_unidad("wu-1"),
                                  _unidad("wu-2", dominio="security", dependencias=["wu-1"]),
                                  _unidad("wu-3", dependencias=["wu-2"])],
                                 dominios=("backend", "security"))
SCOPE_E16 = {"schema_version": "refutation-scope/1.0",
             "workUnits": {wu: [{"scopeId": "s", "source": "workUnitFiles",
                                 "paths": ["src/sesion.py"]}] for wu in ("wu-1", "wu-2", "wu-3")}}

# Lo que la compuerta normativa puede escribir antes de que se lea el plan, por su propio
# contrato (spec, E-16b): `.claude/runtime/knowledge-refresh.json` (auto_refresh.py),
# `.claude/harness.fuentes.json` (auto_refresh.py) y los originales descargados en
# `.claude/conocimiento/fuentes/` (dev-harness.py). No dependen del plan y el rechazo no los
# deshace, asi que no entran en las huellas de "no crea ni modifica". Rutas relativas a .claude/.
DE_LA_COMPUERTA = ("runtime/knowledge-refresh.json", "harness.fuentes.json", "conocimiento/fuentes")

_E16 = {}


def _proyecto_e16():
    """(proyecto con el plan 1.0 que escribio el CLI de 4c6f0f3 y un scope.json, None) o
    (None, motivo). Se arma una vez; cada escenario trabaja sobre una copia."""
    if "r" in _E16:
        return _E16["r"]
    bin_base, motivo = _bin_base()
    if bin_base is None:
        _E16["r"] = (None, motivo)
        return _E16["r"]
    proy = _proyecto(propuestas=[PROPUESTA_E16, PROPUESTA_E16_NUEVA], git=True)
    _json(proy / ".claude" / "refutaciones" / CLAVE / "scope.json", SCOPE_E16)
    codigo, _, error = _cli_de(bin_base, proy, "plan", CLAVE, "--propuesta", proy / "prop-1.json")
    if codigo != 0 or not _plan_de(proy).is_file():
        _E16["r"] = (None, "el CLI de %s no escribio el plan (%s): %s" % (BASE, codigo, error[-400:]))
    else:
        _E16["r"] = (proy, None)
    return _E16["r"]


def _unidades_en(proy, clave=CLAVE):
    carpeta = Path(proy) / ".claude" / "refutaciones" / clave / "units"
    return [_leer_json(p) for p in sorted(carpeta.glob("*.json"))] if carpeta.is_dir() else []


def _sin(doc, *claves):
    return {k: v for k, v in doc.items() if k not in claves}


def _compilado_e16():
    """{"base": unidades de 4c6f0f3, "nuevo": las de este codigo, codigos, plan antes/despues}
    de `refute --compile` sobre dos copias del proyecto de E-16, o None si no hay base."""
    if "compilado" in _E16:
        return _E16["compilado"]
    proy, _ = _proyecto_e16()
    if proy is None:
        _E16["compilado"] = None
        return None
    bin_base, _ = _bin_base()
    p_base, p_nuevo = _copia(proy), _copia(proy)
    antes = _bytes(_plan_de(p_nuevo))
    cb, _, eb = _cli_de(bin_base, p_base, "refute", CLAVE, "--compile")
    cn, _, en = _cli_de(BIN, p_nuevo, "refute", CLAVE, "--compile")
    _E16["compilado"] = {"base": _unidades_en(p_base), "nuevo": _unidades_en(p_nuevo),
                         "codigos": (cb, cn), "errores": (eb, en), "antes": antes,
                         "despues": _bytes(_plan_de(p_nuevo)), "proyecto": p_nuevo}
    return _E16["compilado"]


def test_e16_un_1_0_de_4c6f0f3_se_acepta_y_se_migra_al_escribirlo(t):
    """E-16 — un plan escrito por el codigo de 4c6f0f3 es un 1.0 con estados que existen en 2.0.
    `refute --compile` lo lee sin regenerarlo y compila las mismas unidades que 4c6f0f3;
    `--replanificar` escribe un 2.0 con plan_version + 1 y la historia completa. Tal cual, no
    valida contra el schema 2.0."""
    proy, motivo = _proyecto_e16()
    if proy is None:
        _sin_base(t, "E-16", motivo)
        return
    plan = _leer_json(_plan_de(proy))
    esquema = _esquema_plan()
    t.igual("E-16 el plan de 4c6f0f3 es un 1.0", "orchestration-plan/1.0",
            plan["meta"]["schema_version"])
    t.verdadero("E-16 con estados que existen en 2.0",
                plan["status"] in ESTADOS_PLAN
                and all(u["status"] in ESTADOS_UNIDAD for u in plan["workUnits"]))
    t.verdadero("E-16 tal cual, con 1.0, no valida contra el schema 2.0",
                any("schema_version" in e for e in ARMADOR.validar(plan, esquema)))
    como_2 = json.loads(json.dumps(plan))
    como_2["meta"]["schema_version"] = "orchestration-plan/2.0"
    t.igual("E-16 con la cadena 2.0 valida: es un 2.0 salvo la version", [],
            ARMADOR.validar(como_2, esquema))

    c = _compilado_e16()
    t.igual("E-16 refute --compile de 4c6f0f3 sale 0", 0, c["codigos"][0])
    t.igual("E-16 refute --compile lee el 1.0 y sale 0", 0, c["codigos"][1])
    t.igual("E-16 refute --compile no regenera el plan: queda igual, byte a byte",
            c["antes"], c["despues"])
    t.verdadero("E-16 compila unidades", len(c["nuevo"]) > 0)
    clave_de = lambda u: (u["refutationUnitId"], u["workUnitId"], u["standard"]["ruleKey"])
    t.igual("E-16 los mismos ids, WorkUnits y reglas que 4c6f0f3",
            [clave_de(u) for u in c["base"]], [clave_de(u) for u in c["nuevo"]])
    t.igual("E-16 la misma unidad, salvo declaredChecks (E-31)",
            [_sin(u, "declaredChecks") for u in c["base"]],
            [_sin(u, "declaredChecks") for u in c["nuevo"]])

    p = c["proyecto"]
    codigo, _, error = _cli_de(BIN, p, "plan", CLAVE, "--replanificar", p / "prop-2.json",
                               "--motivo", "suma una unidad")
    t.igual("E-16 --replanificar lee el 1.0 y sale 0", 0, codigo)
    nuevo = _leer_json(_plan_de(p))
    t.igual("E-16 --replanificar lo escribe como orchestration-plan/2.0", "orchestration-plan/2.0",
            nuevo["meta"]["schema_version"])
    t.igual("E-16 con plan_version + 1", plan["meta"]["plan_version"] + 1,
            nuevo["meta"]["plan_version"])
    t.igual("E-16 con la historia anterior completa", plan["planHistory"],
            nuevo["planHistory"][:len(plan["planHistory"])])
    t.igual("E-16 y una entrada mas", len(plan["planHistory"]) + 1, len(nuevo["planHistory"]))
    t.igual("E-16 el 2.0 que escribe valida", [], ARMADOR.validar(nuevo, esquema))


VALIDAR_CON_LA_BASE = (
    "import importlib.util, json, sys\n"
    "armador, schema, docs = sys.argv[1:4]\n"
    "spec = importlib.util.spec_from_file_location('armador_base_dm64', armador)\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(m)\n"
    "with open(schema, encoding='utf-8') as f:\n"
    "    esquema = json.load(f)\n"
    "m.controlar_soporte(esquema)\n"
    "with open(docs, encoding='utf-8') as f:\n"
    "    documentos = json.load(f)\n"
    "sys.stdout.write(json.dumps([m.validar(d, esquema) for d in documentos]))\n")


def _validar_con_la_base(documentos):
    """Los errores de cada documento contra el schema de 4c6f0f3, con el validador de 4c6f0f3,
    en un proceso aparte. None si no hay base."""
    base, _ = _base()
    if base is None:
        return None
    ruta = _tmp("dm64-docs-") / "docs.json"
    _json(ruta, documentos)
    codigo, salida, error = _proceso([sys.executable, "-c", VALIDAR_CON_LA_BASE,
                                      str(base / "comun" / "bin" / "contexto-armar.py"),
                                      str(base / "comun" / "schemas" / "orchestration-plan.schema.json"),
                                      str(ruta)])
    return json.loads(salida) if codigo == 0 else ["el validador de la base fallo: " + error]


def _veredicto_cumple(u):
    return {"schema_version": R.VERSION_VEREDICTO, "refutationUnitId": u["refutationUnitId"],
            "workUnitId": u["workUnitId"], "ruleKey": u["standard"]["ruleKey"],
            "verdict": "cumple", "reason": None,
            "citation": {"skillId": u["skillId"], "locator": "ES0902 §6, pág. 12"},
            "evidence": [{"path": u["evidenceScope"]["paths"][0], "line": 1,
                          "observed": "TIMEOUT = 900"}],
            "needed": None, "cacheKey": u["cacheKey"],
            "evidenceFingerprint": u["evidenceFingerprint"], "repoRevision": u["repoRevision"]}


def _preparar_rechazo():
    """(proyecto, plan 1.0 de 4c6f0f3, None) o (None, None, motivo). Una copia del proyecto de
    E-16 con la refutacion de la tarea ya compilada por este codigo, un veredicto registrado
    -deja verdicts/ y una entrada en cache/- y una unidad vieja en units/ que una compilacion
    borraria: asi "no crea, no modifica ni borra" tiene algo que crear, modificar y borrar."""
    proy, motivo = _proyecto_e16()
    if proy is None:
        return None, None, motivo
    plan = _leer_json(_plan_de(proy))
    p = _copia(proy)
    codigo, _, error = _cli(["refute", CLAVE, "--compile", "--proyecto", p])
    if codigo != 0:
        return None, None, "refute --compile no preparo la refutacion: " + error[-400:]
    pendiente = [u for u in _unidades_en(p) if u["status"] == "PENDING_SEMANTIC"]
    if not pendiente:
        return None, None, "la refutacion no dejo ninguna unidad pendiente para registrar"
    R.registrar(str(p), CLAVE, json.dumps(_veredicto_cumple(pendiente[0])))
    vieja = dict(_unidades_en(p)[0], refutationUnitId="REF-999")
    _json(p / ".claude" / "refutaciones" / CLAVE / "units" / "REF-999.json", vieja)
    return p, plan, None


def _artefactos(p):
    claude = Path(p) / ".claude"
    return {"plan": _bytes(_plan_de(p)),
            "refutacion": _arbol(claude / "refutaciones" / CLAVE),
            "cache": _arbol(claude / "refutaciones" / "cache"),
            "resto": _arbol(claude, excluir=DE_LA_COMPUERTA + ("planes", "refutaciones"))}


def _probar_rechazo(t, eid, p, rotulo, documento, agujas, regenerar):
    """Escribe `documento` como el plan guardado y corre los dos consumidores. Cada uno sale con
    2, nombra lo que dicen `agujas` y no crea, modifica ni borra el plan, la refutacion de la
    tarea ni la cache. Lo que escriba la compuerta normativa no cuenta (DE_LA_COMPUERTA)."""
    _escribir(_plan_de(p), json.dumps(documento, ensure_ascii=False, indent=2) + "\n")
    for consumidor, argv in (("refute --compile", ["refute", CLAVE, "--compile"]),
                             ("--replanificar", ["plan", CLAVE, "--replanificar",
                                                 p / "prop-2.json", "--motivo", "rehacerlo"])):
        antes = _artefactos(p)
        codigo, _, error = _cli(argv + ["--proyecto", p])
        nombre = "%s %s, %s" % (eid, rotulo, consumidor)
        t.igual("%s: sale con 2" % nombre, 2, codigo)
        for aguja in agujas:
            t.contiene("%s: el mensaje nombra %s" % (nombre, aguja), aguja, error)
        if regenerar:
            t.verdadero("%s: el mensaje dice que se regenera con plan --propuesta" % nombre,
                        re.search(r"plan \S+ --propuesta", error))
        despues = _artefactos(p)
        t.igual("%s: .claude/planes/<KEY>.json queda igual, byte a byte" % nombre,
                antes["plan"], despues["plan"])
        t.vacio("%s: .claude/refutaciones/<KEY>/ queda igual" % nombre,
                _diferencias(antes["refutacion"], despues["refutacion"]))
        t.vacio("%s: .claude/refutaciones/cache/ queda igual" % nombre,
                _diferencias(antes["cache"], despues["cache"]))
        t.vacio("%s: fuera de lo que escribe la compuerta, nada mas cambia en .claude/" % nombre,
                _diferencias(antes["resto"], despues["resto"]))


def _constantes(ruta):
    try:
        arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    return [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)]


def _py_de(carpeta):
    return sorted(p for p in Path(carpeta).rglob("*.py") if "__pycache__" not in p.parts)


def test_e16b_un_1_0_con_un_estado_que_salio_se_rechaza(t):
    """E-16b — un 1.0 escrito a mano, valido contra el schema de 4c6f0f3 e imposible de producir,
    se rechaza: uno con el plan DELEGATING y otro con una unidad READY. El schema 2.0 no los
    valida; los dos consumidores salen con 2 nombrando campo y valor y piden regenerarlo; nada
    los migra; y el rechazo no toca el plan, la refutacion de la tarea ni la cache."""
    p, plan, motivo = _preparar_rechazo()
    if p is None:
        _sin_base(t, "E-16b", motivo)
        return
    delegando = json.loads(json.dumps(plan))
    delegando["status"] = "DELEGATING"
    lista = json.loads(json.dumps(plan))
    lista["workUnits"][0]["status"] = "READY"
    errores = _validar_con_la_base([delegando, lista])
    t.igual("E-16b los dos validan contra el schema de 4c6f0f3, con su validador", [[], []], errores)
    esquema = _esquema_plan()
    t.verdadero("E-16b el schema 2.0 no valida el plan DELEGATING",
                any("DELEGATING" in e for e in ARMADOR.validar(delegando, esquema)))
    t.verdadero("E-16b el schema 2.0 no valida la unidad READY",
                any("READY" in e for e in ARMADOR.validar(lista, esquema)))
    _probar_rechazo(t, "E-16b", p, "plan DELEGATING", delegando, ("status", "DELEGATING"), True)
    _probar_rechazo(t, "E-16b", p, "unidad READY", lista, ("workUnits[0].status", "READY"), True)
    t.vacio("E-16b ningun codigo de bin/ convierte DELEGATING ni READY en otro estado",
            ["%s: %s" % (p_.relative_to(BIN).as_posix(), c) for p_ in _py_de(BIN)
             for c in _constantes(p_) if c in ("DELEGATING", "READY")])


def test_e16c_otra_version_o_ninguna_se_rechaza(t):
    """E-16c — un plan guardado con otra schema_version, o sin ella, lo rechazan los dos
    consumidores con 2, nombrando la version, y sin tocar los artefactos de E-16b."""
    p, plan, motivo = _preparar_rechazo()
    if p is None:
        _sin_base(t, "E-16c", motivo)
        return
    otra = json.loads(json.dumps(plan))
    otra["meta"]["schema_version"] = "orchestration-plan/3.0"
    sin_version = json.loads(json.dumps(plan))
    del sin_version["meta"]["schema_version"]
    _probar_rechazo(t, "E-16c", p, "orchestration-plan/3.0", otra, ("orchestration-plan/3.0",), False)
    _probar_rechazo(t, "E-16c", p, "sin schema_version", sin_version, ("meta.schema_version",), False)


# -- E-17 a E-20: el productor y las dos reglas de la propuesta -------------------------------

PROPUESTAS_E17 = (
    ("una unidad", _propuesta([_unidad("analizar")])),
    ("tres dominios, hueco, aprobacion y senales", _propuesta(
        [_unidad("leer", senales=["novelty"]),
         _unidad("asegurar", dominio="security", capacidades=["no.existe"],
                 dependencias=["leer"], senales=list(CARA)),
         _unidad("pantalla", dominio="frontend", capacidades=[],
                 normativeSignals={"citizenFacing": True}, applicablePolicies=["accesible"])],
        dominios=("backend", "security", "frontend"), policies=["una politica"])),
)


def _normalizado_e17(doc):
    doc = json.loads(json.dumps(doc))
    doc["meta"].pop("generated_at", None)
    doc["meta"].pop("schema_version", None)
    for h in doc.get("planHistory") or []:
        h.pop("timestamp", None)
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)


def test_e17_el_productor_escribe_lo_mismo_que_4c6f0f3(t):
    """E-17 — con la misma propuesta y el mismo TaskContext, el codigo nuevo escribe el mismo
    documento que 4c6f0f3, salvo generated_at, planHistory[].timestamp y schema_version, que pasa
    de orchestration-plan/1.0 a orchestration-plan/2.0."""
    bin_base, motivo = _bin_base()
    if bin_base is None:
        _sin_base(t, "E-17", motivo)
        return
    for rotulo, propuesta in PROPUESTAS_E17:
        p_base, p_nuevo = _proyecto(propuestas=[propuesta]), _proyecto(propuestas=[propuesta])
        cb, _, eb = _cli_de(bin_base, p_base, "plan", CLAVE, "--propuesta", p_base / "prop-1.json")
        cn, _, en = _cli_de(BIN, p_nuevo, "plan", CLAVE, "--propuesta", p_nuevo / "prop-1.json")
        t.igual("E-17 %s: 4c6f0f3 lo escribe" % rotulo, 0, cb)
        t.igual("E-17 %s: este codigo lo escribe" % rotulo, 0, cn)
        if cb != 0 or cn != 0:
            continue
        viejo, nuevo = _leer_json(_plan_de(p_base)), _leer_json(_plan_de(p_nuevo))
        t.igual("E-17 %s: 4c6f0f3 escribe orchestration-plan/1.0" % rotulo,
                "orchestration-plan/1.0", viejo["meta"]["schema_version"])
        t.igual("E-17 %s: este codigo escribe orchestration-plan/2.0" % rotulo,
                "orchestration-plan/2.0", nuevo["meta"]["schema_version"])
        t.igual("E-17 %s: el mismo documento, salvo generated_at, timestamps y schema_version"
                % rotulo, _normalizado_e17(viejo), _normalizado_e17(nuevo))


def _plan_cli(proy, *argv):
    return _cli(["plan", CLAVE, "--proyecto", proy] + list(argv))


PROPUESTA_BUENA = _propuesta([_unidad("analizar")])
PROPUESTA_REPETIDA = _propuesta([_unidad("repetida"), _unidad("otra"),
                                 _unidad("repetida", dependencias=["otra"])])
PROPUESTA_AJENA = _propuesta([_unidad("analizar"), _unidad("pantalla", dominio="frontend")])


def test_e18_ids_repetidos(t):
    """E-18 — una propuesta con dos WorkUnits del mismo id sale con 2, el error nombra el id, y
    .claude/planes/<KEY>.json no se escribe ni se modifica."""
    levanto = ""
    try:
        _armar(PROPUESTA_REPETIDA)
    except orq_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-18 armar levanta PlanInvalido y nombra el id", "repetida", levanto)
    proy = _proyecto(propuestas=[PROPUESTA_REPETIDA, PROPUESTA_BUENA])
    codigo, _, error = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-18 sale con 2", 2, codigo)
    t.contiene("E-18 el error nombra el id", "'repetida'", error)
    t.verdadero("E-18 el plan no se escribe", not _plan_de(proy).exists())
    codigo, _, _ = _plan_cli(proy, "--propuesta", proy / "prop-2.json")
    antes = _bytes(_plan_de(proy))
    codigo2, _, _ = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-18 sobre un plan que ya existe tambien sale con 2", [0, 2], [codigo, codigo2])
    t.igual("E-18 y el plan que existia no se modifica", antes, _bytes(_plan_de(proy)))


# Los PlanInvalido que ya existian en 4c6f0f3, y los dos rechazos que agrega este cambio.
DE_ANTES_E18B = (
    ("un ciclo de dependencias", _propuesta([_unidad("a", dependencias=["b"]),
                                             _unidad("b", dependencias=["a"])])),
    ("una dependencia rota", _propuesta([_unidad("a", dependencias=["no-existe"])])),
    ("una propuesta sin unidades", _propuesta([])),
)
NUEVOS_E18B = (("un id repetido", PROPUESTA_REPETIDA, "'repetida'"),
               ("un dominio fuera del plan", PROPUESTA_AJENA, "'frontend'"))


def _plan_en_proceso(bin_dir, propuesta, previo):
    """`plan --propuesta` del `bin_dir` dado, en su propio proceso, como lo corre una persona.
    Con `previo`, sobre un plan bueno que ese mismo codigo escribio antes. (codigo, stderr, plan
    antes, plan despues); codigo None si el plan previo no se pudo escribir."""
    proy = _proyecto(propuestas=[propuesta, PROPUESTA_BUENA])
    if previo:
        codigo, _, error = _cli_de(bin_dir, proy, "plan", CLAVE, "--propuesta", proy / "prop-2.json")
        if codigo != 0 or not _plan_de(proy).is_file():
            return None, "el plan previo no se escribio (%s): %s" % (codigo, error[-300:]), None, None
    antes = _bytes(_plan_de(proy))
    codigo, _, error = _cli_de(bin_dir, proy, "plan", CLAVE, "--propuesta", proy / "prop-1.json")
    return codigo, error, antes, _bytes(_plan_de(proy))


def test_e18b_solo_los_rechazos_nuevos_salen_con_2(t):
    """E-18b — solo los rechazos que agrega este cambio salen con 2 (PlanRechazado): el id
    repetido y el dominio fuera del plan. Los PlanInvalido que ya existian -un ciclo, una
    dependencia rota, una propuesta sin unidades- salen con el mismo codigo que en 4c6f0f3, y
    tampoco escriben el plan: ni lo crean ni modifican el que habia. La regla de lectura, el
    tercer PlanRechazado, sale con 2 en E-16b y E-16c.

    Los dos lados corren en un proceso aparte: un PlanInvalido que `main` no atrapa sale por
    traceback, y en este proceso seria una excepcion, no un codigo."""
    bin_base, motivo = _bin_base()
    if bin_base is None:
        _sin_base(t, "E-18b", motivo)
        return
    for rotulo, propuesta in DE_ANTES_E18B:
        for previo in (False, True):
            donde = "sobre un plan que ya existe" if previo else "sin plan"
            nombre = "E-18b %s, %s" % (rotulo, donde)
            cb, _, _, _ = _plan_en_proceso(bin_base, propuesta, previo)
            cn, _, antes, despues = _plan_en_proceso(BIN, propuesta, previo)
            t.verdadero("%s: 4c6f0f3 no lo aceptaba" % nombre, cb not in (None, 0))
            t.igual("%s: sale con el mismo codigo que en 4c6f0f3" % nombre, cb, cn)
            if previo:
                t.verdadero("%s: el plan que habia estaba" % nombre, antes is not None)
                t.igual("%s: el plan que habia no se modifica" % nombre, antes, despues)
            else:
                t.igual("%s: el plan no se escribe" % nombre, None, despues)
    for rotulo, propuesta, aguja in NUEVOS_E18B:
        for previo in (False, True):
            donde = "sobre un plan que ya existe" if previo else "sin plan"
            nombre = "E-18b %s, %s" % (rotulo, donde)
            cn, en, antes, despues = _plan_en_proceso(BIN, propuesta, previo)
            t.igual("%s: sale con 2" % nombre, 2, cn)
            t.contiene("%s: el error lo nombra" % nombre, aguja, en)
            t.igual("%s: el plan no se escribe ni se modifica" % nombre, antes, despues)
            if not previo:
                cb, _, _, d_base = _plan_en_proceso(bin_base, propuesta, previo)
                t.igual("%s: es un rechazo nuevo, 4c6f0f3 salia 0 y lo escribia" % nombre,
                        [0, True], [cb, d_base is not None])


def test_e19_el_dominio_de_la_unidad_esta_entre_los_del_plan(t):
    """E-19 — una WorkUnit cuyo domain no esta en domains sale con 2, el error nombra el dominio,
    y .claude/planes/<KEY>.json no se crea ni se modifica (la compuerta vale como en E-16b)."""
    levanto = ""
    try:
        _armar(PROPUESTA_AJENA)
    except orq_plan.PlanInvalido as e:
        levanto = str(e)
    t.contiene("E-19 armar levanta PlanInvalido y nombra el dominio", "frontend", levanto)
    proy = _proyecto(propuestas=[PROPUESTA_AJENA, PROPUESTA_BUENA])
    codigo, _, error = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-19 sale con 2", 2, codigo)
    t.contiene("E-19 el error nombra el dominio", "'frontend'", error)
    t.verdadero("E-19 el plan no se crea", not _plan_de(proy).exists())
    codigo, _, _ = _plan_cli(proy, "--propuesta", proy / "prop-2.json")
    antes = _bytes(_plan_de(proy))
    codigo2, _, _ = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-19 sobre un plan que ya existe tambien sale con 2", [0, 2], [codigo, codigo2])
    t.igual("E-19 y el plan que existia no se modifica", antes, _bytes(_plan_de(proy)))


def test_e20_replanificar_con_una_propuesta_rota(t):
    """E-20 — --replanificar con una propuesta que viola E-18 o E-19 falla igual y deja el plan
    anterior intacto, byte a byte."""
    proy = _proyecto(propuestas=[PROPUESTA_BUENA, PROPUESTA_REPETIDA, PROPUESTA_AJENA])
    codigo, _, _ = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-20 el plan anterior se escribe", 0, codigo)
    antes = _bytes(_plan_de(proy))
    for rotulo, n, aguja in (("ids repetidos (E-18)", 2, "'repetida'"),
                             ("unidad de otro dominio (E-19)", 3, "'frontend'")):
        codigo, _, error = _plan_cli(proy, "--replanificar", proy / ("prop-%d.json" % n),
                                     "--motivo", "otra propuesta")
        t.igual("E-20 %s: sale con 2" % rotulo, 2, codigo)
        t.contiene("E-20 %s: el error lo nombra" % rotulo, aguja, error)
        t.igual("E-20 %s: el plan anterior queda intacto, byte a byte" % rotulo, antes,
                _bytes(_plan_de(proy)))


# -- E-22 a E-24: quien escribe y quien lee el plan, el registro y el orquestador -------------

def _arbol_py(ruta):
    return ast.parse(Path(ruta).read_text(encoding="utf-8"))


def _nombre(nodo):
    """`a.b.c` de un Name o un Attribute; '' si es otra cosa."""
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        base = _nombre(nodo.value)
        return base + "." + nodo.attr if base else ""
    return ""


def _funciones(arbol):
    return {n.name: n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}


def _llamadas(nodo):
    return [n for n in ast.walk(nodo) if isinstance(n, ast.Call)]


def _usa(nodo, nombre):
    return any(isinstance(n, ast.Name) and n.id == nombre for n in ast.walk(nodo))


def _lee_status_de(nodo, nombres):
    """Las lecturas `X["status"]` o `X.get("status")` con X en `nombres`."""
    salida = []
    for n in ast.walk(nodo):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id in nombres and isinstance(n.slice, ast.Constant)
                and n.slice.value == "status"):
            salida.append("%s[\"status\"]" % n.value.id)
        if (isinstance(n, ast.Call) and _nombre(n.func).split(".")[-1] == "get"
                and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                and n.func.value.id in nombres and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == "status"):
            salida.append("%s.get(\"status\")" % n.func.value.id)
    return salida


def test_e22_un_solo_escritor_y_una_sola_regla_de_lectura(t):
    """E-22 — plan.escribir es lo unico en bin/ que escribe en .claude/planes/. refute --compile y
    --replanificar leen un plan guardado solo por la regla de lectura de D16, y fuera de ella
    ninguno decide nada por el status del plan."""
    # Quien arma una ruta bajo .claude/planes/: el CLI, que se la pasa a plan.escribir, y la
    # refutacion, que la lee.
    con_planes = sorted(p.relative_to(BIN).as_posix() for p in _py_de(BIN)
                        if "planes" in _constantes(p))
    t.igual("E-22 solo dos modulos de bin/ arman una ruta bajo .claude/planes/",
            ["dev-harness.py", "orquestacion/refutacion.py"], con_planes)
    # En plan.py, el unico que abre un archivo para escribir es `escribir`.
    abren = []
    for nombre, f in _funciones(_arbol_py(BIN / "orquestacion" / "plan.py")).items():
        for c in _llamadas(f):
            modos = [a.value for a in c.args[1:2] if isinstance(a, ast.Constant)]
            modos += [k.value.value for k in c.keywords if k.arg == "mode"
                      and isinstance(k.value, ast.Constant)]
            if _nombre(c.func) in ("open", "io.open") and any("w" in str(m) or "a" in str(m)
                                                             for m in modos):
                abren.append(nombre)
    t.igual("E-22 en plan.py solo escribir abre un archivo para escribir", ["escribir"], abren)
    # El CLI: la ruta del plan va solo a estas llamadas, y se lee solo adentro de aceptar_guardado.
    cli = _arbol_py(CLI)
    planificar = _funciones(cli).get("planificar")
    t.verdadero("E-22 el CLI tiene planificar", planificar is not None)
    destinos, lecturas_sueltas = set(), []
    for c in _llamadas(planificar) if planificar else []:
        if any(_usa(a, "destino") and isinstance(a, ast.Name) for a in c.args):
            destinos.add(_nombre(c.func))
        for a in c.args:
            if (isinstance(a, ast.Call) and _nombre(a.func) == "_json_o_vacio"
                    and any(isinstance(x, ast.Name) and x.id == "destino" for x in a.args)
                    and _nombre(c.func) != "orq_plan.aceptar_guardado"):
                lecturas_sueltas.append(_nombre(c.func))
    t.vacio("E-22 la ruta del plan va solo a escribir, a la regla de lectura y a mostrarlo",
            sorted(destinos - {"os.path.isfile", "orq_plan.escribir", "_json_o_vacio",
                               "mostrar_plan"}))
    t.verdadero("E-22 --replanificar lee el plan anterior por aceptar_guardado",
                any(_nombre(c.func) == "orq_plan.aceptar_guardado" for c in _llamadas(planificar)))
    t.vacio("E-22 el CLI no lee el plan guardado fuera de aceptar_guardado", lecturas_sueltas)
    t.vacio("E-22 en el CLI nadie mira el status del plan guardado",
            _lee_status_de(planificar, {"anterior", "plan"}) if planificar else ["sin planificar"])
    # La refutacion: la ruta del plan solo la usa _leer_plan, que pasa por aceptar_guardado.
    ref = _arbol_py(BIN / "orquestacion" / "refutacion.py")
    funciones = _funciones(ref)
    t.igual("E-22 en la refutacion solo _leer_plan usa la ruta del plan", ["_leer_plan"],
            sorted(n for n, f in funciones.items() if n != "ruta_del_plan"
                   and any(_nombre(c.func) == "ruta_del_plan" for c in _llamadas(f))))
    leer_plan = funciones.get("_leer_plan")
    t.verdadero("E-22 _leer_plan pasa el plan por aceptar_guardado",
                leer_plan is not None and any(_nombre(c.func).endswith("aceptar_guardado")
                                              for c in _llamadas(leer_plan)))
    t.verdadero("E-22 compilar toma el plan de _leer_plan",
                any(_nombre(c.func) == "_leer_plan" for c in _llamadas(funciones["compilar"])))
    t.vacio("E-22 en la refutacion nadie mira el status del plan", _lee_status_de(ref, {"plan"}))


def _registro_de_agentes():
    return [a["id"] for a in _leer_json(REGLAS / "agent-registry.json")["agents"]]


# Las formas afirmativas de lo que la segunda verificacion contradijo en el `### Agent` (E-02):
# que el plan solo asigna, admite o acepta agentes del registro, registrados o declarados, o que
# se limita al registro. `_afirma` descarta las negadas: "no se limita al registro" no cuenta.
_SOLO = r"(?:solo|solamente|unicamente)"
_ASIGNA = r"(?:se\s+)?(?:asign\w*|admit\w*|acept\w*|permit\w*)"
_DEL_REGISTRO = r"(?:a\s+)?(?:los\s+)?agentes\s+(?:del\s+registro|registrad\w*|declarad\w*)"
SOLO_DEL_REGISTRO = re.compile(
    r"\b%s\s+%s\s+%s|\b%s\s+%s\s+%s|\bse\s+limita\s+(?:a\s+los\s+agentes\s+del\s+|al\s+)registro"
    % (_SOLO, _ASIGNA, _DEL_REGISTRO, _ASIGNA, _SOLO, _DEL_REGISTRO))


def test_e23_el_registro_decide_si_un_agente_existe(t):
    """E-23 — un agente con su .md en disco que no esta en el registro da agentExists: false. Las
    descripciones de agents[].exists y agentExists dicen que decide el registro y que el disco
    diagnostica.

    Y el `### Agent` del documento canonico (E-02) dice lo que este plan acaba de hacer: no que el
    plan solo asigna agentes del registro -lo dijo, y la segunda verificacion lo contradijo-, ni
    que rechaza uno desconocido, sino los agentExists y agentValidation que el plan escribio."""
    huerfano = "dev-iniciador-code"
    t.verdadero("E-23 %s tiene su .md en disco" % huerfano,
                (RAIZ / "harnesses" / "desarrollo" / "agents" / (huerfano + ".md")).is_file())
    t.verdadero("E-23 y el registro no lo declara", huerfano not in _registro_de_agentes())
    proy = _proyecto(propuestas=[_propuesta([_unidad("iniciar", assignedAgent=huerfano),
                                             _unidad("analizar")])])
    codigo, _, error = _plan_cli(proy, "--propuesta", proy / "prop-1.json")
    t.igual("E-23 el plan se escribe", 0, codigo)
    unidades = {u["id"]: u for u in (_leer_json(_plan_de(proy))["workUnits"] if codigo == 0 else [])}
    t.igual("E-23 la unidad asignada a %s da agentExists false" % huerfano, False,
            (unidades.get("iniciar") or {}).get("agentExists"))
    t.igual("E-23 la de un agente declarado da true", True,
            (unidades.get("analizar") or {}).get("agentExists"))
    iniciar = unidades.get("iniciar") or {}
    t.igual("E-23 la unidad conserva el assignedAgent %s que pidio la propuesta" % huerfano,
            huerfano, iniciar.get("assignedAgent"))
    t.igual("E-23 la unidad asignada a %s da agentValidation AGENT_NOT_FOUND" % huerfano,
            "AGENT_NOT_FOUND", iniciar.get("agentValidation"))
    esquema = _esquema_plan()
    for rotulo, descripcion in (
            ("agents[].exists", esquema["properties"]["agents"].get("description")),
            ("agentExists", esquema["properties"]["workUnits"]["items"]["properties"]
             ["agentExists"].get("description"))):
        texto = _plano(descripcion)
        t.contiene("E-23 la descripcion de %s dice que decide el registro" % rotulo,
                   "decide el registro", texto)
        t.contiene("E-23 la descripcion de %s dice que el disco diagnostica" % rotulo,
                   "diagnostica", texto)
        t.no_contiene("E-23 la descripcion de %s no dice que decide el disco" % rotulo,
                      "lo decide el disco,", texto)
    # El documento, contra lo que el plan acaba de escribir: las agujas salen de la unidad, no del
    # documento. Si el plan no se escribio, `iniciar` queda vacio y las dos ultimas dan rojo.
    agente = "\n".join(dict(_modelo()["bloques"]).get("Agent") or [])
    t.verdadero("E-02 E-23 el documento canonico tiene la seccion ### Agent", bool(agente.strip()))
    t.vacio("E-02 E-23 la seccion Agent no dice que el plan solo asigna agentes del registro",
            _afirma(SOLO_DEL_REGISTRO, agente))
    t.vacio("E-02 E-23 la seccion Agent no dice que el plan rechaza un agente fuera del registro",
            _afirma_prohibicion(agente))
    t.contiene("E-02 E-23 la seccion Agent nombra el agentExists que escribio el plan",
               "agentExists: %s" % json.dumps(iniciar.get("agentExists")), agente)
    t.contiene("E-02 E-23 la seccion Agent nombra el agentValidation que escribio el plan",
               "agentValidation: %s" % iniciar.get("agentValidation"), agente)


def test_e24_el_orquestador_conoce_las_dos_reglas(t):
    """E-24 — dev-orchestrator.md dice que los ids son unicos, que el dominio de cada unidad tiene
    que estar en domains, y que el plan valida contra orchestration-plan/2.0."""
    texto = _texto(RAIZ / "harnesses" / "desarrollo" / "agents" / "dev-orchestrator.md")
    items = _items(texto.splitlines())
    de_id = [i for i in items if i.startswith("- `id`")]
    de_dominio = [i for i in items if i.startswith("- `domain`")]
    t.verdadero("E-24 el id de una unidad es unico", de_id and "unique" in de_id[0])
    t.verdadero("E-24 el dominio de la unidad tiene que estar en domains",
                de_dominio and "`domains`" in de_dominio[0])
    t.contiene("E-24 el plan valida contra orchestration-plan/2.0", "orchestration-plan/2.0", texto)
    t.no_contiene("E-24 y ya no dice orchestration-plan/1.0", "orchestration-plan/1.0", texto)


# -- E-25 a E-30: la identidad de la Task -----------------------------------------------------

# Claves que no cumplen la TaskKey y que igual se pueden usar como nombre de archivo.
CLAVES_INVALIDAS = ("no-es-clave", "GCBA-12a", "gcba_12", "1GCBA-2", "GCBA-")


def test_e25_plan_con_una_clave_invalida_no_escribe(t):
    """E-25 — `plan` con una clave que no cumple la TaskKey no crea ni modifica nada en
    .claude/planes/, aunque exista un contexto con ese nombre puesto a mano. La compuerta corre
    antes y lo suyo vale como en E-16b: por eso la huella es solo de .claude/planes/."""
    for clave in CLAVES_INVALIDAS:
        proy = _proyecto(propuestas=[PROPUESTA_BUENA])
        _json(proy / ".claude" / "contextos" / (clave + ".json"), _contexto(clave))
        _plan_cli(proy, "--propuesta", proy / "prop-1.json")         # un plan de otra tarea
        planes = proy / ".claude" / "planes"
        antes = _arbol(planes)
        try:
            _cli(["plan", clave, "--proyecto", proy, "--propuesta", proy / "prop-1.json"])
        except orq_plan.PlanInvalido:
            # El plan no valida contra el patron de plan_id: es un PlanInvalido de antes, no un
            # PlanRechazado, y sale como salia en 4c6f0f3, por traceback (E-18b). Lo que cuenta
            # aca es .claude/planes/.
            pass
        t.verdadero("E-25 %s: el contexto puesto a mano estaba" % clave,
                    (proy / ".claude" / "contextos" / (clave + ".json")).is_file())
        t.vacio("E-25 %s: no crea ni modifica nada en .claude/planes/" % clave,
                _diferencias(antes, _arbol(planes)))


def test_e26_contexto_refute_y_seguridad_rechazan_la_clave_antes_de_escribir(t):
    """E-26 — contexto, refute y seguridad, con una clave que no cumple la TaskKey, salen con 2 y
    no crean ni modifican ningun archivo en .claude/: la huella es de todo .claude/.

    Se prueba en dos proyectos. Uno con el Jira falso de 19_contexto.py, que contesta el issue
    para cualquier clave, donde antes se comprueba que los tres comandos SI escriben con una
    clave valida: asi el 2 y el .claude/ intacto salen de la clave y no de que faltara algo para
    escribir. Y uno pelado, nuevo por clave, sin configuracion de integraciones: ahi lo primero
    que hace `comando()` -resolver la configuracion, correr la compuerta- ya deja rastro en
    .claude/, y eso es justo lo que la validacion en `main` evita."""
    for clave in CLAVES_INVALIDAS:
        for argv in (["contexto", clave], ["refute", clave, "--compile"], ["seguridad", clave]):
            pelado = _proyecto()
            antes = _arbol(pelado / ".claude")
            codigo, _, _ = _cli(argv + ["--proyecto", pelado])
            nombre = "E-26 sin integraciones, %s" % " ".join(argv)
            t.igual("%s: sale con 2" % nombre, 2, codigo)
            t.vacio("%s: no crea ni modifica nada en .claude/" % nombre,
                    _diferencias(antes, _arbol(pelado / ".claude")))
    valida = M19.CLAVE
    proy = Path(_proyecto_de_19())
    claude = proy / ".claude"
    jira = M19.Transporte({"/issue/": (200, M19.ISSUE), "/search": (200, M19.FICHA)})
    codigo, _, _ = _cli(["contexto", valida, "--proyecto", proy], jira, M19._Bytes({}))
    t.igual("E-26 control: contexto con una clave valida escribe el contexto",
            [0, True], [codigo, (claude / "contextos" / (valida + ".json")).is_file()])
    _json(proy / "prop.json", PROPUESTA_BUENA)
    _cli(["plan", valida, "--propuesta", proy / "prop.json", "--proyecto", proy])
    codigo, _, _ = _cli(["refute", valida, "--compile", "--proyecto", proy], jira, M19._Bytes({}))
    t.igual("E-26 control: refute --compile con una clave valida escribe la refutacion",
            [0, True], [codigo, (claude / "refutaciones" / valida / "run.json").is_file()])
    codigo, _, _ = _cli(["seguridad", valida, "--resumen", "--proyecto", proy], jira,
                        M19._Bytes({}))
    t.igual("E-26 control: seguridad --resumen con una clave valida escribe el resumen",
            [0, True], [codigo, (claude / "runtime" / "security" / valida /
                                 "security-summary.json").is_file()])
    for clave in CLAVES_INVALIDAS:
        for argv in (["contexto", clave], ["refute", clave, "--compile"],
                     ["refute", clave, "--status"], ["seguridad", clave],
                     ["seguridad", clave, "--resumen"]):
            antes = _arbol(claude)
            codigo, _, _ = _cli(argv + ["--proyecto", proy], jira, M19._Bytes({}))
            nombre = "E-26 con Jira, %s" % " ".join(argv)
            t.igual("%s: sale con 2" % nombre, 2, codigo)
            t.vacio("%s: no crea ni modifica nada en .claude/" % nombre,
                    _diferencias(antes, _arbol(claude)))


CLAVES_VALIDAS = ("GCBA-1", "a-0", "A_B-12", "abc1-999", "X-0001", "Gcba_2-77")
CLAVES_DE_PRUEBA = CLAVES_VALIDAS + CLAVES_INVALIDAS + (
    "", "GCBA", "-12", "GCBA 12", "GCBA-1-2", "_A-1", "ÁB-1", "GCBA-1\n", "GCBA-１", "../GCBA-1")


def test_e27_las_cuatro_reglas_aceptan_las_mismas_claves(t):
    """E-27 — CLAVE_JIRA de dev-harness.py, CLAVE de refutacion.py, el patron de meta.task_key de
    task-context y el de plan_id de orchestration-plan sin el prefijo aceptan las mismas claves."""
    if "m" not in _MODULO_CLI:
        _MODULO_CLI["m"] = _cargar("dev_harness_dm64", CLI)
    contexto = _leer_json(SCHEMAS / "task-context.schema.json")
    patron_contexto = contexto["properties"]["meta"]["properties"]["task_key"]["pattern"]
    patron_plan = _esquema_plan()["properties"]["meta"]["properties"]["plan_id"]["pattern"]
    # La semantica de `pattern` es la del validador del repo: re.search.
    reglas = (("CLAVE_JIRA", lambda c: bool(_MODULO_CLI["m"].CLAVE_JIRA.match(c))),
              ("refutacion.CLAVE", lambda c: bool(R.CLAVE.match(c))),
              ("task-context meta.task_key", lambda c: bool(re.search(patron_contexto, c))),
              ("orchestration-plan plan_id", lambda c: bool(re.search(patron_plan, "pln_" + c))))
    referencia = [c for c in CLAVES_DE_PRUEBA if reglas[0][1](c)]
    t.verdadero("E-27 hay claves validas y claves invalidas en el juego",
                0 < len(referencia) < len(CLAVES_DE_PRUEBA))
    for nombre, regla in reglas[1:]:
        t.igual("E-27 %s acepta las mismas que CLAVE_JIRA" % nombre, referencia,
                [c for c in CLAVES_DE_PRUEBA if regla(c)])
    t.vacio("E-27 todas las claves validas del juego pasan",
            [c for c in CLAVES_VALIDAS if c not in referencia])
    t.vacio("E-27 ninguna de las invalidas pasa", [c for c in CLAVES_INVALIDAS if c in referencia])


CLAVES_DE_LIBRO_INVALIDAS = ("no-es-clave", "s-sesion-1", "GCBA_12", "../GCBA-1",
                             "12345678-1234-1234-1234-12345678901", "{%s}" % str(uuid.uuid4()))


def test_e28_la_ledgerkey_es_una_taskkey_o_una_sesion(t):
    """E-28 — contabilidad acepta una TaskKey o un UUID de sesion, y rechaza cualquier otra clave
    con 2, sin escribir. La statusLine sigue escribiendo en runtime/accounting/<session_id>/."""
    fuente = M55._transcripcion(_tmp("dm64-transcripcion-"))
    for clave in ("GCBA-28", str(uuid.uuid4()), str(uuid.uuid4()).upper()):
        proy = _proyecto()
        codigo, _, error = _cli(["contabilidad", clave, "--ingerir", fuente, "--proyecto", proy])
        t.igual("E-28 %s: contabilidad acepta la clave e ingiere" % clave, 0, codigo)
        t.no_contiene("E-28 %s: sin el error de la clave" % clave, "no es una clave de libro", error)
        t.verdadero("E-28 %s: el libro queda en runtime/accounting/<clave>/" % clave,
                    (proy / ".claude" / "runtime" / "accounting" / clave / "ledger.jsonl").is_file())
        sin_libro = _proyecto()
        codigo, _, error = _cli(["contabilidad", clave, "--proyecto", sin_libro])
        t.no_contiene("E-28 %s sin libro: lo que lo frena no es la clave" % clave,
                      "no es una clave de libro", error)
    for clave in CLAVES_DE_LIBRO_INVALIDAS:
        proy = _proyecto()
        antes = _arbol(proy)
        codigo, _, error = _cli(["contabilidad", clave, "--ingerir", fuente, "--proyecto", proy])
        t.igual("E-28 %s: sale con 2" % clave, 2, codigo)
        t.contiene("E-28 %s: dice que no es una clave de libro" % clave,
                   "no es una clave de libro contable", error)
        t.vacio("E-28 %s: sin escribir" % clave, _diferencias(antes, _arbol(proy)))
    # La statusLine, como la corre Claude Code: el renderizador de un arbol instalado, un
    # proceso por dibujo, con el session_id que mande el Host.
    proy = _tmp("dm64-barra-") / "proyecto"
    renderizador = MEDIDOR.armar(str(proy))
    for sesion in (str(uuid.uuid4()), "s-dm64-" + uuid.uuid4().hex[:8]):
        ruta = str(_tmp("dm64-sesion-") / "sesion.jsonl")
        turnos = MEDIDOR.transcripcion(ruta, 4000, sesion)
        codigo, _, _ = _proceso([sys.executable, renderizador],
                                entrada=MEDIDOR.entrada_de(ruta, turnos, sesion),
                                cwd=tempfile.gettempdir())
        libro = proy / ".claude" / "runtime" / "accounting" / sesion / "ledger.jsonl"
        t.igual("E-28 la statusLine con la sesion %s sale 0" % sesion, 0, codigo)
        t.verdadero("E-28 la statusLine escribe en runtime/accounting/%s/" % sesion,
                    libro.is_file())


def _proyecto_de_19():
    """El proyecto con .env e integraciones de 19_contexto.py, que se borra al terminar."""
    raiz = M19._proyecto_listo()
    atexit.register(_borrar, raiz)
    return raiz


def _issue(clave_devuelta):
    issue = json.loads(json.dumps(M19.ISSUE))
    issue["key"] = clave_devuelta
    return issue


def test_e29_jira_devuelve_otra_clave(t):
    """E-29 — si Jira devuelve en `key` una clave distinta de la pedida,
    gaps_and_conflicts.conflicts registra un conflicto con las dos; meta.task_key, context_id y
    el nombre del archivo conservan la pedida."""
    pedida = M19.CLAVE
    for devuelta in (pedida.lower(), "OTRO-99"):
        acumulador = Acumulador(M19.TODAS)
        c_tarea.resolver(M19._jira(M19.Transporte({"/issue/": (200, _issue(devuelta))})), pedida,
                         M19._catalogo(), M19._config(), acumulador)
        t.verdadero("E-29 %s: el resolvedor registra un conflicto con las dos claves" % devuelta,
                    any(pedida in c and devuelta in c for c in acumulador.conflicts))
    igual = Acumulador(M19.TODAS)
    c_tarea.resolver(M19._jira(M19.Transporte({"/issue/": (200, _issue(pedida))})), pedida,
                     M19._catalogo(), M19._config(), igual)
    t.vacio("E-29 con la misma clave no hay conflicto de claves",
            [c for c in igual.conflicts if pedida in c])

    raiz = _proyecto_de_19()
    transporte = M19.Transporte({"/issue/": (200, _issue("OTRO-99")), "/search": (200, M19.FICHA)})
    codigo, _, _ = _cli(["contexto", pedida, "--proyecto", raiz], transporte, M19._Bytes({}))
    t.igual("E-29 contexto sale 0", 0, codigo)
    carpeta = Path(raiz) / ".claude" / "contextos"
    t.igual("E-29 el archivo conserva la clave pedida", [pedida + ".json"],
            sorted(p.name for p in carpeta.glob("*.json")))
    doc = _leer_json(carpeta / (pedida + ".json")) if (carpeta / (pedida + ".json")).is_file() else {}
    t.igual("E-29 meta.task_key conserva la pedida", pedida, (doc.get("meta") or {}).get("task_key"))
    t.igual("E-29 context_id conserva la pedida", "tsk_" + pedida,
            (doc.get("meta") or {}).get("context_id"))
    conflictos = (doc.get("gaps_and_conflicts") or {}).get("conflicts") or []
    t.verdadero("E-29 gaps_and_conflicts.conflicts registra las dos claves",
                any(pedida in c and "OTRO-99" in c for c in conflictos))


def test_e30_la_misma_taskkey_de_punta_a_punta(t):
    """E-30 — para una misma TaskKey K, con integraciones simuladas: el contexto es tsk_K en
    .claude/contextos/K.json, el plan es pln_K, cada RefutationUnit lleva taskKey K y el ledger
    de seguridad esta en runtime/security/K/."""
    clave = M19.CLAVE
    raiz = Path(_proyecto_de_19())
    transporte = M19.Transporte({"/issue/": (200, M19.ISSUE), "/search": (200, M19.FICHA)})
    codigo, _, error = _cli(["contexto", clave, "--proyecto", raiz], transporte, M19._Bytes({}))
    t.igual("E-30 contexto sale 0", 0, codigo)
    contexto = raiz / ".claude" / "contextos" / (clave + ".json")
    t.verdadero("E-30 el contexto esta en .claude/contextos/K.json", contexto.is_file())
    t.igual("E-30 el contexto es tsk_K", "tsk_" + clave,
            (_leer_json(contexto)["meta"] if contexto.is_file() else {}).get("context_id"))

    _escribir(raiz / "src" / "sesion.py", "TIMEOUT = 900\n")
    _json(raiz / "prop.json", PROPUESTA_E16)
    codigo, _, error = _cli(["plan", clave, "--propuesta", raiz / "prop.json", "--proyecto", raiz])
    t.igual("E-30 plan sale 0", 0, codigo)
    plan = _leer_json(_plan_de(raiz, clave)) if _plan_de(raiz, clave).is_file() else {"meta": {}}
    t.igual("E-30 el plan es pln_K", "pln_" + clave, plan["meta"].get("plan_id"))

    _json(raiz / ".claude" / "refutaciones" / clave / "scope.json", SCOPE_E16)
    codigo, _, error = _cli(["refute", clave, "--compile", "--proyecto", raiz])
    t.igual("E-30 refute --compile sale 0", 0, codigo)
    unidades = _unidades_en(raiz, clave)
    t.verdadero("E-30 hay RefutationUnits", len(unidades) > 0)
    t.vacio("E-30 cada RefutationUnit lleva taskKey K",
            [u["refutationUnitId"] for u in unidades if u.get("taskKey") != clave])

    de_es0902 = [u for u in unidades if u["standard"]["id"] == "ES0902"
                 and u["status"] == "PENDING_SEMANTIC"]
    if de_es0902:
        _json(raiz / "v.json", _veredicto_cumple(de_es0902[0]))
        codigo, _, error = _cli(["refute", clave, "--record", raiz / "v.json", "--proyecto", raiz])
        t.igual("E-30 refute --record sale 0", 0, codigo)
    t.verdadero("E-30 hay una unidad de ES0902 para llevar al libro de seguridad", de_es0902)
    codigo, _, error = _cli(["seguridad", clave, "--refutacion", "--proyecto", raiz])
    t.igual("E-30 seguridad sale 0", 0, codigo)
    libro = raiz / ".claude" / "runtime" / "security" / clave / "security-ledger.ndjson"
    t.verdadero("E-30 el ledger de seguridad esta en runtime/security/K/", libro.is_file())
    eventos = [json.loads(l) for l in libro.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if libro.is_file() else []
    t.verdadero("E-30 el ledger tiene eventos", len(eventos) > 0)
    t.vacio("E-30 y cada evento es de la tarea K",
            [e.get("taskId") for e in eventos if e.get("taskId") != clave])


# -- E-31 a E-36: los checks ------------------------------------------------------------------

# Corre los casos de cierre con el `bin` que se le pase, en su propio proceso: compila, escribe el
# checks.json del caso con las huellas de la primera unidad -como `_con_check` de
# 55_refutacion_atomica.py- y vuelve a compilar. Devuelve la corrida, las unidades, los veredictos
# y el checks.json que escribio, para comparar que las dos lineas recibieron lo mismo.
CONDUCTOR = r'''
import json, os, sys
bin_dir, entrada = sys.argv[1], sys.argv[2]
sys.path.insert(0, bin_dir)
from orquestacion import refutacion as R
with open(entrada, encoding="utf-8") as f:
    casos = json.load(f)
original = R._matrices
salida = []
for caso in casos:
    proy, clave = caso["proyecto"], caso["clave"]
    if caso.get("review"):
        def con_review(desde, regla=caso["review"]):
            m = original(desde)
            doc, version = m["ES0902"]
            doc = json.loads(json.dumps(doc))
            for r in doc["rules"]:
                if r["id"] == regla:
                    r["reviews"] = ["session-timeout-review"]
            m["ES0902"] = (doc, version)
            return m
        R._matrices = con_review
    escrito = None
    try:
        R.compilar(proy, clave)
        if caso.get("check"):
            u = R.leer(proy, clave)[1][0]
            c = caso["check"]
            r = {"control": c["control"], "ruleKey": u["standard"]["ruleKey"], "state": c["estado"],
                 "repoRevision": u["repoRevision"], "evidenceFingerprint": u["evidenceFingerprint"]}
            r.update(c.get("cambios") or {})
            escrito = {"schema_version": R.VERSION_CHECKS, "results": [r]}
            ruta = os.path.join(proy, ".claude", "refutaciones", clave, "checks.json")
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(escrito))
            R.compilar(proy, clave)
        corrida, unidades, veredictos = R.leer(proy, clave)
        with open(os.path.join(proy, ".claude", "planes", clave + ".json"), encoding="utf-8") as f:
            plan = json.load(f)
    finally:
        R._matrices = original
    salida.append({"run": corrida, "units": unidades, "verdicts": veredictos, "checks": escrito,
                   "plan": plan})
sys.stdout.write(json.dumps(salida))
'''

SESION_TIMEOUT = "session-inactivity-timeout"


def _casos_de_cierre():
    """Los casos de cierre de 55_refutacion_atomica.py (E-11 a E-15), con sus planes: los arma
    `_plan` de 55 sobre su repositorio de prueba. Mas un FAIL, uno sin checks.json y uno cuyo
    control es el nombre de un requiredCheck de la unidad, que es lo que D6 saca de declaredChecks."""
    vu4 = {"WU-1": M55._bloque(["Vu4"], checks=[SESION_TIMEOUT])}
    vu7 = {"WU-1": M55._bloque(["Vu7"], checks=[SESION_TIMEOUT])}
    requerido = M55._plan(M55.CLAVE, vu4)["workUnits"][0]["requiredChecks"][0]
    pasa = {"control": SESION_TIMEOUT, "estado": "PASS"}
    return [
        ("E-11 un PASS concluyente", vu4, pasa, None),
        ("E-12 APPLICABILITY_UNRESOLVED", vu4, dict(pasa, estado="APPLICABILITY_UNRESOLVED"), None),
        ("E-12 NOT_APPLICABLE", vu4, dict(pasa, estado="NOT_APPLICABLE"), None),
        ("E-12 SESSION_TIMEOUT_UNRESOLVED", vu4, dict(pasa, estado="SESSION_TIMEOUT_UNRESOLVED"), None),
        ("E-13 otra huella", vu4, dict(pasa, cambios={"evidenceFingerprint": "sha256:" + "0" * 64}),
         None),
        ("E-13 otra revision", vu4, dict(pasa, cambios={"repoRevision": "f" * 40}), None),
        ("E-14 la regla pide una review", vu4, pasa, "Vu4"),
        ("E-15 un check de otra regla", vu7, pasa, None),
        ("un FAIL concluyente", vu4, dict(pasa, estado="FAIL"), None),
        ("el control es el requiredCheck %s" % requerido, vu4,
         {"control": requerido, "estado": "PASS"}, None),
        ("sin checks.json", vu4, None, None),
    ]


_CIERRE = {}


def _cierre():
    """{"rotulos", "base", "nuevo"} de los casos de cierre corridos por 4c6f0f3 y por este
    codigo sobre copias identicas, o {"motivo"} si no se pudo."""
    if _CIERRE:
        return _CIERRE
    bin_base, motivo = _bin_base()
    if bin_base is None:
        _CIERRE["motivo"] = motivo
        return _CIERRE
    casos = _casos_de_cierre()
    entradas = {"base": [], "nuevo": []}
    for _, unidades, check, review in casos:
        proy = Path(M55._proyecto(unidades))
        for lado in entradas:
            entradas[lado].append({"proyecto": str(_copia(proy)), "clave": M55.CLAVE,
                                   "check": check, "review": review})
        _borrar(proy)
    for plantilla in M55._PLANTILLAS.values():          # el repositorio de prueba de 55
        atexit.register(_borrar, plantilla)
    _CIERRE["rotulos"] = [c[0] for c in casos]
    carpeta = _tmp("dm64-cierre-")
    for lado, bin_dir in (("base", bin_base), ("nuevo", BIN)):
        ruta = carpeta / ("casos-%s.json" % lado)
        _json(ruta, entradas[lado])
        codigo, salida, error = _proceso([sys.executable, "-c", CONDUCTOR, str(bin_dir), str(ruta)])
        _CIERRE[lado] = json.loads(salida) if codigo == 0 else None
        if codigo != 0:
            _CIERRE["motivo"] = "los casos de cierre no corrieron con %s: %s" % (lado, error[-600:])
    return _CIERRE


def _checks_del_roster():
    return {c["name"] for c in _leer_json(REGLAS / "roster.json")["checks"]}


def _declarados_por_la_norma(plan, unidad):
    """Los ControlCheck que declara la norma para una RefutationUnit (E-31): los `declaredChecks`
    del bloque normativo de su regla -el de su estandar en `standards`, o el bloque de arriba si
    la unidad del plan no trae `standards`- y los del bloque normativo de la unidad."""
    wu = next((w for w in plan.get("workUnits") or []
               if str(w.get("id") or "") == unidad["workUnitId"]), {})
    normativa = wu.get("normative") if isinstance(wu.get("normative"), dict) else {}
    estandares = normativa.get("standards")
    bloque = (estandares.get(unidad["standard"]["id"]) or {}
              if isinstance(estandares, dict) and estandares else normativa)
    return sorted(set(list(bloque.get("declaredChecks") or [])
                      + list(normativa.get("declaredChecks") or [])))


def test_e31_declared_checks_son_los_que_declara_la_norma(t):
    """E-31 — los declaredChecks de toda RefutationUnit compilada son exactamente los ids de
    ControlCheck que declara la norma: los del bloque normativo de la regla y los del bloque
    normativo de la unidad. Ninguno es un nombre de roster.json checks.

    No se exige que esten en control-registry.json: la spec lo corrigio durante la construccion.
    21 de los 34 checks que declara la matriz de ES0901 no estan registrados todavia
    (DECLARED_CHECK_NOT_INSTALLED), y ya pasaba en 4c6f0f3."""
    compilado, cierre = _compilado_e16(), _cierre()
    if compilado is None or cierre.get("nuevo") is None:
        _sin_base(t, "E-31", cierre.get("motivo") or _proyecto_e16()[1])
        return
    roster = _checks_del_roster()
    # Las unidades de E-16 salen del plan del proyecto de E-16, que refute --compile no toca; las
    # de cada caso de cierre, del plan que compilo el conductor.
    plan_e16 = _leer_json(_plan_de(_proyecto_e16()[0]))
    pares = [(plan_e16, u) for u in compilado["nuevo"]]
    pares += [(c["plan"], u) for c in cierre["nuevo"] for u in c["units"]]
    viejas = compilado["base"] + [u for c in cierre["base"] for u in c["units"]]
    t.verdadero("E-31 hay unidades compiladas", len(pares) > 0)
    t.verdadero("E-31 la norma declara checks en alguna unidad",
                any(_declarados_por_la_norma(p, u) for p, u in pares))
    t.verdadero("E-31 la entrada trae requiredChecks: con 4c6f0f3 se mezclaban en declaredChecks",
                any(set(u["declaredChecks"]) & roster for u in viejas))
    t.vacio("E-31 los declaredChecks de cada unidad son exactamente los que declara la norma",
            ["%s %s: %s / la norma: %s" % (u["workUnitId"], u["standard"]["ruleKey"],
                                           u["declaredChecks"], _declarados_por_la_norma(p, u))
             for p, u in pares if u["declaredChecks"] != _declarados_por_la_norma(p, u)][:10])
    t.vacio("E-31 ningun declaredCheck es un check de roster.json",
            sorted({c for _, u in pares for c in u["declaredChecks"] if c in roster}))


def test_e32_los_casos_de_cierre_resuelven_igual_que_4c6f0f3(t):
    """E-32 — sobre los planes y los checks.json de los casos de cierre de
    55_refutacion_atomica.py, el codigo nuevo resuelve las mismas unidades, por el mismo camino y
    con el mismo veredicto que 4c6f0f3."""
    cierre = _cierre()
    if cierre.get("nuevo") is None or cierre.get("base") is None:
        _sin_base(t, "E-32", cierre.get("motivo"))
        return
    camino = lambda u: (u["refutationUnitId"], u["workUnitId"], u["standard"]["ruleKey"],
                        u["status"], u["resolutionPath"], u["failure"])
    juicio = lambda v: (v["refutationUnitId"], v["verdict"], v["resolutionPath"])
    for rotulo, viejo, nuevo in zip(cierre["rotulos"], cierre["base"], cierre["nuevo"]):
        t.igual("E-32 %s: los dos recibieron el mismo checks.json" % rotulo,
                viejo["checks"], nuevo["checks"])
        t.igual("E-32 %s: las mismas unidades, por el mismo camino" % rotulo,
                [camino(u) for u in viejo["units"]], [camino(u) for u in nuevo["units"]])
        t.igual("E-32 %s: los mismos veredictos" % rotulo,
                [juicio(v) for v in viejo["verdicts"]], [juicio(v) for v in nuevo["verdicts"]])
        t.igual("E-32 %s: el mismo agregado" % rotulo,
                [viejo["run"][k] for k in ("status", "counts", "units")],
                [nuevo["run"][k] for k in ("status", "counts", "units")])
    caminos = {u["resolutionPath"] for c in cierre["nuevo"] for u in c["units"]}
    t.verdadero("E-32 los casos ejercitan el cierre por check", "DETERMINISTIC_CHECK" in caminos)


def test_e33_la_cache_key_no_cambia(t):
    """E-33 — con las mismas entradas, la cacheKey de cada unidad es igual a la de 4c6f0f3."""
    compilado, cierre = _compilado_e16(), _cierre()
    if compilado is None or cierre.get("nuevo") is None:
        _sin_base(t, "E-33", cierre.get("motivo") or _proyecto_e16()[1])
        return
    clave = lambda u: (u["refutationUnitId"], u["cacheKey"])
    t.igual("E-33 el plan de E-16: la misma cacheKey por unidad",
            [clave(u) for u in compilado["base"]], [clave(u) for u in compilado["nuevo"]])
    for rotulo, viejo, nuevo in zip(cierre["rotulos"], cierre["base"], cierre["nuevo"]):
        t.igual("E-33 %s: la misma cacheKey por unidad" % rotulo,
                [clave(u) for u in viejo["units"]], [clave(u) for u in nuevo["units"]])
    t.verdadero("E-33 hay cacheKeys que comparar",
                any(u["cacheKey"] for u in compilado["nuevo"]))


def _de_texto(ruta):
    try:
        return (RAIZ / ruta).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


CORRE_EN_PRE = re.compile(r"(?i)\bcorre(?:n)?\s+en\s+`?PreToolUse")
CORRE_EN_POST = re.compile(r"(?i)\bcorre(?:n)?\s+en\s+`?PostToolUse")


def _corrido(texto):
    """El texto con los saltos, comillas, comas y marcas de comentario pasados a un espacio: una
    frase partida entre dos lineas de un `_comentario` JSON se lee entera."""
    return re.sub(r"[\s\",#]+", " ", texto)


def test_e34_ningun_check_del_hook_corre_en_pretooluse(t):
    """E-34 — ningun archivo de comun/ ni de harnesses/ dice que un check del hook corre en
    PreToolUse. control-registry.json y controles.py dicen PostToolUse."""
    archivos = [r for r in _archivos_del_repo() if r.startswith(("comun/", "harnesses/"))]
    t.verdadero("E-34 hay archivos para revisar", len(archivos) > 0)
    t.vacio("E-34 nadie dice que un check corre en PreToolUse",
            [r for r in archivos if CORRE_EN_PRE.search(_corrido(_de_texto(r)))])
    for ruta in ("harnesses/desarrollo/reglas/control-registry.json",
                 "harnesses/desarrollo/bin/orquestacion/controles.py"):
        t.verdadero("E-34 %s dice que los checks del hook corren en PostToolUse" % ruta,
                    CORRE_EN_POST.search(_corrido(_de_texto(ruta))))


def test_e35_ningun_control_se_llama_como_un_check_del_roster(t):
    """E-35 — ningun id del control-registry coincide con un nombre de check de roster.json."""
    controles = {c["id"] for c in _leer_json(REGLAS / "control-registry.json")["controls"]}
    roster = _checks_del_roster()
    t.verdadero("E-35 hay controles y checks para comparar", controles and roster)
    t.vacio("E-35 ningun id del registro es un check del roster", sorted(controles & roster))


def test_e36_la_senal_normativa_es_de_las_dos_normas(t):
    """E-36 — la descripcion de normative-signal.schema.json nombra ES0901 y ES0902."""
    descripcion = _leer_json(SCHEMA_SENAL).get("description") or ""
    t.contiene("E-36 nombra ES0901", "ES0901", descripcion)
    t.contiene("E-36 nombra ES0902", "ES0902", descripcion)


# -- E-37 a E-39: Capability, Tool e Integration ----------------------------------------------

def _capacidades_declaradas():
    """{capacidad: [de donde]}: las clases de integracion (CAPACIDADES, leido del fuente),
    roster.json capacidadesLocales, permisos-por-capacidad.json y manifest.json."""
    salida = {}

    def sumar(capacidad, fuente):
        salida.setdefault(capacidad, []).append(fuente)

    for p in sorted((BIN / "integraciones").glob("*.py")):
        for n in ast.walk(_arbol_py(p)):
            if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "CAPACIDADES"
                                                 for x in n.targets):
                try:
                    valores = ast.literal_eval(n.value)
                except ValueError:
                    continue                 # `CAPACIDADES = CAPACIDADES` en la clase
                for c in valores:
                    sumar(c, "integraciones/" + p.name)
    for c in _leer_json(REGLAS / "roster.json").get("capacidadesLocales") or []:
        sumar(c, "roster.json")
    for c in (_leer_json(REGLAS / "permisos-por-capacidad.json").get("capacidades") or {}):
        sumar(c, "permisos-por-capacidad.json")
    for c in _leer_json(RAIZ / "manifest.json").get("capacidadesSoportadas") or []:
        sumar(c, "manifest.json")
    return salida


def test_e37_la_forma_de_una_capability(t):
    """E-37 — toda capability declarada tiene forma <a>.<b>[.<c>] en minusculas, y ninguna es el
    nombre de una HostTool."""
    declaradas = _capacidades_declaradas()
    fuentes = {f for fs in declaradas.values() for f in fs}
    for fuente in ("integraciones/jira.py", "integraciones/gitlab.py", "roster.json",
                   "permisos-por-capacidad.json", "manifest.json"):
        t.verdadero("E-37 %s declara capabilities" % fuente, fuente in fuentes)
    t.vacio("E-37 todas tienen la forma <a>.<b>[.<c>] en minusculas",
            sorted("%s (%s)" % (c, ", ".join(f)) for c, f in declaradas.items()
                   if not FORMA_DE_CAPABILITY.match(str(c))))
    herramientas = {h.lower() for h in HERRAMIENTAS_DEL_HOST}
    t.vacio("E-37 ninguna es el nombre de una HostTool",
            sorted("%s (%s)" % (c, ", ".join(f)) for c, f in declaradas.items()
                   if str(c).lower() in herramientas))


def _herramientas_de(ruta):
    texto = _texto(ruta).replace("\r\n", "\n")
    frente = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    linea = re.search(r"(?m)^tools:\s*(.*)$", frente.group(1)) if frente else None
    return [h.strip() for h in linea.group(1).split(",") if h.strip()] if linea else None


def test_e38_ningun_agente_nombra_una_capability_en_tools(t):
    """E-38 — ningun `tools:` de un agente de harnesses/desarrollo/agents/ o de comun/agents/
    nombra una capability."""
    capacidades = set(_capacidades_declaradas())
    agentes = sorted(list((RAIZ / "harnesses" / "desarrollo" / "agents").glob("*.md"))
                     + list((RAIZ / "comun" / "agents").glob("*.md")))
    t.verdadero("E-38 hay agentes para revisar", len(agentes) > 0)
    for ruta in agentes:
        herramientas = _herramientas_de(ruta)
        if herramientas is None:
            continue
        t.vacio("E-38 %s no nombra una capability en tools:" % ruta.name,
                [h for h in herramientas if h in capacidades or FORMA_DE_CAPABILITY.match(h)])


DICE_QUE_EL_MANIFIESTO_DECLARA = (
    re.compile(r"(?i)\blos?\s+declara\s+el\s+manifiesto"),
    re.compile(r"(?i)\blas?\s+declaran?\s+el\s+manifiesto"),
    re.compile(r"(?i)declarad[ao]s?\s+(?:en|por)\s+el\s+manifiesto"),
    re.compile(r"(?i)soportad[ao].*->.*manifiesto"),
)


def test_e39_lo_soportado_lo_declaran_las_clases(t):
    """E-39 — integraciones/registro.py y docs/integraciones.md dicen que las capacidades
    soportadas las declaran las clases de integracion, y ninguno dice que las declara el
    manifiesto."""
    registro = _texto(BIN / "integraciones" / "registro.py")
    docs = _texto(RAIZ / "docs" / "integraciones.md")
    t.contiene("E-39 registro.py dice que la soportada la declara la clase de integracion",
               "lo declara la clase de integracion", registro)
    t.contiene("E-39 docs/integraciones.md dice que lo soportado lo declaran las clases",
               "Lo soportado lo declaran las clases de integración", docs)
    for nombre, texto in (("registro.py", registro), ("docs/integraciones.md", docs)):
        t.vacio("E-39 %s no dice que las declara el manifiesto" % nombre,
                [l.strip() for l in texto.splitlines()
                 if any(p.search(l) for p in DICE_QUE_EL_MANIFIESTO_DECLARA)])


# -- E-40 a E-43: el limite de la ejecucion y la observabilidad -------------------------------

CICLO_RE = re.compile(r"(?<![A-Z_])(%s)(?![A-Z_])" % "|".join(CICLO))
EVENTOS = "harnesses/desarrollo/bin/contabilidad/eventos.py"
DONDE_PUEDE_ESTAR = {"comun/schemas/execution-accounting-event.schema.json",
                     "harnesses/desarrollo/bin/contabilidad/agregacion.py"}


def _lineas_de_tipos(ruta):
    """(primera, ultima) linea de la asignacion TIPOS de eventos.py, o (0, -1)."""
    for n in ast.walk(_arbol_py(ruta)):
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "TIPOS"
                                             for x in n.targets):
            return n.lineno, getattr(n, "end_lineno", n.lineno)
    return 0, -1


def test_e40_nadie_emite_los_eventos_del_ciclo(t):
    """E-40 — en bin/ y comun/, TASK_*, WORKUNIT_* y AGENT_RUN_* aparecen solo en eventos.py
    (TIPOS), en el schema y en la lectura del agregador. Ningun productor los emite."""
    primera, ultima = _lineas_de_tipos(RAIZ / EVENTOS)
    tipos = ast.literal_eval(next(n.value for n in ast.walk(_arbol_py(RAIZ / EVENTOS))
                                  if isinstance(n, ast.Assign)
                                  and any(isinstance(x, ast.Name) and x.id == "TIPOS"
                                          for x in n.targets)))
    t.vacio("E-40 TIPOS declara los seis", [c for c in CICLO if c not in tipos])
    enum = _leer_json(SCHEMA_CONTABLE)["properties"]["eventType"]["enum"]
    t.vacio("E-40 el schema los declara", [c for c in CICLO if c not in enum])
    fuera = []
    for ruta in _archivos_del_repo():
        if not ruta.startswith(("harnesses/desarrollo/bin/", "comun/")) or ruta in DONDE_PUEDE_ESTAR:
            continue
        for n, linea in enumerate(_de_texto(ruta).splitlines(), 1):
            if CICLO_RE.search(linea) and not (ruta == EVENTOS and primera <= n <= ultima):
                fuera.append("%s:%d" % (ruta, n))
    t.vacio("E-40 fuera de TIPOS, el schema y el agregador, nadie los nombra", fuera)


LANZADORES = {"run", "Popen", "call", "check_call", "check_output", "getoutput",
              "getstatusoutput"}


def _programa(nodo):
    """El programa que lanza una lista de argumentos: 'git'. '<...>' si no es un literal, None si
    no es una lista."""
    while isinstance(nodo, ast.BinOp):
        nodo = nodo.left
    if isinstance(nodo, (ast.List, ast.Tuple)) and nodo.elts:
        primero = nodo.elts[0]
        if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
            return os.path.splitext(os.path.basename(primero.value))[0].lower()
        return "<%s>" % (_nombre(primero) or type(primero).__name__)
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return (nodo.value.split() or ["<vacio>"])[0]
    return None


def _quien_llama(arbol, funcion):
    """Lo que lanzan las llamadas a `funcion` en el modulo, contando sus alias (`x = a or f`)."""
    alias = {funcion}
    for n in ast.walk(arbol):
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id in alias
                                             for x in ast.walk(n.value)):
            alias |= {x.id for x in n.targets if isinstance(x, ast.Name)}
    programas = []
    for c in _llamadas(arbol):
        f = c.func
        if ((isinstance(f, ast.Name) and f.id in alias)
                or (isinstance(f, (ast.BoolOp, ast.IfExp))
                    and any(isinstance(x, ast.Name) and x.id in alias for x in ast.walk(f)))):
            programas.append(_programa(c.args[0]) if c.args else None)
    return programas


def _lanzamientos(ruta):
    """[(linea, programa)] de cada subprocess, os.system y parecidos de un modulo. Si se lanza
    un parametro, se sigue a quien llama a la funcion que lo recibe."""
    arbol = _arbol_py(ruta)
    modulos, sueltos = set(), set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            modulos |= {a.asname or a.name for a in n.names if a.name == "subprocess"}
        if isinstance(n, ast.ImportFrom) and n.module == "subprocess":
            sueltos |= {a.asname or a.name for a in n.names if a.name in LANZADORES}
    envolventes = {}
    for f in ast.walk(arbol):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(f):
                envolventes[id(n)] = f
    salida = []
    for c in _llamadas(arbol):
        f = c.func
        nombre = _nombre(f)
        if nombre in ("os.system", "os.popen", "pty.spawn") or nombre.startswith(
                ("os.spawn", "os.exec", "asyncio.create_subprocess")):
            salida.append((c.lineno, "<%s>" % nombre))
            continue
        if not ((isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                 and f.value.id in modulos and f.attr in LANZADORES)
                or (isinstance(f, ast.Name) and f.id in sueltos)):
            continue
        arg = c.args[0] if c.args else next((k.value for k in c.keywords if k.arg == "args"), None)
        programa = _programa(arg)
        envolvente = envolventes.get(id(c))
        if (programa is None and isinstance(arg, ast.Name) and envolvente is not None
                and arg.id in [a.arg for a in envolvente.args.args]):
            seguidos = _quien_llama(arbol, envolvente.name)
            salida.extend((c.lineno, p) for p in (seguidos or ["<%s sin quien lo llame>" % arg.id]))
            continue
        salida.append((c.lineno, programa or "<no se puede leer>"))
    return salida


def test_e41_todo_subprocess_lanza_git_o_markitdown(t):
    """E-41 — todo subprocess del codigo de bin/ y comun/ lanza git o markitdown."""
    vistos, ajenos = set(), []
    for p in _py_de(BIN) + _py_de(RAIZ / "comun"):
        for linea, programa in _lanzamientos(p):
            vistos.add(programa)
            if programa not in ("git", "markitdown"):
                ajenos.append("%s:%d %s" % (p.relative_to(RAIZ).as_posix(), linea, programa))
    t.verdadero("E-41 se encontraron los lanzamientos de git y de markitdown",
                {"git", "markitdown"} <= vistos)
    t.vacio("E-41 nada lanza otra cosa que git o markitdown", ajenos)


def test_e42_orquestacion_no_lee_la_contabilidad(t):
    """E-42 — ningun modulo de orquestacion/ importa contabilidad ni abre una ruta bajo
    .claude/runtime/accounting."""
    malos = []
    for p in _py_de(BIN / "orquestacion"):
        arbol = _arbol_py(p)
        for n in ast.walk(arbol):
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "contabilidad"
                                                 for a in n.names):
                malos.append("%s:%d import" % (p.name, n.lineno))
            if isinstance(n, ast.ImportFrom) and (
                    (n.module or "").split(".")[0] == "contabilidad"
                    or any(a.name == "contabilidad" for a in n.names)):
                malos.append("%s:%d from import" % (p.name, n.lineno))
            if (isinstance(n, ast.Call) and _nombre(n.func).split(".")[-1] in
                    ("import_module", "__import__") and n.args
                    and isinstance(n.args[0], ast.Constant)
                    and str(n.args[0].value).split(".")[0] == "contabilidad"):
                malos.append("%s:%d import_module" % (p.name, n.lineno))
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and re.search(r"(^|[\\/])accounting([\\/]|$)", n.value)):
                malos.append("%s:%d ruta %s" % (p.name, n.lineno, n.value))
        malos += ["%s ruta 'runtime', 'accounting'" % p.name
                  for _ in [0] if "accounting" in _constantes(p)]
    t.verdadero("E-42 hay modulos de orquestacion para revisar", len(_py_de(BIN / "orquestacion")) > 0)
    t.vacio("E-42 ninguno importa contabilidad ni abre .claude/runtime/accounting", malos)


def _libro_contable(proy, clave):
    ruta = Path(proy) / ".claude" / "runtime" / "accounting" / clave / "ledger.jsonl"
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if ruta.is_file() else []


def test_e43_la_contabilidad_no_cambia_su_contrato(t):
    """E-43 — el enum de eventType sigue con los mismos 14 valores en el mismo orden, sin $id
    nuevo; la descripcion dice que no es estado de ejecucion y la de taskId que es una TaskKey o
    una sesion del Host; ingerir la misma transcripcion da los mismos eventId que 4c6f0f3."""
    base, motivo = _base()
    if base is None:
        _sin_base(t, "E-43", motivo)
        return
    ahora = _leer_json(SCHEMA_CONTABLE)
    antes = _leer_json(base / "comun" / "schemas" / "execution-accounting-event.schema.json")
    t.igual("E-43 eventType: los mismos valores en el mismo orden",
            antes["properties"]["eventType"]["enum"], ahora["properties"]["eventType"]["enum"])
    t.igual("E-43 son catorce", 14, len(ahora["properties"]["eventType"]["enum"]))
    t.igual("E-43 sin $id nuevo", antes.get("$id"), ahora.get("$id"))
    t.contiene("E-43 la descripcion dice que no es estado de ejecucion",
               "no es estado de ejecucion", _plano(ahora.get("description")))
    task_id = ahora["properties"]["taskId"].get("description") or ""
    t.contiene("E-43 taskId es una TaskKey", "TaskKey", task_id)
    t.contiene("E-43 o una sesion del Host", "sesion del host", _plano(task_id))
    bin_base = base / "harnesses" / "desarrollo" / "bin"
    carpeta = _tmp("dm64-ingesta-")
    ruta_larga = str(carpeta / "larga.jsonl")
    MEDIDOR.transcripcion(ruta_larga, 6000, "s-dm64-ingesta")
    for rotulo, fuente in (("la de 55", M55._transcripcion(carpeta)), ("la de medir_barra", ruta_larga)):
        p_base, p_nuevo = _proyecto(), _proyecto()
        cb, _, _ = _cli_de(bin_base, p_base, "contabilidad", "GCBA-43", "--ingerir", fuente)
        cn, _, _ = _cli_de(BIN, p_nuevo, "contabilidad", "GCBA-43", "--ingerir", fuente)
        t.igual("E-43 %s: las dos ingestas salen 0" % rotulo, [0, 0], [cb, cn])
        viejos = [e["eventId"] for e in _libro_contable(p_base, "GCBA-43")]
        t.verdadero("E-43 %s: hay eventos" % rotulo, len(viejos) > 0)
        t.igual("E-43 %s: los mismos eventId que 4c6f0f3" % rotulo, viejos,
                [e["eventId"] for e in _libro_contable(p_nuevo, "GCBA-43")])


# -- E-46 a E-48: el validador, la documentacion y los pendientes -----------------------------

def test_e46_los_tres_schemas_que_cambian_pasan_controlar_soporte(t):
    """E-46 — los tres schemas que cambian no usan palabras clave que el validador no conozca."""
    for ruta in (SCHEMA_PLAN, SCHEMA_CONTABLE, SCHEMA_SENAL):
        try:
            ARMADOR.controlar_soporte(_leer_json(ruta))
            error = ""
        except Exception as e:            # noqa: BLE001 - el motivo es el detalle
            error = "%s: %s" % (type(e).__name__, e)
        t.igual("E-46 %s pasa controlar_soporte" % ruta.name, "", error)


def _estados_en(texto):
    return [m.group(1) for m in re.finditer(r"(?<![A-Z_])(%s)(?![A-Z_])" % "|".join(QUE_SALEN),
                                            texto)]


def test_e47_la_documentacion_dice_los_estados_y_la_regla_de_lectura(t):
    """E-47 — docs/orquestacion.md nombra exactamente los estados de E-13 y E-14 y ninguno de los
    que salen; nombra orchestration-plan/2.0 y la regla de lectura de un 1.0. docs/contabilidad.md
    dice que la contabilidad no es estado de ejecucion."""
    texto = _texto(RAIZ / "docs" / "orquestacion.md")
    estado = _seccion(texto, "El estado se calcula")
    tablas = _tablas(estado)
    primera = lambda tabla: [re.sub(r"`", "", f[0]) for f in tabla[1:]]
    t.igual("E-47 la tabla del plan tiene exactamente sus tres estados", ESTADOS_PLAN,
            primera(tablas[0]) if tablas else [])
    t.igual("E-47 la tabla de la unidad tiene exactamente sus tres estados", ESTADOS_UNIDAD,
            primera(tablas[1]) if len(tablas) > 1 else [])
    t.vacio("E-47 donde se dicen los estados no aparece ninguno de los que salen",
            _estados_en("\n".join(estado)))
    regla = "La versión del contrato, y un plan guardado con la anterior"
    lectura = "\n".join(_seccion(texto, regla))
    t.verdadero("E-47 tiene la seccion de la regla de lectura", lectura.strip())
    fuera_de_la_regla = "\n".join(l for l in texto.splitlines() if l not in _seccion(texto, regla))
    t.vacio("E-47 fuera de la regla de lectura, ninguno de los que salen",
            _estados_en(fuera_de_la_regla))
    t.contiene("E-47 nombra orchestration-plan/2.0", "orchestration-plan/2.0", texto)
    for aguja in ("`1.0`", "refute --compile", "--replanificar", "Lo rechazan", "plan --propuesta"):
        t.contiene("E-47 la regla de lectura de un 1.0 dice %s" % aguja, aguja, lectura)
    t.contiene("E-47 docs/contabilidad.md dice que la contabilidad no es estado de ejecucion",
               "La contabilidad no es estado de ejecución", _texto(RAIZ / "docs" / "contabilidad.md"))


def _titulos_de_e48():
    lineas = _texto(SPEC).splitlines()
    inicio = next((i for i, l in enumerate(lineas) if l.startswith("- **E-48**")), None)
    salida = []
    for linea in lineas[inicio + 1:] if inicio is not None else []:
        if linea.startswith("- **E-"):
            break
        m = re.match(r"^\s+\d+\.\s+\*(.+)\*[;.]\s*$", linea)
        if m:
            salida.append(m.group(1))
    return salida


def test_e48_los_doce_pendientes(t):
    """E-48 — PENDIENTES-FH.md tiene los doce items de lo que no se arregla aca, con sus titulos."""
    titulos = _titulos_de_e48()
    t.igual("E-48 la spec trae doce titulos", 12, len(titulos))
    pendientes = _texto(RAIZ / "Pendientes" / "Fix-Harness" / "PENDIENTES-FH.md").splitlines()
    encabezados = {l[4:].strip() for l in pendientes if l.startswith("### ")}
    for titulo in titulos:
        t.verdadero("E-48 PENDIENTES-FH.md tiene: %s" % titulo, titulo in encabezados)
