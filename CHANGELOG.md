# Changelog

Formato: cada versión lista lo que cambió a nivel funcional. Las versiones siguen
`MAJOR.MINOR.PATCH`, como exige ES0901 para el software de aplicación del organismo.

## [0.14.0] — 2026-08-21

> 🔴 **Sin cerrar.** `VERSION` sigue en `0.13.0`. Van dos veredictos y el segundo da —13 escenarios
> sostenidos, 0 contradichos, **9 sin sustento**— y un `verificacion.md` con `sin-sustento` no
> cierra el cambio. Nada quedó contradicho: la suite está verde y ningún comportamiento difiere de
> lo que la spec afirma. El bump lo hace `close-a-version` cuando esos diez tengan con qué
> sostenerse.

**El primer recorrido del código.** El harness se instalaba y después no pasaba nada hasta que
alguien escribía algo. Ahora un agente recorre el proyecto una vez y deja escrito qué hay, en
`docs/codebase/`, para que las sesiones que vengan lo lean en vez de re-derivarlo a fuerza de
`grep`.

### Agregado

- **`dev-iniciador-code`** — el agente del primer recorrido, en el harness `desarrollo`. Lista
  con `git ls-files`, agrupa en módulos y escribe una ficha por módulo con cuatro secciones fijas
  más un `indice.md` que las nombra a todas. Lo lanza la persona: el harness sugiere y nunca
  dispara solo
- **`SessionStart` lo sugiere** en una línea, solo con `desarrollo` instalado y solo mientras el
  índice no exista. Desaparece solo en cuanto está
- **`dev-codebase-forma`** — quinto check de `desarrollo`: comprueba que el índice y las fichas se
  correspondan en los dos sentidos y que cada ficha tenga sus cuatro secciones. Avisa, no bloquea
- **`rutaCodebase`** en `harness.config.json`, con default `docs/codebase`. Un proyecto ya
  instalado no verá la clave —ese archivo no se reescribe nunca— y funciona igual: el default se
  resuelve también en el hook y en el agente
- **ADR-0008** — el harness puede aprovechar una herramienta externa y no puede depender de ella
- 388 tests en verde (126 PowerShell + 262 Python), 54 más que en 0.13.0

### Para quien actualiza

- **Nada que hacer.** No hay cambios de comportamiento en lo que ya estaba: ningún bloqueo nuevo,
  ninguna regla nueva que falle, ningún requisito de instalación agregado
- Si tenés `desarrollo` instalado, la primera sesión después de actualizar va a sugerirte el
  recorrido. Es una línea y se apaga sola cuando lo corrés
- `docs/codebase/` **es del proyecto, no del harness**: `-Uninstall` no lo toca

## [0.13.0] — 2026-08-17

**Los hooks corren en Python.** El hook que corre en cada tool call tardaba 981 ms, 2,5× por
encima del umbral de ~400 ms que el plan de 0.6.0 nunca había medido. Los cuatro hooks, los
cinco checks y la suite se portaron de PowerShell a Python — a paridad de comportamiento,
defectos incluidos — y de arrastre se cerró el shim `.sh` que faltaba.

### Agregado

- **Python ≥ 3.9** como requisito de instalación, declarado en `comun/manifest.json` junto a
  `requiereClaudeCode`. `-Doctor` lo verifica y falla con instrucciones si no está o es anterior
- **`run-hook.sh`** — el shim POSIX que faltaba. `install.ps1` ahora escribe dos lanzadores:
  `run-hook.cmd` con la ruta absoluta del `python.exe` de la máquina, y `run-hook.sh`, genérico,
  para la sesión de Claude Code que corra sobre WSL, macOS o Linux
- `lib/zonas.py` — la definición de zonas en un solo lugar, con verbos de línea de comandos que
  `install.ps1` consume por JSON en vez de tener la lógica escrita dos veces
- 318 tests en verde: 102 en PowerShell (lo que sigue siéndolo: `install.ps1`,
  `03-instalador.ps1`, `00-encoding-fuentes.ps1`, `06-composicion.ps1`, `08-bitacora.ps1`) más
  216 en Python, bajo un único comando y un único código de salida
- **`-Doctor` mide la latencia de hook**: corre `pre-tool-use.py` cinco veces sobre el payload
  real y avisa si el p50 pasa los 400 ms. Nunca suma a las fallas; si no hay Python, no mide y
  no falla por eso

