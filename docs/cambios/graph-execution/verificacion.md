# Verificación independiente de Task 5 — Graph Execution

**Estado:** verificación independiente cerrada, sin commitear · **Fecha:** 14 y 15-10-2026 · **Spec verificada:** `docs/cambios/graph-execution/spec.md`
(aprobada para construcción por Nahuel Palacio el 13-10-2026, enmendada en diez pasadas durante la construcción y la verificación: 27.1, puntos A a R;
SHA256 de la versión final: `1C6C72097B182F8FE30E168AF3E3F85D9642EE4EB1AAD4479A8DA3C16D3CB643`)

Este documento lo escribe quien coordina, a partir de los informes **textuales** de los refuters. Ningún refuter lo escribió: el proyecto manda que
quien dictamina no escribe su propio veredicto en archivo, y la guarda de su rol no les deja escribir en el repo. Los veredictos de las tablas son
los de cada refuter, sin editar; la columna de la derecha dice cuál de ellos lo dio. Ninguna de las doce invocaciones de `harness-spec-refuter`
fue el builder, y el encargo de cada una le prohibía usar el informe de construcción y el «45.522/45.522» del builder como evidencia.

**Resultado: 71 escenarios de la suite: 71 sostenidos, 0 contradichos, 0 sin sustento. 0 leídos: ningún escenario de Task 5 es de modelo, así que
[ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md) y [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md)
no se usaron. Invariantes: 31 sostenidas. 12 invocaciones de refuter; la coherencia del texto de §17 (cancelación) dio `contradicho` en siete de ellas
y quedó `sostenido` en la última (parte K): ver «Qué pasó con GE-E48 y con §17».**

## Qué se prometió y qué no (para quien lea solo esto)

- **Lo que Task 5 garantiza sobre una cancelación de grafo** es una *marca persistida* (`cancelacion.json`, una sola vez, con `pedidoPor` redactado)
  que el conductor honra antes de cada despacho: después de la marca, ese GraphRun no despacha ninguna Execution nueva, y su terminal lo decide la regla de
  cierre por el estado de cada nodo.
- **Lo que no garantiza** es que la Execution que ya estaba en vuelo termine `CANCELLED`. Eso es del motor de Task 4: `proceso.esperar` solo mira el pedido
  al comienzo de cada tramo de 1 s (`proceso.py:63-72`), de modo que un Host que sale antes de ese chequeo termina con su propio resultado. La spec
  lo dice en §17.2 (norma) y lo detalla como *observación, no norma* en §17.3 y §17.4.
- La spec se ajustó a lo que el código hace; el código no se ajustó a la spec. Esa decisión fue de Nahuel Palacio (15-10-2026) y está registrada en 27.1.

## Baseline

| | |
|---|---|
| Rama | `main` |
| HEAD | `e33b41b0e897bb1bf09bc961882faae07f785135` |
| Tag en HEAD | `v0.32.0` |
| VERSION | `0.32.0` |
| Commits nuevos | 0. Tag nuevo: ninguno. `close-a-version` no se ejecutó |
| Estado del árbol | 13 archivos modificados y 6 nuevos sin seguimiento (la construcción de Task 5), sin commitear. Dentro de cada parte, igual al empezar y al terminar (entre partes cambió la spec, por las enmiendas) |
| Árbol real | 812 archivos (sin `.git` ni `__pycache__`), con foto por SHA256 antes y después de cada parte, la del refuter y la mía: **idéntica en todas** |

## Archivos inspeccionados (diff)

**Modificados (13):** `Pendientes/Fix-Harness/PENDIENTES-FH.md`, `Pendientes/Ideas-Harness/PENDIENTES-I.md`, `docs/dominio/modelo-canonico.md`,
`harnesses/desarrollo/bin/dev-harness.py`, `harnesses/desarrollo/bin/ejecucion/{admision,host_claude_code,motor,registro}.py`,
`tests/casos/63-harness-unico-instalador.ps1`, `tests/casos/64_modelo_de_dominio.py`, `tests/casos/65_contrato_de_ejecucion.py`,
`tests/casos/72_motor_de_ejecucion.py`, `tests/fixtures/host_falso.py` (980 inserciones, 101 borrados).

**Nuevos (6):** `comun/schemas/graph-run-result.schema.json` (129 líneas), `docs/adr/0016-la-ejecucion-de-un-grafo.md` (97),
`docs/cambios/graph-execution/spec.md`, `harnesses/desarrollo/bin/ejecucion/grafo.py` (625), `tests/casos/73-ejecucion-de-grafo-instalador.ps1` (133),
`tests/casos/73_ejecucion_de_grafo.py`.

**No cambiaron contra `e33b41b`** (por hash, parte A): `contrato.py`, `execution-request.schema.json`, `execution-result.schema.json`, ADR-0013, ADR-0014,
ADR-0015, `VERSION`, `CHANGELOG.md`, `UPGRADE.md`, `install.ps1`, `manifest.json`, `tool_policy.py`, `bin/orquestacion/`, `bin/flujo/`, `bin/estado_de_tarea/`.

**Qué cambió después de la parte A** (comprobado por hash por E a L): el **código productivo no cambió**. Cambiaron la spec (diez pasadas, solo texto) y
`tests/casos/73_ejecucion_de_grafo.py` por las enmiendas de GE-E48: el ayudante del cancelador (intervalo y marcas `barrido.N`), la cláusula c) nueva, el docstring y el título
de b), y tres referencias dentro de comentarios y docstrings (la parte J verificó que ninguna es una aserción).

## Cómo se hizo

La verificación se partió en invocaciones **nuevas e independientes** de `harness-spec-refuter` (ninguna es el builder), todas desde la spec, sin informe del
constructor, cada una sobre una **copia aislada** del repo en `%TEMP%` (la suite completa rompe archivos versionados a propósito y no se corre en el repo real) y con
foto por hash del árbol real antes y después (siempre idéntica: ningún refuter tocó el repo). Las mutaciones se hicieron en copias aparte, con la restauración comprobada por hash.

| Parte | Alcance | Resultado de su parte |
|---|---|---|
| A | Contratos, persistencia, CLI, instalador, modelo canónico, compatibilidad con Task 3 y Task 4: GE-E60 a GE-E70 | `SPEC VERIFIED` |
| B | Planificación, admisión, dependencias, huella del plan, N1, R5: GE-E01 a GE-E27 y GE-E53 a GE-E59 | `SPEC VERIFIED` |
| C | Concurrencia, recovery, cancelación, carrera manual residual: GE-E28 a GE-E52 y GE-E71 | `SPEC FAILED` (GE-E48) |
| D | Suite completa independiente y residuo en `%TEMP%` | corridas 1 y 2 con exit 0; no emitió informe final: la detuve yo, antes de la 3.ª (ver «Suite completa») |
| E | Re-verificación de la primera enmienda de GE-E48 | `SPEC FAILED` (GE-E48 b) |
| F | Segunda re-verificación de GE-E48 | `SPEC FAILED` (ventana de 60 s del cancelador) |
| G | Verificación exhaustiva de toda la sección 17 y suite completa sobre el árbol final | `SPEC FAILED` (dos frases de §17.4) |
| H | Sexta pasada | `SPEC FAILED` (un Ctrl-C real sobre el motor vuelve a mirar el pedido) |
| I | Séptima pasada | `SPEC FAILED` (cuatro frases) |
| J | Octava pasada: lo normativo separado de lo informativo | `SPEC FAILED` (tres afirmaciones normativas nuevas) |
| K | Novena y décima pasadas (solo borrar o suavizar) | `SPEC VERIFIED` |
| L | Suite completa independiente sobre el árbol final | `SPEC VERIFIED` (dos corridas completas, 45.534/45.534, exit 0) |

Desde la parte E, cada parte tiene **dos ítems propios**: *integridad* (cambió solo la spec, y solo donde dice la pasada) y *coherencia* (lo que dice el texto se cumple con la CLI de
producción, el Host falso y procesos reales). Los escenarios e invariantes se verificaron en A, B y C y se re-verificaron en E, F y G donde la enmienda los tocaba.


## Veredictos por escenario (GE-E01 a GE-E71)

Cada fila es la del refuter que verificó ese escenario, textual: no la edité. Si lo verificaron dos veces, va la del que lo verificó último, sobre la spec más nueva, y la columna de la derecha lo dice. «T» es un test del repo releído y corrido, «P» una sonda propia del refuter y «M» una mutación propia.

