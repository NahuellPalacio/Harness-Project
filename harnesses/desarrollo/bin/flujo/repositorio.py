"""De que repositorio es la tarea, y si este checkout es ese.

    la tarea     GITLAB_PROJECT (via entorno.py) y las URLs de GitLab de la Ficha
    el checkout  todos los remotos de `git remote -v`, que es local y no sale a la red
    el estado    MATCHED, MISMATCH o UNRESOLVED, con el codigo del input que fallo

🔴 Compara, no elige. Dos declaraciones distintas del repositorio de la tarea son un
conflicto, no una precedencia: quedarse con la primera es exactamente lo que hacia el
resolvedor del TaskContext, y nadie se enteraba de que la otra existia.

🔴 Nunca se asume que `cwd` es el repositorio correcto. Y nunca se guarda la URL de un remoto:
una `https://oauth2:<token>@host/...` es un secreto con forma de URL. Lo que sale de aca es
la identidad normalizada, `host/grupo/proyecto`, y nada mas.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contexto import repositorio as contexto_repositorio   # noqa: E402

MATCHED = "MATCHED"
MISMATCH = "MISMATCH"
UNRESOLVED = "UNRESOLVED"

REPOSITORY_UNRESOLVED = "REPOSITORY_UNRESOLVED"
REPOSITORY_CONFLICT = "REPOSITORY_CONFLICT"
LOCAL_REPOSITORY_UNRESOLVED = "LOCAL_REPOSITORY_UNRESOLVED"
REPOSITORY_MISMATCH = "REPOSITORY_MISMATCH"

# Que input del registro representa cada codigo.
INPUT_DE = {REPOSITORY_UNRESOLVED: "repository.task",
            REPOSITORY_CONFLICT: "repository.unambiguous",
            LOCAL_REPOSITORY_UNRESOLVED: "repository.local",
            REPOSITORY_MISMATCH: "repository.match"}

# El usuario y la contrasena llegan hasta el ULTIMO `@` antes de la primera barra: una
# contrasena con un `@` sin codificar no puede dejar un pedazo pegado al host.
_URL = re.compile(r"^(?:https?|ssh|git)://(?:[^/\s]*@)?([^/:?#\s@]+)(?::[0-9]*)?(/[^?#\s]*)?",
                  re.IGNORECASE)
# `usuario@host:grupo/proyecto`. Un host de una sola letra es una unidad de Windows.
_SCP = re.compile(r"^(?:[^@/\s]+@)?([^:/\s]{2,}):(?!//)([^\s]+)$")
_CAMINO = re.compile(r"^[A-Za-z0-9_.~-]+(/[A-Za-z0-9_.~-]+)+/?$")


def _limpiar_camino(camino):
    camino = (camino or "").split("/-/")[0]
    partes = [p for p in camino.strip().split("/") if p]
    if partes and partes[-1].lower().endswith(".git"):
        partes[-1] = partes[-1][:-4]
    partes = [p for p in partes if p]
    return "/".join(partes).lower() if len(partes) >= 2 else None


def _host_de(base_url):
    m = _URL.match(str(base_url or "").strip())
    return m.group(1).lower() if m else None


def normalizar(referencia, base_url=None):
    """(host, camino) de una URL, un remoto SCP o un `grupo/proyecto`, o None.

    El host es None solo para un `grupo/proyecto` sin base URL conocida. Un id numerico no
    se normaliza: sin preguntarle a GitLab no hay con que compararlo.
    """
    texto = str(referencia or "").strip()
    if not texto:
        return None
    m = _URL.match(texto)
    if m:
        camino = _limpiar_camino(m.group(2) or "")
        return (m.group(1).lower(), camino) if camino else None
    m = _SCP.match(texto)
    if m:
        camino = _limpiar_camino(m.group(2))
        return (m.group(1).lower(), camino) if camino else None
    if _CAMINO.match(texto):
        camino = _limpiar_camino(texto)
        return (_host_de(base_url), camino) if camino else None
    return None


def como_texto(identidad):
    if identidad is None:
        return None
    host, camino = identidad
    return "%s/%s" % (host, camino) if host else camino


def iguales(a, b):
    """Mismo camino, y mismo host si los dos lo conocen."""
    if a is None or b is None:
        return False
    return a[1] == b[1] and (a[0] is None or b[0] is None or a[0] == b[0])


# -- la tarea ------------------------------------------------------------------

def urls_de_la_ficha(ficha):
    """Todas las URLs de GitLab de la Ficha, en orden y sin repetir. No se elige ninguna."""
    texto = " ".join(str((ficha or {}).get(c) or "") for c in contexto_repositorio.CAMPOS_DE_FICHA)
    vistas = []
    for url in contexto_repositorio.RE_URL_GITLAB.findall(texto):
        if url not in vistas:
            vistas.append(url)
    return vistas


def _web_url_resuelta(task_context, declarado):
    """El web_url que GitLab devolvio para ESTE id, si el TaskContext lo resolvio."""
    repo = (task_context or {}).get("repository") or {}
    proyecto = repo.get("project") or {}
    fuentes = [s for s in (task_context or {}).get("sources") or []
               if isinstance(s, dict) and s.get("type") == "gitlab_project"]
    if str(proyecto.get("id") or "") == declarado or any(
            str(s.get("reference") or "") == declarado for s in fuentes):
        return str(proyecto.get("web_url") or "")
    return ""


def de_la_tarea(task_context, gitlab):
    """(identidad o None, codigo o None, declaradoPor, candidatos). Nunca elige entre dos.

    `candidatos` son todas las identidades distintas que se declararon, ordenadas. Con un
    conflicto es lo que la persona tiene que mirar para decidir; no hay una "primera".
    """
    gitlab = gitlab or {}
    declaraciones, sin_normalizar = [], []
    declarado = str(gitlab.get("gitlabProyecto") or "").strip()
    if declarado:
        ident = normalizar(declarado, gitlab.get("baseUrl"))
        if ident is None and declarado.isdigit():
            ident = normalizar(_web_url_resuelta(task_context, declarado))
        if ident is None:
            sin_normalizar.append("GITLAB_PROJECT")
        else:
            declaraciones.append(("GITLAB_PROJECT", ident))
    ficha = ((task_context or {}).get("project") or {}).get("ficha") or {}
    for url in urls_de_la_ficha(ficha):
        ident = normalizar(url)
        if ident is not None:
            declaraciones.append(("FICHA", ident))

    distintas = []
    for _, ident in declaraciones:
        if not any(iguales(ident, otra) for otra in distintas):
            distintas.append(ident)
    por = sorted(set(origen for origen, _ in declaraciones) | set(sin_normalizar))
    candidatos = sorted(como_texto(i) for i in distintas)
    if len(distintas) > 1:
        return None, REPOSITORY_CONFLICT, por, candidatos
    if sin_normalizar or not distintas:
        return None, REPOSITORY_UNRESOLVED, por, candidatos
    # Si una declaracion no trae host y otra si, se queda la que lo trae: son la misma.
    completa = next((i for _, i in declaraciones if i[0]), distintas[0])
    return completa, None, por, candidatos


# -- el checkout ---------------------------------------------------------------

def remotos(proyecto):
    """[(nombre, identidad)] de los remotos de fetch, o None si no es un repositorio git.

    Solo `git remote -v`: no hay `fetch`, ni `ls-remote`, ni red. Un remoto que no se puede
    normalizar -una ruta local- no cuenta como identidad.
    """
    try:
        salida = subprocess.run(["git", "-C", proyecto, "remote", "-v"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if salida.returncode != 0:
        return None
    vistos = []
    for linea in salida.stdout.decode("utf-8", "replace").splitlines():
        partes = linea.split()
        if len(partes) < 3 or partes[2] != "(fetch)":
            continue
        ident = normalizar(partes[1])
        if ident is not None and (partes[0], ident) not in vistos:
            vistos.append((partes[0], ident))
    return sorted(vistos)


# -- la identidad ---------------------------------------------------------------

def identidad(task_context, gitlab, proyecto):
    """La identidad del repositorio de la tarea contra este checkout. Determinista."""
    de_tarea, codigo, por, candidatos = de_la_tarea(task_context, gitlab)
    locales = remotos(proyecto)
    hechos = {"repository.task": codigo != REPOSITORY_UNRESOLVED,
              "repository.unambiguous": None if codigo == REPOSITORY_UNRESOLVED
              else codigo != REPOSITORY_CONFLICT,
              "repository.local": bool(locales),
              "repository.match": None}
    if codigo is None and not locales:
        codigo = LOCAL_REPOSITORY_UNRESOLVED
    elif codigo is None:
        coincide = any(iguales(de_tarea, ident) for _, ident in locales)
        hechos["repository.match"] = coincide
        if not coincide:
            codigo = REPOSITORY_MISMATCH
    if codigo is None:
        estado = MATCHED
    elif codigo == REPOSITORY_MISMATCH:
        estado = MISMATCH
    else:
        estado = UNRESOLVED
    return {"status": estado,
            "failureCode": codigo,
            "taskRepository": como_texto(de_tarea),
            "declaredBy": por,
            "candidates": candidatos,
            "localRepositories": sorted(set(como_texto(i) for _, i in locales or [])),
            "facts": hechos}