### Cambiado

- 🔴 **El contrato de un check rompe.** `param($Evento, $Proyecto, $Config)` en PowerShell pasa
  a ser `def verificar(evento, proyecto, config) -> list[str]` en Python. Un check propio en
  `.ps1` deja de descubrirse — ver [UPGRADE.md](UPGRADE.md)
- `docs/contrato-hooks.md`, reescrito sobre las trampas de Python: `-I` rompe el import,
  `ensure_ascii=False` en la salida, escribir bytes UTF-8 al buffer y no con `print`, `utf-8-sig`
  al leer stdin, los checks se cargan por ruta porque su nombre lleva guiones

### Lo que no se cumplió, sin maquillar

- 🔴 **E-29 no se cumple.** El umbral era 400 ms y `pre-tool-use` da 558 ms de p50 (14 corridas,
  Stopwatch). La causa está medida: el arranque desnudo del intérprete en esta máquina ya se
  come el umbral solo, así que ni con el código del hook en cero se llegaría por debajo. La
  mejora real es 981 → 558 ms, un 43%. `-Doctor` ya vigila este número en cada corrida

## [0.12.0] — 2026-08-13

**Una bitácora por versión.** El `CHANGELOG` cuenta qué cambió para quien actualiza; lo que no
quedaba en ningún lado es lo que necesita **quien sigue el trabajo**: por qué está así, qué se
descartó y qué quedó abierto. Eso vivía en la conversación, y una conversación se compacta.

### Agregado

- **`docs/versiones/`** — una nota por versión, de 0.1.0 a esta, con secciones fijas: qué se
  hizo · qué se decidió y por qué · lo que se rompió en el camino · lo que quedó abierto ·
  **dónde seguir**. Las de 0.1.0 a 0.6.0 se declaran reconstruidas del `CHANGELOG` y los commits
- **Un test que verifica que cada versión tiene su nota**, que ninguna sobra, que están las cinco
  secciones y que el índice las lista. Sin eso, escribirlas dura hasta la primera semana ocupada

### Corregido

- 🔴 **El harness bloqueaba la escritura de su propia documentación.** Al aislar el valor de una
  asignación, `Get-ValorDeAsignacion` descartaba comillas simples y dobles **pero no el
  delimitador de código de markdown**, así que un relleno obvio delimitado con markdown quedaba
  con el delimitador de cierre pegado y ningún patrón de exclusión anclado podía matchearlo
  - Es la misma familia del bug que ese código vino a arreglar en 0.4.0
  - Verificado que no afloja la detección real; dos tests nuevos, los dos negativos
  - **El detector se había probado contra código, no contra prosa** — y documentar el harness es
    una actividad normal del harness

## [0.11.0] — 2026-08-13

**`desarrollo` ya sabe algo.** Ocho skills, un refutador y los seis estándares destilados a
extractos citables. Con esto el harness deja de ser andamiaje: un agente que trabaja sobre un
proyecto del GCBA puede citar la norma con página en vez de opinar sobre buenas prácticas.

### Agregado

- **`normativa/extractos/` — 2.696 líneas** destiladas de los seis PDF. Cada extracto declara
  **qué NO se puede citar desde ahí**: tablas que se convirtieron desalineadas, reglas que
  viven solo en un diagrama sin capa de texto, anexos que no están en el documento
- **Ocho skills, cortadas por tarea y no por documento.** Nadie se levanta con ganas de leer
  ES0903; se levanta con ganas de diseñar un endpoint

  | Skill | Se activa cuando |
  |---|---|
  | `dev-api` | Un endpoint, un contrato OpenAPI/RAML, la forma de un error |
  | `dev-repositorio` | Estructura, ramas, tags, el paquete de entrega |
  | `dev-versiones` | Fijar la versión de un lenguaje, framework o biblioteca |
  | `dev-identidad` | Login, sesión, tokens, roles, BA ID o AD |
  | `dev-seguridad` | Validaciones, archivos, errores, logs, el assessment |
  | `dev-pantalla` | Una pantalla, un componente, accesibilidad |
  | `dev-ambientes` | Un pase de ambiente, una entrega, qué aprobaciones faltan |
  | `dev-tramites-asi` | Pedirle algo a ASI por ticket |

