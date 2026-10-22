# Verificación — Verification Pipeline Performance: un runner paralelo acotado que da lo mismo que `Invoke-Tests.ps1`, en menos tiempo

**Estado:** cerrado · **Fecha:** 22-10-2026 · **Versión:** 0.35.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió una invocación nueva e independiente de `harness-spec-refuter` el 22-10-2026, que no construyó Task 6.1 y no escribe su propio veredicto en un archivo; quien coordinó lo consolidó acá. Corrió `75_manifest_paralelo.py`, `75_runner_paralelo.py` y `tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75`, leyó el código contra la spec y repitió mutaciones sobre copias fuera del repo donde la marca `rojo visto` no tenía salidas crudas. La spec sobre la que rige es `docs/cambios/verification-pipeline-performance/spec.md` con SHA256 `F0F5B95BA62FBC343784E597869C02666416960F034C2A13EA9D63C57A531415`.

**Resultado: 25 escenarios sostenidos (VP-E24 en dos partes, 26 filas), 0 contradichos, 0 leídos, 0 sin sustento.** Todas las invariantes VP-I01..VP-I17 tienen escenarios sostenidos.

## Qué se verificó y sobre qué

| | |
|---|---|
| Spec verificada | `F0F5B95BA62FBC343784E597869C02666416960F034C2A13EA9D63C57A531415` (construida; enmiendas D-T1..D-T7 en §1.3) |
| Baseline | rama `main`, `d86b285a9d0a4610a44a15ba3ca455be42d2edaa`, tag `v0.34.0`, `VERSION` 0.34.0 |
| Estado del árbol | Task 6.1 sin commit: 4 archivos modificados y 9 sin seguimiento; los hashes coinciden con `POST-CONSTRUCTION-FREEZE` |
| Entorno | Git Bash primero en el `PATH`, sin elevar, `TEMP=TMP=TMPDIR=C:\t`, un trabajo pesado por vez |
| Frontera | Boundary audit del 22-10-2026, solo lectura: `TASK 6.1 BOUNDARY ALIGNED` (el producto, el modelo canónico 11/89, el instalador y las 97 suites históricas, sin cambios) |

## Método

- `python tests\correr.py -k 75_manifest_paralelo.py`: 46/46, exit 0.
- `python tests\correr.py -k 75_runner_paralelo.py`: 838/838, exit 0, 378 s.
- `tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75`: exit 0, «PAR ACEPTADO». Su pata serial es `.\tests\Invoke-Tests.ps1`, la compuerta (§30.1).
- Lectura del código contra §9–§20 para lo que un test no decide.
- Mutaciones propias sobre copias fuera del repo para VP-E23 y VP-E24 parte A, cuyas marcas solo constaban en el registro de construcción.

