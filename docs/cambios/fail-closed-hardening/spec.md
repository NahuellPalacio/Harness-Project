# Flow Governance, Wave 5 — fallar cerrado: capacidades, hallazgos, frescura y el Bloque 4

**Estado:** verificado y cerrado · **Fecha:** 02-10-2026 · **Bloque:** transversal (no es un bloque nuevo)

## Qué problema resuelve

Después de la Wave 4 quedaban cuatro lugares donde el harness decía algo más tranquilo de lo que
sabía:

- **Una integración caída se leía como una capacidad que no existe.** Con Jira en
  `AUTHENTICATION_FAILED`, una unidad que pedía `jira.issue.read` se derivaba a `dev-tool-builder`,
  como si hubiera que construir una tool. Jira sabe leer issues; lo que falla es la conexión.
- **Un hallazgo `CRITICAL` sin resolver dejaba el reporte de seguridad `READY_FOR_SECURITY_REVIEW`,**
  con `CRITICAL: 1` en la tapa. `UNRESOLVED` no estaba ni entre los vigentes ni entre lo incompleto.
- **`plan` y `refute --compile` no miraban la frescura** de la fuente normativa de la que dependen:
  una fuente con una alerta de integridad se usaba como si estuviera al día.
- **El Bloque 4 mostraba `0`** en los tokens que no pudo resolver, y montos y tiempos parciales como
  si fueran el total.

## Qué queda afuera

- **Los cinco estados de integración no cambian:** `NOT_CONFIGURED`, `AUTHENTICATION_FAILED`,
  `CONNECTION_FAILED`, `PERMISSION_DENIED`, `AVAILABLE`. No hay `NOT_REQUIRED`. Lo nuevo vive en la
  capa de la capacidad.
- **El ledger del Bloque 4 no cambia, y `summary.json` solo gana un campo.** El `0` con su
  `unresolved` sigue adentro; lo que cambia es la presentación. El campo nuevo, `resolved`, dice qué
  métrica quedó resuelta, para el reporte de seguridad, que no puede importar la regla. El Bloque 4
  sigue observando: no gobierna.
- **La ingesta del Bloque 4** —el adapter de Claude Code que registra como `RESOLVED` un mensaje sin
  `usage`, la barra que descarta los `USAGE_UNRESOLVED` antes del libro— y **los estados de
  instalación** que pintan `OK` sin resolver (`block4: OK` con el libro vacío, `-Doctor` en verde con
  `CONFIGURED`). Son de la Wave 6; están anotados.
- **La frescura en el reporte de seguridad** sigue como está: el reporte ya pone `BLOCKED` todo ES0902
  que no esté `CURRENT`. Esta Wave agrega la compuerta de las operaciones, no reescribe el reporte.
- Todo lo diferido de la Wave 4: persistencia fuera del proyecto, la lista de programas de lectura,
  `ANSWER` sin inputs reales.

## Las decisiones, y por qué

### La disponibilidad de una capacidad

```text
la integración soporta la capacidad
+
el estado de la integración (y si se descubrió)
=
la disponibilidad de la capacidad
```

| Disponibilidad | Cuándo | `reasonCode` | A `dev-tool-builder` |
|---|---|---|---|
| `SUPPORTED_AVAILABLE` | `ENABLED` en el registro, o capacidad local del roster | `CAPABILITY_AVAILABLE` | no |
| `SUPPORTED_UNAVAILABLE` | Un adapter la declara y el registro no la tiene `ENABLED` | el estado de la integración; `CAPABILITY_NOT_DISCOVERED` si la integración está `AVAILABLE` y esa capacidad no se descubrió; `CAPABILITY_REGISTRY_ABSENT` si nunca se validó | **nunca** |
| `NOT_SUPPORTED` | Ningún adapter la declara ni es local | `CAPABILITY_NOT_SUPPORTED` | sí, como hasta ahora |

**La autoridad de qué soporta cada integración es una sola:** la tupla `CAPACIDADES` de cada adapter,
la misma con la que `dev-harness.py` arma `RegistroCapacidades`. `integraciones/registro.py` la
expone (`clases`, `soporte`, `disponibilidad`) y `dev-harness.py` deja de listar las clases por su
cuenta. El estado de cada integración sale del registro de capacidades, como siempre. No hay un
catálogo nuevo.

