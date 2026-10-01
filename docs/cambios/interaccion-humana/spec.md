# Flow Governance, Wave 4 — la persona responde, decide y retoma

**Estado:** verificado y cerrado · **Fecha:** 30-09-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Después de la Wave 3, una tarea que espera a una persona se queda esperando. La compuerta niega lo
que modifica y el enlace muestra dónde completar lo que falta. Pero no hay cómo aprobar una
solicitud de escalamiento, elegir entre dos repositorios, cancelar la tarea o decir «ya lo cargué,
seguí». Y si lo hubiera como un comando más, lo podría correr el modelo solo. Eso es lo que esta Wave
no puede permitir:

```text
model tool call
!=
human approval
```

La autoridad sale de un evento que prueba que la persona escribió algo: `UserPromptSubmit`. El
comando que aplica la decisión lo puede correr el modelo, pero solo consume lo que la persona dejó
registrado antes, una vez, para esa sesión, esa tarea, esa interacción y ese estado.

## Qué queda afuera

- **La Wave 5:** endurecer las capacidades, el `UNRESOLVED` del reporte de seguridad y la
  presentación del Bloque 4. **La Wave 6:** `dev-iniciador-code` y la limpieza.
- **Escribir el `.env` o `harness.config.json`.** La persona los edita; el harness revalida.
- **Un input por consola.** `setup` y `reconfigurar` siguen sin preguntar nada.
- **Cambiar `task-flow-state/1.0`, `session-task-binding/1.0` o `flow-required-inputs/1.0`.** El
  `interactionId` se deriva, no se guarda en el estado.

## Las decisiones, y por qué

### Interacciones: de dónde salen y cómo se llaman

`flujo/interaccion.py` deriva las interacciones abiertas del estado guardado de la tarea y de su plan.
No guarda nada:

| Bloqueo | Tipo | Acciones |
|---|---|---|
| `HUMAN_APPROVAL_PENDING`, una por cada `humanApprovals[]` en `PENDING` | `HUMAN_DECISION` | `APPROVE`, `USE_ALTERNATIVE` (la opción es el tier de `cheaperAlternative`), `CANCEL` |
| `REPOSITORY_CONFLICT` (`repository.unambiguous`) | `HUMAN_DECISION` | `CHOOSE` (la opción es uno de los candidatos observados), `CANCEL` |
| Un `PERSISTENT_CONFIG_INPUT` | `PERSISTENT_CONFIG_INPUT` | `RESUME`, `CANCEL` |
| Un `TASK_INPUT` | `TASK_INPUT` | `ANSWER` (si su fuente de verdad acepta un valor), `RESUME`, `CANCEL` |
| Un bloqueo `DERIVABLE` | — | ninguna: lo resuelve el harness |

Una tarea `CANCELLED` o `COMPLETED` no tiene interacciones.

El `interactionId` es `ixn-` y los primeros 16 hex del SHA-256 de datos no secretos: la tarea, el
tipo, el `inputId`, el código, el `blockerId`, la unidad de trabajo, el `planFingerprint` y el
`contextHash`. No lleva la hora. Si cambia el bloqueo, el plan o el contexto, cambia el id, y un
intent sobre el id anterior queda viejo.

El `stateFingerprint` es el SHA-256 del estado guardado sin `updatedAt` (`estado.logico`).

### La gramática de la persona

Un prompt es una intención humana solo si es **exactamente** una línea de esta forma, en
mayúsculas:

```text
HARNESS APPROVE     ABC-123 <interactionId>
HARNESS ALTERNATIVE ABC-123 <interactionId> <optionId>
HARNESS CHOOSE      ABC-123 <interactionId> <optionId>
HARNESS CANCEL      ABC-123 <interactionId>
HARNESS ANSWER      ABC-123 <interactionId> <valor-no-secreto>
HARNESS RESUME      ABC-123
```

«dale», «ok», «sí», «aprobá», «hacelo» o un comando metido en un párrafo no son una intención. No se
interpreta lenguaje natural para una aprobación.

### `human-intent/1.0`

```
.claude/runtime/sessions/<SAFE_SESSION_ID>/human-intent.json
{schema_version, sessionId, taskKey, interactionId, action, inputId, optionId, value,
 stateFingerprint, planFingerprint, createdAt, consumedAt}
```

