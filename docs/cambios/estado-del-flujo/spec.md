# Flow Governance, Wave 2 — el estado del flujo por tarea

**Estado:** verificado y cerrado · **Fecha:** 29-09-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Después de la Wave 1 el harness sabe decir, en el momento, si un plan está listo o si se puede
compilar la refutación. Lo que no puede decir es **en qué punto está una tarea**: no hay un lugar
que junte que el TaskContext existe, que el plan está `BLOCKED` por el repositorio, qué le falta a la
persona y desde qué compuerta se retoma. Cada comando vuelve a mirar sus artefactos y lo olvida.

Los hooks de la Wave 3 necesitan leer ese punto sin salir a la red ni recalcularlo todo en cada
turno. Esta Wave lo deja escrito, por tarea, como un **estado derivado**: no manda sobre nada, se
reconstruye de las fuentes que sí mandan, y si se borra se vuelve a armar igual.

## Qué queda afuera

- **Los hooks.** Nadie lee todavía el estado para frenar una herramienta: es la Wave 3.
- **Responder, aprobar, elegir una alternativa o cancelar** (`--answer`, `--approve`,
  `--alternative`, `--cancel`). Son la Wave 4. Por eso `CANCELLED` y `COMPLETED` existen en el
  contrato y ningún camino de esta Wave los produce: los decide una persona.
- **`VERIFICATION`.** Existe en el contrato y no se deriva: no hay hoy un artefacto que diga que la
  ejecución terminó y empezó la verificación. Inventarlo sería justo lo que el estado no puede hacer.
- **Tocar `refutacion.compilar`, `refutation-run/1.0`, `execution-summary/1.0` o la Context Bar.**
- **Los hallazgos diferidos de la Wave 1** (`AlmacenSecretos.set/remove`, `PlanInvalido` en `main`,
  el alcance de E-25 de la Context Bar, el stub de Python, el conteo de `CLAUDE.md`).
- **Una bitácora.** El estado es el de ahora; no guarda historia de transiciones.

## Las decisiones, y por qué

### Un archivo por tarea, y un puntero

`.claude/runtime/tasks/<KEY>/state.json`, con forma `comun/schemas/task-flow-state.schema.json`
(`task-flow-state/1.0`). No hay `.claude/runtime/task-state.json`: un singleton es una tarea que
pisa a otra. `.claude/runtime/active-task.json` es solo `{schema_version, taskKey}`, la última tarea
que reconcilió un comando; lo va a leer la Wave 3.

### Derivado, nunca autoridad

`estado.derivar(proyecto, clave)` arma el estado leyendo, en este orden:

```
TaskContext         .claude/contextos/<KEY>.json    su hash (hash_de de contexto-armar)
OrchestrationPlan   .claude/planes/<KEY>.json       su huella (refutacion.huella) y estado_de recalculado
identidad           flujo/repositorio.identidad     git remote -v, local
registro de inputs  flow-required-inputs.json       evaluado con flujo/precondiciones.evaluar
entorno             integraciones/entorno.resolver  solo en CONTEXT, de lectura
refutación          .claude/refutaciones/<KEY>/run.json   su planFingerprint y su status
```

Guarda referencias —ruta, hash, huella, estado— y nunca una copia: ni el título de la tarea, ni las
unidades del plan, ni un valor del `.env`. Si `state.json` no está, `derivar` da el mismo estado
lógico. Si no hay ningún artefacto, la tarea es `CONTEXT`: `NEW` si lo que pide esa etapa está en el
`.env`, `BLOCKED` si no. Nunca lista.

### Etapa y estado son dos cosas

| stage | cuándo |
|---|---|
| `CONTEXT` | no hay TaskContext |
| `PLANNING` | hay TaskContext y no hay plan listo, o una compuerta de planificación bloquea |
| `EXECUTION` | el plan está `READY_FOR_EXECUTION` y el repositorio coincide |
| `VERIFICATION` | reservado |
| `REFUTATION` | hay una corrida de refutación sobre este plan, o una vieja |
| `COMPLETION` | la corrida sobre este plan dio `PASS` o `NOTHING_TO_VERIFY` |

