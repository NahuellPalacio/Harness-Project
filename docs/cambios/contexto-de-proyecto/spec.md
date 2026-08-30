# El contexto del proyecto como contrato: `project-context.json`

**Estado:** verificado, sin cerrar · **Fecha:** 2026-08-23

> **Dónde quedó, al 2026-08-24.** Todo lo de `## Qué se construye` está escrito, la pasada de
> `rojo visto` está hecha —27 de los 28 escenarios se rompieron a propósito y se vieron en rojo—, la
> suite da **558/558** y el veredicto está en [`verificacion.md`](verificacion.md): **27 sostenidos,
> 0 contradichos, 1 sin sustento**.
>
> Van **dos pasadas de `harness-spec-refuter`**, las dos el 2026-08-24. La primera dejó tres huecos
> —E-07, E-12b y E-20—; los dos primeros se cerraron tocando únicamente `tests/casos/13_contexto.py`
> y la segunda pasada los dio sostenidos. Falta, en este orden:
>
> 1. **La lectura de E-20** según ADR-0009, en un `lectura.md` de este directorio: alguien que no
>    construyó corre el agente, mira el contrato que salió y escribe qué observó, con fecha y firma.
>    🔴 Se suma a las nueve de [`iniciador-code`](../iniciador-code/lectura.md) y a las **cuatro**
>    de [`mapa-de-nodos`](../mapa-de-nodos/lectura.md) —E-01, E-18, E-19 y E-20, en un directorio
>    que además no tiene `verificacion.md`—. Son **catorce**, y las catorce traban el cierre.
>
>    📌 Corregido el 2026-08-26: esta línea decía "diez" y se olvidaba de `mapa-de-nodos`. Lo
>    encontró `harness-spec-refuter` rindiendo sobre la spec del paso 4. Que esa lectura esté sin
>    firmar a propósito no la saca de la pila: ADR-0009 no tiene categoría para una lectura
>    deliberadamente vacía.
> 2. **El cierre de 0.14.0** con `close-a-version`: `VERSION`, `CHANGELOG.md`,
>    `docs/versiones/0.14.0.md` —que hoy sólo cuenta `iniciador-code`—, el índice del README,
>    `UPGRADE.md` y el número de tests de `CLAUDE.md`, que pasa de 455 a 558.
> 3. **Republicar `docs/mapa/recorrido-mensaje.html`** como Artifact a la URL que lleva en su
>    comentario de cabecera. Ya está editado; falta publicarlo.
>
> Nada está commiteado. Lo que sigue después de esta versión —los pasos 3 a 9 del PDF y quién
> consume el contrato— está mapeado en `Pendientes/Ideas-Harness/PENDIENTES-I.md`, bajo *"Which
> PROJECT_CONTEXT fields serve `dev-refutador`"*.

## Qué problema resuelve

`dev-iniciador-code` recorre el repositorio una vez y deja escrito qué hay. Eso ya funciona, y las
sesiones que vienen leen el índice en vez de re-derivarlo. Pero lo que deja escrito es **prosa**, y
la prosa no puede contestar la única pregunta que un agente tiene que poder contestar antes de
decidir nada: **¿de qué snapshot del proyecto salió esto?**

Hoy, mirando `docs/codebase/`, nadie puede decir:

- de qué commit se escribió cada ficha, ni si el código cambió desde entonces;
- de qué archivo salió cada afirmación, ni si esa fuente sigue vigente;
- qué es dato confirmado y qué es inferencia de quien recorrió;
- qué se buscó y **no se encontró** — un hueco no deja rastro, y el que lee después no distingue
  "acá no hay nada" de "acá nadie miró".

El costo aparece cuando el índice tiene un segundo lector. `dev-refutador` ya verifica contra la
norma; el agente de QA que viene después va a tener que decidir si un cambio cumple. Los dos van a
tomar decisiones con información que no saben de cuándo es, y el día que una salga mal no va a
haber cómo reconstruir por qué.

