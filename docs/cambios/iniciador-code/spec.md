# El primer recorrido del código: `dev-iniciador-code`

**Estado:** especificado · **Fecha:** 2026-08-21

## Qué problema resuelve

Un agente que abre un proyecto por primera vez no sabe nada de ese código, y la única forma que
tiene de averiguarlo es grepear y leer archivos. Lo hace en el turno uno, y lo vuelve a hacer en el
turno cuarenta, porque nada de lo que averiguó quedó escrito. Es el mismo trabajo pagado muchas
veces, y se paga en la ventana de contexto de la persona que estaba haciendo otra cosa.

El harness hoy tampoco tiene un primer paso. Se instala, y después no pasa nada hasta que alguien
escribe algo: el momento en que más útil sería —antes de que nadie conozca el código— pasa sin
usarse.

Este cambio construye ese primer paso: un agente que recorre el repositorio una vez y deja escrito
qué hay, para que las sesiones que vengan lo lean en vez de re-derivarlo.

Es la primera banda del `docs/mapa/recorrido-mensaje.html`, y es la mitad concreta del ítem abierto
*"The workflow of each harness cannot be drawn"* de `Pendientes/Ideas-Harness/PENDIENTES-I.md`.

## Qué queda afuera

- **Grafo, aristas y consultas.** No hay `graph.json`, no hay nodos ni relaciones tipadas, no hay
  lenguaje de consulta. Eso es un producto entero —se evaluaron dos y están anotados en Ideas— y
  acá alcanza con markdown que se lee. Si el índice resulta insuficiente, se sabrá con el índice
  puesto y no antes.
- **Actualización incremental.** El recorrido es completo o no es. Detectar qué cambió desde el
  último recorrido es otro cambio, y sin haber visto el primero funcionando no hay con qué
  decidirlo.
- **Cualquier bloqueo.** El aviso de `SessionStart` avisa. Nada de este cambio frena una
  herramienta: los secretos siguen siendo lo único que bloquea en todo el harness.
- **Disparo automático.** El harness sugiere; el recorrido lo lanza la persona. Un agente que
  recorre cientos de archivos sin que nadie lo haya pedido es exactamente la sorpresa que hace que
  se desinstale un harness.
- **Borrar lo que quedó viejo.** Una ficha cuyo módulo ya no existe se reporta, no se borra. Es la
  invariante de `flush-memoria` aplicada acá: ante la duda, no se borra.
- **`analisis`.** Un proyecto de solo análisis no tiene código que recorrer y no recibe este
  agente.

## Las decisiones, y por qué

### Es un agente, no una skill

Una skill corre en el contexto de quien la invoca. Un recorrido completo son cientos de archivos, y
meterlos en la sesión de la persona destruye la ventana que el recorrido venía a ahorrar.

El agente corre en su propio contexto y devuelve el informe, no el material. Es la invariante que
`comun/agents/leer-docs.md` ya declara para los binarios: *"el que te llama nunca ve el documento
crudo"*. Acá vale igual, con el código.

Se descartó el script de Python en `comun/bin/`: determinista y gratis, sirve para el esqueleto
—rutas, imports, tamaños— y no puede escribir qué hace un módulo, que es la única parte por la que
vale la pena recorrer.

### Lo aporta `desarrollo`, y por eso se llama `dev-iniciador-code`

Recorrer código solo tiene sentido donde hay código. Ponerlo en `comun/` lo instalaría también en
un proyecto de solo análisis, donde está de más y se paga igual en cada turno.

El precio es el nombre. Todos los archivos de un harness aterrizan juntos en `.claude/agents/`, sin
subdirectorio, y **el prefijo del manifiesto es lo único que dice de quién es cada cosa**. El
instalador no lo verifica —solo comprueba que dos harness no declaren el mismo prefijo, en
`install.ps1:1038`— así que un archivo sin prefijo no rompe nada y rompe la convención, que es
peor: no falla, y deja de saberse quién es el dueño.

### El índice vive en `docs/codebase/`, separado de `docs/conocimiento/`

Los dos son conocimiento del proyecto y los dos van adentro del repo, versionados y diffeables,
como manda ADR-0003. Pero tienen dueños y ciclos de vida distintos:

