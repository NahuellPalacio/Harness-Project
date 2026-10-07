# Flow Governance — preparación para la calificación

**Estado:** preparación, no calificación · **Fecha:** 02-10-2026, actualizada el 05-10-2026 ·
**Base:** `VERSION 0.28.0`, integrada (`integracion-0.28.md`)

📌 Hasta el 05-10-2026 la base era `VERSION 0.26.0`: las Waves se construyeron sobre 0.26.0, y la
línea oficial llegó a 0.28.0 mientras tanto. Las dos se integraron con un merge, sin rebase. Lo que
cambió de las Waves al integrar está en `integracion-0.28.md`.

Este documento junta lo que una revisión de calificación o de release va a necesitar mirar sobre la
serie Flow Governance (Waves 1 a 6). **No declara nada calificado, listo para producción ni aprobado
para release**: esa decisión es de una fase posterior y de otra persona. Lo que hace es decir qué hay,
con qué evidencia, qué quedó afuera y qué todavía impide calificar.

## Las Waves

| Wave | Qué | HEAD | Verificación | Aceptación | Suite |
|---|---|---|---|---|---|
| 1 | Precondiciones del flujo y compuertas de repositorio | `4a18ddc23a379ff6a9ec09feb0d8af0aa23004f3` | 23 sostenidos (`flujo-precondiciones/`) | funcional 9/9 | 37405/37405 |
| 2 | Estado del flujo por tarea (`task-flow-state/1.0`) | `32febd758697a8407574d5d64736a6ec58058136` | 38 sostenidos (`estado-del-flujo/`) | funcional 23/23 | 37582/37582 |
| 3 | Compuerta de flujo por sesión | `2b43a77c0a9b6fbf39a2268fde82be9d6a54ca9b` | 65 sostenidos (`compuerta-del-flujo/`) | funcional 31/31, runtime real y manual PASS | 38071/38071 |
| 4 | Interacción humana y reanudación segura | `2c33fba41cb13bb59c888377466b619cb70f42d1` | 71 sostenidos, ocho pasadas (`interaccion-humana/`) | manual de aprobación y de configuración persistente PASS | 38455/38455 |
| 5 | Fallar cerrado y semántica de capacidades | `556c7bdde9e54091d40b7ca13124a5155f61388e` | 43 sostenidos, cuatro pasadas (`fail-closed-hardening/`) | manual de capacidades y del Bloque 4 PASS | 38746/38746 |
| 6 | Limpieza de integridad y esta preparación | `73a7b47dc6f4bc2cd6bf105332129279112c1381` | 46 sostenidos, dieciséis pasadas; E-24 sostenido también por la revisión humana independiente (`integrity-cleanup/`) | manual A, B y C PASS de la persona | 39519/39519 |
| Integración | Las Waves 1 a 6 con la línea oficial 0.28.0 | `05fefcdf160c2149c4f6732f22aa0807c4bf3dd0`, merge de `e5d7a14` sobre `73a7b47` | 14 sostenidos, dos pasadas; decisión A sobre la frescura (`integracion-0.28.md`) | Manual B integrada PASS de la persona | 40389/40389 |

Cada número de suite es la compuerta entera, `.\tests\Invoke-Tests.ps1`, corrida por quien verificó.
La verificación la hizo siempre `harness-spec-refuter`, que no es quien construyó.

## Los contratos canónicos

| Contrato | Qué es | Dónde |
|---|---|---|
| `flow-required-inputs/1.0` | Qué necesita cada etapa | `harnesses/desarrollo/reglas/` |
| `task-flow-state/1.0` | El estado del flujo de una tarea; la autoridad | `.claude/runtime/tasks/<KEY>/state.json` |
| `session-task-binding/1.0` | Qué tarea trabaja cada sesión | `.claude/runtime/sessions/<id>/` |
| `session-flow-notice/1.0` | Lo que la sesión ya avisó | `.claude/runtime/sessions/<id>/` |
| `human-intent/1.0` | Lo que la persona escribió en el chat, una vez | `.claude/runtime/sessions/<id>/human-intent.json` |
| `human-decision-record/1.0` | Una decisión aplicada | `.claude/runtime/tasks/<KEY>/decisions/` |
| `orchestration-plan/1.0` | El plan, con `capabilityStatus` y `knowledgeSources` desde la Wave 5 | `.claude/planes/<KEY>.json` |
| `integraciones/1.0` | El registro de capacidades | `.claude/harness.capacidades.json` |
| `sources-state/1.1` | La frescura de las fuentes | `.claude/harness.fuentes.json` |

