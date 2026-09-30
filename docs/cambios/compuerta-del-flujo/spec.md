# Flow Governance, Wave 3 — la sesión, su tarea y la compuerta del flujo en los hooks

**Estado:** verificado y cerrado · **Fecha:** 30-09-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Después de la Wave 2 cada tarea tiene su estado en `.claude/runtime/tasks/<KEY>/state.json`, pero
nadie lo mira mientras se trabaja. Una tarea `BLOCKED` por `REPOSITORY_MISMATCH` se puede seguir
implementando: el bloqueo solo lo ve quien corre `flujo <KEY> --status`.

Esta Wave conecta ese estado con los tres hooks que corren durante la sesión:

```
session_id  ->  tarea de la sesión  ->  task-flow-state  ->  compuerta  ->  allow / deny
```

Y lo hace sin la trampa que dejó anotada la aceptación de la Wave 2: `active-task.json` es la
última tarea que reconcilió **cualquier** comando del proyecto, no la de una sesión. Dos sesiones
sobre el mismo proyecto se lo pisan. Por eso:

```text
hook decision
!=
active-task.json alone
```

## Qué queda afuera

- **Responder, aprobar, elegir una alternativa, cancelar o retomar** (`--answer`, `--approve`,
  `--alternative`, `--cancel`). Son la Wave 4. Una tarea `WAITING_FOR_HUMAN_APPROVAL` sigue
  esperando: esta Wave no le da salida.
- **Ampliar el matcher de `PreToolUse` a la lectura.** `Read`, `Glob` y `Grep` se clasifican pero no
  llegan al hook: son de lectura, y el `.env` lo sigue cerrando `permissions.deny`. La delegación sí
  se agregó (ver abajo).
- **Los hallazgos diferidos:** `AlmacenSecretos.set/remove`, `PlanInvalido` en `main`, el stub de
  Python de Microsoft Store, el conteo de `CLAUDE.md`, la semántica de capacidades y el reporte de
  seguridad `UNRESOLVED` (Wave 5), el registro de `dev-iniciador-code` (Wave 6) y
  `refutacion.compilar` usado como biblioteca.
- **Cambiar `task-flow-state/1.0`, `active-task/1.0` o `flow-required-inputs/1.0`.**

## Las decisiones, y por qué

### El `session_id` es real, y es la identidad

Los payloads grabados de los tres eventos (`tests/payloads/`) traen `session_id`, y el mismo valor
en los tres. La Context Bar ya decide por él en producción (su señal de vida y el libro por
sesión). No se inventa un UUID, ni se usa el PID, un timestamp o `active-task.json` en su lugar.
Sin `session_id` (`SESSION_ID_UNAVAILABLE`) no hay binding: se resuelve como una sesión sin tarea.

### `session-task-binding/1.0`, un archivo por sesión

```
.claude/runtime/sessions/<SAFE_SESSION_ID>/task.json
{schema_version, sessionId, taskKey, source, updatedAt}
```

Forma en `comun/schemas/session-task-binding.schema.json`. `source` es `user-prompt` o
`harness-command`. No guarda el prompt, ni `tool_input`, ni secretos, ni el TaskContext, ni el plan,
ni el estado del flujo.

`<SAFE_SESSION_ID>` es el `session_id` tal cual si es seguro como carpeta en Windows: minúsculas,
dígitos, `.`, `_` y `-`, empieza con letra o dígito, no termina en punto y no es un nombre reservado
(`con`, `nul`, `com1`…). Si no, es `_` seguido del SHA-256 del `session_id`: el `_` inicial no lo
puede tener un id seguro, así que no hay colisión, y dos ids que solo difieren en mayúsculas no caen
en la misma carpeta de NTFS. Es trazable: el archivo guarda el `sessionId` original y se lee solo si
coincide con el del evento.

La escritura es atómica (temporal, flush, fsync, `os.replace`).

### Cuatro estados de la resolución, aparte del estado de la tarea

| Estado | Cuándo |
|---|---|
| `SESSION_TASK_BOUND` | La sesión tiene un binding válido |
| `SESSION_TASK_UNRESOLVED` | Sin binding y con cero o una tarea con estado en el proyecto |
| `SESSION_TASK_AMBIGUOUS` | Sin binding y con dos o más tareas con estado |
| `SESSION_TASK_STALE` | Hay un binding para la sesión y no se puede creer: ilegible, de otra versión, o de otro `sessionId` |

