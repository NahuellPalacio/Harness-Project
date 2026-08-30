# Paso 4 del contrato PROJECT_CONTEXT: `interfaces`, `identity_and_access` y
# `environments`. Escenarios E-01 a E-17 de
# docs/cambios/interfaces-identidad-ambientes/spec.md.
#
# E-18 NO esta aca: su sujeto es una corrida de dev-iniciador-code y se verifica por
# lectura, ADR-0009 -ningun test puede obligar a un modelo a describir bien un
# proyecto-. E-17 tampoco esta aca: es "E-18 del cambio anterior con el valor
# cambiado" segun la propia spec, y ya vive en tests/casos/14-contexto-instalador.ps1
# -la version que ese caso afirma se actualizo a project-context/1.1 ahi mismo-.
#
# Van a un archivo nuevo y no a 13_contexto.py -que ya usa E-01 a E-19 para el
# contrato de los pasos 1 y 2- porque mandarlos ahi hace que "E-03" signifique dos
# escenarios distintos en el mismo archivo. Cada titulo lleva el slug "(paso-4)".
#
# Los fixtures, los helpers (_escribir, _git, _correr, _contrato, FICHA_API, FICHA_DB,
# INDICE) y el estilo de las funciones test_eNN_... copian tests/casos/13_contexto.py.
import io
import json
import re
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
CODEBASE_REAL = RAIZ / "docs" / "codebase"

SALIDA = "project-context.json"

_modulo = reglas._cargar(str(ARMAR))


# ── Un proyecto descartable ──────────────────────────────────────────────────────
# Mismas fichas que 13_contexto.py: `api` depende de `db`, asi que `component_ids`
# siempre trae los dos y `owning_component: api` (E-07) siempre matchea.

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

PROYECTO_BASE = """# Proyecto

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
"""


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with io.open(str(ruta), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd)] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def _proyecto_md(interfaces=None, identidad=None, ambientes=None):
    """El proyecto.md del paso 2 mas las tres secciones nuevas, en el orden que fija
    la spec -Interfaces, Identidad y acceso, Ambientes- entre "## Cómo se testea" y
    "## Qué falta saber". Los encabezados salen de las constantes reales del script,
    no de una copia: si algun dia cambian, este fixture no se desincroniza en silencio.

    `None` omite la seccion ENTERA -header incluido-. Es lo que necesita E-08, "sin
    seccion `## Interfaces`". Un string, aunque sea vacio, deja el header puesto.
    """
    texto = PROYECTO_BASE
    if interfaces is not None:
        texto += "\n## %s\n\n%s\n" % (_modulo.S_INTERFACES, interfaces)
    if identidad is not None:
        texto += "\n## %s\n\n%s\n" % (_modulo.S_IDENTIDAD, identidad)
    if ambientes is not None:
        texto += "\n## %s\n\n%s\n" % (_modulo.S_AMBIENTES, ambientes)
    texto += ("\n## %s\n\n- Si el solapamiento se valida en la API o en la base.\n"
             % _modulo.S_FALTA)
    return texto


def _proyecto(interfaces=None, identidad=None, ambientes=None, con_proyecto_md=True,
             versionado=True, versionar_proyecto_md=True, archivos_extra=None):
    """Un repositorio descartable con su indice del codigo ya escrito, como en
    13_contexto.py.

    `versionar_proyecto_md=False` escribe `proyecto.md` DESPUES del commit, asi que
    `git ls-files` nunca lo lista. Lo necesita E-13: `_contenidos_versionados()` lee
    el disco de cada archivo que git YA sigue, sin mirar si el contenido cambio desde
    el commit -asi que un `proyecto.md` trackeado "encuentra" cualquier URL que el
    mismo escriba en su propia tabla de Ambientes, y las dos mitades del escenario
    -la URL que si esta en un archivo versionado, la que no esta en ninguno- dejan
    de poder distinguirse.
    """
    raiz = Path(tempfile.gettempdir()) / ("harness-ctx4-" + uuid.uuid4().hex[:8])
    codebase = raiz / "docs" / "codebase"
    _escribir(codebase / "indice.md", INDICE)
    _escribir(codebase / "api.md", FICHA_API)
    _escribir(codebase / "db.md", FICHA_DB)
    _escribir(raiz / "package.json", '{"name":"demo"}\n')
    for ruta_rel, contenido in (archivos_extra or {}).items():
        _escribir(raiz / ruta_rel, contenido)

    if con_proyecto_md and versionar_proyecto_md:
        _escribir(codebase / "proyecto.md",
                 _proyecto_md(interfaces, identidad, ambientes))

    if versionado:
        _git(raiz, "init", "-q")
        _git(raiz, "config", "user.email", "t@t")
        _git(raiz, "config", "user.name", "t")
        _git(raiz, "add", "-A")
        _git(raiz, "commit", "-qm", "inicial")

    if con_proyecto_md and not versionar_proyecto_md:
        _escribir(codebase / "proyecto.md",
                 _proyecto_md(interfaces, identidad, ambientes))

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


