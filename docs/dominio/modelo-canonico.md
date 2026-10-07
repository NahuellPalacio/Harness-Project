# El modelo de dominio canónico de HARNESS

Qué conceptos tiene HARNESS, qué significa cada uno, en qué contexto vive y dónde termina el
producto. Sale del relevamiento de 0.29.0 y de la spec que lo aprobó:
[`docs/cambios/canonical-domain-model/spec.md`](../cambios/canonical-domain-model/spec.md). Las
decisiones de largo plazo están en
[ADR-0013](../adr/0013-modelo-de-dominio-canonico.md).

📌 **Cómo se lee.** Los nombres canónicos están en inglés, como pide
[ADR-0011](../adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md) para los
identificadores. El código, el CLI y los archivos de estado siguen mayormente en español, y este
cambio no renombra nada: la sección `## Vocabulario` mapea cada nombre actual a su nombre canónico.

🔴 **El catálogo lo define la tabla de `## Conceptos`.** Un concepto existe si tiene su fila ahí, y
tiene exactamente un `### <Concepto>` debajo. El número de filas es un resultado del relevamiento, no
un contrato: si aparece mejor evidencia, el catálogo se corrige.

## Conceptos

| Concepto | Contexto | Clasificación | Qué es |
|---|---|---|---|
| Task | Work Intake | External | El trabajo que alguien pidió; su registro vive en Jira |
| TaskKey | Work Intake | Value Object | La identidad de una Task, igual en todo lo que se deriva de ella |
| TaskRecord | Work Intake | External | El issue de Jira que registra la Task |
| Ficha | Work Intake | External | La Ficha de Proyecto, un issue de Jira que describe el proyecto |
| TaskContext | Work Intake | Snapshot | Lo que se sabe de una Task en un momento, con la procedencia de cada sección |
| ProvenanceRef | Work Intake | Value Object | De dónde salió un dato del TaskContext |
| SectionConfidence | Work Intake | Value Object | Qué tan seguro está un contexto de una de sus secciones |
| ContextGap | Work Intake | Value Object | Lo que falta, lo que choca, lo redactado y lo preguntado en un contexto |
| SessionTaskBinding | Work Intake | Entity | Qué Task trabaja una sesión del Host, por una clave que se declaró |
| ProjectContext | Project Knowledge | Snapshot | El índice del código del proyecto, con su revisión y su hash |
| ProjectMemory | Project Knowledge | Domain Policy | Las reglas con que HARNESS trata lo que el equipo dejó escrito |
| ManagedSource | Normative Sources | Entity | Un documento normativo cuya identidad registra la fábrica |
| SourceState | Normative Sources | Aggregate Root | El estado de cada fuente en un proyecto, con las decisiones humanas |
| SourceAcceptance | Normative Sources | Record | La decisión de una persona nombrada sobre una identidad observada |
| Channel | Normative Sources | Value Object | Por dónde se observa una fuente |
| NormativeKnowledge | Normative Sources | Snapshot | Lo que el proyecto puede usar como norma vigente |
| RefreshAgenda | Normative Sources | Record | Cuándo se volvió a mirar las fuentes y cuándo vence |
| NormativeFreshnessGate | Normative Sources | Domain Service | La decisión `allowed`, `blocked` o `unresolved` antes de usar la norma |
| Plan | Planning | Aggregate Root | Cómo se descompone una Task en WorkUnits; es un documento, no ejecuta |
| PlanProposal | Planning | DTO / Contract | Lo que escribe `dev-orchestrator`: entrada sin autoridad |
| WorkUnit | Planning | Entity | Una porción de la Task para un dominio y un agente |
| ContextSlice | Planning | Value Object | La parte del TaskContext que ve una WorkUnit |
| ModelPolicy | Planning | Value Object | El tier requerido para una WorkUnit, con el porqué |
| ModelRouter | Planning | Domain Service | Decide el tier por señales de complejidad |
| ConsumptionPolicy | Planning | Value Object | Qué tiers se aprueban solos y cuántas llamadas premium hay |
| ConsumptionGate | Planning | Domain Service | Aprueba un tier o crea una ModelTierApproval |
| ModelTierApproval | Planning | Entity | El pedido de que una persona apruebe un tier caro |
| CapabilityGap | Planning | Value Object | Una capacidad pedida que no está disponible |
| FlowRequiredInput | Planning | Domain Policy | Lo que una etapa del flujo necesita antes de avanzar, y cómo se consigue si falta |
| TaskFlowState | Planning | Snapshot | El estado detallado del flujo de una Task: etapa, condición, qué la frena y desde dónde se retoma |
| HumanIntent | Planning | Entity | Una decisión que una persona escribió en el chat, de un solo uso |
| HumanDecisionRecord | Planning | Record | Una decisión humana ya aplicada |
| AgentRegistry | Catalog | Aggregate Root | La autoridad sobre qué agentes y skills existen |
| Agent | Catalog | Entity | Un rol especializado al que se le asigna una WorkUnit |
| Skill | Catalog | Entity | Un procedimiento que usa un Agent |
| WorkDomain | Catalog | Value Object | Un área de trabajo: backend, frontend, seguridad… |
| Capability | Catalog | Value Object | Una habilidad con nombre que una WorkUnit necesita |
| Integration | Catalog | Entity | Un sistema externo conectado, con su estado y sus capacidades |
| HarnessTool | Catalog | Value Object | Un artefacto que HARNESS generaría bajo un contrato; dormido |
| DatabaseAccessPolicy | Catalog | Domain Policy | Qué operación sobre una base puede correr en cada ambiente; dormida |
| NormativeStandard | Governance | Value Object | Una norma con su versión |
| NormativeMatrix | Governance | Domain Policy | Las reglas de una norma, con su aplicabilidad y sus controles |
| NormativeRule | Governance | Entity | Una regla citable de una norma |
| NormativeSignal | Governance | Value Object | Un hecho que decide si una regla aplica |
| Applicability | Governance | Value Object | Si una regla aplica a una WorkUnit |
| ControlRegistry | Governance | Configuration | Qué controles existen |
| Control | Governance | Entity | Lo que una regla exige que exista |
| Policy | Governance | Domain Policy | Un Control de tipo POLICY: un requisito en prosa |
| ControlCheck | Governance | Domain Service | Un Control de tipo CHECK, que evalúa y devuelve un estado |
| CheckSpecification | Governance | Configuration | El `.md` que describe un ControlCheck |
| Review | Governance | Snapshot | Un Control de tipo REVIEW y el documento que lo resuelve |
| Evidence | Governance | Value Object | Un hecho observado que sostiene una afirmación |
| EvaluationResult | Governance | Value Object | El resultado de evaluar una regla o un control |
| ExternalSecurityApproval | Governance | External | Evidencia de que una autoridad externa aprobó algo |
| Refutation | Governance | Aggregate Root | La refutación de un Plan regla por regla |
| RefutationUnit | Governance | Entity | Una afirmación para refutar: (WorkUnit, regla, alcance) |
| RefutationVerdict | Governance | Record | El juicio sobre una RefutationUnit |
| Finding | Governance | Record | Un hallazgo de governance con estado |
| EvaluationRecord | Governance | Record | Un resultado de evaluación registrado con las huellas de su evidencia |
| SecuritySummary | Governance | Snapshot | El estado de seguridad de una Task |
| SecretGate | Guardrails | Domain Service | La única regla que bloquea: un secreto que se va a escribir |
| GuardrailCheck | Guardrails | Domain Service | Un check del hook en PostToolUse, que avisa y nunca bloquea |
| GuardrailFinding | Guardrails | Value Object | Un aviso de texto de un GuardrailCheck |
| SessionFlowNotice | Guardrails | Infrastructure | La huella del último aviso del flujo a una sesión, para no repetirlo |
| AccountingEvent | Observability | Record | Algo observado del consumo de modelo de una sesión o una Task |
| LedgerKey | Observability | Value Object | La clave de un ledger de contabilidad: una TaskKey o una sesión |
| AccountingSummary | Observability | Snapshot | Los totales de un ledger, conciliados contra el proveedor |
| CostBudget | Observability | Configuration | Los umbrales de contexto y los límites de plata del proyecto |
| ContextBarState | Observability | Snapshot | Lo que dibuja la Context Bar |
| Installation | Host Integration | Aggregate Root | El estado del harness en un proyecto |
| RuntimeComponentHealth | Host Integration | Value Object | Si un componente está `ACTIVE`, y por qué no |
| HarnessConfig | Host Integration | Configuration | La configuración del proyecto, sembrada desde `manifest.json` |
| Host | External | External | Claude Code: el sistema que aloja al producto |
| HostSession | External | External | Una sesión de Claude Code |
| HostTool | External | External | Una herramienta de Claude Code |

### Task

- **Qué es:** el trabajo que alguien pidió en el issue tracker. HARNESS no tiene ni su estado ni
  su ciclo de vida: los tiene Jira.
- **Contexto:** Work Intake
- **Clasificación:** External
- **Identidad:** su TaskKey.
- **Ciclo y estados:** no aplica en HARNESS: el ciclo de vida lo maneja Jira, y HARNESS no lo
  interpreta.
- **Invariantes:** todo artefacto que HARNESS deriva de una Task se nombra con su TaskKey: el
  contexto, el plan, la refutación y el ledger de seguridad.
- **Crea / cambia / lee:** la crea y la cambia una persona en Jira; HARNESS la lee a través de su
  TaskRecord.
- **Persistencia y contrato:** no aplica: HARNESS no la persiste, guarda snapshots y documentos
  derivados de ella.
- **Dónde vive:** en Jira. Ningún código la representa: `TareaNoResuelta`
  (`harnesses/desarrollo/bin/contexto/tarea.py`) es solo una excepción.
- **No es:** el issue de Jira (eso es TaskRecord), ni una WorkUnit, ni una HostSession.

### TaskKey

- **Qué es:** la identidad de una Task, igual en todo artefacto que se derive de ella.
- **Contexto:** Work Intake
- **Clasificación:** Value Object
- **Identidad:** su valor, con la forma `^[A-Za-z][A-Za-z0-9_]*-[0-9]+$`. No se normaliza a
  mayúsculas.
- **Ciclo y estados:** no aplica: es un valor.
- **Invariantes:** ningún artefacto de una Task se escribe con una clave que no cumple la forma, y
  todos usan la misma. La regla está escrita dos veces, idéntica: `CLAVE_JIRA` en `dev-harness.py` y
  `CLAVE` en `refutacion.py`. Unificarlas está pendiente.
- **Crea / cambia / lee:** la escribe una persona como argumento del CLI; la validan `contexto`,
  `refute` y `seguridad`; en `plan` la frena el patrón de `plan_id`.
- **Persistencia y contrato:** viaja en `meta.task_key` y `context_id` de
  `task-context.schema.json`, en `plan_id` y `meta.task_key` de `orchestration-plan.schema.json`, en
  el `taskKey` de cada RefutationUnit y en el nombre de las carpetas.
- **Dónde vive:** `harnesses/desarrollo/bin/dev-harness.py` y
  `harnesses/desarrollo/bin/orquestacion/refutacion.py`.
- **No es:** el id de una sesión del Host, que es una HostSession. Una LedgerKey puede ser
  cualquiera de las dos.

### TaskRecord

- **Qué es:** el issue de Jira que registra la Task.
- **Contexto:** Work Intake
- **Clasificación:** External
- **Identidad:** su clave en Jira.
- **Ciclo y estados:** los de Jira. HARNESS copia `status` y `priority` al TaskContext sin
  interpretarlos.
- **Invariantes:** HARNESS lo lee y nunca lo escribe. Si Jira devuelve una clave distinta de la
  pedida, el TaskContext lo registra como conflicto.
- **Crea / cambia / lee:** lo escribe una persona en Jira; lo lee el resolvedor de tarea a través de
  la Integration de Jira.
- **Persistencia y contrato:** no aplica: vive en Jira. Su copia normalizada es la sección `task` de
  `task-context.schema.json`.
- **Dónde vive:** en Jira; lo lee `harnesses/desarrollo/bin/contexto/tarea.py`.
- **No es:** la Task, ni una entidad de dominio de HARNESS.

### Ficha

- **Qué es:** la Ficha de Proyecto, un issue de Jira que describe el proyecto.
- **Contexto:** Work Intake
- **Clasificación:** External
- **Identidad:** su clave en Jira. Hay una por proyecto, y dos se declaran conflicto.
- **Ciclo y estados:** los de Jira.
- **Invariantes:** da la sección `project` del TaskContext, marcada `inferred`. Si hay más de una, el
  TaskContext declara el conflicto y la deja vacía.
- **Crea / cambia / lee:** la escriben personas en Jira; la leen el resolvedor de proyecto y el
  canal `jira:<FICHA>` de las fuentes.
- **Persistencia y contrato:** no aplica: vive en Jira. Su copia es `project.ficha` de
  `task-context.schema.json`.
- **Dónde vive:** en Jira; la lee `harnesses/desarrollo/bin/contexto/proyecto.py`.
- **No es:** NormativeKnowledge, ni una ficha de módulo de `docs/codebase/`, que es parte del
  ProjectContext.

### TaskContext

- **Qué es:** lo que se sabe de una Task en un momento: la tarea, la Ficha, los documentos y el
  repositorio, cada sección con su procedencia.
- **Contexto:** Work Intake
- **Clasificación:** Snapshot
- **Identidad:** `tsk_<TaskKey>` más `context_hash`.
- **Ciclo y estados:** se regenera entero en cada `contexto` y se pisa. Nadie lo modifica en partes,
  y no tiene estados.
- **Invariantes:** sin `jira.issue.read` no existe. Cada sección declara su SectionConfidence y su
  procedencia, el texto de afuera se redacta, y el hash excluye `generated_at`. Contradicción
  conocida: el hash incluye `retrieved_at`, así que no es determinista.
