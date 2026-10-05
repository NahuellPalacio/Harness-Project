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

# La autoridad del flujo, y lo que ejecuta codigo por su cuenta: `.claude/` entero (el estado, los
# bindings, los intents, las decisiones, el plan, el TaskContext, la refutacion, la CLI y los hooks
# instalados, los settings) y `.git/` entero (core.fsmonitor, los hooks de git). Los escriben los
# hooks, la CLI del Harness y git; una herramienta del modelo, nunca (Wave 4). Leerlos si se puede.
_AUTORIDAD = re.compile(r"(?:^|[/\s\"'=:(;&|<>])\.(?:claude|git)(?=[/\s\"');&|<>]|$)", re.I)


_CARPETAS_DE_AUTORIDAD = (".claude", ".git")
_PEGADA_A_UNA_OPCION = re.compile(r"^-+[A-Za-z0-9]*\.(?:claude|git)$", re.I)


def _palabras(texto, tolerante):
    """Las palabras de un texto como las lee el shell, o None si tiene comillas sin cerrar y no es
    `tolerante`. Una ruta o un valor de una herramienta que no es shell no pasa por un shell: una
    comilla es un caracter mas (`Don't`, `O'Brien.py`), y se parte por los espacios."""
    try:
        return _tokens(texto)
    except ValueError:
        return texto.replace("\\", "/").split() if tolerante else None


def toca_autoridad(texto, tolerante=False):
    """Si un texto nombra `.claude` o `.git` como tramo de una ruta: en el texto crudo y en cada
    palabra del comando, que es como lo va a leer el shell (`cd .claude;` o `cd .claude&&echo`).
    En un comando, comillas sin cerrar son «ante la duda, si»; `tolerante` es para lo que no es un
    comando (ver `_palabras`)."""
    if not isinstance(texto, str):
        return False
    if _AUTORIDAD.search(texto.replace("\\", "/")):
        return True
    palabras = _palabras(texto, tolerante)
    if palabras is None:
        return True                                    # comillas sin cerrar: ante la duda, si
    for palabra in palabras:
        for tramo in palabra.replace("\\", "/").split("/"):
            if tramo.rstrip(" .").lower() in (".claude", ".git") or tramo.lower() in (".claude", ".git"):
                return True
            if _PEGADA_A_UNA_OPCION.match(tramo.rstrip(" .")):   # `-o.claude/...`
                return True
    return False


def _normalizada(ruta, base):
    """La ruta como la va a abrir el sistema: contra `base`, sin `.`, `..` ni barras dobles, sin
    los puntos y espacios finales que Windows ignora, y con los enlaces resueltos."""
    ruta = ruta.replace("\\", "/")
    if base and not os.path.isabs(ruta):
        ruta = base.replace("\\", "/").rstrip("/") + "/" + ruta
    tramos = [t if t in (".", "..") else t.rstrip(" .") or t for t in ruta.split("/")]
    ruta = os.path.normpath("/".join(tramos))
    try:
        ruta = os.path.realpath(ruta)
    except (OSError, ValueError):
        pass
    return os.path.normcase(ruta)


# Lo que Python, PowerShell o git ejecutan por su cuenta en cada hook o comando, fuera de
# .claude/ y .git/ (Wave 6): `usercustomize.py`, `sitecustomize.py`, un `.pth`, un perfil de
# PowerShell, un `.gitconfig`. Con estado del flujo ninguna herramienta los escribe, en el
# proyecto ni en el host. Lo plantado antes, o por fuera de las herramientas del modelo, es un
# limite escrito (docs/cambios/flow-governance/qualification-readiness.md).
_PERSISTENCIA = re.compile(
    r"(?:^|[\\/\s\"'=:(;&|<>~])(?:usercustomize\.py|sitecustomize\.py|[^\\/\s\"';&|<>]*\.pth"
    r"|[^\\/\s\"';&|<>]*profile\.ps1|\.gitconfig)(?=[\s\"');&|<>:]|$)"
    r"|\$\{?profile\}?|(?:^|[\\/])site-packages(?=[\\/\s\"']|$)"
    r"|\.config[\\/]git[\\/]config(?=[\s\"');&|<>:]|$)", re.I)