# ── Fixtures de las tres secciones nuevas, reusadas entre escenarios ────────────

INTERFACES_OK = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | http | POST /api/v2/reservas | bearer JWT | - | api |
"""

IDENTIDAD_OK = ("- Modelo de autenticación: OpenID Connect contra Keycloak\n"
                "- Rol: admin\n")

AMBIENTES_OK = """| id | tipo | urls | mutaciones | datos |
|---|---|---|---|---|
| qa-main | Calidad | `https://qa.ejemplo.gob.ar` | read-write | create test records |
"""


# ── El schema v1.1 ───────────────────────────────────────────────────────────────

def test_e01_paso4_schema_version_1_0_no_pasa(t):
    """E-01 (paso-4) — meta.schema_version `project-context/1.0` no valida contra el
    schema v1.1: el enum lo rechaza y el error nombra el campo."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    _correr(codebase)
    doc = _contrato(codebase)
    doc["meta"]["schema_version"] = "project-context/1.0"
    errores = " ".join(_modulo.validar(doc, _modulo.cargar_schema()))
    t.contiene("E-01 (paso-4): el enum nombra el campo", "schema_version", errores)
    t.contiene("E-01 (paso-4): y rechaza el valor viejo",
              "project-context/1.0", errores)


def _claves_de_schema(nodo, huecos, ruta="$"):
    """Recorre el JSON del schema entero por su cuenta -sin llamar a
    controlar_soporte()- y junta las claves que no son ninguna de las seis que el
    interprete soporta ni una anotacion.

    No es un recorrido generico de "todo dict, toda lista": una clave `properties`
    abre un mapa cuyas CLAVES son nombres de propiedad -no palabras del vocabulario
    del schema-, y ahi lo unico que hay que validar es cada VALOR, no las claves del
    mapa. Confundir las dos cosas hace que el propio nombre de un campo del contrato
    -`meta`, `schema_version`- se lea como si fuera una palabra no soportada, que fue
    el primer bug de esta funcion. `items` en cambio abre un unico sub-schema.
    """
    if not isinstance(nodo, dict):
        return
    for clave, valor in nodo.items():
        if clave not in _modulo.VALIDACIONES and clave not in _modulo.ANOTACIONES:
            huecos.append("%s.%s" % (ruta, clave))
        if clave == "properties" and isinstance(valor, dict):
            for prop, sub in valor.items():
                _claves_de_schema(sub, huecos, "%s.%s" % (ruta, prop))
        elif clave == "items":
            _claves_de_schema(valor, huecos, "%s[]" % ruta)


def test_e02_paso4_schema_solo_usa_las_seis_palabras(t):
    """E-02 (paso-4) — el schema v1.1 no usa, en NINGUNA rama, una palabra fuera de
    type, properties, required, items, enum, pattern (o una anotacion)."""
    esquema = json.loads(Path(_modulo.ruta_schema()).read_text(encoding="utf-8"))
    huecos = []
    _claves_de_schema(esquema, huecos)
    t.igual("E-02 (paso-4): sin construcciones no soportadas en ninguna rama",
            [], huecos)


_ANCLA_ARMAR = re.compile(r"\n( *)doc, resumen = armar\(args\.directorio\)\n")


