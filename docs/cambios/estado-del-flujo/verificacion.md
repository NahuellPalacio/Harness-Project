# Verificación — Flow Governance, Wave 2 — el estado del flujo por tarea

**Estado:** cerrado · **Fecha:** 29-09-2026 · **Versión:** sin release todavía (base 0.26.0, sobre `4a18ddc`)

Este documento cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el
veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los dio
`harness-spec-refuter` el 29-09-2026, en tres pasadas:

- **Primera.** Corrió `62_estado`, `61_flujo`, `55_refutacion`, `53_context`, `60_entorno` y
  `19_contexto`, y la compuerta entera (37548/37548, salida 0). Reprodujo el rojo inicial poniendo
  los tests sobre `4a18ddc`.
- **Segunda y tercera.** Volvió a correr `62_estado` sobre el árbol corregido (173/173) y tomó como
  evidencia la compuerta de quien construyó sobre el árbol final: 37582/37582 (488 PowerShell +
  37094 Python), salida 0. Esa compuerta se lanzó después del último arreglo.

**Resultado: 38 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Dos tareas, dos `state.json` | sostenido | sí | `62_estado_del_flujo.py`, `test_e01_…` |
| E-02 | No hay `task-state.json` ni fuente que lo nombre | sostenido | sí | `test_e02_…` |
| E-03 | `active-task.json` es solo el puntero | sostenido | sí | `test_e03_…` |
| E-04 | Borrado, se reconstruye igual; sin artefactos, `CONTEXT` | sostenido | sí | `test_e04_…` |
| E-05 | No copia el TaskContext | sostenido | sí | `test_e05_…` |
| E-06 | No copia el plan | sostenido | sí | `test_e06_…` |
| E-07 | Ningún valor del `.env` | sostenido | sí | `test_e07_…` |
| E-08 | Un `SECRET` pendiente sin valor, línea, columna ni enlace | sostenido | sí | `test_e08_…` |
| E-09 | `BLOCKED`: sin avance, seis de recuperación | sostenido | sí | `test_e09_…` |
| E-10 | Lo mismo con `WAITING_FOR_HUMAN_APPROVAL` | sostenido | sí | `test_e10_…`; ver abajo |
| E-11 | Una transición no se declara: `FLOW_TRANSITION_INVALID` | sostenido | sí | `test_e11_…` |
| E-12 | Arreglado el checkout, se reevalúa la compuerta y queda `PLAN_NOT_READY` | sostenido | sí | `test_e12_…` |
| E-13 | Sin arreglarlo, el mismo bloqueo | sostenido | sí | `test_e13_…` |
| E-14 | `resumeFrom` con una compuerta canónica | sostenido | sí | `test_e14_…` |
| E-15 | TaskContext cambiado: `TASK_CONTEXT_STALE` | sostenido | sí | `test_e15_…` |
| E-16 | Plan reescrito: `PLAN_STALE` | sostenido | sí | `test_e16_…` |
| E-17 | Remoto cambiado: `REPOSITORY_STATE_STALE` | sostenido | sí | `test_e17_…` |
| E-18 | Corrida de otro plan: `REFUTATION_STATE_STALE` | sostenido | sí | `test_e18_…` |
| E-19 | `state.json` roto: `TASK_FLOW_STATE_INVALID`, sin avance | sostenido | sí | `test_e19_…` |
| E-19b | Un artefacto roto no se toma por ausente | sostenido | sí, antes del arreglo | `test_e19b_…`; ver abajo |
| E-20 | Una escritura rota deja el anterior entero y sin temporales | sostenido | sí | `test_e20_…` |
| E-21 | `contexto` reconcilia | sostenido | sí | `test_e21_…`, con el Jira falso de `19_contexto.py` |
| E-22 | Plan `BLOCKED` por repositorio: tarea `BLOCKED` | sostenido | sí | `test_e22_…` |
| E-23 | Plan listo: `EXECUTION` / `ACTIVE` | sostenido | sí | `test_e23_…` |
| E-23b | Un plan escrito no listo no llega a `EXECUTION`; un `stale` no deja avanzar | sostenido | sí, antes del arreglo | `test_e23b_…`; ver abajo |
| E-24 | Compuerta de refutación fallida: sin `run.json`, estado coherente | sostenido | sí | `test_e24_…` |
| E-25 | `flujo --status` sin red | sostenido | sí | `test_e25_…`, socket y transporte que fallan |
| E-25b | `flujo --status` no escribe | sostenido | sí, por mutación | `test_e25b_…` |
| E-25c | Un estado igual no se reescribe | sostenido | sí, por mutación | `test_e25c_…` |
| E-25d | `--compile` que pasa y `--record` reconcilian | sostenido | sí, por mutación | `test_e25d_…` |
| E-25e | Una reconciliación rota no voltea `plan` | sostenido | sí, por mutación | `test_e25e_…` |
| E-26 | `flujo/` y `estado_de_tarea/` sin red ni modelo | sostenido | sí | `test_e26_…` |
| E-27 | El Bloque 4 no gobierna | sostenido | sí | `test_e27_…` |
| E-28 | Wave 1 sigue verde | sostenido | no consta | `61_flujo_precondiciones`, 183/183 |
| E-29 | Refutación atómica sigue verde | sostenido | no consta | `55_refutacion_atomica`, 305/305 en la compuerta |
| E-30 | Context Bar sigue verde | sostenido | no consta | `53_context_bar`, 465/465 en la compuerta |
| E-31 | Entorno primero sigue verde | sostenido | no consta | `60_entorno_primero`, 307/307 en la compuerta |
| E-32 | La compuerta entera | sostenido | no consta | 37582/37582, salida 0 |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