_NOMBRE_CORTO = re.compile(r"~\d")
_MSYS = re.compile(r"^/([A-Za-z])(/|$)")


def _como_rutas(palabra):
    """Las rutas que una palabra del comando puede abrir, en las formas que el texto deja ver: sin
    redirecciones pegadas; el valor de una opcion pegado con `=` (`--target-directory=x`), con `:`
    (`-Path:x`, PowerShell) o detras de una opcion corta (`-ox`, `-uox`); `/c/x` de Git Bash como
    `c:/x` y `~` expandido."""
    palabra = palabra.lstrip("<>&|0123456789")
    candidatas = [palabra]
    if palabra.startswith("-"):
        if "=" in palabra:
            candidatas.append(palabra.split("=", 1)[1])
        if ":" in palabra:
            candidatas.append(palabra.split(":", 1)[1])
        if not palabra.startswith("--"):
            candidatas.extend(palabra[k:] for k in range(2, min(len(palabra), 10)))
    salida = []
    for c in candidatas:
        c = _MSYS.sub(lambda m: m.group(1) + ":/", c.strip("'\"").replace("\\", "/"))
        salida.append(os.path.expanduser(c) if c.startswith("~") else c)
    return salida


def toca_persistencia(texto, tolerante=False):
    """Si un texto nombra un punto de persistencia del host: un archivo que Python, PowerShell o
    git ejecutan solos. Cada palabra pasa por la misma regla que una ruta de Write; una con un
    nombre corto 8.3 (`GITCON~1`) se resuelve ademas contra el disco. `tolerante`, como en
    `toca_autoridad`."""
    if not isinstance(texto, str):
        return False
    if _PERSISTENCIA.search(texto.replace("\\", "/")):
        return True
    palabras = _palabras(texto, tolerante)
    if palabras is None:
        return True                                    # comillas sin cerrar: ante la duda, si
    if _escribe_config_de_git(palabras, tolerante):
        return True
    return any(es_ruta_de_persistencia(c, resolver=bool(_NOMBRE_CORTO.search(c)))
               for p in palabras for c in _como_rutas(p))


def _planas(palabras, hondura=0, tolerante=False):
    """Las palabras con las que van entre comillas abiertas en las suyas: `bash -c "git ..."`,
    `Start-Process git 'config ...'`, y un arreglo de PowerShell por sus comas
    (`-ArgumentList 'config','--global'`). Levanta ValueError con comillas sin cerrar."""
    salida = []
    for p in palabras:
        if hondura < 2 and re.search(r"\s", p.strip()):
            interiores = _palabras(p, tolerante)
            if interiores is None:
                raise ValueError("comillas sin cerrar")
            salida.extend(_planas(interiores, hondura + 1, tolerante))
        elif "," in p:
            salida.extend(t for t in p.split(",") if t)
        else:
            salida.append(p)
    return salida