| Escenario | Veredicto | Cómo | Evidencia (textual del refuter) | Verificó |
|---|---|---|---|---|
| GE-E01 | sostenido | T,P | `test_ge_e01_camino_feliz` y `…_por_cli` (sale con 0); probe `dos_seguidos_1` | B |
| GE-E02 | sostenido | T,P,M | `test_ge_e02`; probe serial sin solapes; GM-01 en rojo | B |
| GE-E03 | sostenido | T,M | `test_ge_e03` (incluye el registro alterado); GM-02 en rojo | B |
| GE-E04 | sostenido | T,P,M | `test_ge_e04`; probe `orden`; GM-01 en rojo | B |
| GE-E05 | sostenido | T,M | `test_ge_e05` y `…_por_cli`; GM-03 en rojo | B |
| GE-E06 | sostenido | T,M | `test_ge_e06` y `…_por_cli`; GM-03 en rojo | B |
| GE-E07 | sostenido | T,P,M | `test_ge_e07`; probe `dos_seguidos_2`; GM-03 en rojo | B |
| GE-E08 | sostenido | T,P,M | `test_ge_e08` y `…_por_cli` (sale con 2); probe con 9 variantes; GM-06 en rojo | B |
| GE-E09 | sostenido | T,P | `test_ge_e09` y `…_por_cli`; probe `sin_plan`, `no_json`, `otra_taskkey`, `ids_repetidos` | B |
| GE-E10 | sostenido | T,M | `test_ge_e10`; GM-01 en rojo | B |
| GE-E11 | sostenido | T,M | `test_ge_e11`; GM-08 completa no aplicada (O4) | B |
| GE-E12 | sostenido | T | `test_ge_e12`: llamadas `[A, A, B]`; el AST no muestra ninguna llamada a la compuerta desde `grafo.py` | B |
| GE-E13 | sostenido | T | `test_ge_e13` | B |
| GE-E14 | sostenido | T | `test_ge_e14` | B |
| GE-E15 | sostenido | T | `test_ge_e15` | B |
| GE-E16 | sostenido | T | `test_ge_e16` | B |
| GE-E17 | sostenido | T,P | `test_ge_e17`; mi AST (`estatico.py`) | B |
| GE-E18 | sostenido | T,P,M | `test_ge_e18` y `…_por_cli`; probe `failfast`; GM-08 en rojo | B |
| GE-E19 | sostenido | T | `test_ge_e19` y `…_por_cli` (cancelación desde otro proceso) | B |
| GE-E20 | sostenido | T,P,M | `test_ge_e20` y `…_por_cli`; probe `a_cancelled`/`a_rejected`; GM-04 en rojo | B |
| GE-E21 | sostenido | T | `test_ge_e21` (archivos de F′ idénticos byte a byte) | B |
| GE-E22 | sostenido | T | `test_ge_e22` | B |
| GE-E23 | sostenido | T,P,M | `test_ge_e23`; probe H3 con y sin reconciliar; GM-09 en rojo | B |
| GE-E24 | sostenido | T,P,M | `test_ge_e24`, las dos mitades; probe H5 (C independiente y B dependiente); GM-11 y GM-11b en rojo | B |
| GE-E25 | sostenido | T,P | Seis tests `test_ge_e25_*`; probe H7 directo (`REJECTED PLAN_CHANGED`, sin `entrega.json` ni `proceso.json`, 0 invocaciones); t72 546/546; `t4_compara.py` | B |
| GE-E26 | sostenido | T,P | `test_ge_e26`; probe H1 (claves anidadas invertidas, indent 7, CRLF, `ensure_ascii`) y H2 (compacto) | B |
| GE-E27 | sostenido | T,P | `test_ge_e27`; probe H4 (vacío, mitad, ¾, `[]`) | B |
| GE-E28 | sostenido | T, P, M | P2 encuentro 30/30: uno gana, el otro `GRAPH_ALREADY_ACTIVE` por CLI con rc 2, sin carpeta `grf_`. Rojo con M20 (4) y M21 (GM-13). Lo que no aserta el test (rc 2) lo cubre P2 cli | C |
| GE-E29 | sostenido | T, P, M | P2 cli 30 vueltas, en las 30 hubo rechazo; muestreo continuo, máximo 1 ACTIVE. Rojo con M20 (36) | C |
| GE-E30 | sostenido | T, M | Rojo con M17 (7c y 7d fuera). Solo 7c o solo 7d no enrojece: se cubren entre sí | C |
| GE-E31 | sostenido | T, M | Rojo con M13 (3) | C |
| GE-E32 | sostenido | T, P, M | P1b, 18 vueltas con reserva simultánea (ganó el grafo 6, la manual 12): siempre 1 turno, 1 entrega y 1 Host. Rojo con M22 | C |
| GE-E33 | sostenido | T, P, M | Rojo con M13. P3 G3b y P5 dejan la REQUESTED intacta | C |
| GE-E34 | sostenido | T, M | Rojo con M13 (2) | C |
| GE-E35 | sostenido | T, M | Rojo con M14 (3) | C |
| GE-E36 | sostenido | T, P, M | P3 G1 (13/13). Rojo con M04 | C |
| GE-E37 | sostenido | T, P | P3 G2: el exe huérfano no lo nombra ningún turno; A sale con otro id | C |
| GE-E38 | sostenido | T, P | P3 G3a: el residuo sin turno queda (es nuevo) y no hay doble turno | C |
| GE-E39 | sostenido | T, P | P3 G3b: el huérfano nombra la REQUESTED y el comando; el nuevo cierra TASK_EXECUTION_OPEN; A intacta byte a byte | C |
| GE-E40 | sostenido | T, P | P3 G5 con `taskkill /F` de la CLI real: B queda FAILED HOST_INTERRUPTED y no hay invocación nueva | C |
| GE-E41 | sostenido | T, P, M | P3 G6: adopta a y b, despacha solo c, 3 invocaciones. Rojo con M04 | C |
| GE-E42 | sostenido | T, P, M | P3 G7: el huérfano cierra SUCCEEDED, no GRAPH_INTERRUPTED. Rojo con M03 (7) y M04 | C |
| GE-E43 | sostenido | T, P, M | P2d y P4c E46: el cancelador sin candado escribe la marca y no el terminal. Rojo con M01, M18 y M20 | C |
| GE-E44 | sostenido | T, P, M | P5 (Ctrl-C en 5 puntos y Host con 143). Rojo con M07 | C |
| GE-E45 | sostenido | T, P, M | P5 (crear, Vida, post-publicación). Rojo con M11 y M12 | C |
| GE-E46 | sostenido | T + P + M | Test y test por CLI verdes. M03b dio rojo. Probe `7a` 3/3: `CANCELLED`, B sin turno | G (tras las enmiendas; C había dado «sostenido») |
| GE-E47 | sostenido | T + P + M | Verde. M07 y M09 (ventana de 1 s) dieron rojo. Probe `running` 4/4 y 7f con Host ≥1 s 38/38: B `CANCELLED`, Host muerto | G (tras las enmiendas; C había dado «sostenido») |
| GE-E48 | sostenido | T + P + M | a), b) y c) asertan lo que dice el texto enmendado. M02, M04 y M07 dieron rojo. Lo que el escenario «no asevera» lo observé y coincide con 17.4 (F1-ab 3/3 y F1-abc 3/3) | G (tras las enmiendas; C había dado «contradicho») |
| GE-E49 | sostenido | T + P + M | Verde. M04 y M08 dieron rojo. Probes `terminal` 3/3 y huérfano `terminado` 3/3: `SUCCEEDED` con `cancelRequested: true` | G (tras las enmiendas; C había dado «sostenido») |
| GE-E50 | sostenido | T + P + M | Verde. M06 dio rojo. Probe `ilegible`: sobre un terminal sale 0 y no cambia ningún archivo. `dos-vivo` 10/10: una sola marca, los dos salen 0 | G (tras las enmiendas; C había dado «sostenido») |
| GE-E51 | sostenido | T + P + M | Verde. M08 y M10 dieron rojo. Probe huérfano `requested` 3/3: B y el GraphRun `CANCELLED`, `cerradoAqui: true` | G (tras las enmiendas; C había dado «sostenido») |
| GE-E52 | sostenido | T + P + M | Verde. M01 dio rojo. Probe `manual` 3/3: solo se pidió cancelar a B; la manual `RUNNING` Y termina `SUCCEEDED` sin pedido; la `REQUESTED` Z queda intacta | G (tras las enmiendas; C había dado «sostenido») |
| GE-E53 | sostenido | T,P,M | `test_ge_e53`; `n1_orq.py` 30/30; en rojo con `mut-1` | B |
| GE-E54 | sostenido | T,P,M | `test_ge_e54`; `n1_bordes.py` (umbral ±2 s, temporales de `grf_`); en rojo con `mut-2` | B |
| GE-E55 | sostenido | T,M | `test_ge_e55`; en rojo con `mut-2` (`FileNotFoundError` en el `os.link`, el ítem 14) | B |
| GE-E56 | sostenido | T,P | `test_ge_e56`; `r5.py`: win32 da `REJECTED CAPABILITY_UNAVAILABLE`, sin `entrega.json`, 0 invocaciones; `detail` = «tests.run (el Host no ofrece Bash en win32)»; el GraphRun cierra `WORK_UNIT_NOT_SUCCEEDED` | B |
| GE-E57 | sostenido | T,P | `test_ge_e57`; `r5.py` en linux y darwin: SUCCEEDED, `--tools Bash,Skill`, también por GraphRun | B |
| GE-E58 | sostenido | T,P | `test_ge_e58`; `r5.py` `grafo_win32_sin_tests` da SUCCEEDED | B |
| GE-E59 | sostenido | T | `test_ge_e59`; ME-E57 en t72 | B |
| GE-E60 | sostenido | T+P+M | 4 tests releídos y la suite 73 completa: 1720/1720. P-E60-BARRIDO: suite 73 entera, 140 `result.json` válidos (71 SUCCEEDED, 52 FAILED, 17 CANCELLED), 173 `inicio.json`, 284 despachos, 0 errores. `mut-5` (despachos +2): 6 rojas | A |
| GE-E61 | sostenido | T+P+M | P-E61 con 3 GraphRuns reales: no aparece ningún archivo nuevo fuera de `grafos/` ni del registro de Executions; no hay `state.json` de grafo; cada destino de `os.link` es único; no hay `os.replace` en `bin/ejecucion`. P-WO: 25/25 carreras de 4 procesos, gana uno solo y no queda temporal; `mut-1` (`os.replace`): 20/25 en rojo. `mut-7`: lo detectan el audit hook, E64/ME-E46 y E60 | A |
| GE-E62 | sostenido | T+P+M | P-E62: GraphRun real con el Host escribiendo dentro de `grafos/`; la evidencia de cada Execution no lista nada de `.claude/ejecuciones` y ninguna sonda de Task 4 toca `grafos/`. `mut-8`: 8 rojas | A |
| GE-E63 | sostenido | T+P+M | P-CLI: 12 controles. P-T4, misma secuencia de 21 pasos por CLI con el bin de `e33b41b` y con el actual: 14 pasos idénticos; los otros 7 difieren solo por R5 (unidad `t` y sus líneas en `--estado`) o por F2′ (un temporal nuevo que se conserva). `mut-6`: rojo | A |
| GE-E64 | sostenido | T+P+M | Suites 72: 546/546, 64_modelo: 1046/1046, 65_contrato: 674/674, 71: 276/276. AST y `--help`. `mut-7` y `mut-11` en rojo | A |
| GE-E65 | sostenido | T+P+M | `git hash-object` igual al blob de `e33b41b` para los 6 archivos y para VERSION, CHANGELOG, UPGRADE, install, manifest y tool_policy. 23 códigos, `PRECEDENCIA`, `ESTADOS`, `TRANSICIONES`, clave y huella idénticos en tiempo de ejecución, base contra actual, también con `grafo` importado. `mut-10` (ADR-0015): rojo | A |
| GE-E66 | sostenido | T+P | Instaladores: 73 .ps1 16/16, 63 188/188, 72 12/12. Instalé yo la base y el actual: lock 292 → 294, la diferencia son exactamente `grafo.py` y el schema, con hash igual a la fuente, y ninguna basura nueva frente a la instalación base | A |
| GE-E67 | sostenido | T+P+M | El mapa de contextos sigue con los mismos contextos (no hay BC nuevo); conceptos 83 → 85; GraphRun dentro de Execution; la serialidad se expresa como "de a una Execution propia"; la fila run/corrida está enmendada; ADR-0016 revisa ADR-0015, que conserva su hash. `mut-9`: rojo | A |
| GE-E68 | sostenido | T+M | Leí el test (tiene control no vacuo); `mut-4`: 3 rojas | A |
| GE-E69 | sostenido | T+P+M | Ver GE-I24 | A |
| GE-E70 | sostenido | T+P+M | P-CLI: huérfano `ACTIVE` con los dos comandos; los ILEGIBLE salen sin comandos; `--cancelar` sobre ILEGIBLE por CLI da 2 y no escribe; un GraphRun nuevo termina SUCCEEDED sin tocarlos. `mut-2`: rojo | A |
| GE-E71 | sostenido | T, P, M | P1 variantes i ×3 y ii ×2 (28/28 cada una): b y x evidencian `CHANGES_UNATTRIBUTABLE` con `files: []`, y cada una detecta a la otra por `otras_entregadas` (sin suponer simetría). Rojo con M16 | C |

