# Integración de Flow Governance con 0.30.0, y `orchestration-plan/2.1`

**Estado:** verificado y cerrado (0.31.0) · **Fecha:** 07-10-2026 · **Versión de partida:** 0.30.0 (`0f8b725`) más
`integration/flow-governance-0.28` (`ea2dff7`)

Las rutas sin prefijo son relativas a la raíz del repo; `bin/` abrevia `harnesses/desarrollo/bin/`.

---

## Qué problema resuelve

Flow Governance (Waves 1 a 6 y la Qualification Gate 1) se construyó sobre 0.28.0. Mientras tanto,
`main` publicó 0.29.0 («un solo harness») y 0.30.0 («modelo de dominio canónico»). El merge de
`origin/main` sobre la integración deja seis conflictos de texto y tres choques que git no marca:

1. **El contrato del plan.** 0.30.0 redujo `orchestration-plan` a 2.0: tres estados de plan
   (`CAPABILITY_RESOLUTION`, `WAITING_FOR_HUMAN_APPROVAL`, `READY_FOR_EXECUTION`) y la unidad sin
   `blockers`. Flow Governance escribe el plan en `BLOCKED` cuando falta una precondición del flujo
   y le pone `blockers` a la unidad cuyo agente no se rutea. Con el schema de `main`, el plan de una
   precondición faltante no valida y `plan` no lo escribe.
2. **`-Harness` ya no existe.** 0.29.0 sacó el parámetro. Los casos de la Qualification Gate 1 lo
   seguían pasando con `analisis`.
3. **El número de versión.** La rama local se llamaba 0.29.0, que ya es otra versión publicada.

Además, la compuerta del flujo deduce `agents.routing` de «alguna unidad tiene `blockers`». Hoy
solo los lleva la unidad no ruteable; si una unidad bloqueada por capacidad los llevara, la
compuerta diría que un agente no se rutea cuando lo que falta es una capacidad.

## Qué queda afuera

- **Los doce estados de las Waves en el plan.** Describen el estado persistido de la tarea
  (`task-flow-state`), no un documento de plan. 0.30.0 los sacó a propósito (D4 de
  `canonical-domain-model`), y volver a ponerlos sería agrandar el contrato público por inercia.
- **Bloquear las unidades por una precondición del plan entero.** Un repositorio sin resolver o un
  input `HARD_BLOCKER` de la tarea no es de una unidad: queda en `flowPreconditions`, que es donde
  lo lee la compuerta. Marcar todas las unidades `BLOCKED` cambiaría la semántica calificada en las
  Waves (las unidades siguen `PENDING` y el plan `BLOCKED`).
- **Reclasificar inputs del registro.** `agents.routing` es `DERIVABLE` en
  `reglas/flow-required-inputs.json` y sigue así. Este cambio no toca clasificaciones.
- **Sacar el marcador interno `PLANNING` de `plan.armar`.** Se pisa antes de devolver el
  documento y nunca llega a uno escrito (D4 de `canonical-domain-model`). Sacarlo no evita ningún
  artefacto inválido.
- **Cerrar 0.31.0 e incorporar R11.** Son pasos siguientes de la misma integración, con su propio
  ritual (`close-a-version`). Esta spec cubre el merge y el contrato.

## Las decisiones, y por qué

### D1. `orchestration-plan/2.1`, no 3.0 ni 2.0 agrandado

Agregar `BLOCKED` al enum del plan y `blockers` opcional a la unidad es aditivo: todo documento 2.0
válido sigue validando bajo 2.1, salvo la cadena de versión. Es el criterio escrito del repo
(D16 de `canonical-domain-model`, que cita `project-context/1.1`): aditivo sube la menor. Agrandar
2.0 sin subir la cadena es el «enum más flojo» que ese mismo precedente descarta.

### D2. El estado público del plan es uno, el estado detallado de la tarea es otro

`plan.py` escribe solo `ESTADOS_DEL_PLAN` (cuatro) y `ESTADOS_DE_UNIDAD` (tres). Los estados y
etapas finos (`NEW`, `ACTIVE`, `PLANNING`, `INCOMPLETE`…) viven en `task-flow-state`, y la causa
detallada de un bloqueo llega ahí por la compuerta del flujo, no por el plan.