### En el plan

- `capabilityGaps` lleva **solo** lo `NOT_SUPPORTED`, con `derivedTo: dev-tool-builder`.
- Un campo nuevo y opcional, `capabilityStatus[]`, dice por cada capacidad pedida: `capabilityId`,
  `supported`, `available`, `availability`, `integration`, `integrationState`, `reasonCode`,
  `derivedTo` y `toolClass`. Los dos últimos son `null` salvo en `NOT_SUPPORTED`.
- La unidad que pide algo no disponible sigue `BLOCKED`, pero la señal `capability_gap` se agrega solo
  si lo que falta no está soportado.
- Con algo `SUPPORTED_UNAVAILABLE`, el plan queda `BLOCKED` y no `CAPABILITY_RESOLUTION`.

### En el flujo

Un plan `BLOCKED` por una capacidad soportada y no disponible da `CAPABILITY_UNAVAILABLE`:
`HARD_BLOCKER`, en `PLANNING`, `inputId` `plan.capabilityStatus`. Nunca `CAPABILITY_GAP`.

`flujo <KEY> --resume` lo revalida por `registrar_capacidades`, como un input de configuración de la
Wave 4, solo para las integraciones del plan que estaban caídas. Si ahora el registro las tiene
`ENABLED`, el plan quedó viejo (`PLAN_STALE`) y hay que regenerarlo (`PLAN_NOT_READY`).

### Un hallazgo sin resolver no deja pasar

| Hallazgo | Qué significa | Efecto |
|---|---|---|
| `RESOLVED` | resuelto y seguro | ninguno |
| `OPEN` / `REOPENED`, `CRITICAL` o `blocking` | resuelto inseguro: está y es grave | `ACTION_REQUIRED`, como hasta ahora |
| `UNRESOLVED`, `CRITICAL` o `blocking` o de severidad desconocida | no se sabe | bloqueo `REVIEW_INCOMPLETE` |
| `OPEN` / `REOPENED` de severidad `UNRESOLVED` | está y no se sabe cuánto pesa | bloqueo `REVIEW_INCOMPLETE` |

`UNRESOLVED` sigue siendo `UNRESOLVED`: no se convierte en `OPEN` ni se cuenta como abierto. El
bloqueo va en `blockingConditions` con `effect: REVIEW_INCOMPLETE`, y el estado del sistema queda
`REVIEW_INCOMPLETE`. Gana `BLOCKED`, si lo hay; `REVIEW_INCOMPLETE` gana sobre `ACTION_REQUIRED`, la
misma precedencia de siempre. Nunca `READY_FOR_SECURITY_REVIEW`.

El caso de la severidad desconocida lo decidió la persona: un hallazgo que podría ser crítico no se
trata como uno que no lo es.

### La frescura compuerta la operación que depende de la fuente

```text
operación -> fuentes que exige -> su frescura -> compuerta de esa operación
```

| Operación | Fuentes que exige |
|---|---|
| `plan` | los estándares de los bloques normativos de sus unidades: hoy toda unidad trae ES0901 y ES0902 |
| `refute --compile` | el estándar de cada unidad que compila |

Las dos salen de la misma función, la que la refutación ya usa para leer el bloque normativo de una
unidad (`refutacion._bloques`): lo que el plan declara es lo que la refutación va a compilar.

**Bloquean la operación** solo los estados de integridad: `SOURCE_INTEGRITY_ALERT`,
`SOURCE_CHANGED_SAME_VERSION` y `VERSION_REGRESSION`. Son los mismos que la bienvenida ya trata como
bloqueo (`FUENTE_BLOQUEA`), y la lista vive una sola vez en `orquestacion/frescura.py`
(`BLOQUEAN_OPERACION`).

**Todo lo demás que no sea `CURRENT` no bloquea, pero tampoco pasa por `CURRENT`.** Las fuentes de
fábrica traen `sha256: null`, así que todo proyecto arranca en `FRESHNESS_UNVERIFIED`; bloquear eso
dejaría a todo proyecto sin poder planificar ni refutar hasta aceptar las fuentes. La persona eligió
que la operación siga, marcada:

- **el plan** declara `knowledgeSources[]` (`standard`, `state`, `verified`, `blocking`) y un aviso
  cuando alguna fuente no está verificada;
- **la refutación** agrega el aviso `REFUTATION_SOURCE_UNVERIFIED:<estándar>:<estado>` a `run.json`.

Sin `harness.fuentes.json`, o sin la fuente adentro, el estado es `FRESHNESS_UNVERIFIED`: no se
verificó.

Con un estado de integridad:

- **el plan** queda `BLOCKED`, y el flujo da un bloqueo con el estado como código (`HARD_BLOCKER`,
  `PLANNING`, `inputId` `plan.knowledgeSources`). El flujo mira la frescura de **ahora**: si la alerta
  apareció después de planificar, igual bloquea; si se resolvió, el plan quedó viejo;
- **`refute --compile`** no compila y no escribe nada: sale con 2 y el código del estado.

Una fuente que la operación no exige no la bloquea: una alerta en ES0903 o en PC0901 no frena a
ninguno de los dos, y una en ES0901 no cambia el conocimiento del reporte de seguridad, que mira solo
ES0902.

### El Bloque 4 no muestra un cero que no midió

```text
métrica sin resolver -> N/D
cero medido           -> 0
```

| Métrica | Sin resolver cuando |
|---|---|
| Tokens (total, por fila y sin atribuir) | `USAGE_UNRESOLVED` o `USAGE_RECONCILIATION_UNRESOLVED` en `unresolved` |
| Costo real y equivalente | el estado del costo no es `RESOLVED`: un monto parcial es un piso, no un total |
| Tiempo, por clase (`wallMs`, `modelMs`, `toolMs`) | a algún evento le faltó esa clase (`<clase>Missing`); sin ese conteo, `TIME_ATTRIBUTION_UNRESOLVED` |

Lo aplica una sola función, `contabilidad/presentacion.py` (`cantidad`), y vale también para un valor
nulo: lo que no se resolvió es `N/D`, nunca «sin resolver» ni `?` (E-43, decidido por la persona el
02-10-2026). Se usa en `contabilidad` (texto),
`execution-cost.md`, el resumen de la refutación, `contabilidad --barra` y la Context Bar. El
reporte de seguridad no puede importar `contabilidad` (E-06 de `reporte-de-seguridad`), así que lee
la misma decisión del campo `resolved` de `summary.json`. Un `summary.json` anterior, sin ese campo y
con algo en `unresolved`, no deja copiar ningún número como valor: sin saber cuál es un piso, ninguno
lo es. En la sección de ejecución del reporte, lo que no está es `N/D` y ya no «desconocido», en md y
en html: el test que recalcula cada `data-field` del html (E-44 de `48_reporte_de_seguridad`) se
actualizó con esa regla. Por E-43, el costo real de una suscripción en `execution-cost.md` dice `N/D`
y no «sin resolver»: E-12 de `30_b4_contabilidad` se actualizó igual.

El tiempo se decide por clase porque `TIME_ATTRIBUTION_UNRESOLVED` lo levanta cualquier clase que
falte: un tiempo de pared medido entero no es un piso porque falte el de las tools.

```text
metric A unresolved != metric B unresolved

resolved wall time + unresolved model time
=
wall time visible + model time N/D
```

Es lo que ratificó la persona el 02-10-2026, cuando el texto de E-22 se corrigió después de su
contradicho (`verificacion.md`).

**La Context Bar no muestra `N/D`:** su contrato (E-21 de `bloque-1-context-bar`) es que lo que el
Bloque 4 no tiene no aparece. Esta Wave cierra los dos lugares donde aparecía igual: el `Budget %`
calculado sobre un costo parcial y el tiempo parcial.

`--json` de `contabilidad` sigue siendo `summary.json` tal cual: el `0` con su `unresolved`, para un
programa que sabe leerlo.

## Escenarios

Cada `E-nn` es el `W5-0nn` con el mismo número hasta E-34. De E-35 en adelante los pidió la
implementación.

### Capacidades