- **Crea / cambia / lee:** lo crea `dev-harness.py contexto`; lo leen `plan` y `dev-orchestrator`.
- **Persistencia y contrato:** `.claude/contextos/<KEY>.json`, contra `task-context.schema.json`
  (`task-context/1.0`), validado antes de escribir.
- **Dónde vive:** `harnesses/desarrollo/bin/contexto/ensamblador.py`.
- **No es:** Knowledge ni ProjectContext. Un adjunto de la Ficha que no está en el registro es
  documentación del TaskContext, no una ManagedSource.

### ProvenanceRef

- **Qué es:** de dónde salió un dato del TaskContext.
- **Contexto:** Work Intake
- **Clasificación:** Value Object
- **Identidad:** `source_id`.
- **Ciclo y estados:** no aplica.
- **Invariantes:** cada fuente leída deja una, y su `type` es uno de los ocho de `sources[]`.
- **Crea / cambia / lee:** la anota el acumulador de los resolvedores; la lee quien audita el
  contexto.
- **Persistencia y contrato:** `sources[]` de `task-context.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/contexto/comun.py`.
- **No es:** una ManagedSource ni un Channel.

### SectionConfidence

- **Qué es:** qué tan seguro está un contexto de una de sus secciones.
- **Contexto:** Work Intake
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** `confirmed`, `inferred`, `conflicted`, `missing` y `stale`. `stale` no lo
  produce nadie.
- **Invariantes:** toda sección de un TaskContext o de un ProjectContext lleva la suya. Un hueco se
  declara, no se omite.
- **Crea / cambia / lee:** lo escriben los resolvedores y `contexto-armar.py`; lo leen los agentes.
- **Persistencia y contrato:** el campo `knowledge_status` de `task-context.schema.json` y de
  `project-context.schema.json`.
- **Dónde vive:** los resolvedores de `harnesses/desarrollo/bin/contexto/`.
- **No es:** Knowledge, aunque el campo se llame `knowledge_status`.

### ContextGap

- **Qué es:** lo que falta, lo que se contradice, lo que se redactó y lo que queda preguntado en un
  contexto.
- **Contexto:** Work Intake
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** una contradicción entre fuentes se registra en `conflicts`, como dos Fichas o una
  clave de Jira distinta de la pedida. Una capacidad que falta se declara en
  `missing_capabilities`.
- **Crea / cambia / lee:** lo anota el acumulador; lo leen los agentes y quien audita.
- **Persistencia y contrato:** `gaps_and_conflicts` de `task-context.schema.json` y de
  `project-context.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/contexto/comun.py`.
- **No es:** un Finding de governance.

### SessionTaskBinding

- **Qué es:** qué Task trabaja una sesión de Claude Code. Es el vínculo entre una HostSession y una
  TaskKey, y nace de una declaración.
- **Contexto:** Work Intake
- **Clasificación:** Entity
- **Identidad:** el `session_id` de la HostSession. Hay uno por sesión.
- **Ciclo y estados:** lo crea una declaración y lo reemplaza la siguiente. `task_binding.resolver`
  da `SESSION_TASK_BOUND`, `SESSION_TASK_UNRESOLVED`, `SESSION_TASK_AMBIGUOUS` o
  `SESSION_TASK_STALE`.
- **Invariantes:**
  - lo crea solo una declaración: una clave dicha en el prompt, o la de un comando del Harness;
  - nada se infiere de la última Task tocada ni del puntero `active-task.json`: con dos o más
    Tasks con estado y sin vínculo, la resolución es `SESSION_TASK_AMBIGUOUS` y nadie elige por la
    persona;
  - sin `session_id` no hay vínculo;
  - uno ilegible, de otra versión o de otra sesión es `SESSION_TASK_STALE`: no se usa ni se repara;
  - guarda solo la clave: ni el prompt, ni `tool_input`, ni el TaskContext, el Plan o el estado del
    flujo.
- **Crea / cambia / lee:** lo escribe `task_binding.escribir`, desde UserPromptSubmit cuando el
  prompt declara una clave y desde la compuerta del flujo de PreToolUse cuando un comando del
  Harness nombra la suya; lo leen `task_binding.resolver`, la compuerta del flujo y el aviso del
  flujo de UserPromptSubmit.
- **Persistencia y contrato:** `.claude/runtime/sessions/<SAFE_SESSION_ID>/task.json`, contra
  `session-task-binding.schema.json` (`session-task-binding/1.0`). En runtime lo valida un validador
  propio, `_valido` de `task_binding.py`, que exige las claves exactas; el schema entero lo validan
  los tests.
- **Dónde vive:** `comun/hooks/lib/task_binding.py`.
- **No es:** la Task ni la HostSession: es el vínculo entre las dos. Tampoco es el puntero
  `active-task.json` del TaskFlowState, que la resolución nunca lee.

### ProjectContext

- **Qué es:** el índice del código del proyecto, serializado con su revisión y su hash.
- **Contexto:** Project Knowledge
- **Clasificación:** Snapshot
- **Identidad:** `ctx_<repo>_<rev4>` más `context_hash`.
- **Ciclo y estados:** se regenera entero cuando `dev-iniciador-code` vuelve a recorrer el código.
  Nadie compara su `repo_revision` con el HEAD.
- **Invariantes:** lo valida el script antes de escribirlo, su hash no depende del reloj, y nadie lo
  edita a mano.
- **Crea / cambia / lee:** lo producen `dev-iniciador-code`, que es un modelo, y `contexto-armar.py`.
  Lo leen el resolvedor de repositorio (solo el hash), la refutación, la bienvenida y SessionStart.
- **Persistencia y contrato:** `<rutaCodebase>/project-context.json`, versionado en el proyecto,
  contra `project-context.schema.json` (`project-context/1.1`).
- **Dónde vive:** `comun/bin/contexto-armar.py`.
- **No es:** ProjectMemory: `docs/codebase/` no es `docs/conocimiento/`.

### ProjectMemory

- **Qué es:** las reglas con que HARNESS trata lo que el equipo decidió dejar escrito: las zonas del
  `CLAUDE.md` con sus techos, qué se purga y qué no, y el write-back a `docs/conocimiento/`. Los
  documentos son del proyecto.
- **Contexto:** Project Knowledge
- **Clasificación:** Domain Policy
- **Identidad:** no aplica: no es una cosa individual. Es un `CLAUDE.md`, que comparte con el bloque
  del instalador, más una carpeta de notas sueltas.
- **Ciclo y estados:** no aplica como conjunto: cada zona y cada nota cambian por su cuenta.
- **Invariantes:** nada sale de CACHÉ sin estar escrito y verificado en `docs/conocimiento/`, FIJA
  no se purga, y los techos avisan y no bloquean.
- **Crea / cambia / lee:** los documentos los escriben las personas, y `flush-memoria` cuando
  alguien lo invoca. SessionStart lee la zona CACHÉ, y `claude-md-zonas.py` mide los techos.
- **Persistencia y contrato:** los documentos están versionados en el proyecto. Las reglas están en
  las zonas de `comun/hooks/lib/zonas.py` y en los `techoZona*` de `manifest.json`, sin schema.
- **Dónde vive:** `comun/hooks/lib/zonas.py`, `comun/agents/flush-memoria.md` y
  `comun/checks/claude-md-zonas.py`.
- **No es:** Knowledge, ni Source, ni Context, ni un documento.

### ManagedSource

- **Qué es:** un documento normativo cuya identidad registra la fábrica: versión, hash del original
  y extracto.
- **Contexto:** Normative Sources
- **Clasificación:** Entity
- **Identidad:** `id`, como `ES0901`.
- **Ciclo y estados:** `CURRENT` o `RETIRED` en el registro. El registro no guarda historia: la
  historia es git.
- **Invariantes:** el registro es la única autoridad sobre su identidad, y el hash es del original,
  nunca del extracto.
- **Crea / cambia / lee:** la escribe la fábrica; la leen `fuentes`, la compuerta normativa y la
  bienvenida.
- **Persistencia y contrato:** `harnesses/desarrollo/reglas/source-registry.json`, contra
  `source-registry.schema.json` (`source-registry/1.1`). El extracto vive en `normativa/extractos/`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/registro_fuentes.py`.
- **No es:** un adjunto cualquiera de la Ficha, ni la procedencia de un contexto.

### SourceState

- **Qué es:** el estado de cada fuente en un proyecto, derivado de lo observado, con las decisiones
  humanas.
- **Contexto:** Normative Sources
- **Clasificación:** Aggregate Root
- **Identidad:** el proyecto: un archivo por proyecto.
- **Ciclo y estados:** doce estados por fuente, desde `CURRENT` hasta
  `KNOWLEDGE_PROMOTION_INCOMPLETE`.
- **Invariantes:** el estado se deriva de la evidencia observada, `CURRENT` pide cinco condiciones,
  y la frescura es relativa al canal. Contradicción conocida: guarda decisiones humanas en un archivo
  que se declara derivado y que está gitignoreado.
- **Crea / cambia / lee:** lo escriben `fuentes`, `fuentes --aceptar` y la revisión automática; lo
  leen la compuerta normativa, la bienvenida y `seguridad --conocimiento`.
- **Persistencia y contrato:** `.claude/harness.fuentes.json`, contra `source-state.schema.json`
  (`sources-state/1.1`).
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/frescura.py`.
- **No es:** el registro de la fábrica, que es la ManagedSource.

### SourceAcceptance

- **Qué es:** la decisión de una persona nombrada, `APPLY` o `POSTPONE`, sobre una identidad
  observada.
- **Contexto:** Normative Sources
- **Clasificación:** Record
- **Identidad:** fuente, versión y sha256 observados.
- **Ciclo y estados:** `APPLY` o `POSTPONE`. `POSTPONE` no tiene comando en el CLI.
- **Invariantes:** la escribe una persona con nombre, contra lo observado en la misma corrida.
  `--auto` no acepta nada.
- **Crea / cambia / lee:** la escribe `fuentes --aceptar`; la leen la resolución del estado y el
  resumen de seguridad.
- **Persistencia y contrato:** `decisions` y `acceptance` de `source-state.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/dev-harness.py`, el subcomando `fuentes`.
- **No es:** una ModelTierApproval ni una ExternalSecurityApproval.

### Channel

- **Qué es:** por dónde se observa una fuente.
- **Contexto:** Normative Sources
- **Clasificación:** Value Object
- **Identidad:** `jira:<FICHA>` o `archivo:<dir>`.
- **Ciclo y estados:** no aplica.
- **Invariantes:** la frescura es relativa al canal, y el canal no prueba la autoría.
- **Crea / cambia / lee:** lo deja la última corrida de `fuentes`; lo usa la revisión automática.
- **Persistencia y contrato:** el campo `channel` de `source-state.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/auto_refresh.py`.
- **No es:** una ProvenanceRef, ni la Integration de Jira.

### NormativeKnowledge

- **Qué es:** lo que el proyecto puede usar como norma vigente: las ManagedSource en `CURRENT`, con
  su extracto.
- **Contexto:** Normative Sources
- **Clasificación:** Snapshot
- **Identidad:** el proyecto.
- **Ciclo y estados:** se recalcula cada vez que se lee el SourceState.
- **Invariantes:** solo cuentan las fuentes en `CURRENT` o `RETIRED`; las demás quedan pendientes.
- **Crea / cambia / lee:** lo proyectan la bienvenida y el resumen de seguridad; lo lee la persona.
- **Persistencia y contrato:** el campo `knowledge` de `harness-installation-state.schema.json` y el
  bloque `knowledge` de `security-summary.schema.json` son proyecciones suyas.
- **Dónde vive:** `comun/hooks/lib/bienvenida.py`.
- **No es:** ProjectMemory ni SectionConfidence.

### RefreshAgenda

- **Qué es:** cuándo se volvió a mirar las fuentes, cuándo vence y por qué disparador, con su
  política.
- **Contexto:** Normative Sources
- **Clasificación:** Record
- **Identidad:** el proyecto.
- **Ciclo y estados:** `NEVER_CHECKED`, `CURRENT`, `DUE`, `RUNNING`, `SUCCEEDED_WITH_UPDATES`,
  `UNRESOLVED` y `ERROR`. Se escriben tres: `CURRENT`, `SUCCEEDED_WITH_UPDATES` y `UNRESOLVED`.
- **Invariantes:** "vencida" quiere decir que venció la agenda, no la fuente, y SessionStart nunca
  sale a la red.
- **Crea / cambia / lee:** la escribe `auto_refresh.registrar`; la leen la compuerta normativa y la
  bienvenida.
- **Persistencia y contrato:** `.claude/runtime/knowledge-refresh.json`, contra
  `knowledge-refresh-state.schema.json`. La política, contra `knowledge-refresh-policy.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/auto_refresh.py`.
- **No es:** estado de ejecución, ni el SourceState.

### NormativeFreshnessGate

- **Qué es:** la decisión `allowed`, `blocked` o `unresolved` antes de usar conocimiento normativo.
- **Contexto:** Normative Sources
- **Clasificación:** Domain Service
- **Identidad:** no aplica.
- **Ciclo y estados:** devuelve una de las tres decisiones y no persiste nada propio.
- **Invariantes:** corre antes de `plan`, `refute --compile` y `seguridad`, y `blocked` corta salvo
  en `seguridad`. Puede refrescar las fuentes, y eso escribe la RefreshAgenda, el SourceState y
  descargas. Esos efectos son suyos: un plan que después se rechaza no los deshace.
