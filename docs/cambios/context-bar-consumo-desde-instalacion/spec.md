# Bloque 1 — la Context Bar muestra el consumo de contexto desde la instalación

**Estado:** verificado y cerrado · **Fecha:** 30-09-2026 · **Bloque:** 1, leyendo al 4

## Qué problema resuelve

La Context Bar de una instalación nueva **nunca muestra un porcentaje de contexto ni un color**.
Los colores de 0.27.0 existen, pero en un proyecto recién instalado no se disparan. Hay dos causas,
las dos anteriores al renderizador:

- **El límite de la ventana nunca tiene valor.** El único lugar que lo asigna es
  `adaptadores/claude_code.py:95`, y le pone `None`. Sin límite, `barra.py:48-50` no calcula la
  fracción y la barra dibuja `Ctx 10k`. Claude Code sí manda el tamaño de la ventana en el stdin de la
  `statusLine` (`context_window.context_window_size`), pero `statusline.py` lo ignora a propósito:
  su docstring (17-19) dice que "El costo y el contexto que el cliente manda por stdin NO se usan", y
  E-22 de `53_context_bar.py` lo fija.
- **Una instalación nueva no tiene umbrales.** Sin `.claude/harness.presupuesto.json`, que el
  instalador no crea, `presupuesto.nivel` da `UNRESOLVED` para cualquier fracción.

Además, `harness --verbose` dice `ACTIVA` y no explica por qué la barra no puede pintar. La señal de
vida tampoco dice si el proceso real de la `statusLine` tiene `NO_COLOR`.

Lo que dice Claude Code de ese stdin se tomó de su documentación de la `statusLine`
(`code.claude.com/docs/en/statusline`), leída el 30-09-2026:

- `context_window` viene siempre;
- `total_input_tokens` es la entrada de la última respuesta, con la caché incluida, y
  `total_output_tokens` es su salida;
- `current_usage` es `null` antes de la primera llamada a la API y después de un `/compact`, hasta la
  llamada siguiente;
- `used_percentage` cuenta solo la entrada;
- la documentación no dice que Claude Code le ponga `NO_COLOR` a la `statusLine`, solo `COLUMNS` y
  `LINES`.

## Qué queda afuera

- **Usar el `cost` del stdin de la `statusLine`.** Sería una segunda fuente de costo al lado del
  camino del Bloque 4, con otras reglas. El costo sigue saliendo solo de la transcripción, como decidió
  `bloque-1-context-bar`.
- **Una tabla de modelo a tamaño de ventana.** Un número escrito en el harness es un número inventado
  el día que el proveedor lo cambia. El único que sabe el tamaño es el proveedor, y lo manda.
- **Deducir el límite de `exceeds_200k_tokens`.** Según la documentación es un umbral fijo de 200k,
  sea cual sea la ventana real. No dice nada del límite.
- **Tocar el renderizador.** Los campos, su orden, las secuencias ANSI, la negrita de `HARNESS`,
  `LINEA_SIN_DATOS` y la semántica de `NO_COLOR` son de `context-bar-colores`, que está cerrado. Este
  cambio solo informa a `Ctx` lo suficiente para que sea un porcentaje.
- **Un presupuesto de dinero por defecto.** Un límite monetario lo decide el proyecto o el organismo,
  no el instalador. La política por defecto es de contexto y nada más.
- **Volver a preguntar en `setup`.** El `setup` interactivo se retiró en 0.26.0. Este cambio informa;
  lo que agrega algo a una política es un comando explícito.
- **Ignorar `NO_COLOR` porque la barra corre bajo Claude Code.** El arreglo es ver `NO_COLOR`, no
  desobedecerlo.
- **Corregir `Ctx` entre un `/compact` y la llamada siguiente.** En ese intervalo el proveedor no manda
  una observación usable, y la barra sigue con la última foto válida. Queda en Riesgos.
- **El adaptador de Codex.** No tiene `statusLine` y sigue devolviendo todo sin resolver.
- **El formato de `dev-harness contabilidad --barra` (`barra.compacto`).** Sale del mismo resumen y
  gana el porcentaje sin cambiar su forma. Solo se le prohíbe pasar de 100% (E-23).

## Las decisiones, y por qué

### El contexto entra por el stdin, y lo lee el adaptador de Claude Code

Esta decisión pisa, **solo para el contexto**, la línea de `bloque-1-context-bar` que dejaba afuera
los datos del stdin. `statusline.py` le pasa el stdin ya parseado al adaptador de la barra
(`registro.DE_LA_BARRA`), y no nombra ningún campo de `context_window`. La función del adaptador
devuelve una foto normalizada, o "sin observación". Los nombres de campo del proveedor viven en
`adaptadores/claude_code.py` y en ningún otro `.py` de `contabilidad/`. E-22 de `53_context_bar.py`,
que pedía que `context_window.used_percentage` no cambiara nada, queda pisado por esta spec, y su
test lo dice.