## Escenarios

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| VP-E01 | Seis suites verdes, N = 2: exit 0, suma exacta, un inicio por suite, cada Py reporta su stem | sostenido | sí (VM-01a 7/15, VM-01b 6/15, VM-02a, VM-02b) | `75_runner_paralelo.py`, `test_vp_e01_…` (:1057) |
| VP-E02 | Suites con aserciones rojas: exit 1, `N fallaron.` exacto, filas PS antes que Py | sostenido | sí (VM-03 13/14) | `test_vp_e02_…` (:1103) |
| VP-E03 | Un `.ps1` y un `.py` que no cargan aportan una fila de carga cada uno, sin `INFRA` | sostenido | sí (VM-12b 14/15 y 13/15) | `test_vp_e03_…` (:1554) |
| VP-E04 | El resumen es la última línea y cruza con los grupos; exit y conteo incoherentes, rojos | sostenido | sí (VM-04a 18/24, VM-04b 16/24) | `test_vp_e04_…` (:1607) |
| VP-E05 | Un worker matado sale `WORKER_MUERTO`, no suma y no se relanza | sostenido | sí (VM-03 19/20, VM-13a 17/20, VM-13b 17/20) | `test_vp_e05_…` (:1690) |
| VP-E06 | Sin resumen o salida cortada: `SIN_RESUMEN`, nunca `0/0 pasaron.`; `0/0` real, verde | sostenido | sí (VM-12a 15/22) | `test_vp_e06_…` (:1754) |
| VP-E07 | El stderr de una suite Py la pone roja como en el oráculo; el de PS da lo mismo que el oráculo | sostenido | sí (VM-11 9/15) | `test_vp_e07_…` (:1811) |
| VP-E08 | Timeout: corta el árbol vivo en menos de 20 s, testigo vivo, sin relanzar; `null` no corta | sostenido | sí (VM-19a 16/17 con 9 s; VM-19b, c, d con 3 s) | `test_vp_e08_…` (:2394), `timeoutSeconds: 9` (D-T4) |
| VP-E09 | Temporal propio, vacío y distinto por suite; el resto del entorno, heredado sin agregados | sostenido | sí (VM-07a/b, VM-08a–d) | `test_vp_e09_…` (:1868) |
| VP-E10 | Huella igual tras corrida verde y cancelada; un archivo nuevo en la raíz da `ARBOL_CAMBIADO` | sostenido | sí (VM-09a 7/17, VM-09b 13/17) | `test_vp_e10_…` (:2479) |
| VP-E11 | `serial` y desconocida corren solas; el carril no se solapa; la desconocida avisa | sostenido | sí (VM-05a 7/10, VM-05b 8/10, VM-06a 8/10) | `test_vp_e11_…` (:1151) |
| VP-E12 | Nunca más de N vivas y N cuando hay trabajo; `-Workers 0` o `5`, exit 1 | sostenido | sí (VM-14a 13/14, VM-14b 11/14) | `test_vp_e12_…` (:1201) |
| VP-E13 | El agregador, por la costura, nombra faltante, sobrante, repetida, `INFRA`, incoherencia, grupo ajeno y `ERROR_INTERNO` | sostenido | sí (VM-01c 30/39, VM-02c 38/39) | `test_vp_e13_…` (:1313), costura `Get-ReporteDeCorrida` |
| VP-E14 | Reporte comparable idéntico con N = 1, 2 y 4, en orden canónico, sin pid, ruta ni hora | sostenido | sí (VM-10a 14/18, VM-10b 12/18 y 12/18) | `test_vp_e14_…` (:1407) |
| VP-E15 | Layout verde con tildes: oráculo y runner, `EQUIVALENTE` | sostenido | sí (VM-02a 16/21) | `test_vp_e15_…` (:3328) |
| VP-E16 | Con fallos inyectados: los dos salen 1 y `EQUIVALENTE` con las mismas filas fallidas | sostenido | sí (VM-02a, `fallaronPs = 0`, 10/14) | `test_vp_e16_…` (:3393) |
| VP-E17 | Pares adulterados: `NO_EQUIVALENTE` nombrando el campo, `NO_COMPARABLE` con huellas distintas o `MAL` ambigua | sostenido | sí (VM-18a 175, 206, 223 de 237; VM-18c 225/237) | `test_vp_e17_…` (:3545) |
| VP-E18 | Deriva externa con la misma huella: `NO_EQUIVALENTE`; el comparador no acepta tolerancia | sostenido | sí (VM-18b 13/19) | `test_vp_e18_…` (:3608) |
| VP-E19 | Cancelación por archivo: no lanza más, árbol muerto en < 30 s, candado libre, `CANCELADO`, exit ≠ 0 | sostenido | sí (VM-16a–d: 19/21, 20/21, 18/21, 19/21) | `test_vp_e19_…` (:2537) |
| VP-E20 | Nieto huérfano y timeout: `TIMEOUT`, `AVISO LIMPIEZA_INCOMPLETA` con su ruta, testigo vivo | sostenido | sí (VM-19d 9/13; VM-19a no la ve, la ve E08) | `test_vp_e20_…` (:2595) |
| VP-E21 | Limpieza y barrido: aviso sin cambiar el exit, raíz muerta barrida, `.lock` tomado intacto, junction no seguido, ciclo del sidecar | sostenido | sí (VM-17a 25/30, VM-17b 19/20 por excepción, VM-17c 29/30) | `test_vp_e21_…` (:2646) |
| VP-E22 | Candado: de dos corre uno y el otro sale 2; ilegible sale 2; dueño muerto libera; se suelta después del último worker | sostenido | sí (VM-15a–c) | `test_vp_e22_a_…` (:2822), `_b_c_…` (:2894), `_d_…` (:2991) |
| VP-E23 | Sin `-SoloCaso`, el oráculo da lo mismo que `v0.34.0` byte a byte; con `-SoloCaso`, ese archivo y nada más | sostenido | sí (VM-20 y B6; reproducido: 62/66, 56/66, 3/7) | `test_vp_e23_…` (:903, :912, :1017) |
| VP-E24 parte A | Política del manifest real: cobertura 1:1, `reason`, fórmula exacta, sin subcadenas | sostenido | sí (VM-06; reproducido: 45, 40, 44 y 44 de 46) | `75_manifest_paralelo.py`, 46/46 |
| VP-E24 parte B | Forma del manifest en el runner: inválido, `MANIFEST_INVALIDO` sin lanzar nada; fuera de la fórmula, corre | sostenido | sí (VM-06B-i 12/36, VM-06B-ii 32/36) | `test_vp_e24_b_…` (:1496) |
| VP-E25 | Sobre el árbol real, el medidor con `-Umbral 0.75` sale 0: huellas iguales, `EQUIVALENTE`, residuos 0, umbral cumplido | sostenido | sí (sondas rojas del medidor; VM-18 lado medidor) | `tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75`, exit 0 |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006: un test que nunca se vio fallar no probó que puede fallar. En esta spec ningún escenario quedó en `no consta`.