- **Crea / cambia / lee:** la invoca `dev-harness.py`; lee el SourceState y la RefreshAgenda.
- **Persistencia y contrato:** no aplica: no tiene schema. Sus efectos quedan en
  `.claude/runtime/knowledge-refresh.json`, `.claude/harness.fuentes.json` y
  `.claude/conocimiento/fuentes/`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/auto_refresh.py`
  (`ensure_normative_knowledge_fresh`).
- **No es:** un RefutationVerdict ni un EvaluationResult.

### Plan

- **Qué es:** cómo se descompone una Task en WorkUnits, con quién, con qué y qué la frena. Es un
  documento: no ejecuta.
- **Contexto:** Planning
- **Clasificación:** Aggregate Root
- **Identidad:** `pln_<TaskKey>` más `plan_version`.
- **Ciclo y estados:** `BLOCKED`, `CAPABILITY_RESOLUTION`, `WAITING_FOR_HUMAN_APPROVAL` y
  `READY_FOR_EXECUTION`, derivados del contenido al armarlo. La precedencia es la de
  `plan.estado_de`:
  1. precondiciones del flujo sin cumplir o sin evaluar, una capacidad soportada caída o una
     fuente exigida que bloquea dan `BLOCKED`;
  2. si no, un CapabilityGap da `CAPABILITY_RESOLUTION`;
  3. si no hay huecos, una ModelTierApproval `PENDING` da `WAITING_FOR_HUMAN_APPROVAL`;
  4. si no hay aprobaciones pendientes, una WorkUnit `BLOCKED` da `CAPABILITY_RESOLUTION`;
  5. si no queda nada, `READY_FOR_EXECUTION`.

  `--replanificar` sube la versión y suma historia.
- **Invariantes:**
  - los dominios son conocidos y hay al menos una WorkUnit;
  - los ids de WorkUnit son únicos, y el dominio de cada una está entre los del plan;
  - las dependencias existen y no forman ciclos;
  - valida contra el schema antes de escribirse;
  - nadie cambia el estado después;
  - ningún estado habla de delegar ni de ejecutar: los estados finos de la tarea viven en
    `task-flow-state`, no en el plan;
  - un plan `BLOCKED` dice por qué, en `flowPreconditions`, `capabilityStatus`,
    `knowledgeSources` o en los `blockers` de la WorkUnit afectada;
  - una WorkUnit `BLOCKED` lleva `blockers` no vacío, y una que no lo está no lleva.
- **Crea / cambia / lee:** lo arma `plan --propuesta` y lo reescribe `--replanificar`. Lo leen
  `refute --compile` y `--replanificar`, por una sola regla de lectura.
- **Persistencia y contrato:** `.claude/planes/<KEY>.json`, que sobrevive al `-Update`, contra
  `orchestration-plan.schema.json` (`orchestration-plan/2.1`). Un `2.0` o un `1.0` guardado se
  acepta si sus estados existen en 2.1, y se migra la próxima vez que se escribe. Si no, se rechaza
  sin tocar el plan ni la refutación. Un `2.1` con una WorkUnit `BLOCKED` sin `blockers` también se
  rechaza.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/plan.py`.
- **No es:** una ejecución. `READY_FOR_EXECUTION` es un estado del documento.

### PlanProposal

- **Qué es:** lo que escribe `dev-orchestrator`, un modelo. Es la entrada de `plan` y no tiene
  autoridad.
- **Contexto:** Planning
- **Clasificación:** DTO / Contract
- **Identidad:** no aplica.
- **Ciclo y estados:** no persiste: es un archivo que se pasa con `--propuesta`.
- **Invariantes:** no decide ni el tier, ni el estado, ni si un agente existe: el código arma el
  plan y lo valida.
- **Crea / cambia / lee:** la escribe `dev-orchestrator`; la lee `plan.armar`.
- **Persistencia y contrato:** no tiene schema. El esqueleto sale de `plan --plantilla`.
- **Dónde vive:** `harnesses/desarrollo/agents/dev-orchestrator.md` y
  `harnesses/desarrollo/bin/dev-harness.py` (`plantilla_de_propuesta`).
- **No es:** el Plan.

### WorkUnit

- **Qué es:** una porción de la Task para un dominio y un agente, con sus capacidades, normas y
  dependencias.
- **Contexto:** Planning
- **Clasificación:** Entity
- **Identidad:** (PlanId, `id`). El `id` es único en el plan.
- **Ciclo y estados:**
  - `PENDING`: está planificada y nada la frena;
  - `BLOCKED`: le falta una capacidad;
  - `WAITING_FOR_HUMAN_APPROVAL`: su tier pide aprobación.

  Nada la cambia después de armarla.
- **Invariantes:** su dominio es uno de los del plan, y su estado se deriva al armarla. No tiene
  resultado, ni ejecutor, ni estado posterior.
- **Crea / cambia / lee:** sale de la propuesta y la completa el código. La leen la refutación, por
  id, y la contabilidad, por `workUnitId` como texto libre.
- **Persistencia y contrato:** `workUnits[]` de `orchestration-plan.schema.json`. No tiene schema
  propio.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/plan.py` (`_armar_unidad`).
- **No es:** una Task ni una RefutationUnit.

### ContextSlice

- **Qué es:** la parte del TaskContext que ve una WorkUnit, y qué se le omitió.
- **Contexto:** Planning
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** cada dominio ve solo sus secciones, y lo que no viaja se declara en `omitted`.
- **Crea / cambia / lee:** lo arma `contexto_para`; lo lee el especialista.
- **Persistencia y contrato:** `workUnits[].context` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/plan.py` (`CONTEXTO_POR_DOMINIO`).
- **No es:** el TaskContext entero.

### ModelPolicy

- **Qué es:** el tier requerido para una WorkUnit, con el porqué.
- **Contexto:** Planning
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** lo decide el ModelRouter, no la propuesta, y usa perfiles, nunca nombres de
  modelo.
- **Crea / cambia / lee:** lo arma `plan.armar`; nadie lo convierte en un modelo concreto.
- **Persistencia y contrato:** `workUnits[].modelPolicy` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/modelo.py`.
- **No es:** el `model:` del frontmatter de un agente.

### ModelRouter

- **Qué es:** decide el tier por señales de complejidad.
- **Contexto:** Planning
- **Clasificación:** Domain Service
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** es determinista. Una señal desconocida se ignora y se nombra en `reason`.
- **Crea / cambia / lee:** lo llama `plan.armar`.
- **Persistencia y contrato:** no aplica.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/modelo.py` (`enrutar`).
- **No es:** un cliente de modelo: HARNESS no llama a ningún modelo.

### ConsumptionPolicy

- **Qué es:** qué tiers se aprueban solos y cuántas llamadas premium permite un plan.
- **Contexto:** Planning
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica. Se vuelve a leer de la configuración en cada armado.
- **Invariantes:** `maxRetries` y `allowEscalation` existen, y nadie los lee.
- **Crea / cambia / lee:** sale de `harness.config.json`; la lee el ConsumptionGate.
- **Persistencia y contrato:** `consumptionPolicy` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/consumo.py`.
- **No es:** el CostBudget.

### ConsumptionGate

- **Qué es:** aprueba un tier o crea una ModelTierApproval.
- **Contexto:** Planning
- **Clasificación:** Domain Service
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** un tier autoaprobado pasa, un premium pasa mientras quede cupo, y lo demás pide
  aprobación. Nunca lee el ledger de contabilidad.
- **Crea / cambia / lee:** lo llama `_armar_unidad`.
- **Persistencia y contrato:** no aplica.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/consumo.py` (`decidir`).
- **No es:** la evaluación del CostBudget.

### ModelTierApproval

- **Qué es:** el pedido de que una persona apruebe un tier caro para una WorkUnit. Es sobre costo,
  no sobre governance.
- **Contexto:** Planning
- **Clasificación:** Entity
- **Identidad:** (PlanId, `workUnit`).
- **Ciclo y estados:** `PENDING`, `APPROVED`, `DOWNGRADED` y `CANCELLED`. `plan` escribe solo
  `PENDING`. La resuelve una persona: con una HumanIntent, `flujo --approve` la pasa a `APPROVED` y
  `flujo --alternative` a `DOWNGRADED`, y las dos replanifican. `CANCELLED` no lo escribe nadie.
- **Invariantes:** una aprobación `PENDING` deja el plan en `WAITING_FOR_HUMAN_APPROVAL` solo si no
  hay una condición que pese más. `plan.estado_de` mira primero las precondiciones del flujo, que
  dejan el plan en `BLOCKED`, y después los CapabilityGap: si hay uno, el plan queda en
  `CAPABILITY_RESOLUTION` aunque haya aprobaciones pendientes. Después mira las
  aprobaciones, después las unidades `BLOCKED`, y recién entonces da `READY_FOR_EXECUTION`.
- **Crea / cambia / lee:** la crea el ConsumptionGate; la lee la persona en la salida de `plan`.
- **Persistencia y contrato:** `humanApprovals[]` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/consumo.py`.
- **No es:** una ExternalSecurityApproval ni una SourceAcceptance.

### CapabilityGap

- **Qué es:** una capacidad pedida que no está disponible, y a quién se deriva.
- **Contexto:** Planning
- **Clasificación:** Value Object
- **Identidad:** `capability`.
- **Ciclo y estados:** no aplica.
- **Invariantes:** un hueco deja el plan en `CAPABILITY_RESOLUTION`, y se deriva siempre a
  `dev-tool-builder` como `TEMPORARY`.
- **Crea / cambia / lee:** lo calcula `capacidades.py`; lo lee la persona.
- **Persistencia y contrato:** `capabilityGaps[]` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/capacidades.py`.
- **No es:** una Capability.

### FlowRequiredInput

- **Qué es:** lo que una etapa del flujo necesita saber antes de avanzar, qué tan bloqueante es y cómo
  se consigue si falta: se deriva, se le pregunta a la persona o la persona lo completa en un archivo.
- **Contexto:** Planning
- **Clasificación:** Domain Policy
- **Identidad:** (`stage`, `inputId`). No se repite en una etapa.
- **Ciclo y estados:** no aplica: es dato de la fábrica. `stage` es `CONTEXT`, `PLANNING` o
  `REFUTATION`, y `classification` es `HARD_BLOCKER`, `SOFT_DEPENDENCY`, `OPTIONAL` o `DERIVABLE`.
- **Invariantes:**
  - solo bloquea lo declarado bloqueante para esa etapa: un `HARD_BLOCKER` bloquea, y un
    `SOFT_DEPENDENCY` o un `OPTIONAL` no;
  - a un `DERIVABLE` no se le pregunta a nadie, tiene `derivableFrom` y es el único sin
    `interactionType`;
  - un `PERSISTENT_CONFIG_INPUT` lleva `persistentTarget` y se completa en un archivo, no en el
    chat; ningún otro lleva `persistentTarget`;
  - el destino nunca es un archivo que genera el harness (`FLOW_INPUT_TARGET_NOT_HUMAN`);
  - una variable del `.env` tiene que estar en `integration-environment-contract`, y su
    sensibilidad sale de ahí, no de acá;
  - `sourceOfTruth` nombra la autoridad que ya existe: el registro la referencia y no la reemplaza;
  - el registro no se usa a medias: si no valida, es `FLOW_REQUIRED_INPUTS_INVALID`.
- **Crea / cambia / lee:** lo escribe la fábrica; lo cargan y lo leen `flujo/requeridos.py`,
  `flujo/precondiciones.py` (que arma las `flowPreconditions` del Plan), `flujo/estado.py`,
  `flujo/interaccion.py` y `flujo/entrada_humana.py`.
- **Persistencia y contrato:** `harnesses/desarrollo/reglas/flow-required-inputs.json`, contra
  `flow-required-inputs.schema.json` (`flow-required-inputs/1.0`), validado al cargar. Se instala con
  el harness y se pisa en cada `-Update`.
- **Dónde vive:** `harnesses/desarrollo/bin/flujo/requeridos.py`.
- **No es:** un ContextGap ni un CapabilityGap. Tampoco es la configuración: dice dónde se completa un
  dato, y el dato sigue en su fuente.

### TaskFlowState

- **Qué es:** el estado del flujo de una Task: en qué etapa está, en qué condición, qué la frena, qué
  le falta a una persona y desde qué compuerta se retoma. Es el estado detallado de la tarea, que la
  integración de Flow Governance separa del estado público del Plan.
- **Contexto:** Planning
- **Clasificación:** Snapshot
- **Identidad:** la TaskKey. Hay uno por Task.
- **Ciclo y estados:**
  - etapas: `CONTEXT`, `PLANNING`, `EXECUTION`, `VERIFICATION`, `REFUTATION` y `COMPLETION`;
  - estados: `NEW`, `ACTIVE`, `BLOCKED`, `WAITING_FOR_HUMAN_APPROVAL`, `INCOMPLETE`, `FAILED`,
    `COMPLETED` y `CANCELLED`. `COMPLETED` y `CANCELLED` son terminales.

  `derivar` no produce hoy ni `VERIFICATION` ni `COMPLETED`: con la refutación en `PASS`, la Task
  queda en `COMPLETION` y `ACTIVE`. `READY_FOR_EXECUTION` no es un estado suyo: es del Plan, y se lee
  en `planRef.planStatus`.
- **Invariantes:**
  - es derivado: `flujo/estado.derivar` lo arma del TaskContext, el Plan, la identidad del
    repositorio, los FlowRequiredInput, la corrida de refutación y las HumanDecisionRecord. Si se
    borra, da el mismo estado lógico, y sin ningún artefacto la Task está en `CONTEXT`, nunca lista;
  - guarda referencias -ruta, hash y huella-, nunca copias;
  - un estado no se declara: `validar_transicion` rechaza un `BLOCKED` o un
    `WAITING_FOR_HUMAN_APPROVAL` sin `blockedOn`, cualquier otro con `blockedOn`, salir de un
    terminal y un cambio de etapa o de estado sin reevaluar las fuentes
    (`FLOW_TRANSITION_INVALID`);
  - un guardado que no valida no se usa ni se repara: es `TASK_FLOW_STATE_INVALID`, y lo reemplaza
    la próxima reconciliación;
  - los permisos no se guardan: `permisos` los deriva cada vez, y avanzar exige un estado que avanza,
    sin `blockedOn`, sin `stale` y vigente;
  - una HumanDecisionRecord `CANCEL` lo deja `CANCELLED`, sin bloqueos.
