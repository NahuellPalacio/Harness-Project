# Contrato de ejecución: la frontera estable entre Planning y cualquier implementación que ejecute WorkUnits

**Estado:** reverificado sobre 0.31.0 y publicado en 0.32.0 · **Fecha:** 07-10-2026, especificada,
revisada y construida el mismo día; integrada con 0.31.0 el 08-10-2026 · **Versión de partida:**
0.30.0 (`f9393cf`) · **Base actual:** 0.31.0 (`fdca5ce`)

📌 **0.31.0.** Las secciones 1 a 36 se escribieron sobre 0.30.0 y quedan como historia. La sección
37, «Integración con HARNESS 0.31.0», alinea el contrato con Flow Governance y
`orchestration-plan/2.1`: donde dice distinto que una anterior, manda la 37.

Las rutas con número de línea se refieren a `0f8b725`, que es `f9393cf` más dos commits que tocan
solo `README.md`, `docs/instalacion.md` y `terceros/LEEME.md`: el código es el mismo. Las rutas sin
prefijo son relativas a la raíz del repo. Abreviaturas:

- `bin/` es `harnesses/desarrollo/bin/` y `reglas/` es `harnesses/desarrollo/reglas/`;
- **MC** es `docs/dominio/modelo-canonico.md`;
- **FH** es `Pendientes/Fix-Harness/PENDIENTES-FH.md`;
- **la spec de Task 2** es `docs/cambios/canonical-domain-model/spec.md`, y sus contradicciones se
  citan `C-nn`.

📌 **Los ids.** Los escenarios son `EX-Enn`, los invariantes `EX-Inn`, las contradicciones `EC-nn`
y las decisiones `Dnn`. El prefijo `EX-` lo pidió la Task: para el método de `CLAUDE.md`, un `EX-Enn`
es un `E-nn` con todas sus reglas, `rojo visto` incluido.

📌 **Por qué la carpeta se llama `execution-contract`.** Es el nombre del pedido, y cumple
[ADR-0011](../../adr/0011-el-idioma-de-un-archivo-lo-decide-quien-lo-lee.md). La práctica de
`docs/cambios/` es otra (C-43), y no se resuelve acá.

---

## 1. Estado

| | |
|---|---|
| Especificado | Sí. Este documento, revisado una vez antes de construir |
| Construido | Sí, según la sección 34. El detalle está en [informe-de-construccion.md](informe-de-construccion.md) |
| Verificado | Sobre 0.30.0, sí: 57 sostenidos. Sobre 0.31.0, reverificado el 08-10-2026: 70 sostenidos, los 57 de la sección 30 y los 13 EX-Gnn de la 37. Los dos veredictos están en [verificacion.md](verificacion.md) |
| Integrado con 0.31.0 | Sí, según la sección 37, el 08-10-2026 |
| Lo que tocó la especificación | Solo este archivo |
| Lo que sigue | El cierre de versión, que no es parte de este cambio |

## 2. Qué problema resuelve

Task 2 dejó Execution como un **límite reservado**: nombrado, vacío, sin lenguaje ni datos
(MC:1307-1310; ADR-0013 §4). Dejó también tres preguntas para esta Task (MC:1532-1537):

1. dónde vive el estado de una ejecución;
2. qué forma tiene lo que vuelve de un agente;
3. si el contrato de salida es el `agentResult` de los agentes, los "Result Statuses" de las
   skills, o ninguno de los dos.

Hoy, sin un contrato, la Task que construya el primer motor tendría que decidir todo adentro del
código, y el repo ya tiene las piezas que la empujarían a decidir mal:

- **`READY_FOR_EXECUTION` no quiere decir "se puede ejecutar".** Un plan llega a ese estado con
  una unidad cuyo agente no existe (`bin/orquestacion/plan.py:320-326, 418-426`). Lo marca FH:1661,
  y dice que es una decisión que necesita su propia spec (FH:1667-1668).
- **`(plan_id, plan_version)` no identifica un plan.** `plan --propuesta` pisa el archivo y vuelve
  a la versión 1 (`plan.py:260-261`; `bin/dev-harness.py:1235-1244`). Dos planes distintos de la
  misma Task tienen el mismo par.
- **Lo que devuelve un agente no tiene contrato.** Ocho agentes declaran en prosa un `agentResult`
  con cuatro estados, siete skills declaran siete conjuntos distintos, y nadie lee ninguno (C-24).
- **El vocabulario de ejecución existe sin ejecución.** Once tipos de evento contable no los emite
  nadie (`bin/contabilidad/eventos.py:27-42`). El ledger de seguridad reserva un `executionId` que
  siempre es nulo (`bin/reporte_seguridad/productores.py:117`). Y la refutación espera un
  `scope.json` que "escribe quien ejecutó" (`comun/schemas/refutation-unit.schema.json:100`), y no
  lo escribe nadie.
- **Los dos atajos que rompen el modelo están a mano.** Uno es agregar un estado de ejecución al
  Plan, que rompe I-15 y ADR-0013 §4. El otro es leer el ledger de contabilidad para saber qué
  corrió, que rompe I-33.

Este cambio decide el contrato y lo escribe en cuatro formas: dos schemas, un validador puro, el
modelo canónico y un ADR. No ejecuta nada.

## 3. Baseline

| Qué se verificó | Resultado |
|---|---|
| `HEAD` | `0f8b725`, descendiente de `f9393cf`. `git diff f9393cf HEAD` toca solo `README.md`, `docs/instalacion.md` y `terceros/LEEME.md` |
| `VERSION` | `0.30.0` |
| Árbol | Limpio |
| `docs/dominio/modelo-canonico.md` | Existe |
| `docs/adr/0013-modelo-de-dominio-canonico.md` | Existe, `estado: aceptada` |
| `docs/cambios/canonical-domain-model/verificacion.md` | Existe |
| Execution, límite reservado | Sí. MC:1307-1310 lo dice, ADR-0013 §4 lo decide, y `tests/casos/64_modelo_de_dominio.py:533-567` (E-03) lo hace cumplir: ningún concepto tiene Execution como contexto |
| Execution, sin implementar | Sí. Ningún subcomando ejecuta (`dev-harness.py:1843-1845`), y todo `subprocess` lanza `git` o `markitdown` (E-41) |
| La compuerta | No se corrió en este paso, porque no cambió nada ejecutable. La corre la construcción |

## 4. Discovery AS-IS

### 4.1 Cómo se hizo

Hubo tres relevamientos de solo lectura, siguiendo productores y consumidores y no nombres de
carpeta:

1. el código y los schemas de orquestación, contabilidad, contexto e integraciones;
2. los hooks, la sesión del Host, governance, guardrails y contabilidad;
3. los agentes, las skills, el registro, los pendientes, la historia y los tests.

Después se verificaron a mano los hechos que sostienen decisiones:

- `plan.estado_de` y el estado de la unidad (`plan.py:320-326, 418-426`);
- que `plan --propuesta` vuelve a `plan_version: 1` (`dev-harness.py:1235-1244`);
- `refutacion.huella` y el `planFingerprint` de `run.json` (`bin/orquestacion/refutacion.py:147-150,
  830`);
- las claves cerradas de `metadata` (`eventos.py:78-90`);
- el `executionId` nulo (`productores.py:117`);
- el `scope.json` (`refutation-unit.schema.json:98-125`);
- los `agentResult` de los ocho agentes y los "Result Statuses" de las skills;
- las palabras que interpreta el validador (`comun/bin/contexto-armar.py:736-737`);
- que el instalador copia `bin/` y `comun/schemas/` enteros (`install.ps1:1826, 1828, 1841`);
- que `.claude/` está gitignoreado entero (`install.ps1:1975-1977`);
- que no hay `threading`, `asyncio`, `multiprocessing` ni SDK de modelos en `bin/` ni `comun/`.

### 4.2 Los términos buscados, y qué significan donde aparecen

| Término | Dónde | Qué significa ahí | Clase |
|---|---|---|---|
| execute / execution / ejecutar / ejecución | `execution-accounting-event`, `execution-summary/1.0`, `execution-cost.md`, "contabilidad de ejecución" (`dev-harness.py:1458`) | El consumo de modelo de una sesión | observability/accounting behavior |
| | `READY_FOR_EXECUTION`, `executionOrder` | Un estado del documento y un orden topológico | planning behavior |
| | `estandar_de_desarrollo.ejecutar` (`bin/orquestacion/estandar_de_desarrollo.py:295`) | Evaluar controles de G1 al planificar | governance behavior |
| | `executionId` del ledger de seguridad | Un hueco para un ejecutor que no existe | reserved vocabulary |
| | `executionEvidence` (`refutation-unit.schema.json:63, 121`), `EXECUTION_REQUIRED` (`refutation-verdict.schema.json:19`) | Lo que la refutación espera recibir de quien ejecutó | future/intended concept |
| | "orquestar decide; ejecutar modifica" (`docs/orquestacion.md:14-16`; `docs/versiones/0.18.0.md:10-13`) | Un bloque que nunca se construyó | future/intended concept |
| run / runner | `refutation-run/1.0` | El agregado compilado de la refutación, sin fechas ni intentos | historical vocabulary |
| | `counts.semanticRuns` | Cuántas unidades resolvió `dev-refutador` | governance behavior |
| | `run-hook.cmd` / `run-hook.sh` | El lanzador de los hooks | host behavior |
| | `RUNNING` de `knowledge-refresh-state` | Una revisión de fuentes, que nadie escribe (C-30) | dead/dormant code |
| dispatch / launch | — | Sin uso de dominio | — |
| delegate / delegation | `DELEGATING`, `READY_FOR_DELEGATION` | Estados que el plan 2.0 sacó | historical vocabulary |
| | "Delegate backend concerns to the narrowest installed Skill" (`agents/dev-backend.md:29`) | Un agente que pasa trabajo a sus skills | host behavior |
| agent | `agent-registry/1.0`, `agents/*.md` | Un rol declarado, que el Host corre desde su `.md` | actual behavior |
| tool | `tools:` de los agentes; `tool-contract`, `tool-registry` | HostTool; HarnessTool dormida | host behavior; dead/dormant code |
| capability | `capacidades.py`, `roster.json`, las clases de integración | Una habilidad con nombre | actual behavior |
| workUnit / `READY_FOR_EXECUTION` / `PENDING` / `BLOCKED` | `orchestration-plan/2.0` | Estados del documento | planning behavior |
| result / output | `agentResult`, "Result Statuses", `result` de controles y ledger | Una declaración en prosa; un EvaluationResult | future/intended concept; governance behavior |
| evidence | `evidence[]`, inventarios, `evidenceFingerprint` | Evidence de governance | governance behavior |
| verdict | `cumple`/`incumple`/`sin-verificar`; veredictos SDD | RefutationVerdict; método de la fábrica | governance behavior |
| status | plan, unidad, aprobación, registro, refutación, ledger | Cada uno con su enum | — |
| event | `eventType` de contabilidad y de seguridad | Constancias, no Domain Events | observability/accounting behavior |
| accounting | `bin/contabilidad/` | Observability | observability/accounting behavior |
| approval | `humanApprovals[]` y cinco sentidos más (MC:1475) | ModelTierApproval y otras | planning behavior |
| retry / attempt | `maxRetries`, `retryPolicy`, `modelo.escalar`, `lastAttemptAt` | Campos sin lector; el ciclo de la revisión de fuentes | dead/dormant code |
| timeout | `timeoutIntegraciones`, `timeoutSeconds` del `tool-contract` | El HTTP a Jira y GitLab; dormido | actual behavior; dead/dormant code |
| cancel | `KeyboardInterrupt` → "cancelado", sale con 2 (`dev-harness.py:1986-1988`); `CANCELLED` de la aprobación | Cortar un comando; un estado que nadie escribe | host behavior; dead/dormant code |
| failure / success | `SUCCEEDED_WITH_UPDATES` de la revisión de fuentes; `FAILED` del `agentResult` | Normative Sources; prosa | actual behavior; future/intended concept |
| checkpoint / resume | SessionStart `startup\|resume\|clear` (`comun/settings/hooks.plantilla.json:15`) | Reanudar una sesión del Host | host behavior |

### 4.3 Lo que hay, clasificado

| Hallazgo | Evidencia | Clase |
|---|---|---|
| El plan es un documento. `READY_FOR_EXECUTION` es un valor que nada lee para arrancar nada | `plan.py:9-12, 36, 426`; `bin/orquestacion/__init__.py:9` | planning behavior |
| `PENDING` = tier aprobado y ninguna capacidad faltante al armar | `plan.py:320-326` | planning behavior |
| `executionOrder` es un orden topológico, no un cronograma, y no declara paralelismo | `plan.py:102-131`; `orchestration-plan.schema.json:270-273` | planning behavior |
| La refutación: HARNESS entrega una unidad, la sesión del Host corre `dev-refutador`, HARNESS valida de todo o nada | `dev-harness.py:1630-1645`; `refutacion.py:1157-1187` | governance behavior |
| La refutación ya identifica una WorkUnit por `(taskKey, planId, planVersion, workUnitId)`, y el plan por `planFingerprint` | `refutation-unit.schema.json:7-19`; `refutacion.py:830` | governance behavior |
| Los únicos `subprocess` lanzan `git` o `markitdown` | `comun/hooks/session-start.py:52-58`; `comun/bin/contexto-armar.py:151-161`; `bin/contexto/documentos.py:45-56, 152`; `refutacion.py:376-384` | actual behavior |
| No hay `threading`, `asyncio`, `multiprocessing`, cola ni SDK de modelos | búsqueda de imports en `harnesses/` y `comun/` | actual behavior |
| El CLI tiene once subcomandos y ninguno ejecuta | `dev-harness.py:1843-1845` | actual behavior |
| Los hooks atan cuatro eventos del Host; ninguno es Stop ni SubagentStop | `comun/settings/hooks.plantilla.json:13-43` | host behavior |
| Solo los secretos bloquean, en PreToolUse; los GuardrailCheck avisan en PostToolUse y corren todos los instalados en cada llamada | `comun/hooks/pre-tool-use.py:15-28`; `comun/hooks/lib/reglas.py:16, 43-69` | actual behavior (Guardrails) |
| El `session_id` del Host es la LedgerKey de la barra | `bin/contabilidad/statusline.py:190, 211` | host behavior |
| La contabilidad produce 3 de 14 tipos, y reconstruye desde la transcripción | `eventos.py:27-42`; `bin/contabilidad/adaptadores/contrato.py:222-227` | observability/accounting behavior |
| `TASK_*`, `WORKUNIT_*`, `AGENT_RUN_*` existen y nadie los emite; E-40 lo fija | `eventos.py:27-38`; `64_modelo_de_dominio.py:2362-2380` | reserved vocabulary |
| Las claves de `metadata` son una lista cerrada, sin `executionId` ni plan | `eventos.py:78-90` | observability/accounting behavior |
| `executionId` del ledger de seguridad, siempre nulo | `comun/schemas/security-ledger-event.schema.json:45-50`; `productores.py:117`; `docs/cambios/reporte-de-seguridad/spec.md:51-52` | reserved vocabulary |
| `scope.json` y `checks.json` "los escribe quien ejecutó"; hoy se escriben a mano | `refutation-unit.schema.json:100, 127`; `UPGRADE.md:203` | future/intended concept |
| `agentResult` con `COMPLETE \| PARTIAL \| BLOCKED \| FAILED`, en prosa, en los ocho agentes que no son ni el orquestador ni el refutador | `agents/dev-backend.md:101-114` y los otros siete | future/intended concept |
| "Result Statuses" en 7 de 27 skills, con 7 conjuntos distintos de 9 a 18 valores; 20 skills no tienen | `skills/dev-backend-implementation/SKILL.md:520-532` | future/intended concept |
| `maxRetries`, `allowEscalation`, `modelo.escalar`, `retryPolicy` y `timeoutSeconds` sin lector | `bin/orquestacion/consumo.py:23`; `plan.py:363`; `bin/orquestacion/modelo.py:91-106`; `comun/schemas/tool-contract.schema.json:63-81` | dead/dormant code |
| `tools.py` y `registro_tools.py` solo los importan los tests | MC:676-689 | dead/dormant code |
| La ModelTierApproval se escribe solo `PENDING` y ningún comando la resuelve | `consumo.py:74-83` | planning behavior |
| La revisión automática de fuentes es el único ciclo de intentos que persiste | `bin/orquestacion/auto_refresh.py:269-305` | actual behavior (Normative Sources) |
| El HTTP a Jira y GitLab tiene timeout y no reintenta | `bin/integraciones/http.py:27`; `bin/integraciones/fuentes.py:118` | actual behavior |
| "Bloque 4: ejecución" se planeó, y el Bloque 4 que se construyó es contabilidad | `docs/versiones/0.18.0.md:111`; `docs/cambios/bloque-4-contabilidad-de-ejecucion/spec.md:43-47` | historical vocabulary |
| Un agente existe si el registro lo declara y lo deja rutear; el disco diagnostica | `bin/orquestacion/roster.py:90-105`; `bin/orquestacion/registro_agentes.py:45` | actual behavior (Catalog) |
| Los `dev-*` llegan a `.claude/agents/` solo en un proyecto instalado | `install.ps1:1843-1844` | host behavior |
| El `tools:` de un agente nombra HostTools; nada lo liga con las capabilities | `agents/dev-backend.md:4`; MC:1386-1390 | host behavior |
| Las capabilities disponibles son las integraciones `ENABLED` más las locales del roster, que nadie verifica | `bin/orquestacion/capacidades.py:22-26`; `plan.py:252-255` | actual behavior (Catalog) |

### 4.4 En resumen

**Qué existe hoy cerca de la ejecución:**

- un plan con estado de documento;
- unidades con agente, capacidades, dependencias y contexto recortado;
- un registro que decide qué agente existe;
- un precedente de entrega y registro, que es la refutación;
- huellas canónicas;
- una contabilidad que observa la sesión.

**Qué solo parece ejecución:**

- `READY_FOR_EXECUTION`, `executionOrder` y `execution-accounting-event`;
- los `*_STARTED` sin productor;
- el `run` de la refutación;
- el `RUNNING` de las fuentes;
- `maxRetries` y `retryPolicy`;
- el `agentResult` en prosa.

**Qué falta:** una identidad de ejecución, una regla que diga qué entra, un ciclo de vida, un
resultado con forma, un modelo de errores, un lugar para el estado, y la línea que separa lo que
observa el ejecutor de lo que declara el agente.

## 5. Inventario de contratos

Todo lo que se puede confundir con un contrato de ejecución. **Representa** dice si es intención,
ejecución, resultado, evidencia o accounting.

| Contrato | Ruta / versión | Productor | Consumidor | Persistencia | Identidad | Estados | Representa | Activo |
|---|---|---|---|---|---|---|---|---|
| Plan y WorkUnit | `orchestration-plan/2.0` | `plan` (`plan.py:181-300, 439-449`) | `refute --compile`, `--replanificar` | `.claude/planes/<KEY>.json`, se pisa | `pln_<KEY>` más `plan_version`; la unidad, por `(plan, id)` | 3 del plan, 3 de la unidad | intención | sí |
| PlanProposal | sin schema | `dev-orchestrator`, un modelo | `plan.armar` | un archivo del llamador | — | — | intención | sí |
| ModelTierApproval | `humanApprovals[]` del plan; un dict de `consumo.decidir` | `consumo.py:74-83` | la persona que lee la salida de `plan` | adentro del plan | `(plan, workUnit)` | 4 declarados, 1 escrito | intención (costo) | a medias |
| Respuesta de ruteo | dict en memoria | `registro_agentes.resolver_ruteo` (`:370-392`) | tests | no persiste | `requestedAgent` | `routable` más el motivo | catálogo | en memoria |
| Capacidades validadas | `integraciones/1.0`, sin schema | la validación del entorno (`correr_bootstrap`) | `plan` | `.claude/harness.capacidades.json` | la capability | `ENABLED`, `DISABLED` | catálogo | sí |
| `agentResult` | prosa en ocho agentes | el modelo, si lo escribe | nadie | no persiste | `agent` | `COMPLETE \| PARTIAL \| BLOCKED \| FAILED` | resultado declarado | dormido |
| "Result Statuses" | prosa en 7 skills | el modelo, si lo escribe | nadie | no persiste | — | 7 conjuntos, de 9 a 18 valores | resultado declarado | dormido |
| RefutationUnit | `refutation-unit/1.0` | `refute --compile` | `--unit` (el Host corre `dev-refutador`), `--record` | `.claude/refutaciones/<KEY>/units/` | `REF-nnn` más `(taskKey, planId, planVersion, workUnitId)` | `PENDING_SEMANTIC`, `RESOLVED`, `BLOCKED` | intención de verificar | sí |
| `scope.json` | `refutation-scope/1.0`, en `$defs` | "quien ejecutó": nadie en código, se escribe a mano | `refutacion.py:554-566` | `.claude/refutaciones/<KEY>/scope.json` | por `workUnitId` | `source` incluye `executionEvidence` | evidencia de ejecución esperada | se consume, nunca se produce |
| `checks.json` | `refutation-checks/1.0`, en `$defs` | nadie en código | la refutación | `.claude/refutaciones/<KEY>/checks.json` | — | resultados de ControlCheck | evidencia de governance | se consume, nunca se produce |
| RefutationVerdict | `refutation-verdict/1.0` | `dev-refutador` más los campos del harness | `seguridad --refutacion` | `verdicts/` y `cache/` | `refutationUnitId` más `cacheKey` | `cumple`, `incumple`, `sin-verificar`; motivo `EXECUTION_REQUIRED` | resultado de governance | sí |
| Refutation | `refutation-run/1.0` | `refutacion.corrida` | `--status`, `--summary` | `run.json` | `taskKey`, `planId`, `planVersion`, `planFingerprint` | `PASS`, `FAIL`, `INCOMPLETE`, `NOTHING_TO_VERIFY` | agregado, sin fechas ni intentos | sí |
| AccountingEvent | `execution-accounting-event`, sin `$id` | `statusline.py`, `contabilidad --ingerir` | el agregador y la barra | `ledger.jsonl`, append-only | `ev_` más sha256; `taskId` es la LedgerKey | 14 tipos, 3 producidos | accounting | 3 de 14 |
| AccountingSummary | `execution-summary/1.0`, sin schema | `agregacion.resumir` | el reporte | `summary.json` | la LedgerKey | — | accounting | sí |
| EvaluationRecord | `security-ledger-event/1.0` | `reporte_seguridad/productores.py` (2 de 10 con CLI) | el resumen de seguridad | `security-ledger.ndjson` | `sev-…`; `executionId` siempre nulo | 12 tipos | evidencia y resultado de governance | en parte |
| RefreshAgenda | `knowledge-refresh-state/1.0` | `auto_refresh.registrar` | la compuerta normativa | `.claude/runtime/knowledge-refresh.json` | el proyecto | 7 declarados, 3 escritos | una revisión de fuentes, no trabajo | sí |
| HarnessTool | `tool-contract/1.0`, `tool-registry/1.0` | nadie en producción | tests | `.claude/harness.tools.json`, que nunca se escribe | `name@version` | 6 de ciclo; `PASS`, `FAIL`, `NOT_RUN`; `retryPolicy`, `timeoutSeconds` | catálogo | dormido |
| Installation y señal de la barra | `harness-installation/1.1`; `runtime/contextbar.json` | la bienvenida; `statusline.py` | la bienvenida, `-Doctor` | `.claude/harness.installation.json` | el proyecto; `sessionId` | `READY`, `PARTIAL`, `BLOCKED` | estado de la instalación | sí |

**Ninguno es un contrato de ejecución.** El contrato nuevo usa algunos por referencia, sin
adoptarlos:

| Se usa | Para qué |
|---|---|
| La WorkUnit | Es la entrada (D7) |
| `refutacion.huella` y `planFingerprint` | La identidad del plan (D9) |
| `resolver_ruteo` | La existencia del agente (D4) |
| `capacidades.disponibles` | La disponibilidad (D4) |
| La decisión de la compuerta normativa | Lo normativo (D12) |
| El `executionId` del ledger de seguridad | Un lugar de correlación futuro |
| `WORKUNIT_*` | Publicación futura (D15) |
| `scope.json` | Un consumidor futuro (§32) |
| Los cuatro valores del `status` del `agentResult` | El vocabulario de `declaredStatus` del AgentReport (D8) |

**No se adopta:**

- el `agentResult` como contrato: Execution no lo lee. Recibe un AgentReport del Host Adapter, y del
  `agentResult` toma solo su vocabulario de cuatro valores (D8);
- los "Result Statuses";
- el `run` de la refutación;
- los estados de la revisión de fuentes;
- el reintento y el timeout del `tool-contract`.

## 6. Contradicciones

Cada una tiene evidencia en el código, en un schema o en un pendiente. **Destino** dice qué hace
esta Task con ella: la resuelve una decisión de esta spec, va a un pendiente, o pasa a otra Task.
Ninguna se arregla tocando el Plan.

