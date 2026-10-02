# Verificación — Flow Governance, Wave 5 — fallar cerrado: capacidades, hallazgos, frescura y el Bloque 4

**Estado:** cerrado · **Fecha:** 02-10-2026 · **Versión:** sin release todavía (base 0.26.0, sobre `2c33fba`)

Este documento cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el
veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los dio
`harness-spec-refuter` el 01-10-2026 y el 02-10-2026, en cuatro pasadas. En las dos corrió él mismo
`65_fail_closed --detallado`, las nueve suites de regresión una por vez, sus siete sondas propias
(`sonda1.py` a `sonda7.py`) y la compuerta entera, `.\tests\Invoke-Tests.ps1`. La última dio
38746/38746 (488 PowerShell + 38258 Python), salida 0, con el árbol intacto después.

**Resultado: 43 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

En la primera pasada quedaron 38 sostenidos y 3 contradichos (E-19, E-22 y E-39). Los tres se
arreglaron con el test primero, y apareció E-42. **El texto de E-22 se corrigió después de su
contradicho**; está abajo, en su propia sección. Después la persona decidió normalizar la
presentación: toda métrica sin resolver es `N/D`, también con valor nulo (E-43). En la tercera pasada
E-39 y E-43 quedaron contradichos en la sección de presupuesto; se arreglaron con el test primero y
la cuarta pasada los sostuvo.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Soportada y `ENABLED`: `SUPPORTED_AVAILABLE` | sostenido | sí | `65_fail_closed.py`, `test_e01_…` |
| E-02 | Soportada y `AUTHENTICATION_FAILED`: `SUPPORTED_UNAVAILABLE` | sostenido | sí | `test_e02_…` |
| E-03 | Soportada y `CONNECTION_FAILED` | sostenido | sí | `test_e03_…` |
| E-04 | Soportada y `PERMISSION_DENIED` | sostenido | sí | `test_e04_…` |
| E-05 | Soportada y `NOT_CONFIGURED` | sostenido | sí | `test_e05_…` |
| E-06 | Lo que nadie declara: `NOT_SUPPORTED` | sostenido | sí | `test_e06_…` |
| E-07 | Una caída no se deriva al constructor | sostenido | sí | `test_e07_…`; sonda 2 con un plan mixto |
| E-08 | Lo no soportado se sigue derivando | sostenido | sí | `test_e08_…` |
| E-09 | `capabilityStatus` no miente, y `plan` tampoco | sostenido | sí | `test_e09_…` |
| E-10 | `CRITICAL` `OPEN`: `ACTION_REQUIRED` | sostenido | sí, por mutación | `test_e10_…` |
| E-11 | `CRITICAL` `REOPENED`: `ACTION_REQUIRED` | sostenido | sí | `test_e11_…` |
| E-12 | `CRITICAL` `UNRESOLVED`: `REVIEW_INCOMPLETE`, nunca `READY` | sostenido | sí | `test_e12_…`; sonda 4 |
| E-13 | `UNRESOLVED` no se convierte en `OPEN` | sostenido | sí, por mutación | `test_e13_…` |
| E-14 | `CURRENT` deja planificar | sostenido | sí | `test_e14_…` |
| E-15 | Sin verificar: sigue, marcado | sostenido | sí | `test_e15_…` |
| E-16 | Un estado de integridad bloquea la operación | sostenido | sí | `test_e16_…`; sonda 6: `refute --compile` no cambia ningún archivo |
| E-17 | Lo que no se exige no bloquea | sostenido | sí | `test_e17_…` |
| E-18 | Una sola lista de lo que bloquea | sostenido | sí | `test_e18_…`; texto ampliado al flujo |
| E-19 | Tokens sin resolver: `N/D` en todas partes | sostenido | sí | `test_e19_…`; contradicho en la primera pasada, ver abajo |
| E-20 | Un cero medido es `0` | sostenido | sí, por mutación | `test_e20_…` |
| E-21 | No hay un segundo ledger | sostenido | sí, por mutación | `test_e21_…`; texto ajustado al campo `resolved` |
| E-22 | La Context Bar no confunde lo sin resolver con un cero | sostenido | sí | `test_e22_…`; **texto corregido**, ver abajo |
| E-23 | Los cinco estados de integración, exactos | sostenido | sí, por mutación | `test_e23_…` |
| E-24 | No hay `NOT_REQUIRED` | sostenido | sí, por mutación | `test_e24_…` |
| E-25 | La Wave 4 sigue verde | sostenido | no consta | `64_interaccion_humana` 376/376 |
| E-26 | La Wave 3 sigue verde | sostenido | no consta | `63_compuerta_del_flujo` 487/487 |
| E-27 | La Wave 2 sigue verde | sostenido | no consta | `62_estado_del_flujo` 177/177 |
| E-28 | La Wave 1 sigue verde | sostenido | no consta | `61_flujo_precondiciones` 184/184 |
| E-29 | Refutación atómica sigue verde | sostenido | no consta | `55_refutacion_atomica` 306/306 |
| E-30 | Entorno primero sigue verde | sostenido | no consta | `60_entorno_primero` 307/307 |
| E-31 | Reporte de seguridad sigue verde | sostenido | no consta | `48_reporte_de_seguridad` 566/566 |
| E-32 | Bloque 4 sigue verde | sostenido | no consta | `30_b4_contabilidad` 871/871 |
| E-33 | Context Bar sigue verde | sostenido | no consta | `53_context_bar` 464/464 |
| E-34 | La compuerta entera | sostenido | no consta | 38746/38746, salida 0, corrida de quien verificó |
| E-35 | El flujo dice `CAPABILITY_UNAVAILABLE` y `--resume` revalida solo eso | sostenido | sí | `test_e35_…` |
| E-36 | `UNRESOLVED` con `blocking`, y resuelto que vuelve sin resolver | sostenido | sí | `test_e36_…` |
| E-37 | Severidad desconocida: `REVIEW_INCOMPLETE`; resuelto no bloquea | sostenido | sí | `test_e37_…` |
| E-38 | Una alerta que llega después bloquea; resuelta, el plan quedó viejo | sostenido | sí | `test_e38_…` |
| E-39 | Un parcial no es el total | sostenido | sí | `test_e39_…` y `test_e39b_…`; contradicho en la primera y la tercera pasada, ver abajo |
| E-40 | No descubierta o sin registro: nunca `NOT_SUPPORTED` | sostenido | sí | `test_e40_…` |
| E-41 | Una sola autoridad de lo soportado | sostenido | no consta | `test_e41_…` |
| E-42 | Un plan viejo con un hueco soportado quedó viejo | sostenido | sí | `test_e42_…`; nuevo de la verificación |
| E-43 | Toda métrica sin resolver es `N/D`, también con valor nulo | sostenido | sí | `test_e43_…` y `test_e43b_…`; decisión de la persona; contradicho en la tercera pasada, ver abajo |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

