# Graph Execution: un GraphRun que lleva un plan entero a un terminal, de a una WorkUnit por vez

**Estado:** APPROVED FOR CONSTRUCTION · aprobó Nahuel Palacio el 13-10-2026, en el encargo de
construcción de ese día · huella de la versión aprobada (contenido anterior a este registro):
SHA256 `217D1D93A7E0449CA972205666C4ED87FEF28E6C98123FFBC56E1E5F74D15007` · **Fecha:** 13-10-2026 · **Versión de partida:** 0.32.0 (`e33b41b`, tag `v0.32.0`),
árbol limpio · **Corregida** el 13-10-2026: la serialidad es de las Executions propias del GraphRun,
sin exclusión global de la TaskKey (GD-06, §15.4) · **Enmendada el 14-10-2026 durante la construcción
y el 15-10-2026 tras la verificación independiente, con la auditoría completa de la cancelación
(§17.4), su corrección contra los probes del refuter G, tras el refuter H sin afirmaciones universales
sobre las entrañas del motor de Task 4 y, tras el refuter I, con lo normativo de la cancelación (acciones
de Task 5) separado de lo informativo (casos observados) y, tras el refuter J, achicado: ver 27.1**

Esta spec es la Task 5. Consolida las salidas de T5-WU01 a T5-WU09 de la Fase A (corridas por
`harness-architecture-orchestrator`, solo lectura) y decide cada conflicto que esas salidas dejaron
abierto. Se escribió antes de construir: no hay código, tests ni ADR escritos por esta Task.

Abreviaturas:

- `bin/` es `harnesses/desarrollo/bin/`;
- **T3** es `docs/cambios/execution-contract/spec.md`; **T4** es
  `docs/cambios/minimal-execution-engine/spec.md`, y sus secciones se citan `T4 §n`;
- **MC** es `docs/dominio/modelo-canonico.md`; **FH** es `Pendientes/Fix-Harness/PENDIENTES-FH.md`;
- **t72** es `tests/casos/72_motor_de_ejecucion.py`; **t64** es `tests/casos/64_modelo_de_dominio.py`;
- **F** es la huella del plan (`planFingerprint`) a la que queda atado un GraphRun.

📌 **Los ids.** Los escenarios son `GE-Enn`, los invariantes `GE-Inn`, las decisiones `GD-nn` (una
por cada una de las 29 decisiones obligatorias del brief, con el mismo número), los conflictos
decididos `GC-nn`, las mutaciones de rojo `GM-nn` y los pendientes que esta Task deja `GP-nn`. Para el
método de `CLAUDE.md`, un `GE-Enn` es un `E-nn` con todas sus reglas, `rojo visto` incluido.

📌 **Evidencia.** Cada cita `archivo:línea` la leyó el arquitecto de WU10 sobre `e33b41b`. Lo que
dijo un especialista y no se pudo leer en el repo está marcado como tal, y no sostiene ninguna
decisión.

## Índice

1. Estado
2. Baseline
3. Problema
4. AS-IS
5. Gaps y conflictos
6. Boundary
7. Domain model
8. Identity
9. Lifecycle
10. Scheduling
11. Dependencies
12. Admission
13. Persistence
14. Atomicity
15. Concurrency
16. Recovery
17. Cancellation
18. Plan changes
19. Flow / Normative
20. Capabilities
21. Evidence
22. Error model
23. Result
24. CLI / API
25. Security
26. LangGraph
27. Migration
28. Canonical model changes
29. ADR plan
30. Risks
31. Invariants
32. Scenarios
33. Red mutations
34. Construction order
35. Gate

---

## 1. Estado

| | |
|---|---|
| Fase A (WU01 a WU09) | Completa, solo lectura. Las salidas se consolidaron completas, no resumidas |
| WU10 (esta spec) | Consolidada. Ninguna decisión arquitectónica quedó abierta (§5.3, §5.4) |
| Decisión humana pendiente | **Ninguna para la revisión de spec.** La aprobación para construir la da una persona, después de revisar (§35) |
| Código, tests, ADR | No se escribió nada. El ADR y los cambios al modelo canónico se planifican (§28, §29) |

**La respuesta corta**, que el resto de la spec justifica:

- **GraphRun** es un segundo agregado raíz del contexto **Execution**, no un contexto nuevo;
- lleva **todas** las WorkUnits de **un** plan, atado a **una** huella F, a un terminal
  `SUCCEEDED`, `FAILED` o `CANCELLED`;
- es **serial y fail-fast**: una Execution propia por vez, en el orden topológico determinista de
  Planning, y se detiene en la primera unidad que no queda `SUCCEEDED`. Serial respecto de lo que él
  despacha, no un candado de la TaskKey: una Execution manual que arranca después de su chequeo
  previo al despacho puede convivir con la suya (§15.4);
- **no reintenta y no se reanuda**: un reintento lo pide una persona con `ejecutar --unidad`, y
  seguir después de una caída es otro GraphRun que adopta lo que ya está `SUCCEEDED`;
- cada Execution sale de `motor.ejecutar`, con sus dos admisiones: el GraphRun decide **qué intentar**,
  la admisión decide **si es admisible**;
- su estado se deriva de cuatro marcas que se escriben una sola vez y del registro de Executions;
- se monta sobre `ejecutar` con una opción, `--grafo`, sin subcomando nuevo;
- **N1** se cierra en Task 4 sin candado nuevo: ninguna sonda toca una carpeta en creación;
- **R5** se cierra en el Host Adapter: en Windows, `tests.run` es `CAPABILITY_UNAVAILABLE` antes de
  la entrega, y el GraphRun no evalúa capacidades;
- **LangGraph no se usa**.

### 1.1 Las 29 decisiones obligatorias, resueltas

Cada una tiene su detalle, su justificación y su evidencia en la sección que se indica.

| # | Decisión | Resolución | § |
|---|---|---|---|
| GD-01 | Owner de Graph Execution | El contexto Execution. Dueño humano de `bin/ejecucion/`: sigue sin declarar (GP-01) | 6, 7 |
| GD-02 | Nombre | `GraphRun`. Se enmienda la fila «run / corrida» del vocabulario de MC | 7, 28 |
| GD-03 | Identidad | `graphRunId` = `grf_` más 32 hexadecimales al azar, atado a (TaskKey, F) | 8 |
| GD-04 | Lifecycle | `ACTIVE` → `SUCCEEDED` \| `FAILED` \| `CANCELLED`. Huérfano no es un estado | 9 |
| GD-05 | Éxito y falla del grafo | `SUCCEEDED` si y solo si todas las unidades están `SUCCEEDED` bajo F; si no, `FAILED` con un código, o `CANCELLED` | 9, 22 |
| GD-06 | Serial o paralelo | Serial respecto de sus propias Executions: a lo sumo una despachada por el GraphRun abierta a la vez. Antes de cada despacho, chequeo preventivo de la TaskKey (`TASK_EXECUTION_OPEN`); no es exclusión global de la TaskKey | 15 |
| GD-07 | Scheduler | Un conductor en el mismo proceso, un bucle sobre el orden de `orden_de_ejecucion` | 10 |
| GD-08 | Semántica de dependencias | AND estricto sobre el último turno `SUCCEEDED` bajo F. Fail-fast | 11 |
| GD-09 | Reintento | Ninguno automático, ni dentro de un GraphRun ni entre GraphRuns | 11, 16 |
| GD-10 | Recovery | El que toma el candado cierra los GraphRuns huérfanos; no hay reanudación | 16 |
| GD-11 | Cancelación | Marca escrita una vez, propagada con `motor.cancelar` solo a las Executions propias | 17 |
| GD-12 | Persistencia | Marcas de una sola escritura bajo `.claude/ejecuciones/<KEY>/grafos/`, estado derivado | 13 |
| GD-13 | Idempotencia | La de Execution, por clave; un GraphRun no despacha una unidad con turno bajo F | 13, 14 |
| GD-14 | Varios GraphRuns | Secuenciales, cada uno con su terminal; a lo sumo uno `ACTIVE` por TaskKey | 14 |
| GD-15 | Execution manual concurrente | Una terminada se adopta; una abierta que el GraphRun observa antes de despachar lo detiene (`TASK_EXECUTION_OPEN`); una de otra unidad que arranca después del chequeo convive, con la evidencia de Task 4; nunca se rechaza ni se cancela | 14, 15 |
| GD-16 | Cambio de plan | El GraphRun se detiene (`PLAN_FINGERPRINT_CHANGED`) y el motor recibe la huella esperada | 18 |
| GD-17 | Flow | Lo decide la admisión en cada despacho; el GraphRun no lo lee ni lo escribe | 19 |
| GD-18 | Normative | Igual: la compuerta corre dos veces por Execution, sin caché | 19 |
| GD-19 | Capabilities | El GraphRun es ciego a capacidades; la admisión y el adaptador deciden | 20 |
| GD-20 | N1 | Ninguna sonda de candado toca una carpeta en creación (`barrer` y `limpiar_temporales`) | 15 |
| GD-21 | R5 | `provee` conoce la plataforma: en Windows `Bash` no se ofrece y `tests.run` se rechaza al entregar | 20 |
| GD-22 | Error model | `GraphRunError`, propio y cerrado, nueve códigos; un ExecutionError solo se referencia | 22 |
| GD-23 | Result contract | `graph-run-result/1.0`, con schema | 23 |
| GD-24 | CLI / API | `ejecutar <KEY> --grafo`, `--grafo --estado`, `--cancelar grf_…`; trece subcomandos | 24 |
| GD-25 | Migración Task 4 → Task 5 | Dos parámetros opcionales del motor, un lector público del plan, N1 y R5 en Task 4; sin cambio de contrato | 27 |
| GD-26 | ADR | ADR-0016 nuevo, que revisa ADR-0015 §1 sin editarlo | 29 |
| GD-27 | Orden de construcción | N1 y R5 primero, después el motor, el registro del grafo, el conductor y la CLI | 34 |
| GD-28 | Estrategia de tests | Todo determinista: Host falso, procesos reales y cortes por gancho; cero lecturas | 32, 34 |
| GD-29 | IN / OUT | §6.2 | 6 |

---

## 2. Baseline

| Qué se verificó | Resultado |
|---|---|
| Rama | `main` |
| `HEAD` | `e33b41b0e897bb1bf09bc961882faae07f785135` |
| Tag | `v0.32.0`, apunta a `HEAD` |
| `VERSION` | `0.32.0` |
| `git status --porcelain` | vacío |
| `docs/cambios/graph-execution/` | no existía antes de esta spec |

La verificaron WU01 y, de nuevo, el arquitecto de WU10 antes de escribir. La base no es `fdca5ce`:
ese commit es la partida de Task 4 y solo se usa como historia.

---

## 3. Problema

Task 4 dejó un motor que corre **una** WorkUnit **una** vez por invocación de `ejecutar`, y nada elige
la siguiente:

- el plan 2.1 declara las dependencias de cada unidad (`orchestration-plan.schema.json:289`) y su
  orden topológico (`executionOrder`), y **nadie lo consume para ejecutar**: el único lector fuera de
  `plan.py` es la consola;
- ADR-0015 §1 deja explícitamente para Task 5 «elegir la siguiente unidad, en qué orden y cuántas a
  la vez» (`docs/adr/0015-el-motor-minimo-de-ejecucion.md:37-38`);
- MC lista como inexistentes «un ejecutor de lotes o de grafos» y «un scheduler»
  (`modelo-canonico.md:2052-2054`).

Hoy, para llevar un plan de cinco unidades a término, una persona tiene que correr `ejecutar --unidad`
cinco veces, en un orden que calcula ella, mirando cada resultado. No queda constancia de que esas
cinco formaron un intento del plan entero, ni un resultado terminal del plan.

**La pregunta de esta Task:** ¿cuál es la forma mínima de llevar todas las WorkUnits de un plan a un
terminal, respetando sus dependencias, sin romper ninguna garantía de Task 3 ni de Task 4?

Además, dos riesgos heredados entran como input obligatorio (`docs/versiones/0.32.0.md:181-183`):

- **N1**, la ventana entre que se crea `vivo.lock` y se lo bloquea (`ejecucion/registro.py:248` y
  `:250`), donde una sonda de otro proceso hace fallar la creación (FH, «The lock probe can land
  between `O_EXCL` and the lock of `Vida`»);
- **R5**, `Bash` ausente en la sesión del Host en Windows, con una unidad `tests.run` que igual se
  admite (FH, «`Bash` does not exist in the Host session on Windows»).

---

## 4. AS-IS

Lo que hay en `e33b41b`, por pieza. Es el relevamiento de WU01 con las citas releídas; donde WU01 se
equivocó, lo corrige §5.2.

### 4.1 El motor (Task 4)

| Pieza | Qué hace hoy | Evidencia |
|---|---|---|
| `motor.ejecutar` | Configuración, `recuperar`, `al_pedir`, `registro.crear`, `_correr`, `vida.soltar` en el `finally`. Una WorkUnit, sincrónico | `ejecucion/motor.py:188-233` |
| Prohibido por diseño | Scheduler, cola, hilos, reintento automático, reanudación | `motor.py:11-12` |
| `execution_id` | `admision.al_pedir` ya acepta uno externo; `motor.ejecutar` no lo expone y siempre usa `registro.nuevo_id()` | `admision.py:320-321`, `:337`; `motor.py:213-215` |
| Frontera de entrega | Antes de `entrega.json` solo hay rechazos de admisión; después, solo códigos de corrida o `CANCELLED` | `motor.py:14-16`, `:168-169` |
| Ctrl-C | Antes de la entrega, el `KeyboardInterrupt` sale de `ejecutar`; después, el motor lo absorbe y devuelve `FAILED HOST_INTERRUPTED`, o `CANCELLED` si había pedido | `motor.py:229-233`, `:286-289`, `:320-324`; `proceso.py:75-77` |
| `ErrorDelComando` | Sale sin ExecutionError, y puede salir con una Execution ya publicada (una falla al armar el resultado) | `motor.py:40-41`, `:138-140`, `:222-224` |
| Recuperación | Cierra `RUNNING` huérfanas; no toca `REQUESTED` (R2); barre residuos y temporales | `motor.py:369-396` |
| Cancelación | Recupera, escribe `cancelacion.json` una vez, cierra una `REQUESTED` sin motor | `motor.py:427-473` |
| Estado | `motor.estado` solo lee, y sondea el candado de las abiertas | `motor.py:478-497` |
| CLI | `ejecutar <KEY>` con exactamente una de `--unidad`, `--cancelar`, `--estado`, `--recuperar`; 0 solo si `SUCCEEDED` | `dev-harness.py:2250-2254`, `:1194` |

### 4.2 El registro y su atomicidad

| Pieza | Qué hace hoy | Evidencia |
|---|---|---|
| Escritura de una sola vez | Temporal exclusivo, `fsync`, `os.link`; `FileExistsError` si ya existe | `registro.py:180-202` |
| Turnos | `claves/<hex>/<NNNNNN>.json`; una Execution existe si y solo si un turno la nombra | `registro.py:21-23`, `:362-369` |
| Creación | `mkdir`, `Vida`, `request.json`, gancho `antes_de_reservar`, turno `leido+1` | `registro.py:378-409` |
| `Vida` | `os.open(O_CREAT\|O_EXCL\|O_RDWR)` y **después** `_bloquear`: el archivo es visible antes de estar tomado | `registro.py:246-253` |
| Sondas | `candado_libre` toma y suelta; la llaman `barrer` (`:532`), `limpiar_temporales` (`:555`) y `motor.estado` (`motor.py:493`) | `registro.py:266-286` |
| `barrer` | Evalúa `candado_libre` **antes** que la edad | `registro.py:532` |
| `limpiar_temporales` | Sondea toda carpeta `exe_…`, sin guarda de edad; solo los temporales de los turnos tienen umbral | `registro.py:549-571` |
| Lo que ve el registro | `carpetas` filtra `exe_[0-9a-f]{32}`; `tareas` filtra TaskKeys; `otras_entregadas` recorre todo el proyecto | `registro.py:60`, `:466-506` |
| Estado derivado | `REQUESTED`, `RUNNING`, terminal o `ILEGIBLE`, que cuenta como abierta | `registro.py:414-444` |

### 4.3 La admisión

| Pieza | Qué hace hoy | Evidencia |
|---|---|---|
| La regla | Quince condiciones en el orden de `PRECEDENCIA`, al pedir y al entregar | `admision.py:251-308`; `contrato.py:87-103` |
| Lectura del plan | `_leer_plan`: bytes, JSON, `aceptar_guardado`, ids sin repetir. **No revalida ciclos** | `admision.py:116-147` |
| Huella | `contrato.huella(plan)` del documento entero, JSON canónico | `admision.py:260`; `contrato.py:124-132` |
| `PLAN_CHANGED` | Solo al entregar: compara la huella del plan actual con la de la request | `admision.py:261-269`; `contrato.py:60` |
| Dependencias (14) | Último turno `SUCCEEDED` de cada dependencia, bajo la misma huella | `admision.py:220-234` |
| Duplicado (15) | Al pedir, rechaza si el último turno no es `FAILED`, `CANCELLED` ni `REJECTED` | `admision.py:299-301` |
| Capacidades (13) | 13a con capacidades declaradas, en los dos momentos; 13b `adaptador.provee`, solo al entregar | `admision.py:288-295`, `:336` |
| `admission.capabilities` | Se escribe siempre `ALL_AVAILABLE` | `admision.py:376` |
| Rechazo al pedir | No crea Execution: vuelve al que pidió | `contrato.py:53-55` |

### 4.4 El plan

| Pieza | Qué hace hoy | Evidencia |
|---|---|---|
| `orden_de_ejecucion` | Kahn por niveles, `sorted` dentro de cada nivel; levanta con dependencia rota o ciclo | `orquestacion/plan.py:111-140` |
| Dependencias repetidas | El schema no tiene `uniqueItems`; el contrato las rechaza en la request | `orchestration-plan.schema.json:289`; `contrato.py:261-263` |
| Escritura | `io.open(ruta, "w")`: no es atómica | `plan.py:588-589` |
| Quién lo reescribe | `plan`, `--replanificar` y una decisión humana | `estado_de_tarea/decisiones.py:71-92` |
| Aviso de capacidades | Sale solo si falta alguna capacidad | `plan.py:282-285` |

### 4.5 El Host Adapter

| Pieza | Qué hace hoy | Evidencia |
|---|---|---|
| Mapa capability → herramienta | `tests.run → Bash`, fijo para toda plataforma | `host_claude_code.py:45-50` |
| `provee` | Mira solo si las herramientas están en el `tools:` del agente | `host_claude_code.py:194-198` |
| Lo observado del Host | En Windows, `--tools Read,Bash` da una sesión con `Read, StructuredOutput`: `Bash` no está | T4 §34.2, E8 (`spec.md:1867`) |

### 4.6 Las guardas que restringen el diseño

| Guarda | Qué fija | Evidencia |
|---|---|---|
| ME-E47 | Nada de `bin/` ni de `comun/` importa `threading`, `multiprocessing`, `asyncio`, `concurrent`, `sched`, `queue`, un SDK de modelos ni LangGraph; trece subcomandos; el Host lo lanza solo `host_claude_code.py` | t72:2196-2239 |
| E-41 adaptado | Todo `subprocess` de `bin/` y `comun/` lanza `git` o `markitdown` (más `taskkill` y el Host) | t64:2874-2893, `:2819-2860` |
| ME-E46 | En `bin/ejecucion/` solo `registro.py` escribe en disco, y bajo `.claude/ejecuciones/` | t72:2154-2193 |
| EX-E50 | `bin/ejecucion/` no nombra `maxRetries` ni otros campos de reintento | `65_contrato_de_ejecucion.py:1281-1290` |
| E-09 | `## El límite de la ejecución` de MC nombra, en «Lo que todavía no existe», `ejecutor`, `scheduler`, `reintento` y `estado de corrida persistido` | t64:1066-1115 |
| 63 E-15 | El lock instalado tiene 292 rutas | `63-harness-unico-instalador.ps1:421` |

### 4.7 Lo que no existe

Ningún módulo, símbolo ni archivo «graph» en `bin/`, `comun/` ni `tests/`. Ningún estado de grafo,
ningún candado por tarea, ninguna marca de cancelación de algo mayor que una Execution.

---

## 5. Gaps y conflictos

### 5.1 Los gaps

| Gap | Por qué importa |
|---|---|
| Nada elige la siguiente unidad | Es la Task |
| No hay identidad ni terminal de «el plan entero» | Sin eso no hay resultado del grafo, ni cancelación del grafo, ni auditoría |
| `motor.ejecutar` no acepta una huella esperada | Un GraphRun atado a F podría provocar una entrega real bajo otra huella (§18) |
| `aceptar_guardado` no revalida ciclos ni dependencias rotas | Un plan editado a mano dejaría unidades en `DEPENDENCY_NOT_SATISFIED` para siempre |
| Las dependencias repetidas pasan Planning y rompen el contrato | El plan queda `READY` y su unidad sale `CONTRACT_INVALID` al pedir |
| N1 | Con un conductor y una persona sobre la misma tarea, la ventana existe; con concurrencia crece |
| R5 | Un `SUCCEEDED` sin tests habilitaría a las dependientes |
| `ErrorDelComando` no dice si quedó una Execution | Un conductor que lo lea como «nada pasó» se equivocaría (§16) |

### 5.2 Discrepancias de hecho, resueltas leyendo el código

| GC | Tema | Quién dijo qué | Lo que dice el código | Se adopta |
|---|---|---|---|---|
| GC-01 | El aviso de `plan.py:282-285` | WU01: «agrega un aviso» sobre capacidades. WU07 (las dos lentes): sale solo si falta otra capacidad | `if capacidades["missing"]:` (`plan.py:282`). En R5 puro no falta nada: no hay aviso | WU07 |
| GC-02 | Alcance de la guarda contra concurrencia | WU01: la guarda mira `motor.py`. WU02 y WU04: todo `bin/` y `comun/` | `fuentes = _py(BIN) + _py(RAIZ / "comun")` (t72:2214) | WU02 y WU04 |
| GC-03 | ¿`barrer` sondea con guarda de edad? | WU01: sondea con guarda de edad. WU04: el candado se evalúa antes que la edad | `if candado_libre(carpeta) is False or _edad(carpeta) <= umbral:` (`registro.py:532`): `candado_libre` corre primero, siempre | WU04 |
| GC-04 | ¿Un subproceso `ejecutar` pasa la guarda? | WU04: un `Popen` directo pasa en silencio. WU03: no, E-41 solo admite `git` y `markitdown`. WU06: esquiva la letra | E-41 adaptado, dentro de ME-E47 (t72:2231-2239), recorre todo `subprocess` de `bin/` y `comun/` y marca cualquier programa que no sea `git` o `markitdown` (t64:2879-2891, `_lanzamientos` en `:2819`) | WU03. La afirmación de WU04 es falsa |
| GC-05 | ¿El perdedor de N1 puede dejar residuo en Windows (N1b)? | WU05: «sin Execution ni residuo», por la verificación. WU04: el `rmtree` puede fallar con el handle de la sonda abierto (deducido) | `crear` borra con `shutil.rmtree(carpeta, ignore_errors=True)` (`registro.py:403`); lo observado fue «sin residuo y sin turno» (`verificacion.md:979-980`). N1b no se reprodujo | Ninguna invariante depende de N1b: una carpeta sin turno no es una Execution (ME-I28) y `barrer` la recoge. GD-20 elimina la sonda que lo causaría, así que N1b desaparece con N1 |
| GC-06 | ¿Un rechazo por dependencia crea una Execution `REJECTED`? | WU09 (GE-E13): «se crea REQUESTED→REJECTED por cond. 14», como opción | Un rechazo al pedir no crea Execution (`contrato.py:53-55`; `motor.py:218-219`). La condición 14 solo da `REJECTED` al entregar | El código. WU09 no leyó el repo |
| GC-07 | ¿Reformatear el plan cambia la huella? | WU09 (GE-E41): «no probada» | La huella es de la estructura parseada (`admision.py:129`, `:260`; `contrato.py:131`): espacios y orden de claves no la cambian | El código: es un escenario (GE-E26) |

### 5.3 Conflictos arquitectónicos, decididos

Los del orquestador (marcados ORQ) y los que las salidas dejaron como decisión candidata. Ninguno
queda abierto: en cada uno, una de las opciones viola un invariante o un requisito del brief, o no
está comprobada, así que no hay dos opciones igual de válidas.

| GC | Tema | Posiciones | Decisión | Por qué | Se adopta |
|---|---|---|---|---|---|
| GC-08 (ORQ) | ¿El GraphRun puede no lanzar un nodo por capability? | WU07-rt: preflight sobre `adaptador.provee`, nodo «no elegible». WU07-ct: la pista nunca decide (GE-I-R5-1/2). WU02-B: I-G14 | **No.** El GraphRun no evalúa capacidades. La verdad la da `provee`, corregido por plataforma (GD-21), en la condición 13b | Una sola fuente de verdad (`admision.py:288-295`). Con el corte serial y fail-fast, descubrir el rechazo cuesta una Execution `REJECTED` sin corrida de modelo: la 13b corre antes de `entrega.json` (`motor.py:258-266`) | WU07-ct; de WU07-rt, GE-I-10 (la fuente es el adaptador) |
| GC-09 (ORQ) | ¿`CAPABILITY_UNAVAILABLE` detectado en `RUNNING`? | WU07-rt: nunca, coherente con ME-I29. WU07-ct: A2 es válida por T3, revierte ME-I29 | **No se detecta en `RUNNING`.** ME-I29 queda. El GraphRun igual acepta todo lo que el contrato permite: un `FAILED` con ese código es una unidad no exitosa | A2 revierte un invariante cerrado de Task 4 (T4 `spec.md:1257`) y pide `stream-json`, no probado. GD-21 lo resuelve antes de la entrega | WU07-rt para el motor; WU07-ct GE-I-R5-5 para el GraphRun |
| GC-10 (ORQ) | Las dos corridas de WU02 | Ver §5.4 | §5.4 | §5.4 | §5.4 |
| GC-11 (ORQ) | ¿Re-entrada al mismo GraphRun o uno nuevo? | WU05: re-entrada por un proceso nuevo. WU02 (las dos): nunca se reanuda, seguir es otro | **Otro GraphRun.** El huérfano se cierra (`GRAPH_INTERRUPTED`, o `SUCCEEDED` si ya está todo, o `CANCELLED` si tiene la marca de cancelación: §16.1; precisado en 27.1 M) | ADR-0015 §4: «nada se vuelve a entregar» y nadie reanuda. Con estado derivado, el GraphRun nuevo llega al mismo punto adoptando lo `SUCCEEDED`, y cada GraphRun conserva un terminal que no cambia | WU02; de WU05, el procedimiento de reconstrucción (§16) |
| GC-12 (ORQ) | Execution manual o ajena en vuelo | WU02-B: convivir, la ajena retiene solo su unidad. WU04 GE-I-g: no despachar con cualquier `RUNNING` del proyecto. WU03: alcance clave, tarea o proyecto. WU06: secuencial por TaskKey | **Alcance TaskKey.** Antes de cada despacho, si hay en la TaskKey una Execution abierta o ilegible, el GraphRun se detiene con `TASK_EXECUTION_OPEN`. Nunca la cancela ni la rechaza. Una terminada `SUCCEEDED` bajo F se adopta | El GraphRun no despacha si ya observa otra Execution abierta en la TaskKey. Existe una carrera residual con una Execution manual que empieza después del chequeo (§15.4): se acepta, porque excluirla requeriría modificar ExecutionAdmission / Task 3 (una condición 16 de admisión o un candado del GraphRun en la admisión). En esa carrera la evidencia degrada por la regla de Task 4 (`evidencia.py:141-142`), no se atribuye de más. El proyecto entero restringiría tareas sin relación; convivir a propósito, sin chequeo, degradaría la evidencia en cada despacho | WU06, con el freno de WU04 limitado a la TaskKey |
| GC-13 (ORQ) | Clasificación de `CAPABILITY_UNAVAILABLE` en el resultado | WU03: falla local que se propaga. WU07-rt: bloqueo de entorno, terminal aparte. WU06: ambiental, no se reintenta | **Un solo terminal `FAILED`**, con la causa: el código del GraphRun y el `executionCode` referenciado | Con fail-fast, local o sistémico no cambia el comportamiento: todo se detiene. Un terminal más agrega estados sin un caso que los distinga | WU06; WU07-rt AD-4 en su variante «un único FAILED con causas» |
| GC-14 (ORQ) | ¿Lanzar un GraphRun nuevo es pedir el reintento de las unidades fallidas? | WU02 oficial: se inclina por sí. WU02-B: las vuelve elegibles. WU05 (GE-I04, D13), WU03 (R-A3 con costos), WU06 (CR1): no | **No.** Una unidad cuyo último turno bajo F existe no se despacha. El reintento lo pide una persona con `ejecutar --unidad` | ADR-0015:36-37 y `motor.py:11-12`: un reintento es otra Execution que pide una persona. Un consentimiento global volvería a correr en silencio una huérfana cerrada por la recuperación (G5c de WU05: el trabajo puede ya estar en el repo) | WU05, WU06 |
| GC-15 (ORQ) | ¿`GraphRunError` reutiliza códigos de ExecutionError? | WU02-B: reutiliza cinco al arrancar. WU06: vocabulario propio, `CONTRACT_INVALID` es ambiguo | **Vocabulario propio y cerrado** (§22). Un ExecutionError aparece solo como causa referenciada | Mismo nombre con otro dueño confunde a quien lee `--json`; y el GraphRun no lee `detail` (MC:1072) | WU06 |
| GC-16 | GraphRun persistido o proyección derivada (WU02 oficial, OD1, con `ARCHITECTURAL DECISION REQUIRED`) | WU02 oficial recomienda A mínima; WU08 (X1, X3), WU05 (P-B) y WU02-B coinciden | **A mínima: cuatro marcas de una sola escritura y estado derivado** (§13) | La B no cumple el brief: no da resultado terminal (§1 del brief), no puede persistir una cancelación del grafo (§12), no excluye dos conductores (§24) y no deja identidad (§15). WU08 lo prueba dato por dato: sin X1 y X3 no se reconstruye la entidad. No son dos opciones igual de válidas | WU02 oficial, WU08 |
| GC-17 | Fail-fast o seguir con las ramas independientes | WU02 OD6, WU03 AD-2, WU06 AD4, WU07-rt AD-5: abierta | **Fail-fast** | Una falla sistémica (R5, el proveedor, un Ctrl-C) se repetiría en cada rama a costo de una corrida de modelo por nodo; un Ctrl-C absorbido por el motor (`motor.py:286-289`) no puede ser seguido de otro despacho. Lo mínimo que preserva los invariantes. Seguir las ramas independientes se puede agregar después sin cambiar la persistencia (GP-04) | WU02, WU03 (híbrida descartada) |
| GC-18 | Cómo se ata la huella al pedir | WU03 AD-1, WU06 AD1, WU08 D4: (a) huella esperada al motor, con `PLAN_CHANGED` al pedir; (b) chequeo antes y después; (c) candado de Planning | **(a) sin cambiar el contrato:** `motor.ejecutar` y `al_entregar` aceptan `huella_esperada`; si la request no la tiene, la Execution termina `REJECTED PLAN_CHANGED` al entregar, antes del Host | (b) deja pasar una entrega real bajo otra huella (`admision.py:255-269`: `al_pedir` arma con el plan del disco y `al_entregar` compara contra la request); (c) acopla Planning. `PLAN_CHANGED` en `REJECTED` ya es legal (`contrato.py:60`): no hace falta llevarlo a `AL_PEDIR` | WU03, WU06, WU08, con la variante sin cambio de contrato |
| GC-19 | ¿El conductor en el mismo proceso o como proceso padre? | WU03: mismo proceso. WU04, WU05, WU08: las dos | **Mismo proceso**, sobre `motor.ejecutar` | Un subproceso rompe E-41 (GC-04). El Ctrl-C absorbido no se pierde: deja la unidad `FAILED HOST_INTERRUPTED` y el fail-fast detiene el GraphRun | WU03 |
| GC-20 | `REQUESTED` huérfana (R2) que encuentra el GraphRun | WU03 AD-5, WU05 D5, WU08 D6: detenerse o cancelarla | **Detenerse** (`TASK_EXECUTION_OPEN`) con el comando exacto para cancelarla. El GraphRun no la cancela salvo que su propia marca de cancelación lo pida (§17) | ADR-0015:62-63: la cancela una persona. WU06 CR7 | WU06, WU03 primera opción |
| GC-21 | Arreglo de N1 | WU04: F1+F2, F5 mutex, F3 reintento. FH: «tomar el candado antes de que el archivo sea visible, o sondear dos veces» | **F1 + F2′** (§15.3) | Cierra la ventana sin candado nuevo, y usa la regla que `limpiar_temporales` ya aplica a los temporales de los turnos (`registro.py:563-570`). «Sondear dos veces» no protege: la víctima es la que crea (WU04). F5 reabre una alternativa que T4 MD-04 descartó | WU04, con F2 reemplazado por F2′ |
| GC-22 | Cancelar una Execution del grafo desde afuera | WU05 D7 | **Es una falla de la unidad**, no una cancelación del grafo: `FAILED WORK_UNIT_NOT_SUCCEEDED` con `executionStatus: CANCELLED` | La cancelación del grafo es una marca propia; una Execution cancelada sola no la escribe | WU05, primera opción |
| GC-23 | Cancelación que llega con todo terminado | WU05 D8, WU02-B | **Lo observado gana**: todas `SUCCEEDED` es `SUCCEEDED`, con la marca registrada | Precedente de T4: un resultado tardío no pisa (`motor.py:135-146`) | WU02-B, WU05 |
| GC-24 | La ventana entre cancelar y despachar | WU05 D9, WU08 RA4 | **Marca de despacho antes de mirar la cancelación**, y quien cancela mira las marcas de despacho después de escribir la suya (§17.2) | Con dos escrituras de una sola vez cruzadas, al menos uno ve al otro. Sin gancho de producto en el motor. Que el cancelador vea el despacho no garantiza que la Execution termine `CANCELLED`: le pide solo si una de sus vueltas la encuentra con turno y abierta, y qué resultado escribe el motor con el pedido persistido es de Task 4: los casos observados son ejemplos, no una lista exhaustiva (§17.2, §17.4; precisado en 27.1 M y O) | WU08 |