def _escribe_config_de_git(palabras, tolerante=False):
    """Si las palabras de un comando corren un `git config` que escribe, con cualquier alcance: la
    configuracion del repositorio es `.git/config`, autoridad del flujo desde la Wave 4, y la global,
    la del sistema o un `--file` son persistencia del host. Sin excepcion por clave (decision del
    02-10-2026). Usa el mismo parser que decide si `config` lee. El git
    puede venir detras de otro programa (`cmd /c git ...`, `Start-Process git`), adentro de una
    palabra entre comillas, o en un alias de `-c` (`alias.x=config ...`, `alias.x=!git config ...`)."""
    try:
        planas = _planas(palabras, tolerante=tolerante)
    except ValueError:
        return True                                    # comillas sin cerrar: ante la duda, si
    for segmento in _segmentos(planas, False):
        for n, palabra in enumerate(segmento):
            alias = palabra.lower().startswith("alias.") and "=" in palabra
            valor = palabra.rsplit("=", 1)[-1].lstrip("!") if alias else palabra
            resto = None
            if _programa(valor) == "git":
                sub, args = _subcomando_de_git(segmento[n + 1:])
                resto = args if sub == "config" else None
                detras = n > 0 or alias                # otro programa lo corre: puede agregarle
            elif alias and valor == "config":
                resto = segmento[n + 1:]               # un alias que corre `config`
                detras = True
            if resto is not None:
                clase, alcances = _config_de_git(resto, puede_crecer=detras)
                if clase == MUTATING:                  # cualquier alcance, tambien .git/config
                    return True
    return False


def _tramos(ruta):
    """Los segmentos de una ruta como los ve el sistema: sin el stream de NTFS (`x::$DATA`,
    `x:stream`) ni los puntos y espacios finales que Windows ignora. La letra de unidad queda."""
    salida = []
    for n, tramo in enumerate(t for t in ruta.replace("\\", "/").split("/") if t):
        if not (n == 0 and re.match(r"^[A-Za-z]:$", tramo)):
            tramo = tramo.split(":")[0]
        salida.append(tramo.rstrip(" .").lower())
    return [t for t in salida if t]


def es_ruta_de_persistencia(ruta, resolver=True):
    """Si una ruta de archivo es un punto de persistencia del host, por sus segmentos. `resolver`
    la pasa ademas por el disco: un nombre corto 8.3 es el mismo archivo."""
    if not isinstance(ruta, str) or not ruta.strip():
        return False
    rutas = [ruta]
    if resolver:
        try:
            rutas.append(os.path.realpath(ruta))
        except (OSError, ValueError):
            pass
    for r in rutas:
        partes = _tramos(r)
        if not partes:
            continue
        if "site-packages" in partes:                # adentro, o la carpeta como destino
            return True
        if partes[-3:] == [".config", "git", "config"]:
            return True                                # la configuracion global de git, en XDG
        nombre = partes[-1]
        if nombre in ("usercustomize.py", "sitecustomize.py", ".gitconfig") \
                or nombre.endswith(".pth") or nombre.endswith("profile.ps1"):
            return True
    return False


def es_ruta_de_autoridad(ruta, proyecto=None, cwd=None):
    """Si una ruta de archivo cae adentro de la autoridad del flujo de `proyecto`. Mira la ruta
    normalizada, no el texto: `.claude/./runtime` o `.claude./runtime` son la misma carpeta."""
    if not isinstance(ruta, str) or not ruta.strip():
        return False
    final = _normalizada(ruta, cwd or proyecto)
    if toca_autoridad(final, tolerante=True) or toca_autoridad(ruta, tolerante=True):
        return True
    if not proyecto:
        return False
    raiz = _normalizada(proyecto, None)
    for carpeta in _CARPETAS_DE_AUTORIDAD:
        guarda = os.path.join(raiz, carpeta)
        if final == guarda or final.startswith(guarda + os.sep):
            return True
    return False
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


def _resultado(clase, razon, clave=None, etapa=None, reconcilia=False, intencion=None):
    return {"class": clase, "reason": razon, "taskKey": clave, "stage": etapa,
            "reconcilia": reconcilia, "humanIntent": intencion, "protected": False}