Los tests de E-01 a E-24 y de E-35 a E-41 se escribieron antes del código y se corrieron en rojo:
120 de 167 aserciones fallaron. Los seis escenarios que pasaban desde el principio (E-10, E-13, E-20,
E-21, E-23 y E-24) se vieron fallar por mutación. Cada arreglo de la verificación se escribió primero
como test y se vio en rojo.

## E-22, el texto que se corrigió después de su contradicho

```text
antes:  no muestra «un tiempo con TIME_ATTRIBUTION_UNRESOLVED»
ahora:  no muestra «un tiempo de pared al que le faltó algún evento; uno medido entero sí,
        aunque falte otra clase»
```

El código decide el tiempo por clase (`wallMsMissing`, `modelMsMissing`, `toolMsMissing`), porque
`TIME_ATTRIBUTION_UNRESOLVED` lo levanta cualquier clase que falte. La primera pasada mostró que una
pared medida entera, con el tiempo de modelo faltante, aparecía en la barra, y eso contradecía la
letra de E-22. La conducta no cambió: cambió el texto, y la spec dice por qué.

🔴 **No es solo una aclaración: se recortó una proposición.** La de «ocultar una pared completa
cuando falta el tiempo de modelo» desapareció, y no pasó a otro escenario.

**Ratificado por la persona el 02-10-2026.** E-22 queda con el texto nuevo y no vuelve al anterior.
La semántica que ratificó:

```text
metric A unresolved != metric B unresolved

resolved wall time + unresolved model time
=
wall time visible + model time N/D
```

Una métrica sin resolver no se presenta como dato; una resuelta conserva su valor. El tiempo de pared
se oculta, o sale `N/D`, solo si su propia atribución está incompleta.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El reporte de seguridad mostraba `0` con un `summary.json` viejo** (E-19, E-39). La decisión de
   qué está resuelto venía del campo nuevo `resolved`. Un `summary.json` escrito por la 0.26.0 no lo
   trae, y el reporte copiaba el `0` y el monto parcial (`1.25`). Ahora un resumen viejo con algo en
   `unresolved` no deja copiar ningún número como valor. Además la sección de ejecución dice `N/D` y
   no «desconocido», en md y en html; para eso se actualizó la expectativa de E-44 de
   `48_reporte_de_seguridad`.