### Una foto de la ventana es un evento propio: `CONTEXT_WINDOW_OBSERVED`

El contrato del adaptador suma un tercer tipo de registro, `CONTEXT_SNAPSHOT`, al lado de `USAGE` y
`PROVIDER_AGGREGATE`. En el libro se escribe como `CONTEXT_WINDOW_OBSERVED`, un tipo nuevo en el enum
cerrado de `execution-accounting-event.schema.json`. Se descartó reusar `MODEL_CALL_COMPLETED` con
tokens en cero: una foto no es una llamada al modelo, y un evento de uso con ceros entra a los
conteos, a la conciliación y a la atribución. La regla que ya existe se mantiene: **una foto de la
ventana no se suma nunca** (`agregacion.py:196-200`).

### Qué es `contextTokens`

Si los dos totales son enteros válidos no negativos, es `total_input_tokens + total_output_tokens`.
La caché no se suma de nuevo, porque `total_input_tokens` ya la incluye. `current_usage` se usa solo
si los dos totales **faltan**, y cada campo se suma una vez. Un total que está pero es inválido no es
un total que falta: la observación queda sin resolver y no cae a `current_usage`.

`used_percentage` de Claude Code cuenta solo la entrada, así que va a dar algo menos que nuestro
`Ctx`. **Esa diferencia no es una inconsistencia.** El porcentaje reportado se guarda como evidencia
del proveedor y no pisa lo que dicen los tokens y el límite.

### Sin respuesta del modelo no hay observación

Con `current_usage` en `null` y los dos totales en 0, Claude Code todavía no recibió ninguna
respuesta, y eso es lo que dice su documentación. El adaptador lo devuelve como "sin observación": no
se escribe ninguna foto, y la barra no dibuja `Ctx 0%`. Es una regla de Claude Code, y por eso vive en
su adaptador.

### Más tokens que ventana es una falla del proveedor, y se ve

Si `contextTokens > contextLimit`, el resumen lleva `CONTEXT_WINDOW_PROVIDER_INCONSISTENT`, la barra
dibuja `Ctx 270k` sin color, y ningún nivel sale de esa fracción. Ninguna salida muestra un
porcentaje mayor que 100%. No hay un arreglo para un modelo o una versión en particular.

### La identidad de una foto incluye el cursor de la transcripción

La `statusLine` corre con un debounce de 300 ms, así que la misma observación llega muchas veces. El
`dedupKey` sale de la sesión, el modelo, el cursor de la transcripción (la línea más alta ya
ingerida), los tokens, el límite y los dos porcentajes reportados. No usa la hora ni un número al
azar. La misma observación sobre la misma transcripción da el mismo `eventId`, y el libro no crece.

Se descartó una identidad sin el cursor por el caso A → B → A. Si la ventana vuelve a los mismos
valores después de un `/compact`, esa foto sería un duplicado de la primera, y "la última" quedaría
en B, vieja.

### La foto de la `statusLine` le gana a la de la transcripción

Si la sesión tiene alguna foto `CONTEXT_WINDOW_OBSERVED` válida, el contexto del resumen es la
última, en orden del libro, y la fuente es `CLAUDE_CODE_STATUSLINE`. Si no tiene, el contexto sale de
la última llamada al modelo, como hoy: tokens sin límite, fuente `TRANSCRIPT_ONLY`. Si no hay ninguna
de las dos, la fuente es `SIN RESOLVER`. La fracción y el nivel siguen siendo de `barra.py`: ni el
adaptador ni el renderizador calculan severidad.

### La política por defecto es de contexto, no de plata

El instalador copia `harnesses/desarrollo/reglas/budget-policy-context-default.json` a
`.claude/harness.presupuesto.json` **solo si ese archivo no existe**. Lleva:
- `policyId: "gcba-harness-context-bar-default"` y `billingMode: "UNKNOWN"`;
- `task`, `project` y `premiumModel` en `null`;
- `statusBar` con `warningAt` y `errorAt` en `null`, `contextWarningAt: 0.70` y
  `contextErrorAt: 0.90`.

No lleva la clave `rateTable`, ni siquiera en `null`: E-13 de `30_b4_contabilidad.py` falla con
cualquier `rateTable` en un JSON que se instala. El schema la admite ausente, y `costos.calcular` lee
la ausencia igual que `null`. *Precisado el 30-09-2026, durante la construcción: la primera versión
decía `rateTable` en `null`.*

