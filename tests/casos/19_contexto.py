# Context Resolution: de una clave de Jira a un TaskContext.
#
# Escenarios E-01 a E-31 de docs/cambios/contexto-de-tarea/spec.md. E-32 y E-33 son del
# instalador y viven en tests/casos/19-contexto-tarea-instalador.ps1.
#
# Ningun test sale a la red: Jira y GitLab son un servidor falso que contesta por ruta, el
# mismo mecanismo que 18_integraciones. markitdown tampoco se invoca nunca -se simula su
# presencia y su ausencia-, que es lo unico honesto: la maquina que corre la suite puede
# tenerlo o no, y el test tiene que decir lo mismo en las dos.
import io
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

sys.path.insert(0, str(BIN))
from contexto import documentos as c_documentos       # noqa: E402
from contexto import ensamblador as c_ensamblador     # noqa: E402
from contexto import limpieza                         # noqa: E402
from contexto import proyecto as c_proyecto           # noqa: E402
from contexto import repositorio as c_repositorio     # noqa: E402
from contexto import tarea as c_tarea                 # noqa: E402
from contexto.comun import Acumulador, texto_de_adf   # noqa: E402
from integraciones.gitlab import IntegracionGitLab    # noqa: E402
from integraciones.jira import IntegracionJira        # noqa: E402

CLI = BIN / "dev-harness.py"
# El token de las fugas se arma por concatenacion, como ya lo hacia
# 04_secretos.py: un fuente con un literal que dispara el propio detector es un
# fuente que nadie puede editar en una maquina donde el harness esta instalado, y
# ademas lo frena el push protection de GitHub. El valor existe igual en tiempo de
# ejecucion, que es donde el test lo necesita.
CLAVE = "GCBA-1234"
TOKEN = "un-token-que-no-tiene-que-aparecer-en-ningun-lado"

TODAS = {
    "jira.issue.read": "ENABLED", "jira.issue.search": "ENABLED",
    "jira.attachment.read": "ENABLED", "gitlab.project.read": "ENABLED",
    "gitlab.repository.read": "ENABLED", "gitlab.branch.read": "ENABLED",
    "gitlab.merge_request.read": "ENABLED",
}


def _adf(texto):
    """Una descripcion como la devuelve la API v3 de Jira."""
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": texto}]}]}


ISSUE = {
    "key": CLAVE,
    "fields": {
        "summary": "Agregar el filtro por fecha al listado",
        "description": _adf("Como operador quiero filtrar por fecha para encontrar el tramite."),
        "issuetype": {"name": "Historia de Usuario"},
        "status": {"name": "En curso"},
        "priority": {"name": "Alta"},
        "labels": ["backoffice", "listado"],
        "parent": {"key": "GCBA-1000"},
        "issuelinks": [{"type": {"name": "blocks"},
                        "outwardIssue": {"key": "GCBA-1300"}}],
        "project": {"key": "GCBA", "name": "Tramites a Distancia"},
        "attachment": [],
    },
}

FICHA = {
    "issues": [{
        "key": "GCBA-7",
        "fields": {
            "summary": "Ficha de Proyecto — Tramites a Distancia",
            "description": _adf(
                "Sistema de tramites del organismo.\n"
                "Objetivos\n"
                "Bajar el tiempo de gestion de un tramite.\n"
                "Alcance\n"
                "Backoffice y portal ciudadano.\n"
                "Reglas\n"
                "- Un tramite no se borra, se anula.\n"
                "- El CUIT se valida contra AFIP.\n"
                "Arquitectura\n"
                "Angular contra una API REST, repositorio en "
                "https://gitlab.ejemplo.gob.ar/tramites/backoffice"),
            "issuetype": {"name": "Ficha de Proyecto"},
            "attachment": [],
        },
    }]
}


class Transporte(object):
    """Jira y GitLab falsos. Contestan por fragmento de URL y cuentan las llamadas."""

    def __init__(self, respuestas, por_defecto=(404, "")):
        self.respuestas = respuestas
        self.por_defecto = por_defecto
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append(url)
        # Gana el fragmento que aparece MAS TARDE en la URL, que es el mas especifico:
        # /api/v4/projects/42/repository/branches matchea "/projects/" y "branches", y el
        # que corresponde es el segundo. Ordenar por largo no alcanza -"branches" tiene
        # menos letras que "/projects/"- y depender del orden del dict es una trampa que
        # se paga al agregar un caso.
        mejor, posicion = None, -1
        for fragmento, respuesta in self.respuestas.items():
            donde = url.rfind(fragmento)
            if donde > posicion:
                mejor, posicion = respuesta, donde
        if mejor is None:
            return self.por_defecto
        if isinstance(mejor, Exception):
            raise mejor
        if isinstance(mejor[1], (dict, list)):
            return mejor[0], json.dumps(mejor[1])
        return mejor


def _jira(transporte, raiz=None):
    almacen = _AlmacenFalso()
    return IntegracionJira({"enabled": True, "baseUrl": "https://jira.ejemplo",
                            "usuario": "yo@buenosaires.gob.ar"}, almacen, 5, transporte)


def _gitlab(transporte):
    return IntegracionGitLab({"enabled": True, "baseUrl": "https://gitlab.ejemplo.gob.ar"},
                             _AlmacenFalso(), 5, transporte)


class _AlmacenFalso(object):
    def get(self, nombre):
        return TOKEN

    def exists(self, nombre):
        return True


def _catalogo():
    return limpieza.cargar_catalogo()


def _config(**extra):
    base = {"fichaTipoDeIssue": "Ficha de Proyecto"}
    base.update(extra)
    return base


def _proyecto_temporal():
    raiz = tempfile.mkdtemp(prefix="harness-ctx-")
    os.makedirs(os.path.join(raiz, ".claude"))
    return raiz


# -- E-01 a E-05 — la tarea ----------------------------------------------------