No se mezclan con `task-flow-state/1.0`: son de la sesión, no de la tarea.

Prioridad para saber qué tarea trabaja una sesión:

1. el binding de la sesión;
2. una clave declarada en el prompt (`UserPromptSubmit`), que crea o reemplaza el binding;
3. la clave de un comando del Harness parseable (`dev-harness.py plan ABC-123 …`), que crea el
   binding si no había;
4. `active-task.json`, **solo** como sugerencia en `SessionStart`. `PreToolUse` no lo lee.

Con una sola tarea con estado y sin binding, la compuerta evalúa esa (`single-candidate`): no elige
entre varias, y ser estricta con la única que hay no deja pasar nada que no pasaría con ella
declarada. Con dos o más, `SESSION_TASK_AMBIGUOUS`: no elige la activa, ni la última, ni la primera.

El comando de un Harness con clave se evalúa contra **su** clave, aunque la sesión esté vinculada a
otra: es la tarea cuyos artefactos toca.

### La clave declarada, con un parser estricto

Una clave es `[A-Z][A-Z0-9_]*-[0-9]+`, en mayúsculas. Cuenta solo si una línea del prompt la declara:

- la línea es solo la clave (`ABC-123`), o `tarea`, `task`, `ticket` o `issue` y la clave, y nada
  después salvo puntuación; o
- empieza con un verbo de continuidad (`seguimos con`, `sigamos con`, `continuamos con`, `retomamos`,
  `trabajamos en`, `vamos con`, `pasamos a`, `arrancamos con`, `working on`, `continue with`…) y
  sigue la clave, que ahí sí puede seguir con texto.

Sin verbo, una línea que empieza con la clave y sigue con texto es un log («ABC-123 failed at line
3», «task ABC-123 failed with …»), no una declaración.

Antes se sacan los bloques de código y el código en línea. La clave tiene que terminar en un espacio,
en puntuación o en el fin de la línea: `ABC-123/`, `ABC-123.json` o `ABC-123-x` no cuentan. Una clave
en una URL, un JSON, un log o un fuente no está declarada. Dos claves distintas declaradas en el
mismo prompt no crean binding.

### La clasificación de una herramienta

`comun/hooks/lib/tool_policy.py`, de `tool_name` y la forma real de `tool_input`:

| Clase | Qué |
|---|---|
| `READ_ONLY` | `Read`, `Glob`, `Grep`, `LS`, `NotebookRead`, `TodoWrite`, `BashOutput`, `KillBash` (el matcher sin anclar los alcanza por `Write` y `Bash`; leen o paran un shell de fondo, no el proyecto); un `Bash`/`PowerShell` cuyos segmentos son todos de una lista de lectura (`ls`, `cat`, `git status`, `git log`, `Get-Content`…), sin redirección de escritura ni sustitución de comandos; `dev-harness.py harness`, `plan --plantilla`, `refute --status`/`--summary`, `contabilidad --barra` |
| `FLOW_RECOVERY` | `dev-harness.py flujo <KEY> --status`, `contexto <KEY>`, `estado`, `setup`, `reconfigurar`, `fuentes` sin `--aceptar` |
| `WORKFLOW_ADVANCING` | `dev-harness.py plan <KEY>` (PLANNING), `refute <KEY> --compile`/`--record`/`--unit` (REFUTATION); `Task`/`Agent`, la delegación (EXECUTION) |
| `MUTATING` | `Write`, `Edit`, `MultiEdit`, `NotebookEdit`; un comando con redirección de escritura o un programa que escribe (`rm`, `mv`, `git commit`, `Set-Content`…); `seguridad`, `contabilidad --ingerir`, `fuentes --aceptar` |
| `UNRESOLVED_TOOL_CLASS` | Lo demás. Se trata como `MUTATING` |

🔴 Un comando o una ruta que nombra `.env` nunca es `READ_ONLY` ni `FLOW_RECOVERY`: es
`UNRESOLVED_TOOL_CLASS`. Cuenta también un glob que lo alcanza (`.en?`, `.[e]nv`, `*`) y una
variable, que puede valer cualquier ruta. La recuperación del flujo no abre el `.env`.