El contrato `PROJECT_CONTEXT` del documento *QA Agent · Project Context Contract v1.1* resuelve
exactamente eso: **una sola capa de discovery, muchos consumidores, y la procedencia viajando
adentro**. Su capítulo 04 lo pone como regla dura — *"nunca consumir un contexto sin
`repo_revision`/`context_hash`"* — y su capítulo 18 ordena la implementación en nueve pasos.

Este cambio construye los **pasos 1 y 2**: el schema, y un Initiator que lo emite.

## Qué queda afuera

- **`business_rules`, `interfaces`, `identity_and_access`, `environments` y `quality_landscape`
  (pasos 3 a 5).** Cada uno necesita que el agente recorra el proyecto con una pregunta distinta, y
  necesita sintaxis para `source_refs` y `confidence` **por afirmación**, no por documento.
  Diseñarla sin haber visto el contrato base emitido es diseñarla a ciegas.
- **`CHANGE_CONTEXT` y `QA_RUN_REQUEST` (pasos 6 y 7).** `CHANGE_CONTEXT` se apoya en un
  `project_context_ref` que todavía no existe, y toca el método de este repositorio: lo más parecido
  que hay es `docs/cambios/<slug>/spec.md`, y fusionarlos es una decisión sobre ADR-0006 que no se
  toma de paso.
- **El agente de QA.** Va a ser un `dev-qa` adentro de `desarrollo`, y no se escribe hasta que haya
  un contrato que darle.
- **`CONTEXT_REQUIRED` y el enrichment dirigido (paso 8).** Es el protocolo por el que un consumidor
  pide lo que falta. Sin consumidor no hay quien lo emita, y un protocolo sin ninguna de las dos
  puntas no se puede probar.
- **Refresh incremental (paso 9).** El recorrido es completo o no es, igual que hoy.
- **Un check de `PostToolUse` sobre el contrato.** `contexto-armar.py` valida antes de escribir, y
  la suite valida el archivo versionado. Un check sólo atraparía a alguien editando a mano un
  archivo generado que dice "no editar a mano", y ese aviso se paga en latencia **en cada llamada a
  herramienta de cada sesión**. Es el mismo criterio con el que `mapa.html` tampoco tiene check.
- **Avisar que el contexto quedó viejo.** Cualquier commit cambia `HEAD`: un aviso por
  desactualización aparece en todas las sesiones, se vuelve ruido y se deja de leer — y con él se
  pierde el resto del bloque de `SessionStart`. La antigüedad se ve corriendo el script; la
  **ausencia** sí se avisa, que es un estado que se corrige una vez y no vuelve.

## Las decisiones, y por qué

### El agente escribe markdown; el JSON lo genera un script

Es el reparto que ya estaba decidido cuando se eligió un agente en vez de un script para el
recorrido: *"determinista y gratis, sirve para el esqueleto —rutas, imports, tamaños— y no puede
escribir qué hace un módulo"*. Acá se aplica al revés y en la misma pasada.

| Lo calcula `contexto-armar.py` | Lo escribe el agente |
|---|---|
| `meta` entero: `repo_revision`, `docs_revision`, `context_hash` | `project_profile`: qué es el proyecto y para qué |
| `sources[]`, desde `git ls-files` y las fichas | `technology`: lenguajes, frameworks, comandos de build y test |
| `architecture.components[]` y `dependency_edges[]`, desde el grafo | `architecture.entrypoints[]` y `external_integrations[]` |
| `gaps_and_conflicts.missing[]` sembrado con las fichas huérfanas | `gaps_and_conflicts`: qué buscó y no encontró |

**El agente nunca escribe JSON.** Escribe una ficha más, `proyecto.md`, con encabezados fijos, y el
script la serializa. Una sola superficie de autoría y un solo generador: no hay dos archivos que
puedan contradecirse, que es lo que pasaría si el agente escribiera su mitad del JSON a mano.