### 5.4 Las dos corridas de WU02

La corrida oficial (`acae0754…`) y la del primer lanzamiento, con prompt truncado (`aba9ef1e…`),
coinciden en lo central: Execution es el dueño, GraphRun referencia Executions y no las posee, el
vínculo va del GraphRun a la Execution sin tocar `execution-request/1.0`, y no hay reanudación.
Difieren en el modelo de GraphRun. **Se toma la oficial como base** y se suma lo que la otra resolvió
mejor, verificado:

| Tema | Oficial | Primer lanzamiento | Queda |
|---|---|---|---|
| Persistencia | Abierta (OD1) | Persistido, con marcas de despacho | Persistido mínimo (GC-16) |
| Estado abierto | `RUNNING` | `ACTIVE` | `ACTIVE`: `RUNNING` ya es un estado de Execution, y `--estado` muestra los dos |
| Prefijo | `grf_` | `grn_` | `grf_` |
| Vínculo con la Execution | Por la clave | `executionId` preasignado en una marca de despacho antes del motor | Preasignado: `al_pedir` ya acepta `execution_id` (`admision.py:321`, `:337`), y la marca distingue lo propio de lo ajeno sin tocar la request |
| Conjunto de nodos | — | Congelado al arrancar | Congelado en `inicio.json` |
| Nodo `FAILED` previo | OD3, inclinada a reintentar | Elegible en el run nuevo | **No elegible** (GC-14) |
| Ajena abierta | — | Convivir; `WORK_UNIT_HELD` | Detenerse (GC-12) |
| Códigos al arrancar | — | Reutiliza cinco de ExecutionError | Propios (GC-15) |
| Cancelación tardía | — | Gana lo observado | Igual (GC-23) |
| `GRAPH_INTERRUPTED` | «el driver murió» como causa | Código de la recuperación | Código de la recuperación |

El `READY FOR SPEC REVIEW` del primer lanzamiento no vale como cierre: era una invocación de WU02, no
la consolidación.

### 5.5 Lo que dijo WU09 sin leer el repo, verificado

WU09 corrió con cero herramientas y citó todo de WU01. Lo que entró a esta spec se verificó:

| Afirmación de WU09 | Verificación | Entra |
|---|---|---|
| `candado_libre` devuelve `None` sin `vivo.lock` | `registro.py:271-272` | Sí (§15.3) |
| `limpiar_temporales` no se frena con `None` | `registro.py:555`: solo con `False` | Sí |
| Hooks de test `antes_de_reservar` y `antes_de_entregar` | `motor.py:189-190`, `:251-252`; `registro.py:395-396` | Sí |
| `aceptar_guardado` no revalida ciclos | `plan.py:595-649` | Sí |
| REQUESTED→REJECTED por condición 14 | Falso al pedir (GC-06) | No |
| El GraphRun podría entregar una `REQUESTED` existente (D-ADOPT) | Sería reanudar: prohibido (ADR-0015 §4) | No |
| Modos del Host falso: «sin Bash», «cuenta invocaciones» | `tests/fixtures/host_falso.py:1-19`: no existen; hay `eco`, `dormir`, `senal`, `salida`, `resultado` | Como extensión del fixture (§34) |
| Cero escenarios de lectura | Correcto: ningún sujeto es una corrida de un modelo | Sí |

### 5.6 Matriz de consolidación

| Tema | Evidencia | Decisión |
|---|---|---|
| Ownership | ADR-0015:37-38 y :153; MC:1735; WU02 (las dos); WU06 AD8 | Execution, segundo agregado raíz (GD-01). Dueño humano de `bin/ejecucion/`: GP-01 |
| Lifecycle | MC:1977 (sin `BLOCKED`); ADR-0015 §4; WU02, WU05 | `ACTIVE` → tres terminales; sin reanudación (GD-04, GC-11) |
| Scheduling | `plan.py:111-140`; MC:2037; WU03 | Conductor serial sobre `orden_de_ejecucion`, fail-fast, sin reintento (GD-07, GD-08, GC-14, GC-17) |
| Concurrency | t72:2196-2239; t64:2874-2893; `evidencia.py:141`; WU04 | Serial en el conductor y en sus Executions propias, con chequeo preventivo de la TaskKey antes de cada despacho, sin exclusión global de la TaskKey (§15.4); mismo proceso (GD-06, GC-04, GC-19) |
| Recovery | `motor.py:369-396`; WU05 G0-G12; WU08 C1-C9 | Cerrar huérfanos con el candado, reconstruir, nunca reanudar (GD-10) |
| Admission | `admision.py:251-308`; WU06 H1-H6 | Sin cambios en la regla; el motor recibe la huella esperada (GD-16, GC-18) |
| Persistence | ADR-0015:40-47; ME-E46; WU08 X1-X6 | Cuatro marcas de una sola escritura, por `registro.py` (GD-12, GC-16) |
| Tests | ME-E47, E-41, ME-E46, EX-E50, E-09, 63 E-15; WU09 | Todo determinista; cero lecturas; las guardas se respetan o se adaptan con comentario (GD-28, §27) |

---

## 6. Boundary

#### GD-01. El dueño es Execution

| Por qué | Evidencia |
|---|---|
| Elegir la siguiente unidad, el orden y cuántas a la vez ya es «scheduling, de Task 5», dicho al lado del motor | ADR-0015:37-38, :153-154; MC:1735 («Task 5 decide el resto»), :1739-1740 |
| El estado de cada unidad de un grafo sale de los turnos del registro de Execution: un contexto aparte leería almacenamiento interno ajeno | `admision.py:220-234`; `registro.py:348-359` |
| Un undécimo contexto obliga a revisar ADR-0013 §1 y ADR-0014 §1, y «Orchestration» choca con `orchestration-plan` y con `bin/orquestacion/`, que son de Planning | WU02; MC:1735 |
| ME-E46: en `bin/ejecucion/` solo `registro.py` escribe, bajo `.claude/ejecuciones/`. El GraphRun puede persistir ahí sin cambiar la guarda | t72:2170-2183 |

**El dueño humano** de `bin/ejecucion/` sigue sin declarar en `CLAUDE.md` (FH, «Execution and its
schemas have no owner in the factory»). No bloquea la spec; es GP-01.

### 6.1 Las fronteras

| Frente a | Relación | Qué hace el GraphRun | Qué no hace nunca |
|---|---|---|---|
| Planning | Conformista, como Execution (MC:1754) | Lee el plan con la misma regla de lectura que la admisión, calcula F y el orden con `orden_de_ejecucion` | Escribir `.claude/planes/`, cambiar `workUnits[].status`, replanificar |
| ExecutionAdmission | Cliente | Provoca una admisión por intento, a través de `motor.ejecutar` | Evaluar, saltear o guardar en caché alguna de las quince condiciones |
| Motor de Execution | Cliente | `motor.ejecutar`, `motor.cancelar`, `motor.recuperar`, `registro.ultimo_turno`, `registro.estado` | Crear una request, un turno o una carpeta `exe_…`; escribir `cancelacion.json` o `result.json` de una Execution |
| Flow Governance | Ninguna directa | — | Leer o escribir el TaskFlowState |
| Normative Gate | Ninguna directa | — | Llamar a la compuerta |
| Catalog y Host Adapter | Ninguna directa | — | Decidir si una capability está disponible |
| Observability | Ninguna | — | Leer o escribir la contabilidad |

**La hipótesis de WU06 se sostiene:** el GraphRun decide qué WorkUnit intentar; la ExecutionAdmission
decide si ese intento es admisible. El GraphRun puede ser más restrictivo que la admisión (no pedir),
nunca más permisivo.

### 6.2 IN / OUT (GD-29)

**IN:**

- el agregado GraphRun: identidad, lifecycle, conductor serial, terminal, resultado, evidencia
  operacional;
- la adopción de lo `SUCCEEDED` bajo F, manual o de un GraphRun anterior;
- la cancelación del grafo, la recuperación de un GraphRun huérfano y su lectura de estado;
- `huella_esperada` y `execution_id` como parámetros opcionales del motor;
- el arreglo de N1 en `registro.py` y el de R5 en `host_claude_code.py`, en Task 4;
- el schema `graph-run-result/1.0`;
- `ejecutar --grafo`, `--grafo --estado` y `--cancelar grf_…`;
- ADR-0016 y los cambios a MC.

**OUT, cada uno con su razón:**

- **Paralelismo, acotado o pleno, y workers.** Rompe la atribución de evidencia
  (`registro.py:489-506`, `evidencia.py:141`), choca con ME-E47 y E-41, y multiplica N1. GP-03 dice
  qué haría falta.
- **Reintento automático, backoff y reanudación.** ADR-0015 §1 y §4; EX-E50. Un reintento lo pide una
  persona.
- **Seguir con las ramas independientes después de una falla.** GC-17; queda como GP-04.
- **Replanificar o editar el plan.** Es de Planning: el GraphRun detecta y se detiene.
- **Preflight de capacidades en el GraphRun.** GC-08.
- **Mapear `tests.run` a PowerShell en Windows.** No está comprobado que `--tools PowerShell` ande en
  una sesión headless, y casi ningún agente tiene `PowerShell` en su `tools:`. GP-02.
- **Un grafo de varias TaskKeys, o un subconjunto del grafo.** No está en el pedido.
- **Eventos `WORKUNIT_*` y la contabilidad.** MP-02 de T4 sigue: la Task que conecte Execution con
  Observability.
- **Elegir Host o proveedor, un segundo Host, multi-provider.** Hay un solo adaptador.
- **LangGraph y cualquier framework de workflow.** §26.
- **Colas, nube, UI, motor de workflow genérico.**
- **Revalidar ciclos en `aceptar_guardado` o `uniqueItems` en el schema del plan.** Son de Planning;
  el GraphRun se protege solo (§11). GP-05.
- **R1 (Host que sobrevive al motor), R6 y R7 de T4.** Siguen como riesgos de Task 4; §30 dice por qué
  el GraphRun no los agranda.
- **La fila de `ejecutar` en la política de herramientas (R4).** Del `harness-hook-engineer`.
- **`VERSION`, `CHANGELOG.md`, `UPGRADE.md`.** Son de `close-a-version`.

---

## 7. Domain model

#### GD-02. El nombre es `GraphRun`

«Graph Run» es como lo llama el brief, y es lo que es: un intento de recorrer el grafo. «GraphExecution»
haría que «Execution» nombre dos cosas en el mismo contexto. El choque con el vocabulario de MC, donde
«run / corrida» es de Refutation y «en Execution no se usa» (MC:1976), se resuelve enmendando esa fila:
dentro de Execution, «run» se usa solo calificado, `GraphRun`, y nunca para una Execution (§28).

### 7.1 Plan, Execution y GraphRun no son lo mismo

| Concepto | Contexto | Qué es | Qué no hace |
|---|---|---|---|
| Plan / WorkUnit | Planning | El documento: las unidades y sus `dependencies`. La autoridad sobre la forma del grafo | No tiene estado de ejecución (MC:2057-2060) |
| Execution | Execution | Un intento de exactamente una WorkUnit de un plan exacto | No elige la siguiente unidad |
| **GraphRun** | Execution | Un intento de llevar **todas** las WorkUnits de **un** plan, bajo **una** huella F, a un terminal, pidiendo Executions de a una | No redefine Execution, no edita el plan, no habla con el Host |

### 7.2 Las piezas

| Pieza | Clasificación | Qué es |
|---|---|---|
| `GraphRun` | Aggregate Root | Identidad `grf_…`, su huella F, su conjunto de nodos congelado, sus marcas |
| `graphRunId` | Value Object | `grf_` más 32 hexadecimales |
| Conjunto de nodos | Value Object | `[{workUnitId, dependencies}]` del plan F, y su orden, congelados en `inicio.json` |
| Despacho | Registro del GraphRun | `{numero, workUnitId, executionId}`: el intento de despachar una unidad, escrito antes de llamar al motor |
| Estado de un nodo | Value Object derivado | `SATISFIED`, `NOT_SATISFIED`, `OPEN`, `UNREADABLE` o `NOT_STARTED`; nunca se persiste como autoridad (§9.2) |
| `GraphRunError` | Value Object | `{code, workUnitId, executionId, executionStatus, executionCode, detail}` (§22) |
| `GraphRunResult` | Value Object | `graph-run-result/1.0` (§23) |
| Conductor | Domain Service | El bucle que despacha, en el mismo proceso (§10) |

**El GraphRun referencia Executions; no es su dueño.** Una Execution que pidió una persona con
`--unidad`, bajo F, cuenta para cualquier GraphRun de F: la admisión no deja repetir una clave
`SUCCEEDED` (`admision.py:299-301`), así que un GraphRun no puede tener «sus propias» Executions
exclusivas sin romper Task 4.

---

## 8. Identity

#### GD-03. `grf_` más 32 hexadecimales al azar, atado a (TaskKey, F)

- Lo genera HARNESS con el generador criptográfico, como `exe_` (`registro.py:83-85`). No sale del
  contenido, del Host ni de la sesión.
- Se valida con `fullmatch` de `grf_[0-9a-f]{32}` antes de usarlo como ruta, como un `executionId`
  (T4 MD-15).
- Queda atado a la TaskKey y a F, la huella del plan al crearlo. **La huella, no `plan_version`, es la
  identidad del plan**: `plan --propuesta` vuelve a la versión 1 (`docs/versiones/0.32.0.md:75`).
- **Se descartó una identidad determinista**, `huella([taskKey, F])` (WU08 G-A): un solo GraphRun por
  (TaskKey, F) haría que relanzar sea reanudar, y un terminal dejaría de ser terminal.

**El vínculo va del GraphRun a la Execution, nunca al revés.** `execution-request/1.0` tiene
`additionalProperties: false` en la raíz (`execution-request.schema.json:9`): un `graphRunId` en la
request sería un cambio de contrato de Task 3. El vínculo es la marca de despacho, que nombra el
`executionId` **preasignado** que el GraphRun le pasa a `motor.ejecutar`. Una Execution es del GraphRun
si y solo si una marca de despacho suya la nombra **y** un turno la nombra (ME-I21).

---

## 9. Lifecycle

#### GD-04. Un estado abierto y tres terminales

```text
(nada) ──crear, con el candado──▶ ACTIVE ──▶ SUCCEEDED
                                        ├──▶ FAILED      (con un GraphRunError)
                                        └──▶ CANCELLED
```

- **Existe** si y solo si existe su `inicio.json`. Una carpeta `grf_…` sin `inicio.json` no es un
  GraphRun: es un residuo de la creación, y la barre el próximo que toma el candado.
- **`ACTIVE`**: `inicio.json` sin `result.json`.
- **Terminal**: `result.json`, escrito una sola vez; gana el primero. Desde un terminal no sale nada.
- **Huérfano no es un estado.** Es `ACTIVE` sin conductor vivo. Solo lo puede afirmar quien tiene el
  candado de la tarea (§14), y ese lo cierra.
- **`ILEGIBLE` no es un estado del ciclo** (enmienda del 14-10-2026, 27.1 G). Es lo que da la lectura
  de un GraphRun que existe y cuyo `inicio.json` o `result.json` no valida (`registro.py:873-876`). No
  es `ACTIVE` ni terminal: nadie lo cierra, nadie lo reabre y nadie le escribe una marca (§16.1).
- **Sin `BLOCKED`, `PENDING` ni `RUNNING`.** `BLOCKED` no es de Execution (MC:1977); `RUNNING` es un
  estado de Execution, y los dos aparecen juntos en la consola.

#### GD-05. Éxito y falla del grafo: la regla de cierre

Quien escribe el terminal —el conductor, la recuperación de un huérfano o la cancelación de un
huérfano— aplica la misma regla, en este orden:

1. si todos los nodos del conjunto congelado tienen su último turno `SUCCEEDED` bajo F: **`SUCCEEDED`**,
   haya o no una marca de cancelación;
2. si existe la marca de cancelación del GraphRun: **`CANCELLED`**;
3. si no: **`FAILED`**, con el código de la causa (§22).

`SUCCEEDED` es mecánico, como el de Execution (ADR-0014:69): no afirma cumplimiento, ni que se
corrieron tests, ni más de lo que afirma cada nodo.

### 9.1 Un GraphRun que no empieza no existe

Si no se puede tomar el candado, el plan no se lee o su estructura no valida, no se crea nada: el
rechazo vuelve al que pidió, como un rechazo de Execution al pedir (MC:1047). Si el plan se lee y
**todas** las unidades ya están `SUCCEEDED` bajo F, el GraphRun se crea y termina `SUCCEEDED` sin
despachos: queda constancia de que ese plan llegó a término.

### 9.2 El estado de un nodo, derivado

Se calcula en cada decisión, del último turno de `clave_de_idempotencia(TaskKey, F, workUnitId)`
(`contrato.py:135-137`; `registro.py:348-359`):

| Último turno bajo F | Estado del nodo |
|---|---|
| ninguno | `NOT_STARTED` |
| `SUCCEEDED` | `SATISFIED` |
| `FAILED`, `CANCELLED` o `REJECTED` | `NOT_SATISFIED` |
| `REQUESTED` o `RUNNING` | `OPEN` |
| `ILEGIBLE` | `UNREADABLE`, que cuenta como abierto, como para la admisión (`registro.py:417-418`) |

Una Execution de otra huella no se ve: su clave es otra por construcción. Una `RUNNING` sin motor que
el GraphRun encuentra al arrancar ya la cerró `motor.recuperar` (paso 3 de §10), así que llega
`NOT_SATISFIED`; una `REQUESTED` sin motor sigue `OPEN` (R2). **El estado del nodo no se
escribe como autoridad.** El resultado del GraphRun guarda una foto al cerrar, con el número de turno,
para auditar; quien decide vuelve a derivar.

---

## 10. Scheduling

#### GD-07. Un conductor en el mismo proceso, un bucle sobre el orden topológico

El conductor vive en `bin/ejecucion/grafo.py`, corre en el proceso de `dev-harness.py ejecutar` y llama
a `motor.ejecutar` de a una vez. No importa nada de concurrencia, no lanza procesos y no usa
`proceso.lanzar` (ME-E47, E-41). Toda escritura la hace por funciones de `registro.py` (ME-E46).

**El algoritmo**, que define el comportamiento observable; la forma del código es de quien construya:

```text
conducir(proyecto, clave, pedidoPor):
  0  configuración del motor y catálogo de secretos, como motor.ejecutar.
     Si fallan: error del comando, y no se crea nada.
  1  tomar el candado de la tarea (§14), sin esperar.
     Si no se puede: GRAPH_ALREADY_ACTIVE, y no se crea nada.
  2  con el candado: cerrar los GraphRuns huérfanos de la tarea (§16.1) y barrer las carpetas
     grf_… sin inicio.json.
  3  motor.recuperar(clave)                                   (Task 4, sin cambios)
  4  leer el plan con la regla de lectura de la admisión, y su TaskKey; F = huella(plan).
     Si falla: GRAPH_PLAN_UNREADABLE, y no se crea nada.
  5  validar la estructura (§11.1); orden = orden_de_ejecucion(workUnits).
     Si falla: GRAPH_STRUCTURE_INVALID, y no se crea nada.
  6  crear el GraphRun: carpeta grf_…, inicio.json. Desde acá existe.
  7  para cada unidad w de orden:
       a  si existe la marca de cancelación: cerrar.
       b  releer el plan. Ilegible: cerrar con GRAPH_PLAN_UNREADABLE.
          Otra huella: cerrar con PLAN_FINGERPRINT_CHANGED.
       c  estado de w bajo F (§9.2):
            SATISFIED          seguir con la siguiente (adoptada si no la despachó este GraphRun)
            OPEN, UNREADABLE   cerrar con TASK_EXECUTION_OPEN
            NOT_SATISFIED      cerrar con WORK_UNIT_NOT_SUCCEEDED
            NOT_STARTED        seguir abajo
       d  si alguna Execution de la TaskKey, de cualquier clave, está abierta o ilegible:
          cerrar con TASK_EXECUTION_OPEN.
          (chequeo preventivo, best-effort: no excluye una manual que se publica después, §15.4)
       e  exe = registro.nuevo_id(); escribir la marca de despacho {numero, w, exe}.
       f  si existe la marca de cancelación: cerrar, sin llamar al motor.
       g  motor.ejecutar(proyecto, clave, w, pedidoPor, execution_id=exe, huella_esperada=F).
          Un error del comando: cerrar con DISPATCH_FAILED (§16.3).
       h  derivar otra vez, en este orden:
            la huella del plan ya no es F          cerrar con PLAN_FINGERPRINT_CHANGED
            w está SATISFIED                        seguir con la siguiente
            hay en la TaskKey una abierta ajena     cerrar con TASK_EXECUTION_OPEN
            un turno nombra a exe, no exitosa       cerrar con WORK_UNIT_NOT_SUCCEEDED
            ningún turno nombra a exe               cerrar con ADMISSION_REJECTED (el rechazo al pedir)
  8  todas recorridas: cerrar (queda SUCCEEDED por la regla de cierre).

cerrar(causa): result.json por la regla de cierre (§9), una sola vez; soltar el candado.
```

**El selector es determinista.** Con el mismo plan, el mismo registro y la misma marca de cancelación,
el conductor despacha la misma secuencia: el orden lo da `orden_de_ejecucion`, que ordena por punto de
código dentro de cada nivel (`plan.py:129`), y los ids son `[a-z0-9-]`
(`orchestration-plan.schema.json:193`), así que no depende del locale.

**`executionOrder` no se usa.** Es un orden topológico que no es un cronograma (MC:2037; schema:333), y
lo calcula la misma función que el conductor. Recalcular sobre el plan leído es lo que cierra C2 para
el grafo (§11.1).

**Lo que el conductor lee para decidir** es solo: `status` y `error.code` del resultado del motor, el
estado derivado del registro y la huella del plan. Nunca `detail`, el `artifact`, texto de consola ni
el código de salida (MC:1072).

**Costo.** Cada despacho paga las dos admisiones, con la compuerta normativa y la vigencia del flujo,
que puede ir a la red con 10 s de límite (`admision.py:169`). No se guarda nada en caché entre nodos
(§19). El costo no se midió.

---

## 11. Dependencies

#### GD-08. AND estricto, bajo F, y fail-fast

- **Una unidad es elegible** si su estado es `NOT_STARTED` y todas sus dependencias están `SATISFIED`
  bajo F. Es la regla de la condición 14 (`admision.py:220-234`); el schema no tiene un OR
  (`orchestration-plan.schema.json:289`).
- **Fan-out:** una dependencia satisfecha habilita a varias, que se despachan en serie, en el orden de
  §10.
- **Fan-in:** solo cuando todas sus dependencias están satisfechas. La procedencia ya queda en
  `admission.dependencies` de la request (`admision.py:378`).
- **Fail-fast:** la primera unidad que no queda `SUCCEEDED`, o el primer rechazo, cierra el GraphRun.
  Como el orden es topológico, cuando el conductor llega a una unidad todas las anteriores están
  `SATISFIED`: ninguna unidad se despacha con una dependencia sin satisfacer, y el filtro previo nunca
  depende de la admisión para eso.
- **Propagación:** ningún descendiente, directo o transitivo, de una unidad no exitosa recibe una
  Execution en ese GraphRun, y tampoco las unidades independientes que venían después (GC-17).
- **Terminación:** cada unidad se despacha a lo sumo una vez por GraphRun y el plan es finito, así que
  el GraphRun termina.

#### GD-09. Sin reintento

Una unidad con último turno bajo F —`SUCCEEDED`, abierto, ilegible o terminal no exitoso— **no se
despacha**. Para reintentar una unidad `FAILED`, `CANCELLED` o `REJECTED`, una persona corre
`ejecutar <KEY> --unidad <w>` (turno N+1, ya legal: `admision.py:300`) y después vuelve a lanzar el
grafo, que la adopta. Ningún archivo de `bin/ejecucion/` nombra `maxRetries` (EX-E50).

### 11.1 La estructura, validada antes de existir

Planning valida dependencias y ciclos solo al armar (`plan.py:262`); al leer un plan guardado no
(`plan.py:595-649`, C2), y nunca controla dependencias repetidas (`plan.py:126` usa un `set`). El
GraphRun no arregla Planning: se protege con la función de Planning, sin reimplementarla.

| Caso | Dónde se detecta | Resultado |
|---|---|---|
| Dependencia a una unidad que no existe | `orden_de_ejecucion` (`plan.py:119-124`) | `GRAPH_STRUCTURE_INVALID` |
| Ciclo, incluida una unidad que depende de sí misma | `orden_de_ejecucion` (`plan.py:126-134`) | `GRAPH_STRUCTURE_INVALID` |
| Una dependencia repetida en la misma unidad | El GraphRun, antes de ordenar | `GRAPH_STRUCTURE_INVALID`: si no, la unidad saldría `CONTRACT_INVALID` al pedir (`contrato.py:261-263`) |
| Plan sin unidades | El GraphRun | `GRAPH_STRUCTURE_INVALID`: un grafo vacío no tiene nada que llevar a término |
| Ids de unidad repetidos | La regla de lectura (`admision.py:142-146`) | `GRAPH_PLAN_UNREADABLE` |

En los cinco casos no se crea el GraphRun ni ninguna Execution.

---

## 12. Admission

**La regla de quince condiciones no cambia** (`admision.py:251-308`; `contrato.py:87-103`). El
GraphRun la provoca, una vez por intento, a través de `motor.ejecutar`, que la aplica al pedir y al
entregar.

Dos cambios internos, sin cambio de contrato:

| Cambio | Para qué | Contrato |
|---|---|---|
| `admision.leer_plan(proyecto, clave)`: público, el mismo cuerpo que `_leer_plan` | Que el GraphRun lea el plan con la misma regla de lectura que la admisión, sin duplicarla | Ninguno |
| `al_entregar(..., huella_esperada=None)`: si viene y `request.plan.planFingerprint` es otra, `PLAN_CHANGED` | §18 | `PLAN_CHANGED` en `REJECTED` ya es legal (`contrato.py:60`), y va en su lugar de la precedencia, la condición 4 |

**Qué se lleva el GraphRun de cada rechazo:**

| Rechazo | Dónde | Qué ve el conductor | Cierra con |
|---|---|---|---|
| Cualquiera al pedir (`PLAN_NOT_READY`, `DELEGATION_NOT_ALLOWED`, `NORMATIVE_GATE_BLOCKED`, `AGENT_*`, `CAPABILITY_UNAVAILABLE` por 13a, `CONTRACT_INVALID`…) | `al_pedir`; no hay Execution (`contrato.py:53-55`) | Ningún turno nombra al `executionId` preasignado | `ADMISSION_REJECTED`, con `executionCode` |
| `DUPLICATE_EXECUTION` al pedir, o perder la reserva | Otro actor tomó la clave en la ventana | La unidad está `OPEN` por una ajena, o ya `SATISFIED` | `TASK_EXECUTION_OPEN`, o sigue |
| `DEPENDENCY_NOT_SATISFIED` o `WORK_UNIT_NOT_FOUND` al pedir | Casi siempre, el plan cambió | La huella ya no es F | `PLAN_FINGERPRINT_CHANGED` |
| Cualquiera al entregar | La Execution queda `REJECTED` | Un turno nombra a `exe`, `REJECTED` | `WORK_UNIT_NOT_SUCCEEDED` |

**Los cinco códigos que «no alcanzan solos»** según WU06 (`CONTRACT_INVALID`, `DUPLICATE_EXECUTION`,
`DEPENDENCY_NOT_SATISFIED`, `WORK_UNIT_NOT_FOUND`, `WORK_UNIT_NOT_PENDING`) no necesitan `detail`: el
conductor no decide por el código del rechazo sino por lo que vuelve a derivar del registro y del plan
(paso 7h), y el código queda referenciado en la causa.

---

## 13. Persistence

#### GD-12. Cuatro marcas de una sola escritura, y el estado se deriva

```text
.claude/ejecuciones/<TaskKey>/grafos/
  vivo.lock                  el candado de la tarea (§14). Archivo estable: no se borra, y su
                             existencia no significa nada; solo cuenta si está tomado
  <graphRunId>/
    inicio.json              una vez, al crear: el GraphRun existe
    despachos/<NNN>.json     una vez cada uno, antes de llamar al motor
    cancelacion.json         una vez, a pedido
    result.json              graph-run-result/1.0, una vez, al cerrar
```

| Marca | Claves, cerradas | Por qué hace falta |
|---|---|---|
| `inicio.json` | `graphRunId`, `taskKey`, `planFingerprint`, `planId`, `planVersion`, `requestedBy`, `startedAt`, `nodes: [{workUnitId, dependencies}]`, `order` | La existencia, F y quién lo pidió no se derivan de nada (WU08 X1). El conjunto de nodos sobrevive a una reescritura del plan, que no es atómica (`plan.py:588`) y lo pisa en el lugar (WU08 X2) |
| `despachos/<NNN>.json` | `numero`, `workUnitId`, `executionId`, `dispatchedAt` | La request no puede llevar un `graphRunId` (`execution-request.schema.json:9`): sin la marca, «qué Executions creó este GraphRun» no se deriva (WU08 X5) |
| `cancelacion.json` | `pedidoEn`, `pedidoPor` | La cancelación del grafo no la expresa ningún archivo del registro de Executions (WU08 X3) |
| `result.json` | §23 | Un terminal que no cambia: después de un `FAILED`, un reintento manual agrega turnos y el estado derivado «revive» (WU08 X6) |

- **Todo se escribe una sola vez**, con `registro.escribir_una_vez` (`registro.py:180-202`). No hay
  `state.json`, ni puntero a «la unidad actual», ni contador. `vivo.lock` es el único archivo que no es
  una marca, y nadie lo lee.
- **Las marcas no tienen schema**, como los archivos de infraestructura de Execution (T4 MD-03): cada
  una se valida en código con su conjunto cerrado de claves. `result.json` sí lo tiene (§23).
- **Va bajo `.claude/ejecuciones/`**, por cuatro razones verificadas:
  - la evidencia de toda Execution excluye esa raíz (`evidencia.py:27`, `:78`): lo que escribe el
    GraphRun nunca aparece como cambio de una Execution;
  - `carpetas` y `otras_entregadas` filtran `exe_…` (`registro.py:60`, `:466-471`): `grafos/` no es un
    residuo, no se barre y no cuenta como otra entrega;
  - `tareas` filtra TaskKeys (`registro.py:474-480`);
  - ME-E46 admite escrituras de `registro.py` bajo esa raíz (t72:2175-2183).
- **Toda escritura pasa por `registro.py`.** `grafo.py` no abre un archivo para escribir (ME-E46).

**¿Se puede reconstruir un GraphRun desde el Plan y el registro de Executions?** El progreso, sí: el
estado de cada unidad sale de su clave. La entidad, no: le faltan su existencia y F (`inicio.json`), su
cancelación (`cancelacion.json`), qué Executions despachó (`despachos/`) y un terminal que no cambie
(`result.json`). Son exactamente las cuatro marcas, y nada más.

#### GD-13. La idempotencia es la de Execution

La idempotencia de cada intento es la clave `huella([taskKey, F, workUnitId])`, sin cambios. El
GraphRun no agrega otra: no despacha una unidad con turno bajo F (GD-09), y dos GraphRuns de la misma
F operan sobre las mismas claves. Lanzar dos veces el grafo sobre un plan terminado deja dos GraphRuns
`SUCCEEDED` y ninguna Execution nueva.

---

## 14. Atomicity

### 14.1 El candado de la tarea

**Ser el conductor de un GraphRun es tener tomado el candado de la tarea**:
`.claude/ejecuciones/<TaskKey>/grafos/vivo.lock`, con la misma primitiva del sistema operativo que el
candado de vida (`registro._bloquear`, `registro.py:226-231`), sin esperar.

- **Archivo estable.** Se abre con `O_CREAT` y **sin** `O_EXCL`, y no se borra nunca. Su existencia no
  dice nada; solo dice algo que esté tomado. Así no repite N1: no hay un instante en que «el archivo
  existe y no está tomado» signifique «el dueño murió», porque el GraphRun se crea **después** de
  tomar el candado.
- **Se toma antes de crear y se suelta después del terminal.** `inicio.json` se escribe con el
  candado tomado, y el candado se suelta después de `result.json`. Si el proceso muere, el sistema
  operativo lo suelta: sin fechas ni pids (`registro.py:25-26`).
- **Quién lo toma:** el conductor al arrancar, y `--cancelar grf_…` para cerrar un huérfano (§17). Nadie
  más. `--grafo --estado` no lo sondea.