def _valor(argumentos, flag):
    """El valor de `--flag v` o `--flag=v`, o None."""
    for i, a in enumerate(argumentos):
        if a == flag and i + 1 < len(argumentos):
            return argumentos[i + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


# Los comandos que aplican una decision humana (Wave 4): FLOW_RECOVERY solo con un intent valido,
# que la compuerta busca en la sesion del evento.
_DECISIONES = {"--approve": "APPROVE", "--alternative": "USE_ALTERNATIVE", "--choose": "CHOOSE",
               "--cancel": "CANCEL", "--answer": "ANSWER"}


# -- el comando del Harness ----------------------------------------------------

_FLAGS_DE_LECTURA_HARNESS = frozenset(("--json", "--verbose"))


def _harness(argumentos):
    """dev-harness.py <subcomando> [<clave>] [flags]."""
    if not argumentos:
        return _resultado(UNRESOLVED, "dev-harness.py sin subcomando")
    sub, resto = argumentos[0], argumentos[1:]
    clave = resto[0] if resto and CLAVE.match(resto[0]) else None
    repetidos = [a for a in resto if a.startswith("--")]
    if len(set(a.split("=", 1)[0] for a in repetidos)) != len(repetidos):
        # Un flag dos veces: la compuerta leeria uno y la CLI otro.
        return _resultado(UNRESOLVED, "dev-harness.py con un flag repetido", clave)
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
        if clave and flags == {"--resume"}:
            return _resultado(FLOW_RECOVERY, "flujo --resume", clave)
        pedidas = [f for f in _DECISIONES if f in flags]
        if clave and len(pedidas) == 1 and flags <= {pedidas[0], "--option", "--value", "--sesion"}:
            return _resultado(FLOW_RECOVERY, "flujo %s" % pedidas[0], clave, intencion={
                "action": _DECISIONES[pedidas[0]], "interactionId": _valor(resto, pedidas[0]),
                "option": _valor(resto, "--option") or _valor(resto, "--value"),
                "sesion": _valor(resto, "--sesion")})
        return _resultado(UNRESOLVED, "flujo sin una accion conocida", clave)
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
        # Se evalua contra la tarea de la sesion, no contra la clave que nombra: no avanza
        # ninguna etapa, y evaluarla por su clave dejaria a una sesion bloqueada operar sobre
        # otra tarea. La clave viaja aparte, para que el motivo diga a que apuntaba (Wave 6).
        salida = _resultado(MUTATING, "contabilidad")
        salida["target"] = clave
        return salida
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
        return _config_de_git(resto)[0]
    if sub == "stash":
        return READ_ONLY if resto and resto[0] in ("list", "show") else MUTATING
    if sub == "reflog":
        return READ_ONLY if not resto or resto[0] == "show" else MUTATING
    if sub in ("worktree", "submodule"):
        return READ_ONLY if resto and resto[0] in ("list", "status") else MUTATING
    if sub in _GIT_ESCRITURA:
        return MUTATING
    return UNRESOLVED


# Los alcances de `git config`. git lee una opcion larga abreviada si no hay otra que empiece
# igual (`--glob` es `--global`), y `-f` sola o pegada a su valor (`-fx`). Una abreviatura que git
# rechazaria por ambigua (`--g`) se lee igual como alcance: ante la duda, el alcance.
_CONFIG_ALCANCES = ("global", "system", "local", "worktree", "file", "blob", "includes")
_CONFIG_CON_VALOR = frozenset(("file", "blob"))
_CONFIG_LECTURA = ("--get", "--get-all", "--list", "-l", "--get-regexp", "--get-urlmatch",
                   "--get-color", "--get-colorbool")
# Los subcomandos de la sintaxis nueva (git 2.46): `get` y `list` leen; los demas escriben.
_CONFIG_SUBCOMANDOS_DE_LECTURA = ("get", "list")
_CONFIG_SUBCOMANDOS_DE_ESCRITURA = ("set", "unset", "rename-section", "remove-section", "edit")
# Lo que cambia como se muestra, no que se hace: no es la accion.
_CONFIG_MODIFICADORES = frozenset(("--show-origin", "--show-scope", "--name-only", "--null", "-z",
                                   "--fixed-value", "--no-includes", "--bool", "--int",
                                   "--bool-or-int", "--path", "--expiry-date", "--no-type"))
_CONFIG_MODIFICADORES_CON_VALOR = frozenset(("--type", "-t", "--default", "--comment", "--value",
                                             "--url"))


def _alcance_de_config(argumento):
    """(alcance, cuantas palabras ocupa) si `argumento` es un alcance de `git config`, o (None, 0)."""
    if argumento.startswith("--"):
        nombre, igual, _ = argumento[2:].partition("=")
        candidatos = [a for a in _CONFIG_ALCANCES if nombre and a.startswith(nombre.lower())]
        if len(candidatos) != 1:
            return None, 0
        alcance = candidatos[0]
        return alcance, 2 if alcance in _CONFIG_CON_VALOR and not igual else 1
    if argumento.startswith("-") and len(argumento) > 1:
        for n, letra in enumerate(argumento[1:]):
            if letra == "f":                           # -f, -fx, -zf x
                return "file", 1 if argumento[n + 2:] else 2
            if letra == "t":                           # -t lleva el tipo pegado o despues
                break
    return None, 0


def _config_de_git(resto, puede_crecer=False):
    """(clase, alcances) de `git config <resto>`. Ni el alcance ni un modificador (`--show-origin`,
    `--type=bool`, `-z`) dicen si lee o escribe: lo dice la accion, lo que queda. Lee con una
    opcion de lectura (`--get`, `--list`...), con `get` o `list`, o con un nombre solo
    (`git config user.email`); un nombre con su valor, o cualquier otra accion, escribe. Los
    alcances se juntan de todas las palabras, porque git acepta las opciones despues de la accion.

    `puede_crecer`: git corre detras de otro programa que puede agregarle argumentos al correr
    (`xargs git config core.fsmonitor`). Ahi un nombre solo no es una lectura: el valor puede
    venir despues."""
    alcances, accion, i = set(), [], 0
    while i < len(resto):
        if resto[i] == "--":
            accion.extend(resto[i + 1:])
            break
        alcance, ocupa = _alcance_de_config(resto[i])
        if alcance:
            alcances.add(alcance)
            i += ocupa
            continue
        opcion, igual, _ = resto[i].partition("=")
        if opcion in _CONFIG_MODIFICADORES:
            i += 1
            continue
        if opcion in _CONFIG_MODIFICADORES_CON_VALOR:
            i += 1 if igual else 2
            continue
        accion.append(resto[i])
        i += 1
    if not accion:
        return MUTATING, alcances                      # `git config` solo no se sabe: escritura
    primera = accion[0]
    if primera.startswith("-"):
        lee = primera in _CONFIG_LECTURA
    elif primera in _CONFIG_SUBCOMANDOS_DE_LECTURA:
        lee = True
    elif primera in _CONFIG_SUBCOMANDOS_DE_ESCRITURA:
        lee = False
    else:
        lee = len(accion) == 1 and not puede_crecer    # `git config <nombre>` lee su valor
    return (READ_ONLY if lee else MUTATING), alcances


def _subcomando_de_git(argumentos):
    """(subcomando, resto) de `git <opciones globales> <subcomando> ...`, salteando las opciones
    globales y sus valores. (None, []) si no hay subcomando."""
    i = 0
    while i < len(argumentos) and argumentos[i].startswith("-"):
        opcion = argumentos[i].split("=", 1)[0]
        i += 2 if opcion in _GIT_OPCIONES_CON_VALOR and "=" not in argumentos[i] else 1
    if i >= len(argumentos):
        return None, []
    return argumentos[i], argumentos[i + 1:]


def _opcion_corta(argumentos, letra):
    """Si `-<letra>` va sola, agrupada con otras o pegada a su valor."""
    return any(a.startswith("-") and not a.startswith("--") and letra in a[1:] for a in argumentos)


def _posicionales(argumentos):
    """Los argumentos que no son opciones: `-` es la entrada estandar, un posicional como
    cualquiera, y despues de `--` todo lo es. El valor de una opcion cuenta: ante la duda, uno
    mas."""
    salida = []
    for n, a in enumerate(argumentos):
        if a == "--":
            return salida + list(argumentos[n + 1:])
        if a == "-" or not a.startswith("-"):
            salida.append(a)
    return salida


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
    # Una opcion larga de salida escribe, sea cual sea el programa de lectura (Wave 6):
    # `--output`, `--out`, `--outfile`, `--output-file`, con `=valor` o sin el.
    if any(a.lower().startswith("--out") for a in argumentos):
        return MUTATING
    # Programas de lectura que tambien escriben. Una opcion corta se mira agrupada (`-uo`) y
    # pegada a su valor (`-o<ruta>`), y una larga abreviada (`--out=`): getopt las lee igual.
    if programa == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fls")
                                  or a.startswith("-fprint") for a in argumentos):
        return MUTATING
    if programa in ("sort", "tree") and (_opcion_corta(argumentos, "o") or
                                         any(a.startswith("--o") for a in argumentos)):
        return MUTATING
    if programa == "sort" and any(a.startswith("--com") for a in argumentos):
        return UNRESOLVED                        # --compress-program corre un programa
    if programa == "uniq" and len(_posicionales(argumentos)) >= 2:
        return MUTATING                          # uniq <entrada> <salida>, tambien uniq - <salida>
    if programa == "file" and (_opcion_corta(argumentos, "C") or
                               any(a.startswith("--comp") for a in argumentos)):
        return MUTATING                          # -C escribe el .mgc
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
    if powershell and any(tok.startswith("@") for tok in tokens):
        return _resultado(UNRESOLVED, "una variable")  # un splat: `git config @args`
    segmentos = _segmentos(tokens, powershell)
    if not segmentos:
        return _resultado(UNRESOLVED, "comando vacio")
    # Un comando del Harness, solo: `python <...>/dev-harness.py <subcomando> ...`.
    if len(segmentos) == 1 and len(segmentos[0]) >= 2 and _PYTHON.match(
            _programa(segmentos[0][0])) and _es_la_cli(segmentos[0][1], proyecto, cwd):
        salida = _harness(segmentos[0][2:])
        salida["cli"] = True
        return salida
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


