# Integridad de repositorio: investigar un compromiso sin destruir la escena.
#
# Escenarios E-01 a E-51 de docs/cambios/integridad-de-repositorio/spec.md. Entre parentesis, el
# RI-nn del pedido de instalacion; los cincuenta estan cubiertos.
#
# 🔴 Nada de esto se conecta a un repositorio ni ejecuta nada. Lo que se verifica es la CAPACIDAD:
# que el modo de incidente invierta los defaults, que la rama actual no sea una linea de base, que
# un indicador debil no llegue a malware, que confianza y severidad sean dos ejes, y que un secreto
# no salga en claro de ningun lado.
import ast
import copy
import io
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
RUTA_REG = str(BIN / "orquestacion" / "registro_agentes.py")
RUTA_MOD = BIN / "orquestacion" / "integridad.py"

sys.path.insert(0, str(BIN))
from orquestacion import controles as c_controles   # noqa: E402
from orquestacion import evaluacion as c_evaluacion  # noqa: E402
from orquestacion import integridad as I             # noqa: E402
from orquestacion import matriz as c_matriz          # noqa: E402
from orquestacion import registro_agentes as c_reg   # noqa: E402
from orquestacion import seguridad as c_seguridad    # noqa: E402
from orquestacion import tools as c_tools            # noqa: E402

COMMIT_BASE = "a" * 40
COMMIT_ACTUAL = "b" * 40

BASE = {"repository": "gcba/tramites", "ref": "refs/tags/v1.4.0", "commitSha": COMMIT_BASE,
        "source": "APPROVED_RELEASE", "evidence": ["acta de release del 2026-08-01"],
        "establishedAt": "2026-08-01", "establishedBy": "el equipo de release"}

SECRETO = "valor-en-claro-de-la-credencial-que-no-tiene-que-salir"
PAYLOAD = "cuerpo-entero-del-script-sospechoso-que-tampoco-tiene-que-salir"


def _archivo(path, operacion="MODIFIED", clase="SOURCE", **extra):
    a = {"path": path, "operation": operacion, "kind": clase}
    a.update(extra)
    return a


def _evidencia(archivos=None, destinos=("destino-nuevo.example",), **extra):
    e = {
        "repository": "gcba/tramites", "ref": "refs/heads/trabajo",
        "commitSha": COMMIT_ACTUAL, "parents": [COMMIT_BASE],
        "commits": [{"sha": COMMIT_ACTUAL, "parents": [COMMIT_BASE], "author": "alguien",
                     "timestamp": "2026-09-20", "verified": False}],
        "changedFiles": [_archivo("src/app.py", afterHash="h-app", beforeHash="h-app-viejo")]
        if archivos is None else list(archivos),
        "networkDestinations": list(destinos),
        "manifests": ["package.json"], "pipelines": [".ci/deploy.yml"],
        "diffMeta": {"additions": 12, "deletions": 3},
        "timestamp": "2026-09-20T10:00:00Z",
    }
    e.update(extra)
    return e


def _senal(categoria="DYNAMIC_CODE_EXECUTION", indicadores=("EVAL_PRESENT",), directa=False,
           **extra):
    s = {"id": "f-1", "category": categoria, "indicators": list(indicadores),
         "evidence": ["diff de src/app.py, lineas 10-14"], "directEvidence": directa,
         "file": "src/app.py", "location": "10-14"}
    s.update(extra)
    return s


def _confirmada():
    """Una senal con evidencia directa citada y dos indicadores que no son debiles."""
    return _senal(indicadores=("REVERSE_SHELL_ESTABLISHED", "CREDENTIAL_SENT_OFF_HOST"),
                  directa=True, directEvidenceReference="captura de trafico del incidente #7")


# Las claves que un hallazgo lleva, exactamente. Clavadas acá para que agregar un campo —o
# copiar la senal en crudo adentro de uno— tenga que pasar por este test.
CLAVES_DE_HALLAZGO = (
    "findingId", "reviewId", "repository", "baselineCommit", "currentCommit", "commits",
    "file", "location", "beforeHash", "afterHash", "category", "indicators", "pipelineFacts",
    "supplyChainFacts", "weakIndicators", "status", "confidence", "severity", "evidence",
    "reasoningSummary", "recommendedNextAction", "requiresHumanReview", "severityState")

MAPEO = {"authoritative": True, "evidence": ["acta de mapeo de severidades del 2026-07"],
         "source": "ES0902", "map": {"critical": "CRITICAL", "high": "HIGH",
                                     "medium": "MEDIUM", "low": "LOW"}}