- **Crea / cambia / lee:** lo escribe solo `estado_de_tarea/persistencia.reconciliar`, que llaman
  `contexto`, `plan`, `refute` y `flujo`. Lo leen `flujo --status`, la compuerta del flujo de
  PreToolUse (`comun/hooks/lib/flow_gate.py`), el aviso del flujo de UserPromptSubmit
  (`comun/hooks/lib/flow_context.py`) y `flujo/interaccion.py`.
- **Persistencia y contrato:** `.claude/runtime/tasks/<KEY>/state.json`, contra
  `task-flow-state.schema.json` (`task-flow-state/1.0`), validado al escribir y al leer, y escrito de
  una vez. El puntero `.claude/runtime/active-task.json` (`active-task/1.0`, un `$defs` del mismo
  schema) nombra la última Task reconciliada y nunca copia su estado.
- **Dónde vive:** `harnesses/desarrollo/bin/flujo/estado.py` y
  `harnesses/desarrollo/bin/estado_de_tarea/persistencia.py`.
- **No es:** el Plan. El `status` del Plan es el estado público de un documento; el del
  TaskFlowState es el del flujo de la Task, y no lo reemplaza ni lo copia. Tampoco es estado de
  ejecución: `EXECUTION` es una etapa que permite delegar, no una corrida.

### HumanIntent

- **Qué es:** lo que una persona decidió en el chat, escrito en una línea exacta
  `HARNESS <ACCION> <KEY> <interactionId> [<opción>]`. Es la prueba de que una decisión la tomó una
  persona y no el modelo.
- **Contexto:** Planning
- **Clasificación:** Entity
- **Identidad:** el `session_id` de la HostSession: hay una por sesión, y la siguiente la pisa.
- **Ciclo y estados:** sin consumir (`consumedAt` en null) y consumida. Su `action` es `APPROVE`,
  `USE_ALTERNATIVE`, `CHOOSE`, `CANCEL` o `ANSWER`; `HARNESS RESUME` no escribe ninguna.
- **Invariantes:**
  - solo la escribe UserPromptSubmit: «dale», «ok» o un comando adentro de un párrafo no son una
    intención;
  - se registra solo sobre una interacción abierta, con una acción y una opción que esa interacción
    acepta, y un valor con forma de secreto se rechaza sin guardarse;
  - se consume una sola vez, con un candado exclusivo, y solo desde la sesión, para la Task, la
    interacción, la acción y la opción que dice;
  - quien la aplica exige además que el estado y el Plan sean los de cuando la persona decidió
    (`stateFingerprint` y `planFingerprint`);
  - no guarda el prompt, ni un secreto, ni una línea del `.env`.
- **Crea / cambia / lee:** la escribe `human_intent.registrar`, en UserPromptSubmit; la consume
  `estado_de_tarea/decisiones.aplicar`, desde `flujo --approve`, `--alternative`, `--choose`,
  `--cancel` o `--answer`; la compuerta del flujo de PreToolUse la verifica antes de dejar pasar
  ese comando.
- **Persistencia y contrato:** `.claude/runtime/sessions/<SAFE_SESSION_ID>/human-intent.json`,
  contra `human-intent.schema.json` (`human-intent/1.0`). En runtime la valida un validador propio,
  `_valido` de `human_intent.py`, que mira las claves, la versión, la sesión y la acción; el schema
  entero lo validan los tests.
- **Dónde vive:** `comun/hooks/lib/human_intent.py`.
- **No es:** una HumanDecisionRecord, que es la decisión ya aplicada. Tampoco es una llamada de
  herramienta del modelo: el modelo puede correr el comando que la aplica, no escribirla.

### HumanDecisionRecord

- **Qué es:** una decisión humana ya aplicada, para auditarla y para reconstruir el estado del flujo
  después de un reinicio.
- **Contexto:** Planning
- **Clasificación:** Record
- **Identidad:** (TaskKey, `interactionId`).
- **Ciclo y estados:** no aplica: se escribe una vez, con la decisión ya aplicada. Su `action` es
  `APPROVE`, `USE_ALTERNATIVE`, `CHOOSE`, `CANCEL` o `ANSWER`.
- **Invariantes:**
  - no existe sin una HumanIntent consumida de la misma sesión, Task, interacción y acción;
  - se valida todo, se consume la intención y recién después se aplica: un corte a la mitad deja la
    intención gastada, nunca aplicada dos veces;
  - `CANCEL` y `CHOOSE` se derivan de acá: un `CANCEL` deja el TaskFlowState `CANCELLED`, y un
    `CHOOSE` elige el repositorio solo si es sobre el mismo `contextHash`;
  - `APPROVE` y `USE_ALTERNATIVE` quedan además en el Plan: pasan la ModelTierApproval a `APPROVED`
    o `DOWNGRADED` y lo replanifican;
  - no guarda el prompt, ni un secreto, ni el razonamiento de nadie.
- **Crea / cambia / lee:** la escribe `estado_de_tarea/decisiones.aplicar`, desde `flujo`; la leen
  `flujo/interaccion.py` (`decisiones`, `cancelada` y `eleccion_de_repositorio`), `flujo/estado.py`
  y `flujo/precondiciones.py`.
- **Persistencia y contrato:** `.claude/runtime/tasks/<KEY>/decisions/<interactionId>.json`, contra
  `human-decision-record.schema.json` (`human-decision-record/1.0`). Al escribirla no se valida
  contra el schema, y al leerla se mira solo la versión y la TaskKey; el schema entero lo validan los
  tests.
- **Dónde vive:** `harnesses/desarrollo/bin/estado_de_tarea/decisiones.py`.
- **No es:** una HumanIntent, ni una SourceAcceptance, ni una ExternalSecurityApproval.

### AgentRegistry

- **Qué es:** la autoridad sobre qué agentes y skills existen, de qué dominio son y en qué estado
  están.
- **Contexto:** Catalog
- **Clasificación:** Aggregate Root
- **Identidad:** el archivo del registro.
- **Ciclo y estados:** se instala. Cada agente y cada skill tienen un estado de validación.
- **Invariantes:** decide si un agente existe, y el disco solo diagnostica. Un dominio tiene un solo
  dueño especialista, y la identidad sale del frontmatter, nunca del nombre del archivo.
- **Crea / cambia / lee:** lo escribe la fábrica; lo valida `registro_agentes.py` en cada plan.
- **Persistencia y contrato:** `harnesses/desarrollo/reglas/agent-registry.json`, contra
  `agent-registry.schema.json` (`agent-registry/1.0`).
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/registro_agentes.py`.
- **No es:** `roster.json`, que guarda los GuardrailCheck por dominio y las capacidades locales.

### Agent

- **Qué es:** un rol especializado al que se le asigna una WorkUnit. Lo corre el Host desde su `.md`.
- **Contexto:** Catalog
- **Clasificación:** Entity
- **Identidad:** `id`, por frontmatter.
- **Ciclo y estados:** `INSTALLED`, `DECLARED_NOT_INSTALLED` o `DEPRECATED` en el registro.
- **Invariantes:** para el plan, existe si el AgentRegistry lo declara válido. El plan no rechaza uno
  desconocido: lo marca con `agentExists: false`.
- **Crea / cambia / lee:** lo declara la fábrica, lo asigna `plan.armar` y lo ejecuta el Host.
- **Persistencia y contrato:** `agents[]` de `agent-registry.schema.json`, y su `.md` en
  `.claude/agents/`.
- **Dónde vive:** los especialistas `dev-*` están en `harnesses/desarrollo/agents/` y los gobierna
  el AgentRegistry. No todo agente instalado está en el registro:
  - `comun/agents/flush-memoria.md` y `comun/agents/leer-docs.md` se instalan y no están declarados;
    en un proyecto instalado el diagnóstico los marca huérfanos;
  - `dev-iniciador-code` está en `harnesses/desarrollo/agents/`, fuera del registro, como huérfano
    reconocido en `huerfanos-reconocidos.json`.

  El plan no se limita al registro. La propuesta puede pedir cualquier `assignedAgent` y el plan
  conserva ese id. El AgentRegistry decide si existe, y si no lo declara, la unidad lleva
  `agentExists: false` y `agentValidation: AGENT_NOT_FOUND` (`plan.py`, `roster.validacion_de_agente`).
  El plan no se rechaza por eso.
- **No es:** una Skill ni una Capability.

### Skill

- **Qué es:** un procedimiento que usa un Agent. No tiene identidad fuera de su dueño en el
  registro.
- **Contexto:** Catalog
- **Clasificación:** Entity
- **Identidad:** `id`, por frontmatter, bajo su agente dueño.
- **Ciclo y estados:** `INSTALLED`, `DECLARED_NOT_INSTALLED` o `DEPRECATED`.
- **Invariantes:** la huella de su archivo es parte de la clave de la caché de refutación.
- **Crea / cambia / lee:** la escribe la fábrica; la carga el agente con la herramienta `Skill` del
  Host.
- **Persistencia y contrato:** `skills[]` de `agent-registry.schema.json`, y su `SKILL.md` en
  `.claude/skills/`.
- **Dónde vive:** las skills `dev-*` están en `harnesses/desarrollo/skills/`, y cada una tiene un
  dueño en el AgentRegistry. `comun/skills/instalar-desde-github` se instala y no está declarada: en
  un proyecto instalado el diagnóstico la marca como no declarada.
- **No es:** un Agent.

### WorkDomain

- **Qué es:** un área de trabajo: backend, frontend, seguridad y las demás de
  `CONTEXTO_POR_DOMINIO`.
- **Contexto:** Catalog
- **Clasificación:** Value Object
- **Identidad:** su nombre.
- **Ciclo y estados:** no aplica.
- **Invariantes:** un dominio desconocido no arma plan, y el de cada WorkUnit está entre los del
  plan.
- **Crea / cambia / lee:** los declara el código; los usan el registro y el plan.
- **Persistencia y contrato:** `domains[]` y `workUnits[].domain` de
  `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/plan.py`.
- **No es:** un NormativeStandard.

### Capability

- **Qué es:** una habilidad con nombre que una WorkUnit necesita y que da una Integration o el
  entorno local.
- **Contexto:** Catalog
- **Clasificación:** Value Object
- **Identidad:** `<a>.<b>[.<c>]` en minúsculas, como `jira.issue.read` o `repository.read`.
- **Ciclo y estados:** depende de la familia.
  - **De integración** (`jira.issue.read`, `gitlab.project.read`…): soportada, si la declara la
    clase de la integración; disponible, si la última validación del entorno la encontró `ENABLED`
    en esta máquina y quedó así en `harness.capacidades.json`. Esa validación es `correr_bootstrap`
    (`dev-harness.py`), y la corren los casos de uso que validan el entorno.
  - **Locales** (`repository.read`, `repository.write`, `repository.search`, `tests.run`): las
    declara `roster.json` en `capacidadesLocales`, y `capacidades.disponibles` las suma siempre.
    Nadie las valida.
- **Invariantes:** las capabilities declaradas, de integración, locales, de permisos y del
  manifiesto, tienen forma de nombre con puntos y ninguna se llama como una HostTool. Pero ningún
  contrato lo impone sobre lo que pide una propuesta: `requiredCapabilities` no tiene patrón. Un
  nombre como `Read` no se rechaza; se vuelve un CapabilityGap (`capacidades.py`), y el plan se
  escribe en `CAPABILITY_RESOLUTION`.
- **Crea / cambia / lee:** la declaran las clases de integración y `roster.json`; la validación del
  entorno (`correr_bootstrap`) valida las de integración, y las locales no pasan por ella; la piden
  las WorkUnits.
- **Persistencia y contrato:** `.claude/harness.capacidades.json`, sin schema, y
  `requiredCapabilities` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/integraciones/registro.py` y
  `harnesses/desarrollo/bin/orquestacion/capacidades.py`.
- **No es:** una HostTool ni una HarnessTool.

### Integration

- **Qué es:** un sistema externo conectado, con su estado y las capacidades que declara.
- **Contexto:** Catalog
- **Clasificación:** Entity
- **Identidad:** `jira` o `gitlab`.
- **Ciclo y estados:** `NOT_CONFIGURED`, `AUTHENTICATION_FAILED`, `CONNECTION_FAILED`,
  `PERMISSION_DENIED` y `AVAILABLE`.
- **Invariantes:** sin configuración no sale a la red, y solo `AVAILABLE` descubre capacidades. La
  clase cumple dos papeles: la conexión, que es Catalog, y el cliente HTTP, que es Infrastructure.
- **Crea / cambia / lee:** la configura la persona en el `.env`, la valida la validación del entorno
  (`correr_bootstrap`), y la usan los resolvedores.
- **Persistencia y contrato:** `integration-environment-contract.schema.json`, y
  `harness.integraciones.json` como proyección sin schema.
- **Dónde vive:** `harnesses/desarrollo/bin/integraciones/`.
- **No es:** un adaptador de contabilidad.

### HarnessTool

- **Qué es:** un artefacto que HARNESS generaría bajo un contrato. Está dormido: nada lo produce.
- **Contexto:** Catalog
- **Clasificación:** Value Object
- **Identidad:** `name` más `version`.
- **Ciclo y estados:** `EXPERIMENTAL`, `TEMPORARY`, `PROMOTION_CANDIDATE`, `APPROVED`, `DEPRECATED` y
  `RETIRED`. Ninguno se escribe.
- **Invariantes:** quien la construye no la aprueba, y se mide con mínimo privilegio contra
  `permisos-por-capacidad.json`.
