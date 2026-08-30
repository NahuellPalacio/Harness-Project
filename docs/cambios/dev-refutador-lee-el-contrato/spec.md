# `dev-refutador` lee `project-context.json` como evidencia

**Estado:** especificado · **Fecha:** 2026-08-29

## Qué problema resuelve

`project-context.json` se escribe desde el 24-08-2026 —pasos 1, 2 y 4 del contrato
`PROJECT_CONTEXT`— y **no lo lee nadie**. `Pendientes/Ideas-Harness/PENDIENTES-I.md` mapeó, campo
por campo, qué haría `dev-refutador` con cada uno, y cerró con una recomendación explícita: darle
al contrato su primer lector antes de seguir modelando pasos 3 y 5. Ese mapeo es la fuente de este
cambio; acá no se inventa un mapeo nuevo, se implementa el que ya existe.

Hoy `dev-refutador` verifica código contra la norma sin ninguna noción de **de qué snapshot del
proyecto** está hablando: su fila de salida no dice contra qué commit rindió, no puede distinguir
un `cumple` de hace tres meses de uno de hoy, y para saber si Obelisco aplica o si hay OpenAPI que
citar tiene que grepear el repositorio entero en cada corrida —el mismo trabajo que el contrato
existe para no repetir.

## Qué queda afuera

- **El eje regulatorio —qué estándar y qué versión rigen el proyecto.** `PENDIENTES-I.md` ya lo
  encontró y lo dejó **sin decidir** entre dos formas —un bloque `compliance` nuevo, o un valor
  `standard` en `sources[].type`—. Elegir acá sería inventar la decisión que ese documento dice
  explícitamente que no está tomada. `dev-refutador` sigue sacando qué estándar aplica de las
  skills `dev-*`, como hace hoy; el contrato no le agrega ni le saca nada en ese eje.
- **El eje de gobierno del repositorio —ramas, tags, `CHANGELOG.md`/`UPGRADE.md`.** Mismo
  documento, mismo hallazgo: el contrato emite un solo hecho de git, `meta.repo_revision`, y nada
  de `sources[].type` describe un entregable. `dev-refutador` sigue verificando eso —cuando lo
  verifica— sin ayuda del contrato.
- **`business_rules[]` y `quality_landscape`.** El schema v1.1 no los modela —pasos 3 y 5, sin
  construir— y aunque los modelara no le servirían: son territorio de `dev-qa`, no de
  `dev-refutador`, según la distinción que el propio `PENDIENTES-I.md` traza entre los dos ejes
  —norma contra implementado, no esperado contra implementado—.
- **Ejecutar nada.** `dev-refutador` declara `tools: Read, Grep, Glob, Skill` y la fila de
  `PENDIENTES-I.md` lo dice de frente: *"Executes: nothing. It only reads."* Este cambio no le
  agrega `Bash` ni ninguna herramienta de ejecución. Un script que valide el contrato por él sería
  exactamente esa herramienta con otro nombre — ver la decisión de abajo.
- **Tocar `PreToolUse` o `PostToolUse`.** El consumidor es `dev-refutador`; los hooks no cambian de
  responsabilidad.
- **Un mecanismo automático que reintente construir cuando el refutador contradice.** El ciclo
  vuelve a "construir" porque alguien lo retoma, igual que en todo el resto del método —
  [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md), regla 2: *"el ciclo lo abre la
  persona"*. Lo que este cambio agrega es que el retorno sea **explícito y legible**, no que se
  dispare solo.

## Las decisiones, y por qué

### El contrato es evidencia, nunca norma — se lee, no se cita como regla

Es la instrucción explícita del pedido y coincide con lo único que `dev-refutador` puede hacer sin
dejar de ser lo que es: *"De las skills `dev-*` del harness, no de tu memoria"* sigue siendo de
dónde sale la regla. Lo que el contrato aporta es **de qué proyecto** se está hablando —su stack,
sus componentes, sus interfaces, sus ambientes— para decidir **si** una regla aplica y **dónde**
mirar, nunca **qué dice** la regla.

### No hay script intermediario. `dev-refutador` lee el JSON con `Read`, como lee todo lo demás

Se evaluó un script —`comun/bin/leer-contrato.py` o reusar `validar()`/`cargar_schema()` de
`contexto-armar.py`— que `dev-refutador` correría para obtener un veredicto estructurado sobre el
contrato antes de usarlo. **Se descartó.** `dev-refutador` no tiene `Bash` ni `PowerShell` en su
lista de herramientas, y dársela para este único fin contradice la fila de `PENDIENTES-I.md` que
motiva el cambio: *"Executes: nothing."* Convertirlo en un agente que ejecuta un validador —aunque
sea de sólo lectura— es un cambio de naturaleza que este pedido no autoriza y que nadie decidió.