- **E-01** — Una capacidad soportada con el registro `ENABLED` es `SUPPORTED_AVAILABLE`. `rojo visto`
- **E-02** — Soportada y la integración en `AUTHENTICATION_FAILED`: `SUPPORTED_UNAVAILABLE`, con ese
  estado como `integrationState` y `reasonCode`. `rojo visto`
- **E-03** — Lo mismo con `CONNECTION_FAILED`. `rojo visto`
- **E-04** — Lo mismo con `PERMISSION_DENIED`. `rojo visto`
- **E-05** — Lo mismo con `NOT_CONFIGURED`. `rojo visto`
- **E-06** — Una capacidad que ningún adapter declara ni es local: `NOT_SUPPORTED`. `rojo visto`
- **E-07** — Un plan que pide una capacidad `SUPPORTED_UNAVAILABLE` no la deriva: `capabilityGaps`
  vacío, la unidad `BLOCKED`, el plan `BLOCKED` y nunca `CAPABILITY_RESOLUTION`. `rojo visto`
- **E-08** — Una `NOT_SUPPORTED` se sigue derivando a `dev-tool-builder`, `TEMPORARY`. `rojo visto`
- **E-09** — `capabilityStatus` no miente: `derivedTo` y `toolClass` en `null` para una integración
  caída, y `mostrar_plan` dice la integración y su estado, no `→ dev-tool-builder`. `rojo visto`

### Seguridad

- **E-10** — Un hallazgo `CRITICAL` `OPEN` da `ACTION_REQUIRED`. `rojo visto, por mutación`
- **E-11** — Un hallazgo `CRITICAL` `REOPENED` da `ACTION_REQUIRED`. `rojo visto`
- **E-12** — Un hallazgo `CRITICAL` `UNRESOLVED` da `REVIEW_INCOMPLETE`, con un bloqueo de `finding`;
  nunca `READY_FOR_SECURITY_REVIEW`. `rojo visto`
- **E-13** — `UNRESOLVED` no se convierte en `OPEN`: el estado del ítem y los contadores lo
  conservan. `rojo visto, por mutación`

### Frescura

- **E-14** — Con ES0901 `CURRENT`, el plan que la exige sale listo y la declara verificada.
  `rojo visto`
- **E-15** — Con ES0901 `FRESHNESS_UNVERIFIED`, o sin `harness.fuentes.json`, el plan sigue, pero la
  declara no verificada y lo avisa; `refute --compile` compila y agrega
  `REFUTATION_SOURCE_UNVERIFIED`. Nunca pasa por `CURRENT`. `rojo visto`
- **E-16** — Con ES0901 en `SOURCE_INTEGRITY_ALERT`, `SOURCE_CHANGED_SAME_VERSION` o
  `VERSION_REGRESSION`: el plan queda `BLOCKED`, el flujo bloquea con ese código y `refute --compile`
  sale con 2 sin escribir nada. `rojo visto`
- **E-17** — Una fuente que la operación no exige no la bloquea: una alerta en ES0903 o en PC0901
  no frena el plan ni la refutación, y una en ES0901 no bloquea el conocimiento del reporte de
  seguridad. `rojo visto`
- **E-18** — `plan`, `refute` y el flujo usan la misma lista de estados que bloquean, que vive una
  vez en `frescura` y es la de la bienvenida. `rojo visto`

### Bloque 4

- **E-19** — Con `USAGE_UNRESOLVED`, los tokens salen `N/D` en `contabilidad`, en
  `execution-cost.md`, en el resumen de la refutación y en el reporte de seguridad (md y html),
  también con un `summary.json` anterior, sin `resolved`. `rojo visto`
- **E-20** — Un cero medido sale `0`. `rojo visto, por mutación`
- **E-21** — No hay un segundo ledger: el libro es uno, y `summary.json` sigue con su `0` y su
  `unresolved`; solo gana `resolved`. `rojo visto, por mutación`
- **E-22** — La Context Bar no confunde lo sin resolver con un cero: no muestra `Budget %` sobre un
  costo sin resolver, ni tokens con `USAGE_UNRESOLVED`, ni un tiempo de pared al que le faltó algún
  evento; uno medido entero sí, aunque falte otra clase. `rojo visto`

### Los estados de integración

