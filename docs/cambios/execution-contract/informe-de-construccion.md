# Informe de construcción — execution-contract

**Escrito por:** la sesión que construyó el cambio · **Fecha:** 07-10-2026 · **Spec:**
[spec.md](spec.md) · **Línea de base:** 0.30.0 (`f9393cf`), con `HEAD` en `0f8b725`

📌 **Esto no es un veredicto.** Dice qué se construyó, cómo se probó y qué quedó abierto, para que
`harness-spec-refuter` lo contraste contra la spec. Quien construyó no verifica.

📌 **0.31.0.** Lo que sigue hasta *Scope* es la construcción original, sobre 0.30.0. La integración
con 0.31.0 (`fdca5ce`, 08-10-2026) está aparte, al final, en *Rebase / integración 0.31.0*.

## Resultado de la compuerta

```
.\tests\Invoke-Tests.ps1
790/790 pasaron (PowerShell).
39109/39109 pasaron.
39899/39899 pasaron.
exit=0 · 4882 s
```

Corrida el 07-10-2026 sobre el árbol de trabajo sin commitear, como un proceso aparte y con stdin
desde el dispositivo nulo. `pre-tool-use.py` y `zonas.py` tenían después el mismo hash que antes
(`61567f3` y `e996067`), y `.claude/ejecuciones/` no existe. Esta corrida tardó 4882 s y la anterior
1936 s. Entre las dos solo cambiaron la adaptación de `63-harness-unico-instalador.ps1`, la spec y
este informe, y la causa de la diferencia no se investigó. `VERSION`, `CHANGELOG.md` y `UPGRADE.md`
no se tocaron: son del cierre.

**La corrida anterior dio rojo: 39896/39899, exit 1, en 1936 s.** Python pasó entero, 39109/39109.
Fallaron tres aserciones de `63-harness-unico-instalador.ps1`:

- E-15, las rutas del lock (dos aserciones);
- E-16, el contenido de cada archivo instalado.

Las dos comparan un proyecto instalado contra 0.28.0, y este cambio instala cuatro archivos nuevos a
propósito. Se adaptó ese test (ver *Adaptaciones*) y la compuerta volvió a correr entera.

## Baseline

| | |
|---|---|
| `HEAD` inicial | `0f8b725`, en `main`, descendiente de `f9393cf`; los dos commits de diferencia tocan solo `README.md`, `docs/instalacion.md` y `terceros/LEEME.md` |
| `VERSION` | `0.30.0` |
| `git status` inicial | solo `docs/cambios/execution-contract/`, sin seguimiento: la spec |
| Estado de la spec al empezar | `especificado, para revisión`, con los cuatro ajustes de la revisión aplicados |
| Implementación previa de Execution | ninguna: no existían `bin/ejecucion/`, los dos schemas ni `.claude/ejecuciones/` |
| `orchestration-plan/2.0` | intacto: `git diff f9393cf` del schema y de `plan.py` vacío |

## Lo construido

| Artefacto | Qué es |
|---|---|
| `comun/schemas/execution-request.schema.json` (nuevo) | `execution-request/1.0`. La raíz cerrada, con los once campos de §10. La WorkUnit restringe seis campos y deja el resto al plan. `admission` está cerrada, con los valores que pasan; `blocked` no es un valor válido de `normativeGate` |
| `comun/schemas/execution-result.schema.json` (nuevo) | `execution-result/1.0`. La raíz cerrada, con los once campos de §11. `status` tiene solo los cuatro terminales. ExecutionError está en `$defs.error`, con `code` (los 22 de §14, en orden) y `detail`. `evidence` es `{repoRevisionBefore, repoRevisionAfter, changes}`, sin tiempos. `output` es `{path, fingerprint}`. `host` es opaco y sin enum |
| `harnesses/desarrollo/bin/ejecucion/__init__.py` y `contrato.py` (nuevos) | Las constantes de §22 y los validadores puros: `huella`, `clave_de_idempotencia`, `transicion_valida`, `validar_request`, `validar_resultado`, `validar_rechazo` y `validar_informe`. Leen solo sus dos schemas y el del plan. No escriben, no lanzan procesos, y no importan ni la refutación ni la contabilidad |
| `docs/dominio/modelo-canonico.md` | §26.1: Execution como décimo contexto, con sus ocho conceptos, sus diez campos cada uno, las seis relaciones, las seis desigualdades y el vocabulario. `## El límite de la ejecución`, reescrito. Una línea en `### Agent` y otra en `### WorkUnit` |
| `docs/adr/0014-el-contrato-de-ejecucion.md` (nuevo) | Aceptado, con las siete decisiones de §26.2. Revisa el punto 4 de ADR-0013 sin editarlo |
| `tests/casos/65_contrato_de_ejecucion.py` (nuevo) | EX-E01 a EX-E52, con EX-E33b y EX-E36b, y EX-E54. Cada aserción empieza con su id |
| `tests/casos/65-contrato-de-ejecucion-instalador.ps1` (nuevo) | EX-E53, instalando de verdad en `%TEMP%` |
| `tests/casos/64_modelo_de_dominio.py` | Cuatro adaptaciones, con su motivo (abajo) |
| `tests/casos/63-harness-unico-instalador.ps1` | Una adaptación, con su motivo (abajo) |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | La sección *What the execution contract found and left open*, con los cinco títulos de §33 y su evidencia. Una nota en *The canonical domain model closed with five loose ends*: su cuarto punto lo decide ADR-0014 |
| `docs/cambios/execution-contract/spec.md` | Solo el estado, las marcas `rojo visto` y el registro de mutaciones de §35. Las decisiones no cambiaron |

