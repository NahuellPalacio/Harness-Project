# Final Qualification, R11: la autoridad del flujo nombrada con un glob estatico.
#
# Escenarios R11-01 a R11-14 de docs/cambios/flow-governance/final-qualification.md («R11: la
# decision de la persona y el endurecimiento»). Un segmento con `*`, `?` o `[...]` visible en el
# texto que puede ser `.claude` o `.git` en la raiz del proyecto es la autoridad del flujo, igual
# que el literal. Se decide por el texto: sin leer el disco y sin resolver variables.
#
# Una MCP generica queda afuera (R11-10, R11-13, R11-22): sus valores no son destinos tipados, y R11
# no lee un comodin en ellos. Su literal sigue protegido.
#
# Reusa los fixtures del flujo de 62 y 63, como 66. Nada sale a la red.
import glob
import importlib
import importlib.util
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


W2 = _cargar("caso_62_para_70", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")
W3 = _cargar("caso_63_para_70", RAIZ / "tests" / "casos" / "63_compuerta_del_flujo.py")

A = W2.A
PROTEGIDO = "FLOW_AUTHORITY_PROTECTED"


def _policy():
    return importlib.import_module("lib.tool_policy")


def _protegido(t, p, s, escenario, tool, entrada):
    salida = W3._pre(p, s, tool, entrada)
    rotulo = "%s %s %s" % (escenario, tool, str(entrada)[-60:])
    t.igual("%s: deny" % rotulo, "deny", W3._decision(salida))
    t.contiene("%s: protegido" % rotulo, PROTEGIDO, W3._motivo(salida) or "")


def _no_protegido(t, p, s, escenario, tool, entrada):
    """Con la tarea sana pasa, y si algo lo negara no seria por la autoridad."""
    salida = W3._pre(p, s, tool, entrada)
    rotulo = "%s %s %s" % (escenario, tool, str(entrada)[-60:])
    t.verdadero("%s: no es protegido" % rotulo, PROTEGIDO not in (W3._motivo(salida) or ""))
    decision = W3._decision(salida)
    t.igual("%s: pasa con la tarea sana" % rotulo, None,
            decision and (decision, (W3._motivo(salida) or "")[:200]))


def _frontera_mcp(t, p, s, escenario, tool, entrada):
    """El limite declarado de R11 para una MCP generica: sus valores no son destinos tipados, y R11
    no lee un comodin en ellos. No es FLOW_AUTHORITY_PROTECTED, y la herramienta conserva su clase
    conservadora: UNRESOLVED_TOOL_CLASS, nunca READ_ONLY."""
    salida = W3._pre(p, s, tool, entrada)
    rotulo = "%s %s %s" % (escenario, tool, str(entrada)[-60:])
    t.verdadero("%s: frontera, no protegido por R11" % rotulo,
                PROTEGIDO not in (W3._motivo(salida) or ""))
    clase = _policy().clasificar(tool, entrada, str(p), str(p))["class"]
    t.igual("%s: frontera, la clase sigue conservadora" % rotulo, "UNRESOLVED_TOOL_CLASS", clase)


def _con_tarea(nombre):
    p = W2._proyecto()
    W2._listo(p, A)
    W3._vincular(p, nombre, A)
    return p


# -- R11-01 a R11-07: un glob que puede ser la autoridad, en la raiz -------------------------------

def test_r11_01_a_07_un_glob_que_alcanza_la_autoridad(t):
    """R11-01 a R11-07 — un segmento con `*`, `?` o `[...]` que puede ser `.claude` o `.git` en la
    raiz del proyecto, en un comando que escribe, es FLOW_AUTHORITY_PROTECTED con la tarea sana."""
    p = _con_tarea("r11-glob")
    try:
        raiz = str(p).replace("\\", "/")
        casos = [
            # R11-01: el borrado del harness, POSIX
            ("R11-01", "Bash", "rm -rf .cla*/harness"),
            ("R11-01", "Bash", "rm -rf ./.cla*/harness"),
            ("R11-01", "Bash", "rm -rf .cla*"),
            ("R11-01", "Bash", "rm -rf .CLA*/harness"),
            ("R11-01", "Bash", "rm -rf %s/.cla*/harness" % raiz),
            ("R11-01", "Bash", "cd .cla* && rm -rf harness"),
            ("R11-01", "Bash", "rm -rf src/../.cla*/harness"),
            # R11-02: el borrado del harness, PowerShell
            ("R11-02", "PowerShell", "Remove-Item -Recurse -Force .cla*\\harness"),
            ("R11-02", "PowerShell", "Remove-Item -Recurse -Force .\\.cla*\\harness"),
            ("R11-02", "PowerShell", "Remove-Item -Recurse -Force -Path:.cla*\\harness"),
            ("R11-02", "PowerShell", "Remove-Item -Recurse -Force '%s\\.cla*\\harness'" % str(p)),
            ("R11-02", "PowerShell", "ri -r -fo .Cla*\\harness"),
            # R11-03: reescribir el estado de una tarea, POSIX
            ("R11-03", "Bash", "cp x .cla*/runtime/tasks/ABC-123/state.json"),
            ("R11-03", "Bash", "cp x --target-directory=.cla*/runtime/tasks/ABC-123"),
            ("R11-03", "Bash", "mv x ./.cla*/runtime/tasks/ABC-123/state.json"),
            # R11-04: reescribir el estado de una tarea, PowerShell
            ("R11-04", "PowerShell", "Copy-Item x .cla*\\runtime\\tasks\\ABC-123\\state.json"),
            ("R11-04", "PowerShell", "Copy-Item x -Destination .cla*\\runtime\\tasks\\ABC-123\\state.json"),
            # R11-05: un glob que alcanza `.git`
            ("R11-05", "Bash", "cp x .gi*/hooks/pre-commit"),
            ("R11-05", "Bash", "rm -rf .g*"),
            ("R11-05", "Bash", "echo x > .gi*/config"),
            ("R11-05", "PowerShell", "Copy-Item x .g*t\\hooks\\pre-commit"),
            ("R11-05", "PowerShell", "Remove-Item -Recurse -Force .gi?"),
            # R11-06: `?`
            ("R11-06", "Bash", "rm -rf .clau?e/harness"),
            ("R11-06", "Bash", "rm -rf .??????/harness"),
            ("R11-06", "Bash", "cp x .g?t/config"),
            ("R11-06", "PowerShell", "Remove-Item -Recurse -Force .claud?\\harness"),
            # R11-07: `[...]`
            ("R11-07", "Bash", "rm -rf .[c]laude/harness"),
            ("R11-07", "Bash", "rm -rf .[a-z]laude/harness"),
            ("R11-07", "Bash", "rm -rf .[!x]laude/harness"),
            ("R11-07", "Bash", "rm -rf .[^x]laude/harness"),
            ("R11-07", "Bash", "cp x .gi[t]/config"),
            ("R11-07", "Bash", "cp x .[cg]*/config"),
            ("R11-07", "PowerShell", "Remove-Item -Recurse -Force .[c]laude\\harness"),
            ("R11-07", "PowerShell", "Copy-Item x .gi[st]\\config"),
        ]
        for escenario, tool, comando in casos:
            _protegido(t, p, "r11-glob", escenario, tool, {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_01_la_posicion_respeta_el_cwd(t):
    """R11-01 — la raiz es la del proyecto: desde una subcarpeta, `../.cla*` es la autoridad; y la
    clase sale de `clasificar` con el proyecto y el cwd, sin el hook."""
    p = _con_tarea("r11-cwd")
    try:
        sub = p / "src"
        sub.mkdir()
        policy = _policy()
        for tool, comando in (("Bash", "rm -rf ../.cla*/harness"),
                              ("PowerShell", "Remove-Item -Recurse -Force ..\\.cla*\\harness"),
                              ("Bash", "cp x ../.gi?/config")):
            salida = policy.clasificar(tool, {"command": comando}, str(p), str(sub))
            t.verdadero("R11-01 desde src/ %s: protegido" % comando, salida.get("protected"))
    finally:
        W3._borrar(p)


def test_r11_14_un_comodin_solo_en_la_raiz(t):
    """R11-14 — `*`, `.*` y `**` en la raiz pueden ser `.claude` y `.git`: PowerShell expande `*`
    tambien a los nombres que empiezan con punto, y bash con `dotglob`. Escribir con ellos es
    protegido, del lado conservador."""
    p = _con_tarea("r11-comodin")
    try:
        for tool, comando in (("PowerShell", "Remove-Item -Recurse -Force *"),
                              ("PowerShell", "Remove-Item -Recurse -Force .\\*"),
                              ("Bash", "rm -rf *"),
                              ("Bash", "rm -rf .*"),
                              ("Bash", "rm -rf **/harness")):
            _protegido(t, p, "r11-comodin", "R11-14", tool, {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_15_el_glob_dentro_de_otro_shell(t):
    """R11-15 — el glob visible dentro de un comando entre comillas que corre otro shell (`bash -c
    "..."`, `powershell -Command "..."`) es el mismo texto: protegido."""
    p = _con_tarea("r11-anidado")
    try:
        for tool, comando in (("Bash", 'bash -c "rm -rf .cla*/harness"'),
                              ("Bash", "sh -c 'cp x .gi?/config'"),
                              ("PowerShell", 'powershell -Command "Remove-Item -Recurse -Force .cla*\\harness"'),
                              ("PowerShell", "pwsh -c 'Copy-Item x .cla*\\runtime\\tasks\\ABC-123\\state.json'")):
            _protegido(t, p, "r11-anidado", "R11-15", tool, {"command": comando})
        _no_protegido(t, p, "r11-anidado", "R11-15", "Bash", {"command": 'bash -c "rm -rf tmp/.cla*"'})
    finally:
        W3._borrar(p)


def test_r11_16_un_cd_en_el_mismo_comando(t):
    """R11-16 — un `cd` literal en el mismo comando cambia desde donde se resuelve lo relativo: la
    posicion de la raiz ya no se sabe, y un segmento que puede ser la autoridad cuenta en cualquier
    lugar de la ruta. Sin `cd`, la posicion sigue importando (R11-08)."""
    p = _con_tarea("r11-cd")
    try:
        for tool, comando in (("Bash", "cd src && rm -rf ../.cla*/harness"),
                              ("Bash", "cd .. && rm -rf %s/.cla*/harness" % p.name),
                              ("Bash", "pushd src; rm -rf ../.g?t; popd"),
                              ("PowerShell", "Set-Location src; Remove-Item -Recurse -Force ..\\.cla*\\harness"),
                              ("PowerShell", "Push-Location src; Copy-Item x ..\\.gi?\\config")):
            _protegido(t, p, "r11-cd", "R11-16", tool, {"command": comando})
        for tool, comando in (("Bash", "cd src && rm -f *.log"),
                              ("Bash", "cd build && rm -rf .cloud/*"),
                              ("Bash", "cd .. && rm -rf otro/.cla*/harness"),
                              ("PowerShell", "Set-Location src; Remove-Item -Force tmp\\*.tmp")):
            _no_protegido(t, p, "r11-cd", "R11-16", tool, {"command": comando})
    finally:
        W3._borrar(p)


# -- R11-08: un glob que no puede ser la autoridad -------------------------------------------------

def test_r11_08_un_glob_que_no_alcanza_la_autoridad(t):
    """R11-08 — un glob que no puede ser `.claude` ni `.git` en la raiz no es protegido: el segmento
    se compara contra el nombre entero, no por pedazos, y en su posicion."""
    p = _con_tarea("r11-benigno")
    try:
        for tool, comando in (("Bash", "rm -rf .cloud/*"),
                              ("Bash", "rm -rf .class/*"),
                              ("Bash", "rm -rf .clx*"),
                              ("Bash", "rm -rf .garbage/*"),
                              ("Bash", "rm -rf .gitignore*"),
                              ("Bash", "rm -rf .git?*"),
                              ("Bash", "rm -rf .claude?/x"),
                              ("Bash", "rm -rf .cl[x]ude/harness"),
                              ("Bash", "rm -rf ./src/*"),
                              ("Bash", "rm -rf tmp/.cla*"),
                              ("Bash", "rm -rf tmp/.cla*/harness"),
                              ("Bash", "rm -rf ./src/.cla*"),
                              ("Bash", "rm -f *.log"),
                              ("Bash", "rm -rf 2024*"),
                              ("Bash", "rm -rf logs/*"),
                              ("Bash", "cp x build/*.json"),
                              ("PowerShell", "Remove-Item -Recurse -Force .cloud\\*"),
                              ("PowerShell", "Remove-Item -Recurse -Force tmp\\.cla*"),
                              ("PowerShell", "Remove-Item -Force *.tmp")):
            _no_protegido(t, p, "r11-benigno", "R11-08", tool, {"command": comando})
    finally:
        W3._borrar(p)


# -- R11-09: lo que lee sigue leyendo --------------------------------------------------------------

def test_r11_09_un_glob_que_lee_no_se_vuelve_escritura(t):
    """R11-09 — leer con un glob que alcanza la autoridad sigue siendo READ_ONLY: la autoridad se
    protege de la escritura, no de la lectura."""
    p = _con_tarea("r11-lectura")
    try:
        policy = _policy()
        for tool, comando in (("Bash", "ls .cla*/algo"),
                              ("Bash", "cat .cla*/runtime/tasks/ABC-123/state.json"),
                              ("Bash", "ls .g?t"),
                              ("PowerShell", "Get-Content .cla*\\algo"),
                              ("PowerShell", "Get-ChildItem .cla*")):
            salida = policy.clasificar(tool, {"command": comando}, str(p), str(p))
            t.igual("R11-09 %s: READ_ONLY" % comando, "READ_ONLY", salida["class"])
            t.verdadero("R11-09 %s: no protegido" % comando, not salida.get("protected"))
            _no_protegido(t, p, "r11-lectura", "R11-09", tool, {"command": comando})
    finally:
        W3._borrar(p)


# -- R11-10: una MCP generica, frontera ------------------------------------------------------------

def test_r11_10_una_mcp_con_el_glob(t):
    """R11-10 (frontera, decision de la persona del 06-10-2026) — los valores de una MCP generica no
    son destinos tipados: el repo no sabe cual es ruta, destino o comando, y R11 no lo adivina por el
    nombre del campo. Un comodin en `path`, `destination`, `command`, `args` o `script` no es
    FLOW_AUTHORITY_PROTECTED, y la herramienta sigue UNRESOLVED_TOOL_CLASS. El literal `.claude` o
    `.git` en esos mismos campos sigue protegido. El glob tipado de una MCP es trabajo futuro."""
    p = _con_tarea("r11-mcp")
    try:
        for tool, entrada in (("mcp__fs__write_file", {"path": ".cla*/harness/x.py", "content": "x"}),
                              ("mcp__fs__delete", {"path": ".gi?/config"}),
                              ("mcp__fs__move_file", {"source": "x", "destination": "./.cla*/runtime/tasks/ABC-123/state.json"}),
                              ("mcp__shell__run", {"command": "rm -rf .cla*/harness"}),
                              ("mcp__shell__run", {"command": "rm", "args": ["-rf", ".cla*/harness"]}),
                              ("mcp__pwsh__run", {"script": "Remove-Item -Recurse -Force .cla*\\harness"})):
            _frontera_mcp(t, p, "r11-mcp", "R11-10", tool, entrada)
        for tool, entrada in (("mcp__fs__write_file", {"path": ".claude/harness/x.py", "content": "x"}),
                              ("mcp__fs__delete", {"path": ".git/config"}),
                              ("mcp__fs__move_file", {"source": "x", "destination": "./.claude/runtime/tasks/ABC-123/state.json"}),
                              ("mcp__shell__run", {"command": "rm -rf .claude/harness"}),
                              ("mcp__shell__run", {"command": "rm", "args": ["-rf", ".claude/harness"]}),
                              ("mcp__pwsh__run", {"script": "Remove-Item -Recurse -Force .claude\\harness"})):
            _protegido(t, p, "r11-mcp", "R11-10 literal", tool, entrada)
        for tool, entrada in (("mcp__fs__write_file", {"path": "src/.cla*/x.py", "content": "x"}),
                              ("mcp__fs__search", {"pattern": "*.py"}),
                              ("mcp__fs__write_file", {"path": ".cloud/x.py", "content": "x"})):
            _no_protegido(t, p, "r11-mcp", "R11-10", tool, entrada)
    finally:
        W3._borrar(p)


# -- R11-11 y R11-12: sin regresion ----------------------------------------------------------------

def test_r11_11_los_literales_siguen_protegidos(t):
    """R11-11 — los literales de `.claude` y `.git` siguen protegidos."""
    p = _con_tarea("r11-literal")
    try:
        for tool, comando in (("Bash", "rm -rf .claude/harness"),
                              ("Bash", "cp x .claude/runtime/tasks/ABC-123/state.json"),
                              ("Bash", "rm -rf .git"),
                              ("Bash", "rm -rf tmp/.claude"),
                              ("PowerShell", "Remove-Item -Recurse -Force .claude\\harness"),
                              ("PowerShell", "Copy-Item x .git\\hooks\\pre-commit")):
            _protegido(t, p, "r11-literal", "R11-11", tool, {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_12_el_guard_de_git_config_sigue(t):
    """R11-12 — el guard de `git config` no cambia: escribir es protegido, leer no."""
    p = _con_tarea("r11-git-config")
    try:
        for comando in ("git config core.fsmonitor calc", "git config --global core.hooksPath h"):
            _protegido(t, p, "r11-git-config", "R11-12", "Bash", {"command": comando})
        for comando in ("git config --get user.name", "git config --list"):
            _no_protegido(t, p, "r11-git-config", "R11-12", "Bash", {"command": comando})
    finally:
        W3._borrar(p)


# -- R11-13: la decision no lee el disco -----------------------------------------------------------

def test_r11_13_la_proteccion_no_depende_del_disco(t):
    """R11-13 — la proteccion sale del texto: con un proyecto que no existe en el disco y con el
    listado de carpetas prohibido, el glob que alcanza la autoridad sigue protegido y el que no la
    alcanza sigue sin serlo."""
    policy = _policy()
    inexistente = os.path.join(str(RAIZ), "no-existe-r11", "proyecto")
    originales = (os.listdir, os.scandir, glob.glob, glob.iglob)

    def _prohibido(*_a, **_k):
        raise AssertionError("R11-13: la politica listo el disco")

    os.listdir = os.scandir = glob.glob = glob.iglob = _prohibido
    try:
        protegidos = [policy.clasificar(tool, {"command": c}, inexistente, inexistente)
                      for tool, c in (("Bash", "rm -rf .cla*/harness"),
                                      ("PowerShell", "Remove-Item -Recurse -Force .g?t"),
                                      ("Bash", "cp x .[c]laude/runtime/tasks/ABC-123/state.json"))]
        benignos = [policy.clasificar("Bash", {"command": c}, inexistente, inexistente)
                    for c in ("rm -rf .cloud/*", "rm -rf tmp/.cla*")]
        mcp = policy.clasificar("mcp__fs__delete", {"path": ".cla*/harness"}, inexistente, inexistente)
    finally:
        os.listdir, os.scandir, glob.glob, glob.iglob = originales
    t.verdadero("R11-13 sin el disco: los globs de la autoridad, protegidos",
                all(s.get("protected") for s in protegidos))
    t.verdadero("R11-13 sin el disco: los benignos, no", not any(s.get("protected") for s in benignos))
    t.verdadero("R11-13 sin el disco: la MCP generica con un glob, frontera (no protegida, sigue"
                " UNRESOLVED_TOOL_CLASS)",
                not mcp.get("protected") and mcp["class"] == "UNRESOLVED_TOOL_CLASS")


# -- Segunda pasada de R11: el comodin cuenta solo en el destino de lo que escribe -----------------
#
# R11-17 a R11-24 de final-qualification.md («R11, segunda pasada»). La revision independiente de la
# primera pasada encontro falsos positivos (un `*` fuera de un destino) y caminos que no veia (clases
# POSIX, escapes de Bash y de PowerShell, llaves, un `cd` adentro de un bloque). La regla: un
# comodin no es autoridad; lo es el destino de una operacion que escribe, cuando su sintaxis
# textual soportada puede alcanzar `.claude` o `.git` en la raiz.

def test_r11_17_fp1_un_comodin_que_lista(t):
    """R11-17 (FP1, falso positivo previo) — `ls *` y `Get-ChildItem *` no escriben: el `*` no es un
    destino. No son FLOW_AUTHORITY_PROTECTED."""
    p = _con_tarea("r11-fp1")
    try:
        for tool, comando in (("Bash", "ls *"),
                              ("Bash", "ls -la *"),
                              ("PowerShell", "Get-ChildItem *"),
                              ("PowerShell", "Get-ChildItem -Force *")):
            _no_protegido(t, p, "r11-fp1", "R11-17", tool, {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_18_fp2_una_mcp_con_sql(t):
    """R11-18 (FP2, falso positivo previo) — el `*` de un SQL o de un texto que una MCP recibe no es
    una ruta: no es FLOW_AUTHORITY_PROTECTED."""
    p = _con_tarea("r11-fp2")
    try:
        for tool, entrada in (("mcp__db__query", {"query": "SELECT * FROM t"}),
                              ("mcp__db__query", {"sql": "SELECT * FROM t WHERE id = 1"}),
                              ("mcp__db__query", {"sql": "SELECT count(*) FROM t"}),
                              ("mcp__db__batch", {"statements": ["SELECT * FROM a", "SELECT * FROM b"]}),
                              ("mcp__notes__create", {"title": "rating", "text": "* * *"})):
            _no_protegido(t, p, "r11-fp2", "R11-18", tool, entrada)
    finally:
        W3._borrar(p)


def test_r11_19_fp3_un_comodin_en_un_mensaje(t):
    """R11-19 (FP3, falso positivo previo) — el `*` de un mensaje o de un texto entre comillas no es
    un destino, aunque el comando escriba: `git commit -m "fix *"`, `echo "*"`, `echo '*' > x`."""
    p = _con_tarea("r11-fp3")
    try:
        for tool, comando in (("Bash", 'git commit -m "fix *"'),
                              ("Bash", "git commit -m 'fix .cla* pattern'"),
                              ("Bash", 'git tag -a v1 -m "release *"'),
                              ("Bash", 'echo "*"'),
                              ("Bash", "echo '*' > notes.txt"),
                              ("Bash", "printf '%s' '*' >> out.txt"),
                              ("PowerShell", 'git commit -m "fix *"'),
                              ("PowerShell", 'Write-Output "*"'),
                              ("PowerShell", "Set-Content -Path notes.txt -Value '*'")):
            _no_protegido(t, p, "r11-fp3", "R11-19", tool, {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_20_b1_clases_posix(t):
    """R11-20 (B1, bypass previo) — una clase POSIX (`[[:alpha:]]`) adentro de `[...]` que puede ser
    la letra de `.claude` o `.git`, en el destino de lo que escribe: protegido. Una clase que no
    puede (`[[:digit:]]`), no."""
    p = _con_tarea("r11-b1")
    try:
        for comando in ("rm -rf .[[:alpha:]]laude/harness",
                        "rm -rf .[[:lower:]][[:alnum:]]aude/harness",
                        "cp x .gi[[:alpha:]]/config"):
            _protegido(t, p, "r11-b1", "R11-20", "Bash", {"command": comando})
        for comando in ("rm -rf .[[:digit:]]laude/harness",
                        "rm -rf .gi[[:space:]]/config"):
            _no_protegido(t, p, "r11-b1", "R11-20", "Bash", {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_21_b2_escapes_de_bash(t):
    """R11-21 (B2, bypass previo) — la barra invertida de Bash en el destino: un escape que deja el
    comodin activo o arma el nombre literal (`.cla\\ude`, `.c\\la*`, `\\.cla*`) es protegido; uno que
    vuelve literal el comodin (`.cla\\*`, `.\\[c]laude`, `.clau\\?e`) nombra otra carpeta, no."""
    p = _con_tarea("r11-b2")
    try:
        for comando in ("rm -rf .cla\\ude/harness",
                        "rm -rf .c\\la*/harness",
                        "rm -rf \\.cla*/harness",
                        "cp x .g\\it/config"):
            _protegido(t, p, "r11-b2", "R11-21", "Bash", {"command": comando})
        for comando in ("rm -rf .cla\\*/harness",
                        "rm -rf .\\[c]laude/harness",
                        "rm -rf .clau\\?e/harness"):
            _no_protegido(t, p, "r11-b2", "R11-21", "Bash", {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_22_b3_llaves(t):
    """R11-22 (B3, bypass previo) — la expansion de llaves es textual: `{.cla*,x}/harness` da
    `.cla*/harness`. Protegido si alguna alternativa alcanza la autoridad; `{src,tmp}/*`, no. La
    expansion esta acotada: pasado el limite, con una alternativa que puede ser la autoridad,
    protegido; sin ninguna, no, y la decision no tarda."""
    import time
    p = _con_tarea("r11-b3")
    try:
        for comando in ("rm -rf {.cla*,x}/harness",
                        "rm -rf {.cla*,src}/x",
                        "rm -rf .{cla,xyz}*/harness",
                        "rm -rf {.claude,x}/harness",
                        "rm -rf {a,{b,.cl*}}/harness",
                        "cp x {a,.gi?}/config",
                        "rm -rf {.cla*,y}/" + "{a,b}" * 24,
                        "rm -rf {" + ",".join("x%d" % n for n in range(600)) + ",.cla*}/harness"):
            _protegido(t, p, "r11-b3", "R11-22", "Bash", {"command": comando})
        # Una MCP generica no es un comando tipado: frontera, como R11-10.
        _frontera_mcp(t, p, "r11-b3", "R11-22", "mcp__shell__run", {"command": "rm -rf {.cla*,x}/harness"})
        for comando in ("rm -rf {src,tmp}/*",
                        "rm -rf {src,tmp}/.cla*",
                        "rm -f {a,b}.log",
                        "rm -f " + "{a,b}" * 24 + ".log"):
            _no_protegido(t, p, "r11-b3", "R11-22", "Bash", {"command": comando})
        policy = _policy()
        inicio = time.perf_counter()
        policy.clasificar("Bash", {"command": "rm -f " + "{a,b}" * 24 + ".log"}, str(p), str(p))
        policy.clasificar("Bash", {"command": "rm -rf {.cla*,y}/" + "{a,b}" * 24}, str(p), str(p))
        t.verdadero("R11-22 la expansion acotada tarda menos de un segundo",
                    time.perf_counter() - inicio < 1.0)
    finally:
        W3._borrar(p)


def test_r11_23_b4_cd_en_un_bloque(t):
    """R11-23 (B4, bypass previo) — un `cd` literal adentro de un subshell, de un bloque o de `bash
    -c '...'` cambia desde donde se resuelve el destino, como en R11-16. Protegido cuando el destino
    resuelto puede ser la autoridad; no, cuando no."""
    p = _con_tarea("r11-b4")
    try:
        (p / "src").mkdir()
        for comando in ("(cd src && rm -rf ../.cla*/harness)",
                        "{ cd src; rm -rf ../.cla*/harness; }",
                        "bash -c 'cd src && rm -rf ../.cla*/harness'",
                        "sh -c \"cd src; cp x ../.gi?/config\"",
                        "(cd src; cd ..; rm -rf .cla*/harness)"):
            _protegido(t, p, "r11-b4", "R11-23", "Bash", {"command": comando})
        for comando in ("(cd src && rm -f *.log)",
                        "{ cd src; rm -rf build/*; }",
                        "bash -c 'cd src && rm -rf tmp/*'"):
            _no_protegido(t, p, "r11-b4", "R11-23", "Bash", {"command": comando})
    finally:
        W3._borrar(p)


def test_r11_24_b5_backtick_de_powershell(t):
    """R11-24 (B5, bypass previo) — el backtick de PowerShell en el destino. Sin comillas, `` `c ``
    es `c` y `` `* `` sigue siendo comodin para el provider: `` .`cla* ``, `` .cla`* `` y
    `` .`claude `` son protegidos. Doble backtick o comillas simples dejan el `` `* `` para el
    provider, que lo lee literal: no."""
    p = _con_tarea("r11-b5")
    try:
        for comando in ("Remove-Item -Recurse -Force .`cla*\\harness",
                        "Remove-Item -Recurse -Force .cla`*\\harness",
                        "Remove-Item -Recurse -Force .`claude\\harness",
                        "Copy-Item x .g`i?\\config"):
            _protegido(t, p, "r11-b5", "R11-24", "PowerShell", {"command": comando})
        for comando in ("Remove-Item -Recurse -Force .cla``*\\harness",
                        "Remove-Item -Recurse -Force '.cla`*\\harness'"):
            _no_protegido(t, p, "r11-b5", "R11-24", "PowerShell", {"command": comando})
    finally:
        W3._borrar(p)


# -- H1: el valor de una opcion de git, por subcomando ---------------------------------------------
#
# H1 de final-qualification.md («La tercera revision arquitectonica»). Antes, cualquier palabra de
# opciones cortas con `m` o `F` se descartaba como mensaje, y si la letra iba ultima, tambien la
# palabra siguiente. Ahora solo una opcion reconocida para ese subcomando como opcion con valor
# saca su valor de los destinos; una desconocida o un grupo que la tabla no descompone, no.

def _git_casos(t, p, nombre, escenario, protegidos=(), no_protegidos=()):
    for comando in protegidos:
        _protegido(t, p, nombre, escenario, "Bash", {"command": comando})
    for comando in no_protegidos:
        _no_protegido(t, p, nombre, escenario, "Bash", {"command": comando})


def test_r11_h1_a_una_corta_sin_valor_en_su_subcomando(t):
    """R11-H1-A — `-m` no lleva valor en `checkout` ni en `restore` (es `--merge`): el posicional
    que sigue es un destino, y si puede ser la autoridad, protegido."""
    p = _con_tarea("r11-h1-a")
    try:
        _git_casos(t, p, "r11-h1-a", "R11-H1-A",
                   protegidos=("git checkout -m .cla*/harness",
                               "git restore -m .cla*/harness"))
    finally:
        W3._borrar(p)


def test_r11_h1_b_la_misma_letra_con_valor(t):
    """R11-H1-B — `-m` y `--message` llevan el mensaje en `commit`, `tag`, `merge`, `stash` y
    `notes`: su valor no es un destino, aunque sea un glob que alcanzaria la autoridad."""
    p = _con_tarea("r11-h1-b")
    try:
        _git_casos(t, p, "r11-h1-b", "R11-H1-B",
                   no_protegidos=("git commit -m .cla*/harness",
                                  "git commit --message .cla*/harness",
                                  "git tag -a v1 -m .cla*/harness",
                                  "git merge -m .cla*/harness topic",
                                  "git stash push -m .cla*/harness",
                                  "git notes add -m .cla*/harness"))
    finally:
        W3._borrar(p)


def test_r11_h1_c_un_valor_pegado(t):
    """R11-H1-C — un valor pegado a su opcion (`-mfix`, `--message=fix`, `-amfix`) ocupa solo esa
    palabra: el posicional siguiente sigue siendo destino. Una opcion corta que no es de mensaje
    con un valor pegado que termina en `m` (`-bitem`) tampoco se lleva el posicional."""
    p = _con_tarea("r11-h1-c")
    try:
        _git_casos(t, p, "r11-h1-c", "R11-H1-C",
                   protegidos=("git commit -mfix .cla*/harness",
                               "git commit --message=fix .cla*/harness",
                               "git commit -amfix .cla*/harness",
                               "git worktree add -bitem .cla*/wt"))
    finally:
        W3._borrar(p)


def test_r11_h1_d_la_forma_de_f(t):
    """R11-H1-D — lo mismo con `-F`: en `commit` lleva el archivo del mensaje, separado o pegado, y
    ese valor no es destino; el posicional que sigue, si. Un valor pegado de otra opcion que termina
    en `F` (`-bfixF`) no se lleva el posicional."""
    p = _con_tarea("r11-h1-d")
    try:
        _git_casos(t, p, "r11-h1-d", "R11-H1-D",
                   protegidos=("git commit -F msg.txt .cla*/harness",
                               "git commit -Fmsg.txt .cla*/harness",
                               "git worktree add -bfixF .cla*/wt"),
                   no_protegidos=("git commit -F .cla*/harness",
                                  "git tag -a v1 -F .cla*/harness"))
    finally:
        W3._borrar(p)


def test_r11_h1_e_una_opcion_desconocida_no_consume(t):
    """R11-H1-E — una opcion que la tabla no reconoce para ese subcomando no saca de los destinos la
    palabra que sigue: `-um` en `commit` es `-u` con el valor `m`; `--squash` en `merge` no lleva
    valor; un subcomando que no esta en la tabla no tiene opciones con valor."""
    p = _con_tarea("r11-h1-e")
    try:
        _git_casos(t, p, "r11-h1-e", "R11-H1-E",
                   protegidos=("git commit -um .cla*/harness",
                               "git merge --squash .cla*/harness",
                               "git commit --frobnicate .cla*/harness",
                               "git frob -m .cla*/harness",
                               "git frob -F .cla*/harness"))
    finally:
        W3._borrar(p)


def test_r11_h1_f_el_destino_positivo_de_git(t):
    """R11-H1-F (cierra el gap de E1 «extraccion positiva del destino de git») — el posicional de un
    git que escribe, y el valor de `-C`, son destinos: protegidos si pueden ser la autoridad; no, si
    no pueden."""
    p = _con_tarea("r11-h1-f")
    try:
        _git_casos(t, p, "r11-h1-f", "R11-H1-F",
                   protegidos=("git rm -r .cla*/harness",
                               "git mv x .cla*/harness/x",
                               "git checkout -- .cla*/harness",
                               "git restore --source=HEAD .cla*/harness",
                               "git worktree add .cla*/wt",
                               "git clone https://example.invalid/r.git .g?t",
                               "git -C .cla*/harness rm x"),
                   no_protegidos=("git rm -r src/*.log",
                                  "git mv a src/b",
                                  "git checkout -- tmp/.cla*"))
    finally:
        W3._borrar(p)


def test_r11_h1_g_el_mensaje_sigue_sin_falso_positivo(t):
    """R11-H1-G — los controles negativos del mensaje de git siguen sin falso positivo, tambien
    agrupado (`-am`, `-sm`) y con la opcion larga."""
    p = _con_tarea("r11-h1-g")
    try:
        _git_casos(t, p, "r11-h1-g", "R11-H1-G",
                   no_protegidos=('git commit -m "fix *"',
                                  "git commit -m 'fix .cla* pattern'",
                                  'git tag -a v1 -m "release *"',
                                  'git commit -am "fix *"',
                                  "git commit -sm .cla*/harness",
                                  "git commit --message 'fix .cla*'",
                                  "git commit -m arreglo"))
    finally:
        W3._borrar(p)


def test_r11_h1_h_el_guard_de_git_config(t):
    """R11-H1-H — el guard de `git config` no cambia con la tabla de opciones."""
    p = _con_tarea("r11-h1-h")
    try:
        _git_casos(t, p, "r11-h1-h", "R11-H1-H",
                   protegidos=("git config core.fsmonitor calc",
                               "git config --global core.hooksPath h"),
                   no_protegidos=("git config --get user.name",
                                  "git config --list"))
    finally:
        W3._borrar(p)
