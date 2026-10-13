---
estado: aceptada
creado: 2026-10-07
---

# ADR-0014 — El contrato de ejecución

## Contexto

ADR-0013 dejó Execution como un límite reservado: nombrado, vacío, sin lenguaje ni datos. Dejó
también tres preguntas para la Task de ejecución: dónde vive el estado de una ejecución, qué forma
tiene lo que vuelve de un agente, y si el contrato de salida es el `agentResult` de los agentes, los
"Result Statuses" de las skills o ninguno de los dos.

El relevamiento está en `docs/cambios/execution-contract/spec.md`, con 24 contradicciones numeradas
`EC-nn`. Las que pesan en el contrato:

- **un plan llega a `READY_FOR_EXECUTION` con una unidad cuyo agente no existe** (EC-01);
- **`(plan_id, plan_version)` no identifica un plan**, porque `plan --propuesta` vuelve a la versión
  1 (EC-04);
- **lo que devuelve un agente no tiene contrato**: ocho agentes declaran un `agentResult` en prosa,
  siete skills declaran siete conjuntos distintos, y nadie los lee (EC-11);
- **una capacidad disponible para HARNESS no es una capacidad disponible para el agente que corre**
  (EC-08).

Sin un contrato, el primer motor tendría que decidir todo adentro del código, con dos atajos a mano
que rompen el modelo: agregar un estado de ejecución al Plan, o leer el ledger de contabilidad para
saber qué corrió.

## Decisión

### 1. Execution es el décimo contexto

Execution deja de ser un límite reservado y pasa a ser un contexto delimitado, contractual hasta que
la Task siguiente le dé productor. Tiene lenguaje propio, invariantes, un contrato versionado
(`execution-request/1.0` y `execution-result/1.0`) y un ciclo de vida. Sus ocho conceptos son
Execution, ExecutionRequest, ExecutionResult, ExecutionId, ExecutionAdmission, ExecutionError,
ExecutionEvidence y AgentReport. El Host Adapter es infraestructura, no un concepto.

### 2. Una request es una WorkUnit y un intento, con una identidad que genera HARNESS

Una ExecutionRequest identifica exactamente una WorkUnit de exactamente un plan, y una Execution es
exactamente un intento. Su identidad, el ExecutionId, la genera HARNESS: no sale del Host, ni de la
sesión, ni del contenido. Un reintento es otra Execution, con otro ExecutionId y la misma
`idempotencyKey`. Reservar esa clave y crear la Execution es atómico; el mecanismo lo elige la Task
siguiente.

### 3. `READY_FOR_EXECUTION` y `PENDING` son necesarias y no suficientes: decide la admisión

El Plan no cambia, y sus estados siguen siendo del documento. Que una WorkUnit corra lo decide la
ExecutionAdmission, al pedir y otra vez antes de entregar, con una precedencia cerrada de catorce
códigos. La admisión consume lo que deciden Planning, Normative Sources y Catalog sin recalcularlo, y
rechaza en vez de replanificar. Una compuerta normativa en `blocked` da `NORMATIVE_GATE_BLOCKED`:
la decisión es de Normative Sources, y no hay una autorización de Governance antes de ejecutar.

### 4. Seis estados, cuatro terminales, sin `BLOCKED`

`REQUESTED → RUNNING`, `REQUESTED → REJECTED`, `REQUESTED → CANCELLED`, `RUNNING → SUCCEEDED`,
`RUNNING → FAILED` y `RUNNING → CANCELLED`. `RUNNING` empieza cuando el motor entrega la request a
quien la corre. Ninguno de los estados es `BLOCKED`: el `BLOCKED` de la WorkUnit es de Planning. Un
resultado terminal no cambia.

### 5. Execution recibe un AgentReport del Host Adapter, y no interpreta texto

