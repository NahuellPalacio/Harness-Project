# WCAG 2.2 con Obelisco V2: criterios verificables, referencias por tarea y un check que no adivina

**Estado:** especificado · **Fecha:** 2026-10-23

## Qué problema resuelve

El harness dice que la accesibilidad es condición de aprobación (el bloque de `CLAUDE.md` que se carga
siempre, el docstring del check), y lo que tiene para sostenerlo es una skill de 587 líneas que se carga
entera cada vez que se la invoca (12.573 caracteres, unos 3.143 tokens), un check de cuatro reglas sobre
HTML, y la palabra «WCAG» en dos skills. Hoy no puede responder tres preguntas:

1. **Qué exige WCAG 2.2 de esta pantalla, y qué exige Obelisco además.** `dev-accessibility` cita
   Obelisco y WCAG sin decir cuál es cuál; `normativa/extractos/Obelisco.md` mezcla en un mismo checklist
   criterios A, AA y dos AAA (2.4.13 y 3.1.5) bajo un «niveles AA-AAA» que no define cuáles AAA.
2. **Qué comprobó una máquina y qué no.** El check mira cuatro cosas y se calla. Nadie registra, criterio
   por criterio, qué se aprobó, qué falló, qué no aplica y qué no se probó. Una pasada limpia del check
   se lee como «accesible».
3. **Si el propio check acierta.** Medido sobre el código actual:
   - Un control con `id` pasa aunque ninguna `<label>` lo apunte: el `id` se toma por nombre.
   - Un control correctamente envuelto en `<label>` y sin `id` se reporta como defecto.
   - `aria-labelledby="no-existe"` cuenta como nombre.
   - «Va un solo `<h1>`» sale como hallazgo `[a11y]`, con el mismo peso que una imagen sin `alt`. WCAG 2.2
     no exige un único `<h1>`.
   - Solo analiza `.html`, `.blade.php` y `.component.html`: un `.tsx` no se mira y no se dice que no se miró.

La skill `wcag22` que el usuario aportó resuelve la mitad de esto (los 86 criterios, técnicas, plantilla
de informe, dos scripts) y trae sus propios defectos, verificados contra `wcag.json` del W3C:

- **Tres conteos distintos para lo mismo.** `SKILL.md` dice «87 criterios (86 testables)» y «A = 32
  (31 testables)»; `references/checklist.md` dice «A = 32 (30 testables + 4.1.1 removido)». El W3C lista
  **86** criterios con nivel: **A 31 · AA 24 · AAA 31**. 4.1.1 Parsing figura en el JSON del W3C como
  «Obsolete and removed», **sin nivel**: no es un criterio A más.
- **`scripts/contrast_ratio.py` no corre en Python 3.9**, la versión mínima del harness (`install.ps1:503`,
  `docs/contrato-hooks.md`): anota `float | None` sin `from __future__ import annotations`, y eso explota al
  definir la función. Además descarta la transparencia: `#rrggbbaa` y `rgba()` se leen como opacos.
- **`scripts/html_quick_check.py`** acepta `aria-labelledby` si el id existe aunque el elemento no tenga
  texto, y reporta «sin `<h1>`» como si fuera 1.3.1 nivel A.

La evaluación que acompaña a la skill (`wcag22-eval-review.html`, 3 evals, una corrida por configuración)
mide, con y sin la skill cargada entera: tasa de aprobación 0,963 contra 0,967 (diferencia −0,00), tokens
138.813 contra 82.764 (+56.049, +67,7 %), tiempo 388 s contra 218 s (+170 s); 25 de 26 asertos de cada lado.
El único aserto que la skill perdió y el modelo sin ella pasó es el de los niveles correctos del modal:
escribió **«1.3.4 Orientation (Level A)»** (es AA), la confusión que su propio `SKILL.md` advierte. Dos
conclusiones se desprenden y orientan este cambio: cargar el conocimiento entero cuesta más y no mejoró lo
medido, y lo que sí falla se arregla con un control determinista (una tabla de niveles contra la que
contrastar un texto), no con más prosa. Son tres evals con una corrida cada una: indican, no prueban.

## Qué queda afuera

- **Correr un navegador, un teclado o un lector de pantalla.** El harness no lanza Playwright, axe ni NVDA.
  Esas tres pruebas se registran como `not_performed` hasta que alguien las haga. Cablear su ejecución es
  otro cambio.
- **Sacar pares de contraste del CSS.** Requiere la cascada renderizada: un color de `:hover` sobre un fondo
  heredado. Adivinarlo da certeza falsa. `contrast.py` calcula los pares que se le dan y dice cuándo no
  puede.
- **Declarar conformidad legal.** Ley 26.653, resolución 94/SECITD/23 y criterios de la ASI se citan como
  Obelisco los cita; no se interpretan ni se certifican.