Lo escribe solamente `UserPromptSubmit` (`comun/hooks/lib/human_intent.py`), después de comprobar
que la interacción está abierta en el estado guardado y que la acción es una de las suyas. Uno por
sesión: una intención nueva reemplaza a la anterior. `value` existe solo para `ANSWER`, y un valor
con forma de secreto (el catálogo del Secret Guard, o un input `SECRET`) se rechaza sin guardarse.
No guarda el prompt, ni un token, ni una línea del `.env`.

`RESUME` no escribe intent: retomar es revalidar, y revalidar no puede saltear nada.

### Aplicar: `flujo <KEY> --approve|--alternative|--choose|--cancel|--answer`

```
dev-harness.py flujo ABC-123 --approve     <interactionId>                 --sesion <session_id>
dev-harness.py flujo ABC-123 --alternative <interactionId> --option <id>   --sesion <session_id>
dev-harness.py flujo ABC-123 --choose      <interactionId> --option <id>   --sesion <session_id>
dev-harness.py flujo ABC-123 --cancel      <interactionId>                 --sesion <session_id>
dev-harness.py flujo ABC-123 --answer      <interactionId> --value <valor> --sesion <session_id>
dev-harness.py flujo ABC-123 --resume
```

`estado_de_tarea/decisiones.py` aplica en este orden, y cualquier paso que falla deja todo como
estaba:

1. Lee el intent de esa sesión. Sin intent: `HUMAN_INTENT_REQUIRED`. Consumido:
   `HUMAN_INTENT_ALREADY_CONSUMED`. De otra sesión: `HUMAN_INTENT_SESSION_MISMATCH`. De otra tarea:
   `HUMAN_INTENT_TASK_MISMATCH`. Otra interacción, otra acción u otra opción que las del comando:
   `HUMAN_INTENT_MISMATCH`.
2. Recalcula las interacciones abiertas. La del intent ya no está, o el estado cambió:
   `HUMAN_INTENT_STALE`. El plan cambió desde la intención: `HUMAN_DECISION_STALE`.
3. Valida la opción contra la lista cerrada: `HUMAN_OPTION_INVALID`. Un `ANSWER` sobre algo que no
   acepta valor: `HUMAN_ANSWER_NOT_ACCEPTED`.
4. Consume el intent (`consumedAt`, escritura atómica) **antes** del efecto: un corte a la mitad
   deja la intención gastada, nunca aplicada dos veces.
5. Aplica el efecto acotado, escribe `human-decision-record/1.0` y reconcilia el estado con la
   Wave 2. El estado sale de derivar, nunca de «marcar ACTIVE».

| Acción | Efecto |
|---|---|
| `APPROVE` | La aprobación de esa unidad pasa a `APPROVED` y la unidad a `PENDING`, por `orq_plan.replanificar` (sube `plan_version`, lo anota en `planHistory`). |
| `USE_ALTERNATIVE` | La aprobación pasa a `DOWNGRADED` y la unidad corre en el tier de la alternativa. |
| `CHOOSE` | Queda el candidato elegido para ESTA tarea; `repositorio.identidad` lo usa si sigue siendo uno de los candidatos del mismo TaskContext. `GITLAB_PROJECT` no se toca. |
| `CANCEL` | `derivar` da `CANCELLED` mientras exista el decision record. No borra el TaskContext, el plan, la refutación ni las decisiones. |
| `ANSWER` | Hoy ningún input lo acepta (ver abajo): se rechaza con `HUMAN_ANSWER_NOT_ACCEPTED`. |

Después del efecto, la tarea retoma desde su `resumeFrom` con las compuertas de siempre. Aprobar no
salta a EXECUTION: si el plan tiene otra aprobación pendiente, otro bloqueo o está viejo, se queda
ahí.

### `human-decision-record/1.0`

```
.claude/runtime/tasks/<KEY>/decisions/<interactionId>.json
{schema_version, taskKey, interactionId, action, inputId, workUnitId, optionId,
 planFingerprint, planFingerprintAfter, contextHash, stateFingerprint, sessionId, decidedAt}
```

Sobrevive a un reinicio: `CANCEL` y `CHOOSE` se reconstruyen de acá, y `APPROVE`/`USE_ALTERNATIVE`
quedan en el plan. Si alguien borra todo el runtime, no hay decisión, y eso vuelve a esperar: nunca
se asume una aprobación.

