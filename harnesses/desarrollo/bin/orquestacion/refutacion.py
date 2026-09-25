"""La refutacion atomica: del plan a unidades acotadas, y de sus veredictos a un agregado.

Bloque 3, la mitad determinista de la refutacion. `dev-refutador` sigue siendo el unico que
juzga, y lo sigue haciendo la sesion de Claude Code. Lo que hace este modulo es todo lo que se
puede testear:

    compilar     plan -> una RefutationUnit por (unidad de trabajo, regla, alcance)
    acotar       el alcance lo declara quien ejecuto; si no, la unidad queda bloqueada
    huellar      los bytes de cada archivo del alcance, no solo HEAD
    checks       un check concluyente, atado y actual cierra la unidad sin modelo
    cache        un veredicto exacto se reusa solo con las mismas huellas
    validar      lo que devuelve el refutador entra solo si cumple el contrato
    agregar      PASS, FAIL, INCOMPLETE o NOTHING_TO_VERIFY, sin modelo

🔴 Nada de aca razona sobre una norma ni llama a un modelo. Si una decision necesita criterio,
la unidad queda pendiente de refutacion semantica y la toma `dev-refutador`.

🔴 Nunca se cae al repositorio entero. Un alcance que no se puede acotar deja la unidad
bloqueada: un refutador que "mira todo" es el que media revision presenta como completa.
"""
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

VERSION_UNIDAD = "refutation-unit/1.0"
VERSION_VEREDICTO = "refutation-verdict/1.0"
VERSION_CORRIDA = "refutation-run/1.0"
VERSION_ALCANCE = "refutation-scope/1.0"
VERSION_CHECKS = "refutation-checks/1.0"

# La version del contrato de dev-refutador que este modulo sabe alimentar. La huella del
# archivo va al lado: un cambio del texto invalida la cache aunque nadie suba el numero.
CONTRATO = "dev-refutador/2.0"
REFUTADOR = "dev-refutador"
ARCHIVO_DEL_REFUTADOR = "agents/dev-refutador.md"

SCHEMA_UNIDAD = "refutation-unit.schema.json"
SCHEMA_VEREDICTO = "refutation-verdict.schema.json"
SCHEMA_CORRIDA = "refutation-run.schema.json"

BASE = (".claude", "refutaciones")
CACHE = "cache"
CORRIDA = "run.json"
ALCANCE = "scope.json"
CHECKS = "checks.json"

CLAVE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")
ID_DE_UNIDAD = re.compile(r"^REF-[0-9]{3,}$")

# Los estados. En ingles, como todo lo de maquina (ADR-0011).
PENDIENTE = "PENDING_SEMANTIC"
RESUELTA = "RESOLVED"
BLOQUEADA = "BLOCKED"

POR_CHECK = "DETERMINISTIC_CHECK"
SEMANTICA = "SEMANTIC_REFUTATION"
POR_CACHE = "CACHE"

ALCANCE_RESUELTO = "RESOLVED"
ALCANCE_SIN_RESOLVER = "EVIDENCE_SCOPE_UNRESOLVED"

PASA = "PASS"
FALLA = "FAIL"
INCOMPLETA = "INCOMPLETE"
NADA = "NOTHING_TO_VERIFY"

CUMPLE = "cumple"
INCUMPLE = "incumple"
SIN_VERIFICAR = "sin-verificar"
VEREDICTOS = (CUMPLE, INCUMPLE, SIN_VERIFICAR)
REUSABLES = (CUMPLE, INCUMPLE)

SCOPE_UNRESOLVED = "REFUTATION_SCOPE_UNRESOLVED"
RULE_UNRESOLVED = "REFUTATION_RULE_UNRESOLVED"
SKILL_UNAVAILABLE = "REFUTATION_SKILL_UNAVAILABLE"
REFUTER_UNAVAILABLE = "REFUTATION_REFUTER_UNAVAILABLE"
CHECK_UNRESOLVED = "REFUTATION_CHECK_UNRESOLVED"
EVIDENCE_STALE = "REFUTATION_EVIDENCE_STALE"
OUTPUT_INVALID = "REFUTATION_OUTPUT_INVALID"
CACHE_INVALID = "REFUTATION_CACHE_INVALID"
NOTHING_TO_VERIFY = "REFUTATION_NOTHING_TO_VERIFY"
BATCH_INVALID = "REFUTATION_BATCH_INVALID"

# De mayor a menor prioridad. Para cada (unidad, regla) se usan los alcances de la primera
# fuente que tenga alguno; los de las de abajo se descartan.
FUENTES = ("workUnitFiles", "changedFiles", "projectContext", "executionEvidence")

# Lo que solo escribe el harness. Un veredicto que llega con esto se esta atribuyendo un
# camino -cache, check- que no recorrio.
CAMPOS_DEL_HARNESS = ("resolutionPath", "cacheHit", "recordedAt", "checkEvidenceFingerprint",
                      "skillFingerprint", "normativeSourceFingerprint")

CONCLUYENTES = {"PASS": CUMPLE, "FAIL": INCUMPLE}

# Un alcance es acotado o no es alcance. Mas de esto no es la evidencia de una regla: es un
# barrido con otro nombre.
TOPE_DE_ARCHIVOS = 200
TOPE_DE_TEXTO = 300

# Lo que no entra nunca a un alcance. Es la misma lista corta que el hook ya no deja leer: un
# refutador que recibe un `.env` en su alcance va a abrirlo.
SECRETO = re.compile(r"(^|/)(\.env(\..*)?|secrets/.*|.*\.(pem|key|pfx|p12|keystore)|id_rsa.*)$",
                     re.IGNORECASE)
COMODIN = re.compile(r"[*?\[\]]")


def aviso(codigo, *sujetos):
    """Un aviso de maquina: `CODIGO:sujeto:...`. Sin prosa.

    `run.json` es de maquina y sale tal cual por `--json`: un aviso en espanol ahi es texto
    para personas en un contrato. El texto lo arma `texto_de_aviso`, que es del renderizador.
    """
    return ":".join([codigo] + [str(x) for x in sujetos])


AVISO = re.compile(r"^[A-Z][A-Z_]*(:[A-Za-z0-9._-]+)*$")