## Decisiones respetadas

- **El Plan 2.0 queda intacto.** `orchestration-plan.schema.json` y `plan.py` siguen iguales a
  `f9393cf`. Lo prueba EX-E41, que también corre E-13 a E-17 de Task 2 y compara su fuente con la de
  `f9393cf`.
- **El AgentReport es lo que entrega el Host Adapter.** Tiene `{declaredStatus, artifact}` y nada
  más. `validar_informe` no lee el `artifact`: lo prueba EX-E36b, con un `artifact` que dice
  `status: COMPLETE` y otro que trae un bloque `agentResult`.
- **`NORMATIVE_GATE_BLOCKED`.** Ningún código empieza con `GOVERNANCE`, y `normativeGate` acepta
  solo `allowed` y `unresolved`.
- **La atomicidad queda solo en el contrato.** No hay locks, índices, reservas, creación exclusiva
  ni almacenamiento. EX-I28, EX-F01, EX-F02 y P13 están en la spec y en el documento canónico, y son
  de la Task siguiente.
- **Los tiempos quedan fuera de la evidencia.** `evidence` tiene exactamente tres propiedades,
  ninguna de tiempo. `startedAt` y `endedAt` son los únicos tiempos del resultado (EX-E33b).
- **No hay Execution Engine.**
  - `dev-harness.py` sigue con sus once subcomandos;
  - ningún módulo de producción importa `ejecucion`;
  - no hay subprocess nuevo, ni SDK de modelos, ni concurrencia;
  - `.claude/ejecuciones/` no existe (EX-E49 a EX-E53).

## Adaptaciones a tests de Task 2

Cada una lleva un comentario en el test con la decisión que la causa y el escenario de Task 3 que
la protege. Ninguna saca una comprobación que siga siendo cierta.

| Test | Qué cambió | Por qué |
|---|---|---|
| `64` E-03 | Pide diez contextos en vez de nueve, con Execution en la tabla. Ya no pide que Execution figure aparte como límite reservado, ni que ningún concepto lo tenga como contexto. La función pasa a llamarse `test_e03_diez_contextos_con_execution` | ADR-0014 hace de Execution el décimo contexto. Lo de Execution lo protege EX-E44 |
| `64` E-05 | Pide 48 schemas en vez de 46 | ADR-0014 agrega `execution-request` y `execution-result`. EX-E45 |
| `64` E-05 (S4) | Lee la tabla 3.2 de la spec de Task 2 **más** la tabla de §22 de esta spec, que tiene las mismas columnas | Sin eso, S4 exigiría que la spec cerrada de Task 2 nombre schemas que trajo ADR-0014, y esa spec es historia |
| `64` E-06 | Pide las catorce desigualdades de Task 2 más las seis de §26.1 de esta spec: veinte. La regla de citar una ruta que existe vale para las veinte | ADR-0014 agrega seis desigualdades. EX-E46 |
| `64` E-09 | Los apartados del límite pasan a ser *Lo que existe ahora*, *Lo que todavía no existe*, *Lo que sigue intacto* y *Las tres preguntas, contestadas* | ADR-0014 hace existir el contrato |

