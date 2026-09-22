# Evolutivo del Bloque 3 — `dev-tool-builder` construye tools

**Estado:** especificado · **Fecha:** 2026-09-16

## Qué problema resuelve

El Bloque 3 detecta el hueco de capacidad y lo deriva. Nada más. `capacidades.py` arma un
`capabilityGap` con la capacidad, las unidades que la pidieron, `derivedTo: dev-tool-builder` y
`toolClass: TEMPORARY`, y ahí termina el harness. Quién construye la tool, con qué contrato, con
qué permisos, con qué riesgo y cómo se promueve no existe en ningún lado.

El pedido lo llama evolutivo sobre lo ya construido. De las cuatro piezas que nombra:

| Pieza | Hoy |
|---|---|
| Capability Registry | existe — `bin/orquestacion/capacidades.py`, dos fuentes y un hueco derivado |
| `dev-orchestrator` | existe como `.md` y **nunca se corrió** |
| `dev-tool-builder` | declarado en `reglas/roster.json`, **sin archivo**: es un hueco |
| Tool Registry | **no existe** |

Y la spec del Bloque 3 lo dice en `Qué queda afuera`, literal: *"`dev-tool-builder` construyendo
tools. El núcleo detecta el hueco de capacidad, lo deriva y clasifica la tool pedida como
`TEMPORARY`. Quién la escribe y cómo se promueve es otro cambio."*

Este es ese cambio. No fortalece comportamiento existente: construye la mitad que el Bloque 3
excluyó a propósito. El encuadre importa porque un evolutivo no necesita escenarios nuevos, y esto
sí: todo lo que sigue es superficie que nadie escribió todavía.

## Qué queda afuera

- **Escribir tools de verdad.** Ninguna tool nueva entra en este cambio. Se construye el contrato,
  el registro y las reglas que las gobiernan. Una tool escrita acá para probar el mecanismo sería
  un dato inventado, y un registro sembrado con un ejemplo se lee igual de autoritativo que uno
  real. Es la misma razón por la que las 26 reglas de §7.1 entraron sin clasificar.
- **El sandbox real.** El harness corre en la máquina de quien trabaja; no hay entorno aislado
  donde ejecutar código recién generado. La etapa existe en el pipeline y **se reporta `NOT_RUN`**,
  que es un hueco declarado, no un `PASS`. Construir el aislamiento es otro cambio.
- **La ejecución de una unidad de trabajo.** Sigue siendo del Bloque 4. Una tool registrada es una
  tool disponible, no una tool corriendo.
- **El proceso formal de `PROMOTION_CANDIDATE` a `APPROVED`.** Se declara el estado, la evidencia
  que habilita el salto y quién **no** puede darlo. El circuito de revisión de la organización no
  lo define el harness.
- **Los runtime adapters concretos.** El contrato queda independiente del proveedor; escribir el
  adapter de un runtime puntual es otro cambio, y escribirlo antes fija el contrato contra el
  primer runtime que aparezca.
- **Migrar las capacidades locales a tools.** `repository.read`, `repository.write`,
  `repository.search` y `tests.run` siguen siendo capacidades del runtime declaradas en el roster.
  Convertirlas en tools registradas es una migración con su propio riesgo.
- **`dev-security` como archivo.** `SECURITY_REVIEW_REQUIRED` deriva a un agente que hoy es un
  hueco del roster. El estado se emite igual y el hueco se reporta: derivar a un agente que no
  existe es mejor que autoaprobar.
- **La matriz normativa de §7.1.** Sigue sin clasificar, así que ninguna tool va a citar un
  estándar aplicable en este cambio.

## Las decisiones, y por qué

### El riesgo sale del contrato, no del modelo

Un modelo barato puede escribir una tool que borra una base. La clasificación se deriva de lo que
el contrato declara —side effects, permisos, red, secrets, blast radius— y el tier con el que se
construyó no entra en la cuenta. La alternativa era atar el riesgo a la política de consumo, que es
justamente la confusión que el pedido pide deshacer.

### Dos compuertas, y ninguna cubre a la otra

`consumo.py` ya tiene la compuerta de modelo: `premium` se detiene y pregunta con una alternativa
más barata adentro. La de riesgo es otra pregunta, con otro sujeto y otra respuesta. Se agrega
separada. Aprobar gasto no aprueba peligro, y el presupuesto premium preautorizado no compra
ninguna tool.