2. **Un plan de antes de la Wave 5 seguía derivando una integración caída** (E-42). Sin
   `capabilityStatus`, su hueco de `jira.issue.read` daba `CAPABILITY_GAP`. Ahora ese plan quedó viejo
   y se regenera.
3. **La lista de estados que bloquean estaba copiada en el flujo.** `flujo/estado.py` la repetía como
   literal; ahora la lee de `frescura.BLOQUEAN_OPERACION` (E-18).
4. **La spec decía que `summary.json` no cambiaba**, y ganó el campo `resolved`. El texto se corrigió
   (E-21 y «Qué queda afuera»).
5. **La sección de presupuesto mostraba el piso como consumido** (tercera pasada, E-39 y E-43). Con un
   costo parcial, «Consumido» y «Proyectado» decían `USD 1.25` en `contabilidad` y en
   `execution-cost.md`, mientras «Costo real» ya decía `N/D`; con todo sin resolver decían «sin
   resolver». `para_mostrar` no recorría el presupuesto; ahora sí, y `texto_de_decision` respeta `N/D`.
   Las sondas de la segunda pasada no usaban una política de presupuesto y no lo vieron.
6. **Por E-43 cambiaron dos expectativas de tests cerrados**, a la vista en la spec: E-44 de
   `48_reporte_de_seguridad` (lo ausente en la sección de ejecución es `N/D`) y E-12 de
   `30_b4_contabilidad` (el costo real de una suscripción es `N/D`).

## Lo que queda abierto, anotado y no escondido

- **El deny cruzado de la aceptación manual es aislamiento de sesión, no un defecto de esta Wave.**
  Una sesión ligada a ABC-123, que estaba `BLOCKED`, no pudo correr `contabilidad ABC-456`: la
  compuerta de la Wave 3 niega lo `MUTATING` de una sesión cuya tarea está bloqueada, y
  `contabilidad` es `MUTATING` porque escribe `summary.json` (y con `--reporte`, `execution-cost.md`). Evaluado contra
  ABC-456 también sería deny, `TASK_FLOW_STATE_MISSING`, porque ABC-456 no tiene estado del flujo. Lo
  que no cuadra con la Wave 3 es el motivo: `contabilidad` pierde su clave en `tool_policy` y se
  evalúa contra la tarea de la sesión. Es de la Wave 3 (`2b43a77`), igual en la línea de base, y quedó
  anotado para la Wave 6 junto con dos inconsistencias previas del plan, en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **Un `summary.json` viejo** casi siempre trae algo en `unresolved` (por ejemplo
  `AGENT_ATTRIBUTION_UNRESOLVED`). Hasta que se vuelva a correr `contabilidad`, el reporte de
  seguridad muestra `N/D` en toda la ejecución. Es conservador, no una falla.
- **La decisión de presupuesto se calcula sobre un piso**: con un costo parcial, `presupuesto.evaluar`
  igual da `WITHIN_BUDGET`. Los montos ya salen `N/D`, pero el estado es una decisión sobre un número
  que no es el total. El Bloque 4 no gobierna; queda para la Wave 6, en `PENDIENTES-FH.md`.
- **La tabla de conciliación de `execution-cost.md`** muestra lo derivado y lo reportado crudos con
  `USAGE_RECONCILIATION_UNRESOLVED`, rotulados como «la derivación es un piso, no la verdad». Es la
  evidencia de por qué los totales salen `N/D`, no un total.
- **Un hallazgo `HIGH` `UNRESOLVED` sin `blocking`** no bloquea, igual que un `HIGH` `OPEN` sin
  `blocking`. Es lo que dice la tabla de la spec.
- **La ingesta del Bloque 4 y los estados de instalación que pintan `OK`**: para la Wave 6, en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en la entrada «Block 4 still loses the unresolved
  marker on ingest, and installation states paint OK».
- **La frescura de ES0902 en el reporte de seguridad** sigue más estricta que la compuerta de las
  operaciones: el reporte pone `BLOCKED` todo lo que no está `CURRENT`. Son dos preguntas distintas y
  la spec las separa.

## Lo que ningún test cubre y se mira con los ojos

- Que en un proyecto instalado `plan` muestre la capacidad caída con su integración y su estado, sin
  `dev-tool-builder`, y que `flujo --status` diga `CAPABILITY_UNAVAILABLE`. Es la aceptación manual A.
- Que `contabilidad` muestre `N/D` en los tokens de un libro sin resolver. Es la aceptación manual B.