- **E-23** — Los cinco estados de integración siguen siendo exactamente esos cinco. `rojo visto, por mutación`
- **E-24** — `NOT_REQUIRED` no es un estado de integración ni una disponibilidad. `rojo visto, por mutación`

### Lo que no se rompe

- **E-25** — La Wave 4 sigue verde (`64_interaccion_humana`). `rojo visto: no consta`
- **E-26** — La Wave 3 sigue verde (`63_compuerta_del_flujo`). `rojo visto: no consta`
- **E-27** — La Wave 2 sigue verde (`62_estado_del_flujo`). `rojo visto: no consta`
- **E-28** — La Wave 1 sigue verde (`61_flujo_precondiciones`). `rojo visto: no consta`
- **E-29** — La refutación atómica sigue verde (`55_refutacion_atomica`). `rojo visto: no consta`
- **E-30** — Entorno primero sigue verde (`60_entorno_primero`). `rojo visto: no consta`
- **E-31** — El reporte de seguridad sigue verde (`48_reporte_de_seguridad`). `rojo visto: no consta`
- **E-32** — El Bloque 4 sigue verde (`30_b4_contabilidad`). `rojo visto: no consta`
- **E-33** — La Context Bar sigue verde (`53_context_bar`). `rojo visto: no consta`
- **E-34** — La compuerta entera, `.\tests\Invoke-Tests.ps1`. `rojo visto: no consta`

### Lo que pidió la implementación

- **E-35** — El flujo de un plan `BLOCKED` por una capacidad no disponible da `CAPABILITY_UNAVAILABLE`
  (`HARD_BLOCKER`), nunca `CAPABILITY_GAP`; `--resume` revalida solo esas integraciones, y si vuelven
  `ENABLED` el plan queda viejo. `rojo visto`
- **E-36** — Un hallazgo `UNRESOLVED` con `blocking: true`, y uno que estaba `RESOLVED` y pasa a
  `UNRESOLVED`, también dan `REVIEW_INCOMPLETE`. `rojo visto`
- **E-37** — Un hallazgo vigente de severidad desconocida da `REVIEW_INCOMPLETE`; un `RESOLVED` no
  bloquea. `rojo visto`
- **E-38** — Una alerta de integridad que aparece después de planificar bloquea el flujo; resuelta,
  el plan queda viejo. `rojo visto`
- **E-39** — Un costo o un tiempo parcial —algo resuelto y algo no— sale `N/D`, no como el total;
  en el reporte de seguridad también con un `summary.json` anterior, y en la sección de presupuesto
  (consumido y proyectado). `rojo visto`
- **E-40** — Una capacidad soportada con la integración `AVAILABLE` que no se descubrió es
  `SUPPORTED_UNAVAILABLE` con `CAPABILITY_NOT_DISCOVERED`; sin registro de capacidades,
  `CAPABILITY_REGISTRY_ABSENT`. Nunca `NOT_SUPPORTED`. `rojo visto`
- **E-43** — Una métrica del Bloque 4 sin resolver es `N/D` también cuando su valor es nulo, en la
  sección de presupuesto incluida: nunca «sin resolver», ni `?`, ni `0`. Resuelta, su valor, `0` incluido. Cada una por su cuenta: una pared
  resuelta con el modelo sin resolver da la pared visible y el modelo `N/D`. `rojo visto`
- **E-42** — Un plan de antes de la Wave 5, sin `capabilityStatus`, que derivó a `dev-tool-builder`
  una capacidad soportada: el flujo no dice `CAPABILITY_GAP`; el plan quedó viejo y se regenera. Un
  hueco de algo que no se soporta sigue siendo `CAPABILITY_GAP`. `rojo visto`
- **E-41** — La autoridad de lo soportado es una: `registro.soporte()` sale de los `CAPACIDADES` de los
  adapters, `dev-harness.py` usa esas mismas clases y el manifiesto dice lo mismo. `rojo visto: no
  consta`

## Cómo se verifica

`tests/casos/65_fail_closed.py` tiene un test por escenario, de E-01 a E-24 y de E-35 a E-43, con el
id en el nombre. E-25 a E-33 son los archivos de la suite que nombran, y E-34 es la compuerta entera.
Verifica `harness-spec-refuter`, que no es quien construyó.