### El riesgo declarado no puede ser menor que el derivado

El contrato lleva `riskLevel`, y el núcleo lo deriva por su cuenta. Si el declarado es más bajo, se
rechaza; si es más alto, se respeta. Sin esa asimetría, `riskLevel` es un campo que se completa
para pasar la compuerta.

### Una tool generada nace temporal y nadie la promueve sola

`EXPERIMENTAL` o `TEMPORARY`, nunca `APPROVED`. La promoción pide evidencia completa, y el salto
final no lo da el que construyó. Es la misma regla que sostiene todo el resto del harness: quien
construye no verifica.

### Un hueco que aparece construyendo vuelve al orquestador

Si armando una tool falta otra capacidad, el resultado es `TOOL_BUILD_CAPABILITY_GAP` y se corta.
No hay cadena autónoma de construcción. Una tool que construye la tool que necesita la tool es un
lugar donde nadie puede decir después con qué recursos se decidió algo, que es lo único que los
tres bloques anteriores construyeron.

### Un contrato incompatible es una major nueva, no un reemplazo

Otras skills y agentes dependen del contrato de una tool. Pisarlo en su lugar rompe a distancia y
en silencio. Se versiona, y las dos versiones conviven en el registro.

### Los secrets se declaran, no se guardan

El contrato nombra `secretsRequired`; el valor lo inyecta el runtime desde el almacén que ya
existe. Y la limpieza del contrato y del resultado **recorre el documento entero**, no una lista de
campos nombrados. Esto no es una precaución teórica: es exactamente el error que el Bloque 2
cometió y corrigió, y que el Bloque 3 volvió a cometer un bloque después con una lista de cuatro
campos.

### Un check faltante no dispara una tool