Detalle de E-09:

- **Se conservan:**
  - los nueve anclajes de lo que existía;
  - los siete de lo que sigue sin existir;
  - los dos invariantes y las tres preguntas, con sus frases.
- **Salen** `` `Execution` `` y `ExecutionRequest` de *lo que no existe*: ahora existen.
- **Se suman** los anclajes de EX-E47.

Fuera de Task 2, y no prevista en la tabla de §34.1:

| Test | Qué cambió | Por qué |
|---|---|---|
| `63-harness-unico-instalador.ps1` E-15 y E-16 | E-15 espera las rutas de 0.28.0 sin los dos manifiestos **más** las cuatro del contrato, y 263 en vez de 259. E-16 saltea esas cuatro, como ya salteaba las que tocó Task 2 | El instalador copia `bin/` y `comun/schemas/` enteros, y el contrato llega a cada proyecto instalado por diseño (EX-E53) |

## Desvíos respecto de la spec

- **Se adaptaron cinco tests y no tres.** §27 de la spec decía que cambiaban tres asserts de Task 2:
  E-03, E-05 y E-09. También cambiaron:
  - E-06, por las seis desigualdades que pide la propia §26.1;
  - `63-harness-unico-instalador.ps1`, que es de Task 1, por los cuatro archivos que instala el
    contrato.

  §34.1 preveía este caso: "si la suite muestra otro test de Task 2 que dependa del límite
  reservado, se adapta igual, con su motivo". El de 63 no es de Task 2, y se adaptó con el mismo
  criterio.
- **EX-E38, EX-E41 y EX-E51 corren tests de Task 2 desde 65**, y comparan su fuente con la de
  `f9393cf`. Es la forma más directa de probar "siguen en verde sin cambios". Cuesta unos 40 s por
  corrida, casi todo en E-13 a E-17.
- **`validar_rechazo` también controla `detail`**: que no esté vacío y que tenga 300 caracteres o
  menos. Es la forma de ExecutionError de §14, no una coherencia nueva.
- **EX-E55 queda `no consta`.** Es la compuerta misma, como el E-49 de Task 2.

## Rojo visto

**56 de los 57 escenarios tienen rojo visto**, EX-E53 incluido. El que falta es EX-E55: es la
compuerta misma y queda `no consta`. El registro, con la mutación de cada escenario, está en §35 de
la spec.

Cómo se hizo, para cada mutación:

1. se copió el repo, con `.git`, a `%TEMP%`;
2. se corrió el test del escenario y se lo vio en verde;
3. se aplicó la mutación;
4. se lo corrió en un proceso nuevo y se contaron solo las aserciones del propio escenario;
5. se restauró el archivo, byte a byte.

Fueron 59 corridas de mutación y todas quedaron restauradas. El árbol versionado no se tocó.

La primera mutación de EX-E36b no contó: dejaba a `validar_informe` reventando con `KeyError`, y el
test caía por la excepción, no por la aserción. Se rehízo para que de verdad sacara el estado del
texto, y dio cuatro aserciones en rojo.

## Tests

Las corridas focalizadas, sobre el árbol final:

| Corrida | Resultado | Duración |
|---|---|---|
| `python tests/correr.py -k 65_contrato` | 537/537 | 66,0 s |
| `python tests/correr.py -k _modelo_de_dominio` | 987/987 | 121,7 s |
| `python tests/correr.py -k 63_harness_unico` | 180/180 | 34,6 s |
| `65-contrato-de-ejecucion-instalador.ps1`, aislado | 15/15 | 17,8 s |
| `63-harness-unico-instalador.ps1`, aislado | 188/188 | 319 s |

La compuerta entera está arriba.

## Controles estáticos finales

- `.claude/ejecuciones/` no existe en el repo.
- Ningún módulo de producción importa `ejecucion` (EX-E52).
- `contrato.py`:
  - no escribe, no lanza procesos y no importa `refutacion` (EX-E08, EX-E52);
  - con el resto de `bin/ejecucion/`, no importa `contabilidad` (EX-E38).
- Ningún SDK de modelos ni framework de agentes, y nada de concurrencia, en `bin/` ni en `comun/`
  (EX-E49, EX-E51).