def _bin_falso_sin_bloque(bloque):
    """Una copia descartable del bin real -NUNCA sobre comun/-, con el codigo fuente
    parcheado para borrar `doc[bloque]` justo despues de armar() y antes de validar().

    Es la unica forma de ejercitar de punta a punta que el schema real rechaza un
    documento al que de verdad le falta uno de los tres bloques: `armar()` sobre el
    arbol real jamas los omite -los tres bloques son objetos con su knowledge_status,
    nunca ausentes-, asi que la unica manera de que el SCRIPT intente escribir un
    documento sin uno es borrarlo justo antes de que el propio script lo valide.

    Sigue el mismo patron que `_bin_falso()` de 13_contexto.py: el schema que viaja
    con la copia es el REAL, sin mutar -aca lo que cambia es el codigo, no el schema-.
    """
    falso = Path(tempfile.gettempdir()) / ("harness-ctx4-bin-" + uuid.uuid4().hex[:8])
    (falso / "bin").mkdir(parents=True, exist_ok=True)
    (falso / "schemas").mkdir(parents=True, exist_ok=True)

    fuente = ARMAR.read_text(encoding="utf-8")
    m = _ANCLA_ARMAR.search(fuente)
    if not m:
        raise AssertionError(
            "el anzuelo de E-03 (paso-4) no matcheo contexto-armar.py: "
            "cambio la firma de armar() en main()?")
    indent = m.group(1)
    insercion = ("%sif doc is not None and %r in doc:\n"
                "%s    del doc[%r]\n" % (indent, bloque, indent, bloque))
    fuente = fuente[:m.end()] + insercion + fuente[m.end():]
    _escribir(falso / "bin" / ARMAR.name, fuente)
    _escribir(falso / "bin" / MAPA.name, MAPA.read_text(encoding="utf-8"))

    esquema = json.loads(Path(_modulo.ruta_schema()).read_text(encoding="utf-8"))
    _escribir(falso / "schemas" / "project-context.schema.json",
             json.dumps(esquema, ensure_ascii=False, indent=2))
    return falso / "bin" / ARMAR.name


def test_e03_paso4_los_tres_bloques_son_required(t):
    """E-03 (paso-4) — sacando CUALQUIERA de los tres bloques nuevos de un documento
    valido, el script sale con codigo 1 y nombra el bloque que falta. Son tres casos."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    for bloque in ("interfaces", "identity_and_access", "environments"):
        # Aislar cada iteracion: si una escribiera el archivo por error, la siguiente
        # tiene que poder verlo -no heredar un "no escribio" falso del archivo previo.
        (codebase / SALIDA).unlink(missing_ok=True)
        r = subprocess.run(
            [sys.executable, str(_bin_falso_sin_bloque(bloque)), str(codebase)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = r.stderr.decode("utf-8", "replace")
        t.igual("E-03 (paso-4): sin %s, sale codigo 1" % bloque, 1, r.returncode)
        t.contiene("E-03 (paso-4): y nombra %s" % bloque, bloque, err)
        t.contiene("E-03 (paso-4): como obligatorio (%s)" % bloque, "obligatorio", err)
        t.verdadero("E-03 (paso-4): y no escribio (%s)" % bloque,
                    not (codebase / SALIDA).exists())


# ── Interfaces ────────────────────────────────────────────────────────────────────

INTERFACES_E04 = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | http | POST /api/v2/reservas | bearer JWT | - | api |
| reservas | http | GET /api/v2/reservas | bearer JWT | - | api |
"""


def test_e04_paso4_interfaces_id_duplicado(t):
    """E-04 (paso-4) — dos filas con el mismo interface_id: se conserva la primera,
    se descarta la segunda, y la colision se anota en gaps_and_conflicts.conflicts[]."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_E04, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    codigo, _s, _e = _correr(codebase)
    t.igual("E-04 (paso-4): escribe igual", 0, codigo)
    doc = _contrato(codebase)
    items = doc["interfaces"]["items"]
    t.igual("E-04 (paso-4): una sola entrada para el id repetido", 1, len(items))
    t.igual("E-04 (paso-4): se conserva la primera fila",
            "POST /api/v2/reservas", items[0]["path"])
    t.contiene("E-04 (paso-4): la colision queda anotada", "reservas",
              " ".join(doc["gaps_and_conflicts"]["conflicts"]))


INTERFACES_E05 = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | soap | POST /api/v2/reservas | bearer JWT | - | api |
"""