- **`dev-refutador`** — el hermano técnico de `hu-refutador`. Tres veredictos: `cumple`,
  `incumple`, `sin-verificar`. Saca la norma **de las skills, no de su memoria**; si ninguna
  cubre el tema, no lo verifica y lo dice
  - La regla que lo gobierna: **nunca declares `cumple` sin poder citar la regla con su página
    y señalar la línea.** Marcar `sin-verificar` algo que cumplía cuesta una segunda mirada;
    marcar `cumple` algo que no cumplía significa que pasa con el sello puesto y rebota del
    assessment de seguridad con el cronograma ya comprometido

### Lo que encontró la verificación, que vale más que las skills

Cuatro rondas adversariales sobre extractos y skills. **No apareció una sola norma fabricada de
cero.** Lo que apareció, una y otra vez, fue **afirmar con más fuerza o más alcance del que la
fuente da**:

| La fuente dice | Se escribió |
|---|---|
| "la vía **principal** de contacto" | "la vía **única**" |
| "un mismo client id **puede** gestionar varios frontends" | "**no pidas** credenciales separadas" |
| "en la raíz", de `composer.json` | de los tres archivos de dependencias |
| cinco tablas corridas | "las tablas del Anexo II" |
| "delegar el ingreso de credenciales" | "no puede haber tabla de contraseñas" |

Ninguna es falsa en la práctica y todas suenan a buen criterio. **Y ninguna la dice el
documento**, así que quien las cite frente a ASI se queda sin respaldo.

**El patrón se repitió en cada capa, incluidas las correcciones.** Tres veces una pasada
correctiva arregló un problema e introdujo otro de la misma familia — un conteo inflado, una
página corrida, una enumeración que pasó de sobrar a faltar. Por eso cada corrección tiene su
propia refutación: **una corrección no es confiable por ser una corrección.**

**Y cuatro veces un corrector le discutió al verificador con página y cita, y tenía razón.** En
dos de esas el defecto estaba en el extracto, no en la skill: degradaba una cita textual a
paráfrasis, lo que hacía parecer inventada una comilla correcta. Se arregló en el extracto,
para que la próxima skill escrita desde ahí no repita el error.

### Criterio que quedó fijado

- **Los extractos son insumo de autoría, no dependencia de ejecución.** `normativa/` nunca se
  copia a un proyecto — son 11 MB de PDF. Las skills son autosuficientes: llevan la regla
  adentro y citan página para que una persona pueda ir a la fuente
- **Ninguna skill publica un número de versión.** Ni siquiera desde una tabla verificada. Una
  skill con una versión clavada envejece en silencio: el estándar se actualiza y la skill sigue
  diciendo lo mismo. `dev-versiones` es útil sin dar un solo número, y ese es el punto
- **Las contradicciones se registran con sus dos lados, nunca se resuelven.** ES0901 se
  contradice sobre el nombre de las ramas, el umbral de cobertura, los paquetes compilados y el
  assessment del hotfix. Elegir un lado en silencio sería inventar una norma

## [0.10.0] — 2026-08-12

**`desarrollo` deja de estar vacío.** Hasta acá tenía su `manifest.json` y su bloque de
`CLAUDE.md` y nada más: instalarlo daba el esqueleto común y ni una regla técnica. Ahora trae
sus primeros cuatro checks, y son los cuatro que se pueden comprobar sobre un archivo sin
criterio humano.

### Agregado

- **`normativa/fuentes/`** — los seis PDF de los estándares, adentro del repo. Sin la fuente al
  lado, un extracto no es auditable: nadie puede comprobar que dice lo que la norma dice
- **Cuatro checks de `desarrollo`**, todos con el número de línea del hallazgo:

  | Check | Qué mira | De dónde |
  |---|---|---|
  | `dev-dependencias` | Rangos (`^`, `~`, `*`, `>=`) en `package.json` y `composer.json` | ES0901 |
  | `dev-api-rutas` | Rutas sin versión, verbos en la ruta, colección en singular | ES0903 |
  | `dev-infra-en-codigo` | Servidores referenciados por IP en vez de nombre DNS | ES0901 |
  | `dev-accesibilidad-html` | `lang`, `alt`, controles sin forma de nombrarlos, jerarquía de `h1` | ley 26.653 |

