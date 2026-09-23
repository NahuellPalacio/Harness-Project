# El sustrato de conocimiento confiable: registro de fuentes, procedencia, descubrimiento,
# integridad y frescura.
#
# Escenarios E-01 a E-36 de docs/cambios/conocimiento-fuentes-y-frescura/spec.md.
#
# 🔴 Lo que se verifica es que NO haya camino desde evidencia ausente hasta `CURRENT`. Un
# resolvedor que ante la duda contesta "sin cambios" pasa cualquier test escrito sobre el caso
# feliz: por eso E-29 recorre las combinaciones de evidencia y no una sola.
#
# 🔴 Los estados van CLAVADOS por literal. Leerlos del modulo y compararlos contra si mismos es
# un test que pasa con cualquier renombre.
import ast
import copy
import hashlib
import importlib.util
import inspect
import io
import itertools
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SCHEMAS = RAIZ / "comun" / "schemas"
CLI = BIN / "dev-harness.py"

sys.path.insert(0, str(BIN))
from orquestacion import frescura as fr                  # noqa: E402
from orquestacion import linea_base as lb                # noqa: E402
from orquestacion import procedencia as proc             # noqa: E402
from orquestacion import registro_fuentes as rf          # noqa: E402
from orquestacion import tools as c_tools                # noqa: E402
from integraciones import fuentes as desc                # noqa: E402

REGISTRO = rf.cargar()
LINEA = lb.cargar()
INDICE = proc.indice()

# Dos hashes que no son de nada. Lo que importa de un hash en estos escenarios es si coincide.
HASH_A = "a" * 64
HASH_B = "b" * 64

MODULOS = (BIN / "integraciones" / "fuentes.py",
           BIN / "orquestacion" / "frescura.py",
           BIN / "orquestacion" / "procedencia.py",
           BIN / "orquestacion" / "registro_fuentes.py")


def _entrada(**extra):
    """Una entrada del registro que resuelve CURRENT si nada la contradice."""
    e = {"id": "ES0901", "kind": "norma", "title": "Estandar de Desarrollo", "issuer": None,
         "version": "6.3",
         "filenamePattern": r"(?i)^ES0901\b.*\bv([0-9]+(?:\.[0-9]+)*)\.pdf$",
         "sha256": HASH_A, "extract": "normativa/extractos/ES0901.md", "config": None,
         "status": "CURRENT", "authorityRef": None, "acceptedAt": None, "refutedAt": None}
    e.update(extra)
    return e


def _obs(**extra):
    o = {"id": "ES0901", "found": True, "attachmentId": "10001",
         "filename": "ES0901 - Estandar de Desarrollo ASI v6.3.pdf", "size": 1000,
         "created": "2026-01-01T00:00:00.000+0000", "observed_version": "6.3",
         "observed_sha256": HASH_A, "downloaded": False, "local_path": None,
         "identity_changed": False, "evidence": []}
    o.update(extra)
    return o


def _adjunto(**extra):
    a = {"id": "10001", "filename": "ES0901 - Estandar de Desarrollo ASI v6.3.pdf",
         "size": 1000, "created": "2026-01-01T00:00:00.000+0000",
         "content": "https://contenido.example/adjunto/10001"}
    a.update(extra)
    return a


def _previo(obs=None, **extra):
    """El estado anterior de una fuente, con la forma en que lo escribe `frescura`."""
    o = obs or _obs()
    p = {"attachmentId": o["attachmentId"], "filename": o["filename"], "size": o["size"],
         "created": o["created"], "observed_sha256": o["observed_sha256"]}
    p.update(extra)
    return {"ES0901": p}


def _indice_viejo(version="6.2"):
    """Un indice donde un control declara otra version que la aceptada."""
    return {"ES0901": {"controls": [{"id": "un-control", "type": "CHECK",
                                     "declaredVersion": version}],
                       "matrices": [], "matrixRows": [], "agents": [], "skills": []}}


def _sin_derivados():
    """Un indice donde la fuente no tiene un solo derivado. Aisla la condicion del extracto."""
    return {"ES0901": {"controls": [], "matrices": [], "matrixRows": [], "agents": [],
                       "skills": []}}


def _espia(contenido=b""):
    """Un `bajar` falso que escribe lo que se le diga y anota cada llamada."""
    llamadas = []

    def bajar(url, destino):
        llamadas.append((url, destino))
        carpeta = os.path.dirname(os.path.abspath(destino))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with io.open(destino, "wb") as f:
            f.write(contenido)
        return True, len(contenido)

    return llamadas, bajar


def _arbol(t=None):
    """Un arbol instalado de mentira, con reglas, schemas, agents y skills."""
    tmp = tempfile.mkdtemp(prefix="fuentes")
    binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "orquestacion"
    reglas = Path(tmp) / ".claude" / "harness" / "reglas" / "desarrollo"
    esquemas = Path(tmp) / ".claude" / "harness" / "schemas"
    for d in (binario, reglas, esquemas):
        d.mkdir(parents=True)
    (reglas.parent / "secretos.patrones.json").write_text("{}", encoding="utf-8")
    desde = binario / "procedencia.py"
    desde.write_text("# marcador\n", encoding="utf-8")
    return tmp, desde