**Escenarios con fila: 71 de 71 · 71 sostenidos · 0 contradichos · 0 leídos · 0 sin sustento · 0 sin clasificar.**


**Sobre GE-E48 (leer con honestidad):** la parte C lo dio `contradicho` y la parte E también (b). Hoy figura `sostenido` porque F y G lo verificaron sobre
el texto enmendado, que **dice menos que el original**: ver «Qué pasó con GE-E48 y con §17». El código que se verificó es el mismo desde la parte A. La fila de arriba es la de G;
las demás filas de E46 a E52 también son las de G, y C las había dado `sostenido` salvo GE-E48. Entre G y K, GE-E48 solo cambió en dos referencias (lo comprobó la parte J).


## Invariantes (GE-I01 a GE-I31)

| Invariante | Veredicto | Evidencia (textual del refuter) | Verificó |
|---|---|---|---|
| GE-I01 | sostenido | AST: `grafo.py` llama del registro solo marcas y lecturas (ni `crear`, ni `reservar`, ni escrituras directas), y del motor solo `ejecutar`/`cancelar`/`recuperar`. Probe `serial_residual.py`: nada cambia fuera de `.claude/ejecuciones` salvo lo que escribe la compuerta (O3) | B |
| GE-I02 | sostenido | Diff de protegidos vacío; t72 546/546; `t4_compara.py`: motor sin parámetros nuevos igual a `e33b41b` en 7 de 8 escenarios, el octavo es R5; la rama `--unidad` del diff de la CLI no cambia | B |
| GE-I03 | sostenido | E01/E21/E22 en t73; `huella.py`: F atada al plan inicial en los 15 casos | B |
| GE-I04 | sostenido | `huella.py`: ninguna `entrega.json` bajo otra huella en ningún caso; GM-11 la pone en rojo | B |
| GE-I05 | sostenido | `huella.py` H3/H5/H6: cierra sin despachar más | B |
| GE-I06 | sostenido | Snapshot del proyecto antes y después; AST sin imports de flujo, compuerta ni contabilidad | B |
| GE-I07 | sostenido | `admision.py` (probe): 11 estructuras malas, ningún `grf_`, Execution, turno ni residuo | B |
| GE-I08 | sostenido | E02/E04/E10; probe `orden` (`[z,m,a]` da `a,z,m`); GM-01 en rojo | B |
| GE-I09 | sostenido | E03; GM-02 en rojo | B |
| GE-I10 | sostenido | E05/E07/E20; probe `segundo_no_reintenta` (1 turno para B, 0 invocaciones); GM-03 y GM-04 en rojo | B |
| GE-I11 | sostenido | Probe serial con 4 unidades: intervalos sin solape. Carrera residual con procesos reales: B y X solapan, una sola marca, cero propias abiertas al volver B, `TASK_EXECUTION_OPEN` nombrando a X en la variante i | B |
| GE-I12 | sostenido | E11/E18; probe `failfast_independiente` (`z` no se despacha); GM-08 en rojo | B |
| GE-I13 | sostenido | `validar_resultado` en cada GraphRun de mis probes; E06 | B |
| GE-I14 | sostenido | Releí y corrí `test_gd05_*` y los tests de GE-E49 y GE-E50. M13 (el terminal se pisa) puso rojo `test_gd05_el_terminal_se_escribe_una_vez…`; M04 (la cancelación tardía gana) puso rojos GE-E48 c) y GE-E49. En la carrera K (20 corridas) el hash de `result.json` nunca cambió | G (tras las enmiendas; antes C) |
| GE-I15 | sostenido | P2: 30 vueltas por CLI y 30 con encuentro, nunca más de 1 ACTIVE ni dos conductores. P2d: `vivo.lock` se abre con `O_CREAT` y sin `O_EXCL`, nadie lo borra, pesa 0 bytes (sin pid ni fecha). Con el candado de otro proceso, `--grafo` sale `GRAPH_ALREADY_ACTIVE` y no toca nada. Rojo con M20 (46 filas) y M01 | C |
| GE-I16 | sostenido | P3 G1–G7: el huérfano solo gana `result.json`, una segunda corrida no lo toca, y seguir crea otro GraphRun. Rojo con M04 (reanuda) | C |
| GE-I17 | sostenido | Traza P2d: ninguna marca final se abre para escribir; 5 `os.link` (inicio, 001–003, result); ningún rename; no hay `state.json`. Rojo con M15 | C |
| GE-I18 | sostenido | Código: la marca en `grafo.py:643-648`, antes del bucle `:650`; el pedido sale solo de `motor.cancelar` (`:277`). M01, M02, M03b, M06 y M07 dieron rojo. Probe de orden: en 130 corridas ningún pedido propio es anterior a la marca del grafo, y el mismo probe dio rojo 2/2 contra M03a | G (tras las enmiendas; antes C) |
| GE-I19 | sostenido | La REQUESTED queda REQUESTED y sin `cancelacion.json`; la manual X no se cancela ni se marca; adopción con `dispatched: false` | B |
| GE-I20 | sostenido | Nueve códigos; el resultado del motor se ignora salvo `error.code` (ver O2) | B |
| GE-I21 | sostenido | P5: Ctrl-C en 5 puntos → GRAPH_INTERRUPTED, la interrupción sale, ningún despacho posterior y el candado queda libre. Host con 143 → WORK_UNIT_NOT_SUCCEEDED. Rojo con M07 (12 fallas en P5) | C |
| GE-I22 | sostenido | P5: `registro.crear` con OSError y `Vida` con OSError dan DISPATCH_FAILED con el exe de la marca; post-publicación da DISPATCH_FAILED con exe y RUNNING. P1b: si gana la manual, el conductor deriva. Rojo con M11, M12 y M22 | C |
| GE-I23 | sostenido | El test de E68 pasa; `mut-4` (copiar el `detail` de la Execution) lo pone en rojo, 3 aserciones. Barrido: 140 `result.json` de conductor validan contra un schema cerrado, sin `evidence`/`files`/`output`/`artifact` | A |
| GE-I24 | sostenido | E69 por API y por CLI; P-CLI confirma `ana` en `inicio.json` y en cada request; `mut-3` (`"graph"`) da 5 rojas | A |
| GE-I25 | sostenido | N1 con procesos reales: 30/30 y 10/10 misma clave; mutantes en rojo | B |
| GE-I26 | sostenido | `r5.py`: plataforma inyectada; el GraphRun no llama a `provee` | B |
| GE-I27 | sostenido | ME-E57 (ME-I29) verde en t72; GE-E59 verde | B |
| GE-I28 | sostenido | El AST de `grafo.py` no tiene ninguna llamada que escriba ni lance procesos; `--help` base y actual muestran los mismos 13 subcomandos; ME-E47, E-41 y EX-E50 en verde; `mut-11` (`import threading`) en rojo | A |
| GE-I29 | sostenido | P-E61 (audit hook con GraphRuns reales): todo lo escrito en `grafos/` lo escribe `registro.py`; `grafo.py` escribe 0 veces. P-E62: ninguna función de Task 4 toca `grafos/`. `mut-7` y `mut-8` en rojo | A |
| GE-I30 | sostenido | P-CLI: `--grafo --estado` sale 0 con el candado de la tarea tomado por otro proceso, no cambia ni hash ni mtime de nada, y el audit hook no ve ninguna apertura de `vivo.lock` ni escritura. `mut-2` (el estado sondea el candado) pone en rojo los tests del repo y mi probe | A |
| GE-I31 | sostenido | P1, 5 corridas: b y x solapados; nunca más de 1 marca ni más de 1 propia abierta; x sin cancelar, no REJECTED, no tomada como propia. Rojo con M16 | C |