Tampoco son de lectura un scriptblock de PowerShell (`{ … }`), `sed` (sus scripts escriben y
ejecutan), `git … --output`, un `git` con `-c`, `--config-env`, `--exec-path`, `-C`, `--git-dir` o
`--work-tree` (una configuración, la de la línea o la de otro repositorio, puede correr un programa), `git diff --ext-diff`, `git grep -O`, `rg --pre`, `tree -o` ni
`hostname <nombre>`. La CLI del Harness es la instalada en este proyecto:
`.claude/harness/bin/desarrollo/dev-harness.py` relativa y corrida desde la raíz, o su ruta absoluta
dentro de la raíz. Otro `dev-harness.py` es un script cualquiera, también el relativo corrido desde
una subcarpeta.

### La delegación llega al hook

El matcher de `PreToolUse` en `comun/settings/hooks.plantilla.json` pasa a ser
`Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell|^Agent$|^Task$`. Claude Code lo evalúa como una
regex sin anclar: `Agent` es la herramienta que delega en un subagente y `Task` su nombre anterior,
y las dos alternativas van ancladas para no alcanzar a `TaskCreate`, `TaskOutput` y parecidos. Un
deny a esa llamada impide que el subagente arranque. PostToolUse no cambia. Las herramientas que usa
un subagente adentro disparan PreToolUse con el `session_id` de la sesión que lo lanzó, así que
también las evalúa la misma compuerta.

### La compuerta

`comun/hooks/lib/flow_gate.py`. `READ_ONLY` y `FLOW_RECOVERY` pasan siempre (sujetas al Secret
Guard). Para el resto:

1. Sin ningún `state.json` en el proyecto no hay flujo que gobernar, haya o no binding, y el hook se
   comporta como antes. Un binding solo no traba un proyecto que nunca pasó por `contexto`, ni un
   harness sin `desarrollo` (que no tiene cómo salir de ahí).
2. Se resuelve la tarea (arriba). `AMBIGUOUS` o `STALE`: **deny**.
3. Se lee su estado con `estado.leer`. Roto: `TASK_FLOW_STATE_INVALID`. Ausente:
   `TASK_FLOW_STATE_MISSING`. Presente: `estado.vigencia_local`, que recalcula `contextRef`,
   `planRef` y `refutationRef` de los artefactos y la parte local de `repositoryRef` —los remotos
   del checkout, con `repositorio.remotos`, que corre solo `git remote -v`: local, sin red, sin
   `.env`— y se los pasa a `estado.vigencia()`. Un remoto cambiado sin reconciliar es
   `REPOSITORY_STATE_STALE` y deny. La identidad del repositorio de la TAREA pide la URL de GitLab
   del `.env` y no se recalcula en el hook: si cambia la ficha, cambia el TaskContext, y eso ya es
   `TASK_CONTEXT_STALE`. `SessionStart`, que solo muestra, no corre `git remote -v`.

   El hook le pone a `git remote -v` su propio límite, `flow_gate.TIMEOUT_REMOTOS` = 1,5 s; la CLI
   sigue con los 10 s de `repositorio.remotos`. Medido con N=200: mediana 50 ms, p95 69 ms, p99
   91 ms, máximo 258 ms. Vencido, `remotos(..., estricto=True)` levanta `RemotosSinRespuesta` en vez
   de devolver lo mismo que un checkout sin remotos, y la compuerta falla cerrada con
   `FLOW_GATE_UNRESOLVED`: nunca allow, tampoco con la lista guardada vacía.

   El corte tiene que llegar EN el límite. En Windows `git` es un lanzador (`cmd\git.exe`) que deja
   al git de verdad como nieto con los pipes abiertos, y `subprocess.run(timeout=…)` mata al hijo pero
   espera esos pipes. El camino estricto manda la salida a un archivo temporal, espera solo al
   proceso y, vencido, mata el árbol entero (`taskkill /T` en Windows, el grupo en POSIX).