- **La consecuencia**, que es la invariante central: con el candado tomado, ningún otro conductor vive
  en la tarea. Por eso **todo GraphRun `ACTIVE` que ve quien lo tomó es huérfano**, y por eso hay a lo
  sumo uno `ACTIVE` por TaskKey después del paso 2 de §10.
- **Lo que puede pasar:** un `--cancelar grf_…` que tiene el candado un instante hace que un `--grafo`
  que arranca en ese mismo instante salga con `GRAPH_ALREADY_ACTIVE`. Es vivacidad, no seguridad: no se
  crea nada, y se vuelve a lanzar.

### 14.2 Dos schedulers, la misma unidad

El equivalente de grafo de «dos schedulers, misma WorkUnit elegible» tiene dos capas, y ninguna es el
rechazo tardío de la admisión:

| Capa | Excluye | Cuándo |
|---|---|---|
| El candado de la tarea | Dos conductores de la misma tarea | Antes de crear el GraphRun |
| El turno exclusivo de Task 4 (`os.link`, `registro.py:362-369`) | Dos Executions de la misma clave, sea quien sea el que pide | Al crear la Execution, **antes** de la entrega: el perdedor no deja Execution (T4 MD-04) |

Con un conductor y una persona sobre la misma unidad, gana uno el turno; el otro recibe
`DUPLICATE_EXECUTION` sin Execution. El conductor que pierde lo deriva del registro y se detiene
(`TASK_EXECUTION_OPEN`). **Nunca hay dos entregas reales de la misma clave.**

**Ninguna de las dos capas excluye la TaskKey entera.** El candado de la tarea excluye conductores, no
Executions manuales; el turno excluye por clave. Una manual de **otra** unidad que se publica después
del chequeo 7d puede convivir con la Execution propia del GraphRun: es la carrera residual de GD-15 y
§15.4, parte normativa de esta spec, no una falla del candado.

#### GD-14. Varios GraphRuns: secuenciales, cada uno con su terminal

- A lo sumo uno `ACTIVE` por TaskKey (§14.1).
- Varios en el tiempo sobre la misma (TaskKey, F): cada uno con su id y su terminal; el segundo adopta
  lo que el primero dejó `SUCCEEDED`.
- Sobre otra F: claves disjuntas por construcción. El primero, si sigue vivo, se detiene con
  `PLAN_FINGERPRINT_CHANGED` en su próximo paso.
- De tareas distintas: candados distintos. Pueden correr a la vez; ver §15.

#### GD-15. Una Execution manual mientras hay un GraphRun

| Lo que encuentra el conductor | Qué hace |
|---|---|
| Una manual `SUCCEEDED` bajo F | La adopta: el nodo está `SATISFIED`, marcado como no despachado por el GraphRun |
| Una manual `FAILED`, `CANCELLED` o `REJECTED` bajo F | El nodo está `NOT_SATISFIED`: cierra con `WORK_UNIT_NOT_SUCCEEDED` (GD-09) |
| Una manual abierta o ilegible en la TaskKey, de cualquier clave, **observada antes del despacho** (7c o 7d) | Cierra con `TASK_EXECUTION_OPEN`, nombrando su `executionId`. No la cancela, no la espera, no la adopta como propia |
| Una manual **de la misma clave** que compite **después** del chequeo 7d | Gana una sola reserva del turno (`os.link`); nunca dos entregas. El conductor lo deriva en 7h: sigue si la ganadora quedó `SUCCEEDED`, o cierra con `TASK_EXECUTION_OPEN` (GE-E32) |
| Una manual **de otra unidad** cuyo turno se publica **después** del chequeo 7d | **Puede coexistir** con la Execution propia del GraphRun. Si sus `RUNNING` se solapan, la evidencia de cada una puede quedar `CHANGES_UNATTRIBUTABLE` por la regla de Task 4, sin atribuir de más. El GraphRun no despacha otra propia mientras la suya siga abierta, y al seguir trata la unidad de la manual con la regla de §9.2 (§15.4, GE-E71) |

La manual **nunca se rechaza** por el GraphRun ni se cancela, tampoco en la carrera residual: la
persona que corre `--unidad` sigue teniendo el motor de Task 4 tal cual. Excluir la carrera residual
exigiría una condición 16 de admisión o un candado del GraphRun dentro de ExecutionAdmission: cambia
Task 3, y esta Task no lo hace.

---

## 15. Concurrency

#### GD-06. Serialidad

El GraphRun despacha como máximo una Execution propia a la vez. Antes de cada despacho comprueba que
no exista otra Execution abierta o ilegible en la misma TaskKey y, si la observa, falla con
`TASK_EXECUTION_OPEN`. Esa comprobación no crea exclusión global de la TaskKey: una Execution manual
de otra WorkUnit puede comenzar después del chequeo y coexistir con la Execution del GraphRun. Cuando
eso ocurre, la evidencia conserva la semántica conservadora de Task 4 (§15.4).

**Serial quiere decir** serialidad del conductor y de las Executions propias del GraphRun, no
exclusividad total de las Executions de la TaskKey:

- un solo conductor por TaskKey (§14.1);
- una sola Execution propia del GraphRun en vuelo;
- ningún paralelismo interno del GraphRun;
- ninguna segunda WorkUnit propia hasta el terminal de la anterior.

| Dimensión | Serial (se elige) | Paralelismo acotado | Paralelismo pleno |
|---|---|---|---|
| Determinismo | Secuencia y evidencia reproducibles | Cambia el orden de terminación y qué alcanza a arrancar antes de una falla | Peor |
| Evidencia | Atribuible: nunca dos Executions propias a la vez | `CHANGES_UNATTRIBUTABLE` en todo solapamiento (`evidencia.py:141`; `registro.py:489-506`) | Colapsa |
| N1 | Solo con actores externos, y GD-20 lo cierra | Una sonda por proceso y por carpeta de la tarea | Máximo |
| Contención del Host | Un Host, un árbol de trabajo | N Hosts sobre el mismo árbol | Sin techo |
| Guardas | ME-E47 y E-41 intactas | Hilos prohibidos; subprocesos rompen E-41 (GC-04) | Igual |
| Recuperación | A lo sumo una huérfana propia por caída | N huérfanas y N Hosts vivos (R1×N) | Igual |
| Costo operativo | Tiempo = suma | Menos tiempo, más tokens a la vez, cancelación de N | Máximo |

**El paralelismo no se puede tener sin cambiar Task 4**: la regla de evidencia es por proyecto, el
árbol de trabajo es uno, y las guardas prohíben las dos formas de lograrlo. Serial no es una
concesión: es lo único que conserva la atribución entre las Executions del GraphRun. GP-03 dice qué
haría falta para revisarlo.

**Entre tareas:** dos GraphRuns de tareas distintas, o un GraphRun y un `--unidad` de otra tarea,
pueden correr a la vez, como hoy dos `--unidad`. Cuando se solapan, la evidencia que detecta a la otra
por la regla de Task 4 queda `CHANGES_UNATTRIBUTABLE`: degrada, no miente. No se agrega un candado de proyecto,
porque Task 4 no lo tiene y sería una restricción nueva sin un caso de corrección que la pida.

### 15.1 N1, como escenario concreto

Reconstruido por WU04 y releído en el código:

| Paso | Proceso | Dónde | Qué pasa |
|---|---|---|---|
| 1 | A | `registro.py:390` | `mkdir` de `exe_A` |
| 2 | A | `registro.py:248` | `os.open(vivo.lock, O_CREAT\|O_EXCL\|O_RDWR)`: el archivo existe, **sin candado** |
| 3 | B | `motor.py:211` → `:394` → `registro.py:532` | `recuperar` → `barrer`: `exe_A` no tiene turno, es «residuo»; `candado_libre` corre **antes** que la guarda de edad, **toma el candado** |
| 4 | A | `registro.py:250` | `_bloquear` falla con `OSError` |
| 5 | A | `registro.py:399-404` | `crear` borra su carpeta y relanza |
| 6 | A | `motor.py:222-224` | `ErrorDelComando`: «no se pudo crear la Execution», sin ExecutionError |

`limpiar_temporales` (`registro.py:555`) es un segundo punto con la misma forma, y además borra
temporales de una carpeta ajena cuyo candado está libre: un `request.json` a medio escribir, o el
`cancelacion.json` de un `--cancelar` concurrente (FH, ítem 14). La firma coincide con la falla
observada en ME-E18 («1 Execution(s), [], 1 turno(s)», `verificacion.md:952-953`), y la verificación la
forzó (`verificacion.md:975-981`). **Es pérdida de vivacidad, no de seguridad**: nunca hubo dos
Executions ni dos turnos.

**Con el GraphRun**, cada despacho llama a `recuperar` (`motor.py:211`), y un conductor más una
persona sobre la misma tarea abren la ventana.

### 15.2 Lo que se descartó

| Alternativa | Por qué no |
|---|---|
| Sondear dos veces (FH) | La víctima es la que crea, no la sonda |
| `Vida` reintenta `_bloquear` unos milisegundos | Achica la ventana, no la cierra |
| Tomar el candado antes de que el archivo sea visible (renombrar con un handle abierto) | En Windows no está comprobado |
| Un mutex de admisión por TaskKey | T4 MD-04 lo descartó por el recorrido; agrega un candado que GD-20 no necesita |
| No arreglarlo, porque el GraphRun es serial | El GraphRun más una persona sobre la misma tarea es el caso de §14.2 |

### 15.3 GD-20: ninguna sonda toca una carpeta en creación

Dos cambios en `registro.py`, sin candado nuevo:

- **F1, `barrer`:** la guarda de edad va **antes** que el candado. Una carpeta sin turno con
  `_edad <= UMBRAL_DE_RESIDUO` (600 s, `registro.py:67`) no se sondea. Las dos condiciones siguen siendo
  necesarias para borrar.
- **F2′, `limpiar_temporales`:** en cada carpeta `exe_…` mira solo los temporales con más de
  `UMBRAL_DE_RESIDUO` segundos, por su propia fecha. Si no hay ninguno, no sondea el candado. Si hay, y
  el candado está libre, borra solo esos. Es la regla que la función ya aplica a los temporales de los
  turnos (`registro.py:563-570`). Vale igual para las carpetas `grf_…`, que limpia solo quien tiene el
  candado de la tarea.

**Por qué alcanza:** una creación tarda milisegundos, así que su carpeta y sus temporales son nuevos;
las otras sondas —`Tomado` en `recuperar` y `cancelar`, y `motor.estado`— miran solo Executions con
turno, y una Execution con turno ya tiene su candado tomado, porque `Vida` va antes del turno
(`registro.py:393` < `:398`).

**Lo que cambia de Task 4:** T4 §14.1 punto 5 dice «borra los temporales de toda carpeta cuyo candado
esté libre» (`spec.md:682-683`); pasa a decir «con más de diez minutos». Un temporal nuevo se queda
hasta la próxima recuperación después del umbral: lo único que cuesta es disco. Cierra también la mitad
«`--cancelar` racing a recovery that deletes its temporary file» del ítem 14 de FH.

### 15.4 Carrera residual con ejecución manual

```text
chequeo de la TaskKey best-effort  !=  mutex de la TaskKey
```

El chequeo 7d mira el registro **en un instante**; nada impide que, un instante después, una persona
publique una Execution en la misma TaskKey. Una Execution existe recién cuando un turno la nombra
(`registro.py:21-23`), así que lo que cuenta es cuándo se publica su turno:

```text
t0  el GraphRun hace el chequeo 7d: no ve ninguna Execution abierta
t1  una persona corre  ejecutar <KEY> --unidad X   y su turno se publica
t2  el GraphRun despacha B
t3  X y B pueden quedar abiertas a la vez, si X != B
```

**Lo que hace Task 4, leído en `e33b41b`** (es de Task 4; esta Task no lo cambia ni lo amplía, y la
fila de la evidencia es un ejemplo, no un catálogo de los caminos del motor; 27.1 O):

| Caso | Qué pasa | Evidencia |
|---|---|---|
| X y B son la misma unidad (la misma clave) | `al_pedir` rechaza un duplicado si el último turno no es `FAILED`, `CANCELLED` ni `REJECTED`, y dos pedidos que pasan a la vez compiten por el mismo turno `leido + 1` con `os.link`, que no reemplaza: uno gana, el otro recibe `DUPLICATE_EXECUTION` y su carpeta se borra. Nunca dos entregas | `admision.py:298-301`; `registro.py:197`, `:362-369`, `:398`, `:405-408`; `motor.py:225-228` |
| X y B son unidades distintas | La regla de duplicados es por clave: ninguna de las dos se rechaza por la otra | `admision.py:297-301` |
| Las dos llegan a `RUNNING` y se solapan | La evidencia de cada una la arma el motor de Task 4, por sus propios caminos; esta spec no los enumera. Lo leído y lo observado, como ejemplos y no como lista exhaustiva: al cerrar una corrida con su motor vivo, el motor pregunta si otra Execution del proyecto estuvo `RUNNING` desde su propia entrega; si la hubo, se vio la evidencia `CHANGES_UNATTRIBUTABLE`, sin archivos, y también `CHANGES_UNRESOLVED` cuando el árbol no se resolvió antes de esa pregunta: por ejemplo, sin una de las dos fotos (`evidencia.py:127-128`), o con HEAD sin commits aunque las dos fotos se hayan tomado, porque git no compara las revisiones (`evidencia.py:93-94`, `:130-132`; refuter I, P2). Las dos son conservadoras: ninguna atribuye archivos. La recuperación de una huérfana usa otra regla, que no pregunta por las otras (`evidencia.py:161-168`) | `motor.py:309-311`, `:347-349` (`:299-301`, `:337-339` en `e33b41b`); `registro.py:489-506`, numerado según `e33b41b` (texto sin cambio; `:522-539` en el árbol actual); `evidencia.py:93-94`, `:127-128`, `:130-132`, `:141-142` |
| La evidencia no atribuible | No cambia el `status` de la Execution: B puede quedar `SUCCEEDED` con `evidence.changes.state: CHANGES_UNATTRIBUTABLE`. El contrato solo exige, con ese estado, la lista de archivos vacía | `contrato.py:347-352`; ninguna regla de `contrato.py:306-345` ata el `status` a la evidencia |

**Lo que hace el GraphRun en la carrera:**

- **no despacha una segunda Execution propia** mientras B siga abierta: `motor.ejecutar` es
  sincrónico y el conductor no tiene otro camino de despacho;
- **no cancela** a X, **no la rechaza** retroactivamente, **no la toma como propia** (ninguna marca de
  despacho suya la nombra) y **no atribuye** cambios de X a B ni reescribe la evidencia de ninguna:
  la evidencia es de cada Execution y se escribe una sola vez (`motor.py:135-146`);
- después del terminal de B sigue con su algoritmo normal: si B no quedó `SUCCEEDED`, cierra por 7h;
  si quedó, al llegar a la unidad siguiente vuelve a mirar el registro. Si X sigue abierta, 7c o 7d
  la ven y cierra con `TASK_EXECUTION_OPEN`. Si X es un nodo de este mismo GraphRun y ya terminó
  `SUCCEEDED` bajo F, la adopta: `SATISFIED`, `dispatched: false`, sin volver a ejecutarla. Si terminó
  no exitosa, cierra con `WORK_UNIT_NOT_SUCCEEDED` al llegar a ella.

**Por qué se acepta:** cerrar la ventana exige que la admisión de una manual conozca al GraphRun (una
condición 16, o un candado del GraphRun dentro de ExecutionAdmission, o que `ejecutar --unidad` se
rechace con un GraphRun activo). Las tres cambian Task 3 —`PRECEDENCIA`, los 23 códigos o la regla
de quince condiciones— y dejan de lado el `ejecutar --unidad` de Task 4. La carrera cuesta evidencia
no atribuible o sin resolver, no corrupción: degradación conservadora. Se registra como riesgo aceptado (§30.1).

---

## 16. Recovery

#### GD-10. El que toma el candado cierra los huérfanos; nadie reanuda

### 16.1 Cerrar un GraphRun huérfano

Con el candado de la tarea tomado (paso 2 de §10, o `--cancelar grf_…` en §17):

1. llama a `motor.recuperar(clave)` (`grafo.py:323`). Qué cierra es de Task 4, por su regla (T4 MD-24);
   lo observado: una `RUNNING` sin motor queda `FAILED HOST_INTERRUPTED`, o `CANCELLED` si tenía pedido,
   salvo que otro proceso tenga su candado de vida (§17.4, límites 7 y 8 c);
2. si el huérfano tiene `cancelacion.json`: llama a `motor.cancelar` sobre cada Execution **propia** que
   el registro da abierta (`grafo.py:324-326`). Es cumplir un pedido persistido, no una decisión del
   GraphRun. Qué deja esa llamada es de Task 4; lo observado: una `REQUESTED` propia sin motor quedó
   `CANCELLED` (`motor.py:469-478`), salvo §17.4, límite 8 c);
3. escribe el `result.json` por la regla de cierre (§9), por el estado de cada nodo bajo F: `SUCCEEDED`
   si todos están satisfechos, `CANCELLED` con marca, y si no `FAILED` con **`GRAPH_INTERRUPTED`**.

Sin marca de cancelación, el cierre **no** llama a `motor.cancelar`: una `REQUESTED` propia sin motor (R2)
queda abierta, el `result.json` la nombra con el comando para cancelarla (`grafo.py:282-297`) y, si
sigue abierta, el GraphRun siguiente se detiene con `TASK_EXECUTION_OPEN` y ese comando.

**Un GraphRun `ILEGIBLE` no se cierra** (enmienda del 14-10-2026, 27.1 G). Si su `inicio.json` no
valida, no hay F ni conjunto de nodos sobre los que aplicar la regla de cierre; si no valida su
`result.json`, ya tiene un terminal, y escribir otro rompe la escritura de una sola vez (GD-12). Por
eso:

- el paso 2 de §10 no lo cierra ni lo toca, y el conductor **sigue de largo**: un `ILEGIBLE` no bloquea
  a otro GraphRun de la tarea (`registro.activos` solo cuenta `ACTIVE`, `registro.py:903-907`;
  `grafo.py:321-322`, `:331-340`);
- sus Executions siguen las reglas de Execution: una `RUNNING` sin motor la cierra `motor.recuperar`
  (paso 3 de §10, `grafo.py:564`), y una abierta o ilegible detiene al GraphRun nuevo con
  `TASK_EXECUTION_OPEN` (GD-15), que nombra el comando para cancelarla con `--cancelar exe_…`. Una
  `SUCCEEDED` bajo F se adopta como cualquier otra (§9.2);
- `--grafo --estado` lo muestra `ILEGIBLE`, con el motivo y sin comandos (`grafo.py:686-716`);
- `--cancelar grf_…` sobre él es un error del comando que dice que no se lee, y no escribe nada, ni la
  marca (`grafo.py:632-633`): nadie la cumpliría.

Lo resuelve una persona, a mano. Lo fija GE-E70.

### 16.2 Las ventanas de corte

| Ventana | Qué queda en disco | Qué pasa después | ¿Doble entrega? |
|---|---|---|---|
| G1, antes del primer despacho | `inicio.json` | El próximo `--grafo` lo cierra `GRAPH_INTERRUPTED` y crea otro | No |
| G2, después de elegir (marca de despacho escrita, motor sin llamar) | La marca nombra un `exe_…` que ningún turno nombra | Huérfano cerrado; el GraphRun siguiente despacha la unidad con otro id | No |
| G3a, adentro de `crear`, antes del turno | Una carpeta sin turno: un residuo (T4 MD-04d) | La unidad sigue `NOT_STARTED`; el residuo se barre a los 10 minutos | No |
| G3b = G4, turno escrito, sin `entrega.json` | `REQUESTED` sin motor (R2) | El GraphRun siguiente se detiene con `TASK_EXECUTION_OPEN`; una persona cancela | No |
| G5, `RUNNING` | `entrega.json` sin resultado | El GraphRun siguiente llama a `recuperar` (paso 3); qué hace es de Task 4 (T4 MD-24; observado: `FAILED HOST_INTERRUPTED`, o `CANCELLED` con su propio pedido). Con el nodo `NOT_SATISFIED`, o todavía abierto, el GraphRun siguiente se detiene en 7c | No: no se reintenta |
| G6, Execution terminal, el conductor no lo vio | `result.json` de la Execution | `SUCCEEDED` se adopta y se sigue; otro terminal detiene | No |
| G7, todo terminal, sin terminal del GraphRun | Todo `SUCCEEDED` | El cierre del huérfano escribe `SUCCEEDED` | No |

**«Reanudar» no se usa** para nada de esto: ninguna Execution existente se vuelve a entregar
(`entrega.json` se escribe una vez, y nada vuelve a entrar a `_correr` para un id existente,
`motor.py:221-233`), y ningún GraphRun se vuelve a abrir. **Re-entrar** es crear un GraphRun nuevo que
reconstruye el estado leyendo.

### 16.3 Lo que el conductor hace con una interrupción y con un error del comando

- **Ctrl-C mientras el motor tiene la Execution entregada:** qué hace el motor es de Task 4, y esta
  spec no enumera sus caminos (§17.2, 27.1 O). Lo observado, como ejemplos: con el Host vivo, o ya
  salido mientras el motor arma el resultado, el motor lo absorbe y devuelve la unidad `FAILED
  HOST_INTERRUPTED`, o `CANCELLED` si el pedido de la Execution estaba persistido cuando lo miró, aunque
  el Host haya salido con 0 o 1 (`motor.py:296-299`, `:330-334`; `:286-289`, `:320-324` en `e33b41b`;
  refuter H, `ctrlc-real`). Lo que es de Task 5: si el motor le devuelve la Execution, el conductor
  deriva su nodo del registro (7h) y, si el nodo no quedó `SATISFIED`, cierra: no hay otro despacho
  (GE-I21).
- **Ctrl-C que llega al conductor** (en el conductor, o uno que sale del motor; lo observado: antes de
  la entrega, `motor.py:236-240`, y después, un segundo Ctrl-C mientras el motor cierra la corrida del
  primero, refuter I, P3): cierra el GraphRun por la regla (`GRAPH_INTERRUPTED` si no hay marca ni está
  todo satisfecho), suelta el candado y deja salir la interrupción (`grafo.py:388-394`). No llama al
  motor sobre su Execution (§17.4, límite 8 a). Si muere antes de escribir, el cierre lo hace el próximo que tome el
  candado.
- **`ErrorDelComando` del motor:** no quiere decir «no hay Execution». Puede salir antes de publicar
  (N1, disco, configuración) o después (un resultado que no valida, `motor.py:138-140`). El conductor
  deriva por el `executionId` preasignado: si un turno lo nombra, la causa lo referencia con su estado.
  Cierra con **`DISPATCH_FAILED`** en los dos casos.
- **Otra excepción:** sale del conductor sin cerrar; el GraphRun queda huérfano y se cierra con
  `GRAPH_INTERRUPTED`. El conductor no disfraza un bug de resultado.

---

## 17. Cancellation

#### GD-11. Una marca, propagada solo a lo propio

📌 **Qué es norma en esta sección** (27.1 P). Son normativos GD-11, §17.1 y §17.2: describen acciones del
código de Task 5 que se cumplen siempre, y §17.2 las lista, (a) a (f). §17.3 y §17.4 son observaciones,
no normativas: lo que se vio y se leyó de Task 4, del Host y de otros procesos, sin promesa. Donde GD-11
nombra una conducta de Task 4, la nombra como observación.

`ejecutar <KEY> --cancelar grf_…`:

1. valida los ids; el GraphRun tiene que existir. Si ya es terminal **cuando el comando lo lee**, lo
   informa y no escribe nada. La lectura y la marca del paso 2 no son atómicas (quien cancela no toma el
   candado para escribirla): si quien tiene el candado (el conductor, o quien cierra el huérfano: un
   `--grafo` nuevo u otro `--cancelar`) escribe el terminal entre las dos, la marca queda escrita después
   del `result.json`, o entre la lectura de la marca de la regla de cierre (`grafo.py:188`) y el
   `result.json`. Es inerte: el terminal no se reescribe (GE-I14), nadie la lee para decidir (el que
   cerró ya cerró y §16.1 no toca un GraphRun que no está `ACTIVE`), y el `cancelRequested` del
   terminal sigue diciendo si la marca existía cuando la regla de cierre la leyó (GD-23). Ver §17.3
   (27.1 K y N);
2. escribe `cancelacion.json` una vez, con `pedidoPor` redactado. Si ya estaba, sigue;
3. intenta tomar el candado de la tarea:
   - **si lo toma**, el conductor murió (o ya cerró): cierra el huérfano como §16.1 (`grafo.py:657-663`);
   - **si no**, otro tiene el candado: casi siempre el conductor vivo, pero también puede ser otro
     `--cancelar` que está cerrando el huérfano, o un `--grafo` nuevo que lo cierra en su paso 2. En los
     tres casos el informe dice `conductorVivo: true` (`grafo.py:664`), que quiere decir solo que el
     candado estaba tomado. En vueltas separadas por pausas de a lo sumo un segundo, hasta que una vuelta
     termina con vencida la ventana de 60 s contada desde la marca (`grafo.py:601-602`, `:650`,
     `:668-670`; una vuelta lenta puede llevar la salida más allá de los 60 s): llama a `motor.cancelar` sobre cada Execution **propia** que un turno nombra y que el
     registro da abierta en esa vuelta (`grafo.py:263-279`, `:665`), e intenta el candado. Cuando lo
     toma, si el GraphRun ya tiene terminal, termina; si no, cierra como §16.1. Si el GraphRun ya es
     terminal y el candado sigue tomado (por ejemplo, por un `--grafo` nuevo que cerró el huérfano y
     sigue con el suyo), sigue sondeando hasta tomarlo o hasta que venza la ventana, y sale con 0 y
     `sigue: false`. Es un sondeo con ventana. Una que se abre y termina
     entre dos vueltas, o cuyo turno aparece después de la última vuelta (la ventana venció), no recibe
     ninguna llamada de este comando. Lo que pasa después es de Task 4 y es observación, no norma: si el
     pedido queda persistido depende del estado de la Execution cuando `motor.cancelar` la lee
     (`motor.py:448-468`; refuter I, P4: la vuelta la vio `RUNNING`, y la Execution cerró antes de que
     `motor.cancelar` la leyera, sin `cancelacion.json`), y qué resultado escribe el motor con el pedido
     persistido también (§17.3, §17.4; 27.1 J, L, M, N, O y P);
4. informa el estado antes y después. Sale con 0, como `--cancelar` de una Execution
   (`dev-harness.py:1143-1160` en `e33b41b`; `:1245-1262` en el árbol de trabajo), haya o no cerrado.
   (`canceladas`: ver §17.3 y §17.4, que son observaciones.) Si al salir
   el GraphRun sigue `ACTIVE` (`sigue: true`, `grafo.py:671-673`), la CLI imprime, tal cual, «su
   conductor sigue: el pedido quedó escrito y lo va a cumplir» (`dev-harness.py:1190-1192`). **Eso
   significa exactamente esto, y nada más:** la marca del grafo quedó persistida; el conductor, mientras
   viva, la mira antes de cada despacho (7a y 7f), no despacha ninguna unidad más y, cuando el motor le
   devuelva la Execution en vuelo, deriva el nodo del registro (7h) y cierra por la regla de cierre, por
   el estado de cada nodo bajo F (`CANCELLED` si queda algún nodo sin satisfacer, `SUCCEEDED` con
   `cancelRequested: true` si todos lo están); si muere, lo cierra el próximo que tome el candado
   (§16.1). **No** significa nada sobre cómo termina la Execution que ya estaba en vuelo: eso es de Task 4
   y es observación (§17.3, §17.4).

**Propia** es una Execution que nombra una marca de despacho de ese GraphRun. **Nunca se llama a
`motor.cancelar` sobre una ajena**, ni sobre una manual de la misma tarea. Cancelar una Execution del
grafo desde afuera, con `--cancelar exe_…`, no es cancelar el grafo: si el nodo queda sin satisfacer
(que la Execution quede `CANCELLED` es de Task 4: §17.3, observación 1) y el grafo no tiene marca al
cerrar, el GraphRun cierra con `WORK_UNIT_NOT_SUCCEEDED` (GC-22); con la marca, la regla de cierre da
`CANCELLED`.

### 17.1 Qué hace el conductor con la marca (normativo)

La mira antes de cada despacho (paso 7a) y otra vez **después de escribir la marca de despacho y antes
de llamar al motor** (paso 7f) (`grafo.py:398-399`, `:425-426`). Si está, no llama al motor y cierra.
Fuera de eso, el conductor solo la lee en la regla de cierre (`grafo.py:188`), al escribir el terminal:
**no la mira mientras el motor corre** y no le pide nada al motor (el motor no ve la carpeta del
GraphRun, GE-I29; Task 4 no cambia). Así, después de escrita la marca, el GraphRun no
despacha ninguna Execution nueva, siempre; la única que puede seguir es la que ya pasó 7f antes de la
marca, a lo sumo una (GE-I11). Con la Execution que el motor le devuelve, el conductor hace siempre lo
mismo, sea cual sea el camino del motor: deriva el estado del **nodo** del registro (7h,
`grafo.py:441-458`), no del resultado de esa Execution ni de cómo terminó el Host, y el terminal lo
decide la regla de cierre (GD-05, GD-15) por el estado de cada nodo bajo F (`grafo.py:187-192`):
`SUCCEEDED`, con `cancelRequested: true`, si todos están `SATISFIED`; si no, `CANCELLED` por la marca.
Que la Execution propia termine `CANCELLED` no fija el terminal: el nodo puede quedar `SATISFIED` por
otra Execution de la misma clave, por ejemplo una manual publicada después (refuter I, P1 y P1b, 3 de 3:
Execution propia `CANCELLED`, GraphRun `SUCCEEDED` con `cancelRequested: true`). Los casos observados
están en §17.3 y §17.4, y no son norma.

### 17.2 La ventana entre cancelar y despachar, y lo normativo de la cancelación

```text
conductor:  escribe despacho(exe)  →  mira cancelacion.json  →  motor.ejecutar(exe)
cancelador: escribe cancelacion.json  →  mira despachos         →  motor.cancelar(exe)
```

Las dos escrituras son de una sola vez y visibles enteras. **Al menos uno ve al otro:**

- si el conductor ve la marca, no llama al motor: cero Executions;
- si no la ve, el cancelador escribió después de esa lectura, así que su lectura de los despachos es
  posterior a la marca de despacho y la ve. Verla no es llamar: el cancelador solo llama a
  `motor.cancelar` sobre una Execution que un turno ya nombra y que el registro da abierta
  (`registro.py:910-920`, `grafo.py:263-279`). Qué deja esa llamada en la Execution es de Task 4 (§17.3).

**Lo que pasa con ese pedido es de Task 4.** Sobre una Execution en vuelo, Task 5 solo garantiza lo que
garantiza el motor de Task 4: cuándo y cuántas veces el motor mira el pedido, y qué resultado escribe
con el pedido persistido y la salida del Host, son caminos de Task 4, y esta spec no los enumera (27.1
O). Lo leído y lo observado de esos caminos está en §17.3 y §17.4, como observación y no como norma
(27.1 P).

**Lo normativo de la cancelación, y nada más** (27.1 P). Una afirmación de §17 es normativa solo si
describe una acción del código de Task 5 que se cumple siempre, sin depender de lo que hagan el motor de
Task 4, un Host, el sistema operativo o un tercer proceso. Son estas:

- **(a) La marca.** `--cancelar grf_…` valida los ids y que el GraphRun exista y se lea (si no, error
  del comando, sin escribir); si lo lee terminal, no escribe nada; si lo lee `ACTIVE` y está el catálogo
  de secretos (si no, error del comando, sin escribir), escribe `cancelacion.json` una sola vez, con
  `pedidoPor` redactado, antes de cualquier otra cosa (GD-11, pasos 1 y 2; `grafo.py:624-648`).
- **(b) El candado y el sondeo.** Intenta tomar el candado de la tarea: si lo toma, cierra el huérfano
  como §16.1; si no, en vueltas separadas por pausas de a lo sumo un segundo, hasta
  que una vuelta termina con vencida la ventana de 60 s contada desde la marca, llama a `motor.cancelar`
  sobre cada Execution propia que un turno nombra y que el registro da abierta en esa vuelta, e intenta
  el candado otra vez (GD-11, paso 3; `grafo.py:323-326`, `:601-602`, `:650-670`, llamado sin `intervalo`
  desde `dev-harness.py:1176`). Lo hace mientras el comando no salga antes por un error del comando o
  porque lo cortan (§17.4, límite 5). Nunca llama a `motor.cancelar` sobre una ajena ni sobre una manual
  (GE-I18, GE-I19).
- **(c) 7a y 7f.** El conductor lee la marca antes de cada despacho y después de escribir la marca de
  despacho; si la ve, no llama al motor y cierra: esa unidad no tiene Execution de este GraphRun.
  Después de escrita la marca, el GraphRun no despacha ninguna Execution nueva; a lo sumo una sigue, la
  que pasó 7f antes (§17.1, GE-I11).
- **(d) 7h y la regla de cierre.** El conductor deriva el estado de cada nodo del registro, no del
  resultado de la Execution ni del Host, y el terminal sale de la regla de cierre por el estado de cada
  nodo bajo F: `SUCCEEDED`, con `cancelRequested: true`, si todos están `SATISFIED`; `CANCELLED` si hay
  marca y alguno no lo está (GD-05, GD-15; `grafo.py:187-192`, `:441-458`).
- **(e) Una sola escritura.** El `result.json` del GraphRun se escribe una vez y gana el primero; una
  marca posterior no lo cambia, y su `cancelRequested` dice si la marca existía cuando la regla de cierre
  la leyó (GE-I14, GD-23; `grafo.py:188`, `:203`, `:207-210`).