def _una_linea(v):
    """El texto sin los espacios ni los saltos de linea de los bordes, si es de una linea; si no,
    None. Un salto de linea al final no convierte un comando en contenido."""
    if not isinstance(v, str):
        return None
    v = v.strip()
    return v if v and "\n" not in v else None


def _valores_de_una_linea(valor):
    """Los textos de una linea de un `tool_input`, a cualquier profundidad y tambien las claves de
    un objeto (`{"files": {ruta: contenido}}`): los que pueden ser una ruta. Uno con saltos de linea
    es un contenido, no un destino. Sin recursion: un JSON hondo no la agota."""
    pendientes = [valor]
    while pendientes:
        v = pendientes.pop()
        if isinstance(v, str):
            linea = _una_linea(v)
            if linea:
                yield linea
        elif isinstance(v, dict):
            pendientes.extend(v.keys())
            pendientes.extend(v.values())
        elif isinstance(v, (list, tuple)):
            pendientes.extend(v)


def _secuencias(valor):
    """Cada lista y cada objeto de un `tool_input` como la secuencia de sus palabras: los textos
    de una linea que tiene adentro, y los de las listas que tiene adentro, en orden. Es como llega
    un comando repartido: `["git", "config", ...]` o `{"command": "git", "args": [...]}` (E24-E18).
    Cada palabra va entre comillas, asi que vuelve igual al partirla."""
    pendientes = [valor]
    while pendientes:
        v = pendientes.pop()
        hijos = list(v.values()) if isinstance(v, dict) else list(v) if isinstance(v, (list, tuple)) else None
        if hijos is None:
            continue
        palabras = []
        for h in hijos:
            for x in (h if isinstance(h, (list, tuple)) else [h]):
                linea = _una_linea(x)
                if linea:
                    palabras.append(shlex.quote(linea))
        if len(palabras) > 1:
            yield " ".join(palabras)
        pendientes.extend(h for h in hijos if isinstance(h, (dict, list, tuple)))