| status | cuándo |
|---|---|
| `NEW` | `CONTEXT` sin nada que bloquee |
| `ACTIVE` | se puede avanzar en la etapa |
| `BLOCKED` | hay al menos un bloqueo que no es solo una aprobación |
| `WAITING_FOR_HUMAN_APPROVAL` | el único bloqueo es una aprobación pendiente del plan |
| `INCOMPLETE` | la corrida dio `INCOMPLETE` |
| `FAILED` | la corrida dio `FAIL` |
| `COMPLETED`, `CANCELLED` | reservados a una decisión humana (Wave 4) |

`READY_FOR_EXECUTION` sigue siendo del plan: el estado lo referencia en `planRef.planStatus`.

### Las compuertas se reevalúan con lo de ahora

Las compuertas de planificación no se copian del plan: se vuelven a evaluar con `evaluar(PLANNING)`
y los hechos de hoy —la identidad recalculada, el TaskContext presente, el ruteo de las unidades del
plan—. Si el repositorio se arregló después de planificar, el bloqueo de repositorio desaparece y
queda `PLAN_NOT_READY`: el plan escrito sigue diciendo `BLOCKED` y hay que regenerarlo. El estado no
salta a `EXECUTION` sin un plan listo.

Bloqueos que no vienen del registro, con el código que ya existía:

| código | inputId | fuente | compuerta |
|---|---|---|---|
| `CONTEXT_STALE` | `planning.taskContext` | `task-flow-state` | `PLANNING` / `planning-task-context` |
| `CAPABILITY_GAP` | `plan.capabilityGaps` | `orchestration-plan` | `PLANNING` / `plan-capability-gaps` |
| `HUMAN_APPROVAL_PENDING` | `plan.humanApprovals` | `orchestration-plan` | `PLANNING` / `plan-human-approvals` |
| `PLAN_NOT_READY` | `plan.status` | `orchestration-plan` | `PLANNING` / `plan-status` |
| `REFUTATION_PLAN_STALE` | `refutation.compile` | `atomic-refutation` | `REFUTATION` / `refutation-compile` |
| `REFUTATION_OUTPUT_INVALID` | `refutation.compile` | `atomic-refutation` | `REFUTATION` / `refutation-compile` |

Un artefacto que está y no se lee no es un artefacto ausente: un TaskContext roto da
`TASK_CONTEXT_MISSING` (el `failureCode` de `planning.taskContext`), un plan roto `PLAN_NOT_READY`
y un `run.json` roto `REFUTATION_OUTPUT_INVALID`.

`EXECUTION` pide un plan listo **por los dos lados**: el `status` escrito y el que da `estado_de`.
Si alguno no lo es, o el plan no cuadra con la identidad de hoy (`PLAN_STALE`,
`REPOSITORY_STATE_STALE`), y las compuertas de hoy no explican por qué, el bloqueo es
`PLAN_NOT_READY`. Y cualquier `stale` deja los permisos de avance en `false`.

Los del registro llevan `source: flow-preconditions`, su clasificación y la compuerta que sale de su
`inputId` en kebab-case (`repository.match` → `repository-match`). No se agrega un campo al registro:
`flow-required-inputs/1.0` cierra sus claves. `blockerId` es `FLOW-<STAGE>-<NNN>`, en el orden
canónico (etapa, inputId, código). `resumeFrom` del estado es el del primer bloqueo.

### Lo que se guarda de una interacción pendiente