### `project-context.json` vive adentro de `rutaCodebase`

Al lado de `indice.md` y `mapa.html`. Mismo dueño, mismo ciclo de vida, misma regeneración entera.

La alternativa era un directorio propio con una clave `rutaContexto` en el manifiesto, y se descartó
por lo que ya se aprendió con `rutaCodebase`: `harness.config.json` **sólo se crea si no existe**
(`install.ps1:709`), así que una clave nueva no llega jamás a un proyecto ya instalado, ni después
de un `-Update`. Una clave que la mitad de los proyectos nunca va a ver es una clave que hay que
defaultear en tres lugares distintos.

### Se versiona, y por eso el layout es determinista

Como `mapa.html`, y por el mismo motivo: viaja con el proyecto, se diffea y lo lee cualquiera sin
correr nada.

De ahí sale la única sutileza del hash: **`context_hash` se calcula sobre el documento sin
`context_hash` y sin `generated_at`**. Si el reloj entrara en el hash, dos corridas sobre el mismo
código darían hashes distintos, y `context_hash` dejaría de servir para lo único que sirve —decir si
dos consumidores están mirando lo mismo—. Con el reloj afuera, regenerar sin cambios deja un diff de
una línea en vez de un archivo entero nuevo.

### El schema es JSON Schema de verdad, y el validador interpreta un subconjunto

`jsonschema` no es biblioteca estándar, y `mapa-codigo.py` ya fijó la regla del harness: *"No usa
nada de afuera. Biblioteca estándar"*. Las dos salidas malas eran escribir el contrato dos veces
—una en el `.json` y otra en Python— o no tener contrato publicable.

Así que el schema es un archivo JSON Schema real, y `contexto-armar.py` lo **lee** e implementa a
mano `type`, `required`, `enum`, `pattern`, `items` y `properties`. Una sola fuente de verdad.

🔴 **Si el schema usa una construcción que el intérprete no soporta, el script falla y la nombra.**
Sin esa regla el schema crece —alguien agrega un `oneOf`— y el validador lo ignora en silencio: a
partir de ahí devuelve "válido" sobre documentos que nunca miró, que es peor que no validar, porque
tiene el sello puesto.

### `comun/schemas/` es un `aporta` nuevo

El capítulo 17 del documento es explícito: `PROJECT_CONTEXT` **es un contrato del harness**, no un
detalle privado del agente que lo consume. Van a ser cuatro archivos —`project-context`,
`change-context`, `qa-run-request`, `context-enrichment`— y esconderlos adentro de `comun/reglas/`,
que hoy es el catálogo de patrones de secretos, los archiva donde nadie los va a buscar.

Cuesta una línea en la lista de copia de `install.ps1:1096-1101` y su test.

### El script va en `comun/bin/`, aunque sirva sólo a `desarrollo`

No hay alternativa: el `aporta` de un harness copia `checks`, `skills` y `agents` y nada más
(`install.ps1:1106-1108`). Es el mismo lugar y el mismo motivo por el que `mapa-codigo.py` está ahí
sirviendo únicamente a `dev-iniciador-code`.

### 🔴 `mapa-codigo.py` no se refactoriza. Se le agrega un nombre y nada más

Se evaluó extraer `leer_fichas()` y `armar_grafo()` a un `comun/bin/lib/fichas.py` compartido, y
**se descartó**. Son 797 líneas que hoy están verdes, y el mapa es una pieza terminada: mover código
que funciona para que un archivo nuevo lo pueda importar es cobrarle el riesgo al que ya andaba.

`contexto-armar.py` reusa esas dos funciones **cargando el módulo**, sin copiarlas y sin moverlas.
El guion del nombre impide un `import` normal, así que se carga con
`importlib.util.spec_from_file_location`, que es exactamente el patrón que ya usa
`tests/correr.py:46`. Los dos archivos viven en el mismo directorio, en el repositorio y también
instalados (`.claude/harness/bin/`), así que la ruta se resuelve desde `__file__` y no depende de
nada.