| # | Contradicción | Evidencia | Destino |
|---|---|---|---|
| EC-01 | Un plan es `READY_FOR_EXECUTION` con una unidad cuyo `agentExists` es `false` | `plan.py:320-326, 418-426`; FH:1661-1668 | **La resuelve la frontera** (D3, D4: `AGENT_UNAVAILABLE`). El Plan no cambia |
| EC-02 | Las unidades de `orchestration`, `refutation` y `tooling` salen con `assignedAgent: ""`, sin aviso, y el plan llega a `READY_FOR_EXECUTION` | `registro_agentes.py:342-348`; `plan.py:313`; FH:251-268 | **La frontera** las rechaza (`AGENT_UNAVAILABLE`; y `AGENT_NOT_EXECUTABLE` para las dos primeras aunque se les asigne su agente, D5). El arreglo de Planning sigue en FH |
| EC-03 | `PENDING` se lee como "lista", y solo dice que el tier se aprobó y no faltaba una capacidad al armar: no mira el agente, ni las dependencias, ni la compuerta | `plan.py:320-326` | D3 |
| EC-04 | `(plan_id, plan_version)` no identifica un documento: `--propuesta` pisa el plan y vuelve a 1 | `plan.py:260-261, 288-294`; `dev-harness.py:1235-1244`; C-07 | D9: la identidad es la huella. El Plan no cambia (FH *Plan rebuilds lose history*) |
| EC-05 | Las aprobaciones no se pueden satisfacer. Se escribe solo `PENDING`, no hay comando, y replanificar las recalcula desde cero | `consumo.py:74-83`; `dev-harness.py:1229-1234, 1843-1845`; FH:1520-1529 | D12: la request no lleva aprobaciones |
| EC-06 | "execution" nombra a la contabilidad: `execution-accounting-event`, `execution-summary/1.0`, `execution-cost.md`, "contabilidad de ejecución" | `execution-accounting-event.schema.json:3-4`; `bin/contabilidad/agregacion.py:31`; `bin/contabilidad/libro.py:28`; `dev-harness.py:1458` | Vocabulario (§26). No se renombra, por D9 de Task 2. Los contratos nuevos usan `execution-` para la ejecución de verdad |
| EC-07 | Los tipos de ciclo de vida no tienen productor, y `metadata` no tiene cómo llevar un `executionId` | `eventos.py:27-42, 78-90`; E-40; FH:545-562 | D15: consecuencia para Task 4 |
| EC-08 | Una capability disponible para HARNESS no es una capability disponible para el agente que corre. `jira.issue.read` está `ENABLED` para el cliente HTTP del CLI, y ningún `tools:` llega a Jira ni a GitLab. Las locales no se verifican | `capacidades.py:22-26`; `plan.py:252-255`; `bin/integraciones/jira.py:19`; `agents/dev-backend.md:4` | D13 (`CAPABILITY_UNAVAILABLE` al entregar) y pendiente nuevo |
| EC-09 | Un agente válido para el registro no es un agente que el Host pueda invocar. En la fábrica, los `dev-*` son `VALID`, porque el archivo está en `harnesses/desarrollo/agents/`, y no están en `.claude/agents/`. El registro no mira `tools:` ni `model:` | `registro_agentes.py:126-180`; `roster.py:69-81` | D13 (`AGENT_UNAVAILABLE` al entregar) |
| EC-10 | El mismo huérfano tiene dos respuestas: `AGENT_NOT_FOUND` en el plan y `ORPHAN_AGENT` en el ruteo. El plan nunca escribe `ORPHAN_AGENT`, que está en su enum | `roster.py:181-192`; `registro_agentes.py:380-386`; `orchestration-plan.schema.json:157-160` | D4 usa `routable`, no el motivo. Pendiente nuevo |
| EC-11 | Los contratos de salida no coinciden. El `agentResult` tiene 4 estados en 8 agentes; 7 skills tienen 7 conjuntos distintos; 20 skills no tienen ninguno; nada tiene schema ni lector | `agents/dev-backend.md:101-114`; `skills/dev-backend-implementation/SKILL.md:520-532`; C-24 | D8 |
| EC-12 | Un agente al que se le pide declarar su propia existencia: `dev-integration.md` le hace emitir `agentExists: true` y `SPECIALIZED_SKILL_GAP`. La existencia la decide el registro | `agents/dev-integration.md:86-96`; MC, `### Agent` | D8: Execution no lee existencia declarada por un agente. Pendiente nuevo, de texto |
| EC-13 | Los especialistas "devuelven resultados a `dev-orchestrator`", y `dev-orchestrator` no recibe nada: escribe la propuesta y corre `plan` | `agents/dev-backend.md:13`; `agents/dev-orchestrator.md:43-53` | D8: quien recibe el informe es Execution, a través del Host Adapter. Pendiente nuevo, junto con EC-12 |
| EC-14 | `scope.json` y `checks.json` "los escribe quien ejecutó", y nadie ejecuta | `refutation-unit.schema.json:100, 127`; `UPGRADE.md:203` | Diferido (§32, P4). Los contratos de la refutación no cambian |
| EC-15 | El ledger de seguridad reserva un `executionId` y siempre lo deja nulo | `security-ledger-event.schema.json:45-50`; `productores.py:117` | D9 fija su forma. Llenarlo se difiere (§32, P4) |
| EC-16 | `BLOCKED` nombra tres cosas: una unidad sin capacidad, una RefutationUnit sin alcance y un agente que no pudo seguir | `orchestration-plan.schema.json:262`; `refutation-unit.schema.json:90`; `agents/dev-backend.md:106` | D10: Execution no tiene `BLOCKED`. El del agente es una declaración |
| EC-17 | Hay campos de reintento y de escalamiento que nadie lee | `consumo.py:23`; `plan.py:363`; `modelo.py:91-106`; `tool-contract.schema.json:63-81` | El contrato no los adopta (D19; §32, P1) |
| EC-18 | El presupuesto premium se gasta al planificar, no al ejecutar | `consumo.py:67-72`; C-49 | D12: Execution no gasta presupuesto. Los reintentos de una unidad premium, a §32 |
| EC-19 | Una identidad del Host funciona como clave de dominio: el `session_id` es la LedgerKey de la barra | `statusline.py:190, 211`; C-13 | D9 y D16: la identidad de una ejecución no depende del Host |
| EC-20 | El hash del TaskContext no es determinista, así que no sirve como huella del contexto de una ejecución | `bin/contexto/comun.py:49`; C-17; FH:1489-1504 | D7: se registra y no se compara |
| EC-21 | Dos textos dicen todavía que el disco decide si un agente existe. Uno es "los siete especialistas… todavía no tienen su .md"; el otro, "declarado en el roster y no tiene su .md" | `docs/orquestacion.md:327-329`; `roster.py:224-225` | Pendiente nuevo |
| EC-22 | Un plan acepta un agente de otro dominio sin decir nada. El `assignedAgent` de la propuesta se conserva, y `agentExists` no mira el dominio, aunque el registro declara un dueño por dominio | `plan.py:313, 337`; MC, `### AgentRegistry` | D6 (`AGENT_DOMAIN_MISMATCH`). Pendiente nuevo, para Planning |
| EC-23 | Las skills piden capabilities que ningún catálogo declara, como `filesystem.read`, o `test.execute` frente a `tests.run` | `skills/dev-backend-implementation/SKILL.md:538-559`; `skills/dev-appsec-review/SKILL.md:869-871`; FH:1593-1603; C-25 | Pendiente existente. Una propuesta que las pida no llega a `READY_FOR_EXECUTION` |
| EC-24 | `requiredChecks` lista GuardrailCheck por unidad, y PostToolUse corre todos los instalados en cada llamada, sin saber qué unidad ni qué agente actúa | `plan.py:358`; `comun/hooks/lib/reglas.py:43-69`; FH:405-435 | D16: Guardrails observan sin atribución. Pendiente existente |

**Son 24.** Las que más pesan en el contrato son EC-01, EC-03, EC-04, EC-08, EC-11 y EC-22.

## 7. Objetivo

Definir el **Execution Contract** de HARNESS: el contrato estable que toma **una** WorkUnit de un
Plan en `READY_FOR_EXECUTION` y la convierte en una solicitud de ejecución explícita, gobernada y
observable. También representa el resultado de esa ejecución, y lo hace sin atar el dominio a Claude
Code, a un proveedor de modelo, a un framework de agentes ni a una implementación.

```
Plan (orchestration-plan/2.0)          Planning, sin cambios
   │  READY_FOR_EXECUTION, WorkUnit PENDING
   ▼
ExecutionAdmission                     la regla de entrada (D3, D4)
   │  ExecutionRequest  (execution-request/1.0)
   ▼
[motor futuro, Task 4]                 entrega, corre, observa
   │  salida nativa del Host → Host Adapter → AgentReport
   │  ExecutionResult   (execution-result/1.0)
   ▼
Execution                              el registro: request, ciclo de vida, resultado
```

El criterio de terminado es la sección 34 del pedido. Task 4 tiene que poder recibir una
ExecutionRequest y devolver un ExecutionResult **sin volver a decidir** nada de esto:

- la identidad y las precondiciones;
- los estados, el dueño de cada cosa y los errores;
- la evidencia;
- dónde termina la contabilidad, el Host, y el agente, la capacidad y la tool;
- la compatibilidad.

## 8. Modelo propuesto

### 8.1 Los candidatos, uno por uno

| Candidato | Problema real que resuelve | ¿Alcanza con Plan y WorkUnit? | Identidad | Ciclo | Persiste | Crea / cambia / consume | Dominio o infraestructura | ¿Ahora? |
|---|---|---|---|---|---|---|---|---|
| **ExecutionRequest** | Fijar qué se pidió ejecutar, de qué versión exacta del plan, y qué condiciones valían al admitirla | No. El plan se pisa (EC-04) y la WorkUnit no tiene estado posterior (I-15) | ExecutionId | No: es inmutable | Sí (Task 4) | La crea la admisión; no la cambia nadie; la consumen el motor y la auditoría | Dominio | Sí |
| **ExecutionResult** | Decir cómo terminó un intento, con qué evidencia observada y qué declaró el agente | No: la WorkUnit "no tiene resultado" (MC, `### WorkUnit`) | La de su request | No: es terminal | Sí (Task 4) | Lo crea el motor; no lo cambia nadie; lo consumen las dependencias y la auditoría | Dominio | Sí |
| **ExecutionId** | Nombrar un intento sin depender del Host, y llenar el hueco del ledger de seguridad (EC-15) | No: `WorkUnit.id` se repite entre intentos y entre planes | Su valor | No | Adentro de la request | Lo genera la admisión | Dominio | Sí |
| **ExecutionAttempt / AttemptId** | Distinguir intentos | Sí, sin concepto nuevo: **una Execution es un intento** (D1) | — | — | — | — | — | **No** |
| **ExecutionStatus** | El ciclo de vida | Es el ciclo del agregado, no un concepto aparte, igual que el plan no tiene un `PlanStatus` | — | — | — | — | — | **No**, va en Execution |
| **ExecutionError** | Representar una falla sin excepciones ni texto libre | No: el plan no tiene errores | No | No | Adentro del resultado; el rechazo de admisión vuelve al que pidió | Lo crean la admisión y el motor | Dominio | Sí |
| **ExecutionOutput** | El texto que devuelve el agente | — | — | — | — | — | — | **No.** Lo reemplaza **AgentReport**: lo que importa no es la salida sino que es un informe sin autoridad (D8) |
| **AgentReport** | Separar lo que el agente afirma de lo que el motor observa, y que Execution reciba un dato con forma y no una salida nativa del Host | No | No | No | No como documento: su `declaredStatus` se copia al resultado, y su `artifact` se guarda aparte, redactado, referido por huella | Lo arma el Host Adapter desde la salida nativa; lo recibe Execution | Dominio (DTO / Contract) | Sí |
| **ExecutionEvidence** | Lo que el motor observó del árbol: la revisión antes y después, y los cambios. Los tiempos del intento son del resultado | No | No | No | Adentro del resultado | La observa el motor | Dominio | Sí |
| **Execution** (agregado) | Los invariantes del conjunto: transiciones válidas, terminal inmutable, resultado ligado a su request, una ejecución abierta por clave | No | ExecutionId | Sí | Sí (Task 4) | Lo crea la admisión; lo cambia el motor, una transición a la vez | Dominio | Sí |
| **ExecutionAdmission** | La regla que decide si una WorkUnit puede pasar | No. Planning decide el estado del documento, no si algo corre ahora (EC-01, EC-03) | No | No | No | La invoca quien pide; la aplica el motor otra vez al entregar | Dominio (Domain Service) | Sí, como regla. Su implementación es de Task 4 |
| **IdempotencyKey** | Distinguir un reintento de un duplicado | Sí, como campo: `idempotencyKey` de la request (D19). No hace falta un concepto | — | — | — | — | — | **No** |
| **ExecutionRecord** | El registro persistido | Es el agregado Execution con otro nombre | — | — | — | — | — | **No** |

### 8.2 El modelo

| Concepto | Contexto | Clasificación | Qué es |
|---|---|---|---|
| Execution | Execution | Aggregate Root | Un intento de llevar a cabo una WorkUnit: su request, su ciclo de vida y su resultado |
| ExecutionRequest | Execution | Record | La constancia inmutable de que una WorkUnit se admitió para ejecutar |
| ExecutionResult | Execution | Record | La constancia inmutable de cómo terminó un intento |
| ExecutionId | Execution | Value Object | La identidad de un intento, generada por HARNESS |
| ExecutionAdmission | Execution | Domain Service | La regla de entrada, con su precedencia |
| ExecutionError | Execution | Value Object | Una falla con un código de una lista cerrada |
| ExecutionEvidence | Execution | Value Object | Lo que el motor observó del árbol: revisión y cambios |
| AgentReport | Execution | DTO / Contract | Lo que el Host Adapter entrega a Execution: `declaredStatus` y `artifact`; sin autoridad |

Son ocho conceptos, todos con una de las doce clasificaciones de Task 2. Ninguno es un Domain Event.

### 8.3 Las decisiones de esta sección

#### D1. Una request, una WorkUnit, un intento

**Una ExecutionRequest identifica exactamente una WorkUnit**, y una Execution es exactamente un
intento. "Uno o más WorkUnits" son N requests.

Se descartó una request por lote, o por plan entero. Las razones:

- la identidad, el ciclo de vida, la evidencia y la atribución contable son por WorkUnit;
- la refutación también es por WorkUnit: `scope.json` va por `workUnitId`;
- un lote necesita estados parciales, como "tres de cinco terminaron", y eso es un scheduler, que
  es Task 5.

#### D2. Ocho conceptos, y los que no entraron

Entran los ocho de 8.2. No entran ExecutionAttempt, ExecutionStatus, ExecutionOutput,
IdempotencyKey ni ExecutionRecord, por las razones de la tabla de 8.1. El criterio es el de Task 2:
un concepto entra si tiene contrato o evidencia, no porque esté en una lista de DDD.

## 9. La frontera Planning → Execution

### 9.1 Las cinco preguntas

1. **¿`READY_FOR_EXECUTION` quiere decir que todas las WorkUnits se pueden ejecutar?** No. Quiere
   decir que el plan, al armarse, no tenía capacidades faltantes, ni aprobaciones `PENDING`, ni
   unidades `BLOCKED` (`plan.estado_de`, `plan.py:418-426`). Por construcción, en un plan
   `READY_FOR_EXECUTION` todas las unidades están `PENDING`. No dice nada de:
   - si el agente existe (EC-01, EC-02);
   - si las dependencias ya corrieron;
   - si la compuerta normativa deja usar la norma **ahora**;
   - si el Host puede correr ese agente con esas capacidades (EC-08, EC-09).
2. **¿Una WorkUnit `PENDING` es ejecutable?** Es **necesario y no suficiente** (EC-03).
3. **¿Quién decide que una WorkUnit está lista?** La **ExecutionAdmission**, de Execution. No
   decide con criterio propio: consume lo que ya decidieron Planning, Normative Sources y Catalog, y
   suma lo único que es de Execution, que son las dependencias cumplidas y el no duplicado.
4. **¿Qué tiene que valer antes de crear una request?** Las condiciones de la tabla de 9.2.
5. **¿Qué es de Planning y qué de Execution?** La tabla de 9.3.

#### D3. `READY_FOR_EXECUTION` y `PENDING` son necesarias y no suficientes

El Plan no cambia: sus estados siguen siendo del documento, y se siguen derivando de su contenido
(ADR-0013 §4, I-15). **La admisión es la que decide si una unidad corre.** Se descartaron dos
alternativas:

- **Que `estado_de` mire `agentExists`.** Es la salida que FH:1667-1668 dejó abierta. Cambia el
  comportamiento de Planning, cambia qué significa un estado que ya está en planes guardados, y no
  alcanza: el agente puede dejar de existir entre el plan y la ejecución.
- **Un estado nuevo de la WorkUnit, como `READY` o `ADMITTED`.** Es exactamente lo que Task 2 sacó
  del contrato 2.0 (C-02) y lo que I-15 prohíbe.

### 9.2 La regla de admisión

La aplica la ExecutionAdmission **dos veces, con la misma regla**:

- **al crear la request.** Si falla, no se crea nada: vuelve un ExecutionError al que pidió;
- **antes de entregarla.** Si falla, la Execution termina `REJECTED`.

Se mira en este orden, y se informa **el primer código que falla**:

| # | Condición | Código si falla | Dueño del dato |
|---|---|---|---|
| 1 | La TaskKey, el id de la WorkUnit y quien pide tienen forma | `CONTRACT_INVALID` | Execution |
| 2 | El plan existe y lo acepta la regla de lectura única (`plan.aceptar_guardado`) | `PLAN_UNREADABLE` | Planning |
| 3 | `meta.task_key` del plan es la TaskKey pedida | `TASK_KEY_MISMATCH` | Planning |
| 4 | Solo al entregar: la huella del plan es la de la request | `PLAN_CHANGED` | Planning |
| 5 | El plan está `READY_FOR_EXECUTION` | `PLAN_NOT_READY` | Planning |
| 6 | La WorkUnit está en el plan | `WORK_UNIT_NOT_FOUND` | Planning |
| 7 | La WorkUnit está `PENDING` | `WORK_UNIT_NOT_PENDING` | Planning |
| 8 | La compuerta normativa no dio `blocked` | `NORMATIVE_GATE_BLOCKED` | Normative Sources |
| 9 | El AgentRegistry deja rutear el `assignedAgent` **ahora** | `AGENT_UNAVAILABLE` | Catalog |
| 10 | El agente es `SPECIALIST_AGENT` o `INFRASTRUCTURE_AGENT` | `AGENT_NOT_EXECUTABLE` | Catalog |
| 11 | El dominio del agente en el registro es el de la WorkUnit | `AGENT_DOMAIN_MISMATCH` | Catalog |
| 12 | Cada `requiredCapability` está disponible **ahora**. Al entregar, además, la provee quien va a correr | `CAPABILITY_UNAVAILABLE` | Catalog (y el Host Adapter, D13) |
| 13 | Cada dependencia tiene una Execution `SUCCEEDED` del mismo plan, por su huella | `DEPENDENCY_NOT_SATISFIED` | Execution |
| 14 | No hay **otra** Execution, con un `executionId` distinto del actual, abierta o `SUCCEEDED`, con la misma `idempotencyKey`. Al pedir todavía no hay Execution actual; al entregar, la propia Execution `REQUESTED` no es un duplicado de sí misma | `DUPLICATE_EXECUTION` | Execution |

Se informa un solo código para que el resultado sea determinista. El orden va por capas, y la capa
dice de quién es el dato:

1. la forma de lo pedido;
2. Planning;
3. Normative Sources;
4. Catalog;
5. el estado de Execution.

Una aprobación pendiente sale como `PLAN_NOT_READY`, porque el plan queda en
`WAITING_FOR_HUMAN_APPROVAL`. En un plan editado a mano que diga `READY_FOR_EXECUTION`, sale como
`WORK_UNIT_NOT_PENDING`.

#### D4. Cada condición se consume de su dueño, no se recalcula

Cada condición se lee de quien la decide, con su propio código:

| Condición | Se lee de |
|---|---|
| El plan | `plan.aceptar_guardado` |
| La existencia del agente | `registro_agentes.resolver_ruteo`, y su `routable` |
| El tipo y el dominio del agente | El AgentRegistry |
| La disponibilidad | `capacidades.disponibles` |
| La decisión normativa | `auto_refresh.ensure_normative_knowledge_fresh`, igual que en `plan` |

Se usa `routable`, no el motivo: el motivo tiene dos respuestas distintas para el mismo huérfano
(EC-10). `agentExists` y `agentValidation` del plan son historia del armado: **decide el registro
al admitir** (EC-01).

#### D5. Execution no corre agentes de Planning ni de Governance

`dev-orchestrator`, un `ORCHESTRATOR_AGENT`, planifica. `dev-refutador`, un `CRITIC_AGENT`, refuta
por su propio contrato, que es `refute --unit` y `--record`. Si Execution los corriera, estaría
replanificando o refutando por otra puerta.

Por eso una WorkUnit de `orchestration` o de `refutation` sale `AGENT_NOT_EXECUTABLE`, aunque se le
asigne su agente. `dev-tool-builder` es `INFRASTRUCTURE_AGENT` y sí entra: construir una tool es
trabajo, no planificación.

#### D6. El agente tiene que ser el dueño del dominio de la WorkUnit

El plan acepta cualquier `assignedAgent` (EC-22), y el registro declara un dueño por dominio.
Además, el ContextSlice se recortó para el dominio de la unidad (`CONTEXTO_POR_DOMINIO`). Correrla
con el agente de otro dominio le da un contexto recortado para otro dueño, con skills que no son
suyas.

La admisión **rechaza** la WorkUnit y no elige otro agente, porque elegir sería replanificar. El
hueco de Planning va a un pendiente.

### 9.3 Qué decide Planning y qué hace cumplir Execution

| Condición | La decide | La hace cumplir Execution |
|---|---|---|
| La descomposición, el dominio, el agente asignado, las capacidades, las dependencias y el contexto de la unidad | Planning, al armar | No los cambia nunca. Los copia en la request (D7) |
| El tier de modelo y si necesita aprobación | Planning (ModelRouter, ConsumptionGate) | Admite solo unidades `PENDING`. No resuelve aprobaciones ni gasta presupuesto (D12) |
| El estado del plan y el de la unidad | Planning, derivado del contenido | Exige `READY_FOR_EXECUTION` y `PENDING` |
| Que el plan sea el mismo que se admitió | — | Por la huella, al entregar (`PLAN_CHANGED`) |
| Si se puede usar la norma | Normative Sources, con la compuerta | Con `blocked`, rechaza con `NORMATIVE_GATE_BLOCKED` (D12) |
| Si el agente existe, de qué tipo y de qué dominio es | Catalog | Al admitir y al entregar (D4, D5, D6) |
| Si una capacidad está disponible | Catalog, y el Host Adapter al entregar | Al admitir y al entregar (D13) |
| Si las dependencias ya corrieron, y si no hay un duplicado | Execution | Al admitir y al entregar |

## 10. ExecutionRequest

**Qué es:** la constancia inmutable de que una WorkUnit concreta, de un plan concreto, se admitió
para ejecutar. La escribe la admisión y nadie la modifica.

### 10.1 Los campos

| Campo | Marca | Dueño del dato | Por qué |
|---|---|---|---|
| `schema_version` | required | Execution | `execution-request/1.0`, enum de un solo valor |
| `executionId` | required, derived | Execution | Lo genera la admisión (D9) |
| `idempotencyKey` | required, derived | Execution | `huella([taskKey, planFingerprint, workUnit.id])` (D19) |
| `createdAt` | required, derived | Execution | En UTC, `YYYY-MM-DDTHH:MM:SSZ` |
| `requestedBy` | required | Quien pide. Execution lo registra | Quién pidió la ejecución: una persona o una automatización nombrada. Texto, que se redacta |
| `taskKey` | required, derived | Work Intake | Sale de `meta.task_key` del plan |
| `plan` | required, derived | Planning (valores), Execution (huella) | `planId`, `planVersion`, `planFingerprint` y `schemaVersion`, que es la versión con que se leyó el plan (`2.0` o `1.0`). Cerrado |
| `taskContextRef` | required, derived | Work Intake | `{path, contextHash}`, copiado de `meta.task_context_ref`. Es una referencia, no una copia (D7) |
| `workUnit` | required, derived | Planning | **La WorkUnit tal como está en el plan** (D7) |
| `workUnitFingerprint` | required, derived | Execution | La huella de `workUnit` |
| `admission` | required, derived | Execution lo escribe; los hechos son de Planning, Catalog y Normative Sources | Lo que valía al admitir (10.2). Cerrado |
| `domain`, `assignedAgent`, `requiredCapabilities` y `dependencies` en la raíz | **forbidden** | Planning | Ya están en `workUnit`. Duplicarlos es invitar a que difieran |
| Aprobaciones "ya satisfechas" | **forbidden** | Planning | Ninguna se puede satisfacer hoy (EC-05). Una unidad admitida es `PENDING`, y eso ya dice que no necesita aprobación (D12) |
| Decisiones de Governance | **forbidden** | Governance | Las de Governance son posteriores a la ejecución: la refutación necesita la evidencia (D12). La decisión de la compuerta normativa no es de Governance: es de Normative Sources, y va en `admission` |
| Permisos de tools | **forbidden** | El Host | Son del Host: `permissions.deny`, el `tools:` de los agentes y la SecretGate (D13) |
| Timeout y presupuesto | **forbidden** en 1.0 | El motor | Ningún dueño de dominio decide un timeout por unidad. Es configuración del motor (Task 4), y el CostBudget es evidencia, no permiso (MC, `### CostBudget`). Lo que se aplicó sale en el error `TIMEOUT` |
| Sesión y correlación del Host | **forbidden** | El Host | La request no depende del Host (D16). La sesión va en `result.host` |
| Modelo y proveedor concretos | **forbidden** | El runtime | El tier ya está en `workUnit.modelPolicy`. Pasar del tier a un modelo lo resuelve el runtime |
| `attempt` y `priorExecutionId` | **forbidden** | — | Se derivan: las Executions con la misma `idempotencyKey`, ordenadas por `createdAt` |
| El TaskContext entero | **forbidden** | Work Intake | Va por referencia (D7) |

### 10.2 `admission`: lo que valía al admitir

| Campo | Valores que valida el schema | Qué registra |
|---|---|---|
| `planStatus` | `READY_FOR_EXECUTION` | El estado del plan leído |
| `agent.validation` | `VALID`, `VALID_WITH_PENDING_SKILLS` | Lo que dijo el registro al admitir |
| `agent.type` | `SPECIALIST_AGENT`, `INFRASTRUCTURE_AGENT` | El tipo en el registro (D5) |
| `agent.domain` | texto | El dominio en el registro. El validador exige que sea `workUnit.domain` (D6) |
| `capabilities` | `ALL_AVAILABLE` | Que todas las `requiredCapabilities` estaban disponibles |
| `normativeGate` | `allowed`, `unresolved` | La decisión de la compuerta |
| `dependencies[]` | `{workUnitId, executionId}` cerrado | La Execution `SUCCEEDED` que satisfizo cada dependencia |

El schema rechaza por sí solo un request cuyo registro de admisión dice que una condición no se
cumplió: un plan que no está listo, un agente que no existe, una capacidad que falta o una compuerta
que bloqueó. Así, la precondición queda **en el contrato** y no solo en el código de quien admite.

Los valores no se aceptan sin mirar: el motor los vuelve a derivar al entregar (EX-I21). Un request
escrito a mano con valores que pasan no lleva a ejecutar una unidad que no corresponde.

### 10.3 La WorkUnit adentro del request

`execution-request/1.0` **no repite la forma de la WorkUnit**. Restringe seis campos y deja el resto
a la definición de `orchestration-plan.schema.json`, que sigue siendo la autoridad:

| Campo | Restricción del contrato de ejecución |
|---|---|
| `id` | El patrón del plan |
| `domain` | Texto |
| `assignedAgent` | `^dev-[a-z0-9-]+$`, el patrón del registro. Un agente en blanco no valida (EC-02) |
| `requiredCapabilities` | Cada una con forma de capability, `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`. Un `Read` no valida (EC-23; Capability ≠ Tool) |
| `dependencies` | Cada una con el patrón de id |
| `status` | `PENDING` |

`ejecucion.contrato.validar_request` valida además el snapshot contra
`workUnits.items` de `orchestration-plan.schema.json`. Cuando el plan cambie de forma, el request lo
sigue sin una copia que mantener.

### 10.4 Un ejemplo

```json
{
  "schema_version": "execution-request/1.0",
  "executionId": "exe_5b1f0c9e2a7d4c3fa0e8b6d4c2a1f9e7",
  "idempotencyKey": "sha256:…",
  "createdAt": "2026-10-20T14:03:11Z",
  "requestedBy": "Nahue Palacio",
  "taskKey": "GCBA-1234",
  "plan": {"planId": "pln_GCBA-1234", "planVersion": 2,
           "planFingerprint": "sha256:…", "schemaVersion": "orchestration-plan/2.0"},
  "taskContextRef": {"path": ".claude/contextos/GCBA-1234.json", "contextHash": "…"},
  "workUnit": {"id": "implementar-endpoint", "domain": "backend",
               "assignedAgent": "dev-backend", "status": "PENDING", "…": "la unidad entera"},
  "workUnitFingerprint": "sha256:…",
  "admission": {"planStatus": "READY_FOR_EXECUTION",
                "agent": {"validation": "VALID", "type": "SPECIALIST_AGENT", "domain": "backend"},
                "capabilities": "ALL_AVAILABLE", "normativeGate": "allowed",
                "dependencies": [{"workUnitId": "analizar-api",
                                  "executionId": "exe_0c…"}]}
}
```

## 11. ExecutionResult

**Qué es:** la constancia inmutable de **cómo terminó un intento**. Existe solo cuando el intento
es terminal, y se escribe una sola vez.

### 11.1 Lo que no es

| | Qué es | Dónde vive | Quién lo decide |
|---|---|---|---|
| **ExecutionResult** | Si el intento corrió y terminó con un AgentReport válido que declara `COMPLETE`, cuándo empezó y terminó, y qué observó el motor del árbol | Execution | El motor |
| Veredicto SDD (`sostenido`, `contradicho`, `leído`, `sin sustento`) | Si un cambio de la fábrica cumple su spec | El método de la fábrica, fuera del producto | `harness-spec-refuter` |
| EvaluationResult | Si una regla o un control se cumple | Governance | ControlCheck, refutación, resolución de ES0902 |
| Evidence | Un hecho observado que sostiene una afirmación normativa | Governance | Señales, checks, refutador |
| RefutationVerdict | El juicio sobre una RefutationUnit | Governance | `dev-refutador`, un check o la caché |
| AccountingEvent | El consumo de modelo observado | Observability | La `statusLine` y `contabilidad --ingerir` |
| AgentReport | Lo que el Host Adapter entrega de la salida del agente: `declaredStatus` y `artifact` | Execution, sin autoridad | El Host Adapter, desde la salida nativa del agente |

#### D8. Execution recibe un AgentReport del Host Adapter, sin autoridad, y `SUCCEEDED` es mecánico

**El AgentReport es el contrato lógico que el Host Adapter entrega a Execution.** No es un documento
persistido ni tiene schema: es lo que cruza la frontera entre el adaptador y Execution, y lo valida
`ejecucion.contrato.validar_informe` (§22).

```
salida nativa del Host y del agente      prosa, Markdown, un bloque `agentResult`, lo que sea
        ↓
Host Adapter                             Task 4: sabe leer la salida de su Host
        ↓
AgentReport                              {declaredStatus, artifact}
        ↓
Execution                                no ve la salida nativa
        ↓
ExecutionResult                          agentDeclaredStatus, output {path, fingerprint}
```

| Campo | Qué es |
|---|---|
| `declaredStatus` | Exactamente uno de `COMPLETE`, `PARTIAL`, `BLOCKED` o `FAILED`: lo que el agente declara de su trabajo |
| `artifact` | El informe del agente como lo entregó el Host: texto, que puede estar vacío. Execution lo redacta antes de guardarlo aparte, y en el resultado queda solo su ruta y su huella |

El AgentReport tiene esas dos claves y ninguna más.

- **Execution no interpreta texto.** No busca palabras en texto libre, no parsea Markdown y no
  interpreta los "Result Statuses" de las skills. El `artifact` es opaco: su contenido no cambia
  nada de lo que Execution decide.
- **Si el Host Adapter no puede producir un AgentReport con un `declaredStatus` válido**, el
  intento termina `FAILED` con `OUTPUT_INVALID`, sin `agentDeclaredStatus` y sin `output`.
- **Cómo obtiene el `declaredStatus` el adaptador de Claude Code lo decide Task 4.** Task 3 decide
  qué recibe Execution.
- **`SUCCEEDED` quiere decir:** el motor entregó la request, el intento terminó, el Host Adapter
  entregó un AgentReport válido, y su `declaredStatus` es `COMPLETE`. **No quiere decir que el
  trabajo cumple una norma ni una spec.** Eso lo dicen la refutación y, en la fábrica, el método SDD.
- **`declaredStatus` es una declaración y nunca decide sola:** un `PARTIAL`, `BLOCKED` o `FAILED`
  da `FAILED` con `AGENT_DECLARED_NOT_COMPLETE`.
- **El vocabulario de cuatro valores sale del `agentResult`**, porque es el único común a los ocho
  agentes que se pueden ejecutar. Execution toma el vocabulario, no el formato: no lee el bloque
  `agentResult`.
- **Lo demás que el agente afirme** (`changedComponents`, `tests`, `risks`) queda en el `artifact`,
  y no entra al resultado.
- **Execution no lee una existencia declarada por el agente** (EC-12). Quien recibe el informe es
  Execution, a través del Host Adapter, no `dev-orchestrator` (EC-13).

Es la respuesta a la tercera pregunta de Task 2: **ni el `agentResult` ni los "Result Statuses".**
El contrato de salida es el AgentReport que produce el Host Adapter. Su `declaredStatus` usa el
vocabulario de cuatro valores del `agentResult`.

No hace falta un tercer schema: el AgentReport no se persiste como documento. Lo que de él se
guarda está en `execution-result` (`agentDeclaredStatus` y `output`), y el texto, en el archivo del
informe (§21).

### 11.2 Los campos

| Campo | Tipo | Cuándo | Qué es |
|---|---|---|---|
| `schema_version` | `execution-result/1.0` | siempre | — |
| `executionId` | `^exe_[0-9a-f]{32}$` | siempre | El de su request |
| `requestFingerprint` | `sha256:` | siempre | La huella de su request: un request tocado después ya no es el suyo |
| `status` | `SUCCEEDED`, `FAILED`, `CANCELLED`, `REJECTED` | siempre | Solo terminales |
| `error` | ExecutionError o `null` | siempre presente | `null` si y solo si `SUCCEEDED` |
| `startedAt` | UTC o `null` | siempre presente | Cuándo se entregó. `null` si nunca se entregó. Con `endedAt`, es **el único lugar** donde vive el tiempo del intento: la evidencia no lleva tiempos (§18) |
| `endedAt` | UTC | siempre | Cuándo quedó terminal |
| `agentDeclaredStatus` | `COMPLETE`, `PARTIAL`, `BLOCKED`, `FAILED` o `null` | siempre presente | El `declaredStatus` del AgentReport (D8). `null` si no hubo un AgentReport válido |
| `output` | `{path, fingerprint}` o `null` | siempre presente | El `artifact` del AgentReport, redactado y guardado aparte. Ruta relativa, sin `..`. `null` si no hubo un AgentReport válido |
| `evidence` | ExecutionEvidence o `null` | siempre presente | Lo que observó el motor del árbol (§18). `null` si nunca se entregó |
| `host` | `{kind, sessionRef, runRef}` o `null` | siempre presente | Correlación con el Host, opaca (D16) |

Todos los campos son obligatorios, y los que no tienen valor van como `null`: lo que falta se dice,
no se omite. No hay tokens, ni costo, ni referencias contables, ni prompts, ni transcripciones, ni
llamadas a tools. Un `ExecutionResult` no es un contenedor universal.

### 11.3 Coherencias que el schema no puede decir

El validador del repo interpreta un subconjunto: `type`, `properties`, `required`, `items`, `enum`,
`pattern`, `additionalProperties`, `$ref` y `minimum` (`contexto-armar.py:736-737`). No tiene
condicionales. Lo que sigue lo hace cumplir `ejecucion.contrato.validar_resultado`, con el mismo
precedente que `eventos.validar_estructura` en el Bloque 4:

1. `executionId` es el de la request, y `requestFingerprint` es la huella de la request.
2. `status == SUCCEEDED` si y solo si `error` es `null`.
3. `error.code` es uno de los permitidos para su `status` (tabla de §14).
4. `REJECTED` lleva `startedAt`, `evidence`, `output` y `agentDeclaredStatus` en `null`.
5. Con `startedAt`, `evidence` no es nula. Sin `startedAt`, `evidence` es nula.
6. `agentDeclaredStatus` y `output` son los dos nulos o los dos no nulos: vienen del mismo
   AgentReport (D8).
7. Con un AgentReport, el `status` lo decide su `declaredStatus`, y sin él no hay `SUCCEEDED`:
   - `COMPLETE` si y solo si `SUCCEEDED`;
   - `PARTIAL`, `BLOCKED` o `FAILED` si y solo si `FAILED` con `AGENT_DECLARED_NOT_COMPLETE`;
   - por eso `OUTPUT_INVALID`, que es no haber recibido un AgentReport válido, y `CANCELLED` llevan
     los dos en `null`.
8. `SUCCEEDED` y `FAILED` llevan `startedAt`, porque solo se llega a ellos desde `RUNNING` (§13).
9. Con `evidence.changes.state` distinto de `RESOLVED`, `files` es `[]`.
10. Toda ruta, de `output` o de `files`, es relativa y POSIX, no tiene `..`, y no se repite.
11. `createdAt ≤ startedAt ≤ endedAt` cuando están, y `createdAt ≤ endedAt` siempre.
12. `error.detail` no está vacío y tiene 300 caracteres o menos. Es el tope de `libro.TOPE_DE_TEXTO`.

## 12. Identidad

| Identidad | Forma | Qué identifica | En la request | En el resultado |
|---|---|---|---|---|
| TaskKey | `^[A-Za-z][A-Za-z0-9_]*-[0-9]+$` | La Task | `taskKey` | por la request |
| Plan | `planId` más `planVersion` más **`planFingerprint`** | Un documento de plan exacto | `plan` | por la request |
| WorkUnit | `(planFingerprint, workUnit.id)` | Una unidad de un plan exacto | `workUnit`, `workUnitFingerprint` | por la request |
| **ExecutionId** | `exe_` más 32 hexadecimales, al azar | Un intento | `executionId` | `executionId` |
| Clave de idempotencia | `huella([taskKey, planFingerprint, workUnit.id])` | "La misma unidad del mismo plan" | `idempotencyKey` | por la request |
| AttemptId | — | No existe: un ExecutionId ya es un intento | — | — |
| HostSession | el `session_id` del Host | Una sesión de Claude Code u otro Host | **prohibido** | `host.sessionRef`, opcional |
| Correlación contable | `eventId` es `ev_` más sha256 | Un evento de consumo | no | no. La correlación va al revés (D15) |
| `executionId` del ledger de seguridad | texto o `null` | Hoy, nada | — | El ExecutionId de 1.0 le entra tal cual |

#### D9. ExecutionId generado por HARNESS, y el plan identificado por su huella

- **ExecutionId** es `exe_` más 32 hexadecimales al azar, y lo genera la admisión. No se deriva ni
  del Host, ni de la sesión, ni del contenido. Es la identidad, no la deduplicación: para eso está
  la `idempotencyKey`.
- **`planFingerprint`** es la huella del plan **tal como se leyó**: `sha256:` del JSON canónico,
  con claves ordenadas, separadores `,` y `:` y UTF-8 sin escapar. Es la misma función que
  `refutacion.huella`, y el mismo valor que el `planFingerprint` de `run.json`. Por eso **la
  refutación y la ejecución de un mismo plan se correlacionan sin acoplarse.**
  - `plan_version` se conserva, porque es lo que lee una persona. No alcanza: vuelve a 1 (EC-04).

Las preguntas del pedido:

- **¿Hace falta un ExecutionId?** Sí: `WorkUnit.id` se repite entre intentos y entre planes, y el
  ledger de seguridad ya tiene dónde ponerlo (EC-15).
- **¿Una WorkUnit se puede ejecutar más de una vez?** Sí. Después de `FAILED`, `CANCELLED` o
  `REJECTED`, una request nueva con la misma clave es un reintento. Después de `SUCCEEDED`, no
  (D19).
- **¿Qué identifica cada intento?** Su ExecutionId.
- **¿Un reintento conserva el ExecutionId?** No. Es una Execution nueva, con la misma
  `idempotencyKey`.
- **¿La HostSession es identidad?** No: es observabilidad, y va en el resultado (EC-19).
- **¿El resultado se correlaciona sin el Host?** Sí: con `executionId` y `requestFingerprint`.

## 13. Ciclo de vida

| Estado | Qué quiere decir | Lo escribe | Entra desde | Sale a | Terminal |
|---|---|---|---|---|---|
| `REQUESTED` | Admitida y registrada; todavía no se entregó | La admisión | (creación) | `RUNNING`, `REJECTED`, `CANCELLED` | no |
| `RUNNING` | **El motor la entregó a quien la corre** (el Host u otro runner) y todavía no registró un resultado | El motor, al entregar | `REQUESTED` | `SUCCEEDED`, `FAILED`, `CANCELLED` | no |
| `SUCCEEDED` | Terminó con un AgentReport válido cuyo `declaredStatus` es `COMPLETE` (D8) | El motor | `RUNNING` | — | sí |
| `FAILED` | Se entregó y terminó sin eso: falla del Host o del proveedor, interrupción, timeout, ningún AgentReport válido, o el agente declaró otra cosa | El motor | `RUNNING` | — | sí |
| `CANCELLED` | Alguien la canceló explícitamente antes de que fuera terminal | El motor, a pedido | `REQUESTED`, `RUNNING` | — | sí |
| `REJECTED` | Se admitió pero no se entregó: la regla de admisión ya no valía al entregar | El motor | `REQUESTED` | — | sí |

#### D10. Seis estados, cuatro terminales, sin `BLOCKED`

- **`RUNNING` empieza cuando el motor entrega**, no cuando "el modelo piensa". Es lo único que un
  motor puede observar. Además sirve igual para un motor que lanza al Host y para uno que entrega
  la request, como hace la refutación con `--unit`.
- **No hay `ACCEPTED`.** Separar "tomada por un worker" de "entregada" sirve con una cola, que es
  Task 5. Se agrega como versión menor si hace falta.
- **No hay `BLOCKED`** (EC-16). El `BLOCKED` de la WorkUnit es "le falta una capacidad al
  planificar". En Execution, eso es un rechazo con `CAPABILITY_UNAVAILABLE`. El `BLOCKED` del
  `declaredStatus` de un AgentReport es una declaración, y da `FAILED` con
  `AGENT_DECLARED_NOT_COMPLETE`. Ninguno
  de los dos es un estado en el que una ejecución se queda.
- **Un rechazo al crear no es un estado:** no hay Execution. Vuelve un ExecutionError al que pidió.
  **No se persiste**, porque no tiene identidad y la salida del comando es su constancia.
- **Un resultado terminal no cambia.** Un resultado tardío para una Execution terminal, por ejemplo
  después de una cancelación o de un timeout, se rechaza y no se escribe.

Lo que el pedido separa:

| Caso | Cómo se representa |
|---|---|
| Falla de precondición al pedir | No hay Execution. ExecutionError con el código de 9.2, devuelto al que pidió |
| Rechazo de la ejecución | `REJECTED`, con el código de 9.2 que falló al entregar |
| Bloqueo de la compuerta normativa | `NORMATIVE_GATE_BLOCKED`: al pedir, como error devuelto; al entregar, como `REJECTED`. La compuerta es de Normative Sources. **No hay una autorización de Governance antes de ejecutar**: Governance actúa después, o independiente (§15) |
| Falla de la ejecución | `FAILED`, con un código de corrida |
| Interrupción del Host | `FAILED`, con `HOST_INTERRUPTED`. Es infraestructura, no una decisión de nadie. Una Execution que quedó `RUNNING` sin proceso vivo termina así cuando el motor lo detecta. Nunca se reanuda sola |
| Cancelación | `CANCELLED`, solo por un pedido explícito |

## 14. Modelo de errores

Un ExecutionError es `{code, detail}`:

- **`code`** es uno de una lista cerrada, y es lo único que lee una máquina;
- **`detail`** es texto en español para una persona, redactado y de hasta 300 caracteres.

Ni excepciones de Python, ni texto libre que haya que interpretar.

| Código | Categoría | Al pedir | `REJECTED` | `FAILED` | `CANCELLED` |
|---|---|---|---|---|---|
| `CONTRACT_INVALID` | contrato | ✓ | ✓ | | |
| `PLAN_UNREADABLE` | precondición | ✓ | ✓ | | |
| `TASK_KEY_MISMATCH` | precondición | ✓ | ✓ | | |
| `PLAN_CHANGED` | precondición | | ✓ | | |
| `PLAN_NOT_READY` | precondición | ✓ | ✓ | | |
| `WORK_UNIT_NOT_FOUND` | precondición | ✓ | ✓ | | |
| `WORK_UNIT_NOT_PENDING` | precondición | ✓ | ✓ | | |
| `NORMATIVE_GATE_BLOCKED` | normative sources | ✓ | ✓ | | |
| `AGENT_UNAVAILABLE` | agente | ✓ | ✓ | ✓ | |
| `AGENT_NOT_EXECUTABLE` | agente | ✓ | ✓ | | |
| `AGENT_DOMAIN_MISMATCH` | agente | ✓ | ✓ | | |
| `CAPABILITY_UNAVAILABLE` | capacidad | ✓ | ✓ | ✓ | |
| `DEPENDENCY_NOT_SATISFIED` | precondición | ✓ | ✓ | | |
| `DUPLICATE_EXECUTION` | precondición | ✓ | ✓ | | |
| `HOST_FAILURE` | host | | | ✓ | |
| `HOST_INTERRUPTED` | host | | | ✓ | |
| `PROVIDER_FAILURE` | proveedor | | | ✓ | |
| `TIMEOUT` | ejecución | | | ✓ | |
| `OUTPUT_INVALID` | ejecución | | | ✓ | |
| `AGENT_DECLARED_NOT_COMPLETE` | ejecución | | | ✓ | |
| `ENGINE_FAILURE` | ejecución | | | ✓ | |
| `CANCELLED` | cancelación | | | | ✓ |

#### D11. Una lista cerrada de 22, sin `TOOL_UNAVAILABLE`

- **Una tool que falta es una capacidad que no se provee.** El contrato no nombra tools (D13), así
  que su error tampoco: sale `CAPABILITY_UNAVAILABLE`.
- **`AGENT_UNAVAILABLE` y `CAPABILITY_UNAVAILABLE` pueden ser `FAILED`.** Pasa cuando quien corre
  descubre, después de la entrega, que no puede: un agente que el Host no encuentra (EC-09) o una
  tool que no está (EC-08).
- **`PROVIDER_FAILURE` se usa solo cuando el Host distingue al proveedor.** Si no lo distingue, es
  `HOST_FAILURE`.
- **`ENGINE_FAILURE` es una falla del motor mismo**, como un error de disco, y no se disfraza de
  falla del Host.
- **`OUTPUT_INVALID` quiere decir que el Host Adapter no pudo producir un AgentReport con un
  `declaredStatus` válido** (D8). No lo decide Execution leyendo texto.
- **`NORMATIVE_GATE_BLOCKED` nombra a su dueño.** La compuerta es de Normative Sources, no de
  Governance, y los dos contextos siguen separados. No hay un código de "governance denegó",
  porque no hay una autorización de Governance antes de ejecutar (D12).

**Qué es contrato y qué es detalle:** es contrato el código, a qué estado puede ir y la regla de
precedencia. Son detalle del motor o del proveedor el texto de `detail`, los códigos internos del
Host o del proveedor, y cómo se detecta cada caso.

**Lo que no se diseña:** si un código se puede reintentar. Es política de reintento (§32, P1).

## 15. Governance

| Quién | Decide |
|---|---|
| **Planning** | La descomposición, el dominio, el agente asignado, las capacidades, las dependencias, el ContextSlice y el tier. También si el tier necesita aprobación (la ModelTierApproval es de costo, no de governance) y el estado del plan y de cada unidad. La aplicabilidad normativa de cada unidad viaja adentro de la WorkUnit, en `normative` |
| **Normative Sources** | Si la norma se puede usar: `allowed`, `blocked` o `unresolved`, con la compuerta. Para Execution: `allowed` y `unresolved` admiten, y `blocked` da `NORMATIVE_GATE_BLOCKED` |
| **Governance** | Qué controles existen, qué evalúan los ControlCheck, los RefutationVerdict, el SecuritySummary y la ExternalSecurityApproval. **Todo esto es posterior o independiente de la ejecución:** la refutación necesita la evidencia de lo que se hizo (`EXECUTION_REQUIRED`) |
| **Catalog** | Si un agente existe, de qué tipo y de qué dominio es. Qué capacidades están disponibles |
| **Execution hace cumplir** | La regla de 9.2, consumiendo esas decisiones sin recalcularlas. Rechaza en vez de replanificar |
| **Guardrails observan e interceptan** | Durante `RUNNING`, el Host corre la SecretGate (`deny`, `ask`) y los GuardrailCheck (avisos) en cada llamada a una HostTool. Execution no los llama, no lee sus avisos, y no los puede atribuir a una ejecución (EC-24). Un `deny` es un hecho de esa llamada, no un estado de la ejecución: el agente puede seguir |
| **Observability registra** | El consumo. Nunca decide (D15) |

#### D12. Consumir, no recalcular; las aprobaciones no viajan

- **ModelTierApproval:** Execution no resuelve aprobaciones ni gasta presupuesto premium (EC-18).
  Ninguna se puede satisfacer hoy (EC-05), así que una unidad que la necesitó no llega a `PENDING`
  y no se admite. Cuando exista cómo resolverlas, eso va a cambiar el Plan, que es de Planning, no
  la request (§32, P3).
- **Policies:** son prosa normativa. Viajan en `workUnit.normative` y no se ejecutan.
- **ControlChecks:** Execution no los corre. Producir `checks.json` desde una ejecución se difiere
  (§32, P4).
- **GuardrailChecks:** los corre el Host. `requiredChecks` viaja en la WorkUnit como información.
- **`requiredCapabilities`:** se verifican al admitir y al entregar (D13).
- **Permisos de tools:** son del Host. No entran al contrato.
- **Evidencia normativa:** la de las señales viaja en `workUnit.normative`. Execution no la evalúa.
- **La compuerta normativa:** se consulta al admitir, como en `plan`, y su decisión queda en
  `admission.normativeGate`:

  ```
  NormativeFreshnessGate.allowed      → admite
  NormativeFreshnessGate.unresolved   → admite, como en `plan`
  NormativeFreshnessGate.blocked      → NORMATIVE_GATE_BLOCKED
  ```

  Es una decisión de **Normative Sources**, y el código la nombra así. Si la compuerta refresca
  fuentes, esos efectos son suyos (MC, `### NormativeFreshnessGate`).
- **No hay una autorización de Governance antes de ejecutar.** Este contrato no agrega ninguna:
  Governance sigue siendo posterior a la ejecución, o independiente de ella.

## 16. Agent, Capability y Tool

| Concepto | En la frontera de la ejecución |
|---|---|
| **Agent** | Quién corre. La request nombra exactamente uno, el `workUnit.assignedAgent`, validado contra el registro al admitir y al entregar |
| **Capability** | Qué tiene que estar disponible. La request lleva `workUnit.requiredCapabilities`, con forma de capability. Nunca una tool |
| **HostTool** | Cómo el Host realiza una capability. Es del Host: el `tools:` del agente, `permissions.deny` y la SecretGate. **El contrato no la nombra nunca** |
| **Capability de integración** | `jira.*` y `gitlab.*`, disponibles para HARNESS y no necesariamente para el agente que corre (EC-08) |
| **Proveedor y modelo** | Los resuelve el runtime desde el tier de `modelPolicy`. No entran a la request. Si el Host distingue un error del proveedor, entra como `PROVIDER_FAILURE` |
| **Host Adapter** | La pieza del motor que habla con un Host concreto (Task 4). Resuelve el agente y las capacidades, entrega la request, y convierte la salida nativa del Host en un **AgentReport** (D8). Es infraestructura: Execution no sabe qué Host hay detrás |

#### D13. Quién resuelve qué

- **¿La request pide un Agent o una Capability?** Las dos cosas, con papeles distintos: un Agent
  que corre, y las Capabilities que necesita.
- **¿Quién resuelve Capability → Tool?** El **Host Adapter**, el adaptador del motor al Host (Task 4), que es
  infraestructura. Nunca la request, ni el prompt del agente, ni el registro.
- **¿Quién resuelve Agent → implementación?** El mismo adaptador. Para Claude Code, es el subagente
  con ese `name:` en `.claude/agents/`. Para otro Host, lo que ese Host tenga.
- **¿El contrato lleva tools concretas?** No.
- **¿Quién convierte lo que devuelve el agente?** El Host Adapter, que entrega un AgentReport
  `{declaredStatus, artifact}`. Si no puede producir uno con un `declaredStatus` válido, el intento
  termina `FAILED` con `OUTPUT_INVALID`. Execution nunca recibe la salida nativa (D8).
- **¿Qué pasa si el agente existe para el registro y el Host no lo puede correr?** Si el adaptador
  lo descubre antes de entregar, la Execution termina `REJECTED` con `AGENT_UNAVAILABLE`. Si lo
  descubre quien corre después de la entrega, termina `FAILED` con `AGENT_UNAVAILABLE` (EC-09).
- **¿Y si la capability está disponible y nada la provee?** El adaptador declara qué capacidades
  provee. Al entregar, la regla es "disponible para Catalog **y** provista por el adaptador". Si
  falla, la Execution termina `REJECTED` con `CAPABILITY_UNAVAILABLE`. Si falla durante la
  corrida, termina `FAILED` con el mismo código (EC-08). Cómo declara el adaptador lo que provee lo
  decide Task 4 (§32, P7).