La primera interacción humana en ese orden, con `kind`, `inputId` y, si es un
`PERSISTENT_CONFIG_INPUT`, `target`, `key` y `sensitivity` (de `entrada_humana.sensibilidad`, que
lee el contrato de entorno). Ni valor, ni línea, ni columna, ni enlace: la posición se recalcula con
`entrada_humana.localizar` cada vez que se muestra, porque el archivo puede haber cambiado.

### Los permisos no se guardan

`estado.permisos(estado, vigencia)` es pura. Con `BLOCKED`, `WAITING_FOR_HUMAN_APPROVAL`, un estado
guardado desactualizado o uno inválido, los cinco permisos de avance son `false` y solo quedan las
operaciones de recuperación: `inspectState`, `renderPendingInteraction`, `locatePersistentInput`,
`validate`, `revalidate`, `cancel`.

### Las transiciones no se declaran

`estado.validar_transicion(anterior, nuevo, revalidado)` levanta `FLOW_TRANSITION_INVALID` si un
estado terminal cambia, si un cambio que no sale de reevaluar la autoridad no es una cancelación, si
un estado bloqueado llega sin bloqueos, o si uno que no está bloqueado llega con bloqueos.
`reconciliar` es el único camino que escribe, y pasa por ahí.

### Lo desactualizado tiene nombre

En `stale`, lo que no cuadra **entre artefactos**: `TASK_CONTEXT_STALE` (el plan se hizo sobre otro
TaskContext), `PLAN_STALE` (el plan dice un estado que `estado_de` ya no da), `REPOSITORY_STATE_STALE`
(la identidad de hoy no es la del plan) y `REFUTATION_STATE_STALE` (la corrida es de otro plan).
`estado.vigencia(guardado, derivado)` compara el guardado con lo de ahora y da los mismos cuatro
códigos, más `TASK_FLOW_STATE_MISSING` y `TASK_FLOW_STATE_INVALID`.

### Escribir sin dejar medio archivo, y afuera de `flujo/`

`flujo/` no abre nada para escribir: es E-18 de la Wave 1, y se conserva. La derivación vive en
`flujo/estado.py`; la escritura, en `bin/estado_de_tarea/persistencia.py`.


Serializar, escribir a un temporal en la misma carpeta, `flush`, `fsync`, `os.replace`. Un JSON que no
se parsea o no valida es `TASK_FLOW_STATE_INVALID`: no se usa, se dice, y la próxima reconciliación lo
reemplaza con uno derivado. Un estado lógicamente igual no se reescribe, así `updatedAt` es la última
vez que cambió algo.

### Dónde se reconcilia