def test_e05_paso4_interfaces_type_invalido_con_interfaz_real(t):
    """E-05 (paso-4) — un `type` fuera de http|graphql|event|webhook|cli no se
    escribe. Se prueba sobre una fixture CON al menos una interfaz: sobre items:[]
    vacio el enunciado seria vacuamente verdadero."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_E05, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    doc, _resumen = _modulo.armar(str(codebase))
    t.verdadero("E-05 (paso-4): la fixture tiene al menos una interfaz",
                len(doc["interfaces"]["items"]) >= 1)
    errores = " ".join(_modulo.validar(doc, _modulo.cargar_schema()))
    t.contiene("E-05 (paso-4): el enum invalido se nombra", "soap", errores)

    codigo, _s, err = _correr(codebase)
    t.igual("E-05 (paso-4): el script no escribe un documento invalido", 1, codigo)
    t.contiene("E-05 (paso-4): y lo dice por stderr", "soap", err)
    t.verdadero("E-05 (paso-4): y no dejo el archivo", not (codebase / SALIDA).exists())


OPENAPI_YAML = "openapi: 3.0.0\ninfo:\n  title: demo\n  version: '1'\npaths: {}\n"

INTERFACES_E06 = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | http | POST /api/v2/reservas | bearer JWT | `openapi.yaml` | api |
"""


def test_e06_paso4_interfaces_contrato_resuelve_a_source_id(t):
    """E-06 (paso-4) — con un openapi.yaml COMMITEADO en la fixture,
    request_contract_ref de la interfaz que lo nombra es el source_id que
    fuentes_de_contrato() ya le dio, no una ruta repetida."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_E06, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK,
                                archivos_extra={"openapi.yaml": OPENAPI_YAML})
    _correr(codebase)
    doc = _contrato(codebase)
    fuentes_openapi = [f["source_id"] for f in doc["sources"] if f["type"] == "openapi"]
    t.igual("E-06 (paso-4): la fuente openapi existe", ["openapi:openapi.yaml"],
            fuentes_openapi)
    item = doc["interfaces"]["items"][0]
    t.igual("E-06 (paso-4): request_contract_ref es el source_id",
            "openapi:openapi.yaml", item["request_contract_ref"])
    t.igual("E-06 (paso-4): y response_contract_ref tambien",
            "openapi:openapi.yaml", item["response_contract_ref"])
    t.igual("E-06 (paso-4): con openapi detectado, knowledge_status confirmed",
            "confirmed", doc["interfaces"]["knowledge_status"])


INTERFACES_E07 = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | http | POST /api/v2/reservas | bearer JWT | - | api |
| pagos | http | POST /api/v2/pagos | bearer JWT | - | billing |
"""