## 17. Contexto

| Contexto | Cómo viaja | Por qué |
|---|---|---|
| WorkUnit y su ContextSlice | **Copiada tal cual** en `workUnit`, con su huella | Es el insumo contractual. Además, el plan se pisa (EC-04) |
| TaskContext | **Referencia**: `taskContextRef` con `{path, contextHash}` del plan | Es grande y es de Work Intake. Su hash no es determinista (EC-20), así que se registra y **no se compara** |
| ProjectContext | No viaja | El agente lo lee del repositorio si lo necesita. La revisión del repo entra como evidencia (§18) |
| ProjectMemory | No viaja | La carga el Host (`CLAUDE.md`). Es contexto transitorio del Host |
| Normative Sources | La decisión de la compuerta, en `admission` | El conocimiento no se copia |
| Contexto transitorio del Host | Nunca | Ni la transcripción, ni la ventana, ni el `systemMessage` |

#### D7. Una copia de la WorkUnit, una referencia al TaskContext, y huellas

- **Una copia de la WorkUnit, no del plan.** Hay dos razones de dominio:
  1. el plan se pisa sin historia (EC-04, C-08), así que una referencia al plan deja de decir qué
     se pidió;
  2. la WorkUnit **ya está pensada para viajar sola**: "un especialista recibe su unidad suelta"
     (`orchestration-plan.schema.json:150`).

  Copiar el plan entero no agrega nada que la ejecución use.
- **Una referencia al TaskContext**, con su hash registrado. Compararlo dispararía rechazos falsos
  mientras C-17 siga abierta (§32, P8).
- **Dos huellas**: `planFingerprint` y `workUnitFingerprint`.

## 18. Evidencia

| | Qué es | La produce | ¿Entra en ExecutionResult? |
|---|---|---|---|
| **ExecutionEvidence** | Lo que el motor observó del árbol: la revisión del repo antes y después, los archivos que cambiaron con su huella, y el estado de esa observación. **No lleva tiempos** | El motor | **Sí**, en `evidence` |
| Evidence de Governance | Un hecho que sostiene una afirmación normativa | Señales, checks, refutador | **No.** La ExecutionEvidence puede ser **insumo** de la refutación (§32, P4), y Execution nunca decide cumplimiento |
| Evidencia de refutación | El veredicto, con evidencia dentro de su alcance | `dev-refutador`, checks, caché | No |
| Observabilidad y contabilidad | Tokens, costo, tiempo, ventana | Observability | No (D15) |
| Texto del agente | El `artifact` del AgentReport: el informe tal como lo entregó el Host | El agente, por el Host Adapter | **No.** Se guarda aparte, redactado. El resultado lleva su ruta y su huella (`output`) y, del AgentReport, solo `declaredStatus`, como `agentDeclaredStatus`. Execution no lee el texto (D8) |
| Artefacto producido | Los archivos que el agente cambió en el repo | El agente | Como **cambios observados** en `evidence.changes.files`. Los `changedComponents` que declara el agente son afirmaciones, y quedan en el `artifact` |

**Una sola autoridad para cada cosa:**

```
ExecutionResult          el tiempo del intento
  startedAt
  endedAt
ExecutionEvidence        el árbol
  repoRevisionBefore
  repoRevisionAfter
  changes
```

`evidence` es `{repoRevisionBefore, repoRevisionAfter, changes: {state, files[]}}`, cerrado y sin
ningún campo de tiempo. Cada archivo es `{path, change: ADDED | MODIFIED | DELETED, fingerprint}`.
`changes.state` puede ser:

- **`RESOLVED`**: se observó. Una lista vacía quiere decir que no cambió nada.
- **`CHANGES_UNRESOLVED`**: no se pudo observar, por ejemplo sin git.
- **`CHANGES_UNATTRIBUTABLE`**: se observaron cambios que no se pueden atribuir a esta ejecución,
  por ejemplo porque otra cosa tocó el árbol al mismo tiempo.

En los dos últimos, `files` va vacío: **lo que falta no es cero** (EX-I25), como en la contabilidad.

#### D14. Lo observado por el motor y lo declarado por el agente no se mezclan

Es la misma regla que ya tiene la normativa: "lo que interpreta un modelo no pisa un dato
estructurado" y "la afirmación de un agente, sola, no sostiene nada" (`docs/orquestacion.md:298-303`).

El motor observa el árbol y registra el tiempo del intento. El agente declara, y lo que declara le
llega a Execution solo por el AgentReport: `declaredStatus` es una declaración con forma, y el
`artifact` es texto opaco.

Las preguntas del pedido:

- **¿Qué se persiste?** La request, el resultado y el `artifact` redactado. **No** se persisten
  transcripciones, prompts, llamadas a tools, tokens ni diffs.
- **¿Qué prueba que una WorkUnit se ejecutó?** Un resultado escrito por el motor, con su
  `startedAt` y su `endedAt`, ligado a su request por la huella, con la huella del `artifact` y los
  cambios que observó el motor. **No hay prueba criptográfica: se confía en el motor** (§36).
- **¿Qué necesita Task 4 para ser verificable?** Que cada AgentReport pase `validar_informe`, y que
  cada request y cada resultado pasen `validar_request` y `validar_resultado` antes de escribirse.
  También, que los cambios observados se puedan contrastar con el árbol.
- **¿Qué no entra todavía al contrato?** La proyección a `scope.json` y `checks.json`, los eventos
  del ledger de seguridad, el contenido de los diffs, y una atestación del Host.

## 19. Contabilidad y observabilidad

**La contabilidad sigue sin ser estado de ejecución.** Es el invariante 1 de ADR-0013 §4, y esta
Task lo conserva.

#### D15. Execution publica en la contabilidad y nunca la lee

- **¿Qué eventos podría producir un motor?** Con los tipos que ya existen:
  - **`WORKUNIT_STARTED`** al pasar a `RUNNING`;
  - **`WORKUNIT_COMPLETED`** al quedar terminal **después de** `RUNNING`, con el estado terminal;
  - **`MODEL_CALL_COMPLETED`**, cuando se ingiere la transcripción de esa corrida atribuida a la
    ejecución. Es lo que hoy hace `--refutacion` para una unidad de refutación
    (`dev-harness.py:1380-1382`).

  Un `REJECTED`, o un `CANCELLED` antes de entregar, **no** produce eventos: no corrió, no consumió.
  **`TASK_STARTED` y `TASK_COMPLETED` no los produce nunca Execution**, porque la Task es externa y
  su ciclo es de Jira (ADR-0013 §2). `AGENT_RUN_*` no agrega nada: una ejecución corre un solo
  agente, y `agentId` ya atribuye.
- **¿Qué referencias hacen falta?** `taskId`, que es la TaskKey como LedgerKey; `workUnitId`;
  `agentId`; `sessionId` si el Host lo da; y **`metadata.executionId`**.
- **¿Alcanzan los eventos de hoy?** Los tipos, sí. Las claves, no: `metadata` es una lista cerrada
  sin `executionId` (`eventos.py:78-90`), y no hay campo de plan. **Consecuencia para Task 4:**
  sumar `executionId` a `CLAVES_DE_METADATA`, que es código de Observability y no el schema. Ese
  schema tiene `metadata` como objeto libre y **no cambia**. También le toca adaptar E-40, con su
  decisión escrita.
- **¿Algún enum anticipa el ciclo de vida sin productor?** Sí: `WORKUNIT_*`, `AGENT_RUN_*` y
  `TASK_*` en la contabilidad (EC-07), el `executionId` del ledger de seguridad (EC-15) y
  `RUNNING` en la revisión de fuentes, que no es ejecución.
- **El resultado no referencia eventos contables.** La correlación va de la contabilidad hacia la
  ejecución, por `executionId`, y nunca al revés. Ningún dato de un ledger cambia un estado de
  Execution.

## 20. Host

#### D16. El Host corre; no tiene autoridad ni identidad en el contrato

- **¿Quién inicia una ExecutionRequest?** Una persona, directamente por el CLI o a través de la
  sesión del Host que actúa en su nombre. Queda en `requestedBy`. El Host es **quien corre**, nunca
  quien decide: lo que pide pasa por la misma admisión.
- **¿El UUID de la HostSession va en la request?** No (EX-I08). Va en `result.host.sessionRef` si el
  Host lo da, y es solo observabilidad.
- **¿La cancelación del Host es dominio o infraestructura?** Cerrar la sesión o cortar con Ctrl-C es
  **infraestructura**, y da `FAILED` con `HOST_INTERRUPTED`. Cancelar es un **pedido explícito** al
  motor, y da `CANCELLED`.
- **¿stdin y stdout son parte del contrato?** No: son transporte del motor. La salida nativa del
  Host, por stdout, una transcripción o lo que ese Host use, la lee el **Host Adapter**, que
  entrega a Execution un AgentReport (D8). Execution no ve la salida nativa.
- **¿Las llamadas a tools del Host entran al resultado?** No. Son de Guardrails y Observability.
- **`result.host`** es `{kind, sessionRef, runRef}`, con texto libre y sin enum. `kind` puede ser
  `claude-code` o cualquier otro: **el contrato se puede implementar mañana con otro Host** sin
  cambiar de versión.

## 21. Persistencia

| Alternativa | Qué tendría | Por qué no, o por qué sí |
|---|---|---|
| Solo la request | La intención | No dice cómo terminó |
| Solo el resultado | El final | Pierde qué se pidió exactamente: el plan se pisa |
| Solo eventos | Un ledger de transiciones | Habría que plegarlo para saber el estado, y sería un segundo ledger al lado del contable. El contable no puede ser, por I-33 |
| Nada en Task 3 | — | **Es lo que hace Task 3:** no persiste ninguna ejecución. Pero el contrato decide qué persiste Task 4 |
| **El registro de cada Execution** | La request, la marca de entrega, el `artifact` del AgentReport y el resultado | **Se elige** |

#### D17. El estado vive en el registro de cada Execution, en archivos que no se modifican

Es la respuesta a la primera pregunta de Task 2: **ni en el Plan ni en la contabilidad.** El estado
vive en el registro de la propia Execution:

```
.claude/ejecuciones/<TaskKey>/<executionId>/
    request.json      execution-request/1.0   se escribe una vez, al admitir
    <marca>           infraestructura          se escribe una vez, al entregar (Task 4)
    output.<ext>      el artifact, redactado   se escribe una vez, si hubo AgentReport válido
    result.json       execution-result/1.0    se escribe una vez, al quedar terminal
```

- **La fuente de verdad es el estado derivado de lo que existe:**
  - `result.json` da el estado terminal;
  - si no hay `result.json`, la marca de entrega da `RUNNING`;
  - si tampoco hay marca, la Execution está `REQUESTED`.

  Ningún archivo se reescribe. La inmutabilidad del terminal es "`result.json` se crea una sola
  vez".
- **La clave** es `<TaskKey>/<executionId>`, igual que `.claude/refutaciones/<KEY>/`. El nombre
  `ejecuciones` sigue a sus hermanos `planes/`, `contextos/` y `refutaciones/`. La contradicción
  con ADR-0011 es la C-43, y la decide su pendiente, no esta Task.
- **Va bajo `.claude/`**, que se gitignorea entero (`install.ps1:1975-1977`) y sobrevive al
  `-Update`, como `planes/`. No va en `runtime/`: no es observabilidad, es un registro.
- **Para auditar** alcanzan la request, el resultado y la huella del `artifact`. **Reanudar** está
  fuera: una Execution `RUNNING` sin proceso vivo termina `FAILED` con `HOST_INTERRUPTED` (§13).
- **Versionado:** cada documento lleva su `schema_version`. Quien lo lee acepta una lista explícita,
  como `plan.VERSIONES_LEGIBLES`.
- **Lo que decide Task 4** (§32, P6): el formato de la marca, la escritura atómica de cada
  archivo, cómo se detecta un `RUNNING` huérfano y la extensión del informe. Cómo se reserva una
  `idempotencyKey` de forma atómica es otra decisión diferida (§32, P13). Que esa reserva sea
  atómica no es una decisión de Task 4: lo fija EX-I28.

## 22. Schemas

#### D18. Dos schemas y un validador puro, sin schema de error ni de AgentReport

| Schema | `$id` | Por qué existe |
|---|---|---|
| `comun/schemas/execution-request.schema.json` | `execution-request/1.0` | Es un documento persistido, con productor y momento propios: la admisión |
| `comun/schemas/execution-result.schema.json` | `execution-result/1.0` | Es otro documento, con otro productor y otro momento: el motor, al terminar |
| `execution-error.schema.json` | — | **No se crea.** Un error nunca vive solo en un archivo. Es `$defs.error` de `execution-result` |
| un schema de AgentReport | — | **No se crea.** El AgentReport cruza del Host Adapter a Execution y no se persiste como documento (D8). Su forma, dos claves cerradas y un enum, la valida `validar_informe` |

Un schema compuesto, con la request y el resultado en `$defs`, se descartó: son dos documentos con
dos productores, y la refutación, que es el precedente, tiene un schema por documento. Lo que sí
sigue a la refutación es poner en `$defs` lo que no es un documento propio.

La tabla tiene la forma de la 3.2 de la spec de Task 2, para que E-05 (S4) pueda leer las dos:

| Schema | Concepto | Productor | Runtime | Persistencia | Clase |
|---|---|---|---|---|---|
| `execution-request` | ExecutionRequest | ninguno: la admisión es de Task 4 | tests | `.claude/ejecuciones/<KEY>/<executionId>/request.json`, que todavía no escribe nadie | Record |
| `execution-result` | ExecutionResult, ExecutionError | ninguno: el motor es de Task 4 | tests | `.claude/ejecuciones/<KEY>/<executionId>/result.json`, que todavía no escribe nadie | Record |

**`$id` y versión.** Siguen la forma del repo (`orchestration-plan/2.0`). La compatibilidad es la de
ADR-0013 §6: `schema_version` promete **todo documento que el schema declara válido**.

- Un campo opcional o un enum más amplio es una versión menor: `1.1`.
- Achicar un enum, sacar un campo o volver obligatorio uno opcional es una versión mayor: `2.0`.
- Quien lee acepta una lista explícita.

**Dueño.** `comun/schemas/` no tiene un dueño declarado en `CLAUDE.md`, y Execution tampoco: es la
fila "sin dueño declarado", como Planning o Governance. Asignarlo es de Task 4, cuando haya código
que mantener (§33).

**El validador puro:** `harnesses/desarrollo/bin/ejecucion/contrato.py`. El subconjunto de JSON
Schema no tiene condicionales (11.3), y el precedente es `eventos.validar_estructura`. **No es la
admisión ni el motor:** no lee planes, ni registros, ni el disco del proyecto. Lee solo sus schemas
y el del plan, por `rutas.localizar`, como `plan.cargar_schema`.

| Nombre | Qué es |
|---|---|
| `VERSION_REQUEST`, `VERSION_RESULT` | Las dos versiones |
| `ESTADOS`, `TERMINALES`, `TRANSICIONES` | El ciclo de §13. `TRANSICIONES` tiene seis pares |
| `CODIGOS` | `{code: dónde puede ir}`, la tabla de §14 |
| `PRECEDENCIA` | Los catorce códigos de 9.2, en orden |
| `DECLARACIONES_DEL_AGENTE` | `COMPLETE`, `PARTIAL`, `BLOCKED`, `FAILED`: los valores de `declaredStatus` |
| `TIPOS_EJECUTABLES` | `SPECIALIST_AGENT`, `INFRASTRUCTURE_AGENT` |
| `huella(valor)` | El mismo algoritmo que `refutacion.huella`, **sin importar** la refutación: Execution no depende de un módulo de Governance para un hash. Un escenario fija que dan lo mismo (EX-E08) |
| `clave_de_idempotencia(task_key, plan_fingerprint, work_unit_id)` | La clave de D19 |
| `transicion_valida(desde, hacia)` | Si el par está en `TRANSICIONES` |
| `validar_request(doc)` | `[errores]`: el schema, el snapshot contra la WorkUnit del plan, y las coherencias de 10.1 a 10.3 (`planId`, huellas, clave, dominio, dependencias) |
| `validar_resultado(doc, request)` | `[errores]`: el schema y las doce coherencias de 11.3 |
| `validar_rechazo(error)` | `[errores]`: `$defs.error`, y que el código sea de los que pueden ir al pedir |
| `validar_informe(informe)` | `[errores]`: un objeto con exactamente `declaredStatus`, que es uno de `DECLARACIONES_DEL_AGENTE`, y `artifact`, que es texto. **No lee el contenido de `artifact`**: un texto que dice `status: COMPLETE` no arregla un `declaredStatus` que falta |

Las coherencias de `validar_request`:

1. el schema;
2. `workUnit` contra `workUnits.items` de `orchestration-plan.schema.json`;
3. `plan.planId == "pln_" + taskKey`;
4. `workUnitFingerprint == huella(workUnit)`;
5. `idempotencyKey == clave_de_idempotencia(taskKey, plan.planFingerprint, workUnit.id)`;
6. `admission.agent.domain == workUnit.domain`;
7. `admission.dependencies` nombra exactamente `workUnit.dependencies`, una vez cada una, con
   `executionId` distintos del propio.

## 23. Idempotencia

#### D19. La misma unidad del mismo plan: un duplicado mientras está abierta o después de un éxito

La **`idempotencyKey`** es `huella([taskKey, planFingerprint, workUnit.id])`, es decir, "esta
WorkUnit de este documento de plan".

- **¿Se puede pedir dos veces la misma WorkUnit?** Sí, con dos condiciones:
  - nunca dos Executions abiertas con la misma clave;
  - nunca una nueva después de un `SUCCEEDED` con esa clave.
- **¿Cómo se distingue un reintento de un duplicado?**
  - **Duplicado**: hay una Execution abierta (`REQUESTED`, `RUNNING`) o `SUCCEEDED` con la misma
    clave. Da `DUPLICATE_EXECUTION`.
  - **Reintento**: todas las anteriores con esa clave terminaron `FAILED`, `CANCELLED` o
    `REJECTED`. Es una Execution nueva, con otro ExecutionId.
- **¿Qué compara el motor?** La clave, y el estado derivado de las Executions guardadas con esa
  clave. Al entregar lo vuelve a comparar: es la misma regla de 9.2 aplicada otra vez (EX-I21), y
  no reemplaza a la reserva atómica.
- **Al entregar, la Execution se excluye a sí misma.** La segunda aplicación de la admisión
  verifica esto: *no existe **otra** Execution, con un `executionId` distinto del actual, abierta o
  `SUCCEEDED`, con la misma `idempotencyKey`.* La propia Execution `REQUESTED` no es un duplicado
  de sí misma (9.2, condición 14).
- **La reserva es atómica.** Reservar una `idempotencyKey` y crear su Execution son **una sola
  operación** respecto de otras admisiones de la misma clave (EX-I28). Si dos admisiones de la misma
  clave corren a la vez, exactamente una crea su Execution, y la otra recibe `DUPLICATE_EXECUTION`
  sin dejar nada escrito.
  - **Lo que queda fijado ahora:** que la atomicidad es necesaria. Task 4 no puede decidir que no
    lo es.
  - **Lo que decide Task 4:** el mecanismo, sea creación exclusiva, un lock, un índice u otro
    (§32, P13).
  - **Task 3 no implementa locking.**
- **¿Hace falta una huella o una clave de idempotencia?** Sí, la `idempotencyKey`. No hace falta
  una huella de toda la request: el `executionId` y la `createdAt` la hacen única por intento.
- **Lo que no se construye:** la deduplicación, el almacenamiento y la política de reintento
  (§32, P1).

## 24. Orden y dependencias

#### D20. El contrato conserva las dependencias y no decide el orden

- **Conserva:**
  - las `workUnit.dependencies`, en la copia;
  - qué Execution satisfizo cada una, en `admission.dependencies`;
  - la `planFingerprint`, que dice dentro de qué plan vale esa satisfacción.

  `executionOrder` queda en el Plan, donde está.
- **Una dependencia se satisface** con un `SUCCEEDED` de la unidad de la que se depende, **con la
  misma `planFingerprint`** (EX-I26). Después de replanificar, nada se arrastra: se vuelve a
  ejecutar. Es conservador, y reusar resultados entre versiones de un plan es de Task 5 (§32, P12).
- **La independencia en el plan no es concurrencia segura.** Dos unidades sin dependencia entre sí
  comparten el árbol de trabajo, y sus cambios no se pueden atribuir: para eso está
  `CHANGES_UNATTRIBUTABLE`. Decidir si se pueden correr a la vez, con qué workers y en qué orden
  dentro de una ola es de Task 5.
- **No se decide:** scheduler, pools, workers ni paralelismo.

## 25. La decisión del contexto delimitado

**A. Execution sigue reservado.** El contrato vive en esta spec y en el ADR, y el catálogo no
cambia.

- **A favor:** el modelo canónico describe lo que el código expresa, y Execution todavía no tiene
  productor.
- **En contra:**
  - Los schemas nuevos no tienen dónde vivir. E-05 exige que cada schema de `comun/schemas/` figure
    en la persistencia de algún concepto (`64_modelo_de_dominio.py:595-607`). Ponerlos en Planning
    hace que Planning tenga estado de ejecución, y rompe I-15 y D4 de Task 2. Ponerlos en
    Observability rompe I-33.
  - Sin schemas, el contrato no queda versionado, y Task 4 lo escribiría de nuevo y podría
    redecidirlo.
  - Las palabras quedan fuera del vocabulario canónico, que es justo lo que Task 2 vino a terminar.

**B. Execution pasa a ser un contexto delimitado.** Es **la que se elige**: un contexto
**contractual** hasta que Task 4 le dé productor. Cumple las cinco columnas del mapa:

| Columna | Qué tiene |
|---|---|
| Lenguaje propio | Request, admisión, intento, entrega, terminal, rechazo, clave de idempotencia, informe del agente, Host Adapter |
| Invariantes propias | EX-I01 a EX-I29 |
| Dueño | Sin dueño declarado, como Planning, Governance y Observability. Se asigna con Task 4 |
| Datos | `execution-request/1.0` y `execution-result/1.0`. Ninguno se persiste hasta Task 4 |
| Ciclo de vida | `REQUESTED → RUNNING → terminal` |

El precedente para tener conceptos con contrato y sin productor es HarnessTool, que está dormida y
nombrada en Catalog (MC:676-689).

#### D21. Execution es el décimo contexto

| | |
|---|---|
| **Entradas** | El Plan (Planning), por la regla de lectura única; el AgentRegistry y las capacidades (Catalog); la decisión de la compuerta (Normative Sources); quien pide; y, durante la corrida, el AgentReport que entrega el Host Adapter |
| **Salidas** | La ExecutionRequest y el ExecutionResult. A futuro, y fuera de esta Task: eventos para Observability, y evidencia que la refutación puede usar |
| **Dependencias** | Planning, Catalog y Normative Sources, como cliente o conformista. El Host, por el Host Adapter, que es la capa anticorrupción (Task 4) |
| **Lo que no depende de Execution** | Planning, Governance y Observability no leen a Execution para decidir nada |

## 26. Impacto en el modelo canónico, y el ADR

### 26.1 `docs/dominio/modelo-canonico.md`

| Qué cambia | Cómo |
|---|---|
| `## Conceptos` | Ocho filas y ocho bloques nuevos (8.2), con los diez campos de siempre. `Dónde vive` dice "contrato en `comun/schemas/` y `bin/ejecucion/contrato.py`; sin productor hasta Task 4" |
| `### Agent` | Una línea: para Execution, el agente existe si el registro lo deja rutear **al admitir** |
| `### WorkUnit` | Una línea: su ejecución es una Execution, de otro contexto, y la WorkUnit sigue sin resultado ni estado posterior |
| `## Mapa de contextos` | **Diez** contextos. La fila de Execution con sus cinco columnas (§25). Sale la frase "Execution no es un contexto: es un límite reservado" |
| `### Relaciones` | Planning → Execution, **Conformista** (la regla de lectura y la forma de la WorkUnit). Catalog → Execution, **Conformista**. Normative Sources → Execution, **Cliente-proveedor**. Host → Execution, **Capa anticorrupción** (el Host Adapter, Task 4, que entrega el AgentReport). Execution → Observability, **Publicación**, a futuro. Execution → Governance, **Publicación** de evidencia, a futuro |
| `## Lo que no es lo mismo` | Seis desigualdades nuevas. Las de Task 2 quedan |
| `## Vocabulario` | Filas nuevas o corregidas (abajo) |
| `## El límite de la ejecución` | Se reescribe en tres partes: qué existe ahora, qué sigue sin existir, y qué queda fijado (§26.3) |

Las seis desigualdades nuevas:

1. **ExecutionResult ≠ EvaluationResult**: uno dice si un intento terminó; el otro, si una regla se
   cumple.
2. **ExecutionEvidence ≠ Evidence**: una la observa el motor; la otra sostiene una afirmación
   normativa.
3. **AgentReport ≠ ExecutionResult**: lo que el agente dice no es lo que el motor registra.
4. **ExecutionId ≠ HostSession**: identidad contra observabilidad.
5. **`READY_FOR_EXECUTION` ≠ admitida**: necesaria, no suficiente.
6. **`BLOCKED` de la WorkUnit ≠ ningún estado de Execution.**

El vocabulario:

| Término | Nombre canónico |
|---|---|
| execution / ejecución, en `execution-accounting-event`, "contabilidad de ejecución", `execution-summary`, `execution-cost.md` | **AccountingEvent** / **AccountingSummary**. Los nombres no cambian (EC-06) |
| execution / ejecución, en `execution-request`, `execution-result` y `executionId` | **Execution** |
| intento / attempt | Una **Execution** |
| admisión / admitir | **ExecutionAdmission** |
| informe del agente | **AgentReport**: lo que entrega el Host Adapter, `{declaredStatus, artifact}`. En el resultado, `declaredStatus` es `agentDeclaredStatus` |
| `agentResult` | Una salida nativa posible del agente, que lee el Host Adapter de Claude Code (Task 4). Execution no la lee. De ahí sale el vocabulario de `declaredStatus` |
| Host Adapter | La pieza del motor que habla con un Host. No es un concepto de dominio: es infraestructura de Execution |
| "Result Statuses" de las skills | No es un concepto de Execution |
| run / corrida | En Execution no se usa. "Entregar" es pasar a `RUNNING` |
| `BLOCKED` | Un estado de **WorkUnit** o de **RefutationUnit**, o una declaración de **AgentReport**. Nunca un estado de Execution |