## VP-E25 y la compuerta, en números

```
Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75     22-10-2026, capturas en C:\t\hpm-261022-120610\
  serial    .\tests\Invoke-Tests.ps1             3299,4 s   exit 0   48841/48841   stderr 0 B
  paralela  Invoke-Tests-Parallel.ps1 -Workers 2 2049,2 s   exit 0   48841/48841
  huellas   inicial = entre patas = final        880F1EDA…847F
  comparador                                     EQUIVALENTE (35 grupos PS, 75 grupos Py)
  residuos atribuibles                           0 (TempBase vacío, 0 líneas ^AVISO LIMPIEZA_INCOMPLETA)
  relación                                       0,6211  (umbral 0,75: límite 2474,5 s)
  PAR ACEPTADO (exit 0)
```

La pata serial sostiene el punto 1 de §30 sobre el árbol que se verificó. El par corrió sobre `880F1EDA…`, no sobre la huella del par de cierre de la construcción (`94999FD9…`), porque después del cierre cambiaron la spec, el benchmark y los pendientes: es lo que pide §30.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El punto F11 de §17 no está implementado.** La spec promete `ERROR_INTERNO violación de clase` cuando los intervalos muestran una suite `serial` conviviendo con otra. El agregador tiene `SUITE_AUSENTE` y `SUITE_DUPLICADA` (`tests/Invoke-Tests-Parallel.ps1:833-834`), pero no esa detección. Ningún escenario la pide: VP-E11 prueba que el scheduler no las solapa, no que el agregador lo detecte. Quedó como pendiente en FH.
2. **Dos marcas `rojo visto` solo constaban en el registro de construcción**, las de VP-E23 y VP-E24 parte A. Se reprodujeron sobre copias y coinciden.
3. **VP-E22 (d) se sostiene por composición.** No lanza un segundo runner durante la ventana, y la aclaración A5 que lo reemplaza no es una enmienda de §1.3. Lo sostienen dos cosas que sí se prueban: (b) muestra que el runner sale `LOCK_OCUPADO` con el byte 0 tomado, y (d) muestra que el byte sigue tomado hasta después de la muerte del último worker.

## Lo que queda abierto, anotado y no escondido

- **VX-01..VX-29** de la spec, en `Pendientes/Fix-Harness/PENDIENTES-FH.md` («What the parallel test runner left open») y en `Pendientes/Ideas-Harness/PENDIENTES-I.md`.
- **F11 sin implementar**, en FH, en la misma sección: «The runner does not detect a `serial` suite living alongside another, which the spec promises».
- **VP-I01, la parte de «toda excepción interna da ≠ 0» fuera del agregador.** Se leyó en `Invoke-Tests-Parallel.ps1:1535-1539` y no se vio en un test.
- **ADR-0018 §4 (VX-22), resuelto antes del release:** por decisión de Nahuel Palacio del 22-10-2026, §4 dice ahora «Desde la fase C (§2), quien refuta puede explorar con el runner; antes, no lo usa». El ítem salió de FH y la nota 0.35.0 lo nombra como cerrado.

## Lo que ningún test cubre y se mira con los ojos

- **El disparo real de Ctrl-C** sobre el runner (§26, R7). VP-E19 prueba el mismo `finally` con la señal inyectable; que PowerShell 5.1 llegue a ese `finally` ante un Ctrl-C real se confirma con la mano.
- **La relación en otra máquina.** Depende del arranque de PowerShell (2,65–3,25 s en esta) y de la carga ajena. Las tres mediciones de esta máquina dieron 0,658 (con `-Detallado`), 0,709 y 0,621.

## Estado del repositorio al cerrar la verificación

Rama `main`, HEAD `d86b285` (0.34.0), sin commit de Task 6.1. `pre-tool-use.py` y `zonas.py`, sin cambios. Ninguna corrida se cortó a mitad. El release es `close-a-version` como 0.35.0, con la nota de que el cambio es solo de la fábrica y no hace falta reinstalar.