`CAPABILITY_GAP` deriva a `dev-tool-builder`. `CHECK_GAP` se declara y va al circuito normativo.
Las tools ejecutan capacidades, las policies restringen comportamiento y los checks validan
resultados; el día que el constructor de tools pueda crear el check que lo aprueba, el check dejó
de significar algo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/tool-contract.schema.json` | El contrato: `name`, `version`, `capabilities`, `inputs`, `outputs`, `sideEffects`, `permissions`, `secretsRequired`, `networkAccess`, `timeoutSeconds`, `idempotent`, `retryPolicy`, `riskLevel`, `blastRadius` |
| `comun/schemas/tool-registry.schema.json` | El registro: una entrada por tool y versión, con `lifecycle` y el resultado de cada validación |
| `harnesses/desarrollo/bin/orquestacion/tools.py` | Valida el contrato, deriva el riesgo, controla least privilege y decide si un cambio de contrato es incompatible |
| `harnesses/desarrollo/bin/orquestacion/registro_tools.py` | Lee y escribe el Tool Registry, resuelve capacidad a tool y filtra `DEPRECATED` y `RETIRED` |
| `harnesses/desarrollo/reglas/permisos-por-capacidad.json` | Qué permisos necesita cada capacidad, como dato. Lo que no está declarado es hueco, no permiso |
| `harnesses/desarrollo/bin/orquestacion/consumo.py` | Se le agrega la compuerta de riesgo de tool, separada de la de modelo |
| `harnesses/desarrollo/bin/orquestacion/capacidades.py` | El hueco pasa a llevar la solicitud estructurada: `requestedBy`, `purpose`, `expectedInput`, `expectedOutput` |
| `harnesses/desarrollo/agents/dev-tool-builder.md` | El agente, en inglés — decide reusar, extender o crear, y escribe la implementación |
| `comun/schemas/orchestration-plan.schema.json` | `capabilityGaps` enriquecido y `toolApprovals` al lado de `humanApprovals` |
| `docs/orquestacion.md` | El flujo nuevo y las dos compuertas |

## Escenarios verificables

### El contrato antes que el código

- **E-01** — Una tool sin contrato válido no se registra: la operación levanta y el Tool Registry
  queda byte a byte igual que antes. · rojo visto: si
- **E-02** — A un contrato al que le falta un campo obligatorio se le responde `CONTRACT_INVALID` y
  el mensaje nombra el campo que falta. · rojo visto: si
- **E-03** — `sideEffects` fuera de `READ_ONLY`, `MUTATING` y `DESTRUCTIVE` es contrato inválido.
  · rojo visto: si
- **E-04** — `riskLevel` fuera de `LOW`, `MEDIUM`, `HIGH` y `CRITICAL` es contrato inválido.
  · rojo visto: si

### El riesgo sale del contrato

- **E-05** — Un contrato `READ_ONLY`, sin red, sin secrets y con `blastRadius.scope: repository`
  deriva `LOW`. · rojo visto: si
- **E-06** — El mismo contrato con `networkAccess: true` no puede quedar `LOW`: deriva `MEDIUM` o
  más. · rojo visto: si
- **E-07** — Un contrato `DESTRUCTIVE`, o uno que muta con `blastRadius.productionImpact: true`,
  deriva `CRITICAL`. · rojo visto: si
- **E-08** — Un `riskLevel` declarado más bajo que el derivado se rechaza y el mensaje muestra los
  dos; uno más alto se respeta tal como viene. · rojo visto: si
- **E-09** — El mismo contrato construido bajo un perfil `low_cost` y bajo uno `premium` da el
  mismo `riskLevel`: el tier no entra en la derivación. · rojo visto: si

### Least privilege

- **E-10** — Un contrato que pide un permiso que su capacidad no necesita devuelve
  `PERMISSION_SCOPE_TOO_BROAD` y nombra el permiso sobrante. · rojo visto: si
- **E-11** — Una capacidad que no figura en `permisos-por-capacidad.json` se trata como hueco: el
  contrato no se aprueba por defecto ni se le conceden todos los permisos. · rojo visto: si

### Las dos compuertas

- **E-12** — Una tool `CRITICAL` arma una solicitud de aprobación de riesgo, separada de las de
  modelo, y la tool no se registra hasta que alguien decida. · rojo visto: no consta
- **E-13** — Una tool `DESTRUCTIVE` exige aprobación humana explícita aunque su `riskLevel` no sea
  `CRITICAL`. · rojo visto: no consta
- **E-14** — Con presupuesto premium disponible la compuerta de modelo no pregunta, y la de riesgo
  pregunta igual: aprobar consumo no aprueba riesgo. · rojo visto: no consta
- **E-15** — Una tool `HIGH` pregunta o no según la policy configurada, y la policy por defecto
  pregunta. · rojo visto: no consta
- **E-16** — Con una aprobación de riesgo pendiente, el plan no queda `READY_FOR_EXECUTION`.
  · rojo visto: no consta

### Reusar antes que extender, extender antes que crear

- **E-17** — Si la capacidad ya está disponible en el Capability Registry, el resultado es
  `CAPABILITY_ALREADY_EXISTS` y no se construye nada. · rojo visto: si
- **E-18** — Si una tool registrada y seleccionable ya declara esa capacidad, la resolución la
  reusa y `strategy` no es `CREATE`. · rojo visto: si
- **E-19** — Un resultado con `strategy: CREATE` y `alternativesEvaluated` vacío es inválido: crear
  sin haber mirado qué había no es una decisión, es un default. · rojo visto: si
- **E-20** — Una tool `DEPRECATED` o `RETIRED` no se selecciona para trabajo nuevo, aunque declare
  la capacidad pedida. · rojo visto: si

### Ciclo de vida

- **E-21** — Una tool generada entra `EXPERIMENTAL` o `TEMPORARY`, nunca `APPROVED`, aunque todas
  sus validaciones estén en verde. · rojo visto: si
- **E-22** — El salto a `PROMOTION_CANDIDATE` exige la evidencia completa —ejecución exitosa,
  tests, contrato estable, seguridad, permisos y blast radius conocidos—: falta uno solo y no pasa.
  · rojo visto: si
- **E-23** — El salto de `PROMOTION_CANDIDATE` a `APPROVED` no lo puede dar `dev-tool-builder`.
  · rojo visto: si
- **E-24** — Una transición que no está en la máquina de estados se rechaza, y el mensaje dice cuál
  era el estado y cuál el pedido. · rojo visto: si

### Versionado

- **E-25** — Registrar la misma `name@version` con un contrato distinto se rechaza.
  · rojo visto: si
- **E-26** — Un cambio incompatible de contrato exige major nueva, y las dos versiones conviven en
  el registro. · rojo visto: si

### Secrets

- **E-27** — El contrato nombra el secret en `secretsRequired` y el registro guarda el nombre; el
  valor no aparece en ningún campo. · rojo visto: si
- **E-28** — Un valor con forma de secreto en cualquier campo del contrato, del registro o del
  resultado se detecta con el mismo catálogo que ya usa el hook —`comun/hooks/lib/secretos.py`— y
  no se escribe. · rojo visto: si
- **E-29** — La limpieza recorre las claves del documento entero, no una lista de campos por
  nombre: un campo agregado después queda limpio sin que nadie lo agregue a ninguna lista.
  · rojo visto: si

### Pipeline y trazabilidad

- **E-30** — Una etapa del pipeline que no se pudo correr queda `NOT_RUN`, y `NOT_RUN` no cuenta
  como `PASS` en ninguna decisión. · rojo visto: si
- **E-31** — Una tool con alguna validación en rojo no se registra. · rojo visto: si
- **E-32** — La traza de una ejecución dice tool, versión, capacidad, duración, resultado y side
  effects, y no lleva secretos ni contenido sensible. · rojo visto: no consta

### Recursión y límites

- **E-33** — Una capacidad que falta mientras se construye una tool devuelve
  `TOOL_BUILD_CAPABILITY_GAP` al orquestador y no arranca una segunda construcción.
  · rojo visto: no consta
- **E-34** — Un `CHECK_GAP` no deriva a `dev-tool-builder` ni crea ninguna tool.
  · rojo visto: no consta
- **E-35** — El resultado del constructor no crea ni modifica policies ni checks.
  · rojo visto: no consta

### El agente

- **E-36** — `agents/dev-tool-builder.md` está en inglés, como manda ADR-0011 para todo `.md` que
  un modelo carga como instrucciones. · rojo visto: no consta
- **E-37** — Frente a un `capabilityGap` real, el agente evalúa reusar y extender antes de crear, y
  el contrato que devuelve pide los permisos mínimos de esa capacidad y ninguno más.
  · rojo visto: no consta
  · verificación: lectura — el sujeto es una corrida de un modelo, y la suite no invoca al agente

## Cómo se verifica

Treinta y seis de los treinta y siete escenarios pasan por la suite: son comprobables contra datos
y módulos, sin invocar a ningún modelo. El contrato, la derivación de riesgo, las compuertas, el
ciclo de vida, el versionado, los secrets y los límites son código y dato.

El único por lectura es **E-37**, y es por ADR-0009: el sujeto es una corrida de `dev-tool-builder`
sobre un hueco real, y ningún test determinista puede observar si un modelo miró el registro antes
de crear. Lo firma alguien distinto de quien construye, con fecha.

📌 **E-36 es determinista y se queda en la suite.** El idioma de un archivo se puede medir; que el
agente se comporte como el archivo dice, no.

## Riesgos conocidos

- **Sin sandbox, la etapa sale `NOT_RUN` en toda corrida real.** El pipeline es honesto —declara el
  hueco en vez de fingir un `PASS`— pero una tool registrada con `sandbox: NOT_RUN` es una tool que
  nadie vio correr aislada. Es el riesgo más grande del cambio y no se resuelve acá.
- **La derivación de riesgo es una heurística sobre lo declarado.** Una tool cuyo contrato miente
  sale `LOW`. El contrato no se comprueba contra el código de la tool, y comprobarlo pide análisis
  estático que este cambio no construye.
- **`permisos-por-capacidad.json` lo escribe una persona.** Mal escrito por lo bajo,
  `PERMISSION_SCOPE_TOO_BROAD` se vuelve ruido; mal escrito por lo alto, se vuelve silencio. Es la
  misma dependencia de criterio humano que tiene la matriz de §7.1.
- **`dev-security` no existe.** `SECURITY_REVIEW_REQUIRED` deriva a un hueco del roster: el estado
  se emite y nadie lo recibe.
- **La compuerta de riesgo no tiene quién la conteste.** Igual que la de modelo, el plan queda
  esperando una decisión humana que hoy nadie está esperando: no hay interfaz que la muestre.