### 26.2 `docs/adr/0014-el-contrato-de-ejecucion.md`, nuevo

El nombre sigue a los demás ADR (C-43). Lleva `estado: aceptada`, y siete decisiones:

1. Execution deja de ser un límite reservado y pasa a ser el décimo contexto, contractual hasta que
   Task 4 le dé productor.
2. Una ExecutionRequest es una WorkUnit, un intento y una identidad que genera HARNESS. No depende
   del Host.
3. `READY_FOR_EXECUTION` y `PENDING` son necesarias y no suficientes. Decide la admisión, con una
   precedencia cerrada, consumiendo lo que deciden Planning, Normative Sources y Catalog, sin
   recalcularlo y sin replanificar.
4. Seis estados, cuatro terminales, sin `BLOCKED`. Un resultado terminal no cambia.
5. Execution recibe del Host Adapter un AgentReport, `{declaredStatus, artifact}`, sin autoridad, y
   nunca interpreta texto. `SUCCEEDED` es mecánico, no de cumplimiento.
6. El estado de una ejecución vive en su propio registro, ni en el Plan ni en la contabilidad. Los
   dos invariantes de ADR-0013 §4 siguen.
7. `orchestration-plan/2.0` no cambia, y la identidad del plan para ejecutar es su huella.

**Revisa el punto 4 de ADR-0013**, como prevé su `## Revisión`, **sin romper sus dos invariantes.**
ADR-0013 no se edita: es historia. Su propia revisión ya anunciaba este cambio.

### 26.3 Lo que queda fijado para Task 4

- Los dos invariantes de ADR-0013 §4, intactos:
  - la contabilidad no es estado de ejecución;
  - el estado del Plan se deriva del contenido del Plan.
- Los invariantes de la sección 29 que dicen "Task 4".
- Las consecuencias de §34.3.

## 27. Compatibilidad

| Pregunta | Respuesta |
|---|---|
| ¿El contrato afecta a `orchestration-plan/2.0`? | No. No agrega campos ni estados, y no cambia ni el productor ni la regla de lectura. Execution lee el plan **por la regla de lectura única**, así que un `1.0` compatible también se puede ejecutar |
| ¿Hace falta `orchestration-plan/3.0`? | No. Ninguna contradicción lo pide: EC-01 a EC-04 se resuelven en la frontera, y es la preferencia del pedido |
| ¿El Plan 2.0 queda intacto? | Sí. El schema y `plan.py` quedan iguales byte a byte a los de `f9393cf` (EX-E41) |
| ¿Qué datos se reusan? | `plan_id`, `plan_version` y `task_key`; `task_context_ref`; la WorkUnit entera; `executionOrder` (Task 5); `refutacion.huella` como algoritmo; la regla de la TaskKey; `resolver_ruteo`; `capacidades.disponibles`; la compuerta; el `executionId` del ledger de seguridad, que acepta el formato `exe_…`; los tipos `WORKUNIT_*` |
| ¿Qué migración hace falta? | Ninguna. No hay ejecuciones guardadas que migrar |
| ¿Y la contabilidad? | Sin cambios. `execution-accounting-event.schema.json` igual byte a byte (EX-E42). Lo que pide Task 4 está en §19 |
| ¿Y los tests de Task 2? | Cambian **tres asserts**, por la decisión escrita de ADR-0014: E-03 (nueve contextos y Execution reservado), E-05 (46 schemas) y E-09 (los anclajes del límite). §34 dice cómo, y cada cambio lleva su motivo en un comentario. E-40, E-41 y E-42 no cambian |
| ¿Y un proyecto instalado? | Recibe dos schemas y un módulo que nadie llama (EX-E53). Nada de lo que ya hacía cambia |

## 28. Seguridad

| Riesgo | Qué lo cubre en el contrato | Invariante | Lo hace cumplir |
|---|---|---|---|
| Un agente arbitrario | `assignedAgent` con la forma del registro; admisión por `routable`, tipo y dominio | EX-I04, EX-I05, EX-I06 | El schema y el validador (Task 3); la admisión (Task 4) |
| Una tool arbitraria | El contrato no tiene campo de tools; las tools las ata el Host | EX-I07, EX-I23 | El schema (Task 3); el Host |
| Una capability falsificada | La disponibilidad se deriva de Catalog y del Host Adapter, nunca de la request; las capabilities tienen forma | EX-I07, EX-I21 | La admisión y el motor (Task 4) |
| Una request falsificada | El motor no confía en los campos derivados: los vuelve a derivar del plan y del registro antes de entregar, y compara las huellas | EX-I21 | El motor (Task 4) |
| Una TaskKey que no coincide | `TASK_KEY_MISMATCH`; `planId == pln_<taskKey>` | EX-I02 | El validador (Task 3); la admisión (Task 4) |
| Una versión de plan que no coincide | Por la huella, no por la versión: `PLAN_CHANGED` | EX-I03 | El motor (Task 4) |
| Una WorkUnit que no es del plan | `WORK_UNIT_NOT_FOUND`; la huella de la unidad | EX-I02 | La admisión (Task 4) |
| Un replay, o dos admisiones a la vez | `executionId` único; `idempotencyKey`; la reserva atómica de la clave; un terminal no se reescribe; un resultado tardío se rechaza | EX-I09, EX-I10, EX-I12, EX-I28 | El motor y el almacenamiento (Task 4), con el mecanismo de P13 |
| Un contexto adulterado | La copia de la unidad con su huella. El TaskContext tiene su hash registrado, pero no comparado (EC-20) | EX-I11 | El validador (Task 3). El hueco de C-17, en §36 |
| Un secreto que se filtra | La request, el resultado y el `artifact` del AgentReport pasan por la misma redacción que el plan (`limpieza.redactar_arbol`) antes de escribirse. No se guardan prompts ni conversación. `detail` se redacta y tiene tope | EX-I24 | El motor (Task 4). El schema sin campos de texto libre del agente (Task 3) |
| Una salida insegura | La salida nativa no llega a Execution: el Host Adapter entrega un AgentReport. El `artifact` es dato no confiable y opaco, que no se ejecuta, no se interpreta como instrucción y no se lee. Execution usa solo `declaredStatus`, de un enum cerrado | EX-I16 | `validar_informe` (Task 3); el Host Adapter y el motor (Task 4) |

## 29. Invariantes

**Se verifica en** dice dónde se puede contradecir cada uno:

- **Task 3**: lo verifica esta construcción, con el schema, el validador, un chequeo estático o el
  documento;
- **Task 4**: necesita la admisión, el motor o el almacenamiento, y pasa a la spec de Task 4 como
  escenario.

| Id | Invariante | Cómo se observa | Dueño | Se verifica en |
|---|---|---|---|---|
| EX-I01 | Una request identifica exactamente una WorkUnit de exactamente un plan | `workUnit` es un objeto, no una lista; `plan` es uno | Execution, el contrato | Task 3 |
| EX-I02 | La request pertenece a la Task de su plan: `planId == pln_<taskKey>`, y la unidad está en ese plan | Validador; admisión | Execution | Task 3 (forma); Task 4 (pertenencia) |
| EX-I03 | Solo se admite una WorkUnit `PENDING` de un plan `READY_FOR_EXECUTION`, leído por `plan.aceptar_guardado`, y se identifica el plan por su huella | Enums de `admission` y de `workUnit.status`; la admisión | Execution | Task 3 (enums); Task 4 (lectura y huella) |
| EX-I04 | El AgentRegistry es la autoridad de existencia **al admitir y al entregar**; `agentExists` del plan no decide | `admission.agent.validation`; la admisión | Catalog, y lo cumple Execution | Task 3 (enum); Task 4 |
| EX-I05 | Execution no corre agentes `ORCHESTRATOR_AGENT` ni `CRITIC_AGENT` | `admission.agent.type` | Execution | Task 3 |
| EX-I06 | El agente es el dueño, en el registro, del dominio de la WorkUnit | Validador | Execution | Task 3 |
| EX-I07 | Capability ≠ Tool: el contrato nombra capabilities con forma, y nunca HostTools | Patrón; no hay campo de tools | Execution | Task 3 |
| EX-I08 | La identidad de una ejecución no depende del Host: ni el `executionId` ni la request llevan nada del Host | Patrón de `executionId`; nombres de propiedades | Execution | Task 3 |
| EX-I09 | Un `executionId` nombra un solo intento; un reintento es otra Execution con la misma `idempotencyKey` | Validador (clave); almacenamiento | Execution | Task 3 (clave); Task 4 |
| EX-I10 | A lo sumo una Execution abierta por clave, y ninguna nueva después de un `SUCCEEDED` con esa clave. Al entregar, la comparación excluye a la propia Execution: cuenta solo otra con un `executionId` distinto | Admisión y entrega | Execution | Task 4 (EX-F02) |
| EX-I11 | La copia de la WorkUnit y el plan tienen su huella, y la huella es la de `refutacion.huella` | Validador | Execution | Task 3 |
| EX-I12 | Un resultado es terminal y no cambia: no hay transición desde un terminal, y `result.json` se escribe una vez | `TRANSICIONES`; el almacenamiento | Execution | Task 3 (transiciones); Task 4 (escritura) |
| EX-I13 | `SUCCEEDED` si y solo si el error es nulo, y cada código va solo a los estados de §14 | Validador | Execution | Task 3 |
| EX-I14 | `REJECTED` no corrió: sin `startedAt`, sin evidencia y sin AgentReport (`agentDeclaredStatus` y `output` nulos) | Validador | Execution | Task 3 |
| EX-I15 | `SUCCEEDED` exige un AgentReport válido con `declaredStatus: COMPLETE`, y no afirma cumplimiento normativo. Sin un AgentReport válido, el intento que corrió es `FAILED` con `OUTPUT_INVALID` | Validador; documento | Execution | Task 3 |
| EX-I16 | Execution recibe del Host Adapter un AgentReport `{declaredStatus, artifact}`, y nunca la salida nativa. No busca en texto libre, no parsea Markdown, no interpreta los "Result Statuses", y el `artifact` no cambia ninguna decisión. El resultado guarda `declaredStatus` y la huella del `artifact`, nunca el texto | `validar_informe`; schema | Execution | Task 3 (contrato); Task 4 (adaptador) |
| EX-I17 | Execution no escribe el Plan: ningún estado de ejecución cambia el `status` del Plan ni de una WorkUnit | `bin/ejecucion/` no escribe; E-13 a E-17 de Task 2 siguen | Planning, y lo cumple Execution | Task 3 (estático); Task 4 |
| EX-I18 | La contabilidad no es estado de ejecución: Execution publica y nunca lee un ledger | `bin/ejecucion/` no importa `contabilidad`; E-42 | Observability | Task 3 (estático); Task 4 |
| EX-I19 | Execution no replanifica ni refuta: no crea ni modifica WorkUnits, aprobaciones, RefutationUnits ni veredictos; ante una condición de Planning, rechaza | Estático; admisión | Execution | Task 3 (estático); Task 4 |
| EX-I20 | Execution consume la decisión de la compuerta normativa y no la recalcula: `allowed` y `unresolved` admiten, y `blocked` da `NORMATIVE_GATE_BLOCKED`. No hay una autorización de Governance antes de ejecutar | Enum de `admission.normativeGate`; la lista de códigos | Normative Sources, y lo cumple Execution | Task 3 (enum y código); Task 4 |
| EX-I21 | La misma regla de admisión corre al pedir y al entregar, y el motor vuelve a derivar los campos derivados en vez de confiar en ellos | Admisión y motor | Execution | Task 4 |
| EX-I22 | Un rechazo al pedir no crea una Execution ni escribe nada | Admisión | Execution | Task 4 |
| EX-I23 | Nada del Host entra a la request; el resultado tiene un solo bloque del Host, opaco y opcional | Nombres de propiedades; `result.host` | Execution | Task 3 |
| EX-I24 | No hay secretos en el registro de una ejecución: request, resultado y `artifact` pasan por la redacción antes de escribirse, y el resultado no guarda prompts ni conversación | Schema sin texto libre del agente; el motor | Execution | Task 3 (schema); Task 4 (redacción) |
| EX-I25 | Lo que falta no es cero: los cambios declaran su estado, y una lista vacía solo dice "nada cambió" con `RESOLVED` | Validador | Execution | Task 3 |
| EX-I26 | Una dependencia se satisface solo con un `SUCCEEDED` de la unidad de la que se depende, en el mismo plan por su huella | Validador (forma); admisión | Execution | Task 3 (forma); Task 4 |
| EX-I27 | Task 3 no ejecuta: no hay motor, ni subcomando, ni subprocess nuevo, ni SDK de modelos, ni persistencia de ejecuciones | Estático | Execution | Task 3 |
| EX-I28 | La reserva de una `idempotencyKey` y la creación de su Execution son atómicas respecto de otras admisiones de la misma clave. El contrato fija que la atomicidad es necesaria; el mecanismo es de Task 4 (P13) | Dos admisiones concurrentes de la misma clave | Execution | Task 4 (EX-F01) |
| EX-I29 | Una sola autoridad para cada cosa: el tiempo del intento vive solo en el resultado (`startedAt`, `endedAt`), y la evidencia observa solo el árbol (`repoRevisionBefore`, `repoRevisionAfter`, `changes`), sin campos de tiempo | Schema | Execution | Task 3 |

## 30. Escenarios verificables

Ninguno lleva `· verificación: lectura`, porque el sujeto de ninguno es la corrida de un modelo
(ADR-0009). Todos pasan por la suite.

### El contrato

- **EX-E01** — `comun/schemas/execution-request.schema.json` y
  `comun/schemas/execution-result.schema.json` existen. Tienen `$id` `execution-request/1.0` y
  `execution-result/1.0`, y `schema_version` es un enum de un solo valor igual a su `$id`. La raíz
  está cerrada con `additionalProperties: false`, y los dos pasan `controlar_soporte`.
  · rojo visto: si
- **EX-E02** — En un proyecto temporal, `plan --propuesta` escribe un plan `READY_FOR_EXECUTION`.
  El request se arma desde ese plan: su WorkUnit copiada tal cual, sus dos huellas, su clave y una
  admisión que pasa. Ese request valida contra el schema, y `ejecucion.contrato.validar_request`
  devuelve `[]`. · rojo visto: si
- **EX-E03** — El request de EX-E02 deja de pasar `validar_request` en tres casos, y cada error
  nombra el campo:
  - le falta cualquiera de sus once campos obligatorios;
  - trae una clave de más en la raíz, en `plan` o en `admission`;
  - `workUnit` es una lista de dos unidades.

  · rojo visto: si
- **EX-E04** — Para cada uno de los cuatro estados terminales hay un resultado que, con el request
  de EX-E02, pasa `validar_resultado`. Un resultado con `status` `REQUESTED` o `RUNNING` no valida:
  `execution-result/1.0` describe solo resultados terminales. · rojo visto: si
- **EX-E05** — `$defs.error` de `execution-result` tiene exactamente `code` y `detail`, y está
  cerrado. `code` es uno de los 22 de §14, en ese orden. No validan un código fuera de la lista, un
  texto en lugar del objeto, ni un objeto sin `code`. Ningún código empieza con `TOOL_`.
  · rojo visto: si

### Identidad

- **EX-E06** — `executionId` cumple `^exe_[0-9a-f]{32}$` en el request y en el resultado. Un
  `session_id` de Claude Code, que es un UUID con guiones, no valida como `executionId`.
  · rojo visto: si
- **EX-E07** — Un request cuyo `plan.planId` no es `pln_` más su `taskKey` no pasa
  `validar_request`, y uno cuyo `taskKey` no tiene la forma de una TaskKey no valida.
  · rojo visto: si
- **EX-E08** — `contrato.huella(x)` es igual a `refutacion.huella(x)` para el plan de EX-E02 y para
  otros tres valores, y `bin/ejecucion/` no importa `refutacion`. Dos `plan --propuesta` con
  propuestas distintas dejan dos planes con el mismo `plan_id` y `plan_version: 1`, y con
  `planFingerprint` distintos. · rojo visto: si
- **EX-E09** — `idempotencyKey` es `clave_de_idempotencia(taskKey, planFingerprint, workUnit.id)`, y
  un request con otra clave no pasa. Dos requests de la misma WorkUnit del mismo plan, con
  `executionId` distintos, tienen la misma clave. La misma WorkUnit en un plan con otra huella da
  otra clave. · rojo visto: si
- **EX-E10** — Cambiar un campo de `workUnit` sin recalcular `workUnitFingerprint` hace fallar
  `validar_request`. · rojo visto: si
- **EX-E11** — `validar_resultado` exige que el `executionId` sea el del request y que
  `requestFingerprint` sea la huella del request. Cambiar un byte del request después de armar el
  resultado lo hace fallar. · rojo visto: si

### Lo que la admisión deja escrito

- **EX-E12** — Un request con `admission.planStatus` `CAPABILITY_RESOLUTION` o
  `WAITING_FOR_HUMAN_APPROVAL` no valida: es el plan que no está listo y la aprobación pendiente.
  · rojo visto: si
- **EX-E13** — Un request cuya `workUnit.status` es `BLOCKED` o `WAITING_FOR_HUMAN_APPROVAL` no
  valida. · rojo visto: si
- **EX-E14** — Un request no valida si `admission.agent.validation` es cualquiera de los nueve
  valores de `agentValidation` que no son `VALID` ni `VALID_WITH_PENDING_SKILLS`. Tampoco si
  `workUnit.assignedAgent` está vacío o no tiene la forma `^dev-[a-z0-9-]+$`.
  · rojo visto: si
- **EX-E15** — Un request con `workUnit.agentExists: false` y `admission.agent.validation: VALID`
  pasa `validar_request`: decide el registro al admitir, no el plan (EC-01).
  · rojo visto: si
- **EX-E16** — Un request con `admission.agent.type` `ORCHESTRATOR_AGENT` o `CRITIC_AGENT` no
  valida. · rojo visto: si
- **EX-E17** — Un request con `admission.agent.domain` distinto de `workUnit.domain` no pasa
  `validar_request`: es el dominio equivocado. · rojo visto: si
- **EX-E18** — Un request con `admission.capabilities` distinto de `ALL_AVAILABLE` no valida, y uno
  cuyas `workUnit.requiredCapabilities` traen `Read` o `Glob` tampoco: no tienen forma de
  capability. · rojo visto: si
- **EX-E19** — `admission.dependencies` nombra exactamente las `workUnit.dependencies`, una vez
  cada una, con un `executionId` válido y distinto del propio. `validar_request` falla si hay una
  de menos, una de más, una repetida o el propio id. · rojo visto: si
- **EX-E20** — `contrato.PRECEDENCIA` es la lista de 9.2, en ese orden. `validar_rechazo` acepta un
  error con cualquiera de esos códigos salvo `PLAN_CHANGED`, y rechaza los códigos de corrida y
  `CANCELLED`. · rojo visto: si

### La compuerta normativa y Governance

- **EX-E21** — Un request con `admission.normativeGate: allowed` valida. · rojo visto: si
- **EX-E22** — Un request con `admission.normativeGate: unresolved` valida: la compuerta no corta
  con `unresolved`, igual que en `plan`. · rojo visto: si
- **EX-E23** — Un request con `admission.normativeGate: blocked` no valida.
  `NORMATIVE_GATE_BLOCKED` es un código de rechazo al pedir y de `REJECTED`, y un `FAILED` con ese
  código no pasa `validar_resultado`. Ningún código de la lista empieza con `GOVERNANCE`.
  · rojo visto: si
- **EX-E24** — Ninguno de los dos schemas tiene una propiedad cuyo nombre contenga `approval`,
  `budget`, `timeout` o `permission`. · rojo visto: si

### Ciclo de vida

- **EX-E25** — `contrato.TRANSICIONES` tiene exactamente seis pares:
  - `REQUESTED→RUNNING`, `REQUESTED→REJECTED`, `REQUESTED→CANCELLED`;
  - `RUNNING→SUCCEEDED`, `RUNNING→FAILED`, `RUNNING→CANCELLED`.

  `transicion_valida` da `True` para esos seis y `False` para los otros treinta pares de estados.
  · rojo visto: si
- **EX-E26** — Camino feliz: pasa un `SUCCEEDED` con `startedAt`, un `endedAt` posterior,
  `agentDeclaredStatus: COMPLETE`, `output` y `evidence`: el resultado de un AgentReport válido con
  `declaredStatus: COMPLETE`. No pasa si le falta el `output`, si `agentDeclaredStatus` es nulo o
  no es `COMPLETE`, o si `startedAt` es nulo. · rojo visto: si
- **EX-E27** — Rechazo: un `REJECTED` con `startedAt`, `evidence`, `output` o `agentDeclaredStatus`
  no nulos no pasa. Con los cuatro nulos y un código de rechazo, pasa. · rojo visto: si
- **EX-E28** — Falla. No pasa un `FAILED` sin error, ni uno sin `startedAt`, ni uno con un código
  que no es de corrida, como `PLAN_NOT_READY`. Pasa con `HOST_INTERRUPTED`: la interrupción del
  Host es una falla, no una cancelación. Y el AgentReport decide así:
  - `AGENT_DECLARED_NOT_COMPLETE` pasa solo con `agentDeclaredStatus` `PARTIAL`, `BLOCKED` o
    `FAILED` y con `output` no nulo;
  - `OUTPUT_INVALID` pasa solo con `agentDeclaredStatus` y `output` nulos, porque no hubo un
    AgentReport válido;
  - un `FAILED` con un `agentDeclaredStatus` no nulo y cualquier otro código no pasa.

  · rojo visto: si
- **EX-E29** — Cancelación: un `CANCELLED` lleva el código `CANCELLED` y ningún otro, y
  `agentDeclaredStatus` y `output` nulos. Sin `startedAt` no tiene evidencia, y con `startedAt` la
  tiene. · rojo visto: si
- **EX-E30** — En el contrato, un terminal es inmutable: desde cada uno de los cuatro terminales,
  `transicion_valida` es `False` hacia los seis estados, y `contrato.TERMINALES` son exactamente
  esos cuatro. · rojo visto: si
- **EX-E31** — Un `SUCCEEDED` con error no pasa, ni un `FAILED`, `CANCELLED` o `REJECTED` con
  `error: null`. · rojo visto: si
- **EX-E32** — Execution no tiene `BLOCKED`. Ningún valor de `contrato.ESTADOS` ni del enum
  `status` del resultado es `BLOCKED`, `PENDING` ni `WAITING_FOR_HUMAN_APPROVAL`. `BLOCKED` aparece
  solo en `agentDeclaredStatus`. · rojo visto: si

### Evidencia

- **EX-E33** — Un resultado con `startedAt` exige `evidence` no nula, y `evidence.changes.state` es
  `RESOLVED`, `CHANGES_UNRESOLVED` o `CHANGES_UNATTRIBUTABLE`. Con un estado que no es `RESOLVED`,
  `files` tiene que estar vacío. Con `RESOLVED` y `files: []`, pasa. · rojo visto: si
- **EX-E33b** — Una sola autoridad para el tiempo. `evidence` es un objeto cerrado de exactamente
  `repoRevisionBefore`, `repoRevisionAfter` y `changes`, y ninguna propiedad adentro de `evidence`
  se llama `startedAt`, `endedAt` ni contiene `time` o `At`. Un resultado con un `startedAt`
  adentro de `evidence` no valida. Los únicos campos de tiempo del resultado son `startedAt` y
  `endedAt`, en su raíz. · rojo visto: si
- **EX-E34** — Un `SUCCEEDED` con `evidence: null` no pasa, y un `REJECTED` sin evidencia sí.
  · rojo visto: si
- **EX-E35** — El `artifact` del AgentReport no entra al resultado. `output` es un objeto cerrado de
  `path` y `fingerprint`, y ninguna propiedad de los dos schemas se llama `artifact`, `prompt`,
  `transcript`, `message`, `text` o `content`. Una ruta absoluta o con `..`, en `output` o en
  `evidence.changes.files`, no pasa `validar_resultado`. · rojo visto: si
- **EX-E36** — El contrato del AgentReport:
  - `validar_informe` acepta un objeto con exactamente `declaredStatus` y `artifact`, con
    `declaredStatus` en `COMPLETE`, `PARTIAL`, `BLOCKED` o `FAILED` y `artifact` de texto, vacío
    incluido;
  - lo rechaza sin `declaredStatus`, con otro valor (como `DONE` o `complete`), con `artifact` que
    no es texto, o con una clave de más;
  - `agentDeclaredStatus` del resultado acepta exactamente esos cuatro valores y `null`;
  - ningún valor propio de los "Result Statuses" de las skills, como `MISSING_CONTEXT` o
    `POLICY_BLOCKED`, aparece en los schemas ni en `contrato.py`.

  · rojo visto: si
- **EX-E36b** — Execution no interpreta el `artifact`. Un AgentReport sin `declaredStatus` cuyo
  `artifact` dice `status: COMPLETE`, o trae un bloque `agentResult` en Markdown, sigue siendo
  inválido para `validar_informe`. Un AgentReport con `declaredStatus: COMPLETE` y un `artifact`
  que dice `FAILED` es válido. Dos AgentReport con el mismo `declaredStatus` y `artifact` distintos
  dan el mismo resultado de validación. · rojo visto: si

### Contabilidad

- **EX-E37** — Ninguno de los dos schemas tiene una propiedad cuyo nombre contenga `usage`, `cost`,
  `token`, `eventId`, `ledger` o `accounting`. · rojo visto: si
- **EX-E38** — `bin/ejecucion/` no importa `contabilidad` ni nombra `.claude/runtime/accounting`, y
  E-40 y E-42 de `64_modelo_de_dominio.py` siguen en verde sin cambios. · rojo visto: si

### Independencia del Host

- **EX-E39** — En el request, ninguna propiedad fuera de `workUnit` tiene en su nombre `session`,
  `transcript`, `tool`, `provider`, `model` o `claude`. Ningún `enum` ni `pattern` de los dos
  schemas nombra a Claude Code. · rojo visto: si
- **EX-E40** — El único bloque del Host es `result.host`. Puede ser nulo, y `kind`, `sessionRef` y
  `runRef` son texto sin enum. Pasa un resultado con `host: null`, y también uno con
  `host.kind: "otro-host"`. · rojo visto: si

### Compatibilidad

- **EX-E41** — `comun/schemas/orchestration-plan.schema.json` y `bin/orquestacion/plan.py` son
  iguales byte a byte a los de `f9393cf`, y E-13 a E-17 de `64_modelo_de_dominio.py` siguen en
  verde sin cambios. · rojo visto: si