def test_e07_paso4_owning_component_existente_e_inexistente(t):
    """E-07 (paso-4) — la MISMA fixture lleva las dos mitades: un owning_component
    que existe se conserva; uno que no existe queda vacio y la discrepancia se anota
    en gaps_and_conflicts.conflicts[]."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_E07, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    _correr(codebase)
    doc = _contrato(codebase)
    por_id = {it["interface_id"]: it for it in doc["interfaces"]["items"]}
    t.igual("E-07 (paso-4): componente existente se conserva", "api",
            por_id["reservas"]["owning_component"])
    t.igual("E-07 (paso-4): componente inexistente queda vacio", "",
            por_id["pagos"]["owning_component"])
    conflictos = " ".join(doc["gaps_and_conflicts"]["conflicts"])
    t.contiene("E-07 (paso-4): la discrepancia nombra la interfaz", "pagos", conflictos)
    t.contiene("E-07 (paso-4): y el componente que no existe", "billing", conflictos)


def test_e08_paso4_sin_seccion_interfaces_el_bloque_no_se_omite(t):
    """E-08 (paso-4) — sin `## Interfaces` en proyecto.md, el bloque viaja igual: la
    clave presente, items: [], knowledge_status: missing, y una linea en
    gaps_and_conflicts.missing[]."""
    _raiz, codebase = _proyecto(interfaces=None, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    codigo, _s, _e = _correr(codebase)
    t.igual("E-08 (paso-4): escribe igual", 0, codigo)
    doc = _contrato(codebase)
    t.igual("E-08 (paso-4): items vacio", [], doc["interfaces"]["items"])
    t.igual("E-08 (paso-4): knowledge_status missing",
            "missing", doc["interfaces"]["knowledge_status"])
    t.contiene("E-08 (paso-4): el hueco esta declarado", "Interfaces",
              " ".join(doc["gaps_and_conflicts"]["missing"]))


# ── Identidad y acceso ───────────────────────────────────────────────────────────

PROHIBIDAS_PASO4 = ("password", "token", "secret", "credential", "cookie")


def _nombres_de_propiedad(nodo):
    """Todos los nombres de propiedad -claves adentro de cualquier `properties`- que
    aparecen en cualquier rama de `nodo`, recorriendo TODO el sub-arbol del schema."""
    salida = []
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if clave == "properties" and isinstance(valor, dict):
                for prop, sub in valor.items():
                    salida.append(prop)
                    salida.extend(_nombres_de_propiedad(sub))
            else:
                salida.extend(_nombres_de_propiedad(valor))
    elif isinstance(nodo, list):
        for item in nodo:
            salida.extend(_nombres_de_propiedad(item))
    return salida


def test_e09_paso4_ningun_campo_es_una_credencial(t):
    """E-09 (paso-4) — identity_and_access tiene auth_model, roles[], test_principals[],
    access_by_environment[] y knowledge_status, y NINGUNA propiedad del schema, en
    ninguna rama de interfaces/identity_and_access/environments, se llama password,
    token, secret, credential ni cookie. Es una inspeccion del schema, no un test de
    contenido: que no QUEPA una credencial no lo prueba ningun test."""
    esquema = json.loads(Path(_modulo.ruta_schema()).read_text(encoding="utf-8"))
    identidad = esquema["properties"]["identity_and_access"]["properties"]
    for campo in ("auth_model", "roles", "test_principals",
                 "access_by_environment", "knowledge_status"):
        t.verdadero("E-09 (paso-4): identity_and_access tiene `%s`" % campo,
                    campo in identidad)

    for bloque in ("interfaces", "identity_and_access", "environments"):
        nombres = [n.lower() for n in
                  _nombres_de_propiedad(esquema["properties"][bloque])]
        for prohibida in PROHIBIDAS_PASO4:
            t.verdadero("E-09 (paso-4): %s no tiene una propiedad `%s`"
                        % (bloque, prohibida), prohibida not in nombres)


SECRETO_ALTA = "AKIA1234567890ABCDEF"

INTERFACES_E10 = """| id | tipo | ruta | auth | contrato | componente |
|---|---|---|---|---|---|
| reservas | http | POST /api/v2/reservas | Bearer %s | - | api |
""" % SECRETO_ALTA

IDENTIDAD_E10 = ("- Modelo de autenticación: OpenID Connect contra Keycloak\n"
                 "- Usuario de prueba: qa-admin -- token %s\n" % SECRETO_ALTA)

AMBIENTES_E10 = """| id | tipo | urls | mutaciones | datos |
|---|---|---|---|---|
| qa-main | Calidad | - | read-write | acceso con %s |
""" % SECRETO_ALTA


def _catalogo_secretos():
    return secretos.importar_patrones(
        str(RAIZ / "comun" / "reglas" / "secretos.patrones.json"))


def _bloquea(texto, catalogo):
    h = secretos.buscar_secreto(texto, catalogo)
    return bool(h) and h.get("confianza") == "alta"


def test_e10_paso4_secretos_en_los_tres_bloques_y_control_sobre_el_repo(t):
    """E-10 (paso-4) — sobre una fixture cuyos tres bloques nuevos llevan cadenas con
    forma de credencial, el detector de secretos.patrones.json las encuentra con
    confianza alta. El control positivo es la FIXTURE, no este repositorio: aca los
    tres bloques reales salen vacios o casi -no hay APIs, ni modelo de auth, ni
    ambientes reales-, y escanear tres bloques vacios pasaria el dia que se escribe y
    pasaria para siempre."""
    catalogo = _catalogo_secretos()
    t.verdadero("E-10 (paso-4): control positivo, el patron se reconoce aislado",
                _bloquea(SECRETO_ALTA, catalogo))

    _raiz, codebase = _proyecto(interfaces=INTERFACES_E10, identidad=IDENTIDAD_E10,
                                ambientes=AMBIENTES_E10)
    _correr(codebase)
    doc = _contrato(codebase)
    for bloque in ("interfaces", "identity_and_access", "environments"):
        texto = json.dumps(doc[bloque], ensure_ascii=False)
        t.verdadero("E-10 (paso-4): %s tiene un secreto de confianza alta" % bloque,
                    _bloquea(texto, catalogo))

    archivo_real = CODEBASE_REAL / SALIDA
    if archivo_real.is_file():
        limpio = not _bloquea(archivo_real.read_text(encoding="utf-8"), catalogo)
    else:
        limpio = True   # nada que controlar todavia
    t.verdadero(
        "E-10 (paso-4): docs/codebase/project-context.json real, sin secretos", limpio)


# ── Ambientes ────────────────────────────────────────────────────────────────────

def test_e11_paso4_kind_normaliza_por_substring(t):
    """E-11 (paso-4) — la tabla de normalizacion de kind completa: los cinco kind
    conocidos del microformato mas el caso other. environment_id conserva el nombre
    original tal cual en todos los casos."""
    esperado = [
        ("Calidad", "qa"),
        ("Producción Interna", "prd"),
        ("Producción DMZ", "prd"),
        ("DESA", "dev"),
        ("Desarrollo", "dev"),
        ("Homologación", "hml"),
        ("Local", "local"),
        ("Sandbox Raro", "other"),
    ]
    filas = "\n".join("| %s | %s | - | read-write | - |" % (nombre, nombre)
                      for nombre, _kind in esperado)
    ambientes = ("| id | tipo | urls | mutaciones | datos |\n"
                "|---|---|---|---|---|\n" + filas + "\n")
    _raiz, codebase = _proyecto(interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK,
                                ambientes=ambientes)
    _correr(codebase)
    doc = _contrato(codebase)
    por_id = {it["environment_id"]: it for it in doc["environments"]["items"]}
    for nombre, kind in esperado:
        t.igual("E-11 (paso-4): `%s` -> %s" % (nombre, kind),
                kind, por_id[nombre]["kind"])
        t.igual("E-11 (paso-4): `%s` conserva su environment_id" % nombre,
                nombre, por_id[nombre]["environment_id"])


AMBIENTES_E12 = """| id | tipo | urls | mutaciones | datos |
|---|---|---|---|---|
| prd | Producción | - | read-write | - |
"""


def test_e12_paso4_ambiente_prd_fuerza_read_only(t):
    """E-12 (paso-4) — un ambiente kind prd sale con allowed_mutations read-only
    AUNQUE proyecto.md declare otra cosa, y la discrepancia queda en conflicts[]
    nombrando el ambiente."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_E12)
    _correr(codebase)
    doc = _contrato(codebase)
    item = doc["environments"]["items"][0]
    t.igual("E-12 (paso-4): kind es prd", "prd", item["kind"])
    t.igual("E-12 (paso-4): allowed_mutations forzado a read-only",
            "read-only", item["allowed_mutations"])
    conflictos = " ".join(doc["gaps_and_conflicts"]["conflicts"])
    t.contiene("E-12 (paso-4): el conflicto nombra el ambiente", "prd", conflictos)
    t.contiene("E-12 (paso-4): y lo que la tabla declaraba", "read-write", conflictos)


