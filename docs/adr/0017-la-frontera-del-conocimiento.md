---
estado: aceptada
creado: 2026-10-18
---

# ADR-0017 — La frontera del conocimiento

## Contexto

Hasta ahora, un modelo o un script que necesitaba leer un documento del proyecto sabía dónde estaba. El
resolvedor de repositorio de Work Intake armaba la ruta de `project-context.json` y abría el archivo; la
refutación tiene esa ruta fija. Nada de lo que se leía traía su cita ni su revisión, y quien leía no
sabía qué no había podido mirar. Task 7 va a poner una recuperación más rica detrás de la lectura
(índice, embeddings, ranking), y sin una frontera escrita antes, el contrato y el mecanismo se
diseñarían juntos.

El relevamiento y el diseño están en `docs/cambios/knowledge-api/spec.md` (Task 6), con 32 decisiones
`KD-nn` y los conflictos decididos `KC-nn`. Los que pesan en estas decisiones:

- **«Knowledge» ya tenía cuatro sentidos en el modelo canónico**: normas, notas, confianza de sección y
  Ficha. Lo que devuelve una consulta no es ninguno de los cuatro (KD-02);
- **el límite reservado de ADR-0013 era para algo nombrado y vacío**, sin lenguaje ni implementación.
  Esta frontera tiene lenguaje propio, invariantes, datos y ciclo de vida, y ADR-0013 se revisa «si
  aparece un contexto que no quepa» (KC-17);
- **ADR-0008 dice que lo externo nunca es requisito**: un recuperador más rico se aprovecha y no se
  requiere, así que el camino que existe sin él tiene que quedar para siempre;
- **la corrección del SPEC REVIEW**: el respaldo en el recuperador local es de selección y ocurre antes
  de llamar a `buscar`; `knowledge-result/1.0` es un contrato cerrado; y las señales de control del
  proceso no se capturan.

## Decisión

### 1. Knowledge Access es el undécimo contexto, de solo lectura y sin estado

Knowledge Access es un contexto delimitado: lenguaje propio (consulta, `lookup`, `search`, corpus,
documento, cita, ancla, revisión, tramo, cobertura, hueco, recuperador), invariantes propias (solo
lectura; cada ítem trae su cita y su revisión; lo no mirado se declara; ningún secreto sale; un id
nunca se vuelve ruta), datos (el catálogo de corpus, en código) y ciclo de vida (por consulta). No tiene
agregado raíz: no hay nada que se escriba. Sus cuatro conceptos son KnowledgeQuery, KnowledgeResult,
KnowledgeCitation y KnowledgeCorpus; la fachada, el lector y el recuperador son infraestructura, no
conceptos. Es una interfaz de Python interna: sin REST, sin subcomando, sin servidor MCP y sin
capability `knowledge.*`.

### 2. Dos operaciones, y un contrato cerrado

`lookup` trae un documento por `(corpus, document)`: exacto, sin recuperador, un documento o un error.
`search` trae tramos literales de los corpus pedidos para un texto, por un recuperador: devuelve
candidatos con su procedencia y no afirma ausencia. No se fusionan en una sola operación, porque su
semántica de vacío es distinta: un id que no está es un error, y un `search` vacío con cobertura completa
es un éxito. Las dos devuelven un KnowledgeResult, `knowledge-result/1.0`, que es un **contrato
cerrado**: no se agrega ni se quita ni cambia de sentido ninguna clave, y ningún enum se amplía ni se
achica. Una clave nueva, un valor nuevo de un enum o una forma nueva piden otra versión del contrato.
No hay schema y nada se persiste: lo fijan la spec y la suite.

### 3. La cita es `(corpus, documento, ancla)`, y la revisión, el hash del documento entero

Cada ítem trae su cita `(corpus, documento, ancla)`, que no depende de la ruta, de la revisión, del
reloj ni del recuperador, y su revisión: el sha256 del texto normalizado del documento entero (UTF-8
estricto, sin BOM, con `\n`), leído una sola vez por consulta. El tramo y sus líneas salen de esa misma
lectura. La ruta es un localizador relativo y nunca identifica. No hay git, ni reloj, ni score.