La consecuencia se acepta a propósito: **si el archivo no parsea como JSON o no es evidente que
cumple el schema, es el modelo el que tiene que darse cuenta leyéndolo**, no un validador
determinista. Eso es exactamente lo que la sección siguiente convierte en instrucción explícita.

### Contrato ausente, no parseable o que no valida: hueco, nunca inferencia

Es la misma asimetría que gobierna todo lo demás en este harness —`gaps_and_conflicts`, los
`knowledge_status`, la regla que ya tiene `dev-refutador` sobre `sin-verificar`—: marcar de más
cuesta una relectura; inventar de más viaja con el sello puesto. Se aplica literal: sin contrato,
con un contrato roto, o con uno que no alcanza a explicar algo, las conclusiones que dependieran de
eso son `sin-verificar` y se dice por qué — nunca se completa con lo que "probablemente" dice el
proyecto.

### La fila de salida suma una columna: el `repo_revision` contra el que se rindió

Es exactamente lo que pide el `Cost.` de `PENDIENTES-I.md`: *"a column in its output row naming
the `repo_revision` it ruled against."* Sin eso, un `cumple` no dice de cuándo es. Con contrato
ausente, la columna se completa `—` y no se inventa un valor.

### `dev-refutador` lee el contrato **antes** de grepear, no en vez de grepear

También del `Cost.`: *"a step that reads the contract before grepping."* El contrato acota el
alcance —qué componentes, qué stack, qué interfaces existen según el último recorrido—; no
reemplaza mirar el código real, que sigue siendo la única fuente de la línea que cada `cumple`
tiene que poder señalar.

### El cambio en el prompt es un archivo, y un archivo es mecanismo — no es territorio de `lectura`

[ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md) traza la
frontera exacta: *"si el sujeto es un archivo... hay mecanismo posible y la marca no corresponde."*
Que `dev-refutador.md` instruya leer el contrato antes de grepear, que llame al contrato evidencia
y no norma, y que la fila de salida tenga la columna nueva son propiedades del **texto del
archivo**, verificables con `Read`/`grep` sin invocar ningún modelo. Sólo el comportamiento real de
una corrida —¿el agente *de verdad* cita el contrato así, contra un proyecto real?— es sujeto de un
modelo y va por lectura. Son escenarios separados en la sección de abajo, y por esa razón.

### `harness-spec-refuter` verifica este cambio; no lo verifica quien lo construye

