"""GitLab Resolver: el estado tecnico que le corresponde a esta tarea.

Lo que entra a la seccion son las ramas y los merge requests que **nombran la clave del
ticket**. El resto del repositorio no es contexto de esta tarea: un contexto que trae las
cuarenta ramas del proyecto no ayuda a entender GCBA-1234, lo tapa.

De donde sale el proyecto GitLab, en este orden:

    1. `gitlabProyecto`, adentro del bloque `gitlab` de harness.integraciones.json
    2. una URL de GitLab escrita en la Ficha de Proyecto

Si no esta en ninguno de los dos, la seccion queda vacia con su hueco y no se busca nada:
adivinar el repositorio por el nombre del proyecto Jira es exactamente la clase de
inferencia invisible que este contrato existe para no hacer.

Ademas referencia -no copia- el contexto del codigo (`project-context`) que dejo el
recorrido del codigo. Son dos contratos distintos: duplicar uno adentro del otro los
desincroniza en la primera actualizacion.

El contexto del codigo se le pide a Knowledge Access (`conocimiento.acceso.lookup`, spec
docs/cambios/knowledge-api/spec.md, 34.2): este modulo ya no arma la ruta ni abre el archivo.
La ubicacion (`rutaCodebase`), el deny del proyecto y la redaccion de secretos son de esa
frontera, y el resolvedor ya no recibe la ruta del codebase.
"""
import json
import re

from conocimiento import acceso

RE_URL_GITLAB = re.compile(r"https?://[^\s)]*gitlab[^\s)]*", re.IGNORECASE)

# Los campos de la Ficha donde se busca la URL del repositorio. Los lee tambien la identidad
# del repositorio de `flujo/`, que tiene que ver lo mismo que vio este resolvedor.
CAMPOS_DE_FICHA = ("summary", "objectives", "scope", "architecture")


def seccion_vacia(estado="missing"):
    return {
        "project": {"id": "", "name": "", "web_url": "", "default_branch": ""},
        "branches": [],
        "merge_requests": [],
        "code_context_ref": {"path": "", "context_hash": ""},
        "knowledge_status": estado,
    }


def referencia_de_proyecto(config_gitlab, ficha):
    """La referencia al proyecto GitLab, y de donde salio.

    `config_gitlab` es el bloque `gitlab` de harness.integraciones.json, no el documento
    entero: ahi es donde vive `gitlabProyecto`, al lado de su baseUrl.
    """
    declarado = str((config_gitlab or {}).get("gitlabProyecto") or "").strip()
    if declarado:
        return declarado, "la configuracion del harness"

    texto = " ".join(str(ficha.get(c) or "") for c in CAMPOS_DE_FICHA) if ficha else ""
    m = RE_URL_GITLAB.search(texto)
    if m:
        # De https://gitlab.ejemplo/grupo/proyecto queda grupo/proyecto, que es lo que
        # la API acepta URL-encodeado.
        camino = re.sub(r"^https?://[^/]+/", "", m.group(0)).rstrip("/")
        if camino.endswith(".git"):
            camino = camino[:-4]
        if camino:
            return camino, "la Ficha de Proyecto"
    return "", ""


def resolver(gitlab, clave_tarea, config_gitlab, ficha, acumulador, raiz_proyecto):
    """La seccion `repository`. Nunca levanta."""
    seccion = seccion_vacia()
    seccion["code_context_ref"] = _contexto_de_codigo(raiz_proyecto, acumulador)

    referencia, de_donde = referencia_de_proyecto(config_gitlab, ficha)
    if not referencia:
        acumulador.falta(
            "el repositorio: no hay `gitlabProyecto` en el bloque gitlab de "
            "harness.integraciones.json ni una "
            "URL de GitLab en la Ficha de Proyecto. No se adivina por el nombre.")
        return seccion

    if not acumulador.hay("gitlab.project.read", "sin eso no se puede leer el repositorio"):
        return seccion

    respuesta = gitlab.proyecto(referencia)
    if not respuesta.ok:
        acumulador.falta("el repositorio %s: GitLab contesto %d (la referencia salio de %s)"
                         % (referencia, respuesta.codigo, de_donde))
        return seccion

    datos = respuesta.datos() or {}
    id_proyecto = str(datos.get("id") or referencia)
    seccion["project"] = {
        "id": id_proyecto,
        "name": str(datos.get("path_with_namespace") or datos.get("name") or ""),
        "web_url": str(datos.get("web_url") or ""),
        "default_branch": str(datos.get("default_branch") or ""),
    }
    seccion["knowledge_status"] = "confirmed"
    acumulador.fuente("gitlab:" + id_proyecto, "gitlab_project", referencia)

    seccion["branches"] = _ramas(gitlab, id_proyecto, clave_tarea, acumulador)
    seccion["merge_requests"] = _merge_requests(gitlab, id_proyecto, clave_tarea, acumulador)
    return seccion