- **EX-E42** — `execution-accounting-event.schema.json`, `security-ledger-event.schema.json` y
  `refutation-unit.schema.json` son iguales byte a byte a los de `f9393cf`: los contratos que la
  ejecución va a alimentar no cambian. · rojo visto: si
- **EX-E43** — `validar_request` valida `workUnit` contra `workUnits.items` de
  `orchestration-plan.schema.json`: una WorkUnit sin `modelPolicy` no pasa, aunque el schema del
  request no la pida. El schema del request declara en `workUnit` exactamente los seis campos de
  10.3. · rojo visto: si

### El modelo canónico y el ADR

- **EX-E44** — `docs/dominio/modelo-canonico.md` declara diez contextos, Execution entre ellos, y ya
  no dice que Execution es un límite reservado. Los ocho conceptos de 8.2 tienen su fila y su
  bloque, con los campos de siempre, Contexto `Execution` y una de las doce clasificaciones.
  · rojo visto: si
- **EX-E45** — `execution-request.schema.json` figura en la Persistencia y contrato de
  ExecutionRequest, y `execution-result.schema.json` en la de ExecutionResult. El documento nombra
  los 48 schemas de `comun/schemas/`. · rojo visto: si
- **EX-E46** — `## Lo que no es lo mismo` tiene las seis desigualdades de 26.1 y conserva las de
  Task 2. · rojo visto: si
- **EX-E47** — `## El límite de la ejecución` dice tres cosas:
  - qué existe: el contrato, sin productor;
  - qué sigue sin existir: el motor, la admisión implementada, el almacenamiento, el reintento y el
    scheduler;
  - que siguen los dos invariantes de ADR-0013 §4.

  · rojo visto: si
- **EX-E48** — `docs/adr/0014-el-contrato-de-ejecucion.md` existe con `estado: aceptada`. Sus
  decisiones numeradas son las siete de 26.2, y dice que revisa el punto 4 de ADR-0013 sin tocar
  sus dos invariantes. · rojo visto: si

### Fuera de alcance

- **EX-E49** — No hay motor. `dev-harness.py` sigue con los once subcomandos de 0.30.0, sin
  `ejecutar`, `run` ni `execute`. Ningún módulo de `bin/` ni de `comun/` importa `threading`,
  `multiprocessing`, `asyncio`, `concurrent`, `sched` ni `queue`. · rojo visto: si
- **EX-E50** — No hay reintento. Los schemas no tienen propiedades cuyo nombre contenga `retry`,
  `attempt` o `backoff`, y `bin/ejecucion/` no nombra `maxRetries`, `allowEscalation`,
  `retryPolicy` ni `timeoutSeconds`. · rojo visto: si
- **EX-E51** — No hay llamadas a modelos. Ningún módulo de `bin/` ni de `comun/` importa
  `anthropic`, `openai`, `langchain`, `langgraph` ni `claude_agent_sdk`, y E-41 sigue en verde: todo
  `subprocess` lanza `git` o `markitdown`. · rojo visto: si
- **EX-E52** — No hay ejecución persistida:
  - `bin/ejecucion/contrato.py` no abre archivos para escribir, ni llama a `os.replace`,
    `os.makedirs` ni `subprocess`;
  - ningún módulo de `bin/` ni de `comun/` nombra `.claude/ejecuciones`;
  - ningún módulo de producción importa `ejecucion`: solo los tests.

  · rojo visto: si
- **EX-E53** — En un proyecto instalado en `%TEMP%` existen
  `.claude/harness/schemas/execution-request.schema.json`, `execution-result.schema.json` y
  `.claude/harness/bin/desarrollo/ejecucion/contrato.py`. `validar_request`, corrido desde el árbol
  instalado, encuentra sus schemas, y `.claude/ejecuciones/` no existe. · rojo visto: si

### Pendientes y compuerta

- **EX-E54** — `PENDIENTES-FH.md` tiene los cinco títulos de §33. · rojo visto: si
- **EX-E55** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta

**Cobertura del pedido:**

| Tema | Escenarios |
|---|---|
| Contrato | EX-E01 a EX-E05 |
| Identidad | EX-E06 a EX-E11 |
| Precondiciones | EX-E12 a EX-E20 |
| La compuerta normativa y Governance: permitido, pendiente, bloqueado, y sin aprobaciones | EX-E21 a EX-E24 |
| Ciclo de vida | EX-E25 a EX-E32 |
| Evidencia y AgentReport | EX-E33, EX-E33b, EX-E34 a EX-E36, EX-E36b |
| Contabilidad | EX-E37, EX-E38 |
| Host | EX-E39, EX-E40 |
| Compatibilidad | EX-E41 a EX-E43 |
| Modelo y ADR | EX-E44 a EX-E48 |
| Fuera de alcance | EX-E49 a EX-E53 |
| Pendientes y compuerta | EX-E54, EX-E55 |

Son **57**: EX-E01 a EX-E55, más EX-E33b y EX-E36b, que se agregaron en la revisión de la spec y
llevan letra por la regla de `write-a-spec`.

### Escenarios futuros, para la spec de Task 4

**No son escenarios de este cambio, y su verificación no lo cierra.** Necesitan un motor, y Task 3 no
construye ninguno. Quedan escritos para que Task 4 no tenga que decidir si son necesarios. Su spec
los copia con sus propios ids y su `rojo visto`.

| Id | Escenario | Invariante |
|---|---|---|
| EX-F01 | Dos admisiones de la misma WorkUnit del mismo plan corren a la vez. Exactamente una crea su Execution; la otra recibe `DUPLICATE_EXECUTION` y no deja nada escrito: ni request, ni marca, ni reserva | EX-I28 |
| EX-F02 | Una Execution `REQUESTED` se entrega y pasa a `RUNNING` sin chocar consigo misma. Si al entregarla existe **otra**, con otro `executionId` y la misma clave, abierta o `SUCCEEDED`, termina `REJECTED` con `DUPLICATE_EXECUTION` | EX-I10 |

Los demás invariantes marcados "Task 4" en §29 los convierte en escenarios la spec de Task 4
(§34.3).

## 31. La regla de alcance

#### D22. La regla de inclusión de Task 3

> **Un cambio entra en esta Task solo si hace falta para expresar, versionar o verificar el
> contrato entre Planning y Execution, y no hace que algo se ejecute, que algo se persista como
> ejecución, ni que cambie el comportamiento de un productor o un consumidor que ya existe.** También
> entra un cambio descriptivo que saque una contradicción entre el modelo canónico y el contrato
> nuevo. Todo lo demás se documenta, va a §33 si corresponde, y no se hace acá.

Es la D15 de Task 2, con una diferencia: Task 2 arreglaba artefactos que contradecían el modelo,
y Task 3 no arregla nada fuera de la frontera.

| Cambio propuesto | ¿Expresa, versiona o verifica la frontera, sin ejecutar ni cambiar a nadie? | Resultado |
|---|---|---|
| Los dos schemas | Expresan y versionan | **Entra** |
| `bin/ejecucion/contrato.py`, constantes y validadores puros | Verifica lo que el subconjunto no dice (11.3) | **Entra** |
| El modelo canónico y ADR-0014 | Expresan el contexto y sus decisiones | **Entra** |
| Adaptar E-03, E-05 y E-09 de Task 2 | Sin eso, la suite exige que Execution siga reservado | **Entra**, con su motivo |
| Los pendientes de §33 | Registran lo que no se hace | **Entra** |
| La admisión implementada: lee el plan, el registro, la compuerta y el almacenamiento | Es la primera pieza del motor | **No entra**: Task 4 |
| El almacenamiento, `.claude/ejecuciones/` | Persiste ejecuciones | **No entra**: Task 4 |
| Un subcomando `ejecutar` | Ejecuta | **No entra**: Task 4 |
| `executionId` en `CLAVES_DE_METADATA` | Cambia a Observability | **No entra**: Task 4 (D15) |
| Que `estado_de` mire `agentExists` | Cambia a Planning | **No entra** (D3) |
| Un agente para los tres dominios en blanco | Cambia a Planning o a Catalog | **No entra**: FH |
| Corregir el texto de los agentes (EC-12, EC-13) | Cambia la entrada de un modelo | **No entra**: pendiente |
| Que `docs/orquestacion.md` y `roster.huecos` dejen de decir que el disco decide | No es de la frontera | **No entra**: pendiente |
| Adaptar E-40 o E-41 | Nada de Task 3 los rompe | **No entra**: Task 4, si emite eventos o lanza al Host |

## 32. Fuera de alcance

Afuera, y cada uno con su razón:

- **El Execution Engine, la admisión implementada y el almacenamiento.** Son Task 4. Esta Task fija
  qué tienen que cumplir.
- **Un scheduler, un runtime de DAG, colas, workers, threads o procesos.** Son Task 5.
  Decidirlos sin un motor sería diseñar en el vacío.
- **Una política de reintento, backoff, checkpoints y reanudación.** No hay un motor que reintente,
  y `maxRetries` no tiene lector (EC-17).
- **LangGraph, LangChain, RAG, embeddings, vector stores, SDKs de modelos y la implementación de
  prompts.** HARNESS no llama a ningún modelo: lo hace el Host (MC, `### Host`).
- **La implementación de tools y de MCP.** Las tools son del Host (D13).
- **Detalles de Claude Code.** El contrato tiene que poder implementarse con otro Host (D16).
- **Una UI y un parser de intención.** No están en el pedido.
- **Cambiar `orchestration-plan/2.0`.** Ninguna contradicción lo exige (§27).
- **Cambiar el schema de contabilidad.** Lo que Task 4 necesita es código de Observability (D15).
- **Resolver aprobaciones.** Es Planning, y es FH (EC-05).
- **Renombrar `execution-accounting-event` y sus parientes.** Lo prohíbe D9 de Task 2 (EC-06).
- **Mover carpetas o renombrar módulos.** No hace falta.
- **VERSION, CHANGELOG y UPGRADE.** Son de `close-a-version`.

### Decisiones diferidas

| # | Qué se difiere | Por qué | Hasta | Qué queda estable mientras tanto |
|---|---|---|---|---|
| P1 | La política de reintento: automático o no, cuántos, backoff, qué códigos se pueden reintentar | Sin motor no hay evidencia de qué falla, ni cuánto | Task 5 o la que agregue reintento | Cada intento es otra Execution con la misma clave. Después de `FAILED`, `CANCELLED` o `REJECTED` se puede pedir otra vez (D19) |
| P2 | Scheduler, paralelismo y DAG | Es Task 5 | Task 5 | Las dependencias en la copia, `DEPENDENCY_NOT_SATISFIED` y una Execution abierta por clave (D20) |
| P3 | Cómo se resuelve una ModelTierApproval | Es de Planning, y hoy no hay cómo (EC-05) | La Task que lo construya | La request no lleva aprobaciones, y solo entran unidades `PENDING` (D12) |
| P4 | Proyectar la evidencia a `scope.json` y `checks.json`, y llenar el `executionId` del ledger de seguridad | Necesita un motor que produzca evidencia | La primera Task después de Task 4 que conecte Execution con Governance | `refutation-scope/1.0`, `refutation-checks/1.0` y `security-ledger-event/1.0` no cambian. La evidencia ya lleva las rutas (§18) |
| P5 | Qué eventos contables emite el motor, y la clave `metadata.executionId` | Es código de Observability, y necesita un motor | Task 4 | El schema contable no cambia. I-33 (D15) |
| P6 | El formato de la marca de entrega, la escritura atómica de cada archivo, la detección de un `RUNNING` huérfano y la extensión del informe | Son infraestructura del almacenamiento | Task 4 | La clave `<TaskKey>/<executionId>`, archivos que se escriben una vez, los dos schemas (D17) |
| P7 | El adaptador del Host: cómo se resuelven Agent → implementación y Capability → tool, cómo se lanza o se entrega una corrida, cómo se declara lo que el adaptador provee, y **cómo obtiene el `declaredStatus`** de la salida nativa de Claude Code | Es infraestructura y depende del Host | Task 4 | Fuera de `result.host`, que es opaco, el contrato no tiene campos del Host. Execution recibe un AgentReport `{declaredStatus, artifact}` y nunca la salida nativa. Sin AgentReport válido, `OUTPUT_INVALID`. `AGENT_UNAVAILABLE` y `CAPABILITY_UNAVAILABLE` (D8, D13) |
| P8 | Rechazar por un TaskContext desactualizado | Su hash no es determinista (C-17) | Después de arreglar C-17 | `taskContextRef` se registra y no se compara (D7) |
| P9 | Checkpoints y reanudación | No hay Task asignada | Sin fecha | Un `RUNNING` huérfano termina `FAILED` con `HOST_INTERRUPTED` (§13) |
| P10 | Ejecutar por lote o un plan entero | Es scheduling | Task 5 | Una request, una WorkUnit (D1) |
| P11 | El timeout por defecto y los límites por ejecución | Es configuración del motor | Task 4 | El código `TIMEOUT`. La request no lleva timeout |
| P12 | Reusar resultados entre versiones de un plan | Es optimización y tiene riesgo | Task 5 o posterior | Una dependencia se satisface solo dentro de la misma huella de plan (D20) |
| P13 | El mecanismo que hace atómica la reserva de una `idempotencyKey`: creación exclusiva, un lock, un índice u otro | Depende de cómo se guarde, que es P6 | Task 4 | Que la reserva sea atómica **no se difiere**: lo fija EX-I28. También quedan fijas la exclusión de sí misma al entregar (9.2, condición 14) y `DUPLICATE_EXECUTION` |

## 33. Deuda y hallazgos pendientes

Ninguno se arregla en esta Task. **Nuevos**: los anota la construcción en `PENDIENTES-FH.md`, en
inglés, con su evidencia (EX-E54). Estos son los títulos:

1. *An executing agent cannot reach the integration capabilities the plan counts as available*
   (EC-08).
2. *The agent registry gives two answers for the same orphan agent* (EC-10).
3. *A plan accepts an agent from another domain without a word* (EC-22).
4. *Agent prompts describe a result flow and an existence check that belong to someone else*
   (EC-12, EC-13).
5. *Two texts still say the disk decides whether an agent exists* (EC-21).

**Existentes, a los que esta spec agrega evidencia** (se citan; no se duplican):

| Pendiente | Qué agrega |
|---|---|
| FH, *Three domains route to a blank agent, in silence* | EC-02. La frontera los rechaza, y el arreglo de Planning sigue abierto |
| FH, *Six approvals exist and none can be resolved* | EC-05 |
| FH, *Plan rebuilds lose history, and four plan fields are never read* | EC-04, EC-17, EC-18 |
| FH, *Block 4 has thirteen event types and only one producer* | EC-07, y lo que Task 4 tiene que hacer (D15) |
| FH, *The task context hash is not deterministic* | EC-20 |
| FH, *Capabilities that skills name and no catalog declares* | EC-23 |
| FH, *The agent's invariants are enforced by nothing* | EC-24 |
| FH, *The canonical domain model closed with five loose ends* | Su cuarto punto, `READY_FOR_EXECUTION` con `agentExists: false`, queda **decidido** por ADR-0014 en la frontera. La construcción lo anota ahí, y el ítem sale del archivo al cerrar la versión |
| FH, *The Agent Registry is invalid in every installed project* | Nada nuevo: el estado de cada agente, que es lo que usa la admisión, no depende del `registryValid` global |

**Ownership.** Execution y `comun/schemas/` no tienen dueño declarado. Asignarlo es de Task 4, con
el código.

## 34. Plan de construcción

### 34.1 Qué se construye

| Artefacto | Qué hace | Escenarios |
|---|---|---|
| `comun/schemas/execution-request.schema.json` (nuevo) | §10 | EX-E01 a EX-E03, EX-E06, EX-E07, EX-E12 a EX-E18, EX-E21 a EX-E24, EX-E37, EX-E39, EX-E43 |
| `comun/schemas/execution-result.schema.json` (nuevo) | §11 y §14, con `$defs.error` | EX-E01, EX-E04, EX-E05, EX-E24, EX-E32 a EX-E37, EX-E33b, EX-E40 |
| `harnesses/desarrollo/bin/ejecucion/__init__.py` y `contrato.py` (nuevos) | §22. Constantes y validadores puros, `validar_informe` incluido. Sin I/O fuera de leer sus schemas y el del plan | EX-E02 a EX-E36, EX-E36b, EX-E38, EX-E50, EX-E52 |
| `docs/dominio/modelo-canonico.md` | §26.1 | EX-E44 a EX-E47 |
| `docs/adr/0014-el-contrato-de-ejecucion.md` (nuevo) | §26.2 | EX-E48 |
| `tests/casos/65_contrato_de_ejecucion.py` (nuevo) | Los escenarios, cada uno con su id en el título | EX-E01 a EX-E52, con EX-E33b y EX-E36b, y EX-E54 |
| `tests/casos/65-contrato-de-ejecucion-instalador.ps1` (nuevo) | La instalación en `%TEMP%` | EX-E53 |
| `tests/casos/64_modelo_de_dominio.py` | Tres adaptaciones, cada una con un comentario que nombra ADR-0014 y su escenario (abajo) | — |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Los cinco ítems nuevos de §33, y la nota en el ítem de los cinco cabos sueltos | EX-E54 |

Las tres adaptaciones de `64_modelo_de_dominio.py`:

- **E-03**: `NUEVE` pasa a diez contextos, con Execution, y se saca el assert de "límite reservado".
  Lo reemplaza EX-E44.
- **E-05**: de 46 a 48 schemas. S4 lee la tabla 3.2 de la spec de Task 2 **más** la de §22 de esta
  spec.
- **E-09**: los anclajes del límite pasan a los de EX-E47.

Si la suite muestra otro test de Task 2 que dependa del límite reservado, se adapta igual, con su
motivo, y se dice en el informe de construcción.

### 34.2 Lo que no se toca

- `orchestration-plan.schema.json`, `plan.py` y todo `bin/orquestacion/`;
- `bin/contabilidad/` y los schemas de contabilidad, seguridad y refutación;
- `dev-harness.py`;
- los hooks, los checks, los agentes y las skills. Las `SKILL.md` y `dev-refutador.md` son la huella
  de la caché de refutación;
- `install.ps1` y `manifest.json`: el instalador ya copia `bin/` y `comun/schemas/` enteros;
- `VERSION`, `CHANGELOG.md` y `UPGRADE.md`.

### 34.3 Lo que hereda Task 4

Task 4 lo recibe como contrato, no como sugerencia:

1. Implementar la ExecutionAdmission de 9.2: el mismo orden y los mismos códigos, al pedir y al
   entregar. Cada condición se lee de su dueño (D4).
2. Construir el almacenamiento de D17 y llamar a `validar_request` y `validar_resultado` antes de
   cada escritura. Hacer atómica la reserva de la `idempotencyKey` (EX-I28), con el mecanismo que
   elija (P13). Al entregar, excluir a la propia Execution de la comparación de duplicados
   (EX-I10). Los dos casos son EX-F01 y EX-F02.
3. Escribir un Host Adapter que resuelva el agente y las capacidades (D13), y que declare lo que
   provee.
4. Que ese Host Adapter, el de Claude Code, convierta la salida nativa del agente en un AgentReport
   `{declaredStatus, artifact}` que pase `validar_informe` (D8). **Cómo obtiene el
   `declaredStatus` lo decide Task 4.** Si no puede, el intento es `FAILED` con `OUTPUT_INVALID`.
   Execution recibe solo el AgentReport, redacta el `artifact` y lo guarda aparte.
5. Pasar por la redacción antes de escribir (EX-I24).
6. Si emite eventos contables: sumar `executionId` a `CLAVES_DE_METADATA` y adaptar E-40 con su
   decisión (D15).
7. Si lanza al Host por `subprocess`: adaptar E-41 y el invariante de MC, `### Host`, con su
   decisión escrita.
8. Corregir el texto de los agentes que dice que el resultado vuelve a `dev-orchestrator` (EC-13).
9. Convertir en escenarios los invariantes de §29 marcados "Task 4", empezando por EX-F01 y EX-F02.
10. Asignar dueño a Execution y a sus schemas.

### 34.4 El orden

1. Los schemas.
2. `contrato.py`.
3. `65_contrato_de_ejecucion.py`, con el rojo visto de cada escenario.
4. El modelo canónico y ADR-0014.
5. La adaptación de 64.
6. Los pendientes.
7. El instalador de prueba.
8. La compuerta entera en verde.

## 35. Cómo se verifica

**Todos los escenarios pasan por la suite.** Ninguno lleva `· verificación: lectura` (ADR-0009). La
verificación la hace `harness-spec-refuter`, que no construyó nada.

| Escenarios | Cómo |
|---|---|
| EX-E01, EX-E05, EX-E24, EX-E32, EX-E33b, EX-E35, EX-E37, EX-E39, EX-E40, EX-E43 | Se leen los dos schemas como JSON: claves, enums, patrones, `additionalProperties`. Se corre `controlar_soporte` |
| EX-E02, EX-E08 | Un proyecto temporal con integraciones simuladas, como `20_orquestacion.py` y `64_modelo_de_dominio.py`. `plan --propuesta` corre de verdad, y el request se arma en el test desde el plan escrito |
| EX-E03, EX-E04, EX-E06, EX-E07, EX-E09 a EX-E23, EX-E25 a EX-E31, EX-E33, EX-E34 | Se parte de un request y un resultado válidos y se rompe **una cosa por caso**. Se mira qué devuelven `validar_request`, `validar_resultado` o `validar_rechazo`, y que el error nombre el campo |
| EX-E36, EX-E36b | Se le pasan a `validar_informe` AgentReport válidos y rotos, de a una cosa por caso, incluidos `artifact` con `status: COMPLETE`, con `FAILED` y con un bloque `agentResult`. Se buscan los valores de las "Result Statuses" en los schemas y en `contrato.py` |
| EX-E38, EX-E49 a EX-E52 | Chequeos estáticos por AST y texto sobre `bin/` y `comun/`, como E-40 a E-42 |
| EX-E41, EX-E42 | Contra la línea de base: `git show f9393cf:<ruta>`, comparado byte a byte |
| EX-E44 a EX-E48 | Se parsea el modelo canónico y el ADR por secciones y campos, como hace `64_modelo_de_dominio.py` |
| EX-E53 | `65-contrato-de-ejecucion-instalador.ps1`: instalación en `%TEMP%`, y `validar_request` corre desde el árbol instalado |
| EX-E54 | Se buscan los cinco títulos en `PENDIENTES-FH.md` |
| EX-E55 | La compuerta entera |

**El rojo visto** se busca rompiendo a propósito lo que cuida cada escenario, sobre una copia del
repo en un temporal, como en `harness-unico` y `canonical-domain-model`. Por ejemplo:

- sumar `BLOCKED` al enum `status` del resultado;
- aflojar el patrón de `executionId`;
- sacar la coherencia de dominio de `validar_request`;
- dejar que `REJECTED` lleve `startedAt`;
- agregar `REQUESTED→SUCCEEDED` a `TRANSICIONES`;
- importar `refutacion` en `contrato.py`;
- que `validar_informe` saque el `declaredStatus` del `artifact` cuando falta;
- dejar que un `OUTPUT_INVALID` lleve `agentDeclaredStatus`;
- volver a poner `GOVERNANCE_DENIED` en la lista de códigos;
- agregar un `startedAt` adentro de `evidence`;
- agregar un `"timeout"` al request;
- poner `orchestration-plan/3.0` en el schema del plan.

Cada mutación queda registrada en una tabla en esta spec, como en Task 2.

### Registro del rojo visto

Se hizo el 07-10-2026, después de construir, sobre copias completas del repo con `.git` incluido, en
`%TEMP%`. El árbol versionado no se tocó. Para cada mutación:

1. se corrió el test del escenario sobre la copia y se lo vio en verde;
2. se aplicó la mutación;
3. se corrió el test en un proceso nuevo y se contaron solo las aserciones del propio escenario;
4. se restauró el archivo y se comprobó que quedara byte a byte igual.

Un rojo de rebote en otro escenario no se usó para atribuir. **Aserciones rojas** cuenta las del
escenario que la mutación puso en rojo.