- **(f) El cruce.** Las dos escrituras cruzadas de arriba: al menos uno ve al otro.

Todo lo demás —qué terminal escribe una Execution propia (`CANCELLED`, `SUCCEEDED` o `FAILED`), si el
pedido queda persistido en ella, si el Host muere, si una Execution propia queda abierta después del
`result.json` del GraphRun, qué escribe el motor, qué dice la evidencia— es observación (§17.3, §17.4) y
no se promete. Un caso nuevo que se comporte distinto no contradice esta lista: se suma como
observación.

**En una oración:** una cancelación de grafo es una marca persistida que el conductor honra antes de
cada despacho: después de la marca, ese GraphRun no despacha ninguna Execution nueva, y su terminal lo
decide la regla de cierre por el estado de cada nodo. Sobre la Execution que ya estaba en vuelo, a lo
sumo una, la que pasó 7f antes de la marca, Task 5 solo garantiza lo que garantiza el motor de Task 4.

### 17.3 Observaciones, no normativas: casos

**Observaciones, no normativas:** lo que se vio con la CLI de producción y el Host falso, y lo que se
leyó en el código de Task 4. No son garantías de Task 5 y no se prometen: describen casos y lo que Task 4
(o el Host, el sistema operativo u otro proceso) hizo en ellos. §17.4 sigue con los límites observados,
con la misma naturaleza. Lo que esta Task promete es solo la lista de §17.2. Las garantías 2 a 4 de las
pasadas anteriores son hoy las observaciones 1 a 3 (27.1 P).

**Lo leído del motor**, como ejemplos y no como lista exhaustiva (§17.4, límites 1 y 2; §30.1, T4
ME-I22): el motor revisa el pedido antes de entregar (`motor.py:263`, `:282`; `:253`, `:272` en
`e33b41b`) y, durante el Host, al comienzo de cada tramo de un segundo (`proceso.py:63-66`), mientras
`wait` devuelve `TERMINO` apenas el Host sale (`proceso.py:72`). Después de que el Host salió, hay
caminos que vuelven a mirar el pedido, por ejemplo una falla `HOST_INTERRUPTED` (`motor.py:335`; `:325`
en `e33b41b`) o un Ctrl-C sobre el motor mientras arma el resultado (`motor.py:296-297`; `:286-287` en
`e33b41b`), y con el pedido ya persistido la Execution quedó `CANCELLED`, también con una salida 0 o 1
en el segundo caso (refuters G y H). Y hay caminos que no lo miran, por ejemplo una salida 1 o 0 sin
Ctrl-C, y la Execution quedó con el resultado del Host aunque el pedido estuviera persistido.

1. **Observación 1 (antes, garantía 2): la llamada y el pedido.** Si el conductor no vio la marca, en la
   vuelta en que el registro da abierta a esa Execution (`REQUESTED` o `RUNNING`) el cancelador llama a
   `motor.cancelar` de Task 4 (eso es la norma (b)). Lo observado: el pedido quedó persistido en la
   Execution propia cuando ella seguía abierta al leerla `motor.cancelar` (`motor.py:448-468`); si cerró
   antes, no hubo pedido aunque figure en `canceladas` (refuter I, P4, 2 de 2: terminó `SUCCEEDED`). Sin
   ninguna vuelta que la encuentre abierta (venció la ventana, §17.4 límite 4; lo cortaron, límite 5; se
   abrió y terminó entre dos vueltas, límite 3), ver la observación 2. Con el
   pedido persistido, el resultado es el que produjo el motor de Task 4. Lo observado, como ejemplos y
   sin pretender que la lista sea exhaustiva: cuando el motor lo revisó antes de entregar o al comienzo
   de un tramo con el Host vivo, la Execution terminó `CANCELLED`, sin `entrega.json` o con el árbol del
   Host terminado; así terminó, con su motor vivo, un Host que siguió vivo varios tramos después de
   persistido el pedido (GE-E48 b)); cuando el motor murió con el pedido ya persistido, la recuperación
   de Task 4 la cerró `CANCELLED` y nadie mató al Host (límite 7), salvo con su candado de vida tomado por
   otro proceso (límite 8 c).
2. **Observación 2 (antes, garantía 3): la Execution con su propio resultado.** Sin pedido, se vio la
   Execution con su propio resultado, sin `cancelacion.json` propio: límites 3, 4 y 5 de §17.4, que
   nacen del sondeo de esta Task. Con el pedido persistido y no cumplido, también con su propio
   resultado y su `cancelacion.json`: límites 1 y 2, como ejemplos. Con el pedido persistido y la
   Execution todavía sin `result.json`, **esta spec no fija qué resultado escribe el motor**: el
   terminal que escriba es válido para esta Task (los observados: `CANCELLED` y el resultado del Host).
   El motor no mira la marca del grafo (GE-I29). El cierre del GraphRun no es observación: es la norma
   (d), por el estado de cada nodo y no por el resultado de la Execution. Lo visto con ella: en A→B, con
   B `SUCCEEDED`, `SUCCEEDED` con `cancelRequested: true` (como GE-E49 y GC-23); en A→B→C, `CANCELLED` en
   7a antes de C; con el nodo sin satisfacer, `CANCELLED`; y con la Execution propia `CANCELLED` y el
   nodo satisfecho por una manual de la misma clave, `SUCCEEDED` con `cancelRequested: true` (refuter I,
   P1 y P1b).
3. **Observación 3 (antes, garantía 4): Executions propias abiertas después del terminal.** Cuando el
   motor le devolvió al conductor el resultado de la Execution, y cuando el cierre de un huérfano con
   marca llamó a `motor.cancelar` sobre una `REQUESTED` sin motor, no se vio ninguna Execution propia
   abierta después del `result.json` del GraphRun. **No es una garantía** (refuter I, F-2): §17.4,
   límite 8, lista los casos observados en que una quedó abierta —un Ctrl-C que sale del motor hacia el
   conductor, antes o después de la entrega; un error del comando del motor después de publicar; otro
   proceso con el candado de vida de la Execution propia mientras se cierra el huérfano, con ella
   `REQUESTED` o `RUNNING`— sin pretender que sean todos.

**Escala, en producción.** Con la CLI de producción el sondeo es de un segundo (`grafo.py:601-602`, llamado sin `intervalo` desde
`dev-harness.py:1176`), la ventana es de 60 s (`grafo.py:601`) y el tramo es de un segundo
(`proceso.py:25`). Así, el límite 1 lo alcanza un Host cuya duración no pasa de un intervalo del
cancelador más un tramo, y algo más por la demora de cada vuelta; y el límite 4, un conductor que tarda
más que lo que le queda a la ventana entre su lectura 7f y el turno de la Execution (en producción, por
ejemplo, una admisión lenta), con un Host de cualquier duración. Los límites 1 y 2 son conducta de Task
4, sin cambios desde `e33b41b`, y son los casos observados, no un catálogo de los caminos del motor:
el 1 choca con T4 ME-I22 (§30.1, 27.1 L), y el 2 choca o no según se lea «antes de que la corrida termine» (la salida del Host o el `result.json`), cosa que esta Task no
decide. Los límites 3, 4 y 5 son de esta Task (27.1 M).

**Casos observados.** Cada fila dice lo que se vio; donde un caso se sigue de la norma de §17.2, la
fila lo nombra.

| Caso | Lo observado (no normativo) |
|---|---|
| Antes del nodo | La unidad no tiene Execution; el GraphRun cierra `CANCELLED`. No se inventa una Execution `CANCELLED`. Se sigue de las normas (c) y (d) |
| Con la Execution `REQUESTED`, y una vuelta del cancelador la encuentra así | El cancelador llama a `motor.cancelar` (norma (b)). Lo observado: el pedido quedó escrito si seguía abierta al leerla `motor.cancelar` (observación 1); sin motor, `motor.cancelar` de Task 4 la cerró `CANCELLED` (`motor.py:469-478`), salvo con otro proceso que tenía en ese instante su candado de vida (§17.4, límite 8). Con su motor vivo, lo mismo que con `RUNNING`: el resultado fue el del motor de Task 4; `CANCELLED` antes del Host cuando el motor revisó el pedido antes de entregar (27.1 L y O) |
| Con la Execution `RUNNING`, y una vuelta del cancelador la encuentra así | El cancelador llama a `motor.cancelar` (norma (b)). Lo observado: el pedido quedó escrito si seguía abierta al leerla `motor.cancelar` (refuter I, P4: no siempre); el resultado fue el del motor de Task 4: cuando lo revisó con el Host vivo (al comienzo de un tramo), mató su árbol y escribió `CANCELLED`, y el GraphRun cerró `CANCELLED`; así terminó, con su motor vivo, un Host que siguió vivo varios tramos después del pedido (GE-E48 b)). Si el Host sale en el mismo tramo, o ya había salido, ver la fila siguiente (observación 1; 27.1 L y O) |
| El Host sale antes de que el motor cumpla un pedido ya persistido (en el mismo tramo, o antes del pedido pero sin `result.json` todavía), o la Execution se abre y termina entre dos vueltas del cancelador | Sin pedido (entre dos vueltas): se vio su propio resultado, sin `cancelacion.json` propio. Con el pedido persistido: el terminal que escribió el motor de Task 4, y esta spec no fija cuál. Lo observado, como ejemplos y no como lista exhaustiva (§17.4, límites 1 y 2): `CANCELLED` con una falla `HOST_INTERRUPTED` o con un Ctrl-C sobre el motor después de que el Host salió (`motor.py:335`, `:296-297`), y el resultado del Host, con `cancelacion.json` propio, con una salida 1 (`HOST_FAILURE`) o 0 sin Ctrl-C. El cierre del GraphRun es la norma (d), por el estado de cada nodo: los cierres vistos están en la observación 2 (§17.4, límites 1 a 3; 27.1 J, L, M, N, O y P) |
| La ventana de 60 s del cancelador vence antes del turno de la Execution en vuelo (el conductor pasó 7f antes de la marca y tardó más que lo que le quedaba a la ventana hasta publicar el turno) | El cancelador sale con 0, con `sigue: true`, sin esa Execution en `canceladas`, y la CLI imprime «su conductor sigue: el pedido quedó escrito y lo va a cumplir». Se la vio correr entera, con su propio resultado y sin `cancelacion.json` propio. El cierre es la norma (d), por el estado de cada nodo; lo visto: en A→B→C, `CANCELLED` en 7a; en A→B con B `SUCCEEDED`, `SUCCEEDED` con `cancelRequested: true`. Otro `--cancelar grf_…` mientras el GraphRun sigue `ACTIVE` abre otra ventana y sí llama (§17.4, límite 4; 27.1 M) |
| El cancelador se corta (Ctrl-C, el proceso muere) después de escribir la marca | Lo mismo que la fila anterior, para cada Execution sobre la que todavía no había llamado: la marca queda y el conductor la honra en 7a y 7f (normas (a) y (c); §17.4, límite 5) |
| El conductor murió con una Execution propia `RUNNING` | El cancelador toma el candado en la primera vuelta en que está libre y cierra el huérfano (§16.1, norma (b)). Lo observado: la recuperación de Task 4 la cerró por su regla (T4 MD-24: `CANCELLED` con su propio pedido, `FAILED HOST_INTERRUPTED` sin él), sin matar al Host, que puede seguir vivo (R1 de T4), y el GraphRun cerró `CANCELLED`. **No siempre:** con otro proceso que tenía en ese instante el candado de vida de la Execution, la recuperación no la tocó y el GraphRun cerró `CANCELLED` con ella `RUNNING` y con pedido (refuter I, P5, 2 de 2; §17.4, límites 7 y 8 c) |
| Todo terminado, sin terminal del GraphRun | `SUCCEEDED`, con `cancelRequested: true` (GC-23). Se sigue de la norma (d) |
| GraphRun terminal cuando el comando lo lee | Nada: lo informa. Es la norma (a) |
| Quien tiene el candado (el conductor, o quien cierra el huérfano: un `--grafo` nuevo u otro `--cancelar`) escribe el terminal entre la lectura y la marca, o la marca queda entre la lectura de la regla de cierre (`grafo.py:188`) y el `result.json` | Residuo aceptado (27.1 K y N): queda un `cancelacion.json` que el terminal no refleja. El terminal no cambia y es la verdad (norma (e)): su `cancelRequested` dice si la marca existía cuando la regla de cierre la leyó. Visto: el comando sale con 0 y su informe dice `antes: ACTIVE`, `despues:` el terminal, `marcaNueva: true`, `cerradoAqui: false`. `--grafo --estado` muestra `cancelRequested: true`, porque ese campo dice si la marca existe hoy (`grafo.py:712`), no lo que dice el terminal |
| GraphRun `ILEGIBLE` | Error del comando; no escribe nada (§16.1, 27.1 G). Es la norma (a) |
| Dos veces | La segunda no escribe otra marca del grafo (norma (a)). Si el GraphRun sigue `ACTIVE`, abre su propia ventana y llama a `motor.cancelar` sobre toda Execution propia que el registro dé abierta, también sobre una que la primera no alcanzó (límite 4). Lo observado de Task 4: no reescribe un pedido de Execution que ya existe, y el pedido a una que no lo tenía sí es un archivo nuevo. Sobre un terminal, no escribe nada (GE-E50) |

### 17.4 Observaciones, no normativas: límites

Agregada el 15-10-2026 (27.1 M), después de que tres verificaciones seguidas (refuters C, E y F)
encontraran cada una una promesa distinta de esta sección que el código no cumplía; reescrita el mismo
día (27.1 O) cuando los refuters G y H encontraron otros caminos del motor, y pasada a observación (27.1
P) cuando el refuter I encontró cuatro frases más del mismo tipo.

📌 **Sobre una Execution en vuelo, Task 5 solo garantiza lo que garantiza el motor de Task 4.** Cuándo
y cuántas veces ese motor mira un pedido de cancelar, y qué resultado escribe con el pedido persistido
y la salida del Host, son caminos de Task 4.

**Esta tabla es observación, como §17.3, y no norma.** Describe lo que se vio y se leyó; no son
garantías de Task 5 y no se prometen. Las filas cuyo origen es Task 4 (1, 2, 7, 9 y la parte R2 del 8)
son **casos observados, como ejemplos, y no una lista exhaustiva** de esos caminos (§30.1, T4 ME-I22).
Las de origen Task 5 (3, 4, 5, 6 y el cierre del 8) describen lo que las acciones normativas de §17.2
dejan sin cubrir, leídas contra el árbol de trabajo sobre `e33b41b`. Lo normativo es solo la lista de
§17.2. La antigua garantía 4 («ninguna Execution propia queda abierta después del `result.json` del
GraphRun salvo el límite 8») ya no es una garantía: es la observación 3, y el límite 8 lista los casos
vistos en que queda una abierta, sin pretender que sean todos.

Ninguna fila es un defecto de la construcción, y ninguna se corrige en esta Task (Nahuel Palacio,
15-10-2026: no se toca el código ni Task 3/4). Los riesgos están en §30.1.

| # | Condición | Lo observado (no normativo) | Origen | Lo hereda de |
|---|---|---|---|---|
| 1 | El pedido de la Execution se persiste después del comienzo de un tramo de `proceso.esperar` y el Host sale antes de que ese tramo termine (refuter E, F-1) | El terminal que escriba el motor de Task 4, sin orden garantizado entre el pedido y la salida. Observado: `CANCELLED`, o el resultado del Host con `cancelacion.json` propio presente; con la salida del Host ya devuelta, rige lo observado en 2 (ejemplos, no lista cerrada) | `proceso.py:63-66` (durante el Host, el pedido se mira al comienzo de cada tramo), `:72` (`TERMINO` apenas el Host sale), `:25` (tramo de 1 s) | Task 4 (choca con T4 ME-I22; GP-08) |
| 2 | El pedido se persiste después de que el Host salió y antes del `result.json` de la Execution, mientras el motor arma el resultado (evidencia, salida) | El terminal que escriba el motor de Task 4; esta spec no fija cuál. Observado, como ejemplos y no como lista exhaustiva: con una falla `HOST_INTERRUPTED` (por ejemplo, salida 130 o 143 sin un resultado de proveedor), `CANCELLED` si el pedido ya estaba cuando el motor lo miró, y si llegó después, `FAILED HOST_INTERRUPTED` (refuter G, F-2: `p_corte` 143, 3/3 `CANCELLED`; refuter H, `n2-143-antes` y `n2-143-despues`); con un Ctrl-C sobre el motor mientras arma el resultado, `CANCELLED`, también con salida 0 o 1 (refuter H, F-1, `ctrlc-real` 3/3); sin Ctrl-C, con salida 1, `FAILED HOST_FAILURE`, y con 0, `SUCCEEDED`, los dos con pedido (refuter G, control 3/3; refuter H, `n2-1-antes`, `n2-0-antes`); con salida 143 y un resultado JSON de proveedor, `FAILED PROVIDER_FAILURE` con pedido (refuter H, `n2-143-proveedor`) | Ejemplos de caminos que miran el pedido: `motor.py:335` (`:325` en `e33b41b`), `:296-297` (`:286-287` en `e33b41b`); la falla la clasifica el Host Adapter (`host_claude_code.py:385-409`: `PROVIDER_FAILURE` gana sobre `HOST_INTERRUPTED`, `:403-407`) | Task 4 |
| 3 | La Execution se abre y termina entre dos vueltas del cancelador (refuter C, F-1) | Este comando no llama a `motor.cancelar` sobre ella; se vio su propio resultado, sin `cancelacion.json` propio | `grafo.py:651-670` (sondeo), `:602` (`INTERVALO = 1.0`), `dev-harness.py:1176` (sin `intervalo`) | Task 5 |
| 4 | La ventana del cancelador vence antes de que la Execution en vuelo tenga turno: entre la lectura 7f del conductor y la publicación del turno pasa más que lo que le queda a la ventana (refuter F, F-1) | Se la vio correr entera con su propio resultado, sin `cancelacion.json` propio. El cancelador sale con 0, `sigue: true`, sin ella en `canceladas`, e imprime «su conductor sigue: el pedido quedó escrito y lo va a cumplir» (GD-11, paso 4, dice qué significa). El cierre es la norma (d), por el estado de cada nodo: `CANCELLED` si alguno queda sin satisfacer, `SUCCEEDED` con `cancelRequested: true` si todos lo están; lo visto (refuter F), `CANCELLED` en 7a en A→B→C y `SUCCEEDED` en A→B con el nodo de B `SATISFIED`. Otro `--cancelar grf_…` con el GraphRun `ACTIVE` abre otra ventana | `grafo.py:601` (`ESPERA = 60`), `:650`, `:668-669` (sale al vencer, después de su última vuelta); el turno se publica dentro de `motor.ejecutar`, después de la admisión (`motor.py:218-228`) | Task 5 |
| 5 | El cancelador se corta (Ctrl-C, el proceso muere) después de escribir la marca y antes de pedirle a la Execution en vuelo | Igual que 4: la marca queda y el conductor la honra en 7a y 7f (normas (a) y (c)); sin llamada, se vio la Execution en vuelo con su propio resultado | `grafo.py:643-648` (la marca va primero), `:651-670` | Task 5 |
| 6 | Quien tiene el candado (el conductor, o quien cierra el huérfano: un `--grafo` nuevo u otro `--cancelar`) escribe el terminal entre la lectura del comando y la marca, o la marca queda entre la lectura de la regla de cierre (`grafo.py:188`) y el `result.json` (27.1 K y N; refuters A, C y G) | Un `cancelacion.json` que el terminal no refleja (`cancelRequested: false`); el terminal no cambia y es la verdad; `--grafo --estado` muestra `cancelRequested: true` | `grafo.py:628`, `:637-638`, `:643-647`; `:712` | Task 5 |
| 7 | El conductor murió con una Execution propia `RUNNING` (el motor corre en su proceso y murió con él) | Quien cierra el huérfano llama a la recuperación (norma (b)). Lo observado: la recuperación de Task 4 la cerró por su regla (T4 MD-24: `CANCELLED` con su propio pedido, `FAILED HOST_INTERRUPTED` sin él); nadie mató el árbol del Host, que puede seguir vivo y escribiendo; el GraphRun cerró `CANCELLED`. Con otro proceso que tenía en ese instante su candado de vida, la recuperación no la tocó y quedó abierta: límite 8 c) | `grafo.py:657-663`, `:323-326`; `motor.py:379-427` («nunca mata un proceso», `:382`; con el candado de vida tomado no la toca, `:392-394`); refuter I, P5 | Task 4 (R1, MD-24) |
| 8 | Una Execution propia quedó abierta después del `result.json` del GraphRun. Casos vistos, sin pretender que sean todos: (a) un Ctrl-C que sale del motor hacia el conductor, antes de la entrega o después (por ejemplo, un segundo Ctrl-C mientras el motor cierra la corrida del primero); (b) un `ErrorDelComando` del motor después de publicar; (c) al cerrar un huérfano, otro proceso tiene en ese instante el candado de vida de la Execution propia, `REQUESTED` o `RUNNING` | (a): `REQUESTED` sin motor (R2) antes de la entrega, `RUNNING` sin motor después; (b): `REQUESTED`, o `RUNNING` sin motor hasta la próxima recuperación; (c): `REQUESTED`, o `RUNNING` con pedido. El terminal del GraphRun fue `CANCELLED` (con la marca) y no cambia (norma (e)). Lo que hizo el `--grafo` siguiente, bajo la misma huella, dependió del estado: con la `REQUESTED`, se detuvo con `TASK_EXECUTION_OPEN` y el comando para cancelarla; con la `RUNNING` sin motor (b), la recuperó en su paso 3 (por T4 MD-24: `CANCELLED` con su propio pedido, `FAILED HOST_INTERRUPTED` sin él) y, al llegar a ese nodo, cerró `FAILED WORK_UNIT_NOT_SUCCEEDED`, sin comando para cancelarla porque ya no estaba abierta. Con la `RUNNING` de (a) después de la entrega y la de (c) no se observó el `--grafo` siguiente | (a) `motor.py:236-240` (el `KeyboardInterrupt` anterior a `:293` sale del motor), `grafo.py:388-394`; refuter C, O-5; refuter G, `ctrlc`: `REQUESTED` y el siguiente `TASK_EXECUTION_OPEN` con el comando. Después de la entrega: el `except KeyboardInterrupt` de `motor.py:296-299` llama a `_cerrar_sin_host`, que vuelve a tomar la foto del árbol (`:309`) sin otro `except`; refuter I, P3: modo A 2/2 y modo B 4/6, GraphRun `CANCELLED` y su Execution `RUNNING` sin motor (en los otros 2/6 el GraphRun no llegó a terminal: §16.3). (b) `motor.py:138-140`, `grafo.py:431-437`; el siguiente: `grafo.py:564` (paso 3, `motor.recuperar`), `:409-413`, `:470-479` (7c: terminal no exitoso es `WORK_UNIT_NOT_SUCCEEDED`); refuter G, F-1: `repro_limite8b` y `varios-errcmd`, 4/4 (`CANCELLED` con pedido; `HOST_INTERRUPTED` sin él). (c) con la `REQUESTED`, `motor.py:470-471`, por lectura, no reproducido; con la `RUNNING`, la recuperación no toca una Execution cuyo candado de vida tiene otro (`motor.py:392-394`) y `motor.cancelar` solo cierra una `REQUESTED` (`:469`); refuter I, P5, 2/2: GraphRun `CANCELLED` y su Execution `RUNNING` con pedido después del terminal | Task 4 (R2) y Task 5 (el cierre) |
| 9 | `motor.cancelar` recupera antes de pedir (`motor.py:444`), como cada `motor.ejecutar` (`:218`) y cada `--grafo` (paso 3 de §10) | Lo observado: una `RUNNING` huérfana de la TaskKey, propia o no, quedó `FAILED HOST_INTERRUPTED` (o `CANCELLED` con su propio pedido). Es la recuperación de Task 4, no una cancelación: el cancelador no llama a `motor.cancelar` sobre una ajena (norma (b)), y no se le escribe `cancelacion.json` (GE-E52) | `motor.py:379-406`, `:444` | Task 4 (MD-24) |

La oración que resume lo normativo está al final de la lista de §17.2.

---

## 18. Plan changes

#### GD-16. El GraphRun se detiene, y el motor recibe la huella esperada

**El plan se reescribe en el lugar** por `plan`, `--replanificar` y una decisión humana
(`decisiones.py:89-91`), y cualquier reescritura cambia F (la huella es del documento entero,
`generated_at` incluido). El invariante de MC «nadie lo cambia después de armarlo» (MC:2073) no vale
en el código (WU01 C3): el GraphRun no se apoya en que el plan sea inmutable, sino en la huella.

**La frontera:** el GraphRun **detecta**; Planning **decide** el plan nuevo. El GraphRun nunca escribe
el plan, nunca replanifica y nunca mezcla Executions de dos huellas.

| Cuándo cambia | Qué pasa |
|---|---|
| Entre dos despachos | El paso 7b lo ve: `PLAN_FINGERPRINT_CHANGED`, sin despacho |
| Entre el paso 7b y `al_pedir` | `al_pedir` arma la request con el plan nuevo, F2 (`admision.py:255-260`). Con `huella_esperada=F`, `al_entregar` la rechaza: **`REJECTED PLAN_CHANGED`, sin `entrega.json` y sin Host**. Si `al_pedir` ya la rechaza (por ejemplo `DEPENDENCY_NOT_SATISFIED`, porque bajo F2 nada está satisfecho), no hay Execution. En los dos casos el paso 7h ve la huella nueva |
| Entre la creación y la entrega | La regla de hoy: `PLAN_CHANGED` (`admision.py:261-269`) |
| Con la Execution `RUNNING` | Termina normalmente. Su resultado vale para F, y el GraphRun se detiene en el paso siguiente |
| Una lectura a medio escribir (`plan.py:588` no es atómica) | `GRAPH_PLAN_UNREADABLE`. Relanzar lo resuelve |
| Reescrito con el mismo contenido parseado | La huella no cambia (`contrato.py:131`): el GraphRun sigue |

**Sin `huella_esperada` no se puede cumplir «no mezclar».** `motor.ejecutar` no tiene hoy un
parámetro de huella (`motor.py:188`): sin el cambio, un GraphRun atado a F podría provocar una entrega
real bajo F2. Con él, el peor caso es una Execution `REJECTED` bajo F2, que ocupa un turno de una clave
que admite reintento.

**Lo previo no se reusa entre huellas** (EX-I26, T3 P12): después de replanificar, un GraphRun nuevo
sobre F2 despacha también las unidades que estaban `SUCCEEDED` bajo F. Es el costo de que la identidad
del plan sea su huella, y es una decisión de Task 3 que esta Task no reabre.

---

## 19. Flow / Normative

#### GD-17. Flow lo decide la admisión, en cada despacho

- El GraphRun no lee ni escribe el TaskFlowState, no guarda `delegationAllowed` entre nodos y no fija
  una etapa.
- Si el flujo deja de permitir delegar a mitad del GraphRun —por ejemplo, la refutación llega a
  `COMPLETION` (WU06, BC1)— el despacho siguiente sale `DELEGATION_NOT_ALLOWED` al pedir, y el GraphRun
  cierra con `ADMISSION_REJECTED`. Es correcto: el GraphRun no retiene al flujo.
- Una tarea `CANCELLED` en el flujo no cancela una Execution en curso, como hoy: la que corre termina, y
  el despacho siguiente se rechaza.
- Que el flujo no vea el avance del grafo (WU06 BC1) es de Flow Governance, no de esta Task.

#### GD-18. La compuerta normativa, igual

La compuerta corre dos veces por Execution, con las normas de **esa** unidad (`admision.py:73-82`,
`:283`). El GraphRun no la llama, no guarda en caché un «fresca» y no la evalúa por su cuenta. Un
`NORMATIVE_GATE_BLOCKED` al pedir cierra con `ADMISSION_REJECTED`; al entregar, la Execution queda
`REJECTED` y cierra con `WORK_UNIT_NOT_SUCCEEDED`.

| Cambio entre nodos | Qué lo detecta | Cierre |
|---|---|---|
| El flujo deja de delegar | Condición 6 al pedir | `ADMISSION_REJECTED` (`DELEGATION_NOT_ALLOWED`) |
| La compuerta bloquea | Condición 9 | `ADMISSION_REJECTED` o `WORK_UNIT_NOT_SUCCEEDED` (`NORMATIVE_GATE_BLOCKED`) |
| El plan cambia | Paso 7b o 7h | `PLAN_FINGERPRINT_CHANGED` |
| Un agente deja de rutear | Condición 10 | `ADMISSION_REJECTED` o `WORK_UNIT_NOT_SUCCEEDED` (`AGENT_UNAVAILABLE`) |
| Desaparece una capability | Condición 13 | Igual, con `CAPABILITY_UNAVAILABLE` |

---

## 20. Capabilities

#### GD-19. El GraphRun es ciego a capacidades

El GraphRun elige **elegibles** —estado y dependencias—; la admisión decide **admisibles**, con la
condición 13 al pedir y al entregar. Un preflight del GraphRun sobre las capacidades (WU07-rt, opción C)
duplicaría la fuente de verdad, y sin arreglar `provee` no detectaría nada (WU07-ct): ver GC-08.

**Comparación pedida por el brief:**

| | Ciego (se elige) | Capability-aware (preflight) |
|---|---|---|
| Fuente de verdad | Una: la admisión y el adaptador | Dos, o una consulta nueva al adaptador desde el GraphRun |
| Detecta R5 | Sí, con GD-21 | Solo con GD-21 |
| Costo de descubrir un nodo imposible | Una Execution `REJECTED`, sin Host ni modelo | Cero Executions |
| Efectos parciales | Corren los nodos anteriores, que son válidos y se adoptan al relanzar | Puede no correr nada |
| Elegir Host más adelante | `provee` ya es la consulta natural; nada que deshacer | Igual |

La diferencia real es una Execution `REJECTED` contra cero: no justifica una segunda fuente.

#### GD-21. R5: `provee` conoce la plataforma

**El arreglo es del Host Adapter**, como piden FH («Map `tests.run` per platform, or reject it at
admission where the Host cannot provide it. Either is a change to MD-18») y WU07 en sus dos lentes.

- `host_claude_code` declara, por plataforma, las herramientas que el Host no ofrece aunque se las
  pidan: en `win32`, `Bash`. Es un hecho observado del Host (T4 §34.2, E8, con 2.1.295; repetido con
  2.1.296), y se escribe fechado.
- `provee(capacidades, definicion)` devuelve como no provista una capability cuya herramienta el Host no
  ofrece en la plataforma, aunque el agente la tenga en su `tools:`. La plataforma se le pasa al
  adaptador (por defecto `sys.platform`), así los tests prueban las dos ramas en cualquier máquina.
- **Lo que devuelve `provee`** (enmienda del 14-10-2026, 27.1 D): la lista de las capabilities de la
  unidad que no provee, y **cada elemento empieza con el id de la capability**. Es el id solo si la
  capability no está en la tabla de MD-18 o si al agente le falta una de sus herramientas, como en
  Task 4; y es `<id> (el Host no ofrece <herramientas> en <plataforma>)` si la razón es la
  plataforma, que gana cuando se dan las dos. La admisión los junta tal cual en el `detail` del
  rechazo (`admision.py:302-305`): así el `detail` de GE-E56 nombra `Bash` y la plataforma sin que la
  admisión sepa nada de plataformas ni de herramientas. Su único consumidor es `admision.py:302`, que
  solo mira si la lista está vacía y la junta; el conductor no la llama (GM-31). Un consumidor que
  necesite ids compara cada elemento con `c` o con el prefijo `c + " ("`, para cada `c` de
  `requiredCapabilities`.
- Resultado: una unidad con `tests.run` en Windows sale **`REJECTED CAPABILITY_UNAVAILABLE` al
  entregar**, por la condición 13b (`admision.py:291-295`), **antes** de `entrega.json`: sin Host, sin
  modelo y sin `SUCCEEDED` falso. El GraphRun cierra con `WORK_UNIT_NOT_SUCCEEDED`.
- **ME-I29 no cambia:** después de la entrega el motor sigue sin emitir `CAPABILITY_UNAVAILABLE`
  (`motor.py:14-16`). El GraphRun igual trata un `FAILED` con ese código, que el contrato permite
  (`contrato.py:69`), como una unidad no exitosa (GC-09).
- **`herramientas` no cambia** (ME-E40): en Windows no llega a armar `--tools` para una unidad que
  `provee` rechazó, porque el rechazo de la 13b sale de `_correr` (`motor.py:268-276`) antes de
  `adaptador.entregar` (`:324`), que es donde se arman los argumentos (`host_claude_code.py:254-268`).

**La consecuencia, dicha:** en Windows, ninguna unidad con `tests.run` se ejecuta por el motor hasta que
exista un mapeo comprobado (GP-02). Diecisiete skills de `harnesses/desarrollo/skills/` nombran
`tests.run`. No se pierde nada que ande hoy: hoy esas unidades corren sin poder correr
tests y pueden terminar `SUCCEEDED`. **Se cambia un éxito falso por un rechazo honesto.**

**Lo que queda de R5:** `admission.capabilities` se sigue escribiendo `ALL_AVAILABLE` al pedir, cuando
la 13b todavía no corrió (`admision.py:376`): la request de una Execution que después sale `REJECTED`
por la 13b dice algo que el resultado desmiente. Es un riesgo (§30), no un error del grafo.