def _nombra_autoridad(entrada, proyecto, cwd):
    """Si una herramienta que la politica no conoce nombra, en algun valor, `.claude/`, `.git/` o un
    punto de persistencia del host (Wave 6, E24-E14): un servidor MCP que escribe archivos tiene sus
    propios campos, y no se sabe cual es el destino. Ante la duda, cualquiera. Un valor se mira
    tambien como comando, con la regla de Bash: un servidor MCP que corre comandos lo recibe asi
    (E24-E16)."""
    valores = list(_valores_de_una_linea(entrada))
    secuencias = list(_secuencias(entrada))
    if any(es_ruta_de_autoridad(v, proyecto, cwd)
           or es_ruta_de_persistencia(v, resolver=bool(_NOMBRE_CORTO.search(v)))
           or toca_persistencia(v, tolerante=True)     # un servidor MCP que corre comandos
           for v in valores):
        return True
    if any(toca_autoridad(s, tolerante=True) or toca_persistencia(s, tolerante=True)
           for s in secuencias):
        return True
    # La bolsa: las palabras de todos los valores, sin orden y sin comillas (E24-E20). No se puede
    # saber como arma su comando una herramienta que no se conoce: ni en que campo va el programa
    # ni que comillas usa. Lo que en la bolsa es la autoridad, un punto de persistencia o un
    # `git config`, es protegido.
    bolsa = [w for v in valores for w in _SEPARA_LA_BOLSA.split(v.replace("\\", "/")) if w]
    if any(toca_autoridad(w, tolerante=True)
           or any(es_ruta_de_persistencia(c, resolver=bool(_NOMBRE_CORTO.search(c)))
                  for c in _como_rutas(w))
           for w in bolsa):
        return True
    return git_config_a_la_vista(valores, valores + secuencias)