El único cambio que recibe `mapa-codigo.py` es **un nombre más en la exclusión de `leer_fichas()`**,
que hoy excluye únicamente `indice.md`. Es una línea, y E-15 la prueba por el lado que importa: con
`proyecto.md` en el directorio, el `mapa.html` que sale es **byte a byte el mismo** que salía antes.

### `proyecto.md` es un nombre reservado, como `indice.md`

No es una ficha de módulo: no tiene las cuatro secciones, no es un componente y no debe ser un nodo
del grafo. Hay que excluirlo en tres lugares —`leer_fichas()` en el mapa, y `_fichas_en_disco()` y
`_revisar_ficha()` en el check— que viven en archivos que **no se pueden importar entre sí**, porque
el instalador los deja en `.claude/harness/bin/` y `.claude/harness/checks/desarrollo/`.

La constante se define en `mapa-codigo.py`, `contexto-armar.py` la toma del módulo que ya carga, y
`dev-codebase-forma.py` la repite con el motivo escrito al lado. Una duplicación anotada es más
barata que un `sys.path` que sube dos directorios y se rompe el día que el instalador mueva algo.

### Sin repositorio versionado, no se escribe nada

`repo_revision` no es opcional en este contrato. Un `project-context.json` sin él no se puede
consumir según su propia regla, y escribirlo igual sería fabricar un contrato inválido para no tener
que decir que faltaba algo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/project-context.schema.json` | El contrato v1: `meta`, `project_profile`, `sources`, `technology`, `architecture`, `gaps_and_conflicts` |
| `comun/bin/mapa-codigo.py` | **Una línea:** `proyecto.md` se suma a la exclusión de `leer_fichas()`. Nada más se toca |
| `comun/bin/contexto-armar.py` | Lee fichas y `git`, arma el contrato, lo valida contra el schema **antes** de escribirlo, y saca su resumen por stdout. Reusa `leer_fichas()` y `armar_grafo()` cargando `mapa-codigo.py`, sin copiarlas |
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | Dos pasos más: escribir `proyecto.md`, y correr `contexto-armar.py` después del mapa. El informe suma las cifras del contrato |
| `harnesses/desarrollo/checks/dev-codebase-forma.py` | `proyecto.md` pasa a nombre reservado: sin las cuatro secciones y sin línea en el índice |
| `comun/hooks/session-start.py` | El aviso que ya existe suma un tercer estado —índice sí, contrato no— sin agregar una línea más |
| `comun/manifest.json` e `install.ps1` | `schemas` como `aporta`, junto a `hooks`, `reglas`, `checks` y `bin` |
| `tests/casos/13_contexto.py` | Los escenarios del script, el validador y el hook |
| `tests/casos/14-contexto-instalador.ps1` | Los escenarios del reparto del schema |
| `docs/mapa/recorrido-mensaje.html` | La banda del recorrido pasa a nombrar el contrato |

## Escenarios verificables

### El contrato que se escribe

- **E-01** — Sobre un directorio sin fichas, `contexto-armar.py` no escribe ningún archivo, lo dice
  en su resumen y sale con código 0. · rojo visto: si
- **E-02** — El archivo escrito valida contra `comun/schemas/project-context.schema.json`.
  · rojo visto: si
- **E-03** — Dos corridas seguidas sobre las mismas fichas producen archivos que difieren
  **únicamente** en `meta.generated_at`. · rojo visto: si
- **E-04** — El `meta.context_hash` recalculado sobre el archivo escrito —sacándole `context_hash` y
  `generated_at`— da el mismo valor que el archivo trae adentro. · rojo visto: si
- **E-05** — `meta.repo_revision` es el `HEAD` del repositorio que contiene el directorio de fichas.
  · rojo visto: si
- **E-06** — Sobre un directorio que no está en un repositorio git, el script no escribe nada y dice
  que sin `repo_revision` el contrato no se puede consumir. · rojo visto: si

### El validador

- **E-07** — Un documento al que le falta un campo `required` no se escribe: el script sale distinto
  de 0 y nombra el campo que falta. · rojo visto: si
- **E-07b** — `enum` y `pattern` también se verifican. `required` solo no alcanza: un campo presente
  con un valor imposible pasa tan desapercibido como uno ausente. · rojo visto: si

  Agregado durante la construcción. El intérprete soporta seis palabras y el escenario original
  probaba una sola; las otras cinco quedaban sin rojo propio.
- **E-08** — Si el schema usa una construcción que el intérprete no soporta, el script falla y la
  nombra, en vez de dar el documento por válido. · rojo visto: si
- **E-08b** — Y el script entero sale con **código 2**, distinto del 1 de "el documento no valida".
  Son dos problemas distintos y se arreglan en lugares distintos. · rojo visto: si

  🔴 El schema roto se arma en una **copia descartable** del directorio `bin`, nunca sobre
  `comun/schemas/`. Romper un archivo versionado y restaurarlo en un `finally` es exactamente lo
  que dejó `pre-tool-use.py` roto en el árbol durante 0.13.0: el `finally` no sobrevive a que maten
  el proceso. Como el script resuelve el schema como `..\schemas` desde su propio `__file__`,
  alcanza con copiar los dos scripts a un `bin` de mentira.

### Lo que sale de las fichas

- **E-09** — `architecture.components[]` tiene exactamente un elemento por ficha, y
  `dependency_edges[]` exactamente uno por par origen–destino: las mismas cifras que `mapa-codigo.py`
  reporta sobre el mismo directorio. · rojo visto: si
- **E-10** — Una ficha que ninguna otra enlaza aparece en `gaps_and_conflicts.missing[]`.
  · rojo visto: si
- **E-11** — Cada ficha produce una entrada en `sources[]`, con `revision` igual a
  `meta.repo_revision` y `status: current`. · rojo visto: si
- **E-11b** — El `type` de una fuente describe el archivo que va en su `location`, no la unión de
  todo lo que la ficha nombra de paso. · rojo visto: si

  🔴 **Escenario nacido de un bug encontrado al construir, el 2026-08-23.** La primera versión
  miraba todas las rutas de la ficha juntas, y una sola mención de `docs/adr/` adentro de una ficha
  grande tipaba el módulo entero como `adr`. Sobre este repositorio declaró **once ADRs donde hay
  ocho**, y el `type` no describía el `location` que iba al lado: un consumidor que filtrara por
  tipo abría archivos que no eran lo que la etiqueta decía. El escenario existe para que no vuelva.
- **E-11c** — Un bullet de prosa de `## Qué falta saber` entra entero en
  `unresolved_questions[]`, no recortado a su primer span de código. · rojo visto: si

  Del mismo día y de la misma pasada. En las secciones de comandos el bullet vale por lo que hay
  entre comillas invertidas; aplicar ese recorte a la prosa convirtió *"Si `docs/codebase/` sigue
  cubriendo todos los módulos"* en `docs/codebase/`, que no es una pregunta abierta: es una ruta.
