# Aceptación funcional — Flow Governance, Wave 4

**Fecha:** 01-10-2026 · **Baseline:** `VERSION 0.26.0`, HEAD `2b43a77c0a9b6fbf39a2268fde82be9d6a54ca9b`,
con la Wave 4 sin commitear · **Resultado:** PASS en todo lo que sigue

Esta aceptación no es la verificación de ADR-0006, que está en [verificacion.md](verificacion.md).
Junta tres clases de evidencia y no las mezcla:

- **Manual:** lo que observó la persona en una sesión real de Claude Code, sobre proyectos instalados
  con `install.ps1` en el Escritorio.
- **Automática:** la suite y `harness-spec-refuter`, sobre proyectos temporales.
- **Comprobación de quien construyó:** la CLI instalada corrida sin la UI. No es de la persona.

Todos los secretos son sintéticos. Ningún valor se copia acá.

## Resumen

| Qué | Resultado | Evidencia |
|---|---|---|
| Aprobación (manual) | PASS | manual |
| Configuración persistente (manual) | PASS | manual |
| Consistencia del estado | PASS | manual, automática y de quien construyó |
| Retomar revalida la fuente | PASS | manual y automática |
| `--status` y `--status --json` | PASS | automática y de quien construyó |
| Aprobación de un solo uso | PASS | manual y automática |
| La decisión es de la persona (Human Intent) | PASS | manual y automática, por separado |
| Secretos | PASS | manual y automática, por separado |
| Sin debilitar TLS | PASS | automática |
| La autoridad del flujo protegida (E-66) | PASS | automática |
| Sin cambio de VERSION | sí | — |
| Sin push | sí | — |
| Sin commit todavía | sí | — |

## Automática

| Suite | Resultado |
|---|---|
| Wave 4 — `64_interaccion_humana` | 376/376 |
| Wave 3 — `63_compuerta_del_flujo` | 487/487 |
| Wave 2 — `62_estado_del_flujo` | 177/177 |
| Wave 1 — `61_flujo_precondiciones` | 184/184 |
| Entorno primero, refutación atómica, Context Bar, Bloque 4, reporte de seguridad (60, 55, 53, 30, 48) | 307, 305, 464, 865, 566: todas verdes |
| Compuerta entera, `.\tests\Invoke-Tests.ps1` | 38455/38455, salida 0 |
| `harness-spec-refuter`, octava pasada | 71 sostenidos, 0 contradichos, 0 sin sustento, 0 leídos |

La compuerta entera la corrió el refutador sobre el árbol final; el árbol quedó con los mismos 15
archivos del cambio.

## Manual — aprobación

Proyecto `Desktop\harness-w4-aprobacion`, en una sesión real de Claude Code.

| Qué | Observado | Resultado |
|---|---|---|
| `WAITING_FOR_HUMAN_APPROVAL` visible | sí | PASS |
| `interactionId` visible | sí | PASS |
| `APPROVE` / `ALTERNATIVE` / `CANCEL` visibles | sí | PASS |
| El modelo no emitió por su cuenta la decisión | se negó a atribuírsela antes de invocar la CLI | PASS |
| El intent sale de `UserPromptSubmit` | la persona escribió la línea `HARNESS APPROVE …` | PASS |
| `APPROVE` sobre la misma sesión, tarea e interacción | aplicado | PASS |
| Después de aplicar | `EXECUTION` / `ACTIVE`, plan `READY_FOR_EXECUTION`, sin bloqueos | PASS |
| La misma aprobación otra vez | deny `HUMAN_INTENT_ALREADY_CONSUMED`; no se aplicó; siguió `EXECUTION` / `ACTIVE` | PASS |

📌 **En la prueba manual, el modelo se negó antes de llamar a la CLI.** Por eso `HUMAN_INTENT_REQUIRED`
no apareció en esa prueba, y acá no se dice que apareció. Que un tool call sin intent de la persona da
`HUMAN_INTENT_REQUIRED` es evidencia automática: E-12 (en la CLI y en PreToolUse) y E-30. Un intent de
otra tarea o de otra sesión tampoco sirve: E-16, E-17 y E-44.

## Manual — configuración persistente

Proyecto `Desktop\harness-w4-configuracion-2`. La primera vez, con
`Desktop\harness-w4-configuracion`, salieron los dos defectos que arregló el pre-acceptance fix (E-57 a
E-65); esta es la repetición.