### Configuración persistente: editar y retomar

La persona edita el archivo con el enlace de `entrada_humana` y escribe `HARNESS RESUME ABC-123`.
El modelo corre `flujo ABC-123 --resume`. Si sigue faltando, la tarea sigue `BLOCKED` y se vuelve a
mostrar el input. Si quedó bien, avanza hasta la próxima compuerta, que puede ser otro bloqueo: con
un valor sintético, por ejemplo, la sonda da `CONNECTION_FAILED`, y eso es un bloqueo nuevo y válido.
Resolver un bloqueo no es dejar lista la tarea.

Lo que hace `flujo <KEY> --resume`, exactamente:

1. **Lee el estado guardado** para saber qué estaba pendiente.
2. **Si lo pendiente es la configuración de una integración** —un `PERSISTENT_CONFIG_INPUT` de
   `jira.*` o de `gitlab.*`, o `jira.availability`—, revalida las integraciones por el camino de
   siempre: `registrar_capacidades` de `dev-harness.py`, el mismo que usan `estado`, `setup`,
   `reconfigurar` y `contexto --revalidar`. Relee el `.env` (`entorno.resolver`), hace **una sonda por
   integración** —es lo único de `--resume` que sale a la red, y solo en este caso— y escribe el
   registro de capacidades. No repite ese código: lo llama.
3. **Reconcilia el estado** con la Wave 2 (`persistencia.reconciliar`): relee el `.env`, el
   TaskContext, el plan, los remotos y, en CONTEXT, el estado de Jira del registro de capacidades.
   Si Jira está configurado pero la última sonda dio `AUTHENTICATION_FAILED`, `CONNECTION_FAILED` o
   `PERMISSION_DENIED`, CONTEXT queda bloqueado con ese código (`jira.availability`).
4. **Retoma** desde el `resumeFrom` que dé esa reconciliación, con las compuertas de siempre.

Otro bloqueo —un repositorio, un plan, una refutación— no dispara ninguna sonda: `--resume`
reconcilia y nada más. Nunca imprime ni guarda un valor, nunca pregunta por la consola y no toca TLS.

### Una sola fuente para el hook y para `flujo --status`

El hook y la compuerta aplican el **estado guardado**: es lo único que pueden leer sin el `.env`. Por
eso `flujo <KEY> --status` muestra ese mismo estado, y si revalidar lo cambiaría —la persona ya editó
el `.env`, por ejemplo— lo dice debajo («Revalidado ahora …») con el comando que lo aplica. Y el
bloque de `UserPromptSubmit`, cuando el input ya está cargado en el archivo (`present` de
`entrada_humana`, sin leer el valor), dice que falta retomar. Los dos dicen lo mismo: bloqueada por lo
mismo, y que falta `--resume`.

### `flujo --status` y `flujo --status --json`: la misma autoridad

La autoridad del flujo de una tarea es su estado persistido,
`.claude/runtime/tasks/<KEY>/state.json`, leído por `flujo.estado.leer`. La leen los tres que la
muestran o la aplican, y ninguno la recalcula:

| Quién | Qué es | Para quién |
|---|---|---|
| `flujo <KEY> --status` | El estado vigente, en español. | La persona y el modelo. |
| `flujo <KEY> --status --json` | El mismo estado vigente, tal cual está guardado: un `task-flow-state/1.0` válido contra su schema, sin campos de más. | Un programa: un script, un CI, otro agente. |
| La compuerta (PreToolUse) y los hooks | Lo aplican: `evaluar_tarea` lo lee con `estado.leer`. | El enforcement. |

**Status no es revalidación.** Status dice qué estado está vigente y gobierna ahora. Revalidar es
volver a consultar las fuentes y reconciliar, y eso lo hace una operación explícita —`--resume`, o los
comandos que reconcilian (`contexto`, `plan`, `refute`)—, que persiste el estado nuevo; recién entonces
ese estado es la autoridad. Un estado calculado y no persistido no es la autoridad, y nadie lo aplica.

```
STATUS READS AUTHORITY
RESUME MAY CHANGE AUTHORITY
```

- **La vista previa de la revalidación** existe solo en la salida en español: la línea «Revalidado
  ahora …», que dice que la compuerta aplica lo guardado y con qué comando se aplicaría lo otro. No
  entra en el JSON, ni la consume ninguna compuerta. Una vista previa en JSON pediría otro contrato y
  queda diferida.