| Escenario | Mutación que lo puso en rojo | Aserciones rojas | Restaurado |
|---|---|---|---|
| EX-E01 | el `$id` del request pasa a 1.1 | 1 | sí |
| EX-E02 | `validar_request` espera `pln-` en vez de `pln_` | 2 | sí |
| EX-E03 | `admission` deja de ser obligatorio | 3 | sí |
| EX-E04 | `RUNNING` entra al enum `status` del resultado | 2 | sí |
| EX-E05 | vuelve `GOVERNANCE_DENIED` a la lista de códigos | 1 | sí |
| EX-E06 | el `executionId` del request acepta un UUID de sesión | 3 | sí |
| EX-E07 | `validar_request` no compara `planId` con la `taskKey` | 2 | sí |
| EX-E08 | `huella` escapa el Unicode; y, en otra corrida, `contrato.py` importa `refutacion` | 2 y 1 | sí |
| EX-E09 | la clave deja afuera la huella del plan | 2 | sí |
| EX-E10 | no se compara `workUnitFingerprint` | 2 | sí |
| EX-E11 | no se compara `requestFingerprint` | 2 | sí |
| EX-E12 | `planStatus` acepta `WAITING_FOR_HUMAN_APPROVAL` | 2 | sí |
| EX-E13 | la WorkUnit puede estar `BLOCKED` | 2 | sí |
| EX-E14 | `agent.validation` acepta `AGENT_NOT_FOUND`; y, en otra corrida, `assignedAgent` acepta cualquier texto | 2 y 6 | sí |
| EX-E15 | el request exige el `agentExists: true` del plan | 1 | sí |
| EX-E16 | `agent.type` acepta `ORCHESTRATOR_AGENT` | 2 | sí |
| EX-E17 | se saca la igualdad de dominio | 2 | sí |
| EX-E18 | `capabilities` acepta `SOME_MISSING`; y, en otra corrida, `requiredCapabilities` sin forma de capability | 2 y 4 | sí |
| EX-E19 | no se marcan las dependencias repetidas | 2 | sí |
| EX-E20 | `PLAN_CHANGED` se acepta al pedir | 2 | sí |
| EX-E21 | `normativeGate` no acepta `allowed` | 1 | sí |
| EX-E22 | `normativeGate` no acepta `unresolved` | 1 | sí |
| EX-E23 | `NORMATIVE_GATE_BLOCKED` puede ir en `FAILED` | 2 | sí |
| EX-E24 | el request suma `timeoutSeconds` | 1 | sí |
| EX-E25 | se suma `REQUESTED → SUCCEEDED` | 4 | sí |
| EX-E26 | `SUCCEEDED` deja de exigir `startedAt` | 1 | sí |
| EX-E27 | `REJECTED` puede llevar `startedAt` | 1 | sí |
| EX-E28 | `OUTPUT_INVALID` puede llevar `agentDeclaredStatus` | 2 | sí |
| EX-E29 | `CANCELLED` acepta `HOST_INTERRUPTED` | 2 | sí |
| EX-E30 | sale una transición desde `SUCCEEDED` | 1 | sí |
| EX-E31 | no se compara `SUCCEEDED` con el error | 5 | sí |
| EX-E32 | `BLOCKED` entra como estado de Execution | 1 | sí |
| EX-E33 | un estado que no es `RESOLVED` puede llevar archivos | 4 | sí |
| EX-E33b | la evidencia suma un campo de tiempo, `observedAt` | 3 | sí |
| EX-E34 | con `startedAt` la evidencia puede ser `null` | 2 | sí |
| EX-E35 | una ruta con `..` pasa | 4 | sí |
| EX-E36 | `validar_informe` acepta `complete` en minúsculas | 2 | sí |
| EX-E36b | `validar_informe` saca el `declaredStatus` del `artifact` cuando falta: lee `status: X` del texto | 4 | sí |
| EX-E37 | el resultado suma `usage` | 1 | sí |
| EX-E38 | `contrato.py` importa `contabilidad` | 1 | sí |
| EX-E39 | el request suma `hostSessionId` | 1 | sí |
| EX-E40 | `host.kind` solo acepta `claude-code` | 2 | sí |
| EX-E41 | se toca el schema del plan 2.0 | 1 | sí |
| EX-E42 | se toca el schema del ledger de seguridad | 1 | sí |
| EX-E43 | `validar_request` no valida la WorkUnit contra el schema del plan | 2 | sí |
| EX-E44 | ExecutionAdmission pasa a Planning en su bloque | 1 | sí |
| EX-E45 | ExecutionRequest deja de nombrar su schema | 1 | sí |
| EX-E46 | se renombra una desigualdad nueva | 2 | sí |
| EX-E47 | se borra el scheduler de lo que no existe | 1 | sí |
| EX-E48 | el ADR queda `propuesta` | 1 | sí |
| EX-E49 | `contrato.py` importa `threading` | 1 | sí |
| EX-E50 | `contrato.py` nombra `maxRetries` | 1 | sí |
| EX-E51 | `contrato.py` importa `anthropic` | 1 | sí |
| EX-E52 | `contrato.py` crea `.claude/ejecuciones` | 2 | sí |
| EX-E53 | la copia no tiene `execution-result.schema.json`, y el instalador no lo instala: 11/15, y 15/15 al restaurarlo | 4 | sí |
| EX-E54 | se acorta un título de los cinco | 1 | sí |
| EX-E55 | no consta: es la compuerta misma | — | — |

📌 **La primera mutación de EX-E36b no contó.** Dejaba a `validar_informe` reventando con
`KeyError` en vez de aceptar el informe, así que el test fallaba por una excepción y no por la
aserción del escenario. Se rehízo para que de verdad sacara el estado del texto, y esa es la que
figura.

**Lo que ninguna suite ve:**

- **Que el relevamiento sea cierto.** La verdad de las secciones 4, 5 y 6, con sus números de línea,
  la juzga quien verifica, leyendo contra `0f8b725`. Un hallazgo ahí va a `verificacion.md`, en
  `Lo que la verificación encontró`.
- **Que el contrato alcance para Task 4.** Lo prueba Task 4. Si necesita algo que no está, la
  salida es una versión menor (§36).

## 36. Riesgos conocidos

- **El contrato se diseña antes que el motor.** Task 4 puede encontrar que falta un campo. Si es
  aditivo, sale como `1.1` (ADR-0013 §6). Si es un cambio mayor, esta spec falló en su criterio de
  calidad, y eso se dice.
- **Dos schemas y un módulo dormidos llegan a cada proyecto instalado**, como HarnessTool.
  Mitigaciones:
  - los fijan los tests;
  - el modelo canónico los marca sin productor;
  - Task 4 es la siguiente.
- **La copia de la WorkUnit duplica datos de Planning en cada request**, y el bloque `normative`
  puede ser grande. Se acepta porque el plan se pisa (EC-04) y la auditoría necesita saber qué se
  pidió.
- **La huella del plan cambia con cualquier reescritura.** Después de replanificar, todo se vuelve
  a ejecutar (D20). Es conservador a propósito.
- **Se confía en el motor.** La evidencia de que algo corrió es la palabra del motor. No hay
  atestación del Host.
- **Los cambios no se pueden atribuir en un árbol compartido.** `CHANGES_UNATTRIBUTABLE` lo dice,
  pero no lo evita. Correr en paralelo lo empeora (Task 5).
- **Un solo código por rechazo esconde las demás condiciones que fallaban.** Se eligió por
  determinismo, y `detail` puede nombrarlas.
- **`AGENT_DOMAIN_MISMATCH` puede rechazar planes que Planning considera válidos.** Es el caso de
  una propuesta con un agente de otro dominio. El hueco de Planning queda en §33.
- **Hoy la salida de los agentes es prosa.** El Host Adapter de Claude Code tiene que obtener de
  ella un `declaredStatus` válido. Si no puede, el intento es `FAILED` con `OUTPUT_INVALID`. Es
  honesto, y al principio puede ser frecuente. Cómo lo obtiene es de Task 4 (P7). El contrato no
  cambia por eso.
- **La atomicidad de la reserva está fijada, y el mecanismo no.** Un mecanismo mal elegido en Task
  4 rompe EX-I28 sin que ningún test de Task 3 lo vea. Mitigación: EX-F01 pasa a la spec de Task 4
  como escenario.
- **Se cambian tres asserts de tests verificados de Task 2.** El riesgo es aflojarlos. Mitigación:
  cada uno nombra ADR-0014 y el escenario que lo reemplaza, y conserva la forma del assert.
- **`execution-` nombra dos cosas en `comun/schemas/`.** Una es la contabilidad, y es un nombre
  heredado (EC-06). La otra es la ejecución. Mitigación: la descripción de cada schema nombra su
  contexto, y el vocabulario canónico tiene las dos filas.
- **"Execution" es el nombre del contexto y el del agregado.** Mitigación: el modelo canónico dice
  cuál en cada caso.
- **Los registros de ejecución quedan gitignoreados**, como todo `.claude/`. La auditoría vive
  mientras viva el directorio. Es el mismo riesgo que C-31 nombra para las aceptaciones de fuentes.
- **La evidencia salió de tres relevamientos.** Los hechos que sostienen decisiones se verificaron
  a mano (4.1), pero algún número de línea de las secciones 4 a 6 puede estar corrido.

## 37. Integración con HARNESS 0.31.0

**Fecha:** 08-10-2026 · **Base nueva:** 0.31.0 (`fdca5ce`, tag `v0.31.0`) · **Base de las secciones
1 a 36:** 0.30.0 (`f9393cf`)

Task 3 se especificó, se construyó y se verificó sobre 0.30.0: 57 sostenidos, en
[verificacion.md](verificacion.md). Antes de publicarse salió 0.31.0, que integra Flow Governance y
pasa el plan a `orchestration-plan/2.1`. Esta sección alinea el contrato con esa línea.

🔴 **Las secciones 1 a 36 quedan como se escribieron sobre 0.30.0, y son la historia.** Donde una de
ellas y esta sección dicen distinto, manda esta. Lo que esta sección cambia de las anteriores está
nombrado en 37.3 y en 37.6, frase por frase.

### 37.1 La nueva línea de base

| | 0.30.0, la construcción original | 0.31.0, la integración |
|---|---|---|
| Commit | `f9393cf`; las rutas con línea, de `0f8b725` | `fdca5ce` |
| Plan | `orchestration-plan/2.0`, tres estados | `orchestration-plan/2.1`, cuatro estados, con `BLOCKED` y `blockers` |
| Flujo de la tarea | No existía | TaskFlowState, FlowRequiredInput, HumanIntent, HumanDecisionRecord, SessionTaskBinding, SessionFlowNotice y la compuerta del flujo en PreToolUse |
| Schemas en `comun/schemas/` | 46, más los 2 de Task 3 | 52, más los 2 de Task 3 |
| Contextos | 9, más Execution | 9, más Execution |

Cómo se integró, sin rehacer nada:

1. el trabajo de Task 3 se guardó con `git stash -u`, y una copia completa quedó aparte;
2. `main` avanzó a `fdca5ce` con `git merge --ff-only`;
3. `git stash pop` devolvió Task 3. Tres archivos chocaron: `PENDIENTES-FH.md`,
   `63-harness-unico-instalador.ps1` y `64_modelo_de_dominio.py`. En los tres quedó lo de 0.31.0 más
   lo de Task 3. `modelo-canonico.md` se combinó solo.

### 37.2 Qué cambió en 0.31.0, y qué le hace a Task 3

El relevamiento cubre lo que pide el pedido: el schema del plan, `plan.py`, `bin/flujo/`,
`bin/estado_de_tarea/`, los cuatro módulos de `comun/hooks/lib/`, el modelo canónico, la nota de
0.31.0, la spec de la integración, `PENDIENTES-FH.md` y los tests de Flow Governance y de 2.1. Las
clases son:

- **A**, contradice Task 3;
- **B**, la extiende;
- **C**, no la afecta;
- **D**, reemplaza una premisa;
- **E**, es deuda futura, no contractual.

| # | Cambio de 0.31.0 | Dónde | Clase | Qué le hace a Task 3 |
|---|---|---|---|---|
| R-01 | El plan pasa a `orchestration-plan/2.1`, y `plan` escribe solo 2.1 | `orchestration-plan.schema.json`, `plan.py:35` | **A** | `plan.schemaVersion` de la request admitía `2.0` y `1.0`: ninguna admisión sobre un plan de 0.31.0 armaba una request válida |
| R-02 | `BLOCKED` es estado público del plan, y `estado_de` mira primero `flowPreconditions` | `plan.py:525-545` | **B** | `READY_FOR_EXECUTION` sigue siendo el único admisible. Se lee por los dos lados: lo escrito y `plan.estado_de` |
| R-03 | La unidad `BLOCKED` lleva `blockers`; la que no está bloqueada, no | schema, `plan.py:437` | **B** | Viajan solo dentro del snapshot de `workUnit`. Una `PENDING` con `blockers` es una foto incoherente |
| R-04 | El plan suma `flowPreconditions`, `capabilityStatus` y `knowledgeSources` | schema | **C** | Son del documento: entran en `planFingerprint` y no en la request |
| R-05 | Un agente no ruteable deja la unidad `BLOCKED` (`agents.routing`) y el plan `BLOCKED` | `plan.py:373-378`, `450` | **D** | EC-01 y EC-02 dejan de valer para un 2.1 recién escrito. D3 y D4 siguen: el registro cambia después de planificar |
| R-06 | El dominio del agente sigue sin compararse con el de la unidad | `plan.py:_armar_unidad` | **C** | EC-22 sigue en pie, y con ella D6 y `AGENT_DOMAIN_MISMATCH` |
| R-07 | Capacidad soportada y caída ≠ no soportada; `capacidades.estado` | `capacidades.py`, `plan.py:437-447` | **C** | `capacidades.disponibles` sigue (D4, D13). `CAPABILITY_UNAVAILABLE` coincide en nombre y sentido con el código de bloqueo de `plan.capabilityStatus` |
| R-08 | Una aprobación se resuelve con `flujo --approve` o `--alternative`, que replanifican | `estado_de_tarea/decisiones.py`, `plan.replanificar` | **D** | EC-05 y P3 («no hay cómo resolverla») dejan de valer. D12 sigue: la aprobación queda en el plan y cambia su huella |
| R-09 | El TaskFlowState derivado, y sus permisos (`delegationAllowed`) | `flujo/estado.py:374`, `556`, `591` | **B** | Precondición nueva de admisión: la tarea puede delegar **ahora**. El plan no sabe de una tarea cancelada, de un TaskContext que cambió ni de un checkout ajeno |
| R-10 | La compuerta del flujo en PreToolUse; `Agent` y `Task` son `WORKFLOW_ADVANCING` en `EXECUTION` | `comun/hooks/lib/flow_gate.py`, `tool_policy.py:1505` | **C** + **E** | Es otra compuerta: por llamada de herramienta, para la tarea de una sesión. No es la admisión ni la reemplaza. Deuda: lo que corra un Host Adapter dentro de una sesión pasa además por ella |
| R-11 | SessionTaskBinding: `session_id` → TaskKey | `comun/hooks/lib/task_binding.py` | **C** + **E** | La request no lleva `session_id`: la tarea va explícita en `taskKey`. Deuda: una sesión sin vínculo, en un proyecto con dos tareas con estado, es `SESSION_TASK_AMBIGUOUS` |
| R-12 | HumanIntent y HumanDecisionRecord | `comun/hooks/lib/human_intent.py`, `decisiones.py` | **C** | Sin `humanIntentId`: la auditoría va de la request, por `planFingerprint`, al plan y de ahí al HumanDecisionRecord. La HumanIntent es de un uso y se pisa |
| R-13 | La etapa `EXECUTION` y los estados `FAILED`, `CANCELLED` y `BLOCKED` del TaskFlowState | `task-flow-state.schema.json` | **C** | Homónimos. La etapa no es una Execution, y sus estados no son los de Execution |
| R-14 | `refutacion.huella` no cambió; el flujo guarda `planRef.planFingerprint` con ella | `refutacion.py`, `flujo/estado.py:365` | **C** | `planFingerprint` y `PLAN_CHANGED`, confirmados |
| R-15 | `aceptar_guardado` lee 2.1, 2.0 y 1.0, y rechaza un 2.1 con una unidad `BLOCKED` sin `blockers`. «Leer no es compilar» | `plan.py:595` | **B** | La regla #2 sigue con `aceptar_guardado`. Un 2.0 o un 1.0 se lee y no se admite: `PLAN_NOT_READY`, se replanifica |
| R-16 | Seis conceptos nuevos en Work Intake, Planning y Guardrails | `docs/dominio/modelo-canonico.md` | **B** | Siguen nueve contextos más Execution, que sigue décimo. Flow no es contexto. Planning → Execution suma el TaskFlowState |
| R-17 | La idea «Flow governance as a tenth bounded context» | `PENDIENTES-I.md` | **D** | El décimo ya es Execution (ADR-0014). La idea queda como contexto propio, y su costo suma ADR-0014 |
| R-18 | Pendiente: «el modelo canónico dice que solo los secretos bloquean» | `PENDIENTES-FH.md` | **C** | Task 3 no repite la frase ni la arregla: es de otro pendiente |
| R-19 | De 46 schemas a 52 (D7 de la integración) | `comun/schemas/` | **B** | Con los dos de Task 3 son 54. E-05 S4 lee 3.2, D7 y la sección 22 |
| R-20 | Las bases de harness-unico pasan a `ea2dff7`: 282 archivos | `63-harness-unico-instalador.ps1` | **B** | Con los cuatro de Task 3 son 286 |
| R-21 | E-13 a E-17, E-41 y la lista de subcomandos cambiaron a propósito | `64_modelo_de_dominio.py`, `dev-harness.py` | **B** | Lo que 65 comparaba contra `f9393cf` y 0.31.0 tocó pasa a `fdca5ce` |
| R-22 | `derivar` no conoce Executions: la etapa no pasa de `EXECUTION` a `VERIFICATION` | `flujo/estado.py` | **E** | El día que haya ejecuciones, alguien decide si el flujo las mira. Es de Task 4 o de Flow Governance |
| R-23 | `flow-required-inputs` no tiene etapa `EXECUTION` | `reglas/flow-required-inputs.json` | **E** | Si ejecutar pide un input del flujo, se declara ahí, no en la request |
| R-24 | Todo `PlanInvalido` sale con 2; `flujo` es un subcomando nuevo | `dev-harness.py` | **C** | Task 3 no agrega subcomando |
| R-25 | El flujo compara el `context_hash` del plan con el del TaskContext: `CONTEXT_STALE` | `flujo/estado.py:423-427` | **D** | P8 («rechazar por un TaskContext desactualizado», diferido por C-17) lo cumple ahora el flujo. Execution no compara: consume `delegationAllowed`, y D7 sigue |

**En números:** 1 A, 8 B, 10 C (dos con una parte E), 4 D y 2 E.

### 37.3 Las premisas que cambiaron

| Premisa de 0.30.0 | Dónde estaba | Qué la reemplaza |
|---|---|---|
| Un plan llega a `READY_FOR_EXECUTION` con una unidad cuyo agente no existe | §2, EC-01, EC-02, D3 | R-05: en 2.1 la unidad y el plan quedan `BLOCKED`. D3 sigue por el registro que cambia después de planificar |
| Ninguna ModelTierApproval se resuelve | EC-05, P3 | R-08: `flujo --approve` y `--alternative`, con una HumanIntent, replanifican |
| Rechazar por un TaskContext desactualizado espera a C-17 | P8 | R-25: lo hace el flujo, y la admisión lo consume como `DELEGATION_NOT_ALLOWED` |
| `orchestration-plan/2.0` no cambia | §27, D9, la decisión 7 de ADR-0014 | R-01: el plan es 2.1, por Flow Governance. Execution sigue sin cambiarlo (EX-G11) |
| La admisión consume Planning, Normative Sources y Catalog | 9.2, D4, D12 | R-09: Planning incluye ahora el TaskFlowState |
| Una lista cerrada de 22 y una precedencia de 14 | D11, 9.2, §14 | GD3: 23 y 15, con `DELEGATION_NOT_ALLOWED` |

### 37.4 Las decisiones de la integración

#### GD1. La frontera de admisión, con su dueño

La frontera queda así:

```text
HumanIntent ─(flujo --approve/--alternative)─> Plan 2.1 replanificado
                                                     │
Flow Governance: TaskFlowState vigente ─────────────┤ delegationAllowed
Planning: Plan 2.1, leído por aceptar_guardado ──────┤ READY por los dos lados, WorkUnit PENDING
Normative Sources: la compuerta normativa ──────────┤ allowed o unresolved
Catalog: registro de agentes y capacidades ─────────┤ ruteable, tipo, dominio, disponible
Execution: sus propias Execution ───────────────────┤ dependencias y duplicados
                                                     ▼
                                          ExecutionAdmission ──> ExecutionRequest ──> [Task 4]
```

Ni el TaskFlowState reemplaza al Plan, ni el Plan al TaskFlowState. **El Plan** dice qué WorkUnit
hay, de qué forma, con qué agente y si el documento está listo. **El TaskFlowState** dice si la
tarea, entera, puede avanzar ahora: si el TaskContext cambió, si el checkout es el de la tarea, si
una persona la canceló, si espera una decisión. EX-G05 lo prueba sobre un proyecto real: el plan
sigue `READY_FOR_EXECUTION` por los dos lados y el flujo queda `BLOCKED` por `CONTEXT_STALE`.

| Decisión | Dueño | Cómo la lee la admisión | Código si niega |
|---|---|---|---|
| El plan existe y se lee | Planning (Plan) | `plan.aceptar_guardado` | `PLAN_UNREADABLE` |
| El plan es 2.1 y está listo | Planning (Plan) | el `status` escrito y `plan.estado_de` | `PLAN_NOT_READY` |
| La tarea puede delegar | Planning (TaskFlowState) | `flujo/estado.permisos(...)["delegationAllowed"]` sobre el estado vigente | `DELEGATION_NOT_ALLOWED` |
| La compuerta normativa | Normative Sources | `auto_refresh.ensure_normative_knowledge_fresh` | `NORMATIVE_GATE_BLOCKED` |
| El agente y las capacidades | Catalog | `registro_agentes.resolver_ruteo`, `capacidades.disponibles` | `AGENT_*`, `CAPABILITY_UNAVAILABLE` |
| Dependencias y duplicados | Execution | sus propias Execution | `DEPENDENCY_NOT_SATISFIED`, `DUPLICATE_EXECUTION` |

**La compuerta del flujo de PreToolUse no está en la frontera.** Es una defensa del Host: decide por
llamada de herramienta, para la tarea de una sesión, con su propio vocabulario (`FLOW_*`). La
admisión decide por WorkUnit, con el de Execution. El dominio de Execution no depende de un hook: lee
la decisión de `flujo/estado.py`, que es de Planning, y no `comun/hooks/lib/flow_gate.py`. Las dos
leen la misma fuente, `puede_avanzar`, y eso es lo que las hace coherentes sin que una dependa de la
otra. EX-G06 lo fija.

Se descartó la frontera `Plan + TaskFlowState + Flow Gate + …`: poner la compuerta del flujo en la
admisión haría que Execution dependa de un hook, de una sesión y de su vínculo, y la request no
tiene sesión (D16).

#### GD2. Del TaskFlowState viaja un solo dato

La request suma `admission.flow`, con un único valor: `DELEGATION_ALLOWED`. Es la decisión que tomó
el flujo al admitir, del mismo modo que `planStatus` registra la del Plan y `normativeGate` la de la
compuerta normativa. Sigue el patrón de `capabilities: ALL_AVAILABLE`: lo que no se cumplió no
valida.

No viaja nada más del TaskFlowState: ni la etapa, ni `blockedOn`, ni `stale`, ni `resumeFrom`, ni una
huella del estado. El estado es derivado, cambia con cada reconciliación (`updatedAt`) y guarda
referencias que la request ya tiene por su cuenta, como `planFingerprint`. Copiarlo sería duplicar
Planning en cada request.

Se descartó también registrar «la compuerta del flujo dejó pasar»: eso es del Host y de una sesión.

#### GD3. Un código nuevo: `DELEGATION_NOT_ALLOWED`

Se evaluaron los tres candidatos del pedido y uno más:

| Candidato | Qué condición real | Dueño | Al pedir | Al entregar | Qué se decidió |
|---|---|---|---|---|---|
| `FLOW_BLOCKED` | El TaskFlowState no da `delegationAllowed`: bloqueada, esperando a una persona, cancelada, cerrada o desactualizada | Planning (TaskFlowState) | Sí | Sí, `REJECTED` | **Se adopta como `DELEGATION_NOT_ALLOWED`.** Ninguno de los 22 lo dice sin mentir: `PLAN_NOT_READY` diría que el plan no está listo, y lo está (EX-G05); `NORMATIVE_GATE_BLOCKED` es de Normative Sources y no se reusa; `WORK_UNIT_NOT_PENDING` habla de la unidad |
| `FLOW_STATE_UNRESOLVED` | El estado del flujo no se puede derivar o leer | Planning | Sí | Sí | **No.** Falla cerrado: sin estado vigente no hay `delegationAllowed`, y es `DELEGATION_NOT_ALLOWED` con el motivo en `detail`. Lo que hace quien pidió es lo mismo: `flujo <KEY> --status` |
| `TASK_BINDING_INVALID` | La sesión no sabe qué tarea trabaja | Work Intake | No | No | **No.** La admisión recibe la `taskKey` explícita y no resuelve sesiones. El vínculo es del Host y lo resuelve la compuerta del flujo con sus `SESSION_TASK_*`. Es deuda del Host Adapter (37.11) |
| `HUMAN_DECISION_PENDING` | Una aprobación o una decisión espera a una persona | Planning | Sí | Sí | **No.** Una aprobación pendiente deja el plan en `WAITING_FOR_HUMAN_APPROVAL`: `PLAN_NOT_READY`. Otra decisión pendiente deja el flujo sin `delegationAllowed`: `DELEGATION_NOT_ALLOWED` |

**El nombre sale de la fuente:** `permisos()` dice `delegationAllowed`, y el código dice que no. No
empieza con `FLOW_`, que es el vocabulario de la compuerta del hook (EX-G06).

**Va sexto, entre `PLAN_NOT_READY` y `WORK_UNIT_NOT_FOUND`.** Es de Planning, como las condiciones 2
a 7. Va después del plan porque, si el plan no está listo, el flujo tampoco deja avanzar, y el código
del plan es más preciso. Va antes de la WorkUnit porque es de la tarea entera.

**Dos nombres coinciden con otros contratos, y quieren decir lo mismo.** `PLAN_NOT_READY` es también
un código de bloqueo del TaskFlowState, y `CAPABILITY_UNAVAILABLE` uno de `plan.capabilityStatus`. Se
dejan así: en los dos casos el sentido es el mismo.

#### GD4. `READY_FOR_EXECUTION`, `PENDING`, `BLOCKED` y `blockers`

- **Sigue siendo cierto que solo se admite un plan `READY_FOR_EXECUTION`.** No apareció evidencia de
  otro estado que pueda cruzar: `BLOCKED`, `CAPABILITY_RESOLUTION` y `WAITING_FOR_HUMAN_APPROVAL`
  dicen que algo falta. Lo nuevo es cómo se lee: el `status` escrito **y** `plan.estado_de` sobre el
  mismo documento, como pide `derivar` («sin un plan listo por los dos lados no hay EXECUTION»).
- **`PENDING` sigue siendo necesaria, y `BLOCKED` nunca se admite**, ni del plan ni de la unidad.
  La request no cambia en eso: `workUnit.status` ya era `PENDING` y nada más.
- **`blockers` viaja solo dentro del snapshot de `workUnit`**, como cualquier otro campo de la
  WorkUnit: no hay un campo en la raíz ni en `admission`, y no es estado de Execution. Como una
  WorkUnit admitida está `PENDING`, y en 2.1 una que no está bloqueada no lleva `blockers`,
  `validar_request` rechaza un snapshot `PENDING` que los traiga (coherencia 8). El schema del plan
  no lo puede decir: el validador no tiene `if/then`, la misma razón de D3 de la integración de
  0.31.0.

#### GD5. `orchestration-plan/2.1`, y la versión de la request

- **`plan.schemaVersion` admite solo `orchestration-plan/2.1`.** La admisión lee el plan por la
  regla oficial, `plan.aceptar_guardado`, que lee 2.1, 2.0 y 1.0. Pero un 2.0 o un 1.0 no trae
  `flowPreconditions`, y `plan.estado_de` lo da `BLOCKED`: no puede estar listo por los dos lados. Se
  lee y no se admite (`PLAN_NOT_READY`), y se replanifica: «leer no es compilar», como en 0.31.0.
  Execution no migra nada.