AMBIENTES_E13 = ("| id | tipo | urls | mutaciones | datos |\n"
                 "|---|---|---|---|---|\n"
                 "| qa-main | Calidad | `https://qa.ejemplo.gob.ar` "
                 "`https://no-existe.ejemplo.gob.ar` | read-write | - |\n")


def test_e13_paso4_base_urls_solo_lleva_lo_versionado(t):
    """E-13 (paso-4) — de las dos URLs de la fila, la que aparece en un archivo
    versionado entra a base_urls; la que no aparece en ningun lado se descarta y su
    ausencia se declara en gaps_and_conflicts.missing[]."""
    _raiz, codebase = _proyecto(
        interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK, ambientes=AMBIENTES_E13,
        versionar_proyecto_md=False,
        archivos_extra={"docs/notas-ambientes.md":
                       "Ver tambien https://qa.ejemplo.gob.ar para mas detalle.\n"})
    _correr(codebase)
    doc = _contrato(codebase)
    item = doc["environments"]["items"][0]
    t.igual("E-13 (paso-4): solo la URL versionada entra a base_urls",
            ["https://qa.ejemplo.gob.ar"], item["base_urls"])
    huecos = " ".join(doc["gaps_and_conflicts"]["missing"])
    t.contiene("E-13 (paso-4): el hueco nombra el ambiente", "qa-main", huecos)
    t.contiene("E-13 (paso-4): y la URL descartada",
              "https://no-existe.ejemplo.gob.ar", huecos)


