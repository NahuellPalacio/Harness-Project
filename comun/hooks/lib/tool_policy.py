"""Que hace una herramienta, de `tool_name` y la forma real de `tool_input`. Nada semantico.

    READ_ONLY             lee y no cambia nada
    FLOW_RECOVERY         mira o revalida el flujo: flujo --status, contexto, estado, setup
    WORKFLOW_ADVANCING    avanza una etapa: plan, refute --compile/--record/--unit, la delegacion.
                          Solo contexto, plan y refute --compile llevan `reconcilia`: son los que
                          reevaluan su propia compuerta
    MUTATING              escribe en el proyecto
    UNRESOLVED_TOOL_CLASS no se sabe: se trata como MUTATING

Bash y PowerShell se clasifican de forma conservadora: un comando es de lectura solo si cada
segmento es un programa de la lista de lectura, sin redireccion de escritura, sin sustitucion
de comandos y sin asignaciones. No se intenta entender un shell entero: lo que no se reconoce
es UNRESOLVED_TOOL_CLASS.

🔴 Un comando o una ruta que nombra `.env` nunca es READ_ONLY ni FLOW_RECOVERY. La
recuperacion del flujo no abre el `.env`, y leerlo lo sigue impidiendo `permissions.deny`.
"""
import fnmatch
import os
import re
import shlex

READ_ONLY = "READ_ONLY"
FLOW_RECOVERY = "FLOW_RECOVERY"
WORKFLOW_ADVANCING = "WORKFLOW_ADVANCING"
MUTATING = "MUTATING"
UNRESOLVED = "UNRESOLVED_TOOL_CLASS"

# TodoWrite, BashOutput y KillBash llegan porque el matcher no esta anclado (`Write`, `Bash`): leen
# o paran un shell de fondo, no tocan el proyecto.
_HERRAMIENTAS_DE_LECTURA = ("Read", "Glob", "Grep", "LS", "NotebookRead", "TodoWrite", "BashOutput",
                            "KillBash")
_HERRAMIENTAS_QUE_ESCRIBEN = ("Write", "Edit", "MultiEdit", "NotebookEdit")
_DELEGACION = ("Task", "Agent")
_SHELLS = ("Bash", "PowerShell")

CLAVE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$")

# `.env` y `.env.<algo>` como palabra de un comando o como ultimo tramo de una ruta.
_NOMBRA_ENV = re.compile(r"(?:^|[\s\"'=:/\\<>|;&(])\.env(?:\.[\w.-]*)?(?=$|[\s\"';|&)<>])")
_RUTA_ENV = re.compile(r"(?:^|[\\/])\.env(?:\.[^\\/]*)?$")

# Redirecciones que no escriben nada: se sacan antes de mirar el resto.
_INOCUAS = re.compile(r"(?:\s|^)(?:2>&1|[12*]?>\s*(?:/dev/null|\$null|nul)(?=\s|$))", re.I)

_LECTURA_BASH = frozenset((
    "ls", "dir", "pwd", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg", "find",
    "echo", "printf", "which", "where", "type", "file", "stat", "du", "df", "tree", "sort",
    "uniq", "cut", "diff", "cmp", "basename", "dirname", "realpath", "readlink", "date",
    "whoami", "hostname", "uname", "jq", "true", "test", "cd"))
_LECTURA_POWERSHELL = frozenset((
    "get-childitem", "gci", "get-content", "gc", "select-string", "sls", "test-path",
    "get-location", "gl", "get-item", "gi", "resolve-path", "rvpa", "measure-object", "measure",
    "select-object", "select", "where-object", "where", "?", "sort-object", "sort",
    "format-table", "ft", "format-list", "fl", "out-string", "get-date", "write-output",
    "write-host", "echo", "get-command", "gcm", "split-path", "join-path", "get-filehash",
    "compare-object", "group-object", "set-location", "sl", "cat", "type", "ls", "dir", "pwd",
    "cd"))
_ESCRITURA = frozenset((
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "chmod", "chown", "ln", "tee", "truncate", "dd",
    "install", "del", "erase", "rd", "move", "copy", "ren", "rename", "set-content", "sc",
    "add-content", "ac", "out-file", "new-item", "ni", "remove-item", "ri", "move-item", "mi",
    "copy-item", "cpi", "rename-item", "rni", "set-item", "si", "clear-content", "clc"))

_GIT_LECTURA = frozenset((
    "status", "log", "diff", "show", "rev-parse", "ls-files", "ls-tree", "blame", "describe",
    "shortlog", "cat-file", "show-ref", "merge-base", "name-rev", "grep", "whatchanged",
    "count-objects", "rev-list", "for-each-ref", "check-ignore", "var", "help", "version"))