- `harnesses/desarrollo/checks/lib/Dev.psm1` — lo que comparten: qué archivo se escribió, si
  cae en un directorio generado, en qué línea está el hallazgo
- 33 tests. **200 en total, todos en verde**

### El criterio con el que están escritos

**La mitad que importa de cada check es la negativa: que se calle cuando no le toca.** Un check
de nomenclatura con falsos positivos se desactiva la primera semana, y entonces tampoco atrapa
los verdaderos. De los 33 tests nuevos, 14 verifican silencio:

- `postulaciones` no se reporta por empezar con `post`
- una versión `10.51.2.300` no se confunde con una IP
- `alt=""` es correcto: declara que la imagen es decorativa
- un parcial de Angular sin `<h1>` no es un error
- `node_modules` y `vendor` no se tocan nunca
- las rutas que no son de API no se miran, o el check opinaría sobre todo el front

Y las reglas ambiguas se dejaron afuera a propósito. El plural solo se reporta cuando es
inequívoco —un segmento singular seguido de un identificador, `/usuario/{id}`— porque un
`/salud` suelto puede ser cualquier cosa.

### Notas

- Dos bugs de PowerShell en el camino, los dos de la misma familia. `-split` con una alternativa
  que puede matchear vacío **parte en cada carácter**: `crearUsuario` salía en doce pedazos de
  una letra y el verbo nunca se detectaba. Y un arreglo de un elemento devuelto desde una
  función se desenvuelve al elemento, así que `$r[0]` sobre un string devuelve su primer
  **carácter** — el test comparaba `[` contra lo que esperaba y fallaba sin decir por qué
- El test de encoding hizo su trabajo: los seis archivos nuevos nacieron sin BOM y lo detectó
  antes de que nadie los ejecutara

## [0.9.0] — 2026-08-12

**Los dos silencios que quedaban.** Instalar el harness sobre el IGE —el primer proyecto real,
con un `CLAUDE.md` escrito a mano antes de que el harness existiera— destapó que el harness se
callaba en los dos casos donde más caro sale callarse. Los dos fallaban igual: sin error, sin
aviso, y dejando el archivo peor de como estaba.

### Corregido

- 🔴 **Una zona escrita con otro nombre ya no produce una duplicada en silencio.** El
  `CLAUDE.md` del IGE traía `<!-- ÍNDICE -->` y `<!-- CACHÉ -->` —los nombres del prototipo, sin
  el prefijo `ZONA`—. El instalador no los reconoció y agregó las canónicas **al lado**: el
  archivo quedó con dos índices y dos cachés, uno con el contenido real y otro vacío, y el
  check medía el vacío. Ahora el instalador detecta el marcador, **no agrega la zona** y explica
  qué renombrar. Un par de comentarios de apertura y cierre con el mismo nombre **es** una zona,
  la haya escrito el harness o una persona
- **El check ya no da dos consejos que se contradicen.** Decía a la vez *"`ÍNDICE` es tu ZONA
  ÍNDICE con otro nombre"* y *"falta ZONA ÍNDICE, corré `-Update` para reponerla"* — y `-Update`
  a propósito ya no la repone. Un consejo que no funciona gasta la credibilidad de todos los demás

### Agregado

- **Se mide lo que queda fuera de toda zona.** `Measure-Zonas` mide lo que está *adentro*; lo de
  afuera no lo medía nadie: no se purga, no baja al conocimiento del proyecto y no cuenta contra
  ningún techo. Un `CLAUDE.md` de trescientas líneas sin un solo marcador pasaba la medición
  entera sin una palabra. Techo nuevo `techoFueraDeZonas`, por defecto 12 — alcanza para el
  título y dos líneas de presentación, que es lo único que corresponde tener afuera
  - Como `harness.config.json` **no se toca nunca**, una clave nueva no llega a los proyectos ya
    instalados. El check trae el valor por defecto en código para que igual funcione
- `Find-ZonasNoReconocidas` y `Measure-FueraDeZonas` en `Zonas.psm1`, y `Get-MarcadoresHtml`,
  que ubica los marcadores sobre el texto completo: uno puede ocupar varias líneas, y ya pasó