def _literales(ruta, con_docstrings=False):
    """Las cadenas literales de un modulo, sin los docstrings."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docs = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        cuerpo = getattr(nodo, "body", None) or []
        if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)):
            docs.add(id(cuerpo[0].value))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and (con_docstrings or id(n) not in docs)]


# -- E-01 a E-04 — ni regla, ni agente, ni skill, ni aprobacion ----------------

def test_e01_no_es_una_regla(t):
    """E-01 (RI-01) — ni en la matriz de ES0902, ni en la de ES0901, ni en el registro."""
    ids = ("repository-integrity-review", "repository-integrity", "integridad")
    es0902 = c_seguridad.cargar()
    texto_0902 = json.dumps(es0902, ensure_ascii=False)
    for cid in ids:
        t.verdadero("E-01 la matriz de ES0902 no la declara: %s" % cid, cid not in texto_0902)
    texto_0901 = json.dumps(c_matriz.cargar(), ensure_ascii=False)
    for cid in ids:
        t.verdadero("E-01 la matriz de ES0901 tampoco: %s" % cid, cid not in texto_0901)

    registro = c_controles.cargar()
    declarados = {c.get("id") for c in registro.get("controls", [])}
    for cid in ids:
        t.verdadero("E-01 el registro de controles no la declara: %s" % cid,
                    cid not in declarados)
    # Y no aparece como archivo de control sin declarar: no vive en `controles/`.
    t.igual("E-01 ningun archivo de control suelto", [],
            c_controles.reporte()["undeclared"])
    t.verdadero("E-01 el modulo vive en la orquestacion, no en controles/",
                RUTA_MOD.exists() and "controles" not in str(RUTA_MOD.parent))


def test_e02_no_crea_ningun_agente(t):
    """E-02 (RI-02) — el registro sigue igual y el modulo no declara uno nuevo."""
    registro = c_reg.cargar(RUTA_REG)
    agentes = {a["id"] for a in registro["agents"]}
    t.verdadero("E-02 dev-security ya estaba", "dev-security" in agentes)
    t.igual("E-02 el modulo nombra al agente que ya existe", "dev-security", I.AGENTE)
    fuente = RUTA_MOD.read_text(encoding="utf-8")
    for mencionado in sorted(set(re.findall(r"\bdev-[a-z-]+\b", fuente))):
        t.verdadero("E-02 %s ya esta en el registro" % mencionado,
                    mencionado in agentes or mencionado in
                    {s["id"] for a in registro["agents"] for s in a.get("skills") or []})
    t.vacio("E-02 el modulo no declara un inventario de agentes",
            re.findall(r"(?i)\bagents\s*[:=]\s*[\"'\[]", fuente))


def test_e03_las_skills_de_seguridad_siguen_siendo_las_autoritativas(t):
    """E-03 (RI-03) — las tres rutean, y siguen siendo 27 las instaladas."""
    TRES = ("dev-security-assessment", "dev-appsec-review", "dev-vulnerability-management")
    t.igual("E-03 son estas tres las que la capacidad usa", TRES, I.SKILLS)
    for pedido in I.skills_de_ejecucion():
        t.igual("E-03 %s rutea" % pedido["requestedSkill"], "ROUTABLE", pedido["result"])
        t.verdadero("E-03 %s es routable" % pedido["requestedSkill"], pedido["routable"])
        t.igual("E-03 y lo pide la capacidad", "repository-integrity-review",
                pedido["requestedFor"])
    t.igual("E-03 siguen siendo 27 las skills instaladas", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.vacio("E-03 el modulo no declara un inventario de skills",
            re.findall(r"(?i)\bskills\s*[:=]\s*[\"'\[]",
                       "\n".join(_literales(RUTA_MOD))))
    # Y el hueco, si alguna vez falta una, se declara con el estado que ya existe.
    t.igual("E-03 el hueco de skill usa el estado existente", "SPECIALIZED_SKILL_GAP",
            I.HUECO_DE_SKILL)


def test_e04_un_pass_no_es_una_aprobacion(t):
    """E-04 (RI-47) — el resultado no lleva estado oficial y no mueve el de ES0902."""
    # 🔴 El estado oficial se captura ANTES de la revision. Capturarlo despues y compararlo
    # contra otra llamada a la misma funcion pura es una tautologia: no puede fallar, y una
    # capacidad que secuestrara lo que `evaluacion` resuelve pasaba igual.
    #
    # 🔴 Y no alcanza con `estado_oficial(None)`: esa llamada vuelve temprano leyendo la constante
    # `SIN_RESOLVER` y no pasa por la particion de productores, asi que una revision que vaciara
    # `PRODUCTORES_INTERNOS` —o que reemplazara `estado_oficial` por una que acierta con None y
    # aprueba todo lo demas— pasaba verde (segundo veredicto). Lo que se captura es la RESOLUCION
    # de un conjunto representativo de declaraciones, mas la identidad de las funciones y de las
    # constantes de las que esa resolucion depende.
    # Lo que cada declaracion resuelve, clavado por literal: el antes/despues atrapa lo que la
    # revision cambie, y el literal atrapa lo que ya estuviera cambiado al entrar.
    INTERNOS = ("AUTOMATED_SCAN", "INTERNAL_SECURITY_REVIEW", "HARNESS_CHECK",
                "HARNESS_THRESHOLD_CALCULATION", "DEV_SECURITY_AGENT")
    EXTERNOS = ("GCBA_DGSEI", "GCBA_SECURITY_AUTHORITY", "ASI")
    SIN = "OFFICIAL_STATUS_UNRESOLVED"
    declaraciones = [(None, SIN), ({}, SIN),
                     ({"state": "PASS", "producer": "AUTOMATED_SCAN", "evidence": ["x"]}, SIN),
                     ({"state": "NO_SUSPICIOUS_CHANGE_FOUND", "producer": "DEV_SECURITY_AGENT",
                       "evidence": ["x"]}, SIN),
                     ({"state": "INTERNAL_ASSESSMENT", "producer": "DEV_SECURITY_AGENT"},
                      "INTERNAL_ASSESSMENT"),
                     ({"state": "APPROVED", "producer": "repository-integrity-review",
                       "evidence": ["x"]}, SIN),
                     ({"state": "APPROVED", "producer": None, "evidence": ["x"]}, SIN),
                     ({"state": "APPROVED", "producer": "GCBA_DGSEI"}, SIN)]
    for oficial in ("REQUESTED", "IN_ASSESSMENT", "RESUBMITTED", "APPROVED", "REJECTED"):
        for productor in INTERNOS:
            declaraciones.append(({"state": oficial, "producer": productor,
                                   "evidence": ["x"]}, SIN))
        for productor in EXTERNOS:
            declaraciones.append(({"state": oficial, "producer": productor,
                                   "evidence": ["acta de %s" % productor]}, oficial))

    def _resoluciones():
        # Tambien SIN argumento: una revision que reescribiera `__defaults__` para que la
        # declaracion por omision fuera un APPROVED no se ve pasando None a mano (tercer veredicto).
        return [json.dumps(c_evaluacion.estado_oficial(), sort_keys=True),
                json.dumps(c_evaluacion.resultado_interno(), sort_keys=True)] + [
            json.dumps(c_evaluacion.estado_oficial(copy.deepcopy(d)), sort_keys=True)
            for d, _ in declaraciones] + [
            json.dumps(c_evaluacion.resultado_interno({"result": r, "producer": p}),
                       sort_keys=True)
            for r in ("INTERNAL_REVIEW_COMPLETE", "G2_THRESHOLD_SATISFIED", "APPROVED")
            for p in INTERNOS + EXTERNOS] + [
            json.dumps([c_evaluacion.puede_emitir(p, e) for p in INTERNOS + EXTERNOS],
                       sort_keys=True)
            for e in ("APPROVED", "REJECTED", "INTERNAL_ASSESSMENT")]

    def _constantes():
        return {n: getattr(c_evaluacion, n, None) for n in (
            "PRODUCTORES_INTERNOS", "PRODUCTORES_EXTERNOS", "ESTADOS", "ESTADOS_OFICIALES",
            "ESTADOS_DEL_HARNESS", "RESULTADOS_INTERNOS", "SIN_RESOLVER", "APROBADA")}

    FUNCIONES = ("estado_oficial", "es_oficial", "puede_emitir", "resultado_interno")
    funciones_antes = {n: getattr(c_evaluacion, n) for n in FUNCIONES}
    codigo_antes = {n: f.__code__ for n, f in funciones_antes.items()}

    def _omisiones():
        return {n: (repr(getattr(c_evaluacion, n).__defaults__),
                    repr(getattr(c_evaluacion, n).__kwdefaults__)) for n in FUNCIONES}

    omisiones_antes = _omisiones()
    constantes_antes = _constantes()
    identidad_antes = {n: id(v) for n, v in constantes_antes.items()}
    resuelto_antes = _resoluciones()

    # Las revisiones, en todos los caminos: limpia, sospechosa, confirmada, sin linea de base, y
    # en los tres modos. Cualquiera de ellas podria ser la que toca `evaluacion`.
    revisiones = [I.revisar(BASE, _evidencia(), [], modo=m, mapeo=MAPEO) for m in I.MODOS]
    revisiones += [I.revisar(BASE, _evidencia(), [_senal()], mapeo=MAPEO),
                   I.revisar(BASE, _evidencia(), [_confirmada()], mapeo=MAPEO),
                   I.revisar(BASE, _evidencia(), [_senal(categoria="NO_EXISTE")]),
                   I.revisar(None, _evidencia(), [_senal()]),
                   I.revisar(BASE, _evidencia(archivos=[_archivo("x.bin", clase="RARO")]), [])]
    limpia = revisiones[0]

    resuelto_despues = _resoluciones()
    t.igual("E-04 lo que `evaluacion` resuelve, capturado antes, no cambia", resuelto_antes,
            resuelto_despues)
    t.igual("E-04 `estado_oficial()` sin argumento no resuelve un estado oficial", SIN,
            json.loads(resuelto_despues[0])["state"])
    t.igual("E-04 `resultado_interno()` sin argumento no resuelve nada", None,
            json.loads(resuelto_despues[1])["result"])
    # Los valores por omision, antes y despues, y clavados por literal.
    t.igual("E-04 los valores por omision de `evaluacion` no cambian", omisiones_antes,
            _omisiones())
    t.igual("E-04 `estado_oficial` sigue declarando None por omision", (None,),
            c_evaluacion.estado_oficial.__defaults__)
    t.igual("E-04 `resultado_interno` sigue declarando None por omision", (None,),
            c_evaluacion.resultado_interno.__defaults__)
    for nombre in FUNCIONES:
        t.igual("E-04 `%s` no gana argumentos por omision de palabra clave" % nombre, None,
                getattr(c_evaluacion, nombre).__kwdefaults__)
    # 🔴 Y el modulo sigue siendo el mismo objeto por los caminos por los que se lo alcanza:
    # cambiar `sys.modules` y el atributo del paquete dejaba a esta prueba mirando el modulo
    # viejo mientras el resto del harness leia uno nuevo (tercer veredicto).
    paquete = c_evaluacion.__name__.rpartition(".")[0]
    t.verdadero("E-04 `sys.modules` sigue apuntando al mismo modulo de evaluacion",
                sys.modules.get(c_evaluacion.__name__) is c_evaluacion)
    t.verdadero("E-04 el paquete sigue apuntando al mismo modulo de evaluacion",
                getattr(sys.modules.get(paquete), "evaluacion", None) is c_evaluacion)
    t.verdadero("E-04 y la capacidad sigue leyendo ese mismo modulo",
                I.evaluacion is c_evaluacion)
    t.verdadero("E-04 lo mismo con seguridad, de donde sale la constante sin resolver",
                sys.modules.get(c_seguridad.__name__) is c_seguridad
                and I.seguridad is c_seguridad
                and getattr(sys.modules.get(paquete), "seguridad", None) is c_seguridad)
    for (declaracion, esperado), crudo in zip(declaraciones, resuelto_despues[2:]):
        t.igual("E-04 %r resuelve %s" % (declaracion, esperado), esperado,
                json.loads(crudo)["state"])
    for nombre in FUNCIONES:
        t.verdadero("E-04 `evaluacion.%s` sigue siendo la misma funcion" % nombre,
                    getattr(c_evaluacion, nombre) is funciones_antes[nombre])
        t.verdadero("E-04 y con el mismo codigo: `%s`" % nombre,
                    getattr(c_evaluacion, nombre).__code__ is codigo_antes[nombre])
    constantes_despues = _constantes()
    t.igual("E-04 las constantes de `evaluacion` no cambian de valor", constantes_antes,
            constantes_despues)
    t.igual("E-04 ni de identidad", identidad_antes,
            {n: id(v) for n, v in constantes_despues.items()})
    t.igual("E-04 los productores internos siguen siendo estos cinco", INTERNOS,
            c_evaluacion.PRODUCTORES_INTERNOS)
    t.igual("E-04 y los externos estos tres", EXTERNOS, c_evaluacion.PRODUCTORES_EXTERNOS)
    t.igual("E-04 y el modulo de evaluacion no cambio su constante",
            c_seguridad.ESTADO_OFICIAL_SIN_RESOLVER, c_evaluacion.SIN_RESOLVER)
    t.igual("E-04 sin hallazgos", "NO_SUSPICIOUS_CHANGE_FOUND", limpia["state"])

    # 🔴 El resultado no lleva ningun campo que se lea como aprobacion. El vocabulario sale de la
    # spec —«un `PASS` de la revisión no implica aprobación de ES0902», «estado oficial»— y de
    # sus sinonimos directos: pasar (`pass`, `passed`), aprobar, habilitar (`clearance`,
    # `cleared`), otorgar (`granted`), homologar, certificar. Se barre sobre las CLAVES de todos
    # los niveles —y ahi `es0902` tambien: la capacidad no publica nada a nombre del estandar— y
    # sobre todos los VALORES de texto. Un `securityApproved`, un `es0902Passed` o un
    # `securityClearance: "GRANTED"` inventados son exactamente lo que el escenario prohibe.
    APROBATORIAS = re.compile(r"approv|aprob|official|oficial|homolog|certif|accredit|"
                              r"sign_?off|pass|clear|grant|otorg|habilit|es0902|"
                              r"securitystate|securitystatus", re.IGNORECASE)
    # En los valores, con borde de palabra: `APPROVED_RELEASE` es la PROCEDENCIA de una linea de
    # base y `ES0902` es la fuente de la severidad; ninguno de los dos es un veredicto.
    VEREDICTOS = re.compile(r"\b(pass|passed|approved|approval|cleared|clearance|granted|"
                            r"aprobad[oa]|aprobaci[oó]n|homologad[oa]|habilitad[oa]|"
                            r"otorgad[oa]|certificad[oa])\b", re.IGNORECASE)

    def _textos(dato, acumulado):
        if isinstance(dato, dict):
            for v in dato.values():
                _textos(v, acumulado)
        elif isinstance(dato, list):
            for v in dato:
                _textos(v, acumulado)
        elif isinstance(dato, str):
            acumulado.append(dato)
        return acumulado

    def _claves(dato, acumulado):
        if isinstance(dato, dict):
            for k, v in dato.items():
                acumulado.add(k)
                _claves(v, acumulado)
        elif isinstance(dato, list):
            for v in dato:
                _claves(v, acumulado)
        return acumulado

    for i, revision in enumerate(revisiones):
        t.vacio("E-04 la revision %d no lleva ninguna clave de aprobacion" % i,
                sorted(k for k in _claves(revision, set()) if APROBATORIAS.search(str(k))))
        t.vacio("E-04 la revision %d no lleva ningun valor que se lea como veredicto" % i,
                sorted(v for v in _textos(revision, []) if VEREDICTOS.search(v)))
        texto = json.dumps(revision, ensure_ascii=False, default=str)
        # 🔴 Con borde de identificador, no por subcadena: `APPROVED_RELEASE` es la PROCEDENCIA
        # de una linea de base —el estandar la nombra asi— y no el estado oficial `APPROVED` de
        # ES0902. Barrer por subcadena confunde una palabra con un identificador.
        for oficial in ("APPROVED", "REQUESTED", "IN_ASSESSMENT", "RESUBMITTED", "REJECTED",
                        "OFFICIAL_STATUS_UNRESOLVED"):
            t.vacio("E-04 la revision %d no declara el estado oficial %s" % (i, oficial),
                    re.findall(r"(?<![A-Z_])%s(?![A-Z_])" % oficial, texto))
        for palabra in ("approval", "aprobacion", "aprobación", "officialstate"):
            t.verdadero("E-04 la revision %d no declara `%s`" % (i, palabra),
                        palabra not in texto.lower())
    texto = json.dumps(limpia, ensure_ascii=False, default=str)
    t.verdadero("E-04 la premisa: la procedencia de la base si esta", "APPROVED_RELEASE" in texto)
    t.verdadero("E-04 la premisa: el barrido de claves ve una clave anidada",
                "commitSha" in _claves(limpia, set())
                and APROBATORIAS.search("securityApproved"))
    for clave in ("securityApproved", "es0902Passed", "securityClearance", "accessGranted"):
        t.verdadero("E-04 la premisa: el vocabulario ve la clave `%s`" % clave,
                    APROBATORIAS.search(clave))
    for valor in ("GRANTED", "PASS", "passed", "CLEARED", "aprobado"):
        t.verdadero("E-04 la premisa: el vocabulario ve el valor `%s`" % valor,
                    VEREDICTOS.search(valor))
    t.verdadero("E-04 la premisa: la procedencia no se lee como veredicto",
                not VEREDICTOS.search("APPROVED_RELEASE")
                and not VEREDICTOS.search("SECURITY_APPROVED_RELEASE"))
    t.verdadero("E-04 la premisa: los valores de texto se recorren anidados",
                "APPROVED_RELEASE" in _textos(limpia, []))


# -- E-05 a E-10 — el modo de incidente ---------------------------------------

def test_e05_el_modo_incidente_desactiva_lo_automatico(t):
    """E-05 (RI-04) — los tres modos, y las seis acciones apagadas."""
    TRES = ("NORMAL", "SECURITY_ASSESSMENT", "SECURITY_INCIDENT")
    t.igual("E-05 son estos tres modos", TRES, I.MODOS)
    SEIS = ("CODE_REMEDIATION", "FILE_DELETION", "SECRET_ROTATION", "DEPENDENCY_UPGRADE",
            "HISTORY_REWRITE", "ARTIFACT_CLEANUP")
    t.igual("E-05 son estas seis acciones mutantes", SEIS, I.ACCIONES_MUTANTES)
    for accion in SEIS:
        t.verdadero("E-05 %s no corre sola en incidente" % accion,
                    not I.automatico_permitido(accion, "SECURITY_INCIDENT"))
        t.verdadero("E-05 %s si corre en NORMAL" % accion,
                    I.automatico_permitido(accion, "NORMAL"))
    defensas = I.defensas("SECURITY_INCIDENT")
    t.verdadero("E-05 las defensas lo declaran",
                defensas["evidencePreservingDefaults"] is True)
    t.igual("E-05 y ninguna queda en True", [],
            [a for a, ok in defensas["automatic"].items() if ok])


def test_e06_la_evidencia_se_preserva_antes(t):
    """E-06 (RI-05) — sin instantanea sellada, ninguna mutacion se autoriza."""
    preservada = I.instantanea(_evidencia(), "SECURITY_INCIDENT")
    t.verdadero("E-06 la instantanea trae su sello", bool(preservada.get("seal")))
    t.verdadero("E-06 y el sello es valido", I.sello_valido(preservada))
    t.verdadero("E-06 conserva el commit", preservada["commitSha"] == COMMIT_ACTUAL)
    t.verdadero("E-06 y los padres", preservada["parents"] == [COMMIT_BASE])

    # 🔴 LAS SEIS, no una. Con el muestreo de una sola accion, restringir la compuerta a esa
    # dejaba que las otras cinco —las que borran la escena— se ejecutaran sin evidencia
    # preservada, y la suite entera seguia verde.
    SEIS = ("CODE_REMEDIATION", "FILE_DELETION", "SECRET_ROTATION", "DEPENDENCY_UPGRADE",
            "HISTORY_REWRITE", "ARTIFACT_CLEANUP")
    t.igual("E-06 son estas seis las que preservan antes", SEIS, I.ACCIONES_MUTANTES)
    adulterada = dict(preservada, commitSha="c" * 40)
    t.verdadero("E-06 una instantanea adulterada no sella", not I.sello_valido(adulterada))
    for accion in SEIS:
        sin_preservar = I.autorizar_mutacion(accion, "SECURITY_INCIDENT", None,
                                             {"explicit": True, "reference": "acta"})
        t.verdadero("E-06 %s sin instantanea no se autoriza" % accion,
                    not sin_preservar["allowed"])
        t.verdadero("E-06 %s lo dice" % accion,
                    "EVIDENCE_NOT_PRESERVED" in sin_preservar["reasons"])
        con_adulterada = I.autorizar_mutacion(accion, "SECURITY_INCIDENT", adulterada,
                                              {"explicit": True, "reference": "acta"})
        t.verdadero("E-06 %s con la instantanea adulterada tampoco" % accion,
                    not con_adulterada["allowed"])
        t.verdadero("E-06 %s con evidencia y autorizacion, si" % accion,
                    I.autorizar_mutacion(accion, "SECURITY_INCIDENT", preservada,
                                         {"explicit": True, "reference": "acta"})["allowed"])

    con_todo = I.autorizar_mutacion("FILE_DELETION", "SECURITY_INCIDENT", preservada,
                                    {"explicit": True, "reference": "acta de incidente #7"})
    t.verdadero("E-06 con evidencia y autorizacion, se puede", con_todo["allowed"])
    t.verdadero("E-06 y sigue pidiendo revision humana", con_todo["requiresHumanReview"])


def test_e07_la_rotacion_no_es_automatica(t):
    """E-07 (RI-41) — hace falta autorizacion explicita citada."""
    preservada = I.instantanea(_evidencia())
    sola = I.autorizar_mutacion("SECRET_ROTATION", "SECURITY_INCIDENT", preservada)
    t.verdadero("E-07 no se autoriza sola", not sola["allowed"])
    t.verdadero("E-07 y pide autorizacion", "EXPLICIT_AUTHORIZATION_REQUIRED" in sola["reasons"])
    t.igual("E-07 con revision humana", "HUMAN_SECURITY_REVIEW_REQUIRED", sola["state"])
    # Una autorizacion sin referencia no es una autorizacion.
    t.verdadero("E-07 sin cita tampoco", not I.autorizar_mutacion(
        "SECRET_ROTATION", "SECURITY_INCIDENT", preservada, {"explicit": True})["allowed"])


def test_e08_el_borrado_no_es_automatico(t):
    """E-08 (RI-42) — un archivo sospechoso no se borra solo."""
    preservada = I.instantanea(_evidencia())
    salida = I.autorizar_mutacion("FILE_DELETION", "SECURITY_INCIDENT", preservada)
    t.verdadero("E-08 no se autoriza", not salida["allowed"])
    t.verdadero("E-08 con revision humana", salida["requiresHumanReview"])


def test_e09_la_reescritura_no_es_automatica(t):
    """E-09 (RI-43) — force-push y reescritura de historia."""
    preservada = I.instantanea(_evidencia())
    salida = I.autorizar_mutacion("HISTORY_REWRITE", "SECURITY_INCIDENT", preservada)
    t.verdadero("E-09 no se autoriza", not salida["allowed"])
    t.verdadero("E-09 y pide autorizacion",
                "EXPLICIT_AUTHORIZATION_REQUIRED" in salida["reasons"])


def test_e10_recomendar_sigue_permitido(t):
    """E-10 (§3) — una recomendacion nunca queda ejecutada."""
    for accion in I.ACCIONES_MUTANTES:
        r = I.recomendar(accion, "el commit introduce una descarga remota")
        t.igual("E-10 %s se puede recomendar" % accion, accion, r["action"])
        t.verdadero("E-10 %s no queda ejecutada" % accion, r["executed"] is False)
        t.verdadero("E-10 %s pide revision humana" % accion, r["requiresHumanReview"] is True)
        t.verdadero("E-10 %s dice por que" % accion, bool(r["reason"]))


# -- E-11 a E-15 — la linea de base --------------------------------------------

def test_e11_la_rama_actual_no_es_confiable(t):
    """E-11 (RI-06) — una ubicacion no es una procedencia."""
    for ubicacion in ("main", "master", "HEAD~1", "refs/heads/main", "el ultimo tag"):
        base, motivo = I.baseline({"repository": "gcba/tramites", "ref": ubicacion,
                                   "commitSha": COMMIT_ACTUAL})
        t.verdadero("E-11 `%s` no resuelve sola" % ubicacion, base is None)
        t.verdadero("E-11 `%s` dice por que" % ubicacion, "procedencia" in motivo)
    # 🔴 Y el modulo no tiene ningun nombre de rama adentro: no puede elegir la mas comoda.
    for literal in _literales(RUTA_MOD):
        for rama in ("main", "master", "HEAD", "trunk", "develop"):
            t.verdadero("E-11 el modulo no nombra `%s`: %s" % (rama, literal[:28]),
                        not re.search(r"(?i)(^|[^a-z])%s([^a-z]|$)" % rama, literal))


def test_e12_sin_linea_de_base(t):
    """E-12 (RI-07) — las cinco formas del hueco."""
    formas = {
        "sin repositorio": dict(BASE, repository=""),
        "sin ref": dict(BASE, ref=""),
        "sin commit": dict(BASE, commitSha=""),
        "sin procedencia": {k: v for k, v in BASE.items() if k != "source"},
        "sin evidencia": dict(BASE, evidence=[]),
    }
    t.igual("E-12 son cinco formas", 5, len(formas))
    for nombre, declarada in sorted(formas.items()):
        base, motivo = I.baseline(declarada)
        t.verdadero("E-12 %s no resuelve" % nombre, base is None)
        t.verdadero("E-12 %s dice por que" % nombre, bool(motivo))
        salida = I.revisar(declarada, _evidencia(), [])
        t.igual("E-12 %s deja la revision sin base" % nombre, "TRUSTED_BASELINE_UNRESOLVED",
                salida["state"])
        t.verdadero("E-12 %s conserva la limitacion" % nombre, bool(salida["limitations"]))


def test_e13_la_confirmacion_humana_exige_quien(t):
    """E-13 (RI-08) — evidencia y firma."""
    sin_firma = dict(BASE, source="HUMAN_CONFIRMED", establishedBy="")
    base, motivo = I.baseline(sin_firma)
    t.verdadero("E-13 sin firma no resuelve", base is None)
    t.verdadero("E-13 y dice que falta", "quien" in motivo)
    sin_evidencia = dict(BASE, source="HUMAN_CONFIRMED", evidence=[])
    t.verdadero("E-13 sin evidencia tampoco", I.baseline(sin_evidencia)[0] is None)
    con_las_dos = dict(BASE, source="HUMAN_CONFIRMED", establishedBy="la persona de seguridad")
    t.verdadero("E-13 con las dos, resuelve", I.baseline(con_las_dos)[0] is not None)


def test_e14_cambiar_la_base_crea_otro_contexto(t):
    """E-14 (RI-09) — el id sale de la base, y dos bases distintas no lo comparten."""
    una = I.baseline(BASE)[0]
    otra = I.baseline(dict(BASE, commitSha="c" * 40))[0]
    tercera = I.baseline(dict(BASE, source="DEPLOYED_RELEASE"))[0]
    ids = {I.contexto_de_revision(una), I.contexto_de_revision(otra),
           I.contexto_de_revision(tercera)}
    t.igual("E-14 tres bases, tres contextos", 3, len(ids))
    t.igual("E-14 la misma base da el mismo contexto", I.contexto_de_revision(una),
            I.contexto_de_revision(I.baseline(BASE)[0]))
    t.verdadero("E-14 y la revision lo publica",
                I.revisar(BASE, _evidencia(), [])["reviewId"] == I.contexto_de_revision(una))


def test_e15_las_cinco_fuentes(t):
    """E-15 (§4) — las cinco sirven, y ninguna otra."""
    CINCO = ("APPROVED_RELEASE", "DEPLOYED_RELEASE", "SECURITY_APPROVED_RELEASE",
             "HUMAN_CONFIRMED", "OTHER_AUTHORITATIVE")
    t.igual("E-15 son estas cinco", CINCO, I.FUENTES_DE_BASELINE)
    for fuente in CINCO:
        declarada = dict(BASE, source=fuente)
        t.verdadero("E-15 %s sirve" % fuente, I.baseline(declarada)[0] is not None)
    for inventada in ("DEFAULT_BRANCH", "LATEST_TAG", "CURRENT_HEAD", "PROJECT_CONVENTION"):
        t.verdadero("E-15 %s no sirve" % inventada,
                    I.baseline(dict(BASE, source=inventada))[0] is None)


# -- E-16 a E-26 — el inventario ----------------------------------------------

def _evidencia_completa():
    return _evidencia(archivos=[
        _archivo("src/nuevo.py", "ADDED", "SOURCE", afterHash="h-nuevo"),
        _archivo("src/app.py", "MODIFIED", "SOURCE", beforeHash="h-v", afterHash="h-n"),
        _archivo("src/viejo.py", "DELETED", "SOURCE", beforeHash="h-viejo"),
        _archivo("package.json", "MODIFIED", "DEPENDENCY_MANIFEST"),
        _archivo("package-lock.json", "MODIFIED", "LOCKFILE"),
        _archivo(".ci/deploy.yml", "MODIFIED", "CICD"),
        _archivo("Containerfile", "MODIFIED", "BUILD"),
        _archivo("infra/red.tf", "MODIFIED", "INFRASTRUCTURE"),
        _archivo("src/login.py", "MODIFIED", "AUTHENTICATION"),
        _archivo("src/permisos.py", "MODIFIED", "AUTHORIZATION"),
        _archivo("bin/herramienta", "ADDED", "BINARY_ARTIFACT", afterHash="h-bin")])


def test_e16_los_archivos_agregados_modificados_y_borrados(t):
    """E-16 (RI-10) — las tres operaciones."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-16 agregados", ["bin/herramienta", "src/nuevo.py"], inv["FILES_ADDED"])
    t.verdadero("E-16 modificados", "src/app.py" in inv["FILES_MODIFIED"])
    t.igual("E-16 borrados", ["src/viejo.py"], inv["FILES_DELETED"])
    ONCE = ("COMMITS", "FILES_ADDED", "FILES_MODIFIED", "FILES_DELETED",
            "DEPENDENCY_CHANGES", "LOCKFILE_CHANGES", "CICD_CHANGES", "BUILD_CHANGES",
            "AUTH_CHANGES", "NETWORK_DESTINATIONS", "BINARY_ARTIFACTS")
    t.igual("E-16 son estas once clases de cambio", ONCE, I.CLASES_DE_CAMBIO)