**Elegir Host más adelante:** lo que un Host provee depende del tipo de Host, de la plataforma y del
`tools:` del agente, no de Catalog. Elegir Host tiene que pasar antes de la condición 13b y evaluarla
contra el adaptador elegido; ni el Host ni la plataforma entran a la huella del plan ni a la clave de
idempotencia (`result.host` es observabilidad, nunca identidad, `execution-result.schema.json:106`).
Esta Task no lo construye.

**Nota de enmienda a T4 MD-18′** (enmienda del 14-10-2026, 27.1 E; es la que pide el paso 2 de §34).
T4 no se edita: es una spec cerrada. Lo que dice, en `minimal-execution-engine/spec.md:1950-1952`:

> **`Bash` en Windows:** el Host la descarta en silencio, porque su shell es PowerShell (E8). Una
> unidad con `tests.run` se admite y su agente no tiene con qué correr los tests. Queda como riesgo
> (R5): la tabla de MD-18 no cambia en esta enmienda.

| | T4 MD-18′ | Desde Task 5 |
|---|---|---|
| Una unidad con `tests.run`, en `win32` | Se admite y se entrega; el agente corre sin `Bash` y puede terminar `SUCCEEDED` | **`REJECTED CAPABILITY_UNAVAILABLE` al entregar**, por la condición 13b, sin `entrega.json`, sin Host y sin modelo |
| La misma unidad, en otra plataforma | Se admite y se entrega con `Bash` | Igual que en T4 (GE-E57) |
| `provee` (T4 MD-18, `spec.md:949-951`) | Provee si la capability está en la tabla y el `tools:` del agente tiene sus herramientas | Además, ninguna de sus herramientas está en las que el Host no ofrece en esa plataforma (`NO_OFRECIDAS`) |
| La tabla de MD-18 (`tests.run` → `Bash`), `herramientas`, `--tools` y `--allowedTools` | — | Sin cambio (ME-E40) |
| R5 | Riesgo abierto | Cerrado por rechazo, no por mapeo: el mapeo comprobado queda en GP-02 |

---

## 21. Evidence

- **La evidencia de cada Execution no cambia** (T4 MD-20). Con el GraphRun serial, dos Executions
  propias nunca corren a la par, así que `otras_entregadas` no se dispara entre ellas; y el freno de
  `TASK_EXECUTION_OPEN` evita despachar con una abierta ya observada. En la carrera residual de §15.4,
  una manual de otra unidad que se publica después del chequeo sí puede solaparse con la propia, y la
  evidencia de las dos puede quedar `CHANGES_UNATTRIBUTABLE`: la regla de Task 4, sin cambios. El
  GraphRun no atribuye cambios de una a la otra ni reescribe la evidencia de ninguna.
- **Lo que sigue degradando en serial**, de Task 4 y dicho en §30: una unidad que cambia un archivo que
  la anterior dejó sucio queda `CHANGES_UNATTRIBUTABLE` (`evidencia.py:141`), porque el motor no
  commitea.
- **La evidencia operacional del GraphRun** es lo que escribe en sus marcas y en su resultado: F, el
  conjunto de nodos, el orden, cada despacho con su `executionId` y su número, qué se adoptó, la causa
  del cierre y el turno de cada unidad al cerrar.
- **No se duplica nada:** ni `evidence.changes`, ni diffs, ni `output.md`, ni texto del agente o del
  Host. Todo eso está en la Execution, que el GraphRun referencia por `executionId`. `result.json` de una
  Execution se escribe una sola vez (`motor.py:135-146`), así que la referencia no se mueve.

---

## 22. Error model

#### GD-22. `GraphRunError`: propio, cerrado, nueve códigos

No se reutilizan los 23 de ExecutionError (GC-15): **otro dueño, otro vocabulario**. Un ExecutionError
aparece solo como **causa referenciada**, en `executionCode`. Cada código sale de un caso real de esta
spec:

| Código | Dónde | Caso real |
|---|---|---|
| `GRAPH_ALREADY_ACTIVE` | Al arrancar, sin GraphRun | Otro conductor tiene el candado de la tarea (§14.1) |
| `GRAPH_PLAN_UNREADABLE` | Al arrancar, sin GraphRun; o `FAILED` | La regla de lectura falla o el plan es de otra TaskKey; o un plan a medio escribir a mitad del GraphRun (§18) |
| `GRAPH_STRUCTURE_INVALID` | Al arrancar, sin GraphRun | Dependencia rota, ciclo, dependencia repetida o plan sin unidades (§11.1) |
| `WORK_UNIT_NOT_SUCCEEDED` | `FAILED` | Una unidad tiene su último turno bajo F en `FAILED`, `CANCELLED` o `REJECTED`: despachada por este GraphRun o encontrada así |
| `ADMISSION_REJECTED` | `FAILED` | El motor devolvió un rechazo al pedir: no hay Execution |
| `TASK_EXECUTION_OPEN` | `FAILED` | Hay en la TaskKey una Execution abierta o ilegible que este GraphRun no está corriendo |
| `PLAN_FINGERPRINT_CHANGED` | `FAILED` | La huella del plan dejó de ser F. Otro nombre que `PLAN_CHANGED`, que es de Execution y solo `REJECTED` |
| `DISPATCH_FAILED` | `FAILED` | El motor levantó un error del comando, sin ExecutionError (§16.3) |
| `GRAPH_INTERRUPTED` | `FAILED` | El conductor se cortó: lo escribe el cierre de un huérfano, o el conductor ante un `KeyboardInterrupt` |

**La forma:**

```text
error: {
  code             uno de los nueve
  workUnitId       la unidad de la causa, o null
  executionId      la Execution de la causa, o null
  executionStatus  su estado derivado, o null
  executionCode    el code de su ExecutionError o del rechazo, o null
  detail           texto del GraphRun, hasta 300 caracteres: ids, códigos y el comando que sigue.
                   Nunca texto del agente, del Host ni el detail de un ExecutionError
}
```

`CANCELLED` y `SUCCEEDED` no llevan error. Los tres rechazos al arrancar vuelven por la salida del
comando, como `{code, detail}`, y no se persisten: no hay GraphRun donde guardarlos.

**Una máquina lee solo `code`**, como en Execution (MC:1072).

---

## 23. Result

#### GD-23. `graph-run-result/1.0`

`comun/schemas/graph-run-result.schema.json`, nuevo, con `additionalProperties: false` en cada nivel:

| Campo | Qué es |
|---|---|
| `schema_version` | `graph-run-result/1.0` |
| `graphRunId` | `^grf_[0-9a-f]{32}$` |
| `taskKey` | La TaskKey |
| `planFingerprint` | F |
| `requestedBy` | Quien lo pidió, redactado |
| `startedAt`, `endedAt` | UTC, con el formato del contrato |
| `status` | `SUCCEEDED`, `FAILED` o `CANCELLED` |
| `error` | `null`, o la forma de §22 (obligatorio con `FAILED`, prohibido con los otros dos) |
| `cancelRequested` | Si existía la marca de cancelación al cerrar |
| `nodes` | Uno por unidad del conjunto congelado, en el orden de `order`: `{workUnitId, state, executionId, turn, dispatched}`. `state` es uno de los cinco de §9.2; `dispatched` dice si la Execution de ese turno la despachó este GraphRun |

**Coherencias que el schema no puede decir**, validadas en código, como hace `contrato.validar_resultado`
con las suyas:

- `SUCCEEDED` si y solo si todos los `nodes` están `SATISFIED`;
- `nodes` tiene exactamente los `workUnitId` de `inicio.json`, en su orden;
- `error.workUnitId`, si no es `null`, es uno de ellos.

No lleva `evidence`, `files`, `output` ni `artifact`.

**El schema en el modelo canónico** (enmienda del 14-10-2026, 27.1 A). Con las columnas que S4 de t64
lee en 3.2 de Task 2, en D7 de la integración y en §22 de T3 (`COLUMNAS_DE_SCHEMAS`, t64:699):

| Schema | Concepto | Productor | Runtime | Persistencia | Clase |
|---|---|---|---|---|---|
| `graph-run-result` | GraphRun | `bin/ejecucion/grafo.py`, por `registro.py`: el conductor al cerrar, y el cierre de un huérfano | `dev-harness.py ejecutar --grafo`, `--cancelar grf_…` | `.claude/ejecuciones/<KEY>/grafos/<graphRunId>/result.json` | Record |

---

## 24. CLI / API

#### GD-24. Una opción sobre `ejecutar`, sin subcomando nuevo

| Comando | Qué hace | Sale con |
|---|---|---|
| `ejecutar <KEY> --unidad <w>` | **Igual que hoy** | 0 solo si `SUCCEEDED`; 2 si no |
| `ejecutar <KEY> --grafo` | Corre un GraphRun hasta su terminal | 0 solo si `SUCCEEDED`; 2 con `FAILED`, `CANCELLED` o un rechazo al arrancar |
| `ejecutar <KEY> --grafo --estado` | Los GraphRuns de la tarea: id, estado, F, despachos con el estado derivado de cada Execution, causa. Solo lee: no recupera, no cierra, no sondea el candado. Un `ACTIVE` dice que, si su proceso murió, lo cierra el próximo `--grafo` o `--cancelar grf_…` | 0 |
| `ejecutar <KEY> --cancelar <grf_…>` | §17 | 0 |
| `ejecutar <KEY> --cancelar <exe_…>`, `--estado`, `--recuperar` | **Igual que hoy** | Igual |

- `--json` imprime el `graph-run-result/1.0`, el rechazo al arrancar, o la lista de `--estado`.
- `--pedido-por` vale para `--grafo` y `--cancelar grf_…` como hoy.
- La regla de «una sola opción» (`dev-harness.py:2250-2254`) pasa a admitir `--grafo` como modo, y
  `--grafo --estado` como la única combinación. Su mensaje de error nombra `--grafo`; el código de
  salida y la salida estándar no cambian (27.1 I).
- `--cancelar` elige por el prefijo del id. Un id que no es `exe_…` ni `grf_…` válido es un error del
  comando, como hoy.
- **Trece subcomandos**, sin cambio (ME-E47, t72:2222).
- **`--recuperar` no toca GraphRuns.** Cerrar un huérfano exige el candado de la tarea, y lo hacen
  `--grafo` y `--cancelar grf_…`.

**La API interna**, para quien construye y para los tests:

| Función | Dónde |
|---|---|
| `conducir(proyecto, clave, pedido_por, adaptador, config, catalogo, compuerta, cargar_registro, ganchos)` | `ejecucion/grafo.py` |
| `cancelar_grafo(proyecto, clave, graph_run_id, pedido_por, catalogo)` | `ejecucion/grafo.py` |
| `estado_de_grafos(proyecto, clave)` | `ejecucion/grafo.py` |
| `motor.ejecutar(..., execution_id=None, huella_esperada=None)` | `ejecucion/motor.py`; sin ellos, igual que hoy |
| `admision.al_entregar(..., huella_esperada=None)`, `admision.leer_plan` | `ejecucion/admision.py` |
| Rutas, candado de la tarea y marcas del GraphRun | `ejecucion/registro.py` |

`ganchos` son puntos de encuentro de los tests, como `antes_de_reservar` y `antes_de_entregar` del
motor: después de `inicio.json`, después de cada marca de despacho, después de cada retorno del motor
y antes del terminal. En producción no se pasan.

---

## 25. Security

- **Nada se amplía:** cada Execution del GraphRun pasa por el mismo Host Adapter, con las mismas
  banderas, `--tools` mínimo, sin `--bare` ni salteo de permisos, y los hooks del proyecto activos
  (T4 MD-08′, ME-I23).
- **Un GraphRun lanza varias sesiones del Host**, en serie, y cada una cuesta. Lo lanza una persona
  explícitamente con `--grafo`, y queda `requestedBy` en el GraphRun y en cada request. No hay
  presupuesto por corrida (MP-03 de T4 sigue).
- **Lo que persiste el GraphRun no tiene texto ajeno:** ids, códigos, fechas y `requestedBy` redactado
  con el catálogo de secretos, como `cancelacion.json` de Execution (`motor.py:452`). Sin catálogo, el
  GraphRun no arranca: es un error del comando, como en el motor (`motor.py:205-207`).
- **Los ids se validan con `fullmatch` antes de volverse rutas** (`grf_…`, `exe_…`, TaskKey), como T4
  MD-15.
- **R5 mejora la seguridad de la evidencia:** un `SUCCEEDED` ya no puede esconder que los tests no
  corrieron.
- **R4 sigue:** `ejecutar`, también con `--grafo`, cae en `UNRESOLVED_TOOL_CLASS` desde una sesión
  interactiva (`docs/versiones/0.32.0.md:147-149`). La fila es del `harness-hook-engineer`. Un agente
  que pudiera lanzar un grafo lanzaría N sesiones: la fila tiene que tenerlo en cuenta (GP-06).

---

## 26. LangGraph

Evaluado **después** de fijar el modelo, sin instalar nada. **La pregunta: ¿implementa naturalmente
nuestras invariantes?** No.

| Aspecto | Lo que pide este modelo | LangGraph (según su diseño público; no instalado ni probado) | ¿Calza? |
|---|---|---|---|
| Modelo de estado | Derivado de marcas de una sola escritura y del registro de Execution | Un estado mutable del grafo, que los nodos actualizan con reducers | No: es el `state.json` que GD-12 evita |
| Scheduling | Serial, topológico, determinista, fail-fast | Pasos por «supersteps»; nodos del mismo paso corren en paralelo | Se puede forzar, contra su diseño |
| Reintentos | Ninguno automático (GD-09, EX-E50) | Políticas de reintento por nodo | Habría que apagarlas; su presencia choca con EX-E50 |
| Checkpoints | Ninguno: nada se reanuda (ADR-0015 §4) | Checkpointers para reanudar un hilo desde el último paso | Es lo contrario de GD-10 |
| Persistencia | `os.link`, archivos bajo `.claude/ejecuciones/` | Checkpointers en memoria, SQLite o servicios | Un segundo almacenamiento, mutable |
| Interrupts | La cancelación es una marca persistida y la cumple el motor | `interrupt` para pedir intervención humana y reanudar | Otra semántica: reanudar |
| Integración con subprocesos | El Host lo lanza solo `host_claude_code.py` | Nodos que llaman código Python; no aporta nada al Host | Neutro |
| Windows | Corre en Windows con PowerShell | Python puro; no comprobado aquí | Desconocido |
| Locking | Candado del SO por tarea y por Execution | No tiene exclusión entre procesos para nuestro registro | No |
| Ejecución determinista | Misma secuencia con el mismo registro | Determinista por paso; la concurrencia dentro del paso no | Parcial |
| Guardas | ME-E47 prohíbe importar `langgraph` en `bin/` y `comun/` (t72:2197, :2218-2220) | — | Romperla pide un ADR |

**Conclusión: no usar.** El conductor es un bucle de unas decenas de líneas sobre primitivas que ya
existen; LangGraph traería estado mutable, reanudación y reintentos que este modelo prohíbe, y una
dependencia externa (ADR-0008). No hace falta evaluarlo en construcción.

---

## 27. Migration

#### GD-25. Task 4 → Task 5: aditiva, sin cambio de contrato

**Lo que no cambia** (GE-I02): `contrato.py`; `execution-request.schema.json` y
`execution-result.schema.json`; los 23 códigos, `PRECEDENCIA`, `ESTADOS`, `TRANSICIONES`; la clave de
idempotencia; los turnos; `escribir_una_vez`; `Vida`; la regla de quince condiciones;
`ejecutar --unidad`, `--cancelar exe_…`, `--estado` y `--recuperar`, con sus salidas; ADR-0013,
ADR-0014 y ADR-0015.

**Lo que cambia en código de Task 4:**

| Archivo | Cambio | Compatibilidad |
|---|---|---|
| `bin/ejecucion/registro.py` | F1 y F2′ (GD-20); rutas, candado de la tarea y marcas del GraphRun | Una sonda menos; los temporales nuevos esperan al umbral. Enmienda T4 §14.1 p.5 |
| `bin/ejecucion/host_claude_code.py` | Herramientas no ofrecidas por plataforma; `provee` las mira (GD-21) | En Windows, `tests.run` pasa de admitida a `REJECTED`. Enmienda T4 MD-18′ (`spec.md:1950-1952`), con su nota en GD-21 |
| `bin/ejecucion/admision.py` | `leer_plan` público; `huella_esperada` en `al_entregar` | Sin el parámetro, igual que hoy |
| `bin/ejecucion/motor.py` | `execution_id` y `huella_esperada`, opcionales, hasta la admisión | Sin ellos, igual que hoy |
| `bin/dev-harness.py` | `--grafo`, `--grafo --estado`, `--cancelar grf_…` | Trece subcomandos; las opciones de hoy no cambian |

**Lo nuevo:** `bin/ejecucion/grafo.py`; `comun/schemas/graph-run-result.schema.json`;
`tests/casos/73_ejecucion_de_grafo.py`; `tests/casos/73-ejecucion-de-grafo-instalador.ps1`; ADR-0016.

**Tests de tareas anteriores que cambian, cada uno con su comentario:**

| Test | Hoy | Después | Por qué |
|---|---|---|---|
| `63-harness-unico-instalador.ps1` E-15 | 292 rutas en el lock (`:421`) | 294: suma `ejecucion/grafo.py` y `schemas/graph-run-result.schema.json`, en una lista `$huAgregadosPorEjecucionDeGrafo` como las dos de Task 3 y Task 4 (`:398-413`) | Los archivos nuevos se instalan a propósito |
| `63-harness-unico-instalador.ps1` E-16 | Saltea los agregados de Task 3 y Task 4 | Saltea también los dos de esta Task | Igual |
| t64 E-09 | «Lo que todavía no existe» nombra `ejecutor`, `scheduler`, `reintento`, `estado de corrida persistido` (t64:1077-1079) | Sin cambio en el test: MC conserva esos anclajes con texto verdadero (§28) | Lo que sigue sin existir es el ejecutor paralelo, el scheduler concurrente, el reintento automático y un estado de corrida fuera de Execution |
| t72 ME-E47, ME-E46; `65` EX-E50 | — | Sin cambio: `grafo.py` las cumple (GE-E64) | — |
| t72, escenarios de `limpiar_temporales` | — | Si alguno espera el borrado inmediato de un temporal con candado libre, su temporal se envejece con `os.utime`, con un comentario que nombra GD-20 | F2′ |
| t64 E-05 (enmienda del 14-10-2026, 27.1 A) | Cuenta 54 schemas en `comun/schemas/`, 46 + 6 + 2 (t64:658-680); cada uno figura en «Persistencia y contrato» de algún concepto (t64:686-690) | 55: suma una tupla de un schema, `graph-run-result.schema.json`, a la cuenta y a la verificación de presencia, como `SCHEMAS_DE_EJECUCION` (t64:664, :684-685). La de «Persistencia y contrato» no cambia: la cumple la ficha de GraphRun. Comentario `Task 5 / GD-23` | El schema nuevo entra a propósito (GD-23) |
| t64 E-05 (S4) (ídem) | Las tablas de 3.2, de D7 y de §22 de T3 tienen exactamente los schemas en disco (t64:787-792), y cada concepto que nombran lo nombra en su «Persistencia y contrato» (t64:796-801) | Lee además la tabla de schemas de GD-23 de esta spec, buscada por sus columnas como la de §22 de T3 (t64:702-704, :780-786), y la suma a las otras; ningún schema de esa tabla está en las otras. Comentario `Task 5 / GD-23` | Igual |
| `65_contrato_de_ejecucion.py` EX-E45 (ídem) | `son 54 schemas` (t65:1167) | 55. Lo demás sin cambio. Comentario `Task 5 / GD-23` | Igual |
| t72 ME-E48 (enmienda del 14-10-2026, 27.1 F) | `CONCEPTOS = 83` (t72:2253), que compara contra la cantidad de `###` de `## Conceptos` de MC (t72:2273) | `CONCEPTOS = 85`, con un comentario `Task 5 / GD-23` que dice que suman `GraphRun` y `GraphRunError` (§28). Nada más de t72: ni el rótulo de la aserción ni el resto de ME-E48 | Los dos conceptos nuevos entran a propósito (§28, GD-23). Es la única aserción de la suite que fija la cantidad de conceptos |
| Sin adaptación, por el schema nuevo | — | t64 E-01 a E-04 y E-07 rigen sobre la ficha de GraphRun: fila del catálogo y `### GraphRun` (t64:479-482), los diez campos sin vacíos (:494-498), Contexto `Execution` y una de las doce clasificaciones, iguales en la fila y en el bloque (:617, :639). `33_bases_de_datos.py` E-36 pasa cada schema de `comun/schemas/` por `controlar_soporte` (t33:1872-1874): el schema nuevo usa solo palabras clave que ese validador soporta | — |

**Datos:** ningún registro existente se migra. Las Executions de Task 4 se adoptan por la regla de
§9.2. `.claude/ejecuciones/<KEY>/grafos/` aparece recién con el primer `--grafo`.

**Pendientes que salen de FH al cerrar**, a la nota de versión: «The lock probe can land between
`O_EXCL` and the lock of `Vida`» (N1), «`Bash` does not exist in the Host session on Windows» (R5), y
la mitad «`--cancelar` racing a recovery» del ítem «Three engine paths end in a traceback».

### 27.1 Enmiendas posteriores a la aprobación (14-10-2026 y 15-10-2026)

La spec se aprobó el 13-10-2026 con la huella del encabezado, y se enmendó después en diez pasadas,
con los puntos A a R. Al construir las etapas 1 a 5a,
`harness-builder` encontró cinco puntos que la spec no fijaba bien o que omitía. Nahuel Palacio, que
encargó la Task, autorizó el 14-10-2026: **(1)** las adaptaciones de t64 E-05 y S4 y de t65 EX-E45, su
registro acá, y adelantar a la etapa 6 la ficha de `GraphRun` en MC; **(2)** una pasada del arquitecto,
antes de la etapa de mutaciones, por los otros cuatro. Decidió `harness-task-architect`, leyendo el
árbol de trabajo sobre `e33b41b`. Esos son los puntos A a E.

El mismo día, al construir las etapas 5b, 6A y 6B, el builder encontró cuatro puntos más, F a I, y se
registran en una segunda pasada. **F** lo autorizó Nahuel Palacio, en esa sesión, respondiendo una
pregunta del coordinador. **G, H e I** los decidió `harness-task-architect`, leyendo el árbol de
trabajo; la pasada se hizo con el coordinador a pedido del usuario, que quiere cerrar la construcción lo
antes posible.

El 15-10-2026, la verificación independiente (cuatro invocaciones de `harness-spec-refuter`, ninguna del
builder) dio un `contradicho`: la segunda oración de GE-E48. Se registra en una tercera pasada, con los
puntos J y K. **J** lo decidió Nahuel Palacio, en esa sesión: se enmienda la spec, no el código ni Task 3
o Task 4. **K** lo decidió `harness-task-architect`, dentro de esa misma pasada, que la decisión del
usuario nombra («incluye lo que A y C anotaron»). La tercera pasada precisa los pasos 1 y 3 de GD-11 sin
cambiar lo que decide.

El mismo 15-10-2026, una re-verificación independiente de J (refuter E, que no construyó) sostuvo GE-E48
a) y c), GE-E50, GE-I14 y GE-I18, pero dio `contradicho` a GE-E48 b) y a la garantía 2 de §17.2: J
todavía prometía más de lo que el motor de Task 4 cumple. Se registra en una cuarta pasada, con el punto
**L**, que aplica al dato nuevo la decisión de Nahuel Palacio que rige J: la spec dice solo lo que se
puede garantizar con el código y Task 3/4 como están. No hubo dos opciones igual de válidas: lo que el
motor garantiza es un hecho del código, no una elección. L precisa el paso 3 de GD-11 sin cambiar lo que
decide.

El mismo 15-10-2026, otra re-verificación independiente (refuter F, que no construyó) dio
`contradicho` a una tercera promesa distinta de §17: la ventana de 60 s del cancelador. Como corregir de
a una promesa no convergía (C, E y F encontraron una cada uno), la quinta pasada, con el punto **M**,
aplica la misma decisión de Nahuel Palacio a toda la sección 17: auditó oración por oración GD-11,
§17.1 a §17.3, GE-E46 a GE-E52, GM-21 a GM-25, GE-I14, GE-I18, GC-11, GC-22 a GC-24 y las filas de
§30.1, dejó cada afirmación con su condición, y suma §17.4 con la lista completa de límites. No hubo dos
opciones igual de válidas: cada límite es un hecho del código, y describirlo es la única enmienda que
no toca código. M precisa GD-11 pasos 3 y 4 sin cambiar lo que decide.

El mismo 15-10-2026, la verificación independiente exhaustiva de M (refuter G, que no construyó, unas
250 corridas contra la CLI de producción) sostuvo GE-E46 a GE-E52, GE-I14 y GE-I18, sin defectos de
código nuevos, pero encontró dos afirmaciones de §17.4 que el comportamiento real desmiente (F-1: el
`--grafo` siguiente al límite 8 b) recupera la `RUNNING` y no se detiene con `TASK_EXECUTION_OPEN`;
F-2: con un Host cortado, el motor sí vuelve a mirar el pedido) y cuatro imprecisiones (O-1 a O-4). La
sexta pasada, con el punto **N**, aplica la misma decisión de Nahuel Palacio a esas frases y a las que
las repiten, y contrasta cada celda «Resultado» de §17.3, §17.4 y §30.1 con la tabla de probes de G.
No hubo dos opciones igual de válidas: las dos frases son hechos del código. N no cambia lo que decide
GD-11.

El mismo 15-10-2026, la verificación independiente final (refuter H, que no construyó) encontró otro
camino del motor que la spec no listaba: un Ctrl-C sobre el motor después de que el Host salió también
relee el pedido (`motor.py:296-297`). Las verificaciones E, F, G y H habían encontrado, cada una, una
afirmación falsa del mismo tipo: la spec enumeraba los caminos internos del motor de Task 4 con
cuantificadores universales, y cada refuter halló el que faltaba. La séptima pasada, con el punto **O**,
ataca la causa: aplica la misma decisión de Nahuel Palacio a la raíz del patrón, y la spec deja de
afirmar universales sobre las entrañas de Task 4. Lo que es de Task 5 queda absoluto; lo que hace el
motor de Task 4 con un pedido o con la salida del Host queda condicionado y con sus casos observados
como ejemplos, no como lista exhaustiva. No hubo dos opciones igual de válidas: la alternativa, seguir
catalogando caminos, es la que no convergía en cuatro pasadas, y la otra, cambiar el código, la
descartó el usuario. O no cambia lo que decide GD-11.

El mismo 15-10-2026, la verificación independiente (refuter I, que no construyó) sostuvo el código y lo
de Task 5, pero encontró cuatro frases más del mismo tipo (F-1 a F-4): cada refuter, con un caso más
extremo, desmentía otra celda de resultado de §17.3 o §17.4, u otra garantía de §17.2. Nahuel Palacio,
que encargó la Task, eligió entre cuatro opciones el arreglo estructural, y la octava pasada, con el
punto **P**, lo aplica: lo normativo de la cancelación son solo acciones del código de Task 5 (la marca,
el candado y el sondeo, 7a y 7f, 7h y la regla de cierre por nodo, la escritura única, el cruce), listadas
en §17.2; las garantías 2 a 4, la tabla de §17.3 y la de §17.4 pasan a observaciones, explícitamente no
normativas. No hubo dos opciones igual de válidas: el usuario eligió el arreglo, y el criterio (una
afirmación es normativa solo si describe una acción de Task 5 que se cumple siempre) decide cada frase.
§17.3 y §17.4 conservan su número para que las referencias «§17.4, límite n» de §16, §30.1, GP-08, GC-24
y GE-E48 sigan apuntando al mismo lugar. P no cambia lo que decide GD-11.

El mismo 15-10-2026, la verificación independiente final (refuter J, que no construyó) sostuvo la
separación de P y encontró falsas tres afirmaciones que esa pasada había escrito (F-J1 a F-J3) y dos
observaciones con la condición incompleta (O-2). La novena pasada, con el punto **Q**, es la
continuación de P en su forma mínima: solo borra o suaviza; no escribe afirmaciones nuevas. Q no cambia
lo que decide GD-11.

El mismo 15-10-2026, el informe de la novena pasada marcó una frase más del mismo tipo, en la norma (b)
de §17.2, que Q no tocó porque su encargo no rehacía (a) a (f). La décima pasada, con el punto **R**, la
borra con el mismo criterio de Q: solo borrar. R no cambia lo que decide GD-11.

En ninguna de las diez pasadas cambia lo que decide una GD, un GC ni un invariante GE-I; las cuentas
siguen: 29 GD, 24 GC, 31 GE-I, 71 GE-E, 45 GM.