- **El nombre de un marcador se toma por lo que es, no por el separador que venga después.** Los
  archivos generados usan raya larga y una persona escribiendo a mano pone un guion común. Antes
  se cortaba solo por raya, y con un guion común el nombre de apertura no coincidía con el de
  cierre: la zona entera dejaba de existir para el harness
- 16 tests más. **167 en total, todos en verde**

### Notas

- Cuarta aparición de la misma familia de bugs de PowerShell: `return ,$coleccion` la emite como
  **un** objeto —eso es lo que evita que un resultado vacío se desenvuelva a `$null`— pero
  también significa que envolverla en `@()` da un arreglo de un elemento que es la colección
  entera. El contrato quedó fijado con tests para 0, 1 y 2 elementos

## [0.8.0] — 2026-08-12

**La primera skill de `comun/`.** El relevamiento de lo que había en la instalación local
encontró 23 skills activas: dos propias y 21 de dos plugins de terceros. De todo eso, una sola
tenía que entrar al harness.

### Agregado

- **`comun/skills/instalar-desde-github/`** — la disciplina para evaluar, instalar o tomar
  material de un repo de GitHub sin clonarlo: datos duros de la API, README crudo y filtrado,
  cinco preguntas respondidas **antes** de tocar la máquina, y el comando de desinstalación
  anotado junto al de instalación. Es el procedimiento que ya se aplicó con `gentle-ai`, ahora
  escrito y distribuible

  Tres cosas cambian respecto de la versión personal de la que sale:

  - **Deja de afirmar el estado de una máquina.** Decía *"no hay `gh` en esta máquina"*, que era
    cierto donde se escribió y falso en la de cualquier otro. Ahora se comprueba con
    `Get-Command` y se elige la vía en consecuencia
  - **Un runtime nuevo tiene que estar homologado.** Que la herramienta funcione no alcanza si
    el runtime que exige no figura en la tabla de versiones de ES0901
  - **Cubre el caso "no instalamos, tomamos".** Cuando la conclusión es *"de acá nos sirven dos
    ideas"*, eso pasa a ser código de terceros dentro de un repo del GCBA: se lee entero, el
    commit va exacto y completo, la licencia se registra, y se anota también lo que se dejó y
    por qué. Es el procedimiento del ADR-0005, ahora accionable desde donde se decide

  Se suma la cuarta trampa, que salió del caso real: **en Windows puede directamente no haber
  binario.** `gentle-ai` retuvo su distribución para Windows por falta de firma Authenticode —
  el README ofrece la instalación y en esta plataforma no existe

## [0.7.0] — 2026-08-11

**Los dos harness ya conviven de verdad.** El README prometía desde 0.1.0 que un proyecto
podía tener `analisis` y `desarrollo` a la vez. El código lo sostenía solo si los nombrabas
juntos en el mismo comando — y el camino real es el otro: un repo de relevamiento que recibe
su primer código meses después.

### Corregido

- 🔴 **Agregar un segundo harness ya no borra el primero.** Instalar es aditivo: se lee el
  lockfile y se conserva lo que el proyecto ya tenía. Antes, `-Harness desarrollo` sobre un
  proyecto con `analisis` reemplazaba el bloque del `CLAUDE.md` y el lockfile con el conjunto
  nuevo, y los archivos del primero **quedaban en disco fuera del inventario** — invisibles
  para `-Doctor` y para `-Uninstall`. Fallaba en silencio y un `-Update` posterior no los
  recuperaba nunca
- 🔴 **`-Harness analisis,desarrollo` ahora funciona por las dos vías.** En una sesión
  interactiva el parser de PowerShell arma el array y andaba; invocado con `-File` —desde un
  `.cmd`, desde CI, desde otro script— el mismo texto llegaba como una cadena literal y
  abortaba con *"no existe el harness 'analisis,desarrollo'"*. Es la forma que documenta el
  README, así que nunca se probó por la vía que fallaba
- **El orden es canónico, no de instalación.** Llegar al mismo conjunto instalando los dos
  juntos o agregando uno después producía archivos distintos, y el `-Update` siguiente
  generaba un diff que no correspondía a ningún cambio real

### Cambiado

- **`-Harness` es aditivo y lo dice.** Cuando conserva algo ya instalado lo anuncia:
  `se conserva lo ya instalado: analisis`. Conservar en silencio sorprende tanto como borrar
  en silencio. Para quedarse con un conjunto exacto, el camino es `-Uninstall` y reinstalar