**Invariantes con fila: 31 de 31 · 31 sostenidas · 0 contradichas · 0 leídas · 0 sin sustento · 0 sin clasificar.**


## Qué pasó con GE-E48 y con §17 (la historia, para que se lea con honestidad)

La parte C encontró que la spec prometía algo que el motor de Task 4 no puede cumplir: que una cancelación del grafo deja `CANCELLED` a la Execution en vuelo. Con la CLI
real (sondeo de 1 s) y un Host que termina antes de que el pedido lo alcance, la Execution queda `SUCCEEDED`. La raíz está en Task 4 (`proceso.esperar` solo mira el pedido
al comienzo de cada tramo de 1 s) y choca con su propio ME-I22. **No es un defecto del código de Task 5.** Cerrar la ventana de verdad exigía tocar Task 3/4, que la spec prohíbe.

**Quien encargó la Task (Nahuel Palacio, 15-10-2026) decidió resolverlo enmendando la spec con lo que de verdad se puede garantizar**, sin cambiar el código. Esa decisión es lo que
cambió el resultado de GE-E48 de `contradicho` a `sostenido`: **la spec se ajustó a lo que el código hace, no el código a la spec**. Cada enmienda quedó registrada en 27.1
(puntos J a R) con quién la pidió y quién la autorizó, y cada una la re-verificó un refuter distinto.

Corregir una promesa por vez no convergía: cada refuter, con un caso más extremo, desmentía otra celda de «resultado» o otra «garantía». Por eso el 15-10-2026 se eligió el
**arreglo estructural** (27.1 P): la sección 17 separa lo **normativo** (solo acciones del código de Task 5 que se cumplen siempre, §17.2 (a) a (f)) de lo **informativo** (§17.3 y §17.4:
observaciones, no normativas, casos vistos con la CLI de producción y el Host falso, sin tono de promesa). Las dos últimas pasadas (27.1 Q y R) solo **borraron o suavizaron**: ninguna
afirmación nueva.

| Parte | Hallazgo bloqueante (resumen) | Lo resolvió | Lo re-verificó |
|---|---|---|---|
| C | GE-E48 b): con la CLI real (`INTERVALO = 1.0`, `grafo.py:602`), B queda `SUCCEEDED` en 4 de 10 vueltas; el test daba verde porque usa `intervalo=0.2` y un Host que duerme 60 s. Más, sin bloquear: la cancelación contra un terminal deja la marca escrita después del terminal (O-1) | 27.1 J y K | E |
| E | GE-E48 b) y la garantía 2 de §17.2: un Host que sobrevive a la vuelta del cancelador y sale enseguida termina `SUCCEEDED` con el pedido escrito (`proceso.py:63-66`, `:72`; choca con T4 ME-I22) | 27.1 L | F |
| F | Ventana de 60 s del cancelador: si el conductor tarda más de 60 s entre 7f y el turno de B, el cancelador sale 0 con «su conductor sigue…» y B corre entera | 27.1 M (auditoría completa de §17; nace §17.4) | G |
| G | §17.4 límite 8 b) (el `--grafo` siguiente recupera la `RUNNING`, no se detiene con `TASK_EXECUTION_OPEN`) y un Host cortado (130/143) con el pedido persistido: el motor sí vuelve a mirarlo (`motor.py:335`) | 27.1 N | H |
| H | Un Ctrl-C real sobre el motor después del `wait` también mira el pedido (`motor.py:296-297`) | 27.1 O (la spec deja de afirmar universales sobre las entrañas de Task 4) | I |
| I | Cuatro frases: §17.1 razona por la Execution y no por el nodo (caso P1b: Execution propia `CANCELLED`, GraphRun `SUCCEEDED` con `cancelRequested: true`); la oración general de §17.4 y el límite 8; el ejemplo de 15.4 omite `CHANGES_UNRESOLVED` con HEAD sin commits; GD-11 paso 3 afirma sin condición lo que hace `motor.cancelar` | 27.1 P (arreglo estructural) | J |
| J | Tres afirmaciones normativas escritas en la octava pasada: F-J1 (oración final de §17.2: «Task 5 solo llama a `motor.cancelar` si una vuelta del cancelador la encuentra abierta», falsa porque un `--grafo` que cierra un huérfano también la llama), F-J3 (GD-11 paso 4: `canceladas` como las Executions sobre las que llamó a `motor.cancelar`), F-J2 (norma (a): el catálogo de secretos no se valida con un GraphRun terminal) y O-2 | 27.1 Q y R (solo borrar o suavizar) | K |
| K | Ninguno. Seis observaciones que no bloquean (OBS-1 a OBS-6) | — | — |

**Qué quedó en pie de lo que la spec dice sobre cancelación (§17.2, lo normativo):** la marca se escribe una sola vez y antes de cualquier otra cosa; el candado y el sondeo de la tarea;
el conductor lee la marca en 7a y 7f; el terminal sale de la regla de cierre por el estado de cada nodo; el `result.json` se escribe una vez y gana el primero; el cruce de las dos escrituras
(al menos uno ve al otro). Todo lo demás (qué terminal escribe una Execution propia, si el pedido queda persistido en ella, si el Host muere) es observación y no se promete.


## Sondas adversarias