- **Crea / cambia / lee:** nadie en producción; solo los tests.
- **Persistencia y contrato:** `tool-contract.schema.json` y `tool-registry.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/tools.py` y `registro_tools.py`.
- **No es:** una HostTool ni una Capability.

### DatabaseAccessPolicy

- **Qué es:** la regla que decide, antes de conectar, qué clase de operación sobre una base de datos
  puede correr en cada ambiente: `DEV` con todo, `QA`, `HML` y `PRD` en solo lectura, y lo que no
  está declarado, denegado. Es una capacidad transversal, no una norma. Está dormida: ningún módulo de
  producción la importa.
- **Contexto:** Catalog
- **Clasificación:** Domain Policy
- **Identidad:** la regla de la política se identifica por el ambiente, exacto y sensible a
  mayúsculas: `dev` no es `DEV`. Un perfil se identifica por el par (base lógica, ambiente)
  (`bases.clave_de_perfil`): dos ambientes nunca comparten un perfil.
- **Ciclo y estados:** no aplica. La decisión es `FULL`, `READ_ONLY` o `DENY`
  (`DATABASE_ENVIRONMENT_UNRESOLVED` cuando el ambiente no está declarado).
- **Invariantes:**
  - lo que la política no declara se deniega;
  - la clase de la operación decide el permiso, y su efecto, que es el de `tools.py`, decide el
    riesgo;
  - lo que no se puede clasificar se deniega;
  - el módulo nunca abre una conexión ni pide una credencial.
- **Crea / cambia / lee:** la política la escribe la fábrica, y los perfiles los llena el proyecto
  (vienen vacíos). Los lee `bases.py`, que solo importan los tests.
- **Persistencia y contrato:** `harnesses/desarrollo/reglas/database-environment-access-policy.json`
  contra `database-environment-access-policy.schema.json`, y los perfiles, uno por base lógica y
  ambiente, en `database-profiles.json`, contra `database-profile.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/bases.py`.
- **No es:** una NormativeMatrix ni una Policy. `bases.py` lo dice: no es una regla de ES0901, no
  tiene señal de aplicabilidad, no entra en la matriz normativa y no figura en el registro de
  controles.

### NormativeStandard

- **Qué es:** una norma con su versión: ES0901 6.3, ES0902 y las demás del registro.
- **Contexto:** Governance
- **Clasificación:** Value Object
- **Identidad:** `id` más versión.
- **Ciclo y estados:** no aplica.
- **Invariantes:** una regla se identifica por norma y regla juntas: `ES0901.G1` no es `ES0902.G1`.
- **Crea / cambia / lee:** la declara la fábrica; la citan las matrices, los controles y la
  refutación.
- **Persistencia y contrato:** el campo `standard` de las matrices y de `refutation-unit.schema.json`,
  y `normativeSources` de `control-registry.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/matriz.py` y `seguridad.py`.
- **No es:** una ManagedSource: esa es el documento, y esta es la norma como dato.

### NormativeMatrix

- **Qué es:** las reglas de una norma, con su aplicabilidad y los controles que pide cada una.
- **Contexto:** Governance
- **Clasificación:** Domain Policy
- **Identidad:** norma más versión.
- **Ciclo y estados:** cada fila está `CLASSIFIED` o `UNCLASSIFIED`.
- **Invariantes:** se carga cerrada ante un error. Hay dos catálogos de ES0901, y el plan usa el
  viejo para `applicableStandards`, que por eso sale siempre vacío.
- **Crea / cambia / lee:** la escribe la fábrica; la usan la resolución normativa y la refutación.
- **Persistencia y contrato:** `es0901-7.1-normative-matrix.schema.json`,
  `es0902-normative-matrix.schema.json`, `annex-ii-technology-catalog.schema.json`,
  `gcba-it-normative-baseline.schema.json`, `es0902-cross-standard-map.schema.json`,
  `es0902-security-deliverables.schema.json`. Los datos están en `harnesses/desarrollo/reglas/`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/matriz.py`, `seguridad.py` y `normativa.py`.
- **No es:** el ControlRegistry.

### NormativeRule

- **Qué es:** una regla citable de una norma, con su aplicabilidad y los controles que pide.
- **Contexto:** Governance
- **Clasificación:** Entity
- **Identidad:** `ruleKey`, como `ES0901.G1`.
- **Ciclo y estados:** no aplica. Su aplicabilidad es `ALWAYS` o `CONDITIONAL`.
- **Invariantes:** una señal ausente la deja sin resolver, nunca en "no aplica".
- **Crea / cambia / lee:** la declara la matriz, la resuelve `normativa.resolucion` y la refuta
  `dev-refutador`.
- **Persistencia y contrato:** filas de `es0901-7.1-normative-matrix.schema.json` y de
  `es0902-normative-matrix.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/reglas/es0901-7.1-normative-matrix.json` y
  `harnesses/desarrollo/reglas/es0902-6.2-normative-matrix.json`.
- **No es:** un Control.

### NormativeSignal

- **Qué es:** un hecho sobre la Task o el proyecto que decide si una regla aplica. Su valor sale de
  la evidencia.
- **Contexto:** Governance
- **Clasificación:** Value Object
- **Identidad:** `signalId`.
- **Ciclo y estados:** `TRUE`, `FALSE` o `UNRESOLVED`.
- **Invariantes:** el valor no lo declara quien escribe la señal: se deriva de la evidencia. Las
  fuentes débiles no sostienen un valor.
- **Crea / cambia / lee:** llega en la propuesta o la produce `senales.producir`; la lee la
  resolución normativa.
- **Persistencia y contrato:** `normative-signal.schema.json`, para ES0901 y ES0902. Viaja en
  `workUnits[].normative.signals`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/senales.py`.
- **No es:** Evidence: la usa.

### Applicability

- **Qué es:** si una regla aplica a una WorkUnit.
- **Contexto:** Governance
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** `APPLICABLE`, `NOT_APPLICABLE`, `APPLICABILITY_UNRESOLVED` o
  `APPLICABILITY_EXPRESSION_UNRESOLVED`.
- **Invariantes:** es determinista, y una señal ausente la deja sin resolver.
- **Crea / cambia / lee:** la calcula `resolver_regla`; la lee la refutación.
- **Persistencia y contrato:** `workUnits[].normative` de `orchestration-plan.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/matriz.py`.
- **No es:** un EvaluationResult: dice si aplica, no si se cumple.

### ControlRegistry

- **Qué es:** qué controles existen. El registro declara y el disco diagnostica.
- **Contexto:** Governance
- **Clasificación:** Configuration
- **Identidad:** el archivo.
- **Ciclo y estados:** cada control está `INSTALLED`, `DECLARED_NOT_INSTALLED` o `DEPRECATED`.
- **Invariantes:** nunca dice si un control se cumple. En un proyecto instalado los controles dan
  `CONTROL_FILE_MISSING`, porque `controles/` no se instala.
- **Crea / cambia / lee:** lo escribe la fábrica; lo leen la matriz, el ruteo y la refutación.
- **Persistencia y contrato:** `harnesses/desarrollo/reglas/control-registry.json`, contra
  `control-registry.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/controles.py`.
- **No es:** la lista de GuardrailCheck de `roster.json`.

### Control

- **Qué es:** lo que una regla exige que exista: una Policy, un ControlCheck o una Review.
- **Contexto:** Governance
- **Clasificación:** Entity
- **Identidad:** `id`.
- **Ciclo y estados:** `INSTALLED`, `DECLARED_NOT_INSTALLED` o `DEPRECATED`.
- **Invariantes:** está atado a una norma y a una regla, por `source` o por `normativeSources`.
- **Crea / cambia / lee:** lo declara la fábrica; lo leen la matriz y la refutación.
- **Persistencia y contrato:** `controls[]` de `control-registry.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/controles/`.
- **No es:** un GuardrailCheck.

### Policy

- **Qué es:** un Control de tipo POLICY: un requisito normativo en prosa, con sus resultados
  posibles. No se ejecuta.
- **Contexto:** Governance
- **Clasificación:** Domain Policy
- **Identidad:** el `id` del Control.
- **Ciclo y estados:** los del Control.
- **Invariantes:** es el único sentido canónico de "policy".
- **Crea / cambia / lee:** la escribe la fábrica; la citan la matriz y la persona.
- **Persistencia y contrato:** los `.md` de `harnesses/desarrollo/controles/policies/`, con tipo
  `POLICY` en `control-registry.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/controles/policies/`.
- **No es:** el CostBudget, la política de la RefreshAgenda, la ConsumptionPolicy ni los textos
  libres `policies` del plan.

### ControlCheck

- **Qué es:** un Control de tipo CHECK: `evaluar(...)` devuelve un estado y su evidencia.
- **Contexto:** Governance
- **Clasificación:** Domain Service
- **Identidad:** el `id` del Control.
- **Ciclo y estados:** un check pasa por dos momentos, y no son lo mismo:
  - **declarado por la norma:** su id figura en los `checks` de una regla de la matriz. Puede no
    existir todavía: de los 34 checks que declara la matriz de ES0901, 21 no están en el registro,
    que es el hueco `DECLARED_CHECK_NOT_INSTALLED`;
  - **registrado e instalado:** es un `CHECK` `INSTALLED` del ControlRegistry, con su archivo en
    `controles/checks/`.

  Cada uno de los registrados declara su propia tupla de estados.
- **Invariantes:**
  - los `declaredChecks` de una RefutationUnit llevan lo que declara la norma, esté registrado o no,
    y nunca un GuardrailCheck;
  - solo un ControlCheck registrado e `INSTALLED`, atado a la misma `ruleKey`, con un resultado
    concluyente y al día, puede cerrar una RefutationUnit sin modelo. Un check declarado que no está
    en el registro no puede cerrar nada.
- **Crea / cambia / lee:** lo escribe la fábrica; sus resultados entran por `checks.json`.
- **Persistencia y contrato:** `harnesses/desarrollo/controles/checks/*.py`, con tipo `CHECK` en
  `control-registry.schema.json`. Su resultado entra como `checksInput` de
  `refutation-unit.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/controles/checks/`. `controles/` no se instala, así que en un
  proyecto instalado ningún ControlCheck tiene su archivo.
- **No es:** un GuardrailCheck ni un test de la fábrica.

### CheckSpecification

- **Qué es:** el `.md` que describe un ControlCheck. Es documentación y no se ejecuta.
- **Contexto:** Governance
- **Clasificación:** Configuration
- **Identidad:** su archivo.
- **Ciclo y estados:** no aplica.
- **Invariantes:** sus resultados posibles son los estados del ControlCheck que describe.
- **Crea / cambia / lee:** la escribe la fábrica; ningún código del producto la lee.
- **Persistencia y contrato:** los `es0902-*-check.md` de `harnesses/desarrollo/reglas/`, sin schema.
- **Dónde vive:** `harnesses/desarrollo/reglas/`.
- **No es:** un ControlCheck.

### Review

- **Qué es:** un Control de tipo REVIEW, y el documento que lo resuelve con criterio.
- **Contexto:** Governance
- **Clasificación:** Snapshot
- **Identidad:** `reviewId`.
- **Ciclo y estados:** `COMPLIANT`, `COMPLIANT_WITH_OBSERVATIONS`, `NON_COMPLIANT` o
  `REVIEW_INCOMPLETE`.
- **Invariantes:** una unidad con review no se cierra por check. La puede hacer un agente o una
  persona.
- **Crea / cambia / lee:** no se encontró productor; la valida `revisiones.py`.
- **Persistencia y contrato:** `normative-review.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/revisiones.py`.
- **No es:** un `REVIEW_EVALUATION` del ledger de seguridad.

### Evidence

- **Qué es:** un hecho observado que sostiene una afirmación, atado por ruta, línea o huella. No
  lleva el resultado.
- **Contexto:** Governance
- **Clasificación:** Value Object
- **Identidad:** su huella.
- **Ciclo y estados:** no aplica.
- **Invariantes:** el resultado la referencia por huella, y la evidencia de un veredicto está dentro
  de su alcance.
- **Crea / cambia / lee:** la observan las señales, los checks y el refutador. Los inventarios los
  llena el proyecto a mano.
- **Persistencia y contrato:** los ítems `evidence[]`, y los inventarios del proyecto:
  - `authentication-abuse-protection.schema.json`;
  - `authentication-surface.schema.json`;
  - `base-software-data-disclosure.schema.json`;
  - `browser-session-termination.schema.json`;
  - `client-server-validation-parity.schema.json`;
  - `custom-error-message-evidence.schema.json`;
  - `owasp-security-guidance-review.schema.json`;
  - `public-interface-abuse-protection.schema.json`;
  - `role-profile-consistency.schema.json`;
  - `sensitive-data-transmission.schema.json`;
  - `session-inactivity-timeout.schema.json`.
- **Dónde vive:** los inventarios en `harnesses/desarrollo/reglas/`, y los productores de señales y
  veredictos.
- **No es:** un EvaluationResult.

### EvaluationResult

- **Qué es:** el resultado de evaluar una regla o un control.
- **Contexto:** Governance
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** los de cada evaluación: `COMPLIANT`, `NON_COMPLIANT`, `UNRESOLVED`,
  `OVERRIDDEN`, `NOT_APPLICABLE`, `PASS`, `FAIL` y los propios de cada control.
- **Invariantes:** apunta a la evidencia por huella. `COMPLIANT_WITH_OBSERVATIONS` se vuelve
  `UNRESOLVED` en el resumen.
- **Crea / cambia / lee:** lo producen los ControlCheck, la resolución de ES0902 y la refutación; lo
  lee el resumen de seguridad.
- **Persistencia y contrato:** los campos `state` y `result`, y `normative.rules` de
  `security-summary.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/seguridad.py` y
  `harnesses/desarrollo/controles/checks/`.
- **No es:** Evidence.

### ExternalSecurityApproval