Regla general del método, dicha para que quede explícita en esta spec: la implementación de este
cambio la hace quien lo construye, y el veredicto lo emite `harness-spec-refuter` en una pasada
aparte, después, sobre el código ya escrito — igual que en `interfaces-identidad-ambientes`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/agents/dev-refutador.md` | Un paso nuevo antes de "De dónde sacás la norma": leer `docs/codebase/project-context.json` si existe, usarlo como evidencia acotando alcance y aplicabilidad, nunca como norma. La fila de salida suma la columna `repo_revision`. Instrucción explícita para contrato ausente/roto/insuficiente → hueco declarado, `sin-verificar` en lo que dependía de él |
| `tests/casos/16_refutador_contrato.py` | Escenarios mecánicos sobre el **texto** del prompt: qué instruye, qué no toca |
| `tests/casos/13_contexto.py` | Un escenario nuevo: una corrida cuya salida no valida no toca un `project-context.json` válido preexistente |
| `docs/cambios/dev-refutador-lee-el-contrato/lectura.md` | Los dos escenarios cuyo sujeto es una corrida real de `dev-refutador`, sin firmar hasta que alguien que no construyó los lea |

## Escenarios verificables

### El script — lo único de este cambio que toca `contexto-armar.py`

- **E-01** — Un directorio con un `project-context.json` **válido** ya escrito recibe una segunda
  corrida cuyas fichas producen un documento que **no** valida contra el schema: el script sale
  distinto de 0, nombra el error, y el `project-context.json` preexistente queda **byte a byte
  igual y con el mismo `mtime`** que antes de la corrida. · rojo visto: si

  📌 Es el único hueco real que dejó section 2 del pedido: `escribir()` sólo se llama después de
  `validar()` sin errores —confirmado leyendo `contexto-armar.py:1030-1038`—, así que esta
  propiedad ya es cierta hoy. Lo que faltaba era el test que lo dijera; nada del script cambia.

  🔴 **El primer `rojo visto` de este escenario era timing-dependiente, y `harness-spec-refuter` lo
  encontró el 29-08-2026.** Reprodujo la mutación con la misma técnica que ya usa `E-07`
  —`exigir_lo_imposible`, un campo `required` imposible en el schema de `_bin_falso`— y notó que esa
  técnica no cambia nada de lo que `armar()` calcula: la segunda corrida produce un documento
  funcionalmente idéntico al primero, salvo `meta.generated_at`, que tiene resolución de un
  segundo. Si las dos corridas caían dentro del mismo segundo de reloj, los bytes coincidían igual
  **aunque el bug estuviera presente**, y el test pasaba por casualidad de timing. Repitió la
  mutación tres veces: cayó una de tres: en las otras dos, el único test que atrapó la regresión
  fue `E-07`, sobre un directorio vacío — no el escenario nuevo.

  El escenario se corrigió sumando el `mtime` del archivo **en nanosegundos**, capturado antes y
  después de la segunda corrida. Una reescritura real siempre mueve el `mtime` a nivel de sistema
  operativo, coincida o no el contenido por el segundo compartido de `generated_at`. Verificado con
  la mutación repetida cinco veces seguidas: la comparación de bytes sola pasó por casualidad **2 de
  5**; la del `mtime` cayó **5 de 5**.

### El prompt de `dev-refutador` — propiedades de un archivo, mecánicas

- **E-02** — El archivo instruye leer `docs/codebase/project-context.json` **antes** de invocar una
  skill o grepear el repositorio, condicionado a que el archivo exista. · rojo visto: si
- **E-03** — El archivo dice, en una frase que no admite otra lectura, que el contrato es
  **evidencia** y que la norma sigue saliendo únicamente de las skills `dev-*`. · rojo visto: si
- **E-04** — El archivo instruye: contrato ausente, no parseable, o que no valida contra
  `comun/schemas/project-context.schema.json` → se declara el hueco y las conclusiones que
  dependieran de él son `sin-verificar`. En ningún caso instruye completar con inferencia.
  · rojo visto: si
- **E-05** — El formato de salida que el archivo especifica suma una columna que nombra el
  `repo_revision` del contrato usado, o `—` cuando no hubo contrato. · rojo visto: si
- **E-06** — El archivo sigue exigiendo, sin excepción nueva, que un `cumple` cite la regla **y**
  señale la línea — la cita de un campo del contrato no alcanza por sí sola para declarar `cumple`
  de nada. · rojo visto: si

### Lo que ya existía y no se rompe

- **E-07** — `dev-refutador` sigue sin tener `Bash`, `PowerShell` ni ninguna herramienta de
  ejecución en su frontmatter. · rojo visto: si

### Lo que sólo se puede leer

- **E-08** — Sobre un proyecto real con `project-context.json` completo, una corrida real de
  `dev-refutador` efectivamente lee el contrato, lo usa para acotar alcance y aplicabilidad, lo
  cita como evidencia y no como norma, y su fila de salida nombra el `repo_revision` correcto.
  · rojo visto: no consta · verificación: lectura — el sujeto es una corrida de un modelo, y la
  suite no invoca al agente
- **E-09** — Sobre un proyecto sin `project-context.json`, o con uno roto a propósito, una corrida
  real declara `sin-verificar` lo que dependía del contrato, lo dice explícitamente, y no completa
  ningún campo por inferencia. · rojo visto: no consta · verificación: lectura — mismo motivo que
  E-08

## Cómo se verifica

**Por la suite, E-01 a E-07.** E-01 es una propiedad de `contexto-armar.py` sobre una fixture
escrita a mano. E-02 a E-07 son propiedades del **texto** de `dev-refutador.md` —presencia o
ausencia de instrucciones y de herramientas—, verificables con `Read`/regex sin invocar ningún
modelo; ADR-0009 no aplica porque el sujeto es un archivo, no una corrida.

**Por lectura, E-08 y E-09 solamente**, según
[ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md). Los firma
alguien que no construyó, con fecha, sobre una corrida real de `dev-refutador` contra un proyecto
con contrato y contra uno sin él.

## Riesgos conocidos

- **Sin script validador, la robustez de `dev-refutador` ante un contrato roto depende del
  modelo, no de un mecanismo.** Es la decisión de este cambio y está escrita arriba con su motivo;
  el costo es real: un modelo que no note un JSON corrupto puede citar campos de un documento a
  medio escribir. E-09 es la única defensa, y es lectura, no test.
- **El eje regulatorio sigue sin lugar en el contrato.** Este cambio no lo resuelve —lo declara
  fuera de alcance a propósito, ver arriba— y `dev-refutador` sigue sin poder decir, desde el
  contrato, contra qué versión de qué estándar está rindiendo. Sigue en `PENDIENTES-I.md`.
- **E-02 a E-06 prueban que el prompt lo *dice*, no que una corrida real lo *hace*.** Es la
  distinción que sostiene toda la spec —ADR-0009— y por eso E-08/E-09 existen aparte. Un cambio
  futuro al prompt podría dejar la instrucción escrita y el comportamiento real desalineado sin que
  la suite se entere; sólo una lectura nueva lo vuelve a mirar.
- **`tests/casos/16_refutador_contrato.py` no tiene precedente en este repositorio** —es el primer
  archivo que verifica el contenido de un prompt de agente en vez de código—. Si el patrón resulta
  frágil (un reordenamiento de prosa que no cambia el significado rompe el test), el costo de
  ajustarlo es de quien construya la próxima vez que se edite `dev-refutador.md`.