Los tests de E-01 a E-27 se escribieron antes que `flujo/estado.py` y
`estado_de_tarea/persistencia.py`, y se corrieron en rojo: 20/65 aserciones, con al menos una falla
por escenario. Después, trece mutaciones de la lógica dieron rojo en el escenario que tocaban.

## E-10, sin sustento en la primera pasada

La spec pide "lo mismo que E-09", que son dos cosas: ningún permiso de avance y las seis operaciones
de recuperación. El test afirmaba solo la primera. Se agregó la segunda, sin cambiar el texto del
escenario, y en la segunda pasada quedó sostenido.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **F1: la tarea llegaba a `EXECUTION` con un plan escrito `BLOCKED`.** El bloqueo `PLAN_NOT_READY`
   se decidía con `estado_de` recalculado y no con el `status` escrito. Con `flowPreconditions`
   editado a mano, la tarea quedaba `EXECUTION` / `ACTIVE`, y `refute --compile` sin embargo la
   rechazaba por `PLAN_NOT_READY`. El estado y la compuerta de la Wave 1 no coincidían. Ahora
   `EXECUTION` pide el plan listo por los dos lados, y un `stale` entre artefactos no deja avanzar.
   Lo cubre E-23b.
2. **Un TaskContext, un plan o un `run.json` rotos se leían como ausentes, sin aviso.** Con un
   `run.json` roto la tarea quedaba `EXECUTION` con `implementationAllowed: true`. Ahora bloquean con
   `TASK_CONTEXT_MISSING`, `PLAN_NOT_READY` o `REFUTATION_OUTPUT_INVALID`. Lo cubre E-19b.
3. **F2 y F3, dos variantes del punto 2:** un `run.json` roto **sin plan**, y un plan `{}`, que es
   JSON válido pero se tomaba por ausente porque un dict vacío es falso en Python. Las dos entran en
   E-19b.
4. **Cinco afirmaciones de la spec no tenían test** y funcionaban:
   - `flujo --status` no escribe;
   - un estado igual no se reescribe;
   - reconcilian `--compile` cuando pasa y `--record`;
   - una reconciliación rota no voltea el comando.

   Ahora son E-25b a E-25e. Como pasaron en la primera corrida, su rojo es por mutación, y la tabla
   lo dice.
5. **La spec decía "los tests se escriben antes y se registra su rojo" para todo**, y no era así
   para E-25b a E-25e. "Cómo se verifica" ahora dice de dónde sale cada `sí`.

## Lo que queda abierto, anotado y no escondido

- **`VERIFICATION`, `COMPLETED` y `CANCELLED` no se derivan en esta Wave.** Los dos últimos esperan a
  las decisiones humanas de la Wave 4.
- **`active-task.json` es la última tarea reconciliada, no una elección.** Cómo se usa lo decide la
  Wave 3.
- **`refutacion.compilar` como biblioteca** sigue sin compuerta ni reconciliación.
- **Siguen diferidos los hallazgos de la Wave 1:** `AlmacenSecretos.set/remove`, `PlanInvalido` en
  `main`, el alcance de E-25 de la Context Bar, el stub de Python y el conteo de `CLAUDE.md`.

## Lo que ningún test cubre y se mira con los ojos

- Que `flujo <KEY> --status` se lea bien en una terminal real de Windows y que el enlace de la
  interacción pendiente abra el archivo en la línea que dice.