- `git diff --name-only f9393cf` sobre los archivos prohibidos de la consigna está vacío:
  - `orchestration-plan.schema.json`, `bin/orquestacion/`, `dev-harness.py` y `bin/contabilidad/`;
  - los schemas de contabilidad, del ledger de seguridad y de la RefutationUnit;
  - hooks, checks, agentes y skills;
  - `install.ps1`, `manifest.json`, `VERSION`, `CHANGELOG.md` y `UPGRADE.md`.
- `pre-tool-use.py` y `zonas.py` tienen el mismo hash que en `HEAD` (`61567f3` y `e996067`),
  después de cada corrida de la compuerta.

## Archivos

Nuevos:

- `comun/schemas/execution-request.schema.json`
- `comun/schemas/execution-result.schema.json`
- `harnesses/desarrollo/bin/ejecucion/__init__.py`
- `harnesses/desarrollo/bin/ejecucion/contrato.py`
- `docs/adr/0014-el-contrato-de-ejecucion.md`
- `docs/cambios/execution-contract/spec.md` (de la especificación)
- `docs/cambios/execution-contract/informe-de-construccion.md`
- `tests/casos/65_contrato_de_ejecucion.py`
- `tests/casos/65-contrato-de-ejecucion-instalador.ps1`

Modificados:

- `docs/dominio/modelo-canonico.md`
- `Pendientes/Fix-Harness/PENDIENTES-FH.md`
- `tests/casos/64_modelo_de_dominio.py`
- `tests/casos/63-harness-unico-instalador.ps1`

No se hizo commit.

## Scope

La Task siguiente no empezó:

| | |
|---|---|
| Execution Engine | no |
| ExecutionAdmission implementada | no: es una regla escrita, con su precedencia en `contrato.PRECEDENCIA` |
| Persistencia de ejecuciones | no: `.claude/ejecuciones/` no existe y nada escribe un request ni un resultado |
| Host Adapter | no |
| Scheduler, colas, workers, concurrencia | no |
| Reintentos, timeouts en runtime | no |
| Llamadas a modelos, subprocess nuevo | no |

`VERSION`, `CHANGELOG.md` y `UPGRADE.md` no se tocaron: son del cierre. La verificación es de
`harness-spec-refuter`.

## Rebase / integración 0.31.0

**Escrito por:** la sesión que construyó el cambio, la misma que lo integra · **Fecha:** 08-10-2026 ·
**Base nueva:** 0.31.0 (`fdca5ce`) · **Spec:** sección 37

📌 **Todo lo de arriba es la construcción original, sobre 0.30.0, y queda como se escribió.** Esta
sección cuenta solo la integración: qué se movió, qué cambió y cómo se probó. Tampoco es un
veredicto: la reverificación sobre `fdca5ce` es de `harness-spec-refuter`.

### Cómo se movió el trabajo

| Paso | Qué pasó |
|---|---|
| Copia de resguardo | Los catorce archivos de Task 3, enteros, y un `.patch` de los modificados, fuera del repo |
| `git stash push -u` | El árbol quedó limpio en `0f8b725` |
| `git fetch origin` y `git merge --ff-only origin/main` | `main` en `fdca5ce`, `VERSION` 0.31.0 |
| `git stash pop` | Volvieron los diez archivos nuevos. Chocaron tres: `PENDIENTES-FH.md`, `63-harness-unico-instalador.ps1` y `64_modelo_de_dominio.py`. `modelo-canonico.md` se combinó solo |
| Conflictos | En los tres quedó lo de 0.31.0 más lo de Task 3, sin sacar nada de ninguno de los dos |

La entrada del stash sigue guardada hasta que la integración se acepte.

### Antes de cambiar nada: lo que 0.31.0 rompió de Task 3

Con Task 3 restaurada tal cual sobre `fdca5ce`, el 65 dio **511/537**. Las 26 aserciones rojas
fueron justo las que la tabla de 37.2 anticipaba:

- R-01: el request con un plan 2.1 no validaba (`plan.schemaVersion`), y EX-E02 veía el plan
  `BLOCKED` porque al proyecto de prueba le faltaba el repositorio de la tarea;
- R-21: EX-E41, EX-E49 y EX-E51 comparaban contra `f9393cf` lo que 0.31.0 cambió a propósito;
- R-19: EX-E45 contaba 48 schemas y hay 54.

### Lo que cambió