- **E-12** — `proyecto.md` no figura en `architecture.components[]` ni produce un nodo en
  `mapa.html`. · rojo visto: si
- **E-12b** — Y sin embargo no se ignora: `project_profile`, `technology`,
  `architecture.entrypoints`, `external_integrations` y `unresolved_questions` salen de ahí.
  · rojo visto: si

  Agregado durante la construcción. E-12 solo decía qué **no** es `proyecto.md`; un archivo que el
  script leyera y tirara a la basura pasaba ese escenario perfecto.
- **E-13** — Sin `proyecto.md`, el contrato se escribe igual: `project_profile` y `technology` salen
  vacíos y `gaps_and_conflicts.missing[]` dice que faltan. Un hueco se declara, no se completa.
  · rojo visto: si
- **E-13b** — Los cinco bloques que el schema v1 todavía no modela —`business_rules`, `interfaces`,
  `identity_and_access`, `environments`, `quality_landscape`— viajan nombrados en
  `gaps_and_conflicts.missing[]`. · rojo visto: si

  Es la mitigación del riesgo que la spec ya declaraba abajo, convertida en escenario: un consumidor
  tiene que poder distinguir *"este proyecto no tiene reglas de negocio"* de *"esta versión del
  contrato todavía no las modela"*.

### Lo que ya existía y no se rompe