### 4. Los corpus son una tabla cerrada en código, y un id nunca se vuelve ruta

Cuatro corpus: `adr`, `dominio`, `codebase` y `memoria`. Cada uno declara su raíz, qué archivos son
documentos, cómo se identifica cada uno y su derivación: `PRIMARY` en los dos primeros y `GENERATED` en
los otros, siempre por el corpus y nunca por el contenido. Ningún consumidor amplía la tabla y ninguna
configuración suma una raíz: solo `rutaCodebase` y `rutaMemoria` salen de la configuración, y se
validan. Un id nunca se vuelve ruta: `lookup` enumera el corpus, calcula el id de cada archivo y busca
el pedido entre esos, y la contención es por `realpath` en cada carpeta y cada archivo. Antes de abrir un
archivo se aplica el deny del proyecto, y lo que sale pasa por el catálogo de secretos; sin catálogo o
sin un deny legible no sale contenido. Quedan afuera la normativa, las specs, el `CLAUDE.md`,
`Pendientes/` y todo `.claude/`.

### 5. El recuperador es infraestructura detrás de una fachada, y el léxico local es permanente

El puerto es interno: una identidad y `buscar(texto, lector)`, que devuelve candidatos
`(corpus, documento, líneas)`. La fachada hace cumplir el contrato sobre cualquier recuperador: valida
cada candidato, descarta los repetidos, corta el tramo de su propia lectura, redacta y declara. Un
recuperador no puede pasarle texto ni claves propias. `local-lexico/1`, solo con la biblioteca estándar y
sin red ni modelo, es el recuperador de Task 6 y es **permanente**, por ADR-0008: uno más rico de Task 7
se suma detrás del mismo contrato.

El respaldo es de **selección**: si el recuperador opcional no existe o no se puede inicializar, se elige
`local-lexico/1` antes de llamar a `buscar`. Una falla desde que se llamó a `buscar` (una excepción
ordinaria, algo que no es una lista o un candidato inválido) termina `ERROR` con `RETRIEVAL_FAILED`, y la
consulta no se vuelve a correr con otro recuperador: el resultado de uno no esconde la falla de otro.
`lookup` y `search` convierten las fallas operacionales ordinarias, las que derivan de `Exception`;
`KeyboardInterrupt`, `SystemExit` y lo que no deriva de `Exception` se propagan, sin código propio.

### 6. Planning, Execution y los agentes no la consumen en Task 6

Ni la admisión, ni el motor, ni el GraphRun, ni el Host Adapter la llaman, y tampoco lo hacen Planning,
los hooks o los agentes, que siguen con `repository.read` y `repository.search`. Ningún contrato de
Task 3, Task 4 o Task 5 cambia: ni `execution-request/1.0`, ni `execution-result/1.0`, ni
`graph-run-result/1.0`, ni `orchestration-plan/2.1`, ni `task-context/1.0`. El primer consumidor es el
resolvedor de repositorio de Work Intake, que pide el `project-context` por `lookup` y deja de conocer
dónde está el archivo. La refutación no se migra: queda como pendiente.

### 7. Nada se persiste, y no hay caché entre consultas

Nada se persiste: ni consultas, ni historial, ni índice. Dentro de una consulta, cada documento se lee una
sola vez. Una consulta interrumpida no deja estado propio que recuperar.

## Consecuencias

A favor:

- Un consumidor pide un documento por su identidad y recibe su cita y su revisión: deja de conocer rutas,
  y una cita sobrevive a mover `rutaCodebase` o a instalar el mismo documento en otro árbol.
- El contrato sobrevive a Task 7: lo que ella cambia está detrás de `search` (índice, chunking,
  embeddings, ranking), y la suite de conformidad es su compuerta. La consulta, el resultado, la cita y
  los errores no cambian bajo `1.0`.
- Lo que no se pudo mirar se declara: un resultado vacío con cobertura completa es un éxito, y uno con
  huecos dice cuáles y por qué. Los errores son siete códigos cerrados, sin texto libre.
- Ningún secreto de confianza alta sale, y un archivo denegado no se abre. Sin catálogo o sin deny, no
  sale contenido.
