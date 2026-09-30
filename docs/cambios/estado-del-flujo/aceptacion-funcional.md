# Aceptación funcional — Flow Governance, Wave 2

**Fecha:** 29-09-2026 · **Baseline:** `VERSION 0.26.0`, HEAD `4a18ddc23a379ff6a9ec09feb0d8af0aa23004f3`,
con la Wave 2 sin commitear · **Resultado:** 23/23 escenarios funcionales, suite 37582/37582

Esta aceptación no es la verificación de ADR-0006, que está en [verificacion.md](verificacion.md).
Es una corrida de punta a punta sobre proyectos temporales:

- un `git init` con remotos que no existen;
- TaskContexts con su hash calculado;
- `.env` con secretos sintéticos, que acá se escriben `<synthetic-secret>`.

A–S y V corren con la CLI real (`contexto`, `plan`, `refute`, `flujo --status`) en procesos nuevos.
P usa el Jira falso de `tests/casos/19_contexto.py`. Ninguna integración sale a la red.

| # | Escenario | Esperado | Obtenido | Resultado |
|---|---|---|---|---|
| A | Dos tareas independientes | dos `state.json` con sus refs; tocar una no cambia la otra | `ABC-123` y `ABC-456` con su `taskKey`, su `planRef` y su `contextHash`; replanificar `ABC-456` dejó el estado de `ABC-123` byte a byte igual | PASS |
| B | No hay singleton | nunca `.claude/runtime/task-state.json` | ninguno en 21 proyectos, después de `contexto`, `plan`, `refute` y `flujo --status` | PASS |
| C | `active-task` es un puntero | solo `schema_version` y `taskKey` | esas dos claves; pasa a la última tarea tocada (`ABC-456`, después `ABC-123`) | PASS |
| D | Repositorio de otro proyecto | `PLANNING` / `BLOCKED` con `REPOSITORY_MISMATCH`; permisos de avance en `false` | eso, con `resumeFrom {PLANNING, repository-match}` y los cinco permisos en `false` | PASS |
| E | Un secreto pendiente | `kind`, `inputId`, `target`, `key`, `sensitivity`; sin valor ni posición | `{PERSISTENT_CONFIG_INPUT, jira.token, .env, JIRA_TOKEN, SECRET}`; en `state.json` no hay valor, línea, columna, enlace, `password` ni `credential`; la posición y el enlace aparecen recién en `flujo --status` | PASS |
| F | Reconstrucción | borrado `state.json`, el mismo estado lógico | `flujo --status --json` da el mismo estado y `reconciliar` en un proceso nuevo lo vuelve a escribir igual, en los nueve campos | PASS |
| G | Sin artefactos | `CONTEXT`, nunca disponible | `CONTEXT` / `NEW` con Jira configurado; `CONTEXT` / `BLOCKED` sin `.env`; permisos en `false`; `flujo --status` no crea el estado | PASS |
| H | Plan escrito `BLOCKED` | nunca `EXECUTION` | con el remoto corregido y `flowPreconditions` editado a `READY`: `PLANNING` / `BLOCKED` con `PLAN_NOT_READY`, lo mismo que dice `refute --compile` | PASS |
| I | Plan `READY_FOR_EXECUTION` | `EXECUTION` / `ACTIVE` | eso, sin bloqueos y con `implementationAllowed: true` | PASS |
| J | TaskContext cambiado | `TASK_CONTEXT_STALE`, sin avance | vigencia y `stale` con `TASK_CONTEXT_STALE`, bloqueo `CONTEXT_STALE`, permisos en `false` | PASS |
| K | Plan cambiado | `PLAN_STALE` | vigencia `PLAN_STALE`; replanificar por la CLI cambia el `planFingerprint` guardado | PASS |
| L | Remoto cambiado | `REPOSITORY_STATE_STALE` | vigencia `REPOSITORY_STATE_STALE` y bloqueo actual `REPOSITORY_MISMATCH` | PASS |
| M | Refutación de otro plan | `REFUTATION_STATE_STALE` y `REFUTATION_PLAN_STALE` | replanificado: `REFUTATION` / `BLOCKED` con los dos | PASS |
| N | `state.json` corrupto | `TASK_FLOW_STATE_INVALID`, nunca avanzar | `leer` da `TASK_FLOW_STATE_INVALID`, `flujo --status` lo muestra y los permisos quedan en `false` | PASS |
| O | Escritura atómica | el anterior queda entero | con un fallo antes del reemplazo, el anterior queda igual, válido y sin temporales | PASS |
| P | `contexto` reconcilia | el mismo comando deja el estado | `state.json` con el `contextHash` del TaskContext recién escrito | PASS |
| Q | `plan` reconcilia | `BLOCKED` si el plan lo está; ejecución si está listo | D quedó `PLANNING` / `BLOCKED` e I `EXECUTION` / `ACTIVE`, los dos escritos por `plan` | PASS |
| R | Compuerta de refutación que falla | salida distinta de 0, `PLAN_NOT_READY`, sin `run.json`, estado con el bloqueo | salida 2, `PLAN_NOT_READY`, sin `run.json`, estado `BLOCKED` con `AGENT_NOT_ROUTABLE` | PASS |
| S | Refutación que pasa | `run.json` válido y estado al día | `run.json` válido contra `refutation-run/1.0`; `refutationRef` con su `planFingerprint` | PASS |
| T | `flujo --status` es local | sin Jira, GitLab, HTTP ni modelo | ninguna llamada, con `socket`, `create_connection` e `integraciones.http` interceptados; `flujo/estado` y `persistencia` no importan nada de red | PASS |
| U | El Bloque 4 no gobierna | eventos del libro no cambian el estado | con eventos válidos de cierre en el libro, `BLOCKED` e `INCOMPLETE` quedan iguales | PASS |
| V | Reinicio | un proceso nuevo ve lo mismo | dos subprocesos ven el mismo bloqueo, el mismo `resumeFrom` y la misma interacción pendiente que el guardado | PASS |
| W | Permisos no guardados | ningún `state.json` los tiene | ninguno de 20; `permisos()` da `false` para lo bloqueado y deja implementar en `EXECUTION` | PASS |