- **Cambiar `normativa/extractos/Obelisco.md`.** Es un extracto del PDF con su propio contrato de citas. La
  matriz de componentes se arma desde las páginas publicadas del sistema de diseño y cita cada una.
- **Los componentes de Obelisco que no tienen página de accesibilidad propia** quedan con
  `obelisco_sc: []` y requisitos de origen `wcag` o `harness`. No se inventa lo que Obelisco no dice.
- **Otros formatos.** Vue, Svelte, Razor, `.js`/`.ts` con plantillas en cadenas, CSS-in-JS, Markdown, PDF.
  El check los ignora; la revisión completa los lista como no analizados si se le pasan.
- **El texto de `bloque.md`** (la zona del `CLAUDE.md` que se carga siempre). No crece: lo que se necesita
  «a veces» va en la skill.
- **Medir calidad de salida de un modelo con y sin este cambio.** No hay una evaluación comparable (las
  evals de la skill adjunta usan archivos que no vienen en el HTML). Se mide lo determinista: tamaños
  cargados y un corpus etiquetado de HTML, plantillas y JSX. No se afirma «mejor calidad» del modelo.
- **Cerrar la versión.** No se toca `VERSION`, `CHANGELOG.md`, `UPGRADE.md` ni `docs/versiones/`: 0.36.0
  está reservada a la limpieza de 6.1 (en pausa) y cerrar es otro ritual (`close-a-version`). Enmienda del
  24-10-2026: la versión se cerró después, por decisión del usuario, como 0.36.0 y con su propio ritual; la
  limpieza de 6.1 pasa a 0.37.0. Nada de eso cambia un escenario.
- **Traducir el texto normativo del W3C.** Se importa tal cual, en inglés, con su fuente.

## Las decisiones, y por qué

### El objetivo base es WCAG 2.2 AA, propuesto, y los AAA de Obelisco son adicionales y con nombre

AA significa A + AA: 55 criterios. Es una propuesta del harness, no una exigencia que un documento haya
fijado: el checklist de Obelisco dice «WCAG 2.2 en los niveles AA-AAA» y no define cuáles AAA. Se leyó así:
los AAA que Obelisco **nombra** (2.4.13 Focus Appearance, 3.1.5 Reading Level, 2.2.5 Re-authenticating, y los
que sus fichas citan, como 1.4.6 y 2.4.8) se llevan como `adicionales`, con su nivel real a la vista; los
demás AAA no son exigibles. Quien quiera otro objetivo lo declara en el registro (`target.level`,
`target.additional`). Se descartó «AAA completo»: el W3C no lo recomienda como política general y haría
imposible un `pass` honesto.

### Una sola fuente para conteos y niveles, y un testigo externo para vigilarla

`references/wcag22-criteria.json` es la única fuente de niveles, nombres y conteos. Nada de lo que se
escribe en una skill o en un test lleva el 86 a mano. El test lo contrasta contra
`tests/fixtures/wcag22-w3c.json`, extraído de `https://www.w3.org/WAI/WCAG22/wcag.json` (con su hash): si
alguien «corrige» un nivel en el JSON del harness, el testigo lo contradice. 4.1.1 vive aparte, en
`removed`, sin nivel.

### El conocimiento se consulta, no se carga

`SKILL.md` queda como entrada: qué es, las tres fuentes, el flujo y una tabla «tarea → referencia». Las guías
por tarea son cortas. El texto normativo largo —importado de la skill adjunta y verificado— está en
`references/wcag22/`, y `scripts/wcag.py criterion 2.4.11` imprime **solo** la sección de ese criterio.
Cargar la skill adjunta entera serían 476.544 bytes (~118.856 tokens); consultar un criterio, unos pocos
miles de caracteres.

### Tres fuentes, nunca mezcladas en una misma frase

Cada requisito lleva `origin`: `wcag` (texto normativo del W3C), `obelisco` (lo que el sistema de diseño
publica para ese componente) o `harness` (regla propia del harness o del proyecto). Cuando Obelisco cita un
criterio, se guarda con el nivel que Obelisco declara **y** el nivel real, y una discrepancia se registra, no
se corrige en silencio.

### El check liviano solo dice lo que el archivo decide, y la revisión completa dice todo lo demás

`dev-accesibilidad-html.py` corre tras cada escritura y paga latencia en cada turno, y su presupuesto de
ocho avisos es compartido. Reporta solo lo inequívoco: un `fallo` (incumple un criterio por evidencia
estática) o un `defecto` (marcado roto, con efecto probable en accesibilidad). No reporta `probable` ni
`recomendacion`. La revisión completa (`scripts/review.py`) corre cuando el alcance de la tarea lo pide
—un formulario nuevo, una pantalla, un componente— y reporta los cuatro tipos y la cobertura.
Un `<h1>` único es una **recomendación**, no un fallo: sale solo de la revisión completa, sin criterio WCAG.

