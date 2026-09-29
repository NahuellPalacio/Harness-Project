# Aceptación funcional — Flow Governance, Wave 1

**Fecha:** 29-09-2026 · **Baseline:** `VERSION 0.26.0`, HEAD `6cff4b4105b066c04a7b41090787775e41e51463`,
con la Wave 1 sin commitear · **Resultado:** 9/9 escenarios funcionales, suite 37405/37405

Esta aceptación no es la verificación de ADR-0006, que está en [verificacion.md](verificacion.md).
Es una corrida de punta a punta, con la CLI real, sobre proyectos temporales: un `git init` con
remotos que no existen, un TaskContext con su hash calculado y un `.env` con secretos sintéticos.
Acá se escriben `<synthetic-secret>` (el `JIRA_TOKEN` del fixture) y `<synthetic-gitlab-token>`.
Ninguna integración sale a la red. A–G corren por `dev-harness.py plan` y `refute`; H e I, por
`flujo/entrada_humana.py`, porque en esta Wave el localizador todavía no tiene comando.

| # | Escenario | Esperado | Obtenido | Resultado |
|---|---|---|---|---|
| A | Happy path | `MATCHED` · `READY_FOR_EXECUTION` | `MATCHED` · `READY_FOR_EXECUTION` · 0 preguntas bloqueantes | PASS |
| B | Repositorio faltante | `HARD_BLOCKER` · plan no READY · sin inferir del cwd | `repository.task` `HARD_BLOCKER` / `REPOSITORY_UNRESOLVED` · `BLOCKED` · `taskRepository` nulo | PASS |
| C | Conflicto `GITLAB_PROJECT` contra la Ficha | `REPOSITORY_CONFLICT` · `BLOCKED` · los dos candidatos | `REPOSITORY_CONFLICT` · `BLOCKED` · `candidates` con repo-a y repo-b · `declaredBy` con `FICHA` y `GITLAB_PROJECT` | PASS |
| D | Checkout de otro repositorio | `REPOSITORY_MISMATCH` · plan no READY | `MISMATCH` / `REPOSITORY_MISMATCH` · `BLOCKED` | PASS |
| E | Contexto vencido | `CONTEXT_STALE` · sin `run.json` nuevo | salida 2 · `CONTEXT_STALE` · sin `run.json` | PASS |
| F | Plan no listo | `PLAN_NOT_READY` · sin RefutationUnits · sin dev-refutador | plan `BLOCKED` · salida 2 · `PLAN_NOT_READY` · no se crea `.claude/refutaciones/` | PASS |
| G | Refutación vencida | `REFUTATION_PLAN_STALE` en `--unit` y `--record` | compila con 1 unidad pendiente · replanifica · `--unit` y `--record` salen con 2 y `REFUTATION_PLAN_STALE` | PASS |
| H | Localizador seguro | los siete campos · sin secreto, `value`, `rawLine` ni línea del `.env` | ningún campo falta · nada prohibido · `SECRET` · línea 4, columna 1 | PASS |
| I | Variable que no está | línea de inserción segura · archivo intacto | línea 5 en un archivo de 4 · columna 1 · `present: false` · mismos bytes y mismo mtime | PASS |

## La evidencia que importa

- **A.** `taskRepository` y `localRepositories` dan los dos `gitlab.example/grupo/repo-a`, y `plan` sale con 0.
- **B.** La CLI corrió con el `cwd` en **otro** checkout de repo-a cuya Ficha lo nombra, sobre un
  proyecto cuyo propio remoto también es repo-a. Igual dio `REPOSITORY_UNRESOLVED`: el remoto no
  declara el repositorio de la tarea, y el `cwd` no se lee.
- **C.** `GITLAB_PROJECT` salió del `.env` por `entorno.py`. La pregunta es `repository.unambiguous`,
  de tipo `HUMAN_DECISION`, `HARD_BLOCKER`, con `askUser: true`.
- **E.** El plan estaba `READY_FOR_EXECUTION`. El TaskContext se regeneró con otro título y un hash
  válido. `stderr`: `no se compila la refutacion de ACEP-1: CONTEXT_STALE.`
- **F.** La unidad lleva `blockers: [{inputId: agents.routing, code: AGENT_NOT_FOUND}]`. `refute` no
  llama a ningún modelo.
- **G.** El plan tenía la regla `ES0902.Vu4` y un alcance declarado. Después de `plan --replanificar`,
  `verdicts/` quedó vacío.
- **H.** La salida son exactamente los once campos del contrato. En ese JSON y en la instrucción
  renderizada se buscaron `<synthetic-secret>`, `"value"`, `rawLine` y cada línea del `.env`, y no
  apareció ninguno.

## Lo que se controló alrededor

- **Fugas: ninguna.** Los dos secretos sintéticos se buscaron en todo el stdout y el stderr de la
  corrida, y en todos los archivos de los proyectos temporales salvo `.env` y `.git`.
- **Cambios inesperados: ninguno.** Antes y después de la corrida dieron igual el `git status`, el
  hash de `git diff` (`ac449433…`), la huella de los archivos sin trackear y `VERSION`.
- **Regresión.** `.\tests\Invoke-Tests.ps1` dio 37405/37405 (488 PowerShell + 36917 Python) con
  salida 0. `61_flujo_precondiciones` 182/182, `20_orquestacion` 218/218, `22_registro_agentes`
  159/159, `53_context_bar` 463/463, `55_refutacion_atomica` 305/305, `60_entorno_primero` 307/307.