La invariante:

```text
precondición requerida faltante
→ plan.status = BLOCKED, con la causa en flowPreconditions, capabilityStatus,
  knowledgeSources o en los blockers de la unidad afectada
→ task-flow-state BLOCKED, con el código y la clasificación del registro
→ la compuerta no deja pasar a EXECUTION
```

### D3. `blockers` es opcional en el schema y obligatorio en el código

Lo pedido es «opcional en una unidad normal, obligatorio y no vacío si la unidad está `BLOCKED`».
El validador del harness (`comun/bin/contexto-armar.py`) entiende `type`, `properties`, `required`,
`items`, `enum`, `pattern`, `additionalProperties`, `$ref` y `minimum`, y rechaza el resto. No hay
`if/then` ni `minItems`, así que la condición no entra limpia en el schema.

Se reparte así:

- **El schema** declara `blockers` opcional, con la forma de cada ítem, y dice la condición en la
  descripción.
- **El productor** (`plan.armar`) pone `blockers` en toda unidad `BLOCKED`, sea cual sea la causa:
  agente no ruteable (`agents.routing`), capacidad no soportada (`plan.capabilityGaps`,
  `CAPABILITY_GAP`) o soportada y no disponible (`plan.capabilityStatus`, `CAPABILITY_UNAVAILABLE`).
  Una unidad que no está `BLOCKED` no los lleva.
- **La regla de lectura** (`plan.aceptar_guardado`) rechaza un plan **2.1** con una unidad
  `BLOCKED` sin `blockers` o con `blockers` vacío. Un 2.0 o un 1.0 no se rechaza por eso: la
  exigencia es de 2.1.

Lo que se descartó: agregar `if/then` al validador. Es tocar la pieza que valida todos los
contratos del harness para expresar una sola condición, y la regla de lectura ya existe para eso.

### D4. `agents.routing` se lee de los `blockers` de ruteo, no de cualquiera

Con `blockers` en las unidades bloqueadas por capacidad, «alguna unidad tiene `blockers`» deja de
significar «un agente no se rutea». `plan._precondiciones` y `flujo/estado.py` pasan a mirar solo los
`blockers` con `inputId: agents.routing`.

### D5. La regla de lectura acepta `BLOCKED` en un plan guardado de cualquier versión legible

Los planes 1.0 que escribió Flow Governance antes de la integración pueden tener
`status: BLOCKED`, que en 2.1 existe. Se leen como se lee un 1.0 en 0.30.0: tal cual, y pasan a 2.1
cuando se reescriben. `DELEGATING` o `READY` siguen rechazándose.

Leer no es compilar. Después de la regla de lectura, `refute --compile` pasa por la compuerta del
flujo, que exige `flowPreconditions` resueltas: un 2.0 escrito por 0.30.0, o un 1.0 sin ellas, sale
con 2 y `PLAN_NOT_READY`. Es la semántica calificada de las Waves y no se afloja: se resuelve con
`plan --replanificar`. Por eso los tests de 0.30.0 que compilaban un plan guardado (E-16, E-16b,
E-16c y E-45 de `canonical-domain-model`) le agregan las precondiciones reales del proyecto antes de
compilar; lo que siguen afirmando es la lectura, no que un plan sin precondiciones esté listo.

### D8. Reescribir un plan guardado lo pasa a 2.1, por la misma regla de lectura

Tres caminos reescriben un plan que ya está en disco: `--replanificar`, `refute --compile` (que lo
lee) y una decisión humana (`flujo --approve` o `--alternative`, que lo replanifica). Los tres leen
por `plan.aceptar_guardado`. `refute --compile` la aplica antes de la compuerta, que escribe el
estado derivado de la tarea: un plan con un estado retirado sale nombrando el campo y no deja nada
escrito. Un plan que falta o no se lee sigue siendo asunto de la compuerta.