def test_e17_la_identidad_de_los_commits(t):
    """E-17 (RI-11) — sha, padres, autor y verificacion."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-17 un commit", 1, len(inv["COMMITS"]))
    commit = inv["COMMITS"][0]
    t.igual("E-17 el sha", COMMIT_ACTUAL, commit["sha"])
    t.igual("E-17 los padres", [COMMIT_BASE], commit["parents"])
    t.igual("E-17 el autor viaja como metadata", "alguien", commit["author"])
    t.igual("E-17 y la verificacion", False, commit["verified"])
    t.igual("E-17 el commit de la base se conserva", COMMIT_BASE, inv["baselineCommit"])
    t.igual("E-17 y el actual", COMMIT_ACTUAL, inv["currentCommit"])


def test_e18_los_hashes_de_archivo(t):
    """E-18 (RI-12) — cuando la evidencia los trae."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-18 el hash de antes", "h-v", inv["fileHashes"]["src/app.py"]["beforeHash"])
    t.igual("E-18 y el de despues", "h-n", inv["fileHashes"]["src/app.py"]["afterHash"])
    t.igual("E-18 el binario conserva su hash", "h-bin",
            inv["fileHashes"]["bin/herramienta"]["afterHash"])
    t.verdadero("E-18 un archivo sin hash no inventa uno",
                ".ci/deploy.yml" not in inv["fileHashes"])