### Un control con `id` y sin etiqueta: fallo en un documento, defecto en un fragmento

Un parcial, un componente o un JSX no ven el documento entero. Una `<label for="x">` puede estar en la
plantilla padre. Dentro de un documento completo que no arma partes con otros archivos, `id` sin
`<label for>` es un **fallo** de 4.1.2: el `id` solo no es un nombre. Dentro de un fragmento es un
**defecto** (`control-label-missing-in-file`), con el aviso de que la etiqueta puede vivir en otro archivo:
callar ese caso, que es justo el que el pedido señala, dejaría la regla vieja con otro nombre. Y no se decide
nada —es `undeterminable`, «no determinable», solo para la revisión completa— cuando el control está dentro de un componente
propio, el `id` es una expresión, hay una `<label for>` dinámica o el archivo incluye otros. Lo que el motor
no puede interpretar —un componente propio `<TextField />`, un `{...props}`— se registra como **no
analizado**, no se adivina.

### Un análisis estático no aprueba nada

La revisión completa puede producir `fail` con línea y evidencia. Lo que no falla queda `not_tested` con la
nota «estática sin hallazgos». Un `pass` exige evidencia y, si el criterio la requiere según el catálogo,
que la prueba de navegador, teclado o lector de pantalla figure como `performed`. Qué prueba requiere cada
criterio es una **regla propia del harness** (derivada del flujo de auditoría de la skill adjunta), conservadora,
y está en el JSON de criterios.

### Contraste: componer la transparencia o decir que no se puede

Un primer plano con alfa se compone sobre el fondo opaco en sRGB antes de calcular. Un fondo translúcido
exige una base (`--backdrop`); sin ella el script **no da un número**: dice qué le falta. Lo mismo para
`currentColor`, `var(--x)`, `inherit` y los nombres de color que no conoce.

### Python 3.9 se vigila por árbol sintáctico, y se corre de verdad si hay un 3.9

Hay un solo intérprete en esta máquina (3.12). El test recorre el AST de cada script nuevo con
`feature_version=(3, 9)`, prohíbe anotaciones con `|` sin `from __future__ import annotations` y un puñado de
APIs de 3.10 o posterior. Si el entorno tiene un 3.9 (`HARNESS_PYTHON39`), los scripts se ejecutan con él. Que
no haya uno se **dice**; no se da por pasado en silencio.

### Los nombres de contrato van en inglés, lo que lee una persona va en español