- **E-14** — `proyecto.md` no dispara ningún hallazgo de `dev-codebase-forma.py`: ni por faltarle
  las cuatro secciones, ni por no estar nombrado en el índice. · rojo visto: si
- **E-15** — Con `proyecto.md` presente en el directorio, `mapa-codigo.py` escribe el mismo
  `mapa.html` **byte a byte** que sobre el mismo directorio sin `proyecto.md`: mismos nodos, mismas
  aristas, mismo acomodo, mismo panel. · rojo visto: si
- **E-15b** — `contexto-armar.py` no escribe, no mueve y no reescribe `mapa.html` ni ninguna ficha.
  Lo único que toca del directorio es `project-context.json`. · rojo visto: si
- **E-16** — Con `indice.md` presente y sin `project-context.json`, la salida de `SessionStart`
  contiene una línea que nombra al contrato. Con los dos presentes, no aparece ninguna línea de este
  bloque. · rojo visto: si
- **E-16b** — Sin `desarrollo` en el lockfile, ninguna de las tres líneas aparece, aunque no haya
  ni índice ni contrato. Un proyecto de solo análisis no tiene código que recorrer.
  · rojo visto: si

  🔴 **Este cambio le mueve el significado a una fixture de `iniciador-code`, y hay que decirlo.**
  `tests/casos/10_codebase.py` arma sus proyectos con `_proyecto(con_indice=True)` para representar
  *un recorrido terminado*, y usa la cadena `dev-iniciador-code` como marca de que el aviso salió.
  Desde este cambio un recorrido terminado deja **también** `project-context.json`, así que esos
  proyectos pasaron a representar un recorrido a medias — y el hook los avisaba con razón. Cuatro
  afirmaciones se pusieron en rojo: E-02, E-04, E-20 y el test libre de la ruta declarada.

  Lo que se corrigió es **la fixture, no la aserción**: `con_indice=True` ahora escribe el índice y
  su contrato. Las tres afirmaciones de `iniciador-code` siguen diciendo exactamente lo mismo
  —terminado el recorrido, el aviso desaparece— sobre la definición nueva de "terminado", y ninguna
  se debilitó. La alternativa era aflojar la marca a la cadena literal `"Sin indice del codigo
  todavia"`, y eso sí hubiera dejado pasar una línea de más sin que nadie se enterara.

  📌 Queda el parámetro `con_contrato=False` para poder armar el estado intermedio desde ahí el día
  que haga falta. Hoy ese estado lo cubre E-16, que es de quien es el escenario.
- **E-17** — El bloque del recorrido en `SessionStart` sigue agregando **a lo sumo una línea**, con
  cualquier combinación de índice, fichas y contrato. · rojo visto: si

### El instalador

- **E-18** — Tras `install.ps1 -Update`, `.claude\harness\schemas\project-context.schema.json`
  existe y figura en `harness.lock.json`. · rojo visto: si

### Secretos