def test_e01_la_tarea_sale_del_issue(t):
    """E-01 — clave, tipo, titulo, descripcion, estado y prioridad salen del issue."""
    acumulador = Acumulador(TODAS)
    tarea, campos = c_tarea.resolver(_jira(Transporte({"/issue/": (200, ISSUE)})),
                                     CLAVE, _catalogo(), _config(), acumulador)
    t.igual("E-01 clave", CLAVE, tarea["key"])
    t.igual("E-01 tipo", "Historia de Usuario", tarea["type"])
    t.igual("E-01 titulo", "Agregar el filtro por fecha al listado", tarea["title"])
    t.contiene("E-01 descripcion", "filtrar por fecha", tarea["description"])
    t.igual("E-01 estado", "En curso", tarea["status"])
    t.igual("E-01 prioridad", "Alta", tarea["priority"])
    t.igual("E-01 etiquetas", ["backoffice", "listado"], tarea["labels"])
    t.igual("E-01 la fuente quedo anotada", "jira_issue", acumulador.sources[0]["type"])


def test_e01b_el_adf_se_aplana_a_texto(t):
    """E-01b — la descripcion en ADF se aplana; una que ya es texto plano pasa igual."""
    adf = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "Primer parrafo."}]},
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "un item"}]}]}]}]}
    plano = texto_de_adf(adf)
    t.contiene("E-01b el parrafo", "Primer parrafo.", plano)
    t.contiene("E-01b el bullet", "- un item", plano)
    t.no_contiene("E-01b sin nodos del formato", "paragraph", plano)
    t.igual("E-01b texto plano pasa igual", "ya era texto", texto_de_adf("ya era texto"))
    t.igual("E-01b sin descripcion", "", texto_de_adf(None))


def test_e02_los_criterios_no_se_inventan(t):
    """E-02 — salen del campo configurado; sin campo, lista vacia y hueco declarado."""
    acumulador = Acumulador(TODAS)
    tarea, _ = c_tarea.resolver(_jira(Transporte({"/issue/": (200, ISSUE)})),
                                CLAVE, _catalogo(), _config(), acumulador)
    t.igual("E-02 sin campo configurado, vacio", [], tarea["acceptance_criteria"])
    t.verdadero("E-02 el hueco lo dice",
                any("criterios de aceptacion" in m for m in acumulador.missing))
    t.no_contiene("E-02 no se derivan de la descripcion", "filtrar por fecha",
                  " ".join(tarea["acceptance_criteria"]))

    con_campo = json.loads(json.dumps(ISSUE))
    con_campo["fields"]["customfield_10042"] = _adf("- Filtra por rango\n- Muestra vacio")
    acumulador2 = Acumulador(TODAS)
    tarea2, _ = c_tarea.resolver(
        _jira(Transporte({"/issue/": (200, con_campo)})), CLAVE, _catalogo(),
        _config(campoCriteriosAceptacion="customfield_10042"), acumulador2)
    t.igual("E-02 con campo configurado", ["Filtra por rango", "Muestra vacio"],
            tarea2["acceptance_criteria"])