ADR-0011. Campos y valores del registro (`pass`, `fail`, `not_applicable`, `not_tested`), comandos y
referencias, en inglés; avisos del check, salidas de los scripts que lee una persona y `docs/`, en español,
con «aprobado / fallido / no aplicable / no probado» como etiquetas.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/skills/dev-accessibility/SKILL.md` | Reescrita como entrada: fuentes, objetivo, flujo, tabla tarea → referencia, estados |
| `.../dev-accessibility/references/wcag22-criteria.json` | Los 86 criterios, `removed` (4.1.1), pruebas requeridas por criterio. Fuente única |
| `.../references/obelisco-matrix.json` | Componente/patrón de Obelisco → criterios que declara, requisitos adicionales con origen, verificación |
| `.../references/scope-and-sources.md` | Objetivo, las tres fuentes, tratamiento de AAA y de 4.1.1 |
| `.../references/task-*.md` | Guías cortas: formularios, teclado y foco, color y contraste, estructura y semántica, dinámico y medios |
| `.../references/evidence-register.md` | Formato del registro, vocabulario, reglas de validación, correspondencia con las etiquetas en español |
| `.../references/static-coverage.md` | Qué mira el análisis estático, por formato y por regla; qué no |
| `.../references/wcag22/*.md` | Texto normativo, pruebas y técnicas por principio, glosario, conformidad, propósitos de entrada (importados y corregidos); `SOURCE.md` con procedencia |
| `.../scripts/wcag.py` | `criterion`, `list`, `task`, `component`, `term`, `count`, `levels`, `register` |
| `.../scripts/contrast.py` | Contraste con transparencia compuesta, o la limitación dicha |
| `.../scripts/review.py` | Revisión completa estática (HTML, plantillas, JSX/TSX), cobertura, borrador de registro |
| `harnesses/desarrollo/checks/lib/a11y.py` | El motor: tokenizadores HTML y JSX, nombre accesible, reglas con criterio, nivel y tipo |
| `harnesses/desarrollo/checks/dev-accesibilidad-html.py` | El check liviano, sobre el motor; solo `fallo` y `defecto` |
| `harnesses/desarrollo/skills/dev-ui/SKILL.md` | Cada elección de componente enlaza su criterio y su verificación (`accessibilityLinks`) |
| `harnesses/desarrollo/skills/dev-responsive/SKILL.md` | Zoom, reflow, espaciado y tamaño de objetivo con sus umbrales y su verificación |
| `harnesses/desarrollo/skills/dev-frontend-implementation/SKILL.md` | El orden `dev-ui` → `dev-accessibility` → `dev-responsive` y la entrega del registro |
| `harnesses/desarrollo/agents/dev-frontend.md` | Coordina y entrega la evidencia de accesibilidad |
| `docs/accesibilidad.md` | Para personas: las tres fuentes, el objetivo, el flujo y un formulario de punta a punta |
| `docs/codebase/checks.md` | La ficha del check, al día |
| `tests/fixtures/wcag22-w3c.json` | El testigo del W3C: id, nombre, nivel y técnicas citadas, con el hash de su origen |
| `tests/fixtures/a11y/corpus.json` | Corpus etiquetado de HTML, plantillas y JSX con lo que debe y no debe reportarse |
| `tests/fixtures/paridad-checks.json` | El caso de `dev-accesibilidad-html` pasa a decir lo nuevo (la paridad con PowerShell se rompe a propósito) |
| `tests/casos/08_checks_borde.py` | La prueba de `dev-accesibilidad-html` sigue el cambio |
| `tests/casos/78_wcag22_obelisco.py` | Los escenarios que no instalan |
| `tests/casos/78-wcag22-obelisco-instalador.ps1` | Los que instalan, actualizan y desinstalan de verdad |
| `tests/parallel-manifest.json` | Las dos suites nuevas |
| `tests/casos/61_conocimiento_auto_refresco.py` (E-02), `64_modelo_de_dominio.py` (E-16), `72_motor_de_ejecucion.py` (ME-E49), `74_knowledge_api.py` (KA-E53), `63-harness-unico-instalador.ps1` (E-15 y E-16) | Enmienda posterior a la construcción, encontrada por la compuerta y no por esta spec: guardas de Tasks cerradas que fijaban «agentes y skills sin cambios», la huella de una skill o el inventario exacto del lock. Se adaptan, con «Pisado por», a que este cambio modifica a propósito el agente de frontend y cuatro skills y suma 23 archivos instalables; se saltean esas piezas y nada más |

## Escenarios verificables

### Los criterios, una sola fuente

- **E-01** — `wcag22-criteria.json` tiene exactamente 86 criterios, 31 de nivel A, 24 AA y 31 AAA, con ids
  únicos, y coincide con `tests/fixtures/wcag22-w3c.json` en id, nombre y nivel de cada uno.
  · rojo visto: si
- **E-02** — 4.1.1 no está entre los 86: figura en `removed` sin nivel y con el motivo, y ningún criterio de
  los 86 lleva nivel vacío.
  · rojo visto: si
- **E-03** — Los nueve criterios nuevos de 2.2 —2.4.11 AA, 2.4.12 AAA, 2.4.13 AAA, 2.5.7 AA, 2.5.8 AA, 3.2.6 A,
  3.3.7 A, 3.3.8 AA, 3.3.9 AAA— llevan `new_in_22: true` y ningún otro.
  · rojo visto: si
- **E-04** — Ningún archivo de `dev-accessibility/` (SKILL.md, guías, referencias importadas) ni las skills
  `dev-ui`, `dev-responsive` y `dev-frontend-implementation` afirma un conteo distinto de 86 (A 31 · AA 24 ·
  AAA 31): no aparecen «87 criteria», «87 success criteria», «A = 32», «Level A = 32» ni «30 testable».
  · rojo visto: si
- **E-05** — `wcag.py count` imprime 86, 31, 24 y 31, y esos números salen del JSON: con un criterio quitado del
  JSON, el conteo cambia.
  · rojo visto: si
- **E-06** — Cada criterio declara `requires` con valores solo de `browser`, `keyboard` y `screen_reader`
  (puede estar vacío). 2.1.1, 2.1.2 y 2.4.7 requieren `keyboard`; 1.4.10 y 2.5.8 requieren `browser`; 4.1.3
  requiere `screen_reader`.
  · rojo visto: si

### Consultar sin cargar todo

- **E-07** — `wcag.py criterion 2.4.11` imprime nombre, nivel y texto normativo de ese criterio, ninguna de las
  secciones de 2.4.10 ni de 2.4.12 (el texto de 2.4.11 nombra a 2.4.12 como criterio relacionado: es un dato del
  W3C), y menos de 6.000 caracteres.
  · rojo visto: si
- **E-08** — `wcag.py criterion 4.1.1` dice que fue retirado en 2.2, que no tiene nivel, y manda los defectos de
  marcado a 1.3.1 y 4.1.2.
  · rojo visto: si
- **E-09** — `wcag.py criterion 9.9.9` sale con código distinto de 0, dice que el criterio no existe y no
  imprime un traceback.
  · rojo visto: si
- **E-10** — `wcag.py list --level AA` lista los 24 AA y ninguno más; `--up-to AA` lista 55; ambos con nombre y
  nivel.
  · rojo visto: si
- **E-11** — `wcag.py task forms` devuelve el conjunto de criterios y el archivo de guía de esa tarea; cada
  tarea de la tabla de `SKILL.md` se resuelve y apunta a un archivo que existe.
  · rojo visto: si
- **E-12** — `wcag.py component form-text` imprime la fila de Obelisco: los criterios que la página declara con
  el nivel declarado, los requisitos adicionales con su origen y cómo se verifica.
  · rojo visto: si
- **E-13** — Cada archivo que la tabla de `SKILL.md` nombra existe, y cada archivo de `references/` (salvo los
  de `wcag22/`, listados por `SOURCE.md`) está nombrado en la tabla: no hay referencias huérfanas.
  · rojo visto: si
- **E-14** — `dev-accessibility/SKILL.md` no pasa de 8.000 caracteres (hoy 12.573), y lo que se carga para una
  tarea de formularios —`SKILL.md` más la guía de formularios— no pasa de los 12.573 que cargaba la skill
  anterior.
  · rojo visto: si
- **E-15** — La suma del `name` y la `description` de `dev-accessibility`, `dev-ui`, `dev-responsive`,
  `dev-frontend-implementation` y `dev-frontend` no crece más de 20 tokens (1 token cada 4 caracteres) respecto de
  los 591 de hoy.
  · rojo visto: si

### Tres fuentes, niveles a la vista

- **E-16** — Cada requisito de `obelisco-matrix.json` lleva `origin` en {`wcag`, `obelisco`, `harness`}; los de
  origen `obelisco` traen la página de la que salen y su fecha de consulta.
  · rojo visto: si
- **E-17** — Todo criterio de nivel AAA que la matriz cita (los de Obelisco incluidos) figura en
  `aaa_additional`, nunca en el conjunto base de AA, y cada uno dice quién lo pide. Entre ellos están 2.4.13,
  3.1.5, 2.2.5 y 1.4.6.
  · rojo visto: si
- **E-18** — Para cada criterio que la matriz toma de Obelisco, el nivel que Obelisco declara es el nivel real
  de WCAG 2.2, o la discrepancia está registrada en `discrepancy` con lo que dice cada lado.
  · rojo visto: si
- **E-19** — La matriz cubre al menos los componentes y patrones que tocan un formulario o una pantalla de
  trámite: campo de texto, selección, casilla, radio, búsqueda, carga de archivo, validación, botón, enlace,
  modal, tabla, pestañas, alerta y mensaje de estado, tooltip, paginado, migas de pan, colapsable, navegación,
  encabezado, pie, pasos de un formulario y grilla. Cada fila tiene `obelisco_page`, requisitos y
  `verification`; cada regla estática que cita existe en el motor; cada familia manual está en el vocabulario.
  · rojo visto: si
- **E-20** — La matriz tiene la fila `custom` para UI sin componente de Obelisco: exige nombre, rol y estados,
  modelo de teclado y de foco explícitos, y su verificación incluye las tres pruebas manuales.
  · rojo visto: si
- **E-21** — `dev-accessibility/SKILL.md` nombra las tres fuentes (WCAG normativo, lineamientos de Obelisco, reglas
  del harness y del proyecto), propone AA como objetivo, dice que los AAA de Obelisco son adicionales y que la
  skill no certifica conformidad.
  · rojo visto: si

### El registro de evidencia

- **E-22** — `wcag.py register template --level AA` genera un registro con los 55 criterios A y AA en
  `not_tested`, 4.1.1 en `not_applicable` con su motivo, y navegador, teclado y lector de pantalla en
  `not_performed`.
  · rojo visto: si
- **E-23** — Validar un registro al que le falta un criterio del nivel objetivo falla y nombra el criterio: no se
  omite nada en silencio.
  · rojo visto: si
- **E-24** — Validar un registro con un resultado fuera de `pass`, `fail`, `not_applicable` y `not_tested` falla.
  · rojo visto: si
- **E-25** — Un criterio `fail` sin ubicación, sin evidencia o sin corrección propuesta se rechaza, y dice cuál
  falta.
  · rojo visto: si
- **E-26** — Un `pass` sobre un criterio que requiere `keyboard` se rechaza mientras `tests.keyboard` sea
  `not_performed`; se acepta cuando es `performed` y la evidencia del criterio dice que fue de teclado. Un `pass`
  sin evidencia se rechaza siempre.
  · rojo visto: si
- **E-27** — `not_applicable` y `not_tested` sin `reason` se rechazan.
  · rojo visto: si
- **E-28** — 4.1.1 como `fail` o como `pass` se rechaza; solo puede ser `not_applicable`.
  · rojo visto: si
- **E-29** — Si el registro trae un `summary`, sus cuatro conteos (aprobados, fallidos, no aplicables, no probados)
  tienen que coincidir con las filas que el objetivo exige, y si trae `fail_by_level`, los fallidos por nivel también
  (el error de declarar 13 de nivel A y 12 de AA cuando las filas dan 14 y 11).
  · rojo visto: si
- **E-30** — Un registro con `target.additional` pide una fila por cada criterio adicional, y uno AAA que no está
  entre los adicionales no se exige; si aparece, se acepta y se cuenta aparte.
  · rojo visto: si
- **E-31** — `wcag.py levels ARCHIVO` marca «1.3.4 Orientation (Level A)» como par incorrecto (es AA), acepta el
  correcto, marca un número que no existe (5.1.1) y marca 4.1.1 con un nivel; entiende la forma `SC n.n.n … (Level X)` y
  la de tabla `| n.n.n | nombre | X |`.
  · rojo visto: si
- **E-32** — `wcag.py levels` aplicado a `SKILL.md` y `references/*.md` de `dev-accessibility` y a las tres skills
  de frontend que tocan WCAG no marca ningún par: ningún nivel mal escrito en lo que se carga.
  · rojo visto: si

### Contraste

- **E-33** — `contrast.py` da 21:1 para negro sobre blanco, 4,48:1 para `#777` sobre `#fff` y 4,54:1 para `#767676`
  sobre `#fff`; para entradas opacas, lo mismo que el script original.
  · rojo visto: si
- **E-34** — Un primer plano con alfa se compone sobre el fondo antes de calcular: `rgba(0,0,0,0.5)` sobre blanco
  da 3,95:1 (el color compuesto es `#808080`), no 21:1.
  · rojo visto: si
- **E-35** — Entiende `#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, `rgb()` y `rgba()` con comas o con espacios y barra,
  alfa en número o en porcentaje, `hsl()` y `hsla()`, y los nombres de color básicos.
  · rojo visto: si
- **E-36** — Un fondo con alfa menor a 1 sin `--backdrop` no produce un número: sale con código 2 y dice que
  falta la base. Con `--backdrop` compone los dos niveles y calcula.
  · rojo visto: si
- **E-37** — `currentColor`, `var(--x)`, `inherit`, `transparent` como fondo y un nombre de color desconocido
  salen con código 2 y una limitación explícita, sin traceback.
  · rojo visto: si
- **E-38** — El tamaño grande se decide con 24 px (18 pt), o 14 pt (18,67 px) en negrita; el informe distingue 1.4.3 (AA),
  1.4.11 (AA) y 1.4.6 (AAA) y marca a este último como AAA.
  · rojo visto: si
- **E-39** — Los scripts de `dev-accessibility/scripts/` y el motor `checks/lib/a11y.py` son válidos en Python 3.9:
  parsean con `feature_version=(3, 9)`, ninguna anotación evaluada en tiempo de definición usa `|` sin
  `from __future__ import annotations`, y no usan las APIs de 3.10 o posterior de la lista del test. Con
  `HARNESS_PYTHON39` definido se ejecutan además con ese intérprete; sin él, el test lo dice y no lo da por pasado.
  · rojo visto: si

### El check liviano y la revisión completa

- **E-40** — Un `<input id="x">` sin ninguna `<label for="x">` en un documento HTML completo se reporta como control sin
  nombre accesible: el `id` solo no es un nombre.
  · rojo visto: si
- **E-41** — `<label for="x">Nombre</label><input id="x">` no se reporta; `<label>Nombre <input type="text"></label>`
  (envuelto, sin `id`) no se reporta; una `<label>` envolvente sin texto sí.
  · rojo visto: si
- **E-42** — `aria-label="Buscar"` no se reporta; `aria-label="  "` sí.
  · rojo visto: si
- **E-43** — `aria-labelledby` que apunta a un elemento existente con texto no se reporta; a un id que no existe se
  reporta nombrándolo; a un elemento existente sin texto útil se reporta como «sin texto»; con varios ids, basta que
  uno resuelva con texto.
  · rojo visto: si
- **E-44** — Dentro de un fragmento sin `<html>` (parcial, `.component.html`, JSX), un control con `id` y sin
  `<label for>` en el archivo se reporta como **defecto** (`control-label-missing-in-file`), no como fallo, y el aviso
  dice que la etiqueta puede estar en otro archivo. Si el control está dentro de un componente propio, su `id` es
  una expresión, hay una `<label for>` dinámica o el archivo incluye otros, el check liviano calla y la revisión
  completa lo lista como `undeterminable` («no determinable»; el identificador va en inglés por ADR-0011). Un
  control sin `id`, sin `aria-label`, sin `aria-labelledby` y sin
  etiqueta envolvente se reporta como fallo.
  · rojo visto: si
- **E-45** — Un documento con cero o con dos `<h1>` no produce ningún aviso del check liviano. La revisión completa
  los informa como `recomendacion`, sin criterio ni nivel de WCAG.
  · rojo visto: si
- **E-46** — El check liviano emite solo hallazgos de tipo `fallo` y `defecto`: ni un `probable` ni una
  `recomendacion` aparecen en su salida, y cada aviso trae el criterio y su nivel («criterio 4.1.2, nivel A»).
  · rojo visto: si
- **E-47** — El check liviano ignora lo que no le toca: `.ts`, `.js`, `.css`, `.py`, rutas generadas
  (`node_modules`, `dist`…), archivos de más de 512 KB; y un archivo que el tokenizador no puede leer produce
  silencio, nunca una excepción.
  · rojo visto: si
- **E-48** — Plantillas: `{{ }}`, `{% %}`, `@if … @endif` de Blade, `<?php ?>` y los enlaces de Angular
  (`[attr.aria-label]`, `*ngIf`) no producen falsos positivos: un control cuya etiqueta es una expresión se toma por
  nombrado, y un `<title>{{ titulo }}</title>` cuenta como título. Una `<img [src]="u">` sin `alt` sí se reporta.
  · rojo visto: si
- **E-49** — JSX y TSX se leen con un tokenizador propio: `htmlFor`, etiquetas autocerradas, atributos con
  `{expresión}` (que valen «presente y desconocido»), `>` dentro de `{ }` o de una cadena, genéricos `<T,>` y
  comparaciones no rompen el análisis ni lo cuelgan; `<img src={u} />` sin `alt` se reporta, `<img alt="" />` no.
  · rojo visto: si
- **E-50** — En JSX, un elemento con `{...props}` no se juzga en los atributos que el spread podría traer, y un
  componente de nombre capitalizado (`<TextField />`) no se juzga: la revisión completa los cuenta como no
  analizados, con el motivo.
  · rojo visto: si
- **E-51** — La revisión completa informa la cobertura: archivos analizados, archivos o construcciones no analizados
  con su motivo, y formatos reconocidos. Una extensión fuera de alcance se lista como no analizada y no se calla.
  · rojo visto: si
- **E-52** — Un documento de 5.000 controles (unos 400 KB) se analiza en menos de 5 segundos: el costo no es
  cuadrático.
  · rojo visto: si
- **E-53** — Sobre el corpus etiquetado (`tests/fixtures/a11y/corpus.json`), el check liviano no tiene falsos positivos
  ni falsos negativos de los tipos que declara, y cada problema de la lista de este cambio tiene al menos un caso
  positivo y uno negativo.
  · rojo visto: si
- **E-54** — La tabla regla → criterio → nivel del motor coincide con `wcag22-criteria.json`, todo identificador de
  técnica (F, G, H, C, ARIA, SCR) que el motor cita existe en `tests/fixtures/wcag22-w3c.json` y está asociado al
  criterio de esa regla, y la tabla de reglas de `static-coverage.md` lista exactamente las reglas del motor, cada una
  con su criterio, su tipo, su origen y si corre en el check liviano.
  · rojo visto: si
- **E-55** — `review.py --register` produce un borrador que pasa la validación: los criterios con un fallo estático
  salen `fail` con archivo y línea; los demás, `not_tested` con «estática sin hallazgos»; ninguno sale `pass`.
  · rojo visto: si
- **E-56** — `review.py` encuentra el motor desde la fábrica y desde un árbol instalado, y si no lo encuentra lo dice
  y sale con código 2.
  · rojo visto: si
- **E-57** — Las reglas que caen en los fallos de la lista de este cambio quedaron arregladas y cubiertas por E-40 a
  E-45: `id` sin etiqueta, falsos positivos con `<label>` envolvente, referencias ARIA, y el `<h1>`.
  · rojo visto: si

### La integración en las skills y el agente

- **E-58** — `dev-ui/SKILL.md` exige que cada componente o patrón elegido produzca una fila `accessibilityLinks` con
  componente, estrategia, requisitos WCAG y forma de verificación; sin ellas el estado es
  `ACCESSIBILITY_REVIEW_REQUIRED`; y todo componente que su ejemplo de contrato nombra existe en
  `obelisco-matrix.json`.
  · rojo visto: si
- **E-59** — `dev-responsive/SKILL.md` cubre 1.4.4 (200 %), 1.4.10 (320 px CSS de ancho y 256 px de alto), 1.4.12
  (los cuatro valores de espaciado), 1.3.4 y 2.5.8 (24 px) como AA, marca 2.5.5 (44 px) como AAA, y dice que se
  verifican en navegador.
  · rojo visto: si
- **E-60** — `dev-frontend-implementation/SKILL.md` ordena `dev-ui`, `dev-accessibility` y `dev-responsive` para una
  unidad que toca interfaz y exige entregar el registro; `dev-frontend.md` devuelve `accessibilityEvidence` con la
  ruta del registro, los conteos y el estado de las tres pruebas manuales, y conserva sus cuatro skills instaladas.
  · rojo visto: si
- **E-61** — El registro de agentes sigue válido: los cuatro `id` de skills de `dev-frontend` y las rutas
  `skills/<id>/SKILL.md` no cambian.
  · rojo visto: si

### Instalación, actualización y desinstalación

- **E-62** — Tras instalar en un proyecto temporal, el lockfile lista cada archivo de
  `.claude\skills\dev-accessibility\` (`SKILL.md`, `references\**`, `scripts\*.py`) y el motor
  `.claude\harness\checks\desarrollo\lib\a11y.py`, todos en disco y con el SHA256 que dice el lock.
  · rojo visto: si
- **E-63** — Desde el árbol instalado, con `python -I -B`, `wcag.py count`, `contrast.py` y `review.py` corren, y
  `review.py` encuentra el motor instalado.
  · rojo visto: si
- **E-64** — Tras `-Update` con una referencia retirada de la fábrica, la copia sin editar se borra y sale del lock; la
  editada a mano se queda fuera del inventario con aviso; y una referencia nueva en una subcarpeta nueva se instala y
  entra al lock.
  · rojo visto: si
- **E-65** — Tras `-Uninstall` no queda ningún archivo del lock ni la carpeta `dev-accessibility` ni la de
  `lib\a11y.py`, y los scripts corridos con `-B` no dejaron `__pycache__`.
  · rojo visto: si

## Cómo se verifica

Todos los escenarios pasan por la suite: E-01 a E-61 en `tests/casos/78_wcag22_obelisco.py` (y la actualización de
`08_checks_borde.py` y de `07_checks.py` por el testigo), E-62 a E-65 en
`tests/casos/78-wcag22-obelisco-instalador.ps1`, que instala de verdad en `%TEMP%` y rompe solo una copia de la
fábrica (`tests\isolated-factory.ps1`). Ninguno está marcado `lectura`: el sujeto de cada uno es un archivo, un
script o un check, y una prueba determinista los alcanza. Lo que el cambio **no** verifica, y se declara en vez de
callarse: las tres pruebas manuales (navegador, teclado, lector de pantalla), la ejecución en un Python 3.9 real si
la máquina no lo tiene, y la vigencia de la matriz respecto de las páginas vivas de Obelisco.

La comparación «antes y después» que respalda cualquier cifra del informe final se hace con la misma regla en los
dos lados: tamaños en caracteres y tokens aproximados (1 cada 4 caracteres, la regla de
`harness-budget-auditor`) y el corpus etiquetado corrido contra el check de v0.35.0 y contra el nuevo.

## Riesgos conocidos

- **La matriz envejece.** Sale de las páginas publicadas de Obelisco el 2026-10-23, y el sistema de diseño publica
  versiones. Cada fila lleva su fuente y su fecha, y el cambio no puede decir si la página de mañana coincide.
- **La clasificación `requires` de cada criterio es una regla propia**, no del W3C. Es conservadora: ante la duda
  pide una prueba manual, y eso vuelve más difícil un `pass`, no más fácil.
- **El análisis estático tiene falsos negativos por diseño** (contraste, orden de foco, teclado, lector de pantalla).
  Sin hallazgos no significa conforme, y el registro lo impide expresar como `pass`.
- **Sin un Python 3.9 en esta máquina, E-39 se apoya en un lint sintáctico**, que atrapa los errores de anotación y de
  sintaxis de 3.10+, pero no cualquier uso de una API nueva fuera de su lista.
- **El corpus lo armó quien construyó.** Mide que los defectos conocidos están cubiertos, no la exactitud del check
  sobre código ajeno; por eso el informe lo dice así.
- **El testigo de paridad con PowerShell (E-16 de `07_checks.py`) se rompe a propósito** para este check: el aviso de
  `<h1>` se retira y los demás cambian de texto. Quedó anotado en el caso y en el escenario E-57.
- **Esta spec se escribió sabiendo qué defectos tenía el código**, porque los defectos son el pedido. El riesgo que
  ADR-0006 nombra, una spec escrita para pasar, se atenúa con el testigo externo (E-01, E-54) y con el corpus (E-53), y
  no se elimina.