📌 **`summary.json` del Bloque 4:** con `resolved.tokens == false`, los campos numéricos de tokens
son los valores parciales conocidos y no se leen como totales completos. El esquema no cambia y los
campos no pasan a `null`: es un número con su estado al lado, el contrato de programa de la Wave 5.

## Los invariantes

```text
STATUS READS AUTHORITY
RESUME MAY CHANGE AUTHORITY
model tool call != human approval
SUPPORTED_UNAVAILABLE != CAPABILITY_GAP != NEW_TOOL_REQUIRED
unresolved metric -> N/D        resolved zero -> 0
missing usage != RESOLVED usage
CLI gate != only gate
CONFIGURED != ACTIVE != RESOLVED
Block 4 observes, accounts and reports; Block 4 does not govern
```

Los cinco estados de integración son exactamente `NOT_CONFIGURED`, `AUTHENTICATION_FAILED`,
`CONNECTION_FAILED`, `PERMISSION_DENIED` y `AVAILABLE`. No hay `NOT_REQUIRED`.

## Las compuertas

| Compuerta | Qué decide | Dónde |
|---|---|---|
| Secret Guard | Un secreto de confianza alta es deny, antes que todo | `comun/hooks/pre-tool-use.py` |
| Compuerta del flujo | Lo que modifica o avanza, con la tarea de la sesión bloqueada o sin estado: deny | `comun/hooks/lib/flow_gate.py` |
| Autoridad protegida | Con estado del flujo en el proyecto, ninguna herramienta que llega al hook (Write, Edit, el shell, la delegación, `mcp__*`) escribe `.claude/`, `.git/` ni un punto de persistencia del host que nombre en un valor de una línea; los límites están en el modelo de amenaza | `comun/hooks/lib/tool_policy.py` |
| Decisión humana pendiente | Mientras alguien espera a la persona, el shell solo lee | `flow_gate.py` |
| Intent humano | Aplicar una decisión pide lo que la persona escribió en esa sesión | `flow_gate.py`, `lib/human_intent.py` |
| PLANNING y REFUTATION | Las precondiciones de la Wave 1, también para `refutacion.compilar` como biblioteca | `flujo/precondiciones.py`, `orquestacion/refutacion.py` |
| Frescura de la operación | Un estado de integridad de una fuente exigida frena `plan` y `refute --compile` | `orquestacion/frescura.py` |

## Las aceptaciones manuales

- Wave 3: el runtime real de Claude Code y la aceptación manual.
- Wave 4: la aprobación de punta a punta, un solo uso, y la configuración persistente con `--resume`.
- Wave 5: una capacidad soportada y caída sin `dev-tool-builder`, y el Bloque 4 en `N/D`.
- Wave 6: A (en lo que la persona observó; el libro evento por evento todavía no), B y C PASS de la
  persona; B repetida con Claude Code real sobre el árbol final (`integrity-cleanup/verificacion.md`).
- Integración con 0.28.0: la B otra vez, sobre el árbol integrado, PASS de la persona el 05-10-2026.
  En la misma sesión real: `Ctx 5%` de 0.28 y la presentación de 0.27 (sin amarillo ni rojo, que a
  5% no correspondían). Ver `integracion-0.28.md`.

## Lo que se cerró en la Wave 6

- El Bloque 4 registraba como `RESOLVED` un mensaje sin `usage`, y la barra descartaba lo que no se
  resolvió antes del libro.
- El presupuesto decidía `WITHIN_BUDGET` sobre un costo parcial.
- `refutacion.compilar` como biblioteca se salteaba la compuerta de REFUTATION.
- `AlmacenSecretos.set/remove` podían escribir el `.env`.
- El deny cruzado de `contabilidad` nombraba la tarea equivocada.
- El repositorio de la unidad tenía otra fuente que la identidad del flujo, y el aviso de ES0901 decía
  lo contrario de lo que mostraba.
- El Bloque 4 y la barra `ACTIVE` sin datos, la prueba de la señal con campos faltantes, `-Doctor` en
  OK con `CONFIGURED`.
- `PlanInvalido` en un traceback.
- `dev-iniciador-code` huérfano.
- `-Doctor` callado ante el alias de Python de la Store.
- Los puntos de persistencia del host escritos por una herramienta.

## El modelo de amenaza

El harness corre como el mismo usuario que el modelo. Defiende lo que pasa **por las herramientas
del modelo que ven los hooks**; no defiende una máquina ya comprometida.