### Agregado

- 21 tests más en `tests/casos/06-composicion.ps1`, que cubren el ciclo incremental completo:
  los dos juntos, uno después del otro, el inventario sin huérfanos y el `-Update` posterior.
  **151 en total, todos en verde**

---

## [0.6.0] — 2026-08-11

**El esqueleto está terminado.** Con esto el harness ya es útil por sí solo: bloquea secretos,
ordena la memoria del proyecto y te dice en qué quedaron al abrir una sesión.

### Agregado
- **El harness te trata por tu nombre.** Se pide al instalar (`-Usuario`), se guarda en
  `harness.config.json` y no se toca nunca más. Si no lo pasás y hay consola, te lo pregunta;
  si no hay consola, **aborta explicando** en vez de colgarse esperando a nadie
  - Se usa solo para el trato. **No firma archivos ni atribuye cambios**: para eso está git,
    y así no entran datos personales por una vía que nadie audita
  - `-WhatIf` no lo pide: como no escribe nada, no puede exigir nada
- **`CLAUDE.md` canónico con cuatro zonas y sus techos** — FIJA 60, MAPA 20, ÍNDICE 25,
  CACHÉ 80. El instalador crea las que falten, vacías, y **nunca toca una que ya exista**
- **Check `claude-md-zonas`** — mide cada zona después de cada escritura y avisa si pasó su
  techo. Sin medición, "mantener chico el `CLAUDE.md`" es una intención que dura hasta la
  primera semana ocupada. También avisa cuando la caché va llena, para bajarla
- **`SessionStart` contesta «¿en qué quedamos?»** — nombre, harness, estado de git, últimos
  commits, lo anotado en la caché y definiciones pendientes abiertas, en 12 líneas
  - 📌 **Se lee lo que alguien decidió dejar anotado; no se captura nada.** Un capturador
    automático persistiría también la cadena de conexión que el agente leyó hace un rato. Esta
    memoria es más pobre a propósito, y por eso no puede filtrar un secreto
- **`flush-memoria`** — baja la caché a `docs/conocimiento/` del repo, no a un vault personal.
  Conserva su invariante: nunca desaloja lo que no escribió; ante la duda, no borra
- **`leer-docs`** — sin rutas absolutas: `markitdown` se busca en el PATH y `docimg.py` ahora
  **viaja adentro del harness**, así que funciona en cualquier máquina
- `Zonas.psm1` y `Reglas.psm1`; `comun/` ahora también aporta `checks/` y `bin/`
- 19 tests más. **130 en total, todos en verde**
- `docs/memoria.md`

### Cambiado
- **`-Uninstall` saca las zonas vacías y deja las que tienen contenido.** Una zona vacía es
  andamiaje que nadie usó; una con contenido es trabajo de alguien

### Corregido durante la construcción
- Otra vez el mismo patrón: una función que devuelve `@()` se desenvuelve a `$null` y con
  `Set-StrictMode` pedirle `.Count` rompe. Rompió `-Update` entero

## [0.5.0] — 2026-08-10

El harness `analisis` deja de estar vacío, y con él aparece **la verificación independiente**,
que era la brecha más vieja: hasta ahora quien escribía una historia era quien la aprobaba.

### Agregado
- **`hu-refutador`** — el revisor que faltaba. Verifica una historia contra su maqueta y
  devuelve un veredicto por afirmación: `sostenido`, `contradicho` o `sin-sustento`.
  No escribe, no corrige y **no puede agregar hallazgos propios**
  - `sin-sustento` **es** una definición pendiente: cada uno es una decisión que nadie tomó y
    que alguien iba a inventar
  - Regla que lo gobierna: *nunca declares `sostenido` sin poder señalar dónde lo viste*.
    Evidencia ausente, ilegible o ambigua es `sin-sustento`, por la asimetría del costo —
    revisar una maqueta de nuevo es barato, una invención con sello de verificada es carísima
  - Presupuesto acotado: una pasada por historia, una invocación por módulo. Sin bucles