Lo que vuelve de un agente le llega a Execution como un AgentReport, `{declaredStatus, artifact}`,
que arma el Host Adapter desde la salida nativa del Host. `declaredStatus` usa el vocabulario de
cuatro valores del `agentResult`: `COMPLETE`, `PARTIAL`, `BLOCKED` y `FAILED`. Execution no busca en
texto libre, no parsea Markdown y no lee los "Result Statuses" de las skills. El AgentReport no
tiene autoridad: `SUCCEEDED` es mecánico, no de cumplimiento, y sin un AgentReport válido el
intento es `FAILED` con `OUTPUT_INVALID`.

### 6. El estado de una ejecución vive en su propio registro

Ni en el Plan ni en la contabilidad. Los dos invariantes del punto 4 de ADR-0013 siguen:

- La contabilidad no es estado de ejecución.
- El estado del Plan se deriva del contenido del Plan.

### 7. `orchestration-plan/2.0` no cambia, y la identidad del plan es su huella

Execution lee el plan por la regla de lectura única. Como `plan_version` vuelve a 1, la identidad
efectiva de un plan para ejecutar es su huella, `planFingerprint`: la misma que la refutación ya
guarda en `run.json`.

## Consecuencias

A favor:

- La Task siguiente recibe la identidad, las precondiciones, los estados, los errores, la evidencia
  y los bordes ya decididos, y los puede verificar contra dos schemas y un validador.
- El Plan, la contabilidad y Governance no cambian.

En contra, y dicho:

- **Dos schemas y un módulo sin productor llegan a cada proyecto instalado**, como HarnessTool.
- **"Execution" nombra al contexto y al agregado**, y `execution-` nombra también a la contabilidad,
  que es un nombre heredado.
- **La salida de los agentes hoy es prosa.** El Host Adapter de Claude Code va a tener que obtener de
  ahí un `declaredStatus`, y si no puede, el intento es `OUTPUT_INVALID`.

## Integración con HARNESS 0.31.0

Este ADR se escribió sobre 0.30.0 (`f9393cf`). Antes de publicarse salió 0.31.0 (`fdca5ce`), con
Flow Governance y `orchestration-plan/2.1`. El contrato se alineó a esa línea sin reabrir las siete
decisiones. Lo que cambia en su lectura:

- **Decisión 3.** La admisión consume también lo que decide el TaskFlowState, que en 0.31.0 es de
  Planning: si la tarea no puede delegar, `DELEGATION_NOT_ALLOWED`. La precedencia pasa de catorce
  códigos a quince, y la lista de veintidós a veintitrés. La request guarda del flujo solo esa
  decisión, `admission.flow`: ni el TaskFlowState, ni una HumanIntent, ni el vínculo de sesión.
- **La compuerta del flujo no es la admisión.** La de PreToolUse decide por llamada de herramienta
  para la tarea de una sesión; la ExecutionAdmission decide por WorkUnit. Ninguna reemplaza a la otra,
  y Execution no usa los códigos de la compuerta del flujo.
- **Decisión 7.** El plan es `orchestration-plan/2.1` desde 0.31.0, por Flow Governance y no por
  Execution. Lo que decide la 7 sigue: Execution no cambia el plan, lo lee por la regla de lectura
  única, y su identidad es la huella. Un 2.0 o un 1.0 se lee y no se admite: no puede estar listo por
  los dos lados, y se replanifica.
- **Contexto, EC-01.** En 2.1 un agente que el registro no rutea deja el plan `BLOCKED`. La admisión
  conserva `AGENT_UNAVAILABLE` para un registro que cambia después de planificar.

`execution-request/1.0` y `execution-result/1.0` siguen en 1.0: no se publicaron, y no hay una
instancia, un productor ni un proyecto instalado con la versión anterior. El detalle está en la
sección «Integración con HARNESS 0.31.0» de `docs/cambios/execution-contract/spec.md`.

## Revisión

**Revisa el punto 4 de ADR-0013**, como preveía su propia revisión: Execution deja de ser un límite
reservado. ADR-0013 no se edita, porque es historia, y sus dos invariantes siguen en pie. Este ADR se
revisa cuando la Task siguiente construya la admisión, el motor o el almacenamiento, si alguno pide
cambiar el contrato más allá de una versión menor.