def _ramas(gitlab, id_proyecto, clave, acumulador):
    if not acumulador.hay("gitlab.branch.read", "sin eso no se listan las ramas de la tarea"):
        return []
    respuesta = gitlab.ramas(id_proyecto, clave)
    if not respuesta.ok:
        acumulador.falta("las ramas: GitLab contesto %d" % respuesta.codigo)
        return []
    salida = []
    for rama in (respuesta.datos() or []):
        if not isinstance(rama, dict):
            continue
        nombre = str(rama.get("name") or "")
        if clave.lower() not in nombre.lower():
            continue
        commit = rama.get("commit") or {}
        salida.append({
            "name": nombre,
            "last_commit": str(commit.get("id") or "")[:12],
            "web_url": str(rama.get("web_url") or ""),
        })
        acumulador.fuente("gitlab:rama:" + nombre, "gitlab_branch", nombre)
    if not salida:
        acumulador.falta("no hay ninguna rama que nombre %s en el repositorio" % clave)
    return salida


def _merge_requests(gitlab, id_proyecto, clave, acumulador):
    if not acumulador.hay("gitlab.merge_request.read",
                          "sin eso no se listan los merge requests de la tarea"):
        return []
    respuesta = gitlab.merge_requests(id_proyecto, clave)
    if not respuesta.ok:
        acumulador.falta("los merge requests: GitLab contesto %d" % respuesta.codigo)
        return []
    salida = []
    for mr in (respuesta.datos() or []):
        if not isinstance(mr, dict):
            continue
        titulo = str(mr.get("title") or "")
        rama = str(mr.get("source_branch") or "")
        if clave.lower() not in (titulo + " " + rama).lower():
            continue
        salida.append({
            "iid": str(mr.get("iid") or ""),
            "title": titulo,
            "state": str(mr.get("state") or ""),
            "source_branch": rama,
            "target_branch": str(mr.get("target_branch") or ""),
            "web_url": str(mr.get("web_url") or ""),
        })
        acumulador.fuente("gitlab:mr:" + str(mr.get("iid")), "gitlab_merge_request",
                          str(mr.get("iid")))
    if not salida:
        acumulador.falta("no hay ningun merge request que nombre %s en el repositorio" % clave)
    return salida


def _contexto_de_codigo(raiz_proyecto, acumulador):
    """El puntero al contexto del codigo. Se referencia, no se copia.

    Se le pide a Knowledge Access, que resuelve donde esta (`rutaCodebase`), aplica el deny
    del proyecto y le saca los secretos al tramo antes de entregarlo (spec 34.2). Lo que
    devuelve `lookup` decide la referencia y lo que se anota:

        OK, y el tramo es un JSON         la ruta relativa que dio Knowledge Access y el
                                          `meta.context_hash` (vacio si el JSON no lo trae);
                                          la fuente `project-context`
        OK, y el tramo no es un JSON      la ruta relativa y el hash vacio, con un hueco que
                                          la nombra; la fuente `project-context`. Un JSON que
                                          la redaccion de secretos dejo invalido es esto
        DOCUMENT_NOT_FOUND                la referencia vacia y el hueco de siempre: no hay
        o CORPUS_UNAVAILABLE              contexto del codigo y lo escribe dev-iniciador-code
        cualquier otro error              la referencia vacia y un hueco que nombra el codigo
                                          (y su motivo, que es de una lista cerrada); sin
                                          fuente: no se entrego nada

    La ruta absoluta del proyecto no sale nunca: ni en la referencia ni en un hueco.
    """
    resultado = acceso.lookup(raiz_proyecto, {"corpus": "codebase", "document": "project-context"})
    if resultado["status"] != "OK":
        error = resultado["error"]
        if error["code"] in ("DOCUMENT_NOT_FOUND", "CORPUS_UNAVAILABLE"):
            acumulador.falta(
                "el contexto del codigo: no hay project-context. Lo escribe dev-iniciador-code "
                "al recorrer el proyecto por primera vez.")
        else:
            acumulador.falta("el contexto del codigo: Knowledge Access no lo entrego (%s%s)" % (
                error["code"], " / " + error["reason"] if error["reason"] else ""))
        return {"path": "", "context_hash": ""}
    item = resultado["items"][0]
    relativa = item["locator"]["path"]
    hash_ = ""
    try:
        documento = json.loads(item["excerpt"]["text"])
    except (ValueError, RecursionError):
        acumulador.falta("el contexto del codigo: %s no se pudo leer" % relativa)
    else:
        meta = documento.get("meta") if isinstance(documento, dict) else None
        hash_ = str((meta.get("context_hash") if isinstance(meta, dict) else None) or "")
    acumulador.fuente("project-context", "project_context", relativa)
    return {"path": relativa, "context_hash": hash_}
