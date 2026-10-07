# Flow Governance, Wave 6 — limpieza de integridad y preparación para la calificación

**Estado:** cerrado · **Fecha:** 02-10-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Las Waves 1 a 5 dejaron escritos, y diferidos, lugares donde el harness todavía dice más de lo que
sabe o deja una puerta lateral:

- El Bloque 4 registra como `RESOLVED` un mensaje que no trae `usage`, y la barra descarta lo que no
  se resolvió antes de que llegue al libro.
- El presupuesto decide `WITHIN_BUDGET` sobre un costo parcial.
- `refutacion.compilar` llamado como biblioteca se saltea la compuerta de REFUTATION.
- `AlmacenSecretos.set/remove` escriben el `.env`, que es de la persona, y nadie los usa.
- El deny cruzado de `contabilidad` nombra la tarea equivocada.
- El plan tiene dos fuentes para el repositorio de la tarea, y un aviso de ES0901 que dice lo
  contrario de lo que muestra.
- Estados de instalación que pintan verde sin evidencia: el Bloque 4 `ACTIVE` sin libro, `-Doctor`
  en OK con la barra `CONFIGURED`, la prueba de la señal que pasa con campos faltantes.
- `PlanInvalido` termina en un traceback.
- `dev-iniciador-code` está instalado, lo sugiere SessionStart y el registro lo trata como huérfano.
- `-Doctor` dice «Python OK» aunque `python` sea el alias de la Store, y todo comando que muestra el
  harness empieza con `python`.
- Lo que el modelo puede plantar fuera de `.claude/` y `.git/` para que lo ejecute un hook.

## Qué queda afuera

- **Calificar o liberar.** Esta Wave deja un documento de preparación; no declara nada calificado.
- **Una escala nueva.** Ni estados de integración nuevos, ni de presupuesto, ni de componente: se usan
  los que ya existen.
- **Reescribir la compuerta, el Bloque 4 o la refutación atómica.**
- **Defender un host ya comprometido.** Lo plantado antes, fuera del proyecto, es un límite escrito.

## Las decisiones, y por qué

### El Bloque 4 no convierte la falta de uso en un uso resuelto

```text
missing usage != RESOLVED usage
presentation may hide
ledger must retain
```

- Un mensaje del asistente sin ningún **número** de uso —sin `usage`, o con `input_tokens`,
  `output_tokens`, `cache_read_input_tokens` y `cache_creation_input_tokens` ausentes, en `null` o en
  texto— es un registro `USAGE_UNRESOLVED` con su clave estable, `msg|<id>`, su modelo, su sesión y
  su línea. Uno que trae algún número sigue `RESOLVED` con lo que trae; un cero medido es un cero. Llega al libro como cualquier mensaje y
  no se duplica.
- Que no haya nada nuevo desde el cursor de la barra no es un uso: no es un registro.
- La barra deja de descartar por estado. Lo único que no escribe es un registro **sin clave**: no es
  un mensaje sino «la fuente todavía no trae nada», y su id se inventaría en cada dibujo.
- La barra sigue ocultando lo que no tiene (E-21 de `bloque-1-context-bar`); el libro lo conserva.

📌 **Con `resolved.tokens == false`, los campos numéricos de tokens de `summary.json` son los valores
parciales conocidos y no se leen como totales completos.** En la aceptación manual A el resumen dice
12 de entrada y 34 de salida, lo que trajo el único mensaje con `usage`, al lado de `resolved.tokens:
false`; la presentación dice `N/D`. El contrato no cambia en esta Wave: ni el esquema ni los campos,
que no pasan a `null`. Es el contrato de programa de la Wave 5 (`fail-closed-hardening`): un número
con su estado al lado.

### El presupuesto no decide sobre un piso

`presupuesto.consumido` devuelve `None` cuando el estado del total del costo no es `RESOLVED`.
`evaluar` ya sabía qué hacer con eso: `COST_UNRESOLVED`, el estado que existía. Nunca
`WITHIN_BUDGET`, `BUDGET_WARNING` ni `BUDGET_EXCEEDED` sobre un monto parcial; la barra queda en el
nivel `UNRESOLVED`, sin un WARNING o un ERROR calculado sobre un piso.

### La compuerta de REFUTATION es de la operación, no del comando

```text
CLI gate != only gate
```

`refutacion.compilar` evalúa la misma compuerta que la CLI (`precondiciones.compuerta_de_refutacion`)
antes de tocar nada, y levanta `CompuertaCerrada` con los códigos que faltan. Las reglas siguen en un
solo lugar: la CLI ya no la llama por su cuenta, llama a `compilar` y convierte la excepción en el mismo
mensaje de siempre. La configuración pública de GitLab la lee `compilar`, con el lector de solo lectura de la
Wave 2 (`flujo.estado._entorno`).

`compilar` no recibe la configuración de GitLab de quien lo llama: la lee siempre del `.env`, con un
solo lector, así un argumento armado no saltea la compuerta. `refute --unit` y `refute --record` no
tienen compuerta propia desde la Wave 1, y eso no cambia.

Los tests que compilaban como biblioteca sobre un proyecto que no pasa la compuerta usan el fixture
que ya existía, `_listo_para_la_compuerta`: cambia el fixture, no la refutación.

### El harness no escribe la configuración de la persona

`AlmacenSecretos.set` y `remove` no tienen ningún consumidor desde 0.26.0 y escribían el `.env`. Ahora
levantan `ErrorDeAlmacen` sin abrir el archivo. `get` y `exists` no cambian.

### El deny cruzado nombra lo que evaluó

`contabilidad` se evalúa contra la tarea de la sesión, no contra la clave que nombra: no avanza
ninguna etapa del flujo, y evaluarla por su clave dejaría a una sesión bloqueada operar sobre otra
tarea. La decisión no cambia. Lo que cambia es el motivo: cuando el comando apunta a otra tarea, dice
las dos.

### Una fuente para el repositorio de la tarea, y un aviso que dice lo que cuenta

- `workUnits[].context.repository` sale de la identidad del flujo (`flowPreconditions.repository`),
  que es la que usa la compuerta y la que resuelve conflictos y elecciones de la persona. Sin
  precondiciones evaluadas sigue el TaskContext.
- El aviso de ES0901 nombra el archivo que cuenta: las reglas de `es0901-7.1.json` sin `conditions`
  no se citan en `applicableStandards`; la aplicabilidad de cada unidad la decide la matriz normativa
  (`normative`). No dice que la matriz no se construyó.

### Ningún estado más fuerte que su evidencia

```text
CONFIGURED != ACTIVE != RESOLVED
```