| | `docs/conocimiento/` | `docs/codebase/` |
|---|---|---|
| Quién escribe | una persona, y `flush-memoria` al desalojar la caché | `dev-iniciador-code` |
| Cómo se rehace | nunca entero: se agrega y se purga con la invariante | entero, cada vez |

Mezclarlos hace que un recorrido pise lo que alguien escribió a mano. Separarlos cuesta una carpeta
más y deja a `flush-memoria` sin nada que decidir.

### Sugiere `SessionStart`, no `install.ps1`

El instalador corre en una consola de PowerShell donde no hay ningún agente que pueda recorrer
nada. Podría dejar dicho que falta, pero eso es escribir un recordatorio en el peor momento: la
persona está instalando, no trabajando.

`SessionStart` ya contesta *"¿en qué quedamos?"* y ya lee `harness.lock.json` para saber qué
harness rigen. Agregarle una condición más es una línea de su presupuesto de doce, y llega cuando
la persona se sentó a trabajar.

El aviso **desaparece solo** en cuanto el índice existe. Un aviso permanente se vuelve ruido y se
deja de leer, y ahí se pierde también el resto del bloque.

### El default de la ruta va en el agente, no solo en el manifiesto

`rutaCodebase` se declara en el manifiesto de `desarrollo` y llega a `harness.config.json`. Pero
ese archivo **solo se crea si no existe** (`install.ps1:709`): un proyecto que ya tiene el harness
instalado nunca va a ver la clave nueva, ni después de un `-Update`.

Por eso el default vive en el agente y en el hook: si la clave no está, es `docs/codebase`. El
manifiesto sirve para el proyecto que se instala de cero y para poder disentir; no se puede
depender de él.

### Una ficha por módulo, no un archivo único

Un archivo único hay que cargarlo entero para consultar cualquier cosa, que es el problema que el
recorrido vino a resolver. Con `indice.md` más una ficha por módulo se lee la línea del índice y
después solo la ficha que hace falta.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | El agente. Recorre el repositorio, escribe el índice y las fichas, y devuelve un informe corto |
| `harnesses/desarrollo/manifest.json` | Suma `rutaCodebase: "docs/codebase"` a su `config` |
| `comun/hooks/session-start.py` | Una línea más: si `desarrollo` está en el lockfile y el índice no existe, lo sugiere |
| `tests/casos/` y `tests/payloads/` | Los tests de los escenarios de abajo, cada uno nombrando su `E-nn` |
| `docs/mapa/recorrido-mensaje.html` | La caja punteada pasa a caja llena cuando esto exista |

## Escenarios verificables

### El aviso de `SessionStart`

- **E-01** — Con `desarrollo` en `harness.lock.json` y sin `docs/codebase/indice.md`, la salida de
  `SessionStart` contiene una línea que nombra a `dev-iniciador-code`.
  · rojo visto: no consta
- **E-02** — Con `docs/codebase/indice.md` presente, esa línea no aparece.
  · rojo visto: no consta
- **E-03** — Sin `desarrollo` en el lockfile, la línea no aparece aunque el índice no exista.
  · rojo visto: no consta
- **E-04** — Con el aviso incluido, la salida de `SessionStart` no supera sus 12 líneas.
  · rojo visto: no consta
- **E-05** — El aviso sale como `additionalContext`. `SessionStart` no devuelve `deny` ni `ask` en
  ningún caso de este cambio.
  · rojo visto: no consta
- **E-06** — Si `docs/codebase/` no se puede leer —no existe el directorio, o falla el acceso—
  `SessionStart` sale con código 0 y el resto de su bloque se emite igual.
  · rojo visto: no consta

### Lo que queda escrito

- **E-07** — Terminado un recorrido, existe `docs/codebase/indice.md`.
  · rojo visto: no consta
- **E-08** — Cada línea del índice apunta a un archivo que existe dentro de `docs/codebase/`, y
  cada ficha de `docs/codebase/` figura en una línea del índice. La correspondencia va en los dos
  sentidos.
  · rojo visto: no consta
- **E-09** — Cada ficha tiene las cuatro secciones: qué es, qué expone, de qué depende y dónde
  está. Una ficha a la que le falte una no cumple.
  · rojo visto: no consta
- **E-10** — Ningún archivo escrito por el recorrido matchea un patrón de
  `comun/reglas/secretos.patrones.json` con severidad de bloqueo.
  · rojo visto: no consta