| Paso | Observado | Resultado |
|---|---|---|
| `UserPromptSubmit` antes | `CONTEXT` / `BLOCKED`, `FLOW-CONTEXT-001` `jira.token` `JIRA_NOT_CONFIGURED`, `JIRA_TOKEN` como `PERSISTENT_CONFIG_INPUT` / `SECRET`, `vscode://file/…/.env:4:1`, `HARNESS RESUME ABC-123` | PASS |
| `flujo ABC-123 --status` | lo mismo: `CONTEXT`, `BLOCKED`, `FLOW-CONTEXT-001`, `jira.token`, `JIRA_NOT_CONFIGURED`, la misma `interactionId`, retoma en `CONTEXT / jira-token` | PASS |
| Edición | la persona editó solo el `.env` local, con un valor sintético que no pegó en el chat | — |
| `HARNESS RESUME ABC-123` | el hook vio que `JIRA_TOKEN` ya estaba cargado y que el estado guardado seguía siendo el anterior | PASS |
| `flujo ABC-123 --resume` | «Revalidando jira, la fuente de lo pendiente.»; Jira `CONNECTION_FAILED`, GitLab `NOT_CONFIGURED` | PASS |
| Después | `FLOW-CONTEXT-001` `jira.availability` `CONNECTION_FAILED`, retoma en `CONTEXT / jira-availability`; la tarea sigue `BLOCKED` | PASS |
| `reconfigurar jira` a mano | no hizo falta | PASS |

*Resolver un bloqueo no es dejar lista la tarea:* `CONNECTION_FAILED` es el bloqueo nuevo y real de un
host sintético.

## `--status` y `--status --json`

La aceptación final encontró que `--status --json` devolvía el estado recalculado: con el `.env`
editado y sin retomar, decía `NEW` sin bloqueos mientras la compuerta negaba. Ahora el texto, el JSON
y la compuerta leen la misma autoridad, `.claude/runtime/tasks/<KEY>/state.json`, por
`flujo.estado.leer` (E-67 a E-71; el contrato está en la spec).

Comprobación de quien construyó, sin la UI, sobre `Desktop\harness-w4-status-json` instalado con
`install.ps1`:

| Momento | `--status` | `--status --json` | `state.json` |
|---|---|---|---|
| `.env` corregido, sin `--resume` | `BLOCKED`, `FLOW-CONTEXT-001` `jira.token` `JIRA_NOT_CONFIGURED`, con la vista previa rotulada | lo mismo, y es el `state.json` tal cual | lo mismo |
| Después de `--resume` | `BLOCKED`, `FLOW-CONTEXT-001` `jira.availability` `CONNECTION_FAILED`, sin vista previa | lo mismo, y es el `state.json` tal cual | lo mismo |

El valor sintético no apareció en ninguna salida, en el runtime ni en el registro de capacidades.

## Secretos

- **Manual:** el valor no se pegó en el chat; no apareció en la salida de `--resume` que se vio en la
  prueba; el Harness no escribió el `.env`. La persona no inspeccionó `.claude\runtime` a mano.
- **Automática:** E-61 (stdout, runtime y registro), E-02, E-33, E-63 (sin lectura por consola) y
  E-62 (sin `verify=False`, `CERT_NONE` ni contexto sin verificar). Ningún valor filtrado.

## La autoridad del flujo protegida (E-66)

La sexta pasada del refutador encontró que `sort -uo`, `sort -o<ruta>`, `uniq <entrada> <salida>` y
`find -fprint0` escribían aunque se clasificaban como lectura. Con eso, una cancelación de la persona
terminó en aprobación, y se plantó un `core.fsmonitor` en `.git/config`.

- **Test primero:** PASS. Fallaron 40 aserciones antes del arreglo.
- **La forja del intent:** cerrada.
- **El `core.fsmonitor` por `.git/config`:** cerrado.
- **Códigos:** `FLOW_AUTHORITY_PROTECTED` y `FLOW_HUMAN_DECISION_PENDING` siguen igual.
- **Residual:** si un programa de la lista de lectura tiene otra forma de escribir que no está
  modelada, sigue siendo un riesgo de esa lista. No se buscaron más variantes.

## Lo que cambia de la Wave 2

`flujo --status --json` sin estado guardado ya no devuelve el estado derivado, que es lo que usaba la
fila F de la aceptación de la Wave 2. Ahora sale con 2 y `TASK_FLOW_STATE_MISSING`.

La reconstrucción del estado no cambió: `reconciliar` en un proceso nuevo lo vuelve a escribir igual.
Lo que cambió es que `--status --json` ya no la muestra antes de que se aplique.
