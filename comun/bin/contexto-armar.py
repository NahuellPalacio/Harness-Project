#!/usr/bin/env python
"""
contexto-armar - el contrato PROJECT_CONTEXT del proyecto.

Lee las fichas que escribio dev-iniciador-code, les suma lo que git sabe del
repositorio, y escribe `project-context.json` al lado del indice.

    python contexto-armar.py <directorio-de-fichas>

El resumen sale como JSON por stdout: si escribio, cuantas fuentes, cuantos componentes,
cuantas aristas y cuantos huecos quedaron declarados. Eso es lo que el recorrido pone en
su reporte.

Por que existe
--------------

El indice del codigo ya contesta "que hay aca". Lo que no contesta -porque es prosa- es
"de que momento del proyecto salio esto". Sin `repo_revision` y sin `context_hash`, dos
agentes que leen el mismo directorio no pueden saber si estan mirando lo mismo, y el dia
que una decision sale mal no hay con que reconstruir con que informacion se tomo.

El reparto
----------

Este script calcula lo que se puede calcular y NO inventa lo demas:

  - `meta` entero, `sources[]`, y `architecture.components` y `dependency_edges`, que
    salen del grafo de enlaces entre fichas.
  - `project_profile` y `technology` los escribe el agente en `proyecto.md`, con
    encabezados fijos, y aca solo se serializan. Un script puede ver el lockfile; no
    puede saber cual de los tres scripts es el que se corre de verdad.

Si `proyecto.md` no esta, el contrato se escribe igual con esos campos vacios y el hueco
declarado en `gaps_and_conflicts`. Un dato que falta se dice; no se completa con una
inferencia que despues nadie distingue de un hecho.

Tres cosas que este script NO hace
----------------------------------

  - **No toca el mapa.** No escribe, no mueve y no regenera `mapa.html` ni ninguna ficha.
    Lo unico que escribe es `project-context.json`. Reusa `leer_fichas` y `armar_grafo`
    de `mapa-codigo.py` cargando el modulo, sin copiarlas y sin moverlas: el guion del
    nombre impide un `import` normal, asi que se carga por ruta -el mismo patron de
    `tests/correr.py`-.

  - **No infiere aristas.** El nodo es la ficha y la arista es el enlace, igual que en el
    mapa. Una dependencia que ninguna ficha enlaza no aparece: se arregla en la ficha.

  - **No usa nada de afuera.** Biblioteca estandar. Por eso el validador de JSON Schema
    es un interprete de un subconjunto -type, properties, required, items, enum,
    pattern- que LEE el archivo de schema en vez de repetirlo en Python. Si el schema
    usa una construccion que no soporta, falla y la nombra: un validador que ignora en
    silencio lo que no entiende devuelve "valido" sobre documentos que nunca miro, y eso
    es peor que no validar, porque viaja con el sello puesto.

El layout es determinista a proposito: el archivo se versiona. `generated_at` queda
FUERA del hash por el mismo motivo -si el reloj entrara, dos corridas sobre el mismo
codigo darian hashes distintos y el campo dejaria de servir para lo unico que sirve-.

Codigos de salida: 0 escribio o no habia nada que hacer · 1 el documento no valida o el
proyecto no esta versionado · 2 el schema usa algo que este validador no interpreta.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime

SALIDA = "project-context.json"
PROYECTO = "proyecto.md"
SCHEMA = os.path.join("..", "schemas", "project-context.schema.json")
VERSION_SCHEMA = "project-context/1.1"

# Los bloques que el schema v1.1 todavia no modela. Van declarados adentro del
# contrato: un consumidor que no los encuentre tiene que poder distinguir "este
# proyecto no tiene reglas de negocio" de "esta version del contrato todavia no las
# modela". interfaces, identity_and_access y environments dejaron esta lista en v1.1:
# ya estan modelados, aunque salgan vacios con su propio knowledge_status `missing`.
SIN_MODELAR = ("business_rules", "quality_landscape")

# Los encabezados de `proyecto.md`, exactos y con tilde. El agente los escribe asi.
S_QUE_ES = "Qué es el proyecto"
S_STACK = "Stack"
S_LEVANTA = "Cómo se levanta"
S_TESTEA = "Cómo se testea"
S_INTERFACES = "Interfaces"
S_IDENTIDAD = "Identidad y acceso"
S_AMBIENTES = "Ambientes"
S_FALTA = "Qué falta saber"

# Los encabezados de una ficha de modulo. Solo se leen dos: la primera contesta que hace
# el componente y la ultima donde vive.
F_QUE_ES = "Qué es"
F_DONDE = "Dónde está"

# Un bullet con etiqueta: `- Lenguajes: Python, PowerShell`. La etiqueta no puede tener
# comillas invertidas ni dos puntos, y eso es lo que deja pasar de largo a un bullet que
# es un comando -`- \`git -C x rev-parse\`` no tiene etiqueta- o una ruta de Windows.
ETIQUETADO = re.compile(r"^[-*]\s+([^:`\n]{1,40}?):\s*(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
SPAN = re.compile(r"`([^`\n]+)`")
ENCABEZADO = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Lo que se lee como "no hay nada". El agente escribe una raya cuando busco y no habia.
VACIOS = frozenset(("", "-", "--", "---", "—", "–", "n/a", "na", "ninguno", "ninguna",
                    "nada", "no hay", "sin datos"))

TIPOS_PROYECTO = ("web_app", "api", "worker", "monorepo", "library", "cli", "unknown")
ETAPAS = ("mvp", "production", "legacy", "unknown")

# Archivos que son contrato por si mismos y merecen una entrada propia en `sources`. No
# se indexa el repositorio entero: el contrato es un modelo sintetizado, no un dump, y
# los archivos originales siguen siendo referenciables cuando alguien los necesite.
CONTRATOS = (
    ("openapi", ("openapi.yaml", "openapi.yml", "openapi.json",
                 "swagger.yaml", "swagger.yml", "swagger.json")),
    ("config", ("package.json", "composer.json", "pom.xml", "requirements.txt",
                "pyproject.toml", "go.mod", "cargo.toml", "build.gradle")),
)
TOPE_ADR = 50


# ── El mapa, sin tocarlo ─────────────────────────────────────────────────────────

def cargar_mapa():
    """Devuelve el modulo `mapa-codigo.py` cargado por ruta.

    El guion del nombre impide `import mapa_codigo`, y renombrarlo seria mover una pieza
    terminada para acomodar a una nueva. Se carga como lo hace tests/correr.py.
    """
    import importlib.util

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapa-codigo.py")
    if not os.path.isfile(ruta):
        raise RuntimeError(
            "no esta mapa-codigo.py al lado de este script (%s). Sin el no hay grafo, y "
            "sin grafo no hay architecture: no se escribe un contrato a medias." % ruta)
    spec = importlib.util.spec_from_file_location("mapa_codigo", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ── git ──────────────────────────────────────────────────────────────────────────

def _git(directorio, *args):
    """La salida de un git, o None si no se pudo. Nunca levanta."""
    try:
        r = subprocess.run(["git", "-C", directorio] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace").strip()


def datos_del_repo(directorio):
    """(raiz, revision, fecha_de_la_revision) o (None, None, None).

    La fecha sale del commit, no del reloj, y es la que llevan las fuentes en
    `discovered_at`. Es a proposito: el archivo se versiona, y si cada elemento cargara
    la hora de la corrida, dos pasadas sobre el mismo commit darian documentos distintos
    y `context_hash` dejaria de contestar si dos consumidores miran lo mismo. Lo que el
    contrato puede garantizar de verdad es "a esta revision", no "a esta hora".

    El unico campo que si lleva reloj es `meta.generated_at`, y por eso es el unico que
    queda afuera del hash.
    """
    raiz = _git(directorio, "rev-parse", "--show-toplevel")
    revision = _git(directorio, "rev-parse", "HEAD")
    if not raiz or not revision:
        return None, None, None
    fecha = _git(directorio, "log", "-1", "--format=%cI", revision)
    return os.path.normpath(raiz), revision, fecha


def archivos_versionados(raiz):
    salida = _git(raiz, "ls-files")
    if not salida:
        return []
    return [l.strip() for l in salida.splitlines() if l.strip()]


# ── Leer markdown ────────────────────────────────────────────────────────────────

def seccion(texto, titulo):
    """El cuerpo de la seccion `## titulo`, o '' si no esta."""
    encabezados = list(ENCABEZADO.finditer(texto))
    for i, m in enumerate(encabezados):
        if m.group(1).strip().lower() != titulo.lower():
            continue
        desde = m.end()
        hasta = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(texto)
        return texto[desde:hasta].strip()
    return ""


def _limpio(valor):
    v = " ".join((valor or "").split())
    return "" if v.strip().lower() in VACIOS else v


def etiquetas(cuerpo):
    """{etiqueta en minuscula: valor} de los bullets con etiqueta."""
    salida = {}
    for linea in (cuerpo or "").splitlines():
        m = ETIQUETADO.match(linea.strip())
        if m:
            salida[m.group(1).strip().lower()] = _limpio(m.group(2))
    return salida


def bullets_sueltos(cuerpo, comando=True):
    """Los bullets SIN etiqueta, en orden.

    `comando=True` para las secciones de comandos: el bullet es `npm test` y lo que vale
    es lo de adentro de las comillas invertidas, no la oracion que lo rodea.

    `comando=False` para la prosa -los huecos de "Que falta saber"-, donde recortar al
    primer span deja el archivo que se nombra y tira la frase entera. Ese fue el bug:
    "Si `docs/codebase/` sigue cubriendo todos los modulos" entraba al contrato como
    "docs/codebase/", que no es una pregunta abierta, es una ruta.
    """
    salida = []
    for linea in (cuerpo or "").splitlines():
        linea = linea.strip()
        if ETIQUETADO.match(linea):
            continue
        m = BULLET.match(linea)
        if not m:
            continue
        texto = m.group(1).strip()
        if comando:
            spans = SPAN.findall(texto)
            texto = spans[0].strip() if spans else _limpio(texto)
        else:
            texto = _limpio(texto.replace("`", ""))
        if texto:
            salida.append(texto)
    return salida


def lista(valor):
    """Un valor etiquetado partido en items. 'Python, PowerShell' son dos."""
    valor = _limpio(valor)
    if not valor:
        return []
    partes = [p.strip(" `") for p in re.split(r"[,;]| · ", valor)]
    return [p for p in partes if p and p.lower() not in VACIOS]


def prosa(cuerpo):
    """El texto de la seccion sin sus bullets, en una linea."""
    lineas = [l for l in (cuerpo or "").splitlines()
              if l.strip() and not BULLET.match(l.strip())]
    return " ".join(" ".join(lineas).split())


def etiquetas_repetidas(cuerpo):
    """[(etiqueta en minuscula, valor)] de CADA bullet etiquetado, en orden.

    Es lo que `etiquetas()` no puede dar: ahi un `- Rol: admin` seguido de
    `- Rol: operador` se pisan porque el resultado es un dict con una entrada por
    etiqueta. Reusa el mismo regex ETIQUETADO; solo cambia como se junta el resultado.
    """
    salida = []
    for linea in (cuerpo or "").splitlines():
        m = ETIQUETADO.match(linea.strip())
        if not m:
            continue
        valor = _limpio(m.group(2))
        if valor:
            salida.append((m.group(1).strip().lower(), valor))
    return salida


_SEPARADOR_TABLA = re.compile(r"^:?-+:?$")


def tabla_markdown(cuerpo):
    """Una tabla markdown -> lista de dicts, una entrada por fila, clave por columna.

    Encabezado en la primera linea que empieza con `|`, la fila separadora `|---|...|`
    justo despues, y cero o mas filas de datos. Sin esas dos primeras lineas no hay
    tabla que leer y devuelve `[]`. Generica: no sabe nada de interfaces ni de
    ambientes, solo de columnas.
    """
    filas = [l.strip() for l in (cuerpo or "").splitlines() if l.strip().startswith("|")]
    if len(filas) < 2:
        return []

    def celdas(linea):
        return [c.strip() for c in linea.strip("|").split("|")]

    separador = celdas(filas[1])
    if not separador or not all(_SEPARADOR_TABLA.match(c) for c in separador):
        return []

    encabezado = [c.lower() for c in celdas(filas[0])]
    salida = []
    for linea in filas[2:]:
        valores = celdas(linea)
        salida.append({nombre: (valores[i] if i < len(valores) else "")
                       for i, nombre in enumerate(encabezado)})
    return salida


# ── proyecto.md ──────────────────────────────────────────────────────────────────

def leer_proyecto(directorio):
    """Lo que escribio el agente, o None si la ficha no esta."""
    ruta = os.path.join(directorio, PROYECTO)
    if not os.path.isfile(ruta):
        return None
    with io.open(ruta, encoding="utf-8") as f:
        return f.read()


def perfil_y_stack(texto, nombre_repo, huecos):
    """(project_profile, technology, entrypoints, integraciones, preguntas).

    Sin `proyecto.md` devuelve los bloques vacios con knowledge_status `missing` y deja
    el hueco anotado. El contrato se escribe igual: lo que falta se declara.
    """
    if texto is None:
        huecos.append(
            "project_profile y technology: no hay %s en el indice del codigo, asi que "
            "el proposito del proyecto, su stack y sus comandos de build y test no "
            "estan modelados." % PROYECTO)
        perfil = {
            "project_id": nombre_repo,
            "project_name": nombre_repo,
            "project_type": "unknown",
            "purpose": "",
            "lifecycle_stage": "unknown",
            "knowledge_status": "missing",
        }
        tecnologia = {
            "languages": [], "frameworks": [], "runtimes": [], "package_managers": [],
            "build_commands": [], "test_commands": [], "knowledge_status": "missing",
        }
        return perfil, tecnologia, [], [], []

    que_es = seccion(texto, S_QUE_ES)
    stack = seccion(texto, S_STACK)
    levanta = seccion(texto, S_LEVANTA)
    testea = seccion(texto, S_TESTEA)
    falta = seccion(texto, S_FALTA)

    et_que_es = etiquetas(que_es)
    et_stack = etiquetas(stack)
    et_levanta = etiquetas(levanta)

    tipo = (et_que_es.get("tipo") or "unknown").lower().replace(" ", "_")
    if tipo not in TIPOS_PROYECTO:
        huecos.append("project_profile.project_type: `%s` no es uno de los tipos del "
                      "contrato, queda en unknown." % tipo)
        tipo = "unknown"

    etapa = (et_que_es.get("etapa") or "unknown").lower()
    if etapa not in ETAPAS:
        huecos.append("project_profile.lifecycle_stage: `%s` no es una de las etapas "
                      "del contrato, queda en unknown." % etapa)
        etapa = "unknown"

    proposito = prosa(que_es)
    perfil = {
        "project_id": nombre_repo,
        "project_name": _limpio(et_que_es.get("nombre")) or nombre_repo,
        "project_type": tipo,
        "purpose": proposito,
        "lifecycle_stage": etapa,
        "knowledge_status": "confirmed" if proposito else "missing",
    }
    if not proposito:
        huecos.append("project_profile.purpose: %s no dice para que existe el proyecto."
                      % PROYECTO)

    tecnologia = {
        "languages": lista(et_stack.get("lenguajes")),
        "frameworks": lista(et_stack.get("frameworks")),
        "runtimes": lista(et_stack.get("runtimes")),
        "package_managers": lista(et_stack.get("gestores de paquetes")),
        "build_commands": bullets_sueltos(levanta),
        "test_commands": bullets_sueltos(testea),
        "knowledge_status": "confirmed",
    }
    if not tecnologia["test_commands"]:
        tecnologia["knowledge_status"] = "inferred"
        huecos.append("technology.test_commands: %s no nombra ningun comando de test."
                      % PROYECTO)

    entrypoints = lista(et_levanta.get("entrypoints") or et_levanta.get("entrypoint"))
    integraciones = lista(et_levanta.get("integraciones")
                          or et_levanta.get("servicios externos"))
    preguntas = bullets_sueltos(falta, comando=False)
    return perfil, tecnologia, entrypoints, integraciones, preguntas


# ── Interfaces, identidad y acceso, ambientes ────────────────────────────────────

def _span_o_texto(celda):
    """El primer span entre backticks de la celda, o el texto limpio si no hay ninguno."""
    spans = SPAN.findall(celda or "")
    if spans:
        return spans[0].strip()
    return _limpio(celda)


def interfaces_de_proyecto(texto, component_ids, fuentes_contrato, huecos, conflictos):
    """El bloque `interfaces` desde `## Interfaces` de `proyecto.md`.

    Una fila de la tabla por interfaz. `contrato` no viaja tal cual: se resuelve contra
    las fuentes que ya detecto `fuentes_de_contrato()` -mismo criterio que le da su
    source_id a un `openapi.yaml` commiteado- y si ninguna matchea, las dos referencias
    quedan vacias en vez de repetir la ruta.
    """
    cuerpo = seccion(texto or "", S_INTERFACES)
    filas = tabla_markdown(cuerpo)
    if not filas:
        huecos.append(
            "interfaces: %s no declara ninguna interfaz bajo `## %s`."
            % (PROYECTO, S_INTERFACES))
        return {"items": [], "knowledge_status": "missing"}

    openapi = [f for f in fuentes_contrato if f.get("type") == "openapi"]
    validos = set(component_ids)

    vistos = set()
    items = []
    for fila in filas:
        iid = fila.get("id") or ""
        if not iid:
            continue
        if iid in vistos:
            conflictos.append(
                "interfaces: `%s` aparece mas de una vez bajo `## %s`; se conserva la "
                "primera fila y se descarta la repetida." % (iid, S_INTERFACES))
            continue
        vistos.add(iid)

        contrato = _span_o_texto(fila.get("contrato", ""))
        ref = ""
        if contrato:
            for fuente in openapi:
                base = os.path.basename(fuente["location"]).lower()
                if base == contrato.lower() or fuente["location"].lower() == contrato.lower():
                    ref = fuente["source_id"]
                    break

        componente = _span_o_texto(fila.get("componente", ""))
        owning = ""
        if componente:
            if componente in validos:
                owning = componente
            else:
                conflictos.append(
                    "interfaces: `%s` declara owning_component `%s`, que no es "
                    "ninguna ficha existente; el campo queda vacio." % (iid, componente))

        items.append({
            "interface_id": iid,
            "type": _limpio(fila.get("tipo", "")),
            "path": _limpio(fila.get("ruta", "")),
            "auth_requirements": _limpio(fila.get("auth", "")),
            "request_contract_ref": ref,
            "response_contract_ref": ref,
            "owning_component": owning,
        })

    return {"items": items, "knowledge_status": "confirmed" if openapi else "inferred"}


def identidad_de_proyecto(texto, huecos):
    """El bloque `identity_and_access` desde `## Identidad y acceso` de `proyecto.md`.

    Bullets etiquetados con etiquetas que se repiten -`Rol:` puede aparecer muchas
    veces-, por eso usa `etiquetas_repetidas()` y no `etiquetas()`: esta ultima pisa
    cada repeticion porque junta en un dict con una entrada por etiqueta.
    """
    cuerpo = seccion(texto or "", S_IDENTIDAD)
    pares = etiquetas_repetidas(cuerpo)

    auth_model = ""
    roles = []
    test_principals = []
    access_by_environment = []
    vista_alguna = False
    for etiqueta, valor in pares:
        if etiqueta == "modelo de autenticación":
            auth_model = valor
            vista_alguna = True
        elif etiqueta == "rol":
            roles.append(valor)
            vista_alguna = True
        elif etiqueta == "usuario de prueba":
            test_principals.append({"ref": valor})
            vista_alguna = True
        elif etiqueta == "acceso":
            access_by_environment.append(valor)
            vista_alguna = True

    if not vista_alguna:
        huecos.append(
            "identity_and_access: %s no declara nada bajo `## %s`."
            % (PROYECTO, S_IDENTIDAD))

    return {
        "auth_model": auth_model,
        "roles": roles,
        "test_principals": test_principals,
        "access_by_environment": access_by_environment,
        "knowledge_status": "confirmed" if vista_alguna else "missing",
    }


# El orden importa: es la prioridad exacta con la que un substring gana. "produccion"
# sin tilde porque se compara contra el texto ya pasado por _sin_acentos().
_REGLAS_KIND = (
    (("calidad",), "qa"),
    (("produccion interna", "produccion dmz", "dmz", "produccion", "prd"), "prd"),
    (("homolog", "hml"), "hml"),
    (("desa", "desarrollo", "dev"), "dev"),
    (("qa", "testing", "pruebas"), "qa"),
    (("local",), "local"),
)


def _sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "")
                  if not unicodedata.combining(c))


def _kind_de(celda_tipo):
    plano = _sin_acentos(celda_tipo).lower()
    for patrones, kind in _REGLAS_KIND:
        if any(p in plano for p in patrones):
            return kind
    return "other"


def _contenidos_versionados(raiz, versionados):
    """El texto de cada archivo versionado, ignorando el que no abre como texto.

    Se lee una sola vez y se reusa para buscar cada URL de `base_urls`: una URL se
    busca literal, como substring, contra el contenido completo del arbol.
    """
    contenidos = []
    for ruta in versionados:
        try:
            with io.open(os.path.join(raiz, ruta), encoding="utf-8") as f:
                contenidos.append(f.read())
        except (OSError, UnicodeDecodeError, ValueError):
            continue
    return contenidos


def ambientes_de_proyecto(texto, raiz, versionados, huecos, conflictos):
    """El bloque `environments` desde `## Ambientes` de `proyecto.md`.

    `kind` normaliza `tipo` por substring -ver `_REGLAS_KIND`-. Un ambiente `prd`
    siempre sale con `allowed_mutations: read-only`, sin importar lo que declare la
    tabla; la discrepancia, si la hay, se anota en `conflictos`. `base_urls` filtra
    contra el contenido de cada archivo versionado: la URL que no aparece en ninguno
    se descarta y se anota en `huecos`.
    """
    cuerpo = seccion(texto or "", S_AMBIENTES)
    filas = tabla_markdown(cuerpo)
    if not filas:
        huecos.append(
            "environments: %s no declara ningun ambiente bajo `## %s`."
            % (PROYECTO, S_AMBIENTES))
        return {"items": [], "knowledge_status": "missing"}

    contenidos = _contenidos_versionados(raiz, versionados)

    items = []
    for fila in filas:
        eid = fila.get("id") or ""
        if not eid:
            continue
        kind = _kind_de(fila.get("tipo", ""))

        base_urls = []
        for url in SPAN.findall(fila.get("urls") or ""):
            url = url.strip()
            if not url:
                continue
            if any(url in c for c in contenidos):
                base_urls.append(url)
            else:
                huecos.append(
                    "environments: la URL `%s` de `%s` no aparece en ningun archivo "
                    "versionado del repositorio; se descarta de base_urls."
                    % (url, eid))

        mutaciones = _limpio(fila.get("mutaciones", ""))
        if kind == "prd":
            if mutaciones and mutaciones.lower() != "read-only":
                conflictos.append(
                    "environments: `%s` es kind prd y %s declaraba allowed_mutations "
                    "`%s`; se escribe `read-only`." % (eid, PROYECTO, mutaciones))
            mutaciones = "read-only"

        items.append({
            "environment_id": eid,
            "kind": kind,
            "base_urls": base_urls,
            "allowed_mutations": mutaciones,
            "data_policy": _limpio(fila.get("datos", "")),
        })

    return {"items": items, "knowledge_status": "confirmed"}


# ── Las fichas de modulo ─────────────────────────────────────────────────────────

def _tipo_de_fuente(location, nombre_ficha):
    """El tipo describe lo que hay en `location`, y nada mas.

    🔴 Antes miraba la union de TODAS las rutas de la ficha, y una sola mencion de
    `docs/adr/` adentro de una ficha grande tipaba el modulo entero como `adr`. Paso con
    tres fichas de este repositorio -`docs`, `normativa` y `terceros`-, y el resultado era
    un contrato que declaraba once ADRs donde el repositorio tiene ocho. Peor que el
    numero: el `type` no describia el `location` que iba al lado, asi que un consumidor
    que filtrara por tipo leia archivos que no eran lo que decia la etiqueta.
    """
    plano = (location or nombre_ficha).lower().replace("\\", "/")
    base = plano.rsplit("/", 1)[-1]

    if re.search(r"(^|/)(adr|adrs|decisions)(/|$)", plano):
        return "adr"
    if "openapi" in base or "swagger" in base:
        return "openapi"
    if re.search(r"(^|/)(tests?|specs?|__tests__)(/|$)", plano):
        return "tests"
    if base.endswith(".md"):
        return "functional_doc"
    if base.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg")) or "lock" in base:
        return "config"
    if plano.startswith("docs/") or "/docs/" in plano:
        return "functional_doc"
    return "code"


def componentes_y_fuentes(fichas, sello, revision):
    """(components[], sources[], important_paths[]) desde las fichas del indice."""
    componentes = []
    fuentes = []
    caminos = []

    for nombre, titulo, texto in fichas:
        cid = os.path.splitext(nombre)[0]
        rutas = SPAN.findall(seccion(texto, F_DONDE))
        rutas = [r.strip() for r in rutas if r.strip()]
        caminos.extend(rutas)

        sid = "code:%s" % cid
        location = rutas[0] if rutas else nombre
        componentes.append({
            "component_id": cid,
            "name": titulo,
            "responsibility": prosa(seccion(texto, F_QUE_ES)),
            "source_refs": [sid],
        })
        fuentes.append({
            "source_id": sid,
            "type": _tipo_de_fuente(location, nombre),
            "location": location,
            "revision": revision,
            "discovered_at": sello,
            "authority_scope": "implementación observada del módulo",
            "status": "current",
        })

    vistos = set()
    unicos = []
    for c in caminos:
        if c not in vistos:
            vistos.add(c)
            unicos.append(c)
    return componentes, fuentes, unicos


def fuentes_de_contrato(versionados, sello, revision, huecos):
    """Las fuentes que son contrato por si mismas: OpenAPI, manifiestos, ADRs."""
    fuentes = []
    for tipo, nombres in CONTRATOS:
        for ruta in versionados:
            if os.path.basename(ruta).lower() in nombres:
                fuentes.append({
                    "source_id": "%s:%s" % (tipo, ruta),
                    "type": tipo,
                    "location": ruta,
                    "revision": revision,
                    "discovered_at": sello,
                    "authority_scope": "contrato declarado",
                    "status": "current",
                })

    adrs = sorted(r for r in versionados
                  if re.search(r"(^|/)(adr|adrs|decisions)/", r.lower()))
    if len(adrs) > TOPE_ADR:
        huecos.append("sources: hay %d ADRs y se modelaron las primeras %d. Las %d "
                      "restantes no estan en el contrato."
                      % (len(adrs), TOPE_ADR, len(adrs) - TOPE_ADR))
        adrs = adrs[:TOPE_ADR]
    for ruta in adrs:
        fuentes.append({
            "source_id": "adr:%s" % ruta,
            "type": "adr",
            "location": ruta,
            "revision": revision,
            "discovered_at": sello,
            "authority_scope": "decisión vigente de arquitectura",
            "status": "current",
        })
    return fuentes


# ── El schema, interpretado ──────────────────────────────────────────────────────

class SchemaNoSoportado(Exception):
    """El schema crecio y este validador no. Se avisa; no se da por valido."""


ANOTACIONES = frozenset(("$schema", "$id", "title", "description", "examples",
                         "default", "deprecated"))
VALIDACIONES = frozenset(("type", "properties", "required", "items", "enum", "pattern"))
TIPOS = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "integer": int, "number": (int, float),
}


def ruta_schema():
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), SCHEMA))


def cargar_schema():
    ruta = ruta_schema()
    if not os.path.isfile(ruta):
        raise SchemaNoSoportado(
            "no esta el schema en %s. El contrato no se escribe sin poder validarlo."
            % ruta)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def controlar_soporte(esquema, ruta="$"):
    """Recorre el schema entero ANTES de validar y falla ante lo que no interpreta.

    Es la mitad que importa. Un validador que se saltea las palabras que no conoce
    devuelve "valido" sobre partes del documento que nunca miro, y el documento sigue
    viaje con el sello puesto.
    """
    if not isinstance(esquema, dict):
        raise SchemaNoSoportado("%s: se esperaba un objeto de schema" % ruta)

    for clave in esquema:
        if clave in ANOTACIONES or clave in VALIDACIONES:
            continue
        raise SchemaNoSoportado(
            "%s: el schema usa `%s`, que este validador no interpreta. Se amplia el "
            "validador, no se afloja el schema. Soportado: %s"
            % (ruta, clave, ", ".join(sorted(VALIDACIONES))))

    for nombre, sub in (esquema.get("properties") or {}).items():
        controlar_soporte(sub, "%s.%s" % (ruta, nombre))
    if "items" in esquema:
        controlar_soporte(esquema["items"], "%s[]" % ruta)


def validar(dato, esquema, ruta="$"):
    """Lista de errores. Vacia es valido."""
    errores = []
    tipo = esquema.get("type")

    if tipo:
        esperado = TIPOS.get(tipo)
        if esperado is None:
            raise SchemaNoSoportado("%s: tipo `%s` desconocido" % (ruta, tipo))
        # bool es subclase de int en Python y colarse como `integer` seria un falso verde.
        if isinstance(dato, bool) and tipo in ("integer", "number"):
            return ["%s: se esperaba %s y vino un booleano" % (ruta, tipo)]
        if not isinstance(dato, esperado):
            return ["%s: se esperaba %s y vino %s"
                    % (ruta, tipo, type(dato).__name__)]

    if "enum" in esquema and dato not in esquema["enum"]:
        errores.append("%s: `%s` no esta entre los valores permitidos (%s)"
                       % (ruta, dato, ", ".join(str(v) for v in esquema["enum"])))

    if "pattern" in esquema and isinstance(dato, str):
        if not re.search(esquema["pattern"], dato):
            errores.append("%s: `%s` no cumple el patron %s"
                           % (ruta, dato, esquema["pattern"]))

    if isinstance(dato, dict):
        for req in esquema.get("required") or []:
            if req not in dato:
                errores.append("%s.%s: falta y es obligatorio" % (ruta, req))
        for nombre, sub in (esquema.get("properties") or {}).items():
            if nombre in dato:
                errores.extend(validar(dato[nombre], sub, "%s.%s" % (ruta, nombre)))

    if isinstance(dato, list) and "items" in esquema:
        for i, item in enumerate(dato):
            errores.extend(validar(item, esquema["items"], "%s[%d]" % (ruta, i)))

    return errores


# ── El hash ──────────────────────────────────────────────────────────────────────

def canonico(doc):
    """El documento sin `context_hash` ni `generated_at`, ordenado y compacto.

    Es lo unico sobre lo que se calcula el hash. El reloj queda afuera para que dos
    corridas sobre el mismo codigo den el mismo hash: si no, el campo no puede contestar
    la pregunta para la que existe -si dos consumidores estan mirando lo mismo-.
    """
    copia = json.loads(json.dumps(doc))
    copia.get("meta", {}).pop("context_hash", None)
    copia.get("meta", {}).pop("generated_at", None)
    return json.dumps(copia, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def hash_de(doc):
    return "sha256:" + hashlib.sha256(canonico(doc).encode("utf-8")).hexdigest()


def hash_de_fichas(directorio):
    """sha256 sobre el conjunto ordenado de .md del directorio, nombre y contenido."""
    h = hashlib.sha256()
    try:
        nombres = sorted(n for n in os.listdir(directorio)
                         if n.lower().endswith(".md"))
    except OSError:
        nombres = []
    for nombre in nombres:
        ruta = os.path.join(directorio, nombre)
        if not os.path.isfile(ruta):
            continue
        h.update(nombre.encode("utf-8"))
        h.update(b"\0")
        with io.open(ruta, "rb") as f:
            h.update(f.read())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


# ── La version del harness ───────────────────────────────────────────────────────

def version_initiator(raiz):
    lock = os.path.join(raiz, ".claude", "harness.lock.json")
    if os.path.isfile(lock):
        try:
            with io.open(lock, encoding="utf-8-sig") as f:
                v = (json.load(f) or {}).get("version")
            if isinstance(v, str) and v.strip():
                return "harness/" + v.strip()
        except (OSError, ValueError):
            pass
    archivo = os.path.join(raiz, "VERSION")
    if os.path.isfile(archivo):
        try:
            with io.open(archivo, encoding="utf-8-sig") as f:
                v = f.read().strip()
            if v:
                return "harness/" + v
        except OSError:
            pass
    return "harness/desconocida"


# ── Armar ────────────────────────────────────────────────────────────────────────

def armar(directorio):
    """(documento, resumen). Levanta RuntimeError si no se puede armar."""
    directorio = os.path.abspath(directorio)
    mapa = cargar_mapa()

    fichas = mapa.leer_fichas(directorio)
    if not fichas:
        return None, {
            "escrito": False,
            "motivo": "no hay fichas en %s: el recorrido no paso por aca todavia"
                      % directorio,
            "fuentes": 0, "componentes": 0, "aristas": 0, "huecos": 0,
        }

    raiz, revision, fecha_revision = datos_del_repo(directorio)
    if raiz is None:
        raise RuntimeError(
            "%s no esta adentro de un repositorio git. El contrato lleva repo_revision "
            "y sin eso no se puede consumir: es imposible explicar despues con que "
            "informacion decidio un agente. No se escribe nada." % directorio)

    ahora = datetime.now().astimezone().replace(microsecond=0).isoformat()
    # `sello` es lo que llevan las fuentes: la fecha del commit, no la de la corrida.
    sello = fecha_revision or ahora
    nombre_repo = re.sub(r"[^a-z0-9-]+", "-", os.path.basename(raiz).lower()).strip("-")
    nombre_repo = nombre_repo or "proyecto"

    huecos = []
    conflictos = []
    nodos, aristas = mapa.armar_grafo(fichas)
    componentes, fuentes, caminos = componentes_y_fuentes(fichas, sello, revision)
    versionados = archivos_versionados(raiz)
    fuentes_contrato = fuentes_de_contrato(versionados, sello, revision, huecos)
    fuentes.extend(fuentes_contrato)

    texto_proyecto = leer_proyecto(directorio)
    perfil, tecnologia, entrypoints, integraciones, preguntas = perfil_y_stack(
        texto_proyecto, nombre_repo, huecos)

    component_ids = [c["component_id"] for c in componentes]
    interfaces = interfaces_de_proyecto(texto_proyecto, component_ids, fuentes_contrato,
                                        huecos, conflictos)
    identidad = identidad_de_proyecto(texto_proyecto, huecos)
    ambientes = ambientes_de_proyecto(texto_proyecto, raiz, versionados, huecos,
                                      conflictos)

    con_entrada = set(d for _o, d in aristas)
    for n in sorted(nodos):
        if n not in con_entrada:
            huecos.append(
                "architecture: la ficha `%s` no la enlaza ninguna otra. O falta el "
                "enlace en la ficha que la usa, o es un modulo que no usa nadie." % n)

    for bloque in SIN_MODELAR:
        huecos.append("%s: el schema %s todavia no modela este bloque. Su ausencia no "
                      "significa que el proyecto no lo tenga."
                      % (bloque, VERSION_SCHEMA))

    doc = {
        "meta": {
            "schema_version": VERSION_SCHEMA,
            "context_id": "ctx_%s_%s" % (nombre_repo, revision[:4]),
            "context_hash": "sha256:" + "0" * 64,
            "generated_at": ahora,
            "initiator_version": version_initiator(raiz),
            "repo_revision": revision,
            "docs_revision": hash_de_fichas(directorio),
        },
        "project_profile": perfil,
        "sources": fuentes,
        "technology": tecnologia,
        "architecture": {
            "components": componentes,
            "entrypoints": entrypoints,
            "dependency_edges": [{"from": os.path.splitext(o)[0],
                                  "to": os.path.splitext(d)[0]} for o, d in aristas],
            "external_integrations": integraciones,
            "important_paths": caminos,
        },
        "interfaces": interfaces,
        "identity_and_access": identidad,
        "environments": ambientes,
        "gaps_and_conflicts": {
            "missing": huecos,
            "conflicts": conflictos,
            "stale_sources": [],
            "unresolved_questions": preguntas,
        },
    }
    doc["meta"]["context_hash"] = hash_de(doc)

    resumen = {
        "escrito": True,
        "salida": os.path.join(directorio, SALIDA),
        "context_id": doc["meta"]["context_id"],
        "repo_revision": revision,
        "context_hash": doc["meta"]["context_hash"],
        "fuentes": len(fuentes),
        "componentes": len(componentes),
        "aristas": len(aristas),
        "huecos": len(huecos),
        "preguntas_abiertas": len(preguntas),
        "perfil": perfil["knowledge_status"],
    }
    return doc, resumen


def escribir(directorio, doc):
    salida = os.path.join(os.path.abspath(directorio), SALIDA)
    texto = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    with io.open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    return salida


def main():
    ap = argparse.ArgumentParser(
        description="Arma el contrato PROJECT_CONTEXT desde las fichas del indice.")
    ap.add_argument("directorio",
                    help="el directorio de las fichas, normalmente docs/codebase")
    args = ap.parse_args()

    try:
        esquema = cargar_schema()
        controlar_soporte(esquema)
    except SchemaNoSoportado as e:
        sys.stderr.write("schema: %s\n" % e)
        return 2

    try:
        doc, resumen = armar(args.directorio)
    except SchemaNoSoportado as e:
        sys.stderr.write("schema: %s\n" % e)
        return 2
    except RuntimeError as e:
        sys.stderr.write("%s\n" % e)
        return 1

    if doc is None:
        sys.stdout.write(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
        return 0

    errores = validar(doc, esquema)
    if errores:
        sys.stderr.write(
            "el contrato no valida contra %s y por eso NO se escribio:\n" % VERSION_SCHEMA)
        for e in errores:
            sys.stderr.write("  - %s\n" % e)
        return 1

    escribir(args.directorio, doc)
    sys.stdout.write(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
