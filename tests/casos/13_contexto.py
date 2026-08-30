# El contrato PROJECT_CONTEXT: lo que contexto-armar.py escribe al lado del indice.
#
# Escenarios E-01 a E-19 de docs/cambios/contexto-de-proyecto/spec.md, menos E-18 -que
# es del instalador y vive en tests/casos/14-contexto-instalador.ps1- y menos E-20, que
# tiene por sujeto una corrida de dev-iniciador-code y se verifica por lectura,
# ADR-0009: ningun test puede obligar a un modelo a describir bien un proyecto.
import io
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas    # noqa: E402
from lib import secretos  # noqa: E402

ARMAR = RAIZ / "comun" / "bin" / "contexto-armar.py"
MAPA = RAIZ / "comun" / "bin" / "mapa-codigo.py"
CHECK = RAIZ / "harnesses" / "desarrollo" / "checks" / "dev-codebase-forma.py"
HOOKS = RAIZ / "comun" / "hooks"
CODEBASE_REAL = RAIZ / "docs" / "codebase"
CORPUS = RAIZ / "tests" / "fixtures" / "corpus-secretos.txt"

SALIDA = "project-context.json"

_modulo = reglas._cargar(str(ARMAR))


# ── Un proyecto descartable ──────────────────────────────────────────────────────

FICHA_API = """# api

## Qué es
La API HTTP del sistema. Expone los endpoints públicos.

## Qué expone
`POST /reservas`, y usa [db](db.md).

## De qué depende
[db](db.md) y PostgreSQL.

## Dónde está
`src/api`, `src/api/rutas.ts`
"""

FICHA_DB = """# db

## Qué es
Persistencia sobre PostgreSQL.

## Qué expone
El repositorio de reservas.

## De qué depende
PostgreSQL.

## Dónde está
`src/db`
"""

INDICE = """# Índice del código

- `api` — La API HTTP → [`api.md`](api.md)
- `db` — Persistencia → [`db.md`](db.md)
"""

PROYECTO = """# Proyecto

## Qué es el proyecto

Plataforma de reservas de espacios.

- Tipo: web_app
- Etapa: production

## Stack

- Lenguajes: TypeScript, SQL
- Frameworks: Next.js
- Runtimes: Node 20
- Gestores de paquetes: npm

## Cómo se levanta

- `npm run dev`
- Entrypoints: `src/api/main.ts`
- Integraciones: proveedor de pagos sandbox

## Cómo se testea

- `npm test`

## Qué falta saber

- Si el solapamiento se valida en la API o en la base.
"""


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(ruta), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd)] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def _proyecto(con_proyecto_md=True, versionado=True):
    """Un repositorio descartable con su indice del codigo ya escrito."""
    raiz = Path(tempfile.gettempdir()) / ("harness-ctx-" + uuid.uuid4().hex[:8])
    codebase = raiz / "docs" / "codebase"
    _escribir(codebase / "indice.md", INDICE)
    _escribir(codebase / "api.md", FICHA_API)
    _escribir(codebase / "db.md", FICHA_DB)
    _escribir(raiz / "package.json", '{"name":"demo"}\n')
    if con_proyecto_md:
        _escribir(codebase / "proyecto.md", PROYECTO)

    if versionado:
        _git(raiz, "init", "-q")
        _git(raiz, "config", "user.email", "t@t")
        _git(raiz, "config", "user.name", "t")
        _git(raiz, "add", "-A")
        _git(raiz, "commit", "-qm", "inicial")
    return raiz, codebase