# ── Lo que ya existia y no se rompe ──────────────────────────────────────────────

def test_e14_paso4_missing_declara_solo_los_dos_bloques_sin_modelar(t):
    """E-14 (paso-4) — gaps_and_conflicts.missing[] declara EXACTAMENTE dos bloques
    no modelados -business_rules y quality_landscape- y ninguno de los tres nuevos,
    sobre una fixture cuyos tres bloques nuevos SI tienen contenido. Se cuentan las
    DECLARACIONES de bloque, no las entradas de missing[] -que ademas lleva la ficha
    huerfana de la fixture, que no es una declaracion de bloque."""
    _raiz, codebase = _proyecto(interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK,
                                ambientes=AMBIENTES_OK)
    _correr(codebase)
    doc = _contrato(codebase)
    huecos = doc["gaps_and_conflicts"]["missing"]
    declaraciones = [h for h in huecos if "todavia no modela este bloque" in h]
    t.igual("E-14 (paso-4): exactamente dos bloques declarados sin modelar",
            2, len(declaraciones))
    juntos = " ".join(declaraciones)
    t.contiene("E-14 (paso-4): business_rules esta declarado", "business_rules", juntos)
    t.contiene("E-14 (paso-4): quality_landscape esta declarado",
              "quality_landscape", juntos)
    for bloque in ("interfaces", "identity_and_access", "environments"):
        t.no_contiene("E-14 (paso-4): %s NO se declara sin modelar" % bloque,
                      bloque, juntos)


AMBIENTES_E15 = ("| id | tipo | urls | mutaciones | datos |\n"
                "|---|---|---|---|---|\n"
                "| qa-main | Calidad | `https://qa.aparece-despues.ejemplo.gob.ar` "
                "| read-write | - |\n")