4. `estado.puede_avanzar(doc, vigencia)` —la misma condición de `permisos()`— dice si pasa:
   `BLOCKED`, `WAITING_FOR_HUMAN_APPROVAL`, terminal, con bloqueos, con `stale` o con vigencia no
   vacía no pasan. **Deny, nunca ask**: un `ask` dejaría saltar un `HARD_BLOCKER` aprobando una
   herramienta.
5. Excepción: un comando del Harness `WORKFLOW_ADVANCING` que corre la etapa donde el flujo tiene que
   retomar, o una anterior (`estado.reanudar_desde`), pasa como **revalidación**. Son solo `plan` y
   `refute --compile` (y `contexto`, que ya es recuperación): aplican su propia compuerta (Wave 1) y
   reconcilian el estado. `refute --record` y `--unit` no tienen compuerta propia y no revalidan. Sin esto, un `PLAN_NOT_READY` que
   solo se arregla replanificando no tendría salida. Con `WAITING_FOR_HUMAN_APPROVAL` no hay
   excepción: la salida es una decisión humana, de la Wave 4.

Un fallo interno de la compuerta con una herramienta que no es `READ_ONLY` ni `FLOW_RECOVERY` es
`FLOW_GATE_UNRESOLVED` y **deny**: el `invoke_hook` de siempre lo convertiría en silencio, que acá
sería permiso para escribir.

### Secret Guard × Flow Gate, en una sola emisión

| Secret Guard | Flow Gate | Sale |
|---|---|---|
| alta | cualquiera | **deny** del secreto (la compuerta ni se evalúa) |
| media | deny | **deny** del flujo, con el aviso del secreto al lado |
| media | pasa | **ask** del secreto |
| nada | deny | **deny** del flujo |
| nada | pasa | silencio |

El flujo nunca baja un deny a ask ni a allow. `pre-tool-use.py` compone los dos y emite una vez.

### Lo que ve la persona

`UserPromptSubmit` lee el prompt, vincula la sesión si declara una clave, lee el estado local y, si
la tarea de la sesión no puede avanzar, inyecta el porqué. Para un `PERSISTENT_CONFIG_INPUT` la
posición y el enlace salen de `entrada_humana.localizar` y el texto de `entrada_humana.renderizar`:
no hay otro localizador. Nunca un valor.

No repite el bloque: guarda la huella (SHA-256 de tarea, etapa, estado, bloqueos, vigencia,
interacción pendiente y su ubicación) en `.claude/runtime/sessions/<SAFE>/notice.json`
(`session-flow-notice/1.0`). Con la misma huella sale una línea; con otra, el bloque entero. Si la
tarea vuelve a poder avanzar, la huella se borra y un bloqueo que vuelve se informa entero.

`SessionStart` agrega una línea: la continuidad de la tarea vinculada, o, sin binding, la última
tarea tocada **como sugerencia**. Nunca la explicación completa.

Ninguno de los tres sale a la red, llama a un modelo, consulta Jira o GitLab, ni recorre el
repositorio. `SessionStart` y `UserPromptSubmit` siguen callando ante un error propio.

### E-25 de la Context Bar, acotado

E-25 (`docs/cambios/bloque-1-context-bar`) barre todo párrafo que nombra VS Code y exige que lo
niegue. Esta Wave agrega enlaces `vscode://file/…` para abrir el `.env` en una línea, y eso no es una
integración nativa con la barra de estado. El barrido deja de contar el esquema `vscode://` y el
identificador `vscodeUri`; cualquier otra mención sigue obligada a negar, y las dos afirmaciones
testigo se siguen agarrando. El test no se borra. La Context Bar sigue siendo la `statusLine` de
Claude Code, con el Bloque 4 como fuente.

## Escenarios

Cada `E-nn` es el `W3-0nn` de la Wave con el mismo número. De E-49 en adelante los pidió el runtime.
Todos llevan `rojo visto` salvo donde se dice.

- **E-01** — `SessionStart` lee el `session_id`: con binding, la línea de continuidad nombra esa
  tarea. `rojo visto`
- **E-02** — `UserPromptSubmit` lee el `session_id`: el binding queda en la carpeta de esa sesión.
  `rojo visto`