- **E-19** — Ningún valor del `project-context.json` versionado de este repositorio matchea un
  patrón de `comun/reglas/secretos.patrones.json` con `confianza: alta`. El escenario incluye su
  control positivo: el detector **sí** encuentra sobre `tests/fixtures/corpus-secretos.txt`.
  · rojo visto: si

  🔴 **La palabra "versionado" no la probaba nadie, y se arregló el 2026-08-26.** El test afirmaba
  `archivo.is_file()`, así que un contrato suelto en el árbol —o uno que alguien mandara al
  `.gitignore`— daba exactamente el mismo verde: la aserción afirmaba menos que su propio
  docstring, que ya decía "está commiteado". Lo encontró `harness-spec-refuter` rindiendo sobre la
  spec del paso 4, y en ese momento el archivo efectivamente **no estaba versionado**.

  Ahora la aserción es `git ls-files --error-unmatch`, y el archivo está seguido por git. Rojo
  propio visto: des-stageado el archivo, `13_contexto` cae con
  `E-19: el contrato esta versionado, no suelto en el arbol es falso` y ninguna otra aserción se
  mueve — 419/420. Restaurado, 421/421.

### Lo que sólo se puede leer

- **E-20** — El contrato que escribe un recorrido real describe el proyecto que recorrió y no lo
  inventa: `project_profile.purpose` y `technology` se corresponden con lo que hay en el repositorio.
  · rojo visto: no consta
  · verificación: lectura — el sujeto es una corrida de un modelo, y la suite no invoca al agente

## Cómo se verifica

**Por la suite, E-01 a E-19, E-15b incluido.** Todos son propiedades de un archivo generado por un script
determinista, de un hook o del instalador. Ninguno necesita que corra un agente: los que hablan de
fichas se prueban sobre fixtures escritas a mano, y E-19 se prueba sobre la salida **real y
versionada** de `docs/codebase/` de este repositorio — que la escribió `dev-iniciador-code` y está
commiteada — más su control positivo.

📌 El control positivo de E-19 no es un adorno. Sin él, un catálogo de patrones que no carga da
exactamente el mismo verde que un contrato limpio. Es la corrección que ya se pagó una vez en E-10
de `iniciador-code`.

**Por lectura, E-20 solamente**, según ADR-0009: el sujeto es una corrida de un modelo y no hay test
determinista que lo alcance. Lo firma alguien que no construyó, con fecha.

## Riesgos conocidos

- **El mapa recibe una línea, y es todo el riesgo que se le carga.** No hay refactor: `mapa.html`
  tiene que seguir saliendo idéntico, y E-15 y E-15b lo fijan por los dos lados —lo que el mapa
  dibuja y lo que el script nuevo toca—. Si E-15 sale en rojo, lo que se revierte es una línea, no
  una extracción.
- **El intérprete de schema es un subconjunto, y puede quedar atrás.** E-08 lo protege de fallar en
  silencio, pero no impide que alguien necesite un `oneOf` y se encuentre con que el harness no lo
  soporta. La respuesta correcta ese día es ampliar el intérprete, no ampliar el schema.
- **La constante de nombres reservados vive en dos archivos.** Si alguien agrega un tercer nombre en
  `mapa-codigo.py` y se olvida de `dev-codebase-forma.py`, el check reporta un archivo que el mapa
  ya ignora. Ningún test cruzado lo cubre hoy.
- **`contexto-armar.py` carga `mapa-codigo.py` por ruta.** Si alguien renombra o mueve el mapa, el
  script nuevo deja de encontrarlo. Falla ruidosamente —no puede armar `architecture` sin el
  grafo— pero el acoplamiento existe y no lo declara ningún manifiesto.
- **Un contrato v1 sin `business_rules` puede leerse como "este proyecto no tiene reglas".** El
  consumidor todavía no existe, así que el riesgo no se materializa en esta versión; la mitigación
  cuando aparezca es que `gaps_and_conflicts` diga explícitamente qué bloques no modela el schema
  v1, y no que queden ausentes sin explicación.