- **Sin estado guardado, o con uno roto**, no hay autoridad que serializar. `--status --json` no
  inventa un documento: sale con 2 y dice `TASK_FLOW_STATE_MISSING` o `TASK_FLOW_STATE_INVALID`. La
  salida en español lo dice igual, con los permisos en `no`, y muestra debajo lo que se derivaría,
  rotulado como no aplicado.
- `--status`, con o sin `--json`, no sale a la red, no corre el bootstrap, no toca el registro de
  capacidades, no imprime ni guarda un valor del `.env` y no escribe el estado. `--json` ni siquiera
  abre el `.env`; el texto sí lo lee, con `entorno.resolver`, para armar la vista previa.

Esto cambia lo que la Wave 2 dejó en `--status --json`: allí era el estado derivado de ahora. Ningún
consumidor del harness lo leía; la compuerta nunca lo leyó.

### `TASK_INPUT` y `ANSWER`

En el registro real los `TASK_INPUT` son `task.key`, que siempre llega en el comando, y
`repository.local`, `repository.match` y `refutation.repositoryMatch`, cuya fuente de verdad es `git
remote -v`. Ninguno se resuelve con un valor: los tres últimos se arreglan en el checkout y se
retoma. `ANSWER` queda implementado entero —gramática, intent, validaciones— y hoy responde
`HUMAN_ANSWER_NOT_ACCEPTED` a todo, con el camino que sí resuelve. La clave de Jira se declara como
en la Wave 3 («Seguimos con ABC-123»).

### Repositorio: elegir para esta tarea o cambiar el default

`CHOOSE` elige entre los candidatos que ya se observaron, para esta tarea. Cambiar el repositorio
por defecto es `GITLAB_PROJECT`, un `PERSISTENT_CONFIG_INPUT`: se muestra su lugar en el `.env` y no
se reescribe.

### La compuerta

Un comando de aplicación es `FLOW_RECOVERY` solo si PreToolUse encuentra, **en la sesión del
evento**, un intent sin consumir para esa tarea, esa interacción, esa acción y esa opción, y el
`--sesion` del comando es esa sesión. Si no, deny con el código. `--resume` es `FLOW_RECOVERY`.
Mientras la tarea espera, `Write`, `Edit`, `Agent` y todo lo que no se reconoce siguen en deny. El
Secret Guard sigue antes que la compuerta.

### La autoridad no se escribe con una herramienta