_SEPARA_LA_BOLSA = re.compile(r"[\s'\"`;&|()<>,]+")

# El guard de `git config` (Wave 6, E24-E21, decision de la persona del 04-10-2026). No se parsea
# cada shell forma por forma: si el texto deja ver git y `config`, es una escritura de la
# configuracion salvo que el parser pruebe que lee. INTENTIONAL_CONSERVATIVE_OVERPROTECTION: un
# texto que nombra las dos cosas sin correr `git config` (`git commit -m "config"`) es protegido.
# Se parte por los separadores de cualquier shell, tambien `{`, `@`, `:`, `=` y `!` (`& {git`,
# `-FilePath:git`, `@('config'`, `alias.x=!git`). Y se lee ademas como el shell une una palabra:
# sin las continuaciones de linea (`\`, `` ` `` o `^` y un salto) y sin lo que junta o vale vacio
# (`g\it`, ``g`it``, `g^it`, `'gi'+'t'`, `g$'i't`, `g$()it`). Decimotercera pasada.
_SEPARA_LA_EVIDENCIA = re.compile(r"[\s'\"`;&|()<>,{}\[\]@:=!]+")
_SEPARA_LO_UNIDO = re.compile(r"[\s;&|<>,{}\[\]:=!]+")
_CONTINUACION = re.compile(r"[\\`^]\r?\n")
_ESCAPES = re.compile(r"[`^'\"+\\$()@]")
_GIT = re.compile(r"^git(?:-config)?(?:\.(?:exe|cmd|bat|com))?$")
# Lo que en una lectura de `git config` no se sabe que vale: una variable, una sustitucion, un
# splat de PowerShell (`@args`), un scriptblock.
_NO_SE_SABE = re.compile(r"[$`(){}]|^@")