def test_e19_los_manifiestos_de_dependencias(t):
    """E-19 (RI-13)."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-19 el manifiesto", ["package.json"], inv["DEPENDENCY_CHANGES"])


def test_e20_los_lockfiles(t):
    """E-20 (RI-14)."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-20 el lockfile", ["package-lock.json"], inv["LOCKFILE_CHANGES"])


def test_e21_el_pipeline(t):
    """E-21 (RI-15)."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-21 el pipeline", [".ci/deploy.yml"], inv["CICD_CHANGES"])


def test_e22_el_contenedor_y_el_build(t):
    """E-22 (RI-16) — build e infraestructura como código."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-22 build e infraestructura", ["Containerfile", "infra/red.tf"],
            inv["BUILD_CHANGES"])


def test_e23_la_autenticacion_y_la_autorizacion(t):
    """E-23 (RI-17)."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-23 auth", ["src/login.py", "src/permisos.py"], inv["AUTH_CHANGES"])


def test_e24_los_binarios_inesperados(t):
    """E-24 (RI-18) — con su ruta y su hash."""
    inv = I.inventario(I.baseline(BASE)[0], _evidencia_completa())
    t.igual("E-24 el binario", ["bin/herramienta"], inv["BINARY_ARTIFACTS"])
    t.igual("E-24 con su hash", "h-bin", inv["fileHashes"]["bin/herramienta"]["afterHash"])
    t.igual("E-24 y los destinos de red nuevos", ["destino-nuevo.example"],
            inv["NETWORK_DESTINATIONS"])


def test_e25_el_inventario_es_determinista(t):
    """E-25 (RI-50) — la misma entrada, la misma salida; el orden no cambia nada."""
    base = I.baseline(BASE)[0]
    evidencia = _evidencia_completa()
    uno = I.inventario(base, evidencia)
    dos = I.inventario(base, copy.deepcopy(evidencia))
    t.igual("E-25 dos corridas, el mismo inventario", json.dumps(uno, sort_keys=True),
            json.dumps(dos, sort_keys=True))

    # 🔴 Y el orden de entrada no lo cambia: un inventario que depende del orden de un diff no se
    # puede citar, porque la corrida de manana dice otra cosa.
    invertida = copy.deepcopy(evidencia)
    invertida["changedFiles"] = list(reversed(invertida["changedFiles"]))
    invertida["networkDestinations"] = list(reversed(invertida["networkDestinations"]))
    t.igual("E-25 el orden de entrada no lo mueve", json.dumps(uno, sort_keys=True),
            json.dumps(I.inventario(base, invertida), sort_keys=True))

    # Ni una marca de tiempo de *ahora* adentro.
    t.vacio("E-25 el inventario no trae una marca de ahora",
            [k for k in uno if k.lower() in ("now", "generatedat", "ranat")])


def test_e26_un_archivo_sin_clase_no_se_adivina(t):
    """E-26 (§6) — queda sin clasificar y deja la revision incompleta."""
    evidencia = _evidencia(archivos=[
        _archivo("src/app.py", "MODIFIED", "SOURCE"),
        {"path": ".ci/otro.yml", "operation": "MODIFIED"}])
    inv = I.inventario(I.baseline(BASE)[0], evidencia)
    t.igual("E-26 queda sin clasificar", [".ci/otro.yml"], inv["UNCLASSIFIED_CHANGE"])
    t.verdadero("E-26 y no se cuela como pipeline", ".ci/otro.yml" not in inv["CICD_CHANGES"])
    completo, motivo = I.inventario_completo(inv)
    t.verdadero("E-26 el inventario no esta completo", not completo)
    t.verdadero("E-26 y dice cual", ".ci/otro.yml" in motivo)
    t.igual("E-26 la revision queda incompleta", "REVIEW_INCOMPLETE",
            I.revisar(BASE, evidencia, [])["state"])
    DIEZ = ("SOURCE", "DEPENDENCY_MANIFEST", "LOCKFILE", "CICD", "BUILD", "AUTHENTICATION",
            "AUTHORIZATION", "BINARY_ARTIFACT", "INFRASTRUCTURE", "DOCUMENTATION")
    t.igual("E-26 son estas diez clases de archivo", DIEZ, I.CLASES_DE_ARCHIVO)


# -- E-27 a E-32 — las senales y la confirmacion -------------------------------

def test_e27_eval_y_exec_solos(t):
    """E-27 (RI-19) — no producen un veredicto confirmado."""
    for indicador in ("EVAL_PRESENT", "EXEC_PRESENT"):
        senal = _senal(indicadores=(indicador,))
        t.igual("E-27 %s deja sospechoso" % indicador, "SUSPICIOUS_BEHAVIOR_DETECTED",
                I.estado_de_senal(senal))
        t.igual("E-27 %s con confianza baja" % indicador, "LOW", I.confianza(senal))


def test_e28_base64_y_ofuscacion_solos(t):
    """E-28 (RI-20)."""
    senal = _senal(categoria="OBFUSCATED_CODE", indicadores=("BASE64_PRESENT",))
    t.igual("E-28 deja sospechoso", "SUSPICIOUS_BEHAVIOR_DETECTED", I.estado_de_senal(senal))
    t.igual("E-28 con confianza baja", "LOW", I.confianza(senal))
    t.verdadero("E-28 no llega a confirmado",
                I.estado_de_senal(senal) != "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE")


def test_e29_un_dominio_nuevo_solo(t):
    """E-29 (RI-21) — no es exfiltracion confirmada."""
    senal = _senal(categoria="NEW_EXTERNAL_NETWORK_DESTINATION",
                   indicadores=("NEW_DOMAIN_PRESENT",))
    t.igual("E-29 deja sospechoso", "SUSPICIOUS_BEHAVIOR_DETECTED", I.estado_de_senal(senal))
    t.igual("E-29 con confianza baja", "LOW", I.confianza(senal))
    exfiltracion = _senal(categoria="SECRET_EXFILTRATION", indicadores=("NEW_DOMAIN_PRESENT",))
    t.verdadero("E-29 ni siquiera bajo la categoria de exfiltracion",
                I.estado_de_senal(exfiltracion) != "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE")


def test_e30_los_seis_debiles_juntos(t):
    """E-30 (RI-19, RI-20, RI-21) — el invariante, no seis ejemplos."""
    SEIS = ("EVAL_PRESENT", "EXEC_PRESENT", "BASE64_PRESENT", "SHELL_COMMAND_PRESENT",
            "NEW_DOMAIN_PRESENT", "NEW_DEPENDENCY_PRESENT")
    t.igual("E-30 son estos seis los debiles", SEIS, I.INDICADORES_DEBILES)
    # Todas las combinaciones no vacias de los seis, con evidencia directa declarada incluida.
    for mascara in range(1, 1 << len(SEIS)):
        indicadores = tuple(SEIS[i] for i in range(len(SEIS)) if mascara & (1 << i))
        for directa in (False, True):
            senal = _senal(indicadores=indicadores, directa=directa,
                           directEvidenceReference="una cita")
            t.verdadero("E-30 %d debiles, directa=%s, no confirma" % (len(indicadores), directa),
                        I.estado_de_senal(senal) != "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE")
            t.igual("E-30 %d debiles: confianza baja" % len(indicadores), "LOW",
                    I.confianza(senal))


def test_e31_una_senal_produce_evidencia_y_confianza(t):
    """E-31 (RI-22) — y las veintiuna categorias, nombradas una por una."""
    # 🔴 Clavadas por literal, no contadas: con el conteo solo, renombrar una queda verde.
    VEINTIUNA = (
        "REMOTE_PAYLOAD_DOWNLOAD", "DYNAMIC_CODE_EXECUTION", "OBFUSCATED_CODE",
        "CREDENTIAL_ACCESS", "SECRET_EXFILTRATION", "ENVIRONMENT_EXFILTRATION",
        "NEW_EXTERNAL_NETWORK_DESTINATION", "AUTHENTICATION_BYPASS", "AUTHORIZATION_BYPASS",
        "HARD_CODED_PRIVILEGED_IDENTITY", "BACKDOOR_LIKE_BEHAVIOR", "WEB_SHELL_LIKE_BEHAVIOR",
        "CI_CD_TAMPERING", "BUILD_SCRIPT_TAMPERING", "DEPENDENCY_SUBSTITUTION",
        "LOCKFILE_TAMPERING", "UNEXPECTED_BINARY_ARTIFACT", "INFRASTRUCTURE_TAMPERING",
        "PERSISTENCE_MECHANISM", "SECURITY_CONTROL_DISABLEMENT", "UNRESOLVED_SUSPICIOUS_CHANGE")
    t.igual("E-31 son estas veintiuna categorias", VEINTIUNA, I.CATEGORIAS)

    # 🔴 Y el hallazgo lleva EXACTAMENTE las claves del contrato: una senal no se copia en crudo
    # adentro de un campo inventado. Es la misma doctrina que el barrido de proveedores.
    h = I.hallazgo(_senal(rawPayload=PAYLOAD), "ri-1", I.baseline(BASE)[0], MAPEO)
    t.igual("E-31 el hallazgo lleva las claves del contrato", sorted(CLAVES_DE_HALLAZGO),
            sorted(h))
    t.verdadero("E-31 y no copia la senal en crudo", PAYLOAD not in json.dumps(h, default=str))
    t.igual("E-31 conserva el archivo", "src/app.py", h["file"])
    t.igual("E-31 y la ubicacion", "10-14", h["location"])

    for categoria in VEINTIUNA:
        senal = _senal(categoria=categoria)
        h = I.hallazgo(senal, "ri-1", I.baseline(BASE)[0], MAPEO)
        t.verdadero("E-31 %s produce evidencia" % categoria, bool(h["evidence"]))
        t.verdadero("E-31 %s produce confianza" % categoria, h["confidence"] in I.CONFIANZAS)
        t.igual("E-31 %s conserva la categoria" % categoria, categoria, h["category"])
        t.vacio("E-31 %s el hallazgo valida contra el contrato" % categoria,
                I.validar_hallazgo(h))
    # Una categoria que no esta declarada deja la revision incompleta, no la inventa.
    t.igual("E-31 una categoria desconocida no se inventa", "REVIEW_INCOMPLETE",
            I.estado_de_senal(_senal(categoria="LO_QUE_SEA")))


def test_e32_el_confirmado_exige_evidencia_directa(t):
    """E-32 (RI-23) — evidencia directa citada y confianza alta."""
    confirmada = _confirmada()
    t.igual("E-32 con las tres cosas, confirma", "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE",
            I.estado_de_senal(confirmada))
    t.igual("E-32 con confianza alta", "HIGH", I.confianza(confirmada))

    sin_cita = dict(confirmada)
    sin_cita.pop("directEvidenceReference")
    t.igual("E-32 sin la cita no confirma", "SUSPICIOUS_BEHAVIOR_DETECTED",
            I.estado_de_senal(sin_cita))
    sin_bandera = dict(confirmada, directEvidence=False)
    t.igual("E-32 sin la bandera tampoco", "SUSPICIOUS_BEHAVIOR_DETECTED",
            I.estado_de_senal(sin_bandera))
    sin_evidencia = dict(confirmada, evidence=[])
    t.igual("E-32 sin evidencia queda incompleta", "REVIEW_INCOMPLETE",
            I.estado_de_senal(sin_evidencia))


# -- E-33 a E-35 — la confianza y la severidad ---------------------------------

def test_e33_confianza_y_severidad_son_dos_ejes(t):
    """E-33 (RI-24) — el invariante: cambiar una no mueve a la otra."""
    base = I.baseline(BASE)[0]
    CONFIANZAS = ("LOW", "MEDIUM", "HIGH")
    t.igual("E-33 son estas tres confianzas", CONFIANZAS, I.CONFIANZAS)
    por_confianza = {
        "LOW": _senal(indicadores=("EVAL_PRESENT",)),
        "MEDIUM": _senal(indicadores=("REVERSE_SHELL_ESTABLISHED",)),
        "HIGH": _confirmada(),
    }
    for nivel, senal in sorted(por_confianza.items()):
        t.igual("E-33 la confianza es %s" % nivel, nivel, I.confianza(senal))
        for etiqueta, categoria in sorted(MAPEO["map"].items()):
            h = I.hallazgo(dict(senal, scannerSeverity=etiqueta), "ri-1", base, MAPEO)
            t.igual("E-33 confianza %s no mueve la severidad %s" % (nivel, categoria),
                    categoria, h["severity"]["value"])
            t.igual("E-33 y la confianza sigue siendo %s" % nivel, nivel, h["confidence"])
    # Y son campos distintos del hallazgo.
    h = I.hallazgo(dict(_confirmada(), scannerSeverity="low"), "ri-1", base, MAPEO)
    t.igual("E-33 confianza alta", "HIGH", h["confidence"])
    t.igual("E-33 con severidad baja", "LOW", h["severity"]["value"])


def test_e34_no_se_inventa_una_segunda_escala(t):
    """E-34 (RI-25) — la severidad sale del mapeo de ES0902 y de ningun lado mas."""
    base = I.baseline(BASE)[0]
    h = I.hallazgo(dict(_senal(), scannerSeverity="critical"), "ri-1", base, MAPEO)
    t.igual("E-34 la severidad sale del mapeo", "CRITICAL", h["severity"]["value"])
    t.igual("E-34 y declara su fuente", "ES0902", h["severity"]["source"])

    # 🔴 Ninguna lista literal del modulo agrupa dos valores de severidad: eso seria una segunda
    # escala. `CONFIANZAS` no cuenta: son tres valores de CONFIANZA, y el escenario de al lado
    # prueba que no se derivan una de la otra.
    severidades = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "NONE"}
    arbol = ast.parse(RUTA_MOD.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Tuple, ast.List)):
            continue
        textos = {e.value for e in nodo.elts
                  if isinstance(e, ast.Constant) and isinstance(e.value, str)}
        juntas = sorted(textos & severidades)
        t.verdadero("E-34 ninguna lista agrupa severidades: %s" % ", ".join(juntas),
                    len(juntas) <= 1 or juntas == ["HIGH", "LOW", "MEDIUM"])
    # Y usa la misma compuerta que el umbral de G2.
    t.igual("E-34 el estado sin mapeo es el de ES0902", "VULNERABILITY_RISK_MAPPING_UNRESOLVED",
            c_seguridad.MAPEO_DE_RIESGO_SIN_RESOLVER)


def test_e35_sin_mapeo_autoritativo(t):
    """E-35 (RI-26) — SECURITY_SEVERITY_UNRESOLVED en las cuatro formas."""
    senal = dict(_senal(), scannerSeverity="high")
    formas = {
        "sin mapeo": None,
        "sin declararse autoritativo": {"map": {"high": "HIGH"}, "evidence": ["x"]},
        "autoritativo con un string": {"authoritative": "false", "map": {"high": "HIGH"},
                                       "evidence": ["x"]},
        "sin evidencia": {"authoritative": True, "map": {"high": "HIGH"}, "evidence": []},
    }
    for nombre, mapeo in sorted(formas.items()):
        r = I.severidad(senal, mapeo)
        t.igual("E-35 %s no resuelve" % nombre, "SECURITY_SEVERITY_UNRESOLVED", r["state"])
        t.igual("E-35 %s no inventa un valor" % nombre, None, r["value"])
    # Y una severidad que el mapeo no cubre tampoco.
    fuera = I.severidad(dict(_senal(), scannerSeverity="lo-que-sea"), MAPEO)
    t.igual("E-35 una severidad fuera del mapeo", "SECURITY_SEVERITY_UNRESOLVED", fuera["state"])
    h = I.hallazgo(dict(_senal(), scannerSeverity="lo-que-sea"), "ri-1",
                   I.baseline(BASE)[0], MAPEO)
    t.igual("E-35 y el hallazgo lo declara", "SECURITY_SEVERITY_UNRESOLVED",
            h["severityState"])


# -- E-36 a E-38 — los secretos ------------------------------------------------

def test_e36_el_secreto_no_entra_al_hallazgo(t):
    """E-36 (RI-27) — en ninguno de sus campos."""
    evidencia = I.secreto("src/config.py:12", SECRETO)
    senal = _senal(categoria="CREDENTIAL_ACCESS",
                   evidence=[json.dumps(evidencia, sort_keys=True, ensure_ascii=False)])
    h = I.hallazgo(senal, "ri-1", I.baseline(BASE)[0], MAPEO)
    texto = json.dumps(h, ensure_ascii=False, default=str)
    t.verdadero("E-36 el valor en claro no esta", SECRETO not in texto)
    t.verdadero("E-36 y tampoco un tramo largo suyo", SECRETO[:24] not in texto)
    t.vacio("E-36 el hallazgo valida contra el contrato", I.validar_hallazgo(h))
    # Y tampoco en la revision entera.
    r = I.revisar(BASE, _evidencia(), [senal], mapeo=MAPEO)
    t.verdadero("E-36 ni en la revision entera", SECRETO not in
                json.dumps(r, ensure_ascii=False, default=str))


def test_e37_el_secreto_se_redacta_y_se_huella(t):
    """E-37 (RI-28) — redactado, huellado y ubicado."""
    datos = I.secreto("src/config.py:12", SECRETO)
    t.verdadero("E-37 el valor no viaja", SECRETO not in json.dumps(datos))
    t.verdadero("E-37 trae una huella", datos["fingerprint"].startswith("sha256:"))
    t.igual("E-37 conserva la ubicacion", "src/config.py:12", datos["location"])
    t.igual("E-37 y la categoria", "CREDENTIAL_ACCESS", datos["category"])
    t.igual("E-37 la huella del mismo valor es la misma", datos["fingerprint"],
            I.secreto("otro/lado.py:3", SECRETO)["fingerprint"])
    t.verdadero("E-37 y la de otro valor es otra",
                datos["fingerprint"] != I.secreto("src/config.py:12", "otro")["fingerprint"])
    t.verdadero("E-37 lo redactado no es el valor", datos["redacted"] != SECRETO)


def test_e38_la_contabilidad_no_guarda_nada_sensible(t):
    """E-38 (RI-46) — mide, y no guarda secretos ni payloads."""
    # 🔴 El secreto y el payload entran EN CRUDO a la revision, que es el unico caso en el que
    # las dos aserciones de abajo pueden fallar: con la entrada ya redactada no probaban nada.
    senal = _senal(evidence=[json.dumps(I.secreto("src/config.py:12", SECRETO)), SECRETO],
                   reasoningSummary="hay un script sospechoso: " + PAYLOAD)
    r = I.revisar(BASE, _evidencia(), [senal], mapeo=MAPEO)
    t.verdadero("E-38 la premisa: en la revision si estan",
                SECRETO in json.dumps(r, default=str) and PAYLOAD in json.dumps(r, default=str))
    evento = I.contabilidad(r, {"tokens": 1200, "model": "un-modelo"})
    texto = json.dumps(evento, ensure_ascii=False, default=str)
    t.verdadero("E-38 no guarda el secreto", SECRETO not in texto)
    t.verdadero("E-38 no guarda el payload", PAYLOAD not in texto)
    t.verdadero("E-38 no guarda evidencia", "evidence" not in texto)
    t.verdadero("E-38 no guarda el diff", "changedFiles" not in texto)
    t.igual("E-38 mide los hallazgos", 1, evento["findingCount"])
    t.igual("E-38 y el uso", 1200, evento["usage"]["tokens"])
    t.igual("E-38 declara de que es el evento", "REPOSITORY_INTEGRITY_REVIEW",
            evento["eventType"])


# -- E-39 a E-43 — el pipeline y la cadena de suministro -----------------------

def test_e39_el_acceso_nuevo_a_un_secreto(t):
    """E-39 (RI-29)."""
    t.verdadero("E-39 el hecho esta declarado", "NEW_SECRET_ACCESS" in I.HECHOS_DE_PIPELINE)
    senal = _senal(categoria="CI_CD_TAMPERING", indicadores=("NEW_SECRET_ACCESS",),
                   file=".ci/deploy.yml")
    h = I.hallazgo(senal, "ri-1", I.baseline(BASE)[0], MAPEO)
    t.igual("E-39 se expone como sospechoso", "SUSPICIOUS_BEHAVIOR_DETECTED", h["status"])
    t.igual("E-39 y no como indicador debil", "MEDIUM", h["confidence"])
    t.igual("E-39 el hecho sale en el hallazgo", ["NEW_SECRET_ACCESS"], h["pipelineFacts"])
    t.vacio("E-39 y no como debil", h["weakIndicators"])


def test_e40_la_desactivacion_de_un_control(t):
    """E-40 (RI-30)."""
    t.verdadero("E-40 el hecho esta declarado", "DISABLED_SECURITY_GATE" in I.HECHOS_DE_PIPELINE)
    senal = _senal(categoria="SECURITY_CONTROL_DISABLEMENT",
                   indicadores=("DISABLED_SECURITY_GATE",), file=".ci/deploy.yml")
    h = I.hallazgo(senal, "ri-1", I.baseline(BASE)[0], MAPEO)
    t.igual("E-40 se expone", "SUSPICIOUS_BEHAVIOR_DETECTED", h["status"])
    t.igual("E-40 el hecho sale en el hallazgo", ["DISABLED_SECURITY_GATE"],
            h["pipelineFacts"])
    t.verdadero("E-40 la categoria existe",
                "SECURITY_CONTROL_DISABLEMENT" in I.CATEGORIAS)


def test_e41_el_despliegue_privilegiado(t):
    """E-41 (RI-31) — y los once hechos del pipeline SE EXPONEN en el hallazgo."""
    # 🔴 Los once van clavados por literal: el conteo solo deja renombrar uno sin que nadie se
    # entere. Y lo que el escenario afirma es que se EXPONEN, asi que hay que mirar la salida:
    # la version anterior verificaba pertenencia a una tupla que ninguna funcion leia.
    ONCE = ("NEW_SECRET_ACCESS", "NEW_EXTERNAL_UPLOAD", "NEW_EXTERNAL_DOWNLOAD",
            "NEW_SHELL_EXECUTION", "NEW_PUBLICATION_TARGET", "NEW_DEPLOYMENT_TARGET",
            "DISABLED_SECURITY_GATE", "WEAKENED_APPROVAL_GATE", "PRIVILEGED_RUNNER_CHANGE",
            "REPOSITORY_TOKEN_CHANGE", "BRANCH_TRIGGER_CHANGE")
    t.igual("E-41 son estos once los hechos del pipeline", ONCE, I.HECHOS_DE_PIPELINE)
    base = I.baseline(BASE)[0]
    for hecho in ONCE:
        senal = _senal(categoria="CI_CD_TAMPERING", indicadores=(hecho,),
                       file=".ci/deploy.yml")
        h = I.hallazgo(senal, "ri-1", base, MAPEO)
        t.verdadero("E-41 %s se expone en el hallazgo" % hecho, hecho in h["indicators"])
        t.verdadero("E-41 %s se expone como hecho de pipeline" % hecho,
                    hecho in h["pipelineFacts"])
        t.verdadero("E-41 %s no se confunde con la cadena" % hecho,
                    hecho not in h["supplyChainFacts"])
        t.verdadero("E-41 %s no es un indicador debil" % hecho,
                    hecho not in h["weakIndicators"])
        t.igual("E-41 %s deja el hallazgo sospechoso" % hecho, "SUSPICIOUS_BEHAVIOR_DETECTED",
                h["status"])
        t.vacio("E-41 %s valida contra el contrato" % hecho, I.validar_hallazgo(h))

    # 🔴 Una senal con UN hecho no distingue «expone todos» de «expone el primero»: esa mutacion
    # pasaba verde (segundo veredicto). Hace falta una senal que traiga los once juntos, y
    # subconjuntos mezclados con hechos de cadena y con debiles, en desorden y por categorias que
    # no son de pipeline: la spec separa por VOCABULARIO, no por categoria.
    CADENA = ("PACKAGE_SOURCE_CHANGE", "REGISTRY_CHANGE", "GIT_URL_DEPENDENCY",
              "INSTALL_HOOK_CHANGE", "VERSION_JUMP", "PACKAGE_SUBSTITUTION",
              "TRANSITIVE_LOCKFILE_CHANGE")
    DEBILES = ("EVAL_PRESENT", "EXEC_PRESENT", "BASE64_PRESENT", "SHELL_COMMAND_PRESENT",
               "NEW_DOMAIN_PRESENT", "NEW_DEPENDENCY_PRESENT")
    combinaciones = [
        ("los once", ONCE, (), ()),
        ("los once al reves", tuple(reversed(ONCE)), (), ()),
        ("los once con repetidos", ONCE + ONCE[::3], (), ()),
        ("los impares con la cadena", ONCE[1::2], CADENA, ()),
        ("los pares con los debiles", ONCE[::2], (), DEBILES),
        ("los ultimos cuatro con todo", ONCE[-4:], CADENA[:3], DEBILES[2:]),
        ("los once con todo", ONCE, CADENA, DEBILES),
    ]
    categorias = ("CI_CD_TAMPERING", "DYNAMIC_CODE_EXECUTION", "UNRESOLVED_SUSPICIOUS_CHANGE",
                  "DEPENDENCY_SUBSTITUTION", "SECRET_EXFILTRATION")
    # 🔴 Y todas las demas dimensiones de la senal se BARREN, no se fijan: con archivo `.yml`,
    # sin evidencia directa, sin severidad y de a una senal por revision, sobrevivian una
    # capacidad que perdia los hechos al confirmar, que los exponia solo para un `.yml` o solo
    # con archivo, que los perdia al resolver la severidad, que los vaciaba desde el segundo
    # hallazgo o fuera del modo de incidente (tercer veredicto). El escenario dice que se exponen,
    # sin condiciones; el producto de abajo es lo que sostiene «sin condiciones».
    archivos = (("sin archivo", None), ("con un .yml", ".ci/deploy.yml"),
                ("con otro path", "src/app.py"), ("con un path sin extension", "Makefile"))
    directas = (False, True)
    severidades = (None, "high")
    casos = []
    for nombre, pipeline, cadena, debiles in combinaciones:
        for categoria in categorias:
            for directa in directas:
                for rotulo_archivo, archivo in archivos:
                    for escaner in severidades:
                        # Mezclados: el hecho de pipeline no llega primero, asi que «el primero»
                        # tampoco es siempre de pipeline.
                        entrada = list(debiles) + list(cadena) + list(pipeline)
                        extra = {}
                        if directa:
                            extra["directEvidenceReference"] = "captura del incidente #7"
                        if escaner:
                            extra["scannerSeverity"] = escaner
                        senal = _senal(categoria=categoria, indicadores=entrada,
                                       directa=directa, **extra)
                        senal["id"] = "f-%d" % len(casos)
                        if archivo is None:
                            senal.pop("file")
                        else:
                            senal["file"] = archivo
                        esperado = {"indicators": sorted(set(entrada)),
                                    "pipelineFacts": sorted(set(pipeline)),
                                    "supplyChainFacts": sorted(set(cadena)),
                                    "weakIndicators": sorted(set(debiles))}
                        rotulo = "E-41 %s, %s, %s, %s, %s" % (
                            nombre, categoria,
                            "con evidencia directa" if directa else "sin evidencia directa",
                            rotulo_archivo,
                            "con severidad del escaner" if escaner else "sin severidad")
                        casos.append((rotulo, senal, esperado))

    def _hechos(h):
        return {k: h[k] for k in ("indicators", "pipelineFacts", "supplyChainFacts",
                                  "weakIndicators")}

    sueltos = []
    for rotulo, senal, esperado in casos:
        h = I.hallazgo(senal, "ri-1", base, MAPEO)
        sueltos.append(h)
        t.igual("%s, por hallazgo: los hechos salen enteros" % rotulo, esperado, _hechos(h))
        t.vacio("%s, por hallazgo: valida contra el contrato" % rotulo, I.validar_hallazgo(h))

    # Todas las senales juntas en UNA revision, y en cada modo: el hallazgo n no depende de su
    # posicion ni del modo en que se investiga.
    senales = [s for _, s, _ in casos]
    for modo in I.MODOS:
        revision = I.revisar(BASE, _evidencia(), senales, modo=modo, mapeo=MAPEO)
        t.igual("E-41 en %s la revision publica un hallazgo por senal" % modo, len(casos),
                len(revision["findings"]))
        for (rotulo, senal, esperado), h in zip(casos, revision["findings"]):
            t.igual("%s, por la revision en %s: los hechos salen enteros" % (rotulo, modo),
                    esperado, _hechos(h))

    # Las premisas: cada dimension barrida de verdad cambia algo del hallazgo. Sin esto, un
    # barrido que no llegara a confirmado o no resolviera la severidad seria un barrido de nombre.
    confirmados = [h for h, (_, s, _) in zip(sueltos, casos) if s["directEvidence"]]
    t.verdadero("E-41 la premisa: con evidencia directa se llega a confirmado",
                confirmados and all(h["status"] == "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE"
                                    for h in confirmados))
    t.verdadero("E-41 la premisa: sin evidencia directa queda sospechoso",
                all(h["status"] == "SUSPICIOUS_BEHAVIOR_DETECTED"
                    for h, (_, s, _) in zip(sueltos, casos) if not s["directEvidence"]))
    t.verdadero("E-41 la premisa: con severidad del escaner, la severidad se resuelve",
                all(h["severity"]["value"] == "HIGH" and h["severityState"] is None
                    for h, (_, s, _) in zip(sueltos, casos) if "scannerSeverity" in s))
    t.verdadero("E-41 la premisa: sin ella, queda sin resolver",
                all(h["severity"]["value"] is None
                    and h["severityState"] == "SECURITY_SEVERITY_UNRESOLVED"
                    for h, (_, s, _) in zip(sueltos, casos) if "scannerSeverity" not in s))
    t.igual("E-41 la premisa: el archivo se barre en sus cuatro formas",
            [None, ".ci/deploy.yml", "Makefile", "src/app.py"],
            sorted(set(h["file"] for h in sueltos), key=lambda x: (x is not None, x or "")))
    t.igual("E-41 la premisa: el producto entero son 560 senales",
            560, len(casos))
    t.verdadero("E-41 la premisa: una combinacion trae los once a la vez",
                set(ONCE) <= set(combinaciones[0][1]))


def test_e42_la_sustitucion_de_origen_o_registro(t):
    """E-42 (RI-32)."""
    for hecho in ("PACKAGE_SOURCE_CHANGE", "REGISTRY_CHANGE", "PACKAGE_SUBSTITUTION"):
        t.verdadero("E-42 %s esta declarado" % hecho, hecho in I.HECHOS_DE_CADENA)
    senal = _senal(categoria="DEPENDENCY_SUBSTITUTION", indicadores=("REGISTRY_CHANGE",),
                   file="package.json")
    t.igual("E-42 se expone", "SUSPICIOUS_BEHAVIOR_DETECTED", I.estado_de_senal(senal))
    # 🔴 Y una dependencia nueva, sola, sigue siendo un indicador debil.
    nueva = _senal(categoria="DEPENDENCY_SUBSTITUTION", indicadores=("NEW_DEPENDENCY_PRESENT",))
    t.igual("E-42 una dependencia nueva sola es debil", "LOW", I.confianza(nueva))


def test_e43_los_hooks_de_instalacion(t):
    """E-43 (RI-33)."""
    t.verdadero("E-43 el hecho esta declarado", "INSTALL_HOOK_CHANGE" in I.HECHOS_DE_CADENA)
    SIETE = ("PACKAGE_SOURCE_CHANGE", "REGISTRY_CHANGE", "GIT_URL_DEPENDENCY",
             "INSTALL_HOOK_CHANGE", "VERSION_JUMP", "PACKAGE_SUBSTITUTION",
             "TRANSITIVE_LOCKFILE_CHANGE")
    t.igual("E-43 son estos siete los hechos de cadena", SIETE, I.HECHOS_DE_CADENA)
    base = I.baseline(BASE)[0]
    for hecho in SIETE:
        h = I.hallazgo(_senal(categoria="BUILD_SCRIPT_TAMPERING", indicadores=(hecho,)),
                       "ri-1", base, MAPEO)
        t.verdadero("E-43 %s se expone como hecho de cadena" % hecho,
                    hecho in h["supplyChainFacts"])
        t.verdadero("E-43 %s no se confunde con el pipeline" % hecho,
                    hecho not in h["pipelineFacts"])
        t.igual("E-43 %s deja el hallazgo sospechoso" % hecho,
                "SUSPICIOUS_BEHAVIOR_DETECTED", h["status"])


# -- E-44 a E-48 — el analisis dinamico ----------------------------------------

def test_e44_el_binario_no_se_ejecuta_solo(t):
    """E-44 (RI-34)."""
    t.verdadero("E-44 nunca se ejecuta automaticamente", I.ejecucion_automatica_de_binario()
                is False)
    t.igual("E-44 el analisis por defecto es estatico", "STATIC", I.ESTATICO)
    sin_nada = I.analisis_dinamico({}, "SECURITY_INCIDENT")
    t.verdadero("E-44 sin pedido, no se permite", not sin_nada["allowed"])


def test_e45_lo_dinamico_exige_las_cuatro(t):
    """E-45 (RI-35) — aislamiento, autorizacion, contencion y preservacion."""
    preservada = I.instantanea(_evidencia())
    completo = {"isolatedEnvironment": True,
                "authorization": {"explicit": True, "reference": "acta de incidente #7"},
                "networkContainment": True, "evidencePreserved": preservada}
    t.verdadero("E-45 con las cuatro, se permite",
                I.analisis_dinamico(completo, "SECURITY_INCIDENT")["allowed"])
    for falta in ("authorization", "networkContainment", "evidencePreserved"):
        pedido = dict(completo)
        pedido.pop(falta)
        salida = I.analisis_dinamico(pedido, "SECURITY_INCIDENT")
        t.verdadero("E-45 sin %s no se permite" % falta, not salida["allowed"])
        t.verdadero("E-45 sin %s sigue pidiendo revision humana" % falta,
                    salida["requiresHumanReview"])


def test_e46_sin_ambiente_aislado(t):
    """E-46 (RI-36) — DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE."""
    preservada = I.instantanea(_evidencia())
    pedido = {"isolatedEnvironment": False,
              "authorization": {"explicit": True, "reference": "acta"},
              "networkContainment": True, "evidencePreserved": preservada}
    salida = I.analisis_dinamico(pedido, "SECURITY_INCIDENT")
    t.igual("E-46 el estado", "DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE", salida["state"])
    t.verdadero("E-46 no se permite", not salida["allowed"])
    t.verdadero("E-46 y es la primera compuerta",
                salida["reasons"] == ["DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE"])


def test_e47_pasa_por_la_compuerta_de_tools(t):
    """E-47 (RI-37) — la del harness, no una propia."""
    preservada = I.instantanea(_evidencia())
    contrato = {"sideEffects": "DESTRUCTIVE", "riskLevel": "LOW", "networkAccess": True,
                "blastRadius": {"scope": "external-system", "productionImpact": False}}
    pedido = {"isolatedEnvironment": True,
              "authorization": {"explicit": True, "reference": "acta"},
              "networkContainment": True, "evidencePreserved": preservada}
    salida = I.analisis_dinamico(pedido, "SECURITY_INCIDENT", contrato)
    t.igual("E-47 el riesgo lo deriva tools", "CRITICAL", salida["toolRisk"])
    t.verdadero("E-47 y tools rechaza el declarado de menos", bool(salida["toolRiskErrors"]))
    t.verdadero("E-47 asi que no se permite", not salida["allowed"])
    t.verdadero("E-47 tools exige aprobacion humana", salida["toolRequiresHumanApproval"])
    # 🔴 Y la compuerta es la de tools: el mismo contrato le da lo mismo a los dos.
    t.igual("E-47 el mismo riesgo que tools deriva", c_tools.derivar_riesgo(contrato),
            salida["toolRisk"])


def test_e48_una_tool_que_ejecuta_en_el_host(t):
    """E-48 (RI-38) — no puede nacer de bajo riesgo ni por defecto."""
    contrato = {"sideEffects": "DESTRUCTIVE", "riskLevel": "LOW",
                "blastRadius": {"scope": "external-system", "productionImpact": True}}
    t.igual("E-48 el riesgo derivado es el maximo", "CRITICAL", c_tools.derivar_riesgo(contrato))
    t.verdadero("E-48 declarar de menos se rechaza", bool(c_tools.controlar_riesgo(contrato)))
    t.verdadero("E-48 y exige aprobacion humana", c_tools.exige_aprobacion_humana(contrato))
    # Y una tool no nace aprobada.
    t.verdadero("E-48 ninguna tool nace APPROVED", "APPROVED" not in c_tools.AL_NACER)


# -- E-49 a E-51 — la compuerta, la remediacion y los proveedores --------------

def test_e49_la_compuerta_humana(t):
    """E-49 (RI-39, RI-40) — las siete causas."""
    SIETE = ("CONFIRMED_MALICIOUS_BEHAVIOR", "HIGH_CONFIDENCE_SUSPICION", "REMEDIATION_PROPOSED",
             "SECRET_ROTATION_PROPOSED", "DYNAMIC_EXECUTION_PROPOSED", "BASELINE_DISPUTED",
             "CONTRADICTORY_EVIDENCE")
    t.igual("E-49 son estas siete causas", SIETE, I.CAUSAS_DE_REVISION)
    base = I.baseline(BASE)[0]
    confirmado = I.hallazgo(_confirmada(), "ri-1", base, MAPEO)
    g = I.compuerta_humana({"findings": [confirmado]})
    t.verdadero("E-49 un confirmado la exige", g["required"])
    t.igual("E-49 con su estado", "HUMAN_SECURITY_REVIEW_REQUIRED", g["state"])
    t.verdadero("E-49 y nombra la causa", "CONFIRMED_MALICIOUS_BEHAVIOR" in g["causes"])

    alto = I.hallazgo(_senal(indicadores=("REVERSE_SHELL_ESTABLISHED", "DATA_SENT_OFF_HOST")),
                      "ri-1", base, MAPEO)
    t.igual("E-49 confianza alta", "HIGH", alto["confidence"])
    t.verdadero("E-49 la exige tambien",
                I.compuerta_humana({"findings": [alto]})["required"])

    for bandera, causa in (("remediationProposed", SIETE[2]),
                           ("secretRotationProposed", SIETE[3]),
                           ("dynamicExecutionProposed", SIETE[4]),
                           ("baselineDisputed", SIETE[5]),
                           ("contradictoryEvidence", SIETE[6])):
        g = I.compuerta_humana({"findings": [], bandera: True})
        t.verdadero("E-49 %s la exige" % bandera, g["required"])
        t.verdadero("E-49 %s nombra su causa" % bandera, causa in g["causes"])
    t.verdadero("E-49 sin causas no se exige",
                not I.compuerta_humana({"findings": []})["required"])


def test_e50_la_remediacion_es_otra_unidad(t):
    """E-50 (RI-48, RI-49) — enlazada, y la evidencia original no cambia."""
    base = I.baseline(BASE)[0]
    revision = I.revisar(BASE, _evidencia(), [_confirmada()], mapeo=MAPEO)
    sello_original = revision["snapshot"]["seal"]
    unidad = I.unidad_de_remediacion(revision["reviewId"], revision["findings"],
                                     {"explicit": True, "reference": "acta"})
    t.igual("E-50 es otra unidad", "REMEDIATION", unidad["workUnitType"])
    t.igual("E-50 enlazada a la revision", revision["reviewId"], unidad["linkedReviewId"])
    t.igual("E-50 y a los hallazgos", [h["findingId"] for h in revision["findings"]],
            unidad["linkedFindings"])
    t.verdadero("E-50 sigue exigiendo revision humana", unidad["requiresHumanReview"])
    t.verdadero("E-50 y declara que la evidencia se conserva",
                unidad["originalEvidencePreserved"])

    # 🔴 La evidencia original no cambia: tocar la unidad no toca la revision, y el sello lo dice.
    unidad["linkedFindings"].append("inventado")
    t.igual("E-50 el sello de la instantanea no cambio", sello_original,
            revision["snapshot"]["seal"])
    t.verdadero("E-50 y sigue siendo valido", I.sello_valido(revision["snapshot"]))
    t.igual("E-50 los hallazgos de la revision siguen igual", 1, len(revision["findings"]))


def test_e51_los_dos_proveedores_normalizan_igual(t):
    """E-51 (RI-44, RI-45) — la misma forma, y nada propio del proveedor adentro."""
    gitlab = {"project_path": "gcba/tramites", "ref": "refs/heads/trabajo", "id": COMMIT_ACTUAL,
              "parent_ids": [COMMIT_BASE], "author_email": "alguien@example",
              "committer_email": "alguien@example", "committed_date": "2026-09-20",
              # 🔴 Cada entrada lleva los campos PROPIOS de GitLab junto a los normalizados: con
              # solo path/operation/kind, un adaptador que copiara la entrada entera pasaba verde
              # (segundo veredicto).
              "diffs": [{"path": "src/app.py", "operation": "MODIFIED", "kind": "SOURCE",
                         "old_path": "src/ruta-vieja-de-gitlab.py", "new_path": "src/app.py",
                         "a_mode": "100644", "b_mode": "100755", "new_file": False,
                         "renamed_file": True, "deleted_file": False, "generated_file": False,
                         "diff": "@@ -1 +1 @@ cuerpo-del-diff-de-gitlab"}],
              "stats": {"additions": 12, "deletions": 3, "total": 15,
                        "web_url": "una-url-de-stats-de-gitlab"},
              "signature": {"verification_status": "verified"},
              "web_url": "una-url-de-gitlab", "iid": 4412, "project_id": 77}
    github = {"full_name": "gcba/tramites", "ref": "refs/heads/trabajo", "sha": COMMIT_ACTUAL,
              "parents": [{"sha": COMMIT_BASE}],
              "commit": {"author": {"email": "alguien@example", "date": "2026-09-20"},
                         "committer": {"email": "alguien@example"},
                         "verification": {"verified": True}},
              "files": [{"path": "src/app.py", "operation": "MODIFIED", "kind": "SOURCE",
                         "sha": "d" * 40, "filename": "src/app.py", "status": "renamed",
                         "additions": 12, "deletions": 3, "changes": 15,
                         "blob_url": "una-blob-url-de-github", "raw_url": "una-raw-url-de-github",
                         "contents_url": "una-contents-url-de-github",
                         "patch": "@@ -1 +1 @@ cuerpo-del-patch-de-github",
                         "previous_filename": "src/ruta-vieja-de-github.py"}],
              "stats": {"additions": 12, "deletions": 3, "total": 15,
                        "html_url": "una-url-de-stats-de-github"},
              "node_id": "un-node-id", "html_url": "una-url-de-github"}

    uno = I.normalizar(gitlab, "GITLAB")
    dos = I.normalizar(github, "GITHUB")
    t.igual("E-51 las dos formas tienen las mismas claves", sorted(uno), sorted(dos))
    for campo in ("repository", "ref", "commitSha", "parents", "changedFiles"):
        t.igual("E-51 %s normaliza igual" % campo, uno[campo], dos[campo])
    t.igual("E-51 los dos declaran verificado", (True, True), (uno["verified"], dos["verified"]))
    t.igual("E-51 y cada uno declara su proveedor", ("GITLAB", "GITHUB"),
            (uno["provider"], dos["provider"]))

    # 🔴 El barrido es RECURSIVO sobre todo lo que sale, no sobre las claves de arriba: un campo
    # propio metido adentro de cada archivo normalizado viaja al inventario y a la instantanea, y
    # un barrido de primer nivel no lo ve. Es la leccion de D8/E-34 que la spec cita.
    def _claves(dato, acumulado):
        if isinstance(dato, dict):
            for k, v in dato.items():
                acumulado.add(k)
                _claves(v, acumulado)
        elif isinstance(dato, list):
            for v in dato:
                _claves(v, acumulado)
        return acumulado

    # Las claves de cada nivel, clavadas por literal: un archivo normalizado lleva estas cinco y
    # ninguna mas, y el resumen del diff estas tres. Un barrido global con una lista permitida
    # dejaba pasar un `additions` de GitHub adentro de un archivo, porque `additions` es legitima
    # un nivel mas arriba.
    DE_ARCHIVO = ["afterHash", "beforeHash", "kind", "operation", "path"]
    DE_DIFF = {"additions", "deletions", "total"}
    PERMITIDAS = set(I.CAMPOS_NORMALIZADOS) | set(DE_ARCHIVO) | DE_DIFF
    for salida, quien in ((uno, "GitLab"), (dos, "GitHub")):
        t.vacio("E-51 %s no lleva ninguna clave de mas" % quien,
                sorted(_claves(salida, set()) - PERMITIDAS))
        t.verdadero("E-51 la premisa: %s trae archivos que mirar" % quien,
                    len(salida["changedFiles"]) == 1)
        for archivo in salida["changedFiles"]:
            t.igual("E-51 un archivo de %s lleva exactamente las cinco claves" % quien,
                    DE_ARCHIVO, sorted(archivo))
        t.vacio("E-51 el diffMeta de %s no lleva claves de mas" % quien,
                sorted(set(salida["diffMeta"]) - DE_DIFF))
        t.igual("E-51 y conserva las tres cuentas de %s" % quien,
                {"additions": 12, "deletions": 3, "total": 15}, salida["diffMeta"])
    # Los propios de cada proveedor: los de arriba, los de cada archivo y los del resumen.
    PROPIOS = ("web_url", "iid", "project_id", "project_path", "node_id", "html_url",
               "full_name", "parent_ids", "committed_date", "signature", "diffs", "files",
               "sha", "commit", "parents_raw",
               "old_path", "new_path", "a_mode", "b_mode", "new_file", "renamed_file",
               "deleted_file", "generated_file", "diff",
               "filename", "status", "changes", "blob_url", "raw_url", "contents_url",
               "patch", "previous_filename")
    VALORES = ("una-url-de-gitlab", "una-url-de-github", "un-node-id", "4412",
               "src/ruta-vieja-de-gitlab.py", "100755", "cuerpo-del-diff-de-gitlab",
               "una-url-de-stats-de-gitlab", "d" * 40, "una-blob-url-de-github",
               "una-raw-url-de-github", "una-contents-url-de-github",
               "cuerpo-del-patch-de-github", "src/ruta-vieja-de-github.py",
               "una-url-de-stats-de-github")
    for propio in PROPIOS:
        for salida, quien in ((uno, "GitLab"), (dos, "GitHub")):
            t.verdadero("E-51 %s no lleva `%s` en ningun nivel" % (quien, propio),
                        propio not in _claves(salida, set()))
    texto = json.dumps([uno, dos], ensure_ascii=False)
    for valor in VALORES:
        t.verdadero("E-51 el valor `%s` no viaja" % valor, valor not in texto)
    crudo = json.dumps([gitlab, github], ensure_ascii=False)
    t.verdadero("E-51 la premisa: los valores propios SI estaban en la entrada",
                all(v in crudo for v in VALORES))

    # 🔴 Y el escenario dice «no llega AL HALLAZGO» ni a ningun nivel de la salida: hay que
    # construir la revision entera desde la evidencia normalizada —instantanea, inventario y
    # hallazgos— y barrerla, no quedarse en la traduccion.
    for salida, quien in ((uno, "GitLab"), (dos, "GitHub")):
        revision = I.revisar(BASE, salida, [_senal()], mapeo=MAPEO)
        claves = _claves(revision["findings"][0], set())
        t.vacio("E-51 el hallazgo por %s no lleva claves de proveedor" % quien,
                sorted(claves - set(CLAVES_DE_HALLAZGO) - {"value", "source"}))
        # `status` es tambien una clave del hallazgo —su veredicto—, asi que en la revision se
        # barre el resto; el hallazgo ya quedo cerrado arriba contra su lista exacta.
        todas = _claves(revision, set())
        for propio in [p for p in PROPIOS if p != "status"]:
            t.verdadero("E-51 ni la revision por %s lleva `%s` en ningun nivel" % (quien, propio),
                        propio not in todas)
        entero = json.dumps(revision, ensure_ascii=False, default=str)
        for valor in VALORES:
            t.verdadero("E-51 ni la revision por %s lleva `%s`" % (quien, valor),
                        valor not in entero)
        t.igual("E-51 la instantanea por %s guarda el resumen normalizado" % quien,
                {"additions": 12, "deletions": 3, "total": 15},
                revision["snapshot"]["diffMeta"])

    # Y el nucleo consume lo normalizado: el inventario sale igual con los dos.
    t.igual("E-51 el inventario es el mismo por los dos caminos",
            json.dumps(I.inventario(I.baseline(BASE)[0], uno), sort_keys=True),
            json.dumps(I.inventario(I.baseline(BASE)[0], dos), sort_keys=True))
    t.igual("E-51 son dos los proveedores declarados", ("GITLAB", "GITHUB"), I.PROVEEDORES)