Después de `contexto`, de `plan`, de `refute --compile` —pase o no la compuerta— y de `refute --record`.
Una falla al reconciliar se avisa y no voltea el comando: el estado es derivado y el comando ya aplicó
sus propias compuertas. `dev-harness.py flujo <KEY> --status` muestra el estado derivado de ahora y cómo
está el guardado; no escribe, no sale a la red y no llama a ningún modelo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/task-flow-state.schema.json` | `task-flow-state/1.0` y, en `$defs`, `activeTask` |
| `harnesses/desarrollo/bin/flujo/estado.py` | derivar, leer, validar, vigencia, permisos, transiciones, texto. No escribe |
| `harnesses/desarrollo/bin/estado_de_tarea/persistencia.py` | escribir, reconciliar y el puntero a la tarea activa |
| `harnesses/desarrollo/bin/dev-harness.py` | `flujo <KEY> --status`; reconcilia en `contexto`, `plan` y `refute` |
| `tests/casos/62_estado_del_flujo.py` | Los escenarios de esta spec |

## Escenarios verificables

`E-nn` es `W2-0nn` de la Wave.

### Un estado por tarea

- **E-01** — Dos tareas planificadas en el mismo proyecto dejan dos `state.json` en
  `.claude/runtime/tasks/<KEY>/`, cada uno con su `taskKey` y sus referencias. · rojo visto: si
- **E-02** — Después de `contexto`, `plan` y `refute` no existe `.claude/runtime/task-state.json`, y
  ningún fuente de `bin/` lo nombra. · rojo visto: si
- **E-03** — `active-task.json` tiene exactamente `schema_version` y `taskKey`. · rojo visto: si
- **E-04** — Borrado `state.json`, `derivar` da el mismo estado lógico (salvo `updatedAt`). Sin
  ningún artefacto la etapa es `CONTEXT`, nunca una posterior: `NEW` con Jira configurado en el
  `.env`, `BLOCKED` sin él. · rojo visto: si
- **E-05** — El estado no contiene el título, los criterios ni la Ficha del TaskContext. · rojo visto: si
- **E-06** — El estado no contiene el objetivo ni las unidades del plan. · rojo visto: si
- **E-07** — El estado de un proyecto con tokens, base URL y usuario en el `.env` no contiene ninguno de
  esos valores. · rojo visto: si
- **E-08** — Con `JIRA_TOKEN` faltante, la interacción pendiente es `PERSISTENT_CONFIG_INPUT`
  `jira.token` en `.env` con `SECRET`, y el estado no tiene `value`, `rawLine`, `line`, `column` ni
  `vscodeUri`. · rojo visto: si

### Permisos y transiciones

- **E-09** — Con `BLOCKED`, los cinco permisos de avance son `false` y quedan las seis operaciones
  de recuperación. · rojo visto: si
- **E-10** — Lo mismo con `WAITING_FOR_HUMAN_APPROVAL`. · rojo visto: si
- **E-11** — `BLOCKED` en `PLANNING` a `ACTIVE` en `EXECUTION` sin reevaluar es
  `FLOW_TRANSITION_INVALID`, y también un `ACTIVE` con bloqueos. · rojo visto: si
- **E-12** — Con el checkout arreglado, reconciliar reevalúa la compuerta de repositorio: el bloqueo
  `REPOSITORY_MISMATCH` desaparece, queda `PLAN_NOT_READY` y no se llega a `EXECUTION` hasta volver a
  planificar; después, `EXECUTION` / `ACTIVE`. · rojo visto: si
- **E-13** — Sin arreglarlo, reconciliar deja el mismo bloqueo y `BLOCKED`. · rojo visto: si
- **E-14** — Cada `resumeFrom` es `{stage, gate}` con una compuerta del conjunto canónico. · rojo visto: si

### Lo desactualizado

- **E-15** — Cambiado el TaskContext después de planificar: `vigencia` da `TASK_CONTEXT_STALE`, y el
  estado derivado lo lleva en `stale` con un bloqueo `CONTEXT_STALE`. · rojo visto: si
- **E-16** — Reescrito el plan: `vigencia` da `PLAN_STALE`. · rojo visto: si
- **E-17** — Cambiado el remoto del checkout: `vigencia` da `REPOSITORY_STATE_STALE`. · rojo visto: si
- **E-18** — Una corrida compilada sobre otro plan: `REFUTATION_STATE_STALE` en `stale` y un bloqueo
  `REFUTATION_PLAN_STALE`. · rojo visto: si
- **E-19** — Un `state.json` roto da `TASK_FLOW_STATE_INVALID`, con los permisos de avance en `false`,
  y `flujo --status` lo dice. · rojo visto: si
- **E-19b** — Un TaskContext, un plan o un `run.json` que están y no se leen bloquean con
  `TASK_CONTEXT_MISSING`, `PLAN_NOT_READY` o `REFUTATION_OUTPUT_INVALID`: no se leen como ausentes,
  tampoco un `run.json` roto sin plan ni un plan que es `{}`. · rojo visto: si
- **E-20** — Una escritura que falla a mitad de camino deja el `state.json` anterior entero y sin
  temporales. · rojo visto: si

### En los comandos

- **E-21** — `contexto` deja el estado en `PLANNING` con su `contextRef`. · rojo visto: si
- **E-22** — Un plan `BLOCKED` por el repositorio deja la tarea `BLOCKED` con `REPOSITORY_MISMATCH`. · rojo visto: si
- **E-23** — Un plan `READY_FOR_EXECUTION` deja la tarea `EXECUTION` / `ACTIVE`, sin bloqueos. · rojo visto: si
- **E-23b** — Un plan cuyo `status` escrito no es `READY_FOR_EXECUTION` no deja la tarea en
  `EXECUTION` aunque su contenido recalcule listo, y un `stale` entre artefactos deja los permisos
  de avance en `false`. · rojo visto: si
- **E-24** — Una compuerta de refutación que falla no crea `run.json` y deja el estado con el bloqueo
  que explica la falla. · rojo visto: si
- **E-25** — `flujo --status` no abre ningún socket ni llama al transporte. · rojo visto: si
- **E-25b** — `flujo --status` no cambia ningún archivo, con el estado guardado, sin él y sin
  artefactos, y sin `state.json` dice `TASK_FLOW_STATE_MISSING`. · rojo visto: si
- **E-25c** — Reconciliar sin cambios deja el mismo `state.json`, con su `updatedAt` y su mtime. · rojo visto: si
- **E-25d** — `refute --compile` que pasa y `refute --record` dejan el estado con su
  `refutationRef`. · rojo visto: si
- **E-25e** — Si el estado no se puede guardar, `plan` sale igual con 0, escribe el plan y avisa. · rojo visto: si
- **E-26** — `bin/flujo/` no importa ningún cliente de modelo ni de HTTP. · rojo visto: si
- **E-27** — El libro del Bloque 4 no cambia el estado derivado, y `flujo/` no importa `contabilidad`. · rojo visto: si

### Lo que no cambia

- **E-28** — `61_flujo_precondiciones` sigue verde. · rojo visto: no consta
- **E-29** — `55_refutacion_atomica` sigue verde. · rojo visto: no consta
- **E-30** — `53_context_bar` sigue verde. · rojo visto: no consta
- **E-31** — `60_entorno_primero` sigue verde. · rojo visto: no consta
- **E-32** — `.\tests\Invoke-Tests.ps1` sale en verde. · rojo visto: no consta

## Cómo se verifica

E-01 a E-27 en `tests/casos/62_estado_del_flujo.py`, contra la CLI real y repositorios git
temporales con remotos que no existen. E-21 usa el Jira falso de `19_contexto.py`. E-28 a E-31 son
esos archivos de la suite; E-32 es la corrida entera. Ninguno se lee: no hay un modelo en el camino.

De dónde sale cada `rojo visto: si`, porque no todos salen del mismo lugar:

- **E-01 a E-27:** los tests se escribieron antes que `estado.py` y `persistencia.py` y se corrieron
  en rojo: 20/65 aserciones, con al menos una falla por escenario. La verificación lo reprodujo
  poniendo el archivo de tests sobre `4a18ddc`. Después, trece mutaciones de la lógica dieron rojo
  en su escenario.
- **E-19b y E-23b:** salieron de la verificación. Se escribieron antes del arreglo y se vieron fallar.
- **E-25b a E-25e:** describen conducta que ya existía y pasaron en la primera corrida. Su rojo es
  **por mutación**: rompiendo el código a propósito, cada una falla.

## Riesgos conocidos

- **La reconciliación agrega costo a los comandos:** un `git remote -v` y una lectura del `.env`.
- **`active-task.json` es la última tarea tocada**, no una elección. Con dos sesiones sobre dos tareas
  en el mismo proyecto, gana la última; la Wave 3 decide cómo se usa.
- **Un estado derivado puede atrasar** si alguien cambia un artefacto a mano: por eso existe
  `vigencia`, y por eso los permisos caen a `false` si el guardado no está vigente.
- **`refutacion.compilar` como biblioteca** sigue sin compuerta ni reconciliación.