- **`hu-redactor`** — el redactor, sin rutas absolutas ni usuario de Windows adentro. Lee las
  rutas del proyecto de `harness.config.json`. Su Paso 0 ahora **informa cómo cargó la skill**
  (`skill-invocada` / `leida-por-ruta` / `no-encontrada` / `sin-cargar`): una falla de carga
  deja de ser silenciosa, que era como el agente terminaba trabajando sin guía
- **`hu-escribir`** — la skill de formato, generalizada: sin referencias a un vault personal
  ni a rutas de un proyecto puntual. Reemplaza a `escribir-hu-gcba` y adopta el prefijo `hu`
  del harness, que es lo que hace segura la composición entre harness
- 3 tests más: los assets llegan a `.claude/skills/` y `.claude/agents/`, y **todo agente
  instalado declara `tools:`** — sin eso hereda escritura y ejecución total. **107 en total**

### Terceros
- Primer origen registrado: **gentle-ai** (MIT, commit exacto). Se leyeron cuatro archivos
  enteros y **se descartó el binario**: es un configurador de agentes igual que este harness
  y los dos escriben en `.claude/settings.json`; además exige Go 1.25.10+ (no homologado por
  ES0901), en Windows no hay binario firmado, y su README no documenta cómo desinstalarlo
- De su `review-refuter` salió la forma del refutador; de su `review-risk`, los presupuestos
  y el principio de precisión — que resultó ser **el mismo al que habíamos llegado con los
  secretos, por otro camino**; de su `skill-resolver`, el reporte de resolución

## [0.4.0] — 2026-08-10

La regla de secretos, punta a punta. Es lo único que el harness impide.

### Agregado
- `comun/hooks/lib/Secretos.psm1` — detector con dos niveles de confianza:
  **alta bloquea, media pregunta**. Lo ambiguo lo decide la persona, no el harness, porque
  el falso positivo es lo que hace que un harness termine desinstalado
- `comun/reglas/secretos.patrones.json` — 12 patrones y 18 reglas de exclusión. Agregar un
  patrón o cambiar su severidad **no toca una línea de código**
- `Write-HookAsk` en `Hook.psm1` — la cuarta forma de salida, para el caso ambiguo
- El hook `PreToolUse` mira `content`, `new_string`, `command` y las ediciones de `MultiEdit`
- **El motivo nunca repite el secreto.** El texto entra al contexto y queda en la
  transcripción: se informa la forma y el largo, no el valor
- 38 tests nuevos. **16 son casos que NO deben bloquear** — `${VAR}`, `process.env`,
  `os.getenv`, `System.getenv`, `%VAR%`, placeholders, hashes de commit, rutas largas — y
  valen tanto como los positivos. **104 en total, todos en verde**
- `docs/secretos.md` y `docs/adr/0005-terceros-separados-de-lo-propio.md`
- `terceros/` — material bajado de repos públicos, con su lockfile de procedencia. **No es
  fuente de instalación**: lo que se usa se copia a lo propio con nota de origen. Una skill
  ajena es texto que el modelo obedece, no una librería que se llama

### Corregido durante la construcción
- **La exclusión de placeholders recibía la coincidencia entera** (`password = xxxxx`) en vez
  del valor, así que ningún patrón anclado con `^...$` podía matchear nunca. `password = xxxx`
  y `api_key = "your-api-key-here"` se bloqueaban como si fueran credenciales reales

## [0.3.0] — 2026-08-06

**Ya es instalable.** El harness bloquea lecturas de rutas sensibles y registra los cuatro
hooks, aunque todavía no sepa nada de historias de usuario ni de APIs.

### Agregado
- `install.ps1` — `-Doctor`, `-WhatIf`, instalar, `-Update` y `-Uninstall`
  - **`-WhatIf` no escribe un byte**: muestra el diff completo antes de tocar nada
  - Backup con sello de tiempo de todo lo que se pisa; nunca se borra, ni al desinstalar
  - `harness.lock.json` con SHA256 de cada archivo, que es lo que hace **detectable** la
    deriva entre proyectos — la contra de haber elegido copia en vez de enlace (ADR-0002)
  - **`-Update` no pisa lo que editaste**: deja la versión nueva como `.nuevo` al lado
  - `harness.config.json` se crea una vez y no se toca nunca más. Es del humano
  - Los bloques en `CLAUDE.md` y `.gitignore` se inyectan entre marcadores: el resto del
    archivo es intocable, y reinstalar no duplica nada
  - `-Doctor` revisa ExecutionPolicy, Mark-of-the-Web, versión de Claude Code, deriva del
    proyecto, enlaces bajo `.claude/`, y lista los subagentes globales sin `tools:`
  - **La instalación falla y revierte si los cuatro hooks no responden.** Un hook roto es
    peor que ninguno, porque falla en silencio