def test_e15_paso4_el_hash_cambia_si_cambia_environments_sin_tocar_proyecto_md(t):
    """E-15 (paso-4) — meta.context_hash cambia cuando cambia el bloque `environments`
    calculado, y no solo cuando cambian los bytes de proyecto.md.

    `meta.docs_revision` hashea TODOS los .md de docs/codebase/, proyecto.md incluido
    -ver hash_de_fichas()-, asi que reescribir proyecto.md entre dos corridas mueve el
    hash igual sin importar si armar() sella el context_hash antes o despues de sumar
    los tres bloques nuevos: hicimos exactamente esa mutacion -los tres bloques
    reemplazados por objetos vacios, fijos, sin conexion con lo parseado- y el hash
    siguio cambiando igual. Un escenario que no distingue esas dos causas no prueba
    nada sobre el orden del sellado, que es lo que este escenario dice proteger.

    Por eso proyecto.md queda IDENTICO entre las dos corridas -mismos bytes, docs_revision
    fijo- y lo que cambia es el contenido de un archivo versionado FUERA de
    docs/codebase/: la URL de la tabla de Ambientes no aparece en ningun archivo
    versionado en la primera corrida -se descarta de base_urls, environments cambia-, y
    aparece en la segunda -entra a base_urls, environments vuelve a cambiar-. Ninguna
    otra pieza del documento se mueve entre las dos corridas."""
    # versionar_proyecto_md=False: si no, proyecto.md se encuentra A SI MISMO -la URL
    # vive en su propia tabla de Ambientes, y _contenidos_versionados() lo lee como
    # cualquier otro archivo versionado- y la primera corrida ya la daria por
    # encontrada, sin que notas-ambientes.md tuviera que ver.
    _raiz, codebase = _proyecto(
        interfaces=INTERFACES_OK, identidad=IDENTIDAD_OK, ambientes=AMBIENTES_E15,
        versionar_proyecto_md=False,
        archivos_extra={"docs/notas-ambientes.md": "Todavia no hay nada que ver aca.\n"})
    _correr(codebase)
    primero = _contrato(codebase)
    t.igual("E-15 (paso-4): primera corrida, la URL no aparece en ningun lado y se cae",
            [], primero["environments"]["items"][0]["base_urls"])

    # docs_revision depende SOLO de docs/codebase/; notas-ambientes.md vive afuera, asi
    # que reescribirlo sin volver a commitear no mueve ni docs_revision ni repo_revision.
    _escribir(_raiz / "docs" / "notas-ambientes.md",
             "Ahora si: https://qa.aparece-despues.ejemplo.gob.ar esta documentada.\n")
    _correr(codebase)
    segundo = _contrato(codebase)

    t.igual("E-15 (paso-4): docs_revision no se movio -proyecto.md no cambio",
            primero["meta"]["docs_revision"], segundo["meta"]["docs_revision"])
    t.igual("E-15 (paso-4): repo_revision tampoco -no hubo commit nuevo",
            primero["meta"]["repo_revision"], segundo["meta"]["repo_revision"])
    t.igual("E-15 (paso-4): segunda corrida, la URL ahora si aparece",
            ["https://qa.aparece-despues.ejemplo.gob.ar"],
            segundo["environments"]["items"][0]["base_urls"])
    t.verdadero(
        "E-15 (paso-4): con docs_revision Y repo_revision fijos, el hash igual cambio "
        "-la unica diferencia posible es el environments ya calculado",
        primero["meta"]["context_hash"] != segundo["meta"]["context_hash"])


def test_e16_paso4_enlaces_rotos_en_secciones_nuevas(t):
    """E-16 (paso-4) — un [[wiki]] o un enlace relativo a una ficha que no existe,
    adentro de una de las tres secciones nuevas, SI dispara hallazgo de
    dev-codebase-forma.py; una seccion que enlaza una ficha hermana real, no."""
    modulo = reglas._cargar(str(CHECK))
    config = {"rutaCodebase": "docs/codebase"}

    def _hallazgos(identidad):
        raiz, codebase = _proyecto(identidad=identidad, ambientes=AMBIENTES_OK)
        evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
                 "cwd": str(raiz),
                 "tool_input": {"file_path": str(codebase / "proyecto.md")}}
        return list(modulo.verificar(evento, str(raiz), config) or [])

    con_wikilink = _hallazgos(
        "- Modelo de autenticación: OpenID Connect contra Keycloak\n\n"
        "Ver [[Ambiente legado]] para mas contexto.\n")
    t.igual("E-16 (paso-4): el [[wiki]] dispara un hallazgo", 1, len(con_wikilink))
    t.contiene("E-16 (paso-4): y nombra el motivo", "wiki", con_wikilink[0].lower())

    con_enlace_roto = _hallazgos(
        "- Modelo de autenticación: OpenID Connect contra Keycloak\n\n"
        "Ver [detalle](no-existe.md) para mas contexto.\n")
    t.igual("E-16 (paso-4): el enlace relativo roto dispara un hallazgo",
            1, len(con_enlace_roto))
    t.contiene("E-16 (paso-4): y nombra la ficha que falta",
              "no-existe.md", con_enlace_roto[0])

    con_ficha_real = _hallazgos(
        "- Modelo de autenticación: OpenID Connect contra Keycloak\n\n"
        "Ver [api](api.md) para mas detalle.\n")
    t.igual("E-16 (paso-4): enlazar una ficha hermana real no dispara nada",
            [], con_ficha_real)
