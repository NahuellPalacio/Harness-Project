# Aceptación funcional — Flow Governance, Wave 3

**Fecha:** 30-09-2026 · **Baseline:** `VERSION 0.26.0`, HEAD `32febd758697a8407574d5d64736a6ec58058136`,
con la Wave 3 sin commitear · **Resultado:** aceptada. 31/31 escenarios automatizados, corrida real
de Claude Code y aceptación manual en PASS.

Esta aceptación no es la verificación de ADR-0006, que está en [verificacion.md](verificacion.md).
Se hizo en tres partes:

1. Una pre-aceptación adversarial, que encontró dos caminos reales sin cubrir.
2. Una corrida de punta a punta con procesos nuevos por hook, sobre proyectos temporales con
   remotos que no existen y secretos sintéticos.
3. La prueba del runtime real de Claude Code: automatizada en modo headless y manual en la UI.

## Pre-aceptación: dos bypasses encontrados y corregidos

| Bypass | Qué pasaba | Arreglo | Escenario |
|---|---|---|---|
| La delegación esquivaba la compuerta | `Agent` (y `Task`, su nombre anterior) estaba clasificada como avance, pero el matcher registrado de PreToolUse no la alcanzaba: con la tarea `BLOCKED`, un subagente arrancaba igual | El matcher suma `^Agent$\|^Task$`, anclados para no alcanzar a `TaskCreate` y parecidos. `03-instalador.ps1` fija el matcher nuevo por evento | E-64 |
| Un remoto cambiado sin reconciliar dejaba mutar | `repositoryRef` salía del estado guardado, que seguía diciendo `MATCHED` | `vigencia_local` recalcula los remotos del checkout con `repositorio.remotos`, que corre solo `git remote -v`: local, sin red, sin `.env`. Un remoto distinto da deny `REPOSITORY_STATE_STALE` | E-63 |

Los dos se escribieron primero como test y se vieron en rojo.

## Aceptación automatizada: 31/31

| # | Escenario | Resultado |
|---|---|---|
| A | «Seguimos con ABC-123» vincula `session-A`, con cinco campos y sin el prompt ni el secreto del prompt | PASS |
| B | `session-B` → ABC-456, independiente de A | PASS |
| C | Con el puntero en ABC-456, A evalúa ABC-123 (deny); con el puntero en ABC-123, B evalúa ABC-456 (pasa) | PASS |
| D, E, F | Sesión sin binding + `Write`, `Edit`, `Agent`: deny `SESSION_TASK_AMBIGUOUS` | PASS |
| G, H, I | `BLOCKED` + `Write`, `Edit`, `Agent`: deny `FLOW_HARD_BLOCKER` | PASS |
| J | `refute --compile` deny; `plan` pasa como revalidación de la etapa bloqueada | PASS |
| K | `flujo --status`: `FLOW_RECOVERY`, pasa | PASS |
| L | `git status`: `READ_ONLY`, pasa | PASS |
| M | Secreto de confianza alta con la tarea bloqueada: deny del secreto, una emisión | PASS |
| N | Secreto ambiguo con el flujo que pasa: ask | PASS |
| O | Secreto ambiguo con el flujo que niega: deny, con el aviso del secreto al lado, una emisión | PASS |
| P | `jira.token`: `JIRA_TOKEN`, el enlace `vscode://file/…/.env:4:1`, el fallback, el placeholder y «No pegues»; ningún valor | PASS |
| Q | El segundo prompt, con el mismo bloqueo: una línea | PASS |
| R | Un bloqueo nuevo (`jira.user`): el bloque entero otra vez | PASS |
| S | SessionStart con binding a una tarea bloqueada: una línea | PASS |
| T | SessionStart sin binding: la última tarea, como sugerencia y no como elección | PASS |
| U | `TASK_CONTEXT_STALE`: deny | PASS |
| V | `PLAN_STALE`: deny | PASS |
| W | `REFUTATION_STATE_STALE`, con un `run.json` real de `refute --compile`: deny | PASS |
| X | `REPOSITORY_STATE_STALE` sin reconciliar después de cambiar el remoto: deny, y el estado guardado queda igual | PASS |
| Y | Un error interno de la compuerta: deny `FLOW_GATE_UNRESOLVED`; la lectura pasa | PASS |
| Z | UserPromptSubmit y SessionStart con la compuerta rota salen 0, y la mutación sigue en deny | PASS |
| 10 | Quince casos de clasificación; un comando desconocido con la tarea bloqueada es deny | PASS |
| 11 | El `.env` por ruta, glob, Bash, PowerShell y variable: nunca de lectura, y deny | PASS |
| 12 | Procesos nuevos: el mismo binding, el mismo bloqueo y la misma decisión | PASS |
| 16 | Secretos: ninguno en stdout, stderr, `sessions/`, `tasks/` ni en las huellas de aviso | PASS |