`plan.replanificar` migra lo que reescribe: la cadena de versión pasa a 2.1, y una unidad `BLOCKED`
que no traía `blockers` los recibe derivados del contenido, como se deriva el estado (el ruteo del
registro de hoy y sus capacidades faltantes). Si el contenido no dice por qué está bloqueada, se
rechaza y se pide regenerar. Lo encontró el refutador: una decisión sobre un 2.0 o un 1.0 caía al
escribir, porque `escribir` valida contra 2.1 y `replanificar` dejaba la versión vieja.

Lo que se descartó: dejar que `escribir` acepte 2.0 y 1.0. Es el «enum más flojo» que D16 de
`canonical-domain-model` descarta.

### D9. Lo que esta integración pisa de 0.30.0 y de harness-unico

Los tests de esas dos versiones suponían un mundo sin Flow Governance. Lo que cambia, y por qué:

| Test | Qué afirmaba | Qué afirma ahora | Por qué |
|---|---|---|---|
| canonical E-13, E-15, E-16, E-17, E-24, E-45, E-47 | `orchestration-plan/2.0`, tres estados | 2.1, cuatro estados | D1 |
| canonical E-02 S5, E-21 y los planes armados en los tests | Un plan sin precondiciones podía estar listo | Los fixtures traen un repositorio `MATCHED` y precondiciones resueltas; la precedencia empieza por `BLOCKED` | La semántica de las Waves (`flujo-precondiciones`), como ya hizo `20_orquestacion.py` |
| canonical E-16, E-16b, E-16c, E-45 | Un plan guardado compila tal cual | Compila después de recibir las precondiciones reales | D5 |
| canonical E-16b | El código no nombra `READY` | `READY` se admite solo como estado de `flowPreconditions` | Es otro contrato: el de las precondiciones, no el del plan |
| canonical E-17 | El plan es igual al de `4c6f0f3`, salvo fechas | Igual, salvo los campos que suma Flow Governance, que se afirman uno por uno | `flowPreconditions`, `capabilityStatus`, `knowledgeSources` y el repositorio de la unidad son de las Waves |
| canonical E-18b | Un ciclo sale con 1 | Sale con 2 | D6, E-18 |
| canonical E-22 | Dos módulos arman la ruta de `.claude/planes/` | Cinco, más `exigir_plan_vigente` | Las Waves leen el plan desde el flujo, las decisiones y las precondiciones |
| canonical E-23 | `dev-iniciador-code` es un agente sin registrar | El huérfano es uno sembrado en una copia de la fábrica; `dev-iniciador-code` está registrado | La Wave 6 lo registró |
| canonical E-41 | Todo subprocess lanza git o markitdown | También `taskkill`, solo desde `flujo/repositorio.py` | La Wave 3 mata el árbol de `git remote -v` al vencer su límite |
| canonical E-05 | 46 schemas | 52 | D7 |
| harness-unico (los dos archivos) | La base es `e5d7a14` | La base es `ea2dff7`: 282 archivos instalados, 11 agentes, 2 huérfanos; `flujo/estado.py`, `estado_de_tarea/decisiones.py` y `tool_policy.py` entre las excepciones de E-16 | La línea parte de 0.28.0 con Flow Governance; D4, D8 y R11 tocan esos tres archivos |

Cada test pisado cita esta spec en un comentario al lado de su id original.

### D6. Las resoluciones del merge

| Archivo | Qué queda |
|---|---|
| `CLAUDE.md` | La frase de las Waves («every case passing»): una cuenta fija envejece con el primer test nuevo |
| `comun/hooks/lib/bienvenida.py` | La versión de `main`: sin `_sin_desarrollo`, no hay proyecto sin `desarrollo` |
| `install.ps1` | La Context Bar de `-Doctor` como la calculan las Waves (`Get-BarraDelDoctor`), sin la condición `desarrollo` |
| `tests/casos/03-instalador.ps1` | La copia aislada de la fábrica (`-Desde`), sin `-Harness analisis` |
| `tests/casos/69-instalador-sin-consola.ps1` | Los tres usos de `-Harness analisis` se van |
| `bin/dev-harness.py` | Se juntan las excepciones: las de las Waves, `PlanInvalido` (incluye a `PlanRechazado`) y `ClaveDeLibroInvalida`, todas con 2 |