def test_e03_sin_capacidad_no_hay_llamada(t):
    """E-03 — sin jira.issue.read no se llama a nadie y se levanta TareaNoResuelta."""
    transporte = Transporte({"/issue/": (200, ISSUE)})
    acumulador = Acumulador({"jira.issue.read": "DISABLED"})
    levanto = ""
    try:
        c_tarea.resolver(_jira(transporte), CLAVE, _catalogo(), _config(), acumulador)
    except c_tarea.TareaNoResuelta as e:
        levanto = str(e)
    t.contiene("E-03 lo dice", "jira.issue.read", levanto)
    t.igual("E-03 ni una llamada", 0, len(transporte.llamadas))
    t.verdadero("E-03 la capacidad quedo declarada",
                any("jira.issue.read" in c for c in acumulador.missing_capabilities))

    # Y la mitad de la CLI, que es lo que ve la persona: codigo 2, el mensaje, y ningun
    # archivo escrito.
    raiz = _proyecto_listo()
    with io.open(os.path.join(raiz, ".claude", "harness.capacidades.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"capacidades": dict(TODAS, **{"jira.issue.read": "DISABLED"})}))
    transporte2 = Transporte({"/issue/": (200, ISSUE)})
    codigo, _, error = _correr_cli(["contexto", CLAVE, "--proyecto", raiz], transporte2,
                                   _Bytes({}))
    t.igual("E-03 la CLI sale con 2", 2, codigo)
    t.contiene("E-03 y dice que corra el setup", "setup del harness", error)
    t.igual("E-03 sin salir a la red", 0, len(transporte2.llamadas))
    t.verdadero("E-03 y sin escribir el contexto",
                not os.path.isfile(os.path.join(raiz, ".claude", "contextos",
                                                CLAVE + ".json")))


def test_e04_un_issue_que_no_existe(t):
    """E-04 — 404 levanta con la clave adentro, no con una traza."""
    levanto = ""
    try:
        c_tarea.resolver(_jira(Transporte({"/issue/": (404, "")})), CLAVE, _catalogo(),
                         _config(), Acumulador(TODAS))
    except c_tarea.TareaNoResuelta as e:
        levanto = str(e)
    t.contiene("E-04 nombra la clave", CLAVE, levanto)
    t.contiene("E-04 dice que puede ser", "no existe", levanto)


def test_e05_el_padre_y_los_enlaces_son_referencias(t):
    """E-05 — padre y enlaces entran como clave, nunca resueltos."""
    transporte = Transporte({"/issue/": (200, ISSUE)})
    tarea, _ = c_tarea.resolver(_jira(transporte), CLAVE, _catalogo(), _config(),
                                Acumulador(TODAS))
    t.igual("E-05 el padre es una clave", "GCBA-1000", tarea["parent"])
    t.igual("E-05 el enlace es una referencia",
            [{"type": "blocks", "key": "GCBA-1300"}], tarea["links"])
    t.igual("E-05 una sola llamada: no se siguieron los enlaces", 1, len(transporte.llamadas))


# -- E-06 a E-10 — la Ficha de Proyecto ----------------------------------------

def test_e06_la_ficha_entra_entera(t):
    """E-06 — con una sola ficha, sus campos entran y su clave queda en sources."""
    acumulador = Acumulador(TODAS)
    proyecto, campos = c_proyecto.resolver(
        _jira(Transporte({"/search": (200, FICHA)})), ISSUE["fields"], _catalogo(),
        _config(), acumulador)
    ficha = proyecto["ficha"]
    t.igual("E-06 clave de la ficha", "GCBA-7", ficha["key"])
    t.igual("E-06 proyecto", "GCBA", proyecto["jira_key"])
    t.contiene("E-06 objetivos", "tiempo de gestion", ficha["objectives"])
    t.contiene("E-06 alcance", "Backoffice", ficha["scope"])
    t.igual("E-06 reglas", 2, len(ficha["rules"]))
    t.igual("E-06 sin el guion del bullet: es formato, no contenido",
            "Un tramite no se borra, se anula.", ficha["rules"][0])
    t.contiene("E-06 arquitectura", "Angular", ficha["architecture"])
    t.igual("E-06 se declara inferida", "inferred", ficha["knowledge_status"])
    t.verdadero("E-06 la fuente es jira_ficha con su clave adentro",
                any(f["type"] == "jira_ficha" and f["reference"] == "GCBA-7"
                    for f in acumulador.sources))


def test_e07_dos_fichas_es_un_conflicto(t):
    """E-07 — con dos fichas no se elige ninguna: se declara el conflicto."""
    dos = {"issues": [FICHA["issues"][0],
                      {"key": "GCBA-9", "fields": {"summary": "otra", "description": None,
                                                   "attachment": []}}]}
    acumulador = Acumulador(TODAS)
    proyecto, _ = c_proyecto.resolver(_jira(Transporte({"/search": (200, dos)})),
                                      ISSUE["fields"], _catalogo(), _config(), acumulador)
    t.igual("E-07 ficha vacia", "", proyecto["ficha"]["key"])
    t.igual("E-07 estado conflicted", "conflicted", proyecto["ficha"]["knowledge_status"])
    t.igual("E-07 un conflicto declarado", 1, len(acumulador.conflicts))
    t.contiene("E-07 nombra las dos", "GCBA-7, GCBA-9", acumulador.conflicts[0])


def test_e08_sin_ficha_se_declara_el_hueco(t):
    """E-08 — sin ninguna ficha, missing y el hueco dice que se buscó y donde."""
    acumulador = Acumulador(TODAS)
    proyecto, _ = c_proyecto.resolver(_jira(Transporte({"/search": (200, {"issues": []})})),
                                      ISSUE["fields"], _catalogo(), _config(), acumulador)
    t.igual("E-08 estado missing", "missing", proyecto["ficha"]["knowledge_status"])
    t.verdadero("E-08 el hueco nombra el tipo",
                any('"Ficha de Proyecto"' in m for m in acumulador.missing))
    t.verdadero("E-08 el hueco nombra el proyecto",
                any("GCBA" in m for m in acumulador.missing))


def test_e09_el_tipo_de_ficha_es_configurable(t):
    """E-09 — sale de fichaTipoDeIssue, y sin la clave usa el default."""
    transporte = Transporte({"/search": (200, {"issues": []})})
    c_proyecto.resolver(_jira(transporte), ISSUE["fields"], _catalogo(),
                        _config(fichaTipoDeIssue="Project Card"), Acumulador(TODAS))
    t.contiene("E-09 usa el configurado", "Project%20Card", transporte.llamadas[0])

    transporte2 = Transporte({"/search": (200, {"issues": []})})
    c_proyecto.resolver(_jira(transporte2), ISSUE["fields"], _catalogo(), {},
                        Acumulador(TODAS))
    t.contiene("E-09 sin clave, el default", "Ficha%20de%20Proyecto", transporte2.llamadas[0])


def test_e10_sin_busqueda_no_se_busca_la_ficha(t):
    """E-10 — sin jira.issue.search no se llama, y el resto del contexto sigue."""
    transporte = Transporte({"/search": (200, FICHA)})
    acumulador = Acumulador({"jira.issue.search": "DISABLED"})
    proyecto, campos = c_proyecto.resolver(_jira(transporte), ISSUE["fields"], _catalogo(),
                                           _config(), acumulador)
    t.igual("E-10 ni una llamada", 0, len(transporte.llamadas))
    t.igual("E-10 la ficha queda vacia", "", proyecto["ficha"]["key"])
    t.igual("E-10 el proyecto igual se sabe", "GCBA", proyecto["jira_key"])
    t.verdadero("E-10 la capacidad se declara",
                any("jira.issue.search" in c for c in acumulador.missing_capabilities))


# -- E-11 a E-15 — los documentos ----------------------------------------------

def _ficha_con_adjuntos():
    campos = json.loads(json.dumps(FICHA["issues"][0]["fields"]))
    campos["attachment"] = [
        {"id": "10", "filename": "PRD-tramites.pdf", "mimeType": "application/pdf",
         "size": 1024, "content": "https://jira.ejemplo/attach/10"},
        {"id": "11", "filename": "ADR-001-persistencia.md", "mimeType": "text/markdown",
         "size": 64, "content": "https://jira.ejemplo/attach/11"},
    ]
    return campos


class _Bytes(object):
    """Transporte binario falso: devuelve el contenido por URL."""

    def __init__(self, por_url):
        self.por_url = por_url
        self.llamadas = []

    def __call__(self, url, headers, timeout):
        self.llamadas.append(url)
        for fragmento, datos in self.por_url.items():
            if fragmento in url:
                return 200, datos
        return 404, b""


def _jira_con_bytes(bytes_falsos):
    jira = _jira(Transporte({}))
    jira.transporte_bytes = bytes_falsos
    return jira


def test_e11_los_adjuntos_entran_ordenados_y_sin_duplicados(t):
    """E-11 — nombre, tipo, tamaño y origen, ordenados y una sola vez."""
    campos = _ficha_con_adjuntos()
    campos["attachment"].append(dict(campos["attachment"][0]))  # el mismo id, dos veces
    acumulador = Acumulador(TODAS)
    salida = c_documentos.resolver(
        _jira_con_bytes(_Bytes({"/10": b"%PDF-1.4 x", "/11": b"# ADR"})),
        ISSUE["fields"], campos, _catalogo(), _config(), acumulador,
        tempfile.mkdtemp(prefix="harness-doc-"), ejecutar=lambda a: (1, ""))
    nombres = [i["filename"] for i in salida["items"]]
    t.igual("E-11 sin duplicados", 2, len(nombres))
    t.igual("E-11 ordenados", sorted(nombres), nombres)
    pdf = [i for i in salida["items"] if i["filename"].endswith(".pdf")][0]
    t.igual("E-11 el tamaño viaja", 1024, pdf["size"])
    t.igual("E-11 el tipo viaja", "application/pdf", pdf["mime"])
    t.igual("E-11 y el origen dice de que issue cuelga", "ficha", pdf["origin"])


def test_e12_sin_capacidad_no_se_baja_nada(t):
    """E-12 — sin jira.attachment.read, inventario vacio y capacidad declarada."""
    bytes_falsos = _Bytes({"/10": b"x"})
    acumulador = Acumulador({"jira.attachment.read": "DISABLED"})
    salida = c_documentos.resolver(_jira_con_bytes(bytes_falsos), ISSUE["fields"],
                                   _ficha_con_adjuntos(), _catalogo(), _config(),
                                   acumulador, tempfile.mkdtemp(), ejecutar=lambda a: (1, ""))
    t.igual("E-12 sin items", [], salida["items"])
    t.igual("E-12 no se bajo nada", 0, len(bytes_falsos.llamadas))
    t.verdadero("E-12 la capacidad se declara",
                any("jira.attachment.read" in c for c in acumulador.missing_capabilities))


def test_e13_markitdown_presente_y_ausente(t):
    """E-13 — con markitdown el texto entra; sin markitdown se declara el hueco."""
    destino = tempfile.mkdtemp(prefix="harness-doc-")
    bytes_falsos = _Bytes({"/10": b"%PDF-1.4 fake", "/11": b"# ADR 001\nSe usa Oracle."})

    def con_markitdown(argumentos):
        if argumentos[1] == "--version":
            return 0, "markitdown 0.1"
        return 0, "# PRD\nEl tramite se inicia en el portal."

    acumulador = Acumulador(TODAS)
    salida = c_documentos.resolver(_jira_con_bytes(bytes_falsos), ISSUE["fields"],
                                   _ficha_con_adjuntos(), _catalogo(), _config(),
                                   acumulador, destino, ejecutar=con_markitdown)
    pdf = [i for i in salida["items"] if i["filename"].endswith(".pdf")][0]
    t.igual("E-13 con markitdown, extractor", "markitdown", pdf["extractor"])
    t.igual("E-13 con markitdown, texto extraido", True, pdf["text_extracted"])
    t.contiene("E-13 el texto es el convertido", "El tramite se inicia", pdf["text"])

    def sin_markitdown(argumentos):
        raise OSError("no esta")

    acumulador2 = Acumulador(TODAS)
    salida2 = c_documentos.resolver(_jira_con_bytes(_Bytes({"/10": b"%PDF", "/11": b"# ADR"})),
                                    ISSUE["fields"], _ficha_con_adjuntos(), _catalogo(),
                                    _config(), acumulador2, tempfile.mkdtemp(),
                                    ejecutar=sin_markitdown)
    pdf2 = [i for i in salida2["items"] if i["filename"].endswith(".pdf")][0]
    t.igual("E-13 sin markitdown, extractor", "ninguno", pdf2["extractor"])
    t.igual("E-13 sin markitdown, no miente", False, pdf2["text_extracted"])
    t.verdadero("E-13 el archivo igual quedo", pdf2["local_path"] != "")
    t.verdadero("E-13 el hueco dice que falta",
                any("markitdown" in m for m in acumulador2.missing))
    md = [i for i in salida2["items"] if i["filename"].endswith(".md")][0]
    t.igual("E-13 el markdown no necesita markitdown", "texto-plano", md["extractor"])


def test_e14_la_clasificacion_es_inferida(t):
    """E-14 — sale de patrones sobre el nombre y el bloque viaja como inferido."""
    t.igual("E-14 prd", "prd", c_documentos.clasificar("PRD-tramites.pdf"))
    t.igual("E-14 adr", "adr", c_documentos.clasificar("ADR-001-persistencia.md"))
    t.igual("E-14 regla", "regla", c_documentos.clasificar("reglas-de-negocio.docx"))
    t.igual("E-14 manual", "manual", c_documentos.clasificar("Manual-de-usuario.pdf"))
    t.igual("E-14 otro", "otro", c_documentos.clasificar("adjunto-sin-nombre-util.bin"))

    salida = c_documentos.resolver(
        _jira_con_bytes(_Bytes({"/10": b"%PDF", "/11": b"# ADR"})), ISSUE["fields"],
        _ficha_con_adjuntos(), _catalogo(), _config(), Acumulador(TODAS),
        tempfile.mkdtemp(), ejecutar=lambda a: (1, ""))
    t.igual("E-14 el bloque se declara inferido", "inferred", salida["knowledge_status"])


def test_e15_el_texto_se_recorta_y_se_dice(t):
    """E-15 — el recorte se declara en el documento y en los huecos."""
    largo = "palabra " * 5000
    acumulador = Acumulador(TODAS)
    salida = c_documentos.resolver(
        _jira_con_bytes(_Bytes({"/11": largo.encode("utf-8"), "/10": b"%PDF"})),
        ISSUE["fields"], _ficha_con_adjuntos(), _catalogo(),
        _config(topeTextoDocumento=100), acumulador, tempfile.mkdtemp(),
        ejecutar=lambda a: (1, ""))
    md = [i for i in salida["items"] if i["filename"].endswith(".md")][0]
    t.igual("E-15 se marca recortado", True, md["truncated"])
    t.verdadero("E-15 el texto quedo corto", len(md["text"]) < 200)
    t.contiene("E-15 el recorte se ve en el texto", "recortado por el harness", md["text"])
    t.verdadero("E-15 y en los huecos", any("se recorto" in m for m in acumulador.missing))


# -- E-16 a E-19 — el repositorio ----------------------------------------------

PROYECTO_GITLAB = {"id": 42, "path_with_namespace": "tramites/backoffice",
                   "web_url": "https://gitlab.ejemplo.gob.ar/tramites/backoffice",
                   "default_branch": "develop"}
RAMAS = [{"name": "feature/GCBA-1234-filtro", "commit": {"id": "abc123def456789"},
          "web_url": "https://gitlab/x"},
         {"name": "feature/GCBA-9999-otra", "commit": {"id": "zzz"}, "web_url": ""}]
MRS = [{"iid": 7, "title": "GCBA-1234 filtro por fecha", "state": "opened",
        "source_branch": "feature/GCBA-1234-filtro", "target_branch": "develop",
        "web_url": "https://gitlab/mr/7"},
       {"iid": 8, "title": "Otra cosa", "state": "merged", "source_branch": "x",
        "target_branch": "develop", "web_url": ""}]


def test_e16_sin_referencia_no_se_busca_nada(t):
    """E-16 — sin repo en la config ni en la ficha, seccion vacia y ni una llamada."""
    transporte = Transporte({"/projects/": (200, PROYECTO_GITLAB)})
    acumulador = Acumulador(TODAS)
    seccion = c_repositorio.resolver(_gitlab(transporte), CLAVE, {},
                                     c_proyecto.ficha_vacia(), acumulador,
                                     _proyecto_temporal())
    t.igual("E-16 ni una llamada", 0, len(transporte.llamadas))
    t.igual("E-16 seccion vacia", "", seccion["project"]["id"])
    t.verdadero("E-16 el hueco lo explica",
                any("No se adivina" in m for m in acumulador.missing))

    ficha = dict(c_proyecto.ficha_vacia())
    ficha["architecture"] = "repo en https://gitlab.ejemplo.gob.ar/tramites/backoffice"
    acumulador2 = Acumulador(TODAS)
    seccion2 = c_repositorio.resolver(
        _gitlab(Transporte({"/projects/": (200, PROYECTO_GITLAB),
                            "branches": (200, RAMAS), "merge_requests": (200, MRS)})),
        CLAVE, {}, ficha, acumulador2, _proyecto_temporal())
    t.igual("E-16 la URL de la ficha alcanza", "42", seccion2["project"]["id"])

    # La clave vive adentro del bloque `gitlab`, al lado de su baseUrl: es donde la
    # escribe la plantilla que reparte el instalador.
    bloque = json.loads(io.open(
        str(RAIZ / "harnesses" / "desarrollo" / "integraciones.plantilla.json"),
        encoding="utf-8").read())["gitlab"]
    t.verdadero("E-16 la plantilla declara gitlabProyecto en el bloque gitlab",
                "gitlabProyecto" in bloque)
    referencia, _ = c_repositorio.referencia_de_proyecto(
        {"baseUrl": "https://gitlab", "gitlabProyecto": "grupo/proy"}, None)
    t.igual("E-16 y se lee de ahi", "grupo/proy", referencia)


def test_e17_solo_lo_que_nombra_la_clave(t):
    """E-17 — entran las ramas y los MR que nombran la clave; el resto no."""
    acumulador = Acumulador(TODAS)
    seccion = c_repositorio.resolver(
        _gitlab(Transporte({"/projects/42": (200, PROYECTO_GITLAB),
                            "/projects/": (200, PROYECTO_GITLAB),
                            "branches": (200, RAMAS), "merge_requests": (200, MRS)})),
        CLAVE, {"gitlabProyecto": "tramites/backoffice"}, None, acumulador,
        _proyecto_temporal())
    t.igual("E-17 una sola rama", ["feature/GCBA-1234-filtro"],
            [r["name"] for r in seccion["branches"]])
    t.igual("E-17 un solo MR", ["7"], [m["iid"] for m in seccion["merge_requests"]])
    t.igual("E-17 el commit viene corto", "abc123def456", seccion["branches"][0]["last_commit"])


def test_e18_cada_capacidad_degrada_por_su_cuenta(t):
    """E-18 — sin branch.read las ramas quedan vacias y los MR no se enteran."""
    acumulador = Acumulador({"gitlab.project.read": "ENABLED",
                             "gitlab.branch.read": "DISABLED",
                             "gitlab.merge_request.read": "ENABLED"})
    seccion = c_repositorio.resolver(
        _gitlab(Transporte({"/projects/": (200, PROYECTO_GITLAB),
                            "branches": (200, RAMAS), "merge_requests": (200, MRS)})),
        CLAVE, {"gitlabProyecto": "tramites/backoffice"}, None, acumulador,
        _proyecto_temporal())
    t.igual("E-18 sin ramas", [], seccion["branches"])
    t.igual("E-18 con MR igual", 1, len(seccion["merge_requests"]))
    t.igual("E-18 una sola capacidad declarada", 1, len(acumulador.missing_capabilities))
    t.contiene("E-18 y es la que falta", "gitlab.branch.read",
               acumulador.missing_capabilities[0])

    # La simetrica: sin merge_request.read, las ramas siguen entrando.
    acumulador2 = Acumulador({"gitlab.project.read": "ENABLED",
                              "gitlab.branch.read": "ENABLED",
                              "gitlab.merge_request.read": "DISABLED"})
    seccion2 = c_repositorio.resolver(
        _gitlab(Transporte({"/projects/": (200, PROYECTO_GITLAB),
                            "branches": (200, RAMAS), "merge_requests": (200, MRS)})),
        CLAVE, {"gitlabProyecto": "tramites/backoffice"}, None, acumulador2,
        _proyecto_temporal())
    t.igual("E-18 al reves: con ramas", 1, len(seccion2["branches"]))
    t.igual("E-18 al reves: sin MR", [], seccion2["merge_requests"])


def test_e19_el_contexto_de_codigo_se_referencia(t):
    """E-19 — si hay project-context.json se apunta con su hash, no se copia."""
    raiz = _proyecto_temporal()
    os.makedirs(os.path.join(raiz, "docs", "codebase"))
    with io.open(os.path.join(raiz, "docs", "codebase", "project-context.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"meta": {"context_hash": "sha256:" + "a" * 64},
                            "architecture": {"components": [{"name": "no copiar"}]}}))
    acumulador = Acumulador(TODAS)
    seccion = c_repositorio.resolver(_gitlab(Transporte({})), CLAVE, {}, None,
                                     acumulador, raiz)
    ref = seccion["code_context_ref"]
    t.igual("E-19 la ruta", "docs/codebase/project-context.json", ref["path"])
    t.igual("E-19 el hash", "sha256:" + "a" * 64, ref["context_hash"])
    t.no_contiene("E-19 no se copio el contenido", "no copiar", json.dumps(seccion))

    acumulador2 = Acumulador(TODAS)
    sin = c_repositorio.resolver(_gitlab(Transporte({})), CLAVE, {}, None, acumulador2,
                                 _proyecto_temporal())
    t.igual("E-19 sin contrato, vacio", "", sin["code_context_ref"]["path"])
    t.verdadero("E-19 y el hueco dice quien lo escribe",
                any("dev-iniciador-code" in m for m in acumulador2.missing))


# -- E-20 a E-23 — el ensamblado -----------------------------------------------

def _resolver_todo(transporte_texto=None, transporte_bytes=None, capacidades=None,
                   raiz=None, config=None, config_gitlab=None):
    """Una resolucion entera, sin CLI."""
    raiz = raiz or _proyecto_temporal()
    transporte_texto = transporte_texto or Transporte({
        "/issue/": (200, ISSUE), "/search": (200, FICHA),
        "/projects/": (200, PROYECTO_GITLAB), "branches": (200, RAMAS),
        "merge_requests": (200, MRS)})
    acumulador = Acumulador(TODAS if capacidades is None else capacidades)
    jira = _jira(transporte_texto)
    jira.transporte_bytes = transporte_bytes or _Bytes({})
    cfg = config or _config()
    task, campos = c_tarea.resolver(jira, CLAVE, _catalogo(), cfg, acumulador)
    project, campos_ficha = c_proyecto.resolver(jira, campos, _catalogo(), cfg, acumulador)
    documentation = c_documentos.resolver(jira, campos, campos_ficha, _catalogo(), cfg,
                                          acumulador, os.path.join(raiz, "adj"),
                                          ejecutar=lambda a: (1, ""))
    repository = c_repositorio.resolver(_gitlab(transporte_texto), CLAVE,
                                        config_gitlab or {}, project["ficha"], acumulador,
                                        raiz)
    documento = c_ensamblador.armar(CLAVE, task, project, documentation, repository,
                                    acumulador, "0.17.0", _catalogo())
    return documento, acumulador, raiz


def test_e20_cada_lectura_deja_su_fuente(t):
    """E-20 — sources lista una entrada por cosa leida, con su tipo y su momento."""
    documento, _, _ = _resolver_todo()
    tipos = sorted(set(f["type"] for f in documento["sources"]))
    t.verdadero("E-20 esta el issue", "jira_issue" in tipos)
    t.verdadero("E-20 esta la ficha", "jira_ficha" in tipos)
    t.verdadero("E-20 esta el proyecto de gitlab", "gitlab_project" in tipos)
    for fuente in documento["sources"]:
        t.verdadero("E-20 %s tiene momento" % fuente["source_id"],
                    len(fuente["retrieved_at"]) >= 19)


def test_e21_un_fallo_en_el_medio_degrada_su_seccion(t):
    """E-21 — un 401 cuando el registro decia ENABLED no voltea la resolucion."""
    transporte = Transporte({
        "/issue/": (200, ISSUE), "/search": (200, FICHA),
        "/projects/": (401, "token vencido")})
    documento, acumulador, _ = _resolver_todo(transporte_texto=transporte)
    t.igual("E-21 la tarea sigue entera", CLAVE, documento["task"]["key"])
    t.igual("E-21 el repositorio quedo vacio", "", documento["repository"]["project"]["id"])
    t.verdadero("E-21 y se declara", any("401" in m for m in acumulador.missing))


def test_e22_con_gitlab_caido_el_documento_sale(t):
    """E-22 — GitLab caido de verdad: el comando sale con codigo 0 y el documento entero.

    "Caido" es que GitLab conteste mal, no que le saquen la capacidad del registro — eso
    ya es E-18. El registro dice ENABLED, como diria despues de un bootstrap exitoso, y la
    llamada real falla: es el caso que se da cuando el servidor se cae entre una corrida y
    la siguiente. Y se mide el codigo de salida, que es la mitad del escenario que antes
    no miraba nadie.
    """
    raiz = _proyecto_listo()
    transporte = Transporte({
        "/issue/": (200, ISSUE), "/search": (200, FICHA),
        "/projects/": (500, "gateway caido"),
    })
    codigo, salida, error = _correr_cli(["contexto", CLAVE, "--proyecto", raiz],
                                        transporte, _Bytes({}))
    t.igual("E-22 el comando sale con 0", 0, codigo)

    documento = json.loads(io.open(os.path.join(raiz, ".claude", "contextos",
                                                CLAVE + ".json"), encoding="utf-8").read())
    t.igual("E-22 la tarea entera", CLAVE, documento["task"]["key"])
    t.igual("E-22 la ficha entera", "GCBA-7", documento["project"]["ficha"]["key"])
    t.igual("E-22 el repositorio vacio", "", documento["repository"]["project"]["name"])
    t.verdadero("E-22 y el 500 declarado",
                any("500" in m for m in documento["gaps_and_conflicts"]["missing"]))
    t.igual("E-22 el documento sale valido igual", [], c_ensamblador.validar(documento))


def test_e23_lo_que_no_se_resolvio_sale_vacio(t):
    """E-23 — nunca un valor por defecto que parezca un dato."""
    documento, _, _ = _resolver_todo(transporte_texto=Transporte({
        "/issue/": (200, ISSUE), "/search": (200, {"issues": []})}))
    ficha = documento["project"]["ficha"]
    for campo in ("key", "title", "summary", "objectives", "scope", "architecture"):
        t.igual("E-23 ficha.%s vacio" % campo, "", ficha[campo])
    t.igual("E-23 reglas vacias", [], ficha["rules"])
    t.igual("E-23 con su estado", "missing", ficha["knowledge_status"])


# -- E-24 a E-26 — los secretos ------------------------------------------------

def test_e24_un_token_en_la_descripcion_no_llega_al_contexto(t):
    """E-24 — se reemplaza por su muestra segura y el hallazgo se declara."""
    fuga = "glpat" + "-A1b2C3D4E5F6G7H8I9J0"
    issue = json.loads(json.dumps(ISSUE))
    issue["fields"]["description"] = _adf("Usa el token %s para probar." % fuga)
    documento, acumulador, _ = _resolver_todo(transporte_texto=Transporte({
        "/issue/": (200, issue), "/search": (200, {"issues": []})}))
    t.no_contiene("E-24 el token no esta en la descripcion", fuga,
                  documento["task"]["description"])
    t.no_contiene("E-24 ni en el documento entero", fuga, json.dumps(documento))
    t.contiene("E-24 queda la marca", "secreto redactado", documento["task"]["description"])
    t.igual("E-24 el hallazgo se declara", 1,
            len(documento["gaps_and_conflicts"]["redacted_secrets"]))
    t.no_contiene("E-24 el hallazgo tampoco lo repite", fuga,
                  documento["gaps_and_conflicts"]["redacted_secrets"][0])


def test_e25_ninguna_ruta_de_entrada_esquiva_la_limpieza(t):
    """E-25 — la ficha y el texto de un documento pasan por lo mismo."""
    fuga = "glpat" + "-Z9y8X7w6V5u4T3s2R1q0"
    ficha = json.loads(json.dumps(FICHA))
    ficha["issues"][0]["fields"]["description"] = _adf("Arquitectura\nToken: %s" % fuga)
    documento, _, _ = _resolver_todo(transporte_texto=Transporte({
        "/issue/": (200, ISSUE), "/search": (200, ficha)}))
    t.no_contiene("E-25 la ficha limpia", fuga, json.dumps(documento["project"]))

    acumulador = Acumulador(TODAS)
    salida = c_documentos.resolver(
        _jira_con_bytes(_Bytes({"/11": ("Clave: %s" % fuga).encode("utf-8"), "/10": b"x"})),
        ISSUE["fields"], _ficha_con_adjuntos(), _catalogo(), _config(), acumulador,
        tempfile.mkdtemp(), ejecutar=lambda a: (1, ""))
    t.no_contiene("E-25 el documento limpio", fuga, json.dumps(salida))
    t.verdadero("E-25 y se declara", len(acumulador.redacted_secrets) >= 1)


def test_e25b_las_dos_rutas_que_se_escapaban(t):
    """E-25 — los criterios de aceptacion y el titulo de la Ficha, que eran las dos fugas.

    Las encontro el refutador: la redaccion se hacia campo por campo y estas dos no
    estaban. El arreglo no fue agregar dos llamadas, fue redactar el documento entero en
    el ensamblador — asi que este test tambien prueba que el arreglo es estructural y no
    dos parches.
    """
    fuga = "glpat" + "-Q1w2E3r4T5y6U7i8O9p0"

    issue = json.loads(json.dumps(ISSUE))
    issue["fields"]["customfield_10042"] = _adf("- El filtro usa el token %s" % fuga)
    documento, _, _ = _resolver_todo(
        transporte_texto=Transporte({"/issue/": (200, issue), "/search": (200, {"issues": []})}),
        config=_config(campoCriteriosAceptacion="customfield_10042"))
    t.no_contiene("E-25 los criterios de aceptacion", fuga,
                  json.dumps(documento["task"]["acceptance_criteria"]))
    t.verdadero("E-25 y el criterio sigue estando, redactado",
                len(documento["task"]["acceptance_criteria"]) == 1)

    ficha = json.loads(json.dumps(FICHA))
    ficha["issues"][0]["fields"]["summary"] = "Ficha con %s pegado" % fuga
    documento2, _, _ = _resolver_todo(transporte_texto=Transporte({
        "/issue/": (200, ISSUE), "/search": (200, ficha)}))
    t.no_contiene("E-25 el titulo de la ficha", fuga, documento2["project"]["ficha"]["title"])
    t.no_contiene("E-25 ni el documento entero", fuga, json.dumps(documento2))

    # Y un campo cualquiera que nadie penso: el nombre de una rama de GitLab.
    ramas = [{"name": "feature/GCBA-1234-%s" % fuga, "commit": {"id": "a"}, "web_url": ""}]
    documento3, _, _ = _resolver_todo(
        transporte_texto=Transporte({
            "/issue/": (200, ISSUE), "/search": (200, {"issues": []}),
            "/projects/": (200, PROYECTO_GITLAB), "branches": (200, ramas),
            "merge_requests": (200, [])}),
        config_gitlab={"gitlabProyecto": "tramites/backoffice"})
    t.igual("E-25 la rama entro de verdad", 1, len(documento3["repository"]["branches"]))
    t.no_contiene("E-25 hasta el nombre de una rama, que ningun resolvedor limpiaba", fuga,
                  json.dumps(documento3))


def test_e26_el_catalogo_es_el_mismo_archivo_del_hook(t):
    """E-26 — se importa, no se copia: un patron nuevo vale acá sin tocar este codigo."""
    ruta = limpieza._localizar(("reglas", "secretos.patrones.json"))
    t.igual("E-26 es el catalogo de comun", str(RAIZ / "comun" / "reglas" / "secretos.patrones.json"),
            os.path.normpath(ruta))
    catalogo = limpieza.cargar_catalogo()
    ids = [p["id"] for p in catalogo["patrones"]]
    t.verdadero("E-26 trae los patrones del harness", "token-gitlab" in ids)
    t.verdadero("E-26 y los de antes", "clave-privada" in ids)
    t.igual("E-26 el modulo tambien", str(RAIZ / "comun" / "hooks" / "lib" / "secretos.py"),
            os.path.normpath(limpieza._localizar(("hooks", "lib", "secretos.py"))))


def test_e26b_la_confianza_media_se_declara_y_no_toca_el_texto(t):
    """E-26b — en el hook decide una persona; aca no hay a quien preguntarle."""
    texto = "api_key = estoesunvalorlargoquenoesunpatron"
    limpio, hallazgos = limpieza.redactar(texto, limpieza.cargar_catalogo(), "prueba")
    t.igual("E-26b el texto no se toca", texto, limpio)
    t.verdadero("E-26b pero se declara", any("confianza media" in h for h in hallazgos))


# -- E-27 a E-29 — el contrato -------------------------------------------------

def test_e27_el_documento_valida(t):
    """E-27 — valida contra task-context/1.0, con el validador que ya existia."""
    documento, _, _ = _resolver_todo()
    t.igual("E-27 sin errores", [], c_ensamblador.validar(documento))
    t.igual("E-27 la version", "task-context/1.0", documento["meta"]["schema_version"])


def test_e28_un_schema_no_soportado_falla(t):
    """E-28 — el validador falla en vez de dar por valido lo que no interpreta."""
    armador = c_ensamblador._armador()
    levanto = False
    try:
        armador.controlar_soporte({"type": "object", "additionalProperties": False})
    except Exception as e:
        levanto = "additionalProperties" in str(e)
    t.igual("E-28 no se afloja el schema", True, levanto)


def test_e29_el_hash_identifica_la_corrida(t):
    """E-29 — dos resoluciones de los mismos datos dan el mismo hash; el reloj no cuenta."""
    uno, _, _ = _resolver_todo()
    dos, _, _ = _resolver_todo()
    t.igual("E-29 mismo hash", uno["meta"]["context_hash"], dos["meta"]["context_hash"])
    t.igual("E-29 mismo id", uno["meta"]["context_id"], dos["meta"]["context_id"])
    t.contiene("E-29 el id lleva la clave", CLAVE, uno["meta"]["context_id"])
    t.verdadero("E-29 el hash tiene forma", uno["meta"]["context_hash"].startswith("sha256:"))

    # El hash que quedo escrito tiene que ser el del contenido, no cualquier cadena con
    # forma de sha256: sin esto, un ensamblador que escriba una constante pasa el test.
    armador = c_ensamblador._armador()
    t.igual("E-29 el hash es el del contenido", uno["meta"]["context_hash"],
            armador.hash_de(uno))

    # Y el reloj queda afuera del hash: es lo que hace que el campo conteste si dos
    # consumidores estan mirando lo mismo.
    con_otro_reloj = json.loads(json.dumps(uno))
    con_otro_reloj["meta"]["generated_at"] = "2020-01-01T00:00:00"
    t.igual("E-29 el reloj no entra al hash", uno["meta"]["context_hash"],
            armador.hash_de(con_otro_reloj))

    otro = json.loads(json.dumps(uno))
    otro["task"]["title"] = "otra cosa"
    t.verdadero("E-29 y cambia si cambian los datos",
                armador.hash_de(otro) != uno["meta"]["context_hash"])


# -- E-30 y E-31 — la CLI ------------------------------------------------------

def _correr_cli(argv, transporte=None, transporte_bytes=None):
    import importlib.util
    spec = importlib.util.spec_from_file_location("dev_harness_ctx", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(argv, transporte, transporte_bytes)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _proyecto_listo():
    raiz = _proyecto_temporal()
    with io.open(os.path.join(raiz, ".env"), "w", encoding="utf-8") as f:
        f.write("JIRA_TOKEN=%s\nGITLAB_TOKEN=%s\n" % (TOKEN, TOKEN))
    with io.open(os.path.join(raiz, ".claude", "harness.integraciones.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"jira": {"enabled": True, "baseUrl": "https://jira.ejemplo",
                                     "usuario": "yo@gcba"},
                            "gitlab": {"enabled": True,
                                       "baseUrl": "https://gitlab.ejemplo.gob.ar",
                                       "gitlabProyecto": "tramites/backoffice"}}))
    with io.open(os.path.join(raiz, ".claude", "harness.capacidades.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"capacidades": TODAS}))
    return raiz


def test_e30_la_cli_escribe_el_contexto_y_lo_resume(t):
    """E-30 — escribe .claude/contextos/<CLAVE>.json e imprime un resumen."""
    raiz = _proyecto_listo()
    transporte = Transporte({"/issue/": (200, ISSUE), "/search": (200, FICHA),
                             "/projects/": (200, PROYECTO_GITLAB),
                             "branches": (200, RAMAS), "merge_requests": (200, MRS)})
    codigo, salida, error = _correr_cli(["contexto", CLAVE, "--proyecto", raiz],
                                        transporte, _Bytes({}))
    destino = os.path.join(raiz, ".claude", "contextos", CLAVE + ".json")
    t.igual("E-30 codigo 0", 0, codigo)
    t.verdadero("E-30 el archivo esta", os.path.isfile(destino))
    t.contiene("E-30 el resumen nombra la tarea", CLAVE, salida)
    t.contiene("E-30 y la ficha", "GCBA-7", salida)
    t.no_contiene("E-30 sin el token", TOKEN, salida + error)

    documento = json.loads(io.open(destino, encoding="utf-8").read())
    t.igual("E-30 el documento valida", [], c_ensamblador.validar(documento))

    codigo, stdout, stderr = _correr_cli(["contexto", CLAVE, "--proyecto", raiz, "--json"],
                                         transporte, _Bytes({}))
    t.igual("E-30 con --json sale por stdout", CLAVE, json.loads(stdout)["meta"]["task_key"])
    t.contiene("E-30 y el resumen se va a stderr", "evento=contexto.listo", stderr)
    t.no_contiene("E-30 el stdout queda parseable, sin eventos", "evento=", stdout)


def test_e30b_una_clave_que_no_es_clave(t):
    """E-30b — contexto sin una clave con forma de clave sale con 2 y lo explica."""
    codigo, _, error = _correr_cli(["contexto", "no-es-una-clave", "--proyecto",
                                    _proyecto_listo()])
    t.igual("E-30b codigo 2", 2, codigo)
    t.contiene("E-30b da el ejemplo", "GCBA-1234", error)


def test_e31_la_segunda_corrida_pisa_y_no_acumula(t):
    """E-31 — el contexto es el de ahora, no una bitacora."""
    raiz = _proyecto_listo()
    transporte = Transporte({"/issue/": (200, ISSUE), "/search": (200, FICHA)})
    _correr_cli(["contexto", CLAVE, "--proyecto", raiz], transporte, _Bytes({}))
    otro = json.loads(json.dumps(ISSUE))
    otro["fields"]["summary"] = "El titulo cambio en Jira"
    _correr_cli(["contexto", CLAVE, "--proyecto", raiz],
                Transporte({"/issue/": (200, otro), "/search": (200, FICHA)}), _Bytes({}))

    carpeta = os.path.join(raiz, ".claude", "contextos")
    archivos = [a for a in os.listdir(carpeta) if a.endswith(".json")]
    t.igual("E-31 un solo archivo", [CLAVE + ".json"], archivos)
    documento = json.loads(io.open(os.path.join(carpeta, CLAVE + ".json"),
                                   encoding="utf-8").read())
    t.igual("E-31 con lo de ahora", "El titulo cambio en Jira", documento["task"]["title"])