- **E-03** — `PreToolUse` lee el `session_id`: evalúa la tarea del binding de esa sesión. `rojo visto`
- **E-04** — Un binding es estable: otro prompt sin clave no lo cambia y tres `PreToolUse` evalúan la
  misma tarea. `rojo visto`
- **E-05** — Dos sesiones vinculan dos tareas distintas, cada una en su archivo. `rojo visto`
- **E-06** — `active-task.json` no pisa el binding de otra sesión. `rojo visto`
- **E-07** — `active-task.json` no autoriza una mutación: con dos tareas y el puntero en la activa,
  una sesión sin binding recibe deny; y ningún módulo de `PreToolUse` lo nombra. `rojo visto`
- **E-08** — «Seguimos con ABC-123» crea el binding `user-prompt` a `ABC-123`. `rojo visto`
- **E-09** — Un prompt ambiguo no inventa tarea: claves en código, URL, JSON, log, dos claves
  distintas, minúsculas o `ABC-123.json`. `rojo visto`
- **E-10** — Dos tareas, sin binding, `Write`: deny con `SESSION_TASK_AMBIGUOUS`. `rojo visto`
- **E-11** — Un binding roto, de otra versión o de otro `sessionId` es `SESSION_TASK_STALE`: deny a
  la mutación, la lectura pasa. `rojo visto`
- **E-12** — El binding tiene exactamente sus cinco campos; ni el prompt ni un secreto sintético del
  prompt aparecen en `.claude/runtime/sessions/`. `rojo visto`
- **E-13** — `SessionStart` con binding a una tarea bloqueada: una línea compacta, sin el enlace ni
  la explicación del `.env`. `rojo visto`
- **E-14** — `SessionStart` sin binding no inventa tarea: la sugerencia dice que no es una elección,
  y sin tareas no dice nada del flujo. `rojo visto`
- **E-15** — `UserPromptSubmit` con la tarea bloqueada inyecta el bloqueo, con su id y su código.
  `rojo visto`
- **E-16** — Un secreto pendiente sale con la URI de VS Code, la línea, el placeholder y «No pegues»,
  y sin el valor. `rojo visto`
- **E-17** — El mismo bloqueo en el turno siguiente: una línea, no el bloque. `rojo visto`
- **E-18** — Un bloqueo distinto, u otra ubicación del input, se informa entero. `rojo visto`
- **E-19** — Secreto de confianza alta con la tarea bloqueada: deny del secreto. `rojo visto, por mutación`
- **E-20** — Secreto ambiguo con la tarea sana: ask, en una sola emisión; con la tarea bloqueada,
  deny. `rojo visto`
- **E-21** — `BLOCKED` + `Write`/`Edit`/`MultiEdit`/`NotebookEdit`: deny. `rojo visto`
- **E-22** — `BLOCKED` en PLANNING + `refute --compile` o `Task`: deny. `rojo visto`
- **E-23** — `BLOCKED` + `git status`, `ls`, `Get-Content`, `Read`, `BashOutput` o `KillBash`: pasa. `rojo visto, por mutación`
- **E-24** — `BLOCKED` + `flujo <KEY> --status` o `contexto <KEY>`: pasa. `rojo visto`
- **E-25** — Un comando que no se sabe clasificar (`npm install`, `curl …`, `$(…)`) con la tarea
  bloqueada: deny con `FLOW_TOOL_CLASS_UNRESOLVED`. `rojo visto`
- **E-26** — `cat .env`, `Get-Content .env`, `type .env`, `Read .env`: nunca `READ_ONLY` ni
  `FLOW_RECOVERY`; con la tarea bloqueada, deny. `rojo visto`
- **E-27** — `PreToolUse` no consulta Jira: con el transporte de integraciones que falla, decide
  igual. `rojo visto`
- **E-28** — `PreToolUse` no consulta GitLab ni lee su URL por ninguna vía: no abre el `.env` ni
  `harness.integraciones.json`, y no llama a `entorno.resolver`, que es la que la resuelve también
  del entorno del proceso. El único proceso que corre es `git -C <raíz> remote -v`, local, a lo sumo
  una vez; si se vence el límite, además el `taskkill /F /T` de ese mismo árbol (en Windows).
  `rojo visto, por mutación`