`PlanInvalido` con 2 es lo que calificó la Wave 6. Incluye a `PlanRechazado`, así que lo que
`main` prometía con 2 sigue saliendo con 2.

### D7. Los seis schemas de Flow Governance en el modelo canónico

E-05 de `canonical-domain-model` exige que cada archivo de `comun/schemas/` figure en la
Persistencia y contrato de un concepto de `docs/dominio/modelo-canonico.md`. 0.30.0 lo cumplió con
los 46 de `main`, y Flow Governance suma seis. La spec de 0.30.0 está cerrada y no se edita: la
tabla de abajo extiende su tabla 3.2, con las mismas columnas, y los tests de E-05 leen las dos.

Un concepto por schema. HumanIntent y HumanDecisionRecord parecen uno y no lo son: la intención es
de una sesión, se pisa con la siguiente y se consume una vez, sin haberse aplicado; el registro es de
una Task y una interacción, y existe recién cuando la decisión se aplicó. SessionTaskBinding y
SessionFlowNotice comparten la carpeta de la sesión, pero el primero decide qué Task mira la
compuerta y el segundo solo recuerda qué se mostró.

Los contextos salen de los nueve:

- **Planning** para FlowRequiredInput, TaskFlowState, HumanIntent y HumanDecisionRecord. D2 separa
  el estado del flujo del estado del Plan, pero los dos responden qué frena la Task: los inputs se
  evalúan en las `flowPreconditions` del Plan, y las decisiones resuelven sus aprobaciones.
- **Work Intake** para SessionTaskBinding: su único dato es la TaskKey que declaró la persona.
- **Guardrails** para SessionFlowNotice: es la memoria de un aviso de los hooks.

Lo que queda abierto: por el criterio del mapa de contextos -lenguaje, invariantes, dueño, datos y
ciclo de vida-, el flujo podría ser un contexto propio. ADR-0013 fija nueve, y abrir un décimo es
una decisión de ADR, no de esta integración.