Que la tarea que espera esté bloqueada no alcanza: la sesión puede estar trabajando **otra** tarea, sana,
y la compuerta evalúa la de la sesión. Por eso, con estado del flujo en el proyecto, ninguna
herramienta que escribe toca `.claude/` ni `.git/`, enteros: ahí están la autoridad del flujo
(estado, bindings, intents, decisiones, plan, TaskContext, refutación) y lo que ejecuta código por su
cuenta (la CLI y los hooks instalados del Harness, los settings, `core.fsmonitor` y los hooks de
git). `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, y un `Bash`/`PowerShell` que no es de lectura y
nombra `.claude` o `.git`, son deny `FLOW_AUTHORITY_PROTECTED`, sea cual sea la tarea de la sesión.
Los escriben los hooks, la CLI del Harness y git, que no son herramientas del modelo; la CLI
reconocida pasa aunque nombre `.claude/`. Leerlos sí se puede, y `.gitignore` o `.github/` no son
`.git/`. Una propuesta para
`plan --propuesta` y un veredicto para `refute --record` se escriben fuera de `.claude/`, como ya
dicen `dev-orchestrator` y `docs/orquestacion.md`. Sin estado del flujo en el proyecto, nada cambia.

Para `Write`, `Edit`, `MultiEdit` y `NotebookEdit` la ruta se mira **normalizada**, no como texto:
contra el `cwd`, sin `.`, `..` ni barras dobles, sin los puntos y espacios finales que Windows ignora,
con los enlaces resueltos y sin distinguir mayúsculas. `.claude/./runtime` y `.claude./runtime` son
la misma carpeta.

### Con una decisión humana pendiente, el shell solo lee

Una regla sobre el texto de un comando de shell se evade sin ofuscar nada: `cd .claude && echo … >
runtime/…`, o un `Write` de un script y después `python` de ese script. Por eso, mientras **alguna**
tarea del proyecto espera una decisión humana —una aprobación o un conflicto de repositorio—, en
cualquier sesión `Bash` y `PowerShell` solo pasan si son de lectura o un comando del Harness
reconocido: lo `MUTATING` y lo `UNRESOLVED_TOOL_CLASS` es deny `FLOW_HUMAN_DECISION_PENDING`. `Write`
y `Edit` sobre archivos del código siguen pasando para una tarea sana. Es un falso positivo deliberado,
como `SESSION_TASK_AMBIGUOUS`: en un proyecto con varias tareas, mientras una espera a la persona, las
otras sesiones no corren comandos que no se reconocen. Resuelta la decisión, vuelve a pasar todo.

### El límite, escrito

El harness corre como el mismo usuario que el modelo: un modelo que puede escribir archivos y hacer
que algo los ejecute puede escribir lo mismo que un hook. Lo que esta Wave cierra es todo camino por
las herramientas que la compuerta ve dentro del proyecto. Queda afuera, y es de la Wave 5 (Fail-Closed
Hardening):

- **Persistencia plantada fuera del proyecto**: `~/.gitconfig` con un `core.fsmonitor`, un
  `usercustomize.py` o un `.pth` en el `site-packages` del usuario, un perfil de PowerShell. Un
  `git status` o la CLI del Harness la ejecutarían.
- **Persistencia plantada antes de que la decisión quede pendiente**, en un archivo que después
  ejecuta algo de lectura.
- **Fuera del modo pendiente**, un script ofuscado podría escribir una cancelación —que falla
  cerrada: la tarea deja de avanzar— o un plan armado a mano, un riesgo que ya existía desde la
  Wave 2.

Es el mismo *best-effort* que `permissions.deny` declara para el `.env`.

Un comando de shell es de lectura solo si cada programa está en la lista de lectura y ninguno usa una
opción que escribe: `sort -o`, `tree -o`, `uniq <entrada> <salida>`, `find -fprint*`/`-fls`,
`file -C`. Las opciones cortas se miran agrupadas y pegadas a su valor (`-uo`, `-o<ruta>`), y las largas
abreviadas (`--out=`), porque `getopt` las lee igual (E-66). Un programa de la lista con una forma de
escribir que no está anotada sería un hueco de esa lista, no de la regla.

Un comando del Harness con un flag repetido (dos `--sesion`) es `UNRESOLVED_TOOL_CLASS`: la
compuerta leería uno y la CLI otro. Consumir un intent toma un candado exclusivo: dos aplicaciones
a la vez no lo consumen dos veces; un candado de más de 60 s es de un proceso que murió y se reclama.

### Reinicio

El intent vive en la carpeta de su sesión. Una sesión nueva tiene otro `session_id`, así que no lo
ve. En la misma sesión (`--resume`), el intent sin consumir sigue valiendo solo si el estado y el plan
son los mismos. Un intent pendiente nunca se aplica solo: hace falta el comando de aplicación.

## Escenarios

Cada `E-nn` es el `W4-0nn` con el mismo número. De E-43 en adelante los pidió la implementación.

- **E-01** — `ANSWER` sobre un `PERSISTENT_CONFIG_INPUT` (`jira.token`): no crea intent ni
  decisión. `rojo visto`
- **E-02** — Un secreto no pasa por el prompt, argv ni el runtime: `HARNESS ANSWER` con un token
  sintético no se guarda en ningún archivo de `.claude/runtime/`, y `--value` con un token es
  rechazado. `rojo visto`
- **E-03** — Con `JIRA_TOKEN` cargado en el `.env`, `flujo --resume` reconcilia y la tarea deja
  `CONTEXT`/`BLOCKED`. `rojo visto`
- **E-04** — Con el `.env` todavía incompleto, `--resume` deja la tarea `BLOCKED`. `rojo visto`
- **E-05** — `--resume` no imprime ningún valor del `.env`. `rojo visto, por mutación`
- **E-06** — La clave de Jira es `TASK_INPUT` en el registro y se declara por el prompt; `ANSWER`
  sobre `task.key` no crea una segunda vía. `rojo visto`
- **E-07** — Un `ANSWER` sobre un `TASK_INPUT` de otra interacción no desbloquea: `HUMAN_INTENT_*`.
  `rojo visto`
- **E-08** — `CHOOSE` de un candidato resuelve `REPOSITORY_CONFLICT` para esa tarea y no cambia el
  `.env`. `rojo visto`
- **E-09** — `REPOSITORY_UNRESOLVED` (`GITLAB_PROJECT`) muestra el enlace al `.env`. `rojo visto, por mutación`
- **E-10** — `HARNESS APPROVE ABC-123 <id>` en `UserPromptSubmit` crea el intent. `rojo visto`
- **E-11** — «dale», «ok», «sí, aprobá», un comando en minúsculas o metido en un párrafo no crean
  intent. `rojo visto`
- **E-12** — `--approve` sin intent: `HUMAN_INTENT_REQUIRED`, el plan y el estado quedan igual, y
  PreToolUse lo niega. `rojo visto`
- **E-13** — `APPROVE` válido: la aprobación pasa a `APPROVED`, el intent queda consumido, y la tarea
  retoma. `rojo visto`
- **E-14** — El mismo intent otra vez: `HUMAN_INTENT_ALREADY_CONSUMED`. `rojo visto`
- **E-15** — Un intent sobre el plan A aplicado con el plan B: `HUMAN_DECISION_STALE`, y la tarea
  vuelve a esperar. `rojo visto`
- **E-16** — Un intent de ABC-123 aplicado a ABC-456: `HUMAN_INTENT_TASK_MISMATCH`. `rojo visto`
- **E-17** — Un intent de session-A aplicado desde session-B: `HUMAN_INTENT_SESSION_MISMATCH`.
  `rojo visto`
- **E-18** — `USE_ALTERNATIVE` solo con la opción declarada; otra: `HUMAN_OPTION_INVALID`.
  `rojo visto`
- **E-19** — `CANCEL` válido: `CANCELLED` y todos los permisos de avance en `false`. `rojo visto`
- **E-20** — `CANCEL` no borra el TaskContext, el plan, un artefacto de refutación ni el decision
  record.
  `rojo visto`
- **E-21** — Replanificar después de aprobar vuelve a pedir la aprobación. `rojo visto`
- **E-22** — Reinicio: con `state.json` borrado, la decisión se reconstruye. `rojo visto`
- **E-23** — Reinicio: un intent sin consumir no aprueba nada solo, y una sesión nueva no lo ve.
  `rojo visto, por mutación`
- **E-24** — El `interactionId` cambia si cambia el bloqueo o el plan. `rojo visto`
- **E-25** — Después de aprobar, la tarea retoma desde su `resumeFrom`. `rojo visto`
- **E-26** — Con dos aprobaciones pendientes, aprobar una no desbloquea: sigue esperando la otra.
  `rojo visto`
- **E-27** — Mientras espera, `Write` y `Agent` siguen en deny. `rojo visto, por mutación`
- **E-28** — Un secreto alto en un comando de aplicación sigue siendo deny del Secret Guard.
  `rojo visto, por mutación`
- **E-29** — `setup` y `reconfigurar` no leen de la consola. `rojo visto, por mutación`
- **E-30** — `active-task.json` nunca autoriza una decisión. `rojo visto`
- **E-31** — Dos sesiones: ninguna consume el intent de la otra. `rojo visto`
- **E-32** — Intent y decision record no guardan el prompt. `rojo visto`
- **E-33** — Intent y decision record no guardan secretos. `rojo visto, por mutación`
- **E-34** — La Wave 3 sigue verde (`63_compuerta_del_flujo`). `rojo visto: no consta`
- **E-35** — La Wave 2 sigue verde (`62_estado_del_flujo`). `rojo visto: no consta`
- **E-36** — La Wave 1 sigue verde (`61_flujo_precondiciones`). `rojo visto: no consta`
- **E-37** — Refutación atómica sigue verde (`55_refutacion_atomica`). `rojo visto: no consta`
- **E-38** — Entorno primero sigue verde (`60_entorno_primero`). `rojo visto: no consta`
- **E-39** — Context Bar sigue verde (`53_context_bar`). `rojo visto: no consta`
- **E-40** — Bloque 4 sigue verde (`30_b4_contabilidad`). `rojo visto: no consta`
- **E-41** — Reporte de seguridad sigue verde (`48_reporte_de_seguridad`). `rojo visto: no consta`
- **E-42** — La compuerta entera, `.\tests\Invoke-Tests.ps1`. `rojo visto: no consta`
- **E-43** — `UserPromptSubmit` muestra el `interactionId` y las acciones válidas de la tarea que
  espera. `rojo visto`
- **E-44** — PreToolUse: un comando de aplicación con un `--sesion` que no es el del evento es deny
  `HUMAN_INTENT_SESSION_MISMATCH`; con el intent de la sesión, pasa. `rojo visto`
- **E-45** — Intent y decision record validan contra sus schemas. `rojo visto`
- **E-46** — `CHOOSE` con un candidato que no está en la lista: `HUMAN_OPTION_INVALID`, sin
  decision record. `rojo visto`
- **E-47** — Los comandos de aplicación no salen a la red: con el transporte que falla, deciden
  igual. `rojo visto`

De E-48 en adelante salieron de la verificación.

- **E-48** — Con la sesión trabajando una tarea sana y otra esperando, escribir un intent, un decision
  record, el plan o el TaskContext con `Write`, `Edit`, `python -c`, `rm`, `cp` o `Set-Content` es
  deny `FLOW_AUTHORITY_PROTECTED`; leerlos pasa; sin estado del flujo, nada cambia. `rojo visto`
- **E-49** — Un comando de aplicación con dos `--sesion` es `UNRESOLVED_TOOL_CLASS` y deny.
  `rojo visto`
- **E-50** — Cuatro aplicaciones a la vez del mismo intent: una sola sale 0 y queda un solo decision
  record. `rojo visto: no consta` (pasó antes del candado: la carrera no se reprodujo)
- **E-51** — `ANSWER` sobre un input `SECRET`, o con un valor con forma de secreto, no se registra;
  sobre uno público sí, con su valor. `rojo visto`

De E-52 en adelante salieron de la segunda pasada de la verificación.

- **E-52** — Un `Write` con la ruta no normalizada (`./`, `//`, `x/..`, un punto final, mayúsculas,
  barras mezcladas, relativa) a la autoridad es deny `FLOW_AUTHORITY_PROTECTED`; un archivo del código
  sigue pasando. `rojo visto`