- **Qué es:** evidencia de que una autoridad externa aprobó algo. HARNESS nunca la produce.
- **Contexto:** Governance
- **Clasificación:** External
- **Identidad:** `approvalId`.
- **Ciclo y estados:** `APPROVED`, `REJECTED` u `OFFICIAL_STATUS_UNRESOLVED`.
- **Invariantes:** solo una autoridad externa con evidencia fija un estado oficial, y las fuentes
  locales nunca cuentan.
- **Crea / cambia / lee:** la carga el proyecto a mano; la evalúan `evaluacion.py` y los controles de
  C2 y O2.
- **Persistencia y contrato:** `security-approval-evidence.schema.json` y
  `security-control-authority.schema.json`. Los inventarios vienen vacíos en
  `harnesses/desarrollo/reglas/`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/evaluacion.py`.
- **No es:** una ModelTierApproval.

### Refutation

- **Qué es:** la refutación de un Plan regla por regla, con sus unidades, sus veredictos y su
  agregado.
- **Contexto:** Governance
- **Clasificación:** Aggregate Root
- **Identidad:** la TaskKey.
- **Ciclo y estados:** el agregado queda en `PASS`, `FAIL`, `INCOMPLETE` o `NOTHING_TO_VERIFY`.
- **Invariantes:** se compila desde el Plan leído por la regla de lectura. Un plan rechazado no crea,
  no modifica ni borra nada de la refutación.
- **Crea / cambia / lee:** la compila `refute --compile`, la completa `--record`, y la lee
  `seguridad --refutacion`.
- **Persistencia y contrato:** `.claude/refutaciones/<KEY>/` y `.claude/refutaciones/cache/`, contra
  `refutation-run.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/refutacion.py`.
- **No es:** una ejecución: su "run" es un agregado compilado, sin fechas ni intentos.

### RefutationUnit

- **Qué es:** una afirmación para refutar: (WorkUnit, regla, alcance).
- **Contexto:** Governance
- **Clasificación:** Entity
- **Identidad:** `REF-nnn`, posicional.
- **Ciclo y estados:** `PENDING_SEMANTIC`, `RESOLVED` o `BLOCKED`.
- **Invariantes:** se cierra por check solo con un ControlCheck `INSTALLED` del registro, de la misma
  `ruleKey`, que está en la matriz y en la unidad, con las huellas al día y un estado `PASS` o
  `FAIL`. Sus `declaredChecks` son los checks que declara la norma, registrados o no, y ninguno es un
  GuardrailCheck.
- **Crea / cambia / lee:** la compila `refute --compile`; la recibe `dev-refutador` con `--unit`.
- **Persistencia y contrato:** `.claude/refutaciones/<KEY>/units/REF-nnn.json`, contra
  `refutation-unit.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/refutacion.py` (`compilar_unidades`).
- **No es:** una WorkUnit.

### RefutationVerdict

- **Qué es:** el juicio sobre una RefutationUnit, por un check, por la caché o por `dev-refutador`.
- **Contexto:** Governance
- **Clasificación:** Record
- **Identidad:** `refutationUnitId` más `cacheKey`.
- **Ciclo y estados:** `cumple`, `incumple` o `sin-verificar`.
- **Invariantes:** solo el harness escribe los campos de resolución y las huellas, y solo `cumple` e
  `incumple` se reutilizan desde la caché.
- **Crea / cambia / lee:** lo escribe `dev-refutador`, que es un modelo, y lo valida `--record`; lo
  arman también un check o la caché; lo lee `seguridad --refutacion`.
- **Persistencia y contrato:** `.claude/refutaciones/<KEY>/verdicts/` y `cache/`, contra
  `refutation-verdict.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/refutacion.py`.
- **No es:** un veredicto del método SDD de la fábrica.

### Finding

- **Qué es:** un hallazgo de governance con estado: de integridad, de una Review o de ES0902.
- **Contexto:** Governance
- **Clasificación:** Record
- **Identidad:** `findingId`.
- **Ciclo y estados:** los de cada tipo. El de integridad: `SUSPICIOUS_BEHAVIOR_DETECTED`,
  `MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE` o `REVIEW_INCOMPLETE`.
- **Invariantes:** el de integridad pide revisión humana. La línea base de integridad está dormida.
- **Crea / cambia / lee:** lo produce `integridad.hallazgo`, en memoria; no tiene camino de CLI.
- **Persistencia y contrato:** `repository-integrity-finding.schema.json` y, dormida,
  `trusted-repository-baseline.schema.json`; también `findings[]` de las reviews.
- **Dónde vive:** `harnesses/desarrollo/bin/orquestacion/integridad.py`.
- **No es:** un GuardrailFinding.

### EvaluationRecord

- **Qué es:** un resultado de evaluación registrado con las huellas de su evidencia.
- **Contexto:** Governance
- **Clasificación:** Record
- **Identidad:** `eventId`.
- **Ciclo y estados:** doce tipos de evento, dos de ellos con camino de CLI.
- **Invariantes:** el productor no decide un resultado. Cada evento nombra a su productor, de una
  lista cerrada, y las huellas de su evidencia.
- **Crea / cambia / lee:** lo escriben `seguridad --conocimiento` y `seguridad --refutacion`; lo lee
  el resumen de seguridad.
- **Persistencia y contrato:** `.claude/runtime/security/<KEY>/security-ledger.ndjson`, contra
  `security-ledger-event.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/reporte_seguridad/`.
- **No es:** un Domain Event ni un AccountingEvent.

### SecuritySummary

- **Qué es:** el estado de seguridad de una Task, armado desde los EvaluationRecord.
- **Contexto:** Governance
- **Clasificación:** Snapshot
- **Identidad:** `snapshotFingerprint`.
- **Ciclo y estados:** `systemSecurityState`, `assessmentState` y `officialApprovalStatus`.
- **Invariantes:** nunca dice que hay aprobación oficial sin evidencia externa.
- **Crea / cambia / lee:** lo escribe `seguridad --resumen`; el reporte lo presenta en md y html.
- **Persistencia y contrato:** `.claude/runtime/security/<KEY>/security-summary.json`, contra
  `security-summary.schema.json`; su presentación, `security-report.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/reporte_seguridad/resumen.py`.
- **No es:** una ExternalSecurityApproval.

### SecretGate

- **Qué es:** la única regla que bloquea: un secreto que se va a escribir o ejecutar da `deny` o
  `ask`. La complementa `permissions.deny`, que impide leer.
- **Contexto:** Guardrails
- **Clasificación:** Domain Service
- **Identidad:** no aplica.
- **Ciclo y estados:** `deny`, `ask` o pasa, en cada llamada.
- **Invariantes:** solo los secretos bloquean. Corre en PreToolUse y sale con 0 siempre.
- **Crea / cambia / lee:** lo corre el Host antes de Write, Edit, MultiEdit, NotebookEdit, Bash y
  PowerShell.
- **Persistencia y contrato:** el catálogo `comun/reglas/secretos.patrones.json`, sin schema.
- **Dónde vive:** `comun/hooks/pre-tool-use.py` y `comun/hooks/lib/secretos.py`.
- **No es:** un GuardrailCheck.

### GuardrailCheck

- **Qué es:** un check del hook: `verificar(evento, proyecto, config) -> [str]`, en PostToolUse.
  Avisa y nunca bloquea.
- **Contexto:** Guardrails
- **Clasificación:** Domain Service
- **Identidad:** su archivo.
- **Ciclo y estados:** no aplica: no guarda estado.
- **Invariantes:** devuelve textos, como mucho ocho por evento; uno que revienta se saltea; el hook
  sale con 0.
- **Crea / cambia / lee:** lo escribe la fábrica y lo corre PostToolUse, que recorre la carpeta
  `checks/` instalada. Los de un dominio viajan por nombre en los `requiredChecks` de la WorkUnit.
- **Persistencia y contrato:** no tiene schema. Hay dos fuentes:
  - `comun/checks/`, con `claude-md-zonas.py`, que corre siempre y no figura en `roster.json`;
  - `harnesses/desarrollo/checks/`, con los `dev-*`, que son los que lista `checks` en
    `harnesses/desarrollo/reglas/roster.json` por dominio.

  Los dos se instalan en `.claude/harness/checks/` y `checks/desarrollo/`.
- **Dónde vive:** `comun/checks/` y `harnesses/desarrollo/checks/`.
- **No es:** un ControlCheck ni un test de la fábrica.

### GuardrailFinding

- **Qué es:** un aviso de texto de un GuardrailCheck.
- **Contexto:** Guardrails
- **Clasificación:** Value Object
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** como mucho ocho por evento, y llegan al modelo como `additionalContext`.
- **Crea / cambia / lee:** lo devuelve un GuardrailCheck; lo lee el modelo en el turno siguiente.
- **Persistencia y contrato:** no aplica: no persiste.
- **Dónde vive:** `comun/hooks/lib/reglas.py`.
- **No es:** un Finding de governance.

### SessionFlowNotice

- **Qué es:** la huella del último aviso del flujo que UserPromptSubmit le dio a una sesión -una
  Task que no puede avanzar, o una sesión sin una Task clara-, para no repetir el bloque entero.
- **Contexto:** Guardrails
- **Clasificación:** Infrastructure
- **Identidad:** el `session_id` de la HostSession. Hay una por sesión.
- **Ciclo y estados:** no tiene estados. Se pisa con cada aviso nuevo, y se borra cuando la Task de
  la sesión vuelve a poder avanzar.
- **Invariantes:** con la misma huella el aviso sale en una línea, y con otra sale el bloque entero.
  `fingerprint` es un SHA-256 de la Task, la etapa, el estado, los bloqueos, la vigencia, la
  interacción pendiente y su ubicación, y no lleva ninguno en claro. Solo cambia qué se muestra: no
  decide nada.
- **Crea / cambia / lee:** la escribe, la lee y la borra `flow_context.del_turno`, en
  UserPromptSubmit.
- **Persistencia y contrato:** `.claude/runtime/sessions/<SAFE_SESSION_ID>/notice.json`, contra
  `session-flow-notice.schema.json` (`session-flow-notice/1.0`). En runtime se miran solo la versión
  y el `sessionId`, y ningún test valida un `notice.json` contra el schema.
- **Dónde vive:** `comun/hooks/lib/flow_context.py`.
- **No es:** un GuardrailFinding ni un TaskFlowState: guarda que se avisó, no qué.

### AccountingEvent

- **Qué es:** algo observado del consumo de modelo de una sesión o de una Task: tokens, costo,
  tiempo, ventana de contexto.
- **Contexto:** Observability
- **Clasificación:** Record
- **Identidad:** `eventId`, que es `ev_` más el sha256 de adaptador, tipo y dedupKey.
- **Ciclo y estados:** hay catorce tipos y se producen tres:
  - `MODEL_CALL_COMPLETED`;
  - `SESSION_COMPLETED`, que es la foto acumulada del proveedor;
  - `CONTEXT_WINDOW_OBSERVED`, que no se suma.
- **Invariantes:** es append-only, y nada fuera de Observability lo lee para decidir. No es estado de
  ejecución.
- **Crea / cambia / lee:** lo escriben la `statusLine` y `contabilidad --ingerir`; lo leen el
  agregador y la barra.
- **Persistencia y contrato:** `.claude/runtime/accounting/<LedgerKey>/ledger.jsonl`, contra
  `execution-accounting-event.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/contabilidad/`.
- **No es:** un Domain Event ni estado de ejecución.

### LedgerKey

- **Qué es:** la clave de un ledger de contabilidad: una TaskKey, o el `session_id` de una
  HostSession.
- **Contexto:** Observability
- **Clasificación:** Value Object
- **Identidad:** su valor.
- **Ciclo y estados:** no aplica.
- **Invariantes:** el CLI acepta una TaskKey o un UUID de sesión, y rechaza lo demás. La
  `statusLine` escribe por el `session_id` que manda el Host.
- **Crea / cambia / lee:** la pasa la persona al CLI, o el Host a la `statusLine`; la valida
  `libro.validar_clave`.
- **Persistencia y contrato:** el `taskId` de `execution-accounting-event.schema.json` y el nombre de
  la carpeta del ledger.
- **Dónde vive:** `harnesses/desarrollo/bin/contabilidad/libro.py`.
- **No es:** siempre una TaskKey.

### AccountingSummary

- **Qué es:** los totales de un ledger, conciliados contra el proveedor.
- **Contexto:** Observability
- **Clasificación:** Snapshot
- **Identidad:** la LedgerKey.
- **Ciclo y estados:** no aplica: se regenera al agregar.
- **Invariantes:** las filas, más lo no atribuido, suman el total.
- **Crea / cambia / lee:** lo escribe el agregador; lo leen el reporte y el resumen de seguridad.
- **Persistencia y contrato:** `summary.json`, que declara `execution-summary/1.0` sin archivo de
  schema.
- **Dónde vive:** `harnesses/desarrollo/bin/contabilidad/agregacion.py`.
- **No es:** estado de ejecución.

### CostBudget

- **Qué es:** los umbrales de contexto y los límites de plata del proyecto. Su evaluación es
  evidencia, nunca un permiso.
- **Contexto:** Observability
- **Clasificación:** Configuration
- **Identidad:** `policyId`.
- **Ciclo y estados:** no aplica. Sin límite declarado, la evaluación da `BUDGET_UNDEFINED`.
- **Invariantes:** no aprueba nada, y el `-Update` no lo pisa.
- **Crea / cambia / lee:** lo siembra el instalador si falta; lo cambian la persona y
  `presupuesto --context-defaults`; lo leen la barra y `contabilidad`.
- **Persistencia y contrato:** `.claude/harness.presupuesto.json`, contra `budget-policy.schema.json`.
- **Dónde vive:** `harnesses/desarrollo/bin/contabilidad/presupuesto.py`.
- **No es:** la ConsumptionPolicy.

### ContextBarState

- **Qué es:** lo que dibuja la Context Bar: modelo, contexto, presupuesto y tiempo.
- **Contexto:** Observability
- **Clasificación:** Snapshot
- **Identidad:** no aplica.
- **Ciclo y estados:** los niveles de contexto y de presupuesto.
- **Invariantes:** un dato que no se tiene no aparece, y nunca muestra más de 100%.
- **Crea / cambia / lee:** lo arma `barra.de`; lo dibuja la `statusLine`.
- **Persistencia y contrato:** no aplica: no persiste. Su señal de vida es parte de la Installation.
- **Dónde vive:** `harnesses/desarrollo/bin/contabilidad/barra.py` y `statusline.py`.
- **No es:** la Installation.

### Installation

- **Qué es:** el estado del harness en un proyecto: versión, bootstrap y salud de sus componentes.
- **Contexto:** Host Integration
- **Clasificación:** Aggregate Root
- **Identidad:** el proyecto. `harnessId` vale `"desarrollo"`.
- **Ciclo y estados:** el bootstrap queda en `READY`, `PARTIAL` o `BLOCKED`.
- **Invariantes:** un componente que no está `ACTIVE` deja la instalación `PARTIAL`, nunca `BLOCKED`.
  Lo de `.claude/harness/` se regenera entero.
- **Crea / cambia / lee:** lo escribe `bienvenida.registrar_instalacion`, desde el instalador y desde
  SessionStart; lo leen la bienvenida, `harness` y `-Doctor`.
- **Persistencia y contrato:** `.claude/harness.installation.json`, con el contrato
  `harness-installation-state.schema.json` (`harness-installation/1.1`). En runtime, la bienvenida no
  valida contra ese archivo: valida contra una copia en línea, `FORMA_INSTALACION` de
  `bienvenida.py`, a la que le falta `integrationConfiguration`. El archivo de schema lo usan solo
  los tests. La duplicación ya está anotada como deuda. El inventario está en
  `.claude/harness.lock.json`.
- **Dónde vive:** `comun/hooks/lib/bienvenida.py` e `install.ps1`.
- **No es:** NormativeKnowledge, aunque proyecte su estado.

### RuntimeComponentHealth

- **Qué es:** si un componente (Block 4, Context Bar, Security Reporting) está `ACTIVE`, y por qué
  no.
- **Contexto:** Host Integration
- **Clasificación:** Value Object
- **Identidad:** el nombre del componente.
- **Ciclo y estados:** la Context Bar tiene ocho estados, entre ellos `RELOAD_REQUIRED` y `ACTIVE`.
- **Invariantes:** la Context Bar está `ACTIVE` solo con una señal de vida de la sesión actual que
  tenga la misma huella.
- **Crea / cambia / lee:** lo calcula la bienvenida; lo lee la persona.
- **Persistencia y contrato:** `runtimeComponents` de `harness-installation-state.schema.json`. La
  señal de vida está en `.claude/runtime/contextbar.json`.
- **Dónde vive:** `comun/hooks/lib/bienvenida.py`.
- **No es:** un AccountingEvent.

### HarnessConfig

- **Qué es:** la configuración del proyecto, sembrada desde `manifest.json` y que después no se toca
  nunca.
- **Contexto:** Host Integration
- **Clasificación:** Configuration
- **Identidad:** el proyecto.
- **Ciclo y estados:** no aplica.
- **Invariantes:** el instalador la crea solo si falta, y los proyectos instalados no reciben claves
  nuevas.
- **Crea / cambia / lee:** la siembra el instalador, la cambia la persona, y la leen el CLI y los
  hooks.
- **Persistencia y contrato:** `.claude/harness.config.json` y `manifest.json`, sin schema.
- **Dónde vive:** `install.ps1` y `manifest.json`.
- **No es:** el `.env`.

### Host

- **Qué es:** Claude Code. No es un concepto de dominio: es el sistema que aloja al producto, y cumple
  seis papeles:
  1. host de los hooks;
  2. UI, con la `statusLine` y el `systemMessage`;
  3. runtime de agentes y skills;
  4. proveedor de herramientas;
  5. proveedor de la transcripción;
  6. acceso al modelo.
- **Contexto:** External
- **Clasificación:** External
- **Identidad:** no aplica.
- **Ciclo y estados:** no aplica.
- **Invariantes:** HARNESS no llama a ningún modelo ni lanza agentes: lo hace el Host.
- **Crea / cambia / lee:** corre los hooks y la `statusLine`, ejecuta los agentes y las skills, da
  las herramientas y escribe la transcripción.
- **Persistencia y contrato:** no aplica. Se filtra en `contextWindow.source` =
  `CLAUDE_CODE_STATUSLINE` de `execution-accounting-event.schema.json` y en el bloque `contextBar` de
  `harness-installation-state.schema.json`.
- **Dónde vive:** fuera del repo. Lo traducen `comun/hooks/lib/hook.py`,
  `harnesses/desarrollo/bin/contabilidad/adaptadores/claude_code.py` y `statusline.py`.
- **No es:** HARNESS.

### HostSession

- **Qué es:** una sesión de Claude Code.
- **Contexto:** External
- **Clasificación:** External
- **Identidad:** `session_id`, un UUID.
- **Ciclo y estados:** los del Host.
- **Invariantes:** es la LedgerKey del ledger de la barra mientras no se declare una Task.
- **Crea / cambia / lee:** la crea el Host; la usan la `statusLine` y la bienvenida.
- **Persistencia y contrato:** `sessionId` de `execution-accounting-event.schema.json`.
- **Dónde vive:** fuera del repo.
- **No es:** una Task.

### HostTool

- **Qué es:** una herramienta de Claude Code: Read, Write, Edit, Bash, PowerShell y las demás.
- **Contexto:** External
- **Clasificación:** External
- **Identidad:** su nombre.
- **Ciclo y estados:** no aplica.
- **Invariantes:** ninguna capability declarada lleva su nombre. Nada impide que una propuesta pida
  una con ese nombre: queda como CapabilityGap, no como una herramienta.
- **Crea / cambia / lee:** la da el Host; la nombran los matchers de los hooks y el `tools:` de los
  agentes.
- **Persistencia y contrato:** no aplica. `comun/settings/hooks.plantilla.json` las nombra en sus
  matchers.
- **Dónde vive:** fuera del repo.
- **No es:** una Capability ni una HarnessTool.

## Mapa de contextos

HARNESS tiene **nueve contextos delimitados**. Cada uno se justifica por su lenguaje, sus
invariantes, su dueño, sus datos y su ciclo de vida.

| Contexto | Lenguaje propio | Invariantes propias | Dueño | Datos | Ciclo de vida |
|---|---|---|---|---|---|
| Work Intake | tarea, Ficha, adjunto, procedencia, sección, hueco, vínculo de sesión | TaskKey, Jira obligatorio, procedencia, redacción; una sesión trabaja la Task que declaró | sin dueño declarado | `.claude/contextos/`, `.claude/runtime/sessions/<SAFE>/task.json` | por Task, se regenera entero; el vínculo, por sesión |
| Project Knowledge | zona, techo, ficha de módulo, índice | write-back antes de desalojar; regeneración entera | el equipo del proyecto | `CLAUDE.md`, `docs/conocimiento/`, `docs/codebase/` | lo cambian personas y modelos |
| Normative Sources | fuente, versión, sha256, canal, aceptar, vigente | identidad por el registro; aceptación por una persona; frescura relativa al canal | sin dueño declarado | `source-registry.json`, `.claude/harness.fuentes.json`, `runtime/knowledge-refresh.json` | observar, aceptar, vigente |
| Planning | plan, propuesta, unidad, dominio, tier, aprobación, hueco, etapa, bloqueo, intención, decisión | las del Plan; un estado del flujo no se declara; una decisión humana no la toma el modelo | sin dueño declarado | `.claude/planes/`, `.claude/runtime/tasks/`, `reglas/flow-required-inputs.json`, `.claude/runtime/sessions/<SAFE>/human-intent.json` | por Task y por versión; el estado del flujo, en cada reconciliación |
| Catalog | agente, skill, dominio, capacidad, integración, disponible, ambiente | registro autoritativo; forma de las capabilities declaradas; lo no declarado se deniega en una base | sin dueño declarado | `agent-registry.json`, `roster.json`, `.claude/harness.capacidades.json`, `database-environment-access-policy.json` | se instala; la disponibilidad de las integraciones la decide la validación del entorno (`correr_bootstrap`) |
| Governance | regla, señal, aplicabilidad, control, evidencia, resultado, veredicto | las de los controles, las señales y la refutación | sin dueño declarado | `reglas/`, `.claude/refutaciones/`, `runtime/security/` | por Task y por versión de la norma |
| Guardrails | evento, herramienta, hallazgo, deny, ask | solo los secretos bloquean; hasta ocho avisos; salida 0 | `harness-hook-engineer` | `comun/reglas/secretos.patrones.json`, los checks, `.claude/runtime/sessions/<SAFE>/notice.json` | por llamada de herramienta, sin estado; la huella del aviso del flujo, por sesión |
| Observability | evento, tokens, costo, ventana, conciliación, presupuesto | id por dedupKey; las fotos no se suman; nadie decide con el ledger | sin dueño declarado | `.claude/runtime/accounting/`, `harness.presupuesto.json` | append-only |
| Host Integration | instalar, actualizar, lock, huella, reinicio, componente | lo regenerable no se edita; lo de fuera sobrevive; PARCIAL y no BLOQUEADO | `harness-backend-engineer` | `.claude/harness/`, `harness.lock.json`, `harness.installation.json` | instalación, `-Update`, `-Uninstall` |

**Execution no es un contexto: es un límite reservado.** No tiene lenguaje, ni datos, ni
invariantes, ni ciclo de vida, ni implementación. Está nombrado para que la próxima Task sepa dónde
va la ejecución, y está vacío: ningún concepto lo tiene como contexto. Ver
`## El límite de la ejecución`.

