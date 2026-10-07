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
import posixpath
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
    comando (ver `_palabras`). Un glob hacia la autoridad lo mira `destino_de_autoridad` (R11)."""
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


# Las clases POSIX de un `[...]` de bash (`[[:alpha:]]`), como rangos que entiende `fnmatch`.
_CLASES_POSIX = {"alpha": "a-zA-Z", "upper": "A-Z", "lower": "a-z", "digit": "0-9",
                 "alnum": "a-zA-Z0-9", "xdigit": "0-9a-fA-F", "word": "a-zA-Z0-9_",
                 "space": " \t\n\r\f\v", "blank": " \t", "punct": "!-/:-@^-`{-~",
                 "graph": "!-~", "print": " -~", "cntrl": "\x01-\x1f"}
_CLASE_POSIX = re.compile(r"\[:(\w*):\]")


def _puede_ser_autoridad(tramo):
    """Si un segmento de ruta, con `*`, `?` o `[...]`, puede ser `.claude` o `.git`: el nombre
    entero contra el patron, sin mayusculas y sin el punto o el espacio final que Windows ignora.
    `[^...]` niega como `[!...]`, como en bash, y una clase POSIX (`[[:alpha:]]`) es su rango; una
    que no se conoce, cualquier caracter. Un `*` puede empezar con punto: PowerShell lo expande
    asi, y bash con `dotglob`."""
    tramo = _CLASE_POSIX.sub(lambda m: _CLASES_POSIX.get(m.group(1).lower(), "!-~"), tramo).lower()
    patrones = {tramo, tramo.rstrip(" .") or tramo}
    patrones |= {p.replace("[^", "[!") for p in patrones}
    return any(fnmatch.fnmatchcase(c, p) for p in patrones for c in _CARPETAS_DE_AUTORIDAD)


def _tramos_de_texto(ruta):
    """Los segmentos de una ruta por el texto, sin mayusculas: `.` y `..` resueltos sin el disco."""
    tramos = [t if t in (".", "..") else t.rstrip(" .") or t
              for t in ruta.replace("\\", "/").split("/")]
    return [t.lower() for t in posixpath.normpath("/".join(tramos)).split("/") if t and t != "."]


_ABSOLUTA = re.compile(r"^(?:/|[A-Za-z]:)")


def _patron_de_autoridad(ruta, proyecto=None, cwd=None, sin_base=False):
    """Si un destino, como patron de `fnmatch` (`*`, `?`, `[...]` activos; un comodin literal va
    escapado como `[*]`), puede ser `.claude` o `.git` en la raiz del proyecto, o algo adentro
    (R11). El glob cuenta en la posicion de la raiz:
    `.cla*/x`, `./.cla*`, `../.cla*` desde una subcarpeta o `<raiz>/.cla*`, y no `tmp/.cla*`. Lo
    relativo se resuelve contra `cwd` y contra `proyecto`: ante la duda sobre desde donde corre,
    cualquiera de los dos. Sin proyecto, la raiz es el primer segmento de una ruta relativa.

    `sin_base`: el comando cambia de carpeta (`cd`), y no se sabe desde donde se resuelve una ruta
    relativa. Ahi el segmento cuenta si lo que tiene adelante, sin los `..`, puede ser el final de
    la raiz: nada (`../.cla*`) o el nombre del proyecto (`cd .. && rm -rf <proyecto>/.cla*`).

    Se decide por el texto: el glob no se expande contra el disco y una variable no se resuelve.
    Del disco sale solo la forma larga de la raiz del proyecto, como en `es_ruta_de_autoridad`."""
    ruta = ruta.replace("\\", "/")
    absoluta = bool(_ABSOLUTA.match(ruta))
    raices = [_tramos_de_texto(proyecto),
              [t.lower() for t in re.split(r"[\\/]", _normalizada(proyecto, None)) if t]] if proyecto else [[]]
    if not absoluta and (sin_base or not proyecto):
        tramos = _tramos_de_texto(ruta)
        while tramos and tramos[0] == "..":
            tramos.pop(0)
        if not sin_base:
            return bool(tramos) and _puede_ser_autoridad(tramos[0])
        return any(_puede_ser_autoridad(t) and (n == 0 or any(
            n <= len(raiz) and all(fnmatch.fnmatchcase(r, x) for r, x in zip(raiz[-n:], tramos))
            for raiz in raices)) for n, t in enumerate(tramos))
    if not proyecto:
        return False                                   # absoluta, sin raiz con que compararla
    bases = [None] if absoluta else [b for b in (cwd, proyecto) if b]
    for base in bases:
        tramos = _tramos_de_texto(ruta if base is None else base.replace("\\", "/") + "/" + ruta)
        for raiz in raices:
            n = len(raiz)
            if len(tramos) > n and _puede_ser_autoridad(tramos[n]) and all(
                    fnmatch.fnmatchcase(r, t) for r, t in zip(raiz, tramos)):
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


def _como_rutas(palabra, redireccion=True):
    """Las rutas que una palabra del comando puede abrir, en las formas que el texto deja ver: sin
    redirecciones pegadas; el valor de una opcion pegado con `=` (`--target-directory=x`), con `:`
    (`-Path:x`, PowerShell) o detras de una opcion corta (`-ox`, `-uox`); `/c/x` de Git Bash como
    `c:/x` y `~` expandido. Sin `redireccion`, una palabra ya partida por el shell conserva sus
    digitos del principio (`2024*` no es `*`)."""
    if redireccion:
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


# -- R11: el destino de una operacion que escribe -------------------------------
#
# Un comodin no es autoridad. Es autoridad el destino de una operacion que escribe, cuando la
# sintaxis textual soportada de ese destino puede alcanzar `.claude` o `.git` en la raiz del
# proyecto (R11, segunda pasada, decision de la persona del 06-10-2026). En orden: la operacion de
# cada segmento, sus destinos, el texto de cada destino como lo deja el shell (comillas, escapes,
# llaves de bash, backtick de PowerShell) y si ese patron alcanza la raiz.
#
# Solo Bash y PowerShell: una MCP generica no tiene destinos tipados, y sus valores no se leen como
# rutas con comodin (R11-10). Lo que solo se sabe al correr -una variable, una sustitucion, un
# programa que elige su destino- sigue siendo limite.

# Los programas que cambian la carpeta desde donde se resuelve lo relativo.
_CAMBIA_DE_CARPETA = frozenset(("cd", "chdir", "pushd", "set-location", "sl", "push-location"))
_SHELLS_POSIX = frozenset(("bash", "sh", "zsh", "dash", "ksh"))
_SHELLS_POWERSHELL = frozenset(("powershell", "pwsh"))
# Lo que abre un bloque o una condicion de bash y no es el programa del segmento.
_PALABRAS_DE_BLOQUE = frozenset(("{", "}", "!", "if", "then", "elif", "else", "while", "until",
                                 "do", "time"))
_OPERADORES_BASH = ("&>>", "<<<", "<<-", "&&", "||", ";;", "|&", ">>", "&>", ">|", "<<", "<>", ">&", "<&",
                    ";", "&", "|", "(", ")", "<", ">")
_REDIRIGE_ESCRITURA = frozenset((">", ">>", "&>", "&>>", ">|", "<>", ">&"))
_REDIRIGE_LECTURA = frozenset(("<", "<<<", "<&"))
_HEREDOC = frozenset(("<<", "<<-"))
_OPERADORES_POWERSHELL = ("&&", "||", ">>", ";", "|", "&", "(", ")", "{", "}", ",", ">")
_ESCAPES_DE_POWERSHELL = {"n": "\n", "t": "\t", "r": "\r", "0": "\0"}
_LIMITE_DE_LLAVES = 256

# Opciones de git cuyo valor no es un destino (un mensaje, el archivo del mensaje, un autor, una
# fecha), por subcomando, porque la misma letra cambia: `-m` lleva el mensaje en `commit` y no lleva
# valor en `checkout`. Cada subcomando: (cortas con valor, cortas sin valor, largas con valor). Las
# cortas sin valor estan solo para descomponer un grupo (`-am`, `-sm`). Solo una opcion de esta
# tabla saca de los destinos su valor; una que no esta, o un subcomando que no esta, no saca nada.
_GIT_VALOR_SIN_RUTA = {
    "commit": ("mF", "aenqsv", frozenset(("--message", "--file", "--reuse-message",
                                          "--reedit-message", "--author", "--date", "--template",
                                          "--cleanup", "--trailer", "--fixup", "--squash"))),
    "tag": ("mF", "aefs", frozenset(("--message", "--file", "--local-user", "--cleanup"))),
    "merge": ("mF", "enqv", frozenset(("--message", "--file", "--cleanup"))),
    "notes": ("mF", "f", frozenset(("--message", "--file", "--reuse-message", "--reedit-message"))),
    "stash": ("m", "akpqu", frozenset(("--message",))),
}
# Parametros de un cmdlet que escribe: los que no llevan valor, y los que llevan un valor que no
# es una ruta. Se aceptan abreviados, como PowerShell. Cualquier otro valor es un destino.
_PS_INTERRUPTORES = ("recurse", "force", "whatif", "confirm", "passthru", "nonewline", "append",
                     "noclobber", "asbytestream", "verbose", "debug", "container")
_PS_VALOR_SIN_RUTA = ("value", "encoding", "itemtype", "type", "credential", "stream",
                      "inputobject", "width")
# Los cmdlets cuyo segundo posicional es el contenido (`Set-Content x '*'`), no otra ruta.
_PS_UNA_RUTA = frozenset(("set-content", "sc", "add-content", "ac", "out-file", "set-item", "si"))


def destino_de_autoridad(tool, comando, proyecto=None, cwd=None):
    """Si algun destino de lo que escribe un comando de Bash o PowerShell puede ser `.claude` o
    `.git` en la raiz del proyecto, o algo adentro, por su texto (R11). Comillas sin cerrar: ante
    la duda, si."""
    if tool not in _SHELLS or not isinstance(comando, str):
        return False
    try:
        return _alcanza(comando, tool == "PowerShell", proyecto, cwd, False, 0)
    except ValueError:
        return True


def _alcanza(texto, powershell, proyecto, cwd, sin_base, hondura):
    segmentos, redirecciones = (_lexico_powershell if powershell else _lexico_bash)(texto)
    segmentos = [s for s in (_sin_bloque(s) for s in segmentos) if s]
    # Un `cd` en el comando deja sin saber desde donde se resuelve lo relativo (R11-16, R11-23).
    sin_base = sin_base or any(_programa(s[0][0]) in _CAMBIA_DE_CARPETA for s in segmentos)
    destinos, carpetas, escribe = list(redirecciones), [], bool(redirecciones)
    for segmento in segmentos:
        clase, propios = _destinos_del_segmento(segmento, powershell)
        if clase == "cd":
            carpetas.extend(propios)
            continue
        escribe = escribe or clase != READ_ONLY
        destinos.extend(propios)
        if hondura < 3:
            for interior, es_powershell in _comandos_anidados(segmento):
                if _alcanza(interior, es_powershell, proyecto, cwd, sin_base, hondura + 1):
                    return True
    if escribe:
        destinos.extend(carpetas)                      # `cd .cla* && rm -rf harness`
    return any(_patron_alcanza(patron, proyecto, cwd, sin_base)
               for _, patrones in destinos for patron in patrones)


def _patron_alcanza(patron, proyecto, cwd, sin_base):
    """Un destino, en las formas de `_como_rutas` (`--target-directory=x`, `-Path:x`, `-tx`): el
    literal, como `toca_autoridad`, o el patron en la posicion de la raiz."""
    for c in _como_rutas(patron, redireccion=False):
        literal = re.sub(r"\[([*?\[])\]", r"\1", c)
        if toca_autoridad(literal, tolerante=True) or _patron_de_autoridad(c, proyecto, cwd, sin_base):
            return True
    return False


def _sin_bloque(segmento):
    """El segmento sin lo que abre un bloque o una condicion (`{ cd src; ...; }`, `! rm ...`)."""
    n = 0
    while n < len(segmento) and segmento[n][0] in _PALABRAS_DE_BLOQUE:
        n += 1
    return segmento[n:]


def _destinos_del_segmento(segmento, powershell):
    """(clase, destinos) de un segmento: un programa y sus palabras. Lo que lee no tiene destinos;
    lo que escribe o no se reconoce, cualquiera de sus argumentos, salvo lo que la operacion dice
    que no es una ruta (el mensaje de git, por subcomando; el valor de `Set-Content`). `cd` va
    aparte: sus argumentos cuentan si el comando escribe."""
    textos = [p[0] for p in segmento]
    programa, argumentos = _programa(textos[0]), segmento[1:]
    if programa in _CAMBIA_DE_CARPETA:
        return "cd", argumentos
    if programa == "git":
        if _git(textos[1:]) == READ_ONLY:
            return READ_ONLY, []
        return MUTATING, _destinos_de_git(argumentos)
    clase = _segmento(textos, powershell)
    if clase == READ_ONLY:
        return READ_ONLY, []
    if powershell and programa in _ESCRITURA:
        return clase, _destinos_de_un_cmdlet(programa, argumentos)
    return clase, argumentos


def _valor_sin_ruta_de_git(subcomando, texto):
    """Cuantas palabras ocupa `texto` si es una opcion de `subcomando` cuyo valor no es un destino
    (`_GIT_VALOR_SIN_RUTA`): 1 si el valor va pegado (`-mfix`, `--message=fix`, `-amfix`), 2 si va
    en la palabra siguiente (`-m fix`, `-am fix`), 0 si la tabla no la reconoce. Un grupo de cortas
    se descompone solo con letras de la tabla: una letra desconocida antes de la del valor, 0."""
    con_valor, sin_valor, largas = _GIT_VALOR_SIN_RUTA.get(subcomando, ("", "", ()))
    if texto.startswith("--"):
        nombre, igual, _ = texto.partition("=")
        return (1 if igual else 2) if nombre in largas else 0
    for n, letra in enumerate(texto[1:]):
        if letra in con_valor:
            return 1 if texto[n + 2:] else 2
        if letra not in sin_valor:
            return 0
    return 0


def _destinos_de_git(argumentos):
    """Los argumentos de git que pueden ser una ruta: las opciones globales `-C`, `--git-dir` y
    `--work-tree`, y lo que el subcomando recibe, salvo el valor de una opcion que la tabla
    `_GIT_VALOR_SIN_RUTA` reconoce para ese subcomando (el mensaje de `commit -m`, `tag -F`...),
    separado, pegado o al final de un grupo que la tabla descompone. La aridad se reconoce solo
    para las opciones y los subcomandos de la tabla: una opcion o un subcomando desconocido es un
    destino mas y no se lleva por si mismo el posicional siguiente. No es la gramatica de opciones
    de git entera: si el valor de una opcion desconocida se escribe igual que una de la tabla
    (`commit -t -m x`), se lee segun la tabla y `x` sale de los destinos (O1). Afecta la precision
    de la extraccion; no hay evidencia de que esconda una escritura de la autoridad."""
    textos = [p[0] for p in argumentos]
    destinos, i = [], 0
    while i < len(textos) and textos[i].startswith("-"):
        opcion = textos[i].split("=", 1)[0]
        if opcion in _GIT_OPCIONES_CON_VALOR and "=" not in textos[i]:
            if opcion != "-c" and i + 1 < len(textos):
                destinos.append(argumentos[i + 1])
            i += 2
            continue
        if opcion != "-c":
            destinos.append(argumentos[i])
        i += 1
    subcomando = textos[i] if i < len(textos) else None
    i += 1
    while i < len(textos):
        texto = textos[i]
        if texto == "--":
            destinos.extend(argumentos[i + 1:])
            break
        ocupa = _valor_sin_ruta_de_git(subcomando, texto) if texto.startswith("-") else 0
        if ocupa:
            i += ocupa
            continue
        destinos.append(argumentos[i])
        i += 1
    return destinos


def _abrevia(nombre, nombres):
    return bool(nombre) and any(n.startswith(nombre) for n in nombres)


def _destinos_de_un_cmdlet(programa, argumentos):
    """Los argumentos de un cmdlet que escribe que pueden ser una ruta: los posicionales y el
    valor de cualquier parametro, salvo los que no llevan valor (`-Recurse`), los que llevan uno
    que no es una ruta (`-Value`, `-Encoding`) y el segundo posicional de `Set-Content` y los
    suyos, que es el contenido."""
    destinos, posicionales, i = [], 0, 0
    while i < len(argumentos):
        texto = argumentos[i][0]
        if texto.startswith("-") and len(texto) > 1:
            nombre, pegado, _ = texto[1:].partition(":")
            nombre = nombre.lower()
            interruptor = _abrevia(nombre, _PS_INTERRUPTORES)
            if _abrevia(nombre, _PS_VALOR_SIN_RUTA) and not interruptor:
                i += 1 if pegado else 2
                continue
            destinos.append(argumentos[i])             # `-Path:x`
            if not (pegado or interruptor) and i + 1 < len(argumentos):
                destinos.append(argumentos[i + 1])     # `-Destination x`
                i += 1
            i += 1
            continue
        if programa not in _PS_UNA_RUTA or posicionales == 0:
            destinos.append(argumentos[i])
        posicionales += 1
        i += 1
    return destinos


def _comandos_anidados(segmento):
    """[(texto, powershell)] de lo que el segmento hace correr a otro shell: `bash -c '...'`,
    `sh -lc "..."`, `powershell -Command ...`, `pwsh -c ...`, `cmd /c ...`, tambien detras de otro
    programa (`sudo bash -c`). `cmd` no expande comodines: los expande cada programa, y su texto se
    lee como el de PowerShell, con `\\` de ruta."""
    textos = [p[0] for p in segmento]
    salida = []
    for n, texto in enumerate(textos):
        programa, resto = _programa(texto), textos[n + 1:]
        if programa in _SHELLS_POSIX:
            for k, opcion in enumerate(resto):
                if re.match(r"^-[A-Za-z]*c[A-Za-z]*$", opcion) and k + 1 < len(resto):
                    salida.append((resto[k + 1], False))
                    break
        elif programa in _SHELLS_POWERSHELL:
            opciones = [o[1:].split(":", 1)[0].lower() if o.startswith("-") else None for o in resto]
            if any(o in ("encodedcommand", "e", "ec", "file", "f") for o in opciones):
                continue                               # codificado o un archivo: limite
            k = next((k + 1 for k, o in enumerate(opciones) if _abrevia(o, ("command",))), None)
            if k is None:                              # sin -Command, lo que sigue a las opciones
                k = next((k for k, o in enumerate(opciones) if o is None), len(resto))
            if k < len(resto):
                salida.append((" ".join(resto[k:]), True))
        elif programa == "cmd":
            k = next((k for k, opcion in enumerate(resto) if opcion.lower() in ("/c", "/k")), None)
            if k is not None and k + 1 < len(resto):
                salida.append((" ".join(resto[k + 1:]), True))
    return salida


# Una palabra es (texto, patrones): el texto como lo recibe el programa, y los patrones de
# `fnmatch` de su destino, con los comodines activos y los literales escapados (`[*]`). Bash da mas
# de un patron cuando expande llaves.

def _lexico_bash(texto):
    """(segmentos, redirecciones) de un comando de bash, como lo parte bash: comillas simples y
    dobles, la barra invertida como escape, los operadores y las redirecciones. Una palabra entre
    comillas o escapada deja sus comodines literales. Levanta ValueError con comillas sin cerrar."""
    segmentos, actual, redirecciones, heredocs = [], [], [], []
    caracteres, en_palabra, redirige = [], False, None
    i, n = 0, len(texto)

    def cerrar():
        nonlocal caracteres, en_palabra, redirige
        if en_palabra:
            palabra = _palabra_de_bash(caracteres)
            if redirige is None:
                actual.append(palabra)
            elif redirige in _HEREDOC:
                heredocs.append((palabra[0], redirige == "<<-"))
            elif redirige and not re.match(r"^(?:\d+|-)$", palabra[0]):
                redirecciones.append(palabra)
            redirige = None
        caracteres, en_palabra = [], False

    while i < n:
        c = texto[i]
        if c == "\\":
            if texto.startswith("\n", i + 1):
                i += 2
                continue
            caracteres.append((texto[i + 1] if i + 1 < n else "\\", True))
            en_palabra, i = True, i + 2
            continue
        if c == "'":
            fin = texto.find("'", i + 1)
            if fin < 0:
                raise ValueError("comillas sin cerrar")
            caracteres.extend((x, True) for x in texto[i + 1:fin])
            en_palabra, i = True, fin + 1
            continue
        if c == '"':
            en_palabra, i = True, i + 1
            while True:
                if i >= n:
                    raise ValueError("comillas sin cerrar")
                d = texto[i]
                if d == '"':
                    i += 1
                    break
                if d == "\\" and i + 1 < n and texto[i + 1] in '$`"\\\n':
                    if texto[i + 1] != "\n":
                        caracteres.append((texto[i + 1], True))
                    i += 2
                    continue
                caracteres.append((d, True))
                i += 1
            continue
        if c in " \t\r\n":
            cerrar()
            i += 1
            if c == "\n":
                segmentos.append(actual)
                actual = []
                i = _saltar_heredocs(texto, i, heredocs)
            continue
        if c == "#" and not en_palabra:
            fin = texto.find("\n", i)
            i = n if fin < 0 else fin
            continue
        operador = next((o for o in _OPERADORES_BASH if texto.startswith(o, i)), None)
        if operador:
            if operador[0] in "<>" and en_palabra and all(x.isdigit() and not lit for x, lit in caracteres):
                caracteres, en_palabra = [], False    # el descriptor de `2>`
            cerrar()
            if operador in _REDIRIGE_ESCRITURA:
                redirige = True
            elif operador in _HEREDOC:
                redirige = operador
            elif operador in _REDIRIGE_LECTURA:
                redirige = False
            else:
                segmentos.append(actual)
                actual = []
            i += len(operador)
            continue
        caracteres.append((c, False))
        en_palabra, i = True, i + 1
    cerrar()
    segmentos.append(actual)
    return [s for s in segmentos if s], redirecciones


def _saltar_heredocs(texto, i, heredocs):
    """Desde el principio de una linea, el final del cuerpo de los heredocs pendientes: el cuerpo
    es la entrada de un programa, no un comando. Vacia `heredocs`."""
    while heredocs:
        delimitador, tabs = heredocs.pop(0)
        while i < len(texto):
            fin = texto.find("\n", i)
            linea = texto[i:] if fin < 0 else texto[i:fin]
            i = len(texto) if fin < 0 else fin + 1
            if (linea.lstrip("\t") if tabs else linea).rstrip("\r") == delimitador:
                break
    return i


def _palabra_de_bash(caracteres):
    """(texto, patrones) de una palabra de bash: las llaves expandidas, acotadas."""
    texto = "".join(c for c, _ in caracteres)
    expandidas = _expandir_llaves(caracteres)
    if expandidas is None:
        expandidas = _llaves_como_comodin(caracteres)
    return texto, ["".join("[%s]" % c if lit and c in "*?[" else c for c, lit in cs)
                   for cs in expandidas]


def _grupo_de_llaves(caracteres):
    """(inicio, fin, alternativas) del primer grupo de llaves que bash expande: `{a,b}` o una
    secuencia `{a..e}`, `{1..9}`, sin comillas y sin el `$` de una variable. None si no hay."""
    for i, (c, lit) in enumerate(caracteres):
        if c != "{" or lit or (i and caracteres[i - 1] == ("$", False)):
            continue
        nivel, comas, fin = 0, [], None
        for j in range(i, len(caracteres)):
            d, l = caracteres[j]
            if l:
                continue
            if d == "{":
                nivel += 1
            elif d == "}":
                nivel -= 1
                if nivel == 0:
                    fin = j
                    break
            elif d == "," and nivel == 1:
                comas.append(j)
        if fin is None:
            continue
        if comas:
            cortes = [i] + comas + [fin]
            return i, fin, [caracteres[a + 1:b] for a, b in zip(cortes, cortes[1:])]
        texto = "".join(c for c, _ in caracteres[i + 1:fin])
        if _SECUENCIA.match(texto):
            secuencia = _secuencia(texto)
            return i, fin, None if secuencia is None else [[(x, True) for x in s] for s in secuencia]
    return None


_SECUENCIA = re.compile(r"^(?:-?\d+\.\.-?\d+|[A-Za-z]\.\.[A-Za-z])(?:\.\.-?\d+)?$")


def _secuencia(texto):
    """Los elementos de una secuencia de bash (`a..e`, `1..9`, `1..9..2`), o None si pasan de
    `_LIMITE_DE_LLAVES`."""
    a, _, resto = texto.partition("..")
    b, _, paso = resto.partition("..")
    paso = abs(int(paso or 1)) or 1
    x, y = (ord(a), ord(b)) if a.isalpha() else (int(a), int(b))
    if abs(y - x) // paso > _LIMITE_DE_LLAVES:
        return None
    valores = range(x, y + (1 if y >= x else -1), paso if y >= x else -paso)
    return [chr(v) if a.isalpha() else str(v) for v in valores]


def _expandir_llaves(caracteres):
    """Las palabras de la expansion de llaves, o None si pasan de `_LIMITE_DE_LLAVES`: no se
    enumera lo que crece exponencial (`{a,b}{a,b}...`)."""
    salida, pendientes = [], [caracteres]
    while pendientes:
        actual = pendientes.pop()
        grupo = _grupo_de_llaves(actual)
        if grupo is None:
            salida.append(actual)
            if len(salida) > _LIMITE_DE_LLAVES:
                return None
            continue
        i, fin, alternativas = grupo
        if alternativas is None or len(alternativas) > _LIMITE_DE_LLAVES:
            return None
        pendientes.extend(actual[:i] + a + actual[fin + 1:] for a in reversed(alternativas))
    return salida


def _llaves_como_comodin(caracteres):
    """Pasado `_LIMITE_DE_LLAVES`, un intento sin garantia: cada grupo de llaves es un `*`, y las
    alternativas con `/` se miran una por una, con los otros grupos como `*`. No es completo: una
    expansion de mas de 256 palabras esta fuera de la frontera de R11 (final-qualification.md,
    OUT_OF_SCOPE_COMPLEXITY_BOUNDARY). Dentro del limite decide `_expandir_llaves`."""
    def todo_comodin(cs):
        grupo = _grupo_de_llaves(cs)
        while grupo is not None:
            cs = cs[:grupo[0]] + [("*", False)] + cs[grupo[1] + 1:]
            grupo = _grupo_de_llaves(cs)
        return cs
    salida, resto = [todo_comodin(caracteres)], caracteres
    while True:
        grupo = _grupo_de_llaves(resto)
        if grupo is None:
            return salida
        i, fin, alternativas = grupo
        salida.extend(todo_comodin(resto[:i] + a + resto[fin + 1:])
                      for a in alternativas or () if any(c == "/" for c, _ in a))
        resto = resto[:i] + [("*", False)] + resto[fin + 1:]


def _lexico_powershell(texto):
    """(segmentos, redirecciones) de un comando de PowerShell: comillas simples (literales) y
    dobles, el backtick como escape fuera de las simples, los operadores y las redirecciones. Las
    llaves y los parentesis parten segmentos: lo de adentro de un scriptblock tambien corre. El
    comodin lo expande el provider, tambien entre comillas, salvo escapado con backtick (`` `* ``).
    Levanta ValueError con comillas sin cerrar."""
    segmentos, actual, redirecciones = [], [], []
    caracteres, en_palabra, redirige = [], False, None
    i, n = 0, len(texto)

    def cerrar():
        nonlocal caracteres, en_palabra, redirige
        if en_palabra:
            palabra = _palabra_de_powershell("".join(caracteres))
            if redirige is None:
                actual.append(palabra)
            elif redirige:
                redirecciones.append(palabra)
            redirige = None
        caracteres, en_palabra = [], False

    while i < n:
        c = texto[i]
        if c == "`":
            if texto.startswith("\n", i + 1) or texto.startswith("\r\n", i + 1):
                i += 3 if texto[i + 1] == "\r" else 2
                continue
            if i + 1 < n:
                caracteres.append(_ESCAPES_DE_POWERSHELL.get(texto[i + 1], texto[i + 1]))
            en_palabra, i = True, i + 2
            continue
        if c == "'":
            en_palabra, i = True, i + 1
            while True:
                if i >= n:
                    raise ValueError("comillas sin cerrar")
                if texto[i] == "'":
                    if texto.startswith("'", i + 1):
                        caracteres.append("'")
                        i += 2
                        continue
                    i += 1
                    break
                caracteres.append(texto[i])
                i += 1
            continue
        if c == '"':
            en_palabra, i = True, i + 1
            while True:
                if i >= n:
                    raise ValueError("comillas sin cerrar")
                d = texto[i]
                if d == "`" and i + 1 < n:
                    caracteres.append(_ESCAPES_DE_POWERSHELL.get(texto[i + 1], texto[i + 1]))
                    i += 2
                    continue
                if d == '"':
                    if texto.startswith('"', i + 1):
                        caracteres.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                caracteres.append(d)
                i += 1
            continue
        if c in " \t\r\n":
            cerrar()
            if c == "\n":
                segmentos.append(actual)
                actual = []
            i += 1
            continue
        if c == "#" and not en_palabra:
            fin = texto.find("\n", i)
            i = n if fin < 0 else fin
            continue
        operador = next((o for o in _OPERADORES_POWERSHELL if texto.startswith(o, i)), None)
        if operador:
            if operador[0] == ">" and en_palabra and all(x.isdigit() or x == "*" for x in caracteres):
                caracteres, en_palabra = [], False    # el stream de `2>` o `*>`
            cerrar()
            if operador in (">", ">>"):
                if re.match(r"&\d", texto[i + len(operador):i + len(operador) + 2]):
                    i += len(operador) + 2             # `2>&1`
                    continue
                redirige = True
            elif operador == ",":
                pass                                   # un arreglo: cada elemento, una palabra
            else:
                segmentos.append(actual)
                actual = []
            i += len(operador)
            continue
        caracteres.append(c)
        en_palabra, i = True, i + 1
    cerrar()
    segmentos.append(actual)
    return [s for s in segmentos if s], redirecciones


def _palabra_de_powershell(texto):
    """(texto, [patron]) de una palabra de PowerShell: para el provider, `` `* `` es un `*` literal
    y `*`, `?`, `[` son comodines."""
    patron, i = [], 0
    while i < len(texto):
        c = texto[i]
        if c == "`" and i + 1 < len(texto):
            siguiente = texto[i + 1]
            patron.append("[%s]" % siguiente if siguiente in "*?[" else siguiente)
            i += 2
            continue
        patron.append(c)
        i += 1
    return texto, ["".join(patron)]


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
                or (isinstance(comando, str) and git_config_a_la_vista([comando], [comando]))
                or destino_de_autoridad(tool_name, comando, proyecto, cwd)):
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