_GIT_ESCRITURA = frozenset((
    "commit", "push", "add", "checkout", "reset", "merge", "rebase", "pull", "fetch", "clone",
    "rm", "mv", "restore", "switch", "cherry-pick", "revert", "clean", "gc", "apply", "am",
    "init", "prune", "filter-branch", "update-ref", "update-index", "notes", "bisect"))
_GIT_OPCIONES_CON_VALOR = ("-C", "-c", "--git-dir", "--work-tree", "--namespace")

_PYTHON = re.compile(r"^(?:python[0-9.]*|py)(?:\.exe)?$", re.I)
# La CLI del Harness es la instalada en ESTE proyecto: relativa, o absoluta dentro de el. Un
# `dev-harness.py` en otra carpeta es un script cualquiera.
_CLI_RELATIVA = ".claude/harness/bin/desarrollo/dev-harness.py"


def _misma(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def _es_la_cli(ruta, proyecto, cwd):
    """La relativa vale si se corre desde la raiz (o si no se sabe desde donde); la absoluta, si es
    la de la raiz. Desde una subcarpeta, la relativa es otro archivo."""
    ruta = ruta.replace("\\", "/")
    if ruta.lower() in (_CLI_RELATIVA, "./" + _CLI_RELATIVA):
        return not (proyecto and cwd) or _misma(cwd, proyecto)
    if not proyecto or not os.path.isabs(ruta):
        return False
    return _misma(ruta, os.path.join(proyecto, *_CLI_RELATIVA.split("/")))
_GLOB = re.compile(r"[*?\[]")


def _nombra_env_en(tokens):
    """Un token que es el `.env`, o un glob que lo alcanza (`.en?`, `.[e]nv`, `*`)."""
    for tok in tokens:
        tramo = os.path.basename(tok.rstrip("/")).lower()
        if tramo == ".env" or tramo.startswith(".env."):
            return True
        if _GLOB.search(tramo) and (fnmatch.fnmatchcase(".env", tramo)
                                    or fnmatch.fnmatchcase(".env.local", tramo)):
            return True
    return False


def _resultado(clase, razon, clave=None, etapa=None, reconcilia=False):
    return {"class": clase, "reason": razon, "taskKey": clave, "stage": etapa,
            "reconcilia": reconcilia}


# -- el comando del Harness ----------------------------------------------------

_FLAGS_DE_LECTURA_HARNESS = frozenset(("--json", "--verbose"))


def _harness(argumentos):
    """dev-harness.py <subcomando> [<clave>] [flags]."""
    if not argumentos:
        return _resultado(UNRESOLVED, "dev-harness.py sin subcomando")
    sub, resto = argumentos[0], argumentos[1:]
    clave = resto[0] if resto and CLAVE.match(resto[0]) else None
    flags = set(a.split("=", 1)[0] for a in resto if a.startswith("--"))
    if "--proyecto" in flags:
        return _resultado(UNRESOLVED, "dev-harness.py sobre otro proyecto", clave)
    if sub == "harness":
        if flags <= _FLAGS_DE_LECTURA_HARNESS:
            return _resultado(READ_ONLY, "dev-harness.py harness")
        return _resultado(MUTATING, "dev-harness.py harness que escribe")
    if sub == "flujo":
        if clave and "--status" in flags and flags <= {"--status", "--json"}:
            return _resultado(FLOW_RECOVERY, "flujo --status", clave)
        return _resultado(UNRESOLVED, "flujo sin --status", clave)
    if sub == "contexto":
        if clave and flags <= {"--revalidar", "--json"}:
            return _resultado(FLOW_RECOVERY, "contexto", clave, "CONTEXT", True)
        return _resultado(UNRESOLVED, "contexto sin clave", clave)
    if sub in ("estado", "setup", "reconfigurar"):
        return _resultado(FLOW_RECOVERY, sub)
    if sub == "fuentes":
        if "--aceptar" in flags:
            return _resultado(MUTATING, "fuentes --aceptar")
        return _resultado(FLOW_RECOVERY, "fuentes")
    if sub == "plan":
        if not clave:
            return _resultado(UNRESOLVED, "plan sin clave")
        if "--plantilla" in flags:
            return _resultado(READ_ONLY, "plan --plantilla", clave)
        return _resultado(WORKFLOW_ADVANCING, "plan", clave, "PLANNING", True)
    if sub == "refute":
        if not clave:
            return _resultado(UNRESOLVED, "refute sin clave")
        if "--compile" in flags:
            return _resultado(WORKFLOW_ADVANCING, "refute --compile", clave, "REFUTATION", True)
        if "--record" in flags:
            # Reconcilia pero no tiene compuerta propia: no revalida nada.
            return _resultado(WORKFLOW_ADVANCING, "refute --record", clave, "REFUTATION")
        if "--unit" in flags:
            return _resultado(WORKFLOW_ADVANCING, "refute --unit", clave, "REFUTATION")
        if flags & {"--status", "--summary"}:
            return _resultado(READ_ONLY, "refute --status", clave)
        return _resultado(UNRESOLVED, "refute sin accion", clave)
    if sub == "seguridad":
        return _resultado(MUTATING, "seguridad", clave)
    if sub == "contabilidad":
        if flags <= {"--barra", "--sesion", "--json"} and "--barra" in flags:
            return _resultado(READ_ONLY, "contabilidad --barra")
        return _resultado(MUTATING, "contabilidad")
    return _resultado(UNRESOLVED, "dev-harness.py %s" % sub, clave)


# -- un comando de shell -------------------------------------------------------

def _tokens(comando):
    """Las palabras y los operadores. Las barras invertidas pasan a `/`: son rutas de Windows,
    no escapes, y shlex en modo posix se las comeria."""
    lexer = shlex.shlex(comando.replace("\\", "/"), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


_SEPARADORES = frozenset(("|", "||", "&&", ";", "&", "\n"))


def _segmentos(tokens, powershell):
    segmentos, actual = [], []
    for tok in tokens:
        if tok in _SEPARADORES:
            if tok == "&" and powershell and not actual:
                continue                         # el operador de llamada de PowerShell
            segmentos.append(actual)
            actual = []
        else:
            actual.append(tok)
    segmentos.append(actual)
    return [s for s in segmentos if s]


def _programa(palabra):
    nombre = os.path.basename(palabra.replace("\\", "/")).lower()
    return nombre[:-4] if nombre.endswith(".exe") else nombre


def _git(argumentos):
    i = 0
    while i < len(argumentos) and argumentos[i].startswith("-"):
        opcion = argumentos[i].split("=", 1)[0]
        if opcion in ("-c", "--config-env", "--exec-path", "-C", "--git-dir", "--work-tree"):
            # Una configuracion -la de la linea o la de otro repositorio, con su core.fsmonitor-
            # puede correr un programa.
            return UNRESOLVED
        i += 2 if opcion in _GIT_OPCIONES_CON_VALOR and "=" not in argumentos[i] else 1
    if i >= len(argumentos):
        return READ_ONLY
    sub, resto = argumentos[i], argumentos[i + 1:]
    posicionales = [a for a in resto if not a.startswith("-")]
    if any(a.startswith("--output") for a in resto):
        return MUTATING
    if any(a == "--ext-diff" or a.startswith("-O") or a.startswith("--open-files-in-pager")
           for a in resto):
        return UNRESOLVED                        # corren un programa externo
    if sub in _GIT_LECTURA:
        return READ_ONLY
    if sub == "branch":
        lectura = {"-a", "-r", "-v", "-vv", "--list", "-l", "--show-current", "--all",
                   "--remotes", "--verbose"}
        return READ_ONLY if not posicionales and set(resto) <= lectura else MUTATING
    if sub == "remote":
        if not resto or set(resto) <= {"-v", "--verbose"}:
            return READ_ONLY
        return READ_ONLY if resto[0] in ("get-url", "show") else MUTATING
    if sub == "tag":
        return READ_ONLY if not resto or resto[0] in ("-l", "--list") else MUTATING
    if sub == "config":
        return READ_ONLY if resto and resto[0] in ("--get", "--get-all", "--list", "-l",
                                                   "--get-regexp") else MUTATING
    if sub == "stash":
        return READ_ONLY if resto and resto[0] in ("list", "show") else MUTATING
    if sub == "reflog":
        return READ_ONLY if not resto or resto[0] == "show" else MUTATING
    if sub in ("worktree", "submodule"):
        return READ_ONLY if resto and resto[0] in ("list", "status") else MUTATING
    if sub in _GIT_ESCRITURA:
        return MUTATING
    return UNRESOLVED


def _segmento(palabras, powershell):
    """La clase de un segmento simple: un programa y sus argumentos."""
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", palabras[0]):
        return UNRESOLVED
    programa, argumentos = _programa(palabras[0]), palabras[1:]
    if programa in _ESCRITURA:
        return MUTATING
    if programa == "git":
        return _git(argumentos)
    # En PowerShell tambien valen los de Bash: con Git en el PATH, `head` es el de Git.
    lectura = (_LECTURA_POWERSHELL | _LECTURA_BASH) if powershell else _LECTURA_BASH
    if programa not in lectura:
        return UNRESOLVED
    if programa == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir",
                                        "-fprint", "-fprintf", "-fls") for a in argumentos):
        return MUTATING
    if programa in ("sort", "tree") and any(a == "-o" or a.startswith("--output")
                                            for a in argumentos):
        return MUTATING
    if programa == "rg" and any(a.startswith("--pre") for a in argumentos):
        return UNRESOLVED                        # --pre corre un programa por archivo
    if programa == "hostname" and any(not a.startswith("-") for a in argumentos):
        return UNRESOLVED                        # con un nombre, lo cambia
    if programa == "date" and any(a in ("-s", "--set") or a.startswith("--set=")
                                  for a in argumentos):
        return UNRESOLVED
    return READ_ONLY