### Neutralizado localmente

- `.claude/` y `.git/`, con estado del flujo:
  - **El literal (Wave 4).** Ninguna herramienta los escribe nombrándolos literalmente en el texto:
    Write, Edit, Bash, PowerShell o un valor de una línea de una MCP.
  - **El glob, solo en Bash y PowerShell (R11, Final Qualification, segunda pasada).** Es protegido
    el **destino de una operación que escribe** cuando, con la sintaxis textual que la política
    normaliza, puede ser `.claude` o `.git` en la raíz del proyecto, o algo adentro. Esa sintaxis
    es, y no otra: comillas y escapes de Bash (`\`), clases POSIX dentro de `[...]`, `*`, `?` y
    `[...]`, expansión de llaves estática (`{a,b}`, `{a..e}`) de hasta 256 resultados —más de 256 es
    límite, abajo—, el backtick de PowerShell, `.` y `..` resueltos por el texto contra
    el cwd y la raíz, un `cd` literal en el mismo comando, y otro shell visible en el texto (`bash
    -c`, `powershell -Command`) hasta tres niveles de anidamiento. Lo que lee no tiene
    destino: un glob en una lectura o en el valor de `Set-Content` no es autoridad. En un git que
    escribe se excluyen de los destinos solo los valores de las opciones no-destino que la política
    reconoce por subcomando (el mensaje de `commit -m`); una opción desconocida no saca por sí
    misma el posicional que la sigue (H1, cerrado). No es la gramática completa de git: si el valor
    de una opción desconocida se escribe igual que una de la tabla, se lee según la tabla (O1,
    residuo aceptado). Se decide por el texto, sin
    expandir el glob contra el disco y sin correr un shell.
  - Lo que queda afuera está en la lista de abajo: lo que arma el destino al correr, los prefijos
    de ruta que la política no normaliza, el anidamiento más hondo, `cmd /c`, la expansión de llaves
    de más de 256 resultados y el glob en una MCP genérica. Ninguna otra sintaxis está prometida.
- `usercustomize.py`, `sitecustomize.py`, cualquier `.pth`, un perfil de PowerShell (`$PROFILE`,
  `${PROFILE}`, `*profile.ps1`), `~/.gitconfig`, `~/.config/git/config` y cualquier archivo bajo un
  `site-packages`, en el proyecto o en el host: con estado del flujo, **ni Write ni Edit los escriben,
  ni un comando de shell que los nombre** —tampoco por un stream de NTFS (`::$DATA`) o un punto final en
  cualquier segmento, ni por un nombre corto 8.3, que se resuelve contra el disco, ni en la forma
  `/c/...` de Git Bash o como `-Parametro:valor` de PowerShell—, ni una copia a la carpeta
  `site-packages` misma, ni un punto de persistencia pegado a una opción (`--x=ruta`, `-Path:ruta`,
  `-oruta`), ni un `git config` que escribe, con cualquier alcance —sin alcance o `--local` es
  `.git/config`; también `--global|--system|--file`, abreviados como los acepta git (`--glob`,
  `--sys`, `--fil`) o `-f<ruta>`, detrás de otro programa, entre comillas o en un alias de `-c`—, ni
  `uniq - <salida>` (Wave 6). Las lecturas de `git config` (`--get`, `--list`, un nombre solo) pasan.
  Es por nombre, a propósito: un `profile.ps1` legítimo del proyecto también queda protegido.
- Una herramienta desconocida que no es shell —un servidor MCP que escribe archivos— con `.claude/`,
  `.git/` o un punto de persistencia del host en un valor o una clave de una línea de su
  `tool_input`, a cualquier profundidad: con estado del flujo, protegida igual (Wave 6, E24-E14).
  Las herramientas `mcp__*` llegan al hook porque el matcher de PreToolUse suma `^mcp__` (E24-E15);
  un proyecto instalado lo recibe con `-Update`.
- Un servidor MCP que corre comandos, con el comando en un valor de una línea, como arreglo o
  repartido en campos: se mira también como comando, con la regla del texto de Bash (Wave 6,
  E24-E16, E24-E18). Además sus palabras se miran como una bolsa, sin orden ni comillas: si una es
  la autoridad o un punto de persistencia, o si están git y `config` (salvo una lectura de `git
  config` parseada estricta), es protegida (E24-E20). Sobreprotege a propósito a una MCP cuyo texto
  solo menciona esas cosas.
- `git config`, sin parsear cada shell forma por forma (Wave 6, E24-E21, decisión de la persona del
  04-10-2026): en Bash, PowerShell o una MCP, un texto que deja ver git y `config` y que el parser
  no prueba como lectura es protegido. Alcanza a un scriptblock (`& {git config ...}`),
  `Start-Process` con `@(...)` o `-FilePath:git`, un escape (`g\it`, ``g`it``, `g^it`), una
  continuación de línea que parte la palabra, algo que vale vacío (`g$'i't`, `g$()it`) o una
  concatenación de literales: el texto se lee también como el shell une cada palabra. La exención es positiva: una sola `config` y una lectura parseada
  estricta (`--get`, `--get-regexp`, `--list`, `-l`, con o sin alcance), sin variables ni
  sustituciones. Sin excepción por clave. **INTENTIONAL_CONSERVATIVE_OVERPROTECTION**: `git commit -m
  "update config"` también se niega; lo aceptó la persona, porque un falso positivo cuesta menos que
  un bypass. No es un deny global: `UNRESOLVED_TOOL_CLASS` sin git config a la vista sigue pasando con
  la tarea sana (SPEC_OVERSTATEMENT de la afirmación 7, ratificado).