| Punto | Lo que decía la spec aprobada | Lo que dice ahora | Evidencia | Lo pidió | Lo autorizó |
|---|---|---|---|---|---|
| A. Schemas en t64, t65 y MC | §27 no listaba t64 E-05, S4 ni t65 EX-E45; la ficha de `GraphRun` iba al paso 12, después del schema (paso 8) | §27 suma esas tres adaptaciones y lo que rige sin adaptar; GD-23 suma la tabla de schemas que lee S4; la ficha de `GraphRun` va en el paso 8, con el schema; el resto de §28 en el 12 (§27, GD-23, §28, §34) | t64:677-680, :689-690, :787-792, :796-801; t65:1167, :1171-1172; t64:479-498, :617, :639; hoy hay 55 archivos en `comun/schemas/` | `harness-builder`, etapa 5a | Nahuel Palacio, 14-10-2026, decisión (1) |
| B. GM-11 | «`huella_esperada` se compara contra el plan actual en vez de contra la request», rojo en GE-E24 | La mutación va en 7g: el conductor relee el plan al llamar al motor y pasa esa huella en vez de F. Es la misma propiedad (la referencia es F, no el plan de hoy) en el único lugar donde es observable. Sigue siendo GM-11, ligada a GE-E24, que ahora dice que corre las dos variantes del gancho (§32, §33) | Equivalencia de la anterior: `admision.py:268` encierra `:273-276`, así que la huella del plan de hoy y la de la request son iguales donde se compara (el builder lo vio: `-k 73` 170/170 con la mutación). Lo que distingue a la nueva: el gancho `despues_del_despacho` (`grafo.py:333`) corre después de 7b (`:309-316`) y antes de 7g (`:337-339`); con el flujo reconciliado, la relectura da la huella nueva, que es la de la request, `al_entregar` admite y el Host recibe C, que el test de GE-E24 prohíbe (t73:1008-1019) | `harness-builder`, etapa 3 | Nahuel Palacio, 14-10-2026, decisión (2) |
| C. Bitácora del Host falso | «una bitácora con una línea por invocación, con inicio y fin» (§34, paso 6) | Una entrada por invocación, escrita al empezar con `fin: null` y completada al terminar con otra línea del mismo `id`; manda la última de cada `id` (§32, §34) | Con una sola línea al final, un Host muerto desde afuera no deja rastro, y GE-E40 y GE-E47 cuentan las invocaciones de un Host así. `host_falso.py:71-74` escribe al empezar, y `:139`, `:146` y `:159` completan antes de morir por `senal`, de contestar sin JSON o de contestar; el lector toma la última (t73:1924-1934); el Host matado queda con `fin: null` (t73:2012-2028) | `harness-builder`, etapa 4 | Nahuel Palacio, 14-10-2026, decisión (2) |
| D. El `detail` de R5 | GE-E56: el `detail` nombra `Bash` y la plataforma; GD-21 no decía de dónde salía | Se acepta el contrato que construyó el builder: cada elemento de `provee` empieza con el id, y en la rama de plataforma lleva la explicación entre paréntesis. La admisión no cambia (GD-21). GE-E56 no cambia | El único consumidor es `admision.py:302-305`, que solo pregunta si la lista está vacía y la junta en el `detail`; `grafo.py` no llama a `provee` (GM-31); la t72 solo lo pisa con un falso que devuelve `[]` (t72:1176-1181). La alternativa, que la admisión arme el texto, obliga a la admisión a conocer la tabla de plataformas de un adaptador concreto, cuando GD-21 pone ese conocimiento en el Host Adapter (`host_claude_code.py:55-61`, `:210-230`) | `harness-builder`, etapa 2 | Nahuel Palacio, 14-10-2026, decisión (2) |
| E. Nota de enmienda a T4 MD-18′ | El paso 2 de §34 la pedía y no estaba escrita | Escrita al final de GD-21, citando T4 `spec.md:1950-1952` y `:949-951`: en `win32`, `tests.run` pasa de admitida a `REJECTED CAPABILITY_UNAVAILABLE` | `minimal-execution-engine/spec.md:1950-1952`, `:949-951`; `host_claude_code.py:61` | `harness-builder`, etapa 2 | Nahuel Palacio, 14-10-2026, decisión (2) |
| F. Cantidad de conceptos en t72 ME-E48 | §27 decía «t72 ME-E47, ME-E46… sin cambio» y no nombraba ME-E48; §28 manda sumar `GraphRun` y `GraphRunError` a MC | §27 suma la fila de t72 ME-E48: `CONCEPTOS = 83` pasa a `85`, con el comentario `Task 5 / GD-23`, y nada más de t72 | t72:2253 fija 83 y t72:2273 lo compara con `len(m["campos"])`, los `###` de `## Conceptos` (t64:435-447). Hoy MC tiene 85 (`### GraphRun` en `:1129`, `### GraphRunError` en `:1171`; el último concepto, `### HostTool`, en `:1770`, antes de `## Mapa de contextos` en `:1786`). Ningún otro test fija la cantidad: `CONCEPTOS` aparece solo en t72; t64 E-01 compara catálogo y bloques sin un número; t65 EX-E44 cuenta los ocho de T3 | `harness-builder`, etapa 6B | Nahuel Palacio, 14-10-2026, decisión en esta sesión |
| G. Un GraphRun `ILEGIBLE` | Nada: GD-04, §16.1 y §17 no trataban un GraphRun que existe y no se lee | Se confirma lo que construyó el builder y se escribe en GD-04 (§9), §16.1 y §17.3: no se cierra, no se reabre, no se le escribe una marca; el conductor sigue de largo, así que no bloquea a otro GraphRun; `--grafo --estado` lo muestra con su motivo; `--cancelar grf_…` es un error del comando. GE-E70 suma el caso | `registro.py:873-876`, `:886-898`, `:903-907`; `grafo.py:321-322`, `:331-340`, `:564`, `:632-633`, `:686-716`; t73:5063-5104. La alternativa, que un `ILEGIBLE` frene la tarea, no es igual de válida: pide un código que GD-22 no tiene (nueve, cerrados), y cerrarlo es imposible sin F ni nodos, o rompe la escritura de una sola vez (GD-12) | `harness-builder`, etapa 5b | Decidido por `harness-task-architect`; la pasada se hizo con el coordinador a pedido del usuario, que quiere cerrar la construcción lo antes posible |
| H. Dos frases de MC fuera de §28 | §28 no tocaba la introducción de MC ni la apertura de «El límite de la ejecución» | §28 suma dos filas, con el texto exacto: las dos frases nombran `--unidad` y el GraphRun. Ningún anclaje de test cambia | Con `--grafo`, «una WorkUnit por invocación de `ejecutar`» (MC:13) y «Elegir la siguiente… es de quien invoca, y de Task 5» (MC:2063-2065) dejan de ser verdad, y la segunda contradice MC:2134 («el GraphRun elige la siguiente»). Ningún test las lee: E-09, EX-E47 y ME-E48 leen solo los apartados `###` del límite (t64:1134-1158, t65:1202-1212, t72:2274-2280), y `_apartados` descarta lo anterior al primer `###` (t64:379-387); la introducción queda antes de `## Conceptos`, y los tests que leen MC entero buscan otras frases (t65:1135, t71:537-544) | `harness-builder`, etapa 6B | Ídem G |
| I. El mensaje de «una sola opción» y el evento de `--grafo` | GD-24: la regla «pasa a admitir `--grafo` como modo»; las opciones de hoy, «igual que hoy» | Nota de implementación; no cambia el comportamiento. El mensaje nombra `--grafo` («…--estado, --recuperar o --grafo (y --grafo --estado, juntas).»); el código de salida (2) y la salida estándar (vacía) son los de 0.32.0. Sin catálogo de secretos, `--grafo` imprime `grafo.pedido` antes del error, como `--unidad` imprime `ejecucion.pedida`. GD-24 suma la frase del mensaje | 0.32.0: «ejecutar necesita una sola de --unidad, --cancelar, --estado o --recuperar.» (`e33b41b:…/dev-harness.py:2252-2253`); hoy `dev-harness.py:2361-2365`. Lo que GD-25 y GE-E63 congelan son las salidas de `--unidad`, `--estado`, `--recuperar` y `--cancelar exe_…`, no las del error de uso. Un mensaje sin `--grafo` le escondería un modo válido a quien se equivocó. El evento: `dev-harness.py:1117` y `:1276`. Los dos los fija GE-E63 (t73:5838-5844, :5936-5945) | `harness-builder`, etapa 6A | Ídem G |
| J. GE-E48, §17.2 y el sondeo de GD-11 | §17.2: «Lo peor que queda… deja al Host arrancar y morir en el primer tramo»; GE-E48, segunda oración: con el conductor detenido entre 7f y 7g, «B queda `CANCELLED` sin `entrega.json`, o con el Host terminado» | (La garantía 2 y b) de este texto las corrige L.) §17.2 dice lo que se garantiza y nada más: con la marca vista, cero Executions; si no, el cancelador cancela la propia en la vuelta en que la encuentra abierta; si el Host termina antes de esa vuelta, la Execution queda con su resultado y el GraphRun cierra por GD-05 (el último nodo `SUCCEEDED` da `SUCCEEDED` con `cancelRequested: true`, como GE-E49 y GC-23); nunca una propia abierta después del `result.json`. GD-11 paso 3 dice que es un sondeo. §17.3 suma el caso. GE-E48 pasa a tres cláusulas: a) y b) las de antes, b) con un Host que sobrevive a la primera vuelta; c) nueva, con un Host inmediato y un intervalo mayor que lo que tardan B y el terminal. §30.1 suma el riesgo; §33 liga GM-23 también a GE-E48 c). Sin escenario ni mutación nuevos | Refuter C, F-1: con la CLI real, B `SUCCEEDED` y GraphRun `SUCCEEDED` con `cancelRequested: true` en 4 de 10 (plan A→B) y B `SUCCEEDED` en 1 de 5 (A→B→C). Causa: `INTERVALO = 1.0` (`grafo.py:601-602`), sin `intervalo` en `dev-harness.py:1176`; el cancelador solo propaga en cada vuelta (`grafo.py:651-670`, `:270-279`); el motor mira solo el `cancelacion.json` de la Execution (`motor.py:258-259`, `:263`, `:282`) y, si el proceso terminó, gana su código (`proceso.py:58`, `:63-72`); `cerrar_grafo` da `SUCCEEDED` con todo satisfecho, haya marca o no (`grafo.py:188-190`, `:203`). El test daba verde con `intervalo=0.2` (t73:363) y un Host de 60 s (t73:4770) | La verificación independiente (refuter C) | Nahuel Palacio, 15-10-2026, decisión en esta sesión |
| K. La marca después de un terminal | GD-11 paso 1 y GE-E50: «Si ya es terminal, lo informa y no escribe nada»; §17.3 no tenía el cruce | GD-11 paso 1 y GE-E50: «ya es terminal **cuando el comando lo lee**». La lectura y la marca no son atómicas: si el conductor escribe el terminal entre las dos, queda un `cancelacion.json` posterior al `result.json`. Residuo aceptado, en §17.3 y §30.1: el terminal es la verdad y no cambia; la marca es inerte; el comando sale con 0 con `marcaNueva: true` y el terminal en `despues`; `--grafo --estado` muestra `cancelRequested: true`, porque ese campo dice si la marca existe hoy. No hay otra opción igual de válida sin cambiar código: tomar el candado antes de marcar rompe la marca contra un conductor vivo, y que `--estado` lea el `cancelRequested` del terminal cambia `grafo.py` | `grafo.py:628`, `:637-638` (lee y decide) y `:643-647` (marca después, sin candado); `registro.py:801-810`, `:750-755` (`marcar_cancelacion` solo pide `inicio.json`); `cerrar_huerfano` no toca un GraphRun que no está `ACTIVE` (`grafo.py:320-322`); `--grafo --estado` toma `cancelRequested` de la marca (`grafo.py:712`, `registro.py:881`, `:846-849`), y el terminal, de la marca al cerrar (`grafo.py:188`, `:203`). Refuter A, `probe_toctou.py`: terminal `SUCCEEDED` con `cancelRequested: false` y hash estable. Refuter C, O-1: 7 de 12 contra un huérfano, un solo `result.json` | Los refuters A y C | Decidido por `harness-task-architect`, dentro de la pasada que el usuario autorizó para incluirlo (la decisión de la sesión lo nombra: «incluye lo que A y C anotaron») |
| L. GE-E48 b), §17.2 garantías 2 y 3, y el pedido que pierde contra el Host | J, garantía 2: «el cancelador, en la vuelta en que la encuentra abierta… le pide cancelar, y esa Execution queda `CANCELLED`»; GE-E48 b): «un Host de B que sobrevive a la primera vuelta del cancelador que la encuentra abierta: B queda `CANCELLED`»; §17.3, fila `RUNNING`: el motor «mata el árbol del Host y escribe `CANCELLED`»; GD-11 paso 3, la fila de J en §17.3 y la de §30.1 solo cubrían la Execution que se abre y termina entre dos vueltas | §17.2 garantía 2: lo único que se garantiza es el pedido persistido en la Execution propia; termina `CANCELLED` si el motor lo revisa antes de que el Host salga (antes de entregar, dos veces, o al comienzo de cada tramo), y en particular si el Host sigue vivo un tramo entero después del pedido. Garantía 3: si el Host sale antes de esa revisión, queda con su resultado aunque su `cancelacion.json` exista; con el pedido y la salida en el mismo tramo no hay orden garantizado y los dos resultados son válidos. Las garantías 1 y 4 no cambian. GD-11 paso 3, las filas `REQUESTED`, `RUNNING` y la de J en §17.3 dicen lo mismo. GE-E48 b): un Host que sobrevive a varios tramos (60 s) da `CANCELLED`; GE-E48 suma que el rango intermedio no tiene resultado único y no se asevera; a) y c) no cambian. §30.1: el riesgo de J nombra el pedido que pierde dentro del tramo y su origen en `proceso.esperar`, y una fila nueva, el choque con T4 ME-I22; GP-08 lo suma. §33 no cambia: GM-21 y GM-22 siguen rompiendo a) y b), y GM-23, c). Sin escenario, mutación, invariante, decisión ni conflicto nuevos | `proceso.py:63-66` (el pedido se mira solo antes de cada tramo) y `:72` (`TERMINO` apenas el Host sale; nadie vuelve a mirar el pedido); `proceso.py` sin cambios desde `e33b41b` (`git diff --stat e33b41b -- …/proceso.py` vacío); `motor.py:263`, `:282` (las dos revisiones antes de entregar), `:327-337` (después de entregar, `CANCELLED` sale de `CANCELADO` o de una interrupción con pedido; con `TERMINO` y sin falla `HOST_INTERRUPTED` nadie mira el pedido); `motor.py:469-478` (`REQUESTED` sin motor); `grafo.py:651-670` (el cancelador solo pide). Refuter E, F-1: con un Host que sobrevive a la vuelta y sale enseguida, abc 5 de 5 y ab 3 de 5 B `SUCCEEDED` (ab: GraphRun `SUCCEEDED`), y con `dormir: 0.5` y la CLI de producción 9 de 10 B `SUCCEEDED` con `cancelacion.json` propio; con `dormir: 1.3`, 0 de 8; con 60 s, `CANCELLED` 2 de 2. Refuter E, F-2: la enmienda J quedó incoherente entre §17.2, §17.3, §30.1 y GE-E48; O-1: el choque con ME-I22 (`minimal-execution-engine/spec.md:1250`) | La re-verificación independiente (refuter E) | Nahuel Palacio, 15-10-2026, la decisión de la sesión de resolver GE-E48 enmendando la spec con lo que de verdad se puede garantizar, que esta pasada aplica al dato nuevo |
| M. Auditoría completa de §17 y la ventana de 60 s | GD-11 paso 4 y §17.2 (párrafo final): «Si a los 60 s el conductor sigue, lo dice: el pedido quedó persistido y el conductor lo va a cumplir», sin decir qué cumple; «el caso 3 lo alcanza un Host cuya duración no pasa de un intervalo del cancelador más un tramo», como si fuera el único camino; §17.2, garantía 2, sin la condición de que una vuelta encuentre abierta a la Execution; garantía 3, «pasa en dos casos»; garantía 4, «en ningún caso»; §17.3 sin fila para la ventana vencida, el cancelador cortado ni el conductor muerto con `RUNNING`, y «Dos veces: la segunda no escribe nada nuevo»; GD-11 paso 3, «cierra el huérfano como §16.1, que propaga la cancelación»; GC-11 sin `CANCELLED`; GE-E48 b) sin la condición de la ventana, y su rango intermedio sin los otros límites | GD-11 paso 3: el sondeo tiene ventana, y la Execution cuyo turno aparece después de la última vuelta no recibe pedido; el huérfano con `RUNNING` lo cierra la recuperación. Paso 4: `canceladas` son pedidos; la línea de la CLI, tal cual, y lo que significa exactamente: no se despacha nada más y se cierra por la regla de cierre, no que la Execution en vuelo se cancele. GD-11, el párrafo de `--cancelar exe_…`, con sus condiciones. §17.1: el conductor no mira la marca mientras el motor corre; después de la marca no hay despacho nuevo, y a lo sumo una Execution sigue. §17.2: el cancelador le pide solo a una con turno y dentro de la ventana; garantía 2 con su condición; garantía 3 con cinco casos; garantía 4 con tres excepciones; el párrafo final, con los límites 1 y 4 en producción y de quién es cada uno. §17.3: las filas `REQUESTED` y `RUNNING` con su condición, la fila de J con el pedido tardío, tres filas nuevas (ventana vencida, cancelador cortado, conductor muerto con `RUNNING`) y «Dos veces» corregida. §17.4 nueva, nueve límites con condición, resultado, origen y quién lo hereda, y la oración final. GE-E48 b): el conductor se suelta apenas existe la marca; el rango intermedio no asevera los otros límites. GC-11 y GC-24 precisados. §30.1: seis filas nuevas y dos con su límite. GP-08 suma el límite 4 como dato. Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | `grafo.py:601-602`, `:643-648`, `:650-673` (la ventana, la salida al vencer después de la última vuelta, `sigue`); `registro.py:910-920` (propia es con turno); `grafo.py:398-399`, `:425-426` (7a y 7f, lo único que mira la marca); `grafo.py:176-211` (regla de cierre), `:323-326`, `:657-663` (huérfano); `motor.py:218-240` (el turno se publica después de la admisión; un `KeyboardInterrupt` antes de la entrega sale del motor), `:319-361` (después de `entregar`), `:379-427` (recuperar no mata), `:437-483` (`cancelar` recupera primero; `:470-471`, el candado de vida); `proceso.py:55-77`; `dev-harness.py:1172-1193` (lo que imprime). Refuter F, F-1: con la CLI de producción y el conductor retenido entre 7f y el turno de B más de 60 s, el cancelador sale 0 a los 60,5 s con «su conductor sigue…»; B corre entera (20,0 s y 5 s) y queda `SUCCEEDED` sin `cancelacion.json` propio; GraphRun `SUCCEEDED` con `cancelRequested: true` en A→B y `CANCELLED` en 7a en A→B→C. Refuter C, O-5: Ctrl-C antes de entregar deja la `REQUESTED` | La re-verificación independiente (refuter F) | Nahuel Palacio, 15-10-2026, la decisión de la sesión (enmendar la spec con lo que de verdad se puede garantizar), aplicada a toda la sección 17 para que deje de dar un hallazgo por pasada |
| N. Dos frases de §17.4 que los probes desmienten, y cuatro precisiones | §17.4 límite 8 y su fila de §30.1: con la Execution abierta después del terminal, «el GraphRun siguiente se detiene con `TASK_EXECUTION_OPEN` y el comando para cancelarla», también con la `RUNNING` sin motor de b). GD-11 paso 3: una cuyo Host sale antes de la revisión del motor posterior al pedido «tampoco lo cumple»; §17.2: «y después nadie vuelve a mirar el pedido», y garantía 3: «En los otros cuatro el resultado es el del Host… no revisa el pedido después del `wait`»; §17.3, fila 4, y límite 2, «Resultado»: el resultado del Host. GD-11 paso 3: «si no [toma el candado], el conductor vive»; paso 1, §17.3 y límite 6: el residuo K lo produce «el conductor», con la marca «posterior al `result.json`»; §17.1: «Es lo único que el conductor hace con la marca» | Límite 8 y §30.1: con una `REQUESTED`, `TASK_EXECUTION_OPEN` y el comando; con la `RUNNING` sin motor de b), el `--grafo` siguiente la recupera en su paso 3 (`CANCELLED` con su pedido, si no `FAILED HOST_INTERRUPTED`) y cierra `FAILED WORK_UNIT_NOT_SUCCEEDED`, sin comando. GD-11 paso 3, §17.2 (párrafo y garantía 3), §17.3 fila 4, límites 1 y 2 de §17.4 y las filas de §30.1 del sondeo, de ME-I22 y del límite 2: el resultado del Host se respeta **salvo** si el Host terminó por una interrupción (`HOST_INTERRUPTED`: salida 130 o 143, o negativa en POSIX); ahí el motor mira el pedido una vez más y, si ya está persistido, la Execution queda `CANCELLED`; con cualquier otra salida (1: `HOST_FAILURE`; 0) se conserva el del Host. Conducta heredada de Task 4. O-1: el candado lo puede tener otro `--cancelar` o un `--grafo` nuevo, y `conductorVivo: true` dice solo que estaba tomado. O-2: el residuo K lo produce quien tenga el candado, y la marca puede quedar entre la lectura de la regla de cierre y el `result.json`. O-3: con el GraphRun ya terminal y el candado tomado, el cancelador sigue sondeando hasta 60 s y sale 0 con `sigue: false`. O-4: §17.1 nombra la lectura de la regla de cierre. Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | F-1: `grafo.py:564` (paso 3, `motor.recuperar`), `:409-413` y `:470-479` (7c), `motor.py:379-427`; refuter G, `repro_limite8b` (1) y `varios-errcmd` (3), 4/4: «`--grafo` siguiente: exit 2 FAILED `WORK_UNIT_NOT_SUCCEEDED`», `executionStatus` `CANCELLED` o `HOST_INTERRUPTED`; `ctrlc` sostiene `TASK_EXECUTION_OPEN` con una `REQUESTED`. F-2: `motor.py:335` (`:325` en `e33b41b`), `host_claude_code.py:84`, `:391` (sin cambios en esa regla desde `e33b41b`); refuter G, `p_corte` 143: 3/3 `CANCELLED` con el pedido 0,21 a 0,39 s después de la salida del Host; control con salida 1: 3/3 `FAILED HOST_FAILURE` con pedido. O-1 a O-3: `grafo.py:650-673` (`:664`, `conductorVivo`), `:320-322`, `:561`; carrera dos-huérfano 10/10. O-2: `grafo.py:188`, `:203`, `:208`; carrera K, 3 de 20 en el residuo. O-4: `grafo.py:188` | La verificación independiente exhaustiva (refuter G) | Nahuel Palacio, 15-10-2026, la decisión de la sesión (enmendar la spec con lo que de verdad se puede garantizar), aplicada a las dos frases que el refuter G encontró falsas |
| O. Las afirmaciones universales sobre las entrañas del motor de Task 4 | §17.2: «Después, el motor mira el pedido una sola vez más, y solo si el Host terminó por una interrupción»; «Con cualquier otra salida… nadie vuelve a mirar el pedido y se conserva el resultado del Host». Garantía 2: «si el motor lo revisa… la Execution termina `CANCELLED`», como regla; garantía 3: «Pasa en cinco casos», «En los otros cuatro el resultado es el del Host, salvo…», «fuera de esa interrupción, no revisa el pedido después del `wait`». La apertura de las garantías: «el motor cumple solo si…». GD-11 paso 3: «tampoco lo cumple, salvo que el Host haya terminado por una interrupción». §17.3, filas `RUNNING` y 4 («con cualquier otra salida… se conserva»). §17.4: «Es la lista completa de los límites conocidos»; límites 1 y 2, «Resultado» y «Origen» («el pedido se mira solo con `CANCELADO`, `INTERRUMPIDO` o `HOST_INTERRUPTED`»); la glosa «`HOST_INTERRUPTED`: salida 130 o 143». §16.3: «Ctrl-C durante el Host», como el único Ctrl-C que absorbe el motor. §15.4: «Lo que garantiza Task 4» y «Cada una, al cerrar, pregunta… su evidencia queda `CHANGES_UNATTRIBUTABLE`». GC-24: «el motor cumple solo si revisa el pedido a tiempo». §30.1, filas del sondeo, de ME-I22, del límite 2 y del 7; GP-08: «pierde contra el Host». GD-21: «nunca llega a armar `--tools`» | **El principio, en §17.2 y en §17.4 (la oración general, al frente):** sobre una Execution en vuelo, Task 5 solo garantiza lo que garantiza el motor de Task 4; esos caminos son de Task 4 y la lista de casos observados es de ejemplos, no exhaustiva (§30.1, ME-I22). Lo absoluto es lo de Task 5: la marca, 7a y 7f, el pedido de cada vuelta del cancelador, la ventana, la regla de cierre, el 7h y la garantía 4 con el límite 8. Con el pedido persistido y la Execution sin `result.json`, la spec no fija qué terminal escribe el motor: el que escriba es válido. §17.2, garantías 2 y 3, GD-11 paso 3, §17.1 (el 7h), §17.3 filas `RUNNING` y 4, §17.4 límites 1, 2, 3 y 7, §16.1, §16.2 G5, §16.3, §15.4, GC-24, §30.1 (sondeo, ME-I22, límites 2, 7 y 8), GP-08 y GD-21 pasan a una de dos formas: un enunciado sobre Task 5, o uno condicionado con sus ejemplos. Hallazgos de H: el Ctrl-C sobre el motor con el Host ya salido es un ejemplo más del límite 2 (F-1); la glosa pasa a «por ejemplo, salida 130 o 143 sin un resultado de proveedor», y el límite 2 suma `PROVIDER_FAILURE` con 143 (observación 2). La recuperación se cita por su regla (T4 MD-24). Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | F-1: `motor.py:296-297` (`except KeyboardInterrupt: codigo = None if cancelada() …`; `:286-287` en `e33b41b`); refuter H, `ctrlc-real` 3/3: `CANCELLED` con salida 0 (antes y después de `:335`) y con 1; controles `n2-0-antes` `SUCCEEDED` y `n2-1-antes` `FAILED HOST_FAILURE`. Observación 2: `host_claude_code.py:403-407` (`PROVIDER_FAILURE` antes que `HOST_INTERRUPTED`); `n2-143-proveedor`. §15.4: `motor.py:409-427` y `evidencia.py:161-168` (la recuperación no pregunta por las otras), `evidencia.py:127-128` (sin foto, `SIN_RESOLVER`). GD-21: `motor.py:268-276`, `:324`; `host_claude_code.py:254-268`, `:318`. El patrón: refuters C (sondeo), E (mismo tramo), F (ventana de 60 s), G (Host cortado, pedido después) y H (Ctrl-C). Notas de H sin cambio de texto propio: ningún test del repo ejerce `motor.py:335` con pedido (observación 3); «nadie vuelve a mirar» también lo desmentía la recuperación (observación 4), que ya cubren la garantía 2 y el límite 7, y que la frase reescrita ya no afirma | La verificación independiente final (refuter H) | Nahuel Palacio, 15-10-2026, la decisión de la sesión (enmendar la spec con lo que de verdad se puede garantizar), aplicada a la causa raíz del patrón: la spec dejó de afirmar universales sobre las entrañas de Task 4 |
| P. Lo normativo separado de lo informativo en §17, y las cuatro frases del refuter I | §17.2: «Lo que se garantiza, y nada más», garantías 1 a 4, la 4 como absoluta («ninguna Execution propia… queda abierta después de su `result.json`», con tres excepciones); §17.3 «Casos» y §17.4 «Lo que la cancelación no garantiza», con celdas «Resultado» y «Resultado válido» en tono de promesa; la oración de §17.4 «Lo que sí es absoluto… y que ninguna Execution propia queda abierta… salvo el límite 8». F-1: §17.1 «Si esa Execution termina `CANCELLED`, la regla de cierre da `CANCELLED`», y la garantía 3, §17.3 fila 4 y el límite 4 razonando por el resultado de la Execution («si quedó `SUCCEEDED`»). F-2: la garantía 4 y §17.3 «El conductor murió con una Execution propia `RUNNING`»: «la recuperación de Task 4 la cierra». F-3: §15.4, «si la hubo y las dos fotos del árbol se tomaron, su evidencia queda `CHANGES_UNATTRIBUTABLE`», con `registro.py:489-506` sin decir que es de `e33b41b`. F-4: GD-11 paso 3, «`motor.cancelar` de Task 4, que le deja el pedido persistido»; §17.3 filas `REQUESTED` y `RUNNING`, «`motor.cancelar` escribe el pedido» | **Estructura:** GD-11 suma al frente qué es norma; GD-11, §17.1 y §17.2 son normativos y redactados como acciones; §17.2 lista lo normativo, (a) a (f) (la marca; el candado y el sondeo; 7a y 7f; 7h y la regla de cierre por nodo; la escritura única; el cruce), dice que todo lo demás es observación y cierra con la oración que resume la norma (antes al final de §17.4). La oración general («Task 5 solo garantiza lo que garantiza el motor de Task 4») queda en §17.2 y §17.4. §17.3 pasa a «Observaciones, no normativas: casos», con la frase de apertura, lo leído del motor, las observaciones 1 a 3 (antes garantías 2 a 4), el párrafo de la escala en producción y la tabla, con su columna «Lo observado (no normativo)» y cada fila marcada como vista o como consecuencia de una norma. §17.4 pasa a «Observaciones, no normativas: límites», columna «Lo observado (no normativo)». La garantía 4 deja de ser garantía: es la observación 3, y el límite 8 suma el Ctrl-C que sale del motor después de la entrega y la `RUNNING` con el candado de vida tomado. **F-1:** §17.1, la observación 2, la fila 4 de §17.3 y el límite 4 razonan por el estado del nodo bajo F (GD-05, GD-15), y §17.1 nombra el caso de P1 como ejemplo. **F-2:** la fila del conductor muerto con `RUNNING`, el límite 7 y el límite 8 suman P3 y P5 como casos vistos; §16.3 dice que con un Ctrl-C el conductor no llama al motor sobre su Execution. **F-3:** §15.4 suma `CHANGES_UNRESOLVED` con HEAD sin commits y la nota de que `registro.py:489-506` es de `e33b41b` (`:522-539` hoy). **F-4:** GD-11 paso 3 y §17.2 dicen que el cancelador **llama** a `motor.cancelar` sobre la propia que el registro da abierta; que el pedido quede persistido depende del estado de la Execution cuando `motor.cancelar` la lee, y pasa a la observación 1; `canceladas` son las Executions sobre las que llamó. Con la misma regla: §16.1 (pasos 1 a 3 como llamadas), §16.2 G5, §16.3, GD-11 (el párrafo de `--cancelar exe_…`) y §30.1 (frase de apertura y filas de la cancelación como límites observados). GE-E48 cambia solo dos referencias: «§17.2, caso 3» por «§17.3, observación 2», y suma «(§17.3, observación 3)» a la de «ninguna Execution propia abierta». Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | F-1: `grafo.py:187-192` (la regla de cierre por nodos), `:441-458` (7h, por el nodo), `:446-447`; refuter I, P1 (con ganchos) y P1b (CLI de producción, 3/3 GraphRun `SUCCEEDED` con la Execution propia `CANCELLED`; control sin la manual: `CANCELLED`). F-2: `motor.py:296-299`, `:309` (el `except KeyboardInterrupt` vuelve a tomar la foto sin otro `except`), `grafo.py:388-394`; `motor.py:392-394` (la recuperación no toca una con el candado de vida tomado), `:469` (`motor.cancelar` cierra solo una `REQUESTED`); refuter I, P3 (A 2/2, B 4/6) y P5 (2/2). F-3: `evidencia.py:93-94`, `:130-132` (sin revisiones comparables, `SIN_RESOLVER` antes de mirar a las otras, `:141`); `registro.py:522` (`def otras_entregadas`); refuter I, P2. F-4: `motor.py:448-468` (sin pedido si ya no está abierta), `grafo.py:263-279`, `:665-667`; refuter I, P4 (2/2: en `canceladas`, sin `cancelacion.json`, `SUCCEEDED`). Lo sostenido por I sin cambio de texto: 7a y 7f (`grafo.py:398`, `:425`), la regla de cierre (`:188`), GD-21, 16.3 en lo de Task 5, la oración general | La verificación independiente (refuter I) | Nahuel Palacio, 15-10-2026, eligió el arreglo estructural entre cuatro opciones en esta sesión |
| Q. Lo normativo achicado: solo borrar o suavizar | F-J1, §17.2 «En una oración»: «Task 5 solo llama a `motor.cancelar` si una vuelta del cancelador la encuentra abierta, y garantiza solo lo que el motor de Task 4 garantiza». F-J3, GD-11 paso 4: «`canceladas` son las Executions sobre las que **llamó** a `motor.cancelar` (…), no las que recibieron un pedido persistido ni las que terminaron `CANCELLED` (…)». F-J2, norma (a): «valida los ids, que el GraphRun exista y se lea, y que esté el catálogo de secretos (si no, error del comando, sin escribir)». O-2: límite 4, «No hay llamada a `motor.cancelar` sobre ella»; su fila de §17.3, «No hubo llamada…»; su fila de §30.1, «Sin llamada a `motor.cancelar`»; límite 5, Origen, «(el pedido sale solo de las vueltas)»; su fila de §30.1, «el pedido a la Execution sale solo de las vueltas del cancelador». Del mismo tipo: GD-11 paso 3, «si lo toma… llama a `motor.recuperar`, llama a `motor.cancelar`…, y escribe el terminal… Qué dejan esas dos llamadas…» y «lo único que hace sobre una Execution propia que una de sus vueltas encuentra abierta es llamar a `motor.cancelar`»; §17.2, «En la primera vuelta… llama a `motor.cancelar` sobre ella. Si el turno aparece después de la última vuelta, no hay llamada»; §16.3, «queda como la dejó el motor (lo observado…)»; §17.3, observación 1, «no hay llamada y se ve lo de la observación 2» | Las mismas frases sin lo borrado. §17.2 cierra con la oración general, ya escrita: «Task 5 solo garantiza lo que garantiza el motor de Task 4». GD-11 paso 4: «(`canceladas`: ver §17.3 y §17.4, que son observaciones.)». Norma (a): la validación del catálogo queda solo en la rama `ACTIVE`, la cláusula anterior restringida (borrarla entera dejaba falsa «si lo lee `ACTIVE`, escribe», por el mismo pj2b). Límites 4 y 5 y sus filas: solo el caso visto. GD-11 paso 3: «cierra el huérfano como §16.1» y «Es un sondeo con ventana». §16.3: «No llama al motor sobre su Execution (§17.4, límite 8 a)». Observación 1: «ver la observación 2». Ninguna afirmación nueva. Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | F-J1 y O-2: refuter J, pj3 orac 2/2; `grafo.py:561` → `:326`. F-J3: pj8 e51; `grafo.py:665-667`, `:659` → `:326`. F-J2: pj2b; `grafo.py:637-641`. Del mismo tipo: `grafo.py:320-322` (pj8 k), `:323-326`, `:388-394` | La verificación independiente final (refuter J) | Nahuel Palacio, 15-10-2026, el arreglo estructural elegido en esta sesión, en su forma mínima: solo borrar |
| R. El paréntesis de la norma (b) | Norma (b) de §17.2: «si lo toma, cierra el huérfano como §16.1 (llama a `motor.recuperar`, llama a `motor.cancelar` sobre cada propia que el registro da abierta, escribe el terminal)» | «si lo toma, cierra el huérfano como §16.1». La norma (a), con su línea larga partida, sin cambiar ninguna palabra. Revisados con el mismo criterio y sin cambio: GD-11 pasos 2 y 3, §16.1 y §17.1. Ninguna afirmación nueva. Sin escenario, mutación, invariante, decisión ni conflicto nuevos; ninguna marca `rojo visto` cambia | `grafo.py:320-322`: con el GraphRun ya terminal al tomar el candado, `cerrar_huerfano` vuelve sin llamar a nada | La novena pasada (el informe de `harness-task-architect`) | Nahuel Palacio, 15-10-2026, el mismo arreglo estructural, en su forma mínima: solo borrar |

**Decisiones abiertas:** ninguna.

---

## 28. Canonical model changes

Se planifican; los escribe quien construya, y E-09 de t64 tiene que seguir verde. La ficha de
`GraphRun` va con el schema (§34, paso 8); el resto de la tabla, en el paso 12 (enmienda del 14-10-2026,
27.1 A). Las dos últimas filas, de la introducción y de la apertura de «El límite de la ejecución», se
sumaron después de ese paso (27.1 H): las escribe quien construye en la etapa siguiente, antes de las
mutaciones.