- **E-29** — `PreToolUse` no abre un socket. `rojo visto, por mutación`
- **E-30** — `PreToolUse` no importa ni llama un cliente de modelo. `rojo visto`
- **E-31** — `UserPromptSubmit` sin red ni modelo; el único proceso, `git -C <raíz> remote -v`, y si
  se vence el límite el `taskkill /F /T` de ese árbol. `rojo visto`; el camino colgado, `por mutación`
- **E-32** — `SessionStart` sin red ni modelo en lo que agrega el flujo. `rojo visto`
- **E-33** — La compuerta consume `estado.vigencia` y `estado.permisos`/`puede_avanzar`: con ellos
  cambiados en el proceso, cambia la decisión. `rojo visto`
- **E-34** — Un plan reescrito después del estado (`PLAN_STALE`) o un TaskContext cambiado
  (`TASK_CONTEXT_STALE`): deny a la mutación. `rojo visto`
- **E-35** — Dos sesiones concurrentes: `session-A` → `ABC-123`, `session-B` → `ABC-456`; con el
  puntero en `ABC-456`, A evalúa `ABC-123`; con el puntero en `ABC-123`, B evalúa `ABC-456`.
  `rojo visto`
- **E-36** — Una sola emisión JSON por corrida en todas las combinaciones. `rojo visto, por mutación`
- **E-37** — Por PowerShell: el hook invocado desde `powershell.exe` da el mismo deny. `rojo visto`
- **E-38** — Por Git Bash: `run-hook.sh` da el mismo deny. `rojo visto`
- **E-39** — Un proyecto en una ruta con espacios: la URI sale codificada y válida, y la compuerta
  funciona. `rojo visto`
- **E-40** — La Context Bar sigue siendo la `statusLine`: el registro de hooks no la toca (el
  matcher de PostToolUse no cambia) y los módulos nuevos no escriben su señal de vida. `rojo visto`
- **E-41** — E-25 queda acotado: un párrafo con `vscode://file/…` no afirma nada; uno que dice que la
  barra se ve en VS Code sigue agarrado. `rojo visto`
- **E-42** — Wave 2 sigue verde (`62_estado_del_flujo`). `rojo visto: no consta`
- **E-43** — Wave 1 sigue verde (`61_flujo_precondiciones`). `rojo visto: no consta`
- **E-44** — Refutación atómica sigue verde (`55_refutacion_atomica`). `rojo visto: no consta`
- **E-45** — Entorno primero sigue verde (`60_entorno_primero`). `rojo visto: no consta`
- **E-46** — Bloque 4 sigue verde (`30_b4_contabilidad`). `rojo visto: no consta`
- **E-47** — Reporte de seguridad sigue verde (`48_reporte_de_seguridad`). `rojo visto: no consta`
- **E-48** — La compuerta entera, `.\tests\Invoke-Tests.ps1`. `rojo visto: no consta`
- **E-49** — Sin `session_id`: no se escribe binding, y con dos tareas la mutación es deny.
  `rojo visto`
- **E-50** — Un `session_id` inseguro va a `_<sha256>`; dos que difieren en mayúsculas no comparten
  carpeta; el archivo guarda el original. `rojo visto`
- **E-51** — Revalidación: `BLOCKED` en PLANNING + `plan <KEY>` pasa; en CONTEXT + `plan <KEY>` es
  deny. `rojo visto`
- **E-52** — `WAITING_FOR_HUMAN_APPROVAL` + `plan <KEY>`: deny, sin excepción. `rojo visto`
- **E-53** — Un comando del Harness con clave evalúa su clave, no la del binding, y crea el binding
  si la sesión no tenía. `rojo visto`
- **E-54** — Un fallo interno de la compuerta con una mutación: deny `FLOW_GATE_UNRESOLVED`; con una
  lectura, pasa. `rojo visto`
- **E-55** — Sin estado del flujo en el proyecto, `PreToolUse` calla como antes y no carga `flujo/`.
  `rojo visto, por mutación`
- **E-56** — Una tarea vinculada sin `state.json`: deny `TASK_FLOW_STATE_MISSING`; `contexto <KEY>`
  pasa. `rojo visto`
- **E-57** — Instalado (`.claude/harness/hooks` y `bin/desarrollo`): el hook encuentra `flujo/` y
  decide igual. `rojo visto`