### Relaciones

| Relación | Tipo | Qué cruza |
|---|---|---|
| Work Intake → Planning | Cliente-proveedor | El TaskContext. Planning se conforma a `task-context/1.0` |
| Catalog → Planning | Conformista | Planning acepta lo que dice el registro: agentes, skills y capacidades |
| Governance ⇄ Planning | Partnership, con ciclo | El Plan lleva la resolución normativa adentro de cada WorkUnit, y la refutación se compila desde el Plan |
| Normative Sources → Governance y Planning | Cliente-proveedor | La decisión de la compuerta normativa, antes de `plan`, `refute --compile` y `seguridad` |
| Host → Guardrails y Observability | Capa anticorrupción | `comun/hooks/lib/hook.py`, `adaptadores/claude_code.py` y `statusline.py` traducen lo de Claude Code |
| Work Intake y Planning → Guardrails | Cliente-proveedor | El SessionTaskBinding dice qué Task mira la compuerta del flujo de los hooks, y el TaskFlowState si puede avanzar. Los hooks leen el estado del flujo y no lo derivan |
| Governance → Observability | Publicación | La refutación arma la metadata de atribución de la contabilidad |
| Host Integration → todos | Proveedor de instalación | Copia, registra y mide la salud, sin interpretar el dominio de nadie |

## Clasificaciones

La lista es cerrada. Ningún concepto se clasifica fuera de ella.

| Clasificación | Cuándo, en este repo |
|---|---|
| Aggregate Root | Hay invariantes que se validan sobre el todo antes de escribir. El Plan es el caso fuerte |
| Entity | Tiene identidad propia y vive adentro de un agregado o de un registro |
| Value Object | Se define por su valor y no tiene identidad propia |
| Snapshot | Un documento derivado que se regenera entero y no se modifica en partes |
| Record | Una constancia append-only de algo observado o decidido |
| Domain Service | Una decisión del dominio en código, sin estado |
| Domain Policy | Una regla del dominio expresada como dato o como procedimiento |
| Application Service | Un subcomando de `dev-harness.py` que orquesta un caso de uso |
| DTO / Contract | Una entrada o salida sin autoridad |
| Configuration | Datos o parámetros que no deciden nada solos |
| External | Vive fuera de HARNESS, y HARNESS solo lo lee o lo usa |
| Infrastructure | Cómo se guarda, se valida o se transporta algo |

Lo que no se usa, y por qué:

- **Domain Event.** Ningún código de HARNESS reacciona a un evento. Los NDJSON son constancias, de
  observabilidad o de evidencia. `FINDING_CREATED`, `FINDING_UPDATED` y `FINDING_RESOLVED` son lo más
  parecido, y nadie los consume.
- **Repository.** Cada agregado se guarda en un archivo con su ruta conocida.
- **Factory.** `plan.armar` y `refutacion.compilar_unidades` ya cumplen ese papel.

## Lo que no es lo mismo

### Task ≠ WorkUnit

Una Task tiene un Plan con N WorkUnits. La Task es externa, y la WorkUnit existe solo adentro del
Plan: `harnesses/desarrollo/bin/orquestacion/plan.py`.

### TaskContext ≠ Knowledge

El TaskContext es un snapshot de la tarea; NormativeKnowledge es lo aceptado de las fuentes. Un
adjunto que no está en el registro es documentación del contexto, no una fuente gestionada
(`comun/schemas/source-registry.schema.json`). La palabra se cruza en `knowledge_status`, que es
SectionConfidence.

### Knowledge ≠ Source

Una ManagedSource es la identidad de un documento. NormativeKnowledge es lo que quedó `CURRENT`
después de observar y aceptar: `harnesses/desarrollo/bin/orquestacion/frescura.py`.

### Capability ≠ Tool