- **El Bloque 4** es `ACTIVE` solo con un libro de la última sesión que vio la barra, que existe, se
  abre y tiene al menos un registro: una línea que es un objeto JSON con algo adentro. Un salto de
  línea, un espacio o una línea rota no son un registro. Sin eso, `CONFIGURED`: instalado y
  escribible, sin datos todavía.
- **La Context Bar** es `ACTIVE` solo si el Bloque 4 también lo es. Con la señal en `OK` y el Bloque 4
  sin datos, `CONFIGURED`, no `ERROR`.
- **La prueba de la señal** exige la versión de la integración (un texto no vacío) y el momento de
  validación (con la forma de `ahora()`) que registró el instalador. Si falta alguno, o no tiene esa
  forma, no prueba nada: `RELOAD_REQUIRED`.
- **`-Doctor`** muestra la barra en OK solo si está `ACTIVE`; `CONFIGURED` es AVISO.

`CONFIGURED` no suma ninguna condición pendiente, como siempre: una sesión nueva no arranca en
PARCIAL. Lo que deja de pasar es que se lea como `ACTIVE`.

«Instalado» porque existen tres archivos queda como estaba, con su límite: la señal del renderer,
que importa el Bloque 4 entero, lo desmiente en el primer dibujo si falta algo.

### La evidencia de la Context Bar sobrevive al reinicio

La aceptación manual B falló en su último paso. En una sesión real la barra dibujó datos. Después
se reinició Claude Code, la sesión nueva dibujó «sin datos del Bloque 4» y `-Doctor` dijo
«CONFIGURADA, todavía sin una sesión que la haya dibujado con datos».

La sesión nueva no tenía por qué ser `ACTIVE` en su SessionStart: eso es E-05 de la Context Bar, y
no cambia. El defecto era otro. La señal de vida guardaba solo el último dibujo, y el primer dibujo
vacío de la sesión nueva pisaba la prueba de que otra sesión ya había dibujado datos. Encima,
`-Doctor` leía el estado que había dejado SessionStart, que describe una sesión y no la integración.

La persona decidió el 05-10-2026 **conservar la evidencia**:

```text
la integración está ACTIVE        != activeInCurrentSession
evidencia histórica               != actividad de la sesión actual
un dibujo vacío                   != borrar la evidencia válida anterior
la configuración cambió           != reusar la evidencia ACTIVE vieja
```

- **La señal** suma un campo opcional, `lastSessionWithData`, con `sessionId`, `renderedAt`,
  `configurationFingerprint` e `integrationVersion`. Un dibujo con datos la pasa a su sesión. Uno
  sin datos la conserva tal cual: no la borra, no la reemplaza por una sesión vacía y no la degrada.
  Los cinco campos de siempre siguen siendo el último dibujo.
- **La evidencia está atada a la configuración.** Prueba algo solo con la misma regla que la señal:
  la huella del `statusLine` de ahora, la versión del renderizador que registró el instalador, y
  dibujada después de ese registro. También hace falta que el libro de esa sesión siga teniendo
  datos. Si no se cumple todo eso, la evidencia sigue escrita pero no prueba nada: falla cerrado.
- **En una sesión** (SessionStart) la evidencia solo se informa, en `lastSessionWithData` del
  estado. Nunca hace `ACTIVE` a la sesión, y `activeInCurrentSession` sigue siendo de esa sesión.
- **Sin sesión** (`harness` y `-Doctor`), la evidencia válida alcanza para `ACTIVE`: es la
  integración probada, no actividad de la sesión actual. El Bloque 4 mira la misma sesión.
- **`-Doctor`** calcula la barra en vivo con `bienvenida.py barra`, el mismo resolvedor que
  `harness`, y dice «última sesión con datos: <id>». Sin Python, o si eso falla, vuelve al estado
  guardado tal cual: no inventa un `ACTIVE`.

`lastValidatedAt` no cambia. En la Context Bar es el momento del registro de la configuración, y se
mueve solo cuando cambia una de las cuatro huellas (`statusLine`, `renderer`, `block4Adapter`,
`sessionStart`). Un `-Update` idéntico no lo toca. El nombre confunde: queda anotado como deuda en
`PENDIENTES-FH.md`, sin cambiar el schema en esta Wave.

### Un error de dominio sale con 2

`PlanInvalido` entra a la tupla de errores de dominio de `main`: sale con 2, `harness: <mensaje>`, sin
traceback. No hay un `except Exception`: un error inesperado sigue siendo un traceback.

### `dev-iniciador-code` queda registrado

Se instala, SessionStart lo sugiere cuando no hay índice del código, y `contexto/repositorio.py`, el
check de forma del codebase y `mapa-codigo.py` leen lo que escribe. Queda en `agent-registry.json`
como `INFRASTRUCTURE_AGENT` de dominio `codebase`, sin skills, con la función que ya tiene; sale de los
huérfanos reconocidos. No se rutea por dominio: se llega por SessionStart y por delegación.

### Python: no anunciar lo que no anda

- `-Doctor` sigue diciendo qué Python corre los hooks, y además avisa si `python` en el PATH es el alias
  de la Microsoft Store, porque los comandos que el harness le muestra al modelo empiezan con `python`.
- `Invoke-Tests.ps1` valida el candidato como `Resolve-Python`: que corra y diga dónde está.

### El modelo de amenaza, escrito

