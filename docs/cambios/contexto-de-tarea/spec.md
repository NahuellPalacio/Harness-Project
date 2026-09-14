# Bloque 2 — Context Resolution: de una clave de Jira a un `TaskContext`

**Estado:** especificado · **Fecha:** 14-09-2026

## Qué problema resuelve

0.16.0 dejó al harness sabiendo **con qué puede hablar**. No sabe **qué preguntar**. Hoy, ante
"trabajá GCBA-1234", lo único que puede hacer un agente es pedir ese issue y leerlo: el ticket dice
qué hay que hacer y casi nunca por qué, a qué proyecto pertenece, qué reglas rigen, qué PRD lo
respalda, qué decisión arquitectónica ya se tomó o en qué repositorio se toca.

Esa información existe y está repartida: el ticket en Jira, el conocimiento del proyecto en otro
ticket de Jira —la **Ficha de Proyecto**—, los documentos como adjuntos de esa ficha, y el estado
técnico en GitLab. Cada agente que la necesite hoy tendría que ir a buscarla solo, con su propio
criterio y sus propias llamadas.

Este cambio construye el resolvedor: una clave de Jira entra, y sale un documento estructurado —el
`TaskContext`— que contesta esas preguntas o declara que no pudo. El límite es ese: lo que se haga
con el contexto es el Bloque 3.

## Qué queda afuera

- **Todo el Bloque 3.** Orquestación, agent loops, el agente que consume el `TaskContext` y las
  tools que se le entregan. Este cambio produce el insumo; decidir cómo se consume con un consumidor
  que todavía no existe sería adivinar su forma.
- **Elegir qué documento es relevante para esta tarea.** El `TaskContext` declara el corpus del
  proyecto con su clasificación y su origen; cuál de esos documentos hay que leer para GCBA-1234 es
  una decisión semántica y la toma quien tenga un modelo, no un resolvedor determinista. Fingir lo
  contrario —filtrar por palabras del título, por ejemplo— esconde un descarte adentro de un paso
  que parece mecánico.
- **Los comentarios del ticket.** Un hilo de comentarios es negociación, no especificación: mezcla
  lo decidido con lo discutido, y duplica el tamaño del contexto. Queda declarado como riesgo,
  porque a veces el criterio de aceptación real vive ahí.
- **Escribir en Jira o en GitLab.** Todo sigue siendo de lectura, por la misma decisión de 0.16.0.
  Ninguna capacidad nueva escribe.
- **Un caché con vencimiento.** Cada resolución vuelve a preguntar salvo que se pida lo contrario
  explícitamente. Un caché obliga a decidir cuánto dura y a explicar por qué el contexto dice una
  cosa que en Jira ya cambió.
- **SharePoint, Confluence y cualquier tercera fuente.** Explícito en el pedido: la documentación
  vive en la Ficha de Proyecto.
- **Reconstruir lo que `project-context.json` ya sabe.** El recorrido del código lo hace
  `dev-iniciador-code` desde 0.14.0 y su contrato ya existe. El `TaskContext` lo **referencia**, con
  su hash, y no vuelve a recorrer nada.
- **Autenticación, tokens y clientes HTTP propios.** Son del Bloque 1. Este bloque consume los
  adapters y el registro de capacidades, y no conoce un solo secreto.

## Las decisiones, y por qué

### Una capacidad ausente no es un error: es un hueco declarado

Cada resolvedor pregunta al registro de 0.16.0 antes de llamar, y si la capacidad no está
`ENABLED` no llama: escribe el hueco en `gaps_and_conflicts.missing_capabilities` y sigue. Sin
GitLab el `TaskContext` sale igual, sin la sección técnica y diciendo por qué.

La única excepción es `jira.issue.read`: sin eso no hay tarea que resolver y el comando sale con
código 2. Un contexto de una tarea que no se pudo leer no es un contexto degradado, es otra cosa.

### La Ficha de Proyecto se busca por tipo de issue, una por proyecto Jira

`fichaTipoDeIssue` en `harness.config.json`, con default `Ficha de Proyecto`. Se busca por JQL
dentro del mismo proyecto Jira del ticket.

Si hay más de una, **no se elige ninguna**: las dos claves van a `gaps_and_conflicts.conflicts` y la
ficha queda vacía. Elegir la primera por fecha sería inventar un criterio que nadie escribió, y el
contexto saldría con el sello de resuelto sobre una elección invisible. Es la misma regla que ya
aplica `project-context`: *se marca el conflicto; no se elige una realidad en silencio.*