- **E-53** — Con ABC-123 esperando y la sesión en ABC-456 sana: `cd tmp && echo >`, `python
  tmp/forja.py`, `npm test`, `Set-Location tmp; Set-Content`, `echo >` son deny
  `FLOW_HUMAN_DECISION_PENDING` (las variantes que nombran `.claude` son de E-56); `git status`, `flujo --status` y un `Write` del código pasan;
  cancelada ABC-123, `npm test` vuelve a pasar. `rojo visto`
- **E-54** — Un candado de consumo fresco impide consumir; uno de más de 60 s se reclama y la
  decisión se aplica. `rojo visto`
- **E-55** — Las interacciones reales declaran su sensibilidad: `jira.token` es `SECRET`.
  `rojo visto`

E-56 salió de la tercera pasada: dos caminos dentro del modo pendiente, `core.fsmonitor` escrito en
`.git/config` y la CLI instalada reemplazada.

- **E-56** — Con estado del flujo, ninguna herramienta escribe en `.claude/**` ni `.git/**`
  (`.git/config`, un hook de git, la CLI y los hooks instalados, los settings, por `Write`, `Edit`,
  `echo >>`, `cd .claude &&` —también con el separador pegado: `cd .claude;`, `cd .claude&&`,
  `cd .git;`, `Set-Location .claude;`, y sin ninguna decisión pendiente— o `Set-Content`): deny
  `FLOW_AUTHORITY_PROTECTED`. `.gitignore`, `.github/`, `cat .git/config` y la CLI reconocida pasan.
  Sin estado del flujo, nada cambia. `rojo visto`