| Artefacto | Cambio |
|---|---|
| `comun/schemas/execution-request.schema.json` | `plan.schemaVersion` admite solo `orchestration-plan/2.1`; `admission.flow` obligatorio, `DELEGATION_ALLOWED` (GD2, GD5) |
| `comun/schemas/execution-result.schema.json` | `DELEGATION_NOT_ALLOWED`, sexto en el enum de códigos (GD3) |
| `harnesses/desarrollo/bin/ejecucion/contrato.py` | `CODIGOS` y `PRECEDENCIA` con el código nuevo; la coherencia 8 de `validar_request`, sin `blockers` en la WorkUnit (GD4) |
| `docs/dominio/modelo-canonico.md` | Los bloques de Execution, ExecutionRequest, ExecutionAdmission y ExecutionError; Planning → Execution; dos desigualdades; dos filas del vocabulario; el límite de la ejecución (GD9) |
| `docs/adr/0014-el-contrato-de-ejecucion.md` | La sección `## Integración con HARNESS 0.31.0`. Las siete decisiones, sin tocar (GD10) |
| `docs/cambios/execution-contract/spec.md` | El estado y la sección 37. Las secciones 1 a 36, sin tocar |
| `docs/cambios/execution-contract/verificacion.md` | Una nota arriba: el veredicto es sobre 0.30.0 y no cierra hasta la reverificación. Los veredictos, sin tocar |
| `Pendientes/Ideas-Harness/PENDIENTES-I.md` | La idea del flujo como contexto: sería el undécimo |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | La nota del cuarto punto de canonical-domain-model suma lo de R-05 |
| `tests/casos/65_contrato_de_ejecucion.py` | EX-G01 a EX-G13; el fixture de EX-E02; las expectativas de EX-E05, E12, E20, E45, E49 y E51; EX-E41 reemplazado; la base `fdca5ce` donde 0.31.0 cambió a propósito |
| `tests/casos/64_modelo_de_dominio.py` | Sobre la versión de 0.31.0: E-05 cuenta 54, y S4 lee la tabla de la sección 22 al lado de 3.2 y D7. Las adaptaciones de E-03, E-06 y E-09 de la construcción original pasaron sin conflicto |
| `tests/casos/63-harness-unico-instalador.ps1` | Sobre la versión de 0.31.0: E-15 espera 286, las 282 de `ea2dff7` y las cuatro del contrato |

### Lo que no se tocó

EX-G11 lo fija contra `fdca5ce`: Flow Governance, el plan 2.1, los hooks, la política de
herramientas, el vínculo de sesión, la intención humana, el registro de agentes, la contabilidad,
`dev-harness.py`, `install.ps1`, `manifest.json` y ADR-0013. Tampoco `VERSION`, `CHANGELOG.md` ni
`UPGRADE.md`, que son del cierre.

### Las bases de comparación

| Escenario | Base | Por qué |
|---|---|---|
| EX-E38 (E-40, E-42) | `f9393cf` | 0.31.0 no los cambió: la base vieja sigue siendo la más exigente |
| EX-E41 (schema del plan, `plan.py`, E-13 a E-17) | `fdca5ce` | 0.31.0 los cambió a propósito |
| EX-E42 (tres schemas) | `f9393cf` | 0.31.0 no los cambió |
| EX-E49 (subcomandos) | `fdca5ce` | 0.31.0 sumó `flujo` |
| EX-E51 (E-41) | `fdca5ce` | 0.31.0 sumó `taskkill` |
| EX-G11, EX-G13 | `fdca5ce` | Son de la integración |

### Rojo visto de la integración

**Los trece EX-Gnn tienen rojo visto**, y los ocho históricos que cambiaron en 37.8 se volvieron a ver
en rojo sobre lo nuevo. Fueron 21 mutaciones sobre tres copias del repo con `.git`, en el temporal de
la sesión, con el mismo procedimiento de la construcción original: verde antes, mutación, corrida en
un proceso nuevo, solo las aserciones del propio escenario, restauración byte a byte. Las 21 quedaron
restauradas. El registro está en 37.12 de la spec.

La mutación de EX-G05 cae sobre `flujo/estado.py`, que es de 0.31.0 y no de Task 3: se hizo solo en
la copia, para probar que el escenario puede fallar.

### Tests focalizados

Sobre el árbol final, en este orden:

| Corrida | Resultado | Duración |
|---|---|---|
| `python tests/correr.py -k 65_contrato` | 666/666 | 89,2 s |
| `python tests/correr.py -k 64_modelo` | 1035/1035 | 133 s |
| `python tests/correr.py -k 71_plan` | 276/276 | 41,7 s |
| `python tests/correr.py -k 61_flujo` | 184/184 | 29,9 s |
| `python tests/correr.py -k 62_estado` | 177/177 | 100,0 s |
| `python tests/correr.py -k 63_compuerta` | 487/487 | 136,2 s |
| `python tests/correr.py -k 64_interaccion` | 376/376 | 353,3 s |
| `python tests/correr.py -k 65_fail` | 284/284 | 38,0 s |
| `python tests/correr.py -k 66_integrity` | 727/727 | 211,6 s |
| `python tests/correr.py -k 67_integracion` | 43/43 | 43,4 s |
| `python tests/correr.py -k 70_r11` | 421/421 | 134,0 s |
| `python tests/correr.py -k 63_harness_unico` | 180/180 | 36,9 s |
| `65-contrato-de-ejecucion-instalador.ps1`, `63-harness-unico-instalador.ps1` y `64-modelo-de-dominio-instalador.ps1`, aislados, con stdin desde el dispositivo nulo | 15/15, 188/188 y 25/25 | 364 s |

**`63_compuerta` dio una vez 486/487.** Fue mientras corrían en paralelo las mutaciones: cuatro
procesos de Python a la vez. Falló la aserción de E-65 que mide que la compuerta corte un
`git remote -v` colgado antes de 3 s: midió 3,2 s. Corrido solo, con la máquina libre, dio 487/487.
Es el límite de 1,5 s que la nota de 0.31.0 ya señala bajo carga, y Task 3 no toca la compuerta.

### La compuerta, sobre `fdca5ce` más Task 3 integrada

```
.\tests\Invoke-Tests.ps1
904/904 pasaron (PowerShell).
42297/42297 pasaron.
43201/43201 pasaron.
exit=0 · 2304 s
```

Corrida el 08-10-2026 sobre el árbol de trabajo sin commitear, como un proceso aparte y con stdin
desde el dispositivo nulo. Después de la corrida:

- `pre-tool-use.py` y `zonas.py` tienen el mismo hash que en `HEAD` (`b9cde9d` y `e996067`);
- `.claude/ejecuciones/` no existe;
- `git status` muestra solo los archivos de Task 3.

La nota de 0.31.0 cerró con 42484 tests. Esta corrida suma los 666 del 65, más los del 63, el 64 y los
instaladores que Task 3 adaptó.

### Archivos de la integración

Modificados por la integración, entre los de Task 3:

- `comun/schemas/execution-request.schema.json`
- `comun/schemas/execution-result.schema.json`
- `harnesses/desarrollo/bin/ejecucion/contrato.py`
- `docs/adr/0014-el-contrato-de-ejecucion.md`
- `docs/cambios/execution-contract/spec.md`
- `docs/cambios/execution-contract/informe-de-construccion.md`
- `docs/cambios/execution-contract/verificacion.md` (solo la nota de arriba)
- `tests/casos/65_contrato_de_ejecucion.py`

Modificados respecto de `fdca5ce`:

- `docs/dominio/modelo-canonico.md`
- `Pendientes/Fix-Harness/PENDIENTES-FH.md`
- `Pendientes/Ideas-Harness/PENDIENTES-I.md`
- `tests/casos/64_modelo_de_dominio.py`
- `tests/casos/63-harness-unico-instalador.ps1`

Sin cambios en la integración: `harnesses/desarrollo/bin/ejecucion/__init__.py` y
`tests/casos/65-contrato-de-ejecucion-instalador.ps1`.

No se hizo commit, y no se cerró versión.

### Scope de la integración

| | |
|---|---|
| Execution Engine | no |
| ExecutionAdmission implementada | no: es la regla de 37.5, con su precedencia en `contrato.PRECEDENCIA` |
| Host Adapter | no |
| Persistencia, locks | no |
| Scheduler, workers, reintentos | no |
| Llamadas a modelos, subcomando nuevo | no |
| Features nuevas de Flow Governance | no |
| Cambios a Flow Governance, plan 2.1, hooks, política de herramientas, vínculo de sesión, intención humana, registro de agentes, contabilidad, `install.ps1` o `dev-harness.py` | no (EX-G11) |