Se descartó el Epic padre: un Epic es trabajo, no conocimiento, y confundirlos hace que el
conocimiento del proyecto herede el ciclo de vida de una entrega.

### Un documento se clasifica por su nombre, y la inferencia se declara

`prd`, `adr`, `regla`, `arquitectura`, `manual`, `diagrama`, `otro`, por patrones sobre el nombre
del archivo y el título del adjunto. Es una heurística y sale marcada `knowledge_status: inferred`,
nunca `confirmed`. La alternativa —abrir cada documento para clasificarlo— es una decisión
semántica, y ya está declarada afuera.

### El texto se extrae si markitdown está, y se declara si no

ADR-0008 al pie: el harness **no** instala markitdown, **no** lo asume presente y **degrada** sin
él. Con markitdown en la máquina, cada adjunto convertible entra con su texto; sin markitdown, entra
con su ruta local y un hueco que dice qué falta y cómo se arregla. Lo que nunca pasa es que el
`TaskContext` mienta sobre si el contenido está.

Se descartó escribir un extractor propio de PDF y OOXML: son semanas de trabajo para un parser peor
que los que ya existen, y ninguno de los dos caminos es obligatorio para que el bloque sirva.

### El texto que viene de afuera pasa por el detector de secretos antes de tocar el disco

Una descripción de Jira puede traer un token pegado por alguien. Si el harness lo escribe en el
`TaskContext`, acaba de crear un archivo con un secreto adentro, y encima uno que un agente va a
leer entero.

Todo texto que entra —descripción, criterios, ficha, texto extraído de un documento— pasa por
`comun/hooks/lib/secretos.py`, el mismo catálogo que ya bloquea escrituras desde el hook. Lo que
dispara un patrón de confianza alta se reemplaza por su muestra segura y el hallazgo se declara en
los huecos. **El catálogo no se duplica: se importa.**

### El registro de capacidades se lee, no se revalida

`contexto` lee `.claude/harness.capacidades.json`, que escribió el bootstrap. Revalidar en cada
resolución agrega entre dos y seis llamadas HTTP antes de empezar el trabajo real, en el camino
caliente.

El precio es que el registro puede estar viejo —un token que venció después de la última corrida— y
por eso cada llamada real maneja su propio fallo: un 401 en el medio de la resolución degrada esa
sección y lo declara, no voltea el comando. `--revalidar` fuerza el bootstrap antes de resolver.

### El contrato tiene schema desde el día uno, y reusa el validador que ya existe

Al revés que en 0.16.0, acá el consumidor es otro agente por definición: para eso se escribe. El
schema va en `comun/schemas/task-context.schema.json`, del mismo lado que `project-context`, y se
valida con el intérprete de subconjunto que ya vive en `comun/bin/contexto-armar.py`, importado por
ruta. **Un segundo validador de JSON Schema en el mismo repositorio sería la misma decisión tomada
dos veces, con dos comportamientos.**

### El vocabulario es el de `project-context`, a propósito

`knowledge_status` con sus cinco valores, `gaps_and_conflicts` con sus listas, las claves en inglés.
`dev-refutador` ya sabe leer ese vocabulario desde 0.14.0. Inventar uno nuevo obligaría a enseñarle
dos.

### El `TaskContext` no se versiona

`.claude/contextos/<CLAVE>.json`, afuera del repositorio del proyecto, como todo lo de `.claude/`.
Es contenido de Jira: texto de tickets, a veces con datos de terceros, y no tiene por qué entrar al
git de un proyecto. Se regenera con un comando, que es la definición de regenerable que ya usa el
harness.