- **`execution-request/1.0` y `execution-result/1.0` no suben de versión.** El cambio del enum quita
  dos valores y suma `admission.flow` obligatorio: si 1.0 ya se hubiera publicado, sería un cambio
  mayor. No se publicó. Task 3 no salió en ninguna versión, y no hay una instancia, un productor ni un
  proyecto instalado con el contrato anterior. D16 de `canonical-domain-model` rige desde la primera
  publicación: 1.0 sale con este contenido.

#### GD6. `PLAN_CHANGED`, `planFingerprint` y la clave de idempotencia

- **`planFingerprint` sigue siendo la identidad efectiva del documento,** y es la misma huella que el
  TaskFlowState guarda en `planRef.planFingerprint` (EX-G08). `flowPreconditions`,
  `capabilityStatus`, `knowledgeSources` y los `blockers` entran en ella, y se quiere así: la request
  fija el documento tal como se leyó. Si una decisión de Flow Governance replanifica después de
  admitir, al entregar la huella no coincide y la Execution termina `REJECTED` con `PLAN_CHANGED`. Es
  el mismo criterio conservador de D20.
- **La clave sigue siendo `huella([taskKey, planFingerprint, workUnit.id])`.** Un cambio del
  TaskFlowState sin cambio del plan no da otra clave: el flujo dice si se puede ejecutar ahora, no qué
  se ejecuta. Una decisión humana que no toca el plan (`CANCEL`, `CHOOSE`, `ANSWER`) tampoco. Una que
  sí lo toca (`APPROVE`, `USE_ALTERNATIVE`) replanifica, cambia la huella y da otra clave, porque es
  otro documento. **El flujo es precondición, no identidad.**

#### GD7. HumanIntent y SessionTaskBinding quedan afuera

- **`requestedBy` alcanza.** No hace falta un `humanIntentId`: la decisión que destrabó el paso ya
  queda auditada sin él. La request lleva `planFingerprint`, el plan con esa huella lleva la
  ModelTierApproval `APPROVED` y su `planHistory`, y el HumanDecisionRecord queda en
  `.claude/runtime/tasks/<KEY>/decisions/`. La HumanIntent, además, es de un solo uso y la próxima de
  la sesión la pisa: no es una referencia estable.
- **El SessionTaskBinding solo le dice al Host qué tarea trabaja una sesión.** No participa de la
  admisión: la tarea viene explícita en `taskKey`. `ExecutionId ≠ HostSession` sigue, y la sesión
  sigue fuera de la identidad (EX-G09).

#### GD8. D4, D6 y D13, confirmadas

- **D4.** Cada condición se sigue leyendo de su dueño. A la tabla de D4 se suma el TaskFlowState
  (`permisos`), y la del plan pasa a ser `aceptar_guardado` más `plan.estado_de`. Las funciones
  nombradas existen en `fdca5ce`: `capacidades.disponibles` (`capacidades.py:28`),
  `registro_agentes.resolver_ruteo` (`registro_agentes.py:370`) y
  `auto_refresh.ensure_normative_knowledge_fresh` (`auto_refresh.py:474`).
- **D6.** Sigue: `_armar_unidad` no compara el dominio del agente con el de la unidad.
- **D13.** Sigue: la disponibilidad es de Catalog, y lo que el agente puede tocar lo resuelve el Host
  Adapter, Capability → Tool. `capacidades.estado` suma la distinción soportada o caída, que es de
  Planning y no cambia la request. Los `blockers` de Planning no son errores de un intento: un
  `CAPABILITY_UNAVAILABLE` de Execution sale de la admisión o del adaptador, no de la unidad.

#### GD9. El modelo canónico: siguen diez contextos

Los contextos reales de 0.31.0 son los nueve de ADR-0013. Flow Governance agregó seis conceptos y
ningún contexto: SessionTaskBinding en Work Intake; FlowRequiredInput, TaskFlowState, HumanIntent y
HumanDecisionRecord en Planning; SessionFlowNotice en Guardrails. Con Execution son **diez**, y
Execution sigue siendo el décimo. El flujo no se hace contexto: 0.31.0 lo dejó como idea abierta, y
la idea ahora dice que sería el undécimo.

En el modelo cambian: la relación Planning → Execution, que suma el TaskFlowState; los bloques de
Execution, ExecutionRequest, ExecutionAdmission y ExecutionError; dos desigualdades que ya existían;
dos filas del vocabulario; y `## El límite de la ejecución`. No se agrega una desigualdad nueva:
«Execution ≠ la etapa `EXECUTION`» y «ExecutionAdmission ≠ la compuerta del flujo» van en el campo
**No es** de cada concepto.

#### GD10. ADR-0014 conserva sus siete decisiones

Ninguna se contradice: la 3 y la 7 se precisan. Se agrega la sección
`## Integración con HARNESS 0.31.0`, que dice qué cambia en su lectura. ADR-0013 no se toca.

### 37.5 La regla de admisión, integrada

Reemplaza la tabla de 9.2. El orden por capas no cambia, y la de Planning suma el TaskFlowState.

| # | Condición | Código si falla | Dueño del dato |
|---|---|---|---|
| 1 | La TaskKey, el id de la WorkUnit y quien pide tienen forma | `CONTRACT_INVALID` | Execution |
| 2 | El plan existe y lo acepta la regla de lectura única (`plan.aceptar_guardado`) | `PLAN_UNREADABLE` | Planning |
| 3 | `meta.task_key` del plan es la TaskKey pedida | `TASK_KEY_MISMATCH` | Planning |
| 4 | Solo al entregar: la huella del plan es la de la request | `PLAN_CHANGED` | Planning |
| 5 | El plan es `orchestration-plan/2.1` y está `READY_FOR_EXECUTION` por los dos lados: el `status` escrito y `plan.estado_de` | `PLAN_NOT_READY` | Planning |
| 6 | El TaskFlowState vigente de la tarea da `delegationAllowed` | `DELEGATION_NOT_ALLOWED` | Planning (TaskFlowState) |
| 7 | La WorkUnit está en el plan | `WORK_UNIT_NOT_FOUND` | Planning |
| 8 | La WorkUnit está `PENDING` | `WORK_UNIT_NOT_PENDING` | Planning |
| 9 | La compuerta normativa no dio `blocked` | `NORMATIVE_GATE_BLOCKED` | Normative Sources |
| 10 | El AgentRegistry deja rutear el `assignedAgent` **ahora** | `AGENT_UNAVAILABLE` | Catalog |
| 11 | El agente es `SPECIALIST_AGENT` o `INFRASTRUCTURE_AGENT` | `AGENT_NOT_EXECUTABLE` | Catalog |
| 12 | El dominio del agente en el registro es el de la WorkUnit | `AGENT_DOMAIN_MISMATCH` | Catalog |
| 13 | Cada `requiredCapability` está disponible **ahora**. Al entregar, además, la provee quien va a correr | `CAPABILITY_UNAVAILABLE` | Catalog (y el Host Adapter, D13) |
| 14 | Cada dependencia tiene una Execution `SUCCEEDED` del mismo plan, por su huella | `DEPENDENCY_NOT_SATISFIED` | Execution |
| 15 | No hay **otra** Execution, con un `executionId` distinto del actual, abierta o `SUCCEEDED`, con la misma `idempotencyKey` | `DUPLICATE_EXECUTION` | Execution |

Corre dos veces, igual que antes: al pedir y antes de entregar. Si una persona cancela la tarea, o el
TaskContext cambia, entre una y otra, la Execution termina `REJECTED` con `DELEGATION_NOT_ALLOWED`.

### 37.6 Lo que cambia en el contrato y en el repo

| Artefacto | Qué cambia |
|---|---|
| `comun/schemas/execution-request.schema.json` | `plan.schemaVersion` admite solo `orchestration-plan/2.1`; `admission.flow`, obligatorio, con `DELEGATION_ALLOWED` |
| `comun/schemas/execution-result.schema.json` | `DELEGATION_NOT_ALLOWED` entra sexto en el enum de `$defs.error.code` |
| `harnesses/desarrollo/bin/ejecucion/contrato.py` | `CODIGOS` y `PRECEDENCIA` con el código nuevo; `validar_request` suma la coherencia 8, sin `blockers` en la WorkUnit |
| `docs/dominio/modelo-canonico.md` | Lo de GD9 |
| `docs/adr/0014-el-contrato-de-ejecucion.md` | La sección de integración (GD10) |
| `Pendientes/Ideas-Harness/PENDIENTES-I.md` | La idea del flujo como contexto: sería el undécimo, y su costo suma ADR-0014 |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | La nota del cuarto punto de canonical-domain-model dice lo de R-05 |
| `tests/casos/65_contrato_de_ejecucion.py` | Los EX-Gnn, y lo de 37.8 |
| `tests/casos/64_modelo_de_dominio.py` | E-05 y E-05 S4 sobre la versión de 0.31.0: 54 schemas, y la tabla de la sección 22 al lado de 3.2 y D7 |
| `tests/casos/63-harness-unico-instalador.ps1` | E-15: 286, las 282 de `ea2dff7` y las cuatro del contrato |

**Lo que no se tocó**, y EX-G11 lo fija contra `fdca5ce`: Flow Governance, el plan 2.1, los hooks, la
política de herramientas, el vínculo de sesión, la intención humana, el registro de agentes, la
contabilidad, `install.ps1`, `manifest.json`, `dev-harness.py` y ADR-0013.

### 37.7 Lo que queda igual

D1, D2, D5, D7, D8, D9, D10, D12, D14 a D22 no cambian. D3, D4, D6, D11 y D13 se precisan en GD3 a
GD8, sin cambiar lo que deciden. Siguen iguales:

- el ciclo de vida: seis estados, cuatro terminales, seis transiciones, sin `BLOCKED`;
- el resultado entero, salvo un código más en la lista;
- el AgentReport, la ExecutionEvidence, el bloque del Host y la contabilidad;
- la identidad (`exe_` más 32 hexadecimales) y la clave de idempotencia;
- que Execution no escribe el Plan ni lee la contabilidad.

### 37.8 Los 57 escenarios, uno por uno

Ninguno se borra ni se renumera. Todos los que arman una request heredan el fixture nuevo de EX-E02:
un plan 2.1 con el repositorio de la tarea resuelto, y `admission.flow`. **En números:** 49 sin
cambio, 1 con el fixture actualizado, 6 con la expectativa actualizada y 1 reemplazado.

| Escenario | Impacto | Por qué |
|---|---|---|
| EX-E01 | sin cambio | Los dos schemas siguen en 1.0 (GD5) |
| EX-E02 | actualizar fixture | El plan solo queda listo con el repositorio de la tarea resuelto (`flowPreconditions`). El proyecto de prueba es `_proyecto_listo`, con `repositorio=True` |
| EX-E03 | sin cambio | La raíz sigue con once obligatorios; `flow` va adentro de `admission` |
| EX-E04 | sin cambio | |
| EX-E05 | actualizar expectativa | 23 códigos, por GD3 |
| EX-E06 | sin cambio | |
| EX-E07 | sin cambio | |
| EX-E08 | sin cambio | La huella sigue siendo la de `refutacion.huella`; los dos planes salen `BLOCKED`, y el escenario mira id, versión y huella |
| EX-E09 | sin cambio | GD6 confirma la clave |
| EX-E10 | sin cambio | |
| EX-E11 | sin cambio | |
| EX-E12 | actualizar expectativa | Suma `BLOCKED`, estado público del plan en 2.1 |
| EX-E13 | sin cambio | Una unidad `BLOCKED` o `WAITING` sigue sin validar (GD4) |
| EX-E14 | sin cambio | |
| EX-E15 | sin cambio | La premisa cambió (R-05), pero el registro puede cambiar después de planificar: decide al admitir (D3, D4) |
| EX-E16 | sin cambio | |
| EX-E17 | sin cambio | EC-22 sigue (D6) |
| EX-E18 | sin cambio | |
| EX-E19 | sin cambio | |
| EX-E20 | actualizar expectativa | Quince en la precedencia, por GD3 |
| EX-E21 | sin cambio | |
| EX-E22 | sin cambio | |
| EX-E23 | sin cambio | `NORMATIVE_GATE_BLOCKED` no se reusa |
| EX-E24 | sin cambio | `admission.flow` es una decisión de la admisión, no un permiso del Host |
| EX-E25 | sin cambio | |
| EX-E26 | sin cambio | |
| EX-E27 | sin cambio | |
| EX-E28 | sin cambio | |
| EX-E29 | sin cambio | |
| EX-E30 | sin cambio | |
| EX-E31 | sin cambio | |
| EX-E32 | sin cambio | |
| EX-E33 | sin cambio | |
| EX-E33b | sin cambio | |
| EX-E34 | sin cambio | |
| EX-E35 | sin cambio | |
| EX-E36 | sin cambio | |
| EX-E36b | sin cambio | |
| EX-E37 | sin cambio | |
| EX-E38 | sin cambio | E-40 y E-42 son iguales en `f9393cf` y en `fdca5ce`: la base `f9393cf` sigue valiendo |
| EX-E39 | sin cambio | `flow` no es del Host |
| EX-E40 | sin cambio | |
| EX-E41 | reemplazar | Afirmaba que el schema del plan 2.0 y `plan.py` eran los de `f9393cf`. 0.31.0 los cambió a propósito. Lo reemplaza: el schema 2.1 y `plan.py` son los de `fdca5ce`, y E-13 a E-17 siguen sin cambios respecto de `fdca5ce`. Lo que protegía, que Task 3 no cambia el plan, sigue: la decisión 7, precisada en GD5 |
| EX-E42 | sin cambio | 0.31.0 no tocó esos tres schemas |
| EX-E43 | sin cambio | La WorkUnit se valida contra `workUnits.items` de 2.1 |
| EX-E44 | sin cambio | Diez contextos (GD9) |
| EX-E45 | actualizar expectativa | 54 schemas, por R-19 |
| EX-E46 | sin cambio | Las seis desigualdades siguen; GD9 no suma otra |
| EX-E47 | sin cambio | |
| EX-E48 | sin cambio | Siete decisiones; la sección de integración no es una octava |
| EX-E49 | actualizar expectativa | Doce subcomandos contra `fdca5ce`: 0.31.0 sumó `flujo` |
| EX-E50 | sin cambio | |
| EX-E51 | actualizar expectativa | E-41 contra `fdca5ce`: 0.31.0 sumó `taskkill` desde `flujo/repositorio.py` |
| EX-E52 | sin cambio | |
| EX-E53 | sin cambio | |
| EX-E54 | sin cambio | |
| EX-E55 | sin cambio | La compuerta, corrida otra vez sobre `fdca5ce` |

### 37.9 Escenarios nuevos

Cubren la lista mínima del pedido. Ninguno lleva `· verificación: lectura`: todos pasan por la suite.

- **EX-G01** — El request armado desde un plan 2.1 `READY_FOR_EXECUTION` real, con su WorkUnit
  `PENDING`, valida y dice `orchestration-plan/2.1`; con `2.0` o `1.0` en `plan.schemaVersion` no
  valida. · rojo visto: sí
- **EX-G02** — Con un agente que el registro no rutea, `plan --propuesta` escribe un plan `BLOCKED` y
  la unidad `BLOCKED` con el blocker `agents.routing`. Ni ese `planStatus` ni el snapshot de esa
  unidad validan en un request. · rojo visto: sí
- **EX-G03** — Ni la raíz, ni `admission`, ni las propiedades que el request declara de `workUnit`
  tienen `blockers`. Una WorkUnit `PENDING` con `blockers`, vacíos o no, no pasa; sin ellos, sí.
  · rojo visto: sí
- **EX-G04** — `admission.flow` es obligatorio y su único valor es `DELEGATION_ALLOWED`: sin él, o con
  otro valor, el request no valida. · rojo visto: sí
- **EX-G05** — Flow Governance frena una tarea con el plan listo. Con el plan `READY_FOR_EXECUTION`
  por los dos lados, el TaskFlowState da `delegationAllowed` en `EXECUTION`. Si el TaskContext cambia
  después de planificar, el plan sigue listo por los dos lados y el flujo queda `BLOCKED` con
  `CONTEXT_STALE`, sin `delegationAllowed`. · rojo visto: sí
- **EX-G06** — Con la tarea vigente, la compuerta del flujo de PreToolUse deja pasar `Agent`; con la
  tarea frenada, lo niega con un código `FLOW_`. Ninguno de los 23 es un código de la compuerta, del
  vínculo de sesión, de la intención humana ni de la política de herramientas, y ninguno empieza con
  `FLOW_`. `bin/ejecucion/` no importa un hook ni el flujo, y no lee el estado del flujo.
  · rojo visto: sí
- **EX-G07** — `DELEGATION_NOT_ALLOWED` es el sexto de los 23 y va entre `PLAN_NOT_READY` y
  `WORK_UNIT_NOT_FOUND`, en una precedencia de quince. Va al pedir y en `REJECTED`, nunca en `FAILED`
  ni en `CANCELLED`. `NORMATIVE_GATE_BLOCKED` sigue siendo otro código. · rojo visto: sí
- **EX-G08** — `planFingerprint` es la huella que el TaskFlowState guarda en `planRef.planFingerprint`
  para ese plan. Cambia si cambia `flowPreconditions`, `capabilityStatus`, `knowledgeSources` o los
  `blockers` de una unidad, y con ella cambia la `idempotencyKey`. · rojo visto: sí
- **EX-G09** — La `idempotencyKey` sale de `taskKey`, `planFingerprint` y `workUnit.id`, y de nada
  más. Ninguna propiedad del request nombra una sesión o un vínculo. En el resultado, la única es
  `host.sessionRef`, que no es identidad. · rojo visto: sí
- **EX-G10** — Ninguna propiedad de los dos schemas nombra la etapa, los bloqueos, la vigencia, la
  reanudación, el estado del flujo, la intención humana, una interacción o una decisión. Del flujo,
  la única propiedad es `admission.flow`. · rojo visto: sí
- **EX-G11** — Lo de 0.31.0 no se toca. Son los de `fdca5ce`, sin archivos nuevos entre ellos:
  - los hooks, el flujo y las decisiones;
  - la orquestación, con `plan.py` y el registro de agentes;
  - la contabilidad, `dev-harness.py` y las reglas;
  - `install.ps1`, el manifiesto y ADR-0013;
  - los siete schemas de 0.31.0 que el contrato toca de cerca.

  · rojo visto: sí
- **EX-G12** — En el modelo canónico, el mapa tiene diez contextos y ninguno es el flujo. Los seis
  conceptos de Flow Governance siguen en sus contextos de 0.31.0. Planning → Execution nombra el
  TaskFlowState y `delegationAllowed`. ExecutionAdmission dice que no es la compuerta del flujo,
  Execution que no es la etapa `EXECUTION`, y ExecutionError cuenta veintitrés. La idea del flujo como
  contexto ya no dice décimo, y nombra ADR-0014. · rojo visto: sí
- **EX-G13** — ADR-0014 tiene `## Integración con HARNESS 0.31.0` y conserva sus siete decisiones;
  ADR-0013 es el de `fdca5ce`. La spec tiene esta sección con la tabla de 37.2, cada cambio de A a E,
  y los 57 escenarios de 37.8, cada uno una sola vez. · rojo visto: sí

| Pedido de la lista mínima | Escenario |
|---|---|
| plan 2.1 `READY` + WorkUnit `PENDING` | EX-G01 |
| plan `BLOCKED` no admitible | EX-G02, EX-E12 |
| WorkUnit `BLOCKED` no admitible | EX-G02, EX-E13 |
| `blockers` viajan solo dentro del snapshot | EX-G03 |
| Flow Governance bloqueando una Task | EX-G05 |
| Flow Gate permitiendo avanzar | EX-G06 |
| `planFingerprint` cambia si cambia un dato contractual de 2.1 | EX-G08 |
| SessionTaskBinding no entra en identidad de Execution | EX-G09 |
| HumanIntent no se copia al request | EX-G10 |
| Normative Gate y Flow Gate siguen siendo conceptos distintos | EX-G06, EX-G07 |

### 37.10 Invariantes nuevos

Siguen la numeración de la sección 29, después de EX-I29.

| Id | Invariante | Cómo se observa | Dueño | Se verifica en |
|---|---|---|---|---|
| EX-I30 | Solo se admite una WorkUnit `PENDING` de un plan `orchestration-plan/2.1` `READY_FOR_EXECUTION` por los dos lados: lo escrito y `plan.estado_de` | Enums de `plan.schemaVersion`, `admission.planStatus` y `workUnit.status`; la admisión | Planning, y lo cumple Execution | Task 3 (enums); Task 4 (lectura) |
| EX-I31 | La admisión exige que el TaskFlowState vigente dé `delegationAllowed`, y del flujo la request guarda solo esa decisión | `admission.flow`; nombres de propiedades; la admisión | Planning (TaskFlowState), y lo cumple Execution | Task 3 (contrato); Task 4 (lectura) |
| EX-I32 | La compuerta del flujo de PreToolUse y la ExecutionAdmission son compuertas distintas: ninguna reemplaza a la otra, y Execution no importa un hook ni usa sus códigos | Estático; las dos listas de códigos | Execution | Task 3 |
| EX-I33 | Los `blockers` de una WorkUnit viajan solo dentro de su snapshot, una WorkUnit admitida no los tiene, y no son estado de Execution | Validador; nombres de propiedades | Execution | Task 3 |
| EX-I34 | La identidad de una Execution no depende del flujo: ni el TaskFlowState, ni una HumanIntent, ni el SessionTaskBinding entran en la request ni en la `idempotencyKey` | Firma de `clave_de_idempotencia`; nombres de propiedades | Execution | Task 3 |

### 37.11 Deuda que queda, no contractual

Lo de clase **E**, y lo que la integración difiere a Task 4. Nada de esto cambia el contrato:

- **Cómo obtiene la admisión el TaskFlowState vigente** (P14, nueva): reconciliarlo
  (`persistencia.reconciliar`, que lee el `.env`) o leer el guardado con `vigencia_local`. Lo que no
  se difiere es que sin un estado vigente no hay `delegationAllowed`.
- **Una corrida en una sesión del Host pasa también por la compuerta del flujo** (R-10, R-11). El
  Host Adapter tiene que dejar la sesión vinculada a la `taskKey` de la request: si no, en un proyecto
  con dos tareas con estado, la compuerta niega con `SESSION_TASK_AMBIGUOUS`. Es parte de P7.
- **El flujo no conoce las Executions** (R-22): con ejecuciones reales, alguien decide si una
  `SUCCEEDED` mueve la etapa. Es de Task 4 o de Flow Governance.
- **`flow-required-inputs` no tiene etapa `EXECUTION`** (R-23): si ejecutar pide un input, se declara
  ahí.
- **`git remote -v` falla cerrado bajo carga** en la compuerta del flujo (nota de 0.31.0). Si la
  admisión de Task 4 deriva el estado con un límite corto, puede dar `DELEGATION_NOT_ALLOWED` de más.

### 37.12 Cómo se verifica, y el rojo visto

| Escenarios | Cómo |
|---|---|
| EX-G01, EX-G02, EX-G05, EX-G08 | Un proyecto temporal con el repositorio de la tarea resuelto. `plan --propuesta` corre de verdad, y el TaskFlowState lo deriva `flujo/estado.derivar` |
| EX-G06 | Lo mismo, y la compuerta del flujo se llama como biblioteca (`flow_gate.decidir`) con un evento `Agent`, como en `63_compuerta_del_flujo.py` |
| EX-G03, EX-G04, EX-G07, EX-G09, EX-G10 | Los schemas como JSON, y un request válido roto de a una cosa |
| EX-G11, EX-G13 | Contra `fdca5ce` con `git diff --quiet` y `git ls-files --others` |
| EX-G12, EX-G13 | El modelo canónico, el ADR, la spec y `PENDIENTES-I.md` leídos por secciones |

**El rojo visto** se registra en la tabla de abajo, con el mismo procedimiento de la sección 35.

| Escenario | Mutación que lo puso en rojo | Aserciones rojas | Restaurado |
|---|---|---|---|
| EX-G01 | `plan.schemaVersion` vuelve a aceptar `orchestration-plan/2.0` | 3 | sí |
| EX-G02 | `workUnit.status` acepta `BLOCKED` | 1 | sí |
| EX-G03 | `validar_request` deja de mirar los `blockers` de la WorkUnit | 4 | sí |
| EX-G04 | `admission.flow` acepta `BLOCKED` | 3 | sí |
| EX-G05 | el flujo deja de bloquear por `CONTEXT_STALE`. Es código de 0.31.0, y se mutó solo en la copia | 2 | sí |
| EX-G06 | `contrato.py` importa `flujo.estado` | 1 | sí |
| EX-G07 | `DELEGATION_NOT_ALLOWED` pasa después de `WORK_UNIT_NOT_FOUND` en la precedencia | 1 | sí |
| EX-G08 | `huella` deja afuera `flowPreconditions` | 2 | sí |
| EX-G09 | `clave_de_idempotencia` suma la sesión | 1 | sí |
| EX-G10 | `admission` suma `taskFlowStage` | 2 | sí |
| EX-G11 | se toca `comun/hooks/lib/flow_gate.py` | 1 | sí |
| EX-G12 | ExecutionAdmission deja de nombrar `flow_gate.py` en **No es** | 1 | sí |
| EX-G13 | se borra la fila de EX-E33b de 37.8 | 1 | sí |

Los ocho históricos que cambiaron en 37.8 (el fixture, la expectativa o el reemplazo) se volvieron
a ver en rojo sobre lo nuevo. Su marca de la sección 30 sigue en `sí`:

| Escenario | Mutación que lo puso en rojo | Aserciones rojas | Restaurado |
|---|---|---|---|
| EX-E02 | `validar_request` espera `pln-` en vez de `pln_`, con el fixture nuevo | 2 | sí |
| EX-E05 | `DELEGATION_NOT_ALLOWED` sale del enum de códigos | 1 | sí |
| EX-E12 | `planStatus` acepta `BLOCKED` | 2 | sí |
| EX-E20 | `DELEGATION_NOT_ALLOWED` sale de la precedencia | 1 | sí |
| EX-E41 | se toca `plan.py` | 1 | sí |
| EX-E45 | un schema de más en `comun/schemas/` | 2 | sí |
| EX-E49 | `dev-harness.py` suma el subcomando `ejecutar` | 3 | sí |
| EX-E51 | `contrato.py` lanza `ls` con `subprocess` | 1 | sí |

Se hizo el 08-10-2026 sobre tres copias completas del repo, con `.git`, en el temporal de la sesión,
con el procedimiento de la sección 35. Fueron 21 mutaciones, y las 21 quedaron restauradas byte a
byte. El árbol versionado no se tocó.