- No entra una dependencia, y ningún archivo ni contrato de Task 3, 4 o 5 cambia.

En contra, y dicho:

- **Un undécimo contexto sin datos propios hasta Task 7**: lo que ADR-0013 evitaba era un límite sin
  lenguaje ni implementación, y este tiene los dos, pero su estado persistido llega con el índice.
- **«Knowledge» nombra ahora un contexto** que convive con Project Knowledge y con NormativeKnowledge: la
  palabra suma un quinto sentido, y el vocabulario del modelo canónico lo desambigua.
- **Una búsqueda sin consumidor de producto**: `search` entra declarado y lo ejercita la suite de
  conformidad, así que su forma no tiene evidencia de uso real.
- **Un `search` vacío no prueba ausencia**, ni siquiera con `complete: true`: otro recuperador puede
  encontrar lo que este no. Quien se apoye en que un ítem contiene las palabras de la consulta se rompe
  en Task 7.
- **Editar una sección cambia la revisión de toda cita del documento**: la señal es «volvé a mirar», no
  «cambió lo citado».
- **Seis guardas de otras suites cambian**: tres por el mapa de diez a once contextos, una por el catálogo
  de 85 a 89 conceptos y dos por el lock instalado, de 294 a 298 rutas y el archivo viejo que modifica la
  migración del primer consumidor. Cada una lleva su comentario.
- **El `codebase` se sirve aunque esté atrasado**: sale marcado `GENERATED`, y compararlo con el HEAD es
  de su productor.
- **Cada consulta recorre el corpus entero**, sin índice ni caché: el corpus de hoy mide unos cientos de
  KB, y crecer es el disparador de Task 7.

## Alternativas descartadas

- **Un Domain Service dentro de Project Knowledge, sin contexto nuevo**: el lenguaje de una consulta, sus
  invariantes y dos de sus cuatro corpus no son de Project Knowledge, y el índice de Task 7 obligaría a
  mover un concepto de contexto, que es la cláusula de revisión de ADR-0013.
- **Una sola operación, `retrieve()`**: la semántica de vacío de `lookup` y de `search` es distinta, y
  `lookup` no puede pasar por el recuperador, porque Task 7 no lo reemplaza.
- **El recuperador local como reintento después de una falla**: esconde el defecto de un recuperador que
  propone algo fuera del contrato. El respaldo se elige antes de llamar a `buscar`.
- **Un contrato abierto, con claves opcionales**: `schema_version` promete todo documento que el schema
  declara válido (ADR-0013, punto 6). Una clave nueva es otra versión.
- **Un puntaje, una hora de recuperación, un `queryId` o un límite en la consulta**: el puntaje no se
  compara entre recuperadores, la hora y el id rompen el resultado byte a byte, y un límite configurable
  pide versionar el contrato.
- **La ruta como identidad de un documento**: ata al almacenamiento y se parte en dos entre la fábrica y
  un proyecto instalado.
- **Raíces declaradas en la configuración**: `harness.config.json` no se actualiza después de instalar, y
  una raíz escrita por una persona podría ser `C:/`.
- **Una capability `knowledge.*`, un subcomando o un servidor MCP**: declarar una capability sin
  proveedor la vuelve «disponible» en todo plan y la rechaza al entregar.
- **KnowledgeSource, Retriever y Chunk como conceptos**: «source» ya tiene siete sentidos, el recuperador
  es infraestructura y el chunk no es un contrato.
- **Migrar la refutación, Planning o los agentes en esta Task**: están fijados contra `v0.33.0`, y
  migrarlos es otra Task.

## Revisión

**Revisa ADR-0013 sin editarlo**, como ADR-0014 revisó su punto 4: su apartado «Revisión» prevé que se
revisa si aparece un contexto que no quepa en los que tiene, y Knowledge Access es el undécimo.
ADR-0013, ADR-0014, ADR-0015 y ADR-0016 no se editan, porque son historia, y los dos invariantes del
punto 4 de ADR-0013 siguen. Este ADR se revisa cuando Task 7 persista un índice, cuando un agente consuma
Knowledge Access, o si `knowledge-result` necesita otra versión.