def _evidencia(texto):
    """Las palabras de un texto en sus dos lecturas: `\\` como barra de una ruta, y como el shell
    une cada palabra."""
    unido = _ESCAPES.sub("", _CONTINUACION.sub("", texto))
    return [[w.lower() for w in _SEPARA_LA_EVIDENCIA.split(texto.replace("\\", "/")) if w],
            [w.lower() for w in _SEPARA_LO_UNIDO.split(unido) if w]]


def git_config_a_la_vista(textos, lecturas):
    """Si los `textos` dejan ver git y `config` (tambien `git-config`), y no estan probados como
    una lectura: una sola `config` en cada lectura del texto, y alguna de las `lecturas`, parseada
    estricta, es `git ... config <una lectura>` (`git config --get x`, `["git", "config",
    "--list"]`). Ante la duda, escritura."""
    git, configs = False, 0
    for palabras in zip(*[_evidencia(t) for t in textos]) if textos else ():
        palabras = [os.path.basename(w) for ws in palabras for w in ws]
        git = git or any(_GIT.match(w) for w in palabras)
        configs = max(configs, sum(1 for w in palabras if w == "config" or (_GIT.match(w) and "config" in w)))
    if not git or not configs:
        return False
    return not (configs == 1 and any(_lee_git_config(t) for t in lecturas))


def _lee_git_config(texto):
    """Si un texto, parseado estricto y sin separadores ni nada que no se sepa que vale, es
    `git ... config <una lectura>`."""
    palabras = _palabras(texto, False)
    if not palabras or any(p in _SEPARADORES or _NO_SE_SABE.search(p) for p in palabras):
        return False
    if _programa(palabras[0]) != "git":
        return False
    sub, args = _subcomando_de_git(palabras[1:])
    return sub == "config" and _config_de_git(args)[0] == READ_ONLY


def clasificar(tool_name, tool_input, proyecto=None, cwd=None):
    """{class, reason, taskKey, stage, reconcilia}. Determinista: la misma entrada, la misma clase.

    `proyecto` es la raiz y `cwd` desde donde corre el comando: la CLI es la de esa raiz.

    `taskKey` es la clave de un comando del Harness; `stage`, la etapa que corre un comando que
    avanza; `reconcilia`, si ese comando reevalua su compuerta y reconcilia el estado.
    """
    entrada = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in _SHELLS:
        comando = entrada.get("command")
        salida = _shell(tool_name, comando, proyecto, cwd)
        if salida["class"] != READ_ONLY and not salida.get("cli") and (
                toca_autoridad(comando) or toca_persistencia(comando)
                or (isinstance(comando, str) and git_config_a_la_vista([comando], [comando]))):
            salida.update({"class": MUTATING, "reason": "escribe la autoridad del flujo",
                           "protected": True, "humanIntent": None})
        return salida
    if tool_name in _HERRAMIENTAS_QUE_ESCRIBEN and any(
            es_ruta_de_autoridad(entrada.get(c), proyecto, cwd) or es_ruta_de_persistencia(entrada.get(c))
            for c in ("file_path", "notebook_path")):
        salida = _resultado(MUTATING, "escribe la autoridad del flujo")
        salida["protected"] = True
        return salida
    if _nombra_env(entrada):
        return _resultado(UNRESOLVED, "nombra .env")
    if tool_name in _HERRAMIENTAS_DE_LECTURA:
        return _resultado(READ_ONLY, tool_name)
    if tool_name in _HERRAMIENTAS_QUE_ESCRIBEN:
        return _resultado(MUTATING, tool_name)
    if tool_name in _DELEGACION:
        return _resultado(WORKFLOW_ADVANCING, "delegacion", etapa="EXECUTION")
    if _nombra_autoridad(entrada, proyecto, cwd):
        salida = _resultado(MUTATING, "escribe la autoridad del flujo")
        salida["protected"] = True
        return salida
    return _resultado(UNRESOLVED, str(tool_name or "sin nombre"))
