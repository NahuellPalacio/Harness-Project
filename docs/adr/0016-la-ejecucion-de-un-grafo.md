---
estado: aceptada
creado: 2026-10-14
---

# ADR-0016 — La ejecución de un grafo

## Contexto

ADR-0015 dejó un motor que corre una WorkUnit por invocación de `ejecutar`, y dejó el resto para la
Task siguiente: elegir cuál sigue, en qué orden y cuántas a la vez es scheduling, y es de Task 5. Hasta
ahora, llevar un plan entero a un terminal era que una persona corriera `ejecutar --unidad` por cada
unidad, mirando a mano las dependencias.

El relevamiento y el diseño están en `docs/cambios/graph-execution/spec.md` (Task 5), con 29
decisiones `GD-nn` y 24 conflictos decididos `GC-nn`. Los que pesan en estas decisiones:

- **«Execution» ya nombra un intento de una WorkUnit**: llamar «GraphExecution» al recorrido del plan
  haría que la palabra nombre dos cosas en el mismo contexto (GD-02);
- **la request no puede llevar un `graphRunId`**: `execution-request/1.0` tiene
  `additionalProperties: false`, y agregarlo cambiaría el contrato de Task 3 (GD-03);
- **un GraphRun no puede tener Executions «suyas» en exclusiva**: la admisión no deja repetir una clave
  que ya está `SUCCEEDED`, así que una Execution que pidió una persona, bajo la misma huella, cuenta
  para cualquier GraphRun de ese plan;
- **una sonda del candado puede caer entre `O_EXCL` y el candado de vida** de una Execution que se está
  creando (N1);
- **`Bash` no existe en la sesión del Host en Windows**, y una unidad con `tests.run` se admitía y su
  agente corría sin poder correr los tests (R5).

## Decisión

### 1. GraphRun es un agregado de Execution, no un contexto nuevo

`GraphRun` es el segundo Aggregate Root del contexto Execution: un intento de llevar todas las
WorkUnits de un plan, atado a una huella, a un terminal. Su identidad es `grf_` más 32 hexadecimales al
azar, y su ciclo, `ACTIVE → SUCCEEDED`, `FAILED` o `CANCELLED`. Orquesta Executions y no las redefine:
cada una sigue siendo un intento de exactamente una WorkUnit, y sale de `motor.ejecutar`, con sus dos
admisiones. El contrato de Task 3 no cambia. Lo nuevo es `graph-run-result/1.0` y un `GraphRunError`
propio, con nueve códigos: un ExecutionError aparece solo como la causa referenciada.

### 2. Serial y fail-fast, en el orden de `orden_de_ejecucion`, en el mismo proceso

Un conductor, un bucle, sin hilos ni procesos nuevos: una Execution propia abierta a la vez, en el
orden de `orden_de_ejecucion`. Una unidad se despacha solo con todas sus dependencias `SUCCEEDED` bajo
la huella, y el GraphRun se detiene en la primera que no lo queda. La serialidad es de lo que el
GraphRun despacha, no un candado de la TaskKey: antes de cada despacho mira el registro, y si hay una
Execution abierta o ilegible que no es suya, cierra con `TASK_EXECUTION_OPEN`.

### 3. Sin reintento automático y sin reanudación, también entre GraphRuns

Una unidad con un turno bajo la huella no se despacha de nuevo, y cada una se despacha a lo sumo una
vez por GraphRun. Reintentar una unidad que terminó mal lo pide una persona con `ejecutar --unidad`. Un
GraphRun huérfano no se reabre: lo cierra quien toma el candado de la tarea, y seguir es otro GraphRun,
que adopta como satisfecho lo que ya está `SUCCEEDED`.

### 4. Atado a una huella, y el motor recibe la huella esperada

El GraphRun queda atado a la huella del plan, `planFingerprint`, desde su `inicio.json`: `plan_version`
no identifica un plan, porque `plan --propuesta` vuelve a la 1. Antes de cada despacho vuelve a leer el
plan, y si la huella cambió cierra con `PLAN_FINGERPRINT_CHANGED`. `motor.ejecutar` recibe, opcionales,
un `execution_id` preasignado y la `huella_esperada`, y los lleva hasta la admisión, que rechaza con
`PLAN_CHANGED` en su lugar de siempre. Sin ellos, el motor es el de Task 4. El vínculo va del GraphRun a
la Execution, por su marca de despacho, y nunca al revés.