- **E-11** — El recorrido no escribe ni modifica ningún archivo fuera de `docs/codebase/`.
  · rojo visto: no consta
- **E-12** — Un archivo ignorado por `.gitignore` no produce ficha ni aparece en el índice.
  · rojo visto: no consta

### Volver a recorrer

- **E-13** — Un segundo recorrido sobre un repositorio sin cambios deja el mismo conjunto de
  nombres de archivo en `docs/codebase/`. No aparecen fichas duplicadas ni con sufijo.
  · rojo visto: no consta
- **E-14** — Si una ficha corresponde a un módulo que ya no existe, el recorrido la deja donde está
  y la nombra en su informe. No la borra.
  · rojo visto: no consta

### El informe que devuelve

- **E-15** — El informe dice cuántas fichas escribió, cuántas dejó igual y qué no recorrió.
  · rojo visto: no consta
- **E-16** — El informe no contiene código fuente del proyecto: ni un bloque de código, ni una
  línea citada de un archivo recorrido.
  · rojo visto: no consta
- **E-17** — Sobre un repositorio sin código, el recorrido no escribe nada y lo dice.
  · rojo visto: no consta

### Instalación

- **E-18** — Instalado `desarrollo`, existe `.claude/agents/dev-iniciador-code.md`.
  · rojo visto: no consta
- **E-19** — Instalado `desarrollo` de cero, `harness.config.json` tiene `rutaCodebase`.
  · rojo visto: no consta
- **E-20** — Sobre un proyecto con `harness.config.json` preexistente y sin la clave, el recorrido
  y el aviso usan `docs/codebase` igual.
  · rojo visto: no consta
- **E-21** — `-Uninstall` deja `docs/codebase/` intacto. Es conocimiento del proyecto, no material
  del harness.
  · rojo visto: no consta

## Cómo se verifica

Por la suite, con un caso por escenario que nombre su id: E-01 a E-06 con payloads de
`SessionStart` en `tests/payloads/`, contra un proyecto de fixture con y sin lockfile de
`desarrollo`; E-18 a E-21 en `tests/casos/03-instalador.ps1`, que ya monta y desmonta instalaciones
completas.

Por lectura de una persona: E-07 a E-17. Todos dependen de que un agente con modelo recorra un
repositorio real, y la suite no invoca modelos —los 334 tests actuales son deterministas y sin
red—. Se verifican corriendo el agente una vez sobre este mismo repositorio y contrastando la
salida contra los escenarios.

Lo que sí puede ir a la suite de esos once es la forma de lo escrito: E-08, E-09, E-10 y E-12 son
comprobables sobre un `docs/codebase/` de fixture, sin invocar a nadie, y ahí conviene que estén.

El que construye no verifica. `harness-spec-refuter` corre la suite y falla contra esta spec.

## Riesgos conocidos

**El índice envejece y nadie se entera.** El recorrido es completo y manual: el día después de un
refactor grande, las fichas mienten. Un índice desactualizado es peor que no tenerlo, porque se lee
con la misma confianza. Este diseño no lo previene —la actualización incremental quedó afuera a
propósito— y lo único que hay es que las fichas están versionadas, así que el diff las muestra
viejas.

**El costo del recorrido no está medido.** Cuánto sale recorrer un repositorio del GCBA, en tokens
y en minutos, no lo sabe nadie todavía. Si el número es alto, la sugerencia de `SessionStart` está
empujando a la gente a un gasto que no anunció. El primer recorrido sobre este repositorio es el
que da ese número, y conviene anotarlo antes de instalarlo en otro lado.

**Las cuatro secciones de una ficha pueden estar y no decir nada.** E-09 comprueba que estén, no
que sirvan. Es el riesgo residual que ADR-0006 ya nombra —*"una spec escrita para pasar el
check"*— trasladado al artefacto: un agente que completa las cuatro secciones con generalidades
pasa el escenario y no aporta nada. La defensa es la lectura de E-07 a E-17, y no es mecánica.

**`dev-iniciador-code` se paga en cada turno.** El nombre y la descripción de un agente ocupan
contexto siempre, se lo use o no —hoy son 926 tokens entre 13 piezas—. Este es la pieza catorce, y
la usa una vez por proyecto. `harness-budget-auditor` tiene que pesarlo antes de que se dé por
cerrado.