De E-57 en adelante salieron de la aceptación manual de la configuración persistente: el hook decía
`BLOCKED` y `flujo --status` decía `NEW`, y después de editar el `.env` hizo falta correr
`reconfigurar jira` a mano.

- **E-57** — Con `jira.token` pendiente, y con el `.env` ya editado pero sin retomar, el hook y
  `flujo --status` dicen lo mismo: `JIRA_NOT_CONFIGURED`, y que falta `--resume`; el hook, que el valor
  ya está cargado; el status, lo que daría revalidar. `rojo visto`
- **E-58** — Editar el `.env` y `--resume` revalidan Jira por `registrar_capacidades` (la sonda
  `myself`): el registro queda `AVAILABLE`, `jira.token` desaparece y la tarea queda `CONTEXT/NEW`, sin
  `reconfigurar` a mano. `rojo visto`
- **E-59** — Si la sonda da `CONNECTION_FAILED`, `jira.token` desaparece y la tarea sigue `BLOCKED`
  por `CONNECTION_FAILED`. `rojo visto`
- **E-60** — Con `jira.token` y `jira.user` pendientes, cargar solo el token y retomar deja
  `jira.user`. `rojo visto, por mutación`
- **E-61** — `--resume` no imprime el token ni lo deja en el runtime ni en el registro.
  `rojo visto, por mutación`