- Un evento de PreToolUse que el hook no puede leer (un JSON demasiado hondo o roto, un
  `RecursionError`): con estado del flujo, deny `FLOW_GATE_UNRESOLVED`, nunca una salida 0 en
  silencio (Wave 6, E24-E17).
- **THREAT_MODEL_BOUNDARY** — una herramienta que no es `mcp__*` ni está en el matcher de
  PreToolUse no llega al hook: ni la compuerta ni la autoridad protegida la ven.
- **THREAT_MODEL_BOUNDARY** — una MCP que corre comandos y recibe un script de varias líneas: un
  texto de varias líneas es contenido y no se mira como comando. Un valor de una línea se mira como
  ruta y como comando.
- **THREAT_MODEL_BOUNDARY** — un `git config` cuyas palabras no están en el texto: armado con
  variables, leído de un archivo o codificado (`-EncodedCommand`). Con la tarea sana pasa como
  cualquier `UNRESOLVED`; con la tarea bloqueada o una decisión pendiente, no.
- `core.fsmonitor`: el `git status` de SessionStart corre con `-c core.fsmonitor=false`.

### THREAT_MODEL_BOUNDARY

Lo que queda fuera, escrito para que nadie lo lea como protegido:

- **THREAT_MODEL_BOUNDARY** — `.claude/` o `.git/` alcanzados por algo que el texto no muestra: una
  variable, una concatenación que arma el nombre al correr, un `cd` calculado, un programa que
  elige qué escribe o borra (`git clean -fdx`), o el borrado de una carpeta que contiene la raíz
  (`rm -rf ../proj`, la raíz por su ruta). Tampoco una sustitución de comandos cuyo destino solo se
  conoce al correr. El literal y el glob dentro de la sintaxis normalizada (arriba) están adentro
  (R11); esto no. Un glob hacia un punto de persistencia del host sigue siendo límite: R11 no lo
  cambió.