## El runtime real de Claude Code

Se corrió el binario de la extensión (Claude Code 2.1.283, `claude.exe -p`) sobre un proyecto
temporal instalado con `install.ps1`. Un registrador de eventos vivió solo en ese proyecto, y el
proyecto ya se borró.

| Qué | Resultado |
|---|---|
| El `session_id` es el mismo en SessionStart, UserPromptSubmit, PreToolUse y PostToolUse, y después de `--resume` | PASS |
| El `systemMessage` y el contexto de UserPromptSubmit llegan; el segundo prompt recibe la línea compacta | PASS |
| `Write` con la tarea bloqueada: deny `FLOW_HARD_BLOCKER`, el archivo no se creó | PASS |
| `Agent` con la tarea bloqueada: llega con ese nombre, deny, 0 subagentes lanzados | PASS |
| `flujo ABC-123 --status` por Bash: corrió | PASS |

## Aceptación manual en la UI

La hizo la persona en su editor, sobre un proyecto instalado con `install.ps1` y ABC-123 bloqueada
por `JIRA_TOKEN`. No es una integración nativa con el editor: es un enlace que el cliente abre.

| Paso | Resultado |
|---|---|
| «Seguimos con ABC-123» muestra el bloqueo por `JIRA_TOKEN`, sin ningún valor | PASS |
| El enlace `vscode://file/…` se puede clickear | PASS |
| Abre el `.env` en la línea 4, columna 1 | PASS |
| «creá el archivo prueba.txt…» da `FLOW_HARD_BLOCKER` | PASS |
| `prueba.txt` no se creó | PASS |

## El cierre: `git remote -v` con límite propio

`repositorio.remotos` esperaba hasta 10 s, y cuando se vencía el tiempo devolvía lo mismo que un
checkout sin remotos. En un hook eso tenía dos costos:

- cada herramienta esperaba 10 s si `git` se colgaba;
- con la lista de remotos guardada vacía, la herramienta pasaba.

Ahora el hook pasa su propio límite, `TIMEOUT_REMOTOS` = 1,5 s, y un vencimiento levanta una
excepción. La compuerta falla cerrada con `FLOW_GATE_UNRESOLVED`, y la CLI sigue con sus 10 s. El
límite sale de medir `git remote -v` 200 veces: mediana 50 ms, p95 69 ms, p99 91 ms y máximo
258 ms. Lo cubre E-65, escrito primero y visto en rojo.

La verificación encontró que el corte no llegaba a tiempo con el `git` real de Windows. Ese `git`
es un lanzador que deja al git de verdad como nieto, y `subprocess.run` esperaba a que terminara.
El camino del hook ahora no usa pipes, espera solo al proceso y, vencido, mata el árbol entero. El
camino normal sigue igual: 200 corridas dieron mediana 50 ms y máximo 116 ms, con la misma salida
que la CLI.

## Lo que se controló alrededor

- **Suite:** `.\tests\Invoke-Tests.ps1` sobre el árbol final: 38071/38071 (488 PowerShell + 37583
  Python), salida 0. Antes del cierre del límite de `git remote -v` daba 38048/38048.
- **Refutador:** 65 escenarios sostenidos, 0 contradichos y 0 sin sustento, en la novena pasada
  ([verificacion.md](verificacion.md)).
- **Secretos:** ninguna fuga, en las salidas de los hooks, en el runtime de los proyectos temporales
  y en las salidas y la transcripción de la corrida real.
- **Versión:** `VERSION` sigue en `0.26.0`. No hubo commit, push ni tag.