- **E-58** — Con `cwd` en una subcarpeta del proyecto, el hook encuentra la raíz del runtime.
  `rojo visto`
De E-59 en adelante salieron de la primera verificación (ver `verificacion.md`).

- **E-59** — Sin ningún `state.json` en el proyecto, un binding no traba nada: `UserPromptSubmit` y
  `SessionStart` callan y el `Write` pasa, con `desarrollo` y sin él. `rojo visto`
- **E-60** — `BLOCKED` en REFUTATION: `refute --record` y `--unit` son deny; `--compile` pasa.
  `rojo visto`
- **E-61** — Sin `lib/tool_policy.py`, el secreto de confianza alta sigue siendo deny; con tareas, la
  mutación es `FLOW_GATE_UNRESOLVED`, también con `cwd` en una subcarpeta; sin tareas, salida 0 y
  sin deny. `rojo visto`
- **E-62** — Scriptblocks, `sed`, `git --output`, `git -c`, `-C`, `--git-dir`, `--work-tree`,
  `git --exec-path`, `git diff --ext-diff`,
  `git grep -O`, `rg --pre`, globs y variables hacia el `.env`, `tree -o`, `hostname <nombre>` y un
  `dev-harness.py` que no es el de este proyecto (otra carpeta, aunque termine en
  `.claude/harness/bin/desarrollo/`, o el relativo corrido desde una subcarpeta): nunca `READ_ONLY`
  ni `FLOW_RECOVERY`. `rojo visto`

E-63 y E-64 salieron de la pre-aceptación: dos caminos reales que la compuerta no cubría. E-65, del
cierre de la aceptación.

- **E-63** — ACTIVE con el repositorio MATCHED; se cambia solo el remoto, sin correr `contexto`,
  `plan` ni `refute`: `Write`, `Edit` y `Task` son deny `REPOSITORY_STATE_STALE`, el estado guardado
  no se toca, la lectura pasa y `plan` revalida. Sin remoto, deny. `rojo visto`
- **E-64** — El matcher registrado de PreToolUse alcanza a `Agent` y a `Task`, y no a `TaskCreate`,
  `TaskOutput`, `Read`, `Glob` ni `Grep`. Delegar con la tarea `BLOCKED`, `AMBIGUOUS` o
  desactualizada es deny; con la tarea `ACTIVE`, pasa; un secreto alto en el pedido sigue siendo el
  deny del secreto. `rojo visto`
- **E-65** — `git remote -v` corre con el timeout de la compuerta, no con el de la CLI, que sigue en
  10 s. Colgado como el lanzador de Git para Windows —un proceso que deja un nieto dormido con los
  pipes heredados—: `Write` y `Agent` son deny `FLOW_GATE_UNRESOLVED` en el límite, también con la
  lista de remotos guardada vacía; la lectura no corre `git` y pasa; sin red ni `.env`. `rojo visto`

## Cómo se verifica

Los tests viven en `tests/casos/63_compuerta_del_flujo.py`, con el id del escenario en el título. Se
escriben antes que `task_binding.py`, `tool_policy.py`, `flow_gate.py` y `flow_context.py`, y se
corren en rojo: cada `rojo visto` sale de esa corrida. E-19, E-23, E-29, E-36 y E-55 afirman
algo que el hook de antes ya cumplía (el deny del secreto, que la lectura pasa, que no hay red ni
procesos, una emisión, el silencio sin flujo): pasaron en esa corrida, y su rojo es por mutación,
rompiendo la regla que cada uno cuida después de implementar. E-28 (el `.env` no se abre) y la
aserción de E-33 sobre `permisos()` se agregaron en la verificación y pasaron de entrada; su rojo
también es por mutación. E-59 a E-62 se escribieron y se corrieron en rojo antes de su arreglo.
E-42 a E-48 son archivos de la suite y la compuerta entera. Verifica `harness-spec-refuter`, que no es quien construyó.

La latencia se mide aparte, con eventos sintéticos: mediana y p95 de `pre-tool-use` con y sin estado
del flujo. El repositorio no fija un presupuesto numérico para esta Wave; la medición se registra en
`verificacion.md` para detectar una regresión grave.
