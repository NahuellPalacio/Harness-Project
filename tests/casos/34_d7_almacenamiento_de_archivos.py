# D7: tres obligaciones en una sola oracion, verificadas por separado, sin inventar el repositorio.
#
# Escenarios E-01 a E-45 de docs/cambios/d7-almacenamiento-de-archivos/spec.md. Entre parentesis,
# el D7-nn del pedido de instalacion.
#
# 🔴 Nada de esto escribe, sube ni borra un archivo. Lo que se verifica son los CONTROLES: que la
# identidad del storage estandar entre como dato declarado y no se invente, que una libreria del
# protocolo no alcance, que el nombre de un path no clasifique un ciclo de vida, y que "inmediata"
# se opere como un momento y no como un numero.
import importlib.util
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
# `desde` se resuelve caminando hacia arriba desde un ARCHIVO, no desde un directorio.
RUTA_REG = str(BIN / "orquestacion" / "registro_agentes.py")

sys.path.insert(0, str(BIN))
sys.path.insert(0, str(CONTROLES / "lib"))
from orquestacion import controles as c_controles    # noqa: E402
from orquestacion import matriz as c_matriz          # noqa: E402
from orquestacion import normativa as c_normativa    # noqa: E402
from orquestacion import registro_agentes as c_reg   # noqa: E402
from orquestacion import senales as c_senales        # noqa: E402

import flujos as FLUJOS                              # noqa: E402