El 70% y el 90% son defaults de producto de este harness. **No son un requisito de ES0901 ni de
ES0902.** Como `billingMode` es `UNKNOWN`, el costo se dibuja igual que sin política.

### `DEFAULT` quiere decir "el contenido de la plantilla"

`setup` y `harness --verbose` dicen `DEFAULT` cuando la política instalada es, parseada, igual a la
plantilla. Dicen `PROJECT` si es otra política válida, `MISSING` si no hay archivo e `INVALID` si no
valida. Se descartó decidirlo por `policyId`: una política con ese id y un `hardLimit` agregado a mano
ya no es la del harness.

### Una política que existe no se toca, salvo por un comando explícito

`install.ps1`, `-Update`, `setup`, `estado` y `harness` nunca escriben una
`.claude/harness.presupuesto.json` que existe. Si le faltan umbrales de contexto, lo dicen por nombre.
El único que escribe es `dev-harness.py presupuesto --context-defaults`:
- si falta el archivo, crea el default;
- si el archivo existe, agrega solo `contextWarningAt` y `contextErrorAt` que falten, y conserva el
  resto de las claves, con sus valores y en su orden.

Nunca crea un `softLimit` ni un `hardLimit`.

### El color lo dice el proceso de la `statusLine`

El shell de quien corre `harness --verbose` no es el de la `statusLine`. La señal de vida suma un
campo opcional, `presentation: {"ansi": "ENABLED" | "DISABLED_NO_COLOR"}`, que escribe la barra desde
su propio proceso. Una señal de vida vieja, sin ese campo, sigue siendo válida y se informa como
`SIN VERIFICAR`. La señal de vida sigue sin llevar números, costos, texto de la transcripción ni
credenciales.

### `INTEGRATION_VERSION` pasa a `1.2.0`