- **E-62** — Nada de lo que corre `--resume` apaga la verificación de certificados.
  `rojo visto, por mutación`
- **E-63** — `--resume` no lee de la consola. `rojo visto, por mutación`
- **E-64** — El bloque de un input persistente y `HARNESS RESUME` mandan a `flujo --resume`, nunca a
  `contexto`. `rojo visto`
- **E-65** — `--resume` sobre un bloqueo que no es de una integración (`REPOSITORY_MISMATCH`) no hace
  ninguna sonda: solo reconcilia. `rojo visto, por mutación`

E-66 salió de la sexta pasada de la verificación: `sort -uo` sobre el `human-intent.json` convirtió
una cancelación de la persona en una aprobación.

- **E-66** — Un programa de lectura que escribe no es de lectura: `sort -uo`, `sort -o<ruta>`,
  `sort --out=`, `uniq <entrada> <salida>`, `find -fprint0`, `tree -o` y `file -C` sobre `.claude/` o
  `.git/` son deny `FLOW_AUTHORITY_PROTECTED`, con una decisión pendiente y sin ella. Leer con esos
  mismos programas sigue pasando. `rojo visto`

E-67 en adelante salieron de la aceptación final: con el `.env` ya editado y sin retomar,
`--status --json` decía `NEW` sin bloqueos mientras la compuerta negaba.

- **E-67** — Con el estado guardado `CONTEXT / BLOCKED` por `jira.token` (`JIRA_NOT_CONFIGURED`), el
  `.env` ya con el valor y sin `--resume`: `flujo --status` dice `BLOCKED`, `flujo --status --json`
  dice `BLOCKED` con el mismo bloqueo y es el `state.json` tal cual, y la compuerta niega lo que
  escribe. Los tres coinciden; el JSON nunca dice `NEW` sin bloqueos mientras lo guardado está
  bloqueado. `rojo visto`
- **E-68** — `--status --json` es `task-flow-state/1.0` válido contra su schema. `rojo visto, por
  mutación`
- **E-69** — `--status --json` no revalida: ninguna llamada a una integración, el registro de
  capacidades y el `state.json` quedan iguales byte a byte, y el valor del `.env` no aparece.
  `rojo visto, por mutación`
- **E-70** — Después de `--resume`, `--status` y `--status --json` muestran el estado nuevo
  persistido: `jira.availability` / `CONNECTION_FAILED`, el mismo que el `state.json`. `rojo visto`
- **E-71** — Sin estado guardado, o con uno roto, `--status --json` sale con 2 y dice
  `TASK_FLOW_STATE_MISSING` o `TASK_FLOW_STATE_INVALID`, sin documento; `--status` en español lo dice
  y rotula lo derivado como no aplicado. `rojo visto`

## Cómo se verifica

Los tests viven en `tests/casos/64_interaccion_humana.py`, con el id del escenario en el título. Se
escriben antes que `flujo/interaccion.py`, `estado_de_tarea/decisiones.py` y `lib/human_intent.py`,
y se corren en rojo: 62 de 137 aserciones, en 31 escenarios. E-05, E-09, E-23, E-27, E-28, E-29 y
E-33 afirman algo que ya se cumplía (no imprimir valores, el enlace al `.env`, una sesión nueva sin
intent, la compuerta mientras espera, la prioridad del Secret Guard, `setup` sin consola, sin
secretos): pasaron en esa corrida, y su rojo es por mutación. E-34 a E-42 son archivos de la suite y
la compuerta entera. Verifica
`harness-spec-refuter`, que no es quien construyó. La aceptación manual en Claude Code (la
configuración persistente y la aprobación) se registra aparte.