class RefutacionInvalida(Exception):
    """No se escribe nada. Lleva el codigo canonico adelante del mensaje."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, "%s: %s" % (codigo, mensaje))
        self.codigo = codigo


# -- utilidades ----------------------------------------------------------------

def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def huella_de_bytes(contenido):
    return "sha256:" + hashlib.sha256(contenido).hexdigest()


def huella(valor):
    """`sha256:` del JSON canonico. La misma forma que usa el libro de seguridad."""
    texto = json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return huella_de_bytes(texto.encode("utf-8"))


def huella_de_archivo(ruta):
    try:
        with io.open(ruta, "rb") as f:
            return huella_de_bytes(f.read())
    except OSError:
        return None


def _huella_memo(ruta, memo):
    if memo is None:
        return huella_de_archivo(ruta)
    if ruta not in memo:
        memo[ruta] = huella_de_archivo(ruta)
    return memo[ruta]


def _como_texto(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _escribir(ruta, doc):
    """A un temporal y despues `os.replace`: un archivo abierto con "w" se trunca antes de que
    el `write` pueda fallar, y un veredicto a medio escribir es peor que ninguno."""
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    temporal = ruta + ".tmp"
    with io.open(temporal, "w", encoding="utf-8", newline="\n") as f:
        f.write(_como_texto(doc))
    os.replace(temporal, ruta)
    return ruta


def _leer_json(ruta):
    """(documento, error). Ausente es (None, None)."""
    if not os.path.isfile(ruta):
        return None, None
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f), None
    except (OSError, ValueError) as e:
        return None, str(e)


def validar_clave(clave):
    clave = str(clave or "")
    if not CLAVE.match(clave):
        raise RefutacionInvalida(
            OUTPUT_INVALID, "`%s` no es una clave de tarea. Tiene la forma PROYECTO-123." % clave)
    return clave


def carpeta_de(proyecto, clave):
    return os.path.join(proyecto, *(BASE + (validar_clave(clave),)))


def carpeta_de_cache(proyecto):
    return os.path.join(proyecto, *(BASE + (CACHE,)))


def ruta_del_plan(proyecto, clave):
    return os.path.join(proyecto, ".claude", "planes", validar_clave(clave) + ".json")


# -- el validador --------------------------------------------------------------

_CACHE_MODULOS = {}


def _armador(desde=__file__):
    if "armador" not in _CACHE_MODULOS:
        ruta = rutas.localizar(("bin", "contexto-armar.py"), desde)
        if ruta is None:
            raise RefutacionInvalida(
                OUTPUT_INVALID, "no esta contexto-armar.py, de donde sale el validador.")
        spec = importlib.util.spec_from_file_location("contexto_armar_refutacion", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CACHE_MODULOS["armador"] = modulo
    return _CACHE_MODULOS["armador"]


def cargar_schema(nombre, desde=__file__):
    ruta = rutas.localizar(("schemas", nombre), desde)
    if ruta is None:
        raise RefutacionInvalida(
            OUTPUT_INVALID, "no esta %s. Nada se escribe sin poder validarlo." % nombre)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _schema_controlado(nombre, desde):
    """El schema ya pasado por `controlar_soporte`, una vez por archivo y por version en disco.

    Se valida una unidad por regla, y releer y recontrolar el schema en cada una era la mitad
    del tiempo de compilar. La fecha del archivo entra en la llave: un schema que cambia se
    vuelve a controlar.
    """
    ruta = rutas.localizar(("schemas", nombre), desde)
    llave = ("schema", ruta, os.path.getmtime(ruta) if ruta else None)
    if llave not in _CACHE_MODULOS:
        esquema = cargar_schema(nombre, desde)
        _armador(desde).controlar_soporte(esquema)
        _CACHE_MODULOS[llave] = esquema
    return _CACHE_MODULOS[llave]


def validar(doc, nombre, definicion=None, desde=__file__):
    """Errores contra el schema, o contra uno de sus `$defs`. Vacio es valido."""
    armador = _armador(desde)
    esquema = _schema_controlado(nombre, desde)
    sub = esquema["$defs"][definicion] if definicion else esquema
    return armador.validar(doc, sub, "$", esquema)


# -- las fuentes normativas ----------------------------------------------------

def _matrices(desde):
    """{estandar: (documento, version)} de las matrices que esten. Una que falta no voltea."""
    from . import matriz
    from . import seguridad
    salida = {}
    try:
        doc = matriz.cargar(desde)
        salida["ES0901"] = (doc, str((doc.get("standard") or {}).get("version") or ""))
    except Exception:                     # noqa: BLE001 - sin matriz, la regla no se resuelve
        pass
    try:
        doc = seguridad.cargar(desde)
        salida["ES0902"] = (doc, str(doc.get("version") or ""))
    except Exception:                     # noqa: BLE001
        pass
    return salida


def regla_de_matriz(matrices, estandar, regla):
    """(entrada, version) de la regla en su matriz, o (None, None)."""
    doc, version = matrices.get(estandar, (None, None))
    for entrada in (doc or {}).get("rules") or []:
        if entrada.get("id") == regla:
            return entrada, version
    return None, None


def _registro_de_agentes(desde):
    from . import registro_agentes
    try:
        return registro_agentes, registro_agentes.cargar(desde)
    except Exception:                     # noqa: BLE001
        return registro_agentes, {"agents": []}


# Lo que se resuelve una vez por compilacion. `compilar_unidades` lo vacia al empezar: entre
# dos compilaciones una skill puede aparecer, cambiar o irse.
_POR_COMPILACION = {}


def _skills_por_agente(desde):
    """{agente: [(skillId, ruta)]} de las skills instaladas con el archivo en disco."""
    llave = ("skills", desde)
    if llave not in _POR_COMPILACION:
        modulo, doc = _registro_de_agentes(desde)
        indice = {}
        for agente in doc.get("agents") or []:
            for skill in agente.get("skills") or []:
                if skill.get("status") != "INSTALLED":
                    continue
                ruta = modulo._ruta_de(skill.get("file") or "", desde)
                if ruta and os.path.isfile(ruta):
                    indice.setdefault(agente.get("id"), []).append((skill["id"], ruta))
        _POR_COMPILACION[llave] = indice
    return _POR_COMPILACION[llave]


def skill_para(entrada, skills_de_la_unidad, desde):
    """(skillId, ruta) de la skill de la que sale la norma, o (None, None).

    Sale de lo que la matriz declara -los `primaryAgents` de la regla- y del registro de
    agentes -sus skills instaladas con el archivo en disco-. Entre esas, primero las que ya
    tiene la unidad de trabajo, y en orden alfabetico. No se busca texto adentro de ninguna
    skill: elegir por contenido seria una decision de criterio, y esa la toma el refutador.
    """
    por_agente = _skills_por_agente(desde)
    candidatas = []
    for agente_id in (entrada or {}).get("primaryAgents") or []:
        candidatas.extend(por_agente.get(agente_id, []))
    if not candidatas:
        return None, None
    propias = set(skills_de_la_unidad or [])
    candidatas = sorted(set(candidatas), key=lambda c: (c[0] not in propias, c[0]))
    return candidatas[0]


def contrato_del_refutador(desde=__file__):
    """{version, fingerprint} del contrato de dev-refutador. fingerprint None si no esta."""
    from . import registro_agentes
    ruta = registro_agentes._ruta_de(ARCHIVO_DEL_REFUTADOR, desde)
    return {"version": CONTRATO,
            "fingerprint": huella_de_archivo(ruta) if ruta and os.path.isfile(ruta) else None}


def _controles(desde):
    from . import controles
    try:
        return controles.cargar(desde).get("controls") or []
    except Exception:                     # noqa: BLE001
        return []


def claves_de_control(control):
    """Las `ruleKey` a las que esta atado un control, por `source` y por `normativeSources`."""
    claves = set()
    fuente = control.get("source") or {}
    if fuente.get("standard") and fuente.get("rule"):
        claves.add("%s.%s" % (fuente["standard"], fuente["rule"]))
    for otra in control.get("normativeSources") or []:
        if otra.get("ruleKey"):
            claves.add(otra["ruleKey"])
    return claves


# -- el repositorio ------------------------------------------------------------

def revision_del_repo(proyecto):
    """`git rev-parse HEAD`, o None si no es un repositorio. Nunca inventa una."""
    try:
        salida = subprocess.run(["git", "-C", proyecto, "rev-parse", "HEAD"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    texto = salida.stdout.decode("utf-8", "replace").strip()
    return texto if salida.returncode == 0 and re.match(r"^[0-9a-f]{40,64}$", texto) else None


def contexto_del_proyecto(proyecto):
    """(documento, referencia) de docs/codebase/project-context.json, o (None, None)."""
    relativa = "docs/codebase/project-context.json"
    doc, error = _leer_json(os.path.join(proyecto, *relativa.split("/")))
    if not isinstance(doc, dict) or error:
        return None, None
    meta = doc.get("meta") or {}
    return doc, {"path": relativa,
                 "repoRevision": meta.get("repo_revision") if isinstance(
                     meta.get("repo_revision"), str) else None,
                 "contextHash": meta.get("context_hash") if isinstance(
                     meta.get("context_hash"), str) else None}


# -- el alcance ----------------------------------------------------------------

def _ruta_valida(relativa):
    """None si la ruta sirve, o por que no."""
    if not isinstance(relativa, str) or not relativa.strip():
        return "una ruta vacia"
    if "\\" in relativa:
        return "`%s` usa `\\`: las rutas van con `/`" % relativa
    if relativa.startswith("/") or re.match(r"^[A-Za-z]:", relativa):
        return "`%s` es absoluta" % relativa
    partes = relativa.split("/")
    if ".." in partes:
        return "`%s` sube con `..`" % relativa
    if relativa.strip("/") in ("", ".") or all(p in ("", ".") for p in partes):
        return "`%s` es la raiz del proyecto: eso es el repositorio entero" % relativa
    if COMODIN.search(relativa):
        return "`%s` tiene comodines" % relativa
    if SECRETO.search(relativa):
        return "`%s` tiene forma de secreto y no entra a ningun alcance" % relativa
    return None


def _expandir(proyecto, relativa):
    """(archivos, error). Un directorio da sus archivos, en orden estable y sin `.git`."""
    motivo = _ruta_valida(relativa)
    if motivo:
        return [], motivo
    relativa = relativa.strip("/")
    absoluta = os.path.join(proyecto, *relativa.split("/"))
    if os.path.isfile(absoluta):
        return [relativa], None
    if not os.path.isdir(absoluta):
        return [], "`%s` no existe" % relativa
    archivos = []
    for base, dirs, nombres in os.walk(absoluta):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for nombre in sorted(nombres):
            ruta = os.path.relpath(os.path.join(base, nombre), proyecto).replace(os.sep, "/")
            motivo = _ruta_valida(ruta)
            if motivo:
                return [], motivo
            archivos.append(ruta)
    if not archivos:
        return [], "`%s` es un directorio vacio" % relativa
    return archivos, None


def resolver_alcance(proyecto, entrada, contexto=None):
    """(archivos, error) de un alcance declarado. Una ruta que no sirve lo invalida entero.

    No se achica: sacar la ruta mala y seguir con las otras es un alcance que nadie declaro.
    """
    if entrada.get("source") == "projectContext":
        importantes = set(((contexto or {}).get("architecture") or {}).get("important_paths") or [])
        if not contexto:
            return [], "el alcance sale de project-context.json, y no esta o no se puede leer"
        for ruta in entrada.get("paths") or []:
            if ruta not in importantes:
                return [], ("`%s` no esta en architecture.important_paths de "
                            "project-context.json" % ruta)
    archivos = []
    for ruta in entrada.get("paths") or []:
        encontrados, error = _expandir(proyecto, ruta)
        if error:
            return [], error
        archivos.extend(encontrados)
    archivos = sorted(set(archivos))
    if not archivos:
        return [], "el alcance `%s` no declara ninguna ruta" % entrada.get("scopeId")
    if len(archivos) > TOPE_DE_ARCHIVOS:
        return [], ("el alcance `%s` tiene %d archivos, y el tope es %d: eso no es la evidencia "
                    "de una regla" % (entrada.get("scopeId"), len(archivos), TOPE_DE_ARCHIVOS))
    return archivos, None


def huella_de_evidencia(proyecto, archivos, memo=None):
    """La huella de los BYTES del alcance, en orden estable. None si uno no se puede leer.

    `HEAD` no alcanza: con un archivo modificado, en stage o no, `HEAD` no cambia y un
    veredicto viejo pasaria por actual.

    `memo` lo pasa solo el compilador, que vive lo que dura una compilacion: muchas unidades
    comparten archivos. `--record` no lo pasa nunca, porque lo que tiene que ver es el byte de
    ahora.
    """
    partes = []
    for relativa in sorted(archivos):
        h = _huella_memo(os.path.join(proyecto, *relativa.split("/")), memo)
        if h is None:
            return None
        partes.append([relativa, h])
    return huella(partes) if partes else None


def alcances_para(entradas, rule_key):
    """Los alcances que valen para esta regla: los de la fuente mas prioritaria que tenga."""
    propios = [e for e in entradas if not e.get("rules") or rule_key in e["rules"]]
    for fuente in FUENTES:
        de_esta = [e for e in propios if e.get("source") == fuente]
        if de_esta:
            return sorted(de_esta, key=lambda e: e["scopeId"])
    return []


# -- el compilador -------------------------------------------------------------

def _bloques(normative):
    """[(estandar, version, bloque)] de una unidad del plan. Sin `standards`, el de arriba."""
    normative = normative if isinstance(normative, dict) else {}
    estandares = normative.get("standards")
    if isinstance(estandares, dict) and estandares:
        return [(sid, str((b.get("standard") or {}).get("version") or "") or None, b)
                for sid, b in sorted(estandares.items()) if isinstance(b, dict)]
    sid = str((normative.get("standard") or {}).get("id") or "ES0901")
    return [(sid, str((normative.get("standard") or {}).get("version") or "") or None, normative)]


def _reglas_del_bloque(bloque):
    """[(regla, aplicable)]: las aplicables y las que no se pudieron decidir."""
    salida = [(str(r), True) for r in bloque.get("applicableRules") or []]
    salida += [(str(r.get("rule")), False) for r in bloque.get("unresolvedRules") or []
               if isinstance(r, dict) and r.get("rule")]
    return salida


def _afirmacion(rule_key, entrada):
    intencion = (entrada or {}).get("operationalIntentEn")
    texto = "The evidence scope complies with %s" % rule_key
    return texto + (": " + intencion if intencion else ".")


def clave_de_cache(unidad):
    """La clave exacta, o None si falta algo. Cada huella entra; ninguna se promedia."""
    partes = {
        "schema": VERSION_UNIDAD,
        "claim": unidad["claim"],
        "standard": unidad["standard"]["id"],
        "standardVersion": unidad["standard"]["version"],
        "ruleKey": unidad["standard"]["ruleKey"],
        "skillFingerprint": unidad["skillFingerprint"],
        "normativeSourceFingerprint": unidad["normativeSourceFingerprint"],
        "evidenceFingerprint": unidad["evidenceFingerprint"],
        "repoRevision": unidad["repoRevision"],
        "refuterContract": unidad["refuterContract"],
    }
    if not all(partes[k] for k in ("skillFingerprint", "normativeSourceFingerprint",
                                   "evidenceFingerprint")):
        return None
    if not unidad["refuterContract"].get("fingerprint"):
        return None
    return huella(partes)


def _entradas_de(proyecto, clave, desde):
    """(scope, checks, avisos) de lo que declaro quien ejecuto. Lo invalido no se usa."""
    carpeta = carpeta_de(proyecto, clave)
    avisos = []
    scope, error = _leer_json(os.path.join(carpeta, ALCANCE))
    if error or (scope is not None and validar(scope, SCHEMA_UNIDAD, "scopeInput", desde)):
        avisos.append(aviso(SCOPE_UNRESOLVED, ALCANCE))
        scope = None
    checks, error = _leer_json(os.path.join(carpeta, CHECKS))
    if error or (checks is not None and validar(checks, SCHEMA_UNIDAD, "checksInput", desde)):
        avisos.append(aviso(CHECK_UNRESOLVED, CHECKS))
        checks = None
    return (scope or {}).get("workUnits") or {}, (checks or {}).get("results") or [], avisos


def compilar_unidades(proyecto, plan, scope, desde=__file__):
    """Las unidades del plan, sin veredictos. Mismas entradas, mismas unidades."""
    _POR_COMPILACION.clear()
    matrices = _matrices(desde)
    contrato = contrato_del_refutador(desde)
    revision = revision_del_repo(proyecto)
    contexto, ref_contexto = contexto_del_proyecto(proyecto)
    meta = plan.get("meta") or {}

    crudas = []
    for wu in plan.get("workUnits") or []:
        wu_id = str(wu.get("id") or "")
        normative = wu.get("normative") if isinstance(wu.get("normative"), dict) else {}
        entradas = scope.get(wu_id) or []
        for estandar, version, bloque in _bloques(normative):
            for regla, aplicable in _reglas_del_bloque(bloque):
                rule_key = "%s.%s" % (estandar, regla)
                alcances = alcances_para(entradas, rule_key) or [None]
                for entrada in alcances:
                    crudas.append((wu_id, rule_key, (entrada or {}).get("scopeId") or "",
                                   estandar, version, regla, aplicable, entrada, wu, bloque))

    crudas.sort(key=lambda c: (c[0], c[1], c[2]))
    memo = {}
    unidades = []
    for i, (wu_id, rule_key, _, estandar, version, regla, aplicable, entrada, wu,
            bloque) in enumerate(crudas, 1):
        entrada_matriz, version_matriz = regla_de_matriz(matrices, estandar, regla)
        skill_id, ruta_skill = skill_para(entrada_matriz, wu.get("skills"), desde)
        archivos, error_alcance = ([], "la unidad de trabajo %s no declara alcance en %s"
                                   % (wu_id, ALCANCE)) if entrada is None else \
            resolver_alcance(proyecto, entrada, contexto)
        huella_ev = huella_de_evidencia(proyecto, archivos, memo) if archivos else None
        if archivos and huella_ev is None:
            archivos, error_alcance = [], "un archivo del alcance no se pudo leer"
        normativa = wu.get("normative") or {}
        unidad = {
            "schema_version": VERSION_UNIDAD,
            "refutationUnitId": "REF-%03d" % i,
            "taskKey": str(meta.get("task_key") or ""),
            "planId": str(meta.get("plan_id") or ""),
            "planVersion": int(meta.get("plan_version") or 1),
            "workUnitId": wu_id,
            "claim": _afirmacion(rule_key, entrada_matriz),
            "standard": {"id": estandar, "version": version_matriz or version, "rule": regla,
                         "ruleKey": rule_key},
            "skillId": skill_id,
            "skillFingerprint": _huella_memo(ruta_skill, memo) if ruta_skill else None,
            "normativeSourceFingerprint": (huella({"standard": estandar,
                                                   "version": version_matriz,
                                                   "rule": entrada_matriz})
                                           if entrada_matriz else None),
            "declaredChecks": sorted(set(list(bloque.get("declaredChecks") or [])
                                         + list(normativa.get("declaredChecks") or [])
                                         + list(wu.get("requiredChecks") or []))),
            "declaredReviews": sorted(set(list(bloque.get("declaredReviews") or [])
                                          + list(normativa.get("declaredReviews") or []))),
            "checkRefs": [],
            "verificationMode": "REVIEW" if (entrada_matriz or {}).get("reviews") else
                                "INTERPRETATION",
            "evidenceScope": {"scopeId": (entrada or {}).get("scopeId"),
                              "source": (entrada or {}).get("source"),
                              "paths": archivos if not error_alcance else []},
            "scopeState": ALCANCE_SIN_RESOLVER if error_alcance else ALCANCE_RESUELTO,
            "repoRevision": revision,
            "evidenceFingerprint": None if error_alcance else huella_ev,
            "projectContextRef": ref_contexto,
            "refuterContract": contrato,
            "cacheKey": None,
            "status": PENDIENTE,
            "resolutionPath": None,
            "failure": None,
            "failureDetail": None,
        }
        # El orden de las fallas es el de la pregunta: primero si la regla se sabe, despues si
        # hay donde mirar, despues con que norma, despues quien mira.
        if not aplicable or entrada_matriz is None:
            _bloquear(unidad, RULE_UNRESOLVED,
                      "no se sabe si %s aplica: su aplicabilidad esta sin resolver en el plan"
                      % rule_key if not aplicable else
                      "%s no esta en la matriz instalada de %s" % (rule_key, estandar))
        elif error_alcance:
            _bloquear(unidad, SCOPE_UNRESOLVED, error_alcance)
        elif skill_id is None:
            _bloquear(unidad, SKILL_UNAVAILABLE,
                      "ninguna skill instalada de los agentes de %s esta en disco" % rule_key)
        elif not contrato["fingerprint"]:
            _bloquear(unidad, REFUTER_UNAVAILABLE, "no esta %s" % ARCHIVO_DEL_REFUTADOR)
        unidad["cacheKey"] = clave_de_cache(unidad) if unidad["status"] != BLOQUEADA else None
        unidades.append(unidad)
    return unidades


def _bloquear(unidad, codigo, detalle):
    unidad["status"] = BLOQUEADA
    unidad["failure"] = codigo
    unidad["failureDetail"] = detalle


# -- los checks ----------------------------------------------------------------

def resolver_por_checks(unidad, resultados, controles_registrados, matrices):
    """El veredicto que dan los checks, o None si no alcanzan. Llena `checkRefs` siempre.

    Cierra solo si el control esta instalado, atado a la misma regla, declarado por la matriz
    para esa regla y por la unidad, con la huella y la revision de ahora, en un estado
    concluyente, y si la regla no pide una review. Un check sin resolver nunca es `cumple`.
    """
    rule_key = unidad["standard"]["ruleKey"]
    entrada, _ = regla_de_matriz(matrices, unidad["standard"]["id"], unidad["standard"]["rule"])
    de_la_matriz = set((entrada or {}).get("checks") or [])
    instalados = {c["id"]: c for c in controles_registrados
                  if c.get("type") == "CHECK" and c.get("status") == "INSTALLED"}
    exigidos = sorted(c for c in de_la_matriz if c in instalados)

    usados = []
    for r in resultados:
        if r.get("ruleKey") != rule_key:
            continue
        if r.get("workUnitId") not in (None, unidad["workUnitId"]):
            continue
        control = instalados.get(r.get("control"))
        atado = (control is not None and rule_key in claves_de_control(control)
                 and r["control"] in de_la_matriz and r["control"] in unidad["declaredChecks"])
        actual = (r.get("evidenceFingerprint") == unidad["evidenceFingerprint"]
                  and r.get("repoRevision") == unidad["repoRevision"])
        concluyente = r.get("state") in CONCLUYENTES
        unidad["checkRefs"].append({"control": str(r.get("control")), "state": str(r.get("state")),
                                    "bound": bool(atado), "current": bool(actual),
                                    "conclusive": bool(concluyente)})
        if atado and actual and concluyente:
            usados.append(r)
    unidad["checkRefs"].sort(key=lambda c: (c["control"], c["state"]))

    if unidad["verificationMode"] == "REVIEW" or not usados:
        return None
    estados = {}
    for r in usados:
        estados.setdefault(r["control"], set()).add(r["state"])
    if any("FAIL" in s for s in estados.values()):
        veredicto = INCUMPLE
    elif exigidos and all(estados.get(c) == {"PASS"} for c in exigidos):
        veredicto = CUMPLE
    else:
        return None
    usados = sorted(usados, key=lambda r: (r["control"], r["state"]))
    return {
        "schema_version": VERSION_VEREDICTO,
        "refutationUnitId": unidad["refutationUnitId"],
        "workUnitId": unidad["workUnitId"],
        "ruleKey": rule_key,
        "verdict": veredicto,
        "reason": None,
        "citation": {"skillId": unidad["skillId"] or "",
                     "locator": "check:" + ",".join(sorted(estados))},
        "evidence": [{"path": "check:%s" % r["control"], "line": None, "observed": r["state"]}
                     for r in usados],
        "needed": None,
        "cacheKey": unidad["cacheKey"],
        "evidenceFingerprint": unidad["evidenceFingerprint"],
        "repoRevision": unidad["repoRevision"],
        "resolutionPath": POR_CHECK,
        "cacheHit": False,
        "checkEvidenceFingerprint": huella(usados),
        "skillFingerprint": unidad["skillFingerprint"],
        "normativeSourceFingerprint": unidad["normativeSourceFingerprint"],
    }


# -- la cache ------------------------------------------------------------------

def _archivo_de_cache(proyecto, cache_key):
    return os.path.join(carpeta_de_cache(proyecto), cache_key.split(":", 1)[-1] + ".json")


def buscar_en_cache(proyecto, unidad, desde=__file__):
    """(veredicto, aviso). Un acierto solo si la entrada valida y cada huella coincide."""
    if not unidad.get("cacheKey"):
        return None, None
    ruta = _archivo_de_cache(proyecto, unidad["cacheKey"])
    guardado, error = _leer_json(ruta)
    if guardado is None and error is None:
        return None, None
    motivo = None
    if error or not isinstance(guardado, dict):
        motivo = "UNREADABLE"
    elif validar(guardado, SCHEMA_VEREDICTO, desde=desde):
        motivo = "SCHEMA_INVALID"
    elif guardado.get("cacheKey") != unidad["cacheKey"]:
        motivo = "cacheKey"
    elif guardado.get("verdict") not in REUSABLES:
        motivo = "NOT_REUSABLE"
    else:
        for campo in ("evidenceFingerprint", "repoRevision", "ruleKey"):
            esperado = unidad["standard"]["ruleKey"] if campo == "ruleKey" else unidad[campo]
            if guardado.get(campo) != esperado:
                motivo = campo
                break
        for campo in ("skillFingerprint", "normativeSourceFingerprint"):
            if not motivo and guardado.get(campo) != unidad[campo]:
                motivo = campo
    if motivo:
        return None, aviso(CACHE_INVALID, unidad["refutationUnitId"], motivo)
    reusado = dict(guardado)
    reusado.update({"refutationUnitId": unidad["refutationUnitId"],
                    "workUnitId": unidad["workUnitId"],
                    "resolutionPath": POR_CACHE, "cacheHit": True})
    return reusado, None


def guardar_en_cache(proyecto, veredicto):
    if veredicto.get("verdict") not in REUSABLES or not veredicto.get("cacheKey"):
        return None
    entrada = dict(veredicto, cacheHit=False)
    return _escribir(_archivo_de_cache(proyecto, veredicto["cacheKey"]), entrada)


# -- la agregacion -------------------------------------------------------------

def agregar(unidades, veredictos):
    """(estado, contadores). Sin modelo, y el orden de entrada no cambia nada."""
    por_id = {v["refutationUnitId"]: v for v in veredictos}
    cuentas = {"units": 0, "cumple": 0, "incumple": 0, "sinVerificar": 0, "cacheHits": 0,
               "checkResolved": 0, "semanticRuns": 0, "pending": 0, "blocked": 0}
    for u in sorted(unidades, key=lambda x: x["refutationUnitId"]):
        cuentas["units"] += 1
        v = por_id.get(u["refutationUnitId"]) if u["status"] == RESUELTA else None
        veredicto = v["verdict"] if v else SIN_VERIFICAR
        cuentas[{"cumple": "cumple", "incumple": "incumple"}.get(veredicto, "sinVerificar")] += 1
        if u["status"] == PENDIENTE:
            cuentas["pending"] += 1
        elif u["status"] == BLOQUEADA:
            cuentas["blocked"] += 1
        camino = (v or {}).get("resolutionPath")
        if camino == POR_CACHE:
            cuentas["cacheHits"] += 1
        elif camino == POR_CHECK:
            cuentas["checkResolved"] += 1
        elif camino == SEMANTICA:
            cuentas["semanticRuns"] += 1
    if not cuentas["units"]:
        return NADA, cuentas
    if cuentas["incumple"]:
        return FALLA, cuentas
    if cuentas["cumple"] == cuentas["units"]:
        return PASA, cuentas
    return INCOMPLETA, cuentas


def corrida(plan, unidades, veredictos, avisos, contrato, revision):
    estado, cuentas = agregar(unidades, veredictos)
    por_id = {v["refutationUnitId"]: v for v in veredictos}
    meta = plan.get("meta") or {}
    doc = {
        "meta": {"schema_version": VERSION_CORRIDA,
                 "taskKey": str(meta.get("task_key") or ""),
                 "planId": str(meta.get("plan_id") or ""),
                 "planVersion": int(meta.get("plan_version") or 1),
                 "planFingerprint": huella(plan),
                 "repoRevision": revision,
                 "refuterContract": contrato},
        "status": estado,
        "counts": cuentas,
        "units": [{"refutationUnitId": u["refutationUnitId"], "workUnitId": u["workUnitId"],
                   "ruleKey": u["standard"]["ruleKey"],
                   "scopeId": u["evidenceScope"]["scopeId"], "status": u["status"],
                   "resolutionPath": u["resolutionPath"],
                   "verdict": (por_id.get(u["refutationUnitId"]) or {}).get("verdict")
                   if u["status"] == RESUELTA else None,
                   "failure": u["failure"]} for u in unidades],
        "warnings": sorted(set(avisos)),
    }
    if estado == NADA:
        doc["warnings"] = sorted(set(doc["warnings"] + [aviso(NOTHING_TO_VERIFY)]))
    return doc


# -- compilar, de punta a punta ------------------------------------------------

def _leer_plan(proyecto, clave):
    plan, error = _leer_json(ruta_del_plan(proyecto, clave))
    if plan is None:
        raise RefutacionInvalida(
            RULE_UNRESOLVED, "no hay plan para %s%s. Corré primero `plan %s --propuesta ...`."
            % (clave, " legible (%s)" % error if error else "", clave))
    return plan


def _veredictos_guardados(carpeta):
    salida = []
    dir_v = os.path.join(carpeta, "verdicts")
    if not os.path.isdir(dir_v):
        return salida
    for nombre in sorted(os.listdir(dir_v)):
        if nombre.endswith(".json"):
            doc, _ = _leer_json(os.path.join(dir_v, nombre))
            if isinstance(doc, dict):
                salida.append(doc)
    return salida


def _sincronizar(carpeta, subdir, docs):
    """Deja en `subdir` exactamente estos documentos, por id. Lo que sobra se borra."""
    destino = os.path.join(carpeta, subdir)
    nombres = set()
    for doc in docs:
        nombre = doc["refutationUnitId"] + ".json"
        nombres.add(nombre)
        ruta = os.path.join(destino, nombre)
        texto = _como_texto(doc)
        actual = None
        if os.path.isfile(ruta):
            with io.open(ruta, encoding="utf-8") as f:
                actual = f.read()
        if actual != texto:
            _escribir(ruta, doc)
    if os.path.isdir(destino):
        for nombre in os.listdir(destino):
            if nombre.endswith(".json") and nombre not in nombres:
                os.remove(os.path.join(destino, nombre))


def compilar(proyecto, clave, desde=__file__):
    """Compila, resuelve por checks y por cache, y escribe. Devuelve la corrida.

    Un veredicto ya registrado sobrevive si su unidad sigue teniendo la misma clave de cache;
    si no, deja de valer y se avisa. Dos compilaciones seguidas dejan los mismos bytes.
    """
    clave = validar_clave(clave)
    carpeta = carpeta_de(proyecto, clave)
    plan = _leer_plan(proyecto, clave)
    scope, resultados, avisos = _entradas_de(proyecto, clave, desde)
    unidades = compilar_unidades(proyecto, plan, scope, desde)
    matrices = _matrices(desde)
    registrados = _controles(desde)

    anteriores = {}
    for v in _veredictos_guardados(carpeta):
        if v.get("resolutionPath") == SEMANTICA:
            anteriores.setdefault((v.get("workUnitId"), v.get("ruleKey")), []).append(v)

    veredictos = []
    for u in unidades:
        if u["status"] == BLOQUEADA:
            continue
        previos = anteriores.get((u["workUnitId"], u["standard"]["ruleKey"]), [])
        previo = next((v for v in previos if v.get("cacheKey") == u["cacheKey"]), None)
        if previos and previo is None:
            avisos.append(aviso(EVIDENCE_STALE, u["workUnitId"], u["standard"]["ruleKey"]))
        # Siempre, aunque haya un veredicto previo: `checkRefs` es parte de la unidad, y
        # compilar despues de registrar tiene que dejar la misma unidad que registrar.
        por_check = resolver_por_checks(u, resultados, registrados, matrices)
        if previo is not None:
            _resolver(u, dict(previo, refutationUnitId=u["refutationUnitId"]), veredictos)
            continue
        if por_check is not None:
            _resolver(u, por_check, veredictos)
            continue
        if any(not (c["bound"] and c["current"] and c["conclusive"]) for c in u["checkRefs"]):
            avisos.append(aviso(CHECK_UNRESOLVED, u["refutationUnitId"]))
        reusado, de_cache = buscar_en_cache(proyecto, u, desde)
        if de_cache:
            avisos.append(de_cache)
        if reusado is not None:
            _resolver(u, reusado, veredictos)

    for u in unidades:
        errores = validar(u, SCHEMA_UNIDAD, desde=desde)
        if errores:
            raise RefutacionInvalida(OUTPUT_INVALID, "la unidad %s no valida: %s"
                                     % (u["refutationUnitId"], "; ".join(errores[:3])))
    for v in veredictos:
        errores = validar(v, SCHEMA_VEREDICTO, desde=desde)
        if errores:
            raise RefutacionInvalida(OUTPUT_INVALID, "el veredicto de %s no valida: %s"
                                     % (v["refutationUnitId"], "; ".join(errores[:3])))

    contrato = contrato_del_refutador(desde)
    doc = corrida(plan, unidades, veredictos, avisos, contrato, revision_del_repo(proyecto))
    errores = validar(doc, SCHEMA_CORRIDA, desde=desde)
    if errores:
        raise RefutacionInvalida(OUTPUT_INVALID, "la corrida no valida: %s"
                                 % "; ".join(errores[:3]))
    _sincronizar(carpeta, "units", unidades)
    _sincronizar(carpeta, "verdicts", veredictos)
    _escribir(os.path.join(carpeta, CORRIDA), doc)
    return doc


def _resolver(unidad, veredicto, veredictos):
    unidad["status"] = RESUELTA
    unidad["resolutionPath"] = veredicto["resolutionPath"]
    veredictos.append(veredicto)


# -- leer lo compilado ---------------------------------------------------------

def leer(proyecto, clave):
    """(corrida, unidades, veredictos). Levanta si no se compilo."""
    carpeta = carpeta_de(proyecto, clave)
    doc, error = _leer_json(os.path.join(carpeta, CORRIDA))
    if doc is None:
        raise RefutacionInvalida(
            NOTHING_TO_VERIFY, "no hay corrida de refutacion para %s%s. Corré primero "
            "`refute %s --compile`." % (clave, " legible (%s)" % error if error else "", clave))
    unidades = []
    dir_u = os.path.join(carpeta, "units")
    for nombre in sorted(os.listdir(dir_u)) if os.path.isdir(dir_u) else []:
        if nombre.endswith(".json"):
            u, _ = _leer_json(os.path.join(dir_u, nombre))
            if isinstance(u, dict):
                unidades.append(u)
    return doc, unidades, _veredictos_guardados(carpeta)


def unidad(proyecto, clave, ref_id):
    _, unidades, _ = leer(proyecto, clave)
    for u in unidades:
        if u["refutationUnitId"] == ref_id:
            return u
    raise RefutacionInvalida(OUTPUT_INVALID, "la unidad %s no existe en %s." % (ref_id, clave))


def para_refutar(proyecto, clave, ids):
    """La unidad a entregar, o el sobre de un micro-lote. Solo unidades pendientes."""
    ids = [i.strip() for i in (ids if isinstance(ids, list) else str(ids).split(",")) if i.strip()]
    if not ids or any(not ID_DE_UNIDAD.match(i) for i in ids):
        raise RefutacionInvalida(OUTPUT_INVALID, "se esperaba REF-001 o REF-001,REF-002.")
    elegidas = [unidad(proyecto, clave, i) for i in ids]
    for u in elegidas:
        if u["status"] != PENDIENTE:
            raise RefutacionInvalida(
                OUTPUT_INVALID, "%s esta %s%s: no hay nada que entregarle al refutador." % (
                    u["refutationUnitId"], u["status"],
                    " (%s)" % u["failure"] if u["failure"] else ""))
    if len(elegidas) == 1:
        return elegidas[0]
    micro_lote(elegidas)
    return {"units": elegidas}


# -- el micro-lote -------------------------------------------------------------

CAMPOS_DE_LOTE = ("ruleKey", "skillId", "evidenceFingerprint", "repoRevision", "verificationMode")


def _campo_de_lote(u, campo):
    return u["standard"]["ruleKey"] if campo == "ruleKey" else u[campo]


def micro_lote(unidades):
    """Levanta si estas unidades no pueden viajar juntas. Nunca dos reglas distintas."""
    if len(unidades) < 2:
        return unidades
    primera = unidades[0]
    for u in unidades[1:]:
        for campo in CAMPOS_DE_LOTE:
            if _campo_de_lote(u, campo) != _campo_de_lote(primera, campo):
                raise RefutacionInvalida(
                    BATCH_INVALID, "%s y %s no comparten `%s`: no van en el mismo lote." % (
                        primera["refutationUnitId"], u["refutationUnitId"], campo))
    return unidades


# -- registrar lo que devolvio el refutador ------------------------------------

def parsear_salida(texto):
    """El objeto (o el arreglo) y nada mas. Prosa, un bloque de codigo o JSON roto se rechazan."""
    crudo = (texto or "").strip()
    if not crudo.startswith(("{", "[")):
        raise RefutacionInvalida(
            OUTPUT_INVALID, "la salida del refutador no es un objeto JSON: trae algo antes.")
    try:
        return json.loads(crudo)
    except ValueError as e:
        raise RefutacionInvalida(
            OUTPUT_INVALID, "la salida del refutador no es JSON valido, o trae algo despues: %s"
            % e)


def _huellas_de_ahora(proyecto, u, desde):
    """Lo que la unidad diria si se compilara ahora: huella, revision, skill y contrato."""
    from . import registro_agentes
    modulo, doc = _registro_de_agentes(desde)
    ruta_skill = None
    for agente in doc.get("agents") or []:
        for s in agente.get("skills") or []:
            if s.get("id") == u["skillId"]:
                ruta_skill = modulo._ruta_de(s.get("file") or "", desde)
    return {"evidenceFingerprint": huella_de_evidencia(proyecto, u["evidenceScope"]["paths"]),
            "repoRevision": revision_del_repo(proyecto),
            "skillFingerprint": huella_de_archivo(ruta_skill) if ruta_skill else None,
            "refuterContract": contrato_del_refutador(desde)}


def validar_veredicto(proyecto, u, v, desde=__file__):
    """Levanta con OUTPUT_INVALID o EVIDENCE_STALE. Devuelve el veredicto limpio."""
    if not isinstance(v, dict):
        raise RefutacionInvalida(OUTPUT_INVALID, "un veredicto es un objeto.")
    del_harness = sorted(c for c in CAMPOS_DEL_HARNESS if c in v)
    if del_harness:
        raise RefutacionInvalida(
            OUTPUT_INVALID, "el veredicto trae %s, que solo escribe el harness."
            % ", ".join(del_harness))
    errores = validar(v, SCHEMA_VEREDICTO, desde=desde)
    if errores:
        raise RefutacionInvalida(OUTPUT_INVALID, "no valida contra %s: %s"
                                 % (VERSION_VEREDICTO, "; ".join(errores[:3])))
    if u["status"] != PENDIENTE:
        raise RefutacionInvalida(OUTPUT_INVALID, "%s no esta pendiente de refutacion semantica."
                                 % u["refutationUnitId"])
    for campo, esperado in (("refutationUnitId", u["refutationUnitId"]),
                            ("workUnitId", u["workUnitId"]),
                            ("ruleKey", u["standard"]["ruleKey"])):
        if v.get(campo) != esperado:
            raise RefutacionInvalida(
                OUTPUT_INVALID, "`%s` es `%s` y la unidad dice `%s`: el refutador no cambia de "
                "afirmacion ni descubre otra regla." % (campo, v.get(campo), esperado))
    for campo in ("cacheKey", "evidenceFingerprint", "repoRevision"):
        if v.get(campo) != u[campo]:
            raise RefutacionInvalida(
                EVIDENCE_STALE, "`%s` del veredicto no es el de la unidad: se hizo sobre otra "
                "evidencia." % campo)
    ahora_ = _huellas_de_ahora(proyecto, u, desde)
    for campo in ("evidenceFingerprint", "repoRevision", "skillFingerprint", "refuterContract"):
        if ahora_[campo] != u[campo]:
            raise RefutacionInvalida(
                EVIDENCE_STALE, "`%s` cambio desde que se compilo %s. Recompilá y volvé a "
                "refutar." % (campo, u["refutationUnitId"]))

    alcance = set(u["evidenceScope"]["paths"])
    for e in v["evidence"]:
        if e["path"] not in alcance:
            raise RefutacionInvalida(
                OUTPUT_INVALID, "la evidencia `%s` esta fuera del alcance de %s. El refutador no "
                "lee fuera de su unidad." % (e["path"], u["refutationUnitId"]))
    if v["verdict"] in (CUMPLE, INCUMPLE):
        cita = v.get("citation")
        if not cita or cita.get("skillId") != u["skillId"] or not cita.get("locator", "").strip():
            raise RefutacionInvalida(
                OUTPUT_INVALID, "un `%s` necesita la cita de %s con su pagina o seccion. Sin cita "
                "es `sin-verificar`." % (v["verdict"], u["skillId"]))
        concretas = [e for e in v["evidence"] if isinstance(e.get("line"), int)
                     and e["line"] >= 1 and e["observed"].strip()]
        if not concretas:
            raise RefutacionInvalida(
                OUTPUT_INVALID, "un `%s` necesita al menos una evidencia con ruta, linea y lo "
                "observado." % v["verdict"])
        if v.get("reason") is not None:
            raise RefutacionInvalida(OUTPUT_INVALID, "`reason` es solo para sin-verificar.")
    else:
        if v.get("reason") is None or not (v.get("needed") or "").strip():
            raise RefutacionInvalida(
                OUTPUT_INVALID, "un `sin-verificar` dice por que (`reason`) y que hay que abrir o "
                "correr para cerrarlo (`needed`).")
    return _limpiar(v)


def _limpiar(v):
    """Los textos libres, sin secretos y recortados. Nada de afuera entra crudo."""
    from contexto import limpieza
    catalogo = limpieza.cargar_catalogo()
    if catalogo is None:
        raise RefutacionInvalida(
            OUTPUT_INVALID, "no esta el catalogo de secretos: un veredicto no se guarda sin "
            "limpiar.")
    v = json.loads(json.dumps(v))
    for e in v["evidence"]:
        e["observed"] = limpieza.redactar_arbol(e["observed"], catalogo, "$")[0][:TOPE_DE_TEXTO]
    for campo in ("needed",):
        if isinstance(v.get(campo), str):
            v[campo] = limpieza.redactar_arbol(v[campo], catalogo, "$")[0][:TOPE_DE_TEXTO]
    if isinstance(v.get("citation"), dict):
        v["citation"]["locator"] = limpieza.redactar_arbol(
            v["citation"]["locator"], catalogo, "$")[0][:TOPE_DE_TEXTO]
    return v


def registrar(proyecto, clave, texto, desde=__file__):
    """Valida lo que devolvio el refutador y lo guarda. Todo o nada. Devuelve los guardados."""
    salida = parsear_salida(texto)
    lista = salida if isinstance(salida, list) else [salida]
    if not lista:
        raise RefutacionInvalida(OUTPUT_INVALID, "un arreglo vacio no es un veredicto.")
    ids = [v.get("refutationUnitId") if isinstance(v, dict) else None for v in lista]
    if len(set(ids)) != len(ids):
        raise RefutacionInvalida(OUTPUT_INVALID, "un veredicto por unidad, y hay ids repetidos.")
    unidades = [unidad(proyecto, clave, str(i)) for i in ids]
    micro_lote(unidades)
    limpios = [validar_veredicto(proyecto, u, v, desde) for u, v in zip(unidades, lista)]

    carpeta = carpeta_de(proyecto, clave)
    cuando = ahora()
    for u, v in zip(unidades, limpios):
        v.update({"resolutionPath": SEMANTICA, "cacheHit": False, "recordedAt": cuando,
                  "checkEvidenceFingerprint": None,
                  "skillFingerprint": u["skillFingerprint"],
                  "normativeSourceFingerprint": u["normativeSourceFingerprint"]})
        errores = validar(v, SCHEMA_VEREDICTO, desde=desde)
        if errores:
            raise RefutacionInvalida(OUTPUT_INVALID, "; ".join(errores[:3]))
    for u, v in zip(unidades, limpios):
        _escribir(os.path.join(carpeta, "verdicts", u["refutationUnitId"] + ".json"), v)
        guardar_en_cache(proyecto, v)
        u["status"] = RESUELTA
        u["resolutionPath"] = SEMANTICA
        _escribir(os.path.join(carpeta, "units", u["refutationUnitId"] + ".json"), u)
    _reagregar(proyecto, clave)
    return limpios


def _reagregar(proyecto, clave):
    doc, unidades, veredictos = leer(proyecto, clave)
    estado, cuentas = agregar(unidades, veredictos)
    por_id = {v["refutationUnitId"]: v for v in veredictos}
    doc["status"], doc["counts"] = estado, cuentas
    por_unidad = {u["refutationUnitId"]: u for u in unidades}
    for fila in doc["units"]:
        u = por_unidad.get(fila["refutationUnitId"]) or {}
        fila["status"] = u.get("status", fila["status"])
        fila["resolutionPath"] = u.get("resolutionPath")
        fila["verdict"] = ((por_id.get(fila["refutationUnitId"]) or {}).get("verdict")
                           if fila["status"] == RESUELTA else None)
    _escribir(os.path.join(carpeta_de(proyecto, clave), CORRIDA), doc)
    return doc


# -- el Bloque 4 ---------------------------------------------------------------

def atribucion(proyecto, clave, ref_id):
    """Lo que el Bloque 4 le pone a lo ingerido de una corrida del refutador.

    Solo para una unidad que fue, o va a ir, a refutacion semantica. Un acierto de cache o un
    check no llamaron a nadie: atribuirles consumo seria inventar una llamada.
    """
    u = unidad(proyecto, clave, ref_id)
    if u["status"] == BLOQUEADA or u["resolutionPath"] in (POR_CACHE, POR_CHECK):
        raise RefutacionInvalida(
            OUTPUT_INVALID, "%s se resolvio por %s: no hubo llamada al refutador que atribuir."
            % (ref_id, u["resolutionPath"] or u["failure"]))
    return {"workUnitId": u["workUnitId"], "agentId": REFUTADOR,
            "metadata": {"phase": "refutation", "refutationUnitId": u["refutationUnitId"],
                         "resolutionPath": SEMANTICA, "cacheHit": False}}


def de_refutacion(eventos):
    """Los eventos del libro contable que son de la fase de refutacion."""
    return [e for e in eventos if isinstance(e.get("metadata"), dict)
            and e["metadata"].get("phase") == "refutation"]


# -- lo que se muestra ---------------------------------------------------------

COMO_SE_LEE = {PASA: "cumple todo", FALLA: "hay incumplimientos",
               INCOMPLETA: "incompleta: hay afirmaciones sin verificar",
               NADA: "no hay nada que verificar"}
CAMINOS = {POR_CHECK: "check", SEMANTICA: "refutador", POR_CACHE: "caché", None: "—"}
VEREDICTO_LEGIBLE = {CUMPLE: "cumple", INCUMPLE: "incumple", SIN_VERIFICAR: "sin verificar",
                     None: "sin verificar"}


COMO_SE_LEE_EL_AVISO = {
    SCOPE_UNRESOLVED: "{0} no valida y no se usa: ninguna unidad tiene alcance",
    CHECK_UNRESOLVED: "{0}: hay checks que no cierran (sin atar, viejos o no concluyentes), va "
                      "al refutador",
    CACHE_INVALID: "{0}: la entrada de cache no coincide en {1} y no se usa",
    EVIDENCE_STALE: "el veredicto anterior de {0} sobre {1} ya no vale: cambio su evidencia",
    NOTHING_TO_VERIFY: "el plan no tiene reglas aplicables ni sin resolver",
}


def texto_de_aviso(crudo):
    """El aviso de maquina, en espanol. Lo que no se conoce sale tal cual."""
    partes = str(crudo).split(":")
    plantilla = COMO_SE_LEE_EL_AVISO.get(partes[0])
    if plantilla is None:
        return str(crudo)
    try:
        return "%s (%s)" % (plantilla.format(*partes[1:]), partes[0])
    except IndexError:
        return str(crudo)


def texto_de_resumen(doc, bloque4=None):
    """El resumen en espanol. Los estados canonicos van entre parentesis, tal cual."""
    c = doc["counts"]
    lineas = ["",
              "%s — Refutación" % doc["meta"]["taskKey"],
              "-" * 60,
              "Estado       %s (%s)" % (COMO_SE_LEE[doc["status"]], doc["status"]),
              "Unidades     %d · cumple %d · incumple %d · sin verificar %d"
              % (c["units"], c["cumple"], c["incumple"], c["sinVerificar"]),
              "Resueltas    por check %d · por caché %d · por el refutador %d"
              % (c["checkResolved"], c["cacheHits"], c["semanticRuns"]),
              "Abiertas     pendientes del refutador %d · bloqueadas %d"
              % (c["pending"], c["blocked"])]
    if bloque4 is not None:
        lineas.append("")
        lineas.append("Bloque 4, fase de refutación")
        if not bloque4.get("events"):
            lineas.append("  sin eventos: todavía no se ingirió ninguna corrida del refutador")
        else:
            lineas.append("  eventos %d · input %s · output %s" % (
                bloque4["events"], _o_guion(bloque4.get("inputTokens")),
                _o_guion(bloque4.get("outputTokens"))))
            lineas.append("  pared %s ms · modelo %s ms" % (
                _o_guion(bloque4.get("wallMs")), _o_guion(bloque4.get("modelMs"))))
            lineas.append("  costo real %s · equivalente de API %s" % (
                _o_guion(bloque4.get("actual")), _o_guion(bloque4.get("apiEquivalentEstimated"))))
    if doc["warnings"]:
        lineas.append("")
        lineas.append("Avisos")
        lineas.extend("  · " + texto_de_aviso(a) for a in doc["warnings"][:10])
    return "\n".join(lineas)


def texto_de_estado(doc):
    lineas = ["", "%s — unidades de refutación" % doc["meta"]["taskKey"], "-" * 60]
    for u in doc["units"]:
        lineas.append("  %-8s %-12s %-12s %-10s %s%s" % (
            u["refutationUnitId"], u["workUnitId"], u["ruleKey"],
            CAMINOS.get(u["resolutionPath"], "—"),
            VEREDICTO_LEGIBLE.get(u["verdict"], "sin verificar"),
            "  [%s]" % u["failure"] if u["failure"] else ""))
    lineas.append("")
    lineas.append("Estado: %s" % doc["status"])
    return "\n".join(lineas)


def _o_guion(valor):
    return "—" if valor is None else str(valor)