Son conceptos con significado y dueño distintos. Una Capability es una habilidad con nombre: la
declaran las integraciones y el roster, y la pide una WorkUnit. Una HostTool es una herramienta que
da Claude Code. Hoy ninguna capability declarada se llama como una HostTool, pero no hay ninguna
restricción contractual que impida usar el mismo texto: `requiredCapabilities` no tiene patrón, y una
propuesta que pide `Read` no se rechaza. Ese nombre queda como CapabilityGap y el plan se escribe en
`CAPABILITY_RESOLUTION` (`harnesses/desarrollo/bin/orquestacion/capacidades.py`). HarnessTool es una
tercera cosa, dormida.

### Agent ≠ Skill

El registro separa los agentes de las skills de cada dueño
(`harnesses/desarrollo/reglas/agent-registry.json`). El Host carga los dos como markdown, pero no son
lo mismo.

### Agent ≠ Capability

El agente es un rol. La capacidad la pide la WorkUnit y la da una Integration o el entorno. Nada
liga el `tools:` de un agente con las capacidades:
`harnesses/desarrollo/agents/dev-orchestrator.md`.

### Policy ≠ Check

POLICY y CHECK son tipos distintos del registro (`comun/schemas/control-registry.schema.json`). Los
datos actuales de G2 declaran el mismo id, `security-vulnerability-acceptance-threshold`, como las dos
cosas. Eso no es una excepción del modelo: es un defecto de los datos, y el producto lo trata así.
`seguridad.colisiones_de_id` lo diagnostica como `SECURITY_CONTROL_ID_TYPE_COLLISION`, y el módulo
dice que la matriz no se corrige acá: se arregla en origen
(`harnesses/desarrollo/bin/orquestacion/seguridad.py`). Hoy ese diagnóstico solo lo llaman los
tests, y ningún comando lo emite. La deuda está en
`Pendientes/Fix-Harness/PENDIENTES-FH.md`, en *The provided ES0902 matrix declares one control id with
two types*.

### Check ≠ development test

Los tres se distinguen por contrato, ciclo de vida, dueño y mecanismo, no por si se instalan:

- **GuardrailCheck:** `verificar(evento, proyecto, config) -> [str]`. Corre en los eventos
  PostToolUse que alcanza el matcher configurado, hoy `Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`
  (`comun/settings/hooks.plantilla.json`), sin guardar estado; su dueño es `harness-hook-engineer`. Es parte del
  producto instalado: va a `.claude/harness/checks/`.
- **ControlCheck:** `evaluar(...)` devuelve un estado y su evidencia. Es de Governance: lo declaran el
  ControlRegistry y las matrices, y sus resultados entran a la refutación por `checks.json`. Su
  implementación vive en `harnesses/desarrollo/controles/checks/`, y hoy `controles/` no se instala:
  es deuda conocida.
- **Test de la fábrica:** un caso de `tests/casos/` que corre `tests/correr.py` o `Invoke-Tests.ps1`
  en este repositorio. Verifica la fábrica y nunca llega a un proyecto.

### Evidence ≠ Result

La Evidence no lleva el resultado. Un EvaluationRecord tiene `result` y `evidenceFingerprints` por
separado: `comun/schemas/security-ledger-event.schema.json`.

### Plan ≠ Execution

`READY_FOR_EXECUTION` es un estado del documento
(`harnesses/desarrollo/bin/orquestacion/__init__.py`). No existe ninguna ejecución.

### Execution ≠ Accounting

`execution-accounting-event` reconstruye la actividad de la sesión desde la transcripción y la
`statusLine`, y ningún orquestador emite nada:
`harnesses/desarrollo/bin/contabilidad/statusline.py`.

### Result ≠ Evidence

Es la misma desigualdad vista desde el otro lado: en la refutación, el veredicto cita evidencia
dentro de su alcance (`harnesses/desarrollo/bin/orquestacion/refutacion.py`).

### Claude Code ≠ HARNESS

Claude Code es el Host. HARNESS no llama a ningún modelo, no lanza agentes y no tiene runtime propio:
el único `subprocess` es `git` o `markitdown` (`harnesses/desarrollo/bin/contexto/documentos.py`).

### Task ≠ HostSession

En el ledger de la barra, la clave es el `session_id` de la sesión
(`harnesses/desarrollo/bin/contabilidad/statusline.py`). Por eso existe la LedgerKey: una TaskKey o
una sesión, y no siempre una Task.

## Vocabulario

| Término actual | Dónde | Qué significa hoy | Nombre canónico |
|---|---|---|---|
| tarea / task / ticket / issue / HU / historia | `tarea.py`, `dev-harness.py`, `docs/contexto-de-tarea.md` | el trabajo pedido, o su registro en Jira | **Task** si es el trabajo; **TaskRecord** si es el issue |
| `task.key` / `task_key` / `taskKey` / clave | task-context, plan, refutación, CLI | la identidad | **TaskKey** |
| `taskId` | contabilidad y seguridad | la tarea, o el id de sesión en la barra | **LedgerKey** en contabilidad; **TaskKey** en seguridad |
| propuesta / proposal | `dev-harness.py`, `dev-orchestrator.md` | la entrada de `plan` | **PlanProposal** |
| plan / orchestration plan / plan de ejecución | schema, bienvenida | el documento | **Plan**; "plan de ejecución" se lee como si ejecutara, y no ejecuta |
| `workUnits` / unidad de trabajo / WorkUnit | plan, prosa | la porción de la Task | **WorkUnit** |
| unidad / unit | `refutacion.py`, `contabilidad/reporte.py` | una WorkUnit o una RefutationUnit | se nombra cuál: **WorkUnit** o **RefutationUnit** |
| step / paso / etapa | skills, resolvedores | un paso de un procedimiento | no es un concepto |
| `requiredChecks` | `plan.py` | los checks del hook del dominio | **GuardrailCheck**; el campo no cambia de nombre |
| `declaredChecks` | matriz, plan, refutación | los controles CHECK de la regla | **ControlCheck** |
| check | cuatro sentidos | el del hook, el control CHECK, su especificación y la entrada `checks.json` | **GuardrailCheck**, **ControlCheck** o **CheckSpecification** |
| control | registro, autoridad O2, `controlResults` | lo que una regla exige que exista | **Control**; "la autoridad de control" es **ExternalSecurityApproval** |
| policy / política | cinco sentidos | el control POLICY y cuatro configuraciones | **Policy** solo para el Control de tipo POLICY; **CostBudget**, **RefreshAgenda**, **ConsumptionPolicy** y **DatabaseAccessPolicy** para las otras cuatro |
| `policies` / `applicablePolicies` del plan | `plan.py` | textos libres de la propuesta, sin validar | no es un concepto |
| review | siete sentidos | el control REVIEW y su documento, entre otros | **Review**; `REVIEW_EVALUATION` es un **EvaluationRecord** |
| verdict / veredicto | seis sentidos | el de la refutación, la decisión de la compuerta y otros | **RefutationVerdict**; la compuerta da una decisión de la **NormativeFreshnessGate** |
| finding / hallazgo | once sentidos | hallazgos con estado y avisos de texto | **Finding** si tiene estado; **GuardrailFinding** si es el texto de un hook |
| evidence / evidencia | once sentidos | lo observado | **Evidence**; `controles/lib/evidencia.py` es infraestructura |
| result / resultado / outcome | controles, resumen, OWASP | el estado de una evaluación | **EvaluationResult** |
| salida / output | variables locales, tokens de salida | — | no es un concepto |
| approval / aprobación | seis sentidos | costo, seguridad externa, fuentes y herramientas | **ModelTierApproval**, **ExternalSecurityApproval** o **SourceAcceptance**; el `HUMAN_APPROVAL_REQUIRED` del presupuesto es una evaluación del **CostBudget** |
| source / fuente | siete sentidos | documento, canal, procedencia y otros | **ManagedSource**, **Channel** o **ProvenanceRef** |
| knowledge / conocimiento | cuatro sentidos | normas, notas, confianza de sección y Ficha | **NormativeKnowledge**, **ProjectMemory**, **SectionConfidence** o **Ficha** |
| contexto / context | cinco sentidos | tarea, proyecto, recorte, ventana y SessionStart | **TaskContext**, **ProjectContext**, **ContextSlice** o **ContextBarState** |
| ficha | Jira y `docs/codebase` | la Ficha de Proyecto, o una ficha de módulo | **Ficha**; la ficha de módulo es parte del **ProjectContext** |
| proyecto | cuatro sentidos | clave de Jira, proyecto de GitLab, raíz local y `project_id` | **ProjectContext** para `project_id`; los otros tres se nombran por lo que son |
| adaptador / adapter | integraciones y contabilidad | dos cosas | **Integration**; el adaptador de contabilidad es infraestructura |
| caché | zona CACHÉ y caché de refutación | dos cosas | zona de **ProjectMemory**; caché de la **Refutation** |
| execution / ejecución | `execution-accounting-event`, "contabilidad de ejecución" | la actividad de la sesión | **AccountingEvent**; el nombre del archivo no cambia |
| run / corrida | refutación, una invocación del CLI | el agregado de la refutación, o una invocación | **Refutation**; una invocación no es un concepto |
| `SESSION_COMPLETED` | `contrato.py` | la foto acumulada del proveedor | un tipo de **AccountingEvent**; no cambia de nombre |
| `PENDING` de una unidad | `plan.py` | planificada, sin nada que la frene | un estado de **WorkUnit** |
| estado de la tarea / estado del flujo / `task-flow-state` | `flujo/estado.py`, `flujo --status` | la etapa y la condición de la tarea | **TaskFlowState**; el `status` del documento de plan es del **Plan** |
| input requerido / precondición del flujo | `flow-required-inputs.json`, `flowPreconditions` | lo que una etapa necesita antes de avanzar | **FlowRequiredInput**; su evaluación queda en el **Plan** y en el **TaskFlowState** |
| intención / intent / `HARNESS <ACCION>` | `human_intent.py`, `flujo` | lo que la persona escribió en el chat para decidir | **HumanIntent** mientras no se aplicó; **HumanDecisionRecord** cuando ya se aplicó |
| binding / vínculo / tarea de la sesión | `task_binding.py`, los hooks | qué tarea trabaja una sesión | **SessionTaskBinding** |
| capability / capacidad / permiso | `capacidades.py`, `permisos-por-capacidad.json` | la habilidad, o su mapa de permisos | **Capability**; el mapa de permisos es de **HarnessTool** |
| role / rol | `agents[].role`, apps | el rol de un agente, o el de un usuario de la app | **Agent**; el rol de un usuario no es de este dominio |
| tool / herramienta | `tools:`, `tool-contract` | herramienta de Claude Code, o artefacto generado | **HostTool** o **HarnessTool** |
| budget / presupuesto | `budget-policy`, `sessionBudget` | plata y contexto, o llamadas premium | **CostBudget** o **ConsumptionPolicy** |

## El límite de la ejecución

### Lo que existe en 0.29

- El Plan en `READY_FOR_EXECUTION`, que es un estado del documento.
- La WorkUnit en `PENDING`, que quiere decir que nada la frena.
- `executionOrder`, un orden topológico que no es un cronograma.
- La `ModelPolicy` con el tier de cada unidad, y la ModelTierApproval en `PENDING`.
- El vocabulario de contabilidad sin productor: `TASK_STARTED`, `TASK_COMPLETED`,
  `WORKUNIT_STARTED`, `WORKUNIT_COMPLETED`, `AGENT_RUN_STARTED`, `AGENT_RUN_COMPLETED`,
  `TOOL_CALL_COMPLETED` y `MODEL_ESCALATION_REQUESTED`.
- Contratos de salida en prosa: el `agentResult` de los especialistas, con
  `COMPLETE|PARTIAL|BLOCKED|FAILED`, y los "Result Statuses" de las skills, con otro conjunto. No
  tienen schema, nadie los lee y no coinciden entre sí.
- Campos que nadie lee: `sessionBudget.maxRetries`, `modelPolicy.allowEscalation`, `modelo.escalar`
  sin quien lo llame, y `retryPolicy` y `timeoutSeconds` del `tool-contract`.
- La refutación, como precedente de "HARNESS entrega, el Host corre, HARNESS registra y valida".
- La revisión automática de fuentes, como el único ciclo de intentos que persiste.

### Lo que no existe

- Un agregado `Execution`.
- Un `ExecutionRequest` o un `ExecutionResult`.
- Un estado posterior a `READY_FOR_EXECUTION`.
- Un ejecutor.
- Un estado de corrida persistido por WorkUnit o por corrida de agente.
- Un ciclo `PENDING → RUNNING → terminal`.
- Un reintento, una reanudación o un checkpoint genéricos.
- Un cliente de modelo.
- Un vínculo entre una corrida de agente y una WorkUnit, salvo el texto libre de `--unidad` y
  `--agente` en contabilidad.

### Lo que queda fijado para la próxima Task

Dos invariantes que valen hoy, y que solo se pueden romper con una decisión escrita:

1. **La contabilidad no es estado de ejecución.** Nada fuera de Observability lee un ledger para
   decidir.
2. **El estado del Plan se deriva del contenido del Plan.** Nadie lo cambia después de armarlo.

Tres preguntas que la Task de ejecución tiene que contestar en su propia spec:

1. Dónde vive el estado de una ejecución.
2. Qué forma tiene lo que vuelve de un agente, distinguiendo EvaluationResult de Evidence.
3. Si el contrato de salida es el `agentResult` de los agentes, los "Result Statuses" de las skills,
   o ninguno de los dos.

## Fuera del producto

La spec, el escenario `E-nn`, la marca `rojo visto`, la lectura y los veredictos del método SDD
(`sostenido`, `contradicho`, `leído` y `sin sustento`) son el método de la fábrica, de `CLAUDE.md` y
de `harness-spec-refuter`. Ningún archivo de `comun/` ni de `harnesses/` los implementa: no son
conceptos del producto. Un RefutationVerdict (`cumple`, `incumple`, `sin-verificar`) no es un
veredicto SDD.