def _correr(directorio):
    r = subprocess.run([sys.executable, str(ARMAR), str(directorio)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (r.returncode,
            r.stdout.decode("utf-8", "replace"),
            r.stderr.decode("utf-8", "replace"))


def _contrato(codebase):
    with io.open(str(codebase / SALIDA), encoding="utf-8") as f:
        return json.load(f)


def _bin_falso(mutar):
    """Una copia descartable del bin, con el schema pasado por `mutar`. Devuelve la ruta
    del script que hay que correr.

    🔴 El schema alterado se arma aca y NUNCA sobre comun/schemas/. Romper un archivo
    versionado y restaurarlo en un finally es lo que ya dejo pre-tool-use.py roto en el
    arbol durante 0.13.0: el finally no sobrevive a que maten el proceso. Como
    contexto-armar.py resuelve el schema como un `schemas/` hermano de su propio `bin/`,
    alcanza con copiar los dos scripts al lado de un schema de mentira."""
    falso = Path(tempfile.gettempdir()) / ("harness-ctx-bin-" + uuid.uuid4().hex[:8])
    (falso / "bin").mkdir(parents=True, exist_ok=True)
    (falso / "schemas").mkdir(parents=True, exist_ok=True)
    for origen in (ARMAR, MAPA):
        (falso / "bin" / origen.name).write_bytes(origen.read_bytes())

    esquema = json.loads(Path(_modulo.ruta_schema()).read_text(encoding="utf-8"))
    mutar(esquema)
    _escribir(falso / "schemas" / "project-context.schema.json",
              json.dumps(esquema, ensure_ascii=False, indent=2))
    return falso / "bin" / ARMAR.name


# ── El contrato que se escribe ───────────────────────────────────────────────────

def test_e01_sin_fichas_no_escribe_nada_y_lo_dice(t):
    """E-01 — un directorio sin fichas es un recorrido que no paso por aca. Escribir un
    contrato vacio seria la promesa de que habia algo que mirar."""
    vacio = Path(tempfile.gettempdir()) / ("harness-ctx-vacio-" + uuid.uuid4().hex[:8])
    vacio.mkdir(parents=True, exist_ok=True)
    codigo, salida, _ = _correr(vacio)
    t.igual("E-01: sale con codigo 0", 0, codigo)
    t.igual("E-01: no escribio", False, json.loads(salida)["escrito"])
    t.verdadero("E-01: no hay archivo en disco", not (vacio / SALIDA).exists())


def test_e02_el_contrato_valida_contra_el_schema(t):
    """E-02 — el archivo escrito valida. El script lo comprueba antes de escribir; aca
    se comprueba sobre el archivo que quedo en disco, que es lo que consume un agente."""
    _raiz, codebase = _proyecto()
    codigo, _s, err = _correr(codebase)
    t.igual("E-02: escribio sin error", 0, codigo)
    t.vacio("E-02: sin nada en stderr", err.strip())
    esquema = _modulo.cargar_schema()
    t.igual("E-02: sin errores de validacion", [],
            _modulo.validar(_contrato(codebase), esquema))


def test_e03_dos_corridas_difieren_solo_en_generated_at(t):
    """E-03 — el archivo se versiona: si cada regeneracion cambiara el archivo entero,
    el diff real quedaria tapado adentro del ruido."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    primero = _contrato(codebase)
    _correr(codebase)
    segundo = _contrato(codebase)

    a = json.loads(json.dumps(primero))
    b = json.loads(json.dumps(segundo))
    a["meta"].pop("generated_at")
    b["meta"].pop("generated_at")
    t.igual("E-03: todo lo demas es identico",
            json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
    t.igual("E-03: y el hash no se movio",
            primero["meta"]["context_hash"], segundo["meta"]["context_hash"])


def test_e04_el_context_hash_recomputado_da_lo_mismo(t):
    """E-04 — el hash es sobre el documento sin context_hash y sin generated_at. Un hash
    que no se puede recalcular no sirve para comparar dos contextos."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)
    t.igual("E-04: coincide", doc["meta"]["context_hash"], _modulo.hash_de(doc))
    t.verdadero("E-04: y tiene la forma sha256:...",
                doc["meta"]["context_hash"].startswith("sha256:"))


def test_e05_repo_revision_es_el_head_del_repositorio(t):
    """E-05 — sin la revision real el contrato miente sobre de cuando es."""
    raiz, codebase = _proyecto()
    _correr(codebase)
    head = _git(raiz, "rev-parse", "HEAD").stdout.decode().strip()
    t.igual("E-05: es el HEAD", head, _contrato(codebase)["meta"]["repo_revision"])


def test_e06_sin_repositorio_git_no_escribe_nada(t):
    """E-06 — repo_revision no es opcional en este contrato. Escribirlo igual seria
    fabricar un contrato invalido para no tener que decir que faltaba algo."""
    _raiz, codebase = _proyecto(versionado=False)
    codigo, _s, err = _correr(codebase)
    t.igual("E-06: sale con codigo 1", 1, codigo)
    t.verdadero("E-06: no escribio nada", not (codebase / SALIDA).exists())
    t.contiene("E-06: dice por que", "repo_revision", err)


# ── El validador ─────────────────────────────────────────────────────────────────

def test_e07_un_campo_obligatorio_que_falta_se_nombra(t):
    """E-07 — el error dice cual falta. Un 'no valida' sin el campo obliga a adivinar.

    El escenario afirma tres cosas y la funcion sola alcanza una. Que el script salga
    distinto de 0 y que NO escriba se prueban de punta a punta, sobre el bin de mentira,
    con un `required` que ningun documento puede satisfacer: es la misma distincion que
    la spec ya elevo a escenario aparte en E-08b, y ahi E-07 no tenia companero."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)
    del doc["meta"]["repo_revision"]
    errores = _modulo.validar(doc, _modulo.cargar_schema())
    t.igual("E-07: un solo error", 1, len(errores))
    t.contiene("E-07: nombra el campo", "repo_revision", errores[0])
    t.contiene("E-07: y dice que es obligatorio", "obligatorio", errores[0])

    # sin esto, "no escribio" lo contestaria el archivo que dejo la corrida de arriba
    os.remove(str(codebase / SALIDA))

    def exigir_lo_imposible(esquema):
        esquema["properties"]["meta"]["required"].append("firma_del_escribano")

    r = subprocess.run(
        [sys.executable, str(_bin_falso(exigir_lo_imposible)), str(codebase)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t.igual("E-07: el script sale distinto de 0", 1, r.returncode)
    t.contiene("E-07: y nombra el campo que falta", "firma_del_escribano",
               r.stderr.decode("utf-8", "replace"))
    t.verdadero("E-07: y no escribio", not (codebase / SALIDA).exists())


def test_e07b_enum_y_pattern_tambien_se_verifican(t):
    """E-07b — required solo no alcanza: un campo presente con un valor imposible pasa
    igual de desapercibido que uno ausente."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)
    doc["project_profile"]["project_type"] = "mainframe"
    doc["meta"]["repo_revision"] = "no-es-un-sha"
    juntos = " ".join(_modulo.validar(doc, _modulo.cargar_schema()))
    t.contiene("E-07b: el enum", "mainframe", juntos)
    t.contiene("E-07b: el pattern", "no-es-un-sha", juntos)


def test_e08_una_construccion_no_soportada_falla_ruidosamente(t):
    """E-08 — un validador que ignora lo que no entiende devuelve 'valido' sobre partes
    del documento que nunca miro, y eso viaja con el sello puesto."""
    esquema = _modulo.cargar_schema()
    _modulo.controlar_soporte(esquema)   # el schema real tiene que pasar

    roto = json.loads(json.dumps(esquema))
    roto["properties"]["meta"]["oneOf"] = [{"type": "object"}]
    try:
        _modulo.controlar_soporte(roto)
        t.verdadero("E-08: tendria que haber fallado", False)
    except _modulo.SchemaNoSoportado as e:
        t.contiene("E-08: nombra la construccion", "oneOf", str(e))
        t.contiene("E-08: y donde esta", "meta", str(e))


def test_e08b_el_script_entero_sale_con_codigo_2(t):
    """E-08b — no alcanza con que la funcion levante: el script tiene que traducirlo a
    un codigo de salida distinto del de 'el documento no valida'. Son dos problemas
    distintos y se arreglan en lugares distintos.

    El schema roto se arma en el bin de mentira de `_bin_falso`, que lleva escrito al
    lado por que ese schema nunca se toca sobre comun/schemas/."""
    _raiz, codebase = _proyecto()

    def romper(esquema):
        esquema["properties"]["meta"]["oneOf"] = [{"type": "object"}]

    r = subprocess.run([sys.executable, str(_bin_falso(romper)), str(codebase)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t.igual("E-08b: codigo 2", 2, r.returncode)
    t.contiene("E-08b: lo dice", "oneOf", r.stderr.decode("utf-8", "replace"))
    t.verdadero("E-08b: y no escribio", not (codebase / SALIDA).exists())


def test_e01_refutador_lee_contrato_validacion_fallida_no_pisa_uno_valido(t):
    """E-01 (refutador-lee-contrato) — docs/cambios/dev-refutador-lee-el-contrato/spec.md.

    Una corrida cuya salida no valida no puede tocar un project-context.json valido que
    ya estaba en el directorio: dev-refutador va a leer ese archivo como evidencia, y una
    corrida rota no puede dejarlo a medio escribir ni borrado.

    E-07 y E-08b ya prueban "no escribio" sobre un directorio vacio; lo que faltaba era
    la mitad que importa aca -que una corrida rota no le haga nada al archivo BUENO que
    ya estaba-. armar() nunca llega a escribir() si validar() encuentra errores
    (contexto-armar.py:1030-1038); esto lo prueba de punta a punta.

    🔴 El primer diseño comparaba solo bytes, y harness-spec-refuter lo encontro fragil el
    29-08-2026: con la misma fixture, "exigir_lo_imposible" no cambia nada de lo que
    armar() calcula -mismas fichas, mismo commit-, asi que una reescritura con el bug
    presente produce un documento funcionalmente IGUAL al original, salvo
    meta.generated_at, que tiene resolucion de un segundo. Si las dos corridas caen en el
    mismo segundo de reloj, los bytes coinciden IGUAL aunque el bug este presente, y el
    test pasa por casualidad de timing, no porque el invariante se sostenga. Se suma el
    mtime del archivo en nanosegundos: una reescritura real -pise lo que pise- SIEMPRE
    mueve el mtime a nivel de sistema operativo, y ahi ninguna coincidencia de segundo
    alcanza para tapar el bug."""
    _raiz, codebase = _proyecto()

    codigo_1, _s1, _e1 = _correr(codebase)
    t.igual("E-01 (refutador-lee-contrato): la primera corrida escribe", 0, codigo_1)
    archivo = codebase / SALIDA
    original = archivo.read_bytes()
    mtime_original = archivo.stat().st_mtime_ns

    def exigir_lo_imposible(esquema):
        esquema["properties"]["meta"]["required"].append("firma_del_escribano")

    r = subprocess.run(
        [sys.executable, str(_bin_falso(exigir_lo_imposible)), str(codebase)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t.igual("E-01 (refutador-lee-contrato): la segunda corrida no valida",
            1, r.returncode)
    t.contiene("E-01 (refutador-lee-contrato): y lo dice", "firma_del_escribano",
               r.stderr.decode("utf-8", "replace"))

    despues = archivo.read_bytes()
    t.igual("E-01 (refutador-lee-contrato): el contrato valido queda byte a byte igual",
            original, despues)
    t.igual(
        "E-01 (refutador-lee-contrato): y el mtime no se movio -no hubo una segunda "
        "escritura, coincida o no con la primera en contenido",
        mtime_original, archivo.stat().st_mtime_ns)


# ── Lo que sale de las fichas ────────────────────────────────────────────────────

def test_e09_un_componente_por_ficha_y_una_arista_por_enlace(t):
    """E-09 — las mismas cifras que reporta el mapa sobre el mismo directorio. Si los
    dos contaran distinto, uno de los dos estaria mintiendo y no se sabria cual."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)

    r = subprocess.run([sys.executable, str(MAPA), str(codebase)],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    resumen = json.loads(r.stdout.decode("utf-8"))

    t.igual("E-09: tantos componentes como nodos del mapa",
            resumen["nodos"], len(doc["architecture"]["components"]))
    t.igual("E-09: tantas aristas como el mapa",
            resumen["aristas"], len(doc["architecture"]["dependency_edges"]))
    t.igual("E-09: la arista es api -> db",
            [{"from": "api", "to": "db"}], doc["architecture"]["dependency_edges"])


def test_e10_una_ficha_huerfana_viaja_en_gaps(t):
    """E-10 — la huerfana ya la detecta el mapa; lo que agrega el contrato es que viaje
    adentro, donde la lee un agente que nunca abrio el mapa.html."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    huecos = " ".join(_contrato(codebase)["gaps_and_conflicts"]["missing"])
    t.contiene("E-10: nombra la ficha que nadie enlaza", "api.md", huecos)


def test_e11_cada_ficha_produce_una_fuente(t):
    """E-11 — una afirmacion sin fuente no se puede contrastar despues."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)
    fuentes = {f["source_id"]: f for f in doc["sources"]}
    revision = doc["meta"]["repo_revision"]

    for cid in ("api", "db"):
        sid = "code:%s" % cid
        t.verdadero("E-11: hay fuente para %s" % cid, sid in fuentes)
        t.igual("E-11: %s trae la revision" % cid, revision, fuentes[sid]["revision"])
        t.igual("E-11: %s esta vigente" % cid, "current", fuentes[sid]["status"])

    for c in doc["architecture"]["components"]:
        for ref in c["source_refs"]:
            t.verdadero("E-11: %s referencia una fuente que existe" % c["component_id"],
                        ref in fuentes)


def test_e11b_el_tipo_de_una_fuente_describe_su_location(t):
    """E-11b — el `type` describe el archivo que va en `location`, no la union de todo
    lo que la ficha nombra de paso.

    Es una regresion con nombre: la primera version miraba todas las rutas juntas, y una
    sola mencion de `docs/adr/` adentro de una ficha grande tipaba el modulo entero como
    `adr`. Sobre este repositorio daba once ADRs donde hay ocho, y el `type` no describia
    el `location` que iba al lado — un consumidor que filtrara por tipo abria archivos
    que no eran lo que la etiqueta decia."""
    t.igual("E-11b: una ruta de codigo", "code",
            _modulo._tipo_de_fuente("comun/hooks", "comun-hooks.md"))
    t.igual("E-11b: un .md es documento", "functional_doc",
            _modulo._tipo_de_fuente("README.md", "docs.md"))
    t.igual("E-11b: un ADR de verdad", "adr",
            _modulo._tipo_de_fuente("docs/adr/0001-algo.md", "docs-adr.md"))
    t.igual("E-11b: un lockfile es configuracion", "config",
            _modulo._tipo_de_fuente("terceros/terceros.lock.json", "terceros.md"))
    t.igual("E-11b: los tests", "tests",
            _modulo._tipo_de_fuente("tests/casos", "tests.md"))
    t.igual("E-11b: un contrato de API", "openapi",
            _modulo._tipo_de_fuente("api/openapi.yaml", "api.md"))


def test_e11c_un_bullet_de_prosa_no_se_recorta_al_primer_span(t):
    """E-11c — la otra regresion de la misma pasada. En las secciones de comandos el
    bullet vale por lo que hay entre comillas invertidas; en la prosa de «Qué falta
    saber» ese recorte deja la ruta y tira la frase.

    Con el bug, «Si `docs/codebase/` sigue cubriendo todos los módulos» entraba al
    contrato como `docs/codebase/`, que no es una pregunta abierta: es una ruta."""
    cuerpo = "- Si `docs/codebase/` sigue cubriendo todos los módulos.\n"
    t.igual("E-11c: como comando, vale el span", ["docs/codebase/"],
            _modulo.bullets_sueltos(cuerpo))
    t.igual("E-11c: como prosa, vale la frase entera",
            ["Si docs/codebase/ sigue cubriendo todos los módulos."],
            _modulo.bullets_sueltos(cuerpo, comando=False))


def test_e12_proyecto_md_no_es_un_componente_ni_un_nodo(t):
    """E-12 — es un nombre reservado. Si entrara al grafo seria una huerfana permanente
    en el informe de cada recorrido, y encima se le exigirian cuatro secciones que a
    proposito no tiene."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    ids = [c["component_id"] for c in _contrato(codebase)["architecture"]["components"]]
    t.igual("E-12: los componentes son las fichas de modulo", ["api", "db"], sorted(ids))

    r = subprocess.run([sys.executable, str(MAPA), str(codebase)],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    t.igual("E-12: y el mapa tampoco lo cuenta", 2,
            json.loads(r.stdout.decode("utf-8"))["nodos"])


def test_e12b_proyecto_md_alimenta_el_perfil_y_el_stack(t):
    """E-12b — la otra mitad de E-12: no es un componente, pero no se ignora."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    doc = _contrato(codebase)
    t.igual("E-12b: el tipo", "web_app", doc["project_profile"]["project_type"])
    t.igual("E-12b: la etapa", "production", doc["project_profile"]["lifecycle_stage"])
    t.contiene("E-12b: el proposito", "reservas", doc["project_profile"]["purpose"])
    t.igual("E-12b: los comandos de test", ["npm test"],
            doc["technology"]["test_commands"])
    t.igual("E-12b: el entrypoint", ["src/api/main.ts"],
            doc["architecture"]["entrypoints"])
    t.igual("E-12b: la integracion externa", ["proveedor de pagos sandbox"],
            doc["architecture"]["external_integrations"])
    t.igual("E-12b: la pregunta abierta queda abierta", 1,
            len(doc["gaps_and_conflicts"]["unresolved_questions"]))


def test_e13_sin_proyecto_md_el_hueco_se_declara(t):
    """E-13 — el contrato se escribe igual y dice que falta. Completar el hueco con una
    inferencia lo vuelve indistinguible de un hecho para el que lee despues."""
    _raiz, codebase = _proyecto(con_proyecto_md=False)
    codigo, _s, _e = _correr(codebase)
    t.igual("E-13: escribe igual", 0, codigo)
    doc = _contrato(codebase)
    t.igual("E-13: el perfil dice que falta", "missing",
            doc["project_profile"]["knowledge_status"])
    t.igual("E-13: la tecnologia tambien", "missing",
            doc["technology"]["knowledge_status"])
    t.vacio("E-13: y el proposito queda vacio", doc["project_profile"]["purpose"])
    t.contiene("E-13: el hueco esta declarado", "proyecto.md",
               " ".join(doc["gaps_and_conflicts"]["missing"]))


def test_e13b_los_bloques_sin_modelar_se_declaran(t):
    """E-13b — un consumidor tiene que poder distinguir 'este proyecto no tiene reglas
    de negocio' de 'esta version del contrato todavia no las modela'."""
    _raiz, codebase = _proyecto()
    _correr(codebase)
    huecos = " ".join(_contrato(codebase)["gaps_and_conflicts"]["missing"])
    for bloque in ("business_rules", "interfaces", "identity_and_access",
                   "environments", "quality_landscape"):
        t.contiene("E-13b: declara %s" % bloque, bloque, huecos)


# ── Lo que ya existia y no se rompe ──────────────────────────────────────────────

def test_e14_proyecto_md_no_dispara_hallazgos_del_check(t):
    """E-14 — el check le pediria las cuatro secciones y el indice le pediria una linea.
    Las dos cosas son falsos positivos sobre un archivo bien escrito, y un falso
    positivo es lo que hace que alguien apague el check."""
    raiz, codebase = _proyecto()
    modulo = reglas._cargar(str(CHECK))
    config = {"rutaCodebase": "docs/codebase"}

    evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
              "cwd": str(raiz),
              "tool_input": {"file_path": str(codebase / "proyecto.md")}}
    t.igual("E-14: escribir proyecto.md no da hallazgos", [],
            list(modulo.verificar(evento, str(raiz), config) or []))

    evento_indice = {"hook_event_name": "PostToolUse", "tool_name": "Write",
                     "cwd": str(raiz),
                     "tool_input": {"file_path": str(codebase / "indice.md")}}
    t.igual("E-14: y el indice no lo reclama como ficha sin indexar", [],
            list(modulo.verificar(evento_indice, str(raiz), config) or []))


def test_e15_el_mapa_sale_identico_con_proyecto_md(t):
    """E-15 — el mapa es una pieza terminada. Este cambio le agrega un nombre a una
    exclusion y nada mas: si el dibujo se moviera, lo que se revierte es esa linea."""
    _raiz, codebase = _proyecto(con_proyecto_md=False)
    subprocess.run([sys.executable, str(MAPA), str(codebase)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sin = (codebase / "mapa.html").read_bytes()

    _escribir(codebase / "proyecto.md", PROYECTO)
    subprocess.run([sys.executable, str(MAPA), str(codebase)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    con = (codebase / "mapa.html").read_bytes()

    t.igual("E-15: mapa.html byte a byte igual", len(sin), len(con))
    t.verdadero("E-15: y el contenido tambien", sin == con)


def test_e15b_armar_el_contrato_no_toca_el_mapa_ni_las_fichas(t):
    """E-15b — el otro lado de E-15. El unico archivo que este script escribe es el
    contrato: si el mapa o una ficha se movieran, el recorrido dejaria de ser
    reproducible y nadie sabria cual de los dos pasos lo cambio."""
    _raiz, codebase = _proyecto()
    subprocess.run([sys.executable, str(MAPA), str(codebase)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    antes = {}
    for f in sorted(codebase.iterdir()):
        if f.name != SALIDA and f.is_file():
            antes[f.name] = f.read_bytes()

    _correr(codebase)

    for nombre, contenido in antes.items():
        t.verdadero("E-15b: %s quedo igual" % nombre,
                    (codebase / nombre).read_bytes() == contenido)
    t.verdadero("E-15b: y el contrato si se escribio", (codebase / SALIDA).exists())


# ── El aviso de SessionStart ─────────────────────────────────────────────────────

MARCAS = ("Sin indice del codigo todavia",
          "Hay fichas del codigo sin indice.md",
          "no tiene su project-context.json")


def _session_start(raiz):
    payload = {"session_id": "s", "cwd": str(raiz), "hook_event_name": "SessionStart"}
    r = subprocess.run([sys.executable, str(HOOKS / "session-start.py")],
                       input=json.dumps(payload).encode("utf-8"),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    salida = r.stdout.decode("utf-8", "replace")
    if not salida.strip():
        return ""
    datos = json.loads(salida)
    return (datos.get("hookSpecificOutput") or {}).get("additionalContext", "")


def _lock(raiz, harness):
    _escribir(raiz / ".claude" / "harness.lock.json",
              json.dumps({"harness": harness, "version": "0.0.0"}))
    _escribir(raiz / ".claude" / "harness.config.json", json.dumps({}))


def test_e16_avisa_cuando_el_indice_esta_y_el_contrato_no(t):
    """E-16 — el indice de un recorrido anterior al contrato. Se avisa por AUSENCIA y no
    por antiguedad: cualquier commit cambia HEAD, asi que un aviso de 'quedo viejo'
    saldria en todas las sesiones para siempre y se dejaria de leer."""
    raiz, codebase = _proyecto()
    _lock(raiz, ["comun", "desarrollo"])
    texto = _session_start(raiz)
    t.contiene("E-16: lo nombra", "project-context.json", texto)

    _correr(codebase)
    texto2 = _session_start(raiz)
    t.no_contiene("E-16: con el contrato puesto, se calla", "project-context.json", texto2)
    for marca in MARCAS:
        t.no_contiene("E-16: ninguna otra marca del bloque", marca, texto2)


def test_e16b_sin_desarrollo_no_dice_nada(t):
    """E-16b — un proyecto de solo analisis no tiene codigo que recorrer."""
    raiz, _codebase = _proyecto()
    os.remove(str(_codebase / "indice.md"))
    _lock(raiz, ["comun", "analisis"])
    texto = _session_start(raiz)
    for marca in MARCAS:
        t.no_contiene("E-16b: sin desarrollo, sin aviso", marca, texto)


def test_e17_el_bloque_agrega_a_lo_sumo_una_linea(t):
    """E-17 — los tres estados son excluyentes. Dos lineas sobre el mismo recorrido se
    leen como ruido y se dejan de leer las dos, y con ellas el resto del bloque."""
    casos = {
        "sin nada": (False, False, False),
        "solo fichas": (True, False, False),
        "indice sin contrato": (True, True, False),
        "todo puesto": (True, True, True),
    }
    for nombre, (fichas, indice, contrato) in casos.items():
        raiz, codebase = _proyecto()
        _lock(raiz, ["comun", "desarrollo"])
        if not fichas:
            for f in list(codebase.glob("*.md")):
                os.remove(str(f))
        if not indice and (codebase / "indice.md").exists():
            os.remove(str(codebase / "indice.md"))
        if contrato:
            _correr(codebase)

        lineas = [l for l in _session_start(raiz).splitlines()
                  if any(m in l for m in MARCAS)]
        t.verdadero("E-17 (%s): a lo sumo una linea del bloque" % nombre,
                    len(lineas) <= 1)


# ── Secretos ─────────────────────────────────────────────────────────────────────

def _catalogo():
    return secretos.importar_patrones(
        str(RAIZ / "comun" / "reglas" / "secretos.patrones.json"))


def _bloquea(texto, catalogo):
    h = secretos.buscar_secreto(texto, catalogo)
    return bool(h) and h.get("confianza") == "alta"


def test_e19_el_contrato_versionado_no_lleva_secretos(t):
    """E-19 — el sujeto es el project-context.json de ESTE repositorio, que lo escribio
    un recorrido real y esta versionado. Si un recorrido futuro mete un secreto y alguien
    lo commitea, este test se pone en rojo.

    Va con su control positivo: sin el, un catalogo que no carga da exactamente el mismo
    verde que un contrato limpio."""
    catalogo = _catalogo()
    t.verdadero("E-19: control positivo, el detector encuentra sobre el corpus",
                _bloquea(CORPUS.read_text(encoding="utf-8"), catalogo))

    archivo = CODEBASE_REAL / SALIDA
    # `is_file()` no alcanzaba: el escenario dice "versionado" y un archivo suelto en el
    # arbol -o uno que alguien mande al .gitignore- daba exactamente el mismo verde, sin
    # que nadie pudiera mirar el contrato desde el repositorio. La asercion afirmaba menos
    # que su propio docstring. Lo encontro harness-spec-refuter el 26-08-2026.
    seguido = _git(RAIZ, "ls-files", "--error-unmatch", str(archivo)).returncode == 0
    t.verdadero("E-19: el contrato esta versionado, no suelto en el arbol", seguido)
    if seguido:
        t.verdadero("E-19: sin secreto de confianza alta",
                    not _bloquea(archivo.read_text(encoding="utf-8"), catalogo))