## Lo que la corrida registró aparte

- **Un secreto presente no puede estar pendiente.** En E, `JIRA_TOKEN` lleva un placeholder y el
  secreto sintético va en otra variable del `.env`. En la variante con `JIRA_TOKEN` cargado, lo
  pendiente pasa a ser `jira.user`, y el secreto tampoco aparece en ninguna salida.
- **`http` y `ssl` están cargados en el proceso de `flujo --status`**, pero no los pide el flujo:
  `dev-harness.py` importa los adaptadores de Jira y GitLab para todos los comandos desde antes de
  la Wave 1. En un proceso limpio, `flujo/estado` y `estado_de_tarea/persistencia` no cargan
  ninguno.
- **La primera corrida dio 22/23 por dos errores del script, no del producto.** En T se contaba un
  módulo cargado como si fuera una llamada, y en Q una variable del escenario D estaba pisada por la
  de E. Se corrigieron los dos y se volvió a correr entera.

## Lo que se controló alrededor

- **Fugas: ninguna.** Los secretos sintéticos se buscaron en todo el stdout y el stderr, en los
  `state.json`, en `active-task.json` y en todos los archivos de los proyectos temporales, salvo los
  `.env` y `.git`.
- **Cambios inesperados: ninguno.** Antes y después dieron igual el `git status`, el hash de
  `git diff` (`a30c8ed0…`) y la huella de los archivos sin trackear. `VERSION` siguió en `0.26.0`.
- **Regresión.** `.\tests\Invoke-Tests.ps1`: 37582/37582 (488 PowerShell + 37094 Python), salida 0.
  Entre los archivos de la suite:

  | Archivo | Resultado |
  |---|---|
  | `62_estado_del_flujo` | 173/173 |
  | `61_flujo_precondiciones` | 183/183 |
  | `55_refutacion_atomica` | 305/305 |
  | `53_context_bar` | 465/465 |
  | `60_entorno_primero` | 307/307 |
  | `19_contexto` | 165/165 |
  | `30_b4_contabilidad` | 861/861 |
  | `48_reporte_de_seguridad` | 566/566 |

## Input obligatorio para Wave 3

`active-task.json` representa **la última tarea reconciliada por cualquier comando del proyecto**.
Se confirmó con `ABC-123` y `ABC-456`: trabajar una lo mueve a esa, y volver a la otra lo mueve de
nuevo.

No representa:

- una sesión de Claude;
- una elección explícita;
- ownership;
- un lock;
- una asociación entre sesión y tarea.

**Riesgo:** dos sesiones de Claude Code sobre el mismo proyecto pueden pisarse el puntero. Un hook que
decida con él puede aplicar los bloqueos de otra tarea. Eso lleva a dos errores:

- **falso negativo:** deja avanzar una tarea bloqueada porque mira una que está lista;
- **falso positivo:** frena una tarea sana.

El estado de cada tarea no corre ese riesgo: vive en su propio archivo.

Por lo tanto la Wave 3 tiene que cumplir:

```text
hook decision
!=
active-task.json alone
```

La tarea sobre la que decide un hook tiene que salir de algo que la sesión declara: la clave en el
pedido, o el argumento del comando que dispara la compuerta. El puntero sirve para mostrar, no
para decidir. Si hay más de una tarea con estado en el proyecto y la sesión no dijo cuál trabaja,
la tarea queda sin resolver y las operaciones de avance se niegan.