def _shell(tool, comando, proyecto=None, cwd=None):
    if not isinstance(comando, str) or not comando.strip():
        return _resultado(UNRESOLVED, "comando vacio")
    if _NOMBRA_ENV.search(comando):
        return _resultado(UNRESOLVED, "nombra .env")
    powershell = tool == "PowerShell"
    if "$(" in comando or (not powershell and "`" in comando):
        return _resultado(UNRESOLVED, "sustitucion de comandos")
    if powershell and ("{" in comando or "}" in comando):
        return _resultado(UNRESOLVED, "un scriptblock de PowerShell")
    limpio = _INOCUAS.sub(" ", comando.replace("\r\n", "\n"))
    try:
        tokens = _tokens(limpio.replace("\n", " ; "))
    except ValueError:
        return _resultado(UNRESOLVED, "comillas sin cerrar")
    if any(">" in tok for tok in tokens if set(tok) <= set("<>&|;()0123456789*")):
        return _resultado(MUTATING, "redireccion de escritura")
    if any(tok in ("<", "(", ")", "<<", "<<<") for tok in tokens):
        return _resultado(UNRESOLVED, "redireccion o subshell")
    if _nombra_env_en(tokens):
        return _resultado(UNRESOLVED, "nombra .env")
    # Una variable puede valer cualquier ruta, el .env tambien: no se sabe que lee.
    if any("$" in tok and tok.lower() != "$null" for tok in tokens):
        return _resultado(UNRESOLVED, "una variable")
    segmentos = _segmentos(tokens, powershell)
    if not segmentos:
        return _resultado(UNRESOLVED, "comando vacio")
    # Un comando del Harness, solo: `python <...>/dev-harness.py <subcomando> ...`.
    if len(segmentos) == 1 and len(segmentos[0]) >= 2 and _PYTHON.match(
            _programa(segmentos[0][0])) and _es_la_cli(segmentos[0][1], proyecto, cwd):
        return _harness(segmentos[0][2:])
    clases = [_segmento(s, powershell) for s in segmentos]
    if MUTATING in clases:
        return _resultado(MUTATING, "un segmento escribe")
    if all(c == READ_ONLY for c in clases):
        return _resultado(READ_ONLY, "todos los segmentos leen")
    return _resultado(UNRESOLVED, "un segmento no se reconoce")