- `harnesses/analisis/` y `harnesses/desarrollo/` — manifest y bloque de `CLAUDE.md` de
  cada uno. La estructura y el contrato quedan fijos; el contenido viene después
- `comun/manifest.json`, los cuatro hooks de evento, la lista de `deny` de secretos y la
  plantilla de registro de hooks
- `.gitattributes` — sin él, `core.autocrlf` convierte el futuro `run-hook.sh` a CRLF y
  deja de ejecutar en Linux
- 30 tests más: el ciclo completo `-WhatIf` → instalar → `-Doctor` → editar a mano →
  `-Update` → `-Uninstall`. **66 en total, todos en verde**

### Corregido durante la construcción
- **`$destino` y `$Destino` son la misma variable.** PowerShell no distingue mayúsculas en
  nombres de variables: el local pisaba el parámetro y las rutas se anidaban una adentro de
  otra a partir de la segunda vuelta del bucle
- **Una función que devuelve `@()` se desenvuelve a `$null`**, y con `Set-StrictMode 2.0`
  pedirle `.Count` es un error terminante. Se devuelve con la coma adelante
- El reemplazo del lanzador en el registro de hooks se hace sobre el texto de la plantilla,
  con las comillas escapadas. Hacerlo después de serializar rompía el JSON

### Cambiado
- **Agregar un harness ya no toca `install.ps1`.** El instalador los descubre leyendo el
  directorio: alcanza con crear su `manifest.json`

## [0.2.0] — 2026-08-06

Infraestructura de hooks, con sus tests. Todavía no hay instalador.

### Agregado
- `comun/hooks/lib/Hook.psm1` — lectura del evento por stdin, las tres formas de salida
  (silencio / avisar / bloquear), encoding UTF-8 y control de errores. Un check que
  explota reporta una vez y sale con código 0: nunca rompe la sesión
- `tests/Invoke-Tests.ps1` — corredor sin dependencias, sale 1 si algo falla
- `tests/payloads/` — payloads reales de los cuatro eventos, más uno de acentos
- `tests/fixtures/` — hooks de prueba para cada forma de salida
- 36 tests, todos en verde
- `docs/contrato-hooks.md` — el contrato y las cinco trampas
- `scripts/Repair-EncodingFuentes.ps1` — agrega BOM a los fuentes que lo necesitan

### Corregido durante la construcción
- **`[Console]::InputEncoding` no se toca.** Asignarlo recrea `Console.In`, y con stdin
  redirigido desde una tubería eso corrompe la lectura: `ConvertFrom-Json` fallaba con
  *"Primitivo JSON no válido"*. La entrada se lee con su propio `StreamReader`
- **Los `.ps1` con caracteres no ASCII van en UTF-8 con BOM.** PowerShell 5.1 los lee
  como ANSI si no lo tienen. Lo insidioso: un test escrito en un archivo corrupto compara
  basura contra basura y **pasa**. Ahora hay un test que verifica la regla sobre todo el
  repo, y un script que la corrige

## [0.1.0] — 2026-08-05

Estructura inicial del repositorio. **Todavía no hay nada instalable.**

### Agregado
- Estructura de directorios: `comun/`, `harnesses/`, `normativa/`, `docs/adr/`, `tests/`
- `README.md` con requisitos, instalación y el límite honesto de la regla de secretos
- Las cuatro decisiones de arquitectura que fundan el diseño:
  - ADR-0001 — la rama de desarrollo se llama `develop`
  - ADR-0002 — se copia, no se enlaza
  - ADR-0003 — Obsidian queda afuera del harness
  - ADR-0004 — el harness no usa la estructura `source/` de ES0901

### Pendiente para 0.2.0
- `Hook.psm1` y la infraestructura de hooks con sus tests
- `install.ps1` con `-WhatIf`, `-Doctor` y lockfile
- La regla de secretos punta a punta
- El `CLAUDE.md` canónico y su validador de zonas