| Schema | Concepto | Productor | Runtime | Persistencia | Clase |
|---|---|---|---|---|---|
| `flow-required-inputs` | FlowRequiredInput | la fábrica | sí, al cargar | `reglas/` | Domain Policy |
| `human-decision-record` | HumanDecisionRecord | `estado_de_tarea/decisiones.aplicar`, desde `flujo` | versión | `.claude/runtime/tasks/<KEY>/decisions/<interactionId>.json` | Record |
| `human-intent` | HumanIntent | `human_intent.registrar`, en UserPromptSubmit | un validador propio | `.claude/runtime/sessions/<SAFE>/human-intent.json` | Entity |
| `session-flow-notice` | SessionFlowNotice | `flow_context.del_turno`, en UserPromptSubmit | versión | `.claude/runtime/sessions/<SAFE>/notice.json` | Infrastructure |
| `session-task-binding` | SessionTaskBinding | `task_binding.escribir`, en UserPromptSubmit y PreToolUse | un validador propio | `.claude/runtime/sessions/<SAFE>/task.json` | Entity |
| `task-flow-state` | TaskFlowState | `estado_de_tarea/persistencia.reconciliar` | sí, al escribir y al leer | `.claude/runtime/tasks/<KEY>/state.json` | Snapshot |

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/orchestration-plan.schema.json` | `$id` y `meta.schema_version` 2.1; `BLOCKED` en el estado del plan; `blockers` opcional en la unidad |
| `bin/orquestacion/plan.py` | Escribe 2.1; `blockers` en toda unidad `BLOCKED`; lee 2.1, 2.0 y 1.0; rechaza un 2.1 con una unidad `BLOCKED` sin `blockers`; `agents.routing` solo de los `blockers` de ruteo |
| `bin/flujo/estado.py` | `agents.routing` solo de los `blockers` de ruteo |
| `bin/orquestacion/refutacion.py` | `compilar` aplica la regla de lectura antes de la compuerta (D8) |
| `bin/estado_de_tarea/decisiones.py` | Una decisión lee el plan por la regla de lectura (D8) |
| `plan.replanificar` | Migra a 2.1 lo que reescribe, con los `blockers` derivados (D8) |
| Las seis resoluciones de D6 | El merge |
| `docs/dominio/modelo-canonico.md`, `docs/orquestacion.md` | Dicen 2.1, `BLOCKED` y `blockers` |
| `docs/dominio/modelo-canonico.md` | Los seis conceptos de D7, con su fila en el catálogo, en el mapa de contextos y en el vocabulario. ModelTierApproval dice que `flujo` la resuelve |
| `tests/casos/` | Los tests de este cambio, y los de 0.30.0 que fijaban 2.0 pasados a 2.1. E-05 de 0.30.0 cuenta 52 schemas y lee la tabla de 3.2 más la de D7 |

## Escenarios verificables

### El contrato

- **E-01** — El schema se identifica como `orchestration-plan/2.1` en `$id` y en el enum de
  `meta.schema_version`, que no acepta otro valor; `plan --propuesta` escribe 2.1.
  · rojo visto: si
- **E-02** — El `status` del plan en el schema es exactamente `BLOCKED`, `CAPABILITY_RESOLUTION`,
  `WAITING_FOR_HUMAN_APPROVAL` y `READY_FOR_EXECUTION`. Ninguno de `RECEIVED`, `ANALYZING`,
  `PLANNING`, `WAITING_FOR_TOOL`, `READY_FOR_DELEGATION`, `DELEGATING`, `REPLANNING` ni `FAILED`
  está. · rojo visto: si
- **E-03** — El `status` de una unidad es exactamente `PENDING`, `BLOCKED` y
  `WAITING_FOR_HUMAN_APPROVAL`. · rojo visto: si
- **E-04** — `blockers` es opcional en el schema: una unidad sin el campo valida. Con el campo, cada
  ítem exige `inputId` y `code`, no admite otras claves, y un `code` en minúsculas no valida.
  · rojo visto: si
- **E-05** — Un documento 2.0 escrito por 0.30.0, con la cadena de versión cambiada a 2.1, valida
  contra el schema 2.1. · rojo visto: si

### Lo que escribe `plan`

- **E-06** — Toda unidad que `plan.armar` deja en `BLOCKED` lleva `blockers` no vacío: agente no
  ruteable → `agents.routing` con el resultado del registro; capacidad no soportada →
  `plan.capabilityGaps` / `CAPABILITY_GAP`; capacidad soportada y no disponible →
  `plan.capabilityStatus` / `CAPABILITY_UNAVAILABLE`. Una unidad `PENDING` o
  `WAITING_FOR_HUMAN_APPROVAL` no lleva `blockers`. · rojo visto: si
- **E-07** — Sin precondiciones evaluadas, o con una pregunta bloqueante en `flowPreconditions`, el
  plan escrito queda en `BLOCKED`, valida contra 2.1 y `flowPreconditions` nombra la pregunta.
  · rojo visto: si
- **E-08** — Sobre todas las combinaciones de unidades, capacidades y aprobaciones de la suite, el
  `status` escrito de un plan está entre los cuatro de E-02 y el de cada unidad entre los tres de
  E-03, y todo plan `BLOCKED` tiene su causa escrita: una pregunta bloqueante en
  `flowPreconditions`, una capacidad `SUPPORTED_UNAVAILABLE`, una fuente que bloquea o una unidad con
  `blockers`. · rojo visto: si
- **E-09** — `estado_de` mira en este orden: precondiciones del flujo, capacidad no disponible o
  fuente que bloquea (`BLOCKED`); hueco de capacidad (`CAPABILITY_RESOLUTION`); aprobación pendiente
  (`WAITING_FOR_HUMAN_APPROVAL`); unidad `BLOCKED` (`CAPABILITY_RESOLUTION`); y si no hay nada,
  `READY_FOR_EXECUTION`. · rojo visto: si

### La compuerta

- **E-10** — Una unidad bloqueada solo por una capacidad no hace falso `agents.routing`: ni
  `flowPreconditions` del plan ni la derivación de `task-flow-state` reportan `AGENT_NOT_ROUTABLE`.
  · rojo visto: si
- **E-11** — Con un agente no ruteable, el plan queda `BLOCKED`, la unidad lleva el `blockers` de
  ruteo y `task-flow-state` queda `BLOCKED` en `PLANNING` con `AGENT_NOT_ROUTABLE`; no llega a
  `EXECUTION`. · rojo visto: si

### La regla de lectura

- **E-12** — `refute --compile` y `--replanificar` leen un plan 2.1, 2.0 o 1.0, y rechazan con
  código 2 cualquier otra versión o la ausencia de versión, nombrándola. · rojo visto: si
- **E-13** — Un plan 1.0 o 2.0 con `status: BLOCKED` se lee; uno con `DELEGATING` en el plan o
  `READY` en una unidad se rechaza con 2 y nombra el campo y el valor. · rojo visto: si
- **E-14** — Un plan 2.1 guardado con una unidad `BLOCKED` sin `blockers`, o con `blockers: []`, se
  rechaza con 2 nombrando la unidad, y el archivo no cambia. El mismo documento con versión 2.0 se
  lee. · rojo visto: si
- **E-15** — `--replanificar` sobre un 2.0 escribe 2.1, sube `plan_version` en uno y conserva la
  historia. · rojo visto: si

### El merge

- **E-16** — Ningún caso de la suite le pasa `-Harness` al `install.ps1` de la fábrica. Solo
  `63-harness-unico-instalador.ps1` lo usa, contra instaladores viejos y para probar el rechazo.
  · rojo visto: si
- **E-17** — `install.ps1 -Doctor` calcula la Context Bar con `Get-BarraDelDoctor` en todo proyecto
  instalado, sin mirar qué harness tiene, y muestra `CONFIGURED` como aviso. · rojo visto: si
- **E-18** — `dev-harness.py plan` con una propuesta con un ciclo de dependencias sale con 2, igual
  que con un id de unidad repetido. · rojo visto: si
- **E-19** — `docs/dominio/modelo-canonico.md` y `docs/orquestacion.md` nombran
  `orchestration-plan/2.1`, `BLOCKED` como estado del plan y `blockers`. · rojo visto: si
- **E-20** — `.\tests\Invoke-Tests.ps1` sale con 0 sobre el árbol integrado. · rojo visto: no consta

### El modelo canónico

- **E-21** — Los seis schemas de Flow Governance figuran en Persistencia y contrato de un concepto de
  docs/dominio/modelo-canonico.md, y la tabla de D7 dice cuál. · rojo visto: si

### Reescribir un plan guardado

- **E-22** — Una decisión humana sobre un plan 2.0 o 1.0 guardado lo escribe como 2.1, con la
  versión siguiente y `blockers` derivados en sus unidades `BLOCKED`. Una unidad `BLOCKED` cuyo
  contenido no dice por qué se rechaza nombrándola, y un plan con un estado retirado se rechaza sin
  tocar el archivo. · rojo visto: si

## Cómo se verifica

Todos los escenarios por la suite. Ninguno es una corrida de un modelo: no hay marcas
`· verificación: lectura`. E-20 es la compuerta entera.

Los tests nuevos van en `tests/casos/71_plan_2_1.py` y nombran su escenario. Los de 0.30.0 que
fijaban 2.0 (`64_modelo_de_dominio.py`, `64-modelo-de-dominio-instalador.ps1`) pasan a 2.1 y citan
este cambio al lado de su id original. E-21 lo cubren los tests de E-05 de
`64_modelo_de_dominio.py`, que pasan a contar 52 schemas y a leer la tabla de D7 junto a la de 3.2.

## Riesgos conocidos

- **La condición de `blockers` vive en dos lugares que no son el schema.** Otro productor que
  valide solo contra el schema puede escribir una unidad `BLOCKED` sin `blockers`, y la regla de
  lectura recién lo rechaza al leerlo.
- **Los planes 1.0 con `BLOCKED` escritos por las Waves se leen sin `blockers` en las unidades
  bloqueadas por capacidad.** Es correcto por D3, pero la compuerta ve esas unidades como antes de
  este cambio hasta que el plan se reescribe.
- **La lectura «unidad afectada» de la invariante es la de las Waves**: la precondición del plan
  entero queda en `flowPreconditions` y no en las unidades. Si se esperaba otra cosa, es un cambio
  de semántica y va en otra spec.