| Vector | Dónde | Qué hace el harness |
|---|---|---|
| `.claude/`, `.git/` | proyecto | protegido desde la Wave 4 |
| `usercustomize.py`, `sitecustomize.py`, `*.pth`, perfiles de PowerShell (`*profile.ps1`, `$PROFILE`, `${PROFILE}`), `.gitconfig`, `~/.config/git/config`, cualquier archivo bajo un `site-packages` o la carpeta misma como destino: escritos con Write o Edit, o con un comando de shell que los nombra, también por un stream de NTFS (`::$DATA`) o un punto final en cualquier segmento, por un nombre corto 8.3 (que se resuelve contra el disco), en la forma `/c/...` de Git Bash o como `-Parametro:valor` de PowerShell | proyecto o host | **protegido** con estado del flujo: `FLOW_AUTHORITY_PROTECTED` |
| `git config` que escribe, con cualquier alcance: sin alcance o `--local`/`--worktree` (`.git/config`), `--global`, `--system` o `--file`, también abreviados como los acepta git (`--glob`, `--sys`, `--fil`, `--file=x`) o `-f<ruta>`, detrás de otro programa o entre comillas (`bash -c "git ..."`, `Start-Process git '...'`), o en un alias de `-c`. Desde E24-E21, **cualquier texto que deje ver git y `config`** y que el parser no pruebe como lectura: un scriptblock (`& {git config ...}`), `Start-Process` con `@(...)` o `-FilePath:git`, un escape (`g\it`, ``g`it``, `g^it`) o una concatenación de literales (`'gi'+'t'`). Las lecturas de `git config` que el parser prueba siguen pasando | proyecto o host | **protegido** igual |
| Un `git config` cuyas palabras no están en el texto: armado con variables, leído de un archivo, codificado (`-EncodedCommand`) | proyecto o host | **límite**: la política mira el texto del comando (E24-E21) |
| Un punto de persistencia como valor pegado a una opción: con `=` (`--target-directory=site-packages`), con `:` (`-Path:x`) o detrás de una opción corta (`-ox`) | proyecto o host | **protegido** igual |
| `uniq - <salida>` y `uniq -- - <salida>`: `-` es la entrada, así que la segunda palabra es la salida | proyecto o host | escritura; sobre un punto de persistencia, **protegido** |
| Una herramienta desconocida que no es shell (un servidor MCP) con `.claude/`, `.git/` o un punto de persistencia en un valor o una clave de una línea de su `tool_input`; las `mcp__*` llegan al hook por el matcher (E24-E15) | proyecto o host | **protegido** igual |
| Una MCP que corre comandos, con el comando en un valor de una línea, como arreglo o repartido en campos | proyecto o host | **protegido** igual, con la regla del texto de Bash (E24-E16, E24-E18) |
| Una MCP que corre comandos y recibe un script de varias líneas | proyecto o host | **límite**: un texto de varias líneas es contenido |
| Un evento de PreToolUse que el hook no puede leer (un JSON demasiado hondo o roto) | proyecto | **falla cerrado** con estado del flujo: `FLOW_GATE_UNRESOLVED` (E24-E17) |
| Una herramienta que no es `mcp__*` ni está en el matcher de PreToolUse | proyecto o host | **límite**: no llega al hook |
| Un glob en una redirección (`>> ~/.gitconf?g`), una variable o una concatenación (`user''customize.py`, `(Get-Variable PROFILE -ValueOnly)`), una ruta relativa que solo se resuelve después de un `cd`, `pip install --user`, un instalador o cualquier otro programa que escriba en esos lugares sin nombrarlos | host | **límite**: la política mira el texto del comando, no lo que el shell o el programa resuelven |
| `core.fsmonitor` de `~/.gitconfig` en el `git status` de SessionStart | host | neutralizado: corre con `-c core.fsmonitor=false` |
| Lo plantado antes de instalar o fuera de las herramientas del modelo | host | **límite**: fuera del modelo |
| `sitecustomize.py` o `.pth` del `site-packages` del sistema | host | **límite** |
| Un ejecutable reemplazado fuera del proyecto | host | **límite** |
| Correr los hooks con `python -I` | proyecto | **diferido**: cambia la codificación de la salida de los hooks y ningún test lo vería |

**Nota posterior de endurecimiento, Final Qualification (R11, 06-10-2026).** La fila de `.claude/` y
`.git/` dice «protegido desde la Wave 4» sin salvedad. La Wave 4 protegió los destinos que su parser
podía ver: el nombre literal. La refutación del Final Qualification Gate escribió la autoridad con
`.cla*`, que no lo es. El endurecimiento R11 posterior amplió esa cobertura, solo en Bash y
PowerShell, al destino de una operación que escribe cuando su sintaxis textual normalizada puede
alcanzar `.claude` o `.git` en la raíz. La sintaxis normalizada es una lista cerrada, escrita en
`flow-governance/qualification-readiness.md` («Neutralizado localmente»). Quedan explícitamente
fuera del modelo:
- una variable, una concatenación o una sustitución que solo se resuelve al correr;
- un programa que elige su destino (`git clean -fdx`) y el borrado de una carpeta que contiene la
  raíz;
- `FileSystem::` y `\\?\`;
- un glob en una MCP genérica, `file:///` incluido;
- el anidamiento de shells más allá de tres niveles, y un shell anidado que recibe su comando
  codificado o de un archivo (`-EncodedCommand`, `-File`);
- una expansión de llaves de más de 256 resultados (OUT_OF_SCOPE_COMPLEXITY_BOUNDARY): lo que la
  política detecte ahí es incidental, no una garantía;
- cualquier sintaxis que no esté en esa lista.

La tabla de arriba es la de la Wave 6 y no se reescribe. La frontera vigente está en
`flow-governance/final-qualification.md`, «R11: el estado vigente».

🔴 **El texto de E-24 se acotó durante la verificación.** El primero decía, sin más, que escribir un
punto de persistencia con una herramienta estaba protegido. La primera pasada encontró caminos que no
lo nombran: los que se pueden ver en el texto —un stream, un nombre corto, `${PROFILE}`, `git config`
con alcance, `site-packages`, la ruta XDG de git y, en las pasadas segunda y tercera, el nombre corto
desde el shell, el stream o el punto final en cualquier segmento, la forma `/c/...` y `-Parametro:valor`—
se cerraron; los que solo se resuelven al correr —un glob, una variable o una concatenación, una ruta
relativa después de un `cd`, `pip install --user`— pasaron a ser límite. Ese recorte lo
tiene que aceptar quien califique (`flow-governance/qualification-readiness.md`).

🔴 **Después de la cuarta pasada, una revisión adversarial independiente contradijo E-24** con tres
clases y nueve entradas: un `site-packages` como destino final, las formas de `git config` que git
acepta por las protegidas, y `uniq -`, que la política leía como lectura y por eso salteaba el
chequeo de persistencia. Se cerraron con E24-E1 a E24-E9. La quinta pasada del refutador encontró
tres formas más que nombran el destino en el texto, y se cerraron con E24-E10 a E24-E12. Lo que esa revisión anotó como límite o
no prometido —un glob, `Get-Variable PROFILE`, una ruta después de un `cd`, `pip install --user`, un
escape o una concatenación, un paquete `sitecustomize/` o un `.pyw`, un destino que solo se calcula
al correr— sigue fuera de E-24.

### La política de lectura

Una opción larga de salida (`--output`, `--out`, `--outfile`, sus abreviaturas y `=valor`) en un
programa de la lista de lectura es escritura, sea cual sea el programa. Lo que no está en la lista
sigue siendo `UNRESOLVED`. Lo que queda es una lista: un programa de ella con otra forma de escribir
sería un hueco de la lista, y está escrito.

### La clase desconocida: lo que promete, ratificado por la persona

```text
UNRESOLVED_TOOL_CLASS != READ_ONLY
UNRESOLVED_TOOL_CLASS -> las restricciones de MUTATING
  tarea gobernada sana                          -> puede pasar
  tarea BLOCKED                                 -> deny
  HUMAN_DECISION_PENDING de la tarea gobernada  -> deny
  binding de la tarea ambiguo o no seguro       -> deny
  HUMAN_DECISION_PENDING de otra tarea          -> deny en el shell (Wave 4); otra herramienta
                                                   desconocida pasa, pero no escribe la autoridad
                                                   (E24-E14)
```

Es el contrato cerrado de la Wave 3 («se trata como `MUTATING`», E-25) y de la Wave 4 (E-53: resuelta
la decisión, `npm test` vuelve a pasar). La afirmación 7 de esta Wave decía «Unknown potentially
mutating commands remain fail-closed»: dice más que ese contrato. **SPEC_OVERSTATEMENT, ratificado
por la persona el 02-10-2026**: no es un defecto de la implementación, y no hay deny global para lo
desconocido. La afirmación queda:

> Unknown tool classes are never treated as READ_ONLY. They inherit the restrictions of MUTATING
> operations and are denied when the governed task is blocked, a human decision is pending on the
> governed task, or task authority is ambiguous.

La séptima pasada leyó «a human decision is pending» también como la de otra tarea, y una herramienta
desconocida que no es shell (`mcp__x__y`) pasa mientras otra tarea espera: la regla cruzada de la
Wave 4 (`interaccion-humana/spec.md`) es del shell. **La persona decidió el 02-10-2026 precisar la
letra y no cambiar el contrato de la Wave 4**: la afirmación habla de la tarea gobernada. Lo que
cerraba esa puerta —que esa herramienta escriba la decisión en `.claude/`— lo cierra E24-E14.

### Una herramienta desconocida no escribe la autoridad

Un servidor MCP que escribe archivos tiene sus propios campos (`path`, `destination`, `edits[].path`…),
y hasta ahora nada los miraba: con la tarea sana, `mcp__filesystem__write_file` sobre `.claude/`,
`.git/` o un `~/.gitconfig` pasaba. **Decisión de la persona del 02-10-2026: MUST_FIX_BEFORE_QUALIFICATION,
dentro de esta Wave.** A una herramienta que la política no conoce y que no es shell se le miran
todos los textos de una línea de su `tool_input`, a cualquier profundidad, con las mismas reglas que
una ruta de Write: si alguno es `.claude/`, `.git/` o un punto de persistencia del host, es
`FLOW_AUTHORITY_PROTECTED`. Se miran también las claves de un objeto (`{"files": {ruta: contenido}}`),
sin tope de profundidad. Un texto con saltos de línea es un contenido y no se mira. Sobreprotege a
propósito: una herramienta desconocida que lee esas rutas, o que tiene un campo de una línea que solo
las menciona, también queda negada. `Task`/`Agent` (la delegación) y las herramientas conocidas no
cambian.

🔴 **Eso solo sirve si la herramienta llega al hook.** La octava pasada mostró que el matcher de
PreToolUse de la Wave 3 (`Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell|^Agent$|^Task$`) no
alcanza a `mcp__*`: en una sesión real una herramienta MCP no pasaba por el hook, ni por la compuerta
ni por esta regla. **Decisión de la persona del 02-10-2026: el matcher suma `^mcp__`, anclado.**

- Las herramientas MCP pasan por la compuerta del flujo, por E24-E14 y por el Secret Guard.
- Cuesta el arranque del hook en cada llamada MCP: el p50 que mide `-Doctor`, unos 100 ms.
- PostToolUse no cambia.
- Un proyecto instalado lo recibe con `-Update`.
- El contrato del matcher de la Wave 3 (`compuerta-del-flujo/spec.md`, «La delegación llega al
  hook») queda ampliado en eso y en nada más.

### Un servidor MCP que corre comandos, y un evento que no se puede leer

La novena pasada, ya con las MCP llegando al hook, encontró dos huecos. **Decisiones de la persona
del 02-10-2026:**

- **Un valor de una línea se mira también como comando.** Un servidor MCP que corre comandos
  (`mcp__shell__run`) recibe el comando en un campo, y la política lo miraba solo como ruta: `git
  config core.fsmonitor x` o `>> ~/.gitconfig` pasaban con la tarea sana. Ahora ese valor pasa por
  la misma regla que el texto de Bash (`toca_persistencia`): `git config` que escribe y un punto de
  persistencia nombrado (E24-E16).
- **Un valor de varias líneas sigue siendo contenido.** Una MCP de shell que recibe un script de
  varias líneas queda como **límite declarado**.
- **Un evento que PreToolUse no puede leer falla cerrado.** Un `tool_input` de unos 3000 niveles
  hace que `json.loads` levante `RecursionError`, y el hook salía 0 sin decidir: pasaba, también
  con la tarea bloqueada. Ahora, si el proyecto tiene estado del flujo, es deny
  `FLOW_GATE_UNRESOLVED`, como un fallo interno de la compuerta (E-54 de la Wave 3).
  - El proyecto sale de `CLAUDE_PROJECT_DIR`, del `cwd` que se alcanza a leer en el texto o de la
    carpeta actual.
  - Sin estado del flujo, sigue como cualquier falla: un aviso y salida 0 (E24-E17).
  - El tope de profundidad ya no es de la política: es de leer el evento, y ahí falla cerrado.

La décima pasada sumó tres ajustes, dentro de esas mismas decisiones:

- **El comando repartido.** Una MCP de shell que recibe `["git", "config", ...]`, o `command` +
  `args`, se mira también como la secuencia de sus palabras: cada lista y cada objeto, con sus
  textos y los de sus listas, en orden (E24-E18).
- **Los bordes.** Un valor se toma sin los espacios ni los saltos de línea de sus bordes. Un `\n`
  al final no convierte un comando en contenido; un script de varias líneas sigue siendo el límite
  declarado.
- **Las comillas sueltas.** Una comilla sin cerrar en un valor que no es un comando (un apóstrofo en
  un comentario de Jira, `Don't`) ya no es «ante la duda, sí»: se parte por los espacios. Lo mismo
  con una ruta de Write: `O'Brien.py` no es la autoridad. En el texto de Bash y PowerShell sigue
  siendo «ante la duda, sí» (E24-E19).

La undécima pasada mostró que esos ajustes seguían dependiendo del orden y de las comillas: `args`
antes que `command`, o un apóstrofo escapado (`don\'t`) que hacía perder un `bash -c "..."`. A una
herramienta que la política no conoce no se le puede saber cómo arma su comando. Por eso, además,
**sus palabras se miran como una bolsa**: todos los valores de una línea partidos por espacios,
comillas y separadores de shell, sin orden (E24-E20).

- Una palabra de la bolsa que es `.claude/`, `.git/` o un punto de persistencia es protegida.
- Si en la bolsa están git y `config` (también `alias.x=config`), es una escritura de la
  configuración y es protegida. Hay una sola excepción: una sola `config`, y algún texto o argv
  que, parseado estricto y con git como programa, es una lectura (`git config --get x`).
- **Sobreprotege a propósito.** Un comentario o un mensaje de una MCP que menciona «git … config»
  se niega como protegido, igual que uno que menciona `.claude/`. El costo lo paga una MCP que
  habla de git; el que se evita es una MCP de shell que escribe `.git/config`.

### El guard de `git config`: no se parsea forma por forma (E24-E21)

La duodécima pasada contradijo E-24 y las afirmaciones 8 y 9 con dos formas de PowerShell que
llegaban a un `git config` que escribe sin quedar protegido: un scriptblock sin espacio después de
`{` (`& {git config ...}`) y `Start-Process` con un arreglo `@(...)` o con `-FilePath:git`. Con la
tarea bloqueada eran deny por `UNRESOLVED`; con la tarea sana pasaban.

**Decisión de la persona del 04-10-2026: se abandona el parser forma por forma para esta superficie.**
Cada pasada encontraba otra sintaxis. La regla queda al revés:

```text
git y `config` a la vista en el texto  +  sin prueba positiva de lectura  =  FLOW_AUTHORITY_PROTECTED
```

- **Lo que es evidencia.** El texto se parte por los separadores de cualquier shell, también `{`,
  `}`, `[`, `]`, `@`, `:`, `=` y `!`. Y se lee además como el shell une una palabra: sin las
  continuaciones de línea (`\`, `` ` `` o `^` y un salto, en Bash, PowerShell y cmd) y sin lo que
  junta o vale vacío (`\`, `` ` ``, `^`, `'`, `"`, `+`, `$`, `(`, `)`, `@`): `g\it`, `'gi'+'t'`,
  `g$'i't`, `g$()it`. No es una lista de formas: es la regla de cómo se arma una palabra, y una
  forma nueva que la parta por otro lado se corrige en esa regla. Hacen falta las dos palabras: git como programa (`git`,
  `git.exe`, `git.cmd`, una ruta que termina en git, `git-config`) y `config`. Una sola no alcanza:
  `npm config ...` o `& {git status}` no son el guard.
- **La exención de lectura es positiva.** Pasa solo si hay una sola `config` y el texto, parseado
  estricto con el parser de siempre (`_subcomando_de_git`, `_config_de_git`), es `git ... config
  <una lectura>`: `--get`, `--get-regexp`, `--list`, `-l`, `get`, `list` o un nombre solo, con
  cualquier alcance. Sin separadores, y sin nada que no se sepa qué vale: una variable, una
  sustitución, un splat de PowerShell (`@args`), un scriptblock. «No vi un verbo que escribe» no es
  una prueba.
- **Sin excepción por clave.** Toda escritura de `git config`, local, global, de sistema o de
  archivo, es autoridad protegida; no solo `core.fsmonitor`.
- **Dónde se aplica.** Al texto de Bash y PowerShell que el parser no probó `READ_ONLY` (salvo la CLI
  del Harness), y a la bolsa de una herramienta desconocida (E24-E20), que usa la misma función. Un
  splat de PowerShell (`git config @a`) deja de ser `READ_ONLY`: es una variable.
- **No es un deny global.** `UNRESOLVED_TOOL_CLASS` no cambia: con la tarea sana puede pasar, con
  la tarea bloqueada, una decisión pendiente o la autoridad ambigua es deny. El guard es aparte, y
  solo se activa si el texto deja ver un `git config`.
- **INTENTIONAL_CONSERVATIVE_OVERPROTECTION.** La persona acepta los falsos positivos sobre esta
  superficie: un falso positivo cuesta menos que un bypass de la autoridad. Los conocidos: `git
  commit -m "update config"`, `echo git config x > notas.txt`, `git config --get-regexp 'x$'` (el `$`
  no se sabe qué vale), una lectura partida por una continuación de línea (`git conf\` y un salto
  y `ig --get x`) y una lectura de `git config` encadenada con algo que no se reconoce. Se
  rodean con `git commit -F <archivo>` o separando la lectura.
- **Lo que queda fuera** es un `git config` cuyas palabras no están en el texto: armado con
  variables, leído de un archivo o codificado. Es límite declarado.

### `git config` que escribe es autoridad, con cualquier alcance

`.git/` es autoridad del flujo desde la Wave 4: Write y Edit no la escriben. `git config` sin alcance
escribe `.git/config` por otro camino, y un `core.fsmonitor`, un `core.hooksPath` o un `core.pager`
plantados ahí con la tarea sana corren después con un `git status` o un `git log`, que son lectura y
pasan también con la tarea bloqueada. **Decisión de la persona del 02-10-2026: MUST_FIX_BEFORE_QUALIFICATION,
dentro de esta Wave.** Toda escritura de `git config` es `FLOW_AUTHORITY_PROTECTED`, sin excepción
por clave: `.git/config`, `--local`, `--worktree`, `--global`, `--system` y `--file`/`-f`.

Las lecturas siguen siendo lecturas. Las decide el mismo parser:

- una opción de lectura: `--get`, `--get-all`, `--get-regexp`, `--list`/`-l`, `--get-urlmatch`,
  `--get-color`, `--get-colorbool`;
- un subcomando de lectura de la sintaxis nueva: `get`, `list`;
- un nombre solo, como `git config user.email`.

Un modificador de cómo se muestra (`--show-origin`, `--type=bool`, `-z`…) no es la acción. `git
commit`, `git status` y `git diff` no son `git config`. El nombre solo es lectura únicamente cuando git
es el programa del comando: detrás de otro programa (`xargs`, `cmd /c`, `bash -c`, un alias de `-c`)
el valor puede llegar al correr, y se trata como escritura.

## Escenarios

Cada `E-nn` es el `W6-0nn` con el mismo número hasta E-35.

### Bloque 4
- **E-01** — Un mensaje del asistente sin ningún número de uso es `USAGE_UNRESOLVED`, con clave
  estable; nunca `RESOLVED`. `rojo visto`
- **E-02** — Ese registro llega al libro por la barra y por `contabilidad --ingerir`, una sola vez.
  `rojo visto`
- **E-03** — La barra no lo muestra como tokens, y el libro lo conserva. `rojo visto`
- **E-04** — Un costo parcial no da `WITHIN_BUDGET`: da `COST_UNRESOLVED`, y la barra no da WARNING ni
  ERROR sobre el piso. `rojo visto`
- **E-05** — Un costo resuelto decide como siempre. `rojo visto, por mutación`

### Refutación
- **E-06** — `refutacion.compilar` directo, con el plan sin estar listo: no compila (`PLAN_NOT_READY`).
  `rojo visto`
- **E-07** — Con el TaskContext cambiado: no compila (`CONTEXT_STALE`). `rojo visto`
- **E-08** — Con otro checkout: no compila (`REPOSITORY_MISMATCH`). `rojo visto`

### Secretos
- **E-09** — `AlmacenSecretos.set/remove` no escriben el `.env`: levantan y lo dejan byte a byte igual.
  `rojo visto`
- **E-10** — Ninguna ruta del harness llama a `set` ni a `remove`. `rojo visto, por mutación`

### Diagnóstico cruzado
- **E-11** — Una sesión ligada a una tarea bloqueada sigue sin poder correr `contabilidad` sobre otra.
  `rojo visto, por mutación`
- **E-12** — El motivo nombra la tarea a la que apunta el comando y la que se evaluó. `rojo visto`
- **E-13** — Tampoco pasa si la otra tarea está sana: no hay salto de tarea. `rojo visto, por mutación`

### Plan
- **E-14** — `workUnits[].context.repository` es el repositorio de la identidad del flujo. `rojo visto`
- **E-15** — El aviso de ES0901 nombra lo que cuenta y no dice que la matriz no existe. `rojo visto`

### Instalación y runtime
- **E-16** — Sin libro, el Bloque 4 no es `ACTIVE`, y la barra con señal `OK` es `CONFIGURED`, no
  `ACTIVE`. Un libro sin ningún registro (`"\n"`, `" "`, `"x"`, `{}`, `[1]`) es lo mismo que no tener
  libro. `rojo visto`
- **E-17** — `-Doctor` no muestra en OK una barra `CONFIGURED`. `rojo visto`
- **E-18** — Una señal sin la versión o el momento que registró el instalador, o con uno que no
  tiene su forma, no prueba nada: `RELOAD_REQUIRED`. `rojo visto`

### CLI
- **E-19** — `plan` con una propuesta inválida sale con 2, sin traceback. `rojo visto`
- **E-20** — Un error inesperado no se convierte en `PlanInvalido` ni sale con 2. `rojo visto, por mutación`

### Agentes y Python
- **E-21** — `dev-iniciador-code` está registrado, no es huérfano y resuelve su ruteo. `rojo visto`
- **E-22** — `-Doctor` avisa si `python` es el alias de la Store, e `Invoke-Tests` no lo toma por un
  Python. `rojo visto`

### Política y modelo de amenaza
- **E-23** — Un comando desconocido sigue `UNRESOLVED`, y una opción larga de salida en un programa de
  lectura es escritura. `rojo visto`
- **E-24** — El modelo de amenaza está escrito, y lo que se puede neutralizar localmente está
  protegido: escribir un punto de persistencia del host con una herramienta —también por un stream de
  NTFS o un punto final en cualquier segmento, un nombre corto (con Write, Edit o el shell), la forma
  `/c/...` de Git Bash, un `-Parametro:valor` de PowerShell, `${PROFILE}`, un `site-packages` (también
  la carpeta misma como destino), la ruta XDG de git, un `git config` que escribe con cualquier
  alcance (también sin alcance, que es `.git/config`; abreviados como los acepta git, o `-f<ruta>`) o
  `uniq - <salida>`— es
  `FLOW_AUTHORITY_PROTECTED`, y el `git status` de SessionStart corre sin `core.fsmonitor`. Lo que no
  se puede ver desde el texto del comando está escrito como límite. `rojo visto`
  - **E24-E1** — `Copy-Item -Recurse payload ...\site-packages.`: deny protegido. `rojo visto`
  - **E24-E2** — `cp -r payload/ .../site-packages./`: deny protegido. `rojo visto`
  - **E24-E3** — La carpeta `site-packages` por su nombre corto 8.3, desde Bash y desde PowerShell:
    deny protegido. `rojo visto`
  - **E24-E4** — `git config --glob` que escribe: deny protegido. `rojo visto`
  - **E24-E5** — `git config --sys` que escribe: deny protegido. `rojo visto`
  - **E24-E6** — `git config --fil <ruta>` que escribe: deny protegido. `rojo visto`
  - **E24-E7** — `git config -f<ruta>` que escribe: deny protegido. `rojo visto`
  - **E24-E8** — `uniq - <salida protegida>`: `MUTATING`, deny protegido. `rojo visto`
  - **E24-E9** — `uniq -- - <salida protegida>`: `MUTATING`, deny protegido. `rojo visto`
  - **E24-E10** — `git config --global` con sus argumentos en una sola palabra detrás de otro
    programa (`Start-Process git '...'`, `-ArgumentList '...'`, también como arreglo de PowerShell,
    `-ArgumentList 'config','--global',...`) o en un alias de `-c`
    (`alias.x='config --global ...'`): deny protegido. `rojo visto`
  - **E24-E11** — La carpeta `site-packages` pegada a una opción con `=`
    (`--target-directory=site-packages`, también con punto final): deny protegido. `rojo visto`
  - **E24-E12** — Un punto de persistencia relativo pegado a una opción corta (`sort -ositecustomize.py`,
    `-ousercustomize.py`, `-o.gitconfig`, `-osite-packages/x.py`): deny protegido. `rojo visto`
  - **E24-E13a** — `git config user.email x@example.invalid`: `MUTATING`, deny protegido. `rojo visto`
  - **E24-E13b** — `git config core.fsmonitor <valor sintético>`: deny protegido. `rojo visto`
  - **E24-E13c** — `git config --add user.name x`: deny protegido. `rojo visto`
  - **E24-E13d** — `git config --replace-all user.name x`: deny protegido. `rojo visto`
  - **E24-E13e** — `--unset`, `--unset-all`, `--remove-section` y `unset`: deny protegido. Lo mismo
    `--local`, `--worktree`, `set`, `--edit` y `git -C . config ...`. `rojo visto`
  - **E24-E13f** — `git config user.email`, un nombre solo: `READ_ONLY`, pasa. `rojo visto`
  - **E24-E13g** — `git config --get user.email`: `READ_ONLY`. `rojo visto`
  - **E24-E13h** — `git config --list` y `-l`: `READ_ONLY`. Lo mismo `--get-regexp`, `get`, `list`,
    `--show-origin --list`, `--type=bool --get` y `-z --list`. `rojo visto`
  - **E24-E13i** — `git commit`, `git status` y `git diff` no quedan protegidos por esta regla, y
    `npm test` sigue pasando con la tarea sana y con deny con la tarea bloqueada (E-53 de la Wave 4).
    `rojo visto: no consta` (son controles)
  - **E24-E13j** — Detrás de un programa que le agrega argumentos al correr (`echo x | xargs git config
    core.fsmonitor`, `xargs -a args.txt git config ...`, también con `--local` o `--glob`), un nombre
    solo no es una lectura: deny protegido. Lo encontró la séptima pasada como regresión de E24-E13f.
    `rojo visto`
  - **E24-E14a a E24-E14f** — Una herramienta desconocida que no es shell con un valor de una línea
    que es `.claude/` (una decisión, `settings.json`), `.git/config`, `~/.gitconfig`, un
    `usercustomize.py` como `destination`, o un perfil de PowerShell dentro de `edits[].path`: deny
    protegido, con la tarea sana. `rojo visto`. Y los controles: la misma herramienta sobre
    `src/app.py`, un contenido de varias líneas que menciona `.claude/`, `mcp__jira__get_issue` y
    `mcp__x__y` sin rutas pasan con la tarea sana; `Task` sigue siendo la delegación.
  - **E24-E15** — El matcher registrado de PreToolUse alcanza a `mcp__*` y a nada más de lo que no
    alcanzaba (`TaskCreate`, `Read`, `WebFetch`, `x_mcp__y` siguen afuera); PostToolUse no cambia. Y
    E24-E14 mira una ruta a 12 niveles de profundidad, en una lista o en un objeto, y como clave de
    un objeto. `rojo visto`
  - **E24-E16** — Una MCP que corre comandos con `git config core.fsmonitor x`, `git config
    core.hooksPath h`, `git config --global ...` o `echo ... >> ~/.gitconfig` en un valor de una
    línea: deny protegido, con la tarea sana. `npm test`, `git config --get`, `git status` y `pytest`
    por la misma MCP pasan. `rojo visto`
  - **E24-E17** — PreToolUse con un evento que no se puede leer (un JSON de 3000 niveles o un JSON
    roto) en un proyecto con estado del flujo: salida 0 y deny `FLOW_GATE_UNRESOLVED`, también corrido
    desde otra carpeta (lo encuentra por el `cwd` del texto). Sin estado del flujo no bloquea.
    `rojo visto`
  - **E24-E18** — Una MCP de shell con el comando como arreglo (`["git", "config",
    "core.fsmonitor", "evil"]`, también con `--global`), repartido en `command` + `args`, un argv a
    un `.gitconfig`, o con un `\n` o `\r\n` al final: deny protegido. El argv de `git config
    --get` y el de `npm test` pasan. `rojo visto`
  - **E24-E19** — Un apóstrofo en un comentario o un mensaje de una MCP, o una comilla suelta, no
    es protegido: pasa con la tarea sana. Con una ruta de la autoridad al lado, sigue negado. Write
    a `src/O'Brien.py` pasa; Write a `x'/.claude/y.json` sigue negado. `rojo visto`
  - **E24-E20** — En cualquier orden y con cualquier comilla: `{"args": [...], "command": "git"}`,
    un campo en el medio, `argv` antes que `program`, `args` anidados, `bash -c "git config ..."` o
    `Start-Process git '...'` con un apóstrofo escapado al lado, un alias con un apóstrofo escapado:
    deny protegido. `git config --get` (texto o argv), un apóstrofo sin git config, `npm test` y
    `git status` pasan. `rojo visto`
  - **E24-E21** — Con la tarea sana, deny `FLOW_AUTHORITY_PROTECTED`:
    - A: un scriptblock de PowerShell sin espacio después de `{` (`& {git config --global ...}`,
      `Invoke-Command -ScriptBlock {git config ...}`);
    - B: `Start-Process` con un arreglo `@('config', ...)`;
    - C: `Start-Process -FilePath:git` o `-FilePath:'C:/Program Files/Git/cmd/git.exe'`, con los
      argumentos en una palabra o en `-ArgumentList:@(...)`;
    - D: un escape o una concatenación (`g\it`, ``g`it``, `cmd /c g^it`, `& ('gi'+'t') config ...`),
      una continuación de línea que parte `git` o `config` (`\`, `` ` `` o `^` y un salto, también
      `\r\n`, también en `-FilePath:`), o algo que vale vacío (`g$'i't`, `"g$()it"`). La
      continuación la encontró la decimotercera pasada;
    - I: una MCP con esas mismas formas en un valor de una línea, o repartidas en campos;
    - J: un `git config` ambiguo (`git config $valor`, `git config @argumentos`, `git config $NOMBRE`).

    Y los controles, que pasan con la tarea sana y no son protegidos:
    - E y F: `git config --get`, `--get-regexp`, `--list`, `-l`, con y sin alcance (`--global`,
      `--local`, `--system`, `--file x`), en Bash y PowerShell, siguen `READ_ONLY`; `git -c ...
      config --get` sigue `UNRESOLVED_TOOL_CLASS` y no es protegido;
    - G: git sin `config` (`& {git status}`, `Start-Process git -ArgumentList @('status')`, `nohup
      git log`, `git commit -m arreglo`);
    - H: `config` sin git (`npm config set`, `Start-Process npm -ArgumentList @('config','list')`,
      `& {npm config get prefix}`, un comentario de Jira que dice «config»).

    Lo desconocido sin git config sigue `UNRESOLVED_TOOL_CLASS`: pasa con la tarea sana y es deny
    con la tarea bloqueada. `rojo visto`: 34 aserciones en rojo antes del código, y 16 más antes
    de corregir la regla por la decimotercera pasada.

  Y los controles: `cat ~/.gitconfig`, `git config --global --get`, `git config --glob --get`,
  `uniq f`, `uniq -` y `uniq -- f` siguen `READ_ONLY`; `cp` a `build/` o a un `site-packages-viejo/`,
  `git config user.email` (la lectura) y `uniq - salida.txt` siguen pasando con la tarea sana y no son
  protegidos;
  `sort -osalida.txt`, `--target-directory=build`, `git commit -m ...` y `Start-Process git 'commit
  ...'` no son protegidos, mientras no digan `config` (E24-E21).

### La evidencia de la Context Bar (aceptación manual B)
- **E-36** — Un dibujo con datos deja en la señal la evidencia de su sesión, con la huella del comando
  que corrió, la versión del renderizador y el momento, sin ningún número. Un dibujo sin datos no la
  inventa. `rojo visto`
- **E-37** — SessionStart de una sesión nueva, después de que otra dibujó con datos: `CONFIGURED` y
  `activeInCurrentSession: false`, sin copiar el `true` de la anterior. La evidencia queda en la señal
  y el estado guardado la nombra en `lastSessionWithData`. `rojo visto`
- **E-38** — El primer dibujo vacío de la sesión nueva no borra, no reemplaza y no degrada la
  evidencia anterior. `rojo visto`
- **E-39** — Después del reinicio y de ese dibujo vacío, `-Doctor` con Python y `harness` calculan en
  vivo: `ACTIVE` por la sesión anterior, con `activeInCurrentSession: false`. El estado guardado por
  SessionStart y la sesión nueva siguen `CONFIGURED`. `rojo visto`
- **E-40** — Con otra huella del `statusLine`, o con un registro posterior al dibujo, la evidencia no
  prueba nada y `-Doctor` no dice `ACTIVE`. `rojo visto`
- **E-41** — Con otra versión del renderizador, la evidencia no prueba nada. `rojo visto`
- **E-42** — Un dibujo con datos de otra sesión pasa la evidencia a esa sesión. `rojo visto`
- **E-43** — Recién instalada, o con sesiones que solo dibujaron vacío, `-Doctor` no dice `ACTIVE`.
  `rojo visto`
- **E-44** — `-Doctor` sin Python, o con un `bienvenida.py` que se cae o no devuelve la barra, usa el
  estado guardado tal cual: sin traceback y sin inventar `ACTIVE`. `bienvenida.py barra` sobre un
  proyecto sin harness sale 0 y no dice `ACTIVE`. `rojo visto`
- **E-45** — `-Doctor` con Python decide con lo que calcula `bienvenida.py barra` y nombra la última
  sesión con datos. `rojo visto`
- **E-46** — La secuencia de la aceptación con el renderizador de verdad: B1 `RELOAD_REQUIRED`, B2/B3
  `CONFIGURED`, B4 `-Doctor` `ACTIVE` con la sesión nueva sin activar. No reemplaza la aceptación
  manual: la repite la persona. `rojo visto`

### Lo que no se rompe
- **E-25** — La Wave 5 sigue verde (`65_fail_closed`). `rojo visto: no consta`
- **E-26** — La Wave 4 sigue verde (`64_interaccion_humana`). `rojo visto: no consta`
- **E-27** — La Wave 3 sigue verde (`63_compuerta_del_flujo`). `rojo visto: no consta`
- **E-28** — La Wave 2 sigue verde (`62_estado_del_flujo`). `rojo visto: no consta`
- **E-29** — La Wave 1 sigue verde (`61_flujo_precondiciones`). `rojo visto: no consta`
- **E-30** — La refutación atómica sigue verde (`55_refutacion_atomica`). `rojo visto: no consta`
- **E-31** — Entorno primero sigue verde (`60_entorno_primero`). `rojo visto: no consta`
- **E-32** — El reporte de seguridad sigue verde (`48_reporte_de_seguridad`). `rojo visto: no consta`
- **E-33** — El Bloque 4 sigue verde (`30_b4_contabilidad`). `rojo visto: no consta`
- **E-34** — La Context Bar sigue verde (`53_context_bar`). `rojo visto: no consta`
- **E-35** — La compuerta entera, `.\tests\Invoke-Tests.ps1`. `rojo visto: no consta`

## Lo que cambia en tests de cambios cerrados

Cada uno queda dicho en el test, con la Wave 6 y el escenario que lo pisa:

| Test | Por qué |
|---|---|
| `18_integraciones` E-03 a E-06 y los helpers `_jira`/`_gitlab` | `set`/`remove` ya no escriben: los tests afirman que levantan y no tocan el archivo, y siembran el `.env` escribiéndolo como la persona (E-09) |
| `20_orquestacion` E-28 | El aviso de ES0901 nombra el archivo que cuenta (E-15) |
| `22_registro_agentes` E-01, E-02, E-03, E-18, E-18b, E-29 | `dev-iniciador-code` está registrado: once agentes, ningún huérfano real; el huérfano y el reconocido se fabrican (E-21) |
| `51_bienvenida` (fixture y E-13, E-18, la bienvenida que no se puede escribir) | La prueba de la señal pide el registro del instalador, y `ACTIVE` un libro con datos (E-16, E-18) |
| `53_context_bar` (fixture y E-03, E-09, E-18, E-41) | Lo mismo: una señal viene con su registro y su libro; recién instalado, el Bloque 4 es `CONFIGURED` (E-16, E-18) |
| Los 16 casos de ES0902 (`37`, `39` a `44`, `46`, `47`, `49`, `50`, `52`, `54`, `56`, `58`, `59`) | Fijaban «diez agentes»: son once con `dev-iniciador-code`. Lo que afirman —ese control no creó ningún agente— no cambia (E-21) |
| `55_refutacion_atomica`, `56`, `58`, `59` (fixtures y E-04 de 55) | `compilar` evalúa la compuerta: los proyectos de prueba la pasan con `_listo_para_la_compuerta` (E-06 a E-08) |
| `03-instalador.ps1`, `$hpsMatcherPre` | El matcher instalado de PreToolUse suma `^mcp__` (E24-E15) |
| `53_context_bar` E-10 | Un dibujo con datos suma `lastSessionWithData` a la señal: los cinco campos y la evidencia de esa sesión (E-36) |

## Cómo se verifica

`tests/casos/66_integrity_cleanup.py` tiene un test por escenario, de E-01 a E-24, con el id en el
nombre; lo de PowerShell (E-17, E-22) está en `tests/casos/66-integrity-instalador.ps1`, que saca las
dos funciones de `-Doctor` de `install.ps1` con el parser y las corre sueltas. Su rojo se vio por
mutación (`Get-NivelDeLaBarra` dando `ok` para `CONFIGURED`). E-25 a E-34
son los archivos de la suite que nombran, y E-35 es la compuerta entera. E-36 a E-46 están en los dos mismos archivos: el
renderizador corre de verdad sobre el árbol que arma `tests/medir_barra.py`, y la mitad de `-Doctor`
(E-44, E-45) saca `Get-BarraEnVivo` y `Get-BarraDelDoctor` de `install.ps1`. Verifica
`harness-spec-refuter`, que no es quien construyó.