### 5. Cuatro marcas de una sola escritura y un candado estable por tarea

Bajo `.claude/ejecuciones/<TaskKey>/grafos/<graphRunId>/`, el GraphRun deja `inicio.json`,
`despachos/<NNN>.json`, `cancelacion.json` y `result.json`, cada una escrita una sola vez. No hay un
archivo de estado: el de cada nodo se deriva del último turno de su clave, y el del GraphRun, de qué
marcas existen. Ser el conductor es tener tomado `grafos/vivo.lock`, un archivo estable que no se borra:
cuenta si está tomado, no si existe. Toda escritura la hace `registro.py`, y las funciones de Task 4 no
ven esa carpeta.

### 6. Ciego a capacidades, y R5 se resuelve en el Host Adapter

El GraphRun no mira capacidades: elige unidades elegibles, y la condición 13 de la admisión decide las
admisibles, sin una segunda fuente de verdad. R5 se arregla donde vive: `provee` conoce la plataforma, y
en `win32` `Bash` no se ofrece. Una unidad con `tests.run` sale `REJECTED CAPABILITY_UNAVAILABLE` antes
de `entrega.json`, sin Host y sin modelo. Se cambia un éxito falso por un rechazo honesto, y el mapeo de
`tests.run` a otra herramienta queda para una Task con su lectura del Host real.

### 7. N1 se cierra sin candado nuevo

Ninguna sonda de candado toca una carpeta en creación: `barrer` mira la edad antes del candado, y
`limpiar_temporales` solo sondea si hay temporales con más de diez minutos. Una creación tarda
milisegundos, así que su carpeta y sus temporales son nuevos y nadie los mira. Lo único que cuesta es
disco: un temporal nuevo espera hasta la próxima recuperación después del umbral.

## Consecuencias

A favor:

- El contrato de Task 3 no cambia: los dos schemas, `contrato.py`, los veintitrés códigos, la
  precedencia, la clave de idempotencia y `ejecutar --unidad` son los mismos. Task 4 cambia solo en
  aditivo: N1, R5, un lector público del plan y dos parámetros opcionales del motor.
- Cada Execution pasa por la admisión, dos veces: el GraphRun decide qué intentar, y la admisión, si es
  admisible. El flujo, la compuerta normativa y las capacidades no se duplican ni se cachean.
- Nada se reintenta ni se reanuda solo, y la causa de un GraphRun que falla queda a la vista, con el
  comando que sigue.
- No entra una dependencia: LangGraph se evaluó contra estas invariantes y no calza, y la guarda que
  prohíbe importarlo sigue en pie. `ejecutar` sigue con trece subcomandos: `--grafo` es una opción.

En contra, y dicho:

- **En Windows, `tests.run` no se ejecuta por el motor**, hasta que exista un mapeo comprobado.
- **La evidencia sigue degradando con archivos sucios compartidos**: una unidad que reescribe lo que la
  anterior dejó sucio queda `CHANGES_UNATTRIBUTABLE`.
- **Un plan replanificado vuelve a correr todo**: nada se reusa entre huellas.
- **Fail-fast deja sin correr las ramas independientes** de una unidad que falló.
- **Una Execution manual abierta que el GraphRun observa antes de despachar detiene el grafo, y una de
  otra unidad que se publica después de ese chequeo puede convivir con la propia**, con evidencia no
  atribuible. Cerrar esa ventana exige que la admisión de una manual conozca al GraphRun, y eso cambia
  Task 3.
- **Un GraphRun lanza varias sesiones del Host**, en serie, y cada una cuesta: no hay un tope por
  corrida.

## Revisión

**Revisa ADR-0015 en lo que dejaba para Task 5** —el scheduling de su decisión 1—, sin cambiar sus
siete decisiones: la 1 sigue valiendo para `ejecutar --unidad`, y el GraphRun la usa por cada unidad.
ADR-0013, ADR-0014 y ADR-0015 no se editan, porque son historia, y los dos invariantes del punto 4 de
ADR-0013 siguen: la contabilidad no es estado de ejecución, y el estado del Plan se deriva del
contenido del Plan. Este ADR se revisa cuando se agregue paralelismo, reintento automático, seguir con
las ramas independientes, un segundo Host o el mapeo de `tests.run` por plataforma.
