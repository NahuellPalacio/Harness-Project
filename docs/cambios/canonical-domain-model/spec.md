# Modelo de dominio canónico: qué conceptos tiene HARNESS, qué significa cada uno y dónde termina

**Estado:** verificado y cerrado (0.30.0) · **Fecha:** 02-10-2026, revisada y construida el 03-10-2026 · **Versión de partida:**
0.29.0 (`4c6f0f3`)

Las rutas con número de línea se refieren a `4c6f0f3`. Las rutas sin prefijo son relativas a la raíz
del repo; `bin/` abrevia `harnesses/desarrollo/bin/` y `reglas/` abrevia `harnesses/desarrollo/reglas/`.

📌 **Por qué la carpeta se llama `canonical-domain-model`.** `write-a-spec` deja el nombre libre, y
[ADR-0011](../../adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md) pide nombres de
archivo en inglés. El nombre del pedido cumple las dos cosas. La práctica del repo no: 60 de las 61
carpetas de `docs/cambios/` tienen nombre en español, también las posteriores a ADR-0011. Es la
contradicción C-43, y no se resuelve acá.

---

## 1. Qué problema resuelve

HARNESS creció en 29 versiones, cambio por cambio, y cada cambio nombró lo que necesitaba. El
resultado es un dominio que existe pero no está escrito en ningún lado. Las mismas palabras nombran
cosas distintas, y la misma cosa tiene varios nombres:

| Palabra | Significados distintos en 0.29.0 |
|---|---|
| `check` | 4: el check del hook, el control normativo de tipo CHECK, la especificación `.md` de ese control y la entrada `checks.json` de la refutación. Los tests de la fábrica son un quinto |
| `policy` | 5: el control de tipo POLICY, `budget-policy`, `knowledge-refresh-policy`, `database-environment-access-policy` y los textos libres `policies`/`applicablePolicies` del plan |
| `source` / `fuente` | 7: la fuente normativa gestionada, el canal `jira:`/`archivo:`, la procedencia de un contexto, el adaptador de contabilidad, la tupla norma-control, el `sources:` de un frontmatter y la capa de una variable de entorno |
| `approval` | 6: la del tier de modelo en el plan, el `HUMAN_APPROVAL_REQUIRED` del presupuesto, la aprobación externa de seguridad, `officialApprovalStatus`, la aceptación de una fuente y la promoción de una herramienta |
| `knowledge` / `conocimiento` | 4: las notas de `docs/conocimiento/`, el estado de las fuentes normativas, el `knowledge_status` de una sección y la Ficha de Proyecto |
| `context` / `contexto` | 5: el de la tarea, el del proyecto, el que inyecta SessionStart, el recorte por unidad y la ventana del modelo |
| `verdict` / `veredicto` | 6, uno de ellos de la fábrica: los veredictos SDD, que no son parte del producto |

Lo que eso cuesta, concretamente:

- **El plan promete un ciclo de vida que no tiene.** `orchestration-plan` declara once estados
  (`comun/schemas/orchestration-plan.schema.json:372-374`) y el código escribe tres
  (`bin/orquestacion/plan.py:371-379`). Los otros hablan de recibir, analizar, delegar y fallar, y
  nada de eso existe. El estado `READY` de una unidad no lo escribe nadie (`plan.py:273-279`).
- **No hay una entidad `Task` y su identidad no se valida igual en todos lados.** La clave de Jira es
  la identidad. Se valida en `contexto` y `refute` (`bin/dev-harness.py:1940-1950`), pero no en
  `plan`, `seguridad` ni `contabilidad`. `plan` sin clave termina en `None + ".json"`
  (`dev-harness.py:1197-1198`). En el ledger de contabilidad que escribe la Context Bar, `taskId` es
  el id de la sesión de Claude Code (`bin/contabilidad/statusline.py:190`), aunque el schema diga
  "la tarea".
- **La refutación mezcla dos clases de check en una lista.** `declaredChecks` junta los controles
  normativos con los checks del hook del dominio (`bin/orquestacion/refutacion.py:621-623`), y el
  registro dice que son cosas distintas (`bin/orquestacion/controles.py:10-14`).
- **Hay vocabulario de ejecución donde nada ejecuta:** `DELEGATING`, `WORKUNIT_STARTED`,
  `AGENT_RUN_COMPLETED` y `maxRetries`. La Task siguiente, la de ejecución, se apoyaría en marcadores
  de posición que nadie diseñó.
- **Schemas que dicen lo contrario del código.** Las contradicciones que encontró el relevamiento
  están enumeradas en la sección 17. Hoy son 57 entradas: de C-01 a C-55, más C-09b y C-17b. El
  número es el de la tabla, no una constante.

Este cambio hace cuatro cosas:

1. Escribe una sola vez el modelo que HARNESS ya expresa.
2. Alinea las descripciones de los contratos que lo contradicen.
3. Cambia comportamiento solo donde, sin ese cambio, el código puede producir o aceptar un
   artefacto que contradice un invariante del modelo. Es la regla de D15, aplicada caso por caso.
4. Deja nombrado el límite de la ejecución, pero vacío.

No construye ejecución, ni reorganiza carpetas, ni renombra identificadores.

## 2. Cómo se hizo el relevamiento

Hubo seis relevamientos de solo lectura sobre 0.29.0, cada uno siguiendo productores y consumidores
y no nombres de carpeta:

1. los 46 schemas;
2. el contexto y la identidad de la tarea;
3. la planificación, los agentes y las capacidades;
4. el governance;
5. la contabilidad, la ejecución implícita y Claude Code;
6. la memoria, el conocimiento y el vocabulario.

Después se verificaron a mano los hechos sobre los que se apoyan las decisiones:

- los estados del plan y de la unidad (`plan.py:249-251, 273-279, 371-379`);
- el colapso de ids duplicados (`plan.py:97`);
- la composición de `declaredChecks` (`refutacion.py:621-623`), y que el cierre por check exige que
  el control esté en la unidad y en la matriz (`refutacion.py:692`);
- que no hay colisión entre los nombres de check del roster y los ids del registro de controles;
- que los únicos `subprocess` del producto son `git` (`comun/bin/contexto-armar.py:154`,
  `comun/hooks/session-start.py:54`, `refutacion.py:379`) y `markitdown`
  (`bin/contexto/documentos.py:55`);
- que ningún test menciona los estados del plan que nadie escribe.

## 3. Inventario AS-IS

### 3.1 Lo que hay, por área

| Área | Qué existe | Quién lo produce → quién lo lee | Dónde persiste |
|---|---|---|---|
| Tarea | Una clave de Jira, sin entidad. `TareaNoResuelta` es la única clase con ese nombre (`bin/contexto/tarea.py:17`) | El argumento del CLI → todos los artefactos | No persiste: es el nombre de los archivos |
| Contexto de tarea | `task-context/1.0`, armado por cuatro resolvedores: tarea, Ficha, documentos y repositorio (`dev-harness.py:1081-1142`) | `contexto` → `plan` y `dev-orchestrator` | `.claude/contextos/<KEY>.json`, se pisa entero |
| Contexto de proyecto | `project-context/1.1` | `dev-iniciador-code` (un modelo) → `contexto-armar.py`. Lo leen `repositorio.py`, `refutacion.py`, la bienvenida y SessionStart | `<rutaCodebase>/project-context.json`, versionado en el proyecto |
| Memoria | Zonas del `CLAUDE.md` y `docs/conocimiento/` (`docs/memoria.md:22-26`; `comun/hooks/lib/zonas.py:15-26`) | La persona, el agente y `flush-memoria` → SessionStart | Versionada en el proyecto |
| Fuentes normativas | `source-registry/1.1` (la identidad) y `sources-state/1.1` (el estado y las aceptaciones) | `fuentes`, `fuentes --aceptar` y `--auto` → la compuerta normativa y la bienvenida | El registro va en `reglas/`; el estado, en `.claude/harness.fuentes.json` |
| Plan | `orchestration-plan/1.0`, armado por el código desde una propuesta que escribe un modelo (`plan.py:161-253`) | `plan` → `refute --compile` | `.claude/planes/<KEY>.json` |
| Unidad de trabajo | `workUnits[]` del plan, sin schema propio | `plan.py:256-323` → la refutación, por id | Adentro del plan |
| Agentes y skills | `agent-registry/1.0`, que es autoritativo (`bin/orquestacion/registro_agentes.py:3-4`) | La fábrica → el plan y el ruteo | `reglas/agent-registry.json` |
| Capacidades | Las clases de integración, `capacidadesLocales` del roster y `permisos-por-capacidad` | la validación del entorno (`correr_bootstrap`): `setup`, `reconfigurar` y `estado` siempre, y `contexto` sin registro o con `--revalidar` → el plan | `.claude/harness.capacidades.json` |
| Normativa | Dos matrices, el registro de 60 controles (31 POLICY, 25 CHECK, 4 REVIEW) y las señales | La fábrica, la propuesta y los checks no instalados → el bloque `normative` de cada unidad | `reglas/` y el plan |
| Refutación | `refutation-unit`, `refutation-verdict` y `refutation-run`, más una caché | `refute` y `dev-refutador` (un modelo) → `seguridad --refutacion` | `.claude/refutaciones/<KEY>/` y `cache/` |
| Seguridad | Ledger de evidencia → resumen → reporte | Dos de diez productores tienen camino de CLI → `seguridad --resumen` | `.claude/runtime/security/<KEY>/` |
| Contabilidad | 14 tipos de evento. Se producen tres: `MODEL_CALL_COMPLETED`, `SESSION_COMPLETED` y `CONTEXT_WINDOW_OBSERVED` | `statusline.py` y `contabilidad --ingerir` → la barra y el resumen | `.claude/runtime/accounting/<clave>/ledger.jsonl` |
| Guardas de sesión | La puerta de secretos en PreToolUse y los checks del hook en PostToolUse | Claude Code → `additionalContext`, `deny` y `ask` | Nada persiste |
| Instalación | `harness-installation/1.1`, el lockfile y la salud de los componentes | El instalador y SessionStart → la bienvenida y `-Doctor` | `.claude/harness.installation.json` y `.claude/harness.lock.json` |

### 3.2 Los 46 schemas

En **Runtime** se dice si el código valida contra ese schema al producir o al leer:

- **sí**: valida.
- **versión**: solo mira la versión.
- **tests**: solo lo validan los tests.
- **controles/**: lo valida un control que no se instala.

**Dormido** quiere decir que el contrato existe y ningún camino de producción lo produce.

**Clase** clasifica el contrato, no el concepto: la clasificación del concepto está en 4.2. Evidence
quiere decir un inventario de evidencia que llena el proyecto; Configuration y Domain Policy son
datos de la fábrica.

| Schema | Concepto | Productor | Runtime | Persistencia | Clase |
|---|---|---|---|---|---|
| `agent-registry` | AgentRegistry | la fábrica | sí, en cada plan | `reglas/` | Configuration |
| `annex-ii-technology-catalog` | NormativeMatrix (Anexo II) | la fábrica | versión | `reglas/` | Domain Policy |
| `authentication-abuse-protection` | Evidence (inventario Vu1) | el proyecto, a mano; viene vacío | controles/ | `reglas/` | Evidence |
| `authentication-surface` | Evidence (C1) | el proyecto | controles/ | `reglas/` | Evidence |
| `base-software-data-disclosure` | Evidence (Vu7) | el proyecto | controles/ | `reglas/` | Evidence |
| `browser-session-termination` | Evidence (Vu3) | el proyecto | controles/ | `reglas/` | Evidence |
| `budget-policy` | CostBudget | el instalador si falta, `presupuesto --context-defaults` o una persona | sí | `.claude/harness.presupuesto.json` | Configuration |
| `client-server-validation-parity` | Evidence (Vu5) | el proyecto | controles/ | `reglas/` | Evidence |
| `control-registry` | ControlRegistry | la fábrica | sí | `reglas/` | Configuration |
| `custom-error-message-evidence` | Evidence (Vu6) | el proyecto | controles/ | `reglas/` | Evidence |
| `database-environment-access-policy` | DatabaseAccessPolicy (dormida) | la fábrica | tests | `reglas/` | Configuration |
| `database-profile` | DatabaseAccessPolicy (dormida: un perfil por base lógica y ambiente) | el proyecto | tests | `reglas/` | Configuration |
| `es0901-7.1-normative-matrix` | NormativeMatrix | la fábrica | versión | `reglas/` | Domain Policy |
| `es0902-cross-standard-map` | NormativeMatrix (relación entre normas, dormida) | la fábrica | tests | `reglas/` | Domain Policy |
| `es0902-normative-matrix` | NormativeMatrix | la fábrica | versión | `reglas/` | Domain Policy |
| `es0902-security-deliverables` | NormativeMatrix (entregables) | la fábrica | ninguna al leer | `reglas/` | Configuration |
| `execution-accounting-event` | AccountingEvent | `statusline.py` y `contabilidad --ingerir` | sí | `.claude/runtime/accounting/…/ledger.jsonl` | Record |
| `gcba-it-normative-baseline` | NormativeMatrix (línea base O1) | la fábrica | sí | `reglas/` | Domain Policy |
| `harness-installation-state` | Installation | `bienvenida.registrar_instalacion`, desde el instalador y SessionStart | contra una copia en línea, no este archivo | `.claude/harness.installation.json` | Snapshot |
| `integration-environment-contract` | Integration | la fábrica | un validador propio | `reglas/` | Configuration |
| `knowledge-refresh-policy` | RefreshAgenda | la fábrica | sí | `reglas/` | Configuration |
| `knowledge-refresh-state` | RefreshAgenda | `auto_refresh.registrar` | sí | `.claude/runtime/knowledge-refresh.json` | Record |
| `normative-review` | Review | ninguno encontrado | sí, si llega | — | Snapshot (dormido) |
| `normative-signal` | NormativeSignal | la propuesta (un modelo) y `senales.producir` | sí | adentro del plan | Value Object |
| `orchestration-plan` | Plan, WorkUnit | `plan` | sí, al escribir | `.claude/planes/<KEY>.json` | Aggregate Root |
| `owasp-security-guidance-review` | Evidence (Vu10) | el proyecto | sí, en el plan | `reglas/` | Evidence |
| `project-context` | ProjectContext | `contexto-armar.py` | sí, al escribir | `<rutaCodebase>/project-context.json` | Snapshot |
| `public-interface-abuse-protection` | Evidence (Vu9) | el proyecto | controles/ | `reglas/` | Evidence |
| `refutation-run` | Refutation | `refutacion.corrida` | sí | `.claude/refutaciones/<KEY>/run.json` | Snapshot |
| `refutation-unit` | RefutationUnit | `refute --compile` | sí | `…/units/REF-nnn.json` | Entity |
| `refutation-verdict` | RefutationVerdict | `dev-refutador` (un modelo), más los campos del harness | sí | `…/verdicts/` y `cache/` | Record |
| `repository-integrity-finding` | Finding (dormido) | `integridad.hallazgo`, en memoria | tests | — | Record |
| `role-profile-consistency` | Evidence (Vu8) | el proyecto | controles/ | `reglas/` | Evidence |
| `security-approval-evidence` | ExternalSecurityApproval | el proyecto | controles/ | `reglas/` | Evidence |
| `security-control-authority` | ExternalSecurityApproval (autoridad O2) | el proyecto | controles/ | `reglas/` | Evidence |
| `security-ledger-event` | EvaluationRecord | `reporte_seguridad/productores.py` (2 de 10 con CLI) | sí | `.claude/runtime/security/<KEY>/security-ledger.ndjson` | Record |
| `security-report` | SecuritySummary (su presentación) | una constante en el código | tests | — | Infrastructure |
| `security-summary` | SecuritySummary | `seguridad --resumen` | sí | `.claude/runtime/security/<KEY>/security-summary.json` | Snapshot |
| `sensitive-data-transmission` | Evidence (Vu2) | el proyecto | controles/ | `reglas/` | Evidence |
| `session-inactivity-timeout` | Evidence (Vu4) | el proyecto | controles/ | `reglas/` | Evidence |
| `source-registry` | ManagedSource | la fábrica | sí, en `fuentes` | `reglas/` | Configuration |
| `source-state` | SourceState, SourceAcceptance | `frescura.escribir` | sí | `.claude/harness.fuentes.json` | Aggregate Root |
| `task-context` | TaskContext | `contexto` | sí, antes de escribir | `.claude/contextos/<KEY>.json` | Snapshot |
| `tool-contract` | HarnessTool (dormido) | ninguno en producción | tests | — | Value Object |
| `tool-registry` | HarnessTool (dormido) | ninguno en producción | tests | `.claude/harness.tools.json`, que nunca se escribe | Record |
| `trusted-repository-baseline` | Finding (línea base, dormida) | ninguno | tests | — | Configuration |

Y lo que tiene forma de contrato **sin schema**:

- la propuesta del plan (`agents/dev-orchestrator.md:43-53`);
- `summary.json` de contabilidad, que declara `execution-summary/1.0` sin archivo;
- `harness.capacidades.json`, `runtime/contextbar.json` y `harness.integraciones.json`, que tienen
  formas en línea en `comun/hooks/lib/bienvenida.py:316-401`;
- `harness.config.json` y `harness.lock.json`;
- `reglas/roster.json`, `es0901-7.1.json`, `permisos-por-capacidad.json`,
  `huerfanos-reconocidos.json`, `security-report-domains.json` y
  `es0902-c3-control-source-binding.json`.

Hay **un solo validador**, un intérprete de un subconjunto de JSON Schema
(`comun/bin/contexto-armar.py:833-968`). Rechaza las palabras clave que no conoce, así que ningún
schema puede llevar marcas propias. La bienvenida tiene una segunda copia
(`bienvenida.py:407-443`).

### 3.3 La ejecución implícita: qué corre hoy

- **Los subcomandos del CLI**: `setup`, `estado`, `reconfigurar`, `contexto`, `plan`, `contabilidad`,
  `fuentes`, `seguridad`, `harness`, `refute` y `presupuesto` (`dev-harness.py:1836-1838`). Son
  sincrónicos, salen con 0 o 2 y no persisten un estado de corrida.
- **Los hooks**, que corre Claude Code. No persisten nada, salvo la marca de "ya avisé"
  (`comun/hooks/lib/hook.py:102-137`).
- **La refutación** es el único lugar donde HARNESS le pasa trabajo al Host y registra lo que
  vuelve:
  - `refute --unit` entrega una unidad;
  - la sesión de Claude Code corre `dev-refutador`;
  - `refute --record` valida el veredicto de todo o nada (`refutacion.py:3-4, 1064-1177`;
    `dev-harness.py:1602-1606`).

  Su "run" es un agregado compilado, sin `startedAt`, sin intentos y sin ejecutor
  (`comun/schemas/refutation-run.schema.json`).
- **La revisión automática de las fuentes** es el único ciclo de intentos que persiste
  (`auto_refresh.py:269-305`). Escribe CURRENT, SUCCEEDED_WITH_UPDATES y UNRESOLVED; RUNNING, DUE y
  ERROR no se escriben nunca.
- **Las llamadas HTTP** a Jira y GitLab tienen timeout y no reintentan
  (`bin/integraciones/fuentes.py:118`). El único reintento del código es un `os.replace` local
  (`auto_refresh.py:357-364`).
- **HARNESS no llama a ningún modelo.** El único `subprocess` es `git` o `markitdown`.

### 3.4 Claude Code: qué papel cumple

| Papel | Evidencia |
|---|---|
| Host de los hooks | `comun/settings/hooks.plantilla.json:12-45` y `install.ps1:731-738` |
| UI | `statusLine` (`install.ps1:741`; `statusline.py`) y `systemMessage` (`comun/hooks/session-start.py:221-222`) |
| Runtime de agentes | `agents/*.md` y `skills/*/SKILL.md`, que son subagentes y skills de Claude Code. La refutación la juzga "la sesión de Claude Code" (`refutacion.py:4`) |
| Proveedor de herramientas | Los matchers `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash\|PowerShell` (`hooks.plantilla.json:30,38`) y el `tools:` de los agentes |
| Proveedor de la transcripción | `bin/contabilidad/adaptadores/claude_code.py:129-149, 269-315` |
| Acceso al modelo | Los ids de modelo llegan por la transcripción y la `statusLine`; `PROVEEDOR = "anthropic"` (`claude_code.py:33`) |

**Por dónde se filtra Claude Code a contratos del producto:**

- `contextWindow.source` es el enum `["CLAUDE_CODE_STATUSLINE"]`
  (`comun/schemas/execution-accounting-event.schema.json:206`);
- el bloque `contextBar` del estado de la instalación, con huella de la `statusLine` y
  `reloadRequired` (`harness-installation-state.schema.json:198-321`);
- el `session_id` usado como `taskId` en el ledger de la barra;
- `providerSessionId` en las claves de metadata (`bin/contabilidad/eventos.py:83`).

Hay un segundo adaptador, `codex.py`, que solo sirve para contabilidad y siempre devuelve
`USAGE_UNRESOLVED` (`codex.py:25-28`).

### 3.5 Fuente e instalado: dónde cambia el significado

En ningún lado se pregunta "¿estoy instalado?". El código prueba rutas:

- `rutas.localizar` sube hasta seis niveles (`bin/rutas.py:19-44`);
- `roster._raices_de_reglas` prueba los dos árboles (`bin/orquestacion/roster.py:27-50`).

Lo que cambia según qué árbol encuentre:

- **`controles/` no se instala** (`install.ps1:1839-1844`). En un proyecto instalado, los 60
  controles dan `CONTROL_FILE_MISSING`. `normativa._ruta_de_evidencia` apunta a una ruta del árbol
  fuente (`bin/orquestacion/normativa.py:178-198`), así que los bloques de Vu3 a Vu10 viajan sin ids.
  Y la línea base de C3 (`developmentStandardBaseline`) queda sin resolver, porque exige los controles
  compartidos de G1 `INSTALLED`: lo encontró la construcción, con E-44.
- **`harness_version` del TaskContext sale del lockfile**, que en la fábrica no existe, así que vale
  `""` (`dev-harness.py:158-159`). El ProjectContext usa `VERSION` (`contexto-armar.py:1013-1032`).
- **Los checks del hook que corren no son los mismos.** En la fábrica corre solo `comun/checks`; en
  un proyecto instalado, también `checks/desarrollo` (`comun/hooks/post-tool-use.py:28`;
  `install.ps1:1827, 1840`).
- **El Agent Registry da `registryValid: false` en un proyecto instalado y `true` en la fábrica.** Ya
  está anotado en `PENDIENTES-FH.md`.
- **Si no encuentra el catálogo de secretos, el contexto no se redacta y nada lo avisa**
  (`bin/contexto/limpieza.py:88-89`; `bin/contexto/ensamblador.py:107-110`).

---

## 4. El modelo canónico

### 4.1 El dibujo

```text
Task — externa: su registro es un issue de Jira. HARNESS guarda solo su TaskKey   [Work Intake]
 │
 ├── TaskContext       snapshot de la tarea, se regenera entero                     [Work Intake]
 │     ├── ProvenanceRef*     de dónde salió cada sección
 │     ├── SectionConfidence  confirmed · inferred · conflicted · missing · stale
 │     ├── ContextGap*        lo que falta, lo que choca, lo redactado
 │     └── ─ ─ ► ProjectContext, por hash                                       [Project Knowledge]
 │
 ├── Plan   pln_<TaskKey> · planVersion                                            [Planning]
 │     ├── WorkUnit*   id único en el plan · domain ∈ plan.domains
 │     │     ├── assignedAgent ─────► Agent, decidido por el AgentRegistry           [Catalog]
 │     │     ├── skills ────────────► Skill*, las del dueño del dominio              [Catalog]
 │     │     ├── requiredCapabilities ► Capability*                                  [Catalog]
 │     │     ├── requiredChecks ────► GuardrailCheck*, por nombre                     [Guardrails]
 │     │     ├── normative ─────────► NormativeRule* · Control* · NormativeSignal*    [Governance]
 │     │     ├── ContextSlice
 │     │     ├── ModelPolicy
 │     │     └── status ∈ { PENDING, BLOCKED, WAITING_FOR_HUMAN_APPROVAL }
 │     ├── CapabilityGap*
 │     ├── ModelTierApproval*   en 0.29 solo se escribe PENDING
 │     └── status ∈ { CAPABILITY_RESOLUTION, WAITING_FOR_HUMAN_APPROVAL, READY_FOR_EXECUTION }
 │
 ├── Refutation   .claude/refutaciones/<TaskKey>                                   [Governance]
 │     ├── RefutationUnit*    REF-nnn · (WorkUnit, ruleKey, alcance)
 │     ├── RefutationVerdict*  cumple · incumple · sin-verificar
 │     └── run.json            PASS · FAIL · INCOMPLETE · NOTHING_TO_VERIFY
 │
 ├── EvaluationRecord* → SecuritySummary                                           [Governance]
 └── AccountingEvent*    ledger por LedgerKey = TaskKey | HostSession            [Observability]

 ┄┄┄ Execution ┄┄┄  vacío en 0.29: nada toma una WorkUnit y la lleva a cabo     [reservado]