| Dónde en MC | Hoy | Pasa a decir |
|---|---|---|
| Mapa de contextos, fila Execution (`:1735`) | «una WorkUnit por invocación; Task 5 decide el resto» | Suma GraphRun como agregado; lifecycle `ACTIVE → terminal`; «un GraphRun lleva un plan entero, serial, sin reintento ni reanudación» |
| Párrafo de Execution (`:1737-1740`) | «El scheduling, las colas y el reintento automático son de Task 5» | El scheduling serial es de Task 5 (ADR-0016); colas, paralelismo y reintento automático siguen sin existir |
| Concepto nuevo `GraphRun` | — | Ficha: qué es, contexto Execution, Aggregate Root, identidad `grf_…`, ciclo, invariantes GE-I03, GE-I10, GE-I13, GE-I15, GE-I16; crea y lee `bin/ejecucion/grafo.py`; «Persistencia y contrato» nombra `graph-run-result.schema.json`. **Se escribe junto con el schema**, no en el paso 12: su fila del catálogo y su bloque con los diez campos (enmienda del 14-10-2026, 27.1 A) |
| Concepto nuevo `GraphRunError` | — | Ficha: nueve códigos; una máquina lee solo `code` |
| `ExecutionId` (`:1023-1026`) | «lo genera HARNESS al admitir» | «lo genera HARNESS: la admisión, o un GraphRun al registrar un despacho, que se lo pasa a la admisión» |
| Vocabulario, «run / corrida» (`:1976`) | «en Execution no se usa» | «en Execution se usa solo como `GraphRun`, nunca para una Execution» |
| Vocabulario, fila nueva | — | «grafo / GraphRun»: un intento de llevar un plan entero a un terminal; no es una Execution ni un estado del Plan |
| «Lo que todavía no existe» (`:2052-2054`) | «Un ejecutor de lotes o de grafos… nada elige la siguiente»; «Un scheduler, colas, workers o paralelismo» | «Un ejecutor paralelo o distribuido: el GraphRun elige la siguiente, de a una»; «Un scheduler concurrente, colas, workers o paralelismo». Conserva `ejecutor` y `scheduler` |
| «Lo que todavía no existe» (`:2055-2058`) | Reintento, reanudación, estado de corrida fuera de Execution | Sin cambio: siguen siendo verdad. El GraphRun vive en Execution |
| «Lo que existe ahora» | — | Suma el GraphRun, `ejecutar --grafo` y `graph-run-result/1.0` |
| «Lo que sigue intacto» (`:2066-2074`) | Los dos invariantes de ADR-0013 §4 | Sin cambio. El GraphRun no lee la contabilidad y no escribe el Plan |
| Introducción, segundo párrafo (`:9-13`; enmienda del 14-10-2026, 27.1 H) | «…y desde Task 4 tiene un motor mínimo ([`docs/cambios/minimal-execution-engine/spec.md`](../cambios/minimal-execution-engine/spec.md) y [ADR-0015](../adr/0015-el-motor-minimo-de-ejecucion.md)): una WorkUnit por invocación de `ejecutar`.» | «…y desde Task 4 tiene un motor mínimo ([`docs/cambios/minimal-execution-engine/spec.md`](../cambios/minimal-execution-engine/spec.md) y [ADR-0015](../adr/0015-el-motor-minimo-de-ejecucion.md)): una WorkUnit por invocación de `ejecutar --unidad`. Desde Task 5 tiene también el GraphRun ([`docs/cambios/graph-execution/spec.md`](../cambios/graph-execution/spec.md) y [ADR-0016](../adr/0016-la-ejecucion-de-un-grafo.md)): `ejecutar --grafo` lleva un plan entero a un terminal, de a una WorkUnit por vez.» Los enlaces de Task 4 quedan como están; la oración de 0.31.0 que sigue, también |
| «El límite de la ejecución», párrafo de apertura (`:2062-2065` del árbol de trabajo; ídem) | «Desde ADR-0014, Execution es un contexto, y desde ADR-0015 tiene un motor mínimo. **HARNESS ejecuta una WorkUnit por invocación de `dev-harness.py ejecutar`, un intento, sincrónico:** la admite, crea la Execution, la entrega al Host y deja su resultado. Elegir la siguiente, en qué orden y cuántas a la vez, es de quien invoca, y de Task 5.» | «Desde ADR-0014, Execution es un contexto; desde ADR-0015 tiene un motor mínimo, y desde ADR-0016, el GraphRun. **HARNESS ejecuta una WorkUnit por invocación de `dev-harness.py ejecutar --unidad`, un intento, sincrónico:** la admite, crea la Execution, la entrega al Host y deja su resultado. **Con `ejecutar --grafo`, un GraphRun elige la siguiente, en el orden de `orden_de_ejecucion`, de a una:** cada una pasa por el mismo motor y por las mismas dos admisiones. Más de una a la vez no existe.» Queda antes del primer `###` de la sección, así que ningún apartado que leen E-09, EX-E47 y ME-E48 cambia |

---

## 29. ADR plan

#### GD-26. ADR-0016, «La ejecución de un grafo»

Nuevo, `docs/adr/0016-la-ejecucion-de-un-grafo.md`. **No edita ADR-0015**: lo revisa, como ADR-0015
pide en su cláusula de revisión («se revisa cuando Task 5 agregue scheduling»,
`0015-el-motor-minimo-de-ejecucion.md:153-154`). ADR-0013 y ADR-0014 tampoco se editan.

**Decisiones que registra:**

1. GraphRun es un agregado de Execution, no un contexto nuevo.
2. Serial y fail-fast, en el orden de `orden_de_ejecucion`, en el mismo proceso.
3. Sin reintento automático y sin reanudación, también entre GraphRuns.
4. Atado a una huella; el motor recibe la huella esperada.
5. Cuatro marcas de una sola escritura y un candado estable por tarea.
6. Ciego a capacidades; R5 se resuelve en el Host Adapter.
7. N1 se cierra sin candado nuevo.

**En contra, y dicho:** en Windows, `tests.run` no se ejecuta; la evidencia sigue degradando con
archivos sucios compartidos; un plan replanificado vuelve a correr todo; una Execution manual abierta
que el GraphRun observa antes de despachar detiene el grafo, y una de otra unidad que se publica
después de ese chequeo puede convivir con la propia, con evidencia no atribuible (§15.4).

**Revisión:** se revisa cuando se agregue paralelismo, reintento automático, seguir con las ramas
independientes, un segundo Host, o el mapeo de `tests.run` por plataforma.

---

## 30. Risks

### 30.1 Riesgos aceptados

Las filas de la cancelación (desde «La cancelación del grafo es un sondeo…») describen **límites
observados** (§17.3, §17.4), no garantías ni promesas: lo que esta Task promete de la cancelación es solo
la lista normativa de §17.2 (27.1 P).

| Riesgo | Qué pasa | Por qué se acepta |
|---|---|---|
| R1 de T4: el Host sobrevive al motor | Una huérfana `RUNNING` cerrada con el Host vivo puede seguir escribiendo | **El GraphRun no lo agranda:** si su propia Execution queda huérfana, el GraphRun siguiente la encuentra `NOT_SATISFIED` (o todavía abierta) y se detiene antes de despachar nada más, porque todo lo anterior en el orden ya está `SATISFIED`. Una huérfana ajena es el R1 de hoy |
| R2 de T4: `REQUESTED` huérfana | Bloquea su clave y detiene al GraphRun | Lo pide una persona (ADR-0015:62-63); el mensaje trae el comando |
| Un plan replanificado vuelve a correr lo que estaba `SUCCEEDED` | Nada se reusa entre huellas | EX-I26 de T3 |
| Fail-fast | Una unidad que falla deja sin correr ramas independientes | GC-17; GP-04 |
| `tests.run` en Windows | Ninguna unidad que la pida corre por el motor | GD-21: un rechazo honesto en lugar de un éxito falso; GP-02 |
| Una Execution manual de otra unidad cuyo turno se publica después del chequeo 7d (§15.4) | Puede coexistir con la Execution propia del GraphRun; si sus `RUNNING` se solapan, las dos evidencias pueden quedar `CHANGES_UNATTRIBUTABLE` (o `CHANGES_UNRESOLVED`, §15.4) | Excluirla cambia ExecutionAdmission / T3; la evidencia degrada, no miente |
| Evidencia en serial con archivos sucios compartidos | Una unidad que reescribe lo que la anterior dejó sucio queda `CHANGES_UNATTRIBUTABLE` | Regla de T4 MD-20; el motor no commitea |
| Una huérfana `RUNNING` de **otra** tarea | Sin recuperar, envenena la evidencia de todo el proyecto (`registro.py:502-503`) | Riesgo de T4 (WU04 RC3), igual con o sin grafo |
| `admission.capabilities: ALL_AVAILABLE` | La request de una Execution rechazada por la 13b afirma algo que su resultado desmiente | Arreglarlo es pasar el adaptador a `al_pedir`: cambia el comportamiento de Task 4 sin un caso del grafo que lo pida (GP-07) |
| `--cancelar grf_…` y `--grafo` en el mismo instante | El que arranca sale `GRAPH_ALREADY_ACTIVE` | Vivacidad, no seguridad |
| La cancelación del grafo es un sondeo de un segundo, y el motor revisa el pedido por tramos de un segundo (27.1 J y L; §17.4, límites observados 1 y 3) | Observado: una Execution propia quedó con su propio resultado cuando su Host terminó antes de que una vuelta del cancelador la encontrara abierta, **y también cuando salió en el mismo tramo en que se persistió el pedido**: con el pedido persistido, el resultado es el que escriba el motor de Task 4 (§17.4, límites 1 y 2, ejemplos observados y no lista exhaustiva; por ejemplo, una falla `HOST_INTERRUPTED` o un Ctrl-C sobre el motor dieron `CANCELLED`). Un Host que dura menos que un intervalo del cancelador más un tramo, y algo más, terminó `SUCCEEDED` aunque su `cancelacion.json` ya existiera. Con el nodo `SATISFIED`, la regla de cierre da lo que da por nodos: si era el último, el GraphRun cerró `SUCCEEDED` con `cancelRequested: true`. Origen observado: `proceso.esperar` mira el pedido al comienzo de cada tramo (`proceso.py:63-66`) y devuelve `TERMINO` apenas el Host sale (`:72`) | Es la regla de GC-23 aplicada a lo que el motor de Task 4 observa. Cerrarlo pide acortar el sondeo (no cierra la ventana, la achica), que el motor mire la marca del grafo, o que `proceso.esperar` revise el pedido después del `wait` (las dos últimas cambian Task 4); Nahuel Palacio decidió el 15-10-2026 no tocar el código ni Task 3/4 |
| La misma conducta contradice T4 ME-I22 (27.1 L) | ME-I22 dice «un pedido de cancelar persistido antes de que la corrida termine o se corte da `CANCELLED`» (`minimal-execution-engine/spec.md:1250`); con un pedido persistido a mitad del último tramo, la corrida puede dar el resultado del Host (o `CANCELLED`, si otro camino del motor mira el pedido después: §17.4, límite 2, ejemplos). Pasa con o sin grafo | Es de Task 4 y no se corrige en esta Task. Va a FH (GP-08) |
| Una marca de cancelación que el terminal no refleja: posterior al terminal, o escrita entre la lectura de la regla de cierre y el `result.json` (27.1 K y N; §17.4, límite 6) | `--grafo --estado` muestra `cancelRequested: true` sobre un terminal cuyo `cancelRequested` es `false` | El terminal es la verdad y no cambia (GE-I14); la marca es inerte. Evitarlo pide cambiar el código |
| Un pedido persistido con el Host ya salido y la Execution sin `result.json` (27.1 M, N y O; §17.4, límite 2) | El resultado es el que escriba el motor de Task 4, y esta spec no fija cuál. Observado, como ejemplos y no como lista exhaustiva: el resultado del Host aunque su `cancelacion.json` exista (salida 1: `FAILED HOST_FAILURE`; salida 0: `SUCCEEDED`; salida 143 con un resultado de proveedor: `FAILED PROVIDER_FAILURE`), o `CANCELLED` cuando un camino del motor posterior a la salida del Host mira el pedido ya persistido (una falla `HOST_INTERRUPTED`, `motor.py:335`; un Ctrl-C sobre el motor, `motor.py:296-297`, también con salida 0 o 1: refuter H, F-1) | Es de Task 4, sin cambios desde `e33b41b`; Nahuel Palacio decidió el 15-10-2026 no tocar Task 4. Va con GP-08 |
| La ventana de 60 s del cancelador vence antes del turno de la Execution en vuelo (27.1 M; §17.4, límite observado 4; refuter F, F-1) | La Execution corrió entera, con su resultado y sin pedido; el cancelador sale con 0 diciendo «su conductor sigue: el pedido quedó escrito y lo va a cumplir», que significa lo que fija GD-11 paso 4 (no se despacha nada más), no que esa Execution se cancele. El GraphRun cierra por la regla de cierre, por nodos; visto: `CANCELLED` en 7a en A→B→C, y `SUCCEEDED` con `cancelRequested: true` en A→B con el nodo de B `SATISFIED`. Origen: `ESPERA = 60` y la salida al vencer (`grafo.py:601`, `:668-669`) | Es de Task 5. Hace falta que el conductor tarde más que la ventana entre 7f y el turno (en producción, una admisión lenta). Cerrarlo pide cambiar el código (una ventana atada a la vida del conductor, o que el conductor pida él mismo al ver la marca); la decisión del 15-10-2026 es no tocarlo. Lo remedia una persona con otro `--cancelar grf_…` o con `--cancelar exe_…` |
| El cancelador se corta antes de pedir (27.1 M; §17.4, límite observado 5) | Igual que la fila anterior para la Execution en vuelo | Es de Task 5 y del mismo origen (`grafo.py:651-670`) |
| Conductor muerto con una Execution propia `RUNNING` (27.1 M; §17.4, límite observado 7) | Observado: la recuperación de Task 4 la cerró por su regla (T4 MD-24: `CANCELLED` o `FAILED HOST_INTERRUPTED`) y nadie mató al Host, que puede seguir escribiendo; con su candado de vida tomado por otro proceso, no la cerró (límite 8 c) | R1 de T4: `recuperar` nunca mata un proceso (`motor.py:382`). Igual con o sin grafo |
| Una Execution propia abierta después del `result.json` del GraphRun (27.1 M y P; §17.4, límite observado 8; no es una garantía) | Casos vistos, sin pretender que sean todos: un Ctrl-C que sale del motor hacia el conductor, antes o después de la entrega; un error del comando del motor después de publicar; o el candado de vida de la Execution tomado por otro al cerrar un huérfano. Dejaron una `REQUESTED` (R2) o una `RUNNING` (sin motor, o con pedido) con el GraphRun ya cerrado (refuter I, P3 y P5) | Es R2 de T4 más el cierre de esta Task. Visto: con una `REQUESTED`, el GraphRun siguiente se detuvo con `TASK_EXECUTION_OPEN` y nombró el comando para cancelarla; con una `RUNNING` sin motor, la recuperó en su paso 3 (`grafo.py:564`; por T4 MD-24: `CANCELLED` con su pedido, si no `FAILED HOST_INTERRUPTED`) y cerró `FAILED WORK_UNIT_NOT_SUCCEEDED`, sin comando para cancelarla (refuter G, F-1). Evitarlo pide cambiar el código |
| `--cancelar grf_…` corre la recuperación de Task 4 sobre la TaskKey (27.1 M; §17.4, límite observado 9) | Observado: una `RUNNING` huérfana de la tarea, también una manual, quedó cerrada por la recuperación mientras se cancelaba el grafo | Es `motor.cancelar` de Task 4 (`motor.py:444`), lo mismo que hace cada `--grafo` y cada `--unidad`; no es cancelarla: no se le escribe un pedido |

### 30.2 Otros riesgos

- **El costo de un GraphRun** es la suma de sus Executions, sin tope (MP-03 de T4).
- **El costo de las admisiones** (compuerta y vigencia del flujo con red, por despacho) no se midió.
- **La tabla de herramientas por plataforma envejece** con una versión nueva de Claude Code. Está
  fechada, y una lectura nueva del Host la corrige.
- **`proceso.esperar` y su docstring** (WU05 C5): el pedido de cancelar se mira antes del `wait`, así
  que un Host que terminó entre dos tramos puede quedar `CANCELADO` aunque el docstring diga «gana su
  código» (`proceso.py:58`, `:63-74`). Es de Task 4, no se reprodujo, y va a FH (GP-08).

### 30.3 Pendientes que deja esta Task

| GP | Pendiente | De quién | Va a |
|---|---|---|---|
| GP-01 | Dueño de `bin/ejecucion/` y de sus schemas, incluido `graph-run-result` | La fábrica, con el `harness-budget-auditor` | FH, ítem existente |
| GP-02 | Mapear `tests.run` a `PowerShell` en Windows: una lectura del Host real con `--tools PowerShell`, los `tools:` de los agentes y la revisión de los hooks | Una Task con su spec | FH |
| GP-03 | Paralelismo: atribución de evidencia por Execution, revisión de ME-E47 y E-41 con ADR, contención del árbol de trabajo | Una Task con su spec | PENDIENTES-I |
| GP-04 | Seguir con las ramas independientes después de una falla | Una Task con su spec | PENDIENTES-I |
| GP-05 | Planning: revalidar ciclos y dependencias en `aceptar_guardado`; `uniqueItems` en `dependencies` | Planning | FH |
| GP-06 | La fila de `ejecutar` en `tool_policy._harness`, con `--grafo` | `harness-hook-engineer` | FH, ítem R4 existente |
| GP-07 | `admission.capabilities` escrito antes de la 13b | Una Task con su spec | FH |
| GP-08 | `proceso.esperar` contra su docstring, y contra T4 ME-I22: un pedido persistido a mitad del último tramo puede perder contra el Host (§30.1, 27.1 L). Suma, como dato para quien lo tome, el límite 4 de §17.4 (la ventana de 60 s del cancelador de esta Task), que no es de Task 4 y queda documentado (27.1 M) | `harness-staff-engineer` o Task 4 | FH |

---

## 31. Invariants

Cada uno se puede contradecir con un test determinista; ninguno depende de una lectura.

| Id | Invariante | Cómo se observa | Escenarios |
|---|---|---|---|
| GE-I01 | Toda Execution que causa un GraphRun sale de `motor.ejecutar`, con sus dos admisiones. El GraphRun no crea una request, un turno ni una carpeta `exe_…`, y no escribe adentro de una | Registro y estático | GE-E01, GE-E60, GE-E61 |
| GE-I02 | `execution-request/1.0`, `execution-result/1.0`, los 23 códigos, `PRECEDENCIA`, `ESTADOS`, `TRANSICIONES`, la clave de idempotencia y `ejecutar --unidad` no cambian | Huellas de archivos y suite 72 | GE-E25, GE-E65 |
| GE-I03 | Un GraphRun está atado a una (TaskKey, F) fijada al crearlo, y cuenta solo Executions bajo claves de F: nunca adopta otra huella | Registro precargado | GE-E01, GE-E21, GE-E22 |
| GE-I04 | Ninguna Execution despachada por un GraphRun se entrega con una request cuya huella no es F | `entrega.json` ausente | GE-E24, GE-E25 |
| GE-I05 | Si la huella del plan deja de ser F, el GraphRun no despacha nada más y cierra | Despachos | GE-E23, GE-E24, GE-E26, GE-E27 |
| GE-I06 | El GraphRun no escribe el Plan, el TaskFlowState, la compuerta, el registro de agentes ni las capacidades, no replanifica y no lee la contabilidad | Archivos sin cambio; estático | GE-E17, GE-E23 |
| GE-I07 | Antes de existir, la estructura valida: al menos una unidad, ninguna dependencia repetida, `orden_de_ejecucion` sin error. Si no, no hay GraphRun ni Execution | Disco vacío | GE-E08, GE-E09 |
| GE-I08 | El selector es determinista: el orden es el de `orden_de_ejecucion`, la elegibilidad sale de `dependencies` y del último turno bajo F, y nunca de `executionOrder` guardado | Secuencia de despachos | GE-E02, GE-E04, GE-E10 |
| GE-I09 | Una unidad se despacha solo con todas sus dependencias `SATISFIED` bajo F | Turnos y `admission.dependencies` | GE-E03 |
| GE-I10 | Nunca se despacha una unidad con último turno bajo F, y a lo sumo una vez por GraphRun: sin reintento automático | Turnos e invocaciones del Host | GE-E05, GE-E07, GE-E20, GE-E40 |
| GE-I11 | El GraphRun tiene a lo sumo una Execution propia abierta a la vez. Antes de cada despacho, si observa cualquier Execution abierta o ilegible en la misma TaskKey, no despacha y falla con `TASK_EXECUTION_OPEN`. No prohíbe que una Execution manual de otra WorkUnit empiece después del chequeo y coexista con la propia ya despachada: eso no la viola (GE-I31) | Intervalos del Host; despachos | GE-E02, GE-E30, GE-E31, GE-E33, GE-E34, GE-E35, GE-E71 |
| GE-I12 | Fail-fast: después de la primera unidad que no queda `SUCCEEDED`, o del primer rechazo, no hay otro despacho | Despachos | GE-E11, GE-E18, GE-E19 |
| GE-I13 | `SUCCEEDED` del GraphRun si y solo si todas las unidades del conjunto congelado están `SATISFIED` bajo F; es mecánico | `result.json` | GE-E01, GE-E06, GE-E42, GE-E58 |
| GE-I14 | El terminal se escribe una vez, gana el primero, y sigue la regla de cierre: `SUCCEEDED`, si no `CANCELLED` con marca, si no `FAILED` | `result.json` | GE-E42, GE-E49, GE-E50 |
| GE-I15 | A lo sumo un GraphRun `ACTIVE` por TaskKey. Ser su conductor es tener el candado estable de la tarea, y `inicio.json` se escribe solo con él tomado; sin pid ni fecha | Dos procesos | GE-E28, GE-E29, GE-E43 |
| GE-I16 | Un GraphRun no se reanuda: un huérfano lo cierra quien toma el candado, y seguir es otro GraphRun | Cortes por gancho | GE-E36, GE-E37, GE-E38, GE-E39, GE-E42 |
| GE-I17 | El estado sale de marcas de una sola escritura y del registro de Executions: no hay un archivo que se reescriba, y cada marca tiene sus claves cerradas | Escrituras; claves | GE-E41, GE-E60, GE-E61 |
| GE-I18 | Cancelar el grafo escribe la marca antes de propagar; propaga solo con `motor.cancelar`, solo a Executions propias abiertas; es idempotente; con la marca vista, no hay despacho | Dos procesos y ganchos | GE-E46, GE-E47, GE-E48, GE-E50, GE-E51 |
| GE-I19 | El GraphRun no cancela, no cierra y no toma como propia una Execution ajena; una `SUCCEEDED` ajena bajo F cuenta como `SATISFIED`, con `dispatched: false` | Registro | GE-E05, GE-E30, GE-E52, GE-E71 |
| GE-I20 | `GraphRunError` es cerrado y propio; un ExecutionError aparece solo en `executionCode`. El conductor decide solo con `status`, `error.code`, el estado derivado y la huella | Códigos; estático | GE-E11 a GE-E16, GE-E17, GE-E60 |
| GE-I21 | Después de un `HOST_INTERRUPTED` o de un `KeyboardInterrupt`, el GraphRun no despacha nada más | Despachos | GE-E44 |
| GE-I22 | Un error del comando del motor no se lee como «no hay Execution»: el conductor deriva por el `executionId` preasignado | `result.json` | GE-E32, GE-E45 |
| GE-I23 | La evidencia del GraphRun son ids, números de turno y códigos: no copia `evidence`, diffs ni texto del agente o del Host | Claves de `result.json` | GE-E62, GE-E68 |
| GE-I24 | `requestedBy` de cada Execution despachada es el del GraphRun | Requests | GE-E69 |
| GE-I25 | Ninguna sonda de candado toca una carpeta en creación ni borra un temporal nuevo | Dos procesos | GE-E53, GE-E54, GE-E55 |
| GE-I26 | Una capability cuya herramienta el Host no ofrece en la plataforma sale `REJECTED CAPABILITY_UNAVAILABLE` antes de `entrega.json`; el GraphRun no evalúa capacidades | Registro; invocaciones del Host; estático | GE-E17, GE-E56, GE-E57, GE-E58 |
| GE-I27 | Después de la entrega el motor sigue sin emitir `CAPABILITY_UNAVAILABLE` (ME-I29), y el GraphRun trata un `FAILED` con ese código como no exitoso | Registro fabricado | GE-E59 |
| GE-I28 | Nada de `bin/` ni de `comun/` importa concurrencia, un SDK de modelos ni LangGraph; ningún lanzamiento nuevo de procesos; trece subcomandos | Estático | GE-E64 |
| GE-I29 | Toda escritura del GraphRun la hace `registro.py`, bajo `.claude/ejecuciones/<KEY>/grafos/`, y las funciones de Task 4 no ven esa carpeta | Estático y registro | GE-E61, GE-E62 |
| GE-I30 | Leer el estado de los GraphRuns no escribe, no recupera y no cierra nada | Huellas de archivos | GE-E70 |
| GE-I31 | Una Execution manual de otra WorkUnit que comienza después del chequeo preventivo puede coexistir con una Execution propia del GraphRun; esa convivencia no habilita un segundo despacho propio, el GraphRun no la cancela, no la rechaza ni la toma como propia, y conserva la semántica de evidencia de Task 4 | Dos procesos y ganchos; despachos; registro; evidencia | GE-E71 |

---

## 32. Scenarios

Todos pasan por la suite, con el Host falso (`tests/fixtures/host_falso.py`, extendido en §34),
procesos reales del sistema operativo cuando hay carrera, y cortes por gancho cuando hay una ventana.
**Ninguno lleva `· verificación: lectura`:** ningún sujeto es una corrida de un modelo (ADR-0009), y
todos se alcanzan con un test determinista. Cada test nombra su id en el título o en un comentario.

«Plan A→B→C» es un plan 2.1 `READY_FOR_EXECUTION` con esas tres unidades `PENDING`, cada una con un
agente ejecutable y capacidades que el adaptador provee, salvo que el escenario diga otra cosa. Las
afirmaciones sobre invocaciones del Host las cuenta la bitácora del Host falso: una entrada por
invocación, que cuenta aunque el Host muera desde afuera (`fin: null`), y un intervalo para cada una
que terminó (§34, paso 6; enmienda del 14-10-2026, 27.1 C).

### Camino feliz y estructura

- **GE-E01** — Con el plan A→B→C y un Host falso que devuelve `COMPLETE` para las tres,
  `ejecutar <KEY> --grafo` crea un GraphRun, deja tres marcas de despacho `001`, `002` y `003` para A, B
  y C, tres Executions `SUCCEEDED` cuyas requests tienen `plan.planFingerprint` igual al
  `planFingerprint` de `inicio.json`, y un `result.json` `SUCCEEDED`, con los tres nodos `SATISFIED`
  y `dispatched: true`. Sale con 0. · rojo visto: sí (A-01 propia, etapa 5a)
- **GE-E02** — Con A→{B, C}, los despachos son A, B, C en ese orden; ni B ni C tienen turno antes de que
  exista el `result.json` de A; y los intervalos de las tres invocaciones del Host, registrados por la
  bitácora, no se solapan. · rojo visto: sí (GM-01, etapa 5a)
- **GE-E03** — Con {B, C}→D, D no tiene turno mientras B o C no estén `SUCCEEDED`, y la request de D
  lleva en `admission.dependencies` los `executionId` de B y de C. · rojo visto: sí (GM-02, etapa 5a)
- **GE-E04** — Con tres unidades sin dependencias, `zeta`, `alfa` y `medio`, los despachos son `alfa`,
  `medio`, `zeta`. · rojo visto: sí (GM-01, etapa 5a)
- **GE-E05** — Con A ya `SUCCEEDED` bajo F por un `ejecutar --unidad` anterior, el GraphRun no crea un
  turno para A, los archivos de la Execution de A quedan idénticos byte a byte, el Host recibe dos
  invocaciones (B y C), y el nodo A del resultado está `SATISFIED` con `dispatched: false`.
  · rojo visto: sí (GM-03, etapa 5a)
- **GE-E06** — Con las tres unidades ya `SUCCEEDED` bajo F, `--grafo` crea un GraphRun sin marcas de
  despacho, con `result.json` `SUCCEEDED`, el Host no recibe invocaciones y sale con 0.
  · rojo visto: sí (GM-03, etapa 5a)
- **GE-E07** — Dos `--grafo` seguidos sobre el mismo plan dejan dos GraphRuns con ids distintos, los dos
  `SUCCEEDED`, y el segundo no crea ninguna Execution. · rojo visto: sí (GM-03, etapa 5a)
- **GE-E08** — Un plan guardado a mano con un ciclo, con una unidad que depende de sí misma, con una
  dependencia a una unidad inexistente, con una dependencia repetida (`["a", "a"]`) o sin unidades:
  `--grafo` sale con 2 y `GRAPH_STRUCTURE_INVALID`, y no queda ninguna carpeta `grf_…`, ningún turno ni
  ninguna Execution. · rojo visto: sí (GM-06 y GM-07, etapa 5a)
- **GE-E09** — Sin plan, con un plan que no es JSON, con un plan de otra TaskKey o con dos unidades del
  mismo id: `--grafo` sale con 2 y `GRAPH_PLAN_UNREADABLE`, sin carpeta `grf_…` ni Execution.
  · rojo visto: sí (GM-07, variante propia, etapa 5a)
- **GE-E10** — El mismo plan de cinco unidades con dos niveles y fan-in, en dos proyectos recién
  armados, da la misma secuencia de `workUnitId` en las marcas de despacho. · rojo visto: sí (GM-01, etapa 5a)

### Admisión: el GraphRun elige, la admisión decide

- **GE-E11** — Con A→B→C y un gancho que, después de que A queda `SUCCEEDED`, deja al flujo sin
  permiso de delegar: B no tiene turno, C tampoco, y el GraphRun cierra `FAILED` con
  `ADMISSION_REJECTED`, `workUnitId: b`, `executionId: null` y `executionCode:
  DELEGATION_NOT_ALLOWED`. La Execution de A queda idéntica. · rojo visto: sí (GM-08, etapa 5a)
- **GE-E12** — Con una compuerta que bloquea solo las normas de B, el GraphRun cierra con
  `ADMISSION_REJECTED` y `executionCode: NORMATIVE_GATE_BLOCKED`; la compuerta se llamó con las normas
  de A al despachar A y con las de B al despachar B, nunca una sola vez para el GraphRun entero.
  · rojo visto: sí (GM-08 y GM-32, etapa 5a)
- **GE-E13** — Con el agente de B que deja de rutear después de A, el GraphRun cierra con
  `ADMISSION_REJECTED` y `executionCode: AGENT_UNAVAILABLE`, sin turno para B. · rojo visto: sí (GM-08, etapa 5a)
- **GE-E14** — Con una capability de B que deja de estar disponible después de A, el GraphRun cierra
  con `ADMISSION_REJECTED` y `executionCode: CAPABILITY_UNAVAILABLE`, sin turno para B.
  · rojo visto: sí (GM-08, etapa 5a)
- **GE-E15** — Con un gancho `antes_de_entregar` que borra `.claude/agents/<agente de B>.md`, B queda
  `REJECTED` con `AGENT_UNAVAILABLE`, sin `entrega.json`, y el GraphRun cierra con
  `WORK_UNIT_NOT_SUCCEEDED`, `executionId` el de B, `executionStatus: REJECTED`. · rojo visto: sí (GM-08, etapa 5a)
- **GE-E16** — Con un plan que no está `READY_FOR_EXECUTION`, el GraphRun se crea, ninguna Execution
  existe, y cierra con `ADMISSION_REJECTED` y `executionCode: PLAN_NOT_READY`. · rojo visto: sí (GM-08, etapa 5a)
- **GE-E17** — `ejecucion/grafo.py` no importa `flujo`, `auto_refresh`, `registro_agentes`,
  `capacidades`, `contabilidad` ni `refutacion`; no llama a `admision._regla`, `admision.al_pedir`,
  `admision.al_entregar`, `adaptador.provee` ni `plan.escribir`; y no lee `detail` ni `artifact` de un
  resultado o un rechazo: ningún acceso `["detail"]`, `.get("detail")`, `["artifact"]` ni
  `.get("artifact")`. · rojo visto: sí (GM-31 y GM-43, etapa 5a)

### Dependencias y fallas

- **GE-E18** — Con A→B→C más una unidad D sin dependencias que va después de B en el orden, y un Host
  falso que declara `PARTIAL` para B: B queda `FAILED AGENT_DECLARED_NOT_COMPLETE`, ni C ni D tienen
  turno, y el GraphRun cierra con `WORK_UNIT_NOT_SUCCEEDED`, `workUnitId: b`, `executionCode:
  AGENT_DECLARED_NOT_COMPLETE`. Sale con 2. · rojo visto: sí (GM-08, etapa 5a; GM-42, etapa 6A)
- **GE-E19** — Con B `RUNNING` y un `ejecutar <KEY> --cancelar <exe de B>` desde otro proceso, B queda
  `CANCELLED`, C no tiene turno, y el GraphRun cierra `FAILED` con `WORK_UNIT_NOT_SUCCEEDED` y
  `executionStatus: CANCELLED`: no `CANCELLED`, porque nadie canceló el grafo. · rojo visto: sí (GM-41, etapas 5a y 6A)
- **GE-E20** — Con A `FAILED` bajo F por un `--unidad` anterior, `--grafo` no crea un turno para A y
  cierra con `WORK_UNIT_NOT_SUCCEEDED`, `dispatched: false`. Después de un `ejecutar --unidad a` que la
  deja `SUCCEEDED`, un `--grafo` nuevo despacha B y C y termina `SUCCEEDED`. · rojo visto: sí (GM-04, etapa 5a)
- **GE-E21** — Con A `SUCCEEDED` bajo una huella F′ de una versión anterior del plan, el GraphRun sobre
  F despacha A otra vez, y los archivos de la Execution de F′ quedan idénticos byte a byte.
  · rojo visto: sí (GM-05, etapa 5a)
- **GE-E22** — Con A `FAILED` bajo F′, el GraphRun sobre F despacha A normalmente. · rojo visto: sí (GM-05, etapa 5a)

### La huella del plan

- **GE-E23** — Con un gancho que reescribe el plan, con otro contenido, después de que A queda
  `SUCCEEDED`: B no tiene turno bajo ninguna huella, el GraphRun cierra con
  `PLAN_FINGERPRINT_CHANGED`, y el archivo del plan es el que dejó el gancho, sin cambios del GraphRun.
  · rojo visto: sí (GM-09 y GM-44, etapa 5a)