def _cargar(nombre, alias):
    spec = importlib.util.spec_from_file_location(alias, CONTROLES / "checks" / (nombre + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


SB = _cargar("storage-backend-compliance", "d7_sb")
PL = _cargar("persistent-local-file-storage", "d7_pl")
TC = _cargar("temporary-file-cleanup", "d7_tc")

SENAL = "fileHandlingPresent"
POLICIES = ("gcba-standard-storage-required", "persistent-local-file-storage-prohibited",
            "temporary-file-immediate-destruction-required")
CHEQUEOS = ("storage-backend-compliance", "persistent-local-file-storage",
            "temporary-file-cleanup")
MODULOS = ((CHEQUEOS[0], SB), (CHEQUEOS[1], PL), (CHEQUEOS[2], TC))

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D7"}

BUILD = {"id": "b-instalacion-de-d7", "runtime": "runtime-de-prueba"}
ALMACEN = {"id": "repositorio-estandar", "source": "GCBA_NORMATIVE",
           "reference": "ES0901 6.3, pag. 19", "protocol": "S3"}
CONTRATO = {"id": "contrato-de-integracion-del-storage", "source": "ASI_INTEGRATION_CONTRACT",
            "reference": "acta de integracion del proyecto"}

LOCAL_OK = {"pathOrAdapter": "./staging", "purpose": "convertir un reporte a pdf",
            "creation": "el servicio de reportes", "consumption": "el mismo servicio",
            "cleanup": "al terminar la conversion", "expectedLifetime": "la operacion acotada",
            "persistenceBehavior": "TEMPORARY"}


# -- las piezas de los casos ---------------------------------------------------

def _ev_senal(eid="s-1", tipo="PROJECT_DOCUMENTATION", ref="ficha de proyecto",
              claim="la aplicacion recibe adjuntos y los guarda", **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": ref, "claim": claim}
    e.update(extra)
    return e


def _senal(valor="TRUE", evidencia=None, sid=SENAL, **extra):
    s = {"signalId": sid, "value": valor,
         "evidence": [_ev_senal()] if evidencia is None else evidencia,
         "producer": {"type": "HUMAN"}}
    s.update(extra)
    return s


def _sin_archivos():
    """La senal en FALSE con evidencia que lo sostiene. Se usa en los tres checks."""
    return _senal("FALSE", [_ev_senal(claim="el alcance esta completo y no gestiona archivos")])


def _ev(eid, tipo, **extra):
    e = {"evidenceId": eid, "sourceType": tipo, "reference": "corrida#1",
         "claim": "lo que la corrida reporta", "buildId": BUILD["id"],
         "runtime": BUILD["runtime"]}
    e.update(extra)
    return e


def _evidencias():
    return ([_ev("e-persistencia", FLUJOS.TRAZA_DE_PERSISTENCIA, mechanism=ALMACEN["id"]),
             _ev("e-local", FLUJOS.TRAZA_DE_ESCRITURA_LOCAL)]
            + [_ev("c-" + n, FLUJOS.TRAZA_DE_LIMPIEZA) for n in FLUJOS.CAMINOS])


def _persistente(fid="f-adjuntos", clase=FLUJOS.ESTANDAR, mecanismo=ALMACEN["id"],
                 refs=("e-persistencia",)):
    return {"id": fid, "classification": clase, "operations": ["RECEIVE", "STORE"],
            "storageMechanism": mecanismo, "evidenceRefs": list(refs)}


def _camino(nombre, mecanismos=(FLUJOS.CICLO_DE_VIDA,), refs=None):
    return {"path": nombre, "mechanisms": list(mecanismos),
            "evidenceRefs": ["c-" + nombre] if refs is None else list(refs)}


def _caminos(mecanismos=(FLUJOS.CICLO_DE_VIDA,), nombres=None, refs=None):
    return [_camino(n, mecanismos, refs) for n in (nombres or FLUJOS.CAMINOS_SIEMPRE)]


def _temporal(fid="f-temporal", clase=FLUJOS.LOCAL_TEMPORAL, caminos=None, local=None,
              temporal=None, refs=("e-local",)):
    """Un flujo temporal local: lleva los dos bloques, porque lo miran los dos checks."""
    bloque_local = dict(LOCAL_OK)
    bloque_local.update(local or {})
    bloque = {"boundedPurpose": "convertir un reporte a pdf", "technique": "context manager",
              "cleanupPaths": _caminos() if caminos is None else list(caminos)}
    bloque.update(temporal or {})
    return {"id": fid, "classification": clase,
            "operations": ["GENERATE", "TEMPORARY_PROCESSING"],
            "local": bloque_local, "temporary": bloque, "evidenceRefs": list(refs)}


def _local(fid="f-permanente", clase=FLUJOS.LOCAL_PERMANENTE, refs=("e-local",), **campos):
    """Una escritura local sin bloque temporal: la mira `persistent-local-file-storage`."""
    bloque = dict(LOCAL_OK)
    bloque.update({"purpose": "guardar los adjuntos", "pathOrAdapter": "un directorio del server",
                   "cleanup": "no se limpia", "expectedLifetime": "indefinida",
                   "persistenceBehavior": "PERSISTENT"})
    bloque.update(campos)
    return {"id": fid, "classification": clase, "operations": ["STORE", "SERVE"],
            "local": bloque, "evidenceRefs": list(refs)}


def _caso(flujos=None, evidencia=None, fuente="PROJECT_ARCHITECTURE", completo=True, **extra):
    caso = {
        "application": {"id": "tramites", "environment": "test"},
        "build": dict(BUILD),
        "testTarget": {"available": True},
        "standardStorage": dict(ALMACEN),
        "integrationContract": dict(CONTRATO),
        "fileFlows": {"source": fuente, "complete": completo,
                      "flows": [_persistente()] if flujos is None else list(flujos)},
        "evidence": _evidencias() if evidencia is None else list(evidencia),
    }
    caso.update(extra)
    return caso


def _mixto(persistente=None, temporal=None):
    """Una aplicacion con un flujo persistente y uno temporal, los dos cumpliendo."""
    return _caso(flujos=[persistente or _persistente(), temporal or _temporal()])


def _estados(caso, senal):
    """El estado de los tres checks para un mismo caso. Es como se lee la independencia."""
    return {nombre: modulo.evaluar(caso, senal)["state"] for nombre, modulo in MODULOS}


# -- los caminos de cada check, uno por estado ---------------------------------

def _sin_ciclo():
    return _temporal(fid="f-sin-ciclo", local={"expectedLifetime": ""})


def _caminos_de_sb():
    return {
        "PASS": (_caso(), _senal()),
        "FAIL": (_caso(flujos=[_persistente(mecanismo="otro-repositorio")]), _senal()),
        "PARTIAL": (_caso(flujos=[_persistente(refs=())]), _senal()),
        "NOT_APPLICABLE": (_caso(), _sin_archivos()),
        "APPLICABILITY_UNRESOLVED": (_caso(), None),
        "FILE_FLOW_COVERAGE_UNRESOLVED": (_caso(fileFlows={}), _senal()),
        "STANDARD_STORAGE_PROVIDER_UNRESOLVED": (_caso(standardStorage={}), _senal()),
        "STORAGE_INTEGRATION_CONTRACT_MISSING": (_caso(integrationContract={}), _senal()),
        "TEST_TARGET_UNAVAILABLE": (_caso(testTarget={}), _senal()),
    }


def _caminos_de_pl():
    return {
        "PASS": (_caso(flujos=[_temporal()]), _senal()),
        "FAIL": (_caso(flujos=[_local()]), _senal()),
        "PARTIAL": (_caso(flujos=[_temporal(), _sin_ciclo()]), _senal()),
        "NOT_APPLICABLE": (_caso(), _sin_archivos()),
        "APPLICABILITY_UNRESOLVED": (_caso(), None),
        "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED": (_caso(flujos=[_sin_ciclo()]), _senal()),
        "FILE_FLOW_COVERAGE_UNRESOLVED": (_caso(fileFlows={}), _senal()),
        "TEST_TARGET_UNAVAILABLE": (_caso(testTarget={}), _senal()),
    }


def _caminos_de_tc():
    return {
        "PASS": (_caso(flujos=[_temporal()]), _senal()),
        "FAIL": (_caso(flujos=[_temporal(caminos=_caminos(("PERIODIC",)))]), _senal()),
        "PARTIAL": (_caso(flujos=[_temporal(caminos=_caminos(refs=()))]), _senal()),
        "NOT_APPLICABLE": (_caso(flujos=[_temporal()]), _sin_archivos()),
        "APPLICABILITY_UNRESOLVED": (_caso(), None),
        "FILE_FLOW_COVERAGE_UNRESOLVED": (_caso(fileFlows={}), _senal()),
        "TEMPORARY_FILE_LIFECYCLE_UNRESOLVED": (
            _caso(flujos=[_temporal(temporal={"boundedPurpose": ""})]), _senal()),
        "CLEANUP_PATH_COVERAGE_UNRESOLVED": (
            _caso(flujos=[_temporal(caminos=_caminos(nombres=(FLUJOS.CAMINO_NORMAL,)))]),
            _senal()),
        "TEST_TARGET_UNAVAILABLE": (_caso(testTarget={}), _senal()),
    }


TODOS_LOS_CAMINOS = ((CHEQUEOS[0], SB, _caminos_de_sb), (CHEQUEOS[1], PL, _caminos_de_pl),
                     (CHEQUEOS[2], TC, _caminos_de_tc))


# -- E-01 a E-07 — la senal y la aplicabilidad ---------------------------------

def test_e01_d7_es_condicional(t):
    """E-01 (D7-01) — CONDITIONAL sobre la senal, y la matriz no la edito este cambio."""
    d7 = c_matriz.regla("D7")
    t.igual("E-01 el modo", "CONDITIONAL", d7["applicability"]["mode"])
    t.igual("E-01 la senal", [SENAL], d7["applicability"]["signals"])
    t.igual("E-01 el id", "D7", d7["id"])
    t.igual("E-01 la categoria", "DESIGN", d7["category"])
    t.igual("E-01 la intencion operativa no cambio",
            "Files must use GCBA standard storage; permanent local storage is prohibited; "
            "temporary files must be destroyed immediately.", d7["operationalIntentEn"])
    t.igual("E-01 el dueno normativo", ["dev-backend"], d7["primaryAgents"])
    t.igual("E-01 las tres policies ya estaban declaradas", list(POLICIES), d7["policies"])
    t.igual("E-01 y los tres checks", list(CHEQUEOS), d7["checks"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", d7["status"])
    t.igual("E-01 la senal la declara D7 y nadie mas", ["D7"], c_senales.reglas_de(SENAL))

    # 🔴 La mitad de "sin que este cambio la edite" que SI se puede sostener: la fila tiene
    # exactamente las claves que tienen las otras filas de diseno. Un campo agregado —una skill,
    # una excepcion, un umbral— se ve acá aunque el valor de los otros campos no cambie.
    otras = [r for r in c_matriz.reglas()
             if r.get("category") == "DESIGN" and r.get("id") != "D7"]
    t.verdadero("E-01 hay otras filas de diseno contra las que comparar", len(otras) >= 5)
    comunes = set(otras[0].keys())
    todas = set(otras[0].keys())
    for otra in otras:
        comunes &= set(otra.keys())
        todas |= set(otra.keys())
    t.igual("E-01 la fila de D7 tiene las claves que toda fila de diseno tiene",
            sorted(comunes), sorted(d7.keys()))
    t.vacio("E-01 y ninguna que no exista en el resto de la matriz",
            sorted(set(d7.keys()) - todas))
    t.verdadero("E-01 `reviews` es opcional y alguna otra fila lo trae",
                "reviews" in todas and "reviews" not in comunes)


def test_e02_true_hace_aplicable(t):
    """E-02 (D7-02) — TRUE con evidencia deja D7 aplicable con sus seis controles."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    t.verdadero("E-02 D7 aplica", "D7" in bloque["applicableRules"])
    for pid in POLICIES:
        t.verdadero("E-02 exige %s" % pid, pid in bloque["declaredPolicies"])
    for cid in CHEQUEOS:
        t.verdadero("E-02 exige %s" % cid, cid in bloque["declaredChecks"])
    t.igual("E-02 la senal resuelta viaja", "TRUE", bloque["signals"][SENAL]["value"])


def test_e03_false_hace_no_aplicable(t):
    """E-03 (D7-03) — FALSE con evidencia deja D7 fuera, y los tres checks NOT_APPLICABLE."""
    bloque = c_normativa.resolucion({SENAL: _sin_archivos()})
    t.verdadero("E-03 D7 no aplica", "D7" in bloque["notApplicableRules"])
    t.verdadero("E-03 y no esta entre las aplicables", "D7" not in bloque["applicableRules"])
    for nombre, estado in _estados(_caso(), _sin_archivos()).items():
        t.igual("E-03 %s no aplica" % nombre, "NOT_APPLICABLE", estado)


def test_e04_sin_senal_no_se_resuelve(t):
    """E-04 (D7-04) — sin la senal, APPLICABILITY_UNRESOLVED con el nombre de la que falta."""
    bloque = c_normativa.resolucion({})
    sin_resolver = {u["rule"]: u for u in bloque["unresolvedRules"]}
    t.verdadero("E-04 D7 queda sin resolver", "D7" in sin_resolver)
    t.igual("E-04 con la senal que falta", [SENAL], sin_resolver["D7"]["missingSignals"])
    for nombre, modulo in MODULOS:
        salida = modulo.evaluar(_caso(), None)
        t.igual("E-04 %s sin resolver" % nombre, "APPLICABILITY_UNRESOLVED", salida["state"])
        t.igual("E-04 %s dice que senal falta" % nombre, [SENAL], salida["missingSignals"])
        t.verdadero("E-04 %s no aprueba" % nombre, not modulo.aprueba(salida))


def test_e05_la_ausencia_nunca_es_false(t):
    """E-05 (D7-05) — lo ausente queda UNRESOLVED, y lo no declarado se rechaza."""
    sin_evidencia = c_senales.resolver_una(_senal("FALSE", []))
    t.igual("E-05 FALSE sin evidencia no queda en FALSE", "UNRESOLVED", sin_evidencia["value"])
    t.verdadero("E-05 y lo dice", "SIGNAL_EVIDENCE_MISSING" in sin_evidencia["states"])

    no_declarada = c_senales.resolver_una(_senal("TRUE", sid="fileHandling"))
    t.verdadero("E-05 una senal que la matriz no declara se rechaza",
                "SIGNAL_NOT_DECLARED" in no_declarada["states"])

    # 🔴 Las tres frases de ausencia, en las DOS clases debiles. Ninguna prueba que no haya
    # archivos: prueban que nadie lo escribio, y el comportamiento de archivo se esconde detras
    # de librerias, servicios compartidos y artefactos generados.
    t.igual("E-05 son dos las clases debiles", ("AGENT_STATEMENT", "REPOSITORY_DEPENDENCY"),
            c_senales.FUENTES_DEBILES)
    ausencias = ("no existe ningun literal .pdf en el repositorio",
                 "no hay ningun componente de subida en el frontend",
                 "no se encontro ninguna llamada al filesystem en el archivo que se leyo")
    for tipo in c_senales.FUENTES_DEBILES:
        for claim in ausencias:
            resuelta = c_senales.resolver_una(_senal("FALSE", [
                _ev_senal(tipo=tipo, claim=claim, supports="FALSE")]))
            t.igual("E-05 %s no baja a FALSE: %s" % (tipo[:5], claim[:30]), "UNRESOLVED",
                    resuelta["value"])
            for nombre, modulo in MODULOS:
                t.igual("E-05 y %s sigue sin resolver" % nombre, "APPLICABILITY_UNRESOLVED",
                        modulo.evaluar(_caso(), resuelta)["state"])

    # 🔴 Y el limite, dicho: el harness confia en la ETIQUETA de la fuente. La misma frase de
    # ausencia etiquetada como dato estructurado si apaga la regla, y `senales.py` no tiene como
    # distinguir una observacion de ausencia de un alcance declarado completo. Es una afirmacion
    # de quien la etiqueta, queda citada y es refutable — y esta escrita donde se lee.
    etiquetada = c_senales.resolver_una(_senal("FALSE", [
        _ev_senal(tipo="TASK_CONTEXT", claim=ausencias[0], supports="FALSE")]))
    t.igual("E-05 el limite: con una fuente de la lista, la misma frase apaga D7", "FALSE",
            etiquetada["value"])
    t.igual("E-05 y el check lo informa como no aplicable", "NOT_APPLICABLE",
            SB.evaluar(_caso(), etiquetada)["state"])
    t.verdadero("E-05 el limite esta anotado en la doc",
                "el harness confía en la etiqueta de la fuente" in _seccion_de_d7_del_doc()[1])
    t.verdadero("E-05 y dice que sigue abierto para las otras quince",
                "sólo para D5" in _seccion_de_d7_del_doc()[1])


def test_e06_un_flujo_es_mas_que_una_subida(t):
    """E-06 (§1) — las once operaciones sostienen la senal por igual."""
    t.igual("E-06 son once operaciones declaradas", 11, len(FLUJOS.OPERACIONES))
    t.verdadero("E-06 la subida es una de las once", "UPLOAD" in FLUJOS.OPERACIONES)
    for op in FLUJOS.OPERACIONES:
        senal = _senal("TRUE", [_ev_senal(tipo="TASK_CONTEXT", reference="alcance",
                                          claim="la unidad de trabajo declara %s de archivos"
                                                % op, supports="TRUE")])
        bloque = c_normativa.resolucion({SENAL: senal})
        t.verdadero("E-06 %s hace aplicable a D7" % op, "D7" in bloque["applicableRules"])


def test_e07_ninguna_otra_senal_sustituye(t):
    """E-07 (§1) — con cualquier otra senal en TRUE, D7 y sus tres checks siguen sin resolver."""
    otras = sorted(c_senales.declaradas() - {SENAL})
    t.verdadero("E-07 hay otras senales declaradas contra las que probar", len(otras) >= 10)
    for otra in otras:
        bloque = c_matriz.resolver({otra: True})
        sin_resolver = {u["rule"] for u in bloque["unresolvedRules"]}
        t.verdadero("E-07 %s no hace aplicable a D7" % otra, "D7" in sin_resolver)

        # 🔴 Y la senal ajena LLEGA a los checks, que es la mitad que faltaba: pasandoles `None`
        # la entrada era identica a la de E-04 y la clausula distintiva de este escenario —"con
        # cualquiera de las otras en TRUE"— no se probaba nunca. Sin el control de `signalId`,
        # dos de los tres daban PASS y los tres publicaban `fileHandlingPresent` como origen.
        for nombre, modulo in MODULOS:
            salida = modulo.evaluar(_caso(), _senal("TRUE", sid=otra))
            t.igual("E-07 %s con %s sigue sin resolver" % (nombre, otra),
                    "APPLICABILITY_UNRESOLVED", salida["state"])
            t.igual("E-07 %s con %s dice que llego otra" % (nombre, otra),
                    "SIGNAL_IDENTITY_MISMATCH", salida["reason"])
            t.igual("E-07 %s con %s sigue pidiendo la suya" % (nombre, otra), [SENAL],
                    salida["missingSignals"])
            t.verdadero("E-07 %s con %s no aprueba" % (nombre, otra), not modulo.aprueba(salida))

    # Y el mapa `{id: resuelta}` que viaja en la resolucion de la unidad tambien se lee bien:
    # con la senal de D7 adentro, resuelve; sin ella, no.
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    for nombre, modulo in MODULOS:
        t.igual("E-07 %s lee el mapa de la unidad" % nombre, "TRUE",
                modulo.evaluar(_caso(), bloque["signals"])["signalValue"])
        ajeno = c_normativa.resolucion({otras[0]: _senal("TRUE", sid=otras[0])})
        t.igual("E-07 %s con un mapa sin su senal no resuelve" % nombre,
                "APPLICABILITY_UNRESOLVED",
                modulo.evaluar(_caso(), ajeno["signals"])["state"])


# -- E-08 a E-12 — las tres obligaciones y los seis ids ------------------------

def test_e08_tres_policies(t):
    """E-08 (D7-06) — exactamente tres, ni una mas."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    de_d7 = [p for p in bloque["declaredPolicies"] if p in POLICIES]
    t.igual("E-08 son tres", 3, len(de_d7))
    t.igual("E-08 y son estas", sorted(POLICIES), sorted(de_d7))
    t.igual("E-08 la fila declara tres", 3, len(c_matriz.regla("D7")["policies"]))


def test_e09_tres_checks(t):
    """E-09 (D7-07) — exactamente tres, ni una mas."""
    bloque = c_normativa.resolucion({SENAL: _senal("TRUE")})
    de_d7 = [c for c in bloque["declaredChecks"] if c in CHEQUEOS]
    t.igual("E-09 son tres", 3, len(de_d7))
    t.igual("E-09 y son estos", sorted(CHEQUEOS), sorted(de_d7))
    t.igual("E-09 la fila declara tres", 3, len(c_matriz.regla("D7")["checks"]))


def test_e10_los_ids_son_los_de_la_matriz(t):
    """E-10 (D7-08) — el registro y la matriz dicen los mismos seis ids, sin renombrar ninguno."""
    filas = c_controles.de_la_regla("D7")
    t.igual("E-10 seis filas en el registro", 6, len(filas))
    por_tipo = {}
    for f in filas:
        por_tipo.setdefault(f["type"], []).append(f["id"])
        t.igual("E-10 %s sale de D7" % f["id"], "D7", f["rule"])
        t.igual("E-10 %s conserva la tupla" % f["id"], TRAZA, f["source"])
        t.igual("E-10 %s esta INSTALLED" % f["id"], "INSTALLED", f["status"])
    t.igual("E-10 las tres policies", sorted(POLICIES), sorted(por_tipo.get("POLICY", [])))
    t.igual("E-10 los tres checks", sorted(CHEQUEOS), sorted(por_tipo.get("CHECK", [])))
    t.igual("E-10 D7 no declara reviews", [], por_tipo.get("REVIEW", []))

    d7 = c_matriz.regla("D7")
    t.igual("E-10 la matriz declara las mismas policies", sorted(POLICIES), sorted(d7["policies"]))
    t.igual("E-10 y los mismos checks", sorted(CHEQUEOS), sorted(d7["checks"]))
    for nombre, modulo in MODULOS:
        t.igual("E-10 el modulo %s se llama igual que su id" % nombre, nombre, modulo.CONTROL)
        t.igual("E-10 %s es un CHECK" % nombre, "CHECK", modulo.TIPO)
        t.igual("E-10 %s sale de D7" % nombre, "D7", modulo.REGLA)


def test_e11_d7_no_crea_ninguna_skill(t):
    """E-11 (D7-09) — ni la fila, ni los siete archivos, ni el conteo de instaladas."""
    d7 = c_matriz.regla("D7")
    t.verdadero("E-11 la fila no declara skills", not d7.get("skills"))
    t.verdadero("E-11 ni la clave existe", "skills" not in d7)

    instaladas = {d.name for d in SKILLS.iterdir() if d.is_dir()}
    t.igual("E-11 siguen siendo 27 las skills instaladas", 27, len(instaladas))

    registro = c_reg.cargar(RUTA_REG)
    agentes = {a["id"] for a in registro["agents"]}
    declaradas = {s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    for nombre, texto in _artefactos_de_d7().items():
        # 🔴 Lo que no puede haber es una DECLARACION de skills —un inventario—. Nombrar una
        # skill instalada para rutear no es declararla, y por eso la mitad de abajo existe: cada
        # `dev-*` que un artefacto nombra tiene que estar ya en el registro.
        t.vacio("E-11 %s no declara un inventario de skills" % nombre,
                re.findall(r"(?i)\bskills\s*[:=]\s*[\"'\[]", texto))
        for mencionada in sorted(set(re.findall(r"\bdev-[a-z-]+\b", texto))):
            t.verdadero("E-11 %s nombra %s, que el registro ya declara" % (nombre, mencionada),
                        mencionada in declaradas or mencionada in agentes)


def test_e12_las_tres_obligaciones_son_independientes(t):
    """E-12 (§2, D7-29) — los seis cruces: romper una no mueve a las otras dos."""
    base = _estados(_mixto(), _senal())
    t.igual("E-12 la base: los tres pasan",
            {c: "PASS" for c in CHEQUEOS}, base)

    roturas = {
        CHEQUEOS[0]: _mixto(persistente=_persistente(mecanismo="otro-repositorio")),
        CHEQUEOS[1]: _mixto(temporal=_temporal(local={"persistenceBehavior": "PERSISTENT"})),
        CHEQUEOS[2]: _mixto(temporal=_temporal(caminos=_caminos(("PERIODIC",)))),
    }
    for roto, caso in roturas.items():
        estados = _estados(caso, _senal())
        t.igual("E-12 roto %s falla" % roto, "FAIL", estados[roto])
        for otro in CHEQUEOS:
            if otro == roto:
                continue
            t.igual("E-12 roto %s, %s no se mueve" % (roto, otro), base[otro], estados[otro])

    # 🔴 Y la unica coincidencia que SI es real: una escritura local permanente incumple dos
    # obligaciones distintas, y las dos lo dicen. No es herencia de estado: es una escritura que
    # persiste fuera del estandar Y usa el local como repositorio.
    dos = _estados(_caso(flujos=[_local()]), _senal())
    t.igual("E-12 el local permanente falla el storage", "FAIL", dos[CHEQUEOS[0]])
    t.igual("E-12 y falla la prohibicion", "FAIL", dos[CHEQUEOS[1]])
    t.igual("E-12 y no arrastra a la limpieza", "NOT_APPLICABLE", dos[CHEQUEOS[2]])


# -- E-13 a E-19 — el storage estandar, que no se inventa ----------------------

def test_e13_un_flujo_con_evidencia_pasa(t):
    """E-13 (D7-10) — identidad, contrato y traza del camino de persistencia dan PASS."""
    salida = SB.evaluar(_caso(), _senal())
    t.igual("E-13 el estado", "PASS", salida["state"])
    t.verdadero("E-13 aprueba", SB.aprueba(salida))
    t.igual("E-13 el flujo se evaluo", ["f-adjuntos"], [f["flowId"] for f in salida["flows"]])
    t.igual("E-13 y paso", "PASS", salida["flows"][0]["state"])
    t.igual("E-13 la identidad informada es la normalizada", ALMACEN["id"],
            salida["standardStorage"]["id"])
    t.igual("E-13 el protocolo que informa es el que el estandar nombra", "S3",
            salida["standardStorage"]["protocol"])
    t.vacio("E-13 sin avisos", salida["issues"])

    # Y con blancos alrededor de cada identificador, el mismo resultado.
    con_blancos = _caso(flujos=[_persistente(mecanismo="  %s  " % ALMACEN["id"])],
                        standardStorage=dict(ALMACEN, id="  %s " % ALMACEN["id"]),
                        evidencia=[_ev("e-persistencia", FLUJOS.TRAZA_DE_PERSISTENCIA,
                                       mechanism=" %s " % ALMACEN["id"])])
    t.igual("E-13 los blancos no cambian nada", "PASS",
            SB.evaluar(con_blancos, _senal())["state"])


def test_e14_lo_inerte_no_pasa(t):
    """E-14 (D7-11) — las seis clases que no prueban nada, una por una."""
    inertes = ("REPOSITORY_DEPENDENCY", "ENVIRONMENT_VARIABLE_NAME", "BUCKET_CONFIGURATION",
               "REMOTE_HTTP_CALL", "UPLOAD_SUCCEEDED", "AGENT_STATEMENT")
    for tipo in inertes:
        caso = _caso(evidencia=[_ev("e-persistencia", tipo, mechanism=ALMACEN["id"])])
        salida = SB.evaluar(caso, _senal())
        t.igual("E-14 %s no pasa" % tipo, "PARTIAL", salida["state"])
        t.igual("E-14 %s deja el motivo" % tipo, "PERSISTENCE_TRACE_MISSING", salida["reason"])
        t.verdadero("E-14 %s no aprueba" % tipo, not SB.aprueba(salida))
        t.verdadero("E-14 %s esta declarada inerte" % tipo,
                    tipo in FLUJOS.EVIDENCIA_QUE_NO_PRUEBA)
    t.igual("E-14 son doce las clases inertes declaradas", 12,
            len(FLUJOS.EVIDENCIA_QUE_NO_PRUEBA))


def test_e15_otro_repositorio_remoto_no_satisface(t):
    """E-15 (D7-12) — un almacen remoto generico no es el estandar en silencio."""
    caso = _caso(flujos=[_persistente(clase=FLUJOS.OTRO_REMOTO)])
    salida = SB.evaluar(caso, _senal())
    t.igual("E-15 el estado", "FAIL", salida["state"])
    t.igual("E-15 el motivo", "PERSISTENT_PATH_NOT_STANDARD_STORAGE", salida["reason"])
    t.verdadero("E-15 no aprueba", not SB.aprueba(salida))


def test_e16_sin_identidad_no_se_inventa(t):
    """E-16 (D7-13) — sin id, sin fuente de la lista, sin referencia o en blancos."""
    for nombre, almacen in (
            ("sin nada", {}),
            ("sin id", {"source": "GCBA_NORMATIVE", "reference": "r"}),
            ("sin fuente", {"id": "x", "reference": "r"}),
            ("con una fuente que no esta en la lista",
             {"id": "x", "source": "PROJECT_CONVENTION", "reference": "r"}),
            ("sin referencia", {"id": "x", "source": "GCBA_NORMATIVE"}),
            ("todo en blancos", {"id": "   ", "source": "GCBA_NORMATIVE", "reference": "  "}),
            ("solo el protocolo", {"protocol": "S3"})):
        salida = SB.evaluar(_caso(standardStorage=almacen), _senal())
        t.igual("E-16 %s queda sin proveedor" % nombre,
                "STANDARD_STORAGE_PROVIDER_UNRESOLVED", salida["state"])
        t.verdadero("E-16 %s no aprueba" % nombre, not SB.aprueba(salida))

    for fuente in FLUJOS.FUENTES_DE_IDENTIDAD:
        ok, _ = SB.proveedor_valido({"standardStorage": {"id": "x", "source": fuente,
                                                         "reference": "r"}})
        t.verdadero("E-16 %s sirve como origen" % fuente, ok)


def test_e17_sin_contrato_es_otro_hueco(t):
    """E-17 (D7-14) — con identidad y sin contrato, y son dos estados distintos."""
    salida = SB.evaluar(_caso(integrationContract={}), _senal())
    t.igual("E-17 el estado", "STORAGE_INTEGRATION_CONTRACT_MISSING", salida["state"])
    t.verdadero("E-17 la identidad si se resolvio", salida["standardStorage"]["id"])
    t.verdadero("E-17 no aprueba", not SB.aprueba(salida))
    t.verdadero("E-17 los dos huecos son estados distintos",
                SB.SIN_PROVEEDOR != SB.SIN_CONTRATO)
    for nombre, contrato in (("sin fuente", {"id": "x", "reference": "r"}),
                             ("sin referencia", {"id": "x", "source": "GCBA_NORMATIVE"}),
                             ("en blancos", {"id": " ", "source": "GCBA_NORMATIVE",
                                             "reference": " "})):
        t.igual("E-17 %s falta el contrato" % nombre, "STORAGE_INTEGRATION_CONTRACT_MISSING",
                SB.evaluar(_caso(integrationContract=contrato), _senal())["state"])


def test_e18_el_cliente_existe_y_el_camino_lo_esquiva(t):
    """E-18 (§7) — lo diga el flujo o lo diga solo su traza, es FAIL."""
    por_el_flujo = _caso(flujos=[_persistente(mecanismo="otro-repositorio")])
    salida = SB.evaluar(por_el_flujo, _senal())
    t.igual("E-18 el flujo declara otro mecanismo", "FAIL", salida["state"])
    t.igual("E-18 con el motivo", "ALTERNATE_STORAGE_MECHANISM", salida["reason"])

    # El flujo dice lo correcto y la corrida dice otra cosa: la corrida manda.
    por_la_traza = _caso(evidencia=[_ev("e-persistencia", FLUJOS.TRAZA_DE_PERSISTENCIA,
                                        mechanism="otro-repositorio")])
    salida = SB.evaluar(por_la_traza, _senal())
    t.igual("E-18 la traza manda sobre lo declarado", "FAIL", salida["state"])
    t.igual("E-18 y deja el motivo", "ALTERNATE_STORAGE_MECHANISM", salida["reason"])

    # Una traza muda no prueba nada, y un flujo que no dice por donde persiste tampoco.
    muda = _caso(evidencia=[_ev("e-persistencia", FLUJOS.TRAZA_DE_PERSISTENCIA)])
    t.igual("E-18 una traza que no dice por donde", "PARTIAL",
            SB.evaluar(muda, _senal())["state"])
    t.igual("E-18 y el motivo", "TRACE_MECHANISM_UNDECLARED",
            SB.evaluar(muda, _senal())["reason"])
    callado = _caso(flujos=[_persistente(mecanismo="")])
    t.igual("E-18 un flujo que no dice por donde", "PARTIAL",
            SB.evaluar(callado, _senal())["state"])
    t.igual("E-18 y su motivo", "STORAGE_MECHANISM_UNDECLARED",
            SB.evaluar(callado, _senal())["reason"])


# 🔴 El invariante de D7: un artefacto de la regla no lleva el mecanismo del storage estandar ni
# una duracion. Lo que se busca es ESTRUCTURAL —un localizador de red, un nombre de
# infraestructura con su valor, una credencial, un especificador de paquete, una declaracion de
# mecanismo, un numero con unidad de tiempo—. El barrido de nombres de proveedor es la segunda
# red, y las dos se prueban con fugas crudas.
#
# Las dos excepciones son citas del estandar y estan afuera del barrido a proposito: el protocolo
# `S3`, y los dos numeros de §8.4 —20 niveles y 100.000 objetos—.
PROHIBIDOS = (
    # localizadores de red: con esquema, sin esquema, con puerto —con o sin punto— o una IP.
    r"(?i)https?://",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*\.(ar|com|net|org|gov|gob|io|dev|app|cloud|bue|"
    r"tech|local)\b",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*:\d{2,5}\b",
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    # nombres de infraestructura con su valor. El separador es parte del patron: la policy dice
    # "no invents a bucket" y eso es prosa, no una declaracion.
    r"(?i)\b(bucket|container|contenedor|region|regi[oó]n|tenant|namespace|prefix|prefijo|"
    r"retention|retenci[oó]n|arn|host|hostname)\b[\"']?\s*[:=]",
    # credenciales. El numero es parte del patron del token a proposito: `token con un numero`
    # es prosa y `Token 8f3a2b9c` es una credencial.
    r"(?i)\b(bearer|token)\s+[A-Za-z0-9._-]*\d[A-Za-z0-9._-]*",
    r"(?i)\b(access[_-]?key|secret[_-]?key|api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"session[_-]?token|credentials?[_-]?file)\b",
    # declaraciones del mecanismo, tambien con separador.
    r"(?i)\b(endpoint|sdk|client|cliente|adapter|adaptador|driver|connection[_-]?string|"
    r"storage[_-]?class)\b[\"']?\s*[:=]",
    # paquetes: por el gestor, por el scope, o por como se importa.
    r"(?i)\b(npm|pnpm|yarn|pip|composer|nuget|gem|go)\s+(i|install|add|require|get)\b",
    r"@[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*",
    r"(?i)\b(import|require)\b[^\n]{0,40}[\"'][a-z0-9@][a-z0-9@/._-]*"
    r"(s3|storage|blob|bucket|boto)[\"']",
    # Y la forma sin comillas, que es como se importa en la mitad de los lenguajes.
    r"(?i)\bfrom\s+[a-z0-9_.]*(s3|storage|blob|bucket|boto)[a-z0-9_.]*\s+import\b",
    # duraciones: un numero con unidad de tiempo, o un TTL con valor. Es lo que "inmediata" no
    # tiene que tener nunca.
    r"(?i)\b\d+(\.\d+)?\s*(ms|s|seg|segs|segundos?|seconds?|min|mins|minutos?|minutes?|h|hs|"
    r"horas?|hours?|d[ií]as?|days?|semanas?|weeks?)\b",
    r"(?i)\bttl\b[\"']?\s*[:=]\s*\d",
)

# Proveedores y productos de almacenamiento. Aca no se nombra ninguno: una lista de prohibidos
# envejece, corre el eje de la regla —que no es *no uses estos* sino *usa el del GCBA*— y deja al
# invariante sin poder distinguir un contraejemplo de una invencion.
#
# 🔴 Los distintivos se buscan sobre el texto SIN separadores, asi `Amazon S3`, `amazon-s3` y
# `amazons3` son lo mismo: partir un nombre en dos es una de las formas que escapan.
PEGADOS = ("amazons3", "awss3", "amazonwebservices", "googlecloudstorage", "azureblob",
           "blobstorage", "hitachicontentplatform", "digitaloceanspaces", "cloudfiles")
# Los cortos o ambiguos van con borde de palabra y sin normalizar.
SUELTOS = ("aws", "amazon", "azure", "gcp", "minio", "ceph", "hcp", "hitachi", "boto3", "s3fs",
           "wasabi", "backblaze", "cloudian", "scality")


def _seccion_de_d7_del_doc():
    """La seccion que D7 agrego a `docs/normativa-7.1.md`.

    Se barre esa y no el archivo entero: el documento cubre las 24 reglas, y el dia que D8 cite
    un mecanismo de token el barrido de D7 no tiene por que ponerse en rojo. Que el titulo exista
    se afirma aparte, asi que renombrarlo no achica el sujeto en silencio.
    """
    texto = (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8")
    titulo = "## Tres obligaciones en una oración: D7"
    if titulo not in texto:
        return titulo, ""
    return titulo, texto.split(titulo, 1)[1].split("\n## ", 1)[0]


def _artefactos_de_d7():
    """Los diez textos que la tabla `Qué se construye` de la spec declara como artefactos."""
    textos = {}
    for pid in POLICIES:
        textos["la policy %s" % pid] = (CONTROLES / "policies" / (pid + ".md")).read_text(
            encoding="utf-8")
    for cid in CHEQUEOS:
        textos["el check %s" % cid] = (CONTROLES / "checks" / (cid + ".py")).read_text(
            encoding="utf-8")
    textos["el modulo compartido"] = (CONTROLES / "lib" / "flujos.py").read_text(
        encoding="utf-8")
    textos["el registro"] = repr(c_controles.de_la_regla("D7"))
    textos["la fila de la matriz"] = repr(c_matriz.regla("D7"))
    textos["la doc"] = _seccion_de_d7_del_doc()[1]
    return textos


def _fugas_en(texto):
    sin_separadores = re.sub(r"[\s_\-]+", "", texto).lower()
    hallados = [p for p in PROHIBIDOS if re.search(p, texto)]
    hallados += [v for v in PEGADOS if v in sin_separadores]
    hallados += [v for v in SUELTOS
                 if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(v), texto.lower())]
    return sorted(set(hallados))


def test_e19_ningun_artefacto_lleva_el_mecanismo(t):
    """E-19 (§3, D7-30, D7-32) — el invariante sobre los diez artefactos, y sus tres mitades."""
    titulo, seccion = _seccion_de_d7_del_doc()
    t.verdadero("E-19 la seccion de D7 esta en la doc", bool(seccion))
    t.verdadero("E-19 y tiene contenido", len(seccion) > 2000)

    artefactos = _artefactos_de_d7()
    t.igual("E-19 son diez textos los que se barren", 10, len(artefactos))
    for nombre, texto in sorted(artefactos.items()):
        t.igual("E-19 %s no lleva el mecanismo" % nombre, [], _fugas_en(texto))

    # Y el resultado que cada check produce, en todos sus caminos: es lo que viaja a un plan.
    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        for estado, (caso, senal) in caminos().items():
            t.igual("E-19 ni el resultado de %s en %s" % (nombre, estado), [],
                    _fugas_en(repr(modulo.evaluar(caso, senal))))

    # 🔴 La segunda mitad. Las formas son CRUDAS: ninguna se escribio para que el patron la
    # agarre; son las que alguien escribiria de verdad.
    FUGAS = (
        'endpoint: https://storage.example/v1',
        'ENDPOINT = "HTTPS://STORAGE.GCBA.GOB.AR"',
        'bucket: tramites-adjuntos',
        'BUCKET = "adjuntos-prod"',
        'region: us-east-1',
        'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',
        'secret_key: 8f3a2b9c',
        'access_token = "abc123"',
        'Authorization: Bearer 8f3a2b9c',
        "Authorization: Token 8f3a2b9c",
        'sdk: storage-gcba-js',
        'client = "gcba-storage-client"',
        'cliente: el cliente institucional',
        'adapter: local-disk',
        'connection_string: acct=adjuntos',
        "pip install boto3",
        "npm install @gcba/storage-sdk",
        'import boto3',
        'require("aws-s3")',
        'from storage import cliente',
        "storage.gcba.gob.ar",
        "almacen-interno:9000",
        "10.20.30.40/storage",
        "adjuntos.gcba.bue",
        "storage.gcba.tech",
        # Duraciones, que es lo que "inmediata" no puede tener.
        "la limpieza corre a los 5 segundos",
        "se borra en 30 s",
        "TTL = 3600",
        "ttl: 86400",
        "retencion de 7 dias",
        "se destruye antes de 1 minuto",
        "el temporal vive 2 horas",
        "cleanup after 500 ms",
        "expires in 24 hours",
        # Proveedores y productos, juntos, partidos y pegados.
        "se resguarda en Amazon S3",
        '"amazon-s3"',
        "el storage de AWS",
        "usar MinIO como alternativa",
        "Azure Blob Storage no alcanza",
        "Google Cloud Storage tampoco",
        "el repositorio es un Hitachi Content Platform",
        "el HCP del organismo",
        "se usa Ceph en el datacenter",
        "boto3 es la libreria",
        # Infraestructura declarada en la forma citada, que es como entraria en un json.
        '{"bucket": "adjuntos"}',
        '"region": "sa-east-1"',
        '{"tenant": "gcba"}',
        '"prefix": "tramites/2026"',
        '{"retention": "90"}',
    )
    t.igual("E-19 son cuarenta y nueve formas de fuga", 49, len(FUGAS))
    for fuga in FUGAS:
        t.verdadero("E-19 se detecta: %s" % fuga[:40], bool(_fugas_en(fuga)))

    # La premisa que hace valer la mitad de arriba: el texto real, con una fuga adentro, deja de
    # estar limpio.
    base = artefactos["la policy gcba-standard-storage-required"]
    t.igual("E-19 la premisa: la policy esta limpia", [], _fugas_en(base))
    t.verdadero("E-19 y con una fuga adentro deja de estarlo",
                bool(_fugas_en(base + '\nendpoint: https://storage.example/v1\n')))
    t.verdadero("E-19 y la doc tambien",
                bool(_fugas_en(artefactos["la doc"] + "\nEl temporal se borra a los 30 s.\n")))

    # 🔴 La tercera mitad: lo que NO es una fuga. Un barrido que se pone en rojo con texto
    # correcto es un barrido que alguien apaga la primera vez que lo ve fallar sin motivo. Las
    # dos primeras son las citas del estandar, y son las que importan.
    LIMPIOS = (
        "la tecnologia actual esta basada en el protocolo S3 (Simple Storage Service)",
        "no crear estructuras de carpetas que tengan mas de 20 niveles de profundidad",
        "evitar colocar una gran cantidad de objetos (mas de 100.000) en una sola carpeta",
        "ES0901 6.3, seccion 7.1, regla D7, pagina 13",
        "el apartado de apoyo es 8.4 Sistema de Archivos, pag. 19",
        "hablar el protocolo no identifica un repositorio, como hablar HTTP no identifica un sitio",
        "no se declara ningun endpoint, ningun bucket y ninguna credencial",
        "la identidad entra como dato declarado con su fuente citada",
        "un adaptador de disco local configurado como repositorio permanente",
        "una dependencia de almacenamiento de objetos declarada en el manifiesto",
        "el nombre de una variable de ambiente no prueba por donde paso el archivo",
        "STANDARD_STORAGE_PROVIDER_UNRESOLVED / STORAGE_INTEGRATION_CONTRACT_MISSING",
        "BUCKET_CONFIGURATION y ENVIRONMENT_VARIABLE_NAME son clases inertes",
        "tmp en un path no prueba un ciclo de vida temporal",
        "finally, defer, using, un context manager o una primitiva con borrado determinista",
        "la destruccion se ata al fin del proposito y no a un numero de segundos",
        "27 skills instaladas y 31 controles declarados",
        "controles/checks/storage-backend-compliance.py y controles/lib/flujos.py",
        "docs/normativa-7.1.md, es0901-7.1.json y la matriz",
        "PERSISTENT_STANDARD_STORAGE PERSISTENT_LOCAL TEMPORARY_LOCAL OTHER_REMOTE_STORAGE",
        "los siete datos: pathOrAdapter, purpose, creation, consumption y cleanup",
        "un cron diario, el arranque, el reinicio del contenedor o un TTL sin especificar",
    )
    for limpio in LIMPIOS:
        t.igual("E-19 no dispara con: %s" % limpio[:38], [], _fugas_en(limpio))

    # Y la cita del protocolo tiene que ESTAR: es lo que el estandar dice, y borrarla para pasar
    # el barrido seria perder la unica evidencia de tecnologia que la regla tiene.
    for nombre in ("la policy gcba-standard-storage-required", "el modulo compartido",
                   "el check storage-backend-compliance", "la doc"):
        t.verdadero("E-19 %s cita el protocolo" % nombre, "S3" in artefactos[nombre])


# -- E-20 a E-24 — el local permanente -----------------------------------------

def test_e20_el_local_permanente_falla(t):
    """E-20 (D7-15) — almacenamiento local permanente de archivos de la aplicacion."""
    salida = PL.evaluar(_caso(flujos=[_local()]), _senal())
    t.igual("E-20 el estado", "FAIL", salida["state"])
    t.igual("E-20 el motivo", "PERSISTENT_LOCAL_STORAGE", salida["reason"])
    t.verdadero("E-20 no aprueba", not PL.aprueba(salida))
    t.igual("E-20 el flujo se nombra", ["f-permanente"], salida["localFlows"])

    # Y tambien cuando la clase no lo dice y el comportamiento declarado si.
    por_comportamiento = _caso(flujos=[_temporal(local={"persistenceBehavior": "PERSISTENT"})])
    salida = PL.evaluar(por_comportamiento, _senal())
    t.igual("E-20 el comportamiento declarado alcanza", "FAIL", salida["state"])
    t.verdadero("E-20 y la contradiccion queda anotada",
                any("LOCAL_CLASSIFICATION_CONTRADICTED" in i for i in salida["issues"]))


def test_e21_el_nombre_del_path_no_clasifica(t):
    """E-21 (D7-16) — `tmp` con ciclo de vida desconocido, y la evidencia inerte."""
    sin_vida = _caso(flujos=[_temporal(local={"pathOrAdapter": "/tmp/adjuntos",
                                              "expectedLifetime": ""})])
    salida = PL.evaluar(sin_vida, _senal())
    t.igual("E-21 el estado", "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED", salida["state"])
    t.verdadero("E-21 no aprueba", not PL.aprueba(salida))
    t.verdadero("E-21 dice que campo falta",
                "expectedLifetime" in salida["flows"][0]["missingFields"])

    # Los siete campos escritos y la unica evidencia es como se llama el path: no se resuelve.
    for tipo in ("PATH_NAMING", "CONTAINER_ASSUMPTION", "AGENT_STATEMENT"):
        caso = _caso(flujos=[_temporal(local={"pathOrAdapter": "/tmp/adjuntos"})],
                     evidencia=[_ev("e-local", tipo)])
        salida = PL.evaluar(caso, _senal())
        t.igual("E-21 %s no sostiene el ciclo de vida" % tipo,
                "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED", salida["state"])
        t.igual("E-21 %s deja el motivo" % tipo, "LOCAL_LIFECYCLE_EVIDENCE_MISSING",
                salida["reason"])
        t.verdadero("E-21 %s esta declarada inerte" % tipo,
                    tipo in FLUJOS.EVIDENCIA_QUE_NO_PRUEBA)


def test_e22_un_temporal_no_es_persistente_por_ser_local(t):
    """E-22 (D7-17) — la prohibicion no lo toca, y la limpieza si lo evalua."""
    caso = _caso(flujos=[_temporal()])
    salida = PL.evaluar(caso, _senal())
    t.igual("E-22 la prohibicion no lo hace fallar", "PASS", salida["state"])
    t.igual("E-22 y lo deriva", "temporary-file-cleanup", salida["flows"][0]["deferredTo"])
    t.igual("E-22 el check que lo evalua es el otro", "PASS",
            TC.evaluar(caso, _senal())["state"])
    t.igual("E-22 y lo tiene en su lista", ["f-temporal"],
            TC.evaluar(caso, _senal())["temporaryFlows"])


def test_e23_un_volumen_montado_no_esquiva_la_prohibicion(t):
    """E-23 (D7-18) — el rol que cumple el almacenamiento, no como se monto."""
    for path in ("un volumen montado en la aplicacion", "un directorio del server",
                 "el adaptador de disco del framework", "el filesystem del contenedor"):
        caso = _caso(flujos=[_local(pathOrAdapter=path)])
        salida = PL.evaluar(caso, _senal())
        t.igual("E-23 %s falla igual" % path[:30], "FAIL", salida["state"])
        t.igual("E-23 %s con el mismo motivo" % path[:30], "PERSISTENT_LOCAL_STORAGE",
                salida["reason"])


def test_e24_los_siete_datos_del_ciclo_de_vida(t):
    """E-24 (§8) — falta uno de los siete y no se resuelve; y la mitad sabida es PARTIAL."""
    t.igual("E-24 son siete campos", 7, len(FLUJOS.CAMPOS_LOCALES))
    for campo in FLUJOS.CAMPOS_LOCALES:
        caso = _caso(flujos=[_temporal(local={campo: ""})])
        salida = PL.evaluar(caso, _senal())
        t.igual("E-24 sin %s no se resuelve" % campo, "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED",
                salida["state"])
        t.verdadero("E-24 y lo nombra: %s" % campo,
                    campo in salida["flows"][0]["missingFields"])
        t.verdadero("E-24 sin %s no aprueba" % campo, not PL.aprueba(salida))

    # Ninguna establecida es no saber nada; una si y otra no es saber la mitad.
    ninguna = PL.evaluar(_caso(flujos=[_sin_ciclo()]), _senal())
    t.igual("E-24 ninguna establecida", "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED", ninguna["state"])
    mitad = PL.evaluar(_caso(flujos=[_temporal(), _sin_ciclo()]), _senal())
    t.igual("E-24 la mitad establecida", "PARTIAL", mitad["state"])
    t.igual("E-24 con el motivo del hueco", "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED",
            mitad["reason"])
    t.verdadero("E-24 y ninguno de los dos aprueba",
                not PL.aprueba(ninguna) and not PL.aprueba(mitad))


# -- E-25 a E-31 — la destruccion inmediata ------------------------------------

def test_e25_un_temporal_con_limpieza_atada_se_evalua(t):
    """E-25 (D7-19) — el flujo no desaparece: entra, se evalua y su camino normal pasa."""
    caso = _caso(flujos=[_temporal(caminos=_caminos(nombres=(FLUJOS.CAMINO_NORMAL,)))])
    salida = TC.evaluar(caso, _senal())
    t.igual("E-25 el flujo esta en la lista", ["f-temporal"], salida["temporaryFlows"])
    t.igual("E-25 y se evaluo", 1, len(salida["flows"]))
    t.igual("E-25 el camino normal se evaluo", [FLUJOS.CAMINO_NORMAL],
            [c["path"] for c in salida["flows"][0]["paths"]])
    t.igual("E-25 y paso", "PASS", salida["flows"][0]["paths"][0]["state"])
    t.igual("E-25 el proposito acotado queda declarado", "convertir un reporte a pdf",
            salida["flows"][0]["boundedPurpose"])


def test_e26_la_limpieza_del_camino_feliz_no_alcanza(t):
    """E-26 (D7-20) — con los caminos de falla sin declarar, no llega a PASS."""
    caso = _caso(flujos=[_temporal(caminos=_caminos(nombres=(FLUJOS.CAMINO_NORMAL,)))])
    salida = TC.evaluar(caso, _senal())
    t.igual("E-26 el estado", "CLEANUP_PATH_COVERAGE_UNRESOLVED", salida["state"])
    t.igual("E-26 el motivo", "CLEANUP_PATH_UNDECLARED", salida["reason"])
    t.verdadero("E-26 no aprueba", not TC.aprueba(salida))
    t.igual("E-26 dice que caminos faltan", ["VALIDATION_FAILURE", "PROVIDER_FAILURE"],
            salida["flows"][0]["missingPaths"])

    # Y el cuarto camino se exige solo cuando el proyecto declara que el runtime deja limpiar.
    cancelable = _caso(flujos=[_temporal(temporal={"runtimeCleanupPossible": True})])
    salida = TC.evaluar(cancelable, _senal())
    t.igual("E-26 con cancelacion posible se exige el cuarto",
            "CLEANUP_PATH_COVERAGE_UNRESOLVED", salida["state"])
    t.igual("E-26 y es el que falta", [FLUJOS.CAMINO_CANCELACION],
            salida["flows"][0]["missingPaths"])


def test_e27_el_cron_solo_no_pasa(t):
    """E-27 (D7-21) — una limpieza periodica no es la destruccion al terminar el proposito."""
    caso = _caso(flujos=[_temporal(caminos=_caminos(("PERIODIC",)))])
    salida = TC.evaluar(caso, _senal())
    t.igual("E-27 el estado", "FAIL", salida["state"])
    t.igual("E-27 el motivo", "DELAYED_CLEANUP_NOT_IMMEDIATE", salida["reason"])
    t.verdadero("E-27 no aprueba", not TC.aprueba(salida))
    t.verdadero("E-27 y la clase de evidencia tambien es inerte",
                "PERIODIC_CLEANUP_JOB" in FLUJOS.EVIDENCIA_QUE_NO_PRUEBA)


def test_e28_el_reinicio_solo_no_pasa(t):
    """E-28 (D7-22) — confiar en que el contenedor se reemplace no es limpiar."""
    caso = _caso(flujos=[_temporal(caminos=_caminos(("RESTART",)))])
    salida = TC.evaluar(caso, _senal())
    t.igual("E-28 el estado", "FAIL", salida["state"])
    t.igual("E-28 el motivo", "DELAYED_CLEANUP_NOT_IMMEDIATE", salida["reason"])
    t.verdadero("E-28 la clase de evidencia es inerte",
                "RESTART_POLICY" in FLUJOS.EVIDENCIA_QUE_NO_PRUEBA)


def test_e29_el_ttl_el_arranque_y_lo_manual_no_pasan(t):
    """E-29 (D7-23) — las tres demoras restantes, y las cinco declaradas."""
    t.igual("E-29 son cinco las demoradas", 5, len(FLUJOS.DEMORADAS))
    for mecanismo in FLUJOS.DEMORADAS:
        caso = _caso(flujos=[_temporal(caminos=_caminos((mecanismo,)))])
        salida = TC.evaluar(caso, _senal())
        t.igual("E-29 %s solo falla" % mecanismo, "FAIL", salida["state"])
        t.igual("E-29 %s con el motivo" % mecanismo, "DELAYED_CLEANUP_NOT_IMMEDIATE",
                salida["reason"])
    # Y nada tambien falla, con otro motivo: no limpiar no es limpiar tarde.
    nada = _caso(flujos=[_temporal(caminos=_caminos((FLUJOS.SIN_LIMPIEZA,)))])
    t.igual("E-29 no limpiar falla", "FAIL", TC.evaluar(nada, _senal())["state"])
    t.igual("E-29 con su propio motivo", "CLEANUP_MISSING",
            TC.evaluar(nada, _senal())["reason"])


def test_e30_la_cobertura_completa_pasa_y_la_tecnica_no_se_exige(t):
    """E-30 (D7-25, §9) — exito y falla con traza dan PASS; la tecnica no cambia nada."""
    salida = TC.evaluar(_caso(flujos=[_temporal()]), _senal())
    t.igual("E-30 el estado", "PASS", salida["state"])
    t.verdadero("E-30 aprueba", TC.aprueba(salida))
    t.igual("E-30 los tres caminos se evaluaron", 3, len(salida["flows"][0]["paths"]))
    t.vacio("E-30 y no falta ninguno", salida["flows"][0]["missingPaths"])

    # 🔴 Lo demorado AL LADO de la atadura es defensa en profundidad y no rompe nada.
    con_cron = _caso(flujos=[_temporal(
        caminos=_caminos((FLUJOS.CICLO_DE_VIDA, "PERIODIC")))])
    t.igual("E-30 el cron al lado no rompe", "PASS", TC.evaluar(con_cron, _senal())["state"])

    # Y la tecnica: seis formas y ninguna, con el mismo resultado.
    tecnicas = ("finally", "defer", "using/dispose", "context manager", "try/finally",
                "una primitiva de archivo temporal con borrado determinista", "")
    for tecnica in tecnicas:
        caso = _caso(flujos=[_temporal(temporal={"technique": tecnica})])
        salida = TC.evaluar(caso, _senal())
        t.igual("E-30 la tecnica `%s` no cambia el estado" % (tecnica or "sin declarar"),
                "PASS", salida["state"])
        t.igual("E-30 y se registra: `%s`" % (tecnica or "sin declarar"), tecnica,
                salida["flows"][0]["technique"])


def test_e31_inmediato_no_se_define_con_un_numero(t):
    """E-31 (D7-24) — ningun umbral, ni en el modulo ni en los artefactos."""
    numeros = sorted(n for n, v in vars(TC).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-31 el check de limpieza no declara ninguna constante numerica", [], numeros)
    numeros = sorted(n for n, v in vars(PL).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-31 ni el de la prohibicion", [], numeros)
    numeros = sorted(n for n, v in vars(FLUJOS).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-31 ni el modulo compartido", [], numeros)

    # 🔴 Los dos unicos numeros de D7 son las dos CITAS de §8.4, y viven en el check del storage.
    numeros = sorted(n for n, v in vars(SB).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-31 el de storage declara solo los dos numeros citados",
            ["LIMITE_DE_OBJETOS", "LIMITE_DE_PROFUNDIDAD"], numeros)
    t.igual("E-31 la profundidad que el estandar nombra", 20, SB.LIMITE_DE_PROFUNDIDAD)
    t.igual("E-31 y la concentracion de objetos", 100000, SB.LIMITE_DE_OBJETOS)

    # La unica forma de aprobar la limpieza es la atadura estructural, no una duracion.
    t.igual("E-31 el mecanismo que cumple", "LIFECYCLE_BOUND", FLUJOS.CICLO_DE_VIDA)
    for texto in _artefactos_de_d7().values():
        t.vacio("E-31 ningun artefacto declara una duracion",
                re.findall(r"(?i)\b\d+(?:\.\d+)?\s*(?:ms|seg|segundos?|seconds?|min|minutos?|"
                           r"minutes?|hs|horas?|hours?|d[ií]as?|days?)\b", texto))


# -- E-32 a E-37 — la cobertura de flujos --------------------------------------

def test_e32_el_inventario_incompleto_no_se_resuelve(t):
    """E-32 (D7-26) — las seis formas de incompleto, en los tres checks."""
    formas = {
        "sin inventario": _caso(fileFlows={}),
        "sin flujos": _caso(flujos=[]),
        "sin fuente del inventario": _caso(fuente="PROJECT_CONVENTION"),
        "con un flujo sin id": _caso(flujos=[_persistente(fid="  ")]),
        "con un flujo sin clasificacion":
            _caso(flujos=[dict(_persistente(), classification="OTRA_COSA")]),
        "con un flujo sin resolver":
            _caso(flujos=[dict(_persistente(), classification=FLUJOS.CLASE_SIN_RESOLVER)]),
        "declarado incompleto": _caso(flujos=[_temporal()], completo=False),
    }
    t.igual("E-32 son siete formas de inventario incompleto", 7, len(formas))
    for nombre, caso in formas.items():
        for check, estado in _estados(caso, _senal()).items():
            t.igual("E-32 %s deja %s sin cobertura" % (nombre, check),
                    "FILE_FLOW_COVERAGE_UNRESOLVED", estado)

    # Y un persistente que cumple al lado de uno sin clasificar tampoco pasa.
    mezcla = _caso(flujos=[_persistente(),
                           dict(_persistente(fid="f-?"),
                                classification=FLUJOS.CLASE_SIN_RESOLVER)])
    t.igual("E-32 un flujo sin clasificar no lo tapa el que cumple",
            "FILE_FLOW_COVERAGE_UNRESOLVED", SB.evaluar(mezcla, _senal())["state"])


def test_e33_sin_temporales_la_limpieza_no_aplica(t):
    """E-33 (D7-27) — sobre una clasificacion completa, NOT_APPLICABLE."""
    salida = TC.evaluar(_caso(), _senal())
    t.igual("E-33 el estado", "NOT_APPLICABLE", salida["state"])
    t.igual("E-33 el motivo", "NO_TEMPORARY_FILE_FLOW", salida["reason"])
    t.vacio("E-33 no hay flujos temporales", salida["temporaryFlows"])
    t.verdadero("E-33 y no aprueba", not TC.aprueba(salida))
    # Sobre una clasificacion INCOMPLETA, no: eso seria convertir un hueco en una ausencia.
    t.igual("E-33 sin clasificacion completa no se declara ausencia",
            "FILE_FLOW_COVERAGE_UNRESOLVED", TC.evaluar(_caso(completo=False), _senal())["state"])


def test_e34_un_temporal_solo_no_falla_el_storage(t):
    """E-34 (D7-28) — no falla por no persistir, y no se le pide la identidad."""
    caso = _caso(flujos=[_temporal()])
    salida = SB.evaluar(caso, _senal())
    t.igual("E-34 el estado", "NOT_APPLICABLE", salida["state"])
    t.igual("E-34 el motivo", "NO_PERSISTENT_FILE_FLOW", salida["reason"])
    t.vacio("E-34 no hay flujos persistentes", salida["persistentFlows"])

    # 🔴 Y sin identidad declarada, el resultado es el mismo: a quien no persiste no se le exige
    # un storage estandar.
    sin_identidad = _caso(flujos=[_temporal()], standardStorage={}, integrationContract={})
    salida = SB.evaluar(sin_identidad, _senal())
    t.igual("E-34 sin identidad sigue siendo NOT_APPLICABLE", "NOT_APPLICABLE", salida["state"])
    t.verdadero("E-34 y no informa una identidad que no hay", "standardStorage" not in salida)


def test_e35_persistentes_y_temporales_se_evaluan_por_separado(t):
    """E-35 (D7-29) — cada check nombra solo los flujos de su clase."""
    caso = _mixto()
    storage = SB.evaluar(caso, _senal())
    limpieza = TC.evaluar(caso, _senal())
    local = PL.evaluar(caso, _senal())

    t.igual("E-35 el storage mira el persistente", ["f-adjuntos"], storage["persistentFlows"])
    t.igual("E-35 la limpieza mira el temporal", ["f-temporal"], limpieza["temporaryFlows"])
    t.igual("E-35 la prohibicion mira la escritura local", ["f-temporal"], local["localFlows"])
    t.igual("E-35 los tres ven el inventario entero", ["f-adjuntos", "f-temporal"],
            storage["fileFlows"]["flows"])
    t.igual("E-35 los tres pasan", {c: "PASS" for c in CHEQUEOS}, _estados(caso, _senal()))


def test_e36_la_clasificacion_no_es_aplicabilidad(t):
    """E-36 (§6) — para las seis clases, D7 aplica igual y la senal vale lo mismo."""
    t.igual("E-36 son seis clases", 6, len(FLUJOS.CLASES))
    for clase in FLUJOS.CLASES:
        caso = _caso(flujos=[dict(_persistente(), classification=clase)])
        # 🔴 La clase ENTRA en la señal, no se recalcula lo mismo seis veces: si la resolucion no
        # depende de la clase, las dos aserciones de abajo no pueden distinguir una de otra y la
        # mitad se vuelve una constante disfrazada de invariante.
        bloque = c_normativa.resolucion({SENAL: _senal("TRUE", [_ev_senal(
            tipo="TASK_CONTEXT", reference="inventario de flujos",
            claim="la unidad declara un flujo de archivo clasificado %s" % clase,
            supports="TRUE")])})
        t.verdadero("E-36 con %s D7 sigue aplicando" % clase,
                    "D7" in bloque["applicableRules"])
        t.igual("E-36 con %s la senal sigue valiendo TRUE" % clase, "TRUE",
                bloque["signals"][SENAL]["value"])
        for nombre, modulo in MODULOS:
            salida = modulo.evaluar(caso, _senal())
            t.igual("E-36 %s con %s no cambia el valor de la senal" % (nombre, clase),
                    "TRUE", salida["signalValue"])
            t.verdadero("E-36 %s con %s no queda sin resolver por la clase" % (nombre, clase),
                        salida["state"] != "APPLICABILITY_UNRESOLVED")


def test_e37_un_flujo_que_cumple_no_tapa_otro_que_no(t):
    """E-37 (§7) — el FAIL manda, tambien sobre un inventario incompleto."""
    mezcla = _caso(flujos=[_persistente(), _persistente(fid="f-viejo", mecanismo="otro")])
    salida = SB.evaluar(mezcla, _senal())
    t.igual("E-37 el estado", "FAIL", salida["state"])
    t.verdadero("E-37 no aprueba", not SB.aprueba(salida))
    estados = {f["flowId"]: f["state"] for f in salida["flows"]}
    t.igual("E-37 el que cumple sigue en PASS", "PASS", estados["f-adjuntos"])
    t.igual("E-37 y el que no, en FAIL", "FAIL", estados["f-viejo"])

    incompleto = _caso(flujos=[_persistente(fid="f-viejo", mecanismo="otro")], completo=False)
    t.igual("E-37 un bypass probado manda sobre un inventario incompleto", "FAIL",
            SB.evaluar(incompleto, _senal())["state"])

    # 🔴 Y un flujo que NO se declara persistente con una traza de persistencia deja el
    # inventario sin credibilidad: o esta mal clasificado, o la traza es de otro flujo.
    contradicho = _caso(flujos=[dict(_temporal(), evidenceRefs=["e-persistencia"])])
    salida = SB.evaluar(contradicho, _senal())
    t.igual("E-37 la clasificacion contradicha no se resuelve",
            "FILE_FLOW_COVERAGE_UNRESOLVED", salida["state"])
    t.igual("E-37 con su motivo", "FLOW_CLASSIFICATION_CONTRADICTED", salida["reason"])


# -- E-38 a E-40 — §8.4, citado y no inventado ---------------------------------

def test_e38_s3_es_protocolo_y_no_proveedor(t):
    """E-38 (D7-30) — declararlo no resuelve la identidad, y nadie nombra un proveedor."""
    solo_protocolo = _caso(standardStorage={"protocol": "S3"})
    salida = SB.evaluar(solo_protocolo, _senal())
    t.igual("E-38 el protocolo solo no identifica un repositorio",
            "STANDARD_STORAGE_PROVIDER_UNRESOLVED", salida["state"])
    t.verdadero("E-38 no aprueba", not SB.aprueba(salida))

    # Con identidad y con el protocolo, los dos se informan y son campos distintos.
    salida = SB.evaluar(_caso(), _senal())
    t.igual("E-38 la identidad es un campo", ALMACEN["id"], salida["standardStorage"]["id"])
    t.igual("E-38 y el protocolo es otro", "S3", salida["standardStorage"]["protocol"])

    # Y ningun artefacto atribuye un proveedor a la regla: es la segunda red del barrido.
    for nombre, texto in _artefactos_de_d7().items():
        sin_separadores = re.sub(r"[\s_\-]+", "", texto).lower()
        t.vacio("E-38 %s no nombra un proveedor pegado" % nombre,
                [v for v in PEGADOS if v in sin_separadores])
        t.vacio("E-38 %s no nombra un proveedor suelto" % nombre,
                [v for v in SUELTOS
                 if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(v), texto.lower())])


def test_e39_lo_medido_que_se_aparta_se_expone(t):
    """E-39 (D7-31) — profundidad y concentracion medidas, y el estado que dejan."""
    # 🔴 Los numeros van literales, no `SB.LIMITE + 1`. Con la constante adentro, el escenario
    # se mueve junto con lo que verifica: cambiar el limite a 200 movia tambien la entrada del
    # test y el invariante quedaba verde con una pauta que ya no era la del estandar.
    casos = (("FOLDER_DEPTH", {"folderDepth": 21}),
             ("OBJECTS_PER_FOLDER", {"objectsPerFolder": 100001}),
             ("TRAFFIC_CONCENTRATION", {"trafficConcentration": "CONCENTRATED"}))
    for hecho, estructura in casos:
        caso = _caso(storageStructure=dict(estructura, source="PROJECT_ARCHITECTURE"))
        salida = SB.evaluar(caso, _senal())
        t.verdadero("E-39 %s se expone como desvio" % hecho,
                    hecho in salida["storageStructure"]["deviations"])
        t.igual("E-39 %s no deja el check en PASS" % hecho, "PARTIAL", salida["state"])
        t.igual("E-39 %s deja el motivo" % hecho, "STORAGE_STRUCTURE_GUIDANCE_DEVIATION",
                salida["reason"])
        t.verdadero("E-39 %s no aprueba" % hecho, not SB.aprueba(salida))

    # En el limite exacto no hay desvio: el estandar dice "mas de".
    for estructura in ({"folderDepth": 20}, {"objectsPerFolder": 100000},
                       {"trafficConcentration": "BALANCED"}):
        caso = _caso(storageStructure=dict(estructura, source="PROJECT_ARCHITECTURE"))
        salida = SB.evaluar(caso, _senal())
        t.vacio("E-39 en el limite no hay desvio: %s" % list(estructura)[0],
                salida["storageStructure"]["deviations"])
        t.igual("E-39 y el check pasa: %s" % list(estructura)[0], "PASS", salida["state"])


def test_e40_lo_no_medido_no_se_inventa(t):
    """E-40 (D7-32) — sin evidencia, NOT_MEASURED, y no baja el estado."""
    salida = SB.evaluar(_caso(), _senal())
    observaciones = salida["storageStructure"]["observations"]
    t.igual("E-40 son cinco hechos de §8.4", 5, len(observaciones))
    for o in observaciones:
        t.igual("E-40 %s no se midio" % o["fact"], "NOT_MEASURED", o["state"])
        t.verdadero("E-40 %s no inventa un valor" % o["fact"], "value" not in o)
    t.vacio("E-40 sin desvios", salida["storageStructure"]["deviations"])
    t.igual("E-40 y lo no medido no baja el estado", "PASS", salida["state"])
    t.verdadero("E-40 aprueba", SB.aprueba(salida))


# -- E-41 a E-45 — la propagacion, el registro, la traza y el ruteo ------------

def test_e41_la_unidad_propaga_los_seis_controles(t):
    """E-41 (D7-33) — con senal con evidencia y con la forma vieja de booleanos."""
    for nombre, senales in (("con evidencia", {SENAL: _senal("TRUE")}),
                            ("con un booleano", {SENAL: True})):
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-41 %s D7 aplica" % nombre, "D7" in bloque["applicableRules"])
        for pid in POLICIES:
            t.verdadero("E-41 %s propaga %s" % (nombre, pid), pid in bloque["declaredPolicies"])
        for cid in CHEQUEOS:
            t.verdadero("E-41 %s propaga %s" % (nombre, cid), cid in bloque["declaredChecks"])
        t.igual("E-41 %s la senal resuelta viaja" % nombre, "TRUE",
                bloque["signals"][SENAL]["value"])
    # Y la forma vieja declara de donde sale, para que no parezca respaldada.
    bloque = c_normativa.resolucion({SENAL: True})
    t.igual("E-41 el booleano declara su origen", "TASK_CONTEXT",
            bloque["signals"][SENAL]["evidence"][0]["sourceType"])


def test_e42_los_controles_dejan_de_ser_un_hueco(t):
    """E-42 (D7-34) — instalados, declarados, veinticuatro, y sin archivos sueltos."""
    reporte = c_controles.reporte()
    # 📌 Eran veinticuatro cuando D7 cerro; D8 sumo dos. Exacto a proposito.
    t.igual("E-42 son cincuenta y cuatro controles", 54, reporte["summary"]["declaredControls"])
    t.verdadero("E-42 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-42 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-42 ningun archivo suelto", [], reporte["undeclared"])
    t.vacio("E-42 sin errores de schema", reporte["schemaErrors"])

    for control in POLICIES + CHEQUEOS:
        t.igual("E-42 %s esta INSTALLED" % control, "INSTALLED",
                reporte["controls"].get(control))

    resolucion = c_matriz.resolver({SENAL: True})
    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    for control in POLICIES + CHEQUEOS:
        t.verdadero("E-42 %s ya no figura como no instalado" % control, control not in faltan)

    # 🔴 Y el modulo compartido NO es un control: no se declara, y no se reporta como suelto.
    declarados = {c["file"] for c in c_controles.cargar()["controls"]}
    t.verdadero("E-42 flujos.py no se declara como control",
                "controles/lib/flujos.py" not in declarados)


def test_e43_todo_resultado_conserva_la_traza(t):
    """E-43 (D7-35) — ES0901 / 6.3 / 7.1 / D7, en todos los caminos de los tres checks."""
    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        t.igual("E-43 %s declara la tupla" % nombre, TRAZA, modulo.TRAZA)
        for estado, (caso, senal) in caminos().items():
            salida = modulo.evaluar(caso, senal)
            t.igual("E-43 %s en %s conserva la tupla" % (nombre, estado), TRAZA,
                    salida["source"])
            t.igual("E-43 %s en %s dice que control es" % (nombre, estado), nombre,
                    salida["control"])
            t.igual("E-43 %s en %s dice de que senal depende" % (nombre, estado), SENAL,
                    salida["signal"])
    # Y ninguno nombra otra regla ni otro estandar.
    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        for estado, (caso, senal) in caminos().items():
            texto = repr(modulo.evaluar(caso, senal))
            for otra in ("D5", "D6", "D8", "ES0902", "ES0903"):
                t.verdadero("E-43 %s en %s no nombra %s" % (nombre, estado, otra),
                            otra not in texto)


def test_e44_los_estados_existen_y_solo_pasa_uno(t):
    """E-44 (§14) — cada estado declarado se alcanza, y ningun sin resolver aprueba."""
    esperados = {
        CHEQUEOS[0]: 9,
        CHEQUEOS[1]: 8,
        CHEQUEOS[2]: 9,
    }
    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        declarados = set(modulo.ESTADOS)
        t.igual("E-44 %s declara %d estados" % (nombre, esperados[nombre]),
                esperados[nombre], len(modulo.ESTADOS))
        alcanzados = {}
        for estado, (caso, senal) in caminos().items():
            alcanzados[estado] = modulo.evaluar(caso, senal)["state"]
        t.igual("E-44 %s alcanza todos los que declara" % nombre, declarados,
                set(alcanzados))
        for esperado, obtenido in sorted(alcanzados.items()):
            t.igual("E-44 %s alcanza %s" % (nombre, esperado), esperado, obtenido)
        # 🔴 El unico que aprueba es PASS. Ningun estado sin resolver se convierte en PASS.
        for estado, (caso, senal) in caminos().items():
            salida = modulo.evaluar(caso, senal)
            t.igual("E-44 %s aprueba en %s solo si es PASS" % (nombre, estado),
                    estado == "PASS", modulo.aprueba(salida))


def test_e45_la_ejecucion_rutea_sin_crear_una_skill(t):
    """E-45 (§11) — dev-backend con dev-storage resuelve ROUTABLE, y nada se crea."""
    ruteo = c_reg.resolver_ruteo("dev-backend", "dev-storage", None, RUTA_REG)
    t.igual("E-45 el agente existe", "VALID", ruteo["agentValidation"])
    t.igual("E-45 la skill esta instalada", "INSTALLED", ruteo["skillStatus"])
    t.igual("E-45 y rutea", "ROUTABLE", ruteo["result"])
    t.verdadero("E-45 es routable", ruteo["routable"])

    for nombre, modulo in MODULOS:
        pedidos = modulo.skills_de_ejecucion()
        t.verdadero("E-45 %s pide al menos una skill" % nombre, len(pedidos) >= 1)
        for p in pedidos:
            t.igual("E-45 %s pide para si mismo" % nombre, nombre, p["requestedFor"])
            t.verdadero("E-45 %s rutea %s" % (nombre, p["requestedSkill"]), p["routable"])
        t.igual("E-45 %s nombra al dueno de la fila" % nombre, "dev-backend", modulo.AGENTE)

    # Y siguen siendo 27: D7 no crea ni modifica ninguna skill.
    t.igual("E-45 27 skills instaladas", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))