NormativeKnowledge = ManagedSource* + SourceAcceptance* ⇒ SourceState       [Normative Sources]
ProjectMemory = reglas sobre documentos del equipo: zonas de CLAUDE.md,
                techos, write-back a docs/conocimiento/                       [Project Knowledge]
Installation = versión · bootstrap · salud de los componentes                [Host Integration]
SecretGate · GuardrailCheck*                                                       [Guardrails]

Host (Claude Code) — externo: hooks · statusLine · subagentes · skills · herramientas ·
                     transcripción · modelos
```

### 4.2 Los conceptos

Esta tabla es la **fuente canónica del catálogo**. Un concepto existe si tiene su fila acá, y el
documento canónico la copia como su índice (E-01). El relevamiento encontró 68 conceptos en nueve
contextos. Ese número es un resultado, no un contrato: si en la construcción o en la verificación
aparece mejor evidencia, el catálogo se corrige y el número cambia. Ya pasó una vez: la primera
verificación mostró que `database-environment-access-policy` no es una NormativeMatrix (S4), y se
agregó DatabaseAccessPolicy. Hoy son 69.

Las clasificaciones están definidas en la sección 6. Debajo de la tabla van en detalle los conceptos
sobre los que se apoya el resto.

| Concepto | Contexto | Clasificación | Qué es | Identidad | Contrato |
|---|---|---|---|---|---|
| Task | Work Intake | External | El trabajo que alguien pidió. Su registro vive en Jira; HARNESS no tiene su estado ni su ciclo de vida | TaskKey | ninguno propio |
| TaskKey | Work Intake | Value Object | La identidad de una Task, igual en todo artefacto que se derive de ella | `^[A-Za-z][A-Za-z0-9_]*-[0-9]+$` | patrones de `task-context` y `orchestration-plan` |
| TaskRecord | Work Intake | External | El issue de Jira que registra la Task. Se lee por la Integration de Jira | su clave en Jira | — |
| Ficha | Work Intake | External | La Ficha de Proyecto, un issue de Jira que describe el proyecto. Da la sección `project` del TaskContext y es el Channel de las fuentes | su clave | — |
| TaskContext | Work Intake | Snapshot | Lo que se sabe de una Task en un momento: tarea, Ficha, documentos y repositorio, cada uno con su procedencia | `tsk_<TaskKey>` + `context_hash` | `task-context/1.0` |
| ProvenanceRef | Work Intake | Value Object | De dónde salió un dato del TaskContext | `source_id` | `task-context` `sources[]` |
| SectionConfidence | Work Intake | Value Object | Qué tan seguro está un contexto de una de sus secciones | — | `knowledge_status` |
| ContextGap | Work Intake | Value Object | Lo que falta, lo que se contradice, lo que se redactó y lo que queda preguntado | — | `gaps_and_conflicts` |
| ProjectContext | Project Knowledge | Snapshot | El índice del código del proyecto, serializado con su revisión y su hash | `ctx_<repo>_<rev4>` + `context_hash` | `project-context/1.1` |
| ProjectMemory | Project Knowledge | Domain Policy | Las reglas con que HARNESS trata lo que el equipo decidió dejar escrito: las zonas del `CLAUDE.md` con sus techos, qué se purga y qué no, y el write-back a `docs/conocimiento/`. Los documentos son del proyecto | no aplica: no es una cosa individual | `manifest.json` `techoZona*`, `zonas.py` |
| ManagedSource | Normative Sources | Entity | Un documento normativo cuya identidad registra la fábrica: versión, hash del original y extracto | `id`, como `ES0901` | `source-registry/1.1` |
| SourceState | Normative Sources | Aggregate Root | El estado de cada fuente en un proyecto, derivado de lo observado, con las decisiones humanas | el proyecto | `sources-state/1.1` |
| SourceAcceptance | Normative Sources | Record | La decisión de una persona nombrada (APPLY o POSTPONE) contra una identidad observada | fuente + versión + sha256 | `source-state` `decisions` y `acceptance` |
| Channel | Normative Sources | Value Object | Por dónde se observa una fuente | `jira:<FICHA>` o `archivo:<dir>` | `source-state` `channel` |
| NormativeKnowledge | Normative Sources | Snapshot | Lo que el proyecto puede usar como norma vigente: las ManagedSource en CURRENT, con su extracto | el proyecto | `harness-installation-state` `knowledge` (proyección) |
| RefreshAgenda | Normative Sources | Record | Cuándo se volvió a mirar las fuentes, cuándo vence y por qué disparador; con su política | el proyecto | `knowledge-refresh-state`, `knowledge-refresh-policy` |
| NormativeFreshnessGate | Normative Sources | Domain Service | La decisión `allowed`/`blocked`/`unresolved` antes de `plan`, `refute --compile` y `seguridad` | — | ninguno (`auto_refresh.py:474-513`) |
| Plan | Planning | Aggregate Root | Cómo se descompone una Task en WorkUnits, con quién, con qué y qué la frena. Es un documento: no ejecuta | `pln_<TaskKey>` + `plan_version` | `orchestration-plan/2.0`; un `1.0` se lee según D16 |
| PlanProposal | Planning | DTO / Contract | Lo que escribe `dev-orchestrator`, un modelo: entrada sin autoridad | ninguna | sin schema |
| WorkUnit | Planning | Entity | Una porción de la Task para un dominio y un agente, con sus capacidades, normas y dependencias | (PlanId, `id`) | `orchestration-plan` `workUnits[]` |
| ContextSlice | Planning | Value Object | La parte del TaskContext que ve una WorkUnit, y qué se le omitió | — | `workUnits[].context` |
| ModelPolicy | Planning | Value Object | El tier requerido para una WorkUnit, con el porqué | — | `workUnits[].modelPolicy` |
| ModelRouter | Planning | Domain Service | Decide el tier por señales de complejidad (`bin/orquestacion/modelo.py:18-34`) | — | — |
| ConsumptionPolicy | Planning | Value Object | Tiers aprobados solos y llamadas premium permitidas por plan | — | `consumptionPolicy` |
| ConsumptionGate | Planning | Domain Service | Aprueba un tier o crea una ModelTierApproval (`bin/orquestacion/consumo.py:55-84`) | — | — |
| ModelTierApproval | Planning | Entity | El pedido de que una persona apruebe un tier caro para una WorkUnit | (PlanId, `workUnit`) | `humanApprovals[]` |
| CapabilityGap | Planning | Value Object | Una capacidad pedida que no está disponible, y a quién se deriva | `capability` | `capabilityGaps[]` |
| AgentRegistry | Catalog | Aggregate Root | La autoridad sobre qué agentes y skills existen, de qué dominio y en qué estado | el archivo | `agent-registry/1.0` |
| Agent | Catalog | Entity | Un rol especializado al que se le asigna una WorkUnit. Lo corre el Host desde su `.md` | `id`, por frontmatter | `agent-registry` `agents[]` |
| Skill | Catalog | Entity | Un procedimiento que usa un Agent. No tiene identidad fuera de su dueño en el registro | `id`, por frontmatter | `agent-registry` `skills[]` |
| WorkDomain | Catalog | Value Object | Un área de trabajo: backend, frontend, seguridad… (`plan.py:35-48`) | el nombre | `domains[]` |
| Capability | Catalog | Value Object | Una habilidad con nombre que una WorkUnit necesita y una Integration o el entorno local da | `<a>.<b>[.<c>]` | `requiredCapabilities`, `harness.capacidades.json` |
| Integration | Catalog | Entity | Un sistema externo conectado, con su estado y las capacidades que declara | `jira`, `gitlab` | `integration-environment-contract`, `harness.integraciones.json` |
| HarnessTool | Catalog | Value Object | Un artefacto que HARNESS generaría bajo un contrato. Dormido: nada lo produce | `name` + `version` | `tool-contract`, `tool-registry` |
| DatabaseAccessPolicy | Catalog | Domain Policy | Qué clase de operación sobre una base puede correr en cada ambiente, decidido antes de conectar. Dormida: `bases.py` no tiene importador de producción | el ambiente, para la regla; (base lógica, ambiente), para un perfil | `database-environment-access-policy`, `database-profile` |
| NormativeStandard | Governance | Value Object | Una norma con su versión: ES0901 6.3, ES0902… | `id` + versión | campo `standard` |
| NormativeMatrix | Governance | Domain Policy | Las reglas de una norma, con su aplicabilidad y sus controles | norma + versión | `es0901-7.1-normative-matrix`, `es0902-normative-matrix` y las demás de la tabla 3.2 |
| NormativeRule | Governance | Entity | Una regla citable de una norma, con su aplicabilidad y los controles que pide | `ruleKey`, como `ES0901.G1` | filas de la matriz |
| NormativeSignal | Governance | Value Object | Un hecho sobre la Task o el proyecto que decide si una regla aplica. Su valor sale de la evidencia | `signalId` | `normative-signal` |
| Applicability | Governance | Value Object | Si una regla aplica a una WorkUnit: APPLICABLE, NOT_APPLICABLE o sin resolver | — | `workUnits[].normative` |
| ControlRegistry | Governance | Configuration | Qué controles existen. El registro declara, el disco diagnostica | el archivo | `control-registry/1.0` |
| Control | Governance | Entity | Lo que una regla exige que exista: una Policy, un ControlCheck o una Review | `id` | `control-registry` `controls[]` |
| Policy | Governance | Domain Policy | Un Control de tipo POLICY: un requisito normativo en prosa, con sus resultados posibles. No se ejecuta | `id` del Control | `controles/policies/*.md` |
| ControlCheck | Governance | Domain Service | Un Control de tipo CHECK: `evaluar(...)` devuelve un estado y su evidencia | `id` del Control | `controles/checks/*.py` |
| CheckSpecification | Governance | Configuration | El `.md` que describe un ControlCheck. Es documentación, no se ejecuta | su archivo | `reglas/es0902-*-check.md` |
| Review | Governance | Snapshot | Un Control de tipo REVIEW y el documento que lo resuelve con criterio | `reviewId` | `normative-review/1.0` |
| Evidence | Governance | Value Object | Un hecho observado que sostiene una afirmación, atado por ruta, línea o huella. No lleva resultado | su huella | ítems `evidence[]` y los 13 inventarios |
| EvaluationResult | Governance | Value Object | El resultado de evaluar una regla o un control: COMPLIANT, NON_COMPLIANT, PASS, FAIL, UNRESOLVED… | — | campos `state` y `result` |
| ExternalSecurityApproval | Governance | External | Evidencia de que una autoridad externa aprobó algo. HARNESS nunca la produce | `approvalId` | `security-approval-evidence`, `security-control-authority` |
| Refutation | Governance | Aggregate Root | La refutación de un Plan regla por regla, con sus unidades, veredictos y agregado | TaskKey | `refutation-run/1.0` |
| RefutationUnit | Governance | Entity | Una afirmación para refutar: (WorkUnit, ruleKey, alcance) | `REF-nnn` | `refutation-unit/1.0` |
| RefutationVerdict | Governance | Record | El juicio sobre una RefutationUnit, por un check, por caché o por `dev-refutador` | `refutationUnitId` + `cacheKey` | `refutation-verdict/1.0` |
| Finding | Governance | Record | Un hallazgo de governance con estado: de integridad, de Review o de un hallazgo ES0902 | `findingId` | `repository-integrity-finding`, `findings[]` |
| EvaluationRecord | Governance | Record | Un resultado de evaluación registrado con las huellas de su evidencia | `eventId` | `security-ledger-event` |
| SecuritySummary | Governance | Snapshot | El estado de seguridad de una Task, armado desde los EvaluationRecord | `snapshotFingerprint` | `security-summary`, `security-report` |
| SecretGate | Guardrails | Domain Service | La única regla que bloquea: un secreto que se va a escribir o ejecutar da `deny` o `ask`. Lo complementa `permissions.deny`, que impide leer | — | `comun/reglas/secretos.patrones.json` |
| GuardrailCheck | Guardrails | Domain Service | Un check del hook: `verificar(evento, proyecto, config) -> [str]` en PostToolUse. Avisa, nunca bloquea | su archivo | `roster.json` `checks` |
| GuardrailFinding | Guardrails | Value Object | Un aviso de texto de un GuardrailCheck, como mucho ocho por evento | — | `additionalContext` |
| AccountingEvent | Observability | Record | Algo observado del consumo de modelo de una sesión o una Task: tokens, costo, tiempo, ventana | `eventId` | `execution-accounting-event` |
| LedgerKey | Observability | Value Object | La clave de un ledger de contabilidad: una TaskKey o una HostSession | TaskKey o UUID | `taskId` |
| AccountingSummary | Observability | Snapshot | Los totales de un ledger, conciliados contra el proveedor | la LedgerKey | `summary.json`, sin schema |
| CostBudget | Observability | Configuration | Los umbrales de contexto y los límites de plata del proyecto. Su evaluación es evidencia, nunca un permiso | `policyId` | `budget-policy` |
| ContextBarState | Observability | Snapshot | Lo que dibuja la Context Bar: modelo, contexto, presupuesto, tiempo | — | `barra.de` (`bin/contabilidad/barra.py:39-97`) |
| Installation | Host Integration | Aggregate Root | El estado del harness en un proyecto: versión, bootstrap y salud de sus componentes | el proyecto | `harness-installation/1.1` |
| RuntimeComponentHealth | Host Integration | Value Object | Si un componente (Block 4, Context Bar, Security Reporting) está ACTIVE y por qué no | el nombre del componente | `runtimeComponents` |
| HarnessConfig | Host Integration | Configuration | La configuración del proyecto, sembrada desde `manifest.json` y que después no se toca nunca | el proyecto | `harness.config.json`, `manifest.json` |
| Host | External | External | Claude Code. Corre los hooks, dibuja la UI, ejecuta agentes y skills, da las herramientas, la transcripción y los modelos | — | — |
| HostSession | External | External | Una sesión de Claude Code | `session_id`, un UUID | `sessionId` |
| HostTool | External | External | Una herramienta de Claude Code: Read, Write, Edit, Bash, PowerShell… | su nombre | matchers de los hooks, `tools:` de los agentes |

**Fuera del producto.** Spec, escenario `E-nn`, la marca `rojo visto`, lectura y los veredictos SDD
(`sostenido`, `contradicho`, `leído`, `sin sustento`) son el método de la fábrica (`CLAUDE.md`;
`.claude/agents/harness-spec-refuter.md`). Ningún archivo de `comun/` ni de `harnesses/` los
implementa. No son conceptos del producto, y un `RefutationVerdict` no es un veredicto SDD.

#### En detalle

**Task**
- **Es** la unidad de trabajo que alguien pidió en el issue tracker.
- **No tiene estado ni ciclo de vida en HARNESS.** Lo tiene Jira, y HARNESS lo lee.
- **Identidad:** TaskKey.
- **Lo que HARNESS tiene de una Task:** snapshots, como el TaskContext, y documentos derivados, como
  el Plan, la Refutation y los ledgers. Todos se nombran por su TaskKey.
- **No es** el issue de Jira (eso es TaskRecord), ni una WorkUnit, ni una HostSession.
- **Hoy no existe como código**, y este cambio no la crea (decisión D1).

**TaskKey**
- **Forma:** `^[A-Za-z][A-Za-z0-9_]*-[0-9]+$` (`dev-harness.py:92`).
- **Dónde la crean:** el argumento del CLI.
- **Dónde viaja:**
  - `meta.task_key`, `context_id` y el nombre del archivo del contexto (`ensamblador.py:67, 95`;
    `dev-harness.py:1133`);
  - `plan_id` y `meta.task_key` del plan (`plan.py:213, 217`);
  - `taskKey` de la refutación (`refutacion.py:608`);
  - la carpeta del ledger de seguridad (`bin/reporte_seguridad/libro.py:47`).
- **Hoy se valida** en `contexto` y en `refute`, con dos reglas idénticas (`dev-harness.py:92`;
  `refutacion.py:57`). `plan` no la valida, pero no puede escribir un plan con una clave inválida:
  el patrón de `plan_id` lo rechaza al escribir.
- **Con este cambio** se valida también en `seguridad`, que hoy escribe un ledger con cualquier
  nombre (E-26). E-25 y E-27 fijan lo que ya vale.
- **Queda pendiente** unificar las dos reglas y que `plan` sin clave no reviente. No pasan la regla
  de D15.
- **No se normaliza** a mayúsculas (decisión D12).

**TaskContext**
- **Es** un snapshot armado por la aplicación `contexto`.
- **Lo validan** contra `task-context/1.0` antes de escribirlo (`ensamblador.py:120-139`).
- **Se pisa entero** en cada corrida y nadie lo modifica. Su consumidor es el Plan.
- **Invariantes:**
  - sin `jira.issue.read` no existe (`tarea.py:34-41`);
  - cada sección declara su SectionConfidence;
  - el texto de afuera pasa por la redacción;
  - el hash excluye `generated_at` (`contexto-armar.py:973-988`).
- **Contradicción:** el hash incluye `retrieved_at`, así que dos corridas no dan el mismo hash (C-17).
- **No es** Knowledge. Un adjunto de la Ficha que no está en el registro es documentación del
  TaskContext, no una ManagedSource (`comun/schemas/source-registry.schema.json:27`).

**ProjectContext**
- **Lo producen** un modelo, `dev-iniciador-code`, y un script determinista que lo serializa y lo
  valida (`agents/dev-iniciador-code.md:206-219`; `contexto-armar.py:1037-1187`).
- **Está versionado** en el proyecto y se regenera solo cuando el agente vuelve a recorrer el código.
- **Nadie compara** su `repo_revision` con el HEAD.
- **No es** ProjectMemory: `docs/codebase/` "no es `docs/conocimiento/`"
  (`dev-iniciador-code.md:45-47`).

**ProjectMemory**
- **Es** la política con que HARNESS trata lo que alguien decidió dejar anotado: "no se captura
  nada" (`docs/memoria.md:5`).
- **Los documentos son del equipo.** Son el `CLAUDE.md` y las notas de `docs/conocimiento/`, y están
  versionados en el proyecto. HARNESS los lee en SessionStart, los mide con un check y los mueve con
  `flush-memoria` cuando alguien lo invoca, pero no es su dueño.
- **Lo que define HARNESS:**
  - las zonas FIJA, MAPA, ÍNDICE y CACHÉ (`zonas.py:15-26`), con su techo como dato
    (`manifest.json` `techoZona*`);
  - nada sale de CACHÉ sin estar escrito y verificado en `docs/conocimiento/`
    (`comun/agents/flush-memoria.md:50-67`);
  - FIJA no se purga;
  - los techos avisan y no bloquean (`comun/checks/claude-md-zonas.py:3-4`).
- **Por qué Domain Policy y no Entity.** No tiene una identidad estable: es un `CLAUDE.md`, que
  además comparte con el bloque del instalador, más una carpeta de notas sueltas. No existe como una
  sola cosa. No tiene un ciclo de vida propio, porque cada zona y cada nota cambian por su cuenta. No
  se modifica como unidad. Ningún código protege sus invariantes sobre el conjunto: el write-back es
  un procedimiento de `flush-memoria`, que es un modelo, y el techo es un aviso por zona. Lo estable,
  lo que HARNESS escribe y lo que se puede probar son las reglas. Por eso es una regla del dominio
  expresada como dato y como procedimiento. Llamarlo Entity inventaría una identidad y un dueño que
  la evidencia no muestra.
- **No es** Knowledge, ni Source, ni Context, ni un documento.

**ManagedSource, SourceState, SourceAcceptance y NormativeKnowledge**
- **La identidad la da el registro**, y el hash es del original, nunca del extracto
  (`bin/orquestacion/registro_fuentes.py:8-14`).
- **El estado se deriva** de lo observado por un Channel, en doce valores (`frescura.py:46-62`).
- **La frescura es relativa al canal** (`frescura.py:14-16`).
- **Una aceptación la escribe una persona nombrada**, contra la identidad observada en la misma
  corrida (`dev-harness.py:843-873`). `--auto` no acepta nada.
- **NormativeKnowledge es la proyección** de lo vigente. Es lo que el estado de la instalación llama
  `knowledge` (`bienvenida.py:566-604`).
- **Contradicción:** las aceptaciones viven en un archivo que se declara derivado y que está
  gitignoreado. Una aceptación vale solo en la máquina donde se hizo (C-31).

**Plan**
- **Es el agregado con más invariantes del producto.** La propuesta la escribe un modelo; el plan lo
  arma y lo valida el código.
- **Invariantes que el código ya sostiene:**
  - dominios conocidos;
  - al menos una WorkUnit;
  - dependencias existentes y sin ciclos (`plan.py:90-105, 168-175`);
  - validez contra el schema antes de escribir (`plan.py:382-402`);
  - replanificar pide un motivo y un plan existente.
- **El estado se deriva del contenido** y nadie lo cambia después (`plan.py:371-379`).
- **`READY_FOR_EXECUTION`** quiere decir que no hay CapabilityGap, ni ModelTierApproval pendiente, ni
  WorkUnit bloqueada. **No dice** que el agente exista, ni que las reglas estén resueltas, ni que algo
  vaya a correr (`orquestacion/__init__.py:9`).
- **Lo que decide el Plan, y no la WorkUnit:** dominios, objetivo, `executionOrder` (un orden
  topológico, "no es un cronograma"), huecos agregados, ruteo de modelos, presupuesto, aprobaciones,
  historia y estado.
- **Persiste** en `.claude/planes/<KEY>.json` y sobrevive al `-Update`.
- **Su contrato pasa a `orchestration-plan/2.0`.** Un plan `1.0` guardado se lee según D16: se acepta
  si sus estados existen en 2.0 y se migra la próxima vez que se escribe. Si no, se rechaza.

**WorkUnit**
- **Es** una entidad del Plan, y no tiene identidad fuera de él: se la nombra (PlanId, WorkUnitId).
- **Sale de la propuesta:** `id`, `objective`, `domain`, `dependencies` y `requiredCapabilities`.
- **Lo resuelve el código:**
  - `assignedAgent`, `agentExists` y `agentValidation`;
  - `skills`, `context`, `normative` y `requiredChecks`;
  - `modelPolicy` y `status`.
- **Estados:**
  - `PENDING`: está planificada y nada la frena;
  - `BLOCKED`: le falta una capacidad;
  - `WAITING_FOR_HUMAN_APPROVAL`: su tier pide una aprobación.
- **Invariantes nuevos:** id único en el plan, y dominio entre los del plan (E-18, E-19).
- **No tiene:** resultado, salidas esperadas, ejecutor ni estado posterior. Eso es el límite de la
  ejecución.

**ModelTierApproval**
- Es la única aprobación que vive en el Plan, y es sobre costo, no sobre governance.
- Se escribe solo `PENDING` (`consumo.py:82`).
- `APPROVED`, `DOWNGRADED` y `CANCELLED` existen en el schema, pero ningún comando resuelve un pedido.
  Es un hueco de la aplicación, no de la ejecución.

**Agent, Skill y AgentRegistry**
- **El registro decide si un agente existe**, y el disco solo diagnostica (`registro_agentes.py:3-4`;
  `roster.py:90-105`).
- **El plan no rechaza un agente desconocido.** Lo registra como `agentExists: false`.
- **Un Agent es un rol con un dominio**, y lo corre el Host desde su `.md`.
- **Una Skill es un procedimiento** que el Agent carga con la herramienta `Skill` del Host.
- **Agent ≠ Capability.** Nada liga el `tools:` de un agente con las capacidades (C-25).

**Capability e Integration**
- **Una Capability es un nombre con puntos.** Hay dos familias:
  - **de integración:** `jira.issue.read`, `jira.issue.search`, `jira.attachment.read`,
    `gitlab.project.read`, `gitlab.repository.read`, `gitlab.branch.read` y
    `gitlab.merge_request.read`, declaradas por la clase (`bin/integraciones/jira.py:19`;
    `gitlab.py:12-13`);
  - **locales:** `repository.read`, `repository.write`, `repository.search` y `tests.run`
    (`reglas/roster.json:51-56`).
- **Soportada** quiere decir que la declara la clase. **Disponible** quiere decir que se validó
  ENABLED en esta máquina (`bin/integraciones/registro.py:10-16`). Eso vale para las de
  integración: las locales no se validan, y `capacidades.disponibles` las suma siempre.
- **Una Integration tiene cinco estados**: `NOT_CONFIGURED`, `AUTHENTICATION_FAILED`,
  `CONNECTION_FAILED`, `PERMISSION_DENIED` y `AVAILABLE` (`bin/integraciones/base.py:29-35`).
- **La clase hace dos papeles:**
  - la conexión y sus capacidades, que es Catalog;
  - el cliente HTTP, que es Infrastructure.

  El código la llama "adaptador" (`dev-harness.py:174`), igual que a los adaptadores de contabilidad.

**Control, Policy, ControlCheck, Review y GuardrailCheck**
- **Un Control dice qué tiene que existir, nunca si se cumple** (`controles.py:16`).
- **Policy** es solamente el Control de tipo POLICY.
- **ControlCheck** evalúa y devuelve un estado y su evidencia. **CheckSpecification** lo describe.
- **GuardrailCheck es otra cosa:**
  - corre en la sesión, en PostToolUse;
  - devuelve textos;
  - no persiste nada;
  - lo cuida otro dueño, `harness-hook-engineer`.
- **Los tests de `tests/casos/` no son checks.** Son la verificación de la fábrica.

**Evidence y EvaluationResult**
- **Evidence** es lo observado: `{path, line, observed}`, un ítem de evidencia de una señal o un
  artefacto de aprobación.
- **EvaluationResult** es el estado que sale de evaluar, y apunta a la evidencia por huella.
- **Un EvaluationRecord** del ledger de seguridad junta los dos, y "el productor no decide un
  resultado" (`bin/reporte_seguridad/productores.py:27-29`).

**Refutation, RefutationUnit y RefutationVerdict**
- **Una RefutationUnit** sale de cada (WorkUnit, regla, alcance) (`refutacion.py:569-659`).
- **Se cierra por check** solo si el control:
  - es un CHECK `INSTALLED`;
  - está atado a la misma `ruleKey`;
  - está en la matriz y en la unidad;
  - tiene las huellas al día y un estado PASS o FAIL (`refutacion.py:670-735`).
- **Si no se cierra por check**, sale por la caché o por `dev-refutador`.
- **El harness es el único que escribe** `resolutionPath`, `cacheHit`, `recordedAt` y las huellas
  (`refutacion.py:100-101, 1068-1072`).
- **Solo `cumple` e `incumple` se reutilizan** (`refutacion.py:779-783`).

**AccountingEvent y LedgerKey**
- **El `eventId`** es `ev_` + sha256 de adaptador|tipo|dedupKey (`eventos.py:284-292`).
- **Hay 14 tipos y se producen tres.**
- **`SESSION_COMPLETED`** es en realidad la foto acumulada del proveedor, y sale varias veces por
  sesión (`claude_code.py:269-315`).
- **`CONTEXT_WINDOW_OBSERVED`** no se suma (`bin/contabilidad/agregacion.py:7-9`).
- **Una LedgerKey** es una TaskKey o una HostSession: "la sesión es la tarea mientras nadie declare
  una" (`bienvenida.py:1032-1038`).
- **Nada fuera de Observability lee un ledger para decidir algo.** La evaluación del presupuesto es
  evidencia (`bin/contabilidad/presupuesto.py:3-7`).
- **No es** estado de ejecución. **No es** un Domain Event.

**Installation**
- **Lo escribe** `bienvenida.registrar_instalacion`, desde el instalador y desde SessionStart.
- **Un componente que no está ACTIVE** deja la instalación PARCIAL y nunca BLOQUEADA
  (`bienvenida.py:25-30`).
- **`harnessId` vale `"desarrollo"`** como constante, por ADR-0012.

**Host**
- **Es Claude Code.** No es un concepto de dominio: es el sistema que aloja al producto.
- **Cumple seis papeles** (sección 3.4).
- **Los acoples se nombran y no se rompen acá** (decisión D3).

### 4.3 Lo que no es lo mismo

| Desigualdad | Se sostiene | Por qué, con evidencia |
|---|---|---|
| Task ≠ WorkUnit | sí | Una Task tiene un Plan con N WorkUnits (`plan.py:173-175, 213`). La Task es externa; la WorkUnit existe solo adentro del Plan |
| TaskContext ≠ Knowledge | sí | El TaskContext es un snapshot de la tarea. NormativeKnowledge es lo aceptado de las fuentes. Un adjunto que no está en el registro es "documentación contextual" (`source-registry.schema.json:27`). La palabra se cruza en `knowledge_status`, que es SectionConfidence |
| Knowledge ≠ Source | sí | Una ManagedSource es la identidad de un documento. NormativeKnowledge es lo que quedó CURRENT después de observar y aceptar (`frescura.py:8-12`) |
| Capability ≠ Tool | sí | Son conceptos con significado y dueño distintos: la capability la declaran las integraciones y el roster y la pide una WorkUnit, y la HostTool la da Claude Code. Ninguna capability declarada se llama como una HostTool, pero ningún contrato lo impide: `requiredCapabilities` no tiene patrón, y un `Read` pedido se vuelve un CapabilityGap, no un rechazo (`capacidades.py:29-55`). HarnessTool es una tercera cosa, dormida |
| Agent ≠ Skill | sí | El registro separa `agents[]` de las `skills[]` de cada dueño (`reglas/agent-registry.json`). El Host carga las dos como markdown |
| Agent ≠ Capability | sí | El agente es un rol. La capacidad la pide la WorkUnit y la dan una Integration o el entorno. Nada las liga (C-25) |
| Policy ≠ Check | sí | POLICY y CHECK son tipos distintos del registro (`control-registry.schema.json:17`). Los datos actuales de G2 declaran un mismo id como las dos cosas, y eso es un defecto de los datos, no una excepción: `seguridad.colisiones_de_id` lo diagnostica como `SECURITY_CONTROL_ID_TYPE_COLLISION`, y el módulo dice que se arregla en origen (`bin/orquestacion/seguridad.py:37-39, 281-295`). Hoy ese diagnóstico solo lo llaman los tests: ningún comando lo emite. Es deuda anotada en `PENDIENTES-FH.md` |
| Check ≠ development test | sí | Se distinguen por contrato, ciclo de vida, dueño y mecanismo. El GuardrailCheck es `verificar(...) -> [str]` en PostToolUse, y se instala. El ControlCheck es `evaluar(...)`, de Governance: lo declaran el registro y las matrices, y vive en `controles/checks/`, que hoy no se instala (deuda conocida). Los tests de `tests/casos/` verifican la fábrica y nunca llegan a un proyecto |
| Evidence ≠ Result | sí | La Evidence no lleva resultado. Un EvaluationRecord tiene `result` y `evidenceFingerprints` por separado (`security-ledger-event.schema.json`) |
| Plan ≠ Execution | sí | `READY_FOR_EXECUTION` "es un estado del documento" (`orquestacion/__init__.py:9`; `plan.py:12`). No existe Execution |
| Execution ≠ Accounting | sí, aunque el nombre diga lo contrario | `execution-accounting-event` reconstruye la actividad de la sesión desde la transcripción y la `statusLine`. Ningún orquestador emite nada (C-12) |
| Result ≠ Evidence | sí | Es la misma desigualdad vista desde el otro lado. En la refutación, el veredicto cita evidencia dentro del alcance (`refutacion.py:1099-1116`) |
| Claude Code ≠ HARNESS | sí | Claude Code es el Host. HARNESS no llama a ningún modelo, no lanza agentes y no tiene runtime propio (sección 3.3) |
| Task ≠ HostSession | **hoy se confunden** | En el ledger de la barra, `taskId` es el `session_id` (`statusline.py:190`). Se resuelve nombrando la LedgerKey (E-28 y E-43) |

---

## 5. Mapa de contextos

### 5.1 Los contextos y por qué cada uno lo es

| Contexto | Lenguaje propio | Invariantes propias | Dueño | Datos | Ciclo de vida | Depende de |
|---|---|---|---|---|---|---|
| **Work Intake** | tarea, Ficha, adjunto, procedencia, sección, hueco | TaskKey, Jira obligatorio, procedencia, redacción | sin dueño declarado en `CLAUDE.md` | `.claude/contextos/` | por Task, se regenera entero | Catalog (capacidades), Host |
| **Project Knowledge** | zona, techo, ficha de módulo, índice | write-back antes de desalojar; regeneración entera | el equipo del proyecto | `CLAUDE.md`, `docs/conocimiento/`, `docs/codebase/`, versionados | lo cambian personas y modelos | Host |
| **Normative Sources** | fuente, versión, sha256, canal, aceptar, posponer, vigente | identidad por el registro; aceptación por una persona; frescura relativa al canal | sin dueño declarado | `reglas/source-registry.json`, `.claude/harness.fuentes.json`, `runtime/knowledge-refresh.json` | observar → aceptar → vigente | Work Intake (la Ficha como canal) |
| **Planning** | plan, propuesta, unidad, dominio, tier, aprobación, hueco | las del Plan (4.2) | sin dueño declarado | `.claude/planes/` | por Task y por versión | Work Intake, Catalog, Governance, Normative Sources (compuerta) |
| **Catalog** | agente, skill, dominio, capacidad, integración, disponible, ambiente | registro autoritativo; forma de la capability; lo no declarado se deniega en una base | sin dueño declarado | `reglas/agent-registry.json`, `roster.json`, `.claude/harness.capacidades.json`, `database-environment-access-policy.json` | se instala; la disponibilidad la decide la validación del entorno (`correr_bootstrap`) | Host (archivos `.md`) |
| **Governance** | regla, señal, aplicabilidad, control, evidencia, resultado, veredicto, hallazgo | las de los controles, las señales y la refutación (4.2) | sin dueño declarado | `reglas/` (matrices, registros, inventarios), `.claude/refutaciones/`, `runtime/security/` | por Task (refutación y seguridad) y por versión de la norma | Planning (el Plan), Normative Sources, Catalog |
| **Guardrails** | evento, herramienta, hallazgo, deny, ask | solo los secretos bloquean; hasta 8 avisos; salida 0 | `harness-hook-engineer` | `comun/reglas/secretos.patrones.json`, checks | por llamada de herramienta, sin estado | Host, Project Knowledge (zonas) |
| **Observability** | evento, tokens, costo, ventana, conciliación, presupuesto | id por dedupKey; las fotos no se suman; nadie decide con el ledger | sin dueño declarado | `.claude/runtime/accounting/`, `harness.presupuesto.json` | append-only | Host (transcripción, `statusLine`) |
| **Host Integration** | instalar, actualizar, lock, huella, reinicio, componente | lo regenerable no se edita; lo de fuera sobrevive; PARCIAL y no BLOQUEADO | `harness-backend-engineer` | `.claude/harness/`, `harness.lock.json`, `harness.installation.json` | instalación → `-Update` → `-Uninstall` | todos, como lectura de su salud |


**Nueve contextos delimitados, y un límite reservado.** `Execution` no figura en la tabla porque no es
un contexto: no tiene lenguaje, datos, invariantes, ciclo de vida ni implementación. Es el límite
donde la próxima Task va a ubicar la ejecución, y está vacío (10.1).

### 5.2 Las relaciones

```text
                       Host (Claude Code) — externo
     hooks ▼            statusLine ▼            subagentes/skills ▼          transcripción ▼
  Guardrails        Observability ◄──────────── (la sesión corre los agentes) ──── Observability
     │                    ▲
     │ lee las zonas      │ metadatos de atribución de la refutación (refutacion.atribucion)
     ▼                    │
 Project Knowledge     Governance ◄──── compuerta ──── Normative Sources ◄── canal: Ficha ── Work Intake
     ▲                  ▲     │                                                       │
     │ hash             │     │ resolucion normativa por unidad                       │ TaskContext
     │                  │     ▼                                                       ▼
 Work Intake ───────────┼── Planning ◄────────── registro autoritativo ─────────── Catalog
                        │      │
                        └──────┘  la refutación compila desde el Plan

 Host Integration: instala todo y lee la salud de Observability, Governance y Normative Sources
 Execution: ningún contexto le escribe ni le lee, porque no existe
```

| Relación | Tipo | Qué cruza |
|---|---|---|
| Work Intake → Planning | Cliente-proveedor | El TaskContext. Planning se conforma a `task-context/1.0` |
| Catalog → Planning | Conformista | Planning acepta lo que diga el registro: agentes, skills, capacidades |
| Governance ⇄ Planning | **Partnership, con ciclo** | Planning lleva la resolución normativa adentro de cada WorkUnit, y Governance compila la refutación desde el Plan. El acople es real: el Plan carga datos de Governance. Se documenta y no se rompe |
| Normative Sources → Governance y Planning | Cliente-proveedor | La decisión de la compuerta, antes de `plan`, `refute --compile` y `seguridad` |
| Host → Guardrails y Observability | Capa anticorrupción | `comun/hooks/lib/hook.py`, `bin/contabilidad/adaptadores/claude_code.py` y `statusline.py` traducen lo de Claude Code. Las fugas son las de 3.4 |
| Governance → Observability | Publicación | La refutación arma la metadata de atribución. El resumen de seguridad copia totales del Bloque 4 solo para mostrarlos |
| Host Integration → todos | Proveedor de instalación | Copia, registra y mide la salud. No interpreta el dominio de nadie |

### 5.3 Lo que se descartó

- **Partir Governance en Normativa, Refutación y Seguridad.** Comparten el lenguaje (`ruleKey`,
  control, evidencia, resultado), los registros y el dueño. La refutación se conforma a las matrices
  y al registro de controles. Partirlo obligaría a duplicar qué es una `ruleKey`.
- **Juntar Work Intake y Project Knowledge.** Tienen otro productor (un CLI determinista contra un
  modelo y una persona), otra persistencia (`.claude/` contra el repo) y otro ciclo de vida (por
  tarea contra versionado).
- **Meter Normative Sources en Governance.** Tiene invariantes que nadie más tiene: la aceptación por
  una persona y el hash del original. Governance lo consume solo por la compuerta.
- **Meter Catalog en Planning.** El registro tiene su propio ciclo de validación, y también lo
  consumen Governance (el ruteo de controles y las huellas de las skills en la refutación) y la
  bienvenida.
- **Hacer de Execution un contexto.** No tiene lenguaje, ni datos, ni invariantes, ni código. Se
  nombra para que el próximo cambio sepa dónde va. Inventarle contenido sería diseñar la Task 3
  acá.

---

## 6. Clasificación DDD, sin ceremonia

La lista es cerrada, y el documento canónico la usa tal cual:

| Clasificación | Cuándo, en este repo |
|---|---|
| Aggregate Root | Hay invariantes que se validan sobre el todo antes de escribir. **Plan** es el caso fuerte; los demás (SourceState, AgentRegistry, Refutation e Installation) se validan enteros |
| Entity | Tiene identidad propia y vive adentro de un agregado o de un registro: WorkUnit, Agent, Skill, Control, NormativeRule, RefutationUnit… |
| Value Object | Se define por su valor y no tiene identidad propia: TaskKey, Capability, ModelPolicy, Evidence… |
| Snapshot | Un documento derivado que se regenera entero y no se modifica en partes: TaskContext, ProjectContext, SecuritySummary… |
| Record | Una constancia append-only de algo observado o decidido: AccountingEvent, EvaluationRecord, SourceAcceptance, RefutationVerdict… |
| Domain Service | Una decisión del dominio en código, sin estado: ModelRouter, ConsumptionGate, ControlCheck, GuardrailCheck… |
| Domain Policy | Una regla del dominio expresada como dato o como procedimiento: NormativeMatrix, Policy, ProjectMemory |
| Application Service | Un subcomando de `dev-harness.py` que orquesta un caso de uso: `contexto`, `plan`, `refute`, `fuentes`… |
| DTO / Contract | Una entrada o salida sin autoridad: PlanProposal |
| Configuration | Datos o parámetros que no deciden nada solos: registros, HarnessConfig, CostBudget |
| External | Vive fuera de HARNESS y HARNESS solo lo lee o lo usa: Host, HostSession, HostTool, TaskRecord, Ficha, Task |
| Infrastructure | Cómo se guarda, se valida o se transporta: el validador, los ledgers como archivos, las clases HTTP, `rutas.py`, el instalador |

Lo que **no** se usa, y por qué:

- **Domain Event.** Ningún código de HARNESS reacciona a un evento. Los NDJSON son constancias: de
  observabilidad (`AccountingEvent`) o de evidencia (`EvaluationRecord`). Llamarlos Domain Event
  inventaría un bus que no existe. `FINDING_CREATED`, `FINDING_UPDATED` y `FINDING_RESOLVED` son lo
  más parecido, y nadie los consume.
- **Repository.** Cada agregado se guarda en un archivo JSON con su ruta conocida. Un patrón
  Repository no saca ninguna ambigüedad.
- **Factory.** `plan.armar` y `refutacion.compilar_unidades` ya son eso, y nombrarlos así no
  agrega nada.

---

## 7. Invariantes

**Estado** dice si el invariante se cumple hoy (con su evidencia), si lo agrega este cambio (con el
escenario) o si solo se documenta, con el ítem pendiente.

| # | Invariante | Contexto | Estado |
|---|---|---|---|
| I-01 | Ningún artefacto de una Task se escribe con una clave que no cumple `^[A-Za-z][A-Za-z0-9_]*-[0-9]+$` | Work Intake | Hoy, en `contexto` y `refute` por validación, y en `plan` por el patrón de `plan_id` (E-25). `seguridad` no lo cumple, y este cambio lo agrega (E-26) |
| I-02 | Todo artefacto de una Task se nombra con la misma TaskKey | Work Intake | Hoy, de hecho (E-30). Las dos reglas del código son idénticas, y E-27 fija que acepten lo mismo. Unificarlas es el pendiente 12 |
| I-03 | Sin `jira.issue.read` no hay TaskContext | Work Intake | Hoy (`tarea.py:34-41`) |
| I-04 | Cada sección del TaskContext tiene su SectionConfidence y su procedencia, y el texto de afuera se redacta | Work Intake | Hoy, salvo que no se encuentre el catálogo, y entonces no se redacta (C-17b) |
| I-05 | Si Jira devuelve una clave distinta de la pedida, el TaskContext lo dice | Work Intake | Lo agrega este cambio (E-29) |
| I-06 | El ProjectContext se regenera entero, y su hash no depende del reloj | Project Knowledge | Hoy (`contexto-armar.py:973-988`) |
| I-07 | Nada sale de CACHÉ sin estar escrito y verificado; FIJA no se purga; los techos avisan | Project Knowledge | Hoy (`flush-memoria.md:50-67`; `claude-md-zonas.py:3-4`) |
| I-08 | La identidad de una fuente la da el registro, y el hash es del original | Normative Sources | Hoy (`registro_fuentes.py:8-14`) |
| I-09 | Una aceptación la escribe una persona nombrada, contra lo observado en la misma corrida | Normative Sources | Hoy (`dev-harness.py:843-873`) |
| I-10 | La frescura es relativa al canal | Normative Sources | Hoy (`frescura.py:14-16`) |
| I-11 | Un Plan por Task: `pln_<TaskKey>` | Planning | Hoy (`plan.py:213`) |
| I-12 | Al menos una WorkUnit; dependencias existentes; sin ciclos | Planning | Hoy (`plan.py:90-105, 174-175`) |
| I-13 | Los ids de WorkUnit son únicos en el Plan | Planning | Lo agrega este cambio (E-18, E-20). Hoy colapsan en silencio (`plan.py:97`) |
| I-14 | El dominio de una WorkUnit es uno de los dominios del Plan, y todos son conocidos | Planning | Los dominios conocidos, hoy (`plan.py:168-172, 131-135`). La pertenencia la declara el schema (`orchestration-plan.schema.json:50`) y no la cumple el código, porque `dominios_del_plan` no se usa (`plan.py:256`). Este cambio la agrega (E-19) |
| I-15 | El estado del Plan y de cada WorkUnit se deriva del contenido al armarlo, y nadie lo cambia después | Planning | Hoy (`plan.py:273-279, 371-379`). Este cambio lo fija (E-15, E-21, E-22) |
| I-16 | Los estados posibles son los que el código escribe, y ninguno habla de delegar ni de ejecutar | Planning | Lo agrega este cambio, en el contrato `orchestration-plan/2.0` (E-13, E-14) |
| I-16b | Un plan guardado se lee por una sola regla: un `2.0`, o un `1.0` cuyos estados existen en 2.0, que se migra al reescribirlo. Cualquier otra cosa se rechaza sin crear ni modificar el plan, la refutación de esa Task ni nada derivado del plan | Planning | Lo agrega este cambio (D16; E-16, E-16b, E-16c) |
| I-17 | El tier lo decide el ModelRouter, no la propuesta | Planning | Hoy (`modelo.py:65-78`) |
| I-18 | La propuesta no tiene autoridad: el código arma el Plan y lo valida antes de escribirlo | Planning | Hoy (`plan.py:382-402`) |
| I-19 | El AgentRegistry decide si un agente existe; el disco solo diagnostica | Catalog | Hoy (`registro_agentes.py:3-4`). El schema dice lo contrario y este cambio lo corrige (E-23) |
| I-20 | Una capability declarada (de integración, local, de permisos o del manifiesto) tiene forma de nombre con puntos en minúsculas y no es el nombre de una HostTool | Catalog | Hoy, de hecho. Este cambio lo fija (E-37, E-38). No vale para lo que pide una propuesta: `requiredCapabilities` no tiene patrón, y un nombre de HostTool queda como CapabilityGap |
| I-21 | Soportada la declara la clase de la integración; disponible quiere decir validada ENABLED en esta máquina | Catalog | Hoy (`registro.py:10-16`). Dos textos dicen que sale del manifiesto y este cambio los corrige (E-39) |
| I-22 | El ControlRegistry declara y el disco diagnostica, y ninguno de los dos dice si un control se cumple | Governance | Hoy (`controles.py:6-16`) |
| I-23 | El valor de una señal sale de su evidencia, y una señal ausente deja la regla sin resolver, nunca en "no aplica" | Governance | Hoy (`senales.py:220-287`; `orchestration-plan.schema.json:185`) |
| I-24 | Una RefutationUnit se cierra por check solo bajo las cinco condiciones de 4.2 | Governance | Hoy (`refutacion.py:670-735`) |
| I-25 | Los `declaredChecks` de una RefutationUnit son los checks que declara la norma, estén registrados o no, y nunca un GuardrailCheck. Un check declarado que no está en el registro no puede cerrar la unidad: solo un ControlCheck registrado e `INSTALLED` (I-24) | Governance | Lo agrega este cambio (E-31). Hoy se mezclan con GuardrailCheck (`refutacion.py:621-623`) |
| I-26 | Solo el harness escribe los campos de resolución y las huellas de un veredicto, y solo `cumple`/`incumple` entran a la caché | Governance | Hoy (`refutacion.py:100-101, 779-783, 1068-1072`) |
| I-27 | HARNESS nunca produce una aprobación oficial de seguridad: solo registra evidencia de una autoridad externa | Governance | Hoy (`bin/orquestacion/evaluacion.py:75-80, 126-182`) |
| I-28 | La Evidence no lleva el resultado, y el resultado la referencia por huella | Governance | Hoy, en el ledger de seguridad. Se documenta |
| I-29 | Lo único que bloquea es un secreto, en PreToolUse | Guardrails | Hoy (`comun/hooks/pre-tool-use.py:1`; `hook.py:88-99`) |
| I-30 | Un GuardrailCheck devuelve textos, como mucho ocho por evento; uno que revienta se saltea; los hooks salen con 0 | Guardrails | Hoy (`comun/hooks/lib/reglas.py:16, 62-65`; `hook.py`) |
| I-31 | Un AccountingEvent se identifica por adaptador, tipo y dedupKey | Observability | Hoy (`eventos.py:284-292`). Falla cuando no hay dedupKey (C-15) |
| I-32 | `CONTEXT_WINDOW_OBSERVED` no se suma | Observability | Hoy (`agregacion.py:7-9, 108-117`) |
| I-33 | Nada fuera de Observability lee un ledger de contabilidad para decidir algo | Observability | Hoy, de hecho. Este cambio lo fija (E-42) |
| I-34 | Una LedgerKey es una TaskKey o el `session_id` de una HostSession | Observability | Hoy, sin nombre ni validación. Este cambio la valida (E-28) y la nombra (E-43) |
| I-35 | Un componente que no está ACTIVE deja la instalación PARCIAL, nunca BLOQUEADA | Host Integration | Hoy (`bienvenida.py:25-30`) |
| I-36 | `.claude/harness/` se regenera entero, y lo de fuera sobrevive al `-Update` | Host Integration | Hoy (`install.ps1:2163-2203`; `UPGRADE.md:256-257`) |
| I-37 | HARNESS no lanza agentes ni llama a modelos: el único `subprocess` es `git` o `markitdown` | límite de la ejecución | Hoy, de hecho. Este cambio lo fija (E-41) |
| I-38 | Nada emite `TASK_*`, `WORKUNIT_*` ni `AGENT_RUN_*` | límite de la ejecución | Hoy, de hecho. Este cambio lo fija (E-40) |
| I-39 | Un concepto significa lo mismo en el árbol de la fábrica y en un proyecto instalado | todos | Hoy no, por `controles/` (3.5): los ids de Vu3 a Vu10 y la línea base de C3. Este cambio fija lo que se cumple (E-44) y nombra lo que no, que sigue en FH #4 |

---

## 8. Vocabulario

En **Nombre canónico**, una celda en blanco quiere decir que el término no es un concepto: es una
variable, una palabra clave de JSON Schema o prosa.

| Término actual | Dónde | Qué significa hoy | Nombre canónico |
|---|---|---|---|
| tarea / task / ticket / issue / HU / historia | `tarea.py`, `dev-harness.py:878`, `contexto-de-tarea.md:13` | el trabajo pedido, o su registro en Jira | **Task** si es el trabajo; **TaskRecord** si es el issue |
| `task.key` / `task_key` / `taskKey` / clave | task-context, plan, refutación, CLI | la identidad | **TaskKey** |
| `taskId` | `execution-accounting-event`, `security-ledger-event` | la tarea, o el id de sesión en la barra | **LedgerKey** en contabilidad; **TaskKey** en seguridad |
| propuesta / proposal | `dev-harness.py:1847`, `dev-orchestrator.md:28` | la entrada de `plan` | **PlanProposal** |
| plan / orchestration plan / plan de ejecución | schema, bienvenida | el documento | **Plan**. "Plan de ejecución" se lee como si ejecutara, y no ejecuta |
| `workUnits` / unidad de trabajo / WorkUnit | plan, prosa | la porción de la Task | **WorkUnit** |
| unidad / unit | `refutacion.py`, `contabilidad/reporte.py:65` | una WorkUnit o una RefutationUnit | se nombra cuál: **WorkUnit** o **RefutationUnit** |
| step / paso / etapa | skills, resolvedores | un paso de un procedimiento | — |
| `requiredChecks` | `plan.py:311` | los checks del hook del dominio | **GuardrailCheck** (el campo no cambia de nombre) |
| `declaredChecks` | matriz, plan, refutación | los controles CHECK de la regla, y hoy también los del hook en la refutación | **ControlCheck** |
| check | 4 sentidos (sección 1) | — | **GuardrailCheck**, **ControlCheck**, **CheckSpecification** y la entrada `checks.json` (resultado de un ControlCheck) |
| control | registro, autoridad O2, `controlResults` | lo que una regla exige que exista | **Control**. "La autoridad de control" es **ExternalSecurityApproval** |
| policy / política | 5 sentidos (sección 1) | — | **Policy** solo para el Control de tipo POLICY; **CostBudget**, **RefreshAgenda** (su política), **ConsumptionPolicy** y **DatabaseAccessPolicy** (dormida) para los demás |
| `policies` / `applicablePolicies` del plan | `plan.py:231, 304` | textos libres de la propuesta, sin validar | — (C-09b) |
| review | 7 sentidos | — | **Review** para el Control de tipo REVIEW y su documento. `REVIEW_EVALUATION` es un **EvaluationRecord** de un veredicto |
| verdict / veredicto | 6 sentidos | — | **RefutationVerdict**. La compuerta da una **decisión**. SDD es de la fábrica |
| finding / hallazgo | 11 sentidos | — | **Finding** si tiene estado; **GuardrailFinding** si es el texto de un hook |
| evidence / evidencia | 11 sentidos | — | **Evidence**. `controles/lib/evidencia.py` es Infrastructure: "esto no es un control" |
| result / resultado / outcome | controles, resumen, OWASP | el estado de una evaluación | **EvaluationResult** |
| salida / output | variables locales, tokens de salida | — | — |
| approval / aprobación | 6 sentidos | — | **ModelTierApproval**, **ExternalSecurityApproval** y **SourceAcceptance**. El `HUMAN_APPROVAL_REQUIRED` del presupuesto es una evaluación del **CostBudget**. La promoción de una HarnessTool está dormida |
| source / fuente | 7 sentidos | — | **ManagedSource**, **Channel** y **ProvenanceRef**. El adaptador de uso es Infrastructure; la tupla norma-control es **NormativeStandard** + `ruleKey`; la capa de una variable es Infrastructure |
| knowledge / conocimiento | 4 sentidos | — | **NormativeKnowledge**, **ProjectMemory** (`docs/conocimiento/`), **SectionConfidence** (`knowledge_status`) y **Ficha** |
| contexto / context | 5 sentidos | — | **TaskContext**, **ProjectContext**, **ContextSlice** y **ContextBarState** (la ventana). Lo que inyecta SessionStart es salida del Host Integration |
| ficha | Jira y `docs/codebase` | la Ficha de Proyecto, o una ficha de módulo | **Ficha**; la ficha de módulo es parte del **ProjectContext** |
| proyecto | 4 sentidos | clave de Jira, proyecto de GitLab, raíz local y `project_id` | se nombra cuál |
| adaptador / adapter | integraciones y contabilidad | dos cosas | **Integration**; el adaptador de contabilidad es Infrastructure |
| caché | zona CACHÉ y caché de refutación | dos cosas | zona de **ProjectMemory**; caché de **Refutation** |
| execution / ejecución | `execution-accounting-event`, "contabilidad de ejecución" | la actividad de la sesión | **AccountingEvent**; el nombre del archivo no cambia (D5) |
| run / corrida | refutación, una invocación del CLI | el agregado de la refutación, o una invocación | **Refutation** (su `run.json`); una invocación no es un concepto |
| `SESSION_COMPLETED` | `contrato.py:222-227` | la foto acumulada del proveedor | **AccountingEvent** de tipo foto del proveedor; el tipo no cambia de nombre (D5) |
| `PENDING` de una unidad | `plan.py:279` | planificada, sin nada que la frene | se define así en el schema y en el documento |
| capability / capacidad / permiso | `capacidades.py`, `permisos-por-capacidad.json` | la habilidad, o su mapa de permisos | **Capability**; el mapa de permisos es **Configuration** de HarnessTool |
| role / rol | plan `agents[].role`, apps | el rol de un agente, o el de un usuario de la app | **Agent**; el rol de un usuario no es de este dominio |
| tool / herramienta | `tools:`, `tool-contract` | herramienta de Claude Code, o artefacto generado | **HostTool** o **HarnessTool** |
| budget / presupuesto | `budget-policy`, `sessionBudget` | plata y contexto, o llamadas premium | **CostBudget** o **ConsumptionPolicy** |

**Regla del vocabulario:** este cambio no renombra ningún identificador, módulo, archivo, campo de
contrato ni valor de enum. El nombre canónico vive en el documento y apunta al actual (decisión D9).

---

## 9. Contratos existentes por concepto

| Concepto | Contrato | ¿Contradice el modelo? |
|---|---|---|
| TaskKey | `task-context` (`meta.task_key`, `context_id`), `orchestration-plan` (`plan_id`) | No. E-27 fija que acepten las mismas claves |
| TaskContext | `task-context/1.0` | Sí, sin arreglo acá: el hash, `local_path` y `origin` (C-17, C-18) |
| ProjectContext | `project-context/1.1` | No |
| SourceState, SourceAcceptance | `sources-state/1.1` | Sí, sin arreglo acá: decisiones humanas en un archivo que se declara derivado (C-31) |
| Plan, WorkUnit | `orchestration-plan/1.0`, que pasa a `2.0` | **Sí, se arregla:** los estados, con cambio de versión mayor y regla de lectura (C-01, C-02, D16), y quién decide si un agente existe (C-04). Sin arreglo: `normative.standards` y los extras sin declarar (C-36) |
| ModelTierApproval | `humanApprovals[]` | Declara tres estados que nadie escribe. Se documentan como hueco (C-03) |
| AgentRegistry | `agent-registry/1.0` | Sin arreglo: claves decorativas (`rules.*`, `agentTypes`) |
| Capability, Integration | clases de integración, `roster.json`, `harness.capacidades.json` | **Sí, se arregla en dos textos** (C-28) |
| HarnessTool | `tool-contract`, `tool-registry` | Dormido (C-26, C-27) |
| NormativeSignal | `normative-signal` | **Sí, se arregla:** dice que es solo de ES0901 (C-11) |
| Control | `control-registry` | **Sí, se arregla:** dice que los checks del hook corren en PreToolUse (C-10) |
| RefutationUnit | `refutation-unit/1.0` | **Sí, se arregla en el productor**, sin cambiar el schema (C-09) |
| AccountingEvent, LedgerKey | `execution-accounting-event` | **Sí, se arreglan las descripciones** (C-12, C-13). Los nombres no cambian |
| EvaluationRecord, SecuritySummary | `security-ledger-event`, `security-summary` | Sin arreglo acá: extras sin declarar y eventos no idempotentes (C-36, C-53) |
| Installation | `harness-installation/1.1` | Sin arreglo acá: copia en línea y `knowledgeRefresh` sin declarar (C-29) |

---

## 10. Gaps

### 10.1 El límite de la ejecución

**Lo que existe en 0.29.0:**

- **El Plan en `READY_FOR_EXECUTION`**, que es un estado del documento.
- **La WorkUnit en `PENDING`**, que quiere decir que nada la frena.
- **`executionOrder`**, un orden topológico que no es un cronograma.
- **`ModelPolicy`** con el tier de cada unidad, y la **ModelTierApproval** en `PENDING`.
- **El vocabulario de contabilidad sin productor:**
  - `TASK_STARTED` y `TASK_COMPLETED`;
  - `WORKUNIT_STARTED` y `WORKUNIT_COMPLETED`;
  - `AGENT_RUN_STARTED` y `AGENT_RUN_COMPLETED`;
  - `TOOL_CALL_COMPLETED` y `MODEL_ESCALATION_REQUESTED`.

  Lo declaran `bin/contabilidad/eventos.py:27-42` y el schema.
- **Los contratos de salida en prosa:**
  - el "Output Contract" de cada especialista: `agentResult` con `COMPLETE|PARTIAL|BLOCKED|FAILED`
    (`agents/dev-backend.md:101-114`);
  - los "Result Statuses" de las skills, con otro conjunto (`skills/dev-backend-implementation/SKILL.md:459-534`).

  Ninguno de los dos tiene schema, nadie los lee y no coinciden entre sí (C-24).
- **Campos que nadie lee:**
  - `sessionBudget.maxRetries` (`consumo.py:23`);
  - `modelPolicy.allowEscalation`;
  - `modelo.escalar`, que no tiene quien lo llame (`modelo.py:91-106`);
  - `retryPolicy` y `timeoutSeconds` del `tool-contract`.
- **La refutación** como precedente de "HARNESS entrega, el Host corre, HARNESS registra y valida"
  (3.3).
- **La revisión automática de fuentes**, como el único ciclo de intentos que persiste.

**Lo que no existe:**

- un agregado `Execution`;
- un `ExecutionRequest` o un `ExecutionResult`;
- un estado posterior a `READY_FOR_EXECUTION`;
- un ejecutor;
- un estado de corrida persistido por WorkUnit o por corrida de agente;
- un ciclo `PENDING → RUNNING → terminal`;
- un reintento, una reanudación o un checkpoint genéricos;
- un cliente de modelo;
- un vínculo entre una corrida de agente y una WorkUnit, salvo el texto libre de `--unidad` y
  `--agente` en contabilidad (`dev-harness.py:1373`).

**Lo que este cambio deja fijado para la Task siguiente, sin diseñarla:**

- **Dos invariantes que valen hoy**, y que solo se pueden romper con una decisión escrita:
  - la contabilidad no es estado de ejecución (I-33);
  - el estado del Plan se deriva del contenido del Plan (I-15).
- **Tres preguntas que la Task 3 tiene que contestar en su propia spec:**
  1. dónde vive el estado de una ejecución;
  2. qué forma tiene lo que vuelve de un agente: hay que distinguir EvaluationResult de Evidence;
  3. si el contrato de salida es el `agentResult` de los agentes, los "Result Statuses" de las
     skills, o ninguno de los dos.

### 10.2 Otros huecos, sin construir acá

- **Ningún comando resuelve una ModelTierApproval**, y `fuentes` no tiene cómo posponer (C-03, C-32).
- **La PlanProposal no tiene schema.**
- **`summary.json` declara `execution-summary/1.0` sin schema.**
- **`harness.capacidades.json`, `runtime/contextbar.json` y `harness.integraciones.json`** tienen
  forma solo en `bienvenida.py`.
- **Ningún productor de evidencia del ledger** tiene camino de CLI, salvo dos: `desde_frescura` y
  `desde_refutacion`.
- **No hay una Task en código.** Es a propósito (D1).

---

## 11. Las decisiones, y por qué

### D1. La Task es externa, y HARNESS formaliza solo su identidad

HARNESS no tiene ni el estado ni el ciclo de vida de una Task: los tiene Jira, y todo lo que HARNESS
guarda de una Task es un snapshot o un documento derivado nombrado por su clave. Formalizar
`TaskKey` alcanza: es un valor con una forma, y todo artefacto de una Task la lleva igual (I-02).
Dónde hace falta validarla de nuevo lo decide D15.

Lo que se descartó:

- **Un agregado `Task`:** le inventaría un ciclo de vida que HARNESS no maneja.
- **El issue de Jira como entidad de dominio:** ata el dominio a un proveedor. El issue es un
  `TaskRecord` externo y se lee por la `Integration` de Jira.

### D2. Nueve contextos, y un límite reservado para Execution

HARNESS tiene hoy nueve contextos delimitados. `Execution` no es un décimo: no tiene lenguaje, datos,
invariantes, ciclo de vida ni implementación. Es un límite reservado, con nombre para que el próximo
cambio sepa dónde va, y sin ningún concepto, contrato ni estado.

Cada contexto se justifica en 5.1 y lo descartado está en 5.3. El ciclo entre Planning y Governance
se acepta y se nombra: el Plan carga la resolución normativa de cada unidad porque la refutación la
necesita unidad por unidad.

### D3. El Host no es dominio

Claude Code es `External` y tiene seis papeles. Las fugas de la sección 3.4 se documentan y no se
rompen en este cambio:

- cambiar `CLAUDE_CODE_STATUSLINE` toca un enum persistido;
- cambiar el bloque `contextBar` toca el estado de la instalación;
- separar la sesión de la tarea en el ledger cambia dónde se guarda lo que ya se registró.

Las tres capas anticorrupción ya existen: `lib/hook.py`, `adaptadores/claude_code.py` y
`statusline.py`.

### D4. El plan describe un documento, y su schema dice solo los estados que el código escribe

Del enum del plan salen RECEIVED, ANALYZING, PLANNING, WAITING_FOR_TOOL, READY_FOR_DELEGATION,
DELEGATING, REPLANNING y FAILED. Del enum de la unidad sale READY. Ningún productor los escribe, y
la mayoría describe delegar o ejecutar, cosas que no existen.

Achicar el enum hace inválidos documentos que el schema 1.0 declaraba válidos, así que el contrato
cambia de versión: **`orchestration-plan/2.0`**. La política está en D16, y la lectura de un `1.0`
guardado también.

`plan.py` conserva su marcador interno `PLANNING`, que se pisa antes de validar y nunca llega a un
documento escrito. Sacarlo no evita ningún artefacto inválido, así que no pasa la regla de D15.

Lo que se descartó:

- **Dejarlos como reservados:** un schema no puede anotar un valor del enum, y el validador rechaza
  las palabras clave propias (3.2). No hay cómo marcarlos.
- **Dejarlos en silencio:** sostiene la ambigüedad que este cambio existe para sacar.

La Task 3 diseña los estados de la ejecución en su propia spec, y no hereda estos.

### D5. La contabilidad conserva su vocabulario, y se corrige su descripción

Los 14 tipos de evento quedan, aunque once no tengan productor:

- son lo que un ejecutor emitiría para que la contabilidad lo observe;
- sacarlos rompe el contrato del Bloque 4 y del agregador (`agregacion.py:44-45, 398-400`);
- la ambigüedad la saca I-38, junto con una descripción que diga que no son estado.

**`SESSION_COMPLETED` no se renombra.** El tipo entra en el hash del `eventId`, así que renombrarlo
duplicaría cada evento al reingerir. **`execution-accounting-event` tampoco se renombra:** es el
nombre de un archivo instalado y lo citan el código y la documentación. Se corrigen su descripción y
la de `taskId` (LedgerKey).

### D6. "Check" son tres conceptos, y la refutación deja de mezclarlos

GuardrailCheck, ControlCheck y CheckSpecification tienen nombres canónicos distintos, y
`tests/casos/` no es ninguno de los tres. Los campos de contrato no cambian de nombre: `requiredChecks`
sigue nombrando GuardrailCheck y `declaredChecks` sigue nombrando ControlCheck.

`refutacion.py` deja de unir `requiredChecks` en los `declaredChecks` de la unidad. Esto **pisa** el
punto 3 de las condiciones de cierre de `docs/cambios/refutacion-atomica/spec.md:131-132` ("en
`declaredChecks` o `requiredChecks`"). La razón: el punto 1 exige un CHECK del registro de controles,
y un GuardrailCheck nunca lo es. La unión no cambió jamás una resolución, y solo hacía que la unidad
dijera que declara algo que no declara. No cambian:

- la `cacheKey`, que no incluye `declaredChecks` (`refutacion.py:532-551`);
- los ids `REF-nnn`, que son posicionales por unidad;
- ningún veredicto.

### D7. "Policy" es solo el control de governance

Las otras cuatro políticas reciben nombres calificados en el vocabulario, y no se renombra nada en
el código. Los textos libres `policies` y `applicablePolicies` del plan no los valida nadie ni los
consume nadie. Se documentan y se anotan como pendiente (C-09b).

### D8. "Knowledge" sola no nombra nada

Siempre va calificada: NormativeKnowledge, ProjectMemory o SectionConfidence. El campo `knowledge`
del estado de la instalación es la proyección de NormativeKnowledge (`bienvenida.py:566-604`).

### D9. No se renombra ningún identificador

Los nombres canónicos están en inglés, como pide ADR-0011, y los módulos, el CLI y los archivos de
estado están mayormente en español. Renombrar cambia:

- nombres persistidos: `.claude/planes`, `contextos` y `harness.fuentes.json`;
- huellas, como la de las skills en la caché de refutación;
- hashes, como el `eventId`;
- decenas de tests.

El costo es muy alto para lo que se gana. El documento canónico mapea cada nombre, y la deuda queda
anotada (C-43).

### D10. Los dos invariantes del Plan que hoy fallan en silencio

Los ids únicos y el dominio de la unidad entre los del plan no se inventan acá: el contrato y el
código ya los suponen.

- **Ids únicos.** La identidad de una WorkUnit es (PlanId, `id`). Con ese id se arman las
  dependencias, el orden (`plan.py:97`), las aprobaciones (`humanApprovals[].workUnit`) y las
  unidades de la refutación (`workUnitId`). Una identidad repetida no identifica.
- **El dominio entre los del plan.** El schema dice que `domains` "es lo que decide qué especialistas
  participan: un plan no invoca a todos" (`orchestration-plan.schema.json:50`), y `_armar_unidad`
  recibe `dominios_del_plan` sin usarlo (`plan.py:256`). Una unidad de otro dominio mete a un
  especialista que, según el propio plan, no participa.

Los dos pasan la regla de D15. **Se descartó que el dominio fuera solo un aviso:** el documento
incoherente se escribiría igual.

### D11. El documento canónico vive en la fábrica

`docs/dominio/modelo-canonico.md` no se instala: en un proyecto nadie lo lee, e instalarlo agrega
inventario sin ningún lector. Se descartó un glosario JSON en `comun/` por la misma razón. Si un
agente instalado necesita el vocabulario, eso es otro cambio, con su costo de contexto medido.

### D12. La validación de la TaskKey no normaliza

Aceptar `abc-1` y escribirlo `ABC-1` cambiaría el nombre de los artefactos que ya existen. La clave
se valida y se usa tal cual. Si Jira devuelve otra clave, sea por mayúsculas o porque el issue se
movió, el TaskContext lo registra como conflicto (I-05).

### D13. LedgerKey acepta dos formas

En un proyecto, el ledger de la barra ya está guardado por `session_id`. `contabilidad` acepta una
TaskKey o un UUID de sesión, y rechaza todo lo demás.

### D14. El ADR

ADR-0013 registra estas seis decisiones:

1. los nueve contextos;
2. la Task como identidad;
3. el Host fuera del dominio;
4. Execution como límite reservado;
5. los tres nombres de "check";
6. qué promete `schema_version` (D16).

La regla de inclusión de D15 no va al ADR: es el criterio de alcance de este cambio, no una decisión
de largo plazo. El ADR se escribe durante la construcción, como ADR-0012 en `harness-unico`.

### D15. La regla de inclusión: qué contradicción se corrige en esta Task

> **Un cambio de comportamiento entra en esta Task solo cuando, sin él, el código puede producir o
> aceptar un artefacto que contradice directamente un invariante del modelo canónico.** También entra
> un cambio puramente descriptivo, de documentación o de la descripción de un schema, que saque una
> contradicción con el comportamiento actual sin agregar funcionalidad. Todo lo demás se documenta,
> va a pendientes si corresponde, y no se corrige acá.

El invariante tiene que poder citarse en un contrato o en el código que ya existe, no en una
preferencia. Aplicada hacia atrás a todo lo que la spec proponía:

| Cambio propuesto | ¿Artefacto que contradice un invariante, o descripción? | Resultado |
|---|---|---|
| Ids de WorkUnit únicos (C-05) | `plan` escribe un Plan con dos unidades del mismo id: contradice la identidad de la WorkUnit (D10, I-13) | **Entra** |
| Dominio de la unidad entre los del plan (C-06) | `plan` escribe una unidad con un especialista que, según `domains` (schema `:50`), no participa (I-14) | **Entra** |
| Estados del plan en el schema, versión 2.0 y regla de lectura (C-01, C-02) | El validador de escritura y los dos consumidores aceptan un plan `DELEGATING` o una unidad `READY`, y contradicen I-15 e I-16 (Plan ≠ Execution) | **Entra** |
| Sacar el marcador interno `PLANNING` | Nunca llega a un documento | **No entra**: queda como está (D4) |
| TaskKey en `seguridad` (C-20) | `seguridad <cualquiera>` escribe ledger y resumen con un `taskId` que no es una TaskKey (I-01, I-02) | **Entra** |
| TaskKey en `plan` y `plan` sin clave (C-20) | `plan` no puede escribir un plan con una clave inválida: lo frena el patrón de `plan_id`. Sin clave revienta, pero no escribe nada | **No entra**: pendiente 12. E-25 fija que no escribe |
| Una sola regla de TaskKey en el código | Las dos reglas son idénticas (`dev-harness.py:92`; `refutacion.py:57`): ningún artefacto sale distinto | **No entra**: pendiente 12. E-27 fija que acepten lo mismo |
| Conflicto cuando Jira devuelve otra clave (C-19) | `contexto` escribe un TaskContext con dos claves distintas para la misma tarea y sin conflicto declarado. Contradice que `gaps_and_conflicts.conflicts` registra lo que se contradice, como ya hace con dos Fichas (`proyecto.py:68-76`; I-04, I-05) | **Entra** |
| LedgerKey en `contabilidad` (C-13, C-20) | `contabilidad <cualquiera> --ingerir` escribe un ledger cuya clave no es ni TaskKey ni sesión (I-34) | **Entra** |
| `declaredChecks` sin GuardrailCheck (C-09) | `refute --compile` escribe RefutationUnits que declaran como controles a checks del hook. Contradice "estos checks no son los checks del hook" (`controles.py:10-14`; I-25) | **Entra** |
| Descripciones de `agentExists` y `agents[].exists` (C-04) | Descripción contra comportamiento | **Entra**, descriptivo |
| Descripción de `normative-signal` (C-11) | Descripción contra comportamiento | **Entra**, descriptivo |
| Descripciones de `execution-accounting-event` (C-12, C-13) | Descripción contra comportamiento | **Entra**, descriptivo |
| "PostToolUse" en el registro de controles (C-10) | Descripción contra comportamiento | **Entra**, descriptivo |
| De dónde salen las capabilities soportadas (C-28) | Descripción contra comportamiento | **Entra**, descriptivo |
| `dev-orchestrator.md`, `docs/orquestacion.md`, `docs/contabilidad.md` | Describen lo que el código acepta y la versión 2.0 | **Entra**, descriptivo |
| Documento canónico y ADR-0013 | Son el objeto de la Task, no un cambio de comportamiento | **Entra** |

Ninguna contradicción de la sección 17 marcada para pendientes pasa la regla. Todas son de una de
estas tres clases:

- el artefacto que producen no contradice un invariante del modelo (C-14, C-15, C-49…);
- arreglarlas agrega funcionalidad (C-03, C-32);
- su arreglo cambia una salida que nadie declaró como invariante (C-17, C-21).

### D16. Qué promete `schema_version`, y la compatibilidad de `orchestration-plan`

**La pregunta.** ¿`schema_version` promete solo los documentos que produce el productor oficial, o
todo documento que el schema declara válido?

**La respuesta del repo: todo documento que el schema declara válido.** Es la convención escrita, y
no se elige acá:

- **El precedente.** `interfaces-identidad-ambientes` subió a `project-context/1.1` y escribió el
  criterio. Es 1.1 y no 2.0 "porque el cambio es puramente aditivo: todo documento v1.0 válido sigue
  siendo válido salvo por la cadena de versión". Lo que se juzga es el conjunto de los válidos, no
  el de los producidos. Para el documento ajeno fijó la salida: "lo que corresponde es una
  migración, no un `enum` más flojo. Aceptar las dos versiones en el mismo campo convierte
  `schema_version` en decorado" (`docs/cambios/interfaces-identidad-ambientes/spec.md:96-102`).
- **Los demás casos siguen el mismo criterio.** `harness-installation/1.1` agregó un bloque
  obligatorio y "los archivos 1.0 se migran solos" (`CHANGELOG.md:301-302`). `sources-state/1.1`
  sumó campos opcionales y no subió, porque "un estado viejo sigue validando"
  (`docs/cambios/aceptar-fuentes-en-el-proyecto/spec.md:40-41`).

Achicar el enum no es aditivo: un `1.0` válido con `status: DELEGATING` deja de serlo. Por la
convención, el contrato cambia de versión mayor. **Es la alternativa B: `orchestration-plan/2.0`.** La
A, mantener 1.0 y prometer solo lo producible, contradice el criterio escrito del repo.

Las tres compatibilidades:

| Compatibilidad | Qué se promete |
|---|---|
| **Del productor** | `plan` escribe solo `orchestration-plan/2.0`, en `$id` y en el enum de `meta.schema_version`, que son dos ediciones como pide el precedente. Nunca escribe un 1.0 |
| **Del consumidor** | Hoy, los dos consumidores de un plan guardado, `refute --compile` (`refutacion.py:576, 821`) y `--replanificar` (`dev-harness.py:1223-1228`), no validan ni `schema_version` ni `status`. El precedente pide que la versión signifique algo, así que leen por una sola regla: reconocen `2.0` y `1.0`, y rechazan cualquier otra versión con 2, nombrándola |
| **Del documento guardado** | Un `1.0` cuyo `status` y los de todas sus unidades existen en 2.0 es equivalente a un 2.0, salvo la cadena de versión. Se lee, y se migra la próxima vez que se escribe: `--replanificar` lo escribe como 2.0, con su versión y su historia. Un `1.0` con un estado que no existe en 2.0, como `DELEGATING` o `READY`, **se rechaza**: sale con 2, nombra el campo y el valor, y no crea ni modifica el plan, la refutación de esa Task ni nada derivado del plan (E-16b). No es deshacer toda la aplicación: lo que escribió antes la compuerta normativa queda. **No se migra**, porque no hay un estado 2.0 que signifique "delegando". La salida es regenerarlo con `plan --propuesta` |

Ningún plan escrito por HARNESS 0.29.0 cae en el rechazo: el código nunca produjo esos estados. El
rechazo protege del documento ajeno, escrito o editado a mano, como pedía el precedente.

La caché de refutación no se invalida: la `cacheKey` no incluye el plan. El `planFingerprint` de
`run.json` sí cambia cuando el plan se reescribe como 2.0, pero no es clave de nada.

---

## 12. Qué se construye

| Artefacto | Qué hace | Qué ambigüedad saca |
|---|---|---|
| `docs/dominio/modelo-canonico.md` (nuevo) | El modelo de las secciones 4 a 10. `## Conceptos` abre con la tabla índice, que es la fuente canónica del catálogo, y sigue con un `### <Concepto>` por fila, con los campos fijos de E-02. Lleva el mapa de contextos (nueve contextos y el límite reservado), las clasificaciones, lo que no es lo mismo, el vocabulario y el límite de la ejecución | Que el dominio exista sin estar escrito |
| `docs/adr/0013-modelo-de-dominio-canonico.md` (nuevo) | Las seis decisiones de D14 | Que el lenguaje dependa de quién lo recuerde |
| `comun/schemas/orchestration-plan.schema.json` | Pasa a `orchestration-plan/2.0` en `$id` y en `meta.schema_version` (D16). Los dos enums de `status` (D4). La descripción de `status`, con `PENDING` definido. Las descripciones de `agents[].exists` y `agentExists`: decide el registro | Un plan que promete delegar y ejecutar, una versión que no dice qué cambió, y un schema que dice que decide el disco |
| `harnesses/desarrollo/bin/orquestacion/plan.py` | Escribe `orchestration-plan/2.0`. La regla de lectura de un plan guardado, una sola, para los dos consumidores (D16). Rechaza ids repetidos y unidades de un dominio que no está en el plan, también en `--replanificar`. Esos rechazos y los de la regla de lectura son `PlanRechazado`, una subclase de `PlanInvalido`, y son lo único que la CLI saca con código 2: los `PlanInvalido` que ya existían salen como en `4c6f0f3` (D15). El marcador interno `PLANNING` no se toca (D15) | Unidades que colapsan en silencio, un plan incoherente y un plan ajeno que se acepta |
| `harnesses/desarrollo/agents/dev-orchestrator.md` | Las dos reglas de la propuesta, y `orchestration-plan/2.0` donde dice 1.0 | Que el modelo no sepa por qué se rechaza su propuesta |
| `harnesses/desarrollo/bin/contexto/tarea.py` o `ensamblador.py` | El conflicto, cuando la clave que devuelve Jira difiere de la pedida | Dos claves dentro del mismo documento |
| `harnesses/desarrollo/bin/dev-harness.py` | `seguridad` valida la TaskKey con la regla que ya existe. `--replanificar` lee el plan anterior por la regla de lectura | Un ledger de seguridad con cualquier nombre |
| `harnesses/desarrollo/bin/orquestacion/refutacion.py` | `refute --compile` lee el plan por la regla de lectura. Los `declaredChecks` de la unidad dejan de unir los `requiredChecks` (D6) | Un plan ajeno aceptado en silencio, y dos clases de check en una lista |
| `harnesses/desarrollo/bin/contabilidad/libro.py` | Valida la LedgerKey | Una carpeta de ledger con cualquier nombre |
| `comun/schemas/execution-accounting-event.schema.json` | Solo las descripciones: qué observa, quién lo emite, que no es estado de ejecución, y `taskId` como LedgerKey. Sin cambiar `$id`, enum ni campos | Contabilidad leída como ejecución, y sesión leída como tarea |
| `comun/schemas/normative-signal.schema.json` | La descripción nombra ES0901 y ES0902 | Un contrato que dice ser de una sola norma |
| `harnesses/desarrollo/reglas/control-registry.json` y `bin/orquestacion/controles.py` | "PostToolUse" donde dicen "PreToolUse" | Un check del hook que parece una guarda bloqueante |
| `harnesses/desarrollo/bin/integraciones/registro.py` y `docs/integraciones.md` | Lo soportado lo declaran las clases de integración, no el manifiesto | Dos autoridades para la misma lista |
| `docs/orquestacion.md` y `docs/contabilidad.md` | Los estados canónicos, `orchestration-plan/2.0` con su regla de lectura, y que la contabilidad no es ejecución | Lo mismo, para quien lee la documentación |
| `README.md` | El enlace al documento canónico | — |
| `tests/casos/64_modelo_de_dominio.py` y `tests/casos/64-modelo-de-dominio-instalador.ps1` (nuevos) | E-01 a E-49, con E-16b y E-16c | — |
| Los tests que fijen lo que cambia | Se adaptan los que hagan falta: por ejemplo, los que esperen `orchestration-plan/1.0`, el plan con ids repetidos o los `declaredChecks` de una unidad. Cada test dice por qué | — |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Lo que no se arregla acá, agrupado en los doce títulos de E-48 | — |

**Cada fila de esta tabla pasa la regla de inclusión de D15.** La demostración, cambio por cambio,
está en la tabla de D15. Lo que no la pasó salió de acá y está en `Qué queda afuera`.

Ningún archivo cambia de lugar. El único schema que cambia de versión es `orchestration-plan`, de 1.0
a 2.0. `execution-accounting-event` y `normative-signal` cambian solo descripciones y no cambian ni
`$id` ni versión. `dev-refutador.md` y las `SKILL.md` no se tocan, porque son la huella de la caché de
refutación.

## 13. Qué queda afuera

- **El Execution Engine, un runtime de DAG, un scheduler, reintentos, checkpoints, LangGraph,
  LangChain, RAG, embeddings, vector stores, un parser de intención, una UI y un runtime de modelo
  propio.** Están fuera del pedido. El límite queda nombrado en 10.1.
- **Una entidad o un agregado `Task`.** D1.
- **Renombrar identificadores, módulos, archivos, campos o valores de enum.** D9. Eso incluye
  `SESSION_COMPLETED` y `execution-accounting-event` (D5).
- **Unificar las seis aprobaciones en un solo registro.** Son seis cosas distintas: este cambio las
  nombra, no las junta.
- **Unificar el `agentResult` de los agentes con los "Result Statuses" de las skills.** Es la Task 3.
- **Arreglar el hash del TaskContext, `local_path`, `origin` y los adjuntos con el mismo nombre.** Es
  un comportamiento con su propia compatibilidad: va a pendientes (C-17, C-18).
- **`applicableStandards` siempre vacío, y el aviso de que la matriz no se construyó.** Cambia la
  salida de cada plan: va a pendientes (C-21).
- **Una forma de posponer en el CLI, y dónde se guardan las aceptaciones.** C-31 y C-32.
- **Instalar `controles/`** (FH #4) y **arreglar el Agent Registry en un proyecto instalado.** Ya
  están anotados.
- **Conectar HarnessTool, o sacar los contratos dormidos.** Quedan dormidos y nombrados.
- **Cerrar los schemas abiertos** (`additionalProperties`), **darle schema a `summary.json`** y
  **declarar `knowledgeRefresh`.** C-29 y C-36.
- **Instalar el documento canónico en los proyectos.** D11.
- **Mover carpetas.** No hace falta para ninguna de las ambigüedades de arriba.
- **Reescribir la historia:** `docs/cambios/*`, `docs/versiones/*` y las entradas viejas del
  `CHANGELOG.md`.
- **Las capabilities que nombran las skills sin que ningún catálogo las declare**
  (`filesystem.read`, `dependency.inspect`, `task-context.read`). Arreglarlas toca `SKILL.md`, y eso
  invalida la caché de refutación (C-25).
- **Todo cambio de comportamiento que no pase la regla de D15**, aunque arregle un defecto real.
  Salieron de la construcción al aplicarla:
  - unificar las dos reglas de la TaskKey;
  - que `plan` valide la clave y no reviente sin ella;
  - sacar el marcador interno `PLANNING`.

  Los dos primeros van al pendiente 12. El tercero queda como está, porque no produce ningún
  artefacto.

---

## 14. Escenarios verificables

### El documento canónico

- **E-01** — Existe `docs/dominio/modelo-canonico.md`, y su sección `## Conceptos` abre con una tabla
  índice que es la fuente canónica del catálogo, como la tabla de 4.2 de esta spec. Sobre esa tabla y
  los encabezados `###` de la misma sección:
  1. cada concepto de la tabla aparece exactamente una vez como `### <Concepto>`;
  2. ningún `###` de la sección nombra un concepto que no esté en la tabla;
  3. ningún nombre se repite, sin distinguir mayúsculas, ni en la tabla ni en los encabezados;
  4. todos cumplen E-02.

  No se exige ninguna cantidad: el catálogo se puede corregir. · rojo visto: si
- **E-02** — Cada concepto tiene estos diez campos rotulados: `Qué es`, `Contexto`, `Clasificación`,
  `Identidad`, `Ciclo y estados`, `Invariantes`, `Crea / cambia / lee`, `Persistencia y contrato`,
  `Dónde vive` y `No es`. Uno que no aplica dice `no aplica` y no se omite. · rojo visto: si
- **E-03** — `## Mapa de contextos` declara nueve contextos y, aparte, `Execution` como límite
  reservado, no como contexto.
  - El `Contexto` de cada concepto es uno de los nueve, o `External`.
  - Solo puede tener `External` un concepto clasificado `External`.
  - Cada uno de los nueve tiene al menos un concepto.
  - Ningún concepto tiene `Execution` como contexto.

  · rojo visto: si
- **E-04** — La `Clasificación` de cada concepto es una de las doce de `## Clasificaciones`, y ninguno
  dice `Domain Event`. · rojo visto: si
- **E-05** — Cada uno de los 46 archivos de `comun/schemas/` figura en `Persistencia y contrato` de al
  menos un concepto. Todo schema que nombra el documento existe en disco. · rojo visto: si
- **E-06** — `## Lo que no es lo mismo` tiene un apartado por cada una de las catorce desigualdades
  de 4.3, y cada apartado cita al menos una ruta del repo que existe. · rojo visto: si
- **E-07** — Cada fila de `## Vocabulario` apunta a un concepto del documento o dice
  `no es un concepto`. · rojo visto: si
- **E-08** — No hay un `### Claude Code`. Existe `### Host`, con clasificación `External`, y nombra
  sus seis papeles. · rojo visto: si
- **E-09** — `## El límite de la ejecución` tiene, como ítems, lo que existe y lo que no de 10.1, más
  los dos invariantes y las tres preguntas. · rojo visto: si
- **E-10** — Los veredictos `sostenido`, `contradicho`, `leído` y `sin sustento` figuran como de la
  fábrica, fuera del producto, y separados de `RefutationVerdict`. · rojo visto: si
- **E-11** — `README.md` enlaza `docs/dominio/modelo-canonico.md`. · rojo visto: si

### El ADR

- **E-12** — `docs/adr/0013-modelo-de-dominio-canonico.md` existe, con `estado: aceptada`, y registra
  las seis decisiones de D14. · rojo visto: si

### Plan y WorkUnit

- **E-13** — `orchestration-plan.schema.json` se identifica como `orchestration-plan/2.0` en `$id` y
  en el enum de `meta.schema_version`, que no acepta otro valor. El `status` del plan es exactamente
  `CAPABILITY_RESOLUTION`, `WAITING_FOR_HUMAN_APPROVAL` y `READY_FOR_EXECUTION`.
  · rojo visto: si
- **E-14** — El `status` de una WorkUnit es exactamente `PENDING`, `BLOCKED` y
  `WAITING_FOR_HUMAN_APPROVAL`. La descripción define `PENDING` como planificada y sin nada que la
  frene. · rojo visto: si
- **E-15** — Ningún documento que escriben `plan --propuesta` o `--replanificar`, sobre las
  combinaciones de E-21, tiene un `status` fuera de los conjuntos de E-13 y E-14. El marcador
  interno de `plan.py` no cuenta, porque no llega al documento (D4). · rojo visto: si
- **E-16** — Un plan escrito por el código de `4c6f0f3`, sacado con `git archive`, es un `1.0` con
  estados que existen en 2.0. **Se acepta y se migra al escribirlo:**
  - `refute --compile` lo lee sin regenerarlo y compila las mismas unidades que con `4c6f0f3`: los
    mismos ids, WorkUnits y reglas. Los `declaredChecks` cambian por E-31;
  - `--replanificar` lo lee y escribe un `orchestration-plan/2.0` con `plan_version` + 1 y la
    historia anterior completa.

  Tal cual está, con `orchestration-plan/1.0`, ese plan **no** valida contra el schema 2.0: la
  aceptación es la regla de lectura de D16, no un enum más flojo. · rojo visto: si
- **E-16b** — Un documento histórico escrito a mano, `orchestration-plan/1.0`, válido contra el schema
  de `4c6f0f3` pero imposible de producir con ese código, **se rechaza**. Se prueba con dos: uno con
  `status: DELEGATING` en el plan, y otro con una unidad `status: READY`. Para cada uno:
  - el schema 2.0 no lo valida;
  - `refute --compile` y `--replanificar` salen con 2, el mensaje nombra el campo y el valor y dice
    que se regenera con `plan --propuesta`;
  - no se migra: ningún código convierte `DELEGATING` ni `READY` en otro estado;
  - **el rechazo no crea, no modifica ni borra ningún artefacto del plan ni derivado de él:**
    - `.claude/planes/<KEY>.json` queda igual, byte a byte: no se reescribe como 2.0, no sube
      `plan_version` y no suma historia;
    - `.claude/refutaciones/<KEY>/` queda igual: ni `units/` ni `verdicts/` cambian, ninguna unidad
      vieja se borra y `run.json` no se escribe;
    - `.claude/refutaciones/cache/` queda igual.

  **Rechazar el plan no es deshacer toda la aplicación.** Antes de leer el plan, los dos comandos
  corren la compuerta normativa (`dev-harness.py:1766-1770, 1783-1786`). Por su propio contrato, la
  compuerta puede escribir tres cosas:
  - `.claude/runtime/knowledge-refresh.json` (`auto_refresh.py:398, 406, 446`);
  - `.claude/harness.fuentes.json` (`auto_refresh.py:438`);
  - originales descargados en `.claude/conocimiento/fuentes/` (`dev-harness.py:986`).

  No dependen del plan y no contradicen este escenario. El rechazo no los deshace.

  Que el documento valida contra el schema de `4c6f0f3` se comprueba con ese schema, sacado con
  `git archive`. · rojo visto: si
- **E-16c** — Un plan guardado con un `meta.schema_version` que no es `orchestration-plan/1.0` ni
  `orchestration-plan/2.0`, o sin ese campo, también lo rechazan `refute --compile` y
  `--replanificar`. Salen con 2 y nombran la versión. El rechazo deja intactos los mismos artefactos
  de E-16b: `.claude/planes/<KEY>.json`, `.claude/refutaciones/<KEY>/` y
  `.claude/refutaciones/cache/`. Los efectos de la compuerta normativa que corrió antes valen igual
  que en E-16b. · rojo visto: si
- **E-17** — Con la misma propuesta y el mismo TaskContext, el código nuevo escribe el mismo
  documento que el de `4c6f0f3`, salvo `meta.generated_at`, `planHistory[].timestamp` y
  `meta.schema_version`, que pasa de `orchestration-plan/1.0` a `orchestration-plan/2.0`.
  · rojo visto: si
- **E-18** — Una propuesta con dos WorkUnits del mismo `id` sale con 2, el error nombra el id, y
  `.claude/planes/<KEY>.json` no se escribe ni se modifica. · rojo visto: si
- **E-18b** — Solo los rechazos que agrega este cambio salen con 2: el id repetido, el dominio fuera
  del plan y la regla de lectura (`PlanRechazado`). Los `PlanInvalido` que ya existían, como un ciclo
  de dependencias, una dependencia rota o una propuesta sin unidades, salen con el mismo código que en
  `4c6f0f3` y tampoco escriben el plan. · rojo visto: si

  📌 **Agregado después de la primera verificación.** El constructor había mapeado todo
  `PlanInvalido` a 2, y eso cambiaba también casos que ya existían sin evitar ningún artefacto: no
  pasaba D15 por sí solo (`verificacion.md`, hallazgo 5).
- **E-19** — Una propuesta con una WorkUnit cuyo `domain` no está en `domains` sale con 2, el error
  nombra el dominio, y `.claude/planes/<KEY>.json` no se crea ni se modifica. Lo que escriba antes
  la compuerta normativa vale como en E-16b. · rojo visto: si

  📌 **Precisión después de la segunda verificación: un dominio desconocido también cae acá.** Una
  WorkUnit con un dominio que HARNESS no conoce (`"inventado"`, `""`) salía con 1 en `4c6f0f3`,
  por el `PlanInvalido` de `contexto_para`. Ahora sale con 2 por esta regla. Se acepta así por tres
  razones:
  - `domains` solo admite dominios conocidos (`plan.py:188-192`), así que un dominio desconocido
    nunca puede estar en ese conjunto;
  - la unidad viola el mismo invariante que este escenario introduce, `domain ∈ plan.domains`;
  - no se busca recuperar el 1 para este subtipo.

  D15 no se amplía en general: el caso queda absorbido por un invariante que este cambio agrega
  explícitamente. Por lo mismo, E-18b no lo cuenta entre los `PlanInvalido` de antes.
- **E-20** — `--replanificar` con una propuesta que viola E-18 o E-19 falla igual y deja el plan
  anterior intacto, byte a byte. · rojo visto: si
- **E-21** — Sobre las combinaciones de huecos de capacidad, aprobaciones y unidades bloqueadas,
  ningún plan generado queda en `READY_FOR_EXECUTION` con un hueco, una aprobación `PENDING` o una
  unidad que no esté en `PENDING`. · rojo visto: si
- **E-22** — `plan.escribir` es lo único en `bin/` que escribe en `.claude/planes/`. `refute --compile`
  y `--replanificar` leen un plan guardado solo a través de la regla de lectura de D16, y fuera de
  esa regla ninguno decide nada por el `status` del plan. · rojo visto: si
- **E-23** — Un agente con su `.md` en disco que no está en el registro da `agentExists: false`. La
  descripción de `agents[].exists` y la de `agentExists` dicen que decide el registro y que el disco
  diagnostica. · rojo visto: si
- **E-24** — `dev-orchestrator.md` dice que los ids de las unidades son únicos, que el dominio de
  cada unidad tiene que estar en `domains`, y que el plan valida contra `orchestration-plan/2.0`.
  · rojo visto: si

### La identidad de la Task

- **E-25** — `dev-harness.py plan` con una clave que no cumple la TaskKey no crea ni modifica nada en
  `.claude/planes/`, aunque exista un contexto con ese nombre puesto a mano. Fija lo que ya vale por
  el patrón de `plan_id`. No es una atomicidad de todo `.claude/`: `plan` no valida la clave antes de
  correr la compuerta normativa (`dev-harness.py:1766-1770`), así que lo que esa compuerta escriba vale
  como en E-16b. Que `plan` sin clave no reviente queda en el pendiente 12 (D15).
  · rojo visto: si
- **E-26** — `contexto`, `refute` y `seguridad`, con una clave que no cumple la TaskKey, salen con 2 y
  no crean ni modifican ningún archivo en `.claude/`. La condición es sobre todo `.claude/` porque la
  clave se rechaza antes de cualquier escritura:
  - `contexto` y `refute` la validan en `main` (`dev-harness.py:1940-1950`), antes de `comando()`
    (`:1962`), que es donde corren la compuerta y el caso de uso;
  - `seguridad` ya valida ahí que la clave no saque la carpeta de `.claude/runtime/security/`
    (`:1952-1959`, "antes de tocar el disco"), y la TaskKey se agrega en ese mismo lugar.

  En `contexto` y `refute` ya vale; en `seguridad` lo agrega este cambio. · rojo visto: si
- **E-27** — Para un conjunto de claves válidas e inválidas, aceptan exactamente las mismas:
  - las dos reglas del código, `CLAVE_JIRA` de `dev-harness.py` y `CLAVE` de `refutacion.py`;
  - el patrón de `meta.task_key` de `task-context`;
  - el de `plan_id` de `orchestration-plan`, sin el prefijo.

  Fija la coherencia que ya existe. Unificar las reglas es el pendiente 12.
  · rojo visto: si
- **E-28** — `contabilidad` acepta una TaskKey o un UUID de sesión, y rechaza cualquier otra clave con
  2, sin escribir. La `statusLine` sigue escribiendo en `runtime/accounting/<session_id>/`.
  · rojo visto: si
- **E-29** — Si Jira devuelve en `key` una clave distinta de la pedida,
  `gaps_and_conflicts.conflicts` registra un conflicto con las dos. `meta.task_key`, `context_id` y
  el nombre del archivo conservan la pedida. · rojo visto: si
- **E-30** — Para una misma TaskKey `K`, de punta a punta con integraciones simuladas:
  - el contexto es `tsk_K` en `.claude/contextos/K.json`;
  - el plan es `pln_K`;
  - cada RefutationUnit lleva `taskKey: K`;
  - el ledger de seguridad está en `runtime/security/K/`.

  · rojo visto: si

### Los checks

- **E-31** — Los `declaredChecks` de toda RefutationUnit compilada son exactamente los ids de
  ControlCheck que declara la norma: los `declaredChecks` del bloque normativo de la regla y los del
  bloque normativo de la unidad. Ninguno es un nombre de `roster.json` `checks`. · rojo visto: si

  📌 **Corregido durante la construcción.** La redacción aprobada decía "ids de controles `CHECK` del
  `control-registry`", y así no se puede cumplir. La matriz de ES0901 declara 34 checks, y 21 no están
  en `control-registry.json`: su propio `_comentario` dice que "NO existen todavía". Esos ids llegan
  por el bloque normativo, no por `requiredChecks`, y ya pasaba en `4c6f0f3`. Son ControlCheck que la
  norma pide y todavía no se instalaron, el hueco `DECLARED_CHECK_NOT_INSTALLED`; no son
  GuardrailCheck. La intención del escenario, que la unidad no declare checks del hook, no cambia
  (D6, I-25).
- **E-32** — Sobre los planes y los `checks.json` de los casos de cierre de
  `55_refutacion_atomica.py`, el código nuevo resuelve las mismas unidades, por el mismo camino y con
  el mismo veredicto que el de `4c6f0f3`. · rojo visto: si
- **E-33** — Con las mismas entradas, la `cacheKey` de cada unidad es igual a la de `4c6f0f3`.
  · rojo visto: si
- **E-34** — Ningún archivo de `comun/` ni de `harnesses/` dice que un check del hook corre en
  PreToolUse. `control-registry.json` y `controles.py` dicen PostToolUse. · rojo visto: si
- **E-35** — Ningún id del `control-registry` coincide con un nombre de check de `roster.json`.
  · rojo visto: si
- **E-36** — La descripción de `normative-signal.schema.json` nombra ES0901 y ES0902.
  · rojo visto: si

### Capability, Tool e Integration

- **E-37** — Toda capability declarada tiene forma `<a>.<b>[.<c>]` en minúsculas, y ninguna es el
  nombre de una HostTool: Read, Write, Edit, MultiEdit, NotebookEdit, Bash, PowerShell, Glob, Grep,
  WebFetch, WebSearch, Skill, Task o Agent. Las capabilities declaradas son las de las clases de
  integración, `roster.json` `capacidadesLocales`, `permisos-por-capacidad.json` y `manifest.json`
  `capacidadesSoportadas`. · rojo visto: si
- **E-38** — Ningún `tools:` de un agente de `harnesses/desarrollo/agents/` o de `comun/agents/`
  nombra una capability. · rojo visto: si
- **E-39** — `integraciones/registro.py` y `docs/integraciones.md` dicen que las capacidades
  soportadas las declaran las clases de integración, y ninguno dice que las declara el manifiesto.
  · rojo visto: si

### El límite de la ejecución y la observabilidad

- **E-40** — En `bin/` y `comun/`, los literales `TASK_STARTED`, `TASK_COMPLETED`, `WORKUNIT_STARTED`,
  `WORKUNIT_COMPLETED`, `AGENT_RUN_STARTED` y `AGENT_RUN_COMPLETED` aparecen solo en `eventos.py`
  (`TIPOS`), en el schema y en la lectura del agregador. Ningún productor los emite.
  · rojo visto: si
- **E-41** — Todo `subprocess` del código de `bin/` y `comun/` lanza `git` o `markitdown`.
  · rojo visto: si
- **E-42** — Ningún módulo de `orquestacion/` importa `contabilidad` ni abre una ruta bajo
  `.claude/runtime/accounting`. · rojo visto: si
- **E-43** — En `execution-accounting-event.schema.json`, el enum de `eventType` sigue con los mismos
  14 valores en el mismo orden, y no hay `$id` nuevo. La descripción dice que no representa estado
  de ejecución, y la de `taskId` dice que es una TaskKey o una sesión del Host. Ingerir la misma
  transcripción de prueba da los mismos `eventId` que con `4c6f0f3`. · rojo visto: si

### Fuente e instalado

- **E-44** — Con el mismo TaskContext y una propuesta sin `normativeEvidence`, el plan que se arma
  desde la fábrica y el que se arma en un proyecto instalado son iguales, salvo dos cosas:
  - `meta.generated_at`, `meta.harness_version` y `planHistory[].timestamp`;
  - los resultados normativos que dependen de `controles/`, que no se instala. Hoy es uno:
    `workUnits[*].normative.standards.ES0902.rules.C3.developmentStandardBaseline`.

  Esa diferencia no se esconde: el test comprueba que es la única que hay y que es la conocida,
  `RESOLVED` en la fábrica y sin resolver en el proyecto instalado. · rojo visto: si

  📌 **Corregido durante la construcción.** La redacción aprobada excluía solo `normativeEvidence`, y
  así no se puede cumplir. `estandar_de_desarrollo.resolver_base` exige que los controles compartidos
  de G1 estén `INSTALLED`, y `controles/` no llega a un proyecto instalado (FH #4, fuera de alcance
  por la sección 13). Con `4c6f0f3` pasa lo mismo: no es una regresión. Es el acople que I-39 ya dejaba
  documentado como lo que no se cumple, y ahora queda nombrado por su ruta.

### Compatibilidad

- **E-45** — En un proyecto instalado con `4c6f0f3`, con un TaskContext, un plan `1.0` y una
  refutación compilada, se corre `-Update` con el instalador nuevo. Después:
  - `refute --compile` funciona sobre el plan viejo sin regenerarlo;
  - `--replanificar` lo reescribe como `orchestration-plan/2.0`, sin perder la historia.

  · rojo visto: si
- **E-46** — Los tres schemas que cambian pasan `controlar_soporte`: no usan palabras clave que el
  validador no conozca. · rojo visto: si
- **E-47** — `docs/orquestacion.md` nombra exactamente los estados de E-13 y E-14, y ninguno de los
  que salen. También nombra `orchestration-plan/2.0` y la regla de lectura de un `1.0`.
  `docs/contabilidad.md` dice que la contabilidad no es estado de ejecución.
  · rojo visto: si
- **E-48** — `PENDIENTES-FH.md` tiene los doce ítems de lo que no se arregla acá: los once de la
  sección 17 y el de lo que sacó la regla de D15. Estos son los títulos:
  1. *The task context hash is not deterministic, and three of its fields say something else*;
  2. *Plan rebuilds lose history, and four plan fields are never read*;
  3. *Six approvals exist and none can be resolved*;
  4. *A source acceptance is a human decision stored in a derived, gitignored file*;
  5. *The plan reports the normative matrix as unbuilt*;
  6. *Accounting names and counts that say something else*;
  7. *Schemas that do not describe what their producers write*;
  8. *Capabilities that skills name and no catalog declares*;
  9. *Who may overwrite a project-owned rule file is read two ways*;
  10. *ADR-0011 says identifiers are English and most are Spanish*;
  11. *ADR-0006 and CLAUDE.md disagree on where SDD applies*;
  12. *The task key rule is written twice, and `plan` crashes without a key*.

  · rojo visto: si
- **E-49** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta

---

## 15. Cómo se verifica

**Todos los escenarios pasan por la suite.** Ninguno lleva `· verificación: lectura`, porque el
sujeto de ninguno es la corrida de un modelo (ADR-0009).

| Escenarios | Cómo |
|---|---|
| E-01 a E-11 y E-47 | `64_modelo_de_dominio.py` parsea el documento por secciones y campos, como `63_harness_unico.py` hace con `docs/instalacion.md`. E-05 cruza contra `comun/schemas/` |
| E-12 | Se lee el frontmatter y las seis decisiones del ADR |
| E-13, E-14, E-22, E-34 a E-42 | Chequeos estáticos sobre schemas, código y documentos |
| E-15, E-21 | Se arman planes sobre las combinaciones y se miran los documentos escritos |
| E-16, E-16b, E-17, E-32, E-33, E-43 | Contra la línea de base: `git archive 4c6f0f3` del código y del schema que hagan falta, como hace `63_harness_unico.py` con `e5d7a14`. Los dos documentos de E-16b se escriben en el test y se validan contra el schema de `4c6f0f3` antes de usarlos. Nada se versiona copiado |
| E-16c, E-18 a E-20, E-23, E-25 a E-31 | Unidades y CLI, con integraciones simuladas como en `19_contexto.py` y `20_orquestacion.py` |
| Las condiciones de "no crea ni modifica" | **E-16b, E-16c, E-18, E-19, E-20 y E-25:** se toman las huellas de los artefactos que el escenario nombra, antes y después, y se comparan byte a byte. Corren con una compuerta normativa que no corta, por ejemplo sin canal, para que el plan llegue a leerse. Los archivos que la compuerta puede escribir no entran en la comparación, y el test los nombra. **E-26:** se toma la huella de todo `.claude/`, porque ahí la clave se rechaza antes de cualquier escritura. **E-28:** `contabilidad` no pasa por la compuerta (`dev-harness.py:1772-1773`), y la ruta del ledger (`:1363`) es el primer paso que toca el disco |
| E-44, E-45 | `64-modelo-de-dominio-instalador.ps1`: instalación en `%TEMP%`, con el instalador de `4c6f0f3` para E-45 |
| E-46 | Se corre `controlar_soporte` sobre los tres schemas |
| E-48 | Se buscan los doce títulos en `PENDIENTES-FH.md` |
| E-49 | La compuerta entera |

**El rojo visto** se busca rompiendo a propósito lo que cada escenario cuida, sobre una copia del repo
en un temporal, como en `harness-unico`. Por ejemplo:

- volver a poner `DELEGATING` en el enum;
- sacar la validación de ids únicos;
- volver a unir `requiredChecks`;
- borrar un concepto del documento o duplicarlo;
- poner `Read` como nombre de una capability.

### Registro del rojo visto

Se hizo el 03-10-2026, después de construir, sobre copias completas del repo con `.git` incluido, en
`%TEMP%`. El árbol versionado no se tocó. Cada mutación apunta a lo que cuida un escenario. Un rojo de
rebote en otro escenario no se usó para atribuir.

| Escenario | Mutación que lo puso en rojo |
|---|---|
| E-01 | `TaskKey` duplicado en el índice y `TaskRecord` borrado |
| E-02 | a `Ficha` le falta `Identidad` |
| E-03 | `ContextSlice` pasa a `Execution` |
| E-04 | `AccountingEvent` pasa a `Domain Event` |
| E-05 | `annex-ii-technology-catalog.schema.json` sale del documento |
| E-06 | se borra "Result ≠ Evidence" |
| E-07 | `**TaskIdentifier**` en el vocabulario |
| E-08 | `### Host` pasa a `### Claude Code` |
| E-09 | se borra "Un ejecutor." |
| E-10 | se saca "sin sustento" |
| E-11 | se borra el enlace del README |
| E-12 | `estado: propuesta` en el ADR |
| E-13 | `DELEGATING` vuelve al enum del plan |
| E-14 | `READY` vuelve al enum de la unidad |
| E-15 | `READY` en el enum, y el productor lo escribe |
| E-16 | `VERSIONES_LEGIBLES` sin la 1.0 |
| E-16b | `aceptar_guardado` acepta cualquier estado |
| E-16c | `aceptar_guardado` acepta cualquier versión |
| E-17 | `VERSION_SCHEMA` y el enum vuelven a 1.0 |
| E-18 | sin el control de ids repetidos |
| E-19 | sin el control de dominio |
| E-20 | sin el control de ids, y en otra copia sin el de dominio |
| E-21 | `estado_de` ignora las aprobaciones `PENDING` |
| E-22 | `_leer_plan` sin `aceptar_guardado` |
| E-23 | `agentExists: True` siempre, y la descripción vuelve a "tiene su .md" |
| E-24 | `dev-orchestrator.md` vuelve a nombrar la 1.0 |
| E-25 | los patrones de `plan_id` y `task_key` se aflojan |
| E-26 | sin el chequeo de clave de `seguridad`; sin los de `contexto` y `refute` en `main`, cada clave inválida deja rastro en `.claude/` |
| E-27 | `refutacion.CLAVE` exige mayúscula inicial |
| E-28 | `validar_clave` acepta todo; y `carpeta_de` validando, que deja sin escribir a la `statusLine` con un `session_id` que no es UUID |
| E-29 | sin el conflicto de claves |
| E-30 | `tsk_`, `pln_` y la `taskKey` de la unidad con un sufijo, y la carpeta del ledger de seguridad con otro |
| E-31 | vuelve la unión con `requiredChecks` |
| E-32 | un check viejo cierra igual (`actual = True`) |
| E-33 | `declaredChecks` entra en la `cacheKey` |
| E-34 | `controles.py` vuelve a decir PreToolUse |
| E-35 | un control `dev-api-rutas` en el registro |
| E-36 | la descripción nombra solo ES0901 |
| E-37 | `Read` en `capacidadesLocales` |
| E-38 | `repository.read` en el `tools:` de un agente |
| E-39 | `registro.py` vuelve a decir que lo declara el manifiesto |
| E-40 | un literal `"TASK_STARTED"` en `contrato.py` |
| E-41 | un `subprocess.run(["python", ...])` en `refutacion.py` |
| E-42 | `from contabilidad import libro` en `controles.py` |
| E-43 | el enum de `eventType` reordenado, y `id_de` hasheando un campo de más |
| E-44 | `modelRouting.runtime.version` dependiendo de dónde corre `plan.py`; y sin el `if faltan:` de `resolver_base`, que borra la diferencia conocida de C3 |
| E-45 | `VERSIONES_LEGIBLES` sin la 1.0, sobre la copia |
| E-46 | `"const"` en `normative-signal` |
| E-47 | `DELEGATING` en la tabla de `docs/orquestacion.md`, y `contabilidad.md` sin la frase |
| E-48 | un título de los doce, acortado |
| E-49 | no consta: es la compuerta misma |

**Después de la primera verificación** (04-10-2026), con el mismo método y por las correcciones S1 a
S5 y el cambio de `PlanInvalido`. Los tres escenarios contradichos ya tenían rojo visto, y estas
mutaciones apuntan a lo que se corrigió:

| Escenario | Mutación que lo puso en rojo |
|---|---|
| E-02 (S5) | se invierten los dos primeros `if` de `plan.estado_de`, y en otra copia vuelve el invariante viejo de ModelTierApproval |
| E-05 (S4) | `database-environment-access-policy` vuelve a NormativeMatrix; y un `from . import bases` en `plan.py` |
| E-06 (S1) | "el plan lo prohíbe" vuelve al apartado; `capacidades.resolver` rechaza un nombre de HostTool; un `pattern` en `requiredCapabilities` |
| E-06 (S2) | un `Copy-Arbol` de `controles` en `install.ps1`; y "ControlCheck se instala" en el apartado |
| E-06 (S3) | "a propósito" vuelve al apartado; y `colisiones_de_id` que nunca reporta |
| E-18b | `main` vuelve a atrapar `PlanInvalido`; y el id repetido levanta `PlanInvalido` en vez de `PlanRechazado` |

**Lo que ninguna suite ve.** Los tests miden la estructura y la cobertura del documento, no si sus
definiciones son ciertas. Que cada definición describa lo que hace el código lo juzga quien
verifica, leyendo el documento contra el código. No es un escenario: un hallazgo ahí va en
`Lo que la verificación encontró` de `verificacion.md`.

---

## 16. Riesgos conocidos

- **El documento puede desviarse del código sin que ningún test lo note.** E-05 cubre los schemas y
  E-01 a E-04 la forma, pero no la verdad de las definiciones. Mitigación: los invariantes que
  importan tienen su escenario sobre el código, no sobre el documento.
- 🔴 **`orchestration-plan` cambia de versión mayor: 1.0 pasa a 2.0.** Es un cambio que rompe el
  contrato:
  - algo fuera del repo que exija `orchestration-plan/1.0` en un plan nuevo deja de encontrarlo;
  - un plan editado a mano con un estado que no existe en 2.0 deja de poder leerse, y hay que
    regenerarlo con `plan --propuesta`;
  - los planes que escribió HARNESS siguen funcionando y se migran al reescribirlos (D16).

  La entrada de `UPGRADE.md` que escribe `close-a-version` tiene que decir las tres cosas. No se
  conoce ningún lector externo.
- **E-19 puede rechazar propuestas que hoy escribe el modelo.** Por ejemplo, una unidad de `tooling`
  o de `refutation` en un plan que no lista ese dominio. Mitigación: `dev-orchestrator.md` lo dice,
  y el error nombra el dominio. Un plan ya guardado no se vuelve a validar entero al leerlo: la regla
  de lectura de D16 mira solo la versión y los estados.
- **Un plan rechazado no deshace lo que la compuerta normativa escribió antes.** Si la compuerta
  refrescó las fuentes, `harness.fuentes.json`, la agenda y las descargas quedan aunque después el
  plan se rechace. Es su contrato y no depende del plan, y el rechazo garantiza solo lo que es del
  plan (E-16b). Este cambio no agrega transacciones ni rollback.
- **La regla de D15 deja afuera defectos reales**, como `plan` sin clave, que revienta. Están en el
  pendiente 12, y la regla es la que impide que este cambio crezca mientras se construye.
- **La TaskKey en `seguridad` y la LedgerKey en `contabilidad` pueden rechazar claves que hoy
  funcionan**, en proyectos o en tests que usen claves que no son de Jira. Lo que se rompa en un test
  se adapta con su motivo. Un proyecto que use otras claves lo va a ver con un error que nombra el
  formato.
- **Sacar los `requiredChecks` de la refutación.** Si algo leía las unidades para saber qué checks
  del hook tenía un dominio, deja de verlo. No se encontró ningún lector.
- **Toca archivos instalados:** tres schemas, `plan.py`, `refutacion.py`, `tarea.py` o
  `ensamblador.py`, `libro.py`, `dev-harness.py`, `controles.py`, `registro.py`,
  `control-registry.json` y `dev-orchestrator.md`. En el `-Update`, lo editado a mano queda como
  `.nuevo`. **La caché de refutación no se invalida**, porque `dev-refutador.md` y las `SKILL.md` no
  se tocan y la `cacheKey` no incluye el plan.
- **El vocabulario canónico en inglés convive con módulos en español.** Quien lee necesita el mapa,
  y ese es el costo de D9.
- **La evidencia salió de seis relevamientos.** Los hechos que sostienen decisiones se verificaron a
  mano (sección 2), pero un número de línea mal citado en las secciones 3 y 17 es posible. Las
  rutas se refieren a `4c6f0f3`.
- **Doce ítems nuevos de pendientes** pueden normalizar la deuda en lugar de pagarla. Mitigación:
  cada uno nombra su contradicción por número.
- **El catálogo tiene 69 conceptos (68 en el relevamiento y uno que agregó la primera verificación),
  y son muchos para leer.** Mitigación: el documento separa
  los centrales y marca los dormidos, y ninguno se agregó por la lista de DDD: cada uno tiene su
  contrato o su evidencia. El número no es un contrato (E-01).

---

## 17. Contradicciones encontradas

Están numeradas para que los pendientes y la verificación las citen. **Se arregla** quiere decir que
este cambio la arregla, con el escenario que lo prueba. Lo demás va a `PENDIENTES-FH.md`, bajo el
título de E-48 que se indica.

| # | Contradicción | Evidencia | Destino |
|---|---|---|---|
| C-01 | El plan declara 11 estados, y el código escribe 3, más `PLANNING` de forma transitoria | `orchestration-plan.schema.json:372-374`; `plan.py:249-251, 371-379` | **Se arregla** en el contrato 2.0, con regla de lectura (E-13, E-15, E-16b; D16). El marcador interno queda, porque no llega a ningún documento (D15) |
| C-02 | El `READY` de la unidad no lo escribe nadie | schema `:261-264`; `plan.py:273-279` | **Se arregla** en el contrato 2.0 (E-14, E-16b) |
| C-03 | `humanApprovals`: se escribe solo `PENDING` y no hay comando para resolverla | `consumo.py:82`; `dev-harness.py:1836-1838` | 3 |
| C-04 | El schema dice que la existencia de un agente "lo decide el disco"; el código, que el registro | schema `:62, 150`; `roster.py:90-105` | **Se arregla** (E-23) |
| C-05 | Los ids de unidad repetidos colapsan en silencio | `plan.py:97` | **Se arregla** (E-18) |
| C-06 | `dominios_del_plan` no se usa | `plan.py:256` | **Se arregla** (E-19) |
| C-07 | Volver a correr `--propuesta` resetea `plan_version` y la historia | `dev-harness.py:1231-1244` | 2 |
| C-08 | El schema dice que el plan es "regenerable", y regenerarlo pierde la historia | schema `:5` | 2 |
| C-09 | La refutación une los checks del hook a `declaredChecks` | `refutacion.py:621-623` | **Se arregla** (E-31) |
| C-09b | `policies` y `applicablePolicies` son textos libres que nadie valida ni consume | `plan.py:231, 304` | 2 |
| C-10 | El registro y los controles dicen que los checks del hook corren en PreToolUse | `control-registry.json:13`; `controles.py:10-12` | **Se arregla** (E-34) |
| C-11 | `normative-signal` se declara solo de ES0901 | schema `:4`; `senales.py:102-118` | **Se arregla** (E-36) |
| C-12 | "Los emite quien orquesta la ejecución", y los emiten la `statusLine` y el CLI | `execution-accounting-event.schema.json:19` | **Se arregla** (E-43) |
| C-13 | `taskId` es "la tarea", y en la barra es el `session_id` | schema `:41`; `statusline.py:190` | **Se arregla** (E-28, E-43) |
| C-14 | `SESSION_COMPLETED` sale varias veces por sesión; `SESSION_STARTED`, nunca | `contrato.py:222-227`; `claude_code.py:269-315` | 6 |
| C-15 | "Reingerir no duplica" es falso para `USAGE_UNRESOLVED` sin dedupKey | `docs/contabilidad.md:32-33`; `eventos.py:305` | 6 |
| C-16 | "Siete claves" son 11; "nueve productores" son 10; "trece tipos" son 14 | `eventos.py:78-95`; `reporte_seguridad/libro.py:49-53` | 6 |
| C-17 | El hash del TaskContext incluye `retrieved_at`, así que no es determinista, aunque el schema y la spec anterior lo afirmen | `contexto/comun.py:49`; `contexto-armar.py:980-982`; `task-context.schema.json:25` | 1 |
| C-17b | Sin el catálogo de secretos, el contexto no se redacta y nada lo avisa | `limpieza.py:88-89`; `ensamblador.py:107-110` | 1 |
| C-18 | `local_path` es absoluta y el schema dice relativa; `origin` vale `tarea`/`ficha` y el schema dice "la clave"; dos adjuntos con el mismo nombre se pisan | schema `:168, 177`; `documentos.py:90, 131` | 1 |
| C-19 | `CLAVE_JIRA` acepta minúsculas, la sonda de Jira solo mayúsculas, y nadie compara `task.key` con `meta.task_key` | `dev-harness.py:92`; `jira.py:30`; `tarea.py:69` | La comparación **se arregla** (E-29); las mayúsculas, 1 |
| C-20 | `plan`, `seguridad` y `contabilidad` no validan la clave, y `plan` sin clave revienta | `dev-harness.py:1197-1198`; `libro.py:37-45` | `seguridad` y `contabilidad` **se arreglan** (E-26, E-28). `plan` no puede escribir con una clave inválida (E-25); su validación y que no reviente sin clave van al pendiente 12 (D15) |
| C-55 | La regla de la TaskKey está escrita dos veces, idéntica | `dev-harness.py:92`; `refutacion.py:57` | 12. E-27 fija que acepten lo mismo |
| C-21 | `applicableStandards` siempre vacío, y el aviso de que la matriz "todavía no se construyó" | `normativa.py:53-79`; `es0901-7.1.json` | 5 |
| C-22 | `roster.cargar()` devuelve `{}` sin avisar, aunque su docstring dice que el plan lo declara | `roster.py:53-66`; `plan.py:196-208` | 2 |
| C-23 | `dev-orchestrator.md` dice `model: sonnet` contra "perfiles, nunca nombres de modelo" | `dev-orchestrator.md:5`; `modelo.py:3-5` | 2 |
| C-24 | Los estados del `agentResult` de los agentes no son los de las skills, y ninguno tiene schema | `dev-backend.md:101-114`; `SKILL.md:459-534` | La Task 3 (10.1) |
| C-25 | Las skills nombran capacidades que ningún catálogo declara, y nada liga el `tools:` con las capacidades | `dev-backend-implementation/SKILL.md:542-559`; `dev-architecture-analysis/SKILL.md:445` | 8 |
| C-26 | `tool-registry` dice que el Capability Registry lo consulta, y no lo consulta | `tool-registry.schema.json:5`; `capacidades.py:22-26` | 8 |
| C-27 | La salida de `dev-tool-builder` no es el `tool-contract` | `dev-tool-builder.md:191-209`; `tool-contract.schema.json` | 8 |
| C-28 | Lo soportado, según el texto, sale del manifiesto; según el código, de las clases | `integraciones/registro.py:12`; `docs/integraciones.md:142`; `dev-harness.py:227-229` | **Se arregla** (E-39) |
| C-29 | El estado de la instalación se valida contra una copia en línea a la que le falta `integrationConfiguration`, y `knowledgeRefresh` no está en el schema | `bienvenida.py:366-378, 1298` | 7 |
| C-30 | `knowledge-refresh-state` declara RUNNING, DUE y ERROR, que nadie escribe; la bienvenida emite `UNREADABLE`, que no está en el enum | `auto_refresh.py:266, 292`; `bienvenida.py:801` | 7 |
| C-31 | `harness.fuentes.json` "se deriva y no se escribe a mano", pero guarda las decisiones humanas y está gitignoreado | `source-state.schema.json:5, 217-276`; `install.ps1:1976` | 4 |
| C-32 | La bienvenida invita a "posponer" y `fuentes` no tiene cómo | `bienvenida.py:1811`; `dev-harness.py:1885-1900` | 4 |
| C-33 | Según `registro_fuentes.py`, `normativa/` no se instala, y el instalador la copia | `registro_fuentes.py:134-136`; `install.ps1:1831-1834` | 7 |
| C-34 | La refutación fija `docs/codebase/project-context.json` y no respeta `rutaCodebase` | `refutacion.py:389` | 7 |
| C-35 | `normative-review` dice que el validador no soporta `type` como lista, y lo soporta | schema `:212`; `contexto-armar.py:758-770` | 7 |
| C-36 | El plan, el resumen de seguridad y el hallazgo de integridad escriben campos que su schema no declara | `normativa.py:116-166`; `resumen.py:590-610`; `integridad.py:540-554` | 7 |
| C-37 | `COMPLIANT_WITH_OBSERVATIONS` se vuelve `UNRESOLVED` en el resumen | `resumen.py:58-64, 276` | 7 |
| C-38 | `NO_SUSPICIOUS_CHANGE_FOUND` aparece en el resumen con otro nombre | `integridad.py:71`; `resumen.py:105-107` | 7 |
| C-39 | Los `.md` de governance de Vu3 a Vu7 no tienen los mismos `primaryAgents` que la matriz | `es0902-vu3-governance.md:27-29` | 7 |
| C-40 | Conteos viejos: "36 policies y 34 checks", "16 condicionales", "31 controles" | `matriz.py:20-21, 276`; `senales.py:4-5`; `docs/normativa-7.1.md:41` | 7 |
| C-41 | ADR-0006 hace del SDD el método de los proyectos instalados y no de este repo; `CLAUDE.md` lo hace método de la fábrica; el producto no instala nada de SDD | `docs/adr/0006…md:43, 86-87, 100-103` | 11 |
| C-42 | `dev-refutador.md` cita un archivo retirado | `dev-refutador.md:8` | ya anotado |
| C-43 | ADR-0011 pide identificadores y nombres de archivo en inglés, y el CLI, los módulos, el estado y 60 de 61 carpetas de `docs/cambios/` están en español | ADR-0011 `:54`; `dev-harness.py:1836-1900` | 10 |
| C-44 | El `$id` no coincide con el nombre del archivo: `sources-state` y `source-state`, `harness-installation` y `harness-installation-state`, y la matriz de ES0902 | `source-state.schema.json:3` | 7 |
| C-45 | `docs/versiones/0.17.0.md` dice "Nada consume el TaskContext" | `:113` | Historia: no se reescribe |
| C-46 | Para `PENDIENTES-FH.md`, el `-Update` pisa en silencio un `reglas/*.json` llenado por el proyecto; el instalador deja `.nuevo`, y otra lectura ve un `Copy-Item -Force` | `PENDIENTES-FH.md:1264-1287`; `install.ps1:339, 2112-2229` | 9 |
| C-47 | Inventarios del proyecto, como `security-approval-evidence.json`, viven en `reglas/`, que es la carpeta de la fábrica | `docs/seguridad-es0902.md:189` | 9 |
| C-48 | `_con_desarrollo` usa `knowledge.applies` como si significara "desarrollo instalado": es un resto de la composición | `bienvenida.py:1532-1533` | 7 |
| C-49 | El presupuesto premium se gasta al planificar y se resetea en cada regeneración | `plan.py:177`; `consumo.py:55-84` | 2 |
| C-50 | Los eventos de seguridad hashean su propio timestamp, así que no son idempotentes | `productores.py:110-131` | 6 |
| C-51 | Una transcripción que se ingiere por CLI y por la barra queda en dos ledgers | `dev-harness.py:1855`; `statusline.py:190` | 6 |
| C-52 | `docs/seguridad-es0902.md` y `docs/reporte-de-seguridad.md` describen controles y productores que ya existen como si no existieran | `docs/seguridad-es0902.md:7-9`; `docs/reporte-de-seguridad.md:34-36` | 7 |
| C-53 | El `pdfOutput` de `security-report` apunta al HTML | `reporte.py:34-39` | 7 |
| C-54 | El ítem de pendientes sobre los tipos de contabilidad dice "trece tipos" y "solo dos emitidos": son 14 y 3 | `PENDIENTES-FH.md:545-550` | 6 |