def _correr_cli(argv):
    """dev-harness.py en proceso. Devuelve (codigo, stdout, stderr)."""
    spec = importlib.util.spec_from_file_location("dev_harness_fuentes", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(argv)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _llamadas_de(ruta):
    """Los nombres de todo lo que el modulo llama: `os.path.join`, `f.read`, `print`."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        objetivo = nodo.func
        if isinstance(objetivo, ast.Name):
            nombres.add(objetivo.id)
        elif isinstance(objetivo, ast.Attribute):
            nombres.add(objetivo.attr)
    return nombres


def _importados(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add((nodo.module or "").split(".")[0])
    return nombres


# -- El registro de fuentes ----------------------------------------------------

def test_e01_el_registro_valida_y_no_inventa_hashes(t):
    """E-01 — valida contra source-registry/1.1 y sin un original aceptado el hash es null."""
    t.igual("E-01 la version del contrato", "source-registry/1.1",
            REGISTRO.get("schema_version"))
    t.vacio("E-01 valida", rf.validar_schema(REGISTRO))
    t.verdadero("E-01 hay fuentes gestionadas", len(rf.gestionadas(REGISTRO)) >= 3)
    for f in rf.fuentes(REGISTRO):
        sha = f.get("sha256")
        t.verdadero("E-01 %s: el hash es null o un sha256 de verdad" % f["id"],
                    sha is None or (len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)))

    # 🔴 Un hash que no es un sha256 no entra: sin esto, "sha256: 6.3" pasaria.
    roto = copy.deepcopy(REGISTRO)
    roto["sources"][0]["sha256"] = "no-es-un-hash"
    t.verdadero("E-01 un hash con cualquier forma no valida", bool(rf.validar_schema(roto)))


def test_e02_una_entrada_por_fuente(t):
    """E-02 — dos entradas con el mismo id son un registro que no se puede leer."""
    doble = copy.deepcopy(REGISTRO)
    doble["sources"].append(dict(doble["sources"][0], version="6.2"))
    informe = rf.validar(doble)
    t.igual("E-02 la repetida se diagnostica", "DUPLICATE_SOURCE_ID",
            informe["sources"][doble["sources"][0]["id"]])
    t.contiene("E-02 y se dice por que", "una entrada por fuente, no una por version",
               " ".join(rf.hallazgos(doble)))

    # 🔴 Y el registro NO CARGA. Diagnosticarlo y seguir era lo que dejaba a `buscar`
    # devolviendo la primera de dos sin que nadie se enterara: el escenario pide que no cargue.
    tmp, desde = _arbol()
    try:
        reglas = Path(tmp) / ".claude" / "harness" / "reglas" / "desarrollo"
        (reglas / rf.ARCHIVO).write_text(json.dumps(doble, ensure_ascii=False),
                                         encoding="utf-8")
        try:
            rf.cargar(str(desde))
            t.verdadero("E-02 un id repetido hace que el registro no cargue", False)
        except rf.RegistroInvalido as e:
            t.contiene("E-02 un id repetido hace que el registro no cargue",
                       "el registro lleva una entrada por fuente", str(e))
            t.contiene("E-02 y nombra la repetida", doble["sources"][0]["id"], str(e))
        # Con el registro bueno en el mismo arbol, carga.
        (reglas / rf.ARCHIVO).write_text(json.dumps(REGISTRO, ensure_ascii=False),
                                         encoding="utf-8")
        t.igual("E-02 y con una entrada por fuente carga", len(REGISTRO["sources"]),
                len(rf.fuentes(rf.cargar(str(desde)))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e03_sin_lista_de_derivados(t):
    """E-03 — un `derived[]` en el registro lo invalida: el impacto se calcula."""
    con_lista = copy.deepcopy(REGISTRO)
    con_lista["sources"][0]["derived"] = ["control:approved-technology-required"]
    errores = rf.validar_schema(con_lista)
    t.verdadero("E-03 el registro con derivados no valida", bool(errores))
    t.contiene("E-03 y el error nombra la clave", "derived", " ".join(errores))
    for f in rf.fuentes(REGISTRO):
        t.vacio("E-03 %s no lleva derivados escritos a mano" % f["id"], f.get("derived"))


def test_e04_la_linea_base_toma_la_version_del_registro(t):
    """E-04 — la linea base no declara la version de una fuente gestionada; la lee del registro."""
    for fid, version in (("ES0901", "6.3"), ("ES0902", "6.2")):
        f = lb.fuente(fid, LINEA)
        t.vacio("E-04 %s no declara version en la linea base" % fid, f.get("version"))
        t.igual("E-04 %s la resuelve por el registro" % fid, version, lb.version_de(f))
        t.igual("E-04 y es la misma que dice el registro", version, rf.version_de(fid))

    # 🔴 Declararla en los dos lados es el mapeo duplicado que este cambio vino a sacar.
    dos_veces = copy.deepcopy(LINEA)
    dos_veces["sources"][0]["version"] = "6.3"
    veredicto, errores = lb.validar(dos_veces)
    t.igual("E-04 declarar la version en los dos lados invalida la linea base",
            "NORMATIVE_BASELINE_INVALID", veredicto)
    t.contiene("E-04 y dice cual manda", "la dice el registro", " ".join(errores))

    # Una fuente que el registro NO gestiona conserva lo que declare.
    suelta = {"id": "RES-177-ASINF-2013", "version": "2013"}
    t.igual("E-04 una fuente no gestionada conserva la suya", "2013", lb.version_de(suelta))


def test_e05_o1_no_cambia(t):
    """E-05 — con el arbol como viene, O1 sale igual que antes y por las mismas razones."""
    veredicto, errores = lb.validar(LINEA)
    t.igual("E-05 la linea base sigue valida", "NORMATIVE_BASELINE_VALID", veredicto)
    t.vacio("E-05 sin errores", errores)
    revision = lb.revision()
    t.igual("E-05 la revision sigue incompleta", "REVIEW_INCOMPLETE", revision["result"])
    for estado in ("EXTERNAL_NORMATIVE_CONTEXT_REQUIRED", "NORMATIVE_SUPERSESSION_UNRESOLVED"):
        t.verdadero("E-05 sigue por %s" % estado, estado in revision["states"])
    t.igual("E-05 y la policy tampoco se mueve", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
            lb.estado_de_policy(revision))
    fila = [f for f in lb.resolver()["sources"] if f["id"] == "ES0901"][0]
    t.igual("E-05 la fila de ES0901 sigue trayendo su version", "6.3", fila["version"])


def test_e06_un_extracto_que_no_esta_se_dice(t):
    """E-06 — una fuente cuyo extracto no existe se diagnostica con su id y su ruta."""
    sin_extracto = {"schema_version": "source-registry/1.1",
                    "sources": [_entrada(extract="normativa/extractos/NO-EXISTE.md")]}
    t.igual("E-06 se diagnostica", "SOURCE_EXTRACT_MISSING",
            rf.validar(sin_extracto)["sources"]["ES0901"])
    dicho = " ".join(rf.hallazgos(sin_extracto))
    t.contiene("E-06 nombra la fuente", "ES0901", dicho)
    t.contiene("E-06 y la ruta", "normativa/extractos/NO-EXISTE.md", dicho)
    t.igual("E-06 y la ruta no se resuelve", None,
            rf.ruta_de_extracto(_entrada(extract="normativa/extractos/NO-EXISTE.md")))
    t.verdadero("E-06 la del extracto que si esta se resuelve",
                bool(rf.ruta_de_extracto(_entrada())))


# -- El indice inverso de procedencia ------------------------------------------

def test_e07_de_una_fuente_a_sus_controles(t):
    """E-07 — los controles que declaran ES0901 en `normativeSources[]`, y ninguno mas."""
    ids = {c["id"] for c in proc.impacto("ES0901", INDICE)["controls"]}
    t.verdadero("E-07 estan los de ES0901", "approved-technology-required" in ids)
    t.verdadero("E-07 y tambien los de G2", "industry-good-practices-required" in ids)
    t.verdadero("E-07 y no los que solo declaran ES0902",
                "gcba-it-security-normative-compliance-required" not in ids)
    solo_es0902 = {c["id"] for c in proc.impacto("ES0902", INDICE)["controls"]}
    t.verdadero("E-07 que si estan en ES0902",
                "gcba-it-security-normative-compliance-required" in solo_es0902)


def test_e08_de_una_fuente_a_las_filas_de_su_matriz(t):
    """E-08 — las filas, con sus policies, sus checks y sus reviews."""
    filas = {f["id"]: f for f in proc.impacto("ES0901", INDICE)["matrixRows"]}
    t.verdadero("E-08 esta G1", "ES0901.G1" in filas)
    t.verdadero("E-08 con su policy",
                "approved-technology-required" in filas["ES0901.G1"]["policies"])
    t.verdadero("E-08 con su check",
                "technology-homologation" in filas["ES0901.G1"]["checks"])
    o1 = {f["id"]: f for f in proc.impacto("ES0902", INDICE)["matrixRows"]}
    t.verdadero("E-08 y la review de O1 esta del lado de ES0902",
                "gcba-it-security-normative-review" in o1["ES0902.O1"]["reviews"])
    t.igual("E-08 la matriz de ES0901 declara su version", "6.3",
            proc.impacto("ES0901", INDICE)["matrices"][0]["declaredVersion"])


def test_e09_un_agente_y_una_skill_que_declaran_su_fuente(t):
    """E-09 — `sources:` en el frontmatter entra en el indice de esa fuente."""
    t.igual("E-09 el bloque de guiones", [("ES0901", "6.3")],
            proc.declaraciones_de("---\nname: x\nsources:\n  - ES0901@6.3\n---\n"))
    t.igual("E-09 la lista en linea", [("ES0902", None)],
            proc.declaraciones_de("---\nname: x\nsources: [ES0902]\n---\n"))
    t.vacio("E-09 lo que esta en el cuerpo no es metadata",
            proc.declaraciones_de("---\nname: x\n---\nsources:\n  - ES0901@6.3\n"))

    tmp, desde = _arbol()
    try:
        agentes = Path(tmp) / ".claude" / "agents"
        skills = Path(tmp) / ".claude" / "skills" / "dev-ejemplo"
        agentes.mkdir(parents=True)
        skills.mkdir(parents=True)
        (agentes / "dev-ejemplo.md").write_text(
            "---\nname: dev-ejemplo\nsources:\n  - ES0901@6.3\n---\n# Agent: dev-ejemplo\n",
            encoding="utf-8")
        (skills / "SKILL.md").write_text(
            "---\nname: dev-ejemplo\nsources:\n  - ES0901@6.3\n---\n# Skill: dev-ejemplo\n",
            encoding="utf-8")
        declarado = proc.componentes(str(desde))
        t.igual("E-09 el agente declara su fuente", [("ES0901", "6.3")],
                declarado.get(("agent", "dev-ejemplo")))
        t.igual("E-09 la skill tambien", [("ES0901", "6.3")],
                declarado.get(("skill", "dev-ejemplo")))
        ind = proc.indice(str(desde))
        t.igual("E-09 y salen en el indice de ES0901", ["dev-ejemplo"],
                [a["id"] for a in proc.impacto("ES0901", ind)["agents"]])
        t.igual("E-09 la skill tambien sale", ["dev-ejemplo"],
                [s["id"] for s in proc.impacto("ES0901", ind)["skills"]])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e10_un_derivado_que_declara_otra_version(t):
    """E-10 — con las dos versiones a la vista."""
    viejos = proc.desactualizados("ES0901", "6.4", INDICE)
    t.verdadero("E-10 hay derivados viejos si la aceptada es 6.4", len(viejos) > 10)
    uno = viejos[0]
    t.igual("E-10 dice cual es la declarada", "6.3", uno["declaredVersion"])
    t.igual("E-10 y cual la aceptada", "6.4", uno["sourceVersion"])
    t.verdadero("E-10 y nombra el activo", uno["asset"].startswith(("control:", "matrix")))
    t.vacio("E-10 con la aceptada en 6.3 no hay ninguno",
            proc.desactualizados("ES0901", "6.3", INDICE))

    # Lo que no declara version no cuenta como viejo: no saber no es estar desactualizado.
    sin_version = {"ES0901": {"controls": [{"id": "c", "type": "CHECK", "declaredVersion": None}],
                              "matrices": [], "matrixRows": [], "agents": [], "skills": []}}
    t.vacio("E-10 lo que no declara version no cuenta",
            proc.desactualizados("ES0901", "6.4", sin_version))


def test_e11_un_id_que_nadie_declara(t):
    """E-11 — impacto vacio, no el arbol entero."""
    vacio = proc.impacto("NORMA-QUE-NO-EXISTE", INDICE)
    for clave in ("controls", "matrices", "matrixRows", "agents", "skills"):
        t.vacio("E-11 %s vacio" % clave, vacio[clave])
    t.vacio("E-11 y aplanado tambien", proc.aplanar(vacio))


# -- El descubrimiento ---------------------------------------------------------

def test_e12_metadata_sin_cambios_no_baja_nada(t):
    """E-12 — mismo adjunto, mismo nombre, mismo tamaño, misma version: no se baja."""
    llamadas, bajar = _espia(b"cualquier cosa")
    tmp = tempfile.mkdtemp(prefix="fuentes-sin-bajar")
    try:
        obs = desc.observar([_entrada()], [_adjunto()], _previo(), bajar, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    t.vacio("E-12 no se llamo a bajar", llamadas)
    t.igual("E-12 y no se declara bajado", False, obs[0]["downloaded"])
    t.igual("E-12 el hash se reusa del estado anterior", HASH_A, obs[0]["observed_sha256"])
    t.contiene("E-12 y se dice por que", "no cambio", " ".join(obs[0]["evidence"]))

    # 🔴 El caso que el fixture de arriba no podia fallar: el estado anterior SIN hash, porque
    # la descarga de esa vez no anduvo, y un hash aceptado en el registro. Es el unico que
    # distingue "la metadata manda" de "se baja igual", y es el que se da todas las sesiones en
    # cuanto una descarga falla una vez.
    llamadas2, bajar2 = _espia(b"lo mismo de siempre")
    tmp2 = tempfile.mkdtemp(prefix="fuentes-sin-hash-previo")
    try:
        previo = _previo(_obs(observed_sha256=None))
        obs2 = desc.observar([_entrada()], [_adjunto()], previo, bajar2, tmp2)[0]
        t.vacio("E-12 con el estado anterior sin hash tampoco se baja", llamadas2)
        t.igual("E-12 y no se declara bajado", False, obs2["downloaded"])
        t.contiene("E-12 y se dice que queda sin verificar", "sin verificar",
                   " ".join(obs2["evidence"]))
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)


def test_e13_una_version_posterior(t):
    """E-13 — version observada mayor que la aceptada: UPDATE_AVAILABLE."""
    adjunto = _adjunto(filename="ES0901 - Estandar de Desarrollo ASI v6.4.pdf", id="10002")
    obs = desc.observar([_entrada()], [adjunto])[0]
    t.igual("E-13 la version sale del nombre", "6.4", obs["observed_version"])
    r = fr.resolver_una(_entrada(), obs)
    t.igual("E-13 el estado", "UPDATE_AVAILABLE", r["state"])
    t.igual("E-13 y bloquea", True, r["blocking"])


def test_e14_sin_version_resoluble(t):
    """E-14 — VERSION_UNRESOLVED, que no es lo mismo que sin cambios."""
    adjunto = _adjunto(filename="ES0901 sin numero.pdf")
    entrada = _entrada(filenamePattern=r"(?i)^ES0901\b.*\.pdf$")
    obs = desc.observar([entrada], [adjunto])[0]
    t.igual("E-14 se reconoce el archivo", True, obs["found"])
    t.igual("E-14 y la version no se resuelve", None, obs["observed_version"])
    r = fr.resolver_una(entrada, obs)
    t.igual("E-14 el estado", "VERSION_UNRESOLVED", r["state"])
    t.contiene("E-14 y se dice", "no se pudo resolver", " ".join(r["evidence"]))

    # Cuando la Ficha la declara, se resuelve por ahi.
    obs2 = desc.observar([entrada], [adjunto], texto_ficha="ES0901: 6.4\n")[0]
    t.igual("E-14 la Ficha tambien la puede decir", "6.4", obs2["observed_version"])


def test_e15_misma_version_con_otra_identidad(t):
    """E-15 — se baja y se hashea ANTES de resolver."""
    contenido = b"el pdf que reemplazaron"
    llamadas, bajar = _espia(contenido)
    tmp = tempfile.mkdtemp(prefix="fuentes-bajar")
    try:
        previo = _previo()
        previo["ES0901"]["attachmentId"] = "99999"          # otro adjunto, misma version
        obs = desc.observar([_entrada()], [_adjunto()], previo, bajar, tmp)[0]
        t.igual("E-15 se bajo una vez", 1, len(llamadas))
        t.igual("E-15 se declara bajado", True, obs["downloaded"])
        t.igual("E-15 la identidad cambio", True, obs["identity_changed"])
        t.igual("E-15 y el hash es el del documento bajado",
                hashlib.sha256(contenido).hexdigest(), obs["observed_sha256"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r = fr.resolver_una(_entrada(), obs)
    t.igual("E-15 y con un contenido distinto del aceptado es una alerta",
            "SOURCE_INTEGRITY_ALERT", r["state"])

    # Sin poder hashear lo que cambio, el estado es el que dice que no se pudo decidir.
    sin_hash = _obs(identity_changed=True, observed_sha256=None)
    t.igual("E-15 sin hash del que cambio", "SOURCE_CHANGED_SAME_VERSION",
            fr.resolver_una(_entrada(), sin_hash)["state"])

    # 🔴 Y con una fuente que todavia no tiene hash aceptado —que es como esta hoy el registro
    # entero— la regla de la misma version es la UNICA que manda bajar. Sin este caso, sacarla
    # del codigo no rompia nada: quedaba tapada por la regla del hash aceptado.
    llamadas2, bajar2 = _espia(b"otro contenido")
    tmp2 = tempfile.mkdtemp(prefix="fuentes-sin-hash-aceptado")
    try:
        previo = _previo(_obs(observed_sha256=None))
        previo["ES0901"]["attachmentId"] = "99999"
        obs2 = desc.observar([_entrada(sha256=None)], [_adjunto()], previo, bajar2, tmp2)[0]
        t.igual("E-15 sin hash aceptado tambien se baja", 1, len(llamadas2))
        t.igual("E-15 y se hashea lo que cambio",
                hashlib.sha256(b"otro contenido").hexdigest(), obs2["observed_sha256"])
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)


def test_e16_la_fuente_no_esta_en_la_ficha(t):
    """E-16 — SOURCE_MISSING."""
    obs = desc.observar([_entrada()], [_adjunto(filename="otra-cosa.pdf")])[0]
    t.igual("E-16 no se encontro", False, obs["found"])
    r = fr.resolver_una(_entrada(), obs)
    t.igual("E-16 el estado", "SOURCE_MISSING", r["state"])
    t.contiene("E-16 y se dice", "no aparece en el canal", " ".join(r["evidence"]))
    t.igual("E-16 sin adjuntos, lo mismo", "SOURCE_MISSING",
            fr.resolver_una(_entrada(), desc.observar([_entrada()], [])[0])["state"])


def test_e17_el_modo_local_no_necesita_jira(t):
    """E-17 — nombre de archivo y SHA-256 del contenido, sin red."""
    tmp = tempfile.mkdtemp(prefix="fuentes-local")
    try:
        contenido = b"%PDF-1.7 el original"
        nombre = "ES0901 - Estandar de Desarrollo ASI v6.3.pdf"
        (Path(tmp) / nombre).write_bytes(contenido)
        obs = desc.observar_archivos([_entrada()], tmp)[0]
        t.igual("E-17 se reconoce", True, obs["found"])
        t.igual("E-17 con su version", "6.3", obs["observed_version"])
        t.igual("E-17 y el sha del archivo", hashlib.sha256(contenido).hexdigest(),
                obs["observed_sha256"])
        t.igual("E-17 no hay nada que bajar", False, obs["downloaded"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    t.igual("E-17 y la firma no admite transporte ni descarga",
            ["entradas", "directorio"],
            list(inspect.signature(desc.observar_archivos).parameters))


def test_e18_la_ficha_es_de_lectura(t):
    """E-18 — el descubrimiento no transiciona, no comenta, no sube y no borra."""
    ruta = BIN / "integraciones" / "fuentes.py"
    llamadas = _llamadas_de(ruta)
    for prohibido in ("post", "put", "patch", "delete", "transicionar", "comentar", "subir",
                      "pedir", "pedir_bytes", "remove", "rmtree", "unlink", "rename"):
        t.verdadero("E-18 no llama a `%s`" % prohibido, prohibido not in llamadas)
    t.igual("E-18 lo unico que importa es de la biblioteca estandar",
            {"hashlib", "io", "os", "re"}, _importados(ruta))
    # El adapter no se importa ni se toca: lo unico que entra de afuera es el callable que se
    # le inyecta. La prosa del modulo puede nombrar a Jira; el codigo no lo llama.
    t.verdadero("E-18 y no llama a nada del adapter de Jira",
                "jira." not in ruta.read_text(encoding="utf-8").lower())
    t.verdadero("E-18 lo que baja entra inyectado",
                "bajar" in inspect.signature(desc.observar).parameters)


def test_e19_el_descubrimiento_no_imprime(t):
    """E-19 — devuelve datos: su salida no toca stdout ni stderr."""
    ruta = BIN / "integraciones" / "fuentes.py"
    llamadas = _llamadas_de(ruta)
    t.verdadero("E-19 no llama a print", "print" not in llamadas)
    fuente = ruta.read_text(encoding="utf-8")
    for prohibido in ("sys.stdout", "sys.stderr", "logging"):
        t.verdadero("E-19 no nombra `%s`" % prohibido, prohibido not in fuente)


# -- La integridad -------------------------------------------------------------

def test_e20_misma_version_y_otro_contenido(t):
    """E-20 — SOURCE_INTEGRITY_ALERT, y no hay entrada que lo lleve a CURRENT."""
    r = fr.resolver_una(_entrada(), _obs(observed_sha256=HASH_B))
    t.igual("E-20 el estado", "SOURCE_INTEGRITY_ALERT", r["state"])
    t.igual("E-20 bloquea", True, r["blocking"])
    t.contiene("E-20 y lo dice", "reemplazado sin cambiar el numero", " ".join(r["evidence"]))
    for extra in ({"downloaded": True}, {"identity_changed": False},
                  {"identity_changed": True}, {"created": None}, {"size": None}):
        obs = _obs(observed_sha256=HASH_B, **extra)
        t.verdadero("E-20 con %s sigue sin ser CURRENT" % sorted(extra),
                    fr.resolver_una(_entrada(), obs)["state"] != "CURRENT")


def test_e21_misma_version_y_mismo_contenido(t):
    """E-21 — puede quedar CURRENT."""
    r = fr.resolver_una(_entrada(), _obs())
    t.igual("E-21 el estado", "CURRENT", r["state"])
    t.igual("E-21 no bloquea", False, r["blocking"])
    t.contiene("E-21 y dice contra que", "coinciden con lo aceptado", " ".join(r["evidence"]))


def test_e22_una_version_anterior(t):
    """E-22 — VERSION_REGRESSION, y no se promueve sola."""
    obs = _obs(observed_version="6.2")
    r = fr.resolver_una(_entrada(), obs)
    t.igual("E-22 el estado", "VERSION_REGRESSION", r["state"])
    t.igual("E-22 bloquea", True, r["blocking"])
    t.igual("E-22 y el riesgo sube", "HIGH", r["effectiveRisk"])
    t.igual("E-22 el registro no se movio", "6.3", r["registry_version"])


def test_e23_el_hash_es_el_del_original(t):
    """E-23 — el del markdown del extracto da distinto y no se usa en ninguna comparacion."""
    ruta = rf.ruta_de_extracto(_entrada())
    del_extracto = hashlib.sha256(Path(ruta).read_bytes()).hexdigest()
    t.verdadero("E-23 el hash del extracto no es el aceptado", del_extracto != HASH_A)
    r = fr.resolver_una(_entrada(), _obs(observed_sha256=del_extracto))
    t.igual("E-23 pasarlo como observado es una alerta, no un CURRENT",
            "SOURCE_INTEGRITY_ALERT", r["state"])

    # Y el que calcula el descubrimiento es el del archivo que baja, byte a byte.
    tmp = tempfile.mkdtemp(prefix="fuentes-hash")
    try:
        contenido = b"bytes del original"
        (Path(tmp) / "ES0901 - Estandar de Desarrollo ASI v6.3.pdf").write_bytes(contenido)
        obs = desc.observar_archivos([_entrada()], tmp)[0]
        t.igual("E-23 el descubrimiento hashea el archivo",
                hashlib.sha256(contenido).hexdigest(), obs["observed_sha256"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- La resolucion de frescura -------------------------------------------------

def test_e24_las_cinco_condiciones(t):
    """E-24 — sacando cualquiera de las cinco, el estado deja de ser CURRENT."""
    t.igual("E-24 con las cinco", "CURRENT", fr.resolver_una(_entrada(), _obs())["state"])
    casos = (
        ("sin descubrir", _entrada(), _obs(found=False), None),
        ("sin version resuelta", _entrada(), _obs(observed_version=None), None),
        ("sin integridad aceptada", _entrada(sha256=None), _obs(), None),
        ("con integridad contradicha", _entrada(), _obs(observed_sha256=HASH_B), None),
        ("sin extracto activo", _entrada(extract="normativa/extractos/NO-EXISTE.md"),
         _obs(), None),
        # 🔴 El extracto ESTA y salio de otra version: el caso que la ausencia del archivo
        # tapaba. La fuente aceptada es 6.2, lo observado es 6.2, los hashes coinciden y nada
        # quedo viejo — lo unico que no coincide es de que version salio el extracto activo.
        ("con el extracto de otra version", _entrada(version="6.2"),
         _obs(observed_version="6.2"), _sin_derivados()),
        ("con un derivado viejo", _entrada(), _obs(), _indice_viejo()),
    )
    for nombre, entrada, obs, ind in casos:
        r = fr.resolver_una(entrada, obs, ind=ind)
        t.verdadero("E-24 %s no es CURRENT" % nombre, r["state"] != "CURRENT")
        t.igual("E-24 %s bloquea" % nombre, True, r["blocking"])
        t.verdadero("E-24 %s deja su motivo" % nombre, len(r["evidence"]) > 0)


def test_e25_sin_canal_no_hay_frescura(t):
    """E-25 — FRESHNESS_UNVERIFIED con la evidencia perfecta, y nunca CURRENT."""
    r = fr.resolver_una(_entrada(), _obs(), canal_disponible=False)
    t.igual("E-25 el estado", "FRESHNESS_UNVERIFIED", r["state"])
    t.contiene("E-25 y el motivo", "no se pudo consultar", " ".join(r["evidence"]))
    doc = fr.documento([_entrada()], [_obs()], canal=None)
    t.igual("E-25 sin canal en el documento entero", "FRESHNESS_UNVERIFIED",
            doc["sources"]["ES0901"]["state"])
    doc2 = fr.documento([_entrada()], [_obs()], canal={"reachable": False, "reason": "caido"})
    t.igual("E-25 y con el canal caido", "FRESHNESS_UNVERIFIED",
            doc2["sources"]["ES0901"]["state"])


def test_e26_un_derivado_viejo_impide_current(t):
    """E-26 — aunque la fuente este intacta."""
    r = fr.resolver_una(_entrada(), _obs(), ind=_indice_viejo())
    t.verdadero("E-26 no es CURRENT", r["state"] != "CURRENT")
    t.igual("E-26 y se nombra el derivado", ["control:un-control"], r["stale_derived"])
    t.contiene("E-26 con su motivo", "declarando otra version", " ".join(r["evidence"]))


def test_e27_la_misma_evidencia_da_lo_mismo(t):
    """E-27 — estado, riesgo e impacto, en el mismo orden."""
    argumentos = ([_entrada()], [_obs()], {"key": "GCBA-1", "reachable": True}, {},
                  "2026-01-01T00:00:00")
    uno = fr.documento(*argumentos)
    otro = fr.documento(*argumentos)
    t.igual("E-27 los dos documentos son identicos",
            json.dumps(uno, sort_keys=True), json.dumps(otro, sort_keys=True))
    t.igual("E-27 el impacto sale ordenado", sorted(uno["sources"]["ES0901"]["derived_impact"]),
            uno["sources"]["ES0901"]["derived_impact"])


def test_e28_todo_estado_se_puede_contradecir(t):
    """E-28 — id, versiones, hashes y evidencia viajan con cada estado."""
    doc = fr.documento(rf.gestionadas(REGISTRO), [_obs()],
                       canal={"key": "GCBA-1", "reachable": True})
    for sid, f in doc["sources"].items():
        for campo in ("state", "registry_version", "observed_version", "registry_sha256",
                      "observed_sha256", "derived_impact", "evidence", "blocking"):
            t.verdadero("E-28 %s trae `%s`" % (sid, campo), campo in f)
        t.verdadero("E-28 %s trae con que contradecirlo" % sid, len(f["evidence"]) > 0)


def test_e29_ningun_camino_desde_la_ausencia_hasta_current(t):
    """E-29 — recorridas las combinaciones, la unica CURRENT es la de las cinco condiciones."""
    versiones = ("6.3", "6.4", None)
    hashes = (HASH_A, HASH_B, None)
    extractos = ("normativa/extractos/ES0901.md", "normativa/extractos/NO-EXISTE.md")
    corrientes = 0
    total = 0
    for encontrada, version, sha, extracto, viejo, canal in itertools.product(
            (True, False), versiones, hashes, extractos, (False, True), (True, False)):
        total += 1
        entrada = _entrada(extract=extracto)
        obs = _obs(found=encontrada, observed_version=version, observed_sha256=sha)
        estado = fr.resolver_una(entrada, obs, canal_disponible=canal,
                                 ind=_indice_viejo() if viejo else None)["state"]
        if estado != "CURRENT":
            continue
        corrientes += 1
        t.verdadero("E-29 la CURRENT tiene las cinco condiciones",
                    encontrada and version == "6.3" and sha == HASH_A
                    and extracto.endswith("ES0901.md") and not viejo and canal)
    t.igual("E-29 y es una sola de las %d combinaciones" % total, 1, corrientes)


# -- El estado en disco --------------------------------------------------------

def test_e30_el_estado_valida_contra_su_contrato(t):
    """E-30 — y un estado que no existe no se escribe."""
    doc = fr.documento([_entrada()], [_obs()], canal={"key": "GCBA-1", "reachable": True})
    t.igual("E-30 la version del contrato", "sources-state/1.1", doc["schema_version"])
    t.vacio("E-30 valida", fr.validar(doc))
    roto = copy.deepcopy(doc)
    roto["sources"]["ES0901"]["state"] = "AL_DIA"
    t.verdadero("E-30 un estado inventado no valida", bool(fr.validar(roto)))
    tmp = tempfile.mkdtemp(prefix="fuentes-estado")
    try:
        destino = os.path.join(tmp, ".claude", "harness.fuentes.json")
        try:
            fr.escribir(roto, destino)
            t.verdadero("E-30 y no se escribe", False)
        except ValueError as e:
            t.contiene("E-30 y no se escribe", "no valida", str(e))
        t.igual("E-30 el archivo no quedo", False, os.path.isfile(destino))
        fr.escribir(doc, destino)
        t.igual("E-30 el bueno si", True, os.path.isfile(destino))
        t.vacio("E-30 y lo escrito valida",
                fr.validar(json.loads(Path(destino).read_text(encoding="utf-8"))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e31_el_validador_interpreta_un_mapa(t):
    """E-31 — `additionalProperties` con un schema valida los valores del mapa."""
    armador = c_tools._armador()
    esquema = {"type": "object",
               "additionalProperties": {"type": "object", "required": ["state"],
                                        "additionalProperties": False,
                                        "properties": {"state": {"type": "string",
                                                                 "enum": ["A", "B"]}}}}
    armador.controlar_soporte(esquema)
    t.vacio("E-31 un mapa valido pasa", armador.validar({"x": {"state": "A"}}, esquema))
    errores = armador.validar({"x": {"state": "Z"}}, esquema)
    t.verdadero("E-31 un valor fuera del enum no pasa", bool(errores))
    t.contiene("E-31 y el error nombra la clave", "$.x.state", " ".join(errores))
    t.verdadero("E-31 una clave de mas adentro del mapa tampoco",
                bool(armador.validar({"x": {"state": "A", "otra": 1}}, esquema)))
    t.verdadero("E-31 lo que falta se sigue exigiendo",
                bool(armador.validar({"x": {}}, esquema)))

    # 🔴 Se amplia el validador, no se afloja el schema: lo que adentro del mapa no se
    # interpreta sigue sin interpretarse, y se declara.
    try:
        armador.controlar_soporte({"type": "object",
                                   "additionalProperties": {"type": "objeto"}})
        t.verdadero("E-31 un schema roto adentro del mapa se declara", False)
    except Exception as e:                                  # noqa: BLE001
        t.contiene("E-31 un schema roto adentro del mapa se declara", "objeto", str(e))
    try:
        armador.controlar_soporte({"type": "object", "additionalProperties": True})
        t.verdadero("E-31 y `true` sigue sin interpretarse", False)
    except Exception as e:                                  # noqa: BLE001
        t.contiene("E-31 y `true` sigue sin interpretarse", "additionalProperties", str(e))


def test_e32_el_estado_se_escribe_redactado(t):
    """E-32 — un secreto en el nombre de un adjunto no queda en claro."""
    secreto = "AKIA" + "ZZ1234567890ABCD"
    obs = _obs(filename="ES0901 %s v6.3.pdf" % secreto)
    doc = fr.documento([_entrada()], [obs], canal={"key": "GCBA-1", "reachable": True})
    tmp = tempfile.mkdtemp(prefix="fuentes-secreto")
    try:
        destino = os.path.join(tmp, ".claude", "harness.fuentes.json")
        fr.escribir(doc, destino)
        texto = Path(destino).read_text(encoding="utf-8")
        t.no_contiene("E-32 el secreto no quedo en el archivo", secreto, texto)
        t.contiene("E-32 y se declara que se redacto", "secreto redactado", texto)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e33_pending_count_sale_de_los_estados(t):
    """E-33 — lo cuenta el resolvedor, no lo declara quien escribe."""
    entradas = [_entrada(), _entrada(id="ES0902", version="6.2",
                                     extract="normativa/extractos/ES0902.md")]
    doc = fr.documento(entradas, [_obs()], canal={"key": "GCBA-1", "reachable": True})
    bloqueadas = [s for s in doc["sources"].values() if s["blocking"]]
    t.igual("E-33 cuenta las que bloquean", len(bloqueadas), doc["pending_count"])
    t.igual("E-33 y acá es una sola", 1, doc["pending_count"])
    t.verdadero("E-33 no hay forma de declararlo por afuera",
                "pending_count" not in inspect.signature(fr.documento).parameters)


def test_e34_ninguna_ruta_nombra_sharepoint(t):
    """E-34 — ni los modulos, ni los contratos, ni el registro."""
    archivos = list(MODULOS) + [SCHEMAS / "source-registry.schema.json",
                                SCHEMAS / "source-state.schema.json",
                                REGLAS / "source-registry.json",
                                CLI]
    for archivo in archivos:
        t.verdadero("E-34 %s no nombra SharePoint" % archivo.name,
                    "sharepoint" not in archivo.read_text(encoding="utf-8").lower())


# -- La CLI --------------------------------------------------------------------

def test_e35_la_cli_escribe_y_sale_cero(t):
    """E-35 — una fuente desactualizada no es una falla del harness."""
    tmp = tempfile.mkdtemp(prefix="fuentes-cli")
    try:
        codigo, salida, error = _correr_cli(["fuentes", "--proyecto", tmp])
        t.igual("E-35 sale 0", 0, codigo)
        destino = os.path.join(tmp, ".claude", "harness.fuentes.json")
        t.igual("E-35 y escribio el estado", True, os.path.isfile(destino))
        doc = json.loads(Path(destino).read_text(encoding="utf-8"))
        t.verdadero("E-35 con fuentes pendientes", doc["pending_count"] > 0)
        t.vacio("E-35 y lo escrito valida", fr.validar(doc))
        t.contiene("E-35 y se dice que no se pudo verificar", "sin verificar", salida + error)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e36_con_json_el_documento_va_por_stdout(t):
    """E-36 — y todo lo demas por stderr."""
    tmp = tempfile.mkdtemp(prefix="fuentes-cli-json")
    try:
        codigo, salida, error = _correr_cli(["fuentes", "--proyecto", tmp, "--json"])
        t.igual("E-36 sale 0", 0, codigo)
        doc = json.loads(salida)
        t.igual("E-36 stdout es el documento", "sources-state/1.1", doc["schema_version"])
        t.no_contiene("E-36 y no lleva la prosa", "Fuentes gestionadas", salida)
        t.contiene("E-36 que salio por stderr", "aviso:", error)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