Cambian el contrato con el proveedor y la señal de vida. Como también cambian `statusline.py` y
`claude_code.py`, sus huellas cambian, y un proyecto actualizado desde 1.1.0 queda en
`RELOAD_REQUIRED` hasta que Claude Code corre el comando nuevo. Eso ya lo hace
`bienvenida._guardado_al_registrar`; este cambio lo prueba.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/contabilidad/adaptadores/claude_code.py` | `contexto_de_statusline(entrada)`: de un stdin ya parseado, una foto `CONTEXT_SNAPSHOT` o "sin observación". Es el único lugar con los nombres de campo de `context_window` |
| `harnesses/desarrollo/bin/contabilidad/adaptadores/contrato.py` | El tipo de registro `CONTEXT_SNAPSHOT`, su forma, y su paso a `CONTEXT_WINDOW_OBSERVED` |
| `harnesses/desarrollo/bin/contabilidad/eventos.py` y `comun/schemas/execution-accounting-event.schema.json` | El tipo `CONTEXT_WINDOW_OBSERVED` y sus campos: `contextTokens`, `contextLimit`, los dos porcentajes reportados y el diagnóstico |
| `harnesses/desarrollo/bin/contabilidad/agregacion.py` | Las fotos quedan afuera de sumas, conteos, conciliación y atribución. El contexto sale de la última foto, o de la transcripción, con `source` |
| `harnesses/desarrollo/bin/contabilidad/barra.py` | Sin fracción si `contextTokens > contextLimit`, y el diagnóstico `CONTEXT_WINDOW_PROVIDER_INCONSISTENT` |
| `harnesses/desarrollo/bin/contabilidad/statusline.py` | Le pasa el stdin al adaptador, anota la foto en el libro y escribe `presentation.ansi` en la señal de vida. `INTEGRATION_VERSION = "1.2.0"` |
| `comun/hooks/lib/bienvenida.py` | El contrato de la señal de vida acepta `presentation` opcional, y el estado ANSI sale de ahí |
| `harnesses/desarrollo/reglas/budget-policy-context-default.json` | La política por defecto, solo de contexto |
| `install.ps1` | Siembra `.claude/harness.presupuesto.json` si falta, en instalación y en `-Update`, y dice que los umbrales quedaron puestos sin prometer un porcentaje |
| `harnesses/desarrollo/bin/dev-harness.py` | El bloque `Context Bar` en `setup`, el bloque de diagnóstico en `harness --verbose` y `presupuesto --context-defaults` |
| `docs/contabilidad.md` | `Ctx` contra `Tok`, qué pasa con `/compact`, los umbrales como defaults operativos, y la política por defecto |
| `tests/casos/62_context_bar_consumo.py` | Los escenarios de abajo que no instalan de verdad |
| `tests/casos/62-context-bar-consumo-instalador.ps1` | E-31, E-38 a E-40, E-62 a E-68 y E-75: instalan de verdad |
| `tests/casos/53_context_bar.py` y `tests/casos/30_b4_contabilidad.py` | Las aserciones pisadas que nombra E-73, y `colores E-20` por E-65. Cada test lo dice |
| `harnesses/desarrollo/bin/contabilidad/adaptadores/registro.py`, `costos.py` y `presupuesto.py` | Lo que necesitan la foto y la plantilla. `costos.py` pierde el literal del millón que E-10 prohíbe |
| `tests/medir_barra.py` | Manda `context_window` en el stdin, así `-Doctor` mide también la escritura de la foto |

## Escenarios verificables

Cada escenario lleva entre paréntesis su id del pedido (`CTXFIX-nnn`). Los que no tienen id los agrega
esta spec.

### El adaptador de Claude Code

- **E-01** — (CTXFIX-001) Con `context_window.context_window_size` en 200000, la foto lleva
  `contextLimit: 200000`. Con 1000000, lleva 1000000. El valor sale del stdin y de ningún otro lado.
  · rojo visto: si
- **E-02** — (CTXFIX-002) Con `total_input_tokens: 120000` y `total_output_tokens: 4000`, la foto
  lleva `contextTokens: 124000`. · rojo visto: si
- **E-03** — (CTXFIX-003) Con los dos totales presentes y `current_usage` con
  `cache_read_input_tokens` y `cache_creation_input_tokens` distintos de cero, `contextTokens` es
  exactamente la suma de los dos totales. · rojo visto: si
- **E-04** — (CTXFIX-004) Sin los dos totales, `contextTokens` es la suma de `input_tokens`,
  `output_tokens`, `cache_creation_input_tokens` y `cache_read_input_tokens` de `current_usage`, cada
  uno una vez. Con los totales presentes, cambiar `current_usage` no cambia `contextTokens`.
  · rojo visto: si
- **E-05** — (CTXFIX-005) Un stdin sin `context_window`, con `context_window: null`, o con
  `current_usage: null` y los dos totales en 0, no escribe ninguna foto en el libro. La línea no
  tiene `Ctx 0%` ni ningún `%`. · rojo visto: si
- **E-06** — (CTXFIX-006) Con `context_window_size` en 0, -1, 1.5, `"200000"`, `true` o `null`, la
  foto lleva `contextLimit: null`, y la línea dibuja `Ctx <tokens>` sin `%`. · rojo visto: si
- **E-07** — (CTXFIX-007) Con `total_input_tokens` en `true`, -1, `"12000"`, una lista, o un número
  no finito leído del JSON, ninguna foto lleva `contextTokens: 0`, y la observación no cae a
  `current_usage`. · rojo visto: si
- **E-08** — (CTXFIX-008) Un stdin con `cost.total_cost_usd: 99.99` y el mismo sin `cost` dan el
  mismo libro y la misma línea, byte a byte. Ningún evento del libro lleva 99.99.
  · rojo visto: si
- **E-09** — (CTXFIX-009) `statusline.py` no contiene `context_window`, `context_window_size`,
  `used_percentage`, `remaining_percentage`, `current_usage`, `total_input_tokens` ni
  `total_output_tokens`. Entre los `.py` de `contabilidad/`, esos nombres aparecen solo en
  `adaptadores/claude_code.py`. · rojo visto: si
- **E-10** — (CTXFIX-010) Ningún `.py` de `contabilidad/`, adaptadores incluidos, contiene los
  literales `200000`, `1000000`, `200_000` ni `1_000_000`, y ninguno lee `exceeds_200k_tokens`.
  · rojo visto: si

### Una foto no es consumo

- **E-11** — (CTXFIX-011) Un libro con llamadas al modelo y fotos da `tokens.input` igual que el
  mismo libro sin las fotos. · rojo visto: si
- **E-12** — (CTXFIX-012) Igual para `tokens.output`. · rojo visto: si
- **E-13** — (CTXFIX-013) Igual para `cacheRead` y `cacheCreation`. · rojo visto: si
- **E-14** — (CTXFIX-014) Igual para el costo `actual` y `apiEquivalentEstimated`, y ninguna foto
  lleva un monto. · rojo visto: si
- **E-15** — (CTXFIX-015) `events.counted` y el `events` de cada fila de `byAgent`, `byWorkUnit`,
  `bySession` y `byModel` son iguales con y sin fotos. · rojo visto: si
- **E-16** — (CTXFIX-016) En un libro donde todo el uso está atribuido a una unidad de trabajo y a un
  agente, sumar fotos no agrega `WORKUNIT_…` ni `AGENT_ATTRIBUTION_UNRESOLVED`.
  · rojo visto: si
- **E-17** — (CTXFIX-017) Con tres fotos válidas en el libro, el contexto del resumen es la última
  anotada, nunca la suma ni la mayor. · rojo visto: si
- **E-18** — (CTXFIX-018) Diez dibujos con el mismo stdin sobre la misma transcripción dejan
  exactamente una foto en el libro. · rojo visto: si
- **E-19** — (CTXFIX-019) Otro valor de tokens o de límite deja una foto nueva. Los valores de la
  primera foto, repetidos después de que avanzó la transcripción, también dejan una foto nueva, y el
  contexto es esa última. · rojo visto: si
- **E-20** — (CTXFIX-020) El estado de conciliación y sus totales son iguales con y sin fotos.
  · rojo visto: si

### Lo que dibuja la barra

- **E-21** — (CTXFIX-021) Con `contextTokens` 134000 y `contextLimit` 200000, la línea tiene
  `Ctx 67%`. · rojo visto: si
- **E-22** — (CTXFIX-022) Con `contextTokens` 134000 y el límite sin resolver, la línea tiene
  `Ctx 134k` y ningún `%` en ese fragmento. · rojo visto: si
- **E-23** — (CTXFIX-023) Con `contextTokens` 270000 y `contextLimit` 200000, la línea tiene
  `Ctx 270k`, el resumen lleva `CONTEXT_WINDOW_PROVIDER_INCONSISTENT`, y ni la línea ni
  `contabilidad --barra` muestran un porcentaje mayor que 100. · rojo visto: si
- **E-24** — (CTXFIX-024) En ese caso, con la política por defecto, `Ctx` sale sin ninguna secuencia de
  color y la línea no tiene la etiqueta `WARNING` ni `ERROR`. · rojo visto: si
- **E-25** — (CTXFIX-025) Con 50% y la política por defecto, `Ctx 50%` sale sin secuencia de color.
  La única secuencia de la línea es la negrita de `HARNESS`. · rojo visto: si
- **E-26** — (CTXFIX-026) Con la política por defecto, 70% da `WARNING` y 69% da `NORMAL`.
  · rojo visto: si
- **E-27** — (CTXFIX-027) Con la política por defecto, 90% da `ERROR` y 89% da `WARNING`.
  · rojo visto: si
- **E-28** — (CTXFIX-028) El fragmento `Ctx` en `WARNING` y la etiqueta `WARNING` son, byte a byte, los
  de E-02 y E-07 de `context-bar-colores`. · rojo visto: si
- **E-29** — (CTXFIX-029) El fragmento `Ctx` en `ERROR` y la etiqueta `ERROR` son, byte a byte, los de
  E-03 y E-08 de `context-bar-colores`. · rojo visto: si
- **E-30** — (CTXFIX-030) `LINEA_SIN_DATOS` es `HARNESS | sin datos del Bloque 4`, y el renderizador
  instalado sin stdin dibuja exactamente eso. · rojo visto: si

### La política por defecto

- **E-31** — (CTXFIX-031) Instalar en un proyecto sin `.claude/harness.presupuesto.json` lo deja
  creado. · rojo visto: si
- **E-32** — (CTXFIX-032) La política creada valida contra `budget-policy.schema.json` con el
  validador del harness. · rojo visto: si
- **E-33** — (CTXFIX-033) Lleva `statusBar.contextWarningAt: 0.7`. · rojo visto: si
- **E-34** — (CTXFIX-034) Lleva `statusBar.contextErrorAt: 0.9`. · rojo visto: si
- **E-35** — (CTXFIX-035) No lleva `softLimit` en ninguna parte del archivo. · rojo visto: si
- **E-36** — (CTXFIX-036) No lleva `hardLimit` en ninguna parte del archivo. · rojo visto: si
- **E-37** — (CTXFIX-037) Con solo la política por defecto, la línea no tiene fragmento `Budget`, y
  el fragmento de costo es el mismo que sin política. · rojo visto: si
- **E-38** — (CTXFIX-038) Instalar en un proyecto que ya tiene una política la deja igual byte a byte.
  · rojo visto: si
- **E-39** — (CTXFIX-039) `-Update` en un proyecto sin política la crea, igual a la plantilla.
  · rojo visto: si
- **E-40** — (CTXFIX-040) `-Update` en un proyecto con una política la deja igual byte a byte, también
  una sin umbrales de contexto. · rojo visto: si

### `setup`

- **E-41** — (CTXFIX-041) `setup` con stdin cerrado termina con 0 y no espera ninguna respuesta.
  · rojo visto: si
- **E-42** — (CTXFIX-042) Con la política por defecto, `setup` muestra un bloque `Context Bar` con
  `política DEFAULT`, `contexto WARNING 70%`, `contexto ERROR 90%` y
  `presupuesto monetario SIN CONFIGURAR`. · rojo visto: si
- **E-43** — (CTXFIX-043) `setup` dice `DEFAULT` con la plantilla, `PROJECT` con otra política
  válida, `MISSING` sin archivo e `INVALID` con uno que no valida. · rojo visto: si
- **E-44** — (CTXFIX-044) Con una política `PROJECT` sin `contextWarningAt`, `setup` nombra
  `contextWarningAt`, y el archivo queda igual byte a byte. · rojo visto: si
- **E-45** — (CTXFIX-045) Igual con `contextErrorAt`. · rojo visto: si
- **E-46** — (CTXFIX-046) Sobre una política `PROJECT` sin umbrales de contexto, `setup`, `estado`,
  `harness` e `install.ps1 -Update` no cambian el archivo. `presupuesto --context-defaults` le
  agrega los dos umbrales con 0.7 y 0.9, y todas las demás claves quedan con sus valores y en su
  orden. · rojo visto: si
- **E-47** — (CTXFIX-047) `presupuesto --context-defaults` no agrega `softLimit` ni `hardLimit`: con
  `task` y `project` en `null` siguen en `null`, y los límites que ya había quedan con su valor.
  · rojo visto: si

### `harness --verbose`

- **E-48** — (CTXFIX-048) Con la barra `ACTIVA` y sin límite de ventana, `harness --verbose` dice
  `Estado ACTIVA` y no dice que la barra está lista. Con todo resuelto, dice
  `La barra está lista para mostrar consumo porcentual y alertas.` · rojo visto: si
- **E-49** — (CTXFIX-049) Sin límite, dice `Límite de ventana SIN RESOLVER` y explica que el
  proveedor todavía no informó `context_window_size`. · rojo visto: si
- **E-50** — (CTXFIX-050) Sin umbrales de contexto, dice `Umbral WARNING SIN CONFIGURAR` y
  `Umbral ERROR SIN CONFIGURAR`, y nombra los que faltan, `contextWarningAt` y `contextErrorAt`, y
  solo esos. · rojo visto: si
- **E-51** — (CTXFIX-051) Con límite, umbrales y `presentation.ansi: ENABLED`, dice
  `Límite de ventana <n>`, los dos umbrales en porcentaje, `Color ANSI HABILITADO` y la línea de
  lista. · rojo visto: si
- **E-52** — (CTXFIX-052) Con la última foto en `CONTEXT_WINDOW_PROVIDER_INCONSISTENT`, lo dice con
  ese código, y no dice que la barra está lista. · rojo visto: si
- **E-53** — (CTXFIX-053) Con `presentation.ansi: DISABLED_NO_COLOR`, dice
  `Color ANSI DESHABILITADO POR NO_COLOR` y que `NO_COLOR` está definido en el proceso de la
  `statusLine`. · rojo visto: si
- **E-54** — (CTXFIX-054) Con una señal de vida sin `presentation`, dice `Color ANSI SIN VERIFICAR`, y
  el estado de la barra es el mismo que con esa señal antes de este cambio. · rojo visto: si
- **E-55** — (CTXFIX-055) La salida de `harness --verbose` no contiene una marca que está en el texto
  del prompt de la transcripción de prueba. · rojo visto: si
- **E-56** — (CTXFIX-056) La salida no contiene el token de prueba del `.env` ni uno puesto en el stdin
  de la barra. · rojo visto: si

### La señal de vida

- **E-57** — (CTXFIX-057) Sin `NO_COLOR` en el proceso de la barra, la señal de vida lleva
  `presentation.ansi: "ENABLED"`. · rojo visto: si
- **E-58** — (CTXFIX-058) Con `NO_COLOR=1`, lleva `"DISABLED_NO_COLOR"`. · rojo visto: si
- **E-59** — (CTXFIX-059) Con `NO_COLOR=` vacía, también `"DISABLED_NO_COLOR"`. · rojo visto: si
- **E-60** — (CTXFIX-060) Las claves de la señal de vida son `sessionId`, `configurationFingerprint`,
  `integrationVersion`, `lastRenderedAt`, `block4` y `presentation`, y ningún valor es un número.
  · rojo visto: si
- **E-61** — (CTXFIX-061) Una señal de vida con las cinco claves de 1.1.0 cumple el contrato nuevo.
  · rojo visto: si

### El comando instalado

- **E-62** — (CTXFIX-062) El comando que registra `install.ps1`, corrido con
  `powershell.exe -NoProfile -Command` y un stdin con `context_window` usable, sale con 0 y dibuja
  `Ctx NN%`. · rojo visto: si
- **E-63** — (CTXFIX-063) Igual con `bash -c`. · rojo visto: si
- **E-64** — (CTXFIX-064) En los dos shells, con `context_window` y sin él, dibuja una sola línea no
  vacía. · rojo visto: si
- **E-65** — (CTXFIX-065) La señal de vida que deja lleva la huella del comando y
  `integrationVersion: "1.2.0"`, y la bienvenida la toma como prueba, igual que antes.
  · rojo visto: si
- **E-66** — (CTXFIX-066) Un proyecto instalado con el renderizador 1.1.0 queda en `RELOAD_REQUIRED`
  después de `-Update`, hasta una señal de vida 1.2.0 con la huella nueva. Con esa señal, pasa a
  `ACTIVE`. · rojo visto: si
- **E-67** — (CTXFIX-067) En un proyecto recién instalado, un dibujo sin observación de contexto no
  tiene `%`, y el dibujo siguiente, con una observación usable, tiene `Ctx NN%`.
  · rojo visto: si
- **E-68** — (CTXFIX-068) Entre esos dos dibujos no se corre `setup` ni `-Update`, no se toca
  `harness.presupuesto.json` y el comando registrado es el mismo. · rojo visto: si

### La documentación

- **E-69** — (CTXFIX-069) La sección de la Context Bar de `docs/contabilidad.md` dice que `Ctx` es la
  ocupación de la ventana actual y `Tok` los tokens acumulados de la sesión en el libro, y que son dos
  métricas distintas. · rojo visto: si
- **E-70** — (CTXFIX-070) Con una foto de 150000, más transcripción y una foto de 60000, `Ctx` baja
  mientras `Tok` sube. La misma sección dice que después de compactar eso es lo esperable.
  · rojo visto: si
- **E-71** — (CTXFIX-071) La misma sección dice que 70% y 90% son defaults operativos del harness, no
  reglas de ES0901 ni de ES0902. · rojo visto: si

### Lo que ya estaba

- **E-72** — (CTXFIX-072) Todas las aserciones `colores E-nn` de `53_context_bar.py` y E-19 de
  `54-context-bar-instalador.ps1` siguen en verde. `colores E-20` pasa a pedir `1.2.0` en lugar de
  `1.1.0`, pisado por E-65. · rojo visto: si
- **E-73** — (CTXFIX-073) `30_b4_contabilidad.py`, `30-contabilidad-instalador.ps1` y los escenarios
  de `bloque-1-context-bar` de `53_context_bar.py` siguen en verde. Cuatro aserciones quedan pisadas
  por esta spec, y cada test lo dice:
  - E-22 de 53: el `context_window` del stdin ahora cambia `Ctx`;
  - E-10 de 53: la señal de vida lleva seis claves, por E-60;
  - E-01 de 30: los tipos de evento pasan de trece a catorce, con `CONTEXT_WINDOW_OBSERVED`;
  - E-37 de 30: el techo del evento más grande se re-mide con los campos de `contextWindow`, y sigue
    debajo de 10.000 bytes.

  *Precisado el 30-09-2026, durante la construcción.* · rojo visto: si
- **E-74** — (CTXFIX-074) `.\tests\Invoke-Tests.ps1` sale 0. · rojo visto: no consta

### Los que agrega esta spec

- **E-75** — `install.ps1` termina diciendo
  `Umbrales de contexto configurados: WARNING 70% / ERROR 90%` y
  `El porcentaje aparecerá con la primera observación de contexto de Claude Code.`, y su salida no
  tiene ningún `Ctx NN%`. · rojo visto: si
- **E-76** — `harness --verbose` dice `Fuente de contexto CLAUDE_CODE_STATUSLINE` con una foto,
  `TRANSCRIPT_ONLY` sin fotos y con llamadas al modelo, y `SIN RESOLVER` sin ninguna de las dos.
  · rojo visto: si
- **E-77** — La foto guarda `used_percentage` y `remaining_percentage` como los mandó el proveedor. Un
  `used_percentage` que contradice a los tokens y al límite no cambia `contextTokens` ni el `%` de la
  línea. · rojo visto: si
- **E-78** — `harness --verbose` dice `Política DEFAULT` con la plantilla, `PROJECT` con otra
  política válida, `MISSING` sin archivo e `INVALID` con uno que no valida, con el mismo criterio que
  `setup` en E-43, y no cambia el archivo. *Agregado el 30-09-2026, después del primer veredicto: la
  decisión "`DEFAULT` quiere decir el contenido de la plantilla" y `docs/contabilidad.md` ya lo
  afirmaban, y el código no lo hacía.* · rojo visto: si

## Cómo se verifica

Todo por la suite. E-31, E-38 a E-40, E-62 a E-68 y E-75 instalan de verdad, en
`62-context-bar-consumo-instalador.ps1`. El resto va en `62_context_bar_consumo.py`, contra el
adaptador, la agregación, `dibujar`, la CLI y el renderizador instalado. E-72 a E-74 son la suite
entera. Ningún escenario tiene por sujeto una corrida de un modelo, así que no hay `lectura`.

El `rojo visto` sale de romper el código una vez por comportamiento, al menos en estos casos:
- ignorar `context_window_size`;
- sumar la caché dos veces;
- sumar las fotos a los totales de tokens;
- sacar `contextWarningAt` o `contextErrorAt` de la plantilla;
- pisar una política del proyecto;
- escribir `ENABLED` en la señal de vida con `NO_COLOR` puesta;
- decir que la barra está lista con el límite sin resolver;
- escribir 200000 en el renderizador.

El `rojo visto` salió de romper el código, la plantilla, el instalador y la documentación el
30-09-2026, sobre una copia del repositorio en un directorio temporal: nada del árbol versionado
se tocó. Fueron 63 mutaciones de una sola sustitución, cada una con su escenario en rojo, y dos de
varias sustituciones para E-55 y E-56, que tienen dos defensas —el libro no guarda texto ni
secretos, y `harness --verbose` no imprime nada de la sesión— y no se ven en rojo rompiendo una
sola. Los ocho casos de la lista: ignorar `context_window_size` dejó en rojo E-01; sumar la caché
dos veces, E-03; sumar las fotos a los totales, E-11 a E-13 y E-20; sacar `contextWarningAt` o
`contextErrorAt` de la plantilla, E-33 y E-34, con E-26 y E-27; pisar una política del proyecto,
E-38 y E-40; escribir `ENABLED` con `NO_COLOR` puesta, E-58 y E-59; decir que la barra está lista
con el límite sin resolver, E-48; y escribir 200000 en el renderizador, E-10. E-72 y E-73 se vieron
en rojo durante la construcción, antes de pisarlos: `colores E-20` de `53_context_bar.py` con la
versión en 1.2.0, E-10 de `53_context_bar.py` con la clave `presentation`, y E-01 y E-37 de
`30_b4_contabilidad.py` con el tipo catorce. E-74 no consta: la suite entera no se corrió con un
defecto adentro. E-78 se vio en rojo el mismo 30-09-2026, también sobre copias, con cuatro
mutaciones más: `harness --verbose` diciendo siempre `Política DEFAULT`, sin la línea `Política`,
escribiendo el archivo al leerlo, y decidiendo `DEFAULT` por el `policyId`.

Lo que ningún test puede ver es el entorno exacto que Claude Code le da al proceso real de la
`statusLine`. Después de la suite, alguien distinto de quien construyó hace esto en un proyecto
descartable, y lo anota en `verificacion.md` como observación de una sesión real, no como evidencia
automática:
1. instala o actualiza, abre Claude Code y produce al menos una respuesta;
2. mira la barra y corre `dev-harness.py harness --verbose`;
3. confirma que la señal de vida dice si el ANSI quedó habilitado;
4. ve `Ctx NN%` y `Tok … in / … out` juntos;
5. cruza los umbrales de forma controlada y ve los colores;
6. si el proveedor manda un límite inconsistente, ve que la barra falla a la vista.

## Riesgos conocidos

- **Los campos de `context_window` son de Claude Code y pueden cambiar.** Viven en un solo
  adaptador. Si una versión deja de mandar una ventana usable, `Ctx` vuelve a tokens, `Tok` sigue, y
  `harness --verbose` dice por qué.
- **Entre un `/compact` y la llamada siguiente, `Ctx` puede mostrar la ventana de antes de
  compactar.** El proveedor manda `current_usage: null` en ese intervalo, y la barra no inventa una
  foto. Se mira en la sesión real.
- **Nuestro `Ctx` no coincide con el porcentaje de Claude Code**, porque el nuestro cuenta la salida.
  Queda dicho en `docs/contabilidad.md` para que nadie lo lea como un error.
- **La barra escribe en el libro en cada observación nueva.** Con el debounce de 300 ms, eso suma
  latencia a un dibujo que ya está cerca de su presupuesto: unos 370 ms de 400, según lo medido el
  24-09-2026 y anotado en `PENDIENTES-FH.md`. Se mide con `tests/medir_barra.py` antes y después, y el número va en la
  verificación.
- **El libro crece con cada avance de la transcripción que trae otra ventana.** Está acotado por la
  transcripción misma, pero nada lo poda (`.claude/runtime/accounting/` ya tiene su ítem en FH).
- **Una política `PROJECT` sin umbrales de contexto sigue sin colores** hasta que alguien corre
  `presupuesto --context-defaults`. Es a propósito, y `setup` lo dice.