- **THREAT_MODEL_BOUNDARY** — un glob hacia `.claude/` o `.git/` escrito con un prefijo de ruta que
  la política no normaliza: el provider de PowerShell (`FileSystem::`) o una ruta de dispositivo de
  Windows (`\\?\`). Es B6, límite explícito por decisión de la persona del 06-10-2026 (Final
  Qualification, R11 segunda pasada). El literal sigue protegido.

- **THREAT_MODEL_BOUNDARY** — un glob hacia `.claude/` o `.git/` dentro de un shell anidado más de
  tres niveles (`bash -c` dentro de `bash -c`…), o en un shell anidado que recibe su comando
  codificado o de un archivo (`-EncodedCommand`, `-File`). Pasado el límite, el análisis del glob no
  sigue; el literal visible en el texto sigue protegido.

- **THREAT_MODEL_BOUNDARY, OUT_OF_SCOPE_COMPLEXITY_BOUNDARY** — una expansión de llaves que da más
  de 256 resultados. La política no la enumera. Lo que hace pasado el límite es un intento sin
  garantía: puede bloquear algunos casos, pero esa detección es incidental, no es conservadora y no
  prueba que se detecte todo destino de autoridad (decisión de la persona del 06-10-2026, F1).

- **THREAT_MODEL_BOUNDARY** — cualquier otra sintaxis de Bash, PowerShell o `cmd` que la política no
  normaliza expresamente (arriba). `cmd /c` está fuera del alcance: el código lo lee con el léxico de
  PowerShell, pero la sintaxis propia de `cmd` no está normalizada y lo que se detecte ahí no es una
  garantía. R11 no interpreta un shell entero: lo que no está en la lista de lo
  normalizado no está prometido.

- **THREAT_MODEL_BOUNDARY** — un glob hacia `.claude/` o `.git/` en un valor de una MCP genérica
  (`path: .cla*/harness`, `command: rm -rf .cla*/harness`). Sus valores no son destinos tipados: R11
  no adivina por el nombre del campo cuál es ruta o comando. El literal sigue protegido y la
  herramienta sigue `UNRESOLVED_TOOL_CLASS`. Incluye un `file:///` con glob en una MCP (B7). Cerrarlo
  pide un adaptador MCP tipado, trabajo posterior a la calificación (decisión de la persona del
  06-10-2026, Final Qualification, R11 segunda pasada; `PENDIENTES-I.md`).

- **THREAT_MODEL_BOUNDARY** — `.claude\harness\` borrado por algo fuera de este modelo de amenaza
  (cualquiera de los límites de arriba, otro proceso, la persona): el lanzador `run-hook.cmd` no se
  encuentra, el hook sale 0 y deja de gobernar la sesión (R9). Dentro de la sintaxis normalizada, R11
  protege el destino que se ve; afuera, no. `run-hook.cmd` no cambia en esta calificación.

- **THREAT_MODEL_BOUNDARY** — lo plantado **antes** de instalar el harness, o escrito por fuera de las
  herramientas del modelo (otro proceso, la persona, un instalador): un `usercustomize.py` o un `.pth`
  en el `site-packages` del usuario, un perfil de PowerShell, un `~/.gitconfig` con `core.fsmonitor`,
  `core.hooksPath` o un `core.pager`.
- **THREAT_MODEL_BOUNDARY** — un `sitecustomize.py` o un `.pth` en el `site-packages` del sistema o del
  Python que corre los hooks.
- **THREAT_MODEL_BOUNDARY** — un ejecutable reemplazado fuera del proyecto (`git`, `python`, `pwsh`).
- **THREAT_MODEL_BOUNDARY** — las demás llamadas a `git` de la CLI y de los hooks (`git remote -v`, que
  no corre `core.fsmonitor`) siguen leyendo la configuración global.
- **THREAT_MODEL_BOUNDARY** — lo que escribe en esos lugares **sin nombrarlos en el texto del comando**:
  un glob que el shell resuelve (`>> ~/.gitconf?g`), una variable o una concatenación
  (`user''customize.py`, `(Get-Variable PROFILE -ValueOnly)`), una ruta relativa que solo se resuelve
  después de un `cd`, `pip install --user` (que puede dejar
  un `.pth`), un instalador o cualquier programa que decida su destino solo. **Es un recorte aceptado
  durante la verificación de la Wave 6** (ver E-24 en `integrity-cleanup/spec.md`) y lo tiene que
  aceptar quien califique. La política mira el texto
  del comando, no lo que el shell o el programa resuelven; un comando que no reconoce es
  `UNRESOLVED` y, con la tarea bloqueada o una decisión pendiente, no pasa, pero con la tarea sana sí.
- **Diferido** — correr los hooks con `python -I` (aislado: sin `PYTHONPATH`, sin el `site-packages` del
  usuario). Neutralizaría la persistencia del usuario en Python, pero cambia la codificación de la
  salida de los hooks y ningún test de la suite lo vería. Pide su propio cambio, con una prueba en una
  sesión real.

### La política de lectura

Un comando de shell es de lectura solo si cada programa está en una lista y no usa una forma de
escribir anotada. Lo desconocido es `UNRESOLVED`: nunca `READ_ONLY`, y con las restricciones de
`MUTATING`. No pasa con la tarea bloqueada, con una decisión humana pendiente de la tarea
gobernada ni con la autoridad de la tarea ambigua; con la tarea gobernada sana puede pasar. Una
decisión pendiente de otra tarea del proyecto frena el shell (Wave 4), no las demás herramientas
desconocidas, que igual no escriben la autoridad. Es el contrato de las Waves 3 y 4,
ratificado por la persona el 02-10-2026 (SPEC_OVERSTATEMENT de la afirmación 7, en
`integrity-cleanup/spec.md`). Desde la Wave 6 una opción larga de
salida (`--output`, `--out*`) en un programa de la lista es escritura. Un programa de la lista con otra
forma de escribir, no anotada, sería un hueco de esa lista: es un riesgo aceptado y escrito, no una
garantía.

## Riesgos aceptados

- La lista de programas de lectura, descrita arriba.
- «Instalado» para el Bloque 4 porque existen tres archivos: la señal del renderer, que importa el
  Bloque 4 entero, lo desmiente en el primer dibujo.
- `CONFIGURED` no suma condición pendiente: una sesión nueva no arranca en PARCIAL. Lo que no pasa es
  que se lea como `ACTIVE`.
- Un hallazgo `HIGH` `UNRESOLVED` sin `blocking` no bloquea el reporte de seguridad.
- La tabla de conciliación de `execution-cost.md` muestra lo derivado crudo, rotulado como piso.
- `contabilidad --ingerir` de una fuente sin consumo, o de Codex, escribe un evento sin clave cada vez
  que se corre en otro segundo.

## Qualification Gate 1

**CLOSED** el 06-10-2026 (`qualification-gate-1.md`). Cerró los dos impedimentos que esta sección
nombraba y que `PENDIENTES-FH.md` ponía primero y segundo:

- **Q1, CLOSED:** los tests del instalador ya no rompen archivos versionados; corren sobre una copia
  aislada, y matar la suite no toca el árbol.
- **Q2, CLOSED:** `-NonInteractive` con una consola real no espera input ni aprueba solo; sale 1 con
  el diagnóstico.

Evidencia: dos pasadas del refutador sin contradichos, la aceptación humana de Q2 (A a E PASS) y la
compuerta desde la terminal de la persona, 40447/40447, exit 0. Cerrar el gate no es calificar.

## Final Qualification Gate

Evaluado el 06-10-2026 sobre `ea2dff7` (`final-qualification.md`). **Veredicto: `QUALIFIED`**, por
decisión de la persona del 07-10-2026; antes fue `NOT_QUALIFIED`. QF-04 está `SUSTAINED_BY_ARCHITECTURE_REVIEW_WITH_PROCESS_EXCEPTION` desde el 07-10-2026.

- El hallazgo original: un glob visible en el texto (`.cla*`) escribía la autoridad del flujo.
- La persona decidió endurecerlo (R11 = HARDEN). La segunda pasada, por destino, está construida.
- La refutación adversarial independiente no llegó a un veredicto. La persona aceptó, para R11 y solo
  en esta calificación, una excepción de proceso: «R11 EVIDENCE PROCESS EXCEPTION» en
  `final-qualification.md`.
- La revisión independiente del arreglo de H1 dio `EVIDENCE_SUFFICIENT_FOR_HUMAN_ACCEPTANCE`; la
  persona la aceptó y la excepción de proceso quedó `ACTIVATED`. No hay una refutación adversarial
  sostenida.
- R1 a R8 y R10 están aceptados. R9 = `ACCEPTED_RESIDUAL_RISK` desde el 07-10-2026: fuera del
  modelo de amenaza soportado, algo que el analizador no ve puede borrar o inutilizar el lanzador, y
  sin el lanzador el hook no es por sí mismo una raíz externa de enforcement. La garantía vale dentro
  de la frontera publicada; no es «fail closed ante cualquier manipulación».
- Los límites residuales de R11, los de «THREAT_MODEL_BOUNDARY» y O1 incluidos, son
  `ACCEPTED_EXPLICIT_THREAT_MODEL_BOUNDARIES`: quedan fuera de la garantía, no cubiertos de forma
  implícita.

## Lo que impedía calificar

Resuelto el 07-10-2026: la persona leyó y aceptó lo que sigue al aceptar R9 y los límites de R11.

- Las sobreprotecciones a propósito (INTENTIONAL_CONSERVATIVE_OVERPROTECTION de `git config`, las
  herramientas desconocidas que mencionan la autoridad) y las dos observaciones NON-BLOCKING de la
  decimosexta pasada, leídas y aceptadas por quien califique.
- El modelo de amenaza de arriba, leído y aceptado por quien califique.

## Lo que se decide después de calificar

No es un bloqueante de la calificación: es una decisión de release.

- **La versión siguiente se escribe al integrar, no en la calificación.** No es 0.28.x: Flow Governance
  trae un endurecimiento material y un cambio explícito del contrato y del modelo de amenaza, aunque
  compatible. La calificación se hizo sobre `VERSION` 0.28.0, la base de esta rama. No se crea un
  tag 0.29.0: `origin/main` ya tiene 0.29.0 y 0.30.0, y el número se decide al integrar.