Cada refuter escribió sus sondas en su carpeta temporal (`%TEMP%\refuter-t5-<parte>\probes\`), fuera del repo. Acá van las tablas textuales de las partes que verificaron escenarios; las de E a J están en sus informes y se resumen en la historia de arriba, y las de K abajo.

### Parte A

Todos en `%TEMP%\refuter-t5-A\probes\`.

| Id | Ataca | Resultado |
|---|---|---|
| `probe_e61.py` | Escrituras de un GraphRun real, atribuidas por audit hook | Solo `registro.py` escribe en `grafos/`. `.claude/runtime/knowledge-refresh.json` cambia por la admisión, igual que en el control de Task 4 (`probe_e61_control.py`) |
| `probe_wo.py` | Write-once de inicio, despacho (dos formas), cancelación y resultado, con 4 procesos | 25/25 OK; `mut-1`: 20 rojas |
| `probe_inmutable.py` | Corte real, cierre del huérfano, `--cancelar` sobre terminales, `--estado` y otro `--grafo` | Ningún archivo de `grafos/` cambia ni se borra después de escrito |
| `probe_t4.py` y `cmp_t4.py` | Task 4 base contra actual por CLI: `--unidad`, `--estado`, `--cancelar exe_` (REQUESTED, RUNNING vivo, terminal), `--recuperar` sobre una huérfana matada, residuos | Solo difieren R5 y F2′, que son deliberados |
| `probe_cli.py` | GE-E63 y GE-E70 por el comando real | 23/23 |
| `probe_e62.py` | `grafos/` lleno, con el Host escribiendo adentro | Pasa |
| `probe_toctou.py` | `--cancelar` contra el terminal | Ver la observación 3 |
| `t3_valores*.py`, `hash_protegidos.py`, `mc_check.py`, `ast_grafo.py`, `help_cmp.py` | Estáticos y de valores | Pasan |

### Parte B

| Id | Qué ataca | Resultado |
|---|---|---|
| P-N1 | `n1_orq.py`: A detenido entre `O_EXCL` y `_bloquear`; B (otro proceso) corre `limpiar_temporales`, `barrer` y `recuperar`, y retiene el candado si toca la carpeta de A | Referencia 30/30: B nunca sondea la carpeta de A; el temporal de 595 s queda y el de 605 s se borra; el residuo viejo se barre y el nuevo ni se sondea; 0 fallas de creación; ninguna clave con dos turnos. `mut-1` y `mut-2`: 3/3 fallan con `ErrorDelComando (PermissionError)` |
| P-N1c | `n1_misma_clave.py`: C pide la misma unidad con A en la ventana | 10/10: un turno, una carpeta, A recibe `DUPLICATE_EXECUTION` sin excepción |
| P-BORDE | `n1_bordes.py` | U−2 s no se sondea ni se borra; U+2 s se sondea y se borra; temporales de `grf_`: sin candado da `RegistroInvalido`, con candado solo los vencidos |
| P-R5 | `r5.py` + `host_contador.py` | Ver E56–E58. `provee` se llama solo desde `admision.py` y siempre después de la marca y el turno de su unidad |
| P-HUELLA | `huella.py` | Ver E23–E27 y H6: plan cambiado con B RUNNING → B SUCCEEDED y SATISFIED bajo F, cierre `PLAN_FINGERPRINT_CHANGED`, C no se despacha |
| P-ADM | `admision.py` | Tabla de GD-15: CANCELLED/REJECTED → `WORK_UNIT_NOT_SUCCEEDED`; REQUESTED o turno ilegible → `TASK_EXECUTION_OPEN`; abierta de otra clave → 7d |
| P-T4 | `t4_compara.py`, `e33b41b` contra la construcción | Igual salvo `tests.run` en win32 (R5). La diferencia en `estado` es solo de orden |
| P-GM11 | `mut-3` y `mut-4` contra `test_ge_e24` | Rojo solo en la variante reconciliada: el Host recibe C y C queda SUCCEEDED bajo F2 |

GM-11 no es tautológica ni irrelevante. Toda forma observable de violar la propiedad (pasar la huella releída, o no pasar ninguna) da rojo. Las variantes que no dan rojo son las dos que la spec declara equivalentes en §33.

### Parte C

| Id | Qué ataca | Cómo | Resultado | Script |
|---|---|---|---|---|
| P1 | Carrera residual §15.4 | Conductor en un proceso; `--unidad x` por CLI real después de 7d; muestreo de marcas y propias | 5/5 sostenido | `p1_carrera_residual.py` |
| P1b | Misma clave | Conductor y manual detenidos en `antes_de_reservar`, soltados a la vez | 18/18: un turno, una entrega | `p1b_misma_clave.py` |
| P2 / P2c / P2d | Candado, huérfano, `--estado` | 2 CLIs a la par; encuentro; traza de auditoría; candado de otro proceso | Sostenido. Observación O-1 | `p2_candado.py`, `p2c_huerfano.py`, `p2d_estado_traza.py` |
| P3 | G1–G7 | `os._exit` en gancho; G5 con `taskkill /F` | 7/7 | `p3_recovery.py` |
| P4v / P4c | Ventana 17.2 y casos de §17.3 | CLI real de `--cancelar grf_…` | **GE-E48 (b) falla con Host rápido**; el resto sostenido | `p4_ventana.py`, `p4_cancelar.py`, `repro_ge_e48*.py` |
| P5 | E44 y E45 | Ctrl-C, Host con 143, OSError | 37/37 | `p5_e44_e45.py` |
| M01–M22 | Rojo de los tests y de mis probes | `mutar.py`, `correr_algunos.py` | 22 de 22 mutantes con rojo en algún test o probe; M08 (GM-12 literal) solo en los tests de GE-I15 (O-2) | `mut-tests*.log`, `mut-probes.log` |

### Parte G

Scripts en `%TEMP%\refuter-t5-G\probes`; corridas en `logs\*.jsonl`.

| Probe | Ataca | Resultado |
|---|---|---|
| `p_ventana` 7f→motor, Host inmediato / 0,3 / 0,5 / 0,8 / 1,0 / 1,3 / 1,5 / 5 / 60 s (108 corridas) | Garantías 2 y 3; límites 1, 2 y 3 | Hasta 0,8 s: el resultado del Host (con pedido propio, o sin él si el Host es inmediato). Desde 1,0 s: `CANCELLED` en todas. Con pedido y `SUCCEEDED`, el Host salió como mucho 0,646 s después del pedido, nunca un tramo entero. 0 violaciones |
| `p_ventana` antes del primer nodo, 7a y 7e–7f, con suelta inmediata y con >60 s (14) | Garantía 1, filas 1 y 5 de 17.3 | `CANCELLED`, sin Execution nueva |
| F1-ab / F1-abc / F1-texto y `reservar-finc` (conductor retenido >60 s) (9) | Límite 4; texto de la CLI | El cancelador sale 0 a unos 60,4 s, `sigue: true`, sin `canceladas`. Imprime «su conductor sigue: el pedido quedó escrito y lo va a cumplir. Mirá …». B corre entera sin pedido. A→B: `SUCCEEDED` con `cancelRequested: true`; A→B→C: `CANCELLED` |
| `menos60` (3); `entregar-3` y `entregar-finc` (REQUESTED con motor vivo) (6) | Filas `REQUESTED` y ventana | B `CANCELLED`; con REQUESTED, sin `entrega.json` |
| `matar` (5) | Límite 5 | Se cumple lo de la fila del cancelador cortado |
| `p_huerfano`: running, running-con-pedido, requested, terminado (12) | Paso 3a; límite 7 | `FAILED HOST_INTERRUPTED`, o `CANCELLED` si ya había pedido; el Host sigue vivo; GraphRun `CANCELLED` |
| `p_segundo` (2) | Fila «Dos veces» | El segundo cancelador le pide a B (archivo nuevo); la marca del grafo, con los mismos bytes |
| `p_varios`: exe, exe-y-grafo, exe-corto (10) | GC-22 | Coincide con el texto. Las marcas `v` de `exe` son un bug de mi chequeo (tupla mal armada); el `error` real es el que pide GC-22 |
| `p_varios`: ctrlc (4) | Límite 8 a) | 2/4 B queda `REQUESTED` y el GraphRun siguiente cierra `TASK_EXECUTION_OPEN` con el comando; 2/4 B `CANCELLED` |
| `p_varios`: errcmd (3) y `repro_limite8b` (1) | Límite 8 b) | **F-1** |
| `p_corte` 143 (3) y control salida 1 (3) | Límite 2 con un Host cortado | **F-2** |
| `p_varios`: ilegible, secreto | §16.1, redacción | Error del comando con exit 2 y sin escribir nada; el secreto queda redactado |

Las marcas `v` de `matar` (el cancelador no sale con 0) y de `terminal` (C tiene Execution) son esperadas por diseño del probe, no violaciones.

### Parte K

| Id | Qué ataca | Resultado |
|---|---|---|
| PA (`probe_a.py`), con la CLI de producción | Norma (a): `ACTIVE` / terminal / `ILEGIBLE` / inexistente / id malformado, cada uno con catálogo, sin catálogo y con catálogo ilegible | Las 14 combinaciones cumplen. `ACTIVE` sin catálogo o con catálogo ilegible: exit 2, no escribe y queda `ACTIVE`. Terminal sin catálogo: exit 0, no escribe. `pedidoPor` redactado, sin fuga. Ningún orden de validación desmiente la oración. |
| S2 | Norma (b): toma el candado a la primera, huérfano con B `REQUESTED` | Orden: lectura → marca → candado → `recuperar` → `cancelar(B)` → `CANCELLED`. La marca va antes de cualquier otra cosa. |
| S3 | Norma (b) con el GraphRun ya terminal al tomar el candado | `cerrar_huerfano` devuelve `None`, cero llamadas al motor. Se reproduce el residuo K (`cancelRequested: false` y la marca existe). |
| S4 ×13, más S4cli | Sondeo con el conductor vivo, B `RUNNING` y una manual `z` `RUNNING` a la vez | `motor.cancelar` solo sobre B, en cada vuelta, e intenta el candado otra vez. `z` termina `SUCCEEDED` sin pedido. |
| S1, S1c | §16.1 sin marca | Sin marca: 0 llamadas a `motor.cancelar`, B queda `REQUESTED`, el `result.json` nombra el comando para cancelarla, y el GraphRun siguiente se detiene con `TASK_EXECUTION_OPEN` y ese comando. Con marca: 1 llamada y B `CANCELLED`. |
| S7, S7b | §16.3: Ctrl-C al conductor, sin y con marca | Cero llamadas al motor después del Ctrl-C. GraphRun `FAILED GRAPH_INTERRUPTED` (sin marca) o `CANCELLED` (con marca). B queda `REQUESTED` (límite 8 a). Candado libre. |
| S8 | Dos `--cancelar` a la vez | Una sola marca con hash estable; los dos salen con 0; `marcaNueva` = [false, true]; ningún despacho. |
| S5a | Límite 4 | El cancelador sale con 0 a los 60,8 s, con «su conductor sigue…». B corre entera: `SUCCEEDED`, una invocación del Host, sin pedido. `CANCELLED` en 7a; C sin turno. |
| S5b | Límite 4, y otro `--cancelar` con el GraphRun `ACTIVE` | La segunda ventana sí llama: B `CANCELLED` con su pedido. |
| S6 | Límite 5: el cancelador se mata después de la marca | B `SUCCEEDED` con su propio resultado, sin pedido; `CANCELLED` en 7a. |

### RACES
S3, S4, S5a, S5b, S6 y S8 son carreras entre procesos reales, sincronizadas por marcas en disco, sin sleeps como sincronización. **Flakiness:** las primeras corridas de S2/S3 y una de S4 dieron un `TypeError` causado por **mi** instrumentación (reemplacé la clase del candado por una función). Después de corregirla con una subclase: S2 y S3 pasan, y S4 pasa 12 de 12 más la variante por CLI. No es del producto.

### REAL HOST READINGS
Ninguna.

### OBSERVATIONS (no bloquean)
- **OBS-1:** el límite 5 conserva «sin llamada, se vio la Execution en vuelo con su propio resultado», sin la condición "con el conductor vivo". Es de la misma naturaleza que O-2, pero es texto previo a Q y R y es cierto como observación del caso visto (S6).
- **OBS-2:** la norma (b) dice «si lo toma, cierra el huérfano como §16.1». Con el GraphRun ya terminal no hay huérfano y no se llama a nada (S3). Es coherente con GD-11 paso 1 («§16.1 no toca un GraphRun que no está `ACTIVE`») y con el «(o ya cerró)» del paso 3. La redacción se puede mejorar, pero no es falsa.
- **OBS-3:** la referencia de GD-11 paso 4 («`canceladas`: ver §17.3 y §17.4») no es colgante: la observación 1, la fila de la ventana y el límite 4 nombran el campo. Pero ninguna lo define. Dato de S2: cuando el cancelador cierra el huérfano y llama a `motor.cancelar` sobre B, `canceladas` queda `[]`; nada del texto actual lo contradice.
- **OBS-4:** GD-11 paso 4, «la CLI imprime, tal cual, …», describe la salida humana. Con `--json` sale el JSON con `sigue: true`. Es texto previo a Q y R.
- **OBS-5:** §16.1, «una `REQUESTED` propia sin motor (R2) queda abierta», se apoya en R2 de Task 4. Es cierto (S1) y su parte de Task 5, no llamar a `motor.cancelar`, también. Texto no tocado por Q ni R.
- **OBS-6:** hay 640 archivos `ge73-vuelta-*.guion.json` en `%TEMP%`, acumulados por varias corridas; no se pueden atribuir a una sola. Mi carpeta `tmp` de probes quedó vacía.

### FINDINGS
- **Bloqueantes:** ninguno.
- **No bloqueantes:** OBS-1 a OBS-6.

### TREE INTEGRITY
La foto del repo real antes y después es **idéntica** (812 archivos). La copia de referencia también quedó idéntica (0 diferencias).

### VERDICT COUNTS
| | sostenido | contradicho | leído | sin sustento |
|---|---|---|---|---|
| Ítems de K (integridad; coherencia) | 2 | 0 | 0 | 0 |
| Escenarios asignados a K | — | — | — | — |
| Invariantes asignadas a K | — | — | — | — |

La parte K no tiene escenarios ni invariantes asignados por rango.

SPEC VERIFIED


## Carreras

### Parte A

- Write-once: 4 procesos × 5 rondas × 5 marcas.
- `--grafo --estado` con el candado tomado por otro proceso.
- Corte con `os._exit` y su cierre.
- Cancelación contra terminal.

Todas pasaron en la primera corrida; no vi flakiness.

### Parte B

N1 con procesos reales (30 + 10 vueltas, sin flakiness, bajo carga) y carrera manual residual en sus dos variantes (sostenida). La carrera de dos `--grafo` y la de `--grafo` contra `--cancelar` son de otra parte.

### Parte C

| Carrera | Vueltas | Resultado |
|---|---|---|
| `--grafo` contra `--grafo` | 30 sin encuentro, 30 con encuentro | Nunca dos conductores ni dos ACTIVE |
| `--grafo` contra `--cancelar grf_…` sobre un huérfano | 12 | Seguro; O-1 en 7 de 12 |
| Cancelación y despacho (17.2) | modo a: 3; modo b: 5 + 10 (CLI), 10 (API a 0,2 s), 8 sin ganchos | **B SUCCEEDED en 4 de 10 y 1 de 5 con la CLI de producción**; 0 de 10 a 0,2 s; 0 de 8 sin ganchos |
| Manual de otra unidad | 5 | Sostenido |
| Manual de la misma clave | 18 | Sostenido |

Flakiness: ninguna en mis carreras, salvo la que depende del tiempo de GE-E48, que es el hallazgo.

### Parte G

| Carrera | Corridas | Resultado |
|---|---|---|
| K: cancelar contra el terminal | 20 | 3 en el residuo K, con el informe igual a la fila de 17.3 y `--estado` mostrando `cancelRequested: true`; 5 leyeron el terminal y no escribieron; 12 marcaron antes del cierre |
| Dos `--cancelar` sobre un conductor vivo / sobre un huérfano | 10 / 10 | Una sola marca nueva, un solo pedido por Execution, todo `CANCELLED`. El límite 8 c) no se reprodujo |
| Instante al azar, A→B→C con Hosts de 0,3 s | 30 | Ninguna Execution despachada después de la marca; a lo sumo una creada después de la marca; ninguna propia queda abierta |
| `--grafo` contra `--cancelar` sobre un huérfano | 10 | Sin un `ACTIVE` que quede, sin residuos; `GRAPH_ALREADY_ACTIVE` sin carpeta nueva |

### Parte K

S3, S4, S5a, S5b, S6 y S8 son carreras entre procesos reales, sincronizadas por marcas en disco, sin sleeps como sincronización. **Flakiness:** las primeras corridas de S2/S3 y una de S4 dieron un `TypeError` causado por **mi** instrumentación (reemplacé la clase del candado por una función). Después de corregirla con una subclase: S2 y S3 pasan, y S4 pasa 12 de 12 más la variante por CLI. No es del producto.

### REAL HOST READINGS
Ninguna.

### OBSERVATIONS (no bloquean)
- **OBS-1:** el límite 5 conserva «sin llamada, se vio la Execution en vuelo con su propio resultado», sin la condición "con el conductor vivo". Es de la misma naturaleza que O-2, pero es texto previo a Q y R y es cierto como observación del caso visto (S6).
- **OBS-2:** la norma (b) dice «si lo toma, cierra el huérfano como §16.1». Con el GraphRun ya terminal no hay huérfano y no se llama a nada (S3). Es coherente con GD-11 paso 1 («§16.1 no toca un GraphRun que no está `ACTIVE`») y con el «(o ya cerró)» del paso 3. La redacción se puede mejorar, pero no es falsa.
- **OBS-3:** la referencia de GD-11 paso 4 («`canceladas`: ver §17.3 y §17.4») no es colgante: la observación 1, la fila de la ventana y el límite 4 nombran el campo. Pero ninguna lo define. Dato de S2: cuando el cancelador cierra el huérfano y llama a `motor.cancelar` sobre B, `canceladas` queda `[]`; nada del texto actual lo contradice.
- **OBS-4:** GD-11 paso 4, «la CLI imprime, tal cual, …», describe la salida humana. Con `--json` sale el JSON con `sigue: true`. Es texto previo a Q y R.
- **OBS-5:** §16.1, «una `REQUESTED` propia sin motor (R2) queda abierta», se apoya en R2 de Task 4. Es cierto (S1) y su parte de Task 5, no llamar a `motor.cancelar`, también. Texto no tocado por Q ni R.
- **OBS-6:** hay 640 archivos `ge73-vuelta-*.guion.json` en `%TEMP%`, acumulados por varias corridas; no se pueden atribuir a una sola. Mi carpeta `tmp` de probes quedó vacía.

### FINDINGS
- **Bloqueantes:** ninguno.
- **No bloqueantes:** OBS-1 a OBS-6.

### TREE INTEGRITY
La foto del repo real antes y después es **idéntica** (812 archivos). La copia de referencia también quedó idéntica (0 diferencias).

### VERDICT COUNTS
| | sostenido | contradicho | leído | sin sustento |
|---|---|---|---|---|
| Ítems de K (integridad; coherencia) | 2 | 0 | 0 | 0 |
| Escenarios asignados a K | — | — | — | — |
| Invariantes asignadas a K | — | — | — | — |

La parte K no tiene escenarios ni invariantes asignados por rango.

SPEC VERIFIED


## Regresión de Task 3 y de Task 4

Textual de las partes A y B (las dos corrieron contra una copia de `git archive e33b41b` como línea base ejecutable):

- **Archivos protegidos:** `git hash-object` igual al blob de `e33b41b` para `contrato.py`, los dos schemas de ejecución, ADR-0013, ADR-0014, ADR-0015, `VERSION`, `CHANGELOG.md`, `UPGRADE.md`, `install.ps1`, `manifest.json`
  y `tool_policy.py` (parte A). `contrato.py` difiere en bytes solo por CRLF y su blob es igual.
- **Valores en tiempo de ejecución:** los 23 códigos, `PRECEDENCIA`, `ESTADOS`, `TRANSICIONES`, la clave y la huella son idénticos entre la base y el árbol actual, también con `grafo` importado (parte A).
- **Diff contra `e33b41b`:** no tiene otro cambio de comportamiento que N1 (F1 y F2′) y R5. El resto es aditivo: `_leer_plan` pasa a `leer_plan` sin otros llamadores; `execution_id` y `huella_esperada` son opcionales y van al final; la comprobación de
  huella esperada queda dentro de la condición 4, después de `CONTRACT_INVALID`, como pide `PRECEDENCIA`; las funciones nuevas del GraphRun no las nombra ninguna función de Task 4 (parte A).
- **Task 4 por la CLI real, base contra actual:** misma secuencia de 21 pasos (`--unidad`, `--estado`, `--cancelar exe_` sobre `REQUESTED`, `RUNNING` vivo y terminal, `--recuperar` sobre una huérfana matada, residuos): 14 idénticos; los otros 7 difieren solo por R5
  (unidad `tests.run` y sus líneas en `--estado`) o por F2′ (un temporal nuevo que se conserva) (parte A, `probe_t4.py`; parte B, `t4_compara.py`: «igual salvo `tests.run` en win32; la diferencia en `estado` es solo de orden»).
- **Suites de Task 3 y Task 4:** parte A: `72_motor_de_ejecucion` 546/546, `64_modelo_de_dominio` 1.046/1.046, `65_contrato_de_ejecucion` 674/674, `71` 276/276. Parte E, con el filtro por patrón de nombre de archivo (`-k 72`, `-k 64`, `-k 65`, `-k 71`, que agrupan más archivos): 546/546, 1.422/1.422, 958/958 y 276/276. ME-I29 sigue: ME-E57 y ME-E42 pasan en el árbol base y en el actual. El filtro `-k 64` (que lee la spec) se re-corrió con la spec final en la parte K: 1.422/1.422.
- **Instalador:** lock 292 → 294; la diferencia son exactamente `grafo.py` y el schema nuevo, con hash igual a la fuente, y ninguna basura nueva frente a la instalación base (parte A). `73-ejecucion-de-grafo-instalador.ps1` 16/16, `63` 188/188, `72` 12/12.
- **`motor.py`, `proceso.py`:** `proceso.py` no cambió desde `e33b41b` (parte E). Las líneas de `motor.py` que cita la spec se verificaron contra `e33b41b` (partes F, I).


## Suite completa


Ninguna corrida de la suite completa se hizo en el repo real: la suite rompe archivos versionados a propósito (`tests/casos/03-instalador.ps1`) y los restaura en un `finally`; se corrió siempre en copias aisladas, con la foto del árbol real idéntica antes y después.

| Corrida | PowerShell | Python | Total | Exit | Sobre qué |
|---|---|---|---|---|---|
| A | 932/932 | 44.590/44.590 | 45.522/45.522 | 0 | copia del árbol de la parte A (1 h 06 min) |
| B | 932/932 | 44.590/44.590 | 45.522/45.522 | 0 | copia del árbol de la parte B |
| D, corrida 1 | 932/932 | 44.590/44.590 | 45.522/45.522 | 0 | copia (74 min) |
| D, corrida 2b | — | — | — | 0 | copia; D no emitió informe final |
| G | 932/932 | 44.602/44.602 | 45.534/45.534 | 0 | copia del árbol con el código final (44 min); los 12 casos de más son aserciones nuevas de t73 por las enmiendas de GE-E48 |
| L, corrida 1 | — | — | — | cortada | sobre el árbol final; la máquina se suspendió de 17:05:08 a 19:55:07 (Kernel-Power 42/107, «Button or Lid») y al volver el límite de 2 h la mató. No muestra ningún defecto del producto |
| **L, corrida 2** | 932/932 | 44.602/44.602 | **45.534/45.534** | **0** | **árbol final** (la spec de la décima pasada y el código final), 56 min 43 s |
| **L, corrida 3** | 932/932 | 44.602/44.602 | **45.534/45.534** | **0** | **árbol final**, 45 min 03 s, con `TEMP`, `TMP` y `TMPDIR` aislados |

Corridas parciales posteriores, en copias, todas exit 0: E: `-k 73` 1.732/1.732, `-k 72` 546/546, `-k 64` 1.422/1.422, `-k 65` 958/958, `-k 71` 276/276; F: `-k 73` y `-k 64`; H, I, J y K: `-k 64` 1.422/1.422 y `-k 73` 1.732/1.732.

Las partes C y G corrieron además `-k 73` (1.720/1.720 en C, 1.732/1.732 en G). El 45.522 del builder se reprodujo de forma independiente en A, B y D; ninguna parte lo usó como evidencia.

**Sobre el árbol final:** la parte L corrió la suite completa dos veces, con exit 0 y 45.534/45.534, sobre una copia idéntica por hash a la que verificaron J y K (la foto del árbol real, 812 archivos, no cambió antes ni después). Ningún caso que lea `docs/cambios/` cambió de resultado por las diez pasadas de enmiendas.

**Nota sobre D y L:** el entorno trae `TMPDIR` apuntando al `%TEMP%` global y Python lo prefiere a `TEMP`/`TMP`: hay que fijar también `TMPDIR` para aislar los temporales de una corrida. D lo detectó (por eso detuve su 3.ª corrida, la que iba a medir el residuo con el temporal de Python aislado, porque A, B y K ya lo habían medido) y L lo corrigió en su corrida 3. En la corrida 2 de L el motor Python escribió 20 `ge73-*` y 236 `me72-*` en el `%TEMP%` global (no los borró: la regla es no tocar nada fuera de su carpeta).


## Observaciones (no bloquean)

Cada una la anotó un refuter y ninguna cambia un veredicto. Las que piden trabajo están, redactadas para `Pendientes/`, en la sección siguiente.

### GM-11, texto final (parte B)

GM-11 **no es tautológica ni irrelevante**: toda forma observable de violar la propiedad (pasar la huella releída, o no pasar ninguna) pone en rojo `test_ge_e24`; las variantes que no dan rojo son las dos que la spec declara equivalentes en §33.
La mutación solo da rojo en la variante reconciliada: el Host recibe C y C queda `SUCCEEDED` bajo F2. GE-E24 y GE-I04 quedan `sostenido`.

### GE-E61, cobertura parcial de su test (parte A)

Los tests que llevan el id de GE-E61 prueban solo las primitivas, y la mutación `mut-7` no los pone en rojo. La cláusula del «GraphRun real» la sostienen `E60` («exactamente GD-12»), `ME-E46` y la sonda `P-E61` de A
(audit hook sobre tres GraphRuns reales: todo lo escrito en `grafos/` lo escribe `registro.py` y `grafo.py` escribe 0 veces; ningún archivo nuevo fuera de `grafos/` y del registro de Executions). El escenario queda `sostenido`; el test que lo nombra es débil.

### Residuo en `%TEMP%` (partes A, B y K; solo medición)

| Medición | `ge73-vuelta-*.guion.json` | carpetas `me72-*` |
|---|---|---|
| Antes de las corridas de A | 280 (27,3 KB; del 14-10, entre 12:02 y 16:15) | 5.143 (24,6 MB; desde el 10-10) |
| Después de A | 440 (51 KB) | 7.252 (32 MB) |
| Parte B | 440 | 226 carpetas (compartido con las otras partes: no se puede atribuir) |
| Parte K | 640 | — |
| Parte L, al empezar | 662 | 9.871 |
| Parte L, después de su corrida 2 | 682 | 10.107 |
| Parte L, corrida 3 (carpeta aislada con `TMPDIR`) | 20 (uno por vuelta de GE-E29) | 236 (188 `.guion`, 37 `.json`, 1 carpeta `-shim` y sueltos) |

**Cada corrida completa de la suite deja 20 `ge73-vuelta-*.guion.json` y 236 entradas `me72-*` sin barrer** (medido en la carpeta aislada de L). El mecanismo es el mismo de N10: el guion se escribe en `proy.parent`
(el directorio temporal del que cuelga el proyecto de prueba) y nadie lo limpia. **Nada queda dentro del repo y no afecta ningún resultado.** `PENDIENTES-FH.md` nombra solo la suite 72; corresponde sumar la 73
(texto propuesto abajo). Las columnas de A, B, K y el comienzo de L son una medición mixta de varias corridas y varios refuters sobre el mismo `%TEMP%`; no se atribuyen a una sola.

### Trazabilidad de N1 y R5 en `Pendientes/` (partes A y B)

Los ítems de N1 y de R5 **salieron de `PENDIENTES-FH.md` durante la construcción** (§34, paso 15), antes de `close-a-version`; yo no toqué ese archivo. La trazabilidad alcanza: spec §3, §15.1 a §15.3, GD-21 y §27, más `git` en HEAD, donde los ítems siguen.
N1 y la mitad del ítem 14 dejan la frase «closed with Task 5 and goes to its version note»; R5 no la tiene y queda solo como «what is left of R5» en GP-02. **Todavía no hay nota de versión** en `docs/versiones/`: la escribe `close-a-version`, que no se ejecutó.

### Tests débiles (mutaciones que sobreviven)

- **GM-12 literal** (C, O-2): `O_EXCL` más borrar al soltar deja verdes GE-E28 y GE-E43; solo enrojecen los tests de primitiva de GE-I15. Un candado que no excluye sí los enrojece.
- **GM-16** (C, O-3): depende de la lectura; la lectura «7h sin mirar el registro» pone rojo GE-E32, la primera no.
- **M03a, M11, M05b** (G): propagar una vuelta antes de escribir la marca no lo detecta ningún test (el orden «marca primero» de GE-I18 lo sostiene solo la sonda del refuter); ningún test aserta la línea «su conductor sigue…» de la CLI; un `--grafo --estado` que sondea el candado con `msvcrt` directo no pone rojo GE-E70.
- **`motor.py:335`** (H): ningún test del repo ejerce esa línea con pedido (grep de `senal=True`).
- **Los tests de cancelación no corren con la configuración de producción** (C, O-4): usan `intervalo=0.2` y esperas cortas. Los refuters cubrieron E46, E47 y E49 a E52 con la CLI real (1 s / 60 s): todos verdes.

### Otras

- **`PLAN_UNREADABLE` y `GRAPH_PLAN_UNREADABLE`** (B, O1): un plan a medio escribir entre 7b y `al_pedir` cierra `ADMISSION_REJECTED` con `executionCode: PLAN_UNREADABLE`, y no `GRAPH_PLAN_UNREADABLE`. Coincide con 7h al pie de la letra y con la tabla de §12; GD-22 y §18 se pueden leer de otra forma. No hay despacho ni Execution. Queda sin resolver; el texto no cambió por esto.
- **`grafo.py:568`** (B, O2): copia `r.detalle` (el texto del rechazo de `leer_plan`) en el rechazo al arrancar. No decide con ese texto, se redacta y no se persiste.
- **`knowledge-refresh.json`** (A, B): lo reescribe la compuerta normativa dentro de la admisión de Task 4 (`os.rename` en `auto_refresh.py`), también en `motor.ejecutar`. No es del GraphRun ni es un archivo nuevo.
- **Parte K, OBS-1 a OBS-6:** el límite 5 conserva «sin llamada, se vio la Execution en vuelo con su propio resultado» sin la condición «con el conductor vivo» (texto previo a Q y R, cierto como observación del caso visto); la norma (b) dice «si lo toma, cierra el huérfano como §16.1» y con el GraphRun ya terminal no hay huérfano
  (coherente con GD-11 paso 1); la referencia de GD-11 paso 4 («`canceladas`: ver §17.3 y §17.4») no es colgante pero ninguna sección define el campo; GD-11 paso 4, «la CLI imprime, tal cual…», describe la salida humana (con `--json` sale el JSON con `sigue: true`); §16.1 se apoya en R2 de Task 4; 640 `ge73-vuelta-*.guion.json` en `%TEMP%`.
- **Menores de A:** hay `__pycache__` bajo checks/hooks tanto en la instalación base como en la actual; `--grafo` es un flag global de argparse; `limpiar_temporales_de_grafos` no mira la raíz de `grafos/`, donde nadie escribe temporales.
- **Ctrl-C antes de entregar** (C, O-5): deja la `REQUESTED` sin nombrarla en el `GRAPH_INTERRUPTED`; la nombra el `--grafo` siguiente. §16.3 no lo exige.

### Cómo quedó atribuida la enmienda de las pasadas Q y R

27.1 Q y R dicen que las autorizó «Nahuel Palacio, 15-10-2026, el arreglo estructural, en su forma mínima: solo borrar». Lo que decidió Nahuel Palacio ese día fue el **arreglo estructural** (separar lo normativo de lo informativo, 27.1 P), eligiéndolo entre cuatro opciones.
**La forma mínima «solo borrar» la fijé yo, quien coordina, dentro de esa decisión**, cuando le encargué esas dos pasadas a `harness-task-architect`; el usuario no aprobó Q ni R por separado. Además, en R3 (la cláusula del catálogo de secretos de la norma (a)) el architect **no borró la cláusula entera**:
la restringió a la rama «lee `ACTIVE`», porque borrarla dejaba falsa otra frase (con el GraphRun `ACTIVE` y sin catálogo el comando sale con rc 2 y no escribe); K comprobó las 14 combinaciones y la dio por cierta. La redacción de las dos filas se puede corregir si se prefiere que diga esto.


## Pendientes propuestos (todavía no están en `Pendientes/`)

`CLAUDE.md` pide que los pendientes de `Pendientes/` estén en inglés y que los registre `note-a-pending`. **No los registré**: `Pendientes/Fix-Harness/PENDIENTES-FH.md` está en el diff sin commitear de la construcción (N1 y R5 salieron de ahí) y la indicación de la verificación
fue no editarlo. Texto listo para pegar, en inglés:

1. **`proceso.esperar` lets the Host's exit win over a persisted cancellation request** (Task 4). `proceso.py:63-72` reads the request only at the start of each 1 s slice, and `wait` returns `TERMINO` as soon as the Host exits, so a request written mid-slice loses to a Host that exits in
   the same slice and the Execution ends `SUCCEEDED` with its `cancelacion.json` present. It contradicts T4 ME-I22 («request persisted before the run ends → `CANCELLED`»). Task 5 spec §17.2 / §17.4 documents it as an observation, not a promise. A real fix touches Task 4 (`proceso.py`, `motor.py`) and needs its own spec. Evidence: refuters C, E, F (probes `repro_ge_e48.py`, `probe_b_api.py`).
2. **The canceller's 60 s window ends before a slow conductor reaches the Execution** (Task 5, spec §17.4 limit 4). If more than 60 s pass between 7f and the turn of the unit, `--cancelar grf_…` exits 0 with «su conductor sigue…» and the unit runs to the end with its own result. It is documented as an observation. Evidence: refuters F and K (`vence.py`, S5a).
3. **Suite 73 (and suite 72) leak temporary directories in `%TEMP%`**, same mechanism as N10: the script file is written under `proy.parent` and never cleaned. Measured by refuters A, B, K and L (mixed on the same `%TEMP%`): 280 → 440 → 640 → 682 `ge73-vuelta-*.guion.json`, and 5143 → 7252 → 10107 `me72-*` entries (about 32 MB at the second point). Each full run of the suite leaves 20 `ge73-vuelta-*.guion.json` and 236 `me72-*` entries (measured in an isolated folder by L; note that Python prefers `TMPDIR` over `TEMP`/`TMP`, so an isolated run has to set all three). Nothing is left inside the repo. `PENDIENTES-FH.md` names only suite 72.
4. **Weak tests found by the verification** (add or tighten): the tests that name GE-E61 only cover the primitives; no test asserts that the marker is written before the first propagation sweep (M03a); no test asserts the CLI line «su conductor sigue…» (M11); `--grafo --estado` probing the lock with `msvcrt` directly does not turn GE-E70 red (M05b); GM-12 literal (`O_EXCL` plus delete on release) does not turn GE-E28 or GE-E43 red; no test exercises `motor.py:335` with a request; the cancellation tests run with `intervalo=0.2` instead of the production 1 s / 60 s.

Los cuatro quedaron registrados el 16-10-2026 en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en la sección «What the verification of graph execution left open», al cerrar la versión 0.33.0.


## Hallazgos bloqueantes

**En el estado final, ninguno.** Escenarios: 71 `sostenido`, 0 `contradicho`, 0 `leído`, 0 `sin sustento`. Invariantes: 31 `sostenido`. Los siete `contradicho` de coherencia de §17 (partes C, E, F, G, H, I y J) están resueltos por las enmiendas 27.1 J a R y los dos ítems de la parte K,
que verificó el texto final (SHA256 `1C6C72097B182F8FE30E168AF3E3F85D9642EE4EB1AAD4479A8DA3C16D3CB643`), quedaron `sostenido`.

**Qué no se verificó:** ninguna lectura de Host real (Task 5 no tiene escenarios de lectura). La cancelación, la recuperación y las carreras se probaron con el Host falso del repo, procesos reales y la CLI de producción; ningún refuter las corrió contra Claude Code real.

**Qué falta para cerrar la versión:** esto no cierra la Task por sí solo. Falta `close-a-version` (VERSION, CHANGELOG, UPGRADE, nota de versión en `docs/versiones/` con N1 y R5, suite final sobre el árbol, revisión de secretos, commit y tag), que hace `harness-release-closer`. Hasta entonces, todo sigue en el árbol de trabajo sin commitear.

## Veredicto

Closure criterion del encargo: `contradicho = 0`, `sin sustento = 0` y suite completa con exit 0. Se cumple sobre el árbol final: 71 escenarios y 31 invariantes `sostenido`, y la parte L corrió la suite completa dos veces con exit 0 (PowerShell 932/932, Python 44.602/44.602, total 45.534/45.534) sobre una copia idéntica por hash a la que verificó K, con la spec en su versión final.

**TASK 5 SPEC VERIFIED**