Queda a un costado del `.claude/harness/` que el `-Update` mueve, igual que `harness.config.json`:
una actualización del harness no borra los contextos que alguien resolvió.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/task-context.schema.json` | El contrato `task-context/1.0`, validable |
| `harnesses/desarrollo/bin/contexto/tarea.py` | Jira Task Resolver: el issue a campos normalizados |
| `harnesses/desarrollo/bin/contexto/proyecto.py` | Project Resolver: encuentra la Ficha de Proyecto y la lee |
| `harnesses/desarrollo/bin/contexto/documentos.py` | Document Resolver: adjuntos, descarga y extracción |
| `harnesses/desarrollo/bin/contexto/repositorio.py` | GitLab Resolver: proyecto, ramas y MRs que nombren la clave |
| `harnesses/desarrollo/bin/contexto/limpieza.py` | Redacción de secretos y topes de tamaño |
| `harnesses/desarrollo/bin/contexto/ensamblador.py` | Context Assembler: arma el documento y sus huecos |
| `harnesses/desarrollo/bin/integraciones/jira.py` | Crece: `issue`, `buscar`, `adjuntos`, `bajar_adjunto` |
| `harnesses/desarrollo/bin/integraciones/gitlab.py` | Crece: `proyecto`, `ramas`, `merge_requests` |
| `harnesses/desarrollo/bin/dev-harness.py` | Subcomando `contexto <CLAVE>`, con `--json` y `--revalidar` |
| `harnesses/desarrollo/manifest.json` | `fichaTipoDeIssue`, `campoCriteriosAceptacion`, `topeTextoDocumento` |
| `docs/contexto-de-tarea.md` | Qué resuelve, qué declara como hueco y cómo se lee el documento |
| `tests/casos/19_contexto.py` | Los escenarios de resolución, ensamblado y contrato |
| `tests/casos/19-contexto-tarea-instalador.ps1` | Lo que deja el instalador y lo que sobrevive |

## Escenarios verificables

### La resolución de la tarea

- **E-01** — Con `jira.issue.read` disponible, una clave existente produce un `TaskContext` con
  clave, tipo, título, descripción, estado y prioridad tomados del issue. · rojo visto: si
- **E-01b** — La descripción en Atlassian Document Format se aplana a texto plano, conservando el
  texto y los saltos entre bloques; una que ya es texto plano pasa igual. · rojo visto: si
- **E-02** — Los criterios de aceptación salen del campo que los tiene y, si no hay ninguno, la
  lista queda vacía y el hueco se declara — nunca se inventan a partir de la descripción.
  · rojo visto: si
- **E-03** — Sin `jira.issue.read` en el registro, el comando sale con código 2 y un mensaje que
  dice que corra el setup, **sin hacer ni una llamada**. · rojo visto: si
- **E-04** — Un issue inexistente —404— sale con código 2 nombrando la clave, no con una traza.
  · rojo visto: si
- **E-05** — El padre y los enlaces del issue entran como referencias —clave y tipo de enlace—,
  nunca como issues resueltos: un contexto que sigue enlaces sin límite termina bajando el proyecto
  entero. · rojo visto: si

### La Ficha de Proyecto

- **E-06** — Con una sola ficha del tipo configurado en el proyecto Jira del ticket, sus campos
  entran en `project.ficha` y su clave queda en `sources`. · rojo visto: si
- **E-07** — Con dos fichas, no se elige ninguna: las dos claves van a `conflicts` y
  `project.ficha` sale vacía con `knowledge_status: conflicted`. · rojo visto: si
- **E-08** — Sin ninguna ficha, `project.ficha` sale vacía con `knowledge_status: missing` y el
  hueco dice qué tipo de issue se buscó y en qué proyecto. · rojo visto: si
- **E-09** — El tipo de issue de la ficha sale de `fichaTipoDeIssue` en `harness.config.json`, y un
  proyecto que no tiene la clave usa el default `Ficha de Proyecto`. · rojo visto: si
- **E-10** — Sin `jira.issue.search` disponible no se busca la ficha: se declara la capacidad
  ausente y el resto del contexto se arma igual. · rojo visto: si

### Los documentos

- **E-11** — Los adjuntos de la ficha entran con nombre, tipo, tamaño y origen, ordenados y sin
  duplicados. · rojo visto: si
- **E-12** — Sin `jira.attachment.read`, no se baja nada: la sección queda con el inventario vacío
  y la capacidad ausente declarada. · rojo visto: si
- **E-13** — Con markitdown disponible, un adjunto convertible entra con su texto y
  `extractor: markitdown`; el mismo adjunto sin markitdown entra con `extractor: ninguno`,
  `texto_extraido: false` y el hueco que dice cómo se arregla. · rojo visto: si
- **E-14** — La clasificación de un documento sale de patrones sobre su nombre y viaja marcada
  `inferred`, nunca `confirmed`. · rojo visto: si
- **E-15** — El texto extraído se recorta en `topeTextoDocumento` y el recorte se declara en el
  documento y en los huecos: un contexto que se come el presupuesto entero no es utilizable.
  · rojo visto: si

### El repositorio

- **E-16** — El proyecto GitLab sale de la ficha o de la configuración; sin ninguno de los dos, la
  sección queda vacía con su hueco y no se busca nada. · rojo visto: si
- **E-17** — Las ramas y los merge requests que entran son los que nombran la clave del ticket en
  su nombre o su título; el resto no entra. · rojo visto: si
- **E-18** — Sin `gitlab.branch.read` o sin `gitlab.merge_request.read`, cada lista queda vacía con
  su capacidad declarada, de forma independiente de la otra. · rojo visto: si
- **E-19** — Si el proyecto tiene `docs/codebase/project-context.json`, el `TaskContext` lo
  referencia con su ruta y su `context_hash`, y no copia su contenido. · rojo visto: si

### El ensamblado y los huecos

- **E-20** — `sources` —en la raíz del documento, al lado de `meta`— lista una fuente por cada
  cosa que se leyó, con su tipo y el momento en que se obtuvo. · rojo visto: si
- **E-21** — Un fallo en el medio —un 401 cuando el registro decía `AVAILABLE`— degrada su sección,
  la declara en los huecos y no voltea el comando. · rojo visto: si
- **E-22** — Con Jira disponible y GitLab caído, el documento sale completo en su mitad funcional y
  el comando sale con código 0. · rojo visto: si

  📌 **El primer test de este escenario no lo probaba.** Simulaba "GitLab caído" sacándole las
  capacidades al registro —que es la condición de E-18, no la de este— y nunca corría el comando,
  así que la mitad que importa, el código de salida, no la medía nadie. Lo encontró el refutador.
  El test se reescribió: el registro dice `ENABLED`, como diría después de un bootstrap exitoso, y
  GitLab contesta 500 en la llamada real — que es lo que pasa cuando el servidor se cae entre una
  corrida y la siguiente.
- **E-23** — Ninguna sección se inventa: lo que no se pudo resolver sale vacío con su
  `knowledge_status`, y nunca con un valor por defecto que parezca un dato. · rojo visto: si

### Los secretos

- **E-24** — Una descripción de Jira que trae un token de confianza alta no llega al `TaskContext`:
  el valor se reemplaza por su muestra segura y el hallazgo se declara en los huecos.
  · rojo visto: si
- **E-25** — Lo mismo vale para el texto extraído de un documento y para los campos de la ficha:
  ninguna ruta de entrada esquiva la limpieza. · rojo visto: si

  🔴 **Este escenario estuvo contradicho, y tenía razón.** La primera implementación redactaba
  campo por campo, y dos rutas nombradas en este mismo documento no estaban: los criterios de
  aceptación y el `title` de la Ficha. Un token pegado en cualquiera de los dos llegaba al archivo
  escrito. Lo encontró el refutador corriendo la CLI de verdad, y la suite no lo veía porque ningún
  test configuraba el campo de criterios con texto sucio.

  **El arreglo no fue agregar dos llamadas.** Redactar en cada lugar donde se arma un campo obliga
  a acordarse una vez por campo, para siempre, y el campo número veinte lo escribe alguien que no
  leyó esta discusión. La redacción se movió al ensamblador y recorre el documento entero —
  `sources` incluido, que fue donde apareció la tercera fuga: la referencia de una fuente es el
  nombre de una rama. Ahora "ninguna ruta esquiva la limpieza" es una propiedad de la estructura,
  no una promesa.
- **E-26** — El catálogo de patrones que usa la limpieza es el mismo archivo que usa el hook, no una
  copia: agregar un patrón ahí lo hace valer también acá, sin tocar este código.
  · rojo visto: si

- **E-26b** — Lo de confianza media se declara en los huecos y **no toca el texto**: en el hook lo
  ambiguo pregunta y decide una persona, y acá no hay a quién preguntarle. · rojo visto: si

### El contrato

- **E-27** — El documento que se escribe valida contra `comun/schemas/task-context.schema.json`, y
  el validador es el que ya existe en `comun/bin/contexto-armar.py`. · rojo visto: si
- **E-28** — Si el schema usa una construcción que el validador no interpreta, falla en vez de dar
  el documento por válido — la misma regla que ya declara `project-context`. · rojo visto: si
- **E-29** — `meta.context_hash` es el del contenido y se puede recomputar leyendo el archivo; el
  reloj no entra, así que dos resoluciones de la misma clave sobre los mismos datos dan el mismo
  hash. · rojo visto: si

  📌 **El escenario decía "`context_id` y `generated_at` identifican la corrida" y así escrito lo
  satisfacía un ensamblador que escribiera una constante.** La primera versión del test no podía
  fallar: comparaba el hash de un documento contra sí mismo. Al escribir la aserción que sí falla
  —que el hash escrito es el del contenido— apareció un defecto real: `context_id` se escribía
  **después** de calcular el hash, y `canonico` no lo saca del cálculo, así que el documento cambiaba
  después de hashearse y su hash dejaba de ser recomputable por quien lo lee. Se corrigió el código:
  el id se escribe antes y no deriva del hash. El escenario se reescribió para decir lo que importa,
  que es que el hash sirva para lo único que sirve — contestar si dos consumidores están mirando lo
  mismo.

  📌 **Y lo que el escenario dejó de afirmar, dicho en voz alta:** `context_id` ahora es
  `tsk_<clave>`, constante entre corridas. Identifica la tarea, no la corrida. Lo que distingue dos
  resoluciones es `context_hash`, que está al lado.

### La CLI y el instalador

- **E-30** — `contexto GCBA-1234` escribe `.claude/contextos/GCBA-1234.json` e imprime un resumen
  legible; con `--json` el documento sale por stdout y el resumen por stderr. · rojo visto: si
- **E-30b** — `contexto` sin una clave con forma de clave sale con código 2 y muestra el ejemplo,
  en vez de salir a buscar algo que no existe. · rojo visto: si
- **E-31** — Una segunda corrida de la misma clave pisa el archivo anterior y no acumula versiones:
  el contexto es el de ahora, no una bitácora. · rojo visto: si
- **E-32** — `-Update` no borra `.claude/contextos/`, y `-Uninstall` tampoco. · rojo visto: si
- **E-33** — Con `desarrollo` instalado quedan los módulos de `contexto/` y el schema
  `task-context.schema.json` bajo `.claude/harness/`. · rojo visto: si

## Cómo se verifica

Los treinta y seis son deterministas; ninguno tiene por sujeto una corrida de un modelo, así que no
hay escenario de lectura en este cambio.

- **E-01 a E-31**, con sus insertados, corren en `tests/casos/19_contexto.py`, con el mismo
  transporte falso que 0.16.0 —un servidor de Jira y uno de GitLab que devuelven respuestas
  fijas— sobre proyectos temporales. E-13 corre las dos mitades simulando markitdown presente
  y ausente, nunca invocándolo de verdad.
- **E-32 y E-33** corren en `tests/casos/19-contexto-tarea-instalador.ps1` sobre proyectos
  descartables.

Ningún test sale a la red.

## Riesgos conocidos

- **Los criterios de aceptación no tienen un campo estándar en Jira.** Pueden estar en un custom
  field, en la descripción bajo un encabezado, o en ningún lado. Este cambio lee el campo
  configurado y, si no hay, declara el hueco — pero la primera corrida contra el Jira del organismo
  es lo que va a decir si ese campo existe y cómo se llama.
- **La Ficha de Proyecto no existe todavía en ningún Jira real.** Es un concepto que este bloque
  introduce. Si el organismo termina modelándola distinto —un proyecto Jira aparte, un espacio de
  Confluence— el Project Resolver cambia de estrategia, aunque el contrato que produce no.
- **Los comentarios quedan afuera y a veces ahí está el criterio real.** Declarado como exclusión
  con su motivo; si la primera corrida real lo desmiente, entra con su propio escenario y su tope.
- **La limpieza de secretos puede recortar un texto legítimo.** El catálogo tiene patrones de
  confianza media que preguntan en vez de bloquear cuando corre en el hook; acá no hay a quién
  preguntar, así que **solo los de confianza alta redactan** y los de media se declaran en los
  huecos sin tocar el texto. Un falso positivo que mutile una descripción es peor que un aviso.
- **`markitdown` corre en un venv propio.** `docimg.py` ya documenta esa ruta y este bloque hereda
  el problema: encontrar el intérprete correcto en una máquina ajena es best-effort, y por eso la
  ausencia es un camino soportado y no una falla.