- **GE-E24** — Con un gancho que reescribe el plan, cambiando solo una unidad sin dependencias C,
  después del paso 7b y antes de que el motor lea el plan: o no hay Execution, o la Execution de C
  queda `REJECTED PLAN_CHANGED` sin `entrega.json`. En los dos casos el Host no recibe la invocación y
  el GraphRun cierra con `PLAN_FINGERPRINT_CHANGED`. El escenario corre las dos variantes del gancho:
  la reescritura sin reconciliar el flujo (la admisión al pedir rechaza: no hay Execution) y la de
  quien planifica, con el flujo reconciliado (la admisión al pedir la admite bajo la huella nueva, y
  es `huella_esperada` la que la detiene al entregar). Solo la segunda distingue GM-11 (enmienda del
  14-10-2026, 27.1 B). · rojo visto: sí (GM-10, etapa 3; GM-11, etapa 8)
- **GE-E25** — `motor.ejecutar` con `huella_esperada` igual a la del plan corre como siempre; con otra,
  la Execution termina `REJECTED PLAN_CHANGED` sin `entrega.json`; sin el parámetro, la suite 72
  entera sigue verde. · rojo visto: sí (contra el código sin el cambio y GM-10, etapa 3)
- **GE-E26** — Con un gancho que reescribe el plan con el mismo contenido, otra indentación y otro orden
  de claves, el GraphRun sigue y termina `SUCCEEDED`. · rojo visto: sí (mutación propia, etapa 5a)
- **GE-E27** — Con un gancho que deja el plan cortado a la mitad después de A, el GraphRun cierra con
  `GRAPH_PLAN_UNREADABLE` sin despachar B. · rojo visto: sí (mutación propia, etapa 5a)

### Exclusividad, idempotencia y Executions manuales

- **GE-E28** — Dos procesos del sistema operativo lanzan `--grafo` sobre la misma TaskKey, con un punto
  de encuentro antes de tomar el candado: queda exactamente un GraphRun; el otro sale con 2,
  `GRAPH_ALREADY_ACTIVE`, sin carpeta `grf_…`; cada unidad tiene exactamente una Execution, y el Host
  recibe tantas invocaciones como unidades. · rojo visto: sí (GM-12 y GM-13, etapa 5b)
- **GE-E29** — Lo mismo, veinte veces, sin punto de encuentro: cada vez, a lo sumo un GraphRun sin
  terminal en todo momento, una Execution por unidad, y un turno por clave. · rojo visto: sí (GM-12, etapa 5b)
- **GE-E30** — Con un `ejecutar --unidad b` corriendo en otro proceso (candado de vida tomado) cuando el
  GraphRun llega a B: el GraphRun no crea turno para B, cierra con `TASK_EXECUTION_OPEN` y el
  `executionId` de la manual, y la manual termina con su propio resultado, sin `cancelacion.json`.
  · rojo visto: sí (GM-14 y mutación propia de 7c, etapa 5b)
- **GE-E31** — Con una Execution manual `RUNNING` de otra unidad de la misma TaskKey, el GraphRun cierra
  con `TASK_EXECUTION_OPEN` sin ninguna marca de despacho. · rojo visto: sí (GM-14, etapa 5b)
- **GE-E32** — Con un gancho, después de la marca de despacho de B y antes del motor, que corre un
  `ejecutar --unidad b` completo en otro proceso: B tiene exactamente una Execution, la de la manual; el
  `executionId` de la marca del GraphRun no lo nombra ningún turno; y el GraphRun sigue con C si la
  manual quedó `SUCCEEDED`, o cierra con `TASK_EXECUTION_OPEN` si sigue abierta. · rojo visto: sí (GM-16, etapa 5b)
- **GE-E33** — Con una `REQUESTED` sin motor en la TaskKey (R2), el GraphRun cierra con
  `TASK_EXECUTION_OPEN`, su `detail` trae `ejecutar <KEY> --cancelar <exe>`, y la `REQUESTED` sigue
  `REQUESTED`. · rojo visto: sí (GM-14, etapa 5b)
- **GE-E34** — Con una Execution de la TaskKey cuyo `result.json` no valida, el GraphRun cierra con
  `TASK_EXECUTION_OPEN` y `executionStatus: ILEGIBLE`. · rojo visto: sí (GM-14, etapa 5b)
- **GE-E35** — Con una Execution `RUNNING` de **otra** TaskKey del mismo proyecto, el GraphRun corre y
  termina `SUCCEEDED`. · rojo visto: sí (GM-15, etapa 5b)
- **GE-E71** — **Carrera residual con Execution manual de otra WorkUnit** (§15.4). Plan con `b` y `x`
  independientes (orden `b`, `x`), en un proyecto en git como los de la suite 72. En el gancho
  posterior a la marca de despacho de B —ya superado el chequeo 7d—, otro proceso del sistema
  operativo corre `ejecutar <KEY> --unidad x` con un Host falso que duerme, y el gancho vuelve cuando X
  tiene `entrega.json`. El conductor sigue y despacha B. Entonces: los intervalos de B y de X en la
  bitácora del Host se solapan (las dos estuvieron `RUNNING` a la vez); la única marca de despacho que
  existe antes del `result.json` de B es la `001`, que nombra a B, y ninguna marca nombra el
  `executionId` de X; X no tiene `cancelacion.json` y no termina `REJECTED`; la clave de B y la de X
  tienen un turno cada una. Sobre la evidencia: ninguna de las dos atribuye a su Execution cambios de
  la otra; toda evidencia cuya Execution, al cerrar, detecta a la otra por la regla de Task 4
  (`registro.otras_entregadas`) queda `CHANGES_UNATTRIBUTABLE` con `evidence.changes.files: []`, aunque
  B quede `SUCCEEDED`; el escenario no exige que las dos evidencias terminen en
  `CHANGES_UNATTRIBUTABLE`, porque Task 4 no garantiza esa simetría (§15.4); y en ningún caso una
  Execution recibe una atribución de archivos que no pueda sostener. Después del terminal de B, dos
  variantes, elegidas en el gancho posterior al retorno del motor: **(i)** con X todavía `RUNNING`, el GraphRun cierra con
  `TASK_EXECUTION_OPEN` nombrando a X, sin marca de despacho para `x`, y X termina después con su propio
  resultado; **(ii)** dejando que X termine `SUCCEEDED` antes de seguir, el nodo `x` queda `SATISFIED`
  con `dispatched: false`, el GraphRun termina `SUCCEEDED` y el Host recibe dos invocaciones en total,
  una por unidad. · rojo visto: sí (GM-45, etapa 5b)

### Recuperación: las ventanas de corte

Cada corte es un proceso hijo que corre el conductor y muere con `os._exit` en un gancho; después se
corre otro `--grafo` (o `--cancelar grf_…`) en un proceso nuevo.

- **GE-E36** — **G1.** Corte después de `inicio.json` y antes del primer despacho. El `--grafo`
  siguiente deja el GraphRun cortado `FAILED` con `GRAPH_INTERRUPTED`, crea otro, y ese termina
  `SUCCEEDED` con una Execution por unidad. · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E37** — **G2.** Corte después de la marca de despacho de A y antes del motor. Ningún turno nombra
  el `executionId` de esa marca; el GraphRun siguiente despacha A con otro id, una sola vez, y el Host
  recibe una invocación por unidad en total. · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E38** — **G3a.** Corte en el gancho `antes_de_reservar` del motor, durante el despacho de A. Queda
  una carpeta `exe_…` sin turno; A sigue sin turno; el GraphRun siguiente despacha A una sola vez y
  termina `SUCCEEDED`. · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E39** — **G3b y G4.** Corte en el gancho `antes_de_entregar` del motor, durante A. A queda
  `REQUESTED` sin motor. El `--grafo` siguiente cierra el GraphRun cortado `FAILED`
  `GRAPH_INTERRUPTED`, y el nuevo cierra con `TASK_EXECUTION_OPEN` nombrando a A, sin cancelarla ni
  entregarla. Después de `--cancelar <exe de A>`, otro `--grafo` cierra con `WORK_UNIT_NOT_SUCCEEDED`
  (A está `CANCELLED`); después de `ejecutar --unidad a`, otro `--grafo` termina `SUCCEEDED`.
  · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E40** — **G5.** El proceso del conductor se mata mientras el Host falso de B duerme. El `--grafo`
  siguiente deja B `FAILED HOST_INTERRUPTED` por la recuperación de Task 4, cierra el GraphRun cortado
  con `GRAPH_INTERRUPTED`, y el nuevo cierra con `WORK_UNIT_NOT_SUCCEEDED` para B sin despachar nada: el
  Host no recibe ninguna invocación nueva. · rojo visto: sí (contra el código sin el cambio y GM-04, etapa 5b)
- **GE-E41** — **G6.** Corte en el gancho posterior al retorno del motor, con B ya `SUCCEEDED`. El
  GraphRun siguiente adopta B, despacha solo C, y el Host recibe tres invocaciones en total.
  · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E42** — **G7.** Corte en el gancho anterior al terminal, con las tres `SUCCEEDED`. El `--grafo`
  siguiente cierra el GraphRun cortado `SUCCEEDED`, no `GRAPH_INTERRUPTED`, y el nuevo termina
  `SUCCEEDED` sin despachos. · rojo visto: sí (contra el código sin el cambio y GM-17, etapa 5b)
- **GE-E43** — Con un conductor vivo, detenido en un gancho, otro `--grafo` sale con
  `GRAPH_ALREADY_ACTIVE` y un `--cancelar grf_…` escribe la marca y no el terminal: el GraphRun vivo no
  tiene `result.json` hasta que su conductor sigue. · rojo visto: sí (contra el código sin el cambio, GM-12 y GM-18, etapa 5b)
- **GE-E44** — Un `KeyboardInterrupt` levantado en el gancho posterior al retorno del motor, con A
  `SUCCEEDED`, deja el GraphRun `FAILED` con `GRAPH_INTERRUPTED` y sin despacho de B. Un Host falso con
  `senal: true`, que muere como un Host cortado desde afuera (sale con 143), deja B `FAILED
  HOST_INTERRUPTED`, y el GraphRun cierra con `WORK_UNIT_NOT_SUCCEEDED` sin despachar C.
  · rojo visto: sí (GM-19, etapa 5b)
- **GE-E45** — Con `registro.crear` forzado a fallar con `OSError` antes del turno, el GraphRun cierra
  con `DISPATCH_FAILED` y `executionId` que ningún turno nombra. Con un error del comando forzado después
  de publicar la Execution, cierra con `DISPATCH_FAILED`, el `executionId` de esa Execution y su estado
  derivado. · rojo visto: sí (GM-16 y GM-20, etapa 5b)

### Cancelación

- **GE-E46** — Con el conductor detenido en el gancho posterior a A, `--cancelar grf_…` desde otro
  proceso escribe `cancelacion.json`; al seguir, el conductor no despacha B y cierra `CANCELLED`, con
  `cancelRequested: true`; A queda idéntica. · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E47** — Con B `RUNNING` y el Host falso durmiendo, `--cancelar grf_…` deja B `CANCELLED` por el
  camino de Task 4, con el árbol del Host terminado; C no tiene turno; el GraphRun queda `CANCELLED`; y
  el comando vuelve con el terminal ya escrito. · rojo visto: sí (contra el código sin el cambio y GM-22, etapa 5b)
- **GE-E48** — La ventana entre cancelar y despachar (§17.2), en tres cláusulas (27.1 J y L). **a)** Con el
  conductor detenido entre la marca de despacho de B y su lectura de la cancelación (7e a 7f), y
  `--cancelar grf_…` completo en ese hueco: B no tiene turno ni Host, y el GraphRun cierra `CANCELLED`.
  **b)** Con el conductor detenido después de esa lectura y antes del motor (7f a 7g), soltado apenas
  existe la marca del grafo (así el turno de B aparece mucho antes de que venza la ventana del
  cancelador), y un Host de B que sobrevive a varios tramos de un segundo después de que el cancelador
  le pide cancelar (por ejemplo, uno que duerme 60 s): el cancelador le pide cancelar a B, y B queda
  `CANCELLED` sin `entrega.json`, o con el árbol del Host terminado; el GraphRun cierra `CANCELLED`. **c)** En el plan
  A→B, con el conductor detenido en el mismo punto que en b) hasta que el cancelador completó su primera
  vuelta sin encontrar turno de B, un Host de B que termina de inmediato y un cancelador cuyo intervalo
  supera lo que tardan B y el terminal (por ejemplo, 5 s): B queda `SUCCEEDED` con una sola invocación
  del Host y sin `cancelacion.json` propio; el GraphRun cierra `SUCCEEDED` con `cancelRequested: true`; el
  `cancelacion.json` del grafo existe; el cancelador no le pidió cancelar a ninguna Execution
  (`canceladas: []`) y vuelve con el terminal ya escrito. En las tres, ninguna Execution propia del
  GraphRun queda abierta después de su `result.json`. **El rango intermedio no tiene resultado único y
  este escenario no lo asevera:** un Host de B que el cancelador encuentra abierto y que sale en el mismo
  tramo en que se persiste el pedido puede dejar a B `CANCELLED` o con su propio resultado, y al GraphRun
  `CANCELLED` o `SUCCEEDED` con `cancelRequested: true` (§17.3, observación 2; 27.1 L). **Tampoco asevera** los
  otros límites de §17.4: un conductor retenido entre 7f y el turno de B más que la ventana de 60 s del
  cancelador (B corre entera, con su propio resultado y sin `cancelacion.json` propio; el GraphRun
  cierra por la regla de cierre: en A→B con B `SUCCEEDED`, `SUCCEEDED` con `cancelRequested: true`, y
  `CANCELLED` en 7a si quedan nodos), un cancelador cortado antes de
  pedir, un pedido que llega con el Host ya salido, ni las excepciones a «ninguna Execution propia
  abierta» (§17.3, observación 3) del límite 8 (27.1 M).
  · rojo visto: sí (GM-21, GM-22 y GM-23, etapa 5b y etapa 10)
- **GE-E49** — Con las tres `SUCCEEDED` y el conductor detenido antes del terminal, `--cancelar grf_…`
  deja el GraphRun `SUCCEEDED` con `cancelRequested: true`. · rojo visto: sí (GM-23, etapa 5b)
- **GE-E50** — `--cancelar grf_…` sobre un GraphRun que ya es terminal cuando el comando lo lee no
  escribe ningún archivo (un terminal escrito después de esa lectura es el residuo de §17.3, 27.1 K, y
  este escenario no lo cubre). Dos `--cancelar`
  sobre uno `ACTIVE` dejan un solo `cancelacion.json`, y el segundo sale con 0. · rojo visto: sí (GM-25, etapa 5b)
- **GE-E51** — Con el conductor muerto y su Execution de B `REQUESTED` sin motor, `--cancelar grf_…`
  toma el candado, deja B `CANCELLED` y el GraphRun `CANCELLED`. · rojo visto: sí (contra el código sin el cambio, etapa 5b)
- **GE-E52** — Con una Execution manual abierta de la misma TaskKey, `--cancelar grf_…` no escribe su
  `cancelacion.json`, y la manual termina con su propio resultado. · rojo visto: sí (GM-22 y GM-24, etapa 5b)

### N1

- **GE-E53** — Dos procesos: A detenido entre `os.open(O_EXCL)` y `_bloquear` de `Vida`; B corre
  `motor.recuperar` sobre la misma tarea, con su sonda detenida mientras tiene el candado. A publica su
  Execution, y B nunca sondea la carpeta de A. Con F1 revertido, A sale con un error del comando: es el
  rojo. · rojo visto: sí (GM-26, etapa 1)
- **GE-E54** — `limpiar_temporales` no sondea ni borra un temporal de menos de diez minutos en una
  carpeta con el candado libre, y sí borra uno envejecido a once minutos. Una carpeta sin temporales
  viejos no se sondea. · rojo visto: sí (GM-27, etapa 1)
- **GE-E55** — Un `--cancelar exe_…` sobre una `REQUESTED` sin motor, con un `recuperar` de otro proceso
  en el instante entre su temporal y su `os.link`, termina sin excepción y deja la Execution
  `CANCELLED`. · rojo visto: sí (GM-27, etapa 1)

### R5

- **GE-E56** — Con el adaptador en plataforma `win32`, una unidad B con `tests.run` y un agente con
  `Bash` en su `tools:`: B queda `REJECTED CAPABILITY_UNAVAILABLE`, sin `entrega.json`; el Host no
  recibe la invocación de B; el `detail` nombra `Bash` y la plataforma; el GraphRun cierra con
  `WORK_UNIT_NOT_SUCCEEDED` y `executionCode: CAPABILITY_UNAVAILABLE`; A, ya `SUCCEEDED`, queda idéntica.
  · rojo visto: sí (GM-28, etapa 2)
- **GE-E57** — La misma unidad con el adaptador en plataforma `linux` se admite y se entrega con `Bash`
  en `--tools`. · rojo visto: sí (GM-29, etapa 2)
- **GE-E58** — Un plan sin `tests.run`, con el adaptador en `win32`, termina `SUCCEEDED`.
  · rojo visto: sí (GM-30, etapa 2)
- **GE-E59** — ME-E42 sigue verde: un adaptador que devuelve `CAPABILITY_UNAVAILABLE` después de la
  entrega da `ENGINE_FAILURE`. Y con un registro armado donde el último turno de A es un `FAILED
  CAPABILITY_UNAVAILABLE` válido por contrato, el GraphRun cierra con `WORK_UNIT_NOT_SUCCEEDED` sin
  despachar. · rojo visto: sí (GM-30, etapa 2; GM-40, etapa 5a)

### Contrato, persistencia, CLI y documentos

- **GE-E60** — El `result.json` de cada GraphRun de esta suite valida contra
  `graph-run-result.schema.json` y sus coherencias; cada marca tiene exactamente sus claves;
  `inicio.json` trae los `workUnitId` y `dependencies` del plan; las marcas de despacho son
  consecutivas desde `001`; y cada `error.code` es uno de los nueve. · rojo visto: sí (S-1 propia, etapas 5a y 8; GM-33, etapa 5a)
- **GE-E61** — Después de un GraphRun, todo archivo nuevo fuera del registro de Executions está bajo
  `.claude/ejecuciones/<KEY>/grafos/`; ninguna marca se pudo escribir dos veces; no hay un archivo de
  estado; y en `bin/ejecucion/` solo `registro.py` escribe en disco (ME-E46 con `grafo.py` adentro).
  · rojo visto: sí (GM-34, etapa 4; GM-35 vía ME-E46, etapa 8)
- **GE-E62** — Con `grafos/` lleno, `registro.carpetas`, `residuos`, `barrer`, `limpiar_temporales` y
  `otras_entregadas` no lo nombran ni lo tocan, y la evidencia de una Execution que corrió durante un
  GraphRun no lista nada de `grafos/`. · rojo visto: sí (GM-36, etapa 4)
- **GE-E63** — `--grafo` sale con 0 solo con `SUCCEEDED`; con `--json` imprime el resultado o el rechazo
  al arrancar; `--grafo --unidad b` es un error del comando; `--cancelar` con un id que no es `exe_…` ni
  `grf_…` válido es un error del comando; `--estado`, `--recuperar` y `--cancelar exe_…` dan la misma
  salida que en 0.32.0. · rojo visto: sí (GM-42 y contra el código sin el cambio, etapa 6A)
- **GE-E64** — ME-E47 y E-41 siguen verdes con `grafo.py`: sin módulos de concurrencia, sin SDK de
  modelos ni LangGraph, sin `subprocess`, sin `proceso.lanzar`, y trece subcomandos. EX-E50 sigue verde.
  · rojo visto: sí (GM-39 y GM-35, etapas 5a y 8)
- **GE-E65** — `contrato.py`, `execution-request.schema.json`, `execution-result.schema.json` y
  ADR-0013, ADR-0014 y ADR-0015 tienen la misma huella que en `e33b41b`. · rojo visto: sí (tres mutaciones, etapa 7)
- **GE-E66** — En un proyecto instalado en `%TEMP%`, `grafo.py` y `graph-run-result.schema.json` están
  instalados, y `ejecutar --grafo` lleva un plan de dos unidades a `SUCCEEDED` con el Host falso.
  · rojo visto: sí (sin `grafo.py` y sin el schema, etapa 6A)
- **GE-E67** — MC tiene la ficha de GraphRun en el contexto Execution y la fila «run / corrida»
  enmendada; E-09 de t64 sigue verde; `docs/adr/0016-la-ejecucion-de-un-grafo.md` existe y nombra la
  revisión de ADR-0015. · rojo visto: sí (mutaciones propias, etapa 7)
- **GE-E68** — Ningún `result.json` de GraphRun tiene claves `evidence`, `files`, `output` ni
  `artifact`, y su `detail` no contiene el texto que el Host falso puso en el `artifact` ni en el
  `detail` de una Execution. · rojo visto: sí (GM-33, etapa 5a)
- **GE-E69** — Con `--pedido-por ana`, cada request que despacha el GraphRun tiene `requestedBy: ana`, y
  también `inicio.json`. · rojo visto: sí (GM-37, etapas 5a y 6A)
- **GE-E70** — `--grafo --estado` con un GraphRun huérfano lo muestra `ACTIVE`, con el comando para
  cerrarlo, y después de correrlo no cambió ningún archivo del proyecto. Con un GraphRun cuyo
  `inicio.json` no valida y otro cuyo `result.json` no valida (enmienda del 14-10-2026, 27.1 G): los
  muestra `ILEGIBLE`, con su motivo y sin comandos; `--cancelar grf_…` sobre cada uno es un error del
  comando que no escribe nada; y un GraphRun nuevo de la tarea termina `SUCCEEDED` sin cambiar ningún
  archivo de los dos. · rojo visto: sí (GM-38, etapas 5b y 6A; mutaciones propias del ILEGIBLE, etapa 7)

---

## 33. Red mutations

Cada mutación se aplica sobre una copia del código, en `%TEMP%`, nunca en el árbol versionado; el test
del escenario tiene que ponerse rojo, y verde al revertir. El rojo visto de cada escenario se registra
en esta spec cuando pase (`no consta` → `sí`).

| GM | Mutación | Se pone rojo |
|---|---|---|
| GM-01 | El conductor despacha en el orden de `workUnits`, no en el de `orden_de_ejecucion` | GE-E02, GE-E04, GE-E10 |
| GM-02 | La elegibilidad pide «alguna» dependencia satisfecha | GE-E03 |
| GM-03 | El conductor no mira el registro antes de despachar | GE-E05, GE-E06, GE-E07 |
| GM-04 | Una unidad `FAILED` bajo F es elegible | GE-E20, GE-E40 |
| GM-05 | La clave se calcula sin la huella, o con la del plan actual | GE-E21, GE-E22 |
| GM-06 | Sin validación de dependencias repetidas, o sin `orden_de_ejecucion` | GE-E08 |
| GM-07 | El GraphRun se crea antes de validar la estructura | GE-E08, GE-E09 |
| GM-08 | Después de un nodo no exitoso, sigue con el siguiente | GE-E18, GE-E11 |
| GM-09 | El conductor no relee la huella en 7b | GE-E23 |
| GM-10 | `motor.ejecutar` ignora `huella_esperada` | GE-E24, GE-E25 |
| GM-11 | En 7g, el conductor pasa como `huella_esperada` la huella del plan que **relee al llamar al motor**, después del gancho `despues_del_despacho`, en vez de F de `inicio.json` (enmienda del 14-10-2026, 27.1 B) | GE-E24, variante con el flujo reconciliado: el Host recibe la invocación de C y C no queda `REJECTED` |
| GM-12 | El candado de la tarea se abre con `O_EXCL` y se borra al soltar | GE-E28, GE-E29, GE-E43 |
| GM-13 | `inicio.json` se escribe antes de tomar el candado | GE-E28 |
| GM-14 | Sin el chequeo 7d | GE-E31, GE-E33, GE-E34 |
| GM-15 | El chequeo 7d mira todo el proyecto | GE-E35 |
| GM-16 | En 7h, ningún turno que nombre a `exe` se lee como «sin Execution» sin mirar el registro | GE-E32, GE-E45 |
| GM-17 | El cierre de un huérfano escribe `GRAPH_INTERRUPTED` aunque todo esté satisfecho | GE-E42 |
| GM-18 | Un `--grafo` cierra un GraphRun sin tener el candado | GE-E43 |
| GM-19 | El conductor absorbe el `KeyboardInterrupt` y sigue | GE-E44 |
| GM-20 | Un error del comando cierra sin `executionId` | GE-E45 |
| GM-21 | Sin el chequeo 7f | GE-E48 |
| GM-22 | El cancelador no mira los despachos después de escribir su marca | GE-E48 |
| GM-23 | La cancelación tardía gana sobre todo `SUCCEEDED` | GE-E49, GE-E48 c) (27.1 J) |
| GM-24 | `--cancelar grf_…` cancela toda Execution abierta de la tarea | GE-E52 |
| GM-25 | `--cancelar grf_…` sobre un terminal escribe la marca | GE-E50 |
| GM-26 | `barrer` sondea antes de la edad (se revierte F1) | GE-E53 |
| GM-27 | `limpiar_temporales` borra temporales nuevos (se revierte F2′) | GE-E54, GE-E55 |
| GM-28 | `provee` ignora la plataforma | GE-E56 |
| GM-29 | `provee` rechaza `Bash` en toda plataforma | GE-E57 |
| GM-30 | `provee` rechaza toda unidad en `win32` | GE-E58 |
| GM-31 | El conductor llama a `adaptador.provee` para elegir | GE-E17 |
| GM-32 | El conductor guarda en caché la compuerta | GE-E12 |
| GM-33 | `result.json` copia la evidencia de cada Execution | GE-E68 |
| GM-34 | `result.json` se reescribe con `os.replace` | GE-E60, GE-E61 |
| GM-35 | `grafo.py` escribe un archivo directamente | GE-E61 |
| GM-36 | `grafos/` se crea con un nombre `exe_…` | GE-E62 |
| GM-37 | `requestedBy` del despacho es «graph» | GE-E69 |
| GM-38 | `--grafo --estado` cierra huérfanos | GE-E70 |
| GM-39 | `grafo.py` importa `threading` | GE-E64 |
| GM-40 | Un `FAILED CAPABILITY_UNAVAILABLE` se toma como satisfecho | GE-E59 |
| GM-41 | Una Execution cancelada sola cierra el grafo `CANCELLED` | GE-E19 |
| GM-42 | `--grafo` sale con 0 con `FAILED` | GE-E63, GE-E18 |
| GM-43 | El conductor lee `detail` para clasificar | GE-E17 |
| GM-44 | El GraphRun escribe el plan | GE-E23 |
| GM-45 | Después de despachar B, el conductor ignora su estado y despacha otra Execution propia mientras B sigue abierta (escribe la marca del nodo siguiente y lo despacha sin esperar el retorno del motor por B) | GE-E71, GE-E02 |

No hay una mutación que intente prohibir la Execution manual de la carrera residual: su convivencia con
la propia es comportamiento permitido (GE-I31).

GE-E65, GE-E66 y GE-E67 se ponen rojos sacando el archivo o el texto que piden.

**Dos mutaciones de GM-11 que no se aplican, porque son equivalentes** (enmienda del 14-10-2026, 27.1 B):
comparar `huella_esperada` contra la huella del plan de hoy en `al_entregar`, porque esa comparación
vive dentro de la rama donde la condición 4 ya exige que la huella del plan de hoy sea la de la request
(`admision.py:268`, `:273-276`); y pasar en 7g la huella leída en 7b, porque 7b ya cerró si no era F
(`grafo.py:309`, `:315`).

---

## 34. Construction order

#### GD-27. Primero lo que sostiene a todo lo demás

1. **N1 en `registro.py`** (F1, F2′), con GE-E53, GE-E54 y GE-E55, y la suite 72 verde: la carrera de
   ME-E18 corre sobre esto.
2. **R5 en `host_claude_code.py`**, con GE-E56 a GE-E59, y la enmienda de T4 MD-18′ en una nota de
   esta spec: escrita en GD-21 (enmienda del 14-10-2026, 27.1 E).
3. **La admisión:** `leer_plan` público y `huella_esperada` en `al_entregar`, con GE-E25.
4. **El motor:** `execution_id` y `huella_esperada`.
5. **El registro del GraphRun en `registro.py`:** rutas, candado de la tarea, marcas.
6. **El Host falso:** guion por unidad (`por_unidad`: un guion distinto por `workUnitId`, leído del
   prompt) y una bitácora con **una entrada por invocación**, con inicio y fin: la entrada se escribe
   al empezar, con `fin: null`, y se completa al terminar con otra línea del mismo `id`; quien lee la
   bitácora toma la última línea de cada `id`. Una invocación que muere desde afuera queda con
   `fin: null` y cuenta igual (GE-E40, GE-E47); una que muere por su guion (`senal`) anota su `fin`
   antes de morir (GE-E44). Sin tocar los modos que ya usa la suite 72 (enmienda del 14-10-2026,
   27.1 C).
7. **`grafo.py`:** conductor, cierre, cancelación, estado, con sus ganchos.
8. **`graph-run-result.schema.json`**, y en el mismo paso, porque sin ellos t64 y t65 quedan rojos
   desde que el schema entra al árbol: la ficha de `GraphRun` en MC (§28) y las adaptaciones de t64
   E-05, t64 E-05 (S4) y t65 EX-E45 (§27). En la construcción en curso el schema ya entró, así que van
   en la etapa siguiente del builder, la 6 (enmienda del 14-10-2026, 27.1 A).
9. **`dev-harness.py`:** `--grafo`, `--grafo --estado`, `--cancelar grf_…`.
10. **`tests/casos/73_ejecucion_de_grafo.py`** y **`73-ejecucion-de-grafo-instalador.ps1`**, cada test
    con su id.
11. **Las adaptaciones de §27** en el caso 63, con su comentario.
12. **MC y ADR-0016** (§28, §29): el resto de §28, sin la ficha de `GraphRun`, que ya entró en el
    paso 8.
13. **El rojo visto** de cada escenario, con GM-01 a GM-45, registrado en esta spec.
14. **La compuerta entera** en verde: `.\tests\Invoke-Tests.ps1`.
15. **FH:** salen N1, R5 y la mitad del ítem 14; entran GP-02, GP-05, GP-07 y GP-08; GP-03 y GP-04
    van a `PENDIENTES-I.md`.

**Lo que no se toca:** `contrato.py`; los dos schemas de ejecución; la regla de quince condiciones;
`bin/orquestacion/`, `bin/flujo/`, `bin/estado_de_tarea/`; los hooks y `tool_policy.py`; los agentes y
las skills; `install.ps1` y `manifest.json`; ADR-0013, ADR-0014 y ADR-0015; `VERSION`,
`CHANGELOG.md` y `UPGRADE.md`.

**Quién construye** lo decide la fábrica (GP-01). Quien construya no verifica: verifica
`harness-spec-refuter` (ADR-0006).

#### GD-28. La estrategia de tests

- **Todo determinista.** Host falso, procesos reales del sistema operativo con puntos de encuentro en
  disco para las carreras (como ME-E18), y cortes con `os._exit` en ganchos para las ventanas.
- **Sin hilos en los tests de carreras:** procesos, como la suite 72.
- **La plataforma se inyecta** en el adaptador, así R5 se prueba en las dos ramas en cualquier máquina.
- **Cero escenarios de lectura.** La observación de R5 contra el Host real ya está hecha (T4 §34.2, E8);
  la que haga falta para GP-02 es de esa Task.
- **Dos motores, un código de salida:** la compuerta corre los casos Python por `tests/correr.py` y los
  `.ps1` del instalador, como hoy.

---

## 35. Gate

### 35.1 La revisión de esta spec

| Condición | Estado |
|---|---|
| Las 35 secciones, sin vacías | Sí |
| Las 29 decisiones obligatorias resueltas, con evidencia | Sí, GD-01 a GD-29 |
| Cada conflicto del orquestador decidido, con quién dijo qué | Sí, GC-01 a GC-24 |
| Decisión arquitectónica con dos opciones igual de válidas, abierta | **Ninguna** |
| Cada invariante con al menos un escenario | Sí, GE-I01 a GE-I31, sobre GE-E01 a GE-E71 |
| Mutaciones de rojo | GM-01 a GM-45 |
| Escenarios con `· verificación: lectura` | Cero |
| Contradicción GD-06 / GE-I11 contra la carrera residual de GD-15 | Corregida el 13-10-2026: serialidad propia del GraphRun, sin exclusión global de la TaskKey (GD-06, GC-12, §14.2, GD-15, §15.4, GE-I11, GE-I31, GE-E71, GM-45). Task 3 y Task 4 sin cambios |

**Veredicto de WU10:** `READY FOR TASK 5 SPEC REVIEW`. **No es** una aprobación para construir: esa la
da una persona, después de revisar, y se registra en el encabezado con su nombre y la fecha.

### 35.2 El cierre del cambio, cuando se construya

El cambio cierra cuando:

- `harness-spec-refuter`, que no construyó, dictamina los 71 escenarios: todos `sostenido`. Ninguno es
  `leído`;
- ningún escenario de Task 3 ni de Task 4 queda `contradicho`, salvo las adaptaciones de §27 con su
  decisión;
- `.\tests\Invoke-Tests.ps1` sale con 0;
- `contrato.py`, los dos schemas de ejecución, ADR-0013, ADR-0014 y ADR-0015 tienen la huella de
  `e33b41b` (GE-E65);
- nada de la lista «Lo que no se toca» de §34 cambió.

Un `verificacion.md` que exista no cierra nada por sí solo.