# -- la herramienta ------------------------------------------------------------

def _nombra_env(entrada):
    for campo in ("file_path", "notebook_path", "path"):
        valor = entrada.get(campo)
        if isinstance(valor, str) and _RUTA_ENV.search(valor.strip()):
            return True
    return False


def clasificar(tool_name, tool_input, proyecto=None, cwd=None):
    """{class, reason, taskKey, stage, reconcilia}. Determinista: la misma entrada, la misma clase.

    `proyecto` es la raiz y `cwd` desde donde corre el comando: la CLI es la de esa raiz.

    `taskKey` es la clave de un comando del Harness; `stage`, la etapa que corre un comando que
    avanza; `reconcilia`, si ese comando reevalua su compuerta y reconcilia el estado.
    """
    entrada = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in _SHELLS:
        return _shell(tool_name, entrada.get("command"), proyecto, cwd)
    if _nombra_env(entrada):
        return _resultado(UNRESOLVED, "nombra .env")
    if tool_name in _HERRAMIENTAS_DE_LECTURA:
        return _resultado(READ_ONLY, tool_name)
    if tool_name in _HERRAMIENTAS_QUE_ESCRIBEN:
        return _resultado(MUTATING, tool_name)
    if tool_name in _DELEGACION:
        return _resultado(WORKFLOW_ADVANCING, "delegacion", etapa="EXECUTION")
    return _resultado(UNRESOLVED, str(tool_name or "sin nombre"))
